# CasCor Concurrency Architecture — Thread Handoff

**Date**: 2026-03-18
**From Thread**: sunny-mixing-lightning (juniper-ml worktree)
**Purpose**: Hand off to a new thread to continue Phase 1b implementation

---

## Thread Handoff Prompt

Continue implementing the Juniper CasCor Concurrency Architecture Plan — starting Phase 1b: WebSocket Worker Endpoint.

## Phase 1a (Security Fixes) completed

- PR #29 created in juniper-cascor: <https://github.com/pcalnon/juniper-cascor/pull/29>
- Branch: security/phase-1a-concurrency-hardening (commit 27cce13)
- Worktree: /home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--security--phase-1a-concurrency-hardening--20260318-1738--74942162
- 5 fixes implemented:
  1. Timing-safe API key comparison (hmac.compare_digest in src/api/security.py)
  2. Hardcoded authkey removed (constants_model.py → None, config auto-generates via secrets.token_hex)
  3. RestrictedUnpickler with empirically validated allowlist (cascade_correlation.py)
  4. _validate_training_result() with type/bounds/NaN checks, integrated into_collect_training_results()
  5. Queue maxsize=1000 on all 4 Queue creations
- All 2159 unit tests pass, 0 regressions, 29 new security tests added
- PR awaiting review/merge

## Remaining work (Phases 1b → 4)

1. **Phase 1b (WebSocket worker endpoint)**: Add /ws/v1/workers to juniper-cascor
   - New files: src/api/websocket/worker_stream.py, src/api/workers/registry.py, src/api/workers/coordinator.py, src/api/workers/protocol.py
   - Modified: cascade_correlation.py (dual-path dispatch), cascade_correlation_config.py (remote worker config fields)
   - Wire protocol: JSON control messages + binary numpy tensor frames (no pickle)
   - JWT auth on WebSocket upgrade, heartbeat/health monitoring
2. **Phase 2 (worker agent)**: Rewrite juniper-cascor-worker with WebSocket client
3. **Phase 3 (unified TaskDistributor)**: Integrate local MP + remote WS paths
4. **Phase 4 (security hardening)**: mTLS, JWT lifecycle, audit logging

## Key context

- Full plan: notes/CASCOR_CONCURRENCY_PLAN.md on branch worktree-harmonic-crafting-castle in juniper-ml repo
  - Section 9.1.2 has Phase 1b file-level implementation plan
  - Section 12 has revised recommendations and wire protocol spec
- Free-threading was rejected (Python 3.14 is GIL-enabled, PyTorch unsupported)
- RC-2 broke BaseManager remote path — WebSocket is a replacement, not addition
- Approach A (WebSocket for remote) + existing MP for local is the approved architecture
- The plan's wire protocol uses JSON envelopes + raw numpy binary frames (Section 12.6)
- Result validation spec in Section 12.7
- Phase 1a security fixes are on a separate branch/PR — Phase 1b should branch from main and can be developed independently
- juniper-cascor conda env: JuniperCascor (Python 3.14)
- juniper-cascor test runner: cd src/tests && bash scripts/run_tests.bash
- Worktree procedure is mandatory — create a new worktree in juniper-cascor for Phase 1b work

## Verification commands

- git log --oneline -3 (in juniper-cascor main — verify HEAD is 7494216)
- gh pr view 29 --repo pcalnon/juniper-cascor (verify Phase 1a PR exists)
- git show worktree-harmonic-crafting-castle:notes/CASCOR_CONCURRENCY_PLAN.md | head -10 (verify plan in juniper-ml)
- conda run -n JuniperCascor python -c "import torch; print(torch.\__version__)" (verify env)

## Git status

- juniper-ml: branch worktree-sunny-mixing-lightning (3 behind origin/main, clean)
- juniper-cascor: main branch clean at 7494216
- juniper-cascor worktree: security/phase-1a-concurrency-hardening at 27cce13 (pushed, PR #29 open)

---
