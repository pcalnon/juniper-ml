"""
Tests for util/recurrence_env_preflight.bash

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
Version:     1.0.0
License:     MIT License

W0.2 of ``notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md``
(closes F-E2): before ``serve``, both host launchers now run this preflight against the
interpreter the recurrence console script runs under. On 2026-10-03 the default env served a
stale ``juniper-recurrence-model`` 0.1.5 (no ``derive_full_split``) and ``juniper-service-core``
0.5.0 under an app pinned ``>=0.3.0,<0.4.0`` / ``>=0.6.0,<0.8.0``; ``/v1/health/ready`` passed and
every ``POST /v1/crossval`` 422'd (F-E1).

What is pinned here, and why each matters:

- the plan's acceptance pair -- a synthetic stale env REFUSES with its text and exit code, and
  unrelated ``pip check`` noise (the env's CUDA conflicts) does NOT refuse;
- ``--skip`` still runs every check and prints each finding as a loud WARNING, exit 0;
- a violated pin refuses on its own, naming package, installed version and specifier;
- the closure filter in both directions (requiring side, installed side, missing dependency,
  platform, pip's parse-problem warning, PEP 503 name forms) and its fail-closed edges (pip
  that will not run, a probe that crashes, a reworded closure line, a missing interpreter);
- every interpreter call passes ``-s`` FIRST and runs from ``/``, so neither a ``~/.local``
  package nor the caller's working directory can mask a gap in the env.

Two doubles (``tests/recurrence_env_fakes.py``): a fake ``python`` with canned answers for the
branch matrix, and a REAL offline venv whose ``pip check`` / pin probe / import run for real, so
the script is also checked against pip's actual output and the probe's actual Python. Hermetic:
no network, no conda, nothing outside a temp dir.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.recurrence_env_fakes import (
    CUDA_BINDINGS_LINE,
    CUDA_CORE_LINE,
    IMPORT_ERROR_LINE,
    IMPORT_PROBE,
    MODEL_PIN_LINE,
    PINS_OK,
    PINS_STALE,
    PREFLIGHT_SCRIPT,
    SERVICE_CORE_PIN_LINE,
    SKIP_MARKER,
    host_packaging_dir,
    host_pip_dir,
    make_synthetic_venv,
    read_calls,
    write_fake_python,
)
from tests.redacted_env import RedactedEnv

SCRIPT_TIMEOUT_SECONDS = 60
REFUSED_STALE = "ENV PREFLIGHT REFUSED: 5 finding(s); fix the env or pass --skip-env-preflight"


def _run_preflight(*args: str, cwd: "Path | None" = None) -> subprocess.CompletedProcess:
    """Run the script with ``bash`` -- it is committed 0644, exactly as the launchers run it."""
    env = RedactedEnv(os.environ)
    # A caller's PYTHONPATH reaches the interpreter (`-s` does not stop it); keep the doubles hermetic.
    for key in ("PYTHONPATH", "PYTHONHOME"):
        env.pop(key, None)
    return subprocess.run(["/bin/bash", str(PREFLIGHT_SCRIPT), *args], capture_output=True, text=True, env=env, cwd=cwd, timeout=SCRIPT_TIMEOUT_SECONDS)


def _last_line(text: str) -> str:
    lines = [line for line in text.splitlines() if line.strip()]
    return lines[-1] if lines else ""


class _FakePythonCase(unittest.TestCase):
    """A temp dir per test, holding the fake interpreter and its call log."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.calls_log = self.root / "calls.log"

    def fake(self, **kwargs) -> Path:
        kwargs.setdefault("calls_log", self.calls_log)
        return write_fake_python(self.root / "env" / "bin" / "python", **kwargs)


