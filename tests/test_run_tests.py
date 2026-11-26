#!/usr/bin/env python3
"""Regression tests for util/run_tests.py, the local test runner: juniper-ml's spec, against the real workflows.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon (authored via Claude Code)
License:     MIT License

util/run_tests.py is a thin spec over the shared engine, ``juniper_ci_tools.run_tests``, which it loads from this
checkout's ``juniper-ci-tools/`` tree. The engine's own suite -- selection, running, the exit codes, ``--changed``,
on fake checkouts of juniper-ml's shape and two others -- is ``juniper-ci-tools/tests/test_run_tests.py``, which
``ci-ci-tools.yml`` runs. This file pins what is juniper-ml's own, against the real workflows (no test runs):

- every suite ci.yml's "Run Python regression tests" step invokes, in its order, is a job of the unittest lane;
  every other command of that step and of "Run bash regression tests" is a job too;
- every ``ci-<pkg>.yml`` with a ``test`` job is a package lane with a pytest step, a coverage gate and a PYTHONPATH
  inside this checkout, and ci-observability.yml's sentry-sdk check runs before its tests;
- the spec runs this checkout's engine, never an installed juniper-ci-tools;
- every option ``--help`` lists appears in docs/REFERENCE.md's "Running tests locally" section.

A workflow change the runner cannot read fails here, in the PR that makes it, instead of on the next person's
machine.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_ci_test_wiring_drift import _invoked_suites, _regression_run_script

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "util" / "run_tests.py"
REFERENCE = REPO_ROOT / "docs" / "REFERENCE.md"
ENGINE = REPO_ROOT / "juniper-ci-tools" / "juniper_ci_tools" / "run_tests.py"


def _load_runner():
    spec = importlib.util.spec_from_file_location("run_tests_under_test", RUNNER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


RT = _load_runner()


def _repo_tmp() -> Path:
    """This checkout's gitignored tmp/: on a CI runner the default temp directory is the system one."""
    path = REPO_ROOT / "tmp"
    path.mkdir(exist_ok=True)
    return path


