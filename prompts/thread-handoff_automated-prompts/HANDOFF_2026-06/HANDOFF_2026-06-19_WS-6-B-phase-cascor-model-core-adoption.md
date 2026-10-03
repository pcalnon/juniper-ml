# Thread Handoff — WS-6 B-phase (cascor native model-core adoption)

**Date**: 2026-06-19
**Author**: Paul Calnon
**Type**: Thread-handoff prompt (continue in a fresh thread; prior thread near full context)
**Origin**: A long, productive session — model-core 0.3.0 multi-ticker ship+deploy, WS-5/WS-6 reevaluation, doc-hygiene

---

## Continue

Resume **WS-6 — the juniper-cascor refactor — at its B-phase**: make production cascor **implement the
model-core `TrainableModel` / `GrowableModel` interfaces natively**, replacing the *test-only*
`CascorModelCoreAdapter`. This is the **dependency-clear** cutover step ratified as **DR-1 (do B now;
defer the A-phase decision)** in `notes/JUNIPER_2026-06-19_JUNIPER-ECOSYSTEM_WS5-WS6-REEVALUATION.md` (juniper-ml #475,
merged).

**Approach: design-first, multi-PR.** Do NOT dive straight into production cascor code. Mirror the
pattern used for the OUT-12/13 gate and the reevaluation:

1. **Reality audit** (sub-agents): map cascor's current `src/api/lifecycle/**` + `src/api/routes/**`
   and *every* place `CascadeCorrelationNetwork` is named/coupled in the service layer
   (`git grep -n CascadeCorrelationNetwork src/ ':(exclude)src/tests/'` on cascor `origin/main`).
2. **Scope** what "native adoption" means concretely: does `CascadeCorrelationNetwork` implement
   `GrowableModel` directly, or via a thin production wrapper? What do the adapter's known gaps mean in
   production — **D-C3** (`grow_step` is a no-op; cascor grows inside `fit()`) and **D-C4** (serialization
   conformance skipped: kit wants `np.array_equal` bit-exact, cascor is `allclose(1e-6)`)?
3. **Write a linted build plan** in `notes/` (validated by independent sub-agents; markdownlint +
   `juniper-check-doc-links` clean), then **implement across small PRs**, checkpointing each.

## What shipped this session (the arc — all verified)

- **model-core 0.3.0 (multi-entity walk-forward, `walk_forward_folds(..., groups=)`)** — juniper-ml
  **#472 MERGED**; GitHub Release `juniper-model-core-v0.3.0` cut (`--latest=false`); **LIVE on PyPI**
  (publish job success; version endpoint HTTP 200). Notes archived (`#474`). F-CRIT-1 lockstep done
  (`[tools]` pin `<0.4.0` + `test_pyproject_extras`).
- **WS-5/WS-6 reevaluation** — juniper-ml **#475 MERGED** (`notes/JUNIPER_2026-06-19_JUNIPER-ECOSYSTEM_WS5-WS6-REEVALUATION.md`);
  **DR-1…DR-5 ratified** (see below). Built from 4 sub-agents (2 reality audits + fact-check + completeness critic).
- **Doc-hygiene status reconcile** — juniper-ml **#479 OPEN** (doc-links pass): roadmap + parent-plan
  WS-5/WS-6 + OUT-12/13 cells corrected to merged reality.

## Open PRs for Paul to merge (Paul approves all merges + PyPI/deploy gates)

- **juniper-ml #479** — WS-5/WS-6 + OUT-12/13 status reconcile (docs; doc-links green).
- **this handoff PR** (the file you are reading).

## WS-6 B-phase — the plan & guardrails (from the reeval §2 + DR-1)

**B vs A (do not conflate):** the cutover has two sub-phases (parent plan Part 8 §8.4):

- **6b / B-phase (THIS task):** cascor's lifecycle/routes operate against the model-core interfaces
  instead of naming `CascadeCorrelationNetwork`. **Needs no other package — dependency-clear today.**
- **6a / A-phase (NOT this task):** cascor's `src/api/**` become re-export shims over
  `juniper_service_core`. **Blocked on OUT-11** (service-core T2 unpublished) and is a *separate*,
  concurrently-built effort. DR-1 = defer the A-decision until OUT-11 is published + soaked.

**Hard guardrails:**

