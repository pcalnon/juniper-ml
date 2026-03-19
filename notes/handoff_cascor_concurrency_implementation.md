# Cascor Concurrency Architecture

Continue implementing the Juniper CasCor Concurrency Architecture Plan.

## Completed so far

- Comprehensive investigation of concurrency across juniper-cascor, juniper-cascor-worker, juniper-cascor-client, and legacy code
- Three architectural proposals developed (WebSocket, Enhanced MP, Hybrid Free-Threading)
- Full security analysis with threat model
- Plan written to notes/CASCOR_CONCURRENCY_PLAN.md (1,576 lines)
- Plan validated by three independent agents (architecture, completeness, security)
- Plan revised with 12 findings addressed (Section 12)
- Plan committed: 2be2e01 on branch worktree-harmonic-crafting-castle

## Remaining work

1. **Phase 1a (security fixes)**: Implement in juniper-cascor (restricted unpickler, result validation, authkey fix, timing-safe API key, queue size limits)
2. **Phase 1b (WebSocket worker endpoint)**: Add /ws/v1/workers to juniper-cascor
3. **Phase 2 (worker agent)**: Rewrite juniper-cascor-worker with WebSocket
4. **Phase 3 (unified TaskDistributor)**: Integrate local MP + remote WS
5. **Phase 4 (security hardening)**: mTLS, JWT lifecycle, audit logging
6. **Post-work validation**: Audit all changes against plan
7. **Cleanup**: Commit, push, create PRs, perform worktree cleanup V2

## Key context

- Working directory: /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/harmonic-crafting-castle
- Branch: worktree-harmonic-crafting-castle (diverged from origin/main by 1 commit ahead, 3 behind)
- Plan file: notes/CASCOR_CONCURRENCY_PLAN.md (read Section 12 for revised recommendations)
- Free-threading was rejected (Python 3.14 is GIL-enabled build, PyTorch unsupported)
- RC-2 already broke BaseManager remote path -- WebSocket is a replacement, not addition
- Recommended approach: Approach A (WebSocket for remote) + existing MP for local
- The plan's Phase structure was revised: 1a -> 1b -> 2 -> 3 -> 4
- Implementation spans juniper-cascor and juniper-cascor-worker repos (accessible from parent /home/pcalnon/Development/python/Juniper/)
- Thread handoff procedure: notes/THREAD_HANDOFF_PROCEDURE.md
- Worktree cleanup procedure: notes/WORKTREE_CLEANUP_PROCEDURE_V2.md

## Verification commands

- git log --oneline -5 (verify plan commit exists)
- cat notes/CASCOR_CONCURRENCY_PLAN.md | head -10 (verify plan file)
- ls /home/pcalnon/Development/python/Juniper/juniper-cascor/src/cascade_correlation/cascade_correlation.py (verify cascor access)
