"""Tests for juniper_ci_tools.run_tests, the engine behind every Juniper repo's util/run_tests.py.

The three per-repo copies' fake-checkout suites (juniper-ml#2629, juniper-recurrence#240, juniper-data-client#273),
merged and run against the engine. Each repo keeps the tests of its own spec against its real workflows and docs.

Three fake checkouts, one per shape a spec takes:

- **ml**: juniper-ml's: two named steps of ci.yml as the ``unittest`` and ``bash`` lanes (a command among the suites),
  and a ``ci-<pkg>.yml`` test job per package, named by its workflow, with a kept environment-check step and an
  :class:`EnvFlag`.
- **dc**: juniper-data-client's: every job that runs pytest is a lane, named by its job id; ``env:`` expansion, the
  rc-capture rule, an opt-in table, a scheduled workflow, the coverage floor.
- **rec**: juniper-recurrence's: lanes named by their ``ci-recurrence-*.yml`` workflow, ``test-*`` jobs optional, a
  ``changes`` job's path filter, a lane whose directory is a package, and no root pyproject.toml.

The runs are in-process (``rt.main(spec, argv)``), so coverage measures the engine; the fake ``pytest``,
``coverage`` and gate are stubs that record how they were called. The checkouts live under the juniper-ml checkout's
gitignored ``tmp/``, never the system temp directory, which the engine refuses as a log root. One test runs a thin
``util/run_tests.py`` as a process, as each repo does.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import signal
import subprocess  # nosec B404 - runs the engine, git and fake tools with a fixed argv, in fake checkouts under tmp/
import sys
import tempfile
import textwrap
import threading
import time
from pathlib import Path
from typing import Iterator, NamedTuple

import pytest

from juniper_ci_tools import run_tests as rt

ROOT = Path(__file__).resolve().parents[2]  # the juniper-ml checkout that holds juniper-ci-tools/
PACKAGE_DIR = Path(rt.__file__).resolve().parents[1]  # juniper-ci-tools/, for a subprocess's PYTHONPATH

# ---------------------------------------------------------------------------------------------------------------
# The fake checkouts
# ---------------------------------------------------------------------------------------------------------------

ML_CI_YML = """\
name: CI
on: [push, pull_request]
jobs:
  tests:
    runs-on: ubuntu-latest
    steps:
      - name: Install test dependencies
        run: |
          python -m pip install --upgrade "pip>=26.1.1"
          pip install "pyyaml>=6.0"
      - name: Run Python regression tests
        run: |
          echo "banner"
          # tests/test_ghost.py: a comment names a suite; it is not one
          python3 -m unittest -v tests/test_alpha.py
          python3 -m unittest -v tests/test_beta.py
          python3 -m unittest -v tests/test_gamma.py  # a trailing comment
          python3 util/check.py verify
      - name: Run bash regression tests
        run: |
          echo "banner"
          bash scripts/test_shell.bash
"""

ML_DEMO_YML = """\
name: CI demo
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: juniper-demo
    steps:
      - uses: actions/checkout@v4
      - name: Install package + test extras
        run: |
          python -m pip install --upgrade "pip>=26.1.1"
          pip install -e ".[test]"
      - name: Check the environment is the right one
        run: python -c "import os, sys; sys.exit(int(os.environ.get('FAKE_CHECK_ENV_RC', '0')))"
      - name: Run unit tests with coverage
        run: |
          python -m pytest \\
            --cov=juniper_demo \\
            --cov-report=term-missing \\
            --cov-report=json:coverage.json \\
            --cov-fail-under=85
      - name: Enforce per-file coverage gate (blocking)
        run: |
          pip install "juniper-ci-tools>=0.9.0,<0.10.0"
          python ../gate.py --coverage-json coverage.json --enforce
      - name: Report the informational Python 3.15 result
        if: always()
        run: |
          echo "${{ toJSON(steps) }}"
  test-other:
    runs-on: ubuntu-latest
    steps:
      - name: Not a lane of this spec (jobs=("test",))
        run: python -m pytest juniper-demo/tests
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Build
        run: python -m build
"""

# juniper-ml's ci-service-core.yml shape: no working directory, so the lane's directory is the spec's
# "juniper-{name}", not the tests/ directory pytest names.
ML_OTHER_YML = """\
name: CI other
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Install package + test extras
        run: pip install -e "juniper-other/.[test]"
      - name: Run unit tests
        run: pytest juniper-other/tests/ -q --cov=juniper_other --cov-report=json:coverage.json
      - name: Enforce per-file coverage gate (blocking)
        run: python gate.py --coverage-json coverage.json --enforce
"""

DC_CI_YML = """\
name: CI/CD Pipeline
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  workflow_dispatch:
env:
  PYTHON_TEST_VERSION: "3.99"
  COVERAGE_FAIL_UNDER: "77"
jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - name: Run pre-commit hooks
        run: pre-commit run --all-files --show-diff-on-failure
  unit-tests:
    needs: [pre-commit]
    runs-on: ${{ matrix.os }}
    env:
      JOB_LEVEL: "from-${{ env.PYTHON_TEST_VERSION }}"
      FAKE_CI_ONLY: ${{ secrets.FAKE_CI_ONLY }}
    steps:
      - uses: actions/checkout@v4
      - name: Install dependencies
        run: |
          python -m pip install --upgrade "pip>=26.1.1"
          pip install -e ".[test]"
      - name: Create required directories
        run: |
          mkdir -p reports/junit reports/htmlcov
      - name: Run Unit Tests
        run: |
          echo "unit tests"
          python -m pytest \\
            tests/ \\
            --verbose \\
            --junitxml=reports/junit/junit-unit.xml \\
            --cov=fake_client \\
            --cov-report=term-missing:skip-covered \\
            --cov-report=xml:reports/coverage.xml \\
            --cov-report=json:coverage.json \\
            --cov-report=html:reports/htmlcov
      - name: Enforce Coverage Gate
        run: |
          echo "coverage gate"
          python -m coverage report --fail-under=${COVERAGE_FAIL_UNDER}
      - name: Enforce Per-File Coverage Gate
        run: |
          pip install "juniper-ci-tools>=0.9.0,<0.10.0"
          python gate.py --coverage-json coverage.json --enforce
      - name: Upload Coverage Artifacts
        if: always()
        uses: actions/upload-artifact@v4
      - name: Report the informational Python 3.15 result
        if: always() && matrix.experimental == true
        env:
          STEPS_JSON: ${{ toJSON(steps) }}
        run: |
          python3 - <<'PY'
          print("${{ toJSON(steps) }}")
          PY
  integration-tests:
    needs: [pre-commit]
    runs-on: ubuntu-latest
    steps:
      - name: Install dependencies
        run: pip install -e ".[test]"
      - name: Run Integration Tests (-m integration)
        run: |
          set +e
          python -m pytest \\
            -m "integration" \\
            tests/ \\
            --junit-xml reports/junit/junit-integration.xml
          rc=$?
          set -e
          if [ "$rc" = "5" ]; then
            echo "::notice::No integration-marked tests collected -- treating as skip."
            exit 0
          fi
          if [[ $rc == 3 ]]; then
            exit 0
          fi
          exit "$rc"
  generator-parity:
    needs: [pre-commit]
    runs-on: ubuntu-latest
    steps:
      - name: Install dependencies (including the server)
        run: |
          pip install -e ".[test]"
          pip install "fake-server[api]"
      - name: Confirm the server is importable
        run: python -c "import fake_server; print('ok')"
      - name: Run Generator Parity Cross-Check
        env:
          FAKE_REQUIRE_LIVE: "1"
        run: |
          python -m pytest tests/test_demo.py --verbose -rs
  security:
    needs: [pre-commit]
    runs-on: ubuntu-latest
    steps:
      - name: Install security tools
        run: pip install "bandit[sarif]"
      - name: Run Bandit (SAST)
        run: |
          bandit -r fake_client -f sarif -o reports/security/bandit.sarif --exit-zero
      - name: Run pip-audit (Dependency Vulnerabilities)
        run: |
          pip install -e ".[test]"
          pip list --format=freeze > reports/security/requirements.txt
      - name: Gitleaks pull-request scan self-test (real engine)
        env:
          FAKE_PARITY_REQUIRED: "1"
        run: python -m pytest tests/test_demo.py -v -v
  dispatch-only:
    if: github.event_name == 'repository_dispatch'
    runs-on: ubuntu-latest
    steps:
      - name: A job a pull request never runs
        run: python -m pytest tests/
  build:
    needs: [unit-tests]
    runs-on: ubuntu-latest
    steps:
      - name: Build sdist and wheel
        run: python -m build --sdist --wheel
"""

DC_SCHEDULED_YML = """\
name: Scheduled Tests
on:
  schedule:
    - cron: '0 6 * * *'
  workflow_dispatch:
jobs:
  slow-or-integration-tests:
    runs-on: ubuntu-latest
    steps:
      - name: Install dependencies
        run: |
          pip install -e ".[test]" || pip install -e ".[dev]" || pip install -e .
      - name: Run slow / integration tests
        run: |
          mkdir -p reports/junit
          set +e
          python -m pytest \\
            -m integration \\
            --tb=short \\
            --junitxml=reports/junit/junit-slow.xml
          rc=$?
          set -e
          if [ "$rc" -eq 5 ]; then
            echo "::notice::No integration tests collected."
            exit 0
          fi
          exit "$rc"
"""

TOOLING_YML = """\
name: Tooling
on:
  pull_request:
    branches: [main]
jobs:
  tooling:
    runs-on: ubuntu-latest
    steps:
      - name: Install the tooling's dependency
        run: |
          python -m pip install --upgrade "pip>=26.1.1"
          pip install "pyyaml>=6.0.1" ./local-tool
      - name: Run the tooling suites
        run: |
          set -euo pipefail
          # tests/test_ghost.py: a comment names a suite; it is not one
          python3 -m unittest -v tests/test_alpha.py
          python3 -m unittest -v tests/test_beta.py  # a trailing comment
          python3 -m unittest -v tests/test_gamma.py
  second:
    runs-on: ubuntu-latest
    steps:
      - name: The same suite again
        run: python3 -m unittest -v tests/test_alpha.py
  for-another-event:
    if: github.event_name == 'repository_dispatch'
    runs-on: ubuntu-latest
    steps:
      - name: Never on a pull request
        run: python3 -m unittest -v tests/test_dispatch_only.py
"""

SCHEDULE_ONLY_YML = """\
name: Scheduled scan
on:
  schedule:
    - cron: "0 3 * * 1"
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - name: A scheduled-only suite
        run: python3 -m unittest -v tests/test_scheduled_only.py
"""

REC_DEMO_YML = """\
name: CI -- demo
on:
  pull_request:
  push:
    branches: [main]
jobs:
  changes:
    runs-on: ubuntu-latest
    steps:
      - name: Decide
        run: |
          git diff --name-only "$BASE" HEAD | grep -qE '^(juniper-recurrence-demo/|\\.github/workflows/ci-recurrence-demo\\.yml$)'
  lint:
    runs-on: ubuntu-latest
    steps:
      - name: Lint
        run: ruff check .
  test:
    needs: [changes]
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: juniper-recurrence-demo
    steps:
      - name: Install
        run: pip install -e ".[test]"
      - name: Test
        run: python -m pytest --cov=juniper_recurrence_demo --cov-report=json:coverage.json --cov-fail-under=90
      - name: Gate
        run: |
          pip install "juniper-ci-tools>=0.9.0,<0.10.0"
          python ../gate.py --coverage-json coverage.json --enforce
  test-torch:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: juniper-recurrence-demo
    steps:
      - name: Install
        run: pip install -e ".[test]"
      - name: Test the torch readout
        run: python -m pytest tests/test_demo.py -ra
  test-docs:
    runs-on: ubuntu-latest
    steps:
      - name: A test-* job that runs no pytest is no lane
        run: echo docs
