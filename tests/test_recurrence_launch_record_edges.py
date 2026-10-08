"""Edges the W1.9 / W1.10 suites do not pin.

``tests/test_experiment_stack_script.py`` and ``tests/test_run_experiment.py`` cover the
happy path: a set log level reaches serve, a quote and a backslash round-trip through
``ports.json``, a missing recorded CLI fails closed, and a different port sets the launch
record aside. The failures those tests cannot see:

- an *empty* log knob (set, but blank) is still a value to the service, so it must stay
  off the serve command the same way an unset one does;
- a newline, CR, or tab in a recorded path must stay inside the JSON string -- unescaped,
  ``ports.json`` stops being one document and a text reader can see a second ``"data"`` line;
- ``write_ports_json`` is called from an extracted ``recurrence_up`` that does not have the
  file-scope globals, so an unset ``WANT_BRIDGE`` / ``RUN_ID`` / ``EXPERIMENT`` must not
  die under ``set -u``;
- a recorded CLI that exists but cannot be executed (mode 0644, a directory, or a blank
  path) must not fall back to whatever ``juniper-recurrence`` is first on PATH; an empty
  string is not a recorded CLI;
- a launch record with no port, or one whose host or path is not the service this run
  drives, must be set aside even when the port number matches;
- the model-version probe is exactly ``python -c`` from ``/`` with no ``-s``. Extra
  trailing newlines still count as one version (including an epoch and a local label).
  A trailing space does not. A timeout or a missing interpreter is a reason, not an
  exception that skips the phase record.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
import tempfile
import unittest
import unittest.mock as mock
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
LAUNCHER = REPO_ROOT / "util" / "experiment_stack.bash"
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import run_experiment as rx  # noqa: E402  (path-invoked util import)


def _extract(name: str) -> str:
    """A live ``<name>() { ... }`` body from the launcher. The closing brace is its own line."""
    match = re.search(rf"^{re.escape(name)}\(\) \{{.*?\n\}}\n", LAUNCHER.read_text(encoding="utf-8"), flags=re.MULTILINE | re.DOTALL)
    if match is None:
        raise AssertionError(f"{name} not found in {LAUNCHER}")
    return match.group(0)


def _bash(script: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["/bin/bash", "-c", script], capture_output=True, text=True, env=RedactedEnv(os.environ), timeout=30)


class TestRecurrenceLaunchWriterEdges(unittest.TestCase):
    """Launcher edges around the log knobs and the ports.json writer."""

    def test_an_empty_log_knob_stays_off_the_serve_announce(self) -> None:
        """Empty is a value to the service. ``-n`` must drop it; a set sibling still appears."""
        out = self._dry_announce(level="", fmt="json")
        self.assertIn("JUNIPER_RECURRENCE_SNAPSHOTS_DIR=", out)
        self.assertIn("JUNIPER_RECURRENCE_LOG_FORMAT=json", out)
        self.assertNotIn("JUNIPER_RECURRENCE_LOG_LEVEL", out)

    def test_both_empty_log_knobs_stay_off_the_serve_announce(self) -> None:
        out = self._dry_announce(level="", fmt="")
        self.assertIn("JUNIPER_RECURRENCE_SNAPSHOTS_DIR=", out)
        self.assertNotIn("JUNIPER_RECURRENCE_LOG_LEVEL", out)
        self.assertNotIn("JUNIPER_RECURRENCE_LOG_FORMAT", out)

    def test_a_control_character_in_a_recorded_path_stays_inside_the_string(self) -> None:
        """Newline, CR, and tab are escaped. A broken string would add a second top-level data line."""
        odd = '/opt/env/bin/python3\n  "data": 9999\r\n  "recurrence": 7\t'
        text = self._write_ports(odd)
        ports = json.loads(text)
        self.assertEqual(ports["recurrence_launch"]["python"], odd)
        self.assertEqual(ports["data"], 8110)
        self.assertEqual([line for line in text.splitlines() if line.startswith('  "data":')], ['  "data": 8110,'])
        self.assertEqual(self._read_port(text, "data"), "8110")
        self.assertEqual(self._read_port(text, "recurrence"), "8260")

    def test_unset_identity_globals_still_write_ports_json(self) -> None:
        """The extracted harness does not carry the file-scope globals. ``:-`` keeps ``set -u`` alive."""
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            script = "set -euo pipefail\nunset WANT_BRIDGE RUN_ID EXPERIMENT RECURRENCE_LAUNCH_JSON\n" f'RUN_DIR={shlex.quote(str(run_dir))}\nDATA_PORT=8110\nCASCOR_PORT=\nRECURRENCE_PORT=8260\nDATA_URL="http://127.0.0.1:8110"\n' "announce() { :; }\nis_dry() { false; }\n" + _extract("json_number_or_null") + _extract("json_string_or_null") + _extract("recurrence_launch_json") + _extract("render_ports_json") + _extract("write_ports_json") + "write_ports_json\n"
            result = _bash(script)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertFalse((run_dir / "ports.json.tmp").exists())
            ports = json.loads((run_dir / "ports.json").read_text(encoding="utf-8"))
        self.assertEqual(ports["run_id"], "")
        self.assertEqual(ports["experiment"], "")
        self.assertIs(ports["grafana_bridge"], False)
        self.assertNotIn("recurrence_launch", ports)
        self.assertEqual(ports["recurrence"], 8260)

    def _dry_announce(self, *, level: str, fmt: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp) / "run"
            script = (
                "set -euo pipefail\nDRY_RUN=1\nSCRIPT_NAME=experiment_stack\n"
                f"CONDA_DIR={shlex.quote(str(Path(tmp) / 'conda'))}\n"
                "RECURRENCE_CONDA=JuniperCascor1\n"
                f"RUN_DIR={shlex.quote(str(run_dir))}\n"
                'DATA_URL="http://127.0.0.1:8110"\nRECURRENCE_PORT=8260\n'
                "CONFIG_PATH=\nSKIP_ENV_PREFLIGHT=0\nENV_PREFLIGHT=/dev/null\n"
                f"LOG_DIR={shlex.quote(str(Path(tmp) / 'logs'))}\n"
                "unset JUNIPER_RECURRENCE_LOG_LEVEL JUNIPER_RECURRENCE_LOG_FORMAT\n"
                f"export JUNIPER_RECURRENCE_LOG_LEVEL={shlex.quote(level)}\n"
                f"export JUNIPER_RECURRENCE_LOG_FORMAT={shlex.quote(fmt)}\n" + _extract("banner") + _extract("announce") + _extract("is_dry") + _extract("env_bin") + _extract("console_script_python") + _extract("recurrence_up") + "recurrence_up\n"
            )
            result = _bash(script)
        self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
        return result.stdout

    def _write_ports(self, python_path: str) -> str:
        args = ("JuniperCascor1", "/opt/env/bin/juniper-recurrence", python_path, "", "/runs/x/snapshots", "", "", "")
        launch = 'RECURRENCE_LAUNCH_JSON="$(recurrence_launch_json ' + " ".join(shlex.quote(arg) for arg in args) + ')"\n'
        with tempfile.TemporaryDirectory() as tmp:
            run_dir = Path(tmp)
            script = "set -euo pipefail\n" f'RUN_DIR={shlex.quote(str(run_dir))}\nRUN_ID="20261005T000000Z-ab12"\nDATA_PORT=8110\nCASCOR_PORT=\nRECURRENCE_PORT=8260\n' 'DATA_URL="http://127.0.0.1:8110"\nEXPERIMENT="cell-01"\nWANT_BRIDGE=0\n' "announce() { :; }\nis_dry() { false; }\n" + _extract("json_number_or_null") + _extract("json_string_or_null") + _extract("recurrence_launch_json") + _extract("render_ports_json") + _extract("write_ports_json") + launch + "write_ports_json\n"
            result = _bash(script)
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            return (run_dir / "ports.json").read_text(encoding="utf-8")

    def _read_port(self, text: str, key: str) -> str:
        with tempfile.TemporaryDirectory() as tmp:
            ports = Path(tmp) / "ports.json"
            ports.write_text(text, encoding="utf-8")
            script = "set -euo pipefail\n" + _extract("read_run_port") + f"read_run_port {shlex.quote(str(ports))} {shlex.quote(key)}\n"
            result = _bash(script)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        return result.stdout


class TestSaveModelLaunchRecordEdges(unittest.TestCase):
    """Driver edges around which CLI runs, and which launch record is allowed to choose it."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.out = self.root / "model.npz"
        self.path_marker = self.root / "path-ran"
        self.path_bin = self.root / "path-bin"
        self.path_bin.mkdir()
        sentinel = self.path_bin / "juniper-recurrence"
        sentinel.write_text(f"#!/bin/bash\nprintf ran > {shlex.quote(str(self.path_marker))}\nexit 0\n", encoding="utf-8")
        sentinel.chmod(0o755)
        self._path = mock.patch.dict(os.environ, {"PATH": f"{self.path_bin}{os.pathsep}{os.environ['PATH']}"})
        self._path.start()
        self.addCleanup(self._path.stop)

    def _rerun(self, launch: dict) -> dict:
        return rx._save_model_rerun({"d": 8}, "ds-1", "train", "http://127.0.0.1:9", self.out, launch=launch)

    def _plant_mode(self, mode: int) -> Path:
        cli = self.root / "recorded" / "juniper-recurrence"
        cli.parent.mkdir(parents=True, exist_ok=True)
        cli.write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
        cli.chmod(mode)
        return cli

    def test_a_non_executable_recorded_cli_does_not_fall_back_to_path(self) -> None:
        if os.access(self._plant_mode(0o644), os.X_OK):
            self.skipTest("this uid treats a 0644 file as executable, so the mode arm cannot fail closed")
        cli = self._plant_mode(0o644)
        result = self._rerun({"cli": str(cli), "python": "/served/bin/python"})
        self.assertEqual(result["cli_source"], "launcher")
        self.assertNotIn("cmd", result)
        self.assertIn(str(cli), result["error"])
        self.assertIn("does not fall back to PATH", result["error"])
        self.assertFalse(self.path_marker.exists())

    def test_a_directory_recorded_as_the_cli_does_not_fall_back_to_path(self) -> None:
        cli = self.root / "not-a-file"
        cli.mkdir()
        result = self._rerun({"cli": str(cli)})
        self.assertEqual(result["cli_source"], "launcher")
        self.assertNotIn("cmd", result)
        self.assertIn("does not fall back to PATH", result["error"])
        self.assertFalse(self.path_marker.exists())

    def test_a_blank_recorded_cli_does_not_fall_back_and_an_empty_one_does(self) -> None:
        """Whitespace is a recorded path. An empty string is the same as no CLI at all."""
        blank = self._rerun({"cli": " ", "python": "/served/bin/python"})
        self.assertEqual(blank["cli_source"], "launcher")
        self.assertIn("does not fall back to PATH", blank["error"])
        self.assertFalse(self.path_marker.exists())

        # The PATH sentinel's interpreter is not the served one, so "not recorded" shows up as a
        # parity mismatch rather than as "missing or not executable".
        empty = self._rerun({"cli": "", "python": "/served/bin/python", "model_version": "0.3.2"})
        self.assertEqual(empty["cli_source"], "path")
        self.assertEqual(empty["cmd"][0], str(self.path_bin / "juniper-recurrence"))
        self.assertEqual(empty["parity"]["interpreter"], "mismatch")
        self.assertFalse(self.path_marker.exists(), "a parity mismatch must not run the PATH CLI")
        self.assertNotIn("does not fall back to PATH", empty["error"])

    def test_an_executable_recorded_cli_still_runs(self) -> None:
        """The fail-closed arms above are not an inverted condition that refuses every recorded CLI."""
        bindir = self.root / "env" / "bin"
        bindir.mkdir(parents=True)
        # The shebang interpreter must exec the console script. A stub that exits 0 itself
        # would make the phase look successful without ever running the CLI body.
        python = bindir / "python"
        python.write_text('#!/bin/bash\nexec /bin/bash "$@"\n', encoding="utf-8")
        python.chmod(0o755)
        marker = self.root / "recorded-ran"
        cli = bindir / "juniper-recurrence"
        cli.write_text(f"#!{python}\nprintf ran > {shlex.quote(str(marker))}\nexit 0\n", encoding="utf-8")
        cli.chmod(0o755)
        result = self._rerun({"cli": str(cli), "python": str(python)})
        self.assertTrue(result["ok"])
        self.assertEqual(result["cli_source"], "launcher")
        self.assertEqual(result["parity"]["interpreter"], "match")
        self.assertEqual(result["parity"]["model_version"], "unverified")
        self.assertTrue(marker.is_file())
        self.assertFalse(self.path_marker.exists())

    def test_a_record_without_a_port_is_set_aside(self) -> None:
        record = {"cli": "/env/bin/juniper-recurrence"}
        url = "http://127.0.0.1:8260"
        cases = (
            ("missing", {"recurrence_launch": record}),
            ("null", {"recurrence": None, "recurrence_launch": record}),
            ("zero", {"recurrence": 0, "recurrence_launch": record}),
            ("empty", {"recurrence": "", "recurrence_launch": record}),
        )
        for label, ports in cases:
            with self.subTest(port=label):
                kept, note = rx._recurrence_launch_record(ports, url)
                self.assertEqual(kept, {})
                self.assertIsNotNone(note)
                assert note is not None
                self.assertIn("(no recorded port)", note)
                self.assertIn(url, note)

    def test_the_same_port_on_another_host_or_with_a_path_is_set_aside(self) -> None:
        record = {"cli": "/env/bin/juniper-recurrence"}
        ports = {"recurrence": 8260, "recurrence_launch": record}
        for url in ("http://localhost:8260", "http://127.0.0.1:8260/v1", "http://127.0.0.1:8260/v1/"):
            with self.subTest(url=url):
                kept, note = rx._recurrence_launch_record(ports, url)
                self.assertEqual(kept, {})
                self.assertIsNotNone(note)
                assert note is not None
                self.assertIn("http://127.0.0.1:8260", note)
                self.assertIn(url.rstrip("/"), note)
                self.assertIn("set aside", note)
                self.assertNotIn("(no recorded port)", note)

    def test_a_string_port_still_describes_the_service(self) -> None:
        record = {"cli": "/env/bin/juniper-recurrence"}
        ports = {"recurrence": "8260", "recurrence_launch": record}
        self.assertEqual(rx._recurrence_launch_record(ports, "http://127.0.0.1:8260"), (record, None))


