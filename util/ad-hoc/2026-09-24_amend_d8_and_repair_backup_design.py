#!/usr/bin/env python3
"""Record the owner's 2026-09-24 rulings in the backup design, repair its stale text, and stop §8.

Project:     juniper-ml
Sub-Project: backup infrastructure
Author:      Paul Calnon
Created:     2026-09-24
Status:      ad-hoc -- document-of-record edit
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md
             sections 6, 8, 10, 11 and 12
             notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md
             prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_backup-arc-seven-decisions-ruled-smart-passed-p0-is-next.md
             (items 3, 4 and 5 of "What THIS SESSION may do next" scoped the first draft)

What this records, all of it prose:

1. THREE OWNER RULINGS OF 2026-09-24.
   D-8 amended: the one log scrub runs before P0, as P0.5a item 4, not "after P1". The 2026-09-22 ruling
   was made from section 10's Recommendation column, which ml#1999 never updated after round 1 (Lane B3,
   F-18) moved the scrub into a P0.5 bucket and round 2's split made it P0.5a item 4. ml#1999 merged at
   04:55 CDT on 2026-09-22; the rulings were recorded by ml#2029, merged at 20:44 the same day.
   P0's gate: P0.5a items 1, 2 and 4 precede P0; items 5-7 run alongside, each before the step needing it.
   The ruling set no order among items 1, 2 and 4; the design's number order comes from note 10.1e.
   What the STOP holds: P0.5a items 2 and 4, P0, P0.5b, P1, P2 and P4. The rest of section 8 is
   released, within two limits (note 10.1g); since round 7 the design reads the ruling's "only reads" and
   its transcript limit narrowly, and says so.
2. TEXT THE 2026-09-22 RULINGS, OR ml#1999's OWN MERGE, LEFT STALE: the front matter's order, section 8's
   step -1 paragraph, P1 steps 3 and 5, P2 step 2, section 6's S-1/S-2/S-3 sentence, a preface for
   section 10, section 11's round-3 count and D-14 dissent, and note 10.2a's dead "section 12" citation.
3. DEFECTS OF FACT. P0 step 0(c) and note 10.2c said `--no-local-db` rebuilds from "all 877 dindex
   volumes": 877 is the destination's TOTAL (434 dblock + 434 dindex + 9 dlist, counted 2026-09-24), and
   the ">30 minutes" they cite was recorded on 2026-08-23 by ml#1268 against the old `Ubuntu` archive,
   before the Yamaguchi destination existed.
4. ROUNDS 4 TO 8. Round 4's three validators found defects in section 8's procedure itself; the five
   re-derived from source go into a STOP block at the top of section 8, and the front matter points at
   it. Rounds 5 to 7 each checked the previous pass's corrections and found more -- in the corrections'
   own text, in older text they now contradicted, in host state the design still described after it had
   moved, and, in round 7, in what the release lets the owner do today. Fixing the procedure is a
   separate change; the owner ruled this one narrow on 2026-09-24.
5. ml#2045's DROPPED CHANGES: note 10.2b moved ahead of 10.2c (adopted); four whole tables re-padded to
   column alignment (not adopted). The SMART-script refactor is adopted in its own file, not here.
6. SECTION 12 ROWS that were owed, and this one.
7. ONE LINE OF THE ROUND-2 RECORD, whose "15 defects, all applied" round 4 refuted.

Guards, all checked BEFORE anything is written, in each file the edit set touches:
  * `edit()` refuses an edit whose `old` is a substring of its `new` (the 2026-09-22 double-apply);
  * every anchor must occur exactly the declared number of times;
  * no line longer than 512 characters may occur more often afterwards than before (MD013 counts table
    rows). The count is per distinct line, so a new copy of a long line the file already carries fails
    too; the long lines a file already carries -- the round-2 record has seventy, all verbatim reports --
    are not this script's to judge;
  * every fenced code block -- including the indented ones inside list items -- must be byte-identical
    before and after: the design's tagged blocks are what util/ad-hoc/2026-09-22_stage_design_artifacts.py
    extracts, so a prose edit that touched one would silently desynchronise a staged artifact;
  * each file's own list of stale phrases (STALE_BY_PATH) must be absent from it afterwards.

`--self-test` watches the anchor count and the width, fence and stale-phrase gates each fail on a
mutant, working on temporary copies of the base commit; it writes nothing in the repository.
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

DESIGN = Path("notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md")
ROUND2 = Path("notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md")
ROUND4 = "JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md"

EDITS: list[tuple[str, str, str, int, Path]] = []

# A fence may be indented (a block inside a numbered list item is); the closing fence carries the
# same indentation, which the backreference enforces.
FENCE = re.compile(r"^([ \t]*)```[^\n]*\n.*?^\1```", re.M | re.S)

STALE = (
    "877 dindex",
    "pending merge:",
    "**Re-decide D-2**",
    "**After a D-14 ruling**",
    "D-8's journal scrub after P1",
    "Run P0.5a items 1 and 2 before anything in P0",
    "§12 / D-12a",
    "15 defects, all applied",
    "**The destination permission model — OPEN**",
    "without checking anything",
    "VALIDATED (round 2)",
    "the next action in this arc is §8's P0 recovery",
    "**two rounds**, plus a third",
    "`nologin` **immediately**",
    "**Time-critical, owner**: `history -c",
    "The owner actions §6 lists outside §8",
    "Do this **after** the two live",
    "shred when the editor closes",
    "still unwritten and still recoverable",
    "listed as owner actions in §8",
    "it is the one check §7.5 item 6",
    "(none depends on the recovery)",
    "grep -c ENCRYPTION /root/.bash_history",
    "Two live `su - duplicati`",
    "which is true of five and false of",
    "depend on nothing in the recovery",
    "None touches the recovery",
    "each reading a frozen commit) confirmed 41",
    "in P0, in that\n  order. Items 5–7",
    "§11's round-3 count, round count",
    "deletes the old copies server-side",
    "(§8 owner actions)",
    "once the migration is accepted (R-6)",
    "owner-gated exactly as §8 is",
    "editor backups of the unit are the last untested",
    "anything that only reads, such as P0 step −1's review",
    "Items 5–7 run in the same session",
    "items 5–7 run in the same session",
    "the release's two limits in",
    "with the 877 in §10.2 steps 4–7",
    "start the S-4 copy-out",
    "which P1 step 4 first **copies**",
    "so the exit wrote nothing",
    "whether their working copy had a debug switch is recorded",
    "NOT EXECUTABLE — §8 is behind a STOP",
    "do not execute §8 yet.**",
    "touches P0.5a items 1, 5, 6 or 7",
    "-i -E 'encryption\\|passphrase",
    "`Duplicati.empty-2026-09-20/.env` included (P1 step 2)",
    "reads that write nothing",
    "three of them only after round 7",
    "Those four files are the",
    "P3 but its step 3",
    "count-grep now",
    "look before then",
    "except the one escrow copy named in P1 step 4",
    "(no shell history names it)",
    "`/home/duplicati/bin/` entirely\n(it holds",
    "rounds 4–7",
    "Rounds 4–7",
    "seven rounds",
    "four rounds' reports",
    "holds all four rounds",
)

# The round-2 record is checked for its own stale phrase only: it legitimately carries others --
# "VALIDATED (round 2)" is its subject, not a leftover.
STALE_BY_PATH = {DESIGN: STALE, ROUND2: ("15 defects, all applied",)}


def edit(tag: str, old: str, new: str, count: int = 1, path: Path = DESIGN) -> None:
    # A re-run must not apply an edit twice. If `old` survives inside `new`, the anchor still matches
    # after the edit lands, and the ALREADY test in main() cannot see it (the count is 1, not 0).
    if old in new:
        raise SystemExit(
            f"NON-IDEMPOTENT edit {tag!r}: `old` is a substring of `new`. "
            f"Widen the anchor to SPAN the insertion point instead of preceding it."
        )
    EDITS.append((tag, old, new, count, path))


# --------------------------------------------------------------------------------------------
# Front matter -- the round-4 record, a STOP, and the order level with section 8 and the rulings.
# --------------------------------------------------------------------------------------------

edit(
    "front matter: round 4, STOP, order",
    """  - `JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md`
