# HANDOFF 2026-10-04 — backup arc Phase B: fix-forward merged (ml#2134); Phase B frozen; round 3's fold-in pending

Session c9277a65 ("backup phase b"). Written 2026-10-04 at a usage limit, and refreshed 2026-10-05 after
round 3's lane B reported and this file was validated three times; all four are folded in below.

The names used below:

| Name | File |
| --- | --- |
| D | `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` |
| A | `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` (the assessment, never a lane) |
| R4 | `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md` |
| record | `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md` |
| R3 | `util/ad-hoc/2026-10-04_backup-phase-b-round3/` |
| R3A, R3B, R3C | round 3's lanes A, B and C; their reports are the record's "Round 3, lane …" sections |
| HV, HV2, HV3 | this file's three validations: the record's "The 2026-10-04 handoff's validation", "… re-validation" and "… third validation" |
| re-key, gate | `util/ad-hoc/2026-10-03_rekey_settings_key.bash`, `util/ad-hoc/2026-10-03_rekey_gate.py` |
| wrapper, installer | `scripts/duplicati-wrapper.bash`, `util/install_duplicati_service.bash` |
| contract, stub | `util/systemd/duplicati-env.contract`, `tests/duplicati_api_stub.py` |
| clearing script | `util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py` |
| re-assembly | `util/ad-hoc/2026-10-05_reassemble_phase_b_record.bash` |

The record is on `main`, landed with this file ahead of the Phase B change. It holds all 16 reports so far,
verbatim. The same PR carries:

- the record's header, `R3/RECORD_HEADER.md.in`;
- the archiver, `util/ad-hoc/2026-10-04_archive_phase_b_round_reports.py`, and the re-assembly;
- R3C's harness, `R3/r3c-harness/`, with a README;
- four helpers:
  - `util/ad-hoc/2026-10-04_save_subagent_report.py`;
  - `util/ad-hoc/2026-10-04_wip_worktree_delta.py`;
  - `util/ad-hoc/2026-10-05_match_reports_to_final_messages.py`;
  - `util/ad-hoc/2026-10-05_attack_phase_b_archiver.py`.

## Continue

Continue Phase B of A §6.2 from round 3's fold-in, in this worktree:

- **Worktree**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/sorted-stargazing-garden`
- **Branch**: `wip/backup-phase-b`
- **Frozen commit**: `c3d0e890`. It is local and unsigned: **never push it**. Its parent is `e509353e`, the head
  of ml#2134 before update-branch. Every Phase B file is in that commit.
- **Never remove or sweep this worktree before the Phase B PR merges.** `c3d0e890` and R3's drafts and
  reports exist only here. The branch is also bundled at
  `/home/pcalnon/Development/python/Juniper/backups/juniper-ml_wip-backup-phase-b_c3d0e890_2026-10-05.bundle`.
  To restore it, run `git fetch <bundle> wip/backup-phase-b:wip/backup-phase-b`; it needs `cf711cf4`, which is
  on `main`.

Read `HANDOFF_2026-10-03_backup-arc-consolidated.md` too: it keeps the traps and the carried-item inventory.

## Completed

- **ml#2134 merged** as `f01a438c`; its post-merge runs on `main` are green, main-verify included. It fixes
  forward ml#2115:
  - `export` issues the single-operation token;
  - the stub answers 400 for a token-less request, 500 for an unsigned token and 401 for another operation's
    token;
  - an absent watchdog `--backup-id` records `JOB_MISSING`;
  - usage errors exit 64.
- **Phase B is assembled**: 26 files, pinned by `R3/MANIFEST.sha256`. The manifest pins round 3's copies of
  the record, its header and the archiver, and `main`'s are newer.
  - D regenerates **byte-for-byte** from `main`'s D. Reset it first (`git show origin/main:<D> > <D>`), then
    run `util/ad-hoc/2026-09-22_stage_design_artifacts.py --from-repo` and the clearing script.
  - The clearing script makes 54 edits: 53 to prose and 1 declared `FENCE_EDITS` change to P0 step 10's
    guard dry-run. Its `FIXFWD` defaults to `ml#2134`.
  - The checks pass: 180 tests, every hook, both sequence-safety screens, a structure delta of 0, and
    markdownlint clean on D, A and the record.
- **Round 3 reported**: R3A 0 BLOCKER / 6 DEFECT / 8 NIT, R3B 0/4/11, R3C 0/5/13. R3B was stopped at the
  2026-10-04 usage limit and resumed on 2026-10-05.
- **HV, HV2 and HV3 are applied** to this file, the record's header, the scripts and the drafts. HV found 2
  BLOCKER, 4 DEFECT and 10 NIT; HV2 found 0 BLOCKER, 3 DEFECT and 11 NIT; HV3, on HV2's changes only, found
  0 BLOCKER, 1 DEFECT and 9 NIT. No fourth round ran: HV3's one DEFECT was its own report's missing slot.
