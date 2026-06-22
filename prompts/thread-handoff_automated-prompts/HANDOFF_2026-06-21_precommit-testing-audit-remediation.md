# Thread Handoff — Juniper Pre-commit & Testing-Infrastructure Audit Remediation

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Author**: Paul Calnon
**Prepared by**: Claude Code (Opus 4.8)
**Created**: 2026-06-21
**Purpose**: Resume the ecosystem-wide pre-commit / testing-infrastructure audit + remediation in a fresh thread, per the mandatory thread-handoff policy (handoff replaces compaction). Use this file as the opening prompt for the new thread.

---

## 0. FIRST — verify current project state before beginning any work task

Repos in this ecosystem advance **same-day**, and **multiple Claude sessions run this same backlog in parallel** — duplicate-work races have already happened during this effort (two sessions independently shipped recurrence items 5/7/9). **Do not act on the assumptions below without re-verifying live state.** Run these and reconcile before touching anything:

1. **Read the running record (source of truth).** The auto-memory file carries the full PR-by-PR history and the latest reconciliation note; treat it as authoritative over this prompt where they differ:

   ```bash
   cat "$HOME/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/project_precommit_testing_audit_2026-06-19.md"
   ```

2. **Confirm the last in-flight PR landed.** `juniper-recurrence` PR #42 (pre-commit config fix + CI enforcement lane) was open/green at handoff:

   ```bash
   gh pr view 42 -R pcalnon/juniper-recurrence --json state,title,mergedAt
   ```

   If MERGED: remove its worktree (`git -C <…>/juniper-recurrence worktree list` → remove the `…precommit-config-fix-and-enforce…` entry, then `git worktree prune`) and verify the security scan ran (`gh run list -R pcalnon/juniper-recurrence --workflow security-scan.yml`; advisories are informative).

3. **Collision check — before EVERY remediation task.** For the target repo run BOTH, and if another session already opened or merged the same fix, **STOP and reconcile** (do not duplicate):

   ```bash
   gh pr list -R pcalnon/<repo> --state open
   git -C <repo> log --oneline -12 origin/main
   ```

4. **Branch fresh, every time.** `git -C <repo> fetch origin`, then a worktree off `origin/main` in the centralized `…/Juniper/worktrees/` (`<repo>--<branch>--<YYYYMMDD-HHMM>--<short-hash>`). **One commit per PR** (squash-merge here can drop follow-up commits). PR to `main`; **never commit to main directly — Paul approves all merges** and owns branch-protection toggles.

5. **Read live files, not this doc.** Versions, configs, CI workflows, and conda envs change; open the actual files in the fresh worktree before editing.

---

## 1. What is already done

