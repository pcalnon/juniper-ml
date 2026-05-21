# Requirements Consolidation

Continue Juniper ecosystem CI hygiene + branch-protection cleanup. The session has been a long chain of: detect-CI-regression → diagnose → fix → merge → cleanup → repeat, across all 8 repos. Multiple parallel sessions are active; PRs occasionally stomp on each other.

## Completed so far

- Branch-protection refresh: all 8 repos now have active rulesets with current required-status-checks (renames since #266 etc.); 4 (data/cascor/canopy/worker) already had async-route audit required. Dropped `require_code_owner_review` on juniper-data + juniper-canopy so PR authors can self-approve.
- README markdownlint per-file MD013/MD033/MD041 disable applied to 5 repos (ml #283, cascor #276, worker #71, data-client #68, cascor-client #52) — same canonical §4-layout pattern.
- juniper-canopy script rename `generate_dep_docs.bash → .sh` to match ci.yml invocation (#295).
- Dep-docs script: sed → awk #69 → python yaml #72 — all chased wrong root cause. Real fix in #74: `pip install -q pyyaml` in ci.yml + `pyyaml>=6.0` in pyproject `[test]` extras. The script's `python -c "import yaml" 2>/dev/null` swallowed `ModuleNotFoundError` and surfaced it as misleading "invalid YAML syntax".
- Lockfile guardrails (auto-regen on pyproject change + pre-commit presence guard) ported across all 4 lockfile-having repos.
- pip-audit: 11 unpatched torch PYSEC IDs (2025-189..197, 2025-210, 2026-139) `--ignore-vuln`'d in juniper-cascor #282 + juniper-cascor-worker #75 with documented re-eval cadence (quarterly).
- Status docs: notes/STATUS_FOLLOWUP_ASYNC_ROUTE_AUDIT_2026-05-19.md + notes/STATUS_ROADMAP_AUDIT_2026-05-19.md in juniper-ml.

## Current state (2026-05-20)

- ❌ juniper-ml CI failure on `2e69954f` (PR #289 feat/doc-tools-precommit-hook)
- ❌ juniper-canopy CI failure on `3b93077d` (PR #299 fix/api-01-health-status-normalize)
- ✅ Other 6 repos green: data, cascor, worker, cascor-client, data-client, deploy

## Remaining work

1. Investigate juniper-ml failure (sha 2e69954f, PR #289) — likely a new failure from the doc-tools-precommit-hook landing.
2. Investigate juniper-canopy failure (sha 3b93077d, PR #299).
3. Optional preventative: juniper-data + juniper-cascor scripts still use the awk pattern from PR #69; could port to python yaml + pyyaml install pattern. Not currently failing.
4. Wave-3 doc-tools-precommit-hook PRs just landed across all 8 repos — sanity-check for cross-repo issues.

## Key context

- I'm in juniper-ml session worktree `.claude/worktrees/transient-moseying-gizmo`. Worktree cleanup deferred to harness per Paul's standing preference.
- Parallel-session PR collision: PR #73 in worker stomped on #72's pyyaml fix. Defensive answer was declaring pyyaml in `[test]` extras AND a strong DO-NOT-REMOVE comment in ci.yml. Watch for similar collisions.
- Branch-protection is ACTIVELY ENFORCING; BLOCKED merges need `gh pr merge --admin` (I have admin). Already used once on cascor-client #49 earlier.
- Quality Gate is an aggregator — don't add to required-checks elsewhere without ensuring its dependent jobs reliably pass.
- Solo-author rule: ALL 8 repos now have `require_code_owner_review: false` or no `pull_request` rule. Don't re-introduce.
- `notes/REQUIREMENTS_NEXT_STEPS.md` + `notes/STATUS_ROADMAP_AUDIT_2026-05-19.md` track requirements work; v5 consolidate script is irrecoverable (plan-doc §12 #19).
- pip-audit `--ignore-vuln` list re-evaluation cadence: quarterly, or when pip-audit advisory DB syncs a new torch release.

## Verification commands for the new thread

- `for r in juniper-ml juniper-data juniper-cascor juniper-canopy juniper-cascor-worker juniper-cascor-client juniper-data-client juniper-deploy; do gh run list --workflow=ci.yml --branch=main --limit=1 -R pcalnon/$r --json conclusion,headSha -q '"'"'.[]'"'"'; done`
- For each red repo: `gh api repos/pcalnon/<repo>/commits/<sha>/check-runs?per_page=100 --jq '.check_runs[] | select(.conclusion == "failure") | .name'`
- `gh pr list -R pcalnon/<repo> --state open` for any in-flight PRs

## Git status

clean tree, branch is whatever the session worktree was last on (chore/status-audits-2026-05-19 region, all earlier work merged).

---
