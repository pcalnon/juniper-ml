#!/usr/bin/env python3
"""Drift gate: juniper-ml's CI Python matrices against conf/python_versions.yaml (3.15 migration, phase 1).

Project:     Juniper
Sub-Project: juniper-ml
Application: ecosystem tooling regression tests
Author:      Paul Calnon
License:     MIT License

The owner's ruling of 2026-11-14: Python 3.12, 3.13 and 3.14 are blocking, 3.15 is informational, and an
informational check reports without blocking a commit, a merge or a deployment. In CI the ruling is a shape
(juniper-ml#2567). Each informational version is an ``include`` entry with ``experimental: true`` under the
job-level ``continue-on-error: ${{ matrix.experimental == true }}``, so a red leg leaves the job, and the
Quality Gate that reads ``needs.tests.result``, green. Two edits break it silently:

- the version moves into the matrix's plain ``python-version`` list, and becomes blocking;
- the ``continue-on-error`` line goes, and a red 3.15 leg fails the job and the gate.

Neither shows until a 3.15 leg goes red on a PR that did not touch it. This suite holds every
Python-version matrix in ``.github/workflows/`` to the lists in conf/python_versions.yaml, the file
util/python_version_check.py reads, so the local and CI sides move together. Pre-commit matrices are exempt
(the owner's ruling the same day: pre-commit stays on 3.12-3.14).

It also holds the config's juniper-ml recipe to ci.yml's ``tests`` job: the recipe must install exactly
the requirements of ``Install test dependencies`` and must name a regression runner that exists.
"""

from __future__ import annotations

import re
import shlex
import unittest
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS = REPO_ROOT / ".github" / "workflows"
CONFIG = REPO_ROOT / "conf" / "python_versions.yaml"
COE_EXPRESSION = "${{ matrix.experimental == true }}"
#: Pre-commit matrices are exempt (owner ruling, 2026-11-14).
EXEMPT_JOBS = frozenset({"pre-commit"})
#: The matrices the CI half (juniper-ml#2567) gave informational legs; the scan must find at least these.
EXPECTED_JOBS = frozenset(
    {
        ("ci.yml", "tests"),
        ("ci-ci-tools.yml", "test"),
        ("ci-config-tools.yml", "test"),
        ("ci-doc-tools.yml", "test"),
        ("ci-model-core.yml", "test"),
        ("ci-observability.yml", "test"),
        ("ci-service-core.yml", "test"),
    }
)
CI_INSTALL_STEP = "Install test dependencies"
#: pip options that take a value: the value is not a requirement.
PIP_VALUE_OPTIONS = frozenset({"-r", "--requirement", "-c", "--constraint", "-i", "--index-url", "--extra-index-url", "-f", "--find-links"})


def load_config() -> dict:
    return yaml.safe_load(CONFIG.read_text(encoding="utf-8"))


def python_matrix(job: dict) -> dict | None:
    """The job's strategy.matrix when it varies python-version, in its plain list or in an include entry."""
    matrix = (job.get("strategy") or {}).get("matrix")
    if not isinstance(matrix, dict):
        return None
    includes = matrix.get("include") or []
    if "python-version" in matrix or any(isinstance(entry, dict) and "python-version" in entry for entry in includes):
        return matrix
    return None


