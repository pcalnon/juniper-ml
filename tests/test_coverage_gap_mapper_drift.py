"""Dogfood / drift gate for the ``juniper-coverage-gap-map`` console script
(enhancement E-4, plan
``notes/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_2026-06-27.md`` §6.7,
Phase-2 PR-6).

The advisory per-file coverage-gap mapper is hosted in the
``juniper-ci-tools`` sub-package (its own pytest suite is the behavioural
gate, run by ``.github/workflows/ci-ci-tools.yml``). This juniper-ml-side
test is the **structural** dogfood gate, modelled on
``tests/test_ci_tools_drift.py``. It asserts:

1. The ``juniper-coverage-gap-map`` console script is registered in
   ``juniper-ci-tools/pyproject.toml`` ``[project.scripts]`` and points at
   ``juniper_ci_tools.cli_coverage_gap_mapper:main``.
2. Both halves of the tool ship: the logic module
   (``coverage_gap_mapper.py``) and the CLI wrapper
   (``cli_coverage_gap_mapper.py``).
3. The version is coherent: ``juniper_ci_tools/_version.py``'s
   ``__version__`` equals ``pyproject.toml`` ``[project].version``.
4. The pin is coherent: juniper-ml's own workflows
   (``ci.yml`` / ``lockfile-update.yml`` / ``docs-full-check.yml``) pin a
   ``juniper-ci-tools>=X,<Y`` range that still admits the current version --
   so bumping ci-tools to ship E-4 without widening the pin ceiling fails
   loudly here (the same coupling ``test_ci_tools_drift.py`` enforces).

Why this is a STRUCTURAL gate (the manual-verify note)
------------------------------------------------------
The mapper's *point* is to run coverage over a target repo and map the
per-file gaps. That cross-repo coverage run **cannot execute in juniper-ml
CI**: juniper-ml is a meta-package with no application package to measure,
and the target repos (cascor-model, canopy, ...) are not checked out in the
per-PR ubuntu runner. So this gate is structural only -- it proves the tool
is *shipped and wired*, not that a live coverage run behaves. The behaviour
is proven two ways: the ``juniper-ci-tools/tests/test_coverage_gap_mapper.py``
fixtures (synthetic ``coverage.json``; no real run) and a documented
**manual-verify** invocation an operator runs against a real repo::

    # From a target repo with a real test command (e.g. juniper-cascor's
    # cascor-model package, whose CI has no per-file coverage gate):
    cd <target-repo>
    pip install "juniper-ci-tools>=0.5.0,<0.6.0"
    juniper-coverage-gap-map --repo-root . --package <pkg> \\
        --test-command "python -m pytest"
    # -> prints the per-file distribution, the files below 90%, and each
    #    sub-module's average vs the 95% bar; exits 0 regardless (advisory).

    # Or against a pre-generated coverage.json (the primary path):
    juniper-coverage-gap-map --coverage-json coverage.json --json

Skip semantics mirror ``test_ci_tools_drift.py``: there is no consumer-repo
pin for this brand-new script yet, so there is no cross-repo sibling
assertion to run; the structural checks above are all juniper-ml-local and
run unconditionally. ``JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`` is honoured only by
the informational environment probe, for parity with the sibling drift tests.
"""

from __future__ import annotations

import os
import re
import unittest
from pathlib import Path

# Pin-range pattern, identical to test_ci_tools_drift.py:
#   pip install "juniper-ci-tools>=0.1.0,<0.6.0"
_PIN_PATTERN = re.compile(r"juniper-ci-tools\s*>=\s*([0-9]+(?:\.[0-9]+)+)\s*,\s*<\s*([0-9]+(?:\.[0-9]+)+)")

# The console-script entry E-4 registers (whitespace-forgiving).
_SCRIPT_PATTERN = re.compile(r"""juniper-coverage-gap-map\s*=\s*["']juniper_ci_tools\.cli_coverage_gap_mapper:main["']""")

# juniper-ml's own workflows that pin juniper-ci-tools (same set as
# test_ci_tools_drift.py's _ML_OWN_WORKFLOWS).
_ML_OWN_WORKFLOWS = (
    ".github/workflows/ci.yml",
    ".github/workflows/lockfile-update.yml",
    ".github/workflows/docs-full-check.yml",
)

# The two module halves of the tool (the logic-module + thin-CLI-wrapper
# pattern mirrored from lint_agents_md_version.py / cli_lint_agents_md_version.py).
_TOOL_MODULES = (
    "juniper-ci-tools/juniper_ci_tools/coverage_gap_mapper.py",
    "juniper-ci-tools/juniper_ci_tools/cli_coverage_gap_mapper.py",
)


def _parse_version(value: str) -> tuple[int, ...]:
    """Convert "0.5.0" -> (0, 5, 0). Ignores any pre-release tags."""
    return tuple(int(part.split("-")[0].split("+")[0]) for part in value.split("."))


def _read_pyproject_version(pyproject: Path) -> str | None:
    """Read ``[project].version`` from the ci-tools pyproject (regex, like the
    sibling drift test -- no tomllib dependency)."""
    if not pyproject.exists():
        return None
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        match = re.match(r'^version\s*=\s*"([^"]+)"\s*$', line.strip())
        if match:
            return match.group(1)
    return None


def _read_dunder_version(version_py: Path) -> str | None:
    """Read ``__version__`` from ``_version.py``."""
    if not version_py.exists():
        return None
    match = re.search(r'__version__\s*=\s*"([^"]+)"', version_py.read_text(encoding="utf-8"))
    return match.group(1) if match else None


def _extract_pins(yaml_text: str) -> list[tuple[str, str]]:
    """Every ``juniper-ci-tools>=X,<Y`` (lower, upper) pair in the text."""
    return [(m.group(1), m.group(2)) for m in _PIN_PATTERN.finditer(yaml_text)]


