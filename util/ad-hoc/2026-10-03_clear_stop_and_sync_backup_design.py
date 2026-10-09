#!/usr/bin/env python3
"""Clear the backup design's STOP: record that its five defects are fixed in the artifacts, and sync the prose.

Project:     juniper-ml
Sub-Project: backup infrastructure
Author:      Paul Calnon
Created:     2026-10-03
Status:      ad-hoc -- document-of-record edit (Phase B of the 2026-10-03 assessment, its B7)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md
             notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md (section 6.2)
             util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py (the STOP this clears; same guards)

ORDER. Run `python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py --from-repo` FIRST: it rewrites the
design's tagged blocks from the repository files (the unit, the defaults file, the wrapper, the installer,
the env contract), which are canonical since ml#1999. This script then edits PROSE ONLY and refuses to
touch a fenced block -- the same fence gate as the 2026-09-24 script, so a prose edit that strayed into a
tagged block fails before anything is written.

What the prose edits record, each from a validated source:

1. THE STOP IS CLEARED (front matter, the block at the top of section 8, the six phase markers, section
   10.2's "next action", section 11 and 12). Its five defects: (1) the D-1 flag and D-9's two options now
   ship in util/systemd/duplicati.default, so step 0(a) can pass and the drift gate protects them; (2) the
   re-key is a script that keeps the OLD key in place for the decrypt start, swaps by a copy and one atomic
   `mv`, and delivers --disable-db-encryption through a runtime drop-in it removes with rm + daemon-reload
   (that flag SATISFIES --require-db-encryption-key, so it must never live in the defaults file); (3) the API clients gain
   serverstate/pause/resume and read one 0600 credential (the assessment's B2); (4) the snapshot timer is
   `disable --now` at the start of P0 and `enable --now` only after the first start has re-encrypted;
   (5) the snapshot unit carries ProtectSystem=strict WITH ReadWritePaths= on its output directory, runs the
   installed copy, and the installer carries the whole lane under its blessed-checksum gate. Beside the
   five: D13 (the env contract lives at /etc/duplicati/env), InaccessiblePaths= masks the sibling escrow
   copy, and the installer's first-install bug (I-36) is fixed. Residue that is NOT fixed here is listed in
   the clearing note (note 8a), as the STOP's own exit condition required.
2. PROCEDURE A2 LOSES THE UI PASSWORD (step 6, step 7, P0 step 0(a)): `wipe-encryption` clears
   `pbkdf-config`, the only home of the web-UI password since 2.1, and --webservice-disable-signin-tokens is
   applied unconditionally -- so A2 and B need the password-init hand start before the unit's first start,
   and A0 is the default path (the assessment's I-37, Lane B B-1, confirmed in the 2.4.0.0 source).
3. HOST FACTS THE RECORD LACKED (section 4.1's .env row, section 4.3 item 9): the 2026-09-22 .env rewrite
   and wrapper v2's actual next-start failure (exit 78 on SETTINGS_ENCRYPTION_KEY_OLD, before preflight).
4. P0.5B IS NEEDED ON PROCEDURE A ONLY (its heading, P1 step 1): on A0/A2/B the first start with the new
   credential encrypts the placed database, which was never under a compromised key in the new folder.
5. SECTION 7.7 and P0.5A ITEM 2 describe the lane as installed; P1 step 2 names /etc/duplicati/env; P0 step 8
   places the hand start before the first `systemctl start`; section 12 gains the row, note 12c (its files) and
   the ml#2113 reference in note 12b, and note 12a's D13 is closed.

6. THE PHASE B ROUND, FOLDED IN (2026-10-04; its reports are archived verbatim in
   JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md). All three lanes found that
   `systemctl revert` would DELETE the installed unit -- a dpkg vendor unit exists under /usr/lib/systemd/system/,
   and revert removes any unit overriding a vendor one -- so the re-key removes its drop-in with rm +
   daemon-reload and asserts FragmentPath. Also: the key swap is a copy then an atomic `mv`; an EXIT trap; the
   gate covers all five encrypted columns; P0.5b runs INSIDE step 10, before the operator's `resume`; the
   hand start sets the password only (`encrypted-fields` stays False until the unit's first start); step 8
   re-points `DBPath` with sqlite3 while no server runs and writes the settings key; step 10's dry-run refuses
   an empty URL -- the one fenced block this script changes, declared in FENCE_EDITS; the residue list; and
   section 7.6, section 7.9, P3 and AC-6/AC-10 record what ml#2114 and ml#2115 built.

7. ROUND 3 ON THE FOLD-IN, FOLDED IN (2026-10-08; reports util/ad-hoc/2026-10-04_backup-phase-b-round3/R3A.md,
   R3B.md, R3C.md). The owner's ruling on R3B DEFECT-1: step 10's edits REMOVE the job's `retention-policy`, so
   the first backup after recovery deletes nothing, and step 11 restores it -- as the NEW policy
   2W:1D,6M:1W,2Y:1M,5Y:2M -- only after AC-4's first drill has passed; every "nothing under
   /mnt/Backups/Ubuntu/ is deleted" sentence names that second exception, and step 11 states what the first
   pass under the new policy deletes (util/ad-hoc/2026-10-08_backup-phase-b-fold-in/retention_table.py).
   DEFECT-2: step 8 stores `paused-until` = 0 with sqlite3 while no server runs, reads `startup-delay` back,
   writes the web credential, and requires the first start to read Paused; the 12:00 watchdog check moves after
   step 10. DEFECT-3: Procedure B's rebuild tool runs only on a paused server, with a future 14:00Z schedule and
   every stale default listed. DEFECT-4: section 7.3.6's recovery deletes `pbkdf-config` too, and A2 leaves it.
   Also: step 8 copies the index's -wal/-journal/-shm; the residue list is now exactly the round-4 record's open
   rows plus ml#2134's job-2 list; Appendix C's item 4 is applied; the web-credential format; and the cheap NITs
   (P2 step 4's --backup-id, A2's re-entry after login, B's step order, the key write that refuses to overwrite,
   step 10's `id=` line, AC-6's P2 remnants, the 102 run's real effects). The artifact lanes' changes are
   described too: the env file's allow-list of eight tunables and the wider deny list (wrapper 2.3.0, now 2.4.0), the
   installer (1.3.0, now 1.5.1) judging env files by running the wrapper and copying never-blessed files aside, the
   snapshot's DELETE-mode file (1.2.0), the re-key's file-derived EXIT trap, its pre-flight count of
   never-rewritten blobs and its timer check; and step 8 warns about an existing /etc/duplicati/env and the
   BEHAVIOUR CHANGE an earlier blessing reports.

8. ROUND 4 ON THE FOLD-IN, FOLDED IN (2026-10-08; reports util/ad-hoc/2026-10-08_backup-phase-b-round4/R4A.md,
   R4B.md, R4C.md). R4B DEFECT-1: the job queued at the first start is a copy taken BEFORE step 10's edits, so
   step 10 now ends with a restart on A0, A2 and B (the queue is in memory only; the stored pause survives; the
   start re-queues from the edited database), an `export` read-back, and AC-3 as a manual run whenever the slot
   was used up. DEFECT-2: B's Verify runs only at resume. The NITs: the stored pause read before it is replaced,
   Running means stop the unit, --aes-version pinned and keep-* read back in step 10, the index copied (never
   moved) from a named path, the retention restore preceded by a copy of the five dlists and stated for one date
   range, post-recovery thinning, four blessed files, the wrapper versions, the STOP's three stale mentions, a
   D section 12 row, and one `gone` pattern for both marker deletions.

9. ROUND 5 (2026-10-08; R5A.md, R5B.md in util/ad-hoc/2026-10-08_backup-phase-b-round4/). R5B DEFECT-1: the
   server's default options (Option rows at BackupID -1) never appear in `export`, so step 8 clears their
   retention-policy / keep-time / keep-versions with sqlite3 and step 11 restores them only with the policy.
   DEFECT-2: Repair deletes remote volumes the index does not know, so B's Repair runs with --dry-run first,
   every file it would delete is copied aside, and Repair is the third, conditional exception. R5A DEFECT-2:
   an existing /etc/duplicati/env passes in either of O-12's forms and the installer does not settle O-12.
   Also: the orphan copy's place and shred, B's queue already holding a backup, the blessed-file count
   against origin/main, and the installer hint's stop / restart / `…-key.new`.

10. ROUND 6 (2026-10-08; R6.md). DEFECT-1: B's Repair dry run is a mechanism — three job options, a log file under
   ReadWritePaths, four DryRun message ids, the options removed and read back before the real Repair — and the
   third exception names every kind of remote file a Repair deletes. DEFECT-3: keep-time / keep-versions defaults
   are never restored (they combine with the policy, DeleteHandler.cs:82-87). NIT-1: the defaults SQL is
   case-insensitive.

Guards (identical in kind to the 2026-09-24 script): every anchor exactly once; `old` never a substring of
`new`; no new line over 512 characters -- a prose line the edits push over it is wrapped at word boundaries by
the 2026-09-21 helper's algorithm, with the list item's content indentation, while a table row cannot be and
is shortened by hand (the gate refuses one that is not); every fenced block byte-identical except the ones
FENCE_EDITS declares, which must change into exactly the declared text; the stale phrases absent after.
Round 3 added three (R3C N-3, N-11): FIXFWD_PR must be `ml#<digits>` (checked before anything is read); an
edit that DELETES text counts as already applied only when its `gone` pattern no longer matches, so a reworded
marker on main fails instead of passing as ALREADY; and the STOP block is replaced only when it is
byte-identical to the one this script was written against (STOP_SHA256), so an item main adds inside it is
refused rather than dropped. tests/test_clear_stop_backup_design.py exercises the gates (R3C D-5).
"""

from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

DESIGN = Path("notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md")
ASSESS = "JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md"
RECORD = "JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md"
# The ml#2115 fix-forward (export's single-operation token; the watchdog's absent id): ml#2134, opened 2026-10-04.
# FIXFWD_PR overrides it; main() refuses, before reading anything, any value that is not `ml#<digits>` -- the
# placeholder `ml#FIXFWD`, an empty value and `ml#fixfwd` alike (round 3, R3C N-3: only the exact placeholder was
# refused, and only once it had reached the text).
FIXFWD = os.environ.get("FIXFWD_PR", "ml#2134")
FIXFWD_FORM = re.compile(r"ml#[0-9]+")
# The retention policy step 11 restores (the owner's ruling of 2026-10-08) and the one step 10 removes.
NEW_RETENTION, OLD_RETENTION = "2W:1D,6M:1W,2Y:1M,5Y:2M", "1W:1D,1M:1W,1Y:1M,3Y:2M"
RETENTION_TOOL = "util/ad-hoc/2026-10-08_backup-phase-b-fold-in/retention_table.py"
WRAP_HELPER = Path("util/ad-hoc/2026-09-21_wrap_long_markdown_lines.py")
WIDTH, TARGET = 512, 480
NO_WRAP = ("|", "#", "<!--", ">", "[", "```")  # the helper's own exclusions: shortened by hand, never wrapped
FENCE = re.compile(r"^([ \t]*)```[^\n]*\n.*?^\1```", re.M | re.S)
EDITS: list[tuple[str, str, str, int]] = []
# For an edit that DELETES its anchor (new == ""): a regex that must NOT match once the deletion is in place.
# Without it, "already applied" was vacuously true, so main rewording the anchor passed as ALREADY and the
# reworded text survived (round 3, R3C N-11).
GONE: dict[str, re.Pattern[str]] = {}
# Fenced blocks this edit set changes on purpose: (old body text, new body text). Each must occur in exactly one
# fence before, and the fence gate then requires every other fence to be byte-identical and these to equal
# exactly the declared result. An untagged operator command, never a tagged block (--from-repo owns those).
FENCE_EDITS: list[tuple[str, str]] = []

STALE = (
    "§8 is behind a STOP",
    "**STOP — §8 is held",
    "§8 is not executable as written",
    "*Held by the STOP at the top of §8 (note 10.1g).*",
    "*Items 2 and 4 are held by the STOP",
    "the next action in this arc is the follow-up change that clears the STOP",
    "so the **UI password survives** and",
    "D13 is open (note 12a)",
    "and `--disable-db-encryption` appended to `DAEMON_OPTS`",
    "Install it at /etc/duplicati/env in a 0755 root:root\n# directory and point the wrapper's DUPLICATI_ENV_FILE default there.",
    "set it to the §7.3.5 contract. **Mode:",
    "1,599 B | — | one active line",
    "Scrub both log stores** — `/var/log/syslog*` *and* the journal",
    # the Phase B round's fold-in (2026-10-04): main's prose these edits replace, and the round's own errors
    "nine are landed and one is not",
    "all nine scripts §8 invokes are merged; the tenth is a P3 deliverable",
    "then **P0.5b** (the re-key, same session as step 8",
    "UI **Database → Placement → Save**, or `PUT /api/v1/backup/<id>`",
    "`RestConnection.cs`",
    "and refuses a non-server database",
    "Expect in the journal: schema upgrade 11→12 and",
    "Land the client changes (the credential path **and** the new `pause`/`resume` subcommands)",
    "(extended with `pause`/`resume`)",
    "becomes provable only when the snapshot lane is re-pointed",
    "Expect 97 directories to change owner",
    "and the census goes through the second",
    "**The deployed watchdog unit takes no `--backup-id`**",
    "observe one SKIPPED (unplugged) and one OK (plugged) run",
    "so no reporter change is needed",
    "the installer and `juniper-backup-failure.service` have not",
    "the same scheduler with `JUNIPER_BACKUP_DEVICES` set to the drive's mount name",
    "a run with no drive reads `SKIPPED`; a run with a drive attached",
    "**(A P2 criterion — not provable at the end of P0.)**",
    "removes with `systemctl",
    "`systemctl revert` removes the drop-in",
    "one-`mv` key swap",
    "after step 11 — it pauses the scheduler",
    "immediately after P0 step 11, same session",
    "its placement is after step 11",
    "and step 9's client change, which must land with §7.6's re-pointing before P0 runs,",
    "| `home/duplicati/.config/Duplicati/.env` | `.env` contract |",
    # round 3 on the fold-in (2026-10-08)
    "is deleted or moved except the in-tree escrow",
    "with exactly one exception, and it needs owner sign-off",
    "this is the single exception to the",
    "is deleted or moved.\n2. **The local database",
    "so it will start on its own once the startup pause lapses",
    "update its defaults before use",
    "None of items 1–10 has been applied",
    "the six ad-hoc job scripts",
    "(the credential this needs was created in step 9)",
    "makes AC-6 unprovable until P2",
    "**AC-6 is a P2 criterion**",
    "Procedures A0, A and A2 all recover a database",
    "sets the password and nothing else",
    "and the passphrase — through the **web UI** or `util/ad-hoc/yamaguchi_build_job.py`",
    "redeploy with `util/ad-hoc/yamaguchi_watchdog_deploy.bash`.",
    "confirm the next 12:00 fire reads",
    "refuses security options there",
    "an EXIT trap removes the drop-in and reports what an interrupted run left",
    # round 4 on the fold-in (2026-10-08)
    "the STOP at the top of §8",
    "every post-recovery fileset younger than two weeks stays",
    "between late October 2026",
    "three blessed files",
    "which `resume` fires immediately",
    "move the index, re-point",
    "so the two cannot disagree",
    "R4C-NIT-4",
    # round 5 on the fold-in (2026-10-08)
    "in the job or in the server's default options",
    "with exactly two exceptions",
    "refuses any other owner or mode",
    "while the server is stopped and a copy is kept",
    "there is nothing to compare and it does not",
    f"`--no-auto-compact=true`, `retention-policy={OLD_RETENTION}`, `--asynchronous-upload-limit=1`,\n`--allow-missing-source",
)


