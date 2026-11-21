# Handoff: backup Phase D -- the sitting's C.1 to C.9 are done; the first retention pass runs on 2026-11-15; then the record PR

**Date**: 2026-11-15 (facts read between 2026-11-14 23:39Z and 2026-11-15 11:45Z unless a time is given)
**Session**: host yamaguchi, worktree `D` = `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swirling-skipping-turtle`
(on `main` `57c76b63`, clean). The running record lives in `W` = `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swift-stargazing-spindle`.
**Predecessors, on `main`** (all in `prompts/thread-handoff_automated-prompts/`):
`HANDOFF_2026-11-14_backup-phase-d-tools-merged-sitting-resumes-at-c1.md` (below: `HANDOFF_2026-11-14_…md`), and through it
`HANDOFF_2026-11-13_backup-phase-d-tools-pr-last-commit-built-step-14-checks-not-started.md` and
`HANDOFF_2026-11-12_backup-phase-d-step14-tools-pr-open-false-alert-source-found.md` (below: `HANDOFF_2026-11-12_…md`).
Their limits and Key context still hold except where this file says otherwise. **This file's status lists replace their
C.x and Qx statuses.**

---

## Goal statement

1. After the 2026-11-15 13:00Z backup (07:00 CST) has finished, the Overtoad runs `status`; check that run's retention pass,
   the first that can delete anything (step A below).
2. Watch AC-5 complete: the probe can read `PASS` from 02:00Z on 11-17 (step B).
3. Build the record PR (C.10) into `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`
   §6.3.1 (step C).
4. Carry the open questions to the Overtoad: Q1, Q6's Warning half, Q4, Q8 (step D). Then C.11 (step E).

The working pattern holds: the Overtoad runs every command that changes the host or reaches the server and pastes summary
lines; the session checks read-only, keeps the running record and names each next command with its expected output.
Ask the Overtoad for merge approval again in a new session.

### What this session did (2026-11-14 23:38Z to 2026-11-15 11:45Z)

- **juniper-ml#2569 MERGED** 01:35:25Z as `e8c97956`. Retention keeps every fileset of the last two weeks:
  `2W:U,6M:1W,2Y:1M,5Y:2M`. The retention port reads `U` as Duplicati's keep-all, interval zero (`Options.cs`
  2059-2061, `DeleteHandler.cs` 393 at tag `v2.4.0.0_stable_2026-09-03`). The UI's regex accepts upper-case `U` only.
- **juniper-ml#2583 MERGED** 06:05:47Z as `c4d69f81` (head `7d1795fa` after a pinned update-branch). Probe 1.3.0:
  - AC-2 expects 5 sources and 76 filters;
  - the schedule is judged against dated slots (14:00Z from 11-07, 13:00Z from 11-15), and so is AC-6a's snapshot fire
    (13:45Z, then 12:45Z);
  - AC-5 does not count an `OK RUNNING` day.

  The watchdog timer moved to 20:00 local, the snapshot timer to 12:45 UTC.
