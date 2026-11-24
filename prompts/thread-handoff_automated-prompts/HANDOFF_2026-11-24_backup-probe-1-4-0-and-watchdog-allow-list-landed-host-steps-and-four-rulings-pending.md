# Handoff: backup Phase D follow-up -- C.1 and C.3 landed (probe 1.4.0, the watchdog's warning allow-list); the Overtoad's host steps and four rulings pending; the "14:00Z daily" fix, C.2 and E next

**Date**: 2026-11-24 (facts read between 12:23Z and 13:50Z unless a time is given)
**Session**: e8efc11a, host yamaguchi, worktree `R` = `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/radiant-marinating-seahorse`.
**Predecessor, on `main`**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_backup-ac5-not-passed-runs-slowed-io-class-ruled-host-steps-and-probe-fixes-next.md`
(below: the 11-24 predecessor; juniper-ml#2622). Its Limits and traps still hold except where this file says otherwise. **This file's
status list replaces its steps A to E.**

`…RECOVERY-PLAN.md` is `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`; `D` is
`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`.

---

## Goal statement

1. **Confirm the Overtoad's host steps** (step A below, the 11-24 predecessor's, unchanged). They had **not** run at 13:47Z.
2. **Get the Overtoad's four step-D answers**, asked in text in this session at about 12:53Z and unanswered at handoff: Q4,
   the Q6 classes, Q1's size bound, and which fileset is partial (optional). Text, not a dialog: a dialog blocks the session.
3. **Code, one PR each**: the "14:00Z daily" messages (ready to do); C.2 once the size bound is ruled; the Q6 classes once named.
4. **Watch AC-5** (step B) and ask for the probe's redeploy (1.4.0 is merged; the deployed copy is still 1.3.0).
5. **E**: the C.11 items and Phase E.

The working pattern holds: the Overtoad runs every command that changes the host or reaches the server and pastes summary
lines; the session checks read-only and names each next command with its expected output. Ask the Overtoad for merge approval
again in a new session (this session's grant covered its own PRs only).

### What this session did

- **Reviewed the technical-owner sweep** (juniper-ml#2632, a peer session's; MERGED 13:20:45Z as `c93914a7`) for the backup
  files, and held juniper-ml merges for its window at the peer's request. The sweep would have broken
  `tests/test_yamaguchi_acceptance_probe.py:580`, a needle asserting the probe's snapshot message, and it had missed two
  technical owners at `util/ad-hoc/2026-11-11_phase_d_tools_mutation_check.py:193` and `:207`. The peer adopted all three.
- **C.1 = juniper-ml#2633, MERGED 13:42:44Z as `ac60acc8`** (the auto-merge net, required checks green): probe 1.4.0,
  finding 42. A 400 to the job log while a task of THIS job is active no longer stops the server criteria. AC-2, AC-13,
  `OPTIONS` and `CENSUS` are judged as usual, and `OFFSCHED` reads `SKIP`. `RUN` names the run and reads `SKIP`, or `FAIL`
  when the newest finished backup began more than 50 h earlier. It reads that start from the job's metadata
  (`LastBackupStarted`, form `20261107T212907Z`, which the 2026-11-08 census read; the census values are now in finding 42).
  Any other refusal still reads `ERROR`. Replayed: `SKIP` on 11-19 and 11-22, `FAIL` on 11-21. 115 tests; 101/101 probe
  mutants killed.
- **C.3 = juniper-ml#2634, MERGED 14:01:33Z as `3ec619a8`** (squash, required checks green): the watchdog's `ACCEPTED_WARNING_CLASSES`, **empty**. A `Warning` run whose every warning is
  of an accepted class reads `OK WARNINGS_ACCEPTED`, which the probe's AC-5 already counts. `NOT_SUCCESS` now names the
  warning tags, never their text. 35 watchdog tests; 49/49 mutations of `util/ad-hoc/2026-10-03_b2_mutation_check.py`.
- **Read for step D**: the 11-16 run's three warnings were exactly the Firefox-profile class of AC-3's 11-08 ruling (the
  probe's 11-16 `RUN` line: `FileBlockProcessor.FileEntry-PathNotFound`, `FilePreFilterProcess.FileEntry-PathNotFound`,
  `MetadataGenerator.Metadata-MetadataProcessFailed`, one each, all under `~/.mozilla/firefox/`). And Q1's size half cannot be
  coded as an absolute ±5 % check: the newest run's bytes were 13.2 % over the 11-08 baseline (340.9 GB against 301.1 GB).

### Status

- AC-1 `PASS`. AC-5 `FAIL` (newest watchdog line: 11-23 20:00 CST `ALERT STALE`). AC-7 `FAIL` as ruled. AC-9 not judged.
- Ruled: Q1 (run-to-run count; the size half's bound is open), Q2, Q3, Q6 (both halves; no class accepted yet), Q7, Q8, the
  slow-run remedy. Open: Q4.
- Host at 13:47Z: still the idle class (`DropInPaths=` empty; 30 server threads `idle`), the crontab still `7 6 * * *`, today's
  `clamscan` (pid 4128326, since 06:07 CST, nice 0, best-effort 4) running. The 13:00Z run was in progress (the server used
  about one CPU core at 13:07Z).

### Remaining work, in order

**A. The Overtoad's host steps**, verbatim from the 11-24 predecessor (its step A, with its session check and expected output).
Also offered, for today's scan: `renice -n 19 -p 4128326 && ionice -c3 -p 4128326` (own process, no `sudo`). `ionice -u` changes
running threads, so the steps still help mid-run.

**D. The Overtoad's answers** (re-ask in text if none came):

1. Q4, the drill sample: one `~/Pictures/Screenshots/*.png`, restored into a root-only directory and shredded. (a) no exclusion
   (recommended), (b) exclude `Pictures/`.
2. Q6's classes: (a) accept the Firefox-profile class above for AC-5 (recommended), (b) read the 11-09, 11-10 and 11-11 22:14Z
   runs' warnings in the UI first, (c) none yet.
3. Q1's size bound: (a) bytes run-to-run ±10 % plus a floor at the baseline less 5 % (286 GB; recommended), (b) rebaseline to
   the newest run and keep ±5 %, (c) leave the size as `ATTN`.
4. Optional: which of `20260915T204850Z` and `20260916T183346Z` is partial (`IsFullBackup`).

**C'. Code** (each its own PR; the shared-file trap below):

1. **The "14:00Z daily" messages** → 13:00Z: `util/ad-hoc/yamaguchi_server_db_snapshot.py:174` and
   `util/ad-hoc/yamaguchi_reboot_verify.bash:156`. No test pins either. D's line 3155 calls the message stale (leave D's pinned
   passages alone: `tests/test_clear_stop_backup_design.py`); `…RECOVERY-PLAN.md`'s "Still open" names it. The installed
   snapshot copy needs the Overtoad's redeploy.
2. **C.2** per the size ruling: `judge_run`'s count drift becomes `FAIL` outside ±10 % (Q1 is ruled), the size per the bound;
   drop "question Q1 is unruled" from both messages; probe 1.5.0; tests at the edges; harness mutants.
3. **The Q6 classes**, once named: `ACCEPTED_WARNING_CLASSES` in `util/ad-hoc/yamaguchi_watchdog.py` (key, scope). It reaches
   the watchdog only when the primary checkout holds it (finding 44).

**B. Watch** (read-only, daily): the probe's `RUN` line, the watchdog's 20:00 CST line, and
`python3 -I util/ad-hoc/2026-11-23_backup_slowdown_evidence.py`. AC-5 needs three consecutive `OK OK` (or `OK WARNINGS_ACCEPTED`)
checks. **Ask for the probe's redeploy**: `bash util/ad-hoc/yamaguchi_acceptance_probe_deploy.bash --backup-id 2` from a checkout
holding `ac60acc8` (it prints the SHA-256 of what it deployed).

**E. C.11 and Phase E** (the 11-24 predecessor's step E, less the snapshot message): the AC-4 driver's gaps (finding 29); §6.4
step 4's check text (finding 33); `util/safe_merge.py`'s commit text (finding 37); Phase E (§6.5).

### Traps found this session

- **The rehome tool conflicts on ADJACENT lines** (`util/ad-hoc/2026-11-12_rehome_worktree_edits_on_new_main.py`, through
  `git merge-file`), even when the neighbouring change is identical on both sides. For `CHANGELOG.md` (a newer entry at the
  same spot) and the plan's "Still open" lines: save your copy, `git checkout --` the file, rehome, `diff` main's against yours,
  and restore yours only if the diff is exactly your hunk; for the CHANGELOG, re-insert your entry instead.
- **`util/ad-hoc/2026-10-03_b2_mutation_check.py` mutates the working tree in place** (restored by sha256). Never run it beside
  `util/ad-hoc/2026-11-11_phase_d_tools_mutation_check.py`, which copies `yamaguchi_server_api.py`, the watchdog and the stub at
  its start.
- **`util/ad-hoc/2026-10-05_codeql_python_prescreen.py` takes paths only**: `--help` is read as a path.
- **The worktree guard refuses `{ …; } > file` groups and `while read` loops that name git**: use the Write tool or split.
- Finding 42's fix rests on a correlation (3 of 3 run days); why the server answers 400 was not read.

### Limits (unchanged, from the 11-24 predecessor)

Never start, stop, restart, enable, disable or reload a unit; never run a Duplicati binary, never contact 127.0.0.1:8300, no
`sudo`; nothing under `/mnt/Backups/Ubuntu/` beyond `stat`; never read a secret file or print an environment variable or a token;
no `git stash`, no interactive shells, no host actions. Pastes carry counts and summary lines only; never print `send-http-url`,
`TargetURL` or a warning's text. No file is written under `/tmp`.

## Verification commands (start of the next thread)

```bash
gh pr view 2634 --repo pcalnon/juniper-ml --json state,mergedAt,mergeCommit --jq '"\(.state) \(.mergedAt) \(.mergeCommit.oid)"'
date -u
systemctl show duplicati.service -p DropInPaths -p IOSchedulingClass -p NRestarts --no-pager
ionice -p "$(systemctl show -p MainPID --value duplicati.service)"
crontab -l | command grep -o -E '^[0-9]+ [0-9]+ \* \* \* (nice -n 19 ionice -c3 )?/usr/bin/clamscan'
tail -n 3 /home/pcalnon/.local/state/duplicati/server-watchdog.log | cut -c1-140
journalctl --user -u yamaguchi-acceptance-probe.service --since yesterday -o cat | command grep -E '^(== |RUN|AC-5|RESULT)' | cut -c1-200
```

**Expect**: `MERGED 2026-11-24T14:01:33Z 3ec619a8…` for #2634; the drop-in and `best-effort: prio 7` once step A has run; the probe's banner reading 1.4.0 only
after the redeploy; the 11-24 20:00 CST watchdog line, which depends on whether today's run ends before then.

## Git status at handoff

- `main` holds #2633 (`ac60acc8`) and #2634 (`3ec619a8`). `R` is at `3ec619a8` with nothing unmerged but this file.
- This file goes in on its own PR.
- `R`'s `tmp/` holds both PRs' drafts (`c1-pr/`, `c3-pr/`) and the rehome scratch copies: keep them under the retention rule
  in the parent `AGENTS.md`, with the predecessors' worktrees (`modular-gathering-squirrel`, `goofy-painting-rabin`,
  `swift-stargazing-spindle`, `swirling-skipping-turtle`, `parallel-strolling-meteor`).
- The auto-memory index `MEMORY.md` is 22,401 bytes: the compaction toward 20 KB is still owed (retire closed arcs' lines into
  `project_closed_arcs_hub.md` verbatim; never strip hooks).