def edit(tag: str, old: str, new: str, count: int = 1, gone: str | None = None) -> None:
    if old in new:
        raise SystemExit(f"NON-IDEMPOTENT edit {tag!r}: `old` is a substring of `new`.")
    if new == "":
        if gone is None:
            raise SystemExit(f"edit {tag!r} deletes its anchor and names no `gone` pattern")
        GONE[tag] = re.compile(gone)
    EDITS.append((tag, old, new, count))


def fence_edit(tag: str, old: str, new: str) -> None:
    """An edit INSIDE one untagged fenced block, declared so the fence gate accepts exactly this change."""
    edit(tag, old, new)
    FENCE_EDITS.append((old, new))


# --------------------------------------------------------------------------------------------
# Front matter
# --------------------------------------------------------------------------------------------

edit(
    "front matter: status",
    "- **Status**: HELD, except what note 10.1g releases — §8 is behind a STOP (rounds 4–8, 2026-09-24). Rounds 1 and 2 are reconciled; round 3 found 15 defects and 13 were applied, D13 is open (note 12a); rounds 4–8 found defects in §8's procedure, which are open (§11). The owner's rulings are in §10.1.",
    "- **Status**: EXECUTABLE in the order below, since 2026-10-03 — the STOP of 2026-09-24 is cleared: its five procedure defects, and the findings beneath them, "
    "are fixed in the artifacts §8 installs (note 8a); what is not fixed is listed there as residue. Rounds 1 and 2 are reconciled; round 3's D13 is closed "
    "(the env contract lives at `/etc/duplicati/env`); rounds 4–8's §8 defects are closed (§11). The owner's rulings are in §10.1. "
    f"The execution plan — who does what, in which sitting — is `{ASSESS}` §6.",
)

edit(
    "front matter: STOP bullet becomes the clearing",
    "- **STOP — §8 is held, except what the owner released on 2026-09-24.** Rounds 4–8 found defects in the procedure that can re-lock the recovered database, pass the pre-backup guard without its `TargetURL` check, or copy a cleartext database into the backup Source. The STOP block at the top of §8 lists them and what may run now — P0.5a items 1, 5, 6 and 7, P3's tier-2 fix, §6's sink checklist, S-4's "
    "`chmod 0600` and the reads it names — within its two limits (note 10.1g); the rest waits until it is gone.",
    "- **The STOP of 2026-09-24 is cleared (2026-10-03, note 8a).** The owner's release of that day (note 10.1g) stands as history: its two limits still bind — no history file is wiped before P0 step 3 has tested the key candidates it may hold, and the transcript limit is discharged, every round of this arc being archived on `main` — and everything it held is now runnable in the order below.",
)

edit(
    "front matter: order heading",
    "- **§8's order once the STOP is cleared — this and no other, unless the follow-up changes it**: **P0.5a** items 1, 2 and 4, in that order,",
    "- **§8's order — this and no other**: **P0.5a** items 1, 2 and 4, in that order,",
)

edit(
    "front matter: the order's review step names every script (the Phase B round)",
    "then **P0 step −1** (a review — all nine scripts §8 invokes are merged; the tenth is a P3 deliverable)",
    "then **P0 step −1** (a review — every script §8 invokes is merged on `main`; the paragraph after note 8a names them)",
)

edit(
    "front matter: P0.5b runs inside step 10 (the Phase B round)",
    "then **P0 steps 1–8**, then **P0.5b** (the re-key, same session as step 8 — it needs the recovered data folder), then **P0 steps 9–11**.",
    "then **P0 steps 1–9**, then **P0 step 10** — on Procedure A with **P0.5b** (the re-key) run inside it, after its edits and in place of "
    "the operator's `resume` — then **P0 step 11**.",
)

# --------------------------------------------------------------------------------------------
# Section 4 -- two host facts the record lacked (the assessment, section 3)
# --------------------------------------------------------------------------------------------

edit(
    "section 4.1: the .env row records the 2026-09-22 rewrite",
    "| `.env` | `/home/duplicati/.config/Duplicati/.env` 0660 duplicati:duplicati, 1,599 B | — | one active line (`SETTINGS_ENCRYPTION_KEY`, 32-char value, single-quoted, contains `$ @ & #`), five commented-out lines carrying `PASSPHRASE_OLD`, `PASSPHRASE` and three spellings of the key; **the active key equals `PASSPHRASE`** | `2026-09-21_env_file_shape.py` |",
    "| `.env` | `/home/duplicati/.config/Duplicati/.env` 0660 duplicati:duplicati, 1,599 B on 09-21; **0640, 1,701 B since 09-22** (note e) | — | "
    "on 09-21 one active line (`SETTINGS_ENCRYPTION_KEY`, 32-char value, single-quoted, contains `$ @ & #`), five commented-out lines carrying "
    "`PASSPHRASE_OLD`, `PASSPHRASE` and three spellings of the key; **the active key equals `PASSPHRASE`**; since 09-22 **two** active lines, "
    "`_OLD` fatal to wrapper v2 (note e) | `2026-09-21_env_file_shape.py`; re-run 10-03 |",
)

edit(
    "section 4.3 item 9: wrapper v2 changed the next-start failure",
    "9. The unit now loaded (`ExecStart=… '--daemon-opts=\"${DAEMON_OPTS}\"'`, armed by a global systemd reload at 03:23:44 on 09-21) and both wrapper revisions are mutually incompatible:",
    "9. *(Measured again 2026-10-03: the live symlink has resolved to wrapper v2 since 09-22 12:56, which passes the armed word through as an unknown "
    "option and supplies its own port default — so the argv incompatibility below is history. The next start now fails **earlier**: v2 exits 78 at the "
    "`.env`'s `SETTINGS_ENCRYPTION_KEY_OLD` line, before `preflight()`; and were that line removed, the 0700 gate refuses the 0777 folder as before. "
    "Two blockers, both closed by P0; the verdict \"does not start\" is unchanged.)* The unit now loaded (`ExecStart=… '--daemon-opts=\"${DAEMON_OPTS}\"'`, "
    "armed by a global systemd reload at 03:23:44 on 09-21) and both wrapper revisions of 09-21 are mutually incompatible:",
)


edit(
    "section 4.1: note (e) for the .env rewrite",
    "only before 09-18 21:03 (Appendix C item 9).\n\nEvery row above is a **Lane A subject**:",
    f"only before 09-18 21:03 (Appendix C item 9).\n- **(e)** The `.env` was rewritten on 2026-09-22 at 19:17:37 CDT (00:17Z on 09-23 — 24 minutes before ml#2029's first commit, so that\n"
    "  PR, which recorded that the new secret \"does NOT go in `.env`\", did not know of it): 0640 duplicati:duplicati, 1,701 B, two active\n"
    "  lines — `SETTINGS_ENCRYPTION_KEY_OLD` holding a 32-character value (the length of the previous active key) and\n"
    "  `SETTINGS_ENCRYPTION_KEY` holding a new 64-character one — with the five commented-out assignments still present. The\n"
    "  directory's mtime twelve seconds after the write, with no swap file left, reads as an interactive rename of the old key plus a\n"
    "  new one (an inference; O-1 of the assessment). `SETTINGS_ENCRYPTION_KEY_OLD` is read by nothing in 2.4.0.0 (note 10.1b) and is\n"
    "  fatal to wrapper v2 (exit 78, before `preflight()`; §4.3 item 9). Measured with `2026-09-21_env_file_shape.py` through\n"
    f"  `sg duplicati`, names and lengths only (`{ASSESS}` §3, note 3a).\n"
    "\nEvery row above is a **Lane A subject**:",
)

# --------------------------------------------------------------------------------------------
# Section 7 -- the env contract's home, the snapshot lane as installed
# --------------------------------------------------------------------------------------------

# (The section 7.3.5 contract block is a TAGGED block: --from-repo rewrites it from
# util/systemd/duplicati-env.contract, which carries the settled text itself. No prose edit here.)

edit(
    "section 7.7: the lane as installed",
    """`util/ad-hoc/yamaguchi_server_db_snapshot.py` keeps `SRC = /usr/lib/duplicati/data/Duplicati-server.sqlite`.
After recovery it must read `/home/duplicati/.config/Duplicati/Duplicati-server.sqlite`. Its docstring lines
20 and 36 ("the encrypted passphrase") are corrected to state the actual condition: encrypted only when the
settings key is in force (D-1).""",
    """*(As built 2026-10-03, the assessment's B3.)* `util/ad-hoc/yamaguchi_server_db_snapshot.py` (1.1.0; 1.2.0 since 2026-10-08) reads
`/home/duplicati/.config/Duplicati/Duplicati-server.sqlite` and its docstring states the actual condition of
the passphrase (encrypted under the settings key since 2026-09-18, cleartext before — §5.4). The unit
`util/systemd/yamaguchi-server-db-snapshot.service` executes the **installed copy**
`/usr/local/lib/duplicati/yamaguchi_server_db_snapshot.py` under `ProtectSystem=strict` **with**
`ReadWritePaths=/home/pcalnon/.local/state/duplicati-server-db` (the STOP's item 5: `strict` alone broke the
snapshot), `ProtectHome=read-only` and `PrivateTmp=yes`; `util/install_duplicati_service.bash` installs the
script, the unit and the timer under its blessed-checksum gate, so the lane changes only by re-running it.
The script opens the source `mode=ro`, and `ProtectHome=read-only` makes the data folder read-only to the
unit, so SQLite can read the WAL-mode database only while its `-wal` and `-shm` already exist — it cannot
create them. While the server runs they do; a fire after a clean close that removed them fails closed, with an
SQLite error (the Phase B round, lane A NIT-6).""",
)

edit(
    "section 7.6: both clients read the one credential, and the census uses the FIRST (the Phase B round)",
    "- **One credential path, in both clients, in the same PR.** `util/ad-hoc/yamaguchi_server_api.py:41` hard-codes `CRED_FILE` to the primary "
    "checkout's `.env`, and `util/ad-hoc/duplicati_api.py`'s `PW_FILE` defaults to the same file; `util/ad-hoc/yamaguchi_reboot_verify.bash:73` "
    "calls the first and the census goes through the second. Re-pointing only one of them leaves every acceptance instrument 401-ing after the "
    "password rotates — which is exactly today's watchdog symptom.\n"
    "  Both move to `~/.config/duplicati-backup/web-credential`, and P0 is ordered so that file exists **before** AC-2 runs.",
    "- **One credential path, in both clients — built (B2, ml#2115).** `util/ad-hoc/yamaguchi_server_api.py` and `util/ad-hoc/duplicati_api.py` "
    "both read `~/.config/duplicati-backup/web-credential` (0600) through one parser, `read_credential()`; until ml#2115 the first hard-coded the "
    "primary checkout's `.env` and the second defaulted to it. `util/ad-hoc/yamaguchi_reboot_verify.bash:73` and the census "
    "(`util/ad-hoc/yamaguchi_census.py:37`) both go through the **first** client; until 2026-10-04 this paragraph said the census used the "
    "second, whose only importer is `util/ad-hoc/duplicati_build_fresh_job.py`. Re-pointing only one of them would have left every acceptance "
    "instrument 401-ing after the password rotates, which is the watchdog's daily symptom since 09-18.\n"
    "  P0 is ordered so that file exists **before** AC-2 runs.",
)

edit(
    "section 7.6: the watchdog's job id (the Phase B round; the ml#2115 fix-forward)",
    "- **The deployed watchdog unit takes no `--backup-id`**, so it uses the client's default of 2. If recovery assigns the job a different id "
    "(Procedure B always does — `sqlite_sequence` starts at 1), the unit must be redeployed with `--backup-id <id>` or it alerts `JOB_MISSING` forever.",
    "- **The job id has no default since B2.** The repository unit passes `--backup-id ${YAMAGUCHI_BACKUP_ID}`, which the drop-in written by "
    "`util/ad-hoc/yamaguchi_watchdog_deploy.bash --backup-id <id>` sets. The unit still loaded on the host predates that and passes no id: "
    "the 2026-10-04 12:00 check, the first to run the B2 script through it, exited 2 and wrote no record. Since "
    + FIXFWD
    + " an absent id is recorded as `ALERT JOB_MISSING` instead. So run the deploy script right after every sync of the primary checkout, "
    "and again whenever recovery assigns the job a new id (Procedure B always does — `sqlite_sequence` starts at 1).",
)

