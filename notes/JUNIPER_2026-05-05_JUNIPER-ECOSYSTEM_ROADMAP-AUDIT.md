# Implementation Roadmap Audit — 2026-05-05

**Owner**: Paul Calnon (audit by Claude Code)
**Audit date**: 2026-05-05
**Roadmap audited**: [`JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md`](./JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md)
**Roadmap version / date**: v7.0.0, 2026-04-23
**Scope**: All 8 Juniper repositories (`juniper-cascor`, `juniper-canopy`, `juniper-data`, `juniper-data-client`, `juniper-cascor-client`, `juniper-cascor-worker`, `juniper-deploy`, `juniper-ml`)

---

## 1. Executive summary

The roadmap is a **substantively trustworthy** catalog of known issues, but it is **stale by ~12 days and ~654 commits**, and the major delivery work that has happened in that window (Phase 6E CAN-015g and CAN-015h, the observability audit phase, and an ecosystem-wide CVE-2026-3219 mitigation) is not reflected in it. Independent of staleness, the codebase audit surfaced **a small number of new low-to-medium-severity issues** that the prior audits missed.

**Top-line numbers** (sampled, not exhaustive):

| Dimension                               | Findings                                                                                                                       |
|-----------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|
| Section 3 ("Now Fixed") sample-verify   | 9/9 verified. Line numbers drift but content is real.                                                                          |
| Section 5 ("Active Bugs") sample-verify | 11 sampled → **9 silently fixed (82%)**, 2 still present (BUG-CC-12, BUG-JD-10).                                               |
| Post-2026-04-23 commits not in roadmap  | 654 commits across 8 repos; major themes: CAN-015g/h delivery, observability audit, CVE-2026-3219 response — **all unmapped**. |
| Cross-repo API contract drift           | 5 pairs audited, **0 active drift** (CAN-015h-5 panel-target bug already fixed in canopy #239).                                |
| New coding/architectural issues         | 6 issues found, mostly LOW; 2 with HIGH/MED severity (silent stat failures, silent CSV missing-data conversion).               |

**Headline recommendation**: a v7.0.1 hotfix update to the roadmap is justified before any further v7.x work is keyed to it, because users will key off the "still open" markers and waste effort on already-shipped items.

---

## 2. Audit method

Five independent investigation passes were run in parallel, each scoped to one dimension to prevent any single pass from becoming a 15K-line read of the roadmap:

| # | Dimension                              | Method                                                                                                      |
|---|----------------------------------------|-------------------------------------------------------------------------------------------------------------|
| 1 | Section 3 "Now Fixed" trust            | Sample 8–12 ✅ items spanning repos; verify in code                                                         |
| 2 | Section 5 "Active Bugs" still-presence | Sample 10–12 🐛/🔴 items; verify still broken                                                               |
| 3 | Post-2026-04-23 deltas                 | `git log --since` per repo; cross-reference with roadmap text                                               |
| 4 | Cross-repo API contracts               | Cascor pydantic models vs. canopy/client callers; WebSocket envelopes; route paths                          |
| 5 | New coding/architectural issues        | Targeted greps for bare excepts, silent skips, dead code, numpy-JSON, threading smells, half-finished impls |

This is a **sampling-based** audit: not every one of the ~300 catalogued items was re-validated. The methodology trades off exhaustiveness for time-boxing, which is reasonable given the prior audit's documented thoroughness — re-validating every entry would itself take longer than the source audit took.

---

## 3. Section 3 ("Now Fixed") — verification of 9 sampled items

| Item                                | Repo   | Verdict  | Evidence                                                                                 |
|-------------------------------------|--------|----------|------------------------------------------------------------------------------------------|
| Task 2 Ph1 (metadata-only)          | canopy | VERIFIED | `dataset_plotter.py:454` renders the documented empty-plot                               |
| Task 1A (validation overlays)       | canopy | VERIFIED | `metrics_panel.py:1475, 1720`; helper at `:1546`                                         |
| Task 1C (learning rate card)        | canopy | VERIFIED | `metrics_panel.py:582` calls `_update_learning_rate_handler()`                           |
| Phase C (WS set_params)             | canopy | VERIFIED | `settings.py:182` flag + `cascor_service_adapter.py:114-118` routing                     |
| Phase D (WS control buttons)        | canopy | VERIFIED | `settings.py:186` + `dashboard_manager.py:2531, 2551`                                    |
| Per-IP connection cap               | canopy | VERIFIED | `settings.py:99` + `websocket_manager.check_per_ip_limit()` at `:358`                    |
| OPT-3 (persistent output layer)     | cascor | VERIFIED | `cascade_correlation.py:1616-1621` re-creates `nn.Linear` per call (documented decision) |
| SEC-08 (request body limit)         | cascor | VERIFIED | `middleware.py:58-89` `RequestBodyLimitMiddleware`                                       |
| SEC-09 (server-generated worker ID) | cascor | VERIFIED | `worker_stream.py:176` `f"worker-{uuid.uuid4().hex[:12]}"`                               |

**Drift type**: Cosmetic only — line-number references in the roadmap are outdated due to subsequent edits, but every claimed fix is present and functionally correct.

**Verdict**: Section 3 is **substantively trustworthy**. No "claimed fixed but actually broken" entries in the sample.

---

## 4. Section 5 ("Active Bugs") — still-presence check on 11 sampled items

This is the section with the largest impact on user planning, so it warrants the most scrutiny.

### 4.1 Still present (2/11)

#### BUG-CC-12 — yaml loader still in place of torch loader

- **Location**: `juniper-cascor/src/utils/utils.py:89-91`
- **State**: `yaml.safe_load(file_path.read())` is the active path; `torch.load` is commented out at line 90.
- **Why this is a bug**: The function is supposed to be a torch-state-dict loader for cascor checkpoints; it currently parses files as YAML. This compiles only because callers happen not to exercise the path with real torch tensors.
- **Severity**: HIGH — silent corruption if any caller does pass a torch state dict; LOW in practice given the active code paths don't reach it.
- **Root cause**: A serialization-format swap was started but not completed; the safe-mode replacement is wrong.

#### BUG-JD-10 — synchronous storage I/O in async route

- **Location**: `juniper-data/juniper_data/api/routes/datasets.py:429-440`
- **State**: `batch_update_tags` calls `store.get_meta()` and `store.update_meta()` synchronously inside the `async def` route handler, blocking the FastAPI event loop for the duration of every batch.
- **Severity**: MED — single-tenant dev-mode users won't notice; multi-tenant or under load it's a tail-latency cliff.
- **Root cause**: The async-wrapping pattern (`asyncio.to_thread`) is applied elsewhere in the same file but missed on this one route.

### 4.2 Silently fixed (9/11)

| Bug ID    | File                                                              | Evidence the fix landed                                                          |
|-----------|-------------------------------------------------------------------|----------------------------------------------------------------------------------|
| BUG-CC-02 | `cascor/src/api/lifecycle/manager.py:1592`                        | Reads real `best_correlation` instead of hardcoded `0.0`                         |
| BUG-CC-11 | `cascor/src/utils/utils.py:208`                                   | Walrus operator parenthesized; `content` correct type                            |
| BUG-CC-15 | `cascor/src/api/middleware.py:91-98`                              | Stream-read with early abort + comment                                           |
| BUG-CC-18 | `cascor/src/cascade_correlation/cascade_correlation.py:1976-1989` | Raises `CandidateTrainingError` instead of installing dummies                    |
| BUG-CN-01 | `canopy/src/demo_mode.py:1656-1668`                               | `_stop.clear()` / `_pause.clear()` now under `with self._lock`                   |
| BUG-CN-09 | `canopy/src/communication/websocket_manager.py:615-640`           | `broadcast_from_thread` snapshots `active_connections` under `_connections_lock` |
| BUG-CN-11 | `canopy/src/demo_mode.py:1698-1733`                               | State mutations atomic under `_lock`                                             |
| BUG-JD-02 | `juniper-data/juniper_data/storage/local_fs.py:221-239`           | Idempotent unlink                                                                |
| BUG-JD-03 | `juniper-data/juniper_data/storage/local_fs.py:262-291`           | Temp-file-then-replace atomicity                                                 |
| BUG-JD-07 | `juniper-data/juniper_data/api/routes/datasets.py:144, 154`       | `record_dataset_generation()` on both error and success paths                    |

**Verdict**: Section 5 is **accurately catalogued but heavily stale**. 82% of the sampled bugs have been fixed since the roadmap was written, with no roadmap update reflecting that. This is the single largest source of "wasted-planning" risk in the document — a developer reading the roadmap today and picking up an "active bug" has an ~80% chance of finding it already fixed.

---

## 5. Post-2026-04-23 deltas — work shipped without roadmap tracking

### 5.1 Per-repo commit volume since 2026-04-23

| Repo                  | Commits | Themes                                                                                                                                                      |
|-----------------------|---------|-------------------------------------------------------------------------------------------------------------------------------------------------------------|
| juniper-ml            | 187     | Observability audit (27 post-4/23 items, 6× P1), `register_or_reuse` design, idempotency fixes                                                              |
| juniper-canopy        | 162     | **CAN-015h network editor (h-4..h-6 shipped)**, **CAN-015g replay V2 wired**, obs-wire-02, network-editor follow-ups                                        |
| juniper-cascor        | 109     | **CAN-015g weight history (g-1)**, **CAN-015h endpoints (h-1..h-3 + retargets)**, **CAN-015h fixes (numpy coercion, round-trip test)**, obs-wire-02 metrics |
| juniper-cascor-client | 26      | `_ensure_counter` idempotency, CVE-2026-3219, CI matrix expand                                                                                              |
| juniper-data          | 57      | `_ensure_dataset_metrics` idempotency, METRICS-MON R3.1/R4.5, CVE-2026-3219, observability cardinality bound                                                |
| juniper-data-client   | 48      | METRICS-MON R4.3 (`on_request` hook), R4.6 (X-Request-ID), CVE-2026-3219                                                                                    |
| juniper-cascor-worker | 34      | METRICS-MON R4.4 (heartbeat), R4.7 (unrecognized-frame log), CVE-2026-3219, macOS leg required                                                              |
| juniper-deploy        | 31      | obs-route-01 alertmanager tickets, Grafana dashboard refresh, SLO catalog (5+8 SLIs), burn-rate alerts                                                      |

**Total: 654 commits in 12 days.** This volume is consistent with a 5–6 person team working at full pace; the roadmap's tracking cadence has not kept up.

### 5.2 Critical blind spot — CAN-015g and CAN-015h

The roadmap (around line 5121) flags CAN-015g and CAN-015h as **"deferred to dedicated post-Phase-6E sprints"**. As of 2026-05-05 both are **shipped end-to-end** on `main`:

**CAN-015g (Replay V2 — per-epoch weight history)** — 8 PRs:

| Sub-task | PR                             | What shipped                                    |
|----------|--------------------------------|-------------------------------------------------|
| g-1      | cascor #180                    | Schema v2 + adaptive sampling                   |
| g-2      | cascor #189 (retarget of #184) | Replay session weight cache                     |
| g-3      | cascor #190 (retarget of #187) | Sample-boundary weight emission                 |
| g-4      | canopy #220                    | Replay player V2 buffer + WS bridge             |
| g-5a     | cascor #196                    | Schema-v2 migration FAQ                         |
| g-5b     | canopy #221                    | V2 indicator badges + snap-to-sample FAQ        |
| g-6      | cascor #191                    | Live capture in training loop                   |
| g-7      | canopy #222                    | Decision-boundary + network-evolution renderers |

**CAN-015h (Restore-state weight + topology editing)** — 7 PRs:

| Sub-task | PR                             | What shipped                            |
|----------|--------------------------------|-----------------------------------------|
| h-0      | cascor #198                    | `_install_hidden_unit` extraction       |
| h-1      | cascor #199                    | `PATCH /v1/network/weights`             |
| h-2      | cascor #214 (retarget of #200) | `POST /v1/network/hidden-units`         |
| h-3      | cascor #215 (retarget of #201) | `DELETE /v1/network/hidden-units/{idx}` |
| h-4      | canopy #223                    | Adapter pass-throughs                   |
| h-5      | canopy #224                    | Network Editor panel + tab              |
| h-6      | canopy #235                    | Destructive-op confirm modal            |

A separate hardening pass added 5 follow-up PRs after that:

- cascor #219, #222 — pydantic-core numpy serialization (narrow then envelope-level)
- canopy #239 — Network Editor PATCH target schema mismatch
- cascor #225 — round-trip integration test
- juniper-ml #212 — design plan annotated with delivery state

**Status delta**: roadmap says "future deferred", code says "shipped, hardened, integration-tested".

### 5.3 Other unmapped work

- **Observability audit phase** (juniper-ml #194/#195 and follow-ups): 27 new items, 6 P1. Idempotency fixes for `set_build_info`, `PrometheusMiddleware`, control-stream `Counter`, REGISTRY isolation in pytest. **Unmapped**.
- **CVE-2026-3219 mitigation**: 6 repos coordinated `pip-audit --ignore-vuln` workaround between 2026-04-24 and 2026-05-02. **Zero roadmap mentions**.
- **METRICS-MON R4.x and obs-wire-01/02 and obs-route-01**: shipping across deploy/canopy/cascor/data; live but uncatalogued.
- **Hotfixes** (P-1 through P-9 markers in commit messages): validation-loss gauge index bug (cascor #206), parallelism RC-4 race (cascor #203), replay set_range overwrite leak (cascor #195), WS Counter idempotency (cascor #216), Prometheus REGISTRY isolation (data #88, canopy V34). All flagged with `P-N` audit markers in commit messages but not back-ported into the roadmap.

---

## 6. Cross-repo API contract drift — 5 pairs audited

| Pair                                                                                        | State                                                                        |
|---------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| canopy ↔ cascor REST                                                                        | VERIFIED                                                                     |
| canopy ↔ cascor WebSocket (with `best_candidate_id` ↔ `top_candidate_id` bridge documented) | VERIFIED                                                                     |
| cascor ↔ juniper-data-client                                                                | VERIFIED (cascor consumes data-client internally; no cross-repo schema hop)  |
| cascor-client ↔ cascor                                                                      | VERIFIED (pydantic enforces field names; method signatures match endpoints)  |
| canopy ↔ canopy proxy ↔ adapter ↔ cascor                                                    | VERIFIED (h-5 panel-target bug found here, **already fixed in canopy #239**) |

**Verdict**: zero active drift at the time of audit. The most recent drift incident (canopy panel sending `target="output_weights"` against cascor's `Literal["output", "hidden_unit"]`) was caught and fixed during the CAN-015h hardening pass.

---

## 7. New coding / architectural issues not in the roadmap

### 7.1 Confirmed issues

| #   | Severity | Location                                                               | Description                                                                                                                                                             |
|-----|----------|------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| N-1 | HIGH     | `juniper-canopy/src/backend/statistics.py:88-93`                       | `stats.skew()` / `stats.kurtosis()` wrapped in bare `except Exception:` with silent fallback to `0.0` and no logging. Caller cannot distinguish failure from real zero. |
| N-2 | MED      | `juniper-data/juniper_data/generators/csv_import/generator.py:152-156` | Non-numeric feature values silently converted to `0.0` via `except (ValueError, TypeError): feature_row.append(0.0)`. No warning logged. Missing data biases analysis.  |
| N-3 | MED      | `juniper-canopy/src/backend/cassandra_client.py:168`                   | `_is_connected()` swallows all exceptions from `self._session.is_shutdown` and returns `False`. Masks legitimate connection-state inspection errors.                    |
| N-4 | LOW      | `juniper-canopy/src/settings.py:194` + `main.py:297`                   | `session_secret_key` defaults to empty string; auto-generation path lacks an entropy / minimum-length validation.                                                       |
| N-5 | LOW      | `juniper-cascor/src/cascade_correlation/backups/` (and 5+ similar)     | Orphaned `_ORIG.py` / `_fix.py` / `verify_*.py` modules left in source tree. Not imported.                                                                              |
| N-6 | LOW      | `juniper-canopy/src/backend/cascor_service_adapter.py:138-172`         | Multiple bare `except Exception` blocks without context propagation; complicates root-cause analysis on service failures.                                               |

### 7.2 Things explicitly checked and clean

The audit checked but did **not** find active issues in:

- Numpy → JSON serialization in routes other than the just-fixed cascor case.
- Threading discipline in CircuitBreaker / state machine / training-loop locks.
- API response envelope consistency (other than health checks, which are intentionally flat).
- Half-finished implementations behind `raise NotImplementedError` / `pass` placeholders in the hot paths.
- Python version compatibility (e.g. `is_relative_to` is only used where Python ≥ 3.12 is the floor).

---

## 8. Root causes

### 8.1 Roadmap drift

| Root cause                                                  | Symptom                                                                                   | Frequency                           |
|-------------------------------------------------------------|-------------------------------------------------------------------------------------------|-------------------------------------|
| **No roadmap-update step in PR template / merge protocol**  | Section 5 bugs silently fix without `✅` flip                                             | 9/11 sample = 82%                   |
| **Major delivery sprints don't trigger a roadmap revision** | CAN-015g/h shipped end-to-end without any roadmap delta                                   | All 15 sub-tasks                    |
| **Audit/hotfix work isn't pushed back into the roadmap**    | Observability phase, CVE-2026-3219, P-N hotfixes all unmapped                             | Multiple ecosystem-wide initiatives |
| **Stacked-PR retargets aren't summarized at sprint close**  | g-2/g-3 and h-2/h-3 retargets only visible to readers of the design plan, not the roadmap | 4 retargets                         |

### 8.2 Recurring code smells (that the new-issue audit surfaced)

| Root cause                                        | Pattern                                                                                         |
|---------------------------------------------------|-------------------------------------------------------------------------------------------------|
| **Bare `except Exception:` with silent fallback** | N-1, N-3, N-6 — three instances of "swallow + return safe default" with no log                  |
| **Missing-data → `0.0` without telemetry**        | N-2 — CSV generator silently zeroes; equivalent to lossy-cast bugs hidden in data               |
| **Half-finished safety swap**                     | BUG-CC-12 yaml-vs-torch — incomplete refactor lives in source for months                        |
| **No async-wrap discipline**                      | BUG-JD-10 — async route synchronously calls blocking I/O; pattern-matched neighbors are correct |
| **Backup files left in source tree**              | N-5 — five-plus `_ORIG.py` / `_fix.py` files in cascor cascade-correlation backups dir          |

---

## 9. Recommended fixes

### 9.1 For the roadmap itself

1. **Publish a v7.0.1 hotfix update** that:
    - Marks Section 3 line numbers as advisory.
    - Flips ~9 entries in Section 5 from `🐛` to `✅` based on §4.2 above.
    - Adds a new Section 28 ("v7.0.0 → v7.0.1 deltas") capturing CAN-015g/h, observability audit, CVE-2026-3219, METRICS-MON R4.x, obs-wire-01/02, obs-route-01.
2. **Adopt a roadmap-touch step in the merge protocol**: any `feat(...)` / `fix(...)` PR that closes a roadmap item must touch the roadmap in the same PR (single source of truth, easier to review than a separate sweep).
3. **Add a "Recent shipped" section** at the top of the roadmap that gets a one-line entry per merged feature PR, dated. Lets readers diff against `git log` quickly.
4. **Track ecosystem incident response** (CVEs, urgent hotfixes, cross-repo breaking changes) in a dedicated section so it doesn't go dark.

### 9.2 For the still-present bugs

> **2026-05-19 update**: Both bugs below were already fixed *before* this audit was written; the audit's "CONFIRMED" findings in §B.1 were stale. Verifications:
>
> - **BUG-CC-12** — Resolved by juniper-cascor PR #228 (commit `53070cd`). Current `src/utils/utils.py:103` reads `data = torch.load(file_path, map_location="cpu", weights_only=True)`; no `yaml.load` remains in the file.
> - **BUG-JD-10** — Resolved by juniper-data PR #90 (commit `aae0081`). Current `juniper_data/api/routes/datasets.py:435,444` wraps both `store.get_meta` and `store.update_meta` in `await asyncio.to_thread(...)`.
>
> The recommendations below are retained for historical context (they describe the intended fix shape). Both PRs implemented exactly this shape.

1. **BUG-CC-12** (`utils.py:89-91`): finish the safe-loader swap — replace `yaml.safe_load(file_path.read())` with a `torch.load(file_path, map_location="cpu", weights_only=True)` (post-2.x torch supports `weights_only` for safer state-dict loading) or with the equivalent `safetensors` call. Add a unit test that round-trips a real torch state dict through the loader.
2. **BUG-JD-10** (`datasets.py:429-440`): wrap each `store.get_meta()` and `store.update_meta()` in `await asyncio.to_thread(...)` to match the rest of the file. Add an integration test that batches 50+ tag updates and asserts no event-loop blocking (use `asyncio.get_running_loop().time()` to bound the gap between requests).

### 9.3 For the new issues

1. **N-1 (silent statistic failures)**: replace the bare except with `(ValueError, RuntimeError, FloatingPointError)` and log at WARNING with the offending value range. The `0.0` fallback is acceptable; the silence is not.
2. **N-2 (silent CSV missing-data)**: same shape — log at WARNING, surface a count of replaced cells in the response metadata so users can decide whether to clean their data or accept the imputation.
3. **N-3 (cassandra `_is_connected`)**: `try / except (driver.NoHostAvailable, driver.OperationTimedOut)`-style narrowing; log unexpected exceptions at ERROR before returning `False`.
4. **N-4 (session secret key)**: validate the auto-generated key is at least 32 bytes from `os.urandom`; fail fast at startup if the OS RNG is unavailable rather than silently defaulting.
5. **N-5 (orphaned backups)**: delete or move to `notes/legacy/` with a short README explaining why they're retained. Add a pre-commit hook to block `_ORIG.py` / `_fix.py` filenames at the source root.
6. **N-6 (adapter exception specificity)**: introduce a small `_log_and_swallow(exc, *, op, ctx)` helper that captures the operation name for each call site; replace the bare excepts so root-cause traces survive in logs.

### 9.4 For the recurring patterns

1. **Lint rule for bare excepts**: enable `flake8-bugbear`'s `B902` and add a `--select B902` opt-in to the existing `flake8` configuration. Allow per-line `# noqa: B902` only with a justification comment.
2. **Async-route audit**: add a CI gate that greps each `async def` route handler for synchronous-looking storage calls (`store.`, `requests.`, `open(...)`); flag for review.
3. **Backup-file ban at source root**: pre-commit hook that fails on any path matching `*-ORIG.py` / `*_fix.py` / `*_old.py` outside an explicit `notes/legacy/` allow-list.

---

## 10. What this audit did not cover

To set expectations honestly:

- The audit did **not** re-validate every one of the ~300 catalogued items. The verification was sampling-based.
- The audit did **not** examine deploy / Helm chart / Docker Compose / Grafana dashboard correctness in detail — only the source code and route layer.
- The audit did **not** evaluate the security posture of any newly-introduced dependencies in the 12-day window (it noted the CVE-2026-3219 mitigation but did not assess whether other CVEs slipped in alongside).
- The audit did **not** validate test coverage numbers cited in the roadmap. A separate coverage-snapshot pass would be needed.

These are reasonable scope limits but the deliverable is best read as "structured spot-check with high confidence on what was checked" rather than "full re-validation of v7.0.0".

---

## 11. Validation pass

The five investigation agents ran in parallel without cross-checking each other; this pass re-verifies their highest-impact findings via direct file reads to filter out any agent hallucinations and to recalibrate severity where appropriate.

### 11.1 STILL-PRESENT bug validation

| Finding                                 | Validation method                                                        | Verdict                                                                                                             |
|-----------------------------------------|--------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| **BUG-CC-12** (yaml-vs-torch loader)    | Read `juniper-cascor/src/utils/utils.py:88-91` directly                  | **CONFIRMED** — line 89 is `data = yaml.safe_load(file_path.read())`, line 90 is the commented-out                  |
|                                         |                                                                          | `# data = torch.load(file_path)`. The bug shape matches agent 2's description exactly.                              |
| **BUG-JD-10** (sync I/O in async route) | Read `juniper-data/juniper_data/api/routes/datasets.py:412-440` directly | **CONFIRMED** — line 413 is `async def batch_update_tags(...)`; lines 430 and 439 call `store.get_meta(dataset_id)` |
|                                         |                                                                          | and `store.update_meta(dataset_id, meta)` synchronously inside the loop. Agent 2's description matches.             |

### 11.2 New-issue validation (§7.1)

| ID                                | Validation                                                                  | Re-verdict                                                                                                                 |
|-----------------------------------|-----------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------------------------------|
| **N-1** (silent stat failures)    | Read `canopy/src/backend/statistics.py:85-94`                               | **CONFIRMED**, but **severity downgraded from HIGH to MED**. The path is a UI-display stats function, not a                |
|                                   |                                                                             | security or correctness boundary; a silent 0.0 in a histogram is misleading but not load-bearing on training behaviour.    |
| **N-2** (silent CSV missing-data) | Read `juniper-data/juniper_data/generators/csv_import/generator.py:149-156` | **CONFIRMED** at MED. Lines 153-156 unconditionally substitute `0.0` for any non-coercible value with no warning surfaced. |
|                                   |                                                                             | Agent's description is accurate.                                                                                           |
| **N-3, N-4, N-5, N-6**            | Not re-validated in this pass                                               | Agent 5's description is internally consistent. These are LOW-severity quality findings; spot-checking them                |
|                                   |                                                                             | would be more useful as the basis for a follow-up cleanup PR than as part of this audit.                                   |

### 11.3 "Silently fixed" claim spot-check

| Bug           | Validation method                                            | Verdict                                                                                                                                           |
|---------------|--------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------|
| **BUG-CC-02** | Read `cascor/src/api/lifecycle/manager.py:1591`              | **CONFIRMED** — line 1591 reads `actual_correlation = float(getattr(unit, "best_correlation", 0.0) or 0.0)`, exactly as agent 2 reported.         |
| **BUG-CN-09** | Read `canopy/src/communication/websocket_manager.py:633-637` | **CONFIRMED + STRONGER**. The code now carries an inline comment that literally says `# BUG-CN-09 (Phase 3C): the early-out used to read len(set) |
|               |                                                              | from a background thread without the lock. Snapshot the size under the lock and decide based on that to avoid racing against connect().`          |
|               |                                                              | Section 5 of the roadmap should be flippable to ✅ on this one with high confidence.                                                              |

### 11.4 CAN-015g/h shipping verification

Cross-checked agent 3's PR list against `git log` on each repo's `main`:

```bash
cascor: PR #198 (h-0), #199 (h-1), #214 (h-2), #215 (h-3), #180 (g-1), #191 (g-6) — all confirmed on main
canopy: PR #223 (h-4), #224 (h-5), #235 (h-6), #220 (g-4), #221 (g-5b), #222 (g-7) — all confirmed on main
```

Also verified the roadmap text agent 3 quoted from line 5121:

> "Two future items deferred to dedicated post-Phase-6E sprints: CAN-015g (Replay V2 with per-epoch weight history…), CAN-015h (Restore weight + topology editing endpoints…)"

The line is verbatim. Agent 3's "live shipping vs. deferred-in-roadmap" gap is real and significant — the most consequential staleness in the document.

### 11.5 API contract drift verification

Agent 4's verdict was "no active drift".
The recent CAN-015h-5 panel-target bug (canopy `target="output_weights"` vs. cascor `Literal["output", "hidden_unit"]`) was the obvious drift candidate, and it has been fixed in canopy #239 with a parametrized regression test (`TestPatchWeightsWireSchemaConformance`, 5 cases).
I'm comfortable with agent 4's verdict but note that the **absence of the regression test pattern across other Pydantic Literal fields** (`optimizer_type`, `activation_function_name`, `init_output_weights`) means the drift-prevention coverage is uneven — see recommendation §9.1 / §9.4 about extending the test pattern.

### 11.6 What changed in §7 / §9 after validation

- **N-1 severity HIGH → MED**: not load-bearing on correctness.
- **BUG-CN-09 trustworthiness boosted to "explicit code comment confirms fix"**: the §5 silent-fix recommendation now has high-confidence basis for at least this entry; the user can flip it confidently rather than re-validating.
- **Section 9.1 strengthened**: the §11.4 quoted text confirms the "v7.0.1 hotfix" recommendation isn't a judgement call — the roadmap is verifiably wrong about CAN-015g/h's status, with a verbatim quote to point at.

### 11.7 Validation summary

| Finding category                       | Validation result                                                                            |
|----------------------------------------|----------------------------------------------------------------------------------------------|
| §4 STILL PRESENT bugs (2 items)        | Both CONFIRMED                                                                               |
| §5 CAN-015g/h shipping claim           | CONFIRMED via git log + roadmap line 5121 quote                                              |
| §7 New issues, HIGH/MED tier (2 items) | Both CONFIRMED; N-1 re-graded HIGH→MED                                                       |
| §7 New issues, LOW tier (4 items)      | Not re-validated; agent description internally consistent, suitable for cleanup-PR follow-up |
| §6 cross-repo API contract verdict     | Agent 4's "no drift" verdict accepted; coverage gap noted in §9.1 / §9.4                     |

No agent finding was discarded as a hallucination.
The audit's confidence level is **HIGH** for the §4, §5 (shipping), and §7-HIGH/MED claims; **MEDIUM** for the §7-LOW claims (not re-validated but plausible); and **HIGH** for the §6 verdict (the worst-case drift was the one already caught and fixed).

---

## 12. Open questions for the user

1. **v7.0.1 hotfix scope**: should the hotfix be a minimal patch flipping the verified ✅ entries and adding a "Recently shipped" section, or a fuller revision that also folds in the observability audit / METRICS-MON / obs-wire / obs-route work?
   **Answer**: Let's go with the fuller revision that includes observability audit / metrics mon / obs-rout.

2. **Follow-up PRs**: should I open the BUG-CC-12 and BUG-JD-10 fix PRs (§9.2) as part of this audit, or leave them as queued items for a future track?
   **Answer**: Open the fix PRs for these two issues.

3. **Lint-rule changes**: the §9.4 `flake8-bugbear` opt-in and async-route audit hook would produce churn across all 8 repos — should I propose a migration plan or leave that for a separate ecosystem-CI track?
   **Answer**: Propose a migration plan for the async-route audit hook.
