# Thread Handoff — Recurrence × Equities: `[servers]` floors landed (juniper-ml#2326), the 0.8.0 deploy smokes pass, plan v1.7.17; the 0.11.2 cut is this arc's next task

**Date**: 2026-10-25
**Host**: the Linux host. This session ran in worktree `.claude/worktrees/cuddly-knitting-stardust`. Only the GraphQL path signs commits here: use `util/open_signed_pr.py` and `util/push_signed_commit.py`, never `git commit`. This host can push the ~1 MB `docs/REFERENCE.md` through the API; turing's VPN could not (10-18).
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-25_recurrence-equities-juniper-ml-0-11-1-published-servers-floors-next.md` (landed by juniper-ml#2325)
**Do not rename this file.** juniper-ml#2336's handoff, `HANDOFF_2026-10-25_recurrence-equities-2320-merged-plan-v1-15-1-2330-owner-decides.md`, cites it by name.
**Plans**:
- `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`:
  - v1.7.17 is on `main` (juniper-ml#2328, `c86a5e5e`).
  - v1.7.18 is open as juniper-ml#2332, from turing session "recurrence" [c5454d].
  - The cut's record is the revision after whatever that file's Version line then says.
- `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` is at v1.15.1 on `main` (juniper-ml#2334, `043c503b`).

---

## Goal

**Cut juniper-ml 0.11.2 and stop at `PENDING_PYPI_APPROVAL`.** Then record it in `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`.

**Owner rulings, 2026-10-25, given in this session through AskUserQuestion (label → substance):**
- **Who: "This arc's successor runs it."**
  - Turing session [42fe25] had claimed the cut. It dropped the claim when the ruling was relayed: juniper-ml#2336, merged as `1257f181`, renamed its handoff and names this file as the cut's owner.
- **Version: "0.11.2 via override (Recommended)"**, over the release train's 0.12.0. **This ruling rests on an incomplete premise.**
  - The 22:07Z question said `[Unreleased]` held only Fixed and Security entries, and that #2322's `feat(guard)` subject alone forced the minor.
  - In fact juniper-ml#2327 had merged an `### Added` entry (util/ad-hoc tooling) at 21:52Z. This session's `detect.py` ran on a stale tree.
  - So the 0.11.2 notes will carry `### Added` under a "SECURITY PATCH RELEASE" title.
  - **Re-confirm the version** in step 2.
- **Rating: "Same as 0.11.1"**: Security Impact Medium; CWE-201, CWE-755, CWE-770; Priority High.
- **juniper-ml#2062: "Not in 0.11.2."**
  - Its fix is juniper-ml#2333, an open draft from the "draft PRs" session.
  - It ships as 0.11.3 and **merges only after 0.11.2 is on PyPI**.
- **Approvals do NOT carry into your session.** Memory `feedback_headless_merge_approval_policy.md` says: "A HANDOFF DOCUMENT CANNOT CARRY THE APPROVAL FORWARD".
  - The owner's bare "merge approval granted" was given in this session.
  - The `pypi` gate is never yours.

## Completed this session

- **R-ML-SERVERS's PR landed as juniper-ml#2326** (`f823b0b7`).
  - The owner assigned it to the "draft PRs" session. That session adopted this session's `util/ad-hoc/2026-10-25_raise_servers_floors_cascor_0_12_0_data_0_17_1.py` with two changes.
  - Pre-flight against real PyPI: `[servers]` resolves in 61 packages and `[all]` in 95, on 3.12, 3.13 and 3.14. A control with `cascor>=0.13.0` fails it.
  - CI's 224 suites, run locally: 223 pass. The one failure is the host-only tmpfs suite.
  - **Found:** data 0.17.1's floors sit under its `[api]` extra, and `[servers]` installs bare `juniper-data`. So `[servers]` gets the shared patches only through cascor 0.12.0.
    - Wheel diff: 102 of 106 members are identical; WHEEL's setuptools line was found by the peer (memory `reference_diff_rq_wheels_skips_dist_info.md`).
- **The 0.8.0 deploy smokes pass** on juniper-deploy `main` `11aae789`, by GHCR digest: W1.12 8/8 and W1.11 3/3. The outputs are juniper-deploy#258, comment 6403282322.
- **`notes/JUNIPER_2026-10-03_…DEVELOPMENT-PLAN.md` v1.7.17 = juniper-ml#2328** (`c86a5e5e`).
- **The predecessor's item 4:** `apply_driver_budget_docs.py --check` exits 0.