"""

REC_BENCH_YML = """\
name: CI -- bench
on: [pull_request, push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Install
        run: pip install -e "./juniper-recurrence-demo[test]"
      - name: Test the bench
        run: python -m pytest bench/ -ra
      - name: A dispatch-only step
        if: github.event_name == 'repository_dispatch'
        run: python -m pytest bench/ --slow
"""

REC_TOOLING_YML = """\
name: Tooling
on: [pull_request]
jobs:
  suites:
    runs-on: ubuntu-latest
    steps:
      - name: Run the runner's suite
        run: python3 -m unittest -v tests/test_alpha.py
"""

REC_MANUAL_YML = """\
name: Manual
on: workflow_dispatch
jobs:
  manual:
    runs-on: ubuntu-latest
    steps:
      - name: A suite only a dispatch runs
        run: python3 -m unittest -v tests/test_beta.py
"""

PYTEST_STUB = """\
    import json
    import os
    import sys
    from pathlib import Path

    import {module}

    args = sys.argv[1:]
    keys = ("COVERAGE_FAIL_UNDER", "PYTHON_TEST_VERSION", "JOB_LEVEL", "FAKE_CI_ONLY", "FAKE_REQUIRE_LIVE", "FAKE_PARITY_REQUIRED")
    record = {{
        "argv": args,
        "cwd": os.getcwd(),
        "PYTHONPATH": os.environ.get("PYTHONPATH"),
        "COVERAGE_FILE": os.environ.get("COVERAGE_FILE"),
        "module": {module}.__file__,
        "env": {{key: os.environ.get(key) for key in keys}},
    }}
    Path(os.environ["FAKE_STATE"], os.environ.get("FAKE_PYTEST_RECORD", "pytest") + ".json").write_text(json.dumps(record))
    for arg in args:  # write every report where it was told to: a path left unrouted lands in the checkout
        if arg.startswith("--junitxml="):
            target = Path(arg.split("=", 1)[1])
        elif arg.startswith("--cov-report=") and ":" in arg and arg.split("=", 1)[1].split(":", 1)[0] in ("xml", "json", "html"):
            target = Path(arg.split(":", 1)[1])
        else:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({{"totals": {{"percent_covered": 100.0}}}}))
    if "--junit-xml" in args:
        target = Path(args[args.index("--junit-xml") + 1])
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("<testsuites/>")
    if any(arg.startswith("--cov=") for arg in args):
        Path(os.environ.get("COVERAGE_FILE", ".coverage")).write_text("fake coverage data")
    rc = int(os.environ.get("FAKE_PYTEST_RC", "5" if "integration" in args else "0"))
    if os.environ.get("FAKE_PYTEST_SILENT"):
        sys.exit(rc)
    if os.environ.get("FAKE_PYTEST_MANY"):
        for number in range(12):
            print(f"FAILED tests/test_demo.py::test_{{number}} - boom")
        print("12 failed in 0.01s")
        sys.exit(1)
    print({{0: "1 passed in 0.01s", 5: "12 deselected in 0.01s"}}.get(rc, "FAILED tests/test_demo.py::test_demo - boom\\n1 failed in 0.01s"))
    sys.exit(rc)
    """

COVERAGE_STUB = """\
    import json
    import os
    import sys
    from pathlib import Path

    data = os.environ.get("COVERAGE_FILE", ".coverage")
    record = {"argv": sys.argv[1:], "cwd": os.getcwd(), "COVERAGE_FILE": os.environ.get("COVERAGE_FILE"), "data_exists": Path(data).is_file()}
    Path(os.environ["FAKE_STATE"], "coverage-report.json").write_text(json.dumps(record))
    rc = int(os.environ.get("FAKE_COVERAGE_RC", "0"))
    if rc and not os.environ.get("FAKE_COVERAGE_SILENT"):
        print("Coverage failure: total of 76.50 is less than fail-under=77.00")
    elif not rc:
        print("TOTAL  10  0  100.00%")
    sys.exit(rc)
    """

GATE = """\
    import json
    import os
    import sys
    from pathlib import Path

    args = sys.argv[1:]
    report = Path(args[args.index("--coverage-json") + 1])
    Path(os.environ["FAKE_STATE"], "gate.json").write_text(json.dumps({"argv": args, "cwd": os.getcwd(), "report_exists": report.is_file()}))
    sys.exit(int(os.environ.get("FAKE_GATE_RC", "0" if report.is_file() else "1")))
    """

SUITES = {
    "tests/__init__.py": "",
    "tests/test_alpha.py": """\
        import os
        import unittest

        if os.environ.get("FAKE_ALPHA_CRASH"):
            raise SystemExit(3)


        class AlphaTest(unittest.TestCase):
            def test_cap_one(self):
                self.assertTrue(True)

            def test_two(self):
                self.assertTrue(True)

            @unittest.skip("a skipped test")
            def test_skipped(self):
                pass
        """,
    "tests/test_beta.py": """\
        import os
        import unittest
        from pathlib import Path


        class BetaTest(unittest.TestCase):
            def test_fails(self):
                mode = os.environ.get("FAKE_BETA", "fail")
                if mode == "flaky":
                    marker = Path(os.environ["FAKE_STATE"]) / "beta-ran-once"
                    if not marker.exists():
                        marker.write_text("1")
                        self.fail("the first attempt fails")
                    return
                self.assertEqual(mode, "pass", "beta was told to fail")
        """,
    "tests/test_gamma.py": """\
        # Gamma reads what util/check.py prints and uses tests/helper_mod.py (the --changed tests need both names).
        import json
        import os
        import subprocess
        import sys
        import time
        import unittest
        from pathlib import Path

        KEYS = ["TMPDIR", "GIT_CEILING_DIRECTORIES", "DBUS_SESSION_BUS_ADDRESS", "PYTHONPATH", "PYTHONHOME", "DISPLAY",
                "WAYLAND_DISPLAY", "PYTHONUNBUFFERED", "CLAUDE_FAKE", "JUNIPER_FAKE", "WTC_FAKE", "FAKE_DRIFT"]


        class GammaTest(unittest.TestCase):
            def test_environment(self):
                state = Path(os.environ["FAKE_STATE"])
                record = {key: os.environ.get(key) for key in KEYS}
                record["stdin"] = sys.stdin.read()
                (state / "gamma-env.json").write_text(json.dumps(record))
                if os.environ.get("FAKE_GAMMA_CHILD"):
                    child = subprocess.Popen(["sleep", "300"])
                    (state / "gamma-child.pid").write_text(str(child.pid))
                seconds = float(os.environ.get("FAKE_GAMMA_SLEEP", "0"))
                if seconds:
                    (state / "gamma-sleeping").write_text("1")
                    time.sleep(seconds)
        """,
    "tests/test_scheduled_only.py": "import unittest\n",
    "tests/test_dispatch_only.py": "import unittest\n",
    "tests/helper_mod.py": "VALUE = 1\n",
    "util/check.py": "import os\nimport sys\n\nprint('check ok', sys.argv[1:])\nsys.exit(int(os.environ.get('FAKE_CHECK_RC', '0')))\n",
    "gate.py": GATE,
}

ML_FILES = {
    **SUITES,
    "pyproject.toml": '[project]\nname = "juniper-fake-ml"\nversion = "0.0.1"\n',
    "scripts/test_shell.bash": '#!/usr/bin/env bash\necho "PASS: shell"\n',
    "juniper-demo/pyproject.toml": """\
        [project]
        name = "juniper-demo"
        version = "0.0.1"
        dependencies = []

        [project.optional-dependencies]
        test = []
        """,
    "juniper-demo/juniper_demo/__init__.py": "VALUE = 1\n",
    "juniper-demo/tests/__init__.py": "",
    "juniper-demo/tests/test_demo.py": "# names util/check.py\ndef test_demo():\n    assert True\n",
    "juniper-demo/tests/test_cli.py": "def test_cli():\n    assert True\n",
    "juniper-demo/tests/nested/test_cli.py": "def test_nested_cli():\n    assert True\n",
    "juniper-demo/build/lib/test_built.py": "a build directory's copy: never a test file of the lane\n",
    "juniper-demo/pytest.py": PYTEST_STUB.replace("{module}", "juniper_demo").replace("{{", "{").replace("}}", "}"),
    "juniper-other/pyproject.toml": '[project]\nname = "juniper-other"\nversion = "0.0.1"\n',
    "juniper-other/juniper_other/__init__.py": "VALUE = 2\n",
    "juniper-other/tests/test_other.py": "def test_other():\n    assert True\n",
    "pytest.py": PYTEST_STUB.replace("{module}", "juniper_other").replace("{{", "{").replace("}}", "}"),
}

DC_FILES = {
    **SUITES,
    "pyproject.toml": """\
        [project]
        name = "fake-data-client"
        version = "0.0.1"
        dependencies = []

        [project.optional-dependencies]
        test = []
        dev = ["black>=23.0.0"]
        """,
    "local-tool/pyproject.toml": '[project]\nname = "local-tool"\nversion = "0.0.1"\n',
    "fake_client/__init__.py": "VALUE = 1\n",
    "tests/conftest.py": "",
    "tests/test_demo.py": "def test_demo():\n    assert True\n",
    "tests/test_widget.py": "# The widget reads util/check.py.\ndef test_widget():\n    assert True\n",
    "pytest.py": PYTEST_STUB.replace("{module}", "fake_client").replace("{{", "{").replace("}}", "}"),
    "coverage.py": COVERAGE_STUB,
}

REC_FILES = {
    **SUITES,
    "juniper-recurrence-demo/pyproject.toml": """\
        [project]
        name = "juniper-recurrence-demo"
        version = "0.0.1"
        dependencies = ["numpy>=1.0"]

        [project.optional-dependencies]
        test = ["pytest>=8.0"]
        """,
    "juniper-recurrence-demo/juniper_recurrence_demo/__init__.py": "VALUE = 1\n",
    "juniper-recurrence-demo/tests/test_demo.py": "def test_demo():\n    assert True\n",
    "juniper-recurrence-demo/pytest.py": PYTEST_STUB.replace("{module}", "juniper_recurrence_demo").replace("{{", "{").replace("}}", "}"),
    "bench/__init__.py": "",
    "bench/test_bench.py": "def test_bench():\n    assert True\n",
    "pytest.py": PYTEST_STUB.replace("{module}", "bench").replace("{{", "{").replace("}}", "}"),
}

WORKFLOWS = {
    "ml": {"ci.yml": ML_CI_YML, "ci-demo.yml": ML_DEMO_YML, "ci-other.yml": ML_OTHER_YML},
    "dc": {"ci.yml": DC_CI_YML, "scheduled-tests.yml": DC_SCHEDULED_YML, "tooling.yml": TOOLING_YML, "security-scan.yml": SCHEDULE_ONLY_YML},
    "rec": {"ci-recurrence-demo.yml": REC_DEMO_YML, "ci-recurrence-bench.yml": REC_BENCH_YML, "tooling.yml": REC_TOOLING_YML, "manual.yml": REC_MANUAL_YML},
}
FILES = {"ml": ML_FILES, "dc": DC_FILES, "rec": REC_FILES}

KEPT = "Check the environment is the right one"
OPT_IN = {
    "generator-parity": "needs fake-server[api]: FAKE_REQUIRE_LIVE makes its skip a failure",
    "security": "needs the gitleaks binary on PATH: FAKE_PARITY_REQUIRED makes its skip a failure",
}


def ml_spec(root: Path, **overrides) -> rt.RepoSpec:
    fields = dict(
        project="juniper-fake-ml",
        script=str(root / "util" / "run_tests.py"),
        lanes=(
            rt.step_lane("unittest", "ci.yml", "tests", "Run Python regression tests", deps="Install test dependencies", groups=("regression",)),
            rt.step_lane("bash", "ci.yml", "tests", "Run bash regression tests", groups=("regression",)),
            rt.job_lanes(workflows=("ci-*.yml",), jobs=("test",), name=rt.workflow_stem("ci-"), directory="juniper-{name}", keep=(KEPT,), groups=("packages",)),
        ),
        docs="docs/REFERENCE.md, 'Running tests locally'",
        description="The fake ml repo's tests.",
        epilog="selectors: all, regression, packages",
        flags=(rt.EnvFlag("--force-drift", "FAKE_DRIFT", "the drift suites run outside CI"),),
        unwired_hint="the wiring check fails until ci.yml runs it",
    )
    fields.update(overrides)
    return rt.RepoSpec(**fields)


def dc_spec(root: Path, **overrides) -> rt.RepoSpec:
    fields = dict(project="fake-data-client", script=str(root / "util" / "run_tests.py"), lanes=(rt.unittest_lane(), rt.job_lanes()), opt_in=OPT_IN, strip_suffix="-tests")
    fields.update(overrides)
    return rt.RepoSpec(**fields)


def rec_spec(root: Path, **overrides) -> rt.RepoSpec:
    fields = dict(
        project="juniper-recurrence",
        script=str(root / "util" / "run_tests.py"),
        lanes=(rt.unittest_lane(), rt.job_lanes(workflows=("ci-recurrence-*.yml",), jobs=("test", "test-*"), name=rt.workflow_stem("ci-recurrence-"), optional={"test-*": "{workflow}'s {job} job"}, groups=("packages",))),
        marker="ci-recurrence-*.yml",
        pyproject=False,
        docs="README.md, 'Running tests locally'",
    )
    fields.update(overrides)
    return rt.RepoSpec(**fields)


SPECS = {"ml": ml_spec, "dc": dc_spec, "rec": rec_spec}
FAKE_KEYS = (
    "FAKE_BETA",
    "FAKE_GAMMA_SLEEP",
    "FAKE_GAMMA_CHILD",
    "FAKE_PYTEST_RC",
    "FAKE_PYTEST_RECORD",
    "FAKE_PYTEST_SILENT",
    "FAKE_PYTEST_MANY",
    "FAKE_COVERAGE_RC",
    "FAKE_COVERAGE_SILENT",
    "FAKE_GATE_RC",
    "FAKE_CHECK_RC",
    "FAKE_CHECK_ENV_RC",
    "FAKE_ALPHA_CRASH",
    "FAKE_REQUIRE_LIVE",
    "FAKE_PARITY_REQUIRED",
    "FAKE_CI_ONLY",
    "FAKE_DRIFT",
    "FAKE_PROBE_REPORT",
    "JOB_LEVEL",
    "NO_COLOR",
)


class Ran(NamedTuple):
    code: int
    out: str
    err: str


def _pid_gone(pid: int, wait: float = 10.0) -> bool:
    deadline = time.monotonic() + wait
    while time.monotonic() < deadline:
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return True
        stat = Path(f"/proc/{pid}/stat")
        if stat.exists() and ") Z " in stat.read_text():
            return True  # a zombie awaiting its reaper: dead
        time.sleep(0.05)
    return False


class Repo:
    """A disposable fake checkout of one shape, its spec, and an in-process runner."""

    def __init__(self, base: Path, shape: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> None:
        self.shape = shape
        base = base / shape  # two shapes in one test get one directory each
        self.root = base / "checkout"
        self.logs = base / "logs"
        self.state = base / "state"
        self.state.mkdir(parents=True)
        self.workflows = self.root / ".github" / "workflows"
        self.workflows.mkdir(parents=True)
        for name, text in WORKFLOWS[shape].items():
            (self.workflows / name).write_text(text)
        for rel, text in FILES[shape].items():
            self.write(rel, textwrap.dedent(text))
        self.spec = SPECS[shape](self.root)
        self.monkeypatch = monkeypatch
        self.capsys = capsys

    def write(self, rel: str, text: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def edit(self, rel: str, old: str, new: str) -> None:
        path = self.root / rel
        text = path.read_text()
        assert old in text, (rel, old)
        path.write_text(text.replace(old, new))

    def lanes(self) -> dict[str, rt.Lane]:
        return rt.discover(self.root, self.spec)

    def pick(self, *tokens: str, cwd: Path | None = None) -> dict[str, list[str]]:
        lanes = self.lanes()
        picker = rt.Picker(lanes)
        for token in tokens:
            rt.resolve_selector(token, lanes, self.root, cwd or self.root, picker, self.spec)
        return {job.id: job.targets for job in picker.jobs()}

    def run(self, *args: str, log_dir: bool = True, **env: str) -> Ran:
        with self.monkeypatch.context() as patch:
            for key in FAKE_KEYS:
                patch.delenv(key, raising=False)
            patch.setenv("FAKE_STATE", str(self.state))
            for key, value in env.items():
                patch.setenv(key, value)
            patch.chdir(self.root)
            self.capsys.readouterr()
            argv = ["--checkout", str(self.root), *(["--log-dir", str(self.logs)] if log_dir else []), "--color", "never", *args]
            code = rt.main(self.spec, argv)
            out, err = self.capsys.readouterr()
        return Ran(code, out, err)

    def run_dir(self) -> Path:
        runs = sorted(path for path in self.logs.iterdir() if path.is_dir() and path.name != "latest")
        assert runs, "no run directory was written"
        return runs[-1]

    def summary(self) -> dict:
        return json.loads((self.run_dir() / "summary.json").read_text())

    def jobs(self) -> dict[str, dict]:
        return {job["id"]: job for job in self.summary()["jobs"]}

    def read_state(self, name: str) -> dict:
        return json.loads((self.state / name).read_text())

    def assert_checkout_clean(self) -> None:
        for name in ("reports", "coverage.json", ".coverage", "htmlcov", "juniper-demo/coverage.json"):
            assert not (self.root / name).exists(), f"{name} landed in the checkout"

    def git(self, *args: str) -> str:
        config = self.root.parent / "gitconfig"
        config.touch()
        env = rt._Env(os.environ)
        env.update(
            GIT_CONFIG_GLOBAL=str(config),
            GIT_CONFIG_NOSYSTEM="1",
            GIT_AUTHOR_NAME="run-tests",
            GIT_AUTHOR_EMAIL="run-tests@example.invalid",
            GIT_COMMITTER_NAME="run-tests",
            GIT_COMMITTER_EMAIL="run-tests@example.invalid",
            GIT_CEILING_DIRECTORIES=str(self.root.parent),
        )
        for key in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
            env.pop(key, None)
        return subprocess.run(["git", "-C", str(self.root), *args], env=env, capture_output=True, text=True, check=True).stdout  # nosec B603 B607 - fixed git argv in the fake checkout

    def commit(self, message: str) -> None:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)


@pytest.fixture
def scratch() -> Iterator[Path]:
    """A directory under the juniper-ml checkout's gitignored tmp/ (on a CI runner the default temp is the system one)."""
    base = ROOT / "tmp"
    base.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="run-tests-engine-", dir=base) as tmp:
        yield Path(tmp)


