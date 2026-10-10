# Round 6 — Lane A3 (whole-plan consistency and residue)

<!-- markdownlint-disable -->

> **Archived verbatim.** A round-6 validation lane report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Its findings are dispositioned in `round6-reconciliation.md` in this directory. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

<!-- markdownlint-disable MD013 -->

- Instrument:
  - **Artifact**: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` v1.5.0 (`…CONSOLIDATED-DEVELOPMENT-PLAN.md` below). sha256 prefix `17a9c12de47992c2` at 13:12:19Z (start) and `17a9c12de47992c2` at 13:46:04Z (end), so it was unchanged. Window: 2026-10-05, 13:12:19Z–13:46:04Z. "Lnnn" is a line of v1.5.0. Other short forms are the plan's own; `EX/` is this directory.
  - **Read**: the whole plan; `…CONSENSUS-PROCEDURE.md`; `round5-reconciliation.md`, `round5-laneA-reprobe.md`, `round5-laneB-attack.md`; the v1.4→v1.5 diff; v1.0–v1.4 by targeted grep; §2 of all ten extraction reports, plus their item rows where cited; `round1-reconciliation.md`, round 1's Lane A2 and A3 reports and the census report (cited rows); `…RECOVERY-PLAN.md` §6.3 and §6.6; `util/install_juniper_backup_timer.bash` L196–218; `util/juniper-backup.bash` (grep); `…harness-consolidated.md` L86, L158.
  - **Ran**: `util/ad-hoc/2026-10-04_plan_id_coverage.py` (v1.0.0 → v1.5.0); `sha256sum` over the plan and the six stored versions; eight read-only helpers in the session scratchpad's `round6/a3/` (reference extraction, a stricter Appendix A parser, a tier-against-wave check, a severity counter, a short-form check, a numbered-list check, an owner-decision extractor, a context grep).
  - **Not used**: REST, the scan tool, host commands, `.env` files, credentials or transcripts.
  - Extraction-report line numbers are of the files as archived, with their 4-line header.
- Entry point: the whole of plan v1.5.0
- Sample:
  - about 420 internal reference occurrences extracted by token (§n, XC-*, A1–A9, S0.n, H-n, R-* names, steps, items, rows, Appendix rows), about 130 read in context;
  - 21 facts stated in more than one place, across about 75 statements;
  - all 141 owner-decision rows in the ten reports' §2, by ID, against §6;
  - all 34 round-5 dispositions;
  - all 375 extraction IDs (tool), re-parsed against Appendix A alone and against §4.

## Findings

| ID | Severity | Plan location (v1.5 "Lnnn") | What the plan says | Measured (where it disagrees, file:line) | Proposed correction |
| --- | --- | --- | --- | --- | --- |
| R6A3-01 | MAJOR | L396, L607 vs L611, L536, L1089 | Under vehicle (b), `juniper-ml[recurrence]` users wait "for R-ML-b to lift ml's `<0.6.0` cap" | R-ML-a (L611, L536) carries "the `[recurrence]` caps", before the P12 chain, per round 1's A2-01 (`EX/round1-laneA2-residue-P4-P5-P11-P12.md:20`) and L597's cap-first rule. Appendix B row 6 (L1089) omits them. The R-ML-b text dates from v1.4, and it overstates (b)'s cost at A1 | Pick one release for the cap; fix the rest and A1's cost of (b) |
| R6A3-02 | MINOR | L307, L949, L836, L732, L321 | "Only juniper-data's daily cron scans history" (L307, H-17). §9 and §7.1 item 6 treat only data's PR as changing a history scan | Note 2 (L319) adds ml's `workflow_dispatch` (R5B-14). `round5-reconciliation.md` L83 changed note 2 only; R5B-14's own lines (v1.4 L302, L933) stand. L321's "leaves no repository rescanning history" needs every such PR to stop | Carry note 2 into L307, H-17, L836 and item 6; make L321 conditional |
| R6A3-03 | MINOR | L617–618 | §5's order: "2. The image lock PRs, which pick up both". F-S10's vehicle (a) joins at step 3, after them | R5B-11 cited v1.4 L603: "pick up both" holds only if the patch is on PyPI first, and the vehicle needs only the fix. Its disposition (`round5-reconciliation.md` L80) changed Wave 1 only (L495–499, three independent routes) | Make item 2 conditional; take vehicle (a) out of the sequence |
| R6A3-04 | MINOR | L833, L966, L1105 | §9's gate row: "the defaults plus the interim B9-class rule, through an explicit config"; §12 and Appendix B row 22 ("the B9 rule") likewise | Unchanged since v1.4 (`plan_v1.4.0.md` L817, L950, L1089). v1.5's gate unions two scans, with the B9-class rules outside `[extend]` (L277–279), because one `[extend]` config drops "true", "false" and "null" values (R5A-05) | Restate §9 and §12 as two unioned scans, only exit 0 passing; "B9-class rules" in row 22 |
| R6A3-05 | MINOR | L438, L477–478, L483 vs L446 | S0.9, S0.10 and S0.12 come "before step 8", meaning sitting item 8 (the other Group A rulings) | The sitting's item 3 is headed "Step 8: install Tier 2" (L446), and L438 has just named §6.3's steps 1–9. Read as §6.3 step 8, Tier 2 waits on session prep: the fault R5B-06 fixed | Write "before sitting item 8", or retitle item 3 "Tier 2 install (§6.3 step 8)" |
| R6A3-06 | MINOR | L204–205, L648 | Default: three subagents "account-wide, of any kind". Enforcement: none while a round runs; "between rounds, each session caps its own at three" | By L205's own count, a per-session cap of three allows 21–24 across 7–8 sessions, so between rounds the enforcement permits what the default forbids. A7 asks the owner to accept both | Say "three account-wide during a round, three per session between rounds", or enforce the default between rounds |
| R6A3-07 | MINOR | L522 vs L831; L440 | Wave 1: P1-10 needs "O-2, O-7, O-8 and O-12 ruled". Item 1 calls all of A2 "the rulings the host steps need" | §9 (L831) omits O-2. `…RECOVERY-PLAN.md` L298: O-2 gates Phase D step 7, not B. O-2, O-7, O-8 and O-12 gate no Wave 0 host step (L303, L304, L308) | Drop O-2 from L522, or add it to L831 with a reason. Retitle item 1 "rulings that need no prep" |
| R6A3-08 | MINOR | L663–669, L751; L526, L832 | Group B is the "second sitting (gates T2 and T5)". Its P1 rulings come "before Phase D" | Phase D (P1-18) is T1 (L1000), and Wave 1 lists it (L526). §9's P1-18 row (L832) and Wave 1 omit O-1, O-13 and O-14 (`…RECOVERY-PLAN.md` L297, L309–310). O-5 and O-9 gate Phase E, not Phase D (L301, L305) | Add O-1, O-13 and O-14 to L832 and L526. Say that Group B also gates Phase D. Mark O-5 and O-9 "before Phase E" |
| R6A3-09 | MINOR | L705, L711, L713, L650, L682, L689, L714 | The same question sits in up to three groups: P12 O12 (B) and P2 O12 (C); P4-Q6 (B) and P4 D-10 (C); data#409 and cascor#582 (A9 R1, P5 OD-9, P4 D-14); P6-22 (B) and OD-11 (C) | `EX/extraction-P12-equities.md` L185 (O12 = P2 O12) and L186 (P4-Q6 = P4 item 6). `EX/extraction-P4-release-P11-k8s.md` L120 and L124. `EX/extraction-P6-perf.md` L95: OD-11 blocks P6-22 | Put each question in one group, and name the twin IDs there |
| R6A3-10 | MINOR | L400, L514, L838 | "Ship it after OD-3"; "OD-3 depends on what it surfaces" (the second in P5-11's §9 row) | L636 says every ID carries a path prefix. P5, P6 and P9 each have an OD-3 (`EX/extraction-P5-partition.md:113`, `EX/extraction-P6-perf.md:87`, `EX/extraction-P9-ci-budget-P10-ci-tools.md:70`). In P5-11's row, a reader looks up P5's; the intended one is P6's (L685) | Write "P6 OD-3" at all three |
| R6A3-11 | MINOR | L989 vs L12–13, L1245; L223 | The plan cannot support "`detect.py`, the census, the budget re-probe and the register crosscheck", which "were not run, by design" | "The census" is the live census, which ran (L12, L13, L1245). L989 is v1.0 text (`plan_v1.0.0.md:594`). There, as at L223, it meant P7's `util/ad-hoc/2026-09-22_p04_log_marker_census.py` (`EX/extraction-P7-logging.md:9`) | Name each script at L223 and L989 |
| R6A3-12 | MINOR | L337–339, L348, L660 vs L968 | XC-FLEET: "Triage them before the sweeper arms them". ml#2122 "is green 22/22, so the sweeper could merge it". The owner disposes at the mid-wave sitting | No first-sitting item disposes of a draft (L440–460), so known closes (#2129, #2122) wait for mid-wave. Triage closes nothing (H-1), yet §12 calls it the mitigation | Rule the known dispositions (L345–351) in the first sitting, or say who may close a draft sooner |
| R6A3-13 | MINOR | L497 vs L826, L605 | Trio route: "the owner upgrades the trio's environments, data-client and any cascor fix" | L826 needs the cascor fix only "merged", and R-CASCOR closes the relay "in images" (L605). The trio runs cascor from the primary (`EX/extraction-P6-perf.md:108`). O13 governs pulling it (`EX/extraction-P2-canopy.md:87`; L786). An environment upgrade does not deliver a merged fix | Add "pull the cascor primary (O13)" to the trio route in §4 and §9 |
| R6A3-14 | MINOR | L510, L802 vs L495, L727–735 | Wave 1: "P3-05 validates cascor#690, then P3-08 merges". §8: "P3-08 first" across cascor's files, including F-S10's cascor fix | `EX/extraction-P3-defect-register.md:64`: P3-08 does not depend on P3-05. Together the two rules hold P3-08 (item 2, S) and the cascor F-S10 fix (item 3, S) until item 9's round, and every F-S10 route starts "merged" (L495) | Justify or drop the P3-05 edge; exempt the cascor fix from "P3-08 first" where files differ |
| R6A3-15 | MINOR | L470 vs L642, L645 | S0.5 (Wave 0, parallel): validate canopy#685 in a round, then fix forward | `EX/extraction-P3-defect-register.md:62`: "D-04 can change scope". Call (a) is ruled at A1 and calls (b) and (c) at A4 ("P3-06 scope"), both in sitting item 8. Nothing holds the fix-forward, so a safety round can run on the wrong scope | Fix forward only after A1 and A4 rule (S0.5; §7.1 item 4) |
| R6A3-16 | MINOR | L1009–10, L1021, L1040, L1052, L1075 vs L553–563 | Appendix A places these at T2, "by lane": P2-R8, P2-R10, P3-33 (= P6-33), P6-27, P8-06, P12-35 and P12-36 | No Wave 2 lane lists them; P3-33's "register lane" (L848) omits it. P8-06, the conditional round 3 (`EX/extraction-P8-harness.md:41`), falls between P8-05 and P8-07. P12-35/36 are W3.x (`EX/extraction-P12-equities.md:146–147`), T5 under Wave 4 (L577) | Add each to its lane, or move it to the tier where §4 schedules it |
| R6A3-17 | MINOR | L857 | ml#2117 moved "P7's 09-22 source, …, P5's 09-23 and 09-09 sources, and P2's predecessor C and its 09-08 addendum target" | Four of the six have no filename, in a list sessions "must apply" (L854). That breaks the naming rule. P7's source is named in `EX/extraction-P7-logging.md:9` | Give each one's post-move `HO/HANDOFF_2026-09/…` filename |
| R6A3-18 | NIT | L1002, L1060; L1007, L1021; L1028–1029 | Merged pairs sit at different tiers: P1-24 (T3) and P9-17 (T6); P2-01 (T1) and P3-20 (T2); P2-03 (T1) and P3-21 (T2). P4-27 is at T3 (in P4-24..P4-29) and at T5 | Round 1's F14 asked for the tiers to be aligned (`EX/round1-laneA3-residue-P6-P10.md:43`). P3-33/P6-33 were aligned; these were not | Give each pair one tier, and take P4-27 out of the T3 range |
| R6A3-19 | NIT | L1008, L559 | "P2-26..P2-30 (after O7)" | P2-26 is O7 itself (`EX/extraction-P2-canopy.md:55`), so it waits on itself | "P2-27..P2-30, after O7 (= P2-26, §6 A5)" |
| R6A3-20 | NIT | L258, L152, L359 | "Method (validation rounds 1–4)"; Goals: "fix F-S10 (W1.14)"; XC-CRED: Sentry receives the key "in an exception chain" | Round 5 rewrote the method too (L277). A1 rules on three F-S10 fixes (L642). R5A-09 added the log-record route (L82, L956) | "rounds 1–5"; "fix F-S10 (the fixes A1 accepts)"; "and as a log record" |
| R6A3-21 | NIT | L602–612 | Each release name carries a version in parentheses | Eight give the current PyPI version, for example R-DATA "(0.16.0)"; R-DC-PATCH's "(0.5.1)" is the target | Prefix "PyPI", as R-OBS-SC does, and label R-DC-PATCH's version as the target |
| R6A3-22 | NIT | L715 | "P7: D4..D6, which gate XC-CLEAN" | Only D4 and D5 gate it (L410, L846). D6 is "record only" (`EX/extraction-P7-logging.md:89`) | "D4 and D5, which gate XC-CLEAN; D6" |
| R6A3-23 | NIT | L995 vs L999, L1006–1007, L1032 | "→" marks a merge into a cross-cutting or release item "(Appendix B)" | Five targets have no Appendix B row: P1-13 and P2-18 →XC-FLEET; P2-22 →XC-PRESERVE f; P5-09 →XC-PRESERVE c; P2-38 →§6 | Add rows for them, or drop "(Appendix B)" |
| R6A3-24 | NIT | L7, L170, L217, L561, L749, L800, L897, L911, L1145, L1270 | Role references without a filename: "the procedure", "the register", "the §8 STOP", "the shared run index", "the probe tool", "the API primer", "the round-6 archiver", "the reconciliation" | This breaks the naming rule. "The §8 STOP" also collides with this plan's own §8. The primer's file is named in `EX/extraction-P3-defect-register.md:23` | Name each, or add a short form to the Documents table |
| R6A3-25 | NIT | L220, L598, L808, L844 vs L569; L412 vs L1234 | "Wave 4"; "round 6" | Each term has two meanings. "Wave 4" is P4's Docker Hub wave at L220, L598, L808 and L844, and this plan's long-arcs wave at L569. "Round 6" means P9's at L412 and this plan's at L1234 | "P4's Wave 4"; "P9's round 6" |
| R6A3-26 | NIT | L616–621; L799; L466, L562; L645–646 | §5's order; §8's `docs/REFERENCE.md` row; S0.3; A4 and A5 | The order leaves out R-CASCOR-2 and R-CASCOR-MODEL (L606, L610). P6-07 edits the REFERENCE exit-code table (`EX/extraction-P6-perf.md:45`) but is missing from §8. P1-25 appears in both Wave 0 and Wave 2. A4 and A5 each ask when to cut canopy | Fill or state each gap. Keep P1-25 and the canopy cut question in one place each |
| R6A3-27 | NIT | L127 | `util/ad-hoc/2026-10-04_plan_id_coverage.py` "checks that coverage", meaning that Appendix A places every ID | The tool accepts any mention anywhere in the plan (tool L48–55), and its pattern misses `P2-R8`. A parse of Appendix A alone (this lane) finds no unplaced ID | "checks that every extraction ID appears in the plan" |

The table holds 0 BLOCKER, 1 MAJOR, 16 MINOR and 10 NIT.

## Checked and holds (short)

- **Versions.** The stored v1.0–v1.4 hash to the prefixes in the Validation record. Every lane count there matches its report: 14 reports, recounted by severity.
- **Numbering.** All 12 ordered lists run without a skip or repeat. These sequences are also complete: XC-PRESERVE rows a–q, Appendix B rows 1–22, H-1..H-22, S0.1..S0.12, §7.1 items 1–17 and sitting items 1–8.
- **References that resolve.**
  - Every internal § reference resolves, except L217 and L1270 (R6A3-24).
  - Every XC-* name is defined in §3, and every cited row (b, c, f, k, l) exists.
  - Every H-n citation matches its hazard, and every S0.n, "§7.1 item 3" and "Appendix B row 16" resolves.
  - Every R-* name used is defined in §5's table.
  - All 25 `…X.md` short forms used are defined.
- **The sitting.** It covers A1–A9 once each. A2's O-6 comes later by its own text, and A5 is split on purpose.
- **Repeated facts that agree.**
  - The five leak paths: L165, the Overview and H-22.
  - Three to five weeks: L109, L745, L753 and L1231. §7.1's arithmetic: 11 items, 22 rounds, 110 runs, 11–22 days.
  - The six DSN variables: XC-SENTRY and H-14.
  - The fleet: 42 = 28 + 8 + 2 + 2 + 2.
  - P2: 59 commits and 24 files (§2, §5, §10).
  - A9 and DC-0.6, and R-DC-PATCH before W1.4: §5, §9 and Wave 2.
  - Repository counts: nine public; ten in Tier 2 (`util/juniper-backup.bash:133`, which adds juniper-slacker); eight with secret scanning plus deploy.
- **Size.** 375 IDs equals the per-path sum. 141 owner rows ("about 140"). Six *(v)* IDs and two XC items.
- **Sources that hold.**
  - `…RECOVERY-PLAN.md` §6.3 has steps 1–9, so A3's "steps 1–9" and Wave 0's split agree, and L255 does say SKIPPED first.
  - The installer's L205–214 says OK first, with both sticks.
  - The L86 quote and "at most 3 agents" are verbatim.
  - #2122 green 22/22 and canopy #700 `dirty` are sourced (`EX/round1-laneA4-live-census.md:23`, `EX/round2-laneA-reprobe-corrections.md:37`).
- **Residue.** The tool exits 0: 375 IDs, none missing, none dropped. The stricter Appendix A parse also finds no unplaced ID.
  - Every one of the 141 owner rows reaches §6, XC-GRANT, XC-CRED or §5. Rows carried only implicitly: P1 O-4 (resolved), P1 N-4 (XC-FLEET), P2 O14 (R-DATA), P4 D-2 and D-3 (P3's D-12/D-07 and D-02/D-03), P5 OD-10, P6 OD-14 and P7 D7 (§5), P3 D-16 (P6 OD-2), P3 D-01 and P7 D1 (XC-GRANT).
  - The P1, P6 and P12 hazards (§4) map to §3 or §11, or are path-specific, as §11's first line allows.
- **Round 5.** 32 of 34 dispositions are in the place `round5-reconciliation.md` names. R5B-11 and R5B-14 are partial (R6A3-02, -03).

## Could not check

- **Live state**: GitHub and PyPI, including whether ml#2122 is still mergeable or armable; the host; and the trio's launch mode. No REST call was made.
- **The scan tool**: whether case 22's "this plan's own PR passes with 0 findings" still holds. It was measured on 36 files before v1.5 and `round5-reconciliation.md` existed. That is Lane A1's remit.
- **Recurrence and Sentry**: whether recurrence initialises Sentry through juniper-observability. If it does, vehicle (a), cut from the v0.5.0 tag, ships pre-R-OBS-SC locks in its image, and §9 L820 omits recurrence.
- **Juniper-slacker**: whether it is public. It is in Tier 2's ten, but not in the plan's "nine".
- **External documents**: the content of their sections beyond those opened above.

## What this report cannot support

- **Severities are judgement.** R6A3-01 rests on the plan's own cap-first rule and on round 1's correction. It cannot say which release the owner intends.
- **This is consistency, not correctness.** Facts were re-derived only where a disagreement needed a source; Lane A2 re-derives round 5's claims.
- **Both ID instruments are blind to some IDs.** They see `P<n>-<NN>` and `P<n>-R<NN>` only, so `P2-R8` and `P5-01a..j` were checked by eye.
- **No state after the end of the window.**

**Changed**: this file only, `reports/2026-10-04_consolidated-development-plan/round6-laneA3-consistency.md`. Scratch helpers stayed in the session scratchpad's `round6/a3/`.
