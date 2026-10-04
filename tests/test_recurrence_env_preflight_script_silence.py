"""
Silence and a preflight that never runs, for the W0.2 recurrence env check.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
Version:     1.0.0
License:     MIT License

``tests/test_recurrence_env_preflight.py`` drives every branch with a fake that
prints a reason, and both launcher suites drive the real script (exit 0 or 1,
with findings). Neither reaches two fail-closed edges of the code that landed
in #2139:

- A probe that exits and prints nothing. ``pip check`` exit 1 with an empty
  capture must still be a finding (``no output``), not a clean scan. A pin
  probe that exits 0 without a protocol line must still refuse: the script
  treats "no protocol" as a failed probe. An import that exits 1 with an empty
  capture must name the probe. The other two checks still run.
- ``run_env_preflight`` in both launchers, called the way ``recurrence_up``
  calls it (``fn || return 1``, which turns ``set -e`` off for the body). A
  missing script is exit 127 and must refuse; a script that exits 99 must
  refuse even though it never prints ``ENV PREFLIGHT REFUSED``. A blank line
  in the report is not copied into ``launch.log``. An unwritable ``launch.log``
  warns and does not flip the verdict either way.

Hermetic: no network, no conda, nothing outside a temp dir.
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.recurrence_env_fakes import IMPORT_PROBE, PREFLIGHT_SCRIPT
from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
LAUNCHERS = (
    REPO_ROOT / "util" / "experiment_stack.bash",
    REPO_ROOT / "util" / "isolated_stack.bash",
)
SCRIPT_TIMEOUT_SECONDS = 30
PINS_OK = "APP 0.5.0 packaging\nOK juniper-recurrence-model 0.3.0 <0.4.0,>=0.3.0\nOK juniper-service-core 0.7.0 <0.8.0,>=0.6.0\n"
PIP_CLEAN = "No broken requirements found.\n"
PIN_MARKER = "recurrence_env_preflight version-pin probe"
REFUSED_ONE = "ENV PREFLIGHT REFUSED: 1 finding(s); fix the env or pass --skip-env-preflight"
# A logged blank message is `timestamp [script] ` with nothing after the bracket.
_BLANK_LOG_LINE = re.compile(r"^\S+ \[[^\]]+\] $")


def _last_line(text: str) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def _run_preflight(python: Path) -> subprocess.CompletedProcess[str]:
    env = RedactedEnv(os.environ)
    for key in ("PYTHONPATH", "PYTHONHOME"):
        env.pop(key, None)
    return subprocess.run(
        ["/bin/bash", str(PREFLIGHT_SCRIPT), "--python", str(python)],
        capture_output=True,
        text=True,
        env=env,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


def _write_python(path: Path, *, pip_text: str, pip_rc: int, pins_text: str, pins_rc: int, import_text: str, import_rc: int) -> None:
    """An executable ``python`` that prints exactly the given text for each of the three probes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "#!/usr/bin/env bash\n"
        'if [[ "${1-}" != "-s" ]]; then echo "silent python: -s required first" >&2; exit 97; fi\n'
        "shift\n"
        'if [[ "${1-}" == "-m" && "${2-}" == "pip" && "${3-}" == "check" ]]; then\n'
        f"    printf %s {shlex.quote(pip_text)}\n"
        f"    exit {pip_rc}\n"
        "fi\n"
        'if [[ "${1-}" == "-c" ]]; then\n'
        '    case "${2-}" in\n'
        f'        *"{PIN_MARKER}"*)\n'
        f"            printf %s {shlex.quote(pins_text)}\n"
        f"            exit {pins_rc}\n"
        "            ;;\n"
        f'        "{IMPORT_PROBE}")\n'
        f"            printf %s {shlex.quote(import_text)}\n"
        f"            exit {import_rc}\n"
        "            ;;\n"
        "    esac\n"
        "fi\n"
        'echo "silent python: unexpected call: $*" >&2\n'
        "exit 98\n"
    )
    path.chmod(0o755)


def _extract(script_text: str, name: str) -> str:
    match = re.search(rf"^{re.escape(name)}\(\) \{{.*?\n\}}\n", script_text, flags=re.MULTILINE | re.DOTALL)
    if match is None:
        raise AssertionError(f"{name}() not found")
    return match.group(0)


def _write_preflight(path: Path, body: str) -> None:
    path.write_text(body)
    path.chmod(0o755)