- **The WS-6 gate is ARMED and ENFORCED.** Golden (`Golden / Snapshot Regression`, cascor #340) +
  conformance (`model-core Conformance`, cascor #341) are **REQUIRED status checks** (ruleset
  `juniper-cascor-rules-1`, id 15081045). A B-phase PR that shifts training trajectories / event order /
  metric semantics **is blocked, not merely flagged.** Keep both green.
- **`predict` must NEVER `argmax`** — return raw scores (RK-6); the conformance kit guards this.
- **Design against the future `ServiceLifecycleManager` subclass seam** (the OUT-11 base) so the
  deferred A-phase does not redo the B-phase manager changes. The cascor `lifecycle/manager` (~3k lines)
  is the most-coupled module (T2-audit "CASCOR-BOUND").
- **Behavior-preserving:** the golden suite pins two-spiral trajectories at tolerance — the refactor is
  accepted only if golden + conformance stay green. Honor the **kill-criterion** (parent plan §2.7): if
  conformance can't stay green without observable-behavior change, WS-6 is abandoned (cascor keeps its
  own stack) — it has NOT fired (#341 is green).

**The ratified DRs (context for the broader tail):**

- **DR-1** = B now, defer A (B→A per roadmap §5.4, vs park-after-B/S2).
- **DR-2** = WS-5 D1-A (canopy one-shot path) + ratify `ModelSpec.execution` before A1a.
- **DR-3** = Task B (canopy + crossval) deferred (service-side `/v1/crossval` exists; canopy surface open).
- **DR-4** = verify the concurrent WS-7/OUT-4 recurrence-deploy delivery (Dockerfile #21 done).
- **DR-5** = in-canopy `RecurrenceServiceAdapter` first; defer published `juniper-recurrence-client` (OUT-8).

## Key context / guardrails (DO-NOT-TOUCH map — heavy concurrent sessions)

- **WS-5 (canopy) is OWNED by a concurrent session** — D2 / 3-D dataset load is hot
  (`canopy-3d-dataset-load` worktree, canopy #372). **Do not touch WS-5.**
- **OUT-11 (service-core T2) is OWNED by a concurrent session** — actively building (#473/#476/#478…);
  it is the A-phase consumer, not your B-phase. **Do not touch service-core.**
- **Wave C** (OUT-8 recurrence-client, OUT-9 canopy) is taken. **Do not touch.**
- **DUP-GUARD:** `gh pr list` **and** scan `/home/pcalnon/Development/python/Juniper/worktrees/` for
  concurrent branches before claiming any item — the remote check misses local-only / just-pushed branches.
- **cascor API reality + adapter mappings** live in memory `project_cascor_golden_suite_plan_2026-06-17`,
  in the merged adapter `src/tests/conformance/cascor_model_core_adapter.py` (cascor #341), and in the
  wiring plan `notes/JUNIPER_2026-06-18_JUNIPER-CASCOR_MODEL-CORE-CONFORMANCE-WIRING-PLAN.md` (cascor repo).
- **Standing rules:** Paul approves merges + PyPI/deploy gates (drive to the gate, hand off). Worktrees
  in `/home/pcalnon/Development/python/Juniper/worktrees/`. Scripts under `util/` (never `/tmp/`). Run
  cascor / model-core suites on the **JuniperCascor1** conda env (GIL; model-core 0.3.0 available).

## Stale worktrees to clean up (this session's MERGED PRs; do NOT touch other sessions')

All merged-PR worktrees from this session were already removed (crossval-multiticker #472,
release-notes-030 #474, ws5-ws6-reeval #475). Still present, keep until their PRs merge:

```text
juniper-ml--docs--ws5-ws6-reconcile--…       (#479 OPEN — keep)
juniper-ml--docs--handoff-ws6-bphase--…      (this handoff PR — keep until merged)
```

## Verify starting state (new thread)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml && git fetch origin
gh pr view 475 -R pcalnon/juniper-ml          # the ratified reeval (read §2 for WS-6)
cd /home/pcalnon/Development/python/Juniper/juniper-cascor && git fetch origin
git grep -n CascadeCorrelationNetwork origin/main -- src/ ':(exclude)src/tests/'  # map service coupling
ls src/api/lifecycle/ src/api/routes/         # the B-phase surface
gh pr list -R pcalnon/juniper-cascor          # dup-guard
ls /home/pcalnon/Development/python/Juniper/worktrees/   # dup-guard: concurrent branches
# Confirm gate is armed: gh api repos/pcalnon/juniper-cascor/rulesets/15081045
```

## Git / branch state

- juniper-ml `origin/main` = `857dec2` (post #478). juniper-cascor `origin/main` has #340 + #341 (gate armed).
- model-core 0.3.0 is LIVE on PyPI. The B-phase lands on a **fresh feature branch in juniper-cascor**;
  no B-phase WIP exists yet.
- The B-phase is a **production cascor behavioral change — large, multi-PR.** Build the plan first,
  checkpoint at each PR, keep golden + conformance green throughout.