edit(
    "section 7.9: the fstab drive uses the relative form (the ml#2114 lane)",
    "the same scheduler with `JUNIPER_BACKUP_DEVICES` set to the drive's mount name, `JUNIPER_BACKUP_PERIOD_DAYS=30`",
    "the same scheduler with `JUNIPER_BACKUP_MEDIA_ROOT=/mnt` and `JUNIPER_BACKUP_DEVICES=JuniperArchive` — the relative (leaf) form, which the "
    "scheduler and the runner resolve to the same path — `JUNIPER_BACKUP_PERIOD_DAYS=30`",
)

edit(
    "section 7.9: the absolute form as built, and runner-only (the ml#2114 lane)",
    "`util/juniper-backup.bash` needs one change for this: a `MEDIA_NAMES` entry beginning with `/` is taken as an absolute mount root (today "
    "every entry is forced under `/media/pcalnon/`, a path udisks stopped using on\n"
    "  2026-09-07, §4.5 — so the change is required for Tier 2 as well, not only for the external drive).",
    "*(As built 2026-10-03, ml#2114.)* `util/juniper-backup.bash` takes an entry beginning with `/` as an absolute mount root, accepted only "
    "strictly under `/mnt`, `/media` or `/run/media`. That form is **runner-only**: the scheduler prefixes `${MEDIA_ROOT}` to every entry, so it "
    "never finds such a drive and the lane never runs on it — which is why the cadence above uses the relative form. Both now default to "
    "`/run/media/$USER`; the runner used to force `/media/pcalnon/`, a path udisks stopped using on 2026-09-07 (§4.5), so the change was\n"
    "  required for Tier 2 as well, not only for the external drive.",
)

# --------------------------------------------------------------------------------------------
# Section 8 -- the STOP block becomes the clearing note; phase markers; steps
# --------------------------------------------------------------------------------------------

STOP_START = "> **STOP — §8 is not executable as written (rounds 4–8, 2026-09-24).**"
STOP_END = "> (Procedure B's first start is step 7, and the overdue job can run before `resume`); and the lower-severity\n> items the record lists.\n"
# sha256 of the STOP block, STOP_START through STOP_END, as origin/main carries it (81d3fbb3; unchanged since
# ml#2113). The block is replaced whole, so a block that differs -- an item main added inside it -- is refused
# rather than silently dropped (round 3, R3C N-11).
STOP_SHA256 = "994ac7a4a0ff7ea95fc83d18a85bc22d179626a2d82cfa09d402db69f43af265"

CLEARED = f"""> **The STOP of 2026-09-24 is cleared — 2026-10-03 (note 8a).** Rounds 4–8 found five defects in this
> procedure. Each is fixed in the artifact that would have executed it, not in prose, and the artifacts are
> what §8 installs:
>
> 1. **Step 0(a) can pass.** `--require-db-encryption-key` (D-1), `--webservice-disable-signin-tokens` and
>    `--webservice-allowed-hostnames=localhost` (D-9, §7.3.6) ship in `util/systemd/duplicati.default`'s
>    `DAEMON_OPTS`, so the installed copy carries them and D-6's drift gate protects them. Note that the
>    signin-token flag is applied **unconditionally at every start** (Server `Program.cs`), so "once a password
>    exists" is an order the procedure keeps — step 10 — not a property of the flag.
> 2. **The re-key cannot re-lock the database.** `util/ad-hoc/2026-10-03_rekey_settings_key.bash` (Procedure A
>    only) keeps the old key at the credential path for the decrypt start and the new key at `…-key.new`, and
>    delivers `--disable-db-encryption` through a runtime drop-in under `/run/systemd/system/` — never through
>    `/etc/default/duplicati`, because that flag **satisfies** `--require-db-encryption-key` and would decrypt the
>    database silently on every later start. It removes the drop-in with `rm` and `daemon-reload` and then asserts
>    that systemd still loads the installed unit — **never `systemctl revert`**: a dpkg vendor unit exists under
>    `/usr/lib/systemd/system/`, so revert would delete the installed `/etc/systemd/system/duplicati.service` and
>    the encrypt start would run the vendor unit, unconfined and without `LoadCredential=` (the Phase B round's
>    BLOCKER, found by all three lanes). The key swap is a copy then one atomic `mv`, so the credential path is
>    never absent. An EXIT trap stops the unit while a drop-in is present, removes the drop-in, names each key
>    file by hash (swapped / not swapped / unexpected), reports the database as UNKNOWN once a decrypt or
>    encrypt start was attempted without its "Server has started" line, prints the gate's counts on a gate
>    failure, and prints only the recovery that applies, never "start the unit" after a FragmentPath refusal;
>    a refusal before the pause says nothing changed (Phase B round 3: lane A D-4, lane B N-11, lane C D-1).
>    Before the first stop it counts, on a copy of the database, the `enc-v1:` blobs the product's
>    re-encryption never rewrites: any in `ConnectionString`, and any in an `Option`, `Source` or
>    `BackupTargetUrl` row whose BackupID names no backup. `Option` and `Source` have no foreign key
>    (`Schema.sql:44-45, 72-73`), so a deleted job's rows can outlive it. The settings rows at -1 and -2 are
>    rewritten (`Connection.cs:145`; `ServerSettings.cs:851-855` → `SetSettings(-2)`), and so are a live
>    backup's rows. It refuses if there is one, or if the count itself fails, because such a blob would stay
>    under the old key and fail the exit gate only after the key swap (lane A D-5, lane C D-2; round 4, lane
>    C DEFECT-2). Remedy, the owner's: saved connection strings are deleted through the web UI and re-created
>    after the re-key; an orphaned row, which the UI cannot reach, is deleted with sqlite3 while the unit is
>    stopped (it comes up Paused again), a copy of the database first kept in a root-only 0700 directory outside
>    `/home/pcalnon` and shredded (`shred -u`) once the exit gate has passed — on Procedure A that copy holds
>    blobs under the compromised 09-18 key (Phase B round 5, lane B NIT-3). It refuses unless the snapshot timer is neither enabled (in any form, `enabled-runtime` and
>    `linked` included) nor active (lane B N-8), and while a task is active; it pauses the scheduler through the
>    API before the decrypt start (an indefinite pause persists across both starts; an overdue schedule is
>    queued at every start), and its exit gate, on a copy, is
>    `encrypted-fields` True and every `enc-v1:` blob in all five encrypted columns under the new key
>    (`util/ad-hoc/2026-10-03_rekey_gate.py`), with no drop-in present.
> 3. **Step 10's guard dry-run cannot pass on an empty `TargetURL`.** The API clients read one 0600 credential
>    (`~/.config/duplicati-backup/web-credential`), carry `serverstate`/`pause`/`resume`, and require
>    `--backup-id` (the assessment's B2, ml#2115). `export` obtains the single-operation token 2.4.0.0 requires
>    and prints nothing on stdout when it fails ({FIXFWD}; ml#2115 alone sent the Bearer header, and every
>    export was HTTP 400). Step 10's dry-run now refuses an empty URL before it runs the guard.
> 4. **The snapshot timer cannot copy a cleartext database into the Source.** It is `disable --now` at the start
>    of the P0 session (a plain `stop` does not survive a reboot under `Persistent=true`) and `enable --now` only
>    at `{ASSESS}` §6.4 step 13, after the first start has re-encrypted the placed database and that is verified
>    on a copy.
> 5. **`ProtectSystem=strict` does not break the snapshot.** The unit carries `ReadWritePaths=` on its output
>    directory and executes the installed copy (§7.7).
>
> Beside the five: round 3's D13 is closed (`/etc/duplicati/env`, §7.3.5); `InaccessiblePaths=` masks the sibling
> escrow copy `/mnt/Backups/Ubuntu/_yamaguchi_keys` that P0.5a item 5 creates; the installer's first-install bug
> is fixed (with no blessed file it ended silently — `{ASSESS}` I-36); the wrapper no longer exports
> `DUPLICATI__*` names from the env file (2.2.0) — the server reads `DUPLICATI__<OPTION>` for **every** option,
> including `disable-db-encryption` — accepts only allow-listed tunables there (2.3.0, below), and redacts
> `--print-command` by option name; and **Procedure A2 is no longer the cheap path**: `wipe-encryption` clears `pbkdf-config`, the only
> home of the web-UI password, so A2 and B need the password-init hand start
> (`util/ad-hoc/2026-10-03_password_init_hand_start.bash`, steps 6–8). It sets the password, upgrades the
> schema and re-encrypts the password-named server settings under the settings key; the backups' fields and
> `encrypted-fields` are unchanged until the unit's first start; and A0 is the default.
>
> Round 3's fold-in (2026-10-08) tightened the env file further. Its `--option` lines are now an allow-list
> of eight tunables (wrapper 2.3.0; 2.4.0 now); the deny list, kept for its specific refusal, gains
> `--parameters-file`/`--parameterfile` (the server reads that file in-process and copies its options over
> argv), `--webservice-enable-forever-token`, `--webservice-cors-origins` and the alias
> `--webservice-allowedhostnames`; and the installer (1.3.0; 1.5.1 now) judges the contract — and any existing
> `/etc/duplicati/env` — by running the wrapper itself, so both apply one grammar. Since 1.4.0 the installer also
> checks an existing `/etc/duplicati/env`'s owner and mode, and since 1.5.0 it accepts exactly O-12's two forms —
> `root:duplicati` 0640 or `duplicati:duplicati` 0600, a regular file, never other-readable — so the grammar check
> (run as root) and the service's read (as `duplicati`) agree on the file itself; it does not settle O-12 (§11;
> P1 step 2). A first install copies a
> never-blessed file that differs from the repository's aside (`<file>.pre-install-<UTC>`) before replacing
> it; the snapshot script (1.2.0) writes a single DELETE-mode file with no `-wal`/`-shm` beside it; and the
> snapshot unit's `ReadWritePaths=` stays without a `-` prefix, so a missing destination fails the unit
> closed (the installer prints a NOTE rather than creating it).
>
> Round 4 (2026-10-08): wrapper 2.4.0 makes an empty `DUPLICATI_REQUIRE_MOUNT` switch its mount check off
> (with `:-` the installer's contract gate and every suite silently depended on `/mnt/Backups` being mounted
> and would fail on CI); the allow-listed welcome-page tunable is `--webservice-suppress-welcome-page`, the
> server's real name, and both lists are now pinned against a vendored copy of the product's option table
> (`tests/fixtures/duplicati_2.4.0.0_server_options.txt`); every trailing CR is stripped and a NUL in the key
> refused. Installer 1.4.0 (1.5.1 now) refuses an unblessed differing file without `--update-backup-behavior`, checks an
> existing env file's owner and mode, says where it copied a file aside, and prints step 8's prerequisites
> and step 10's guard block verbatim; since round 5 the hint also says to stop the unit (never `pause`) if the
> first start reads Running, includes step 10's restart, and names Procedure A's `…-key.new`. The re-key (1.3.0) and its gate (1.2.0) also refuse orphaned `Option`
> and `Source` blobs, and the gate and the hand start (1.3.0) refuse a NUL in a key file.
>
> **Residue, recorded as the STOP's exit condition required** (`{ASSESS}` I-41 and note 5b, which lists the
> same items; the round-4 record's follow-up rows, rounds 4–8). Closed since that list was drawn: round-4 B14
> (the installer's hint uses `env`), B16 (P1 step 2 names the moved-aside `.env`), B17 (step 8 re-points
> `DBPath` while no server runs), B18 (AC-6 waits for the first fire after the timer is re-enabled), and B26
> and U2 (moot: Python's `sqlite3`; I-28). Open: AC-14's raw `\\|`; P0 step 1's second listing; §4.1/§7.3.1's
> "P0.5 closes 0777 `.config`"; the no-print key-candidate extractor for P0 step 3 (built only if Phase C's
> history counts are non-zero); round-4 B11, B13, B15, B22 (AC-8's undefined "hardening timestamp"), B24, B27,
> U1, U3 and U4; from the record's round-5 disposition, P0 step 8's own over-broad file-mode sentence; from its
> round-6 disposition, the frozen 811-volume copy and `PASSPHRASE_OLD`, which have no route (the owner's O-9),
> and what §10.2 step 7's swap does with the local pre-rotation set; from its round-8 disposition, note
> sink-c's counting method; Appendix C's corrections other than item 4; wrapper v2's `die` path with an
> `=`-less word; the sign-in URL logged whatever the token flag says (round 5); the sdc4 read-only loop probe
> and the frozen evidence mirror (D-12a); the Dropbox account audit after "Delete forever" (P1 step 4);
> Procedure B's statement on `additional-report-url` (S-8); `confirm_a0_premise.bash`'s "here" comment; and
> ml#2115's job-2 residue, twelve ad-hoc scripts ({FIXFWD}'s list). Eight take a job-id flag that defaults to
> 2 — pass the id explicitly: `--backup-id` in `yamaguchi_census.py`, `yamaguchi_edit_setting.py`,
> `yamaguchi_edit_sources.py`, `yamaguchi_edit_target.py`, `yamaguchi_config_record.py`,
> `duplicati_source_measure.py` and `duplicati_size_histogram.py`, `--source-job` in
> `duplicati_build_fresh_job.py`. Four
> hard-code job 2 on six lines and take no id at all, so after a recovery that assigns another id they must
> not be run: `yamaguchi_switch_aes.py` (three lines, among them a **PUT** to `/api/v1/backup/2`),
> `yamaguchi_retire_tier3.py`, `old_archive_purge.py` and `yamaguchi_retire_tier2.bash`. None changes a step
> that runs on the host before P1, except P0 step 3 if Phase C's history counts are non-zero: the extractor is
> its instrument.
"""

edit(
    "section 8: the STOP block becomes the clearing note",
    STOP_START,
    "\x00STOP-REPLACED\x00",
)


