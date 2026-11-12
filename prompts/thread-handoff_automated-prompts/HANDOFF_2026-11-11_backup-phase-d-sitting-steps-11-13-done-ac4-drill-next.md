# Handoff: backup Phase D sitting -- steps 9-13 done, AC-3 accepted, AC-4 drill 1 next

**Date**: 2026-11-11
**Session**: `backup-phase-d-design-merged-then-sitting` (continued), host yamaguchi
**Predecessor**: `HANDOFF_2026-10-30_backup-phase-d-design-merged-then-sitting.md` (this directory)
**Plans of record**:

- the recovery plan, `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`
  (its §6.4 holds the sitting's steps 0-14; §6.3.1 receives the record);
- the integrated design, `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`
  (its §8 P0 steps 9-11, and the AC table with notes AC-3a, AC-4a, AC-12a and AC-13a).

---

## Goal statement

Continue the Phase D sitting (Procedure A0) from step 14 of the recovery plan's §6.4. Close AC-4 with two restore drills.
After AC-4's first drill passes, copy the five dlists aside and restore `retention-policy`. Close AC-5, AC-6 and AC-7.
Then land the sitting's record in the recovery plan's §6.3.1 as one signed PR.

The **first task** is the process change described in the section "Process change: automate the remainder" below. Build
the two tools, then run the rest of the sitting through them.

**The working pattern holds.** The owner runs every command that changes the host or reaches the server, in the root
shell or the pcalnon shell. They paste the summary lines. The session checks read-only, keeps the running record, and
writes each next block with its expected output. "merge approval granted" covers this sitting's PRs.

### Completed in this segment (2026-11-04 to 11-09)

- **Step 9, the escrow.** Two scripts were written and audited: `util/key_escrow.bash` and
  `util/secure_copy-to-clipboard.bash`.
  - The owner's stub was empty: it never called a clipboard tool. The only `xclip` was in a deprecated conda env and
    wrote the PRIMARY selection, which a password manager's paste doesn't read.
  - The settings key went into all three escrow places, each confirmed by sha256: the sda1 sibling, 3 printed copies,
    and the password manager (two typed checks).
  - Both CUPS spool copies, the passphrase sheet and the old `.env` were shredded.
- **Step 10.** The server started with the key from the systemd credential, and the stored pause held: `serverstate`
  exited 2.
- **Step 11.** Every edit was read back through `export 2`.
  - The UI password was rotated. The `web-credential` file was rewritten in place, the S-5 line was retired from the
    primary checkout's `.env`, and `.env` was chmodded from 664 (world-readable) to 600.
  - In job 2: `--tempdir=/home/duplicati/.cache/duplicati-tmp`, the guard as `--run-script-before-required`,
    `--aes-version=2`, and "Keep all backups". There are no server-wide retention defaults.
  - The guard dry run exited 0. The service was restarted, `export 2` confirmed the edits, and `resume` fired the
    overdue backup, which is the AC-3 run.
- **AC-3, accepted by owner ruling (2026-11-08).**
  - The run is `20261107T212908Z`: `Warning`, 3 transient Firefox `PathNotFound`/`MetadataProcessFailed` warnings, 0
    errors, census `AGREE`, nothing deleted.
  - The new baseline is **1,882,694 files / 280.40 GiB**. The growth is real, not lost filters: the 45 filters are
    intact. About 1.05M of the files are in `juniper-ml/.claude/worktrees` (234 worktrees). Excluding that tree was
    rejected because uncommitted work lives there.
  - The `~/.ssh` (33 files) and `~/.gnupg` (97) finds were done in the UI's Restore browser, by owner ruling instead of
    `duplicati-cli find`.
- **Step 12** was skipped (it applies to Procedure A only).
- **Step 13.**
  - The re-key gate passed on a root-only copy, which was then shredded: `encrypted-fields=True`, 11 blobs, all under
    the credstore key.
  - `yamaguchi-server-db-snapshot.timer` was enabled. It fired at once, `success`, and fires next daily at 13:45 UTC.
- **These acceptance checks pass:**
  - **AC-1:** 38 h, `NRestarts=0`.
  - **AC-2:** includes `blocksize` `1MB`.
  - **AC-12:** 1.7, with 15 ✗ rows, all in note AC-12a's accepted set.
  - **AC-13.**
  - **The watchdog:** its 12:00 check on 11-08 read `OK`.
- **AC-7 was found failing and fixed temporarily.**
  - The post-recovery volumes are `0640 duplicati:duplicati` (the unit's `UMask=0027`). The Dropbox daemon, started
    10-28, lacked gid 139, so every new volume was `unsyncable`.
  - The owner restarted it with `sg duplicati -c 'dropbox start'`, giving it primary gid 139. It is now syncing.
- **A new AC-4 driver.** `util/ad-hoc/2026-11-09_ac4_restore_drill.py` decrypts in-process with no passphrase on argv,
  names the fileset with `--dlist`, keeps secrets out of the sample, and runs two negative controls.
  - Its self-test passes.
  - Its select-only run on `duplicati-20260918T140000Z` passed: 1,164,145 entries, 18 benign candidates, all
    `static=True`.

### Remaining work, in order

1. **The process change.** See the section "Process change: automate the remainder" below.
2. **AC-4, drill 1.** Restore `duplicati-20260918T140000Z.dlist.zip.aes`. **The owner had not reported its result at
   handoff.**
   - Check first whether `/root/phase-d-tmp/ac4-drill1.out` exists. If it does, read its result lines through the
     owner; don't re-run.
   - Run it after that day's 14:00Z backup has finished. The drill refuses its own result if the dlist list changes
     mid-restore.
   - Then shred the run directory.
3. **Before restoring retention, recompute the deletion table.** The post-recovery filesets now include two on 11-08,
   only 9.7 h apart (`20261108T140001Z` and `20261108T234122Z`), so the table must take them into account:
   `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/retention_table.py --policy 2W:1D,6M:1W,2Y:1M,5Y:2M`.
4. **The aside copy.** Copy the dlists the first pass will delete to `/mnt/Backups/Ubuntu/_yamaguchi_retention_aside`:
   root, mode 0700, `cp -p`, with `sha256sum` compared on both sides. Per the recovery plan these are 0912, 0915T0856,
   0916, 0917 and 0918, plus whatever the recompute adds.
5. **Restore `retention-policy`** as `2W:1D,6M:1W,2Y:1M,5Y:2M` in the UI, and record the date.
   - `keep-time` and `keep-versions` are **never** restored.
   - **After saving, read back with `export 2`.** The B3 save silently added `send-http-url` and
     `http-report-status-url`, and moved the schedule `Time` from 09-18 to 09-17.
6. **AC-4, drill 2,** on the first post-recovery fileset, `duplicati-20261107T212908Z.dlist.zip.aes`.
7. **AC-5:**
   - 3 consecutive watchdog `OK` days (from 11-08);
   - a deliberate `--backup-id 999` run must report `JOB_MISSING`;
   - the log is `~/.local/state/duplicati/server-watchdog.log`.
8. **AC-6:** the snapshot's mtime advances daily (the 11-09 13:45 UTC fire onwards), and the snapshot appears in the
   next fileset.
9. **AC-7, durably.** See open question Q3. Then: the newest dlist is `up to date` within 24 h, and `_yamaguchi_keys/`
   sits outside the Dropbox root.
10. **The record PR**, into the recovery plan's §6.3.1. The findings to fold in are listed in the "Key context" section
    below.
11. **Then:** update the memory hub `project_backup_arc_hub.md`, and move on to the after-Phase-D items: Phase E, O-11,
    D-12, finding 15, and AC-14's Phase E ruling.

### Open questions (the owner's to rule)

- **Q1. AC-3's count criterion going forward.** The day after the rebaseline, the 23:41Z run examined 2,045,309 files
  (+8.6%). A fixed count with a ±2 % tolerance will keep failing.
  - Recommendation: compare each run with the previous run (for example ±10 % per day), plus the absolute size check.
- **Q2. The 2026-11-08 23:41:22Z run, which the owner says they didn't start.**
  - The job log puts it 30 s after the owner's Restore-browser searches (`ListFilesets`, `ListFolder`, `SearchFiles`
    from 23:35 to 23:40:51).
  - Nothing on the host triggered it: the journal from 17:38 to 17:43 CST shows no unit or timer.
  - Most likely it was an inadvertent **Start** or **Run now** click in the UI. The result was `Success`, 0 warnings.
  - Optional confirmation: the UI's **About → Logs → Stored** around 17:41 CST (K2). If it reads as an API or
    remote-control request, treat it as a security finding, because the console connection is enabled.
- **Q3. A durable fix for AC-7.** The `sg` start does not survive logout or reboot. A fresh login gives Dropbox gid 139
  as a supplementary group, because `/etc/group` lists pcalnon. Two options:
  - (a) rely on re-login, and have the probe check after each boot;
  - (b) an autostart override, `Exec=sg duplicati -c "dropbox start -i"`.

  Recommendation: (a), plus the probe's check.
- **Q4. Drill sample scope.** The 09-18 sample includes one `~/Pictures/Screenshots/*.png`. It is restored only into a
  root-only directory and then shredded. Should `Pictures/` be excluded anyway?
- **Q5. Where the scripts land.** This PR commits the three new scripts (named in "Key context" below) so that they
  survive the worktree. The original plan was the record PR. Confirm that this is acceptable.

### Process change: automate the remainder (the first task)

**The problem.** Each step of this sitting cost one owner round-trip per command block. On top of that, about a third
of the session's corrections came from hand-written check commands:

- a grep for a log line the wrapper never writes (`via systemd credential`);
- a `--since` cut that excluded the start;
- a warning classifier that matched path text;
- a parser that returned 0 entries silently.

**The change.** Move every remaining check into tools with fixed, tested predicates. The owner then runs one command per
step and pastes one verdict block.

1. **`util/ad-hoc/yamaguchi_acceptance_probe.py`**, read-only, run as pcalnon. Install it on a daily user timer after
   the 14:00Z run (for example 15:30 UTC).
   - It evaluates:
     - AC-1 (`systemctl show`);
     - AC-2 and AC-13 (`export 2`, filtered by option name; values for a fixed allow-list only, never `send-http-url` or
       `TargetURL`);
     - AC-5 (the watchdog log: N consecutive `OK`);
     - AC-6 (snapshot mtime and size against yesterday);
     - AC-7 (Dropbox daemon `Gid`/`Groups` includes 139, and `dropbox filestatus` of the newest dlist);
     - AC-12 (`systemd-analyze security`: score ≤ 2.0, and the ✗ set equals AC-12a's);
     - the newest run from `yamaguchi_census.py --runs 1`: `ParsedResult`, `Warnings` classified by their
       `[Warning-<id>]` tag against an allow-list (the Firefox class), count delta against the previous run, `AGREE`.
   - It writes `~/.local/state/duplicati/acceptance.json` and one line per criterion. Its exit code is non-zero on any
     FAIL. The watchdog can include its summary.
   - It prints counts, tags and names only. It never prints a warning's text, a URL or a value.
2. **`util/ad-hoc/2026-11-xx_phase_d_finish.bash`**, root, run once per step. It sequences:
   - **drill** — the AC-4 driver plus the run-directory shred;
   - **aside** — the dlist list from the `retention_table.py` recompute, `install -d -m 0700`, `cp -p`, a sha256 compare,
     refusing if drill 1's `results.json` isn't PASS;
   - **status** — the probe's verdict.

   Each verb prints its own pass/fail block. The UI-only steps (the retention edit) stay manual, with a read-back through
   the probe.
3. **Tests.** Add hermetic tests for every predicate in both tools. Start with the four regressions above: the absent log
   line, the time-window edge, tag-based classification, and a BOM or empty stream.
4. **Rule for future sittings:** no hand-written grep, count or filter in an owner block when a tool can carry it. A new
   check goes into a tool with a test first.

### Key context

- **The running record.** It is the sitting's evidence trail and is gitignored. There are two copies:
  - `tmp/phase-d-sitting/running-record.md` in the worktree
    `juniper-ml/.claude/worktrees/parallel-strolling-meteor`;
  - an archive copy at the same relative path in the **primary** checkout's `tmp/`, which survives `git worktree
    remove`.

  It holds hash prefixes, so it stays out of git.
- **The new scripts, committed by this PR:**
  - `util/key_escrow.bash` and `util/secure_copy-to-clipboard.bash` (step 9);
  - `util/ad-hoc/2026-11-09_ac4_restore_drill.py` (AC-4).

  They resolve the owner's home through `getent`/`pwd` (the G5 home-path gate), never as a literal. The drill's
  self-test is `tmp/phase-d-sitting/drill_selftest.py` (gitignored), which the probe's test suite should absorb.
- **Old drill tool, superseded for AC-4:** `util/ad-hoc/duplicati_drill_fresh.py`. It puts the passphrase on argv
  through `duplicati-aescrypt d <pw>`, drills only the newest dlist, passes the deprecated `--no-local-blocks`, and its
  scratch default `/media/pcalnon/temp_backups` is unmounted.
- **Destination modes are mixed.** 877 pre-recovery volumes are `770 pcalnon:duplicati`. The post-recovery ones were
  `640 duplicati:duplicati`, but on 11-09 every listed dlist read `770 pcalnon:duplicati`, and the cause is unknown. The
  probe should record modes daily.
- **The report URL (S-8, O-13 "keep").** It lives in the server's console-connection settings, which neither `export`
  nor the default options show. Since the B3 save it is also in the job, as `send-http-url`.
  - Neither post-recovery run result carried a report warning. The report is sent after the result is final.
  - Never print either value: `send-http-url` carries the bearer token.
- **Findings for the record PR (§6.3.1)**, in addition to the predecessor handoff's list:
  - the escrow-stub defects;
  - the wl-copy `TMPDIR` buffer, which is now pinned to `XDG_RUNTIME_DIR`;
  - the session's `cmp` slip on a secret file;
  - the session's own mistakes: the grep pattern with `via`, and the `--since` cut;
  - the report URL hidden from `export` and the defaults;
  - the classifier lesson (classify by tag, never by free text);
  - `.env` at 664;
  - the UI save's side effects (`send-http-url`, the `Time` shift);
  - the AC-3 rebaseline and Q1;
  - the AC-7 gid gap;
  - the 23:41Z UI-session run;
  - the drill tool's gaps and their fixes;
  - AC-14 blind (no `--log-console`).
- **The limits still bind** (predecessor handoff):
  - the session never starts or stops units, runs a Duplicati binary, contacts `:8300`, uses `sudo`, or reads a secret
    file;
  - nothing under `/mnt/Backups/Ubuntu/` beyond `stat`;
  - no `/tmp`; root scratch goes in `/root/phase-d-tmp`;
  - pastes are counts and summary lines only.

---

## Verification commands (start of the next thread)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch -q origin && git log -1 --oneline origin/main
ls util/key_escrow.bash util/secure_copy-to-clipboard.bash util/ad-hoc/2026-11-09_ac4_restore_drill.py
tail -n 20 tmp/phase-d-sitting/running-record.md
systemctl show duplicati.service -p ActiveState -p NRestarts
systemctl list-timers yamaguchi-server-db-snapshot.timer --no-pager | head -2
journalctl --user -u yamaguchi-watchdog.service --since -3days -o cat | grep -E ' (OK|FAIL|STALE|JOB_MISSING) ' | tail -n 3
for p in $(pgrep -x dropbox); do grep -E '^(Gid|Groups)' /proc/$p/status; done
```

**Expect:**

- the three scripts are present;
- the record's last lines describe the J1 re-run and the J2 block;
- `active`, `NRestarts=0`;
- the next timer fire at 13:45 UTC;
- the watchdog showing `OK` lines;
- the Dropbox `Gid` or `Groups` line including `139`.

## Git status at handoff

- **Branch:** `docs/backup-phase-d-sitting-handoff-2026-11-11`, opened from `origin/main` through
  `util/open_signed_pr.py`. It adds this handoff and the three scripts.
- **Worktree:** `parallel-strolling-meteor` (branch `worktree-parallel-strolling-meteor`, at the old base `50d2b229`).
  It has no other uncommitted work.
- **Its `tmp/`** holds the running record and the drill self-test. **Do not remove it** until the record PR has merged:
  the primary checkout's `tmp/` copy of the record is the backup.
