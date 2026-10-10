# Extraction — P12 (provisional) recurrence equities plan

<!-- markdownlint-disable -->

> **Archived verbatim.** An extraction report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Corrections found by validation are in the `round*-reconciliation.md` files in this directory, and the plan's §10. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

measured_at: 2026-10-04T20:54Z–21:13Z (all probes below ran in this window; read-only)

**The plan** = `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.2.0). **The consensus note** = `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-PLAN-CONSENSUS-VALIDATION.md`. "Lnnn" in a Source cell is a line of the plan. Path handoffs: P2 = `HANDOFF_2026-10-03_canopy-consolidated.md`, P3 = `HANDOFF_2026-10-03_defect-register-round-42-consolidated.md`, P4 = `HANDOFF_2026-10-03_release-and-distribution-consolidated.md`, P5 = `HANDOFF_2026-10-03_partition-arc-decision-12-consolidated.md`, P6 = `HANDOFF_2026-10-03_perf-lane-consolidated.md` (all in `prompts/thread-handoff_automated-prompts/`).

## 0. Sources read

| Source | Read |
| --- | --- |
| The plan | full, L1–794 |
| The consensus note | full, L1–157 |
| `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md` | full |
| P4, P5 | full |
| P3 | L1–75, 215–250, 286–345, plus grep (not the whole 413 lines) |
| P6 | L1–60, 120–170 (partial) |
| P2 | L30–130, 280–400 (partial) |
| P10 (`HANDOFF_2026-10-03_ci-tools-reevaluation-consolidated.md`) and the remaining consolidated handoffs | grep only |
| `notes/JUNIPER_2026-09-16_JUNIPER-RECURRENCE_MODEL-PERSISTENCE-DESIGN.md` | outline and §11 (L243–360) |
| `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` | L1292–1335, L1428–1432, grep |
| `notes/JUNIPER_2026-07-29_…CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md`, `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md` | grep only |
| `reports/2026-10-03_recurrence-equities-consensus/*.md` | grep plus the laneB1-r2 outline |
| GitHub issues | data#409 body; recurrence#183 and #184 bodies; recurrence#178's last 3 comments |
| Y2 frozen commit bodies (`…/idempotent-jumping-sparkle/reports/2026-09-23_y2-wave2-consensus/session-state/main/commit_2{b,c}_*.md`) | full |
| Memory `project_canopy_libtorch_python_collision_2026-05-07.md` | L1–40 |
| **Not read** | the equities ingest-sizing note; the 2026-06 recurrence notes; lanes A1/A2/A3/B1/B2/oracle in full; the content of the 103 evidence files |

**Probes.** Q-ids are cited in the tables below.

- **Q1.** `gh api …/juniper-ml/pulls/2116`: merged 2026-10-03T19:06:56Z (`17f12f7f`). juniper-ml main head is `cf711cf4`, which equals this worktree.
- **Q2.** PyPI JSON: data 0.16.0, data-client 0.5.0, recurrence 0.5.0, recurrence-model 0.3.0, recurrence-client 0.3.0, canopy 0.8.1, ml 0.10.0, service-core 0.7.0, observability 0.4.0, model-core 0.3.2.
- **Q3.** juniper-recurrence:
  - main head `be081fae` (2026-10-02). This is the plan's audit SHA, so no recurrence commit has landed since the audit.
  - 0 open PRs; no `feat/p0*` branch.
- **Q4.** recurrence main files, via the contents API:
  - `main.py`: has `--generator` (:52); no `--params`.
  - `app.py`: no `RequestId`.
  - `data.py:73`: `JuniperDataClient(base_url, api_key)`, no timeout.
  - `routers/crossval.py:82-88`: no `order=`/`groups=`.
  - `schemas.py`: no `metrics_scope` and no `operation_id`.
  - `pyproject.toml`:
    - :51 service-core `>=0.6.0,<0.8.0`
    - :52 model-core `>=0.2.0`
    - :53 model `<0.4.0`
    - :54 data-client `>=0.4.2,<0.6.0`
    - :97/:106 juniper-data `<0.17.0`
  - Snapshot routes: `POST /v1/model/snapshots` and `…/{id}/restore` (`snapshots.py:137-184`). The CHANGELOG `[Unreleased]` section holds the snapshots and `restored`.
  - The bench `changes` job's PR filter covers only `bench/`, the workflow and `pyproject.toml`.
  - App CI `:131` runs `pip install -e ".[test]"`, so the model comes from PyPI.
- **Q5.** recurrence#178 is **CLOSED 2026-10-03T10:16:14Z**; the closing comment says the dispatch path was verified by runs 37114403856 and 37114410788. #182, #183 and #184 are OPEN.
- **Q6.** juniper-data:
  - `compare v0.16.0...main` = ahead 9; the latest release is v0.16.0; #437 merged 2026-09-24.
  - `equities_seq/generator.py:56`: `VERSION = "6.0.0"`.
  - `equities/defaults.py`: :45 `nan`, :50 `False`, :103 `next_close`.
  - The CHANGELOG `[Unreleased]` "Changed" section carries X8, with no breaking marker.
  - #409 is OPEN with 0 comments; #423 is OPEN; 0 open PRs.
  - Branch `fix/conditional-requests-round4-followups` is diverged (2 ahead / 6 behind) and has no PR.
  - `environments/dockerhub/secrets` is `[]` in both data and recurrence.
  - notify-consumers: latest run 37114403856, success.
- **Q7.** juniper-deploy:
  - main `9403dbf5`; 0 open PRs; no Y2 branch.
  - `docker-compose.yml` pins: :164/:523 data 0.16.0, :598 recurrence 0.5.0, :662/:806/:897 canopy 0.8.1.
  - The recurrence block (:589-648) has no `volumes:` and no `SNAPSHOTS`.
- **Q8.** juniper-canopy:
  - main `1b2dd438`.
  - Path-filtered commits:
    - the adapter was last touched 2026-06-22;
    - `outbound_errors.py` and `recurrence_backend.py` were last touched by #685 (2026-09-24);
    - `model_registry.py` was last touched by #682;
    - nothing has touched `dashboard_manager.py` or `metrics_panel.py` since 10-02.
  - `model_registry.py:491` has `version="0.1.0"`.
  - The adapter's `_parse` keeps the body only as `body=`, and its 401 text says "check recurrence_api_key".
  - `pyproject.toml:192` caps data-client `<0.6.0`, and there is no recurrence dependency.
- **Q9.** data-client: `contract.py` was last changed 2026-09-09 (#194); 0 open PRs.
- **Q10.** This worktree:
  - `experiment_stack.bash:142` defaults to `JuniperCascor1`. It has no `pip check` or preflight, and no `JUNIPER_RECURRENCE_SNAPSHOTS_DIR`.
  - `run_suite.py`: `TERMINAL_OUTCOMES` at :81 lacks `degraded`; :585-600 reads the top-level keys.
  - The driver files were last touched 2026-09-23.
  - `pyproject.toml`: :86 `juniper-data>=0.15.0`; :104-106 caps the recurrence extras at `<0.4.0` / `<0.6.0`.
  - The register says of APD-ML-002…006 that they "need an owner decision before code is written" (:1312-1330).
  - model-core has had `order=`/`groups=` since tag `juniper-model-core-v0.3.0`.
  - Tag `juniper-observability-v0.4.0` ships `RequestIdMiddleware`.
- **Q11.** Host (read-only `ls`/`cat`/`ps`):
  - JuniperCascor1 py3.14 holds `__editable__.juniper_recurrence_model-0.3.0.pth`, **mtime 20:56:02Z today**, pointing at the shared `juniper-recurrence` checkout (`.git/HEAD` = `main`).
  - `juniper_service_core-0.5.0.dist-info` holds module `0.4.0`; this was unchanged at 21:08:51Z.
  - No recurrence process is running, and the recurrence `AGENTS.md` has no recipe.
  - JuniperCanopy1's activate and deactivate hooks are present, and `~/.bashrc:139-140` exports LIBTORCH.
- **Q12.** Four **new P0 worktrees** under `worktrees/`, created 20:59–21:02Z. Their names give the branches:
  - `juniper-recurrence--feat--p0-cli-params-metrics-scope--20261004-1559--be081fae`
  - `juniper-canopy--fix--p0-recurrence-422-detail-in-sample-label--20261004-1600--1b2dd438`
  - `juniper-ml--feat--p0-recurrence-env-preflight--20261004-1601--cf711cf4`
  - `juniper-ml--fix--p0-suite-degraded-outcome-headline-metrics--20261004-1602--cf711cf4`

  Agent worktrees in `.claude/worktrees/agent-*` were created in the same minutes. Nothing has been pushed, and no PR exists.
- **Q13.** Evidence:
  - The 103 files are in `.amp/in/artifacts/recurrence-equities-audit/`.
  - The frozen `equities_seq-6.0.0-15505731cba5b86d.{npz,meta.json}` is in `.amp/in/scratch/data-store/`.
  - Both are excluded by `.git/info/exclude:18` (`/.amp/in/`).
- **Q14.** The Y2 wave-2 worktrees exist. Commit body 2b is the recurrence Compose bind mount plus `JUNIPER_RECURRENCE_SNAPSHOTS_DIR`. Commit body 2c makes both launchers declare the root, and adds a §11.1 correction to the persistence design.
- **Q15.** A grep of all `HANDOFF_2026-10-0[34]_*.md` for the plan's filenames, "recurrence-equities" and "2116" finds **no match**. None of the 11 consolidated handoffs, nor the index, references the equities plan.

## 1. Work items

**In flight.** The P0 items marked "in flight" are being executed by another session, as of 20:56–21:02Z today (Q11, Q12).

| ID | Item | Src | Live status | Gate | Depends on | Repo(s) | Eff | Crit | Overlaps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P12-01 (W0.1) | Repair JuniperCascor1 to model 0.3.x and service-core 0.7.x, drop the stale pair, restart listeners, record the `python -s` recipe; raise the recurrence data-client floor to ≥0.5.0 | L346,358 | [CHANGED SINCE HANDOFF: Q11 → model now editable 0.3.0 (20:56Z, another actor); service-core still metadata 0.5.0 with module 0.4.0; no recipe; Q4 → floor still ≥0.4.2] | OWNER-ACTION (host), in flight | — | host, recurrence | S | UNBLOCKER | — |
| P12-02 (W0.2) | Scoped recurrence-closure preflight in `recurrence_up`; `--skip-env-preflight` logs loudly | L347,362 | [VERIFIED 2026-10-04: Q10 → absent]; in flight (Q12) | STARTABLE | P12-01 (host acceptance) | ml | M | DATA-INTEGRITY | — |
| P12-03 (W0.3) | Per-phase manifest results; `degraded` derived from phases, in `TERMINAL_OUTCOMES`, non-zero exit; audit consumers | L348,364 | [VERIFIED: Q10 → :81 lacks it]; in flight (Q12) | OWNER-DECISION (R6) | R6 | ml | M | DATA-INTEGRITY | P6 item 4 (APD-ML-003/-004, same files) |
| P12-04 (W0.4) | `_headline_metrics` reads nested `train_r2` / `cv_r2` / `cv_r2_std` / `n_windows`; four fixtures | L349,367 | [VERIFIED: Q10 → :585-600 still top-level]; in flight (Q12) | OWNER-DECISION (register rule) | APD-ML menu | ml | S | DATA-INTEGRITY | **DUPLICATE APD-ML-002** (P6 item 4, `[ALSO P3]`) |
| P12-05 (W0.5) | Canopy parses the 422 `detail` (≤300 chars) into the error, the WARNING log and the UI | L350 | [VERIFIED: Q8 → body dropped; `outbound_error_text` (canopy#685) passes `str(exc)` when a status is present]; in flight (Q12) | OWNER-DECISION (#685 call a) | P3 item 3 | canopy | M | USER-FACING | P3 items 3 and 10 (APD-ECO-014) |
| P12-06 (W0.6) | CLI `train --params` / `--params-file`; an `equities_seq` example in `--help`; an offline E2E | L351,368 | [VERIFIED: Q4 → absent]; in flight (Q12) | STARTABLE | — | recurrence | S | UNBLOCKER | — |
| P12-07 (W0.7) | `TrainResponse.metrics_scope:"in_sample"`; canopy panel title "in-sample" | L352 | [VERIFIED: Q4 → absent]; in flight (Q12) | STARTABLE | — | recurrence, canopy | S | USER-FACING | analogue of ml#2064 (P5 item 3) |
| P12-08 (W0.8) | Replay the E-H crossval (RFF, ridge 1.0, 256 features, median gamma) on the frozen id; record theta, ridge, gamma and per-fold ranges as §1 of the W5.1 note | L353,369 | [VERIFIED: Q13 → the artifact exists only in git-excluded scratch]; not run | STARTABLE (shadowed) | P12-01 for an as-served run | ml (ad-hoc), recurrence | S | RESEARCH | P6 item 2 (PF-3 window) |
| P12-09 (W0.9) | Run the {readout × ridge × normalise × theta} matrix; record the P5 go/no-go as §2 of the W5.1 note; consensus review; closes M0 | L354,371 | [NOT RE-PROBED — not started (Q3, Q10)] | BLOCKED-ON P12-01, P12-06, P12-08 | — | ml, recurrence | M | RESEARCH | P6 item 2 |
| P12-10 (W1.1a) | Document the recurrence-ready explicit bundle; merge only after the W0.9 verdict | L379,395 | [VERIFIED: Q6 → defaults unchanged; #409 unanswered] | BLOCKED-ON P12-09, plus OWNER-DECISION (#409) | #409 | data | S | USER-FACING | P4 item 7 (#409) |
| P12-11 (W1.1b) | Optional `preset:"lmu"` hashed into `dataset_id` | L379 | [NOT RE-PROBED — an option] | OWNER-DECISION (R1) | R1 | data | S–M | USER-FACING | P4 item 7 |
| P12-12 (W1.2) | Forward only params in the schema; no `n_samples` / `noise` translation; R7 precedence; preview of the effective request | L380,396 | [VERIFIED: Q8 → backend unchanged since 09-24, before the audit] | OWNER-DECISION (R7) | R7; a complete `dataset_schema` | canopy | M | USER-FACING | — |
| P12-13 (W1.3) | `target=reg|class|auto`; default `reg`; WARN on the one-hot fallback | L381,398 | [VERIFIED: Q3 → code at the audit SHA] | OWNER-DECISION (R8) | R8 | recurrence-model | S | DATA-INTEGRITY | — |
| P12-14 (W1.4) | Validator: finite `dt`; check `target_dt` and `seq_lengths`; enforce float32; mirror in the model reader | L382,399 | [VERIFIED: Q9 → unchanged] | OWNER-DECISION (R2) | R2 | data-client, model | M | DATA-INTEGRITY | P5 item 6 (KeyError at `contract.py:72`); P5 spec W3 |
| P12-15 (W1.5) | `operation_id` on train, 409 and status; terminal `failed`; `expect_operation_id`; `juniper_data_timeout_seconds`; canopy handles the four races; driver gets a dataset-create timeout | L383,400 | [VERIFIED: Q4 → no ids; `data.py:73` has no timeout] | STARTABLE (service half); the canopy and driver halves are BLOCKED-ON the service half | — | recurrence, canopy, ml | L | DATA-INTEGRITY | P3 later-arc C-A / APD-ECO-003 |
| P12-16 (W1.6) | 401 remedy text names the env var; `restored` / `restored_from`; 429 with Retry-After | L384 | [VERIFIED: Q8 → old text; Q4 → `restored` is unreleased] | STARTABLE | live only after P12-23 | canopy | S | USER-FACING | P2 B6 wave 3 / O8 (partial) |
| P12-17 (W1.7) | Read the version from `/v1/health`; floor `juniper-recurrence-client>=0.3.0,<0.5.0` in `[service]` | L385 | [VERIFIED: Q8 → `"0.1.0"`; no dependency] | STARTABLE | — | canopy | S | HYGIENE | — |
| P12-18 (W1.8) | `cost_basis` under `drop`, per R3; bump the generator only if values change | L386 | [NOT RE-PROBED — data main = audit SHA + 2 CI bumps (Q6)] | OWNER-DECISION (R3) | R3 | data | S–M | DATA-INTEGRITY | — |
| P12-19 (W1.9) | Launcher records the CLI path and effective settings; driver uses them; rerun parity | L387,404 | [VERIFIED: Q10 → unchanged] | STARTABLE | — | ml | S | DATA-INTEGRITY | P2 2c (`env/launch.env`, same region) |
| P12-20 (W1.10) | `recurrence_up` exports `JUNIPER_RECURRENCE_SNAPSHOTS_DIR` and LOG_LEVEL / LOG_FORMAT | L388 | [VERIFIED: Q10 → absent] | Snapshot half: OWNER-DECISION (O7). Log half: STARTABLE | O7 | ml | S | HYGIENE | **DUPLICATE** of Y2 2c (P2 Lane B) |
| P12-21 (W1.11) | Release data 0.17.0 (X8); ml floor ≥0.17.0; Compose data pins; canopy→recurrence→data smoke | L389,405 | [VERIFIED: Q2/Q6 → 0.16.0 latest; main 9 ahead; X8 unmarked; Q7 → pins 0.16.0; Q10 → floor ≥0.15.0] | OWNER-ACTION (release cut) | P3 item 1; the #437 marker ruling; recurrence `[bench]` cap PR (Q4) | data, ml, deploy, recurrence | M | UNBLOCKER | **DUPLICATE**: P4 item 5; P3 item 10 [R]; P2 C3/O14 |
| P12-22 (W1.12) | Recurrence Compose bind mount and `SNAPSHOTS_DIR`; document that there is no restore-on-boot | L390 | [VERIFIED: Q7 → no `volumes:`; Q14 → 2b prepared, never opened] | OWNER-DECISION (O7) | P12-23 (the routes are unreleased) | deploy, recurrence | S | DATA-INTEGRITY | **DUPLICATE** of Y2 2b (P2 Lane B) |
| P12-23 (W1.13) | Release train: data-client 0.6.0 → model 0.4.0 → recurrence 0.6.0 → canopy 0.9.0; move the pins; re-run the smoke | L391,407 | [VERIFIED: Q2 → none released; Q4/Q8/Q10 → caps `<0.6.0` / `<0.4.0` block it] | OWNER-ACTION (releases) | P12-13…17, P12-21; cap PRs first | 5 repos | M | UNBLOCKER | P4 item 5; P5 spec W3/W4/W10 and its "recurrence release" owner item; P2 Lane B tail |
| P12-24 (W2.1) | Catch fit and crossval exceptions; log ERROR with fields; return 500 with an `incident_id` | L413 | [NOT RE-PROBED — Q3] | STARTABLE | — | recurrence | S | USER-FACING | — |
| P12-25 (W2.2) | `RequestIdMiddleware`; canopy sends `X-Request-ID`; three-service test | L414 | [VERIFIED: Q4 → absent; Q10 → already in observability 0.4.0] | STARTABLE | — | recurrence, canopy | M | USER-FACING | — |
| P12-26 (W2.3) | INFO for generator params and artifact inventory; WARNING validation summary | L415 | [NOT RE-PROBED — Q3] | STARTABLE | — | recurrence | M | USER-FACING | P5 item 6 (same lines) |
| P12-27 (W2.4) | Model fit-summary logging; `captureWarnings`; log the resolved theta | L416 | [NOT RE-PROBED — Q3] | STARTABLE | — | model, recurrence | M | USER-FACING | — |
| P12-28 (W2.5) | Snapshot and 409 logging; service-core 401 / 429 WARNING | L417 | [VERIFIED: Q10 → only the throttle logs] | STARTABLE; the service-core half ships only with a release | service-core release | recurrence, ml | M | USER-FACING | P3 item 10 [F]; fork-drift gate |
| P12-29 (W2.6) | `init_logging` before `uvicorn.run` and in CLI `train`; access-log formatter; DEBUG lines | L418 | [NOT RE-PROBED — Q3] | STARTABLE | — | recurrence | S | HYGIENE | — |
| P12-30 (W2.7) | `*_failures_total{reason}`, in-progress gauge, histogram recorded on failure | L419 | [NOT RE-PROBED — Q3] | STARTABLE | — | recurrence | S | HYGIENE | — |
| P12-31 (W2.8) | Driver writes `http_error_<phase>.json` and log tails, and sets `completion_reason` | L420 | [VERIFIED: Q10] | STARTABLE | — | ml | S | USER-FACING | P6 item 4 (APD-ML-004, same file) |
| P12-32 (W2.9) | Canopy `makeRecord(func=…)`; fix or delete the midnight-rotation block | L421 | [NOT RE-PROBED] | STARTABLE | — | canopy | S | HYGIENE | — |
| P12-33 (W2.10) | Producer cap/truncation WARNING; data-quality INFO | L422 | [NOT RE-PROBED — Q6] | STARTABLE | — | data | S | HYGIENE | — |
| P12-34 (W3.0a) | Crossval route test on a three-partition fixture with the real validator | L428 | [NOT RE-PROBED — Q3] | BLOCKED-ON P12-37 | P12-36, P12-14 | recurrence | S | DATA-INTEGRITY | — |
| P12-35 (W3.0b) | Readiness asserts `derive_full_split` and the model pin; 503 otherwise | L429 | [NOT RE-PROBED — Q3] | STARTABLE | — | recurrence | S | DATA-INTEGRITY | — |
| P12-36 (W3.1) | Compositional CI lane over the local model, app and client | L430 | [VERIFIED: Q4 → app CI installs the model from PyPI; no such lane] | STARTABLE (lands first in P3) | — | recurrence | M | UNBLOCKER | — |
| P12-37 (W3.2) | Shared `equities_seq` fixture; real validator; ≥6 route tests; 14-symbol guard | L431 | [NOT RE-PROBED — Q3] | BLOCKED-ON P12-36 | P12-14 | recurrence | M | DATA-INTEGRITY | — |
| P12-38 (W3.3) | Offline bench `[bench-equities]` lane on a committed cache fixture | L432 | [NOT RE-PROBED] | STARTABLE | — | recurrence | M | HYGIENE | — |
| P12-39 (W3.4) | Drift script also scans the AGENTS.md prose and the README version | L433 | [NOT RE-PROBED] | STARTABLE | P12-46 | recurrence | S | HYGIENE | — |
| P12-40 (W3.5) | Make a model or app change re-run the bench; file a new issue for it | L434 | [CHANGED SINCE HANDOFF: Q5 → #178 CLOSED 10:16Z, via the dispatch path; Q4 → the PR filter is still path-scoped] | STARTABLE (re-scope first) | — | recurrence | S | HYGIENE | P4 item 2 (DONE) |
| P12-41 (W3.6) | Run canopy's recurrence tests under `conda run -n JuniperCanopy1`; do not reinstall torch | L435 | [CHANGED SINCE HANDOFF: Q11 → the error is the LIBTORCH collision, and the hooks exist] | STARTABLE | — | host, canopy | S | HYGIENE | — |
| P12-42 (W3.7) | `tests/test_recurrence_equities_path.py` regression module | L436 | [NOT RE-PROBED] | BLOCKED-ON P12-05, P12-12, P12-15, P12-16 | — | canopy | M | HYGIENE | — |
| P12-43 (W4.1) | CLI and canopy runbooks: required conditioning, one caller per service, no r² text before R5 | L442,451 | [NOT RE-PROBED] | Draft STARTABLE; merge BLOCKED-ON P12-06, P12-07, P12-10 | — | recurrence, canopy | M | USER-FACING | — |
| P12-44 (W4.2) | README examples use `equities_seq` with params; state that flat `equities` is refused | L443 | [NOT RE-PROBED — Q3] | STARTABLE | — | recurrence | S | USER-FACING | — |
| P12-45 (W4.3) | Add recurrence to the parent AGENTS.md graph, port table and agent-file table; add a port-context table | L444 | [VERIFIED: parent `AGENTS.md:26` lists it only in the Active Repositories table] | OWNER-ACTION (parent file is unversioned); repo halves STARTABLE | — | parent, recurrence, ml | S | HYGIENE | — |
| P12-46 (W4.4) | README 0.5.0; AGENTS.md status prose | L445 | [NOT RE-PROBED — Q3] | STARTABLE | — | recurrence | S | HYGIENE | — |
| P12-47 (W4.5) | data README/REFERENCE: three-way split, `nan`, 15 features, cap; params docstring; ml `REFERENCE` :6470-6510 | L446 | [NOT RE-PROBED] | STARTABLE | — | data, ml | S | HYGIENE | — |
| P12-48 (W4.6) | Persistence-design banner; #183/#184 sentence edits; banners on the 2026-06 notes | L447 | [VERIFIED: Q5 → #183 and #184 OPEN; Q14 → 2c writes the §11.1 correction] | §11.1: OWNER-DECISION (O7); rest STARTABLE | #183, #184 | ml notes, recurrence | S | HYGIENE | P2 2c (partial) |
| P12-49 (W5.1) | CV blow-up investigation note: per-candidate verdicts, R5 recommendation, consensus review | L460,470 | [NOT RE-PROBED] | BLOCKED-ON P12-09 | — | ml, recurrence | L | RESEARCH | — |
| P12-50 (W5.2) | Pass `order=` / `groups=`; expose the date, ticker and `target_dt` keys; embargo ≥ lookback; exclude `test` | L461,472 | [VERIFIED: Q4 → not passed; Q10 → supported since model-core 0.3.0; recurrence floor ≥0.2.0] | STARTABLE | — | recurrence, model | L | DATA-INTEGRITY | — |
| P12-51 (W5.3) | Predict metrics with scope, split and `operation_id`; canopy propagation; `test_r2` only from `test` | L462,475 | [NOT RE-PROBED] | BLOCKED-ON P12-15, P12-07, P12-52 | — | recurrence, canopy, ml | M | DATA-INTEGRITY | ml#2064 (P5 item 3) |
| P12-52 (W5.4) | Build the suite-YAML `acceptance:` facility (gate/report; a missing metric follows the mode); then encode the R5 band | L463,476 | [VERIFIED: Q10 → no facility] | Facility BLOCKED-ON P12-04 and R6; band OWNER-DECISION (R5) | R5, P12-49 | ml | M–L | DATA-INTEGRITY | P6 item 4 (APD-ML-003) |
| P12-53 (W5.5) | `stats_summary.py`: regression-target summary per split | L464 | [NOT RE-PROBED] | STARTABLE | — | ml | S | HYGIENE | P5 item 3 / ml#2064; APD-ML-005/-006 |
| P12-54 (W5.6) | `--shared-equities-cache` opt-in, with its own runbook section | L465 | [VERIFIED: Q10 → per-run cache only] | STARTABLE | — | ml | S | HYGIENE | CLI plan H-9 |
| P12-55 (W5.7) | Record dropped symbols in `data_quality`; refuse or flag a lost requested symbol; guard `close > 0` | L466 | [NOT RE-PROBED] | STARTABLE | — | data | S | DATA-INTEGRITY | P3 round-39 §0.4 (`data_quality` has no recurrence consumer) |

## 2. Owner decisions pending

| ID | Question | Options and the source's recommendation | Blocks | Source |
| --- | --- | --- | --- | --- |
| Dates | Confirm or reset M0 10-24, M1 11-21, M2/M3 12-12, M4 2027-01-15 | The author's estimate; no reviewer checked it | schedule | the consensus note §7; plan L487-493 |
| R6 | Exit code for a `degraded` or `flagged` informational row | Non-zero for `degraded`; unchanged for `flagged`; `gate` opts in to failing | P12-03, P12-52 | L733 |
| APD-ML menu | May APD-ML-002 (= W0.4) and -003…-006 be coded? | The register requires a ruling. P6 recommends starting with APD-ML-003 and asking all five as one menu | P12-04 (and the P12-03 / P12-52 files) | register :1312-1330; P6 item 4 |
| #685(a) | Keep a status-bearing error's upstream text, or make it type-only? | P3 gives no recommendation. W0.5 needs "keep" | P12-05 | P3 item 10 |
| R2 | Enforce float32, or document the tolerance? | Enforce | P12-14 | L729 |
| R3 | Pre-purchase `cost_basis` under `drop` | Refuse when `purchase_date > start_date`; otherwise drop the rows | P12-18 | L730 |
| R7 | Canopy precedence between the seed and the form | Generic form values never override the seed; an explicit edit wins; show a preview | P12-12 | L734 |
| R8 | Ship the `reg` default in 0.6.0 as a breaking change? | Ship it; the bench keeps `auto` | P12-13 | L735 |
| R1 + data#409 | A preset, a documented bundle, or new defaults? | Plan: preset optional, bundle ships anyway. #409 asks the same question and proposes no change to the defaults | P12-10, P12-11 | L728; data#409 |
| R5 | E-H band, and gate vs report | Rule only after W0.9 and W5.1 | P12-52 | L732 |
| #437 + data cut | Is X8 breaking in the release notes? Cut the next data release once P3 item 1 validates? | P3 asks yes/no | P12-21 | P3 item 10 [R]; P4 item 5 |
| O7 | Does Y2 wave 2 continue, who runs it, and how do the sweeper and the merge order interact? | P2's default is fix-forward | P12-20, P12-22, P12-48 | P2 O7 |
| O8 | Canopy wave-3 gating | A capability test or a third branch | P12-16 | P2 O8 |
| O12 | Should recurrence `Settings` be case-sensitive? | — | P12-20 | P2 O12 |
| P4-Q6 | Should data answer a fetch failure with 502/503 rather than 400? | Not yet put to the owner | how F-S9 surfaces (P12-15, P12-33) | P4 item 6 |
| DC-0.6 | Which arc owns data-client 0.6.0: Decision 12 W3, or W1.13 / W1.4? | Neither source poses it | P12-14, P12-23; P5 spec W3/W4 | spec :527-556; L391 |

## 3. Cross-path dependencies

**P12 depends on other paths:**

- **P4.** P12-21 and P12-23 are release cuts that need the owner and the ceremony (P4 item 5). The juniper-ml floor changes need a juniper-ml release. Wave 4 (P4 item 3c) edits the `publish-image.yml` files in all five repos, the same workflows P12-23's image publications run, so the two must not run at once.
- **P3.**
  - P12-21 waits on P3 item 1, the data fix-forward (P3 dependency (i)).
  - P12-05 waits on P3 item 3 (validating #685) and on call (a).
  - P12-28's service-core half rides the service-core release that P3 item 10 [F] carries.
  - P12-15 overlaps C-A (APD-ECO-003).
  - P12-05's `detail` parsing should anticipate D-C (RFC 9457).
- **P5.**
  - data-client 0.6.0 is claimed by both arcs (P12-23, and spec W3/W11).
  - The same caps (canopy and recurrence data-client `<0.6.0`) and the same recurrence release are W10's precondition (b).
  - The data release numbering must not hard-code 0.17.0 (R2-6).
  - P5 item 6 touches the `recurrence/data.py` lines that P12-15 and P12-26 edit.
- **P6.**
  - P12-04 is APD-ML-002.
  - P12-03, P12-31, P12-52 and P12-53 edit the files APD-ML-003…006 cover.
  - P12-08 and P12-09 must not overlap a PF-3 pass.
- **P2.** P12-22 is 2b; P12-20 (snapshot half) and P12-48 (§11.1) are 2c; P12-16 touches wave 3 / O8; P12-21 is C3/O14.

**Other paths depend on P12:**

- P4 and P2 C3 gain W1.11's deploy smoke.
- The #183 and #184 follow-ups of P2's Lane B need P12-48's sentence list.
- P5 W9 (the recurrence call site, floor data-client ≥0.6.0) sequences after P12-15 and P12-26 in `data.py`.
- P6's PF-3 quiet window is threatened by P12-09's load.
- P5's ml#2064 shares `stats_summary.py` with P12-53.

## 4. Hazards

1. **Duplicate execution.** Another actor is already running P0 (Q11, Q12): the editable model install, plus four P0 worktrees covering W0.2–W0.7. Dispatch none of these again. Confirm that the session holds the R6 ruling, the APD-ML-002 decision and #685(a). The owner's sweeper arms any PR that opens, so W0.3, W0.4 and W0.5 could merge unruled.
2. **Rival Y2 implementations.** P12-20, P12-22 and P12-48 duplicate the prepared 2b/2c work. Their worktrees hold the only copy, so keep them. X1/F7: if 2b lands before 2a is merged and pulled, every deploy-main bring-up refuses.
3. **Fragile measurement input.** W0.8's frozen artifact and the 103 evidence files exist only in the primary checkout, excluded by `.git/info/exclude`. A `git clean -x`, a re-clone or a cleanup destroys them, and re-minting refetches from Yahoo and SEC, so the bytes may differ.
4. **Shared environments.**
   - W0.1 changes JuniperCascor1, which cascor also uses.
   - The editable model resolves from the shared `juniper-recurrence` checkout, so that checkout's branch is what gets served.
   - Never touch `lib/python3.13`.
   - Under W3.6 as written, a torch reinstall would be wrong.
5. **CI wiring collisions.** Each new juniper-ml test needs wiring in `ci.yml` (the wiring-drift gate), so parallel P0 ml PRs collide there.
6. **Releases.** Cap PRs land before the releases they unblock. Never approve a `pypi` gate. A release cut under an open PR silently moves its CHANGELOG entries. A negated closing keyword still closes an issue (#185 closed #178 that way).

## 5. Discrepancies

1. The plan says #178 is open (F-T6, W3.5). It CLOSED 2026-10-03T10:16:14Z, nine hours before the plan merged, and the plan's model/app path gap has no issue (Q5, Q4).
2. F-E1: the model is no longer 0.1.5. It became editable 0.3.0 today, while service-core is still split between metadata 0.5.0 and module 0.4.0 (Q11).
3. F-T9 and W3.6 misdiagnose a known LD_LIBRARY_PATH collision. The JuniperCanopy1 hooks exist; the audit probably invoked `bin/python` directly (Q11).
4. The plan's snapshot routes `/v1/snapshots/save` and `POST /v1/snapshots/restore` do not exist. The real routes are `POST /v1/model/snapshots` and `…/{snapshot_id}/restore` (Q4).
5. F-C6, F-DEP2 and the W1.12 round trip assume snapshots and `restored`, but #172 is unreleased. Published 0.5.0, which is the Compose pin and canopy's target, has neither (Q4).
6. W1.11 and W1.13 omit the cap PRs the releases need:
   - recurrence `[bench]` / `[bench-equities]` caps `juniper-data<0.17.0`;
   - recurrence and canopy cap data-client `<0.6.0`;
   - recurrence caps the model `<0.4.0`;
   - ml's `[recurrence]` caps are `<0.6.0` / `<0.4.0`.

   P5 also claims data-client 0.6.0.
7. W5.2: the recurrence model-core floor `>=0.2.0` predates `groups=` (0.3.0), so it must be raised.
8. W0.4 and W0.5 do not cite APD-ML-002 or canopy#685 / APD-ECO-014, both of which gate them.
9. The status table targets "juniper-data 0.17.0" for W1.8 and W2.10, yet W1.11 needs 0.17.0 cut soon, and that cut is gated on P3 item 1.
10. W1.1(a) is said to "need no ruling", but it presupposes one answer to the unanswered #409.
11. W4.6 says "four" notes, while the References list six notes for banners.
12. F-X10's sentence list omits the texts wave 2 itself introduces, which #184's body lists.
13. Minor: the plan cites `juniper_observability/request_id.py`; the file is `middleware/request_id.py`. Data main is now 9 commits ahead of v0.16.0, not 7.

## 6. Residue

These items appear in the plan's references, but the plan does not carry them:

- Y2 2a, the round-15 fix pass, round 16 and open/merge (P2 Lane B).
- The implementation of recurrence#183 and #184.
- Wave 3 / X10 canopy snapshot wiring (persistence design §11.4 step 3).
- The recurrence `requirements.lock:70/:74` refresh after a service-core release (P3).
- recurrence#182, which is likely unblocked (P10).
- ml#1994 and canopy#368, cited as context only.
- APD-RCLIENT-004: the client returns dicts, so new response fields go untyped.
- APD-ECO-003 / C-A.
- P5 item 6 (the KeyError escape).
- P4-Q6 (the 400 vs 502 question).
- Raising ml's `[recurrence]` extra, which needs an ml release.
- ml#2064, the cascor in-loop vs held-out labelling.
- The CLI plan's R-6 and H-9 rows, which need updating once R5, R6 and W5.6 land.
- No item preserves the frozen artifact or the evidence.
- No item corrects or annotates the false `succeeded` row already in the shared run index (`20261003T091414Z-4ba6`); W0.3 fixes only future rows.

## 7. Path assessment

- **Urgency: high.** F-D1 already wrote a false `succeeded` into the shared run index [VERIFIED 2026-10-04: the last row of `~/.local/state/juniper-experiments/index.jsonl` is `c001-0d8782ae` / `20261003T091414Z-4ba6`, `outcome: "succeeded"`; no recurrence run since]. The published stack refuses `equities_seq`. But P0 is already moving in another session, so the binding constraint is now owner decisions and coordination, not dispatch.
- **Leverage.**
  - W0.1 and W0.6, then W0.8 and W0.9, decide all of P5, W1.1(a) and R5.
  - W1.11 unblocks canopy × `equities_seq` on published images, and helps P4, P2 and P5.
  - W1.13 unblocks juniper-ml 0.11.0.
- **Cost.**
  - 55 items: 3 L, 1 M–L, 18 M, 2 S–M, 31 S.
  - 16 owner decisions: 8 from the plan, 8 cross-path.
  - Six publications: data, data-client, model, recurrence, canopy and juniper-ml. They span 6 repos plus the host.
  - Plan horizon: 2027-01-15.

**Next actions, in order:**

1. **P12-01…07: coordinate before anything opens.** Identify the session behind Q11/Q12, and give it, or hold its PRs pending, R6, the APD-ML menu and #685(a).
2. **§2: one owner batch.** R6, APD-ML, #685(a), O7 (dedupe P12-20/22/48), #409+R1, dates. Then R2, R3, R7 and R8 for P1.
3. **P12-08, then P12-09.** Once P12-01's service-core half lands, first copy the frozen artifact somewhere durable. Then run the W0.8 replay outside a PF-3 window: it is the cheapest item with the most information.

## 8. What this report cannot support

- **The in-flight session.** It cannot say who is executing P0, what those worktrees contain, or whether that session holds any ruling. Git there is refused and nothing is pushed.
- **The audit-time env state.** It cannot say what py3.14 held at audit time, only what it holds today.
- **Live behaviour.** No service was run, so it cannot speak to the E-H RFF result. It did not check whether canopy's tests pass under `conda run`, or whether the frozen artifact is intact beyond the file existing.
- **`detect.py` counts.** Not run.
- **Line-level verification.** Every citation was not re-checked line by line. The citations carry because recurrence main is the audit SHA, data main is the audit SHA plus 2 CI bumps, and canopy's recurrence files are unchanged.
- **Rulings made only in other sessions' chats.** These are invisible to this report.
