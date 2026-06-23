# Thread Handoff — Juniper Pre-commit & Testing-Infra Audit Remediation (recurrence MED/LOW tail → F13)

**Project**: Juniper — Cascade Correlation Neural Network Research Platform
**Author**: Paul Calnon
**Prepared by**: Claude Code (Opus 4.8)
**Created**: 2026-06-23
**Purpose**: Continue the ecosystem-wide pre-commit / testing-infrastructure audit **remediation**, picking up where [`HANDOFF_2026-06-23_precommit-audit-remediation-F10-F7-recurrence.md`](HANDOFF_2026-06-23_precommit-audit-remediation-F10-F7-recurrence.md) left off. That thread completed **F10** and **F7**; what remains is the **`juniper-recurrence` MED/LOW tail** and **F13** (wheel-install smoke). Use this file as the opening prompt for a fresh thread, per the mandatory thread-handoff policy.

---

## 0. FIRST — verify live state before any work (repos advance same-day; multiple sessions run this backlog)

1. **Read the running record (source of truth)** — full PR-by-PR history + latest reconciliation:

   ```bash
   cat "$HOME/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory/project_precommit_testing_audit_2026-06-19.md"
   ```

2. **Confirm this session's 8 PRs merged**, then sweep their worktrees once each shows `MERGED`:
   - F10: canopy **#387**, cascor **#357** (both single-commit, green when handed off)
   - F7 (`pre-commit-hooks`→v6.0.0): cascor **#358**, cascor-client **#80**, cascor-worker **#109**, data-client **#101**, juniper-ml **#518**, deploy **#131**

   ```bash
   for pr in "juniper-canopy 387" "juniper-cascor 357" "juniper-cascor 358" "juniper-cascor-client 80" "juniper-cascor-worker 109" "juniper-data-client 101" "juniper-ml 518" "juniper-deploy 131"; do
     set -- $pr; gh pr view "$2" -R "pcalnon/$1" --json state,mergedAt,title --jq '"\($1) #\($2): \(.state)"'
   done
   ```

   Worktrees to remove once merged (all under `…/Juniper/worktrees/`): the `*--fix--f10-env-docs-durable-naming--*` (canopy, cascor) and `*--fix--precommit-hooks-v6-audit-f7--*` (6 repos) dirs; `git worktree prune` in each repo after. Also this handoff's own worktree `juniper-ml--docs--handoff-recurrence-tail-f13--*` once its PR merges.

3. **Collision-check before EVERY recurrence PR** (a concurrent session may grab the same item):

   ```bash
   gh pr list -R pcalnon/juniper-recurrence --state open
   git -C /home/pcalnon/Development/python/Juniper/juniper-recurrence log --oneline -10 origin/main
   ```

4. **VERIFY EVERY FINDING against fresh `origin/main`.** Load-bearing lesson of this whole effort — F3/F14/F10/F11 were each materially different on inspection. **The recurrence LOCAL checkout was STALE this session** (it lacked the merged B3 artifacts). **Always create your worktree off fresh `origin/main` and inspect there — never trust the local working tree or even this doc's line numbers without re-checking.** Recent DP-3 work (#44/#45/#46) may have already touched bench deps — re-confirm DEP-3/TST-6 against current files.

---

## 1. What is already done (carry-forward)

