# Handoff — AGENTS.md version-drift lint fanout (2026-05-21, evening)

Continue Juniper ecosystem CI hygiene work. This handoff follows ~3 hours of ad-hoc cleanup that surfaced organically from the prior `HANDOFF_2026-05-21_ci-hygiene-completion.md` verification step. The ecosystem remains in an unusually clean state.

## Completed this session

| # | Item                                                                                                                                | PR(s)                                                               |
|---|-------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|
| A | juniper-ml CI failure — 3 trailing-whitespace lines in `CHANGELOG.md` (post-#301 fallout) red-lighting all 3 Pre-commit matrix legs | juniper-ml #302                                                     |
| B | juniper-ml AGENTS.md version-drift — header said 0.4.0 but pyproject.toml is 0.5.0 (6 days stale post #295)                         | juniper-ml #304                                                     |
| C | New ecosystem-wide drift-check lint test pinning `AGENTS.md` `**Version**:` ↔ `pyproject.toml` `[project].version`                  | juniper-ml #305 (canonical)                                         |
| D | Strip dead `sys.version_info < (3, 11)` guard from the canonical lint (ruff UP036 surfaced during fanout port)                      | juniper-ml #306                                                     |
| E | Port lint + fix existing drift — juniper-data AGENTS.md 0.5.0 → 0.6.0                                                               | juniper-data #138                                                   |
| F | Port lint + fix existing drift — juniper-cascor-client AGENTS.md 0.3.0 → 0.4.0                                                      | juniper-cascor-client #58                                           |
| G | Port lint + fix existing drift — juniper-data-client AGENTS.md 0.3.2 → 0.4.1                                                        | juniper-data-client #74                                             |
| H | Preventive port (already-in-sync repos) — juniper-cascor / juniper-canopy / juniper-cascor-worker                                   | juniper-cascor #294, juniper-canopy #309, juniper-cascor-worker #81 |

**11 PRs shipped across 7 repos, all merged via `gh pr merge --admin --squash --delete-branch`.** Three of the merges returned `! Pull request was already merged` (concurrent merges by Paul or another agent); same expected behavior as the prior session.

## Final ecosystem state

| Repo                  | AGENTS.md         | pyproject.toml     | Lint installed?                                        |
|-----------------------|-------------------|--------------------|--------------------------------------------------------|
| juniper-ml            | 0.5.0             | 0.5.0              | ✅ `tests/test_agents_md_version_drift.py` (canonical) |
| juniper-data          | 0.6.0 ← was 0.5.0 | 0.6.0              | ✅ `util/test_agents_md_version_drift.py`              |
| juniper-cascor        | 0.4.0             | 0.4.0              | ✅ `util/test_agents_md_version_drift.py` (preventive) |
| juniper-canopy        | 0.4.0             | 0.4.0              | ✅ `util/test_agents_md_version_drift.py` (preventive) |
| juniper-cascor-worker | 0.3.0             | 0.3.0              | ✅ `util/test_agents_md_version_drift.py` (preventive) |
| juniper-cascor-client | 0.4.0 ← was 0.3.0 | 0.4.0              | ✅ `util/test_agents_md_version_drift.py`              |
| juniper-data-client   | 0.4.1 ← was 0.3.2 | 0.4.1              | ✅ `util/test_agents_md_version_drift.py`              |
| juniper-deploy        | 0.2.1             | n/a (no pyproject) | ⏸ N/A — correctly skipped                              |

All 7 pyproject-having Juniper repos now lint-protected against the same drift class going forward.

## Key discoveries

1. **AGENTS.md → pyproject.toml drift is a real ecosystem-wide class, not a one-off.** Discovered while verifying juniper-ml's own state post the prior handoff (PR #304 fix). A quick `grep -E "^\*\*Version\*\*:" + pyproject.toml version` audit across all 8 repos surfaced 3 silently drifting siblings (data, cascor-client, data-client) ranging 1 minor to 0.9 patches behind. Followed the `test_pyproject_extras.py` / `test_workflow_script_paths.py` playbook (lint + fanout) to make recurrence mechanically impossible.

2. **Ruff UP036 caught dead-code on the portable port.** juniper-ml's canonical had a defensive `if sys.version_info < (3, 11): raise SkipTest(...)` guard that ruff (in juniper-data) flagged as unreachable because the ecosystem's `requires-python` floor is `>=3.11`/`>=3.12` everywhere. Cleaning it up in the sibling port forced a follow-up cleanup PR on juniper-ml (#306) to keep the canonical bit-identical to the ports. **Takeaway**: when porting between repos with different linters (juniper-ml uses black+flake8+mypy; juniper-data uses ruff), expect downstream-strict catches and budget a sync-back PR.

3. **Portable-by-design tests pay off.** `test_agents_md_version_drift.py` was written from the start to walk up for `pyproject.toml + AGENTS.md` from its own location, so the file is copy-paste verbatim across all 7 repos — same module, no per-repo edits. The only per-repo work was the ci.yml wiring and the (sometimes) AGENTS.md bump.

4. **Concurrency-cancellation noise around dispatch events.** Several runs showed `cancelled` status because `repository_dispatch` events (`data-client-updated`, `cascor-worker-updated`, `cascor-client-updated`) superseded `push` events for the same SHA. Always cross-check the push-event run for the same SHA before assuming red. Verified pattern: `gh run list --branch=main --limit=10 -R pcalnon/<repo> --workflow=ci.yml --json status,conclusion,event,headSha`.

5. **juniper-ci-tools v0.2.0 Wave 4 is actively fanning out** (`ci: adopt juniper-ci-tools v0.2.0 juniper-lint-workflow-paths`). Landed in juniper-data, juniper-cascor-worker, juniper-cascor-client, juniper-data-client during this session. juniper-cascor, juniper-canopy, juniper-ml are likely next. This is the parallel migration moving `util/test_workflow_script_paths.py` into the shared PyPI package — analogous to the dep-docs Wave 2/4 migration the prior session watched for.

## Active in-flight work to watch (not ours)

- **juniper-cascor [API-09 PR 3/3](https://github.com/pcalnon/juniper-cascor/commit/b1f9ea3a)** ("drop top-level 'detail' deprecation alias"). PR 1 landed earlier in the prior session (#293).
  - When PR 3 lands, downstream `juniper-cascor-client` may need an adapter update — its `_request()` currently reads `body.get("detail", response.text)`.
  - PR 2 (cascor-client #2564ba9d) already added regression coverage for the dual-shape envelope, so the alias removal in PR 3 should be safe — but worth eyeballing the next cascor-client release.
- **juniper-ci-tools Wave 4** continuing — cascor / canopy / ml fanout PRs likely incoming.
- **juniper-ml release** — `pyproject.toml` is at 0.5.0; PyPI is at 0.4.1; latest git tag is `v0.4.0`. A "chore: release v0.5.0 prep" commit (94a88e13) landed during this session. Paul is likely lining up the v0.5.0 tag/release.

## Remaining deferred items (from prior handoff, still deferred)

- ⏳ **Worktree sweep** — `/home/pcalnon/Development/python/Juniper/worktrees/` now has ~12 fresh worktrees from this session in addition to the prior ~40. Per Paul's standing preference, cleanup is deferred to the harness — **not** something the next thread should clean up unsolicited.
- ⏳ **Inline-script duplication audit** — actively being absorbed by juniper-ci-tools Waves 2 & 4; defer until those land.
- ⏳ **Wave 3 pre-commit hook adoption** (`juniper-check-doc-links` in `.pre-commit-config.yaml`) — quality-of-life, not blocking.

## Suggested next-thread agenda (priority order)

1. **Verify ecosystem state.** Run the verification commands below; confirm 8 repos still green on main, drift map still clean.
2. **Watch for juniper-ci-tools Wave 4 fallout** in cascor / canopy / ml as the fanout completes.
3. **Watch for juniper-cascor API-09 PR 3/3 landing** and check downstream juniper-cascor-client compatibility (PR 2's regression coverage should make this a no-op, but eyeball it).
4. **Optional drift-class hunt** — same playbook applied to other surfaces:
   - `**Last Updated**:` headers in AGENTS.md (probably stale across many repos)
   - PyPI version vs git tag lag (juniper-ml is the clearest example: pyproject 0.5.0, tag v0.4.0, PyPI 0.4.1)
   - juniper-ci-tools pin currency now that v0.2.0 is shipping (the existing `test_ci_tools_drift.py` should already catch this — verify it does, not silently skipped)
5. **Address whatever new ad-hoc Paul/concurrent-agent work surfaces.**

## Key context

- I'm in `/home/pcalnon/Development/python/Juniper/juniper-ml` (the main repo, not a worktree).
- Branch protection actively enforcing across all 8 repos; `gh pr merge --admin` is required and worked throughout the session.
- juniper-canopy local main is now in sync with origin (Paul's WIP `feat/env-and-settings-normalization-2026-05-20` landed mid-session as PR #308, merge 2acfc81).
- juniper-ml untracked files (Paul's): `notes/JUNIPER_2026-06-01_JUNIPER-ECOSYSTEM_CI-CLEANUP.md`, `prompts/prompt112_2026-05-21.md`, 6 prior handoffs in `prompts/thread-handoff_automated-prompts/`, `util/ad-hoc/apply_dep_docs_swap.py`, `util/ad-hoc/wave4_delete_inline_dep_docs.sh`. This handoff adds a 7th prompt file.
- Solo-author rule: all 8 repos have `require_code_owner_review: false` or no `pull_request` rule. Don't re-introduce.
- Pre-commit hook in juniper-ml will reformat with black on commit — the version-drift lint test was reformatted on first commit; that's normal, just `git add` and re-commit.
- **Portable test convention**: the lint test discovers its own repo root by walking up for `pyproject.toml + AGENTS.md`. Same pattern as `test_workflow_script_paths.py`. Resist any temptation to hardcode paths in future ports.
- **Per-repo file location convention**: juniper-ml puts unittest lint tests in `tests/`; siblings put them in `util/` (alongside `test_workflow_script_paths.py`). Honor whichever the repo already established.
- **Known pre-existing canopy flake** still applies: `test_probe_runs_concurrently_not_serially_under_fanout` (macOS Py3.12, threshold ~3200ms). Re-flaked once during this session then passed on retry. Pre-existing timing-sensitive flake — don't chase.

## Verification commands for the new thread

```bash
# 1. Confirm all 8 repos green on main
for r in juniper-ml juniper-data juniper-cascor juniper-canopy juniper-cascor-worker juniper-cascor-client juniper-data-client juniper-deploy; do
  gh run list --workflow=ci.yml --branch=main --limit=1 -R pcalnon/$r --json conclusion,headSha,displayTitle -q '"\(.[0].conclusion // "running")  '"$r"' \(.[0].headSha[:8])  \(.[0].displayTitle[:55])"'
done

# 2. Confirm zero open PRs (this session left zero)
for r in juniper-ml juniper-data juniper-cascor juniper-canopy juniper-cascor-worker juniper-cascor-client juniper-data-client juniper-deploy; do
  c=$(gh pr list -R pcalnon/$r --state open --json number -q 'length')
  [ "$c" != "0" ] && echo "$r: $c open" && gh pr list -R pcalnon/$r --state open
done

# 3. Confirm AGENTS.md ↔ pyproject.toml drift map is clean across all 7 applicable repos
for r in juniper-ml juniper-data juniper-cascor juniper-canopy juniper-cascor-worker juniper-cascor-client juniper-data-client; do
  cd /home/pcalnon/Development/python/Juniper/$r
  git fetch origin >/dev/null 2>&1
  agents_v=$(git show origin/main:AGENTS.md 2>/dev/null | grep -E "^\*\*Version\*\*: " | head -1 | awk -F': ' '{print $2}')
  pyproject_v=$(git show origin/main:pyproject.toml 2>/dev/null | grep -E '^version = ' | head -1 | awk -F'"' '{print $2}')
  drift="✓"
  [ "$agents_v" != "$pyproject_v" ] && drift="❌"
  printf "%s %-25s AGENTS=%-8s pyproject=%s\n" "$drift" "$r" "$agents_v" "$pyproject_v"
done

# 4. Confirm the portable lint is present in every applicable repo
for r in juniper-ml juniper-data juniper-cascor juniper-canopy juniper-cascor-worker juniper-cascor-client juniper-data-client; do
  cd /home/pcalnon/Development/python/Juniper/$r
  if [ "$r" = "juniper-ml" ]; then P="tests/test_agents_md_version_drift.py"; else P="util/test_agents_md_version_drift.py"; fi
  exists="❌"
  git cat-file -e origin/main:"$P" 2>/dev/null && exists="✅"
  printf "%s  %-25s  %s\n" "$exists" "$r" "$P"
done
```

## Git status snapshot

- Branch: `main` in `juniper-ml`
- Working tree: clean except for Paul's longstanding untracked files (now +1 handoff prompt from this session)
- Open PRs: 0 across all 8 repos
- Worktrees: ~50 directories under `~/Development/python/Juniper/worktrees/` (deferred to harness)
- Most recent PRs merged (this thread): juniper-ml #302/#304/#305/#306, juniper-data #138, juniper-cascor #294, juniper-canopy #309, juniper-cascor-worker #81, juniper-cascor-client #58, juniper-data-client #74

## Thread URL

`https://ampcode.com/threads/T-019e4b98-ed76-7216-a421-c8dbdb07d0b2`

---
