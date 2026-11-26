#!/usr/bin/env python3
"""Run any subset of juniper-ml's tests locally, with the commands CI runs.

Project: juniper-ml
Sub-Project: developer tooling (local test runs)
Author: Paul Calnon (authored via Claude Code)
Created: 2026-11-23 (a thin spec over the shared engine since 2026-11-26)
Status: permanent utility
Related: juniper-ci-tools/juniper_ci_tools/run_tests.py (the engine this declares a spec for, and its canonical
         home); .github/workflows/ci.yml and .github/workflows/ci-<pkg>.yml (the lists it reads);
         tests/test_run_tests.py (this spec against the real workflows and the docs; the engine's own suite is
         juniper-ci-tools/tests/test_run_tests.py); docs/REFERENCE.md § Test Suite Reference, "Running tests locally"
         (the operator documentation); util/python_version_check.py (the same tests under another Python version, in
         a venv)

Why this exists
---------------
juniper-ml has no test discovery. ci.yml's "Run Python regression tests" step is a hand-maintained list of
``python3 -m unittest -v tests/<suite>.py`` commands, one per suite, run under ``bash -e``, so CI stops at the
first failing suite and says nothing about the ones after it. "Run bash regression tests" follows it, and each of
the six in-repo packages has its own ``ci-<pkg>.yml`` whose ``test`` job runs pytest with a coverage floor and
then a per-file coverage gate. This script runs any subset of that locally, reading the commands from the
workflows on every run, so its lists cannot drift from CI's.

What is juniper-ml's own
------------------------
Everything that runs is the engine's: ``juniper_ci_tools.run_tests`` (the ``--help`` epilog and docs/REFERENCE.md
say how it selects, runs and reports). This file declares only what the engine cannot read from the workflows, as
its :class:`RepoSpec`:

- the ``unittest`` and ``bash`` lanes are two named steps of ci.yml's ``tests`` job (``regression`` is both), and the
  ``unittest`` lane's requirements are what that job's "Install test dependencies" step installs;
- each ``ci-<pkg>.yml``'s ``test`` job is the ``<pkg>`` lane (``packages`` is all six), whose directory is
  ``juniper-<pkg>/`` (so ``juniper-<pkg>`` names it too). Its "Check the installed sentry-sdk is 3.x" step runs
  although it runs no test: ci-observability.yml's comment says why (a 2.x resolution would skip every 3.x wire test
  and still pass);
- ``--force-drift`` sets ``JUNIPER_DRIFT_TEST_FORCE_LOCAL=1`` for every child;
- the ``--help`` text, which tests/test_run_tests.py pins against docs/REFERENCE.md.

The engine is loaded from this checkout's ``juniper-ci-tools/`` tree, never from an installed juniper-ci-tools: CI
and util/python_version_check.py install 0.9.x, which has no engine, and this tree is where the engine is changed.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "juniper-ci-tools" / "juniper_ci_tools" / "run_tests.py"


def _load_engine():
    spec = importlib.util.spec_from_file_location("juniper_ml_run_tests_engine", ENGINE)
    if spec is None or spec.loader is None:
        sys.stderr.write(f"run_tests.py: cannot load the engine from {ENGINE}\n")
        raise SystemExit(2)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # @dataclass resolves annotations through sys.modules
    spec.loader.exec_module(module)
    return module


rt = _load_engine()

CI_WORKFLOW = "ci.yml"
CI_JOB = "tests"
DEPS_STEP = "Install test dependencies"
UNITTEST_STEP = "Run Python regression tests"
BASH_STEP = "Run bash regression tests"
PACKAGE_WORKFLOWS = ("ci-*.yml",)
PACKAGE_JOB = "test"
# Runs although it runs no test: without it, a 2.x resolution would skip every 3.x wire test and still pass.
KEPT_STEPS = ("Check the installed sentry-sdk is 3.x",)
DRIFT_FLAG = "JUNIPER_DRIFT_TEST_FORCE_LOCAL"

_DESCRIPTION = """\
Run any subset of juniper-ml's tests locally, with the commands CI runs.