- **§8 is executable in this order and no other**: **P0.5a** items 1–2, then **P0 step −1** (review and merge the nine scripts §8 invokes that are now staged; the tenth is a P3 deliverable), then **P0 step 0**'s owner gates, then **P0**, then **P0.5b** (the re-key, which needs the recovered data folder).""",
    f"""  - `JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md`
  - `{ROUND4}` — rounds 4–8, which found defects in §8's procedure itself
- **STOP — §8 is held, except what the owner released on 2026-09-24.** Rounds 4–8 found defects in the procedure that can re-lock the recovered database, pass the pre-backup guard without its `TargetURL` check, or copy a cleartext database into the backup Source. The STOP block at the top of §8 lists them and what may run now — P0.5a items 1, 5, 6 and 7, P3's tier-2 fix, §6's sink checklist, S-4's `chmod 0600` and the reads it names — within its two limits (note 10.1g); the rest waits until it is gone.
- **§8's order once the STOP is cleared — this and no other, unless the follow-up changes it**: **P0.5a** items 1, 2 and 4, in that order, then **P0 step −1** (a review — all nine scripts §8 invokes are merged; the tenth is a P3 deliverable), then **P0 step 0** (a verification since the 2026-09-22 rulings, §10.1; item (c) after step 1's freeze), then **P0 steps 1–8**, then **P0.5b** (the re-key, same session as step 8 — it needs the recovered data folder), then **P0 steps 9–11**.
  - P0.5a items 5–7 run alongside, each before the step that needs it: item 7 before step 8's first start, item 5 before step 10's `resume`; item 6, a repository change, lands whenever it is ready and gates nothing (owner ruling 2026-09-24, note 10.1f).
  - P0.5a item 1 is released now (note 10.1g); if it has already run, this order starts at item 2.""",
)

edit(
    "front matter: status",
    "- **Status**: VALIDATED (round 2) — consensus round 1 (six validators) and round 2 (four lanes) have both reported, and every finding is applied or recorded as dissent in §11.",
    "- **Status**: HELD, except what note 10.1g releases — §8 is behind a STOP (rounds 4–8, 2026-09-24). Rounds 1 and 2 are reconciled; round 3 found 15 defects and 13 were applied, D13 is open (note 12a); rounds 4–8 found defects in §8's procedure, which are open (§11). The owner's rulings are in §10.1.",
)

# --------------------------------------------------------------------------------------------
# Section 2 -- R-6 says `nologin` "immediately"; the 2026-09-24 gate ruling times item 7.
# --------------------------------------------------------------------------------------------

edit(
    "R-6: item 7's timing",
    "| O | Kept; `nologin` **immediately**, in §8 P0.5a item 7 — moved out of P4",
    "| O | Kept; `nologin` in §8 P0.5a item 7, before step 8's first start (owner ruling, note 10.1f; the STOP at the top of §8 asks whether Procedure B's step-7 start must come first) — moved out of P4",
)

# --------------------------------------------------------------------------------------------
# Section 6 -- S-2's value IS the live passphrase, so a settings-key re-key does not retire it.
# --------------------------------------------------------------------------------------------

edit(
    "section 6: what retires S-1, S-2 and S-3",
    """missed a file. S-1 and S-2 stop mattering once both keys are rotated (P0.5 does the re-key); S-3 matters as
long as the current set is in service, which is what D-2 decides.""",
    """missed a file. S-1's key unlocks nothing (note S-1a), so its lines matter only as a published literal. S-2's value
**is** the live passphrase, so its lines matter as long as any ciphertext under it survives, whatever the settings-key
re-key (P0.5b) does: the live set until §10.2 re-encrypts it and no pre-rotation copy is left — its step 8 deletes
the server-side ones, and §10.2 does not say what step 7's swap does with the local set — and the 811-volume
`_yamaguchi_frozen_20260826/` copy of the same set (§4.4), which §10.2 does not name. S-3 is that passphrase plus
`PASSPHRASE_OLD`, the old archive's, which D-2 does not touch.""",
)

edit(
    "section 6: the shells' sink row is overtaken",
    "| **Time-critical, owner**: `history -c; unset HISTFILE` in each shell *before* it exits |",
    "| **Overtaken on 2026-09-24** — both shells have exited; note sink-b says what that leaves |",
)

edit(
    "section 6: the shells' sink row no longer calls them live",
    "| Two live `su - duplicati` shells (pids 3065639, 3117158) |",
    "| Two `su - duplicati` shells (pids 3065639, 3117158), live at round 2 |",
)

edit(
    "section 6: note sink-b",
    """A purge that walks only the transcripts misses them.
- **(S-9a)**""",
    """A purge that walks only the transcripts misses them.
- **(sink-b)** Both `su - duplicati` shells had exited by 15:19 CDT on 2026-09-24, and
  `/home/duplicati/.bash_history` (0600 `duplicati`) was last written at 14:56:34 that day, 8,261 bytes. So
  whether `history -c; unset HISTFILE` ran first is unknown, and the 09-20 migration's commands may now be on
  disk. The root `vim` (pid 2318515) had exited too, with no swap file left behind (its row above). Owner:
  count, never print — keep the `-c` —
  `sudo grep -c -i -E 'encryption|passphrase|password' /home/duplicati/.bash_history`. **Do not wipe it on the
  count.** Those shells were open during 09-19's key failures against the root folder, so the file may hold key
  candidates §5.4 never listed; wipe it with root's history, once P0 step 3 has tested what they hold.
- **(sink-c)** A transcript is counted by value, never by label — this arc's own prose quotes every label —
  and never with a value on argv, where it would land in shell history and, run through Claude Code, in a new
  transcript. No step does that yet; the method is follow-up. The `.jsonl` transcripts are purged only within
  the release's second limit, which exists to keep this arc's validation reports (note 10.1g). A `journalctl`
  capture the harness saved under `tool-results/` holds no report, and the last row's rule applies to it: it
  goes in the session that made it.
- **(S-9a)**""",
)

edit(
    "section 6: root history is counted now and wiped only after step 3",
    "| unreadable without root; the design *relies* on them as the last place the 09-18 key may be recorded | owner: count-grep first (`sudo grep -c ENCRYPTION /root/.bash_history`), then wipe once §5.4's search is done |",
    "| unreadable without root; the design *relies* on them, with the `duplicati` user's (note sink-b), as the last places the 09-18 key may be recorded | owner: count now, never print — `sudo grep -c -i -e encryption -e passphrase -e password /root/.bash_history /root/.viminfo` — and wipe only once P0 step 3 has tested what they hold; the STOP holds step 3 |",
)

# A pipe inside a table cell must be written `\|`, and a reader who copies the command out of the raw
# file keeps the backslash -- which turns GNU grep's ERE alternation into a literal pipe and prints a
# false zero (round 7). The `-e` form has no pipe to escape.
edit(
    "section 6: duplicati's viminfo is counted, and wiped only with the history files",
    "| `/home/duplicati/.viminfo` | 14.7 KB, mtime 09-20 17:59 — vim was used as `duplicati` after `.env` was written; viminfo keeps registers and command history | wipe |",
    "| `/home/duplicati/.viminfo` | 14.7 KB, mtime 09-20 17:59 — vim was used as `duplicati` after `.env` was written; viminfo keeps registers and command history | owner: count now, never print — `sudo grep -c -i -e encryption -e passphrase -e password /home/duplicati/.viminfo` — and wipe it with the history files, once P0 step 3 has tested what they hold (note sink-b) |",
)

edit(
    "section 6: the transcript row carries the release's second limit",
    "| count-grep and purge **both** the `.jsonl` transcripts and the `tool-results/` files; this is what makes D-2's \"local exposure\" framing false |",
    "| as note sink-c says: count by value, never with a value on argv, and purge only within the release's transcript limit; this is what makes D-2's \"local exposure\" framing false |",
)

edit(
    "section 6: the re-measuring row covers tool-results copies too",
    "deletes the capture in the same session, and says so |",
    "deletes the capture in the same session, and says so — a copy the harness saved under `tool-results/` included (note sink-c) |",
)

edit(
    "section 6: the root editor's swap file is overtaken",
    "| root-owned but **0644, world-readable**; 0 `ENCRYPTION` lines when counted; the same editor carried the key into that unit on 09-18 | shred when the editor closes |",
    "| root-owned but **0644, world-readable**; 0 `ENCRYPTION` lines when counted; the same editor carried the key into that unit on 09-18 | **Overtaken** (found 2026-09-24) — the editor (pid 2318515) has exited, and the directory's last entry change, 2026-09-22 19:10:21, bounds the swap file's removal; the unit's mtime is still 2026-09-21 01:44:57, so the exit did not write the unit (a normal exit does write a viminfo — the row above) |",
)

edit(
    "section 4.1 note (a): the shells and the editor have exited",
    "**all three were still alive 2 days 8 hours later** at round 2 — both shells' in-memory history is still unwritten and still recoverable (§6).",
    "**all three were still alive 2 days 8 hours later** at round 2; by 2026-09-24 all three had exited, and the swap file with them (note sink-b).",
)

