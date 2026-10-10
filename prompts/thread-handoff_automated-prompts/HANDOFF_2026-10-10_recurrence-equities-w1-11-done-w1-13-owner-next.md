# Thread Handoff — Recurrence × Equities: W1.11 done (juniper-data 0.17.0 deployed); W1.13 is the owner's next

- **Date**: 2026-10-10
- **Session**: "equities recurrence" (juniper-ml worktree `.claude/worktrees/synchronous-splashing-bird`)
- **Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-09_recurrence-equities-p1-wave2-merged-w1-11-awaiting-0.17.0.md`
- **Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (**v1.5.2**, in this handoff's PR)

---

## Handoff goal

Continue the recurrence × equities arc from the plan `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.5.2). **W1.11 is done, and P1's code is complete.** Everything left for M1 waits on the owner:

- W1.13's four publications, then the recurrence and canopy pins and a re-run of the smoke;
- W1.14 acceptance;
- the owner rulings.

The 2c snapshots-dir reconciliation waits on canopy Lane B.

### Completed this session (2026-10-10)

- **Verified the 0.17.0 publication, each check with a control.**
  - **The PyPI wheel**, uploaded 09:02Z by publish run `37861468866` (green). The new `util/ad-hoc/2026-10-10_verify_data_0_17_0_published_wheel.py`, run in a clean venv with `-I`, PASSES on 0.17.0:
    - `equities_seq` is 6.0.0 / `regression`;
    - `compute_shape_meta` nulls `n_classes`, while a `classification` control on the same arrays counts 2;
    - the `dataset_id` carries 6.0.0.

    It FAILS on 0.16.0, on the label.
  - **The GHCR image**, index `sha256:3ab1ef79…`:
    - multi-arch;
    - revision label `f13a83ee`, the `v0.17.0` tag's commit;
    - juniper-data's own `util/check_image_serves.py` exits 0, with `/v1/health` reporting 0.17.0;
    - no `juniper_data/tests/`;
    - the registry declares `equities_seq` 6.0.0 / `regression`.
- **juniper-deploy#243 merged** (`3ce86fb2`). Its CHANGELOG records the image checks (signed commit `53fdab46`). `verify_published_images.py --fail-on-stale` exits 0 on it and 1 (`STALE PIN`) on the 0.16.0 tree.
- **juniper-deploy#245 merged** (`8071fa45`). `scripts/test_canopy_recurrence_smoke.sh --published` passed **3/3** (6.14 s) with every pin run by its GHCR digest:

  | Service | Version | Digest |
  | --- | --- | --- |
  | juniper-data | 0.17.0 | `3ab1ef79` |
  | juniper-recurrence | 0.5.0 | `96242690` |
  | juniper-canopy | 0.8.1 | `544ffb87` |
  | juniper-cascor | 0.11.0 | `05b3bf06` |

  It ran on a local merge of the #243 and #245 heads, whose tree differs from the merged one only in `CHANGELOG.md`. The teardown left nothing behind.
- **juniper-ml#2190 merged** (`cad7f613`, 11:30Z): the `[servers]` / `[all]` floor is `juniper-data>=0.17.0`.
  - Pre-flight against real PyPI: 61 packages on Python 3.12, 3.13 and 3.14. `[all]` resolves in 96 packages alongside recurrence 0.5.0.
  - Follow-up commits:
    - `d0c4fa88`: the CHANGELOG entry says "pre-flighted" instead of "held", it narrows the 5.0.0 claim (0.14.0 was 3.0.0), and it adds the wheel probe;
    - `c6792a29`: AGENTS.md `Last Updated`, re-bumped after the update-branch merge.
- **Plan v1.5.2** (this PR). W1.11 is Done. Updated: F-P4, F-DEP1, §1, Success Metrics, M1, and the dependency and risk rows. Executive summary item 4's stale "canopy's gate refuses" is corrected; it had survived the 2026-10-08 correction. Two table repairs.
- **Cleanup**: both deploy W1.11 worktrees and the temporary combined-smoke worktree were removed, and their branches are gone locally and on the remote.

### Remaining work (in order)

