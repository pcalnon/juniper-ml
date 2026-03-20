# Cascor Concurrency Architecture — Phase 3+ Implementation

Continue implementing the Juniper CasCor Concurrency Architecture Plan starting from Phase 3.

## Completed so far

- **Phase 1a** (security fixes): PR #29 merged into juniper-cascor main — restricted unpickler, result validation, runtime authkey, timing-safe API key, queue size limits
- **Phase 1b** (WebSocket worker endpoint): PR #30 merged into juniper-cascor main — WorkerRegistry, WorkerCoordinator, WorkerProtocol with BinaryFrame, worker_stream WebSocket handler, settings additions, app integration
- **Phase 2** (worker agent rewrite): PR #10 OPEN on juniper-cascor-worker (branch: feature/phase-2-websocket-worker) — CascorWorkerAgent, WSConnection, task_executor, updated config/CLI with --legacy support

## Remaining work

1. **Phase 2 completion**: Merge the open PR #10 on juniper-cascor-worker (review and merge via `gh pr merge 10 --merge`)
2. **Phase 3**: Unified TaskDistributor — integrate local MP + remote WS workers
   - New file: `juniper-cascor/src/parallelism/task_distributor.py`
   - Modify `cascade_correlation.py` to use TaskDistributor instead of direct pool usage
   - Local-first scheduling (local workers get priority, remote gets overflow)
   - Task timeout and reassignment (failed remote tasks fall back to local)
   - Mixed-tier result collection
3. **Phase 4**: Security hardening — JWT lifecycle, mTLS, cert tooling, audit logging
4. **Post-work validation**: Audit all changes against the plan
5. **Cleanup**: Commit, push, create PRs, perform worktree cleanup V2

## Key context

- Working directory: /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/imperative-meandering-steele
- Branch: worktree-imperative-meandering-steele (juniper-ml worktree)
- Plan file: notes/CASCOR_CONCURRENCY_PLAN.md (read Section 9.3 for Phase 3 details, Section 12 for revised recommendations)
- juniper-cascor main is up to date with Phase 1a+1b merged
- juniper-cascor-worker main does NOT yet have Phase 2 (PR #10 still open)
- Implementation uses structured JSON + binary tensor frames (no pickle for remote path)
- The merged code uses different class names/patterns than the plan (e.g. `WorkerProtocol.build_*` static methods, `BinaryFrame.encode/decode`, `WorkerCoordinator.submit_tasks/collect_results`)
- The coordinator uses `_send_callbacks` dict and `register_send_callback()` for async dispatch from the training thread
- All existing cascor unit tests pass (2130 passed, 15 skipped)

## Important files in merged code

- `juniper-cascor/src/api/workers/protocol.py` — BinaryFrame, WorkerProtocol, MessageType
- `juniper-cascor/src/api/workers/registry.py` — WorkerRegistry, WorkerRegistration
- `juniper-cascor/src/api/workers/coordinator.py` — WorkerCoordinator, PendingTask, TaskResult
- `juniper-cascor/src/api/websocket/worker_stream.py` — worker_stream_handler
- `juniper-cascor/src/api/settings.py` — remote_workers_enabled, etc.
- `juniper-cascor/src/cascade_correlation/cascade_correlation.py` — RestrictedUnpickler, _validate_training_result,_QUEUE_MAXSIZE
- Tests in: `src/tests/unit/api/test_worker_*.py`, `src/tests/unit/test_cascade_correlation_security.py`

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-cascor && git log --oneline -5
cd /home/pcalnon/Development/python/Juniper/juniper-cascor-worker && gh pr view 10 --json state
conda run -n JuniperCascor python -m pytest src/tests/unit/ --tb=no -q  # from juniper-cascor dir
```
