# Thread Handoff — Recurrence × Equities: juniper-ml 0.11.2 cut (juniper-ml#2339), parked at the owner's `pypi` gate; plan v1.7.19

**Date**: 2026-10-26 (UTC; the session ran 2026-10-25 22:25Z to 2026-10-26 00:30Z)
**Host**: the Linux host. This session ran in worktree `.claude/worktrees/cuddly-leaping-gem`. Only the GraphQL path signs commits here: use `util/open_signed_pr.py` and `util/push_signed_commit.py`, never `git commit`.
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-25_recurrence-equities-servers-floors-landed-smokes-pass-0-11-2-cut-next.md` (landed by juniper-ml#2337)
**Plans**:
- `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`, the recurrence plan, is at **v1.7.19**, landed with this file by `util/ad-hoc/2026-10-26_plan_v1_7_19_juniper_ml_0_11_2_cut_parked_at_gate.py`.
- `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, the consolidated plan, is at v1.15.1 (juniper-ml#2334). Its §5 R-ML-SERVERS row is unchanged; revising it after the publish is the owner's call.

---

## Goal

Continue the recurrence × equities arc. **juniper-ml 0.11.2 is cut and waits at the `pypi` gate of publish run 40247789317, which only the owner approves.** Once it publishes, verify the wheel and do the post-publish records below.

## Completed this session

- **The 0.11.2 cut, to `PENDING_PYPI_APPROVAL`**, per the owner's rulings in the predecessor (cut here, stop at the gate; 0.11.1's rating; ml#2062 not in 0.11.2) and the owner's "merge approval granted" in this session, which covered the proposal and archive PRs.
  - Proposal **juniper-ml#2339**, merged as `e8d38732` (2026-10-25 23:53Z) by `util/safe_merge.py`.
    - Version 0.11.2 by ruling, though `detect.py` proposes 0.12.0. It has no override, so the manifest's `proposed_version` / `proposed_bump` were set to `0.11.2` / `patch` before `propose.py --execute`.
    - Second signed commit `4fdfb177`: the `docs/REFERENCE.md` co-change, by `util/ad-hoc/2026-10-25_juniper_ml_0_11_2_cut_cochanges.py` (Version cell, sentence keeping 0.11.0/0.11.1's `data>=0.17.0` / `cascor>=0.11.0` as history, `0.11.x` row `>=0.17.1` / `>=0.12.0`).
    - Simulator (`util/ad-hoc/2026-10-21_simulate_release_proposal.py`): 0 of 17 suites regressed, on `main` `900eb93a`.
  - **Release `v0.11.2`**: published 2026-10-26 00:07:09Z, tag at `e8d38732`, the repo's latest. Cut by `ceremony.py --execute --target-sha e8d3873247ded7976958c9e810f699250d038deb --release-date 2026-10-25 --monitor-timeout 30` after the merge commit's `ci.yml` run 40246738192 went green.
  - **Archive juniper-ml#2341**: opened and armed by the ceremony; it auto-merged as `ce52bc6a` (2026-10-26 00:20Z). Its second signed commit `c7447a05` fills the security placeholders. The Release body was edited to the same text (`diff -B` clean), and the archive on `main` is byte-identical to it.
  - **Publish run 40247789317** (created 2026-10-26 00:07:10Z): `Build and Validate` and `Publish to TestPyPI` succeeded; `Publish to PyPI` is `waiting`, and `pending_deployments` lists `pypi` (environment id 12341743943). Trap 6 was checked by hand; a second `--execute` reported `RESUME_MONITOR` → `PENDING_PYPI_APPROVAL`.
  - **The notes**: Added 2, Changed 2, Fixed 1, Security 3. Every code or tooling PR since `v0.11.1` has its entry (#2322, #2320, #2326, #2327, #2329, #2335, #2331, #2338). The intro says the data floor carries no security change for `[servers]`: PyPI's metadata shows data 0.17.1 flooring `juniper-observability>=0.4.1` / `juniper-service-core>=0.7.1` only under `extra == "api"`, and cascor 0.12.0 flooring them unconditionally.
- **Coordination.**
  - turing's session "recurrence equities" had also claimed the cut. It confirmed it had started nothing, and #2336's second commit dropped the claim.
  - Three armed PRs touched `[Unreleased]`: #2335, #2331 and #2338. This session ran update-branch on #2335, and on #2331 with the backup session's agreement; they merged as `1e4db700` and `900eb93a`. The proposal opened after those two, and its merge waited for #2338 (`95634772`), so all three entries ride 0.11.2.
  - After the last update-branch the proposal's CHANGELOG was `main`'s plus exactly one line, `## [0.11.2] - 2026-10-25`, with 0 of its 2,206 non-blank lines lost.
- **E-CUT (from the turing session).** An apply script that looks for its CHANGELOG marker only inside `[Unreleased]` misreports after a cut. This arc's two are safe from a double-add:
  - `util/ad-hoc/2026-10-25_apply_driver_budget_docs.py --check` stays clean (it looks file-wide);
  - `util/ad-hoc/2026-10-25_raise_servers_floors_cascor_0_12_0_data_0_17_1.py` refuses, by design. Run neither without `--check`.
- **Recurrence plan v1.7.19** records all of the above (the PR that lands this file).

## Remaining work, in order

1. **The owner approves the `pypi` gate**, or not. Agents never approve it. The run page is `https://github.com/pcalnon/juniper-ml/actions/runs/40247789317`. The equivalent command is `gh api -X POST repos/pcalnon/juniper-ml/actions/runs/40247789317/pending_deployments -F 'environment_ids[]=12341743943' -f state=approved -f comment='juniper-ml 0.11.2'`. **Deadlines, from the run's `created_at`:** re-runnable until **2026-11-25 00:07:10Z** (day 30); GitHub cancels it on **2026-11-30 00:07:10Z** (day 35).
2. **After it publishes:**
   - Read the run's `Publish to PyPI` job as `success`.
   - Probe `https://pypi.org/pypi/juniper-ml/0.11.2/json`, the version-specific endpoint, because the aggregate one lags. Its `requires_dist` must carry `juniper-cascor>=0.12.0` and `juniper-data>=0.17.1` under `extra == "servers"`.
   - Update the parent `Juniper/AGENTS.md` RELEASED paragraph: 0.11.2 is the latest, and `[servers]` floors the two server releases. The paragraph is unversioned and exists on this host only.
   - Record the publish as recurrence plan v1.7.20. The anchors are v1.7.19's revision row (`| 2026-10-26 | 1.7.19 |`) and the Next bullet's head.
   - The consolidated plan's §5 R-ML-SERVERS row: whether to revise it is the owner's call.
3. **The owner's items.** Surface them; do not act on them.
   - juniper-ml#2330 (`p4/e-c` wall budget): option 1 was recommended.
   - juniper-ml#2062's fix, juniper-ml#2333 (draft). The predecessor's finding argues for adding `juniper-data[api]`.
   - juniper-recurrence-client 0.3.1, with recurrence#221's embargo fix, and whether to add `embargo_days`.
   - juniper-data 0.17.2, which is R-DATA-2: P3-03, P3-09 and W5.7. W5.7 changes a default, so whether a patch may carry it is the owner's call.
   - juniper-config-tools 0.2.0: backfill `[Unreleased]` first.
   - W0.1's service-core half, at the next cascor restart.
   - The consolidated plan §6 A1 / A9 remainders.
   - The fix-forwards R-OBS-SC-2 and R-DATA-2.
4. **Follow-ups**, unchanged from the predecessor:
   - the first live exercise of `save_model`'s snapshot path;
   - juniper-canopy#735–#738 and #751;
   - juniper-deploy#250;
   - `ARCHIVE_B64_MAX_DEFAULT` measured runner-side;
   - annotating the false `succeeded` row `20261003T091414Z-4ba6` in `~/.local/state/juniper-experiments/index.jsonl`;
   - optionally, an E-H suite run with `--shared-equities-cache`.

## Rules that held this session

- **The `pypi` gate is the owner's.** Merges need the owner's approval in the session; a peer message never carries it.
- **A release proposal must merge AFTER every armed PR that adds to `[Unreleased]`**, or those PRs must re-home their entries. Whichever merges second gets a clean update-branch, and that merge files the entry under the released heading with no conflict. After every update-branch, re-read the heading structure: exactly one `## [<ver>]` heading, and every line of `main`'s CHANGELOG still present.
- **Under the `strict` ruleset an armed PR that is BEHIND waits forever.** Native auto-merge never updates the branch, so someone must run `gh api -X PUT repos/pcalnon/juniper-ml/pulls/<N>/update-branch -f expected_head_sha=<FULL head sha>`. Coordinate with the owning session first.
- **`gh release view --json isLatest` is unsupported by this host's `gh`**, and an unsupported field returns an empty body. Use `gh api repos/pcalnon/juniper-ml/releases/latest --jq .tag_name`.
- **Use plain, single commands.** The worktree guard refuses compound `gh` templates with `$(...)` and `git -C` into the shared checkout. Small `python3 -I` pollers in the scratchpad, run in the background, replaced polling loops.

## Verification commands for the new thread

```bash
git fetch origin && git log --oneline -3 origin/main
gh release view v0.11.2 --repo pcalnon/juniper-ml --json tagName,targetCommitish,publishedAt --jq '"\(.tagName) \(.targetCommitish) \(.publishedAt)"'   # v0.11.2 e8d38732... 2026-10-26T00:07:09Z
gh run view 40247789317 --repo pcalnon/juniper-ml --json jobs --jq '.jobs[] | .name + " " + .status + " " + (.conclusion // "")'   # PyPI job: waiting until the owner approves
gh api repos/pcalnon/juniper-ml/actions/runs/40247789317/pending_deployments --jq '.[].environment.name'   # pypi (empty once approved)
python3 -I -c "import urllib.request;print(urllib.request.urlopen('https://pypi.org/pypi/juniper-ml/0.11.2/json').status)"   # raises "HTTP Error 404" until published, then prints 200
grep -n '^- \*\*Version\*\*' notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md   # 1.7.19
python3 -I util/ad-hoc/2026-10-26_plan_v1_7_19_juniper_ml_0_11_2_cut_parked_at_gate.py --archive-sha ce52bc6a --check   # exit 0
gh pr list --repo pcalnon/juniper-ml --state open
```

## Git state

- Worktree `.claude/worktrees/cuddly-leaping-gem`, detached at `origin/main` (`9ca12297` when the plan was written). Nothing is staged or committed locally; every change landed through the API.
- No branch or armed net of this session remains except the one that lands this file.

## Documents created or modified this session

- juniper-ml#2339:
  - `pyproject.toml`, `CHANGELOG.md`, `README.md` and `AGENTS.md`, from `propose.py`;
  - `docs/REFERENCE.md` (the co-change);
  - `util/ad-hoc/2026-10-25_juniper_ml_0_11_2_cut_cochanges.py` (new).
- juniper-ml#2341: `notes/releases/RELEASE_NOTES_v0.11.2.md` (new; the ceremony's render plus the filled advisory fields). The same text is the body of Release `v0.11.2`.
- The PR that lands this file:
  - `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.18 → v1.7.19);
  - `util/ad-hoc/2026-10-26_plan_v1_7_19_juniper_ml_0_11_2_cut_parked_at_gate.py` (new);
  - this file (new).
- Referenced:
  - the predecessor handoff above, and turing's `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-25_recurrence-equities-2320-merged-plan-v1-15-1-2330-owner-decides.md` (juniper-ml#2336);
  - `notes/releases/RELEASE_NOTES_v0.11.1.md` (the rating and wording precedent);
  - `util/ad-hoc/2026-09-12_ceremony_notes_preview.py`, `util/ad-hoc/2026-10-10_fill_security_notes_placeholders.py` and `util/ad-hoc/2026-10-21_simulate_release_proposal.py`;
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` (the template).