- **Plan + Wave-1 ecosystem audit** of local pre-commit + testing infrastructure across the 9 active repos (the 8 documented ecosystem repos + `juniper-recurrence`; `juniper-slacker` excluded as a pre-project). Methodology was multi-agent-validated; Wave-1 produced a per-repo drift matrix + findings F1–F17 (see §4).
- **Batch 1 — safe config hardening (8 PRs, MERGED):** `default_install_hook_types` pre-push wiring (data), stale CI `SKIP` removals (cascor/deploy), explicit `asyncio_mode` (cascor/cascor-client/cascor-worker/data), missing `--strict-config`/`--strict-markers` (cascor-client/cascor-worker/data-client/deploy/config-tools), autoload guard for ci-tools/config-tools.
- **Batch 2 — coverage parity (7 PRs, MERGED):** a `make coverage` target + `util/run_coverage.bash` + AGENTS.md docs that reproduce each repo's CI coverage gate locally (finding F1), across canopy/cascor/cascor-client/cascor-worker/data/data-client; plus the previously-missing service-core CI coverage gate (F4, in juniper-ml).
- **B3 — `juniper-recurrence` (the one CRITICAL repo), CORE COMPLETE:** governance-docs refresh + autoload guard + model-lint job (#33); pre-commit onboarding via the audit's §8 profile (#34); bench CI lane + `[tool.coverage.*]` config (#36/#37, plus a concurrent session's #38); required-checks gate + pip-audit security + broadened push triggers (a concurrent session's #40, duplicating this session's #35); and — the genuinely-remaining gap — **making the pre-commit config actually pass and enforcing it in CI (#42)**: ruff-pre-commit pin bumped to `v0.15.18` (the line-length cap rose 320→512 at ruff 0.15.13), `.yamllint.yaml` added, AGENTS.md MD040 + bandit B104 fixed, and a new `ci-pre-commit.yml` lane (verified green live). A concurrent session duplicated items 5/7/9; `main` was verified clean afterward.

## 2. What remains

1. **(immediate)** Merge recurrence #42 if not already; clean its worktree; verify the `security-scan` run.
2. **B4 — juniper-ml monorepo governance (F3).** The root `.pre-commit-config.yaml` scopes Python to `^(scripts|tests)/.*\.py$`, so the **6 internal sub-packages' Python** (ci-tools, config-tools, doc-tools, model-core, observability, service-core) is governed by **no** pre-commit hook — lint/format/security run only in per-package CI. Design the fix (extend the root scope vs per-package hook wiring); **design-first — bring a proposal before executing.**
3. **B5 — fleet currency / hygiene.** F7 (`pre-commit-hooks` spans 3 majors v4.6.0/v5.0.0/v6.0.0 — align via considered bumps), F10 (stale conda-env-map docs: canopy + cascor name the deprecated bare `JuniperCanopy`/`JuniperCascor` envs; live envs are the `*1` variants), F11 (dead/stale `util/run_tests.bash` stubs in cascor + data), F13 (CI installs editable only — add a wheel-install smoke), F14 (juniper-ml has ~6 `tests/` modules not invoked by `ci.yml`).
4. **Commit the audit reports into `juniper-ml/notes/`.** The Wave-1 findings doc and the recurrence audit report were uncommitted in worktrees at handoff — commit them for the record (verify whether a concurrent session already did this).
5. **recurrence MED/LOW tail.** CI-6 (`docker` job `needs:`), CI-8 (concurrency groups), DEP-3 (declare `juniper-data[equities]` for the bench equities row), DEP-6 (dep-floor caps), TST-5 (warnings policy), TST-6/7/8 (untested bench-evaluator / `X-Request-ID` / `EventSink` overflow). Optional: format `bench/` at 512 (it landed at ruff's default 88).

## 3. Conventions & guardrails (carry these forward)

- **Evidence-cited, anti-hallucination.** Every factual claim → a `file:line` or a captured command + result; treat docs (AGENTS.md/CLAUDE.md/README) as claims to verify, not ground truth; `NOT VERIFIED` is a valid, first-class state.
- **Worktree per repo**, off fresh `origin/main`; **single commit per PR**; **PR to main, Paul merges**; clean worktrees only after a confirmed `MERGED` state (`gh pr view`).
- **Provisional-then-CI-measures** for risky thresholds (coverage gates): ship a safe value, let the PR's own CI reveal reality, then tune.
- **Commit trailers:** end commits with `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` and the `Claude-Session:` link.
- **Live conda envs:** `JuniperCanopy1`, `JuniperCascor1`, `JuniperData` (docs name the deprecated bare variants — that is itself finding F10).
- **Delegate well-specified mechanical PRs to parallel sub-agents** (proven reliable across ~20 PRs this effort): give each the exact edits, the validation steps, single-commit + trailer format, and a "STOP and report if the file doesn't match the expected anchor" guard.

## 4. Artifacts & references (all in `juniper-ml`)

- Memory: `project_precommit_testing_audit_2026-06-19.md` — the running record; **read first.**
- `notes/JUNIPER_PRECOMMIT_TESTING_AUDIT_PLAN_2026-06-19.md` — methodology + rubric (Areas A/B/C), multi-agent-validated.
- `notes/JUNIPER_PRECOMMIT_TESTING_AUDIT_WAVE1_FINDINGS_2026-06-19.md` — cross-repo drift matrix + findings F1–F17.
- `notes/JUNIPER_RECURRENCE_PRECOMMIT_TESTING_CI_AUDIT_2026-06-21.md` — recurrence deep-dive (§8 = the pre-commit profile, §9 = the prioritized backlog).

## 5. Recommended first move

Complete §0 (verify state), confirm #42 is merged + its worktree cleaned, then bring a **B4 design proposal** (the highest-severity remaining finding) for owner review before executing — consistent with the design-first cadence used throughout this effort.

---

*Generated by Claude Code (Opus 4.8) as a mandatory thread handoff. Begin by completing §0.*
