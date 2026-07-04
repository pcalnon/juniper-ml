# Thread Handoff — Juniper-Recurrence Full-Audit Remediation (Medium cluster → H2)

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Author**: Paul Calnon
**Prepared by**: Claude Code (Opus 4.8)
**Created**: 2026-06-25
**Purpose**: Continue the `juniper-recurrence` **full-audit remediation** backlog. The audit
([`notes/JUNIPER_2026-06-24_JUNIPER-RECURRENCE_FULL-AUDIT.md`](../../notes/JUNIPER_2026-06-24_JUNIPER-RECURRENCE_FULL-AUDIT.md),
shipped as juniper-ml#546) is the **source of truth** for every finding ID below. High-sev **H1** and
Mediums **M1/M2/M3** are shipped; the controlling-thread **tasks 1 (drift-consumer activation)** and
**2 (publish-trigger sweep)** are PR'd and green. What remains, in the user's stated order:
**task 3 = the Medium cluster**, then **task 4 = H2** (torch-MLP readout gating/coverage).

---

## 0. FIRST — verify live state (repos advance same-day; multiple sessions share this backlog)

1. **Read the audit (source of truth):**

   ```bash
   cat /home/pcalnon/Development/python/Juniper/juniper-ml/notes/JUNIPER_2026-06-24_JUNIPER-RECURRENCE_FULL-AUDIT.md
   ```

   §3 = finding inventory (3 High · 14 Medium · ~18 Low · 0 Critical); §4 = High/Medium detail;
   §6 = prioritized P1/P2/P3 plan.

2. **Sweep this session's 3 PRs' worktrees** — all **MERGED 2026-06-25** (re-confirm, then
   `git worktree prune`):

   ```bash
   for spec in "juniper-ml 560" "juniper-ml 561" "juniper-recurrence 65"; do
     set -- $spec; gh pr view "$2" -R "pcalnon/$1" --json state,title --jq "\"$1 #$2: \(.state) — \(.title)\""
   done
   ```

   - juniper-ml **#560** (`chore/service-core-drift-recurrence-consumer`) — task 1
   - juniper-ml **#561** (`chore/publish-workflows-dedupe-sweep`) — task 2a
   - juniper-recurrence **#65** (`chore/recurrence-publish-skip-existing`) — task 2b

3. **Collision-check before EVERY recurrence PR** (a concurrent session may grab the same item):

   ```bash
   gh pr list -R pcalnon/juniper-recurrence --state open
   git -C /home/pcalnon/Development/python/Juniper/juniper-recurrence log --oneline -10 origin/main
   ```

4. **VERIFY EVERY FINDING against fresh `origin/main`.** Recent PRs #61–#65 touched exactly these
   files, so the audit's line refs may have moved. Always create your worktree off fresh `origin/main`
   and inspect there — never trust the local tree or this doc's line numbers without re-checking.

---

## 1. Already done — carry-forward (merged to recurrence `main` @ `394b03e`)

- **H1** (OBS-01 / OBS-02) — application logging: **#61** added
  `juniper_recurrence/logging_config.py::init_logging(settings)` (guarded
  `from juniper_observability import configure_logging` + stdlib `basicConfig` fallback); **#64**
  moved the call into a `create_app(lifespan=)` lifespan in `app.py` (removed from `main._serve`,
  dropped the stray `import logging`).
- **service-core lifespan hook** — `juniper-service-core` **0.3.0**: **#550** added the
  `create_app(..., lifespan=...)` param → `FastAPI(lifespan=...)`; published via the **#555** recovery
  (after the release+push double-trigger bug stranded 0.3.0 on TestPyPI). juniper-ml `[tools]` pin is
  now `juniper-service-core>=0.3.0,<0.4.0`; recurrence app pins `>=0.3.0,<0.4.0` (#64).
- **M1** (MODEL-01) — `NaN`/`Inf` `dt` hardening: **#63** added `np.isfinite` guards on `u`/`dt` in
  `units/lmu_varstep.py` (`rollout` + `rollout_batch`) and `data.py`; `RFFReadout.__init__` now
  rejects `n_features_out < 1`.
- **M2 / M3** (DOC-01..05 / CI-01) — doc-currency sweep: **#62** reconciled all version tables,
  READMEs, and CHANGELOG dependency pins to shipped reality (app 0.2.0 / model 0.1.5 / client 0.2.0).
- **Controlling-thread tasks 1 + 2** — **#560** (recurrence registered in `_CONSUMER_REPOS` of
  `tests/test_service_core_drift.py`, monorepo subpath `juniper-recurrence/juniper-recurrence`),
  **#561** (5 sibling publish workflows: drop `push:tags` double-trigger → release-only + add
  `skip-existing`), **#65** (3 recurrence publish workflows: add `skip-existing` re-run defense; they
  are `push:tags`-only so no double-trigger). All three **MERGED 2026-06-25**.

## 2. Remaining — do in this order (user's task 3 → task 4)

All recurrence work: worktree off **fresh `origin/main`**, **single commit**, PR-to-main, **Paul
merges**. No JR-ID (net-new). Re-verify each line ref before editing.

### Task 3 — Medium cluster (audit §4 "Medium — remaining")

**Open scoping question for Paul** (he explicitly invited this choice — do NOT start before confirming):
the 4 focused PRs below, **or** one combined "Medium cluster" PR.