- **Drafts** are in R3: `PR_BODY.md`, `COMMIT_BODY_ONLY.txt` and `CHANGELOG_ENTRY.md`. They carry placeholders
  for the counts and sections the fold-in is known to change: `<<ROUND3>>`, `<<ROUND3-CHANGELOG>>`,
  `<<EDITS>>`, `<<TESTS>>`, `<<TESTS-CONTRACT>>`, `<<NEW-SUITES>>`, `<<SUITES>>`, `<<FILES>>` and
  `<<FILE-LISTS>>`.
  - Other values may move without a placeholder: the wrapper's and installer's versions, and the
    stage-script and snippet-linter counts.
  - `CHANGELOG_ENTRY.md` is the frozen commit's entry with those fixes, so take the entry from it, not from
    `c3d0e890`.

## Remaining (in order)

1. **Fold in round 3.** Check the fleet PRs below that touch the same code first.

   *R3A and R3C (both found the first three):*

   - **Deny lists.** Add `parameters-file` and `parameterfile` to the wrapper's `ENV_OPTION_DENY` and the
     installer's `HAZARD_OPTION`, then update the contract and D.
     - Weigh `webservice-enable-forever-token`, `webservice-cors-origins` and the alias
       `webservice-allowedhostnames`, and R3A D-1's alternative, an allow-list of tunables.
     - Test **every** entry.
   - **The re-key's EXIT trap** prints wrong recovery text in four states. R3B N-11's timed-out decrypt start
     may duplicate them, as R3B says: it is R3A D-4's case. Make the trap:
     - derive the state from the key files by hash (key, `.old`, `.new`);
     - set a STARTED flag once it pauses, and DO_NOT_START after a FragmentPath refusal;
     - stop the unit if a drop-in was present;
     - report the database as UNKNOWN once a decrypt **or** encrypt start was attempted (`:254`);
     - print the gate's counts on a gate failure;
     - print only the branch that applies.
   - **The re-key's pre-flight.**
     - Before the first stop, count the `enc-v1:` blobs in `ConnectionString` and `BackupTargetUrl` on a copy.
       Refuse, or document the remedy, if the count is non-zero.
     - Require the timer to be inactive as well as not enabled (R3B N-8).
     - Guard the dry run's "decrypt start done" line.
     - Add a `REKEY_INSTALLED_UNIT` override, so the test stays hermetic once the installer has run on the
       owner's host.
   - **Real-path tests.** 14 of 25 mutants survived.
     - From `R3/r3c-harness/` (`mkstubs.bash`, `t3_installer_real.bash`, `t4_*`; see its README), build a
       stubbed non-dry-run test for the re-key and a real-path test for the installer.
     - Add a test for the clearing script.
     - Fix `docs/REFERENCE.md`'s claim that the contract suite pins the drift copy-aside (R3C D-5).
   - **Prose**, in the clearing script and A:
     - the residue list must be exactly R4's open rows: add B22 (R3B N-2), R4:153, :217, :231 and :351, and fix
       note 5b to match;
     - D's Appendix C says "None of items 1–10 has been applied"; item 4 now is (R3A D-2);
     - the job-2 residue is ml#2134's list: 8 flag defaults and 4 files with 6 hard-coded lines (R3B N-3);
     - the web-credential format goes in D step 9 and A step 11. It is one line, `DUPLICATI_WEB_CREDENTIAL=<password>`,
       from which one outer quote pair is stripped;
     - the edit count, wherever it is stated: 54 today, 53 of them prose, and more after the fold-in. The frozen
       `CHANGELOG.md` entry is one such place;
     - A §8's Round 2 entry omits five of round 2's findings. Lane B's NIT-1 and lane C's N-4, N-5 and N-6 were
       fixed; lane A's DEFECT-4 is partial (its count is the pre-flight item above). Add all five (R3A N-1 and
       D-5).

   *R3B, new. All four are in `main`'s procedure too, behind §8's STOP, so the STOP must not clear without them:*

   - **DEFECT-1: the first backup after recovery deletes old filesets.**
     - Its retention pass (`1W:1D,1M:1W,1Y:1M,3Y:2M`) keeps 1 to 3 of the 9. It keeps the 2026-09-18 one only
       if the run falls between 2026-10-17 22:14Z and 2026-10-18 14:00Z.
     - AC-4's first drill restores that fileset; it gates §10.2 step 1 and runs after the backup.
     - Lane B's remedies: run AC-4's pre-recovery drill before the first backup; or drop `retention-policy` in
       step 10's edits and restore it after AC-4; or re-target AC-4 and §10.2 step 1.
     - **This is the owner's choice**: put it to the owner with a recommendation.
     - Then correct every statement that nothing under `/mnt/Backups/Ubuntu/` is deleted.
       `grep -n 'is deleted or moved'` finds them: in `c3d0e890`'s D at :16, :704 (a unit comment that cites
       the rule), :2080 and :2761, and in A at :204.
   - **DEFECT-2: an unread startup delay.**
     - Set `paused-until` to `0` with `sqlite3` while no server runs: on A0, A and A2 in step 8; on B after the
       hand start and before the first start.
     - Read `startup-delay` back, and check that the first start reads Paused.
     - Move "confirm the next 12:00 fire" after step 10.
   - **DEFECT-3: Procedure B's rebuild tool** (`util/ad-hoc/yamaguchi_build_job.py`) starts an overdue job.
     - Pause first.
     - POST a future 14:00Z `Schedule.Time`.
     - List every default to change.
     - Create the web credential before step 7.
   - **DEFECT-4: §7.3.6's recovery** must delete `pbkdf-config` too, and drop A2 from the paragraph.

   *NITs:* fix the cheap ones, R3B N-4 among them (D's P2 step 4 redeploys the watchdog without
   `--backup-id`). Record the rest in A §8 as residue, each with a reason.
