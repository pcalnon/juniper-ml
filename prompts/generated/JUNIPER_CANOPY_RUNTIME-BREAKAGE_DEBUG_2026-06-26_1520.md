# Diagnose & Fix Regression — juniper-canopy basic functionality is dead at runtime after the multi-repo refactor (green tests, broken app)

<!--
Generated prompt — Juniper custom-agent suite. Category: regressions (execution-class).
Grounded against juniper-canopy @ main c25b7a1 (discovery bundle 2026-06-26, first-party re-probed).
See the companion analysis: notes/JUNIPER_CANOPY_DEBUG-PROMPT_ANALYSIS_2026-06-26.md
Convention: this is a session-starting prompt; paste it as the opening message of a fresh session.
-->

## Role

You are an experienced principal software engineer running a debugging session on **juniper-canopy** (the real-time monitoring dashboard, Dash + FastAPI).
Canopy's unit/CI test suite is green, yet the running application is broken badly enough that basic functionality does not work.
Your job is to find **every** serious runtime issue, determine the **root cause** of each, fix the root causes (not the symptoms), prove the app works again, and document the result. Diagnose before you change; verify before you claim.

## Resources

**Target repo / state (re-confirm before trusting):**

- Repo: `/home/pcalnon/Development/python/Juniper/juniper-canopy/`, branch `main`, HEAD `c25b7a1`, version `0.5.0`.
- Live conda env: **`JuniperCanopy1`** (Python 3.13). Do **not** use `JuniperCanopy-DEPRECATED`. (Env-name convention: canopy `AGENTS.md`; commit `a06abb1` "durable conda env-name convention — live JuniperCanopy1".)
- Entry point: `app = FastAPI(...)` at `src/main.py:339`; run as `uvicorn main:app` from `src/`. Demo launcher: `./demo` → symlink to `util/juniper_canopy-demo.bash` (exports `JUNIPER_CANOPY_DEMO_MODE=1`, `JUNIPER_DATA_URL=http://localhost:8100`). Demo mode is the default run mode.
- Service ports (parent `AGENTS.md`): juniper-data `8100`, juniper-cascor `8201` (host), juniper-canopy `8050`. Env vars in play: `JUNIPER_DATA_URL`, `JUNIPER_DATA_API_KEY`, `CASCOR_SERVICE_URL`, `CASCOR_LOG_LEVEL`.

**Confirmed root cause (leading hypothesis — verify it, do not assume it is the whole story).**
The `JuniperCanopy1` env holds client wheels **below the code's `pyproject.toml` floors**. The recent refactor bumped canopy to call client APIs the installed wheels do not have, but the env was never reinstalled from `requirements.lock`. First-party evidence (re-run to confirm):

| Package                 | Installed in JuniperCanopy1 | `pyproject.toml` floor           | `requirements.lock` pin            | Code calls API                           | Present in installed?   |
|-------------------------|-----------------------------|----------------------------------|------------------------------------|------------------------------------------|-------------------------|
| `juniper-data-client`   | **0.4.0**                   | `>=0.4.1` (`pyproject.toml:138`) | `==0.4.1` (`requirements.lock:69`) | `JuniperDataClient(on_request=…)`        | **No → TypeError**      |
| `juniper-cascor-client` | **0.3.0**                   | `>=0.5.0` (`pyproject.toml:149`) | `==0.5.0` (`requirements.lock:63`) | `CascorControlStream(origin=…)`          | **No → TypeError**      |
| `juniper-cascor-client` | 0.3.0                       | `>=0.5.0`                        | `==0.5.0`                          | `JuniperCascorClient.save_snapshot(...)` | **No → AttributeError** |
| `juniper-observability` | 0.4.0                       | `>=0.4.0`                        | —                                  | (build-info, metrics-auth)               | ✓ ok                    |

Re-confirm the gap in one command:

```bash
conda run -n JuniperCanopy1 python -c "import inspect; from juniper_data_client import JuniperDataClient as C; print('on_request' in inspect.signature(C.__init__).parameters)"
# expected on the stale env: False   (the smoking gun)
```

**Confirmed runtime crash sites (grep-verified at HEAD `c25b7a1`):**

