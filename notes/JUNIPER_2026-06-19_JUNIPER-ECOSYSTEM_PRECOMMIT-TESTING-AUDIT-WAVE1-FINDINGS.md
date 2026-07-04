# Juniper Pre-commit & Testing Audit — Wave 1 (Static + Parity) Findings

**Status**: INTERIM — Wave 1 of 3 complete (static + parity). Dynamic (W2) and adversarial verification (W3) pending.
**Date**: 2026-06-19
**Method**: 9 parallel per-repo collector agents, read-only, evidence-cited (`file:line` / `cmd→exit`), frozen schema. See plan `JUNIPER_2026-06-19_JUNIPER-ECOSYSTEM_PRECOMMIT-TESTING-AUDIT-PLAN.md`.
**Corroboration**: systemic findings (esp. F1, F5) were independently reproduced by ≥8 collectors — strong cross-agent agreement.

Repo keys: can=canopy, cas=cascor, ccl=cascor-client, cwk=cascor-worker, dat=data, dcl=data-client, dep=deploy, ml=juniper-ml, rec=recurrence.

---

## 1. Cross-repo drift matrix (C1)

| Dimension | can | cas | ccl | cwk | dat | dcl | dep | ml | rec |
|-----------|-----|-----|-----|-----|-----|-----|-----|-----|-----|
| `pre-commit-hooks` rev | **v6.0.0** | v4.6.0 | v4.6.0 | v4.6.0 | **v6.0.0** | v4.6.0 | **v5.0.0** | v4.6.0 | **none** |
| Lint/format stack | b/i/f+ruff-async | b/i/f+ruff-async | b/i/f | b/i/f+ruff-async | **ruff** | b/i/f | **non-py** | b/i/f (sub-pkgs ruff, ungoverned) | ruff (CI-only) |
| black ver (where used) | 26.3.1 | 25.1.0 | 25.1.0 | 26.3.1 | — | 25.1.0 | — | 26.3.1 | — |
| coverage `fail_under` | 80 | 80 | 80 | 80 | 80(+85/mod) | 80 | none | none(root)/85–95(sub) | 90 |
| `--cov` in addopts (local-enforced?) | **No** | **No** | **No** | **No** | **No** | **No** | n/a | **No** | **No** |
| `--strict-markers` | Y | Y | Y | Y | Y | Y | **N** | Y/**N**(config-tools) | Y |
| `--strict-config` | Y | Y | **N** | **N** | Y | **N** | **N** | Y/**N**(config-tools,root) | Y |
| `asyncio_mode` | auto | **unset*** | **unset*** | **unset*** | **unset*** | N/A | N/A | strict(obs,svc) | N/A |
| `filterwarnings` baseline | RuntimeWarn=err | scoped | **none** | error | scoped | **none** | error | mostly **none** | **none** |
| autoload guard (`-p no:dash/pw`) | **N** | Y | Y | Y | N/A | N/A | Y | Y root/4-of-6 sub | client-only |
| async-audit hook | Y | Y | **N** | Y | Y | N/A | N/A | N/A | **none** |
| `no-unencrypted-env` | Y | Y | Y | Y | Y | Y | Y | Y | **NONE** |
| `require-requirements-lock` | Y | Y | N | Y | Y | N | N/A | **N** | none |
| `default_install_hook_types` | **No (universal — every repo)** | | | | | | | | |
| CI python matrix | 3.12–3.14 | 3.12–3.14 | 3.12–3.14 | 3.12–3.14 | 3.12–3.14 | 3.12–3.14 | **3.12 only** | varies (3.11–3.14 / 3.12–3.13) | 3.12–3.14 |
| CI OS matrix | +macos | +macos | +windows | +macos | +macos | +macos | **ubuntu-only** | **ubuntu-only** | **ubuntu-only** |
| CI install-mode | editable+wheel | editable | editable-only | editable-only | wheel/`.[all]`+guard | editable-only | testdeps | editable+wheel-smoke | editable-only |
| pre-commit in CI | Y | Y | Y | Y | Y | Y | Y | Y | **NO** |
| local checkout vs origin | −3 | −2 | −6 | 0 | 0 | −3 | −4 | 0 | 0 |

`*` `asyncio_mode` unset but all current async tests are explicitly `@pytest.mark.asyncio`-decorated → safe today, latent risk only.

---

## 2. Systemic findings (ranked)

- **F1 [HIGH, systemic 9/9] Coverage `fail_under` is inert locally everywhere.** No repo puts `--cov` in pytest `addopts`; the gate fires only in CI (or, for data, a pre-push hook that isn't auto-wired — see F5). A developer's local `pytest` enforces **no** coverage threshold. Fix class: add `--cov`/`--cov-fail-under` to a documented local command or addopts, and make pyproject `fail_under` == CI.
- **F2 [CRITICAL, rec] `juniper-recurrence` has zero pre-commit infrastructure.** No root `.pre-commit-config.yaml`, no root `pyproject.toml`, no sub-package configs, no CI pre-commit lane, no `no-unencrypted-env`/`detect-private-key`/async-audit. Lint/format (ruff) runs only in CI. Net-new repo never onboarded to the fleet standard. Target profile: clone ml's root-config-governs-subpackages pattern over the 3 sub-packages.
- **F3 [HIGH, ml] Monorepo governance gap.** Root pre-commit scopes Python to `^(scripts|tests)/.*\.py$`, so **all 6 sub-packages' Python is ungoverned** by any pre-commit hook (black/isort/flake8/mypy/bandit/ruff) — enforced only in per-package CI.
- **F4 [HIGH, ml/service-core] `juniper-service-core` has no coverage gate at all** (CI runs `pytest -v` with no `--cov`), uniquely among the core sub-packages (siblings 85–95%).
- **F5 [HIGH, systemic] No `default_install_hook_types`/`default_stages` anywhere.** Most damaging in **data**: its `pre-push` coverage gate + `require-requirements-lock` never wire after a plain `pre-commit install` (needs `--hook-type pre-push`), so they silently never run locally.
- **F6 [MED, 4 repos] `asyncio_mode` unset** on cas/ccl/cwk/dat (all ship `pytest-asyncio`). Safe today (every async test decorated) but a future undecorated `async def test_` is silently never-awaited. Fix: set `asyncio_mode="auto"|"strict"` explicitly.
- **F7 [MED, fleet] `pre-commit-hooks` version drift** across **three majors**: v4.6.0 (5 repos) / v5.0.0 (deploy) / v6.0.0 (canopy, data). Broader currency gradient: canopy newest (black 26.3.1, mypy v1.20.0, mdlint v0.48.0), most repos lag (mypy v1.13.0, mdlint v0.42.0).
- **F8 [MED, 2 repos] Stale/no-op CI `SKIP` directives** referencing non-existent hooks: cascor `SKIP: pytest-unit,coverage-gate`; deploy `SKIP: docker-compose-check`. Copy-paste cruft that masks intent.
- **F9 [MED, can] canopy lacks the `-p no:dash/-p no:playwright` autoload guard** — the repo most exposed to the Dash/Playwright FT-3.14t SIGSEGV class relies on `--ignore=src/tests/ui` + Makefile split instead.
- **F10 [MED] Stale env-map docs.** canopy (`AGENTS.md` ×7 + `conda_environment_ci.yaml` name the deprecated `JuniperCanopy`) and cascor (deprecated `JuniperCascor` + refs to a deleted `pytest.ini`) point at `*-DEPRECATED` envs; live envs are `JuniperCanopy1`/`JuniperCascor1`.
- **F11 [MED] Doc/runner drift.** Dead/stale `util/run_tests.bash` stubs (cascor stub sources a missing `conf/init.conf`; data's is a copied-from-cascor stub that won't run); canopy AGENTS.md test paths don't resolve (`tests/` vs real `src/tests/`); recurrence AGENTS.md says the app is "not yet scaffolded" (it ships).
- **F12 [MED] No warnings policy** in ccl, dcl, ml-root, ci-tools, config-tools, model-core, and all 3 rec packages (`filterwarnings`/`-W error` absent).
- **F13 [MED, systemic] Wheel never test-installed (C8).** Most repos test only the editable install; the built wheel is `twine check`'d but not imported/tested → wheel-only packaging regressions (MANIFEST/package-data, `py.typed`) uncovered. Better: ml (wheel smoke-test), canopy, data (wheel content guard).
- **F14 [LOW, ml] 6 `tests/` modules not invoked by `ci.yml`** (e.g. `test_requirements_drift_check.py`, `test_agents_md_*`) — possible silently-skipped suites (verify they aren't run by another lane).
- **F15 [LOW] `--strict-config`/`--strict-markers` gaps:** config-tools has neither; ccl/cwk/dcl/deploy missing `--strict-config`. `xfail_strict` unset fleet-wide (low impact — little xfail debt).
- **F16 [LOW] CI matrix inconsistency:** OS matrix only on the services (macOS) / ccl (windows); ml/rec/deploy are Linux-only. deploy has no python matrix (3.12 only). obs/service-core narrower (3.12–3.13).
- **F17 [LOW, ccl] async client without async-audit;** **[LOW] config-tools/ci-tools** missing autoload guard (sibling inconsistency).

---

## 3. Per-repo headline (Wave-1)

- **canopy**: strong/current stack; gaps = no autoload guard (F9), stale env-map docs (F10, C3=0), AGENTS.md test paths don't resolve (F11).
- **cascor**: mature, best test hygiene (seeds, orphan-reaper, `.env`-leak fixture); gaps = stale CI SKIP (F8), dead run_tests stub + deleted-pytest.ini refs (F11), asyncio_mode unset (F6), `pre-commit-hooks` v4.6.0.
- **cascor-client**: gaps = no warnings policy (F12), asyncio_mode unset (F6), **dead `integration` marker** → CI integration lane is a perpetual no-op, no async-audit on an async client, no `--strict-config`.
- **cascor-worker**: gaps = coverage inert (F1), no orphan-reaper despite torch+forkserver, AGENTS.md python-floor 3.11≠3.12, source file-header missing.
- **data**: ruff outlier (intentional, documented); gaps = **F5 pre-push gates dormant** + **F1 coverage inert** (both HIGH here), asyncio_mode unset, ci-tools pins partly unbounded, stale run_tests stub.
- **data-client**: gaps = no warnings policy (F12, B6=0), coverage inert, network isolation convention-only, `pre-commit-hooks` v4.6.0. (Prior bandit-SARIF CI issue confirmed **resolved**.)
- **deploy**: non-Python profile (correct); gaps = stale `SKIP` (F8), `helm-lint` `language:system` needs `helm` CI doesn't install, no `--strict-markers/-config`, no py/OS matrix, repo's own `.py` unlinted.
- **ml**: gaps = **F3 sub-package Python ungoverned** + **F4 service-core no coverage** + **F1 all gates inert** + **F14 6 tests not in CI**; config-tools weakest sub-pkg (no strict flags, no guard); ci-tools missing autoload guard.
- **recurrence**: **F2 CRITICAL** (no pre-commit infra at all) + coverage inert (90 CI-only) + materially stale AGENTS.md (F11) + no warnings policy; test hygiene itself is decent (seeds, `.env`-leak fixture, sync TestClient so async config correctly absent).

---

## 4. What Wave 2 (dynamic) would add

W2 actually runs, in throwaway worktrees + bounded (`--co` first, `timeout`, autoload guard, orphan-reap, UI suites excluded), only where envs are healthy (evidence-based: can→JuniperCanopy1, cas/cwk→JuniperCascor1, dat→JuniperData; pure-Python pkgs in a default audit env). It would confirm/measure: actual `pre-commit run --all-files` health + autofix noise (A8), real coverage numbers vs the gate, test collection/pass + flakiness/segfaults/orphans (B-dynamic), and the helm-lint CI gap. Most **remediation items above are config-level and already actionable from static evidence** — W2 mainly confirms behavior and adds the dynamic-only dimensions.
