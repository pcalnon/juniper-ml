# Thread Handoff: Track 4 Phases D and E Implementation

**Handoff Date**: 2026-04-26
**Handoff Author**: Claude Code (Opus 4.7, 1M context)
**Worktree**: `rippling-leaping-tarjan`
**Branch (juniper-ml)**: `worktree-rippling-leaping-tarjan` (open PR #141)
**Effort Level**: high

---

## Goal

Continue working on Track 4 of `notes/JUNIPER_OUTSTANDING_DEVELOPMENT_ITEMS_V7_IMPLEMENTATION_ROADMAP.md`, **Phases 4D and 4E**.

Track 4 covers cross-repo alignment and client-library cleanup across `juniper-data-client`, `juniper-cascor-client`, and `juniper-cascor-worker`. Phases 4A, 4B, and 4C are done (4C is in review on the listed PRs). Phases 4D and 4E remain.

The roadmap is the source of truth — read the relevant per-item sections (line numbers below) before changing any code. Each item has a documented Approach, Recommended choice, Implementation snippet, and Severity/Priority/Scope. Follow the recommended approach unless something has materially changed in the codebase.

---

## Context: What the Prior Thread Completed

### Phase 4A ✅ — generator name constants (already on main)

- juniper-ml #133, juniper-data-client #33, juniper-data #43.

### Phase 4B ✅ — 503 retry, missing params, idempotent-only retry (merged 2026-04-24/25)

- juniper-data-client #34 (XREPO-09 `tags`/`ttl_seconds`; XREPO-11 idempotent-only `RETRY_ALLOWED_METHODS`).
- juniper-cascor-client #23 (XREPO-02/CC-02 added 429+503 to `RETRYABLE_STATUS_CODES`).
- juniper-ml #137 (roadmap markers).

**Carry-forward gap** (not blocking, document if you address): roadmap recommended an opt-in `retry_non_idempotent: bool = False` on the data-client; not implemented.

### Phase 4C 🟡 — JSONDecodeError handling (PRs open, not yet merged at handoff time)

- juniper-data-client #35 — ERR-01: `_parse_json` staticmethod wraps all 14 `response.json()` sites; new `tests/test_malformed_json_response.py`.
- juniper-cascor-client #24 — ERR-02: `_parse_json_body` helper used in `_request()`; new `TestMalformedJsonResponse` class in `tests/test_client.py`.
- juniper-cascor-worker #33 — CW-01/CW-06: `WorkerConnection.receive_json()` wraps `json.loads()` and raises `WorkerConnectionError`; same fix covers task and registration paths because both call `receive_json()`.
- juniper-ml #141 — roadmap markers for Phase 4C (this worktree's branch).

**Verify before starting Phase 4D**: `gh pr view <n>` for each of the four PRs above and confirm they merged cleanly. If any failed CI or required review changes, address those first.

---

## Phase 4D Scope (3 items, ~3×M)

| Item     | Repo                  | Roadmap line | Summary |
|----------|-----------------------|--------------|---------|
| XREPO-04 | juniper-cascor-worker | §7223        | Add `tests/test_protocol_alignment.py` that imports both server `MessageType` and worker `MSG_TYPE_*` constants and asserts equality. CI must run it. |
| XREPO-05 | juniper-cascor-client | §7305        | Add canonical `TRAINING_STATE_STOPPED/STARTED/PAUSED/FAILED/COMPLETED` UPPERCASE constants to `juniper_cascor_client/constants.py`. Update `juniper_cascor_client/testing/constants.py` lines ~39-43 from lowercase (`"idle"`, `"training"`, `"paused"`, `"complete"`) to UPPERCASE matching server FSM. |
| XREPO-07/08 | juniper-cascor-client | §7400, §7454 | `juniper_cascor_client/ws_client.py` `send_command()` (line ~99) and `command()` direct path (line ~232) currently send `{"command": ...}` without a `"type"` field. Add `"type": "command"` to both so all WS messages share one envelope (line ~280 `set_params()` already has it). Cross-ref CC-06. |

**Verification commands**:

```bash
# cascor-worker
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-worker
conda run -n JuniperCascor python -m pytest tests/ -q

# cascor-client
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-client
conda run -n JuniperCascor python -m pytest tests/ -q
```

**Watch for**: XREPO-05 is a breaking-style change for downstream callers comparing against lowercase strings. The roadmap recommends UPPERCASE but a case-insensitive compatibility shim during migration may be warranted — read §7310-7339 carefully.

---

## Phase 4E Scope (8 items, ~8×S-M)

| Item   | Repo                  | Roadmap line | Summary |
|--------|-----------------------|--------------|---------|
| CC-04  | juniper-cascor-client | §9899        | Document `set_params()` in `AGENTS.md` Architecture section. |
| CC-05  | juniper-cascor-client | §9928        | Add `"3.14"` to `.github/workflows/ci.yml` Python matrix (current matrix: 3.11/3.12/3.13). |
| CC-06  | juniper-cascor-client | §9951        | Cross-ref to XREPO-07 (handled in Phase 4D). Update status only. |
| CC-07  | juniper-data-client   | §9973        | NpzFile resource leak. `juniper_data_client/client.py:409` calls `np.load(io.BytesIO(content))` without closing the returned NpzFile. Use a context manager: `with np.load(io.BytesIO(content)) as npz: ...` and copy arrays out before exit, or call `.close()` explicitly. |
| CW-02  | juniper-cascor-worker | §10527       | `requirements.lock` includes ~25 CUDA packages (~2-4GB). Split into `requirements-cpu.lock` (PyTorch CPU wheels via `--extra-index-url`) and `requirements-gpu.lock`. Default Dockerfile uses CPU. |
| CW-03  | juniper-cascor-worker | §10534       | `pyproject.toml` defines `integration` marker but tests/ has zero integration tests. Add 3-5 tests covering registration, task receipt, binary frame decoding, result submission, graceful disconnect. Use `requires_server` marker (skip when server unavailable). |
| CW-04  | juniper-cascor-worker | §10563       | `juniper_cascor_worker/worker.py:225` timeout path hardcodes `"candidate_uuid": ""`; capture from `candidate_data.get("candidate_uuid", "")` (already in scope at line 211). |
| CW-05  | juniper-cascor-worker | §10612       | `task_executor.py:46` does `from candidate_unit.candidate_unit import CandidateUnit` via sys.path. Approach A: create `juniper-cascor-core` package and depend on it. Approach B: vendor the file. Roadmap recommends A long-term, B as interim. **Decide and document the choice.** |
| CW-07  | juniper-cascor-worker | §10671       | `worker.py:202-205` receives binary frames per `tensor_manifest` key but never validates that received tensor keys match. Add post-loop check: `missing = set(manifest.keys()) - set(tensors.keys())`; on mismatch send error response and return early. |
| CW-08  | juniper-cascor-worker | §10736       | `task_executor.py:12` has top-level `import torch` (2-5s startup penalty). Move inside `execute_training_task()` or use a lazy-import helper. |

**Verification commands**:

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-client && conda run -n JuniperCascor python -m pytest tests/ -q
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-worker && conda run -n JuniperCascor python -m pytest tests/ -q
cd /home/pcalnon/Development/python/Juniper/juniper-data-client && conda run -n JuniperData python -m pytest tests/ -q
```

---

## Working Procedure

1. **Verify Phase 4C PRs merged**. If not, do not start 4D — fix or land them first.

2. **One worktree per repo per phase**, per parent CLAUDE.md (`/home/pcalnon/Development/python/Juniper/CLAUDE.md`):
   - Centralized location: `/home/pcalnon/Development/python/Juniper/worktrees/`
   - Naming: `<repo>--<branch>--<YYYYMMDD-HHMM>--<short-hash>`
   - Suggested branch names: `fix/phase-4d-protocol-alignment`, `fix/phase-4e-worker-improvements`, `fix/phase-4e-client-cleanup`. Avoid bundling 4D and 4E in one PR — too large.

3. **For each item**: read the roadmap remediation section (line refs above), implement the recommended approach, add tests that fail before and pass after, run the full repo test suite, commit, push, open PR.

4. **Update roadmap markers** (this juniper-ml worktree, branch `worktree-rippling-leaping-tarjan`) once each phase's per-repo PRs are merged. PR #141 already updates Phase 4C; rebase before adding Phase 4D/4E markers.

5. **Conda envs**: `JuniperData` for data-client, `JuniperCascor` for cascor-client and cascor-worker.

6. **Pre-commit hooks** run on every commit (`flake8`, `bandit`, `shellcheck`, `markdownlint`, `yamllint`, SOPS check). Don't bypass with `--no-verify`.

---

## Git State at Handoff

- juniper-ml worktree `rippling-leaping-tarjan` is on `worktree-rippling-leaping-tarjan` branch, clean working tree, pushed to origin.
- Phase 4C feature branches exist on origin in their respective repos: `fix/phase-4c-jsondecode-handling` (3 PRs).
- Open PRs at handoff: juniper-data-client #35, juniper-cascor-client #24, juniper-cascor-worker #33, juniper-ml #141.

---

## Tasks

The current Claude Code task list at handoff:

- #1, #2, #3 — Phases 4A/4B/4C (completed).
- #4 — Phase 4D (pending).
- #5 — Phase 4E (pending).
- #6 — Roadmap status updates / commit / PR / cleanup (completed for 4C).

Recreate equivalent tasks in the new thread before starting work.
