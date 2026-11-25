# Handoff: backup Phase D follow-up -- step E's three findings landed or armed (29 ml#2652, 33 ml#2653, 37 ml#2656); AC-5 day 1 of 3; the Overtoad's host steps still to run; a Phase E runbook next

**Date**: 2026-11-25 (facts read between 01:49Z and 03:06Z unless a time is given)
**Session**: 281261dd, host yamaguchi, worktree `K` = `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/cosmic-orbiting-kernighan`.
**Predecessor, on `main`**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-25_backup-rulings-landed-watchdog-class-and-probe-1-5-0-host-steps-and-e-items-next.md`
(below: the 11-25 predecessor; juniper-ml#2649). Its Limits and traps still hold except where this file says otherwise. **This file's
status list replaces its steps 1 to 4.**

`…RECOVERY-PLAN.md` is `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`; `D` is
`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`.

---

## Goal statement

1. **Confirm juniper-ml#2656 merged** (finding 37; `safe_merge --execute` was waiting on it at handoff, its net armed with no
   body). If it is not merged, read why before re-arming.
2. **Confirm the Overtoad's host steps**, re-given in this session at about 01:58Z and not run by 03:05Z:
   - **Step A**, verbatim from `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_backup-ac5-not-passed-runs-slowed-io-class-ruled-host-steps-and-probe-fixes-next.md`, its step A (the drop-in, `ionice -u`, the `clamscan` crontab line), with its session check.
   - **One combined round** (pull, hashes, snapshot copy, probe redeploy), below. #2648 is merged, so the predecessor's rounds 1 and 2 are one.
3. **Watch AC-5**: day 1 is the 11-24 20:00 CST check, `OK OK`. Days 2 and 3 are the 11-25 and 11-26 checks (02:00Z on 11-26
   and 11-27). The 11-25 run starts at 13:00Z.
4. **Phase E** (`…RECOVERY-PLAN.md` §6.5): write its runbook first, one owner command per step with each step's session check,
   as `notes/JUNIPER_2026-10-29_JUNIPER-ECOSYSTEM_BACKUP-PHASE-D-STEP0-TRIAL-AND-KEY-WRITE-RUNBOOK.md` did for Phase D. Every
   step is the Overtoad's on the host; the session designs and checks.

The working pattern holds: the Overtoad runs every command that changes the host or reaches the server and pastes summary
lines; the session checks read-only and names each next command with its expected output. Ask the Overtoad for merge approval
again in a new session (this session's grant covered its own PRs only).

### What this session did

- **ml#2652, MERGED 02:29:29Z as `ad19fa19`** (finding 29, driver 1.1.0), by the armed net:
  - `restore_ok()` admits only 0, 1 and 2, so a restore killed by a signal fails, as the finish tool already judged it.
  - `eligible()` refuses a path any of whose characters does not print.
  - `stratum_of()` gives no stratum to a size that is not a non-negative int, so a missing size no longer raises `KeyError`.
  - The BOM is built with `chr(0xFEFF)`, and the driver's source holds no character that does not print.
  - `tests/test_ac4_restore_drill.py` has 28 tests. `util/ad-hoc/2026-11-11_phase_d_tools_mutation_check.py` now runs the
    driver's suite and seeds 14 driver mutants: 261/261 killed.
- **ml#2653, MERGED 03:03:23Z as `b3c57641`** (finding 33), by the armed net: §6.4 step 4 counts the non-comment lines (1) and
  `cmp`s the installed `/etc/default/duplicati` with `util/systemd/duplicati.default`. Read on the host: plain count 2,
  non-comment 1, `cmp` identical. Its first `safe_merge` exited 3 on an api.github.com connection error, after it had already
  run update-branch; the re-run saw the merge through.
- **ml#2656, OPEN and armed at handoff** (finding 37): `util/safe_merge.py`'s local merge copies a net's stored non-empty
  `commitHeadline` and `commitBody` (`stored_commit_text`, read after the wait); a `null`, `""` or non-string is never copied, and
  arming is unchanged. gh 2.46.0's source (`pkg/cmd/pr/merge/http.go` at tag `v2.46.0`) sends `--subject`/`--body` on
  `mergePullRequest`. `tests/test_safe_merge.py` 84 tests; `util/ad-hoc/2026-11-25_safe_merge_commit_text_mutation_check.py`
  kills 9/9. Its six files: `util/safe_merge.py`, `tests/test_safe_merge.py`, that new script, `…RECOVERY-PLAN.md`,
  `docs/REFERENCE.md`, `CHANGELOG.md`.
- **Read**:
  - The 11-24 20:00 CST watchdog line: `OK OK` (newest backup 2026-11-24T13:00:00Z, `Success`, 13.0 h): AC-5's first day.
  - **The evidence on the slow runs changed.** The 11-24 run took 4 h 19 m under the idle class, with that day's `clamscan`
    (pid 4128326, nice 0, started 06:07 CST on 11-24; still running at 03:05Z on 11-25, 15.0 h) scanning throughout. `/home`'s
    disk (`sdb`) was 36.8 % busy in the 07:00-19:00 CST window, against 64-79 % on 11-19 to 11-23
    (`util/ad-hoc/2026-11-23_backup_slowdown_evidence.py`). The ruled remedy stands; the slow days' cause is not isolated.
  - The primary checkout is on `main` at `f41b1d07`, behind by every PR since. A read-only pre-check
    (`K/tmp/session-281261dd/primary_pull_precheck.py`, at 02:00Z) found nothing in the way of `git pull --ff-only`.
  - For Phase E: `systemd-analyze security duplicati.service` reads **1.7 OK** on the interim unit (AC-12
    wants at most 2.0); O-9 is ruled (10-25: re-encrypt the frozen set and the old dlists as a second pass of §10.2); D-14's step
    runs `util/ad-hoc/2026-09-21_backup_destination_permissions.bash` (a scratch directory on `sda1` first, and only while
    `dropbox status` reads up to date; D §8 P2).

### Status

- AC-1 `PASS`. AC-5: 1 of 3 (`OK OK` on 11-24). AC-7 `FAIL` as ruled. AC-9 not judged. AC-12 read 1.7 (not judged).
- Host at 03:05Z: the idle class (`DropInPaths=` empty, `IOSchedulingClass=3`), the crontab `7 6 * * *` with no nice, the
  snapshot script 1.2.0 (`8fa7bb24…`), the probe 1.3.0 (`9baec4ec…`), the primary's watchdog `9c49dc0a…` (pre-#2645).

### Remaining work, in order

**A. The Overtoad's steps** (re-give whatever has not run):

- Step A: as in the goal statement. Its session check: `systemctl show duplicati.service -p DropInPaths -p IOSchedulingClass -p IOSchedulingPriority -p NeedDaemonReload -p NRestarts --no-pager` and `ionice -p "$(systemctl show -p MainPID --value duplicati.service)"`; expect the drop-in, class 2, priority 7, `NeedDaemonReload=no`, `NRestarts=0`, `best-effort: prio 7`; then `crontab -l | command grep -c '^0 21 \* \* \* nice -n 19 ionice -c3 /usr/bin/clamscan '` = 1.
  - **Raised, not answered**: cron starts each day's scan whether or not the last is still running, and in the idle class a
    scan can outlast a day, so scans can pile up. A `flock -n <lockfile>` prefix prevents it but departs from the ruled line:
    the Overtoad's call. Installed before 21:00 CST while a scan runs, the new line also starts a second scan that evening.
- The combined round:

  ```bash
  cd ~/Development/python/Juniper/juniper-ml && git pull --ff-only
  sha256sum util/ad-hoc/yamaguchi_watchdog.py util/ad-hoc/yamaguchi_server_db_snapshot.py util/ad-hoc/yamaguchi_acceptance_probe.py
  sudo install -m 0755 -o root -g root util/ad-hoc/yamaguchi_server_db_snapshot.py /usr/local/lib/duplicati/yamaguchi_server_db_snapshot.py
  sha256sum /usr/local/lib/duplicati/yamaguchi_server_db_snapshot.py
  bash util/ad-hoc/yamaguchi_acceptance_probe_deploy.bash --backup-id 2
  ```

  Expect `aa789a22…` (watchdog), `c3aebdc6…` (snapshot, both copies) and `7d87e6f9…` (probe 1.5.0). Then the deploy prints
  `NOTE: the first run did not read PASS` (AC-5 and AC-7 still fail), `sha256 7d87e6f9…`, `sha256 756b41f6…`
  (`yamaguchi_server_api.py`), and a first-run banner reading `1.5.0`. The snapshot goes in by itself:
  `util/install_duplicati_service.bash` would also replace the unit's interim `UMask=0017`. A refused pull is the Overtoad's to
  resolve; do not suggest forcing it.

**B. Watch** (read-only, daily): the probe's `RUN` line, the watchdog's 20:00 CST line, the evidence script. AC-5 reads `PASS`
after three consecutive `OK OK` (or `OK WARNINGS_ACCEPTED`) checks.

**E. Phase E** (`…RECOVERY-PLAN.md` §6.5), a runbook first. What is known before writing it:

1. P1: S-4's in-tree delete and dropbox.com "Delete forever" need the Overtoad's sign-off; the account audit (2FA, linked
   devices, third-party apps, retention: D's note S-4a) is the Overtoad's. The user-lane removal PR is D's P4 step 4, after
   seven consecutive successful daily runs: not yet.
2. P2: D-14's permission step; Dropbox restarted in a session carrying gid 139 (AC-7); the watchdog redeploy with the backup id
   (AC-5); AC-12; the reboot test (AC-9). AC-7's offsite route under the Q3 ruling is still open, and a Dropbox client start
   re-owns the volumes to `pcalnon` (finding 43): ask the Overtoad before the runbook fixes an order.
3. §10.2, the D-2 rotation, then O-9's second pass. AC-4's first drill passed on 11-15, which unblocked it.
4. P4 after seven consecutive successful daily runs; `/etc/default/duplicati.bak-20260830-010814` goes then too.

### Traps found this session

- **`safe_merge` can exit 3 after it has already acted.** Its `wait_for_checks` failed three times connecting to api.github.com
  after a BEHIND re-sync had moved the head (#2653: `0b91adab` → `d379ecef`). The armed net survived. Read
  `gh pr view <N> --json headRefOid,autoMergeRequest,mergeStateStatus` first, then re-run it.
- **Two PRs that edit one line must land in sequence.** #2652, #2653 and #2656 each changed `…RECOVERY-PLAN.md`'s "Still open"
  line, and the uploads are whole files. Build each from the `main` that holds the one before; restore the merged files with
  `git checkout --` only after `git diff --stat origin/main -- <files>` reads empty.
- **A file untracked in the worktree reads as deleted** in `git diff <branch> -- <path>`. Compare it with `git show <branch>:<path>`
  into a file and `cmp`.
- **The phase-D harness by file**: `--file phase_d_finish` covers the finish tool and its wrapper (133), `--file
  yamaguchi_acceptance_probe` the probe and its deploy script (112), `--file retention_table` (2), `--file ac4_restore_drill` (14).
  Every run's baseline runs all its suites, and runs side by side are safe because each copies its files.
- **The host's `tail` is uutils**: `tail -2 a b` errors (use `tail -n 2`). `xargs command grep` fails; use `xargs /usr/bin/grep`.
- **The worktree guard** refused `git -C <primary>` and compound commands that name git, including a `for` loop around `curl`.
  Read the primary's head from its `.git/HEAD` and `.git/refs/heads/main`, and compare its files through a script under `K/tmp/`.

### Limits (unchanged, from the 11-24 predecessor)

Never start, stop, restart, enable, disable or reload a unit; never run a Duplicati binary, never contact 127.0.0.1:8300, no
`sudo`; nothing under `/mnt/Backups/Ubuntu/` beyond `stat`; never read a secret file or print an environment variable or a token;
no `git stash`, no interactive shells, no host actions. Pastes carry counts and summary lines only; never print `send-http-url`,
`TargetURL` or a warning's text. No file is written under `/tmp`.

## Verification commands (start of the next thread)

```bash
gh pr view 2656 --repo pcalnon/juniper-ml --json state,mergedAt,mergeCommit --jq '"\(.state) \(.mergedAt) \(.mergeCommit.oid)"'
date -u
systemctl show duplicati.service -p DropInPaths -p IOSchedulingClass -p NRestarts --no-pager
ionice -p "$(systemctl show -p MainPID --value duplicati.service)"
crontab -l | command grep -o -E '^[0-9]+ [0-9]+ \* \* \* (nice -n 19 ionice -c3 )?/usr/bin/clamscan'
tail -n 3 /home/pcalnon/.local/state/duplicati/server-watchdog.log | cut -c1-140
journalctl --user -u yamaguchi-acceptance-probe.service --since yesterday -o cat | command grep -E '^(== |RUN|AC-5|RESULT)' | cut -c1-200
sha256sum /usr/local/lib/duplicati/yamaguchi_server_db_snapshot.py /home/pcalnon/Development/python/Juniper/juniper-ml/util/ad-hoc/yamaguchi_watchdog.py ~/.local/lib/yamaguchi-acceptance/yamaguchi_acceptance_probe.py
```

**Expect**:

- `MERGED` for #2656.
- The drop-in and `best-effort: prio 7` once step A has run.
- The 11-25 20:00 CST watchdog line (02:00Z on 11-26), `OK OK` if that day's run ended before then.
- `c3aebdc6…`, `aa789a22…` and `7d87e6f9…` once the round has run, and a probe banner reading 1.5.0.

## Git status at handoff

- `main` holds #2652 (`ad19fa19`) and #2653 (`b3c57641`). #2656's branch is `fix/safe-merge-local-merge-commit-text`
  (`232bdc38`).
- `K` is at `b3c57641`, with #2656's five modified files and its new script, identical to that branch. This file goes in on its
  own PR.
- `K/tmp/session-281261dd/` holds the three PRs' drafts and `safe_merge` logs (`f29-pr/`, `f33-pr/`, `f37-pr/`), the harness logs,
  the pull pre-check and gh v2.46.0's two downloaded source files. Keep them under the retention rule in the parent `AGENTS.md`,
  with the predecessors' worktrees (`staged-mapping-lerdorf`, `radiant-marinating-seahorse`, `modular-gathering-squirrel`,
  `goofy-painting-rabin`, `swift-stargazing-spindle`, `swirling-skipping-turtle`, `parallel-strolling-meteor`).
- The auto-memory index `MEMORY.md` is about 22.8 KB, over the Overtoad's 20 KB target: a compaction by retiring entries is
  still owed (`feedback_memory_index_target_is_20kb.md`; the hook's 17.1 KB is not the target).
