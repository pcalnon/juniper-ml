# Handoff: backup Phase E -- the Overtoad ruled three questions (offsite route deferred, order P1-P2-10.2-P4, clamscan with flock); AC-5 day 2 of 3; the Phase E runbook is drafted, to validate and land; step A and the round still owed

**Date**: 2026-11-26 (facts read between 01:23Z and 02:26Z unless a time is given)
**Session**: e45ac81a, host yamaguchi, worktree `W` = `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/joyful-soaring-pnueli`.
**Predecessor, on `main`**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-25_backup-step-e-findings-landed-ac5-day-1-host-steps-and-phase-e-runbook-next.md`
(the 11-25 predecessor; juniper-ml#2657, merged 04:32:40Z as `ba7f8196`). Its Limits and traps still hold except where this file
says otherwise. **This file's status list replaces its goal items 1 to 4.**

`…RECOVERY-PLAN.md` is `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`; `D` is
`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`; **the draft** is `W/tmp/phase-e/runbook_draft.md`
(775 lines, sha256 `5fabd7c30a5a2d69…`), written by a fresh planner agent from the brief `W/tmp/phase-e/brief.md`; its final
message is archived verbatim at `W/tmp/phase-e/drafter_final_message.txt`.

---

## Goal statement

1. **Confirm the Overtoad's host steps.** Re-given at about 01:5xZ with ruling 3's line and not run at 01:55Z. **Step A** is the
   draft's §2.1: the 11-24 handoff's step A (`prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_backup-ac5-not-passed-runs-slowed-io-class-ruled-host-steps-and-probe-fixes-next.md`,
   lines 70-79) with one change, its `sed` line now inserting `/usr/bin/flock -n /home/pcalnon/.local/state/clamscan.lock`
   before `nice -n 19 ionice -c3`. Both `sed` forms were dry-run against the live crontab (2 lines): each changes exactly the one
   clamscan line. **The round**: the pull ran at 01:16Z (the Overtoad's), so only the snapshot copy
   (`sudo install -m 0755 -o root -g root util/ad-hoc/yamaguchi_server_db_snapshot.py /usr/local/lib/duplicati/yamaguchi_server_db_snapshot.py`, then `sha256sum` it: `c3aebdc6…`)
   and `bash util/ad-hoc/yamaguchi_acceptance_probe_deploy.bash --backup-id 2` remain, both from the primary checkout. The step A
   crontab line must be in before **06:07 CST**, or the old line starts a nice-0 scan 53 minutes before the 07:00 CST backup, as
   it did on 11-25.
2. **AC-5 day 3**: the 11-26 20:00 CST check (02:00Z on 11-27). It needs the 11-26 13:00Z run to end within 13 h; the 11-25 run
   took about 12 h 45 m and beat its check by about ten minutes. If day 3 reads `OK OK` (or `OK WARNINGS_ACCEPTED`), AC-5 reads
   `PASS` at the 11-27 probe (23:30Z).
3. **Validate the draft, then land it** as `notes/JUNIPER_2026-11-26_JUNIPER-ECOSYSTEM_BACKUP-PHASE-E-RUNBOOK.md`, together with
   `…RECOVERY-PLAN.md` §6.6 rows for the three rulings below and a pointer from its §6.5, in one signed PR (`util/open_signed_pr.py`;
   ask the Overtoad for merge approval: it is per session). Validate per the auto-memory note
   `feedback_multi_agent_adversarial_validation_sop.md`: copy the draft into your worktree first, freeze it during each round,
   lanes as fresh agents with a brief file, findings as `findings.txt` plus `fixes.json` (a subagent's `.md` findings Write is
   refused: `reference_subagent_findings_md_write_refused.md`). The lanes I would run: **A** re-probe every claim against its cited
   `file:line`; **B** each owner command against its `#` lines on this host (uutils coreutils, GNU sed 4.9, util-linux 2.41.3 `flock`);
   **C** omission and order against `D` §8 P1/P2/P4, §9 and §10.2. Start from the drafter's own list (below).
