# juniper-recurrence — Pre-commit / Testing / CI Audit

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Subject repo**: `pcalnon/juniper-recurrence`
**Author**: Paul Calnon
**Prepared by**: Claude Code (Opus 4.8)
**Date**: 2026-06-21
**Status**: Findings report — read-only audit, no fixes applied (remediation = backlog in §9)
**License**: MIT License
**Method**: 5 parallel evidence-cited auditors (read-only) + owner spot-verification of all CRIT/HIGH findings. Rubric: [`notes/JUNIPER_2026-06-19_JUNIPER-ECOSYSTEM_PRECOMMIT-TESTING-AUDIT-PLAN.md`](JUNIPER_2026-06-19_JUNIPER-ECOSYSTEM_PRECOMMIT-TESTING-AUDIT-PLAN.md) (Areas A/B/C). This is the deep-dive execution of that ecosystem plan scoped to the one repo it flagged as having **no pre-commit and no root pyproject**.

**Checkout audited**: `2fd2b81` (clean working tree). At audit time this was 2 commits behind `origin/main` `036fde7` (both bench-only equities-rebench). `origin/main` advanced **during this session** to `461fc4a` — HEAD is now **6 behind**, and the newer commits include the DP-3 P1 readout work (recurrence #30/#31), which is **not** bench-only. Model-package line-refs/findings should therefore be re-confirmed against the tip before remediation; the structural findings (no pre-commit, no coverage config, model-CI lint gap, stale AGENTS.md) are unaffected. Sibling repos under `…/Juniper/` are the desired-state baseline.

---

## 1. Executive summary

`juniper-recurrence` is **not** the "pre-implementation scaffold" its own `AGENTS.md` still claims — it is a live **4-sub-project monorepo** (FastAPI app `juniper-recurrence/`, model `juniper-recurrence-model/`, HTTP client `juniper-recurrence-client/`, and a `bench/` harness) with **three packages already published to PyPI**. The *package-level* engineering is genuinely good: clean static-version wiring, sane publish-first-aware internal pins, a best-in-class set of OIDC / TestPyPI-first publish workflows, strong route/behavioral test suites, and seeded-deterministic numeric model tests that pass the shared `juniper-model-core` conformance kit. The problems are almost entirely at the **repo-governance and CI-breadth layer**, exactly where a fast-scaffolded new repo accrues debt.

Three defects rise to **critical**: (1) the repo has **zero local pre-commit governance** — no `.pre-commit-config.yaml` anywhere, so secrets, private keys, malformed YAML/TOML, and unformatted code can all be committed with no gate, and CI `ruff` is the *only* lint that ever runs; (2) the **root `AGENTS.md` is badly stale** — the single most-read agent/onboarding file describes a state ("app not yet scaffolded", "WS-0 not ratified", layout showing only the model dir) that is contradicted by three live PyPI releases; (3) the **`bench/` suite is collected by no CI lane at all** — `bench/test_bench_smoke.py` (6 tests guarding the Δt thesis: LMU-beats-naive, var-Δt-beats-fixed-Δt, noise-robustness) never runs, because the app CI runs from `working-directory: juniper-recurrence/` with `testpaths=["tests"]` and `bench/` is a sibling of that dir.

Beyond those, a consistent **High-severity cluster** repeats across packages: **no `[tool.coverage.*]` config anywhere** (the `--cov-fail-under=90` gate lives only in CI YAML — invisible and unenforceable locally, and statement-only because `branch=true` is never set); the **model package CI has no lint job at all** (its `[tool.ruff]` is dead config in CI); the **autoload-SIGSEGV guard** (`-p no:dash -p no:playwright`) is missing from the app and model `addopts` though the client carries it; **no required-checks aggregation gate** exists in any CI workflow; and there is **no `pip-audit`/security scanning** of three published packages' dependency trees. The repo also sits **entirely outside the ecosystem's doc-tools / ci-tools / pre-commit governance**.

**Net:** the code and the publish pipeline are solid; the **safety net and the docs are not**. None of the remediation is large — most of the highest-leverage fixes are sub-hour, and Auditor 1 has already designed the complete target pre-commit profile (§8). No `torch` is involved (numpy-only), so the usual heavy-env hazards do not apply.

### Severity tally (consolidated, de-duplicated)

Counts are exact enumerations of the finding IDs in §4/§5/§7 (PC-4 ≡ CI-2 cross-listed, counted once). Item lists are keyed by ID; see the area sections for full text.

| Severity | Count | Items |
|---|---|---|
| **CRIT** | 3 | PC-1 no pre-commit; DEP-1 stale root AGENTS.md; TST-1 bench/ ungated by CI |
| **HIGH** | 10 | PC-2 no secret/key detection; PC-3 no bandit; PC-4/CI-2 model-CI no lint; TST-2 no coverage config; TST-3 app suite un-runnable locally (no on-host env); TST-4 autoload guard missing (app+model); CI-1 no required-checks gate; CI-3 no security/pip-audit; DEP-2 app README version drift; DEP-3 bench deps undeclared |
| **MED** | 17 | PC-5 no md/yaml/file-check hooks; PC-6 no async-audit/shellcheck/pre-push wiring; TST-5 no warnings policy; TST-6 bench evaluator untested; TST-7/8/9 client request-id / EventSink / model-ctor untested; CI-4 push-only-on-main; CI-5 no wheel-install smoke; CI-6 docker job no `needs:`; CI-7 no docs-link job; CI-8 no concurrency groups; CI-9 model coverage gate < analog; DEP-4 outside doc/ci-tools governance; DEP-5 model-core runtime floor understates capability; DEP-6 uncapped dep floors; DEP-8 ml `[recurrence]` extra omits client |
| **LOW** | 17 | PC-7..10; TST-10..15; CI-10/11; DEP-7 (port cross-ref nit); DEP-9..12 — see §4–§7 tables |
| **INFO** | 4 blocks | positives + non-applicable confirmations (§4 / §5 / §7-CI / §7-deps) |

---

## 2. Repo state at a glance

| Sub-project | PyPI | Version (`_version.py`) | CI workflow | Lint in CI | Tests | Coverage config |
|---|---|---|---|---|---|---|
| `juniper-recurrence/` (app) | ✅ live | `0.1.1` | `ci-recurrence-app.yml` | ✅ `lint` job | 9 modules, route-complete | ❌ none (`--cov-fail-under=90` CI-only) |
| `juniper-recurrence-model/` | ✅ live | `0.1.2` | `ci-recurrence-model.yml` | ❌ **no ruff step** | 56 tests, conformance-passing | ❌ none |
| `juniper-recurrence-client/` | ✅ live | `0.1.0` | `ci-recurrence-client.yml` | ⚠️ folded into test job | 33 tests, HTTP fully mocked | ❌ none |
| `bench/` | n/a (not a package) | n/a (no `pyproject.toml`) | ❌ **none** | ❌ none | 6 tests **never run in CI** | n/a |

**Repo-root governance present**: `.gitignore`, `LICENSE`, `README.md`, `AGENTS.md`(+`CLAUDE.md` symlink), `.github/` (7 workflows + CODEOWNERS).
**Repo-root governance absent**: `.pre-commit-config.yaml`, root `pyproject.toml`, `.markdownlint.yaml`, `.gitattributes`, `.sops.yaml`, `.yamllint`, `MANIFEST.in` (any package).

---

## 3. Scope & method

- **Units**: pre-commit/governance → per repo; testing → per package (app, model, client, bench); CI → per workflow (7).
- **Verticals (parallel auditors)**: (1) pre-commit & lint governance; (2) CI & publish workflows; (3) testing — app + bench; (4) testing — model + client; (5) dependencies, metadata, versioning, docs.
- **Anti-hallucination**: every finding cites `file:line`. All CRIT/HIGH findings were owner-spot-verified directly (coverage-section absence, model-CI lint gap, README version drift, autoload-guard placement, checkout currency — see the verification block in the session transcript).
- **Out of scope**: applying fixes (backlog only); dynamic full-suite runs (no recurrence conda env exists on-host — see TST-H3); CI matrix certification (a single-host audit cannot certify the 3.12/3.13/3.14 matrix — recorded as a parity statement, not a pass).

---

## 4. Area A — Pre-commit & lint governance

### [CRIT] PC-1 · No `.pre-commit-config.yaml` — the entire repo has zero local hooks  (A1, C5)
- **What**: No pre-commit configuration exists anywhere; commits to all 4 sub-projects bypass every hook the rest of the fleet enforces (file checks, secret/private-key detection, markdown/yaml/shell lint, formatting). CI `ruff` is the only lint that ever runs, and it does not run for the model package at all (CI-2).
- **Evidence**: `find . -name .pre-commit-config.yaml` → none; `git log --oneline --all -- .pre-commit-config.yaml` → empty (never existed). Owner-verified.
- **Baseline**: every active sibling ships one — `juniper-ml/.pre-commit-config.yaml:58`, `juniper-data/.pre-commit-config.yaml:51`, `juniper-cascor/.pre-commit-config.yaml:74`.
- **Impact**: secrets/keys/merge-markers/malformed config/unformatted code are committable with no local gate. Largest single governance gap in the repo.
- **Action**: add a root `.pre-commit-config.yaml` per the **target profile in §8** (ruff-stack, mirroring `juniper-data`, scoped across all 4 sub-trees) + a `.markdownlint.yaml`.

### [HIGH] PC-2 · No secret / private-key detection anywhere  (A6)
- **What**: nothing scans for committed private keys or unencrypted `.env` — no `detect-private-key`, no `no-unencrypted-env`, no `.sops.yaml`. The service handles real `X-API-Key` secrets at runtime (client `client.py` header documents `_FILE` Docker-secret indirection).
- **Evidence**: no pre-commit config; `find . -name .sops.yaml` → none.
- **Baseline**: `juniper-ml/.pre-commit-config.yaml:87-88` (`detect-private-key`) + `:253-260` (`no-unencrypted-env`); identical in `juniper-data:80-81,257-265`.
- **Impact**: an API-key-handling service with no secret-scan gate; a `.env`/`.pem` could be committed silently.
- **Action**: include `detect-private-key` + the local `no-unencrypted-env` hook in the new config (in §8 profile).

### [HIGH] PC-3 · No bandit security scan over app/model/client source  (A6)
- **What**: no bandit anywhere, despite the app being a network-facing FastAPI service with auth + rate-limiting middleware (`app.py`: `RequestBodyLimitMiddleware → SecurityHeadersMiddleware → SecurityMiddleware`).
- **Evidence**: no pre-commit config; no `[tool.bandit]` in any of the 3 pyprojects.
- **Baseline**: `juniper-data/.pre-commit-config.yaml:143-151` (bandit `--skip=B101,B311`, excludes tests); `juniper-cascor:243-256`.
- **Impact**: no automated detection of subprocess/shell, insecure-deserialization, or hardcoded-bind classes in service code.
- **Action**: bandit hook scoped to the 3 source dirs (excl. `tests/`), `--skip=B101,B311`.

### [HIGH] PC-4 · Model-package CI runs no lint — `[tool.ruff]` is dead config in CI  (A4, C4)
*(cross-listed as CI-2; counted once in the tally)*
- **What**: `ci-recurrence-model.yml` has only `test` + `build` jobs; the most algorithmically dense package (the LMU model) is the only one with no lint gate.
- **Evidence**: owner-verified — `grep -niE "ruff|lint" ci-recurrence-model.yml` → none. Contrast `ci-recurrence-app.yml:57-58` (`ruff check .`) and `ci-recurrence-client.yml:61-62`.
- **Baseline**: app/client CIs in this same repo both run ruff.
- **Action**: add a `lint:` job to `ci-recurrence-model.yml` (`working-directory: juniper-recurrence-model`). The §8 pre-commit also covers it locally.

### [MED] PC-5 · No markdownlint / yamllint / general-file-check hooks  (A1, A5)
- **What**: 13 tracked `.md` files + 7 workflow YAMLs are governed by no markdownlint, yamllint, or `check-yaml`/`check-toml`/`check-merge-conflict`/`end-of-file-fixer`/`trailing-whitespace`.
- **Evidence**: no pre-commit config; no `.markdownlint.yaml`.
- **Baseline**: `juniper-data/.pre-commit-config.yaml:55-81` (file-check block), `:156-162` (yamllint), `:169-182` (markdownlint).
- **Impact**: malformed workflow YAML (the class that broke 3 CIs on 2026-05-18) or broken-TOML pyproject is uncaught locally.
- **Action**: add the standard `pre-commit-hooks` block + yamllint + markdownlint + a `.markdownlint.yaml` (copy `juniper-ml/.markdownlint.yaml`, line-length 512).

### [MED] PC-6 · No `default_install_hook_types`/`default_stages`; no async-route audit; no shellcheck  (A2, A11, A5)
- **What**: with no config, no pre-push stage can self-wire; the FastAPI app has **no async-route audit** (the BUG-JD-10 sync-in-async class the fleet hardened across 4 repos); no shellcheck (vacuous today — zero shell — but a forward gap).
- **Evidence**: no pre-commit config; app is async (FastAPI). Baseline async audit: `juniper-data:105-110` (`--select ASYNC`), `juniper-cascor:138-146`.
- **Action**: in §8 profile set `default_install_hook_types: [pre-commit, pre-push]`; add `ruff-async-audit` scoped to the app source; include shellcheck (no-ops cleanly).

### [LOW] PC-7…PC-10 (compressed)
| ID | Finding (A-dim) | Evidence | Action |
|---|---|---|---|
| PC-7 | ruff rev will diverge — local ruff `0.15.13` vs fleet pin `v0.15.2` (A3/A9) | `.ruff_cache/0.15.13`; fleet `rev: v0.15.2` | pin to fleet `v0.15.2` for lockstep |
| PC-8 | no `ci:` autoupdate block (A9) | no config | add `autofix_prs:false`, `autoupdate_schedule:monthly` |
| PC-9 | `.ruff_cache/` not in `.gitignore` (A1) | `.gitignore` lacks the line | add `.ruff_cache/` |
| PC-10 | no `.gitattributes` (line-ending norm) (C4) | `find` → none | add `* text=auto` (LFS only if binaries land) |

**INFO (positives)**: all 3 sub-package `[tool.ruff]` blocks are consistent & correct (line-length 512, `target-version py312`, `select=[E,F,W,B,I,N]`, sensible `N803/N806` ignores for ML matrix names) — the lint *rules* are right, only *enforcement wiring* is missing. Pure-ruff stack (no black/isort/flake8/mypy) is the correct modern target (follow `juniper-data`, not ml's legacy black-stack). Source modules correctly use docstring headers (banner header is config-file-only, per fleet convention).

---

## 5. Area B — Testing infrastructure

### [CRIT] TST-1 · `bench/` test suite is collected by zero CI lanes  (B2, B15)
- **What**: `bench/test_bench_smoke.py` (6 tests guarding the core Δt thesis) never runs in CI. The app CI sets `working-directory: juniper-recurrence/` and the app pytest config sets `testpaths=["tests"]`; `bench/` is a *sibling* of `juniper-recurrence/`, so it is unreachable. No workflow references `bench` at all.
- **Evidence**: `ci-recurrence-app.yml:68-69,82`; app `pyproject.toml:84` `testpaths=["tests"]`; `grep bench .github/` → none. Verified: `cd juniper-recurrence/ && pytest --co` collects only `tests/`; `cd <root> && pytest bench/ --co -q` → 6 collected, exit 0.
- **Impact**: the benchmark harness — the repo's scientific raison d'être — can rot silently; a refactor of `bench.datasets`/`bench.baselines` that breaks the Δt claim ships green.
- **Action**: add a `bench` CI lane (path-scoped to `bench/**`) installing `.[test,bench]` and running `python -m pytest bench/` **from the repo root** (so `import bench` resolves); or give `bench/` its own minimal `pyproject.toml` + workflow.

### [HIGH] TST-2 · No `[tool.coverage.*]` in any package — gate is CI-only, non-branch, unenforceable locally  (B4)
- **What**: none of the 3 pyprojects declare `[tool.coverage.run]`/`[report]`, and none put `--cov` in `addopts`. The only gate is `--cov-fail-under=90` baked into CI YAML — so a local `pytest` produces **no coverage and no gate** (surprise-at-CI), and because `branch=true` is never set, even CI's 90% is **statement-only**.
- **Evidence**: owner-verified — `grep -rn "tool.coverage" */pyproject.toml` → none; `--cov-fail-under=90` in all 3 workflows (`ci-recurrence-{app:82,client:66,model:62}.yml`).
- **Baseline**: `juniper-canopy/pyproject.toml:379-418` and `juniper-cascor/pyproject.toml:225-251` ship full `[tool.coverage]` with `branch=true`; client baselines `juniper-data-client:113-140`, `juniper-cascor-client:121-140` likewise.
- **Impact**: branch blind-spots (the many `if x is None` / error-mapping branches) count as covered; local/CI parity gap; the "90" intent is unrecorded (and exceeds the documented 80% target with no codified rationale).
- **Action**: add `[tool.coverage.run]` (`source`, `branch=true`, `omit=["*/tests/*"]`) + `[tool.coverage.report]` (`fail_under=90`, `exclude_lines`, `show_missing`) to all 3; optionally add `--cov=… --cov-report=term-missing` to `addopts` so local runs enforce the CI bar.

### [HIGH] TST-3 · No on-host env + CI-only coverage = app suite is un-runnable locally  (B11/B12)
- **What**: no conda env on-host carries the app's deps; the active `JuniperCascor1` lacks `juniper_service_core`, so a local `pytest` aborts at collection for every route/smoke/metrics module. Compounds TST-2: the gate is both CI-only by config *and* un-runnable locally for lack of an env.
- **Evidence**: verified — `cd juniper-recurrence/ && python -m pytest --co -q` (env `JuniperCascor1`) → `ModuleNotFoundError: No module named 'juniper_service_core'`, exit 2 (model-core-only modules `test_cli/test_cli_train/test_data_adapter` DID collect → failure is dependency-scoped). `Juniper/CLAUDE.md` conda table lists no recurrence env.
- **Action**: document `pip install -e ".[test,observability]"` (or add a `JuniperRecurrence` env to the ecosystem table) + the exact invocation in AGENTS.md.

### [HIGH] TST-4 · Autoload-SIGSEGV guard missing from app + model `addopts`  (B8)
- **What**: app & model omit `-p no:dash -p no:playwright`, the fleet-standard defense against the dash/playwright pytest plugins auto-loading from a shared conda env and segfaulting at collection. The client (same repo) carries it; the two others are the gap.
- **Evidence**: owner-verified — app & model `addopts` MISSING the guard; client HAS it (`juniper-recurrence-client/pyproject.toml:62-63`, comment "Ecosystem-standard autoload SIGSEGV defense").
- **Baseline**: `juniper-ml/juniper-model-core/pyproject.toml:75`; `juniper-cascor/pyproject.toml:181-182`.
- **Impact**: on any env with `dash`/`pytest-playwright` present (common in shared Juniper envs), collection can SIGSEGV before any test runs — esp. relevant on the 3.14t matrix legs.
- **Action**: add `"-p","no:dash","-p","no:playwright"` to app + model `addopts`.

### [MED] TST-5 · No `filterwarnings` / `-W error` policy (app, model, client)  (B6)
- **What**: no warnings policy anywhere; deprecations (pydantic v2; Starlette's deprecated `HTTP_422_UNPROCESSABLE_ENTITY` — already worked around in `_common.py:50-52`/`predict.py:64`; numpy 2.x; urllib3 2.x) pass silently.
- **Evidence**: `grep filterwarnings` → none in any package. Baseline `juniper-cascor/pyproject.toml:184-191`. *(Note: client/model baselines also lack it — partially an ecosystem-wide gap; the app vs cascor contrast is the actionable one.)*
- **Action**: add `filterwarnings=["error", <targeted ignores>]` (start app-side, matching cascor's targeted-ignore shape).

### [MED] TST-6 · Bench logic gating the Δt verdict is untested  (B15)
- **What**: `bench/test_bench_smoke.py` covers `baselines`/`datasets`, but **nothing** tests `run_benchmark.evaluate_bands` (the PASS/MISS band arithmetic, `run_benchmark.py:54-96`), `run_dataset`, `_render_report`, or `app_e2e.main`.
- **Evidence**: `grep -rn "run_benchmark\|app_e2e\|evaluate_bands" bench/test_bench_smoke.py` → none (only `baselines, datasets` imported).
- **Impact**: `evaluate_bands`' RMSE-reduction arithmetic could silently invert a verdict; the committed `bench/results/REPORT.md` could go stale vs the (untested) evaluator.
- **Action**: add a unit test feeding `evaluate_bands` a hand-built `results` dict asserting pass/fail; promote `app_e2e.main` (already uses `TestClient`) into the bench CI lane.

### [MED] TST-7…(client/model untested surfaces)  (B14, B15)
| ID | Finding | Evidence | Action |
|---|---|---|---|
| TST-7 | client `X-Request-ID` propagation branch untested (both present/absent paths) | `client.py:214-223`; no test refs `request_id_var` | test graceful no-op when observability absent + header-attached + caller-supplied-wins |
| TST-8 | `EventSink` ring-buffer eviction (`maxlen=256`) untested | `events.py:25,29`; only indirect ≤3-event coverage | overflow test with `maxlen=2` |
| TST-9 | model `time_unit`/`random_seed` ctor params never exercised non-default (latter is inert — closed-form solve) | `model.py:73,205,236-237`; not in tests | round-trip test or document `random_seed` reserved/inert |

### [LOW] (compressed)
| ID | Finding | Action |
|---|---|---|
| TST-10 | no marker registry while `--strict-markers` on (safe today; brittle to first custom marker) | add `markers=[unit,integration]` table |
| TST-11 | `JuniperRecurrenceConfigurationError` is a dead export (never raised/tested) | wire to a config-validation path or drop |
| TST-12 | `step_matrices` + the model/client `_version` lack direct tests (the app `_version` **is** asserted — `test_app_smoke.py:25`) | optional direct tests |
| TST-13 | `-q` flag inconsistent (model has it, client doesn't) | align |
| TST-14 | `bench/results/*.json`+`REPORT.md` committed (generated artifacts in git) | gitignore or add a "reproduces-committed-files" CI check |
| TST-15 | app coverage bar (90) exceeds documented 80 with no codified rationale | resolve via TST-2 `fail_under` + AGENTS note |

**INFO (positives)**: app config hygiene is sound — `--strict-markers --strict-config`, explicit discovery globs, autouse `_clean_juniper_env` fixture scrubbing `JUNIPER_*` (the `.env`-leak guard, asserted `test_settings.py:96-101`), `tmp_path` not `/tmp`. `asyncio_mode` correctly absent (all routes are sync `def` — no "never awaited" risk). Model determinism sound (every RNG seeded via `np.random.default_rng(int)`; no torch). Conformance genuinely runs (`test_conformance.py` subclasses the kit; 10 collected). Client HTTP fully isolated via `responses` on every networked test. **No app source module is fully untested** (see §6 coverage map).

---

## 6. Coverage maps (source → exercising tests)

**App (`juniper_recurrence/`)** — route-complete; only thin spot is the `EventSink` overflow branch (TST-8):

| Module | Status | Note |
|---|---|---|
| `app.py`, `main.py`, `data.py`, `schemas.py`, `settings.py`, `state.py` | Covered | smoke + CLI + adapter + settings (13 tests incl. `_FILE`, `.env`-no-leak, IP-validator) |
| `routers/{_common,crossval,dataset,model,predict,training}.py` | Covered | happy/409/422/404/auth paths; `_common` branch-exhaustive (`test_routes.py:193-211`) |
| `events.py` | Partial | `__call__`/`snapshot` via routes; `maxlen` eviction untested (TST-8) |

**Model (`juniper_recurrence_model/`)** — comprehensive (`model.py` fit/predict/ridge/target_dt/mask/serializer all covered; `data.py` all 7 ValueError paths; conformance + crossval real). Gaps: `step_matrices` direct (LOW), `time_unit`/`random_seed` non-default (TST-9).

**Client (`juniper_recurrence_client/`)** — comprehensive (URL-normalize, auth env/`_FILE`/precedence, all verbs, all error mappings, readiness poll, context-manager; HTTP mocked). Gaps: `X-Request-ID` branch (TST-7), `JuniperRecurrenceConfigurationError` dead export (TST-11).

---

## 7. Area C — CI/CD workflows + dependencies/metadata/docs

### CI / publish

### [CRIT] (bench ungated) — see TST-1 (cross-listed).

### [HIGH] CI-1 · No `required-checks` aggregation gate in any CI workflow  (B12, C7)
- **What**: no workflow has a final job that `needs:` all others to serve as the single branch-protection status check.
- **Evidence**: `ci-recurrence-app.yml` jobs end at `docker` with no aggregator; same in model/client CIs.
- **Baseline**: `juniper-ml/.github/workflows/ci.yml:397-401` `required-checks` (`needs:[…]`); `juniper-canopy/ci.yml:813`.
- **Impact**: branch protection must enumerate each matrix leg by name; renaming a job silently drops it from the gate; a new job is unprotected until manually added.
- **Action**: add a `required-checks` job per CI workflow (or one repo `ci.yml`) as the sole required check.

### [HIGH] CI-2 · Model CI runs no lint  — see PC-4 (cross-listed).

### [HIGH] CI-3 · No security / `pip-audit` job and no weekly security scan  (B12)
- **What**: no recurrence workflow runs `pip-audit`/bandit/gitleaks; no `security-scan.yml`. Three live PyPI packages with a broad dep surface have **zero dependency-vulnerability scanning**.
- **Evidence**: workflow dir has only the 7 files; no `pip-audit` string in any.
- **Baseline**: `juniper-ml/.github/workflows/security-scan.yml:1-29` (weekly `pip-audit --strict --desc on`) + inline `security` job in `ci.yml:288`.
- **Action**: add `security-scan.yml` (weekly `pip-audit` per package) and/or a `security` job per CI.

### [MED] CI-4…CI-9 (compressed)
| ID | Finding (dim) | Evidence | Baseline | Action |
|---|---|---|---|---|
| CI-4 | push CI only on `main`; `feat/**`/`fix/**`/`chore/**` get no push-CI (the juniper-data trigger-gap class; `[skip ci]` ancestor can strand checks) | `ci-recurrence-{app:25,model:24,client:25}.yml` `push: branches:[main]` | `juniper-ml/ci.yml:28-34` | add `feature/**`,`fix/**` to push filters |
| CI-5 | CI never tests the shipped wheel (editable-only; `build` stops at `twine check`) — MANIFEST/package-data risk | `ci-recurrence-app.yml:78,105` | `ci-model-core.yml:98-105` clean-venv wheel import | add wheel-install smoke to each `build` |
| CI-6 | app `docker` job has no `needs:` — runs even when lint/test fail; green `docker` can mask red tests | `ci-recurrence-app.yml:107` (no `needs:`) | `juniper-canopy/ci.yml:756` gated | add `needs:[lint,test]` |
| CI-7 | no docs-link validation (`juniper-check-doc-links`) — relevant given the stale-doc CRITs | no such step | `juniper-ml/ci.yml:273` | add a `docs` job (`--cross-repo skip`) |
| CI-8 | no `concurrency:` groups — superseded runs not cancelled | `grep concurrency .github/` → none | `juniper-ml/ci.yml:41` | add concurrency to CI (not publish) |
| CI-9 | model coverage gate (90) < ml model-core analog (95); no coverage artifact | `ci-recurrence-model.yml:62` vs `ci-model-core.yml:71` | — | consider raising to 95; emit artifact |

### [LOW] CI-10/CI-11
- CI-10 · CODEOWNERS says "two distributions" + lists only model+app; client+bench fall through to `*` (`.github/CODEOWNERS:16,26,29`). Add explicit `/juniper-recurrence-client/` + `/bench/` blocks; fix the count.
- CI-11 · client folds ruff into the matrix `test` job (runs 3×, mis-attributes lint failures) vs app's dedicated `lint` job. Standardize to a single-version `lint` job in all three.

**INFO (positives)**: publish workflows are **best-in-class** — OIDC trusted publishing (`id-token: write`, no tokens), TestPyPI-first with install verification, the no-prod-fallback TestPyPI policy (`--no-deps`, single `--index-url`, retry), decoupled per-package tag patterns (`juniper-recurrence-model-v*` won't fire the app publisher), and the GitHub-Release-required gate with a `workflow_dispatch` escape hatch — all matching `juniper-ml/publish-model-core.yml` structure. `pr-base-branch-guard.yml` is correct & portable (dynamic default-branch compare + `stacked-pr` label opt-out). Path-scoping is disjoint & correct. *(The `pypi` env dual-gate lives in GitHub environment settings — NOT VERIFIED from repo files; the workflow-side `environment: {name: pypi}` ref is present.)*

### Dependencies / metadata / docs

### [CRIT] DEP-1 · Root `AGENTS.md` describes a non-existent pre-scaffold state  (C3)
- **What**: the repo-level `AGENTS.md` (the most-read agent/onboarding file) claims a pre-implementation scaffold with only the model package; the repo ships app+model+client+bench, **three live on PyPI**.
- **Evidence**: `AGENTS.md:46` "the future app package … is **not yet scaffolded**"; `:56-58` "Pre-implementation scaffold; WS-0 not ratified"; `:26-44` layout shows **only** `juniper-recurrence-model/` (omits app, client, bench, notes, .github), and the model subtree it shows is itself stale; `:7` Version `0.1.0`; `:8` Last Updated `2026-06-17`. Contradicted by 6 published tags spanning 3 live PyPI packages (`git tag --merged HEAD`) and `juniper-recurrence/README.md:18` "This is the application layer (WS-4b)".
- **Impact**: any agent/human onboarding via `AGENTS.md`/`CLAUDE.md` is told the app doesn't exist and nothing is ratified — actively misleading. Also fails the canonical-header currency convention enforced elsewhere by `agents-md-touch-up.yml`.
- **Action**: rewrite "What this is" + layout + Status to the real 3-package + bench monorepo; bump Version→`0.1.1` + Last Updated; document the test command + env (closes TST-3 doc half). Optionally add app/model AGENTS.md (only the client has one today — INFO).

### [HIGH] DEP-2 · App README version (`0.1.0`) lags shipped `0.1.1`  (C3)
- **What**: PyPI landing page for `juniper-recurrence` 0.1.1 will display "Version: 0.1.0".
- **Evidence**: owner-verified — `juniper-recurrence/README.md:7` `**Version**: 0.1.0` vs `_version.py:9` `0.1.1`, `CHANGELOG.md:31` `[0.1.1]`.
- **Action**: bump README header to `0.1.1` (or drop the header to match the model/client READMEs' convention).

### [HIGH] DEP-3 · `bench/` deps declared only via the app's `[bench]` extra; equities dep undeclared  (C1)
- **What**: `bench/` has no `pyproject.toml`; its deps are satisfied implicitly by the app's `[bench]` + base deps. The `equities_seq` row additionally needs `juniper-data[equities]`, declared **nowhere** — so `pip install -e '.[bench]'` does not make that row runnable (silent SKIP).
- **Evidence**: `bench/__init__.py:9-13`; `bench/datasets.py:50-87` (imports `juniper_data.generators.*`), `:81-85` (documents `equities` extra need + 0.7.0 wheel omits `sp500_constituents.csv`); only bare `juniper-data>=0.7.0` in app `pyproject.toml:65`.
- **Action**: cap `juniper-data` (`<0.8.0`); add a `bench-equities` extra (`juniper-data[equities]`) or document the source-install requirement.

### [MED] DEP-4…DEP-6, DEP-8 (compressed)
| ID | Finding (dim) | Evidence | Action |
|---|---|---|---|
| DEP-4 | outside doc-tools/ci-tools/pre-commit governance entirely | `grep -rniE 'doc-tools\|ci-tools\|pip-audit\|pre-commit' .github/` → none | adopt the ecosystem templates (overlaps PC-1, CI-3, CI-7) |
| DEP-5 | model-core **runtime** floor `>=0.1.0` understates advertised crossval (CHANGELOG/README imply 0.2.0) | model `pyproject.toml:33` vs `:42` (`[crossval]` correctly `>=0.2.0`); `CHANGELOG.md:13-16` | confirm runtime works on 0.1.0 or raise floor to `>=0.2.0` |
| DEP-6 | uncapped dep floors (3): `juniper-data>=0.7.0`, `juniper-observability[prometheus]>=0.4.0`, client `juniper-observability>=0.3.1` | app `pyproject.toml:59,65`; client `:41` | add `<0.8.0` / `<0.5.0` caps |
| DEP-8 | `juniper-ml[recurrence]` extra omits the now-published client (baseline drift, juniper-ml change) | `juniper-ml/pyproject.toml:66-69` | add `juniper-recurrence-client>=0.1.0,<0.2.0` to `[recurrence]`/`[clients]` + CLAUDE.md table |

### [LOW] DEP-7, DEP-9…DEP-12
| ID | Finding | Action |
|---|---|---|
| DEP-7 | port doc nit (downgraded from MED on verification): the deploy host `8211` → container `8210` mapping **is** documented (app `README.md:81`); only the client README quickstart (`README.md:24`) uses host `:8211` without a cross-ref. The original "README only mentions 8210" premise was wrong. | add a one-line port cross-ref to the client README |
| DEP-9 | legacy `license={text="MIT"}` table form (all 3) vs newer SPDX `license="MIT"` (`juniper-data-client`) — emits setuptools deprecation | migrate to SPDX form (ecosystem-wide, low urgency) |
| DEP-10 | build-system drift: client `setuptools>=61.0` vs app/model `>=68` | align client to `>=68` |
| DEP-11 | no `Typing :: Typed` classifier (sibling `data-client` has it) — `py.typed` presence NOT VERIFIED | add classifier if `py.typed` ships |
| DEP-12 | no `MANIFEST.in` in any package | none now (code-only wheels); revisit if package-data added |

**INFO**: torch is **not** a dependency (verified numpy-only) → the `>=2.10.0` CVE-2025-3001 floor is **N/A** (correctly so). Version triple is otherwise consistent (model 0.1.2, client 0.1.0 all aligned across `_version`/pyproject/CHANGELOG). Publish governance tag-decoupled & correct. No `JR-REC-*` requirements shortcode exists → findings here are net-new and carry no JR-ID (per the ecosystem convention).

---

## 8. Target pre-commit profile (the §4 PC-1 fix, designed)

A **single root `/.pre-commit-config.yaml`**, cloning `juniper-data`'s ruff-stack layout (modern fleet pattern) + the root-config-over-sub-packages governance of `juniper-ml`/`juniper-cascor`. Per-sub-package ruff/test stays in the existing per-package CIs; the root config owns cross-cutting hooks + a repo-wide ruff safety net.

- **Header**: banner block copied from `juniper-data/.pre-commit-config.yaml:1-26` (banner is the file class where it's expected).
- **Top-level**: `minimum_pre_commit_version`, `default_language_version: {python: python3}`, **`default_install_hook_types: [pre-commit, pre-push]`** (so pre-push self-installs — closes PC-6), repo-wide `exclude:` (`.git/`,`.venv/`,`__pycache__/`,`.pytest_cache/`,`.ruff_cache/`,`.benchmarks/`,`*.egg-info/`,`bench/results/`,`data/`,`*.npz`).
- **Hooks** (revs = fleet-pinned for lockstep — PC-7):
  - `pre-commit/pre-commit-hooks v4.6.0`: check-yaml/toml/json, EOF-fixer, trailing-whitespace, check-merge-conflict, check-added-large-files, check-ast, debug-statements, **detect-private-key** (closes PC-2 + PC-5 file-checks).
  - `astral-sh/ruff-pre-commit v0.15.2`: `ruff --fix` + `ruff-format`, scoped `^(juniper-recurrence/juniper_recurrence|juniper-recurrence-model/juniper_recurrence_model|juniper-recurrence-client/juniper_recurrence_client|bench)/.*\.py$` — the **4-way scope is the one genuinely net-new bit** (no sibling has 3 import-package dirs + a bench dir); this is also what closes the `bench/` lint gap.
  - ruff alias `ruff-async-audit` (`--select ASYNC`, `stages:[pre-commit,manual]`), app-source-only (closes PC-6 async).
  - `PyCQA/bandit 1.9.4` (`--skip=B101,B311`, excl. the 3 `tests/`) (closes PC-3).
  - `igorshubovych/markdownlint-cli v0.42.0` (`--config=./.markdownlint.yaml`, excl. `CHANGELOG`/`notes/`) + add `.markdownlint.yaml` (copy ml's) (closes PC-5 md).
  - `adrienverge/yamllint v1.35.1` (covers the 7 workflows) (PC-5 yaml).
  - `shellcheck-py v0.10.0.1` (no-ops today; forward-coverage) (PC-6).
  - local `no-unencrypted-env` (`^\.env(\.secrets)?$`) (PC-2).
- **`ci:` trailer**: `autofix_prs: false`, `autoupdate_schedule: monthly` (PC-8).

**Decisions**: ruff stack (not black) — repo is already pure-ruff; ONE root config; pre-push coverage gate = **No/optional** (the 3 CIs already gate coverage; `default_install_hook_types` lets it be added later without re-install). **Do NOT** add a root `pyproject.toml` (would fight per-package `[tool.ruff]` ownership) or SOPS (no encrypted secrets yet).

**Companion files**: `.markdownlint.yaml` (copy `juniper-ml`); `lint:` job in `ci-recurrence-model.yml`; `.gitignore += .ruff_cache/`; `.gitattributes` (`* text=auto`).

---

## 9. Prioritized remediation backlog (severity × effort)

All remediation is a **separate effort in the `juniper-recurrence` repo** (its own worktree per the cross-repo worktree procedure; PR-to-main, never direct commit). DEP-8 is a juniper-ml change. Net-new → no JR-ID.

| # | Item | Sev | Effort | Findings |
|---|---|---|---|---|
| 1 | **Refresh root `AGENTS.md`** (real layout/status/version + test command + env) | CRIT | ~30 min | DEP-1, TST-3(doc) |
| 2 | **Fix app README version** 0.1.0→0.1.1 | HIGH | ~5 min | DEP-2 |
| 3 | **Add autoload guard** to app + model `addopts` (2 lines each) | HIGH | ~10 min | TST-4 |
| 4 | **Add `lint:` job** to `ci-recurrence-model.yml` | HIGH | ~15 min | PC-4/CI-2 |
| 5 | **Wire `bench/` into CI** (path-scoped lane, run from root) | CRIT | ~1 hr | TST-1 |
| 6 | **Add `.pre-commit-config.yaml` + `.markdownlint.yaml`** (+ `.gitignore`/`.gitattributes` companions) (§8 profile) | CRIT | ~2 hr | PC-1/2/3/5/6/7/8/9/10, DEP-4 |
| 7 | **Add `[tool.coverage.*]`** to all 3 pyprojects (`branch=true`, `fail_under=90`) | HIGH | ~1 hr | TST-2 |
| 8 | **Add `required-checks` gate** to each CI (or one repo `ci.yml`) | HIGH | ~1 hr | CI-1 |
| 9 | **Add `security-scan.yml` + `pip-audit`** | HIGH | ~1 hr | CI-3 |
| 10 | **Broaden CI push filters** (`feature/**`,`fix/**`) + `docker needs:` + `concurrency:` | MED | ~30 min | CI-4/6/8 |
| 11 | **Cap dep floors** + add `bench-equities` extra + model-core floor decision | MED | ~30 min | DEP-3/5/6 |
| 12 | **Wheel-install smoke** in each `build` job | MED | ~45 min | CI-5 |
| 13 | **Docs-link job** (`juniper-check-doc-links --cross-repo skip`) | MED | ~30 min | CI-7 |
| 14 | Warnings policy; bench-evaluator/EventSink/request-id tests; markers; CODEOWNERS; port note; ml `[recurrence]` extra; misc LOW | MED–LOW | as capacity | TST-5..15, CI-10/11, DEP-7..12 |

**Suggested first PR (sub-2-hour, high signal)**: items 1–4 (all doc/one-liner fixes) bundled — removes the most misleading artifacts and closes the model-lint hole immediately. Then item 6 (pre-commit) as its own PR, then 5/7/8/9.

---

## 10. Appendix — provenance

- **Auditors** (read-only, parallel, evidence-or-silence): A1 pre-commit/lint (agent `aae7516e`); A2 CI/publish (`af407a15`); A3 testing app+bench (`a8a87b01`); A4 testing model+client (`ab0d6a97`); A5 deps/metadata/docs (`a61559f6`).
- **Owner spot-verification** (this session): coverage-section absence; `--cov-fail-under` CI-only; model-CI no lint; app README 0.1.0 vs `_version` 0.1.1; autoload-guard placement (app/model missing, client present); checkout `2fd2b81`, 2 behind `origin/main` `036fde7`.
- **Confidence**: CRIT/HIGH findings corroborated by ≥2 sources (config evidence + owner re-derivation, or ≥2 independent auditors). `NOT VERIFIED` recorded inline where applicable (pypi env dual-gate; `py.typed` presence).
- **Currency caveat**: audited `2fd2b81` (clean tree). At audit time, 2 behind `origin/main` `036fde7` (both bench equities-rebench). `origin/main` advanced **during this session** to `461fc4a` (HEAD now 6 behind); the newer commits include DP-3 P1 readout work (recurrence #30/#31) — **not** bench-only — so model-package findings warrant re-confirmation against the tip. Structural findings (no pre-commit, no coverage config, model-CI lint gap, stale AGENTS.md) stand.
- **Validation**: this report was adversarially re-verified by 5 independent fact-checkers (one per section, claim-and-repo re-derivation, all baseline citations re-opened) on 2026-06-21. Result: **0 findings refuted**; corrections applied = severity-tally recount (HIGH 9→10, MED/LOW undercounts fixed), DEP-7 premise corrected + downgraded MED→LOW, §6 ValueError count 6→7, DEP-3/5/6 line-refs (+1..3 off), DEP-1 tag wording, TST-12 `_version` scoping, and this currency caveat.
