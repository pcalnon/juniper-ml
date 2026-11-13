# Handoff: backup Phase D -- step 14's tools in an open PR, no sitting step run yet, and a false "Backup FAILED" alert traced to a test

**Date**: 2026-11-12 local (written 2026-11-13 02:20Z to 02:55Z)
**Session**: continued from `HANDOFF_2026-11-11_backup-phase-d-sitting-steps-11-13-done-ac4-drill-next.md`, host yamaguchi,
worktree `juniper-ml/.claude/worktrees/swift-stargazing-spindle`
**Predecessor**: `HANDOFF_2026-11-11_backup-phase-d-sitting-steps-11-13-done-ac4-drill-next.md` (this directory), and
through it `HANDOFF_2026-10-30_backup-phase-d-design-merged-then-sitting.md`
**Plans of record**:

- the recovery plan, `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`
  (below: `…RECOVERY-PLAN.md`). Its §6.4 holds the sitting's steps 0-14, §6.5 holds Phase E, §6.3.1 receives the record.
- the integrated design, `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`
  (below: `…INTEGRATED-DESIGN.md`). Its §7.4 holds the destination permission model, §9 the AC table, §10.1 the
  owner's rulings.

---

## Goal statement

Three threads. Take them in this order.

1. **Land juniper-ml#2548** (the tools for step 14). It is open, has no conflict, and is **red on purpose**: it
   stepped aside for the 0.11.5 release cut. One more signed commit is owed after the release proposal merges.
2. **The owner's new issue (2026-11-12): desktop alerts say a Duplicati backup failed, and no such backup exists.**
   One source is found and proven: a test sends a real notification. Its fix, juniper-ml#2559, merged on
   2026-11-13 at 02:49Z (`ae801a70`). A sweep for other tests of the same kind was running at handoff. A
   second, real source is the watchdog. The job's off-schedule runs are a separate, open question.
3. **Continue the Phase D sitting (Procedure A0) at step 14 of `…RECOVERY-PLAN.md` §6.4.** No step ran in this
   segment and no host was changed. Each remaining step is one owner command and one pasted verdict block.

**The working pattern holds.** The owner runs every command that changes the host or reaches the server. They paste
summary lines. The session checks read-only, keeps the running record, and names each next command with its expected
output. The owner granted merge approval for this arc's PRs on 2026-11-11 and added thread 2 to the arc; ask again in a
new session.

### Completed in this segment (2026-11-11 to 11-13 UTC)