edit(
    "section 5.4: where the key could still be recorded",
    """**Where the key could still be recorded**: root's `~/.bash_history` and `.viminfo`, and editor backups of the
unit (`/usr/lib/systemd/system/.duplicati.service.swp` — root 0644, world-readable, 0 `ENCRYPTION` lines when
checked; there is no `duplicati.service~` and no `duplicati.service.d/`), for the window 09-18 20:42–21:03.
Those are the only untested places; a candidate found there is tested with the probe in seconds. Both are
root-only reads and are listed as owner actions in §8.""",
    """**Where the key could still be recorded**: root's `~/.bash_history` and `.viminfo`, for the window 09-18
20:42–21:03, and `/home/duplicati/.bash_history` and `.viminfo`, whose shells were open during 09-19's key
failures (note sink-b). The unit's editor swap file, `/usr/lib/systemd/system/.duplicati.service.swp`, is gone
(§6's `.swp` row), and there is no `duplicati.service~` and no `duplicati.service.d/`. Those files are the only
untested places, and each needs root to read — even to confirm that root's two exist, since `/root` is 0700; a
candidate found there is tested with the probe in seconds.
No §8 step yet extracts a candidate from them without printing it; the follow-up behind the STOP at the top of
§8 owes one.""",
)

edit(
    "section 5.3: the root-history search has no section-8 step",
    "is the one place left to look (§8 owner actions).",
    """is the one place left to look, and only without printing a line — a Repair command there may carry `--passphrase`,
  and §6's row for the file says never print; no §8 step lists that search or a way to run it without printing, and once
  P0 step 3 has tested the file, the release's first limit no longer keeps it (note 10.1g).""",
)

edit(
    "section 11: root's shell history is unread, not silent",
    "renamed the profile server database (no shell history names it);",
    "renamed the profile server database (pcalnon's shell history does not name it; root's is unread, §5.3);",
)

edit(
    "section 6: S-2 points at note S-3c",
    "Re-key in **P0.5b** (note S-2a) |",
    "Re-key in **P0.5b** (notes S-2a, S-3c) |",
)

edit(
    "section 6: S-3 points at note S-3c",
    "rotation alone does not re-encrypt (note S-3b) |",
    "rotation alone does not re-encrypt (notes S-3b, S-3c) |",
)

edit(
    "section 6: note S-3c",
    """names the three hazards that ride with it.
- **(S-4a)**""",
    """names the three hazards that ride with it.
- **(S-3c)** D-2's ruling covers `PASSPHRASE` only. `PASSPHRASE_OLD` protects the old archive's ten retained
  dlists, and `_yamaguchi_frozen_20260826/` — 811 volumes the owner kept as a restore point (YAM §8.25) — sits
  under `PASSPHRASE` in the Dropbox-synced tree (§4.4), which §10.2 does not re-encrypt and §8 may not delete or
  move. Both need an owner decision, and any action on them also lifts §8's no-move rule for those paths:
  re-encrypt them — the 811 volumes are 196 GiB, a second pass of §10.2 steps 4–7, since `/` has about 376 GiB
  free for staging (note 10.2b), not the 399 GiB both sets need at once — or move them out of the Dropbox root
  and then **delete forever** the cloud copies, which otherwise stay restorable (§7.5 item 7); or accept the
  exposure in writing.
- **(S-4a)**""",
)

edit(
    "section 6: note S-now -- which rows' actions the release lets run",
    """same terms.

Detection gap behind S-1:""",
    """same terms.
- **(S-now)** What the rows above let the owner do now (the 2026-09-24 release, note 10.1g): S-4's `chmod 0600`
  and its copy out of the Dropbox root, and S-7's removal (P0.5a item 5); S-1's detection gap (item 6). Held
  until the STOP at the top of §8 is lifted: S-2's re-key (P0.5b), S-3's line deletion (P1 step 2), S-4's in-tree
  delete, "Delete forever" and account audit (P1 step 4), S-5's and S-6's password work (P0 step 9), and the D-8
  scrub (P0.5a item 4).

Detection gap behind S-1:""",
)

edit(
    "P0.5a item 7: the shells have exited",
    "Do this **after** the two live `su - duplicati` shells in §6's sink checklist have been closed per their own row — closing those is the owner's time-critical action; this makes",
    "Do this **after** every `duplicati`-uid shell outside the unit has exited — the two §6 named have (note sink-b), and `ps -u duplicati` should list only the server; this makes",
)

edit(
    "P0 step 10: TargetURL is one of two checks",
    "vacuous, and it is the one check §7.5 item 6 says the guard exists for.",
    "vacuous, and `TargetURL` is one of the two checks, with the mount, that §7.5 item 6 says give the guard its value.",
)

# --------------------------------------------------------------------------------------------
# What the release makes live (round 7): text that still timed or scoped released steps as held.
# --------------------------------------------------------------------------------------------

edit(
    "section 7.3.1: nologin comes from P0.5a item 7",
    "shell `/usr/sbin/nologin` once the migration is accepted (R-6).",
    "shell `/usr/sbin/nologin` from P0.5a item 7, before P0 step 8's first start (R-6; released 2026-09-24, note 10.1g).",
)

edit(
    "section 7.11: bin/ is not retired after acceptance -- item 1 deletes it before P0",
    """the wrapper's header comment; `/home/duplicati/bin/` entirely
(it holds only the symlink D-6 replaces with an installed copy — a "fallback" symlink into a developer checkout should not exist); and **`/mnt/Backups/Ubuntu/.dropbox-dist`**, a second, unused Dropbox client (270.4.3312) owned `duplicati:duplicati` that nothing runs — the live daemons are pcalnon's.""",
    """the wrapper's header comment; and **`/mnt/Backups/Ubuntu/.dropbox-dist`**, a second, unused
Dropbox client (270.4.3312) owned `duplicati:duplicati` that nothing runs — the live daemons are pcalnon's. `/home/duplicati/bin/` is not on this list: it holds only the symlink D-6 replaces with an installed copy — a "fallback" symlink into a developer checkout should not exist — and P0.5a item 1 deletes it before P0 (released 2026-09-24, note 10.1g).""",
)

edit(
    "front matter: the no-move rule names the in-tree escrow, which only P1 step 4 deletes",
    "  - Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved except the one escrow copy named in P1 step 4.",
    "  - Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved except the in-tree escrow `…/Dropbox/Backups/_yamaguchi_keys/`, which only P1 step 4 deletes, once P0.5a item 5 or P1 step 4 has copied it out.",
)

edit(
    "P3 step 2: what already landed",
    """class-1 drill (`util/ad-hoc/2026-08-26_backup_restore_drill.bash`).
3. Rule on D-5;""",
    """class-1 drill (`util/ad-hoc/2026-08-26_backup_restore_drill.bash`). The scheduler and the three user units landed with ml#1999; the installer and `juniper-backup-failure.service` have not.
3. Rule on D-5;""",
)

edit(
    "section 8 preamble: item 5 may make the S-4 copy; only P1 step 4 deletes",
    """`…/Dropbox/Backups/_yamaguchi_keys/`, which P1 step 4 first **copies** to a sibling outside the Dropbox root
and only then deletes from the synced tree (S-4).""",
    """`…/Dropbox/Backups/_yamaguchi_keys/`, which P0.5a item 5 or P1 step 4 first **copies** to a sibling outside the
Dropbox root, and which only P1 step 4 then deletes from the synced tree (S-4).""",
)

edit(
    "P0.5a item 5: the copy is P1 step 4's; the delete stays held",
    """`chmod 0600` the escrow `env`, and start the S-4 copy-out. The Dropbox "delete forever" and account audit are owner actions.""",
    """`chmod 0600` the escrow `env`, then make P1 step 4's copy:
   confirm `/mnt/Backups/Ubuntu/_yamaguchi_keys` does not exist — nothing in this arc creates it, so stop if it does, and into an existing directory `cp -a` nests — then `cp -a` the folder to it, `chmod 0700` the copy (`cp -a` carries the source's `0770`; §7.4) and sha256-verify both sides. The in-tree delete, Dropbox's "Delete forever" and the account audit stay with P1 step 4, which the STOP holds.""",
)

edit(
    "section 10.2: nothing in it is released",
    "execute** — it is owner-gated exactly as §8 is, and it runs *after* the recovery, not during it.",
    "execute** — it is owner-gated, note 10.1g releases none of it, and it runs *after* the recovery, not during it.",
)

edit(
    "section 11: the last untested places",
    "(root's shell history and editor backups of the unit are the last untested places)",
    "(the shell and vim histories §5.4 lists are the last untested places)",
)

# --------------------------------------------------------------------------------------------
# Section 8 -- the STOP block, the step -1 paragraph, the P0 preamble, step 0(c), P0.5a's heading
# and intro, P0.5a item 4, P1 steps 3 and 5, P2 step 2.
# --------------------------------------------------------------------------------------------

