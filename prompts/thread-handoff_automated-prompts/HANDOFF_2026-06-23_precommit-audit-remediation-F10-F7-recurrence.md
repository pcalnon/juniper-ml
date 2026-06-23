# Thread Handoff — Juniper Pre-commit & Testing-Infra Audit Remediation (F10 → F7 → recurrence)

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Author**: Paul Calnon
**Prepared by**: Claude Code (Opus 4.8)
**Created**: 2026-06-23
**Purpose**: Continue the ecosystem-wide pre-commit / testing-infrastructure audit **remediation** in a fresh thread, per the mandatory thread-handoff policy (handoff replaces compaction). This picks up where [`HANDOFF_2026-06-21_precommit-testing-audit-remediation.md`](HANDOFF_2026-06-21_precommit-testing-audit-remediation.md) left off — the juniper-ml-local items (B4 / Wave-1 doc / F14) and the F11 stub removals are now done; what remains is the **cross-repo / fleet tail**: F10 → F7 → the recurrence MED/LOW tail (Paul-confirmed order). Use this file as the opening prompt for the new thread.

---

## 0. FIRST — verify current project state before beginning any work task

Repos in this ecosystem advance **same-day**, and **multiple Claude sessions run this same backlog in parallel** — duplicate-work races have already happened during this effort. **Do not act on the assumptions below without re-verifying live state.**

1. **Read the running record (source of truth).** The auto-memory file carries the full PR-by-PR history and the latest reconciliation note; treat it as authoritative where it differs from this prompt:

   ```bash
   cat "$HOME/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/project_precommit_testing_audit_2026-06-19.md"
   ```

2. **Confirm the two in-flight F11 PRs landed**, then clean their worktrees:

   ```bash
   gh pr view 205 -R pcalnon/juniper-data   --json state,mergedAt,title
   gh pr view 354 -R pcalnon/juniper-cascor --json state,mergedAt,title
   ```

   If MERGED: remove the corresponding centralized worktrees under `…/Juniper/worktrees/` (look for `juniper-data--fix--remove-dead-util-run-tests-stub--*` and `juniper-cascor--fix--remove-dead-util-run-tests-stub--*`), then `git worktree prune` in each repo. If still OPEN, leave them.

3. **Collision check — before EVERY remediation task.** For the target repo run BOTH; if another session already opened/merged the same fix, **STOP and reconcile** (do not duplicate):

   ```bash
   gh pr list -R pcalnon/<repo> --state open
   git -C <repo-path> log --oneline -12 origin/main
   ```

4. **VERIFY EVERY FINDING against live files.** This is the load-bearing lesson of the whole effort: **F3, F14, F10, and F11 were each materially different from the Wave-1 finding on inspection** (F3 worse than stated; F14 "~6"→3; F10 mostly-legitimate; F11 cascor premise wrong). Treat the Wave-1 findings doc as a *claim to verify*, not ground truth.

5. **Ground-truth the conda envs before any F10 edit:**

   ```bash
   conda env list | grep -i juniper   # live = JuniperCanopy1 / JuniperCascor1 / JuniperData; bare = *-DEPRECATED
   ```

6. **Branch fresh, every time.** `git -C <repo> fetch origin`, then a worktree off `origin/main` in the centralized `…/Juniper/worktrees/` (`<repo>--<branch>--<YYYYMMDD-HHMM>--<short-hash>`). **One commit per PR.** PR to `main`; **never commit to main — Paul approves all merges.** **juniper-data: use a `fix/**` branch** (its `chore/**` branches get no push-CI).

---

## 1. What is already done (this remediation effort)