class CoverageGapMapperDriftTest(unittest.TestCase):
    """Structural dogfood gate for the E-4 ``juniper-coverage-gap-map`` script."""

    # Declared so the annotated method bodies type-check (the attributes are
    # populated in setUpClass; mypy checks annotated bodies under this config).
    juniper_ml_root: Path
    ci_tools_root: Path
    pyproject: Path
    version_py: Path
    current_version: str | None

    @classmethod
    def setUpClass(cls) -> None:
        cls.juniper_ml_root = Path(__file__).resolve().parent.parent
        cls.ci_tools_root = cls.juniper_ml_root / "juniper-ci-tools"
        cls.pyproject = cls.ci_tools_root / "pyproject.toml"
        cls.version_py = cls.ci_tools_root / "juniper_ci_tools" / "_version.py"
        cls.current_version = _read_pyproject_version(cls.pyproject)

    def test_environment_note(self) -> None:
        """Informational: state plainly that the cross-repo coverage run is a
        documented manual-verify step, not a CI assertion (so an operator
        reading CI logs is not confused). Mirrors test_ci_tools_drift.py's
        environment sanity probe."""
        forced = os.environ.get("JUNIPER_DRIFT_TEST_FORCE_LOCAL")
        print("INFO: coverage-gap-mapper drift gate is STRUCTURAL -- the real per-file " "coverage run is a manual-verify step (see module docstring); juniper-ml CI " f"cannot run it (meta-package; no target repo checked out). FORCE_LOCAL={forced!r}")

    def test_current_version_is_readable(self) -> None:
        self.assertIsNotNone(
            self.current_version,
            "Could not read juniper-ci-tools [project].version from juniper-ci-tools/pyproject.toml; the drift gate depends on it as the source of truth for 'current'.",
        )

    def test_console_script_registered(self) -> None:
        """The juniper-coverage-gap-map console script is registered and points
        at the CLI wrapper's ``:main``."""
        self.assertTrue(self.pyproject.exists(), "juniper-ci-tools/pyproject.toml is missing")
        text = self.pyproject.read_text(encoding="utf-8")
        self.assertIn("[project.scripts]", text, "juniper-ci-tools/pyproject.toml has no [project.scripts] table")
        self.assertRegex(
            text,
            _SCRIPT_PATTERN,
            'juniper-coverage-gap-map = "juniper_ci_tools.cli_coverage_gap_mapper:main" is not registered in [project.scripts] -- E-4 console script unwired.',
        )

    def test_tool_modules_exist(self) -> None:
        """Both the logic module and the thin CLI wrapper ship."""
        for rel in _TOOL_MODULES:
            with self.subTest(module=rel):
                self.assertTrue((self.juniper_ml_root / rel).is_file(), f"{rel} is missing -- E-4 module not shipped")

    def test_version_dunder_matches_pyproject(self) -> None:
        """``_version.py`` __version__ mirrors pyproject [project].version."""
        if self.current_version is None:
            self.skipTest("no current version available")
        dunder = _read_dunder_version(self.version_py)
        self.assertIsNotNone(dunder, "juniper_ci_tools/_version.py has no __version__")
        self.assertEqual(
            dunder,
            self.current_version,
            f"_version.py __version__ ({dunder}) != pyproject [project].version ({self.current_version}); bump both in the same PR.",
        )

    def test_ml_own_workflow_pins_admit_current(self) -> None:
        """juniper-ml's own workflow pins must admit the current ci-tools
        version. Shipping E-4 as a minor bump (0.4.0 -> 0.5.0) without widening
        the ``<X.Y.0`` ceiling here fails loudly -- the exact coupling this and
        test_ci_tools_drift.py exist to catch."""
        if self.current_version is None:
            self.skipTest("no current version available")
        current = _parse_version(self.current_version)
        for rel in _ML_OWN_WORKFLOWS:
            with self.subTest(workflow=rel):
                workflow = self.juniper_ml_root / rel
                if not workflow.exists():
                    self.skipTest(f"{rel} not present in this checkout")
                pins = _extract_pins(workflow.read_text(encoding="utf-8"))
                self.assertGreater(len(pins), 0, f"{rel} no longer pins juniper-ci-tools")
                for lower, upper in pins:
                    self.assertLessEqual(_parse_version(lower), current, f"{rel} pin lower bound {lower} is ahead of current {self.current_version}")
                    self.assertLess(current, _parse_version(upper), f"{rel} pin upper bound {upper} excludes current {self.current_version} -- widen the ceiling in the same PR as the ci-tools bump.")


class PinHelperTest(unittest.TestCase):
    """Direct unit tests for the helpers so they are not solely reliant on the
    integration assertions for coverage."""

    def test_parse_version(self) -> None:
        self.assertEqual(_parse_version("0.5.0"), (0, 5, 0))
        self.assertEqual(_parse_version("0.5.0-rc1"), (0, 5, 0))
        self.assertEqual(_parse_version("0.10.0"), (0, 10, 0))

    def test_extract_pins(self) -> None:
        self.assertEqual(_extract_pins('pip install "juniper-ci-tools>=0.1.0,<0.6.0"'), [("0.1.0", "0.6.0")])
        self.assertEqual(_extract_pins("nothing here"), [])

    def test_script_pattern_matches_canonical_entry(self) -> None:
        self.assertRegex('juniper-coverage-gap-map = "juniper_ci_tools.cli_coverage_gap_mapper:main"', _SCRIPT_PATTERN)
        self.assertNotRegex('juniper-lint-workflow-paths = "juniper_ci_tools.cli_lint_workflow_paths:main"', _SCRIPT_PATTERN)


if __name__ == "__main__":
    unittest.main()