STOP_BLOCK = f"""> **STOP — §8 is not executable as written (rounds 4–8, 2026-09-24).** Independent validation of this
> document (`{ROUND4}`) found defects in the
> procedure itself. This block stays until a follow-up change fixes items 1–5 and the findings beneath them,
> settles each open question in its last paragraph, passes its own validation round, and removes it. Until then
> the owner's 2026-09-24 ruling (note 10.1g) decides what runs:
>
> - **Held**: P0.5a items 2 and 4, P0, P0.5b, P1, P2 and P4.
> - **Released**: P0.5a items 1, 5, 6 and 7 — item 1 still before item 4 — and P3's tier-2 fix (its steps 1 and
>   2; step 3 waits on D-5); §6's sink checklist and S-4's `chmod 0600`; and "read-only steps", which the design
>   reads as reads that change nothing outside a scratch directory and run no Duplicati binary (note 10.1g) —
>   P0 step −1's `--check` review, P0 step 1's two `sudo ls` listings and §6's count-only greps. P0 step 0(c) is
>   not one of them: it runs `duplicati-cli`, which item 1 must secure first, with the passphrase, and it needs
>   step 1's freeze, which writes.
> - **Two limits on what is released**: no history file is wiped before P0 step 3 has tested the key candidates
>   it may hold (§6's history rows, note sink-b), and no transcript is purged before "this arc's reports are
>   archived", which the design reads as every validation round of the arc — any still running, and the
>   follow-up's own — archived verbatim into a record merged to `main` (note sink-c, note 10.1g).
>
> Re-derived from source:
>
> 1. **Step 0(a) cannot pass where it sits.** It asks for `--require-db-encryption-key` (D-1) and a
>    `.blessed.sha256` (D-6). No shipped artifact carries the flag — `util/systemd/duplicati.default` names it
>    only in a comment — and the blessed file is written by step 8's installer. The flag also has no durable
>    home: added by hand to `/etc/default/duplicati`, it trips D-6's drift gate, and the gate's
>    `--update-backup-behavior` reinstalls the repository copy, which lacks it.
> 2. **P1 step 1, which P0.5b runs, can re-lock the database.** Its key command writes the new key over
>    `/etc/credstore/duplicati-settings-key`, then asks for the first start "with the **old** key still in the
>    credential file".
> 3. **Step 10's guard dry-run can pass without its `TargetURL` check.** Step 9's client change — the credential
>    path, and `pause`/`resume` — has not landed: `util/ad-hoc/yamaguchi_server_api.py` still reads the primary
>    checkout's `.env` and has neither subcommand. When the client fails, the dry-run's TargetURL is empty, and
>    the guard compares TargetURL only when it is non-empty. Its mount, directory and stray-file checks still
>    run, but `TargetURL` is one of the two checks §7.5 item 6 says give the guard its value.
> 4. **Restarting the snapshot timer after step 8 can copy a cleartext database into the backup Source.** The
>    timer is `Persistent=yes`, so a restart fires a missed 13:45 UTC run at once. P0.5a item 2 says to restart
>    it once step 8 has placed the recovered database, and under Procedure A0 that database is cleartext until
>    the first start.
> 5. **P0.5a item 2's `ProtectSystem=strict` — §7.7 prescribes it too — breaks the snapshot.** `strict` mounts
>    the whole hierarchy read-only (`systemd.exec(5)`), and the unit writes into
>    `/home/pcalnon/.local/state/duplicati-server-db` with no `ReadWritePaths=`.
>
> Also re-derived, beside the five: D-9's `--webservice-disable-signin-tokens` and §7.3.6's
> `--webservice-allowed-hostnames=localhost` are installed by no artifact and no step — item 1's shape — and
> round 3's D13, the `.env` path, is still open and P1 step 2 inherits it (note 12a). Three more matter because
> of the release (round 7): no P0 step 3 procedure extracts key candidates from root's and `duplicati`'s shell
> and vim histories without printing them (§5.4), and the release's first limit waits on one; P1 step 4's
> `cp -a` nests a second copy if P0.5a item 5 already made it; and §7.3.2's `InaccessiblePaths=` masks the
> escrow inside the Dropbox root but not the copy item 5 makes at `/mnt/Backups/Ubuntu/_yamaguchi_keys/`.
>
> Reported by rounds 4 and 5 and still to be re-derived: whether P0.5b is needed at all after Procedures A0, A2
> and B — its claim to close S-1 and S-2 (P0.5a's intro, P0.5b, §7.3.5) contradicts §6, where S-2's value is the
> live passphrase — and whether its placement runs server starts before step 10's `pause`; Procedure B starting
> the server before step 8 installs the unit; whether P0.5a items 5 and 7 are timed to the right events
> (Procedure B's first start is step 7, and the overdue job can run before `resume`); and the lower-severity
> items the record lists.

"""

edit(
    "section 8: STOP block",
    """## 8. Remediation plan

**Ten paths are named below;""",
    """## 8. Remediation plan

"""
    + STOP_BLOCK
    + """**Ten paths are named below;""",
)

edit(
    "section 8 preamble: step -1 is a review",
    """deliverable** (§7.3.4, §7.8), not a P0 item — do not look for it here. **P0 step −1 is to review and merge the
nine**, re-extracted with `util/ad-hoc/2026-09-21_lint_design_snippets.py` and re-staged with
`util/ad-hoc/2026-09-22_stage_design_artifacts.py`, rather than pasted onto a root prompt during the recovery.""",
    """deliverable** (§7.3.4, §7.8), not a P0 item — do not look for it here. **P0 step −1 is to review the nine.**
All nine are merged on `main` — ml#1999 landed them, and ml#2029 re-landed the three the 2026-09-22 rulings
changed — so nothing is left to merge: re-extract them with `util/ad-hoc/2026-09-21_lint_design_snippets.py`,
run `util/ad-hoc/2026-09-22_stage_design_artifacts.py --check` and read its closing line — it exits 0 either
way, so only **"0 staged"** means current, and anything else is a drift to re-stage (without `--check`), review
and merge before P0 — and read what will run, rather than pasting it onto a root prompt during the recovery.""",
)

edit(
    "section 8 preamble: P0.5 is the exception to phase order",
    """Phases are ordered; nothing in a later phase is a precondition of an earlier one — **but that is true of""",
    """Phases are ordered, and apart from P0.5 — printed after P0, but its items run before P0 or inside it (note
10.1f) — and step 9's client change, which must land with §7.6's re-pointing before P0 runs, nothing in a later
phase is a precondition of an earlier one — **but that is true of""",
)

HELD = "*Held by the STOP at the top of §8 (note 10.1g).*"

for _tag, _heading, _next in (
    ("P0", "### P0 — freeze and recover the job (target: same day)", "**Run P0.5a"),
    ("P0.5b", "### P0.5b — immediately after P0 step 8, same session", "**Item 3 (the re-key) only.**"),
    ("P1", "### P1 — secrets (same week)", "1. *(Executed in P0.5b"),
    ("P2", "### P2 — hardening and re-pointing (same week)", "1. *(The chown"),
    ("P4", "### P4 — cleanup (after seven consecutive successful daily runs)", "1. Archive"),
):
    edit(f"STOP marker under {_tag}", f"{_heading}\n\n{_next}", f"{_heading}\n\n{HELD}\n\n{_next}")

edit(
    "STOP marker under P3: released",
    "### P3 — tiers 2 and 3 (following week)\n\n1. **Fix the runner's mount root first",
    "### P3 — tiers 2 and 3 (following week)\n\n*Steps 1 and 2, the tier-2 fix, are released by the owner's 2026-09-24 ruling (note 10.1g); step 3, tier 3, waits on D-5.*\n\n1. **Fix the runner's mount root first",
)

edit(
    "P0 preamble: the gate",
    """**Run P0.5a items 1 and 2 before anything in P0.** They take minutes, depend on nothing in the recovery, and
item 1 closes the path by which the service user controls the very binaries steps 0(c), 3, 4 and 7 execute.
P0.5 is printed *after* P0 only because it also carries work that follows the recovery; an operator working
top to bottom would otherwise run the recovery with that path open.""",
    """**Run P0.5a items 1, 2 and 4, in that order, before anything in P0 — item 1 is released and may already have
run; items 5–7 may run now too (note 10.1g), each before the step that needs it** — item 7 before step 8's first
start, item 5 before step 10's `resume`; item 6 gates nothing (owner rulings 2026-09-24; the order among items 1,
2 and 4 is the design's, note 10.1f). Items 1, 2 and 4 take minutes — only item 2's timer restart waits on the recovery, for step 8 — and item 1 closes the path
by which the service user controls the very binaries steps 0(c), 3, 4 and 7 execute. Item 4 is D-8's one log
scrub; the owner's 2026-09-24 amendment moved the ruling to match it (§10.1, note 10.1e). P0.5 is printed
*after* P0 only because it also carries work that follows the recovery; an operator working top to bottom would
otherwise run the recovery with that path open.""",
)