The lists come from the workflows on every run: ci.yml's "Run Python regression tests" and
"Run bash regression tests" steps, and the test job of each .github/workflows/ci-<package>.yml.
Every selected job runs (CI stops at the first failure), each in its own process group, and the
results go to one log per step plus summary.json under the primary checkout's tmp/."""

_EPILOG = """\
selectors (any number; default: all):
  all                       every lane below
  regression                ci.yml's Regression Tests job: the unittest and bash lanes
  unittest                  every command of ci.yml's "Run Python regression tests" step: one
                            `python3 -m unittest -v tests/<suite>.py` per suite, plus its checks
  bash                      ci.yml's "Run bash regression tests" step
  packages                  every package lane
  <package>                 one ci-<package>.yml test job: pytest with its coverage floor, then
                            the per-file coverage gate (ci-tools, config-tools, doc-tools,
                            model-core, observability, service-core; juniper-<package> works too)
  <suite>                   one regression suite: tests/test_safe_merge.py, test_safe_merge.py,
                            test_safe_merge or safe_merge
  '<glob>'                  every regression suite whose name matches: 'soak_*', '*predict_merge*'
  <suite>::<Class>[::<test>]  one class or test of a suite; tests.test_x.Class.test works too
  <package path>[::<node>]  a file, directory or node id under a package (for example
                            juniper-doc-tools/tests/test_cli.py): that lane's pytest on it alone,
                            with the coverage gates off
  --changed adds the jobs a change touches; --failed adds the failures of the last run.

examples:
  python3 util/run_tests.py                            everything, -j auto, past failures
  python3 util/run_tests.py regression -j 1 -x         ci.yml's regression job as CI runs it
  python3 util/run_tests.py safe_merge                 one suite, its output live
  python3 util/run_tests.py 'release_train_*' -k cap   a family of suites, tests matching "cap"
  python3 util/run_tests.py doc-tools service-core     two package lanes with their gates
  python3 util/run_tests.py juniper-doc-tools/tests/test_cli.py -- -x -vv
  python3 util/run_tests.py --changed                  what the branch touches (vs origin/main)
  python3 util/run_tests.py --failed                   the failures of the last run, again
  python3 util/run_tests.py --list 'soak*'             what a selector selects; runs nothing

exit codes:
  0    every selected job passed (a job that failed alongside others and passed alone counts,
       and is listed)
  1    at least one job failed or timed out
  2    usage or configuration error: an unknown selector, a workflow it cannot parse
  3    nothing failed, but at least one selected job could not run (UNAVAILABLE)
  5    no test ran: -k matched nothing in any selected job
  130  interrupted; summary.json holds the jobs that finished

Logs: the primary checkout's tmp/run-tests/<checkout name>/<UTC stamp>/ (one log per step,
summary.json, summary.txt; never pruned). Full documentation: docs/REFERENCE.md,
§ Test Suite Reference, "Running tests locally"."""

SPEC = rt.RepoSpec(
    project="juniper-ml",
    script=__file__,
    lanes=(
        rt.step_lane("unittest", CI_WORKFLOW, CI_JOB, UNITTEST_STEP, deps=DEPS_STEP, groups=("regression",)),
        rt.step_lane("bash", CI_WORKFLOW, CI_JOB, BASH_STEP, groups=("regression",)),
        rt.job_lanes(workflows=PACKAGE_WORKFLOWS, jobs=(PACKAGE_JOB,), name=rt.workflow_stem("ci-"), directory="juniper-{name}", keep=KEPT_STEPS, groups=("packages",)),
    ),
    marker=CI_WORKFLOW,
    docs="docs/REFERENCE.md, 'Running tests locally'",
    description=_DESCRIPTION,
    epilog=_EPILOG,
    flags=(rt.EnvFlag("--force-drift", DRIFT_FLAG, "the drift suites' cross-repo and live-API assertions run instead of skipping outside CI"),),
    unwired_hint="tests/test_ci_test_wiring_drift.py fails until ci.yml runs it",
)


if __name__ == "__main__":
    raise SystemExit(rt.main(SPEC))
