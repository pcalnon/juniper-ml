#!/usr/bin/env python3
"""
Report, for every local-only commit the canopy E2E ledger or its handoffs cite, what keeps it: a branch, a reflog, or nothing.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md (A6, A9)
         notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 9 "Still owed" items 13 and 15

Why: the ledger's item 15 asks whether its local-only commits get a provenance ref. A cleanup must not
run before that question is answered: removing a worktree deletes its HEAD reflog, and deleting a
branch deletes that branch's reflog. Once no branch and no reflog references a commit, a later
``git gc`` may prune it (by default after a 2-week grace; reflog entries for commits no branch holds
expire after 30 days).

What it reports per commit (states, most to least protected):
  ON-MAIN      an ancestor of ``origin/main`` (as this clone last fetched it).
  BRANCH       held by one or more local or remote-tracking branches (``git branch -a --contains``).
  REFLOG-ONLY  held by no branch, but named in at least one reflog file (branch reflogs under
               ``logs/refs/`` and worktree ``logs/HEAD`` files). A cleanup of the listed
               branch/worktree removes that protection.
  NO-HOLDER    in the object store, held by no branch and named in no reflog: prunable by ``git gc``.
  MISSING      not in this clone's object store.
Every BRANCH / REFLOG-ONLY line is followed by its holders. A reflog holder is printed as the reflog
file's path relative to the common git dir.

What it does NOT see: stashes, other clones, other hosts, and GitHub (a commit GitHub has is safe
regardless; none of the commits below is on GitHub as of 2026-09-24). Being an ancestor of a branch
tip counts as BRANCH; which commit a provenance ref should point at is the TIP of the holding branch,
not the cited commit itself (the Phase 9 frozen commits are descendants of f6861234).

READ-ONLY: it runs only ``git rev-parse``, ``git cat-file``, ``git merge-base --is-ancestor``,
``git branch --contains`` and ``git worktree list``, and it reads reflog files. juniper-ml commands
run from THIS checkout (worktrees share one object store and one ref namespace); canopy commands
run from the canopy primary.

Usage: python3 util/ad-hoc/2026-09-24_ledger_cited_commit_reachability.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

JUNIPER = Path("/home/pcalnon/Development/python/Juniper")
ML = Path(__file__).resolve().parents[2]
CANOPY = JUNIPER / "juniper-canopy"

# (repo label, repo dir, sha, where it is cited)
CITED = [
    ("canopy", CANOPY, "ce78e0de", "ledger item 15: served"),
    ("canopy", CANOPY, "78c057e2", "ledger item 15: served"),
    ("canopy", CANOPY, "668380ec", "ledger item 15: served"),
    ("canopy", CANOPY, "723ee812", "ledger item 15: served"),
    ("canopy", CANOPY, "884d22fb", "ledger item 15: served (F-055 first fix)"),
    ("canopy", CANOPY, "cf6fb1dc", "ledger item 15: cited, never served"),
    ("canopy", CANOPY, "7a4a2e33", "ledger item 15: cited, never served"),
    ("canopy", CANOPY, "8990f65c", "ledger item 15: cited, never served"),
    ("canopy", CANOPY, "5310b81a", "ledger item 15: cited, never served"),
    ("canopy", CANOPY, "c360fb53", "ledger item 15: cited, never served"),
    ("canopy", CANOPY, "040dc5c1", "ledger item 15: cited, never served"),
    ("canopy", CANOPY, "26bf27b3", "ledger item 13: follow-up local commit"),
    ("canopy", CANOPY, "96e7b105", "ledger item 13: follow-up rebased copy"),
    ("canopy", CANOPY, "b07943d6", "ledger Phase 9 round 5: the FAQ's text"),
    ("canopy", CANOPY, "135c2782", "E2E handoff: follow-up local branch head"),
    ("ml", ML, "ada8e50c", "ledger item 15: juniper-ml"),
    ("ml", ML, "b54e3b3f", "ledger item 15: juniper-ml"),
    ("ml", ML, "f6861234", "ledger item 15: rebased copy of b54e3b3f"),
    ("ml", ML, "800c20bb", "ledger Phase 9: the 09-23 WIP commit"),
    ("ml", ML, "5a0e4ea9", "ledger Phase 9: 800c20bb's rebased copy"),
    ("ml", ML, "e624c281", "ledger Phase 9 round 1 frozen commit"),
    ("ml", ML, "acf1a93a", "ledger Phase 9 frozen commit"),
    ("ml", ML, "3f83b9c6", "ledger Phase 9 frozen commit"),
    ("ml", ML, "86e82c0c", "ledger Phase 9 frozen commit"),
    ("ml", ML, "07aef715", "ledger Phase 9 frozen commit"),
    ("ml", ML, "b0b17cad", "ledger Phase 9 frozen commit"),
    ("ml", ML, "129f4880", "ledger Phase 9 frozen commit"),
    ("ml", ML, "3297131f", "ledger Phase 9 frozen commit"),
    ("ml", ML, "04db8614", "ledger Phase 9 frozen commit"),
    ("ml", ML, "b0eb4ac1", "ledger Phase 9 round 10 frozen commit"),
    ("ml", ML, "808b74df", "E2E handoff: graceful-sprouting-panda local head"),
    ("ml", ML, "08a1573a", "09-23 E2E handoff: squishy-dancing-moth WIP"),
    ("ml", ML, "48df689b", "09-23 E2E handoff: squishy-dancing-moth WIP"),
]


def git(repo: Path, *args: str) -> tuple[int, str]:
    proc = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True)
    return proc.returncode, proc.stdout.strip()


def worktree_by_branch(repo: Path) -> dict[str, str]:
    """Map ``refs/heads/<b>`` -> worktree path, from ``git worktree list --porcelain``."""
    _, out = git(repo, "worktree", "list", "--porcelain")
    mapping: dict[str, str] = {}
    path = ""
    for line in out.splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree ") :]
        elif line.startswith("branch "):
            mapping[line[len("branch ") :]] = path
    return mapping


def reflog_files(repo: Path) -> tuple[Path, list[Path]]:
    """The common git dir, and every reflog file in it: branch reflogs and each worktree's HEAD reflog."""
    _, common = git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir")
    base = Path(common)
    files = [p for p in (base / "logs").rglob("*") if p.is_file()]
    files += [p for p in (base / "worktrees").glob("*/logs/HEAD") if p.is_file()]
    return base, files


