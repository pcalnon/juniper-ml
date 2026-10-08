"""The W0.2 pin probe's real Python, which a canned protocol cannot see.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon
Version:     1.0.0
License:     MIT License

``tests/test_recurrence_env_preflight.py`` drives ``util/recurrence_env_preflight.bash`` with a
fake interpreter that prints OK/BAD/INVALID/NOREQ itself, and its real-venv cases only install
final versions (0.1.5, 0.5.0, 0.3.0, 0.7.0). Neither can tell whether the probe embedded in
the script actually evaluates versions. These tests build the same offline venv and then
rewrite the installed metadata, so a broken PEP 503 match, a swallowed marker, or a probe that
crashes on one bad requirement fails here. ``prereleases=True`` matters only where the probe
resolves packaging < 26: packaging 26 made ``SpecifierSet.contains`` accept a prerelease by
default, and the synthetic venv borrows the test interpreter's pip (and its vendored
packaging), so on a current pip the prerelease arm pins the outcome and a text check pins the
flag itself -- the env the probe judges may still carry an older packaging.

Hermetic: no network, no conda, nothing outside a temp dir. Skips when the test interpreter
has no pip to lend the venv.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from collections.abc import Sequence
from pathlib import Path

from tests.recurrence_env_fakes import PREFLIGHT_SCRIPT, host_pip_dir, make_synthetic_venv
from tests.redacted_env import RedactedEnv

SCRIPT_TIMEOUT_SECONDS = 60

_MODEL_FLOOR = "juniper-recurrence-model<0.4.0,>=0.3.0"
_SERVICE_FLOOR = "juniper-service-core<0.8.0,>=0.6.0"


def _run_preflight(python: Path) -> subprocess.CompletedProcess[str]:
    """Run the real script with ``bash``, the way both launchers do."""
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


def _site(python: Path) -> Path:
    result = subprocess.run(
        [str(python), "-c", "import sysconfig; print(sysconfig.get_paths()['purelib'])"],
        check=True,
        capture_output=True,
        text=True,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )
    return Path(result.stdout.strip())


def _rewrite_requires(python: Path, requires: Sequence[str]) -> None:
    """Replace juniper-recurrence's declared requirements. The probe reads these, not the helper's."""
    meta = next(_site(python).glob("juniper_recurrence-*.dist-info")) / "METADATA"
    lines = [line for line in meta.read_text().splitlines() if not line.startswith("Requires-Dist:")]
    lines.extend(f"Requires-Dist: {req}" for req in requires)
    meta.write_text("\n".join(lines) + "\n")


def _set_version(python: Path, dist_glob: str, version: str) -> None:
    """Overwrite the Version field. importlib.metadata reports this string unvalidated."""
    meta = next(_site(python).glob(dist_glob)) / "METADATA"
    lines = [f"Version: {version}" if line.startswith("Version:") else line for line in meta.read_text().splitlines()]
    meta.write_text("\n".join(lines) + "\n")


class TestPinProbeEvaluation(unittest.TestCase):
    """Behaviors of the embedded probe. The script's branch matrix is covered elsewhere."""

    def setUp(self) -> None:
        if host_pip_dir() is None:
            self.skipTest("the test interpreter has no pip to lend the synthetic venv")
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def _venv(self, *, model_version: str, service_core_version: str) -> Path:
        return make_synthetic_venv(
            self.root,
            model_version=model_version,
            service_core_version=service_core_version,
            derive_full_split=True,
            cuda_noise=False,
        )

    def test_a_prerelease_inside_the_specifier_is_a_satisfied_pin(self) -> None:
        # packaging < 26 excludes 0.3.1a1 from >=0.3.0,<0.4.0 unless prereleases=True, and
        # dropping that flag refuses a model serve can import. packaging >= 26 accepts it by
        # default, so under a current pip the run below pins the outcome and this pins the flag.
        self.assertIn("req.specifier.contains(Version(installed), prereleases=True)", PREFLIGHT_SCRIPT.read_text(encoding="utf-8"))
        python = self._venv(model_version="0.3.1a1", service_core_version="0.7.0")
        result = _run_preflight(python)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn(
            "ENV PREFLIGHT: pin ok: juniper-recurrence-model 0.3.1a1 satisfies juniper-recurrence-model<0.4.0,>=0.3.0\n",
            result.stdout,
        )
        self.assertNotIn("FINDING:", result.stdout)

    def test_a_noncanonical_requirement_name_still_matches_the_pin(self) -> None:
        # The probe's own canonical(), not importlib's. A lowercasing-only match
        # prints NOREQ and the version-pin finding disappears; pip check would still refuse.
        python = self._venv(model_version="0.3.0", service_core_version="0.5.0")
        _rewrite_requires(python, [_MODEL_FLOOR, "Juniper_Service.Core<0.8.0,>=0.6.0"])
        result = _run_preflight(python)
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn(
            "FINDING: version pin: juniper-service-core 0.5.0 is installed; juniper-recurrence 0.5.0 requires juniper-service-core<0.8.0,>=0.6.0\n",
            result.stdout,
        )
        self.assertNotIn("declares no unconditional requirement on juniper-service-core", result.stdout)

    def test_a_malformed_requirement_is_skipped_and_the_real_violation_remains(self) -> None:
        # The bad line is first. An uncaught Requirement() error dies before the real pin
        # and the script reports "version-pin probe failed" instead of the violation.
        python = self._venv(model_version="0.3.0", service_core_version="0.5.0")
        _rewrite_requires(python, ["!!!not a requirement", _MODEL_FLOOR, _SERVICE_FLOOR])
        result = _run_preflight(python)
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn(
            "FINDING: version pin: juniper-service-core 0.5.0 is installed; juniper-recurrence 0.5.0 requires juniper-service-core<0.8.0,>=0.6.0\n",
            result.stdout,
        )
        self.assertNotIn("version-pin probe failed", result.stdout)

    def test_both_requirements_on_one_distribution_are_checked(self) -> None:
        # 0.3.0 satisfies the floor and violates !=0.3.0. Keeping only the first requirement
        # still exits 1, because pip check sees the second pin; the version-pin line is the probe's.
        python = self._venv(model_version="0.3.0", service_core_version="0.7.0")
        _rewrite_requires(python, [_MODEL_FLOOR, "juniper-recurrence-model!=0.3.0", _SERVICE_FLOOR])
        result = _run_preflight(python)
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn(
            "ENV PREFLIGHT: pin ok: juniper-recurrence-model 0.3.0 satisfies juniper-recurrence-model<0.4.0,>=0.3.0\n",
            result.stdout,
        )
        self.assertIn(
            "FINDING: version pin: juniper-recurrence-model 0.3.0 is installed; juniper-recurrence 0.5.0 requires juniper-recurrence-model!=0.3.0\n",
            result.stdout,
        )

    def test_an_unmatched_environment_marker_is_not_a_pin(self) -> None:
        # python_version < "3.0" is false here. Treating every marker as unconditional
        # refuses 0.5.0. Skipping every marker is the other test.
        python = self._venv(model_version="0.3.0", service_core_version="0.5.0")
        _rewrite_requires(python, [_MODEL_FLOOR, 'juniper-service-core<0.8.0,>=0.6.0; python_version < "3.0"'])
        result = _run_preflight(python)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn(
            "ENV PREFLIGHT: juniper-recurrence declares no unconditional requirement on juniper-service-core; no pin to check\n",
            result.stdout,
        )
        self.assertNotIn("FINDING:", result.stdout)

    def test_a_matched_environment_marker_with_a_violated_specifier_refuses(self) -> None:
        # python_version >= "3.0" is true here. Skipping every marker prints NOREQ and
        # pip check is what refuses, so the version-pin line is the probe's.
        python = self._venv(model_version="0.3.0", service_core_version="0.7.0")
        _rewrite_requires(python, [_MODEL_FLOOR, 'juniper-service-core<0.1; python_version >= "3.0"'])
        result = _run_preflight(python)
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn(
            "FINDING: version pin: juniper-service-core 0.7.0 is installed; juniper-recurrence 0.5.0 requires juniper-service-core<0.1\n",
            result.stdout,
        )
        self.assertNotIn("declares no unconditional requirement on juniper-service-core", result.stdout)

    def test_a_non_pep440_installed_version_names_the_specifier_it_could_not_check(self) -> None:
        python = self._venv(model_version="0.3.0", service_core_version="0.7.0")
        _set_version(python, "juniper_recurrence_model-*.dist-info", "not-a-version")
        result = _run_preflight(python)
        self.assertEqual(result.returncode, 1, msg=result.stdout + result.stderr)
        self.assertIn(
            "FINDING: version pin: juniper-recurrence-model not-a-version is not a PEP 440 version, " "so juniper-recurrence 0.5.0's juniper-recurrence-model<0.4.0,>=0.3.0 cannot be checked\n",
            result.stdout,
        )
        self.assertNotIn("version-pin probe failed", result.stdout)

    def test_a_bare_requirement_with_an_empty_specifier_is_pin_ok(self) -> None:
        # str(specifier) is empty. The message concatenates name and specifier, so a space
        # or an invented "==" changes the line. An empty specifier contains every version.
        python = self._venv(model_version="0.3.0", service_core_version="0.7.0")
        _rewrite_requires(python, ["juniper-recurrence-model", "juniper-service-core"])
        result = _run_preflight(python)
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("ENV PREFLIGHT: pin ok: juniper-recurrence-model 0.3.0 satisfies juniper-recurrence-model\n", result.stdout)
        self.assertIn("ENV PREFLIGHT: pin ok: juniper-service-core 0.7.0 satisfies juniper-service-core\n", result.stdout)
        self.assertNotIn("FINDING:", result.stdout)


if __name__ == "__main__":
    unittest.main()
