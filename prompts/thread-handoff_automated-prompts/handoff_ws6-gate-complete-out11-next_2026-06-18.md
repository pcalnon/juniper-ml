# Thread Handoff Prompt — 2026-06-18 (model-core 0.2.0 + WS-6 gate complete → OUT-11 next)

Continue the Juniper **model/middleware refactor (WS-6 track)**. The prior thread completed the
`juniper-model-core` 0.2.0 arc and verified the **entire WS-6 trigger-gate**; the next major piece
is **OUT-11 — build `juniper-service-core`'s T2 surface**, the last prerequisite for the WS-6 cascor
cutover. **Heavy concurrent-session activity — VERIFY before building** (see Key context).

Stack is at a clean stopping point: model-core is done + published + consumed; the WS-6 gate is
built + green; the only thing standing between "gate met" and "cutover startable" is OUT-11.

## Completed in the prior thread (verify, don't redo)

- **#436** umbrella model-core state-evaluation + roadmap (11 sub-agents). **#439** Phase 0 doc-truth
  (reconciled the canonical Status Tracker; `recurse`→`recurrence` rename).
- **#449** crossval 0.2.0 §4 API ratified (D-CV-6…10) + banked; reconciled to the **concurrent build
  #442** (adopted its held-out-default `pass_eval_as_val`, the more rigorous choice). **#450** polish
  (`ReferenceLinearModel.predict(**kw)`, `scheme: Literal`) + a one-char `pyproject.toml:64`
  trailing-space fix that **unbroke main's pre-commit**.
- **#456** OW-17 (model-core CI coverage gate 85→95; actual 97%). **#457** OW-18 (activated the
  `test_model_core_drift.py` consumer roster for the recurrence app — nested-path + `[crossval]`-extra aware).
- **#461** OUT-13 cascor↔model-core conformance plan **audited against reality** (all ~20 claims
  confirmed), then §0 (D-C1…D-C5) ratified + a §0.1 audit record banked.
- **#465 (MERGED)** WS-6 `DEFERRED→PLANNED` (trigger met), WS-4b corrected to `SHIPPED`, stale
  execution-banner refreshed. **#466** WS-6 OUT-11 caveat (gate passed ≠ cutover unblocked).
