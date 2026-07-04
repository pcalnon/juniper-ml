# Per-File Coverage Rollout — Scoping (Phase C of the Test-Suite Audit)

**Project**: Juniper ML Research Platform
**Repository**: pcalnon/juniper-ml
**Author**: Paul Calnon (session by Claude Code, custom-agent suite)
**License**: MIT License
**Document Type**: SCOPING (operationalizes Phase C of the audit plan)
**Status**: Draft — measured; owner-ratified decisions inline
**Last Updated**: 2026-06-30

---

## 0. What this is + ratified decisions

Operationalizes **Phase C** of [`JUNIPER_ECOSYSTEM_TEST_SUITE_AUDIT_PLAN_2026-06-26.md`](JUNIPER_ECOSYSTEM_TEST_SUITE_AUDIT_PLAN_2026-06-26.md) (§6 contract, §7 measurement design, §11 Phase C order) into a measured, sequenced, one-PR-per-unit backlog. **Scoping only — no gate is added by this document.**

**Owner-pinned targets (carried, not softened):** every source file ≥ **90%** line coverage; every packaged sub-module ≥ **95%** average.

**Decisions ratified this session:**

- **The ≥95% sub-module "average" = statement-weighted aggregate** (`pooled_percent = Σcovered / Σstatements`), not mean-of-files. This is consequential — measured data shows the two diverge and flip outcomes (e.g. `juniper-ci-tools`: pooled **96.02** ✓ vs mean-of-files **89.24** ✗; `service-core/routes`: pooled **92.13** ✗ vs mean **95.97** ✓). The shipped `juniper-coverage-gap-map` already computes `pooled_percent` alongside `average_percent`; the gate uses **pooled**.
- **The per-file ≥90% gate uses STATEMENT coverage** (`covered_statements / num_statements`), not branch-inclusive %. `service-core` runs `branch = true`, which dropped 3 files below 90 on branch that are ≥90 on statement (its file count is **15 (statement)** vs 18 (branch)). A statement basis keeps the gate apples-to-apples across all units.
- **Depth = measured scoping:** real per-file numbers were captured for the 9 cheaply-measurable units (§5); the 10 heavy/blocked units carry their exact measurement command + blocker (§6).

---

## 1. Tooling state — the gap to close (the C-0 enabler)

`juniper-coverage-gap-map` (in `juniper-ci-tools` ≥0.5.0; `juniper_ci_tools/coverage_gap_mapper.py` + `cli_coverage_gap_mapper.py`) **measures** the per-file distribution, files-below-threshold (default 90), and per-sub-module average vs a bar (default 95). It is **advisory by contract — "Exit 0 always; it reports, it never fails a build."**

So the rollout's prerequisite is an **enforcing mode**. Two further mapper facts shape the design:

