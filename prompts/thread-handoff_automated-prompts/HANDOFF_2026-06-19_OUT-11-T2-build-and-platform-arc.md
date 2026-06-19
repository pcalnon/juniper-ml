# Thread Handoff — OUT-11 service-core T2 build (+ platform/environment session arc)

**Date**: 2026-06-19
**Author**: Paul Calnon
**Type**: Thread-handoff prompt (continue in a fresh thread; this thread is near full context)
**Origin**: A long, very productive "platform/environment roadmap" session (OUT-12/13/4/5 + fixes + OUT-11 design/audit)

---

## Continue

Resume the **`juniper-service-core` T2-surface build (OUT-11)** — specifically **build step 1**, then the
remaining phases — per the **ratified design + gate-audit** in juniper-ml **PR #468**
(`notes/JUNIPER_SERVICE_CORE_T2_SURFACE_DESIGN_AND_AUDIT_2026-06-19.md`). Paul approved proceeding to the build
(Option 3, full T2) after the design (4) and gate-audit; the audit gate is **GO**.

> **Path note:** Paul asked for the handoff under `notes/thread-handoff_automated-prompts/`, but the established
> directory is **`prompts/thread-handoff_automated-prompts/`** (where this file lives, beside prior handoffs).

## What shipped this session (the arc — all verified)