edit(
    "P0 step 0(c): dindex count and where the timing was measured",
    """than using `--no-local-db`, which on this destination rebuilds the index from all 877 dindex volumes
(`util/ad-hoc/duplicati_drill_run.py`: ">30 minutes for a single small file here, without completing"). The
passphrase is **parsed** out of the credential file, never `.`-sourced, and never touches argv:""",
    """than using `--no-local-db`, which — as `util/ad-hoc/duplicati_drill_run.py` records it, its lines 33–35 —
rebuilds a temporary index from every dindex volume on each invocation. This destination holds **434** of them:
its 877 files are 434 dblocks, 434 dindexes and 9 dlists (counted 2026-09-24). That script's ">30 minutes for a
single small file here, without completing" was recorded on 2026-08-23 by ml#1268, during the damage drill
against the old `Ubuntu` archive, then at `/mnt/Backups/Ubuntu` (DMG §4a) — before this destination existed. It
shows the rebuild is slow, not how slow it is here. The passphrase is **parsed** out of the credential file,
never `.`-sourced, and never touches argv:""",
)

edit(
    "P0.5a: heading and intro carry the gate",
    """### P0.5a — before anything in P0 (minutes; depends on nothing)

Items 1, 2, 4, 5, 6 and 7 below. These were scattered across P1, P2 and P4 while the recovered server ran for
days with the holes open. None touches the recovery, each takes minutes, and item 1 closes the path by which
the service user controls the very binaries P0 steps 0(c), 3, 4 and 7 execute.""",
    """### P0.5a — items 1, 2 and 4, in that order, before P0; items 5–7 alongside it

*Items 2 and 4 are held by the STOP at the top of §8; items 1, 5, 6 and 7 are released (note 10.1g).*

Items 1, 2, 4, 5, 6 and 7 below. These were scattered across P1, P2 and P4 while the recovered server ran for
days with the holes open. Only item 2's timer restart waits on the recovery (for step 8), and item 1 closes the
path by which the service user controls the very binaries P0 steps 0(c), 3, 4 and 7 execute. **Items 1, 2 and 4
run before anything in P0, in that order** — item 1, released now (note 10.1g), before item 4, because until
item 1 deletes `/home/duplicati/bin/`, an unplanned restart of the running server executes whatever that path
resolves to (note 10.1e).
Items 5–7 may run now (note 10.1g), and each must be done before the P0 step that needs it: item 7 before step
8's first start, because a `duplicati`-uid shell is a hole in the confined service's mount mask; item 5 before
step 10's `resume` fires the first backup, because S-7's cleartext file sits inside the backup Source; and item 6
at any point, because it is a repository change, not a host one (owner rulings 2026-09-24, notes 10.1f and 10.1g).""",
)

edit(
    "P0.5a: the earlier heading's claim, and what came after it",
    """heading that claimed "none of it depends on the recovery", which is true of five and false of the one that
closes S-1 and S-2.""",
    """heading that claimed "none of it depends on the recovery", which was true of five and false of the one that
closes S-1 and S-2; item 2's timer restart, which waits for step 8, came later, from round 2's D8.""",
)

edit(
    "P0.5a item 4: D-8's one scrub",
    """A journal-only scrub leaves an identical copy behind.
5. **Handle S-7 and S-4.**""",
    """A journal-only scrub leaves an identical copy behind. **This is D-8's one scrub** (amended 2026-09-24 from "after P1" to here — §10.1, note 10.1e): do not repeat it after P1, where `--vacuum-time=1s` would also delete the journal of the recovery itself.
5. **Handle S-7 and S-4.**""",
)

edit(
    "P1 step 3: merged",
    "3. *(**Executed in-tree**, pending merge: `scripts/duplicati-wrapper.bash`",
    "3. *(**Executed in-tree and merged** — ml#1999, `43980f13`: `scripts/duplicati-wrapper.bash`",
)

edit(
    "P1 step 5: D-2 and D-8 are ruled",
    """5. **Re-decide D-2**, do not merely execute it: it was ruled "accept + scrub" against a local-journal exposure, and the same lines are in `/var/log/syslog*`, in cloud-linked Claude Code transcripts, and — as a cleartext passphrase file — in S-7 and in a third party's cloud (S-4). Then rule on D-8 and execute.""",
    """5. *(**D-2 and D-8 are RULED** — §10.1; kept so the numbering holds.)* This step asked for D-2 to be re-decided, not merely
   executed: the "accept + scrub" ruling assumed a local-journal exposure, and the same lines are in `/var/log/syslog*`, in
   cloud-linked Claude Code transcripts, and — as a cleartext passphrase file — in S-7 and in a third party's cloud (S-4). It was
   re-decided on 2026-09-22 as **rotate and keep**, which §10.2 runs *after* the recovery is drill-verified — not here. D-8 is
   **scrub once, before P0**, as P0.5a item 4 (amended 2026-09-24, note 10.1e), so P1 runs no log scrub.""",
)

edit(
    "P2 step 2: D-14 is ruled",
    "2. **After a D-14 ruling**, run `util/ad-hoc/2026-09-21_backup_destination_permissions.bash`",
    "2. **D-14 is RULED** — the read-only model (§10.1), which the script now implements. Run `util/ad-hoc/2026-09-21_backup_destination_permissions.bash`",
)

# --------------------------------------------------------------------------------------------
# Section 10 -- a preface; 10.1's preamble, D-8 row, notes 10.1e and 10.1f; 10.2's heading and
# step 2; notes 10.2a, 10.2b (moved ahead of 10.2c) and 10.2c.
# --------------------------------------------------------------------------------------------

edit(
    "section 10: preface",
    """## 10. Owner decisions

| ID | Decision | Recommendation |""",
    """## 10. Owner decisions

**Seven of the fourteen are RULED — on 2026-09-22, with D-8's timing amended on 2026-09-24 — and §10.1 is
binding.** This table keeps the question each ruling answered and the recommendation it was made against, so a
ruled row's "Rule before P0" or "Re-decide" is the history of a gate, not an open one.

| ID | Decision | Recommendation |""",
)

edit(
    "section 10.1 preamble: the 2026-09-24 rulings",
    """D-12 and D-13 remain open and keep their recommendations.

| ID | Ruling | Effect in this document |""",
    """D-12 and D-13 remain open and keep their recommendations. **One ruling has since been amended by the owner:
D-8's timing, on 2026-09-24** (note 10.1e). The same day the owner ruled which P0.5a items gate P0 (note 10.1f)
and what the STOP block at the top of §8 holds (note 10.1g).

| ID | Ruling | Effect in this document |""",
)

edit(
    "section 10.1: D-8 row",
    "| D-8 | **Scrub once, after P1** (`--rotate` + `--vacuum-time=1s`) | unchanged from the recommendation |",
    """| D-8 | **Scrub once, before P0** — both log stores, as P0.5a item 4 (the syslog day files, then `--rotate` + `--vacuum-time=1s`). **AMENDED 2026-09-24**; ruled 2026-09-22 as "scrub once, after P1" | P0.5a item 4 is the one scrub; §10.2 step 2 checks it rather than performing it (note 10.1e) |""",
)

