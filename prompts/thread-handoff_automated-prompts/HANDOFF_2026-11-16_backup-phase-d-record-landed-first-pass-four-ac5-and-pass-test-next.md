# Handoff: backup Phase D -- the record has landed (the first pass deleted four, not five); AC-5's last day, the second pass's test and the owner's questions next

**Date**: 2026-11-16 (facts read between 07:50Z and 2026-11-16T09:30:10Z unless a time is given)
**Session**: host yamaguchi, worktree `G` = `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/goofy-painting-rabin`
(fast-forwarded to `origin/main` `0961e1ab` at the start, `9d9ec797` later). The running record still lives in `W` =
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swift-stargazing-spindle`.
**Predecessor, on `main`**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_backup-phase-d-c1-to-c9-done-first-retention-pass-then-record-pr.md`
(below: `HANDOFF_2026-11-15_…md`). Its Limits and traps still hold except where this file says otherwise. **This file's
status list replaces its steps A to E.**

---

## Goal statement

1. Read the 2026-11-16 13:00Z run's retention pass. It tests `…RECOVERY-PLAN.md` §6.3.1 finding 18 (step A below).
2. Watch AC-5 complete: the 2026-11-16 20:00 CST watchdog check must read `OK OK` (step B).
3. Record both outcomes with a short follow-up to the record PR (step C).
4. Put the open questions to the owner: Q1, Q4, Q8 and Q6's Warning half (step D). Then the C.11 items (step E).

`…RECOVERY-PLAN.md` is `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`.
The working pattern holds: the owner runs every command that changes the host or reaches the server and pastes summary
lines; the session checks read-only and names each next command with its expected output. Ask the owner for merge
approval again in a new session.

### What this session did

- **Step A of `HANDOFF_2026-11-15_…md`, read from the probe's own files** (read-only; the owner's `status` paste was not
  received). The 2026-11-15 13:00Z run: `Success`, 4h05m, W=0. **Retention deleted 4 filesets, not 5**:
  `20260912T140000Z`, `20260915T085649Z`, `20260917T221344Z`, `20260918T140000Z`. `20260916T183346Z` was kept.
  CENSUS at 23:30Z: 984 files = 18 dlist + 483 dblock + 483 dindex, `AGREE`. Nothing is lost: `aside` holds all 21.
- **Why**: `plan`'s port assumes every fileset is FULL; Duplicati keeps a PARTIAL fileset inside a frame and does not
  measure the next interval from it. The new `util/ad-hoc/2026-11-16_partial_fileset_retention_check.py` replays the
  pass from `~/.local/state/duplicati/acceptance-history.jsonl`: 8 of 32 partial-flag assignments reproduce it, and in
  every one exactly one of `20260915T204850Z` / `20260916T183346Z` is partial (`20260908T140000Z` full in all).
- **The record PR (C.10): juniper-ml#2596, MERGED 2026-11-16T09:30:10Z as `445ebf4e`.** It adds §6.3.1's Phase D part
  (step table, AC table, findings 18-39, "Still open"), §6.6's sitting rulings with notes (e) to (h), §1's status and a
  §9 row, plus the replay script. A fork drafted it; an independent reader validated it (0 critical, 5 major, 22 minor,
  all folded in: `G/tmp/backup-phase-d-goofy/validation-r1.md`); a narrow second round checked the fixes
  (0 critical, 1 major, 6 minor, all folded in by the PR's second commit; the major: a passphrase fingerprint the record
  called gitignored-only has been committed since 2026-08-25; `G/tmp/backup-phase-d-goofy/validation-r2.md`).
- Memory: `project_backup_arc_hub.md` has a 2026-11-16 paragraph; the MEMORY.md line was updated.

### Status

