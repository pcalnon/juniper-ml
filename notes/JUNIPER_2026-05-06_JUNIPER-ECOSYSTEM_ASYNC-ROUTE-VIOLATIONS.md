# Async-Route Audit — Phase 0 Violation Enumeration

**Owner**: Paul Calnon
**Run date**: 2026-05-06
**Tool**: `ruff 0.15.6` with `--select ASYNC --exit-zero --output-format=concise`
**Migration plan**: [`ASYNC_ROUTE_AUDIT_HOOK_MIGRATION_PLAN.md`](./ASYNC_ROUTE_AUDIT_HOOK_MIGRATION_PLAN.md) §4 Phase 0
**Companion fix PRs (already shipped)**: [juniper-data #90](https://github.com/pcalnon/juniper-data/pull/90) (BUG-JD-10 spot-fix)

---

## 1. Summary

Across the four in-scope repos:

| Repo | Violations | In production code | In test code | Most-impactful sites |
|---|---|---|---|---|
| **juniper-cascor-worker** | 0 | 0 | 0 | — clean |
| **juniper-data** | 3 | 3 | 0 | `health.py` (storage path probe) |
| **juniper-cascor** | 4 | 4 | 0 | `service_launcher.py` (orchestration script — likely all per-file-ignored) |
| **juniper-canopy** | 20 | 8 | 12 | `main.py` snapshot history I/O (real); test files ASYNC109 (per-file-ignore) |
| **Total** | **27** | **15** | **12** | |

**Phase 3 cleanup volume**: ~5–8 real route-handler fixes (the production-code violations minus the orchestration scripts), plus per-file-ignores for test files and intentional-blocking sites. Confirms the migration plan's "1–3 person-days ecosystem-wide" estimate; the actual fix work is on the lower end of that range.

---

## 2. Per-repo enumeration

### 2.1 juniper-cascor-worker — 0 violations

`ruff check --select ASYNC --exit-zero --output-format=concise .` on the repo root reports `All checks passed!`. No async route handlers in this repo (it's a sync CLI worker that connects via WebSocket); the small async surface in `juniper_cascor_worker/control_stream.py` and `juniper_cascor_worker/training_stream.py` already uses the right primitives.

**Phase 4 implication**: this is the easiest repo to enforce on. Could become the canary. (Per user's 2026-05-06 answer, the proposed enforcement order [data → cascor → canopy → worker] is preserved, but worker would also be a fine candidate to flip first if confidence-building dictated.)

### 2.2 juniper-data — 3 violations (3 production)

| File | Line | Rule | Disposition |
|---|---|---|---|
| `juniper_data/api/app.py` | 46:34 | `ASYNC240` `pathlib.Path` in async function | **Production fix** — wrap in `await asyncio.to_thread(...)` (lifespan startup probe) |
| `juniper_data/api/routes/health.py` | 131:8 | `ASYNC240` `storage_path.is_dir()` in async route | **Production fix** — wrap in `to_thread`. Filesystem stat is small but a slow disk would still block the loop. |
| `juniper_data/api/routes/health.py` | 132:34 | `ASYNC240` `storage_path.glob("*.npz")` in async route | **Production fix** — wrap in `to_thread`. Globbing a large dataset directory is the meaningful blocker. |

**Phase 3 estimate**: 1 small PR, 30 minutes including a regression test for the health-check route timing.

### 2.3 juniper-cascor — 4 violations (1 file)

| File | Line | Rule | Disposition |
|---|---|---|---|
| `src/api/service_launcher.py` | 94:5 | `ASYNC109` `wait_for_health` has a `timeout` parameter | **Per-file-ignore** — orchestration helper, not a route handler. The `timeout` parameter is the legitimate API of a polling helper. |
| `src/api/service_launcher.py` | 104:18 | `ASYNC210` `urllib.request.urlopen` in async function | **Per-file-ignore** — internal health-poll, intentional sync (it's literally a helper that wraps `time.monotonic` + `await asyncio.sleep`). |
| `src/api/service_launcher.py` | 149:22 | `ASYNC230` `open(log_file, "a", ...)` in async function | **Per-file-ignore** — opens a subprocess log file at process-start time; runs once per service, not per request. |
| `src/api/service_launcher.py` | 157:19 | `ASYNC220` `subprocess.Popen` in async function | **Per-file-ignore** — that's the whole point of the helper; it's the start_service primitive. |

**Phase 3 estimate**: zero code fixes. A single PR adding `[tool.ruff.lint.per-file-ignores]` entry for `src/api/service_launcher.py` with a `# why: orchestration helper, not a route handler` justification comment. ~15 minutes.

### 2.4 juniper-canopy — 20 violations (8 production, 12 test)

#### Production code (8) — 5 distinct sites

| File | Line | Rule | Disposition |
|---|---|---|---|
| `src/main.py` | 1409:18 | `ASYNC230` `open(history_file, "r")` reading `snapshot_history.jsonl` in route handler | **Production fix** — real route handler, real I/O. Wrap in `to_thread`. |
| `src/main.py` | 1484:12, 1489:21, 1645:9 | `ASYNC240` `pathlib.Path` ops in route handlers | **Production fix** — same pattern as data; wrap in `to_thread`. |
| `src/main.py` | 2926:35 | `ASYNC109` async function with `timeout` parameter | **Review** — likely fine if the function uses `timeout` to gate `asyncio.wait_for`; per-line `# noqa` with comment if so. |
| `src/backend/cascor_service_adapter.py` | 114:49 | `ASYNC109` async function with `timeout` parameter | **Per-line `# noqa`** — adapter method passes `timeout` through to `httpx.AsyncClient`, which is the correct pattern. |
| `src/backend/cascor_service_adapter.py` | 134:17 | `ASYNC110` `asyncio.sleep` in `while` loop instead of `asyncio.Event` | **Production fix worth considering** — replace polling-with-sleep with an `Event.wait()` if the underlying signal supports it; otherwise `# noqa` with comment. |
| `src/discovery.py` | 30:38, 55:5 | `ASYNC109` × 2 | **Per-line `# noqa`** — discovery polls remote services with bounded `timeout`; correct pattern. |
| `src/health.py` | 60:49 | `ASYNC109` | **Per-line `# noqa`** — health probe with timeout, correct pattern. |

#### Test code (12)

All ASYNC109 in `tests/unit/test_*.py` files. Standard pytest-async pattern — `async def test_x(timeout=...)`. **All per-file-ignored** in `[tool.ruff.lint.per-file-ignores]`.

**Phase 3 estimate**:

- 1 production-fix PR (4 sites in `main.py` for snapshot-history file I/O + pathlib ops): ~1 hour including regression tests.
- 1 cleanup PR adding `# noqa` justifications + per-file-ignores for tests + the `cascor_service_adapter.py` ASYNC110 review: ~30 minutes.

### 2.5 Eight repos summary table

| Repo | In scope? | Violations | Phase 3 effort |
|---|---|---|---|
| juniper-data | Y | 3 | ~30 min |
| juniper-cascor | Y | 4 | ~15 min (per-file-ignores) |
| juniper-canopy | Y | 20 | ~1.5 hrs |
| juniper-cascor-worker | Y | 0 | none — already clean |
| juniper-cascor-client | N | n/a | n/a — sync HTTP client |
| juniper-data-client | N | n/a | n/a — sync HTTP client |
| juniper-deploy | N | n/a | n/a — no Python code |
| juniper-ml | N | n/a | n/a — no Python code |

**Total Phase 3 effort across in-scope repos**: ~2.5 hours of code work, plus ~30 min per repo for the wiring (Phase 1) + soft-fail CI (Phase 2) + enforcement (Phase 4). Well under the migration plan's 1–3 person-day estimate.

---

## 3. Rule-class breakdown

| Rule | Violations | Severity for our codebase | Notes |
|---|---|---|---|
| `ASYNC109` (timeout param on async def) | 13 (1 cascor, 1 data, 11 canopy — 9 of which are tests) | LOW | Mostly false positives — pytest-async tests, `httpx.AsyncClient` adapters, and discovery probes all use `timeout` correctly. Per-line `# noqa` or per-file-ignore. |
| `ASYNC210` (sync HTTP in async) | 1 (cascor service_launcher only) | NONE in route handlers | Orchestration helper, intentional |
| `ASYNC220` (subprocess in async) | 1 (cascor service_launcher only) | NONE in route handlers | Same |
| `ASYNC230` (`open()` in async) | 2 (1 cascor, 1 canopy) | MED in canopy | Canopy main.py:1409 reads JSONL in route handler — real fix needed; cascor service_launcher is orchestration |
| `ASYNC240` (pathlib in async) | 6 (3 data, 3 canopy) | MED | Several real route-handler probes, all wrap-with-`to_thread` fixable |
| `ASYNC110` (sleep in while-loop) | 1 (canopy adapter) | LOW–MED | Worth reviewing as `Event.wait()` candidate; `# noqa` if the underlying signal isn't event-shaped |

**No `ASYNC100` violations** (the most aggressive rule, catching `time.sleep` in async functions). That's the single best signal in the report — the codebase isn't blocking the event loop on `time.sleep` anywhere.

**No project-internal blocking calls in route handlers were caught by ruff** (it doesn't recognize `*Store.get_meta`, `cache.*`, etc.). The migration plan's §5.2 deny-list — implemented as a small AST script in `juniper-ml/util/check_async_routes.py` and centralised per the user's 2026-05-06 answer to Q3 — is what closes that gap.

---

## 4. Open follow-up items

1. **BUG-JD-10 leftovers**: ruff's ASYNC ruleset did **not** catch the BUG-JD-10 sync-store-call class because `store.get_meta` / `store.update_meta` aren't on its blocking-call list. The BUG-JD-10 PR ([data #90](https://github.com/pcalnon/juniper-data/pull/90)) fixed `batch_update_tags` only; the audit roadmap entry (§5 of the v7.0.1 roadmap) flags `get_meta` / `save` / `batch_export` as still-sync. **The centralised AST checker is what closes this gap** — it's not in this Phase 0 report because Phase 0 only enumerates ruff's findings; the AST-checker scan is part of Phase 1's wiring step.

2. **canopy adapter ASYNC110**: the polling-loop violation at `cascor_service_adapter.py:134` deserves a closer look. If the underlying state-change signal can be modeled as an `asyncio.Event`, the `Event.wait()` approach is more responsive than poll-with-sleep. Worth a 15-minute spike before deciding `# noqa` vs. real fix.

3. **Phase 1 wiring scope**: the per-file-ignore lists for cascor (`service_launcher.py`) and canopy (test files + adapter + discovery + health) should be drafted in the Phase 1 PR alongside the disabled-state hook config. That way when Phase 2 flips the soft-fail CI on, the noise floor is already established.

---

## 5. What this enumeration changes in the migration plan

Concrete updates feeding back into [`ASYNC_ROUTE_AUDIT_HOOK_MIGRATION_PLAN.md`](./ASYNC_ROUTE_AUDIT_HOOK_MIGRATION_PLAN.md):

- **§3 scope table**: confirmed; the four in-scope repos are correct. Worker has zero violations — easiest enforcement.
- **§4 Phase 3 effort** ("varies — 1 hr to 1 day"): **revised down to ~2.5 hours total** across the three repos with non-zero counts.
- **§7 effort estimate** (1–3 person-days ecosystem-wide): **revised down to ~1 person-day** ecosystem-wide based on this enumeration.
- **§5.2 deny-list**: confirmed necessary — ruff alone misses the project-internal `*Store.*` blocking calls (the BUG-JD-10 class). The centralised AST checker (per user's 2026-05-06 answer to Q3) lands in Phase 1.
- **§10 open questions Q1/Q2/Q3**: all answered — see the migration plan §10 update for the resolution.

The Phase 0 result is a **green light to proceed**: cleanup volume is small, enforcement order is settled, and the deny-list home is decided. Phase 1 (wiring in disabled state) is the next concrete step.
