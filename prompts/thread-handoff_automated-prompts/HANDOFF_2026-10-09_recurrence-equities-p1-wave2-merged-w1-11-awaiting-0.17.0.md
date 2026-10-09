# Thread Handoff — Recurrence × Equities: P1 wave 2 merged, W1.11 drafts waiting on juniper-data 0.17.0

- **Date**: 2026-10-09
- **Session**: "equities recurrence" (juniper-ml worktree `.claude/worktrees/proud-cuddling-wreath`)
- **Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-05_recurrence-equities-consensus-round2-p1-wave1-in-flight.md`
- **Plan**: `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (**v1.5.1**, in this handoff's PR; v1.5.0 = juniper-ml#2197 `bf8357f0`)

---

## Handoff goal

Continue the recurrence × equities arc from the plan `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md` (v1.5.1). **P1's code is complete.** What remains: finish W1.11 once juniper-data 0.17.0 is on PyPI; the 2c snapshots-dir reconciliation if canopy Lane B lands; then, once the owner rules or releases, P2 onward. The owner rulings and releases are the owner's.

### Completed this session (all merged 2026-10-08 unless stated)

- **W1.5 driver half**: juniper-ml#2195 → `2b80fef6`.
  - `dataset_create_timeout_seconds` (default 120; CLI > YAML > default; independent of `max_wall_seconds`; expiry → `timed_out`).
  - `X-Request-ID` on train; `expect_operation_id` on predict, skipped with a WARNING against 0.5.0.
  - `recurrence_up` exports `JUNIPER_RECURRENCE_JUNIPER_DATA_TIMEOUT_SECONDS`.
  - Runbook in `docs/REFERENCE.md`.
- **W1.5 canopy half + W1.7 display half**: juniper-canopy#732 → `394bb6f7`.
  - Success after a timeout requires three things: `requested_by` is canopy's, the operation is `train`, and `model_operation_id == operation_id` (`_classify_train_outcome`).
  - The version is fetched in the background at startup and on selection.
- **W1.2 (R7's recommended default, applied pending ruling)**: juniper-canopy#733 → `85900074`.
  - Schema snapshot in `dataset_schema.py`, pinned against a committed `GET /v1/generators` copy.
  - "Edited" means the value differs from what the form displayed.
  - The preview is served by `POST /api/recurrence/effective_request`.
- **W1.11 canopy comment half**: juniper-canopy#734 → `4f69524b` (comments only).
- **W1.11 code half, DRAFTS (slip rule)**, all required checks green:
  - juniper-deploy#243: Compose data pins + Helm `data.image.tag` → 0.17.0.
  - juniper-deploy#245: the canopy → recurrence → juniper-data smoke. 3 passed against data built from `main` `462da218` with the other images published, by GHCR digest. Against 0.16.0 it fails clearly on the label.
  - juniper-ml#2190: `[servers]` floor `juniper-data>=0.17.0`.
- **Plan v1.5.0 / v1.5.1**:
  - Status rows, R7 in "Applied pending ruling", the progress paragraph and change log.
  - **Corrections by measurement**: canopy does NOT refuse recurrence + `equities_seq` under data 0.16.0. The gate reads canopy's own `DATASET_TYPES`, and `/api/train/start` checks none; the #245 run never reached the gate, so this conclusion rests on the code. juniper-data silently drops unknown params (F-C3, no 422).
  - The 2026-10-03 consensus record (`notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-PLAN-CONSENSUS-VALIDATION.md` §4.1) carries a dated correction.
- **Memory**: `project_recurrence_equities_p0_arc_2026-10-04.md` has a 2026-10-08 section, and its MEMORY.md line is updated.

### Remaining work (in order)

1. **W1.11 finish (after the owner approves the PyPI publish).**
   - The juniper-data `v0.17.0` Release was cut 2026-10-08 23:48Z and its GHCR image published. PyPI publish run `37861468866` awaits approval; PyPI served 0.16.0 at handoff.
   - Once PyPI serves 0.17.0, verify it: PyPI JSON plus a wheel probe per `util/ad-hoc/2026-09-10_verify_published_wheels.py` showing `equities_seq` `regression` / 6.0.0. Also check GHCR `tags/list`.
   - Then for each draft: record the image checks in #243's CHANGELOG, run the resolver pre-flight for #2190, and run #245's smoke with `--published`.
   - Mark the three PRs ready and merge with `safe_merge.py`, **only with a merge approval granted in that session**.
   - Update the plan's W1.11 row and the M1 note.
2. **W1.13 release train** (owner): recurrence 0.6.0, model 0.4.0, data-client 0.6.0, canopy 0.9.0 → remaining pins → re-run the smoke. Until recurrence 0.6.0 ships #192, neither canopy nor the driver can attribute an operation against the published 0.5.0.
3. **2c snapshots-dir clash**: canopy Lane B "2c" (`prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_canopy-consolidated.md`) has not landed. `util/experiment_stack.bash` uses W1.10's `${RUN_DIR}/snapshots`, and `isolated_stack.bash` sets none. Whichever lands second reconciles.
4. **Follow-ups the agents flagged** (not yet filed):
   - The canopy restart modal still offers `n_samples` / `noise` for sequence datasets.
   - Flat `equities` on cascor has the F-C2 class.
   - CI doesn't notice juniper-data param drift against canopy's schema snapshot.
   - The suite's `per_run_timeout_seconds` isn't checked to cover dataset + wall budgets.
   - `save_model` via `POST /v1/model/snapshots` with `expect_operation_id`.
   - Gateway 502/504 aren't followed by canopy.
5. **Owner items** (unchanged; keep "Applied pending ruling" current):
   - Dates; confirm R1–R8 (R2, R3, R7 applied as recommended; R8 as its alternative); R5.
   - W5.8 (B) vs W5.11; W5.9 / W5.10.
   - F-P8 Major + the W5.7 guard; re-rate F-P4's severity.
   - W1.14.
   - The W0.1 service-core half (`JuniperCascor1` service-core 0.5.0; a live cascor on `:8202` imports it).

### Key context

- **Merge approvals do not carry over.** This session's approval was granted in this session only.
- **Mechanics that held**:
  - Five task-executors ran in parallel on disjoint files, in worktrees cut from `origin/main`.
  - `util/open_signed_pr.py`; `util/safe_merge.py --execute` (read the `MERGED` line); `gh api -X PUT …/update-branch` for a BEHIND PR.
  - The owner's armed auto-merge net sometimes wins the race, which is fine.
- **Worktree hook refusals**: loops, variables around git/gh, `git ... && python3 util/open_signed_pr.py` compounds. Run git and gh as single plain commands.
- **Host trap**: the local image tags `juniper-data:0.16.0`, `juniper-recurrence:0.5.0`, `juniper-canopy:0.8.1` and `juniper-cascor:0.11.0` are dev builds; run published images by GHCR digest. The image `juniper-data-w111:main-462da218` was left for re-running the slip-rule smoke.
- **A concurrent canopy session** (worktree `…f055-f058-f068-request-ack-pacer…`) was editing `dashboard_manager.py`; do not touch it.

## Verification commands

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git log --oneline -3 origin/main     # expect this handoff's PR above bf8357f0 (#2197)
gh pr view 2195 --repo pcalnon/juniper-ml --json state -q .state         # MERGED
gh pr view 732 --repo pcalnon/juniper-canopy --json state -q .state      # MERGED (also 733, 734)
gh pr list --repo pcalnon/juniper-deploy --state open --json number,isDraft   # 243, 245 drafts
gh pr view 2190 --repo pcalnon/juniper-ml --json isDraft -q .isDraft     # true
curl -s https://pypi.org/pypi/juniper-data/json | python3 -c 'import json,sys;print(json.load(sys.stdin)["info"]["version"])'   # 0.17.0 → start item 1
ls -d /home/pcalnon/Development/python/Juniper/worktrees/*w1-* 2>&1      # only the two deploy W1.11 worktrees
```

## Git status at handoff

- juniper-ml: worktree `proud-cuddling-wreath` on `main` at `bf8357f0`, plus this handoff's docs PR (plan v1.5.1, the consensus-record qualification, this file). Nothing else uncommitted.
- Worktrees left for the open drafts:
  - `worktrees/juniper-deploy--chore--pin-data-0.17.0--20261008-1754--a84af1fb`
  - `worktrees/juniper-deploy--test--w1-11-canopy-recurrence-smoke--20261008-1754--a84af1fb`
  - `juniper-ml/.claude/worktrees/agent-a0cc83f337e9b068d` (branch `chore/w1-11-servers-floor-juniper-data-0.17.0`, #2190)
- All merged PRs' worktrees and local branches have been removed.