- **Batch 1** (safe config hardening, 8 PRs) and **Batch 2** (coverage parity, 7 PRs) — MERGED (earlier threads).
- **B3 — `juniper-recurrence`** onboarding (the one CRITICAL repo) — CORE COMPLETE & MERGED (pre-commit config + bench CI lane + coverage + required-checks + security + the config-actually-passes fix #42).
- **B4 — juniper-ml monorepo governance (F3)** — `#508` **MERGED**: one `ruff` (`--fix`) + `ruff-format` hook pair (`ruff-pre-commit v0.15.18`) in the **root** `.pre-commit-config.yaml`, scoped to the 6 sub-package dirs; ruff per-file config auto-discovery (doc-tools=320 / rest=512); CI enforcement free via the existing root `ci.yml` pre-commit job. Decisions: `N` kept active but `ignore=["N803","N806"]` (ML Data-Contract `X`/`X_val`/`y`); 2× `N818` exported exceptions grandfathered via `# noqa`; 2 real model-core bugbear fixed (B905/B017).
- **Wave-1 findings doc** archived — `#509` **MERGED** (`notes/JUNIPER_PRECOMMIT_TESTING_AUDIT_WAVE1_FINDINGS_2026-06-19.md`).
- **F14 — orphaned tests wired into `ci.yml`** — `#510` **MERGED**: `test_requirements_drift_check.py` + `test_juniper_plant_all.py` + `test_juniper_chop_all.py` were enumerated-out of the `tests` job; all 3 CI-safe, pass 3.12–3.14.
- **F11 — dead `util/run_tests.bash` stubs** — **data `#205`** + **cascor `#354`** (both single-commit, CI-green, **OPEN, awaiting Paul's merge** as of handoff). data stub = copied-from-cascor (`Application: juniper_cascor`, `proto.bash`, unreferenced). cascor stub = broken (`/opt/miniforge3/envs/JuniperPython/bin/python` no longer exists; `SCRIPT_DIR`→`util/`; redundant with the real `src/tests/scripts/run_tests.bash`, which was left untouched).

## 2. What remains (do in this order — Paul-confirmed)

### 2.1 — F10: durable env-name fix (canopy + cascor)

Dev-setup docs tell developers to `conda activate JuniperCanopy` / `JuniperCascor` — the now-**`-DEPRECATED`** envs (activating one drops you into a broken-torch env). **Paul chose the DURABLE fix, NOT a bare→`1` bump**: in the dev-setup docs, add a one-time **convention note + `conda env list | grep Juniper<App>` discovery** so the docs never re-stale on the next env rebuild, and point activation/path/verify commands at the current `JuniperCanopy1` / `JuniperCascor1`.

- **SCOPE IN** — canopy: `README.md`, `AGENTS.md`, `docs/DEVELOPER_CHEATSHEET.md`, `docs/ENVIRONMENT_SETUP.md`. cascor: `README.md`, `AGENTS.md`, `docs/DEVELOPER_CHEATSHEET.md`, `docs/install/ENVIRONMENT_SETUP.md`, `docs/install/QUICK_START.md`, `docs/testing/ENVIRONMENT_SETUP.md`, `docs/ci_cd/ENVIRONMENT_SETUP.md`.
- **SCOPE OUT (bare name is LEGITIMATE — do NOT touch):** file-header `# Sub-Project: JuniperCanopy/JuniperCascor` lines (that's the *project* name); **functional CI env files** (canopy `conf/conda_environment_ci.yaml` `name:`, cascor `.github/workflows/ci.yml` `ENV_NAME: JuniperCascor` — these create *ephemeral, internally-consistent* CI envs); `notes/history/**`; captured stack traces (e.g. cascor `notes/setup_config_guides/forkserver_fix.md`); `CHANGELOG.md`; timestamped `conda_environment_ci_*.yaml` snapshots.
- **THE CATCH (env-flow coherence):** the env **CREATE-from-file** path is interdependent — a doc that says `conda env create -f conf/conda_environment.yaml` then `conda activate <name>` must stay coherent with that yaml's `name:` field. Do **not** ship a doc that creates `JuniperCanopy` then activates `JuniperCanopy1`. Simplest coherent design: the per-doc convention note frames the versioned naming + "run the grep and substitute your live env," so any residual create-from-file name is *explained* rather than contradictory. (canopy `docs/ENVIRONMENT_SETUP.md` already uses `conda env list | grep JuniperCanopy` in its Verify section — build on that.)
- **Output:** ~2 PRs (one per repo). Recommend doing canopy first as the reference implementation, then mirroring in cascor.

### 2.2 — F7: pre-commit-hooks fleet alignment → v6.0.0

`pre-commit-hooks` spans three majors: **v4.6.0** (cascor, cascor-client, cascor-worker, data-client, **juniper-ml**), **v5.0.0** (deploy), **v6.0.0** (canopy, data — already on v6 and passing, so v6 is the proven target). Bump the laggards to **v6.0.0**. After each bump, **verify `pre-commit run --all-files` still passes** in that repo (major bumps can change hook behavior). ~6 PRs; delegating these to parallel sub-agents is a good fit.

### 2.3 — recurrence MED/LOW tail (was task #4)

In `juniper-recurrence`: **CI-6** (docker job `needs:`), **CI-8** (concurrency groups), **DEP-3** (declare `juniper-data[equities]` for the bench equities row), **DEP-6** (dep-floor caps), **TST-5** (warnings policy), **TST-6/7/8** (new tests for untested bench-evaluator / `X-Request-ID` / `EventSink` overflow). Mix of trivial config + a few real new tests. Optional: format recurrence `bench/` at 512 (landed at ruff default 88).

### 2.4 — F13 (lower priority, can fold into F7 sweeps)

Wheel-install smoke: most repos test only the editable install; the built wheel is `twine check`'d but never imported. juniper-ml already has a wheel smoke-test — propagate the pattern. Cross-repo.

## 3. Conventions & guardrails (carry these forward)

- **Verify-first, evidence-cited.** Every factual claim → a `file:line` or captured command+result. `NOT VERIFIED` is a valid first-class state. The Wave-1 findings doc is a claim-set, not truth.
- **Per repo:** read its `AGENTS.md` first (parent `CLAUDE.md` mandate), collision-check, worktree off fresh `origin/main`, **single commit per PR**, PR to `main`, **Paul merges**. Clean worktrees only after a confirmed `MERGED` state.
- **Commit trailers:** end commits with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` and the `Claude-Session:` link. PR bodies end with the `🤖 Generated with [Claude Code]` footer.
- **juniper-data CI-trigger gotcha:** `chore/**` branches get no push-CI (only `main`/`develop`/`feature/**`/`fix/**`); use a `fix/**` branch.
- **Delegation works:** well-specified mechanical PRs delegated to parallel sub-agents have been reliable across this effort (F11's two removals, ~20 PRs earlier). Give each agent the exact edits, validation steps, single-commit + trailer format, collision-check, and a "STOP and report if reality doesn't match" guard. Return the PR URL.
- **Provisional-then-CI-measures** for risky thresholds.

## 4. Artifacts & references (all in `juniper-ml`)

- Memory: `project_precommit_testing_audit_2026-06-19.md` — the running record; **read first.**
- `notes/JUNIPER_PRECOMMIT_TESTING_AUDIT_PLAN_2026-06-19.md` — methodology + rubric.
- `notes/JUNIPER_PRECOMMIT_TESTING_AUDIT_WAVE1_FINDINGS_2026-06-19.md` — cross-repo drift matrix + findings F1–F17 (interim snapshot; **verify before trusting**).
- `notes/JUNIPER_RECURRENCE_PRECOMMIT_TESTING_CI_AUDIT_2026-06-21.md` — recurrence deep-dive (§9 = prioritized backlog feeding §2.3).
- Prior handoff: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-06-21_precommit-testing-audit-remediation.md`.

## 5. Recommended first move

Complete §0 (verify state; confirm `#205`/`#354` merged + clean their worktrees), then start **F10 on canopy** — design the durable convention note once, apply it coherently across canopy's 4 dev-setup docs (mind the create-from-file env-flow), open the PR, and use it as the template for cascor. Then F7, then the recurrence tail.

---

*Generated by Claude Code (Opus 4.8) as a mandatory thread handoff. Begin by completing §0.*
