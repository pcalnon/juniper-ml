#!/usr/bin/env python3
"""Apply Lane B's round-40 findings to both handoffs: wrong squash SHAs, branch, and the amputation.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-21
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: round-40 handoff §6; round-39 handoff §9.5 / §9.8

FOUR FINDINGS, ALL RE-DERIVED BEFORE BEING ACCEPTED (procedure §5.2 -- a lone finding is a lead,
not a fact).

1. TWO CITED "squash" SHAs ARE HEAD SHAs, and neither is on main. Re-derived:
       git merge-base --is-ancestor 968b9e9e origin/main   -> NO
       gh api .../pulls/1974 --jq .merge_commit_sha        -> ea24a19ae33f  (head was 968b9e9e31b4)
       gh api .../pulls/659  --jq .merge_commit_sha        -> b47bd262b508  (head was 435d60693105)
   This is the trap already recorded in memory `reference_safe_merge_exits_zero_without_merging`:
   **util/safe_merge.py prints the HEAD sha, not the squash commit.** The handoffs cited
   safe_merge's output as the merge commit while claiming "verified by content on origin/main,
   not by a MERGED badge" -- so the very citation offered as proof pointed at a commit that is
   not on main. The FILE CONTENT claim survives (content on main was verified separately, and
   the diff between cited and actual SHA is empty); only the citation was wrong.
   Fixed in BOTH handoffs, and the register was checked and is clean (it cites no SHAs).

2. BRANCH NAME. Both documents say branch `main`. Actual: `git branch --show-current` ->
   `worktree-eager-seeking-milner`. A worktree cannot share a branch with the primary checkout;
   the session-start snapshot that said `main` described the primary repo, not here.

3. "Working tree carries only this document" is FALSE. Corrected to describe what is actually
   there, including WHY: `git checkout origin/main -- notes/` restaged every notes file that
   differs between this worktree's stale HEAD and origin/main, which is where the
   container-registry plan and the backup-tests note came from. They are origin/main content,
   not uncommitted work from another arc -- but the claim as written was wrong either way.

4. THE AMPUTATION, and it is the one that matters. Round 40 dropped the PR-opening mechanism
   ENTIRELY -- no open_signed_pr, no required_signatures, no conda envs, no shell-structure
   limits -- with no pointer to round 39 §5, which carries them. Round 39's OWN round-2
   validation caught this exact omission one cycle earlier and round 39 fixed it. Regressing a
   defect a validator already caught is worse than never having fixed it, because the lineage
   now looks like it has the guard. A new §4a carries the minimum, and points at round 39 §5 for
   the rest.

Also hedges §1's canopy language, which stated a mechanism conclusion as settled while §6 says
no lane attacked it.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "prompts" / "thread-handoff_automated-prompts"
R39 = ROOT / "HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md"
R40 = ROOT / "HANDOFF_2026-09-21_defect-register-round-40-x-c-and-m-a-shipped-and-d-a-grounded.md"

R39_SUBS = [
    (
        "juniper-cascor#659 (squash `435d6069`) → `src/api/security.py:68,72`; juniper-ml#1974 (squash\n`968b9e9e`) →",
        "juniper-cascor#659 (squash `b47bd262`) → `src/api/security.py:68,72`; juniper-ml#1974 (squash\n`ea24a19a`) →",
    ),
    (
        "(`juniper-ml/.claude/worktrees/eager-seeking-milner`), branch `main`, which was one commit\nbehind `origin/main` at session start (`52571621` vs `d721fc78`).",
        "(`juniper-ml/.claude/worktrees/eager-seeking-milner`), branch **`worktree-eager-seeking-milner`**\n(*corrected 2026-09-21: this said `main`. A worktree cannot share a branch with the primary\ncheckout; the session-start snapshot describing `main` was the primary repo, not here*), one\ncommit behind `origin/main` at session start (`52571621` vs `d721fc78`).",
    ),
]

R40_SUBS = [
    (
        "juniper-cascor#659 (squash `435d6069`) → `src/api/security.py:68,72`; juniper-ml#1974 (squash\n`968b9e9e`) →",
        "juniper-cascor#659 (squash `b47bd262`) → `src/api/security.py:68,72`; juniper-ml#1974 (squash\n`ea24a19a`) →",
    ),
    (
        "| juniper-cascor#659 | MERGED `435d6069` |",
        "| juniper-cascor#659 | MERGED `b47bd262` |",
    ),
    (
        "| juniper-ml#1974 | MERGED `968b9e9e` |",
        "| juniper-ml#1974 | MERGED `ea24a19a` |",
    ),
    # Hedge the canopy mechanism claim to match §6.
    (
        "**this is NOT the auth bypass it looks like.** Its only caller",
        "**this is very probably NOT the auth bypass it looks like — but read §6 before relying on\nit, because no lane attacked this and it is a *mechanism* claim.** Its only caller",
    ),
    (
        "is set. Do not let a future summary promote it. Memory:",
        "is set. That reasoning was traced through the caller, `get_secret` and the boot check, and\nnot merely read off the line — but it was never independently refuted, so treat it as the best\ncurrent reading rather than a settled fact, and do not let a future summary promote it further.\nMemory:",
    ),
    # Git status.
    (
        "juniper-ml worktree `eager-seeking-milner`\n(`juniper-ml/.claude/worktrees/eager-seeking-milner`), branch `main`, behind `origin/main` (all\nfive PRs above are merged; the worktree was refreshed from `origin/main` before each register\nedit). Working tree carries only this document at handoff time.",
        "juniper-ml worktree `eager-seeking-milner`\n(`juniper-ml/.claude/worktrees/eager-seeking-milner`), branch **`worktree-eager-seeking-milner`**\n— *not* `main`; a worktree cannot share a branch with the primary checkout. Behind\n`origin/main` (all five PRs above are merged; the register and both handoffs were refreshed from\n`origin/main` before each edit).\n\n**The working tree is NOT clean, and an earlier draft of this section wrongly said it carried\nonly this document.** It holds this document plus the session's `util/ad-hoc/` scripts\n(untracked), and a staged `notes/` tree. That staging is an artefact of\n`git checkout origin/main -- notes/`, which restages **every** notes file differing between this\nworktree's stale HEAD and `origin/main` — so files from unrelated arcs (the container-registry\nplan, the backup-tests note) appear staged. They are `origin/main` content, not uncommitted work\nfrom another session, but **verify with `git status --short` rather than trusting this\nparagraph**, and never `git commit -a` from here.",
    ),
]

R40_NEW_SECTION_ANCHOR = "---\n\n## 5. Verify starting state"
R40_NEW_SECTION = """---

