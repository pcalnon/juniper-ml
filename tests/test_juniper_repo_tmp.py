#!/usr/bin/env python3
"""Hermetic gate for util/juniper_repo_tmp.bash (the 2026-10-26 repo tmp/ rule).

Project:     Juniper
Sub-Project: juniper-ml
Application: harness tooling regression tests
Author:      Paul Calnon
License:     MIT License

``notes/JUNIPER_2026-10-26_JUNIPER-ECOSYSTEM_REPO-TMP-DIRECTORY-CONVENTION.md``: no file is ever written
under the system temp directory; each repo writes to its own gitignored ``tmp/``. Scripts that keep state
another process must find (the isolated stack's run dir, the reaper's protected root, the experiment
stack's lock root) name it with ``juniper_repo_tmp``. The answer must be the PRIMARY checkout's ``tmp/``
-- a linked worktree is removed when its task ends -- and a directory in no checkout must fail rather
than fall back to anything.

How the suite stays hermetic: every case builds temp git repos and runs the helper with every ``GIT_*``
variable scrubbed (the session's ``GIT_CONFIG_COUNT`` signing guard included), ``GIT_CONFIG_NOSYSTEM=1``,
an isolated ``GIT_CONFIG_GLOBAL`` and a temp ``HOME``. ``GIT_CEILING_DIRECTORIES`` stops discovery at the
case's temp directory, which may itself sit inside a checkout's ``tmp/``.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # nosec B404 - drives the helper and real git on temp repos
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "util" / "juniper_repo_tmp.bash"
TIMEOUT_SECONDS = 60
GITCONFIG = "[init]\n\tdefaultBranch = main\n[user]\n\tname = Repo Tmp Test\n\temail = repo-tmp-test@example.invalid\n[commit]\n\tgpgsign = false\n"


def setUpModule() -> None:
    if shutil.which("git") is None:
        raise unittest.SkipTest("git not installed")


class _Fixture(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        (self.base / "home").mkdir()
        gitconfig = self.base / "gitconfig"
        gitconfig.write_text(GITCONFIG, encoding="utf-8")
        self.env = RedactedEnv({k: v for k, v in os.environ.items() if not k.startswith("GIT_") and k != "GIT"})
        self.env.update(HOME=str(self.base / "home"), GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=str(gitconfig), GIT_TERMINAL_PROMPT="0", GIT_CEILING_DIRECTORIES=str(self.base))

    def git(self, cwd: Path, *args: str) -> None:
        subprocess.run(["git", "-C", str(cwd), *args], env=self.env, check=True, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)

    def make_repo(self, name: str, *, commit: bool = False) -> Path:
        repo = self.base / name
        (repo / "sub" / "deeper").mkdir(parents=True)
        self.git(repo, "init", "-q")
        if commit:
            self.git(repo, "commit", "-q", "--allow-empty", "-m", "init")
        return repo

    def run_helper(self, *args: str, cwd: Path | None = None, **env: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(["bash", str(SCRIPT_PATH), *args], cwd=cwd or self.base, env=RedactedEnv(self.env, **env), capture_output=True, text=True, timeout=TIMEOUT_SECONDS)

    def source_and_call(self, function: str, arg: str) -> subprocess.CompletedProcess[str]:
        script = 'set -u; before="$-"; source "$1"; "$2" "$3"; status=$?; [ "$-" = "$before" ] || echo "OPTIONS CHANGED: $before -> $-" >&2; exit "$status"'
        return subprocess.run(["bash", "-c", script, "probe", str(SCRIPT_PATH), function, arg], cwd=self.base, env=self.env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)

    def assert_prints(self, proc: subprocess.CompletedProcess[str], expected: Path) -> None:
        self.assertEqual(proc.returncode, 0, f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}")
        self.assertEqual(Path(proc.stdout.strip()).resolve(), expected.resolve())
        self.assertEqual(proc.stdout.count("\n"), 1)


class TestResolution(_Fixture):
    def test_a_primary_checkout_resolves_to_its_own_tmp_and_creates_it(self) -> None:
        repo = self.make_repo("repo")
        self.assertFalse((repo / "tmp").exists())
        self.assert_prints(self.run_helper(str(repo / "sub" / "deeper")), repo / "tmp")
        self.assertTrue((repo / "tmp").is_dir())

    def test_a_linked_worktree_resolves_to_its_primary(self) -> None:
        repo = self.make_repo("repo", commit=True)
        worktree = self.base / "wt"
        self.git(repo, "worktree", "add", "-q", str(worktree))
        (worktree / "nested").mkdir()
        self.assert_prints(self.run_helper(str(worktree / "nested")), repo / "tmp")
        self.assertTrue((repo / "tmp").is_dir())
        self.assertFalse((worktree / "tmp").exists(), "the worktree's own tmp/ must not be created")

    def test_a_directory_in_no_checkout_fails_and_creates_nothing(self) -> None:
        plain = self.base / "plain" / "sub"
        plain.mkdir(parents=True)
        proc = self.run_helper(str(plain))
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")
        self.assertIn("is not in a git checkout", proc.stderr)
        self.assertEqual(sorted(p.name for p in (self.base / "plain").iterdir()), ["sub"])

    def test_a_missing_directory_fails(self) -> None:
        proc = self.run_helper(str(self.base / "nowhere"))
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")

    def test_dir_defaults_to_the_working_directory(self) -> None:
        repo = self.make_repo("repo")
        self.assert_prints(self.run_helper(cwd=repo / "sub"), repo / "tmp")

    def test_git_dir_in_the_environment_is_ignored(self) -> None:
        repo = self.make_repo("repo")
        other = self.make_repo("other")
        proc = self.run_helper(str(repo / "sub"), GIT_DIR=str(other / ".git"), GIT_WORK_TREE=str(other))
        self.assert_prints(proc, repo / "tmp")
        self.assertFalse((other / "tmp").exists())

    def test_a_separate_git_dir_checkout_uses_its_top_level(self) -> None:
        worktree = self.base / "separate"
        worktree.mkdir()
        self.git(self.base, "init", "-q", f"--separate-git-dir={self.base / 'store.git'}", str(worktree))
        self.assert_prints(self.run_helper(str(worktree)), worktree / "tmp")

    def test_a_tmp_that_cannot_be_created_fails(self) -> None:
        repo = self.make_repo("repo")
        (repo / "tmp").write_text("a file, not a directory\n", encoding="utf-8")
        proc = self.run_helper(str(repo))
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")
        self.assertIn("cannot create", proc.stderr)

    def test_a_missing_git_fails(self) -> None:
        repo = self.make_repo("repo")
        bin_dir = self.base / "bin"
        bin_dir.mkdir()
        for tool in ("mkdir", "dirname"):
            found = shutil.which(tool)
            if found:
                (bin_dir / tool).symlink_to(found)
        proc = subprocess.run([shutil.which("bash") or "bash", str(SCRIPT_PATH), str(repo)], cwd=self.base, env=RedactedEnv(self.env, PATH=str(bin_dir)), capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout, "")
        self.assertFalse((repo / "tmp").exists())


class TestSourcedForm(_Fixture):
    def test_sourcing_defines_both_functions_and_changes_no_option(self) -> None:
        repo = self.make_repo("repo")
        self.assert_prints(self.source_and_call("juniper_repo_tmp", str(repo / "sub")), repo / "tmp")
        proc = self.source_and_call("juniper_repo_primary", str(repo / "sub"))
        self.assert_prints(proc, repo)
        self.assertEqual(proc.stderr, "")

    def test_juniper_repo_primary_creates_nothing(self) -> None:
        repo = self.make_repo("repo")
        self.assert_prints(self.source_and_call("juniper_repo_primary", str(repo)), repo)
        self.assertFalse((repo / "tmp").exists())

    def test_a_failure_returns_1_to_the_caller_without_exiting_it(self) -> None:
        plain = self.base / "plain"
        plain.mkdir()
        proc = self.source_and_call("juniper_repo_tmp", str(plain))
        self.assertEqual(proc.returncode, 1)
        self.assertNotIn("OPTIONS CHANGED", proc.stderr)


class TestUsage(_Fixture):
    def test_help_exits_0(self) -> None:
        for flag in ("-h", "--help"):
            with self.subTest(flag=flag):
                proc = self.run_helper(flag)
                self.assertEqual(proc.returncode, 0)
                self.assertIn("usage:", proc.stdout)

    def test_two_arguments_exit_2(self) -> None:
        proc = self.run_helper("a", "b")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(proc.stdout, "")


class TestThisCheckout(unittest.TestCase):
    def test_this_checkout_resolves_to_its_primary_tmp(self) -> None:
        env = RedactedEnv({k: v for k, v in os.environ.items() if not k.startswith("GIT_")})
        common = subprocess.run(["git", "-C", str(REPO_ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"], env=env, capture_output=True, text=True, check=True, timeout=TIMEOUT_SECONDS).stdout.strip()
        primary = Path(common).parent if common.endswith("/.git") else REPO_ROOT
        proc = subprocess.run(["bash", str(SCRIPT_PATH), str(REPO_ROOT / "util")], env=env, capture_output=True, text=True, timeout=TIMEOUT_SECONDS)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(Path(proc.stdout.strip()).resolve(), (primary / "tmp").resolve())

    def test_the_tmp_directory_is_ignored_and_root_anchored(self) -> None:
        lines = [line.strip() for line in (REPO_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()]
        self.assertIn("/tmp/", lines)  # tmp-path-literal: allow -- the .gitignore rule itself
        self.assertNotIn("tmp/", lines, "an unanchored rule would also ignore a nested tmp/ package or fixture directory")


if __name__ == "__main__":
    unittest.main()
