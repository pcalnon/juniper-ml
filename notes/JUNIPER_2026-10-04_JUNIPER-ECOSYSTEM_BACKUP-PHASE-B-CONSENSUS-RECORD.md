# Backup arc, Phase B — validation rounds 2 and 3, the ml#2115 fix-forward lanes and the handoff validations, verbatim reports

**Project**: Juniper (workstation backup infrastructure, host `yamaguchi`)
**Author**: Paul Calnon
**Date**: 2026-10-04 (re-assembled 2026-10-05)
**Procedure**: [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
**Artifacts validated**: Phase B of [`JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`](JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md) §6.2 (rows B1, B3, B4, B5, B7, B8 and B10), including the regenerated [`JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`](JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md)
**Also validated**: the fix-forward of B2 (ml#2115), which landed as ml#2134, and the two handoffs that carried the work between sessions
**Status**: landed on `main` on 2026-10-05, AHEAD of the Phase B change it validates, so that its reports cannot be lost with an uncommitted worktree. The change itself — the artifacts and the prose the reports judge — is pending: `HANDOFF_2026-10-04_backup-phase-b-round3-fold-in-pending.md` carries it, and the fix-forward ml#2134 is the only part already on `main`
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
    block the merge;
  - N-2 to N-4: the archiver parses the record strictly. A report file or origin that disagrees with the
    archived one is refused unless `--replace` names it. A header edit, or text outside every section, is
    refused rather than discarded. `--check` compares bytes and exits 1 on a difference. The attack script
    covers each case;
  - N-5 to N-9: the harness README, the provenance wording, the drafts' CHANGELOG slot, the routing of
    round 3 lane B's open questions, and the small errors.

## Disposition of round 3

*Pending* — round 3's fold-in, a round 4 on its delta and on the whole procedure, and the Phase B PR are the
next session's work (`HANDOFF_2026-10-04_backup-phase-b-round3-fold-in-pending.md`). This section is completed
when that change lands.

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
