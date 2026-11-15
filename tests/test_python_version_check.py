#!/usr/bin/env python3
"""Hermetic gate for util/python_version_check.py, the local Python-version test helper (3.15 migration, phase 1).

Project:     Juniper
Sub-Project: juniper-ml
Application: ecosystem tooling regression tests
Author:      Paul Calnon
License:     MIT License

The owner's ruling of 2026-11-14: Python 3.15 is tested locally and in CI, and its checks report results
without blocking a commit, a merge or a deployment. util/python_version_check.py builds one venv per repo
and version at a FIXED path in the repo's primary tmp/, installs the repo with its CI's commands, and runs
the repo's own wrapper there. This suite pins:

- the config: conf/python_versions.yaml carries the ruling (blocking 3.12-3.14, informational 3.15), and an
  invalid file (a version in both lists, an unquoted version, an unknown key) is refused with exit 2;
- the venv path: derived from the root, the repo and the version only, whatever TMPDIR, the cwd or
  --checkout say;
- the exit code: 0 whatever the results, and 1 under --strict on a failure or an unavailable check;
- an interpreter that is missing or reports another version is `unavailable`, not a crash;
- --dry-run and --list run nothing and write nothing;
- every log lands where the summary says, under juniper-ml's primary tmp/;
- the child environment: the venv first on PATH, VIRTUAL_ENV, TMPDIR, the scrubbed variables;
- the venv is reused, rebuilt on --recreate or when stale, and a path that is not a venv is never removed;
- a run changes no file of the checkout;
- .pre-commit-config.yaml never runs the helper.

How it stays hermetic: no real interpreter, venv, pip or repo is used. A stub ``python3.15`` answers the
version probe and builds a stub venv, whose ``python`` answers the probe and ``-m pip``; the demo checkout's
wrapper records its environment. PATH holds only those stubs and symlinks to a few shell tools, and
PYTHON_VERSION_CHECK_SYSTEM_BIN names a temp directory, so the host's own python3.15 is never found. Every
path is under a directory from tempfile, which follows TMPDIR.
"""

from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess  # nosec B404 - drives the helper and its stubs with fixed argv
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

import yaml

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "python_version_check.py"
REPO_CONFIG = REPO_ROOT / "conf" / "python_versions.yaml"
PRE_COMMIT_CONFIG = REPO_ROOT / ".pre-commit-config.yaml"
TIMEOUT_SECONDS = 120
DEMO = "juniper-demo"
TOOLS = ("bash", "chmod", "cp", "ln", "mkdir")
HELPER_NAMES = ("python_version_check", "python_versions.yaml")

#: The ten repos of the parent Juniper/AGENTS.md's Active Repositories table, in the config's order.
ECOSYSTEM_REPOS = (
    "juniper-canopy",
    "juniper-cascor",
    "juniper-cascor-client",
    "juniper-cascor-worker",
    "juniper-data",
    "juniper-data-client",
    "juniper-deploy",
    "juniper-harcot",
    "juniper-ml",
    "juniper-recurrence",
)