- **Batches 1 & 2**, **B3 recurrence onboarding**, **B4 ml-governance (#508)**, **Wave-1 doc (#509)**, **F14 (#510)**, **F11 (data #205, cascor #354)** — all MERGED (earlier threads).
- **F10 — durable conda env-name convention** — canopy **#387** + cascor **#357**, both **single-commit, CI-green, OPEN** at handoff. Design: per-doc convention note (versioned `JuniperX1→X2→…` + `conda env list | grep JuniperX` discovery + never-activate-`*-DEPRECATED`) + point activate/verify/path/create at the live `JuniperCanopy1`/`JuniperCascor1`. Latent-bug fix: `conf/conda_environment.yaml` has **no `name:` field** in both repos → nameless `conda env create -f` errors → create cmds now pass `-n <env>`. Scope-out (left unchanged): arch diagrams, `# Sub-Project:` headers, SECURITY-PATCH/Grafana product names, functional `conf/*.yaml` + CI/Docker env files (cascor `docs/ci_cd/ENVIRONMENT_SETUP.md` is all ephemeral CI/Docker env → untouched, + 1 clarifying note). **Gotcha handled:** both touched `AGENTS.md` → the `agents-md-touch-up.yml` bot pushed a `[skip ci]` date-bump commit (→ 2 commits, `BLOCKED`); fixed by squashing the bump into my commit (`git reset --soft HEAD~2 && commit && push --force-with-lease`) so the touch-up no-ops on re-run.
- **F7 — `pre-commit-hooks`→v6.0.0** across all 6 laggards (6 PRs above), each verified `pre-commit run --all-files` clean, single-commit (config-only). Safe per official changelog: v6.0.0 removed only `check-byte-order-marker`+`fix-encoding-pragma` (neither used anywhere); min-Python 3.9 satisfied. canopy+data were already v6.

---

## 2. What remains (do in this order)

All recurrence work = **`juniper-recurrence` repo, worktree off fresh `origin/main`, PR-to-main, Paul merges.** No JR-ID (net-new). Full spec: [`notes/JUNIPER_RECURRENCE_PRECOMMIT_TESTING_CI_AUDIT_2026-06-21.md`](../../notes/JUNIPER_RECURRENCE_PRECOMMIT_TESTING_CI_AUDIT_2026-06-21.md) §9 backlog (items 10, 11, 12, 14) — verify line refs against current files.

### Verified repo facts (re-confirm, but these held on 2026-06-23 origin/main)

- Monorepo: `juniper-recurrence/` (app), `juniper-recurrence-model/`, `juniper-recurrence-client/`, and **`bench/` at REPO ROOT** (sibling of the packages).
- `origin/main` already has `.pre-commit-config.yaml`, `.markdownlint.yaml`, `.yamllint.yaml`, `ci-pre-commit.yml`, `ci-recurrence-bench.yml`, `security-scan.yml` (B3 #34–#42). **So validate edits with `pre-commit run --all-files` in your worktree.**
- **No `agents-md-touch-up.yml`** in recurrence → the F10 touch-up squash gotcha does NOT apply here.
- CI push triggers are `main`-only today (that's CI-4 below); **PRs to main still get `pull_request` CI**, so a `fix/**` head works. Use `fix/**` (not `chore/**`).

### 2.1 — Config-currency PR (audit items 10 + 11 + TST-5) — ~1.5 hr, recommend bundling

- **CI-4** — broaden push filters: add `feature/**`, `fix/**` to `push: branches:` in `ci-recurrence-{app,model,client}.yml` (currently `[main]`).
- **CI-6** — add `needs: [lint, test]` to the app **docker** job (`ci-recurrence-app.yml`, ~L107 — runs ungated today).
- **CI-8** — add `concurrency:` groups to the 3 CI workflows (NOT the publish workflows).
- **DEP-3** — add a `bench-equities` extra = `juniper-data[equities]` (app `pyproject.toml`) and cap `juniper-data<0.8.0`; the `equities_seq` bench row needs it (silent SKIP today). `bench/` has no pyproject — deps ride the app's `[bench]` extra.
- **DEP-6** — cap dep floors: app `juniper-data>=0.7.0`→`,<0.8.0`, `juniper-observability[prometheus]>=0.4.0`→`,<0.5.0`; client `juniper-observability>=0.3.1`→`,<0.5.0`.
- **DEP-5** (decision) — model runtime floor `juniper-model-core>=0.1.0` understates advertised crossval (CHANGELOG/README imply 0.2.0; `[crossval]` already `>=0.2.0`). Confirm runtime works on 0.1.0 or raise floor to `>=0.2.0`. Include if cheap to verify, else note.
- **TST-5** — add a `filterwarnings = ["error", <targeted ignores>]` policy to the app `[tool.pytest.ini_options]`, matching `juniper-cascor/pyproject.toml`'s targeted-ignore shape (start app-side).

### 2.2 — Tests PR (audit item 14 subset TST-6/7/8) — real new tests

- **TST-6** — unit-test `bench/run_benchmark.evaluate_bands` (the PASS/MISS RMSE-reduction arithmetic, `run_benchmark.py:54-96`) with a hand-built `results` dict asserting pass/fail; and promote `app_e2e.main` (already uses `TestClient`) into the bench CI lane.
- **TST-7** — client `X-Request-ID` propagation (`client.py:214-223`): test graceful no-op when observability absent + header-attached + caller-supplied-wins.
- **TST-8** — `EventSink` ring-buffer eviction (`events.py:25,29`, `maxlen=256`): overflow test with `maxlen=2`.
- (Optional, same PR or note: TST-9 model `time_unit`/`random_seed`; TST-10 marker registry; CODEOWNERS CI-10; client lint-in-matrix CI-11 — all LOW.)

### 2.3 — F13: wheel-install smoke (audit item 12 / CI-5) — cross-repo

Most repos test only the editable install; the built wheel is `twine check`'d but never imported. Propagate juniper-ml's clean-venv wheel-import pattern (`juniper-ml/ci.yml`; recurrence baseline `ci-model-core.yml:98-105`) into each `build` job. Start with recurrence's 3 `build` jobs, then the wider fleet per the original handoff §2.4.

---

## 3. Conventions & guardrails (unchanged)

- **Verify-first, evidence-cited** (`file:line` or captured command). `NOT VERIFIED` is valid. Work off fresh `origin/main`.
- Per repo: read its `AGENTS.md`; collision-check; worktree off fresh `origin/main` in `…/Juniper/worktrees/` (`<repo>--<safe-branch>--<YYYYMMDD-HHMM>--<short8hash>`); **single commit per PR**; PR-to-main; **Paul merges.** Clean worktrees only after confirmed `MERGED`.
- Commit trailers: `Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>` + the `Claude-Session:` link. PR bodies end with the `🤖 Generated with [Claude Code]` footer.
- **Delegation works** for well-specified mechanical PRs (F7 ran 6 in parallel cleanly). The config-currency items (2.1) suit one careful PR; TST-6/7/8 need source-reading, so do them directly or delegate with exact specs.
- Recurrence-specific: validate with `pre-commit run --all-files` (config now exists); `bench/` is at repo root; no agents-md-touch-up.

## 4. Recommended first move

Complete §0 (verify the 8 PRs' merge state + sweep merged worktrees), then start **§2.1 config-currency PR** off fresh `origin/main` (re-verify every line ref first), then **§2.2 tests**, then **§2.3 F13**.

---

*Generated by Claude Code (Opus 4.8) as a mandatory thread handoff at the F7→recurrence phase boundary. Begin by completing §0.*
