#!/usr/bin/env python3
"""
Reproduce: worktree_cleanup.bash phase 4's branch-refusal message lists NO commits.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-08
Status: ad-hoc — investigation (Cursor flood #3 evaluation of juniper-ml#2163)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/worktree_cleanup.bash phase_4_cleanup (the `git log ... --not --branches` line);
         juniper-ml#2163's PR body, which noted the empty list and did not pin it

When `git branch -d` refuses, phase 4 prints "These commits would be lost. Nothing has been
deleted:" and then runs

    git log --oneline --no-merges "$OLD_BRANCH" --not --branches --remotes --tags

`--not --branches` excludes every commit reachable from ANY local branch -- the refused branch
included -- so the list is empty by construction. This builds a throwaway repository under a
temporary directory (nothing outside it is read or written), runs main's command and a corrected
one (`--exclude=<branch>` before `--branches`), and prints both. Exit 0 if main's command is empty
and the corrected one names the unique commit (the defect reproduces), 1 otherwise.
"""

import pathlib
import subprocess
import sys
import tempfile


def _git(cwd, *args):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, check=True).stdout


def main():
    with tempfile.TemporaryDirectory() as tmp:
        repo = pathlib.Path(tmp) / "repo"
        repo.mkdir()
        _git(repo, "init", "-q", "-b", "main")
        _git(repo, "config", "user.email", "repro@example.invalid")
        _git(repo, "config", "user.name", "Repro")
        _git(repo, "config", "commit.gpgsign", "false")
        (repo / "a.txt").write_text("a\n", encoding="utf-8")
        _git(repo, "add", "a.txt")
        _git(repo, "commit", "-q", "-m", "initial")
        _git(repo, "checkout", "-q", "-b", "feature/refused")
        (repo / "b.txt").write_text("b\n", encoding="utf-8")
        _git(repo, "add", "b.txt")
        _git(repo, "commit", "-q", "-m", "unique commit that must survive")
        _git(repo, "checkout", "-q", "main")
        as_on_main = _git(repo, "log", "--oneline", "--no-merges", "feature/refused", "--not", "--branches", "--remotes", "--tags")
        corrected = _git(repo, "log", "--oneline", "--no-merges", "feature/refused", "--not", "--exclude=feature/refused", "--branches", "--remotes", "--tags")
    print(f"main's command lists:      {as_on_main!r}")
    print(f"with --exclude=<branch>:   {corrected!r}")
    reproduced = as_on_main == "" and "unique commit that must survive" in corrected
    print("DEFECT REPRODUCED" if reproduced else "not reproduced")
    return 0 if reproduced else 1


if __name__ == "__main__":
    sys.exit(main())
