#!/usr/bin/env python3
"""Regression tests for util/run_tests.py, the local test runner.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests
Author:      Paul Calnon (authored via Claude Code)
License:     MIT License

util/run_tests.py runs any subset of juniper-ml's tests with the commands CI runs, reading them from the
workflows on every run. Two kinds of test pin it:

- **Against the real workflows** (no test runs): every suite ci.yml's "Run Python regression tests" step invokes,
  in its order, is a job of the unittest lane; every other command of that step and of "Run bash regression
  tests" is a job too; and every ``ci-<pkg>.yml`` with a ``test`` job is a package lane with a pytest step, a
  coverage gate and a PYTHONPATH inside this checkout. A workflow change the runner cannot read fails here, in
  the PR that makes it, instead of on the next person's machine.
- **Against a fake checkout** built under this checkout's gitignored ``tmp/`` (never the system temp directory,
  which the runner refuses as a log root): three suites, a command, a bash script, and a package lane whose
  ``pytest`` is a stub that records how it was called. These run the real script end to end -- selection,
  timeouts and process-group kills, leftover processes, the parallel re-run, ``-k``, ``--failed``,
  ``--changed``, the child environment, the coverage-path rewrite, the exit codes -- in a few seconds.

Every option ``--help`` lists must appear in docs/REFERENCE.md's "Running tests locally" section.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv
from tests.test_ci_test_wiring_drift import _invoked_suites, _regression_run_script

REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "util" / "run_tests.py"
REFERENCE = REPO_ROOT / "docs" / "REFERENCE.md"


def _load_runner():
    spec = importlib.util.spec_from_file_location("run_tests_under_test", RUNNER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # @dataclass resolves annotations through sys.modules
    spec.loader.exec_module(module)
    return module


RT = _load_runner()

CI_YML = """\
name: CI
on: [push]
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

CI_DEMO_YML = """\
name: CI demo
on: [push]
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
"""

CI_GHOST_YML = """\
name: CI ghost
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: juniper-demo
    steps:
      - name: Install package + test extras
        run: pip install -e ".[test]"
      - name: Run unit tests with coverage
        run: python -m pytest --cov=juniper_demo --cov-report=json:coverage.json
      - name: Enforce per-file coverage gate (blocking)
        run: |
          pip install "juniper-no-such-tools>=1"
          juniper-no-such-tool --coverage-json coverage.json --enforce
"""

