# Handoff: backup Phase D follow-up -- AC-5 has not passed (runs of a day or more from 11-19); the owner ruled the remedy; the host steps, the 3-day watch and the probe fixes next

**Date**: 2026-11-24 (facts read between 2026-11-23T20:59Z and 2026-11-24T02:05Z unless a time is given)
**Session**: host yamaguchi, worktree `M` = `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/modular-gathering-squirrel`
(on `origin/main` plus juniper-ml#2617's files; its `tmp/backup-after-sitting/` holds the PR helpers, both commit bodies and the PR body).
**Predecessor, on `main`**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-16_backup-phase-d-record-landed-first-pass-four-ac5-and-pass-test-next.md`
(below: `HANDOFF_2026-11-16_…md`; juniper-ml#2597). Its Limits and traps still hold except where this file says otherwise. **This file's
status list replaces its steps A to E.** The primary checkout's copy of that file (named with a double underscore after
`2026-11-16`) was rewritten by the 2026-11-20 to 11-22 rename pass; `main`'s copy is the original.

`…RECOVERY-PLAN.md` is `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`; `D` is
`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`.

---

## Goal statement

1. **Confirm the owner's host steps for the slow-run ruling** (step A). They had not run at 01:54Z on 11-24.
2. **Watch AC-5** from the 2026-11-24 13:00Z run on (step B). It needs three consecutive `OK OK` watchdog checks at 20:00 CST,
   which needs runs that end before 20:00 CST.
3. **Build the owed probe and watchdog changes** (step C): `ERROR` while a run is in progress (finding 42), AC-3's count (Q1),
   and the warning allow-list (Q6).
4. **Ask the owner Q4**, and ask them to read the unread warnings that the allow-list needs (step D). Then the C.11 items and
   Phase E (step E).

The working pattern holds: the owner runs every command that changes the host or reaches the server and pastes summary lines;
the session checks read-only and names each next command with its expected output. Ask the owner for merge approval again
in a new session.

### What this session did

- **Read a week of the host** (11-16 to 11-23), read-only. `util/ad-hoc/2026-11-23_backup_slowdown_evidence.py` prints the
  probe's history, the watchdog's log and sysstat. Findings 40 to 44 of `…RECOVERY-PLAN.md` §6.3.1 are the result.
- **The retention model held three times** (finding 40). The 11-16 pass deleted nothing. The 11-21 run's pass deleted
  `20261108T140001Z`, which needs `20261107T212908Z` full. The pass of the off-slot run that began at 19:28:47Z on 11-22 deleted
  exactly the two filesets the replay had named, `20261108T234122Z` and `20261109T140001Z`. `20260916T183346Z` was kept every
  time; the all-full port deletes it.
- **AC-5 has not passed** (finding 41). The 11-16 run ended `Warning`. 11-17 and 11-18 read `OK OK`. After that:
  - 11-19's run took 24 h 54 m; the 11-20 slot was lost; the 11-21 run took about 30 h.
  - The 11-22 run began off its slot at 19:28:47Z and took 26 h 56 m; the 11-23 slot was lost.
  - Measured: the `/home` HDD was 67 to 79 % busy in the backup window, against about 45 % before the 11-17 reboot. Duplicati
    ran in the IDLE I/O class (on `mq-deadline`, an idle request waits up to 10 s). clamtk's daily `clamscan` (06:07 CST) ran
    through the long runs. The cause is not isolated.
- **Found and recorded** the 11-17 reboot (finding 43), the probe's `ERROR`s while a run is in progress (finding 42) and the
  watchdog's dependence on the primary checkout (finding 44):
  - The reboot: Dropbox's helper re-owned 31 volumes to `pcalnon`, so AC-7 reads `PASS`, but the ruled `FAIL` stands.
  - The primary checkout is on `task/owner-is-the-overtoadgit`.
- **Owner rulings, 2026-11-23 local** (one dialog, answered by 01:46Z on 11-24, about 4 h after it was asked). They are in
  `…RECOVERY-PLAN.md` §6.6's new table:
  - Slow runs: "Both changes". The I/O class becomes best-effort, priority 7, and `clamscan` moves out of the backup window.
  - Q6's other half: an allow-list after the owner's review.
  - Q1: AC-3's count is judged run-to-run plus an absolute size check.
  - Q8: the aside directory stays where it is.
- **juniper-ml#2617**: commit 1 `a587bd7a` (findings, AC rows, the digest script); commit 2 `66563b08` (the rulings,
  `util/systemd/duplicati.service` to `best-effort`, D's unit listing with an amendment comment and no §12 row);
  update-branch `d516212b`. Its merge state is in "Git status" below.

### Status

- AC-1 `PASS` (since 11-18). AC-5 `FAIL` (newest checks `STUCK`/`STALE`). AC-7 `FAIL` as ruled (the probe reads `PASS`).
  AC-9 not judged (the reboot is evidence, not the test).
- Ruled: Q1, Q2, Q3, Q6 (both halves), Q7, Q8, the slow-run remedy. Open: Q4.
- Host at 01:54Z on 11-24: still the idle class (`ionice -p` reads `idle`), `DropInPaths=` empty, and the crontab still at
  `7 6 * * *` with no nice.

### Remaining work, in order

**A. The owner's host steps** (given in the session at 01:5xZ on 11-24; re-give them if not run). In a pcalnon shell with `sudo`:

```bash
sudo install -d -m 0755 /etc/systemd/system/duplicati.service.d
printf '[Service]\nIOSchedulingClass=best-effort\nIOSchedulingPriority=7\n' | sudo tee /etc/systemd/system/duplicati.service.d/10-io-class.conf >/dev/null
sudo systemctl daemon-reload
sudo ionice -c2 -n7 -u "$(id -u duplicati)"
crontab -l > ~/.local/state/crontab-2026-11-24.bak
sed -E 's|^7 6 \* \* \* /usr/bin/clamscan |0 21 * * * nice -n 19 ionice -c3 /usr/bin/clamscan |' ~/.local/state/crontab-2026-11-24.bak > ~/.local/state/crontab-2026-11-24.new
diff ~/.local/state/crontab-2026-11-24.bak ~/.local/state/crontab-2026-11-24.new
crontab ~/.local/state/crontab-2026-11-24.new
```

Session check (read-only):

```bash
systemctl show duplicati.service -p DropInPaths -p IOSchedulingClass -p IOSchedulingPriority -p NeedDaemonReload -p NRestarts --no-pager
ionice -p "$(systemctl show -p MainPID --value duplicati.service)"
```

Expect `DropInPaths=…/10-io-class.conf`, `IOSchedulingClass=2`, `IOSchedulingPriority=7`, `NeedDaemonReload=no`, `NRestarts=0`,
then `best-effort: prio 7`. Then `crontab -l | command grep -c '^0 21 \* \* \* nice -n 19 ionice -c3 /usr/bin/clamscan '` should
read 1.

- **Do not restart** the service for this. A start may queue the missed slot, and AC-1's clock would reset.
- `ionice -u` changes every existing thread, and new threads inherit the class.
- The drop-in is redundant once Phase E reinstalls the unit with `UMask=0027` (the repository's unit already says
  `best-effort`). Remove it then.

**B. Watch the runs** (read-only, daily):

- the probe's `RUN` line gives each run's duration (`journalctl --user -u yamaguchi-acceptance-probe.service --since today -o cat`);
- the watchdog's 20:00 CST line (`tail -n 3 ~/.local/state/duplicati/server-watchdog.log`);
- `python3 -I util/ad-hoc/2026-11-23_backup_slowdown_evidence.py` for the window's `%util` and iowait.

AC-5 reads `PASS` after three consecutive `OK OK` checks. If runs still exceed about 13 h with best-effort in force, the cause
is elsewhere. Sample per-process I/O during a run (`/proc/<pid>/io` of pcalnon's processes; `localsearch-3` and Firefox are
the largest writers since the reboot).

**C. Code, one PR each, with tests** (the probe's suites, the mutation harness after any change to the suites it drives):

1. **The probe on HTTP 400 during a run** (finding 42): report "run in progress" and judge what needs no log.
2. **AC-3's count per Q1**: run-to-run (about ±10 % a day) plus the absolute size check. Read the 11-11 recommendation first:
   `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-11_backup-phase-d-sitting-steps-11-13-done-ac4-drill-next.md`.
3. **The warning allow-list per Q6**, in the watchdog and the probe. Classify by the `[Warning-<id>]` tag, never by free text
   (finding 35). The list is empty until the owner names classes.

**D. The owner** (one dialog, after any time-critical step; it blocks the session until answered):

- Q4, the drill sample's scope (recommendation: no exclusion).
- Ask the owner to read the unread warnings of the 11-09, 11-10, 11-11 22:14Z and 11-16 runs, and to name the classes to
  accept.
- Optionally: which of `20260915T204850Z` and `20260916T183346Z` is partial (`IsFullBackup`).

**E. C.11 and Phase E**:

- the AC-4 driver's gaps (finding 29);
- the snapshot script's "14:00Z daily" message (`util/ad-hoc/yamaguchi_server_db_snapshot.py:174`,
  `util/ad-hoc/yamaguchi_reboot_verify.bash:156`, the installed copy);
- §6.4 step 4's check text (finding 33);
- `util/safe_merge.py`'s commit text (finding 37);
- Phase E (§6.5): D-14's permission step, which also closes Q8's rename exposure; AC-9's real test.

### Traps found this session

- **sysstat's device names are per boot.** `/home`'s disk is `sdb` since the 11-17 reboot and was `sdc` before it.
  Compare across a reboot by elimination or by UUID, never by name.
- **`/proc/<pid>/io` `write_bytes` is not a disk figure.** `gnome-software` reads 1,584 GiB, more than sysstat counts for all
  disks together.
- **An owner dialog took about 4 h.** Run `date -u` after one returns: the 23:30Z probe and the 02:00Z watchdog had passed or
  were imminent.
- **`main` moved three times in one session.** Fast-forward when the new commits miss your files; the PR helpers refuse
  otherwise.
- **The worktree guard refuses shell loops and compound commands naming git.** Put them in a script under `M/tmp/` and run that.
- **The watchdog runs the primary checkout's file**: any branch the primary holds is live (finding 44).
- **The auto-memory index `MEMORY.md` is at about 23.4 KiB**, 1 KiB under the 24.4 KiB read limit. A compaction to the owner's
  20 KB target is owed, by `feedback_memory_index_target_is_20kb.md`: retire closed arcs' lines into
  `project_closed_arcs_hub.md` verbatim and compare link sets. Never strip hooks; never chase the hook's 17.1 KB.

### Limits (unchanged, verbatim from `HANDOFF_2026-11-16_…md`)

- "Never start, stop, restart, enable, disable or reload a unit."
- "Never run a Duplicati binary, never contact 127.0.0.1:8300, no `sudo`."
- "Nothing under `/mnt/Backups/Ubuntu/` beyond `stat`."
- "Never read a secret file; never print an environment variable or a token."
- "No `git stash`; no interactive shells; no host actions."
- "The owner may direct a named action in person, which releases that action only. Nothing releases one of
  `…RECOVERY-PLAN.md` §6.0 item 6's absolutes."
- Pastes carry counts and summary lines only. Never print `send-http-url`, `TargetURL` or a warning's text. No file is
  written under `/tmp`.

## Verification commands (start of the next thread)

```bash
gh pr view 2617 --repo pcalnon/juniper-ml --json state,mergedAt,mergeCommit --jq '"\(.state) \(.mergedAt) \(.mergeCommit.oid)"'
date -u
systemctl show duplicati.service -p DropInPaths -p IOSchedulingClass -p NRestarts --no-pager
ionice -p "$(systemctl show -p MainPID --value duplicati.service)"
crontab -l | command grep -o -E '^[0-9]+ [0-9]+ \* \* \* (nice -n 19 ionice -c3 )?/usr/bin/clamscan'
tail -n 3 /home/pcalnon/.local/state/duplicati/server-watchdog.log | cut -c1-140
journalctl --user -u yamaguchi-acceptance-probe.service --since yesterday -o cat | command grep -E '^(RUN|CENSUS|AC-5|RESULT)' | cut -c1-200
```

**Expect**:

- `MERGED`, if the session merged it;
- the drop-in and `best-effort: prio 7`, once the owner has run step A;
- `0 21 * * * nice -n 19 ionice -c3 /usr/bin/clamscan`;
- the 2026-11-23 20:00 CST watchdog line, expected to read `ALERT STALE`, since the newest backup is the 11-22 19:28:47Z one.

## Git status at handoff

- juniper-ml#2617 carries `…RECOVERY-PLAN.md`, `D`, `util/systemd/duplicati.service` and
  `util/ad-hoc/2026-11-23_backup_slowdown_evidence.py`. Check its state first.
- This file goes in on its own PR.
- `M`: `origin/main` plus #2617's four files, uncommitted locally, which `main` will hold once #2617 merges.
- **Do not remove `M`, `goofy-painting-rabin`, `swift-stargazing-spindle`, `swirling-skipping-turtle` or
  `parallel-strolling-meteor` yet**: their `tmp/` hold the running record, the validation reports and the tools' evidence (the
  retention rule in the parent `AGENTS.md`).
