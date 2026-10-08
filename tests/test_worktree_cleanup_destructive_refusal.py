"""Phase 4 must not escalate past git's two refusals, or delete snapshot files.

``util/worktree_cleanup.bash`` used to turn a failed ``git worktree remove`` into
``--force`` and a failed ``git branch -d`` into ``-D``. Those are git's only two
refusals (uncommitted or untracked work, and commits merged nowhere). A
gitignored ``cascor-snapshots/*.h5`` does not trip either refusal, so the
snapshot guard has to fire first.

The cases below drive ``phase_4_cleanup`` through ``parse_args`` on a fixture
repo. They do not touch the host checkout. Remote deletion is skipped so the
tests never need ``gh``.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from tests.redacted_env import RedactedEnv

SCRIPT_PATH = Path(__file__).resolve().parent.parent / "util" / "worktree_cleanup.bash"
SCRIPT_TIMEOUT_SECONDS = 30


def _run_git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        timeout=SCRIPT_TIMEOUT_SECONDS,
        check=check,
    )


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _run_git(path, "init", "-q", "-b", "main")
    _run_git(path, "config", "user.email", "tests@example.invalid")
    _run_git(path, "config", "user.name", "Test User")
    _run_git(path, "config", "commit.gpgsign", "false")
    (path / "README.md").write_text("# test\n")
    _run_git(path, "add", "README.md")
    _run_git(path, "commit", "-q", "-m", "initial")
    _run_git(path, "update-ref", "refs/remotes/origin/main", "HEAD")


def _prepare(tmp: Path, branch: str, *, ignore_snapshots: bool = False) -> tuple[Path, Path]:
    """Return ``(main_repo, old_worktree)`` with ``branch`` pushed to a bare origin.

    The branch matches its upstream, so a clean tree is one ``git branch -d``
    will accept. ``ignore_snapshots`` commits the ignore on main first, so the
    feature branch still matches that upstream.
    """
    main_repo = tmp / "main-repo"
    old_worktree = tmp / "old-worktree"
    remote = tmp / "remote.git"
    _init_repo(main_repo)
    if ignore_snapshots:
        (main_repo / ".gitignore").write_text("cascor-snapshots/\n")
        _run_git(main_repo, "add", ".gitignore")
        _run_git(main_repo, "commit", "-q", "-m", "ignore cascor snapshots")
        _run_git(main_repo, "update-ref", "refs/remotes/origin/main", "HEAD")
    _run_git(main_repo, "clone", "--bare", "-q", str(main_repo), str(remote))
    _run_git(main_repo, "remote", "add", "origin", str(remote))
    _run_git(main_repo, "checkout", "-q", "-b", branch)
    _run_git(main_repo, "push", "-q", "-u", "origin", branch)
    _run_git(main_repo, "checkout", "-q", "main")
    _run_git(main_repo, "worktree", "add", "-q", str(old_worktree), branch)
    return main_repo, old_worktree


def _run_phase4(
    *,
    main_repo: Path,
    old_worktree: Path,
    old_branch: str,
    force: bool = False,
    discard_snapshots: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Source the script (skip ``main``) and run phase 4 through ``parse_args``."""
    driver = r"""
set -euo pipefail
export JUNIPER_ML_MAIN_REPO="$1"
SCRIPT_PATH="$2"
# shellcheck disable=SC1090
source <(sed '/^main "/d' "${SCRIPT_PATH}")
args=(--skip-remote-delete --old-worktree "$3" --old-branch "$4")
if [[ "$5" == "force" ]]; then
    args+=(--force-destructive)
fi
parse_args "${args[@]}"
phase_4_cleanup
"""
    env = RedactedEnv(os.environ)
    if discard_snapshots:
        env["WORKTREE_CLEANUP_DISCARD_SNAPSHOTS"] = "1"
    else:
        env.pop("WORKTREE_CLEANUP_DISCARD_SNAPSHOTS", None)
    return subprocess.run(
        [
            "bash",
            "-c",
            driver,
            "phase4-refusal-driver",
            str(main_repo),
            str(SCRIPT_PATH),
            str(old_worktree),
            old_branch,
            "force" if force else "keep",
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=SCRIPT_TIMEOUT_SECONDS,
    )


def _branch_exists(repo: Path, branch: str) -> bool:
    result = _run_git(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}", check=False)
    return result.returncode == 0


class TestWorktreeRemoveRefusal(unittest.TestCase):
    """A dirty tree is kept unless ``--force-destructive`` is actually passed."""

    def test_untracked_file_is_kept_when_remove_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            branch = "feature/dirty-keep"
            main_repo, old_worktree = _prepare(root, branch)
            kept = old_worktree / "WIP.txt"
            kept.write_text("untracked\n")

            result = _run_phase4(main_repo=main_repo, old_worktree=old_worktree, old_branch=branch)

            self.assertEqual(result.returncode, 1, msg=result.stderr)
            self.assertIn("git REFUSED to remove", result.stderr)
            self.assertIn("Nothing has been deleted", result.stderr)
            self.assertIn("WIP.txt", result.stderr)
            self.assertNotIn("worktree remove --force", result.stderr)
            self.assertNotIn("branch -D", result.stderr)
            self.assertTrue(old_worktree.is_dir())
            self.assertEqual(kept.read_text(), "untracked\n")
            self.assertTrue(_branch_exists(main_repo, branch))

    def test_force_destructive_deletes_the_untracked_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            branch = "feature/dirty-force"
            main_repo, old_worktree = _prepare(root, branch)
            (old_worktree / "WIP.txt").write_text("untracked\n")

            result = _run_phase4(
                main_repo=main_repo,
                old_worktree=old_worktree,
                old_branch=branch,
                force=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("--force-destructive given, forcing", result.stderr)
            self.assertIn("worktree remove --force", result.stderr)
            self.assertFalse(old_worktree.exists())
            self.assertFalse(_branch_exists(main_repo, branch))


class TestBranchDeleteRefusal(unittest.TestCase):
    """A commit that is merged nowhere survives unless ``--force-destructive`` is passed."""

    def _unique_commit(self, old_worktree: Path) -> str:
        (old_worktree / "only-here.txt").write_text("not on any other branch\n")
        _run_git(old_worktree, "add", "only-here.txt")
        _run_git(old_worktree, "commit", "-q", "-m", "unique commit that must survive")
        return _run_git(old_worktree, "rev-parse", "HEAD").stdout.strip()

    def test_unmerged_commit_is_kept_when_branch_delete_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            branch = "feature/unmerged-keep"
            main_repo, old_worktree = _prepare(root, branch)
            tip = self._unique_commit(old_worktree)

            result = _run_phase4(main_repo=main_repo, old_worktree=old_worktree, old_branch=branch)

            self.assertEqual(result.returncode, 1, msg=result.stderr)
            self.assertIn("holds commits merged nowhere", result.stderr)
            self.assertIn("Nothing has been deleted", result.stderr)
            # git's own hint quotes `branch -D`. The script must not have run it.
            self.assertNotRegex(result.stderr, r"Running: .*branch -D")
            # The checkout was clean, so removing the worktree is allowed.
            # The commits are what must remain.
            self.assertFalse(old_worktree.exists())
            self.assertTrue(_branch_exists(main_repo, branch))
            self.assertEqual(_run_git(main_repo, "rev-parse", branch).stdout.strip(), tip)

    def test_force_destructive_drops_the_unmerged_branch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            branch = "feature/unmerged-force"
            main_repo, old_worktree = _prepare(root, branch)
            tip = self._unique_commit(old_worktree)

            result = _run_phase4(
                main_repo=main_repo,
                old_worktree=old_worktree,
                old_branch=branch,
                force=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("branch -D", result.stderr)
            self.assertFalse(_branch_exists(main_repo, branch))
            self.assertNotEqual(
                _run_git(main_repo, "merge-base", "--is-ancestor", tip, "main", check=False).returncode,
                0,
            )


class TestSnapshotGuard(unittest.TestCase):
    """A gitignored ``.h5`` is deleted by ``worktree remove`` with no ``--force``.

    The guard has to refuse before that remove. ``--force-destructive`` does
    not bypass it; only ``WORKTREE_CLEANUP_DISCARD_SNAPSHOTS=1`` does.
    """

    def test_help_names_the_force_flag(self) -> None:
        result = subprocess.run(
            ["bash", str(SCRIPT_PATH), "--help"],
            capture_output=True,
            text=True,
            timeout=SCRIPT_TIMEOUT_SECONDS,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--force-destructive", result.stdout)
        self.assertIn("REFUSES", result.stdout)

    def test_snapshot_h5_is_kept_even_if_force_destructive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            branch = "feature/snapshot-keep"
            main_repo, old_worktree = _prepare(root, branch, ignore_snapshots=True)
            snap = old_worktree / "cascor-snapshots" / "model.h5"
            snap.parent.mkdir()
            snap.write_bytes(b"not-a-real-hdf5")

            result = _run_phase4(
                main_repo=main_repo,
                old_worktree=old_worktree,
                old_branch=branch,
                force=True,
            )

            self.assertEqual(result.returncode, 1, msg=result.stderr)
            self.assertIn("snapshot .h5", result.stderr)
            self.assertIn("cascor-snapshots/", result.stderr)
            self.assertNotIn("Removing worktree:", result.stderr)
            self.assertNotIn("worktree remove --force", result.stderr)
            self.assertEqual(snap.read_bytes(), b"not-a-real-hdf5")
            self.assertTrue(_branch_exists(main_repo, branch))

    def test_discard_snapshots_removes_the_h5_and_the_worktree(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            branch = "feature/snapshot-discard"
            main_repo, old_worktree = _prepare(root, branch, ignore_snapshots=True)
            snap = old_worktree / "cascor-snapshots" / "model.h5"
            snap.parent.mkdir()
            snap.write_bytes(b"not-a-real-hdf5")

            result = _run_phase4(
                main_repo=main_repo,
                old_worktree=old_worktree,
                old_branch=branch,
                discard_snapshots=True,
            )

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertIn("WORKTREE_CLEANUP_DISCARD_SNAPSHOTS=1", result.stderr)
            self.assertIn("Discarding", result.stderr)
            self.assertFalse(old_worktree.exists())
            self.assertFalse(_branch_exists(main_repo, branch))

    def test_ignored_non_h5_does_not_trip_the_snapshot_guard(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            branch = "feature/snapshot-txt"
            main_repo, old_worktree = _prepare(root, branch, ignore_snapshots=True)
            note = old_worktree / "cascor-snapshots" / "notes.txt"
            note.parent.mkdir()
            note.write_text("not a snapshot\n")

            result = _run_phase4(main_repo=main_repo, old_worktree=old_worktree, old_branch=branch)

            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertNotIn("snapshot .h5", result.stderr)
            self.assertFalse(old_worktree.exists())
            self.assertFalse(_branch_exists(main_repo, branch))