class TestStaleEnvRefuses(_FakePythonCase):
    """Acceptance (a): the F-E1 env -- two closure pip-check lines, stale pins, no derive_full_split."""

    def _stale(self) -> Path:
        return self.fake(pip_check=(CUDA_BINDINGS_LINE, MODEL_PIN_LINE, SERVICE_CORE_PIN_LINE), pins=PINS_STALE, import_error=IMPORT_ERROR_LINE)

    def test_refuses_with_exit_one_and_the_summary_line(self) -> None:
        result = _run_preflight("--python", str(self._stale()))
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertEqual(_last_line(result.stdout), REFUSED_STALE)

    def test_prints_both_juniper_pip_lines_verbatim(self) -> None:
        out = _run_preflight("--python", str(self._stale())).stdout
        self.assertIn(f"FINDING: {MODEL_PIN_LINE}\n", out)
        self.assertIn(f"FINDING: {SERVICE_CORE_PIN_LINE}\n", out)

    def test_prints_the_import_failure_verbatim(self) -> None:
        out = _run_preflight("--python", str(self._stale())).stdout
        self.assertIn("derive_full_split", out)
        self.assertIn(f"FINDING: import probe '{IMPORT_PROBE}' failed (exit 1): {IMPORT_ERROR_LINE}\n", out)

    def test_names_both_violated_pins(self) -> None:
        out = _run_preflight("--python", str(self._stale())).stdout
        self.assertIn("FINDING: version pin: juniper-recurrence-model 0.1.5 is installed; juniper-recurrence 0.5.0 requires juniper-recurrence-model<0.4.0,>=0.3.0\n", out)
        self.assertIn("FINDING: version pin: juniper-service-core 0.5.0 is installed; juniper-recurrence 0.5.0 requires juniper-service-core<0.8.0,>=0.6.0\n", out)

    def test_the_unrelated_cuda_line_is_reported_but_is_not_a_finding(self) -> None:
        out = _run_preflight("--python", str(self._stale())).stdout
        self.assertIn(f"ENV PREFLIGHT: unrelated to recurrence (not a finding): {CUDA_BINDINGS_LINE}\n", out)
        self.assertNotIn(f"FINDING: {CUDA_BINDINGS_LINE}", out)
        self.assertIn("ENV PREFLIGHT: pip check: 2 recurrence-closure line(s), 1 unrelated line(s)\n", out)


class TestUnrelatedNoiseDoesNotRefuse(_FakePythonCase):
    """Acceptance (b): JuniperCascor1's CUDA conflicts make pip check exit 1 -- and are not recurrence's."""

    def test_cuda_only_pip_check_passes(self) -> None:
        python = self.fake(pip_check=(CUDA_BINDINGS_LINE, CUDA_CORE_LINE), pins=PINS_OK)
        result = _run_preflight("--python", str(python))
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertNotIn("FINDING", result.stdout)
        self.assertIn(f"ENV PREFLIGHT: unrelated to recurrence (not a finding): {CUDA_BINDINGS_LINE}\n", result.stdout)
        self.assertIn(f"ENV PREFLIGHT: unrelated to recurrence (not a finding): {CUDA_CORE_LINE}\n", result.stdout)
        self.assertIn("ENV PREFLIGHT: pip check: 0 recurrence-closure line(s), 2 unrelated line(s)\n", result.stdout)
        self.assertEqual(_last_line(result.stdout), "ENV PREFLIGHT OK: no findings")

    def test_an_unrelated_missing_dependency_passes(self) -> None:
        python = self.fake(pip_check=("torch 2.11.0 requires nvidia-nccl-cu13, which is not installed.",), pins=PINS_OK)
        result = _run_preflight("--python", str(python))
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_an_unrelated_parse_problem_is_not_read_as_pip_failing_to_run(self) -> None:
        # pip check exits 1 on a metadata parse problem and prints only this warning; it ran.
        python = self.fake(pip_check=("WARNING: Error parsing dependencies of cuda-python: Invalid requirement: 'cuda-bindings~='",), pins=PINS_OK)
        result = _run_preflight("--python", str(python))
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertNotIn("could not run", result.stdout)


