# Thread Handoff — Recurrence × Equities: save_model saves the scored model (juniper-ml#2211, #2316); #2313's re-check passed; plan v1.7.16

**Date**: 2026-10-24
**Host**: turing (Darwin, Intel x86_64; no commit signing; bash 3.2). Every landing goes through `util/open_signed_pr.py` / `util/push_signed_commit.py` / `util/ad-hoc/2026-10-17_push_signed_with_retry.py`.
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_recurrence-equities-juniper-ml-0-11-0-published-plan-v1-7-15.md` (juniper-ml#2312)
**Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` at **v1.7.16** (this session, via `util/ad-hoc/2026-10-24_plan_v1_7_16_save_model_snapshot.py --recheck-sha f694a450 --save-pr 2316 --save-sha b585cdaf`)

---

## Goal

Continue the arc from plan v1.7.16. **This session** (turing session 10, "generic-hugging-hamster" `[08bf3d]`, merge approval granted at its start) took the predecessor's items 1 and 2. It is the same session that landed juniper-ml#2313 on 2026-10-21, which the predecessor records.

- **Item 1, the post-merge re-check of juniper-ml#2313, passed** on `main` `f694a450` (2026-10-24, three days and six merges later): `git show origin/main:CHANGELOG.md | grep -c "The release-train proposal now moves README"` prints 1 and the `set_readme_compat_version` grep prints 2.
- **Item 2, juniper-ml#2211, landed as juniper-ml#2316** (merged as `b585cdaf`). `save_model` in `util/experiments/run_experiment.py` now saves the model the run scored instead of fitting a second one:
  - **The call.** When `POST /v1/train` returned an `operation_id`, `_save_model_snapshot` posts `POST /v1/model/snapshots` with it as `expect_operation_id` and `description: "run_experiment <run_id>"`. The contract was read from the published `juniper-recurrence-v0.8.0` tag (`routers/snapshots.py`, `schemas.py`, `routers/_common.py`): 201 with `{id, created, size_bytes, description, meta}`; 409 when no model is held (string detail) or when the id names another operation (`{message, expected_operation_id, model_operation_id}`); `expect_operation_id` has `min_length=1`.
  - **The copy.** `_snapshots_dir` is `ports.json` `recurrence_launch.snapshots_dir` when the launcher recorded one for this service, else `$RUN_DIR/snapshots`. The driver copies `<dir>/<id>.npz` to `artifacts/results/model.npz`, requires its size to equal `size_bytes`, and records the `sha256`.
  - **Failure modes.** A 409 fails the phase (`degraded`, exit 1) and nothing re-fits a substitute. An id that does not match the service's own `[A-Za-z0-9][A-Za-z0-9_-]{0,63}` never becomes a path. A size mismatch or a copy error fails the phase and removes the unvouched copy. A snapshot the run cannot read (another host, or a staged `service: snapshots_dir` that outranks the recorded env value) is `ok` with `model_path: null` and a `note`, and a stale `model.npz` is not claimed.
  - **The fallback.** Only a train response without an `operation_id` (a pre-W1.5 service) still takes the W1.9 CLI re-fit, unchanged, including the pinned wording `save_model re-run failed: ...`.
  - **The manifest.** The new `manifest.save_model` block names the path (`source`: `snapshot` or `refit`). `save_model_rerun` keeps the re-fit's evidence and is `null` on the snapshot path. `manifest.operation` is unchanged: `test_the_train_id_rides_back_on_predict_and_nowhere_else` pins its exact shape.
  - **Tests.** Eight `SaveModelSnapshotTest` cases in `tests/test_recurrence_operation_identity_and_dataset_budget.py`; the stub gains a 0.8.0-shaped `/v1/model/snapshots`, and the CLI re-fit is patched to fail any case where it runs except the fallback. All eight fail against the old driver (6 assertions, 2 errors); the file's 24 older cases pass on both.
  - **Docs.** The module docstring, `docs/REFERENCE.md` (driver section; "Recurrence launch record and service env" with a `save: .save_model` `jq` field and four "What you see" rows; the W1.5 suite entry), `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, `docs/QUICK_START.md`, `docs/DOCUMENTATION_OVERVIEW.md` and `CHANGELOG.md` were written by `util/ad-hoc/2026-10-24_apply_save_model_snapshot_docs.py` (idempotent) on fresh `origin/main` copies.
- **Plan v1.7.16** changes the Status line, the Progress block (a session 10 bullet; Next rewritten) and the revision row. It lands in one PR with this handoff and its script.

## Remaining work, in order

1. **Re-check #2316 after merge**, about an hour after it landed, per memory `api-whole-file-uploads-rebase-on-main`. Each should print ≥ 1:
   - `git show origin/main:CHANGELOG.md | grep -c "saves the recurrence model the run scored"`
   - `git show origin/main:docs/REFERENCE.md | grep -c "Since juniper-ml#2211 the driver"`
   - `git show origin/main:util/experiments/run_experiment.py | grep -c "_save_model_snapshot"`

   A reverted docs or CHANGELOG edit costs one re-run of `util/ad-hoc/2026-10-24_apply_save_model_snapshot_docs.py --root <fresh main copy>`.
2. **juniper-ml#2210 (recommended next agent task).** `per_run_timeout_seconds` is checked against `max_wall_seconds` only. Compute each cell's worst-case driver budget (the dataset budget + the health waits + `max_wall` per HTTP phase + `save_model`) and refuse at `load_suite`, or derive the subprocess timeout from it; the issue has the full budget table. **The `save_model` term changed with #2316**: on the snapshot path it is one `POST /v1/model/snapshots` bounded by `max_wall` (the copy is local), and the 600 s CLI re-fit (`_save_model_rerun`'s `timeout=600`) applies only to a service that returns no `operation_id`. Since the driver cannot know which path a cell will take before the train responds, the worst case is still the re-fit's 600 s unless the suite pins a ≥ 0.6.0 service; say which rule you pick in the PR.
3. **Owner** (carried):
   - the parent `Juniper/AGENTS.md` RELEASED paragraph (juniper-ml 0.11.0, recurrence 0.8.0, model 0.6.0); that file is not on turing;
   - the juniper-recurrence-client 0.3.1 release (juniper-recurrence#221's embargo fix), and whether to add `embargo_days`;
   - juniper-config-tools 0.2.0 for the typing marker, or leave it: backfill its empty `[Unreleased]`, then preflight with `python3 util/ad-hoc/2026-10-21_simulate_release_proposal.py --package juniper-config-tools --from-version 0.1.0 --to-version 0.2.0 --sim-dir <scratch>/sim`;
   - the W0.1 service-core half; juniper-data's next release carrying W5.7;
   - refreshing the juniper-recurrence and juniper-data checkouts (`! git -C /Users/pcalnon/Development/python/Juniper/juniper-recurrence pull --ff-only`, likewise juniper-data).
4. **Follow-ups** (carried, plus one):
   - **new:** the first live exercise of the snapshot path. On the next real recurrence run with `outputs.save_model: true`, check `jq '{phase: .phases.save_model, save: .save_model}' "$RUN_DIR/manifest.json"`: `source` should be `snapshot`, `model_path` set and `sha256` equal to `shasum -a 256 "$RUN_DIR/artifacts/results/model.npz"`;
   - the W1.12 / W1.11 smokes on the 0.8.0 image, on a host whose Docker reaches GHCR;
   - juniper-canopy#735–738 and #751, and juniper-deploy#250;
   - the `ARCHIVE_B64_MAX_DEFAULT` runner-side measurement in `util/release_train/ceremony.py`;
   - optional: a first real run of the E-H suite with `--shared-equities-cache`.

## Landing rules learned this session

- **Do not run two heavy suite sets at once when attributing failures.** The pristine-export diff (memory `turing-juniper-ml-darwin-test-failures`) showed one extra name, `PreemptArmsTest.test_409_from_an_active_run_is_preempted_and_retried`, only because the change's run overlapped the pristine run; it passes 5 of 5 alone on both trees. Run the two sets one after the other, and re-run any lone extra name in isolation before blaming the change.
- **The snapshot route answers 201, not 200.** `_run_recurrence`'s `_aux_phase` accepts only 200, which is why `save_model` has its own helper; reuse `_aux_phase` only for routes that answer 200.
- **`util/ad-hoc/2026-10-17_push_signed_with_retry.py` takes one `--message` per `--file`**, in order; one `--message` for three files is a usage error (exit 2) before anything is pushed. `docs/REFERENCE.md` (1,051,316 B) landed on attempt 1 on 2026-10-24.
- **A handoff you are handed may be superseded** (memory `duplicate-handoff-pickup`, updated this session): `ls -t prompts/thread-handoff_automated-prompts/` before starting, and check `gh pr list` for the task right before landing.
- Everything else is as in the predecessor: the `pypi` gate is the owner's; one plain command per call under the worktree guard; build every whole-file upload from a fresh `origin/main` copy; `util/safe_merge.py` without `--timeout`.

## Verification commands for the new thread

```bash
grep -n '^- \*\*Version\*\*' notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md   # 1.7.16 (or later)
python3 -I util/ad-hoc/2026-10-24_plan_v1_7_16_save_model_snapshot.py --recheck-sha f694a450 --save-pr 2316 --save-sha b585cdaf --check   # every edit "already applied", exit 0
gh pr view 2316 --repo pcalnon/juniper-ml --json state,mergeCommit -q '.state + " " + (.mergeCommit.oid // "-")'   # MERGED b585cdaf...
python3 -I util/ad-hoc/2026-10-24_apply_save_model_snapshot_docs.py --check   # every edit "already applied", exit 0 (on a tree at main)
python3 -B -m unittest tests/test_recurrence_operation_identity_and_dataset_budget.py   # 32 OK
gh issue view 2210 --repo pcalnon/juniper-ml --json state -q .state   # OPEN: the recommended next agent task (Remaining work, item 2)
```

## Git state

- Worktree `/Users/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/generic-hugging-hamster` on branch `worktree-generic-hugging-hamster`. Nothing is committed locally; every change landed through the API. Once the plan PR merges, the worktree's changes are all on `origin/main`, and `git checkout -- . && git clean -fd` on it is safe.
- The juniper-recurrence and juniper-data checkouts are untouched. The 0.8.0 contract was read from GitHub at tag `juniper-recurrence-v0.8.0`.

## Documents created or modified this session

- juniper-ml#2316: `util/experiments/run_experiment.py`, `tests/test_recurrence_operation_identity_and_dataset_budget.py`, `util/ad-hoc/2026-10-24_apply_save_model_snapshot_docs.py` (new), `docs/REFERENCE.md`, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, `docs/QUICK_START.md`, `docs/DOCUMENTATION_OVERVIEW.md`, `CHANGELOG.md`
- The plan PR: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.7.15 → v1.7.16), this file (new), `util/ad-hoc/2026-10-24_plan_v1_7_16_save_model_snapshot.py` (new)
- Earlier in this session (2026-10-21, recorded by the predecessor): juniper-ml#2313 (`util/release_train/propose.py`, `tests/test_release_train_propose.py`, `util/ad-hoc/2026-10-21_simulate_release_proposal.py`, `util/ad-hoc/2026-10-21_apply_propose_readme_compat_changelog.py`, `CHANGELOG.md`)
- Referenced:
  - the predecessor handoff above, and `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_recurrence-equities-release-train-sees-pins-client-embargo-fixed-plan-v1-7-13.md` (the handoff the session was started on, superseded);
  - `util/ad-hoc/2026-10-21_plan_v1_7_15_juniper_ml_0_11_0_published.py` (the revision script this follows);
  - `util/experiment_stack.bash` (`recurrence_launch.snapshots_dir`, the YAML-over-env precedence note);
  - `tests/test_run_experiment.py`, `tests/test_save_model_recorded_cli_contract.py`, `tests/test_recurrence_launch_record_edges.py`, `tests/test_recurrence_aux_timeout_and_exit.py` (the re-fit's suites, unchanged and green apart from the documented macOS set).
