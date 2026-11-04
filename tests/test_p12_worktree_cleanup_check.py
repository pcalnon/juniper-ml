"""Hermetic gate for util/ad-hoc/2026-11-04_p12_worktree_cleanup_check.bash.

The script deletes worktrees. On git 2.43, `git worktree remove` without
--force still deletes ignored files, and when status.showUntrackedFiles=no it
also deletes untracked files. An empty archive directory must not count as a
copy of tmp/. These tests stub gh and never call the network.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "util" / "ad-hoc" / "2026-11-04_p12_worktree_cleanup_check.bash"
SCRIPT_TIMEOUT_SECONDS = 30

# First TARGETS row. The other five paths stay absent.
WT_NAME = "juniper-canopy--fix--declared-param-staging-735-736--20261026-1649--da08414f"
ARCHIVE_NAME = "canopy--declared-param-staging-735-736"

GH_STUB = """#!/bin/sh
if [ "${P12_GH_RC:-0}" != "0" ]; then
    exit "$P12_GH_RC"
fi
printf '%s\\n' "${P12_GH_STDOUT:-#9 MERGED}"
"""

GIT_WRAPPER = """#!/usr/bin/env python3
import os
import sys

real = os.environ["P12_REAL_GIT"]
argv = sys.argv[1:]
if os.environ.get("P12_FAIL_GIT_FETCH") == "1" and "fetch" in argv:
    sys.stderr.write("fatal: simulated fetch failure\\n")
    raise SystemExit(128)
if os.environ.get("P12_FAIL_GIT_LOG") == "1" and "log" in argv:
    sys.stderr.write("fatal: simulated log failure\\n")
    raise SystemExit(128)