def reflow(original: str, text: str) -> tuple[str, int]:
    """Wrap each prose line the edits pushed over WIDTH at word boundaries, with the list item's content indentation.

    The algorithm is the 2026-09-21 helper's (`wrap_line`, imported from its file), which is how §8's long steps
    were wrapped in the first place, so the result matches the surrounding text. Only lines absent from the
    original are candidates; a table row, heading, comment, blockquote or link definition is left for the width
    gate to refuse, because none of those can be wrapped.
    """
    spec = importlib.util.spec_from_file_location("wrap_long_markdown_lines", WRAP_HELPER)
    if spec is None or spec.loader is None:
        raise SystemExit(f"FATAL: cannot load {WRAP_HELPER}")
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    before = Counter(line for line in original.split("\n") if len(line) > WIDTH)
    out: list[str] = []
    wrapped = 0
    for line in text.split("\n"):
        if len(line) > WIDTH and not before[line] and not line.lstrip().startswith(NO_WRAP):
            pieces = helper.wrap_line(line, TARGET)
            if len(pieces) > 1:
                wrapped += 1
                out.extend(pieces)
                continue
        out.append(line)
    return "\n".join(out), wrapped


def already_applied(text: str, new: str) -> bool:
    """True when `new` is in the text already -- compared with runs of whitespace collapsed, because the reflow
    may have wrapped it, or (for the STOP marker) when the clearing note is in place."""
    if new == "":
        raise AssertionError("a deletion is checked through its GONE pattern, in main()")
    if new == "\x00STOP-REPLACED\x00":
        return CLEARED.split("\n", 1)[0] in text
    squash = re.compile(r"\s+")
    return squash.sub(" ", new) in squash.sub(" ", text)


def replace_stop_block(text: str) -> str:
    """Replace the whole STOP block (its first line through STOP_END) with CLEARED; whole-block, not anchored."""
    start = text.index("\x00STOP-REPLACED\x00")
    end = text.index(STOP_END, start) + len(STOP_END)
    return text[:start] + CLEARED + text[end:]


# One pattern for both marker deletions: any italic line that still names the STOP. Until round 4 the patterns
# required "held by the STOP", so a rewording that dropped "held" passed as ALREADY (R4C NIT-1, mutant X33).
MARKER_GONE = r"(?im)^\*[^*\n]*\bSTOP\b"


def stop_block_digest(text: str) -> str | None:
    """sha256 of the STOP block (STOP_START through STOP_END) in `text`; None when it is absent."""
    if STOP_START not in text:
        return None
    start = text.index(STOP_START)
    end = text.find(STOP_END, start)
    if end < 0:
        return "unterminated"
    return hashlib.sha256(text[start:end + len(STOP_END)].encode("utf-8")).hexdigest()


for marker_old in (
    "*Held by the STOP at the top of §8 (note 10.1g).*\n\n",
):
    edit("phase markers: held", marker_old, "", count=5, gone=MARKER_GONE)

edit(
    "P0.5a marker",
    "*Items 2 and 4 are held by the STOP at the top of §8; items 1, 5, 6 and 7 are released (note 10.1g).*\n\n",
    "",
    gone=MARKER_GONE,
)

# The paragraph after note 8a. Its first sentence is also where main() places note 8a (TEN_PATHS).
TEN_PATHS_OLD = "**Ten paths are named below; nine are landed and one is not.**"
TEN_PATHS = "**Ten paths are named below, and all ten are landed.**"

edit(
    "section 8: all ten paths are landed (ml#2114 landed the tenth)",
    TEN_PATHS_OLD + " Landed, and byte-identical to their tagged\nblocks here:",
    TEN_PATHS + " Nine are byte-identical to their tagged\nblocks here:",
)

edit(
    "section 8: the tenth, and the three 2026-10-03 files without a tagged block",
    "The\ntenth, `util/install_juniper_backup_timer.bash`, has **no tagged block** in this document and is a **P3\n"
    "deliverable** (§7.3.4, §7.8), not a P0 item — do not look for it here. **P0 step −1 is to review the nine.**",
    "The\ntenth, `util/install_juniper_backup_timer.bash`, has **no tagged block** in this document; it landed with ml#2114 (B6) and is a\n"
    "**P3** item (§7.3.4, §7.8), not a P0 one — do not look for it here. Three files §8 invokes since 2026-10-03 have no tagged block\n"
    "either and are read in the repository: `util/ad-hoc/2026-10-03_password_init_hand_start.bash` (steps 6–8),\n"
    "`util/ad-hoc/2026-10-03_rekey_settings_key.bash` and its gate `util/ad-hoc/2026-10-03_rekey_gate.py` (P0.5b). **P0 step −1 is to\n"
    "review the nine and those three.**",
)

edit(
    "section 8: what is merged",
    "All nine are merged on `main` — ml#1999 landed them, and ml#2029 re-landed the three the 2026-09-22 rulings\nchanged — so nothing is left to merge:",
    "All twelve are merged on `main` — ml#1999 landed the nine, ml#2029 re-landed the three the 2026-09-22 rulings\nchanged, and the "
    "2026-10-03 change (§12) landed the three helpers and re-landed the installer, the unit and the defaults — so nothing is left to merge:",
)

edit(
    "section 8: the phase-order exception for step 9's client change is history",
    "— and step 9's client change, which must land with §7.6's re-pointing before P0 runs, nothing in a later",
    "— and step 9's client change, which landed with ml#2115, nothing in a later",
)

edit(
    "P0 step 0(a): seven blessed paths, flags installed",
    "`--require-db-encryption-key` (D-1), and a `.blessed.sha256` written by the installer (D-6). D-2's rotation is",
    "`--require-db-encryption-key` (D-1) and D-9's two web-service options — all in the installed `/etc/default/duplicati` since the 2026-10-03 change — and a `.blessed.sha256` written by the installer listing its seven files (D-6). D-2's rotation is",
)

edit(
    "P0 step 6: Procedure A2 loses the UI password",
    "`Source` rows in the snapshot are cleartext, so sources survive; `server-passphrase`/`-salt` are **hashes** and not in the wipe list, so the **UI password survives** and \"set the UI password afresh\" is optional, not required.",
    "`Source` rows in the snapshot are cleartext, so sources survive. **The UI password does NOT survive** (corrected 2026-10-03, "
    f"`{ASSESS}` I-37, confirmed in the 2.4.0.0 source): `pbkdf-config` — the only home of the web-UI password since 2.1, because "
    "`UpgradePasswordToKBDF` nulls `server-passphrase` — is in the password-field set the tool clears, so the next start mints a random password, and "
    "with `--webservice-disable-signin-tokens` installed no signin token is accepted either. So in step 8, after the database is placed and the "
    "installer has run but **before** `systemctl start`, run the password-init hand start (`util/ad-hoc/2026-10-03_password_init_hand_start.bash`: "
    f"one server run with `--webservice-password-init` through a 0600 `--parameters-file`, exit 102; `{ASSESS}` §6.4 step 10). That run sets "
    "the password (`pbkdf-config` becomes an `enc-v1:` blob under the new key), upgrades the schema and re-encrypts the password-named "
    "server settings under the settings key; the backups' fields and `encrypted-fields` are unchanged until the unit's first start; and the "
    "whole database is re-encrypted at the unit's first start, which is where to check it. This, not the "
    "restore, is why A0 is the default path and A2 the fallback. The tool also wipes `remote-control-config`.",
)

edit(
    "P0 step 6: wipe-encryption SKIPS a non-server database (the Phase B round, lane A NIT-7)",
    "(delete it — it still holds the encrypted values) and refuses a non-server database.",
    "(delete it — it still holds the encrypted values) and skips a non-server database with exit 0 (`WipeEncryption.cs`), so read its "
    "output, not its status.",
)

edit(
    "P0 step 8: the hand start precedes the first start on A2",
    "property of any API-signed commit, not a one-off to fix: the next one lands the same way. Then\n   `sudo systemctl start duplicati.service`.",
    "property of any API-signed commit, not a one-off to fix: the next one lands the same way. **Before the install, check any existing "
    "`/etc/duplicati/env` — option names only, never values**: since the installer's 1.5.1 judges that file by running the wrapper it is "
    "installing (2.4.0), an `--option` line in it outside the wrapper's eight allow-listed tunables stops the install, and would make every "
    "start exit 78. It must be one of O-12's two forms — `root:duplicati` 0640 (what the installer creates, and what this design "
    "recommends) or `duplicati:duplicati` 0600 (the recorded dissent); the installer accepts either and does **not** settle O-12 "
    "(§11; P1 step 2). Anything else is refused: another owner or group, a group- or other-writable file, an other-readable one (the "
    "file may carry the key), and a symlink, which must be replaced by a regular file. Where a `.blessed.sha256` from an earlier install exists, this install reports **BEHAVIOUR CHANGE** and refuses: "
    "against a host installed from `origin/main`'s installer (wrapper 2.0.0, installer 1.0.0), six of the seven blessed files "
    "differ — all but the guard; against the Phase B branch's own first fold-in, rounds 3 and 4 changed four: the wrapper (2.2.0 to "
    "2.4.0, the env file's allow-list — the one real behaviour change), the snapshot script, the snapshot unit and a comment in "
    "`duplicati.service`. Either way read the differences and re-run it with `--update-backup-behavior`; on a never-blessed host (I-36) an installed file that matches the repository installs quietly, but one that differs — "
    "this host's `/etc/default/duplicati` does — is reported **UNBLESSED** and refused the same way, so re-run with "
    "`--update-backup-behavior`; the installer keeps the old file as `<file>.pre-install-<UTC>` and says where. "
    "**Write the settings key before any start** "
    "— the unit's `LoadCredential=` fails on an absent file — **and never over an existing one**: on **A0, A2 and B** a new random key, "
    "`sudo test ! -e /etc/credstore/duplicati-settings-key && { umask 077; openssl rand -base64 48 | tr -d '\\n' | sudo tee "
    "/etc/credstore/duplicati-settings-key >/dev/null; }` (mode 0600; on a re-run of this step the `test` refuses, because the database may "
    "already be under the key on disk and the escrowed copy would be the only other one); on **Procedure A** the accepted 09-18 key to "
    "`/etc/credstore/duplicati-settings-key` and a random one to `…-key.new`, which P0.5b swaps in. Escrow the new key now and verify it "
    f"by hash (`{ASSESS}` §6.4 step 9). On **A2**, run the password-init hand start now "
    "(step 6; B did in step 7). **Write the web credential before the first start** (the format is step 9's), with the password the "
    "database holds now — on A0 and A the root-era one (if it is not known, §7.3.6's recovery runs here, before the first start), on A2 "
    "and B the hand start's — so that the first start can be checked and B's "
    "rebuild can log in; step 9 rewrites it after the password change. Then\n   `sudo systemctl start duplicati.service`, and "
    "`python3 util/ad-hoc/yamaguchi_server_api.py serverstate` must exit **2** (Paused, the stored `paused-until` above). If it reads "
    "Running, **stop the unit** at once (`sudo systemctl stop duplicati.service`) and record it: on a running server the overdue job may "
    "already be running, and `pause` only suspends it — step 10's `resume` would continue it with the options it started with. Read the "
    "stored `paused-until` before starting again (Phase B round 4, lane B NIT-6). The installer's closing hint prints this "
    "stop-not-pause rule and step 10's restart.",
)

edit(
    "P0 step 8: DBPath is re-pointed in the placed file, with no server running (round-4 B17; the Phase B round)",
    "and `RestConnection.cs`'s `ResolveDbPath` returns a rooted path unchanged — the server never relocates it.",
    "and `ResolveDbPath` (`Duplicati/Library/RestAPI/Database/Connection.cs:766`) returns a rooted path unchanged — the server never relocates it.",
)

edit(
    "P0 step 8: the sqlite3 re-point replaces the UI/PUT one (round-4 B17)",
    "So: stop the server, `cp` `BMXWPAOGLP.sqlite` into the new data folder (`chown duplicati`, `0600`), and update the row — UI "
    "**Database → Placement → Save**, or `PUT /api/v1/backup/<id>` — after which 2.4.0.0 stores it *relative* (`GetRelativeDbPath`).",
    "So, with no server running, `cp` — never `mv`: the original stays in place, and in step 1's freeze, until P4 — "
    "`/usr/lib/duplicati/data/BMXWPAOGLP.sqlite` into the new data folder (`chown duplicati`, `0600`) **together with every "
    "`BMXWPAOGLP.sqlite-wal`, `-journal` or `-shm` beside it**, under the same names — unlike the recovered server database above, whose "
    "file is clean and closed: the index is the sole copy, and whether its last writer closed it cleanly is not known; a `-wal` or a hot "
    "`-journal` holds pages the main file alone lacks, which SQLite applies at the first open (the assessment's Phase C step 6 lists "
    "`/usr/lib/duplicati/data/` and so says whether any exist; copy whatever it shows). On **A0, A and A2** re-point "
    "the row in the placed database as the `duplicati` user — `UPDATE \"Backup\" SET \"DBPath\" = '/home/duplicati/.config/Duplicati/BMXWPAOGLP.sqlite' "
    "WHERE \"ID\" = <id>;` with `sqlite3` (installed in the assessment's Phase C) — and read it back: the UI's **Database → Placement → Save** "
    "and `PUT /api/v1/backup/<id>` need a running server, and none may run before this step is done (round-4 B17). On **B** the job does "
    "not exist until step 7 rebuilds it with the server running, so point it at the copied index there — the UI's Placement page, after "
    "the rebuild (the import ignores a `DBPath` sent with it) — after which 2.4.0.0 stores it *relative* (`GetRelativeDbPath`). "
    "**Then hold the scheduler, on every path, while no server runs** (Phase B round 3, lane B DEFECT-2): in the placed "
    "`Duplicati-server.sqlite`, as `duplicati` and with the same `sqlite3`, first record what is stored — `SELECT \"Name\", \"Value\" "
    "FROM \"Option\" WHERE \"BackupID\" = -2 AND \"Name\" IN ('paused-until', 'startup-delay');` (it says how far the old pause "
    "reached; Phase B round 4, lane B NIT-1) — then `DELETE FROM \"Option\" WHERE \"BackupID\" = -2 AND \"Name\" = "
    "'paused-until'; INSERT INTO \"Option\" (\"BackupID\", \"Filter\", \"Name\", \"Value\") VALUES (-2, '', 'paused-until', '0');` — a stored "
    "`0` is an indefinite pause, which every start restores and only `resume` lifts (`Duplicati/Library/RestAPI/LiveControls.cs`, `Init`) — "
    "then run the same `SELECT` again and record both values. The stored `startup-delay` (30m when last read, on 08-31) is the only other pause there is: without this "
    "row the job, overdue since 09-19, starts when that delay lapses — or at once, if it is unset — before step 10's guard is in place, "
    "and on Procedure A under the 09-18 key. On **A0, A and A2** do it here, with the `DBPath` update; on **B**, after step 7's hand "
    "start and before the first start. **In the same session, clear the server's default retention options**: the `Option` rows at "
    "`BackupID` -1 join every run (`Runner.cs`, `GetCommonOptions`) but never appear in `export`, so step 10's read-back cannot see "
    "them (Phase B round 5, lane B DEFECT-1). `SELECT \"Name\", \"Value\" FROM \"Option\" WHERE \"BackupID\" = -1 AND "
    "lower(ltrim(\"Name\", '-')) IN ('retention-policy', 'keep-time', 'keep-versions');` (any case — Phase B round 6, NIT-1) — record what it returns in the validation record "
    "(the values are retention strings, not secrets) — then delete exactly those rows (`DELETE FROM \"Option\"` with the same "
    "`WHERE`) and run the `SELECT` again: it must return nothing. `keep-time` and `keep-versions` defaults are never restored (step "
    "11); a `retention-policy` default only if the owner wants one. The ruling's home is the job's own `retention-policy`.",
)

