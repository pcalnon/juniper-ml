# Handoff: backup Phase D follow-up -- the Overtoad ruled Q4, Q6's classes and Q1's size bound; the watchdog's class (ml#2645) and the stale times (ml#2642) landed, probe 1.5.0 (ml#2648) armed; the host steps, the redeploys and step E next

**Date**: 2026-11-25 (facts read between 2026-11-24T21:32Z and 2026-11-25T00:45Z unless a time is given)
**Session**: 78bcb8ef, host yamaguchi, worktree `S` = `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/staged-mapping-lerdorf`.
**Predecessor, on `main`**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_backup-probe-1-4-0-and-watchdog-allow-list-landed-host-steps-and-four-rulings-pending.md`
(below: the 11-24 predecessor; juniper-ml#2636). Its Limits and traps still hold except where this file says otherwise. **This file's
status list replaces its steps A to E.**

`…RECOVERY-PLAN.md` is `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`; `D` is
`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`.

---

## Goal statement

1. **Confirm juniper-ml#2648 merged** (probe 1.5.0; `safe_merge --execute` was waiting on it at handoff). If it is not merged,
   read why before re-arming (see the traps).
2. **Confirm the Overtoad's host steps.** At 21:45Z on 11-24, none had run:
   - **Step A**: the 11-24 predecessor's step A, verbatim from ITS predecessor (the drop-in, `ionice -u`, the `clamscan` crontab line).
   - **Round 1**: pull the primary checkout and copy the snapshot script (given in the session at about 00:30Z). Below.
   - **Round 2**, after #2648: redeploy the probe from the pulled primary. Below.
3. **Watch AC-5** (step B of the 11-24 predecessor). It needs three consecutive `OK OK` (or `OK WARNINGS_ACCEPTED`) checks
   at 20:00 CST. 11-24's run ended `Success` (4 h 19 m, the 23:30Z probe), so the 11-24 20:00 CST check (02:00Z on 11-25)
   should read `OK OK`: the first of the three.
4. **Step E, one PR each**: findings 29, 33 and 37 of `…RECOVERY-PLAN.md`, then Phase E (§6.5).

The working pattern holds: the Overtoad runs every command that changes the host or reaches the server and pastes summary
lines; the session checks read-only and names each next command with its expected output. Ask the Overtoad for merge approval
again in a new session (this session's grant covered its own PRs only).

### What this session did

- **juniper-ml#2642, MERGED 22:36:01Z as `08cc7032`**: the "14:00Z daily" item (C'.1). Text only:
  - `util/ad-hoc/yamaguchi_server_db_snapshot.py` 1.2.1 says 13:00Z.
  - `util/ad-hoc/yamaguchi_reboot_verify.bash` names 13:00Z and the 20:00 watchdog.
  - `util/systemd/yamaguchi-acceptance-probe.timer`'s comment says 13:00 UTC.
- **The Overtoad's rulings, answered by 22:31Z as "1a 2a 3A"** (asked in text). They are in `…RECOVERY-PLAN.md` §6.6's new 11-24 table:
  - Q4: no exclusion.
  - Q6's classes: AC-3's Firefox-profile class, three keys under `~/.mozilla/firefox/`.
  - Q1's size bound: bytes within ±10 % of the previous run, plus a floor at the 2026-11-08 baseline less 5 % (286 GB).
  - Every question of the sitting is now ruled.
- **juniper-ml#2645, MERGED 2026-11-25 00:29:02Z as `673d208f`** (C'.3): the watchdog's `ACCEPTED_WARNING_CLASSES` holds
  those three keys, pinned by a test to the probe's `ALLOWED_WARNING_TAGS` and `ALLOWED_WARNING_SCOPE`. 37 watchdog tests;
  52/52 mutations of `util/ad-hoc/2026-10-03_b2_mutation_check.py`.
- **juniper-ml#2648, OPEN and armed at handoff** (C'.2, probe 1.5.0):
  - `RUN` reads `FAIL` when files or bytes move more than 10 % from the previous run, or the bytes fall under the floor. An
    exact edge is inside.
  - A count the result lacks reads `ERROR`. `OFFSCHED` is the only criterion left that reads `ATTN`.
  - 118 probe tests. The phase-D harness kills 247/247, 111/111 of them probe mutants.
  - Its head commit carries an `Allow-Symbol-Loss:` trailer for the replaced test.
- **Read**: 11-24's 13:00Z run wrote its dlist at 17:13:20Z (`stat` only), the first short run since 11-18. The probe's `RUN`:
  `Success`, files +8.3 %, bytes +15.8 % against the baseline (1.3.0 called that `ATTN`; 1.5.0 passes it).
  - Today's `clamscan` (pid 4128326, nice 0) was still running at 21:46Z (state R, 6 h of CPU in 9 h 42 m), so the slow
    runs' cause is still not isolated.
  - ClamTk's history logs (`~/.clamtk/history/`, mtimes only) put recent scans between about 1 h and 32 h.

### Status

- AC-1 `PASS`. AC-5 `FAIL` (newest watchdog line: 11-23 20:00 CST `ALERT STALE`). AC-7 `FAIL` as ruled. AC-9 not judged.
- Host at 21:45Z on 11-24:
  - The idle I/O class (`DropInPaths=` empty, `IOSchedulingClass=3`), the crontab still `7 6 * * *`, `UMask=0017`.
  - The deployed probe is 1.3.0 (`9baec4ec…`). The installed snapshot script is 1.2.0 (`8fa7bb24…`).
  - The primary checkout is on `main`, but behind: its snapshot script is 1.2.0 and its watchdog `9c49dc0a…` (pre-#2645).

### Remaining work, in order

**A. The Overtoad's steps** (re-give whatever has not run):

- Step A: verbatim from `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_backup-ac5-not-passed-runs-slowed-io-class-ruled-host-steps-and-probe-fixes-next.md`, its step A, with its session check and expected output.
- Round 1:

  ```bash
  cd ~/Development/python/Juniper/juniper-ml && git pull --ff-only
  sha256sum util/ad-hoc/yamaguchi_watchdog.py util/ad-hoc/yamaguchi_server_db_snapshot.py
  sudo install -m 0755 -o root -g root util/ad-hoc/yamaguchi_server_db_snapshot.py /usr/local/lib/duplicati/yamaguchi_server_db_snapshot.py
  sha256sum /usr/local/lib/duplicati/yamaguchi_server_db_snapshot.py
  ```

  Expect `aa789a22…` for the watchdog (main at `673d208f`) and `c3aebdc6…` for both copies of the snapshot. The snapshot
  goes in by itself: `util/install_duplicati_service.bash` would also replace the unit's interim `UMask=0017`. A refused pull
  is the Overtoad's to resolve; do not suggest forcing it.
- Round 2, after #2648 merges: pull the primary again, then `bash util/ad-hoc/yamaguchi_acceptance_probe_deploy.bash --backup-id 2`
  from it. It prints the SHA-256 of the deployed probe (compute it from `main`'s file) and of `yamaguchi_server_api.py`
  (`756b41f6…`). The first run's banner reads 1.5.0.

**B. Watch** (read-only, daily): the probe's `RUN` line, the watchdog's 20:00 CST line, and
`python3 -I util/ad-hoc/2026-11-23_backup_slowdown_evidence.py`. If runs stay short with the idle class still in force, say
so: the ruled remedy stands, but the evidence changed.

**E. One PR each**:

1. **Finding 29**, the AC-4 driver's gaps (`util/ad-hoc/2026-11-09_ac4_restore_drill.py`; suite `tests/test_ac4_restore_drill.py`; the driver is in the phase-D harness's `COPIED`):
   - `returncode < 3` (`:377`; also `:352`) passes a restore killed by a signal, whose return code is negative.
   - `eligible()` (`:197`) admits a path with control characters.
   - `stratum_of(-1)` (`:185`) is `small`, then raises `KeyError`.
   - Line 162 holds a literal U+FEFF.
2. **Finding 33**: §6.4 step 4's `grep -c -- --require-db-encryption-key /etc/default/duplicati` reads 2 on a correct
   install. Count non-comment lines (1), or `cmp` the file with the repository's. This is a `…RECOVERY-PLAN.md` edit.
3. **Finding 37**: `util/safe_merge.py`'s local merge passes no commit text. It is shared by every session: read its
   docstring's three-state `commitBody` analysis first, and keep the fix narrow.
4. **Phase E** (§6.5).

### Traps found this session

- **`util/open_signed_pr.py` cuts the branch from `main` at UPLOAD time.** `main` moved (`42f56b45`) between the fetch and the
  upload, and the whole-file `CHANGELOG.md` reverted its entries. `util/push_signed_commit.py --expected-head` fixed it
  forward. Right after every upload, check that `git diff --stat origin/main origin/<branch>` equals the dangling probe
  commit's stat.
- **`safe_merge`'s 2800 s budget runs out on a busy evening.** The 3.13 and 3.14 legs queued 11 to 14 min, and each
  update-branch restarts CI: #2645 needed three runs. Use `--timeout 5000`, an outer `timeout` above it, and `python3 -u`.
  Without `-u` the log is lost when the timeout kills the run. An armed net that outlives a killed run still merges.
- **The phase-D harness copies its files at start.** An edit made while it runs is not covered: re-run it with
  `--file <name>` on the final file.
- **MyPy (pre-commit) refuses `**dict` into a helper with optional positional parameters**, and a dict of mixed kwargs.
  Pass keywords explicitly.
- **A renamed test is a symbol loss.** Put `Allow-Symbol-Loss: method:<Class>.<test>` in the commit's trailer block, before
  `Co-Authored-By:`.

### Limits (unchanged, from the 11-24 predecessor)

Never start, stop, restart, enable, disable or reload a unit; never run a Duplicati binary, never contact 127.0.0.1:8300, no
`sudo`; nothing under `/mnt/Backups/Ubuntu/` beyond `stat`; never read a secret file or print an environment variable or a token;
no `git stash`, no interactive shells, no host actions. Pastes carry counts and summary lines only; never print `send-http-url`,
`TargetURL` or a warning's text. No file is written under `/tmp`.

## Verification commands (start of the next thread)

```bash
gh pr view 2648 --repo pcalnon/juniper-ml --json state,mergedAt,mergeCommit --jq '"\(.state) \(.mergedAt) \(.mergeCommit.oid)"'
date -u
systemctl show duplicati.service -p DropInPaths -p IOSchedulingClass -p NRestarts --no-pager
ionice -p "$(systemctl show -p MainPID --value duplicati.service)"
crontab -l | command grep -o -E '^[0-9]+ [0-9]+ \* \* \* (nice -n 19 ionice -c3 )?/usr/bin/clamscan'
tail -n 3 /home/pcalnon/.local/state/duplicati/server-watchdog.log | cut -c1-140
journalctl --user -u yamaguchi-acceptance-probe.service --since yesterday -o cat | command grep -E '^(== |RUN|AC-5|RESULT)' | cut -c1-200
sha256sum /usr/local/lib/duplicati/yamaguchi_server_db_snapshot.py /home/pcalnon/Development/python/Juniper/juniper-ml/util/ad-hoc/yamaguchi_watchdog.py
```

**Expect**:

- `MERGED` for #2648.
- The drop-in and `best-effort: prio 7` once step A has run.
- The 11-24 20:00 CST watchdog line: `OK OK`.
- `c3aebdc6…` and `aa789a22…` once round 1 has run.
- The probe's banner reading 1.5.0 after round 2.

## Git status at handoff

- `main` holds #2642 (`08cc7032`) and #2645 (`673d208f`). #2648's branch is `feat/backup-probe-1-5-0-ac3-count` (`0fb76359`).
- `S` is at `673d208f`, with #2648's six files modified, identical to that branch. This file goes in on its own PR.
- `S`'s `tmp/` holds the three PRs' drafts and logs (`stale-times-pr/`, `q6-classes-pr/`, `c2-probe-pr/`). Keep them under
  the retention rule in the parent `AGENTS.md`, with the predecessors' worktrees (`radiant-marinating-seahorse`,
  `modular-gathering-squirrel`, `goofy-painting-rabin`, `swift-stargazing-spindle`, `swirling-skipping-turtle`,
  `parallel-strolling-meteor`).
- The auto-memory index `MEMORY.md` is 23,132 bytes: the compaction toward 20 KB is still owed (retire closed arcs' lines into
  `project_closed_arcs_hub.md` verbatim; never strip hooks).
