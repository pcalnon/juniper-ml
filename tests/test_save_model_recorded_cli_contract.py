"""Contract of the W1.9 recorded ``save_model`` re-run that the happy-path suites do not pin.

``tests/test_run_experiment.py`` proves a PATH CLI receives ``JUNIPER_DATA_URL`` and an empty
``LD_LIBRARY_PATH``, and that ``--d 8`` is forwarded. ``tests/test_recurrence_launch_record_edges.py``
proves which recorded CLI is allowed to run. Neither watches the environment of the launcher-recorded
CLI (the path a real ``--up`` takes), nor a hyperparameter whose value is numeric zero, nor a
non-string field of the launch record, nor which end of a long failure is kept.

No live services. The recorded console script is a bash stub whose shebang interpreter answers the
model-version probe and then executes the script.
"""

from __future__ import annotations

import os
import shlex
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import run_experiment as rx  # noqa: E402  (path-invoked util import)

DATA_URL = "http://127.0.0.1:8110"
POISON_URL = "http://wrong.example:9"
POISON_LIB = "/poison/libtorch"
SERVED_VERSION = "0.3.2"


def _write_executable(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(0o755)


class TestRecordedCliRerunContract(unittest.TestCase):
    """The CLI ports.json recorded, run under the env the re-run actually builds."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.out = self.root / "model.npz"
        self.log = self.root / "child.log"
        self.path_marker = self.root / "path-ran"
        self.ran = self.root / "recorded-ran"
        path_bin = self.root / "path-bin"
        sentinel = path_bin / "juniper-recurrence"
        _write_executable(sentinel, f"#!/bin/bash\nprintf ran > {shlex.quote(str(self.path_marker))}\nexit 0\n")
        self.sentinel = sentinel
        path = mock.patch.dict(os.environ, {"PATH": f"{path_bin}{os.pathsep}{os.environ.get('PATH', '')}"})
        path.start()
        self.addCleanup(path.stop)
        previous = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, previous)

    def _plant(self, body: str) -> tuple[Path, Path]:
        """A recorded env: ``python`` answers the probe, then runs the console script under bash."""
        bindir = self.root / "env" / "bin"
        python = bindir / "python"
        quoted_log = shlex.quote(str(self.log))
        _write_executable(
            python,
            "#!/bin/bash\n" 'if [[ "${1-}" == "-c" ]]; then\n' f"  printf 'probe_url=[%s]\\n' \"${{JUNIPER_DATA_URL-__UNSET__}}\" >> {quoted_log}\n" f"  printf 'probe_ld=[%s]\\n' \"${{LD_LIBRARY_PATH-__UNSET__}}\" >> {quoted_log}\n" f"  printf '%s\\n' {shlex.quote(SERVED_VERSION)}\n" "  exit 0\n" "fi\n" 'exec /bin/bash "$@"\n',
        )
        cli = bindir / "juniper-recurrence"
        _write_executable(cli, f"#!{python}\n{body}")
        return cli, python

    def _success_body(self) -> str:
        quoted_log = shlex.quote(str(self.log))
        quoted_ran = shlex.quote(str(self.ran))
        return f"printf 'cli_url=[%s]\\n' \"${{JUNIPER_DATA_URL-__UNSET__}}\" >> {quoted_log}\n" f"printf 'cli_ld=[%s]\\n' \"${{LD_LIBRARY_PATH-__UNSET__}}\" >> {quoted_log}\n" f"printf 'argv=[%s]\\n' \"$*\" >> {quoted_log}\n" f"printf ran > {quoted_ran}\n" "prev=''\nout=''\n" 'for a in "$@"; do [ "$prev" = "--out" ] && out="$a"; prev="$a"; done\n' '[ -n "$out" ] && : > "$out"\n' "exit 0\n"

    def _rerun(self, launch: dict, train: dict | None = None) -> dict:
        return rx._save_model_rerun(train if train is not None else {"d": 8}, "ds-1", "train", DATA_URL, self.out, launch=launch)

    def test_the_recorded_cli_gets_the_run_url_an_empty_library_path_and_zero_hyperparameters(self) -> None:
        """A truthy check would drop ridge 0, and hygiene applied only on the PATH arm would miss this CLI."""
        cli, python = self._plant(self._success_body())
        train = {"d": 0, "theta": None, "ridge": 0.0, "readout": "linear", "rff_features": None, "mlp_patience": 0}
        with mock.patch.dict(os.environ, {"JUNIPER_DATA_URL": POISON_URL, "LD_LIBRARY_PATH": POISON_LIB}):
            result = self._rerun({"cli": str(cli), "python": str(python), "model_version": SERVED_VERSION}, train)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["cli_source"], "launcher")
        self.assertEqual(result["parity"]["model_version"], "match")
        self.assertEqual(
            result["cmd"],
            [str(cli), "train", "--dataset", "ds-1", "--split", "train", "--out", str(self.out), "--d", "0", "--ridge", "0.0", "--readout", "linear", "--mlp-patience", "0"],
        )
        recorded = self.log.read_text(encoding="utf-8")
        for line in (f"probe_url=[{DATA_URL}]", "probe_ld=[]", f"cli_url=[{DATA_URL}]", "cli_ld=[]"):
            self.assertIn(line, recorded)
        self.assertNotIn(POISON_URL, recorded)
        self.assertNotIn(POISON_LIB, recorded)
        self.assertNotIn("--theta", recorded)
        self.assertNotIn("--rff-features", recorded)
        self.assertTrue(self.ran.is_file())
        self.assertFalse(self.path_marker.exists())

    def test_a_non_string_cli_is_not_a_recorded_path(self) -> None:
        """``True`` stringifies to a relative path named True. It is not a CLI, so PATH is the fallback."""
        result = self._rerun({"cli": True, "python": "/served/bin/python", "model_version": SERVED_VERSION})
        self.assertEqual(result["cli_source"], "path")
        self.assertEqual(result["cmd"][0], str(self.sentinel))
        self.assertNotIn("True", result["error"])
        self.assertNotIn("does not fall back to PATH", result["error"])
        self.assertFalse(self.path_marker.exists(), "the parity mismatch must still refuse to run")

    def test_a_non_string_python_or_model_version_is_not_coerced(self) -> None:
        """A number is not the served interpreter or the served version. Coercing it would fail a matching re-run."""
        cli, python = self._plant(self._success_body())
        cases = (
            ("python", {"cli": str(cli), "python": True, "model_version": SERVED_VERSION}),
            ("model_version", {"cli": str(cli), "python": str(python), "model_version": 0.3}),
        )
        for label, launch in cases:
            with self.subTest(field=label):
                self.ran.unlink(missing_ok=True)
                result = self._rerun(launch)
                self.assertTrue(result["ok"], result)
                parity = result["parity"]
                self.assertEqual(parity["interpreter"] if label == "python" else parity["model_version"], "unverified")
                self.assertNotIn("error", result)
                self.assertTrue(self.ran.is_file())
                self.assertFalse(self.path_marker.exists())

    def test_stderr_tail_is_the_last_500_characters(self) -> None:
        payload = "STARTMARKER" + ("x" * 600) + "ENDMARKER"
        cli, python = self._plant(f"printf '%s' {shlex.quote(payload)} >&2\nexit 1\n")
        result = self._rerun({"cli": str(cli), "python": str(python)})
        self.assertFalse(result["ok"])
        self.assertEqual(result["returncode"], 1)
        tail = result["stderr_tail"]
        self.assertEqual(len(tail), 500)
        self.assertTrue(tail.endswith("ENDMARKER"))
        self.assertNotIn("STARTMARKER", tail)


class TestLaunchRecordUrlEdges(unittest.TestCase):
    """``rstrip('/')`` does not make a query, a fragment, or userinfo the recorded service."""

    def test_a_query_fragment_or_userinfo_is_set_aside(self) -> None:
        record = {"cli": "/env/bin/juniper-recurrence"}
        ports = {"recurrence": 8260, "recurrence_launch": record}
        for url in ("http://127.0.0.1:8260?x=1", "http://127.0.0.1:8260#frag", "http://user@127.0.0.1:8260"):
            with self.subTest(url=url):
                kept, note = rx._recurrence_launch_record(ports, url)
                self.assertEqual(kept, {})
                self.assertIsNotNone(note)
                assert note is not None
                self.assertIn("http://127.0.0.1:8260", note)
                self.assertIn(url, note)
                self.assertIn("set aside", note)


class TestModelProbeFailureTail(unittest.TestCase):
    """A long probe failure keeps its tail. The first 300 characters are the warning, not the cause."""

    def _fake(self, body: str) -> Path:
        fake = self.root / "python"
        _write_executable(fake, body)
        return fake

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_a_failing_probe_keeps_the_stripped_stderr_tail(self) -> None:
        # Trailing spaces sit past the cause. Slicing before strip keeps only spaces.
        stderr = "HEADMARKER" + ("m" * 400) + "TAILMARKER" + (" " * 500)
        fake = self._fake(f"#!/bin/bash\nprintf '%s' {shlex.quote(stderr)} >&2\nexit 3\n")
        version, reason = rx._probe_model_version(str(fake), {})
        self.assertIsNone(version)
        self.assertIn("exited 3", reason)
        self.assertIn("TAILMARKER", reason)
        self.assertNotIn("HEADMARKER", reason)

    def test_a_long_non_version_answer_keeps_its_tail(self) -> None:
        # A space is not a version token. The cause is at the end; the head is a long warning.
        answer = "HEADMARKER\n" + ("j" * 400) + "BAD TOKEN\n"
        fake = self._fake(f"#!/bin/bash\nprintf '%s' {shlex.quote(answer)}\nexit 0\n")
        version, reason = rx._probe_model_version(str(fake), {})
        self.assertIsNone(version)
        self.assertIn("printed no version", reason)
        self.assertIn("BAD TOKEN", reason)
        self.assertNotIn("HEADMARKER", reason)


class TestSaveModelFlagMap(unittest.TestCase):
    """A train key with no flag raises KeyError outside the re-run's handler and loses the phase record's error."""

    def test_every_train_key_maps_to_its_cli_flag(self) -> None:
        self.assertEqual(set(rx._SAVE_MODEL_FLAG_MAP), set(rx.TRAIN_KEYS_RECURRENCE))
        for key, flag in rx._SAVE_MODEL_FLAG_MAP.items():
            self.assertEqual(flag, "--" + key.replace("_", "-"), key)


if __name__ == "__main__":
    unittest.main()
