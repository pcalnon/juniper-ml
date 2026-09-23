# 2026-09-22 re-evaluation of the 09-11 ci-tools handoff — consensus lane reports

This directory holds the lane reports of the consensus review of the 2026-09-22 status banner in
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`.
The review ran under `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.

**The record is that banner's section "Validation record for this banner"**: sizing, conduct,
verdicts, reconciliation, instrument and limits. This README indexes the files, and says only how
they were made. It restates none of the record's findings, so the two cannot drift apart.

Each file holds one lane's brief as sent, any message sent to it mid-run, and its final report as
returned, all verbatim, taken from the session's subagent transcripts. Only the round-3 lanes got a
mid-run message: a usage limit stopped all three, and each was resumed in place. A subagent's
report otherwise lives only in a local, unversioned transcript. Line numbers inside a report refer to the revision that lane reviewed.

| file | round | lane | entry point |
| --- | --- | --- | --- |
| `round1-laneA1-github-api.md` | 1 | A1 | the GitHub API only |
| `round1-laneA2-published-artifacts.md` | 1 | A2 | PyPI, GHCR and the images themselves |
| `round1-laneA3-independent-census.md` | 1 | A3 | repository contents, with its own census built first |
| `round1-laneB1-refute-conclusions.md` | 1 | B1 | attack the conclusions |
| `round1-laneB2-amputation-executability.md` | 1 | B2 | amputation and executability |
| `round2-laneB-attack-the-fix-pass.md` | 2 | R2-A (Lane B) | attack the round-1 fix pass |
| `round2-laneA-census-adequacy.md` | 2 | R2-B (Lane A) | its own instrument, then mutations of the census |
| `round2-laneA-full-read-artifact-first.md` | 2 | R2-C (Lane A) | the whole document, re-derived from primary artifacts |
| `round3-laneB-attack-the-round2-fix-pass.md` | 3 | R3-A (Lane B) | attack the round-2 fix pass, plus a ledger of every earlier finding |
| `round3-laneA-census-adequacy.md` | 3 | R3-B (Lane A) | its own instrument, then 26 mutations of the census |
| `round3-laneA-record-and-new-numbers.md` | 3 | R3-C (Lane A) | the validation record and every new number, from primary sources |
| `round4-laneB-attack-the-round3-fix-pass.md` | 4 | R4-A (Lane B) | attack the round-3 fix pass, plus a ledger of every round-3 finding |
| `round4-laneB-ship-side-steelman.md` | 4 | R4-B (Lane B, opposing brief) | argue the merge; find over-correction and noise |

The instruments the record cites are in `util/ad-hoc/`:
- `2026-09-22_ci_tools_pin_census_remote.py`, the census;
- `2026-09-22_ci_tools_pin_census_mutation_check.py`, which checks that the census's self-test
  fails when any rule it lists is removed. It proves nothing about rules it does not list.