## 4a. How work gets LANDED here — round 40's first draft dropped this entirely

**Round 39's §5.6-§5.8 carry the full mechanism and you should read them.** This section exists
because round 40's first draft omitted all of it, and Lane B caught that round 39's *own*
round-2 validation had caught the identical omission one cycle earlier. Regressing a defect a
validator already found is worse than never fixing it: the lineage looks like it has the guard.

- **A local `git push` cannot land a mergeable commit.** All nine repos have
  `required_signatures`; local signing hangs (the key needs a hardware touch), and one unsigned
  commit anywhere in a branch's history blocks the merge — squash does not rescue it.
- **Open a PR:** `python3 util/open_signed_pr.py --repo <repo> --branch <branch> --add
  LOCAL:REPOPATH --message <msg> --title <title> --body-file <path>`. Only GraphQL
  `createCommitOnBranch` signs; `PUT /contents` does not.
- **Follow-up commit:** `python3 util/ad-hoc/2026-08-26_push_signed_fixup.py`.
- **Both send WHOLE FILES.** Re-check `git log HEAD..origin/main -- <path>` immediately before
  every push or you silently revert someone else's merged change.
- **Verify a merge in two steps** — and this arc got it wrong: `util/safe_merge.py` prints the
  **HEAD** sha, not the squash commit (§6). Take the squash from
  `gh api repos/<owner>/<repo>/pulls/<N> --jq .merge_commit_sha`, then confirm the CONTENT is on
  `main`.
- **`safe_merge` can exit 0 without merging**, and an armed auto-merge on a `behind` PR waits
  forever under a `strict:true` ruleset — see §8.
- **Environments** (round 39 §5.15): juniper-data → `/opt/miniforge3/envs/JuniperData/bin/python`;
  juniper-cascor → `.../JuniperCascor1/bin/python` (**trailing `1`**); juniper-canopy → `conda run
  -n JuniperCanopy1` (invoking its python directly skips the hook that strips the Rust `libtorch`
  path). juniper-recurrence has **no** environment.
- **The sandbox refuses shell STRUCTURE** (round 39 §5.13): loops, `&&` with a heredoc,
  `${PIPESTATUS}`, unquoted vars in an option position, and any `git`/`gh` argument computed at
  runtime. Put multi-line edits in a script under `util/ad-hoc/` and run it by absolute path;
  `/tmp/` is prohibited for script source.

"""


def apply(path: Path, subs: list[tuple[str, str]]) -> int:
    text = path.read_text(encoding="utf-8")
    for old, _new in subs:
        if text.count(old) != 1:
            print(f"REFUSED  {path.name}: anchor found {text.count(old)} times, wanted 1")
            print(f"         {old[:100]}")
            return 2
    for old, new in subs:
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print(f"applied {len(subs)} substitutions to {path.name}")
    return 0


def main() -> int:
    if (rc := apply(R39, R39_SUBS)) != 0:
        return rc
    if (rc := apply(R40, R40_SUBS)) != 0:
        return rc

    text = R40.read_text(encoding="utf-8")
    if R40_NEW_SECTION in text:
        print("§4a already present")
        return 0
    if text.count(R40_NEW_SECTION_ANCHOR) != 1:
        print(f"REFUSED  §4a anchor found {text.count(R40_NEW_SECTION_ANCHOR)} times, wanted 1")
        return 2
    R40.write_text(text.replace(R40_NEW_SECTION_ANCHOR, R40_NEW_SECTION + R40_NEW_SECTION_ANCHOR, 1), encoding="utf-8")
    print("inserted §4a (how work gets landed)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