NOTES_10_1EF = """- **(10.1e)** **D-8 amended 2026-09-24: the one scrub runs before P0, not after P1.** The 2026-09-22 ruling
  was made from §10's Recommendation column, which still read "scrub once, after P1". By then ml#1999 had
  already moved the scrub: round 1's Lane B3 finding F-18
  (`JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md` — no dependency on the
  recovery, takes minutes, must not stay open for days while the recovered server runs) put it in a new P0.5
  bucket, "same session as the recovery", and round 2's split made it P0.5a item 4, before anything in P0.
  Neither pass updated the column, so the ruling and the plan disagreed from the day the ruling was recorded.
  The owner resolved it for P0.5a on two grounds. **"Once" holds for the families the scrub exists for.** All
  three leaked label families — `LINE: "`, `Exporting Environment Variable` and `Settings Encryption Key:` —
  came from the wrapper, and no committed revision gates them before `64677ab0` (17:48 on 09-20): every one up
  to ml#1967's `6708cb28` (17:26) prints them unconditionally. The leaking passes ran 16:41–17:30 (§4.2 note
  6); those before 17:05 predate every commit, so which working copy they ran — and whether it had a debug
  switch — is recorded nowhere; §1, §4 and §5 say it did. From `64677ab0` the echoes sit behind `DEBUG_MODE`, off by default,
  which is why the 18:19:42 start of the running server added none; wrapper v2 carries none of them (its `die`
  path is a separate, latent case the round-4 record lists). That server is `Restart=always`. Until P0.5a
  item 1 deletes `/home/duplicati/bin/`, an unplanned restart runs whatever its `ExecStart`,
  `/home/duplicati/bin/duplicati-wrapper.bash`, resolves to — on 2026-09-24 the primary checkout's
  `scripts/duplicati-wrapper.bash`, byte-identical to `main`'s v2, but a
  branch switch there (§4.3 item 8), or a replacement inside the 0777 `bin/` (§4.1), changes that — so item 1 runs
  before item 4; P0 step 2 then stops the server. Step 3's optional probe starts `duplicati-server` under
  `systemd-run`, outside the unit, and prints none of the labels either. S-1's 23
  `Invalid slot` lines needed a unit carrying the key in a specifier-parsed setting — 22 in `Environment=`, 1
  in an `ExecStart=` revision (§4.2 note 2) — and the loaded unit has no `Environment=` line, no `%` outside
  comments and no drop-in (checked 2026-09-24), so the `daemon-reload` P0.5a item 2 needs re-emits nothing.
  **S-6's sign-in URLs are the exception**: any start with an autogenerated password mints one (note S-6a),
  so they can follow the scrub; they expire, which is why §10.2 step 2 counts only unexpired ones. **And a
  vacuum after P1 costs what one before P0 does not**: `--vacuum-time=1s` deletes *all* archived journal
  history, so run after P1 it would also delete the journal of the recovery itself — the first start, and
  what AC-8, AC-12 and AC-14 read. A secret found in either log store after P0.5a item 4's `journalctl
  --rotate` — the point AC-8's undefined "hardening timestamp" must be defined as, a follow-up item — is a
  **new** exposure, with its own row in §6, not a reason to re-run the scrub.
- **(10.1f)** **P0's gate — ruled 2026-09-24.** P0.5a items 1, 2 and 4 run before anything in P0. The ruling
  set no order among the three: the design runs them in number order because item 1 must precede item 4 (note
  10.1e; round 5 found it), and it names no constraint on item 2's place. Items 5–7 run alongside — the ruling
  said "in the same session" — each before the P0 step that needs it: item 7 before step 8's first start, item 5
  before step 10's `resume`, item 6 at any point; since note 10.1g they may also run now. Since ml#1999 the
  design had said "items 1–2" (the front matter) and "items 1 and 2" (the P0 preamble), while P0.5a's intro,
  under the heading "before anything in P0", listed "Items 1, 2, 4, 5, 6 and 7". Round 4 found that the wider
  reading would hold a recovery that has been down since 2026-09-18 on item 6, a repository change that goes
  through CI, and on item 7, which then waited on the owner closing two `su - duplicati` shells — both since
  gone (note sink-b).
- **(10.1g)** **What the STOP holds — ruled 2026-09-24.** Round 6 found that no defect the STOP block at the
  top of §8 then listed touched P0.5a items 1 or 6, or P3, and that items 5 and 7 were questioned only on their
  timing (the block's last paragraph), which running them early satisfies; round 7 added two findings on item
  5's copy, which bind only once P1 step 4 and P0 step 8 run. Holding those items would keep open the 0777
  `bin/` under a `Restart=always` server, the world-readable S-7 file, and tier 2 — broken since 2026-09-07, so
  with tier 1 down the host had no working backup at all. The owner's ruling, in its own words: hold "P0.5a
  items 2 and 4, P0, P0.5b, P1, P2 and P4"; release "P0.5a items 1, 5, 6 and 7 (item 1 still runs before item
  4), P3's tier-2 fix, §6's sink checklist and S-4's `chmod 0600`, with two limits: no history file is wiped
  before P0 step 3 tests the keys it may hold, and no transcript is purged before this arc's reports are
  archived. Read-only steps may run." Rounds 7 and 8 found two of those phrases wider than they look, and the
  design reads them narrowly. **"Read-only steps"** are reads that change nothing outside a scratch directory
  and run no Duplicati binary: P0 step 0(c) calls itself read-only, but it runs `duplicati-cli`, which item 1
  must secure first, with the passphrase, and it needs step 1's freeze, which writes. **"This arc's reports"**
  are every validation round of the arc, any still running and the follow-up's own, archived verbatim into a
  record merged to `main`. Both readings hold back more than the words alone would; the owner may widen them.
"""

edit(
    "section 10.1: notes 10.1e and 10.1f",
    """  destination tree below it, where only `duplicati` holds write on the directories — which is what an
  unlink requires.

### 10.2 D-2 execution: scrub, rotate, re-encrypt — order of operations""",
    """  destination tree below it, where only `duplicati` holds write on the directories — which is what an
  unlink requires.
"""
    + NOTES_10_1EF
    + """
### 10.2 D-2 execution: confirm the scrub, rotate, re-encrypt — order of operations""",
)

edit(
    "section 10.2 step 2: a check, not the scrub",
    "| 2 | Scrub the leaked copies: the S-7 file, the `.env` comment block, and D-8's journal scrub after P1 | S-3, S-6 and S-7 counts all read zero |",
    "| 2 | Confirm the leaked copies are gone: the S-7 file (P0.5a item 5); S-2's active key line and S-3's comment block in the live `.env` (P1 step 2) and in `Duplicati.empty-2026-09-20/.env`, which P0 step 2 moved aside and only P4 step 2 removes; both log stores — D-8's one scrub, P0.5a item 4 | S-2, S-3 and S-7 counts read zero on §6's labels, case-sensitively (v2 logs a lowercase `settings encryption key:`), and S-6 holds no unexpired token (note 10.1e) |",
)

edit(
    "section 10.2: the next action is the STOP's follow-up",
    """**the next action in this arc is §8's P0 recovery, not anything in §10.2**.""",
    """**the next action in this arc is the follow-up change that clears the STOP block at the top of §8, then §8's
P0 recovery — not anything in §10.2**.""",
)

edit(
    "note 10.2a: which copy of the SMART script produced the evidence",
    """  `util/ad-hoc/smart_checks_backup-sda.bash`. An **Extended offline** self-test completed without error
  at lifetime **28,938 h** against **28,941 h** at capture, so the scan is current and covered the""",
    """  `util/ad-hoc/smart_checks_backup-sda.bash` as ml#2041 landed it (the owner's refactor, adopted 2026-09-24,
  changes neither the commands it runs nor the names it writes). An **Extended offline** self-test completed
  without error at lifetime **28,938 h** against **28,941 h** at capture, so the scan is current and covered the""",
)

NOTE_10_2B = """- **(10.2b)** **Staging goes on `nvme0n1p5` (`/`), not on `sda`.** `sda1` has 3.1 TiB free and is the
  obvious-looking target, which is exactly the trap: it holds the sole local copy, so staging there puts
  the original and the re-encrypted copy in **one failure domain** for the whole of steps 4–7. The clean
  SMART report above does not change that — it lowers the probability, not the consequence, and the
  criterion the owner set is that access is *never* lost. `/` has 376 GiB free against the ~203 GiB
  needed, sits on a different physical device, is **ext4** so ownership and modes survive for D-14's
  read-only model, and is **outside the `/home/pcalnon` backup source**. `sdc3` (`/home`, 1.2 TiB free)
  satisfies the failure-domain test but fails the last one: staging there would sweep 203 GiB of
  ciphertext into the next fileset unless an exclusion were added first — the same class of mistake as
  S-7.
"""

edit(
    "note 10.2a: live citation, and note 10.2b moved ahead of 10.2c",
    """  This **closes** the §12 / D-12a carried item "sda SMART never read".
- **(10.2c)**""",
    """  This **closes** the §3.4 / D-12a carried item "sda SMART never read".
"""
    + NOTE_10_2B
    + """- **(10.2c)**""",
)

edit(
    "note 10.2b: removed from its old place after 10.2c",
    """  negative control that must fail, and treat the **exit code as not evidence**.
"""
    + NOTE_10_2B
    + """
---

## 11. Validation record""",
    """  negative control that must fail, and treat the **exit code as not evidence**.

---

## 11. Validation record""",
)

edit(
    "note 10.2c: dindex count and where the timing was measured",
    """  **P0 step 1's freeze** — `--no-local-db` rebuilds it from all 877 dindex volumes and was measured at
  ">30 minutes for a single small file here, without completing"
  (`util/ad-hoc/duplicati_drill_run.py`). The distinction that makes a drill possible at all is that the
  **server** database is the file locked under an unmatched key (§5.4), while the **job** index —""",
    """  **P0 step 1's freeze** — `--no-local-db` rebuilds it from every dindex volume on each invocation (434 on
  this destination), a rebuild `util/ad-hoc/duplicati_drill_run.py` recorded at ">30 minutes for a single small
  file here, without completing" against the old `Ubuntu` archive, not this one (P0 step 0(c)). The
  distinction that makes a drill possible at all is that the **server** database is the file locked under an
  unmatched key (§5.4), while the **job** index —""",
)

# --------------------------------------------------------------------------------------------
# Section 11 -- the state line, round 3's count, round 4, the D-14 dissent.
# --------------------------------------------------------------------------------------------

edit(
    "section 11: state of the record",
    "**State of the record: two rounds delivered and fully reconciled.**",
    "**State of the record: rounds 1 and 2 delivered and fully reconciled; round 3's D13 open (note 12a); rounds 4–8 (2026-09-24) open — their §8 defects are the STOP block at the top of §8, and their other findings, several outside §8, are follow-up items in the round-4 record.**",
)

edit(
    "section 11: eight rounds",
    "- **Iterations and what each one changed**: **two rounds**, plus a third single-agent confirmation pass.",
    "- **Iterations and what each one changed**: **eight rounds** — two full rounds, a single-agent confirmation pass (round 3), and rounds 4–8 on 2026-09-24.",
)

