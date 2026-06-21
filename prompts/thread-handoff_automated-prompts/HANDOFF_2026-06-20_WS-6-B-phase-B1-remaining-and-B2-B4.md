# Thread Handoff — WS-6 B-phase (cascor model-core adoption): finish PR-B1, then B2–B4

**Date**: 2026-06-20
**Author**: Paul Calnon
**Type**: Thread-handoff prompt (continue in a fresh thread; prior thread at a clean phase boundary)
**Origin**: The design thread that authored + shipped the ratified B-phase build plan (juniper-ml #485) and landed PR-B1 step 1 (the production `CascorModel` wrapper). Continuation of `HANDOFF_2026-06-19_WS-6-B-phase-cascor-model-core-adoption.md`.

---

## Continue

Finish **WS-6 B-phase PR-B1** (juniper-cascor), then proceed through **B2a → B2b → B3 → B4** per the
ratified build plan. The design is done and ratified; this is execution.

- **Design of record (READ FIRST):** `notes/JUNIPER_CASCOR_WS6_BPHASE_MODEL_CORE_ADOPTION_BUILD_PLAN_2026-06-19.md`
  on juniper-ml `main` (merged via #485). §4–§5 are the implementation spec; §3 is the behavior-preservation
  contract; §9 holds the two open decisions (OQ-B1, OQ-B2).
- **Memory:** `project_cascor_ws6_bphase_plan_2026-06-19.md` (full status + grounded facts).

The decision is settled: cascor adopts the interface via a **production `CascorModel(GrowableModel)`
wrapper** (NOT by modifying `CascadeCorrelationNetwork`), because the golden suite calls `CCN.fit()`
directly, so the wrapper keeps CCN numerics byte-identical.

## What shipped this thread (verified)

- **Build plan ratified** — juniper-ml **#485 MERGED**. Authored from 4 reality audits + fact-check +
  completeness critique (4 HIGH gaps folded in: the 4 `self.network` rebinds, the Unit-Tests / Lockfile
  required lanes, and the on_event `/ws/training` regression risk). markdownlint + doc-links clean.
- **Baseline gate verified green** from the cascor worktree: golden **4 passed**, conformance **13 passed**
  (validated the plan §8 commands).
- **PR-B1 step 1 DONE + pushed** — cascor commit **`b4bd237`** on branch
  `refactor/ws6-bphase-model-core-native`:
  - `src/api/models/cascor_model.py` — `CascorModel(GrowableModel)`: wraps a **pre-built** CCN, **never
    re-seeds/re-constructs** inside `fit` (plan §4.2), exposes the wrapped CCN as a public `.network`
    property; 13 interface members (no-op `grow_step` D-C3, raw-score `predict` RK-6, numpy boundary D2).
  - `src/tests/unit/test_cascor_model.py` — **11 unit tests green**; pre-commit (black/isort/flake8 @512/
    mypy/bandit) clean.

## Remaining work — finish PR-B1 (manager wiring + dep + lockfile)

Work in the cascor worktree (below). Run the gate from the worktree root (its `src/tests/conftest.py`
forces local `src/` ahead of the editable install). Use `JuniperCascor1`.

1. **Wire `src/api/lifecycle/manager.py`** — convert the **4** `self.network` rebinds to `self.model`
   and add a getter `network` property. The monkey-patch (`self.network.fit = monitored_fit`) and all
   `self.network.<attr>` *reads* work UNCHANGED through the getter (only rebinds need changing):
   - `:1080` `self.network = None` → `self.model = None` (set first in `__init__` so the property resolves).
   - `:1425` `self.network = CascadeCorrelationNetwork(config=config)` → build the CCN, then
     `self.model = CascorModel(network=ccn)`. Add `from api.models.cascor_model import CascorModel`.
   - `:1452` `self.network = None` → `self.model = None`.
   - `:3941` `self.network = network` → `self.model = CascorModel(network=network)` (**re-wrap** the bare
     HDF5-loaded CCN — the subtle one).
   - Add: `@property def network(self): return self.model.network if self.model is not None else None`.
   - Keep the decision-boundary on `self.network.forward(...)` (M3 — do NOT route through interface
     `predict`, which returns numpy). Do NOT rename other attrs/methods here (that is B2a).
2. **Dependency:** add `juniper-model-core>=0.2.0,<0.3.0` to cascor `pyproject.toml`
   `[project].dependencies` (OQ-B2 recommendation: match the conformance pin).
3. **Regenerate `requirements.lock` SAME PR** (H3 — Lockfile Freshness is a required check). Beware the
   uv self-pin trap: compile to a temp path then move. Recipe:
   `uv pip compile pyproject.toml --extra ml --extra api --extra observability --extra juniper-data --index-strategy unsafe-best-match --no-emit-package torch --upgrade -o /tmp/req.lock && mv /tmp/req.lock requirements.lock`.
4. **Manager-wiring unit tests:** property getter ↔ `model.network`; the 4 assignment paths (create →
   `self.model` set; delete → `None`; snapshot-load → re-wrap); `has_network()` via `self.model`.
5. **Run + verify:** golden + conformance (must stay 4/13 green) + the unit lane (incl. new tests) +
   the lockfile diff. Commit, push, open **PR-B1** (Paul merges).

## After B1 — the rest of the B-phase (per plan §5)

- **B2a:** rename attributes/methods to the `ServiceLifecycleManager` seam (`training_monitor→monitor`,
  `_training_lock→_lock`, `_stop_requested→_stop_event`, `_network_params→_params`,
  `has_network→has_model`, add `_dataset_name/_last_result/_last_error/join`). **Update every
  `src/tests/unit/` call site in the same PR** (H2 — `patch.object` sites raise `AttributeError`).
- **B2b:** converge signatures/returns (`start_training` params `x→X` …; snapshot methods `bool→dict`).
- **B3 (the crux / kill-criterion):** replace monkey-patch monitoring with the `on_event` sink. **Spike
  first** — exit test is REST API-snapshot golden **AND** a `/ws/training` per-candidate-granularity
  assertion (H4). **Resolve OQ-B1 with Paul before building B3** (full migration vs. cut at B2b).
- **B4:** point native conformance at `CascorModel`; retire the test-only adapter.

## Key context / guardrails

- **`CascorModel.fit` is NOT on the B1 production path** — the manager still calls the monkey-patched
  `self.model.network.fit`. `CascorModel.fit` is the conformance (B4) + on_event (B3) surface.
- **The getter-only property suffices** — all 4 rebinds are converted to `self.model`; a missed
  `self.network = x` would fail loudly (AttributeError) and be caught by the gate. (`:276` is a helper
  class's own attribute, not the manager's — leave it.)
- **Gate is ARMED + required:** golden #340 + conformance #341 must stay green every PR (ruleset
  `juniper-cascor-rules-1` id 15081045). Kill-criterion = conformance can't stay green without behavior
  change (not fired).
- **DUP-GUARD** before each PR: `gh pr list -R pcalnon/juniper-cascor` **and** scan
  `/home/pcalnon/Development/python/Juniper/worktrees/`. **Paul approves all merges + PyPI/deploy gates.**
- **DO-NOT-TOUCH:** WS-5 (canopy) + OUT-11 (service-core T2) are concurrent sessions. The B-phase imports
  nothing from service-core (aligns to its shape only).

## Verify starting state (new thread)

```bash
CWT=/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--refactor--ws6-bphase-model-core-native--20260619-2100--07f85475
git -C "$CWT" fetch origin && git -C "$CWT" log --oneline -2     # expect b4bd237 (CascorModel) on top of #342
cd "$CWT"
/opt/miniforge3/envs/JuniperCascor1/bin/python -m pytest src/tests/unit/test_cascor_model.py -m unit -q   # 11 pass
# baseline gate (plan §8): golden 4, conformance 13 — must stay green after wiring
gh pr list -R pcalnon/juniper-cascor                            # dup-guard
```

## Git / branch state

- **cascor:** branch `refactor/ws6-bphase-model-core-native` (worktree above), 1 commit `b4bd237` ahead
  of `origin/main` (#342), **pushed**, tree clean. No PR open yet (PR-B1 opens after the wiring lands).
- **juniper-ml:** plan merged to `main` (#485). This handoff archives on `docs/handoff-ws6-bphase-b1-2026-06-20`.
- **Open decisions for Paul:** OQ-B1 (on_event appetite — gates B3) and OQ-B2 (model-core pin — recommend
  `>=0.2.0,<0.3.0`, applied in B1).
