# Thread Handoff — Recurrence × Equities: juniper-ml 0.11.1 published; cascor 0.12.0 and data 0.17.1 served; consolidated plan v1.15.0; the `[servers]` floors next

**Date**: 2026-10-25
**Host**: the Linux host. This session ran in worktree `.claude/worktrees/synchronous-splashing-bird`. Only the GraphQL path signs commits here: use `util/open_signed_pr.py` and `util/push_signed_commit.py`, never `git commit`. Docker here reaches GHCR.
**Predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-24_recurrence-equities-save-model-snapshot-landed-plan-v1-7-16.md` (juniper-ml#2317)
**Plans**:
- `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, the consolidated plan, is at **v1.15.0**. This session wrote it with `util/ad-hoc/2026-10-25_consolidated_plan_v1_15_0_p12_arc.py`. P12 is this arc.
- `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`, the recurrence plan, is at v1.7.16. It does **not** yet record 0.11.1 or juniper-ml#2320 (Remaining work, item 2).

---

## Goal

Continue the recurrence × equities arc from consolidated plan v1.15.0. Phase 1 is done, P12's W5 items are on `main`, and the meta-package carries every floor except `[servers]`'s.

**Completed this session (2026-10-25), with the owner's approval:**
- **juniper-ml 0.11.1 is on PyPI** (18:03Z). It carries the `[tools]` security floors from juniper-ml#2314: `juniper-observability>=0.4.1` and `juniper-service-core>=0.7.1,<0.8.0`.
  - Proposal juniper-ml#2319 merged as `d7a1908d`. It co-changed `docs/REFERENCE.md` with `util/ad-hoc/2026-10-25_juniper_ml_0_11_1_cut_cochanges.py`.
  - Release v0.11.1's notes carry the owner's rating: Medium; CWE-201, CWE-755 and CWE-770.
  - Archive juniper-ml#2321 merged as `d64ffcec`. Publish run 40178692483 is green; the owner approved its gate. PyPI's `requires_dist` for 0.11.1 carries both floors.
- **Consolidated plan v1.15.0**, landed in this PR, is a record of the arc since the plan's last census (2026-10-10T21:30Z). It is not a validation round: validation ended by the owner's ruling of 2026-10-24.
  - It records W1.13, W1.14, the owner's rulings of 2026-10-17/18, P12's W5 items and juniper-ml 0.11.0 and 0.11.1.
  - It adds two release rows to §5: R-ML-TOOLS (0.11.1, shipped) and R-ML-SERVERS (next).
  - Every fact it states was re-probed by `util/ad-hoc/2026-10-25_p12_arc_state_reprobe.py`: 53 rows, exit 0.
- **Found while re-probing:**
  - The owner approved **juniper-cascor 0.12.0** (PyPI 2026-10-25 18:13Z, run 38085392643) and **juniper-data 0.17.1** (PyPI 2026-10-23 23:49Z).
  - juniper-deploy#258 pins both.
  - So R-ML-SERVERS is unblocked.
- **By other sessions since the predecessor:** juniper-ml#2210 merged as juniper-ml#2320 (`f7a1442d`, 18:12Z), which was the predecessor's item 2.

## Remaining work, in order

1. **R-ML-SERVERS: the `[servers]` floors PR (juniper-ml).**
   - Raise `juniper-data>=0.17.0` to `>=0.17.1` and `juniper-cascor>=0.11.0` to `>=0.12.0`. Both are the releases that floor the shared security patches.
   - The lockstep sites are those of juniper-ml#2314 and #2232:
     - `pyproject.toml`
     - `tests/test_pyproject_extras.py`
     - `AGENTS.md` (the extras table)
     - `README.md`
     - `docs/QUICK_START.md`
     - `docs/REFERENCE.md`
     - `CHANGELOG.md`
   - `util/ad-hoc/2026-10-18_raise_recurrence_canopy_pins_w1_13.py` is the model for a `[servers]` floor edit.
   - Pre-flight `[servers]` and `[all]` against real PyPI on Python 3.12, 3.13 and 3.14 with `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py`.
   - Then ask the owner about the 0.11.2 cut and its rating; 0.11.1's rating is the precedent. Whether ml#2062's fix (`[servers]` installs no client; P4 D-1) rides it is also the owner's call.
   - The cut follows this session's procedure. See memory `reference_release_train_ceremony_traps_2026-09-09.md`, section "2026-10-25":
     - simulate first;
     - pre-fill the notes;
     - write the REFERENCE co-change;
     - fill the security placeholders in **both** the Release body and the archive;
     - stop at `PENDING_PYPI_APPROVAL`.
