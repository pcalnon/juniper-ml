# Thread Handoff — Recurrence × Equities: the model 0.6.0 `pypi` gate still parked; the gate-independent tidy landed (juniper-ml#2283); #215 refreshed onto main; #215 → 0.8.0 → #219 → the 0.8.0 pins still next

**Date**: 2026-10-20
**Host**: turing (Darwin, Intel; no commit signing; bash 3.2) — every landing goes through `util/open_signed_pr.py` / `util/push_signed_commit.py` / `util/ad-hoc/2026-10-17_push_signed_with_retry.py`
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_recurrence-equities-w5-5-w5-6-landed-p5-code-complete-model-0-6-0-gate-parked.md`
**Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` at **v1.7.10** (unchanged this session: nothing here is an arc item)

---

## Goal

Continue the arc from plan v1.7.10. **This session** picked up the predecessor with merge approval granted and found the `pypi` gate on the model 0.6.0 publish run **still `waiting`** (run 39197693617; PyPI serves model 0.5.0 and recurrence 0.7.0). Merge approval covers PR merges, not the owner's deployment gate, so the session did the gate-independent work only:

- **juniper-recurrence#215 refreshed onto `main`** (`gh api -X PUT .../pulls/215/update-branch`; head `25b75832` → `a196f777`, `BEHIND` → `BLOCKED`). Its red set is unchanged and is entirely pip failing to resolve `juniper-recurrence-model>=0.6.0,<0.7.0` (the Test, Bench-smoke and Build lanes die in 7–26 s with "No matching distribution found"); the model, client, docs, pre-commit, CodeQL, memory-budget, sequence-safety and base-branch-guard lanes are green. After the gate, re-fire only the three failed runs on `a196f777`: **39408038761** (CI — juniper-recurrence-app), **39408038638** (CI — bench harness), **39408038634** (Publish Container Image).
- **juniper-ml#2283 (docs tidy)** landed the two follow-ups every handoff since 2026-10-18 carried: `CHANGELOG.md`'s `[Unreleased]` had two `### Changed` headings (the 0.6.1 raise, #2243, added one after `### Added`; the 0.7.0 raise, #2262, opened a second at the top); the two entries of the first block now head the surviving block and the section reads Added / Changed / Fixed. `docs/QUICK_START.md` § 2. Verify's `pip list` block still described juniper-ml 0.9.0 on 2026-09-22; it now shows what 0.10.0 resolves to on 2026-10-20 per `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py --extra recurrence --extra all` (`[recurrence]` 32 packages, `[all]` 76, on Python 3.12 / 3.13 / 3.14 alike; six lines moved: canopy 0.9.x, data 0.17.x, data-client 0.6.x, juniper-ml 0.10.0, recurrence 0.7.x, model 0.5.x). Applied by the idempotent `util/ad-hoc/2026-10-20_tidy_unreleased_changed_and_quick_start_pip_list.py` (`--check`, `--root`). Landed as two signed commits (the small files through `util/open_signed_pr.py`, the 180 KB `CHANGELOG.md` through the retry script, attempt 1 in 6 s at SNR 10 dB), merged with `util/safe_merge.py --execute`.
- **Deliberately not touched**: `docs/REFERENCE.md`'s Ecosystem Compatibility pins sentence (the 2026-10-18 handoff's ruling: it waits for the 0.11.x matrix row); the juniper-recurrence-client `train` / `crossval` docstrings (`client.py:414`, `:522`, response fields without `diagnostics`) — they follow #215, which changes the crossval response again, so one touch after 0.8.0 describes the current contract.

## Remaining work, in order (unchanged from the predecessor except the run ids)