class TestSkipWarnsLoudlyAndPasses(_FakePythonCase):
    """Acceptance (c): --skip runs every check, prints every finding as a WARNING, exits 0."""

    def test_stale_env_with_skip_exits_zero_with_every_finding_as_a_warning(self) -> None:
        python = self.fake(pip_check=(CUDA_BINDINGS_LINE, MODEL_PIN_LINE, SERVICE_CORE_PIN_LINE), pins=PINS_STALE, import_error=IMPORT_ERROR_LINE)
        result = _run_preflight("--python", str(python), "--skip")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        out = result.stdout
        self.assertIn(f"{SKIP_MARKER} {MODEL_PIN_LINE}\n", out)
        self.assertIn(f"{SKIP_MARKER} {SERVICE_CORE_PIN_LINE}\n", out)
        self.assertIn(f"{SKIP_MARKER} import probe '{IMPORT_PROBE}' failed (exit 1): {IMPORT_ERROR_LINE}\n", out)
        self.assertEqual(out.count(SKIP_MARKER), 6, msg="five findings plus the summary, all in the WARNING form")
        self.assertNotIn("FINDING:", out)
        self.assertNotIn("REFUSED", out)
        self.assertEqual(_last_line(out), f"{SKIP_MARKER} 5 finding(s) ignored; juniper-recurrence will serve from an env that FAILED its preflight")

    def test_skip_still_runs_every_check(self) -> None:
        python = self.fake(pip_check=(SERVICE_CORE_PIN_LINE,), pins=PINS_STALE)
        _run_preflight("--python", str(python), "--skip")
        self.assertEqual(len(read_calls(self.calls_log)), 3, msg="--skip must not short-circuit a check")

    def test_skip_on_a_clean_env_says_it_had_nothing_to_override(self) -> None:
        result = _run_preflight("--python", str(self.fake(pins=PINS_OK)), "--skip")
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(_last_line(result.stdout), "ENV PREFLIGHT OK: no findings (--skip had nothing to override)")


class TestPinViolationAloneRefuses(_FakePythonCase):
    """Acceptance (d): a clean pip check and a good import do not outvote a violated pin."""

    def test_service_core_below_its_floor_refuses_naming_package_version_and_specifier(self) -> None:
        python = self.fake(pins=("APP 0.5.0 packaging", "OK juniper-recurrence-model 0.3.0 <0.4.0,>=0.3.0", "BAD juniper-service-core 0.5.0 <0.8.0,>=0.6.0"))
        result = _run_preflight("--python", str(python))
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("FINDING: version pin: juniper-service-core 0.5.0 is installed; juniper-recurrence 0.5.0 requires juniper-service-core<0.8.0,>=0.6.0\n", result.stdout)
        self.assertEqual(_last_line(result.stdout), "ENV PREFLIGHT REFUSED: 1 finding(s); fix the env or pass --skip-env-preflight")

    def test_a_missing_pinned_distribution_refuses(self) -> None:
        python = self.fake(pins=("APP 0.5.0 packaging", "MISSING juniper-recurrence-model <0.4.0,>=0.3.0", "OK juniper-service-core 0.7.0 <0.8.0,>=0.6.0"))
        result = _run_preflight("--python", str(python))
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("FINDING: version pin: juniper-recurrence-model is not installed; juniper-recurrence 0.5.0 requires juniper-recurrence-model<0.4.0,>=0.3.0\n", result.stdout)

    def test_an_unparseable_installed_version_refuses(self) -> None:
        python = self.fake(pins=("APP 0.5.0 packaging", "INVALID juniper-recurrence-model not-a-version <0.4.0,>=0.3.0", "OK juniper-service-core 0.7.0 <0.8.0,>=0.6.0"))
        self.assertEqual(_run_preflight("--python", str(python)).returncode, 1)

    def test_an_app_without_metadata_refuses(self) -> None:
        result = _run_preflight("--python", str(self.fake(pins=("NOAPP",))))
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("juniper-recurrence has no distribution metadata in this interpreter", result.stdout)

    def test_a_crashing_pin_probe_refuses_with_its_exception_line(self) -> None:
        python = self.fake(pins=("Traceback (most recent call last):", "RuntimeError: boom"), pins_rc=1)
        result = _run_preflight("--python", str(python))
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("FINDING: version-pin probe failed (exit 1): RuntimeError: boom\n", result.stdout)

    def test_no_packaging_falls_back_to_pip_checks_verdict(self) -> None:
        clean = _run_preflight("--python", str(self.fake(pins=("NOPACKAGING",))))
        self.assertEqual(clean.returncode, 0, msg=clean.stdout + clean.stderr)
        self.assertIn("the pin check falls back to pip check's verdict", clean.stdout)
        stale = _run_preflight("--python", str(self.fake(pip_check=(SERVICE_CORE_PIN_LINE,), pins=("NOPACKAGING",))))
        self.assertEqual(stale.returncode, 1, msg=stale.stdout + stale.stderr)
        self.assertIn(f"FINDING: {SERVICE_CORE_PIN_LINE}\n", stale.stdout)

    def test_an_app_that_pins_nothing_is_said_and_does_not_refuse(self) -> None:
        python = self.fake(pins=("APP 0.5.0 packaging", "NOREQ juniper-recurrence-model", "NOREQ juniper-service-core"))
        result = _run_preflight("--python", str(python))
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("declares no unconditional requirement on juniper-service-core", result.stdout)


