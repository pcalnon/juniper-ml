# Extraction — P6 perf lane & util/experiments residue

<!-- markdownlint-disable -->

> **Archived verbatim.** An extraction report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Corrections found by validation are in the `round*-reconciliation.md` files in this directory, and the plan's §10. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

measured_at: 2026-10-04T20:53:43Z – 21:02:47Z (all probes). juniper-ml `origin/main` = `cf711cf4` (`git ls-remote` 20:58Z, equal to this worktree). juniper-cascor `main` = `95cdc562`. juniper-canopy `main` = `1b2dd438`.

## 0. Sources read

- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_perf-lane-consolidated.md`: read in full (L1–259). This is "the consolidated handoff" below.
- `…/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: read in full.
- `…/HANDOFF_2026-09-24_perf-lane-helper-binds-axis3-run-d6-control-micro-cut.md` and `…/HANDOFF_2026-09-22_structure-screen-was-blind-to-its-founding-incident-and-five-open-items-in-run-suite.md` ("the structure-screen handoff"): both read in full.
- `…/HANDOFF_2026-09/HANDOFF_2026-09-23_perf-lane-d1-debt-clear-flip-pf1-rebaselined-pf2-axis2-ceiling-5882.md` and `…/HANDOFF_2026-09-22_perf-lane-d2-binds-d6-discharged-and-two-host-advantaged-tests.md`: both read in full.
- `…/HANDOFF_2026-09-11_perf-lane-burst-terminator-…md`: the RE-PROBED block (L27–105) and §5–§7. `…/HANDOFF_2026-09-07_perf-lane-wave0-closed-and-three-decisions-ruled.md`: §3.3–3.4 and §8. The two 09-10 handoffs and the 09-09 handoff: grep only.
- The following `notes/` files:
  - `…PERF-LANE-SIX-OWNER-DECISIONS-RULED.md` ("the rulings note"): full.
  - `…PERF-LANE-PF2-RESPECIFICATION.md` ("the re-spec"): full.
  - `…PERF-LANE-D1-EPOCH-COUNT-DEBT.md` and `…PERF-LANE-D6-EPOCHS-COMPLETED-SPREAD.md`: full.
  - `…PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md` ("the ICV note"): §7–8.
  - `…PERF-LANE-P2-PLAN.md` ("the P2 plan"): L1–60, Waves 1–5, §3–§6.
  - `…PERF-LANE-PHASING-AND-WORK-PRIORITISATION.md` ("the phasing note"): §1.1, §2 row C, §3 Tier 4, §5.
  - `…PERF-LANE-P1-DESIGN.md`: the acceptance list.
  - `…CLI-EXPERIMENTATION-TAIL-REPROBE.md` ("the tail re-probe"): §0.1, §0, §1, §4, §5.
  - `…P4-STUDIES-EVIDENCE.md`: L528–572. `…P3-ACCEPTANCE-ROLLUP.md`: grep only.
  - `…DEFECT-REGISTER.md` ("the register"): the §4.9 rows APD-ML-002..006, its park block (L1225–1344) and L1420–1432.
- `util/experiments/suites/perf/README.md` and the header of `pf3-cascor-pool-scaling.yaml`.
- Cross-path consolidated handoffs:
  - P2 `…canopy-consolidated.md`: deps L124–130 and C6/O13 L380–399.
  - P3 `…defect-register-round-42-consolidated.md` and P4 `…release-and-distribution-consolidated.md`: grep, plus P4 L45–66.
  - P5 `…partition-arc-decision-12-consolidated.md`: L78–122.
  - P7 `…logging-arc-consolidated.md`: the P2.1 lines and deps L97–100.
- **Not read**: the bodies of the width-sweep, 09-17 spread, PF-8 occupancy, attribution and rescope notes. They are cited only for closed history.

## 1. Work items