- **OUT-12 golden suite** + **OUT-13 model-core conformance** → the **WS-6 trigger-gate is BUILT and ENFORCED**.
  Both are **required status checks** in cascor ruleset `juniper-cascor-rules-1` (merged: cascor #340, #341).
- **Roadmap reconciliation** (juniper-ml #452, merged) — the platform roadmap is current.
- **OUT-4 recurrence Dockerfile** (juniper-recurrence #21, merged) + **OUT-5 deploy compose** (juniper-deploy
  #124, merged) → the recurrence model is **deployable end-to-end** (PyPI → image → compose, host 8211→ctr 8210).
- **Deploy wait-test fix** (juniper-deploy #125, **open, CI green**) → repairs the PR-#123 pre-existing failure
  (juniper-data internal-only); deploy `main` goes fully green on merge.
- **OUT-11 design + gate-audit** (juniper-ml #468, **open**).

## Open PRs for Paul to merge (Paul approves all merges + PyPI/deploy gates)

- **juniper-deploy #125** — wait_for_services test fix (CI green; greens deploy main).
- **juniper-ml #468** — OUT-11 T2 design + gate-audit (docs).

## OUT-11 build — the plan (from the ratified #468)

**Headline:** OUT-11 is an **EXTRACTION from cascor, not greenfield.** cascor ships the full T2 in
`src/api/{websocket,workers,lifecycle,routes}/` + `src/parallelism/task_distributor.py`; `juniper-service-core`
(juniper-ml subdir, T1 only) has **0** T2 files. Approach = **"extract base, keep cascor subclass"**, driven by a
**stub regression model** (`juniper_model_core.conformance.ReferenceGrowableModel`) for both-stacks-green contract
tests. The decoupling seam is the **model-core interfaces** (`TrainableModel`/`GrowableModel`/`TrainingEvent`/`Topology`).

**Audit verdict — GO, ~70% extractable** (see #468 §5.6 for the per-module ledger):

- **Routes/lifecycle:** CLEAN = most routes (admin/dataset/health/history/metrics/workers/snapshots + most of
  training) + `state_machine`; ADAPTER = `network`/`training`/`monitor`; CASCOR-BOUND = `manager` (3k-line) +
  `decision_boundary` → build a generic `ServiceLifecycleManager` base, cascor subclasses it.
- **WebSocket:** CLEAN = `manager`/`training_stream`/`control_security`/`messages` (7-of-9 frames); ADAPTER =
  `control_stream` (→ injectable `CommandExecutor`); OUT-OF-SCOPE = `worker_stream` + `cascade_add`/`candidate_progress`.
- **OQ-11 (worker) RESOLVED by evidence:** model-agnostic at the **pool-infra** layer
  (`registry`/`coordinator`/`audit`/`metrics`/`security` = extract now); **cascade-bound** at the
  protocol/reduction layer (task payload `correlation`/`candidate_data` + `CandidateUnit` reconstruction =
  **defer the generic Task envelope to WS-8**).

**Build phasing (each a PR, both-stacks-green; cascor unchanged via its subclass, stub model proves the base):**

1. **Generic routes + lifecycle base** (`ServiceLifecycleManager`) onto the model-core interfaces + a stub-model
   contract test (the lowest-coupling, WS-6-relevant first slice). ← **start here.**
2. **WebSocket subsystem** (drop `cascade_add`/`candidate_progress` + `worker_stream`).
3. **Worker-pool infra** (registry/coordinator/audit/metrics/security); defer the generic Task envelope to WS-8.
4. **Cross-cutting:** `[tools]` extras pin (`juniper-service-core`) + drift-lint + publish-rail
   (`juniper-service-core-v*` → PyPI) + `tests/test_pyproject_extras.py` lockstep.

## Key context / guardrails

- **Front-run accepted:** no *immediate* consumer (recurrence wrote its own synchronous routes; ws→WS-5/canopy is
  hot; worker→WS-8). cascor (WS-6 A-phase) is the real consumer; the now-enforced OUT-12/13 gate protects adoption.
- **DUP-GUARD LESSON (cost me a near-collision this session):** the remote branch/PR check **misses local-only or
  just-pushed concurrent branches** — also scan **`/home/pcalnon/Development/python/Juniper/worktrees/`** for other
  sessions' branches. Wave C is already taken: **OUT-8 recurrence-client = recurrence PR #24** (active);
  **OUT-9 canopy** is hot (canopy #372, `canopy-3d-dataset-load` worktree). **Do not touch Wave C.**
- **Standing rules:** Paul approves merges + PyPI/deploy gates (drive to the gate, hand off). `gh pr list` (and a
  worktrees scan) before assuming a red PR or unclaimed item is yours. Use worktrees in
  `/home/pcalnon/Development/python/Juniper/worktrees/`. Scripts go under `util/` (never `/tmp/`).

## Stale worktrees from THIS session to clean up (merged PRs; do NOT touch other sessions')

```bash
juniper-cascor--test--model-core-conformance--…        (cascor #341 MERGED)
juniper-deploy--feat--recurrence-compose--…            (deploy #124 MERGED)
juniper-ml--docs--out-13-conformance-plan--…           (ml #453 MERGED)
juniper-ml--docs--roadmap-reconcile-2026-06-18--…      (ml #452 MERGED)
juniper-recurrence--feat--app-dockerfile--…            (recurrence #21 MERGED)
# keep until their PRs merge: juniper-deploy--fix--wait-internal-data-test (#125),
#   juniper-ml--docs--out-11-service-core-t2-plan (#468), and this handoff worktree.
```

## Verify starting state (new thread)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git fetch origin
gh pr view 468 -R pcalnon/juniper-ml          # the ratified OUT-11 design + audit
ls juniper-service-core/juniper_service_core/ # T1 only (app/health/launcher/lifecycle/middleware/security/settings/secrets); T2 to add
ls /home/pcalnon/Development/python/Juniper/worktrees/   # dup-guard: scan for concurrent branches
# Build lands on a FRESH feature branch in juniper-ml's juniper-service-core/ subdir. No build WIP exists yet.
# Run cascor/model-core suites on the JuniperCascor1 conda env (GIL; model-core 0.2.0 installed).
```

## Git / branch state

- juniper-ml `origin/main` = `db792da` (post #465). Build target = `juniper-service-core/` subdir, new branch.
- Open: ml #468 (OUT-11 plan), deploy #125 (wait-test fix). No OUT-11 build code exists yet.
- The OUT-11 build is **large and multi-PR** — phase it (step 1 first), checkpoint at each PR.