def reflog_holders(full_sha: str, base: Path, files: list[Path]) -> list[str]:
    """Reflog files that name ``full_sha`` as an old or new value (reflogs store full SHAs)."""
    held = []
    for path in files:
        try:
            text = path.read_text(errors="replace")
        except OSError:
            continue
        if full_sha in text:
            held.append(str(path.relative_to(base)))
    return sorted(held)


def main() -> int:
    maps = {"canopy": worktree_by_branch(CANOPY), "ml": worktree_by_branch(ML)}
    logs = {"canopy": reflog_files(CANOPY), "ml": reflog_files(ML)}
    counts: dict[str, int] = {}
    for label, repo, sha, why in CITED:
        rc, full = git(repo, "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}")
        if rc or not full:
            print(f"{label:6} {sha}  MISSING      ({why})")
            counts["MISSING"] = counts.get("MISSING", 0) + 1
            continue
        on_main = git(repo, "merge-base", "--is-ancestor", full, "origin/main")[0] == 0
        _, branches = git(repo, "branch", "-a", "--contains", full, "--format=%(refname)")
        refs = [b for b in branches.splitlines() if b]
        base, files = logs[label]
        reflogs = [] if (on_main or refs) else reflog_holders(full, base, files)
        if on_main:
            state = "ON-MAIN"
        elif refs:
            state = "BRANCH"
        elif reflogs:
            state = "REFLOG-ONLY"
        else:
            state = "NO-HOLDER"
        counts[state] = counts.get(state, 0) + 1
        print(f"{label:6} {sha}  {state:11}  ({why})")
        for ref in refs:
            wt = maps[label].get(ref)
            print(f"         held by {ref}" + (f" [worktree {Path(wt).name}]" if wt else ""))
        for rl in reflogs:
            print(f"         reflog  {rl}")
    summary = ", ".join(f"{k} {v}" for k, v in sorted(counts.items()))
    print(f"\n{len(CITED)} commits: {summary}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