- **The tools, built and reviewed** (the predecessor's "process change"):
  - `util/ad-hoc/yamaguchi_acceptance_probe.py` (1.1.0), read-only, run as pcalnon: one verdict line per criterion.
  - `util/ad-hoc/yamaguchi_acceptance_probe_deploy.bash`, `util/systemd/yamaguchi-acceptance-probe.service` and
    `util/systemd/yamaguchi-acceptance-probe.timer`: a daily user timer at 23:30 UTC. **Not deployed.**
  - `util/ad-hoc/2026-11-11_phase_d_finish.bash` and `util/ad-hoc/2026-11-11_phase_d_finish.py` (1.1.0): the root steps
    as verbs `plan`, `drill {1,2}`, `aside`, `ac6`, `status`, `shred`.
  - `tests/test_yamaguchi_acceptance_probe.py` (92 tests), `tests/test_phase_d_finish.py` (128) and
    `tests/test_ac4_restore_drill.py` (23); `util/ad-hoc/2026-11-11_phase_d_tools_mutation_check.py` (208 seeded
    defects, all killed on the tools' final bytes).
  - A reader with no knowledge of the design found 15 defects before any verb ran on the host. Three let a drill read
    `PASS` without having passed. All are fixed and tested; the body of juniper-ml#2548 lists them.
- **juniper-ml#2548, opened 2026-11-12 09:11Z, failed CI on its first head** (`0ced35dd`), in the new tests only:
  - `tests/test_env_repr_safety.py` forbids `dict(os.environ, …)` in a test. It is the third command of the regression
    step, which runs under `bash -e`, so no later suite ran on that head.
  - CodeQL flagged seven fixtures that set a group- or world-readable mode on purpose, and four smaller notes.
- **This session then sat idle for about 16 hours** (cause not known). In that time the owner armed auto-merge
  (2026-11-12 23:07Z), applied three CodeQL autofix commits, merged `main`, and pushed two commits to
  `tests/test_yamaguchi_acceptance_probe.py`. `main` moved again and the PR conflicted in `AGENTS.md` and
  `docs/REFERENCE.md`.
- **2026-11-13 02:16Z, the PR stepped aside for the 0.11.5 cut:**
  - commit `bf53a1d6` repairs the two test files and sets `AGENTS.md`, `CHANGELOG.md`, `docs/REFERENCE.md` and
    `.github/workflows/ci.yml` to `main`'s copy (`f9582a74`), byte for byte;
  - the server-side update-branch `5099d14c` followed. Its tree is `main` plus the PR's eleven files.
  - The release session (ListAgents name `r-obs-sc-2-follow-ups-five-prs-validated-opening-next`) was told. It will
    message when the proposal merges and when the tag is cut.
- **The alert issue: one source proven** (details under "Key context").

### Remaining work, in order

**A. juniper-ml#2548** (branch `feat/backup-phase-d-acceptance-probe-and-finish-tool`).

1. Wait until the 0.11.5 proposal ("release: juniper-ml v0.11.5 (proposal)") has merged: `main`'s `CHANGELOG.md` then
   shows a `## [0.11.5]` heading under an empty `[Unreleased]`. `gh release view v0.11.5` says whether the tag is cut.
2. Run update-branch, pinned: `gh api -X PUT repos/pcalnon/juniper-ml/pulls/2548/update-branch -f expected_head_sha=<head>`.
   It is clean, because the PR changes none of the four shared files.
3. Push **one** signed commit that re-adds the PR's lines on top of `main`'s then-current copies:
   - `.github/workflows/ci.yml`: the `cryptography>=44.0.1` install block and the three suite blocks;
   - `AGENTS.md`: the suite count (`main`'s plus 3) and `**Last Updated**` set to that day's UTC date;
   - `docs/REFERENCE.md`: the count clause, three list lines, three suite entries and two tool entries. Write "each
     verb prints the SHA-256 prefix of every file it runs **as root**";
   - `CHANGELOG.md`: the entry under the **new** `[Unreleased]`, adding `### Added` there. Never under `[0.11.5]`.
   - The text of all four additions is in this worktree: `git diff 15b5d9bb -- <file>`, and
     `tmp/phase-d-finish/my-tracked-changes-3.patch`. The worktree's base is `15b5d9bb`, which is stale: build the files
     from `origin/main`'s blobs, or unstage and use `util/ad-hoc/2026-11-12_rehome_worktree_edits_on_new_main.py`.
   - Prove the candidate first: `tmp/phase-d-finish/build_step_aside.py` shows the method (a temporary index,
     `git merge-tree`, the merged tree unpacked and its suites run). Then `util/push_signed_commit.py`, with
     `--expected-head` pinned to the update-branch head.
4. Run every command of the regression step past failures: `tmp/phase-d-finish/run_regression_list.py`. On this host
   four suites fail only because `TMPDIR` is inside a checkout: `test_workflow_script_paths`,
   `test_a0_restore_scripts`, `test_e2e_f037_render_census`, `test_replay_redrive_stack_refusal`.
5. `util/safe_merge.py --pr 2548 --repo juniper-ml --execute` in the background; read its `MERGED` line. The stored
   auto-merge text is this session's first commit message, armed 2026-11-12 23:07Z; check what the squash will say.
6. Then land this handoff as its own PR (`tmp/phase-d-finish/open_handoff_pr.py`; its body file is not written yet).

**B. The false alerts.**

1. Read the sweep: `python3 tmp/phase-d-finish/alerts/hermeticity_sweep.py report tmp/phase-d-finish/alerts/sweep-full`.
   Part 1 (commands 1-120) started at 02:27Z and was running at handoff; run part 2 with `… hermeticity_sweep.py range 121 238 sweep-full`.
2. **juniper-ml#2559** fixes `tests/test_duplicati_scheduled_backup.py`: a recording `notify-send` stub in every
   fixture, the session bus address handed to children pointed at a path that does not exist, assertions that the
   notification reached the stub, and three tests that pin all of it. It **merged** on 2026-11-13 at 02:49Z
   (`ae801a70`). It carries no CHANGELOG entry on purpose; add one under the new `[Unreleased]` (`### Fixed`) after
   the 0.11.5 proposal merges. Sessions whose checkout is older than that merge still send the alert when they run
   the suite.
3. If the sweep names another suite that runs a real alerting tool, fix it the same way in a second PR. Its first 40
   commands named none. They did show `tests/test_prompt_discovery.py` running the real `gh pr list` and `ssh -G`:
   no alert, but a network call from a unit test; record it as a finding.
4. The watchdog and the off-schedule runs need the server, so they need the owner: see questions Q2 and Q6.

**C. The sitting.** `D` below is a checkout that holds the tools. On 2026-11-13 the **primary** checkout
(`/home/pcalnon/Development/python/Juniper/juniper-ml`) is on the PR's branch and holds them; so does this worktree.
`T` is `$D/util/ad-hoc/2026-11-11_phase_d_finish.bash`. As root each verb prints the SHA-256 prefix of the tool, the
wrapper and each file it runs as root; compare them with the list in "Key context". The probe and the API client run as
pcalnon and are not in that list of printed hashes.

1. **Before drill 1 (root):** `bash "$T" status --backup-id 2`. It lists the verdict records, any run directory still
   on disk, and the probe's lines. It always exits 0; read its lines.
   - The record says the 2026-11-09 select-only run left `/root/phase-d-tmp/ac4-20260918T140000-20261109-050909`, which
     holds a decrypted dlist. If `status` lists it: `bash "$T" shred --run-dir <that path>`.
   - The run root must be `0700 root`, or the tool refuses.
2. **AC-4, drill 1 (root):** `bash "$T" drill 1`, after that day's backup has finished. The tool refuses while the
   server reports an active task. If it cannot read the server's state it says so and proceeds.
   - If `/root/phase-d-tmp/ac4-drill1.out` exists, the tool adopts it and does not run the driver. If the adopted
     output reads `ERROR`, run `bash "$T" drill 1 --rerun`.
   - The owner pastes from `-- summary of drill 1` to `VERDICT:`. On `PASS` the run directory is shredded.
3. **The aside copy (root):** `bash "$T" aside`. It copies **every** dlist (18 on 2026-11-13, 2,313,447,418 bytes) to
   `/mnt/Backups/Ubuntu/_yamaguchi_retention_aside` and writes `MANIFEST.sha256`. It refuses until drill 1 has passed.
   Run it right before step 4; if a backup finishes in between, run it again.
   - `bash "$T" plan` (any user) is the recompute the predecessor asks for. The copy does not depend on it.
4. **Restore `retention-policy`** as `2W:1D,6M:1W,2Y:1M,5Y:2M` in the UI, and record the date. Read question Q7 first.
   - `keep-time` and `keep-versions` are **never** restored.
   - **Read back (pcalnon):** `/usr/bin/python3 -I "$D/util/ad-hoc/yamaguchi_acceptance_probe.py" --backup-id 2
     --expect-retention restored`. See "What the read-back judges" below: it is narrower than a hand-read `export 2`.
5. **AC-4, drill 2 (root):** `bash "$T" drill 2`, on `duplicati-20261107T212908Z.dlist.zip.aes`.
6. **AC-6b (root):** `bash "$T" ac6`, after a backup finishes and before the next 13:45 UTC.
7. **AC-5 (pcalnon):** three consecutive days whose every watchdog record reads `OK`, and one deliberate
   `/usr/bin/python3 "$D/util/ad-hoc/yamaguchi_watchdog.py" --backup-id 999`, which must record `ALERT JOB_MISSING`
   (it also sends a desktop alert; that is the test). The streak was 2 days on 2026-11-12 (11-11 and 11-12).
8. **AC-7.** It fails today, and it is tied to a ruled design decision: question Q3.
9. **Deploy the probe's timer (pcalnon):** `bash "$D/util/ad-hoc/yamaguchi_acceptance_probe_deploy.bash" --backup-id 2`.
   The unit runs copies under `~/.local/lib/yamaguchi-acceptance/`.
10. **The record PR**, into `…RECOVERY-PLAN.md` §6.3.1. Fold in the findings lists of both predecessor handoffs and
    "Key context" below.
11. **Then:** update the memory hub `project_backup_arc_hub.md`; fix the AC-4 driver's gaps; move on to the
    after-Phase-D items of `…RECOVERY-PLAN.md` §6.5 (Phase E), O-11, D-12, finding 15, and AC-14's Phase E ruling.

**Rule for every sitting** (the predecessor's rule 4): no hand-written grep, count or filter in an owner block when a
tool can carry it. A new check goes into a tool with a test first.

### Open questions (the owner's to rule)

- **Q1. AC-3's count criterion going forward.** Unruled. The probe treats a move of more than ±10 % against the
  previous run, or ±5 % of bytes against the 2026-11-08 baseline, as `ATTN`, not `FAIL`.
- **Q2. The job's off-schedule runs: now three.** They began 2026-11-08 23:41:22Z, 2026-11-10 00:36:22Z and
  2026-11-11 22:14:21Z (the last took 12 h 25 m). Nobody is known to have started them.
  - Evidence needs the server: the probe's `OFFSCHED` line lists the operations logged in the 15 minutes before each.
    Pass `--runs 14`: the default of 8 stops reaching the first of them after the 2026-11-14 run. The line also
    counts the first post-recovery run (2026-11-07 21:29Z), which `resume` started; that one is explained.
  - The UI's **About → Logs → Stored** around each start (K2 in the running record) names the request. If it reads as
    an API or remote-control request, treat it as a security finding, because the console connection is enabled.
  - Checked read-only on 2026-11-13: one `duplicati-server` process, listening on loopback port 8300 only; no
    autostart entry; pcalnon's own `~/.config/Duplicati` untouched since 2026-09-22.
  - No Claude session of this project wrote a transcript record in the 20 minutes before the second or the third
    start (`tmp/phase-d-finish/alerts/offschedule_transcript_scan.py`). So neither a session nor a test started them.
  - **A candidate, not verified: a save of the job in the UI.** Duplicati's scheduler at the installed tag
    (`Duplicati/Library/RestAPI/Scheduler.cs`, fetched to `tmp/phase-d-finish/alerts/upstream/`) re-reads a schedule
    row whose time changed and queues the job at once when that time is not in the future
    (`if (start <= DateTime.UtcNow)`). A job save rewrites that row. The sitting already saw one UI save move the
    schedule's date back a day. Ask the owner whether the job's edit page was saved near each start.
  - **It matters for step C.4**, which is a job save: a backup may start at the save, and the first retention pass then
    runs at the end of that backup, not at the next 14:00Z. Finish `aside` first, and do not save during a backup.
- **Q3. AC-7 against D-14.** The two do not hold together as observed.
  - D-14 is ruled (`…INTEGRATED-DESIGN.md` §7.4 and §10.1): volumes `0640 duplicati:duplicati`, directories
    `duplicati:duplicati 2750`, so that Dropbox reads through the group and cannot write or delete. The group-write
    form was rejected, because a cloud-side change would then reach the local master.
  - The step that applies the model to the existing tree is Phase E's (`…RECOVERY-PLAN.md` §6.5 item 2). It has not
    run: the destination directory is `2770 pcalnon:duplicati` and its parent `770 pcalnon:duplicati`.
  - **Observed 2026-11-13:** the 9 volumes that conform (`640 duplicati:duplicati`, the three runs since 11-11) read
    `unsyncable`. The other 965 are owned by pcalnon; on 2026-11-12 every one of them read `up to date`. The daemon
    carries gid 139 as its primary group, so reading is not what is missing. A likely cause, not verified: the client
    writes its own extended attribute on each file, which needs write access.
  - Dropbox's own helper re-owns the tree when its polkit prompt is approved: `chown -h -R 1000` and `chmod -R u+rwX`
    on `/mnt/Backups/Ubuntu/Dropbox`, as root, on 2026-11-10 19:33:01 CST. That explains the 11 volumes at
    `640 pcalnon:duplicati`. It does **not** explain mode 770. The 877 pre-recovery volumes were `770 pcalnon` before
    the recovery. The 77 post-recovery volumes of 11-07 and 11-08 read `770 pcalnon` on 2026-11-09, after a root
    script ran through pkexec at 03:25:59 CST that day; its content was not recorded.
  - So the question is the design's: keep D-14 and send the offsite copy another way, or accept that the synced tree
    is owned by pcalnon. Do not make volumes group-writable as a fix; that is the form D-14 rejected.
  - Still true from the predecessor: the `sg duplicati` start of Dropbox does not survive logout or reboot; check the
    daemon's groups after each boot (the probe's `AC-7` line does).
- **Q4. Drill sample scope** (`Pictures/`). Unruled. Recommendation: no exclusion.
- **Q6. The watchdog and AC-5.** Part of thread 2 as well.
  - A run whose result is `Warning` reads `ALERT NOT_SUCCESS`, sends a desktop alert and resets the streak
    (2026-11-10). That run's warnings have not been read; the probe's `RUN` line classes them by tag.
  - The 12:00 CST check often lands mid-run. `OK RUNNING` judges no result, and the 6-hour limit is not reached at a
    check four hours after the start, though runs took 6 h 51 m, 8 h 46 m and 12 h 25 m.
- **Q7. The policy's `1D` interval on this schedule.** Duplicati keeps a fileset in a frame when its time less the
  last kept one's is at least the interval. Two effects:
  - in today's list the off-schedule filesets are the kept ones, so the scheduled filesets of 11-08, 11-09 and 11-10
    are deleted (`plan`: 9 of 18, with the off-schedule one of 11-11);
  - on scheduled filesets alone, a daily one stamped a second earlier than the last kept one (`140000` after `140001`)
    is 23:59:59 later and is deleted.

  Restoring the ruled value as it stands is the standing instruction.
- **Q8. The aside directory's location.** Its parent is `770 pcalnon:duplicati`, so either account can rename the
  directory. The tool writes through a descriptor on the opened directory. `…INTEGRATED-DESIGN.md` §7.4 wants that
  parent at `2750`; that is Phase E's step too.

Q5 of the predecessor (where the scripts land) is settled: juniper-ml#2544 committed them.

### Key context

- **The false alert, proven.**
  - `tests/test_duplicati_scheduled_backup.py`, `TestFailureReporter.test_missing_status_still_writes_failures_log_and_exits_zero`,
    runs `util/duplicati_backup_failure.bash` with `PATH=<stubs>:/usr/bin:/bin`. Its fixture writes no `notify-send`
    stub, so the script finds the real one.
  - Each run of that suite on this host sends `notify-send --urgency=critical "Backup FAILED: duplicati-backup.service"`,
    whose text ends `See …/juniper-ml/tmp/tmp<random>/state/failures.log`: a temporary directory that is gone when the
    test ends. `strace` shows the call (`tmp/phase-d-finish/alerts/strace-reporter-test.txt`).
  - No backup runs: `duplicati-cli` is a stub there. Every local run of the regression list sends one alert.
  - The owner's `util/ad-hoc/check_for_duplicati_failed_logs.bash` (juniper-ml#2549) looks in exactly that place.
  - The real unit of that name is gone, and its last real failure record is dated 2026-08-25
    (`~/.local/state/duplicati/failures.log`, 3 records). The tier-2 and tier-3 reporters have never written one.
- **The real alert source is the watchdog** (`util/ad-hoc/yamaguchi_watchdog.py`, daily 12:00 local):
  `"Duplicati (Yamaguchi) backup ALERT"`. Its `~/.local/state/duplicati/server-failures.log` holds 59 records: daily
  through the outage to 2026-11-07, then 2026-11-10 (question Q6).
- **What `PASS` means in the tools.**
  - A drill's output must be one complete driver run: no `FATAL`, no line twice, the driver's order, nothing after
    `RESULT`. The verdict is then recomputed from the numbers with AC-4's floors (15 verified, 5 live matches).
  - `aside` copies every dlist because `plan` is only a prediction: the retention port treats every fileset as a full
    backup, and `DeleteHandler.cs` at tag `v2.4.0.0_stable_2026-09-03` treats a partial one differently.
  - Exit codes: 0 `PASS`, 1 `FAIL`, 2 `ERROR`, 3 `REFUSED` (nothing was changed), 64 usage. The wrapper's own
    refusals print one `REFUSED:` line and no `VERDICT:` line.
- **What the read-back judges** (step C.4). The job's name; that `TargetURL` is the design's; 2 sources and 45 filters
  **by count**; `Repeat` `1D` at 14:00:00 UTC; `blocksize`, `tempdir`, `aes-version`, `no-auto-compact` by value; the
  guard path; the option **names** against the recorded set (so an added or dropped option fails); retention. It does
  **not** compare the schedule's anchor date (it prints it), the contents of the sources and filters, or any other
  option's value. For those, the owner compares an `export 2` from before the save with one from after.
- **SHA-256 prefixes of the tools** (unchanged since the PR's first head):
  - `2026-11-11_phase_d_finish.py` `4a66d4cba2c614cf`; `2026-11-11_phase_d_finish.bash` `c5659bff20b93c73`;
  - `2026-11-09_ac4_restore_drill.py` `29db0ed3ec5d3368`; `retention_table.py` `489509efe3c960ca`;
  - `yamaguchi_acceptance_probe.py` `bc09364c325e93f9`; `yamaguchi_server_api.py` `756b41f60c7af32d`;
  - `yamaguchi_acceptance_probe_deploy.bash` `09f4067d0bc10fb1`.
- **The AC-4 driver was not changed**, because drill 1 is pending. Its gaps, to fix after the drills:
  - `proc.returncode < 3` passes a restore killed by a signal. The finish tool fails a negative code.
  - `eligible()` admits a path with control characters. In the finish tool a newline in a path cannot supply or forge
    a summary line. Other control characters (ESC, CR, U+2028) still reach the root terminal as they are.
  - `stratum_of(-1)` returns `small`, so a File entry with no `size` is sampled and then raises `KeyError`.
  - Its line 162 holds a literal U+FEFF inside a string.
  - It prints a 16-hex SHA-256 prefix of the passphrase. The tool withholds it; an adopted hand-run output file still
    holds it (root-only, 0600).
- **The host, read-only, 2026-11-13 02:19Z.**
  - Nothing of step 14 has run: no aside directory, no `~/.local/state/duplicati/acceptance.json`, no probe timer.
  - Probe, server-free: AC-1 `PASS` (136.8 h); AC-5 `PENDING` (2 of 3 days; no 999 record); AC-6a `PASS` (5 days);
    AC-7 `FAIL` (9 `unsyncable`, all owned by `duplicati`); AC-12 `PASS` (1.7; 15 unset rows, all accepted).
  - 18 dlists. `plan` predicts 9 deleted (5 pre-recovery, 4 post-recovery), 1,153,733,317 bytes.
  - The primary checkout is on the PR's branch at `3d823aca`, with no local change to the tools or tests.
- **The running record** is gitignored and holds hash prefixes:
  - `tmp/phase-d-sitting/running-record.md` in this worktree: the predecessor's 386 lines plus this segment
    (`segment-2026-11-11.md` and `segment-2026-11-12b.md` beside it), 652 lines on 2026-11-13;
  - an archive copy of the same 652 lines at `tmp/phase-d-sitting/running-record.md` in the **primary** checkout,
    with the predecessor's copy kept beside it as `running-record.predecessor-386-lines.md`;
  - the predecessor's own, at the same path in the worktree `parallel-strolling-meteor`.

  `tmp/phase-d-sitting/assemble_record.py` rebuilds and re-archives it after a new segment file is added.
- **Where the tools differ from the predecessor's sketch.**
  - The timer fires at 23:30 UTC, not 15:30: runs took up to 12 h 25 m.
  - `aside` reads drill 1's verdict record, not `results.json`, and copies in-process (owner, group, mode, timestamps).
  - The probe reads the job log through `util/ad-hoc/yamaguchi_server_api.py`, not through `yamaguchi_census.py`.
- **Still true from the predecessor.**
  - `util/ad-hoc/duplicati_drill_fresh.py` is superseded for AC-4: it puts the passphrase on argv.
  - The report URL (item S-8 of `…INTEGRATED-DESIGN.md` §6; ruling O-13 "keep" in `…RECOVERY-PLAN.md` §6.6) lives in the
    server's console-connection settings, and, since the UI save in step 11 part B of the sitting (the running
    record's "OBSERVATION: after the UI save"), in the job as `send-http-url`. It carries a bearer token.
- **Findings for the record PR** (`…RECOVERY-PLAN.md` §6.3.1), added to both predecessors' lists:
  - AC-7 against D-14, the Dropbox helper's `chown`, and what is not explained (Q3);
  - the predecessor's "gid 139 is sufficient" (2026-11-09) was confounded: the volumes were re-owned at that restart;
  - three off-schedule runs (Q2);
  - the predecessor's verification grep, `OK|FAIL|STALE|JOB_MISSING`, cannot show an `ALERT` line;
  - the `plan` numbers, the partial-fileset correction to `retention_table.py`, and the aside copy of every dlist;
  - the `1D` interval (Q7); the watchdog's blind spots (Q6);
  - the review: a mutation check that killed 115 of 115 defects did not find the three false-`PASS` paths;
  - the driver's gaps;
  - the false alert, and that a test fixture which keeps `/usr/bin` on `PATH` reaches the real tool when a stub is
    missing;
  - this PR's own CI failures: only the three new suites were run before the PR opened.
- **The limits still bind.** From `HANDOFF_2026-10-30_backup-phase-d-design-merged-then-sitting.md`, verbatim:
  - "Never start, stop, restart, enable, disable or reload a unit."
  - "Never run a Duplicati binary, never contact 127.0.0.1:8300, no `sudo`."
  - "Nothing under `/mnt/Backups/Ubuntu/` beyond `stat`."
  - "Never read a secret file; never print an environment variable or a token."
  - "No `git stash`; no interactive shells; no host actions."
  - "The owner may direct a named action in person, which releases that action only. Nothing releases one of
    `…RECOVERY-PLAN.md` §6.0 item 6's absolutes."
  - A lane brief says "no `sudo` in any form, not even `-n` or `-l`" and sets `PYTHONDONTWRITEBYTECODE=1`.
  - Also: no `/tmp`; root scratch goes in `/root/phase-d-tmp`; pastes are counts and summary lines only; never print
    `send-http-url`, `TargetURL` or a warning's text.
- **Where this segment went past "beyond `stat`".** Nothing under the destination was opened. But:
  - the probe, as built, lists the destination's file names and asks the Dropbox daemon for the sync status of every
    file there (the predecessor asked for the newest dlist only); `plan` lists the dlist names;
  - by hand, the session listed the names (not the values) of the extended attributes of three volumes.

  The owner should confirm that the probe's census is acceptable, or ask for it to be narrowed.
- **Traps of this segment.**
  - In this harness a four-hex-digit backslash-u escape typed into a file reaches it as the character itself. Build
    such a character with `chr()`.
  - The pre-commit secrets hook scans staged content only. Scan copies of new files with the pinned scanner
    (`tmp/phase-d-finish/leak_scan.py`); it flagged a stub credential line in a new test.
  - Run the **whole** regression list before opening a PR, not only the new suites: a repo lint lives in it.
  - CodeQL flags an integer literal with group or world bits that reaches `os.chmod`, also through a conditional
    expression. A mode built from the `stat` module's names is not flagged.
  - `util/push_signed_commit.py` uploads whole files. The owner had pushed to the PR's branch; pin `--expected-head`
    and build on the branch's files, not on a worktree's older copies.
  - A release cut under an open PR files its CHANGELOG entry under the released heading with no conflict. Step aside
    (no CHANGELOG change) until the proposal merges, then add the entry under the new `[Unreleased]`.
  - A worktree session's shell refuses a compound command that names `git`. Write a script under `tmp/` and run it.
  - The host is busy (load average 9 to 21, a virus scan among the causes), so `fsync` and `shred` are slow.

---

## Verification commands (start of the next thread)

Run each line as its own command, from the new session's own worktree. `W` is this segment's worktree.

```bash
W=/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/swift-stargazing-spindle
gh pr view 2548 --repo pcalnon/juniper-ml --json state,mergeStateStatus,headRefOid,mergedAt
gh release view v0.11.5 --repo pcalnon/juniper-ml --json publishedAt,targetCommitish
gh pr list --repo pcalnon/juniper-ml --state open --search 'v0.11.5 in:title' --json number,title
sha256sum "$W/util/ad-hoc/2026-11-11_phase_d_finish.py" "$W/util/ad-hoc/2026-11-11_phase_d_finish.bash" "$W/util/ad-hoc/yamaguchi_acceptance_probe.py" | cut -c1-16,65-
bash "$W/util/ad-hoc/2026-11-11_phase_d_finish.bash" plan | tail -n 5
/usr/bin/python3 -I "$W/util/ad-hoc/yamaguchi_acceptance_probe.py" --backup-id 2 --no-server --no-write
tail -n 6 ~/.local/state/duplicati/server-watchdog.log | cut -c1-160
ls "$W/tmp/phase-d-finish/alerts/sweep-full" | wc -l
tail -n 40 "$W/tmp/phase-d-sitting/segment-2026-11-11.md"
```

**Expect:**

- the PR `OPEN` and `BLOCKED` (red on purpose) until step A.3, then `MERGED`; the release absent until it is cut;
- the three hash prefixes of "Key context";
- `plan`'s `predicted` line fourth from the end (9 of 18 on 2026-11-13; it changes with each new fileset);
- the probe's local lines: AC-1 `PASS`, AC-6a `PASS`, AC-12 `PASS`; AC-5 `PENDING` or `PASS` (`FAIL` when the newest
  day holds an alert for the job, or the newest record is over 36 h old); AC-7 `FAIL` until Q3 is settled; the server
  criteria `SKIP`;
- the watchdog's raw lines, `ALERT` lines included;
- the sweep's traces (two files per command: 476 when both parts have run).

## Git status at handoff

- **juniper-ml#2548** is open at `5099d14c` (nine commits, auto-merge armed by the owner, red on purpose).
- **juniper-ml#2559** (the alert fix) merged as `ae801a70`. This worktree's copy of
  `tests/test_duplicati_scheduled_backup.py` holds the same fix as an unstaged change, because the worktree's HEAD
  is older than the merge.
- **Worktree `swift-stargazing-spindle`** (branch `worktree-swift-stargazing-spindle`, HEAD `15b5d9bb`, which is
  stale):
  - staged: `AGENTS.md`, `CHANGELOG.md`, `docs/REFERENCE.md`, `.github/workflows/ci.yml` (this PR's additions on the
    old base) and the `retention_table.py` docstring;
  - untracked: the PR's ten new files (the two repaired test files equal the PR's), and this handoff.
- **The primary checkout** is on the PR's branch at `3d823aca`, two commits behind it.
- **This worktree's `tmp/`** holds the running record, `tmp/phase-d-finish/` (the review's experiments, the mutation
  logs, the scan and build scripts, the regression logs) and `tmp/phase-d-finish/alerts/` (the trace and the sweep).
  **Do not remove it, or `parallel-strolling-meteor`'s,** until the record PR has merged.
