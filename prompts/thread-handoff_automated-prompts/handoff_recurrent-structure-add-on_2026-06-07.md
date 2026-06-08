# Handoff — Recurrent Structure Add-On (juniper-recurse / OQ-4) + refactor/migration state

**Date**: 2026-06-07 (refreshed 2026-06-08)
**Topic**: Adding recurrent capability to Cascade-Correlation (OQ-4 model pick) + the model/middleware refactor & migration plan the new model plugs into.
**Use as the initial prompt for a fresh thread.**

---

Continue the **recurrent-structure add-on** effort for juniper-recurse (how to add recurrent capability to Cascade-Correlation — the work that reopened **[OQ-4]**), together with the **model/middleware refactor + migration plan** the new model plugs into. **Three live threads remain: (1) OQ-4 model pick, (2) juniper-cascor-core deploy (CW-05 / cascor#319), (3) the deferred Round-2 adversarial re-verification of the model pick.**

## Completed so far

**Design + planning (all MERGED to juniper-ml `main`):**

- **Docs split (#344):** `notes/JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md` (model) + `notes/JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md` (refactor + cross-cutting Status Tracker / Risk Register / OQ table / Verification Log). Original path is a redirect stub.
- **OQ-4 exploration doc (#377):** `notes/JUNIPER_RECURSE_OQ4_RECURRENT_CASCOR_PROPOSALS_2026-06-04.md` — 3 proposals (P1 self-recurrent RCC / P2 group-implementing units / P3 grown reservoir-memory blocks), 15-agent adversarial validation, Q1 + Q(a)/Q(b).
- **Irregular-Δt handling note (#378):** `notes/JUNIPER_RECURSE_DELTA_T_HANDLING_2026-06-05.md` — the `dt`/`t`/`observed_mask`/`target_dt` 3-D NPZ contract (§6), windowing-leakage property test (§7), and the solver-free variable-Δt LMU ZOH path (§8, model §1.3.4 amendment).
- **Round-2 live-code re-verification + Part 8 migration/cutover path (#349):** refactor doc Part 7 "Round 2" (7 read-only anti-hallucination agents re-grounded every refactor claim vs live repos; doc structurally sound; drift `G1`–`G7` integrated append-only) + new **Part 8** (on-host vs docker dependency-resolution asymmetry, per-workstream two-column runbook, both-stacks-green ladder).
- **OQ-16/17/18 folded into the Part 5 canonical OQ table (#385).**
- **Part 5 OQ statuses reconciled to Paul's answers (#387)** + **§1.6 `Answer-N` blocks recorded (#388)** — Part 5 (status SoT) and §1.6 (discussion) now agree.

**Paul's model-OQ answers (2026-06-06; now committed in Part 5 #387 + §1.6 #388):**

- **OQ-1** recurrent ✓ · **OQ-2** R5 & C1 BOTH bind / complementary (C1 transparency *enables* R5 capability — *not* "C1 overrides") · **OQ-3** framework / RCC-first as a path to the FULL scope (RCC-only = sequencing, not reduced scope) · **OQ-5** datasets = spiral / XOR / MNIST / equities + multi-sine / Mackey-Glass / AR(p) ("not limited to") · **OQ-7 irregular-Δt = GATING for a completed state, NOT deferrable.**
- **WS-1 data work tracked in `juniper-data#168`** (3-D NPZ + `task_type` + shared `temporal_split` + the gating irregular-Δt contract; equities #164 already demonstrated regression target + temporal split, X still 2-D).

## Remaining work — three live threads

### 1. OQ-4 — resolve / ratify the model pick (the sole open model OQ; gates WS-0 ratification)

- Two (possibly non-exclusive) approaches under analysis; **a dedicated doc/section is forthcoming (Paul).** Hinge: is the no-count / no-group star-free ceiling acceptable for time-series *regression*? If yes → P1 (self-recurrent RCC) or P3 (reservoir/LMU fading-memory); if breaking it is required → P2 research track (no constructive training recipe yet).
- **Carry-over from the prior handoff:** Paul flagged "two open questions" on the #377 proposals; as of 2026-06-07 only Q1 (+ a/b) was answered — **confirm whether his second was resolved before proceeding.**
- On resolution: fold the chosen pick into model doc §1.5/§1.6, update the Part 5 `OQ-4` row (currently `OPEN — under active analysis`), and promote Status-Tracker `WS-0` toward ratification.
- Also pending: promote "WS-0 temporal substrate" to an explicit WS in the refactor Status Tracker; decide the window-ownership boundary (juniper-data vs model-side; OQ-8-adjacent; proposals §7.2).

### 2. juniper-cascor-core deploy (CW-05 / cascor#319 dual-path) — PARALLEL THREAD

- **Own detailed handoff:** `prompts/thread-handoff_automated-prompts/handoff_cascor-core-publish-and-dualpath-verify_2026-06-07.md` (on branch `docs/handoff-cascor-core-publish-2026-06-07`, **not on main**). Plan: `notes/JUNIPER_CASCOR_CORE_PYPI_MIGRATION_PLAN_2026-06-03.md` (Wave 0 + Wave 1 ratified; Wave 2 deferred behind a drift-guard).
- **Done:** `juniper-cascor-core` Wave 0 (ml#345) + worker Wave 1 (worker#98 — pyproject dep + `candidate_unit`/`ACTIVATION_MAP` import wiring) + cascor#324 (dispatch `int()` fix + worker-payload-normalization drift backport) — all MERGED.
- **Remaining (critical path, in order):**
  1. **Publish `juniper-cascor-core` 0.1.0.** `publish-cascor-core.yml` is ready (tag `juniper-cascor-core-v*` → TestPyPI→PyPI) but has **never fired** (PyPI 404). **BLOCKED ON PAUL:** configure PyPI + TestPyPI trusted-publishing pending-publisher (admin-only), cut tag/release `juniper-cascor-core-v0.1.0`, approve the pypi dual gate.
  2. **Regenerate the worker locks** (`requirements.lock` + `requirements-cpu.lock` — stale, missing `juniper-cascor-core`; can't regen until 0.1.0 is on PyPI). Worker `main` is already red from multiple causes — check full CI, don't assume publish+lock greens it.
  3. **Revert the deploy stopgap** — `juniper-deploy/docker-compose.cw05-stopgap.yml` is an untracked operational overlay (nothing in git to revert); stop applying it, delete the local file, rebuild the worker container so it imports `candidate_unit` from the installed package.
  4. **MANDATORY live dual-path verification** (the original #319 goal): on the running 2-worker deploy stack, confirm cascade training grows hidden units via the **REMOTE tier** — **read WORKER logs, not just cascor status.** `cascor#319` stays OPEN until this passes.

### 3. Round-2 adversarial re-verification on the model pick (deferred)

- The refactor doc Part 7 carries a **"Pending — Round 2 (a)"** note: when the OQ-4 model-pick redesign lands, re-verify **(a)** the revised model recommendation + any new citations, and **(b)** that the doc edits introduced no dangling cross-references / dropped content.
- The **refactor-scope** Round-2 (live-code drift sweep) is DONE (#349); the **model-scope (a)** pass is still **pending OQ-4 (thread 1).** Run it with independent adversarial agents (cite primary sources, self-flag unverifiable claims) once the pick is chosen, and append results to Part 7.

## Key context (decisions + constraints — do not re-litigate)

- **cascor has NO temporal substrate today** (stateless 2-D `(batch, features)`, single-shot autograd / no BPTT, 4-key frozen-unit dict with no state slot). Gating prerequisite for any recurrent unit.
- **Window variable, T ∈ 1..~30 ⇒ BPTT-over-window is the default candidate gradient**; readout-mask for dense-state / sparse-supervision; output-layer training stays a static solve; **T=1 ⇒ today's cascor** (safe identity migration). RTRL deferred (proposals §8).
- **Ceiling reality (validated):** P1 *inherits* it; P2 *breaks* it but has no constructive training recipe; P3 does **not** escape it (ESP fading memory ≠ counting).
Knorozova-Ronca remedy = negative-weight second-order / multiplicative neurons, **not** rotation matrices.
- **Migration constraint (Part 8 §8.1) — durable:** the two deploy stacks resolve shared packages by INCOMPATIBLE mechanisms — on-host = editable `pip install -e` into conda envs (`JuniperData` / `JuniperCascor1` / `JuniperCanopy1`); docker = PyPI-pinned `requirements.lock` with single-repo build context → **publish-first is mandatory, and pyproject-pin + lock-regen must land in the SAME change** (else green build → runtime `ModuleNotFoundError`).
This is exactly why cascor-core thread step (1) blocks step (2).
On-host hazard: host `8200` is held by `duplicati` (cascor stays on 8201); `JuniperCascor1` lacks LIBTORCH activate hooks.
- **CONCURRENCY (resolved this thread):** the earlier shared-`main`-checkout hazard is CLEARED — the stale/destructive uncommitted doc edits were stashed to `stash@{0}` ("tier-1-prep stash") and local `main` was fast-forwarded.
**But a parallel session keeps advancing juniper-ml `main` — run `gh pr list` + check recent `main` before editing shared docs; coordinate, don't race.**
A `feature/juniper-cascor-core` worktree may still exist.

## Git status

- juniper-ml local `main` is **current + clean** (the earlier "behind / blocked-by-uncommitted-edits" state is fixed). This thread's work all MERGED: **#349, #385, #387, #388** (plus prior #344, #377, #378). No outstanding worktree/branch of mine.
- cascor-core publish handoff lives on its own unmerged branch (`docs/handoff-cascor-core-publish-2026-06-07`).
- Superseded doc edits preserved in `stash@{0}` — drop when confident (`git stash drop stash@{0}`).

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin && git log --oneline origin/main -8                  # what concurrent sessions merged
for n in 349 385 387 388; do echo -n "#$n "; gh pr view $n --json state -q .state; done   # all MERGED
# cascor-core deploy gating signals (thread 2):
curl -s -o /dev/null -w "%{http_code}\n" https://pypi.org/pypi/juniper-cascor-core/json    # 404 until published
gh issue view 319 -R pcalnon/juniper-cascor --json state -q .state                          # OPEN until live dual-path verified
# OQ-4 (thread 1):
sed -n '1,40p' notes/JUNIPER_RECURSE_OQ4_RECURRENT_CASCOR_PROPOSALS_2026-06-04.md
```
