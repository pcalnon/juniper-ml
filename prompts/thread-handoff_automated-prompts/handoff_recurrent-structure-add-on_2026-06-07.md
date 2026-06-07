# Handoff — Recurrent Structure Add-On (juniper-recurse / recurrent Cascade-Correlation, OQ-4)

**Date**: 2026-06-07
**Topic**: Adding recurrent capability to Cascade-Correlation — OQ-4 model-pick redesign
**Use as the initial prompt for a fresh thread.**

---

Continue the **recurrent-structure add-on** design effort for juniper-recurse — i.e. how to add recurrent capability to Cascade-Correlation, the work that reopened **[OQ-4]** (RCC's star-free / no-count-no-group representational ceiling).

## Completed so far

- **Design docs split + merged (#344):** `notes/JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md` (model) and `notes/JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md` (refactor + cross-cutting). Original path is a redirect stub.
- **OQ-4 exploration doc created + merged (#377):** `notes/JUNIPER_RECURSE_OQ4_RECURRENT_CASCOR_PROPOSALS_2026-06-04.md`. Contains: 3 proposals (P1 self-recurrent RCC / P2 group-implementing units / P3 grown reservoir-memory blocks); a 15-agent adversarial validation (verdicts + corrections, no fabricated citations); Q1 (batching vs temporal); Q(a) decision; Q(b) resolution; §8 RTRL future work.

## Remaining work

- **FIRST: ask Paul his second open question** — he flagged "two open questions"; only Q1 (+ its a/b sub-parts) was answered. Do not skip this.
- **Resolve OQ-4 / ratify the model pick** (Paul's decision). Hinge: is the no-count/no-group ceiling acceptable for time-series *regression*? If yes → P1 (self-recurrent RCC) or P3 (reservoir/LMU, fading-memory). If breaking it is required → P2 research track (no training recipe yet).
- **Fold the chosen pick + OQ-4 conclusions into the model doc** (§1.5/§1.6). **COORDINATE — concurrent session is editing it (see Key context).**
- **Promote "Workstream 0 — temporal substrate" to an explicit WS** in the refactor doc Status Tracker (shared prerequisite for all 3 proposals).
- **Decide window-ownership boundary** (juniper-data owns windowing vs model-side; OQ-8-adjacent) — proposals doc §7.2.

## Key context (decisions + constraints — do not re-litigate)

- **cascor has NO temporal substrate today** (stateless 2-D `(batch,features)`, single-shot autograd / no BPTT, 4-key frozen-unit dict with no state slot, scalar worker tuples). This is the gating prerequisite.
- **Window = variable, T ∈ 1..~30, variable output stride.** ⇒ **BPTT-over-window is the default candidate gradient** (small T → memory trivial); dense-state/sparse-supervision via a **readout mask**; output-layer training stays a **static solve** (freezing localizes live recurrence to candidate training); **T=1 ⇒ today's cascor** (subsumption → safe `T=1`-identity migration). **RTRL deferred** (proposals doc §8).
- **Ceiling reality (validated):** P1 *inherits* it; P2 *breaks* it but has **no constructive training recipe**; P3 does **not** escape it (ESP fading memory ≠ counting — this corrected a category error). Knorozova-Ronca's real remedy = negative-weight **second-order/multiplicative** neurons (C2), **not** rotation matrices (a corrected hallucination).
- **CONCURRENCY HAZARD:** a parallel session is actively editing the model + refactor docs in the shared `main` checkout (uncommitted) and a `feature/juniper-cascor-core` worktree exists. **Run `git status` and `gh pr list` before editing those two docs; do not clobber.**
- juniper-data `equities` #164 landed a regression target + temporal split (X still 2-D) = partial WS-1 progress.

## Git status

- On `main` (shared checkout). Local `main` `22c32bd` is **behind** `origin/main` (concurrent merges); local pull is **blocked by another session's uncommitted edits** to the model + refactor docs — leave them alone.
- All of this thread's work is **merged** (#344, #377); no outstanding branch/worktree of mine.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
gh pr view 344 --json state -q .state   # MERGED
gh pr view 377 --json state -q .state   # MERGED
git fetch origin && git log --oneline origin/main -6   # what concurrent sessions merged
git status --short                       # see concurrent edits before touching model/refactor docs
sed -n '1,40p' notes/JUNIPER_RECURSE_OQ4_RECURRENT_CASCOR_PROPOSALS_2026-06-04.md
```