- `src/demo_mode.py:918-921` and `src/demo_mode.py:1795-1798` — `JuniperDataClient(... on_request=build_data_client_request_hook())`. Constructed **above** the `try:` (≈`src/demo_mode.py:935`), so the `TypeError` is **uncaught**; the deprecated local-fallback path (`_generate_spiral_dataset_local`, ≈`src/demo_mode.py:1001`) is never reached. Spiral-dataset fetch is core demo-mode behavior → first data fetch kills the page.
- `src/backend/cascor_service_adapter.py:44` imports `CascorControlStream`; `:131-134` constructs `CascorControlStream(origin=self._ws_origin)` (see the intent comment at `:88`). Breaks the training-control WebSocket supervisor → start/stop/pause/resume against a real cascor backend.
- `src/backend/cascor_service_adapter.py:1537` `def save_snapshot(...)` calls `self._client.save_snapshot(description=…)` at `:1545` → `AttributeError` on snapshot-save against cascor-client 0.3.0.
- `create_backend` is at `src/backend/__init__.py:33` (provider routing).

**Why the green suite hides all of this:** `src/tests/conftest.py` registers an autouse session fixture `mock_juniper_data_client` that **mocks the data client entirely** (documented in canopy `AGENTS.md`); the cascor client is likewise mocked.
The real 0.4.0/0.3.0 constructor signatures are therefore never exercised, and imports succeed because the old wheels still export the top-level symbols.
CI is green because it installs from `requirements.lock` (correct versions) and/or runs against mocks. The breakage lives only at the real-client **call seam**, which no test touches.

**Do NOT chase the "188 failing tests" figure** from any stale `.pytest_cache`. The `lastfailed` cache in this checkout is dated **2026-05-13** (six weeks stale, pre-refactor). A bounded, cache-safe `pytest --co -q` in `JuniperCanopy1` **collects cleanly (exit 0, zero import errors)** at HEAD — the breakage is at runtime call sites, not at import/collection. Establish the *current* test state yourself; do not trust the cache.

**Secondary / suspected items (lower confidence — verify, do not presume):**

- After upgrading cascor-client to 0.5.0, re-verify the **full adapter surface** against a live cascor backend (not mocks): `cascor_service_adapter.py` makes heavy use of the private `self._client._request(...)` (≈lines 911/920/929/962/981/1029/1045/1081/1108) plus `get_metrics_history`, `get_decision_boundary`, `get_topology`, `update_params`, etc. Symbol existence ≠ matching signature/behavior.
- Recurrence model is selectable + `status="live"` (`src/model_registry.py`) and Train-gating allows Start, but `recurrence_service_url` / `recurrence_api_key` default `None` (`src/settings.py`) and the demo path sets neither → selecting "Recurrence (LMU)" and starting will fail to reach a service. Confirm intended UX.
- `src/demo_mode.py` (~line 1808) notes `validate_npz_contract` "is absent from the pinned/published juniper-data-client (0.4.x)" — evidence of ongoing canopy↔data-client API churn; check it is resolved on 0.4.1.
- Requirements-doc drift: `conf/requirements.txt`, `requirements.txt`, `requirements_ci.txt` carry **commented** client pins at the OLD versions (e.g. `# juniper-cascor-client==0.3.0`); `requirements.lock` is correct. Misleading to anyone reinstalling.