edit(
    "P0 step 8: the schema upgrade is A0's only (the Phase B round)",
    "Expect in the journal: schema upgrade 11→12 and\n   `Server has started`.",
    "Expect in the journal `Server has started`, and on **A0** a schema upgrade\n   11→12 — on A2 and B the hand start "
    "already upgraded the database, so this start shows none.",
)

edit(
    "P0 step 9: both clients already read the credential (B2, ml#2115)",
    ", write `~/.config/duplicati-backup/web-credential` (0600), and re-point **both** API clients at it (§7.6). "
    "`util/ad-hoc/yamaguchi_server_api.py:41` hard-codes the primary checkout's `.env`, whose value §6 S-5 records as stale, so a run order "
    "that pauses the\n   scheduler first and creates the credential afterwards makes step 10's `pause` 401 — and `resume` is what fires the "
    "overdue backup. Land the client changes (the credential path **and** the new `pause`/`resume` subcommands) in the same PR as §7.6's "
    "re-pointing, before P0 runs. Redeploy the watchdog with `--backup-id <id>`; confirm the next 12:00 fire reads `OK`.",
    " and rewrite `~/.config/duplicati-backup/web-credential` (0600) with the new password — step 8 wrote it with the old one — the one "
    "file **both** API clients read since B2 (ml#2115; §7.6). Its format is one line, `DUPLICATI_WEB_CREDENTIAL=<password>`; the clients "
    "strip **one** matching pair of outer quotes, so a password whose first and last characters are the same quote character is written "
    "inside one more pair. A run order that pauses the\n   scheduler first and creates the credential afterwards makes step 10's `pause` "
    "fail — and `resume` is what fires the overdue backup. On **A2**, re-enter `TargetURL` and the passphrase now, in the web UI's editor "
    "of the existing job (step 6). Redeploy the watchdog with `util/ad-hoc/yamaguchi_watchdog_deploy.bash --backup-id <id>`; its first "
    "12:00 check is confirmed after step 10, not here.",
)

edit(
    "P0 step 10: the pause/resume verbs exist (B2)",
    "Pause and resume go through `util/ad-hoc/yamaguchi_server_api.py` (extended with `pause`/`resume`), **not** `duplicati-server-util`",
    "Pause and resume go through `util/ad-hoc/yamaguchi_server_api.py`'s `pause`/`resume` verbs (B2; each reads the state back), **not** "
    "`duplicati-server-util`",
)

fence_edit(
    "P0 step 10: the guard dry-run refuses an empty TargetURL (STOP item 3; the Phase B round)",
    "   sudo -u duplicati env \\\n"
    "     DUPLICATI__REMOTEURL=\"$(python3 util/ad-hoc/yamaguchi_server_api.py export <id> \\\n"
    "       | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"Backup\"][\"TargetURL\"])')\" \\\n"
    "     /usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash; echo \"guard exit=$?\"\n",
    "   unset url id\n"
    "   id=<id>\n"
    "   case \"$id\" in ''|*[!0-9]*) echo \"REFUSE: set id to the job's number\" >&2; false ;; esac &&\n"
    "   url=\"$(python3 util/ad-hoc/yamaguchi_server_api.py export \"$id\" \\\n"
    "     | python3 -c 'import json,sys; print(json.load(sys.stdin)[\"Backup\"][\"TargetURL\"])')\"\n"
    "   test -n \"$url\" || { echo \"REFUSE: export $id gave no TargetURL\" >&2; false; } &&\n"
    "   sudo -u duplicati env DUPLICATI__REMOTEURL=\"$url\" \\\n"
    "     /usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash; echo \"guard exit=$?\"\n",
)

edit(
    "P0 step 10: why the test line, and P0.5b's place (the Phase B round)",
    "that §7.5 item 6 says give the guard its value.",
    "that §7.5 item 6 says give the guard its value; and the `test -n` line is not optional either: command substitution ignores a failed "
    "`export`, and an empty `DUPLICATI__REMOTEURL` makes the guard skip its `TargetURL` comparison and pass (the 2026-09-24 STOP's item 3). "
    "Replace `<id>` on the second line only. The first line is there because a line with `<id>` left in it is a syntax error that an "
    "interactive shell discards before running the next one, so without the `unset` a `url` left over from earlier in the session reached "
    "the guard (Phase B round 3, lane B NIT-7); now an unset or non-numeric `id` refuses, and so does the empty `url` it leaves. "
    "**Then, on A0, A2 and B, restart the unit before `resume`**: `sudo systemctl stop duplicati.service`, then `sudo systemctl start "
    "duplicati.service`. The queue lives only in the server's memory (`QueueRunnerService`), so the copy queued at the first start — old "
    "`retention-policy`, old `--tempdir`, no guard — goes with the process; the start restores the stored indefinite pause "
    "(`LiveControls.Init` reads `paused-until` 0, and `Program.cs` `LiveControl_StateChanged` saves it again, line 1308), and that save "
    "reschedules, so the overdue job is queued afresh from the edited database. `serverstate` must exit 2 again. Read the edits back with "
    "`export <id>` — `--tempdir`, `--run-script-before-required` and `--aes-version` as set, and no `retention-policy`, `keep-time` or "
    "`keep-versions` in the job — the server's default options never appear in `export`, which is why step 8 clears them "
    "with `sqlite3` — and only then `resume`. **AC-3 is a manual run whenever the "
    "overdue slot was used up** — by a run `resume` fired before the restart, or by any failed run — because `resume` then fires nothing: "
    "`python3 util/ad-hoc/yamaguchi_server_api.py run <id>`. **On Procedure A, P0.5b runs here** instead of the restart, after these "
    "edits and this dry-run and **in place of** the operator's `resume`: its own two starts drop the stale copy the same way, and its "
    "closing `resume` fires the overdue backup, under the new key. On A0, A2 and B, `resume` after the restart. Then confirm that the watchdog's next 12:00 "
    "check reads `OK` — step 9 asked for it before this step until 2026-10-08, which kept the server waiting up to a day before its "
    "guard was in place.",
)

edit(
    "P0 step 11: AC-6 waits for the first fire after the timer is re-enabled (round-4 B18)",
    "`AC-6` cannot be proved here — it becomes provable only when the snapshot lane is re-pointed (P0.5a item 2), and `AC-1` needs 24 h.",
    "`AC-6` cannot be proved here: step 8's installer re-points the snapshot lane, but AC-6 needs the 13:45 UTC fire and the 14:00 UTC "
    "fileset after the timer is re-enabled (P0.5a item 2) — and `AC-1` needs 24 h.",
)

edit(
    "AC-6: provable the day after P0 (round-4 B18)",
    "| AC-6 | **(A P2 criterion — not provable at the end of P0.)** Snapshot lane reads the new data folder;",
    "| AC-6 | **(Provable the day after P0, not at its end: the 13:45 UTC fire after the timer is re-enabled.)** Snapshot lane reads the new data folder;",
)

edit(
    "AC-10: the first OK needs BOTH sticks; FAILED until the first success (the ml#2114 lane)",
    "a run with no drive reads `SKIPPED`; a run with a drive attached (mounted under the root `util/juniper-backup.bash` is configured for — "
    "`/run/media/pcalnon/` or the fstab paths, §4.5) produces verified archives on every mounted drive;",
    "the first run, with **both** configured drives attached (under the runner's root — `/run/media/pcalnon/` or the fstab paths, §4.5), "
    "reads `OK` with verified archives on both — one drive is PARTIAL (rc 4), `FAILED`; after that first success a run with no drive reads "
    "`SKIPPED`, before it `FAILED`;",
)

edit(
    "P3 step 1: landed (ml#2114)",
    "1. **Fix the runner's mount root first — and install it.**",
    "1. *(Landed 2026-10-03 by ml#2114, the assessment's B6: the runner and the scheduler read one root setting, `JUNIPER_BACKUP_MEDIA_ROOT`, "
    "default `/run/media/$USER`; an absolute entry is accepted only under `/mnt`, `/media` or `/run/media`, and is runner-only — §7.9.)* "
    "**Fix the runner's mount root first — and install it.**",
)

edit(
    "P3 step 2: the OK run first, with BOTH sticks (the ml#2114 lane)",
    "Install; enable; observe one SKIPPED (unplugged) and one OK (plugged) run;",
    "Install; enable; do the **OK run first, with BOTH configured sticks mounted** (`EBC5-F0A3` and `DFF3-2782`) — the runner counts the "
    "configured devices, so a one-stick run is PARTIAL (rc 4) and reads `FAILED` — then one run unplugged, which reads `SKIPPED` only after that "
    "first success (before it, a lane that has never succeeded reads `FAILED`);",
)

edit(
    "P3 step 2: the reporter's title, and what landed (ml#2114)",
    "The reporter itself already takes the unit name as `$1` (`util/duplicati_backup_failure.bash:31`), so no reporter change is needed.",
    "The reporter takes the unit name as `$1`; ml#2114 also titles its notification with it (`Backup FAILED: <unit>`), where it named the "
    "duplicati lane before.",
)

edit(
    "P3 step 2: the installer and the failure unit landed (ml#2114)",
    "The scheduler and the three user units landed with ml#1999; the installer and `juniper-backup-failure.service` have not.",
    "The scheduler and the three user units landed with ml#1999; the installer and `juniper-backup-failure.service` with ml#2114.",
)

edit(
    "P0.5a item 1: 96 directories, not 97 (the Phase B round)",
    "Expect 97 directories to change owner and 21 (the `runtimes/` subtree and ten `licenses/<package>/`",
    "Expect 96 directories to change owner (95 below the top and the top itself; this said 97 until 2026-10-04, counting `data/` and its "
    "subdirectory, which the command excludes) and 21 (the `runtimes/` subtree and ten `licenses/<package>/`",
)

edit(
    "Appendix B: the env contract's block is etc/duplicati/env (D13)",
    "| `home/duplicati/.config/Duplicati/.env` | `.env` contract | `KEY=VALUE` / `--option` grammar (keyed on the basename `.env`) |",
    "| `etc/duplicati/env` | env contract (`util/systemd/duplicati-env.contract`) | `KEY=VALUE` / `--option` grammar (keyed on the directory "
    "`etc/duplicati/`) |",
)

edit(
    "P0 step 7: Procedure B needs the password-init hand start",
    "7. **Procedure B — rebuild the job through the API.** Start the empty server with the §7.3 unit and a **new** settings key, in a data folder created `0700 duplicati:duplicati` (the one moved aside in step 2 is 0777 and 2.4.0.0 refuses it); set the UI password through the web UI;",
    "7. **Procedure B — rebuild the job through the API.** These run inside step 8, in this order: after its installer **and its key write** "
    "(the hand start refuses a missing key file), create the data folder `0700 duplicati:duplicati` (the one moved aside in step 2 is 0777 and "
    "2.4.0.0 refuses it); run the password-init hand start against it (`util/ad-hoc/2026-10-03_password_init_hand_start.bash`, exit 102 — the "
    "empty database's password is autogenerated, and the installed signin-token flag accepts no token); store `paused-until` and write the web "
    "credential as step 8 says; then start the unit with the **new** settings key, confirm it reads Paused, and log in with that password;",
)

edit(
    "P0.5a item 2: the lane as installed",
    "2. **Install the snapshot timer's script as a root-owned copy** under `/usr/local/lib/duplicati/` and add `ProtectSystem=strict` to `yamaguchi-server-db-snapshot.service`. It runs as **root** today with `ExecStart` naming the primary checkout, so `sys.path[0]` is pcalnon-writable and every branch switch changes what root executes at 13:45 UTC (§7.7). In the **same installed copy**, re-point `SRC` to\n"
    "   `/home/duplicati/.config/Duplicati/Duplicati-server.sqlite`, and **stop the timer** (`systemctl stop yamaguchi-server-db-snapshot.timer`) until P0 step 8 has placed the recovered database; restart it only then.",
    "2. **The snapshot lane is installed by `util/install_duplicati_service.bash` at P0 step 8** — the script as a root-owned copy under "
    "`/usr/local/lib/duplicati/`, the unit with `ProtectSystem=strict` **and** `ReadWritePaths=` on its output directory, reading the new data "
    "folder (§7.7; all three blessed). It runs as **root** today with `ExecStart` naming the primary checkout, so `sys.path[0]` is pcalnon-writable "
    "and every branch switch changes what root executes at 13:45 UTC. What this item does **before** P0 is "
    "`systemctl disable --now yamaguchi-server-db-snapshot.timer` (not `stop`: `Persistent=true` re-fires after a reboot), and the timer is "
    "`enable --now` only after the first start has re-encrypted the placed database (on Procedure A, after P0.5b) and a copy has been checked "
    f"— `{ASSESS}` §6.4 step 13.",
)