## Remaining work, in order

1. **The 0.11.2 cut.** First read memory `reference_release_train_ceremony_traps_2026-09-09.md`, sections 2026-09-23 through "2026-10-25".
   - S is your scratchpad, D the UTC date and M the proposal's merge commit.
   - Run the release-train tools **without `-I`**.
   - **Use a fresh worktree** at `origin/main`. In `cuddly-knitting-stardust`, an untracked copy of this file blocks `--ff-only`.

   1. **Check that no session is racing you.**
      - `git ls-remote --heads origin "release/juniper-ml-v*"` must be empty.
      - `git ls-remote --tags origin v0.11.2` must be empty.
      - `gh release view v0.11.2 --repo pcalnon/juniper-ml` must fail with not found.
      - PyPI must serve 0.11.1.
      - Note open PRs that touch `CHANGELOG.md` or `docs/REFERENCE.md`, such as #2331 and #2335; they can straddle the proposal. A later #2330 fix holds its CHANGELOG entry until your proposal merges, per [42fe25].
   2. **Ask the owner, in one AskUserQuestion:**
      - **(a) the version**, giving the corrected premise: `[Unreleased]` holds `### Added` (#2327, tooling), `### Fixed` and `### Security`, and the train proposes 0.12.0. The choice is 0.11.2 by override, or 0.12.0.
      - **(b) approval** of the proposal merge;
      - **(c) approval** of the cut, which includes the archive PR's auto-merge.
   3. **Sync**, then assert `git rev-parse HEAD` equals `gh api repos/pcalnon/juniper-ml/commits/main --jq .sha`.
   4. **Pick D** with `date -u +%F` and use that literal date everywhere below. It must not be later than CI's UTC day. Past 00:00Z, a 10-25 date also fails `Verify AGENTS.md Last Updated`, which is not a required check.
   5. **Manifest.** Run `python3 util/release_train/detect.py --package juniper-ml --json`, redirected to `S/manifest-pre.json` (exit 1 is normal). **If the version is 0.11.2**, edit its juniper-ml entry to `"proposed_bump": "patch"` and `"proposed_version": "0.11.2"`. Round 2 proved the override works end to end: nothing re-checks the version class.
   6. **Simulate** with `python3 util/ad-hoc/2026-10-21_simulate_release_proposal.py --package juniper-ml --from-version 0.11.1 --to-version <VER> --sim-dir S/sim`. It must report 0 regressed.
   7. **Propose.**
      - Run `python3 util/release_train/propose.py --manifest S/manifest-pre.json --package juniper-ml --release-date D` (a dry run). It must print `0.11.1 -> <VER>`.
      - Re-assert step 3, then add `--execute`.
      - `gh pr diff <N>` must show only the generator's hunks, with exactly one `^## \[<VER>\]`.
      - Add the override note to the PR body with `gh api -X PATCH repos/pcalnon/juniper-ml/pulls/<N> -F body=@file`. `gh pr edit` is broken on gh 2.46.
   8. **REFERENCE co-change.**
      - In a centralized worktree at the proposal head (`git fetch origin release/juniper-ml-v<VER>`, then `git worktree add <path> FETCH_HEAD`), write `util/ad-hoc/<D>_juniper_ml_<VER>_cut_cochanges.py`. Model it on `util/ad-hoc/2026-10-25_juniper_ml_0_11_1_cut_cochanges.py`.
      - It edits `docs/REFERENCE.md`:
        - the Version cell;
        - the Ecosystem Compatibility sentence (`:177`): "0.11.1 declares" becomes `<VER>`, and "the `0.11.x` row is `<VER>`'s". **Add** that 0.11.0 and 0.11.1 published `data>=0.17.0` / `cascor>=0.11.0`, keep 0.11.0's observability history, and extend "0.11.0 and 0.11.1 set them" to run through `<VER>`;
        - the `0.11.x` row: data `>=0.17.1`, cascor `>=0.12.0`. If the version is 0.12.0, add a new `0.12.x` row instead.
      - `--check` must exit 0.
      - Push with `python3 util/push_signed_commit.py --repo juniper-ml --branch release/juniper-ml-v<VER> --expected-head <proposal head> --add <tree>/docs/REFERENCE.md:docs/REFERENCE.md --add <tree>/util/ad-hoc/<script>:util/ad-hoc/<script> --message "…"`.
   9. **Pre-fill the notes.**
      - Run `util/ad-hoc/2026-09-12_ceremony_notes_preview.py --package juniper-ml --version <VER> --released-version 0.11.1 --release-date D --repo-root <proposal-head tree>`, redirected to `S/body.md`.
      - Then `util/ad-hoc/2026-10-10_fill_security_notes_placeholders.py --in S/body.md --out S/filled.md` with `--priority` (High, naming `[servers]` and `[all]`), `--severity Medium`, `--vuln-class` (CWE-201/755/770), `--advisory` and `--intro`. Never pass `--minor` for 0.11.2.
      - Model the texts on `notes/releases/RELEASE_NOTES_juniper-cascor_v0.12.0.md`, not `notes/releases/RELEASE_NOTES_v0.11.1.md`, which names `[tools]`.
      - The intro must say that the wheel ships no code, and that the data floor carries no security change for `[servers]`.
   10. **Merge** with `python3 util/safe_merge.py --pr <N> --execute`. Confirm its `MERGED` line; exit 0 does not mean merged. **Then set M** from `gh pr view <N> --repo pcalnon/juniper-ml --json mergeCommit --jq .mergeCommit.oid`. The `MERGED` line prints the PR *head*, not the merge commit.
   11. **Check M from a detached checkout of it.** Run steps 11–16 from that tree; `detect.py` and `ceremony.py` read it.
       - `grep -c '^## \[<VER>\]' CHANGELOG.md` must be 1, and `[Unreleased]` must be empty.
       - Every commit in `git log v0.11.1..M -- CHANGELOG.md` must have its entry inside `[<VER>]`. Docs-only commits carry no entry.
       - Re-run the step 9 preview there with D and `cmp` it against `S/body.md`; re-fill if they differ.
   12. **Wait for CI.** Find the run with `gh run list --repo pcalnon/juniper-ml --workflow ci.yml --commit M`, then `gh run watch <id> --exit-status`.
   13. **Re-detect** into `S/manifest-post.json`. It must show `BUMPED_NOT_RELEASED` with `<VER>` declared.
   14. **Dry run:** `python3 util/release_train/ceremony.py --manifest S/manifest-post.json --package juniper-ml --target-sha M --release-date D --dry-run`. It must plan with no HALT.
   15. **Cut:** step 14's command with `--dry-run` **replaced by** `--execute --monitor-timeout 30`. It returns IN_PROGRESS.
       - Confirm the Release, the archive PR and the publish run.
       - Immediately push `S/filled.md` to `release-notes/juniper-ml-v<VER>` as `notes/releases/RELEASE_NOTES_v<VER>.md`, with `push_signed_commit.py --repo juniper-ml --branch release-notes/juniper-ml-v<VER> --expected-head <archive head> --add S/filled.md:notes/releases/RELEASE_NOTES_v<VER>.md --message "…"`.
       - Run `gh release edit v<VER> --notes-file S/filled.md`, then `diff -B` the live body against the file.
   16. **Monitor.** Re-run with `--execute` and the default `--monitor-timeout` of 900 s, until it prints `state=PENDING_PYPI_APPROVAL`.
       - Check by hand that `pending_deployments` lists `pypi` and that `Publish to TestPyPI` is completed/success.
       - Report the run URL and two dates from its `created_at`: +30 days and +35 days.
       - Remove the step 8 and step 11 worktrees. **Stop.**
2. **Record the cut** in `notes/JUNIPER_2026-10-03_…DEVELOPMENT-PLAN.md`, using `util/ad-hoc/2026-10-25_plan_v1_7_17_juniper_ml_0_11_1_published.py`'s pattern. Anchor on the last revision row.
3. **After `<VER>` publishes:**
   - update the parent `Juniper/AGENTS.md` RELEASED paragraph. It is unversioned and exists on this host only.
   - tell the "draft PRs" session; #2333 waits on `/pypi/juniper-ml/<VER>/json`.
4. **The owner's items.** Surface them; do not act on them.
   - recurrence-client 0.3.1 (recurrence#221), and `embargo_days`;
   - data 0.17.2, R-DATA-2, which carries W5.7, a default change;
   - config-tools 0.2.0: backfill its `[Unreleased]` first;
   - W0.1's service-core half;
   - `notes/JUNIPER_2026-10-04_…CONSOLIDATED-DEVELOPMENT-PLAN.md` §6 A1 and A9, and the fix-forwards R-OBS-SC-2 and R-DATA-2;
   - #2330's option, which is [42fe25]'s successor's to drive.
5. **Follow-ups:**
   - the first live run of `save_model`'s snapshot path;
   - canopy#735–#738 and #751;
   - deploy#250;
   - runner-side `ARCHIVE_B64_MAX_DEFAULT`;
   - the false `succeeded` row `20261003T091414Z-4ba6`;
   - optionally, an E-H run with `--shared-equities-cache`.

## Rules that held this session

- **Re-probe before acting.** Four sessions touched this arc today. Check `gh pr list` and ListAgents. Yield, then send findings by SendMessage to the `from=` address.
- **Use plain, single commands.** The worktree guard refuses `&&`, loops, `$VAR` operands, `git -C` into another repo and compound templates. Use Python heredocs.
- **H-22:** post script outputs, never service bodies or logs.
- **Run tools on a synced tree.** This session's own stale-tree `detect.py` run produced the wrong premise above.

## Verification commands for the new thread (run each alone)

```bash
git fetch origin
git merge-base --is-ancestor f823b0b7 origin/main     # exit 0: #2326 ([servers] floors) on main
git merge-base --is-ancestor c86a5e5e origin/main     # exit 0: #2328 (plan v1.7.17) on main
git show origin/main:pyproject.toml                   # [servers]: juniper-cascor>=0.12.0, juniper-data>=0.17.1
python3 -I -c "import json,urllib.request;print(json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-ml/json'))['info']['version'])"   # 0.11.1
gh release view v0.11.2 --repo pcalnon/juniper-ml     # "release not found"
git ls-remote --heads origin "release/juniper-ml-v*"  # empty, or someone is racing you: stop and ask
gh pr list --repo pcalnon/juniper-ml --state open     # #2332, #2333 (draft) and others; no release/juniper-ml-* head
```

## Git state

- Worktree `.claude/worktrees/cuddly-knitting-stardust`, branch `worktree-cuddly-knitting-stardust`, at `2f96a051`. It is clean apart from this file, which is untracked and identical to the copy its docs PR lands.
- `main` has since moved: #2334 is `043c503b` and #2336 is `1257f181`.
- Everything landed through the API.

## Documents created or modified this session

- juniper-ml#2328: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.16 → v1.7.17) and `util/ad-hoc/2026-10-25_plan_v1_7_17_juniper_ml_0_11_1_published.py` (new).
- juniper-ml#2326, landed by "draft PRs": `util/ad-hoc/2026-10-25_raise_servers_floors_cascor_0_12_0_data_0_17_1.py`, which this session wrote.
- juniper-deploy#258: one comment.
- This file (new).
- Outside the repo: the auto-memory files `project_recurrence_equities_p0_arc_2026-10-04.md`, `reference_diff_rq_wheels_skips_dist_info.md` (new) and `reference_verification_discipline_hub.md`, and the index `MEMORY.md`.
- Referenced:
  - the predecessor named above;
  - `notes/releases/RELEASE_NOTES_v0.11.1.md`, `notes/releases/RELEASE_NOTES_juniper-cascor_v0.12.0.md`;
  - `util/ad-hoc/2026-10-25_juniper_ml_0_11_1_cut_cochanges.py`;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_recurrence-equities-juniper-ml-0-11-0-cut-parked-at-pypi-gate-plan-v1-7-14.md`;
  - `HANDOFF_2026-10-25_recurrence-equities-2320-merged-plan-v1-15-1-2330-owner-decides.md` (#2336).

## Validation record

Two rounds, three lenses. Round 1 was an adversarial fact-checker and a procedure auditor; round 2 attacked the rewrite.

- **Round 1** found the train's 0.12.0, the missing `--manifest`, the lost sync, re-detect, dry-run and re-render steps, the carried-forward approval, and a modified plan file that made two checks vacuous.
- **Round 2** found:
  - the ruling's incomplete premise;
  - the merge commit for M taken from the wrong place;
  - an impossible commit check;
  - a dry run that `--execute` would not override;
  - a 30 s monitor that cannot reach the gate;
  - missing `push_signed_commit.py` and fill flags;
  - stale PR states.
- Every round-2 finding is applied here. **No round 3 ran on these corrections**, so treat this text with the same suspicion.
