# Thread Handoff — Juniper Per-File Coverage Rollout (C-4 + C-5)

**Date:** 2026-07-01
**Author:** Paul Calnon (Claude Code, custom-agent suite)
**Continue:** execute the remaining per-file-coverage rollout — **C-4 (service-core)** then **C-5 (deferred/heavy-env units)** — per the scoping doc, one PR per unit, owner-gated merges/publishes.

---

## The task

Roll out a **blocking per-file coverage gate** across the Juniper ecosystem's 19 coverage units: every source file **≥90% statement**, every packaged sub-module **≥95% statement-weighted pooled**. This is **Phase C** of the test-suite audit.

**READ FIRST (both on juniper-ml main):**
- `notes/JUNIPER_ECOSYSTEM_PER_FILE_COVERAGE_ROLLOUT_SCOPING_2026-06-30.md` — the sequenced backlog (C-0..C-5), measured gap data, ratified decisions, excluded-files policy. **This is the operating doc.**
- `notes/JUNIPER_ECOSYSTEM_TEST_SUITE_AUDIT_PLAN_2026-06-26.md` — the parent audit plan (§6 contract, §7 measurement design).

---

## Completed (ALL merged to main — 8 units enforcing)

- **C-0** — the enforcing tool. `juniper-coverage-gap-map --enforce` shipped in **`juniper-ci-tools` 0.6.0** (LIVE on PyPI). PR ml#595. Interface: `--enforce` (opt-in; advisory `exit 0` stays the default) + `--fail-under-file 90` + `--fail-under-submodule 95` + repeatable `--omit <glob>`. Exits **1** if (after `--omit`) any source file's **statement** coverage <90 OR any sub-module's **`pooled_percent`** <95; exits 0 clean.
- **C-1** (free wins) — model-core + config-tools (ml#597), cascor-protocol (cascor#364).
- **C-2** (per-file nudges) — observability (ml#600), ci-tools (ml#601), data-client (data-client#107). The 4 sub-90 files all → 100%.
- **C-3** (real lifts) — doc-tools (ml#603, pooled 87→99), cascor-client (cascor-client#85, sub-module pooled 90→≥95).
- **Broken-main fix** ml#598 (an over-long AGENTS.md line — see gotchas).

Every **cheaply-measurable / pure-Python** unit is now gated. What remains needs conda envs / torch / a blocker fixed.

---

## Remaining

### C-4 — service-core (`juniper-ml/juniper-service-core`) — THE heavy one
Measured 2026-06-30: overall ~84% statement (81.14 branch-inclusive; it runs `branch=true`), **5/5 sub-modules pooled <95**, ~15 statement-basis files <90, concentrated in `websocket/` (pooled 76.45) + `workers/` (83.66); also `security.py`, `launcher.py`, `lifecycle/`.
- **DO FIRST:** add `prometheus_client` to service-core's `[test]` extra — `workers/metrics.py` reads **15%** only because 2 tests skip (a test-dep gap, not real under-coverage); re-measure after adding it (the `workers/` pooled jumps).
- **Re-measure on the statement basis first** (branch-vs-statement nuance below).
- Write real tests for `websocket/` + `workers/` (+ the tail) → every file ≥90 statement + all 5 sub-modules pooled ≥95.
- Wire the blocking gate into `.github/workflows/ci-service-core.yml` (add `--cov-report=json:coverage.json` + a step: `pip install "juniper-ci-tools>=0.6.0,<0.7.0" && juniper-coverage-gap-map --coverage-json coverage.json --enforce`).
- **Likely 2 PRs** (`websocket/` and `workers/`+tail) — it's the largest single unit; smaller PRs review better.

### C-5 — deferred / heavy-env units (each needs its env or a blocker cleared)
- **canopy** — `JuniperCanopy1` conda env; today's gate is a partial subset (unit+regression), measure whole `src`.
- **cascor** — `JuniperCascor1` + torch; bash harness (`src/tests/scripts/run_tests.bash`); partial-subset.
- **cascor-worker** — torch.
- **data** — heavy deps; already has an ADVISORY per-module check (`scripts/check_module_coverage.py`) → generalize to the C-0 gate.
- **recurrence app + client** — **DISC-1 MUST BE FIXED FIRST**: `juniper-recurrence/juniper-recurrence/pyproject.toml:~132` filters a `starlette.exceptions.StarletteDeprecationWarning` class absent from the installed Starlette → `pytest --co` errors at config-parse. Pin/guard it before measuring. (Recurrence-client shares the pattern.)
- **recurrence-model** — torch; reuse its `.coveragerc.torch` two-lane (base-omit + torch-include) pattern.
- **cascor-model** — the **no-gate outlier** (`ci-cascor-model.yml` = `pytest -v` only); C-5 adds its FIRST coverage gate.
- **juniper-ml meta** (no importable package → N/A or scope to `util/`) and **juniper-deploy** (no source) are **exempt/special-cased**.

---

## Key context / decisions / gotchas (learned the hard way — carry these)

- **Gate metric (RATIFIED by owner):** sub-module bar = **statement-weighted `pooled_percent`** (NOT mean-of-files); per-file = **statement** % (NOT branch-inclusive). The tool computes both; `--enforce` gates on pooled + statement.
- **branch-vs-statement:** for `branch=true` repos (data-client, doc-tools, service-core), the scoping table's per-file "<90" counts are **branch-inclusive**; the gate is **statement**, so real failures are FEWER (e.g. data-client's `client.py` "89.56" was branch; it was already 93.10 statement). **Always re-measure on the statement basis first.**
- **`__main__.py` / thin entry shims:** prefer an in-process `runpy.run_module(..., run_name="__main__")` smoke test (doc-tools ml#603 → 100%); else `--omit "*/__main__.py"` per scoping §2 (ci-tools ml#601 did this).
- **ci-tools version pins:** a `juniper-ci-tools` minor bump MUST widen juniper-ml's own three workflow pins (`.github/workflows/ci.yml`, `docs-full-check.yml`, `lockfile-update.yml`) in the SAME PR, or the ungated `tests/test_ci_tools_drift.py` + `tests/test_env_drift_check_drift.py` fail. Current pins are `<0.7.0`; consumers pin `juniper-ci-tools>=0.6.0,<0.7.0`.
- **AGENTS.md ≤512 chars/line** (markdownlint MD013): an over-long AGENTS.md line broke main once (ml#598). Keep every AGENTS.md line ≤512. (`prompts/`, `notes/`, `docs/`, CHANGELOG are markdownlint-excluded; AGENTS.md is NOT.)
- **Verify-before-green:** wait for **Pre-commit** (not just the fast checks) to fully resolve before calling a PR green, and confirm the exact main HEAD's `ci.yml` run. (Calling ml#595 green early caused the ml#598 detour.)
- **Process:** one PR per unit; isolated worktrees under `/home/pcalnon/Development/python/Juniper/worktrees/`; `gh pr list` dup-guard; **no merge without a PR**; **Paul (owner) merges every PR and approves every PyPI publish** (the `pypi` environment gate — never self-approve). The **`task-executor`** agent pattern worked well: isolated worktree → real tests (no weakening) → wire gate → verify `--enforce` exit 0 → open PR → report. Run per-unit task-executors in the background; verify each PR's CI independently before reporting it green.
- **Open follow-ups (tracked, not blocking):** juniper-ml#588 (`util/env_floor_drift_check.py` ↔ ci-tools consolidation); observability leaky test `test_fixture_is_no_op_when_prometheus_client_missing` (never restores `builtins.__import__` — hermetic-fix candidate).

---

## Verification commands (per unit, isolated venv — statement basis)

```bash
python3 -m venv /tmp/cov-<unit>
/tmp/cov-<unit>/bin/pip install -e "<dir>[test]" "juniper-ci-tools==0.6.0"
cd <dir> && /tmp/cov-<unit>/bin/python -m pytest --cov=<import_pkg> \
    --cov-report=term-missing --cov-report=json:/tmp/<u>.json -q -p no:cacheprovider
/tmp/cov-<unit>/bin/juniper-coverage-gap-map --coverage-json /tmp/<u>.json --enforce   # exit 0 == passes the gate
```
(Heavy units: run in the correct conda env — `conda run -n JuniperCanopy1 …` / `JuniperCascor1` + torch. numpy-2.x needs package-form `--cov`, which the tool already uses.)

---

## Git status

- All C-0..C-3 work is **MERGED to main**; **no rollout PRs open** in any of the 4 repos (juniper-ml, juniper-cascor, juniper-cascor-client, juniper-data-client). juniper-ml main HEAD ≈ `ac93d6e`; `juniper-ci-tools` `0.6.0`.
- This session ran from a `.claude/worktrees/` session worktree with no uncommitted work pending. **A fresh thread should start clean on `main`** (`git fetch && git checkout main && git pull --ff-only`).
- **Stale-working-tree trap:** the on-disk `juniper-ml` main checkout may be parked at an **ancestor** of `origin/main` (e.g. `ef48b92`, behind `ac93d6e`). Probing the working tree **before** pulling shows a stale `juniper-ci-tools 0.5.1` and a *missing* scoping doc. Run the fetch/checkout/pull above **first**, then verify every anchor against the refreshed `main` — never against the un-pulled tree.

---

## First action for the new thread

Read the scoping doc §5 (C-4 row), then execute **C-4 (service-core)**: (1) add `prometheus_client` to its `[test]` extra + re-measure on the statement basis; (2) write real tests for `websocket/` + `workers/` (+ `security.py`/`launcher.py`/`lifecycle/`) to reach per-file ≥90 statement and all sub-modules pooled ≥95; (3) wire the blocking `--enforce` gate into `ci-service-core.yml`; (4) verify `--enforce` exit 0; open PR(s) (likely 2), never merge. Then proceed to **C-5**, fixing **DISC-1** before the recurrence units and adding cascor-model's first gate. Use `task-executor` agents in isolated worktrees; keep every AGENTS.md line ≤512; wait for Pre-commit before calling any PR green; Paul merges and approves all publishes.