edit(
    "section 11: round 3 applied 13 of 15",
    """  15 defects, all applied. Its own instruments reproduced AC-12a's `1.7 OK` and all 15 ✗ rows, the 53/18""",
    """  15 defects, of which 13 were applied: D11 (a §12 row for the landed artifacts) and D13 (wrapper v2's `.env`
  default against §7.3.5's `/etc/duplicati/env`) were not — found by round 4 on 2026-09-24; §12 now carries
  D11's row, and D13 is open. Its own instruments reproduced AC-12a's `1.7 OK` and all 15 ✗ rows, the 53/18""",
)

edit(
    "section 11: round 4",
    """  exists to prevent. §12 records the result.
- **A procedure failure in round 2""",
    f"""  exists to prevent. §12 records the result.
  **Round 4** (2026-09-24; three lenses — fact re-probe, consequence attack, amputation — on the diff that
  records D-8's amendment, each reading a frozen commit): its fact lens confirmed 41 of that diff's claims and
  refuted 10 — among them who printed the leaked labels, how many of round 3's defects were applied, and what
  ml#2045 changed — the other two lenses refuted more of its text, and the round found defects in §8's
  procedure itself, most of them through the consequence lens. The five re-derived from source are the STOP
  block at the top of §8. **Round 5** (two lenses on round 4's corrections, reading a frozen commit) refuted 16 and 23
  statements respectively — the lenses overlap — lens A's all in the corrections' own text or the record,
  which its brief confined it to, and most of lens B's; each is applied here, listed as follow-up, or — the
  "debug mode" wording of §1, §4 and §5 — acknowledged in note 10.1e and left unchanged. **Round 6** (two
  lenses on round 5's corrections) found the STOP's first exemption wording false and its scope a decision
  the owner then made (note 10.1g), and host state the design still described that had moved (note sink-b);
  its findings are applied here or listed as follow-up, four of them only after round 7. **Round 7** (two
  lenses on round 6's corrections) found what the release had made live: a transcript row and a `.viminfo` row
  that carried neither limit, a "read-only" step that runs a Duplicati binary with the passphrase, and text that
  still bound the released items to the recovery session; each is applied here or listed as follow-up. **Round 8**
  (two lenses on round 7's corrections) found a correction recorded as applied but never made (§10.2 step 2's
  moved-aside `.env`), ruling wording that was not the owner's own (the STOP bullets and note 10.1g now quote the
  ruling), P0.5a item 5's copy-out carrying the escrow's group-writable mode, and two released instructions with
  no safe method (the root-history search and the transcript count); each is applied here or listed as follow-up.
  `{ROUND4}` holds the five rounds' reports verbatim.
- **A procedure failure in round 2""",
)

edit(
    "section 11: D-14 dissent settled",
    "  4. **The destination permission model — OPEN**, promoted to **D-14** (§10).",
    """  4. **The destination permission model — SETTLED by owner ruling.** Promoted to **D-14** (§10) while open,
     and **ruled 2026-09-22 for the read-only form** (§10.1).""",
)

# --------------------------------------------------------------------------------------------
# Section 12 -- the rows that were owed, and this one.
# --------------------------------------------------------------------------------------------

ROWS_12 = f"""| 2026-09-22 (later) | **Consensus round 3** — one agent reading a frozen document (§11): 15 defects (D1–D15), 13 applied by the `r3-*` edits of `util/ad-hoc/2026-09-22_apply_round2_corrections.py`; D11 and D13 were not (note 12a). Rounds 1–3 landed together as ml#1999 (`43980f13`). |
| 2026-09-22 (later) | **Design artifacts landed** with ml#1999 — round 3's D11, recorded 2026-09-24. **Changed**: `scripts/duplicati-wrapper.bash` (now v2). **Added**: the twelve other staged artifacts (P0 step −1's nine, `util/systemd/juniper-backup.{{timer,path,service}}`), the round-2 record, `util/ad-hoc/2026-09-22_{{stage_design_artifacts,duplicati_literal_scan,archive_consensus_reports,append_signed_commit}}.py`, `util/ad-hoc/2026-09-22_watch_pr_{{runs,regression_checks}}.bash`. |
| 2026-09-22 (evening) | **Seven owner rulings recorded** — ml#2029 (`ab434c9b`): §10.1, §10.2, and the artifacts the rulings change. **Changed**: this file, `util/systemd/duplicati.service`, `util/install_duplicati_service.bash`, `util/ad-hoc/2026-09-21_backup_destination_permissions.bash`. **Added**: `util/ad-hoc/2026-09-22_apply_owner_rulings.py`, `util/ad-hoc/2026-09-22_recoverytool_verbs.py`, `util/ad-hoc/2026-09-22_shepherd_automerge.bash`. |
| 2026-09-23 | **`sda` SMART PASSED** — ml#2041 (`4b311619`): notes 10.2a and 10.2b, and the D-12a carried item closed. **Changed**: this file. **Added**: nine reports under `reports/smart/`, `util/ad-hoc/smart_checks_backup-sda.bash`, `util/ad-hoc/2026-09-23_record_smart_result.py`. |
| 2026-09-23 (later) | **§10.2 step 1's drill placed** — ml#2057 (`d15e7c01`): it is AC-4's first drill, run inside P0 step 11, and cannot precede P0 (note 10.2c). **Changed**: this file. **Added**: `util/ad-hoc/2026-09-23_clarify_drill_ordering.py`. |
| 2026-09-24 | **Front matter reformatted**, content unchanged — ml#2067 (`dcfc024f`), re-landing that part of the closed ml#2045's change to this file (note 12b). **Changed**: this file. **Added**: `util/ad-hoc/2026-09-24_reformat_design_frontmatter.py`, `util/ad-hoc/2026-09-23_pr2045_net_effect.py`. |
| 2026-09-24 (later) | **D-8 amended; P0's gate and the STOP's scope ruled; §8 behind a STOP** (notes 10.1e–10.1g, 12b). **Changed**: this file; the round-2 record's round-3 count; `util/ad-hoc/smart_checks_backup-sda.bash` (the owner's ml#2045 refactor, adopted but for its mode). **Added**: `{ROUND4}` (rounds 4–8), `util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py`, `util/ad-hoc/2026-09-24_archive_round4_reports.py`. |
"""

NOTES_12 = """Notes on the rows above:

- **(12a)** Six rows were missing until 2026-09-24: round 3's, the artifacts row round 3 itself asked for (its
  D11), and one each for ml#2029, ml#2041, ml#2057 and ml#2067, which changed this file without one. They are
  reconstructed from each PR's merge commit and file list, not from memory. Each PR also archived its body under
  `util/ad-hoc/2026-09-22_backup-design-round2/`; those files are not repeated per row. Round 3's D13 — point
  wrapper v2's `.env` default at §7.3.5's `/etc/duplicati/env` and install that path — changes landed artifacts,
  and is open.
- **(12b)** What the 2026-09-24 (later) row changed. **The owner's rulings**: D-8's amendment (§10.1's row and
  preamble, note 10.1e, P0.5a item 4, §10.2's heading and step 2) and P0's gate (note 10.1f, the front matter,
  the P0 preamble, P0.5a's heading and intro, R-6). **Leftovers of the 2026-09-22 rulings and of ml#1999's own
  merge**: the front matter's status and order (step −1 a review of nine merged scripts; step 0 a verification;
  P0.5b between steps 8 and 9, not after step 11), §8's phase-order sentence and step −1 paragraph (with
  `--check`'s exit status), P1 steps 3 and 5, P2 step 2, §6's S-1/S-2/S-3 sentence, §10's preface, §11's
  round-3 count and D-14 dissent, and note 10.2a — its dead "§12" citation now reads
  §3.4, and its evidence line names the copy of the SMART script that produced the report. **Host state that
  moved**: the two `su - duplicati` shells and the root `vim` §6 held open had exited (note sink-b, §4.1 note
  (a), P0.5a item 7), so §6's rows for them are overtaken and §5.4 names the duplicati history as a key source.
  **The STOP's scope**: note 10.1g, the STOP block's held and released lists, a marker under every §8 phase
  heading, the history-file limit in §6's history rows and note sink-b, and the transcript limit in §6's
  transcript row. **What the release lets the owner do**: note S-now, §5.3, §5.4, §7.3.1, §7.11, the §8
  preamble's S-4 sentence, the P0 preamble, P0.5a's intro and item 5, and §10.2's opening. **Exposures D-2
  does not reach**: note S-3c, cited from the S-2 and S-3 rows. **Defects of fact**: P0 step
  0(c) and note 10.2c called all 877 destination files dindex volumes — 434 are, beside 434 dblocks and 9
  dlists — and set the ">30 minutes" measurement against this destination, when ml#1268 recorded it against the
  old `Ubuntu` archive. The comment inside the tagged `util/ad-hoc/2026-09-22_confirm_a0_premise.bash` block
  still quotes that figure with its "here": a tagged block and its landed copy change together or not at all,
  and that is left for the §8 follow-up. **ml#2045's dropped changes**: the owner's 2026-09-23 refactor of the
  SMART script (commit `b0223f18`: every constant exported, the clock read error-checked) is adopted with one
  `date` call where it had two — two calls can straddle midnight — and a header that drops the
  `# shellcheck disable=SC2034` directive the exports made dead and no longer calls its device palette the host's
  inventory. Its mode is not: `b0223f18` is `0755`, but a `createCommitOnBranch` commit cannot set a mode — a new
  file lands `100644` and an existing one keeps its own — so this one stays `100644` and runs as `sudo bash
  util/ad-hoc/smart_checks_backup-sda.bash`. ml#2045 also moved note 10.2b ahead of 10.2c, adopted here, and
  re-padded four whole tables to column alignment, which is not: every other table here uses the compact form.
  **Rounds 4–8**: the front matter's STOP bullet, the STOP block at the top of §8, P0 step 10's guard sentence
  (one of two checks), §10.2's next action — which ml#2057 wrote on 2026-09-23 and the STOP overtook — §11's
  entries and round count, and the round-4 record, which holds all five rounds.
"""