edit(
    "P0.5a item 4: journal-only since the syslog copy rotated",
    "4. **Scrub both log stores** — `/var/log/syslog*` *and* the journal, in that order (§6, D-8) — and verify with `sudo ls -la /var/log/syslog-2026092*`. A journal-only scrub leaves an identical copy behind.",
    f"4. **Scrub the journal** (§6, D-8). *(Both stores were named here until 2026-10-03; `logrotate` pruned the `/var/log/syslog*` copy of the 09-20 echoes around 10-01 — `rotate 10`, daily — so a count-only `zgrep` over every `syslog*` file now reads 0 and the journal, 264 lines, is the one copy left: `{ASSESS}` note 3c.)*",
)

edit(
    "P0.5b heading",
    "### P0.5b — immediately after P0 step 8, same session",
    "### P0.5b — Procedure A only: inside P0 step 10, in place of the operator's `resume`",
)

edit(
    "P0.5b body",
    """**Item 3 (the re-key) only.** It runs the server against the **recovered** data folder, so it cannot precede
the recovery: stop the snapshot timer, do the two-start re-key back to back, then
`PRAGMA wal_checkpoint(TRUNCATE); VACUUM;` with the server stopped, then restart the timer (§7.3.5). This is""",
    f"""**Item 3 (the re-key) only, and only on Procedure A.** On A0, A2 and B the placed database was never under a
compromised key in the new folder, and the first start with the new credential encrypts it — nothing to re-key
(`{ASSESS}` §6.4 step 10, O-7). On Procedure A the recovered folder arrives under the accepted 09-18 key: run
`util/ad-hoc/2026-10-03_rekey_settings_key.bash` inside step 10, after its edits and its guard dry-run, **in
place of** the operator's `resume`. It refuses while a task is active, and unless the snapshot timer is neither
enabled (in any form, `enabled-runtime` and `linked` included) nor active. Before the first stop it counts, on a
copy of the database, the `enc-v1:` blobs the product's re-encryption never rewrites: any in `ConnectionString`,
and any in an `Option`, `Source` or `BackupTargetUrl` row whose BackupID names no backup. `Option` and `Source`
have no foreign key (`Schema.sql:44-45, 72-73`), so a deleted job's rows can outlive it. The settings rows at -1
and -2 are rewritten (`Connection.cs:145`; `ServerSettings.cs:851-855` → `SetSettings(-2)`), and so are a live
backup's rows. It refuses if there is one, or if the count itself fails, because such a blob would stay under the
old key and fail the exit gate only after the key swap (Phase B round 3, lanes A and C; round 4, lane C DEFECT-2). Remedy, the owner's:
saved connection strings are deleted through the web UI and re-created after the re-key; an orphaned row, which
the UI cannot reach, is deleted with sqlite3 while the unit is stopped (it comes up Paused again), a copy of the
database first kept in a root-only 0700 directory outside `/home/pcalnon` and shredded (`shred -u`) once the exit
gate has passed — on Procedure A that copy holds blobs under the compromised 09-18 key. It then pauses the scheduler, does the two starts with a
runtime drop-in that it removes with `rm` and `daemon-reload` (never `systemctl revert` — note 8a), swaps the
keys by a copy and one atomic `mv`, gates on a copy (all five encrypted columns), runs
`PRAGMA wal_checkpoint(TRUNCATE); VACUUM;` with the server stopped, and resumes — that `resume` fires the overdue
backup, now under the new key (§7.3.5). Its EXIT trap stops the unit while a drop-in is present, removes the
drop-in, names each key file by hash (swapped / not swapped / unexpected), reports the database as UNKNOWN once a
decrypt or encrypt start was attempted without its "Server has started" line, prints the gate's counts on a gate
failure, and prints only the recovery that applies — never "start the unit" after a FragmentPath refusal; a
refusal before the pause says nothing changed (Phase B round 3). It needs step 9's credential, because its pause
goes through the API. This is""",
)

edit(
    "P1 step 1: the procedure of record is the script",
    "1. *(Executed in P0.5b — kept here as the procedure of record.)* Generate a new settings key (`umask 077; openssl rand -base64 48 | tr -d '\\n' > /etc/credstore/duplicati-settings-key`), then re-key the database in two starts: first with the **old** key still in the credential file and `--disable-db-encryption` appended to `DAEMON_OPTS` (every field is decrypted on that start), then with the new key in the credential file and the flag removed (every field is",
    "1. *(Procedure A only; executed in P0.5b by `util/ad-hoc/2026-10-03_rekey_settings_key.bash` — kept here as the procedure of record.)* Generate the "
    "new settings key into `/etc/credstore/duplicati-settings-key.new` (`umask 077; openssl rand -base64 48 | tr -d '\\n'`), then re-key the database in "
    "two starts: first with the **old** key still at `…/duplicati-settings-key` and `--disable-db-encryption` delivered by a runtime drop-in under "
    "`/run/systemd/system/` — never in `DAEMON_OPTS`, where it would satisfy `--require-db-encryption-key` and decrypt the database silently on every "
    "later start — (every field is decrypted on that start), then, after the new key is copied into place with one atomic `mv` and the drop-in is "
    "removed (`rm` and `daemon-reload` — never `systemctl revert`, which would delete the installed unit, note 8a), with the "
    "new key (every field is",
)

edit(
    "P1 step 2: the contract file is /etc/duplicati/env",
    "2. Delete the five commented lines from `.env`; set it to the §7.3.5 contract. **Mode: `0640 root:duplicati` as recommended, or `0600 duplicati:duplicati` — this is the open dissent recorded in §11**; install the stricter form until the owner rules.",
    "2. The contract file is `/etc/duplicati/env`, installed by P0 step 8's installer from `util/systemd/duplicati-env.contract` (§7.3.5, D13 closed): confirm it carries no key line and no commented assignment, and `shred -u` the old `.env` in the moved-aside folder `Duplicati.empty-2026-09-20/` (P0 step 9 of the assessment does this; it held both keys and the five commented secrets). **Mode: `0640 "
    "root:duplicati` as installed, or `0600 duplicati:duplicati` — the open dissent recorded in §11 (O-12 of the assessment)**.",
)

edit(
    "section 10.2: the next action",
    "**the next action in this arc is the follow-up change that clears the STOP block at the top of §8, then §8's\nP0 recovery — not anything in §10.2**.",
    f"**the next action in this arc is §8's P0 recovery, in the order `{ASSESS}` §6.3–6.4 gives — not anything in §10.2**.",
)

# --------------------------------------------------------------------------------------------
# Sections 11 and 12
# --------------------------------------------------------------------------------------------

edit(
    "section 11: state line",
    "**State of the record: rounds 1 and 2 delivered and fully reconciled; round 3's D13 open (note 12a); rounds 4–8 (2026-09-24) open —",
    "**State of the record (2026-10-03): rounds 1 and 2 delivered and fully reconciled; round 3's D13 closed; rounds 4–8's §8 defects closed by the artifacts (note 8a), their residue listed there; the 2026-10-03 assessment's own round 1 (three lanes) is in that document's §8. Until 2026-10-03 this line read: round 3's D13 open (note 12a); rounds 4–8 (2026-09-24) open —",
)

edit(
    "section 12: the clearing row",
    "`util/ad-hoc/2026-09-24_archive_round4_reports.py`. |\n\nNotes on the rows above:",
    "`util/ad-hoc/2026-09-24_archive_round4_reports.py`. |\n"
    f"| 2026-10-03 | **The STOP cleared; its five defects fixed in the artifacts** — Phase B of `{ASSESS}` (note 8a), with its validation "
    "round folded in. **Changed**: this file, the assessment, seven service-lane files and two design scripts (note 12c names each). **Added**: "
    "the env contract, the re-key script and its gate, the password-init helper, a test suite, the round record and this change's edit script "
    "(note 12c). |\n"
    "| 2026-10-08 | **Phase B rounds 3 and 4 folded in**: the retention ruling (P0 steps 10–11), the stored pause and the restart "
    "that re-queues the edited job (steps 8, 10), B's rebuild and Verify, §7.3.6, the env allow-list, the re-key's pre-flight and trap. "
    "**Changed**/**Added**: note 12c; dispositions in the assessment's §8. |\n"
    "\nNotes on the rows above:",
)

edit(
    "P0.5b: runnable only inside step 10",
    "but it is also not runnable before step 8.",
    "but it is also not runnable before step 10.",
)

edit(
    "section 12: note 12a -- D13 closed",
    "changes landed artifacts,\n  and is open.",
    "changes landed artifacts,\n  and was open until 2026-10-03 (note 12c).",
)

edit(
    "section 12: note 12b -- the PR that landed the 2026-09-24 (later) row",
    "- **(12b)** What the 2026-09-24 (later) row changed.",
    "- **(12b)** What the 2026-09-24 (later) row — ml#2113 (`c01c837e`), landed 2026-10-03 — changed.",
)

edit(
    "section 12: note 12c -- the 2026-10-03 row's files",
    "which holds all five rounds.\n\n---",
    "which holds all five rounds.\n"
    "- **(12c)** The 2026-10-03 row's files — Phase B of the assessment, its §6.2 rows B1, B3, B4, B5, B7, B8 and B10 (B2\n"
    f"  and B6 landed on their own: ml#2115 with its fix-forward {FIXFWD}, and ml#2114). **Changed**: this file; the\n"
    "  assessment (its Phase B rows and round record); `util/systemd/duplicati.default` (D-1 and D-9's options in\n"
    "  `DAEMON_OPTS`); `util/systemd/duplicati.service` (`InaccessiblePaths=` on both escrow copies);\n"
    "  `scripts/duplicati-wrapper.bash` (2.2.0: `/etc/duplicati/env` is the default, and the env file can carry neither a\n"
    "  security option nor a `DUPLICATI__*` export); `util/install_duplicati_service.bash` (1.2.0: seven files under the\n"
    "  gate, `--dry-run`, the first-install fix, `/etc/duplicati/env` installed if absent, a wider secret gate, drift\n"
    "  copied aside); `util/systemd/yamaguchi-server-db-snapshot.service` (the installed copy under\n"
    "  `ProtectSystem=strict` with `ReadWritePaths=`); `util/systemd/yamaguchi-server-db-snapshot.timer` (its\n"
    "  `Documentation=` names the installed copy); `util/ad-hoc/yamaguchi_server_db_snapshot.py` (1.1.0: the new `SRC`);\n"
    "  `util/ad-hoc/2026-09-22_stage_design_artifacts.py` (`--from-repo`); `util/ad-hoc/2026-09-21_lint_design_snippets.py`\n"
    "  (the env grammar for `etc/duplicati/`). **Added**: `util/systemd/duplicati-env.contract`,\n"
    "  `util/ad-hoc/2026-10-03_rekey_settings_key.bash` and its gate `util/ad-hoc/2026-10-03_rekey_gate.py`,\n"
    "  `util/ad-hoc/2026-10-03_password_init_hand_start.bash`, `tests/test_duplicati_wrapper_contract.py` (wired into\n"
    f"  `ci.yml` and `docs/REFERENCE.md`), `{RECORD}` (the round's reports, verbatim) and\n"
    "  `util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py`, this edit set. The fold-in of rounds 3 and 4\n"
    "  (2026-10-08, the 2026-10-08 row) changed this file, the assessment, `scripts/duplicati-wrapper.bash` (2.4.0),\n"
    "  `util/install_duplicati_service.bash` (1.5.1), `util/systemd/duplicati-env.contract`, the comments of\n"
    "  `util/systemd/duplicati.service` and `util/systemd/yamaguchi-server-db-snapshot.service`,\n"
    "  `util/ad-hoc/yamaguchi_server_db_snapshot.py` (1.2.0), the re-key (1.3.0), its gate (1.2.0), the hand start (1.3.0),\n"
    "  the two A0 scripts (`2026-09-22_confirm_a0_premise.bash`, `2026-09-22_restore_server_db_from_fileset.bash`),\n"
    "  `tests/test_duplicati_wrapper_contract.py` and this edit set; it added three suites —\n"
    "  `tests/test_clear_stop_backup_design.py`, `tests/test_duplicati_installer_real_path.py` and\n"
    "  `tests/test_backup_rekey_real_path.py` — the fixture `tests/fixtures/duplicati_2.4.0.0_server_options.txt` and the\n"
    "  evidence scripts under\n"
    f"  `util/ad-hoc/2026-10-08_backup-phase-b-fold-in/`; `{ASSESS}` §8 records each finding.\n\n---",
)

# --------------------------------------------------------------------------------------------
# Round 3 on the fold-in (2026-10-08): R3B DEFECT-1..4 under the owner's ruling, and the cheap NITs
# --------------------------------------------------------------------------------------------

edit(
    "front matter: the second exception -- the job's own retention, restored after AC-4 (R3B DEFECT-1; owner ruling 2026-10-08)",
    "  - Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved except the in-tree escrow `…/Dropbox/Backups/_yamaguchi_keys/`, which only "
    "P1 step 4 deletes, once P0.5a item 5 or P1 step 4 has copied it out.",
    "  - Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved except (1) the in-tree escrow `…/Dropbox/Backups/_yamaguchi_keys/`, which "
    "only P1 step 4 deletes, once P0.5a item 5 or P1 step 4 has copied it out, and (2) the old filesets the job's own retention pass deletes "
    f"once P0 step 11 restores `retention-policy` — as `{NEW_RETENTION}`, after AC-4's first drill has passed, and after the five dlists it will delete are copied out of the Dropbox root; P0 step 10 "
    "removes it and restarts the unit, so the first backup after the recovery runs from the edited job and deletes nothing (owner "
    "ruling 2026-10-08); and (3), on Procedure B only and only if Verify finds the index inconsistent, the remote files a Repair "
    "deletes — volumes the index does not know, the index's own temporary, deleting or incompletely uploaded files, and empty or "
    "replaced index files — which P0 "
    "step 8 first copies aside after a dry run.",
)

