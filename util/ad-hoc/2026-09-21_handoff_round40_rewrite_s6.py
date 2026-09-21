#!/usr/bin/env python3
"""Rewrite round 40's §6 with both validation rounds' actual results.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-21
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: round-40 handoff §6

Exists as a script rather than an inline edit because the sandbox refuses a heredoc whose text
names git commands (round 39 §5.13) -- the section being written quotes the very commands used to
re-derive Lane B's findings.
"""

from __future__ import annotations

import sys
from pathlib import Path

DOC = Path(__file__).resolve().parents[2] / "prompts" / "thread-handoff_automated-prompts" / "HANDOFF_2026-09-21_defect-register-round-40-x-c-and-m-a-shipped-and-d-a-grounded.md"

START = "## 6. Validation of this arc"
END = "## 7. What this session did"

NEW = """## 6. Validation — two rounds ran, and Lane B did NOT pass this document

Procedure: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.

### Round 1 (the X-C / M-A work) — 1 of 5 lanes survived

Sized at 3 Lane A + 2 Lane B. **Four died on API rate limits and produced nothing.** Only
**Lane A3** (raw source-tree census) completed: denied the register and the handoff, it
independently reached **four** `APIKeyAuth` copies, named canopy as the only one without the
blank-key filter, stated the `_FORK_REPOS` consequence more sharply than the author had ("no
guard can reference canopy even in principle"), and established that **juniper-recurrence is a
CONSUMER of `juniper_service_core`, not a fifth copy**. Round 39 §9.7 holds the table of what
nobody attacked.

### Round 2 (this document) — Lane A verified it; Lane B found four defects

**Lane A (measurement re-creation)** re-derived §5's whole block, §3's grounding and §1/§2's
claims, and **verified every substantive one** — including by widening its own pathspec to prove
"exactly three sites" was not an artefact, confirming the recurrence zero-hit ran over a
non-empty 89-file corpus, and proving the `_FORK_REPOS` gate **by executing** a constructed
`ForkSite("juniper-canopy", ...)` rather than by reading the assertion. It found four
imprecisions, all now fixed; **one mattered** — §3 had inherited round 39 §0.1's implication that
`csv_import/generator.py:133` documents the `allow_truncation` asymmetry. It documents the
**`max_bytes`** clamp, by analogy. A D-A implementer would have edited the wrong sentence.

**Lane B (amputation / executability / false authority) did not pass it.** Three findings were
re-derived before being accepted (procedure §5.2 — a lone finding is a lead, not a fact):

1. **Two cited "squash" SHAs were HEAD shas, and neither is on `main`.** `968b9e9e` (ml#1974)
   and `435d6069` (cascor#659) are branch heads; the real merge commits are `ea24a19a` and
   `b47bd262`, re-derived with `merge-base --is-ancestor` and each PR's `merge_commit_sha`.
   **This trap is already in memory** — `reference_safe_merge_exits_zero_without_merging` says
   plainly that `util/safe_merge.py` prints the head sha, not the squash commit — and it was
   walked into anyway, inside a sentence whose whole point was "verified by content, not by a
   badge". The content claim survives (the diff between cited and actual SHA is empty, and
   content on `main` was checked separately); the *citation* was wrong. Fixed here and in round
   39 §9.8. The register cites no SHAs and is clean.
2. **The PR-opening mechanism was amputated wholesale** — no `open_signed_pr`, no
   `required_signatures`, no conda environments, no shell-structure limits, and no pointer to
   round 39 §5, which carries them. **Round 39's own round-2 validation caught this identical
   omission one cycle earlier**, and round 39 fixed it. Regressing a defect a validator already
   found is worse than never having fixed it, because the lineage then *looks* like it has the
   guard. §4a now carries the minimum and points at round 39 §5 for the rest.
3. **§9's git status was wrong twice** — the branch is `worktree-eager-seeking-milner`, not
   `main` (a worktree cannot share a branch with the primary checkout), and "carries only this
   document" was false.

A fourth finding — that §1 stated the canopy fail-closed mechanism as settled while §6 called it
unvalidated — is accepted as **framing**, and §1 is now hedged to match.

Lane B also **correctly reported the one attack that did not land**: §3's reasoning about the
memory's *"do not fix the `or settings.*`"* SURVIVED, and Lane B found the confirming passage the
author had missed — that same memory carries a later **"OWNER RULING: option 3 becomes a CALLER
right"** entry which supersedes the earlier caution and enumerates the very sites §3 lists. It
also found the memory's line numbers (`:432`/`:462`) are **stale**, and §3's re-derived
`:499`/`:529` correct.

### What remains unattacked

The canopy fail-closed mechanism, the register closes' protocol compliance, whether the guard's
two markers are defeatable, behavioural equivalence of the two loops, and the PR census — listed
in round 39 §9.7, attacked by no surviving lane. **M-A (§2) was verified by Lane A but never
adversarially attacked.** Re-run those lanes.

**Neither round passed on its first pass, and both changed this document.** That is now three
consecutive rounds in this lineage of which that is true — which is the argument for running the
lanes, not evidence that the documents are getting worse.

---

"""


def main() -> int:
    text = DOC.read_text(encoding="utf-8")
    if "Round 2 (this document)" in text:
        print("§6 already rewritten")
        return 0
    if text.count(START) != 1 or text.count(END) != 1:
        print(f"REFUSED: START x{text.count(START)}, END x{text.count(END)}")
        return 2
    start, end = text.index(START), text.index(END)
    DOC.write_text(text[:start] + NEW + text[end:], encoding="utf-8")
    print("rewrote §6")
    return 0


if __name__ == "__main__":
    sys.exit(main())