os.execv(real, [real, *argv])
"""


def _run_git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=SCRIPT_TIMEOUT_SECONDS,
        check=True,
    )
    return result.stdout.strip()


class P12WorktreeCleanupCheckTest(unittest.TestCase):
    def _env(self, home: Path, bin_dir: Path, **extra: str) -> RedactedEnv:
        return RedactedEnv(
            os.environ,
            HOME=str(home),
            PATH=str(bin_dir) + os.pathsep + os.environ.get("PATH", ""),
            **extra,
        )

    def _write_executable(self, path: Path, text: str) -> None:
        path.write_text(text)
        path.chmod(path.stat().st_mode | stat.S_IEXEC)

    def _layout(self, root: Path) -> tuple[Path, Path, Path, Path]:
        home = root / "home"
        worktree = home / "Development" / "python" / "Juniper" / "worktrees" / WT_NAME
        archive = home / "Development" / "python" / "Juniper" / "juniper-ml" / "tmp" / "worktree-cleanup-2026-11-03-p12" / ARCHIVE_NAME
        archive.mkdir(parents=True)
        main = root / "repo"
        origin = root / "origin.git"
        _run_git(root, "init", "-q", "--bare", "-b", "main", str(origin))
        main.mkdir()
        _run_git(main, "init", "-q", "-b", "main")
        _run_git(main, "config", "user.email", "tests@example.invalid")
        _run_git(main, "config", "user.name", "Test User")
        _run_git(main, "config", "commit.gpgsign", "false")
        (main / ".gitignore").write_text("tmp/\n*.secret\n")
        (main / "README.md").write_text("# test\n")
        _run_git(main, "add", ".gitignore", "README.md")
        _run_git(main, "commit", "-q", "-m", "initial")
        _run_git(main, "remote", "add", "origin", str(origin))
        _run_git(main, "push", "-q", "origin", "main")
        _run_git(main, "worktree", "add", "-q", "-b", "p12-cleanup", str(worktree), "main")
        return home, worktree, archive, main

    def _bin(self, root: Path) -> Path:
        bin_dir = root / "bin"
        bin_dir.mkdir()
        self._write_executable(bin_dir / "gh", GH_STUB)
        return bin_dir

    def _run(self, home: Path, bin_dir: Path, *args: str, **extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["bash", str(SCRIPT), *args],
            capture_output=True,
            text=True,
            env=self._env(home, bin_dir, **extra),
            timeout=SCRIPT_TIMEOUT_SECONDS,
            check=False,
        )

    def test_ignored_secret_outside_tmp_is_not_removed_even_when_pr_is_merged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home, worktree, archive, _main = self._layout(root)
            (archive / "notes.txt").write_text("archived\n")
            (worktree / "local.secret").write_text("decrypted secret\n")
            result = self._run(home, self._bin(root), "--remove")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("ignored outside archived tmp/: YES", result.stdout)
            self.assertIn("-> KEEP", result.stdout)
            self.assertNotIn("\n   removed", result.stdout)
            self.assertEqual((worktree / "local.secret").read_text(), "decrypted secret\n")

    def test_show_untracked_files_no_cannot_hide_untracked_wip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home, worktree, archive, main = self._layout(root)
            (archive / "notes.txt").write_text("archived\n")
            (worktree / "precious.txt").write_text("untracked WIP\n")
            _run_git(worktree, "config", "status.showUntrackedFiles", "no")
            _run_git(main, "config", "status.showUntrackedFiles", "no")
            self.assertEqual(_run_git(worktree, "status", "--porcelain"), "")
            result = self._run(home, self._bin(root), "--remove")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("dirty:   YES", result.stdout)
            self.assertIn("-> KEEP", result.stdout)
            self.assertNotIn("\n   removed", result.stdout)
            self.assertEqual((worktree / "precious.txt").read_text(), "untracked WIP\n")

    def test_empty_archive_does_not_remove_tmp_payload(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home, worktree, _archive, _main = self._layout(root)
            (worktree / "tmp").mkdir()
            (worktree / "tmp" / "only-copy.txt").write_text("not archived\n")
            result = self._run(home, self._bin(root), "--remove")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("tmp/ has files but the archive has none", result.stdout)
            self.assertIn("-> KEEP", result.stdout)
            self.assertEqual((worktree / "tmp" / "only-copy.txt").read_text(), "not archived\n")

    def test_open_pr_beside_merged_pr_is_not_removable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home, worktree, archive, main = self._layout(root)
            (archive / "notes.txt").write_text("archived\n")
            (worktree / "README.md").write_text("# follow-up\n")
            _run_git(worktree, "add", "README.md")
            _run_git(worktree, "commit", "-q", "-m", "follow-up, not merged")
            result = self._run(home, self._bin(root), "--remove", P12_GH_STDOUT="#1 MERGED, #2 OPEN")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("-> KEEP", result.stdout)
            self.assertNotIn("\n   removed", result.stdout)
            self.assertTrue(worktree.is_dir())
            self.assertIn("follow-up, not merged", _run_git(main, "log", "-1", "--format=%s", "p12-cleanup"))

    def test_archived_tmp_only_tree_is_removed_and_the_branch_is_kept(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home, worktree, archive, main = self._layout(root)
            (worktree / "tmp").mkdir()
            (worktree / "tmp" / "notes.txt").write_text("session notes\n")
            (archive / "notes.txt").write_text("session notes\n")
            result = self._run(home, self._bin(root), "--remove")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("-> REMOVABLE", result.stdout)
            self.assertIn("\n   removed", result.stdout)
            self.assertFalse(worktree.exists())
            _run_git(main, "show-ref", "--verify", "--quiet", "refs/heads/p12-cleanup")

    def test_squash_merged_unique_commits_are_removed_when_no_pr_is_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home, worktree, archive, main = self._layout(root)
            (archive / "notes.txt").write_text("archived\n")
            (worktree / "README.md").write_text("# squashed\n")
            _run_git(worktree, "add", "README.md")
            _run_git(worktree, "commit", "-q", "-m", "already squash-merged")
            result = self._run(home, self._bin(root), "--remove", P12_GH_STDOUT="#9 MERGED")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("-> REMOVABLE", result.stdout)
            self.assertIn("\n   removed", result.stdout)
            self.assertFalse(worktree.exists())
            self.assertIn("already squash-merged", _run_git(main, "log", "-1", "--format=%s", "p12-cleanup"))

    def test_failed_fetch_is_not_treated_as_no_unique_commits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home, worktree, archive, _main = self._layout(root)
            (archive / "notes.txt").write_text("archived\n")
            bin_dir = self._bin(root)
            self._write_executable(bin_dir / "git", GIT_WRAPPER)
            real_git = shutil.which("git")
            self.assertIsNotNone(real_git)
            result = self._run(home, bin_dir, "--remove", P12_REAL_GIT=real_git, P12_FAIL_GIT_FETCH="1")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("KEEP: fetch of origin/main failed", result.stdout)
            self.assertNotIn("\n   removed", result.stdout)
            self.assertTrue(worktree.is_dir())

    def test_failed_origin_comparison_is_not_treated_as_no_unique_commits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            home, worktree, archive, main = self._layout(root)
            (archive / "notes.txt").write_text("archived\n")
            (worktree / "README.md").write_text("# unique\n")
            _run_git(worktree, "add", "README.md")
            _run_git(worktree, "commit", "-q", "-m", "unique, not on origin/main")
            bin_dir = self._bin(root)
            self._write_executable(bin_dir / "git", GIT_WRAPPER)
            real_git = shutil.which("git")
            self.assertIsNotNone(real_git)
            result = self._run(home, bin_dir, "--remove", P12_REAL_GIT=real_git, P12_FAIL_GIT_LOG="1")
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("KEEP: cannot resolve origin/main..HEAD", result.stdout)
            self.assertNotIn("\n   removed", result.stdout)
            self.assertTrue(worktree.is_dir())
            self.assertIn("unique, not on origin/main", _run_git(main, "log", "-1", "--format=%s", "p12-cleanup"))