class RealWorkflowsTest(unittest.TestCase):
    """The spec reads this checkout's workflows, and reads them the way CI runs them."""

    lanes: dict
    ci_suites: list[str]

    @classmethod
    def setUpClass(cls) -> None:
        cls.lanes = RT.rt.discover(REPO_ROOT, RT.SPEC)
        ci_text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        cls.ci_suites = ["tests/" + name for name in _invoked_suites(_regression_run_script(ci_text))]

    def test_the_spec_runs_this_checkouts_engine(self) -> None:
        self.assertEqual(Path(RT.rt.__file__).resolve(), ENGINE.resolve(), "util/run_tests.py loaded an engine from outside this checkout")
        self.assertEqual(RT.ENGINE.resolve(), ENGINE.resolve())
        self.assertEqual(list(self.lanes)[:2], ["unittest", "bash"])

    def test_every_suite_ci_invokes_is_a_unittest_job_in_ci_order(self) -> None:
        suites = [job.id for job in self.lanes["unittest"].jobs if job.kind == "unittest"]
        self.assertGreater(len(suites), 200, "the runner found almost no suites: its reader is broken")
        self.assertEqual(suites, self.ci_suites)

    def test_every_suite_on_disk_is_runnable(self) -> None:
        on_disk = sorted(f"tests/{path.name}" for path in (REPO_ROOT / "tests").glob("test_*.py"))
        self.assertEqual(sorted(job.id for job in self.lanes["unittest"].jobs if job.kind == "unittest"), on_disk)

    def test_the_other_commands_of_both_steps_are_jobs(self) -> None:
        import yaml

        job = yaml.safe_load((REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))["jobs"][RT.CI_JOB]
        for lane, step_name in (("unittest", RT.UNITTEST_STEP), ("bash", RT.BASH_STEP)):
            script = next(step["run"] for step in job["steps"] if step.get("name") == step_name)
            expected = [line for line in RT.rt.logical_lines(script) if not line.startswith("echo") and "-m unittest" not in line]
            with self.subTest(lane=lane):
                self.assertEqual(len([j for j in self.lanes[lane].jobs if j.kind == "command"]), len(expected))
        self.assertTrue(self.lanes["bash"].jobs, "the bash lane is empty")

    def test_one_package_lane_per_ci_workflow_with_a_test_job(self) -> None:
        import yaml

        expected = sorted(path.stem[len("ci-") :] for path in (REPO_ROOT / ".github" / "workflows").glob("ci-*.yml") if RT.PACKAGE_JOB in (yaml.safe_load(path.read_text(encoding="utf-8")).get("jobs") or {}))
        packages = RT.rt.package_lanes(self.lanes)
        self.assertEqual(sorted(lane.name for lane in packages), expected)
        self.assertGreaterEqual(len(expected), 6)
        for lane in packages:
            with self.subTest(lane=lane.name):
                labels = [step.label for step in lane.jobs[0].steps]
                self.assertIn("pytest", labels)
                self.assertIn("coverage-gate", labels)
                self.assertTrue(lane.pythonpath, "no editable install found: the lane would test whatever is installed")
                for path in lane.pythonpath:
                    self.assertTrue((path / "pyproject.toml").is_file(), path)
                    path.relative_to(REPO_ROOT)  # inside this checkout
                self.assertTrue(lane.packages, "no importable package found in the editable directories")
                self.assertEqual(lane.package_dir, REPO_ROOT / f"juniper-{lane.name}")
                self.assertEqual(lane.left_out, [], "a package test job gained a step the runner leaves out: run it (keep) or say why not")

    def test_the_sentry_sdk_check_runs_before_observabilitys_tests(self) -> None:
        steps = self.lanes["observability"].jobs[0].steps
        self.assertEqual([step.label for step in steps], ["python", "pytest", "coverage-gate"])
        self.assertIn("sentry_sdk.VERSION.split('.')[0] != '3'", " ".join(steps[0].argv))

    def test_list_runs_nothing_and_names_every_suite(self) -> None:
        proc = subprocess.run([sys.executable, str(RUNNER), "--list", "--color", "never"], cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        listed = [line.strip() for line in proc.stdout.splitlines() if line.startswith("  tests/test_")]
        self.assertEqual(listed, self.ci_suites)
        self.assertIn("groups: all = unittest bash ", proc.stdout)
        self.assertIn("; regression = unittest bash; packages = ", proc.stdout)

    def test_dry_run_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="run-tests-", dir=_repo_tmp()) as tmp:
            logs = Path(tmp) / "logs"
            proc = subprocess.run([sys.executable, str(RUNNER), "--dry-run", "--log-dir", str(logs), "--color", "never", "regression", "packages"], cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=300)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("Plan", proc.stdout)
            self.assertIn("-m unittest -v tests/test_run_tests.py", proc.stdout)
            self.assertFalse(logs.exists(), "a dry run created the log directory")


class ReferenceDocsTest(unittest.TestCase):
    """docs/REFERENCE.md documents the runner, and every option --help lists."""

    def test_every_option_is_documented(self) -> None:
        text = REFERENCE.read_text(encoding="utf-8")
        start = text.find("### Running tests locally")
        self.assertNotEqual(start, -1, "docs/REFERENCE.md has no 'Running tests locally' section")
        end = text.find("\n### ", start + 1)
        section = text[start : end if end != -1 else len(text)]
        options = sorted({option for action in RT.rt.build_parser(RT.SPEC)._actions for option in action.option_strings if option not in ("-h", "--help")})
        missing = [option for option in options if f"`{option}" not in section and f"{option} " not in section and f"{option}`" not in section]
        self.assertEqual(missing, [], "options --help lists that the REFERENCE section does not document")
        for selector in ("all", "regression", "unittest", "bash", "packages", "--changed", "--failed", "juniper_ci_tools.run_tests"):
            self.assertIn(selector, section)


if __name__ == "__main__":
    unittest.main()
