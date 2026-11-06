"""Edges of the scratch that borrows the checkout's objects.

``tests/test_predict_merge.py`` already pins a shallow *normal* checkout whose PR head
exists only as ``origin/<branch>``. Three neighboring failures stay green there:

* a linked worktree, whose ``.git`` is a file and whose objects live in the common
  directory (``--git-dir`` has no ``objects`` directory at all);
* a sha256 source, whose scratch ``git init`` must use the same object format or
  ``update-ref`` cannot pin the borrowed commits;
* a file whose required smudge filter refuses to run unless ``GIT_LFS_SKIP_SMUDGE=1``.
  That is the variable git-lfs honors; the scratch has no remote to fetch LFS content from.

Each test drives ``simulate_merge`` on a synthetic repo. No network, no ``gh``, no
``pre-commit``. Production ``util/fleet_triage/predict_merge.py`` is unchanged.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from fleet_triage import predict_merge as pm  # noqa: E402  (path-invoked util import)

GIT_TIMEOUT = 60
POINTER_TEXT = "version https://git-lfs.github.com/spec/v1\noid sha256:abc\nsize 4\n"


def _git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    # The scratch's own git commands are what set GIT_LFS_SKIP_SMUDGE. A parent
    # that already sets it would hide a regression that dropped that assignment,
    # so fixture git never inherits it.
    env.pop("GIT_LFS_SKIP_SMUDGE", None)
    cp = subprocess.run(
        ["git", "-C", str(cwd), *args],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        env=env,
    )
    if check and cp.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed ({cp.returncode}): {cp.stderr.strip()}")
    return cp


def _init_repo(path: Path, object_format: str = "sha1") -> None:
    path.mkdir(parents=True, exist_ok=True)
    _git(path, "init", "-q", "-b", "main", f"--object-format={object_format}")
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


def _for_each_ref(repo: Path) -> str:
    return _git(repo, "for-each-ref", "--format=%(objectname) %(refname)").stdout


def _worktree_count(repo: Path) -> int:
    out = _git(repo, "worktree", "list", "--porcelain").stdout
    return sum(1 for ln in out.splitlines() if ln.startswith("worktree "))


def _origin_only_branch(repo: Path, filename: str, content: str) -> None:
    """Commit ``filename`` on a branch, publish it as ``origin/cursor/remote-only``, and delete the local branch."""
    _git(repo, "checkout", "-q", "-b", "cursor/remote-only")
    _write(repo, filename, content)
    _commit(repo, f"add {filename}")
    _publish(repo, "cursor/remote-only")
    _git(repo, "checkout", "-q", "main")
    _git(repo, "branch", "-q", "-D", "cursor/remote-only")
    local = _git(repo, "for-each-ref", "refs/heads/cursor").stdout
    if local:
        raise AssertionError(f"the head must have no local branch, found {local!r}")


def _kept_clone(scratch_parent: Path) -> Path:
    clones = list(scratch_parent.glob("fleet-triage-*/clone"))
    if len(clones) != 1:
        raise AssertionError(f"expected one kept scratch clone under {scratch_parent}, got {clones}")
    return clones[0]


def _alternates(clone: Path) -> list[Path]:
    text = (clone / ".git" / "objects" / "info" / "alternates").read_text(encoding="utf-8")
    return [Path(line).resolve() for line in text.splitlines() if line.strip()]


class ScratchBorrowEdgesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="fleet-triage-scratch-edges-"))
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(self.tmp)], check=False))
        self.repo = self.tmp / "repo"

    def _scratch_parent(self) -> Path:
        parent = self.tmp / "scratch-parent"
        parent.mkdir()
        return parent

    def test_shallow_linked_worktree_borrows_the_common_object_store(self) -> None:
        """A shallow linked worktree resolves an origin-only head from the common object directory.

        ``--git-dir`` for a linked worktree is ``.git/worktrees/<name>``, which has no
        ``objects`` directory. Pointing the alternate there (or at ``<worktree>/.git/objects``,
        where ``.git`` is a file) raises before the merge. ``git clone --shared`` of this
        shallow source does not borrow ``origin/*`` either.
        """
        _init_repo(self.repo)
        _write(self.repo, "fileA.txt", "A0\n")
        root = _commit(self.repo, "c0")
        _publish(self.repo, "main")
        (self.repo / ".git" / "shallow").write_text(root + "\n", encoding="utf-8")
        _origin_only_branch(self.repo, "fileD.txt", "D\n")

        worktree = self.tmp / "wt"
        _git(self.repo, "worktree", "add", "--detach", str(worktree), "main")
        self.assertTrue((worktree / ".git").is_file(), "the invoking checkout must be a linked worktree")
        self.assertEqual(_git(worktree, "rev-parse", "--is-shallow-repository").stdout.strip(), "true")
        common = Path(_git(worktree, "rev-parse", "--path-format=absolute", "--git-common-dir").stdout.strip())
        self.assertEqual(common.resolve(), (self.repo / ".git").resolve())

        refs_before = _for_each_ref(self.repo)
        worktrees_before = _worktree_count(self.repo)
        scratch_parent = self._scratch_parent()
        verdict = pm.simulate_merge(
            worktree,
            "origin/cursor/remote-only",
            run_gates=False,
            keep_scratch=True,
            scratch_parent=scratch_parent,
        )
        self.assertEqual(verdict["verdict"], "MERGE-CLEAN", verdict.get("error"))
        self.assertEqual(verdict["true_delta"], ["fileD.txt"])

        clone = _kept_clone(scratch_parent)
        self.assertTrue((clone / ".git").is_dir(), "the scratch is a repository, not a worktree pointer")
        self.assertEqual(_alternates(clone), [(self.repo / ".git" / "objects").resolve()])
        self.assertEqual(_for_each_ref(self.repo), refs_before)
        self.assertEqual(_worktree_count(self.repo), worktrees_before)

    def test_sha256_origin_only_head_uses_the_source_object_format(self) -> None:
        """The scratch is initialized with the source's object format, then pins an origin-only sha256 commit.

        Dropping ``--object-format`` leaves a sha1 scratch. ``update-ref`` of the borrowed
        sha256 commit fails, and so does a scratch that does not borrow the source's objects.
        """
        _init_repo(self.repo, object_format="sha256")
        self.assertEqual(_git(self.repo, "rev-parse", "--show-object-format").stdout.strip(), "sha256")
        _write(self.repo, "fileA.txt", "A0\n")
        _commit(self.repo, "c0")
        _publish(self.repo, "main")
        _origin_only_branch(self.repo, "fileD.txt", "D\n")

        scratch_parent = self._scratch_parent()
        verdict = pm.simulate_merge(
            self.repo,
            "origin/cursor/remote-only",
            run_gates=False,
            keep_scratch=True,
            scratch_parent=scratch_parent,
        )
        self.assertEqual(verdict["verdict"], "MERGE-CLEAN", verdict.get("error"))
        self.assertEqual(verdict["true_delta"], ["fileD.txt"])

        clone = _kept_clone(scratch_parent)
        self.assertEqual(_git(clone, "rev-parse", "--show-object-format").stdout.strip(), "sha256")
        self.assertEqual(_alternates(clone), [(self.repo / ".git" / "objects").resolve()])

    def test_lfs_checkout_leaves_the_pointer_in_place(self) -> None:
        """A required smudge runs only when ``GIT_LFS_SKIP_SMUDGE`` is unset, and then the checkout fails.

        git-lfs reads that variable and refuses to download into a scratch that has no
        remote. The stand-in filter does the same, so the pin does not depend on git-lfs
        being installed. The parent environment may already set the variable; this test
        clears it, and the scratch's git commands are what put it back.
        """
        self._without_inherited_smudge_skip()
        smudge = self.tmp / "smudge.sh"
        smudge.write_text(
            "#!/bin/sh\n" 'if [ "$GIT_LFS_SKIP_SMUDGE" = "1" ]; then\n' "  cat\n" "  exit 0\n" "fi\n" 'echo "smudge refused" >&2\n' "exit 1\n",
            encoding="utf-8",
        )
        smudge.chmod(0o755)
        self._inject_smudge_filter(smudge)

        _init_repo(self.repo)
        clean = self.tmp / "clean.sh"
        clean.write_text("#!/bin/sh\ncat <<'EOF'\n" + POINTER_TEXT + "EOF\n", encoding="utf-8")
        clean.chmod(0o755)
        _git(self.repo, "config", "filter.fleet-test.clean", str(clean))
        _git(self.repo, "config", "filter.fleet-test.required", "true")
        _write(self.repo, "fileA.txt", "A0\n")
        _commit(self.repo, "c0")
        _publish(self.repo, "main")
        _git(self.repo, "checkout", "-q", "-b", "cursor/remote-only")
        _write(self.repo, ".gitattributes", "*.png filter=fleet-test -text\n")
        _write(self.repo, "pic.png", "payload-that-must-not-be-checked-out\n")
        _commit(self.repo, "add pic.png")
        pointer = _git(self.repo, "show", "HEAD:pic.png").stdout
        self.assertEqual(pointer, POINTER_TEXT)
        _publish(self.repo, "cursor/remote-only")
        _git(self.repo, "checkout", "-q", "main")
        _git(self.repo, "branch", "-q", "-D", "cursor/remote-only")

        refs_before = _for_each_ref(self.repo)
        scratch_parent = self._scratch_parent()
        verdict = pm.simulate_merge(
            self.repo,
            "origin/cursor/remote-only",
            run_gates=False,
            keep_scratch=True,
            scratch_parent=scratch_parent,
        )
        self.assertEqual(verdict["verdict"], "MERGE-CLEAN", verdict.get("error"))
        self.assertEqual(verdict["true_delta"], [".gitattributes", "pic.png"])
        self.assertEqual((_kept_clone(scratch_parent) / "pic.png").read_text(encoding="utf-8"), POINTER_TEXT)
        self.assertEqual(_for_each_ref(self.repo), refs_before)

    def _without_inherited_smudge_skip(self) -> None:
        skipped = os.environ.pop("GIT_LFS_SKIP_SMUDGE", None)

        def restore() -> None:
            if skipped is None:
                os.environ.pop("GIT_LFS_SKIP_SMUDGE", None)
            else:
                os.environ["GIT_LFS_SKIP_SMUDGE"] = skipped

        self.addCleanup(restore)

    def _inject_smudge_filter(self, smudge: Path) -> None:
        """Make the scratch's git use ``smudge`` for ``filter.fleet-test``. The scratch is a new repo, so the source's local config does not apply to it."""
        injected = {
            "GIT_CONFIG_COUNT": "2",
            "GIT_CONFIG_KEY_0": "filter.fleet-test.smudge",
            "GIT_CONFIG_VALUE_0": str(smudge),
            "GIT_CONFIG_KEY_1": "filter.fleet-test.required",
            "GIT_CONFIG_VALUE_1": "true",
        }
        previous = {key: os.environ.get(key) for key in injected}
        os.environ.update(injected)

        def restore() -> None:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

        self.addCleanup(restore)


if __name__ == "__main__":
    unittest.main()