FILES = {
    "tests/test_alpha.py": """\
        import unittest


        class AlphaTest(unittest.TestCase):
            def test_cap_one(self):
                self.assertTrue(True)

            def test_two(self):
                self.assertTrue(True)
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
        # Gamma reads what util/check.py prints and uses tests/helper_mod.py (the --changed test needs both names).
        import json
        import os
        import subprocess
        import sys
        import time
        import unittest
        from pathlib import Path

        KEYS = ["TMPDIR", "GIT_CEILING_DIRECTORIES", "DBUS_SESSION_BUS_ADDRESS", "PYTHONPATH", "PYTHONHOME", "DISPLAY",
                "WAYLAND_DISPLAY", "PYTHONUNBUFFERED", "CLAUDE_FAKE", "JUNIPER_FAKE", "WTC_FAKE", "JUNIPER_DRIFT_TEST_FORCE_LOCAL"]


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
    "tests/helper_mod.py": "VALUE = 1\n",
    "util/check.py": """\
        import sys

        print("check ok", sys.argv[1:])
        """,
    "scripts/test_shell.bash": """\
        #!/usr/bin/env bash
        echo "PASS: shell"
        """,
    "gate.py": """\
        import json
        import os
        import sys
        from pathlib import Path

        args = sys.argv[1:]
        report = Path(args[args.index("--coverage-json") + 1])
        Path(os.environ["FAKE_STATE"], "gate.json").write_text(json.dumps({"argv": args, "cwd": os.getcwd(), "report_exists": report.is_file()}))
        sys.exit(0 if report.is_file() else 1)
        """,
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
    "juniper-demo/tests/test_demo.py": "def test_demo():\n    assert True\n",
    # A stand-in for pytest: `python -m pytest`, run from juniper-demo/, imports this module before any real one.
    "juniper-demo/pytest.py": """\
        import json
        import os
        import sys
        from pathlib import Path

        import juniper_demo

        args = sys.argv[1:]
        Path(os.environ["FAKE_STATE"], "pytest.json").write_text(json.dumps({
            "argv": args,
            "cwd": os.getcwd(),
            "PYTHONPATH": os.environ.get("PYTHONPATH"),
            "COVERAGE_FILE": os.environ.get("COVERAGE_FILE"),
            "juniper_demo": juniper_demo.__file__,
        }))
        for arg in args:
            if arg.startswith("--cov-report=json:"):
                Path(arg.split(":", 1)[1]).write_text(json.dumps({"totals": {"percent_covered": 100.0}}))
        rc = int(os.environ.get("FAKE_PYTEST_RC", "0"))
        print("1 passed in 0.01s" if rc == 0 else "FAILED tests/test_demo.py::test_demo - boom\\n1 failed in 0.01s")
        sys.exit(rc)
        """,
}


def _repo_tmp() -> Path:
    """This checkout's gitignored tmp/: on a CI runner the default temp directory is the system one."""
    path = REPO_ROOT / "tmp"
    path.mkdir(exist_ok=True)
    return path


def _stop(proc: subprocess.Popen) -> None:
    """Cleanup: never leave a runner behind when a test fails before it finishes."""
    if proc.poll() is None:
        proc.kill()
        proc.wait(timeout=30)


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


class FakeCheckout(unittest.TestCase):
    """A disposable checkout with fake workflows, suites, a command, a bash script and a package lane."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="run-tests-", dir=_repo_tmp())
        self.addCleanup(self._tmp.cleanup)
        base = Path(self._tmp.name)
        self.root = base / "checkout"
        self.logs = base / "logs"
        self.state = base / "state"
        self.state.mkdir()
        workflows = self.root / ".github" / "workflows"
        workflows.mkdir(parents=True)
        (workflows / "ci.yml").write_text(CI_YML)
        (workflows / "ci-demo.yml").write_text(CI_DEMO_YML)
        for rel, text in FILES.items():
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(textwrap.dedent(text))

    def env(self, **overrides: str) -> RedactedEnv:
        env = RedactedEnv(os.environ, FAKE_STATE=str(self.state), **overrides)
        for key in ("FAKE_BETA", "FAKE_GAMMA_SLEEP", "FAKE_GAMMA_CHILD", "FAKE_PYTEST_RC", "NO_COLOR"):
            if key not in overrides:
                env.pop(key, None)
        return env

    def run_tests(self, *args: str, timeout: float = 120, **env: str) -> subprocess.CompletedProcess:
        argv = [sys.executable, str(RUNNER), "--checkout", str(self.root), "--log-dir", str(self.logs), "--color", "never", *args]
        return subprocess.run(argv, cwd=self.root, env=self.env(**env), capture_output=True, text=True, timeout=timeout, check=False)

    def summary(self) -> dict:
        runs = sorted(path for path in self.logs.iterdir() if path.is_dir() and path.name != "latest")
        self.assertTrue(runs, "no run directory was written")
        return json.loads((runs[-1] / "summary.json").read_text())

    def jobs(self) -> dict[str, dict]:
        return {job["id"]: job for job in self.summary()["jobs"]}

    def read_state(self, name: str) -> dict:
        return json.loads((self.state / name).read_text())


# ---------------------------------------------------------------------------------------------------------------
# The real workflows
# ---------------------------------------------------------------------------------------------------------------


class RealWorkflowsTest(unittest.TestCase):
    """The runner reads this checkout's workflows, and reads them the way CI runs them."""

    lanes: dict
    ci_suites: list[str]

    @classmethod
    def setUpClass(cls) -> None:
        cls.lanes = RT.discover(REPO_ROOT)
        ci_text = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        cls.ci_suites = ["tests/" + name for name in _invoked_suites(_regression_run_script(ci_text))]

    def test_every_suite_ci_invokes_is_a_unittest_job_in_ci_order(self) -> None:
        suites = [job.id for job in self.lanes["unittest"].jobs if job.kind == "unittest"]
        self.assertGreater(len(suites), 200, "the runner found almost no suites: its reader is broken")
        self.assertEqual(suites, self.ci_suites)

    def test_every_suite_on_disk_is_runnable(self) -> None:
        on_disk = sorted(f"tests/{path.name}" for path in (REPO_ROOT / "tests").glob("test_*.py"))
        self.assertEqual(sorted(job.id for job in self.lanes["unittest"].jobs if job.kind == "unittest"), on_disk)

    def test_the_other_commands_of_both_steps_are_jobs(self) -> None:
        import yaml

        job = yaml.safe_load((REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))["jobs"]["tests"]
        for lane, step_name in (("unittest", RT.UNITTEST_STEP), ("bash", RT.BASH_STEP)):
            script = next(step["run"] for step in job["steps"] if step.get("name") == step_name)
            expected = [line for line in RT.logical_lines(script) if not line.startswith("echo") and "-m unittest" not in line]
            with self.subTest(lane=lane):
                self.assertEqual(len([j for j in self.lanes[lane].jobs if j.kind == "command"]), len(expected))
        self.assertTrue(self.lanes["bash"].jobs, "the bash lane is empty")

    def test_one_package_lane_per_ci_workflow_with_a_test_job(self) -> None:
        import yaml

        expected = sorted(path.stem[len("ci-") :] for path in (REPO_ROOT / ".github" / "workflows").glob("ci-*.yml") if "test" in (yaml.safe_load(path.read_text(encoding="utf-8")).get("jobs") or {}))
        self.assertEqual(sorted(lane.name for lane in RT.package_lanes(self.lanes)), expected)
        self.assertGreaterEqual(len(expected), 6)
        for lane in RT.package_lanes(self.lanes):
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

    def test_list_runs_nothing_and_names_every_suite(self) -> None:
        proc = subprocess.run([sys.executable, str(RUNNER), "--list", "--color", "never"], cwd=REPO_ROOT, capture_output=True, text=True, check=False, timeout=120)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        listed = [line.strip() for line in proc.stdout.splitlines() if line.startswith("  tests/test_")]
        self.assertEqual(listed, self.ci_suites)

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
        options = sorted({option for action in RT.build_parser()._actions for option in action.option_strings if option not in ("-h", "--help")})
        missing = [option for option in options if f"`{option}" not in section and f"{option} " not in section and f"{option}`" not in section]
        self.assertEqual(missing, [], "options --help lists that the REFERENCE section does not document")
        for selector in ("all", "regression", "unittest", "bash", "packages", "--changed", "--failed"):
            self.assertIn(selector, section)


# ---------------------------------------------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------------------------------------------


class ParsingTest(unittest.TestCase):
    def test_comments_are_stripped_as_bash_reads_them(self) -> None:
        self.assertEqual(RT.strip_comment("pip install wheel  # a comment"), "pip install wheel")
        self.assertEqual(RT.strip_comment('echo "a # b" c'), 'echo "a # b" c')
        self.assertEqual(RT.strip_comment("echo a#b"), "echo a#b")
        self.assertEqual(RT.split_command("python3 -m unittest -v tests/test_x.py  # tests/test_ghost.py", "t"), ["python3", "-m", "unittest", "-v", "tests/test_x.py"])

    def test_continuations_join_and_comment_lines_drop(self) -> None:
        script = "# a comment\npython -m pytest \\\n  --cov=x \\\n  -q\n\necho done\n"
        self.assertEqual(RT.logical_lines(script), ["python -m pytest --cov=x -q", "echo done"])

    def test_commands_that_need_a_shell_are_named(self) -> None:
        for line in ("cd tests && python3 -m unittest t.py", "pytest | tee log", "python $FILE", "export A=1", "FOO=1 pytest", "cmd 2>&1"):
            with self.subTest(line=line):
                self.assertIsNotNone(RT.shell_need(RT.split_command(line, "t")))
        self.assertIsNone(RT.shell_need(RT.split_command('juniper-coverage-gap-map --coverage-json coverage.json --omit "*/__main__.py"', "t")))

    def test_pip_install_arguments(self) -> None:
        args = RT.pip_install_args(RT.split_command('python -m pip install -U "pip>=26" -r req.txt -e ".[test]" --index-url https://example.invalid/simple wheel', "t"))
        self.assertEqual(RT.parse_pip_install(args), (["pip>=26", "wheel"], [".[test]"]))
        self.assertIsNone(RT.pip_install_args(["echo", "pip", "install"]))

    def test_editable_targets_and_extras(self) -> None:
        base = Path("/checkout")
        self.assertEqual(RT.editable_target(".[test]", base / "juniper-doc-tools"), (base / "juniper-doc-tools", ["test"]))
        self.assertEqual(RT.editable_target("juniper-service-core/.[test,api]", base), (base / "juniper-service-core", ["test", "api"]))
        self.assertEqual(RT.editable_target("juniper-model-core", base), (base / "juniper-model-core", []))

    def test_result_lines_are_counted(self) -> None:
        counts, failed = RT.unittest_counts("FAIL: test_b (tests.test_x.T.test_b)\nERROR: setUpClass (tests.test_x.U)\nRan 12 tests in 0.5s\n\nFAILED (failures=1, errors=1, skipped=3)\n")
        self.assertEqual(counts, {"ran": 12, "failures": 1, "errors": 1, "skipped": 3})
        self.assertEqual(failed, ["tests.test_x.T.test_b", "tests.test_x.U.setUpClass"])
        self.assertEqual(RT.describe_counts("unittest", counts), "1 failed, 1 errors of 12, 3 skipped")
        counts, failed = RT.pytest_counts("FAILED tests/test_a.py::test_x - boom\n===== 1 failed, 230 passed, 2 skipped in 5.12s =====\n")
        self.assertEqual(counts, {"failed": 1, "passed": 230, "skipped": 2})
        self.assertEqual(failed, ["tests/test_a.py::test_x"])

    def test_origin_verdict(self) -> None:
        here = Path(REPO_ROOT / "juniper-doc-tools" / "juniper_doc_tools")
        self.assertEqual(RT.origin_verdict("juniper_doc_tools", str(here / "__init__.py"), here), "")
        self.assertIn("not from this checkout", RT.origin_verdict("juniper_doc_tools", "/elsewhere/site-packages/juniper_doc_tools/__init__.py", here))
        self.assertIn("not importable", RT.origin_verdict("juniper_doc_tools", None, here))


# ---------------------------------------------------------------------------------------------------------------
# Selection, on the fake checkout
# ---------------------------------------------------------------------------------------------------------------


class SelectionTest(FakeCheckout):
    def pick(self, *tokens: str, cwd: Path | None = None) -> dict[str, list[str]]:
        lanes = RT.discover(self.root)
        picker = RT.Picker(lanes)
        for token in tokens:
            RT.resolve_selector(token, lanes, self.root, cwd or self.root, picker)
        return {job.id: job.targets for job in picker.jobs()}

    def test_groups_lanes_and_aliases(self) -> None:
        everything = ["tests/test_alpha.py", "tests/test_beta.py", "tests/test_gamma.py", "util/check.py verify", "scripts/test_shell.bash", "demo"]
        self.assertEqual(list(self.pick("all")), everything)
        self.assertEqual(list(self.pick("regression")), everything[:5])
        self.assertEqual(list(self.pick("unittest")), everything[:4])
        self.assertEqual(list(self.pick("bash")), ["scripts/test_shell.bash"])
        self.assertEqual(list(self.pick("packages")), ["demo"])
        self.assertEqual(list(self.pick("juniper-demo")), ["demo"])

    def test_every_spelling_of_a_suite(self) -> None:
        for token in ("tests/test_alpha.py", "test_alpha.py", "test_alpha", "alpha", "tests.test_alpha"):
            with self.subTest(token=token):
                self.assertEqual(self.pick(token), {"tests/test_alpha.py": []})
        self.assertEqual(self.pick("test_alpha.py", cwd=self.root / "tests"), {"tests/test_alpha.py": []})

    def test_globs(self) -> None:
        self.assertEqual(list(self.pick("*a")), ["tests/test_alpha.py", "tests/test_beta.py", "tests/test_gamma.py"])
        self.assertEqual(list(self.pick("test_g*")), ["tests/test_gamma.py"])

    def test_a_class_or_test_narrows_a_suite_and_the_whole_suite_wins(self) -> None:
        self.assertEqual(self.pick("tests/test_alpha.py::AlphaTest::test_two"), {"tests/test_alpha.py": ["tests.test_alpha.AlphaTest.test_two"]})
        self.assertEqual(self.pick("tests.test_alpha.AlphaTest"), {"tests/test_alpha.py": ["tests.test_alpha.AlphaTest"]})
        self.assertEqual(self.pick("tests/test_alpha.py::AlphaTest", "alpha"), {"tests/test_alpha.py": []})
        self.assertEqual(self.pick("alpha", "tests/test_alpha.py::AlphaTest"), {"tests/test_alpha.py": []})

    def test_a_package_path_narrows_its_lane(self) -> None:
        target = str(self.root / "juniper-demo" / "tests" / "test_demo.py")
        self.assertEqual(self.pick("juniper-demo/tests/test_demo.py::test_demo"), {"demo": [target + "::test_demo"]})
        self.assertEqual(self.pick("juniper-demo"), {"demo": []})

    def test_commands_by_path(self) -> None:
        self.assertEqual(list(self.pick("scripts/test_shell.bash")), ["scripts/test_shell.bash"])
        self.assertEqual(list(self.pick("util/check.py")), ["util/check.py verify"])

    def test_unknown_selectors_are_usage_errors_with_suggestions(self) -> None:
        with self.assertRaises(RT.UsageError) as caught:
            self.pick("alpah")
        self.assertIn("did you mean alpha", str(caught.exception))
        for token in ("'no_such_*'", "tests/test_nope.py", "docs/nothing.md"):
            with self.subTest(token=token), self.assertRaises(RT.UsageError):
                self.pick(token.strip("'"))

    def test_an_unwired_suite_is_refused_by_name(self) -> None:
        (self.root / "tests" / "test_unwired.py").write_text("import unittest\n")
        with self.assertRaises(RT.UsageError) as caught:
            self.pick("tests/test_unwired.py")
        self.assertIn("not a suite ci.yml runs", str(caught.exception))


# ---------------------------------------------------------------------------------------------------------------
# Running, on the fake checkout
# ---------------------------------------------------------------------------------------------------------------


class RunTest(FakeCheckout):
    def test_everything_passes_and_the_record_is_complete(self) -> None:
        proc = self.run_tests("all", "-j", "3", FAKE_BETA="pass")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        jobs = self.jobs()
        self.assertEqual({job["status"] for job in jobs.values()}, {"PASS"}, proc.stdout)
        self.assertEqual(jobs["tests/test_alpha.py"]["counts"]["ran"], 2)
        self.assertEqual(jobs["demo"]["detail"], "1 passed; coverage gates passed")
        summary = self.summary()
        self.assertEqual(summary["schema"], 1)
        self.assertEqual(summary["exit_code"], 0)
        run_dir = next(path for path in self.logs.iterdir() if path.is_dir() and path.name != "latest")
        self.assertEqual(os.readlink(self.logs / "latest"), run_dir.name)
        self.assertTrue((run_dir / "summary.txt").is_file())
        self.assertTrue((run_dir / "unittest" / "test_alpha.log").is_file())
        self.assertIn("PASSED", proc.stdout)

    def test_the_package_lane_tests_this_checkout_and_writes_coverage_to_the_run_directory(self) -> None:
        proc = self.run_tests("demo")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        run_dir = next(path for path in self.logs.iterdir() if path.is_dir() and path.name != "latest")
        pytest = self.read_state("pytest.json")
        self.assertIn(f"--cov-report=json:{run_dir / 'demo' / 'coverage.json'}", pytest["argv"])
        self.assertIn("--cov-fail-under=85", pytest["argv"])
        self.assertEqual(pytest["COVERAGE_FILE"], str(run_dir / "demo" / ".coverage"))
        self.assertEqual(pytest["PYTHONPATH"], str(self.root / "juniper-demo"))
        self.assertEqual(pytest["juniper_demo"], str(self.root / "juniper-demo" / "juniper_demo" / "__init__.py"))
        gate = self.read_state("gate.json")
        self.assertTrue(gate["report_exists"])
        self.assertEqual(gate["argv"][gate["argv"].index("--coverage-json") + 1], str(run_dir / "demo" / "coverage.json"))
        self.assertFalse((self.root / "juniper-demo" / "coverage.json").exists(), "coverage.json landed in the checkout")

    def test_a_narrowed_package_run_turns_the_coverage_gates_off(self) -> None:
        proc = self.run_tests("juniper-demo/tests/test_demo.py")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        argv = self.read_state("pytest.json")["argv"]
        self.assertFalse([arg for arg in argv if arg.startswith("--cov")], argv)
        self.assertEqual(argv[-1], str(self.root / "juniper-demo" / "tests" / "test_demo.py"))
        self.assertFalse((self.state / "gate.json").exists(), "the coverage gate ran on a partial run")
        self.assertIn("coverage gates off", self.jobs()["demo"]["detail"])
        proc = self.run_tests("demo", "--no-coverage")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertFalse([arg for arg in self.read_state("pytest.json")["argv"] if arg.startswith("--cov")])

    def test_a_package_failure_is_reported_and_the_gate_does_not_run(self) -> None:
        proc = self.run_tests("demo", FAKE_PYTEST_RC="1")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        job = self.jobs()["demo"]
        self.assertEqual(job["status"], "FAIL")
        self.assertEqual(job["failed_tests"], ["tests/test_demo.py::test_demo"])
        self.assertEqual([step["status"] for step in job["steps"]], ["FAIL", "NOT-RUN"])
        self.assertFalse((self.state / "gate.json").exists())

    def test_a_failure_is_reported_and_every_other_job_still_runs(self) -> None:
        proc = self.run_tests("regression", "-j", "1")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        jobs = self.jobs()
        self.assertEqual(jobs["tests/test_beta.py"]["status"], "FAIL")
        self.assertEqual(jobs["tests/test_beta.py"]["failed_tests"], ["tests.test_beta.BetaTest.test_fails"])
        self.assertEqual(jobs["tests/test_gamma.py"]["status"], "PASS", "a job after the failure did not run")
        self.assertEqual(jobs["scripts/test_shell.bash"]["status"], "PASS")
        self.assertIn("beta was told to fail", proc.stdout, "the failure's output tail was not printed")
        self.assertIn("--failed", proc.stdout)

    def test_fail_fast_starts_nothing_after_the_first_failure(self) -> None:
        proc = self.run_tests("regression", "-j", "1", "-x")
        self.assertEqual(proc.returncode, 1)
        jobs = self.jobs()
        self.assertEqual(jobs["tests/test_beta.py"]["status"], "FAIL")
        self.assertEqual(jobs["tests/test_gamma.py"]["status"], "NOT-RUN")

    def test_a_job_that_passes_alone_after_failing_in_parallel_is_a_rerun_pass(self) -> None:
        proc = self.run_tests("unittest", "-j", "2", FAKE_BETA="flaky")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        beta = self.jobs()["tests/test_beta.py"]
        self.assertEqual(beta["status"], "RERUN-PASS")
        self.assertEqual(beta["first_pass"]["status"], "FAIL")
        self.assertTrue(beta["steps"][0]["log"].endswith("test_beta.rerun.log"))
        self.assertIn("Passed only when re-run alone", proc.stdout)
        (self.state / "beta-ran-once").unlink()
        proc = self.run_tests("unittest", "-j", "2", "--no-rerun", FAKE_BETA="flaky")
        self.assertEqual(proc.returncode, 1, "--no-rerun still re-ran the failure")

    def test_keywords_filter_tests_and_a_filter_that_matches_nothing_exits_5(self) -> None:
        proc = self.run_tests("regression", "-k", "cap", FAKE_BETA="pass")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        jobs = self.jobs()
        self.assertEqual(jobs["tests/test_alpha.py"]["counts"]["ran"], 1)
        self.assertEqual(jobs["tests/test_beta.py"]["status"], "NO-TESTS")
        self.assertNotIn("util/check.py verify", jobs, "-k ran a command job, which has no test names")
        proc = self.run_tests("unittest", "-k", "no_such_test")
        self.assertEqual(proc.returncode, 5, proc.stdout + proc.stderr)

    def test_failed_reruns_the_failures_of_the_last_run(self) -> None:
        self.assertEqual(self.run_tests("regression", "-j", "1").returncode, 1)
        listed = self.run_tests("--failed", "--list")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        self.assertEqual([line.strip() for line in listed.stdout.splitlines() if line.startswith("  tests/")], ["tests/test_beta.py  (failed in " + sorted(p.name for p in self.logs.iterdir() if p.name != "latest")[-1] + ")"])
        proc = self.run_tests("--failed", FAKE_BETA="pass")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(list(self.jobs()), ["tests/test_beta.py"])

    def test_a_timeout_kills_the_whole_process_group(self) -> None:
        # 4 s, not less: on a loaded CI runner the suite must still reach its sleep (and write the pid) first.
        proc = self.run_tests("gamma", "--timeout", "4", FAKE_GAMMA_SLEEP="60", FAKE_GAMMA_CHILD="1")
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertEqual(self.jobs()["tests/test_gamma.py"]["status"], "TIMEOUT")
        self.assertTrue((self.state / "gamma-child.pid").is_file(), "the suite timed out before it started its child: the test proved nothing")
        self.assertTrue(_pid_gone(int((self.state / "gamma-child.pid").read_text())), "the step's grandchild survived the timeout")

    def test_processes_a_step_leaves_behind_are_killed(self) -> None:
        proc = self.run_tests("gamma", FAKE_GAMMA_CHILD="1")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        job = self.jobs()["tests/test_gamma.py"]
        self.assertTrue(job["steps"][0]["leftovers"])
        self.assertIn("killed processes it left behind", job["detail"])
        self.assertTrue(_pid_gone(int((self.state / "gamma-child.pid").read_text())))

    def test_sigterm_ends_the_run_like_ctrl_c_and_keeps_the_summary(self) -> None:
        argv = [sys.executable, str(RUNNER), "--checkout", str(self.root), "--log-dir", str(self.logs), "--color", "never", "gamma", "--timeout", "0"]
        runner = subprocess.Popen(argv, cwd=self.root, env=self.env(FAKE_GAMMA_SLEEP="60", FAKE_GAMMA_CHILD="1"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(_stop, runner)
        deadline = time.monotonic() + 30
        while not (self.state / "gamma-sleeping").exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertTrue((self.state / "gamma-sleeping").exists(), "the suite never started")
        runner.send_signal(signal.SIGTERM)
        out, err = runner.communicate(timeout=60)
        self.assertEqual(runner.returncode, 130, out + err)
        summary = self.summary()
        self.assertTrue(summary["interrupted"])
        self.assertEqual(summary["jobs"][0]["status"], "NOT-RUN")
        self.assertTrue(_pid_gone(int((self.state / "gamma-child.pid").read_text())))

    def test_ctrl_c_in_a_parallel_run_kills_every_running_step(self) -> None:
        argv = [sys.executable, str(RUNNER), "--checkout", str(self.root), "--log-dir", str(self.logs), "--color", "never", "unittest", "-j", "2", "--timeout", "0"]
        runner = subprocess.Popen(argv, cwd=self.root, env=self.env(FAKE_BETA="pass", FAKE_GAMMA_SLEEP="60", FAKE_GAMMA_CHILD="1"), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.addCleanup(_stop, runner)
        deadline = time.monotonic() + 30
        while not (self.state / "gamma-sleeping").exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        self.assertTrue((self.state / "gamma-sleeping").exists(), "the suite never started")
        runner.send_signal(signal.SIGINT)
        out, err = runner.communicate(timeout=60)
        self.assertEqual(runner.returncode, 130, out + err)
        self.assertIn("INTERRUPTED", out)
        jobs = self.jobs()
        self.assertEqual(jobs["tests/test_gamma.py"]["status"], "NOT-RUN")
        self.assertTrue(self.summary()["interrupted"])
        self.assertTrue(_pid_gone(int((self.state / "gamma-child.pid").read_text())), "Ctrl-C left the step's grandchild running")

    def test_the_child_environment(self) -> None:
        tmpdir = self.root.parent / "children-tmp"
        tmpdir.mkdir()
        proc = self.run_tests("gamma", TMPDIR=str(tmpdir), CLAUDE_FAKE="1", JUNIPER_FAKE="1", WTC_FAKE="1", DISPLAY=":99", PYTHONPATH="/nonexistent", WAYLAND_DISPLAY="w")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        record = self.read_state("gamma-env.json")
        self.assertEqual(record["DBUS_SESSION_BUS_ADDRESS"], RT.BUS_GUARD)
        self.assertIsNone(record["DISPLAY"])
        self.assertIsNone(record["WAYLAND_DISPLAY"])
        self.assertIsNone(record["PYTHONPATH"])
        self.assertEqual(record["PYTHONUNBUFFERED"], "1")
        self.assertEqual(record["TMPDIR"], str(tmpdir))
        self.assertEqual(record["GIT_CEILING_DIRECTORIES"].split(os.pathsep)[0], str(tmpdir))
        self.assertEqual(record["stdin"], "", "a child's stdin is not /dev/null")
        self.assertEqual((record["CLAUDE_FAKE"], record["JUNIPER_FAKE"]), ("1", "1"))
        self.assertIsNone(record["JUNIPER_DRIFT_TEST_FORCE_LOCAL"])
        proc = self.run_tests("gamma", "--clean-env", "--force-drift", TMPDIR=str(tmpdir), CLAUDE_FAKE="1", JUNIPER_FAKE="1", WTC_FAKE="1")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        record = self.read_state("gamma-env.json")
        self.assertEqual((record["CLAUDE_FAKE"], record["JUNIPER_FAKE"], record["WTC_FAKE"]), (None, None, None))
        self.assertEqual(record["JUNIPER_DRIFT_TEST_FORCE_LOCAL"], "1")

    def test_a_tmpdir_under_the_system_temp_directory_is_replaced(self) -> None:
        system_tmp = "/tmp"  # tmp-path-literal: allow -- the value under test; the runner must refuse it, so nothing is written there
        proc = self.run_tests("gamma", TMPDIR=os.path.join(system_tmp, "run-tests-never-created"))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(self.read_state("gamma-env.json")["TMPDIR"], str(self.root / "tmp"))
        self.assertIn("TMPDIR was under the system temp directory", proc.stdout)
        refused = self.run_tests("gamma", "--tmpdir", os.path.join(system_tmp, "x"))
        self.assertEqual(refused.returncode, 2)
        self.assertIn("system temp directory", refused.stderr)

    def test_a_missing_gate_tool_makes_the_lane_unavailable(self) -> None:
        (self.root / ".github" / "workflows" / "ci-ghost.yml").write_text(CI_GHOST_YML)
        proc = self.run_tests("ghost")
        self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
        job = self.jobs()["ghost"]
        self.assertEqual(job["status"], "UNAVAILABLE")
        self.assertIn("juniper-no-such-tool is not installed", job["detail"])
        self.assertIn("juniper-no-such-tools>=1", job["detail"])

    def test_usage_errors_exit_2(self) -> None:
        for args, needle in ((("alpah",), "did you mean alpha"), (("alpha", "demo", "--", "-x"), "one runner"), (("--stream", "--quiet"), "do not go together")):
            with self.subTest(args=args):
                proc = self.run_tests(*args)
                self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
                self.assertIn(needle, proc.stderr)

    def test_a_ci_line_that_needs_a_shell_is_refused_by_name(self) -> None:
        ci = self.root / ".github" / "workflows" / "ci.yml"
        ci.write_text(CI_YML.replace("python3 util/check.py verify", "cd util && python3 check.py verify"))
        proc = self.run_tests("--list")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("cd util && python3 check.py verify", proc.stderr)
        self.assertIn("needs a shell", proc.stderr)

    def test_dry_run_prints_the_commands_and_writes_nothing(self) -> None:
        proc = self.run_tests("--dry-run", "all")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("-m unittest -v tests/test_alpha.py", proc.stdout)
        self.assertIn("PYTHONPATH=", proc.stdout)
        self.assertFalse(self.logs.exists())
        self.assertFalse((self.state / "gamma-env.json").exists(), "a dry run ran a suite")


class ChangedTest(FakeCheckout):
    """--changed: a heuristic over-selection from file references, against a merge base."""

    def git(self, *args: str) -> str:
        config = self.root.parent / "gitconfig"
        config.touch()
        env = RedactedEnv(
            os.environ,
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
        return subprocess.run(["git", "-C", str(self.root), *args], env=env, capture_output=True, text=True, check=True).stdout

    def test_changed_selects_what_names_the_changed_files(self) -> None:
        if shutil.which("git") is None:
            self.skipTest("git is not installed")
        self.git("init", "-q", "-b", "main")
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "base")
        (self.root / "util" / "check.py").write_text("print('changed')\n")
        (self.root / "juniper-demo" / "juniper_demo" / "extra.py").write_text("X = 1\n")
        proc = self.run_tests("--changed", "--base", "main", "--list")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("tests/test_gamma.py  (mentions util/check.py)", proc.stdout)
        self.assertIn("util/check.py verify  (runs util/check.py)", proc.stdout)
        self.assertIn("changed juniper-demo/juniper_demo/extra.py", proc.stdout)
        self.assertNotIn("tests/test_alpha.py", proc.stdout)
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "next")
        (self.root / "tests" / "helper_mod.py").write_text("VALUE = 2\n")
        proc = self.run_tests("--changed", "--base", "HEAD", "--list")
        self.assertIn("tests/test_gamma.py  (mentions tests/helper_mod.py)", proc.stdout)
        proc = self.run_tests("--changed", "--base", "no-such-ref", "--list")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("no merge base", proc.stderr)


if __name__ == "__main__":
    unittest.main()
