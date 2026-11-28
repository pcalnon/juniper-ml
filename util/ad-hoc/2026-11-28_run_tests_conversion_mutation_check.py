#!/usr/bin/env python3
"""
Mutation check for the two run_tests thin-spec conversions: each mutant must make the test that pins it fail.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-11-28
Status: ad-hoc -- the run_tests rollout, step 4 of § 4.3 of
        notes/JUNIPER_2026-11-26_JUNIPER-ECOSYSTEM_RUN-TESTS-ENGINE-EXTRACTION-PROPOSAL.md
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-26_run_tests_engine_mutation_check.py (the engine's mutation check);
         util/ad-hoc/2026-11-26_run_tests_engine_equivalence.py (the conversions' before/after proof)

Why this exists
---------------
After the conversion, juniper-data-client's and juniper-recurrence's tests/test_run_tests.py pin only what is each
repo's own: the lanes its workflows give, the engine pin, the docs. A test that passes whatever the code says pins
nothing, so each invariant is broken once here, in place, and the test that should catch it must fail:

- data-client: the per-file gate's and dependency-docs' juniper-ci-tools range in ci.yml, the [test] extra's entry,
  ENGINE_REQUIREMENT, strip_suffix, an OPT_IN key, and two facts docs/REFERENCE.md must state;
- recurrence: sequence-safety.yml's ceiling (the unittest lane merges its install), ci-tooling.yml's range,
  ENGINE_REQUIREMENT, the optional test-* table, the packages group, and a fact README.md must state.

Each mutant replaces exactly one occurrence of a string, runs one test (pytest in data-client, unittest in
recurrence, as their CI runs them), and restores the file byte for byte, checked by sha256, whatever happens. The
unmutated EngineTest classes must pass afterwards. Exit 0 when every mutant is killed and both controls pass.

Usage:
    python3 util/ad-hoc/2026-11-28_run_tests_conversion_mutation_check.py --dc DC_WORKTREE --rec REC_WORKTREE \
        --dc-python DC_VENV_PYTHON --rec-python REC_VENV_PYTHON
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess  # nosec B404 - the repos' own test runners, fixed argv
from pathlib import Path

CI = ".github/workflows/ci.yml"
GATE = 'pip install "juniper-ci-tools>=0.10.0,<0.11.0"\n          juniper-coverage-gap-map'
DEPDOCS = 'pip install "juniper-ci-tools>=0.10.0,<0.11.0"\n\n      - name: Generate Dependency Documentation'
DC_ENGINE = "EngineTest::test_no_job_that_installs_the_test_extra_installs_another_engine"

MUTANTS = [
    ("dc", CI, GATE, GATE.replace(">=0.10.0,<0.11.0", ">=0.9.0,<0.10.0"), DC_ENGINE),
    ("dc", CI, DEPDOCS, DEPDOCS.replace(">=0.10.0,<0.11.0", ">=0.9.0,<0.10.0"), DC_ENGINE),
    ("dc", "pyproject.toml", '    "juniper-ci-tools>=0.10.0,<0.11.0",\n', "", "EngineTest::test_the_test_extra_asks_for_the_engine"),
    ("dc", "util/run_tests.py", 'ENGINE_REQUIREMENT = "juniper-ci-tools>=0.10.0,<0.11.0"', 'ENGINE_REQUIREMENT = "juniper-ci-tools>=0.11.0,<0.12.0"', "EngineTest::test_the_installed_engine_is_in_the_specs_range"),
    ("dc", "util/run_tests.py", 'strip_suffix="-tests",', 'strip_suffix="",', "RealWorkflowsTest::test_every_alias_names_its_lane"),
    ("dc", "util/run_tests.py", '    "security": "needs the gitleaks binary', '    "security-x": "needs the gitleaks binary', "RealWorkflowsTest::test_all_is_the_lanes_the_test_extra_can_run"),
    ("dc", "docs/REFERENCE.md", "a thin spec over the shared engine, `juniper_ci_tools.run_tests`", "a thin spec over the shared engine", "DocsTest::test_the_section_names_the_engine_and_its_install"),
    ("dc", "docs/REFERENCE.md", "`tests` names it too", "tests names it too", "DocsTest::test_every_lane_and_group_is_documented_in_the_reference_and_the_help"),
    ("rec", ".github/workflows/sequence-safety.yml", 'pip install "juniper-ci-tools>=0.9.0,<0.11.0"', 'pip install "juniper-ci-tools>=0.9.0,<0.10.0"', "EngineTest.test_every_engine_install_the_unittest_lane_merges_admits_the_engine"),
    ("rec", ".github/workflows/ci-tooling.yml", '"juniper-ci-tools>=0.10.0,<0.11.0"', '"juniper-ci-tools>=0.9.0,<0.11.0"', "EngineTest.test_ci_tooling_installs_the_engine"),
    ("rec", "util/run_tests.py", 'ENGINE_REQUIREMENT = "juniper-ci-tools>=0.10.0,<0.11.0"', 'ENGINE_REQUIREMENT = "juniper-ci-tools>=0.11.0,<0.12.0"', "EngineTest.test_the_installed_engine_is_in_the_specs_range"),
    ("rec", "util/run_tests.py", "optional={OPTIONAL_JOBS: \"{workflow}'s {job} job, which CI runs beside its test job\"}, ", "", "RealWorkflowsTest.test_the_torch_job_is_an_optional_lane_outside_all"),
    ("rec", "util/run_tests.py", "groups=(PACKAGES_GROUP,)),", "groups=()),", "RealWorkflowsTest.test_one_gating_lane_per_ci_recurrence_workflow_with_a_test_job"),
    ("rec", "README.md", "the engine's own suite is juniper-ml's\n`juniper-ci-tools/tests/test_run_tests.py`", "the engine's own suite is juniper-ml's\nengine suite", "ReadmeDocsTest.test_every_option_is_documented"),
]


def run_test(args: argparse.Namespace, repo: str, test: str) -> int:
    if repo == "dc":
        argv, cwd = [args.dc_python, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"tests/test_run_tests.py::{test}"], args.dc
    else:
        argv, cwd = [args.rec_python, "-m", "unittest", f"tests.test_run_tests.{test}"], args.rec
    return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=600, check=False).returncode  # nosec B603


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dc", required=True, type=Path, help="the juniper-data-client conversion worktree")
    parser.add_argument("--rec", required=True, type=Path, help="the juniper-recurrence conversion worktree")
    parser.add_argument("--dc-python", required=True, help="an interpreter with data-client's [test] extra and juniper-ci-tools 0.10")
    parser.add_argument("--rec-python", required=True, help="an interpreter with PyYAML and juniper-ci-tools 0.10")
    args = parser.parse_args()
    survived = 0
    for repo, rel, old, new, test in MUTANTS:
        path = (args.dc if repo == "dc" else args.rec) / rel
        original = path.read_bytes()
        digest = hashlib.sha256(original).hexdigest()
        text = original.decode("utf-8")
        if text.count(old) != 1:
            print(f"BAD      {repo} {rel}: the mutation's text occurs {text.count(old)} times")
            survived += 1
            continue
        try:
            path.write_bytes(text.replace(old, new).encode("utf-8"))
            rc = run_test(args, repo, test)
        finally:
            path.write_bytes(original)
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise SystemExit(f"{path} was not restored")
        killed = rc != 0
        survived += not killed
        print(f"{'KILLED  ' if killed else 'SURVIVED'} {repo} {rel} -> {test} (rc {rc})")
    controls = {repo: run_test(args, repo, "EngineTest") for repo in ("dc", "rec")}
    print(f"{len(MUTANTS) - survived} of {len(MUTANTS)} mutants killed; unmutated EngineTest rc: {controls}")
    return 1 if survived or any(controls.values()) else 0


if __name__ == "__main__":
    raise SystemExit(main())
