# Quick Start Guide

## Install Juniper Packages with juniper-ml

**Version:** 0.3.45
**Status:** Active
**Last Updated:** 2026-11-09
**Project:** Juniper - Meta-Package for PyPI Distribution

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Install](#1-install)
- [Verify](#2-verify)
- [Next Steps](#3-next-steps)

---

## Prerequisites

- **Python 3.12+** (`python --version`)

---

## 1. Install

`juniper-ml` is a meta-package with no code of its own. Choose the extra that matches your use case:

```bash
# Client libraries only (juniper-data-client + juniper-cascor-client)
pip install juniper-ml[clients]

# Distributed training worker only (juniper-cascor-worker)
pip install juniper-ml[worker]

# Server packages (juniper-canopy + juniper-cascor + juniper-data, with the clients they call)
pip install juniper-ml[servers]

# Shared tooling (juniper-ci-tools + juniper-doc-tools + juniper-observability)
pip install juniper-ml[tools]

# Markdown link validator only (back-compat alias for one entry in [tools])
pip install juniper-ml[doc-tools]

# Everything
pip install juniper-ml[all]
```

> **Note on install size.** `juniper-ml[all]` transitively pulls a multi-GB dependency tree (notably `torch` via `juniper-cascor-worker` and `juniper-cascor`). On a fresh environment this resolves to approximately **5 GB on disk after install** (measured on Python 3.13 + Linux x86_64 against PyPI on 2026-05-21).
> Callers who do not need the worker or server distributions should prefer a narrower extra. Measured on disk on 2026-10-25 (Python 3.12, Linux x86_64, pip itself excluded): `[doc-tools]` is about 1 MB, `[clients]` about 85 MB and `[tools]` about 91 MB. `[servers]` is about 410 MB, with no torch: it requests each server's client and `[api]` extras, never cascor's `[ml]` or canopy's `[demo]`. scipy, plotly, numpy and dash are about three quarters of it.

### What Each Extra Installs

| Extra       | Packages                                                                                                                                                                                                     |
|-------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `clients`   | `juniper-data-client>=0.5.0`, `juniper-cascor-client>=0.8.0`                                                                                                                                                 |
| `worker`    | `juniper-cascor-worker>=0.4.0`                                                                                                                                                                               |
| `servers`   | `juniper-canopy[juniper-cascor,juniper-data]>=0.9.0`, `juniper-cascor[api,juniper-data]>=0.12.0`, `juniper-data[api]>=0.17.1`                                                                                  |
| `tools`     | `juniper-ci-tools>=0.1.0`, `juniper-config-tools>=0.1.0,<0.2.0`, `juniper-doc-tools>=0.1.0,<0.2.0`, `juniper-model-core>=0.1.0,<0.4.0`, `juniper-observability>=0.4.1`, `juniper-service-core>=0.7.1,<0.8.0` |
| `doc-tools` | `juniper-doc-tools>=0.1.0,<0.2.0` (back-compat alias for the doc-tools entry in `tools`)                                                                                                                     |
| `recurrence`| `juniper-recurrence-model>=0.6.0,<0.7.0`, `juniper-recurrence>=0.8.1,<0.9.0`, `juniper-recurrence-client>=0.3.0,<0.4.0`                                                                                      |
| `all`       | All packages from `clients` + `worker` + `servers` + `tools` + `recurrence`                                                                                                                                  |

### Shared Observability Package

Since `juniper-ml` 0.5.0, `juniper-observability` is also aggregated under the `[tools]` and `[all]` extras, so a `pip install juniper-ml[all]` will install it alongside the rest of the platform. Callers that only want the shared observability primitives without the full meta-package can still install it directly:

```bash
pip install "juniper-observability[all]"
```

See [`../juniper-observability/README.md`](../juniper-observability/README.md) for its public surface and independent release workflow.

---

## 2. Verify

```bash
# Check installed packages
pip list | grep juniper
```

Expected output (with `[all]`): 18 lines, one per package. The versions are what `juniper-ml` 0.11.4
resolved to on 2026-11-07 (`pip install --dry-run` against PyPI on Python 3.12, 3.13 and 3.14, which agree).
A later release inside each extra's range (the table above) is expected, not a failure. Two of these
packages come in transitively: `juniper-cascor-model` and `juniper-cascor-protocol`.

```bash
juniper-canopy              0.9.x
juniper-cascor              0.13.x
juniper-cascor-client       0.8.x
juniper-cascor-model        0.1.x
juniper-cascor-protocol     0.2.x
juniper-cascor-worker       0.6.x
juniper-ci-tools            0.9.x
juniper-config-tools        0.1.x
juniper-data                0.17.x
juniper-data-client         0.6.x
juniper-doc-tools           0.1.x
juniper-ml                  0.11.4
juniper-model-core          0.3.x
juniper-observability       0.4.x
juniper-recurrence          0.8.x
juniper-recurrence-client   0.3.x
juniper-recurrence-model    0.6.x
juniper-service-core        0.7.x
```

```python
# Verify client imports
from juniper_data_client import JuniperDataClient
from juniper_cascor_client import JuniperCascorClient
from juniper_cascor_worker import CandidateTrainingWorker
```

REST `base_url` is normalised at construction on GitHub-main of the three HTTP clients (whitespace, case-insensitive `http(s)://`, host required, trailing `/v1` stripped). A hostless value raises `Juniper*ConfigurationError` rather than failing inside `requests` on the first call. `pip install juniper-ml[clients]` does **not** yet require those tips — see [HTTP Client Base-URL Contract](REFERENCE.md#http-client-base-url-contract).

---

## 3. Next Steps

- [Documentation Overview](DOCUMENTATION_OVERVIEW.md) -- navigation index
- [Reference](REFERENCE.md) -- extras, compatibility, and version reference
- [juniper-config-tools](REFERENCE.md#juniper-config-tools) -- `env_with_legacy_alias`: `""` is set, the deprecation warning is silent outside `__main__`, and PyPI `0.1.1` ships `py.typed` (the `0.1.0` wheel does not)
- [Host Orchestration Utilities](REFERENCE.md#host-orchestration-utilities) -- run services on-host with `util/juniper_plant_all.bash` and `util/juniper_chop_all.bash`
- [The firewall gate reads getblockall](REFERENCE.md#the-firewall-gate-reads-getblockall) -- G-SEC passes when `--getblockall` contains `is blocking all non-essential incoming connections` and `State >= 1`; the state-2 global line and `--setblockall`'s confirmation do not decide block-all
- [Conda Env Torch Shadow Diagnostic](REFERENCE.md#conda-env-torch-shadow-diagnostic-p-5) -- classify `import torch` / `torch._C` (exit **2** = P-5 free-threaded; exit **4** = May-7; does not rebuild)
- [Environment Floor Drift — Malformed Input](REFERENCE.md#malformed-operator-input) -- `env_floor_drift_check.py` exit 2 is a resolution failure, including a truthy non-mapping in `ecosystem.yaml`; a bad extra does not drop `dependencies` floors
- [Cascor Primary Freeze Tell](REFERENCE.md#cascor-primary-freeze-tell) -- whether a live importer holds the cascor primary; exit 0 is "no user-owned importer", not "no importer"
- [Fleet Triage and Sequence Safety](REFERENCE.md#fleet-triage-and-sequence-safety) -- `predict_merge` + `Allow-Docs-Rewrite` trailer parity (#926)
- [Resident-Hazard Gap Triage](REFERENCE.md#resident-hazard-gap-triage) -- re-run after an `AGENTS.md` cut; the candidate count grows by construction (health is score ≥ 3)
- [Ruleset Context Audit](REFERENCE.md#ruleset-context-audit) -- why a required name that never reports leaves `main` unmergeable; re-run, do not quote the 2026-08-10 §1 counts
- [Flood-Remediation CI Gates](REFERENCE.md#flood-remediation-ci-gates) -- G4 pre-commit split, required Sequence Safety (outside the Quality Gate) and advisory Fleet PR Lint, post-merge `main-verify` catch-up
- [Post-Merge Main Verification](REFERENCE.md#post-merge-main-verification) -- G3 / G3.1 catch-up BASE, stable-title failure notify, trailers vs labels, battery path-gate
- [YubiKey GPG Provisioning](REFERENCE.md#yubikey-gpg-provisioning) -- ed448-on-card caveat + pointer to the validated transfer procedure
- [Juniper Project-Tree Backup](REFERENCE.md#juniper-project-tree-backup) -- per-repo `.tbz2.gpg` to external media; restore with `tar -xjf`; not the Duplicati `$HOME` lane
- [Yamaguchi Duplicati Server Client](REFERENCE.md#yamaguchi-duplicati-server-client) -- server on `127.0.0.1:8300`; `export` needs a single-operation token; the watchdog has no default `--backup-id`
- [The failed-auth table drops the oldest source IPs](REFERENCE.md#the-failed-auth-table-drops-the-oldest-source-ips) -- 10,000-IP cap on `FailedAuthThrottle`; an evicted IP is not blocked, and `check()` does not put it back
- [Phase D Trial Drop-In and Settings-Key Write](REFERENCE.md#phase-d-trial-drop-in-and-settings-key-write) -- throwaway `duplicati-trial` drop-in (wrapper off `/run`); Procedure A re-derives the settings key and never prints it
- [Host-Check Wording](REFERENCE.md#host-check-wording-e-h3) -- a turing kubectl failure names task D3 (Docker Desktop) before D4; G-MEM says `free + speculative + inactive` while `macvm_ctl` says `free + inactive` for the same MiB
- [Open-PR Budget Alarm](REFERENCE.md#open-pr-budget-alarm) -- daily report-only open-PR / `cursor/` queue guardrail
- [Ruleset Scope Guard](REFERENCE.md#ruleset-scope-guard) -- `~ALL` re-arms deleted dependabot/Copilot bypass rows; exit 2 is not clean
- [Experiment Stack Utilities](REFERENCE.md#experiment-stack-utilities) -- per-run cascor/recurrence experiments via `util/experiment_stack.bash` + `run_experiment.py` (failed `--up` auto-tears down)
- [Recurrence Env Preflight](REFERENCE.md#recurrence-env-preflight) -- W0.2 (juniper-ml#2139): the recurrence leg refuses a stale env before `serve` (scoped `pip check`, installed pins, `derive_full_split`); `--skip-env-preflight` warns and still serves
- [Replay speed, range, and a paused completion](REFERENCE.md#replay-speed-range-and-a-paused-completion) -- shared replay speed clamps to [-10, 10] and sleeps at most 0.5 s per frame; a fit that returns while paused settles COMPLETED (unreleased; first in the juniper-service-core release after 0.7.2; 0.7.2 and earlier stay wedged, PAUSED and then STARTED after a resume, until stop or reset)
- [Crossval 500 with model-core 0.2.0](REFERENCE.md#crossval-500-with-model-core-020) -- `juniper-recurrence` 0.8.0 plus `juniper-model-core` 0.2.0 passes preflight, then every `POST /v1/crossval` is an unhandled `groups=` `TypeError` (HTTP 500). Fixed in 0.8.1 (PyPI 2026-11-06): upgrade `juniper-recurrence`, or install `juniper-model-core[crossval]>=0.3.0,<0.4.0` to stay on 0.8.0
- [Recurrence launch record and service env](REFERENCE.md#recurrence-launch-record-and-service-env) -- `save_model` saves the scored model by `operation_id` (a pre-W1.5 service re-runs the launcher-recorded CLI under interpreter and model-version parity instead); per-run recurrence snapshots dir
- [A failed snapshot save does not re-fit](REFERENCE.md#a-failed-snapshot-save-does-not-re-fit) -- with an `operation_id`, a non-201, a dropped connection, a bad `size_bytes`, or a copy error is `degraded` (exit 1) and does not call the CLI. A bad copy deletes `model.npz`.
- [PF Scenario Suites](REFERENCE.md#pf-scenario-suites) -- Wave 7.3 instruments (`--dry-run` first; PF-1 matched 4000/4000 epochs; `JUNIPER_SUITE_GRAFANA_BRIDGE`; PF-4/PF-8 are not driver suites)
- [Perf-Lane Work Gate](REFERENCE.md#perf-lane-work-gate) -- `read_run_metrics` / `make_baseline` / `compare_baseline`; sound since ml#1743, but **never** wire the exact `step_count` gate to CI — P1 design §6 closed 2026-09-07; host identity blocks on hosted runners, so it would exit 2 REFUSED every time
- [Equities Symbol Cap](REFERENCE.md#equities-symbol-cap) -- default `equities` / `equities_seq` is 422 at 14 symbols (cost is per request; silent slice deleted in data#354)
- [Equities Dataset Id Does Not Pin Array Content](REFERENCE.md#equities-dataset-id-does-not-pin-array-content) -- one `dataset_id` can be two arrays; compare `meta.checksum` before quoting a crossval r²
- [Recurrence Equities Crossval Instruments](REFERENCE.md#recurrence-equities-crossval-instruments) -- re-run the E-H W0.8/W0.9 scripts; exit 0 is not a passing crossval
- [Canopy E2E Matrix Writes](REFERENCE.md#canopy-e2e-matrix-writes) -- fill / set-verdicts / rescore for the click-by-click ledger (fill is dry-run; set-verdicts is not)
- [F-CANOPY-027 Poller Starvation Probes](REFERENCE.md#f-canopy-027-poller-starvation-probes) -- 12-slot dash-renderer starvation (FIXED); do not add a new Interval; isolated stack only
- [Worktree Divergence / in-use probe](REFERENCE.md#worktree-divergence-is-a-memory-cost) -- cwd-only liveness is not enough; STRONG cwd/open-fd vs WEAK cmdline
- [Canopy E2E Finding Triage](REFERENCE.md#canopy-e2e-finding-triage) -- header-only P0/P1 open-count; ACCEPTED is a third disposition; WITHDRAWN (`WITHDR`) is a fourth; always exits 0
- [CSV Import Byte Cap](REFERENCE.md#csv-import-byte-cap) -- csv_import 128 MiB bound (422 until opt-in); experiment-stack `IMPORT_DIR` pitfall; equities is capped in symbols instead ([Equities Symbol Cap](REFERENCE.md#equities-symbol-cap))
- [F-CANOPY-037 Render Census](REFERENCE.md#f-canopy-037-render-census) -- 11-session topology-graph paint tally; exit 0 is not a paint PASS
- [Defect Register Close Protocol](REFERENCE.md#defect-register-close-protocol) -- `**FIXED` token, cwd pitfall, third reading vs the two §4 counters
- [Pointer-Follow Soak](REFERENCE.md#pointer-follow-soak) -- unprimed probe loop, characterisation vs least-covered, `--force` on terminal verdicts
- [Canopy E2E Topology Driver](REFERENCE.md#canopy-e2e-topology-driver) -- Playwright scorer for Topology-tab rows; `STEPS` is the authority; M-06/M-07/M-12 can PASS the easier half
- [Snapshot Sidecar Chain](REFERENCE.md#snapshot-sidecar-chain) -- index / classify / backfill the cascor archive (`--root`, not `JUNIPER_CASCOR_SNAPSHOTS_DIR`)
- [Recurrence Work Is Not Countable](REFERENCE.md#recurrence-work-is-not-countable) -- PF-5/6/7 report-only; `read_run_metrics.py --json`; `make_baseline` / `compare_baseline` refuse a recurrence suite
- [Recurrence Crossval Hyperparameters](REFERENCE.md#recurrence-crossval-hyperparameters) -- a crossval body without the `train:` keys is linear at `default_ridge` (0.0); RFF's omitted ridge is `gcv`; the call fits a fresh model per fold
- [Recurrence Upstream Error Text](REFERENCE.md#recurrence-upstream-error-text) -- a recurrence 502 `detail` can contain a rejected data API key; the experiment driver copies it into `manifest.json`. Do not paste that file.
- [One caller per recurrence service](REFERENCE.md#one-caller-per-recurrence-service) -- a busy `POST /v1/train` is a `409`; the driver does not cancel a timed-out fit
- [Perf-lane metrics and baselines](REFERENCE.md#perf-lane-metrics-and-baselines) -- `read_run_metrics.py` / `make_baseline.py`; gate `step_count` exactly, never `wall_seconds` or `timings.drive`
- [Perf-Lane Split Comparator](REFERENCE.md#perf-lane-split-comparator) -- `compare_baseline.py`: identity first, work exact / speed reported, exit 0/1/2 (#1622)
- [Canopy E2E Matrix Writes](REFERENCE.md#canopy-e2e-matrix-writes) -- fill / set-verdicts / rescore for the click-by-click ledger (fill is dry-run; set-verdicts is not)
- [F-CANOPY-027 Poller Starvation Probes](REFERENCE.md#f-canopy-027-poller-starvation-probes) -- 12-slot dash-renderer starvation (FIXED); do not add a new Interval; isolated stack only
- [Worktree Divergence / in-use probe](REFERENCE.md#worktree-divergence-is-a-memory-cost) -- cwd-only liveness is not enough; STRONG cwd/open-fd vs WEAK cmdline
- [Canopy E2E Finding Triage](REFERENCE.md#canopy-e2e-finding-triage) -- header-only P0/P1 open-count; ACCEPTED is a third disposition; WITHDRAWN (`WITHDR`) is a fourth; always exits 0
- [Suite Report Gate Inputs](REFERENCE.md#suite-report-gate-inputs) -- `run_suite` `aggregate.csv` / `REPORT.md` carry `step_count` + mean step; `--compare-baseline` is reporting only (P2 1.4 / #1643)
- [Suite Report Gate Inputs](REFERENCE.md#suite-report-gate-inputs) -- `run_suite` `aggregate.csv` / `REPORT.md` carry `step_count` + mean step; `--compare-baseline` is reporting only (P2 1.4 / #1643)
- [Run lister / pruner](REFERENCE.md#run-lister--pruner-list_runspy) -- `list_runs.py` directory-truth scan; `--prune` deletes the `RUN_DIR`, `--down` keeps `artifacts/`
- [Suite Driver](REFERENCE.md#suite-driver) -- multi-cell `run_suite.py` (expansion, resume, cascor parallel floor, Grafana env toggle)
- [Recurrence Degraded Outcome and Headline Metrics](REFERENCE.md#recurrence-degraded-outcome-and-headline-metrics) -- a lost enabled phase is `degraded` (suite exit 1); r² columns read nested `stats.recurrence`
- [An empty stats.json is not a missing file](REFERENCE.md#an-empty-statsjson-is-not-a-missing-file) -- `aggregate` prints a readable object's headline, including `{}`, and prints the registry's recorded metrics when the file is missing or not a JSON object
- [Suite driver](REFERENCE.md#suite-driver) -- multi-cell campaigns via `util/experiments/run_suite.py` (`--dry-run` / `--resume`; cascor parallel needs launched tree ≥ 0.10.0)
- [Experiment Stats Summary](REFERENCE.md#experiment-stats-summary-ss83) -- how to read `stats.json` / `summary.md` (de-ratified wall, per-poll p50/p95, scrape_confirmed tri-state)
- [A zero is a measured value](REFERENCE.md#a-zero-is-a-measured-value) -- accuracy `0` stays in `summary.md`, `eval_metrics.png`, and the `test_accuracy` column (test split); a bool is text in `summary.md` only; `train.theta: 0` stays `explicit`
- [Shared-Package CI Workflows](REFERENCE.md#shared-package-ci-workflows) -- the six in-repo `ci-<pkg>.yml` contracts (paths, floors, coverage enforce)
- [Docs Full Check](REFERENCE.md#docs-full-check) -- weekly cross-repo link validation + the `ECOSYSTEM_REPOS` clone-list lockstep
- [Scheduled Security Scan and Lockfile Update](REFERENCE.md#scheduled-security-scan-and-lockfile-update) -- weekly `pip-audit --strict` + the lockfile refresh PR (header dates and a new snapshot pair are expected even when pins did not move)
- [CodeQL Analysis](REFERENCE.md#codeql-analysis) -- `Analyze (python)` can be green while merge stays `BLOCKED`; **File is not always closed** is a bare `open()` (use `with`); do not dismiss the thread
- [Release-Train Detect Summary and Slack](REFERENCE.md#release-train-detect-summary-and-slack) -- action set vs the ceremonial class, hard-fail banner
- [AGENTS.md Date Check](REFERENCE.md#agentsmd-date-check) -- verifies `**Last Updated**:` was bumped on PRs touching `AGENTS.md`
- [The MERGED line's SHA is the verified head](REFERENCE.md#the-merged-lines-sha-is-the-verified-head) -- `safe_merge` prints the pull request head; the squash commit is `gh pr view --json mergeCommit`
- [Claude.yml Access Validation](REFERENCE.md#claudeyml-access-validation) -- L2/L3 `ANTHROPIC_API_KEY` safeguards + `DEFAULT_REPOS` fan-out
- [Idle compaction and the tracked settings file](REFERENCE.md#idle-compaction-and-the-tracked-settings-file) -- `"idleCompaction": false` in repo-root `settings.local.json` is not loaded; Claude Code reads `.claude/settings.local.json`
- [juniper-service-core](REFERENCE.md#juniper-service-core) -- body limit, 429 headers, control-WS sanitizer, `/ws/workers` contracts
- [A task assigned for exactly the reassignment timeout stays assigned](REFERENCE.md#a-task-assigned-for-exactly-the-reassignment-timeout-stays-assigned) -- equality stays assigned; any larger age requeues; the worker stays registered and its next idle heartbeat can be given the same task
- [A WebSocket text frame that fills 65536 characters is delivered](REFERENCE.md#a-websocket-text-frame-that-fills-65536-characters-is-delivered) -- equality is in; one more character closes `/ws/control` **1009** or worker registration **4005**; the worker message loop stays open
- [A body that fills the cap is delivered](REFERENCE.md#a-body-that-fills-the-cap-is-delivered) -- `RequestBodyLimitMiddleware` admits `max_bytes` exactly (both checks use `>`); the next byte is 413 and the route is not called. `GET` and `DELETE` are not stream-capped
- [A measured zero heartbeat overwrites](REFERENCE.md#a-measured-zero-heartbeat-overwrites) -- a reported `0` / `[]` replaces the prior worker reading; `None` keeps it; a heartbeat aged exactly one timeout (default 30 s) is already stale
- [Control channel edges](REFERENCE.md#control-channel-burst-origin-match-and-cooldown-edges) -- `/ws/control` banks at most its rate-limit setting, matches Origin exactly, and blocks on the Nth failed handshake (default the 10th)
- [Training-stream resume and the connection cap](REFERENCE.md#training-stream-resume-and-the-connection-cap) -- `/ws/training` replay is continuous through the seq just before the buffer; `out_of_range` keeps the socket and sends a fresh snapshot. Pending handshakes count toward close 1013. Address-less sockets share `"unknown"`
- [Non-ASCII API keys and Sentry frame locals](REFERENCE.md#non-ascii-api-keys-and-sentry-frame-locals) -- a non-ASCII `X-API-Key` is a 401 (WebSocket close 4001) from service-core 0.7.1, and observability 0.4.1's `configure_sentry` sends no frame locals; juniper-data's, juniper-cascor's and juniper-canopy's own copies compare bytes from 0.17.0, 0.12.0 and 0.9.0
- [HTTP Client Base-URL Contract](REFERENCE.md#http-client-base-url-contract) -- shared REST `_normalize_url`, TLS-downgrade pitfall, WS streams still rstrip-only
- [The worker connection bucket refills only up to its burst](REFERENCE.md#the-worker-connection-bucket-refills-only-up-to-its-burst) -- `/ws/workers` close 4029 `Rate limited` is the per-host token bucket; a source quiet past the cleanup interval is dropped at the next cleanup pass and returns with a full burst
- [X7 Off-Loop Census](REFERENCE.md#x7-off-loop-census) -- canopy event-loop blocking; count is 58 (canopy#567); the slice-1a gate is authority for `main.py` only (do not quote the v1 name-matching census)
- [Topology Step Order and Blast-Radius IDs](REFERENCE.md#canopy-e2e-topology-step-order-and-blast-radius-ids) -- `topostate` first or alone; the `W4-*` / `W1-12..14` IDs are real matrix §4 steps (F-E2E-007 claimed otherwise and was withdrawn)
- [P4 Campaign Suites](REFERENCE.md#p4-campaign-suites) -- 19 YAML catalog; `include` does not inherit `matrix`; cap-128 H2H is n=2; recurrence P4 cells report, they do not gate
- [Memory-Budget Slack (Planning)](REFERENCE.md#memory-budget-slack-planning) -- `measure-growth` sizes a ceiling; headroom below that figure is not a `Memory Budget` failure
- [F-039 Store Probe](REFERENCE.md#f-039-store-probe) -- apply / soak / report / revert when a canopy store looks empty after a correct wire response; read the whole series; `--target topology` refuses
- [CAN-015 Replay Re-drive](REFERENCE.md#can-015-replay-re-drive) -- throwaway ports off `8101`/`8202`/`8051`; replay the explicit `POST /v1/snapshots` (automatic snapshots have `length=0`); Stop before the next Start
- [MEMORY.md Index Check](REFERENCE.md#memorymd-index-check) -- local Claude Code index gate; 200/25k silent newest-first truncate; hook-not-line 120 on NEW slugs; CI cannot see `~/.claude`
- [F-CANOPY-037 Render Census](REFERENCE.md#f-canopy-037-render-census) -- 11-session topology-paint instrument; one green session is not a claim; exit 2 = failed to measure
- [X7 Off-Loop Census](REFERENCE.md#x7-off-loop-census) -- canopy event-loop blocking; slice-1a count is **58**; C5 remedy refuted
- [Train / Val / Test Partition Contract](REFERENCE.md#train--val--test-partition-contract) -- shipped NPZ still requires `*_full`; design drops it; recurrence `dataset.split: validation` is exit 2
- [Canopy E2E Dataset Drivers](REFERENCE.md#canopy-e2e-dataset-drivers) -- W6 `--steps` (no ranges; never confirm restart) vs §3.6 `--step`; `LD_LIBRARY_PATH=` + `JuniperCanopy1`
- [Pointer-Follow Soak](REFERENCE.md#pointer-follow-soak) -- unprimed probe loop; do not run n≈8–10; `--force` is an open owner decision; full slugs; `--class` on miss
- [Requirements Snapshot Consolidation](REFERENCE.md#requirements-snapshot-consolidation) -- refresh `notes/requirements/` from `by-area` (never from the ledger); `--check-roundtrip` then `--check-views`
- [Canopy E2E Unfilled-Rows Ledger](REFERENCE.md#canopy-e2e-unfilled-rows-ledger) -- plan matrix re-drives from `e2e_unfilled_rows.py` (status cells), not the TSV estimator
- [Worker Result Anomaly Detector](REFERENCE.md#worker-result-anomaly-detector) -- a fast, perfect, stale, or duplicate score is a warning; the result is still accepted. A missing duration is timed as `0.0` s
- [juniper-observability README](../juniper-observability/README.md) -- shared observability primitives
- [juniper-data-client Quick Start](https://github.com/pcalnon/juniper-data-client) -- dataset client usage
- [juniper-cascor-client Quick Start](https://github.com/pcalnon/juniper-cascor-client) -- training client usage
- [juniper-cascor-worker Quick Start](https://github.com/pcalnon/juniper-cascor-worker) -- worker setup

---

**Last Updated:** 2026-11-09
**Version:** 0.3.45
**Status:** Active