edit(
    "section 8 preamble: two exceptions (R3B DEFECT-1)",
    "**Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved by\nany step below, with exactly one exception, and it needs owner "
    "sign-off**: the passphrase escrow copy at",
    "**Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved by\nany step below, with two exceptions and one conditional third.** The "
    "third applies only if Procedure B's Verify finds the index inconsistent: a Repair deletes remote files — volumes the index does not know (`RepairHandler.cs:299`, `:397`), files the index itself holds as temporary, deleting or incompletely uploaded (`FilelistProcessor.cs`, `VerifyAndClean`, `:384-400`, `:469-480`), and empty or replaced index files (`RepairHandler.cs:599-609`, `:1050-1053`) — "
    "so step 8 runs it as a dry run first and copies every file it would delete aside (Phase B rounds 5 and 6). The first is the job's "
    "own retention pass: step 10 removes `retention-policy` and restarts the unit, so the first backup runs from the edited job and "
    f"deletes nothing, and step 11 restores it, as `{NEW_RETENTION}`, only after AC-4's first drill has passed — its first pass then "
    "deletes five of the nine pre-recovery filesets, which step 11 first copies to a root-only directory outside the Dropbox root, and "
    "the deletions reach Dropbox (step 11; owner ruling 2026-10-08). Until 2026-10-08 this paragraph named only the second, and the "
    "first backup's pass under the old policy would have deleted six to eight of the nine, AC-4's drill target among them (Phase B "
    "round 3, lane B DEFECT-1). The second needs owner sign-off: the passphrase escrow copy at",
)

edit(
    "P1 step 4: no longer the single exception (R3B DEFECT-1)",
    "(this is the single exception to the \"nothing under `/mnt/Backups/Ubuntu/` is moved\" rule; the preamble names it)",
    "(this is the one exception to the \"nothing under `/mnt/Backups/Ubuntu/` is moved\" rule that needs owner sign-off; the preamble "
    "names it and the others: the job's own retention pass after P0 step 11, and on Procedure B the remote files a Repair deletes, copied aside first)",
)

edit(
    "section 10.2 hazard 1: section 8's rule has two exceptions (R3B DEFECT-1)",
    "   under `/mnt/Backups/Ubuntu/` is deleted or moved.\n2. **The local database",
    "   under `/mnt/Backups/Ubuntu/` is deleted or moved beyond the exceptions its preamble names.\n2. **The local database",
)

edit(
    "section 7.5: retention suspended, then the new policy (owner ruling 2026-10-08)",
    f"`--no-auto-compact=true`, `retention-policy={OLD_RETENTION}`, `--asynchronous-upload-limit=1`,",
    f"`--no-auto-compact=true`, `retention-policy` (removed by P0 step 10 and restored by step 11, after AC-4's first drill, as "
    f"`{NEW_RETENTION}` — replacing the snapshot's `{OLD_RETENTION}`; owner ruling 2026-10-08), `--asynchronous-upload-limit=1`,",
)

edit(
    "section 7.3.6: the unknown-password recovery deletes pbkdf-config; A2 is not in it (R3B DEFECT-4)",
    "case: Procedures A0, A and A2 all recover a database whose `server-passphrase`/`-salt` hashes survive\n"
    "(`wipe-encryption` does not clear them, §8 step 6), so the server does **not** consider the password\n"
    "autogenerated, `--webservice-password-init` refuses it with exit 103, and the argv routes are banned. The\n"
    "recovery is to clear the stored hash **on the copy, before step 8 installs it**, so the server treats it as\n"
    "autogenerated again: with the server stopped,\n"
    "`DELETE FROM Option WHERE BackupID=-2 AND Name IN ('server-passphrase','server-passphrase-salt','server-passphrase-trayicon','server-passphrase-trayicon-hash');`\n"
    "then `--webservice-password-init` on a single hand start. Without this, P0 step 9 is unreachable for three of\n"
    "the four procedures, and step 10, AC-2, AC-5, AC-9 and AC-13 all sit behind it.",
    "case: Procedures A0 and A recover a database whose password is real, so the server does **not** consider it\n"
    "autogenerated, `--webservice-password-init` refuses it with exit 103, and the argv routes are banned. Since 2.1\n"
    "the password lives in `pbkdf-config` (`UpgradePasswordToKBDF` nulls `server-passphrase`), and that function\n"
    "returns at once while `pbkdf-config` is set — so the recovery must delete **`pbkdf-config` too**, or it changes\n"
    "nothing. On the placed database, with no server running, as `duplicati`:\n"
    "`DELETE FROM Option WHERE BackupID=-2 AND Name IN ('pbkdf-config','server-passphrase','server-passphrase-salt','server-passphrase-trayicon','server-passphrase-trayicon-hash');`\n"
    "The next start then mints a random password and marks it autogenerated, so the password-init hand start\n"
    "(`util/ad-hoc/2026-10-03_password_init_hand_start.bash`, run before the unit's first start, as on A2) returns\n"
    "102. Until 2026-10-08 this paragraph deleted only the `server-passphrase` rows, which ends in exit 103 and an\n"
    "unreachable server (Phase B round 3, lane B DEFECT-4), and it named A2, whose `wipe-encryption` already empties\n"
    "`pbkdf-config` (§8 step 6) — A2 always takes the hand start and never needs this. Without it, P0 step 9 is\n"
    "unreachable on A0 and A whenever the password is lost, and step 10, AC-2, AC-5, AC-9 and AC-13 all sit behind it.",
)

edit(
    "P0 step 6: A2 re-enters its values after step 9's login, in the UI (R3B NIT-5)",
    "   Re-enter the two values that matter — `TargetURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi` and the passphrase — through "
    "the **web UI** or `util/ad-hoc/yamaguchi_build_job.py`, which reads the passphrase in-process; never a `curl -X PUT` that puts the "
    "passphrase on argv. Then step 8.",
    "   Then step 8. The two values that matter — `TargetURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi` and the passphrase — are "
    "re-entered **after step 9's login**, in the **web UI**'s editor of the existing job (no server runs before step 8, so not here), and "
    "before step 10's dry-run reads the `TargetURL`. Not `util/ad-hoc/yamaguchi_build_job.py`, which POSTs a *new* job (it refuses an "
    "existing name, and with `--allow-duplicate` would create a second job on the same destination), and never a `curl -X PUT` that puts "
    "the passphrase on argv.",
)

edit(
    "P0 step 7: the rebuild tool runs only paused, with a future schedule and every stale default changed (R3B DEFECT-3)",
    "(`util/ad-hoc/yamaguchi_build_job.py` built the job the first time and reads the passphrase in-process; update its defaults before use).",
    "(`util/ad-hoc/yamaguchi_build_job.py` built the job the first time and reads the passphrase in-process). **That tool is a 2026-08-25 "
    "template, not runnable as it stands** (Phase B round 3, lane B DEFECT-3): it POSTs a job whose schedule `Time` is already past, and "
    "any change to the job list reschedules, so on a running server the job starts at the POST — before its index is re-pointed, before "
    "**Verify files**, before the guard. So: the server reads Paused before the POST (step 8's `paused-until`; `serverstate` exits 2) and "
    "stays paused until step 10's `resume`; the web credential exists first (its `login()` reads it; step 8 writes it); and in a scratch "
    "copy of the tool, never committed, every default the rebuild needs is changed — `Schedule.Time` to the next 14:00 UTC still in the "
    "future (`Repeat` `1D`); `encryption-module` `aes` (the 877 volumes are `.zip.aes`), `--gpg-encryption-switches` dropped and "
    "`--aes-version` pinned (§7.5); `Sources` the snapshot's two; `Filters` the snapshot's 45, not the runner's parse; `retention-policy` "
    "removed (step 10; step 11 restores it); `--tempdir=/home/duplicati/.cache/duplicati-tmp`; the remaining options from §7.5's list — "
    "and its command line names `--target /mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi` and a `--record-dir` outside the Source (the "
    "default is a retired `/media/pcalnon/` path). The import ignores a `DBPath` sent with it: the new job gets a fresh index name, so "
    "re-point it at the copied index afterwards (step 8).",
)

edit(
    "P0 step 10: the stored pause holds the overdue job (R3B DEFECT-2)",
    "so it will start on its own once the startup pause lapses. Immediately after the server is up:",
    "so on a running server it would start on its own. Step 8's stored `paused-until` keeps it from running, but **not from being "
    "queued**: the first start's own pause bookkeeping reschedules, and the scheduler queues the overdue job as a copy of it taken then — "
    "before any of this step's edits, which a queued task never sees (`Scheduler.cs`: `GetBackup(id)` at queue time, and a job already "
    "queued is not queued again; Phase B round 4, lane B DEFECT-1). That is why this step ends with a restart. Before anything is changed:",
)

edit(
    "P0 step 10: the edits remove retention-policy; the credential exists since step 8 (R3B DEFECT-1, DEFECT-2)",
    "add `--run-script-before-required` (§7.5), then `resume` and **sample `serverstate` again** (the credential this needs was created in "
    "step 9).",
    f"add `--run-script-before-required` (§7.5), **pin `--aes-version`** (§7.5; `{ASSESS}` O-14 recommends 2) and **remove "
    "`retention-policy`** — and any `keep-time` or `keep-versions` — from the job's options (only the legacy UI's **Keep all backups** "
    "removes all three) — "
    "the owner's 2026-10-08 ruling suspends retention until AC-4's first drill has passed (step 11): left in place, the first backup's "
    "retention pass would delete six to eight of the nine pre-recovery filesets, the 2026-09-18 one AC-4 drills among them, and the "
    "deletions reach Dropbox (Phase B round 3, lane B DEFECT-1) — then the guard dry-run and the restart below, then `resume`, and "
    "**sample `serverstate` again** (the credential this needs exists since step 8).",
)

edit(
    "P0 step 11: retention restored after AC-4's first drill, as the new policy, and what its first pass deletes (owner ruling 2026-10-08)",
    "then `AC-12` and `AC-13`. `AC-6` cannot be proved here:",
    "then `AC-12` and `AC-13`. "
    f"**Restore `retention-policy` only after AC-4's first drill has passed**, and as the new policy `{NEW_RETENTION}` (owner ruling "
    f"2026-10-08; it replaces `{OLD_RETENTION}`, which step 10 removed) — the web UI's retention setting, custom — and record the date "
    "and the string in the validation record. Of the server-wide defaults step 8 deleted, **`keep-time` and `keep-versions` are never "
    "restored**: the removers combine — `DeleteHandler.cs:82-87` takes the union of `KeepTimeRemover` and `RetentionPolicyRemover`, "
    "then applies `KeepVersionsRemover` to what is left — so either default would delete beyond the table below and the aside list, "
    "and could take some of the four filesets it keeps, the sole copy (Phase B round 6, DEFECT-3). A `retention-policy` default may "
    "come back only if the owner wants one, and only after the table and the aside copy are recomputed against it "
    f"(`{RETENTION_TOOL} --policy …`). The owner's ruling — the job's own `{NEW_RETENTION}` — is unchanged. Its first pass runs at the end of the next backup. For a first pass on any date from "
    "2026-10-08 to 2027-02-27 it **keeps four** of the nine pre-recovery filesets — `20260825T102739Z`, `20260901T140000Z`, "
    "`20260908T140000Z` and `20260915T204850Z` — and **deletes five**: `20260912T140000Z`, `20260915T085649Z`, `20260916T183346Z`, "
    "`20260917T221344Z` and `20260918T140000Z`, the fileset AC-4's first drill restored and Procedure A0's source; from 2027-02-28 it "
    "deletes more. Post-recovery filesets are thinned too: within two weeks to one a day — a fileset less than 24 h after the last one "
    "kept is deleted, so an off-schedule run such as a manual AC-3 at 15:20 UTC costs the next day's 14:00 fileset — and to one a week "
    "after that. **Before restoring it, copy the five dlists it will delete** (`duplicati-<timestamp>.dlist.zip.aes`, the timestamps "
    "above, or the port's for a later date) to a root-only directory outside the Dropbox root — `sudo install -d -m 0700 -o root -g root "
    "/mnt/Backups/Ubuntu/_yamaguchi_retention_aside`, `sudo cp -p` each, and compare `sha256sum` on both sides — so this destructive step "
    "too is preceded by a copy; `--no-auto-compact=true` keeps every dblock and dindex those dlists reference, so the copies keep the "
    "five filesets recoverable (Phase B round 4, lane B NIT-5). Only dlists go, and **the deletions reach Dropbox**, which keeps a "
    "deleted file 30 or 180 days by plan (§10.2 step 8). The figures are a port of 2.4.0.0's retention remover (`DeleteHandler.cs`, "
    f"`RetentionPolicyRemover`), `{RETENTION_TOOL}`. `AC-6` cannot be proved here:",
)

edit(
    "P2 step 4: the watchdog redeploy names the job id (R3B NIT-4)",
    "4. Watchdog changes (§7.6); redeploy with `util/ad-hoc/yamaguchi_watchdog_deploy.bash`.",
    "4. Watchdog changes (§7.6); redeploy with `util/ad-hoc/yamaguchi_watchdog_deploy.bash --backup-id <id>` (without the id the script "
    "refuses, exit 2, before it changes anything).",
)

edit(
    "P0.5a item 2: AC-6 is not a P2 criterion (round-4 B18; R3A NIT-7)",
    "silently destroys Procedure A0's own source for any later re-run and makes AC-6 unprovable until P2.",
    "silently destroys Procedure A0's own source for any later re-run and makes AC-6 unprovable.",
)