- C.1 to C.10: done. C.4's first pass: done (4 deleted). C.7 (AC-5): 2 of 3 days (11-14, 11-15 `OK OK`).
- C.8 (AC-7): `FAIL` by the Q3 ruling (unchanged). C.11: open (step E).
- Q2, Q3, Q6 (the `OK RUNNING` half), Q7: ruled. Open: Q1, Q4, Q8, Q6's Warning half.
- **Three "still" items of `HANDOFF_2026-11-15_…md` were stale when written** (round 1 measured them): the primary
  checkout was pulled to `eeb5c694` at 2026-11-15T02:04:55Z (it holds #2548 and #2569, not #2583's timers);
  `JuniperCascor1`'s three links were restored at 2026-11-14 18:54 CST; the primary's `.env` is `600` since 11-06.

### Remaining work, in order

**A. The second pass (session, read-only), after the probe's 23:30Z run on 11-16** (`acceptance.json` is overwritten
daily; `acceptance-history.jsonl` keeps every run's dlist names).

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/goofy-painting-rabin
python3 -I util/ad-hoc/2026-11-16_partial_fileset_retention_check.py --before 2026-11-15T23:30:00Z \
    --after 2026-11-16T23:30:00Z --run 2026-11-16T13:00:00Z --duration <the probe's RUN duration, e.g. 4h05m>
```

Expect `observed: 0 deleted`, 19 dlists after, and exit 0 with matches that again put exactly one of the two partial.
**If the pass deletes `20260916T183346Z`**, finding 18's reading is refuted: say so in step C and re-open the cause.
An alternative needing no root: the probe's `RUN` line reads `retention deleted 0 fileset(s)`.

**B. AC-5 (read-only).** `tail -n 3 ~/.local/state/duplicati/server-watchdog.log`: the 2026-11-16T20:00 line must read
`OK OK` on the 13:00Z run. Then AC-5 reads `PASS` from 02:00Z on 11-17; the daily probe first shows it at 23:30Z 11-17.
A `Warning` run resets the streak (Q6's Warning half).

**C. Record A and B**: a short PR into `…RECOVERY-PLAN.md` §6.3.1 (finding 18's test; the AC table's AC-5 row; §1).
Build from `origin/main` blobs; `util/open_signed_pr.py` signs; probe-commit both sequence-safety screens first
(`G/tmp/backup-phase-d-goofy/record_pr.bash` is a template).

**D. The owner's questions** (one dialog, after any time-critical step; it blocks the session until answered):

- Q1, AC-3's count criterion: bytes read +8.7% against the 11-08 baseline (threshold 5%), mostly the owner's source
  change. Options: a per-run comparison (about ±10% a day) plus the absolute size check (the 11-11 recommendation);
  rebaseline on the 11-15 13:00Z run; or keep `ATTN` only.
- Q4, the drill sample's scope (`Pictures/`): recommendation, no exclusion.
- Q8, the aside directory's location: its parent is `770 pcalnon:duplicati`, so either account can rename it; D §7.4
  wants `2750`, Phase E's step. It holds the only copies of the four deleted filesets: never propose deleting it.
- Q6's Warning half: a `Warning` run reads `ALERT NOT_SUCCESS` and resets AC-5; three `Warning` runs (11-09, 11-10,
  11-11 22:14Z; 633 warnings) were never read.
- Optional: which fileset is partial (the owner can read each fileset's `IsFullBackup`).

**E. C.11**: the AC-4 driver's gaps (finding 29); the snapshot script's "14:00Z daily" message
(`util/ad-hoc/yamaguchi_server_db_snapshot.py:174`, `util/ad-hoc/yamaguchi_reboot_verify.bash:156`, and the installed
copy; check whether the installer blesses that file before changing it); §6.4 step 4's check text (finding 33);
`util/safe_merge.py`'s commit text (finding 37); Phase E (§6.5); AC-7's route under Q3.

### Traps found this session

- **`plan` and §6.4 step 14 count every fileset as full.** Use the replay script for any pass that is already observed.
- **A "still" in a handoff is a claim about the past.** Re-measure it before copying it into a record (three were wrong).
- **Worktree isolation refuses `git -C .`, compound commands naming git, and some heredocs.** Put them in a script
  under `G/tmp/` and run that (`G/tmp/backup-phase-d-goofy/verify_pr.bash` checks a PR's signature and blobs).
- **Notes lines may already exceed 512 characters**; check only the lines you change.

### Limits (unchanged, verbatim from `HANDOFF_2026-11-15_…md`)

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
gh pr view 2596 --repo pcalnon/juniper-ml --json state,mergedAt,mergeCommit --jq '"\(.state) \(.mergedAt) \(.mergeCommit.oid)"'
date -u
tail -n 3 /home/pcalnon/.local/state/duplicati/server-watchdog.log | cut -c1-140
journalctl --user -u yamaguchi-acceptance-probe.service --since today -o cat | command grep -E '^(RUN|CENSUS|AC-5|RESULT)' | cut -c1-200
systemctl --user list-timers yamaguchi-acceptance-probe.timer yamaguchi-watchdog.timer --no-pager
```

**Expect**: `MERGED 2026-11-16T09:30:10Z 445ebf4e`; the watchdog's 20:00 CST lines; the probe's lines once 23:30Z has
passed; the probe timer at 17:30 CST and the watchdog at 20:00 CST.

## Git status at handoff

- `main` holds juniper-ml#2596. No PR of this arc is open, except the one that carries this file.
- `G`: on `main` plus this file. Its `tmp/backup-phase-d-goofy/` holds the replay's scratch versions, the fork's
  diff, both validation reports and the frozen copies, `record_pr.bash`, `leak_scan.py` and `verify_pr.bash`.
- **Do not remove `G`, `W`, `D` (`swirling-skipping-turtle`) or `parallel-strolling-meteor` yet**: their `tmp/` hold
  the running record, the validation reports and the tools' evidence (the retention rule in the parent `AGENTS.md`).