4. **Ruling 1's investigation**, the Overtoad's words: "let's look into changing the file owner for dropbox. ideally, i'd like
   to specify acceptable owner(s) per directory tree." The facts are below and in the draft's §5. Turn them into design candidates
   and put them to the Overtoad in one dialog, after any time-critical step (a dialog blocks the session until answered).

The working pattern holds: the Overtoad runs every command that changes the host or reaches the server and pastes summary
lines; the session checks read-only and names each next command with its expected output.

### The Overtoad's rulings of 2026-11-26 (one dialog: opened after 01:36:20Z, answered before 01:53:12Z; local date 11-25)

1. **Offsite route: "Defer the route"**, with the note quoted in goal item 4. So `D`'s D-14 permission step on the existing tree,
   the unit's return to `UMask=0027` and AC-7 wait for the route's design. The options put were a local mirror (recommended:
   master outside the Dropbox root under D-14, a pcalnon-owned one-way `rsync --delete` copy at today's path), a one-way upload
   (rclone or similar; a new credential), and deferral.
2. **Order: "P1, P2, 10.2, P4 (Recommended)"**: `D`'s own order. P2 here means its route-independent items.
3. **clamscan: "With a flock guard (Recommended)"**: `0 21 * * * /usr/bin/flock -n /home/pcalnon/.local/state/clamscan.lock nice -n 19 ionice -c3 /usr/bin/clamscan …`
   (the rest of clamtk's line unchanged).

### What this session did

- **juniper-ml#2656 MERGED** 2026-11-25 03:22:04Z as `8aa58b08` (finding 37). #2652 (`ad19fa19`) and #2653 (`b3c57641`) re-read: merged.
- **Host, read 01:23Z to 02:01Z.** The primary was pulled by the Overtoad at 01:15:58Z and 01:16:19Z to `966cdb13` (reflog;
  `main` is now `fcbc5d3c`, two juniper-observability release commits that touch no backup file). Its four scripts equal `main`'s:
  watchdog `aa789a22…`, snapshot `c3aebdc6…`, probe `7d87e6f9…` (1.5.0), API client `756b41f6…`. So the 11-25 20:00 CST check
  was the first run of the post-#2645 watchdog (Result=success). Installed copies unchanged: snapshot 1.2.0 `8fa7bb24…`, probe
  1.3.0 `9baec4ec…`. Step A not run (no drop-in, `IOSchedulingClass=3`, `idle`, crontab `7 6 * * *`, no `crontab-2026-11-24.bak`).
  No system unit had `NeedDaemonReload=yes`, so step A's `daemon-reload` loads only the drop-in.
- **The 11-25 run**: still working at 01:25Z (24 s of CPU in 36 s); the 23:30Z probe 1.3.0 read `RUN ERROR log -> 400`
  (finding 42; `RESULT: UNDETERMINED (4 PASS, 1 PENDING, 6 ERROR, 2 INFO)`). Its dlist is `duplicati-20261125T130001Z.dlist.zip.aes`
  (stat: written 01:42:53Z, 352,715,981 B; 11-24's was 317,839,949 B), the folder last changed 01:50:03Z, Duplicati idle by 02:01Z.
  The watchdog line, verbatim: `2026-11-25T20:00:00-0600 OK OK backup=2 newest backup 2026-11-25T13:00:00.1907973Z ParsedResult=Success age=13.0h`.
- **11-25 was a slow day again** (`util/ad-hoc/2026-11-23_backup_slowdown_evidence.py`): `sdb` (`/home`) 75.8 % busy over
  07:00-19:00 CST (11-24: 36.8 %), swap 94-96 %, iowait 12.6 %. Hourly (sar): 69-83 % from 08:00 to 19:00 CST at only 1-4 MB/s
  read and 1.5-3 MB/s write, a seek-bound load. Both clamscans ended without a summary line (logs `~/.clamtk/history/Nov-24-2026.log`
  last written 12:31 CST on 11-25 -- that scan ran about 30 h -- and `Nov-25-2026.log` 12:40 CST); no OOM or systemd-oomd kill is
  recorded and none was running at 19:25 CST; asked the Overtoad whether they stopped them: **not answered**. The disk stayed busy
  for hours after they ended, so clamscan is not the only competitor; the idle-class mechanism (mq-deadline ageing) still fits
  the ruled remedy.
- **Dropbox facts (ruling 1)**: the 11-17 boot's helper, from the journal: `pkexec … /bin/sh -c 'chown -h -R -- "$1" "$2"; chmod -R -- "u+$3" "$2"; echo Done' sh 1000 /mnt/Backups/Ubuntu/Dropbox rwX`
  -- one recursive re-own of the whole Dropbox root, no per-tree scope. No Dropbox polkit action is installed; the generic
  `org.freedesktop.policykit.exec` is `auth_admin` (any, inactive, active; no `keep`), so **finding 43's re-own happened only because
  a password prompt was approved**; a local polkit rule can refuse that exact command line. **Write, not ownership, blocks sync**:
  `660 duplicati:duplicati` volumes sync (probe AC-7 `PASS` since 11-17), `640 duplicati:duplicati` read `unsyncable` with the
  daemon in gid 139 (finding 22). So "owners per tree" reduces to "which uid may write each tree"; any write grant to `pcalnon` is
  D-14's rejected exposure. Dropbox documents no per-directory owner setting (forum threads only, cited in the draft's §5).
- **Other facts**: S-4's in-tree `…/Dropbox/Backups/_yamaguchi_keys` is still present (`770 pcalnon:duplicati`, mtime 2026-08-29);
  the sibling `/mnt/Backups/Ubuntu/_yamaguchi_keys` is `700 pcalnon:pcalnon` (11-05). `df`: `sda1` 3,042 G free; `/` 264 G free, where
  `D` §10.2 step 4 stages and assumed 357 G against ~203 GiB -- the set's size today is recorded nowhere. `Duplicati.empty-2026-09-20/.env`
  was shredded at Phase D step 9 (`…RECOVERY-PLAN.md` §6.3.1, the "9, escrow" row), so `D` §10.2's "only P4 step 2 removes" is
  stale; the folder (`700 duplicati`) stays for P4. The watchdog's drop-in reads `YAMAGUCHI_BACKUP_ID=2`, so P2's redeploy is done.
- **The draft** (sections §0-§12: rulings, step A and the round, P1, P2's route-independent items with AC-9's hazards first, the
  deferred items plus the Dropbox investigation, §10.2 then O-9, P4, departures, open items OI-1 to OI-17, findings F-1 to F-12).
  The drafter's headline findings: **F-1** `yamaguchi_reboot_verify.bash post` forces a watchdog run whose record can cost AC-5 its
  day, so reboot after AC-5 passes; **F-3** §10.2 never pauses the job between the staging copy and the swap, so the swap would
  drop backups made in between; **F-4** `/` may lack room for staging; **F-8** nothing reads the new `/etc/credstore/duplicati-passphrase`.
  It flagged as unverified: `flock`'s lock-file creation, two systemd property names, `journalctl --since -8d`, GNU tar `--compare`,
  the reboot command and the RecoveryTool's executable name; its two `/tmp` matches need a G-TMP look.

### Corrections (this session's own errors, caught in-session)

- I predicted `ALERT STUCK` from the 01:25Z CPU sample; the run ended about 01:43-01:50Z and the check read `OK OK`. Predict a
  check from nothing but the check; stat the dlist by name (and a fileset can be `…01Z`).
- The brief said runs took "4 h to 30 h": finding 41 gives 1 h 41 m to about 30 h. It said a gate refuses `/home/pcalnon` in
  notes: G5 covers only scripts under `util/`, `scripts/` and `.github/` (`.pre-commit-config.yaml:342-346`). Its last bullet
  extrapolated "still in progress at 12.9 h" to 01:53Z; the drafter was sent the measured correction before it finished.

### Status

- AC-1 `PASS`. **AC-5: 2 of 3** (11-24, 11-25). AC-7 `FAIL` as ruled, its route deferred. AC-9 not judged. AC-12 read 1.7 on 11-25.
- Host at 02:01Z: idle class, no drop-in, crontab `7 6`, snapshot 1.2.0, probe 1.3.0, no clamscan running, no backup running.

### Traps found this session

- **The worktree guard** refused `for f in …; do … "$(git show origin/main:$f | sha256sum …)"; done` and a `for` loop around
  `[ -f ] && { …; grep …; }`. When HEAD equals `origin/main`, hash the worktree's own files; put loops in a script under `W/tmp/`.
- **uutils `sort -t=`** errors ("separator must be exactly one character long"): put the key first and sort on field 1.
- **`pidstat -d` cannot read the `duplicati` uid's I/O** (and shows no iodelay for it): it lists pcalnon's processes only.
- **A background agent dies with its session**: wait for its notification before ending; log its final message to a file first.

### Limits (unchanged, from the 11-24 predecessor)

Never start, stop, restart, enable, disable or reload a unit; never run a Duplicati binary, never contact 127.0.0.1:8300, no
`sudo`; nothing under `/mnt/Backups/Ubuntu/` beyond `stat`; never read a secret file or print an environment variable or a token;
no `git stash`, no interactive shells, no host actions. Pastes carry counts and summary lines only; never print `send-http-url`,
`TargetURL` or a warning's text. No file is written under `/tmp`.

## Verification commands (start of the next thread)

```bash
date -u
systemctl show duplicati.service -p DropInPaths -p IOSchedulingClass -p IOSchedulingPriority -p NeedDaemonReload -p NRestarts --no-pager
ionice -p "$(systemctl show -p MainPID --value duplicati.service)"
crontab -l | command grep -c '^0 21 \* \* \* /usr/bin/flock -n /home/pcalnon/.local/state/clamscan.lock nice -n 19 ionice -c3 /usr/bin/clamscan '
tail -n 3 /home/pcalnon/.local/state/duplicati/server-watchdog.log | cut -c1-140
journalctl --user -u yamaguchi-acceptance-probe.service --since yesterday -o cat | command grep -E '^(== |RUN|AC-5|RESULT)' | cut -c1-200
sha256sum /usr/local/lib/duplicati/yamaguchi_server_db_snapshot.py ~/.local/lib/yamaguchi-acceptance/yamaguchi_acceptance_probe.py
sha256sum /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/joyful-soaring-pnueli/tmp/phase-e/runbook_draft.md
```

**Expect**:

- Once step A has run: `DropInPaths=/etc/systemd/system/duplicati.service.d/10-io-class.conf`, `IOSchedulingClass=2`,
  `IOSchedulingPriority=7`, `NeedDaemonReload=no`, `NRestarts=0`, then `best-effort: prio 7`, then a count of 1.
- The 11-26 20:00 CST watchdog line (02:00Z on 11-27).
- Once the round has run: `c3aebdc6…` and `7d87e6f9…`, and a probe banner reading `1.5.0`.
- The draft: `5fabd7c30a5a2d69…`.

## Git status at handoff

- `main` is `fcbc5d3c`. This file goes in on its own PR.
- `W` is at `966cdb13`, clean apart from this file. `W/tmp/phase-e/` (ignored) holds `brief.md`, `runbook_draft.md`,
  `drafter_final_message.txt` and `wait_watchdog_2026-11-25.bash`: keep them under the retention rule in the parent `AGENTS.md`,
  and copy them out before any `git worktree remove` of `W` (it deletes ignored files). The predecessors' worktrees listed in the
  11-25 handoff are still to be kept.
- The auto-memory hub `project_backup_arc_hub.md` holds this session's entry; the index `MEMORY.md` is about 23.0 KB, over the
  Overtoad's 20 KB target: a compaction by retiring entries is still owed (`feedback_memory_index_target_is_20kb.md`).
