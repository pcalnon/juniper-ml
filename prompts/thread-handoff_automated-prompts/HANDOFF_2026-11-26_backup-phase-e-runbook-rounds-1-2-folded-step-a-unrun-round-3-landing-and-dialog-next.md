# Handoff: backup Phase E -- the runbook's validation rounds 1 and 2 are folded (round 3 and landing owed); step A still not run (the old clamscan line fired at 06:07 CST); the Dropbox design dialog is prepared, not asked

**Date**: 2026-11-26 (facts read between 11:45Z and 14:05Z unless a time is given)
**Session**: 8f4c4170, host yamaguchi, worktree `R` = `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/reactive-dazzling-muffin`.
**Predecessor, on `main`**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-26_backup-phase-e-rulings-route-deferred-runbook-drafted-ac5-day-2-host-steps-owed.md`
(juniper-ml#2670, `8378665f`). Its limits and traps still hold except where this file says otherwise. **This file's goal list replaces its
goal items 1 to 4.**

`A` is `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`; `D` is
`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`; **the runbook** is `R/tmp/phase-e/val-r3/frozen_r3.md`
(1,005 lines, sha256 `12376c0459bd4948…`, 0 problems from `util/ad-hoc/2026-09-05_markdown_structure_check.py`), to land as
`notes/JUNIPER_2026-11-26_JUNIPER-ECOSYSTEM_BACKUP-PHASE-E-RUNBOOK.md`; **the log** is `R/tmp/phase-e/RUNNING_LOG.txt` (every event of this
session with its time).

---

## Goal statement

1. **Step A and the round are still the Overtoad's.** Not run at 14:05Z: no drop-in, idle class, crontab `7 6`, snapshot 1.2.0
   (`8fa7bb24`), probe 1.3.0 (`9baec4ec`). The old line started a clamscan at 06:07 CST (pid 2912875, nice 0, I/O `none: prio 0`),
   still running at 14:05Z, and the 07:00 CST backup started in the idle class. The blocks were given in-session at 11:47Z and are
   the runbook's §2.1 and §2.2, in this order: the scan, `renice -n 19 -p 2912875; ionice -c3 -p 2912875` (no `sudo`); the crontab
   lines (no `sudo`); the I/O class (`sudo ionice -c2 -n7 -u "$(id -u duplicati)"` reaches the running backup too); then the
   snapshot copy (**never at 06:45 CST**, the snapshot's fire) and the probe redeploy. The runbook's §0 now says: one line at a time.
   When the Overtoad pastes, run §2.1's and §2.2's session checks.
2. **AC-5 day 3** is the 11-26 20:00 CST check (02:00Z on 11-27); it needs the 13:00Z run to end `Success` first. AC-5 first reads
   `PASS` at the first probe run after that check: the timer's at 17:30 CST on 11-27 (23:30Z), or §2.2's deploy if it runs after
   02:00Z. Do not predict from CPU; stat the dlist by name (`duplicati-20261126T13000?Z.dlist.zip.aes`). At 14:05Z the destination
   folder had not changed since 11-25 19:50 CST.
3. **Round 3 on the runbook**, then land it. Two fresh lanes, each with a brief file and the rules file
   `R/tmp/phase-e/val-r2/RULES.txt` (copy it to `val-r3/` and change its paths). Lane 1: round 2's corrections, hunk by hunk, from
   `diff -u R/tmp/phase-e/val-r2/frozen_r2.md R/tmp/phase-e/val-r3/frozen_r3.md`. Lane 2: the whole document as the Overtoad will use
   it, plus `git diff` of `A` in `R`. Give the rulings lens the dialog's **full option text**, which is in
   `R/tmp/phase-e/val-r2/lane-y/BRIEF.txt` (round 1 had labels only and missed what the chosen option said). Brief them to write
   `findings.txt` and `fixes.json` (a subagent's `.md` write is refused) and **never to kill any process** (round 1's lane B used
   `pkill`). Apply with `R/util/ad-hoc/2026-11-26_phase_e_runbook_apply_fixes.py`: `--lenient` for the second lane, `--target
   assessment` for fixes to `A`, and read every OVERLAP line it prints (two lanes meeting one span doubled a heading in round 1).
   If round 3 finds a BLOCKER or a MAJOR, run round 4. §12 and the Status line must end recording the last round, never "in
   progress" or "owed".
4. **Land** in one signed PR (`util/open_signed_pr.py`, `--add` each file): the runbook at its `notes/` name; `A` from
   `R/notes/` (its diff against `main` adds the §6.5 pointer, the §6.6 table of the rulings of 2026-11-25 local with footnote (j), the
   "Still open" deferrals, and a §9 row, and removes one stale bullet); and `R/util/ad-hoc/2026-11-26_phase_e_runbook_apply_fixes.py`
   and `R/util/ad-hoc/2026-11-26_phase_e_runbook_rebase_a_citations.py`, which `A`'s §9 row names. Before the push: pre-commit on the
   files, the CodeQL prescreen (`util/ad-hoc/2026-10-05_codeql_python_prescreen.py`) on the two scripts, and a non-vacuous
   `gitleaks dir` scan. Merge with `util/safe_merge.py`, run `python3 -u`. The Overtoad's words to this session at about 11:46Z:
   "merge approval granted for this work arc" (the predecessor recorded the same words). If `main` changes `A` before landing,
   re-run the re-base tool: the runbook's `[A]` line numbers are the PR's version of `A`.
5. **The Dropbox dialog** (ruling 1's investigation, the predecessor's goal 4): ask it after any time-critical step, because a
   dialog blocks the session. If the answers arrive before round 3, fold them in first (the update-before-a-round rule). Prepared,
   four questions:
   - **OI-18, the order.** Ruling 2's question put the route inside P2 ("P2 is the route, D-14, the unit back to UMask 0027, AC-7,
     AC-12 and the AC-9 reboot test"), and its chosen option said "The route and D-14 land next, so AC-7 can pass. The rotation's
     swap then lands once, on the final layout." Ruling 1's chosen option said "The runbook orders everything else first and
     leaves D-14's permission step and the offsite route to a later design." Options: "Everything else first (Recommended)":
     §10.2 and P4 go on today's layout, and the route's D-14 step re-modes the set later. "Rotation waits for the route": §10.2's
     steps 3 to 8, O-9's pass and P4 wait for the route.
   - **OI-24, the route's direction.** Dropbox has no per-tree owner setting, and syncs only what its own uid can write. D-14
     exists so that a cloud-side delete fails loudly [D:1744-1757], and any client that can write the master's directories
     carries that delete in, whichever uid runs it. Options: "Mirror outside Dropbox (Recommended)" (master `0640 duplicati` outside
     the root, a pcalnon-owned one-way copy inside); "Duplicati sync tool" (`duplicati-sync-tool`, installed, one-way, renames
     instead of deleting under `--retention`; D-3's own alternative [D:2992]; a new Dropbox credential and a full re-upload);
     "Dedicated Dropbox user" (a second headless client under a new uid with file-write ACLs only: untested, a second linked device,
     and an overwrite in place still reaches the master).
   - **The owner map.** A list of acceptable owners per tree that the probe checks, plus a local polkit rule refusing the helper's
     whole-root re-own (pkexec(1) warns that `command_line` "is not secure" for checks: a changed command line fails open).
     Options: both (Recommended); the rule only; neither.
   - **OI-21.** Convert the watchdog to an installed copy, as D §7.6 puts in P2 [D:1941-1943]. The primary sat on the Overtoad's
     README branch three times on 11-25 and 11-26. Options: as a P2 item (Recommended); with the route; not needed.
   Record the answers verbatim in `A` §6.6 and the runbook's §1 and §10, quoting what each chosen option said.
6. **Memory**: `MEMORY.md` is about 23 KB, over the Overtoad's 20 KB target; a compaction by retiring entries is still owed
   (`feedback_memory_index_target_is_20kb.md`). This session updated `project_backup_arc_hub.md` and
   `feedback_multi_agent_adversarial_validation_sop.md`, and did not touch the index.

### What this session did

- **Host**: urged step A (push notifications 11:57Z and 12:07Z). Found the primary on `pcalnon-patch-1-1` three times in its reflog
  (19:28Z-20:09Z and 20:21Z-01:16Z on 11-25/26, 10:40Z-11:31Z on 11-26). No 02:00Z check fell inside, and every tip carried `main`'s
  watchdog (`aa789a22`). The primary is on `main` since 11:31Z.
- **Validation**: a pre-launch pass, then round 1 (lanes A, B and C: 26, 22 and 19 findings, two BLOCKERs) and round 2 (lanes X and
  Y: 31 and 26, two BLOCKERs), all folded. The runbook's §12 records both. Each lane's `findings.txt` and `fixes.json` are under
  `R/tmp/phase-e/val-r1/` and `val-r2/`.
- **What the draft and the predecessor had wrong**, now corrected in the runbook:
  - The probe's CENSUS does record the set: 252,057,774,864 B (234.7 GiB, 1,024 files) on 11-24. Staging plus `recompress`'s
    `<localfolder>`, which downloads the whole set again, needs about 470 GiB against 264 G free on `/`.
  - The probe reads AC-7 `PASS`; the FAIL is the ruled verdict.
  - A bad forced watchdog record after AC-5 passes re-opens it.
  - `syslog.1.gz` holds one unrecorded `signin.html` line, dated 2025-08-31 (OI-23).
  - ClamTk's Scheduler Apply would delete the `flock` line.
- **Dropbox research**: `R/tmp/phase-e/dropbox-research/findings.txt` (Sonnet agent, cited URLs).
- **`A` edited in `R` (uncommitted)**, and two tools added under `R/util/ad-hoc/` (untracked).

### Corrections (this session's own errors, caught in-session)

- At 12:07Z I told the Overtoad the snapshot copy's before-06:40 CST window "has passed"; at 06:07 CST it had 33 minutes left.
  Corrected at 12:22Z.
- My first `A` row said "P2 here is its items that do not depend on the route" under "Quoted as answered": a reading presented as
  a ruling (round 1's C-2). Now the question's own P2 definition, with OI-18 open.

### Traps found this session

- The worktree guard also refuses some Python heredocs ("too complex") and any `git -C <primary>`: write the script to a file.
- A fix whose old text lies inside an earlier fix's new text applies again on top of it. The apply tool reports it as OVERLAP.
- uutils `install` unlinks the target and re-creates it, as GNU `install` does: neither is atomic.

### Limits (unchanged)

Never start, stop, restart, enable, disable or reload a unit; never run a Duplicati binary, never contact 127.0.0.1:8300, no
`sudo`; nothing under `/mnt/Backups/Ubuntu/` beyond `stat`; never read a secret file or print an environment variable or a token;
no `git stash`, no host actions, no kill. Pastes carry counts and summary lines only. No file is written under `/tmp`.

## Verification commands (start of the next thread)

```bash
date -u
systemctl show duplicati.service -p DropInPaths -p IOSchedulingClass -p IOSchedulingPriority -p NeedDaemonReload -p NRestarts --no-pager
ionice -p "$(systemctl show -p MainPID --value duplicati.service)"
crontab -l | command grep -c '^0 21 \* \* \* /usr/bin/flock -n /home/pcalnon/\.local/state/clamscan\.lock nice -n 19 ionice -c3 /usr/bin/clamscan '
pgrep -c -x clamscan
stat -c '%y %n' /mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi
tail -n 3 /home/pcalnon/.local/state/duplicati/server-watchdog.log | cut -c1-140
sha256sum /usr/local/lib/duplicati/yamaguchi_server_db_snapshot.py ~/.local/lib/yamaguchi-acceptance/yamaguchi_acceptance_probe.py
sha256sum /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/reactive-dazzling-muffin/tmp/phase-e/val-r3/frozen_r3.md
```

**Expect**:

- Once step A has run: `DropInPaths=/etc/systemd/system/duplicati.service.d/10-io-class.conf`, `IOSchedulingClass=2`,
  `IOSchedulingPriority=7`, `NeedDaemonReload=no` and `NRestarts=0`, one per line; then `best-effort: prio 7`; then a count of 1.
- Until then: `idle` and 0, and the 06:07 scan in `pgrep` until it ends.
- Once the round has run: `c3aebdc6…` and `7d87e6f9…`.
- The runbook: `12376c0459bd4948…`.

## Git status at handoff

- `main` is `89e876d2`; no cited or hashed file changed since `8378665f`. This file goes in on its own PR.
- `R` is at `8378665f` with `A` modified and the two `util/ad-hoc/` tools untracked; that work lands with the runbook (goal 4).
- `R/tmp/phase-e/` (ignored) holds the draft and its copies, the briefs, every lane's findings and fixes, and the research. Keep it
  under the retention rule in the parent `AGENTS.md`, and copy it out before any `git worktree remove` of `R`, which deletes
  ignored files. The predecessor's worktree `joyful-soaring-pnueli` still holds the original draft and brief; keep it too.
