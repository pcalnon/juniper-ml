# Archive the 2026-09-24 backup-arc handoff, after three-lens consensus validation

## What this is

The thread handoff for the Juniper backup-infrastructure arc, archived per
`notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` §Step 4.

State it carries: all seven gating owner decisions **ruled** (§10.1, ml#2029); `sda` SMART **run and
passed** 2026-09-23 (ml#2041); drill ordering clarified (ml#2057); ml#2045 closed unmerged; ml#2067
open. **§8 P0 recovery is the next action and is owner-gated.**

## Validated by consensus — all three lenses returned FAIL on the first draft

Three independent agents re-probed every assertion against the live host, repo and `gh`: a
fact-checker, a procedure auditor role-playing a fresh session holding only the document, and an
adversarial reviewer. **40 findings.** All are folded in. Three-way convergence on four:

| Finding | Why it mattered |
|---|---|
| `duplicati.service` is **active**, not inactive | The draft's check said "expect inactive". A successor seeing `active` would reconcile by stopping or restarting — both forbidden, and the restart is irreversible (the 0700 gate refuses it) |
| **P0.5b runs inside P0**, immediately after step 8 | The draft put it after all of P0, which would run the first backup and both AC-4 drills with the compromised settings key still installed |
| The citation "§12 / D-12a" | §12 is Document history and holds no carried items; the register is D-12a alone |
| **The handoff was committed nowhere** | …while telling its successor "nothing is lost if the worktree is discarded". Following its own advice destroyed it. This PR is the fix |

## Two defects in the predecessor's own claims, corrected here

- **ml#2045's net effect was two files, not one.** The instrument compared `added` paths **by path**
  and `modified` paths **by content** — mismatched units, and the weaker one governed the answer. The
  file it hid is `util/ad-hoc/smart_checks_backup-sda.bash`, which differs by **+56/−50**: merging
  ml#2045 would have rewritten the very script it was named for. `util/ad-hoc/2026-09-23_pr2045_net_effect.py`
  now compares every status by content, with `--status all` as the default, and documents the defect.
- **The SMART gate closes D-12a but does NOT unblock the rotation.** §10.2 step 1 is **half done**; its
  drill half is AC-4's first drill, inside P0 step 11. The draft's past tense implied otherwise.

## Defects this validation found in the DESIGN, not the handoff

Recorded in the handoff's "What this session may do next" rather than silently fixed:

- §8 says `--no-local-db` rebuilds "from all 877 **dindex** volumes" — 877 is the *total* destination
  file count, of which 9 are dlists.
- §12 Document history has no row for ml#2029, ml#2041 or ml#2057.
- P1 step 5 still says "Re-decide D-2" and P2 step 2 "After a D-14 ruling" — both closed by §10.1.

## Changes

**Added**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_backup-arc-seven-decisions-ruled-smart-passed-p0-is-next.md`,
`util/ad-hoc/2026-09-22_backup-design-round2/PR_BODY_HANDOFF.md`.
**Changed**: `util/ad-hoc/2026-09-23_pr2045_net_effect.py` (the unit-mismatch repair).

## Verification

`markdownlint 0.42.0` (pinned hook version) — exit 0. The `../../notes/...` relative link resolves.
Every verification command in the handoff is a **separate** assertion: the draft used one OR'd
`grep -c` with a `>= 9` threshold that still passed with the entire §10.1 rulings section deleted.

## Requirements

References JR-DEP-SEC-005.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_016TcEz8juUrgh8PWf2LqZGX
