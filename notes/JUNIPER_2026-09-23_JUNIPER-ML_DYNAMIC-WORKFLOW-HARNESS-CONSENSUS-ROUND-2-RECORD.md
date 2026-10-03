# Dynamic workflow harness design — consensus round 2, verbatim validator reports and reconciliation

**Project**: juniper-ml — Meta-package & automation hub for the Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon
**License**: MIT License
**Document Type**: Record (validation round; decides nothing)
**Date**: 2026-09-23
**Status**: RECORD — round 2 of the consensus on `JUNIPER_2026-09-22_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-DESIGN.md`, briefed on v3's corrections only (CON §4: "these N changes were made in response to round 1; find what they broke")
**Predecessor**: [`JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-CONSENSUS-ROUND-1-RECORD.md`](JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-CONSENSUS-ROUND-1-RECORD.md)
**Procedure**: [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
**Subject frozen at**: design v3 as written 2026-09-23 06:4xZ; no edit was made to it while a round-2 agent was running

---

## Why this file exists

Round 1 produced 59 corrections (design Appendix D and Appendix E) and one architectural change (the controller surface, Appendix E row 30). The fix pass is the least trustworthy part of a document, so round 2 attacks the corrections themselves: one Lane A agent executes the corrected mechanisms (the rewritten script, the rewritten pacing rule, the proposed V3 landed test on real squash-merged branches, the merge rule, the new transition regex) and one Lane B agent argues that the corrections broke what survived or failed to repair what they claim. The sections headed `## Report …` are copied verbatim from the agents' transcripts by `util/ad-hoc/2026-09-23_archive_subagent_reports.py`.

## Round composition

| Lane | Brief | Agent type |
| --- | --- | --- |
| A | execute: §6.2 script under a stub runtime (three scenarios), §8.1–§8.2 on fixtures incl. a reset between ticks, the §7.3 patch-id test on the six squash-merged branches Lane B1 named, `open_signed_pr.py` modes that do not yet exist, the `claudey` bypass citation, the §5.1 merge rule, the §4.3 case-2 regex over all headers, Appendix E spot-checks | `general-purpose` |
| B | refute the corrections: the timer + `-p` child surface, the heartbeat, code-created worktrees without isolation, the docs-branch model across squash merges, case 2/case 3 liveness, `VERIFY_PENDING` with one refuter, the own-token debit vs account-wide headroom, calibration resolution, `-p` visibility, Appendix E rows vs text | `general-purpose` |