1. **Owner**: approve the `pypi` gate on run 39197693617 (`juniper-recurrence-model-v0.6.0` at `2c5a419c`; environment `pypi`, id 16691727515; `current_user_can_approve` is true for the agent, which is exactly why it is not the agent's click):
   `gh api -X POST repos/pcalnon/juniper-recurrence/actions/runs/39197693617/pending_deployments -f 'environment_ids[]=16691727515' -f state=approved -f comment='model 0.6.0'`.
   Then verify 0.6.0's `requires_dist` equals 0.5.0's (`python3 -I -c` against `https://pypi.org/pypi/juniper-recurrence-model/0.6.0/json`).
2. **juniper-recurrence#215** (W5.2 service half + the `[torch]` extra fix, head `a196f777`, now level with main): once 0.6.0 is on the index, `gh run rerun 39408038761 --failed --repo pcalnon/juniper-recurrence`, likewise 39408038638 and 39408038634 (a fresh `update-branch` first if `main` has moved again; then the run ids are new — list them with `gh run list --repo pcalnon/juniper-recurrence --commit <head>`), then `python3 -I util/safe_merge.py --pr 215 --repo juniper-recurrence --execute` (its own merge approval). Then **recurrence 0.8.0**: `util/release_train/detect.py` → `propose.py --dry-run` / `--execute --cross-repo` → merge → `ceremony.py --execute --cross-repo --target-sha <merge sha>`; close the follow-on ceiling PR only if a floor raise supersedes it; the release notes must name the `[torch]` fix (0.7.0's `juniper-recurrence[torch]` cannot resolve).
3. **juniper-recurrence#219** (bench multi-ticker row, `5e409f50`, `BLOCKED`): rerun its lanes after #215 merges and 0.6.0 is on PyPI; the CHANGELOG hunk may conflict after #215 — re-run `util/ad-hoc/2026-10-19_apply_w5_2_bench_multi_ticker.py` on a fresh main copy.
4. **The 0.8.0 pins** (owner rulings, taken with merge approval last time): juniper-ml `[recurrence]` → `juniper-recurrence>=0.8.0,<0.9.0` and `juniper-recurrence-model>=0.6.0,<0.7.0` (copy `util/ad-hoc/2026-10-19_raise_recurrence_floor_0_7_0.py`; its `_insert_changelog_entry` no longer meets two `### Changed` headings; pre-flight with `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py`; regenerate the README compat table with `util/ad-hoc/2026-09-21_sync_readme_compat_table.py`; the `docs/QUICK_START.md` pip-list block moves recurrence to 0.8.x and model to 0.6.x in the same PR — the 0.7.0 script does not touch it, add two exact-text edits); Compose `juniper-recurrence:0.8.0` (copy `util/ad-hoc/2026-10-19_pin_compose_recurrence_0_7_0.py`; verify GHCR first).
5. **Owner**: W0.1 service-core half (cascor restart recipe in juniper-recurrence/AGENTS.md); parent `Juniper/AGENTS.md` RELEASED paragraph (recurrence 0.7.0, model 0.5.0 → 0.6.0 after the gate); juniper-data's next release carrying W5.7; refresh the juniper-recurrence and juniper-data checkouts (`! git -C /Users/pcalnon/Development/python/Juniper/juniper-recurrence pull --ff-only`, likewise juniper-data, behind #486).
6. Follow-ups: W1.12 / W1.11 smokes on the 0.7.0 image (a host whose Docker reaches GHCR); recurrence-client docstrings (`client.py:414`, `:522`) after #215; juniper-canopy#735–738, #751; juniper-ml#2210, #2211; juniper-deploy#250; the `ARCHIVE_B64_MAX_DEFAULT` measurement in `util/release_train/ceremony.py`; `docs/REFERENCE.md`'s pins sentence with the 0.11.x matrix row; optional: a first real run of the E-H suite with `--shared-equities-cache` to measure the per-cell saving. **Closed this session**: the duplicate `### Changed` headings; the `docs/QUICK_START.md` pip-list block.

## Landing rules learned or confirmed this session

- **The `pypi` gate is the owner's even with merge approval in hand.** `pending_deployments` reports `current_user_can_approve: true`; the memory `pypi-gate-is-owner-only` records why it is still not the agent's click. Report the run id and the command; do the gate-independent work.
- **`update-branch` on a PR whose only red is an unpublished dependency is cheap and worth doing early**: the lanes fail in seconds, the branch is level with main, and the post-gate step shrinks to `gh run rerun <id> --failed` on three known run ids.
- The markdownlint hook excludes `CHANGELOG.md`, `docs/`, `notes/` and `prompts/` (`.pre-commit-config.yaml`), so "Passed" on those paths is vacuous; the doc-link validator and gitleaks do run on them. For an API landing, scan copies with the hook's gitleaks binary in `dir` mode (`~/.cache/pre-commit/repo5uz_qsw8/golangenv-system/bin/gitleaks dir <copies> --config .gitleaks.toml --redact`).
- Everything else as in the predecessor: upload worktree files directly only while `origin/main` equals the worktree base (checked immediately before each upload; this session's base `b9f9d38d` held); `CHANGELOG.md` and `docs/REFERENCE.md` as their own retried commits; merge approvals do not carry over (#215, 0.8.0's proposal, #219 and the 0.8.0 pins each need their own); the worktree guard's refusals (one plain command per call, literal paths, `python3 -I <script>`).

## Verification commands for the new thread

```bash
gh run view 39197693617 --repo pcalnon/juniper-recurrence --json status,conclusion
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-recurrence-model/json'))['info']['version'])"
gh pr view 2283 --repo pcalnon/juniper-ml --json state,mergeCommit -q '.state + " " + (.mergeCommit.oid // "-")'
gh pr view 215 --repo pcalnon/juniper-recurrence --json state,headRefOid,mergeable,mergeStateStatus -q '.state + " " + .headRefOid + " " + .mergeable + " " + .mergeStateStatus'
gh run list --repo pcalnon/juniper-recurrence --commit a196f7774b9c421aaad33637d6025e9fc1a2e93e --json databaseId,name,conclusion
gh pr view 219 --repo pcalnon/juniper-recurrence --json state,headRefOid,mergeable,mergeStateStatus -q '.state + " " + .headRefOid + " " + .mergeable + " " + .mergeStateStatus'
git show origin/main:CHANGELOG.md | awk '/^## \[Unreleased\]/{f=1} f&&/^## \[/&&!/Unreleased/{exit} f&&/^### /{print NR": "$0}'
git show origin/main:docs/QUICK_START.md | grep -c 'resolved to on 2026-10-20'
python3 -I util/ad-hoc/2026-10-20_tidy_unreleased_changed_and_quick_start_pip_list.py --check   # exit 0 on main
```

## Git state

- Worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/elegant-hatching-minsky` on branch `worktree-elegant-hatching-minsky`, base `b9f9d38d`; nothing committed locally; every change landed through the API. Its modified / untracked files (`CHANGELOG.md`, `docs/QUICK_START.md`, the tidy script, this handoff) are all on `origin/main` once the handoff PR merges; `git checkout -- . && git clean -fd` on the worktree is safe after that.
- juniper-recurrence and juniper-data checkouts untouched (juniper-data at `7465d5a4`, behind #486's `58c013e3`).

## Documents created or modified this session

- `CHANGELOG.md` (juniper-ml#2283: heading merge only)
- `docs/QUICK_START.md` (juniper-ml#2283: § 2. Verify, the pip-list prose and block)
- `util/ad-hoc/2026-10-20_tidy_unreleased_changed_and_quick_start_pip_list.py` (new, juniper-ml#2283)
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_recurrence-equities-model-0-6-0-gate-still-parked-docs-tidy-landed-215-refreshed.md` (this file)
- Referenced, unchanged: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.10); the predecessor handoff above; `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-18_recurrence-equities-0-6-1-published-extras-floor-and-p5-next.md` (the pins-sentence ruling)