2. **Round 4**: at least two lanes, on the fold-in's delta **and** the whole procedure.
   - One lane carries R3B's lens: an end-to-end walk of A0, A, A2 and B at the round-4 head, looking for damage
     to the sole copy.
   - R3B's two open questions cannot be answered under the standing limits, so route each to the step that
     answers it:
     - **Is there a `-wal` or `-journal` beside `/usr/lib/duplicati/data/BMXWPAOGLP.sqlite`, the sole-copy
       index?** D step 8 copies only the main file. Phase C step 6's released listing of that directory
       answers it (A:257 in `c3d0e890`, A:253 on `main`). Make D step 8 copy whatever it finds.
     - **What are the stored `startup-delay` and `paused-until` values?** They decide how far DEFECT-2
       reaches. They live in the databases P0 restores, so DEFECT-2's own step-8 read-back answers them.
   - Save each report the moment it lands:
     `util/ad-hoc/2026-10-04_save_subagent_report.py --tasks-dir ~/.claude/projects/<project-slug>/<session-id>/subagents --agent <id> --out util/ad-hoc/<date>_backup-phase-b-round4/<lane>.md`.
     A session's subagent transcripts can move to `~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/<session-id>/subagents/`
     when it ends, so find them by the session id.
3. **Open the Phase B PR.**
   - Append each round-4 report to the re-assembly's `ENTRIES` as `<heading>|<file>|<origin>`, and complete
     "Disposition of round 3" in `R3/RECORD_HEADER.md.in`. Then run the re-assembly with `--check` first, and
     read what it says:
     - By default it lifts the 16 archived reports from the record and reads only the new files.
     - It refuses, with exit 2, to drop an archived report or any record text outside a section; to keep an
       archived report that its file or `ENTRIES` origin contradicts; and to overwrite a header that differs
       from the `.in` file.
     - Completing the disposition is a header change, so the write needs `--accept-header`. Pass
       `--replace "<heading>"` or `--allow-drop` only for a change you mean.
   - **Never restore the record, its header or the archiver from `c3d0e890`.** If `main`'s copy of one has
     moved past this worktree's, copy `main`'s over it first.
   - Fill in every `<<…>>` placeholder in the three R3 drafts. Re-derive every count, claim and file list in
     them from the final diff; HV2 D-3 names the ones known to change.
   - Rebuild `CHANGELOG.md`, `docs/REFERENCE.md`, `ci.yml` and `AGENTS.md` from **current** `origin/main`.
     - Since `cf711cf4`, ml#2134, #2145 and #2139 touched the first three; run `git log` on each path.
     - AGENTS.md's suite count is `main`'s plus the suites Phase B adds: 174 with one new suite.
     - A fleet PR that lands first raises it (#2138 adds two suites, #2140 and #2159 one each).
     - Confirm with `util/ad-hoc/2026-09-10_agents_md_test_list_drift.py`.
   - Re-run the checks:
     - the suites;
     - markdownlint (the repo pins v0.42.0) and the snippet linter;
     - `util/markdown_structure_delta.py --base origin/main`;
     - flake8, shellcheck and both screens;
     - pre-commit.
   - Open it with `util/open_signed_pr.py`, which sends **whole files**.
4. **Merge it** with `util/safe_merge.py --execute`, read the `MERGED` line, and verify on `main`. **The merge
   approval was granted in session c9277a65; a new session needs a new grant.**
5. **B9** as its own PR: a gitleaks content rule plus a hook. Go is at `/snap/bin/go`. The repo setting
   `secret_scanning_non_provider_patterns` is the owner's to change.

## Owner actions

- **The watchdog deploy has not run.**
  - The primary checkout was synced on 2026-10-05 at 14:23 CDT, after that day's 12:00 run had again exited 2
    with no record.
  - The installed unit (2026-08-26) passes no `--backup-id`. So until the deploy runs, each 12:00 check
    records `JOB_MISSING` instead of checking job 2.
  - Run `bash util/ad-hoc/yamaguchi_watchdog_deploy.bash --backup-id 2`. Use `2` until the web credential
    exists: A0, A and A2 keep that id, and the deploy must be re-run after Procedure B.
  - After the deploy, every check records `ALERT UNREACHABLE` until the web credential exists. That is the
    intended signal, not a failure.
- **Choose R3B DEFECT-1's remedy** (Remaining, item 1). Until then, if job 2 is restored by any route, let no
  backup complete before AC-4's first drill.
  - A's 2026-10-03 measurement found no job on the running server (A:129).
  - §8's STOP is a document, not a lock.
  - The first completed backup's retention pass would delete 6 to 8 of the 9 filesets, and the deletions reach
    Dropbox.
- **R3B wrote five lines to `~/.bash_history`**: stub commands from its guard test (`bash -i`), with no
  secret. Delete them if you like.
- **Fleet PRs**, all open drafts as of 2026-10-05:
  - **#2129** is superseded by ml#2134: close it.
  - **#2128 and #2119** carry statements that ml#2134 made false.
  - **New since ml#2134**:
    - #2137 (docs);
    - #2138 (tests: token encoding, illegal watchdog ids);
    - #2140 (tests: "export-token transport leaks and a whitespace TargetURL"); `_target_url` does accept a
      whitespace-only URL;
    - #2159 (tests: the pre-backup guard).
  - **Older test drafts** #2121, #2124 and #2127 each conflict once in `docs/REFERENCE.md`: keep both sides.

## Verify first

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/sorted-stargazing-garden
git fetch origin main
git log --oneline -2          # c3d0e890 WIP (frozen) over e509353e
sha256sum -c util/ad-hoc/2026-10-04_backup-phase-b-round3/MANIFEST.sha256 | grep -c ': OK'   # 23: the record, RECORD_HEADER.md.in and the archiver FAIL by design; never restore them from c3d0e890
git status --short            # M: those three, the INDEX, the consolidated handoff; ??: this file, three 2026-10-05 scripts, R3's reports, drafts and harness, util/ad-hoc/2026-10-04_ml2115_fix_forward/; nothing staged
git ls-tree --name-only origin/main -- notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md   # non-empty: the record is on main
git diff --stat origin/main -- notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md util/ad-hoc/2026-10-04_archive_phase_b_round_reports.py util/ad-hoc/2026-10-04_backup-phase-b-round3/RECORD_HEADER.md.in   # empty; if one moved on main, copy main's over the worktree's before the re-assembly
bash util/ad-hoc/2026-10-05_reassemble_phase_b_record.bash --check   # IDENTICAL to the existing file, exit 0
PYTHONDONTWRITEBYTECODE=1 python3 util/ad-hoc/2026-10-05_attack_phase_b_archiver.py --scratch <your scratch dir>   # 0 failure(s); checks that need the untracked report files SKIP where they are absent
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_duplicati_wrapper_contract.py   # 33 OK (32 once the installer has run on this host, R3C D-4)
gh pr view 2134 --json state,mergeCommit    # MERGED f01a438c
```

The index and the consolidated handoff are hot files that other sessions edit, so they may differ from
`main`'s copies. Nothing here reads them.

## Limits

**Standing limits** (and every lane's brief must carry them):

- never start, stop, restart, enable, disable or reload a unit, system or `--user`;
- never run a Duplicati binary, never contact 127.0.0.1:8300, and no `sudo`;
- nothing under `/mnt/Backups/Ubuntu/` is read beyond `stat`, and nothing there is touched;
- never read a secret file: `~/.config/duplicati-backup/*`, any `.env` or `*.env`, `/etc/default/duplicati`
  beyond `stat`, `/etc/credstore`, `/etc/duplicati`, or a data-folder database;
- never print an environment variable or a token, and never send the owner's email or any credential to an
  external service;
- no `git stash`; log greps are count-only; no interactive shells (`bash -i` writes `~/.bash_history`);
- no session performs host actions: those are the owner's.

**Harness traps**:

- `git -C <sibling worktree>` is refused. Read a sibling worktree with
  `util/ad-hoc/2026-10-04_wip_worktree_delta.py` instead.
- These are also refused:
  - a heredoc that writes outside this worktree;
  - a Python heredoc whose text names git or another worktree's path;
  - `xargs`;
  - a compound command around `git show … > file`.
- Instead, split the command, put the script in `util/ad-hoc/`, or use the Edit tool.
- The `/tmp` scratch trees are expendable.
