"""A linked worktree of a shallow checkout still hands predict_merge the common-dir graft.

``tests/test_predict_merge.py`` pins the graft copy on a normal checkout, where ``.git`` is a
directory. Fleet triage runs from linked worktrees of juniper-ml's shallow primary. There
``.git`` is a file, and the shallow boundary lives in the common git dir. Reading
``<worktree>/.git/shallow`` misses it, ``git merge`` walks a parent the shallow clone never
fetched, and a clean behind-main PR comes back ``CONFLICT``.

Production ``util/fleet_triage/predict_merge.py`` is unchanged. The fixture repos are
temporary and never touch the invoking checkout.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from fleet_triage import predict_merge as pm  # noqa: E402  (path-invoked util import)

GIT_TIMEOUT = 60


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    cp = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, timeout=GIT_TIMEOUT)
    if check and cp.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed ({cp.returncode}): {cp.stderr.strip()}")
    return cp


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q", "-b", "main")
    _git(path, "config", "user.email", "tests@example.invalid")
    _git(path, "config", "user.name", "Fleet Tests")
    _git(path, "config", "commit.gpgsign", "false")


def _write(repo: Path, rel: str, content: str) -> None:
    target = repo / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def _commit(repo: Path, msg: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


class ShallowWorktreeGraftTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="fleet-triage-wt-"))
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(self.tmp)], check=False))
        self.repo = self.tmp / "repo"
        _init_repo(self.repo)

    def test_a_linked_worktree_copies_the_common_dir_graft_verbatim(self) -> None:
        """Both boundary lines are copied from the common dir, and the missing parent stays missing.

        The second line is a side commit the merge never walks. A copy that kept only the
        boundary the merge needs would still return NEEDS-UPDATE-BRANCH; the byte compare
        is what rejects that rewrite.
        """
        _write(self.repo, "fileA.txt", "A0\n")
        root = _commit(self.repo, "c0")
        _write(self.repo, "fileA.txt", "A1\n")
        boundary = _commit(self.repo, "c1")
        _write(self.repo, "fileA.txt", "A2\n")
        _commit(self.repo, "c2")
        _git(self.repo, "update-ref", "refs/remotes/origin/main", "refs/heads/main")

        _git(self.repo, "checkout", "-q", "-b", "cursor/behind", boundary)
        _write(self.repo, "fileD.txt", "D\n")
        behind = _commit(self.repo, "add D")
        _git(self.repo, "update-ref", "refs/remotes/origin/cursor/behind", "refs/heads/cursor/behind")
        _git(self.repo, "checkout", "-q", "main")
        _git(self.repo, "branch", "-q", "-D", "cursor/behind")

        _git(self.repo, "checkout", "-q", "-b", "side", boundary)
        _write(self.repo, "fileS.txt", "S\n")
        side = _commit(self.repo, "side")
        _git(self.repo, "checkout", "-q", "main")
        _git(self.repo, "branch", "-q", "-D", "side")

        graft = f"{boundary}\n{side}\n"
        shallow = self.repo / ".git" / "shallow"
        shallow.write_text(graft, encoding="utf-8")
        parent = self.repo / ".git" / "objects" / root[:2] / root[2:]
        self.assertTrue(parent.is_file(), "the boundary's parent must be a loose object before the test deletes it")
        parent.unlink()

        worktree = self.tmp / "wt"
        _git(self.repo, "worktree", "add", "--detach", str(worktree), "HEAD")
        self.assertTrue((worktree / ".git").is_file(), "a linked worktree's .git is a file, not a directory")
        common = Path(_git(worktree, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip())
        self.assertEqual(common.resolve(), (self.repo / ".git").resolve())
        self.assertEqual((common / "shallow").read_text(encoding="utf-8"), graft)
        self.assertFalse((worktree / ".git" / "shallow").exists())
        self.assertEqual(_git(worktree, "rev-parse", "--is-shallow-repository").stdout.strip(), "true")
        self.assertEqual(_git(worktree, "merge-base", "origin/main", "origin/cursor/behind").stdout.strip(), boundary)

        scratch_parent = self.tmp / "scratch-parent"
        scratch_parent.mkdir()
        result = pm.simulate_merge(
            worktree,
            "origin/cursor/behind",
            run_gates=False,
            keep_scratch=True,
            scratch_parent=scratch_parent,
        )
        self.assertEqual(result["verdict"], "NEEDS-UPDATE-BRANCH", result)
        self.assertTrue(result["behind_main"])
        self.assertEqual(result["true_delta"], ["fileD.txt"])
        self.assertEqual(result["conflicted_files"], [])
        self.assertEqual(result["branch_sha"], behind)

        clone = next(scratch_parent.glob("fleet-triage-*/clone"))
        self.assertEqual((clone / ".git" / "shallow").read_bytes(), graft.encode("utf-8"))
        self.assertEqual((common / "shallow").read_text(encoding="utf-8"), graft)
        self.assertFalse(parent.exists(), "simulating a merge must not write the missing parent back into the source")
        self.assertEqual(_git(self.repo, "worktree", "list", "--porcelain").stdout.count("worktree "), 2)

    def test_a_non_shallow_linked_worktree_does_not_grow_a_scratch_graft(self) -> None:
        """``--is-shallow-repository`` is false, so the scratch gets no ``.git/shallow``.

        An empty graft would change merge-base. A worktree whose ``.git`` is a file must
        take the same early return as a normal checkout.
        """
        _write(self.repo, "fileA.txt", "A0\n")
        _commit(self.repo, "c0")
        _git(self.repo, "update-ref", "refs/remotes/origin/main", "refs/heads/main")
        _git(self.repo, "checkout", "-q", "-b", "cursor/ahead")
        _write(self.repo, "fileD.txt", "D\n")
        _commit(self.repo, "add D")
        _git(self.repo, "update-ref", "refs/remotes/origin/cursor/ahead", "refs/heads/cursor/ahead")
        _git(self.repo, "checkout", "-q", "main")
        _git(self.repo, "branch", "-q", "-D", "cursor/ahead")

        worktree = self.tmp / "wt"
        _git(self.repo, "worktree", "add", "--detach", str(worktree), "HEAD")
        self.assertTrue((worktree / ".git").is_file())
        self.assertEqual(_git(worktree, "rev-parse", "--is-shallow-repository").stdout.strip(), "false")

        scratch_parent = self.tmp / "scratch-parent"
        scratch_parent.mkdir()
        result = pm.simulate_merge(
            worktree,
            "origin/cursor/ahead",
            run_gates=False,
            keep_scratch=True,
            scratch_parent=scratch_parent,
        )
        self.assertEqual(result["verdict"], "MERGE-CLEAN", result)
        self.assertFalse(result["behind_main"])
        self.assertEqual(result["true_delta"], ["fileD.txt"])
        clone = next(scratch_parent.glob("fleet-triage-*/clone"))
        self.assertFalse((clone / ".git" / "shallow").exists())


if __name__ == "__main__":
    unittest.main()
