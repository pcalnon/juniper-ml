# Thread Handoff — juniper-canopy A1 recurrence training integration

**Date**: 2026-06-21
**Author**: Paul Calnon
**Type**: Thread-handoff prompt (continue in a fresh thread)
**Origin**: Completion of the **3-D dataset visualization design (Phases 1–3)** for juniper-canopy —
5 PRs merged (#374 / #375 / #377 / #378 / #379). This hands off the **A1 recurrence *training*
integration**, the larger model-selection enabler.
**Design-of-record (read first)**: `notes/JUNIPER_2026-06-18_JUNIPER-CANOPY_MODEL-SELECTION-A1-ENABLER-SCOPE.md`
(D1–D5) and `notes/JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md` (A0 / A1 selection UI).

---

## Continue

Build the **A1 recurrence training integration** in **juniper-canopy** so a recurrence / LMU model can be
**trained** from canopy. Today canopy can only *monitor* cascor training and (since Phases 1–3) *display*
3-D datasets. The design is ratified; this is the build. **Propose a slice cadence first** (like the
Phase-2 3-way split that worked well), then implement one PR per slice, awaiting Paul's merge between
slices.

## The dominant finding (do not relitigate — `..._A1_ENABLER_SCOPE_2026-06-18.md`)

A1 is **NOT mainly a selection-UI problem; it is an execution-paradigm mismatch.**

- **Canopy is a live-training *monitor*.** It polls `get_status` / `get_metrics` / `get_metrics_history`
  and charts per-epoch loss + network-topology growth + a 2-D decision boundary. `BackendProtocol`
  (`src/backend/protocol.py`) is cascor-shaped (`total=False` TypedDicts).
- **The recurrence service `POST /v1/train` is a SYNCHRONOUS one-shot fit** — it blocks until done,
  status is terminal (`idle` / `trained`), and there is **no background job, no WebSocket, no per-epoch
  metrics** (LMU is a single ridge / lstsq solve).
- ⇒ Canopy's poll-and-chart machinery has **nothing to poll** for a recurrence fit. That mismatch — not
  the picker UI — is the heart of A1.

## Ratified decisions (D1–D5)

- **D1-A (recommended) — a second "one-shot fit" execution path.** Canopy must grow a submit → spinner →
  render-final-metrics flow, suppressing the cascade-only panels (per-epoch chart, topology growth)
  via model-class metadata. **REJECT D1-B (faking a streaming feed).**
- **D2 — already shipped** (3-D dataset display; Phases 1–3 done). *Training delivery* stays
  service-side (the model service fetches arrays from juniper-data; canopy does not pipe the array).
- **D3 — a generic `RecurrenceServiceAdapter`** (httpx, ~150–250 LOC, **no WebSocket**). Must send
  `X-API-Key` (recurrence is API-key-secured) and use a **generous read-timeout** (the train call
  blocks). Needs a new canopy `recurrence_api_key` setting + a juniper-deploy `_FILE` secret.
- **D5 — provider-keyed routing** via `create_backend()` (`src/backend/__init__.py:32`) on
  `ModelSpec.provider` (today demo-vs-service only, with no model dimension).

## Current state — verified 2026-06-21 (all NOT built yet)

- `create_backend()` at `src/backend/__init__.py:32` — the D5 routing point; demo-vs-service only today.
- **No `recurrence_api_key` setting** in canopy settings.
- **No `RecurrenceServiceAdapter`.**
- **No recurrence service** in `juniper-deploy/docker-compose.yml`.
- Recurrence **Dockerfile is done** (juniper-recurrence #21, slim ~77 MB, no torch, monorepo app subdir).
- Recurrence model + app are **live on PyPI** (`juniper-recurrence 0.1.x`); the app exposes
  `POST /v1/train` (confirm the exact route set — likely also `POST /v1/predict`, `GET /v1/status` —
  against the recurrence app `app/` before wiring the adapter).

## Suggested slice cadence (propose to Paul, then build one PR per slice)

- **A1-i — adapter + settings (canopy, buildable now vs a mock).** New `recurrence_api_key` setting;
  `RecurrenceServiceAdapter` (httpx, no WS, `X-API-Key`, long read-timeout); unit-tested against a
  mocked recurrence service. No UI yet.
- **A1-ii — provider routing (canopy).** `create_backend()` keyed on `ModelSpec.provider`; the
  recurrence provider → the adapter. Keep the demo / cascor paths unchanged.
- **A1-iii — the one-shot execution path (canopy; the big UI/UX slice).** Submit → spinner → final
  metrics; suppress cascade-only panels via model-class metadata (the `model_registry` `status` /
  capability fields). This is the D1-A core.
- **A1-iv — the A1 selection UI.** The dedicated full-width model surface / table + sidebar gate +
  compact summary + reason-suffix on greyed options + inline ✕ + the `nn_model` backend mirror
  (`..._MODEL_DATASET_SELECTION_DESIGN_2026-06-17.md` A1). May sub-split A1a (sidebar gate + summary +
  minimal picker) → A1b (full facet table).
- **A1-deploy — juniper-deploy recurrence service (PAUL-GATED).** Standard add:
  `build.context ../juniper-recurrence/juniper-recurrence`, host port `8211:8210`, clone the cascor
  service block in `docker-compose.yml`; wire the `recurrence_api_key` `_FILE` secret + `make
  prepare-secrets`. **Deploy approvals are Paul's** — drive to the gate, then hand off.

Most of A1 is canopy-side and buildable now against a mock; the deploy service is the **live e2e gate**
Paul manages. Order: i → ii → iii in canopy; A1-deploy can land in parallel (Paul-gated); A1-iv is the
UI capstone; live e2e verification once the deploy service is up.

## Conventions (Juniper)

- **Worktrees**: centralized in `/home/pcalnon/Development/python/Juniper/worktrees/`, named
  `<repo>--<branch>--<YYYYMMDD-HHMM>--<short-hash>`. Create off freshly-pulled `origin/main`.
- **2-gate cleanup**: only remove a worktree after Paul says THAT PR is merged AND `gh pr view` shows
  `state=MERGED` for it.
- **Tests** run under the **JuniperCanopy1** conda env. Per canopy PR: keep the **L1 control-graph lint**
  (`src/tests/unit/test_control_graph_lint.py`) green (every new interactive control must be wired), and
  regenerate the panel snapshot (`rm src/tests/regression/snapshots/dataset_plotter.txt` → run the
  regression test → commit the new baseline) if `get_layout()` changes. The **L2 behavioral manifest**
  (`src/tests/ui_contract/control_manifest.py`) is only for controls with backend behavior to prove —
  a `POST` round-trip — not for pure front-end controls.
- **Pre-commit**: black / isort / flake8 / mypy / bandit / async-route audit / doc-links — all must pass
  (line length 512). Run `pre-commit run --files <changed>` before pushing.
- **PR descriptions** SHOULD carry a `## Requirements` JR-ID section where a tracked requirement applies.
- **Squash-merge ships the first commit only** — keep each PR to one clean commit (or use rebase-merge).

## Verify the new thread's start

- `gh -R pcalnon/juniper-canopy pr list --state merged --limit 5` — expect #374 / #375 / #377 / #378 /
  #379 (the 3-D viz phases).
- `git -C /home/pcalnon/Development/python/Juniper/juniper-canopy log --oneline -3` — HEAD = the #379
  merge `e0acc98`.
- `grep -n "def create_backend" /home/pcalnon/Development/python/Juniper/juniper-canopy/src/backend/__init__.py`
  — the D5 routing point (~line 32).
- Confirm no recurrence pieces yet:
  `grep -rn "recurrence_api_key" /home/pcalnon/Development/python/Juniper/juniper-canopy/src` (none) and
  `grep -n "recurrence" /home/pcalnon/Development/python/Juniper/juniper-deploy/docker-compose.yml` (none).

## Git status at handoff

- juniper-canopy `main` carries Phases 1–3 (HEAD = `e0acc98`, the #379 merge); all five viz worktrees
  are cleaned up (worktrees + local + remote branches removed, pruned).
- This handoff doc lands on its own juniper-ml `docs/handoff-a1-recurrence-integration` branch (open PR).
- No uncommitted work in flight; no half-applied edits.
