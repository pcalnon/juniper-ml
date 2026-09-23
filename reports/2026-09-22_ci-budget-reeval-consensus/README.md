# CI-budget re-evaluation — independent-agent consensus record (2026-09-22/23)

Validation of the re-evaluation of
[`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md)
(its § Re-evaluation 2026-09-22) and of the two PRs that carried it, ml#2017 and ml#2035, under
[`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md).

**This directory is evidence, not the conclusion.** The reconciliation — what each round
changed, the dissent and the owner's ruling, and what the evidence cannot support — is the
handoff's § Validation record 2026-09-22 and its "Corrections from consensus round N"
subsections. The files here are each lane's final message, copied verbatim from the lane's own
session transcript by `util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/round4-fix/archive_round_reports.py`,
which cross-checks it against the task notification the orchestrator received and refuses
credential-shaped text. A subagent's report otherwise lives only in a local, unversioned
transcript. (The first archive was taken from the notifications, which HTML-escape `<`, `>` and
`&`; round 5 caught that, and every file was re-taken from the lane's own transcript.) The only
change is presentational: a bare JSON verdict is wrapped in a `json` fence.

## Rounds

Each round after the first was briefed on the previous round's corrections only.

| Round | Frozen at | Lane | Report |
|---|---|---|---|
| 1 | ml#2017 `53d05121` | A1: history and timelines (git, PR and Actions history only) | `round1-laneA1.md` |
| 1 | ml#2017 `53d05121` | A2: the CI spans, re-measured by an independent instrument | `round1-laneA2.md` |
| 1 | ml#2017 `53d05121` | A3: file content and execution | `round1-laneA3.md` |
| 1 | ml#2017 `53d05121` | B1: omission and executability | `round1-laneB1.md` |
| 1 | ml#2017 `53d05121` | B2: argue HOLD on the budget re-pin | `round1-laneB2.md` |
| 1 | ml#2017 `53d05121` | B3: argue SHIP, and attack the soak verdict | `round1-laneB3.md` |
| 1 | ml#2017 `53d05121` | Rubric: prompt-validator, iteration 1 | `round1-rubric.md` |
| 2 | ml#2017 `d873aed6` | A: re-derive the new figures | `round2-laneA.md` |
| 2 | ml#2017 `d873aed6` | B: find what the round-1 fixes broke | `round2-laneB.md` |
| 2 | ml#2017 `d873aed6` | Rubric: prompt-validator, iteration 2 | `round2-rubric.md` |
| 3 | ml#2017 `f0b3cc73` | A: re-derive the new figures | `round3-laneA.md` |
| 3 | ml#2017 `f0b3cc73` | B: find what the round-2 fixes broke | `round3-laneB.md` |
| 3 | ml#2017 `f0b3cc73` | Rubric: prompt-validator, iteration 3 | `round3-rubric.md` |
| 4 | ml#2035 `0ffe15dc` | A: re-derive the round-3 claims | `round4-laneA.md` |
| 4 | ml#2035 `0ffe15dc` | B: find what the round-3 fixes broke | `round4-laneB.md` |
| 5 | ml#2035 `bdd60b20` | one reviewer: re-derive the round-4 claims and find what the corrections broke | `round5.md` |

## Two things the record says that the reports alone do not

- **ml#2017 merged while round 3 was running** (2026-09-23 01:17 UTC, by the owner, every
  required check green). Rounds 3 and later were recorded, and their fixes landed, in ml#2035.
- **Round 4's two lanes were cut off by the session usage limit** and resumed in place after it
  reset; each kept its own reading, and neither saw the other's report.

A lane's report is its own account. Where one conflicts with the handoff, the handoff's record
says which finding was re-derived and how it was resolved; the reports are not edited to agree.