- **Verified already-built by concurrent sessions (do NOT rebuild):** crossval layer (cascor… no —
  juniper-ml **#442**), recurrence `POST /v1/crossval` endpoint (**juniper-recurrence #18**), the
  recurrence-side LMU-CV second-implementer test (**#15**), and the OUT-13 cascor conformance baseline
  (**juniper-cascor #341**). **4/4 "build X" requests this session were already built.**

## Current state (verified 2026-06-18)

- **model-core 0.2.0 on PyPI** — `TrainableModel`/`GrowableModel` ABCs + conformance kit + the
  `crossval` fold-executor (`metrics`/`splits`/`executor`, behind the `[crossval]` extra). Consumed by
  the recurrence app, which pins `juniper-model-core[crossval]>=0.2.0,<0.3.0` and serves `/v1/crossval`.
- **WS-6 gate FULLY MET** — OUT-12 golden suite (cascor #340, required check) + OUT-13 conformance
  baseline (cascor #341, conforms to the ratified §0) both green; recurrence interfaces proven.
- **WS-6 cutover BLOCKED on OUT-11** — `juniper-service-core` ships only its **T1** surface
  (`app`/`settings`/`security`/`middleware`/`health`/`lifecycle`/`launcher`/`secrets`). cascor cannot
  repoint its API/websocket/worker onto a T2 surface that does not exist.

## Remaining work — OUT-11 (the next major piece)

**OUT-11 = design + build `juniper-service-core`'s T2 surface.** Scope: generic routes (training /
predict / metrics / dataset / snapshots), the websocket subsystem, and the worker subsystem +
`TaskDistributor`. It is **un-designed** (no plan doc exists yet — unlike crossval/conformance, which
had detailed plans first) and **unbuilt** (no `routes/`/websocket/worker module on any branch).

1. **DUP-CHECK FIRST.** As of 2026-06-18 it was dup-clear (no service-core-T2 PR/branch/commit), but
   re-verify against fresh `origin/main` + branches + `gh pr list` before doing anything (the pattern
   is overwhelming — assume it may already be in flight).
2. **DESIGN PASS FIRST** (Paul is design-first): write a build plan in `notes/` (header schema like the
   other plan docs; ratify §0 decisions with Paul) before code. Reference material to generalize from:
   - the **recurrence app's routers** — `juniper-recurrence/juniper-recurrence/juniper_recurrence/routers/`
     `{training,predict,model,dataset,crossval,_common}.py` (the concrete routes a generic T2 abstracts);
   - **cascor's existing** `src/api/**` routes + websocket + worker (the production T2 source);
   - platform-roadmap doc `notes/JUNIPER_PLATFORM_ENVIRONMENT_STATE_AND_ROADMAP_2026-06-17.md` (OUT-11
     entry: "needed in full by WS-6; partially exercised by WS-4b routes").
3. **Then** the WS-6 cutover (6a/6b) is unblocked: cascor adopts service-core T1+T2 + makes the
   model-core conformance native (replacing the test-only OUT-13 adapter).

## Key context / lessons (read these — they cost real time to learn)

- **VERIFY-BEFORE-BUILD.** Every "build X" this session was already built concurrently. Before building:
  `git fetch`; check `origin/main` for the **code** (`git show origin/main:<path>`, not the local
  working tree); `gh pr list --state all`; `git branch -a`; `git log --all`. Build only if truly absent.
- **STALE LOCAL CHECKOUTS.** Sibling repos (`juniper-recurrence`, `juniper-cascor`) on disk are often
  behind their `origin/main` — a stale local checkout caused a wrong "cascor not yet wired" finding
  mid-session. Always `git -C <repo> fetch` + read `origin/main`, never the local working tree's `main`.
- **SQUASH-MERGE STRANDING.** Paul merges PRs fast, sometimes mid-iteration; GitHub squash-merge +
  branch auto-delete strands follow-up commits (happened #465→#466). After a merge, base new work off a
  fresh `origin/main`; don't push more onto a just-merged branch.
- **markdownlint on `notes/`.** `notes/` is EXCLUDED from the CI markdownlint hook, so many notes docs
  carry pre-existing violations. When you edit one, run
  `npx markdownlint-cli@0.42.0 --config=./.markdownlint.yaml <doc>` (line-length 512). `--fix` fixes
  blank-line rules (MD022/031/032/058) but NOT line-length — wrap prose manually; **table rows can't
  wrap, so trim** their cells.
- **Canonical docs.** Status Tracker = `notes/JUNIPER_MODEL_MIDDLEWARE_REFACTOR_DESIGN_AND_PLAN_2026-05-31.md`
  (reconciled to 2026-06-18 via #465/#466). The platform-roadmap doc tracks OUT-* items but
  self-disclaims its per-§3/§4 status cells as point-in-time 2026-06-17 snapshots — don't trust those cells.
- **Process guardrails.** No merge without Paul's explicit per-PR "merged" signal **and** `gh pr view`
  = MERGED; releases/PyPI/deploy gates are Paul-driven (don't self-approve).

## Verification commands (confirm starting state)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml   # (or the active worktree)
pip index versions juniper-model-core                    # expect 0.2.0 (+ 0.1.0)
( cd juniper-model-core && python3 -m pytest -q tests )  # expect ~95 passed
# WS-6 gate halves merged on cascor:
git -C ../juniper-cascor log --oneline origin/main | grep -E '#340|#341'
# OUT-11 still unbuilt (expect EMPTY):
git ls-tree -r origin/main --name-only -- juniper-service-core/juniper_service_core | grep -iE 'route|websocket|worker'
# OUT-11 dup-check (expect no T2 build PR/branch):
gh pr list --state open | grep -iE 'service-core|t2|route|websocket|worker'
git branch -a | grep -iE 'service-core|t2'
```

## Git / PR status (2026-06-18)

- **Open PRs awaiting Paul's review/merge:** #456 (OW-17), #457 (OW-18), #461 (OUT-13 ratification),
  #466 (WS-6 OUT-11 caveat).
- **Merged this session:** #436, #439, #449, #450, #465.
- Work happens in `.claude/worktrees/<session>` on feature branches cut from `origin/main`; clean up
  merged branches (`git branch -D` after `gh pr view` = MERGED, then `git fetch --prune`).
- **Memory:** `project_juniper_model_core_state_roadmap_2026-06-17.md` is the canonical session record
  (model-core arc, crossval reconciliation, WS-6 gate, the OUT-11 blocker, and the verify-first lessons).