- It already carries **both** `SubmoduleCoverage.average_percent` (mean-of-files) **and** `pooled_percent` (statement-weighted), but its current `below_bar()` / `submodules_below_bar()` gate on **`average_percent`**. The enforcing mode must gate on **`pooled_percent`** (the ratified basis).
- `FileCoverage.percent_covered` trusts `summary.percent_covered` from `coverage.json` (branch-inclusive when the repo sets `branch=true`). The enforcing mode must gate per-file on **statement %** (`covered_statements / num_statements`, both already on `FileCoverage`) for cross-unit consistency.
- numpy-2.x is already handled (package-form `--cov` + `[report] include` shim) and zero-statement files already score 100% (so `__init__.py` shims don't false-positive).

### Work-unit **C-0 — enforcing gate** (juniper-ml / juniper-ci-tools; the enabler)

Add an opt-in blocking mode to `juniper-coverage-gap-map` (advisory stays the default): e.g. `--enforce` (or `--fail-under-file 90 --fail-under-submodule 95`) → **exit 1** when, after exclusions (§2), any source file's **statement** % `< 90` OR any sub-module's **`pooled_percent` `< 95`**; print the offending files/sub-modules; exit 0 when clean. Add the excluded-files/waiver handling (§2), the mapper's own unit tests (`juniper-ci-tools/tests/`, ≥85 gate), and a dogfood test in `juniper-ml/tests/` (mirror `test_coverage_gap_mapper_drift.py`).

- **Versioning gotcha (same class as the 0.5.1 incident):** an additive flag is a **minor** bump → `0.5.1`→`0.6.0`, which **exceeds** juniper-ml's own `<0.6.0` ci-tools pins (`ci.yml`/`docs-full-check.yml`/`lockfile-update.yml`) — widen them to `<0.7.0` **in the same PR** (the `test_ci_tools_drift.py` / `test_env_drift_check_drift.py` class guard will fail loudly otherwise). A **patch** (`0.5.2`, staying `<0.6.0`) avoids the pin edits — implementer's call.
- **Verify:** `pytest --cov=juniper_ci_tools --cov-fail-under=85` green with the new mode; `juniper-coverage-gap-map --coverage-json <fixture> --enforce` exits 1 on a synthetic gap, 0 when clean; `python3 -m unittest tests/test_coverage_gap_mapper_drift.py` + the new dogfood pass.
- **Then:** owner cuts `juniper-ci-tools-v<C-0>` (Release, templated notes → `notes/releases/`) — **owner-gated** — so consumers can `pip install` the enforcing tool. (Or consumers run `python -m juniper_ci_tools.cli_coverage_gap_mapper --enforce` from a pinned install.)

---

## 2. Excluded-files & waiver policy (ratified)

- **Auto-100% already:** zero-statement files (re-export `__init__.py`) — handled by the mapper; no action.
- **Explicit exclusion allowlist** (per-repo `--omit` globs the tool applies on the parsed json): thin **`__main__.py`** / CLI entry shims that are pure `main()` dispatch (measured **0%** in `ci-tools` & `doc-tools` — 4 statements each), generated code, `bench/`, `scripts/`, `util/ad-hoc/`. Prefer a 1-line smoke test over an exclusion where cheap.
- **NOT excluded:** the shipped `testing/` sub-packages in `data-client` (pooled **99.63**) and `cascor-client` (**97.74**) — measured well-covered, so the earlier "shim dominates pooled stats" worry does **not** bear out; keep them in the gate.
- **Waivers** (a file genuinely <90 but kept): structured allowlist entry with a linked issue + expiry; the tool warns on expired waivers and an expired waiver does **not** unblock. Not a blanket `# pragma: no cover`.

---

## 3. Measured gap table — the 9 cheaply-measurable units

Captured 2026-06-30 via `juniper-coverage-gap-map` (juniper-ci-tools 0.5.1), fresh per-unit venvs, package-form `--cov`, `--cov-report=json`. `overall` = statement-pooled (service-core branch-inclusive, statement-reconciled in notes). Gate columns use the **ratified** basis (per-file statement <90; sub-module `pooled` <95).

| Unit | overall (pooled) | files <90 (statement) | sub-modules failing `pooled<95` | status |
|------|------------------|------------------------|----------------------------------|--------|
| `juniper-model-core` | **97.54** | **0** | 0 / 3 | ✅ gate-ready today |
| `juniper-cascor-protocol` | **98.94** | **0** | 0 / 3 | ✅ gate-ready today |
| `juniper-config-tools` | **96.43** | **0** | 0 / 1 | ✅ gate-ready today |
| `juniper-observability` | **98.52** | 1 (`testing.py` 89.47) | 0 / 3 | per-file nudge only |
| `juniper-data-client` | **95.80** | 1 (`client.py` 89.56) | 0 / 2 | per-file nudge only |
| `juniper-ci-tools` | **96.02** | 3 (`__main__.py` 0 → exclude; `cli_lint_agents_md_header` 87.18; `cli_lint_agents_md_version` 83.02) | 0 / 1 (pooled passes; mean-of-files would fail) | per-file nudges (+1 exclude) |
| `juniper-cascor-client` | **93.72** | 3 (`client.py` 85.03; `observability.py` 84.09; `ws_client.py` 88.39) | 1 / 1 (pkg pooled **90.29**) | real lift |
| `juniper-doc-tools` | **87.33** | 3 (`__main__.py` 0 → exclude; `check_doc_links.py` 88.18; `cli.py` 87.30) | 1 / 1 (pooled **87.33**) | real lift |
| `juniper-service-core` | **~84** (branch 81.14) | **15** (18 on branch) | **5 / 5** (websocket 76.45, workers 83.66, pkg 85.09, lifecycle 90.57, routes 92.13) | **heavy lift** |

**service-core pre-gate fixes (two real findings):** (1) `workers/metrics.py` scored **15%** only because **`prometheus_client` is missing from its `[test]` extra** (2 tests skip) — add it + re-measure (the true number is materially higher); (2) pin the statement-vs-branch basis (flips the count 15↔18 and pulls `routes` in/out). The deep work is concentrated in `websocket/` and `workers/`.

---

## 4. Deferred units (10) — measurement command + blocker

Each is measured at the start of its own rollout PR (warn-only run produces the number). None measurable in a generic CI runner without its env.

| Unit | Measure command (per-file via the mapper) | Blocker / env |
|------|--------------------------------------------|---------------|
| `juniper-canopy` | `conda run -n JuniperCanopy1` pytest the full suite `--cov=src --cov-report=json` → mapper | `JuniperCanopy1` env; today's gate is a **partial subset** (unit+regression) — measure the whole `src` |
| `juniper-cascor` | `conda run -n JuniperCascor1` `bash src/tests/scripts/run_tests.bash` w/ `--cov-report=json` → mapper | torch + `JuniperCascor1`; partial-subset (`-m "unit and not slow"`) |
| `juniper-cascor-model` | torch env; `pytest --cov=juniper_cascor_model --cov-report=json` → mapper | torch; **the no-gate outlier** — has NO coverage gate at all today (bring to per-file 90 + sub-module 95 + add a CI gate) |
| `juniper-cascor-worker` | torch env; `pytest --cov=juniper_cascor_worker --cov-report=json` → mapper | torch |
| `juniper-data` | its env; `pytest -m "unit and not slow" --cov=juniper_data --cov-report=json` → mapper | heavy deps; partial-subset; **already has an advisory per-module check** (`scripts/check_module_coverage.py`) → fold into the shared C-0 gate |
| `juniper-recurrence` (app) | `pytest --cov=juniper_recurrence --cov-report=json` → mapper | **DISC-1** — Starlette `filterwarnings` collection failure (`pyproject.toml:132`) blocks collection; **fix first** |
| `juniper-recurrence-client` | `pytest --cov=juniper_recurrence_client --cov-report=json` → mapper | **DISC-1** (same pattern) — fix first |
| `juniper-recurrence-model` | torch lane + `.coveragerc.torch` two-lane (base-omit + torch-include) → mapper per lane, union | torch |
| `juniper-ml` (meta) | n/a — **no importable package** (`packages = []`) | per-file gate **N/A**; optionally scope to `util/` only, else exempt |
| `juniper-deploy` | n/a — **no importable source** | **exempt** (compose/secret tests stay) |

---

## 5. The sequenced rollout backlog (one PR per unit; warn → blocking)

Order = enabler → free wins → small nudges → real lifts → heavy → deferred (worst-first within each band). Each unit PR: add `--cov-report=json` + the `juniper-coverage-gap-map --enforce` step in **warn-only** first, close any gap, then flip to **blocking** and move the threshold into the repo. All under worktree isolation; `gh pr list` dup-guard; no-merge-without-PR; owner merges; publishes are owner-gated.

| # | Step | Units | Verify | Acceptance |
|---|------|-------|--------|------------|
| **C-0** | enforcing gate tool + publish | juniper-ci-tools (juniper-ml) | `--enforce` exits 1 on synthetic gap / 0 clean; dogfood + ci-tools suite green | enforcing mode shipped + (owner) published; pins widened if minor |
| **C-1** | turn the gate ON, blocking — **free wins** | `model-core`, `cascor-protocol`, `config-tools` | each: mapper `--enforce` exits 0 today | blocking per-file 90 + sub-module 95 gate live; no coverage work needed |
| **C-2** | close the handful of per-file gaps, then gate | `observability` (testing.py), `data-client` (client.py), `ci-tools` (exclude `__main__`, lift 2 lint CLIs) | mapper `--enforce` exits 0 after the small tests | each named file ≥90; gate blocking |
| **C-3** | real coverage lifts, then gate | `doc-tools` (pooled 87→95; check_doc_links/cli + exclude `__main__`), `cascor-client` (pkg pooled 90→95; client/observability/ws_client) | mapper `--enforce` exits 0 | pooled ≥95 + all files ≥90; gate blocking |
| **C-4** | heavy lift | `service-core` (fix `[test]` prometheus_client + pin branch basis FIRST; then websocket/ + workers/ + the long tail) | mapper `--enforce` exits 0 (statement basis) | 5/5 sub-modules pooled ≥95; all files ≥90; gate blocking |
| **C-5** | deferred / heavy-env units (measure→lift→gate, worst-first after measurement) | `cascor-model` (also add its first gate), `canopy`, `cascor`, `cascor-worker`, `data`, `recurrence-model`, then `recurrence`-app/-client **after DISC-1** | each in its env per §4 | per-unit per-file 90 + pooled 95; gate blocking |
| — | special-cased | `juniper-ml` meta (scope to `util/` or exempt), `juniper-deploy` (exempt) | n/a | documented exemption |

**Owners:** C-0/C-1/C-2 + meta = juniper-ml; ci-tools/doc-tools/config-tools/observability/model-core/service-core = juniper-ml (sub-modules); cascor-client/cascor-worker/data-client/data = their repos; cascor + cascor-model + cascor-protocol = juniper-cascor; canopy = juniper-canopy; recurrence×3 = juniper-recurrence (DISC-1 first).

---

## 6. Risks & notes

- **Pooled-vs-mean divergence is real** (ci-tools, service-core/routes) — gating on the wrong basis would mis-classify units. Gate on `pooled_percent` (ratified); the advisory mapper's `below_bar` (mean) is for the human report only.
- **Branch-vs-statement** changes per-file counts (service-core 15↔18) — gate on statement (ratified); the C-0 tool must compute statement % per file, not trust branch-inclusive `summary.percent_covered`.
- **Large legacy / heavy-env units** (cascor, data, canopy, service-core) are the bulk of the work and need their conda env + (cascor/worker/recurrence-model) torch; warn-only first avoids a flag-day red CI.
- **DISC-1 gates recurrence** app+client measurement — must be fixed before C-5 reaches them.
- **`cascor-model` is the no-gate outlier** — C-5 both lifts it and adds its first CI gate.
- **Versioning**: the C-0 minor bump repeats the `<0.6.0`-pin-widen requirement (the env-drift-check 0.5.1 lesson) — the existing class guard catches it.
- **Partial-subset gates** (cascor, canopy, data) measure the whole `src` tree from a unit-only subset today — the per-file rollout measures against the suite actually run; flag any file only reachable by an excluded subset.

---

## 7. Appendix — measurement reproduction

```bash
# Per unit (cheaply-measurable): fresh venv, editable install + the mapper, package-form --cov to /tmp.
python3 -m venv /tmp/cov-<unit>
/tmp/cov-<unit>/bin/pip install -e "<dir>[test]" "juniper-ci-tools==0.5.1"
cd <dir> && COVERAGE_FILE=/tmp/.cov-<unit> /tmp/cov-<unit>/bin/python -m pytest \
    --cov=<import_pkg> --cov-report=json:/tmp/<unit>.json -q -p no:cacheprovider
/tmp/cov-<unit>/bin/juniper-coverage-gap-map --coverage-json /tmp/<unit>.json \
    --file-threshold 90 --submodule-bar 95            # add --enforce once C-0 ships
```

Measured set (2026-06-30): observability, service-core, model-core, ci-tools, config-tools, doc-tools, data-client, cascor-client, cascor-protocol. Repos stayed clean (coverage artifacts redirected to `/tmp`).

---
