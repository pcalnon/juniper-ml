# Juniper ecosystem — consolidated development plan, v2 (the re-plan of 2026-11-12)

- **Project**: Juniper ecosystem (all repositories; the plan lives in juniper-ml)
- **Author**: Paul Calnon
- **Date**: 2026-11-12 (UTC; 2026-11-11 in America/Chicago)
- **Version**: 2.0.0
- **Status**: **DRAFT, NOT VALIDATED.** Compiled by session `64ddc378` ("consolidated development project") in worktree `.claude/worktrees/vectorized-wandering-planet`, and paused at the owner's request before any independent review (Validation record). Treat every row as a lead to re-check, not as a finding.
  - It is the re-plan that v1 prescribes ("re-plan after Wave 1", v1's Out of Scope and §12). v1's Waves 0–1 have not exited (§3.4), but v1's state is a month old for ten of its twelve paths, and its three-to-five-week window for those waves ended about 2026-11-08.
  - Planning only: this plan changes no code, authorizes no merge, release or host action, and carries no approval.
- **Owner**: Paul Calnon
- **Relation to v1**: v1 is `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, at v1.15.15 on `main` (`348777f4`).
  - v2 replaces v1's **state** (§2), **order of work** (§4) and **owner packet** (§6), from the date above.
  - v1 stays the record of everything else: its 381 item IDs and their sources, its cross-cutting items, its release rows and their notes, its hazards H-1 to H-23, and its validation record. v2 cites them and does not restate them.
  - v2 does not edit v1. A session that records into v1 (the R-OBS-SC-2 follow-ups owe v1.15.16) goes on doing so until the owner rules otherwise (§7.4, item 20).
- **Template**: `notes/templates/TEMPLATE_DEVELOPMENT_ROADMAP.md`, as v1 adapted it.
- **Snapshot**:
  - The probe ran at 2026-11-12T02:09Z over the window that starts at v1's final census, 2026-10-10T21:30Z. The files in `EV/` are that run. A first run at 01:50Z read 484 commits and 48 open PRs; the differences are noted where they matter.
  - Handoffs were read as they stood on `main` at `348777f4` (2026-11-12T01:36Z).
  - Host reads (worktree and transcript checks) ran between 01:50Z and 02:09Z on the Linux host.
  - Four arcs had a live session while this was compiled (§2). Their state moves by the hour: re-probe before acting on any row.
- **Evidence**: `reports/2026-11-12_consolidated-development-plan-v2/` (cited as `EV/`), and the probe that wrote it, `util/ad-hoc/2026-11-12_consolidated_plan_v2_state_probe.py`.

## Documents referenced

Short forms used below. `HO/` = `prompts/thread-handoff_automated-prompts/`; `EX/` = `reports/2026-10-04_consolidated-development-plan/`; `EV/` = `reports/2026-11-12_consolidated-development-plan-v2/`.

| Short form | File |
| --- | --- |
| v1 | `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.15.15) |
| the probe | `util/ad-hoc/2026-11-12_consolidated_plan_v2_state_probe.py`; its outputs are `EV/state-probe.txt` and `EV/state-probe-with-merges.txt` |
| v1's census | `util/ad-hoc/2026-10-05_ecosystem_live_census.py` |
| `…INDEX_consolidated-development-paths.md` | `HO/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md` |
| `…round-13-rebaseline-drift-then-pr.md` | `HO/HANDOFF_2026-10-10_consolidated-development-plan-reconcile-round-13-rebaseline-drift-then-pr.md` (v1's last dedicated handoff; consumed) |
| `…backup-phase-d-sitting.md` | `HO/HANDOFF_2026-11-11_backup-phase-d-sitting-steps-11-13-done-ac4-drill-next.md` (P1's current handoff) |
| `…canopy-phase16-round33.md` | `HO/HANDOFF_2026-11-12_canopy-phase16-round33-frozen-round34-relaunch-next.md` (P2's current handoff) |
| `…r-obs-sc-2-follow-ups.md` | `HO/HANDOFF_2026-11-12_r-obs-sc-2-follow-ups-four-ruled-four-open.md` (P3's and P4's current handoff) |
| `…flood4-seven-landed.md` | `HO/HANDOFF_2026-11-11_flood4-seven-landed-validations-pending.md` (P15's current handoff) |
| `…open-pr-sweep.md` | `HO/HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md` (the launcher arc's last handoff; flood 4's first) |
| `…turing-check-wording.md` | `HO/HANDOFF_2026-10-30_turing-check-wording-fixed-owner-steps.md` (P13's current handoff) |
| `…RECOVERY-PLAN.md` | `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` |
| `…INTEGRATED-DESIGN.md` | `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` |
| `…E2E-VALIDATION-EVIDENCE.md` | `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` (the canopy ledger) |
| `…DEFECT-REGISTER.md` | `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` |
| `…EQUITIES-PLAN.md` | `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.24) |
| `…TURING-PLAN.md` | `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` |
| `…SIGNING-PLAN.md` | `notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md` |
| `…K8S-NODE-AUDIT.md` | `notes/JUNIPER_2026-10-27_JUNIPER-ECOSYSTEM_TURING-K8S-NODE-AUDIT.md` |
| `…FLOOD-3-DISPOSITION.md` | `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` |
| `…FLOOD-4-DISPOSITION.md` | `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md` |
| `…REPO-TMP-DIRECTORY-CONVENTION.md` | `notes/JUNIPER_2026-10-26_JUNIPER-ECOSYSTEM_REPO-TMP-DIRECTORY-CONVENTION.md` (on juniper-ml#2360's branch only; not on `main`) |
| `…SECURITYFS-RCA.md` | `notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-SECURITYFS-UNMOUNT-ROOT-CAUSE-ANALYSIS.md` |
| `…PARTITION-PROVENANCE-SPEC.md` | `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md` |
| `…LOGGING-REDESIGN-ROADMAP.md` | `notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md` |
| `…HARNESS-DESIGN.md` | `notes/JUNIPER_2026-09-22_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-DESIGN.md` |
| `…GROUNDING-INVENTORIES-RECORD.md` | `notes/JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-GROUNDING-INVENTORIES-RECORD.md` |
| `…CONSENSUS-PROCEDURE.md` | `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` |

**How each statement is marked.** A state claim ends with the mark of where it came from:

- **[P]** — measured for this plan on 2026-11-12: by the probe (`EV/state-probe.txt`), or by a read-only command this plan names.
- **[H]** — taken from the path's current handoff, which the row names. Not re-derived.
- **[V1]** — carried from v1 at v1.15.15, from the section named. Not re-derived, and stale wherever v1 says its own text is.

A row with no **[P]** is a pointer, not a measurement.

---

## 1. Where the consolidated plan stands

### 1.1 What was built

1. **2026-10-03.** Nineteen handoffs were consolidated into eleven development paths, P1–P11 (`…INDEX_consolidated-development-paths.md`).
2. **2026-10-04.** v1.0.0 ordered those paths and a twelfth, P12, into one queue: 375 extracted item IDs, some 140 owner-decision rows, ten extraction reports (`EX/extraction-*.md`).
3. **2026-10-04 to 10-10.** Fourteen consensus rounds validated it (v1's Validation record; `EX/round*-reconciliation.md`).
4. **2026-10-10.** v1.12.1 landed as a record through juniper-ml#2214. v1.13.0 re-baselined it to that day's final census (21:30Z), and round 14 ran on it.
5. **2026-10-24.** The owner ruled "correct and land, with no round 15". v1.14.0 landed through juniper-ml#2318, and validation ended.
6. **2026-10-25 to 11-09.** Fifteen records, v1.15.0 to v1.15.15, each written by the P12 arc or its R-OBS-SC-2 successor about its own rows. No round checked any of them (v1's Status says so of each).

### 1.2 What stalled

- **No session has owned the plan as a whole since 2026-10-24.** Its last dedicated handoff is `…round-13-rebaseline-drift-then-pr.md`, which session `560c1ec5` consumed. Nothing succeeded it.
- **v1 says of itself that it is stale.** v1.14.0 "takes in no drift after 2026-10-10T21:30Z"; v1.15.0 takes in P12's drift only, and "the rest of the drift (P1, P2, P3, the turing host plan, flood 3's record) is not taken in" (v1, Snapshot).
- **The re-plan never ran.** v1 forbids status tracking in its own file and prescribes a re-plan after Wave 1 (v1, Out of Scope; §12's risk table).
- **Three arcs started that v1 does not carry at all**: the turing host bring-up with commit signing (from 2026-10-15), the repository `tmp/` convention (from 2026-10-26), and a fourth Cursor flood (from 2026-11-04).

### 1.3 What happened meanwhile, measured

- **487 commits** reached `main` across the nine public repositories since v1's final census: 221 in juniper-ml, 63 in juniper-canopy, 42 in juniper-data, 39 in juniper-cascor, 32 in juniper-recurrence, 27 each in juniper-data-client and juniper-deploy, 20 in juniper-cascor-worker and 16 in juniper-cascor-client. 183 of them are attributed to a bot account. **[P]**
- **23 versions reached PyPI** in the window, across twelve packages (§5). **[P]**
- **41 PRs are open, all in juniper-ml**: 40 Cursor drafts and #2360. **[P]** At 01:50Z juniper-data had six more (five Cursor drafts and #534) and juniper-canopy one (#814); none of the seven was open at 02:09Z.
- v1's census reads one page of 50 commits per repository and says so when the page is full. Over this window juniper-ml and juniper-canopy fill it, so this plan's probe pages through (`EV/state-probe-with-merges.txt` lists every commit).

### 1.4 What this plan is

- One current map: each path's state with its source, v1's Waves 0–1 item by item, what decayed while the plan was stalled, the order of work from here, the release train, and one owner packet.
- It is built from each path's newest handoff and a live probe. It does not re-derive v1's 381 IDs one by one (§9 lists what it did not re-probe).
- Each path's handoff stays that path's operating manual, as under v1.

---

## 2. State at a glance (2026-11-12)

"Session" is what `ListAgents` showed at 01:40Z: four arcs had a live, busy session. P13 to P17 are paths v1 does not have.

| Path | State | Next | Tier | Session |
| --- | --- | --- | --- | --- |
| P1 backup | Backups run again in all three tiers. Phase D's sitting is through step 13; four acceptance checks are open, and retention is still "keep all". | AC-4 drill 1 | T0 | live |
| P2 canopy | canopy 0.9.0 ships the P0 fix. The ledger's Phases 12–15 are on `main`. Phase 16 is not: it is frozen locally after 33 consensus rounds. | Round 34; then land Phase 16 | T1/T2 | live |
| P3 register | P3-07 shipped as R-OBS-SC-2. Four follow-ups are ruled and in flight. Eight gate items have no PR and no session. | The follow-ups; then the unowned gates (§4.2) | T0/T1 | live, follow-ups only |
| P4 release | 23 PyPI uploads in the window. No running image carries observability 0.4.2 yet. Five cuts are owed or unruled (§5). | juniper-ml 0.11.5 | T1 | the P3 session |
| P5 partition | Dormant. Spec v3 has not started. | P5-01 | T2 | none |
| P6 perf | Dormant. APD-ML-002 closed on 2026-11-01; PF-2 and PF-3 are where v1 left them. | P6-01; the owner menu | T2 | none |
| P7 logging | Dormant since 2026-10-04. | P7-01 | T2 | none |
| P8 harness | Dormant since 2026-10-03, and its round-1 evidence has expired (§3.5). | P8-03, re-grounded | T2 | none |
| P9 CI budget | Dormant. Budgets were last measured on 2026-09-22/23. | P9-13 | T0/T2 | none |
| P10 ci-tools | Dormant. ci-tools 0.9.1 is on PyPI. | P10-04 | T2 | none |
| P11 k8s | Closed in juniper-ml (v1 §2). | — | — | — |
| P12 equities | Phase 1 is done and released. M1 is 2026-11-21. W5.7 is unreleased until R-DATA-2. | R-DATA-2; A1's open limbs | T1/T2 | none by that name |
| P13 turing and signing | New. 0 of 7 readiness gates pass, each on an owner step. | The owner's steps 1–9 | T3 | none |
| P14 `tmp/` convention | New. Eight sibling PRs are merged; juniper-ml#2360 is open. | Land #2360 | T1 | the owner |
| P15 Cursor fleet | New (v1's XC-FLEET grown into an arc). Flood 3 is closed. Flood 4 is mid-landing, with 40 drafts open. | Re-run five stopped items; land the queue | T1/T2 | live |
| P16 yamaguchi incident | New, closed. Remediated on 2026-11-08. | — | — | — |
| P17 juniper-harcot | New. A tenth active repository, private. | — | — | — |

### 2.1 Notes by path

**P1 backup** (`…backup-phase-d-sitting.md`; `…RECOVERY-PLAN.md`)

- v1's first headline, "no backup has completed since 2026-09-18", no longer holds. **[H]**
  - Phase C ran. Tier 2 wrote and verified its first set since 2026-08-28 (AC-10), and Tier 3 its first full set; one Tier 3 archive was restored and matched the live tree (AC-11, 2026-10-29) (`…RECOVERY-PLAN.md`, its status line of 2026-10-29).
  - Tier 1 ran again on 2026-11-07 (run `20261107T212908Z`), and the owner accepted AC-3 on 2026-11-08, with a new baseline of 1,882,694 files and 280.40 GiB.
  - About 1.05 million of those files are in juniper-ml's `.claude/worktrees` (234 worktrees). Excluding that tree was rejected, because uncommitted work lives there. So Tier 1 now holds a copy of every session's worktree, which v1's XC-PRESERVE did not have.
- Passing: AC-1, AC-2, AC-12, AC-13 and the watchdog (`OK` at its 12:00 check on 2026-11-08). **[H]**
- Open, in order: the process change (an acceptance probe and a finish script), AC-4 drill 1, the deletion table's recompute, the aside copy, the retention restore, AC-4 drill 2, AC-5, AC-6, AC-7's durable fix, and the record PR into `…RECOVERY-PLAN.md` §6.3.1. **[H]**
- After Phase D: Phase E (v1's P1-19), O-11, D-12, finding 15 and AC-14's Phase E ruling. **[H]**
- The session's limits bind as before: it never starts or stops a unit, runs a Duplicati binary, or reads a secret file (v1's H-7, H-20).

**P2 canopy** (`…canopy-phase16-round33.md`; `…INDEX_consolidated-development-paths.md`, its P2 row)

- On `main`: Phase 12 (the pacer, canopy#731, closes F-CANOPY-055, -058 and -068), Phase 13 (the manual sweep), Phase 14 (F-CANOPY-069 filed) and Phase 15 (F-CANOPY-069 and -028 fixed), all between 2026-10-19 and 10-21. Items 34 and 20 are done in canopy#762 and canopy#763. **[H]**
- Phase 16 records those two items and the Linux host's checks. It exists only as local, unsigned commit `4963cb52` on branch `docs/canopy-e2e-phase16` in worktree `.claude/worktrees/distributed-giggling-clarke`: 198 paths, no remote branch, no PR. **[H]**
- Round 34's two lanes stopped at the account's weekly limit on 2026-11-09 without reporting. **[H]**
- Triage: 86 / 64 / 1 / 2 / 19. **[H]**
- Three legs of state it depends on are unruled (§6.1): whether juniper-ml#2360 lands before Phase 16; a rule that lets O13's list converge; the menu for 14 undated drivers' defaults.
- After Phase 16: items 18, 19 and 21 (canopy fixes), 27, 25 and 28 (the trio), 29, 26's second step and 33. Y2 wave 2 is stalled at round 15. **[H]**

**P3 register and P4 release** (`…r-obs-sc-2-follow-ups.md`; v1 §2, §5)

- Shipped: P3-07 (juniper-ml#2523), observability 0.4.2 and service-core 0.7.2 (PyPI 2026-11-09), and the second lock round in all four consumers (data#525, cascor#748, canopy#806, recurrence#233). **[V1]** **[P]** for the PyPI and merge facts.
- Ruled on 2026-11-09 and being carried out by session `6e3bdef0`: floors go in each consumer's next release PR; a `[tools]` floor PR, then juniper-ml 0.11.5; register row APD-ECO-016 with one fix PR per fork and a drift guard; the telemetry opt-out ported to cascor and canopy. **[H]**
- v1.15.16 is that session's to write. **[H]**
- **No PR and no session**: P3-01 and P3-02 (the data fix-forward's rounds), P3-03, P3-09, P3-05 (the validation of cascor#690), P3-08 (cascor's Sentry F-fixes), P3-06 (the validation of canopy#685) and P3-11 (the closes PR). **[V1]**, with two checks:
  - `…DEFECT-REGISTER.md` on `main` still calls APD-ECO-013 and -014 RESERVED, and has no APD-ECO-016. **[P]**
  - No commit in the window names any of the eight. **[P]** (a title search of `EV/state-probe-with-merges.txt`; it cannot prove absence).
- These eight gate R-DATA-2 and R-CASCOR (§5), so they are the release train's critical path.

**P5 to P10, the dormant lanes**

- **P5.** `…PARTITION-PROVENANCE-SPEC.md` was last touched on 2026-11-06, to v0.2.2, by P12's rulings only. **[P]** The worktree v1 names as the only home of juniper-data#434's round-3 fixes is still present, and no juniper-data commit in the window names them. **[P]** P5-11 is done (juniper-ml#2381). **[V1]**
- **P6.** No perf PR merged in the window. **[P]** PF-2 axis 1 needs a cascor field, PF-3 a quiet window, and APD-ML-003 to -006 one owner menu. **[V1]**
- **P7.** No commit has touched `…LOGGING-REDESIGN-ROADMAP.md` since 2026-10-04, and no cascor logging PR merged in the window. **[P]** Round 2's reconciliation is not on `main`; Lane A's four hunks exist only in worktree `temporal-snacking-zebra`, which is present. **[V1]** **[P]**
- **P8.** No commit has touched `…HARNESS-DESIGN.md` or `…GROUNDING-INVENTORIES-RECORD.md` since juniper-ml#2110. **[P]** Round 2 was never relaunched. **[V1]**
- **P9.** No budget PR merged in the window. **[P]** S0.10's re-measure of the nine CI budgets has no record. **[V1]**
- **P10.** ci-tools 0.9.1 reached PyPI on 2026-10-21. **[P]** The banner edit, the recurrence floor and X7 were not re-probed. **[V1]**

**P12 equities** (`…EQUITIES-PLAN.md`; v1's XC-P12)

- v1 is current on P12 to 2026-11-09, so this plan adds nothing to it. Its milestones stand: M1 2026-11-21, M2 and M3 2026-12-12, M4 2027-01-15. **[V1]**
- Its open owner items are A1's limbs (§6.3, item 13). **[V1]**

**P13 turing host and commit signing** (`…turing-check-wording.md`; `…TURING-PLAN.md` v1.4.11; `…SIGNING-PLAN.md`)

- Between 2026-10-16 and 10-30 the arc landed the host gates and their tools (the alias, path and host-state checks; the agent guard, 1.2.0 on 2026-10-30; the SME agents; the Serena pin). **[H]** **[P]** for the merges.
- Readiness is 0 of 7 gates. Each failure names an owner step: transport (A1 to A3), the signing chain (K13 first, then K10), SIP and key-export files, Docker Desktop's upgrade (D3), the parent guide file, the network (F2, A6, iperf3) and memory. **[H]** (2026-10-30; not re-measured, because turing is another host).
- No turing session was live on 2026-11-12. **[P]**

**P14 the repository `tmp/` convention**

- The rule is the owner's directive of 2026-10-26: no file is written under the system temp directory; each repository uses its own gitignored `tmp/`.
- Merged on 2026-10-27/28: one PR in each of juniper-data, -data-client, -cascor, -cascor-client, -cascor-worker, -canopy, -deploy and -recurrence. **[P]**
- Open: juniper-ml#2360. At 01:50Z its head was `397a13bc`, MERGEABLE and BEHIND, with auto-merge not armed; at 02:09Z the probe shows auto-merge armed. **[P]**
  - Its design note (`…REPO-TMP-DIRECTORY-CONVENTION.md`) and its gate (`util/tmp_path_literal_check.py`) exist only on its branch. Neither is on `main`. **[P]**
  - The juniper-ml primary checkout sits on that branch, so the owner is working it there. **[H]** (`…canopy-phase16-round33.md`)
- It collides with two arcs: Phase 16's gate baseline (P2), and turing's G1 mutation checks, which must be re-run when it lands (`…turing-check-wording.md`, "Agent next" item 9).

**P15 the Cursor fleet** (`…flood4-seven-landed.md`; `…FLOOD-3-DISPOSITION.md`; `…FLOOD-4-DISPOSITION.md`)

- **Flood 3** is closed: `…FLOOD-3-DISPOSITION.md` reads "Complete", with thirteen follow-up updates to 2026-11-04. **[P]** (its header on `main`).
- **Flood 4** began as an open-PR sweep on 2026-11-04: 74 open PRs at its census of 2026-11-06 (`…open-pr-sweep.md`). **[H]**
  - Landed: the round-1 carriers (juniper-ml#2517 and #2519, with data's and canopy's), the record (juniper-ml#2530), and seven round-2 fixes on 2026-11-09. **[H]** **[P]** for the merges.
  - Stopped by the weekly limit on 2026-11-09: five work items, whose partial work is on disk in worktrees only. **[H]**
  - Open: nine decisions, D1 to D9, which the owner asked to clarify before answering. **[H]**
- 40 Cursor drafts are open, all in juniper-ml; juniper-data's five were open at 01:50Z and none at 02:09Z. juniper-ml#2484 is stacked on a non-`main` base. **[P]**
- The launcher arc is closed (juniper-ml#2405, #2438, #2468). **[H]** (`…open-pr-sweep.md`)

**P16 the yamaguchi securityfs incident** (`…SECURITYFS-RCA.md`)

- `make up` in juniper-deploy created every container and started none. The root cause is established, and the owner remediated it on 2026-11-08 (the record's Status line). **[P]** (that line on `main`).
- Recorded through juniper-ml#2516, #2518 and #2521, with a preflight in juniper-deploy. **[P]**

**P17 juniper-harcot**

- A tenth active repository since 2026-11-10: the private equities-analysis repository built on juniper-recurrence (the wording of juniper-ml's own naming convention, which juniper-ml#2538 extended with its token). **[P]** It is private, so this plan records no state of it.
- Every sweep that starts from "the nine repositories" now misses one. v1's census, this plan's probe and v1's H-18 all say nine.

---

## 3. v1's Waves 0–1, item by item

"No record" means: no handoff names it done, and no commit title in the window names it. That is a title search, so it cannot prove absence; the path's session confirms before anyone acts on it.

### 3.1 The owner sitting (v1 §4, Wave 0, items 1–8)

| # | v1's item | State | Mark |
| --- | --- | --- | --- |
| 1 | The rulings the host steps need (O-10, N-1, N-2; O13) | Ruled in the backup arc (`…RECOVERY-PLAN.md` §6.6, rulings of 2026-10-25 to 10-28). O13: the trio was stopped on 2026-10-30, and four primaries got a pull rule on 2026-11-03. The canopy and juniper-ml primaries are open. | [V1] |
| 2 | Phase C, steps 1–7 | Done. | [H] |
| 3 | Tier 2 install | Done; Tier 3 too. | [H] |
| 4 | The T0 snapshot timer | Re-enabled on the recovered server at Phase D step 13 (`yamaguchi-server-db-snapshot.timer`). | [H] |
| 5 | The watchdog redeploy | Working: `OK` on 2026-11-08. | [H] |
| 6 | XC-SENTRY (a) or (b); XC-CRED | The trio is stopped, and the deployed stack's DSNs are empty. Whether a Sentry-side scrubbing rule exists is not recorded. XC-CRED: Phase D rotated the UI credential and escrowed the settings key; the rest has no record. | [H] |
| 7 | XC-LEAKS settings | **Not done.** juniper-deploy has secret scanning and push protection off. Non-provider patterns are off in all nine. | [P] |
| 8 | The other Group A rulings | A9 is ruled in full, and A6 by the 2026-11-03 ruling. A1's remainder, A4, A5's O2 and O7, P4 D-4 and D-5, A7 and A10 are open (§6.3). | [V1] |

### 3.2 The session items (v1 §4, Wave 0, S0.1–S0.14)

| Item | v1's work | State | Mark |
| --- | --- | --- | --- |
| S0.1 | XC-PRESERVE: copy every single-copy artifact | Every location v1 names that could be checked is still there, and Tier 1 now backs the worktrees up. Four rows were lost to expiry (§3.5). No manifest has a record. | [P] |
| S0.2 | XC-LEAKS session work | The configs of juniper-data, -canopy and -deploy now find (data#490, canopy#764, deploy#259; 2026-10-25). **juniper-recurrence still runs no gitleaks**: no config, no workflow that names it, no hook. | [P] |
| S0.3 | P1 follow-through: the small `docs/REFERENCE.md` PR and the after-the-fact reads | No record. The window H-23 guarded closed when P0 step 10's restart ran, so the docs PR's text needs re-deriving before anyone writes it. | [V1] |
| S0.4 | P3's Sentry F-PRs | P3-07 merged. P3-08 has no record. | [V1] |
| S0.5 | P3-06, the validation of canopy#685 | No record. | [V1] |
| S0.6 | P3-11, the closes PR | Not done: APD-ECO-013 and -014 are still RESERVED. | [P] |
| S0.7 | The recurring fleet check | Overtaken: flood 4 arrived and has its own arc (P15). | [H] |
| S0.8 | P2-16, F-ML-002 | No record. | [V1] |
| S0.9 | XC-P12's asks | Overtaken: ruled on 2026-10-17 and 10-18. | [V1] |
| S0.10 | P9-13, re-measure the CI budgets | No record. | [V1] |
| S0.11 | F-S10's tests | Unwritten (`…r-obs-sc-2-follow-ups.md`, Q3). The per-lock probe stood in for them at the second lock round, by the owner's ruling. | [H] |
| S0.12 | A6's list | Overtaken by the 2026-11-03 ruling on the `MEMORY.md` compaction. | [V1] |
| S0.13 | The reads of juniper-ml#2183, #2185 and #2196 | No record. A10 still waits on them. | [V1] |
| S0.14 | XC-CRED's count-only search | No record. | [V1] |

### 3.3 Wave 1 (v1 §4)

| Block | State | Mark |
| --- | --- | --- |
| Security delivery | Steps 1–4 are done: P3-07, the D-03 ruling for the lock PRs, R-OBS-SC-2, the second lock round. Step 5 is open: the owner's upgrade of the trio's environments, a recorded pass, the restart. | [V1] |
| F-S10 delivery | Recurrence's relay is fixed from recurrence 0.6.0. The data-client and cascor fixes still wait for A1; data-client 0.6.0, which carries the unfixed text, has been served since 2026-10-17. | [V1] [P] |
| Data | P3-01 to P3-03, P3-09 and P5-09's PR are open. R-DATA-2 is ruled to be 0.18.0 and is owed. | [V1] |
| Cascor | P3-05 and P3-08 are open. cascor 0.12.0 and 0.13.0 shipped ahead of them; whether a fix-forward is owed is unruled. | [V1] |
| Canopy | P3-06 is open. R-CANOPY-A shipped as canopy 0.9.0; the second cut (P4 D-4) is unruled. | [V1] |
| P5-11 | Done (juniper-ml#2381). | [V1] |
| Tier-1 recovery | Phase B merged; Phase D (P1-18) is under way, through step 13. | [H] |
| The P2 ledger | Phases 12–15 are on `main`. Phase 16 is in rounds. P2-03 and P2-04 have no record. | [H] |
| Records (P4-01, P4-02, P4-04) | No record. | [V1] |
| After R-DATA | Done, except P4-06's read of whether the notify run exercised 0.17.0: the notify ran, the pins moved, and R-ML-a shipped inside juniper-ml 0.11.0. | [V1] |

### 3.4 The exit for Waves 0–1 (v1 §4, "Exit for Waves 0–1")

| v1's exit condition | Met? |
| --- | --- |
| A verified Tier-2 archive, and the watchdog redeployed | **Yes.** |
| Every XC-PRESERVE manifest matched | **No.** No manifest has a record, and four rows expired. |
| The XC-LEAKS configs and settings fixed, and the history scans reported | **In part.** Three configs are fixed; juniper-recurrence has none; the owner's settings are unchanged; the scans' reports were not read. |
| The Sentry F-PRs merged and validated | **In part.** P3-07 yes; P3-08 and P3-09 no. |
| The accepted F-S10 fixes merged and validated | **In part.** Recurrence's only; the rest wait for A1. |
| R-OBS-SC-2 cut, and its second lock round merged | **Yes.** |
| R-DATA-2 and R-CANOPY-A cut | **In part.** R-CANOPY-A shipped as canopy 0.9.0; R-DATA-2 is owed. |
| P1-10 merged | **Yes.** |

Three of eight are met. The waves have not exited; this re-plan is forced by the age of v1's state, not by the exit.

### 3.5 What decayed while the plan was stalled

v1 ranks decay second among its criteria (v1 §1.2). These are the deadlines that passed.

1. **Three sets of session transcripts expired before their archive PRs.** On 2026-11-12 the oldest session transcript on the Linux host, at any depth under the Claude Code projects directory, was last written on 2026-10-10 (one plugin file from April aside). **[P]** `cleanupPeriodDays` is unset, so the 30-day default applies (`…RECOVERY-PLAN.md` §6.3.1).
   - **Row j** (v1's XC-PRESERVE): the transcripts behind `…GROUNDING-INVENTORIES-RECORD.md` and P8's five round-1 reports, from sessions of about 2026-09-22. v1 dated their expiry at about 2026-10-22 and made P8-10 the item that archives them. P8 has no commit since 2026-10-03. **[P]**
   - **Row l**: the transcripts that P3's archiver re-verifies (sessions of 2026-09-23/24), due by about 2026-10-23 under P3-04. No record.
   - **Row k**: the transcripts of two backup-arc rounds archived nowhere, due by about 2026-11-02. No record of an archive PR. `…INTEGRATED-DESIGN.md`'s release limit 2 asks for a verbatim record on `main` before any purge; expiry is not a purge, but the effect is the same.
   - Tier 1 made no backup between 2026-09-18 and 2026-11-07, so it holds none of them. Whether a copy survives anywhere else was not searched.
2. **Row g is gone.** The four executor spec files and the `primer-venv` sat in a session scratchpad under the system temp directory. No directory for that session exists there now. **[P]** That is the loss the `tmp/` convention (P14) exists to stop.
3. **The owner's XC-LEAKS settings are unchanged after 39 days** (first measured 2026-10-04; item 7 of §3.1). **[P]**
4. **The CI budgets are 50 days stale** (last measured 2026-09-22/23). A stale budget makes `util/safe_merge.py` refuse healthy PRs on every path (v1 §4, S0.10). **[V1]**
5. **The account's weekly usage limit was reached on 2026-11-09 at about 16:15Z.** It stopped at least seven running agents at once: P15's five and P2's two lanes. Its reset is 2026-11-12 at 03:00Z. **[H]** (`…flood4-seven-landed.md`; `…canopy-phase16-round33.md`). v1's concurrency rule (§6 A7) was never ruled.
6. **Worktrees keep accumulating.** On 2026-11-12 there are 274 directories under juniper-ml's `.claude/worktrees` and 290 under `Juniper/worktrees`, and `git worktree list` in juniper-ml prints 317 lines. **[P]** The first figure was 234 on 2026-11-07, when that tree was more than half of Tier 1's file count (`…backup-phase-d-sitting.md`).
7. **Four repositories have drifted far from their last Release** with no cut planned: juniper-deploy 52 commits past v0.3.0 (2026-09-17), juniper-cascor-client 38 past v0.8.0, juniper-cascor-worker 32 past v0.6.1, juniper-data-client 27 past v0.6.0. **[P]** What those commits hold was not read. Within the window, more than half of each one's commits are a bot's (§1.3).

---

## 4. The order of work from here

v1's tiers and criteria stand (v1 §1.1, §1.2): loss exposure first, then decay, leverage, owner time, cost. What changed is the binding constraint. v1 named owner time; the weekly limit of 2026-11-09 shows agent capacity binds too, and the two interact: four live arcs are each waiting on the owner, and the largest of them spends its capacity on rounds that an owner ruling would end (§7).

### 4.1 Tier 0 — exposure now, or cheap prevention

| # | Item | Who | Why now |
| --- | --- | --- | --- |
| T0-1 | **The XC-LEAKS settings**: secret scanning and push protection in juniper-deploy; non-provider patterns in all nine public repositories | Owner, minutes | 39 days open; alerts are private, so it waits on nothing (v1 §3 XC-LEAKS, step 4) |
| T0-2 | **Finish Phase D's acceptance**: AC-4 drill 1, the retention restore, drill 2, AC-5, AC-6, AC-7 | P1's session and the owner | Tier 1 runs, but no restore from it has been drilled since the recovery; retention stays suspended until drill 1 passes |
| T0-3 | **Land Phase 16's frozen work, or copy it off the one worktree** | P2's session | 33 rounds of work sit in one local unsigned commit; Tier 1's daily run is its only other copy |
| T0-4 | **juniper-recurrence's gitleaks step, config and hook** | A session, after v1's step 1 scan of its history | The only public repository that scans nothing (v1 §3 XC-LEAKS; H-17) |
| T0-5 | **P3-08 and P3-09**: cascor's and data's Sentry F-fixes | Unowned (§4.2) | v1's T0 since 2026-10-04; each needs a validation round before it reaches a branch |
| T0-6 | **A1's F-S10 limbs**: accept or decline the data-client source fix and the cascor fix | Owner ruling | data-client 0.6.0 serves the unfixed error text; cascor and canopy relay it (v1, Overview 2; H-22) |
| T0-7 | **P9-13**: re-measure the nine CI budgets, report only | A session, small | A stale budget refuses healthy merges on every path |

- H-14 stays in force for every suite and service run: the host's session environment sets `SENTRY_SDK_DSN` non-empty (`…r-obs-sc-2-follow-ups.md`, Traps). **[H]**
- XC-SENTRY's interim mitigations stay in force until juniper-observability 0.4.3: 0.4.2 leaves query strings, Sentry Logs and exception values (v1 §5, R-OBS-SC-3). **[V1]**

### 4.2 Tier 1 — unblockers

1. **One owner sitting on the questions already asked** (§6.1). Four live arcs wait on it. It is the highest-leverage hour in the program.
2. **The order of juniper-ml#2360 and Phase 16** (§6.1, item 2). Each blocks the other's landing.
3. **The R-OBS-SC-2 follow-ups**, in flight: the two telemetry PRs, the three fork fixes and their register row and guard, the `[tools]` floor, juniper-ml 0.11.5, v1.15.16. **[H]**
4. **A session for the unowned gates.** P3-01, P3-02, P3-03, P3-05, P3-06, P3-08, P3-09 and P3-11 gate R-DATA-2 and R-CASCOR, and no session has them. The order v1 gives still holds:
   - P3-01 (round 2 on the rebased data fix-forward), P3-02 if needed, then P3-03;
   - P3-09, with P5-09's PR, which shares data's `[Unreleased]`;
   - P3-05 and P3-08, neither waiting on the other;
   - P3-06 now, from a fresh tree; its fix-forward waits for A1 and A4;
   - P3-11, which files the three severity-S rows. v1 also has it take in flood 3's open §4 defects; `…FLOOD-3-DISPOSITION.md`'s later updates say its follow-ups fixed those rows, so re-derive what is left before writing it.
   - One register or primer PR open at a time (v1 §8). P3's follow-up session will open one for APD-ECO-016: coordinate through `ListAgents`.
5. **The cuts that carry the new locks** (§5): unruled (§6.1, item 4's Q2).
6. **The trio**: the owner's environment upgrade, the restart gate (§6.1, item 4's Q3), then the restart. It has been stopped since 2026-10-30, and P2's items 25 and 28 wait on it.
7. **P12's M1 on 2026-11-21.** v1 records its smokes passing on recurrence 0.8.0; what M1 still lacks was not re-derived here (§9).

### 4.3 Tier 2 — lanes

| Lane | Order | Note |
| --- | --- | --- |
| P2 canopy | Round 34 → Phase 16's landing → items 18, 19, 21 → 27 → 25, 28 (the trio) → 29 → 26's second step | Lane B (Y2 wave 2) still waits on O7 |
| P15 fleet | The five stopped items → the landing queue by repository → ruling 10's ports → round 3 (#2404, #2406) → ruling 7's cleanup → the record update | A strict ruleset in each repository: one merge leaves the rest BEHIND |
| P12 equities | R-DATA-2 → M1 → P2 and P3 of its own plan toward M2 and M3 | Its plan is `…EQUITIES-PLAN.md` |
| P1 backup | The record PR → Phase E's inputs | After T0-2 |
| P13 turing | The owner's steps unblock each "Agent next" item | Nothing here is session-startable until an owner step lands |
| P5, P6, P7, P8, P9, P10 | As v1 §4 Wave 2 orders each | **Dormant.** Each needs a resume-or-park ruling (§6.4, item 21) |

**If a session slot opens**, this plan recommends, in order: the unowned gates (§4.2, item 4); then T0-7 with P9's lane; then P7-01, because its input exists in one worktree only; then P5-01; then P10-04; then P8, which must first settle what its expired evidence still supports (§3.5, item 1).

### 4.4 Tier 4 — host time

- PF-3 still needs a quiet window (v1 §7.2). The trio is stopped, but the host is not idle: four canopy legs listen (`:8052`, `:8053`, `:8058`, `:8059`), and a juniper-deploy stack has run for about two days. **[H]**
- Those four legs are guarded: check them against `ss` before any reaper run (`…canopy-phase16-round33.md`).

### 4.5 Tier 5 — long arcs

As v1 §4 Wave 4, with these changes: P1-19 (Phase E) is next after Phase D; P13's k8s node work (`…K8S-NODE-AUDIT.md`) joins the list; P6-08 is done.

---

## 5. Release train

Measured by the probe on 2026-11-12. "Past" is how many commits `main` is past the repository's newest GitHub Release. **[P]** throughout, except the last two columns.

| Package | PyPI newest (uploaded) | Past | Next cut | What it waits for |
| --- | --- | --- | --- | --- |
| juniper-ml | 0.11.4 (11-07) | — | **0.11.5**, a patch | The `[tools]` floor PR; then the owner's `pypi` gate (ruled 2026-11-09) [H] |
| juniper-observability | 0.4.2 (11-09) | — | **0.4.3** (R-OBS-SC-3) | Its design, whose start is unruled (§6.1, Q1) [H] |
| juniper-service-core | 0.7.2 (11-09) | — | **0.8.0**, a minor | Every consumer cap is `<0.8.0`: the caps widen first [H] |
| juniper-data | 0.17.1 (10-23) | 42 | **0.18.0** (R-DATA-2) | P3-03 and P3-09; recurrence's two bench caps widened first [V1] |
| juniper-data-client | 0.6.0 (10-17) | 27 | 0.6.1 (R-DC-PATCH-6), if accepted | A1 (T0-6) [V1] |
| juniper-cascor | 0.13.0 (10-28) | 23 | Unnumbered | Q2; P3-05 and P3-08; the fix-forward question [H] |
| juniper-canopy | 0.9.0 (10-17) | 55 | The second cut (P4 D-4) | Q2 [H] |
| juniper-recurrence | 0.8.1 (11-06) | 4 | Its next release | Carries the 0.4.2 and 0.7.2 lock; floors ride its release PR [H] |
| juniper-recurrence-model | 0.6.0 (10-20) | — | — | — |
| juniper-recurrence-client | 0.3.1 (10-27) | — | — | — |
| juniper-cascor-client | 0.8.0 (09-05) | 38 | None planned | — |
| juniper-cascor-worker | 0.6.1 (09-23) | 32 | None planned | — |
| juniper-cascor-model | 0.1.0 (06-14) | — | R-CASCOR-MODEL | P7-21; P4 D-7 [V1] |
| juniper-ci-tools | 0.9.1 (10-21) | — | — | — |
| juniper-config-tools | 0.1.1 (11-04) | — | — | — |
| juniper-doc-tools | 0.1.2 (08-30) | — | — | — |
| juniper-model-core | 0.3.2 (09-11) | — | — | — |
| juniper-deploy (no PyPI) | Release v0.3.0 (09-17) | 52 | None planned | Its image pins move with each consumer cut |

- juniper-ml and juniper-recurrence publish several packages from one repository, so "past the newest Release" is not a per-package figure there. juniper-recurrence's `main` is 4 commits past `juniper-recurrence-v0.8.1`. **[P]**
- **No running image carries R-OBS-SC-2.** Each consumer's newest Release predates its second lock PR, and the deployed stack's four service images lock observability 0.4.1. **[H]** (`…r-obs-sc-2-follow-ups.md`, Q2)
- Two rules of v1 §5 bind every cut: cap PRs land before the Release, and every PyPI deploy is a GitHub Release with archived release notes.
- The owner approves every `pypi` gate. No session does.

---

## 6. Owner packet

There is no standing merge grant: each session asks in its own first turn (v1's H-2). The numbering is new; each item names where its options and recommendation are.

### 6.1 Asked already, and waiting — the first sitting

Each of these was put to the owner by a live arc and came back to be clarified, or was never answered. Answering them unblocks the most work per minute.

1. **Per-session merge approval**, for each arc that asks. P3's follow-up session holds one (2026-11-12T00:39Z). **[H]**
2. **P2 and P14: does juniper-ml#2360 land before Phase 16?** Phase 16's landing step assumes #2360 lands last, with its gate baseline regenerated to count Phase 16's lines. If #2360 goes first, Phase 16's PR meets the gate instead (`…canopy-phase16-round33.md`, "Owner questions still open").
3. **P2: a rule that lets O13's list converge.** O13 lists every pull of `main` on a date a trio primary was pulled. The primaries were pulled in four batches after the freeze, so each round finds the list incomplete, which the arc's rule rates MAJOR. The session asks for a ruling that closes the list at a stated read time (same section). With it: O13's standing parts (who made the pulls; who may pull the canopy primary; the four legs' leave), and the menu for the 14 undated drivers' defaults.
4. **P3: round 2's four questions**, sent back on 2026-11-12 to be clarified (`…r-obs-sc-2-follow-ups.md`, "Round 2"):
   - **Q1** when juniper-observability 0.4.3's design starts;
   - **Q2** which releases carry the new locks, which also takes P4 D-4 (canopy's second cut), P4 D-5 (cascor's timing) and the cascor fix-forward question;
   - **Q3** whether the per-lock probe may stand in for S0.11's relay run at the trio's restart;
   - **Q4** who may move the juniper-ml primary, which the cascor conda environment imports.
   - Also: whether that session may cut juniper-ml 0.11.5.
5. **P15: decisions D1 to D9**, which the owner asked to clarify before answering, and whether to close #2404 and #2406 as stale (`…flood4-seven-landed.md`, "Open decisions").
6. **P1: Q1 to Q5** (`…backup-phase-d-sitting.md`, "Open questions"): AC-3's count criterion; the run of 2026-11-08 23:41Z that the owner did not start; a durable fix for AC-7; the drill sample's scope; where the three new scripts land.

### 6.2 Owner actions — minutes each, no ruling needed

7. **XC-LEAKS settings** (T0-1).
8. **The trio's environments**: `JuniperData` (its `python3.14t`) and `JuniperCanopy1` hold observability 0.4.0 and service-core 0.5.0 (`…r-obs-sc-2-follow-ups.md`, Q3). **[H]**
9. **Rotations with no record**: the TestPyPI credential captured into a transcript on 2026-09-21 (`…RECOVERY-PLAN.md`, I-31 and O-11), and turing's Hugging Face credential (`…turing-check-wording.md`, owner step 2).
10. **Turing's nine steps** (`…turing-check-wording.md`, "Owner steps"). K13 comes first in the signing chain.
11. **`pypi` gates as they arrive**, juniper-ml 0.11.5 first.

### 6.3 Carried from v1's packet, still open

12. **A7, the concurrency rule** (v1 §1.3). It now has a measurement behind it (§3.5, item 5), and §7.1 proposes its terms.
13. **A1's open limbs**: the data-client source fix and the cascor fix, with their release vehicles (T0-6); canopy#685 call (a); P6 OD-2's order for APD-ML-003 to -006; whether host recurrence legs take a port of W1.14.
14. **A4**: P3 D-04 calls (b) and (c); the four parked canopy severity-S rows, APD-ECO-009 to -012; P2 O3.
15. **A5's remainder**: O2 (provenance refs) and O7 (Y2 wave 2).
16. **A10**: keep or remove what juniper-ml#2183, #2185 and #2196 published. S0.13's reads, its input, never ran.
17. **XC-CRED** in full, and S0.14's counts (v1 §3).
18. **Group B and Group C** as v1 §6 lists them, except those v1 marks ruled. None was re-derived here.

### 6.4 New — about the program itself

19. **Who takes the unowned gates** (§4.2, item 4). Recommendation: one session, named for P3's gates, started next.
20. **Whether v2 becomes the planning surface.** If so: path sessions stop writing v1.15.x records after v1.15.16, record outcomes in their own plans and handoffs (v1's own rule), and this file's §2 is refreshed at each phase boundary by whichever session holds the plan.
    - Recommendation: yes. v1 is 365 KB, and each v1.15.x record costs a session a writer script, a re-probe and two reviewers to change a few rows.
21. **Resume or park P5, P6, P7, P8, P9 and P10.** They have been idle for five to seven weeks while v1 lists them as in-flight work that decays.
    - Recommendation: park P5, P6, P8 and P10 by name, with a date to revisit; resume P9 with T0-7; resume P7 at P7-01 only, to get its hunks out of a single worktree.
22. **The four losses of §3.5** (rows j, k, l and g): accept each with a line in its path's record, or name a search for a surviving copy.
23. **The cleanup signal** (v1's XC-CLEAN): 564 worktrees exist. Removal is the owner's word, worktree by worktree; `util/remove_stale_worktrees.bash` is never used, and `curious-plotting-hummingbird` is never swept (v1's H-6, H-16).
24. **juniper-harcot in the sweeps**: whether the census, the probe, the fleet tools and H-18's count take a tenth repository, and how a public record refers to a private one.

---

## 7. Scheduling and coordination

### 7.1 Capacity

- **The weekly limit is the calendar now.** v1's §7.1 calendar assumed 18 rounds of at least five agents. One arc alone has run 33 rounds: Phase 16's rounds cost about two lanes and two orchestrator forks each, and each fork used about 0.65 million tokens (`…canopy-phase16-round33.md`). **[H]**
- **A limit that trips stops every agent at once**, and their results never reach disk unless each wrote as it went (`…flood4-seven-landed.md`, Traps). **[H]**
- **Proposed terms for A7** (item 12), for the owner to rule:
  1. While any arc runs a consensus round, no other session launches subagents; outside a round, at most three per session (v1's proposed default, unchanged).
  2. A round's lanes write their findings to disk as they go, so a stop loses minutes, not the round.
  3. Each arc that runs rounds states an ending rule before round 1, as the owner gave v1 on 2026-10-10 (a round whose only MAJORs are of a named class may end validation). A list that cannot converge while the world moves gets a stated read time (item 3).
  4. Before launching, a session checks `ListAgents` for a round in flight, and the reset time if a limit was recently reached.

### 7.2 Collisions

v1's collision map (§8) stands. Additions:

| File or state | Arcs that edit it now |
| --- | --- |
| `docs/REFERENCE.md`, `CHANGELOG.md` | P15's carriers, P3's follow-ups (the floor PR, the guard), juniper-ml#2360, the 0.11.5 proposal |
| `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` | P3's follow-ups (APD-ECO-016) and P3-11, when it starts |
| v1's own file | P3's follow-ups (v1.15.16) only. v2 does not touch it |
| The juniper-ml primary checkout | The owner (on #2360's branch). No session moves it (Q4) |
| The gate baseline of juniper-ml#2360 | P2's Phase 16 and #2360 itself |
| `tests/test_pyproject_extras.py` | P3's floor PR and Cursor draft juniper-ml#2507 |

### 7.3 Dates ahead

| Date | What |
| --- | --- |
| Rolling | A session transcript expires about 30 days after its last write: on 2026-11-12 the oldest on the Linux host was written on 2026-10-10. An arc whose record must quote a lane verbatim archives it first |
| 2026-11-21 | P12's M1 |
| 2026-12-12 | P12's M2 and M3 |
| 2027-01-15 | P12's M4 |
| 2027-02-27 | After this date the first retention pass deletes more old filesets than the five v1 counts (v1, Overview 1); P1 recomputes that table before the restore |

---

## 8. Hazards

v1's H-1 to H-23 stand as written (v1 §11), with these notes and additions.

- **H-17, amended.** A green gitleaks step now means something in juniper-data, -canopy and -deploy. juniper-recurrence still has no step. **[P]**
- **H-18, amended.** Nine repositories are public. A tenth, juniper-harcot, is private, as is juniper-k8s: nothing of theirs goes into a public file.
- **H-23, narrowed.** Its window before P0 step 10's restart has closed. What remains is the retention restore after AC-4's first drill, with the dlists copied aside first (`…backup-phase-d-sitting.md`, steps 3 to 5).
- **H-24. No file under the system temp directory** (the owner's directive of 2026-10-26; P14). It is a tmpfs aged at ten days, and it has already cost v1's row g (§3.5).
- **H-25. A usage limit stops every agent at once** (§7.1). Write findings to disk as you go.
- **H-26. A primary checkout is somebody's working tree.** Never pull one or switch its branch. The juniper-ml primary is also what the cascor conda environment imports, so its branch is what the next cascor restart runs (`…r-obs-sc-2-follow-ups.md`, Q4).
- **H-27. A plan that is on a branch is not on `main`.** `…REPO-TMP-DIRECTORY-CONVENTION.md` and its gate are cited by the parent guide and by handoffs, and exist only on juniper-ml#2360's branch. **[P]** Check `origin/main` before citing a file as landed.
- **H-28. One host is not the estate.** Turing's state, its transcripts and its sessions are not visible from the Linux host; this plan read none of them.

---

## 9. What this plan did not re-probe

- **v1's 381 IDs one by one.** Only the items of v1's Waves 0–1 were re-dispositioned (§3), and most of those from records, not from the code.
- **Any host other than the Linux host**, and on it, no service, unit, port or backup medium. Every P1 and trio fact is from a handoff.
- **Any private repository.**
- **The content of commits.** The window's commits were counted and their titles read. No diff was read.
- **P12's M1 exit**, the composition of the four drifted packages (§3.5, item 7), and whether juniper-deploy's `main` pins what the running stack runs.
- **v1's XC-PRESERVE manifests, XC-MEM, XC-PATHS and XC-CLEAN rows**, beyond the existence checks named in §3.2 and §3.5.
- **Groups B and C of v1's owner packet.**
- **Whether any "no record" item of §3 was in fact done** under a title that does not name it.

---

## Validation record

**None yet.** No independent reviewer has read this draft: the owner paused the arc on 2026-11-12 before a review was launched. What was checked is mechanical only:

- the probe's self-test (24 of 24), and its exit status 0 on both runs in `EV/`;
- no line over 512 characters; the repository's pre-commit hooks on the new files;
- the sums of §1.3 against `EV/state-probe.txt`.

Owed before this plan is relied on, per `…CONSENSUS-PROCEDURE.md`: one lane that re-derives a sample of the **[P]** and **[H]** rows from their sources, and one that attacks §4's order and §6's packet; then a reconciliation recorded here and under `EV/`. The steps are in `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_consolidated-development-plan-v2-draft-compiled-validation-next.md`.

---

## Changed by this plan

- **Created**:
  - this file, `notes/JUNIPER_2026-11-12_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN-V2.md`;
  - `util/ad-hoc/2026-11-12_consolidated_plan_v2_state_probe.py`, the probe;
  - `reports/2026-11-12_consolidated-development-plan-v2/state-probe.txt` and `state-probe-with-merges.txt`, its outputs of 2026-11-12;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_consolidated-development-plan-v2-draft-compiled-validation-next.md`, the handoff that pauses the arc.
- **Modified**: nothing. v1 is not edited.
