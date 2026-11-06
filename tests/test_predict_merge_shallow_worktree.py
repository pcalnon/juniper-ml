"""Shallow-graft edges for a predict_merge scratch that borrows a linked worktree.

``tests/test_predict_merge.py`` copies ``.git/shallow`` when the invoking checkout is a
normal repository, so ``.git`` is a directory. A linked worktree's ``.git`` is a file.
The graft lives in the common directory, and ``--git-path shallow`` is what names it.
Reading ``<worktree>/.git/shallow`` finds nothing, the scratch is not shallow, and a
behind-main PR whose boundary parent was never fetched is reported ``CONFLICT``.

A source git still calls shallow, whose graft path is not a file, is refused. Continuing
would merge without the graft and report that same false conflict.

Each test drives ``simulate_merge`` on a synthetic repo. No network, no ``gh``, no
``pre-commit``. Production ``util/fleet_triage/predict_merge.py`` is unchanged.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from fleet_triage import predict_merge as pm  # noqa: E402  (path-invoked util import)

GIT_TIMEOUT = 60


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    cp = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
    )
    if check and cp.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed ({cp.returncode}): {cp.stderr.strip()}")
    return cp


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q", "-b", "main")
    _git(path, "config", "user.email", "tests@example.invalid")
    _git(path, "config", "user.name", "Fleet Tests")
    _git(path, "config", "commit.gpgsign", "false")
    _git(path, "config", "tag.gpgsign", "false")


def _write(repo: Path, rel: str, content: str) -> None:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _commit(repo: Path, msg: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


def _publish(repo: Path, name: str) -> None:
    _git(repo, "update-ref", f"refs/remotes/origin/{name}", f"refs/heads/{name}")


def _origin_only(repo: Path, branch: str, start: str, filename: str, content: str) -> None:
    """Commit ``filename`` on ``branch`` at ``start``, publish ``origin/<branch>``, and delete the local branch."""
    _git(repo, "checkout", "-q", "-b", branch, start)
    _write(repo, filename, content)
    _commit(repo, f"add {filename}")
    _publish(repo, branch)
    _git(repo, "checkout", "-q", "main")
    _git(repo, "branch", "-q", "-D", branch)


def _for_each_ref(repo: Path) -> str:
    return _git(repo, "for-each-ref", "--format=%(objectname) %(refname)").stdout


def _worktree_count(repo: Path) -> int:
    out = _git(repo, "worktree", "list", "--porcelain").stdout
    return sum(1 for ln in out.splitlines() if ln.startswith("worktree "))


def _kept_clone(scratch_parent: Path) -> Path:
    clones = list(scratch_parent.glob("fleet-triage-*/clone"))
    if len(clones) != 1:
        raise AssertionError(f"expected one kept scratch clone under {scratch_parent}, got {clones}")
    return clones[0]


class ShallowWorktreeGraftTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="fleet-triage-shallow-wt-"))
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(self.tmp)], check=False))
        self.repo = self.tmp / "repo"
        _init_repo(self.repo)

    def test_a_linked_worktree_copies_the_common_graft_and_a_real_conflict_still_conflicts(self) -> None:
        """A behind-main PR from a shallow linked worktree stays NEEDS-UPDATE-BRANCH when the boundary parent is missing.

        The scratch must copy the common directory's ``shallow`` file, the path ``--git-path``
        reports from the worktree. ``<worktree>/.git`` is a file, so a copy of
        ``<worktree>/.git/shallow`` drops the graft and ``git merge`` refuses unrelated
        histories. A real edit of the same file main changed is still ``CONFLICT``.
        """
        _write(self.repo, "fileA.txt", "A0\n")
        root = _commit(self.repo, "c0")
        _write(self.repo, "fileA.txt", "A1\n")
        boundary = _commit(self.repo, "c1")
        _write(self.repo, "fileA.txt", "A2\n")
        _commit(self.repo, "c2")
        _publish(self.repo, "main")
        _origin_only(self.repo, "cursor/behind", boundary, "fileD.txt", "D\n")
        _origin_only(self.repo, "cursor/conflict", boundary, "fileA.txt", "branch\n")

        worktree = self.tmp / "wt"
        _git(self.repo, "worktree", "add", "--detach", str(worktree), "main")
        self.assertTrue((worktree / ".git").is_file(), "the invoking checkout must be a linked worktree")

        graft = boundary + "\n" + boundary + "\n"
        shallow = self.repo / ".git" / "shallow"
        shallow.write_text(graft, encoding="utf-8")
        parent = self.repo / ".git" / "objects" / root[:2] / root[2:]
        self.assertTrue(parent.is_file(), "the boundary's parent must be a loose object before the test deletes it")
        parent.unlink()
        self.assertNotEqual(_git(self.repo, "cat-file", "-t", root, check=False).returncode, 0)
        self.assertEqual(_git(worktree, "rev-parse", "--is-shallow-repository").stdout.strip(), "true")
        named = Path(_git(worktree, "rev-parse", "--path-format=absolute", "--git-path", "shallow").stdout.strip())
        self.assertEqual(named.resolve(), shallow.resolve())
        self.assertFalse((worktree / ".git" / "shallow").exists())

        refs_before = _for_each_ref(self.repo)
        worktrees_before = _worktree_count(self.repo)
        scratch_parent = self.tmp / "scratch-parent"
        scratch_parent.mkdir()
        behind = pm.simulate_merge(
            worktree,
            "origin/cursor/behind",
            run_gates=False,
            keep_scratch=True,
            scratch_parent=scratch_parent,
        )
        self.assertEqual(behind["verdict"], "NEEDS-UPDATE-BRANCH", behind)
        self.assertTrue(behind["behind_main"])
        self.assertEqual(behind["true_delta"], ["fileD.txt"])
        self.assertEqual(behind["conflicted_files"], [])
        self.assertFalse(parent.exists(), "simulating a merge must not write the missing parent back into the source")
        self.assertEqual(shallow.read_text(encoding="utf-8"), graft)
        self.assertEqual(_for_each_ref(self.repo), refs_before)
        self.assertEqual(_worktree_count(self.repo), worktrees_before)

        clone = _kept_clone(scratch_parent)
        self.assertEqual((clone / ".git" / "shallow").read_bytes(), shallow.read_bytes())

        conflict = pm.simulate_merge(worktree, "origin/cursor/conflict", run_gates=False)
        self.assertEqual(conflict["verdict"], "CONFLICT", conflict)
        self.assertIn("fileA.txt", conflict["conflicted_files"])
        self.assertEqual(shallow.read_text(encoding="utf-8"), graft)
        self.assertEqual(_for_each_ref(self.repo), refs_before)
        self.assertEqual(_worktree_count(self.repo), worktrees_before)

    def test_a_shallow_source_whose_graft_file_disappears_is_refused(self) -> None:
        """Git has already said the source is shallow, and the graft path is not a file: refuse, and leave no scratch.

        The two ``rev-parse`` calls are not one snapshot. The file is removed after the
        shallow answer and before ``--git-path`` is stated. Copying nothing would merge
        without the graft. The scratch created for that attempt is removed.
        """
        _write(self.repo, "fileA.txt", "A0\n")
        head = _commit(self.repo, "c0")
        _publish(self.repo, "main")
        shallow = self.repo / ".git" / "shallow"
        shallow.write_text(head + "\n", encoding="utf-8")
        self.assertEqual(_git(self.repo, "rev-parse", "--is-shallow-repository").stdout.strip(), "true")
        refs_before = _for_each_ref(self.repo)
        scratch_parent = self.tmp / "scratch-parent"
        scratch_parent.mkdir()

        real_git = pm._git

        def drop_graft_after_the_shallow_answer(repo: Path, *args: str) -> subprocess.CompletedProcess:
            result = real_git(repo, *args)
            if args == ("rev-parse", "--is-shallow-repository") and result.returncode == 0 and result.stdout.strip() == "true":
                shallow.unlink()
            return result

        with mock.patch.object(pm, "_git", drop_graft_after_the_shallow_answer):
            with self.assertRaises(pm.PredictMergeError) as raised:
                pm.simulate_merge(self.repo, "main", run_gates=False, scratch_parent=scratch_parent)
        self.assertIn("shallow boundary could not be read", str(raised.exception))
        self.assertIn("is not a file", str(raised.exception))
        self.assertEqual(list(scratch_parent.glob("fleet-triage-*")), [])
        self.assertFalse(shallow.exists(), "a refused copy must not write the graft back")
        self.assertEqual(_for_each_ref(self.repo), refs_before)
