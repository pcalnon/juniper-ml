# Thread Handoff — Recurrence × Equities: the release train sees the juniper-ml pins again; the recurrence client's embargo default fixed; plan v1.7.13

**Date**: 2026-10-21
**Host**: turing (Darwin, Intel; no commit signing; bash 3.2). Every landing goes through `util/open_signed_pr.py` / `util/ad-hoc/2026-10-17_push_signed_with_retry.py`.
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_recurrence-equities-recurrence-0-8-0-published-extras-and-compose-pins-landed-plan-v1-7-12.md` (juniper-ml#2293)
**Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` at **v1.7.13** (this session, via `util/ad-hoc/2026-10-21_plan_v1_7_13_release_train_sees_pins_client_embargo.py`)

---

## Goal

Continue the arc from plan v1.7.13. **This session** was one thread, with merge approval granted at its start. It picked up the predecessor at step 2.

- **Step 2, the post-merge re-check, passed.** Every juniper-ml#2292 line is on `main` `b16121ac`: `AGENTS.md`, `docs/REFERENCE.md` (its two-column extras table), `CHANGELOG.md`, `docs/QUICK_START.md` and `pyproject.toml`. `util/ad-hoc/2026-10-20_raise_recurrence_floor_0_8_0.py --check` now exits 1 only because of the two date stamps (2026-10-21); every content site is "already at target".
- **Step 3, the juniper-ml release, was blocked twice. Both blocks were found in dry runs and both are fixed.**
  - **juniper-ml#2296, merged as `ed1dc061`: the detector.** `util/release_train/detect.py`'s `classify_pyproject_patch` took a hunk's TOML table only from a `[table]` line inside the hunk or from its `@@` trailer. Git's default trailer is the nearest line that starts with a letter (`@@ -81,9 +81,9 @@ doc-tools = [`), never a `[table]`. So every `[servers]` / `[recurrence]` range change since v0.10.0 read as tooling, juniper-ml (`ship_paths: []`) read **UP_TO_DATE**, and `propose.py` had nothing to propose. Published 0.10.0 still carries `juniper-recurrence>=0.5.0,<0.6.0`. The fix takes each hunk's table from the HEAD file when the hunk's new-side lines align there, and an unresolved table is UNCERTAIN, never NON-SHIP.
    - Measured on the 7 in-repo packages: juniper-ml now reads **UNRELEASED_CHANGES → 0.11.0**, and **juniper-config-tools UNRELEASED_CHANGES → 0.2.0**. config-tools' `Typing :: Typed` classifier, together with `py.typed` package-data, is unreleased since 0.1.0, and its `[Unreleased]` is empty, so the manifest flags it under-documented. The other 5 are unchanged.
    - The daily `release-train.yml` is in `report` mode (`RELEASE_TRAIN_MODE` unset), so nothing is proposed by itself.
  - **juniper-ml#2298, merged as `f7af5e3d`: the proposal PR body.** `propose.py` inlined the whole notes draft in the PR body and opens the PR only after the release branch and its signed commit exist. GitHub refuses a body over 65,536 characters. 0.11.0's draft is 88,548 B, which made the body 90,219 characters, so `--execute` would have left `release/juniper-ml-v0.11.0` with no PR. An over-long draft is now a pointer to the PR's own CHANGELOG diff, which brings the body to 1,909 B, and `execute_proposal` refuses an over-long body before any write.
