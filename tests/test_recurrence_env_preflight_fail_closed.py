"""
Fail-closed edges of the W0.2 recurrence env preflight that the branch matrix does not reach.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
Version:     1.0.0
License:     MIT License

``tests/test_recurrence_env_preflight.py`` already pins the stale-env refusal, the closure
filter, a crashing probe that prints no protocol, and a missing interpreter path. It cannot
see the edges below, each of which fails open under a one-token edit:

- ``check_pins`` refuses when ``rc != 0 || protocol == 0``. An OK line followed by a non-zero
  exit, or an unrecognised line with exit 0, must still refuse. Dropping either conjunct lets
  a probe that did not finish, or never spoke the protocol, read as a clean env.
- ``check_interpreter`` returns before pip, the pin probe, and the import. A mode ``0644`` file
  and a directory are one finding and are never executed. Removing the short-circuit turns the
  refusal into "pip check could not run" after the kernel has already been asked to exec it.
- The interpreter path is not ``realpath``'d. A venv ``bin/python`` is a symlink to the base
  interpreter; resolving it would judge the base install, which can be clean while the venv is
  not. The banner must name the path the launcher passed.
- Both launchers pass ``--skip`` only when ``SKIP_ENV_PREFLIGHT`` is exactly ``1``. ``true``,
  ``yes``, ``0``, empty, and ``1 `` with a trailing space still refuse. Widening the comparison
  to any non-empty value would serve a stale env for the spelling an operator actually types.
"""

from __future__ import annotations

import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.recurrence_env_fakes import PINS_OK, PREFLIGHT_SCRIPT, SKIP_MARKER, read_calls, write_fake_python
from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENT_STACK = REPO_ROOT / "util" / "experiment_stack.bash"
ISOLATED_STACK = REPO_ROOT / "util" / "isolated_stack.bash"
SCRIPT_TIMEOUT_SECONDS = 60
OK_PIN = "OK juniper-recurrence-model 0.3.0 <0.4.0,>=0.3.0"
PROBE_ABORT = "RuntimeError: probe aborted after the pin"
UNRECOGNISED = "NOTE the probe spoke but established no protocol"
REFUSED_ONE = "ENV PREFLIGHT REFUSED: 1 finding(s); fix the env or pass --skip-env-preflight"