def load_module():
    spec = importlib.util.spec_from_file_location("python_version_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their module through sys.modules
    spec.loader.exec_module(module)
    return module


PVC = load_module()

INTERPRETER_STUB = r"""#!/bin/bash
# Stub python3.X: records its argv, answers the version probe, and builds a stub venv.
printf 'interpreter %s\n' "$*" >> "$STUB_LOG"
if [ "$1" = "-I" ] && [ "$2" = "-c" ]; then
    echo "${STUB_VERSION:-3.15.2}"
    exit 0
fi
if [ "$1" = "-m" ] && [ "$2" = "venv" ] && [ "$#" -eq 3 ]; then
    if [ "${STUB_VENV_RC:-0}" != 0 ]; then
        echo "stub venv: failing on purpose" >&2
        exit "$STUB_VENV_RC"
    fi
    mkdir -p "$3/bin"
    printf 'home = stub\nversion = %s\n' "${STUB_VERSION:-3.15.2}" > "$3/pyvenv.cfg"
    cp "$STUB_VENV_PYTHON" "$3/bin/python"
    chmod 755 "$3/bin/python"
    ln -s python "$3/bin/python3"
    exit 0
fi
echo "stub interpreter: refusing argv: $*" >&2
exit 99
"""

VENV_PYTHON_STUB = r"""#!/bin/bash
# Stub venv interpreter: answers the version probe and `-m pip`, and refuses anything else.
printf 'venv-python %s\n' "$*" >> "$STUB_LOG"
if [ "$1" = "-I" ] && [ "$2" = "-c" ]; then
    echo "${STUB_VERSION:-3.15.2}"
    exit 0
fi
if [ "$1" = "-m" ] && [ "$2" = "pip" ]; then
    echo "stub pip: $*"
    exit "${STUB_PIP_RC:-0}"
fi
echo "stub venv python: refusing argv: $*" >&2
exit 99
"""

STALE_VENV_PYTHON = "#!/bin/bash\necho 3.14.9\n"

WRAPPER = r"""#!/bin/bash
# The demo checkout's test wrapper: records its environment outside the checkout and prints a marker.
printf 'wrapper %s\n' "$*" >> "$STUB_LOG"
{
    printf 'VIRTUAL_ENV=%s\n' "$VIRTUAL_ENV"
    printf 'PATH=%s\n' "$PATH"
    printf 'TMPDIR=%s\n' "$TMPDIR"
    printf 'GIT_CEILING_DIRECTORIES=%s\n' "$GIT_CEILING_DIRECTORIES"
    printf 'PYTHONPATH=%s\n' "${PYTHONPATH-<unset>}"
    printf 'PYTHONHOME=%s\n' "${PYTHONHOME-<unset>}"
    printf 'DEMO_UNSET_ME=%s\n' "${DEMO_UNSET_ME-<unset>}"
    printf 'PIP_DISABLE_PIP_VERSION_CHECK=%s\n' "${PIP_DISABLE_PIP_VERSION_CHECK-<unset>}"
    printf 'CWD=%s\n' "$(pwd -P)"
    printf 'python=%s\n' "$(command -v python)"
} > "$STUB_ENV_DUMP"
echo "WRAPPER-OUTPUT-MARKER"
exit "${STUB_TEST_RC:-0}"
"""


def write(path: Path, text: str, mode: int = 0o644) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    path.chmod(mode)
    return path


def demo_config(install: list[str] | None = None, test: dict[str, str] | None = None) -> str:
    recipe = {
        "install": install if install is not None else ['python -m pip install -e ".[test]"'],
        "test": test if test is not None else {"unit": "bash run_tests.bash"},
        "env_unset": ["DEMO_UNSET_ME"],
    }
    return yaml.safe_dump({"schema": 1, "blocking": ["3.12", "3.13", "3.14"], "informational": ["3.15"], "repos": {DEMO: recipe}}, sort_keys=False)


def snapshot(tree: Path, skip_top: tuple[str, ...] = ()) -> dict[str, str]:
    """Every file under tree (relative path -> sha256), and every directory (relative path -> 'dir')."""
    found: dict[str, str] = {}
    for path in sorted(tree.rglob("*")):
        rel = path.relative_to(tree)
        if rel.parts[0] in skip_top:
            continue
        found[str(rel)] = "dir" if path.is_dir() else hashlib.sha256(path.read_bytes()).hexdigest()
    return found


class Sandbox:
    """A temp Juniper root holding a demo checkout and an empty juniper-ml, plus the stubs and a tool dir."""

    def __init__(self, test: unittest.TestCase) -> None:
        self.dir = Path(tempfile.mkdtemp(prefix="python-version-check-"))
        test.addCleanup(shutil.rmtree, self.dir, True)
        self.root = self.dir / "root"
        self.checkout = self.root / DEMO
        write(self.checkout / "run_tests.bash", WRAPPER, 0o755)
        write(self.checkout / "pyproject.toml", "[project]\nname = 'demo'\n")
        (self.root / "juniper-ml").mkdir(parents=True)
        self.sysbin = self.dir / "sysbin"
        self.pathbin = self.dir / "pathbin"
        self.tools = self.dir / "tools"
        for d in (self.sysbin, self.pathbin, self.tools):
            d.mkdir()
        for tool in TOOLS:
            found = shutil.which(tool)
            if not found:
                raise unittest.SkipTest(f"{tool} is not on PATH")
            (self.tools / tool).symlink_to(found)
        self.venv_python = write(self.dir / "stubs" / "python", VENV_PYTHON_STUB, 0o755)
        self.log = self.dir / "stub.log"
        self.env_dump = self.dir / "env.dump"
        self.config = write(self.dir / "python_versions.yaml", demo_config())
        self.venv = self.root / DEMO / "tmp" / "pyvenv" / "py3.15"
        self.log_root = self.root / "juniper-ml" / "tmp" / "python-version-checks"

    def add_interpreter(self, where: str = "sysbin", version: str = "3.15") -> Path:
        return write(getattr(self, where) / f"python{version}", INTERPRETER_STUB, 0o755)

    def env(self, **overrides: str) -> RedactedEnv:
        return RedactedEnv(
            os.environ,
            PATH=os.pathsep.join([str(self.pathbin), str(self.tools)]),
            PYTHON_VERSION_CHECK_SYSTEM_BIN=str(self.sysbin),
            STUB_LOG=str(self.log),
            STUB_ENV_DUMP=str(self.env_dump),
            STUB_VENV_PYTHON=str(self.venv_python),
            **overrides,
        )

    def run(self, *args: str, cwd: Path | None = None, **env: str) -> subprocess.CompletedProcess:
        argv = [sys.executable, str(SCRIPT), "--config", str(self.config), "--root", str(self.root), *args]
        return subprocess.run(argv, cwd=cwd or self.dir, env=self.env(**env), capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False)  # nosec B603

    def summaries(self) -> list[Path]:
        """Oldest first, by write time: two runs in one second get `<stamp>` and `<stamp>-1`."""
        return sorted(self.log_root.glob("*/summary.json"), key=lambda p: (p.stat().st_mtime_ns, str(p)))

    def last_summary(self) -> dict:
        found = self.summaries()
        if not found:
            raise AssertionError(f"no summary.json under {self.log_root}")
        return json.loads(found[-1].read_text(encoding="utf-8"))

    def calls(self) -> list[str]:
        return self.log.read_text(encoding="utf-8").splitlines() if self.log.exists() else []

    def env_seen(self) -> dict[str, str]:
        return dict(line.split("=", 1) for line in self.env_dump.read_text(encoding="utf-8").splitlines())


# ── the config ───────────────────────────────────────────────────────────────────────────────────


def valid_doc() -> dict:
    return {
        "schema": 1,
        "blocking": ["3.12", "3.13", "3.14"],
        "informational": ["3.15"],
        "repos": {"juniper-demo": {"install": ["python -m pip install -e ."], "test": {"unit": "bash run_tests.bash"}}},
    }


class ConfigTest(unittest.TestCase):
    """conf/python_versions.yaml carries the owner's ruling, and an invalid config is refused (exit 2)."""

    def refuse(self, doc: object, *needles: str) -> None:
        with self.assertRaises(PVC.UsageError) as caught:
            PVC.validate_config(doc, Path("conf.yaml"), "0" * 64)
        for needle in needles:
            self.assertIn(needle, str(caught.exception))

    def test_repo_config_carries_the_owner_ruling(self) -> None:
        config = PVC.load_config(REPO_CONFIG)
        self.assertEqual(config.blocking, ("3.12", "3.13", "3.14"))
        self.assertEqual(config.informational, ("3.15",))
        self.assertEqual(tuple(config.repos), ECOSYSTEM_REPOS)
        for repo, recipe in config.repos.items():
            with self.subTest(repo=repo):
                self.assertTrue(recipe.install, f"{repo}: no install step")
                self.assertTrue(recipe.test, f"{repo}: no test step")

    def test_valid_document_loads(self) -> None:
        config = PVC.validate_config(valid_doc(), Path("conf.yaml"), "0" * 64)
        self.assertEqual(config.version_class("3.15"), "informational")
        self.assertEqual(config.version_class("3.13"), "blocking")
        self.assertEqual(config.repos["juniper-demo"].test, (("unit", "bash run_tests.bash"),))
        self.assertEqual(config.repos["juniper-demo"].env_unset, ())

    def test_a_version_in_both_lists_is_refused(self) -> None:
        doc = valid_doc()
        doc["informational"] = ["3.14", "3.15"]
        self.refuse(doc, "3.14 is in both `blocking` and `informational`")

    def test_an_unquoted_version_is_refused(self) -> None:
        doc = yaml.safe_load("schema: 1\nblocking: [3.12, 3.13]\ninformational: []\nrepos: {}\n")
        self.refuse(doc, "not a string", "quote it")

    def test_yaml_reads_an_unquoted_3_10_as_3_1(self) -> None:
        # The reason the rule above exists.
        self.assertEqual(yaml.safe_load("[3.10]"), [3.1])

    def test_malformed_and_duplicate_versions_are_refused(self) -> None:
        for bad, needle in (("3.x", "not a 3.X version"), ("2.7", "not a 3.X version"), ("3.15.1", "not a 3.X version")):
            with self.subTest(version=bad):
                doc = valid_doc()
                doc["informational"] = [bad]
                self.refuse(doc, needle)
        doc = valid_doc()
        doc["blocking"] = ["3.12", "3.12"]
        self.refuse(doc, "lists 3.12 twice")

    def test_an_empty_blocking_list_is_refused_and_an_empty_informational_list_is_not(self) -> None:
        doc = valid_doc()
        doc["blocking"] = []
        self.refuse(doc, "`blocking` must name at least one version")
        doc = valid_doc()
        doc["informational"] = []
        self.assertEqual(PVC.validate_config(doc, Path("conf.yaml"), "0" * 64).informational, ())

    def test_schema_must_be_one(self) -> None:
        for bad in (2, True, None, "1"):
            with self.subTest(schema=bad):
                doc = valid_doc()
                doc["schema"] = bad
                self.refuse(doc, "`schema` must be 1")

    def test_unknown_keys_are_refused(self) -> None:
        doc = valid_doc()
        doc["versions"] = []
        self.refuse(doc, "unknown top-level key(s) versions")
        doc = valid_doc()
        doc["repos"]["juniper-demo"]["tests"] = {}
        self.refuse(doc, "unknown key(s) tests")

    def test_recipe_shapes_are_checked(self) -> None:
        cases: tuple[tuple[object, str], ...] = (
            ({"install": []}, "needs both `install` and `test`"),
            ({"install": [], "test": {}}, "non-empty mapping"),
            ({"install": [], "test": ["bash x"]}, "non-empty mapping"),
            ({"install": [""], "test": {"unit": "x"}}, "non-empty string"),
            ({"install": [], "test": {"Unit Tests": "x"}}, "step name 'Unit Tests'"),
            ({"install": [], "test": {"unit": ""}}, "non-empty command string"),
            ({"install": [], "test": {"unit": "x"}, "env_unset": ["NOT-A-NAME"]}, "not a valid name"),
            ("bash x", "must be a mapping"),
        )
        for recipe, needle in cases:
            with self.subTest(recipe=recipe):
                doc = valid_doc()
                doc["repos"] = {"juniper-demo": recipe}
                self.refuse(doc, needle)

    def test_repo_names_are_checked(self) -> None:
        for bad in ("demo", "juniper_demo", "Juniper-Demo"):
            with self.subTest(repo=bad):
                doc = valid_doc()
                doc["repos"] = {bad: valid_doc()["repos"]["juniper-demo"]}
                self.refuse(doc, "is not of the form juniper-<name>")

    def test_an_invalid_config_exits_2_and_writes_nothing(self) -> None:
        box = Sandbox(self)
        box.add_interpreter()
        write(box.config, "schema: 1\nblocking: ['3.14']\ninformational: ['3.14']\nrepos: {}\n")
        proc = box.run("--repo", DEMO)
        self.assertEqual(proc.returncode, 2, proc.stderr)
        self.assertIn("in both", proc.stderr)
        self.assertEqual(box.calls(), [])
        self.assertFalse(box.log_root.exists())


# ── the command line ─────────────────────────────────────────────────────────────────────────────


class UsageTest(unittest.TestCase):
    """Bad arguments exit 2 before anything runs or is written."""

    def setUp(self) -> None:
        self.box = Sandbox(self)
        self.box.add_interpreter()

    def assert_usage_error(self, proc: subprocess.CompletedProcess, needle: str) -> None:
        self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
        self.assertIn(needle, proc.stderr)
        self.assertEqual(self.box.calls(), [], "nothing may run on a usage error")
        self.assertFalse(self.box.log_root.exists(), "nothing may be written on a usage error")

    def test_unknown_repo(self) -> None:
        self.assert_usage_error(self.box.run("--repo", "juniper-nope"), "unknown repo 'juniper-nope'")

    def test_a_version_in_neither_list(self) -> None:
        self.assert_usage_error(self.box.run("--repo", DEMO, "--python", "3.11"), "Python 3.11 is in neither list")

    def test_checkout_needs_exactly_one_repo(self) -> None:
        self.assert_usage_error(self.box.run("--all", "--checkout", str(self.box.checkout)), "--checkout needs exactly one --repo")

    def test_a_repo_or_all_or_list_is_required(self) -> None:
        self.assert_usage_error(self.box.run(), "name a repo with --repo, or pass --all or --list")

    def test_repo_and_all_are_exclusive(self) -> None:
        proc = self.box.run("--repo", DEMO, "--all")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(self.box.calls(), [])

    def test_a_root_that_is_not_a_directory(self) -> None:
        argv = [sys.executable, str(SCRIPT), "--config", str(self.box.config), "--root", str(self.box.dir / "missing"), "--repo", DEMO]
        proc = subprocess.run(argv, cwd=self.box.dir, env=self.box.env(), capture_output=True, text=True, timeout=TIMEOUT_SECONDS, check=False)  # nosec B603
        self.assertEqual(proc.returncode, 2)
        self.assertIn("is not a directory", proc.stderr)

    def test_the_juniper_prefix_is_optional(self) -> None:
        proc = self.box.run("--repo", "demo")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(self.box.last_summary()["results"][0]["repo"], DEMO)


# ── the venv path ────────────────────────────────────────────────────────────────────────────────


class VenvPathTest(unittest.TestCase):
    """The venv lives at {root}/{repo}/tmp/pyvenv/py{version}: no input but those three moves it."""

    def test_the_path_is_a_function_of_root_repo_and_version(self) -> None:
        root = Path("juniper-root").absolute()
        self.assertEqual(PVC.venv_path(root, "juniper-data", "3.15"), root / "juniper-data" / "tmp" / "pyvenv" / "py3.15")
        self.assertEqual(PVC.lock_path(root, "juniper-data", "3.15"), root / "juniper-data" / "tmp" / "pyvenv" / "py3.15.lock")
        self.assertEqual(PVC.log_root(root), root / "juniper-ml" / "tmp" / "python-version-checks")

    def test_the_default_root_is_juniper_root_then_home(self) -> None:
        with unittest.mock.patch.dict(os.environ, {"JUNIPER_ROOT": "/srv/juniper"}):
            self.assertEqual(PVC.juniper_root(None), Path("/srv/juniper"))
            self.assertEqual(PVC.juniper_root("/elsewhere"), Path("/elsewhere"))
        with unittest.mock.patch.dict(os.environ, {"HOME": "/home/tester"}):
            os.environ.pop("JUNIPER_ROOT", None)
            self.assertEqual(PVC.juniper_root(None), Path("/home/tester/Development/python/Juniper"))

    def venv_line(self, proc: subprocess.CompletedProcess) -> str:
        lines = [line for line in proc.stdout.splitlines() if line.strip().startswith("venv ")]
        self.assertEqual(len(lines), 1, proc.stdout)
        return lines[0].split()[1]

    def test_tmpdir_cwd_and_checkout_do_not_move_it(self) -> None:
        box = Sandbox(self)
        box.add_interpreter()
        other = box.dir / "worktree"
        write(other / "run_tests.bash", WRAPPER, 0o755)
        seen = {
            self.venv_line(box.run("--repo", DEMO, "--dry-run", TMPDIR=str(box.dir / "a"))),
            self.venv_line(box.run("--repo", DEMO, "--dry-run", cwd=box.checkout, TMPDIR=str(box.dir / "b"))),
            self.venv_line(box.run("--repo", DEMO, "--dry-run", "--checkout", str(other))),
        }
        self.assertEqual(seen, {str(box.venv)})

    def test_a_real_run_from_another_checkout_keeps_the_venv_in_the_primary(self) -> None:
        box = Sandbox(self)
        box.add_interpreter()
        other = box.dir / "worktree"
        write(other / "run_tests.bash", WRAPPER, 0o755)
        before = snapshot(other)
        proc = box.run("--repo", DEMO, "--checkout", str(other))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = box.last_summary()["results"][0]
        self.assertEqual(result["venv"], str(box.venv))
        self.assertEqual(result["checkout"], str(other))
        self.assertTrue((box.venv / "pyvenv.cfg").is_file())
        self.assertEqual(box.env_seen()["CWD"], str(other.resolve()), "the wrapper runs in --checkout")
        self.assertEqual(snapshot(other), before, "nothing is written in a --checkout, not even a tmp/")


# ── a real run with stubs ────────────────────────────────────────────────────────────────────────


class RunTest(unittest.TestCase):
    """One check end to end: the phases, the statuses, the exit code, the logs and the environment."""

    def setUp(self) -> None:
        self.box = Sandbox(self)

    def only_result(self) -> dict:
        results = self.box.last_summary()["results"]
        self.assertEqual(len(results), 1, results)
        return results[0]

    def test_a_passing_check(self) -> None:
        self.box.add_interpreter()
        proc = self.box.run("--repo", DEMO)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = self.only_result()
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["class"], "informational")
        self.assertEqual(result["interpreter"], str(self.box.sysbin / "python3.15"))
        self.assertEqual(result["interpreter_version"], "3.15.2")
        self.assertEqual(result["venv_action"], "created")
        self.assertEqual([(s["phase"], s["name"], s["returncode"]) for s in result["steps"]], [("venv", "venv", 0), ("install", "install-1", 0), ("test", "unit", 0)])
        self.assertRegex(proc.stdout, r"(?m)^PASSED +juniper-demo 3\.15 \(informational\)")

    def test_logs_and_summary_land_where_promised(self) -> None:
        self.box.add_interpreter()
        proc = self.box.run("--repo", DEMO)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        summaries = self.box.summaries()
        self.assertEqual(len(summaries), 1)
        run_dir = summaries[0].parent
        self.assertEqual(run_dir.parent, self.box.log_root)
        self.assertRegex(run_dir.name, r"^\d{4}-\d{2}-\d{2}T\d{6}Z$")
        summary = self.box.last_summary()
        self.assertEqual(summary["schema"], 1)
        self.assertEqual(summary["run_dir"], str(run_dir))
        self.assertEqual(summary["exit_code"], 0)
        self.assertEqual(summary["counts"], {"passed": 1, "failed": 0, "unavailable": 0})
        self.assertFalse(summary["interrupted"])
        self.assertIsNotNone(summary["finished"])
        logs = run_dir / DEMO / "py3.15"
        self.assertEqual(sorted(p.name for p in logs.iterdir()), ["install-1.log", "test-unit.log", "venv.log"])
        for step in summary["results"][0]["steps"]:
            self.assertEqual(Path(step["log"]).parent, logs)
            self.assertTrue(Path(step["log"]).is_file())
        self.assertIn("WRAPPER-OUTPUT-MARKER", (logs / "test-unit.log").read_text(encoding="utf-8"))
        self.assertIn("stub pip: -m pip install -e .[test]", (logs / "install-1.log").read_text(encoding="utf-8"))
        self.assertIn(f"summary: {summaries[0]}", proc.stdout)
        self.assertNotIn("WRAPPER-OUTPUT-MARKER", proc.stdout + proc.stderr, "step output goes to its log only")

    def test_an_informational_failure_exits_0(self) -> None:
        self.box.add_interpreter()
        proc = self.box.run("--repo", DEMO, STUB_TEST_RC="1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = self.only_result()
        self.assertEqual((result["status"], result["failed_phase"]), ("failed", "test"))
        self.assertIn("`unit` exited 1", result["reason"])
        self.assertRegex(proc.stdout, r"(?m)^FAILED +juniper-demo 3\.15 \(informational\)")
        self.assertEqual(self.box.last_summary()["exit_code"], 0)

    def test_strict_makes_a_failure_exit_1(self) -> None:
        self.box.add_interpreter()
        proc = self.box.run("--repo", DEMO, "--strict", STUB_TEST_RC="1")
        self.assertEqual(proc.returncode, 1, proc.stderr)
        self.assertEqual(self.box.last_summary()["exit_code"], 1)
        self.assertTrue(self.box.last_summary()["strict"])

    def test_strict_with_everything_passing_exits_0(self) -> None:
        self.box.add_interpreter()
        self.assertEqual(self.box.run("--repo", DEMO, "--strict").returncode, 0)

    def test_a_missing_interpreter_is_unavailable_not_a_crash(self) -> None:
        proc = self.box.run("--repo", DEMO)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)
        result = self.only_result()
        self.assertEqual(result["status"], "unavailable")
        self.assertIn(f"no python3.15 in {self.box.sysbin} or on PATH", result["reason"])
        self.assertEqual(result["steps"], [])
        self.assertRegex(proc.stdout, r"(?m)^UNAVAILABLE +juniper-demo 3\.15")
        self.assertFalse((self.box.root / DEMO / "tmp").exists(), "no venv dir for a check that cannot start")

    def test_strict_makes_an_unavailable_check_exit_1(self) -> None:
        self.assertEqual(self.box.run("--repo", DEMO, "--strict").returncode, 1)

    def test_an_interpreter_reporting_another_version_is_unavailable(self) -> None:
        self.box.add_interpreter()
        proc = self.box.run("--repo", DEMO, STUB_VERSION="3.14.4")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = self.only_result()
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("reports 3.14.4, not 3.15", result["reason"])
        self.assertNotIn("interpreter -m venv", " ".join(self.box.calls()))

    def test_the_interpreter_is_found_on_path_when_the_system_bin_lacks_it(self) -> None:
        stub = self.box.add_interpreter(where="pathbin")
        proc = self.box.run("--repo", DEMO)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = self.only_result()
        self.assertEqual((result["status"], result["interpreter"]), ("passed", str(stub)))

    def test_the_system_bin_wins_over_path(self) -> None:
        system = self.box.add_interpreter(where="sysbin")
        self.box.add_interpreter(where="pathbin")
        self.box.run("--repo", DEMO)
        self.assertEqual(self.only_result()["interpreter"], str(system))

    def test_a_blocking_version_runs_on_request_and_is_labelled(self) -> None:
        self.box.add_interpreter(version="3.15")
        self.box.add_interpreter(version="3.14")
        proc = self.box.run("--repo", DEMO, "--python", "3.15", "--python", "3.14", STUB_VERSION="3.14.4")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        results = {r["python"]: r for r in self.box.last_summary()["results"]}
        self.assertEqual(results["3.14"]["class"], "blocking")
        self.assertEqual(results["3.14"]["status"], "passed")
        self.assertEqual(results["3.15"]["status"], "unavailable", "the 3.15 stub reports 3.14.4 here")

    def test_an_install_failure_skips_the_tests(self) -> None:
        self.box.add_interpreter()
        proc = self.box.run("--repo", DEMO, STUB_PIP_RC="1")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = self.only_result()
        self.assertEqual((result["status"], result["failed_phase"]), ("failed", "install"))
        self.assertEqual([s["phase"] for s in result["steps"]], ["venv", "install"])
        self.assertFalse(any(call.startswith("wrapper") for call in self.box.calls()), "no test may run after a failed install")

    def test_a_venv_failure_skips_install_and_tests(self) -> None:
        self.box.add_interpreter()
        proc = self.box.run("--repo", DEMO, STUB_VENV_RC="3")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = self.only_result()
        self.assertEqual((result["status"], result["failed_phase"]), ("failed", "venv"))
        self.assertIn("-m venv` exited 3", result["reason"])
        self.assertFalse(any(call.startswith(("venv-python", "wrapper")) for call in self.box.calls()))

    def test_every_test_step_runs_and_each_failure_is_named(self) -> None:
        self.box.add_interpreter()
        write(self.box.config, demo_config(test={"first": "exit 4", "second": "bash run_tests.bash"}))
        proc = self.box.run("--repo", DEMO)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = self.only_result()
        self.assertEqual([(s["name"], s["returncode"]) for s in result["steps"] if s["phase"] == "test"], [("first", 4), ("second", 0)])
        self.assertEqual(result["reason"], "test `first` exited 4")

    def test_the_child_environment(self) -> None:
        self.box.add_interpreter()
        proc = self.box.run("--repo", DEMO, PYTHONPATH=str(self.box.dir / "elsewhere"), DEMO_UNSET_ME="present", GIT_CEILING_DIRECTORIES="/outer")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        seen = self.box.env_seen()
        repo_tmp = str(self.box.root / DEMO / "tmp")
        self.assertEqual(seen["VIRTUAL_ENV"], str(self.box.venv))
        self.assertEqual(seen["PATH"].split(os.pathsep)[0], str(self.box.venv / "bin"))
        self.assertEqual(seen["python"], str(self.box.venv / "bin" / "python"), "`python` in a recipe is the venv's")
        self.assertEqual(seen["TMPDIR"], repo_tmp)
        self.assertEqual(seen["GIT_CEILING_DIRECTORIES"], os.pathsep.join([repo_tmp, "/outer"]))
        self.assertEqual(seen["PYTHONPATH"], "<unset>")
        self.assertEqual(seen["PYTHONHOME"], "<unset>")
        self.assertEqual(seen["DEMO_UNSET_ME"], "<unset>", "a recipe's env_unset names are removed")
        self.assertEqual(seen["PIP_DISABLE_PIP_VERSION_CHECK"], "1")
        self.assertEqual(seen["CWD"], str(self.box.checkout.resolve()))

    def test_a_run_changes_no_file_of_the_checkout(self) -> None:
        self.box.add_interpreter()
        before = snapshot(self.box.checkout)
        self.assertEqual(self.box.run("--repo", DEMO).returncode, 0)
        self.assertEqual(snapshot(self.box.checkout, skip_top=("tmp",)), before, "only the gitignored tmp/ may change")
        self.assertEqual(sorted(p.name for p in (self.box.checkout / "tmp").iterdir()), ["pyvenv"])

    def test_a_missing_checkout_is_unavailable(self) -> None:
        self.box.add_interpreter()
        proc = self.box.run("--repo", DEMO, "--checkout", str(self.box.dir / "gone"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = self.only_result()
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("no checkout at", result["reason"])
        self.assertEqual(self.box.calls(), [])

    def test_a_missing_primary_is_unavailable_and_never_created(self) -> None:
        self.box.add_interpreter()
        other = self.box.dir / "worktree"
        write(other / "run_tests.bash", WRAPPER, 0o755)
        shutil.rmtree(self.box.checkout)
        proc = self.box.run("--repo", DEMO, "--checkout", str(other))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("no primary checkout at", self.only_result()["reason"])
        self.assertFalse(self.box.checkout.exists(), "the helper never creates a checkout")


class VenvLifecycleTest(unittest.TestCase):
    """Reuse, --recreate, a stale venv, and the two paths that are never removed."""

    def setUp(self) -> None:
        self.box = Sandbox(self)
        self.box.add_interpreter()

    def venv_builds(self) -> int:
        return sum(1 for call in self.box.calls() if call.startswith("interpreter -m venv"))

    def last_result(self) -> dict:
        return self.box.last_summary()["results"][0]

    def test_a_second_run_reuses_the_venv(self) -> None:
        self.assertEqual(self.box.run("--repo", DEMO).returncode, 0)
        self.assertEqual(self.box.run("--repo", DEMO).returncode, 0)
        self.assertEqual(self.venv_builds(), 1)
        self.assertEqual(len(self.box.summaries()), 2, "each run gets its own run directory")
        self.assertEqual(self.last_result()["venv_action"], "reused")

    def test_recreate_rebuilds_the_venv(self) -> None:
        self.assertEqual(self.box.run("--repo", DEMO).returncode, 0)
        write(self.box.venv / "marker", "old venv\n")
        self.assertEqual(self.box.run("--repo", DEMO, "--recreate").returncode, 0)
        self.assertFalse((self.box.venv / "marker").exists())
        self.assertEqual(self.venv_builds(), 2)
        self.assertEqual(self.last_result()["venv_action"], "recreated")

    def test_a_stale_venv_is_rebuilt(self) -> None:
        self.assertEqual(self.box.run("--repo", DEMO).returncode, 0)
        write(self.box.venv / "bin" / "python", STALE_VENV_PYTHON, 0o755)
        self.assertEqual(self.box.run("--repo", DEMO).returncode, 0)
        self.assertEqual(self.venv_builds(), 2)
        self.assertEqual(self.last_result()["venv_action"], "recreated")

    def test_a_directory_without_pyvenv_cfg_is_never_removed(self) -> None:
        keep = write(self.box.venv / "keep.txt", "not a venv\n")
        for extra in ((), ("--recreate",)):
            with self.subTest(args=extra):
                proc = self.box.run("--repo", DEMO, *extra)
                self.assertEqual(proc.returncode, 0, proc.stderr)
                result = self.last_result()
                self.assertEqual((result["status"], result["failed_phase"]), ("failed", "venv"))
                self.assertIn("holds no pyvenv.cfg", result["reason"])
                self.assertTrue(keep.is_file())
        self.assertEqual(self.venv_builds(), 0)

    def test_a_symlink_is_never_used_or_removed(self) -> None:
        target = self.box.dir / "elsewhere"
        write(target / "pyvenv.cfg", "home = elsewhere\n")
        self.box.venv.parent.mkdir(parents=True)
        self.box.venv.symlink_to(target)
        proc = self.box.run("--repo", DEMO, "--recreate")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("is a symlink", self.last_result()["reason"])
        self.assertTrue((target / "pyvenv.cfg").is_file())
        self.assertTrue(self.box.venv.is_symlink())

    def test_a_venv_another_run_holds_is_unavailable(self) -> None:
        lock = self.box.root / DEMO / "tmp" / "pyvenv" / "py3.15.lock"
        lock.parent.mkdir(parents=True)
        with lock.open("a", encoding="utf-8") as held:
            fcntl.flock(held.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            proc = self.box.run("--repo", DEMO)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = self.last_result()
        self.assertEqual(result["status"], "unavailable")
        self.assertIn(f"another run holds {lock}", result["reason"])
        self.assertEqual(self.venv_builds(), 0)
        self.assertEqual(self.box.run("--repo", DEMO).returncode, 0)
        self.assertEqual(self.last_result()["status"], "passed", "the lock is free once its holder lets go")


class NothingRunsTest(unittest.TestCase):
    """--dry-run and --list run nothing and write nothing."""

    def setUp(self) -> None:
        self.box = Sandbox(self)

    def assert_untouched(self, before: dict[str, str]) -> None:
        self.assertEqual(self.box.calls(), [], "no stub may be invoked")
        self.assertEqual(snapshot(self.box.root), before, "no file or directory may be written")

    def test_dry_run_runs_and_writes_nothing(self) -> None:
        self.box.add_interpreter()
        before = snapshot(self.box.root)
        proc = self.box.run("--repo", DEMO, "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertRegex(proc.stdout, r"(?m)^PLAN +juniper-demo 3\.15 \(informational\)$")
        self.assertIn("bash run_tests.bash", proc.stdout)
        self.assertIn("dry run: nothing was run or written", proc.stdout)
        self.assert_untouched(before)

    def test_dry_run_reports_an_unavailable_interpreter_and_strict_exits_1(self) -> None:
        before = snapshot(self.box.root)
        proc = self.box.run("--repo", DEMO, "--dry-run")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertRegex(proc.stdout, r"(?m)^UNAVAILABLE +juniper-demo 3\.15")
        self.assertEqual(self.box.run("--repo", DEMO, "--dry-run", "--strict").returncode, 1)
        self.assert_untouched(before)

    def test_list_runs_and_writes_nothing(self) -> None:
        self.box.add_interpreter()
        before = snapshot(self.box.root)
        proc = self.box.run("--list")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertRegex(proc.stdout, r"(?m)^informational +3\.15$")
        self.assertRegex(proc.stdout, r"(?m)^blocking +3\.12 3\.13 3\.14$")
        self.assertIn(f"python3.15     {self.box.sysbin / 'python3.15'}", proc.stdout)
        self.assertIn("unavailable", proc.stdout, "the stub dirs hold no python3.12")
        self.assert_untouched(before)


class PreCommitTest(unittest.TestCase):
    """The helper is never wired into pre-commit (owner ruling, 2026-11-14): its checks block nothing."""

    @staticmethod
    def hooks_naming_the_helper(doc: dict) -> list[str]:
        found: list[str] = []
        for repo in doc.get("repos") or []:
            for hook in repo.get("hooks") or []:
                fields = " ".join(str(hook.get(key, "")) for key in ("id", "name", "entry", "files", "args"))
                if any(name in fields for name in HELPER_NAMES):
                    found.append(str(hook.get("id")))
        return found

    def test_pre_commit_config_does_not_run_the_helper(self) -> None:
        doc = yaml.safe_load(PRE_COMMIT_CONFIG.read_text(encoding="utf-8"))
        self.assertTrue(doc.get("repos"), "the scan found no hooks to check")
        self.assertEqual(self.hooks_naming_the_helper(doc), [])

    def test_the_scan_bites_on_a_hook_that_runs_it(self) -> None:
        planted = {"repos": [{"repo": "local", "hooks": [{"id": "pyver", "name": "versions", "entry": "python3 util/python_version_check.py --all", "language": "system"}]}]}
        self.assertEqual(self.hooks_naming_the_helper(planted), ["pyver"])
        planted = {"repos": [{"repo": "local", "hooks": [{"id": "cfg", "entry": "true", "files": "^conf/python_versions.yaml$"}]}]}
        self.assertEqual(self.hooks_naming_the_helper(planted), ["cfg"])


if __name__ == "__main__":
    unittest.main()
