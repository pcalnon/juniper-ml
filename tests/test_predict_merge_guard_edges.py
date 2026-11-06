"""Edges of the predict_merge scratch guards that ``tests/test_predict_merge.py`` does not pin.

The depth-1 history cut, a missing filter binary, a binary blob, ``GIT_DIR`` plus ``GIT_WORK_TREE``,
and a linked worktree's object borrow are already covered there. These tests pin the neighboring
contracts on the same scratch:

* a shallow boundary whose parent object is gone, while the merge base is still present, merges
  (``NEEDS-UPDATE-BRANCH``) or really conflicts (``CONFLICT``) -- it must not become an error or a
  false conflict, and it must not write the missing parent back into the source;
* ``GIT_INDEX_FILE``, ``GIT_OBJECT_DIRECTORY``, and ``GIT_COMMON_DIR`` inherited from a hook do not
  redirect the scratch or change the source;
* two histories with no merge base raise ``PredictMergeError`` (unrelated histories), and the scratch
  is removed;
* an ``OSError`` while preparing the scratch is ``PredictMergeError`` and the scratch directory is
  removed, so one PR cannot abort ``triage_batch`` (that loop catches only ``PredictMergeError``).
"""

from __future__ import annotations

import os
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


def _publish_main(repo: Path) -> None:
    _git(repo, "update-ref", "refs/remotes/origin/main", "refs/heads/main")


def _publish_branch(repo: Path, name: str) -> None:
    _git(repo, "update-ref", f"refs/remotes/origin/{name}", f"refs/heads/{name}")


def _for_each_ref(repo: Path) -> str:
    return _git(repo, "for-each-ref", "--format=%(objectname) %(refname)").stdout


def _object_files(repo: Path) -> tuple:
    """Bytes of every loose/pack file under ``.git/objects``, so a redirected object dir is visible."""
    root = repo / ".git" / "objects"
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            files.append((str(path.relative_to(root)), path.read_bytes()))
    return tuple(files)


def _scratches(parent: Path) -> list:
    return list(parent.glob("fleet-triage-*"))


class _RepoCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="fleet-triage-guard-"))
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(self.tmp)], check=False))
        self.repo = self.tmp / "repo"
        _init_repo(self.repo)


class ShallowBoundaryTest(_RepoCase):
    def test_a_missing_parent_past_the_boundary_merges_or_really_conflicts(self):
        """The merge base is present; only the boundary's parent object is gone.

        Without the source's ``.git/shallow``, ``git merge`` dies with ``refusing to merge unrelated
        histories`` and the new non-0/1 guard turns a clean behind-main PR into ``PredictMergeError``.
        The root-boundary fixture in ``test_predict_merge.py`` never deletes a parent, so it stays green
        either way. A real content conflict must stay ``CONFLICT``.
        """
        _write(self.repo, "fileA.txt", "A0\n")
        root = _commit(self.repo, "c0")
        _write(self.repo, "fileA.txt", "A1\n")
        boundary = _commit(self.repo, "c1")
        _write(self.repo, "fileA.txt", "A2\n")
        _commit(self.repo, "c2")
        _publish_main(self.repo)

        _git(self.repo, "checkout", "-q", "-b", "cursor/behind", boundary)
        _write(self.repo, "fileD.txt", "D\n")
        _commit(self.repo, "add D")
        _publish_branch(self.repo, "cursor/behind")
        _git(self.repo, "checkout", "-q", "main")
        _git(self.repo, "branch", "-q", "-D", "cursor/behind")

        _git(self.repo, "checkout", "-q", "-b", "cursor/conflict", boundary)
        _write(self.repo, "fileA.txt", "branch\n")
        _commit(self.repo, "edit A")
        _publish_branch(self.repo, "cursor/conflict")
        _git(self.repo, "checkout", "-q", "main")
        _git(self.repo, "branch", "-q", "-D", "cursor/conflict")

        shallow = self.repo / ".git" / "shallow"
        shallow.write_text(boundary + "\n", encoding="utf-8")
        parent = self.repo / ".git" / "objects" / root[:2] / root[2:]
        self.assertTrue(parent.is_file(), "the boundary's parent must be a loose object before the test deletes it")
        parent.unlink()
        self.assertNotEqual(_git(self.repo, "cat-file", "-t", root, check=False).returncode, 0)
        self.assertEqual(_git(self.repo, "rev-parse", "--is-shallow-repository").stdout.strip(), "true")
        self.assertEqual(_git(self.repo, "merge-base", "origin/main", "origin/cursor/behind").stdout.strip(), boundary)
        refs_before = _for_each_ref(self.repo)

        scratch_parent = self.tmp / "scratch-parent"
        scratch_parent.mkdir()
        behind = pm.simulate_merge(
            self.repo, "origin/cursor/behind", run_gates=False, keep_scratch=True, scratch_parent=scratch_parent,
        )
        self.assertEqual(behind["verdict"], "NEEDS-UPDATE-BRANCH", behind)
        self.assertTrue(behind["behind_main"])
        self.assertEqual(behind["true_delta"], ["fileD.txt"])
        self.assertEqual(behind["conflicted_files"], [])
        self.assertFalse(parent.exists(), "simulating a merge must not write the missing parent back into the source")
        self.assertEqual(shallow.read_text(encoding="utf-8"), boundary + "\n")
        self.assertEqual(_for_each_ref(self.repo), refs_before)
        clone = next(scratch_parent.glob("fleet-triage-*/clone"))
        self.assertEqual((clone / ".git" / "shallow").read_bytes(), shallow.read_bytes())

        conflict = pm.simulate_merge(self.repo, "origin/cursor/conflict", run_gates=False, scratch_parent=self.tmp)
        self.assertEqual(conflict["verdict"], "CONFLICT", conflict)
        self.assertIn("fileA.txt", conflict["conflicted_files"])
        self.assertFalse(parent.exists(), "a conflicting simulation must not write the missing parent back")


