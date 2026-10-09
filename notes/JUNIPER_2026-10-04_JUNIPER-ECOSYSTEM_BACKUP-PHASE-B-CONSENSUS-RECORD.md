# Backup arc, Phase B — validation rounds 2 to 7, the fold-in lanes, the ml#2115 fix-forward lanes and the handoff validations, verbatim reports

**Project**: Juniper (workstation backup infrastructure, host `yamaguchi`)
**Author**: Paul Calnon
**Date**: 2026-10-04 (re-assembled 2026-10-05; rounds 4 to 7 and the fold-in reports added 2026-10-08)
**Procedure**: [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
**Artifacts validated**: Phase B of [`JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`](JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md) §6.2 (rows B1, B3, B4, B5, B7, B8 and B10), including the regenerated [`JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`](JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md)
**Also validated**: the fix-forward of B2 (ml#2115), which landed as ml#2134, and the two handoffs that carried the work between sessions
**Status**: rounds 2 to 7 complete; round 7 found no DEFECT. The first 16 reports landed on `main` on 2026-10-05, AHEAD of the Phase B change they validate, so that they could not be lost with an uncommitted worktree. The change itself (the artifacts and the prose these reports judge) lands with this record's 2026-10-08 additions, in the Phase B PR; the fix-forward ml#2134 landed separately
**Earlier rounds**: round 1 is the assessment's own (its §8); the design's rounds 1–8 are in [`JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`](JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md), [`JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md`](JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md) and [`JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md`](JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md)

---

## Why this record exists

Until it was archived here, every report below lived off `main`: in a session's scratch directory, an
uncommitted worktree or a subagent transcript. A report that is not on `main` does not exist for the next
session (the uncommitted-sibling-worktree trap). Session 652c1204, which ran round 2 on 2026-10-03, was cut
off by a usage limit partway through folding the round in; round 3's lane B was stopped by the next one.

Nothing below is retyped. Each section's first line says where its text came from:

- **Round 2's reports and the 2026-10-03 handoff's validation** are the files each lane wrote itself, in
  session 652c1204's scratch directory. Each was last modified while its lane was still running; the
  session only copied them.
- **The two briefs** are the files the coordinating session wrote for its lanes, unchanged since the first
  lane started.
- **Every later report** is its lane's final message, saved from the transcript.

`util/ad-hoc/2026-10-05_match_reports_to_final_messages.py` confirms all but four sections by content: a
final message, or a lane's Write and Edit calls replayed. It does not replay Bash, and four files were
finished in place by a `sed -i` or a Python `.replace`:

- round 2's lane B, ml#2114 and ml#2115 reports, by their own lanes;
- round 3's brief, by the coordinating session before its first lane started.

For those four the evidence is the file's last writer and its mtime. The 2026-10-04 handoff's re-validation
confirmed the first 14 origins with its own instruments, and its third validation confirmed the 15th.

Every report was screened for credential-shaped content before it was archived
(`util/ad-hoc/2026-10-04_archive_phase_b_round_reports.py`). That archiver parses this record as its header
followed by sections laid end to end. Each section's first line carries the first 16 hex digits of its
body's sha256, and its declared length must end at its closing marker, so nothing quoted inside a report is
read as structure. The record is re-assembled by `util/ad-hoc/2026-10-05_reassemble_phase_b_record.bash`. By
default it takes every report the record already holds from the record itself, so `main` alone is enough to
rebuild it.

**Line numbers a report cites refer to the copy it judged, not to this one.** Round 3's "record:41 / :52 / :58"
are in `c3d0e890`'s copy of this record. The 2026-10-04 handoff's validations cite the 2026-10-05 working
copies of 08:14, 09:14 and 16:30, in turn.

## What round 2 was for

The assessment's §6.2 plan: one round, three lanes, on the PR that closes the STOP's five defects in code,
plus one lane on each executor PR that landed separately (ml#2114 for B6, ml#2115 for B2). The frozen set was
18 files, pinned by a `MANIFEST.sha256`; every lane checked it first. The common brief is archived below.

| Lens | Brief |
| --- | --- |
| A — option names, product behaviour, unit directives | re-probe every option and directive in the 2.4.0.0 source, the installed assemblies and this host's systemd |
| B — consequence | grant the facts; walk the §6.4 checklist with the artifacts in hand and find the step that damages the sole copy, re-locks the database, or leaves the server unreachable |
| C — run the things | dry-run the installer, the re-key script and the password-init helper against scratch trees, with mutations, and re-run the design's reproduction |
| PR lanes — ml#2114, ml#2115 | each executor PR against its own claims |

## What round 2 found

| Lane | BLOCKER | DEFECT | NIT | Verdict line |
| --- | --- | --- | --- | --- |
| A | 1 | 6 | 7 | `systemctl revert` deletes the installed unit; the 102 run does not encrypt; the wrapper admits `DUPLICATI__*` |
| B | 2 | 5 | 3 | the same BLOCKER; the clearing block claims an unmerged B2 |
| C | 1 | 7 | 6 | the same BLOCKER, found by reading (it could not be demonstrated without root) |
| ml#2114 | 1 | 3 | 5 | refuted on claims, not code: a one-stick run is `FAILED` |
| ml#2115 | 1 | 1 | 5 | refuted on one claim: `export` cannot succeed on 2.4.0.0 |

**The BLOCKER all three main lanes found independently**, each by reading the product and `systemctl(1)` — no lane
could reproduce it without root: `systemctl revert duplicati.service` would delete the
installed `/etc/systemd/system/duplicati.service`. A dpkg vendor unit exists under `/usr/lib/systemd/system/`,
and revert removes any unit that overrides a vendor one, so the re-key's encrypt start would have run the vendor
unit, unconfined and without `LoadCredential=`, on a cleartext database with the keys already swapped.

## Disposition of round 2

The fold-in meant to apply every finding, and recorded none as dissent. The assessment's §8 "Round 2" entry
lists where each one landed. Round 3 tested that list as a claim, and found it incomplete: of the 38 lane A/B/C
findings, 30 are fixed, 7 only in part, and 1 fixed but wrong (see "What round 3 found").

- **Code** (the 2026-10-03 session, before it was cut off): the re-key script and its new gate, the
  password-init helper, the wrapper (2.2.0), the installer (1.2.0), the contract, the service unit's comment,
  the snapshot timer, and the test suite (33 tests).
- **Prose** (2026-10-04): the design, regenerated through the clearing script's 54 edits — 53 to prose and one
  declared fence edit — and the assessment.
- **ml#2114**: its own agent fixed it before it merged.
- **ml#2115**: merged with its BLOCKER and DEFECT. Both are fixed by ml#2134 (next section).

## The ml#2115 fix-forward lanes

Two lanes ran on the fix-forward's first draft (local commit `663443e8`), launched together:

- **F1 — product fidelity.** Re-derived the export flow from the 2.4.0.0 tag and drove the real CLI against a
  model server. 0 BLOCKER, 2 DEFECT, 6 NIT; the client's wire behaviour was not refuted.
- **F2 — consequences.** Callers, exit codes, host facts, its own mutations, and the concurrent fleet PRs.
  0 BLOCKER, 3 DEFECT, 8 NIT; the code was not refuted.

**Disposition**: everything is applied in ml#2134 — F1 D-1 included: the stub now answers 500, not 401, for a
token it never signed — except two findings that belong elsewhere:

- **F1 D-2** asks the guard dry-run to refuse an empty URL. That is design text, so it belongs to Phase B and is
  done in P0 step 10's fence.
- **F2 D-3** asks for fleet-PR actions — closing #2129, and the stale statements in #2128 and #2119. Those are
  the owner's, and were put to the owner rather than taken.

## What round 3 was for

Round 2 refuted things, so the assessment's own rule applies ("round N+1 only if round N refutes something,
scoped to the delta"). Round 3 validates the fold-in: every change made after round 2's frozen set, and whether
each one fixes what round 2 found without breaking anything else. It read local commit `c3d0e890` (26 files,
pinned by a manifest that every lane checked), with three lenses: **A** fold-in fidelity, **B** the consequences
of the folded-in procedure, **C** running the things on copies. Lane B's brief asked for an end-to-end walk of
procedures A0, A, A2 and B, not only the delta. It was stopped at the 2026-10-04 usage limit and resumed on
2026-10-05, still reading `c3d0e890`.

## What round 3 found

| Lane | BLOCKER | DEFECT | NIT | Verdict line |
| --- | --- | --- | --- | --- |
| A — fold-in fidelity | 0 | 6 | 8 | the `revert` fix holds; 30 of round 2's 38 findings fixed, 7 in part, 1 fixed but wrong |
| B — procedure consequences | 0 | 4 | 11 | the fold-in's own changes hold; the first backup after recovery deletes the fileset AC-4 drills |
| C — run the things | 0 | 5 | 13 | the reproduction and every gate hold; 14 of 25 mutants of the new code survive the suites |

Lanes A and C found the same three defects, independently. Lane B's resume message said it need not re-derive
them:

- `--parameters-file` gets past the env-file deny list. The server reads options from that file and merges them
  over argv, so `--disable-db-encryption` could return through it.
- The re-key's EXIT trap prints a fixed recovery block that is wrong in four failure states. Lane B's N-11
  describes a timed-out decrypt start, which lane B says may duplicate them; it is lane A's D-4 case.
- Round 2's request for a `ConnectionString` count in the re-key's pre-flight was not carried out.

Lane A adds:

- the residue list is not the round-4 record's open rows;
- the job-2 residue still says "six";
- the web credential's line format is missing from the design.

Lane B adds four defects. All four are in the procedure on `main` as well, outside the fold-in's delta, where
§8's STOP still holds them; the fold-in's P0.5b placement adds a dependence on the second:

- **The first backup deletes the 2026-09-18 fileset.** Its retention pass keeps 1 to 3 of the 9 old filesets,
  and the 09-18 one only for a first run between 2026-10-17 22:14Z and 2026-10-18 14:00Z. AC-4's first drill,
  the gate for §10.2 step 1, is sequenced after that backup. From 2026-10-18 no surviving fileset holds a copy
  of the server database, so Procedure A0 could not be re-run.
- **An unread startup delay.** Between the unit's first start and step 10's `pause` there is a time limit that
  no step states, reads or sets. Once it lapses the overdue job starts unguarded, and "`resume` fires the
  overdue backup" becomes false.
- **Procedure B's rebuild tool** creates a job that is already overdue, on a fresh index, while the scheduler
  runs. The run deletes nothing, but it starts before any guard or verification.
- **§7.3.6's recovery** for an unknown root-era UI password cannot work on a 2.1+ database: it leaves
  `pbkdf-config`, so the hand start gets exit 103.

Lane C adds:

- the re-key's dry-run test is not hermetic on the owner's host;
- the real code paths have too few tests (the mutant survivors).

## The handoff validations

Each handoff that carried this work to a new session was validated before it landed. All four reports are
archived below.

- **The 2026-10-03 handoff** (`HANDOFF_2026-10-03_backup-phase-b-fold-in-pending.md`), validated on
  2026-10-04: REFUTED, two BLOCKERs. Session 652c1204 corrected the handoff before it landed (#2126).
- **The 2026-10-04 handoff** (`HANDOFF_2026-10-04_backup-phase-b-round3-fold-in-pending.md`), validated on
  2026-10-05: REFUTED in part — 2 BLOCKER, 4 DEFECT, 10 NIT. Session c9277a65 applied them before this record
  landed:
  - B-1: the handoff's verify block names the pins that fail by design, and checks `git status` and that this
    record reached `main`;
  - B-2: lane B was resumed rather than lost, and its report is above;
  - D-1 to D-4: the suite count is `main`'s plus one; the standing limits are restored; the re-assembly is a
    saved script; and each report states its own origin. Until then the archiver wrote "a file the 2026-10-03
    session saved verbatim" for every file source, which was false for five sections;
  - the NITs, in the handoff and the Phase B PR's draft. This header carries the record parts of round 3's
    R3A N-1 and R3C N-9.
- **The same handoff, re-validated** on 2026-10-05 after that fold-in: REFUTED in part — 0 BLOCKER, 3 DEFECT,
  11 NIT. Session c9277a65 applied them before this record landed:
  - D-1: this header and the match script say it confirms 10 of the 14 sources by content, and why;
  - D-2: one list of entries now drives both re-assembly modes, a missing file is refused, and the archiver
    refuses to drop a report the record holds;
  - D-3: the Phase B drafts' false sentences are fixed, and the handoff orders every count and file list
    re-derived after the fold-in;
  - the NITs, in the handoff, the drafts and the archiver. N-5 is why each section's line now carries a hash;
    `util/ad-hoc/2026-10-05_attack_phase_b_archiver.py` runs A6, A7 and the D-2 sequence against copies;
  - N-8: round 3's lane C harness is carried as `util/ad-hoc/2026-10-04_backup-phase-b-round3/r3c-harness/`.
    It existed only in a tmpfs scratch directory and an untracked worktree copy.
- **The same handoff, validated a third time** on 2026-10-05, on the re-validation's changes only: REFUTED in
  part — 0 BLOCKER, 1 DEFECT, 9 NIT. Session c9277a65 applied them before this record landed, and ran no
  fourth round: the one DEFECT was this report's own missing slot, and the attack script covers every code
  change. The changes:
  - D-1: this report is archived as the record's 16th section, and every count says so;
  - N-1: the harness's six pyflakes findings are fixed before landing, because CodeQL review threads would
    block the merge. CodeQL still raised 12 threads, on seven lines pyflakes does not flag, when the first
    archive PR (#2176) opened. Those lines are fixed too, and that PR was replaced by one with a single
    commit;
  - N-2 to N-4: the archiver parses the record strictly. A report file or origin that disagrees with the
    archived one is refused unless `--replace` names it. A header edit, or text outside every section, is
    refused rather than discarded. `--check` compares bytes and exits 1 on a difference. The attack script
    covers each case;
  - N-5 to N-9: the harness README, the provenance wording, the drafts' CHANGELOG slot, the routing of
    round 3 lane B's open questions, and the small errors.

## Disposition of round 3

Folded in on 2026-10-08 by session 097ae87b, in three lanes that owned disjoint files: C1 (the wrapper, the
installer, the env contract and the units), C2 (the re-key, its gate and the password-init hand start) and P
(the clearing script, the design and the assessment). Their briefs and reports are archived below. Every one of
round 3's 15 DEFECTs and 32 NITs is fixed, or recorded in the assessment's §8 as residue with a reason. The
assessment's §8 "Round 3" entry gives the disposition by finding id. The owner made one ruling (R3B DEFECT-1, 2026-10-08): retention is
**suspended** through recovery, so step 10's edits remove `retention-policy`; after AC-4's first drill passes it is
restored as `2W:1D,6M:1W,2Y:1M,5Y:2M`, replacing `1W:1D,1M:1W,1Y:1M,3Y:2M`.

Two changes go beyond the findings as written:

- C1 replaced the env file's deny list with an **allow-list** of tunables (R3A D-1's alternative). The deny list
  had missed a channel in two consecutive rounds, first `DUPLICATI__*`, then `--parameters-file`.
- C2 refuses an `enc-v1:` blob in `BackupTargetUrl` only on rows of no backup, because a live backup's rows are
  rewritten (verified at the 2.4.0.0 tag).

## What round 4 found

Three lanes reviewed the frozen fold-in (local commit `a0ff619c`): A (fold-in fidelity), B (an end-to-end walk of
A0, A, A2 and B for damage to the sole copy) and C (run and attack the code). Totals: 0 BLOCKER, 6 DEFECT, 28 NIT;
A's D-1 and C's DEFECT-1 are the same defect.

- **The suites depended on the host's mounts** (A D-1, C DEFECT-1). `${DUPLICATI_REQUIRE_MOUNT:-…}` cannot be
  emptied, so every wrapper and installer test needed `/mnt/Backups` mounted and would have failed on CI.
- **An allow-listed option did not exist** (A D-2). The server's option is `webservice-suppress-welcome-page`.
- **The first `resume` ran a stale copy of the job** (B DEFECT-1). On A0 and A2 the job queued at the first start
  is copied before step 10's edits, so it had the old retention, the old tempdir and no guard. Nothing was damaged,
  but only by accident.
- **B's Verify could not run while paused** (B DEFECT-2).
- **The pre-flight missed orphaned `Option`/`Source` rows** (C DEFECT-2).

## Disposition of round 4

All folded in on 2026-10-08 by the same three lanes, resumed. The highlights:

- wrapper 2.4.0 honours an empty mount override, and both of its lists are pinned against a vendored copy of the
  product's option table;
- step 10 ends with a restart, so the queue is rebuilt from the edited job (verified in the source), then an
  `export` read-back;
- B's Verify runs in a pause/resume cycle;
- the pre-flight counts orphans in all three child tables.

The assessment's §8 "Round 4" entry has the disposition by finding id.

## Round 5 and its disposition

A two-lane confirmation round on round 4's delta (local commit `9ce2f602`), code and procedure: 0 BLOCKER,
4 DEFECT, 12 NIT. The code lane found the installer's hint still said "pause" where round 4 says stop, and an
env-file mode check that settled the owner's open decision O-12. The installer now accepts either of O-12's two
forms. The procedure lane found two gaps:

- the server's default options (`BackupID` −1) are invisible to `export`, so step 8 now clears them with
  `sqlite3`;
- a Procedure B Repair deletes extra remote volumes, so it now runs `--dry-run` first, copies every named file
  aside, and is named as a third, conditional exception to §8's "nothing is deleted" rule.

All four DEFECTs and every NIT are fixed; the assessment's §8 "Round 5" entry has the disposition.

## Rounds 6 and 7, and their disposition

Round 6 was a single combined lane on round 5's delta (local commit `ee7fcee7`). It found 0 BLOCKER, 3 DEFECT and
4 NIT:

- **DEFECT-1, the Repair step.** As written, the dry-run / copy-aside step read one of the four message IDs a
  Repair logs deletions under. It could not be queued with `--dry-run` at all, and its lines never reach the stored
  job log. It is now done through three temporary job options and a `DryRun`-level log file under
  `/home/duplicati`. Every `Would…Delete…File` line is copied aside, and the options are removed and checked with
  `export` before the real Repair.
- **DEFECT-2, the A0 restore guard.** The script's refusal to restore into the backup Source used `readlink -f`,
  which a path two or more new levels deep got through. It now uses `realpath -m`, and its test no longer needs
  `/home/pcalnon` to exist (it would have failed on CI).
- **DEFECT-3, restoring defaults.** Restoring the server-default `keep-time` / `keep-versions` would combine with
  the job's policy and void the keep/delete table. Those two are never restored.

Round 7, on round 6's delta (local commit `19ae4aa9`), found 0 BLOCKER, **0 DEFECT** and 7 NIT. All seven are
fixed, and the assessment's §8 "Round 6" and "Round 7" entries have the disposition. No eighth round ran: round 7
found no DEFECT, and its NITs were wording, one test pin and the record's own counts.

---

## Round 2 — the common brief

Archived verbatim (5,443 characters, sha256 `c35aa0fd91fd61b9`), lifted from the brief session 652c1204 wrote for round 2's lanes on 2026-10-03.

<!-- markdownlint-disable -->

# Phase B validation round — common brief (read first, then your lane's lens)

You are one of three independent validation lanes on a frozen set of repository changes (Phase B of
`notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`,
its section 6.2). Your job is to REFUTE: try to prove the artifacts wrong. Default to REFUTED when
uncertain; mark anything you cannot test as UNVERIFIABLE and say what would test it. Do not confirm
by re-reading — re-derive every claim from the source of truth (the files, the installed product's
assemblies, the product source, a dry run).

## Where the artifacts are

Working tree (read it; run its scripts only in the modes named by your lane; write nothing in it):

    /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/cached-swinging-summit

The frozen set and its checksums: `val/PB/MANIFEST.sha256` in the scratch root
`/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/652c1204-ac9f-426c-91fd-7bc68338e828/scratchpad/`.
FIRST run, from the working tree directory: `sha256sum -c <scratch>/val/PB/MANIFEST.sha256`. If any
line is not `OK`, stop and report the mismatch — the set moved under you and your findings would
not bind.

What changed versus `main`: `git diff origin/main --stat` in the working tree (ignore the five
`prompts/`/`notes/..CANOPY..` files that `main` changed and this tree has not; they are not part of
the set). The four untracked files are new: `tests/test_duplicati_wrapper_contract.py`,
`util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py`,
`util/ad-hoc/2026-10-03_password_init_hand_start.bash`, `util/ad-hoc/2026-10-03_rekey_settings_key.bash`;
so is `util/systemd/duplicati-env.contract` (it is NOT listed by `git status` because the repository
ignores `*.env`-shaped names — this one was renamed to escape that rule; check it is not ignored:
`git check-ignore -v util/systemd/duplicati-env.contract` must print nothing).

Design document of record ("D"): `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`.
Its tagged code blocks (`# file: <path>` first line inside a fence) are generated from the repository
files by `util/ad-hoc/2026-09-22_stage_design_artifacts.py --from-repo`; its prose edits for this
change are `util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py`. The PR's claim is that
running those two scripts on `main`'s copy of D reproduces this tree's D byte-for-byte.

A read-only copy of the Duplicati 2.4.0.0 source (the installed version) is at
`<scratch>/val/B/src` (search it with grep; cite file and line). The installed assemblies are under
`/usr/lib/duplicati/` (549 DLLs); `util/ad-hoc/2026-09-22_duplicati_literal_scan.py <literal>...`
scans them in both encodings (a .NET string literal is UTF-16LE — an ASCII grep gives false
negatives).

## Hard limits (a breach is worse than any finding)

- Never start, stop, restart or reload `duplicati.service` or any other unit; never `daemon-reload`.
- Never run any Duplicati binary — `duplicati-server --version` STARTS a server; `duplicati-cli`,
  `duplicati-database-tool` likewise. The dry-run modes you are asked to use set the server path
  to `/bin/true` or print without executing; keep it that way.
- Never use `sudo`. Everything in your lane runs as the current user.
- Never read a secret file: `/home/duplicati/.config/Duplicati/.env`, anything under
  `~/.config/duplicati-backup/`, `/etc/credstore/`, `/etc/credstore.encrypted/`, any
  `_yamaguchi_keys/` directory, `~/.bash_history`, `~/.viminfo`, `resources/duplicati.env`.
  `stat`/`ls -la` is allowed; `cat`/`grep` of their contents is not.
- Never grep the journal or `/var/log` for values. Count-only (`grep -c`) at most, and only if your
  lane needs it (none does).
- Never touch anything under `/mnt/Backups/`.
- Never print environment variables, tokens or credential files, including in debugging listings.
  Never send the owner's email address or any credential to an external service (no network calls
  are needed for this round at all).
- Never `git stash`, `git checkout`, `git commit`, `git push`, or modify a tracked file. Read-only
  git (`git show`, `git diff`, `git log`) is fine.
- Write only under `<scratch>/val/PB/<your lane letter>/` (create it). Scratch trees you build for
  dry runs go there too.

## Report format

Write `<scratch>/val/PB/<lane>.md` and return the same content as your final message. Structure:

1. `## Manifest` — the `sha256sum -c` result (all OK, or stop).
2. `## Findings` — ordered by severity: BLOCKER (would damage the sole local copy, re-lock the
   database, leave the server unreachable, leak a secret, or make the PR unmergeable),
   DEFECT (wrong but recoverable), NIT. For each: file + line or heading; the claim as written;
   the evidence (the command you ran and the exact output excerpt, or the source file:line); what
   the correction should be. A claim you tested and could NOT refute is listed under
   `## Not refuted` with the test that failed to refute it — that list is as important as the
   findings. `## Unverifiable` names what you could not test and why.
3. `## Slips` — anything you did that touched the hard limits, plainly, or "none".

Cite D by section heading and the line number of this tree's copy. Do not quote any secret value
(there should be none anywhere in the set; if you see one, report its LOCATION only).

<!-- markdownlint-enable -->

---

## Round 2, lane A — option names, product behaviour, unit directives

Archived verbatim (40,006 characters, sha256 `50d29d05e08b2ac1`), lifted from the report file the lane wrote itself, in session 652c1204's scratch directory, on 2026-10-03.

<!-- markdownlint-disable -->

# Lane A — option names, product behaviour, systemd directives (re-probed against the installed product, the 2.4.0.0 source and this host's systemd)

Working tree: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/cached-swinging-summit` (HEAD `6a1514e4`, based on `b7840a14`; `origin/main` is at `c01c837e`, a docs commit on D — not an ancestor of HEAD).
Source snapshot: `<scratch>/val/B/src` = 26 files of tag `v2.4.0.0_stable_2026-09-03` (`b3e9268c`), plus `attag/` history copies. Where a file is absent from the snapshot I say so and use the installed DLLs' literals instead.
Installed product: `/usr/lib/duplicati/` (1,443 files). systemd: 259 (259.5-0ubuntu3.4).
Lane artifacts: `<scratch>/val/PB/A/` (`D.diff`, `D.plus`, `literal_scan_options.txt`, `units/` with the three copied units, the saved man pages, `check_directives.py`, `syscall_sets.py`; `wrap/` with the mutation env files, `stub.sh`, `run_m4.bash`, `run_m5.bash`).

## Manifest

```
$ sha256sum -c <scratch>/val/PB/MANIFEST.sha256      (run from the working tree, before and after the lane)
.github/workflows/ci.yml: OK
docs/REFERENCE.md: OK
notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md: OK
notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md: OK
scripts/duplicati-wrapper.bash: OK
util/ad-hoc/2026-09-21_lint_design_snippets.py: OK
util/ad-hoc/2026-09-22_stage_design_artifacts.py: OK
util/ad-hoc/yamaguchi_server_db_snapshot.py: OK
util/install_duplicati_service.bash: OK
util/systemd/duplicati.default: OK
util/systemd/duplicati.service: OK
util/systemd/yamaguchi-server-db-snapshot.service: OK
util/systemd/yamaguchi-server-db-snapshot.timer: OK
util/systemd/duplicati-env.contract: OK
tests/test_duplicati_wrapper_contract.py: OK
util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py: OK
util/ad-hoc/2026-10-03_password_init_hand_start.bash: OK
util/ad-hoc/2026-10-03_rekey_settings_key.bash: OK
exit=0
$ git check-ignore -v util/systemd/duplicati-env.contract ; echo ci-exit=$?
ci-exit=1            (prints nothing: not ignored)
```

All 18 OK at the start; re-run at the end (see the last section) — still all OK. `git status --short` after the lane shows nothing beyond the set (the test was run with `PYTHONDONTWRITEBYTECODE=1`).

## Findings

### BLOCKER-1 — `systemctl revert duplicati.service` deletes the installed hardened unit, not just the drop-in; the re-key's encrypt start then runs under the VENDOR unit (no `LoadCredential=`, `Restart=always`, no confinement) with the database already decrypted and the keys already swapped

**Where the claim is made.** `util/ad-hoc/2026-10-03_rekey_settings_key.bash:40-41` ("`systemctl revert duplicati.service` (the drop-in is removed; the unit is back to the installed text)"), `:109`, `:156-157` (`run systemctl revert "${UNIT}"` followed only by `[[ -e "${DROPIN}" ]]`); D § 8 P0.5b/P1 step 1, line 2374 ("after one `mv` swaps the keys and `systemctl revert` removes the drop-in"); D § "STOP clearing" item 2, line 1878 ("removes with `systemctl revert`"); the assessment's note 6a (`…ASSESSMENT-AND-RECOVERY-PLAN.md:233`, "removed with `systemctl revert`, so nothing durable carries `--disable-db-encryption`"); `util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py:200,365` (the prose generator); `tests/test_duplicati_wrapper_contract.py:193-198` pins the `revert` step into the expected dry-run order.

**Evidence.** This host's `systemctl(1)`:

```
$ man -P cat systemctl | grep -n -A14 '^ *revert '
 996:       revert UNIT...
 997-           Revert one or more unit files to their vendor versions. This command
 998-           removes drop-in configuration files that modify the specified units,
 999-           as well as any user-configured unit file that overrides a matching
1000-           vendor supplied unit file. Specifically, for a unit "foo.service"
1001-           the matching directories "foo.service.d/" with all their contained
1002-           files are removed, both below the persistent and runtime
1003-           configuration directories (i.e. below /etc/systemd/system and
1004-           /run/systemd/system); if the unit file has a vendor-supplied version
1005-           (i.e. a unit file located below /usr/) any matching persistent or
1006-           runtime unit file that overrides it is removed, too.
```

The installer places the hardened unit exactly where that sentence bites — `util/install_duplicati_service.bash:44`: `UNIT_DST=/etc/systemd/system/duplicati.service` — and a vendor-supplied version exists and is package-owned:

```
$ dpkg -S /lib/systemd/system/duplicati.service
duplicati: /lib/systemd/system/duplicati.service
$ ls -la /usr/lib/systemd/system/duplicati.service
-rw-r--r-- 1 root root 461 Sep 21 01:44 /usr/lib/systemd/system/duplicati.service
$ systemctl show duplicati.service -p FragmentPath -p Restart -p ProtectSystem -p ExecStart     (read-only)
FragmentPath=/usr/lib/systemd/system/duplicati.service
Restart=always
ProtectSystem=no
ExecStart={ path=/home/duplicati/bin/duplicati-wrapper.bash ; argv[]=/home/duplicati/bin/duplicati-wrapper.bash --daemon-opts="${DAEMON_OPTS}" ; ... }
$ ls -la /home/duplicati/bin/
drwxrwxrwx 2 duplicati duplicati 4096 Sep 20 16:53 .
lrwxrwxrwx 1 duplicati duplicati   82 Sep 20 16:53 duplicati-wrapper.bash -> /home/pcalnon/Development/python/Juniper/juniper-ml/scripts/duplicati-wrapper.bash
```

So on the recovery day the script's step 7 (`:156`) removes `/etc/systemd/system/duplicati.service` (the blessed D-6 copy), and `daemon-reload` + `start` (`:158-160`) starts the vendor fragment: `/home/duplicati/bin/duplicati-wrapper.bash` (a symlink into the pcalnon-writable primary checkout, inside a 0777 directory) with the glued `--daemon-opts` word, **no `LoadCredential=`** (so no `$CREDENTIALS_DIRECTORY`, so no key unless the env file carries one), `Restart=always`, `ProtectSystem=no`, no `InaccessiblePaths=`. With `/etc/default/duplicati` by then carrying `--require-db-encryption-key` (D-1), the server throws `RequireDbEncryptionKey` (`Server/Program.cs:1249-1250`) and `Restart=always` loops it; `wait_started` (`:81-95`) dies after 120 s. The script exits **after** step 5 decrypted every field (`Connection.cs:131-153`) and **after** step 6 moved the keys (`:153-154`) — leaving: the database cleartext on disk, the old key at `…-key.old`, the new key at the credential path, the hardened unit file gone, and a flapping unconfined unit. The script's own `:157` check (`drop-in still present after revert`) cannot see any of this because the drop-in *is* gone. If the vendor unit happened to start the server (e.g. a key reachable through `/etc/duplicati/env`), it would run with no confinement and `Restart=always` on a cleartext database — the opposite of the STOP's item 2 ("the re-key cannot re-lock the database").

**Correction.** Remove the drop-in the same way it was written: `rm -f "${DROPIN}"; rmdir "${DROPIN_DIR}" 2>/dev/null || true; systemctl daemon-reload` (never `revert` while `/lib/systemd/system/duplicati.service` exists — and it exists for as long as the `duplicati` package is installed; P4 deleting `/usr/lib/duplicati` does not remove it). Update the four prose sites and the test's expected order (`tests/test_duplicati_wrapper_contract.py:198`) in the same change; the dry-run test would otherwise keep certifying the destructive step. Add to the preflight: refuse if `/etc/systemd/system/duplicati.service` is absent, and after the drop-in removal assert `systemctl show -p FragmentPath` still names `/etc/systemd/system/duplicati.service`.

### DEFECT-1 — the `--webservice-password-init` run (exit 102) does **not** encrypt the database and does **not** set `encrypted-fields=True`; the hand-start script's success message and the assessment's B10/step-10 verification are wrong

**Claims.** `util/ad-hoc/2026-10-03_password_init_hand_start.bash:22-24` ("the same start encrypts the database under the new settings key (the first start with a key re-encrypts every field)"), `:107` (dry-run text), `:137` ("exit 102: UI password set and the database encrypted under the settings key. Verify on a COPY: autogenerated-passphrase=False, encrypted-fields=True"); `…ASSESSMENT-AND-RECOVERY-PLAN.md:228` (B10: "verifies `autogenerated-passphrase=False` and `encrypted-fields=True` on a copy") and `:277` (step 10: "exit **102**, `autogenerated-passphrase=False` and `encrypted-fields=True` verified on a copy").

**Evidence (Server/Program.cs, 2.4.0.0).** `Main` calls `GetDatabaseConnection` (`:257`), `UpgradePasswordToKBDF()` (`:263`), then `AdjustApplicationSettings` (`:286`) and **returns its exit code at `:288`**:

```
286:                var adjustres = AdjustApplicationSettings(connection, commandlineOptions);
287:                if (adjustres.HasValue)
288:                    return adjustres.Value;
...
295:                DuplicatiWebserver = StartWebServerAsync(commandlineOptions, connection, logHandler, applicationSettings).Await();
...
324:                connection.ReWriteAllFieldsIfEncryptionChanged();
```

`AdjustApplicationSettings` returns `EXITCODE_INITPASSWORD_SUCCESS` at `:682` (and 103 at `:686`). The only writer of `encrypted-fields = True` in the server is `Connection.ReWriteAllFieldsIfEncryptionChanged` (`Library/RestAPI/Database/Connection.cs:131-153`, the flag at `:146` through `ServerSettings.EncryptedFields`, `ServerSettings.cs:851-855`); `grep -rn 'EncryptedFields\s*=' src/` finds no other writer (`WipeEncryption.cs:154` sets it to `False`). That call sits at `:324`, after the return. What the 102 run **does** write: `UpgradePasswordToKBDF` (`ServerSettings.cs:363-392`) and `SetWebserverPassword` (`:398-411`) each `SaveSettings()` (`:209-219`) → `Connection.SetSettings(…, -2)` (`Connection.cs:384-391`), which encrypts only names in `_encryptedFields` (`:66-91`: `pbkdf-config`, `jwt-config`, `remote-control-config`, …) — so after exit 102, `pbkdf-config` is an `enc-v1:` blob under the new key, `autogenerated-passphrase` is `False` (`:407`), and `encrypted-fields` is unchanged (`False`, or absent on an empty database). On the A2 path every other field the wipe left cleartext stays cleartext until the unit's first start, which does reach `:324` (`EncryptedFields(False) != true` → rewrite → `True` → `VACUUM`).

**Why it matters.** The script tells the operator the database is encrypted when it is not, and the prescribed verification (`encrypted-fields=True` on a copy) **fails** on a correct run — inviting a re-run (which returns 103, whose message then points the operator at the A0 procedure) or a conclusion that the key was not applied. The end state after the unit's first start is right; the description of the intermediate state and the gate are wrong.

**Correction.** In the script (`:22-24`, `:107`, `:137`) and in B10 / step 10: "sets the password; `autogenerated-passphrase=False` and `pbkdf-config` carries `enc-v1:` + sha256(new key); `encrypted-fields` becomes `True` only at the unit's first start — verify it then, not here." Keep the timer-enable ordering as it is (the snapshot unit's comment `:21-24` already keys it to the unit's first start).

### DEFECT-2 — the wrapper's allow-list admits `DUPLICATI__*` names the server maps onto **every** option, including `disable-db-encryption`, `allow-insecure-datafolder` and `settings-encryption-key`; `/etc/duplicati/env` is unblessed by design, so this is a second silent channel for exactly the flag D says must never live in a durable file

**Claims.** `scripts/duplicati-wrapper.bash:44` (`ENV_EXPORT_ALLOW='^(SETTINGS_ENCRYPTION_KEY|DUPLICATI__[A-Z0-9_]+|TMPDIR|TZ|LANG|LC_ALL)$'`) with `:106-108` ("Only names the server is meant to read may be exported"); `util/systemd/duplicati-env.contract:27-28`; `util/systemd/duplicati.default:5-7` and D:1878/2374 ("that flag must never live here… AC-14 cannot see it"); `util/systemd/duplicati.service:109-117` (pre-existing on `main`): "DUPLICATI__DISABLE_UPDATE_CHECK and DUPLICATI__USAGE_REPORTER_LEVEL do NOT exist… The generic DUPLICATI__ mapping is LOWER-case with '-' -> '_' (run-script-example.sh ll. 76-80)".

**Evidence.** The server composes the names at runtime, upper-case, for every supported option (so the literal scan's NOT-FOUND is the composed-name trap the scanner's own docstring warns about):

```
Server/Program.cs
131:        private static readonly string ENV_NAME_PREFIX = AutoUpdateSettings.AppName.ToUpperInvariant();
971:        private static void ApplyEnvironmentVariables(Dictionary<string, string> commandlineOptions)
973:            foreach (var key in SupportedCommands.SelectMany(x => (x.Aliases ?? []).Prepend(x.Name)).Distinct())
976:                if (commandlineOptions.ContainsKey(key))   // Commandline options take precedence
977:                    continue;
979:                var envkey = $"{ENV_NAME_PREFIX}__{key.Replace('-', '_').ToUpperInvariant()}";
981:                if (!string.IsNullOrWhiteSpace(envval))
982:                    commandlineOptions[key] = envval;
986:            if (... SETTINGS_ENCRYPTION_KEY ... && string.IsNullOrWhiteSpace(commandlineOptions.GetValueOrDefault(SETTINGS_ENCRYPTION_KEY_OPTION)))
```

`SupportedCommands` includes `disable-update-check` (`:1588`), `allow-insecure-datafolder` (`:1591`), `disable-db-encryption` (`:1592`), `require-db-encryption-key` (`:1594`), `settings-encryption-key` (`:1595`). `DataFolderManager.cs:71-72` documents `DUPLICATI__ALLOW_INSECURE_DATAFOLDER` separately. The lower-case form the unit's comment cites (`/usr/lib/duplicati/run-script-example.sh:76-80`, `Library/Modules/Builtin/RunScript.cs:361` `"DUPLICATI__" + kv.Key.Replace('-', '_')`) is the mapping the product **exports to run-scripts**, the opposite direction. Mutation `m4j` (`wrap/run_m4.bash`): `DUPLICATI__ALLOW_INSECURE_DATAFOLDER=true` in the env file → wrapper exit 0, exported to the child (stub shows it). The installer keeps the env file out of the blessed set on purpose (`util/install_duplicati_service.bash:58-59`), and `--disable-db-encryption` is not on argv, so `DUPLICATI__DISABLE_DB_ENCRYPTION=true` there is honoured at `:982`, satisfies `--require-db-encryption-key` (`:1249`), decrypts every field at the next start (`Connection.cs:131-153`), writes no "Unknown option supplied" line (AC-14 blind) and trips no drift gate (D-6 blind). `DUPLICATI__SETTINGS_ENCRYPTION_KEY=` set there wins over the `LoadCredential=` key, because `:973-983` runs before `:986` (fail-closed: `SettingsEncryptionKeyMismatchException`, `EncryptedFieldHelper.cs:138-139`). The file is `0640 root:duplicati`, so the actor is root — the same trust as `/etc/default/duplicati`, which D does guard.

**Correction.** Drop the `DUPLICATI__[A-Z0-9_]+` wildcard from `ENV_EXPORT_ALLOW` (nothing in the set uses it), or deny-list `DUPLICATI__DISABLE_DB_ENCRYPTION`, `DUPLICATI__ALLOW_INSECURE_DATAFOLDER`, `DUPLICATI__SETTINGS_ENCRYPTION_KEY`, `DUPLICATI__REQUIRE_DB_ENCRYPTION_KEY`, `DUPLICATI__WEBSERVICE_PASSWORD*`; state the channel in the contract. Fix the unit comment (`duplicati.service:109-117`): the server **does** read `DUPLICATI__DISABLE_UPDATE_CHECK` (upper-case, composed at runtime); `DUPLICATI__USAGE_REPORTER_LEVEL` indeed does not exist (no such server option). The `Environment=` lines and the option in `DAEMON_OPTS` are correct as they stand.

### DEFECT-3 — `--print-command` redaction misses `--webservice-password-init=` and `--webservice-pre-auth-tokens=`

**Claim.** `scripts/duplicati-wrapper.bash:20-21` ("No secret value is ever printed -- including by the error paths") and `:170-171` (`(password|passphrase|key|token)=` → `<redacted>`).

**Evidence** (`wrap/run_m5.bash`, M5d, dummy values):

```
would exec: /bin/true ... --settings-encryption-key=\<redacted\> --webservice-password-init=not-a-real-pw
```

The regex requires the word immediately before `=`; `password-init=` and `tokens=` (plural, `WebServerLoader.cs:112` `webservice-pre-auth-tokens`) do not match. Both are `Password`/secret-typed server options (`Program.cs:1571`, `:1581`). The assessment's step 10 has the operator run `--print-command` by hand.

**Correction.** Match on the option **name**: `^--[^=]*(password|passphrase|key|token|secret)[^=]*=` — or redact every option whose name is in the server's `Password`-typed set.

### DEFECT-4 — the re-key exit gate scans three of the five encrypted-bearing columns; `ConnectionString.BaseUrl` is neither re-keyed by the product's rewrite pass nor checked by the gate, and the old key is shredded on a pass

**Claim.** `util/ad-hoc/2026-10-03_rekey_settings_key.bash:42-44`, `:180` (`Option.Value`, `Backup.TargetURL`, `Source.Path`), `:188-189` (gate), `:218` (shred old key); D:1878/2374 ("every field is re-encrypted").

**Evidence.** The product's own list of columns that carry `enc-v1:` values: `CommandLine/DatabaseTool/Commands/WipeEncryption.cs:97-103` — `Backup.TargetURL`, `Source.Path`, `ConnectionString.BaseUrl`, `BackupTargetUrl.TargetURL` — plus password-named `Option.Value` (`:116`). `ReWriteAllFieldsIfEncryptionChanged` (`Connection.cs:131-153`) rewrites backups via `AddOrUpdateBackup` — which covers `BackupTargetUrl` because `Backup.LoadChildren` loads them (`Backup.cs:54`) and `AddOrUpdateBackup` writes them (`Connection.cs:893`) — and the `-1`/`-2` settings; it never touches `ConnectionString` (written only by `AddConnectionString`/`UpdateConnectionString`, `:1647-1694`, both encrypting with the current key). A `ConnectionString` row encrypted under the OLD key therefore survives both starts unchanged; the gate never looks at it; `shred -u "${CRED}.old"` (`:218`) then makes it permanently unreadable (`Decrypt` throws on a key-hash mismatch, `EncryptedFieldHelper.cs:138-139`). Whether the Yamaguchi database has such rows is not established anywhere in the set — `yamaguchi_server_db_snapshot.py:139` prints only a table count — so I cannot call it moot.

**Correction.** Add `SELECT "BaseUrl" FROM "ConnectionString"` and `SELECT "TargetURL" FROM "BackupTargetUrl"` to the gate's scan (keep the `OperationalError` guard); treat any `under-another-key` blob as GATE FAILED (the script already does), and in the pre-flight print the `ConnectionString` row count so the operator knows whether the product gap can bite.

### DEFECT-5 — D's STOP-clearing item 3 states a fix (B2: `serverstate`/`pause`/`resume`, `--backup-id`) that is not in this tree or on `origin/main`

**Claim.** D § STOP clearing, item 3 (`D.plus:232-234`): "The API clients … carry `serverstate`/`pause`/`resume`, and require `--backup-id` (the assessment's B2)", under a preamble that says "Each is fixed in the artifact that would have executed it… and the artifacts are what §8 installs".

**Evidence.** `util/ad-hoc/yamaguchi_server_api.py:80` in this tree: `choices=["status", "export", "abort", "delete", "import", "run", "progress", "log", "task"]`; `git diff origin/main --stat -- util/ad-hoc/yamaguchi_server_api.py` is empty; the verbs exist only on `origin/fix/backup-b2-web-credential-serverstate-backup-id` (`d941f186`, `34b0ae6c`), not merged. The re-key script fails closed on this (`:110`, `--help | grep -q serverstate` → `die "… B2 must land first"`), and the dry-run test passes only because the API check is skipped under `--dry-run` (`:106`).

**Correction.** Item 3 should say B2 is a separate PR that must merge before P0 step 10/12, and name it.

### DEFECT-6 (pre-existing on `main`, carried verbatim into D:862) — "the only non-zero exits in Server/Program.cs are 100 … and 102/103"

**Claim.** `scripts/duplicati-wrapper.bash:25-26`; D:861-863 (tagged block).

**Evidence.** `Server/Program.cs:949` and `:960`: `Environment.Exit(200)` in `CreateApplicationInstance` — single-instance lock failure or "another instance detected" — on the console path (`writeToConsoleOnException`, i.e. `duplicati-server` invoked directly, which is how the hand-start runs it). The hand-start script's `case` catches it as "unexpected exit" (`:139`), but nothing in the set names 200, and running the hand start while the unit holds the data folder is exactly how it would surface.

**Correction.** "…100 (unhandled exception), 200 (single-instance lock / another instance, console mode) and 102/103."

### NIT-1 — hand-start: `--webservice-interface`, `--webservice-port`, `--webservice-allowed-hostnames` and the port-in-use gate are inert on the 102 path

`Program.cs:288` returns before `StartWebServerAsync` (`:295`), and inside `AdjustApplicationSettings` the 102 return (`:682`) precedes `SetAllowedHostnames` (`:690-693`). No socket is ever bound, so `:81-83` (`ss -ltn`) guards nothing, and the assessment's "on an unused loopback port" (`:228`, `:264`) describes a bind that does not happen. Harmless; say so, or drop the three options and the gate.

### NIT-2 — hand-start: the server `.Trim()`s every parameters-file line

`Program.cs:1620` (`.Select(x => x.Trim())`). The script's "survives verbatim" (`:90-93`) holds for `$ & # @` and quotes, not for leading/trailing whitespace in a secret; the embedded python (`:118`) rejects only embedded newlines. Add `key != key.strip()` to its check.

### NIT-3 — wrapper: option names are deduplicated case-sensitively; Duplicati option names are case-insensitive

`m4h` (`wrap/run_m4.bash`): `--Webservice-Port=8300` in the env file passes as a **second** option beside `--webservice-port` (stub argv shows both). The server's own slim parser is `OrdinalIgnoreCase` (`DataFolderManager.cs:316-318`). Lower-case the map key in `add_opt` (`:69`).

### NIT-4 — contract wording: the comment-assignment rule is not the wrapper's

`util/systemd/duplicati-env.contract:23-26` opens "Grammar (enforced by the wrapper, which refuses anything else)" and continues "A comment must never START with an assignment". M2: `# TZ=UTC` and `#SETTINGS_ENCRYPTION_KEY=notasecret` lines → wrapper exit 0 (`wrapper:98-99` skips any `#` line). The rule is enforced by `tests/test_duplicati_wrapper_contract.py:85` (regex `^\s*#\s*(export\s+)?[A-Za-z_][A-Za-z0-9_]*=\S`, repository copy only) and by AC-8's `2026-09-21_env_file_shape.py` on the installed copy (D:2429) — not by the wrapper, and nothing checks an operator's later edit of `/etc/duplicati/env` at start time. Say "counted by AC-8 and the contract test, not refused by the wrapper".

### NIT-5 (pre-existing) — D:2293 cites `RestConnection.cs`

No such file in the snapshot or the DLLs (`literal_scan`: NOT FOUND); `ResolveDbPath`/`GetRelativeDbPath` are in `Library/RestAPI/Database/Connection.cs:766-790` (`Duplicati.Library.RestAPI.dll`). Behaviour as described: rooted paths returned unchanged (`:768-769`), stored relative when under the data folder (`:779-790`, used at `:801` and `:868`).

### NIT-6 — snapshot unit: a `mode=ro` open of a WAL-mode source needs `-shm` to exist

`util/ad-hoc/yamaguchi_server_db_snapshot.py:123` opens the source `file:…?mode=ro`; under `ProtectHome=read-only` the data folder is read-only to the unit, so SQLite can read a WAL-mode database only while `-wal`/`-shm` already exist (the ≥3.22 read-only-WAL rule); it cannot create them. Today they exist (`ls -la /home/duplicati/.config/Duplicati/`: `Duplicati-server.sqlite` 4096 B, `-wal` 383,192 B, `-shm` 32,768 B, all Sep 27 18:20), so the design's "strict + ReadWritePaths works" measurement holds while the server runs; a run after a clean close that removed the sidecars would fail (fail-closed, with an SQLite error). Not refuted; worth one sentence in § 7.7 and a `?immutable=1` fallback **only** when the server is stopped.

### NIT-7 (pre-existing) — D:2273 "refuses a non-server database"

`WipeEncryption.cs:62-66` prints "Skipping … wipe-encryption only applies to server databases" and `continue`s; exit status 0. "Skips" is the word.

## Option names (part 1)

Every `--option` used or asserted (the installer's `--dry-run`/`--update-backup-behavior`, the API client's `--backup-id`, journalctl's `--vacuum-time`, the wrapper's `--print-command` and the hand scripts' own flags excluded):

| name | scanner (`literal_scan_options.txt`) | definition |
|---|---|---|
| `webservice-port` | FOUND utf-16le `Duplicati.Server.Implementation.dll` | `Server/WebServerLoader.cs:53` (default 8200, `:137`) |
| `webservice-interface` | FOUND | `WebServerLoader.cs:58` (default `loopback`, `:187`) |
| `server-datafolder` | FOUND (7 DLLs) | `Library/AutoUpdater/DataFolderManager.cs:65`; subcommand option `WipeEncryption.cs:24` |
| `disable-update-check` | FOUND | `Server/Program.cs:67`, registered `:1588`, read `:303` |
| `require-db-encryption-key` | FOUND | `Program.cs:63`, `:1594`, enforced `:1249` |
| `webservice-disable-signin-tokens` | FOUND | `WebServerLoader.cs:96`, applied `Program.cs:661-662` |
| `webservice-allowed-hostnames` | FOUND | `WebServerLoader.cs:83` (alias `webservice-allowedhostnames` `:87`) |
| `disable-db-encryption` | FOUND | `Program.cs:59`, `:1592`, read `:1159` |
| `webservice-token-duration` | FOUND | `WebServerLoader.cs:117` (hyphenated, as the wrapper comment says) |
| `webservice-password-init` | FOUND | `WebServerLoader.cs:68`, `Program.cs:675-687` |
| `webservice-password` | FOUND | `WebServerLoader.cs:63` |
| `settings-encryption-key` | FOUND (4 DLLs) | `Program.cs:65`, `:1595`; env name `SETTINGS_ENCRYPTION_KEY` `EncryptedFieldHelper.cs:87` |
| `parameters-file` | FOUND (`Server.Implementation.dll` utf-16le) | `Program.cs:49` (alias `parameterfile` `:51`), reader `:1617-1700` |
| `allow-insecure-datafolder` | FOUND (6 DLLs) | `DataFolderManager.cs:74` |
| `daemon-opts` | NOT FOUND (both encodings) | not an option anywhere — consistent with D's account of the glued word being an *unknown* option |

`webservice-allowed-hostnames-alt` was my own probe (not a name in the set) and is correctly absent.

## Not refuted (with the test that failed to refute each)

- **`--disable-db-encryption` satisfies `--require-db-encryption-key`.** `Program.cs:1249`: `if (requireDbEncryptionKey && !(hasValidEncryptionKey || disableDbEncryption)) throw …` — the comment in `duplicati.default:6` quotes it correctly.
- **`--webservice-disable-signin-tokens` is applied unconditionally at every start.** `Program.cs:661-662` inside `AdjustApplicationSettings`, called on every start at `:286` (before the webserver); `:1577` registers it. Enforcement: `WebserverCore/Endpoints/V1/Auth.cs:67-68` (`auth/signin`) and `:110-111` (`auth/issuesignintoken`) throw `Unauthorized`; password login (`:90`) stays open. The hand-start's "line 662" citation is exact. (Side note: with an autogenerated password the server still logs a signin URL with a token at `:337-346` — unusable, but a token in the journal.)
- **IP-literal Host is always allowed.** `WebserverCore/Services/HostnameValidator.cs:66-67` (`IPAddress.TryParse → true`); `:34` also always allows `localhost`, `127.0.0.1`, `[::1]`, `localhost.localdomain`; `Middlewares/HostnameFilter.cs:30` uses `Request.Host.Host` (port stripped). `--webservice-allowed-hostnames=localhost` is therefore redundant but harmless.
- **`--webservice-password-init`: 102 iff autogenerated, 103 otherwise; file read in-process.** `Program.cs:675-687`; `ReadOptionsFromFile` reads the file in-process (`:1620`, `ReadFileWithDefaultEncoding`) after `ApplyEnvironmentVariables` (`:226` vs `:237`) and its options override argv (`:1676`). `SetWebserverPassword` writes `pbkdf-config`, clears `server-passphrase` and `server-passphrase-salt`, sets `autogenerated-passphrase=False` (`ServerSettings.cs:398-411`). 103 writes nothing (`:684-686`).
- **`wipe-encryption` clears `pbkdf-config` and `remote-control-config`; `--server-datafolder` is a subcommand option; default folder is `~/.config/Duplicati`.** `WipeEncryption.cs:116` with `Connection.PasswordFieldNames` (`Connection.cs:66-91`, includes both at `:80-82`); values set to `''` only when `enc-v1:`-prefixed (`:190-`), which an encrypted database's are; `VerifyWebserverPassword` returns false on an empty config (`ServerSettings.cs:328-332`); the next `UpgradePasswordToKBDF` mints a random password with `autogenerated=True` (`:363-392`). `--server-datafolder` at `WipeEncryption.cs:24`; default via `DataFolderLocator.cs:82-86` → `SpecialFolder.ApplicationData` → `~/.config/Duplicati` on Linux. The `-<ts>.bak` is `Helper.cs:24-39`.
- **`UpgradePasswordToKBDF` nulls `server-passphrase`; since 2.1.** `ServerSettings.cs:385`; `attag/ServerSettings_2.0.8.1.cs` has no `UpgradePasswordToKBDF`/`PBKDF_CONFIG`, `2.1.0.5` and `2.3.0.4` do (grep counts 0/1, 0/5).
- **`enc-v1:` layout and the gate's offsets.** Writer `EncryptedFieldHelper.cs:157-175`: `"enc-v1:" + sha256hex(ciphertext-hex) + key.Hash + ciphertext-hex`; reader `:118-131`: 64-char content hash, then 64-char key hash. The script's slice `[7+64 : 7+128]` (`rekey:186`) is the key-hash field. Trailing-newline handling agrees between the wrapper's `$(<file)` and the gate's `rstrip("\n")` (M5c: both see 24 chars). What I could not confirm: `key.ComputeHashToHex(hasher)` (`:59`) lives in `Duplicati.Library.Utility` (absent from the snapshot) — see Unverifiable.
- **`encrypted-fields` is `Option` row `BackupID=-2`, `Value='True'`.** `Connection.cs:57` (`SERVER_SETTINGS_ID = -2`), `ServerSettings.cs:109`, setter `:854` (`bool.ToString()` → `True`/`False`), read by the server at `Program.cs:1174-1179` exactly as the gate reads it.
- **Indefinite pause persists across restarts; `resume` fires the overdue job.** Persist: `Program.cs:1308` (`PausedUntil = e.WaitTimeExpiration`, which `LiveControls.Pause()` sets to `DateTime(0)`, `LiveControls.cs:312-331`, event at `:258-266`); restore: `LiveControls.cs:192-200` (`Ticks == 0` → paused, timer off); re-applied at start `Program.cs:311-316`; cleared on Running `:1316`. Scheduler: overdue schedules are added with `AddTask` regardless of pause (`Scheduler.cs:307-396`); within the snapshot the scheduler thread starts only via `Reschedule()` (`:121-126`), called from the Running branch (`Program.cs:1315`) — so under a restored pause nothing is queued **until** `resume`, which then queues and runs it. Same safety outcome as claimed; "queued at every start" is the imprecise half.
- **`GetRelativeDbPath`/`ResolveDbPath`.** `Connection.cs:766-790` as above (NIT-5 for the filename).
- **0700 gate before argv parse; refuses 0777.** `Program.cs:198` `new ApplicationSettings()` → `ApplicationSettings.cs:26` `GetDataFolder(ReadWritePermissionSet)` → `DataFolderManager.cs:144-145` `PrepareSecureDataFolder` → `:280-302` throws `InsecureDataFolderPermissions` for a pre-existing non-canonical folder; this precedes the full parse at `Program.cs:211` and reads raw argv through `ExtractOptionSlim` (`:311-340`) — so `--server-datafolder` must be on argv, not in the parameters file (the hand-start does put it on argv). The predicate itself (`SystemIO.IO_OS.DirectoryHasPermissionUserRWOnly`) is outside the snapshot; its message literals in `/usr/lib/duplicati/Duplicati.Library.Common.dll` (UTF-16LE dump) are `'permissions allow group or other access ('` and `'owner is uid ' … ' but expected the current user (uid '` — a 0777 folder fails the first, a 0700 folder of another uid the second. Consistent with the hand-start's `${RUN_AS}:700` gate (`:76`) and with D:2267 ("2.4.0.0 refuses it"). The gate is repeated at `Program.cs:1143`. `--allow-insecure-datafolder` / `DUPLICATI__ALLOW_INSECURE_DATAFOLDER` bypass it (`:214`, DEFECT-2).
- **Unknown options are a warning, not a refusal.** `Library/Utility/CommandLineArgumentValidator.cs:64` (`WriteWarningMessage "Unknown option supplied: {key}"`), called at `Program.cs:240`.
- **systemd directives.** `systemd-analyze verify --man=no` on the three copies in `units/`: snapshot `.service` and `.timer` exit 0 with no output; `duplicati.service` prints only `Command /usr/local/lib/duplicati/duplicati-wrapper.bash is not executable: No such file or directory` — the installed wrapper path is absent on this box (`ls /usr/local/lib/duplicati/` → no such directory; the installer has not run), expected; a probe copy with `ExecStart=/bin/true $DAEMON_OPTS` (`units/probe/`) verifies clean, exit 0. All 50 directives used appear in this host's `systemd.exec(5)`/`systemd.service(5)`/`systemd.unit(5)`/`systemd.timer(5)`/`systemd.resource-control(5)` (`units/check_directives.py`; `Group=` and `StartLimitBurst=` are documented on shared lines `systemd.exec:622`, `systemd.unit:983`).
- **`ProtectSystem=strict` leaves `/home/duplicati/.config/Duplicati/Duplicati-server.sqlite` readable and `ReadWritePaths=` punches the write path; `ReadWritePaths=` nests inside `ProtectHome=read-only`.** `systemd.exec(5)` `:1337-1352` ("entire file system hierarchy is mounted read-only… ReadWritePaths= may be used to exclude specific directories"), `:1364-1377` (`read-only` "is mostly equivalent to ReadOnlyPaths="), `:1619-1626` ("Nest ReadWritePaths= inside of ReadOnlyPaths= in order to provide writable subdirectories within read-only directories") — the sentence `duplicati.service:37-39` quotes. The snapshot unit runs as root, so DAC on the 0700 folder is not in play. See NIT-6 for the WAL caveat.
- **`InaccessiblePaths=-/path` tolerates a missing path.** `systemd.exec(5):1650-1652` ("may be prefixed with "-", in which case they will be ignored when they do not exist"); verify confirms the 15-entry line parses.
- **`Persistent=true` re-fires after a reboot; `disable --now` is the right verb.** `systemd.timer(5):334-345`: "When the timer is activated, the service unit is triggered immediately if it would have been triggered at least once during the time when the timer was inactive." A stopped-but-enabled timer is re-activated by `timers.target` at boot and catches up; `disable --now` prevents the activation. Corollary the set already honours: `enable --now` at step 13 fires the snapshot immediately.
- **Vendor unit `Restart=always`.** `/usr/lib/systemd/system/duplicati.service:17` (dpkg-owned; the file was hand-edited on Sep 21 for its ExecStart, lines 13-15, but `Restart=always` is the vendor line).
- **`LoadCredential=` places the file at `$CREDENTIALS_DIRECTORY/<ID>`; the wrapper reads that id.** `systemd.exec(5):3665-3690`; unit `:26` id `settings-key`; wrapper `:43` `CRED_NAME="settings-key"`, `:122-127`. M5a: a dummy credential overrides the env-file value and is logged as a char count only; M5b: an empty credential → exit 78.
- **Unbraced `$DAEMON_OPTS` splits at whitespace.** `systemd.service(5):1291-1299` ("$FOO as a separate word … split at whitespace … quotes are respected when splitting into words, and afterwards removed"), as `duplicati.default:2-3` says.
- **`@system-service` admits `name_to_handle_at` and not `open_by_handle_at`; 18 of `@privileged`'s 53 calls are in its closure.** `units/syscall_sets.py` (transitive expansion via `systemd-analyze syscall-filter`): `@privileged` 53, `@system-service` 395, intersection 18 = `capset chown chown32 fchown fchown32 fchownat lchown lchown32 setfsuid setfsuid32 setgroups setgroups32 setresuid setresuid32 setreuid setreuid32 setuid setuid32`; `open_by_handle_at` in `@privileged` only. The unit's numbers (`:72-82`) are exact. `ProtectProc=invisible` hides other users' processes (`systemd.exec(5):352-353`), as `:94-96` says.
- **Wrapper grammar vs the contract** (`wrap/run_m4.bash`, `run_m5.bash`, stub server):
  - precedence `DEFAULT_OPTS < env file < argv < later argv`: env `--webservice-port=8301` < argv `8302` < argv `8303` → `8303` (M3); distinct options accumulate (`--log-level`, `--disable-update-check` both present); first-seen order is stable;
  - leading whitespace on an `--option` line ignored (M3 line 1); `--option` lines passed verbatim, quotes included, as one argv word (`--webservice-allowed-hostnames="a b"`); CRLF tolerated (m4d);
  - assignment values literal, matching quotes stripped (`TZ="UTC"` → `UTC`, `export LANG='C.UTF-8'` → `C.UTF-8`, M3b); no inline comments (`LC_ALL=en_US.UTF-8 # trailing` exports the whole literal — correct per "literal", worth one line in the contract); empty value allowed (m4g);
  - environment wins over the file for the same name (M3 `TZ`, m4k `SETTINGS_ENCRYPTION_KEY` → "already set in the environment; file value ignored");
  - refused with exit 78 and no value printed: `export SETTINGS_ENCRYPTION_KEY_OLD=x` (M1: names the key, value absent), `PATH=`, `LD_PRELOAD=` (m4a, m4c), an unparseable line, a bare `-x`, and `webservice-port=8300` without dashes (m4b, m4i, m4e);
  - `# NAME=value` comments are accepted (M2 — NIT-4);
  - the shipped contract prints `would exec: /bin/true --webservice-interface=loopback --webservice-port=8300 --server-datafolder=<scratch>` (the contract's `--webservice-port` line is inert by dedup, as it says);
  - `tests/test_duplicati_wrapper_contract.py`: 13 tests, OK (0.7 s), run with `PYTHONDONTWRITEBYTECODE=1`.

## Unverifiable

- **`--dry-run` of `wipe-encryption` flips the copy to WAL.** `SQLiteLoader.LoadConnectionAsync` (`WipeEncryption.cs:106`, `Helper.cs:71,111`) is not in the snapshot. Corroboration only: `journal_mode` is a UTF-16LE literal in `/usr/lib/duplicati/SQLiteHelper.dll` (not the `=WAL` spelling, which is only in `SQLite-net.dll`). Test: `PRAGMA journal_mode` on a scratch copy before/after one `--dry-run` — requires running `duplicati-database-tool`, which this round forbids.
- **`ComputeHashToHex` hashes the UTF-8 bytes of the key** (what `rekey:176` assumes). The extension lives in `Duplicati.Library.Utility.dll` (not in the snapshot; no IL tools on the box). If wrong, the gate reports every blob `under-another-key` and refuses to shred — fail-closed. Test: on a root-made copy of a database known to be encrypted under a known key, compare the 64-char slice with `sha256(key.encode())`.
- **`DirectoryHasPermissionUserRWOnly`'s exact predicate** (e.g. whether 0600 or 0500 passes): outside the snapshot; only its message literals were read (above). Test: the owner's rehearsal in step 0.
- **Whether `ConnectionString` has rows in the Yamaguchi database** (DEFECT-4's reach): no document in the set states it, and reading the live database is outside this lane.

## Host-state observations (stat / read-only queries only; no action taken)

- `duplicati.service` reads `active` and `enabled`, fragment `/usr/lib/systemd/system/duplicati.service` (vendor), `ProtectSystem=no`, `Restart=always`; `yamaguchi-server-db-snapshot.timer` reads `active` and `enabled`. `/etc/systemd/system/duplicati.service`, `/etc/duplicati/`, `/usr/local/lib/duplicati/` do not exist (installer not run). `/etc/default/duplicati` is `-rw-r--r-- duplicati duplicati` (Sep 20), not the `root:root` `duplicati.default:3` describes — the installer would correct it; until then the service user can rewrite its own `DAEMON_OPTS`. Data folder `drwxrwxrwx duplicati` with the 4 KB main file and Sep 27 WAL/SHM sidecars; `/home/duplicati/bin/` is 0777 and symlinks the wrapper into the primary checkout. `origin/main` (`c01c837e`, a docs commit on D) is not an ancestor of this tree (`b7840a14`), so D will need a rebase before merge (Lane C's concern).

## Slips

None. No unit was started, stopped, reloaded or reverted (`systemctl is-active`/`is-enabled`/`show` and `systemd-analyze verify`/`syscall-filter` only); no Duplicati binary was run (`DUPLICATI_SERVER=/bin/true` or the lane's `stub.sh`); no `sudo`; no secret file opened (the data folder, `/etc/credstore*` and `/home/duplicati/bin` were listed with `ls -la` only; `/usr/lib/duplicati/run-script-example.sh` and the DLLs are public product files); no journal or `/var/log` read; nothing under `/mnt/Backups/` touched; no tracked file modified; git used read-only (`diff`, `log`, `status`, `merge-base`, `check-ignore`); writes confined to `<scratch>/val/PB/A/`. Dummy credential values only were used in the mutation files.

## Manifest (re-check after the lane)

```
$ sha256sum -c <scratch>/val/PB/MANIFEST.sha256 | grep -c ': OK'
18
```

<!-- markdownlint-enable -->

---

## Round 2, lane B — consequence

Archived verbatim (29,586 characters, sha256 `df41257970d1b9b0`), lifted from the report file the lane wrote itself, in session 652c1204's scratch directory, on 2026-10-03.

<!-- markdownlint-disable -->

# Phase B validation — Lane B (consequence lens)

Tree: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/cached-swinging-summit` (HEAD `6a1514e4`, merge-base with `origin/main` = `b7840a14`; `origin/main` is at `c01c837e`, #2113).
"D" = `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`; "A" = `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`; "R4" = `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md`. Line numbers are this tree's. Product source = the 2.4.0.0 copy at `<scratch>/val/B/src`; installed assemblies scanned with `util/ad-hoc/2026-09-22_duplicati_literal_scan.py`.

## Manifest

`sha256sum -c val/PB/MANIFEST.sha256` from the tree: **18/18 OK** (exit 0). `git check-ignore -v util/systemd/duplicati-env.contract` printed nothing (exit 1): the contract is not ignored.

## Findings

### BLOCKER-1 — `systemctl revert duplicati.service` deletes the installed D-6 unit on this host; the encrypt start then runs the vendor unit

- **Where**: `util/ad-hoc/2026-10-03_rekey_settings_key.bash:156` (`run systemctl revert "${UNIT}"`), `:109` (pre-flight tells the owner to run `systemctl revert` by hand), `:38-41` (header: "the drop-in is removed; the unit is back to the installed text"); D §8 clearing block L1875-1878 ("removes with `systemctl revert`"), D P1 step 1 L2374, A note 6a L233; pinned by `tests/test_duplicati_wrapper_contract.py:198` (`order` requires the string `systemctl revert duplicati.service`).
- **Claim**: the revert removes only the runtime drop-in and leaves the unit "back to the installed text".
- **Evidence**: `man systemctl` (systemd 259.5 on this host): *"if the unit file has a vendor-supplied version (i.e. a unit file located below /usr/) any matching persistent or runtime unit file that overrides it is removed, too."* A vendor unit exists and will still exist on the recovery day: `dpkg -L duplicati` lists `/lib/systemd/system/duplicati.service` (= `/usr/lib/systemd/system/duplicati.service`, 461 B, edited in place 09-21, flagged by `dpkg -V duplicati`); nothing in Phase C or P0 removes it (A I-25 L169 relies on it being *shadowed* by `/etc/systemd/system/duplicati.service`, D §4.3 item 10 L267 records it). The installer installs to `UNIT_DST=/etc/systemd/system/duplicati.service` (`util/install_duplicati_service.bash:44`). So line 156 removes the D-6 copy; line 158 reloads; line 160 starts the **vendor** unit (`User=duplicati`, `Restart=always`, no `LoadCredential=`, `ExecStart=/home/duplicati/bin/duplicati-wrapper.bash '--daemon-opts="${DAEMON_OPTS}"'`). The enablement symlink `/etc/systemd/system/multi-user.target.wants/duplicati.service -> /usr/lib/systemd/system/duplicati.service` survives, so a reboot also runs the vendor unit.
- **Consequence, walked** (Procedure A, P0.5b, after the decrypt start — every field cleartext on disk, keys already swapped at `:153-154`):
  - Phase C step 1 done (`rm -r /home/duplicati/bin`, A L247): `ExecStart` target missing → exit 203 → `Restart=always` loops to the start limit → `wait_started` dies at `:94` after 120 s. State: `/etc/systemd/system/duplicati.service` **gone** (`.blessed.sha256` still lists it), drop-in gone, new key at `…-key`, old at `…-key.old`, **server database cleartext**, unit failed, scheduler paused (persisted). Server unreachable; the die message says only "no 'Server has started' within 120 s".
  - Phase C step 1 not done: the symlink resolves to the primary checkout's wrapper **2.0.0** (`git diff origin/main -- scripts/duplicati-wrapper.bash`: `main` still defaults `ENV_FILE` to `/home/duplicati/.config/Duplicati/.env`), which passes the glued `--daemon-opts=` word through as an unknown option; the server starts **unconfined, without any key and without `--require-db-encryption-key`** (the real options are inside the glued word), finds `encrypted-fields=False`, prints `Server has started` (Program.cs L1255-1257, L328); the gate at `:172-190` fails (`encrypted-fields=False`) and the script exits with the unit stopped at `:164`. Same end state plus one unconfined run.
  - Either way the pre-flight's own recovery instruction (`:109`, "run 'systemctl revert …' and inspect before retrying") performs the same deletion. Recovery exists but is nowhere in the script or the documents: re-run the installer (it passes: absent destination is not DRIFT), `systemctl start`, re-run the gate by hand.
- **Correction**: replace both `systemctl revert` uses with `rm -f "${DROPIN}"; rmdir "${DROPIN_DIR}" 2>/dev/null || true` (+ `daemon-reload`), run the same from an `EXIT` trap (see DEFECT-3), fix the three prose sites and A note 6a, and change the test's `order` list. Alternatively have the installer mask the vendor copy — but a mask symlink would collide with `UNIT_DST`, so `rm` of the drop-in is the only shape that fits the installed layout.

### BLOCKER-2 — the clearing block's item 3 claims an artifact this tree (and `main`) does not carry; the re-key and P0 steps 9–11 cannot run without it

- **Where**: D L1882-1884 ("The API clients read one 0600 credential (`~/.config/duplicati-backup/web-credential`), carry `serverstate`/`pause`/`resume`, and require `--backup-id` (the assessment's B2)"); D L12 ("everything it held is now runnable"); D L6 status "EXECUTABLE".
- **Evidence**: `python3 util/ad-hoc/yamaguchi_server_api.py --help` in this tree lists `{status,export,abort,delete,import,run,progress,log,task}` — no `serverstate`, `pause`, `resume`; `CRED_FILE = "/home/pcalnon/Development/python/Juniper/juniper-ml/.env"` (`:41`). `git show origin/main:util/ad-hoc/yamaguchi_server_api.py` is the same. B2 exists only as commit `34b0ae6c` on `origin/fix/backup-b2-web-credential-serverstate-backup-id`, which is an ancestor of neither HEAD nor `origin/main` (`git merge-base --is-ancestor`). A §9 L384 itself says "B2 and B6 in their own [PR]".
- **Consequence**: `2026-10-03_rekey_settings_key.bash:110` dies in pre-flight ("has no serverstate/pause/resume verbs yet") — correct behaviour, but it means P0.5b cannot be executed as written; D step 9/10 (`pause`/`resume` "through `util/ad-hoc/yamaguchi_server_api.py` (extended with `pause`/`resume`)", L2303-2305) and A §6.4 step 11 ("`python3 util/ad-hoc/yamaguchi_server_api.py serverstate` works", L279) cannot be followed. The STOP's item 3 is reported fixed in prose while the file that fixes it is unmerged — exactly the "claims fixed, not in the file" class.
- **Correction**: merge B2 first (or into this PR) and make item 3 and the status line say the dependency explicitly; keep the pre-flight.

### DEFECT-1 — the password-init hand start does **not** encrypt the database; the verification the operator is told to run (`encrypted-fields=True`) will read False

- **Where**: `util/ad-hoc/2026-10-03_password_init_hand_start.bash:22-24` ("the same start encrypts the database under the new settings key (the first start with a key re-encrypts every field)") and `:137` ("exit 102: UI password set and the database encrypted … Verify on a COPY: autogenerated-passphrase=False, encrypted-fields=True"); A §6.2 B10 L228 ("verifies autogenerated-passphrase=False and encrypted-fields=True on a copy"); A §6.4 step 10 L277 ("exit **102**, `autogenerated-passphrase=False` and `encrypted-fields=True` verified on a copy").
- **Evidence** (Server `Program.cs`, 2.4.0.0): `GetDatabaseConnection` L260 → `UpgradePasswordToKBDF` L265 → `AdjustApplicationSettings` L286-288 returns **102 at L682** inside that call → `return adjustres.Value` — **before** `StartWebServerAsync` (L295) and before `connection.ReWriteAllFieldsIfEncryptionChanged()` (L324), which is the only place `encrypted-fields` is set (`Connection.cs` L131-152, `this.ApplicationSettings.EncryptedFields = m_encryptSensitiveFields` at L146). What the 102 run does write is `SaveSettings()` (`ServerSettings.cs` L209-220 → `SetSettings(…, -2)`, which encrypts the password-named fields when a key is present, `Connection.cs` L394-400): `pbkdf-config` becomes an `enc-v1:` blob under the new key while the flag stays `False` and every other field stays as placed.
- **Consequence**: on A2/B the operator is told to expect a value the product cannot produce; a careful operator stops or re-runs the hand start (now 103). Not damaging — the unit's first start (same key) decrypts `pbkdf-config` and rewrites everything (flag `False ≠ true`), so the state is consistent — but the step's gate is wrong, and A §6.4 step 13's verification is where `encrypted-fields=True` first becomes true on these paths.
- **Correction**: after 102 expect `autogenerated-passphrase=False`, `encrypted-fields=False`, `pbkdf-config` an `enc-v1:` blob carrying sha256(new key); say the full re-encryption happens at the unit's first start. Also (NIT-level, same site) the server exits without disposing the connection (`Program.cs` L405-444), so `-wal`/`-shm` are likely left beside the file: the "verify on a COPY" instruction must copy the siblings or the copy will show the pre-password state (D's own probe script, L2074-2077, states this trap).

### DEFECT-2 — the re-key's "no backup running" pre-flight is claimed but not implemented, and every placement the documents give for P0.5b runs it after the `resume` that fires the first backup

- **Where**: rekey `:23` ("pre-flight: … no backup running"); A §6.2 B4 L222 ("refuses to run with the server active or a backup in progress" — also contradicts `:107`, which *requires* the unit active); placements: D L13 (front matter: "P0 steps 1–8, then P0.5b, then P0 steps 9–11"), D L2361 + L2366 + note 8a L1909 ("after P0 step 11"), rekey `:18` ("after P0 steps 10-11 (the unit's first start, the UI password, the pause/edits/resume)" — A's numbering), A §6.4 step 12 L281 (after step 11, whose last action is `resume`), note 12b L2832 (ml#2113 put it "between steps 8 and 9, not after step 11").
- **Evidence**: the pre-flight (`:98-112`) checks root, credentials, unit active, timer not enabled, no drop-in, API verbs, DB present — nothing about a task; `:116` `api serverstate || true` is informational. `resume` fires the overdue job at once (Program.cs L1311-1316 `schedulerService?.Reschedule()`; Scheduler.cs L307 queues `start <= UtcNow`; D L2302 "resume is what fires the overdue backup"). `api pause` (`:117`) then pauses the running task (L1307) and `systemctl stop` (`:121`) terminates it mid-run.
- **Consequence per placement**: front-matter order (after D step 8, before D step 9) — `api pause` runs before the web-credential exists (created at D step 9) → non-zero → `set -e` exit before anything is touched: harmless, cannot execute. D-heading order ("after step 11" in D's numbering = after AC-2, AC-3's backup and AC-4's drills): the first backup and both drills are written while the server database is under the burned 09-18 key — contradicts P0.5b's own "closes S-1 and S-2, not deferrable" (L2369) — and a running backup is stopped. A's order (step 12 after step 11's `resume`): the first backup since 09-18 (a full home-directory scan) is almost certainly in progress; it is paused then killed. Duplicati recovers an interrupted backup on the next run, but the per-job index `BMXWPAOGLP.sqlite` is the sole local copy and this is avoidable.
- **Correction**: implement the check (B2's `serverstate` prints `ActiveTask`/`SchedulerQueueIds`; refuse while `ActiveTask` is non-null), and place P0.5b in all four sites at one point: after D step 9's credential and inside D step 10 **before** the operator's `resume` (the script's own `resume` then fires the backup, after the tempdir/guard edits).

### DEFECT-3 — the re-key has no cleanup trap: most exits between the first `stop` and the final `resume` leave the drop-in, a half-swapped key, a persisted pause, or an un-shredded database copy, and the die messages do not say so

- **Where**: rekey `:50-220` (no `trap`); header `:3-4` ("without ever leaving `--disable-db-encryption` behind"); A I-28 L172 ("exit gate = `encrypted-fields` True **and** no drop-in"); D L1881.
- **Walk of each exit** (state afterwards):
  - `:121` stop fails → paused (persisted `paused-until`=0, `ServerSettings.cs` L240 / `LiveControls.cs` Init), keys intact, no drop-in.
  - `:132` no `ExecStart=` → stopped, paused, nothing else; recoverable (installer, start, resume by hand — not said).
  - `:144` start fails / `:88` / `:94` (wait) → **drop-in present in `/run/systemd/system/duplicati.service.d/`**, old key in place; the unit may be retrying under `Restart=on-failure` (RestartSec 30 s, burst 5/10 min) and a later success runs **decrypted** with the drop-in; or the server is up, cleartext, paused. The only instruction naming the drop-in is `:109` — `systemctl revert` (BLOCKER-1).
  - `:153-154` the swap is two `mv`s (D L1877 "one `mv`"); a failure between them leaves `…-key` absent → `LoadCredential=` fails every start until the owner moves `.old` back.
  - `:156-158` → keys swapped, drop-in present or (on this host) the installed unit deleted; DB cleartext.
  - `:160-161` → vendor unit (BLOCKER-1); DB cleartext; keys swapped.
  - `:172-190` gate fails → `sys.exit` under `set -e` skips `:191`: the **copy of the server database stays in `/root/.cache/duplicati-rekey/gate-<ts>.sqlite`** (+ `-wal`/`-shm`). If the encrypt start did not run, that copy is **cleartext and holds the job passphrase** — a new §6-class sink the design's own step 4 (L2259-2262) says must be shredded. Root-only 0700, but new.
  - `:199-206` VACUUM fails → stopped, encrypted under the new key, old key kept; no instruction.
  - `:213` `api resume` fails or `:217` not Running → **server up, scheduler paused indefinitely and persisted across restarts** (the 42.6 h class, I-39); the message does not say "resume by hand / in the UI".
- **Correction**: `trap` on EXIT that (a) removes the drop-in dir and reloads, (b) if `…-key.old` exists and the gate has not passed, restores it (or at least prints the exact `mv`), (c) shreds the gate copy, (d) prints the on-disk state of the database (cleartext / old key / new key) and whether the scheduler is paused. Keep the old key until the gate passes (already so).

### DEFECT-4 — cross-document numbers, names and orders that disagree

1. **Step numbering**: every artifact calls A §6.4's checklist numbers "P0 step N" while D's P0 uses different numbers for the same actions — installer `:216` ("this is P0 step 10"; D: step 8) and `:220` ("P0 step 13"; no such D step); hand start `:2` ("P0 step 10"; D: step 8); rekey `:15-18`, `:49`, `:108` ("P0 step 1" for the timer; D: P0.5a item 2), `:132` ("P0 step 9" installer; D: step 8); and inside D itself P0.5a item 2 L2349 ("`enable --now` only at P0 step 13") and P0.5b L2361 ("after P0 step 11") use A's numbering while the P0 preamble L1954-1956 ("item 7 before step 8's first start, item 5 before step 10's `resume`") uses D's. An operator holding only D reads "P0 step 10" as the pause/resume step and "step 13" as nothing. Say "assessment §6.4 step N" everywhere, or renumber.
2. **Blessed-file count**: A §6.4 step 9 L275 "blesses six paths" vs A step 4 L269 "seven", D L1966 "seven", installer `PAIRS` = 7, test `"7 installed files"`, dry run "7 installed files".
3. **Files named that do not exist**: A §6.2 B4/B10/B11 (L222, L228, L229) name `util/ad-hoc/2026-10-0X_rekey_settings_key.bash`, `…0X_password_init_hand_start.bash`, `…0X_history_key_candidates.py`; the first two are `2026-10-03_…`, the third does not exist (B11 open). D Appendix B L2931 still lists the tagged block `home/duplicati/.config/Duplicati/.env`; the block is now `# file: etc/duplicati/env` (D L1265).
4. **`DBPath` re-pointing** (lane question 2): D step 8 L2293-2294 says "all BEFORE the first run" yet gives "stop the server, `cp` … and update the row — UI **Database → Placement → Save**, or `PUT /api/v1/backup/<id>`", which needs a running server (R4 B17, L31 of its lens-B table: "no literal reading" — not applied, not in the residue list); A §6.4 step 9 L275 re-points with `sqlite3` on the placed file before the installer. Two mechanisms, one of them impossible at that point. Adopt A's.
5. **The settings key's creation is not a D step for A0/A2/B**: only the installer's NOTE (D L1229) and A step 9 L275-276 say to write `/etc/credstore/duplicati-settings-key`; D step 8 goes from "Install" to "Then `systemctl start`" — with `LoadCredential=` on an absent file the unit cannot start. D step 5 (Procedure A) names only `…-key`, never `…-key.new`, which the re-key's pre-flight (`:101-105`) requires; A step 9 has it.
6. **Counts and wording**: D P0.5a item 1 L2342 "97 directories" vs A §6.3 step 1 L247 "96"; D L1877 "one `mv`" vs two; A note 6c L235 describes the fix as `|| true` while the shipped fix is `return 0` in `blessed_for` (equivalent); D L1916-1931 "Ten paths are named below; nine are landed … P0 step −1 is to review the nine" is stale — §8 now invokes the two 2026-10-03 helpers, which are in this PR, not on `main`, and have no tagged block; D 2026-10-03 row L2818 "five artifacts and two scripts" vs note 12c listing six artifacts; note 12c L2858 "whose §6.2 carries the same list" — §6.2 also lists B2, B6, B9, B11, none in this PR.
7. **Schema-upgrade expectation**: D step 8 L2299 "Expect in the journal: schema upgrade 11→12" is true for A0 only; on A2/B the hand start already ran `UpgradeDatabase` (Program.cs L1148) so the unit's first start shows no upgrade.

### DEFECT-5 — the residue list is not what I-41 and R4's follow-up rows say, and its "none changes a step … before P1" claim is false for two of its own items

- **Where**: D L1897-1902; A I-41 L185 + note 5b L191; R4 L83-93.
- **Evidence**: R4's follow-up rows carry round-4 **B11, B13–B18, B24, B26, B27, U1–U4**, "wrapper v2's `die` path with an `=`-less word", and (round 5) "the sign-in URL is logged whatever the token flag says"; note 5b additionally carries "the sdc4 read-only loop probe and the frozen evidence mirror (D-12a)". The note lists B11, B13, B14, B15, B24, B27, U1, U3 only. Of the omissions: B16 is applied (D L2376 names the moved-aside `.env`), B26 and U2 are moot (python `sqlite3`; I-28), but **B17** (DEFECT-4.4) and **B18** (D L2315 still says AC-6 "becomes provable only when the snapshot lane is re-pointed (P0.5a item 2)" — the installer re-points it at step 8; the wait is the next 13:45 UTC fire) are unapplied and unlisted; U4 is unlisted; the sdc4/D-12a items are unlisted.
- **"None changes a step that runs on the host before P1"**: the no-print extractor is P0 step 3's instrument (A step 7 L272: "every candidate B11 extracted from the histories") — if Phase C step 5's count is non-zero, step 3 is blocked on an unbuilt tool; and B14 is the installer's own printed hint (`:213-214`, the bare `VAR=value` prefix D step 10 L2305 says sudoers refuses, and a hand-typed URL D L2314 calls vacuous), which runs on the host at the first start.
- **Correction**: list exactly R4's open rows plus note 5b's, mark B16/B26/U2 as closed with the closing site, and reword the claim ("none … except P0 step 3 if Phase C step 5 counts non-zero, and the installer's hint, which D step 10 overrides").

### NIT-1 — secrets residue of the hand start

- `:37` names `--ui-password-file /root/.ui-password.new`; neither D step 6/7/8 nor A step 10 says how to create it without the value reaching `~/.bash_history` (D step 3 L2058 has the `set +o history; read -rs` idiom for key candidates; nothing for the UI password) nor when to shred it (after A step 11's password change). New place for a secret, undocumented lifetime.

### NIT-2 — rehearsal prerequisites and timer `Documentation=`

- A §6.4 step 0(a) rehearses the hand start, which requires `--settings-key-file`; the real key is written at step 9, so the rehearsal needs a throwaway key file — not stated. `util/systemd/yamaguchi-server-db-snapshot.timer:3` still points `Documentation=` at the primary checkout while the service unit points at the installed copy.

### NIT-3 — "Phase B landed" is recorded before the PR merged

- A §9 L384 and D §12 L2818 state the landing inside the change itself; harmless by local convention, noted because the clearing note's truth depends on merge order (BLOCKER-2).

## Walk of the four paths (state of the host after each step that matters)

Numbers are A §6.4's. T = snapshot timer, S = Duplicati scheduler, DB = `/home/duplicati/.config/Duplicati/Duplicati-server.sqlite`.

| Step | A0 (default) | A | A2 | B |
| --- | --- | --- | --- | --- |
| 1 `disable --now` T | T disabled+inactive; `Persistent=true` stamp kept (`/var/lib/systemd/timers/stamp-…` exists) so step 13's `enable --now` fires at once if 13:45 UTC passed meanwhile. **Nothing in an artifact enforces this on A0/A2/B** (only the re-key's pre-flight checks it, A only); if skipped and the session spans 13:45 UTC, the placed cleartext DB (A0) is copied into the backup Source. | same | same | same |
| 6 stop old server, move folder | vendor unit stopped (`Restart=always` does not restart an explicit stop); old 0777 folder aside | same | same | same |
| 9 place DB, re-point, installer, key | DB cleartext 0600 in a 0700 folder; `DBPath` re-pointed by `sqlite3` (A) — D's UI/PUT method impossible here; installer writes 7 files, `/etc/duplicati/env` 0640, `daemon-reload` only (starts/enables nothing — verified in code `:209-210`; the `.timer` reinstall changes no enablement, the wants symlink is what enables); `install -d` re-modes the folder (verified: 0777→0700 in scratch); random key at `…-key` | folder is the 09-18 copy, **encrypted under the burned key**; accepted key at `…-key`, random at `…-key.new` (A step 9 only — D step 5 omits `.new`) | wiped copy (`encrypted-fields` cleared by `WipeEncryption.cs` L145-154, `pbkdf-config` = ''), key as A0 | installer creates the empty 0700 folder; key as A0 |
| 10 hand start | **not run**; if run by mistake: schema 11→12 written, `FixInvalidBackupId`/settings may be saved with `pbkdf-config` encrypted under the new key, exit 103 → `die`, params file shredded; the unit start (same key) is consistent — harmless. If run before the installer/key: gate `:77-80` dies, nothing written. | not run | server runs once as `duplicati` outside the unit: upgrade 11→12, `UpgradePasswordToKBDF` mints a random password (`pbkdf-config` '' → autogenerated=True), password-init sets the known one, **exit 102 before the web server and before `ReWriteAllFields`** (DEFECT-1); `encrypted-fields` still `False`; `-wal`/`-shm` likely left; S never created, T disabled | same, on a fresh schema-12 DB |
| 10 `systemctl start` (installed unit) | wrapper exports the credential as `SETTINGS_ENCRYPTION_KEY`; server upgrades 11→12, rewrites every field under the new key and VACUUMs **before** `Server has started` (Program.cs L324 → L328); S queues the overdue job but `startup-delay`/pause holds it; the window until step 11's `pause` is the unverified `startup-delay` value (pre-existing design risk) | starts under the accepted key, DB still under the burned key until step 12 | consistent (DEFECT-1 explains why); flag becomes True here | same |
| 11 login, credential, pause, edits, resume | needs B2 (BLOCKER-2); `resume` fires the first backup at once | same | same | same |
| 12 re-key | — | pre-flight dies on B2 (BLOCKER-2); if B2 present: pause persists across both starts (verified `LiveControls.cs` Init L192-199, Program.cs L1308); decrypt start under the old key + drop-in rewrites every field cleartext (Connection.cs L136-150 with `m_encryptSensitiveFields=false`, `m_key=old`); **`systemctl revert` deletes the installed unit** (BLOCKER-1); a backup fired by step 11 is killed (DEFECT-2) | — | — |
| 13 verify copy, `enable --now` T | flag True, hash = new key; T fires at once and copies an encrypted DB via `sqlite3.backup()` while the server runs | after a corrected re-key, same | same | same |

Timer/scheduler window answer (lane item 1): with step 1 done there is none on any path — the DB is encrypted before `Server has started` at the first start, the scheduler only runs on `resume`, and the re-key holds a persisted pause. Without step 1 the window is "placement → first start" on A0/A2/B and nothing but prose closes it.

## Not refuted (claim — test that failed to refute it)

- Clearing item 1: `--require-db-encryption-key`, `--webservice-disable-signin-tokens`, `--webservice-allowed-hostnames=localhost` are in `util/systemd/duplicati.default:13` and `DEFAULTS_DST` is in the blessed `PAIRS` (`install_duplicati_service.bash:63`); all three names present in `Duplicati.Server.Implementation.dll` (utf-16le scan); `DisableSigninTokens` set from the option at every start (Program.cs L661-662).
- Clearing item 4's mechanism: `disable --now` removes the wants symlink (present today → `/etc/systemd/system/yamaguchi-server-db-snapshot.timer`); `install -m 0644` over the unit file does not touch it; `Persistent=true` + the stamp file fires the missed run at `enable --now`. Installer starts/enables nothing (code read, dry run).
- Clearing item 5: `yamaguchi-server-db-snapshot.service:32-38` executes the installed copy under `ProtectSystem=strict` with `ReadWritePaths=` on the output dir; the script's only writes are inside it (`os.makedirs/chown/chmod/replace`, `:114-150`); `SRC` is the new folder (`:61`).
- `--disable-db-encryption` satisfies `--require-db-encryption-key`: Program.cs L1249 `requireDbEncryptionKey && !(hasValidEncryptionKey || disableDbEncryption)`.
- The decrypt start decrypts (not refuses) when a valid old key is present with the flag: `Connection(con, true, oldKey)` (L1275, ctor L95-101) → `ReWriteAllFieldsIfEncryptionChanged` writes cleartext; `Decrypt` with the right key hash (EncryptedFieldHelper L112-131).
- Blob layout and the gate's offsets: `Encrypt` = `enc-v1:` + sha256hex(ciphertext) + `key.Hash` + ciphertext (EncryptedFieldHelper L157-185); `key.Hash` = sha256hex of the key string (L58-59); the gate slices `[7+64:7+128]` and compares case-insensitively; `encrypted-fields` lives at `BackupID=-2` (Program.cs L1176-1179). The copy is taken after `systemctl stop` with `-wal`/`-shm`, so the gate cannot pass while the live file differs; the only field classes it does not read are `ConnectionString.BaseUrl` and `BackupTargetUrl.TargetURL` (2.4.0.0 tables, expected empty for this job — unverifiable).
- An indefinite API pause persists: `Pause(bool)` sets expiration ticks 0 (LiveControls L312-331) → `PausedUntil` saved (Program.cs L1308) → next `Init` reads `Ticks == 0` → Paused (L192-199); the overdue schedule is queued at start but the queue runner is paused (L1306).
- `--parameters-file` is read in-process by the Server (Program.cs L230-238, `ReadOptionsFromFile` L1617-1699) and `--settings-encryption-key` is a Server option (L1595); exit codes 102/103 at L682/L686 only when `AutogeneratedPassphrase` is True/False.
- Hand start secrets handling: both values go through a 0600 `duplicati`-owned file inside the 0700 folder, never argv/env; `cleanup` shreds it on every exit (`:98-104`); dry run prints paths only (ran it: no values); `sudo`'s `COMMAND=` line carries paths only. The test's `assertNotIn("dummy", …)` covers the dry-run path; fixtures hold placeholders, not secrets; `duplicati-env.contract` has no assignment; the installer refuses a credential-shaped line (`:102-105`).
- Re-key secrets handling (excluding DEFECT-3's leftover copy): no `set -x`; the gate prints counts only; the journal is only `grep -c`'d; nothing of the key reaches argv.
- `install -d -m 0700` re-modes an existing directory (tested in scratch) — the installer's claim at `:172-175`.
- `is_option` accepts the bare `--disable-db-encryption` word appended by the drop-in; the wrapper passes it as argv precedence 4.
- The three dry runs run as a non-root user, exit 0, and print no values (`val/PB/B/dry/`).

## Unverifiable (what would test it)

- `systemctl revert`'s deletion on this exact host — needs root and touches the unit; the man page plus the presence of the vendor file is the evidence. Test: on a throwaway unit with a `/usr/lib` and an `/etc` copy, `systemctl revert` then `ls`.
- Whether the hand start leaves `-wal`/`-shm` (needs a run; the `finally` block never disposes the connection).
- `LoadCredential=` with `InaccessiblePaths=-/etc/credstore` (AC-12a rehearsal, A step 0b).
- `sudo -u pcalnon` HOME for B2's `expanduser` (R4 U3).
- The snapshot unit reading a WAL database under `ProtectHome=read-only` when the server is **stopped** (clean close deletes `-wal`/`-shm`; a read-only directory cannot recreate `-shm`) — only matters if the timer fires while the server is down; test: `systemd-run` with the unit's properties against a scratch copy with the server stopped.
- `ExtractOptions`'s quote stripping for a UI password that begins and ends with the same quote character (file not in the source copy).
- The `startup-delay` value that bounds the window between the first start and step 11's `pause`.

## Slips

None. No unit was started, stopped, reloaded or reverted; no Duplicati binary ran (dry runs only, `DUPLICATI_SERVER` untouched and `--dry-run` set); no `sudo`; no secret file read (`/home/duplicati` and `/etc/credstore` were `ls -la`/`stat`-ed only; `/etc/default/duplicati`, a 0644 config file, was read through a `sed` that prints variable names only); no journal or `/var/log` read; nothing under `/mnt/Backups/` touched; git used read-only (`show`, `diff`, `log`, `merge-base`, `branch --contains`); writes only under `<scratch>/val/PB/B/`.

<!-- markdownlint-enable -->

---

## Round 2, lane C — run the things

Archived verbatim (28,411 characters, sha256 `830d15bb66985383`), lifted from the report file the lane wrote itself, in session 652c1204's scratch directory, on 2026-10-03.

<!-- markdownlint-disable -->

# Lane C — run the things (Phase B validation, 2026-10-03)

Working tree: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/cached-swinging-summit` (branch `wip/backup-phase-a`).
Scratch: `<scratch>/val/PB/C/` — numbered `NN_*.txt` files hold the full outputs quoted below; `mut/`, `inst/`, `pw/`, `gate/`, `repro/` hold the scratch trees and runners.
"D" = `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` (this tree's copy; line numbers are its).

## Manifest

```
$ sha256sum -c <scratch>/val/PB/MANIFEST.sha256      # from the working tree
… 18 lines, every one `: OK`; exit=0
$ git check-ignore -v util/systemd/duplicati-env.contract
(nothing) check-ignore exit=1                        # not ignored
$ git diff --stat origin/main HEAD -- notes/JUNIPER_2026-09-21_…INTEGRATED-DESIGN.md
(nothing)                                            # HEAD's D == main's D
```

## Findings

### BLOCKER

**C-1. `systemctl revert duplicati.service` deletes the installer's unit on this host, so the re-key's ENCRYPT start runs the VENDOR unit with the keys already swapped and the database in cleartext.**
Where: `util/ad-hoc/2026-10-03_rekey_settings_key.bash:40-41` ("the drop-in is removed; the unit is back to the installed text"), `:109` (tells the operator to run `systemctl revert` as cleanup), `:156` (`run systemctl revert "${UNIT}"`); D §8 clearing block lines 1877-1878 ("a runtime drop-in it removes with `systemctl revert`"), D §P1 line 2374; `tests/test_duplicati_wrapper_contract.py:198` pins `systemctl revert duplicati.service` in the required order.
Claim as written: revert removes the drop-in and leaves the installed unit in effect.
Evidence:
```
$ for p in /usr/lib/systemd/system/duplicati.service /etc/systemd/system/duplicati.service; do stat -c '%A %U:%G %s %n' "$p" || echo ABSENT $p; done
-rw-r--r-- root:root 461 /usr/lib/systemd/system/duplicati.service
ABSENT /etc/systemd/system/duplicati.service        # until the installer runs (P0 step 9)
$ systemctl show duplicati.service -p FragmentPath
FragmentPath=/usr/lib/systemd/system/duplicati.service
$ systemctl --version | head -1 ; man systemctl | col -b | grep -A14 '^ *revert UNIT'
systemd 259 (259.5-0ubuntu3.4)
   … This command removes drop-in configuration files that modify the specified units,
   as well as any user-configured unit file that overrides a matching vendor supplied unit file.
   … if the unit file has a vendor-supplied version (i.e. a unit file located below /usr/) any
   matching persistent or runtime unit file that overrides it is removed, too.
```
The vendor unit (the package's file, edited in place: `ExecStart=/home/duplicati/bin/duplicati-wrapper.bash '--daemon-opts="${DAEMON_OPTS}"'`, no `LoadCredential=`) is exactly what D §7.3.4 lines 1250-1255 says the installer SHADOWS ("Installing to `/etc/systemd/system/duplicati.service` **shadows** that file, it does not replace it — the vendor copy stays on disk"). D states the shadowing in one section and prescribes `revert` in two others; the two are incompatible under the manual's rule. Sequence on the day: step 6 swaps the keys (`mv`), step 7 `revert` deletes `/etc/systemd/system/duplicati.service` with the drop-in, `daemon-reload`, `systemctl start` loads the vendor unit; `/home/duplicati/bin/` is deleted by P0.5a item 1 (D line 1860) so the start fails, `wait_started` dies after 120 s (`:94`), and the operator is left with: the hardened unit gone, `CRED` = new key, `CRED.old` = old key, `CRED_NEW` gone (so the script cannot be re-run — `:103` dies on the missing `.new`), the database cleartext (decrypted in step 5), server unreachable. If `/home/duplicati/bin/` still exists, the vendor unit STARTS the old wrapper instead — a worse outcome. Not demonstrable here without root; the manual and the file's presence are the evidence.
Correction: never `revert`. Replace `:156` with `rm -f "${DROPIN}"; rmdir "${DROPIN_DIR}" 2>/dev/null || true` (keep the `:157` presence check and the `:158` `daemon-reload`), change the hint at `:109` the same way, fix D lines 1877-1878 and 2374, and change the test's `order` list at `:198` (it currently REQUIRES the defective step). Also consider having the installer record, in its "Next:" text, that a vendor unit exists under `/usr/lib` and that `systemctl revert` must never be used on this unit.

### DEFECT

**C-2. `--update-backup-behavior` also waves DRIFT (an installed file edited outside the installer) and overwrites "the only evidence".**
Where: `util/install_duplicati_service.bash:107-114` (the two drifts "mean OPPOSITE things"; "Never overwrite that silently; it is the only evidence"), `:18-19` (the switch "bless[es] the repository's current contents"), `:130-148` (one `drift` flag for both), `:157-160` (install over it). D §12 D-6 row line 2500 names the switch as "the escape hatch" without distinguishing the two.
Evidence (`04d_installer_wrong_update.txt`):
```
$ DUPLICATI_INSTALL_BLESSED=inst/blessed.wrong bash util/install_duplicati_service.bash --dry-run --update-backup-behavior; echo exit=$?
3:DRIFT: installed /etc/default/duplicati does not match its blessed checksum -- changed outside this installer
7:DRIFT: installed /etc/systemd/system/yamaguchi-server-db-snapshot.service does not match …
16:would: install -m 0644 -o root -g root util/systemd/duplicati.default /etc/default/duplicati
23:would: write … with the sha256 of each of the 7 installed files
exit=0
```
Correction: on DRIFT, copy the installed file aside (`cp -p "$dst" "$dst.drifted-$(date +%s)"`) before `install`, or require a second, differently named switch for DRIFT; the test at `:142-152` cannot see this because it has no installed file to drift (see C-4).

**C-3. The installer's "no secret" gate refuses three names only; five secret-carrying shapes are deployed to `/etc/duplicati/env` with exit 0 — including the name that caused the outage.**
Where: `util/install_duplicati_service.bash:101-105` ("The env contract must carry no secret: a KEY=VALUE line with a non-placeholder value is refused"; the grep names `SETTINGS_ENCRYPTION_KEY|PASSPHRASE(_OLD)?|DUPLICATI_WEB_CREDENTIAL` on active lines).
Evidence — a scratch copy of the 8 sources + installer at `val/PB/C/repo/` (so `REPO_DIR` is the scratch tree), one mutation per case, `--dry-run`, absent blessed file (`04f_installer_mutations.txt`):
```
F1_active_key                      exit=2  REFUSING: …duplicati-env.contract carries a credential-shaped assignment
F2_export_quoted_key               exit=2  REFUSING
F8_bare_PASSPHRASE                 exit=2  REFUSING
F3_COMMENTED_key   (# SETTINGS_ENCRYPTION_KEY=abcdefghijklmnop)      exit=0  first install …   <- deployed
F4_key_OLD_name    (SETTINGS_ENCRYPTION_KEY_OLD=abcdefghijklmnop)    exit=0  first install …   <- deployed; wrapper exits 78 only at the NEXT START
F5_DUPLICATI__PASSPHRASE                                             exit=0                    <- deployed AND exported by the wrapper (allow-list :44)
F6_option_settings_encryption_key (--settings-encryption-key=…)      exit=0                    <- deployed; passed to the server on argv
F7_option_webservice_password     (--webservice-password=…)          exit=0                    <- deployed; passed to the server on argv
F9/F10/F11 ($KEY, <key>, empty)                                      exit=0  (placeholders, by design)
$ grep -n 'duplicati-env.contract /etc/duplicati/env' inst/out.F4_key_OLD_name.txt
12:would: install -m 0640 -o root -g duplicati util/systemd/duplicati-env.contract /etc/duplicati/env
```
The contract's own text (`util/systemd/duplicati-env.contract:30`) says a commented assignment "is still a secret on disk", and F6/F7 put the value on argv — the thing `2026-10-03_password_init_hand_start.bash:27-29` exists to avoid. The unittest catches F3 for the REPOSITORY copy only; the installer is the deployment gate and is the only gate for a checkout that is not CI-green.
Correction: match any line (commented or not) with `(export\s+)?[A-Z0-9_]*(KEY|PASSPHRASE|PASSWORD|CREDENTIAL|TOKEN)[A-Z0-9_]*\s*=\s*<non-placeholder>` and any `--[a-z-]*(key|password|passphrase)=<value>` option line; the stage script's `SECRET_SHAPED` (`2026-09-22_stage_design_artifacts.py:84-92`) is the pattern to reuse.

**C-4. The suite is not hermetic for the installer: three tests read real host paths, the first-install test will FAIL on the production host once the installer has run, and the "drift path" the module docstring claims to rehearse is unreachable.**
Where: `tests/test_duplicati_wrapper_contract.py:18-20` ("every input is written into a temporary directory the test owns"), `:11-13` ("the never-blessed, drift and behaviour-change paths each get a `--dry-run` rehearsal"), `:137` (asserts `would: install -m 0640 … /etc/duplicati/env`); installer `:48` (`ENV_DST=/etc/duplicati/env`, not overridable), `:166` (`[[ -e "${ENV_DST}" ]]`), `:135` (sha256 of the real `${dst}`), `:43-51` (all DSTs hardcoded).
Evidence:
```
# host state (stat only): /etc/default/duplicati EXISTS (duplicati:duplicati 404 B) and both snapshot units exist under /etc/systemd/system
$ DUPLICATI_INSTALL_BLESSED=inst/blessed.equal bash util/install_duplicati_service.bash --dry-run   # blessed == repo for all 7 (04b)
DRIFT: installed /etc/default/duplicati does not match its blessed checksum …
DRIFT: installed /etc/systemd/system/yamaguchi-server-db-snapshot.service does not match …
Refusing to install …  exit=4            # host content, not the script, decided this
$ … blessed.equal5 (the 5 destinations absent on this host or identical to it)  exit=0, 0 DRIFT/BEHAVIOUR lines (04b2)
# one-line edit on the scratch copy: ENV_DST -> an existing scratch file (04g):
48c48  < ENV_DST=/etc/duplicati/env  > ENV_DST=…/inst/existing-env
12:kept existing …/inst/existing-env (not overwritten; …)     # and NO `would: install -m 0640` line -> :137 fails
```
So `test_first_install_runs_to_the_end_without_a_blessed_file` goes red on the owner's host after P0 step 9, and no test can create an installed file, so the DRIFT branch (`:135-138`) has no rehearsal; today it fires on this host only by accident (the pre-existing `/etc/default/duplicati`) and nothing asserts it.
Correction: a test-only destination prefix (`DUPLICATI_INSTALL_PREFIX`, same pattern as `DUPLICATI_INSTALL_BLESSED` at `:54-56`) applied to every `*_DST`, `ENV_DIR`, `DATA_FOLDER`, `CRED_DST`; then write real DRIFT and "kept existing" tests, and reword `:11-20`.

**C-5. The re-key order test is blind to three dangerous re-orderings because it matches FIRST occurrences and `systemctl stop`/`start` each occur three times.**
Where: `tests/test_duplicati_wrapper_contract.py:193-202` (`positions = [out.find(step) …]`).
Evidence — scratch copies of the script with two steps swapped, tracked test run against each (`03_rekey_order_test_mutations.txt`, diffs in `mut/`):
```
R1_pause_after_first_stop     TEST FAILS (caught)
R2_revert_before_mv           TEST FAILS (caught)
R3_vacuum_before_gate         TEST FAILS (caught)
R4_encrypt_start_before_revert  TEST PASSES (NOT caught)   # server starts under the drop-in with the NEW key
R5_mv_before_second_stop        TEST PASSES (NOT caught)   # keys swapped under a RUNNING decrypt-mode server
R6_gate_before_third_stop       TEST PASSES (NOT caught)   # gate (and VACUUM) on a live server's database
$ bash mut/rekey.R5_mv_before_second_stop.bash --dry-run | grep -n would:
13: would: mv /etc/credstore/duplicati-settings-key … ; 14: would: systemctl stop duplicati.service   # mv printed BEFORE the stop
```
Correction: assert the whole `would:` sequence (collect the lines, strip paths, compare to an expected list) rather than first-occurrence positions.

**C-6. The re-key exit gate scans three of the five columns that carry `enc-v1:` blobs; the old key is shredded on a pass.**
Where: `2026-10-03_rekey_settings_key.bash:180` (`Option.Value`, `Backup.TargetURL`, `Source.Path`), `:42-44` ("every `enc-v1:` blob carries sha256(new key)"), `:218` (`shred -u "${CRED}.old"`); D §8 line 1881 repeats the "every `enc-v1:` blob" claim.
Evidence — the 2.4.0.0 source (`<scratch>/val/B/src/Duplicati/Library/RestAPI/Database/Connection.cs`): `EncryptedFieldHelper.Encrypt` is called at `:491` (Source.Path), `:862` (Backup.TargetURL), `:1589` (Option.Value via `EncryptSensitiveFields`), `:1656`/`:1680` (**ConnectionString.BaseUrl**), `:1794` (**BackupTargetUrl.TargetURL**). `ReWriteAllFieldsIfEncryptionChanged` (`:131-152`) rewrites backups (which reach `BackupTargetUrl` through `LoadChildren`, `Backup.cs:54`) and the server settings — it never touches `ConnectionString`. Gate in isolation (`08_rekey_gate_isolated.txt`, G11): a K2 blob in a table the gate does not read → `PASS rc=0`. Whether the Yamaguchi database has rows in those two tables is unverifiable here (cannot read it); if it does, a pass shreds the only key that opens them.
Correction: add `'SELECT "BaseUrl" FROM "ConnectionString"'` and `'SELECT "TargetURL" FROM "BackupTargetUrl"'` to the tuple at `:180` (the `try/except OperationalError` already tolerates an absent table), and state in `:43` which columns are covered.

**C-7. The re-key script's header and the assessment's B4 row describe pre-flight checks the code does not have, and one it has the opposite of.**
Where: `2026-10-03_rekey_settings_key.bash:23` ("pre-flight: … the unit active, **no backup running**, …") — no code checks for a running backup (`:116` `api serverstate || true` is informational; grep for `progress|ActiveTask|ProgramState` finds only the comment); `:121` then `systemctl stop`s a server that may be mid-backup. `notes/…ASSESSMENT-AND-RECOVERY-PLAN.md:222` (B4): "refuses to run with the server active or a backup in progress" — the script REQUIRES the unit active (`:107` dies if it is not). Also `:110` (the API-verb check) is root-free yet skipped under `--dry-run` (`:106`), so the dry run passes on a tree where the real run dies at pre-flight (see C-8).
Correction: implement the running-backup refusal once the `serverstate` verb exists (or document that pause + stop aborts a running backup), fix the B4 row, run `:110` in dry-run too.

**C-8. D records STOP defect 3 (the API clients' `serverstate`/`pause`/`resume`) as fixed, but the client in this tree is `main`'s and has no such verbs; the fix is open PR #2115, which D does not name.**
Where: D front matter line 6 ("its five procedure defects … are fixed in the artifacts §8 installs"); D §8 clearing block lines 1882-1884 ("The API clients … carry `serverstate`/`pause`/`resume` … (the assessment's B2)"); `2026-10-03_clear_stop_and_sync_backup_design.py:27-28`. The assessment's own row (`…ASSESSMENT-AND-RECOVERY-PLAN.md:384`, new in this set) says "B2 and B6 in their own [PR]".
Evidence:
```
$ git status --porcelain -- util/ad-hoc/yamaguchi_server_api.py; git diff --stat origin/main HEAD -- util/ad-hoc/yamaguchi_server_api.py
(both empty: identical to main)
$ python3 util/ad-hoc/yamaguchi_server_api.py --help | grep -c serverstate
0            # choices: {status,export,abort,delete,import,run,progress,log,task}
$ gh pr list --state open … -> 2115 fix/backup-b2-web-credential-serverstate-backup-id (OPEN, MERGEABLE; touches ci.yml @986 and docs/REFERENCE.md — different hunks from this set's @625/:2831)
```
Consequence: with this set merged and #2115 not, `rekey …bash` dies at `:110` ("B2 must land first") — fail-closed, no damage — but the document of record says otherwise, and the merge order is unstated.
Correction: D's clearing block item 3 and note 8a should say "lands with ml#2115" (or the set should merge after #2115 and D's row name it).

### NIT

**N-1.** `--dry-run` writes to the checkout: `util/install_duplicati_service.bash:100` (`python3 -m py_compile`) leaves `util/ad-hoc/__pycache__/yamaguchi_server_db_snapshot.cpython-314.pyc` (observed in the working tree at 06:25:35 during the suite run, and reproduced on the scratch copy: 0 pyc before, 1 after). Contradicts `:16` ("write nothing"); under `sudo` the pyc is root-owned. Use `python3 -c 'import ast,sys; ast.parse(open(sys.argv[1]).read(), sys.argv[1])'` or set `PYTHONPYCACHEPREFIX`.

**N-2.** Unit-file syntax is unchecked in dry-run and checked too late in the real run: F15 (garbage appended to `duplicati.service`) → `exit=0`, 16 `would:` lines; the real run's `systemd-analyze verify` (`:210`) comes after install, bless and `daemon-reload`, so a broken unit is already installed and blessed when it fails. `systemd-analyze verify` accepts source paths unprivileged (the design linter already does this at `2026-09-21_lint_design_snippets.py:130`).

**N-3.** The password-init port gate fails open on a busy host: `2026-10-03_password_init_hand_start.bash:81` is `ss -ltn 2>/dev/null | grep -qE …` under `set -o pipefail`; `grep -q` exits on the first match and a producer with more than one pipe write dies of SIGPIPE, making the pipeline status 141, which `if` reads as "not in use". Demonstrated: `set -o pipefail; seq 1 400000 | grep -qE '^7$'` → `MISSED: pipeline status=141`; `seq 1 40 | …` → detected. This host's `ss -ltn` is 2160 bytes / 36 lines, so P5 (a real bound port, 60173) was correctly refused. Also fails open when `ss` is absent. Use `ss -ltnH "sport = :${PORT}" | grep -q .` (filter in `ss`, no early exit).

**N-4.** `tests/test_duplicati_wrapper_contract.py:85` misses a commented assignment with spaces around `=`: M5 (`# SETTINGS_ENCRYPTION_KEY = abc`) → `failures=0` (`02_contract_test_mutations.txt`); the other nine mutations (M1-M4, M6-M10) are caught. Allow `\s*=\s*`.

**N-5.** The module docstring (`:14-16`) claims tests for "a port in use" and for the re-key script's refusals; no test binds a port and the re-key script's gates (`:99-111`) are root-only and untested. The ci.yml comment (`:628-635`) is accurate; the docstring is not.

**N-6.** The re-key dry run silently substitutes a fallback ExecStart when the installed unit is absent (`:131-134`): on this host `07_rekey_dry_run.txt:8` prints `ExecStart=/usr/local/lib/duplicati/duplicati-wrapper.bash $DAEMON_OPTS --disable-db-encryption` with no word that it is the fallback, so a reviewer reads it as the installed text. (The fallback equals `util/systemd/duplicati.service:27`, so the shape is right.) Print "(fallback — installed unit absent)".

## Not refuted

- **Suite as shipped**: `python3 -m unittest -v tests/test_duplicati_wrapper_contract.py` → `Ran 13 tests … OK` (`01_…`). `python3 -m unittest tests.test_ci_test_wiring_drift` → `Ran 14 tests OK`. The suite is named at `.github/workflows/ci.yml:636` (comment `:628-635`) and `docs/REFERENCE.md:2831`; `util/ad-hoc/2026-09-10_agents_md_test_list_drift.py` → 169 on disk, 0/0/0 drift. The predecessor suite `test_duplicati_recovery_guards.py` is likewise only in the run-all block, so no per-suite description convention is broken.
- **`test_shipped_contract_has_no_commented_assignment_and_no_key` fires** under M1 `# export SETTINGS_ENCRYPTION_KEY=abc`, M2 `# SETTINGS_ENCRYPTION_KEY=abc`, M3/M4 active key lines, M6 `# export TZ=UTC`, M7 an extra option line, M8 `DUPLICATI__PASSPHRASE=abc`, M9 leading whitespace, M10 quoted value (tracked module imported, `CONTRACT` pointed at a scratch copy; `mut/run_contract_mutations.py`).
- **Re-key order test fires** on R1 (pause after the first stop), R2 (revert before mv), R3 (VACUUM before the gate) — "the re-key steps are out of order".
- **Installer (a)**: absent blessed file → `exit=0`, `first install: no … yet`, seven `would: install -m …` lines (`04a` lines 5-11), `would: install -m 0640 -o root -g duplicati util/systemd/duplicati-env.contract /etc/duplicati/env` (12), `would: write … 7 installed files` (14), `would: check /etc/credstore/duplicati-settings-key …` (15), `would: systemctl daemon-reload` / `systemd-analyze verify` (16-17). "Next:" says `systemctl start duplicati.service` and "(START, never restart …)"; no `restart` command anywhere.
- **(c)** wrong hashes → `exit=4`, seven `BEHAVIOUR CHANGE:` lines + `Refusing to install.`; **(d)** with the switch → `exit=0`, `would: write`; **(e)** `--bogus` → `unknown argument: --bogus`, `exit=2`; non-root without `--dry-run` → `run with sudo …`, `exit=2`.
- **(b)** restricted to the five destinations absent on this host or identical to it → `exit=0`, zero DRIFT/BEHAVIOUR lines (the repo==blessed half of the claim holds; the installed==blessed half is Unverifiable).
- **Installer syntax gates**: F12/F13 (`if [[ 1 ]]; then` appended to wrapper/guard) → `bash -n` error, `exit=2`; F14 (`def broken(:` in the snapshot script) → `SyntaxError`, `exit=1`; F16 (contract removed) → `missing source: …`, `exit=2`; F0 pristine scratch tree → `exit=0`.
- **Password-init dry run** (`05_…`): `exit=0`; prints `--parameters-file=<file>`, `expecting exit 102 … 103 means … Procedure A0`, names the two files by PATH; `grep -c dummy-` on all output = 0; data folder left empty. Gates: pw 0640 → `exit=1 FATAL: secret file must be mode 0600, never readable by the group: … is 640`; key 0640 → same; folder 0750 → `exit=1 FATAL: data folder must be pcalnon-owned mode 0700 …: pcalnon:750`; empty file → `exit=1 … missing or empty`; port 60173 bound by a scratch python listener → `exit=1 FATAL: port 60173 is in use`; unknown flag → usage, `exit=2`; non-root real run → `exit=1 FATAL: run with sudo` before the trap is installed.
- **Trap proof** (`06_…`; scratch COPY edited at exactly two lines — `:85` root check neutralised, `:128` `sudo -u "${RUN_AS}" --` → `env --`; `DUPLICATI_SERVER` = a scratch script that records and exits): for fake exits 103 / 102 / 1 the server saw a parameters file that `exists=yes mode=600 owner=pcalnon lines=2`, option names `--settings-encryption-key --webservice-password-init`, `in data folder: yes`; after the script exited the file was gone (`parameters file shredded` logged) in all three cases; exit 103 → script `exit=1` with the "Procedure A0 case" message; 102 → `exit=0`; 1 → `exit=1 unexpected exit`; a two-line key file → python `FATAL: each secret file must hold exactly one non-empty line`, no file created, server never invoked. No `dummy-` string in any output. `SERVER=` is assigned once (`:47`, from `DUPLICATI_SERVER`), no fallback path anywhere else.
- **Re-key dry run** (`07_…`): `exit=0`; the 25 lines name every step in the required order — pause (4-6) → stop (7) → drop-in `… $DAEMON_OPTS --disable-db-encryption` (8) → daemon-reload → start (10) → wait (11) → stop (13) → `mv …key …key.old (0600) ; mv …key.new …key` (14) → revert (15) → start (17) → wait → stop (19) → copy + `encrypted-fields=True, every enc-v1 blob …, no drop-in` (20) → `PRAGMA wal_checkpoint(TRUNCATE); VACUUM;` (21) → start (22) → resume (24) → serverstate/shred (25). Nothing executed (`would:` only; no `sudo`, no `systemctl`). `--bogus` → usage `exit=2`; non-root → `FATAL: run with sudo (or --dry-run)` `exit=1`. Pre-flights exercised in dry-run: credential files (only if visible — here "not visible", by design), the installed unit's `ExecStart=` (absent here → fallback, N-6). Skipped (root-only or gated by `DRY_RUN == 0`): root (`:99`), unit active (`:107`), timer disabled (`:108`), stale drop-in (`:109`), API verbs (`:110`, C-7), DB present (`:111`).
- **Gate in isolation** (`08_…`; the 17-line heredoc extracted verbatim — occurs exactly once in the script — run against scratch SQLite with blobs built as `"enc-v1:" + sha256hex(ct) + sha256hex(key) + ct`): G1 all under K1, flag True, key K1 → PASS (`blobs=5 under-new-key=5`); G2 same DB, K2 → FAIL (`under-another-key=5`); G3 one blob under K2 → FAIL; G4 `Backup.TargetURL` under K2 → FAIL; G5 flag `False` → FAIL; G6 flag absent → FAIL; G7 flag True, zero blobs → FAIL; G8 truncated blob → FAIL; G9 flag `true` lowercase → PASS; G10 blob keyed with a trailing newline vs a cred file without → FAIL (the `rstrip("\n")` at `:175` is load-bearing and consistent with the wrapper's `$(<file)`).
- **Document of record reproduced** (`09_…`, tree `val/PB/C/repro/`: `git show HEAD:…D` as `notes/…` (sha256 prefix `5d875ed9…` == `origin/main`'s), the four scripts and the 14 STAGE files at their relative paths): `--from-repo` → `5 block(s) rewritten from the repository, 9 already identical, 1 marker(s) retagged`; clearing script → `applied 26, already-present 0; 9 line(s) wrapped; fenced blocks unchanged: 20; … now 2956 lines`; second run → `no change (26 edit(s) already applied) -- idempotent`; `cmp repro/D worktree/D` → `exit=0`, both `f80230470baaf3a0…` (the manifest's hash); `--check` → `0 staged, 14 already current, 0 skipped`; pinned `markdownlint --config .markdownlint.yaml` → exit 0, no output; `awk 'length($0) > 512'` → 0 lines (HEAD's D also 0).
- **Secret-shape sweep** over the 18 files (`10_…`, `10b_…`): no `hf_`, `pypi-`, `AgEIcHlwaS`, `ghp_`, `github_pat_`, `AKIA`, `xox[abp]-`, `-----BEGIN` hit; a deliberately broad 40+-char base64-alphabet probe hit 78 places, all classified without printing values: 31 forty-hex action SHA pins in `ci.yml`, 46 paths (`/` is in the alphabet), 1 camel-case identifier at `docs/REFERENCE.md:1002` (pre-existing; this set's only REFERENCE.md change is `:2831`). `KEY=`/`PASSPHRASE=`/`PASSWORD=`/`TOKEN=`/`SECRET=` assignments with a non-placeholder value: none — the 11 regex hits are `'x'`/`'y'` (assessment `:342`), `%s`/`(.*` (D `:481, :2018, :2058, :2141, :2239`) and Python code fragments (`key = open(…`, `key = self.tmp`, `SECRET_SHAPED = re.compile(`). E-mail addresses of any domain: none in the 18 files. Owner's local-part: none.
- **Lint** (`11_…`): `bash -n` + `shellcheck -x -S style` clean on the two new ad-hoc scripts, the installer and the wrapper; `flake8 --max-line-length 512` clean on the five Python files. `util/yamaguchi-pre-backup-guard.bash` (blessed set, not in the manifest) and `2026-09-21_wrap_long_markdown_lines.py` are byte-identical to `origin/main` and clean in the tree.

## Unverifiable

- Installer (b) as specified — "installed == blessed == repo" for all seven destinations: every `*_DST` is a hardcoded root path (`:43-51`); the dry run compares the REAL `/etc` and `/usr/local` files, and two of them exist here with other content. Verified only for the five destinations that are absent or identical on this host. A `DUPLICATI_INSTALL_PREFIX` (C-4) would make it testable.
- The real effect of `systemctl revert duplicati.service` on this host (C-1): a privileged action on a real unit, forbidden; the manual on this host plus the vendor unit's presence are the evidence. A non-privileged demonstration is impossible (user managers have no writable vendor directory).
- Whether `Duplicati-server.sqlite` has rows in `ConnectionString` / `BackupTargetUrl` (C-6): the database is unreadable here.
- The re-key script's root-only pre-flights (`:99-111`) and its whole real path (`wait_started`'s journal grep, the drop-in write, the `mv`, the live VACUUM); the password-init's real `sudo -u duplicati` exec (replaced by `env --` in the trap proof) and the `chown` to another uid.
- Whether 2.4.0.0 treats a bare `--disable-db-encryption` (no `=true`) as true in the drop-in (Lane B's lens).
- The dry run's hint `sudo -u duplicati DUPLICATI__REMOTEURL=… <guard>` (installer `:213-214`) relies on sudoers permitting a command-line environment assignment for root; plausible under `root ALL=(ALL:ALL) ALL`, not tested.

## Slips

- Three read-only GitHub calls (`gh pr list`, `gh pr view 2115`, `gh pr diff 2115`) to establish C-8; the brief said no network calls are needed. No credential, address or file content was sent; only PR metadata and a diff were read.
- `systemctl cat duplicati.service` and `systemctl show -p FragmentPath` — read-only queries of a real unit (no start/stop/reload/daemon-reload).
- Running the tracked suite from the working tree let the installer's `py_compile` write `util/ad-hoc/__pycache__/yamaguchi_server_db_snapshot.cpython-314.pyc` into the working tree (git-ignored; N-1 is the cause). I did not delete it.
- The stage script's `--check` in the repro tree ran the design linter, which runs `systemd-analyze verify` and `shellcheck` on SCRATCH copies under a temp dir — not a unit operation.
- No `sudo`, no Duplicati binary, no secret file read (`stat` only on `/etc/credstore`), no unit started/stopped/reloaded, nothing under `/mnt/Backups/` touched, no tracked file modified, no git write.

<!-- markdownlint-enable -->

---

## Round 2, the ml#2114 lane

Archived verbatim (23,918 characters, sha256 `2ca5b4797d59c710`), lifted from the report file the lane wrote itself, in session 652c1204's scratch directory, on 2026-10-03.

<!-- markdownlint-disable -->

# Validation lane PB — PR pcalnon/juniper-ml#2114

**PR**: "fix(backup): tier 2 finds its drives under /run/media and gains an installer, a failure unit and tests"
**Head**: `5a849222` on `fix/backup-tier2-run-media-installer-failure-unit`, base `main` (branch base `79dc36d5`, rebased on `c01c837e` = merge of ml#2113)
**Worktree read**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/agent-ae6bdb203f422cdfa` (nothing written there)
**Probe scripts and raw outputs**: `<scratch>/val/PB/pr2114/probe{1,2,3,5,6}*` with `probe*.out`, `mutation_check.out`, `pr_body.md`
**Verdict**: **REFUTED on claims, not on code.** The code changes do what the diff says and the defaults are right for the owner's host (`/run/media/pcalnon`, the two UUID names, `Juniper-8.0.0.python`; Linger=yes; nothing of this lane installed yet). Three things the PR *says* are not what the lane *does*, and one of them is the owner's acceptance instruction, which as written produces `FAILED`. Fixes are small (text in the installer/docs, one validation clause, one reporter title) but they are in files this PR ships.

---

## Findings

### BLOCKER-1 — "Mount a stick … Expect result=OK" is false: with the default two-device list, a one-stick run is `FAILED` (runner rc 4), never stamps, and re-runs the whole archive set on every plug-in

The PR's acceptance instruction (installer closing message, `util/install_juniper_backup_timer.bash:208-209`: *"Mount a stick. The .path unit should start a due run … Expect result=OK and verified archives on every mounted stick."*; PR body "Test plan" owner item 2 "the OK (plugged) run"; `docs/REFERENCE.md:722` "Do the first OK run") does not say both configured sticks must be mounted, and the lane cannot reach OK otherwise:

- Runner, unchanged accounting: `CONFIGURED_COUNT="${#MEDIA_NAMES[@]}"` (`util/juniper-backup.bash:458`) is the *configured* count (2 by default), `TOTAL_EXPECTED += CONFIGURED_COUNT` per repo (`:576`), and `TOTAL_WRITTEN < TOTAL_EXPECTED` → `exit 4` PARTIAL (`:636-638`).
- Scheduler, unchanged: only `rc == 0` writes stamps and `result=OK` (`util/juniper-backup-scheduled.bash:86-93`); any other rc → `result=FAILED "runner rc=N"`, no stamp, exit rc → `juniper-backup.service` fails → `OnFailure=` fires.
- Reproduced end to end through the INSTALLED copies in the PR's own fixture with a gpg stub that "encrypts" into the scratch drive (`probe6_single_stick_ok_run.py`, output `probe6.out`):
  - ONE stick: `written and verified: 1 of 2 expected archive copies` → `PARTIAL` → scheduler `FAILED rc=4 (no stamp written)`; `last-run.status` = `FAILED | runner rc=4`; stamps `[]`; the archive IS on the stick.
  - BOTH sticks: `COMPLETE` → `OK (stamped EBC5-F0A3 DFF3-2782)`.

Consequence on the owner's host if the message is followed with one stick: a multi-hour run that ends `FAILED`, a desktop alert (titled for the wrong lane, DEFECT-3), no stamp — so the lane stays "never succeeded", every subsequent `.path`/timer trigger reads `FAILED`, and the next plug-in of the same stick is "due" again and rebuilds the full set (new UUID; nothing prunes — design §7.8 last paragraph, D-10). Right now neither stick is mounted (`findmnt`: only `/mnt/Backups` and the NTFS partition `/run/media/pcalnon/848099D78099CFD2`), so the plan's "(the sticks are plugged in)" (`…RECOVERY-PLAN.md:238`) is not currently true either.

The design shares the ambiguity (§7.8 `:1506` "fires the same service when either drive appears"; AC-10 `:2306` "produces verified archives on every mounted drive" — satisfied, yet the lane status is FAILED). Minimal PR fix: say "mount BOTH configured sticks (`EBC5-F0A3` and `DFF3-2782`) for the OK run; one stick is rc 4 PARTIAL = FAILED, not OK" in `install_juniper_backup_timer.bash:208-209`, `docs/REFERENCE.md` (Scheduled lane subsection, `:722`), CHANGELOG and the PR body. Whether the scheduler should instead hand the runner only the mounted set (`JUNIPER_BACKUP_DEVICES="${mounted[*]}"`) is a change to a tagged block and an owner decision; flag it to the parent, do not make it here.

### DEFECT-1 — For an absolute `JUNIPER_BACKUP_DEVICES` entry the mount guard does NOT stand between it and the system disk; the only remaining discriminator is "BACKUP_DIR already exists and is writable"

Claimed: `util/juniper-backup.bash:235` *"the mount guard below is what stands between it and the system disk, exactly as for a relative one"*; `:103`, CHANGELOG `:140` and `docs/REFERENCE.md:702` "the mount guard applies to it unchanged"; PR body bullet 1.

Measured (`probe1.out`, real `mountpoint(1)`): `mountpoint -q` is TRUE for `/`, `/home`, `/tmp`, `/run`, `/dev/shm`, `/run/user/1000` on this host (only `/boot` is false). The guard (`util/juniper-backup.bash:382-386`) therefore passes for every one of them. What stops a write is `:387-394` — `[[ -d backup_path ]]` and `[[ -w backup_path ]]` — i.e. a pre-existing writable `<entry>/Juniper-8.0.0.python`. The free-space check (`:498-504`) only WARNs.

Dry-run proof on the real host, real `mountpoint`, gpg PATH-stubbed, scratch `--source`, nothing written (`probe2.out`):
- `JUNIPER_BACKUP_DEVICES=/` → `SKIP /: //Juniper-8.0.0.python does not exist` (not "is not a mount point": the guard passed; the missing directory is what saved it). Same for `/home`.
- `JUNIPER_BACKUP_DEVICES=/run/user/1000 JUNIPER_BACKUP_DIR=systemd` (a user-owned dir on a system tmpfs) → `OK   /run/user/1000` and `[dry-run] build -> /run/user/1000/systemd/Juniper_fakerepo_….tbz2.gpg`, rc 0. A real run with that setting writes the whole archive set into RAM-backed tmpfs.
- The relative form reaches the same places through the root: `JUNIPER_BACKUP_MEDIA_ROOT=/ JUNIPER_BACKUP_DEVICES=tmp` → guard passed on `//tmp`, stopped only by the missing dir.
- Hermetic composition (`probe2.out` 2e): stub `mountpoint` → yes + pre-existing dir → `OK` + build line.

Today no `Juniper-8.0.0.python` exists at `/`, `/home`, `/tmp` or `$HOME` (checked), and no default is affected, so this needs an operator to set the variable to a system mount AND have the directory there — hence DEFECT, not BLOCKER. But the previous runner could only ever write under `/media/pcalnon/<name>/`; this PR widens the reachable write set to any absolute path while describing the guard as unchanged protection. Cheap fix in the validation block (`:239-243`): accept an absolute entry only under the design's own roots (`/mnt/`, `/media/`, `/run/media/` — §7.9 says `/mnt/`), exit 2 otherwise; and correct the comment at `:235`. The PR's test `test_absolute_entry_is_still_mount_checked` (docstring: "only the guard stands between it and the system disk") pins the misconception rather than the hazard — it never tries a mounted system path.

### DEFECT-2 — The design's §7.9 recipe for the fstab drive ("the same scheduler with `JUNIPER_BACKUP_DEVICES` set to the drive's mount name" + the `/` form) is a silent never-due lane under the unchanged scheduler, and the runner copies to an absolute entry the scheduler never stamps

PR body decision 2 says the scheduler does not take the `/` form and documents the `MEDIA_ROOT=/mnt` + `DEVICES=JuniperArchive` workaround (`docs/REFERENCE.md:664`). True, and measured through the installed copies (`probe3.out`):
- (3b/3c) `JUNIPER_BACKUP_DEVICES="EBC5-F0A3 <abs>/mnt/JuniperArchive"` with only the absolute drive mounted: the scheduler probes `-q /run/media/<user>/<abs>/mnt/JuniperArchive` (root-prefixed, `scheduled.bash:68`), silently `continue`s (`:69`, no log line), and reports `no configured drive usable … (wanted: EBC5-F0A3 <abs>/…)` → `FAILED` before the first success, `SKIPPED` forever after a stick has succeeded.
- (3a) With a stick due, the runner (same env) also `OK`s and copies to the absolute entry; stamps written: `last-success.EBC5-F0A3` only. So the runner's device set is a superset of the scheduler's and the claim "cannot name different paths" (`docs/REFERENCE.md:659`, runner `:140-142`, CHANGELOG) is an overclaim for this form.
Not the PR's code, but the PR implements the `/` form the design pairs with the scheduler; the parent's doc fix should either make §7.9 say the `MEDIA_ROOT=/mnt` form, or the T3 step must teach the scheduler. The scheduler could also log an absolute entry as "unsupported" instead of `continue` — a tagged block, owner's call.

### DEFECT-3 — A tier-2 failure's desktop notification is titled "Duplicati backup FAILED"

`util/duplicati_backup_failure.bash:53-54` hard-codes `notify-send … "Duplicati backup FAILED"`; nothing in the unit's `Environment=` or `$1` reaches the title. The record in `failures.log` is correct (unit=juniper-backup.service, this lane's state dir — verified by the PR's `test_unit_as_written_records_into_this_lanes_state_dir` and by reading `:28-49`), but the ANNOUNCE half of "Record and announce a Juniper USB archive (tier 2) failure" (`juniper-backup-failure.service:2`) names the other lane — the exact class §7.8 `:1568-1571` condemns ("a report about a lane that is not running"). The design's "no reporter change is needed" (P3 step 2) and the PR's "Unchanged: util/duplicati_backup_failure.bash" are wrong on this point. With BLOCKER-1 the owner would see this alert after the first one-stick run. Fix: title from `$1`/a second argument or an env var the unit sets. The test's `notify-send` stub discards its arguments, so the suite cannot see it.

### NIT-1 — `util/juniper-backup.bash:143` claims a hand run under `env -i` "resolves the same root instead of dying on set -u"; it dies three lines later

`env -i PATH=… bash util/juniper-backup.bash --dry-run --dest <scratch> …` → `line 151: HOME: unbound variable`, rc 1 (`probe2.out` 2h). The `${USER:-$(id -un)}` fallback (`:144`) is still worthwhile — cron sets `HOME`/`LOGNAME` but not `USER` — so the comment should say cron, not `env -i`. The test only covers "USER unset, HOME set".

### NIT-2 — A newline in `JUNIPER_BACKUP_DEVICES` silently drops every device after the first line

`read -r -a` reads one line (`:145`): `$'EBC5-F0A3\nDFF3-2782'` → one device (`probe1.out` 1d, `probe2.out` 2g: "checking 1 configured"). The scheduler (`scheduled.bash:26`) does the same, so the two agree; a systemd `Environment=` value is unlikely to carry a raw newline. Worth one line in the REFERENCE table ("one line, space-separated").

### NIT-3 — A hand `--dry-run` THROUGH the scheduler writes `last-success.*` stamps and `result=OK` without building anything, and the PR's suite pins that as correct

`scheduled.bash:83-88` stamps on the runner's rc 0; the runner exits 0 after a dry-run preview. `probe3.out` 3d: after `juniper-backup-scheduled.bash --dry-run …` with one stick, stamps=`[last-success.EBC5-F0A3]`, `result=OK`, archives on stick `[]`; the next unplugged run is `SKIPPED` — the "FAILED until first success" alert is silenced by a preview. Pre-existing scheduler behaviour (tagged block), but `test_due_run_reaches_the_installed_runner_under_the_same_root` (`tests/test_juniper_backup_tier2_lane.py:509-510`) asserts exactly this. Document "never run the scheduler with --dry-run by hand" or have the test assert on the runner's output rather than the OK stamp.

### NIT-4 — The installer's `--dry-run` never prints the "Do the OK run FIRST" warning

It exits at `install_juniper_backup_timer.bash:198-201`, before `:204-212`. The PR body says "the installer's closing message says the same" — true only of the real run; the preview an operator reads first does not carry it. Print it in both modes.

### NIT-5 — Overclaims folded into the above, for the parent's doc pass

- "cannot name different paths" (`docs/REFERENCE.md:659`, runner `:140-142`, CHANGELOG) — false for the `/` form (DEFECT-2).
- `Documentation=file:///home/pcalnon/Development/python/Juniper/juniper-ml/util/duplicati_backup_failure.bash` in the new unit (`:3`) is a hard-coded checkout path; same pattern as `duplicati-backup-failure.service:3`, so consistent, but a unit that outlives the checkout points at nothing.

---

## Not refuted

**Check 1 — write target vs the system disk.** Default behaviour is safe: `MEDIA_ROOT=/run/media/pcalnon`, `MEDIA_NAMES=(EBC5-F0A3 DFF3-2782)`, `BACKUP_DIR=Juniper-8.0.0.python` (`:144-146`); `mount_root_for` (`:339-346`) is the single resolver used by both the guard (`:379`) and `target_dir_for` (`:350-354`). Validation (`:236-245`) rejects a relative name with a slash, `.`/`..`, a relative root, a bad `BACKUP_DIR`, and an empty list, exit 2 before any probe (test `test_malformed_settings_exit_2_before_any_probe`, 5 sub-cases). Globbing: no `set -f`, but every expansion of a device-derived variable is double-quoted (`probe1.out` 1b/1c); `read -r -a` never globs — `*` → exit 2 by the regex, `/*` → treated as the literal path, `SKIP /*: /* is not a mount point` (`probe2.out` 2f). Quotes are not special to `read` (`"a b"` → `"a` and `b"` → rejected by the regex); leading/trailing spaces and tabs are stripped/split correctly. `${USER:-$(id -un)}` under `systemd --user`: systemd 259 `systemd.exec(5)` "$USER is set unconditionally … for user services … inherited from the user manager", so runner and scheduler compute the same root. `--dry-run` writes nothing: `:514-546` only echoes and `exit 0`s before the build loop; `probe2.out` 2c/2e show a 0-entry change on the target listing; the PR test `test_dry_run_writes_nothing_and_never_encrypts` snapshots three trees and asserts gpg saw only `--list-keys`. The exposure that remains is DEFECT-1.

**Check 2 — scheduler/runner agreement.** Scheduler `:22` `MEDIA_ROOT="${JUNIPER_BACKUP_MEDIA_ROOT:-/run/media/${USER}}"`, `:23` `BACKUP_DIR="${JUNIPER_BACKUP_DIR:-Juniper-8.0.0.python}"`, `:26` `read -r -a DEVICES <<< "${JUNIPER_BACKUP_DEVICES:-EBC5-F0A3 DFF3-2782}"`; runner `:144` `MEDIA_ROOT="${JUNIPER_BACKUP_MEDIA_ROOT:-/run/media/${USER:-$(id -un)}}"`, `:145` `read -r -a MEDIA_NAMES <<< "${JUNIPER_BACKUP_DEVICES:-EBC5-F0A3 DFF3-2782}"`, `:146` `BACKUP_DIR="${JUNIPER_BACKUP_DIR:-Juniper-8.0.0.python}"`. Names and defaults identical (the test `test_device_list_and_backup_dir_defaults_match_the_scheduler` extracts and compares them). The scheduler does NOT accept the `/` form: `:68` `root="${MEDIA_ROOT}/${dev}"` unconditionally (DEFECT-2 for what follows). `.path` watches the literal `/run/media/pcalnon` (`juniper-backup.path:8`) = the runner's default with `USER=pcalnon`. End to end through the installed copies: `probe3.out` 3a and the PR test `test_due_run_reaches_the_installed_runner_under_the_same_root`.

**Check 3 — failure unit.** `juniper-backup.service:3` carries `OnFailure=juniper-backup-failure.service` (unchanged, as the PR says). Reporter honours `DUPLICATI_STATE_DIR` (`duplicati_backup_failure.bash:28`), appends `${STATE_DIR}/failures.log` (`:49`), reads `${STATE_DIR}/last-run.status` (`:30,39-44`), tails `journalctl --user -u "$1" -n 40` (`:46`), exits 0 (`:62`). "Never succeeded → FAILED": `newest_success_age_days` returns `100000` when no `last-success.*` exists (`scheduled.bash:36-45`), `skip_or_fail` compares `age > STALE_DAYS` (21) → `write_status FAILED …; exit 1` (`:47-54`). Reproduced: `probe3.out` 3b (`stale 100000d`), PR test `test_unplugged_run_is_failed_until_the_first_success_then_skipped`. Installed name `duplicati-backup-failure.bash` (hyphen) from `duplicati_backup_failure.bash` (underscore): deliberate (`install_juniper_backup_timer.bash:81-85`) and identical to the Duplicati installer (`install_duplicati_timer.bash:51-52`) and both units' `ExecStart=`; the host's existing copy is byte-identical ("unchanged" in the dry run). Except DEFECT-3.

**Check 4 — installer.** Read in full (`:1-212`). Copies (never symlinks; `test_installer_never_symlinks`) three scripts with `install -m 0755` into `~/.local/bin` (`:174-180`) and four units with `install -m 0644` into `~/.config/systemd/user` (`:184-190`); `install -d -m 0755` only for an absent dir (`:127-134`). Unit state: `systemctl --user daemon-reload` then `systemctl --user enable --now juniper-backup.timer juniper-backup.path` (`:193,196`) — both units are enabled AND started; `juniper-backup.service` and the failure unit are not enabled (no `[Install]`; correct). Refuses root (`:145-148`), missing sources (`:151-156`), missing systemctl (`:159`), `Linger != yes` (`:162-166`), all before any write. `--dry-run` prints `%q`-quoted commands via `act` (`:101-109`). An existing destination is overwritten by `install` (no backup copy); `copy_state` only reports new/changed/unchanged/replaces-a-symlink (`:112-123`). Ran `bash util/install_juniper_backup_timer.bash --dry-run` against the real HOME: rc 0, 9 `would run` lines, `juniper-backup.bash (new)`, scheduler `(new)`, reporter `(unchanged)`, all four units `(new)`, `ok  Linger=yes for pcalnon`, no systemctl call, nothing written; host listing confirms no tier-2 artefact installed yet and no `~/.local/state/juniper-backup/`. The "Do the OK run FIRST" message is printed by the real run (`:204-206`) only (NIT-4).

**Check 5 — tests and mutations.** `python3 -m unittest -v tests/test_juniper_backup_tier2_lane.py` from the PR worktree: `Ran 34 tests in 2.797s OK`. Hermetic: `PATH = <stubs>:/usr/bin:/bin` with `mountpoint`, `gpg`, `uuidgen`, `bc`, `systemctl`, `loginctl`, `journalctl`, `notify-send` stubbed; `HOME`/`USER` scratch (`USER=b6-tier2-user`); `/run/media/…` appears only in expected-output strings; the mountpoint stub answers from a list and stats nothing, and `-d`/`-w` run only after the stub says mounted (scratch paths). The PR's checker: `CONTROL GREEN` under uutils AND under GNU coreutils (`/usr/bin/gnuinstall` present), `23 mutation(s); 0 problem(s)`, M00 (base runner at `79dc36d5`, which has `MOUNT_NAME="media"`/`USER_NAME="pcalnon"` at `:122-123`) `FAILED (failures=21)` — reproduced (`mutation_check.out`). Hand mutations in scratch copies (`probe5.out`): (a) `mount_root_for` ignores the leading slash → killed by `test_absolute_entry_ignores_the_default_root`, `test_absolute_entry_is_its_own_mount_root`, `test_absolute_entry_is_still_mount_checked` (= checker M04); (b) validation block dropped → killed by `test_malformed_settings_exit_2_before_any_probe` ×5 (= M06); (c) `target_dir_for` pointed at a hard-coded root → killed by 7 tests (`test_env_override_moves_the_root`, `test_backup_dir_override`, `test_due_run_reaches_the_installed_runner_under_the_same_root`, …). For (c) I used the literal `/media-retired/pcalnon/` instead of `/media/pcalnon/` so no subprocess stats under `/media/`; structurally identical (write path decoupled from `mount_root_for`). The checker has no exact guard/write-drift mutation of that shape — M01 moves the DEFAULT root to `/media/pcalnon` (guard and write together) and M00 is the whole base file — but the suite kills the drift form anyway. Also green: `tests/test_ci_test_wiring_drift.py` (14 OK), `util/ad-hoc/2026-09-10_agents_md_test_list_drift.py` (169/169/169, three empty diffs), `shellcheck -S style` 0.11.0 clean on the runner and the installer.

**Check 6 — documentation claims.** `docs/REFERENCE.md` at base `79dc36d5:694`: *"Mount check is the mount root. `mountpoint -q` on `/media/<user>/<MEDIA_NAME>`, not on `BACKUP_DIR`…"* → PR `:702` names `<JUNIPER_BACKUP_MEDIA_ROOT>/<MEDIA_NAME>` / the entry itself; base `:707` SKIP row → PR adds the `findmnt`/`JUNIPER_BACKUP_MEDIA_ROOT` advice and a "First scheduled run reads FAILED" row (`:732`). Confirmed from `scheduled.bash:36-58` that the unplugged-first order reads FAILED. Passages the parent must fix (exact lines, both files untouched by the PR):
- Design `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md:2277` (P3 step 2): *"Install; enable; observe one SKIPPED (unplugged) and one OK (plugged) run"* → OK first, then SKIPPED; and "plugged" must mean BOTH sticks (BLOCKER-1).
- Design `:2306` (AC-10): *"a run with no drive reads `SKIPPED`"* → after the first success; *"produces verified archives on every mounted drive"* → add "and `result=OK` only when every configured drive is mounted".
- Design `:1601` (embedded scheduler header, = `util/juniper-backup-scheduled.bash:11`): *"no configured drive mounted -> SKIPPED, exit 0 (escalates to FAILED after STALE_DAYS)"* → "FAILED when no success is newer than STALE_DAYS, including never".
- Design `:1507-1508` (§7.8 para 1): "treats 'no valid drive mounted' as a benign skip … only when no run has succeeded within STALE_DAYS" — true but should say "including before the first success"; `:1506` "when either drive appears" → see BLOCKER-1.
- Plan `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md:255` (§6.3 step 8): *"one run with no stick mounted (`SKIPPED`), one with a stick mounted (`OK`, verified archives)"* → reverse the order and say both sticks.

**Check 7 — diff hygiene.** Nine files in the diff = nine in the PR body (Changed: runner, ci.yml, REFERENCE.md, AGENTS.md, CHANGELOG.md; Added: installer, failure unit, suite, mutation checker). `AGENTS.md` (168→169 + Last Updated) and `CHANGELOG.md` ([Unreleased] → Fixed, verified under the `## [Unreleased]` heading at `:8/:125`) are conventional here (the count is gated by the drift script). No `#NNNN` in any ADDED line; the body's ml#2113 is MERGED with merge commit `c01c837e` as stated; `2252b3f5`, `5a849222` exist (the latter is HEAD); the only numbers in context lines are pre-existing (`juniper-ml#2046` closed issue, `#1667` closed PR). New files all `100644` (the body says to run the installer with `bash`; correct). No token/key/credential-shaped string in added lines; the only e-mail addresses in the diff are the two pre-existing gpg recipient UIDs in context lines of `util/juniper-backup.bash:193-194` (not added by this PR; location only).

---

## Unverifiable

- **That the owner's sticks mount as `/run/media/pcalnon/EBC5-F0A3` and `/run/media/pcalnon/DFF3-2782` and already hold `Juniper-8.0.0.python`.** Neither is mounted now and `/run/media/` is off-limits. Supporting evidence: udisks names unlabeled volumes by UUID (the live NTFS mount `/run/media/pcalnon/848099D78099CFD2`), and the names worked under `/media/pcalnon/` in August.
- **That `enable --now` on `juniper-backup.timer` (`Persistent=true`, never run) does not fire immediately.** From systemd `timer.c` as I recall it: a persistent timer with no stamp file creates one at start and schedules from the activation time, so the first elapse is Sunday 03:00 (+≤15 min). Cannot start a unit to confirm. `PathChanged=` not triggering at activation is settled by the design's own path.c reading.
- **Real `install(1)` behaviour on the owner's installed symlink-free files** — tested only in scratch (uutils and GNU controls both green).
- **A real (non-dry) run of the PR runner against a mounted drive** — forbidden; the archive pipeline is unchanged by the diff (`tar | gpg`, verify, copy loop) and was exercised only with a gpg stub (probe 6).

## Slips

- Two of my probe-2 cases (2g newline list, 2h `env -i` with HOME) ran the PR runner with the REAL `mountpoint` and the DEFAULT root, so `mountpoint -q /run/media/pcalnon/EBC5-F0A3` and `…/DFF3-2782` were evaluated — a read-only stat on two non-existent paths under `/run/media/`, nothing created, nothing listed. I should have overridden `JUNIPER_BACKUP_MEDIA_ROOT` for those two cases as I did for the others. Also the dry run of probe 2c stat'd/`df`'d `/run/user/1000/systemd` (not a forbidden path; listing unchanged before/after).
- The installer `--dry-run` and the PR suite read `~/.local/bin/*` and `~/.config/systemd/user/*` for `cmp`/listing — no secret file, nothing written.
- No `sudo`, no unit started/stopped/enabled, no `git stash/checkout/commit/push`, no write outside `<scratch>/val/PB/`, no environment variable or credential printed, nothing sent anywhere. Git read-only commands (`cat-file`, `show`, `log`) ran in my own worktree only.

<!-- markdownlint-enable -->

---

## Round 2, the ml#2115 lane

Archived verbatim (21,014 characters, sha256 `26269c74b5de64ec`), lifted from the report file the lane wrote itself, in session 652c1204's scratch directory, on 2026-10-03.

<!-- markdownlint-disable -->

# Validation lane PB — pcalnon/juniper-ml#2115 (B2: one 0600 web credential, `serverstate`/`pause`/`resume`, `--backup-id`, watchdog)

Head `d941f186` (2 commits) on `fix/backup-b2-web-credential-serverstate-backup-id`, base = `origin/main` tip `c01c837e` (#2113). 12 files, +1968/−150, identical to the saved diff. Installed product: `duplicati 2.4.0.0` (`dpkg -l`; `/usr/lib/duplicati/changelog.txt` = `2.4.0.0_stable_2026-09-03`); source cited at that tag's commit `b3e9268c`. Probe scripts and raw outputs: `<scratch>/val/PB/pr2115/` (`cred_probe.{py,out}`, `cli_probe.{py,out}`, `audit_runner.py`, `deploy_probe.{py,out}`, `my_mutations.{py,out}`, `mutation_check.out`, `symbol-report.json`, `src/` = fetched 2.4.0.0 files, `tree/` = scratch copy of the B2 files).

Verdict: **REFUTED on one claim** (the client is not step-10-ready against the installed product: `export` cannot succeed on 2.4.0.0 and the stub encodes the dead path); everything else the brief asked for held under test, with one medium defect in the deployment transition and a handful of nits.

## Findings

### BLOCKER

**B-1. `export <id>` cannot succeed against the installed 2.4.0.0, so the P0 step-10 dry-run the PR says it serves gets an empty `TargetURL` every time — the exact STOP item 3 failure — and the stub encodes the dead path.**

- The product. `GET /api/v1/backup/{id}/export` in 2.4.0.0 has **no** `.RequireAuthorization()`; it requires a non-nullable `[FromQuery] string token` and validates it as a single-operation token: `src/BackupGet.cs:68-82` (`jWTTokenProvider.ReadSingleOperationToken(token)`; `Operation != "export"` → `UnauthorizedException`). The token comes from `POST /api/v1/auth/issuetoken/export` (`Auth.cs:123-137`, Bearer-authorized, returns `{"Token": …}`). The vendor's own 2.4.0.0 CLI does exactly that two-step: `B/src/Duplicati/CommandLine/ServerUtil/Connection.cs:638-648`. The shipped UI too: `/usr/lib/duplicati/webroot/ngax/scripts/services/AppService.js:227-241` (`post("/auth/issuetoken/export")` then `…/export?export-passwords=…&token=`). The installed assembly carries it: `2026-09-22_duplicati_literal_scan.py` FOUND `issuetoken/{operation}` and `ReadSingleOperationToken` in `Duplicati.WebserverCore.dll`.
- The client. `util/ad-hoc/yamaguchi_server_api.py:331` sends `GET …/export?export-passwords=false` with only the Bearer header — no `issuetoken`, no `token=`. A missing required minimal-API query parameter is a **400**, which the repo already recorded on this host: `notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md:1687` — "`yamaguchi_server_api.py export` currently fails `400`". The step-reports record documents the `token=` parameter outright: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-STEP-REPORTS-RECORD.md:1374`. The PR's "endpoints verified" list covers only serverstate/pause/resume.
- Reproduced over real HTTP against a scratch listener shaped like `BackupGet.cs:68-82` (`cli_probe.out`): `export 7` → `rc=1 stdout_bytes=0`, stderr `export 7 failed 400: … Required parameter "string token" was not provided …`; the only requests seen on export paths are two token-less GETs, never `issuetoken`.
- The consequence. Design §8 step 10 (`notes/JUNIPER_2026-09-21_…INTEGRATED-DESIGN.md:2181-2183`) runs `DUPLICATI__REMOTEURL="$(… export <id> | python3 -c 'json.load(sys.stdin)…')"`. Command substitution ignores exit status; empty stdout → `json.load` fails on stdin → `DUPLICATI__REMOTEURL=""` → the guard's `-n` test skips the TargetURL comparison → vacuous pass. The PR's export fix (exit 1, empty stdout — correct in itself) changes nothing here, and the PR body presents the empty-URL case as a transient edge ("can still pass with an empty URL") rather than the only outcome on this product. Plan §6.4 step 11 then requires "must pass **with** a non-empty TargetURL", so the operator following the documented commands is stuck at step 10; AC-2 and AC-13 (`…INTEGRATED-DESIGN.md:2298, 2309`) also run `export <id>`.
- The fixture encodes the defect: `tests/duplicati_api_stub.py` routes `GET /api/v1/backup/7/export` with no token requirement, and `tests/test_yamaguchi_server_api.py:214-223` pins "stdout must be exactly the JSON the design's guard dry-run parses" against it.
- Remedy (either): (a) make `export` do `POST /api/v1/auth/issuetoken/export` → `GET …/export?export-passwords=false&token=<Token>` (the vendor pattern) and make the stub refuse a token-less export; or (b) back `export` with `GET /api/v1/backup/{id}` (`BackupGet.cs:40-42`, Bearer-authorized, same `{Schedule, Backup, DisplayNames}` shape with `Backup.TargetURL` and `Settings`, sensitive fields masked) — which is what `yamaguchi_config_record.py:50` and `yamaguchi_census.py:83` already use successfully. Either way, re-point the design's step 10 / AC-2 / AC-13 text or keep `export` as the name.

### DEFECT

**D-1. Deployment transition: the live timer will run the new script through the old unit and write no durable record until redeploy; the PR's ordering advice makes that window long.**

- The host today (read-only `systemctl --user`): `yamaguchi-watchdog.timer` is active, next fire `Sat 2026-10-03 12:00 CDT`; the loaded unit's `ExecStart` has **no** `--backup-id`; no `yamaguchi-watchdog.service.d/` drop-in exists; the status file's last line is a daily `ALERT UNREACHABLE … login failed (401)` record.
- The unit executes the PRIMARY checkout's script. Once the primary checkout is synced past this merge, the next fire runs the new `yamaguchi_watchdog.py` with no `--backup-id` → argparse usage error, exit 2, **no record** (`record()` is never reached). `tests/test_yamaguchi_watchdog.py:266` pins exactly that ("a usage error writes no record"); `cli_probe.out` `[watchdog no --backup-id] rc=2 stdout=''`. The daily durable signal stops; the only trace is a failed unit. `yamaguchi_reboot_verify.bash:131-143` notices a stale status timestamp only at a reboot.
- The deploy script's stale-unit guard (`yamaguchi_watchdog_deploy.bash:86-89`) forces the order sync → deploy, and the PR body tells the owner to deploy "after this merges and the primary checkout is synced, **and once the credential file exists**" — the credential file is P0 step 9, behind the STOP. That reads as "wait", which leaves the watchdog dark for the whole interval. The deploy script does not need the credential: its first check would record `ALERT UNREACHABLE … does not exist` durably (proven: `[watchdog credential absent] rc=1 … ALERT UNREACHABLE`).
- Remedy: make an absent `--backup-id` take the same durable `JOB_MISSING` path as an empty one (`default=""` instead of `required=True` at `yamaguchi_watchdog.py:296`, adjusting the test at `:266`), and/or state in the PR body and plan §6.4 that `yamaguchi_watchdog_deploy.bash --backup-id <id>` is run immediately after the primary sync, not after step 9. Also: the watchdog's usage exit 2 is indistinguishable from its UNDETERMINED exit 2 — the CLI fixed the analogous collision with 64; the watchdog did not.

### NIT

- **N-1. A symlink is followed, not refused; no owner or parent-directory check.** `read_credential` opens without `O_NOFOLLOW` (`yamaguchi_server_api.py:145`) and judges the target (`cred_probe.out`: `symlink to 0600 target: ACCEPTED`; `symlink to 0640 target: REFUSED mode 0640`); `st_uid` is never compared to `getuid()`; a 0600 file inside a 0777 directory is accepted. The brief expected refusal; the PR documents and pins following (`tests/test_duplicati_web_credential.py:158`). Practical exposure is nil — any target must still be a regular 0600 file with exactly one key line, and a non-root client cannot open another user's 0600 file — so a design choice, not a leak. `O_NOFOLLOW` plus an `st_uid == os.getuid()` check is a two-line hardening if the owner wants the brief's semantics.
- **N-2. `yamaguchi_server_api.py` has no `--base`/`DUPLICATI_URL` override** (`BASE` hard-coded at `:67`), unlike the watchdog (`--base`) and `duplicati_api.py` (`DUPLICATI_URL`). The CLI cannot be exercised against a scratch listener without patching the module (I had to subprocess `python3 -c "…a.BASE=…"`), and any future test that runs the script as a subprocess past argument validation would hit `:8300`.
- **N-3. `log` asks `pagesize=5`; the server clamps to 10** (`src/LogData.cs:71`, `Math.Max(10, Math.Min(500, pagesize))`). Harmless; callers read the first line.
- **N-4. Size TOCTOU in the reader**: `st_size` is checked on the opened descriptor, then `os.read` loops until EOF (`:163-165`); a file growing after `fstat` is read in full. Only the owner can write it; a bound on the loop would close it.
- **N-5. `_unquote` strips one matching outer quote pair** (`:130-134`), so a password whose own first and last characters are the same quote must be double-wrapped. Documented in the module docstring; worth one sentence in the P0 step-9 instruction that writes the file.

## Not refuted

Each item names the instrument that failed to refute it.

1. **Credential reader** (`cred_probe.py`, 30 cases, `cred_probe.out`): a 0600 (and 0400) one-line file is accepted; `0640 0604 0660 0644 0620 0602 0601 0610` each refused with `mode NNNN, owner pcalnon (uid 1000) … chmod 0600`; directory, FIFO (no writer — returned at once, O_NONBLOCK), unix socket (`cannot open … No such device or address`), `/dev/zero` refused as not regular; `64 KiB` accepted, `64 KiB+1` refused unread (`65537 bytes`); zero key lines, two key lines, empty/`''`/whitespace values, empty file, missing file, non-UTF-8 all refused; **no refusal message contains the fixture value** (`leak=False` on all); `exit_code_type=str` so a propagated `CredentialError` exits 1 with the message. `DUPLICATI_WEB_CREDENTIAL_FILE` override works and is itself mode-checked (`override env -> 0640 file: REFUSED`). Retired `DUPLICATI_PW_FILE`/`DUPLICATI_PW_KEY` produce one stderr note each, naming the variable and the credential path, never their values (`retired note leaks value: False`).
2. **Where the password goes**: `grep -rn` over `util/ scripts/ tests/ .github/` finds exactly two consumers of the value — `yamaguchi_server_api.py:200` and `duplicati_api.py:82`, both the login request body. Over real HTTP (`cli_probe.py`, 20+ requests across all verbs and the watchdog) the marker appeared in no URL, query, header, non-login body, stdout or stderr (`leaks: []`, every `leak=False`). Server-side, a failed login returns only "Failed to log in" (`Auth.cs:100-104`). The notify-send child sees neither the value nor a variable carrying it (`test_the_notify_child_gets_no_password`, run).
3. **The verbs against the product** (`src/ServerState.cs`): `GET /serverstate` `:33-37`, `POST /serverstate/pause` `:39-41` (`[FromQuery] string? duration`, `bool? pauseTransfers`), `POST /serverstate/resume` `:43-45` — all `.RequireAuthorization()`. No `duration` → `TimeSpan.Zero` → `liveControls.Pause(false)` = indefinite (`:83-99`; `LiveControls.cs:312-318` sets a zero expiry). Persistence: `Program.cs:1299-1316` writes `PausedUntil` on Paused and nulls it on Running; `ServerSettings.cs:113,231-240` stores it as `paused-until` ticks; `LiveControls.cs:192-208` restores ticks 0 as Paused on `Init()` — so the help text's "survives restarts until resume" is true. Response shape: `ProgramState` is the enum serialized as a **string** (`DuplicatiWebserver.cs:205,229` `JsonStringEnumConverter`; `:227` PascalCase), only `Running`/`Paused` exist (`StatusService.cs:110-117`), `EstimatedPauseEnd` is `DateTime(0, Utc)` for indefinite (`StatusService.cs:58`, `LiveControls.cs:396`) → `0001-01-01T00:00:00Z`, which the client's `startswith("0001-01-01")` reads; `SchedulerQueueIds` are `Tuple<long,string?>` → `{Item1, Item2}` (`ServerStatusDto.cs:33-43`). The pause request the client sends is `POST …/pause` with empty query and empty body (`cli_probe.out`: `('POST', '/api/v1/serverstate/pause', {}, '')`).
4. **Exit codes over real HTTP** (`cli_probe.out`): `serverstate` 0 Running / 2 Paused-indefinite / 2 Paused-timed / 1 unexpected value / 1 on 500 with empty stdout; `pause` 0 with read-back Paused, **1 when the server answers 200 but stays Running** (`not 'Paused'` on stderr); `resume` 0; `export` without id → **64, empty stdout**; `serverstate 7` → 64; `delete 7` without `--yes` → 1 before login; login 401 → 1, `FATAL: login failed (401)` with no password; a failed request → 1 with empty stdout.
5. **Watchdog** (`cli_probe.out`, real HTTP, `--base` to the scratch listener): `OK OK backup=7 newest backup …`; Paused + queue → `ALERT PAUSED_WITH_QUEUE … pause=indefinite` rc=1; empty `--backup-id` → `ALERT JOB_MISSING backup=INVALID` rc=1 (durable, three files); credential 0640 → `ALERT UNREACHABLE … mode 0640` rc=1; credential absent → `ALERT UNREACHABLE … does not exist` rc=1. Keyset paging matches the server: `src/LogData.cs:73-82` is `WHERE ID < @Offset ORDER BY ID DESC LIMIT n`, exactly the watchdog's `offset=<last ID>`.
6. **Mutations.** The PR's `2026-10-03_b2_mutation_check.py` edits tracked files in place, so it ran on a scratch copy (`tree/`): 25/25 killed, every file sha256-restored (`mutation_check.out`). My own 23 (`my_mutations.py`), chosen to differ from the author's: timed-pause exemption, "only my job" queue filter, pause judged after the log scan, age from the newest-any-op entry, non-list queue passing, raw invalid id in the record, one-page scan, refused credential swallowed as OK, group bits ignored, `S_ISREG` dropped, values echoed in a refusal, override env ignored, `duplicati_api` resolving its own path, `_failed` on stdout, contradictory ids accepted, unexpected state exiting 2, `RememberMe` true, password in the login query string, delete logging in before `--yes`, stale-unit guard removed, id regex admitting `0`, drop-in variable renamed, unit comment reverted — **23/23 killed** (`my_mutations.out`). The brief's two required mutations (queue check dropped; freshness from any op) are among the author's and were killed.
7. **Hermeticity.** `audit_runner.py` ran the 83 tests under `sys.addaudithook`: 0 `socket.connect`, 0 opens outside tmp/repo/interpreter, 0 chmod outside tmp; children are the tests' own 5 python runs (credential pointed at an absent temp path; they exit 64/0 before login), the PATH-shadowed `notify-send` stub and `bash -n`. Grep of the four test files for `~`, `$HOME`, `/home/`, `127.0.0.1:8300`, `.config/duplicati-backup`: only a docstring and a literal-value test string. Suites pass on `/usr/bin/python3` 3.14.4 (the unit's interpreter) and the conda 3.14.7, `-W error::ResourceWarning`. `tests.test_ci_test_wiring_drift` 14/14; `2026-09-10_agents_md_test_list_drift.py` 0 drift. `flake8 --max-line-length=512` clean except two E203 (black's slice style; the Pre-commit check passed). `shellcheck -S style` clean; `bash -n` clean.
8. **Call sites.** Every importer uses only `login`/`req` (counted per file): `yamaguchi_retire_tier3.py`, `yamaguchi_edit_setting.py`, `yamaguchi_edit_target.py`, `yamaguchi_edit_sources.py`, `old_archive_purge.py`, `yamaguchi_config_record.py`, `yamaguchi_census.py` (`import yamaguchi_server_api as api`), `yamaguchi_switch_aes.py:25`, `yamaguchi_build_job.py:51` (`from … import login, req`), `duplicati_build_fresh_job.py:44` (`duplicati_api.call`, no `DUPLICATI_PW*`). Bash: `yamaguchi_retire_tier1.bash:54`, `yamaguchi_migrate_copy.bash:56`, `yamaguchi_retire_tier2.bash:75` (`status`), `:98` (`log 2`, positional still accepted), `yamaguchi_reboot_verify.bash:73` (`status`), `yamaguchi_watch.bash:25-29` (`progress`), `yamaguchi_narrow_bind.bash:122-124` (`status` via `runuser -u pcalnon`; an empty result **fails closed**, `:133-134` exit 4). No caller passes a removed flag; none uses a verb whose exit semantics changed (export/abort/delete/import/run/task). All callers now require the new credential file to exist — intended (the stale `.env` value 401s today anyway). The PR's correction stands: the census imports the first client (`yamaguchi_census.py:37`); the second's only importer is `duplicati_build_fresh_job.py`. `util/ad-hoc` has no stdlib-shadowing module names, so the `sys.path.insert(0, …)` the PR adds to `duplicati_api.py` is safe.
9. **Deploy script** (`deploy_probe.py`, PATH restricted to stub `systemctl/loginctl/install/mv/chmod/python3` that record and refuse; HOME nonexistent): `--help` rc=0, no args rc=2, `--backup-id 0|07|2x|abc` rc=2, bare `--backup-id` rc=2, `--bogus` rc=2 — **zero host tools called** in every case. By reading: the argument loop (`:36-69`) precedes `PRIMARY`/`UNIT_DIR` assignment; order is validate → primary-exists (`:77`) → stale-unit grep (`:86`) → linger (`:90`) → `install` units (`:96`) → drop-in written whole and `mv`'d (`:98-101`) → `daemon-reload` → `enable --now` timer → `systemctl --user start` for the first check (`:106`, so the id comes from the drop-in) → prints `Environment` from `systemctl show`. The stale-primary refusal is the literal grep for `--backup-id ${YAMAGUCHI_BACKUP_ID}` in the primary's unit file. Not executed past argument validation.
10. **Unit.** `ExecStart=… --backup-id ${YAMAGUCHI_BACKUP_ID}`; systemd.service(5) on this host: `${FOO}` "always resulting in exactly a single argument", and "variables whose value is not known at expansion time are treated as empty strings" — so no drop-in → one empty argument → the `JOB_MISSING` record proven in item 5. `systemd-analyze --user verify` not re-run (the PR reports it clean).
11. **CodeQL.** Dismissed on this PR: alerts 1006 (`tests/test_duplicati_web_credential.py:162`), 1007 (`:266`), 1008 (`tests/test_yamaguchi_server_api.py:305`), 1009 (`tests/test_yamaguchi_watchdog.py:244`), all `py/overly-permissive-file`, reason "used in tests". Each is `os.chmod(<fixture>, 0o640)` inside a 0700 `TemporaryDirectory`, holding `FIXTURE_MARKER`, in a test asserting the reader **refuses** the file — genuinely test-only. No open alerts on the PR.
12. **Diff hygiene.** Files: the 5 B2 sources, 4 test files, the mutation script, plus `ci.yml`/`docs/REFERENCE.md` test wiring (required by `test_ci_test_wiring_drift`). Added lines contain no `#NNNN` references, no e-mail addresses, no hex/base64 tokens, no secret-shaped assignments (the three markers are labelled fixtures). The PR body's `I-12/I-16/I-39` exist in the plan (`…RECOVERY-PLAN.md:156,160,183`) and B2 is `:220`; alerts 1006-1009 exist. `Allow-Symbol-Loss: func:_password func:main const:PW_FILE` is in the last paragraph of **both** commit bodies; `juniper-symbol-loss-check --base c01c837e --head d941f186` → `fail_count 0`, `WAIVED func:_password, func:main`, `LOST const:PW_FILE` (WARN), `RELOCATED import:re` (WARN) — the waiver names exactly the symbols that need it. Repo squash policy is `COMMIT_MESSAGES`, so the trailer reaches `main`. 21 checks pass, 7 skipped, `mergeStateStatus CLEAN`, no auto-merge armed.

## Unverifiable

- Live behaviour of `pause`/`resume`/`serverstate`/`export` on `127.0.0.1:8300` (prohibited). B-1 and item 3 rest on the release-tag source, the installed DLL literals, the shipped UI and the repo's own recorded 400 — three independent sources agree, but the live 400/401 was not re-observed.
- That this host's systemd expands an unset `${YAMAGUCHI_BACKUP_ID}` to one empty argument: documented in the local man page; no unit was started to observe it.
- The deploy script's host-touching tail (`install`/`daemon-reload`/`enable --now`/`start`/`show`) was never executed.
- `runuser -u pcalnon` HOME semantics for `yamaguchi_narrow_bind.bash` (root) — irrelevant to safety because the script fails closed on an empty status.
- Real `notify-send` delivery (only the stub ran).
- Whether the design's step-10 pipeline is edited to test for an empty URL (plan §6.4 step 11 says it must) — a document change outside this PR.

## Slips

- Two **gitignored** bytecode caches in the PR worktree, `util/ad-hoc/__pycache__/{yamaguchi_server_api,duplicati_api}.cpython-314.pyc`, were regenerated at 07:08 by `cred_probe.py` importing the modules without `PYTHONDONTWRITEBYTECODE` (pre-existing files of the same names, overwritten; no tracked file touched; all other runs set the variable).
- Read-only host look at the live unit to assess D-1: `systemctl --user list-timers` / `cat yamaguchi-watchdog.service`, `ls` of the (absent) drop-in dir, and the last two lines of `~/.local/state/duplicati/server-watchdog.status` (a status line, not on the prohibited list; it carried a 401 error body and no secret). Nothing started, stopped, enabled or installed.
- Network: fetched 8 Duplicati source files from `raw.githubusercontent.com` at the 2.4.0.0 tag commit and used `gh api` read-only on `duplicati/duplicati` and `pcalnon/juniper-ml`; the scratch HTTP listener was on an ephemeral loopback port (asserted `!= 8300`). No credential, e-mail or owner data left the host.
- No `sudo`, no `git stash/checkout/commit/push`; writes confined to `<scratch>/val/PB/pr2115/` and probe-created temp dirs that the probes removed.

<!-- markdownlint-enable -->

---

## The 2026-10-03 handoff's validation

Archived verbatim (21,753 characters, sha256 `56d6aff5a2559616`), lifted from the report file the lane wrote itself, in session 652c1204's scratch directory, on 2026-10-04.

<!-- markdownlint-disable -->

# Validation of `HANDOFF_2026-10-03_backup-phase-b-fold-in-pending.md`

**Verdict: REFUTED — two BLOCKERs.** The file's headline state ("two executor PRs are open and must merge FIRST", "do NOT merge #2115 as it stands") was already false when the file was last written: the owner merged #2114 at 2026-10-03T19:27Z and #2115 at 20:24Z, and the file's mtime is 2026-10-04 14:02 CDT. #2115 merged WITHOUT the lane's fix, so its BLOCKER and DEFECT now live on `main`. Everything else below is a correction to apply before committing; the artifact claims (versions, features, 33 tests, paths) all hold.

Probe time: 2026-10-04 ~14:05–14:40 CDT. Worktree `cached-swinging-summit` at `6a1514e4` (`wip/backup-phase-a`); `origin/main` at `b0598cae`. Read-only throughout (see Slips).

## Findings

### BLOCKER-1 — #2114 and #2115 are MERGED; Remaining item 1 and the "Verify first" expectations describe a state that no longer exists

Evidence (`gh pr view N -R pcalnon/juniper-ml --json number,state,mergeStateStatus,headRefOid,mergeCommit,mergedAt`):

| PR | state | mergedAt | head now | merge commit | handoff says |
| --- | --- | --- | --- | --- | --- |
| #2111 | MERGED | 2026-10-03T10:08:17Z | `a9d84ffa` | `b7840a14` | merged — correct |
| #2113 | MERGED | 2026-10-03T10:43:00Z | `d3792221` | `c01c837e` | merged `c01c837e` — correct |
| #2114 | **MERGED** | **2026-10-03T19:27:36Z** | `66b2bad0` (merge-from-main on top of `0bef9d67`) | `7ec4c7e8` | "CI-green and **unmerged**", "three commits" |
| #2115 | **MERGED** | **2026-10-03T20:24:34Z** | `dd3b8060` (merge-from-main on top of `d941f186`) | `77ef6692` | "**unmerged**", "do NOT merge as it stands" |

Both merged by `pcalnon` (`--json mergedBy`). Merge order was #2114 THEN #2115, the reverse of item 1's "merge #2115 then #2114". `gh pr view 2114 --json commits` lists FOUR commits (`2252b3f5`, `5a849222`, `0bef9d67`, `66b2bad0`), not three; `0bef9d67` is still the last content commit and is signed (`gh api …/commits/0bef9d67` → `verified: true, valid`). The handoff's "after the merge confirm `git diff 0bef9d67 <merge commit> -- <the 10 files>` is empty" — done here: `git diff --stat 0bef9d67 7ec4c7e8 -- <10 files>` is EMPTY (nothing lost). Likewise `git diff --stat dd3b8060 77ef6692 -- <#2115's 12 files>` is empty.

The handoff file itself: `stat` → mtime `2026-10-04 14:02:43 -0500`, ~23 h after both merges. Whatever its authoring time, the committed version must reflect the live state.

Correction: rewrite the opener and item 1. "#2114 and #2115 were merged by the owner on 2026-10-03 (19:27Z `7ec4c7e8`, 20:24Z `77ef6692`); `git diff 0bef9d67 7ec4c7e8 -- <10 files>` and `git diff dd3b8060 77ef6692 -- <12 files>` are both empty (verified 2026-10-04). #2115 merged WITHOUT the lane's fix — see BLOCKER-2." Replace the `gh pr view` lines in "Verify first" with `gh pr view 2114 2115 --json state,mergeCommit` → expect MERGED / `7ec4c7e8`, `77ef6692`. Drop "Two executor PRs are open and must merge FIRST".

### BLOCKER-2 — the #2115 BLOCKER and DEFECT are now ON MAIN, unfixed; the "fix in the B2 branch / resume the B2 agent" path is void

The lane's finding is confirmed in the merged code:

- `git show origin/main:util/ad-hoc/yamaguchi_server_api.py | grep -n -i issuetoken` → no match (rc=1). Same for the B2-worktree copy and this worktree's copy — all three are byte-identical (`diff` → IDENTICAL).
- `export` (main L327–335) calls `req("GET", f"/api/v1/backup/{target}/export?export-passwords=false", tok)`; `req()` (L181–187) adds only `Authorization: Bearer`. No `token=` query parameter anywhere.
- The merged stub/tests encode the token-less route: `tests/test_yamaguchi_server_api.py:216` and `:323` route `GET /api/v1/backup/7/export` → 200 with no token.
- Repo corroboration of the 400: `notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md:1687` on main — "`yamaguchi_server_api.py export` currently fails `400`". The design's P0 step 10 dry-run (worktree L2309) still feeds `DUPLICATI__REMOTEURL="$(python3 util/ad-hoc/yamaguchi_server_api.py export <id> …)"`, so an empty stdout is the vacuous pass the handoff describes.
- The watchdog DEFECT, reproduced from main's copies in scratch (no network reached; the id check precedes login): `python3 yamaguchi_watchdog.py --no-notify --base http://127.0.0.1:1` → `error: the following arguments are required: --backup-id`, **rc=2, no record written**; with `--backup-id ""` → `ALERT JOB_MISSING backup=INVALID`, rc=1, three state files written. Main's `argparse` has `--backup-id` `required=True` (L296). The pre-#2115 unit in this worktree (`util/systemd/yamaguchi-watchdog.service:13`, unmodified since `b7840a14`) is `ExecStart=/usr/bin/python3 /home/pcalnon/…/juniper-ml/util/ad-hoc/yamaguchi_watchdog.py` — no `--backup-id`, and it runs the PRIMARY checkout's script. So once the primary syncs past `77ef6692`, the installed unit exits 2 with no durable record, exactly as the handoff says — but this is now a main defect, not a PR defect.
- No follow-up exists: `gh pr list --state all --search "issuetoken in:title,body"` and `gh issue list --search "issuetoken OR \"single-operation token\""` → empty. The B2 worktree (`agent-ac10a004bba79b35d`) still sits at `d941f186` on the now-merged branch `fix/backup-b2-web-credential-serverstate-backup-id`.

Correction: replace "Fix in the B2 branch … Resume the B2 agent … re-validate narrowly, then merge" with a fix-forward item: "ml#2115 merged with the `export` BLOCKER and the watchdog DEFECT. Open a fix-forward PR from current main (new branch; the B2 branch is merged): (a) `export` issues `POST /api/v1/auth/issuetoken/export` and passes `&token=`, or is backed by the Bearer-authorised `GET /api/v1/backup/{id}` that `yamaguchi_config_record.py:50` / `yamaguchi_census.py:83` use (both verified on main); fix `tests/duplicati_api_stub.py` + `tests/test_yamaguchi_server_api.py:216,323`; (b) `--backup-id` `default=""` so a missing id takes the `JOB_MISSING` path; say 'deploy the unit immediately after the sync'. One narrow lane on the delta, then merge. Until it lands, P0 step 10's guard dry-run must assert a non-empty URL." Keep "Record B2's six job-id-defaulting scripts as residue" — the six are listed in the #2115 body's "Residue for the owner" (`yamaguchi_census.py:78`, `yamaguchi_edit_setting.py:184`, `yamaguchi_edit_sources.py:104`, `yamaguchi_edit_target.py:139`, `yamaguchi_config_record.py:45`, `duplicati_build_fresh_job.py:118`).

### DEFECT-1 — git state is miscounted and mis-classified

`git status --short` → **14** modified tracked files (not 11) and **8** untracked paths. The B2 client copy `util/ad-hoc/yamaguchi_server_api.py` shows as ` M` (tracked, modified — the file existed on main before #2115), not "untracked" as the "Verify first" comment says. The untracked list omits `util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py`, `util/systemd/duplicati-env.contract` and the handoff file itself. Nothing is staged (`git diff --cached --stat` empty). Branch and WIP commit are correct (`wip/backup-phase-a`, `6a1514e4`).

Correction: "14 modified tracked files (incl. the B2 client copy, identical to main's) + 8 untracked: the gate, the test suite, the two P0 helpers, the clearing script, `util/systemd/duplicati-env.contract`, the validation dir and this handoff; nothing staged."

Also state that the branch is 8 commits behind `origin/main` (`git log HEAD..origin/main` → `b0598cae` … `79dc36d5`, including #2113/#2114/#2115). `git diff --stat b7840a14 origin/main -- <the 14 files + AGENTS.md>` shows main moved on exactly five of them: `ci.yml` (+29), `docs/REFERENCE.md` (+71), `AGENTS.md`, the design (+429 = #2113, and HEAD's design is byte-identical to main's — no clobber) and `yamaguchi_server_api.py` (identical to main's — no clobber). None of the six untracked paths exists on main (`git ls-tree origin/main …` empty) — no add/add collision.

### DEFECT-2 — the design and the round-4 record are never named by filename; `D` is undefined

`grep -c INTEGRATED-DESIGN` → 0; `grep -c ROUND-4-RECORD` → 0. Item 2 says "(D's prose)", "`cp <scratch>/design_head.md D` (= `git show HEAD:D`)", "R4's open rows"; line 11 says "the way the round-4 record did"; item 3 says "Assessment edits" without the filename. The convention (Juniper/AGENTS.md § Cross-Project Conventions; juniper-ml AGENTS.md "Name every document…") binds handoffs and requires the filename on every reference when two or more documents are cited.

Correction: define once at the top — "D = `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`; A = `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`; R4 = `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md` (on main via ml#2113)" — and carry the filename on each later reference. Also name `BRIEF_COMMON.md` where "the common brief" appears.

### DEFECT-3 — item 3 lists as owed an assessment edit that is already applied (and names the wrong step)

`git diff origin/main -- <assessment>` shows exactly one content change already in the tree: §6.4 step **4** now reads "the `.blessed.sha256` will list **seven** paths (… snapshot timer — B3 added the timer after this line first said six)". The handoff's '§6.4 step 9 "six" → seven' is (a) done and (b) mislabelled — the phrase "after step 9" sits inside step 4 (A:269); step 9 (A:275) is P0 step 8's placement and never said "six". Correction: delete the item, or re-state it as "done in tree".

The other item-3 edits ARE still owed in the worktree: note 6a still says `systemctl revert` (A:233); B4/B10/B11 still carry `2026-10-0X_` names (A:222, 228, 229).

### DEFECT-4 — the line numbers in `pr2114.md` are `origin/main`'s, not the worktree design's; the successor will edit the wrong passages if it applies them

The handoff's own cites are correct for the worktree design (2,955 lines, unchanged since the freeze — `MANIFEST.sha256` OK): L1916 "Ten paths are named below; nine are landed", L2273 "refuses a non-server database" (lane A NIT-7 → "skips", `WipeEncryption.cs:62-66`, exit 0), L2293 `RestConnection.cs` (lane A NIT-5 → `Library/RestAPI/Database/Connection.cs:766-790`), Appendix B row at L2931, front-matter line 13 (it places P0.5b after steps 1–8 while the P0.5b heading at L2361 says "after P0 step 11").

But the numbers the #2114 lane cites in `pr2114.md` (§7.8 `:1506` "either drive appears", `:1507-1508` "benign", `:1601` scheduler header "no configured drive mounted -> SKIPPED, exit 0", P3 step 2 `:2277` "Install; enable; observe one SKIPPED", AC-10 `:2306`) match `git show origin/main:<design>` (2,817 lines) exactly and in the worktree design land on: L1506 = the guard's `# file:` header, L1601 = `### 7.6 Alerting`, L2277 = Procedure B step 7, L2306 = blank. The worktree positions are **1639, 1640, 1734, 2404, 2431** (offsets +133, +133, +133, +127, +125).

Correction: add to item 2 — "`pr2114.md`'s design line numbers are `origin/main`'s (2,817-line) version; in this worktree's design they are 1639/1640 (§7.8), 1734 (scheduler header), 2404 (P3 step 2), 2431 (AC-10). Lane A/B/C numbers (1916, 2273, 2293, 2931) are the worktree's."

### DEFECT-5 — "archive them verbatim … do not rewrap" — two repo copies are no longer byte-identical to the lanes' originals

`cmp` of `util/ad-hoc/2026-10-03_backup-phase-b-validation/*` against the lanes' originals in `<scratch>/val/PB/`: `A.md`, `B.md`, `pr2115.md`, `BRIEF_COMMON.md`, `PR_BODY.md`, `COMMIT_BODY.txt`, `MANIFEST.sha256` identical; **`C.md` differs (+12 blank lines) and `pr2114.md` differs (+3 blank lines)** — both rewritten at `2026-10-04 14:01:45` (70 ms apart; a formatting pass, no rewrap, no content change). The originals live only on tmpfs (`/tmp`, reaped on reboot).

Correction: either copy the scratch originals back over the two repo files now, or state in the handoff that the repo copies carry inserted blank lines and the record should be built from them. Also: the dir holds **nine** files, not eight (`A.md B.md C.md pr2114.md pr2115.md MANIFEST.sha256 BRIEF_COMMON.md PR_BODY.md COMMIT_BODY.txt`); and `val/PB/…` paths in items 1 and 4 are the scratch dir — point at the repo copies.

### NIT-1 — length

`wc -w` → 1,293 words (1,246 excluding the fenced block) against the procedure's ~1,200 target for the goal statement (`notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md` Step 2). Inside the IQR; trim line 41 if convenient.

### NIT-2 — markdownlint

Pinned binary (`~/.cache/pre-commit/repo2m2h173s/node_env-default/bin/markdownlint --config .markdownlint.yaml <handoff>`) → MD013 on lines 11 (527), 12 (668), 13 (832), 16 (628), 41 (**1,954**) and MD040 (fence at line 47 has no language). NOT a gate: `.pre-commit-config.yaml` excludes `prompts/` from markdownlint, and six handoffs on main already carry >512-char lines. Optional: `util/ad-hoc/2026-10-03_reflow_long_markdown_lines.py` (on main) and ```` ```bash ````.

### NIT-3 — small staleness

- "#2114 … CI 17/17 green, three commits": now four commits; check-runs on `0bef9d67` = 23 success / 5 neutral / 1 skipped (no failure). `d941f186`: 23 success / 5 neutral / 14 skipped.
- "bump AGENTS.md's suite count": main's `AGENTS.md` says "list of 169" while main's `ci.yml` and `docs/REFERENCE.md` run **172** suites (#2114 +1, #2115 +3); the worktree adds one → **173**. No test gates that number (`tests/test_ci_test_wiring_drift.py` gates ci.yml ↔ disk only).
- "`git diff origin/main -- ci.yml docs/REFERENCE.md` holds ONLY your lines": today that diff shows main's +29/+71 lines as removals because the branch is behind; the handoff's "re-apply the suite line on top of main's" is the right instruction — say that `open_signed_pr.py --add` of either whole file from this tree would delete #2114/#2115's lines.

## Not refuted

Each re-derived from the tree or `gh`:

- Phase A merged as ml#2113 `c01c837e`; assessment merged as ml#2111 (`b7840a14`). HEAD's design == `origin/main`'s design (`git diff --stat HEAD origin/main -- <design>` empty); `<scratch>/design_head.md` is byte-identical to `git show HEAD:<design>` (2,817 lines).
- Frozen set: `MANIFEST.sha256` is repo-relative over 18 files; `sha256sum -c` from the repo root → 10 OK (design, assessment, clearing script, ci.yml, REFERENCE.md, snapshot.py, lint/stage scripts, `duplicati.default`, snapshot.service) and 8 changed (wrapper, installer, unit, timer, env contract, tests, hand start, re-key) — exactly the "fold-in half applied" picture.
- **Tests**: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest tests/test_duplicati_wrapper_contract.py` → `Ran 33 tests in 8.788s OK`. flake8 (`--max-line-length=512`) clean on the six Python artifacts; shellcheck clean on the four bash artifacts.
- **Paths**: every named path exists (design, assessment, validation dir, `2026-10-03_rekey_settings_key.bash`, `2026-10-03_rekey_gate.py`, `2026-10-03_password_init_hand_start.bash`, `2026-10-03_clear_stop_and_sync_backup_design.py`, `util/systemd/duplicati-env.contract`, `duplicati.service`, snapshot timer, installer, wrapper, tests, `yamaguchi_server_api.py`, `util/duplicati_backup_failure.bash` (main), `util/safe_merge.py`, `util/open_signed_pr.py`, `util/markdown_structure_delta.py`, lint/stage scripts, `/snap/bin/go`, the pinned markdownlint, the memory file `reference_env_named_repo_file_is_gitignored.md` (linked once from MEMORY.md)). No `duplicati.env` anywhere in the worktree (`find`, excl. `.git`); the installer's `ENV_SRC` and the tests point at `duplicati-env.contract`.
- **Re-key 1.1.0**: `# Version: 1.1.0` (L10); `systemctl revert` appears only in comments/`die` text (L49, 75, 138, 197) — never executed; removal is `rm -f "${DROPIN}"` + `systemctl daemon-reload` (L143–145, and in the trap L162–163); `trap cleanup EXIT` (L179); `FragmentPath` asserted (L148, 194); swap is `cp -p "${CRED}" "${CRED}.old"` then `mv -f "${CRED_NEW}" "${CRED}"` (L248–249); pre-flight `serverstate` → `sys.exit(3 if s.get("ActiveTask") else 0)` (L200–202); `GATE=…/2026-10-03_rekey_gate.py` (L94).
- **Gate**: `COLUMNS` holds five SELECTs — `Option.Value`, `Backup.TargetURL`, `Source.Path`, `ConnectionString.BaseUrl`, `BackupTargetUrl.TargetURL` (L39–43) plus one flag SELECT (L57) = 6 total; empty result is a FAIL; counts only.
- **Hand start 1.1.0**: L9; "the 102 run sets the password only … `encrypted-fields` still False" (L26–33, 62, 177); `ss -ltn` captured, `ss` required (L111–112); edge whitespace refused (L157); exit 200 named (L35, 179); `DUPLICATI_RUN_AS` same-user path (L74, 118–121).
- **Wrapper 2.2.0**: L7; `ENV_EXPORT_ALLOW='^(SETTINGS_ENCRYPTION_KEY|TMPDIR|TZ|LANG|LC_ALL)$'` (L63, no `DUPLICATI__`); `ENV_OPTION_DENY` (L66, applied L129); `REDACT_NAME` (L69, L200); case-insensitive via `${name,,}` (L95).
- **Installer 1.2.0**: L8; `DUPLICATI_INSTALL_PREFIX` (L55); `SECRET_ASSIGN` (L131); `HAZARD_OPTION` (L132); `.drifted-<UTC>` copy-aside (L214); no `.pyc` (L121); dry-run `systemd-analyze verify` on temp copies (L202–203); `env DUPLICATI__REMOTEURL=` hint (L271).
- **Unit/timer**: `duplicati.service:112` comment says `DUPLICATI__DISABLE_UPDATE_CHECK` is honoured whenever not on argv; timer `Documentation=file:///usr/local/lib/duplicati/yamaguchi_server_db_snapshot.py` (main's points at the checkout).
- **Clearing script still stale** (item 2 is correctly owed): `systemctl revert` at L365; "one `mv`" at L25, 199, 365. **Worktree design still stale**: `systemctl\n revert` at L1877–1878 (CLEARED block item 2), L2374; `97 directories` at L2342 (P0.5a item 1); `rekey_gate` 0 mentions; `ml#2115` 0 mentions; §12 note still cites wrapper 2.1.0 / installer 1.1.0 (L2861); AC-6 "unprovable until P2" (L2351, 2427); note 12c at L2858.
- **#2114 amendment on main**: `util/duplicati_backup_failure.bash` is `1.1.0` with `"Backup FAILED: ${UNIT}"` (L64); `util/juniper-backup.bash` requires mount roots strictly under `/mnt`, `/media`, `/run/media` with exit 2 (L115), refuses a newline in `JUNIPER_BACKUP_DEVICES` (L56), one stick = exit 4 PARTIAL → FAILED (L65); `tests/test_juniper_backup_tier2_lane.py` has 43 `def test_`; the mutation script defines 30 mutants.
- **B2 cross-references**: `yamaguchi_config_record.py:50` and `yamaguchi_census.py:83` on main both call `api.req("GET", f"/api/v1/backup/{args.backup_id}", tok)`.
- **Agents/worktrees**: `git worktree list` → `agent-ae6bdb203f422cdfa` at `0bef9d67` [fix/backup-tier2-…], `agent-ac10a004bba79b35d` at `d941f186` [fix/backup-b2-…]; transcripts `agent-ae6bdb203f422cdfa.jsonl`, `agent-a47c9600d78b70e16.jsonl`, `agent-ac10a004bba79b35d.jsonl` exist under `~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-cached-swinging-summit/652c1204-…/subagents/`.
- Reports fail MD013 as stated (A 22, B 17, pr2115 17, pr2114 14, C 12, PR_BODY 5 long lines). All three lanes name the `systemctl revert` BLOCKER (A BLOCKER-1, B BLOCKER-1, C C-1).
- No secret value in the handoff (regex scan for ≥32-hex, `KEY=`, `PASS*=`, `token=`, key headers → none). Verification commands present; branch/WIP stated.

## Unverifiable

- The owner's quoted merge approval ("merge approval granted. let's merge the PRs…") — transcript only; consistent with the owner personally merging #2113/#2114/#2115 on 10-03.
- "Session cut by the usage limit", "Nothing on the host was touched" — no host probe allowed; `C.md`'s Slips record only read-only `systemctl cat/show`.
- The Duplicati 2.4.0.0 source cites (`BackupGet.cs:68-82`, `Auth.cs:123-137`, vendor CLI/UI two-step) — no vendor source tree on this machine (`find … BackupGet.cs` empty) and reading the installed DLL is out of bounds; corroborated by the certification note on main (L1687) and the lane's literal scan.
- That the LIVE installed watchdog unit lacks `--backup-id` — host state; the repo's pre-#2115 unit lacks it, which is what the handoff's premise rests on.
- "CI 17/17" as a required-check count; "30 mutants killed" as a run result (30 mutants defined; the run was not repeated).
- Whether "Resume the B2 agent" is possible from a new session (its transcript exists; its parent session has ended). Moot after BLOCKER-2.

## Slips

- `git fetch origin refs/pull/2115/head` once, to compare `dd3b8060` with its merge commit (writes `FETCH_HEAD` only; no ref, no checkout).
- Ran `origin/main`'s `yamaguchi_watchdog.py` from scratch copies against `http://127.0.0.1:1` with `--no-notify` and `--state-dir ./state` in scratch; both runs exited before any request (argparse / the id check), wrote three files under `<scratch>/wd/state/`, and sent nothing.
- Ran the 33-test suite (hermetic: `DUPLICATI_INSTALL_PREFIX`, `DUPLICATI_SERVER=/bin/true`), markdownlint, flake8 and shellcheck; `sha256sum -c` on the manifest; `gh` read-only (`pr view`, `pr list`, `issue list`, `api …/commits`, `…/check-runs`).
- No `sudo`, no unit or Duplicati binary touched, no secret file read, no environment printed, no edit in the worktree, no `git stash/checkout/commit/push`. The isolation shim refused several compound commands; the equivalents ran as Python scripts in scratch (`paths_check.py`, `design_lines2.py`, `design_grep.py`, `long_lines_main.py`).
- New since the handoff (not its fault, but the successor needs it): fleet PRs #2119 (touches `docs/REFERENCE.md`) and #2121 (touches `ci.yml`, `docs/REFERENCE.md`, `CHANGELOG.md`) opened 2026-10-04 and are OPEN — the same shared files the Phase B PR edits; the owner's sweeper arms open PRs.
- Scratch now also holds `val/PB/HANDOFF_PR_BODY.md` / `HANDOFF_COMMIT_BODY.txt` (written 14:04–14:05 today by the parent session) — the handoff is about to be committed; apply the corrections above first.

<!-- markdownlint-enable -->

---

## Fix-forward lane F1 — product fidelity

Archived verbatim (13,754 characters, sha256 `6b821a6b0a94e961`), lifted from the lane's final message, saved from its transcript by session c9277a65 on 2026-10-04.

<!-- markdownlint-disable -->

# Validation lane F1 -- product fidelity (ml#2115 fix-forward, 663443e8)

**Verdict: REFUTED in part.** The client's wire behaviour matches Duplicati 2.4.0.0 and was not
refuted. The stub's "never-issued token → 401" is false: the product answers 500. There is no BLOCKER.

Source is the tag `v2.4.0.0_stable_2026-09-03` (commit `b3e9268c`), fetched read-only. Scratch dir:
`…/scratchpad/val/F1/`. It holds:
- `src/`: 45 fetched files.
- `model_server.py`: the product model.
- `drive.py` → `drive.out`, `results.json`: 19 end-to-end scenarios.
- `stub_vs_model.py` → `stub_vs_model.out`.
- `guard_excerpt.bash`.
- `tree/`: a `git archive` of 663443e8.
- `tree_mut/`: the stub corrected to the product's status.
- `pr2129.diff`.

## Findings

### BLOCKER

None.

### DEFECT

**D-1. The stub's 401 for a never-issued token is not the product's answer, and a test pins it.**
2.4.0.0 returns **500** for any token it did not sign or cannot validate, including the access token.
It returns 401 only for a validly signed single-operation token minted for a *different* operation.
- **What the product does:**
  - `Duplicati/WebserverCore/Endpoints/V1/Backup/BackupGet.cs:71` calls `ReadSingleOperationToken`.
  - That goes to `Middlewares/JWTProvider.cs:116-126` → `ParseAndValidateToken` at `:174-181`.
  - For a malformed, forged or expired token, or one with the wrong `typ` (the access token is
    `typ=AccessToken`), `JwtSecurityTokenHandler.ValidateToken` or `:180` throws a
    `SecurityToken*Exception`.
  - That exception is neither a `UserReportedHttpException` nor a `UserInformationException`, so
    `DuplicatiWebserver.cs:405-416` answers **500** `{"Error":"An error occurred","Code":500}`.
  - Only `BackupGet.cs:72-73` (`Operation != "export"`) raises `UnauthorizedException`, which is 401
    (`UnauthorizedException.cs:25`, via `:390-398`).
- **Where the change claims otherwise:**
  - `tests/duplicati_api_stub.py:24` (docstring).
  - `:139` returns `401 … # ReadSingleOperationToken, Operation != "export"`. That names the wrong
    branch.
  - `tests/test_yamaguchi_server_api.py:245` asserts `export?token=<access token>` → 401 inside a
    test (`:238`) that says it pins "the fixture's own fidelity".
  - `CHANGELOG.md:143-146` lists "a token it never issued 401" under "The stub enforces the
    product's rule".
- **Reproduction:**
  - `stub_vs_model.out` gives stub/model status pairs:
    - access token as `token=`: 401/500.
    - garbage `token=`: 401/500.
    - empty `token=`: 401/500.
    - a valid `bugreport` token: 401/401.
  - Mutation (`tree_mut/`): I set the stub's unissued-token reply to the product's 500. The suite then
    fails with `FAIL: test_the_stub_refuses_an_export_the_product_refuses … line 245 … 500 != 401`.
- **Impact:** no client behaviour depends on it, because any non-200 exits 1. But the fixture encodes a
  product status that a live 500 contradicts. The test that claims to pin fidelity also blocks anyone
  from correcting it.
- **Remedy:**
  - Stub: answer 500 `{"Error":"An error occurred","Code":500}` for a token the stub did not issue.
  - Stub: answer 401 `{"Error":"Invalid operation","Code":401}` only for a stub-issued token whose
    operation is not `export`. Harvest tokens per operation.
  - Test: change `:245` to expect 500, and add a 401 case that uses a `bugreport` token.
  - Docs: correct `CHANGELOG.md:145` and stub `:24`/`:139`.

**D-2. P0 step 10 still turns every export failure into a vacuous guard pass. The "nothing on stdout"
rationale does not prevent that.**
- **The consumer:** the design's step 10 is a command substitution with no `pipefail` and no check
  (`notes/…INTEGRATED-DESIGN.md:2180-2183`). The guard skips its comparison when the URL is empty
  (`:1403`, `:1421`, `:1429` `if [[ -n "${REMOTE_URL}" ]]`).
- **The client's rationale:** the `_export` docstring (`yamaguchi_server_api.py:338-343`) and help text
  (`:107`) present "a failure prints nothing on stdout" as the guard's protection. But empty stdout
  still becomes `DUPLICATI__REMOTEURL=""`.
- **Reproduction (`drive.out`):** I ran the exact design pipeline against `guard_excerpt.bash` (the
  guard's REMOTEURL logic only) for all 15 failure modes. Every one printed
  `substituted REMOTEURL=[] len=0`, then `TargetURL comparison SKIPPED`, then `guard exit=0`. The
  15 modes:
  - issuetoken: 401, 500, no `Token`, null `Token`.
  - export: 500 bad signature, 500 expired, 401 wrong operation, 404 wrong id.
  - export 200 bodies: non-JSON, empty, no `Backup`.
  - connection reset, login 401, server down.
  - the ml#2115-as-merged client.

  For contrast, a tampered TargetURL on the success path gives `guard exit=5`.
- **Scope:** this predates the change (the earlier B-1 report said the same), and it is narrowed from
  "always" to "on failure". At real runtime `RunScript.cs:368` always sets `DUPLICATI__REMOTEURL`, so
  the runtime guard still compares. What is lost is the dry run's verification value. A mistyped job
  id, which the design warns about, prints `guard exit=0`.
- **Remedy (design, outside this diff):**
  - Capture first:
    `url="$(set -o pipefail; python3 … export <id> | python3 -c '…')" && [ -n "$url" ] || exit 1`.
    Then pass `"$url"`.
  - And/or have the guard refuse an empty `DUPLICATI__REMOTEURL`, which `RunScript.cs:368` makes safe
    at runtime.
  - Reword `_export`'s docstring: empty stdout is hygiene, not the protection.

### NIT

- **N-1.** The help text "Issues a **one-shot** export token" (`:107`) is inaccurate.
  - The token is an HS256 JWT valid for 1 minute plus 5 s skew (`JWTProvider.cs:41,60-65,196`).
  - It is reusable until it expires: the provider is transient and stateless
    (`ServiceCollectionsExtensions.cs:62`) and validation keeps no record of use.
  - While valid it authorises any job's export, including with `export-passwords=true`
    (`BackupGet.cs:68-75`).
  - Say "single-operation" or "short-lived" instead. The client uses it once, at once, so there is no
    functional issue.
- **N-2.** One space was deleted from the `delete <id>` help row (`:108`). Its description now starts
  at column 21; every other row, and origin/main `:95`, use column 22. #2129 kept the alignment.
- **N-3.** Stub response bodies do not match the product's.
  - The stub's token-less 400 body (`:137`) is the RequestDelegateFactory *log* text. The product's
    body is empty in Production, and nothing in the repo sets `ASPNETCORE_ENVIRONMENT`.
  - For an unauthorised issuetoken the product sends an empty 401 plus `WWW-Authenticate: Bearer`;
    the stub sends `{"Error": "Unauthorized"}`.
- **N-4.** Further status mismatches, none exercised by this client. Format is stub/product.
  - The stub answers what the product refuses:
    - expired token (the stub has no clock): 200/500.
    - `export-passwords=maybe`: 200/400.
  - The stub refuses what the product answers, or answers differently:
    - `Token=` key (the product binds case-insensitively): 400/200.
    - `issuetoken/foo`: 404/400.
    - `GET issuetoken/export`: 404/405.
- **N-5.** The client (`:329`) and stub (`:164`) accept a lowercase `token`, and
  `test_export_accepts_a_camelcase_token_field` (`:250`) pins it. 2.4.0.0 cannot emit it
  (`SingleOperationTokenOutputDto.cs:27` plus `PropertyNamingPolicy = null`, `DuplicatiWebserver.cs:203`).
  It is harmless, but the test name implies a product variant that does not exist.
- **N-6.** The success check (`:350`, "`Backup` is a dict") is weaker than its comment ("it has no
  TargetURL"): `{"Backup": {}}` exits 0.
  - The product cannot send that with `export-passwords=false`. An empty TargetURL makes
    `SanitizeTargetUrl` throw (`Backup.cs:135` → `Uri.cs:153-154`), which is a 500.
  - Requiring a non-empty string TargetURL would make the client's contract independent of that
    incidental 500.

## Not refuted

1. **issuetoken call.** `POST /api/v1/auth/issuetoken/{operation}` with no body parameter: only
   `[FromServices]` and `[FromRoute]` (`Auth.cs:123`). The rest of the contract:
   - Bearer is required (`.RequireAuthorization()`, `:137`).
   - Allowed operations are `export|bugreport|websocket`; anything else is 400 (`:125-133`).
   - The response is `SingleOperationTokenOutputDto(Token)` (`:135-136`), serialised PascalCase as
     **`"Token"`** (`DuplicatiWebserver.cs:201-206`).
   - Corroborated by the vendor CLI (`ServerUtil/Connection.cs:640-646` reads `"Token"`) and the
     shipped UI (`ngax/…/AppService.js:229-233`, `resp.data.Token`).
   - Instrument: source plus model. The client sends exactly this (`drive.out`).
2. **export call.** `BackupGet.cs:68`.
   - Parameters:
     - `[FromQuery] string token` is required: non-nullable under `<Nullable>enable</Nullable>`
       (`csproj:7`).
     - `bool? export-passwords` and `string? passphrase` are optional.
   - Access: anonymous. The route has no `RequireAuthorization` (contrast `:42`) and neither does the
     `/api/v1` group (`WebApplicationExtensions.cs:43-45`, filters only). So the client docstring's
     "ignores the Bearer header" holds.
   - Status map:
     - missing token → 400 (binding).
     - invalid token → 500.
     - valid token for another operation → 401.
     - valid token, unknown job → 404 (`:93-94`). The token is checked first (`:71-75`).
   - On 200: `application/octet-stream`, `Content-Disposition` and `Content-Length` are set
     (`:78-81`).
   - The body is System.Text.Json UTF-8 with no BOM, indented and PascalCase (`:312-327`).
     `json.loads` accepts it, and would even accept a BOM (scenario `export_bom`).
3. **POST with no body.** urllib sends `Content-Length: 0`, `Content-Type: application/json` and no
   Transfer-Encoding (`drive.out`: `CL=0 CT=application/json TE=None`). The route binds no body, so
   the server accepts it.
4. **`export-passwords=false`.** `BackupGet.cs:298-301` → `Backup.cs:187-193`.
   - It strips Password-typed options (`Connection.cs:66-91`) from the TargetURL query, the settings,
     special sources and additional targets.
   - The guarded `file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi` round-trips byte-identically
     (`Uri.cs:151-216,262-290,340-343`).
   - `--run-script-before-required` is Path-typed (`RunScript.cs:182`), so it survives and AC-13 can
     diff it. The job `passphrase` is stripped.
   - The client's parameter name matches the server's binding attribute. The in-tree client library
     sends `exportpasswords=` (`DuplicatiServerClient.cs:615`), which the server would ignore.
5. **No side effects.** `GetBackup` reads a fresh object from the database (`Connection.cs:545-567`).
   Neither issuetoken nor export writes anything.
6. **Token hygiene** (19 scenarios, checked in `results.json`):
   - The operation token appears only in the export GET's query. It is never in stdout or stderr
     (tracebacks included), and never in any other request's URL, headers or body.
   - The access token appears in no URL.
   - The password and the archive passphrase are never printed.
   - Server side, the query string is not logged under the default filters
     (`DuplicatiWebserver.cs:311-319`).
7. **End to end.** Run conditions:
   - the frozen client as a subprocess (`/usr/bin/python3` 3.14.4, `BASE` patched).
   - an audit hook refusing port 8300.
   - a 0600 fixture credential and a scratch `HOME`.

   Results:
   - Exactly three requests: login, issuetoken, export.
   - The design's own expression `json.load(sys.stdin)["Backup"]["TargetURL"]` yields
     `file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi` (len 52).
   - The guard excerpt ran, matched, and exited 0.
8. **Failure contract.** All 15 failure modes give rc 1 and 0 stdout bytes.
9. **B-1 reproduced.** The origin/main client gets 400 with an empty body. That matches the repo's
   recorded live 400 (`…DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md:1687`).
10. **Prose that holds:** the client module docstring (`:20-29`), the `_single_operation_token`
    docstring, `CHANGELOG.md:133-142`, and the `docs/REFERENCE.md` entries.
11. **PR #2129.** Same wire flow. This change loses nothing material from it except N-2.
    - It adds the stub's enforcement, the `Backup` check and per-step error labels.
    - It drops #2129's false "Newtonsoft emits `Token`"; the server uses System.Text.Json.
    - #2129's "password not printed" check on the failure path is already covered by the global
      assertion in `run_cli` (`test…:97`).
12. **Suites.** The three B2 suites pass on the scratch archive: 89 tests, OK.

## Unverifiable

- Live behaviour on `:8300`, which was prohibited. Every status above comes from the source and my
  model, corroborated by the vendor CLI, the shipped UI and the recorded live 400. That the installed
  DLL matches the tag rests on an earlier lane's literal scan, which I did not re-run.
- The 400 for a missing token assumes Production (`ThrowOnBadRequest = IsDevelopment()`). Under
  Development it would be a 500.
- An empty `token=` giving 500, and whether filters run on a binding failure, come from my reading of
  ASP.NET Core rather than fetched .NET 10 source.
- The persisted `JWTConfig` could override the 1-minute lifetime; I did not read the live value.
- The real `sudo -u duplicati env …` command and the full guard were not run.
- The CHANGELOG's mutation claim ("33 of 33" killed) was not run; it is outside this lens.

## Slips

- None of mine. All writes went to the scratch dir; HEAD and every tracked file are unchanged.
- Observed: an untracked `util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py` appeared in the
  worktree at 16:25:06 during my run. I did not write it.
- Borderline: I counted proxy variables (`env | grep -c`, result 0). No names or values were printed.

<!-- markdownlint-enable -->

---

## Fix-forward lane F2 — consequences and regressions

Archived verbatim (13,270 characters, sha256 `eee787a730bdbb1c`), lifted from the lane's final message, saved from its transcript by session c9277a65 on 2026-10-04.

<!-- markdownlint-disable -->

# Validation lane F2 -- consequences and regressions (ml#2115 fix-forward, 663443e8)

Verdict: the code change is **NOT REFUTED**. The export flow, the stub, the absent-id record and the
exit 64 all hold under test and against the 2.4.0.0 source, and every host fact checks out. But
handoff item 1 is only partly delivered, one new operator instruction contradicts itself, and the
claim that this supersedes #2129 is not acted on. Totals: 0 BLOCKER, 3 DEFECT, 8 NIT.

## Findings

### BLOCKER

None found.

### DEFECT

**D-1. Item 1's "Residue to record" is not delivered, and the list it names is incomplete at main.**
- `HANDOFF_2026-10-03_backup-phase-b-fold-in-pending.md` item 1 ends "Residue to record: six scripts
  still default to job 2". Nothing in `git diff origin/main 663443e8` records it: no CHANGELOG line,
  no commit-message line, no REFERENCE.md line. The only draft in the worktree,
  `util/ad-hoc/2026-10-04_ml2115_fix_forward/COMMIT_BODY.txt`, doesn't record it either.
- The six cited lines are accurate at main: `yamaguchi_census.py:78`, `yamaguchi_edit_setting.py:184`,
  `yamaguchi_edit_sources.py:104`, `yamaguchi_edit_target.py:139`, `yamaguchi_config_record.py:45`,
  `duplicati_build_fresh_job.py:118` (all under `util/ad-hoc/`).
- The list omits other job-2 sites at main:
  - two more `--backup-id` flags defaulting to 2: `duplicati_source_measure.py:81` and
    `duplicati_size_histogram.py:60`;
  - hard-coded job 2 with no flag: `yamaguchi_switch_aes.py:39,49,53` (GET **and PUT**
    `/api/v1/backup/2`), `yamaguchi_retire_tier3.py:129` and `old_archive_purge.py:209` (gates that
    read job 2's TargetURL), and `yamaguchi_retire_tier2.bash:98` (`... log 2`, the Success gate).
  - After a rebuild these gates either refuse or, if id 2 is reassigned, check the wrong job.
  - `patch_census_derive_dest.py:20,38` are string literals inside a one-shot patcher, not live
    defaults.
- Repro: `grep -rn 'default=["]\?2\|/backup/2\b\|log 2\b' util/ad-hoc/` on the base tree.
- Remedy: record the complete list in the PR body (or the CHANGELOG entry) before merge.

**D-2. The new "deploy immediately, do not wait for the credential" advice contradicts the same
script's instruction for where to get the id.**
- `yamaguchi_watchdog_deploy.bash:30-36` (new) says to run the script right after a sync and
  "Do NOT wait for the web credential". The watchdog docstring (`yamaguchi_watchdog.py:70-71`) and
  the CHANGELOG say the same.
- But the same script says to read the id from `python3 util/ad-hoc/yamaguchi_server_api.py status`
  (`:18-19`, and `usage()` at `:40`). `status` cannot run without that credential: `login()` →
  `read_credential()` → exit 1.
- Repro (socket-guarded, absent scratch path): `status` → `FATAL: web credential file … does not
  exist …`, EXIT=1, 0 connect attempts.
- So an operator following the new advice, while the credential is absent (which the change's own
  prose says is the current state), can't get the id the script requires.
- Remedy: one sentence in the WHEN block saying where the id comes from until P0 step 9. The live
  job is the one every pre-B2 record names (`backup=2`), and the script must be re-run with the
  rebuilt job's id after Procedure B.

**D-3. "Supersedes #2129" is asserted but not acted on, and two open fleet docs PRs carry statements
this change makes false.**
- **#2129** (open draft, MERGEABLE, a Cursor-agent PR) edits both of this change's export files. A
  3-way merge gives 5 conflicting hunks in `tests/test_yamaguchi_server_api.py` and 6 in
  `util/ad-hoc/yamaguchi_server_api.py`. The two cannot be mixed:
  - #2129's suite run against this change's stub: 1 FAIL
    (`test_a_failed_issuetoken_does_not_download_and_leaves_stdout_empty`), because the stub now
    routes issuetoken by default;
  - this change's suite run against #2129's client: 10 FAIL (the issuetoken message format and the
    missing `Backup` check).
  - If the owner's PR sweeper un-drafts #2129 and it lands first, this change needs reworking.
- **#2128** builds its whole argument on the pre-fix state. When merged against this change, these
  statements fall outside the single conflicting hunk and would land silently:
  - "never calls `POST /api/v1/auth/issuetoken/export`" (merged REFERENCE.md :764);
  - "stubs `GET …/export` as HTTP 200" (:776);
  - "`yamaguchi_watchdog.py` require[s] a job id" (:784);
  - the cheatsheet's "`export <id>` cannot succeed" and "The client sends Bearer only", plus the
    overview and quick-start one-liners.
- **#2119**: "`--backup-id` is required and has no default" (merged :703, outside the conflict), and
  its watchdog exit table has no 64.
- `docs/REFERENCE.md` conflicts once with **each** of #2119, #2121, #2124, #2127 and #2128. Checked
  with `git merge-file` on scratch files and agreed by `diff3 -m`. Each fleet PR inserts a row next
  to the two rows this change rewrote. Resolving with "theirs" would bring back "`--backup-id` is
  required" and "25 defects".
- Remedy: close #2129 (superseded) when this PR opens. Close or rewrite #2128. Fix #2119's watchdog
  paragraph and exit table. Resolve the REFERENCE.md conflicts by keeping both sides.

### NIT

- **N-1. The "never printed" guarantee holds only for status 200.**
  `yamaguchi_server_api.py:346` echoes the issuetoken body whenever status ≠ 200. Repro: issuetoken
  201 `{"Token": "probe-op-201"}` → stderr `export 7: issuetoken failed 201: {"Token":
  "probe-op-201"}`, and the same for 202. This contradicts `:28-29` and `:322`. It is latent:
  2.4.0.0 answers 200. Remedy: never echo issuetoken bodies.
- **N-2. The `Backup` check does not check the field its comment names.** `:350` accepts
  `{"Backup": {}}` and `{"Backup": {"TargetURL": ""}}` as success (exit 0). The step-10 dry-run would
  then read `None` or `''`. The comment at `:351-352` justifies the check by "it has no TargetURL".
  Real exports always carry a TargetURL. Remedy: check for a non-empty TargetURL, or reword the
  comment.
- **N-3. "so that 2 can only mean UNDETERMINED" overclaims** (`yamaguchi_watchdog.py:300`).
  `python3` also exits 2 when it can't open the script, which the unit's own NOTE cites
  (`util/systemd/yamaguchi-watchdog.service:23-24`).
- **N-4. The `delete <id>` help line drifted one column.** `yamaguchi_server_api.py:108`: the
  description now starts at column 21; every other verb's starts at 22. It's an unrelated whitespace
  edit in the diff.
- **N-5. Stale wording.** `.github/workflows/ci.yml:1014` still says the watchdog suite pins
  "--backup-id required". `tests/test_yamaguchi_watchdog.py:2,13-14` still say "mandatory job id",
  which is now loose.
- **N-6. One mutation's name is wrong.** The script's mutation at
  `2026-10-03_b2_mutation_check.py:85` is named "…usage error again: exit 2". With `_Parser` still in
  place the mutant exits **64**. It is killed by the right test (`64 != 1`); only the name is wrong.
- **N-7. Gaps in the stub fidelity pin.** `test_the_stub_refuses_an_export_the_product_refuses`
  (`:238-248`) only checks the no-header case. Two of my mutations survive:
  - M3: the issuetoken check accepts *any* Bearer (`duplicati_api_stub.py:132`);
  - M5: the export-path rule narrowed to job 7 only (`:48`).
  - The CHANGELOG's "A test pins that the stub keeps doing so" claims more than the test checks.
- **N-8. Coupling and a behaviour change for manual runs.**
  - `api._Parser` is a private name from a sibling module. A rename would crash `main()` before any
    record is written, though the suite would catch it.
  - A bare manual `yamaguchi_watchdog.py` run now overwrites the live `server-watchdog.status`,
    appends to `server-failures.log` and fires notify-send. Before, it was a no-side-effect usage
    error.

## Not refuted

- **Export flow against the vendor source.** Re-read the 2.4.0.0 `BackupGet.cs` the earlier lane
  saved: `[FromQuery] string token`, `Operation != "export"` → Unauthorized,
  `[FromQuery(Name = "export-passwords")]`. The body is `JsonSerializer.Serialize` with default
  options, so the key is PascalCase `Backup`. `DuplicatiWebserver.cs:201-205` sets
  `PropertyNamingPolicy = null`, so the token field is `Token`.
- **Callers** (grep across util/, scripts/, tests/, .github/, util/systemd/; then read each hit):
  - 10 Python importers; none uses `export`, `_Parser` or the new functions.
  - 6 bash callers, which use only `status`, `log 2` and `progress`.
  - Nothing keys on the watchdog's exit 2: `yamaguchi_reboot_verify.bash:124-128` treats any
    non-zero as the alert, the deploy script's `:114` does the same, and the unit has no
    `SuccessExitStatus`.
  - The new `export 7: issuetoken failed <status>` message has no consumer.
- **`default=""` hides nothing that `required=True` caught.** Socket-guarded run of the frozen script
  with the loaded unit's argv (`--state-dir <scratch> --no-notify` only): exit 1, three files
  written, `ALERT JOB_MISSING backup=INVALID … got 0 character(s) -- redeploy with …`, 0 connect
  attempts. The base script with the same argv: exit 2, nothing written. That matches the journal.
- **`_Parser` reuse.** Base-vs-frozen diff of `--help`, `--bogus`, a bad float and a value-less
  `--backup-id`: only the exit code (2→64) and the usage token `[--backup-id BACKUP_ID]` change. The
  prog name and message text are identical.
- **Host facts** (`systemctl --user show/cat`, a journal window, mtimes, primary reflog,
  `gh pr view 2115`):
  - The loaded unit is the pre-B2 one (no `--backup-id`, empty `DropInPaths`). It ran at 12:00:39
    with `status=2/INVALIDARGUMENT` and the journal shows "the following arguments are required:
    --backup-id".
  - The status file was last written 2026-10-03 12:00:39 (`ALERT UNREACHABLE backup=2`); nothing was
    written on 10-04.
  - ml#2115 merged 20:24Z as `77ef6692`. The primary pulled it at 2026-10-03 17:05:37 CDT; its
    `yamaguchi_watchdog.py` has mtime 17:09:10 and contains `required=True`.
  - Next fire: Mon 2026-10-05 12:00 CDT. If this is merged and the primary synced before then, that
    fire records JOB_MISSING as above, with exit 1 and a notify-send (`/usr/bin/notify-send`; the
    loaded unit passes no `--no-notify`). Otherwise it repeats today's silent exit 2.
- **Suites:** 89/89 OK in the worktree. Mutation script: 33/33 killed in a scratch copy.
  - Each of the eight new mutations fails the pin it names (FAIL, not ERROR), e.g. S1/S2 by the
    stub's 400/401, S6 by the fidelity test alone, S8 by `2 != 64`.
  - Of my 19 mutations, 11 are killed. Survivors: M1, M7 (broader stub token collection) and M10
    (client accepts any 2xx) are equivalent; M3 and M5 are the N-7 gaps; M12 (operation token as
    Bearer on the GET) is harmless; M15 (`default=None`) only changes the message; M14 survives the
    watchdog suite but the client suite kills it.
- **Fleet test PRs** run against this change: #2121 7/7, #2124 11/11, #2127 16/16 + 7/7 pass.
  #2121's CHANGELOG change merges cleanly.
- **Sequence safety:** symbol-loss reports exactly 1 waived symbol
  (`method:MainAndRecordTest.test_backup_id_is_required`) and `import:argparse` as RELOCATED (warning
  only). The docs screen: 0 failures, 1 small-deletion warning. `git log
  --format=%(trailers:key=Allow-Symbol-Loss)` parses the trailer.
- **Item 1 (a) and (b) are delivered**, and with the stub fixed, main's `:323` export call is now
  faithful without edits.
- **Lint and placement:** flake8 E203 is pre-existing and in the repo's ignore list; shellcheck is
  clean; the CHANGELOG entry sits under `[Unreleased]` / `### Fixed`.

## Unverifiable

- Live behaviour of issuetoken and export on :8300 (prohibited).
- `Auth.cs` itself was not in the surviving source copy. The `Token` field rests on the global naming
  policy, the earlier lane's report and #2129's body.
- Whether the operation token is single-use. The help text at `:107` says "one-shot"; the vendor
  calls it single-operation.
- The real 400 body for a missing token; no test depends on it.
- Whether the web-credential file exists now (off-limits). D-2 relies on the change's own statement
  that it doesn't.
- Whether the waiver trailer reaches main; that depends on the squash body at merge.

## Slips

- None against the limits.
- The primary checkout's reflog lines I printed include a committer email address. It stayed in local
  tool output, was not sent anywhere, and is not reproduced here.
- I read the earlier lane's saved vendor sources (another session's scratch), read-only.
- Concurrent writes to the worktree that were not mine:
  - two untracked files, `2026-10-03_clear_stop_and_sync_backup_design.py` and
    `2026-10-04_archive_phase_b_round_reports.py`;
  - `util/ad-hoc/__pycache__/2026-09-22_archive_consensus_reports.cpython-314.pyc` at 16:29. I never
    imported that module; my only worktree run was the three suites at about 16:06 with
    `PYTHONDONTWRITEBYTECODE=1`.
  - HEAD is still `663443e8`.

Probe scripts and outputs are in
`/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/F2/`
(`why_killed.py`/`.out`, `merge_probe.py`, `client_probe.py`, `parser_compare.py`, `guard_run.py`,
`prs/`, `pr2129_vs_frozen.txt`, `rev2129.txt`).

<!-- markdownlint-enable -->

---

## Round 3 — the common brief

Archived verbatim (5,259 characters, sha256 `85ad0209ef91367e`), lifted from the brief session c9277a65 wrote for round 3's lanes on 2026-10-04.

<!-- markdownlint-disable -->

# Phase B, round 3 — common brief (every lane reads this first)

You are one of three independent validation lanes. Do not look for, read or wait on another lane's
output. Your job is to try to prove the artifact WRONG; default to REFUTED when uncertain. Re-derive every
claim from its source of truth — the 2.4.0.0 source at its release tag, the installed product's files, this
host's systemd, git objects, the code itself — never from the documents' own prose.

## What round 3 is

The backup arc's Phase B (assessment §6.2: rows B1, B3, B4, B5, B7, B8, B10) was validated on 2026-10-03 by
**round 2**: three lanes on a frozen set plus one lane on each executor PR (ml#2114, ml#2115). Round 2
refuted things — its BLOCKER, found by all three lanes, was that `systemctl revert duplicati.service` would
delete the installed unit because a dpkg vendor unit exists — so the assessment's own rule applies: "round
N+1 only if round N refutes something, scoped to the delta". **Round 3 validates the fold-in**: every change
made after round 2's frozen set, and whether it fixes what round 2 found without breaking anything else.

## The frozen artifact (do not edit it; read it only)

- Worktree: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/sorted-stargazing-garden`
- Frozen commit: `c3d0e890` (a LOCAL, unpushed commit). Its parent chain: `origin/main` -> the ml#2115
  fix-forward (`e509353e`, PR `ml#2134`) -> this commit. Read with `git show c3d0e890:<path>`,
  `git diff e509353e c3d0e890` (the Phase B change alone) and read-only git only.
- `util/ad-hoc/2026-10-04_backup-phase-b-round3/MANIFEST.sha256` pins every file of the set; check it first
  (`sha256sum -c`, from the worktree root) and report the count.
- Round 2's reports, verbatim: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md`
  in the frozen commit (lanes A, B, C, the ml#2114 and ml#2115 lanes, the 2026-10-04 handoff validation, and the
  ml#2115 fix-forward's lanes F1 and F2). Round 2's frozen hashes, read-only:
  `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/cached-swinging-summit/util/ad-hoc/2026-10-03_backup-phase-b-validation/MANIFEST.sha256`
  — only the HASHES survive: the fold-in edited eight of those files in place in that worktree, so round 2's
  versions of them exist nowhere. Never write there. Judge the fold-in against round 2's FINDINGS and against
  `origin/main`, not against a diff from round 2's files. The assessment's §8 "Round 2" entry lists how each
  finding was folded in — that list is a CLAIM to test, and so is the record's header.

Names: **D** = `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`;
**A** = `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`;
**R4** = `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md`.
D is GENERATED: `git show origin/main:<D>` -> `python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py
--from-repo` -> `python3 util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py` (with
`FIXFWD_PR=ml#2134` in its environment). The clearing script changes prose only, except one declared
fenced block (P0 step 10's guard dry-run).

## Hard limits (violating any of these is worse than missing a finding)

- NEVER start, stop, restart, enable, disable or reload any systemd unit (system or `--user`);
  `systemctl show/cat/list-units/list-timers` and `systemd-analyze verify` on COPIES only. NEVER run any
  Duplicati binary (on this host `duplicati-server --version` STARTS a server) and never contact
  127.0.0.1:8300. No `sudo`.
- NEVER read secret files: `~/.config/duplicati-backup/*`, any `.env` / `*.env`, `/etc/default/duplicati`
  content beyond `stat`, `/etc/credstore`, `/etc/duplicati`, the Duplicati data folders' databases. Never print
  environment variables, tokens or credential files. Never send the owner's email address or any credential to
  an external service. Log reads are COUNT-ONLY (`grep -c`), never values.
- Nothing under `/mnt/Backups/Ubuntu/` is read beyond `stat`, and nothing there is touched.
- Do NOT modify anything in the worktree above or in any other worktree: no edits, no `git
  stash/checkout/switch/commit/reset/push`. Scripts that mutate or install (the mutation checks, the installer,
  the helpers) run only against COPIES in your scratch directory, with every path pointed there.
- Run Python with `PYTHONDONTWRITEBYTECODE=1`.
- Network: read-only GitHub reads of `duplicati/duplicati` (the 2.4.0.0 tag `v2.4.0.0_stable_2026-09-03`) and
  `pcalnon/juniper-ml` only.

## Report format (your final message IS the report; it is archived verbatim in a public repository)

Start with `# Phase B round 3 — lane <X> (<lens>)`, the manifest result, and a one-line verdict. Then
`## Findings` with `### BLOCKER` / `### DEFECT` / `### NIT` — each finding: what is wrong, the evidence
(file:line in the frozen commit, or source file:line at the tag), a reproduction, the remedy. Then
`## Not refuted` (each item names the instrument that failed to refute it), `## Unverifiable`, and `## Slips`
(anything done outside these limits, or "none"). Wrap prose at ~100 characters. No filler.

<!-- markdownlint-enable -->

---

## Round 3, lane A — fold-in fidelity

Archived verbatim (15,343 characters, sha256 `5a85238a8c0e9a57`), lifted from the lane's final message, saved from its transcript by session c9277a65 on 2026-10-04.

<!-- markdownlint-disable -->

# Phase B round 3 — lane A (fold-in fidelity)

**Manifest**: `sha256sum -c util/ad-hoc/2026-10-04_backup-phase-b-round3/MANIFEST.sha256` gives
**26/26 OK**, at the start and again at the end. HEAD is `c3d0e890`.

**Verdict: REFUTED in part.** The BLOCKER's fix holds. Of round 2's 38 lane A/B/C findings, 30 are
FIXED, 7 PARTIAL and 1 FIXED-BUT-WRONG. Six DEFECTs remain:

- the env-file deny list can be bypassed through `--parameters-file`;
- the residue list is not R4's open rows;
- the job-2 residue repeats the "six" that F2 refuted;
- the EXIT trap misreports the decrypt phase;
- two remedies were dropped with no record: A DEFECT-4's pre-flight count and ml#2115 NIT-5.

**Names.** D, A and R4 are as the brief defines them.

| Short name | File |
| --- | --- |
| record | `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md` |
| rekey | `util/ad-hoc/2026-10-03_rekey_settings_key.bash` |
| gate | `util/ad-hoc/2026-10-03_rekey_gate.py` |
| hand start | `util/ad-hoc/2026-10-03_password_init_hand_start.bash` |
| wrapper | `scripts/duplicati-wrapper.bash` |
| installer | `util/install_duplicati_service.bash` |
| contract | `util/systemd/duplicati-env.contract` |
| test | `tests/test_duplicati_wrapper_contract.py` |

Line numbers are the frozen commit's. "Source" means tag `v2.4.0.0_stable_2026-09-03` (`b3e9268c`),
fetched read-only; its paths are relative to `Duplicati/`.

## Findings

### BLOCKER

None.

### DEFECT

**D-1. A DEFECT-2 — FIXED-BUT-WRONG: the env file can still deliver `--disable-db-encryption`.**

- **What is wrong.** wrapper 2.2.0's `ENV_OPTION_DENY` (wrapper:66) refuses 12 names. It does not
  refuse `parameters-file` or its alias `parameterfile` (`Server/Program.cs:49-51`, registered at
  `:1558`).
- **How the server handles it:**
  - it reads that file in-process, after the environment (`:227`, then `:230-237`);
  - it copies every option in the file over whatever argv set (`:1679-1680`).
- **Consequence.** One line in the unblessed `/etc/duplicati/env` naming such a file brings back
  A DEFECT-2's exact outcome:
  - `--disable-db-encryption` satisfies the require flag (`:1249`);
  - the next start rewrites every field in cleartext (`:1275`, `:324`);
  - no "Unknown option" line is logged: the option is removed at `:236`, before validation at
    `:244`;
  - D-6 sees neither file.
- **Worse case.** If the named file sits in the duplicati-writable data folder, the service uid gets
  the very option channel the 0640 root:duplicati mode exists to deny.
- **Same gap elsewhere.** The installer's `HAZARD_OPTION` (install:132) and the test (test:163-171)
  also omit it.
- **Also not refused:**
  - `webservice-enable-forever-token` (honoured at `:658-659`);
  - `webservice-cors-origins` (`:1580`);
  - the alias `webservice-allowedhostnames`. It is inert only while DAEMON_OPTS sets the main name,
    because `:690-692` is an if/else-if.
- **Reproduction** (`val/R3A/wrapprobe.bash`): a scratch copy of the frozen wrapper, run with
  `--print-command` and `DUPLICATI_SERVER=/bin/true`.
  - `--parameters-file=/home/duplicati/.config/Duplicati/p` exits 0 and the path appears on the
    `would exec:` line.
  - `--parameterfile=…` and `--PARAMETERS-FILE=/x` also exit 0.
  - The control, `--disable-db-encryption`, exits 78.
- **Remedy.** Add `parameters-file|parameterfile` to `ENV_OPTION_DENY`, `HAZARD_OPTION`, contract:34-37,
  the test and D's §8 sentence ("refuses security options there"). Better: make the env file's
  `--option` rule an allow-list of tunables.

**D-2. B DEFECT-5 — PARTIAL: §8's "the residue list is the round-4 record's open rows" is false.**

- **What is wrong.** Five R4 rows marked follow-up appear in D's residue paragraph (D:2022-2033)
  neither as open nor as closed. The same claim appears in A:399 and in the clearing script's
  docstring.

| R4 row | What stays open | Where the stale text still is |
| --- | --- | --- |
| R4:90, :143 (B22) | AC-8's undefined "hardening timestamp" | D:2702 itself calls it "a follow-up item" |
| R4:153 | P0 step 8's over-broad file-mode sentence | D:2433-2435, unchanged |
| R4:217 | no route for the 811-volume copy or `PASSPHRASE_OLD` | — |
| R4:231 | §10.2 step 7's pre-rotation set | — |
| R4:351 | sink-c's counting method | — |

- **Note 5b mismatch.** Note 5b (A:191) carries "Appendix C's unapplied corrections"; D's list does
  not.
- **Appendix C is stale.** It still says "None of items 1–10 has been applied". Item 4 is now applied:
  the snapshot script's docstring and the unit's line 5-6 are conditional.
- **Remedy.** List the rows above, then reconcile note 5b and Appendix C.

**D-3. F2 DEFECT-1 not carried into D or A: the job-2 residue is the refuted "six".**

- **What is wrong.** D:2031-2032 and A note 5b (A:192) say "the six ad-hoc job scripts that still
  default to job 2 … pass `--backup-id` or the id explicitly".
- **What F2 and ml#2134 say instead.** F2 DEFECT-1 (in the record) and ml#2134's own PR body list
  eight flag defaults and four hard-coded sites.
- **Re-derived in the scratch tree:**
  - flag defaults: `duplicati_source_measure.py:81` and `duplicati_size_histogram.py:60`, both
    `default=2`;
  - hard-coded: `yamaguchi_switch_aes.py:39/49/53` (GET and **PUT** `/api/v1/backup/2`),
    `yamaguchi_retire_tier3.py:129`, `old_archive_purge.py:209` and `yamaguchi_retire_tier2.bash:98`
    (`log 2`).
- **Consequence.** "Pass `--backup-id`" cannot help the hard-coded four. After Procedure B,
  `switch_aes` would PUT to whichever job holds id 2.
- **Remedy.** Copy ml#2134's list into D and note 5b.

**D-4. B DEFECT-3 — PARTIAL: the trap reports what the script believes, not what is on disk.**

- **What is wrong.** `DB_STATE` stays "under the OLD key (nothing changed yet)" until `wait_started`
  returns (rekey:132, :240). But the rewrite runs before "Server has started" (`Program.cs:324` →
  `:328`).
- **When it bites.** `wait_started` can die during the decrypt start: on the 120 s timeout
  (rekey:128) or on the post-start grep (:121-122). Then:
  - the trap removes the drop-in and reloads (:160-164) but never stops the unit;
  - a process that was started with `--disable-db-encryption` keeps that argv and keeps running;
  - the trap prints "under the OLD key (nothing changed yet) … unit: active … drop-in: absent".
- This is the exit lane B walked: "or the server is up, cleartext, paused".
- **Second problem.** The RECOVERY text (:174-177) says "start the unit" unconditionally. In the
  FragmentPath path that contradicts `:149`'s "do NOT start the unit; re-run the installer first".
- **Remedy:**
  - set `DB_STATE="UNKNOWN — a decrypt start was attempted"` before :238, and likewise before :254;
  - stop the unit in the trap whenever a drop-in was present;
  - make RECOVERY depend on the FragmentPath result.

**D-5. A DEFECT-4 — PARTIAL: the `ConnectionString` pre-flight count was dropped.**

- **What landed.** The gate now covers all five columns (gate:38-44).
- **What did not.** A DEFECT-4's third remedy was "in the pre-flight print the ConnectionString row
  count". It appears nowhere: rekey has 0 matches, D and A mention the table only in lists. §8 does
  not record it as declined.
- **Consequence.** Rows still under the old key fail the gate correctly, but only after both starts,
  with the keys swapped. No re-run can pass either, because the rewrite never touches that table
  (`Library/RestAPI/Database/Connection.cs:131-150`).
- **Remedy.** Count `enc-v1:` rows in `ConnectionString` and `BackupTargetUrl` on the step-1 freeze
  copy (A step 7) or in the pre-flight, and say what to do if the count is non-zero.

**D-6. ml#2115 NIT-5 — NOT FIXED (floor DEFECT, per the brief).**

- **What is wrong.** D step 9 (D:2439) and A step 11 (A:286) say only "write
  `~/.config/duplicati-backup/web-credential` (0600)". Neither gives the format,
  `DUPLICATI_WEB_CREDENTIAL=<password>`.
- **The missing sentence.** The client strips **one** matching outer quote pair. So a password whose
  first and last characters are the same quote must be wrapped once more.
- **Remedy.** Add that sentence to D step 9 and A step 11.

### NIT

- **N-1. Accuracy of the record, A §8 and the CHANGELOG.**
  - Record:41 says lane C "reproduced" the BLOCKER "on a scratch tree". Lane C said it could not
    ("Not demonstrable here without root"), and no lane reproduced it.
  - "54 prose edits and one declared fence edit" (record:58, CHANGELOG): the script applies 54 edits
    in total, one of them the fence edit. That is 52 top-level `edit()` calls, 1 in a loop, and 1
    `fence_edit()`, which calls `edit()`. So there are 53 prose edits.
  - "Everything is applied" (record:52) is false; see D-1 to D-6.
  - A §8 omits four findings that were in fact fixed: B NIT-1 and C N-4, N-5, N-6.
  - The F-lane disposition counts F1 D-1 among "three exceptions" while the same bullet says it is
    applied.
  - The "Code" list omits `util/systemd/duplicati.service`, whose comment changed.
- **N-2. rekey:35-37 contradicts D:1997 and A:234.** It says "the scheduler queues an overdue schedule
  only on resume". At the tag, restoring the pause starts the scheduler anyway:
  - Program.cs:1307 saves `PausedUntil`;
  - that goes through `SetSettings(-2)` (`Connection.cs:430-431`) and `EventPollNotify.cs:121-131`;
  - `WebserverCore/Services/SchedulerService.cs:37-43` calls `Reschedule()`;
  - `Scheduler.cs:121-124` starts the thread, which queues the overdue job (`:396`).

  Safety is unchanged, because `:1305` pauses the queue runner first.
- **N-3. "Sets the password and nothing else" overstates the 102 run.** The phrase appears at D:2019,
  D:2411 and A:238; the hand start's "every OTHER field is still as placed" is at :30-31. The 102 run
  also:
  - upgrades the schema (Program.cs:1148; D:2437 says so itself);
  - runs `FixInvalidBackupId` (:262-263);
  - has `SaveSettings` re-encrypt every password-named server setting (`ServerSettings.cs:209-218`,
    `Connection.cs:1585-1590`).

  Also, the hand start's log line :163 says "on 127.0.0.1:${PORT}", contradicting its own :33-34. A:237
  keeps `--webservice-port=<unused>`.
- **N-4. The exit-code gloss is imprecise.** Wrapper:36 and D:876 say "100 (unhandled exception)".
  Exceptions thrown before `Main`'s `try` end the process unhandled instead of returning 100:
  - the 0700 gate at Program.cs:200;
  - the parameters-file parse at :237.

  `CrashlogHelper.cs:82-85` rethrows them.
- **N-5. C-3 residue.** The installer gate passes `## SETTINGS_ENCRYPTION_KEY=…`,
  `# --webservice-password=…` and `#--settings-encryption-key=…`, all with exit 0
  (`val/R3A/instprobe.bash`). The test's regex at :141 misses the same three.
- **N-6. Two ml#2114 passages unchanged and missing from the residue.** They are D:1749-1751 ("either
  drive appears"; no "including before the first success") and the scheduler header at D:1844.
  P3 step 2, AC-10 and A §6.3 step 8 are fixed.
- **N-7. Partial residues not recorded:**
  - C N-2: the real run still verifies the units only after install and bless (install:267-268);
  - A NIT-6: the `?immutable=1` fallback was not added (the script is byte-identical to round 2's);
  - B DEFECT-4.6: A:239 and I-36 still say `|| true`, while the installer returns 0 (install:156-164);
  - D:2491 and D:2535 still say AC-6 waits for P2;
  - note 12b (D:2977) still records "P0.5b between steps 8 and 9" without noting it moved.
- **N-8. Gate docstring citations (gate:20-22).** The helper lives under `Library/Encryption/`, not
  `Library/Utility/`. The `WipeEncryption.cs` column list is at lines 119-141, not 97-116.

## Not refuted

All 38 lane A/B/C findings are accounted for: 14 + 10 + 14 = 38. Seven of them are in Findings:
A-D2 (D-1), A-D4 (D-5), B-D3 (D-4), B-D5 (D-2), A-N6, B-D4 and C-N2 (N-7), and C-3 (N-5). The other
thirty are FIXED.

| Finding | Where it is now (c3d0e890) | Instrument that failed to refute it |
| --- | --- | --- |
| A-B1, B-B1, C-1 `revert` | rekey:137-150, :193-194, :160-164; D:1991-1996; A:234-236 | systemd.unit(5): `/etc/systemd/system` loads before `/usr/lib/systemd/system`; systemctl(1) revert text matches verbatim; `systemctl show` reports the vendor FragmentPath and empty DropInPaths, so today's pre-flight refuses; scratch dry run |
| A-D1, B-D1 (102 run) | hand start:25-34, :177; A:229, :282; D:2410 | Program.cs:279, :286-288 come before :295 and :324 |
| A-D3 redaction | wrapper:69, :200 | scratch probe; test:179 |
| A-D5, B-B2, C-8 | D:2000-2004 | ml#2134 merged as `f01a438c`; `e509353e`'s backup files are identical to it |
| A-D6 exit 200 | wrapper:35-37; hand start:179 | Program.cs:949, :960 |
| A-N1, N2, N3, N4, N5, N7 | hand start:33, :156; wrapper:95; contract:39-41; D:2429, :2408 | Program.cs:1621; `Connection.cs:766`; `WipeEncryption.cs:87-91` |
| B-D2 no task, one placement | rekey:199-203; D:13, :2037, :2453, :2501; A:222, :286-288 | `ServerStatusDto.cs:33` (nullable tuple); the client prints `ActiveTask` |
| B-N1, B-N2, B-N3 | hand start:53-58; A:271, :283; timer:3-4 | read; B-N3 is accepted by local convention |
| C-2, C-4, C-5, C-6, C-7 | install:213-216, :53-77; test:262-301, :443-483; gate:38-44; rekey:191 | 33 tests pass on a scratch extraction; dry run |
| C N-1, N-3, N-4, N-5, N-6 | install:122; hand start:108-115; test:141, :2-32; rekey:227 | scratch dry runs; tests |

Further checks that failed to refute the artifacts:

- **The five columns are exactly what the server encrypts.** `Encrypt` is called only in
  `Connection.cs`, at :491, :862, :1589, :1656, :1680 and :1794. I scanned all 244 server-side files at
  the tag. The list matches `WipeEncryption.cs:122-141`.
- **Versions** match each file's header and HISTORY: wrapper 2.2.0, installer 1.2.0, re-key 1.1.0,
  hand start 1.1.0. The snapshot script says 1.1.0 in its header and has no HISTORY block.
- **D regenerates byte-identically** (sha256 `890d8a1b…`) and idempotently. `--check` reports
  "0 staged, 14 already current".
- **CI wiring and counts.** The wiring drift test passes 14/14, ci.yml runs 173 suites, and the record's
  severity counts match every report.
- **The host matches D's "96".** Directories under `/usr/lib/duplicati`, excluding `data/`: 96 owned by
  `duplicati`, 21 owned by root.
- **Step 10's fence refuses an empty URL.** Traced: when `$url` is empty the guard is skipped and the
  line prints exit=1.
- **ml#2114's, F1 D-1's, F2 D-2's and F2 N-5's fixes are on `main`.**

## Unverifiable

- Whether the Yamaguchi database has `ConnectionString` rows, which is D-5's reach. Reading it is
  forbidden.
- How long a decrypt start takes under `IOSchedulingClass=idle`, which decides D-4's timeout case.
- The exit code an unhandled .NET exception gives under the unit (N-4).
- D step 6's `--dry-run` WAL flip and its "9 field(s)" figure; the contents of `data/`, which is 0700.

## Slips

None against the limits.

- Read-only `systemctl show`, `ls`, `stat`, and a `find` census of `/usr/lib/duplicati` that pruned
  `data/`.
- GitHub reads only: `gh api` for the tag and its tree, raw fetches from `duplicati/duplicati`, and
  `gh pr view 2134`.
- Writes went only under `val/R3A/`, and Python ran with `PYTHONDONTWRITEBYTECODE=1`.
- Observed, not mine: `COMMIT_BODY_ONLY.txt` and `PR_BODY.md` appeared in the round-3 directory while
  I was running.

<!-- markdownlint-enable -->

---

## Round 3, lane B — procedure consequences

Archived verbatim (24,260 characters, sha256 `df4a03e06e234902`), lifted from the lane's final message, saved from its transcript by session c9277a65 on 2026-10-05, after the lane was resumed from a usage-limit stop.

<!-- markdownlint-disable -->

# Phase B round 3 — lane B (procedure consequences)

This report was finished after a resume. The parent stopped the lane at a usage limit on 2026-10-04 at 22:45Z, and the coordinator resumed it. I judged the frozen commit `c3d0e890` throughout and never touched the worktree. After the resume I read files with `git show c3d0e890:<path>`, because the tree now has unrelated uncommitted edits to four files. As the coordinator asked, I did not re-derive three defects that lanes A and C already reported: the `--parameters-file` deny-list, the EXIT trap, and the ConnectionString count. I did not open their report files.

**Manifest:** 26/26 OK with `sha256sum -c` at the start. After the resume, 26/26 match the blobs of `c3d0e890` (`val/R3B/manifest_vs_commit.py`).

**Verdict:** REFUTED in part. There is no BLOCKER, and I found 4 DEFECTs and 11 NITs. The fold-in's own changes hold: step 8's order, step 10's guard command, P0.5b in place of `resume`, and the snapshot timer. The procedure around them does not:
- The first backup deletes the fileset that AC-4 drills.
- "`resume` fires the overdue backup" depends on a 30-minute startup delay that nobody has read.

Source citations are at `v2.4.0.0_stable_2026-09-03`. "D", "A" and "R4" are as the brief defines them. "CERT" is `notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`.

## Findings

### BLOCKER

None.

### DEFECT

**DEFECT-1 — The first backup after recovery deletes the 2026-09-18 fileset, and 6 to 8 of the 9 old filesets, before AC-4's first drill. Nothing in D or A guards this. (Lead (a): VERIFIED.)**

- **What is wrong.** D step 11 (D:2455) and A §6.4 step 14 (A:291) run AC-3's backup first. AC-4's first drill comes after it, "from `duplicati-20260918T140000Z`" (D:2570), and that drill is the gate for §10.2 step 1 (D:2771, A:291). The first backup is fired by step 10's `resume` on A0, A2 and B (D:2454), or by P0.5b's closing `resume` on A (D:2507-2511). It ends with the job's `retention-policy=1W:1D,1M:1W,1Y:1M,3Y:2M` (D:1591).
- **Evidence.**
  - `BackupHandler.cs:446,837`: after a completed backup, `DeleteHandler` runs whenever a retention policy is set.
  - `DeleteHandler.cs:339-420`: the newest backup is excluded. Within each time frame the *oldest* backup is kept (`:378`), then the next one at least one interval later. Anything older than every frame is deleted (`:420`).
  - `Timeparser.cs:77-79`: W = 7 days, M = 30 days, Y = 365 days.
  - Only dlist files are removed. Only `Files`-type volumes are marked Deleting and returned (`LocalDeleteDatabase.cs:287-317`), then deleted (`DeleteHandler.cs:148-176`). Compaction runs only when `NoAutoCompact` is false (`:204`), and the job sets `--no-auto-compact=true`, so dblock and dindex files stay.
  - The 9 dlists are listed at `ROUND-1-RECORD:58`, and none has been written since (D:172, A:79).
- **Reproduction.** `val/R3B/retention_table.py` ports the remover. It gives these outcomes for a first run on each date (at 14:30Z):

| First run on | Deletes | Keeps (plus the new fileset) |
| --- | --- | --- |
| 10-05 to 10-07 | 6 | 08-25, 09-08, 09-15T20:48 |
| 10-08 to 10-11 | 7 | 08-25, 09-12 |
| 10-12 to 10-14 | 7 | 08-25, 09-15T08:56 |
| 10-15 | 7 | 08-25, 09-15T20:48 |
| 10-16 | 7 | 08-25, 09-16 |
| 10-17 | 7 | 08-25, 09-17T22:13 |
| from 10-18 14:00Z | 8 | 08-25 only |

  The 09-18 fileset survives only a first run between 10-17T22:14Z and 10-18T14:00Z.
- **Consequences.**
  - AC-4's first drill cannot run as written, and neither can §10.2 step 1, which "unblocks the rotation" (A:291).
  - From 10-18, no surviving fileset holds a copy of the server database. The snapshot lane was installed on Aug 30 (unit files dated Aug 30 01:07; CERT:1991), after the 08-25 fileset was taken. So Procedure A0 can never be re-run.
  - The deletions propagate to Dropbox (D:1599).
  - Two statements become false: D §8's "Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved by any step below, with exactly one exception" (D:2080-2081), and A §6.0 item 5 (A:204).
  - Searching D, A, R4 and the Phase B record found no instruction that orders the drill first or suspends retention.
- **Remedy.** Pick one:
  - Run AC-4's pre-recovery drill before the first backup: after step 10's edits and before `resume` or P0.5b, using `duplicati-cli` on a copy of the index, as the A0 scripts already do.
  - Or remove `retention-policy` in step 10's edits and restore it after AC-4, recording both changes.
  - Or re-target AC-4 and §10.2 step 1 at a fileset this first pass keeps.

  In every case, correct the two "nothing is deleted" sentences.

**DEFECT-2 — Between the unit's first start and step 10's `pause` there is a time limit that no step states, reads or sets. Once it lapses, the overdue job starts with no guard (on Procedure A, before the re-key), and "`resume` fires the overdue backup" becomes false.**

- **What is wrong.**
  - D step 10 relies on "once the startup pause lapses" (D:2441).
  - D step 9, which must come first, ends with "confirm the next 12:00 fire reads `OK`" (D:2440). Done in order, that is a wait of up to 24 hours.
  - A step 11 (A:286) puts login, the password change, the credential and retiring S-5 before `pause`.
  - The pause in question is the restored database's `startup-delay`. The record says 30m (CERT:2157, re-tested at :2251-2262, cited at D:140), measured on 08-31 and never re-read. D itself says this value is "not relied on — an unverified pause is not a containment" (D:2322).
- **Evidence.**
  - There is no default delay: `ServerSettings.cs:222-229` returns the stored value, and a new database is seeded with only the `Version` row (`Schema.sql:205`).
  - The server starts Paused only for a stored delay or a persisted `paused-until` (`LiveControls.cs:178-210`).
  - When the delay lapses, the server resumes and reschedules (`Program.cs:1311-1315`). The scheduler thread starts (`Scheduler.cs:123`) and a past-due job is queued (`:306-396`).
  - The schedule's `Time`/`LastRun` are saved when the run finishes, whether it succeeds or fails (`Scheduler.cs:218-232`), so the overdue slot is used up.
  - A first start that comes up Running reschedules at `Program.cs:311`, before `ReWriteAllFieldsIfEncryptionChanged` (`:324`) and before "Server has started" (`:328`).
- **Consequences.**
  - An early run on A0, A or A2 has no `--run-script-before-required` (step 10 adds it) and the old `--aes-version`.
  - It uses `--tempdir=/home/pcalnon/.cache/duplicati-tmp`. That directory exists (`drwxrwxr-x pcalnon`) but is read-only under `ProtectHome=read-only`, so the run fails only by that accident of confinement.
  - On A, the run starts under the 09-18 key before P0.5b. The re-key script's own header says "run it before any backup has started" (`2026-10-03_rekey_settings_key.bash:21-24`).
  - Afterwards, step 10's `resume` and P0.5b's `resume` fire nothing (D:2454, D:2507-2511, re-key `:23-24`), so AC-3 needs a manual `run <id>`.
  - On A2 the early run fails at once, because the TargetURL was wiped. B is covered in DEFECT-3.
- **Relation to round 2.** Round 2 lane B called this window "the unverified `startup-delay` value (pre-existing design risk)" (frozen RECORD:562, :593). Its conclusion that "the scheduler only runs on `resume`" (:567) is true only when the server comes up paused. The fold-in's P0.5b placement now depends on that assumption.
- **Remedy.**
  - In D step 8, while no server runs and with the same `sqlite3` used for the `DBPath` update, set the server setting `paused-until` (an `Option` row with `BackupID` −2) to `0` in the placed database. Do this on A0, A and A2; on B, do it after the hand start and before the first start. Also read `startup-delay` back.
  - Check that the first start reads Paused (`serverstate` exits 2). The server then stays paused until `resume` (`LiveControls.cs:195-199`), and step 10 and P0.5b work as written.
  - Move "confirm the next 12:00 fire" after step 10.

**DEFECT-3 — Procedure B's rebuild tool creates a job that is already overdue, on a fresh index, while the scheduler is running. So D's "run Verify files before any backup" cannot be followed. (Lead (b): the run starts at once — VERIFIED; it deletes files — REFUTED.)**

- **What is wrong.** D step 7 (D:2413-2416) names `util/ad-hoc/yamaguchi_build_job.py` and says only "update its defaults before use". Its frozen defaults are:
  - `Schedule.Time "2026-08-25T18:00:00Z"`, `Repeat 1D` (`:149-151`).
  - `encryption-module gpg` (`:124`), against a destination of AES `.zip.aes` files.
  - One source (`:145`), where AC-2 expects two.
  - The pre-Dropbox target `/mnt/Backups/Ubuntu/Yamaguchi` (`:78`) and the old tempdir (`:83`).
  - Its `login()` (`:51`) needs the web credential, which D creates at step 9 (D:2439), after step 7.
- **Evidence.**
  - The POST ignores any `DBPath` sent in (`BackupListService.cs:47-79`; only `existingdb` sets one, `:111-115`).
  - A new job gets a random index name that does not exist yet (`Connection.cs:818-831`).
  - Any data update triggers a reschedule (`SchedulerService.cs:37-44`).
  - B's fresh database starts Running (see DEFECT-2).
  - So the job starts at the POST: before `DBPath` is re-pointed, before "Verify files" (D:2438), before the guard is added and before `pause`.
- **What the run deletes: nothing.**
  - `PreBackupVerify` calls `VerifyAndClean` (`BackupHandler.cs:266`), which drops to strict mode when the index did not end with active uploads (`FilelistProcessor.cs:285-286`).
  - The cleanup step deletes only files the index tracks as Temporary or Deleting (`:384-400`), and a fresh index tracks none.
  - The 877 files still parse as backup volumes whatever encryption module is set (`VolumeBase.cs:117`). They end up as extra volumes (`:545`), and the run aborts with `ExtraRemoteFiles` (`:175-182`).
  - The error message suggests Repair. Repair on an index that knows no remote volumes renames it and rebuilds it from the destination (`RepairHandler.cs:87-105`); it does not delete either.
- **Consequences.**
  - A backup starts with no guard and uses up the overdue slot. The next run is then at 18:00Z, not 14:00Z.
  - If any default is left unchanged, the job is malformed, for example writing gpg volumes into an AES set.
- **Remedy.**
  - Pause (or set `paused-until=0`, as in DEFECT-2) before the rebuild.
  - POST a future 14:00Z `Schedule.Time`.
  - List every default to change: target, tempdir, `aes`, both sources, the 45 filters, the schedule.
  - Create the web credential before step 7.

**DEFECT-4 — §7.3.6's "root-era UI password is not known" recovery, which D step 9 tells the operator to read first, cannot work on a 2.1+ database. It also contradicts D step 6.**

- **What is wrong.**
  - D:1493-1501 says the fix is `DELETE FROM Option WHERE BackupID=-2 AND Name IN ('server-passphrase','server-passphrase-salt',…)` followed by a hand start with `--webservice-password-init`.
  - It also says A2 returns exit code 103.
  - D step 9 (D:2439) sends the operator to this paragraph.
- **Evidence.**
  - `UpgradePasswordToKBDF` returns immediately when `pbkdf-config` is set (`ServerSettings.cs:365-366`).
  - `--webservice-password-init` works only when the password is marked autogenerated; otherwise it returns 103 (`Program.cs:679-686`).
  - The A0 and A databases carry `pbkdf-config` (A:278, "`pbkdf-config` in cleartext"; A note 5a, A:189: `server-passphrase` is null since 2.1). Deleting the `server-passphrase` rows therefore changes nothing.
  - The result is exit 103. The hand start then dies saying "set the password through the UI" (`2026-10-03_password_init_hand_start.bash:178`), which is impossible if the password is unknown.
  - Sign-in tokens are disabled, so the server is unreachable.
  - For A2, D step 6 (D:2409-2410) says the opposite: `pbkdf-config` is wiped, so the hand start returns 102.
- **Remedy.** Delete `pbkdf-config` as well. `UpgradePasswordToKBDF` then mints a random password and sets `autogenerated-passphrase=True` (`ServerSettings.cs:369-386`), and the hand start returns 102. Remove A2 from the paragraph. This is pre-existing (it is on `origin/main`), and neither A nor the Phase B record mentions it.

### NIT

- **N-1 — The installer's printed guard check is the hand-typed form D calls pointless.**
  - `install_duplicati_service.bash:270-275` prints `env DUPLICATI__REMOTEURL=file:///…/Yamaguchi … guard`, says it "must be 0 BEFORE the job is resumed", and only then prints `systemctl start`.
  - D step 10 (D:2453) says a hand-typed URL makes the check pointless.
  - Round 2 lane B's DEFECT-5 (frozen RECORD:537) named two halves of this problem. The fold-in fixed only the `env` half, yet it records round-4 B14 as closed (D:2023-2024, A:398).
  - Remedy: print D step 10's export-based command, after the start.
- **N-2 — The residue list leaves out round-4 B22.**
  - R4 keeps B22 open (R4:90, :717, :791): AC-8's "hardening timestamp" is undefined.
  - AC-8 still says "since the hardening timestamp" (D:2574).
  - Neither D's residue (D:2022-2033) nor A's note 5b (A:191) lists it, while A §8 says "the residue list is the round-4 record's open rows" (A:400).
- **N-3 — "The six ad-hoc job scripts that still default to job 2" (D:2031-2032; A:191) is really twelve.**
  - The fix-forward commit `e509353e` lists 8 with a default of 2 and 4 hard-coded, and a grep of the frozen tree confirms all 12.
  - Defaults of 2: `yamaguchi_census.py:78`, `yamaguchi_edit_setting.py:184`, `yamaguchi_edit_sources.py:104`, `yamaguchi_edit_target.py:139`, `yamaguchi_config_record.py:45`, `duplicati_build_fresh_job.py:118`, `duplicati_source_measure.py:81`, `duplicati_size_histogram.py:60`.
  - Hard-coded, with no way to pass an id: `yamaguchi_switch_aes.py:39/49/53`, `yamaguchi_retire_tier3.py:129`, `old_archive_purge.py:209`, `yamaguchi_retire_tier2.bash:98`. For these four, the advice "pass the id explicitly" cannot be followed.
- **N-4 — D's P2 step 4 (D:2536) redeploys the watchdog without `--backup-id`. (Lead (c): VERIFIED.)**
  - The frozen deploy script refuses this with exit 2 before touching anything (`yamaguchi_watchdog_deploy.bash:73-77`). It fails safe, but the step cannot run as written.
  - A §6.5 item 2 (A:296), D step 9 (D:2440) and §7.6 (D:1713) all include the id.
- **N-5 — Procedure A2's re-entry is out of order and names the wrong tool.**
  - D:2412 says to re-enter TargetURL and passphrase "through the web UI or `util/ad-hoc/yamaguchi_build_job.py` … Then step 8".
  - No server runs before step 8, so neither route works at that point.
  - The build tool creates a *new* job and refuses an existing name (`:160-170`). With `--allow-duplicate` it would create a second job on the same destination.
  - Remedy: re-enter the values after step 9's login, in the UI.
- **N-6 — Step 13's re-encryption check (A:290) names no tool and does not say to copy the `-wal`/`-shm` files.**
  - SQLite writes VACUUM's result through the WAL; the default auto-checkpoint is 1,000 pages, and the database is about 240 KiB.
  - So on A0 a copy of the main file alone can still be the placed cleartext database. That gives a false "not encrypted" reading and leaves a new cleartext copy of the passphrase wherever the copy lands.
  - Remedy: name `2026-10-03_rekey_gate.py`, copy the database together with its `-wal`/`-shm` files (as the re-key script does at `:263-268`), keep the copy outside `/home/pcalnon`, and shred it afterwards.
- **N-7 — Step 10's command misbehaves if `<id>` is pasted unsubstituted into an interactive shell.**
  - Lines 1–2 are a syntax error and are discarded, so lines 3–5 run with whatever `url` the session already holds.
  - Reproduced in scratch with a stale hand-typed value: the guard ran and printed `guard exit=0`.
  - Remedy: put `id=…` on its own first line and check it, or `unset url` first.
- **N-8 — The re-key script's timer check misses some states.** It checks only `is-enabled != enabled` (re-key `:196`). A timer that is started but not enabled, or is `enabled-runtime`, passes. It should also require the timer to be inactive.
- **N-9 — B's step order in D is circular and partly wrong.**
  - D step 7 runs the hand start "after step 8's installer", but step 8 writes the key after the installer (D:2435-2436).
  - Step 8 says B created its folder "in step 7", while step 7 refers back to step 8.
  - The hand start refuses a missing key file (`:104-107`), so this fails safe. A §6.4 steps 9→10 give the correct order.
- **N-10 — The key-write command is not safe to run twice.**
  - D step 8's `openssl … | sudo tee /etc/credstore/duplicati-settings-key` (D:2435-2436) and the installer's NOTE (`:260-262`) overwrite an existing key without checking.
  - Re-running step 8 after the hand start or after a first start leaves the database under a key that is no longer on disk; the escrowed copy is the only one left.
  - Remedy: guard the write with `test ! -e` or `set -o noclobber`.
- **N-11 — The re-key script's EXIT trap misreports one window. This may duplicate lanes A and C's EXIT-trap finding.**
  - `cleanup()` never stops the unit, and `DB_STATE` is updated only after `wait_started` returns (`:237-241`, `:253-256`).
  - So if a slow decrypt start times out, the script reports "under the OLD key (nothing changed yet)" while the server, still starting with `--disable-db-encryption` on its command line, goes on to decrypt.
  - Here that is harmless: the snapshot timer is disabled, and either a re-run or a restart recovers.

## Not refuted

- **Step 10's command fails safe on every export failure** (stub matrix in `val/R3B/guardtest`: export failing, garbage output, no URL, no `Backup` object → REFUSE, guard not run, `guard exit=1`). The assignment always overwrites a stale `url`, even when export fails, and `&&`/`||` precedence is correct.
- **P0.5b in place of `resume`, with the scheduler already paused:**
  - A second pause does no harm (`LiveControls.cs:312-330`) and is saved across restarts (`Program.cs:1308`).
  - Every start inside the script comes up Paused (`:195-199`), so nothing is rescheduled.
  - The pre-flight check reads `ActiveTask` from the client's own output (`yamaguchi_server_api.py:285-288`), with `|| true` around `serverstate`'s exit 2.
  - `--help | grep -q` passes under `pipefail` (2,747 bytes, 10 of 10 runs).
- **D step 8's preconditions:**
  - `sqlite3` is installed in Phase C, and `DBPath` is not one of the encrypted columns.
  - The installer's `systemd-analyze verify` passes on a scratch copy with the credential file absent (exit 0), so "installer, then key" works.
  - The key path is the same in the unit's `LoadCredential=`, the installer, the re-key script and the hand start.
  - On A2, all of the hand start's own checks are met at that point.
  - The hand start exits at `Program.cs:286`, before the web server and the scheduler start. Its usage reporter cannot transmit first, because it waits 20 s (`EventProcessor.cs`).
  - The forensics check as `duplicati` is possible (`/home/pcalnon` is 0755) and opens only a read-only copy.
- **Snapshot timer:** it is disabled at step 1 on every path. The installer enables nothing, the re-key script refuses if the timer is enabled, and step 13 is the only place it is re-enabled; D:2005-2008, D:2489, re-key `:71`, the installer's `:277-278` and A:272/290 all agree. The product VACUUMs after re-encrypting (`Connection.cs:148-150`), and the snapshot reads through the WAL.
- **Counts, placements and consistency:**
  - `find` gives 96 duplicati-owned directories outside `data/` (including the top) and 21 others, matching the "96".
  - The installer and A both name 7 blessed paths.
  - P0.5b's placement is stated the same way at D:13, D:2039-2042, D:2454, D:2501-2512 and D:2516, A:287-289, and re-key `:21-24`.
  - `systemctl revert` appears only as "never".
  - The hand start's verification is described the same way at D:2410, A:237-238, A:283-284 and hand start `:25-34`/`:177`.
  - The leftover "97" and "between steps 8 and 9" are in §12 history rows only.
- **A reboot mid-session is harmless:** after Phase C step 1, the enabled vendor unit points at `/home/duplicati/bin/…`, which no longer exists, so it fails with 203 and starts nothing.

### State per path (A §6.4 step numbers, D steps in brackets)

| Step | A0 | A | A2 | B |
| --- | --- | --- | --- | --- |
| 1 | Timer disabled and inactive; its last-run stamp is kept | same | same | same |
| 5–6 (D 1–2) | Freeze 0700; `.recovery` copy of the encrypted root-DB snapshot (inside the Source); vendor unit stopped; old folder moved aside 0700 | same | same | same |
| 7 (D 3–6) | Cleartext schema-11 database restored outside `/home/pcalnon` | Folder = `cp -a` of the root `data/` (under the 09-18 key, index plus siblings) | Wiped copy (TargetURL, passphrase and `pbkdf-config` empty; `startup-delay` kept) | — |
| 9 (D 8) | Cleartext DB 0600 in a 0700 folder; index main file only; `DBPath` absolute; 7 files blessed; the `/etc` unit is the one loaded; timer still disabled; new key 0600 | DB under the old key; old key at `…-key`, new at `…-key.new` | as A0 | Installer creates an empty folder; index and key in place |
| 10 (D 6–8) | First start: schema 11→12, re-encrypt and VACUUM before "Server has started"; Paused for 30m if stored, otherwise an early run that fails on the tempdir | Starts under the old key, no rewrite; same clock | Hand start 102 (encrypted-fields stays False), first start encrypts; any early run fails (no TargetURL) | Hand start 102; first start Running, no job |
| 11 (D 9–10) | Pause (removes the delay); edits queue the job while held; guard dry-run; `resume` → first backup → retention removes 6–8 dlists (DEFECT-1) | Same up to the dry-run | as A0, after re-entering values in the UI | Rebuild POST runs at once on a fresh index → `ExtraRemoteFiles`, nothing deleted, overdue slot used up |
| 12 (P0.5b) | — | Pause; decrypt start (Paused); copy-then-`mv` key swap; `rm` drop-in and daemon-reload; encrypt start; gate; VACUUM; `resume` → first backup and retention | — | — |
| 13 | Copy needs `-wal`/`-shm` (N-6); `enable --now` fires at once and copies an encrypted database | after P0.5b | same | same |
| 14 (D 11) | AC-4's drill from 09-18 fails unless the first run fell in 10-17T22:14Z–10-18T14:00Z | same | same | same |

## Unverifiable

- **The restored databases' actual `startup-delay` and `paused-until` values** (it needs reading the database). There is no 09-17 14:00Z fileset (`ROUND-1-RECORD:58`), so the 09-17 server may have been paused. If so, a persisted pause would close DEFECT-2's window for A0.
- **Whether `/usr/lib/duplicati/data/BMXWPAOGLP.sqlite` has a `-wal` or `-journal` file beside it.** D step 8 copies only the main file and does not name its source. Phase C step 6's listing would settle it.
- **Whether a first start that comes up Running could have its VACUUM race an early run's reads** (`Program.cs:311` against `:324`).
- **How long Dropbox keeps the pruned dlists:** 30 days or 180 days depending on the plan (D:2778).

## Slips

- **Writes to the shell history file.** Two `bash -i` runs of the guard test (in scratch) appended their piped input to `~/.bash_history`. Five lines match my markers. They are stub commands only (`url=file:///typed/by/hand`, the test block with `export 2`/`<id>` and `bash ./bin/guard.bash`), with no secret. I left them in place rather than edit the owner's history a second time. This was a write outside the scratch directory.
- **Python without `PYTHONDONTWRITEBYTECODE=1`.** Several `python3 -c` one-liners (stdlib `json` over the fetched tree listing in scratch) ran without that variable. They imported no local module, so no bytecode was written.
- **Network.** GitHub reads were limited to `duplicati/duplicati` at the tag (the tree listing through `gh api`, and raw files).
- **Host metadata reads.** `stat` of `/home/pcalnon/.cache/duplicati-tmp`, and a read-only `find` over `/usr/lib/duplicati` that skipped `data/`. Metadata only.
- **Otherwise none.** No unit was started, stopped or reloaded; no Duplicati binary ran; no `sudo`; no secret file was read; nothing under `/mnt/Backups/Ubuntu` was read or touched; all output went to `val/R3B/`; other lanes' files were not opened.

<!-- markdownlint-enable -->

---

## Round 3, lane C — run the things

Archived verbatim (16,733 characters, sha256 `3130711439a648bc`), lifted from the lane's final message, saved from its transcript by session c9277a65 on 2026-10-04.

<!-- markdownlint-disable -->

# Phase B round 3 — lane C (run the things)

**Manifest:** `sha256sum -c` gives 26/26 OK in the worktree, and 26/26 again in a `git archive c3d0e890` tree in
scratch. HEAD is unchanged at `c3d0e890`. I made no tracked change. During the lane the parent session added
`COMMIT_BODY_ONLY.txt` and `PR_BODY.md` as untracked files; they are not mine.

**Verdict:** REFUTED in part. These hold:
- the reproduction of D;
- the clearing script's gates;
- every dry run;
- the wrapper and installer fixes.

These are refuted:
- the re-key's EXIT trap misreports the state, and gives the wrong recovery command, in four states;
- round 2's A DEFECT-4 is only half folded in;
- the env-file deny list can be bypassed through `--parameters-file`;
- the re-key dry-run test fails on the owner's host once the installer has run;
- 14 of 25 mutants of the fold-in's new code survive the suites.

Every full output is under `$S` = `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C/`.

## Findings

### BLOCKER

None found.

### DEFECT

**D-1. The re-key's EXIT trap prints a fixed recovery block that is wrong or contradictory in four states.**
The script's header (`util/ad-hoc/2026-10-03_rekey_settings_key.bash:64-69`) promises "the command for each
case". In practice:
- `DB_STATE` and `KEYS_STATE` are hard-coded at `:132-133`.
- `KEYS_STATE` is only updated after the swap block (`:251`).
- The RECOVERY text (`:174-177`) is the same in every state.

I drove the real script's non-dry-run path on a copy with its four host paths rewritten into scratch, using
stubbed `systemctl`, `journalctl`, `sudo`, `id`, `chown` and `stat`, and fake keys
(`$S/t4_rekey_trap.txt`, `$S/t4_rerun.txt`):
- **Re-run after a post-swap failure (R1).** The pre-flight dies with
  `FATAL: credential file missing or empty: …key.new`. The trap then prints
  `STATE: database under the OLD key (nothing changed yet); keys: old key at …key, new key at …key.new`.
  On disk the truth is `CRED=NEW`, `CRED.new` absent, `CRED.old=OLD`, and the database is cleartext. The printed
  branch "If it is still under the OLD key and the keys were swapped, move …key.old back to …key before any
  start" then looks like the one that applies. Following it overwrites the only on-host copy of the new key and
  undoes the re-key.
- **FragmentPath turns out to be the vendor unit after the drop-in removal (F3).**
  `FATAL: systemd now loads /usr/lib/systemd/system/duplicati.service … do NOT start the unit` is followed by
  `RECOVERY: if the database is cleartext …, leave the NEW key at …key and start the unit`. Starting the unit in
  that state is round 2's BLOCKER outcome.
- **The stop after the decrypt start fails (F2).** The STATE line reads `CLEARTEXT … keys: old key at …key, new key at …key.new; unit: active`. The trap
  still says "leave the NEW key at …key", but the new key is not there. It also says nothing about the unit
  still running with `--disable-db-encryption` in its argv.
- **The gate fails (F4, and the ConnectionString case in D-2).** Three lines after
  `GATE FAILED … do not shred the old key`, the trap prints
  `STATE: database under the NEW key (the encrypt start completed; not yet verified by the gate)`.

There is also a narrower slip. If `mv` succeeds and the following `chmod` fails (F2b), the trap reports the keys
as unswapped although they were swapped. And every pre-flight refusal, even "not root", prints ABORTED plus the
full RECOVERY block for a run that changed nothing.

**Remedy:** work out the state at trap time from the files themselves (`CRED`, `CRED.old` and `CRED_NEW`,
compared by hash), plus a STARTED flag set after `pause`. Print only the branch that applies. Let a
DO_NOT_START flag set by `:149` suppress "start the unit". In the gate-failure state, print the gate's counts.

**D-2. Round 2's A DEFECT-4 is half folded in, and §8 does not list it.**
- The record (`notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md:331`) asks for the
  gate to scan `ConnectionString` and for the pre-flight to "print the `ConnectionString` row count so the
  operator knows whether the product gap can bite".
- Only the gate half was built. The pre-flight (`:181-206`) has no such count.
- The assessment's "Folded in" list (`:391-401`) never names A DEFECT-4. The record's claim "Everything is
  applied" (`:52`) is therefore refuted.

The gap is real at the tag: `ReWriteAllFieldsIfEncryptionChanged` (`Duplicati/Library/RestAPI/Database/Connection.cs:131-153`) never rewrites `ConnectionString`.

**Reproduction** (`$S/t4_rerun.txt`, case X_F4_conn): all five columns under the new key, except one
`ConnectionString` row under the old key. Result:
`encrypted-fields=True blobs=4 under-this-key=3 under-another-key=1 [… ConnectionString.BaseUrl=1 …]`, exit 1.
This happens after both starts and the swap, with the scheduler left Paused, and no re-run can ever pass.

**Remedy:** count the `enc-v1:` blobs in `ConnectionString` on a copy before the first stop, and refuse (or
document a procedure) when the count is non-zero. List A DEFECT-4 in §8.

**D-3. `--parameters-file` gets past the env-file deny list.**
`ENV_OPTION_DENY` (`scripts/duplicati-wrapper.bash:66`) and the installer's `HAZARD_OPTION`
(`util/install_duplicati_service.bash:132`) do not name it. At the tag, the server reads options from that file
(`Program.cs:49-51`, alias `parameterfile`) and merges them OVER argv (`:230-237`, `:1680`:
`options[keyvalue.Key] = keyvalue.Value`). It does so before evaluating `disableDbEncryption` (`:1159-1160`),
and that flag satisfies `require` (`:1249`).

**Reproduction** (`$S/t3_wrapper_paramfile.txt`):
- the line `--disable-db-encryption` gets wrapper exit 78;
- `--parameters-file=/home/duplicati/.config/Duplicati/opts.txt`, `--parameterfile=…` and `--PARAMETERS-FILE=/tmp/x`
  each get exit 0 and reach argv;
- the installer accepts the same line in the contract (exit 0, no REFUSING line).

So `--disable-db-encryption` in the referenced file would decrypt the database with no "Unknown option" trace.
Exploiting it needs root, because `/etc/duplicati/env` is root-owned.

**Remedy:** add `parameters-file|parameterfile` to both lists, and pin them in the suite.

**D-4. The re-key dry-run test is not hermetic, and fails on the owner's host after assessment step 9.**
- The suite's docstring says no test "touches /etc"
  (`tests/test_duplicati_wrapper_contract.py:30-32`).
- But `INSTALLED_UNIT` has no override (`:84`), and `:221-227` read the installed unit when it is readable.
- The test asserts that `"DRY RUN:"` is printed (`tests/…:483`).

`$S/t2_rekey_test_hermetic.txt` shows the result:
- as on CI, with no installed unit: `'DRY RUN:' printed=True`;
- with the installed unit readable: `'DRY RUN:' printed=False -> … would FAIL`.

This is the same class as round 2's C-4, and the fold-in claimed C-4 fixed.

**Remedy:** add a `REKEY_INSTALLED_UNIT` override (test use only) and set it in the test.

**D-5. The suites never execute the fold-in's real code paths: 14 of 25 mutants survive.**
Results are in `$S/t6_mutations.txt`. Each mutant was applied to one scratch tree and restored byte-for-byte
afterwards. The suites killed M07, M10-M15, M17, M18, M21 and M25. They let these survive:
- **M01-M06, M08, M09 (re-key):** the real `rm` of the drop-in, the FragmentPath assertion, the ActiveTask
  check, `mv` turned into `cp`, the inverted swap, the trap's own drop-in removal, the drop-in's `ExecStart=`
  reset line, and the trap's `DONE` guard.
- **M16:** pre-auth-tokens removed from the deny list.
- **M19:** the installer's `grep -i` dropped.
- **M20:** the drift copy-aside replaced by `true`.
- **M22-M24:** the clearing script's fence gate, its `ml#FIXFWD` check, and its `FENCE_EDITS` declaration.

Why they survive:
- The re-key runs only `--dry-run` plus three text greps, and its "would:" strings are separate literals from
  the commands they describe.
- The deny-list test covers 6 of the 12 entries.
- The installer is only ever run with `--dry-run`, so the `act` description string is all that is checked.
  `docs/REFERENCE.md:3203` nonetheless says the suite "pins" that "drift is … kept as evidence".
- No CI test exercises the clearing script. M22 even survives the brief's own `cmp` check; only an attack
  catches it.

My own instruments killed all 25 (the stub harness, the gate matrix, probes, the installer's non-dry-run
harness, and the attacks). Round 2's C N-5 was closed by deleting the docstring's claim, not by adding a test.

**Remedy:** turn `$S/bin/t4_rekey_trap.py` and `$S/bin/t3_installer_real.bash` into suite tests.

### NIT

- **N-1. The password-init dry run says "gates passed" without running the whitespace gate.** The gate exists
  only in the real path (`util/ad-hoc/2026-10-03_password_init_hand_start.bash:156`, which comes after the
  dry-run exit at `:146`). Case e (`$S/t3_pwinit.txt`) gets dry-run exit 0; the real run gets exit 1.
- **N-2. A carriage return in a key file means two different keys.** The wrapper keeps the CR
  (`$(<file)`, `:154`), and the server uses the environment value as-is (`Program.cs:986-987`). The hand start
  and the gate read the file in Python text mode, which drops it. Evidence (`$S/t3_cr_key.txt`): the unit's key
  is `len=21 ends_with_CR=True`, while the params key is `len=20`. The hand start is not refused, and the gate
  fails a correctly re-keyed database (`under-another-key=2`). **Remedy:** read with `newline=""` and refuse `\r`.
- **N-3. The `FIXFWD_PR` gate refuses only the exact placeholder** (`:80`, `:840`). With `FIXFWD_PR=""` the
  output says `Since  an absent id` and the gate does not refuse it; `ml#fixfwd` is written too
  (`$S/gate_attacks.txt`, cases d2 and d4). **Remedy:** validate against `^ml#[0-9]+$`.
- **N-4. The re-key's timer check is `is-enabled != "enabled"` only (`:196`).** Three states pass it:
  `enabled-runtime`, `linked`, and disabled-but-active (exit 0, 3 starts; `$S/t4_timer_state.txt`). The real
  hazard is an active timer, and `is-active` is never queried.
- **N-5. The dry run claims something happened.** Its output includes
  "decrypt start done: every field is now CLEARTEXT on disk" (`:241` is not guarded by the dry-run flag).
- **N-6. The installer's contract gate is narrower than the wrapper.** Five lines pass the installer (exit 0)
  and then get exit 78 at the next start: reset-jwt-config, interface, server-datafolder, allowed-hostnames and
  `DUPLICATI__*` (`$S/t3_installer.txt`, case vii). **Remedy:** gate on the wrapper itself (`--print-command`).
- **N-7. A first install over files that were never blessed overwrites them without a copy-aside**
  (`:171`, then `:211-218`; case ii prints `'would: cp -p' count: 0`). On this host that would hit
  `/etc/default/duplicati` (duplicati:duplicati, 404 B, 09-20) and both snapshot units from 08-30 (checked by
  stat only).
- **N-8. Every snapshot run against a WAL-mode source leaves two root-owned 0644 files in the destination:**
  `…sqlite.tmp-shm` (32 KiB) and `.tmp-wal` (0 B). Only the main file is renamed by `os.replace` (`:118-150`;
  `$S/t3_snapshot_wal.txt`, case b). They then ride along in the backup.
- **N-9. The edit count is off by one in three places.** "54 prose edits and one declared fence edit" appears at
  the record `:58`, `RECORD_HEADER.md.in:58` and `CHANGELOG.md:154`. The script actually has 54 edits, one of
  which is the fence edit: 53 prose plus 1 fence.
- **N-10. §8's list omits five round-2 findings:** B NIT-1, C N-4, C N-5 and C N-6 (all four fixed in the
  artifacts), plus A DEFECT-4 (see D-2).
- **N-11. Two kinds of change on main would pass the clearing script without warning.**
  - If main rewords all five phase markers, the edit reports `ALREADY phase markers: held` and all five
    reworded markers are written (`:399-403`; `$S/t1_empty_new.txt`).
  - If main adds an item inside the STOP block, it is dropped and the output is still sha256 `890d8a1b`
    (`:410-414`; `$S/t1_stop_block_drift.txt`).
- **N-12. The gate skips an `enc-v1` value stored as a SQLite BLOB** (`str(bytes)`, `:62`). The product never
  writes one.
- **N-13. The snapshot unit's `ReadWritePaths=` has no `-` prefix** (`yamaguchi-server-db-snapshot.service:37`).
  Per systemd.exec(5), only a `-`-prefixed path is "ignored when [it does] not exist", so on a fresh host the
  unit fails until the directory exists. The directory exists here (stat). Not run.

## Not refuted

- **Reproduction** (cmp):
  - origin/main's D (blob `c71c8df0`, identical in cf711cf4 and e509353e) → `--from-repo` (5 rewritten,
    9 identical, 1 retag) → clearing script (`applied 54 … 17 line(s) wrapped; fenced blocks: 20, 1 changed as declared`) gives sha256 `890d8a1b…`, identical to the frozen D;
  - a second clearing run reports 54 ALREADY and the hash is unchanged;
  - `--check` reports `0 staged, 14 already current`.
- **Gate attacks:** every case refused with the hash unchanged (`$S/gate_attacks.txt`):
  - anchor failures (missing in D, altered in the script, present twice) exit 1;
  - strays into a fenced block exit 3: inside a tagged block, a second change inside the declared fence, an
    added fence, an indented added fence, a removed fence line;
  - the declared text differing from the applied text, in either direction, exits 3;
  - main having changed the declared fence exits 1;
  - a fence edit whose anchor is in prose exits 3;
  - `FIXFWD_PR=ml#FIXFWD` exits 3;
  - the width, stale-phrase and non-idempotent gates all refuse.
- **The fence block run against stubs** (`$S/fence_snippet.txt`): a failed export, an absent `Backup`, or an
  empty URL each gives REFUSE, the guard does not run, and the output is `guard exit=1`. A null URL becomes
  `None`, and the guard then fails.
- **Suites:** 137 tests, OK.
- **Installer:** the dry runs (first install, drift, behaviour change, kept env) and a non-dry-run with stubs on a
  scratch prefix all behaved as claimed. The drift copy-aside keeps the bytes (sha16 `e166161c` on both sides).
  No systemctl call was made in any dry run.
- **Re-key:**
  - the dry run prints 22 "would:" lines in order, with no `revert` and no stub called;
  - S0 (success) ends with CRED=NEW, `.new` absent, `.old` shredded, the drop-in absent, and 0 reverts across
    13 cases;
  - ActiveTask, vendor-FragmentPath and enabled-timer refusals all fire before the pause;
  - `systemd-analyze verify` on a copy accepts the drop-in, and refuses it without the reset line.
- **Password-init refusals:** a 0640 secret, a 0750 folder, a port in use (IPv4 and IPv6), and `ss` missing are
  all refused. With a stub server, the parameters file is 0600, has two lines, and is shredded on 102, 103, 200
  and 1.
- **Gate matrix** (`$S/t5_gate.txt`): 21 of 22 cases as expected. One blob under another key in any column
  fails; so do a job option, one of three Source rows, a truncated blob, a False, absent, NULL or `" True"`
  flag, and zero blobs. The blob layout matches the tag's source (`EncryptedFieldHelper.cs:51-59, 157-175`).
- **Snapshot (§7.7):** after a clean close, a run against the read-only directory fails closed (exit 1, "attempt
  to write a readonly database"). With the writer running it succeeds.
- **Linter and screen:**
  - the snapshot linter reports 14 blocks, 0 failures;
  - the archiver's own screen finds 0 hits in the record or its header;
  - the owner's email address occurs 0 times in the record.

## Unverifiable

- Whether the Yamaguchi database has `ConnectionString` rows (D-2's reach): reading the database is forbidden.
- Real systemd and Duplicati behaviour in the two starts: that needs root or the binary.
- A true read-only mount for N-8 and §7.7: user namespaces are refused here (`uid_map: Operation not permitted`),
  so I simulated it with file permissions instead.
- N-13 on a fresh host: that needs starting a unit.

## Slips

- One wrapper probe passed DAEMON_OPTS's real `--server-datafolder`, so its preflight ran `-d`, `-w` and
  `stat %U` on `/home/duplicati/.config/Duplicati` (metadata only). I reran it against a scratch folder.
- The unmodified re-key dry run, as the task asked, tested `-e` on `/etc/credstore/*` (EACCES) and `-r` on the
  absent installed unit.
- I ran `stat` only on `/etc/default/duplicati`, both installed snapshot units, the vendor unit,
  `/usr/bin/duplicati-server` and the snapshot destination.
- My harness scripts live in `$S/bin` under /tmp, as the brief requires. That is not the `util/ad-hoc/` location
  the ecosystem convention asks for, and they will be lost when /tmp is cleared.
- GitHub reads were limited to the duplicati tag: the tree and six files.

<!-- markdownlint-enable -->

---

## The 2026-10-04 handoff's validation

Archived verbatim (24,978 characters, sha256 `fa9a35a10cbb2301`), lifted from the lane's final message, saved from its transcript by session c9277a65 on 2026-10-05.

<!-- markdownlint-disable -->

# Validation of HANDOFF_2026-10-04_backup-phase-b-round3-fold-in-pending.md and its archive package

**Verdict: REFUTED in part.** The handoff gets the facts right about ml#2134, the frozen commit, D's
reproduction, round 3's findings and the watchdog, and it carries every round-3 DEFECT. Two things fail.
Its first verify step returns 24, not 26, on the two files this package rewrote. And it loses round-3
lane B's unreported leads about damage to the sole copy, while scoping round 4 to the delta. Totals:
2 BLOCKER, 4 DEFECT, 10 NIT.

**Names used in this report:**

- **handoff**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-04_backup-phase-b-round3-fold-in-pending.md`.
- **predecessor**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_backup-phase-b-fold-in-pending.md` (on `main`).
- **record**: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md` (working tree).
- **header**: `util/ad-hoc/2026-10-04_backup-phase-b-round3/RECORD_HEADER.md.in`.
- **R3**: the directory `util/ad-hoc/2026-10-04_backup-phase-b-round3/`.
- **D, A, R4**: as the handoff defines them.

## Findings

### BLOCKER

**B-1. "Verify first" gives 24, not 26, and the two failures are the files this package rewrote.**

- `sha256sum -c R3/MANIFEST.sha256 | grep -c ': OK'` returns **24**. The two FAILED lines are the record
  and the header.
  - In `c3d0e890` their blobs hash to the manifest's values (`ec03e61c…`, `dee7b915…`).
  - The working-tree copies hash to `49bb88b3…` and `02628837…`. They are the 2026-10-05 08:14 rewrite
    that the archive PR lands.
- **Why a wrong number is a BLOCKER.** The handoff says three things: `c3d0e890` is frozen, "Every
  Phase B file is in that commit", and the 26 files are "pinned by R3/MANIFEST.sha256". The usual repair
  for a failed pin is to restore the two files from `c3d0e890`. That brings back the header text
  round 3 refuted:
  - "Everything is applied";
  - lane C "reproduced on a scratch tree";
  - "54 prose edits and one declared fence edit".

  Step 3 then re-assembles the record from that header, and `util/open_signed_pr.py` sends whole files.
  The Phase B PR would overwrite `main`'s corrected record.
- **Two more gaps in the block.**
  - It has no `git status` expectation. The handoff procedure requires one, and the predecessor had one.
  - Nothing checks that the record reached `main`. Today it has not: `git ls-tree origin/main` lists
    none of these: the record, the header, `util/ad-hoc/2026-10-04_archive_phase_b_round_reports.py`,
    `util/ad-hoc/2026-10-04_save_subagent_report.py` and `util/ad-hoc/2026-10-04_wip_worktree_delta.py`.
- **Correction** (replace the manifest line, and add two):

  ```
  sha256sum -c util/ad-hoc/2026-10-04_backup-phase-b-round3/MANIFEST.sha256 | grep -c ': OK'   # 24: the record and RECORD_HEADER.md.in FAIL by design (rewritten after the freeze, landed on main) -- never restore them from c3d0e890
  git status --short   # M: the record, RECORD_HEADER.md.in, the INDEX, the consolidated handoff; ??: this handoff, R3's reports/drafts/HANDOFF_PR_BODY.md/r3c-harness/, util/ad-hoc/2026-10-04_ml2115_fix_forward/; nothing staged. The M files and this handoff equal main's copies
  git ls-tree --name-only origin/main -- notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md   # non-empty once the archive PR merged
  ```

  In Completed, add: "the manifest pins round 3's copies of the record and its header; `main`'s are newer".

**B-2. Round-3 lane B's in-flight work is lost, and a round 4 "on the delta" would not recover it.**

- **Lane B was not silent.** The parent session c9277a65 got the usage-limit grace notice at 22:45:01Z
  and stopped lane B with `TaskStop` at 22:45:46Z.
  - The transcript is `agent-a54a66d16fc004c83.jsonl`, under session c9277a65's `subagents/` directory.
    It has 616 records and holds 37 interim notes, but no report.
  - The notes below are lane B's own words. They are leads, not verified findings.
- **Lead 1: the first post-recovery backup may delete the 09-18 fileset.**
  - Lane B: "every successful backup ends with the retention pass"; "Every plausible first-run date prunes
    the 09-18 and 09-17 filesets (only a ±12 h window around 10-18 keeps 09-18)".
  - Lane B: "AC-4's first drill targets `duplicati-20260918T140000Z` and D step 11 sequences it after the
    first backup"; "This ordering predates the fold-in (present on `origin/main`)".
  - Its last note: "No prior record raised it. Let me confirm the delete step removes only dlists under
    `--no-auto-compact=true` … before I state the damage precisely."
  - I checked the inputs, and they hold:
    - D:117 sets `retention-policy=1W:1D,1M:1W,1Y:1M,3Y:2M`;
    - D:2441 says the job "will start on its own once the startup pause lapses";
    - D:2455 orders step 11 as AC-3's backup, then AC-4's drills;
    - D:2818-2819 says AC-4's first drill uses the 09-18 fileset and that drill is §10.2 step 1's gate;
    - D has no retention guard before that drill.
- **Lead 2: Procedure B's rebuild tool.**
  - Lane B: "Procedure B's named rebuild tool sets `Schedule.Time` to 2026-08-25T18:00Z (past) and
    `encryption-module=gpg`". This is true of `util/ad-hoc/yamaguchi_build_job.py:124` and `:149-151`.
    D:2413 names that tool and says "update its defaults before use".
  - Lane B: "`PreBackupVerify` calls `VerifyRemoteListAsync` in VerifyAndClean mode. With Procedure B's
    fresh empty index facing 877 populated files, I must know exactly what 'clean' deletes."
- **Lead 3: smaller open questions.**
  - Lane B: "§7.3.6's remedy is pre-existing and unaddressed by A or round 2".
  - Lane B asked whether the watchdog deploy takes `--backup-id` "as D step 9 writes it". D:2440 does
    pass it. But D:2536 (P2 step 4, also on `main`) says "redeploy with
    `util/ad-hoc/yamaguchi_watchdog_deploy.bash`" with no id, and the script refuses a call without one.
- **What the handoff says.** Only that lane B "left no report", and step 2 scopes round 4 "on the delta".
  Lane B's prompt asked for an end-to-end walk of A0, A, A2 and B, looking for damage to the sole copy.
  Its leads are pre-existing on `main`, outside any fold-in delta, so a lane scoped to the delta has no
  reason to look there.
- **Correction.**
  - Before the archive PR lands, send `SendMessage` to `a54a66d16fc004c83` from session c9277a65. The
    memory's rule is to resume a stopped lane rather than relaunch it, which also keeps it independent.
    Archive its report with `util/ad-hoc/2026-10-04_save_subagent_report.py`.
  - If that fails, add these to Remaining item 2:
    - the transcript's location, found by session id (it moves to
      `~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-…/subagents/`
      when the session ends);
    - the leads above, marked UNVERIFIED;
    - "the consequence lane walks the whole procedure at the round-4 head, as lane B's round-3 prompt
      did, not only the delta".
  - In the record's round-3 table, say that lane B's interim notes exist.

### DEFECT

**D-1. The AGENTS.md suite count to write is 174, not 173.**

- `origin/main`'s `ci.yml` already invokes 173 suites, and `main` has 173 `tests/test_*.py` files.
  #2139 added `tests/test_recurrence_env_preflight.py`.
- `c3d0e890`'s 173 suites lack that one and add `tests/test_duplicati_wrapper_contract.py`. Rebuilt on
  `main`, Phase B has 174. `main`'s AGENTS.md still says 169, at its line 69.
- **Correction**: "suite count = `main`'s at rebuild + 1 (174 today). Any fleet PR that lands first and
  adds a suite raises it (#2138 adds two; #2140 and #2159 add one each). Confirm with
  `util/ad-hoc/2026-09-10_agents_md_test_list_drift.py`."

**D-2. The standing limits were narrowed.**

- The predecessor said "nothing under `/mnt/Backups/Ubuntu/` moved". Round 3's brief
  (`R3/BRIEF_COMMON.md`) adds four more:
  - nothing under `/mnt/Backups/Ubuntu/` is read beyond `stat`;
  - no unit is started, stopped, enabled, disabled or reloaded, system or `--user`;
  - nothing contacts 127.0.0.1:8300;
  - no `sudo`.
- The handoff keeps only the `duplicati.service` start/stop/restart limit. "No session performs host
  actions" now appears only in the INDEX row.
- This matters because round 4's briefs will be drawn from this handoff, and its consequence lens is
  about the sole copy under `/mnt/Backups/Ubuntu/`.
- **Correction**: restore those lines under "Standing limits".

**D-3. Step 3's "re-assemble the record" cannot be run from the handoff alone.**

- `util/ad-hoc/2026-10-04_archive_phase_b_round_reports.py` needs twelve exact
  `--report 'Heading=file:path'` pairs.
- Seven of the sources exist only as untracked files in two places:
  - sibling worktree `cached-swinging-summit`, under `util/ad-hoc/2026-10-03_backup-phase-b-validation/`;
  - `/tmp` copies. This session's own re-assembly at 13:14Z read `…/scratchpad/phaseb-tree/…`, and the
    handoff calls the `/tmp` trees expendable.

  The seven are round 2's brief, its lanes A, B and C, the ml#2114 and ml#2115 lanes, and the
  predecessor's validation.
- The handoff names neither location, nor the twelve headings.
- **Correction**:
  - save the 13:14Z invocation as a script in R3, pointed at `cached-swinging-summit`'s files;
  - name that script in step 3;
  - add "do not sweep `cached-swinging-summit` until the Phase B PR merges" (or: take the report bodies
    from `main`'s record).

**D-4. The record gives false provenance for five sections, and re-assembly will repeat it.**

- Every section says "lifted from a file the 2026-10-03 session saved verbatim". The reason is
  `util/ad-hoc/2026-10-04_archive_phase_b_round_reports.py:89`, which writes that text for every `file:`
  source.
- That is wrong for five sections:
  - F1, F2, R3A and R3C were saved on 2026-10-04 by session c9277a65, from the subagents' transcripts.
    I checked each one byte-equal to its lane's final message.
  - Round 3's brief was written by session c9277a65 itself.
- The header itself says the 2026-10-04 reports are "lifted from the subagents' own transcripts".
- **Correction**: give each `--report` its own origin (for example `file:<path>|<origin>`) and
  re-assemble. Otherwise round 4's reports get the same false line.

### NIT

- **N-1. A finished item is listed as remaining.**
  - The handoff says the record's header "must stop saying 'Everything is applied' and say that no lane
    reproduced the BLOCKER". This package already did both (record lines 46-47 and 54).
  - The only "everything is applied" left is at line 75, the F-lane disposition, which round 3 did not
    refute. A search for the phrase would land there.
  - "Disposition of round 3: Pending" should also say two things:
    - the record parts of R3A N-1 and R3C N-9 are applied in the header;
    - the round-3 reports' "record:41 / :52 / :58" citations refer to `c3d0e890`'s copy.
- **N-2. Shared-file history.**
  - Of "#2130, #2145, #2139 and #2151", only #2145 and #2139 touched CHANGELOG.md, `docs/REFERENCE.md`
    or `ci.yml`. ml#2134 also touched all three.
  - #2130 and #2151 touched none of the four files, and no PR touched AGENTS.md.
  - Harmless, because the step also says "run `git log` on each path".
- **N-3. Some round-3 remedies are carried only in part.**
  - R3A D-4 asks for UNKNOWN before the encrypt start (`2026-10-03_rekey_settings_key.bash:254`) as well
    as the decrypt start.
  - R3A D-2 asks to fix Appendix C's "None of items 1–10 has been applied", since item 4 is now applied.
    The handoff's "and Appendix C, whose item 4 is now applied" reads as a residue addition instead.
  - R3C D-5 notes that `docs/REFERENCE.md:3203` claims the suite pins the drift copy-aside.
  - R3A D-1's alternative, an env-file allow-list of tunables, is not mentioned.
- **N-4. Two parts of ml#2134's owner notes are dropped.**
  - After the deploy, every check records `ALERT UNREACHABLE` durably until the web credential exists.
    That is the intended signal, not a failure.
  - #2121, #2124 and #2127 each conflict once in `docs/REFERENCE.md`: keep both sides (F2 D-3).
- **N-5. Files are named by role only** (the repo's convention is mandatory).
  - "The wrapper" is `scripts/duplicati-wrapper.bash`.
  - "The installer" is `util/install_duplicati_service.bash`.
  - "The contract text" is `util/systemd/duplicati-env.contract`.
  - "The re-key" is `util/ad-hoc/2026-10-03_rekey_settings_key.bash`, with its gate
    `util/ad-hoc/2026-10-03_rekey_gate.py`.
  - "The stub" is `tests/duplicati_api_stub.py`.
  - "Add A DEFECT-4 … to A §8" uses "A" for both the assessment and round 2's lane A.
- **N-6. Problems in the `R3/PR_BODY.md` draft.**
  - It lists five files as "Added": the record, the header and the three `2026-10-04_*` scripts. They
    reach `main` first, through the archive PR.
  - Its last line, "Merge approval … was granted by the owner in this session", is false in the next
    session.
  - Its "pinned hook binary" (`repo2m2h173s`) is markdownlint-cli 0.48.0. juniper-ml pins v0.42.0
    (`repoft72ba_k`). Both are clean on D, A, the record and the handoff.
- **N-7. Operating details the predecessor gave are dropped.**
  - Reset D first (`git show origin/main:<D> > <D>`) before running the two scripts.
  - The checks to re-run after the fold-in: markdownlint, the snippet linter,
    `util/markdown_structure_delta.py --base origin/main`, flake8/shellcheck, and both screens.
  - The `--tasks-dir` path pattern for `util/ad-hoc/2026-10-04_save_subagent_report.py`.
  - A pointer to `HANDOFF_2026-10-03_backup-arc-consolidated.md` for the traps and the carried-item
    inventory. Only the INDEX row and that file's banner say it.
- **N-8. "4 hard-coded sites" is 4 files and 6 lines**: `yamaguchi_switch_aes.py:39`, `:49` and `:53`
  are one file.
- **N-9. The verify unittest drops to 32 of 33 once the installer has run on this host** (R3C D-4).
  Say so next to the command.
- **N-10. "It holds … its header … and the two archiving scripts".** The record holds the reports. The
  header and the scripts are carried by the archive PR, which also adds
  `util/ad-hoc/2026-10-04_wip_worktree_delta.py`.

## Residue check

The predecessor is `git show origin/main:prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_backup-phase-b-fold-in-pending.md`.

1. **Fix-forward for ml#2115: DONE.** ml#2134 merged as `f01a438c` at 2026-10-04 21:56:09Z. Its
   post-merge runs on `main` (CI/CD Pipeline, CodeQL, Post-Merge Main Verification) are all `success`.
   - (a) The export token, the stub and the suite: DONE. On `origin/main`, `_export` obtains the token,
     and the stub's `_product_refusal` returns an empty 400, a 500 and a 401.
   - (b) `--backup-id` defaults to `""` and records JOB_MISSING: DONE (`yamaguchi_watchdog.py:313`; usage
     errors exit 64).
   - "Deploy the watchdog immediately after the sync": DONE in code (the deploy script's WHEN block) and
     CARRIED as the urgent owner action. It is **not yet done on the host**:
     - the primary checkout's `util/ad-hoc/yamaguchi_watchdog.py` is `77ef6692`'s version, mtime
       2026-10-03 17:09:10, with `required=True` at line 296;
     - the deployed unit (installed 08-26) passes no id and has no drop-in;
     - the last status record is `2026-10-03T12:00:39-0500 ALERT UNREACHABLE backup=2`;
     - the 2026-10-04 12:00:39 run ended `Result=exit-code`, `ExecMainStatus=2`.
   - One narrow lane, then merge: DONE (F1 and F2, both in the record).
   - The job-2 residue: DONE in ml#2134's PR body (8 flag defaults + 4 files, which `git grep` on `main`
     confirms) and CARRIED as a D/A prose item.
   - Fleet PRs #2119 and #2121 on the shared files: CARRIED (named). The REFERENCE.md conflict guidance
     is LOST (N-4).
2. **Clearing script and D prose: DONE in `c3d0e890`.** Spot checks in D:
   - `systemctl revert` appears only as a prohibition (:1991, :2508);
   - the key swap is a copy and one atomic `mv` (:1994, :2509);
   - ml#2134 is named (:2003, :3004);
   - the directory count is 96 (:2482);
   - the reset tool "skips a non-server data…" (:2408);
   - the three 2026-10-03 helpers are named as untagged repo files (:2054-2057);
   - wrapper 2.2.0 and installer 1.2.0;
   - Appendix B's row is `etc/duplicati/env` (:3080);
   - the fstab drive uses `MEDIA_ROOT=/mnt` (:1950).

   R3A accounts for all 38 round-2 findings (30 fixed). Its 7 PARTIAL and 1 FIXED-BUT-WRONG are CARRIED:
   - by name: the deny list, R4's open rows and note 5b, the ConnectionString count, and the EXIT trap;
   - through the NIT clause: the two ml#2114 passages, the AC-6 wording, and note 12b.

   Regeneration and the checks: DONE (re-run, see Not refuted).
3. **A's edits: DONE in `c3d0e890`.** A has the §8 "Round 2" entry (A:384) and the §9 row (A:412):
   real file names, note 6a, note 5b. The five findings §8 omits, and I-41/note 5b: CARRIED.
4. **Open the PR, merge it, then B9.**
   - Open the PR from current `main` with whole files, rebuilding the shared files from `main`: CARRIED
     as step 3, but with a stale suite count (D-1).
   - The PR and commit drafts: CARRIED. They are now `R3/PR_BODY.md` and `R3/COMMIT_BODY_ONLY.txt`, both
     still holding `<<ROUND3>>`.
   - `util/safe_merge.py --execute`, then read the MERGED line: CARRIED. The handoff now correctly says
     the merge approval does not carry over (memory `feedback_headless_merge_approval_policy.md`).
   - B9 as its own PR, with Go at `/snap/bin/go`: CARRIED (the path exists).
5. **Standing limits: PARTIAL.** "Nothing under `/mnt/Backups/Ubuntu/` moved" is LOST (D-2).
6. **Verify first: replaced.** The new block fails as written (B-1).

**Round 3** (R3A, R3C):

- All 11 DEFECTs (8 distinct, since three are shared) are CARRIED; three of them only in part (N-3).
- The NITs are covered by "fix the cheap ones; record the rest in A §8". R3C N-4, N-5, N-9 and N-10, and
  R3A N-1, are carried by name.
- No round-3 finding is left neither carried nor covered.

**ml#2134's owner notes:**

- CARRIED: deploy with `--backup-id 2`, why 2, re-run after Procedure B, close #2129, and the stale
  statements in #2128/#2119.
- LOST (N-4): "what it will report meanwhile", and "keep both sides" for the REFERENCE.md conflicts.

**New residue the package should carry but does not**: lane B's interim notes (B-2).

## Not refuted

- **The frozen commit.** `c3d0e890` has parent `e509353e`, carries no `gpgsig`, is on no remote branch,
  and its branch has no upstream (`git cat-file -p`, `git branch -r --contains`). `e509353e` is
  ml#2134's head before update-branch: #2140's commit list shows `e509353e`, then `74c2e3e0`, the merge
  of `main` that is ml#2134's final head.
- **ml#2134.** Its four fixes are on `main`, and its post-merge runs are green (`gh pr view`,
  `gh run list --commit`, `git show origin/main`).
- **D regenerates byte-for-byte.** Run in a `git archive c3d0e890` copy under scratch:
  - input: `main`'s D, sha256 `5d875ed9…` (blob `c71c8df0`, unchanged since `cf711cf4`);
  - `--from-repo`: "5 … rewritten, 9 already identical, 1 … retagged";
  - the clearing script: "applied 54 … fenced blocks: 20, 1 changed as declared";
  - result: `890d8a1b…`, the manifest's hash.
- **The edit count.** The 54 edits are 52 top-level `edit()` calls, 1 `edit()` in a loop (`count=5`),
  and 1 `fence_edit()` on P0 step 10's guard dry-run. `FIXFWD` defaults to `ml#2134` (script lines 80,
  420, 545).
- **Tests.** The six suites named in `R3/PR_BODY.md` run 180 tests, all OK; the wrapper suite alone runs
  33. `git status --porcelain --ignored` was identical before and after.
- **Screens on `c3d0e890` against `origin/main`.**
  - `juniper-symbol-loss-check`: 0 findings.
  - `juniper-docs-additions-check`: OK.
  - `util/markdown_structure_delta.py`: 0 regressions over 6 files.
- **Screens on the four package files.**
  - The structure screen finds 0 problems.
  - `juniper-check-doc-links` finds every link valid.
  - markdownlint 0.48.0 and 0.42.0, run without `--fix`, report 0 findings on the record, the handoff,
    D and A.
  - The two pointer files have the same 16 findings as `main`'s copies; the INDEX row grows from 903 to
    950 characters.
- **The record's contents.**
  - It equals the header plus the twelve sources, byte for byte, in the header's order, and every stated
    character count matches.
  - The round-2 sources equal session 652c1204's scratch originals, so the 10-04 blank-line rewrite of
    `C.md` and `pr2114.md` has been undone.
  - F1, F2, R3A and R3C equal their lanes' final messages.
- **Credential screen.** 0 hits and 0 mail-address shapes in the record, the handoff, the header and
  `R3/HANDOFF_PR_BODY.md`.
- **The header's counts**, checked against each report's headings:
  - round 2: A 1/6/7, B 2/5/3, C 1/7/6, ml#2114 1/3/5, ml#2115 1/1/5;
  - F1 0/2/6 and F2 0/3/8;
  - round 3: A 0/6/8 and C 0/5/13;
  - 30 fixed, 7 in part, 1 fixed but wrong;
  - the three defects both round-3 lanes found, and each lane's additions.
- **"No lane could reproduce it without root".** Round 2's `C.md` says "Not demonstrable here without
  root". Lanes A and B argued from `man systemctl`, `stat` and `dpkg -L`.
- **Lane B was stopped at the limit**, as the parent transcript shows (see B-2).
- **Smaller sources.** Round 2's manifest has 18 files, and R4:90, :143, :153, :217, :231 and :351 are
  follow-up rows.
- **Watchdog facts** (see Residue check, item 1), from `systemctl --user show`, `awk` on the status
  file's first four fields, `stat` and `sha256sum`.
  - The local `main` ref is `cf711cf4`, five commits behind `origin/main`.
  - The deploy script takes `--backup-id`.
  - The primary checkout's unit file already passes `${YAMAGUCHI_BACKUP_ID}`, so the deploy's
    precondition holds after a sync.
- **Fleet PRs.**
  - All ten named are open drafts.
  - #2137, #2138 and #2140 were opened after ml#2134 opened (21:41:48Z); #2159 was opened on 10-05.
  - The commits #2138 and #2140 add touch only tests, `ci.yml` and `docs/REFERENCE.md`. The code changes
    in their diffs come from `e509353e`.
  - #2119 and #2128 still carry the statements ml#2134 made false.
  - No other open PR touches a backup file.
  - `_target_url` on `origin/main` accepts a whitespace-only URL.
- **Web-credential format.** One `DUPLICATI_WEB_CREDENTIAL=` line, and `_unquote` strips one outer quote
  pair.
- **R3's contents.** All 32 lines of `R3/CHANGELOG_ENTRY.md` are in the frozen CHANGELOG.md. The 25 harness
  scripts each contain a `/tmp` path.
- **The named tools exist with the arguments the handoff implies.**
  - The archive script: `--header --out --report --tasks-dir --check`.
  - The save script: `--tasks-dir --agent --out`.
  - The delta script: `--sibling --base list|transplant`; I ran `list`, which is read-only.
  - `util/open_signed_pr.py`: `--add LOCAL:REPO` sends whole files; `--commit-body-file` exists.
  - `util/safe_merge.py`: `--pr --execute`, and it prints `MERGED #n`.
- **The pointer edits.** In the INDEX and the consolidated handoff, only the P1 row and the banner lines
  differ from `main`, and `main`'s copies are unchanged since `cf711cf4`.
- **The sibling `cached-swinging-summit` holds nothing the frozen commit lacks.**
  - 13 of the 20 files it changed are byte-identical to `c3d0e890`'s.
  - The other 7 are superseded:
    - the shared files were rebuilt from `main`;
    - D and A were regenerated;
    - its API client is ml#2115's;
    - its test file differs only in formatting and one case name;
    - the frozen clearing script contains all 26 of the sibling script's edit tags.
- **Not tested:**
  - "every hook passes": pre-commit's hooks run `--fix` in the worktree;
  - "Tier 1 is still down": that needs the server (`duplicati.service` is active on the vendor unit);
  - the archive PR's merge date, which the record's Status line asserts.

## Slips

None against the limits.

- **Writes.** I wrote only under `…/scratchpad/val/HV/`. The `git archive` of `c3d0e890` and the D
  reproduction ran there. The clearing script's final `git diff --stat` failed harmlessly, because that
  directory is not a repository.
- **Host reads.** Read-only `systemctl show` (system and `--user`) and `list-timers`, plus the text of
  the deployed user unit.
- **Transcripts.** I read the parent's and the subagents' transcripts, to compare the reports and to
  read lane B's notes.
- **Tests.** The suites' re-key dry run probes `-e` and `-r` on `/etc/credstore` and on the installed-unit
  path. Those are metadata only, as R3C recorded.
- **Bytecode.** `juniper-check-doc-links` ran without `PYTHONDONTWRITEBYTECODE=1`. It is an installed
  console script, so any bytecode would land in the conda env, not in a worktree. The worktree's
  `--ignored` status is unchanged.
- **Network.** `gh` reads on `pcalnon/juniper-ml` only.
- **Observed, not mine.** `R3/HANDOFF_PR_BODY.md` appeared at 08:15:50, after this lane started.

<!-- markdownlint-enable -->

---

## The 2026-10-04 handoff's re-validation

Archived verbatim (21,646 characters, sha256 `c98dcc734038e5c7`), lifted from the lane's final message, saved from its transcript by session c9277a65 on 2026-10-05.

<!-- markdownlint-disable -->

# Re-validation of the round-3 handoff package

**Manifest:** the sha256 of `R3/PACKAGE.sha256` is `80f196f4…23ea`, as the brief says. `sha256sum -c` gives 13/13 OK, at the start and again at the end. HEAD is `c3d0e890`.

**Verdict: REFUTED in part (0 BLOCKER, 3 DEFECT, 11 NIT).** HV's 16 findings are applied, D-2 only in part. All 15 of R3B's findings are carried or covered, and none is lost. The record re-derives byte-exactly from its header and 14 sources, and every origin line is true. Three things fail:

- The package's own provenance checker cannot confirm 4 of the 14 sources, yet it is cited as the check.
- `--from-files` silently drops any report added later.
- The Phase B drafts still carry claims that round 3 refuted.

**Names used here:**

| Name | File |
| --- | --- |
| handoff | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-04_backup-phase-b-round3-fold-in-pending.md` |
| record | `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md` |
| R3 | `util/ad-hoc/2026-10-04_backup-phase-b-round3/` |
| header | `R3/RECORD_HEADER.md.in` |
| archiver | `util/ad-hoc/2026-10-04_archive_phase_b_round_reports.py` |
| reassemble | `util/ad-hoc/2026-10-05_reassemble_phase_b_record.bash` |
| match | `util/ad-hoc/2026-10-05_match_reports_to_final_messages.py` |
| HPB | `R3/HANDOFF_PR_BODY.md` |
| PRB | `R3/PR_BODY.md` |
| CBO | `R3/COMMIT_BODY_ONLY.txt` |
| HV, R3A, R3B, R3C | `R3/HV.md`, `R3/R3A.md`, `R3/R3B.md`, `R3/R3C.md` |
| D | `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` |
| A | `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` |
| `$S` | my scratch directory, `…/c9277a65-…/scratchpad/val/HV2/` |

## Findings

### BLOCKER

None.

### DEFECT

**D-1. The record cites a provenance check that fails on the record's own sources.**

- **What is wrong.**
  - header:30 says `match` "checks each claim against the transcripts", and HPB:31 says the same.
  - The unpinned `R3/HANDOFF_COMMIT_BODY.txt:11-13`, written after this lane started, would put "checked against the transcripts by" `match` into `main`'s history.
  - Run over the 14 sources, `match` exits 1. Four of them get `final message: NONE; written file: NONE` and `blank-line-insensitive: NONE`: round 2's `B.md`, `pr2114.md` and `pr2115.md`, and round 3's `BRIEF_COMMON.md`.
- **Why.** `match` replays only `Write` and `Edit` calls. Those four files were finished in place by `Bash`:
  - lane B (`abe7ead…`), by a Python `replace` at 2026-10-03T11:51:57Z;
  - the ml#2114 lane (`a0eb88c…`), by `sed -i` at 12:05:02Z;
  - the ml#2115 lane (`a47c960…`), by `sed -i` at 12:34:42Z;
  - the coordinator, by a placeholder `sed -i` at 2026-10-04T21:54:07Z, between its `Write` and two `Edit`s.
- **The origin lines are still true** (see Not refuted). So anyone who runs the cited check is told that four true origin lines are unconfirmed.
- **Reproduction.** Run `PYTHONDONTWRITEBYTECODE=1 python3 <match> --tasks-dir <652c1204>/subagents --tasks-dir <c9277a65>/subagents` with one `--file` for each of the 14 sources that `reassemble --from-files` reads. It exits 1.
  - `$S/trace_writes.py` shows the `Bash` edits.
  - `$S/parent_calls.py brief` replays the brief's `Write`→`sed`→`Edit`→`Edit` to the exact bytes.
- **Remedy.** Do one of these:
  - teach `match` the two `Bash` shapes that occur here (`sed -i 's/…/…/'` and a Python `.replace` on the named file);
  - or add a second criterion: the last writer is the lane, and the mtime falls inside its window.

  Until then, say at header:30, HPB:31 and in the commit body that `match` confirms 10 of 14, and why.

**D-2. `--from-files` silently drops any report added after the first 14.**

- **What is wrong.**
  - `from_files()` (reassemble:57-79) indexes 14 fixed sources, so any heading after `HEADINGS[13]` is ignored.
  - The script's own "Adding a report" steps (:27-30) put a new report in `NEW`, then move its heading into `HEADINGS` and empty `NEW`.
  - After that, default mode keeps the report and `--from-files` drops it.
  - So reassemble:22-23 ("Both modes must give the same record") and HPB:36 ("Both give a byte-identical record") stop being true, with no warning.
- **Reproduction (copies only, `$S/tree`).**
  1. Add a fake round-4 report through `NEW` and run: the record has 15 sections.
  2. Apply the move (`$S/r4_trap_setup.py`). Default `--check` says IDENTICAL; `--from-files --check` says DIFFERENT.
  3. `--from-files` without `--check` exits 0 and rewrites the record with 14 sections. With `NEW` empty, default mode cannot recover the lost report.
- **Why it matters.** handoff:119-121 routes round 4 through exactly this path, and PRB:87 describes the script's change as just "round 4's headings".
- **Remedy.**
  - Key the file sources by heading.
  - Make `--from-files` refuse any heading that has no file.
  - Make the archiver refuse to drop a heading the existing `--out` record holds.

**D-3. The Phase B drafts are handed over as finished except for two placeholders, but some claims are false now and others will become false.**

- **What is wrong.** handoff:122-123 asks only for `<<ROUND3>>` and `<<SUITES>>` to be filled in.
- **False now:**
  - CBO:17-18 says "a BLOCKER all three main lanes reproduced independently". R3A N-1 says no lane reproduced it, and header:63-64, which lands now, says "no lane could reproduce it without root". This commit body becomes permanent history.
  - PRB:16 ("sets the password and nothing else") and CBO:14 ("it sets the password only") are refuted by R3A N-3: the 102 run also upgrades the schema, runs `FixInvalidBackupId` and re-encrypts password-named settings.
  - PRB:35 ("The residue list is now the round-4 record's open rows") contradicts R3A D-2 and R3B N-2.
  - CBO:32 says "hermetic suite", which R3C D-4 refutes.
  - The last two become true only once the fold-in lands.
- **Certain to change.** handoff:66-67 and :77-80 order new tests, and :81-92 orders new prose in the clearing script. That affects:
  - PRB:50 and CBO:30 ("54 edits … 53 to prose");
  - PRB:57-58 ("180 tests", "(33, new)") and CBO:33 ("(33 tests)");
  - PRB:62 and CBO:34 ("`main`'s count plus this suite"), which is wrong if a suite file is added;
  - PRB:66 ("the 26 files"), when the PR itself lists 24;
  - the Changed/Added lists (PRB:69-95, CBO:38-51), which have no slot for new test files.
- **Remedy.**
  - Fix the four now-false sentences.
  - Either turn every count into a placeholder, or add to step 3: "re-derive every number and file list in both drafts after the fold-in".

### NIT

**N-1. Verify block, lines 4-5.**

- handoff:166 and :168 need an up-to-date `origin/main`. The block has no fetch, and the merge does not move the shared refs.
- Line 5 fails today as well as line 4: `git diff --stat origin/main` lists all 5 files (+3206/−1).
- After the merge, line 5 stays empty only while `main` leaves those files alone. The INDEX is a hot file: at least 5 commits touched it between 2026-10-03 10:23Z and 2026-10-05 13:42Z.
- "unless main moved" names no action to take. If the record, header or archiver move on `main`, default mode rebuilds from this worktree's stale copies. The Phase B PR's whole-file send would then revert `main`.
- **Remedy.**
  - Add `git fetch origin main` first.
  - Under line 5, say: "if one moved, copy main's version over the worktree's before running reassemble".

**N-2. Some restatements change what R3B said.**

- **N-11 counted as new.** handoff:68 ("five with R3B N-11's") and header:122-123 ("adds a fifth window") treat R3B N-11 as a new state. R3B said it "may duplicate"; its decrypt-timeout window is R3A D-4's case, which handoff:71-72 already covers.
- **DEFECT-2's B-path dropped.** handoff:102-104 drops R3B's "on B, do it after the hand start and before the first start". As written, it sets `paused-until` in step 8 on every path, but per R3B's state table, B has no database at that step.
- **DEFECT-1's survival window dropped.**
  - handoff:96-97, handoff:147 and HPB:14 state the 09-18 deletion without exception. R3B says the fileset survives a first run between 10-17T22:14Z and 10-18T14:00Z; header:136-137 keeps this.
  - handoff:99 drops "and §10.2 step 1" from the third remedy.
- **"Told not to" overstates.** header:118 says "lane B was told not to re-derive them", but the resume message said "you need not re-derive those".
- **Remedy.** Restore each qualifier.

**N-3. D states the "nothing is deleted" fact twice.**

- `c3d0e890`'s D has it at :16 (front matter) and :2080 (§8); `main`'s D has it at :15 and :1818. A has a third copy at :204 (`main`: :203).
- R3B named only D:2080 and A:204, and handoff:100-101 says to correct "D's … sentence", singular.
- **Remedy.** Name D:16 as well.

**N-4. The `/mnt/Backups/Ubuntu/` limit is narrowed (HV D-2 applied only in part).**

- handoff:180 says "is moved, or read beyond `stat`". `R3/BRIEF_COMMON.md:52` says "is read beyond `stat`, and nothing there is touched".
- Deleting or creating files there is no longer named. Only handoff:186's catch-all ("no session performs host actions") still covers it.
- header:165 calls the limits "restored in full".
- This matters because every lane's brief must carry these limits (handoff:176), and round 4's subject is deletion.
- **Remedy.** Restore "nothing there is touched".

**N-5. The archiver's `record:` source accepts a wrong count if it lands on a CLOSE marker.**

All attacks ran on copies (`$S/attack_record*.py`).

- **A6, short count.** I set a count that ends at a `<!-- markdownlint-enable -->` line quoted inside a body. The tail is dropped silently, the write persists the loss, and a second run reports IDENTICAL.
- **A7, long count.** I set a count that ends at the next section's CLOSE. That section is swallowed and duplicated, and only the following run refuses.
- archiver:26-27 claims "A record: source is exact". That holds only when the count is right.
- These cases all refuse, as they should: counts off by one, a duplicated heading, a body quoting its own heading's marker, and CR bytes.
- One divergence: a body quoting its own heading's marker builds under `--from-files` but refuses under default mode.
- **Remedy.** Either:
  - require that CLOSE is followed by end of file or by the next known `\n---\n\n## <heading>\n\n`;
  - or record each body's hash in its origin line.

**N-6. HPB:61 ("pre-commit passes over every file in this PR") overstates what ran.**

- `prompts/` is in the top-level `exclude:` (`.pre-commit-config.yaml:43`), so no hook ran on the three handoff files.
- The markdownlint hook excludes `notes/` (:240-241).
- The parent's run was piped through `grep -v 'Skipped$'`, which hid what was skipped.
- The substance holds anyway (see Not refuted, Hygiene).
- **Remedy.** Say which hooks ran on which files.

**N-7. `R3/CHANGELOG_ENTRY.md:28` still says "54 prose edits and one".**

- handoff:87-88's "(the R3 drafts are already fixed)" covers only PRB and CBO.
- If step 3's CHANGELOG rebuild (handoff:124) takes its lines from this file, the refuted count returns.
- **Remedy.** Fix the file or delete it.

**N-8. Some work exists in only one place.**

- `R3/r3c-harness/` (25 scripts, every one hard-coding `/tmp` paths), the drafts and `c3d0e890` exist only in this worktree.
- The harness's only other copy is in tmpfs `/tmp`.
- handoff:77-79 builds the fold-in's tests from that harness.
- Nothing says "do not remove or sweep `sorted-stargazing-garden`".
- **Remedy.**
  - Add that sentence.
  - Then either carry `r3c-harness/` in this PR, or `git bundle` the branch to a durable path.

**N-9. There is no slot for this report.**

- If it goes into the record, all of these must change together:
  - handoff:22 ("all 14 reports") and HPB:24 and :29;
  - header:154-155 ("both reports");
  - reassemble's `HEADINGS` and `from_files`;
  - `R3/PACKAGE.sha256`.

**N-10. Some claims are time-bound, or repeat old host measurements.**

- handoff:138 ("before 12:00 CDT 2026-10-05") and HPB:45 ("today") will have expired for most readers.
- The premise still held at about 14:40Z: the primary checkout's `util/ad-hoc/yamaguchi_watchdog.py` has `required=True` and an mtime of 2026-10-03 22:09Z.
- handoff:146 and HPB:16 ("defines no backups today, so nothing can run") repeat A's 2026-10-03 measurement as current. They also treat a document STOP as if it were a technical block.
- **Remedy.**
  - Write "until the deploy is done, each 12:00 run exits 2 and records nothing".
  - Cite A for the server's state.

**N-11. R3B's open questions are not routed anywhere.**

- First: is there a `-wal` or `-journal` file beside `/usr/lib/duplicati/data/BMXWPAOGLP.sqlite`? It is the sole-copy index, and D step 8 copies only the main file.
- Second: the stored `startup-delay` and `paused-until` values decide how far DEFECT-2 reaches.
- Neither is in handoff:112-117 or in the owner's actions.
- **Remedy.** Add both to round 4's consequence lane and to Phase C's listing.

## HV's findings

- **B-1 APPLIED.**
  - handoff:164-168 covers it: the expected count of 23 (the run matches, and the three FAILED files are named), `git status`, `ls-tree` and `diff`.
  - It is reinforced at :43-44 and :120-121.
- **B-2 APPLIED.** Lane B was resumed (`SendMessage` at 13:51:28Z), its report was saved at 14:02:22Z and archived, and handoff:112-117 sets the lens.
- **D-1 APPLIED.** The suite count is 174, correct today:
  - `main` has 173 suites in `ci.yml` and 173 test files;
  - AGENTS.md:69 says 169;
  - #2138 adds two suites, #2140 one and #2159 one.
- **D-2 PARTIAL.** It is restored except that "touched" became "moved" (N-4).
- **D-3 APPLIED.** reassemble is saved and named at handoff:119-121. Its `--from-files` mode has the problem in D-2.
- **D-4 APPLIED.** archiver:99-101 now requires an origin, and all 14 origin lines are true.
- **N-1 APPLIED.** header:36-38 and :168-169. These sit outside "Disposition of round 3", but the content is there.
- **N-2 APPLIED.** handoff:125 matches `git log`. #2145 did not touch `ci.yml`, but the sentence is collective.
- **N-3 APPLIED.** handoff:64-67, :71-72, :79-80 and :84.
- **N-4 APPLIED.** handoff:143-144 and :157.
- **N-5 APPLIED.** The names table is at handoff:8-20, and "lane A's DEFECT-4" is at :90-91.
- **N-6 APPLIED.** PRB:85-87 lists the record, header and reassemble under Changed. There is no approval line. PRB:64 says v0.42.0.
- **N-7 APPLIED.** handoff:45-46, :128-129, :115 and :35.
- **N-8 APPLIED.** handoff:85.
- **N-9 APPLIED.** handoff:170.
- **N-10 APPLIED.** handoff:22-24.

## R3B's findings

None is LOST.

- **DEFECT-1 CARRIED.** handoff:96-101 and :145-148, header:135-138, HPB:12-16. Qualifiers are dropped (N-2), and D:16 is missed (N-3).
- **DEFECT-2 CARRIED.** handoff:102-104, header:139-141. The B-path timing is dropped (N-2).
- **DEFECT-3 CARRIED.** handoff:105-107, header:142-143. The header keeps "the run deletes nothing".
- **DEFECT-4 CARRIED.** handoff:108, header:144-145.
- **N-1 COVERED** by the NIT clause at handoff:110-111.
- **N-2 CARRIED.** handoff:82-83.
- **N-3 CARRIED.** handoff:85.
- **N-4 CARRIED.** It is named in the NIT clause at handoff:110.
- **N-5, N-6 and N-7 COVERED** by the NIT clause at handoff:110-111.
- **N-8 CARRIED.** handoff:74-75.
- **N-9 and N-10 COVERED** by the NIT clause at handoff:110-111.
- **N-11 CARRIED.** handoff:68 and header:122-123, but they wrongly count it as a fifth state (N-2).

## Not refuted

Each item names the instrument that failed to refute it.

- **The record equals its header plus the 14 sources, in order.**
  - `$S/rederive.py` uses its own parser, not `lifted()`.
  - The header matches.
  - All 14 declared counts are right.
  - Re-wrapping gives sha256 `77d36ba1…`, the same as the record.
- **Both modes give the same bytes today.** I ran each mode on a copy tree, blanking the record before the second run. `cmp` shows the outputs equal each other and the record, and `--check` in the worktree reports IDENTICAL for both.
- **All 14 origin lines are true.** Checked with `$S/trace_writes.py` and `$S/parent_calls.py`:
  - **Round 2's brief:** written by the parent at 11:20:50Z, before the first lane started at 11:21:28Z.
  - **Round 2's lanes and the 10-03 handoff's validation:** each file's last writer is its own lane, and its mtime falls inside that lane's window.
    - The parent's later `cp` calls copied outward only.
    - The sibling worktree's copies equal the scratch originals.
  - **Round 3's brief:** last changed at 21:54:39Z, before the first lane started at 21:54:55Z.
  - **F1, F2, R3A, R3B, R3C and HV:** each body is its lane's final message plus a newline, saved by `2026-10-04_save_subagent_report.py` from the transcript.
- **Lane B's brief and resume.** The `Agent` call at 21:55:12Z asked for an end-to-end walk of A0, A, A2 and B. `TaskStop` came at 22:45:46Z and `SendMessage` at 13:51:28Z.
- **The header's counts and summaries.** Heading counts:

  | Lanes | BLOCKER/DEFECT/NIT |
  | --- | --- |
  | Round 2: A, B, C | 1/6/7, 2/5/3, 1/7/6 (38 findings in all) |
  | Round 2: ml#2114, ml#2115 | 1/3/5, 1/1/5 |
  | Fix-forward: F1, F2 | 0/2/6, 0/3/8 |
  | Round 3: A, B, C | 0/6/8, 0/4/11, 0/5/13 |

  The parent's message at 12:08Z to the ml#2114 executor supports the header's ml#2114 disposition.
- **All four of R3B's DEFECTs are on `main`.** From `git show origin/main:<D>`:
  - DEFECT-1: the retention policy (:116) and AC-4's 09-18 drill (:2300 and :2549);
  - DEFECT-2: step 9's 12:00 confirmation (:2174) and step 10's startup-pause lapse (:2175);
  - DEFECT-3: "update its defaults before use" (:2151);
  - DEFECT-4: §7.3.6's `DELETE` (:1260-1268);
  - §8 is held (:6 and :1733).
- **The F-lane disposition.**
  - ml#2134's body has the job-2 list and both owner notes.
  - F1 N-1 and N-2 are fixed on `main`.
- **D regenerates byte for byte.** Checked on a `git archive` copy:
  - `--from-repo` gives 5/9/1 and the clearing script applies 54 edits, yielding `890d8a1b…`.
  - A second run is idempotent, and `--check` reports "0 staged".
  - `main`'s D blob `c71c8df0` is unchanged since `cf711cf4`.
- **Tests.**
  - The six suites run 180 tests, all OK.
  - The contract suite runs 33, OK.
  - `test_thread_handoff_archive.py` runs 4, OK.
  - The worktree's ignored-inclusive status was unchanged afterwards.
- **Screens on `c3d0e890` against `origin/main`.**
  - `juniper-symbol-loss-check`: 0 findings.
  - `juniper-docs-additions-check`: OK.
  - `markdown_structure_delta.py`: 0 regressions.
- **markdownlint 0.42.0.**
  - The record, the handoff, the consolidated handoff, D and A are clean.
  - The INDEX has the same two MD013 findings as `main`'s copy.
- **Pointer files.**
  - Each differs from `main` only in the stated lines.
  - Their base blobs (`065cdc56`, `1b517398`) equal remote `main`'s, checked through `gh api`.
- **No clobber on landing.**
  - None of the 8 added paths exists on `main`.
  - Of the 26 manifest files, `main` has changed only `ci.yml`, `CHANGELOG.md` and `docs/REFERENCE.md` since `cf711cf4`.
- **ml#2134 and the frozen commit.**
  - ml#2134 merged as `f01a438c`, and its post-merge runs passed.
  - The stub answers 400, 500 and 401, and the watchdog records JOB_MISSING and exits 64 on usage errors.
  - `c3d0e890`'s parent is `e509353e`, it is unsigned, and it is on no remote.
- **Fleet PRs.**
  - All ten named PRs are open drafts, and their timing matches.
  - #2128 and #2119 carry statements that ml#2134 made false.
  - The newer #2160 touches docs only.
- **Secrets.** `$S/credscan.py` and `$S/credclass.py` ran count- and shape-only.
  - There is no owner address, email-shaped string, token or key.
  - Every base64-shaped hit is a path.
  - One hit is a 16-character test fixture in round 2 lane C's report.
- **Hygiene.**
  - On all ten PR files, `$S/wscheck.py` finds no trailing whitespace, missing final newline, CR or AST error.
  - `shellcheck` is clean.
  - The header's links resolve on `main`.
- **"owner-accepted residue"** in PRB:3 is A's own wording, from B7 at A:226.

## Unverifiable

- **The archive PR's merge date**, which header:9 already asserts. It needs the merge.
- **Verify lines 4-5 for the next session.** They need the merge and a fetch.
- **"The running server defines no backups".** Testing it needs the server, and contacting 127.0.0.1:8300 is forbidden.
- **R3B's five lines in `~/.bash_history`.** I deliberately did not read the owner's history. A count-only grep for R3B's markers would test it.
- **"Every hook" over the 26 frozen files.** pre-commit runs with `--fix` in the worktree. A scratch git repository would test it.
- **R3B's retention table.** I did not re-derive it. That needs a port of `DeleteHandler` and the 9 dlist timestamps.

## Slips

None against the limits.

**Disclosures:**

- **Test suites.** The suites ran in the worktree. They probe `/etc/credstore` and the installed-unit path for metadata only.
- **`systemd-analyze verify`.** The staging script's linter ran `systemd-analyze verify` on unit snippets in scratch. No unit was started, stopped or reloaded.
- **Script placement.** My scripts live under `/tmp`, as this brief requires, against the repo's `util/ad-hoc/` convention.
- **Primary checkout read.** I read the primary checkout's watchdog file with `sha256sum`, `grep -c` and `stat`.
- **GitHub.** I made `gh` reads on `pcalnon/juniper-ml` only.
- **Git output.** `git archive -o` and `git show … >` wrote only to scratch.
- **Observed, not mine.** `R3/HANDOFF_COMMIT_BODY.txt` appeared at 14:17:23Z, after this lane started. It is unpinned.

**Changed:** none.

<!-- markdownlint-enable -->

---

## The 2026-10-04 handoff's third validation

Archived verbatim (20,401 characters, sha256 `af0dfb9d06b3a409`), lifted from the lane's final message, saved from its transcript by session c9277a65 on 2026-10-05.

<!-- markdownlint-disable -->

# Third validation of the round-3 handoff package

**Manifest:** the sha256 of `R3/PACKAGE_HV3.sha256` is `2689670a…1d44`, as the brief says.
`sha256sum -c` gives 42/42 OK at the start and again at the end. HEAD is `c3d0e890`.

**Verdict: REFUTED in part (0 BLOCKER, 1 DEFECT, 9 NIT).** HV2's 14 findings are applied, except N-11,
which is partial. The record re-derives byte-exactly from its header and its 15 sources, and no landing
file clobbers `main`. Two things fail:

- The drafts contradict each other about this third validation, and no file has a slot for it.
- The new archiver still has silent paths that the package's attack script does not try.

**Names used here:**

| Name | File |
| --- | --- |
| handoff | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-04_backup-phase-b-round3-fold-in-pending.md` |
| record | `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md` |
| R3 | `util/ad-hoc/2026-10-04_backup-phase-b-round3/` |
| header | `R3/RECORD_HEADER.md.in` |
| archiver | `util/ad-hoc/2026-10-04_archive_phase_b_round_reports.py` |
| reassemble | `util/ad-hoc/2026-10-05_reassemble_phase_b_record.bash` |
| match | `util/ad-hoc/2026-10-05_match_reports_to_final_messages.py` |
| attack | `util/ad-hoc/2026-10-05_attack_phase_b_archiver.py` |
| harness, README | `R3/r3c-harness/`, `R3/r3c-harness/README.md` |
| HPB, HCB | `R3/HANDOFF_PR_BODY.md`, `R3/HANDOFF_COMMIT_BODY.txt` |
| PRB, CBO, CLE | `R3/PR_BODY.md`, `R3/COMMIT_BODY_ONLY.txt`, `R3/CHANGELOG_ENTRY.md` |
| HV, HV2, R3A, R3B, R3C | `R3/HV.md`, `R3/HV2.md`, `R3/R3A.md`, `R3/R3B.md`, `R3/R3C.md` |
| A | `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` |
| `$S` | my scratch directory, `…/c9277a65-…/scratchpad/val/HV3/` |

## Findings

### BLOCKER

None.

### DEFECT

**D-1. The drafts disagree about this validation, and nothing has a slot for it (HV2's N-9, again).**

- **What is wrong.**
  - HPB:63 says the package "was validated three times" and that "Every report is in the record".
    HPB:69 holds the third row's placeholder.
  - HCB:21-22, which becomes `main`'s history, says it was "validated twice" and that "both reports are
    in the record". That is false either way, because three validations happened.
  - The record holds 15 sections, and this report is not among them. The count of 15 is fixed, with no
    slot for a 16th:
    - handoff:4 says "validated twice", and handoff:23 and :161 say 15;
    - HPB:24 and :29, HCB:13 and header:162-163 ("All three reports") count the same 15;
    - reassemble's `ENTRIES` (:45-61) has 15 rows.
  - HPB:63 is false unless this report is archived, and archiving it needs every one of those edits.
- **Reproduction.** Run `grep -n 'three times\|twice\|15 reports\|All three'` over HPB, HCB, the handoff
  and the header.
- **Remedy.** Decide now whether this report is archived.
  - If it is:
    - add a 16th `ENTRIES` row (`$saved 2026-10-05`) and a header bullet for this validation;
    - change "All three" to "All four";
    - change 15 to 16 at handoff:23 and :161, HPB:24 and :29, and HCB:13;
    - make handoff:4 and HCB:21-22 say three times;
    - re-run reassemble, its `--check` in both modes and attack, then re-pin.
  - If it is not, make HPB:63 name the reports that are archived, and make HCB:21-22 say three
    validations.

### NIT

**N-1. The PR will probably draw CodeQL review threads on harness lines, and those block the merge.**

- **What.**
  - Ruleset `juniper-ml-rules` (13805432) sets `required_review_thread_resolution: true`.
  - CodeQL runs `security-and-quality` with no path filter and posts a thread for each new alert on a
    changed line.
  - Nothing has linted the harness's 15 Python files. HPB:89 says flake8 ran on the three changed scripts
    only.
- **Evidence.**
  - pyflakes reports `F401` at `t1_fence_snippet.py:9`, `t3_snapshot_wal.py:14`, `t4_timer_state.py:6`
    and `t_record_screen.py:6`, and `F841` at `t3_pwinit.py:54`.
  - `t3_cr_key.py:81` calls `open(…).read()`.
  - `main` already has open CodeQL alerts for these rules under `util/ad-hoc/`: 50 `py/unused-import`, 14
    `py/unused-local-variable` and 86 `py/file-not-closed`.
  - 12 of the 60 most recently updated merged PRs carried CodeQL threads, and every thread I fetched was
    resolved before the merge. #2157, merged today, carried at least 20 on lane-probe scripts ("File is
    not always closed", "Unused import").
  - Counter-example: #2089 added 129 probe scripts and merged with no threads.
- **Reproduction.**
  - Run `flake8 --select=F` over the harness's `.py` files.
  - Run `gh api repos/pcalnon/juniper-ml/rulesets/13805432`.
  - Run a GraphQL `reviewThreads` query on #2157.
- **Remedy.**
  - Fix the six lines before opening the PR, and list them in README's "Changed from the lane's copies",
    which now says two lines.
  - Otherwise expect `safe_merge.py` to refuse until the threads are resolved.

**N-2. Default mode silently keeps an archived report over a corrected one, and `--check` says IDENTICAL.**

- **What.**
  - archiver:175-180 lifts a held section from the record and never reads its file or its `ENTRIES`
    origin. Default mode therefore ignores two kinds of correction:
    - a corrected origin, which is how HV's D-4 was fixed;
    - a report saved again later, for example after a lane is resumed, as R3B was.
  - In both cases `--check` says IDENTICAL, while `--from-files --check` says DIFFERENT. There is no
    supported way to replace a single report.
  - `--check` also exits 0 on DIFFERENT (:201-204).
  - It compares text after newline translation, so a CRLF copy of the record reads IDENTICAL.
- **Reproduction** (on copies: `$S/myattacks.py` E1-E2, `$S/myattacks2.py` E8).
  - Edit R3A's origin in a copied `ENTRIES`, or append a line to a copied `R3B.md`.
  - Default `--check` says IDENTICAL, and a default write leaves the record unchanged.
  - `--from-files --check` says DIFFERENT.
- **Remedy.**
  - In default mode, when an entry's file exists, compare the file and the `ENTRIES` origin with the held
    section. Refuse on a mismatch unless `--replace <heading>` is given.
  - Make `--check` exit 1 on DIFFERENT, and compare bytes.

**N-3. A default write discards any record text outside the wrapped sections, with no refusal.**

- **What.**
  - The drop guard (archiver:185-191) covers only section-shaped headings, and the output is the header
    file plus the sections.
  - So a default run deletes, with exit 0, any hand-added section and any edit made to the record's header
    on `main`, such as a doc-automation reflow or a link fix.
  - handoff:162-163 ("copy `main`'s over it first") does not save a header edit, because the header comes
    from the `.in` file.
- **Reproduction** (on copies: `$S/myattacks.py` E3).
  - In a copied record, edit the `**Date**` line and append an "Owner's note" section.
  - `--check` says DIFFERENT. A default run exits 0, and both edits are gone.
- **Remedy.**
  - In default mode, refuse unless told when the record's header part differs from the `.in` file, or when
    any text lies outside every section.
  - Until then, have handoff:162-163 require `--check` to read IDENTICAL before any write.

**N-4. Wrapper text quoted inside a report is read as structure.**

- **What.**
  - **A whole quoted section passes for a report.** archiver:28-31 says "a report that quotes the
    wrapper's markers cannot pass for a section". A complete, self-consistent quoted section does pass, and
    `sections()` lifts it as a report.
  - **Under an existing heading, it splits the two modes.** Default mode dies with "two sections are
    archived under the heading …", while `--from-files --check` still says IDENTICAL.
  - **A quoted section opening blocks every later run.** The opening is three lines: a `---` line, a
    `## <heading>` line, and a line that starts with the words Archived verbatim and an opening
    parenthesis. If that heading is not in `ENTRIES`:
    - `headings_named()` (:97-100) counts it as a report;
    - every later run, in either mode, is refused as WOULD DROP;
    - the saved invocation cannot override this, because reassemble exits 64 on `--allow-drop` (:69).
  - **`--allow-drop` names nothing.** Called directly, it drops without a word (:187). In my test 14
    sections went and stderr stayed empty.
  - Round 4's lanes will validate this archiver, so a quoted opening is likely. This report avoids the
    shape.
- **Reproduction.** On copies: `$S/myattacks.py` E4, E5, E5b and E6.
- **Remedy.**
  - Ignore any candidate that starts inside an accepted section's body.
  - Print WOULD DROP even under `--allow-drop`.
  - Correct the docstring.

**N-5. README's "Repoint `S=` first" misses six of the 25 scripts.**

- **What.** README:10-12 says every script hard-codes the lane's path as `S=`. Six do not:
  - Five load a sibling script by an absolute tmpfs path, `…/val/R3C/bin/t1_gate_attacks.py` or
    `…/bin/t4_rekey_trap.py`, and the sibling carries its own `S`. They are `t1_b3_redo.py:5`,
    `t1_empty_new.py:7`, `t1_stop_block_drift.py:6`, `t4_rerun.py:8` and `t4_timer_state.py:8`.
  - `t_record_screen.py:10` sets `F = …/R3C/frozen` instead.
- Even after `S=` is repointed, these six still run the tmpfs copies, and they fail once tmpfs is reaped.
  handoff:104-105 builds the fold-in's tests from `t4_*`.
- **Reproduction.** Run `grep -L '^S *='` over the harness, then `grep -n c9277a65` over those six.
- **Remedy.** Name the six in README, or resolve their imports relative to `__file__`.

**N-6. "Existed only in a worktree" is not true.**

- **What.**
  - header:187-188 says "existed only in this worktree", and HPB:41 and HCB:19 say "only in a worktree".
  - The lane's originals are still in session c9277a65's tmpfs scratch, under `…/val/R3C/bin/`.
  - 23 of the 25 are byte-identical to the carried copies, and README:5-6 itself says they were copied
    from there.
  - In a record on `main`, "this worktree" has no referent.
- **Reproduction.** `cmp` each harness file with the file of the same name in `…/val/R3C/bin/`.
- **Remedy.** Write "existed only in a tmpfs scratch directory and an untracked worktree copy".

**N-7. handoff:72-75 overclaims: the drafts do not carry placeholders for everything the fold-in changes.**

- **What.**
  - CLE has no round-3 slot. The fold-in adds deny-list entries, the trap rewrite, the pre-flight and R3B's
    four procedure fixes, and handoff:74-75 says to "take the entry from it".
  - These values may move but are not placeholders:
    - wrapper 2.2.0 and installer 1.2.0 (PRB:30-31 and :79-80, CBO:25 and :28, CLE:12 and :15);
    - "5 blocks rewritten, 9 identical, 1 retagged" (PRB:49);
    - "14 tagged blocks" (PRB:64) and "6 files" (PRB:65).
- handoff:164-165 ("Re-derive every count, claim and file list") is the real safeguard, so this is only a
  NIT.
- **Remedy.** Drop "everything" from handoff:72-73, and give CLE a round-3 slot.

**N-8. HV2's N-11 is only partly routed.**

- **What.** handoff:150-153 gives both of R3B's open questions to a round-4 lane, then says "Both need the
  owner's Phase C listing".
  - **The first question fits.** Phase C step 6 already answers it with `sudo ls -la …
    /usr/lib/duplicati/data/` (A:257 in `c3d0e890`, :253 on `main`).
  - **The second question does not fit.** R3B:210 says the stored `startup-delay` and `paused-until` values
    need "reading the database". Those values live in the databases P0 restores, which is Phase D, not
    Phase C.
  - **Neither is answerable as routed.** A lane under the standing limits can answer neither, and neither is
    among the owner actions.
- **Remedy.**
  - Route the first question to Phase C step 6.
  - Route the second to the step-8 read-back that DEFECT-2's own remedy adds (handoff:136).

**N-9. Small errors in the new text.**

- **match:23-29** speaks of "the Phase B record's 14 sources of 2026-10-05", but the record now has 15. Run
  over all 15, match confirms 11 and exits 1 on the same four. Also, its "its D-1" should read "its Not
  refuted".
- **attack:28** says round 2's files come "from ROUND2_DIR or the default".
  - `run()` (:72-73) builds a fresh environment, so `ROUND2_DIR` is ignored.
  - With `ROUND2_DIR=/nonexistent`, attack still reports 0 failures, while reassemble refuses.
- **handoff:224.** attack's "0 failure(s)" holds only where the untracked reports exist. From a copy shaped
  like `main`, it reports 2 failures, attacks 1 and 2 under `--from-files` (`$S/mainlike_attack.py`).
- **HPB:54** drops "and §10.2 step 1" from the re-target remedy. That is the qualifier HV2's N-2 restored at
  handoff:127-128.

## HV2's findings

- **D-1 APPLIED.**
  - header:30-35, match:23-29 and HPB:31 say match confirms 10 of 14, and why. HCB no longer cites match.
  - Re-derived: over all 15 sources, match confirms 11, and the same four fail.
  - Those four files' Bash writers are in the transcripts at 11:51:57Z, 12:05:02Z, 12:34:42Z and 21:54:07Z.
- **D-2 APPLIED.**
  - One `ENTRIES` list (reassemble:45-61) drives both modes.
  - A missing file is refused, and archiver:185-191 refuses a drop.
  - attack passes 13 of 13. Adjacent gaps are N-2 to N-4.
- **D-3 APPLIED.**
  - The four sentences are fixed: PRB:16 and :35, and CBO:14-16, :18-21 and :34-35.
  - The counts are placeholders, and handoff:164-165 orders the re-derivation. The overclaim is N-7.
- **N-1 APPLIED.** handoff:217, :222 and :229-230.
- **N-2 APPLIED.** handoff:88-89, :123-128 and :134-135, and header:125-131. HPB:54 repeats one of the
  dropped qualifiers (N-9).
- **N-3 APPLIED.** handoff:130-132. `grep` on `c3d0e890` finds exactly D:16, :704, :2080 and :2761, and
  A:204.
- **N-4 APPLIED.** handoff:238 matches `R3/BRIEF_COMMON.md:52`.
- **N-5 APPLIED.**
  - The hash is in the origin line, and A6 and A7 are refused.
  - The self-quoting divergence is gone (`$S/myattacks2.py` E7). N-4 covers what remains.
- **N-6 APPLIED.** HPB:85-89 matches `.pre-commit-config.yaml` at :44, :111, :124, :144, :160, :182, :220
  and :240-241.
- **N-7 APPLIED.** CLE is the entry at `c3d0e890`'s `CHANGELOG.md`:127, with exactly the two fixes.
- **N-8 APPLIED.** handoff:43-47 says it, the harness is carried, and the bundle verifies.
- **N-9 APPLIED** for HV2: 15 is used throughout, and `R3/PACKAGE_HV3.sha256` pins the result. The problem
  recurs for this report (D-1).
- **N-10 APPLIED.** handoff:185-199 and HPB:50-53. The facts are re-measured under Not refuted.
- **N-11 PARTIAL.** See N-8.

## Not refuted

- **The change list is what I judged** (`$S/replay.py`).
  - Replaying the coordinator's Write and Edit calls up to 14:15:30Z rebuilds each changed file HV2 pinned,
    and each rebuild matches its hash in `R3/PACKAGE.sha256`. The record comes from HV2's own tree copy.
  - I diffed those rebuilds against the current files.
- **The record** (`$S/rederive.py`, my own parser).
  - It is the header plus 15 sections, byte-exact, and every count and hash is right.
  - The 14 old bodies and their origins equal those in HV2's pinned `77d36ba1`.
  - Both modes' `--check` says IDENTICAL.
- **HV2's origin** (`$S/bash_writers.py`, match). HV2.md is agent `a07f1fdc`'s final message. It was saved at
  09:56:37 CDT by `util/ad-hoc/2026-10-04_save_subagent_report.py`.
- **Screen and hygiene** (`$S/hygiene.py`).
  - The credential screen finds 0 hits over the 15 bodies and over all 37 landing files.
  - There is no trailing whitespace, no CR and no private-key marker. Every file ends in exactly one
    newline, and every AST parses.
- **The harness.**
  - 23 of the 25 scripts are byte-identical to `…/val/R3C/bin/`. The other two differ by exactly the lines
    README lists.
  - The pinned shellcheck 0.10.0 (`--severity=warning`) is clean on all 10 harness bash files and on
    reassemble. The originals fail SC2010 and SC2046.
  - The `read -r -a` change does not alter behaviour: the frozen `DAEMON_OPTS` is one line with no glob
    characters.
- **The bundle.**
  - `git bundle verify` passes.
  - The bundle carries `refs/heads/wip/backup-phase-b` at `c3d0e890`.
  - It requires `cf711cf4`, which is an ancestor of `origin/main`.
  - The restore refspec matches.
- **The watchdog facts.**
  - The primary checkout's `yamaguchi_watchdog.py` is `main`'s blob `5486f2de`, modified 2026-10-05
    14:23:17 CDT, with no `required=True`.
  - The user unit, dated 2026-08-26, runs it at 12:00 with no `--backup-id`.
  - `main`'s code records `ALERT JOB_MISSING` before it logs in (:200-204). It records UNREACHABLE while the
    credential is missing (:25-26, :71).
  - `server-watchdog.log` was last written 2026-10-03 12:00:39 and has 0 lines dated 10-04 or 10-05. I read
    it count-only.
  - A:129 supports "no job on the running server".
- **The restatements.**
  - R3A:174 says "every password-named server setting", HV:22 says "24, not 26", and R3C:116 says
    "14 of 25".
  - R3B:52 and :77 back handoff:127-128 and :134-135.
- **The verify block.**
  - Line 219 gives 23, and exactly the three named files FAILED. Lines 223 and 224 hold in this worktree.
  - `main` has 173 suites in `tests/` and 173 in `ci.yml`, and AGENTS.md:69 says 169. So "174 with one new
    suite" holds.
- **Lint and tests.**
  - markdownlint 0.42.0 is clean on the record, the header, the handoff, the consolidated handoff and
    README. The INDEX has the two MD013 hits the package states (:25, :28).
  - black 26.3.1 (`--check`) and the hook's flake8 settings pass the three changed scripts.
  - `tests/test_thread_handoff_archive.py` runs 4 tests, OK. The record's three handoff names resolve
    against `main`'s archive plus the new handoff.
- **Question 4: nothing on `main` is clobbered.** `origin/main` equals the remote's `main` (`1dea3b39`).
  - 35 of the 37 landing files do not exist on `main`.
  - The INDEX and the consolidated handoff are `main`'s current blobs (`065cdc56`, `1b517398`) plus only
    the stated lines (+4/−1).
  - `util/ad-hoc/2026-09-22_archive_consensus_reports.py`, which the archiver imports, is identical on
    `main`.
  - No open PR (of 43) touches a landing path.
  - The header's six links resolve on `main`.
- **The fleet PRs.** All ten named PRs are open drafts, and ml#2134 is merged.

## Unverifiable

- **CodeQL's actual threads (N-1).** They need the PR's own analysis.
- **header:9, "landed on `main` on 2026-10-05".** At 22:01Z this holds only if the merge comes before 05:00Z
  (for the CDT date) or before 00:00Z (for the UTC date). It needs the merge.
- **Freshness at send time.** `util/open_signed_pr.py` pins the branch head (`expectedHeadOid`), not each
  file's base. Re-diff the INDEX and the consolidated handoff against `main` immediately before sending.
- **The exit code of the 10-05 12:00 run.** The log has no record for that day, which is consistent with exit
  2. The exit code itself needs a journal read beyond count-only.
- **R3B's five lines in `~/.bash_history`.** I did not read the file.
- **CI's `--from-ref` pre-commit and sequence-safety runs on the PR's commit.** A scratch git repository
  would test them.

## Slips

None against the limits.

**Disclosures:**

- **In the worktree** I ran:
  - reassemble, only with `--check`, in both modes, and once more with `ROUND2_DIR=/nonexistent`, which
    refused;
  - `tests/test_thread_handoff_archive.py` and match;
  - the linters, with no fix flags.
- **On copies.** attack and all my own attacks ran on copies under `$S`.
- **Afterwards.**
  - The worktree's status, ignored files included, is unchanged.
  - Nothing is newer than my start in the worktree, `~/.cache/black`, gh's state, the pre-commit db or the
    worktree's index.
- **Git:** `rev-parse`, `status`, `ls-tree`, `show` (into `$S`), `diff`, `merge-base`, `hash-object` (no
  `-w`), `bundle list-heads` and `bundle verify`. No fetch.
- **GitHub:** read-only `gh` and GraphQL reads of `pcalnon/juniper-ml` only.
- **Read-only access outside the worktree:**
  - the session transcripts, for their tool calls;
  - HV2's and R3C's scratch copies;
  - `~/.cache/pre-commit/db.db`, opened `mode=ro`;
  - the primary checkout's watchdog, by hash, `stat` and `grep -c`;
  - two user unit files, their ExecStart and OnCalendar lines only;
  - `server-watchdog.log`, by `stat` and `grep -c`.

**Changed:** none. My scripts and their outputs are only in `$S`.

<!-- markdownlint-enable -->

---

## Round 3's fold-in — the common brief

Archived verbatim (6,422 characters, sha256 `6a381bc0830574ff`), lifted from the brief session 097ae87b wrote for the fold-in lanes on 2026-10-08.

<!-- markdownlint-disable -->

# Phase B round-3 fold-in — common brief (every lane reads this first)

Session 097ae87b, 2026-10-08. Worktree (shared by all lanes, NOT isolated per lane):
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/golden-floating-willow`,
branch `feature/backup-phase-b` (cut from `origin/main` 81d3fbb3, with the frozen Phase B commit
`c3d0e890`'s files carried onto it as uncommitted changes). Run every command from that directory and use
absolute paths.

## Names

| Name | File |
| --- | --- |
| D | `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` (the design) |
| A | `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` (the assessment) |
| R4 | `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md` |
| record | `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md` (all reports so far, verbatim; read-only for you) |
| R3A, R3B, R3C | `util/ad-hoc/2026-10-04_backup-phase-b-round3/R3A.md`, `R3B.md`, `R3C.md` — round 3's three reports. **Your work items come from these.** |
| harness | `util/ad-hoc/2026-10-04_backup-phase-b-round3/r3c-harness/` (R3C's scripts, with a README) |
| handoff | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-04_backup-phase-b-round3-fold-in-pending.md` ("Remaining", item 1, is the fold-in list) |
| wrapper, installer | `scripts/duplicati-wrapper.bash`, `util/install_duplicati_service.bash` |
| contract | `util/systemd/duplicati-env.contract` |
| re-key, gate | `util/ad-hoc/2026-10-03_rekey_settings_key.bash`, `util/ad-hoc/2026-10-03_rekey_gate.py` |
| hand start | `util/ad-hoc/2026-10-03_password_init_hand_start.bash` |
| clearing script | `util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py` |
| suite | `tests/test_duplicati_wrapper_contract.py` (33 tests today) |

Line numbers in the reports refer to `c3d0e890`'s copies, which are the files now in this worktree.

## How D is built (read before touching D)

D is **generated**, never hand-edited:

1. `git show origin/main:<D> > <D>` (reset; run as its own command),
2. `python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py --from-repo` — rewrites D's tagged fenced
   blocks from the repository files (unit, defaults file, wrapper, installer, contract),
3. `python3 util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py` — prose edits only; it refuses to
   change a fenced block except those it declares in `FENCE_EDITS`.

So a change to the wrapper/installer/contract reaches D through step 2, and every prose change to D is an
edit added to the clearing script. A is hand-edited directly.

## Owner ruling (2026-10-08, this session) — R3B DEFECT-1

The owner chose: **suspend retention during recovery** — step 10's edits remove the job's
`retention-policy`, so the first backup after recovery deletes nothing; it is restored only after AC-4's
first drill has passed. **When it is restored, it is set to the NEW policy `2W:1D,6M:1W,2Y:1M,5Y:2M`**
(replacing `1W:1D,1M:1W,1Y:1M,3Y:2M`). Record both changes.

## File ownership

Each lane edits ONLY the files its own brief assigns. Other files are read-only for you. If a change is
needed in a file you do not own, put it in your report under "Needed elsewhere" with the exact text.
`tests/test_duplicati_wrapper_contract.py` is shared by lanes C1 and C2: C1 edits only the classes
`WrapperEnvContract` and `InstallerDriftGate`; C2 edits only `RecoveryHelperGates` and `RekeyGate`. Prefer a
NEW suite file for new tests. Re-read a file immediately before each edit; if an Edit fails as stale, re-read
and retry — never overwrite another lane's change.

`CHANGELOG.md`, `docs/REFERENCE.md`, `.github/workflows/ci.yml` and `AGENTS.md` are the coordinator's:
never edit them; report what they need (e.g., a new suite to wire into CI).

## Standing limits (verbatim from the handoff; they bind you)

- never start, stop, restart, enable, disable or reload a unit, system or `--user`;
- never run a Duplicati binary, never contact 127.0.0.1:8300, and no `sudo`;
- nothing under `/mnt/Backups/Ubuntu/` is read beyond `stat`, and nothing there is touched;
- never read a secret file: `~/.config/duplicati-backup/*`, any `.env` or `*.env`, `/etc/default/duplicati`
  beyond `stat`, `/etc/credstore`, `/etc/duplicati`, or a data-folder database;
- never print an environment variable or a token, and never send the owner's email or any credential to an
  external service;
- no `git stash`; log greps are count-only; no interactive shells (`bash -i` writes `~/.bash_history`);
- no session performs host actions: those are the owner's.

Also: **no git command that changes state** — no `add`, `commit`, `checkout`, `switch`, `reset`, `restore`,
`stash`, `rebase`, `push` (the one exception is the D reset in "How D is built", run only by the lane that
owns D). Read-only git (`diff`, `show`, `log`, `ls-tree`) is fine; split compound git commands into simple
ones (the harness refuses complex ones). New scripts go in `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/`
or `util/ad-hoc/`, never `/tmp` (scratch DATA may go under
`/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/097ae87b-7a4c-4970-9f46-d052521e17c7/scratchpad/<your-lane>/`).
New Python/bash files carry the repo's standard header (see any `util/ad-hoc/2026-10-0*` file).

## Checks you must run on what you change

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest <each affected suite>` (run the whole contract suite too);
- `shellcheck` on changed bash; `flake8 --max-line-length=512` on changed Python;
- for docs: markdownlint is pinned at v0.42.0 (`.pre-commit-config.yaml`).

A test that passes against the unchanged code proves nothing: for each new test, confirm it FAILS against the
pre-fix code (a mutation or the `c3d0e890` copy) and passes after — say so in your report.

## Your report (your final message)

1. Per finding id (e.g., `R3C D-3`, `R3B N-8`): FIXED (what, file:line) / DECLINED (why) / DEFERRED-TO-RESIDUE
   (the one-line reason A §8 should carry).
2. New/changed tests, with the fail-before/pass-after evidence.
3. Check results (exact counts).
4. "Needed elsewhere": exact text other lanes or the coordinator must apply (prose for D/A describing your
   change, CI wiring for new suites, `docs/REFERENCE.md` lines).
5. Anything you found that is wrong but out of your scope.

<!-- markdownlint-enable -->

---

## Round 3's fold-in, lane C1 — wrapper, installer, contract and units

Archived verbatim (14,854 characters, sha256 `cb49259e7839aceb`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

## Lane C1 report: backup Phase B round-3 fold-in (wrapper, installer, snapshot)

All lane C1 work items are done. One mutant survives, and it is equivalent (explained in section 2). No git command changed state, no unit or binary was touched, and nothing under `/etc` was read. I fetched one public file read-only from GitHub: Duplicati's `Server/Program.cs` at tag `v2.4.0.0_stable_2026-09-03`. No local copy of the Duplicati source exists.

### 1. Findings

**R3A D-1 and R3C D-3 (the env-file deny list): FIXED, with a design change.**
- **Deny list, `scripts/duplicati-wrapper.bash` (now 2.3.0) `ENV_OPTION_DENY`:** gains `parameters-file` and its alias `parameterfile` (Program.cs 49-51, 230-237, 1680), `webservice-enable-forever-token`, `webservice-cors-origins` and the alias `webservice-allowedhostnames`.
  - Forever tokens are written into the database permanently (`EnableForeverTokens()` at :658-659), so one env-file line would change the database for good.
  - CORS origins is a direct exposure setting.
  - The alias is honoured whenever the main name is absent (:690-692).
- **Decision: I adopted R3A D-1's allow-list as well.** `ENV_OPTION_ALLOW` admits only these tunables: `webservice-port`, `webservice-token-duration`, `webservice-timezone`, `log-level`, `log-retention`, `ping-pong-keepalive`, `disable-update-check`, `suppress-welcome-page`. Reasons:
  - Version 2.4.0.0 has about 47 server options. Many are security-posture changes that no deny list named: `register-remote-control`, `webservice-webroot`, `webservice-spa-paths`, `webservice-api-only`, the HTTPS and certificate options, `log-file` (could overwrite the database), `tempdir`, `allowed-*-modules`, `disable-default-secret-provider` and the secret-provider options.
  - The deny list has now missed a channel in two consecutive rounds (`DUPLICATI__*`, then `parameters-file`).
  - The deny list stays and is checked first, so the named hazards still get the specific "security option" message.
  - A side effect: a typo in an env-file option now fails with exit 78 instead of passing silently as an unknown option.
- **Contract prose** (`util/systemd/duplicati-env.contract` lines 32-51) is updated to state both lists.
- **Installer's `HAZARD_OPTION` is removed, not extended.** The installer (`util/install_duplicati_service.bash`, now 1.3.0) runs the wrapper itself, `--print-command` against a scratch data folder with `env -i` and `/bin/true` as the server, through a new `wrapper_accepts` function. So `parameters-file` is refused by the installer through the wrapper's single rule (see N-6).

**R3C D-5 (14 of 25 mutants survived): FIXED for the wrapper and installer.** The new suite `tests/test_duplicati_installer_real_path.py` runs the installer for real, as a non-root user, against a scratch prefix. Its stubs:
- `id -u` answers 0;
- `install` drops `-o`/`-g` and refuses any path outside the scratch root;
- `systemctl` and `systemd-analyze` only log their arguments;
- `stat` answers only for the scratch data folder and credential path.

It never reads `/etc`, so it stays hermetic on the owner's host after a real install (the R3C D-4 class of failure). The re-key and clearing-script mutants (M01-M09, M22-M24) belong to other lanes.

**NITs:**
- **R3C N-2 (CR in a key file): FIXED on the wrapper side.** A new `check_key_shape` refuses a carriage return anywhere in the key, and leading or trailing whitespace. It applies to both the credential path and the environment path.
- **R3C N-6 (installer gate narrower than the wrapper): FIXED.** There is now one rule, the wrapper's. 1.2.0 also had the opposite error: it refused `--webservice-token-duration` because the name contains "token".
  - The installer also judges an existing `/etc/duplicati/env` with the wrapper being installed, and refuses if that wrapper would reject it.
  - In a non-root dry run that file is unreadable, so the installer says it cannot judge it rather than refusing.
- **R3C N-7 (first install over files that were never blessed): FIXED.** A never-blessed file that differs from the repository copy is copied to `<dst>.pre-install-<UTC>` before it is replaced. This uses a new `PREEXISTING` map next to the existing drift handling.
- **R3C N-8 (snapshot leaves `-wal`/`-shm` files): FIXED.** `util/ad-hoc/yamaguchi_server_db_snapshot.py` (now 1.2.0, with a HISTORY block) does three things:
  - sets `PRAGMA journal_mode=DELETE` on the snapshot before closing it;
  - removes `-wal`, `-shm` and `-journal` leftovers before and after the run;
  - also removes residue left by earlier runs.
  - Consequence: the snapshot is now a DELETE-mode file, which is an ordinary SQLite database.
- **R3C N-13 (`ReadWritePaths=` without `-`): DECIDED, keep no `-`.** Reasoning:
  - With `-`, the script would still run under `ProtectHome=read-only`, and its `makedirs` would fail anyway.
  - Without `-`, the unit fails early and loudly with status 226/NAMESPACE, which is fail-closed.
  - A comment explaining this was added to `util/systemd/yamaguchi-server-db-snapshot.service`.
  - The installer now prints a NOTE when the destination is absent. It does not create the directory, because `install -d` would leave any missing parent (`~/.local`, `~/.local/state`) owned by root.
- **R3A N-4 (exit-code gloss): FIXED** in the wrapper header. An exception thrown before `Main`'s `try` block (the 0700 data-folder check, the parameters-file parse) ends the process as an unhandled .NET exception, typically status 134. This is marked as unverified, because checking it needs the binary.
- **R3A N-5 (commented secrets passed the installer): FIXED.**
  - `SECRET_ASSIGN` now sees through any run of `#`.
  - A new `SECRET_OPTION` refuses a secret-valued `--option` line, commented or not.
  - The `WrapperEnvContract` shape test's regex is widened the same way, and it now also refuses commented `--opt=value` lines.
- **R3B N-1 (installer prints a hand-typed guard check): FIXED.** The "Next:" hints now show design step 10's form, which reads the URL from the job via `export <id>`, includes the `test -n` line, and is printed after `systemctl start`.

Version references: the wrapper's "2.2.0" mention in `util/systemd/duplicati.service` now reads "since 2.2.0". No other stale version references remain in my files.

### 2. Tests, with fail-before and pass-after evidence

**New suite: `tests/test_duplicati_installer_real_path.py`, 13 tests.**
- First install, checked byte for byte:
  - all 7 files, plus their modes;
  - the env file at 0640, the data folder at 0700;
  - the blessed set equals the installed files' checksums;
  - `daemon-reload` and `verify` are called on the three units;
  - no start, stop, enable or disable is ever issued.
- Pre-install copy-aside (N-7).
- Drift: refused with the prefix tree unchanged; then the copy-aside holds the drifted bytes; a re-run is clean.
- Behaviour change: refused untouched, then installed with no copy-aside.
- An existing env file is kept byte for byte.
- An existing env file the new wrapper refuses stops the install.
- A refused contract installs nothing.
- The data-folder owner/mode check fails as it should.
- The credential must be root 0600, and its contents are never printed.
- The destination-present path prints no NOTE.
- The guard hint reads the URL from the job.
- The real run is refused without root (skipped when run as root).
- The snapshot WAL test.

**Changed tests in `tests/test_duplicati_wrapper_contract.py`:**
- `WrapperEnvContract`:
  - deny and allow lists are pinned by set equality against hard-coded names, so dropping an entry from the wrapper fails;
  - all 17 deny entries are tried four ways each: bare, with a value, mixed case, and upper case with leading whitespace;
  - options outside the allow-list are refused;
  - every allow-listed tunable passes in either case;
  - the CR and whitespace key shapes are refused;
  - the commented-shape regex is widened.
- `InstallerDriftGate`: the secret-gate test adds the N-5 shapes, the five N-6 lines, a non-tunable, and every deny entry in lower and mixed case. A new allowed case shows `--Webservice-Token-Duration` passes.

**Fail-before:** I ran the new and changed tests against the frozen code from commit `c3d0e890`. They fail there: 66 failures across 11 tests. That covers the deny-list, allow-list, key-shape, secret-gate, pre-install, refused-env/contract, guard-hint, snapshot WAL and NOTE tests. The real-path tests for existing behaviour (drift, behaviour change, env kept, data-folder and credential checks) pass on frozen; they are pins, and the mutation run shows what they catch.

**Mutation kill counts** (instrument: `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/c1_mutations.py`):

| | Mutants | Killed | Survived |
| --- | --- | --- | --- |
| Before (frozen suite, M14-M21) | 8 | 5 | M16, M19, M20 (matches R3C) |
| After (new code) | 32 | 31 | I11 only |

- **After, in detail:** M14-M18, M20 and M21 are re-anchored round-3 mutants and are all killed. M19 no longer exists, because the code it mutated is gone. W1-W8, I1-I15, S1 and S2 are all killed.
- **I11 is equivalent:** "bless with the source checksum" cannot differ from the installed file's checksum, because the line just before it runs `cmp -s src dst` and exits on any mismatch.

### 3. Check results
- `tests/test_duplicati_wrapper_contract.py`: **43 tests OK** (this includes lane C2's current state).
- `tests/test_duplicati_installer_real_path.py`: **13 tests OK**.
- shellcheck on the wrapper and installer: 0 issues.
- flake8 (`--max-line-length=512`) on both suites, the snapshot script and `c1_mutations.py`: 0 issues.
- During my run, lane C2's `test_rekey_dry_run_prints_the_whole_sequence_in_order_and_never_reverts` failed for a while (23 != 22). It is green now.

### 4. Needed elsewhere

**`docs/REFERENCE.md` line 3550** (R3C cited :3203). Current text:
> The installer's never-blessed first install runs to the end (I-36), drift is refused and kept as evidence, an existing contract is never overwritten, and `--dry-run` needs no root and writes no `.pyc`.

Replace with:
> The installer's `--dry-run` paths are rehearsed against a scratch prefix: the never-blessed first install runs to the end (I-36), drift and behaviour change are refused, an existing contract is not overwritten, and the dry run needs no root and writes no `.pyc`; its contract gate refuses every secret shape (commented, behind any run of `#`) and, by running the wrapper itself, every option the wrapper refuses. That a drifted or never-blessed file is really kept is pinned by `tests/test_duplicati_installer_real_path.py`, not here.

Also on that line, replace "`DUPLICATI__*` names and security options are refused from the env file in any case" with:
> `DUPLICATI__*` names are refused from the env file, and an `--option` line there must be one of the wrapper's allow-listed tunables -- the 17 named security options, `--parameters-file` among them, each get their own refusal, in any case

Add a new bullet after it:
> - `tests/test_duplicati_installer_real_path.py` -- Phase B round-3 fold-in (R3C D-5, N-7, N-8): `util/install_duplicati_service.bash` run for REAL (not `--dry-run`) as a non-root user against a scratch prefix with PATH stubs (`id`, `install`, `systemctl`, `systemd-analyze`, `stat`); pins byte-for-byte install and modes, the blessed checksums, the drift copy-aside holding the drifted bytes, the pre-install copy of a never-blessed differing file, the kept and the refused existing env file, the data-folder and credential checks, the step-10 guard hint, and that the server-DB snapshot of a WAL-mode database leaves no `-wal`/`-shm` beside it. Never reads `/etc`.

**CI wiring (`.github/workflows/ci.yml`, after line 646):**
```
          # tests/test_duplicati_installer_real_path.py: the installer's REAL path
          # (no --dry-run) as non-root against a scratch prefix with PATH stubs --
          # drift copy-aside keeps the bytes, never-blessed files are copied aside,
          # an env file the wrapper refuses stops the install -- and the server-DB
          # snapshot leaves no -wal/-shm (Phase B round 3, R3C D-5/N-7/N-8).
          python3 -m unittest -v tests/test_duplicati_installer_real_path.py
```
Add the same `python3 -m unittest -v tests/test_duplicati_installer_real_path.py` line to REFERENCE.md's "Running every suite" list after line 3178.

**Prose for D and A (prose lane):**
> D §8 / A §8: "The env file's `--option` lines are now an allow-list of eight tunables (wrapper 2.3.0); the deny list, kept for its specific refusal, gains `--parameters-file`/`--parameterfile`, `--webservice-enable-forever-token`, `--webservice-cors-origins` and the alias `--webservice-allowedhostnames`, and the installer (1.3.0) judges the contract — and any existing `/etc/duplicati/env` — by running the wrapper itself, so the two cannot disagree. A first install copies a never-blessed differing file aside (`.pre-install-<UTC>`), the snapshot (1.2.0) writes a single DELETE-mode file with no `-wal`/`-shm`, and the snapshot unit's `ReadWritePaths=` stays without `-` so a missing destination fails the unit closed (the installer prints a NOTE)."

D's "refuses security options there" sentence should become "accepts only allow-listed tunables there". A §8 should record R3A N-5, N-4, R3B N-1 and R3C N-2 (wrapper half), N-6, N-7, N-8 and N-13 as folded in. The fenced blocks reach D through the staging script's `--from-repo`. The `yamaguchi_server_db_snapshot.py` and snapshot-unit edits change two blessed files, so the next real install will report BEHAVIOUR CHANGE and needs `--update-backup-behavior`. That is expected, and step 8 may want a sentence saying so.

**Lane C2, the other half of R3C N-2:** `util/ad-hoc/2026-10-03_rekey_gate.py` and the hand start should read the key file with `newline=""` and refuse any `\r`, matching the wrapper.

### 5. Out of scope, found wrong
- `REDACT_NAME` in the wrapper also redacts `--webservice-token-duration`'s value, because the name contains "token". It is harmless over-redaction and I left it.
- `docs/REFERENCE.md` line numbers have drifted since R3C cited them (:3203 is now :3550).
- The installer does not create `/etc/systemd/system` or `/etc/default`. That is correct on any real host, so the test pre-creates them in the prefix.

**Files changed:** `scripts/duplicati-wrapper.bash`, `util/install_duplicati_service.bash`, `util/systemd/duplicati-env.contract`, `util/systemd/duplicati.service` (one comment), `util/systemd/yamaguchi-server-db-snapshot.service` (one comment), `util/ad-hoc/yamaguchi_server_db_snapshot.py`, `tests/test_duplicati_wrapper_contract.py` (`WrapperEnvContract` and `InstallerDriftGate` only).
**Files created:** `tests/test_duplicati_installer_real_path.py`, `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/c1_mutations.py`.

<!-- markdownlint-enable -->

---

## Round 3's fold-in, lane C2 — re-key, gate and hand start

Archived verbatim (11,991 characters, sha256 `beaa12b52e4c19a6`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

# Lane C2 report: Phase B round-3 fold-in (the re-key, its gate, the hand start)

All five work items are done. Of the 13 round-3 mutants of the re-key and its gate, the suites killed **5 before** (M07, M10–M13, the same result R3C got) and **13 after**. With 19 new mutants of the fold-in's own code, that is **32 of 32 killed**. One gap is open: `tests/test_ci_test_wiring_drift.py` fails until the coordinator wires my new suite into CI (section 4).

Files referenced: R3A, R3B and R3C are `util/ad-hoc/2026-10-04_backup-phase-b-round3/R3{A,B,C}.md`. D is `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`. A is `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`.

**Changed**:
- `util/ad-hoc/2026-10-03_rekey_settings_key.bash` (now 1.2.0)
- `util/ad-hoc/2026-10-03_rekey_gate.py` (now 1.1.0)
- `util/ad-hoc/2026-10-03_password_init_hand_start.bash` (now 1.2.0)
- `tests/test_duplicati_wrapper_contract.py`, classes `RecoveryHelperGates` and `RekeyGate` only
- **new**: `tests/test_backup_rekey_real_path.py`
- **new**: `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/c2_rekey_mutations.py`

## 1. Findings

**Re-key EXIT trap (R3A D-4, R3C D-1, R3B N-11): FIXED.** The trap keeps its model: it acts, then prints. In `cleanup()` of the re-key:
- **Key state comes from the files.** The pre-flight hashes both keys (`OLD_H`, `NEW_H`). At trap time `key_tag` labels `…-key`, `.old` and `.new` as OLD, NEW, other or absent, and the layout is reported as UNSWAPPED, SWAPPED or INCONSISTENT.
- **Flags.** `STARTED` (and `PAUSED`) is set before `api pause`. `DO_NOT_START` is set by the FragmentPath refusal in `remove_dropin`.
- **Unit stop.** If a drop-in is present, the trap stops the unit first, then removes the drop-in and reloads.
- **UNKNOWN database.** `DECRYPT_ATTEMPTED` and `ENCRYPT_ATTEMPTED` are set before each `systemctl start`. If the matching "Server has started" line was not seen, the database is reported UNKNOWN.
- **Gate counts.** The gate's output is captured in `GATE_REPORT` and printed as `STATE: gate counts: …`.
- **One branch.** Exactly one recovery branch prints: gate passed, gate failed, keys not swapped, keys swapped (with "do NOT start … re-run the installer" first when `DO_NOT_START` is set), or unexpected layout.
- **Pre-flight refusals** now print "REFUSED … before any change" and no recovery block. If the file layout looks like a previous run's post-swap state, they add a "Do NOT move …key.old back" warning.

**Pre-flight (R3A D-5, R3C D-2): FIXED. Decision: refuse, with the remedy in the refusal.**
- New `rekey_gate.py --unrewritten <copy>`. It runs on a copy (with `-wal`/`-shm`) made before the pause and the first stop; the copy is shredded straight after.
- It refuses on any `enc-v1:` blob in `ConnectionString`.
- **For `BackupTargetUrl` I deviated from the brief:** it refuses only on rows whose `BackupID` names no backup. The source at the tag shows rows of a live backup *are* rewritten: `Backup.cs:54` (LoadChildren) and `Connection.cs:141-142, 892-893, 1773-1810`. Refusing on those would block a re-key the product completes correctly. Attached rows are still counted and printed.
- Refusing beats documenting a remedy because the blob would fail the exit gate only after the key swap, and no re-run could pass it.

**Other pre-flight items: all FIXED.**
- **R3B N-8, R3C N-4 (timer).** `is-enabled` must now be disabled, masked, masked-runtime, not-found or empty, and `is-active` must be `inactive`.
- **R3C N-5 (dry run).** The "decrypt start done" line is guarded; the dry run now says "would be CLEARTEXT … nothing was started".
- **R3C D-4 (hermetic test).** `INSTALLED_UNIT="${REKEY_INSTALLED_UNIT:-…}"`. On a real run the override can only make the pre-flight refuse, because FragmentPath is compared against it.
- **Added beyond the brief:** the pre-flight now refuses identical key files and a `…-key.old` that does not hold the old key.

**Real-path test (R3C D-5): FIXED.** The new suite drives the non-dry-run path through PATH stubs and a fake server on a scratch database, and the real gate judges the copy. Details in section 2.

**NITs:**
- **R3A N-2: FIXED.** The header's step 2 now matches D:1997 and A:234: restoring the pause starts the scheduler, which may queue the overdue job, but the queue runner is paused first.
- **R3A N-8: FIXED.** Gate docstring now cites `Library/Encryption/` and `WipeEncryption.cs` 119-141.
- **R3C N-1: FIXED.** The hand start's secret-format check (`write_params ""`) now runs under `--dry-run` too.
- **R3C N-12: FIXED.** The gate decodes values stored as SQLite BLOBs (`as_text`).
- **R3B N-10: not in my files.** The key-write command is already guarded with `sudo test ! -e … &&` in A:286 and D:2581. The installer's NOTE (C1's file) should get the same guard; I did not check it.

**Also fixed, in my files but not on my list:**
- **R3C N-2:** the gate and the hand start read key files without newline translation and refuse a CR.
- **R3A N-3 (script side):** the hand start's header now lists everything the exit-102 run writes, and its log line no longer claims port 127.0.0.1:PORT is listening.

## 2. Tests: fail before, pass after

The evidence comes from `c2_rekey_mutations.py fail-before`, run against a `git archive c3d0e890` extraction.

- **New suite `tests/test_backup_rekey_real_path.py`: 20 tests.**
  - The happy path checks: keys end as NEW/absent/absent, the gate passes, the drop-in text is exact, a drop-in is present only at the first start, no revert, every copy shredded.
  - 7 pre-flight refusal tests (one of them uses subtests for the four timer states).
  - 9 trap-state tests: pause fails; decrypt start times out *after* the server decrypted; decrypt start command fails; the stop after decrypt fails (F2); chmod after the move fails (F2b); vendor unit after drop-in removal (F3); encrypt start never logs "Server has started"; gate fails; failure after the gate passed.
  - Two of the trap tests then follow the printed "keys not swapped" recovery (start the unit, re-run the script) and confirm it completes. F3 confirms a start under the new key leads to a passing gate.
  - One hermetic dry-run test of the `REKEY_INSTALLED_UNIT` override.
- **Before**, on c3d0e890 with only the override hook added: 18 of the 20 fail. The override test passes, as expected, since the hook is the fix. The "attached BackupTargetUrl rows do not refuse" test also fails there, because the old script never prints the count line.
- **Contract suite, my two classes:**
  - 4 new tests, which fail before: the hand-start dry run runs the secret-format check, the re-key dry run never claims a start happened, a BLOB-typed value is judged, a key file with a CR is refused.
  - 2 new `--unrewritten` tests, which error before because the mode did not exist.
  - The dry-run sequence test now uses the override and checks the new count step and the timer wording; it fails before.
- **After:** everything passes.

## 3. Check results

- `python3 -m unittest tests/test_duplicati_wrapper_contract.py tests/test_backup_rekey_real_path.py`: **62 tests, OK**. That is 42 contract tests, including C1's current ones, plus 20 new.
- `shellcheck` on both changed bash scripts: clean.
- `flake8 --max-line-length=512` on the 4 changed or new Python files: clean.
- CodeQL prescreen: 0 predicted alerts in 3 files.
- `tests/test_ci_test_wiring_drift.py`: **FAILS** until the coordinator wires the new suite in. It also lists `test_duplicati_installer_real_path.py` (C1's).
- Mutations:
  - **Before**: 5 of 13 killed.
  - **After**: 32 of 32 killed. That is M01–M13 re-anchored on the current code, 14 new re-key mutants (N01–N14), 4 gate mutants (G01–G04) and 1 hand-start mutant (P01).
  - Raw results: `<scratchpad>/C2/mut_after.txt`.

## 4. Needed elsewhere

**ci.yml (coordinator)**, inserted after the line `python3 -m unittest -v tests/test_duplicati_wrapper_contract.py`:
```
          # tests/test_backup_rekey_real_path.py: the re-key's NON-dry-run path and every
          # EXIT-trap state (round 3, R3C D-5), against PATH stubs and a fake server on a
          # scratch database; the real exit gate judges the copy. Touches no /etc, /run or unit.
          python3 -m unittest -v tests/test_backup_rekey_real_path.py
```

**docs/REFERENCE.md (coordinator)**
- New bullet: "`tests/test_backup_rekey_real_path.py` -- round 3 of Phase B (R3C D-5): the re-key's non-dry-run path against PATH stubs and a fake server on a scratch database, judged by the real gate. Pins the happy path (keys swapped by `mv`, the old key shredded, the drop-in's `ExecStart=` reset, no `revert`); every pre-flight refusal before the pause (never-rewritten `enc-v1:` blobs, timer enabled in any form or active, an active task, the vendor unit, identical keys, a foreign `.old`); and every EXIT-trap state (key layout read by hash, UNKNOWN after an attempted start, the unit stopped while a drop-in is present, gate counts on failure, one recovery branch, never 'start' after a FragmentPath refusal), following the printed recovery to completion."
- Append to the contract-suite bullet: "; the re-key dry run runs with `REKEY_INSTALLED_UNIT`, so it stays hermetic once the installer has run on a host, and never claims a start happened; the password-init dry run runs the secret-format check; the gate judges a BLOB-typed value and refuses a key file containing a CR, and `--unrewritten` counts the blobs the product never rewrites."

**Prose for D (via the clearing script) and A**
- **Trap (D §8 P0.5b, and A note 6a, replacing "an EXIT trap removes the drop-in and reports what an interrupted run left"):** "an EXIT trap stops the unit while a drop-in is present, removes the drop-in, names each key file by hash (swapped / not swapped / unexpected), reports the database as UNKNOWN once a decrypt or encrypt start was attempted without its 'Server has started' line, prints the gate's counts on a gate failure, and prints only the recovery that applies, never 'start the unit' after a FragmentPath refusal; a refusal before the pause says nothing changed (round 3: R3A D-4, R3B N-11, R3C D-1)."
- **Pre-flight count (D P0.5b, A step 12, and A §8 listing round 2's A DEFECT-4 as now folded in):** "Before the first stop it counts, on a copy of the database, the `enc-v1:` blobs the product's re-encryption never rewrites: any in `ConnectionString`, and in `BackupTargetUrl` rows of no backup (a live backup's rows are rewritten: `Backup.cs:54`, `Connection.cs:892-893`). It refuses if there is one, because such a blob would stay under the old key and fail the exit gate only after the key swap. Remedy, the owner's: record and delete the saved connection strings through the web UI, re-key, then re-create them."
- **Timer (D P0.5b, A step 12):** "and refuses unless the snapshot timer is neither enabled (in any form, `enabled-runtime` and `linked` included) nor active (R3B N-8)."
- **Hand start (R3A N-3, at D:2019, D:2411 and A:238, replacing "sets the password and nothing else"):** "sets the password, upgrades the schema and re-encrypts the password-named server settings under the settings key; the backups' fields and `encrypted-fields` are unchanged until the unit's first start."

## 5. Out of scope

- **R3C N-2, wrapper side (C1).** `scripts/duplicati-wrapper.bash` still passes a CR in the key file through to the server. My gate and hand start now refuse such a file, so the wrapper should refuse it too.
- **Whether to refuse on `ConnectionString` rows is the owner's call.** The remedy text assumes saved connection strings can be deleted through the UI and re-created afterwards; I did not verify that against the product. Nobody has read the Yamaguchi database to see whether it holds any such rows.
- **No slips** against the standing limits. GitHub reads were two files at the Duplicati tag (`Connection.cs`, `Backup.cs`); writes went only under scratch and the files I own.

<!-- markdownlint-enable -->

---

## Round 3's fold-in, lane P — design and assessment prose

Archived verbatim (10,284 characters, sha256 `5df6ddd563783f89`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

I've finished all nine work items in the prose lane. D is regenerated from origin/main (`--from-repo`, then the clearing script), and every check I could run is clean. The two sequence-safety screens did not run: they compare commits, and I may not commit.

**Files**
- **Changed:** D (`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`, regenerated only), A (`notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`, by hand), `util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py`.
- **Added:** `tests/test_clear_stop_backup_design.py`, `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/retention_table.py`, `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/guard_fence_probe.bash`.
- I did not edit `util/ad-hoc/yamaguchi_build_job.py`; prose covers it.

## 1. Per finding

**R3B DEFECT-1 (owner's ruling): FIXED.**
- D step 10's edits remove `retention-policy` (web UI: Keep all backups). D step 11 restores it as `2W:1D,6M:1W,2Y:1M,5Y:2M`, only after AC-4's first drill has passed, and says what the first pass keeps and deletes and that the deletions reach Dropbox.
- §7.5's option list records both changes.
- Every "nothing under `/mnt/Backups/Ubuntu/` is deleted" statement now names the second exception: D front matter (:16), the §8 preamble, P1 step 4 ("single exception"), §10.2 hazard 1, and A §6.0 item 5. A §6.4 steps 11 and 14 mirror the remove and the restore.
- One copy of the sentence is left: D:704, a comment in the unit's tagged block, which belongs to lane C1 (see Needed elsewhere).
- I could not find R3B's port in the repository; it survived only in the old session's scratch directory. I fetched `DeleteHandler.cs`, `Timeparser.cs` and `Options.cs` read-only at tag `v2.4.0.0_stable_2026-09-03` and wrote a new port, `retention_table.py`. Its `--check` reproduces R3B's old-policy table exactly.

**Retention table under the new policy.** First pass at 14:30Z each day, with 2 post-recovery filesets present (the result is the same with 30):

| First pass on | Deletes (of 9) | Keeps | Deleted |
| --- | --- | --- | --- |
| 2026-10-20 to 2027-02-27 | 5 | 08-25T10:27, 09-01T14:00, 09-08T14:00, 09-15T20:48 | 09-12, 09-15T08:56, 09-16T18:33, 09-17T22:13, 09-18T14:00 |
| 2027-02-28 to 03-06 | 6 | 08-25, 09-08, 09-15T20:48 | the above plus 09-01 |
| from 2027-03-07 | 7 | 08-25 plus one other | — |

- Only dlist files are deleted; `--no-auto-compact=true` keeps every dblock and dindex.
- The 09-18 fileset — AC-4's drill target and Procedure A0's source — is among the five deleted.

**R3B DEFECT-2: FIXED.**
- D step 8 stores `paused-until`=`0` with sqlite3 (DELETE then INSERT at BackupID −2) while no server runs: on A0/A/A2 alongside the DBPath update, on B after the hand start. It reads `paused-until` and `startup-delay` back.
- It writes the web credential before the first start, and requires `serverstate` to exit 2 (Paused) after it.
- I confirmed in `LiveControls.cs` that a stored 0 is an indefinite pause.
- "Confirm the 12:00 fire" moved from step 9 to the end of step 10. A §6.4 steps 9–11 mirror all of this.

**R3B DEFECT-3: FIXED (prose).** D step 7 now:
- runs the rebuild tool only while the server reads Paused, with the web credential already written;
- has it run from a scratch copy with every stale default listed: a future 14:00Z `Schedule.Time`, `aes` with `--aes-version` pinned, both sources, the 45 filters, no `retention-policy`, the new tempdir, the Dropbox target, a valid `--record-dir`;
- notes that the import ignores `DBPath`, so the index is re-pointed in the UI afterwards.

A §6.4 step 8 mirrors it.

**R3B DEFECT-4: FIXED.** §7.3.6's recovery now deletes `pbkdf-config` as well, explains why (with it set, `UpgradePasswordToKBDF` changes nothing), and no longer names A2.

**R3B NITs**
- **FIXED:** N-2 and N-3 (residue list); N-4 (P2 step 4 passes `--backup-id`); N-5 (A2 re-enters TargetURL and passphrase after step 9's login, in the UI); N-6 (A step 13 names the gate tool, copies `-wal`/`-shm`, keeps the copy outside `/home/pcalnon`, shreds it); N-7 (the fenced block gains `unset url id`, its own `id=<id>` line and a numeric check — `guard_fence_probe.bash` shows an unsubstituted id, `id=abc` and a failed export each give `guard exit=1`, while `id=7` runs the guard); N-9 (B's step order); N-10 (key write is `test ! -e … && {…}` in D step 8 and A step 9).
- **For other lanes:** N-1 (installer hint) → C1; N-8 and N-11 → C2.

**Round-4 routed question: FIXED.** D step 8 copies every `BMXWPAOGLP.sqlite-wal`, `-journal` or `-shm` beside the index; A §6.3 step 6 says its listing answers whether any exist.

**R3A findings**
- **FIXED:** D-2 (residue list is exactly R4's open rows, adding B22 and the rows at R4 lines 153, 217, 231 and 351, cited by round; note 5b mirrors it; Appendix C says item 4 is applied); D-3 (the 12 job-2 scripts — 8 flag defaults, including `--source-job` in `duplicati_build_fresh_job.py`, and 4 files with 6 hard-coded lines); D-6 (credential format in D step 9 and A step 11); N-3 (the 102 run's real effects, in D and A note 6b); N-6, first half (D §7.8); N-7 (`|| true` in note 6c, I-36 and the §7 check, which now greps `return 0`; AC-6's P2 remnants; note 12b).
- **For the coordinator:** N-1. A §8's Round 2 entry is fixed (the five findings added); the record and CHANGELOG parts are yours.
- **For C1/C2:** N-2, N-4, N-5, N-8, and N-3's log line at hand start :163.

**R3C findings**
- **FIXED:** D-5, clearing-script half (the new suite); N-3 (`FIXFWD_PR` must be `ml#<digits>`, exit 3); N-9 (the script now prints its edit count, prose versus fence); N-10 (A §8); N-11 (a deleted marker needs a `gone` pattern that no longer matches, so a reworded marker on main fails; the STOP block is pinned by sha256 `994ac7a4…`).
- **For other lanes:** N-1, N-2, N-4, N-5, N-12 → C2; N-6, N-7, N-13 → C1.

**Recorded as residue in A §8:**
- R3A N-6, second half: the T2 scheduler header comment; that tagged block comes from a repository file no lane of this fold-in owns.
- R3A N-7's A NIT-6 and R3C N-8: snapshot-script NITs; the script is outside the fold-in's file set.
- R4 line 153: P0 step 8's file-mode sentence, which needs a ruling rather than a prose fix.

A §8 also gains a Round 3 entry (the owner's ruling and the prose fold-in) and a §9 history row.

## 2. Tests
`tests/test_clear_stop_backup_design.py` has 7 tests, all passing. It runs the script in a scratch copy of the repository layout and covers:
- the committed D gives "no change";
- D with one edit reverted is written, equals the committed D byte for byte, and a second run gives "no change";
- an edit inside a fenced block is refused (exit 3);
- a table row pushed over 512 characters is refused (exit 3);
- `FIXFWD_PR` set to `ml#FIXFWD`, empty, `ml#fixfwd`, `ml#21x` or `ml#` is refused (exit 3);
- a reworded deleted marker is refused (exit 1);
- a changed STOP block is refused (exit 1).

**Fail-before evidence** (via `CLEAR_STOP_SCRIPT=<mutant>`). Each mutant fails exactly the tests listed:

| Mutant | Fails |
| --- | --- |
| fence gate off | the stray-fence test |
| `FIXFWD_PR` check reverted to the old exact-placeholder form | 4 `FIXFWD_PR` subtests |
| deletion counted as applied without the `gone` check | the reworded-marker test |
| STOP sha256 check skipped | the STOP-block test |
| width gate off | the over-width test |
| already-applied check off | 4 tests |

## 3. Checks
- **Clearing script:** applied 71, already-present 0; 26 lines wrapped; 20 fenced blocks, 1 changed as declared. Second run: "no change (71 edit(s) already applied)". **Edit count: 71 = 70 prose + 1 fence** (was 54 = 53 + 1). `--from-repo`: 5 rewritten, 9 identical, 1 retagged; `--check` gives "0 staged, 14 already current". Final D sha256 is `da8745d6…`; it will move when C1/C2's tagged files change.
- **markdownlint v0.42.0** on D and A: 0 issues.
- **Structure check:** `markdown_structure_delta.py` itself compares commits, so I ran the check it calls (`2026-09-05_markdown_structure_check.py`) on origin/main's and the working copies: D 0→0, A 0→0.
- **Snippet linter** on D: 14 blocks, 0 failures.
- **flake8** on the changed Python: 0. **shellcheck** on the probe: 0.
- **Unit tests:** `test_duplicati_wrapper_contract`, `test_clear_stop_backup_design` and `test_env_repr_safety` together: 56 tests, OK.
- `test_ci_test_wiring_drift` fails on 3 suites not yet in `ci.yml`, mine among them.

## 4. Needed elsewhere
- **C1, `util/systemd/duplicati.service` comment (D:704):** replace the quoted `"nothing under /mnt/Backups/Ubuntu/ is deleted or moved" rule` with `rule that nothing under /mnt/Backups/Ubuntu/ is deleted or moved beyond its two named exceptions (the job's own retention, the signed-off escrow delete)`.
- **C1, installer:** the NOTE's key write (around install:260-262) should become `sudo test ! -e /etc/credstore/duplicati-settings-key && { umask 077; openssl rand -base64 48 | tr -d '\n' | sudo tee /etc/credstore/duplicati-settings-key >/dev/null; }` (R3B N-10). R3B N-1's hint fix is also C1's.
- **Coordinator, `ci.yml`:** add `python3 -m unittest -v tests/test_clear_stop_backup_design.py`, with a comment: "hermetic gate for the backup design's clearing script: committed design is current, write path idempotent, stray-fence / over-width / FIXFWD_PR / reworded-marker / changed-STOP refusals (Phase B round 3, R3C D-5)".
- **Coordinator, `docs/REFERENCE.md`:** a matching suite entry, and the ad-hoc tools `retention_table.py` and `guard_fence_probe.bash`.
- **Coordinator, AGENTS.md:** suite count +1 for this suite.
- **Coordinator, CHANGELOG and R3 drafts:** the edit count is now "71 edits: 70 prose, 1 fence".
- **Coordinator, A §8:** add C1's and C2's dispositions to my Round 3 entry, including the re-key pre-flight count I described as routed.

## 5. Out of scope
- The scheduler header comment in `util/juniper-backup-scheduled.bash` still omits "before the first success".
- The snapshot script's `?immutable=1` fallback and its `-shm`/`-wal` leftovers (R3C N-8).
- In D step 7 and A step 8 I name the web UI's "Keep all backups" option as the way to remove `retention-policy`. That is from my knowledge of the UI; I did not verify it, because running Duplicati is forbidden.

<!-- markdownlint-enable -->

---

## Round 3's fold-in, lane P (second pass, the code lanes' prose)

Archived verbatim (4,432 characters, sha256 `6d62ba1aff2261b9`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

Second pass is done: every D/A prose item in `C1.md` and `C2.md` (both in `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/`) is folded into D (`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`) and A (`notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`). D is regenerated and every check passes. One item went in differently from your wording: the BEHAVIOUR CHANGE sentence (below).

**Edit count:** still 71 (70 prose, 1 fence). I extended existing edits rather than adding new ones.

**Final D sha256:** `5c98cf27076f291a239479feaa4ac08812a5c493e0b813d0447a3144e4281dac`. It is built from the C1/C2 files as they stand now.

**C1 items, in D (through the clearing script) and A**
- **Clearing note:**
  - "refuses security options there" now reads "accepts only allow-listed tunables there", and the old wording is on the stale-phrase list so it cannot come back.
  - A new paragraph covers wrapper 2.3.0's eight-tunable allow-list and the wider deny list, installer 1.3.0 judging the contract and any existing `/etc/duplicati/env` by running the wrapper, the `.pre-install-<UTC>` copy-aside, the snapshot's single DELETE-mode file (1.2.0), and `ReadWritePaths=` without `-` failing closed with a NOTE.
- **D step 8 and A §6.4 step 9:**
  - An owner caution: before the install, check any existing `/etc/duplicati/env` (option names only, never values). An `--option` line outside the allow-list stops the install and would make every start exit 78.
  - The BEHAVIOUR CHANGE sentence, naming the three changed blessed files and `--update-backup-behavior`.

**C2 items, in D and A**
- **Trap prose:** in the clearing note's item 2, P0.5b, and A note 6a.
- **Pre-flight count:** refuses on any `enc-v1:` blob in `ConnectionString`, and in `BackupTargetUrl` rows of no backup only, with the reason (`Backup.cs:54`, `Connection.cs:892-893`) and the owner's remedy. It is in the clearing note, P0.5b, A note 6a and A §6.4 step 12.
- **Timer prose:** the timer must be neither enabled in any form nor active.
- **Hand start:** C2's "sets the password, upgrades the schema and re-encrypts…" replaces the old wording in the clearing note, D step 6 and A note 6b. "sets the password and nothing else" now occurs 0 times in D and A.

**A §8**
- Round 2's lane A DEFECT-4 is now recorded as FIXED by C2's pre-flight count.
- The Round 3 entry gains C1's and C2's dispositions by finding id, including:
  - R3C N-2 fixed on both sides;
  - R3B N-10's installer half, which you applied;
  - R3C N-13 recorded as a decision (keep no `-`);
  - the unit comment now naming its two exceptions.
- The §9 history row is updated.

**Residue, now recorded in A §8 with reasons**
- **Snapshot `-wal`/`-shm` leftovers:** dropped from residue, because C1 fixed them.
- **R3A NIT-7's A NIT-6 (`?immutable=1`):** stays. Snapshot 1.2.0 did not change how it opens the source, and a fire after a clean close fails closed.
- **R3A NIT-7's C N-2:** stays. The real install still runs `systemd-analyze verify` after installing and blessing; the dry run checks temporary copies first.
- **The scheduler header comment (R3A NIT-6, other half):** stays; it comes from a file no lane owns.
- **The ConnectionString remedy:** whether any such rows exist, and whether the UI route works, is unverified.

**The `is deleted or moved` grep:** five hits, all qualified. D:16, the §8 preamble (D:2242), D:2957, A:210, and D:704, the unit comment, which now says "beyond its two named exceptions".

**Checks**
- Clearing script: second run gives "no change (71 edit(s) already applied)"; `--check` gives "0 staged, 14 already current".
- markdownlint v0.42.0 on D and A: 0 issues. I re-wrapped 7 over-long prose lines in A with the 2026-09-21 wrap helper.
- Structure check: D 0→0, A 0→0.
- Snippet linter: 14 blocks, 0 failures.
- flake8: 0.
- `tests.test_clear_stop_backup_design` plus `tests.test_duplicati_wrapper_contract`: 50 tests, OK.

**Not folded exactly as asked: the BEHAVIOUR CHANGE sentence.** The installer reports BEHAVIOUR CHANGE only when a `.blessed.sha256` already exists. So D and A say it applies "where a `.blessed.sha256` from an earlier install exists", and that a never-blessed host (I-36) has nothing to compare. I don't know whether the owner's host has ever been blessed. Everything else from both reports' "Needed elsewhere" sections that targets D or A is in.

<!-- markdownlint-enable -->

---

## Round 4 — the common brief

Archived verbatim (3,518 characters, sha256 `59b41c4acb1349d8`), lifted from the brief session 097ae87b wrote for round 4's lanes on 2026-10-08 (round 5's lanes used it too).

<!-- markdownlint-disable -->

# Phase B round 4 — common brief (every reviewing lane reads this first)

You are a **read-only adversarial reviewer**. Round 3 found 0 BLOCKER / 15 DEFECT / 32 NIT across three lanes;
its fold-in is now frozen as local commit **`a0ff619c`** on branch `feature/backup-phase-b` in
`/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/golden-floating-willow` (parent:
`origin/main` 81d3fbb3). The whole Phase B change is `git diff origin/main a0ff619c`; the round-3 fold-in
alone is `git diff c3d0e890 a0ff619c` for the files Phase B already had (c3d0e890 is the frozen round-3 head;
the hot files CHANGELOG.md, docs/REFERENCE.md, ci.yml, AGENTS.md were rebuilt from main, so diff those
against origin/main).

Read `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/BRIEF_COMMON.md` for the names (D, A, R4, record, R3A–C,
re-key, gate, wrapper, installer, contract …), how D is generated, and the **owner ruling of 2026-10-08**
(retention suspended through recovery; restored after AC-4's first drill as `2W:1D,6M:1W,2Y:1M,5Y:2M`).
The fold-in lanes' own reports are `C1.md`, `C2.md`, `P.md` in the same directory — treat their claims as
claims to verify, not facts.

## Rules

- **Change nothing in the worktree.** No edits, no git state changes (no add/commit/checkout/stash/reset).
  Write scratch only under
  `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/097ae87b-7a4c-4970-9f46-d052521e17c7/scratchpad/r4-<lane>/`
  (you may copy the repo there, e.g. `git archive a0ff619c | tar -x -C <scratch>`, to run mutations).
- Split git commands into simple single commands (the harness refuses compound ones naming git).
- **Standing limits**, binding absolutely:
  - never start, stop, restart, enable, disable or reload a unit, system or `--user`;
  - never run a Duplicati binary, never contact 127.0.0.1:8300, and no `sudo`;
  - nothing under `/mnt/Backups/Ubuntu/` is read beyond `stat`, and nothing there is touched;
  - never read a secret file: `~/.config/duplicati-backup/*`, any `.env` or `*.env`, `/etc/default/duplicati`
    beyond `stat`, `/etc/credstore`, `/etc/duplicati`, or a data-folder database;
  - never print an environment variable or a token, and never send the owner's email or any credential to an
    external service;
  - no `git stash`; log greps are count-only; no interactive shells (`bash -i` writes `~/.bash_history`);
  - no session performs host actions: those are the owner's.
- Public Duplicati source at tag `v2.4.0.0_stable_2026-09-03` may be fetched read-only from GitHub to verify
  product behaviour; cite file:line.

## Severity

- **BLOCKER**: following D/A as written can damage or lose the sole copy, leak a secret, or leave the host
  unrecoverable; or a shipped script does so.
- **DEFECT**: a step, script or claim is wrong in a way that would make the operator fail, mis-diagnose, or
  rely on a false statement; a test that does not test what it claims.
- **NIT**: accuracy, wording, consistency.

Every finding: what is wrong, file:line evidence (at `a0ff619c`), reproduction where possible, and a remedy.
Say VERIFIED / PLAUSIBLE for each. Also list "Not refuted" (what you tried to break and could not) and
"Unverifiable" (what the limits stopped you checking). A finding you cannot evidence is not a finding.

## Report (your final message)

`# Phase B round 4 — lane <X> (<lens>)`, then: Summary (counts), Findings (BLOCKER / DEFECT / NIT), Not
refuted, Unverifiable, Slips (any limit you came near or broke — say so plainly).

<!-- markdownlint-enable -->

---

## Round 4, lane A — fold-in fidelity

Archived verbatim (12,327 characters, sha256 `c42acd0889cce5a0`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

# Phase B round 4 — lane A (fold-in fidelity)

## Summary

0 BLOCKER, 2 DEFECT, 6 NIT.

- **The round-3 fold-in holds.** Of the round-3 items (R3A 6 DEFECT + 8 NIT, R3B 4 DEFECT + 11 NIT, R3C 5 DEFECT + 13 NIT, plus the handoff's Remaining item 1):
  - every one is FIXED, or recorded as residue in A §8 with a reason, with two exceptions;
  - R3B N-1 is PARTIAL (see N-1 below);
  - R3A N-1's record and CHANGELOG parts are pending, as planned (Disposition of round 3 says "*Pending*"; `CHANGELOG.md` has no Phase B entry at `a0ff619c`).
- **D reproduces exactly.** Starting from origin/main's D, `--from-repo` gives 5 rewritten / 9 identical / 1 retagged. The clearing script then reports "applied 71 … 26 line(s) wrapped … 71 edits: 70 prose, 1 fence", giving sha256 `5c98cf27…`, which equals the committed D. A second run is a no-op, and `--check` reports 0 staged / 14 current.
- **Suites:** 96 tests OK on this host, wiring drift included. markdownlint v0.42.0 is clean on D and A. The AGENTS.md count of 202 matches `ci.yml`, and the drift tool reports 0.
- **Lane claims, re-run:**
  - C1 fail-before: 66 failures, as claimed.
  - C1 after: 31/32 mutants killed. The survivor, I11, is equivalent: `install:302` runs `cmp -s` before the bless.
  - C2 after: 32/32 killed.
  - C2 fail-before: 18 of the real-path tests fail, as claimed. But the suite has **19** tests, not 20 (NIT-6).
- **C2's deviation is VERIFIED** against Duplicati source at the tag:
  - `ReWriteAllFieldsIfEncryptionChanged` (Connection.cs:131-150) iterates `this.Backups` (:1041-1060, every `Backup` row) and calls `LoadChildren`;
  - `LoadChildren` sets `AdditionalTargetURLs = con.GetBackupTargetUrls(id)` (Backup.cs:54; the getter decrypts with `m_key`, :1734);
  - `AddOrUpdateBackup` then calls `SetBackupTargetUrls` (:892-893), which deletes the rows and re-inserts them encrypted (:1773-1810).
  - So only rows of no backup survive the rewrite. `BackupID` is `NOT NULL` with an FK cascade (Schema.sql:188-200), so no row escapes both counts.

## Findings

### BLOCKER

None.

### DEFECT

**D-1. `DUPLICATI_REQUIRE_MOUNT=` does not switch off the wrapper's mount check. The installer's new contract gate, and every wrapper or installer test, therefore depend on `/mnt/Backups` being mounted. VERIFIED.**

- **Cause.** wrapper:80 is `REQUIRE_MOUNT="${DUPLICATI_REQUIRE_MOUNT:-/mnt/Backups}"`. `:-` treats an empty value as unset, so `preflight` still runs `mountpoint -q /mnt/Backups`.
- **Where it bites:**
  - The installer's `wrapper_accepts` (install:162-171) passes `DUPLICATI_REQUIRE_MOUNT=` under `env -i`, and its comment says "no mount is required". That comment is false.
  - The test helper does the same (`tests/test_duplicati_wrapper_contract.py:113`). This part predates round 3, but the real-path installer suite now inherits it.
- **Reproduction.** In a scratch copy I changed only the wrapper's default to `/nonexistent-r4/Backups`, simulating a host without the mount:
  - the wrapper exits 78 with "is not a mountpoint";
  - 10 of 13 installer real-path tests fail, along with most of the InstallerDriftGate and WrapperEnvContract tests.
  - Everything passes here only because this host has `/mnt/Backups` mounted (checked with `mountpoint`).
- **Consequences:**
  - The four suites wired into `ci.yml` should fail on a GitHub runner. This is a prediction: the branch has never run on CI.
  - On the host, an unmounted `/mnt/Backups` at P0 step 8 makes the installer print "REFUSING: the wrapper refuses <contract> … it would exit 78". That misdiagnoses a missing mount as a bad contract (the wrapper's own line does follow).
  - C1's and C2's mutation kill counts are valid only on a host with the mount.
- **Remedy:**
  - pass `DUPLICATI_REQUIRE_MOUNT=/` in the installer and the test helper, or switch the wrapper to `${DUPLICATI_REQUIRE_MOUNT-/mnt/Backups}`;
  - correct the installer comment;
  - add a test that runs with the default mount absent.

**D-2. The new allow-list admits an option the server does not have and refuses the real one. VERIFIED.**

- **What is wrong.** `ENV_OPTION_ALLOW` (wrapper:92) contains `suppress-welcome-page`. At the tag the option is `webservice-suppress-welcome-page`:
  - `WebServerLoader.cs:122`;
  - registered with no alias at `Program.cs:1586`, read at :267.
- **The same wrong name appears in four places:**
  - the contract (line 36);
  - D's tagged blocks (D:934, :1505);
  - the test's `ALLOWED` pin (`tests/test_duplicati_wrapper_contract.py:178`), which pins the hand-copied wrong name, so its "reviewed names" test cannot catch this;
  - `docs/REFERENCE.md`'s "allow-listed tunables".
- **Consequences:**
  - `--suppress-welcome-page` in the env file passes and is ignored by the server with only a warning. That falsifies the wrapper header's new claim that a typo there "fails closed" (wrapper:52-53).
  - The real option is refused with exit 78.
- **Not affected:** the other seven names and all 17 deny entries exist at the tag (47 `CommandLineArgument`s checked).
- **Remedy:** rename the entry to `webservice-suppress-welcome-page` everywhere, and pin the allow-list against the product's option table, not a hand-copied list.

### NIT

- **N-1. R3B N-1 is only PARTIAL. VERIFIED by equivalence.** The installer's printed guard hint (install:341-345) has exactly the form `c3d0e890`'s D fence had (Dold:2446-2450). It lacks D step 10's `unset url id`, `id=<id>` and numeric check (D:2623-2625), which is the R3B N-7 shape R3B reproduced: a stale `url` reaches the guard when `<id>` is pasted unsubstituted. So C1's "shows design step 10's form" and A §8's "the installer's hint is step 10's export-based guard check" both overstate it. **Remedy:** print D's five-line block verbatim.
- **N-2. "Three blessed files" should be four.** D:2606 and A:296 say round 3 changed "the snapshot script, the snapshot unit, a comment in `duplicati.service`". The wrapper is also blessed (install:99) and also changed (2.2.0 → 2.3.0); `cmp` against `c3d0e890` confirms it. A BEHAVIOUR CHANGE run would list the wrapper too, and it is the one real behaviour change in the set.
- **N-3. D:2152 attributes the allow-list to 2.2.0.** It reads "the wrapper (2.2.0) … accepts only allow-listed tunables there". The allow-list is 2.3.0.
- **N-4. The retention window differs between D and A.**
  - D:2637 says the first pass keeps four "between late October 2026 and the end of January 2027".
  - A:319 says "late October 2026 to 2027-02-27".
  - The port (`retention_table.py`, re-run) gives 5 deletions for any first pass from 2026-10-08 through 2027-02-27, so A is right.
  - The ruling itself (removed at D step 10 / A step 11; restored after AC-4's first drill as `2W:1D,6M:1W,2Y:1M,5Y:2M`, replacing `1W:1D,1M:1W,1Y:1M,3Y:2M`) matches across D:16, :1717, :2243, :2618, :2636 and A:210, :309, :318-319, :435.
  - All five "is deleted or moved" sites the handoff listed are corrected.
- **N-5. D gained no history row for this round.** D §12 has no 2026-10-08 row, and note 12c (D:3215-3216) says the fold-in "changed the same set and added `tests/test_clear_stop_backup_design.py` and the evidence scripts". It omits the two other new suites, `tests/test_duplicati_installer_real_path.py` and `tests/test_backup_rekey_real_path.py`. "The same set" is also loose: the defaults file, the timer, and the staging and lint scripts did not change.
- **N-6. Smaller inaccuracies:**
  - C2.md says the real-path suite has 20 tests, and "62 = 42 + 20"; the suite has 19, and 62 = 43 + 19.
  - The PR drafts' file list (`util/ad-hoc/2026-10-04_backup-phase-b-round3/PR_BODY.md:79-81`) still carries 2.2.0 / 1.2.0 / 1.1.0, as do the round-2 prose lines of `PR_BODY.md` and `COMMIT_BODY_ONLY.txt`. The `<<FILE-LISTS>>` placeholder covers re-deriving them.
  - The installer's NOTE key write uses `test ! -s` with no `sudo` (install:316), while D and A use `sudo test ! -e … sudo tee`. It fails safe as a user, but the two forms differ.

## Not refuted

- **R3A:**
  - D-2: the residue list now names B22 and the rows of rounds 5, 6 and 8; note 5b matches; Appendix C says item 4 is applied.
  - D-3: the twelve job-2 scripts are in D and in note 5b, and grep confirms 8 defaults plus 6 hard-coded lines in 4 files.
  - D-4 and D-5: the trap logic and the `--unrewritten` pre-flight were read in full; the trap's branches are consistent with the state flags.
  - D-6: the credential format is in D step 9 and A step 11.
  - N-2, N-3, N-4 (wrapper header), N-5, N-8: fixed.
  - N-6's §7.8 half and N-7: fixed; their residue halves are recorded in A §8 with reasons.
- **R3B:**
  - DEFECT-1 to DEFECT-4: fixed (paused-until with read-back, Paused check, 12:00 confirm moved after step 10; B's rebuild while paused with every default listed; `pbkdf-config` deleted in §7.3.6).
  - N-2 to N-10: fixed.
  - N-11: fixed through R3C D-1.
- **R3C:**
  - D-1 to D-4: fixed; `REKEY_INSTALLED_UNIT` is used by both suites.
  - D-5: fixed; `REFERENCE.md`'s "pins the drift copy-aside" claim is corrected.
  - N-1 to N-12: fixed.
  - N-13: decided, with the reason recorded.
- **Snapshot 1.2.0:** removes only `tmp-*` and `dest-wal` / `dest-shm` residue, never the snapshot itself.
- **Versions:** each artifact's header and HISTORY agree (wrapper 2.3.0, installer 1.3.0, re-key 1.2.0, hand start 1.2.0, snapshot 1.2.0, gate 1.1.0).
- **The eight allow-list names** and the 17 deny names are identical across the wrapper, the contract, D, the test and `REFERENCE.md` (wrong in one name, D-2).
- **Edit count:** 71 = 69 top-level `edit()` calls + 1 in a loop + 1 `fence_edit`, matching the script's own census. The record's "54 / 53" figures belong to round 2's state and are correct there.
- **Collateral damage of C1's allow-list.**
  - Judged only from the repo's history: the env file has only ever shipped `--webservice-port=8300`, which is allowed. The old in-data-folder `.env` carried assignments only (`SETTINGS_ENCRYPTION_KEY`, `_OLD`; D:176, :192), and that file is shredded, not migrated (A:300).
  - So no documented legitimate line is newly refused, apart from D-2's real welcome-page option.
  - The owner is warned before it bites: D step 8 (D:2606) and A step 9 (A:296) say to check option names before the install.
  - The installer refuses an existing `/etc/duplicati/env` that the new wrapper would reject, before it installs anything (install:178-184), and the wrapper's refusal names DAEMON_OPTS.
- **C1's Program.cs citations** hold at the tag: 49-51, 226-237, 1679-1680, 658-659, 690-692 and 986-987.

## Unverifiable

- Whether the suites fail on a GitHub runner (D-1). The branch is local only; the conclusion is a simulation.
- R3B N-7's interactive-shell behaviour for the installer hint (N-1). `bash -i` is forbidden; I rely on R3B's reproduction of the identical shape.
- Whether the accepted 2026-09-18 key has edge whitespace. If it does, the new `check_key_shape` would refuse it on Procedure A, but reading it is forbidden.
- The wrapper header's "0700 gate (Program.cs 200) … before Main's try". At the tag, `PrepareSecureDataFolder` is reached through `GetDatabaseConnection` inside the try at :258-260. Whether `new ApplicationSettings()` at :200 also gates was not traced, and the header already marks this "Unverified".
- The ConnectionString UI remedy, and the database's actual rows. Both are recorded as residue in A §8.

## Slips

- **Harness refusals.** Several compound commands were refused by the harness and re-issued as plain single commands; none ran.
- **Mount check.** One `mountpoint /mnt/Backups` call (metadata only, not under `/mnt/Backups/Ubuntu/`).
- **Network.** GitHub reads only: the Duplicati tree at the tag, `Program.cs`, `WebServerLoader.cs`, `Connection.cs`, `Backup.cs` and `Schema.sql`, plus `gh pr view` on four fleet PRs, all CLOSED.
- **Writes.** Everything went under `scratchpad/r4-A/`, with `PYTHONDONTWRITEBYTECODE=1`. No worktree change, no git state change, no unit, binary, `sudo` or secret file touched.

Scratch evidence is in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/097ae87b-7a4c-4970-9f46-d052521e17c7/scratchpad/r4-A/`:
- `mut1.out`, `mut2.out`: the mutation runs;
- `fb1.out`, `fb2.out`: the fail-before runs;
- `ci/`: the mount-absent copy behind D-1;
- `dup/`: the fetched Duplicati source.

<!-- markdownlint-enable -->

---

## Round 4, lane B — procedure consequences, the sole copy

Archived verbatim (13,791 characters, sha256 `5b17f32c8a3aa7f9`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

# Phase B round 4 — lane B (procedure consequences, the sole copy)

I walked Procedures A0, A, A2 and B at `a0ff619c` in D §8 (`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`) and A §6 (`notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`), step by step, as written. I read every source file at the tag `v2.4.0.0_stable_2026-09-03`. "R3B" is `util/ad-hoc/2026-10-04_backup-phase-b-round3/R3B.md`. I changed nothing in the worktree.

## Summary

**0 BLOCKER, 2 DEFECT, 13 NIT.**

- **The round-3 fixes hold as configuration:**
  - R3B DEFECT-2: `paused-until=0` written with `sqlite3`. The row form and its meaning are right.
  - R3B DEFECT-4: §7.3.6 now deletes `pbkdf-config` too.
  - The `-wal`/`-journal` copy is now in D step 8.
  - The retention ruling is present on all four paths, and `retention_table.py` matches `DeleteHandler.cs`.
- **The new defect.** On A0 and A2, the backup that step 10's `resume` fires is a copy of the job taken at the unit's first start. That is before step 10's edits. So that run carries the old retention policy, the old tempdir and no guard.
  - Nothing is damaged today, but only by accident: A0's old tempdir is read-only under the unit, and A2's copy has an empty `TargetURL`.
  - So for that run, the owner's ruling and "the guard aborts the first backup" are true only by luck.

## Findings

### BLOCKER

None. If A0's old tempdir were writable, DEFECT-1 below would be one.

### DEFECT

**DEFECT-1 — Step 10's edits do not reach the backup that `resume` fires on A0 and A2, and conditionally on B. That run has the old `retention-policy`, the old `--tempdir` and no `--run-script-before-required`. VERIFIED from source; not executed.**

- **What D and A claim** (all of these are false for that run):
  - D:2243: "step 10 removes `retention-policy`, so the first backup deletes nothing".
  - D:2616: "step 8's stored `paused-until` holds it".
  - D:2633: "a missing or failing guard aborts the first backup, which `resume` fires immediately".
  - A:210 and A:318: "it deletes nothing, because step 11 removed `retention-policy`".
- **How the job is queued at the first start, even though the server is paused** (Server `Program.cs`):
  1. The first start comes up Paused. Line 311 calls `LiveControl_StateChanged` directly, and line 1308 sets `appSettings.PausedUntil`.
  2. `SetAndSaveSetting` (`ServerSettings.cs:980-985`, `:209-218`) has no equality check, so it always calls `SetSettings(-2)`.
  3. That leads to `SignalSettingsChanged` (`Connection.cs:431-439`), which calls `IncrementLastDataUpdateId` and `SignalNewEvent`. `SignalNewEvent` raises `NewEvent` synchronously (`EventPollNotify.cs:121-132`).
  4. The service provider is set at line 297 and the scheduler service is built at line 301. Its handler sees the id change and calls `Reschedule()` (`SchedulerService.cs:36-42`).
  5. `Reschedule()` starts the scheduler thread (`Scheduler.cs:121-124`). Its loop queues the overdue job (`:326`, `:356`, `:396`). The task holds `entry = GetBackup(id)`, which loads options, sources and URL eagerly (`Connection.cs:545-565`).
  6. Later edits find the job "already queued" and do not queue it again (`Scheduler.cs:314-324`).
  7. `QueueRunnerService.cs:119` holds the task while paused.
  8. At `resume`, `Runner.cs:786` and `:818` run `data.Backup`. `ApplyOptions` (`Runner.cs:1498-1513`) takes `TargetURL`, `DBPath` and `Settings` from that stale copy.
- **This was half-known.** Note 6a (A:241) records "an overdue schedule is queued at every start". It does not record that the queued copy is frozen at that moment.
- **What each path's first `resume` actually does:**
  - **A0:** the queued run has `retention-policy=1W:1D,1M:1W,1Y:1M,3Y:2M`, `--tempdir=/home/pcalnon/.cache/duplicati-tmp` and no guard.
    - It fails on its first temporary file, because `/home` is read-only under the unit (`duplicati.service:41`, `:51`; the directory is `drwxrwxr-x pcalnon:pcalnon`).
    - `TempFolder.SystemTempPath` checks only that the directory exists (`TempFolder.cs:88-98`).
    - Retention runs only after a completed backup (`BackupHandler.cs:442-452`, `:837`), so nothing is deleted.
  - **A2:** the queued copy's `TargetURL` is empty, so the run fails at once.
  - **On both A0 and A2:**
    - The failed run uses up the overdue slot (`Scheduler.cs` `OnCompletedAsync`).
    - AC-3 then needs a manual run, and no step says so.
    - Step 10's guard dry-run guards nothing on this run.
  - **A is correct.** P0.5b's restarts throw away the queue, and the encrypt start queues a copy taken after the edits.
  - **B:** with a future `Schedule.Time`, nothing is queued, unless the paused session crosses 14:00 UTC. In that case the copy holds whatever `DBPath` and options exist at 14:00.
- **Remedy (either):**
  - **Edit offline.** Make step 10's three job edits in step 8 with `sqlite3`, while no server runs, as `Option` rows for `BackupID=<id>`. None of them is a password-type field, so all are cleartext.
  - **Restart.** After step 10's edits and the dry-run, stop and start the unit. It comes up Paused again because of `paused-until=0`, and the queue is rebuilt from the edited job. Then check `export <id>` and `resume`.

  In either case:
  - Correct D:2243, 2616 and 2633 and A:210 and A:318.
  - Say that AC-3 is a manual run whenever the slot was used up.

**DEFECT-2 — Procedure B's "run Verify files before any backup" cannot be done in the paused window. VERIFIED.**

- **Where the instruction is:** D:2612 says "For Procedure B, run Verify files before any backup … run Repair". A:292-293 says "run Verify files before step 11's resume".
- **Why it cannot be done:** the server is paused from the first start until step 10's `resume`.
  - `POST /backup/{id}/verify` only appends a task (`BackupPost.cs:71`, `:167-168`).
  - Nothing runs while `_isPaused` is set (`QueueRunnerService.cs:119`).
  - So Verify runs only at `resume`, and the operator cannot read its result, or Repair, before then.
  - If 14:00 UTC passed after the rebuild, the scheduled backup is queued ahead of Verify and runs first, from a stale copy (DEFECT-1).
- **Remedy:** say that Verify (and any Repair) executes at `resume`. Do B's `resume` with only Verify queued, check `GetCurrentTasks` or `SchedulerQueueIds` first, finish the session before 14:00 UTC, then `pause`, read the result, and run the first backup by hand.

### NIT

- **N-1 (R3B's second routed question).** The read-back (D:2600-2601) runs after `DELETE`+`INSERT`. It records `startup-delay`, but the previous `paused-until` is destroyed before anyone reads it. Remedy: run `SELECT` before the `DELETE` too.
- **N-2.** D:2637 says "every post-recovery fileset younger than two weeks stays". This is false under `2W:1D`.
  - A fileset less than 24 h after the last kept one is deleted.
  - Reproduced with the port (`scratchpad/r4-B/bin/offschedule.py`):
    - an off-schedule run at 10-09 15:23Z causes the 10-10 14:00Z fileset to be deleted;
    - a second run on the same day is deleted.
- **N-3.** The date ranges for the "keeps four, deletes five" outcome understate it and disagree with each other.
  - D:2637 says "late October 2026 to the end of January 2027", and A:319 says "late October 2026 to 2027-02-27".
  - `retention_table.py --from 2026-10-08` gives the same outcome from 2026-10-08 to 2027-02-27.
- **N-4.** `retention_table.py`'s `outcome()` invents "post-recovery" filesets dated before the recovery when `--recovered-days` is more than the days since recovery.
  - With `--from 2026-10-08 --recovered-days 30` it reports 6 deletions.
  - P.md's "the same with 30" holds only from 10-15.
- **N-5.** D:2242 says "Every destructive step is preceded by a copy". Step 11's retention restore deletes 5 dlists with no copy. Remedy: copy those dlists to a root-only directory outside Dropbox first. With `--no-auto-compact`, the dblocks they reference stay, so the copies keep those filesets restorable.
- **N-6.** D:2611 and A:305 say "If it reads Running … the overdue job may already be queued". If the server is Running, the job is already running. `pause` only suspends it, and step 10's `resume` continues it with stale options. Remedy: stop the unit instead.
- **N-7.** The installer's "Next:" text (`install_duplicati_service.bash:335-345`) prints `systemctl start` without the `paused-until` and web-credential prerequisites, and prints the guard check without the `unset url id` / numeric-`id` gate.
- **N-8.** The A0 scripts copy only the index's main file into their throwaway database (`restore_server_db_from_fileset.bash:31`, `confirm_a0_premise.bash:25`). The fold-in's own step-8 reasoning (D:2597) says a `-wal` or `-journal` holds pages the main file lacks, and step 1's freeze has them.
- **N-9.** D step 10 never pins `--aes-version`, while A:309 and §7.5 (D:1715) require it. This is already on `origin/main`.
- **N-10.** Removing `retention-policy` is enough only if neither `keep-time` nor `keep-versions` is set, in the job or in the common options (`BackupHandler.cs:446`; `GetCommonOptions`).
  - Step 10 should read the options back from `export`.
  - "Keep all backups" removes all three only in the legacy ngax UI (`EditBackupController.js:272-291`).
- **N-11.** §10.2 step 4 (D:2970) still says "877 volumes". That count is stale once step 11 deletes 5 dlists and new filesets are added.
- **N-12.** The index's source path is never named, and the heading "move the index" (D:2584) and A:294's "move … in" contradict the `cp` in the text. A literal `mv` would move the original of the index out of `/usr/lib/duplicati/data`.
- **N-13.** On A0, step 8 needs the root-era password before the first start, to write the credential. The pointer to §7.3.6's lost-password recovery appears only in step 9.

### State per path at `a0ff619c` (A step numbers; D steps in brackets)

| Step | A0 | A | A2 | B |
| --- | --- | --- | --- | --- |
| 1 | Snapshot timer disabled and inactive | same | same | same |
| 5–6 (D 1–2) | Freeze `cp -a` (index plus siblings); `.recovery` snapshot copy; vendor unit stopped; empty folder moved aside | same | same | same |
| 7 (D 3–6) | 09-18 restore through a throwaway index copy (main file only, N-8); destination only read | `cp -a` of root `data/` | Wiped copy | — |
| 9 (D 8) | DB placed; index plus siblings copied (the original index stays in place and in the freeze); `DBPath`; `paused-until=0`; installer; `test ! -e` key; credential; first start Paused, **job queued with the copy taken before the edits** | same, under the old key | same, the copy has an empty URL | Installer, key, folder |
| 10 | — | — | Hand start returns 102; the row survives (exit at `Program.cs:286-288`) | Hand start returns 102, then `paused-until`, credential, first start Paused |
| 11 (D 9–10) | Edits change the database, not the queue; dry-run passes; `resume` → stale run fails on the read-only tempdir, slot used up, nothing deleted, no guard | Edits and dry-run | as A0; stale run fails on the empty URL | Rebuild POST (future Time, nothing queued); Verify queued and blocked; `resume` runs Verify |
| 12 (P0.5b) | — | Restarts drop the stale queue; the encrypt start queues the edited job; `resume` → first backup with guard and no retention | — | — |
| 13 | Copy plus `-wal`/`-shm`; timer `enable --now` | same | same | same |
| 14 (D 11) | AC-3 is a manual run (unstated); AC-4 from 09-18 intact; restored `2W:1D,6M:1W,2Y:1M,5Y:2M` deletes 5 of 9 dlists (09-18 among them), keeps all dblocks | AC-3 is the P0.5b run | as A0 | as A0 |

## Not refuted

- **DEFECT-2 fix (`paused-until=0`).**
  - The row form matches `SetSettings` (`Connection.cs:404-416`; `Schema.sql:72-77`; `SERVER_SETTINGS_ID=-2` at `Connection.cs:57`).
  - `"0"` parses to Ticks 0, which means an indefinite pause (`ServerSettings.cs:231-241`; `LiveControls.cs:192-200`).
  - It cancels the `startup-delay` timer (`LiveControls.cs:186-198`), and every start saves it again (`Program.cs:1308`).
- **The hand start keeps the row.** It returns at `Program.cs:286-288`, before LiveControls exists.
- **DEFECT-4 fix.** With `pbkdf-config` deleted, `UpgradePasswordToKBDF` mints a random password with `autogenerated=True` (`ServerSettings.cs:363-389`), so the hand start returns 102.
- **The retention ruling is present as configuration on all four paths.** Step 10 removes it, B's tool omits it (D:2581), and step 11 restores it for every path.
- **The port matches the remover.** `retention_table.py` matches `DeleteHandler.cs:339-433`; `--check` reproduces R3B's table; and only dlists go (`DeleteHandler.cs:204`).
- **R3B's first routed question is closed.** The `-wal`/`-journal` copy is now in D step 8 (D:2597-2598), A:268 and A:294.
- **B's re-point cannot overwrite the moved index.** `movedb` refuses an existing target (`BackupPost.cs:119-120`).
- **Nothing opens the index's original in place before step 8.**

## Unverifiable

- The stored `startup-delay` value and the common options `keep-*` (both would need the database).
- Whether 2.4's default ngclient UI's "Keep all backups" removes all three retention options.
- Whether a `-wal` or `-journal` exists beside the index.
- DEFECT-1 at runtime: the queueing at first start is shown from source only, since no Duplicati binary may run.
- The exact point where the EROFS-tempdir run fails. Source reading puts it before any upload.

## Slips

None outside the limits.
- **Network:** read-only GitHub reads of `duplicati/duplicati` at the tag (the tree via `gh api`, raw files).
- **Host metadata:** `stat` of `/home/pcalnon/.cache/duplicati-tmp` and `id duplicati`.
- **Scratch only:** `git show origin/main:<D>` was written to scratch, and every script and output is under `scratchpad/r4-B/`.

<!-- markdownlint-enable -->

---

## Round 4, lane C — run the things

Archived verbatim (16,547 characters, sha256 `55589fad85b79344`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

# Phase B round 4 — lane C (run the things)

I checked the code at `a0ff619c` by running it, in scratch extractions under `…/scratchpad/r4-C/`. The worktree is unchanged: HEAD is still `a0ff619c`. The untracked `util/ad-hoc/2026-10-08_backup-phase-b-round4/` was created by someone else during the lane, not by me.

## Summary

**0 BLOCKER, 2 DEFECT, 9 NIT.**

The serious one is DEFECT-1. The two new suites pass only on a host where `/mnt/Backups` is a mountpoint. On CI's `ubuntu-latest`, `/mnt/Backups` is not a mountpoint, so they fail. Every lane so far ran them on the owner's host, where it is.

Check results:

| Check | Result |
| --- | --- |
| `tests/test_duplicati_wrapper_contract.py` | 43 tests, OK on this host |
| `tests/test_duplicati_installer_real_path.py` | 13 tests, OK on this host |
| `tests/test_backup_rekey_real_path.py` | 19 tests, OK. C2.md says 20. |
| `tests/test_clear_stop_backup_design.py` | 7 tests, OK |
| `tests/test_ci_test_wiring_drift.py` | 14 tests, OK |
| `util/ad-hoc/2026-09-10_agents_md_test_list_drift.py` | 0 drift; `AGENTS.md` says 202 and `docs/REFERENCE.md` lists 202 |
| Other duplicati / yamaguchi / tier2 / env-repr suites | All OK, except `tests/test_duplicati_scheduled_backup.py` |
| `tests/test_duplicati_scheduled_backup.py` | 5 failures. The test refuses to stage volumes because this host's `/tmp` is tmpfs. The file is not changed by Phase B, so the failures are unrelated to it. |
| shellcheck (`--severity=warning`) on every changed `.sh`/`.bash` | 0 |
| shellcheck (default severity) on the six named scripts | 0 |
| flake8 `--max-line-length=512` on the 12 changed Python files | 0 |
| markdownlint 0.42.0 (the cached pre-commit environment) on D and A | 0 |
| Snippet linter on D | 14 blocks, 0 failures |
| Idempotence from a fresh `origin/main` D | `--from-repo` gives "5 rewritten, 9 identical, 1 retagged". The clearing script gives "applied 71 … 71 edits: 70 prose, 1 fence". The result is byte-identical to `a0ff619c`'s D (sha256 `5c98cf27…`). A second run reports "no change (71 … already applied)", and `--check` reports "0 staged, 14 already current". |

Mutation kill counts:

| Instrument | Killed | Survivors |
| --- | --- | --- |
| `c1_mutations.py` after | 31 of 32 | I11, which is equivalent, as C1 says |
| `c1_mutations.py` before | 5 of 8 | M16, M19, M20 (matches C1 and R3C) |
| `c2_rekey_mutations.py` after | 32 of 32 | — |
| `c2_rekey_mutations.py` before | 5 of 13 | M07 and M10–M13 killed (matches C2) |
| **My 29 new mutants** (`bin/r4c_mutants.py`) | **17 of 29** | 12, listed below |

My 12 surviving mutants:

- **X12 is a bug, not a test gap.** The mutant deletes `DUPLICATI_REQUIRE_MOUNT=` from the installer, and nothing changes, because that assignment already does nothing. This is DEFECT-1.
- **X21 is equivalent.** Under DELETE mode the post-check cleanup loop has nothing to remove.
- **Ten are untested branches:**
  - X06: CRLF in the env file is no longer stripped.
  - X10: quotes are no longer stripped from `KEY=VALUE`.
  - X11: the env file overrides a variable systemd already set.
  - X15: the pre-install copy loses `cp -p`.
  - X24: the cp-succeeded, mv-failed key layout.
  - X25: an `--unrewritten` crash (exit 2) is treated as a pass.
  - X26: the timer is-active check becomes `!= active`.
  - X40: the "RECOVERY, FIRST" stop line is never printed.
  - X31: an unterminated STOP block gets past the sha gate. The run then probably dies anyway in `replace_stop_block`'s `.index`.
  - X33: the phase-marker `gone` pattern is narrowed to the original wording (see NIT-1).

## Findings

### BLOCKER

None.

### DEFECT

**DEFECT-1. The wrapper cannot switch off its mount check, so two suites depend on the host's mounts and fail on CI. VERIFIED by simulation.**

- **The cause.** `scripts/duplicati-wrapper.bash:80` reads `REQUIRE_MOUNT="${DUPLICATI_REQUIRE_MOUNT:-/mnt/Backups}"`. The `:-` form replaces an empty value as well as an unset one.
- **So "empty means off" is dead code.** `:215` (`if [[ -n "${REQUIRE_MOUNT}" ]]`) is meant to skip the check when the variable is empty, but it never sees an empty value.
- **Every caller that sets it empty still gets the check.**
  - The test helper does this (`tests/test_duplicati_wrapper_contract.py:113`).
  - So does the installer's `wrapper_accepts` (`util/install_duplicati_service.bash:167`). Its comment at `:160-161` says "no mount is required".
  - All of them still run `mountpoint -q /mnt/Backups`. strace confirms it: 76 calls in the contract suite and 46 in the installer suite.
- **Why it passed here.** `/mnt/Backups` is a mountpoint on this host. My mutant X12 survives for the same reason: the assignment it deletes has no effect.
- **Reproduction.**
  - I took a scratch copy (`ci-sim/`) and changed only the wrapper's default to a path that is not a mountpoint.
  - The contract suite then gives `FAILED (failures=35)`, the installer real-path suite gives `FAILED (failures=10)`, and the re-key suite stays OK.
  - Every failure ends at `FATAL: … is not a mountpoint` or at the installer's `REFUSING: the wrapper refuses …contract`.
- **Impact on CI.** `ci.yml` runs both suites in the `tests` job on `ubuntu-latest` (`:158`, `:646`, `:652`). That runner has no `/mnt/Backups` mount, so the PR's required check will fail. The contract suite does not exist on `origin/main`, so this has never run on CI.
- **Impact on a real install.** The installer refuses the contract whenever the backup drive is not mounted during assessment step 9. The message is misleading: it says the wrapper refuses the contract.
- **Remedy.**
  - Change `:80` to `${DUPLICATI_REQUIRE_MOUNT-/mnt/Backups}` (no colon), so a set-but-empty value turns the check off.
  - Add a test that runs `--print-command` with a mount path that does not exist, both with the variable empty and with it unset.

**DEFECT-2. The pre-flight count `--unrewritten` misses orphaned `Option` and `Source` rows, and the test's fake server hides the gap. VERIFIED by reproduction. How far it reaches on Yamaguchi is PLAUSIBLE only.**

- **What the product does.** At the tag, `ReWriteAllFieldsIfEncryptionChanged` (`Connection.cs:131-153`) re-saves each existing Backup with its children, then settings `-1` (`ANY_BACKUP_ID`, `:56`). It re-saves `-2` through the `EncryptedFields` setter calling `SaveSettings` (`ServerSettings.cs:851-888`).
- **Where orphans can sit.** `Option` and `Source` have `BackupID NOT NULL` and **no foreign key** (`Schema.sql:44-45, 72-73`). `BackupTargetUrl`, by contrast, has `ON DELETE CASCADE` (`:199`). So an `Option`/`Source` blob whose BackupID names no backup is never rewritten. That is more likely to exist than the `BackupTargetUrl` orphan C2 chose to refuse on.
- **What the gate does with them.** `rekey_gate.py:113-130` counts only `ConnectionString` and `BackupTargetUrl` orphans, but `gate()` scans every `Option` and `Source` row.
- **Reproduction** (`bin/unrewritten_orphans.py`): one orphaned `Option` (and, separately, `Source`) row holding a blob under the OLD key.
  - `--unrewritten` exits 0 with `ConnectionString.BaseUrl=0 … orphaned=0`.
  - The exit gate then exits 1 with `under-another-key=1`.
  - That is the post-swap failure the pre-flight exists to prevent.
- **The test cannot see it.** The fake server at `tests/test_backup_rekey_real_path.py:94-98` rewrites every `Option` passphrase/pbkdf row and every `Source` row, whatever their BackupID. Its docstring (`:26-29`) says it mirrors the product.
- **Remedy.**
  - Count `Option.Value` blobs whose `BackupID NOT IN (-1, -2, <Backup IDs>)` and `Source.Path` blobs whose `BackupID NOT IN (<Backup IDs>)`, and refuse on either.
  - Make the fake server skip orphaned rows, and add the two cases to the suite.

### NIT

- **NIT-1. The clearing script's `gone` patterns are tied to the wording. VERIFIED.**
  - P.md says "a reworded marker on main fails". It fails only when the rewording keeps "held by the STOP".
  - Reproduction: on `origin/main`'s D, I changed all five phase markers and the P0.5a marker to "blocked behind the STOP". The run printed `ALREADY phase markers: held`, `ALREADY P0.5a marker`, then "applied 69, already-present 2", and D was written with six live STOP markers.
  - Rewording only the five phase markers is refused, but only by accident: the phase-marker pattern also matches the P0.5a marker line, which is still present.
  - The suite's reworded-marker test survives mutant X33.
  - Remedy: use one pattern, `(?im)^\*[^*\n]*\bSTOP\b`, for both edits, and test a rewording that drops "held".
- **NIT-2. D at `a0ff619c` still describes the STOP as in force in three places. VERIFIED.**
  - `:93` — "the STOP at the top of §8 asks whether…".
  - `:373` — "the follow-up behind the STOP at the top of §8 owes one".
  - `:514` — "Held until the STOP at the top of §8 is lifted: S-2's re-key…".
  - Remedy: add edits to the clearing script, or add "the STOP at the top of §8" to `STALE`.
- **NIT-3. A real installer run never says where it copied a file aside. VERIFIED** (`bin/installer_attacks.py`, test I).
  - `act()` prints only under `--dry-run` (`install_duplicati_service.bash:119-127`).
  - On a real run, the `.pre-install-<UTC>` copy and the `.drifted-<UTC>` copy are made with no output naming them. The DRIFT line is printed; the copy's path is not.
  - On this host, assessment step 9 will silently replace `/etc/default/duplicati` (never blessed, and different from the repository copy).
  - Remedy: `say` the aside path in both branches.
- **NIT-4. D says the installer and the wrapper "cannot disagree" (`:2163-2165`). VERIFIED from the code.**
  - `wrapper_accepts` runs as root under `env -i`. The real start runs as `duplicati`, with a credential and systemd's environment.
  - So an existing `/etc/duplicati/env` that is root 0600 passes the installer, which checks `-r` as root (wrapper `:146`). The first start then fails with exit 78: "not readable by duplicati".
  - Remedy: soften the prose, or have the installer also check that the existing file is owned by group duplicati and is group-readable.
- **NIT-5. A missing or empty blessed file bypasses the drift gate. VERIFIED** (test H).
  - A 0-byte blessed file plus an edited installed wrapper gives "first install": exit 0, no DRIFT line, the edit kept only as `.pre-install-*`.
  - The edit is still on disk as the aside, and only root can remove the blessed file.
  - Remedy: treat "blessed file absent but installed files present" as needing `--update-backup-behavior`.
- **NIT-6. A NUL byte in the key file means two keys. VERIFIED** (`bin/nul_key.bash`).
  - The wrapper's `$(<file)` drops the NUL, giving 20 characters, and passes `check_key_shape`. Python reads 21 characters, and neither `read_key` nor the hand start refuses it.
  - This is the same class as R3C N-2 (CR), and is unrealistic for an `openssl rand` key.
  - Remedy: refuse `\0` in both places; in bash, for example, compare `wc -c` against `${#key}`.
- **NIT-7. One allowed value can still carry a CR. VERIFIED.**
  - Only one trailing CR is stripped (wrapper `:149`), so `--log-level=x\r\r` reaches argv as `$'--log-level=x\r'`.
  - CRLF handling is never tested (mutant X06 survives).
- **NIT-8. The hermeticity claims are overstated. VERIFIED by strace (file syscalls only).**
  - `test_backup_rekey_real_path.py`'s `DryRunHermetic` runs the unmodified script, which `stat`s `/etc/credstore/duplicati-settings-key{,.new}`. It gets EACCES here, against the docstring's "Nothing touches /etc" (`:31`).
  - In the contract suite, the installer dry run's advisory `systemd-analyze verify` reads the host's `/etc/systemd/system`, against `:30-32`. This also showed, from a symlink read only, that `timers.target.wants/yamaguchi-server-db-snapshot.timer` exists on this host.
  - No test reads `~/.config`, `/home/duplicati`, or the contents of any secret.
- **NIT-9. Test-count and coverage gaps.**
  - C2.md says the re-key suite has 20 tests; it has 19, and contract plus re-key is 43 + 19.
  - Surviving mutants X24, X25, X26 and X40 mark trap and pre-flight branches that nothing asserts. One of them is the cp-succeeded, mv-failed key layout, which would print "UNEXPECTED layout, do not start" if the predicate regressed.

## Not refuted

- **Hostile env-file lines** (`bin/envfile_attacks.py`: 39 cases under the C, C.UTF-8 and en_US.UTF-8 locales). Every case fails closed or is harmless:
  - leading tabs or spaces, a space around `=`, CRLF, a trailing space, a BOM, `--` alone, `--=x`, a triple dash, and full-width hyphens;
  - a name that extends an allowed name (`--log-level-x`) and an embedded `--disable…` inside a value;
  - NUL inside a denied name, a value with extra `=`, duplicate options (last wins), and `LC_ALL` set from the file;
  - quoted or whitespace-edged keys, and a key with a CR in the middle;
  - a 1 MiB line takes 15–97 s but completes, and 10,000 lines take about 6 s.
- **Unicode lookalikes.**
  - Cyrillic і and о, dotless ı, ſ and İ are all refused. Under UTF-8 the bash range `[A-Za-z]` admits ı and İ, but the allow-list still refuses them.
  - The Kelvin sign K is accepted under en_US.UTF-8, but only because it lowercases to the allowed `--ping-pong-keepalive`, so it is harmless.
- **A NUL-hidden secret in the contract** (`SETTINGS_ENCRYPTION_\0KEY=…`). The installer still refuses it: GNU grep treats NUL as a line break in a binary file.
- **The installer's real path** (stubs reused from the suite):
  - a symlinked unit is copied aside by content, its target is left alone, and it is replaced by a regular file;
  - a symlinked lib directory works;
  - a re-run takes no new asides and keeps the old ones;
  - a failure between install and bless is followed by a clean re-run;
  - an env file symlinked to a file the wrapper refuses is refused;
  - a duplicate entry in the blessed file fails closed (exit 4).
- **The snapshot.** Leftover `-wal`/`-shm` files beside the destination are removed (my mutant X20 is killed). With DELETE mode, the cleanup loop after the integrity check is redundant.
- **The re-key trap and gate.**
  - `key_tag`, DO_NOT_START, STARTED-before-pause, the foreign `.old` check, and a CR in the key are all killed by the suites.
  - The timer is-enabled whitelist, including its empty-string case, is backed up by the strict `== inactive` test.
  - `BackupTargetUrl.BackupID` is `NOT NULL` (`Schema.sql:190`), so the case where `NOT IN` meets NULL cannot occur.
- **The clearing script's FIXFWD form** (mutant X32 killed), the STOP sha gate on a changed block, and its idempotence.

## Unverifiable

- Whether the Yamaguchi database holds orphaned `Option`/`Source`/`BackupTargetUrl` or `ConnectionString` rows: reading it is forbidden.
- CI itself: the branch is local-only. DEFECT-1 is shown by simulation, by changing the default mount path, because I cannot unmount anything (no namespaces, no root).
- How .NET's case-insensitive option matching treats ı or ſ in DAEMON_OPTS. That needs the binary. The env file fails closed regardless.
- How the installer and the re-key behave as root.

## Slips

- **Scripts in tmpfs scratch.** My instruments live only in tmpfs scratch, under `…/scratchpad/r4-C/bin/`: `r4c_mutants.py`, `envfile_attacks.py`, `installer_attacks.py`, `unrewritten_orphans.py`, `nul_key.bash`, `trace_suites.bash`, `run_suites.bash`. The brief requires scratch, but the repository convention wants `util/ad-hoc/`, so they should be copied there before tmpfs is reaped.
- **Host paths touched by the suites, not by me directly.**
  - The suites stat'ed `/etc/credstore/*` (EACCES), ran `systemd-analyze verify` against the host's unit search path, and ran `mountpoint` on `/mnt/Backups`.
  - I ran `mountpoint /mnt/Backups` once myself.
  - Nothing under `/mnt/Backups/Ubuntu/` was touched.
- **No unit, binary, port 8300 or secret content was used.** No state-changing git command was run. The `git show origin/main:D` output went to the scratch copy only.
- **GitHub reads.** I read `Connection.cs`, `ServerSettings.cs` and `Schema.sql`, plus one directory listing, all at tag `v2.4.0.0_stable_2026-09-03`.

**Changed**: no repository file. Documents referenced:
- `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/BRIEF_ROUND4.md`, `BRIEF_COMMON.md`, `C1.md`, `C2.md`, `P.md`
- `util/ad-hoc/2026-10-04_backup-phase-b-round3/R3C.md`
- D (`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`)
- A (`notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`)

<!-- markdownlint-enable -->

---

## Round 4's fold-in, lane C1

Archived verbatim (12,080 characters, sha256 `3b93464dc7601d6e`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

## Lane C1 report: backup Phase B round-4 fold-in

Every round-4 item assigned to me is done, and the four Phase B suites now pass on a simulated host where `/mnt/Backups` is not a mountpoint (101 tests). Nothing on the host was touched, no git command changed state, and all new tests fail against the frozen commit `a0ff619c`.

### 1. Findings

**R4A D-1 = R4C DEFECT-1 (empty mount override ignored): FIXED.**
- `scripts/duplicati-wrapper.bash` is now **2.4.0**. The mount default is `"${DUPLICATI_REQUIRE_MOUNT-/mnt/Backups}"`, so a set-but-empty value really switches the check off. The unit never sets the variable, so production keeps the check.
- **Decision: the installer's `wrapper_accepts` keeps passing an empty value.** It judges the env file's grammar, and a missing mount is not a contract fault. The unit's own start still checks the mount every time.
- The false "no mount is required" comment in `util/install_duplicati_service.bash` (now **1.4.0**) is rewritten to say exactly this.

**R4A D-2 (allow-list had a name the server lacks): FIXED.**
- `suppress-welcome-page` is renamed to `webservice-suppress-welcome-page` in the wrapper, the contract (`util/systemd/duplicati-env.contract`) and the test's `ALLOWED` pin.
- **New fixture:** `tests/fixtures/duplicati_2.4.0.0_server_options.txt`, 50 options.
  - It is the 47 `SupportedCommands` plus the three `secret-provider*` options, with aliases (`parameterfile`, `webservice-allowedhostnames`).
  - Generated by `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/c1_extract_server_options.py` from source fetched read-only at tag `v2.4.0.0_stable_2026-09-03` (commit `b3e9268c…`).
  - The fixture header records the sha256 of each source file.
- **New test:** `test_every_list_entry_is_a_real_server_option_and_every_alias_is_covered` reads the wrapper's own two lists, not the test's copy. Every entry must be a real option or alias, and if a list names part of an alias group it must name the whole group.

**R4A N-1 / R4B N-7 (installer "Next:" hint): FIXED.**
- Before `sudo systemctl start` it now prints step 8's prerequisites:
  - the key in place;
  - `paused-until = 0` read back with `startup-delay`;
  - the web credential in the form `DUPLICATI_WEB_CREDENTIAL=<password>`, mode 0600;
  - the hand start on A2 and B.
- After the start: `serverstate` must exit 2.
- Then design step 10's guard block, verbatim from a heredoc, including `unset url id`, `id=<id>` and the numeric check.

**R4A N-6 (NOTE's key-write command): FIXED.** It is now D's exact form: `sudo test ! -e … && { umask 077; openssl rand … | sudo tee … >/dev/null; }`. It also tells the operator that an empty file is refused on purpose and must be removed by hand.

**R4C N-3 (real run silent about copy-asides): FIXED.** A real run now prints `kept the drifted <dst> as <aside>` or `kept the never-blessed <dst> as <aside>`.

**R4C N-4 (existing `/etc/duplicati/env` readable by the service): FIXED; I chose to enforce rather than soften.**
- The file must be owner root, group duplicati, group-readable, and writable by root only.
- A real run refuses (exit 2) otherwise; a dry run reports `would refuse`.
- Reason: the root-run grammar gate would pass a file that duplicati cannot read, and the first start would then exit 78.

**R4C N-5 (absent or empty blessed file bypassed the drift gate): FIXED.**
- An installed file that differs from the repository and was never blessed is now reported `UNBLESSED` and needs `--update-backup-behavior`, exactly like drift.
- This applies whether the blessed file is absent or empty.
- An installed file identical to the repository still installs quietly.

**R4C N-6 (NUL byte in the key, wrapper side): FIXED.** The wrapper compares `wc -c` with `tr -d '\000' | wc -c` before reading the credential, and refuses on a mismatch.

**R4C N-7 (CR handling): FIXED.** Every trailing CR is stripped from an env-file line, and a CR anywhere else in the line is refused.

**R4C N-8 (tests reading the host's unit tree): FIXED in the tests.** `InstallerDriftGate` puts a `systemd-analyze` stub on PATH, so the dry run's advisory verify no longer reads the host's `/etc/systemd/system`. The real-path suite already stubbed it.

**R4C surviving mutants: all now killed.**
- X06: CRLF lines accepted, no CR reaches the server.
- X10 and X11: tested by actually executing the wrapper against a stub server that prints the `TZ` it received.
- X15: the copy-aside must keep mode and mtime (`cp -p`), checked for both the pre-install and the drift aside.
- X01: lost its anchor after the rename. I added name-extension cases (`--log-level-extra`, `--webservice-port2`) and re-anchored it as R16, which is killed.

### 2. Tests, with fail-before and pass-after evidence

**Changes:**
- **`WrapperEnvContract`**, 7 new tests:
  - fixture pin;
  - empty mount override with the default mount absent;
  - value unquoting and environment precedence;
  - CRLF;
  - NUL in the key;
  - extension cases;
  - the `ALLOWED` rename.
- **`InstallerDriftGate`:** the `systemd-analyze` stub.
- **`tests/test_duplicati_installer_real_path.py`** grows from 13 to 17 tests:
  - UNBLESSED with the blessed file absent or empty, then kept with mode, mtime and the printed path;
  - an identical never-blessed file installs quietly;
  - env-file ownership and mode;
  - an absent backup mount;
  - the verbatim guard block plus the prerequisites;
  - the key NOTE form;
  - the drift aside's mode, mtime and printed path.

**Fail-before:** run against `a0ff619c`'s code, the new tests give **19 failures across 12 tests** (`FAILED (failures=19)`, 45 run). The X10/X11 test passes there; it pins existing behaviour and is what kills those mutants.

**Mutation kill counts:**

| Run | Applied | Killed | Not killed |
| --- | --- | --- | --- |
| `c1_mutations.py after` (round-3 set re-anchored, plus R1–R16) | 47 | 46 | I11, which is equivalent (`cmp -s` runs before the bless) |
| `r4c_mutants.py` on my files, in the ci-sim tree | 15 | 14 | X21, which is equivalent (R4C says so too) |

- In the `after` run, W4 was skipped in the main pass after the rename, then re-anchored and killed in a separate run.
- In the R4C run, X01 and X06 were skipped (no anchor after this round's changes); R16 and R3 cover them, and both are killed.
- R4C's "before" figure for my files was 12 killed of 17 applied.

### 3. Check results
- **On this host:** `tests/test_duplicati_wrapper_contract.py` 51 OK; `tests/test_duplicati_installer_real_path.py` 17 OK.
- **ci-sim** (full worktree copy, wrapper default changed to `/nonexistent-cisim/Backups`):

| Suite | Result |
| --- | --- |
| `tests/test_duplicati_wrapper_contract.py` | 51 OK |
| `tests/test_duplicati_installer_real_path.py` | 17 OK |
| `tests/test_backup_rekey_real_path.py` | 24 OK |
| `tests/test_clear_stop_backup_design.py` | 9 OK |

  Before the fix, R4C measured 35 and 10 failures in the first two suites.
- shellcheck on the wrapper and installer: 0.
- flake8 on my test file, the real-path suite and the two ad-hoc scripts: 0.
- One flake8 E231 remains at `tests/test_duplicati_wrapper_contract.py:645` (`),(` in `test_password_init_dry_run_runs_the_secret_format_gate`). That is lane C2's `RecoveryHelperGates`, not mine.

### 4. Needed elsewhere

**`docs/REFERENCE.md`:**
- No rename is needed: the worktree's REFERENCE.md no longer contains `suppress-welcome-page` (grep finds none).
- In the `tests/test_duplicati_wrapper_contract.py` bullet (line 3553), after "--print-command redacts by option name.", insert:
  > Both option lists are pinned against the product's own table (`tests/fixtures/duplicati_2.4.0.0_server_options.txt`, vendored from Duplicati 2.4.0.0's `Program.cs` with provenance): every entry is a real option or alias, and an alias group is listed whole. An empty `DUPLICATI_REQUIRE_MOUNT` switches the wrapper's mount check off, proven against a copy whose default mount does not exist; CRLF lines, quoted values, environment precedence and a NUL in the key are pinned; the installer dry runs stub `systemd-analyze`, so no test reads the host's unit tree.
- Replace the `tests/test_duplicati_installer_real_path.py` bullet (line 3554) with:
  > - `tests/test_duplicati_installer_real_path.py` -- Phase B round-3/4 fold-in (R3C D-5, N-7, N-8; R4C N-3, N-4, N-5; R4A D-1, N-1, N-6): `util/install_duplicati_service.bash` run for REAL (not `--dry-run`) as a non-root user against a scratch prefix with PATH stubs (`id`, `install`, `systemctl`, `systemd-analyze`, `stat`); pins byte-for-byte install and modes, the blessed checksums, the drift and pre-install copy-asides (bytes, mode and mtime, and the printed path), UNBLESSED (blessed file absent or empty) needing `--update-backup-behavior`, the kept, refused and wrongly-owned existing env file, that an absent backup mount is not a contract fault, the data-folder and credential checks, the key NOTE's `sudo test ! -e` form, step 8's prerequisites before the start and step 10's guard block verbatim, and that the server-DB snapshot of a WAL-mode database leaves no `-wal`/`-shm` beside it. Never reads `/etc`.

CI wiring is unchanged; the suite is already wired.

**D (prose lane, clearing script):**
- In step 8, replace "on a never-blessed host (I-36) there is nothing to compare and it does not." with:
  > on a never-blessed host (I-36) an installed file that matches the repository installs quietly, but one that differs -- this host's `/etc/default/duplicati` does -- is reported **UNBLESSED** and refused the same way, so re-run with `--update-backup-behavior`; the installer keeps the old file as `<file>.pre-install-<UTC>` and says where.
- Extend step 8's existing-env-file sentence:
  > It must also be `root:duplicati`, group-readable and writable by root only (0640); the installer refuses any other owner or mode, because it judges the file as root while the service reads it as duplicati.
- Correct the blessed-file count (R4A N-2):
  > round 3's and round 4's fold-ins changed four blessed files: the wrapper (2.2.0 to 2.4.0), the snapshot script, the snapshot unit and a comment in `duplicati.service`.
- §8 / note 12c, describing this round:
  > Round 4 (2026-10-08): wrapper 2.4.0 makes an empty `DUPLICATI_REQUIRE_MOUNT` switch its mount check off (with `:-` the installer's contract gate and every suite silently depended on `/mnt/Backups` being mounted and would fail on CI); the allow-listed welcome-page tunable is `--webservice-suppress-welcome-page`, the server's real name, and both lists are now pinned against a vendored copy of the product's option table; every trailing CR is stripped and a NUL in the key refused. Installer 1.4.0 refuses an unblessed differing file without `--update-backup-behavior`, checks an existing env file's owner and mode, says where it copied a file aside, and prints step 8's prerequisites and step 10's guard block verbatim. New: `tests/fixtures/duplicati_2.4.0.0_server_options.txt`.
- Note 12c's suite list must include `tests/test_duplicati_installer_real_path.py` (R4A N-5).

**A (§8 and step 9):**
- In step 9, mirror D step 8's UNBLESSED sentence and the env-file owner/mode sentence.
- §8 "Folded in, round 4" should list: R4A D-1, D-2, N-1, N-6; R4B N-7; R4C DEFECT-1, N-3, N-4, N-5, N-6, N-7, N-8; R4C X01, X06, X10, X11, X15.
- No residue from these items.

### 5. Wrong but out of my scope
- The flake8 E231 in lane C2's `RecoveryHelperGates` (line 645).
- R4A N-4 (retention window, D vs A) and R4C NIT-1 and NIT-2 belong to the clearing-script and prose lanes.

**Files changed:**
- `scripts/duplicati-wrapper.bash` (2.4.0)
- `util/install_duplicati_service.bash` (1.4.0)
- `util/systemd/duplicati-env.contract`
- `tests/test_duplicati_wrapper_contract.py` (`WrapperEnvContract` and `InstallerDriftGate` only)
- `tests/test_duplicati_installer_real_path.py`
- `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/c1_mutations.py` (1.1.0: R1–R16, ci-sim mode, id filter)

**Files created:**
- `tests/fixtures/duplicati_2.4.0.0_server_options.txt`
- `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/c1_extract_server_options.py`

<!-- markdownlint-enable -->

---

## Round 4's fold-in, lane C2

Archived verbatim (8,630 characters, sha256 `bd9e19be12cfda6f`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

# Lane C2 report: Phase B round-4 fold-in

All three of your items in my files are fixed. The pre-flight now refuses orphaned `Option` and `Source` blobs (R4C DEFECT-2), and R4C's four surviving mutants are now killed. The mount-check defect (R4A D-1 / R4C DEFECT-1) does not reach my tests.

Mutation results on the current code:
- **`c2_rekey_mutations.py` after-set:** 43 of 43 killed. One defined mutant (G02) was skipped because the code it targets was rewritten; G06 covers the same behaviour.
- **R4C's re-key and gate mutants (`r4c_mutants.py`):** 8 of 8 killed, including X24, X25, X26 and X40. X38 was skipped for the same reason as G02; G06 and G08 cover it.

Files referenced: R4A, R4B and R4C are `util/ad-hoc/2026-10-08_backup-phase-b-round4/R4{A,B,C}.md`. D is `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`. A is `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`.

**Changed**:
- `util/ad-hoc/2026-10-03_rekey_gate.py` (1.1.0 → 1.2.0)
- `util/ad-hoc/2026-10-03_rekey_settings_key.bash` (1.2.0 → 1.3.0)
- `util/ad-hoc/2026-10-03_password_init_hand_start.bash` (1.2.0 → 1.3.0)
- `tests/test_backup_rekey_real_path.py`
- `tests/test_duplicati_wrapper_contract.py`, classes `RecoveryHelperGates` and `RekeyGate` only
- `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/c2_rekey_mutations.py`

## 1. Findings

**R4C DEFECT-2: FIXED.**
- **Gate.** `--unrewritten` (`unrewritten()` and the new `orphans_of()` in the gate) now counts, per table, `enc-v1:` blobs whose BackupID names no backup:
  - `Option.Value`, where -1 and -2 also count as live;
  - `Source.Path`;
  - `BackupTargetUrl.TargetURL`.

  It refuses on any orphan, as well as on any `ConnectionString` blob. Attached rows are printed but do not refuse. If the `Backup` table is absent, every child row counts as an orphan.
- **Verified at tag `v2.4.0.0_stable_2026-09-03` that -1 and -2 are rewritten:**
  - `ANY_BACKUP_ID = -1` and `SERVER_SETTINGS_ID = -2` are defined at `Connection.cs:56-57`.
  - -1 is re-saved directly by the rewrite pass (`Connection.cs:145`).
  - -2 is re-saved through a chain: the `EncryptedFields` setter (`ServerSettings.cs:851-855`) calls `SetAndSaveSetting`, then `SaveSettings` (`:209-218`), then `SetSettings(-2)`. That last call deletes and re-inserts every -2 row with encryption (`Connection.cs:387-407`).
- **Re-key.** The header, the dry-run line and the refusal text now name the orphan rows. The refusal gives the remedy for them: with the server stopped and a copy kept, delete the rows with sqlite3, start the unit, re-run.
- **Fake server** in the real-path suite now rewrites only settings -1/-2 and each existing backup's children, as the product does; its docstring is corrected.
- **Reproduction.** R4C's `r4c-bin/unrewritten_orphans.py`, run against the current tree, now gives `--unrewritten exit=1` (`Option.Value orphaned=1`, then separately `Source.Path orphaned=1`).

**R4C X24, X25, X26 and X40: FIXED** (each with a new test):

| Mutant | What it hid | Test that kills it |
| --- | --- | --- |
| X24 | the cp-succeeded, mv-failed key layout | `test_copy_done_move_failed_reads_as_unswapped_and_recovers` (uses a new `mv` stub; also follows the printed recovery to a successful re-run) |
| X25 | an `--unrewritten` crash (exit 2) passing | `test_refuses_when_the_count_itself_fails`. The script already refused on any exit other than 0 (`case` arms `1)` and `*)`, both `die`); nothing tested it until now |
| X26 | a timer `activating` or `reloading` passing | two cases added to the timer test |
| X40 | the "RECOVERY, FIRST" stop line | `test_trap_stop_fails_prints_stop_first`: the decrypt start times out and the trap's own stop fails |

**R4C NIT-6 (NUL in a key file), Python side: FIXED.** `read_key` in the gate and `write_params` in the hand start both refuse `\0`.

**R4C NIT-8: FIXED.**
- New `REKEY_CREDSTORE_DIR` hook in the re-key. It is honoured under `--dry-run` only; a real run with it set exits 2, because the unit's `LoadCredential=` reads `/etc/credstore` regardless.
- Both dry-run tests now set it, and assert that `/etc/credstore` never appears in the output. The real-path suite's docstring claim ("nothing touches `/etc`") is now true.

**R4A N-6 / R4C NIT-9: CORRECTED.** My round-3 report said 20 real-path tests; there were 19. The suite now has 24: 19 plus 5 new.

**R4A D-1 / R4C DEFECT-1 (wrapper mount check): no effect on my tests.** `RecoveryHelperGates`, `RekeyGate` and `tests/test_backup_rekey_real_path.py` never call the wrapper, and R4C's own mount-absent simulation found the re-key suite still OK.

## 2. Tests: fail before, pass after

Evidence from `c2_rekey_mutations.py fail-before` on an `a0ff619c` extraction. The re-key there got only a test-anchor change: its two `CRED` assignments rewritten into the `CRED_DIR` form, same paths, no behaviour change.

- **Fail on `a0ff619c`:**
  - `test_refuses_an_orphaned_option_or_source_blob` (both subtests). It also shows that without the refusal, the gate fails after the swap.
  - The three new gate tests: orphaned Option/Source counted while -1/-2 are not, no Backup table, NUL key.
  - The hand start's NUL case inside `test_password_init_dry_run_runs_the_secret_format_gate`.
  - Both `DryRunHermetic` tests.
  - The updated dry-run sequence and attached-rows tests.
- **Pass on `a0ff619c`, as expected:** the X24/X25/X26/X40 tests. They pin behaviour that was already there but untested; the mutation kills above are their evidence.

## 3. Check results

- `python3 -m unittest tests/test_duplicati_wrapper_contract.py tests/test_backup_rekey_real_path.py`: **75 tests, OK** (51 contract tests, including C1's current ones, plus 24 real-path).
- `shellcheck` on both changed bash scripts: clean.
- `flake8 --max-line-length=512` on the 4 changed Python files: clean.
- CodeQL prescreen: 0 predicted alerts.

## 4. Needed elsewhere

**D, P0.5b pre-flight sentence** (replaces round 3's "any in `ConnectionString`, and in `BackupTargetUrl` rows of no backup …"):
> Before the first stop it counts, on a copy of the database, the `enc-v1:` blobs the product's re-encryption never rewrites: any in `ConnectionString`, and any in an `Option`, `Source` or `BackupTargetUrl` row whose BackupID names no backup. `Option` and `Source` have no foreign key (`Schema.sql:44-45, 72-73`), so a deleted job's rows can outlive it. The settings rows at -1 and -2 are rewritten (`Connection.cs:145`; `ServerSettings.cs:851-855` → `SetSettings(-2)`), and so are a live backup's rows. It refuses if there is one, or if the count itself fails, because such a blob would stay under the old key and fail the exit gate only after the key swap (R3A D-5, R3C D-2, R4C DEFECT-2). Remedy, the owner's: saved connection strings are deleted through the web UI and re-created after the re-key; an orphaned row, which the UI cannot reach, is deleted with sqlite3 while the server is stopped and a copy is kept.

**A, step 12 and note 6a:**
> The re-key refuses, before anything changes, on an `enc-v1:` blob the product never rewrites: a `ConnectionString` row, or an `Option`/`Source`/`BackupTargetUrl` row of no backup (round 4, R4C DEFECT-2).

**A §8 round-4 entry:**
> R4C DEFECT-2 fixed (orphan count); X24/X25/X26/X40 tested; NIT-6 Python side and NIT-8 fixed (`REKEY_CREDSTORE_DIR`, dry-run only); real-path suite count corrected to 24 (it was 19, not 20, at `a0ff619c`).

**docs/REFERENCE.md** (coordinator):
- Real-path suite bullet: change "never-rewritten `enc-v1:` blobs" to "never-rewritten `enc-v1:` blobs (ConnectionString; Option/Source/BackupTargetUrl rows of no backup) or a failed count". Add "timers `activating`/`reloading`", "the cp-done/mv-failed key layout", "the 'RECOVERY, FIRST' stop line when the trap's stop fails", and "a dry run that stats nothing under `/etc` (`REKEY_INSTALLED_UNIT`, `REKEY_CREDSTORE_DIR`)".
- Contract-suite bullet: add "`--unrewritten` counts orphaned Option/Source rows, not the -1/-2 settings rows; a NUL in a key or secret file is refused".

**CI wiring:** no change from round 3; `tests/test_backup_rekey_real_path.py` must still be in `ci.yml`.

## 5. Out of scope

- **R4C NIT-6, wrapper side (C1).** The wrapper's `$(<file)` still drops a NUL. My readers now refuse such a file, so the wrapper should refuse it too (R4C's suggestion: compare `wc -c` against `${#key}`).
- **The `Option` orphan remedy is a host action for the owner.** It deletes rows with sqlite3. Whether the Yamaguchi database holds any orphaned or `ConnectionString` rows is still unknown, since reading it is forbidden.

<!-- markdownlint-enable -->

---

## Round 4's fold-in, lane P

Archived verbatim (6,397 characters, sha256 `70c446ba94dd5f27`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

My round-4 items are folded in and D is regenerated. Every check passes, except the sequence-safety screens, which compare commits and so I could not run them. Items that belong to C1 and C2 are marked "pending C1/C2" in A §8's new Round 4 entry for you to complete.

**Edit count:** 78 (77 prose, 1 fence), up from 71.

**D sha256:** `5b4dfea085a40ce72991c21cd0998f44a2506f92a58065a8d8d741d3a0dc0b5a`. `--from-repo` now rewrites 7 blocks, because the two A0 scripts changed.

## R4B DEFECT-1: remedy (b), the restart, verified in the Duplicati 2.4.0.0 source
- **The queue does not survive a stop.** It lives only in memory (`QueueRunnerService`, `List<IQueuedTask> _tasks`).
- **`paused-until`=0 survives the restart.**
  - `LiveControls.Init` reads Ticks 0 as an indefinite pause.
  - `Program.cs:311` then calls `LiveControl_StateChanged` with `EstimatedPauseEnd`, which is tick 0 (`LiveControls.cs:318`, `:396`).
  - Line 1308 saves that 0 again.
- **The restart re-queues the edited job.** That save reschedules, and the scheduler takes its copy (`Scheduler.cs:326`, `GetBackup(id)`) from the database at that moment, so after the step-10 edits.
- **Why not (a):** (b) edits through the product instead of writing `Option` rows by hand.

What changed:
- **D step 10** now pins `--aes-version`, removes `keep-time` and `keep-versions` along with `retention-policy` (R4B N-9, N-10), and ends on A0, A2 and B with: stop, start, `serverstate` exits 2, `export <id>` read-back, then `resume`. P0.5b's own two starts do the same job on Procedure A.
- **D:2633** now says the guard aborts the first backup only once the restart has re-queued the job.
- **AC-3 is a manual `run <id>`** whenever the overdue slot was used up. This is stated in D step 10 and A §6.4 step 11.
- **D:2243 and :16, A:210 and :318** now mention the restart.
- **A note 6a** records that the queued copy is frozen at the first start.

## R4B DEFECT-2
B's Verify, and any Repair, runs only at a `resume`. The cycle in D step 8 and A step 8 is:
1. After step 10's restart, confirm `SchedulerQueueIds` holds no backup, and keep the session clear of 14:00 UTC.
2. Queue Verify, `resume`, wait, `pause`, read the result; Repair the same way if needed.
3. AC-3 is then `run <id>` and `resume`.

## Corrected retention table
`retention_table.py` (`--check` still reproduces R3B's table):

| First pass on | Deletes (of 9) | Keeps |
| --- | --- | --- |
| 2026-10-08 to 2027-02-27 | 5 (09-12, 09-15T08:56, 09-16, 09-17T22:13, 09-18) | 08-25, 09-01, 09-08, 09-15T20:48 |
| 2027-02-28 to 03-06 | 6 (adds 09-01) | 08-25, 09-08, 09-15T20:48 |

The result is the same with 30 recovered days now that `outcome()` no longer invents filesets dated before the recovery (N-4). Before the fix, `--from 2026-10-08 --recovered-days 30` reported 6 deletions.

## Other round-4 findings: fixed (D through the clearing script, A by hand)
- **R4B NITs:**
  - N-1: the stored `paused-until` and `startup-delay` are recorded before being replaced.
  - N-2: post-recovery thinning is stated — one fileset a day within two weeks, so a manual AC-3 off the 14:00 slot costs the next day's fileset; weekly after that.
  - N-3: one date range, 2026-10-08 to 2027-02-27, in both D and A.
  - N-5: before the restore, the five dlists are copied to a root-only `/mnt/Backups/Ubuntu/_yamaguchi_retention_aside` with sha256 checked on both sides.
  - N-6: a Running first start means stop the unit.
  - N-8: I took ownership of the two A0 scripts for this fix; each now copies the index's `-wal`/`-journal` into its throwaway. shellcheck 0.
  - N-11: §10.2 step 4's volume count.
  - N-12: the index is copied, never moved, from `/usr/lib/duplicati/data/BMXWPAOGLP.sqlite`, and the step-8 heading says "copy".
  - N-13: the pointer to §7.3.6's recovery is now in step 8.
- **R4A:**
  - N-2: four blessed files changed, the wrapper among them.
  - N-3: the clearing note now attributes the allow-list to 2.3.0 (the `DUPLICATI__*` refusal stays 2.2.0).
  - N-4: the single date range above.
  - N-5: D §12 has a 2026-10-08 row, and note 12c's file and suite lists are corrected.
- **R4C NIT-1:** one `gone` pattern, `(?im)^\*[^*\n]*\bSTOP\b`, for both marker deletions. Two new tests: a rewording without "held" (kills X33) and an unterminated STOP block (kills X31). Both mutants fail the suite; the real script passes 9/9.
- **R4C NIT-2:** R-6, §5's key-candidate sentence and note S-now no longer describe the STOP as in force; "the STOP at the top of §8" is on the stale-phrase list.

## Left for you
- **R4C NIT-4:** "cannot disagree" is withdrawn. D's clearing note has the placeholder `` `<<R4C-NIT-4>>` `` for you to reconcile with C1.
- **Pending C1/C2, recorded as such in A §8:**
  - R4A D-1, D-2, N-1, and N-6's installer-NOTE half;
  - R4B N-7;
  - R4C DEFECT-1, DEFECT-2, NIT-3, NIT-5 to NIT-9.
- **Yours:** R4A N-6's count half (the re-key suite has 19 tests) and the PR drafts' version numbers.
- **R4C's harness:** its scripts are still only in tmpfs scratch and should be copied to `util/ad-hoc/`.
- **No new prose residue from round 4.** The restart remedy rests on reading the source; on the host it is checked by `serverstate` exiting 2 and the `export` read-back.

## Checks
- **Clearing script:** applied 78, then a second run gives "no change". `--check` gives "0 staged, 14 already current".
- **`is deleted or moved` grep:** 5 hits, all qualified, including the unit comment at D:705.
- **markdownlint v0.42.0:** 0 issues on D and A.
- **Structure check:** 0 problems in D and A.
- **Snippet linter:** 14 blocks, 0 failures.
- **flake8 and shellcheck:** 0.
- **Suites:** `test_clear_stop_backup_design`, `test_duplicati_wrapper_contract`, `test_duplicati_installer_real_path`, `test_backup_rekey_real_path`, `test_ci_test_wiring_drift` and `test_env_repr_safety`: 121 tests, OK. The clearing suite re-ran OK after the last change.

**Changed:** D (`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`, regenerated), A (`notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`), `util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py`, `tests/test_clear_stop_backup_design.py`, `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/retention_table.py`, `util/ad-hoc/2026-09-22_confirm_a0_premise.bash`, `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash`.

<!-- markdownlint-enable -->

---

## Round 4's fold-in, lane P (second pass, the code lanes' prose)

Archived verbatim (3,916 characters, sha256 `7ef0df024f5abc2f`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

C1's and C2's round-4 prose is folded into D and A, and D is regenerated with every check passing. The edit count stays at 78 (77 prose, 1 fence), because I extended existing edits rather than adding new ones.

**D sha256:** `4249b301341c2799984068a27c0ed0959d9ef64fc6dd49deb580fc57441f2c20`

**Into D (through the clearing script)**
- **Step 8:**
  - **UNBLESSED sentence:** on a never-blessed host, a file that differs from the repository is refused unless the installer is re-run with `--update-backup-behavior`; this host's `/etc/default/duplicati` is one such file. The old file is kept as `.pre-install-<UTC>`.
  - **Env-file owner and mode:** `root:duplicati`, 0640, and the reason (the installer judges the file as root, the service reads it as `duplicati`).
  - **Four blessed files:** the wrapper went 2.2.0 → 2.4.0.
  - **Versions:** installer 1.4.0, wrapper 2.4.0.
- **Clearing note, `<<R4C-NIT-4>>` resolved:** since 1.4.0 the installer requires an existing `/etc/duplicati/env` to be `root:duplicati`, group-readable and writable by root only, so the grammar check (run as root) and the service's read (as `duplicati`) agree on the file itself. It claims nothing more than that.
- **Clearing note, new round-4 paragraph:**
  - wrapper 2.4.0: the mount override, `--webservice-suppress-welcome-page`, the vendored fixture, CR and NUL handling;
  - installer 1.4.0;
  - re-key 1.3.0, gate 1.2.0 and hand start 1.3.0: the orphan refusal and NUL refusal.
- **Pre-flight sentence:** C2's text is in both the clearing note's item 2 and P0.5b. It covers `Option`, `Source` and `BackupTargetUrl` rows that belong to no backup, a failed count, and the owner's remedy for orphaned rows.
- **Note 12c:** versions are now 2.4.0, 1.4.0, 1.3.0, 1.2.0 and 1.3.0, and it lists the fixture alongside the three suites.
- **§7.7:** the snapshot script is "1.1.0; 1.2.0 since 2026-10-08".
- **Stale-phrase list:** the placeholder and the old "nothing to compare" sentence are added, so neither can come back.

**Into A**
- **Step 9:** the UNBLESSED and env-mode sentences, and versions 1.4.0 / 2.4.0.
- **Note 6a and step 12:** C2's pre-flight sentence.
- **Round 3 entry:** its version mentions are annotated "(2.4.0 / 1.4.0 since round 4)".
- **Round 4 entry:** every "pending C1/C2" item is now FIXED, with the lane named. That covers:
  - R4A D-1, D-2, N-1, N-6;
  - R4B N-7;
  - R4C DEFECT-1, DEFECT-2, NIT-3 to NIT-9;
  - mutants X01 (re-anchored as R16), X06, X10, X11, X15, X24, X25, X26 and X40 killed; X21 and I11 equivalent;
  - suite counts 51 / 17 / 24 / 9.

  No "pending" text is left in D or A.

**Checks**
- **Clearing script:** applied 78; a second run gives "no change"; `--check` gives "0 staged, 14 already current".
- **markdownlint v0.42.0:** 0 issues on D and A.
- **Structure check:** 0 problems in D and A.
- **Snippet linter:** 14 blocks, 0 failures.
- **flake8:** 0.
- **Suites:** 121 tests OK across the six (clearing 9, contract 51, installer real path 17, re-key real path 24, wiring drift, env-repr).
- **`is deleted or moved` grep:** all four remaining hits are qualified.

**Left as written, deliberately**
- Some older version numbers remain as history, not current state:
  - note 12c's 2026-10-03 paragraph lists what that change shipped (wrapper 2.2.0, installer 1.2.0, snapshot 1.1.0);
  - A note 6c says the helper fix was "built in installer 1.1.0";
  - the clearing note says the env allow-list was introduced in 2.3.0.

  If you want "match the files" read literally, those four are the ones to change.
- D:921 sits inside the wrapper's tagged block, which is C1's file, so I did not touch it.

**Changed:** D (`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`, regenerated), A (`notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`), `util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py`.

<!-- markdownlint-enable -->

---

## Round 5, lane A — code confirmation

Archived verbatim (12,886 characters, sha256 `bec151df7c245754`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

# Phase B round 5 — lane A (code confirmation)

I reviewed commit `9ce2f602` against `a0ff619c`. Everything was run on scratch extractions under `scratchpad/r5-A/`. The "ci-sim" copy `cisim/` is a host without the backup mount: its wrapper default points at `/nonexistent-r5a/Backups`, which does not exist.

## Summary

**0 BLOCKER, 2 DEFECT, 6 NIT.**

- **Every round-4 code finding is fixed, and each reproduction now passes.**
- **Suites on the mount-absent ci-sim copy all pass:** contract 51, installer real path 17, re-key real path 24, clearing script 9, wiring drift 14, env-repr 6. `c1_mutations.py cisim` also passes all four suites.
- **`tests/test_duplicati_scheduled_backup.py` still has 5 failures.** These come from `/tmp` being tmpfs on this host, which Phase B does not touch. R4C reported the same.
- **Mutation instruments, all run in ci-sim:**

| Instrument | Killed | What was not killed |
| --- | --- | --- |
| `c1_mutations.py after` | 46 of 47 applied | I11, equivalent, as C1 says. R1 was skipped because my ci-sim edit moved its anchor; I re-ran it by hand and it is killed (contract and installer suites fail). |
| `c2_rekey_mutations.py mutate --set after` | 43 of 43 | G02 skipped, as C2 reports |
| `r4c-bin/r4c_mutants.py` | 24 of 25 | X21 survives, equivalent. X01, X06, X38 and X33 have no anchor any more; their replacements R16, F04/F05, G06/G08 and the new clearing-script tests are killed. |
| My 24 new mutants (`bin/r5a_mutants.py`) | 17 of 24 | Survivors are listed under NIT-3 to NIT-5 |

- **shellcheck** (default severity) on the wrapper, the installer, the re-key, the hand start, both A0 scripts and the `r4c-bin` bash scripts: 0 findings.
- **flake8 `--max-line-length=512`** on the four test files, the clearing script, the gate and the fold-in scripts: 0 findings. The evidence scripts copied into `util/ad-hoc/` have 6 (NIT-6).
- **D is idempotent at the head.** The staging script with `--check` reports "0 staged, 14 already current". The clearing script reports "no change (78 edit(s) already applied)", and D's sha256 stays `4249b301…`.
  - That sha differs from the `5b4dfea0…` in `P_round4.md`, because the `<<R4C-NIT-4>>` placeholder was filled in afterwards. That is expected; the report's sha is simply stale.

## Round-4 code findings, confirmed at 9ce2f602

| Finding | Status | How I checked |
| --- | --- | --- |
| R4A D-1 / R4C DEFECT-1 (mount check could not be switched off) | FIXED | `wrapper:90` now uses `${DUPLICATI_REQUIRE_MOUNT-/mnt/Backups}`. All the ci-sim suites pass. The new tests show: empty means no check, unset means the default mount is required (exit 78), a named non-mountpoint is exit 78. |
| R4A D-2 (wrong welcome-page option name) | FIXED | `webservice-suppress-welcome-page` is now in the wrapper, the contract and the test. I re-fetched the five source files at the tag and re-ran `c1_extract_server_options.py`; it reproduces the fixture byte for byte. The pin test reads the wrapper's own lists. |
| R4C DEFECT-2 (orphaned Option/Source rows) | FIXED | `unrewritten_orphans.py` against the head gives `--unrewritten exit=1` for both the Option orphan and the Source orphan. The fake server now rewrites only the -1/-2 settings rows and live backups. |
| -1/-2 rewrite claim | VERIFIED | `Connection.cs:131-153` at the tag: the backups are re-saved, then `SetSettings(GetSettings(ANY_BACKUP_ID), ANY_BACKUP_ID)`. `SetSettings` deletes and re-inserts every row of that ID (`:384-407`). `GetSettings` decrypts regardless of the option's name. |
| R4C NIT-3, NIT-5; R4A N-1, N-6; R4B N-7 | FIXED | The "kept … as …" lines are printed. UNBLESSED covers an absent or empty blessed file. The guard block matches D:2719-2726 verbatim. The key NOTE matches D:2699 exactly. `installer_attacks.py` passes all its tests on the head. |
| R4C NIT-6 (NUL in the key) | FIXED | `nul_key.bash` now gets wrapper exit 78 "contains a NUL byte". The gate refuses too. |
| R4C NIT-7 (CR handling) | FIXED | `envfile_attacks.py` (39 cases × 3 locales): a double CR is accepted and stripped, a CR mid-line is refused, everything else fails closed as in round 4. The 1 MiB line now takes about 1 s. |
| R4C NIT-8 (tests reading host paths) | FIXED | strace over the three suites (ci-sim): no `/etc/credstore`, no host `/etc/systemd/system`, no `/mnt/Backups`. |
| X24, X25, X26, X40, X10, X11, X15 | KILLED | See the instrument runs above. |

## Findings

### BLOCKER

None.

### DEFECT

**DEFECT-1. The installer's "Next:" hint still says "pause at once" on Running. R4B N-6 changed that to "stop the unit". VERIFIED.**

- **Where the old text remains:**
  - `util/install_duplicati_service.bash:382` prints: "if it reads Running, pause at once."
  - D's embedded copy of the installer carries the same text at D:1499.
- **What D and A now say:** D:2703 and A:315, as round 4 corrected them, say **stop the unit**. The reason they give is that on a Running server the overdue job may already be running, and `pause` only suspends it. Step 10's `resume` would then continue it with its stale options: no guard, old tempdir, old retention.
- **Why it matters:** this hint is the text printed at the very moment the operator does the first start. It directly contradicts round 4's own fix.
- **Not caught by tests:** the hint test (`test_the_next_steps_print_…`) does not check this sentence.
- **Remedy:** print "if it reads Running, stop the unit at once (`sudo systemctl stop duplicati.service`) and record it — do not pause", and assert that sentence in the hint test.

**DEFECT-2. The new owner/mode check on an existing env file enforces one side of an owner decision that is still open (O-12). VERIFIED.**

- **What the code does:** `install:205-214` refuses on a real run (exit 2) unless the file is `root:duplicati`, group-readable and not group- or other-writable. The test pins `duplicati:duplicati:640` as refused (`tests/test_duplicati_installer_real_path.py`, `…cannot_read_stops_the_install`).
- **The decision is still open in four places:**
  - the contract header (`util/systemd/duplicati-env.contract:8-16`): "MODE IS AN OPEN OWNER DECISION … 0600 duplicati:duplicati … 0640 root:duplicati";
  - D P1 item 2 (D:2817): "`0640 root:duplicati` as installed, or `0600 duplicati:duplicati` — the open dissent";
  - A's open-items table, row O-12 (A:359);
  - and D step 8, the round-4 sentence at D:2697, now states the installer "refuses any other owner or mode", which contradicts D:2817.
- **Consequence:** if the owner rules for `0600 duplicati:duplicati`, which is a mode the service can read, every later installer run exits 2 with "make it root:duplicati 0640 first".
- **Remedy (owner's choice):**
  - either accept both documented modes (the service user can read either);
  - or record that the installer settles O-12, and update the contract header, D:2817 and A's O-12 row.
- **Related, part of the same check:** `stat` without `-L` reads the symlink's own `777`, so a symlinked `/etc/duplicati/env` is refused forever with a remedy (`chmod`) that cannot work. It fails closed; the message should say "symlink".

### NIT

- **NIT-1. The installer's messages say "(0640)", but the check also accepts 0644.**
  - The test pins `root:duplicati:644` as passing.
  - The wrapper lets the env file export `SETTINGS_ENCRYPTION_KEY`, and the secret-shape gates run only on the repository contract, not on the existing file. So a world-readable key in `/etc/duplicati/env` passes the installer.
  - This is not a regression, since there was no mode check before. But adding `& 8#004` to the refusal costs nothing.
- **NIT-2. The hint's NOTE for Procedure A says "place the accepted 09-18 key instead" and omits the random `…-key.new` that D step 8 also requires.**
- **NIT-3. Test gaps in the wrapper and installer (mutants that survive):**
  - **F01:** the wrapper's production default emptied (`${DUPLICATI_REQUIRE_MOUNT-}`) survives. No test pins `/mnt/Backups`, because `_wrapper_with_default_mount` replaces whatever the default is. `RequiresMountsFor=/mnt/Backups` in the unit still holds the line.
  - **F07:** dropping the group condition (so `root:root:0640` is accepted, which duplicati cannot read: exactly R4C N-4's case) survives. The refused-meta list has no `root:root:640` case.
- **NIT-4. Test gaps in the recovery helpers:**
  - **F19:** the hand start's NUL check limited to the password survives; only the password file gets a NUL in the test.
  - **F22 / F23:** removing the A0 scripts' new `-wal`/`-journal` copy, or copying it under the wrong name, survives. No suite exercises either A0 script.
- **NIT-5. Survivors of little consequence:**
  - **F14:** `Source` rows at -1/-2 counted as attached. Such rows are unrealistic.
  - **F21:** `REKEY_CREDSTORE_DIR=""` honoured (`+x`). A real run then exits 2 anyway, so it fails safe.
- **NIT-6. The evidence scripts copied into `util/ad-hoc/` fail flake8 at 512:**
  - `r4b-bin/offschedule.py` (E401, E702 ×2);
  - `r4c-bin/envfile_attacks.py` (F401);
  - `r4c-bin/installer_attacks.py` (F401, E201, E303).
  - The pre-commit flake8 scope is `^(scripts|tests)/`, so nothing gates them.

## Not refuted

- **The UNBLESSED gate on this host.** `/etc/default/duplicati` is `duplicati:duplicati 0644`, 404 bytes (stat only). No `/usr/local/lib/duplicati`, `/etc/duplicati` or `/etc/systemd/system/duplicati.service` exists.
  - So a real run reports only `UNBLESSED: …/etc/default/duplicati` and exits 4, with the "re-run with --update-backup-behavior" text.
  - Re-running with the switch keeps a `.pre-install-<UTC>` copy (`cp -p`), installs, and blesses.
  - D:2699 and A:305 tell the operator exactly this. A file identical to the repository installs quietly. I see no trap.
- **The NUL check** (`wc -c` vs `tr -d '\000'`). It is bytewise, a trailing newline is unaffected (F03 is killed), and it runs before `$(<file)`.
- **CR stripping.** Every trailing CR is removed, a CR mid-line is refused, and the refusal prints no value (F04 and F05 are killed).
- **The orphan SQL:**
  - `BackupID` is `NOT NULL`, and a NULL would count as an orphan (fails closed);
  - an absent `Backup` table makes every child row an orphan (F15 is killed);
  - -1 and -2 are each needed (F17 and F18 are killed);
  - `sqlite3.Error` gives exit 2, and the re-key refuses on any exit other than 0.
- **`REKEY_CREDSTORE_DIR` cannot leak into a real run.** It is checked right after argument parsing, before anything changes: set on a real run, it exits 2; empty, it is ignored. `sudo` resets the environment anyway. No other `/etc/credstore` literal remains in the script.
- **The fake server mirrors the product's scope**, at the gate's level: -1/-2 plus live backups only; orphans and `ConnectionString` are untouched.
- **The A0 scripts:** the `-wal`/`-journal` copy happens before the open, and both are included in the final `rm`.
- **The installer and the clearing script hold:** the guard block is verbatim, the "gone" pattern change is killed by its tests, and the staged copy of the installer inside D is current.

## Unverifiable

- **CI itself.** The branch is local, so the ci-sim run is a simulation by changing the default path.
- **Behaviour under root.** I could not run the installer's real path or the re-key as root.
- **Whether the Yamaguchi database holds orphaned rows.** Reading it is forbidden.

## Slips

- **Harness refusals.** Several compound commands were refused by the harness and re-issued as plain ones; none of the refused ones ran.
- **The R1 re-run.** It ran in a ci-sim copy, so the default mount was a nonexistent path; nothing on the host was checked.
- **Host access:**
  - `stat` only on `/etc/default/duplicati` and the other installer destinations (metadata, no content);
  - no unit, Duplicati binary, `:8300` connection, `sudo` or secret content;
  - nothing under `/mnt/Backups` touched; the ci-sim strace shows no access to it.
- **Network.** GitHub raw reads of `Connection.cs`, `Program.cs`, `WebServerLoader.cs`, `DataFolderManager.cs`, `Util.cs` and `Options.cs`, all at tag `v2.4.0.0_stable_2026-09-03`.
- **Worktree.** No change and no git state change. The untracked `R5B.md` and `r5b-bin/` were written by another lane.
- **Scripts in tmpfs.** My scripts are only in tmpfs scratch, under `scratchpad/r5-A/bin/`: `r5a_mutants.py`, `run_suites.bash`, `mk_cisim.bash`, `idem.bash`, `fetch_and_extract.bash`. Copy them to `util/ad-hoc/` if they should be kept.

**Documents referenced:**
- `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/BRIEF_ROUND4.md`, `C1_round4.md`, `C2_round4.md`, `P_round4.md`
- `util/ad-hoc/2026-10-08_backup-phase-b-round4/R4A.md`, `R4B.md`, `R4C.md`
- D: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`
- A: `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`

**Changed:** no repository file.

<!-- markdownlint-enable -->

---

## Round 5, lane B — procedure confirmation

Archived verbatim (14,455 characters, sha256 `a2b2eb4c8b3ee6d0`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

# Phase B round 5 — lane B (procedure confirmation)

I reviewed local commit `9ce2f602`, and the delta `git diff a0ff619c 9ce2f602` for D (`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`) and A (`notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`). The baseline is the "State per path" table in R4B (`util/ad-hoc/2026-10-08_backup-phase-b-round4/R4B.md`). I fetched the Duplicati source again, read-only, at `v2.4.0.0_stable_2026-09-03`, into `scratchpad/r5-B/src/`. I changed nothing in the worktree, and `git status` is clean after the run.

## Summary

**0 BLOCKER, 2 DEFECT, 6 NIT.**

- **Every round-4 procedure and prose finding in my lens is fixed:**
  - R4B DEFECT-1 and DEFECT-2, and R4B N-1 to N-13;
  - R4A N-2 to N-5;
  - R4C NIT-1, NIT-2 and NIT-4.
- **The step-10 restart holds up against the source.** It loses nothing, the stored pause survives it, and the overdue job is queued again from the edited database.
- **D regenerates byte-for-byte**, `4249b301…`, and the clearing script is idempotent.
- **markdownlint v0.42.0 is clean** on D and A.
- **The retention ruling and the table are stated the same way everywhere** in D and A.
- **What the delta did not fix:**
  - The new read-back cannot see the server's default options, although D says it does (DEFECT-1).
  - Repair, which the delta's text touches again, deletes remote files. That contradicts "exactly two exceptions" (DEFECT-2).

## Findings

### BLOCKER

None.

### DEFECT

**DEFECT-1 — `export <id>` cannot show "the server's default options", so the check that no `retention-policy` / `keep-time` / `keep-versions` remains there checks nothing. Mechanism VERIFIED from source; impact PLAUSIBLE (what the defaults hold is unknown).**

- **What D says.** D:2733 says to read the edits back with `export <id>`, with "no `retention-policy`, `keep-time` or `keep-versions`, in the job or in the server's default options". A:320 and A:331 remove the three options from the job only.
- **What export returns.** `GET /backup/{id}/export` serialises `PrepareBackupForExport` (`Connection.cs:204-216`): `Backup`, `Schedule` and `DisplayNames` only.
- **What a run uses.** The defaults are the `BackupID=-1` rows (`Connection.Settings` → `GetSettings(ANY_BACKUP_ID)`, `Connection.cs:1098-1101`). They join every run through `ApplyOptions(…, GetCommonOptions(…))` (`Runner.cs:818`, `:1584-1590`).
- **Why it matters.** If the restored root-era database (A0) carries any of the three in its defaults, the first backup's retention pass still runs. It can delete the drill target, and the operator's read-back reports clean. R4B left these defaults "Unverifiable" for the same reason.
- **Remedy (either):**
  - In step 8, while no server runs, use the same `sqlite3`: `SELECT "Name","Value" FROM "Option" WHERE "BackupID" = -1 AND ltrim("Name",'-') IN ('retention-policy','keep-time','keep-versions');`. Delete any row it finds, keeping a copy.
  - Or read the effective options with `GET /api/v1/backup/<id>/export-cmdline`. It is Bearer-authorised and built from `GetCommonOptions` (`BackupGet.cs:277-283`, `Runner.cs:640-646`). The API client has no verb for it.

  In both cases, drop "in the server's default options" from the `export` sentence, and add the defaults to A §6.4 step 11.

**DEFECT-2 — Repair deletes remote volumes that the index does not know. D and A still say nothing under `/mnt/Backups/Ubuntu/` is deleted except two things. VERIFIED from source. This predates round 4, but the delta re-touched it ("run Repair the same way").**

- **The mechanism.** `RepairHandler.cs:299` loops over `tp.ExtraVolumes`, and `:397` calls `backendManager.DeleteAsync(n.File.Name …)` unless `--dry-run` is set (`:400`).
- **Where it applies.** D step 8 (D:2706-2707) and A:297 tell Procedure B to run Repair if Verify finds the index inconsistent. That is exactly the case in which extra volumes exist.
- **The contradiction.** D:2324 ("exactly two exceptions") and A:210 (§6.0 item 5) are both false on that branch.
- **The case to worry about.** The index's last writer may have stopped uncleanly (D step 8's own `-wal` reasoning). Its 09-18 dlist could then be an "extra" volume, and that is AC-4's drill target.
- **Remedy:**
  - run Repair with `--dry-run` first and read the `WouldDeleteFile` lines;
  - copy every named file to the aside directory before a real Repair;
  - name Repair as a third, conditional exception in D:2324 and A:210.

### NIT

- **N-1. The installer's "Next" text contradicts the N-6 fix and leaves out the restart. VERIFIED.**
  - `util/install_duplicati_service.bash:382` (and D's fence, D:1499) still says "if it reads Running, pause at once". D step 8 now says stop the unit, because `pause` only suspends the job and `resume` would continue it.
  - Its item 4 goes straight from the guard dry-run to "resume" and omits step 10's stop-and-start.
  - Remedy: print "stop the unit (`sudo systemctl stop duplicati.service`)" and add "then step 10's restart" after the guard block.
- **N-2. A:334 says a manual AC-3 "off the 14:00 slot costs the next day's". That holds only for a run after 14:00. VERIFIED** (`scratchpad/r5-B/bin/morning_ac3.py`, using `retention_table.py`'s `to_delete`).
  - AC-3 at 10:00 → the same day's `10-12T14:00` is deleted.
  - AC-3 at 15:20 → `10-13T14:00` is deleted.
  - D:2737's 15:20 example is correct. Remedy: in A, say "the next 14:00 fileset within 24 h".
- **N-3. The orphan remedy says "a copy is kept" with no place and no shred** (D:2201, D:2800, A:247-248).
  - On Procedure A, that copy holds `enc-v1:` blobs under the compromised 09-18 key.
  - Step 13's discipline should apply: a root-only 0700 directory outside `/home/pcalnon` (the backup Source), `shred -u` after the gate passes, and the unit stopped and then started again (it comes up Paused).
- **N-4. B's Verify cycle has no remedy if `SchedulerQueueIds` already holds a backup** (D:2706, A:297). It only says "keep clear of 14:00".
  - A restart alone re-queues it, because the job is overdue and `LastRun` is written only on completion (`Scheduler.cs:218-232`).
  - Remedy: move the schedule's `Time` to the next day's 14:00, restart, and confirm the queue is empty.
- **N-5. "Rounds 3 and 4 changed four blessed files" (D:2698, A:304) is counted from `c3d0e890`, which was never on `main`.**
  - Against `origin/main`, whose installer also blesses files (wrapper 2.0.0, installer 1.0.0), six of the seven differ: all but the guard.
  - This is moot on this never-blessed host (I-36), but wrong for any host installed from `main`.
- **N-6. A:212 says the server is "never restarted before step 10".** Step 8's Running remedy (stop the unit, check `paused-until`, start again) is such a restart. Remedy: add "except step 8's stop when it reads Running".

### Round-4 items in my lens: confirmed fixed

- **R4B DEFECT-1** — D:2712, D:2731-2734, A:320-325; the source chain is re-verified under "Not refuted".
- **R4B DEFECT-2** — D:2706-2707, A:297.
- **R4B NITs:**
  - N-1: `SELECT` before `DELETE`, at D step 8 and A step 9.
  - N-2: thinning stated, but see N-2 above for A's wording.
  - N-3 and R4A N-4: one range, 2026-10-08 to 2027-02-27, in both D and A.
  - N-4: re-run with `--recovered-days 30` → 5 deletions.
  - N-5: the aside copy.
  - N-6: stop on Running.
  - N-7: the installer prerequisites, apart from N-1 above.
  - N-8: both A0 scripts and D's fences copy `-wal`/`-journal`.
  - N-9: `--aes-version` pinned in D step 10. `aes-version` exists at `AESEncryption.cs:43`.
  - N-10: covers the job only (DEFECT-1).
  - N-11: §10.2 step 4.
  - N-12: `cp`, never `mv`, from the named path; no "move/moved index" remains.
  - N-13: the §7.3.6 pointer in step 8.
- **R4A N-2** — four blessed files (see N-5 above).
- **R4A N-3** — the allow-list is 2.3.0, and `DUPLICATI__*` is 2.2.0.
- **R4A N-5** — D §12 has a 2026-10-08 row. Note 12c lists the three suites and the fixture, and its unit changes are comment-only (checked with a `c3d0e890..9ce2f602` diff).
- **R4C NIT-1** — `MARKER_GONE = r"(?im)^\*[^*\n]*\bSTOP\b"` at clearing script:554, used for both edits; `tests/test_clear_stop_backup_design.py` runs 9 tests, OK.
- **R4C NIT-2** — D:93, :373 and :514 were rewritten.
- **R4C NIT-4** — installer 1.4.0 checks owner, group and mode, and D says "agree on the file itself".

### State per path at `9ce2f602` (A step numbers; D steps in brackets)

| Step | A0 | A | A2 | B |
| --- | --- | --- | --- | --- |
| 1 | Snapshot timer disabled and inactive | same | same | same |
| 5–6 (D 1–2) | Freeze (`cp -a`, index plus siblings); vendor unit stopped once; empty folder moved aside | same | same | same |
| 7 (D 3–6) | 09-18 restore through a throwaway index copy, now with `-wal`/`-journal`; destination only read | `cp -a` of root `data/` | Wiped copy | — |
| 9 (D 8) | DB placed; index `cp`'d with siblings, original stays; `DBPath`; old `paused-until`/`startup-delay` recorded, then `0`; installer (UNBLESSED refusal → `--update-backup-behavior`, aside path printed); key `test ! -e`; credential (§7.3.6 if the password is unknown); first start Paused; **stale copy queued** | same, under the old key | same; the stale copy has an empty URL | Installer, key, folder |
| 10 | — | — | Hand start returns 102 | Hand start returns 102, then `paused-until`, credential, first start Paused |
| 11 (D 9–10) | Edits (tempdir, guard, aes-version, no retention / keep-* **in the job only — the defaults are unchecked, DEFECT-1**); guard dry-run; **restart → stale copy gone, pause kept, re-queued from the edited DB**; `export` read-back; `resume` → first backup with guard and no retention | Edits and dry-run | as A0 (TargetURL re-entered in step 9, before the restart) | Rebuild (future Time); restart; queue empty; Verify → `resume` → `pause` → read (Repair deletes extras, DEFECT-2); `run` and `resume` = AC-3 |
| 12 (P0.5b) | — | Two starts drop the stale copy; the closing `resume` runs the edited job | — | — |
| 13 | Gate on a copy plus `-wal`/`-shm`; timer `enable --now` | same | same | same |
| 14 (D 11) | AC-3 is the post-restart run (manual if it failed); AC-4 from 09-18 intact; **five dlists copied to `_yamaguchi_retention_aside`**, then `2W:1D,6M:1W,2Y:1M,5Y:2M` deletes those five, keeps four and all dblocks | same | same | same |

## Not refuted

- **Stopping mid-session loses nothing:**
  - The queue is in memory only (`QueueRunnerService._tasks`; `Terminate` at `:103-113`).
  - Shutdown never writes `PausedUntil` (`Program.cs:405-430`).
  - The queued stale task never started, because `StartNextTask` returns while `_isPaused` (`:119`).
  - The schedule's `Time`/`LastRun` are written only in `OnCompletedAsync` (`Scheduler.cs:218-232`), so the job is still overdue after the restart and is queued again.
- **`paused-until=0` survives:**
  - `Init` with Ticks 0 → Paused, with the startup-delay timer cancelled (`LiveControls.cs:191-200`).
  - Line 311 → `LiveControl_StateChanged` → `PausedUntil = EstimatedPauseEnd` = Ticks 0 → saved as `"0"` (`Program.cs:1308`; `ServerSettings.cs:231-240`).
  - The API `pause` with no duration also stores 0 (`ServerState.cs` `ExecutePause` → `Pause(bool)`).
  - `SetAndSaveSetting` has no equality check (`ServerSettings.cs:980-985`), so `SignalSettingsChanged` (`Connection.cs:434-441`) → `Reschedule`.
- **No early-start race between scheduler creation (`Program.cs:301`) and the pause (`:311`):**
  - the update poll waits a minute (`UpdatePollThread.cs:99`);
  - the purge and certificate timers first fire after an hour (`Program.cs:545-590`).
- **AC-1's `NRestarts=0` is not affected.** `NRestarts` counts only systemd's automatic restarts, not an operator stop/start.
- **The retention aside fits §8.** It is a copy (no delete or move) to `/mnt/Backups/Ubuntu/_yamaguchi_retention_aside`, outside the Dropbox root. The operator makes it with `sudo` from the host, so the unit's `ProtectSystem=strict`/`ReadWritePaths` (`duplicati.service:40`, `:51`) do not apply. Root 0700 keeps it from `duplicati`, and the guard's stray check covers only the destination directory.
- **The retention table.** Re-run, `retention_table.py` gives 5 deletions for every first pass from 2026-10-08 to 2027-02-27, and 6 from 2027-02-28. The default run and `--recovered-days 30` agree, and `--check` reproduces R3B. The ruling (removed at D step 10 / A step 11; restored after AC-4's first drill as `2W:1D,6M:1W,2Y:1M,5Y:2M`, replacing `1W:1D,1M:1W,1Y:1M,3Y:2M`) reads the same at D:9-10, 1783, 2324, 2735-2736 and A:210-211, 331-334, 450. D:118 is the historical snapshot.
- **Verify and Repair are queued tasks** (`BackupPost.cs:71`, `:168`, `:206`). The guard passes them (it checks only mount, URL and stray files).
- **D regeneration.** `git archive 9ce2f602` → reset D from `origin/main` → `stage --from-repo` (7 blocks rewritten) → clearing script ("applied 78") gives sha256 `4249b301…`, identical to the commit. A second run reports "no change".
- **markdownlint 0.42.0** (from the pre-commit cache) on D and A, with `.markdownlint.yaml`: rc 0, no findings.
- **The suite counts A §8 states.** Contract, installer and re-key run 92 tests together (= 51 + 17 + 24), OK. The clearing-script suite runs 9, OK.

## Unverifiable

- The `BackupID=-1` default options in the restored or root-era database (DEFECT-1's actual exposure). Reading it is the owner's.
- Whether 2.4's ngclient "Keep all backups" removes all three options. D's "only the legacy UI" asserts that it does not, and that is unverified.
- The ACLs on `/mnt/Backups/Ubuntu/` that the aside directory would inherit (reading them is beyond `stat`).
- Whether the index has extra or missing volumes against the destination (DEFECT-2's trigger).
- Everything at runtime: the restart's re-queue is shown from source only.

## Slips

None.
- **Network:** read-only raw GitHub fetches at the tag, into `scratchpad/r5-B/src/`.
- **Scratch:** the regeneration copy is under `scratchpad/r5-B/regen/` and the probe script is at `scratchpad/r5-B/bin/morning_ac3.py`.
- **Worktree:** markdownlint ran without `--fix`, and the test suites ran from the worktree, which stayed clean.
- **Never done:** no unit was touched, no Duplicati binary was run, and no secret was read.

**Changed**: none. **Created** (scratch only): `scratchpad/r5-B/bin/morning_ac3.py`, `scratchpad/r5-B/D.wdiff`, `scratchpad/r5-B/regen/`, `scratchpad/r5-B/src/`.

<!-- markdownlint-enable -->

---

## Round 5's fold-in, lane C1

Archived verbatim (8,449 characters, sha256 `8aaf94ad79720e05`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

## Lane C1 report: backup Phase B round-5 fold-in (final round)

All five round-5 items are done. The four Phase B suites pass on a simulated host without the backup mount (105 tests). Every surviving mutant is either equivalent or no longer applies to the rewritten code. No host action and no state-changing git command.

### 1. Findings

**R5A DEFECT-1 and R5B N-1 (the installer's "Next:" hint): FIXED** in `util/install_duplicati_service.bash`, now **1.5.0**.
- **On Running:** step 3 now says, as one printed sentence: "If it reads Running, stop the unit at once (sudo systemctl stop duplicati.service) and record it; do not pause". It adds design step 8's reason: `pause` only suspends a job that may already be running, and `resume` would continue it with its old options.
- **New item 5, after the guard block:** "Then, on A0, A2 and B, restart the unit before resume (step 10): sudo systemctl stop duplicati.service, then sudo systemctl start duplicati.service; serverstate must exit 2 again; read the edits back with export <id> (step 10 lists what to check) -- and only then resume. On Procedure A, P0.5b runs here instead."
- I deliberately did not list the read-back's contents. R5B DEFECT-1 says that read-back cannot see the server's default options, so the hint defers to D.

**R5A DEFECT-2 and NIT-1 (an existing `/etc/duplicati/env`): FIXED without settling O-12.**
- The file passes only as exactly `root:duplicati:640` or `duplicati:duplicati:600`, the two forms O-12 documents. Everything else is refused. That includes:
  - any other owner or group;
  - any group-writable or other-writable file;
  - anything other-readable, so `0644` is refused because the file may carry the key.
- A symlink is caught before `stat` runs and refused with the word "symlink" in the message.
- Every message names both forms through one variable, `ENV_MODES_ACCEPTED`: "root:duplicati 0640 or duplicati:duplicati 0600 (O-12 is open; either form is accepted)".
- The code comment cites O-12 and says the installer does not settle it.
- One judgement call: I took the modes as exact, so variants such as `root:duplicati 0440` or `duplicati:duplicati 0400` are also refused. Widening is a one-line change if the owner prefers it.

**R5A NIT-2 (Procedure A's second key): FIXED.** The key NOTE now says: "on Procedure A, place the accepted 09-18 key here instead, and a random one at `<cred>.new`, which P0.5b swaps in -- the same command with .new". This matches D step 8 at `9ce2f602`.

**R5A NIT-3 F01 (production default mount unpinned): FIXED.**
- New test `test_unset_the_production_default_requires_mnt_backups` puts a `mountpoint` stub first on PATH that records its arguments and exits 1. With the variable unset, the wrapper must exit 78 with "FATAL: /mnt/Backups is not a mountpoint", and the stub must have been asked exactly `-q /mnt/Backups`.
- It passes on the owner's host, where the mount exists, and on CI, where it does not, and never reads the real mount table.
- **Consequence:** R5A's way of simulating CI (editing the wrapper's default to a nonexistent path, as in `mk_cisim.bash`) now fails this pin by design. The ci-sim mode of `c1_mutations.py` (now 1.2.0) therefore simulates the absent mount with the same `mountpoint` stub on PATH instead.

**F07 (root:root 0640 accepted): KILLED** by item 2's tests. R5A's F07–F10 have no anchor in the rewritten check, so I re-anchored them:
- R18 adds `root:root:640` to the accepted forms (this is F07);
- R19 accepts an other-readable 0644;
- R20 refuses O-12's dissent form;
- R21 accepts group-writable (F08's class);
- R22 drops the `exit 2` (F10);
- R23 fakes the `stat` result (F11);
- R24 removes the symlink check.

All seven are killed.

### 2. Tests, with fail-before and pass-after evidence
- **`tests/test_duplicati_installer_real_path.py`, now 18 tests:**
  - `test_an_existing_env_file_must_be_one_of_o12s_two_forms` replaces the old mode test. It refuses 11 combinations, including `root:root:640` and `root:duplicati:644`, and checks that every refusal names both forms. It accepts both O-12 forms.
  - New `test_an_existing_env_file_that_is_a_symlink_is_refused_by_name`.
  - The hint test now asserts the stop-not-pause sentence, that "pause at once" is gone, and that the restart sentence comes after the guard block and before "only then resume".
  - The key-NOTE test asserts the `….new` sentence.
- **`WrapperEnvContract`:** the F01 pin (one new test).
- **Fail-before:** against `9ce2f602`'s code the new and changed tests give **15 failures across 4 tests**. The F01 pin passes there, which is expected: the pin holds on unmutated code, and mutants R17 and F01 show it catching the change.

### 3. Check results

| Check | Result |
| --- | --- |
| `tests/test_duplicati_wrapper_contract.py` on this host | 53 tests, OK |
| `tests/test_duplicati_installer_real_path.py` on this host | 18 tests, OK |
| ci-sim, contract suite | 53, PASS |
| ci-sim, installer real-path suite | 18, PASS |
| ci-sim, re-key real-path suite | 25, PASS |
| ci-sim, clearing-script suite | 9, PASS |
| shellcheck on the wrapper and installer | 0 |
| flake8 on the real-path suite and `c1_mutations.py` | 0 |

**Mutation counts, all run in ci-sim:**

| Instrument | Applied | Killed | Not killed |
| --- | --- | --- | --- |
| `c1_mutations.py after` | 57 | 56 | I11, equivalent (`cmp -s` runs before the bless) |
| R5A's `r5a_mutants.py`, F01–F13, via the new `r5a` mode | 9 | 9 | none |

- In the `c1_mutations.py` run, R9 and R10 found no anchor; they are superseded by R18–R23.
- In the R5A run, F01 was re-anchored on the production default (killed). F07–F10 have no anchor; their re-anchored equivalents are R18–R22, all killed.
- The `r5a` mode loads R5A's script unchanged and only wraps its `run()` so the `mountpoint` stub is first on PATH.

### 4. Needed elsewhere

**D (prose lane, clearing script):** in step 8, replace the round-4 sentence "It must also be `root:duplicati`, group-readable and writable by root only (0640); the installer refuses any other owner or mode…" with:
> It must be one of O-12's two forms -- `root:duplicati` 0640 (what the installer creates, and what this design recommends) or `duplicati:duplicati` 0600 (the recorded dissent); the installer accepts either and does **not** settle O-12. Anything else is refused: another owner or group, a group- or other-writable file, an other-readable one (the file may carry the key), and a symlink, which must be replaced by a regular file.

Also in step 8, where the first-start check is described, add:
> The installer's closing hint prints this stop-not-pause rule and step 10's restart.

**A, step 9 and §8:**
- Step 9 gets the same mode sentence as D.
- §8 "Folded in, round 5": R5A DEFECT-1, DEFECT-2, NIT-1, NIT-2, NIT-3 (F01, F07); R5B N-1.
- The O-12 row in A's open-items table stays OPEN. Add: "the installer (1.5.0) accepts either form".

**`docs/REFERENCE.md`, the `tests/test_duplicati_installer_real_path.py` bullet:** replace "the kept, refused and wrongly-owned existing env file" with:
> the kept and refused existing env file, which must be one of O-12's two forms (`root:duplicati` 0640 or `duplicati:duplicati` 0600; symlinks, other-readable and group-writable files refused)

and replace "step 10's guard block verbatim" with:
> step 10's guard block verbatim, stop-not-pause on a Running first start, and step 10's restart before resume

In the contract-suite bullet, after "An empty `DUPLICATI_REQUIRE_MOUNT` switches the wrapper's mount check off", add:
> and the unset production default is pinned to `/mnt/Backups` through a `mountpoint` PATH stub, which is also how CI's missing mount is simulated

**Other lanes and review rounds:** a future ci-sim must use a `mountpoint` PATH stub, not edit the wrapper's default. The F01 pin fails the second method on purpose.

### 5. Out of scope
- R5B DEFECT-1, which says the `export <id>` read-back cannot see the server's default options, belongs to the prose lane. The hint avoids repeating that claim.
- The `c1_mutations.py after` baseline excludes lane C2's classes, as in earlier rounds.

**Files changed:**
- `util/install_duplicati_service.bash` (1.5.0)
- `tests/test_duplicati_installer_real_path.py`
- `tests/test_duplicati_wrapper_contract.py` (`WrapperEnvContract` only)
- `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/c1_mutations.py` (1.2.0: R17–R27, ci-sim by `mountpoint` stub, `after` run in ci-sim, `r5a` mode)

<!-- markdownlint-enable -->

---

## Round 5's fold-in, lane C2

Archived verbatim (6,354 characters, sha256 `88554da9ce7d3505`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

# Lane C2 report: Phase B round-5 fold-in (the last one)

Items 1 and 2 are done, and both optional items (F14, F21) were trivial, so they are done too. All five mutants (F14, F19, F21, F22, F23) are killed by the current suites.

There is one catch for item 2. **R5A's own `r5a_mutants.py` still reports F22 and F23 as surviving**: its suite map for the two A0 scripts lists only the contract, installer and re-key suites, not the new `tests/test_a0_restore_scripts.py`. My tool (`c2_rekey_mutations.py`), using R5A's exact anchors plus the new suite, kills both. One line in `r5a_mutants.py` needs changing (section 4).

Files referenced: R5A is `util/ad-hoc/2026-10-08_backup-phase-b-round4/R5A.md`; A is `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`.

**Changed**:
- **new**: `tests/test_a0_restore_scripts.py`
- `tests/test_duplicati_wrapper_contract.py`, classes `RecoveryHelperGates` and `RekeyGate` only
- `tests/test_backup_rekey_real_path.py`
- `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/c2_rekey_mutations.py`

I did not edit any script. In particular the two A0 scripts (`util/ad-hoc/2026-09-22_confirm_a0_premise.bash`, `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash`) are unchanged: their existing `YAMAGUCHI_*` overrides plus a `duplicati-cli` stub on PATH were enough.

## 1. Findings

**F19 (R5A NIT-4): FIXED, test only.** The hand start reads two files, the settings key and the UI password, and its check (`if "\0" in key or "\0" in pw`) already covered both. Only the test was one-sided. `test_password_init_dry_run_runs_the_secret_format_gate` now applies all four bad inputs (edge whitespace, CR, NUL, two lines) to each file in turn.

**F22 and F23 (R5A NIT-4): FIXED.** The new suite stubs `duplicati-cli` and was cheap. It never runs a Duplicati binary, never touches `/usr/lib/duplicati` or `/mnt/Backups`, and needs no `sqlite3` stub because the scripts never call it. For each A0 script it checks:
- **The F22/F23 behaviour:** `duplicati-cli` sees the main copy and, byte-identical, each `-wal`/`-journal` sibling, beside `--dbpath` under the copy's own name. It sees nothing when the index has none.
- **Clean-up:** every temporary file is gone afterwards, and the frozen index is never written.
- **Passphrase:** a value containing `$ & @ # ^` is parsed verbatim, reaches the stub through the environment only, and never appears in argv or the output.
- **Copy, not original:** `duplicati-cli` gets the copy, never the frozen index. With no index at all, the script exits 2 and `duplicati-cli` does not run.
- **Per script:** the premise script runs `list --version=0 '*duplicati-server-db*'`. The restore script restores into the named directory (mode 0700), and refuses a directory under `/home/pcalnon` before anything runs.

**F14 (optional): FIXED, test only.** The code was already right: a `Source` row at -1 or -2 counts as an orphan, because `SetSources` writes per backup. The new test `test_unrewritten_counts_a_source_row_at_a_settings_id_as_orphaned` pins it.

**F21 (optional): FIXED, test only.** The code already ignores an empty `REKEY_CREDSTORE_DIR` (it tests `-n "${…:-}"`). The new test `test_an_empty_credstore_override_is_ignored` checks that an empty value leads to the ordinary "run with sudo" refusal, not the hook's exit 2. It runs on the scratch copy, so even the trap's look at `…-key.old` stays off `/etc`.

## 2. Tests

Each new test passes on the current code and fails under its target mutant.

| Tool | Mutants | Result |
| --- | --- | --- |
| `c2_rekey_mutations.py mutate --set after F14 F19 F21 F22 F23` | the five, anchors verbatim from R5A | **5 of 5 killed** (baseline 89 tests OK) |
| `r5a_mutants.py <tree> F14 F19 F21 F22 F23` | the same five | 3 of 5 killed; F22 and F23 survive because its map omits the new suite |

The killing tests:
- F14: `test_unrewritten_counts_a_source_row_at_a_settings_id_as_orphaned`
- F19: `test_password_init_dry_run_runs_the_secret_format_gate`
- F21: `test_an_empty_credstore_override_is_ignored`
- F22, F23: `test_siblings_are_copied_beside_the_copy_under_its_name`

## 3. Check results

- `python3 -m unittest tests/test_duplicati_wrapper_contract.py tests/test_backup_rekey_real_path.py tests/test_a0_restore_scripts.py`: **89 tests, OK**.
  - 53 contract tests, including C1's current ones;
  - 25 real-path tests (24 plus 1);
  - 11 A0 tests.
- `flake8 --max-line-length=512` on the 4 changed Python files: clean.
- CodeQL prescreen: 0 predicted alerts.
- No bash changed this round.

## 4. Needed elsewhere

**ci.yml (coordinator)**, inserted after the line for the re-key real-path suite:
```
          # tests/test_a0_restore_scripts.py: Procedure A0's two scripts hand duplicati-cli
          # a COPY of the frozen job index with its -wal/-journal beside it under the copy's
          # name (round 5, R5A F22/F23); passphrase by environment only. duplicati-cli is a
          # PATH stub; no Duplicati binary, /usr/lib/duplicati or /mnt/Backups is touched.
          python3 -m unittest -v tests/test_a0_restore_scripts.py
```

**`r5a_mutants.py`** (R5A's, not mine): add `A0 = "tests/test_a0_restore_scripts.py"` and include it in the `A1` and `A2` entries of `SUITES`, so its own run kills F22 and F23.

**docs/REFERENCE.md (coordinator)**
- New bullet: "`tests/test_a0_restore_scripts.py` -- round 5 of Phase B (R5A NIT-4): `util/ad-hoc/2026-09-22_confirm_a0_premise.bash` and `…_restore_server_db_from_fileset.bash` against a `duplicati-cli` PATH stub. Pins: the frozen job index's `-wal`/`-journal` copied beside the `--dbpath` copy under its name and byte-identical (nothing when absent); every temporary copy removed; the frozen index never handed over or written; the passphrase parsed verbatim and passed by environment only; no index means exit 2; the restore directory refused inside the backup Source."
- Contract-suite bullet: add "the hand start's secret checks apply to both the key and the password file".

**A §8 (prose lane):**
> Round 5: R5A NIT-4 fixed. F19's test now covers both files the hand start reads, and the new `tests/test_a0_restore_scripts.py` kills F22 and F23. R5A NIT-5's F14 and F21 are pinned by tests; the code was already correct.

No D change is needed.

## 5. Out of scope

`r5a_mutants.py`'s suite map, as above. Nothing else.

<!-- markdownlint-enable -->

---

## Round 5's fold-in, lane P

Archived verbatim (5,435 characters, sha256 `dd8f97aaa008d547`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

Round 5 is folded into D and A, and D is regenerated. The edit count stays at 78 (77 prose, 1 fence); I extended existing edits rather than adding new ones.

**D sha256:** `470e33f871da4682a4ebf344780dbad5b6c5d6e4ed2e8262cb427027ab77bfa1`. It includes C1's installer changes as they stood when I regenerated, so it will move if C1 changes the installer again.

**Lane B fixes**
- **R5B DEFECT-1 (server default options):** in step 8, while no server runs, the same `sqlite3` session now:
  1. reads the -1 rows: `SELECT "Name", "Value" FROM "Option" WHERE "BackupID" = -1 AND ltrim("Name", '-') IN ('retention-policy', 'keep-time', 'keep-versions');`
  2. records them in the validation record (they are retention strings, not secrets);
  3. deletes exactly those rows;
  4. runs the `SELECT` again, which must return nothing.

  The reason given in D is that these rows join every run (`GetCommonOptions`) but never appear in `export`. Step 11 restores them only together with the job's policy, and only if the owner wants server-wide defaults at all. The step-10 read-back now covers the job only, and says why. A mirrors this in step 9 (clear), step 11 (read-back) and step 14 (restore).
- **R5B DEFECT-2 (Repair deletes extra volumes):** on B, Repair now runs:
  1. with `--dry-run` first;
  2. then every `WouldDeleteFile` line is read;
  3. then each named file is copied to `/mnt/Backups/Ubuntu/_yamaguchi_retention_aside` (root 0700, outside Dropbox, `sudo cp -p`, sha256 checked on both sides);
  4. only then does the real Repair run.

  The text notes that the 09-18 dlist (AC-4's drill target) can be one of those files. Repair is now named as a third, conditional exception in D's front matter, the §8 preamble, P1 step 4 and §10.2 (which now says "the exceptions its preamble names"), and in A §6.0 item 5.
- **R5B N-2 to N-6:**
  - N-2: a manual AC-3 costs the next 14:00 fileset within 24 h, which is the same day's for a morning run.
  - N-3: the orphan-row copy goes in a root-only 0700 directory outside `/home/pcalnon` and is `shred -u`'d once the gate passes. The text says that on Procedure A it holds blobs under the 09-18 key, and that the unit is stopped and comes back Paused. This is in D (clearing note and P0.5b) and A note 6a.
  - N-4: if B's queue already holds a backup, move the job's `Time` to the next day's 14:00 UTC, restart and re-check.
  - N-5: both counts are stated. Against a host installed from `origin/main`, six of seven blessed files differ (all but the guard). Against the branch's first fold-in, four changed. Either way it is BEHAVIOUR CHANGE and needs `--update-backup-behavior`. The count is moot on this never-blessed host and only matters for a host installed from `main`.
  - N-6: A says the server is never restarted before P0 step 10, except by P0 step 8's stop and start if the first start reads Running.

**Lane A fixes (prose side)**
- **R5A DEFECT-2:** D step 8, D's clearing note and A step 9 now say an existing `/etc/duplicati/env` passes in either of O-12's forms (`root:duplicati` 0640 or `duplicati:duplicati` 0600), never world-readable, and that the installer does not settle O-12. "refuses any other owner or mode" is gone and is on the stale-phrase list. This prose describes C1's in-progress code, not code I checked.
- **R5A NIT-2:** wherever D and A describe the installer hint, they now say it stops the unit on Running (never `pause`), includes step 10's restart, and names Procedure A's `…-key.new`. A marks that code as pending C1.

**A §8 Round 5 entry** records every R5A and R5B finding:
- **FIXED (P):** R5B DEFECT-1, DEFECT-2 and N-2 to N-6; R5A DEFECT-2's prose.
- **FIXED, test added in parallel:** R5A NIT-4's F22/F23. A new suite, `tests/test_a0_restore_scripts.py`, appeared from another lane during this pass; it covers that case and passes. It is not yet in `ci.yml`, which is why the wiring-drift test currently fails on it. That wiring is yours.
- **Pending C1:** R5A DEFECT-1, DEFECT-2's code and the symlink message, NIT-1, NIT-2, NIT-3; R5B N-1.
- **Pending C2:** NIT-4's F19; NIT-5.
- **Yours:** NIT-6.

**For you: the unit comment in `util/systemd/duplicati.service`, lines 47–50.** Replace those lines with:
```
# propagating to Dropbox. That would also contradict section 8's rule that nothing under
# /mnt/Backups/Ubuntu/ is deleted or moved beyond its named exceptions (the job's own
# retention, the signed-off escrow delete, and a Procedure B Repair whose deletions are
# copied aside first). Duplicati needs write on the destination directory only.
```
After you apply it, D needs one more regeneration. Until then D:705 still reads "two named exceptions".

**Checks**
- **Clearing script:** applied 78; a second run says "no change"; `--check` reports 0 staged, 14 current.
- **Doc checks:** markdownlint v0.42.0 is clean on D and A; the structure check finds 0 problems in either; the snippet linter reports 14 blocks, 0 failures; flake8 is clean.
- **Suites:** the clearing-script suite passes 9/9, `tests/test_a0_restore_scripts.py` passes, and `test_env_repr_safety` passes. `test_ci_test_wiring_drift` fails only on that unwired new suite.

**Changed:** D (`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`, regenerated), A (`notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`), `util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py`.

<!-- markdownlint-enable -->

---

## Round 5's fold-in, lane P (second pass, the code lanes' prose)

Archived verbatim (2,965 characters, sha256 `a32efb9b127ef18c`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

C1's and C2's round-5 prose is folded into D and A, D is regenerated, and every check passes.

- **Edit count:** 78 (77 prose, 1 fence). I extended existing edits rather than adding new ones.
- **D sha256:** `589d46c51c100f196946119d855af26e445ca57349e2ca69c58fb92267f9c473`
- **D:705:** confirmed. The regenerated unit comment now reads "beyond its named exceptions (the job's own retention, the signed-off escrow delete, and a Procedure B Repair whose deletions are copied aside first)".
- **No "pending" left:** none remains in D or A as a disposition. Five unrelated uses of the word remain:
  - D:3134–3135: the SMART attribute `Current_Pending_Sector` and the error-log text beside it.
  - D:3258: "installs it that way pending a ruling", about the O-12 question, which is still open.
  - D:3291 and D:3293: two old §12 history rows.
  - A:11: a predecessor handoff's filename.

**What I folded in**
- **Mode sentence (D step 8, A step 9):** C1's exact text. The file must be one of O-12's two forms, `root:duplicati` 0640 or `duplicati:duplicati` 0600. The installer accepts either and does not settle O-12. Anything else is refused, including a symlink, which must be replaced by a regular file. The clearing note says the same: exactly the two forms, a regular file, never other-readable.
- **Stop-not-pause (D step 8):** added after the Running remedy: "The installer's closing hint prints this stop-not-pause rule and step 10's restart."
- **O-12 row in A:** stays OPEN, with "the installer (1.5.0) accepts either form" added.
- **Installer version:** 1.5.0 wherever the current version is stated. That covers D step 8, the clearing note, note 12c and the script's docstring, plus A step 9. Historical mentions are marked, for example "1.4.0 (1.5.0 now)".
- **A §8 Round 5:** every item is now FIXED, attributed to C1, C2, the coordinator or P. That covers:
  - R5A DEFECT-1, DEFECT-2 and NIT-1 to NIT-6;
  - R5B N-1;
  - the F01/F07 test gaps, pinned via R18;
  - F19/F22/F23, now covered by `tests/test_a0_restore_scripts.py`;
  - F14/F21, pinned by tests (the code was already correct).

  The suite counts are recorded as 53 / 18 / 25 / 11 / 9.

**Checks**
- **Clearing script:** applied 78; a second run says "no change"; `--check` reports 0 staged and 14 current.
- **markdownlint v0.42.0:** clean on D and A.
- **Structure check:** 0 problems in either file.
- **Snippet linter:** 14 blocks, 0 failures.
- **flake8:** clean.
- **Suites:** 136 tests OK across all seven:
  - clearing script, 9;
  - contract, 53;
  - installer real path, 18;
  - re-key real path, 25;
  - A0 scripts, 11;
  - CI wiring drift (now passing, so the A0 suite is wired);
  - env-repr.

**Changed:** D (`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`, regenerated), A (`notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`), `util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py`.

<!-- markdownlint-enable -->

---

## Round 6 — confirmation of round 5's fold-in

Archived verbatim (13,939 characters, sha256 `bc178d8deddee49e`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

# Phase B round 6 — confirmation of round 5's fold-in

I reviewed local commit `ee7fcee7` and the delta `git diff 9ce2f602 ee7fcee7`. All runs used scratch extractions under `scratchpad/r6/`. The ci-sim used a `mountpoint` stub, first on PATH, that exits 1; I did not edit the wrapper default.

Documents:
- **D**: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`
- **A**: `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`
- **record**: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md`
- **R5A, R5B**: round 5's reports, `util/ad-hoc/2026-10-08_backup-phase-b-round4/R5A.md` and `R5B.md`

## Summary

**0 BLOCKER, 3 DEFECT, 4 NIT.**

- **Round 5's findings:** every R5A and R5B finding is fixed at `ee7fcee7` or recorded correctly in A §8, with one exception. The fix for R5B DEFECT-2 (Repair) is incomplete and cannot be carried out as written (DEFECT-1 below).
- **Suites, run normally and in ci-sim:** all pass, with identical counts.

| Suite | Tests | Result |
| --- | --- | --- |
| contract | 53 | OK |
| installer real path | 18 | OK |
| re-key real path | 25 | OK |
| A0 scripts | 11 | OK |
| clearing script | 9 | OK |
| CI wiring drift | 14 | OK |
| env-repr | 6 | OK |

  In ci-sim, no suite asked the stub about `/mnt/Backups`; it was asked only about scratch paths.
- **The A0 suite will fail on a real CI runner, though.** That host has no `/home/pcalnon` (DEFECT-2).
- **Mutation instruments:**

| Instrument | Killed | Not killed |
| --- | --- | --- |
| `c1_mutations.py after` (its built-in ci-sim) | 56 of 57 applied | I11, equivalent. R9 and R10 have no anchor; R18–R22 replace them. |
| `c2_rekey_mutations.py mutate --set after` | 48 of 48 | G02 has no anchor, as before |
| `r5a-bin/r5a_mutants.py` (via c1's `r5a` mode, with the stub) | 20 of 20 applied | F07–F10 have no anchor; R18–R22 cover them. F22 and F23 are now killed, because the A0 suite is in its map. |
| My 10 new mutants (`scratchpad/r6/bin/r6_mutants.py`) | 9 of 10 | N08: the hint's "pause only suspends…" reason line can be deleted (NIT-3) |

- **shellcheck** at `--severity=warning`, as the hook runs it: 0 findings. At default severity, `r5a-bin/mk_cisim.bash:7` gives one SC2016 *info*, which the hook does not report.
- **flake8 `--max-line-length=512`** on the four test files, the clearing script, the gate and every fold-in and evidence `.py`: 0 findings. That includes the R5A NIT-6 files.
- **markdownlint v0.42.0** (from the pre-commit cache) on D, A and the record: rc 0.
- **D regenerates byte-identical.** Starting from `origin/main`'s D, I ran `stage --from-repo` (7 blocks rewritten) and then the clearing script ("applied 78"). The result has sha256 `589d46c5…`, identical to `ee7fcee7`. A second run reports "no change".

## Round-5 findings at ee7fcee7

| Finding | Status |
| --- | --- |
| R5A DEFECT-1 / R5B N-1 (stop, not pause, on Running; the restart) | FIXED. `install:406-408`, `:422-424`; asserted by the tests; R25, R26 and N09 are killed. |
| R5A DEFECT-2 (O-12) and NIT-1 (0644) | FIXED. The `case` accepts exactly `root:duplicati:640` or `duplicati:duplicati:600`. `-L` is checked before `-e`, so a dangling link is refused too. Every message names both forms, and the code comment says O-12 is not settled. D step 8, A step 9 and A's O-12 row (still OPEN) agree. |
| R5A NIT-2 (`…-key.new`) | FIXED (`install:378`; R27 killed) |
| R5A NIT-3 F01 / F07 | FIXED (R17 and R18 killed) |
| R5A NIT-4 F19 / F22 / F23 | FIXED (killed in both instruments) |
| R5A NIT-5 F14 / F21 | FIXED (pinned) |
| R5A NIT-6 | FIXED (flake8 clean) |
| R5B DEFECT-1 (`BackupID -1` default options) | FIXED. See "Not refuted" for the SQL check; NIT-1 is a residue. |
| R5B DEFECT-2 (Repair deletes) | **Partially fixed.** See DEFECT-1. |
| R5B N-2 to N-6 | FIXED, in both D and A |
| Third exception wording | Consistent in D's front matter, the §8 preamble, P1 step 4, §10.2, A §6.0 item 5 and the unit comment (`duplicati.service:48-50`). No "two exceptions" or "exactly two" remains. |

## Findings

### BLOCKER

None.

### DEFECT

**DEFECT-1. The Repair `--dry-run` / copy-aside step cannot be done as written, and the copy set it names is incomplete. VERIFIED from source at the tag.**

D's B text (D:2746-2747) and A §6.4 say: queue Repair "with `--dry-run`", "read every `WouldDeleteFile` line", copy each named file aside. Four things are wrong with that.

1. **Repair deletes more than `WouldDeleteFile` names.** Repair runs `RemoteListAnalysisAsync(…, VerifyMode.VerifyAndCleanForced)` (`RepairHandler.cs:173`). Its dry run logs each deletion of a Temporary, Deleting or incomplete Uploading remote file under the ID **`WouldDeleteRemoteFile`** (`FilelistProcessor.cs:388-399`, `:469-480`). Repair itself adds **`WouldDeleteEmptyIndexFile`** (`RepairHandler.cs:598-609`) and **`WouldDeleteIndexFile`** (`:1050-1053`). `WouldDeleteFile` (`:400`) is only the ExtraVolumes branch. An operator who copies only the `WouldDeleteFile` names leaves the other deletions uncopied. The incomplete-upload case is exactly what an unclean last writer produces, which is the scenario the step was written for.
2. **The dry-run lines never reach the place the operator reads results.** `WriteDryrunMessage` logs at `LogMessageType.DryRun` (`Log.cs:246-248`). The result object keeps only Error, Warning and Information (`ResultClasses.cs:437-447`). So the stored job log, which the API client's `log` verb reads, has no `Would…` lines at all.
3. **There is no way to "queue it with `--dry-run`".** The repair endpoint's input is `RepairInputDto(only_paths, time, version, paths, refresh_lock_info)` (`RepairInputDto.cs`; `BackupPost.cs:173-206`): no dry-run and no free-form options. `yamaguchi_server_api.py` has no repair verb. The only route is a job-level `--dry-run` advanced option. Left in place, that option would turn AC-3 into a silent dry run, and step 10's `export` read-back does not check for it.
4. **The suggested remedy route has a path limit.** A job-level `--log-file` must sit under `ReadWritePaths` (`duplicati.service:51`).

**Remedy:**
- Name the mechanism: add `--dry-run`, plus `--log-file=/home/duplicati/<name>.log` with `--log-file-log-level=DryRun`, to the job. Queue Repair, `resume`, wait, `pause`.
- Copy every file named by **any `Would…Delete…`** line: `WouldDeleteFile`, `WouldDeleteRemoteFile`, `WouldDeleteEmptyIndexFile`, `WouldDeleteIndexFile`.
- Remove all three options, and add "no `--dry-run`/`--log-file`" to the read-back.
- Change "the remote volumes the index does not know" to also cover the index's own incomplete or deleting files, in D's front matter, the §8 preamble, A §6.0 item 5 and the unit comment.

**DEFECT-2. `tests/test_a0_restore_scripts.py` fails on a CI runner, and the guard it pins can be bypassed. VERIFIED.**

- **The test fails off this host.** `test_refuses_a_restore_directory_inside_the_backup_source` passes `/home/pcalnon/a0-restore-must-not-be-created` to the restore script. The script's refusal is `case "$(readlink -f "${OUT}")/" in /home/pcalnon/*)` (`restore_server_db_from_fileset.bash:25-27`). `readlink -f` prints nothing and exits 1 when a parent directory is missing, so the case word becomes `/` and the refusal never fires. `install -d` then fails with EACCES and the script exits 1, not 2.
  - **Reproduction:** `scratchpad/r6/bin/ci_home_absent.bash` replaces `/home/pcalnon` with a nonexistent root directory in copies of the script and the test. Result: `AssertionError: 1 != 2 : install: cannot create directory …: Permission denied`.
  - **Effect:** GitHub runners have no `/home/pcalnon`, and `ci.yml` now runs this suite, so CI goes red. The suite's docstring claims it is hermetic, which this test is not.
- **The script's guard has a real hole.** On the owner's host, any `OUT` two or more new levels under `/home/pcalnon` gets past the refusal: `readlink -f` fails, `install -d` creates the directory, and cleartext key material is restored into the backup Source.
  - **Reproduction:** `readlink -f srcroot/missing/sub` gives rc=1 and empty output → NOT-REFUSED.
  - D:2687-2688 says "The script refuses a restore path under `/home/pcalnon/`".
  - This predates round 5. D does not name a path under home, so it needs operator error, which is why it is not a BLOCKER.
- **A regressed refusal writes into the real home.** If the refusal ever regresses, this test creates a directory in the owner's home and never cleans it up.

**Remedy:**
- In the script, use `realpath -m` (canonicalise even when components are missing), and refuse if that fails.
- In the test, assert a nested nonexistent path (for example `/home/pcalnon/x/y`). With `realpath -m` it then passes on CI too.

**DEFECT-3. Restoring the server-wide defaults "with" the new policy voids D's five/four prediction. Mechanism VERIFIED; exposure PLAUSIBLE (the contents of the `-1` rows are unknown).**

- **What D and A allow:** D step 11 and A step 14 say the deleted `BackupID -1` retention defaults "come back only with it, and only if the owner wants defaults at all".
- **What the product does:** the removers form a union. `KeepTimeRemover`, `RetentionPolicyRemover` and then `KeepVersionsRemover` all contribute deletions (`DeleteHandler.cs:82-87`). A default is only overridden when the job sets the same name (`Runner.cs:1505-1513`, `:1584-1590`).
- **Consequence:** a restored default `keep-time` or `keep-versions` combines with the job's `retention-policy`. The first pass can then delete pre-recovery filesets beyond the five that were copied aside. Those are the sole copies, and the "keeps four, deletes five" statement and the aside list would both be false.
- **Remedy:** say "never restore `keep-time` / `keep-versions` / `retention-policy` as server defaults while the job carries its own policy (they combine, `DeleteHandler.cs:82-87`)". Or require a `retention_table.py` re-run that includes them, and a matching aside copy.

### NIT

- **NIT-1. The clearing `SELECT` does not cover a mixed-case name.** It matches `ltrim("Name",'-')` exactly, so a mixed-case name such as `--Keep-Time` is not covered. I tested the statements against `Schema.sql` with eight rows: correct otherwise. Such rows are unrealistic. Optionally use `lower(ltrim(…))`.
- **NIT-2. A §8 Round 5 cites the wrong mutant for F01.** It says the F01 pin is "(R18)". In `c1_mutations.py`, R17 is F01 and R18 is F07.
- **NIT-3. The hint test does not pin the reason line.** It does not assert "pause only suspends a job that may already be running…" (N08 survives). Item 3 also stops at "record it": it does not say to read `paused-until` and start again, as D step 8 does.
- **NIT-4. The record at `ee7fcee7` is not reassembled.** It lacks every entry from round 3's fold-in onward. `2026-10-05_reassemble_phase_b_record.bash --check` exits 2 with "header differs … pass --accept-header". This is expected for WIP, but it must be run before the PR.

## Not refuted

- **The installer's mode check:**
  - exact `%U:%G:%a` matching: setuid, sticky or 0440 variants are refused;
  - a dangling symlink is refused;
  - a dry run reports and continues;
  - root reads either form;
  - N07 and N10 are killed.
- **The clearing SQL** against `Schema.sql` at the tag:
  - it selects and deletes exactly the three names at `-1`, with or without dashes and with any `Filter`;
  - it leaves `-2`, job rows and other `-1` options alone;
  - a re-`SELECT` is empty.
- **Side effects of the delete: none found.**
  - The values are plaintext: `EncryptSensitiveFields` works by name (`Connection.cs:1585-1590`).
  - `GetCommonOptions`'s `ToDictionary` (`Runner.cs:1587`) would only have failed on duplicate names, and the delete removes any.
  - The re-key's `SetSettings(GetSettings(-1))` re-saves the remainder.
- **The cited source lines are accurate:** `RepairHandler.cs:299` and `:397` are correct, and Verify uses `VerifyOnly` (`TestHandler.cs:67`), so it deletes nothing.
- **The A0 suite**, apart from DEFECT-2:
  - it is stub-only; strace shows no `/mnt/Backups`, `/usr/lib/duplicati`, `/etc/credstore` or credential access;
  - the passphrase stays out of argv;
  - the copy goes to `--dbpath`, never the frozen index;
  - siblings are byte-identical and cleaned up;
  - the restore directory is created 0700;
  - N01 to N06 are all killed.
- **The installer hint ordering** (N09 killed) and the `…-key.new` NOTE.

## Unverifiable

- What the restored database's `BackupID -1` rows hold (DEFECT-3's exposure).
- Whether the index has incomplete or extra remote volumes (DEFECT-1's trigger).
- Whether 2.4's live-log viewer shows DryRun-level lines. I did not check this from source.
- CI itself: the branch is local, so the ci-sim and the home-absent run are simulations.

## Slips

- **Harness refusals.** Several compound commands were refused (`git` inside a raw-content hostname, a computed `HOME`) and re-issued as scratch scripts. None of the refused commands ran.
- **Host access:**
  - the strace and A0 runs `stat`ed `/home/pcalnon/a0-restore-must-not-be-created`, which does not exist, and opened `/home/pcalnon` for `readlink`; nothing was created;
  - no unit, Duplicati binary, `:8300` connection, `sudo` or secret file;
  - nothing under `/mnt/Backups` was touched.
- **Network:** read-only raw fetches and one tree listing from GitHub at `v2.4.0.0_stable_2026-09-03`, into `scratchpad/r6/src/`.
- **Worktree:** I made no change and no git state change. `git status` now also shows a modified `CHANGELOG.md` and an untracked `CHANGELOG_ENTRY.md`, written by another lane during my run, not by me.

**Changed**: no repository file.

**Created, scratch only**, under `scratchpad/r6/bin/`: `fetch.bash`, `tree.bash`, `run_suites.bash`, `strace_suites.bash`, `ci_home_absent.bash` and `r6_mutants.py`. These live in tmpfs; copy them to `util/ad-hoc/` if they should be kept.

<!-- markdownlint-enable -->

---

## Round 6's fold-in, lane C1

Archived verbatim (2,550 characters, sha256 `7ea291fc66446a94`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

## Lane C1 report: backup Phase B round-6 fold-in

All three round-6 items in the installer hint are done, and all four of round 6's installer mutants are killed (N08 included). The four Phase B suites pass on a simulated host without the backup mount.

**R6 NIT-3 (what follows "stop the unit"): FIXED.** `util/install_duplicati_service.bash` is now 1.5.1. Right after the stop-not-pause reason, the hint prints a new line: "Then read the stored paused-until (step 8's read-back) before starting again." This matches D step 8. The reason line itself is still its own `echo`, unchanged, so N08's anchor still applies.

**R6 NIT-4 (mutant N08): FIXED.** The hint test now asserts the full reason sentence: "pause only suspends a job that may already be running, and step 10's resume would continue it with the options it started with." It also asserts the order: the stop, then the reason, then "Then read the stored paused-until…", all before the guard block.

**R6 NIT-5 (approximate ordering check): FIXED.** Both positions are now taken with `flat.index` in the same flattened text: the guard block's end (`echo "guard exit=$?"`) must come before the restart sentence.

**Repair:** the hint does not mention Repair anywhere, so lane P's rewrite of the Repair dry-run step cannot conflict with it. I added nothing about Repair.

**Mutants** (run in ci-sim, with the `mountpoint` stub first on PATH):

| Instrument | Killed |
| --- | --- |
| R6's `r6_mutants.py`, N07–N10 (the installer ones) | 4 of 4, N08 included |
| `c1_mutations.py`, the hint mutants R14, R25 and R26, re-checked after the edit | 3 of 3 |

`r6_mutants.py` runs unchanged through a new `r6` mode in `c1_mutations.py` (now 1.3.0). That mode filters to the named mutant ids and puts the stub first on the script's hard-coded PATH.

**Checks:**

| Check | Result |
| --- | --- |
| ci-sim, contract suite | 53, PASS |
| ci-sim, installer real-path suite | 18, PASS |
| ci-sim, re-key real-path suite | 25, PASS |
| ci-sim, clearing-script suite | 9, PASS |
| `tests/test_duplicati_installer_real_path.py` on this host | 18, OK |
| shellcheck on the installer | 0 |
| flake8 on the real-path suite and `c1_mutations.py` | 0 |

**Needed elsewhere:** D's embedded copy of the installer picks up the new hint line through the staging script's `--from-repo` step. No other prose change is needed.

**Files changed:**
- `util/install_duplicati_service.bash` (1.5.1)
- `tests/test_duplicati_installer_real_path.py`
- `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/c1_mutations.py` (1.3.0)

<!-- markdownlint-enable -->

---

## Round 6's fold-in, lane C2

Archived verbatim (4,510 characters, sha256 `5c170625e7ed6a83`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

# Lane C2 report: Phase B round-6 fold-in (R6 DEFECT-2)

The refusal in `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash` (the A0 restore script) is fixed with `realpath -m`. A restore path anywhere under the backup Source is now refused, at any depth, whether or not it exists, and through a symlink. R6's reproduction passes, and the new tests fail against the pre-fix script.

The other A0 script, `util/ad-hoc/2026-09-22_confirm_a0_premise.bash`, has no such pattern (no `readlink`, no restore path), so it is unchanged.

Files referenced: R6 is `util/ad-hoc/2026-10-08_backup-phase-b-round4/R6.md`. D is `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`; A is `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`.

**Changed**: `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash`, `tests/test_a0_restore_scripts.py`.

## 1. Finding: R6 DEFECT-2, FIXED

**What I chose: `realpath -m`**, on both the restore path and the Source root. It canonicalises a path whether or not it exists, and resolves every symlink on the part that does exist. `readlink -f` printed nothing when two or more trailing levels were missing, and an empty answer never matched.

The refusal now reads, in the restore script:
```bash
SOURCE_ROOT="$(realpath -m -- "${YAMAGUCHI_SOURCE_ROOT:-/home/pcalnon}")"
OUT_REAL="$(realpath -m -- "${OUT}")"
[[ -n "${SOURCE_ROOT}" && -n "${OUT_REAL}" ]] || { echo "refusing: cannot resolve ${OUT}" >&2; exit 2; }
case "${OUT_REAL}/" in
    "${SOURCE_ROOT}"/*) echo "refusing: ${OUT} is inside the backup Source (${SOURCE_ROOT})" >&2; exit 2 ;;
esac
```
- The match is on a whole path component, so the root itself is refused and `<root>-other` is not.
- An empty resolution fails closed (exit 2).
- `YAMAGUCHI_SOURCE_ROOT` defaults to `/home/pcalnon`; an empty value counts as unset.

**Tests.** The suite now sets `YAMAGUCHI_SOURCE_ROOT` to a scratch directory for every test, so it never stats or creates anything in the real home. The old one-level test now runs against the scratch root, and four new tests cover:
- two or more new levels: `a0/out` and `x/y/z`;
- the root itself, and a path that reaches it through `..` with two new levels;
- a symlink into the Source: through a symlinked directory with new levels under it, and a symlink to an existing directory inside it;
- a sibling `<root>-other/out`, which is accepted and created.

## 2. Evidence

- **R6's reproduction** `r6-bin/ci_home_absent.bash` (which renames `/home/pcalnon` to a root that does not exist) on the fixed tree: the refusal test passes. The whole A0 suite in that same copy: 15 tests OK.
- **Pre-fix script** (`ee7fcee7`) with only the `YAMAGUCHI_SOURCE_ROOT` hook grafted in, keeping `readlink -f`:
  - the one-level case passes;
  - the two-level, `..`, and symlink-with-new-levels tests **fail**: 3 failures in 10.
- **Pre-fix script unmodified:** 4 failures in 10. The one-level test fails there too, because that script ignores the scratch root.

## 3. Check results

- `python3 -m unittest tests/test_duplicati_wrapper_contract.py tests/test_backup_rekey_real_path.py tests/test_a0_restore_scripts.py`: **93 tests, OK** (53 + 25 + 15; the A0 suite grew from 11 to 15).
- `shellcheck` on both A0 scripts: clean.
- `flake8 --max-line-length=512` on the A0 suite: clean.
- CodeQL prescreen: 0 predicted alerts.

## 4. Needed elsewhere

**D:2687-2689.** The claim is now true, but it should say how far it reaches. Replace "The script refuses a restore path under `/home/pcalnon/` for the same reason:" with:
> The script refuses a restore path under `/home/pcalnon/` — at any depth, existing or not, and through a symlink (`realpath -m`; round 6, R6 DEFECT-2: `readlink -f` let a path two or more new levels deep through) — for the same reason:

**A §8, round-6 entry:**
> R6 DEFECT-2 fixed: the A0 restore script's Source refusal uses `realpath -m` and takes a `YAMAGUCHI_SOURCE_ROOT` override (default `/home/pcalnon`). The suite pins two-or-more-new-level, `..` and symlink paths against a scratch root, and passes on a host without `/home/pcalnon`.

**docs/REFERENCE.md**, in the A0 suite bullet: change "the restore directory refused inside the backup Source" to "the restore directory refused inside the backup Source at any depth, existing or not, and through a symlink (against a scratch `YAMAGUCHI_SOURCE_ROOT`)".

**CI wiring:** none new; `tests/test_a0_restore_scripts.py` is already in `ci.yml`.

<!-- markdownlint-enable -->

---

## Round 6's fold-in, lane P

Archived verbatim (4,162 characters, sha256 `4c8d97c34ef80c03`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

Round 6 is folded into D and A, D is regenerated last, and every check passes. One change is still yours: the unit comment's wording, which I need you to apply (exact text below).

- **Edit count:** 79 (78 prose, 1 fence). The one new edit is C2's D step 4 sentence on the restore refusal.
- **D sha256:** `3ad886576e5e6d5c9473781f11a6b8aa4aaebb491fb725c7b1f17c2291380ccc`

**R6 findings**
- **DEFECT-1 (Repair mechanism), D step 8 and A step 8.** I re-read every citation at tag `v2.4.0.0_stable_2026-09-03` before writing:
  - `RepairHandler.cs` 397/400, 599/609, 1051/1053;
  - `FilelistProcessor.cs` 289, 390/399, 471/480;
  - `RepairInputDto`, `BackupPost.cs` `DoRepair`, `Log.cs:246-248` and `ResultClasses.cs:437-447`.

  The procedure now reads:
  1. Add `--dry-run`, `--log-file=/home/duplicati/repair-dryrun.log` and `--log-file-log-level=DryRun` to the job. The log must sit under the unit's `ReadWritePaths=`; `/home/duplicati` is the only writable path besides the destination, and a file there would trip the guard.
  2. Queue Repair, `resume`, wait, `pause`.
  3. Read every log line matching `Would(Delete|DeleteRemote|DeleteEmptyIndex|DeleteIndex)File` and copy each named file aside (root 0700, sha256 checked on both sides).
  4. Remove all three options and confirm with `export <id>` that none remains. Left in place, `--dry-run` would make AC-3 a dry run.
  5. Only then run the real Repair.
  6. `shred -u` the log. Its DryRun lines name files only, but at that level it also carries warnings and errors that nobody has audited for content.

  Step 10's read-back now also checks for no `--dry-run`, `--log-file` or `--log-file-log-level`. The third exception is widened everywhere to "the remote files a Repair deletes": volumes the index does not know, the index's own temporary, deleting or incompletely uploaded files, and empty or replaced index files.
- **DEFECT-2:** FIXED by C2. D step 4 uses C2's sentence: the refusal holds at any depth, whether the path exists or not, and through a symlink (`realpath -m`). A records the A0 suite as 15 tests.
- **DEFECT-3:** D step 11 and A step 14 say `keep-time` and `keep-versions` defaults are never restored, because they combine with the policy (`DeleteHandler.cs:82-87`, verified). A `retention-policy` default comes back only if the owner wants one, with the table and the aside copy recomputed against it first. The owner's ruling is unchanged.
- **NIT-1:** the step-8 `SELECT` and `DELETE` now match on `lower(ltrim("Name",'-'))`.
- **NIT-2:** A's Round 5 entry now cites R17 for F01.
- **NIT-3:** FIXED by C1 (installer 1.5.1). The new hint line reaches D through `--from-repo` (D:1529).
- **NIT-4:** the record's re-assembly, which is yours.
- A §8 has a Round 6 entry using the final report's numbering. No "pending" remains in D or A.

**Installer version:** 1.5.1 wherever D or A states the current one. Historical mentions ("since 1.5.0 it accepts…") are left as they are.

**Your edit to `util/systemd/duplicati.service`.** D:705–707 still reads "a Procedure B Repair whose deletions are copied aside first". Replace the parenthesis with:
```
# /mnt/Backups/Ubuntu/ is deleted or moved beyond its named exceptions (the job's own
# retention, the signed-off escrow delete, and the remote files a Procedure B Repair
# deletes, copied aside first). Duplicati needs write on the
```
D needs one more reset, `--from-repo` and clearing-script run after you apply it.

**Checks**
- **Clearing script:** applied 79; a second run says "no change"; `--check` gives "0 staged, 14 already current".
- **markdownlint v0.42.0:** clean on D and A.
- **Structure check:** 0 problems in either file.
- **Snippet linter:** 14 blocks, 0 failures.
- **flake8:** clean.
- **Suites:** 140 tests OK across the clearing-script, contract, installer real-path, re-key real-path, A0, wiring-drift and env-repr suites.

**Changed:** D (`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`, regenerated), A (`notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`), `util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py`.

<!-- markdownlint-enable -->

---

## Round 7 — confirmation of round 6's fold-in

Archived verbatim (11,157 characters, sha256 `361155bd5723dd90`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

# Phase B round 7 — confirmation of round 6's fold-in

I reviewed local commit `19ae4aa9` and the delta `git diff ee7fcee7 19ae4aa9`. All runs used scratch extractions under `scratchpad/r7/`. I checked Duplicati source at tag `v2.4.0.0_stable_2026-09-03`, using round 6's fetched files in `scratchpad/r6/src/` plus files I fetched into `scratchpad/r7/src/`.

Documents:
- **D**: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`
- **A**: `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`
- **R6**: `util/ad-hoc/2026-10-08_backup-phase-b-round4/R6.md`
- **Fold-in reports**: `C1_round6.md`, `C2_round6.md` and `P_round6.md`, in `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/`

## Summary

**0 BLOCKER, 0 DEFECT, 7 NIT.**

- **R6's findings:** all 3 DEFECTs and NIT-1 to NIT-3 are fixed. NIT-4 (reassembling the record) is still open; it is the coordinator's action and is expected before the PR.
- **The rewritten Repair procedure (D step 8, A step 8) works as written against the source.** The detail is under "Not refuted".

**Suites, run normally and in ci-sim** (a `mountpoint` stub first on PATH that exits 1). Both runs pass with identical counts:

| Suite | Tests |
| --- | --- |
| contract | 53 |
| installer real path | 18 |
| re-key real path | 25 |
| A0 scripts | 15 |
| clearing script | 9 |
| CI wiring drift | 14 |
| env-repr | 6 |

- In ci-sim the stub was asked only about scratch paths under `/tmp/wrapper-contract-*`, never `/mnt/Backups`.
- **`r6-bin/ci_home_absent.bash`** (simulates a host with no `/home/pcalnon`): the refusal test passes, and so does the whole A0 suite (15 OK).

**Mutants:**

| Instrument | Result |
| --- | --- |
| `r6_mutants.py` | 10 of 10 killed, N08 included |
| My 8 new mutants (`scratchpad/r7/bin/r7_mutants.py`) | 4 killed (readlink regression, case on raw `OUT`, `realpath -s`, the dropped paused-until hint line) |

Of my 4 survivors, Q05 and Q07 are equivalent under the test's conditions. Q01 and Q02 are a real gap (NIT-1).

**Lint and regeneration:**
- shellcheck at `--severity=warning`: 0 findings. flake8 at `--max-line-length=512`: 0 findings.
- markdownlint v0.42.0 (from the pre-commit cache) on D and A: rc 0.
- **D regenerates byte-identical.** I started from `origin/main`'s D, ran `stage --from-repo` (7 blocks rewritten), then the clearing script ("applied 79"). The result's sha256 is `da39e40ff714…`, the same as `19ae4aa9`. A second run reports "no change".

## R6 findings at 19ae4aa9

| Finding | Status |
| --- | --- |
| DEFECT-1 (Repair) | FIXED. D:2756-2759; A:301. Verified from source (see "Not refuted"). |
| DEFECT-2 (`realpath -m`) | FIXED. `restore_server_db_from_fileset.bash:29-34`. Two or more new levels, `..`, symlinks and the root itself are all refused; `<root>-other` is accepted. Q03, Q04 and Q06 are killed. |
| DEFECT-3 (defaults) | FIXED. D step 11 (:2789) and A step 14 (:344) say `keep-time` / `keep-versions` defaults are never restored. The union described matches `DeleteHandler.cs:79-87` exactly. |
| NIT-1 (`lower(ltrim())`) | FIXED. Tested against `Schema.sql`. Mixed-case and single-dash names are selected. `-2` rows, job rows, `--keep-versions-extra` and other `-1` options are left alone. A re-`SELECT` is empty. |
| NIT-2 (R17) | FIXED |
| NIT-3 (hint) | FIXED (installer 1.5.1, `install:411`). The reason line and the new line are both asserted in order (Q08 and N08 killed). |
| NIT-4 (record) | OPEN, as expected. `--check` exits 2 with "header differs … --accept-header". The reassembly list now names R6 and the three round-6 fold-in reports. |

## Findings

### BLOCKER

None.

### DEFECT

None.

### NIT

**NIT-1. The production default `/home/pcalnon` is not pinned by any test. VERIFIED.**
- Every A0 test sets `YAMAGUCHI_SOURCE_ROOT` (`tests/test_a0_restore_scripts.py:92`).
- So changing the default at `restore_server_db_from_fileset.bash:29` to `/` (Q01) or to `/nonexistent` (Q02) survives, and either change switches the refusal off in production.
- The variable also lets a stray environment value weaken the refusal.
- **Remedy:** add one test with the variable unset and `OUT=/home/pcalnon/x/y`, asserting exit 2. `realpath -m` creates nothing, so this is hermetic on CI too. Optionally, also assert the literal default in the script text.

**NIT-2. D's front matter lists only two of the three kinds of file a Repair deletes. VERIFIED.**
- D:17 lists "volumes the index does not know, and the index's own temporary, deleting or incompletely uploaded files".
- It omits "empty or replaced index files", which the §8 preamble (D:2362), step 8 (D:2756) and A:212 all include.
- A's round-6 entry (A:536) says "the third exception names every kind".
- **Remedy:** add the third kind at D:17.

**NIT-3. Step 10's read-back cannot catch the Repair dry-run options it names. VERIFIED from D's own ordering.**
- D:2786 ("no `--dry-run`, `--log-file` or `--log-file-log-level` (step 8's Repair dry run, on B)") and A:333 put this check in step 10's read-back.
- But on B, Verify and any Repair run only after step 10's restart and `resume` (D:2755; A:300). So that read-back always happens before the options exist.
- The real safeguard is item (4)'s `export` check, which is correct.
- **Remedy:** drop the parenthetical, or move it to the step that follows the Repair.

**NIT-4. `shred -u` on the log fails as the operator. VERIFIED.**
- `/home/duplicati` is `duplicati:duplicati 755`, and `UMask=0027` (`duplicati.service:19`) makes the log 0640.
- pcalnon is in group `duplicati`, so reading the log works. But overwriting and unlinking it does not.
- The failure is loud and harmless.
- **Remedy:** `sudo -u duplicati shred -u /home/duplicati/repair-dryrun.log` at D:2759 and A:301.

**NIT-5. "/home/duplicati is the one writable path besides the destination" is not literally true. VERIFIED from the unit.**
- `PrivateTmp=yes` (`duplicati.service:53`) gives the service a private writable `/tmp` and `/var/tmp`.
- The choice of `/home/duplicati` is still right, because the operator cannot easily reach the private tmp.
- **Remedy:** say "the one writable path the operator can read, besides the destination".

**NIT-6. CHANGELOG edit counts are stale. VERIFIED.**
- CHANGELOG.md:179-181 says the clearing script "makes 78 edits … 77 to prose". It now applies 79 (78 prose, 1 fence).
- The bullet heading "Rounds 3 to 5, folded in" also omits round 6, although the same entry archives round 6's reports.

**NIT-7. The test comments cite R6 findings that do not exist. VERIFIED.**
- `tests/test_duplicati_installer_real_path.py:451` says "R6 NIT-4 / N08", and `:458` says "R6 NIT-5".
- R6 has four NITs. N08 belongs to NIT-3, and NIT-4 is the record.
- `C1_round6.md` repeats the same numbering, apparently from a draft of R6.

## Not refuted

**The job-level options reach a queued Repair.**
- `DoRepair` snapshots the backup at queue time (`BackupPost.cs:59-60, 206`).
- `Runner.cs:818` applies `ApplyOptions`, which copies every job `--` option, minus its dashes, into the options (`:1510-1513`). `TestIfOptionApplies` always returns true (`:1361-1365`).
- Nothing in `Runner.cs` strips `log-file`.
- `Controller.cs:914-924` opens the log file for every operation. `Options.cs:1104-1124` parses `DryRun` case-insensitively.
- The level filter is `entry.Level >= level` (`ControllerMultiLogTarget.cs:125`). With `DryRun` sitting between Information and Warning, the log receives DryRun, Warning and Error lines. That matches D's wording.

**The log file is writable under the unit.**
- `ReadWritePaths=/home/duplicati …` (`duplicati.service:52`), and `/home/duplicati` exists as `duplicati:duplicati 755`.
- The directory-exists check at `Controller.cs:916-918` is satisfied.
- The file is opened with `FileMode.Append` (`StreamLogDestination.cs:51`), so a stale earlier log only over-copies.

**The four message IDs are complete, and every line names the file.**
- Every `WriteDryrunMessage` on the Repair path is one of:
  - `WouldDeleteRemoteFile`: `FilelistProcessor.cs:390`, `:471`;
  - `WouldDeleteFile`: `RepairHandler.cs:400`;
  - `WouldDeleteEmptyIndexFile`: `:599`;
  - `WouldDeleteIndexFile`: `:1051`;
  - non-destructive IDs: `WouldUploadVerificationFile`, `WouldReUploadFileset` (`:461`, `:713`), `WouldReUploadIndexFile` (`:779`) and `WouldReplaceBlockFile` (`:1023`).
- The re-upload paths are only for volumes listed as missing. They write new names, from `ProbeUnusedFilenameNameAsync` or a new writer, and only mark the absent original Deleted in the database. They neither delete nor overwrite an existing remote file.
- The line format is `… - [DryRun-<tag>-<Id>]: <message>` (`LogEntry.cs:160`, `:169`). So the regex matches the ID, and each message ends with the remote filename.

**The dry run predicts the real run's deletions.**
- The dry run commits some database state unconditionally: `RepairHandler.cs:173-175`, and the unguarded `UpdateRemoteVolumeAsync` calls at `FilelistProcessor.cs:428-449`.
- Those changes only promote files that exist and are complete, or schedule database-only cleanup for missing ones. Neither adds a remote deletion that the dry run did not log.

**Removing the options is confirmed by `export`.** `PrepareBackupForExport` (`Connection.cs:204-215`) clones the whole backup, settings included.

**The `realpath -m` refusal could not be bypassed.** I tried:
- `..` paths and symlinked directories, both with new levels below them;
- the root itself;
- `/proc/self/root` (it resolves);
- a prefix sibling such as `<root>-other`, which is correctly accepted.

Q05 (removing the empty-resolution guard) is equivalent, because under `set -e` a failed `realpath` already exits.

**Defaults wording.** "Never restored" appears consistently in D step 11, D step 8, A step 9's clearing and A step 14.

## Unverifiable

- Whether the restored index needs a Repair at all, and what the server-database `BackupID -1` rows hold.
- Whether the job's `--run-script-before-required` guard lets a non-backup operation through. This predates the delta and is not checked here.
- CI itself: the branch is local, so the ci-sim and home-absent runs are simulations.

## Slips

- **Harness refusals.** Several compound commands were refused and re-issued as scratch scripts, run from the worktree directory. None of the refused commands ran.
- **Host access:**
  - I ran `stat` on `/home/duplicati` and `realpath` on `/home`;
  - I read `id` / `getent group duplicati`;
  - I read no secret file.
- **What I did not do:** start or stop any unit, run a Duplicati binary, contact `:8300` or use `sudo`. Nothing under `/mnt/Backups` was touched.
- **Network:** read-only raw fetches from GitHub at the tag, into `scratchpad/r7/src/`.
- **Worktree:** no change and no git state change. `git status` is clean at `19ae4aa9`.

**Changed**: no repository file.

**Created, scratch only**, under `scratchpad/r7/bin/`: `regen.bash`, `all.bash`, `r7_mutants.py`, and copies of `fetch.bash`, `run_suites.bash`, `ci_home_absent.bash` and `r6_mutants.py`. These live in tmpfs; copy them to `util/ad-hoc/` if they should be kept.

<!-- markdownlint-enable -->

---

## Round 7's fold-in, lane C2

Archived verbatim (1,865 characters, sha256 `6b2b8c0e5bc19465`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

# Lane C2: round-7 NIT-1 (A0 restore script's default Source root)

Q01 and Q02 are killed. **The A0 suite now has 17 tests, all passing.** I also killed Q07 while there.

`r7_mutants.py` on a scratch copy of the current tree killed 7 of its 8 mutants. **The one survivor, Q05, is untested on purpose**: it deletes the guard that refuses when `realpath -m` returns an empty path, and I found no input that makes it do so. Treat Q05 as equivalent, or keep it as a defensive line.

**Changed**: `tests/test_a0_restore_scripts.py` only. The A0 restore script itself (`util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash`) did not change.

**New tests** (R7 is `util/ad-hoc/2026-10-08_backup-phase-b-round4/R7.md`):
- **`test_the_production_default_root_is_the_real_home`** kills Q01 and Q02. With `YAMAGUCHI_SOURCE_ROOT` unset it checks:
  - `/home/pcalnon/a0-r7-probe-must-not-exist/x/y` gets exit 2, the message names `/home/pcalnon`, `duplicati-cli` does not run, and nothing is created;
  - a scratch path outside the home is accepted (exit 0), which is what kills Q01, whose default of `/` refuses everything;
  - the script text contains the literal `${YAMAGUCHI_SOURCE_ROOT:-/home/pcalnon}`.
- **`test_a_source_root_given_through_a_symlink_is_canonicalised`** kills Q07: a root named through a symlink still refuses a path under the real directory.
- **Safety net:** a PATH stub for `install` now refuses any `/home/*` argument. Under Q02 the script would otherwise have run `install -d` in the real home. The probe directory was confirmed absent after the mutant run.

**Checks**: 17 tests OK; flake8 at 512 and the CodeQL prescreen are both clean.

**Needed elsewhere**: no new CI wiring. In `docs/REFERENCE.md`, the A0 suite bullet can add: "the production default root `/home/pcalnon` is pinned, and a root given through a symlink is canonicalised".

<!-- markdownlint-enable -->

---

## Round 7's fold-in, lane P

Archived verbatim (2,284 characters, sha256 `1de2440664980f86`), lifted from the lane's report, saved from its transcript by session 097ae87b on 2026-10-08.

<!-- markdownlint-disable -->

Round 7 is folded into D and A, D is regenerated, and every check passes.

- **Edit count:** 79 (78 prose, 1 fence). Round 7 extended existing edits and added none.
- **D sha256:** `d1e0b855e74061db0e8604987d31a0188c29327a794bc7ba44a2a533bba05ccd`. A changed after this regeneration; D did not, so the hash still holds.

**Fixed (in D through the clearing script, and in A)**
- **NIT-2:** D's front matter now names all three kinds of remote file a Repair deletes, including empty or replaced index files.
- **NIT-3:** step 10's read-back in D and A no longer mentions the Repair dry-run options. Item (4)'s `export` check in step 8 is the safeguard.
- **NIT-4:** the log is removed with `sudo -u duplicati shred -u /home/duplicati/repair-dryrun.log`, in D and A.
- **NIT-5:** D and A now say "the one writable path the operator can read, besides the destination".
- **Unit comment:** D:705–707 now carries your text, "the remote files a Procedure B Repair deletes, copied aside first", via `--from-repo`.

**A §8 Round 7 entry:** 0 BLOCKER, 0 DEFECT, 7 NIT.
- NIT-1: fixed by C2. It records the new default-root test (kills Q01 and Q02), the symlinked-root test (kills Q07), and Q05 as equivalent.
- NIT-2 to NIT-5: fixed by P.
- NIT-6 and NIT-7: fixed by you.
- It states that no eighth round ran because round 7 found no DEFECT.
- I re-labelled the earlier A0 test counts, which read as current, as point-in-time: Round 5's "Suite counts now" now says "at round 5" with "(17 since round 7)" beside the 11, and Round 6's 15 now reads "15 tests then; 17 since round 7".

**Checks**
- **Clearing script:** applied 79; a second run says "no change"; `--check` gives "0 staged, 14 already current".
- **markdownlint v0.42.0:** clean on D and A, including after the last A edit.
- **Structure check:** 0 problems in D and A.
- **Snippet linter:** 14 blocks, 0 failures.
- **flake8:** clean.
- **Suites:** 141 tests OK across the seven suites. Re-run after C2's change, the A0 suite alone passes 17/17.

**Changed:** D (`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`, regenerated), A (`notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`), `util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py`.

<!-- markdownlint-enable -->