def _run_launcher(launcher: Path, *, env_preflight: str, log_dir: Path, python: str = "/opt/fake-env/bin/python") -> subprocess.CompletedProcess[str]:
    """Call the launcher's own ``run_env_preflight`` under the OR-list that disables ``set -e``."""
    text = launcher.read_text(encoding="utf-8")
    log_dir.mkdir(parents=True, exist_ok=True)
    harness = "\n".join(
        [
            "set -euo pipefail",
            f"SCRIPT_NAME={shlex.quote(launcher.name)}",
            f"LOG_DIR={shlex.quote(str(log_dir))}",
            f"ENV_PREFLIGHT={shlex.quote(env_preflight)}",
            "SKIP_ENV_PREFLIGHT=0",
            'log() { echo "[${SCRIPT_NAME}] $*"; }',
            _extract(text, "log_launch"),
            _extract(text, "run_env_preflight"),
            "failed=0",
            f"run_env_preflight {shlex.quote(python)} || failed=1",
            "printf 'STATUS=%s\\n' \"$failed\"",
        ]
    )
    return subprocess.run(["/bin/bash", "-c", harness], capture_output=True, text=True, env=RedactedEnv(os.environ), timeout=SCRIPT_TIMEOUT_SECONDS)


class TestSilentProbes(unittest.TestCase):
    """A probe that exits without printing is a finding, and the other checks still run."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.python = Path(self._tmp.name) / "env" / "bin" / "python"

    def test_an_empty_pip_check_failure_refuses_and_names_no_output(self) -> None:
        _write_python(self.python, pip_text="", pip_rc=1, pins_text=PINS_OK, pins_rc=0, import_text="", import_rc=0)
        result = _run_preflight(self.python)
        out = result.stdout
        self.assertEqual(result.returncode, 1, msg=out + result.stderr)
        self.assertIn("FINDING: pip check could not run (exit 1): no output\n", out)
        self.assertIn("ENV PREFLIGHT: pin ok: juniper-service-core 0.7.0 satisfies juniper-service-core<0.8.0,>=0.6.0\n", out)
        self.assertIn(f"ENV PREFLIGHT: import ok: {IMPORT_PROBE}\n", out)
        self.assertEqual(_last_line(out), REFUSED_ONE)

    def test_an_empty_pin_probe_that_exits_zero_still_refuses(self) -> None:
        # Exit 0 with no protocol line is not "pins ok". The script never saw APP/OK/BAD.
        _write_python(self.python, pip_text=PIP_CLEAN, pip_rc=0, pins_text="", pins_rc=0, import_text="", import_rc=0)
        result = _run_preflight(self.python)
        out = result.stdout
        self.assertEqual(result.returncode, 1, msg=out + result.stderr)
        self.assertIn("FINDING: version-pin probe failed (exit 0): no output\n", out)
        self.assertNotIn("pin ok:", out)
        self.assertIn(f"ENV PREFLIGHT: import ok: {IMPORT_PROBE}\n", out)
        self.assertEqual(_last_line(out), REFUSED_ONE)

    def test_an_empty_import_failure_names_the_probe(self) -> None:
        _write_python(self.python, pip_text=PIP_CLEAN, pip_rc=0, pins_text=PINS_OK, pins_rc=0, import_text="", import_rc=1)
        result = _run_preflight(self.python)
        out = result.stdout
        self.assertEqual(result.returncode, 1, msg=out + result.stderr)
        self.assertIn(f"FINDING: import probe '{IMPORT_PROBE}' failed (exit 1): no output\n", out)
        self.assertIn("ENV PREFLIGHT: pin ok: juniper-recurrence-model 0.3.0 satisfies juniper-recurrence-model<0.4.0,>=0.3.0\n", out)
        self.assertEqual(_last_line(out), REFUSED_ONE)


class TestLauncherWhenThePreflightDoesNotRun(unittest.TestCase):
    """``run_env_preflight`` fails closed when the script itself does not finish cleanly.

    Invoked as ``run_env_preflight || failed=1``. Production is
    ``run_env_preflight || return 1`` inside ``recurrence_up || failed=1``;
    either form turns ``set -e`` off for the body. The ``|| rc=$?`` on the
    ``bash`` line is what records the failure; dropping it reports a pass.
    """

    def test_a_missing_script_refuses_and_records_exit_127(self) -> None:
        missing = "/no/such/recurrence_env_preflight.bash"
        for launcher in LAUNCHERS:
            with self.subTest(launcher=launcher.name):
                with tempfile.TemporaryDirectory() as tmp:
                    log_dir = Path(tmp) / "logs"
                    result = _run_launcher(launcher, env_preflight=missing, log_dir=log_dir)
                    out = result.stdout
                    self.assertEqual(result.returncode, 0, msg=result.stderr + out)
                    self.assertIn("STATUS=1\n", out)
                    self.assertIn(f"bash: {missing}: No such file or directory", out)
                    self.assertIn("recurrence env preflight refused /opt/fake-env/bin/python (exit 127); serve NOT started", out)
                    log_text = (log_dir / "launch.log").read_text(encoding="utf-8")
                    self.assertIn("No such file or directory", log_text)
                    self.assertIn("exit 127", log_text)

    def test_exit_99_refuses_without_the_scripts_own_refused_banner(self) -> None:
        for launcher in LAUNCHERS:
            with self.subTest(launcher=launcher.name):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    script = root / "preflight.bash"
                    _write_preflight(script, "#!/bin/bash\nprintf 'probe died before a verdict\\n'\nexit 99\n")
                    log_dir = root / "logs"
                    result = _run_launcher(launcher, env_preflight=str(script), log_dir=log_dir)
                    out = result.stdout
                    self.assertEqual(result.returncode, 0, msg=result.stderr + out)
                    self.assertIn("STATUS=1\n", out)
                    self.assertIn("probe died before a verdict", out)
                    self.assertNotIn("ENV PREFLIGHT REFUSED", out)
                    self.assertIn("(exit 99); serve NOT started", out)
                    log_text = (log_dir / "launch.log").read_text(encoding="utf-8")
                    self.assertIn("probe died before a verdict\n", log_text)
                    self.assertIn("exit 99", log_text)

    def test_a_blank_line_between_report_lines_is_not_logged(self) -> None:
        for launcher in LAUNCHERS:
            with self.subTest(launcher=launcher.name):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    script = root / "preflight.bash"
                    _write_preflight(script, "#!/bin/bash\nprintf 'ENV PREFLIGHT OK: no findings\\n\\nkept\\n'\nexit 0\n")
                    log_dir = root / "logs"
                    result = _run_launcher(launcher, env_preflight=str(script), log_dir=log_dir)
                    out = result.stdout
                    self.assertEqual(result.returncode, 0, msg=result.stderr + out)
                    self.assertIn("STATUS=0\n", out)
                    self.assertNotIn("serve NOT started", out)
                    log_lines = (log_dir / "launch.log").read_text(encoding="utf-8").splitlines()
                    # The command line, the OK line, and "kept". The blank line is dropped.
                    self.assertEqual(len(log_lines), 3, msg=log_lines)
                    self.assertTrue(any(line.endswith(" ENV PREFLIGHT OK: no findings") for line in log_lines), msg=log_lines)
                    self.assertTrue(any(line.endswith(" kept") for line in log_lines), msg=log_lines)
                    self.assertFalse(any(_BLANK_LOG_LINE.match(line) for line in log_lines), msg=log_lines)
                    if launcher.name == "isolated_stack.bash":
                        self.assertTrue(any("LD_LIBRARY_PATH= bash " in line for line in log_lines), msg=log_lines)
                    else:
                        self.assertTrue(any("preflight: bash " in line and "LD_LIBRARY_PATH=" not in line for line in log_lines), msg=log_lines)

    def test_an_unwritable_log_warns_and_a_clean_preflight_still_passes(self) -> None:
        for launcher in LAUNCHERS:
            with self.subTest(launcher=launcher.name):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    script = root / "preflight.bash"
                    _write_preflight(script, "#!/bin/bash\nprintf 'ENV PREFLIGHT OK: no findings\\n'\nexit 0\n")
                    log_dir = root / "logs"
                    log_dir.mkdir()
                    (log_dir / "launch.log").mkdir()
                    result = _run_launcher(launcher, env_preflight=str(script), log_dir=log_dir)
                    out = result.stdout
                    self.assertEqual(result.returncode, 0, msg=result.stderr + out)
                    self.assertIn("STATUS=0\n", out)
                    self.assertIn(f"WARNING: could not append to {log_dir}/launch.log", out)
                    self.assertNotIn("serve NOT started", out)
                    self.assertIn("ENV PREFLIGHT OK: no findings", out)

    def test_an_unwritable_log_does_not_hide_a_refusal(self) -> None:
        for launcher in LAUNCHERS:
            with self.subTest(launcher=launcher.name):
                with tempfile.TemporaryDirectory() as tmp:
                    root = Path(tmp)
                    script = root / "preflight.bash"
                    _write_preflight(script, "#!/bin/bash\nprintf 'FINDING: stale\\n'\nexit 1\n")
                    log_dir = root / "logs"
                    log_dir.mkdir()
                    (log_dir / "launch.log").mkdir()
                    result = _run_launcher(launcher, env_preflight=str(script), log_dir=log_dir)
                    out = result.stdout
                    self.assertEqual(result.returncode, 0, msg=result.stderr + out)
                    self.assertIn("STATUS=1\n", out)
                    self.assertIn(f"WARNING: could not append to {log_dir}/launch.log", out)
                    self.assertIn("FINDING: stale", out)
                    self.assertIn("(exit 1); serve NOT started", out)