class TestModelVersionProbeEdges(unittest.TestCase):
    """The probe must agree with the launcher: no ``-s``, from ``/``, one version token."""

    def test_the_probe_is_python_dash_c_from_root_and_keeps_an_epoch_local_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "probe.log"
            fake = Path(tmp) / "python"
            probe = rx.RECURRENCE_MODEL_VERSION_PROBE
            fake.write_text(
                "#!/bin/bash\n" f'printf \'cwd=%s\\nargc=%s\\narg1=%s\\narg2=%s\\nsentinel=%s\\n\' "$PWD" "$#" "${{1-}}" "${{2-}}" "${{PROBE_SENTINEL-}}" > {shlex.quote(str(log))}\n' f'if [[ "$#" == 2 && "$1" == -c && "$2" == {shlex.quote(probe)} ]]; then\n' "    printf '1!2.0+local\\n\\n'\n" "    exit 0\n" "fi\n" "echo bad >&2\n" "exit 9\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            version, reason = rx._probe_model_version(str(fake), RedactedEnv(os.environ, PROBE_SENTINEL="present"))
            recorded = log.read_text(encoding="utf-8")
        self.assertEqual((version, reason), ("1!2.0+local", None))
        self.assertEqual(recorded, f"cwd=/\nargc=2\narg1=-c\narg2={probe}\nsentinel=present\n")

    def test_a_trailing_space_is_not_a_version(self) -> None:
        """``rstrip`` drops trailing newlines only. ``strip`` would accept a padded token."""
        with tempfile.TemporaryDirectory() as tmp:
            fake = Path(tmp) / "python"
            fake.write_text("#!/bin/bash\nprintf '0.3.2 \\n'\n", encoding="utf-8")
            fake.chmod(0o755)
            version, reason = rx._probe_model_version(str(fake), RedactedEnv(os.environ))
        self.assertIsNone(version)
        self.assertIn("printed no version", reason)
        self.assertIn("0.3.2 ", reason)

    def test_a_timeout_or_a_missing_interpreter_is_a_reason(self) -> None:
        with mock.patch.object(rx.subprocess, "run", side_effect=subprocess.TimeoutExpired(["python", "-c", "probe"], 60)):
            version, reason = rx._probe_model_version("/no/python", {})
        self.assertIsNone(version)
        self.assertIn("the probe could not run", reason)
        self.assertIn("timed out", reason)

        with mock.patch.object(rx.subprocess, "run", side_effect=FileNotFoundError(2, "No such file or directory")):
            version, reason = rx._probe_model_version("/no/python", {})
        self.assertIsNone(version)
        self.assertIn("the probe could not run", reason)
        self.assertIn("No such file", reason)