class TestClosureFilter(_FakePythonCase):
    """The scope rule both ways: the requiring side OR the installed side, PEP 503 names, fail-closed edges."""

    def _verdict(self, *pip_lines: str, rc: "int | None" = None) -> subprocess.CompletedProcess:
        return _run_preflight("--python", str(self.fake(pip_check=pip_lines, pip_check_rc=rc, pins=PINS_OK)))

    def test_a_closure_package_on_the_installed_side_refuses(self) -> None:
        line = "juniper-canopy 0.8.1 has requirement juniper-service-core>=0.7.0, but you have juniper-service-core 0.5.0."
        result = self._verdict(line)
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        self.assertIn(f"FINDING: {line}\n", result.stdout)

    def test_a_missing_closure_dependency_refuses(self) -> None:
        line = "juniper-recurrence 0.5.0 requires juniper-observability, which is not installed."
        self.assertEqual(self._verdict(line).returncode, 1)

    def test_a_closure_distribution_unsupported_on_this_platform_refuses(self) -> None:
        self.assertEqual(self._verdict("juniper-model-core 0.3.2 is not supported on this platform").returncode, 1)

    def test_a_closure_parse_problem_refuses(self) -> None:
        self.assertEqual(self._verdict("WARNING: Error parsing dependencies of juniper-data-client: Invalid requirement").returncode, 1)

    def test_every_closure_member_is_in_scope(self) -> None:
        for dist in ("juniper-recurrence", "juniper-recurrence-model", "juniper-recurrence-client", "juniper-service-core", "juniper-observability", "juniper-data-client", "juniper-model-core"):
            with self.subTest(dist=dist):
                self.assertEqual(self._verdict(f"{dist} 9.9.9 has requirement numpy<2, but you have numpy 2.3.0.").returncode, 1)

    def test_a_non_closure_juniper_package_is_out_of_scope(self) -> None:
        line = "juniper-cascor 0.11.0 has requirement juniper-cascor-client>=0.9, but you have juniper-cascor-client 0.8.0."
        self.assertEqual(self._verdict(line).returncode, 0)

    def test_pep_503_name_forms_are_recognised(self) -> None:
        for name in ("Juniper_Service.Core", "JUNIPER--RECURRENCE__MODEL"):
            with self.subTest(name=name):
                self.assertEqual(self._verdict(f"{name} 0.5.0 is not supported on this platform").returncode, 1)

    def test_a_reworded_closure_line_still_refuses(self) -> None:
        # Outside pip's grammar (a later pip may reword); led by a closure name, so fail closed.
        line = "juniper-service-core 0.5.0 conflicts with juniper-recurrence 0.5.0"
        result = self._verdict(CUDA_BINDINGS_LINE, line)
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        self.assertIn(f"FINDING: {line}\n", result.stdout)

    def test_pip_that_cannot_run_refuses(self) -> None:
        result = self._verdict("/opt/fake-env/bin/python: No module named pip", rc=1)
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        self.assertIn("FINDING: pip check could not run (exit 1): /opt/fake-env/bin/python: No module named pip\n", result.stdout)

    def test_a_clean_pip_check_is_not_a_finding(self) -> None:
        result = self._verdict()
        self.assertEqual(result.returncode, 0, msg=result.stdout)
        self.assertIn("ENV PREFLIGHT: pip check: 0 recurrence-closure line(s), 0 unrelated line(s)\n", result.stdout)