- **The Overtoad ran, as root, from `W` (tools 1.1.0) and then from `D` (tools 1.2.0, then main's):**
  - C.1 `status` and `shred`: `run dirs : 0 on disk`;
  - drill 1 `PASS` 01:53:01Z, drill 2 `PASS` 03:23:38Z, `ac6` (AC-6b) `PASS` 04:08:40Z;
  - `aside` `PASS` at 05:42:13Z (20 dlists) and again at 11:08:28Z (21; `MANIFEST.sha256 lists 21`, 2,924,387,121 B);
  - the two timers installed (snapshot timer as one file);
  - the 999 test: `ALERT JOB_MISSING`, and the desktop alert fired.
- **C.4, retention restored by a UI save "made at 2026-11-14 11:45pm CST"** (05:45Z). Read back: OPTIONS `PASS`. The save's
  next-run time was in the past, so it queued a backup at once (05:45:35Z, 4h22m, Success). **That run's retention pass
  deleted nothing; the cause is not known.** A candidate, not verified: the save-queued run did not carry the new option.
  The schedule stayed at 14:00Z until a second save (next run 2026-11-15 07:00 CST). That save started no run. AC-2 reads
  `PASS` "repeat=1D at 13:00:00Z (anchor date 2026-11-15)" since 11:16:00Z.
- **C.9 deployed** by the Overtoad at 11:30:09Z: probe `9baec4ec1e8228ca…`, API client `756b41f60c7af32d…`. Timer
  `NEXT Sun 2026-11-15 17:30:00 CST`, enabled, `YAMAGUCHI_BACKUP_ID=2`.
  - First run: `RESULT: FAIL (7 PASS, 1 FAIL, 1 PENDING, 2 ATTN, 2 INFO)`, AC-7 the one FAIL.
  - The unit reads `failed` after a FAIL **by design**: the unit file says so.
- **Running record**: 1,197 lines, `W/tmp/phase-d-sitting/running-record.md`. It is rebuilt by
  `W/tmp/phase-d-sitting/assemble_record.py`, which now lists this session's `segment-2026-11-14b.md`, and archived to the
  primary's `tmp/phase-d-sitting/` (both copies sha256 `96db88a0d44fde7d`). The segment's source is
  `D/tmp/phase-d-sitting/segment-2026-11-14b.md`. If you edit a segment, edit `W`'s copy and re-run the assembler.
- Memory: `project_backup_arc_hub.md` has the 2026-11-15 paragraph; the MEMORY.md line was updated.

### The Overtoad rulings this session (answers verbatim)

- Dialog, 2026-11-15 00:08:36Z:
  - May the probe list the destination's file names (the census): "Accept as built (Recommended)".
  - Q7: "Keep all for two weeks".
- Dialog, 04:46:17Z:
  - AC-2's source change: "Yes, deliberately".
  - Q2: "Yes, all three". The three off-schedule starts were the Overtoad's UI saves; 05:45:35Z was a fourth, observed.
  - Q3: "Keep D-14; 0017 interim".
  - Q6: "Don't count them".
- On the UMask, the Overtoad's words: "the change to umask 0017 was intended to write backup files into the Yamaguchi
  directory that were group writable. the group Overtoadship of these files is duplicati. since the pcalnon user is a
  member of the duplicati group, this allows files to be processed by Dropbox." D-14 stands. **Never propose
  group-writable volumes**; `0017` is the Overtoad's own interim.
- The Overtoad request: "move the watchdog check to 8:00pm CST" and "move the scheduled backup time to 7:00am CST". Done
  (#2583, the Overtoad's installs and the second save).

### Status of every predecessor item

- C.1 to C.7 and C.9: done, as above.
  - C.7 (AC-5): the streak is 1 of 3, on 11-14.
  - C.4: its first pass is step A.
- C.8 (AC-7): `FAIL` by the Q3 ruling. The 14 volumes `dropbox filestatus` reads `unsyncable` equal, kind by kind,
  MODES' `640 duplicati:duplicati` counts (5 dblock, 5 dindex, 4 dlist). The six `660` volumes written under `0017` are
  not among them.
- C.10: not started (step C). C.11: the memory hub is updated; the rest is step E.
- Q2, Q3, Q6, Q7: ruled (above). Open: Q1, Q4, Q8, and Q6's Warning half.
- `HANDOFF_2026-11-14_…md` item D (fold the 11-14 Python switch, `safe_merge.py`'s local path and the squash text, and the
  3.15.2 regression runs into the record PR): still owed, in step C.
- Not done: the primary checkout's pull (Overtoad), and `JuniperCascor1`'s three links. They still point at `/usr/bin`; the
  restore is three `ln -sfn python3.14 …` commands, the Overtoad's. This session ran the env's 3.14.7 through the shim
  `D/tmp/backup-phase-d-swirling/py314-bin/`.

### Remaining work, in order

**A. The first retention pass (Overtoad, root), once the 13:00Z run has finished.** Runs have taken 0h52m to 12h30m.

```bash
D=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swirling-skipping-turtle
bash "$D/util/ad-hoc/2026-11-11_phase_d_finish.bash" status --backup-id 2
```

Expect:

- the RUN line on the 2026-11-15T13:00Z run, with the note `retention deleted 5 fileset(s)`;
- that run `scheduled` in the run table;
- CENSUS `17 dlist` (21, plus the run's own, less the five pre-recovery dlists `aside` predicted at 11:08Z), AGREE;
- AC-2 `PASS`; OFFSCHED still 4 of 10.

`plan` evaluates every pass time up to 60 h ahead, so the clock should not change the count.

- **If the pass deletes none again**, refuse any further save and ask the Overtoad. Nothing is lost: `aside` holds all 21.
- **If it deletes some other number**, run `bash "$D/util/ad-hoc/2026-11-11_phase_d_finish.bash" plan` (any user) and
  compare its `stability` line.

**B. AC-5 (pcalnon, read-only).** Watchdog-log stamps carry `-0600`, so the probe's days are local dates.

- 11-14 holds two `OK OK` records for backup 2. 11-15 holds only the two 999 test records, which the streak ignores.
- If the 20:00 CST checks of 11-15 and 11-16 both read `OK OK`, AC-5 reads `PASS` from 02:00Z 11-17. The daily probe
  first sees it at 23:30Z 11-17; the Overtoad can run the probe by hand sooner.
- A `Warning` run resets the streak (Q6's Warning half).

**C. The record PR (C.10)**, into `…RECOVERY-PLAN.md` §6.3.1. Fold in:

- the findings lists and Key context of `HANDOFF_2026-11-12_…md` and `HANDOFF_2026-11-13_…md`;
- item D of `HANDOFF_2026-11-14_…md`;
- this session's segment (`W/tmp/phase-d-sitting/segment-2026-11-14b.md`): rulings, results, and the traps below.

Build it from `origin/main` blobs. `util/open_signed_pr.py` signs. Run both sequence-safety screens on a local
probe commit first (never pushed; `git reset --soft` after).

**D. For the Overtoad:**

- Q1: AC-3 after the source change. Examined bytes read +8.1% against the 2026-11-08 baseline; AC-3's threshold is 5%.
- Q6's Warning half: a `Warning` run reads `ALERT NOT_SUCCESS` and resets the streak, and the 11-10 run's 575 warnings
  have not been read.
- Q4: the drill sample scope. Recommendation: no exclusion.
- Q8: the aside directory's location.

**E. C.11:**

- the AC-4 driver's gaps;
- the snapshot script's stale message "14:00Z daily" (repo and installed copies);
- Phase E, `…RECOVERY-PLAN.md` §6.5: O-11, D-12, finding 15, AC-14's Phase E ruling;
- AC-7's route, under the Q3 ruling;
- the `safe_merge.py` squash-body follow-up.

### Traps found this session

- **A job save whose next-run time is not in the future queues a backup at once.** Before saving in the UI, set the
  next run in the future, and never save during a backup.
- **`tests/test_clear_stop_backup_design.py` pins passages of
  `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`.** An amendment pointer inside a
  `new` passage of `util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py`, or any row after that file's §12
  2026-10-08 row, fails CI. Put pointers beside those passages.
- **`util/install_duplicati_service.bash` would reinstall `duplicati.service` with `UMask=0027`** over the interim `0017`.
  Install a single unit file by hand instead.
- **The watchdog's deploy script installs from the PRIMARY checkout** (still at `4a786c81`). Do not use it until the
  primary is pulled.
- **Moving a `Persistent=true` timer to a time that has already passed today fires it once at `daemon-reload`.**
  The watchdog did so at 23:40:44 CST.
- **Worktree isolation refuses compound commands that name git**, even inside a URL or header. Put them in a script
  under `tmp/` and run that.
- **Mutant anchors must occur exactly once.** Re-anchor them after any rewrite of an anchored function.

### Limits (unchanged, verbatim)

- "Never start, stop, restart, enable, disable or reload a unit."
- "Never run a Duplicati binary, never contact 127.0.0.1:8300, no `sudo`."
- "Nothing under `/mnt/Backups/Ubuntu/` beyond `stat`."
- "Never read a secret file; never print an environment variable or a token."
- "No `git stash`; no interactive shells; no host actions."
- "The Overtoad may direct a named action in person, which releases that action only. Nothing releases one of
  `…RECOVERY-PLAN.md` §6.0 item 6's absolutes."
- Pastes carry counts and summary lines only. Never print `send-http-url`, `TargetURL` or a warning's text. No file is
  written under `/tmp`.

## Verification commands (start of the next thread)

```bash
gh pr view 2583 --repo pcalnon/juniper-ml --json state,mergedAt,mergeCommit --jq '"\(.state) \(.mergedAt) \(.mergeCommit.oid)"'
gh pr view 2569 --repo pcalnon/juniper-ml --json state,mergedAt --jq '"\(.state) \(.mergedAt)"'
date -u
tail -n 4 /home/pcalnon/.local/state/duplicati/server-watchdog.log | cut -c1-120
systemctl --user list-timers yamaguchi-acceptance-probe.timer yamaguchi-watchdog.timer --no-pager
sha256sum /home/pcalnon/Development/python/Juniper/juniper-ml/tmp/phase-d-sitting/running-record.md | cut -c1-16
```

**Expect:**

- `MERGED 2026-11-15T06:05:47Z c4d69f81…` and `MERGED 2026-11-15T01:35:25Z`;
- watchdog records of 20:00 CST once 11-15's has run;
- the probe timer at 17:30 CST, the watchdog at 20:00 CST;
- `96db88a0d44fde7d`, unless a later session rebuilt the record.

## Git status at handoff

- `main` holds #2569 and #2583. No PR of this arc is open, except the one that carries this file.
- `D` (`swirling-skipping-turtle`): on `main` `57c76b63` plus this file. Its `tmp/backup-phase-d-swirling/` holds:
  - the check scripts;
  - the 3.14.7 PATH shim;
  - the regression and `safe_merge` logs;
  - the mutant trees;
  - the upstream sources fetched for Q7.
- **Do not remove `D`, `W` or `parallel-strolling-meteor` until the record PR has merged.** Their `tmp/` hold files the
  primary's archive lacks.
