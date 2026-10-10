# Extraction — P2 canopy

<!-- markdownlint-disable -->

> **Archived verbatim.** An extraction report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Corrections found by validation are in the `round*-reconciliation.md` files in this directory, and the plan's §10. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

measured_at: 2026-10-04T20:52Z–21:08Z (gh REST, PyPI JSON, raw fetches of canopy `1b2dd438` and cascor `95cdc562`, reads of this worktree at `cf711cf4`, `ls`/`wc`/`find`/`sha256sum` on files. No repo scripts, tests, stacks, browsers or host-process probes.)

## 0. Sources read

Aliases used below. **10-04** = `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-04_canopy-replay-player-fixed-and-live-verified-p2-items-2-to-7-next.md`. **CONS** = `HANDOFF_2026-10-03_canopy-consolidated.md` (same directory). **INDEX** = `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`. **LEDGER** = `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, where "iN" is Phase 9's "Still owed" item N. **MATRIX** = `notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md`. **S** = `.claude/worktrees/idempotent-jumping-sparkle/reports/2026-09-23_y2-wave2-consensus/session-state/`.

| Source | What was read |
|---|---|
| 10-04, CONS, INDEX | In full. |
| LEDGER (798 KB, 9,785 lines) | **Not in full.** Read: `:9008–9786` (Phase 9 findings, instruments, consensus, still-owed); the still-owed lists of Phases 6, 7 and 8 (`:7064–7083`, `:7847–7873`, `:8448–8493`); the Phase 4 wave (`:6140–6216`); `:213–222`, `:3727`, `:6594–6619` and `:6819–6828`. Every `**F-…**` header was parsed inline with `util/ad-hoc/e2e_finding_triage.py`'s regex. The script itself was not run. |
| MATRIX | BLOCKED count; M-REPLAY rows `:863–879`. |
| `reports/2026-09-24_canopy-combined-handoff-consensus/r1/` | `DRAFT_r1.md:120–179`; predecessor A (`…phase9-landed…followup-684.md`) `:8–119`; predecessor B (`…y2-wave2-round-15-fix-pass.md`) outline only, **not read in full**. |
| `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09/` | Predecessor C (`…canopy-selection-cleanup-done-item-19-closed-y7-grounded-owner-calls-remain.md`) in full; `…four-decisions-shipped-residue-is-owner-scoped.md` § B `:142–200`; `…queue-drained-mirror-shipped-a-n2-run-owner-rulings-open.md:86–100`; `…four-rulings-shipped-cleanup-and-carry-forwards-remain.md:76–81`. |
| Design notes | `notes/JUNIPER_2026-09-02_JUNIPER-CANOPY_SELECTION-REACHABILITY-DESIGN.md` §4.3; `notes/JUNIPER_2026-09-16_JUNIPER-RECURRENCE_MODEL-PERSISTENCE-DESIGN.md` (headings only); `notes/JUNIPER_2026-08-27_JUNIPER-CANOPY_WS-MIGRATION-PLAN-JR-CAN-PERF-004.md` (grep). |
| `reports/2026-09-23_canopy-a-n2-generate-stage-train-render/README.md` | `:188–226` (O1–O8). |
| Other paths' handoffs | P3 (`HANDOFF_2026-10-03_defect-register-round-42-consolidated.md`), P4 (`…release-and-distribution-consolidated.md`) and P10 (`…ci-tools-reevaluation-consolidated.md`): P2-relevant lines only. |
| Superseded phase 7/8/9 handoffs | Remaining-work lists only. `HANDOFF_2026-09-24_canopy-combined-round-1-done-fix-pass-owed.md` was **not read**; CONS says it folded that file's F1–F22. |
| Tools | `util/release_train/detect.py` (grepped) and `registry.yaml` (canopy entry). Read, not run. |

## 1. Work items

| ID | Item | Source | Live status | Gate | Depends on | Repo(s) | Effort | Crit |
|---|---|---|---|---|---|---|---|---|
| P2-01 | File Phase 10 through consensus: F-060 (open); F-061/062 FIXED-BY canopy#685; the "Nothing was loaded" divergence; O2–O5 and O9 (ids from F-063). Archive predecessor A. | 10-04 i2; CONS §A2 | [VERIFIED 2026-10-04: header parse → LEDGER ends at F-CANOPY-059. A2 anchors hold at canopy `1b2dd438`: `dashboard_manager.py:8404`, `:8410`, `:8381`; `test_start_fresh_refusal_and_modal_text.py:42`. F-061 is now at `main.py:532`; F-062 at `security.py:391`/`:497`. cascor `manager.py` has no "Nothing was loaded". Branch `docs/canopy-e2e-handoff-2026-09-24` = `dd4413e5`, 0 PRs.] | STARTABLE | P3 item 3 (F-061/062 status) | juniper-ml | M | UNBLOCKER |
| P2-02 | In the same PR, record: F-057 P1→P2 (by its own rule); LEDGER i13's follow-up landed as canopy#684; M-REPLAY rows reconciled with the 10-04 re-drive | LEDGER F-057 `:9110–9115`, i13 | [VERIFIED 2026-10-04: canopy#684 merged `f2147403` and touched `docs/USER_MANUAL.md` and `REPLAY_V2_FAQ.md`, which now say no weight reaches the page. LEDGER header still says P1. MATRIX M-REPLAY-05 and -07..-12 read FAIL; last MATRIX commit 09-23.] | STARTABLE | P2-01 | juniper-ml | S | HYGIENE |
| P2-03 | Fix F-060: cut only at `" To accept it,"`; check that the three-option prompt fits a cap refusal | CONS §A2(a); P3 ("P2 owns fixing F-060") | [VERIFIED 2026-10-04: cut tuple at `:8410`; options at `:8442–8443`] | STARTABLE | P2-01 (id) | canopy | S | USER-FACING |
| P2-04 | Re-word canopy's two copies of cascor's withdrawn "Nothing was loaded…" sentence, if re-derivation keeps the finding | CONS §A2(a) | [VERIFIED 2026-10-04: see P2-01; cascor#690 merged `0fbb447a`] | STARTABLE | P2-01 | canopy | S | USER-FACING |
| P2-05 | Repair the F-058 census: hook executed transitions, detect fires before reset, score T-apply only while in flight, synthetic check both ways. Then run it on a `main` leg, counting evictions across 5 triggers. | LEDGER i0, i14; CONS A4 | [VERIFIED 2026-10-04: tool on main; its docstring says do not run as written. F-058 OPEN P1.] | STARTABLE (leg reads `:8101`/`:8202` only) | — | juniper-ml, canopy | M | UNBLOCKER |
| P2-06 | One redesign for F-055 + F-058 (request/ack pacer, no `running=`, covers the second Input). Real-renderer tests, live census, F-025 allow arm, correct the contradicted text, consensus, PR. | LEDGER i0; CONS A5 | [VERIFIED 2026-10-04: both OPEN P1; text at `dashboard_manager.py:472`, `:4736` and `test_poll_gating.py:313`] | BLOCKED-ON P2-05 | P2-05; a writable leg | canopy | L | USER-FACING |
| P2-07 | Hunt the F-053 latency regression `f9defb4`→`9bffaba1`: profile both builds, dispatch census by source | LEDGER i1 | [NOT RE-PROBED — LEDGER unchanged since #2083] | STARTABLE (sensitive to host load) | P6 quiet window (soft) | canopy | L | RESEARCH |
| P2-08 | Design the timestamp-only `/api/state` rewrite, keeping the phase-duration clock | LEDGER i2 | [NOT RE-PROBED] | STARTABLE | — | canopy | M | USER-FACING |
| P2-09 | Fix F-049 (the relay says "healthy" for a forgotten socket; tell a heartbeat from a payload). Also cascor#674's follow-ups in the service-core and canopy WS managers. | LEDGER i6 | [VERIFIED 2026-10-04: F-049 OPEN P2] | STARTABLE | service-core release (P3/P4) | canopy, juniper-ml | M | USER-FACING |
| P2-10 | F-057: re-land cascor#190's `weights` emitter, add `weights` to canopy's relay key set, sweep cascor for stacked PRs merged into bases that had already landed, then verify live | LEDGER i7; 10-04 "Also open" | [VERIFIED 2026-10-04: `_emit_frame` (`manager.py:1260`) adds no `weights`; `_to_dashboard_metric` (`cascor_service_adapter.py:1960`) has none; 0 open cascor PRs] | STARTABLE (cascor first) | cascor release (P4) | cascor, canopy | M | USER-FACING |
| P2-11 | Re-drive M-CANDIDATES-10/-11 with one browser context per page; the M-TOPOLOGY-16 fade half; F-038's browser-level test | LEDGER i8, i9 | [NOT RE-PROBED] | STARTABLE (needs a leg) | — | canopy, juniper-ml | M | HYGIENE |
| P2-12 | Re-derive the starvation mechanism under FIFO; correct the "lowest-priority callbacks" comment | LEDGER i11 | [VERIFIED 2026-10-04: `dashboard_manager.py:445`] | STARTABLE | — | canopy | M | RESEARCH |
| P2-13 | F1 (pause at the current index when the slider equals `slider_w`) and Phase 8's round-1 minors | LEDGER i12 | [NOT RE-PROBED] | STARTABLE | — | canopy | S | USER-FACING |
| P2-14 | Remove the stale refresh-rate config and manual text; fix the live-check instrument's six gaps before it reruns | LEDGER i13 | [VERIFIED 2026-10-04: `conf/app_config.yaml:170`, `:181`; the manual line moved to `:1346`] | STARTABLE | — | canopy, juniper-ml | S | HYGIENE |
| P2-15 | Live re-drive of the 08-28 wave's rows (C2.9-05, M-PARAMETERS-04/-05/-06, M-METRICS-03, M-WORKERS-02, C2.1-01/02, Network Editor patch rows), so F-001/-012/-013/-018/-028/-034 can close. Re-trace F-033, re-diagnose F-032, plan F-051. | LEDGER `:6141–6215` (dropped after Phase 4) | [VERIFIED 2026-10-04: all OPEN P2 by header parse; #532, #533 and #535 merged 08-28] | STARTABLE (needs a leg) | — | canopy, juniper-ml | L | HYGIENE |
| P2-16 | Fix F-ML-002: `--down` stops `${RECURRENCE_PORT}` without an occupancy check | LEDGER `:216` | [VERIFIED 2026-10-04: `util/isolated_stack.bash:507`, inside `do_down`] | STARTABLE | — | juniper-ml | S | SAFETY |
| P2-17 | Fix F-CASCOR-001 (an OOM is classified as a stall) and F-CASCOR-002 (every restore drops optimizer state) | LEDGER `:213`, `:3727` | [VERIFIED 2026-10-04: cascor#590 and #602 OPEN; cascor#632 says it left #602 "unchanged"] | STARTABLE | cascor release (P4) | cascor | M | DATA-INTEGRITY |
| P2-18 | Triage the Cursor-fleet drafts before the sweeper arms them: canopy#698–#701; ml#2122/#2125 | new | [VERIFIED 2026-10-04: all drafts by cursor[bot], none armed. #698 and #700 duplicate each other and say "#697 not on main". #699 is `dirty`: it carries a pre-merge copy of #697's test file (blob `2dd0b3d0`; main has `78e3a3a6`). #701 is clean and adds 5 tests. #2125's body says "Do not merge #2122".] | STARTABLE (triage), then OWNER-ACTION | — | canopy, juniper-ml | S | HYGIENE |
| P2-19 | Cut a canopy release so the fixes for F-059 (P0), F-056 and #697 reach PyPI | INDEX P2→P4 row | [VERIFIED 2026-10-04: the latest release, v0.8.1 (PyPI 09-18), contains #532 `359e1bf7`, so it ships F-059. 58 commits since; about 26 SHIP (§5).] | OWNER-ACTION (release) | P4 ceremony | canopy | S | USER-FACING |
| P2-20 | Compact MEMORY.md: retire entries, snapshot the link set first, never strip hooks | 10-04 i6; CONS A8 | [VERIFIED 2026-10-04: `wc -m` → 24,993 against the ~25,000 limit] | STARTABLE (shared) | all paths | auto-memory | S | UNBLOCKER |
| P2-21 | Worktree cleanup per CONS A9 (`…control--main…` is eligible now; the rest after O2). Inventory about 16 older E2E-arc canopy trees that no list names. | 10-04 i7; CONS A9 | [VERIFIED 2026-10-04: `ls -d` → every A9/C1 tree exists; also the `f035`×2, `f039`×2, `f040`, `f041`×2, `f044`, `f047`, `f052`, `m16`, `raw-topology-poll`, `probe/verify/triage` trees] | BLOCKED-ON P2-22 | P2-22 | canopy, juniper-ml | M | HYGIENE |
| P2-22 | O2: push provenance refs for the commits LEDGER cites that exist only locally (4 of them only in canopy reflogs), before any cleanup | CONS A6; LEDGER i15 | [VERIFIED 2026-10-04: no `refs/provenance/*` on canopy or juniper-ml] | OWNER-DECISION | — | canopy, juniper-ml | S | DATA-INTEGRITY |
| P2-23 | O3 (LEDGER i17): a replay replaces cascor's live network, while canopy promises "read-only playback" | CONS A3 | [VERIFIED 2026-10-04: cascor `start_replay` `:6399` → `:6429` → `self.model` `:6186`; `_auto_snap_best` is False (`:1550`); canopy `hdf5_snapshots_panel.py:533`, `main.py:3016`] | OWNER-DECISION | — | canopy, cascor | M | DATA-INTEGRITY |
| P2-24 | O6: rule on LEDGER i3, i4, i9 (M-DATASET) and i10 | LEDGER i3/i4/i9/i10 | [NOT RE-PROBED] | OWNER-DECISION | — | canopy | S | USER-FACING |
| P2-25 | O4/O5: confirm the account's actions on 09-23/24; the replay ratings | LEDGER i15 | [CHANGED SINCE HANDOFF: F-056 and F-059 are FIXED; only F-057's rating is still live] | OWNER-DECISION | — | juniper-ml | S | HYGIENE |
| P2-26 | O7: does Y2 wave 2 continue, and who runs it? Sweeper vs merge order. | CONS i8 | [VERIFIED 2026-10-04: 0 open PRs on recurrence or deploy; no Y2 branch] | OWNER-DECISION | — | — | S | UNBLOCKER |
| P2-27 | Re-base the delta and re-run the moved-path checks for all four upload sets, including the addendum's moved target | CONS i9 | [VERIFIED 2026-10-04: recurrence `be081fae` and deploy `9403dbf5` unchanged since 10-03; 0 ml commits since `f9c81d80` on the two launchers or their suites. CHANGED SINCE HANDOFF: ml#2117 (`8b6edddd`) moved the 09-08 handoff (R097) into `HANDOFF_2026-09/`.] | BLOCKED-ON P2-26 | P2-26 | ml, recurrence, deploy | M | UNBLOCKER |
| P2-28 | Round-15 fix pass (3 MAJOR, 10 MINOR, ~20 NIT, plus F20's sub-fixes), then round 16 onward until `APPROVED_FREEZE` | CONS B1–B2 | [VERIFIED 2026-10-04: `S/r15/SHA256SUMS` digest `66742624…4a3171`; nothing under S is newer than 09-25; no `r16`] | BLOCKED-ON P2-26 | P2-27 | ml, recurrence, deploy | L | DATA-INTEGRITY |
| P2-29 | Open 2b→2a→2c→addendum; merge 2c→2a→2b→addendum; `pull --ff-only` the shared recurrence checkout after 2a | CONS B3 | [NOT RE-PROBED — `S/main/PLAN.md` v5 not re-read] | OWNER-ACTION (merge) | P2-28 | deploy, recurrence, ml | M | SAFETY |
| P2-30 | Closing work: closing handoff from `handoff_v4.md`, archive rounds 1–16+ with a README, closing PR with the tools; the final summary repeats O10 | CONS B4–B5 | [NOT RE-PROBED] | BLOCKED-ON P2-29 | P2-29 | ml | M | HYGIENE |
| P2-31 | Wave 3 + X10: a recurrence branch at canopy's five snapshot sites, adapter save/list/get/restore, a probe in `initialize()` | CONS B6 | [VERIFIED 2026-10-04: `recurrence_service_adapter.py` has only `train` and `training_status`; recurrence on PyPI is 0.5.0] | OWNER-DECISION (O8) | recurrence release (P4) | canopy | L | DATA-INTEGRITY |
| P2-32 | Lane B's P4 tail: recurrence release after 2a; canopy release after wave 3; deploy pin bumps; raise the ml `recurrence` extra | CONS "Dependencies" | [VERIFIED 2026-10-04: `pyproject.toml:105` reads `>=0.5.0,<0.6.0`] | OWNER-ACTION (release) | P2-29, P2-31 | recurrence, canopy, deploy, ml | M | USER-FACING |
| P2-33 | C1/O15: owner removes `jazzy-soaring-minsky`, `bright-crunching-alpaca`, `tender-wibbling-flask` and `enumerated-marinating-puddle`, after running the probes | CONS C1 | [VERIFIED 2026-10-04: all four exist] | OWNER-ACTION (host) | — | juniper-ml | S | HYGIENE |
| P2-34 | C2/O9: rule on Y7 (greyed dataset options carry no `aria-disabled`), then implement | CONS C2; design §4.3 | [NOT RE-PROBED — note dated 09-24] | OWNER-DECISION | — | canopy or dash | S–M | USER-FACING |
| P2-35 | C3/O14: cut the next juniper-data release (X8: #437, #438) | CONS C3 | [VERIFIED 2026-10-04: GitHub latest is v0.16.0; PyPI 0.16.0] | OWNER-ACTION (release) | P3 item 1; P4 | data | S | DATA-INTEGRITY |
| P2-36 | C4: O9/U-6 ("Current Dataset" shows the staged dataset after a refused Start) becomes a design question if it survives Phase 10 | CONS C4 | [NOT RE-PROBED] | BLOCKED-ON P2-01 | P2-01 | canopy | S | USER-FACING |
| P2-37 | C6/O13: who may stop the mixed-version trio, and who pulls the primaries under the freeze | CONS C6 | [NOT RE-PROBED — host state; LEDGER's F-059 status says the trio's pids did not change during the 10-04 drive] | OWNER-DECISION / OWNER-ACTION (host) | — | host | S | UNBLOCKER |
| P2-38 | Send ONE owner message: O1 (merge approval) through O16, plus the dispositions for P2-18 and the release in P2-19 | CONS "Before anything else" | [VERIFIED 2026-10-04: 10-04 says no approval is carried] | STARTABLE | — | — | S | UNBLOCKER |
| P2-39 | O10: rotate `HF_TOKEN`, `JUNIPER_ML_PYPI` and `JUNIPER_ML_TEST_PYPI` (leaked into transcripts) | CONS O10 | [NOT RE-PROBED — secrets] | OWNER-ACTION (secrets) | — | — | S | SAFETY |
| P2-40 | O11: keep or retire the ad-hoc signed-commit driver copies. O12: make recurrence's `Settings` case-sensitive. | CONS O11/O12 | [NOT RE-PROBED] | OWNER-DECISION | — | ml, recurrence | S | HYGIENE |
| P2-41 | O16 remainder: archive predecessors A and B under `HANDOFF_2026-09/`, or accept the `r1/predecessors/` copies; retire branch `dd4413e5` | CONS O16; 10-04 i2 | [CHANGED SINCE HANDOFF: CONS was validated (INDEX) and merged (ml#2109); copies of A and B are on main via ml#2096] | OWNER-DECISION | P2-01 | ml | S | HYGIENE |

## 2. Owner decisions pending

| ID | Question | Options (source's recommendation) | Blocks | Source |
|---|---|---|---|---|
| O1 | Merge approval for this path's PRs | Grant or withhold. None is carried. | Every P2 merge | 10-04; CONS |
| O2 | Provenance for the commits the LEDGER cites that exist only locally | Push `refs/provenance/<arc>` to each remote at the branch tips; keep a local ref; or accept the loss. CONS calls it urgent before cleanup. | P2-21 | CONS A6 |
| O3 | A replay discards cascor's live network | Change canopy's wording, cascor's design, or both. No recommendation. | P2-23 | LEDGER i17 |
| O4 | The account's later actions (update-branch, re-arms, #676's CI re-run) | Confirm or deny | Closes LEDGER i15 | LEDGER i15 |
| O5 | Replay ratings against F-014's P1 precedent | Now moot except for F-057, which LEDGER's own rule returns to P2 | P2-02 | LEDGER i15 |
| O6 | (a) F-004's contract: 22–30 s measured against ≤16 s. (b) `FULL_HISTORY_POLL_TICK_MODULUS` → 1 (32.4 s refetch). (c) Which arm loads M-DATASET-17..26: the live `/api/stage_dataset`, the demo lane, or both (both grows the denominator). (d) Is a metrics replay that moves no chart intended? | No recommendation on any of the four | P2-24, MATRIX rows | LEDGER i3/i4/i9/i10 |
| O7 | Does Y2 wave 2 continue, who runs it, and sweeper vs merge order? | Exclude the four PRs from the sweeper; fix forward (the owner may pre-create `recurrence-snapshots/`); or have 2b's preflight warn until 2a is released. Default if unanswered: fix forward. | P2-27 through P2-30 | CONS i8 |
| O8 | How wave 3 is gated | A capability test (persistence design §8 item 3, §11.4 step 3), or a third branch ("never a widened predicate", 09-22 handoff § B). Record the choice in the design. | P2-31 | CONS O8 |
| O9 | Y7 | An upstream dash `aria-disabled`; an accessible-name marker (changes labels the Y8 tests pin); a clientside observer (binds to private class names); or accept the gap. No recommendation. | P2-34 | design §4.3 |
| O10 | Rotate the leaked tokens | Rotate. Status unknown. | Safety | CONS |
| O11/O12 | Signed-commit driver copies; recurrence `Settings` case | Keep or retire; yes or no | P2-40 | CONS |
| O13 | Who may stop the trio and pull the primaries | Stop the trio (which may free P6), or keep it | P2-37 | CONS C6 |
| O14/O15 | X8 data release; the C1 removals | Cut or wait; run or wait | P2-35, P2-33 | CONS |
| O16 | Archive A and B; retire `dd4413e5` | Partly overtaken (§5) | P2-41 | CONS |
| new | Dispositions of the fleet drafts | Merge or close each of #698–#701, #2122 and #2125 | P2-18 | live |
| new | Cut a canopy release | Cut now (a P0 is on PyPI) or wait for P2-06 | P2-19 | INDEX |

## 3. Cross-path dependencies

- **P2 → P4.** P2-19 (the canopy release), P2-32 (recurrence, canopy, deploy pins and the ml extra), P2-35 (X8) and the shipping of P2-10/P2-17 (cascor's release has 17 unreleased) are all owner-gated release cuts. The P2→P4 row of INDEX applies.
- **P3 → P2.** P3 item 3 (validate canopy#685 after its merge; not started) gates P2-01's FIXED-BY status for F-061/062. P3 item 11 hands F-060..062 and "Nothing was loaded" to P2-01. P2 owns P2-03. **P2 → P3**: send the id assigned to "Nothing was loaded" to P3.
- **P2-09 ↔ P3/P4**: the service-core changes ride the same release that P3's fix-forwards wait on. Only one session cuts it.
- **P2-37 (O13) ↔ P6**: stopping the trio may free the cascor primary. P2-07's profiling waits, softly, for P6's quiet windows.
- **P2-10/P2-17 ↔ P6/P7**: all three edit cascor. Sequence cascor PRs.
- **P10 → P2**: X7 is canopy#661, OPEN with 0 comments and untouched since 09-23 [VERIFIED 2026-10-04]. Only P10 carries it. Coordinate if P2 touches `src/tests/regression/test_x7_sites_outside_main_gate.py`.
- **P8 (soft)**: launch the consensus rounds for P2-01, P2-06 and P2-28 when no other arc is mid-round.
- **All paths ↔ P2-20**: MEMORY.md.

## 4. Hazards

- **Never drive a replay against the trio** (`:8101`/`:8202`/`:8051`). Every replay replaces cascor's network. `util/isolated_stack.bash` defaults to the trio's ports, so a bare `--down` kills it. F-ML-002 (P2-16) also kills whatever holds `:8211`.
- **The owner's sweeper un-drafts and arms open PRs, and its merges are intended.** Validate before opening. The fleet drafts (P2-18) are exposed now, and #698 and #700 would land duplicate docs.
- **Destroying the A6 commits**: removing a worktree or `branch -D` deletes reflog-only commits (canopy `78c057e2`, `26bf27b3`, `96e7b105`, `b07943d6`). O2 comes before any cleanup. Never run `util/remove_stale_worktrees.bash`.
- **Lane B's uncommitted state is the only copy** (`idempotent-jumping-sparkle` plus the two Y2 worktrees). Never do Lane A edits there: `open_signed_pr.py` uploads whole files and would revert main.
- **The X1 stake**: if 2b lands before 2a is merged and pulled, every deploy-main bring-up refuses.
- **ml#2117 moved the addendum's target file.** Uploading the frozen addendum to the old path would recreate the file there.
- **MEMORY.md is 7 characters from its limit.** The next index line truncates the tail for every session.
- **The LEDGER is 798 KB.** It needs its own signed commit, and a 499/502 can still land, so re-read the ref before retrying.
- **Replay checks need an explicit `POST /v1/snapshots` save.** Automatic snapshots have `length=0`, so every seek or range check on one passes vacuously.
- Briefs must forbid printing secrets or env values, and forbid sending the owner's email anywhere.

## 5. Discrepancies

1. **Open canopy PRs.** CONS says "dependabot only (#689, #692, #693)". Those have merged. There are now four Cursor-fleet drafts, created 11:03–11:08Z against #697's pre-merge head (#697 merged at 11:15Z).
2. **The count of unreleased canopy changes.** INDEX says 23 (detect.py, before #694). Now: 58 commits since v0.8.1 (45 not from dependabot). By detect.py's path rule (`src/` minus tests), #694, #696 and #697 add 3 SHIP, so about **26**. #689/#692/#693 (`conf/requirements_ci.txt`) and #695 (tests only) do not ship. [UNVERIFIED — detect.py not run]
3. **The P0 is on PyPI.** v0.8.1 contains #532, so the published canopy ships F-059 and F-056. Neither handoff states this.
4. **F-057 is still rated P1** although LEDGER's rule ("returns to P2 when the follow-up correcting both files merges") fired when canopy#684 merged on 09-24.
5. **LEDGER i13** says the follow-up branch is "not yet pushed". It is canopy#684 `f2147403`.
6. **canopy `REPLAY_V2_FAQ.md:11`** still says that against cascor the player "shows no session at all" (F-059). That has been false since #694, and it contradicts the FAQ's own `:35`.
7. **MATRIX M-REPLAY-07..-12 read FAIL**, while the 10-04 re-drive passed play, pause, seek, speed, range and stop live.
8. **O16's premise.** CONS's header says "written without consensus validation", but INDEX reports two validators per path, and ml#2109 merged the file.
9. **Selection-arc handoffs moved.** CONS cites predecessor C ("main, #2087"), O8's 09-22 source and the 09-08 addendum target at the top level. ml#2117 moved all three into `HANDOFF_2026-09/`.
10. **The manual line moved.** LEDGER i13 cites `docs/USER_MANUAL.md:1344`; it is now `:1346`.

## 6. Residue (open in references, carried by neither handoff)

- **R1.** The 08-28 wave's live row re-drive, F-033's redux re-trace and F-032's re-diagnosis (LEDGER `:6211–6215`). Six P2s were fixed in code but stay OPEN; the work dropped out of every later list. → P2-15.
- **R2.** F-CASCOR-001/002, OPEN P1s carried by no path. → P2-17.
- **R3.** F-ML-002. → P2-16. **R4.** F-051 has no plan. → P2-15.
- **R5–R7.** The F-057 re-rating, the MATRIX M-REPLAY rows and the FAQ status note. → P2-02, P2-18.
- **R8.** A-N2 observations O6–O8 (a continued model, a 67.9 s fit, the recurrence leg's model 0.1.5 against the extra's pin) were never registered. The selection arc handed over only O2–O5 and O9. Disposition UNTRACEABLE.
- **R9.** About 16 older E2E-arc canopy worktrees are in no cleanup list. → P2-21.
- **R10.** Phase 6 items 1b ("RENDER-STILL-DEAD unexplained") and 4 (the ~4–5 s re-enable overhead) are absent from Phase 7 onward. Disposition UNTRACEABLE.
- **R11.** `notes/JUNIPER_2026-08-27_JUNIPER-CANOPY_WS-MIGRATION-PLAN-JR-CAN-PERF-004.md` still gates Phase 2 on the "F-CANOPY-036 decision" (`:265`, `:279`), although canopy#536 shipped it. No path carries the plan.
- **R12.** canopy#552 (main-verify failing, filed automatically 08-31) is still OPEN, though main-verify is green on `1b2dd438`. No owner.
- Closed by probe: the "measured" fixture sweep in LEDGER item 16. Only `test_p2_wave_batch_a.py` still uses the phrase, in a comment that corrects it.

## 7. Path assessment

- **Urgency.** High for users and low for agents. A P0 (F-059) ships on PyPI until the owner cuts a canopy release. MEMORY.md is 7 characters from overflow. Four fleet drafts are exposed to the sweeper.
- **Triage counts** [VERIFIED 2026-10-04: inline parse]. 70 findings: 51 fixed, 1 accepted, 2 withdrawn, 16 open. Of the open: 0 P0, 5 P1 (F-055, -057, -058, F-CASCOR-001, -002) and 11 P2. MATRIX has 20 BLOCKED. Plan §6.3's exit criterion (every P0 and P1 closed or deferred) is 5 P1s away, or 4 after P2-02.
- **Leverage.**
  - P2-01/02 unblock P2-03, P2-04, P2-36 and P3's hand-over.
  - P2-05 unblocks the P1 redesign, P2-06.
  - O7 alone gates all of Lane B.
- **Cost.**
  - Lane A agent work: about 3 L, 9 M and 8 S.
  - Lane B: L, needing four PRs across three repos plus rounds.
  - Lane C: owner-only.
- **Next actions, in order:**
  1. **P2-38**: one owner message carrying O1, O2, O7, O13, the canopy release (P2-19) and the fleet dispositions. It is cheap, and it unblocks the most.
  2. **P2-18**: triage the fleet drafts before the sweeper merges duplicates. It also settles the FAQ fix in P2-02.
  3. **P2-01 + P2-02**: the Phase 10 ledger PR, validated before it is opened.

  P2-20 (MEMORY.md) is urgent but shared. The planner should assign it once, ecosystem-wide.

## 8. What this report cannot support

- **Host state.** I did not probe whether the trio is alive or its pids, the primaries' HEADs, the freeze tell, `/tmp` inodes, or O4's editable install.
- **The count of about 26** is inferred from paths. detect.py's hunk test was not run.
- **The LEDGER was read in part.** Items buried in old phase bodies may be missed; R1 surfaced only by following Phase 4.
- **Correctness of the fleet PRs.** No tests were run.
- **Decisions made outside GitHub or the repo** (chat, for example) are invisible to these probes.
- **F-058 on canopy itself, F-057's runtime absence, and O2/O3/O5** rest on source reads only.
- **Predecessor B and the combined round-1 handoff** were not read in full. Lane B's fix-list details rest on CONS.