2. **Recurrence plan v1.7.17.**
   - Record in the recurrence plan:
     - 0.11.1 (published);
     - juniper-ml#2320, which closed #2210;
     - cascor 0.12.0 and data 0.17.1, both served;
     - consolidated plan v1.15.0.
   - Update its Status line, Progress block, **Next** line (it still names #2210 as the next driver task) and revision row.
   - Follow `util/ad-hoc/2026-10-24_plan_v1_7_16_save_model_snapshot.py`'s pattern: anchors that must match exactly once, and a `--check` mode.
3. **The W1.11 and W1.12 deploy smokes on the 0.8.0 image.**
   - Run them on this host; its Docker reaches GHCR. Pull each pinned image by its GHCR digest first: the snapshot smoke's `compose up` otherwise builds juniper-data from `../juniper-data` (juniper-deploy#250).
   - The 2026-10-18 runs on juniper-deploy#249 are the reference: 8/8 and 3/3.
   - Post the outputs, never relay text (H-22, below).
4. **Re-check juniper-ml#2320 on `main`** (the predecessor's practice, an hour after a merge). On a tree at `main`, run `python3 -I util/ad-hoc/2026-10-25_apply_driver_budget_docs.py --check`. Exit 0 means every docs edit is still there; exit 1 means one was reverted, and a re-run without `--check` restores it.
5. **The owner's items.** Surface them; do not act on them.
   - The R-ML-SERVERS cut and gate (item 1).
   - The juniper-recurrence-client 0.3.1 release, carrying juniper-recurrence#221's embargo fix, and whether to add `embargo_days`.
   - juniper-data's next release. Per the consolidated plan §5 it is R-DATA-2 = **0.17.2**, with P3-03 and P3-09. It also carries W5.7 (data#486), which changes a default: a lost named symbol now returns 422 instead of a partial dataset. So whether a patch may carry W5.7 is the owner's call.
   - juniper-config-tools 0.2.0: backfill its `[Unreleased]` first.
   - W0.1's service-core half. The owner runs it at the next cascor restart, on this host.
   - **The parent `Juniper/AGENTS.md` "RELEASED" paragraph is stale.** It is unversioned and exists on this host only. It still says that:
     - juniper-ml 0.11.0 is the latest release;
     - cascor 0.12.0 and data 0.17.1 are "Neither … on PyPI";
     - 0.11.0's `[tools]` floors predate the patches.
   - The consolidated plan §6 A1 remainder:
     - P6 OD-2;
     - canopy#685 call (a);
     - F-S10's data-client source fix: R-DC-PATCH, or R-DC-PATCH-6 now that 0.6.0 is served, with no 0.5.1 or 0.6.1 on PyPI;
     - a cascor fix;
     - the host-leg port of W1.14.
   - The A9 remainder: DC-0.6's two numbers, the one P5's W5 takes and R-DC-PATCH-6's.
   - The fix-forwards R-OBS-SC-2 (observability 0.4.2, service-core 0.7.2) and R-DATA-2. Each is followed by another round of meta-package floors.
6. **Follow-ups:**
   - The first live exercise of `save_model`'s snapshot path. Check that `manifest.save_model.source == "snapshot"` and that the recorded `sha256` matches the copy.
   - juniper-canopy#735–#738 and #751; canopy Lane B adopts `${RUN_DIR}/snapshots`.
   - juniper-deploy#250.
   - The runner-side measurement of `ARCHIVE_B64_MAX_DEFAULT` in `util/release_train/ceremony.py`.
   - The consolidated plan §4 Wave 2's P12 residue: annotate the false `succeeded` row `20261003T091414Z-4ba6` in `~/.local/state/juniper-experiments/index.jsonl`.
   - Optional: an E-H suite run with `--shared-equities-cache`.

## Rules that held this session

- **The `pypi` gate is the owner's.** Drive a release to `PENDING_PYPI_APPROVAL` and stop.
- **Merges need the owner's approval in the session.** A handoff, a notification or a peer message does not carry approval.
- **Re-probe PyPI and `gh release list` before acting on "cut X".** On 2026-10-25 the owner asked for two releases that other sessions had already cut.
- **Run `util/release_train/*.py` without `python3 -I`**, or `import detect` fails.
  - `detect.py` exiting 1 means "unreleased changes".
  - `detect.py` has no `--output`; redirect its stdout instead.
- **The consolidated plan holds every line to 512 characters.** Its longest line on v1.14.0 is exactly 512, and the v1.15.0 script refuses longer.
  - Notes are outside markdownlint, so nothing else catches a long line.
  - Put the detail of a table row in a note below the table.
- **Use plain, single git commands.** The worktree guard refuses compound commands, loops and `git -C` into another worktree.
- **H-22 is still in force.** Never paste a recurrence, cascor or canopy body or log, a Sentry event, or any run or suite file into a PR, issue or report. The relays that fill them are fixed only per running service.

## Verification commands for the new thread

```bash
grep -n '^- \*\*Version\*\*' notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md   # 1.15.0 (or later)
python3 -I util/ad-hoc/2026-10-25_consolidated_plan_v1_15_0_p12_arc.py --census-time 2026-10-25T19:56Z --probe-time 2026-10-25T19:56:36Z --check   # every edit "already applied", exit 0
python3 util/ad-hoc/2026-10-25_p12_arc_state_reprobe.py   # exit 0; a DIFFERS row means the state moved since v1.15.0
python3 -I -c "import json,urllib.request;d=json.load(urllib.request.urlopen('https://pypi.org/pypi/juniper-ml/json'));print(d['info']['version'])"   # 0.11.1, or later
grep -n 'juniper-data>=\|juniper-cascor>=' pyproject.toml   # >=0.17.0 / >=0.11.0 until item 1 lands
gh pr list --repo pcalnon/juniper-ml --state open   # check for a concurrent session's [servers] PR before opening one
```

The `--census-time` and `--probe-time` values are the ones the plan's Snapshot records in its v1.15.0 bullet. With other values the Snapshot edit still reads as applied, because the script finds it by a marker.

## Git state

- Worktree `.claude/worktrees/synchronous-splashing-bird`, branch `worktree-synchronous-splashing-bird`, clean at `d7a1908d` before this PR. Every change landed through the API.
- After the PR merges, `main` holds every file listed below, and the worktree's untracked copies can be removed.
- Nothing is staged or committed locally.

## Documents created or modified this session

- juniper-ml#2319:
  - `pyproject.toml`, `CHANGELOG.md`, `README.md`, `AGENTS.md` and `docs/REFERENCE.md`;
  - `util/ad-hoc/2026-10-25_juniper_ml_0_11_1_cut_cochanges.py` (new).
- juniper-ml#2321: `notes/releases/RELEASE_NOTES_v0.11.1.md` (new). The v0.11.1 Release body was also edited.
- This PR:
  - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1.14.0 → v1.15.0);
  - `util/ad-hoc/2026-10-25_consolidated_plan_v1_15_0_p12_arc.py` (new);
  - `util/ad-hoc/2026-10-25_p12_arc_state_reprobe.py` (new);
  - this file (new).
- Outside the repository: the auto-memory files `project_recurrence_equities_p0_arc_2026-10-04.md` and `reference_release_train_ceremony_traps_2026-09-09.md`, and the index `MEMORY.md`.
- Referenced:
  - the predecessor handoff above;
  - `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-21_recurrence-equities-juniper-ml-0-11-0-cut-parked-at-pypi-gate-plan-v1-7-14.md`, for the 0.11.0 procedure 0.11.1 followed;
  - `notes/releases/RELEASE_NOTES_juniper-observability_v0.4.1.md` and `notes/releases/RELEASE_NOTES_juniper-service-core_v0.7.1.md`, whose ratings 0.11.1 mirrors;
  - `util/ad-hoc/2026-10-05_ecosystem_live_census.py`, the census v1.15.0's Snapshot cites;
  - `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`, this file's template.