class InheritedGitEnvTest(_RepoCase):
    def test_index_object_dir_and_common_dir_do_not_redirect_the_scratch(self):
        """A hook exports these. ``GIT_DIR`` is already pinned; each of these three must be ignored too.

        Dropping any one of them from the denylist makes ``simulate_merge`` raise instead of returning
        ``MERGE-CLEAN`` (checkout reads the foreign index; ``git init`` follows the foreign object dir or
        common dir).
        """
        _write(self.repo, "fileA.txt", "A0\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "-b", "clean")
        _write(self.repo, "fileD.txt", "D\n")
        _commit(self.repo, "add D")
        sentinel = self.tmp / "sentinel.index"
        sentinel.write_bytes(b"SENTINEL\n")
        cases = (
            ("GIT_INDEX_FILE", str(sentinel)),
            ("GIT_OBJECT_DIRECTORY", str(self.repo / ".git" / "objects")),
            ("GIT_COMMON_DIR", str(self.repo / ".git")),
        )
        for name, value in cases:
            with self.subTest(var=name):
                refs_before = _for_each_ref(self.repo)
                head_before = (self.repo / ".git" / "HEAD").read_text(encoding="utf-8")
                objects_before = _object_files(self.repo)
                index_before = sentinel.read_bytes()
                with mock.patch.dict(os.environ, {name: value}):
                    verdict = pm.simulate_merge(self.repo, "clean", run_gates=False, scratch_parent=self.tmp)
                self.assertEqual(verdict["verdict"], "MERGE-CLEAN", verdict)
                self.assertEqual(verdict["true_delta"], ["fileD.txt"])
                self.assertEqual(_for_each_ref(self.repo), refs_before)
                self.assertEqual((self.repo / ".git" / "HEAD").read_text(encoding="utf-8"), head_before)
                self.assertEqual(_object_files(self.repo), objects_before)
                self.assertEqual(sentinel.read_bytes(), index_before)
                self.assertEqual(_scratches(self.tmp), [], "the scratch must be removed")


class MergeFailureTest(_RepoCase):
    def test_unrelated_histories_raise_and_leave_no_scratch(self):
        """An orphan branch has no merge base. Exit 128 must raise, not come back as ``CONFLICT``."""
        _write(self.repo, "fileA.txt", "A0\n")
        _commit(self.repo, "main root")
        _publish_main(self.repo)
        _git(self.repo, "checkout", "-q", "--orphan", "orphan")
        _git(self.repo, "rm", "-q", "-rf", ".")
        _write(self.repo, "fileO.txt", "O\n")
        _commit(self.repo, "orphan root")
        refs_before = _for_each_ref(self.repo)

        with self.assertRaises(pm.PredictMergeError) as caught:
            pm.simulate_merge(self.repo, "orphan", run_gates=False, scratch_parent=self.tmp)
        self.assertIn("refusing to merge unrelated histories", str(caught.exception))
        self.assertEqual(_for_each_ref(self.repo), refs_before)
        self.assertEqual(_scratches(self.tmp), [], "a failed merge must not leave the scratch behind")

    def test_a_prepare_oserror_is_a_predict_merge_error_and_removes_the_scratch(self):
        """``triage_batch`` only catches ``PredictMergeError``. A bare ``OSError`` would abort the whole batch."""
        _write(self.repo, "fileA.txt", "A0\n")
        _commit(self.repo, "c0")
        _publish_main(self.repo)
        real = Path.write_text

        def fail_alternates(self_path: Path, *args, **kwargs):
            if self_path.name == "alternates":
                raise OSError(28, "No space left on device")
            return real(self_path, *args, **kwargs)

        with mock.patch.object(Path, "write_text", fail_alternates):
            with self.assertRaises(pm.PredictMergeError) as caught:
                pm.simulate_merge(self.repo, "main", run_gates=False, scratch_parent=self.tmp)
        self.assertIn("could not prepare the scratch repository", str(caught.exception))
        self.assertIn("No space left on device", str(caught.exception))
        self.assertEqual(_scratches(self.tmp), [], "a prepare failure must remove the scratch directory")


if __name__ == "__main__":
    unittest.main()