def _run_preflight(*args: str) -> subprocess.CompletedProcess:
    """Run the script with ``bash``, the same way both launchers run the 0644 file."""
    env = RedactedEnv(os.environ)
    for key in ("PYTHONPATH", "PYTHONHOME"):
        env.pop(key, None)
    return subprocess.run(
        ["/bin/bash", str(PREFLIGHT_SCRIPT), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


def _last_line(text: str) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


def _extract_fn(source: str, name: str) -> str:
    """The live ``name() { ... }`` body, so this suite cannot drift from a hand-copied double."""
    match = re.search(rf"^{re.escape(name)}\(\) \{{.*?\n\}}\n", source, flags=re.MULTILINE | re.DOTALL)
    if match is None:
        raise AssertionError(f"{name}() not found")
    return match.group(0)


class _FakePythonCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.calls_log = self.root / "calls.log"

    def fake(self, **kwargs) -> Path:
        kwargs.setdefault("calls_log", self.calls_log)
        return write_fake_python(self.root / "env" / "bin" / "python", **kwargs)


class TestPinProbeFailClosed(_FakePythonCase):
    """The pin probe's exit status and its protocol are independent. Either one missing refuses."""

    def test_an_ok_line_then_a_non_zero_exit_still_refuses(self) -> None:
        python = self.fake(pins=(OK_PIN, PROBE_ABORT), pins_rc=1)
        result = _run_preflight("--python", str(python))
        out = result.stdout
        self.assertEqual(result.returncode, 1, msg=out + result.stderr)
        self.assertIn(f"ENV PREFLIGHT: pin ok: juniper-recurrence-model 0.3.0 satisfies juniper-recurrence-model<0.4.0,>=0.3.0\n", out)
        self.assertIn(f"ENV PREFLIGHT: pin probe also said: {PROBE_ABORT}\n", out)
        self.assertIn(f"FINDING: version-pin probe failed (exit 1): {PROBE_ABORT}\n", out)
        self.assertNotIn(f"FINDING: {OK_PIN}", out)
        self.assertNotIn(f"FINDING: {PROBE_ABORT}\n", out)
        self.assertEqual(_last_line(out), REFUSED_ONE)
        self.assertEqual(len(read_calls(self.calls_log)), 3, "pip, the probe, and the import still run")

    def test_an_unrecognised_line_with_exit_zero_still_refuses(self) -> None:
        python = self.fake(pins=(UNRECOGNISED,), pins_rc=0)
        result = _run_preflight("--python", str(python))
        out = result.stdout
        self.assertEqual(result.returncode, 1, msg=out + result.stderr)
        self.assertIn(f"ENV PREFLIGHT: pin probe also said: {UNRECOGNISED}\n", out)
        self.assertIn(f"FINDING: version-pin probe failed (exit 0): {UNRECOGNISED}\n", out)
        self.assertNotIn(f"FINDING: {UNRECOGNISED}\n", out)
        self.assertEqual(_last_line(out), REFUSED_ONE)


class TestInterpreterIsNotExecuted(_FakePythonCase):
    """A path that is not an executable file is one finding, and the three probes never start."""

    def _assert_one_finding_and_no_probe(self, python: Path) -> None:
        refused = _run_preflight("--python", str(python))
        self.assertEqual(refused.returncode, 1, msg=refused.stdout + refused.stderr)
        self.assertIn(f"FINDING: interpreter not found or not executable: {python}\n", refused.stdout)
        self.assertNotIn("pip check", refused.stdout)
        self.assertNotIn("could not run", refused.stdout)
        self.assertNotIn("import ok", refused.stdout)
        self.assertNotIn("import probe", refused.stdout)
        self.assertEqual(_last_line(refused.stdout), REFUSED_ONE)
        self.assertEqual(read_calls(self.calls_log), [])
        skipped = _run_preflight("--python", str(python), "--skip")
        self.assertEqual(skipped.returncode, 0, msg=skipped.stdout + skipped.stderr)
        self.assertIn(f"{SKIP_MARKER} interpreter not found or not executable: {python}\n", skipped.stdout)
        self.assertNotIn("pip check", skipped.stdout)
        self.assertEqual(read_calls(self.calls_log), [], "--skip must not execute the probes either")

    def test_a_non_executable_file_is_not_run(self) -> None:
        python = self.fake(pins=PINS_OK)
        python.chmod(0o644)
        self._assert_one_finding_and_no_probe(python)

    def test_a_directory_is_not_run(self) -> None:
        python = self.root / "env" / "bin" / "python"
        python.parent.mkdir(parents=True)
        python.mkdir()
        python.chmod(0o755)
        self._assert_one_finding_and_no_probe(python)


class TestSymlinkIsNotResolved(_FakePythonCase):
    """The path on the banner is the path the launcher passed, not the symlink target."""

    def test_a_symlink_to_the_interpreter_is_judged_as_the_link(self) -> None:
        real = self.root / "base" / "python"
        write_fake_python(real, pins=PINS_OK, calls_log=self.calls_log)
        link = self.root / "venv" / "bin" / "python"
        link.parent.mkdir(parents=True)
        link.symlink_to(real)
        result = _run_preflight("--python", str(link))
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn(f"ENV PREFLIGHT: juniper-recurrence env preflight (plan W0.2) of {link}\n", result.stdout)
        self.assertNotIn(str(real), result.stdout)
        self.assertEqual(len(read_calls(self.calls_log)), 3)


class TestSkipIsExactlyOne(unittest.TestCase):
    """``--skip`` is passed only for the value ``1``. Every other spelling still refuses."""

    NOT_SKIP = ("true", "yes", "0", "", "1 ", "2")

    def _run(self, script: Path, value: str) -> subprocess.CompletedProcess:
        source = script.read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            log_dir = root / "logs"
            log_dir.mkdir()
            stub = root / "preflight-stub.bash"
            stub.write_text("#!/bin/bash\nprintf 'stub-args:%s\\n' \"$*\"\nif [[ \" $* \" == *\" --skip \"* ]]; then\n    exit 0\nfi\nexit 1\n")
            stub.chmod(0o755)
            harness = (
                "set -u\n"
                f"SCRIPT_NAME={script.name}\n"
                f"LOG_DIR={log_dir}\n"
                "log() { printf '%s\\n' \"[${SCRIPT_NAME}] $*\"; }\n"
                + _extract_fn(source, "log_launch")
                + _extract_fn(source, "run_env_preflight")
                + "ENV_PREFLIGHT=\"${STUB}\"\n"
                + "SKIP_ENV_PREFLIGHT=\"${SKIP_VALUE}\"\n"
                + "set +e\n"
                + "run_env_preflight /opt/env/bin/python\n"
                + "status=$?\n"
                + "printf 'STATUS=%s\\n' \"${status}\"\n"
            )
            env = RedactedEnv(os.environ, STUB=str(stub), SKIP_VALUE=value)
            return subprocess.run(
                ["/bin/bash", "-c", harness],
                capture_output=True,
                text=True,
                env=env,
                timeout=SCRIPT_TIMEOUT_SECONDS,
            )

    def test_only_the_digit_one_skips_in_both_launchers(self) -> None:
        for script in (EXPERIMENT_STACK, ISOLATED_STACK):
            for value in self.NOT_SKIP:
                with self.subTest(script=script.name, value=value):
                    result = self._run(script, value)
                    self.assertIn("STATUS=1\n", result.stdout, msg=result.stdout + result.stderr)
                    # The refusal text names the flag. The stub's own argv is what proves it was not passed.
                    self.assertIn("stub-args:--python /opt/env/bin/python\n", result.stdout)
                    self.assertNotIn("stub-args:--python /opt/env/bin/python --skip\n", result.stdout)
                    self.assertIn("serve NOT started", result.stdout)
            with self.subTest(script=script.name, value="1"):
                result = self._run(script, "1")
                self.assertIn("STATUS=0\n", result.stdout, msg=result.stdout + result.stderr)
                self.assertIn("stub-args:--python /opt/env/bin/python --skip\n", result.stdout)
                self.assertNotIn("serve NOT started", result.stdout)


if __name__ == "__main__":
    unittest.main()