class TestInterpreterHygiene(_FakePythonCase):
    """`-s` first on every call, `/` as the working directory, and the interpreter itself checked."""

    def test_every_call_passes_dash_s_first(self) -> None:
        _run_preflight("--python", str(self.fake(pins=PINS_OK)))
        calls = read_calls(self.calls_log)
        self.assertEqual(len(calls), 3, msg=calls)
        for call in calls:
            self.assertTrue(call.startswith("call: [-s] "), msg=call)
        self.assertTrue(any("[-m] [pip]" in call for call in calls), msg=calls)
        self.assertTrue(any(f"[{IMPORT_PROBE}]" in call for call in calls), msg=calls)

    def test_every_call_runs_from_root_not_the_callers_directory(self) -> None:
        _run_preflight("--python", str(self.fake(pins=PINS_OK)), cwd=self.root)
        calls = read_calls(self.calls_log)
        self.assertEqual(len(calls), 3, msg=calls)
        for call in calls:
            self.assertIn(" cwd=/ ", call)

    def test_a_relative_interpreter_path_is_resolved_against_the_callers_directory(self) -> None:
        # The script does `cd /` before its probes, so a relative path must be made absolute first.
        self.fake(pins=PINS_OK)
        result = _run_preflight("--python", "env/bin/python", cwd=self.root)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        # bash takes $PWD from getcwd() here (the inherited PWD names another directory): physical path.
        self.assertIn(f"preflight (plan W0.2) of {self.root.resolve()}/env/bin/python\n", result.stdout)
        self.assertEqual(len(read_calls(self.calls_log)), 3)

    def test_a_missing_interpreter_refuses_and_skip_downgrades_it(self) -> None:
        missing = str(self.root / "nowhere" / "python")
        refused = _run_preflight("--python", missing)
        self.assertEqual(refused.returncode, 1, msg=refused.stdout)
        self.assertIn(f"FINDING: interpreter not found or not executable: {missing}\n", refused.stdout)
        self.assertEqual(_last_line(refused.stdout), "ENV PREFLIGHT REFUSED: 1 finding(s); fix the env or pass --skip-env-preflight")
        skipped = _run_preflight("--python", missing, "--skip")
        self.assertEqual(skipped.returncode, 0, msg=skipped.stdout)
        self.assertIn(f"{SKIP_MARKER} interpreter not found or not executable: {missing}\n", skipped.stdout)