1. **W1.13 release train (owner).**
   - Order: data-client 0.6.0 → model 0.4.0 → recurrence 0.6.0 → canopy 0.9.0. PyPI on 2026-10-10 serves 0.5.0 / 0.3.0 / 0.5.0 / 0.8.1. The preconditions are met.
   - **Before recurrence 0.6.0**, raise its `[bench]` / `[bench-equities]` cap of `juniper-data<0.17.0` (`juniper-recurrence/pyproject.toml:97,106`).
   - Then move the recurrence and canopy Compose pins, and re-run `bash scripts/test_canopy_recurrence_smoke.sh --published` in juniper-deploy.
   - Until recurrence 0.6.0 ships #192, neither canopy nor the driver can attribute an operation.
2. **The 2c snapshots-dir clash.** Still not landed on 2026-10-10:
   - neither canopy `main` nor `util/isolated_stack.bash` sets `JUNIPER_RECURRENCE_SNAPSHOTS_DIR`;
   - `util/experiment_stack.bash` sets it to `${RUN_DIR}/snapshots`.

   Whichever lands second reconciles.
3. **Follow-ups (not yet filed)**:
   - the canopy restart modal still offers `n_samples` / `noise` for sequence datasets;
   - flat `equities` on cascor has the F-C2 class;
   - CI does not notice juniper-data param drift against canopy's schema snapshot;
   - the suite's `per_run_timeout_seconds` is not checked to cover the dataset and wall budgets;
   - `save_model` via `POST /v1/model/snapshots` with `expect_operation_id`;
   - canopy does not follow gateway 502 / 504;
   - recurrence's `[bench]` cap (item 1).
4. **Owner items** (unchanged; keep "Applied pending ruling" current):
   - dates;
   - R1–R8 confirmation (R2, R3 and R7 applied as recommended; R8 as its alternative), and R5;
   - W5.8 (B) vs W5.11; W5.9 / W5.10;
   - F-P8 Major + the W5.7 guard; re-rating F-P4's severity;
   - W1.14;
   - the W0.1 service-core half.

### Key context

- **Merge approvals do not carry over.** This session's approval covered the three W1.11 PRs and this docs PR.
- **Mechanics that held**:
  - `gh api -X PUT …/update-branch -f expected_head_sha=<full sha>` BEFORE a signed follow-up commit, so CI runs once, on the final head;
  - `util/push_signed_commit.py --expected-head`;
  - `gh pr ready` **works** on gh 2.46. Only `gh pr edit` is broken; set bodies with `gh api -X PATCH --input <json>`;
  - `util/safe_merge.py --execute`: read the `MERGED` line. It syncs a BEHIND PR itself, but only three times;
  - **when `main` outruns CI**, use the contended-lane fallback. safe_merge REFUSED #2190 ("went BEHIND 3 times") while `main` took four merges in 40 minutes, and disarmed its net. What landed it was `gh pr merge <N> --squash --auto --match-head-commit <full sha>`, checked to read `state=OPEN armed=true`, then `util/ad-hoc/2026-09-23_converge_pr_through_moving_main.py --pr <N>` in the background. That needed one update-branch, and the net merged on the next green.
- **Trap met.** An update-branch merge can drop a PR's `**Last Updated**` bump out of its diff when `main` carries the same date. `Verify AGENTS.md Last Updated` then fails; the fix is to bump to today's UTC date.
- **Trap avoided.** A floor pre-flight over `[servers]` alone does not cover `[all]`. Recurrence pins juniper-data in its `bench` extras, so `[all]` was resolved separately (96 packages, clean).
- **Worktree hook.** It refuses:
  - `git -C` into this repo's other worktrees;
  - git / gh commands built from variables or compounds;
  - `docker run … sh`;
  - `python3 -` fed from a pipe.

  Use plain single commands. `git -C` into OTHER repos is allowed.
- **Host.** The published images are now present locally by digest. The local `juniper-*:<release>` tags are still dev builds, so use `--published`.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git log --oneline -3 origin/main                                          # this handoff's PR on top
gh pr view 2190 --repo pcalnon/juniper-ml --json state -q .state          # MERGED
gh pr view 243 --repo pcalnon/juniper-deploy --json state -q .state       # MERGED (and 245)
git -C ../juniper-deploy show origin/main:docker-compose.yml | grep -c 'juniper-data:0.17.0'   # 2
curl -s https://pypi.org/pypi/juniper-recurrence/json | python3 -c 'import json,sys;print(json.load(sys.stdin)["info"]["version"])'   # 0.6.0 means W1.13 has started
```

## Git status at handoff

- juniper-ml: worktree `synchronous-splashing-bird`, holding this handoff's docs PR (plan v1.5.2, this file). Nothing else is uncommitted.
- No W1.11 worktree or branch remains in juniper-deploy or juniper-ml.