- **Step 4's client follow-up grew a correctness fix: juniper-recurrence#221, merged as `cc2a6467`.** `JuniperRecurrenceClient.crossval` defaulted `embargo` to `0` and always sent it. 0.8.0 honours an explicit value, so every client caller who omitted it ran unembargoed, and W5.2's look-back default never applied. `embargo` now defaults to `None` and is sent only when given. The docstrings and README now name `metrics_scope`, `operation_id`, `diagnostics`, `folding` and the `trainval` pool.
  - Unaffected: juniper-canopy (it does not call crossval, OQ-2) and the juniper-ml driver (raw HTTP; it omits `embargo` already, #2256).
  - It ships in the client's next release, a 0.3.1 patch inside juniper-ml's `<0.4.0` ceiling. An `embargo_days` passthrough would make that release a minor, so it is left to the owner.
- **Plan v1.7.13** (`util/ad-hoc/2026-10-21_plan_v1_7_13_release_train_sees_pins_client_embargo.py --detect-sha ed1dc061 --propose-sha f7af5e3d --client-sha cc2a6467`) updates the Status line, the Progress block (session 7 bullet, Next rewritten) and the revision row. It lands in one PR with this handoff and the script.

## Remaining work, in order

1. **Owner decision: the juniper-ml 0.11.0 cut (timing is the owner's call).** Once it is a go, follow the 0.8.0 recipe (memory `release-train-follow-on-pr`):
   - Get a tree at `origin/main`. `python3 util/release_train/detect.py --package juniper-ml --json > <manifest>` should read UNRELEASED_CHANGES, 0.11.0.
   - **Dry-run first**: `python3 util/release_train/propose.py --manifest <manifest> --package juniper-ml --dry-run --json`. Check that `pr_body` is ≤ 65,536 and that the `notes_draft` base64 is ≤ 125,000 B. On 2026-10-21 it was **118,064 B, 6,936 B of headroom**, and every new `[Unreleased]` entry eats into it. Over the cap, condense with `util/ad-hoc/2026-10-17_condense_release_notes_section.py` (the canopy 0.9.0 precedent).
   - `propose.py --execute`, then merge the proposal with `util/safe_merge.py` and re-detect at its merge sha (it reads BUMPED_NOT_RELEASED).
   - `ceremony.py --execute --cross-repo --target-sha <40-char>` after main CI completes green. It cuts the Release and the archive PR, then parks at the owner's `pypi` gate.
   - Co-change with the cut: `docs/REFERENCE.md:177`'s pins sentence still says "`juniper-ml` 0.10.0 declares…" with juniper-ml 0.8.0's recurrence ranges, and needs a `0.11.x` matrix row (data `>=0.17.0`, canopy `>=0.9.0`).
   - After the publish, the parent `Juniper/AGENTS.md` RELEASED paragraph follows.
2. **Owner**: the juniper-recurrence-client 0.3.1 release (it carries #221's embargo fix), and whether to add `embargo_days`. Also juniper-config-tools: release 0.2.0 for the typing marker (backfill its `[Unreleased]` first), or leave it. Plus the predecessor's owner list:
   - the W0.1 service-core half;
   - the parent `Juniper/AGENTS.md` RELEASED paragraph (recurrence 0.8.0, model 0.6.0);
   - juniper-data's next release carrying W5.7;
   - refreshing the juniper-recurrence and juniper-data checkouts: `! git -C /Users/pcalnon/Development/python/Juniper/juniper-recurrence pull --ff-only`, likewise juniper-data. juniper-recurrence is now also behind #221.
3. **Post-merge re-check** (memory `api-whole-file-uploads-rebase-on-main`): about an hour after #2296 / #2298 merge, run `git show origin/main:CHANGELOG.md | grep -c 'The release-train detector no longer discounts'` and the same for `'The release-train proposal keeps its PR body'`; each should print 1. A revert costs one re-run of `util/ad-hoc/2026-10-21_apply_detect_pyproject_table_changelog.py` / `…_apply_propose_pr_body_limit_changelog.py`.
4. Follow-ups:
   - The W1.12 / W1.11 smokes on the 0.8.0 image, on a host whose Docker reaches GHCR.
   - juniper-ml#2211 is now unblocked: `save_model` via `POST /v1/model/snapshots` with `expect_operation_id`, since juniper-ml pins recurrence 0.8.0.
   - juniper-ml#2210: `per_run_timeout_seconds` against the summed driver budgets.
   - juniper-canopy#735–738 and #751; juniper-deploy#250.
   - The `ARCHIVE_B64_MAX_DEFAULT` runner-side measurement in `util/release_train/ceremony.py`, which matters now that 0.11.0 is within 7 KB of the cap.
   - Optional: a first real run of the E-H suite with `--shared-equities-cache`.

## Landing rules learned this session

- **`main` moved twice during one PR's CI** (#2295, then #2297). Each move turns a green PR BEHIND, and auto-merge waits. The recipe each time:
  1. `git fetch origin <branch>`;
  2. `git merge-tree --write-tree --name-only origin/main FETCH_HEAD` (a bare tree id means clean);
  3. `gh api -X PUT repos/pcalnon/juniper-ml/pulls/N/update-branch -f expected_head_sha=<full sha>`.
  Each update restarts CI (about 10 min). Auto-merge armed with `--match-head-commit` survives the update.
- **Two PRs that both insert at the top of `[Unreleased]`'s `### Fixed` conflict**, so the second one's `CHANGELOG.md` is built after the first merges. The apply scripts find the `### Fixed` heading instead of anchoring on today's first entry, so they re-run cleanly on any later `main`.
- **A `.py` fix's discrimination check**: copy `main`'s module and the new tests into a scratch tree and run them there. The new tests must fail, and the old ones must pass on both. propose's suite needs repository fixtures, so there a direct probe of both modules (`propose_body_probe.py` in the scratchpad) showed the difference instead.
- The worktree guard refuses `gh … -q` jq programs that contain `\(…)` string interpolation inside a shell `for` loop. Run one plain `gh` call per issue.
- Everything else is as in the predecessor: the `pypi` gate is the owner's; `CHANGELOG.md` lands as its own retried commit built from a fresh `origin/main` copy; the dir-mode secret scan runs through a scratchpad wrapper; one plain command per call under the guard.

## Verification commands for the new thread

```bash
gh pr view 2296 --repo pcalnon/juniper-ml --json state,mergeCommit -q '.state + " " + (.mergeCommit.oid // "-")'            # MERGED ed1dc061
gh pr view 2298 --repo pcalnon/juniper-ml --json state,mergeCommit -q '.state + " " + (.mergeCommit.oid // "-")'            # MERGED f7af5e3d
gh pr view 221 --repo pcalnon/juniper-recurrence --json state,mergeCommit -q '.state + " " + (.mergeCommit.oid // "-")'     # MERGED cc2a6467
python3 util/release_train/detect.py --package juniper-ml --json | python3 -I -c "import json,sys; p=json.load(sys.stdin)['packages'][0]; print(p['classification'], p['proposed_version'])"   # UNRELEASED_CHANGES 0.11.0 (tree at origin/main)
python3 -m unittest tests/test_release_train_detect.py tests/test_release_train_propose.py    # 97 + 146 OK
grep -n '^- \*\*Version\*\*' notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md   # 1.7.13
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-ml/json'))['info']['version'])"   # 0.10.0 until the cut
```

## Git state

- Worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/sleepy-cooking-hammock` on branch `worktree-sleepy-cooking-hammock`, base `b16121ac`. Nothing is committed locally; every change landed through the API. Its modified and untracked files are all on `origin/main` once #2296, #2298 and the plan PR merge, so `git checkout -- . && git clean -fd` on the worktree is safe after that.
- The juniper-recurrence and juniper-data checkouts are untouched. The client work was done on a scratch copy of juniper-recurrence `main` `87a28761`, fetched by API.

## Documents created or modified this session

- `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.12 → v1.7.13)
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_recurrence-equities-release-train-sees-pins-client-embargo-fixed-plan-v1-7-13.md` (this file)
- `util/ad-hoc/2026-10-21_plan_v1_7_13_release_train_sees_pins_client_embargo.py` (new)
- juniper-ml#2296: `util/release_train/detect.py`, `tests/test_release_train_detect.py`, `util/ad-hoc/2026-10-21_apply_detect_pyproject_table_changelog.py` (new), `CHANGELOG.md`
- juniper-ml#2298: `util/release_train/propose.py`, `tests/test_release_train_propose.py`, `util/ad-hoc/2026-10-21_apply_propose_pr_body_limit_changelog.py` (new), `CHANGELOG.md`
- juniper-recurrence#221: `juniper-recurrence-client/juniper_recurrence_client/client.py`, `juniper-recurrence-client/tests/test_client.py`, `juniper-recurrence-client/README.md`, `juniper-recurrence-client/CHANGELOG.md`
- Referenced:
  - the predecessor handoff above;
  - `notes/JUNIPER_2026-07-11_JUNIPER-ECOSYSTEM_PYPI-RELEASE-TRAIN-WORKFLOW-PLAN.md` §5 (the SHIP / NON-SHIP rule, "never silent-skip");
  - `util/release_train/ceremony.py` (`ARCHIVE_B64_MAX_DEFAULT`);
  - `util/ad-hoc/2026-10-20_raise_recurrence_floor_0_8_0.py`;
  - `util/ad-hoc/2026-10-17_condense_release_notes_section.py`;
  - `notes/requirements/by-area/DEP.md` (JR-ML-DEP-042), `notes/requirements/by-area/OPS.md` (JR-ML-OPS-007), `notes/requirements/by-repo/rec.md` (JR-REC-API-001).