**Regenerate the grounding bundle** (do not rely on a prior session's scratch copy):

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml   # the suite's home
python util/prompt_discovery/cli.py --repo-root /home/pcalnon/Development/python/Juniper/juniper-canopy \
  --subject "canopy runtime breakage post-refactor client floor drift" \
  --symbols "JuniperDataClient,CascorControlStream,save_snapshot,create_backend"
```

## Primary Objective

Restore basic, working juniper-canopy functionality by finding **all** of the serious runtime issues, determining and fixing each one's **root cause** (not its symptom), and guarding against silent recurrence — demonstrated by the app actually running and the suite passing, with a concise root-cause writeup.

## Assigned Tasks / Directives

1. **Establish ground truth.** Work in an isolated canopy git worktree (canopy `notes/WORKTREE_SETUP_PROCEDURE.md`); run `gh pr list` first as a duplicate-work guard. In `JuniperCanopy1`: run the current test suite via canopy's documented command (its `Makefile` / `AGENTS.md`; respect the CI path-scope — `-m "unit or integration"` skips by-path snapshot/regression tests), and **launch the app** (`./demo`, then load `http://localhost:8050`) to observe the live failures. Capture the actual tracebacks.
2. **Identify every serious issue (do not stop at the three known crashes).** Triage what prevents basic functionality: dataset load/generation, the training-control WebSocket, snapshot save/delete, model selection (cascor and recurrence), the dashboard rendering and status updates. Treat the findings in *Resources* as a verified **starting map**, not an exhaustive list. Consider fanning out to the `auditor` agent for systematic, evidence-backed issue enumeration.
3. **Determine the root cause of each and isolate the code locations.** For the three known crashes, confirm the env-vs-floor drift empirically (the one-line signature check above) and identify the commits that adopted the new client APIs — note that canopy's **code is correct against its floors**; the **environment** is what drifted, so do not git-bisect canopy source chasing a "bad commit."
   For anything else you find, localize it to `file:line` and explain the mechanism.
   Re-confirm each cited `file:line`/symbol in-repo before relying on it; if a path/symbol/flag does not resolve, **stop and report** rather than inventing one.
4. **Fix the root causes; generate the code/config changes.** At minimum: correct the env to satisfy the floors (recommended: `conda run -n JuniperCanopy1 python -m pip install -r requirements.lock`, which pins `juniper-data-client==0.4.1` and `juniper-cascor-client==0.5.0`; confirm the signature check now returns `True`).
   Then, with a healthy env, re-run the app and fix any **genuine code defects** that remain (e.g. adapter signature mismatches against cascor-client 0.5.0, recurrence routing when the service URL is unset).
   Decide — and justify — whether to also harden `demo_mode.py` so a client construction/transport error degrades gracefully instead of hard-crashing (the current "no local fallback" is explicit; treat changing it as an owner-relevant design choice, not a default).
   Make the smallest correct change set; match canopy's idiom (line-length 512, canonical file headers).
5. **Guard against silent recurrence.** Add a regression guard that **fails before and passes after**: e.g. a canopy test asserting the active env's installed `juniper-*` versions satisfy the `pyproject.toml` floors (the class of defect that juniper-ml's `editable_install_drift_check.py` misses, because it only covers *editable* installs, not plain wheels). Do not disable, skip, or weaken any existing test to make the suite pass.
6. **Document any other Juniper issues you discover** (design gaps, config problems, syntax errors, architectural weaknesses, incomplete development) — including whether sibling envs (`JuniperCascor1`, `JuniperData`) show the same plain-wheel-vs-lockfile drift. **Note these; do not fix them here** (keep this session's blast radius to canopy + its guard).
7. **Land the fix and document results.** Open a PR against canopy `main` (never merge — the owner merges); include a `## Requirements` section with any applicable `JR-CANOPY-*` IDs. Write a short root-cause writeup (what broke, when, why, the fix, the guard) into canopy `notes/`.

## Key Deliverables & Requirements

- Basic functionality restored, **demonstrated**: the app launches in `JuniperCanopy1` and the spiral dataset loads in the browser without the `on_request` crash; the smoking-gun signature check returns `True`; (against a live cascor) training control and snapshot-save no longer raise.
- All serious runtime issues enumerated, each with a `file:line` location and a confirmed root cause.
- The root-cause fixes applied as the smallest correct change set, landed as a **PR** (not a merge), with the real test suite + the new guard passing and **no test weakened**.
- A new regression guard that fails on the stale env and passes on the corrected env.
- A root-cause writeup in canopy `notes/`, plus a documented list of any other Juniper issues found (incl. sibling-env drift).

## Constraints

- Do NOT disable, skip, or weaken any test to make the suite pass (CRITICAL and ABSOLUTE).
- Do not invent the introducing commit, paths, APIs, versions, or flags — every reference must resolve in the grounding bundle or the live repo; STOP and report if unverifiable.
- Keep scope to **juniper-canopy** plus its regression guard. Sibling-repo drift and any juniper-ml tooling gap (e.g. a plain-wheel drift checker) are to be **documented, not fixed** in this session.
- One PR per work-unit; never merge (the owner merges and approves any deploy/PyPI gates); worktree cleanup only after the PR merges.

## Finalize / Validation

- Paste passing evidence: the app launching and serving `:8050`, the one-line signature check now `True`, the full suite green via canopy's documented command, and the new guard test failing-before / passing-after.
- For this high-blast-radius claim ("basic functionality restored"), cross-validate before declaring done: verify against actually-running juniper-data (`:8100`) and, where claimed, juniper-cascor (`:8201`) services — not against mocks — or via an independent sub-agent smoke pass.
- Verify per the standing rules: `gh pr list` dup-guard before starting, one PR per work-unit, no merge without a PR.