edit(
    "round-2 record: round 3 applied 13 of 15",
    """cross-reference — 15 defects, all applied. Its sharpest finding was the one round 2 created: the""",
    """cross-reference — 15 defects, of which 13 were applied (D11 and D13 were not — found by round 4 on
2026-09-24; the design's §11). Its sharpest finding was the one round 2 created: the""",
    path=ROUND2,
)

edit(
    "section 12: owed rows and notes",
    """**Added**: that script, `util/ad-hoc/2026-09-22_credential_file_shape.py`. |

---

## Appendix A — evidence excerpts""",
    """**Added**: that script, `util/ad-hoc/2026-09-22_credential_file_shape.py`. |
"""
    + ROWS_12
    + "\n"
    + NOTES_12
    + """
---

## Appendix A — evidence excerpts""",
)


def main() -> int:
    paths = list(dict.fromkeys(path for *_, path in EDITS))
    for path in paths:
        if not path.is_file():
            print(f"FATAL: {path} not found (run from the repository root)", file=sys.stderr)
            return 2

    originals = {path: path.read_text(encoding="utf-8") for path in paths}
    texts = dict(originals)
    failures: list[str] = []
    applied = skipped = 0

    for tag, old, new, count, path in EDITS:
        text = texts[path]
        have = text.count(old)
        if have == count:
            texts[path] = text.replace(old, new, count)
            applied += 1
            print(f"  OK       {tag}")
        elif have == 0 and text.count(new) >= 1:
            skipped += 1
            print(f"  ALREADY  {tag}")
        else:
            failures.append(f"{tag}: anchor found {have}x, expected {count}x")
            print(f"  FAIL     {tag}: found {have}x, expected {count}x", file=sys.stderr)

    if failures:
        print(f"\n{len(failures)} anchor(s) failed; NOTHING written.", file=sys.stderr)
        return 1

    if texts == originals:
        print(f"\nno change ({skipped} edit(s) already applied) -- idempotent")
        return 0

    # Every gate below runs BEFORE any write: a check after the write is a report, not a gate.
    gate_failures: list[str] = []

    fenced: dict[Path, int] = {}
    for path in paths:
        # Count long lines, do not merely look them up: a second copy of a long line the file already
        # carries is a new over-width line too, and a set lookup would pass it. The long lines a file
        # carried before (the round-2 record has seventy, all verbatim reports) are not ours to fail.
        before_long = Counter(line for line in originals[path].split("\n") if len(line) > 512)
        after_lines = texts[path].split("\n")
        for line, count in Counter(line for line in after_lines if len(line) > 512).items():
            if count > before_long[line]:
                where = [n for n, text in enumerate(after_lines, 1) if text == line]
                gate_failures.append(f"OVER-WIDTH {path.name} line(s) {where}: {len(line)} chars, "
                                     f"{count}x where the original had {before_long[line]}x")

        # Whole matches, not findall(): the pattern has a capture group, and findall would return only
        # the indentation of each fence -- a comparison that passes whatever the blocks contain.
        before = [m.group(0) for m in FENCE.finditer(originals[path])]
        after = [m.group(0) for m in FENCE.finditer(texts[path])]
        fenced[path] = len(after)
        if path == DESIGN and not before:
            gate_failures.append("no fenced block found in the design -- the FENCE pattern is broken")
        elif before != after:
            gate_failures.append(f"a fenced code block changed in {path.name} -- this edit set must touch prose only")

        for stale in STALE_BY_PATH[path]:
            if stale in texts[path]:
                gate_failures.append(f"stale phrase survived in {path.name}: {stale!r}")

    if gate_failures:
        for failure in gate_failures:
            print(f"  GATE     {failure}", file=sys.stderr)
        print(f"\n{len(gate_failures)} gate(s) failed; NOTHING written.", file=sys.stderr)
        return 3

    for path in paths:
        if texts[path] != originals[path]:
            path.write_text(texts[path], encoding="utf-8")
    unchanged = ", ".join(f"{fenced[path]} in {path.name}" for path in paths)
    print(f"\napplied {applied}, already-present {skipped}; fenced blocks unchanged: {unchanged}; "
          f"{DESIGN} now {len(texts[DESIGN].splitlines())} lines")
    # Outside a repository -- the self-test's scratch copies -- `git diff` given two paths silently
    # turns into `--no-index` and diffs the two files against each other.
    if Path(".git").exists():
        subprocess.run(["git", "diff", "--stat", "--", *map(str, paths)], check=False)
    return 0


BASE = "6c23fdde"  # main when this edit set was written; the self-test's copies come from it


def self_test() -> int:
    """Watch the gates fail: each mutant must be refused -- exit 1 for an anchor, 3 for a gate -- on copies of BASE.

    A gate nobody has seen fail is not known to work. Round 6 found two of them blind -- a second copy of
    a long line the round-2 record already carried, and a rewrite inside one of its fences both exited 0.
    The control, the edit set alone, must still exit 0, or every "refused" below proves nothing.
    """
    import contextlib
    import io
    import os
    import tempfile

    base = {
        path: subprocess.run(["git", "show", f"{BASE}:{path}"], capture_output=True, text=True, check=True).stdout
        for path in (DESIGN, ROUND2)
    }
    title = base[ROUND2].split("\n", 1)[0]
    long_line = next(line for line in base[ROUND2].split("\n") if len(line) > 512)
    fenced = next(
        line
        for block in FENCE.finditer(base[ROUND2])
        for line in block.group(0).split("\n")[1:-1]
        if len(line) > 8 and base[ROUND2].count(line) == 1
    )
    indented = "   sudo chown root:root /usr/lib/duplicati\n"
    appendix = "## Appendix A — evidence excerpts"
    cases = [
        ("control: the edit set alone", None, 0),
        ("an anchor the file does not carry", ("MUTANT: no such anchor 7f3c", "MUTANT 7f3c", DESIGN), 1),
        ("a second copy of a long line the round-2 record carries", (title, f"{long_line}\n\n# MUTANT", ROUND2), 3),
        ("a rewrite inside one of the round-2 record's fences", (fenced, ("X" if fenced[0] != "X" else "Y") + fenced[1:], ROUND2), 3),
        ("the round-2 record's own stale phrase", (title, "# MUTANT: 15 defects, all applied", ROUND2), 3),
        ("a new over-width line in the design", (appendix, "## Appendix A: evidence excerpts\n\n" + "Z" * 600, DESIGN), 3),
        ("a rewrite inside one of the design's indented fences", (indented, indented.replace("duplicati\n", "duplicatX\n"), DESIGN), 3),
        ("one of the design's stale phrases", (appendix, "## Appendix A: 877 dindex", DESIGN), 3),
    ]

    bad = 0
    home = os.getcwd()
    for label, mutant, want in cases:
        with tempfile.TemporaryDirectory() as work:
            for path, text in base.items():
                (Path(work) / path).parent.mkdir(parents=True, exist_ok=True)
                (Path(work) / path).write_text(text, encoding="utf-8")
            if mutant:
                old, new, path = mutant
                edit(f"MUTANT: {label}", old, new, path=path)
            os.chdir(work)
            try:
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    got = main()
            finally:
                os.chdir(home)
                if mutant:
                    EDITS.pop()
        bad += got != want
        print(f"  {'ok ' if got == want else 'BAD'}  exit {got}, want {want}: {label}")
    print(f"\n{len(cases) - bad} of {len(cases)} as expected; nothing in the repository was written")
    return 1 if bad else 0


if __name__ == "__main__":
    if sys.argv[1:] not in ([], ["--self-test"]):
        raise SystemExit(f"usage: {sys.argv[0]} [--self-test]")
    raise SystemExit(self_test() if sys.argv[1:] else main())