class TestCommandLine(unittest.TestCase):
    """Misuse exits 2; --help exits 0."""

    def test_help(self) -> None:
        result = _run_preflight("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("Usage: bash recurrence_env_preflight.bash --python PATH [--skip]", result.stdout)

    def test_misuse_exits_two(self) -> None:
        for args in ((), ("--skip",), ("--python",), ("--python", "--skip"), ("--bogus",)):
            with self.subTest(args=args):
                result = _run_preflight(*args)
                self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
                self.assertIn("Usage:", result.stderr)


class TestRealInterpreterSyntheticEnv(unittest.TestCase):
    """The plan's own acceptance shape, for real: a venv whose pip check, pin probe and import all run.

    The fake proves the branches; this proves the script reads pip's ACTUAL output and that the
    probe's ACTUAL Python evaluates the pins -- through pip's vendored ``packaging`` here, since
    a fresh venv has no top-level one, and through ``packaging`` itself when it is lent.
    """

    def setUp(self) -> None:
        if host_pip_dir() is None:
            self.skipTest("the test interpreter has no pip to lend the synthetic venv")
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_the_synthetic_stale_env_is_refused_with_pips_own_text(self) -> None:
        python = make_synthetic_venv(self.root, model_version="0.1.5", service_core_version="0.5.0", derive_full_split=False)
        result = _run_preflight("--python", str(python))
        out = result.stdout
        self.assertEqual(result.returncode, 1, msg=out + result.stderr)
        # pip's own lines, byte for byte the ones the audit recorded for JuniperCascor1.
        self.assertIn(f"FINDING: {MODEL_PIN_LINE}\n", out)
        self.assertIn(f"FINDING: {SERVICE_CORE_PIN_LINE}\n", out)
        self.assertIn(f"ENV PREFLIGHT: unrelated to recurrence (not a finding): {CUDA_BINDINGS_LINE}\n", out)
        self.assertIn("ENV PREFLIGHT: pins declared by juniper-recurrence 0.5.0 (evaluated with pip._vendor.packaging)\n", out)
        self.assertIn("FINDING: version pin: juniper-recurrence-model 0.1.5 is installed; juniper-recurrence 0.5.0 requires juniper-recurrence-model<0.4.0,>=0.3.0\n", out)
        self.assertIn("FINDING: version pin: juniper-service-core 0.5.0 is installed; juniper-recurrence 0.5.0 requires juniper-service-core<0.8.0,>=0.6.0\n", out)
        self.assertIn("ImportError: cannot import name 'derive_full_split' from 'juniper_recurrence_model.data'", out)
        self.assertEqual(_last_line(out), REFUSED_STALE)

    def test_the_repaired_env_passes_despite_the_cuda_noise(self) -> None:
        python = make_synthetic_venv(self.root, model_version="0.3.0", service_core_version="0.7.0", derive_full_split=True)
        result = _run_preflight("--python", str(python))
        out = result.stdout
        self.assertEqual(result.returncode, 0, msg=out + result.stderr)
        self.assertIn(f"ENV PREFLIGHT: unrelated to recurrence (not a finding): {CUDA_BINDINGS_LINE}\n", out)
        # The extra-gated `juniper-recurrence-model[torch]` line is not a pin serve needs.
        self.assertIn("ENV PREFLIGHT: pin ok: juniper-recurrence-model 0.3.0 satisfies juniper-recurrence-model<0.4.0,>=0.3.0\n", out)
        self.assertIn("ENV PREFLIGHT: pin ok: juniper-service-core 0.7.0 satisfies juniper-service-core<0.8.0,>=0.6.0\n", out)
        self.assertIn(f"ENV PREFLIGHT: import ok: {IMPORT_PROBE}\n", out)
        self.assertEqual(_last_line(out), "ENV PREFLIGHT OK: no findings")

    def test_the_packaging_distribution_is_preferred_when_importable(self) -> None:
        if host_packaging_dir() is None:
            self.skipTest("the test interpreter has no packaging to lend the synthetic venv")
        python = make_synthetic_venv(self.root, model_version="0.3.0", service_core_version="0.5.0", derive_full_split=True, top_level_packaging=True)
        result = _run_preflight("--python", str(python))
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn("ENV PREFLIGHT: pins declared by juniper-recurrence 0.5.0 (evaluated with packaging)\n", result.stdout)
        self.assertIn("FINDING: version pin: juniper-service-core 0.5.0 is installed; juniper-recurrence 0.5.0 requires juniper-service-core<0.8.0,>=0.6.0\n", result.stdout)


if __name__ == "__main__":
    unittest.main()