- **3a — small config (one PR):**
  - **TEST-02** — add `filterwarnings = ["error", <targeted ignores>]` to the **model** and
    **client** `[tool.pytest.ini_options]` (the **app** already has it — mirror its exact shape).
  - **CI-05** — add `.github/dependabot.yml` (pip weekly + github-actions weekly; mirror
    juniper-ml's). 3 published pkgs + SHA-pinned actions currently have no update bot.
- **3b — OBS-03 build-info provenance** *(bigger — not a one-liner):* thread `git_sha`/`build_date`
  into `set_build_info` (`juniper_recurrence/app.py:91`). recurrence has **no provenance module yet**;
  siblings (data/cascor/canopy) generate git_sha/build_date at build time — see the
  `project_build_provenance_effort` memory and `juniper-observability >= 0.4.0` `set_build_info`
  kwargs. Needs a provenance source first.
- **3c — CI-06 version-drift lint:** new test (or workflow) asserting each package's `_version.py`
  ↔ latest matching git tag ↔ top CHANGELOG heading agree. This is exactly what would have caught
  the DOC-05 / CI-01 drift.
- **3d — CI-04 bench CI parity:** add `feature/**`, `fix/**` to the `push:` filter in
  `ci-recurrence-bench.yml` (`:31`, currently `[main]`); consider a `required-checks` aggregator job.
- **Also Medium — fold in or explicitly note:** **TEST-03** bench-orchestration tests
  (`bench/run_benchmark.py` `run_dataset` / `_render_report` / `main` are untested — only leaf helpers
  covered); **DOC-06** archive the 5 missing `notes/releases/` files for already-published tags.
  **OBS-04** (domain metrics) is **design-deferred → skip.**

### Task 4 — H2 (TEST-01): torch-MLP readout gating + coverage

The shipped `readout="mlp"` (torch) path has **no merge-gating test** and is **omitted from
coverage** → it can regress green. Fix EITHER (ideally both): promote the `test-torch` CI lane into
required-checks (gating), OR add coverage of the MLP readout path
(`juniper-recurrence-model/.../readouts.py` torch-gated `MLPReadout` / `_readout_mlp`). Audit §4 H2
cites model `pyproject.toml:85` + `ci-recurrence-model.yml:124`.

## 3. Conventions & guardrails

- **Verify-first, evidence-cited** (`file:line` or captured command output). `NOT VERIFIED` is valid.
- **Monorepo layout:** `juniper-recurrence/` (app), `juniper-recurrence-model/`,
  `juniper-recurrence-client/`, and **`bench/` at repo root** (sibling of the packages). Validate edits
  with `pre-commit run --all-files` (config exists). **No `agents-md-touch-up.yml` in recurrence** →
  the F10 touch-up squash gotcha does NOT apply here.
- **recurrence CI:** PRs to main get `pull_request` CI; the 3 `ci-recurrence-{app,model,client}.yml`
  push-trigger on `feature/**`/`fix/**`, but **bench is main-only** (that's CI-04). Use a `fix/**` or
  `chore/**` head.
- **Worktrees** centralized at `/home/pcalnon/Development/python/Juniper/worktrees/`
  (`<repo>--<safe-branch>--<YYYYMMDD-HHMM>--<short8hash>`). Clean only after confirmed `MERGED`, then
  `git worktree prune`.
- **Commit trailers:** `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` + the
  `Claude-Session:` link. PR bodies end with the `🤖 Generated with [Claude Code]` footer.
- **Paul merges** (admin-bypass; `mergeStateStatus=BLOCKED` with all checks green is the normal
  state). `git fetch` before any re-push; do **not** force-push onto a branch Paul may have pushed to.
- **PyPI deploy gates are Paul's** — drive to the gate, then hand off; never self-approve.

## 4. Git / worktree state at handoff

- recurrence `origin/main` @ **`394b03e`** (PR #64 merged); juniper-ml `origin/main` @ **`a132a36`**
  (#561, the last of this session's three, merged).
- **MERGED this session (2026-06-25):** juniper-ml **#560** + **#561**; juniper-recurrence **#65**.
- **Worktrees ready to sweep** (`git worktree remove <dir>` then `git worktree prune`):
  - `…/worktrees/juniper-ml--chore--sc-drift-consumer--20260625-1451--6dbd0db0` (#560)
  - `…/worktrees/juniper-ml--chore--publish-workflows-dedupe-sweep--*` (#561 — locate via
    `git -C /home/pcalnon/Development/python/Juniper/juniper-ml worktree list`)
  - `…/worktrees/juniper-recurrence--chore--publish-skip-existing--20260625-1504--394b03e2` (#65)
  - plus this handoff's own `docs/handoff-recurrence-medium-h2` worktree once its PR merges.
- This handoff was written from the `eager-squishing-lagoon` juniper-ml session worktree.

## 5. Recommended first move

Complete §0 (verify #560/#561/#65 merged + sweep merged worktrees), then **ask Paul to confirm the
task-3 slicing** (4 focused PRs vs one combined Medium PR — he explicitly invited the choice), then
start **3a** off fresh recurrence `origin/main`.

---

*Generated by Claude Code (Opus 4.8) as a mandatory thread handoff at the tasks-1+2 → task-3 phase
boundary. Begin by completing §0.*