| ID | Item | Source | Live status | Gate | Depends on | Repo(s) | Effort | Criticality |
|---|---|---|---|---|---|---|---|---|
| P6-01 | Add a nullable `candidate_epochs_completed: list[int] \| None` to cascor `training_step` rows (not a new row kind). Check the golden snapshots and the canopy tiles. | consolidated handoff item 1; rulings note §6 | [VERIFIED 2026-10-04: cascor `95cdc562` — `_process_training_results` :2986, `epochs_completed` :3035, `on_epoch_end` :258 / `kind` :267, `manager.py` :2058 = `output_epoch` (avoid), drain :2332, call :2386; search `candidate_epochs_completed` → 0; 0 open cascor PRs] [CHANGED SINCE HANDOFF: fixture path, see §5 item 1] | STARTABLE | — | juniper-cascor | M | UNBLOCKER |
| P6-02 | Build the PF-2 axis-1 suite (pool × `candidate_epochs`, base ≈2000) and a reducer that reads the field and excludes volatile fields. | item 1; re-spec §2, §5 | Not built. [VERIFIED 2026-10-04: the driver saves `metrics_history.json` verbatim at `run_experiment.py:1103`; `metrics_history_count` defaults to 1000 (`:128`). Whether 1000 covers every row is unverified] | BLOCKED-ON P6-01 (a merged or pinned cascor tree; no release needed) | P6-01; must not share host time with P6-03, P5-4, P7-P2.1 | juniper-ml | M | RESEARCH |
| P6-03 | Run PF-3 (14 cells, ~7 h per pass) only in a quiet window, with the sampler beside it. Check load at launch. Pick and quote the cascor SHA (`0d2d826` pin or post-flip `95cdc562`). | item 2; rulings note §6; suite header | [NOT RE-PROBED — host state]. No commit since `514b6c24` (09-24) records a run [VERIFIED git log]. The pin worktree exists [VERIFIED ls] | WAIT-QUIET-WINDOW | serialize with P6-02, P6-18, P5-4, P7-P2.1 | juniper-ml (+cascor tree) | L | RESEARCH |
| P6-04 | Present the D6 recount as counts only. The owner decides advisory or blocking. | item 3; rulings note §5.4; D6 note §4 | The advisory is still non-blocking, with reference `{100: 68, 200: 68}` [VERIFIED: cascor `test_candidate_epochs_completed_advisory.py:125`]. Since 10-03 09:00Z: 30 runs, only 2 dependabot heads plus main `95cdc562` [VERIFIED actions/runs]. Counter not re-run (prohibited) | OWNER-DECISION | P6-05 | juniper-cascor | S | DATA-INTEGRITY |
| P6-05 | Record the 10-03 recount (0 firings / 36 SHAs / 168 legs; control 4/4) in rulings note §5.4. | residue | [VERIFIED 2026-10-04 grep: the figure exists only in the consolidated handoff; §5.4 holds 09-23's 0/6/28] | STARTABLE | — | juniper-ml | S | HYGIENE |
| P6-06 | Put APD-ML-002..006 to the owner as one menu. | item 4; register §4.9 park block | [VERIFIED: "UNPARKED, and NOT thereby actionable" on main; last register commit `5af9d722` (09-24)]. Tagged ALSO P3, but P3 does not carry them (§5 item 6) | OWNER-DECISION | — | juniper-ml | S | DATA-INTEGRITY |
| P6-07 | APD-ML-003: make `expand_cells`' four repro shapes exit 2. Repair both the docstring and the REFERENCE exit-code table. | register row; structure-screen handoff §8.2 | [VERIFIED: contract `run_suite.py:28-30`, `expand_cells` :318, `except SuiteError` :887, REFERENCE heading :5207] | BLOCKED-ON P6-06 | — | juniper-ml | S | USER-FACING |
| P6-08 | APD-ML-002: fix `_headline_metrics` (4 of its 6 names exist nowhere) and add the first tests for the registry `metrics` columns. | register; structure-screen handoff §8.1 | [VERIFIED: `run_suite.py:585`, names unchanged; companion guards now at :755 / :778 / :797] | BLOCKED-ON P6-06 | P5-3 (ml#2064 edits `eval_scalars`, `stats_summary.py:225`) | juniper-ml | M | DATA-INTEGRITY |
| P6-09 | APD-ML-004: make an `_emit_stats` failure visible, and pin a failure test. | register; structure-screen handoff §8.3 | [VERIFIED: `run_experiment.py:1166`, `stats_error` :1181 / :1184] | BLOCKED-ON P6-06 | — | juniper-ml | S | DATA-INTEGRITY |
| P6-10 | APD-ML-005: guard `eval_aggregate` / `eval_std` the way `plots_recurrence.py` does. | register; structure-screen handoff §8.4 | [VERIFIED: `stats_summary.py:238-239`, :329] | BLOCKED-ON P6-06 | same file as P5-3 | juniper-ml | S | DATA-INTEGRITY |
| P6-11 | APD-ML-006: rule on the disk re-render coupling. Keep the test-pinned `present` fallback. | register; structure-screen handoff §8.5 | [VERIFIED: `stats_summary.py:340` unchanged] | OWNER-DECISION | P6-06 | juniper-ml | S | HYGIENE |
| P6-12 | Take the next falsy-guard batch on in-file evidence (`run_experiment.py:397`, `stats_summary.py:274`). Re-take the sweep over ml#2002's `or {}` sites before quoting "needs nothing". | consolidated handoff §C; structure-screen handoff §5 | [VERIFIED: both lines present; ml#2002's sites now :451, :650, :955] | STARTABLE (not register rows) | coordinate with P6-08..10 | juniper-ml | S | HYGIENE |
| P6-13 | Put the PF-2 axis-3 gating menu to the owner: ~5 paired dataset seeds per cell, and roc_auc, raw f1 or chance-adjusted f1. | item 5; re-spec §4.3 | Unchanged since 09-24 [VERIFIED git log] | OWNER-DECISION | P6-14 | juniper-ml | S | RESEARCH |
| P6-14 | Ratify the PF thresholds: the exit condition of the F-P3 phase. Every suite still says "unratified". | phasing note §1.1, §5; suites README | Not carried as its own item by the consolidated handoff | OWNER-DECISION | — | juniper-ml | M | RESEARCH |
| P6-15 | ICV residuals 1–2: the re-pin path in the `result_queue.get()` unpickle, and why the re-pin depends on op shape. | ICV note §7 | Open and optional [NOT RE-PROBED; no commit since 09-24] | STARTABLE | — | juniper-ml | M | RESEARCH |
| P6-16 | ICV residual 3: read the ICV inside a live listener. Needs a new mechanism (`ptrace_scope`=1; standing rule against modifying cascor). | ICV note §7 | As P6-15 | OWNER-DECISION | — | juniper-ml / cascor | M | RESEARCH |
| P6-17 | Qualify "recurrence has no work-done counter" in REFERENCE and the P2 plan; the MLP readout keeps `n_epochs_`. | 09-07 handoff §3.4; 09-22 d2 handoff §8 | [VERIFIED: `docs/REFERENCE.md:4718` unqualified, no mention of `readout_mlp`; `_readout_mlp.py` is in recurrence-model (code search)] | STARTABLE | — | juniper-ml | S | HYGIENE |
| P6-18 | Optionally run PF-5/6/7 (report-only forever). | P2 plan 2.3 | Never executed [NOT RE-PROBED — host state] | WAIT-QUIET-WINDOW | serialize with P6-03 | juniper-ml | M | RESEARCH |
| P6-19 | Decide whether PF-8 gets a committed parallel cascor suite under `suites/perf/`. | P2 plan 4.2 / §4 | README still says "Not checked in" [VERIFIED] | OWNER-DECISION | — | juniper-ml | S | RESEARCH |
| P6-20 | Optional experiment-scoped alerts. | P2 plan 5.2 | [VERIFIED: deploy `prometheus/alert_rules.yml` has 0 positive `host-experiment` selectors and 82 exclusions] | OWNER-DECISION | — | juniper-deploy | S | HYGIENE |
| P6-21 | Owner picks the title extraction rule. Any repair of the 91 artifacts is gated on `scan --check`. | tail re-probe §5; consolidated handoff §D | [NOT RE-PROBED — repo script]. Corpus and scanner unchanged since 10-03 [VERIFIED git log] | OWNER-DECISION | — | juniper-ml | M | DATA-INTEGRITY |
| P6-22 | Scope the `JR-ML-OBS-003` Detail-selection defect. | tail re-probe §5 | [VERIFIED: `id_assignments.yaml:459-463`, status `designed`, priority P0]. No entry point in the sources | OWNER-DECISION | — | juniper-ml | S (scoping) | DATA-INTEGRITY |
| P6-23 | R-1's second clause: cascor must not report `succeeded` when per-candidate allocation failures leave zero installable candidates. | tail re-probe §4 | [NOT RE-PROBED] | STARTABLE (no ruling recorded as needed) | — | juniper-cascor | M | DATA-INTEGRITY |
| P6-24 | F-P4-7: why the noise-free spiral is harder. | tail re-probe §4 | Open, no entry point | OWNER-DECISION | — | cascor / ml | S (scoping) | RESEARCH |
| P6-25 | E-C noise rows 0.10 / 0.20 at cap 128 (untested). | tail re-probe §4 | Open, minor | OWNER-DECISION | host time | juniper-ml | S | RESEARCH |
| P6-26 | W-12 `csv_import` corpus (un-parked by Q-7; scope widened). | phasing note §2 row C | Open; Q-7 itself is closed (§5 item 5) | OWNER-DECISION | — | cascor / recurrence | M | RESEARCH |
| P6-27 | G-16 refusal half: add a fixture that withholds an optional dependency. | tail re-probe §0.1 | Untestable in JuniperData [NOT RE-PROBED] | STARTABLE | — | juniper-data | S | HYGIENE |
| P6-28 | Record whether the owner's rider on the withdrawn 0.5% threshold is honoured or retired. | 09-07 handoff §8 | Recorded nowhere | OWNER-DECISION | — | juniper-ml | S | HYGIENE |
| P6-29 | Optional: test why `thread16` first diverges at candidate phase 20. | D1 debt note §4 | Hypothesis untested | STARTABLE (structural) | — | juniper-ml | M | RESEARCH |
| P6-30 | Remove the converged worktrees `reflective-mixing-pearl` and `idempotent-wibbling-dongarra`, plus `lively-marinating-truffle` and `gentle-kindling-pascal`, after a cleanliness check. | item 7; Git state | [VERIFIED: all 4 registered; HEADs `f8e04b11`, `514b6c24`, `d721fc78` and `d594a9d3` are ancestors of `cf711cf4`; cleanliness not probed] | OWNER-ACTION | — | juniper-ml | S | HYGIENE |
| P6-31 | Ship the BLAS-2 default with its deployment note in the next cascor release. | consolidated handoff, P4 dependency | [VERIFIED: cascor CHANGELOG `[Unreleased]` already carries the entry and a "Deployment note"; latest release v0.11.0 (GitHub 09-09, PyPI 09-10); deploy `docker-compose.yml` and `.env.example` set 0 BLAS vars] | OWNER-ACTION (release cut) | P4 item 5 | juniper-cascor | S | USER-FACING |
| P6-32 | Revisit the re-spec §1 axis-2 ceiling once juniper-data#432 is fixed. | consolidated handoff deps | [VERIFIED: #432 OPEN, 0 comments, no labels, updated 09-23] | BLOCKED-ON data#432 | P6-33 | juniper-ml | S | HYGIENE |
| P6-33 | Assign juniper-data#432 an `APD-DATA-*` id (register lane). | deps; 09-24 handoff item 7 | Unassigned, and P3's handoff never mentions #432 [VERIFIED grep] | STARTABLE (P3's session) | — | juniper-ml (register) | S | HYGIENE |
| P6-34 | Non-perf: owner rules which closed-arc entries `MEMORY.md` retires. First fix the gates that do not read hook text. | structure-screen handoff §7 | [CHANGED SINCE HANDOFF: 25,189 B, was 25,125 on 10-03] | OWNER-DECISION | all paths | auto-memory | S | HYGIENE |
| P6-35 | Non-perf: reword the malformed-pyproject reason in `env_floor_drift_check.py`. | structure-screen handoff §7 | [VERIFIED: `:384` unchanged] | STARTABLE | ALSO P10 | juniper-ml | S | HYGIENE |
| P6-36 | Make `register_status_crosscheck.py` able to catch §2 count drift. | structure-screen handoff §7 | [VERIFIED: keyed on `**FIXED`; unchanged since `b0e496dc` (09-05)] | STARTABLE | ALSO P3 | juniper-ml | S | HYGIENE |
| P6-37 | Fix the requirements plan's stale "thin indexes" text (ml#1462 made those views full projections). | tail re-probe §0.1 ("plan §97") | [VERIFIED: still present, now at `…REQUIREMENTS-IDENTIFICATION-PLAN.md:99`] | STARTABLE | — | juniper-ml | S | HYGIENE |
| P6-38 | Refresh the phasing note's deliverables table. | phasing note §1.1 | [VERIFIED: it still says P1 "[ ] Reviewed", P2 "awaiting", P4 "not started". P1 design `:250` is [x] Reviewed; REFERENCE has § Perf-Lane Work Gate :4727 and § PF Scenario Suites :4887] | STARTABLE | — | juniper-ml | S | HYGIENE |
| P6-39 | Retire F-P1-2 and Q-7 from the carried CLI tail. Both closed 2026-08-16. | §5 item 5 | The consolidated handoff §D still carries both | STARTABLE | — | juniper-ml | S | HYGIENE |

"P5-3", "P5-4" and "P7-P2.1" are P5 items 3 and 4 and P7 item P2.1.

## 2. Owner decisions pending

| ID | Question | Options, and the source's recommendation | Blocks | Source |
|---|---|---|---|---|
| OD-1 | D6: keep the gate advisory, or make it blocking? | Keep advisory or block. The source says to present counts and **not recommend**. On 10-03: 0 / 36 / 168, control 4/4. Most SHAs are dependabot, and no PR has changed candidate numerics, so tree-sensitivity is untested. | Gate policy only | rulings note §5.4; consolidated handoff item 3 |
| OD-2 | Authorise APD-ML-002..006, and in what order? | Source: start at APD-ML-003; ship 002 with its first column tests; repair both surfaces for 003; never delete 006's fallback. | P6-07..P6-11 | structure-screen handoff §1, §8; register §4.9 |
| OD-3 | Which metrics and split should `aggregate.csv` carry? *(Raised here; not in the sources.)* Only `cascor.final.val_accuracy`, the selected-on val split, exists of the six names. ml#2064 (P5) would surface the test-split `eval_metrics.final`. | No recommendation in the sources | P6-08 | register APD-ML-002; P5 item 3 |
| OD-4 | PF-2 axis-3 gate design | About 5 dataset seeds per cell, compared paired; roc_auc, raw f1 or chance-adjusted f1. Source: do not decide. | Gating axis 3 | consolidated handoff item 5; re-spec §4.3 |
| OD-5 | PF threshold ratification | None proposed. "The lane cannot finish its verification phase without it." | Gating any PF suite | phasing note §5 |
| OD-6 | A committed PF-8 suite? / experiment-scoped alerts? | Both "optional". | P6-19, P6-20 | P2 plan :481, :375 |
| OD-7 | The title-artifact extraction rule | It must be chosen before any repair, and repair gated on the scan. | P6-21 | tail re-probe §5 |
| OD-8 | The 0.5% rider: honoured or retired? | "Arguably moot". Decide and record. | P6-28 | 09-07 handoff §8 |
| OD-9 | A mechanism for ICV residual 3 | A new mechanism, or relax the no-modify rule. | P6-16 | ICV note §7 |
| OD-10 | APD-ML-006: whether a disk re-render tool may exist | No recommendation. | P6-11 | structure-screen handoff §8.5 |
| OD-11 | Whether to pursue W-12, F-P4-7, E-C 0.10/0.20 and JR-ML-OBS-003, and their scope | No entry point given. | P6-22, P6-24..P6-26 | tail re-probe §4 |
| OD-12 | `MEMORY.md` retirement set | Retire entries; never strip hooks. | P6-34 | structure-screen handoff §7 |
| OD-13 | **P2's O13**: who may stop the trio, and who pulls primaries under the freeze ("may also free P6") | Owner. | Pulling the cascor primary | P2 handoff L127, L397 |
| OD-14 | The cascor release cut (carries #683) | Owner, via P4. | P6-31 | P4 handoff item 5 |

## 3. Cross-path dependencies

**What P6 needs from other paths:**

- **P4**: the cascor release cut, for P6-31. PF-2 axis 1 does **not** need a release, because suites run a source tree.
- **P3**:
  - APD-ML-002..006 (P6-06..P6-11) and #432's id (P6-33) are register work.
  - **P3's consolidated handoff carries neither.**
- **P2 / O13**: the trio holds the cascor primary. P6 runs from pinned worktrees through `JUNIPER_EXP_CASCOR_SRC_DIR`, but the base CONFIG still comes from the primary (trap A.1). [UNVERIFIED — freeze not re-probed]
- **P2 canopy**: P6-01 must stay additive, because `metrics_panel.py:1652` and `:1887` read `metrics_data[-1]`. [VERIFIED 2026-10-04: canopy `1b2dd438`]
- **juniper-data**: a fix for #432 triggers P6-32.

**What other paths need from P6:**

- **P5 item 3** (ml#2064: `stats_summary.py:225`, `plots_cascor.py`) touches the same file as P6-08, P6-10 and P6-11. Serialize them. P6-08's metric choice also depends on what ml#2064 surfaces.
- **P5 item 4** (V-3, cascor#677) and **P7's P2.1 wall-clock A/B** share the host with P6-02, P6-03 and P6-18. No two may overlap a PF-3 window.
- **P7**: run P2.1 and P2.2 in a cascor worktree, measured against the parent commit, so that #683 is held constant.
- **P8** (soft): consensus rounds share the account's usage windows.

## 4. Hazards

- Never run `util/reap_pytest_orphans.bash` or `util/juniper_chop_all.bash`. They kill nohup'd experiment services.
- Never run `util/remove_stale_worktrees.bash`: it has no staleness predicate.
- Retained state must not be deleted:
  - the `…perf-pf1-baseline-pin…0d2d826b` and `…e-c-cap64…67d7ea35` worktrees, and the shadow symlink;
  - baselines `pf1-2026-09-04*`. Supersession is by name, and there is no `--force`.
  - the suite directories.
- Run from a session worktree, the experiment stack resolves its project dir to `.claude/worktrees` and fails silently, inverting results. Export `JUNIPER_EXP_PROJECT_DIR` and pin `JUNIPER_EXP_CASCOR_SRC_DIR`.
- Instrument traps:
  - `torch.get_num_threads()` re-pins the calling thread. Use `util/thread_width.py`, which CI enforces.
  - `pkill -f` kills its own shell; kill by PID.
  - Never quote wall-clock figures from loaded runs.
- Fix traps:
  - For APD-ML-002, a one-level unwrap harvests 2 of 6 names and *looks* fixed.
  - APD-ML-006's fallback is test-pinned. Do not delete it.
- PF-3 needs a ~7 h quiet window. Peers run suites around the clock, and any P5 or P7 timing run inside the window corrupts both measurements.
- High-conflict files are `docs/REFERENCE.md`, `ci.yml` and `AGENTS.md`. Four open ml PRs titled `docs(reference)` exist (#2119, #2122, #2125, #2128; judged by title only).
  - AGENTS.md's `Last Updated` check.
  - CHANGELOG entries go at the end of `[Unreleased]`.
  - A same-file test rename in cascor counts as symbol loss.
- Before pulling the cascor primary, check that no process holds it (P2's freeze).

## 5. Discrepancies

1. **The API snapshot fixture path is wrong.** The consolidated handoff names `src/tests/fixtures/api_snapshots/`, which is a 404. The real directory is `src/tests/fixtures/golden/api_snapshots/`.
   - `metrics_history_fresh.json` is `data: []`, so the new field cannot break it.
   - `metrics_post_train.json` pins `/v1/metrics`' key set and may need regenerating.
2. **cascor `main` moved** from `b2921712` to `95cdc562` (dependabot #697, 10-03 09:56Z, lockfiles only). All the axis-1 anchors are unchanged.
3. **The D6 recount (0/36/168) is recorded only in the consolidated handoff**, not in the rulings note.
4. **The `ml#1811` / `xor-staged` row is closed, not NOT RE-PROBED.** It merged 2026-09-07T16:06:23Z, and `PENDING_EPOCH_SPLIT_DECISIONS = {}` (`tests/test_experiment_config_schemas.py:144`).
5. **F-P1-2 and Q-7 are carried as open but were closed on 2026-08-16.** The consolidated handoff §D carries them, as does the 08-29→09-22 chain. The closures are in:
   - the phasing note §5, "Closed this round: F-P1-2 (premise refuted), Q-6, Q-7…";
   - `JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_F-P1-2-GRAFANA-RENDER-CLOSURE-EVIDENCE.md`;
   - the P3 rollup's update.

   `…P4-STUDIES-EVIDENCE.md`:563 (08-16) says the opposite. W-12 is the half that survives.
6. **P3 does not carry what the consolidated handoff tags `[ALSO P3]`.** grep of P3's handoff finds no "432", and only APD-ML-007 and -008.
7. **P5's gate reason is stale.** P5 says V-3 waits because "PF-1 holds the box" (cascor#677 comment, 09-23T20:58Z). PF-1's runs finished 09-23, and the documents show no P6 run since 09-24. Host state was not re-probed.
8. **The register's anchors have drifted** (re-grep before editing):

   | anchor | register says | now |
   |---|---|---|
   | `except SuiteError` | :882 | :887 |
   | companion guards | :750 / :773 / :792 | :755 / :778 / :797 |
   | REFERENCE exit-code table | :5136 | :5207 |
   | `run_suite.py` exit-code contract | :28-29 | :28-30 |

9. **`MEMORY.md`** is 25,189 B, up from 25,125.
10. **The phasing note's deliverables table is stale** (P6-38).

## 6. Residue

Open items in the references that the consolidated handoff does not carry:

- **PF threshold ratification** as a lane exit condition. Now P6-14.
- **The requirements plan's "thin indexes" text**, dropped from every handoff since 09-07. Now P6-37.
- **The stale deliverables table** in the phasing note. Now P6-38.
- **The unrecorded D6 recount.** Now P6-05.
- **Two axis-1 checks**: does `metrics_history_count` (1000) cover every row, and does the golden `metrics_post_train.json` change? Both folded into P6-01 and P6-02.

Items that turned out to be resolved:

- **The D1 §5.2 constructor-pin question is RESOLVED.** cascor's `blas_threads.py` docstring documents the `:1180` pin as RC-1's retained oversubscription guard, independent of the environment variables. [VERIFIED 2026-10-04]
- **G-17's marker half is CLOSED**, per P2 plan 3.2 [NOT RE-PROBED].

Untraceable:

- **`install_hint`** was unblocked on 08-31, but no later document records whether it shipped.

## 7. Path assessment

**Urgency** is low to moderate. Nothing here is safety-critical. The data-integrity rows (APD-ML-002, -004, -005) are long-standing silent losses and are owner-gated.

**Leverage:**

- P6-01 is the only startable item that unblocks another one, axis 1, which is the last unbuilt PF-2 axis. It needs no host time and no release.
- The owner menu (P6-06) unblocks five fixes and settles how they sequence against P5 item 3.
- PF-3 is purely host-bound.

**Cost:**

- P6-01: M, cross-repo.
- P6-02: M, plus host time.
- PF-3: 7 h per pass, about 21 h for three round-robin passes.

**Recommended next actions, in order:**

1. **P6-01.** Open the cascor PR for the additive field. Check the golden `metrics_post_train.json`, the canopy tiles, and the history count.
2. **P6-05, then P6-04, P6-06 and P6-13 in one owner sitting.** Record the recount first. Then put the D6 counts, the APD-ML menu (with OD-3 and the ordering against P5 item 3) and the axis-3 menu.
3. **One host-time schedule** serializing PF-3 (P6-03), P6-02, P5's V-3 and P7's P2.1 A/B. PF-3 still waits for the ruled quiet window.

## 8. What this report cannot support

- **No host state was probed**, as instructed: load, `clamscan`, the trio or the freeze, running processes, suite and baseline directories.
- **"No run since 09-24" rests on git commits only.**
- **D6 counts after 10-03 and the title-scan count are not re-measured.** Neither script was run.
- **Worktree cleanliness is unknown**, because cross-worktree git is refused.
- **Two code questions are open:** whether `/v1/metrics` would expose the new field, and how many history rows a run emits.
- **Code-search results are index-based.** No strict models or `training_step` consumers were found in juniper-cascor-client.
- **Effort sizes are my estimates** except where the P2 plan states one.