@pytest.fixture
def ml(scratch: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> Repo:
    return Repo(scratch, "ml", monkeypatch, capsys)


@pytest.fixture
def dc(scratch: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> Repo:
    return Repo(scratch, "dc", monkeypatch, capsys)


@pytest.fixture
def rec(scratch: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture) -> Repo:
    return Repo(scratch, "rec", monkeypatch, capsys)


def needs_git() -> None:
    if shutil.which("git") is None:
        pytest.skip("git is not installed")


# ---------------------------------------------------------------------------------------------------------------
# The public API
# ---------------------------------------------------------------------------------------------------------------


def test_the_public_api_is_what_all_names() -> None:
    for name in rt.__all__:
        assert hasattr(rt, name), name
    assert rt.ENGINE_VERSION == re.search(r'__version__ = "([^"]+)"', (Path(rt.__file__).with_name("_version.py")).read_text()).group(1)


def test_the_engine_version_is_read_beside_the_module(monkeypatch: pytest.MonkeyPatch, scratch: Path) -> None:
    lonely = scratch / "run_tests.py"
    monkeypatch.setattr(rt, "__file__", str(lonely))
    assert rt._engine_version() == "unknown"
    (scratch / "_version.py").write_text("no version here\n")
    assert rt._engine_version() == "unknown"
    (scratch / "_version.py").write_text('__version__ = "9.8.7"\n')
    assert rt._engine_version() == "9.8.7"


def test_a_spec_refuses_what_cannot_work(scratch: Path) -> None:
    good = dict(project="x", script=str(scratch / "util" / "run_tests.py"), lanes=[rt.unittest_lane()])
    spec = rt.RepoSpec(**good)
    assert spec.lanes == (rt.unittest_lane(),) and spec.groups == ("all", "optional")
    for overrides, needle in (({"project": ""}, "project is empty"), ({"lanes": ()}, "no lane strategy"), ({"lanes": ("unittest",)}, "not a lane strategy"), ({"flags": (rt.EnvFlag("-f", "X", "h"),)}, "--long option")):
        with pytest.raises(ValueError, match=needle):
            rt.RepoSpec(**{**good, **overrides})
    assert rt.EnvFlag("--force-drift", "X", "h").dest == "force_drift"


def test_groups_come_from_the_strategies_in_order(scratch: Path) -> None:
    spec = ml_spec(scratch)
    assert spec.groups == ("all", "regression", "packages", "optional")
    assert dc_spec(scratch).groups == ("all", "optional")


def test_workflow_stem_names_lanes_by_their_workflow() -> None:
    name = rt.workflow_stem("ci-recurrence-")
    assert name(Path("ci-recurrence-model.yml"), "test") == "model"
    assert name(Path("ci-recurrence-model.yml"), "test-torch") == "model-torch"
    assert name(Path("ci-recurrence-model.yml"), "other") == "model-other"
    assert name(Path("tooling.yml"), "test") == "tooling"
    assert rt.JOB_ID(Path("ci.yml"), "unit-tests") == "unit-tests"


# ---------------------------------------------------------------------------------------------------------------
# Reading the workflows
# ---------------------------------------------------------------------------------------------------------------


def test_comments_are_stripped_as_bash_reads_them() -> None:
    assert rt.strip_comment("pip install wheel  # a comment") == "pip install wheel"
    assert rt.strip_comment('echo "a # b" c') == 'echo "a # b" c'
    assert rt.strip_comment("echo a#b") == "echo a#b"
    assert rt.strip_comment("echo 'it''s' \\# not a comment") == "echo 'it''s' \\# not a comment"
    assert rt.split_command("python3 -m unittest -v tests/test_x.py  # tests/test_ghost.py", "t") == ["python3", "-m", "unittest", "-v", "tests/test_x.py"]
    with pytest.raises(rt.UsageError, match="cannot parse"):
        rt.split_command('echo "unterminated', "t")


def test_continuations_join_and_comment_lines_drop() -> None:
    assert rt.logical_lines("# a comment\npython -m pytest \\\n  --cov=x \\\n  -q\n\necho done\n") == ["python -m pytest --cov=x -q", "echo done"]
    assert rt.logical_lines("pytest \\") == ["pytest"]
    assert rt.logical_lines("echo a\\\\\n") == ["echo a\\\\"]
    assert rt.logical_lines(None) == []


def test_commands_that_need_a_shell_are_named() -> None:
    for line in ("cd tests && python3 -m unittest t.py", "pytest | tee log", "python $FILE", "export A=1", "FOO=1 pytest", "cmd 2>&1", "echo `date`"):
        assert rt.shell_need(rt.split_command(line, "t")) is not None, line
    assert rt.shell_need(rt.split_command('juniper-coverage-gap-map --coverage-json coverage.json --omit "*/__main__.py"', "t")) is None
    assert rt.segments(rt.split_command("a && b || c", "t")) == [["a"], ["b"], ["c"]]


def test_expand_substitutes_what_the_workflow_sets() -> None:
    env = {"FLOOR": "80", "SPACED": "a b", "CI_ONLY": None}
    assert rt.expand("python -m coverage report --fail-under=${FLOOR}", env) == "python -m coverage report --fail-under=80"
    assert rt.expand("x --fail-under=$FLOOR y", env) == "x --fail-under=80 y"
    assert rt.expand("x --fail-under=${{ env.FLOOR }}", env) == "x --fail-under=80"
    assert rt.expand('x "$FLOOR"', env) == 'x "80"'
    for line in ("echo '$FLOOR'", "x \\$FLOOR", "x $SPACED", "x $CI_ONLY", "x ${{ env.CI_ONLY }}", "x $RUNNER_TEMP", "x ${{ matrix.os }}", "rc=$?", "x $"):
        assert rt.expand(line, env) == line, line


def test_env_blocks_layer_and_hide_what_only_ci_knows() -> None:
    block = rt.env_block({"A": "1", "B": "${{ env.A }}-x", "C": "${{ secrets.T }}", "D": True, "E": 80, "F": "${{ env.UNSET }}", "G": None}, {"A": "0"})
    assert block == {"A": "1", "B": "0-x", "C": None, "D": "true", "E": "80", "F": "", "G": ""}
    assert rt.env_block({"A": "2"}, {"A": "1", "Z": "z"}) == {"A": "2", "Z": "z"}
    assert rt.env_block({"B": "${{ env.C }}"}, {"C": None}) == {"C": None, "B": None}
    assert rt.env_block(None, {"A": "1"}) == {"A": "1"}


def test_pip_install_arguments_and_fallbacks() -> None:
    args = rt.pip_install_args(rt.split_command('python -m pip install -U "pip>=26" -r req.txt -e ".[test]" --editable=./other --index-url https://example.invalid/simple wheel -e', "t"))
    assert rt.parse_pip_install(args) == (["pip>=26", "wheel"], [".[test]", "./other"])
    assert rt.pip_install_args(["pip3", "install", "x"]) == ["x"]
    assert rt.pip_install_args(["echo", "pip", "install"]) is None
    assert rt.install_parts(rt.split_command('pip install -e ".[test]" || pip install -e ".[dev]" || pip install -e .', "t")) == [["pip", "install", "-e", ".[test]"]]
    assert len(rt.install_parts(rt.split_command('pip install -U pip && pip install -e ".[test]"', "t"))) == 2
    assert rt.requirement_name("Juniper_CI.Tools>=0.9") == "juniper-ci-tools"
    assert rt.requirement_name(">=1") == ">=1"


def test_local_paths_are_not_requirements() -> None:
    for spec in (".", "./sub/package[test,extra]", "../x", "sub/", "sub/dir[test]", "~/pkg", "/abs/pkg"):
        assert rt.is_local_path(spec), spec
    for spec in ("juniper-ci-tools>=0.9.0,<0.10.0", "pyyaml", "pkg @ https://example.invalid/pkg.whl", "https://example.invalid/a/b.whl"):
        assert not rt.is_local_path(spec), spec


def test_editable_targets_projects_and_packages(scratch: Path) -> None:
    base = Path("/checkout")
    assert rt.editable_target(".[test]", base) == (base, ["test"])
    assert rt.editable_target("./sub[test,bench]", base) == (base / "sub", ["test", "bench"])
    assert rt.editable_target("juniper-model-core", base) == (base / "juniper-model-core", [])
    (scratch / "pyproject.toml").write_text('[project]\nname = "p"\ndependencies = ["a"]\n[project.optional-dependencies]\ntest = ["b"]\n')
    assert rt.project_requirements(scratch, ["test", "missing"]) == ("p", ["a", "b"])
    (scratch / "pyproject.toml").write_text("[project\n")
    with pytest.raises(rt.UsageError):
        rt.project_requirements(scratch, [])
    (scratch / "pkg").mkdir()
    (scratch / "pkg" / "__init__.py").write_text("")
    (scratch / "tests").mkdir()
    (scratch / "tests" / "__init__.py").write_text("")
    (scratch / "not-an-identifier").mkdir()
    assert rt.import_packages(scratch) == {"pkg": scratch / "pkg"}
    assert rt.import_packages(scratch / "missing") == {}


def test_load_workflow_refuses_what_is_no_workflow(scratch: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = scratch / "w.yml"
    path.write_text("- a list\n")
    with pytest.raises(rt.UsageError, match="not a workflow"):
        rt.load_workflow(path)
    path.write_text("a: [unclosed\n")
    with pytest.raises(rt.UsageError, match="cannot read"):
        rt.load_workflow(path)
    with pytest.raises(rt.UsageError, match="cannot read"):
        rt.load_workflow(scratch / "missing.yml")
    monkeypatch.setitem(sys.modules, "yaml", None)
    with pytest.raises(rt.UsageError, match="PyYAML is needed"):
        rt.load_workflow(path)


def test_the_rc_capture_rule() -> None:
    tail = ["rc=$?", 'if [ "$rc" = "5" ]; then', "exit 0", "fi", 'exit "$rc"']
    assert rt.exit_rule(["python -m pytest -m integration", *tail], "t") == (["python -m pytest -m integration"], (5,))
    assert rt.exit_rule(["pytest", "rc=$?", 'if [ "$rc" -eq 5 ]; then', "exit 0", "fi", "if [[ $rc == 2 ]]; then", "exit 0", "fi", "exit $rc"], "t") == (["pytest"], (5, 2))
    assert rt.exit_rule(["python -m pytest"], "t") == (["python -m pytest"], ())
    for lines in (["pytest", "rc=$?", "exit $rc"], ["pytest", "status=$?", 'if [ "$rc" = "5" ]; then', "exit 0", "fi", 'exit "$rc"'], ["pytest", *tail, "echo after"], ["pytest || rc=$?", 'exit "$rc"'], ["rc=$?"]):
        with pytest.raises(rt.UsageError, match="captures an exit code"):
            rt.exit_rule(lines, "t")


def test_lane_commands() -> None:
    for line in ("python -m pytest tests/", "pytest -q", "python3 -m coverage report --fail-under=80", "coverage report", "juniper-coverage-gap-map --coverage-json c.json --enforce", "x --coverage-json=c.json"):
        assert rt._is_lane_command(rt.split_command(line, "t")), line
    for line in ("python -m coverage run x.py", "bandit -r x", "python -c 'import pytest'", "python3 -m unittest t.py"):
        assert not rt._is_lane_command(rt.split_command(line, "t")), line
    assert rt._runs_lane_command('pytest "unterminated') and not rt._runs_lane_command('echo "unterminated')
    assert not rt._runs_unittest('python3 -m unittest "unterminated')
    assert rt._split_unittest(["-v", "-k", "cap", "-t", ".", "tests/a.py", "tests/b.py"]) == (["-v", "-k", "cap", "-t", "."], ["tests/a.py", "tests/b.py"])


def test_report_paths_move_into_the_run_directory() -> None:
    run = Path("/run/unit-tests")
    assert rt._report_path("xml:reports/coverage.xml", run) == "xml:/run/unit-tests/coverage.xml"
    assert rt._report_path("html:reports/htmlcov", run) == "html:/run/unit-tests/htmlcov"
    for spec in ("term-missing", "term-missing:skip-covered", "term:skip-covered", "json"):
        assert rt._report_path(spec, run) == spec
    assert rt.gate_argv(["gate", "--coverage-json", "a/c.json", "--coverage-json=b/d.json", "x"], run) == ["gate", "--coverage-json", "/run/unit-tests/c.json", "--coverage-json=/run/unit-tests/d.json", "x"]


def test_programs_resolve_to_the_interpreter_beside_it_or_path(scratch: Path) -> None:
    env = rt._Env(PATH=str(scratch / "nowhere"))
    assert rt.resolve_program(["pytest", "-q"], "/py/bin/python", env) == (["/py/bin/python", "-m", "pytest", "-q"], "")
    assert rt.resolve_program(["python3", "x.py"], "/py/bin/python", env) == (["/py/bin/python", "x.py"], "")
    assert rt.resolve_program(["./tool", "a"], "/py/bin/python", env) == (["./tool", "a"], "")
    bindir = scratch / "bin"
    bindir.mkdir()
    (bindir / "tool").write_text("#!/bin/sh\n")
    (bindir / "tool").chmod(0o755)
    assert rt.resolve_program(["tool", "a"], str(bindir / "python"), env) == ([str(bindir / "tool"), "a"], "")
    program, missing = rt.resolve_program(["no-such-tool"], str(bindir / "python"), env)
    assert program == ["no-such-tool"] and "no-such-tool is not installed next to" in missing


def test_pytest_options_are_moved_or_dropped_with_their_values() -> None:
    run = Path("/run/lane")
    step = rt.Step("pytest", ["python", "-m", "pytest"], Path("/nowhere"))
    job = rt.Job("lane", "lane", "pytest", [step], 0)
    argv = ["python", "-m", "pytest", "--cov", "pkg", "--cov-report", "xml:r/c.xml", "--cov-report", "term", "-q"]
    assert rt.pytest_argv(argv, step, job, True, run, [], []) == ["python", "-m", "pytest", "--cov", "pkg", "--cov-report", "xml:/run/lane/c.xml", "--cov-report", "term", "-q"]
    assert rt.pytest_argv(argv, step, job, False, run, ["k1"], ["-x"]) == ["python", "-m", "pytest", "-q", "-k", "k1", "-x"]
    assert rt.pytest_argv(["python", "-m", "pytest", "--junitxml=r/j.xml", "--no-cov"], step, job, False, run, [], []) == ["python", "-m", "pytest", "--junitxml=/run/lane/j.xml"]


def test_events_and_steps_for_other_events() -> None:
    assert rt.workflow_events({True: {"pull_request": None, "push": None}}) == {"pull_request", "push"}
    assert rt.workflow_events({"on": "push"}) == {"push"}
    assert rt.workflow_events({True: ["schedule"]}) == {"schedule"}
    assert rt.workflow_events({}) == set()
    assert rt.other_event_only({"if": "github.event_name == 'repository_dispatch'"}) == "repository_dispatch"
    for condition in ("github.event_name == 'pull_request' || github.event_name == 'merge_group'", "github.event_name != 'repository_dispatch'", "always() && matrix.experimental == true", ""):
        assert rt.other_event_only({"if": condition}) == "", condition


def test_the_changes_job_path_filter() -> None:
    job = {"steps": ["not a step", {"run": "git diff --name-only x | grep -qE '^(pkg/|\\.github/workflows/ci\\.yml$)'"}]}
    pattern = rt.changes_filter(job)
    assert re.search(pattern, "pkg/client.py") and not re.search(pattern, "docs/REFERENCE.md")
    assert rt.changes_filter({"steps": [{"run": "echo no filter"}]}) == ""
    assert rt.changes_filter({"steps": [{"run": "grep -E '(unclosed' x"}]}) == ""
    assert rt.changes_filter(None) == ""


def test_result_lines_and_floors_are_read() -> None:
    counts, failed = rt.unittest_counts("FAIL: test_b (tests.test_x.T.test_b)\nERROR: setUpClass (tests.test_x.U)\nFAIL: test_b (tests.test_x.T.test_b)\nRan 12 tests in 0.5s\n\nFAILED (failures=1, errors=1, skipped=3, unexpected successes=1)\n")
    assert counts == {"ran": 12, "failures": 1, "errors": 1, "skipped": 3, "unexpected_successes": 1}
    assert failed == ["tests.test_x.T.test_b", "tests.test_x.U.setUpClass"]
    assert rt.describe_counts("unittest", counts) == "1 failed, 1 errors, 1 unexpected successes of 12, 3 skipped"
    assert rt.describe_counts("unittest", {"ran": 3}) == "3 tests"
    counts, failed = rt.pytest_counts("FAILED tests/test_a.py::test_x - boom\n===== 1 failed, 230 passed, 2 skipped, 1 error in 5.12s =====\n")
    assert counts == {"failed": 1, "passed": 230, "skipped": 2, "errors": 1}
    assert failed == ["tests/test_a.py::test_x"]
    assert rt.pytest_counts("===== no tests ran in 0.01s =====\n") == ({}, [])
    _, failed = rt.pytest_counts("SUBFAILED(name='a b', new='x) y') tests/test_a.py::T::test_y - boom\nSUBFAILED tests/test_a.py::T::test_z\nERROR tests/test_b.py\n")
    assert failed == ["tests/test_a.py::T::test_y", "tests/test_a.py::T::test_z", "tests/test_b.py"], "pytest 9's subTest failures are failures too"
    assert rt._COV_REPORT_FLOOR.search("Coverage failure: total of 79.12 is less than fail-under=80.00").group("total", "floor") == ("79.12", "80.00")
    assert rt._COV_FLOOR.search("FAIL Required test coverage of 80% not reached. Total coverage: 79.50%").group("total", "floor") == ("79.50", "80")
    assert rt.describe_counts("command", {}) == ""


def test_durations_slugs_and_paths() -> None:
    assert (rt.fmt_duration(5.25), rt.fmt_duration(125), rt.fmt_duration(7300)) == ("5.2s", "2m05s", "2h01m")
    assert rt._slug("tests/test_x.py") == "test_x" and rt._slug("util/check.py verify") == "util_check.py_verify" and rt._slug("///") == "job"
    assert rt._display_path(Path("/a/b"), Path("/a")) == "b" and rt._display_path(Path("/a"), Path("/a")) == "." and rt._display_path(Path("/x"), Path("/a")) == "/x"
    assert rt._has_glob("a*") and not rt._has_glob("a")
    assert repr(rt._Env({"SECRET_VALUE": "hidden"})) == "<child env: 1 vars (values redacted)>"


def test_origin_verdict(scratch: Path) -> None:
    here = scratch / "pkg"
    assert rt.origin_verdict("pkg", str(here / "__init__.py"), here) == ""
    assert "not from this checkout" in rt.origin_verdict("pkg", "/elsewhere/site-packages/pkg/__init__.py", here)
    assert "not importable" in rt.origin_verdict("pkg", None, here)


# ---------------------------------------------------------------------------------------------------------------
# Discovery: the three shapes
# ---------------------------------------------------------------------------------------------------------------


def test_ml_two_named_steps_and_a_lane_per_package_workflow(ml: Repo) -> None:
    lanes = ml.lanes()
    assert list(lanes) == ["unittest", "bash", "demo", "other"]
    unittest_lane = lanes["unittest"]
    assert [job.id for job in unittest_lane.jobs] == ["tests/test_alpha.py", "tests/test_beta.py", "tests/test_gamma.py", "util/check.py verify"]
    assert [job.kind for job in unittest_lane.jobs] == ["unittest"] * 3 + ["command"]
    assert unittest_lane.requirements == ["pyyaml>=6.0"], "the deps step's installs, without pip itself"
    assert unittest_lane.groups == ("regression",) and unittest_lane.source == ".github/workflows/ci.yml > tests > Run Python regression tests"
    assert [job.id for job in lanes["bash"].jobs] == ["scripts/test_shell.bash"] and lanes["bash"].requirements == []
    demo = lanes["demo"]
    assert [step.label for step in demo.jobs[0].steps] == ["python", "pytest", "coverage-gate"], "the kept step runs first, as in CI"
    assert demo.package_dir == ml.root / "juniper-demo" and demo.pythonpath == [ml.root / "juniper-demo"]
    assert demo.packages == {"juniper_demo": ml.root / "juniper-demo" / "juniper_demo"} and demo.left_out == []
    assert demo.jobs[0].steps[2].hints == ["juniper-ci-tools>=0.9.0,<0.10.0"]
    other = lanes["other"]
    assert other.package_dir == ml.root / "juniper-other", "the spec's directory, not the tests/ directory pytest names"
    assert other.pythonpath == [ml.root / "juniper-other"] and [step.cwd for step in other.jobs[0].steps] == [ml.root, ml.root]


def test_dc_every_job_that_runs_pytest_is_a_lane(dc: Repo) -> None:
    lanes = dc.lanes()
    assert list(lanes) == ["unittest", "unit-tests", "integration-tests", "generator-parity", "security", "slow-or-integration-tests"]
    unit = lanes["unit-tests"]
    assert [step.label for step in unit.jobs[0].steps] == ["pytest", "coverage-floor", "coverage-gate"]
    assert "--fail-under=77" in unit.jobs[0].steps[1].argv
    assert unit.env == {"PYTHON_TEST_VERSION": "3.99", "COVERAGE_FAIL_UNDER": "77", "JOB_LEVEL": "from-3.99"}, "a secret reached the env, or an env: block was not read"
    assert unit.left_out == [] and lanes["integration-tests"].jobs[0].steps[0].tolerated == (5, 3)
    assert lanes["generator-parity"].left_out == ["Confirm the server is importable"]
    assert lanes["security"].left_out == ["Run Bandit (SAST)", "Run pip-audit (Dependency Vulnerabilities)"]
    assert lanes["security"].pythonpath == [dc.root]
    assert lanes["slow-or-integration-tests"].requirements == [], "an install fallback (|| pip install -e .[dev]) was read as an install"
    assert lanes["generator-parity"].requirements == ["fake-server[api]"]
    assert [lane.optional for lane in lanes.values()] == [False, False, False, True, True, True]
    assert lanes["slow-or-integration-tests"].why == "scheduled-tests.yml: CI runs it on schedule, workflow_dispatch, never on a pull request"
    assert lanes["security"].why == OPT_IN["security"]


def test_dc_the_unittest_lane_reads_every_pull_request_workflow(dc: Repo) -> None:
    lane = dc.lanes()["unittest"]
    assert [job.id for job in lane.jobs] == ["tests/test_alpha.py", "tests/test_beta.py", "tests/test_gamma.py"], "a scheduled, a repeated or another event's suite was read"
    assert ".github/workflows/tooling.yml > tooling > Run the tooling suites" in lane.jobs[0].origin
    assert lane.requirements == ["pyyaml>=6.0.1"], "the hosting job's installs, without pip itself or a local path"
    assert lane.source == ".github/workflows/tooling.yml > tooling; .github/workflows/tooling.yml > second"


def test_rec_lanes_by_workflow_with_optional_test_jobs(rec: Repo) -> None:
    lanes = rec.lanes()
    assert list(lanes) == ["unittest", "bench", "demo", "demo-torch"]
    assert [job.id for job in lanes["unittest"].jobs] == ["tests/test_alpha.py"], "a dispatch-only workflow's suite is not in the lane"
    bench = lanes["bench"]
    assert bench.package_dir == rec.root / "bench" and bench.packages["bench"] == rec.root / "bench", "a lane directory that is a package is imported from the root"
    assert [step.argv for step in bench.jobs[0].steps] == [["python", "-m", "pytest", "bench/", "-ra"]], "the dispatch-only step ran"
    demo = lanes["demo"]
    assert demo.path_filter and re.search(demo.path_filter, "juniper-recurrence-demo/x.py") and demo.requirements == ["numpy>=1.0", "pytest>=8.0"]
    assert lanes["demo-torch"].optional and lanes["demo-torch"].why == "ci-recurrence-demo.yml's test-torch job"
    assert lanes["demo"].groups == ("packages",)
    with_dispatch = rec_spec(rec.root, lanes=(rt.unittest_lane(events=rt.LOCAL_EVENTS), *rec.spec.lanes[1:]))
    assert [job.id for job in rt.discover(rec.root, with_dispatch)["unittest"].jobs] == ["tests/test_beta.py", "tests/test_alpha.py"], "manual.yml sorts before tooling.yml"


def test_a_named_step_job_or_workflow_that_is_gone_is_a_usage_error(ml: Repo) -> None:
    for spec, needle in (
        (ml_spec(ml.root, lanes=(rt.step_lane("unittest", "gone.yml", "tests", "x"),)), "no such workflow"),
        (ml_spec(ml.root, lanes=(rt.step_lane("unittest", "ci.yml", "gone", "x"),)), "has no 'gone' job"),
        (ml_spec(ml.root, lanes=(rt.step_lane("unittest", "ci.yml", "tests", "Gone step"),)), "has no step named 'Gone step'"),
        (ml_spec(ml.root, lanes=(rt.step_lane("unittest", "ci.yml", "tests", "x", deps="Gone deps"),)), "has no step named 'Gone deps'"),
    ):
        with pytest.raises(rt.UsageError, match=needle):
            rt.discover(ml.root, spec)
    ml.edit(".github/workflows/ci.yml", '          echo "banner"\n          bash scripts/test_shell.bash\n', '          echo "banner"\n')
    with pytest.raises(rt.UsageError, match="found no command"):
        ml.lanes()


def test_a_job_named_exactly_must_run_pytest_and_a_kept_step_must_exist(ml: Repo, rec: Repo) -> None:
    ml.edit(".github/workflows/ci-demo.yml", "          python -m pytest \\\n", "          python -m pytest_not \\\n")
    with pytest.raises(rt.UsageError, match="found no pytest command"):
        ml.lanes()
    assert "demo-docs" not in rec.lanes(), "a test-* glob match that runs no pytest is no lane, and no error"
    stale = rec_spec(rec.root, lanes=(rt.job_lanes(workflows=("ci-recurrence-*.yml",), keep=("No such step",)),))
    with pytest.raises(rt.UsageError, match="keeps 'No such step'"):
        rt.discover(rec.root, stale)


def test_lane_names_cannot_collide(dc: Repo) -> None:
    dc.write(".github/workflows/zz.yml", "on: [push]\njobs:\n  all:\n    runs-on: x\n    steps:\n      - run: pytest tests/\n")
    with pytest.raises(rt.UsageError, match="collides with another lane or a group"):
        dc.lanes()


def test_an_opt_in_name_no_lane_has_is_a_usage_error(dc: Repo) -> None:
    dc.edit(".github/workflows/ci.yml", "  security:\n", "  security-renamed:\n")
    with pytest.raises(rt.UsageError, match="opt_in names security"):
        dc.lanes()


def test_odd_workflows_are_read_or_skipped_without_guessing(dc: Repo) -> None:
    dc.write(".github/workflows/odd.yaml", "on: [push]\njobs: [not, a, mapping]\n")
    dc.write(".github/workflows/odd2.yml", "on: [push]\njobs:\n  j: just a string\n  k:\n    steps:\n      - just a string\n      - name: no run\n")
    assert "j" not in dc.lanes() and "k" not in dc.lanes()


def test_the_lane_directory_without_a_working_directory_is_the_first_one_pytest_names(dc: Repo) -> None:
    assert dc.lanes()["unit-tests"].package_dir == dc.root / "tests"
    dc.write(".github/workflows/zz.yml", "on: [push]\njobs:\n  bare:\n    runs-on: x\n    steps:\n      - run: pytest -q\n      - run: python -m pytest -q\n")
    assert dc.lanes()["bare"].package_dir is None


def test_a_test_step_the_engine_cannot_read_is_refused_by_name(dc: Repo) -> None:
    for old, new, needle in (
        ("            --cov-report=html:reports/htmlcov\n", "            --cov-report=html:reports/htmlcov | tee unit.log\n", "needs a shell"),
        ("          python -m coverage report --fail-under=${COVERAGE_FAIL_UNDER}\n", "          python -m coverage report --fail-under=${COVERAGE_FAIL_UNDER}\n          python util/check.py\n", "shares a step with a test command"),
        ('          exit "$rc"\n  generator-parity:', '          echo "$rc"\n  generator-parity:', "captures an exit code"),
        ('          FAKE_REQUIRE_LIVE: "1"\n', "          FAKE_REQUIRE_LIVE: ${{ secrets.LIVE }}\n", "only CI can evaluate"),
        ("--cov=fake_client \\\n", "--cov=${{ matrix.package }} \\\n", "only CI can evaluate"),
        ("--fail-under=${COVERAGE_FAIL_UNDER}", "--fail-under=${NOT_SET_ANYWHERE}", "shell expansion"),
        ('pip install "fake-server[api]"', "pip install ./no-such-dir", "has no pyproject.toml"),
    ):
        (dc.workflows / "ci.yml").write_text(DC_CI_YML)
        dc.edit(".github/workflows/ci.yml", old, new)
        ran = dc.run("--list")
        assert ran.code == 2, (needle, ran)
        assert needle in ran.err and "ci.yml > " in ran.err, (needle, ran.err)


def test_a_unittest_step_with_another_command_is_refused_by_name(dc: Repo, ml: Repo) -> None:
    dc.edit(".github/workflows/tooling.yml", "python3 -m unittest -v tests/test_gamma.py", "python3 util/check.py verify")
    ran = dc.run("--list")
    assert ran.code == 2 and "python3 util/check.py verify" in ran.err and "shares a step with a unittest command" in ran.err
    for new, needle in (("cd tests && python3 -m unittest t.py", "needs a shell"), ("python3 -m unittest -v", "names no test suite")):
        (dc.workflows / "tooling.yml").write_text(TOOLING_YML.replace("python3 -m unittest -v tests/test_gamma.py", new))
        assert needle in dc.run("--list").err
    for new, needle in (("cd util && python3 check.py verify", "needs a shell"), ("python3 -m unittest -v", "names no test suite")):
        (ml.workflows / "ci.yml").write_text(ML_CI_YML.replace("python3 util/check.py verify", new))
        ran = ml.run("--list")
        assert ran.code == 2 and needle in ran.err, ran.err


# ---------------------------------------------------------------------------------------------------------------
# Selection
# ---------------------------------------------------------------------------------------------------------------


def test_ml_groups_lanes_and_aliases(ml: Repo) -> None:
    everything = ["tests/test_alpha.py", "tests/test_beta.py", "tests/test_gamma.py", "util/check.py verify", "scripts/test_shell.bash", "demo", "other"]
    assert list(ml.pick("all")) == everything
    assert list(ml.pick("regression")) == everything[:5]
    assert list(ml.pick("unittest")) == everything[:4]
    assert list(ml.pick("bash")) == ["scripts/test_shell.bash"]
    assert list(ml.pick("packages")) == ["demo", "other"]
    assert list(ml.pick("juniper-demo")) == ["demo"] and list(ml.pick("juniper-demo/")) == ["demo"]
    assert ml.pick("juniper-other") == {"other": []}, "a package directory names its lane, as juniper-<pkg> does"
    target = ml.root / "juniper-other" / "tests" / "test_other.py"
    assert ml.pick("juniper-other/tests/test_other.py") == {"other": [str(target)]} and ml.pick("other") == {"other": []}
    assert ml.pick("optional") == {}


def test_dc_groups_lanes_and_aliases(dc: Repo) -> None:
    suites = ["tests/test_alpha.py", "tests/test_beta.py", "tests/test_gamma.py"]
    assert list(dc.pick("all")) == [*suites, "unit-tests", "integration-tests"]
    assert list(dc.pick("optional")) == ["generator-parity", "security", "slow-or-integration-tests"]
    for token, lane in (("unit", "unit-tests"), ("integration", "integration-tests"), ("slow-or-integration", "slow-or-integration-tests"), ("tests", "unit-tests"), ("tests/", "unit-tests"), ("security", "security")):
        assert dc.pick(token) == {lane: []}, token


def test_rec_groups_lanes_and_aliases(rec: Repo) -> None:
    assert list(rec.pick("all")) == ["tests/test_alpha.py", "bench", "demo"]
    assert list(rec.pick("packages")) == ["bench", "demo"]
    assert list(rec.pick("optional")) == ["demo-torch"]
    assert rec.pick("juniper-recurrence-demo") == {"demo": []} and rec.pick("bench/") == {"bench": []}


def test_every_spelling_of_a_suite(ml: Repo) -> None:
    for token in ("tests/test_alpha.py", "test_alpha.py", "test_alpha", "alpha", "tests.test_alpha"):
        assert ml.pick(token) == {"tests/test_alpha.py": []}, token
    assert ml.pick("test_alpha.py", cwd=ml.root / "tests") == {"tests/test_alpha.py": []}
    assert list(ml.pick("*a")) == ["tests/test_alpha.py", "tests/test_beta.py", "tests/test_gamma.py"]
    assert list(ml.pick("test_g*")) == ["tests/test_gamma.py"]


def test_a_class_or_test_narrows_a_suite_and_the_whole_suite_wins(ml: Repo) -> None:
    assert ml.pick("tests/test_alpha.py::AlphaTest::test_two") == {"tests/test_alpha.py": ["tests.test_alpha.AlphaTest.test_two"]}
    assert ml.pick("tests.test_alpha.AlphaTest") == {"tests/test_alpha.py": ["tests.test_alpha.AlphaTest"]}
    assert ml.pick("tests/test_alpha.py::AlphaTest", "tests.test_alpha.AlphaTest.test_two") == {"tests/test_alpha.py": ["tests.test_alpha.AlphaTest", "tests.test_alpha.AlphaTest.test_two"]}
    assert ml.pick("tests/test_alpha.py::AlphaTest", "alpha") == {"tests/test_alpha.py": []}
    assert ml.pick("alpha", "tests/test_alpha.py::AlphaTest") == {"tests/test_alpha.py": []}


def test_commands_and_package_paths(ml: Repo) -> None:
    assert list(ml.pick("scripts/test_shell.bash")) == ["scripts/test_shell.bash"]
    assert list(ml.pick("test_shell.bash", cwd=ml.root / "scripts")) == ["scripts/test_shell.bash"]
    assert list(ml.pick("util/check.py")) == ["util/check.py verify"]
    target = str(ml.root / "juniper-demo" / "tests" / "test_demo.py")
    assert ml.pick("juniper-demo/tests/test_demo.py::test_demo") == {"demo": [target + "::test_demo"]}
    assert ml.pick("juniper-demo/tests/test_demo.py") == {"demo": [target]}
    assert ml.pick("test_demo") == {"demo": [target]}, "a test file under a gating lane's directory, by its stem"
    assert ml.pick("*demo*") == {"demo": [target]}


def test_a_test_file_two_places_share_is_refused_until_named_by_path(ml: Repo) -> None:
    with pytest.raises(rt.UsageError, match="2 test files are named test_cli.py"):
        ml.pick("cli")
    assert ml.pick("juniper-demo/tests/nested/test_cli.py") == {"demo": [str(ml.root / "juniper-demo" / "tests" / "nested" / "test_cli.py")]}
    with pytest.raises(rt.UsageError, match="matches no test file"):
        ml.pick("*built*")


def test_every_spelling_of_a_test_file_narrows_the_unit_lane(dc: Repo) -> None:
    target = str(dc.root / "tests" / "test_demo.py")
    for token in ("tests/test_demo.py", "test_demo", "demo", "tests.test_demo"):
        assert dc.pick(token) == {"unit-tests": [target]}, token
    assert dc.pick("test_demo.py", cwd=dc.root / "tests") == {"unit-tests": [target]}
    assert dc.pick("*wid*") == {"unit-tests": [str(dc.root / "tests" / "test_widget.py")]}
    assert dc.pick("tests.test_demo.TestX.test_y") == {"unit-tests": [target + "::TestX::test_y"]}
    assert dc.pick("tests/test_demo.py::test_demo", "unit") == {"unit-tests": []}
    assert dc.pick("tests") == {"unit-tests": []}


def test_unknown_selectors_are_usage_errors_with_suggestions(ml: Repo, dc: Repo) -> None:
    with pytest.raises(rt.UsageError, match="did you mean alpha"):
        ml.pick("alpah")
    with pytest.raises(rt.UsageError, match="demo"):
        dc.pick("demoo")
    for token, needle in (("no_such_*", "matches no test file"), ("tests/test_nope.py", "no such file"), ("docs/nothing.md", "no such file"), ("tests.test_nope", "not a suite any workflow runs")):
        with pytest.raises(rt.UsageError, match=needle):
            ml.pick(token)
    ml.write("docs/x.md", "x\n")
    with pytest.raises(rt.UsageError, match="a path under a gating lane's directory"):
        ml.pick("docs/x.md")
    with pytest.raises(rt.UsageError, match="outside the checkout"):
        ml.pick(str(ml.root.parent / "state"))
    with pytest.raises(rt.UsageError, match="not a suite a lane runs"):
        ml.pick("util/check.py::nope")


def test_an_unwired_suite_is_refused_by_name_with_the_specs_hint(ml: Repo) -> None:
    ml.write("tests/test_unwired.py", "import unittest\n")
    with pytest.raises(rt.UsageError, match=r"tests/test_unwired.py is not a suite any lane runs \(the wiring check fails until ci.yml runs it\)"):
        ml.pick("tests/test_unwired.py")


def test_an_empty_lane_is_named(dc: Repo) -> None:
    (dc.workflows / "tooling.yml").unlink()
    assert list(dc.pick("all")) == ["unit-tests", "integration-tests"]
    with pytest.raises(rt.UsageError, match="the unittest lane is empty"):
        dc.pick("unittest")
    with pytest.raises(rt.UsageError, match="tests/test_gone.py is not a suite any workflow runs, or a test file"):
        dc.pick("tests.test_gone")


# ---------------------------------------------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------------------------------------------


def test_ml_everything_passes_and_the_record_is_complete(ml: Repo) -> None:
    ran = ml.run("all", "-j", "3", FAKE_BETA="pass")
    assert ran.code == 0, ran
    jobs = ml.jobs()
    assert {job["status"] for job in jobs.values()} == {"PASS"}, ran.out
    assert jobs["tests/test_alpha.py"]["counts"]["ran"] == 3 and jobs["tests/test_alpha.py"]["detail"] == "3 tests, 1 skipped"
    assert jobs["demo"]["detail"] == "1 passed; coverage gates passed"
    assert jobs["util/check.py verify"]["detail"] == "exit 0"
    summary = ml.summary()
    assert summary["schema"] == 1 and summary["exit_code"] == 0 and summary["engine"] == {"module": "juniper_ci_tools.run_tests", "version": rt.ENGINE_VERSION}
    assert summary["options"]["force_drift"] is False and summary["argv"][-3:] == ["all", "-j", "3"]
    run_dir = ml.run_dir()
    assert os.readlink(ml.logs / "latest") == run_dir.name
    assert (run_dir / "summary.txt").is_file() and (run_dir / "unittest" / "test_alpha.log").is_file() and (run_dir / "demo" / "1-python.log").is_file()
    assert "PASSED" in ran.out and "3 tests, 1 skipped" in ran.out and "(5 tests, 1 skipped)" in ran.out
    ml.assert_checkout_clean()


def test_the_package_lane_tests_this_checkout_and_writes_coverage_to_the_run_directory(ml: Repo) -> None:
    ran = ml.run("demo")
    assert ran.code == 0, ran
    run_dir = ml.run_dir()
    record = ml.read_state("pytest.json")
    assert f"--cov-report=json:{run_dir / 'demo' / 'coverage.json'}" in record["argv"] and "--cov-fail-under=85" in record["argv"]
    assert record["COVERAGE_FILE"] == str(run_dir / "demo" / ".coverage")
    assert record["PYTHONPATH"] == str(ml.root / "juniper-demo")
    assert record["module"] == str(ml.root / "juniper-demo" / "juniper_demo" / "__init__.py")
    gate = ml.read_state("gate.json")
    assert gate["report_exists"] and gate["argv"][gate["argv"].index("--coverage-json") + 1] == str(run_dir / "demo" / "coverage.json")
    assert "1 passed" in ran.out, "stream mode did not show the step's output"
    ml.assert_checkout_clean()


def test_a_kept_step_that_fails_stops_its_lane(ml: Repo) -> None:
    ran = ml.run("demo", FAKE_CHECK_ENV_RC="1")
    assert ran.code == 1, ran
    job = ml.jobs()["demo"]
    assert [step["status"] for step in job["steps"]] == ["FAIL", "NOT-RUN", "NOT-RUN"]
    assert "exit 1: no pytest summary line" in job["detail"]


def test_dc_the_unit_lane_routes_every_report_and_both_gates_read_them(dc: Repo) -> None:
    ran = dc.run("unit")
    assert ran.code == 0, ran
    lane_dir = dc.run_dir() / "unit-tests"
    record = dc.read_state("pytest.json")
    for arg in (f"--junitxml={lane_dir / 'junit-unit.xml'}", f"--cov-report=xml:{lane_dir / 'coverage.xml'}", f"--cov-report=json:{lane_dir / 'coverage.json'}", f"--cov-report=html:{lane_dir / 'htmlcov'}", "--cov-report=term-missing:skip-covered", "--cov=fake_client"):
        assert arg in record["argv"], arg
    assert record["COVERAGE_FILE"] == str(lane_dir / ".coverage") and record["PYTHONPATH"] == str(dc.root)
    assert record["env"] == {"COVERAGE_FAIL_UNDER": "77", "PYTHON_TEST_VERSION": "3.99", "JOB_LEVEL": "from-3.99", "FAKE_CI_ONLY": None, "FAKE_REQUIRE_LIVE": None, "FAKE_PARITY_REQUIRED": None}
    floor = dc.read_state("coverage-report.json")
    assert floor["argv"] == ["report", "--fail-under=77"] and floor["COVERAGE_FILE"] == str(lane_dir / ".coverage") and floor["data_exists"]
    gate = dc.read_state("gate.json")
    assert gate["report_exists"] and gate["argv"][gate["argv"].index("--coverage-json") + 1] == str(lane_dir / "coverage.json")
    dc.assert_checkout_clean()


def test_dc_floor_gate_and_pytest_failures_are_named(dc: Repo) -> None:
    ran = dc.run("unit", FAKE_COVERAGE_RC="2")
    assert ran.code == 1
    job = dc.jobs()["unit-tests"]
    assert "coverage 76.50% is under the 77.00% floor" in job["detail"] and [step["status"] for step in job["steps"]] == ["PASS", "FAIL", "NOT-RUN"]
    assert not (dc.state / "gate.json").exists()
    dc.run("unit", FAKE_COVERAGE_RC="2", FAKE_COVERAGE_SILENT="1")
    assert "the coverage floor failed (exit 2; see the log)" in dc.jobs()["unit-tests"]["detail"]
    dc.run("unit", FAKE_GATE_RC="1")
    assert "the per-file coverage gate failed" in dc.jobs()["unit-tests"]["detail"]
    assert dc.run("unit", FAKE_PYTEST_RC="1").code == 1
    job = dc.jobs()["unit-tests"]
    assert job["failed_tests"] == ["tests/test_demo.py::test_demo"] and [step["status"] for step in job["steps"]] == ["FAIL", "NOT-RUN", "NOT-RUN"]
    dc.run("unit", FAKE_PYTEST_RC="2", FAKE_PYTEST_SILENT="1")
    assert "exit 2: no pytest summary line (see the log)" in dc.jobs()["unit-tests"]["detail"]
    ran = dc.run("unit", "-q", FAKE_PYTEST_MANY="1")
    assert "... and 2 more" in ran.out and "│" in ran.out, "the failing step's tail was not printed"


def test_dc_the_integration_lane_passes_on_its_accepted_codes_as_ci_does(dc: Repo) -> None:
    ran = dc.run("integration")
    assert ran.code == 0, ran
    assert "no tests collected" in dc.jobs()["integration-tests"]["detail"]
    assert dc.read_state("pytest.json")["argv"] == ["-m", "integration", "tests/", "--junit-xml", str(dc.run_dir() / "integration-tests" / "junit-integration.xml")]
    dc.run("integration", FAKE_PYTEST_RC="3")
    assert "exit 3, which the workflow accepts" in dc.jobs()["integration-tests"]["detail"]
    assert dc.run("integration", FAKE_PYTEST_RC="1").code == 1
    ran = dc.run("slow-or-integration-tests")
    assert ran.code == 0 and "no tests collected" in dc.jobs()["slow-or-integration-tests"]["detail"]
    dc.assert_checkout_clean()


def test_dc_an_opt_in_lane_runs_its_test_step_alone_with_its_variable(dc: Repo) -> None:
    ran = dc.run("generator-parity")
    assert ran.code == 0, ran
    record = dc.read_state("pytest.json")
    assert record["argv"] == ["tests/test_demo.py", "--verbose", "-rs"] and record["env"]["FAKE_REQUIRE_LIVE"] == "1"
    assert "missing: fake-server[api]" in ran.out and "install: " in ran.out
    assert [step["label"] for step in dc.jobs()["generator-parity"]["steps"]] == ["pytest"], "the import probe ran"
    ran = dc.run("security")
    assert ran.code == 0 and dc.read_state("pytest.json")["env"]["FAKE_PARITY_REQUIRED"] == "1"
    assert [step["label"] for step in dc.jobs()["security"]["steps"]] == ["pytest"], "a scan ran"


def test_list_names_lanes_optional_flags_and_left_out_steps(dc: Repo, ml: Repo) -> None:
    listed = dc.run("--list")
    assert "generator-parity" not in listed.out.split("groups:", 1)[0]
    listed = dc.run("--list", "optional")
    assert "optional: runs only when named (needs fake-server[api]" in listed.out
    assert "optional: runs only when named (scheduled-tests.yml: CI runs it on schedule, workflow_dispatch, never on a pull request)" in listed.out
    assert "left out, running no test: Run Bandit (SAST); Run pip-audit (Dependency Vulnerabilities)" in listed.out
    assert "$ FAKE_PARITY_REQUIRED=1 python -m pytest tests/test_demo.py -v -v" in listed.out
    assert "groups: all = unittest unit-tests integration-tests; optional = generator-parity security slow-or-integration-tests" in listed.out
    assert "exit 5, 3 passes" in dc.run("--list", "integration").out
    assert "(.github/workflows/tooling.yml > tooling > Run the tooling suites)" in dc.run("--list", "unittest").out
    listed = ml.run("--list")
    assert "groups: all = unittest bash demo other; regression = unittest bash; packages = demo other; optional = none" in listed.out
    assert "  $ python -c " in listed.out, "the kept step is not listed"


def test_a_narrowed_run_turns_the_coverage_gates_off(dc: Repo, ml: Repo) -> None:
    ran = dc.run("demo")
    assert ran.code == 0, ran
    argv = dc.read_state("pytest.json")["argv"]
    assert not [arg for arg in argv if arg.startswith("--cov")] and "tests/" not in argv and argv[-1] == str(dc.root / "tests" / "test_demo.py")
    assert f"--junitxml={dc.run_dir() / 'unit-tests' / 'junit-unit.xml'}" in argv
    assert not (dc.state / "coverage-report.json").exists() and not (dc.state / "gate.json").exists()
    assert "coverage gates off" in dc.jobs()["unit-tests"]["detail"]
    assert dc.run("unit", "--no-coverage").code == 0
    assert not [arg for arg in dc.read_state("pytest.json")["argv"] if arg.startswith("--cov")]
    ran = ml.run("juniper-demo/tests/test_demo.py")
    assert ran.code == 0 and ml.read_state("pytest.json")["argv"][-1] == str(ml.root / "juniper-demo" / "tests" / "test_demo.py")
    dc.assert_checkout_clean()


def test_a_failure_is_reported_and_every_other_job_still_runs(ml: Repo) -> None:
    ran = ml.run("regression", "-j", "1")
    assert ran.code == 1, ran
    jobs = ml.jobs()
    assert jobs["tests/test_beta.py"]["status"] == "FAIL" and jobs["tests/test_beta.py"]["failed_tests"] == ["tests.test_beta.BetaTest.test_fails"]
    assert jobs["tests/test_gamma.py"]["status"] == "PASS" and jobs["scripts/test_shell.bash"]["status"] == "PASS"
    assert "beta was told to fail" in ran.out and "--failed" in ran.out
    ran = ml.run("util/check.py", FAKE_CHECK_RC="4")
    assert ran.code == 1 and ml.jobs()["util/check.py verify"]["detail"] == "exit 4"


def test_a_suite_that_dies_before_it_runs_is_named(ml: Repo) -> None:
    ran = ml.run("alpha", FAKE_ALPHA_CRASH="1")
    assert ran.code == 1
    assert "exit 3: no unittest result line, so it died before or while loading" in ml.jobs()["tests/test_alpha.py"]["detail"]


def test_fail_fast_starts_nothing_after_the_first_failure(ml: Repo) -> None:
    assert ml.run("regression", "-j", "1", "-x").code == 1
    jobs = ml.jobs()
    assert jobs["tests/test_beta.py"]["status"] == "FAIL" and jobs["tests/test_gamma.py"]["status"] == "NOT-RUN"
    assert "not started: an earlier job failed (-x)" in jobs["tests/test_gamma.py"]["detail"]


def test_a_job_that_passes_alone_after_failing_in_parallel_is_a_rerun_pass(ml: Repo) -> None:
    ran = ml.run("unittest", "-j", "2", FAKE_BETA="flaky")
    assert ran.code == 0, ran
    beta = ml.jobs()["tests/test_beta.py"]
    assert beta["status"] == "RERUN-PASS" and beta["first_pass"]["status"] == "FAIL" and beta["steps"][0]["log"].endswith("test_beta.rerun.log")
    assert "Passed only when re-run alone" in ran.out and "PASSED (1 only on a re-run alone)" in ran.out
    (ml.state / "beta-ran-once").unlink()
    assert ml.run("unittest", "-j", "2", "--no-rerun", FAKE_BETA="flaky").code == 1, "--no-rerun still re-ran the failure"


def test_keywords_filter_tests_and_a_filter_that_matches_nothing_exits_5(ml: Repo, dc: Repo) -> None:
    ran = ml.run("regression", "-k", "cap", FAKE_BETA="pass")
    assert ran.code == 0, ran
    jobs = ml.jobs()
    assert jobs["tests/test_alpha.py"]["counts"]["ran"] == 1 and jobs["tests/test_beta.py"]["status"] == "NO-TESTS"
    assert "util/check.py verify" not in jobs and "skipping 2 command job(s)" in ran.out
    assert ml.run("unittest", "-k", "no_such_test").code == 5
    ran = dc.run("unit", "-k", "nothing", "-k", "else", FAKE_PYTEST_RC="5")
    assert ran.code == 5, "a -k that matches nothing in a pytest lane is not NO-TESTS"
    assert "(nothing) or (else)" in dc.read_state("pytest.json")["argv"]


def test_a_unittest_job_that_ran_nothing_under_a_filter_is_no_tests_on_every_python(scratch: Path) -> None:
    """Python 3.11's unittest exits 0 with "Ran 0 tests" when -k matches nothing; 3.12 and later exit 5. Both are NO-TESTS."""
    log = scratch / "zero.log"
    printed = "import sys; print('Ran 0 tests in 0.000s'); print(); print('OK'); sys.exit(0)"
    job = rt.Job("unittest", "tests/test_zero.py", "unittest", [rt.Step("unittest", [sys.executable], scratch)], 0)
    planned = [rt.Planned("unittest", [sys.executable, "-c", printed], scratch, rt._Env(os.environ), {}, log)]
    filtered = rt.Engine(timeout=60, fail_fast=False, filtered=True).run_job(job, planned, stream=False)
    assert (filtered.status, filtered.detail) == (rt.NO_TESTS, "no test matched")
    unfiltered = rt.Engine(timeout=60, fail_fast=False, filtered=False).run_job(job, planned, stream=False)
    assert unfiltered.status == rt.PASSED, "a suite with no tests at all, run unfiltered, is CI's pass"


def test_failed_reruns_the_failures_of_the_last_run(ml: Repo, dc: Repo) -> None:
    ran = ml.run("--failed")
    assert ran.code == 2 and "no recorded run" in ran.err
    assert ml.run("regression", "-j", "1").code == 1
    listed = ml.run("--failed", "--list")
    stamp = sorted(path.name for path in ml.logs.iterdir() if path.name != "latest")[-1]
    assert [line.strip() for line in listed.out.splitlines() if line.startswith("  tests/")] == [f"tests/test_beta.py  (failed in {stamp})"]
    ran = ml.run("--failed", FAKE_BETA="pass")
    assert ran.code == 0 and list(ml.jobs()) == ["tests/test_beta.py"]
    assert dc.run("demo", FAKE_PYTEST_RC="1").code == 1
    assert "only: " + str(dc.root / "tests" / "test_demo.py") in dc.run("--failed", "--list").out, "--failed lost a narrowed lane's target"
    ml.run("regression", "-j", "1")
    ml.edit(".github/workflows/ci.yml", "python3 -m unittest -v tests/test_beta.py\n", "")
    listed = ml.run("--failed", "--list")
    assert "--failed: skipped 'tests/test_beta.py'" in listed.out


def test_a_timeout_kills_the_whole_process_group(ml: Repo) -> None:
    # 4 s, not less: on a loaded CI runner the suite must still reach its sleep (and write the pid) first.
    ran = ml.run("gamma", "--timeout", "4", FAKE_GAMMA_SLEEP="60", FAKE_GAMMA_CHILD="1")
    assert ran.code == 1, ran
    assert ml.jobs()["tests/test_gamma.py"]["status"] == "TIMEOUT" and "timed out after 4.0s" in ml.jobs()["tests/test_gamma.py"]["detail"]
    assert (ml.state / "gamma-child.pid").is_file(), "the suite timed out before it started its child: the test proved nothing"
    assert _pid_gone(int((ml.state / "gamma-child.pid").read_text())), "the step's grandchild survived the timeout"


def test_processes_a_step_leaves_behind_are_killed(ml: Repo) -> None:
    ran = ml.run("gamma", "-q", FAKE_GAMMA_CHILD="1")
    assert ran.code == 0, ran
    job = ml.jobs()["tests/test_gamma.py"]
    assert job["steps"][0]["leftovers"] and "killed processes it left behind" in job["detail"]
    assert _pid_gone(int((ml.state / "gamma-child.pid").read_text()))


def _when_sleeping(state: Path, sig: int) -> threading.Thread:
    """Send ``sig`` to this process once the gamma suite is asleep (its step is running and the engine waits)."""

    def watch() -> None:
        deadline = time.monotonic() + 30
        while not (state / "gamma-sleeping").exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        time.sleep(0.2)
        os.kill(os.getpid(), sig)

    thread = threading.Thread(target=watch, daemon=True)
    thread.start()
    return thread


def test_sigterm_ends_the_run_like_ctrl_c_and_keeps_the_summary(ml: Repo) -> None:
    previous = signal.signal(signal.SIGTERM, lambda signum, frame: None)  # a late SIGTERM must not end pytest
    try:
        watcher = _when_sleeping(ml.state, signal.SIGTERM)
        ran = ml.run("gamma", "--timeout", "0", FAKE_GAMMA_SLEEP="60", FAKE_GAMMA_CHILD="1")
        watcher.join(timeout=30)
    finally:
        signal.signal(signal.SIGTERM, previous)
    assert ran.code == 130, ran
    summary = ml.summary()
    assert summary["interrupted"] and summary["jobs"][0]["status"] == "NOT-RUN"
    assert _pid_gone(int((ml.state / "gamma-child.pid").read_text()))


def test_ctrl_c_in_a_parallel_run_kills_every_running_step(ml: Repo) -> None:
    watcher = _when_sleeping(ml.state, signal.SIGINT)
    ran = ml.run("unittest", "-j", "2", "--timeout", "0", FAKE_BETA="pass", FAKE_GAMMA_SLEEP="60", FAKE_GAMMA_CHILD="1")
    watcher.join(timeout=30)
    assert ran.code == 130, ran
    assert "INTERRUPTED" in ran.out and ml.jobs()["tests/test_gamma.py"]["status"] == "NOT-RUN" and ml.summary()["interrupted"]
    assert _pid_gone(int((ml.state / "gamma-child.pid").read_text())), "Ctrl-C left the step's grandchild running"


def test_the_heartbeat_names_the_jobs_still_running(ml: Repo, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(rt, "HEARTBEAT", 0.4)
    ran = ml.run("alpha", "beta", "gamma", "-j", "3", FAKE_BETA="pass", FAKE_GAMMA_SLEEP="2")
    assert ran.code == 0, ran
    assert "still running (1): tests/test_gamma.py" in ran.out, ran.out


def test_an_internal_error_in_one_job_keeps_the_summary(ml: Repo, monkeypatch: pytest.MonkeyPatch) -> None:
    real = rt.Engine.run_job

    def run_job(self, job, planned, stream, rerun=False):
        if job.id == "tests/test_beta.py":
            raise RuntimeError("boom")
        return real(self, job, planned, stream, rerun)

    monkeypatch.setattr(rt.Engine, "run_job", run_job)
    ran = ml.run("alpha", "beta", "-j", "2", "--no-rerun")
    assert ran.code == 1
    assert ml.jobs()["tests/test_beta.py"]["detail"] == "run_tests.py internal error: RuntimeError: boom"


def test_the_child_environment(ml: Repo) -> None:
    tmpdir = ml.root.parent / "children-tmp"
    tmpdir.mkdir()
    ran = ml.run("gamma", TMPDIR=str(tmpdir), CLAUDE_FAKE="1", JUNIPER_FAKE="1", WTC_FAKE="1", DISPLAY=":99", PYTHONPATH="/nonexistent", WAYLAND_DISPLAY="w")
    assert ran.code == 0, ran
    record = ml.read_state("gamma-env.json")
    assert record["DBUS_SESSION_BUS_ADDRESS"] == rt.BUS_GUARD
    assert (record["DISPLAY"], record["WAYLAND_DISPLAY"], record["PYTHONPATH"]) == (None, None, None)
    assert record["PYTHONUNBUFFERED"] == "1" and record["TMPDIR"] == str(tmpdir) and record["GIT_CEILING_DIRECTORIES"].split(os.pathsep)[0] == str(tmpdir)
    assert record["stdin"] == "", "a child's stdin is not /dev/null"
    assert (record["CLAUDE_FAKE"], record["JUNIPER_FAKE"], record["FAKE_DRIFT"]) == ("1", "1", None)
    ran = ml.run("gamma", "--clean-env", "--force-drift", TMPDIR=str(tmpdir), CLAUDE_FAKE="1", JUNIPER_FAKE="1", WTC_FAKE="1")
    assert ran.code == 0, ran
    record = ml.read_state("gamma-env.json")
    assert (record["CLAUDE_FAKE"], record["JUNIPER_FAKE"], record["WTC_FAKE"], record["FAKE_DRIFT"]) == (None, None, None, "1")
    assert ml.summary()["options"]["force_drift"] is True and "FAKE_DRIFT=1" in ran.out


def test_a_tmpdir_under_the_system_temp_directory_is_replaced(ml: Repo) -> None:
    system_tmp = "/tmp"  # tmp-path-literal: allow -- the value under test; the engine must refuse it, so nothing is written there
    ran = ml.run("gamma", TMPDIR=os.path.join(system_tmp, "run-tests-never-created"))
    assert ran.code == 0, ran
    assert ml.read_state("gamma-env.json")["TMPDIR"] == str(ml.root / "tmp") and "TMPDIR was under the system temp directory" in ran.out
    for args, needle in ((("gamma", "--tmpdir", os.path.join(system_tmp, "x")), "system temp directory"), (("--log-dir", os.path.join(system_tmp, "logs"), "gamma"), "no Juniper tool may use")):
        refused = ml.run(*args)
        assert refused.code == 2 and needle in refused.err, refused
    other = ml.root.parent / "chosen-tmp"
    assert ml.run("gamma", "--tmpdir", str(other)).code == 0 and ml.read_state("gamma-env.json")["TMPDIR"] == str(other)
    ran = ml.run("gamma", TMPDIR=str(ml.root.parent / "no-such-dir"))
    assert "TMPDIR was not a directory" in ran.out
    with ml.monkeypatch.context() as patch:
        patch.delenv("TMPDIR", raising=False)
        assert "TMPDIR was unset" in ml.run("gamma").out


def test_a_missing_tool_makes_the_lane_unavailable(ml: Repo, monkeypatch: pytest.MonkeyPatch, scratch: Path) -> None:
    ml.edit(".github/workflows/ci-demo.yml", 'pip install "juniper-ci-tools>=0.9.0,<0.10.0"\n          python ../gate.py', 'pip install "juniper-no-such-tools>=1"\n          juniper-no-such-tool')
    ran = ml.run("demo")
    assert ran.code == 3, ran
    job = ml.jobs()["demo"]
    assert job["status"] == "UNAVAILABLE" and "juniper-no-such-tool is not installed" in job["detail"] and "juniper-no-such-tools>=1" in job["detail"]
    assert "INCOMPLETE (1 unavailable)" in ran.out
    assert "UNAVAILABLE: juniper-no-such-tool is not installed" in ml.run("--dry-run", "demo").out
    ml.edit(".github/workflows/ci-demo.yml", "juniper-no-such-tool", "../gate-not-executable")
    ml.write("gate-not-executable", "not a program\n")
    ran = ml.run("demo")
    assert ran.code == 3 and "cannot start ../gate-not-executable" in ml.jobs()["demo"]["detail"]
    empty = scratch / "empty-path"
    empty.mkdir()
    ran = ml.run("bash", PATH=str(empty))
    assert ran.code == 3 and "bash is not on PATH" in ran.out
    ran = ml.run("bash", "alpha", "-j", "2", PATH=str(empty))
    assert ran.code == 3 and ml.jobs()["scripts/test_shell.bash"]["status"] == "UNAVAILABLE" and ml.jobs()["tests/test_alpha.py"]["status"] == "PASS"


def test_the_preflight_refuses_a_lane_that_would_test_other_code(ml: Repo, scratch: Path) -> None:
    fake = scratch / "bin" / "python3"
    fake.parent.mkdir()
    fake.write_text(f"#!{sys.executable}\nimport json, os, sys\ncode = sys.argv[2] if len(sys.argv) > 2 else ''\nif 'sys.version_info[:3]' in code:\n    print('3.99.1')\nelif os.environ.get('FAKE_PROBE_REPORT') == 'garbage':\n    print('not json'); sys.stderr.write('the probe broke\\n')\nelse:\n    print(os.environ['FAKE_PROBE_REPORT'])\n")
    fake.chmod(0o755)
    elsewhere = {"requirements": [{"requirement": "x>=2", "status": "unsatisfied", "have": "1.0"}, {"requirement": "y", "status": "missing", "have": None}, {"requirement": "z; python_version<'3'", "status": "not-applicable", "have": None}], "packages": {"juniper_demo": {"origin": "/site-packages/juniper_demo/__init__.py", "error": None}}, "packaging": False}
    ran = ml.run("--dry-run", "--python", str(fake), "demo", FAKE_PROBE_REPORT=json.dumps(elsewhere))
    assert ran.code == 0, ran
    assert "REFUSED  demo: juniper_demo imports from /site-packages" in ran.out and "(see docs/REFERENCE.md, 'Running tests locally')" in ran.out
    assert "REFUSED by the preflight" in ran.out and "python    3.99.1" in ran.out
    here = {"requirements": elsewhere["requirements"], "packages": {"juniper_demo": {"origin": str(ml.root / "juniper-demo" / "juniper_demo" / "__init__.py"), "error": None}}, "packaging": False}
    ran = ml.run("--dry-run", "--python", str(fake), "demo", FAKE_PROBE_REPORT=json.dumps(here))
    assert "WARN" in ran.out and "unsatisfied: x>=2 (have 1.0)" in ran.out and "missing: y" in ran.out and "install: " in ran.out
    assert "versions not compared: packaging is not installed" in ran.out and "0 of 2 requirements satisfied" in ran.out
    ran = ml.run("--dry-run", "--python", str(fake), "demo", FAKE_PROBE_REPORT="garbage")
    assert "preflight could not run (the probe broke); nothing was checked" in ran.out
    broken = {"requirements": [], "packages": {"juniper_demo": {"origin": None, "error": "ImportError: boom"}}, "packaging": True}
    assert "REFUSED  demo: ImportError: boom" in ml.run("--dry-run", "--python", str(fake), "demo", FAKE_PROBE_REPORT=json.dumps(broken)).out
    ran = ml.run("demo", "--python", str(fake), FAKE_PROBE_REPORT=json.dumps(elsewhere))
    assert ran.code == 3 and ml.jobs()["demo"]["status"] == "UNAVAILABLE"


def test_the_interpreter_is_checked_before_anything_runs(ml: Repo, scratch: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    junk = scratch / "junk-python"
    junk.write_text("#!/bin/sh\necho junk\n")
    junk.chmod(0o755)
    for python, needle in ((str(scratch / "missing"), "not an executable file"), (str(junk), "does not run as a Python interpreter")):
        ran = ml.run("gamma", "--python", python)
        assert ran.code == 2 and needle in ran.err, ran
    assert rt.resolve_python(Path(sys.executable).name)[0].endswith(Path(sys.executable).name)

    def refuse(*args, **kwargs):
        raise OSError("refused")

    monkeypatch.setattr(rt.subprocess, "run", refuse)
    with pytest.raises(rt.UsageError, match="cannot run it"):
        rt.resolve_python(sys.executable)


def test_an_activation_directory_goes_first_on_path(ml: Repo, scratch: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    venv = scratch / "venv" / "bin"
    venv.mkdir(parents=True)
    (venv / "python3").symlink_to(sys.executable)
    (venv / "python").symlink_to(sys.executable)
    assert rt.activation_dir(str(venv / "python")) == venv
    assert rt.activation_dir(str(scratch / "nowhere" / "python")) is None
    ran = ml.run("--dry-run", "--python", str(venv / "python"), "gamma", PATH="/usr/bin:/bin")
    assert f"PATH={venv}{os.pathsep}..." in ran.out

    def broken(*args):
        raise OSError("gone")

    monkeypatch.setattr(rt.os.path, "samefile", broken)
    assert rt.activation_dir(str(venv / "python")) is None


def test_usage_errors_exit_2(ml: Repo, monkeypatch: pytest.MonkeyPatch) -> None:
    for args, needle in ((("alpah",), "did you mean alpha"), (("alpha", "demo", "--", "-x"), "one runner")):
        ran = ml.run(*args)
        assert ran.code == 2 and needle in ran.err, ran
    with pytest.raises(SystemExit):
        ml.run("--stream", "--quiet")
    for bad in (("-j", "0"), ("-j", "many"), ("--timeout", "-1"), ("--timeout", "soon")):
        with pytest.raises(SystemExit):
            ml.run(*bad)
    assert rt._jobs_value("auto") >= 1 and rt._jobs_value("3") == 3
    monkeypatch.setattr(rt.os, "name", "nt")
    ran = ml.run("gamma")
    assert ran.code == 2 and "POSIX only" in ran.err


def test_not_a_checkout_of_the_repo_is_a_usage_error(dc: Repo, rec: Repo) -> None:
    dc.edit("pyproject.toml", 'name = "fake-data-client"', 'name = "another-project"')
    ran = dc.run("--list")
    assert ran.code == 2 and "is not a fake-data-client checkout: it needs .github/workflows/ci.yml and a pyproject.toml whose project is fake-data-client" in ran.err
    (dc.root / "pyproject.toml").write_text("[broken\n")
    assert dc.run("--list").code == 2
    for path in rec.workflows.glob("ci-recurrence-*.yml"):
        path.unlink()
    ran = rec.run("--list")
    assert ran.code == 2 and "it needs .github/workflows/ci-recurrence-*.yml (--checkout)" in ran.err


def test_dry_run_prints_the_commands_and_writes_nothing(dc: Repo) -> None:
    ran = dc.run("--dry-run", "all", "optional", "-j", "2")
    assert ran.code == 0, ran
    for needle in ("-m unittest -v tests/test_alpha.py", "PYTHONPATH=", "FAKE_PARITY_REQUIRED=1", "--fail-under=77", "(dry run: nothing is written)", "failures re-run alone"):
        assert needle in ran.out, needle
    assert not dc.logs.exists() and not (dc.state / "gamma-env.json").exists() and not (dc.state / "pytest.json").exists()
    ran = dc.run("--dry-run", "--no-coverage", "unit", "-x")
    assert "coverage-floor: skipped: coverage is off for --no-coverage" in ran.out and "stop at the first failure" in ran.out


def test_nothing_selected_runs_nothing(ml: Repo) -> None:
    needs_git()
    ml.git("init", "-q", "-b", "main")
    ml.commit("base")
    ran = ml.run("--changed", "--base", "main")
    assert ran.code == 0 and "Nothing selected." in ran.out


def test_the_log_root_and_the_latest_link(ml: Repo, monkeypatch: pytest.MonkeyPatch) -> None:
    ran = ml.run("gamma", log_dir=False)
    assert ran.code == 0, ran
    assert (ml.root / "tmp" / "run-tests" / "checkout" / "latest").is_symlink(), "the default log root is the primary checkout's tmp/run-tests/<checkout name>"

    def no_links(*args):
        raise OSError("no symlinks here")

    monkeypatch.setattr(rt.os, "symlink", no_links)
    assert rt.point_latest(ml.logs, ml.logs / "x") is False


def test_run_directories_never_collide(scratch: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    first, second = rt.make_run_dir(scratch / "logs"), rt.make_run_dir(scratch / "logs")
    assert first != second and rt.STAMP_RE.fullmatch(first.name) and rt.STAMP_RE.fullmatch(second.name)

    class Frozen(rt.dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 1, 1, tzinfo=tz)

    monkeypatch.setattr(rt.dt, "datetime", Frozen)
    full = scratch / "full"
    full.mkdir()
    (full / "20260101T000000Z").mkdir()
    for number in range(2, 1000):
        (full / f"20260101T000000Z-{number}").mkdir()
    with pytest.raises(rt.UsageError, match="cannot create a run directory"):
        rt.make_run_dir(full)
    assert rt.run_dirs(scratch / "missing") == []
    (first / "summary.json").write_text("{not json")
    assert rt.last_summary(scratch / "logs") is None


def test_a_checkout_that_is_a_linked_worktree_logs_under_its_primary(ml: Repo) -> None:
    needs_git()
    ml.git("init", "-q", "-b", "main")
    ml.commit("base")
    linked = ml.root.parent / "linked"
    ml.git("worktree", "add", "-q", "--detach", str(linked))
    spec = ml_spec(linked)
    with ml.monkeypatch.context() as patch:
        patch.setenv("GIT_CEILING_DIRECTORIES", str(ml.root.parent))
        ml.capsys.readouterr()
        code = rt.main(spec, ["--checkout", str(linked), "--dry-run", "--color", "never", "gamma"])
        out = ml.capsys.readouterr().out
    assert code == 0 and f"logs      {ml.root / 'tmp' / 'run-tests' / 'linked'}" in out and "(HEAD @ " in out
    assert rt.primary_checkout(ml.root.parent / "state") == ml.root.parent / "state"


def test_git_that_cannot_run_is_no_checkout(monkeypatch: pytest.MonkeyPatch, scratch: Path) -> None:
    def refuse(*args, **kwargs):
        raise OSError("no git")

    monkeypatch.setattr(rt.subprocess, "run", refuse)
    assert rt._git(scratch, "status") is None and rt.git_state(scratch) == {}


def test_signals_and_groups(monkeypatch: pytest.MonkeyPatch) -> None:
    assert rt._signal_group(2**22 + 12345, 0) is False and rt._group_alive(2**22 + 12345) is False

    def not_ours(pgid: int, sig: int) -> None:
        raise PermissionError("a group this user may not signal")

    monkeypatch.setattr(rt.os, "killpg", not_ours)
    assert rt._signal_group(12345, 0) is False and rt._group_alive(12345) is True, "a group that is not ours: alive, and not signalled"
    monkeypatch.undo()
    with pytest.raises(KeyboardInterrupt):
        rt._raise_interrupt(signal.SIGTERM, None)


def test_output_paints_and_tails(scratch: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    out = rt.Output(color=True, quiet=False)
    assert out.paint("x", rt.PASSED) == "\033[32mx\033[0m" and out.paint("x", "no-style") == "x"
    assert rt._color("always") and not rt._color("never")
    monkeypatch.setenv("NO_COLOR", "1")
    assert not rt._color("auto")
    log = scratch / "step.log"
    log.write_text("# run_tests: header\nline one\nline two\n\n\n")
    assert rt.tail_lines(str(log), 1) == ["line two"] and rt.tail_lines(None, 5) == [] and rt.tail_lines(str(log), 0) == [] and rt.tail_lines(str(scratch / "missing"), 3) == []
    assert rt.split_passthrough(["a", "--", "-x"]) == (["a"], ["-x"]) and rt.split_passthrough(["a"]) == (["a"], [])


def test_exit_codes_and_verdicts() -> None:
    job = rt.Job("lane", "id", "pytest", [], 0)

    def results(*statuses: str) -> list[rt.Result]:
        return [rt.Result(job, status, "", 0.0, []) for status in statuses]

    assert rt.exit_code(results(rt.PASSED), True) == (130, "INTERRUPTED")
    assert rt.exit_code(results(rt.FAIL, rt.PASSED), False) == (1, "FAILED (1 of 2)")
    assert rt.exit_code(results(rt.UNAVAILABLE), False) == (3, "INCOMPLETE (1 unavailable)")
    assert rt.exit_code(results(rt.NO_TESTS, rt.NO_TESTS), False) == (5, "NO TESTS RAN (-k matched nothing)")
    assert rt.exit_code(results(rt.RERUN_PASSED), False) == (0, "PASSED (1 only on a re-run alone)")
    assert rt.exit_code(results(rt.PASSED), False) == (0, "PASSED")
    narrowed = rt.Result(rt.Job("lane", "id", "pytest", [], 0, targets=["t"], select=["a", "b"]), rt.PASSED, "", 0.0, [{"log": "x", "status": rt.PASSED}, {"log": None, "status": rt.SKIPPED}])
    assert narrowed.name == "a, b" and narrowed.logs() == ["x"]


# ---------------------------------------------------------------------------------------------------------------
# --changed
# ---------------------------------------------------------------------------------------------------------------


def test_changed_needs_a_checkout_and_a_merge_base(ml: Repo) -> None:
    ran = ml.run("--changed", "--list")
    assert ran.code == 2 and "--changed needs a git checkout" in ran.err
    needs_git()
    ml.git("init", "-q", "-b", "main")
    ml.commit("base")
    ran = ml.run("--changed", "--base", "no-such-ref", "--list")
    assert ran.code == 2 and "no merge base" in ran.err


def test_ml_changed_selects_what_names_the_changed_files(ml: Repo) -> None:
    needs_git()
    ml.git("init", "-q", "-b", "main")
    ml.commit("base")
    (ml.root / "util" / "check.py").write_text("print('changed')\n")
    (ml.root / "juniper-demo" / "juniper_demo" / "extra.py").write_text("X = 1\n")
    ran = ml.run("--changed", "--base", "main", "--list")
    assert ran.code == 0, ran
    assert "tests/test_gamma.py  (mentions util/check.py)" in ran.out
    assert "util/check.py verify  (runs util/check.py)" in ran.out
    assert "changed juniper-demo/juniper_demo/extra.py" in ran.out
    assert "tests/test_alpha.py" not in ran.out
    ml.commit("next")
    (ml.root / "tests" / "helper_mod.py").write_text("VALUE = 2\n")
    assert "tests/test_gamma.py  (mentions tests/helper_mod.py)" in ml.run("--changed", "--base", "HEAD", "--list").out
    ml.commit("third")
    (ml.root / "tests" / "test_alpha.py").write_text(FILES["ml"]["tests/test_alpha.py"] + "\n")
    assert "tests/test_alpha.py  (changed)" in ml.run("--changed", "--base", "HEAD", "--list").out


def test_dc_changed_selects_what_a_change_touches(dc: Repo) -> None:
    needs_git()
    dc.git("init", "-q", "-b", "main")
    dc.commit("base")
    (dc.root / "util" / "check.py").write_text("print('changed')\n")
    out = dc.run("--changed", "--base", "main", "--list").out
    tests = dc.root / "tests"
    assert "tests/test_gamma.py  (mentions util/check.py)" in out
    assert f"  only: {tests / 'test_gamma.py'}, {tests / 'test_widget.py'}  (mentions util/check.py)" in out, "the unit lane was not narrowed to the two files that name util/check.py"
    assert "integration-tests" not in out.split("groups:", 1)[0], "a file outside the lanes chose a whole lane"
    dc.commit("next")
    (dc.root / "fake_client" / "extra.py").write_text("X = 1\n")
    out = dc.run("--changed", "--base", "HEAD", "--list").out
    assert "unit-tests  1 job" in out and "integration-tests  1 job" in out and "(changed fake_client/extra.py)" in out
    for optional in ("generator-parity", "security", "slow-or-integration-tests"):
        assert f"{optional}  1 job" not in out, "--changed chose an optional lane"
    dc.commit("third")
    (dc.root / "docs").mkdir()
    (dc.root / "docs" / "notes.md").write_text("# notes\n")
    assert "0 job(s) touch them" in dc.run("--changed", "--base", "HEAD", "--list").out
    ran = dc.run("--changed", "--base", "HEAD")
    assert ran.code == 0 and "Nothing selected." in ran.out


def test_rec_changed_follows_the_workflows_path_filter(rec: Repo) -> None:
    needs_git()
    rec.git("init", "-q", "-b", "main")
    rec.commit("base")
    (rec.root / "juniper-recurrence-demo" / "notes.txt").write_text("not python, but under the filter\n")
    (rec.root / "bench" / "extra.py").write_text("X = 1\n")
    out = rec.run("--changed", "--base", "main", "--list").out
    assert "demo  1 job" in out and "(changed juniper-recurrence-demo/notes.txt)" in out
    assert "bench  1 job" in out and "(changed bench/extra.py)" in out
    assert "demo-torch" not in out.split("groups:", 1)[0]


def test_a_changed_run_says_it_is_a_heuristic(ml: Repo) -> None:
    needs_git()
    ml.git("init", "-q", "-b", "main")
    ml.commit("base")
    (ml.root / "util" / "check.py").write_text("print('changed')\n")
    ran = ml.run("--changed", "--base", "main", "-j", "1")
    assert ran.code == 0, ran
    assert "CI runs every lane on every pull request. Run all before trusting green." in ran.out


# ---------------------------------------------------------------------------------------------------------------
# A thin util/run_tests.py, as a process
# ---------------------------------------------------------------------------------------------------------------

THIN_SCRIPT = """\
import sys
from pathlib import Path

from juniper_ci_tools import run_tests as rt

SPEC = rt.RepoSpec(
    project="juniper-fake-ml",
    script=__file__,
    lanes=(rt.step_lane("unittest", "ci.yml", "tests", "Run Python regression tests", groups=("regression",)),),
)

if __name__ == "__main__":
    raise SystemExit(rt.main(SPEC))
"""


def test_a_thin_script_runs_the_engine_and_sigterm_ends_it_like_ctrl_c(ml: Repo) -> None:
    script = ml.write("util/run_tests.py", THIN_SCRIPT)
    env = rt._Env(os.environ)
    for key in FAKE_KEYS:
        env.pop(key, None)
    env.update(PYTHONPATH=str(PACKAGE_DIR), FAKE_STATE=str(ml.state), FAKE_GAMMA_SLEEP="60", FAKE_GAMMA_CHILD="1")
    listed = subprocess.run([sys.executable, str(script), "--list", "--color", "never"], cwd=ml.root, env=env, capture_output=True, text=True, timeout=120, check=False)  # nosec B603 - the thin script, fixed argv
    assert listed.returncode == 0 and "tests/test_alpha.py" in listed.stdout, listed.stderr
    runner = subprocess.Popen([sys.executable, str(script), "--log-dir", str(ml.logs), "--color", "never", "gamma", "--timeout", "0"], cwd=ml.root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)  # nosec B603 - the thin script, fixed argv
    try:
        deadline = time.monotonic() + 30
        while not (ml.state / "gamma-sleeping").exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert (ml.state / "gamma-sleeping").exists(), "the suite never started"
        runner.send_signal(signal.SIGTERM)
        out, err = runner.communicate(timeout=60)
    finally:
        if runner.poll() is None:
            runner.kill()
            runner.wait(timeout=30)
    assert runner.returncode == 130, out + err
    assert ml.summary()["interrupted"] and _pid_gone(int((ml.state / "gamma-child.pid").read_text()))


def test_build_parser_carries_the_specs_text_and_flags(ml: Repo) -> None:
    parser = rt.build_parser(ml.spec)
    assert parser.description == "The fake ml repo's tests." and parser.epilog == "selectors: all, regression, packages"
    assert "--force-drift" in {option for action in parser._actions for option in action.option_strings}
    help_text = parser.format_help()
    assert "set FAKE_DRIFT=1: the drift suites run outside CI" in help_text
    assert isinstance(parser.parse_args(["--force-drift"]), argparse.Namespace)
    bare = rt.build_parser(dc_spec(ml.root))
    assert bare.description is None and "--force-drift" not in bare.format_help()