edit(
    "P2 step 3: AC-6 is provable the day after P0 (round-4 B18; R3A NIT-7)",
    "**AC-6 is a P2 criterion**, not a P0 one, for exactly this reason.",
    "AC-6 itself is provable the day after P0, at the first 13:45 UTC fire after the timer is re-enabled (round-4 B18); this step "
    "re-confirms it once P2's changes are in.",
)

edit(
    "note 12b: P0.5b has moved since (R3A NIT-7)",
    "  P0.5b between steps 8 and 9, not after step 11),",
    "  P0.5b between steps 8 and 9, not after step 11 — since moved inside step 10, note 8a),",
)

edit(
    "section 7.8: FAILED until the first success; the first OK needs both drives (the ml#2114 lane; R3A NIT-6)",
    "failure (so `OnFailure=` fires) only when no run has succeeded within `STALE_DAYS`.",
    "failure (so `OnFailure=` fires) only when no run has succeeded within `STALE_DAYS` — or at all: before the lane's first success a "
    "skip reads `FAILED` (ml#2114), and the first `OK` needs **both** configured drives mounted (AC-10).",
)

edit(
    "Appendix C: item 4 is applied (R3A D-2)",
    "**None of items 1–10 has been applied to its target document.** That is tracked work, not a closed correction: item 1's targets are "
    "YAM §8.20.4 and `HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §1.8; item 4's are "
    "`util/ad-hoc/yamaguchi_server_db_snapshot.py:20,36` and `util/systemd/yamaguchi-server-db-snapshot.service:5`; item 5's is the "
    "destination README.",
    "**Of items 1–10, only item 4 has been applied to its target**, by the 2026-10-03 change (note 12c): the snapshot script's docstring "
    "and the snapshot unit's comment now state the condition (encrypted under the settings key since 2026-09-18, cleartext before). The "
    "rest is tracked work, not a closed correction, and §8's residue carries it: item 1's targets are YAM §8.20.4 and "
    "`HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §1.8; item 5's is the destination README.",
)

# --------------------------------------------------------------------------------------------
# Round 4 on the fold-in (2026-10-08): R4B DEFECT-1/2 and NITs, R4A N-2/3/5, R4C NIT-1/2/4
# --------------------------------------------------------------------------------------------

edit(
    "P0 step 8 heading: the index is copied, not moved (R4B NIT-12)",
    "8. **Common to A0, A, A2 and B — place the database, move the index, re-point `DBPath`, all BEFORE the first run.**",
    "8. **Common to A0, A, A2 and B — place the database, copy the index, re-point `DBPath`, all BEFORE the first run.**",
)

edit(
    "P0 step 8: B's Verify runs only at resume (R4B DEFECT-2)",
    "For Procedure B, run **Verify files** before any backup; if verification reports the index inconsistent with the destination, run "
    "Repair (this index *is* the destination's own, last written 09-18, so rule 11 does not apply) or, last resort, Recreate.",
    "For Procedure B, **Verify files** must pass before the first backup — and it cannot run while the server is paused: a verify, like "
    "a Repair, is a task appended to the same queue, held until `resume` (`BackupPost.cs`; `QueueRunnerService`; Phase B round 4, lane B "
    "DEFECT-2). So on B, step 10's `resume` runs Verify alone: after step 10's restart, confirm that `serverstate`'s `SchedulerQueueIds` "
    "holds no backup (the rebuilt job's `Schedule.Time` is in the future; keep the session clear of 14:00 UTC, or a scheduled run is "
    "queued ahead of Verify). If it already holds one, a restart alone re-queues it — the job stays overdue until a run completes — so "
    "move the job's schedule `Time` to the next day's 14:00 UTC, restart again, and confirm the queue is empty (Phase B round 5, lane B "
    "NIT-4). Then queue **Verify files**, `resume`, wait for it to finish, `pause`, and read its result. If it reports the index "
    "inconsistent with the destination, Repair it the same way (this index *is* the destination's own, last written 09-18, so rule 11 "
    "does not apply) — but **a Repair deletes remote files**: volumes the index does not know (`RepairHandler.cs:299`, `:397`), files the index itself holds as temporary, deleting or incompletely uploaded (`FilelistProcessor.cs`, `VerifyAndClean`, `:384-400`, `:469-480`), and empty or replaced index files (`RepairHandler.cs:599-609`, `:1050-1053`); the 09-18 dlist, AC-4's drill target, can be among them. "
    "The queued Repair takes no `--dry-run` of its own (`RepairInputDto` carries only `only_paths`, `time`, `version`, `paths` and "
    "`refresh_lock_info`; `BackupPost.cs` `DoRepair`), and its dry-run lines never reach the job's stored result, which keeps only "
    "errors, warnings and information (`ResultClasses.cs:437-447`; `Log.cs:246-248` logs them at `DryRun`). So, in this order "
    "(Phase B rounds 5 and 6, DEFECT-2 and DEFECT-1): (1) add three options to the job — `--dry-run`, "
    "`--log-file=/home/duplicati/repair-dryrun.log` and `--log-file-log-level=DryRun`; the log must sit under the unit's "
    "`ReadWritePaths=`, and `/home/duplicati` is the one writable path the operator can read, besides the destination, where a stray file "
    "would trip the guard; (2) queue Repair, `resume`, wait for it to finish, `pause`; (3) read every line of that log matching "
    "`Would(Delete|DeleteRemote|DeleteEmptyIndex|DeleteIndex)File` and copy each named file to `/mnt/Backups/Ubuntu/_yamaguchi_retention_aside` (root 0700, outside the "
    "Dropbox root; `sudo cp -p`, `sha256sum` on both sides); (4) **remove all three options** and confirm with `export <id>` that none "
    "remains — left in place, `--dry-run` would make every later run, AC-3 among them, a dry run; (5) only then queue the real Repair. "
    "Then `sudo -u duplicati shred -u /home/duplicati/repair-dryrun.log` (the log is the service's, 0640): its `DryRun` lines name remote files only, but at that level it also carries warnings and errors, "
    "which nobody audited for content. Last resort, Recreate. B's first backup, AC-3, is then a manual `run <id>` and `resume`.",
)

edit(
    "P0 step 10: the guard aborts the first backup only after the restart (R4B DEFECT-1)",
    "so a missing or failing guard aborts the first backup, which `resume` fires immediately.",
    "so a missing or failing guard aborts the first backup that `resume` fires — once the restart below has queued the job afresh from "
    "the edited database; the copy queued at the first start carries no guard.",
)

edit(
    "section 10.2 step 4: the volume count moves after P0 (R4B NIT-11)",
    "| 4 | Copy the 877 volumes to staging on",
    "| 4 | Copy every volume at the destination (877 on 09-21; after P0, five dlists fewer and the new filesets' volumes more) to staging on",
)

edit(
    "R-6: the STOP's question is settled (R4C NIT-2)",
    "(owner ruling, note 10.1f; the STOP at the top of §8 asks whether Procedure B's step-7 start must come first)",
    "(owner ruling, note 10.1f; the 2026-09-24 STOP asked whether Procedure B's step-7 start must come first — note 8a: it follows step "
    "8's installer)",
)

edit(
    "section 5: the extractor is residue, not a STOP follow-up (R4C NIT-2)",
    "the follow-up behind the STOP at the top of\n§8 owes one.",
    "the no-print key-candidate extractor (§8 note 8a's\nresidue, built only if the history counts are non-zero) owes one.",
)

edit(
    "S-now: the STOP was cleared (R4C NIT-2)",
    "Held\n  until the STOP at the top of §8 is lifted:",
    "Held\n  until the STOP of 2026-09-24 was cleared (2026-10-03, note 8a), and runnable since in §8's order:",
)

edit(
    "P0 step 4: the A0 restore refusal reaches every depth (round 6, DEFECT-2; C2)",
    "The script refuses a restore path under\n   `/home/pcalnon/` for the same reason:",
    "The script refuses a restore path under\n   `/home/pcalnon/` — at any depth, existing or not, and through a symlink (`realpath -m`; Phase B round 6, "
    "DEFECT-2: `readlink -f` let a path two or more new levels deep through) — for the same reason:",
)

NOTE_8A = f"""
Notes on the clearing:

- **(8a)** The STOP's exit condition was "fixes items 1–5 and the findings beneath them, settles each open
  question in its last paragraph, passes its own validation round, and removes it." The fixes are the
  artifacts named in the block above and in §12's 2026-10-03 row; the open questions are settled thus: P0.5b
  is needed on Procedure A only (its heading); it runs inside step 10, after that step's edits and in place
  of the operator's `resume` — the script refuses while a task is active, pauses the scheduler itself, and
  its own closing `resume` fires the overdue backup, under the new key; Procedure B's first start follows
  step 8's installer and the password-init hand start (step 7); P0.5a items 5 and 7 keep their 2026-09-24
  timing (note 10.1f) and item 7's precondition is met — the two `su - duplicati` shells closed on
  2026-09-24 (note sink-b). The validation is the assessment's Phase B round and the round on its fold-in,
  recorded in `{ASSESS}` §8 and archived verbatim in `{RECORD}`. Residue is the block's last paragraph.
"""


def edit_census() -> str:
    """The edit count every summary of this script must quote: total, prose and fence (round 3, R3C N-9)."""
    return f"{len(EDITS)} edits: {len(EDITS) - len(FENCE_EDITS)} prose, {len(FENCE_EDITS)} fence"


def main() -> int:
    if not FIXFWD_FORM.fullmatch(FIXFWD):
        print(f"  GATE     FIXFWD_PR={FIXFWD!r} is not of the form ml#<digits> -- set FIXFWD_PR=ml#<n>", file=sys.stderr)
        print("\n1 gate(s) failed; NOTHING written.", file=sys.stderr)
        return 3
    if not DESIGN.is_file():
        print(f"FATAL: {DESIGN} not found (run from the repository root)", file=sys.stderr)
        return 2
    original = DESIGN.read_text(encoding="utf-8")
    digest = stop_block_digest(original)
    if digest is not None and digest != STOP_SHA256:
        print(f"FATAL: the STOP block differs from the one this script replaces (sha256 {digest[:16]}…, expected "
              f"{STOP_SHA256[:16]}…) -- main changed it; read the change and update CLEARED before re-running. "
              "NOTHING written.", file=sys.stderr)
        return 1
    text = original
    failures: list[str] = []
    applied = skipped = 0
    for tag, old, new, count in EDITS:
        have = text.count(old)
        if have == count:
            text = text.replace(old, new, count)
            applied += 1
            print(f"  OK       {tag}")
        elif have == 0 and (not GONE[tag].search(text) if new == "" else already_applied(text, new)):
            skipped += 1
            print(f"  ALREADY  {tag}")
        else:
            why = "; its `gone` pattern still matches -- main reworded the text" if new == "" and have == 0 else ""
            failures.append(f"{tag}: anchor found {have}x, expected {count}x{why}")
            print(f"  FAIL     {tag}: found {have}x, expected {count}x{why}", file=sys.stderr)
    if failures:
        print(f"\n{len(failures)} anchor(s) failed; NOTHING written.", file=sys.stderr)
        return 1
    if "\x00STOP-REPLACED\x00" in text:
        text = replace_stop_block(text)
        # note 8a goes right after the block, before the "Ten paths" paragraph (its edited first sentence)
        anchor = TEN_PATHS
        if text.count(anchor) != 1:
            print("FATAL: cannot place note 8a", file=sys.stderr)
            return 1
        text = text.replace(anchor, NOTE_8A.lstrip("\n") + "\n" + anchor)
    if text == original:
        print(f"\nno change ({skipped} edit(s) already applied) -- idempotent; {edit_census()}")
        return 0
    text, wrapped = reflow(original, text)

    gate_failures: list[str] = []
    before_long = Counter(line for line in original.split("\n") if len(line) > 512)
    after_lines = text.split("\n")
    for line, n in Counter(line for line in after_lines if len(line) > 512).items():
        if n > before_long[line]:
            where = [i for i, t in enumerate(after_lines, 1) if t == line]
            gate_failures.append(f"OVER-WIDTH line(s) {where}: {len(line)} chars")
    before = [m.group(0) for m in FENCE.finditer(original)]
    after = [m.group(0) for m in FENCE.finditer(text)]
    expected = list(before)
    for old_body, new_body in FENCE_EDITS:
        hits = [i for i, block in enumerate(expected) if old_body in block]
        if not hits and sum(new_body in block for block in expected) == 1:
            continue  # applied by an earlier run; the block must then be unchanged, like any other
        if len(hits) != 1:
            gate_failures.append(f"a declared fence edit matches {len(hits)} fenced blocks, expected exactly 1")
            continue
        expected[hits[0]] = expected[hits[0]].replace(old_body, new_body)
    if after != expected:
        gate_failures.append("a fenced code block changed beyond FENCE_EDITS -- prose only otherwise (run --from-repo first, separately)")
    for stale in STALE:
        if stale in text:
            gate_failures.append(f"stale phrase survived: {stale!r}")
    if "ml#FIXFWD" in text:
        gate_failures.append("the fix-forward PR number is still the placeholder -- set FIXFWD_PR=ml#<n>")
    if gate_failures:
        for f in gate_failures:
            print(f"  GATE     {f}", file=sys.stderr)
        print(f"\n{len(gate_failures)} gate(s) failed; NOTHING written.", file=sys.stderr)
        return 3
    DESIGN.write_text(text, encoding="utf-8")
    print(f"\napplied {applied}, already-present {skipped}; {wrapped} line(s) wrapped; fenced blocks: {len(after)}, "
          f"{len(FENCE_EDITS)} changed as declared, the rest byte-identical; {DESIGN} now {len(after_lines)} lines; "
          f"{edit_census()}")
    if Path(".git").exists():
        subprocess.run(["git", "diff", "--stat", "--", str(DESIGN)], check=False)
    return 0


if __name__ == "__main__":
    if sys.argv[1:]:
        raise SystemExit(f"usage: {sys.argv[0]}")
    raise SystemExit(main())