def matrix_jobs() -> dict[tuple[str, str], dict]:
    """Every job of every workflow that has a Python-version matrix, keyed by (file name, job id)."""
    found: dict[tuple[str, str], dict] = {}
    for path in sorted(WORKFLOWS.glob("*.y*ml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for job_id, job in (doc.get("jobs") or {}).items():
            if isinstance(job, dict) and python_matrix(job) is not None:
                found[(path.name, str(job_id))] = job
    return found


def violations(job: dict, informational: list[str]) -> list[str]:
    """What keeps this job's matrix from running each informational version as a non-blocking leg."""
    problems: list[str] = []
    matrix = python_matrix(job) or {}
    coe = job.get("continue-on-error")
    if not isinstance(coe, str) or " ".join(coe.split()) != COE_EXPRESSION:
        problems.append(f"job-level continue-on-error is {coe!r}, not {COE_EXPRESSION!r}")
    plain = [str(v) for v in matrix.get("python-version") or []]
    includes = [entry for entry in matrix.get("include") or [] if isinstance(entry, dict)]
    for version in informational:
        if version in plain:
            problems.append(f"informational {version} is in the plain python-version list, which makes it blocking")
        if not any(str(entry.get("python-version")) == version and entry.get("experimental") is True for entry in includes):
            problems.append(f"no include entry runs informational {version} with experimental: true")
    for entry in includes:
        if entry.get("experimental") is True and str(entry.get("python-version")) not in informational:
            problems.append(f"include entry {entry} is experimental but {entry.get('python-version')} is not informational, so it would stop blocking")
    return problems


def pip_requirements(script: str) -> set[str]:
    """The requirement arguments of every ``pip install`` in a shell script (comments and options skipped)."""
    found: set[str] = set()
    for raw in script.splitlines():
        tokens = shlex.split(raw, comments=True)
        for i in range(1, len(tokens)):
            if tokens[i] == "install" and tokens[i - 1] == "pip":
                skip = False
                for token in tokens[i + 1 :]:
                    if skip:
                        skip = False
                    elif token in PIP_VALUE_OPTIONS:
                        skip = True
                    elif token in ("||", "&&", ";"):
                        break
                    elif not token.startswith("-"):
                        found.add(token)
                break
    return found


def ci_install_script() -> str:
    doc = yaml.safe_load((WORKFLOWS / "ci.yml").read_text(encoding="utf-8"))
    for step in doc["jobs"]["tests"]["steps"]:
        if step.get("name") == CI_INSTALL_STEP:
            return step["run"]
    raise AssertionError(f"ci.yml's tests job has no {CI_INSTALL_STEP!r} step (renamed?); update this gate with it")


class MatrixDriftTest(unittest.TestCase):
    """Every Python matrix runs each informational version as an experimental include, and only those."""

    informational: list[str]
    blocking: list[str]
    jobs: dict[tuple[str, str], dict]

    @classmethod
    def setUpClass(cls) -> None:
        config = load_config()
        cls.informational = [str(v) for v in config["informational"]]
        cls.blocking = [str(v) for v in config["blocking"]]
        cls.jobs = matrix_jobs()

    def test_the_scan_finds_every_known_matrix(self) -> None:
        missing = EXPECTED_JOBS - set(self.jobs)
        self.assertFalse(missing, f"the scan did not find {sorted(missing)}: renamed, or the scanner went blind")
        self.assertIn(("ci.yml", "pre-commit"), self.jobs, "the exemption names a job the scan no longer finds")

    def test_the_config_has_an_informational_version_to_hold_ci_to(self) -> None:
        # With an empty list every check below passes vacuously.
        self.assertTrue(self.informational, "conf/python_versions.yaml lists no informational version; rewrite this gate when 3.15 becomes blocking")

    def test_every_python_matrix_runs_the_informational_versions_without_blocking(self) -> None:
        checked = 0
        for (name, job_id), job in sorted(self.jobs.items()):
            if job_id in EXEMPT_JOBS:
                continue
            checked += 1
            with self.subTest(workflow=name, job=job_id):
                self.assertEqual(violations(job, self.informational), [])
        self.assertGreaterEqual(checked, len(EXPECTED_JOBS))

    def test_every_blocking_version_stays_blocking_where_ci_yml_runs_it(self) -> None:
        tests = self.jobs[("ci.yml", "tests")]
        plain = [str(v) for v in python_matrix(tests).get("python-version")]
        self.assertEqual(plain, self.blocking, "ci.yml's regression matrix must run exactly the blocking versions as blocking legs")


class ViolationNegativeControlTest(unittest.TestCase):
    """The checker bites on each shape that would make an informational leg blocking (or a blocking one not)."""

    def good_job(self) -> dict:
        return {
            "continue-on-error": COE_EXPRESSION,
            "strategy": {"fail-fast": False, "matrix": {"python-version": ["3.12", "3.13", "3.14"], "include": [{"python-version": "3.15", "experimental": True}]}},
        }

    def test_the_good_shape_passes(self) -> None:
        self.assertEqual(violations(self.good_job(), ["3.15"]), [])

    def test_a_version_in_the_plain_list_is_caught(self) -> None:
        job = self.good_job()
        job["strategy"]["matrix"]["python-version"].append("3.15")
        self.assertTrue(any("makes it blocking" in p for p in violations(job, ["3.15"])))

    def test_a_missing_continue_on_error_is_caught(self) -> None:
        for coe in (None, True, "${{ matrix.experimental }}"):
            with self.subTest(coe=coe):
                job = self.good_job()
                if coe is None:
                    del job["continue-on-error"]
                else:
                    job["continue-on-error"] = coe
                self.assertTrue(any("continue-on-error" in p for p in violations(job, ["3.15"])))

    def test_a_missing_or_non_experimental_include_is_caught(self) -> None:
        for include in ([], [{"python-version": "3.15"}], [{"python-version": "3.15", "experimental": "true"}]):
            with self.subTest(include=include):
                job = self.good_job()
                job["strategy"]["matrix"]["include"] = include
                self.assertTrue(any("experimental: true" in p for p in violations(job, ["3.15"])))

    def test_an_experimental_blocking_version_is_caught(self) -> None:
        job = self.good_job()
        job["strategy"]["matrix"]["include"].append({"python-version": "3.14", "experimental": True})
        self.assertTrue(any("would stop blocking" in p for p in violations(job, ["3.15"])))

    def test_a_non_experimental_include_such_as_a_macos_leg_is_allowed(self) -> None:
        job = self.good_job()
        job["strategy"]["matrix"]["include"].append({"os": "macos-latest", "python-version": "3.12", "experimental": False})
        self.assertEqual(violations(job, ["3.15"]), [])

    def test_a_job_without_a_python_matrix_is_not_scanned(self) -> None:
        self.assertIsNone(python_matrix({"runs-on": "ubuntu-latest"}))
        self.assertIsNone(python_matrix({"strategy": {"matrix": {"os": ["ubuntu-latest"]}}}))
        self.assertIsNotNone(python_matrix({"strategy": {"matrix": {"include": [{"python-version": "3.15"}]}}}))


class JuniperMlRecipeTest(unittest.TestCase):
    """The config's juniper-ml recipe installs what ci.yml's tests job installs, and runs a runner that exists."""

    recipe: dict

    @classmethod
    def setUpClass(cls) -> None:
        cls.recipe = load_config()["repos"]["juniper-ml"]

    def test_the_recipe_installs_exactly_the_ci_test_dependencies(self) -> None:
        ci = pip_requirements(ci_install_script())
        local = pip_requirements("\n".join(self.recipe["install"]))
        self.assertTrue(ci, "found no pip requirement in ci.yml's install step: the extractor went blind")
        self.assertEqual(local, ci, f"only in ci.yml: {sorted(ci - local)}; only in the recipe: {sorted(local - ci)}")

    def test_the_regression_runner_the_recipe_names_exists(self) -> None:
        paths = [token for command in self.recipe["test"].values() for token in shlex.split(command) if re.fullmatch(r"util/[\w./-]+\.py", token)]
        self.assertTrue(paths, "the juniper-ml recipe names no util/ script")
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue((REPO_ROOT / path).is_file(), f"{path} does not exist")

    def test_the_requirement_extractor(self) -> None:
        script = "\n".join(
            [
                'python -m pip install --upgrade "pip>=26.1.1"',
                '# pip install "commented>=1"',
                'pip install "a>=1" wheel  # trailing comment',
                "pip install -r requirements.txt --index-url https://example.invalid/simple b",
                'pip install "c @ git+https://example.invalid/c.git@main" || true',
                "echo pip install-like text is ignored",
            ]
        )
        self.assertEqual(pip_requirements(script), {"pip>=26.1.1", "a>=1", "wheel", "b", "c @ git+https://example.invalid/c.git@main"})


if __name__ == "__main__":
    unittest.main()
