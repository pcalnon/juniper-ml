#!/usr/bin/env python3
"""Fold consensus round 1 Lanes A1, B1, B2 and B3 into the backup design.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-09-22
Status:      ad-hoc -- reconciliation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md
             notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md
             prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-21_backup-redesign-round-1-validated-reconciliation-pending.md

Rebuilds the design from the pristine `origin/main` blob every run, so the script is
idempotent by reconstruction: re-running it always produces the same bytes. Every
replacement asserts its anchor occurs exactly the expected number of times, so a drifted
anchor fails loudly instead of silently no-opping (the "silent no-op exclusion flag" class).

Usage:  python3 util/ad-hoc/2026-09-22_reconcile_backup_design.py [--check]
        --check  writes nothing; reports which edits would apply.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DESIGN = Path("notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md")
PRISTINE_REF = "origin/main"

EDITS: list[tuple[str, str, str, int]] = []   # (tag, old, new, expected_count)


def edit(tag: str, old: str, new: str, count: int = 1) -> None:
    EDITS.append((tag, old, new, count))


# =====================================================================================
# Header / status
# =====================================================================================

edit(
    "status-line",
    """**Status**: DRAFT — consensus round 1 COMPLETE (six validators), reconciliation PENDING. Lane A2 and A3 corrections are applied; Lane A1, B1, B2 and B3 corrections are **not** — beyond the §4.1 unit row; the §11 adequacy and cannot-support entries; the §8 STOP warning; §7.3.2's env override (B1 F11); P1 step 2's `chmod 0600` (B2 D15); the AC-12 row, §0's instrument list and §12's file list (B2 D22) — (verbatim reports: `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`;
remaining work: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-21_backup-redesign-round-1-validated-reconciliation-pending.md`). **Do not execute §8 from this revision** —
see the warning at the top of §8 and the record in
§11.""",
    """**Status**: VALIDATED (round 2) — consensus round 1 (six validators) and round 2 (four lanes) are
COMPLETE and **fully reconciled**: every Lane A1, A2, A3, B1, B2 and B3 correction is applied or
recorded as dissent in §11. Verbatim reports:
`JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md` (round 1) and
`JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md` (round 2).
§8 may now be executed — **P0 step 0 first** (the owner gates in §8's preamble), and nothing under
`/mnt/Backups/Ubuntu/` is deleted or moved except the one escrow copy named in P1 step 4.""",
)

# =====================================================================================
# §0 — instruments
# =====================================================================================

edit(
    "s0-instruments",
    """`util/ad-hoc/2026-09-21_wrap_long_markdown_lines.py` (wraps over-long prose lines at word boundaries for MD013 without touching tables or fences).""",
    """`util/ad-hoc/2026-09-21_wrap_long_markdown_lines.py` (wraps over-long prose lines at word boundaries for MD013 without touching tables or fences). Validation round 1 added two more, both of which changed a conclusion: `util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py` (tests a candidate settings key against a database **copy** offline, from the SHA-256 of the key embedded in every `enc-v1:` value — it excluded both candidates §5.4 had ranked) and
`util/ad-hoc/2026-09-21_env_value_equality.py` (prints booleans only: which secret values are byte-identical to which). Reconciliation itself is `util/ad-hoc/2026-09-22_reconcile_backup_design.py`, which rebuilds this file from its pristine blob on every run so the edit set is re-derivable rather than remembered.""",
)

# =====================================================================================
# §1 — Executive summary
# =====================================================================================

edit(
    "s1-armed-restart",
    """**One more restart makes it worse.** A global systemd reload at 03:23:44 on 09-21 armed the operator's latest unit edit, whose `ExecStart` hands the wrapper a single `--daemon-opts="…"` word that neither wrapper revision can parse; the next restart or reboot starts the server on port 8200 or not at all (§4.3 item 9). Recovery (§8 P0) installs the corrected unit and wrapper before the first restart.""",
    """**One more restart makes it worse.** A global systemd reload (03:23:44 on 09-21 by the orchestrator's own journal reading; no validation lane measured that timestamp) armed the operator's latest unit edit, whose `ExecStart` hands the wrapper a single `--daemon-opts="…"` word that neither wrapper revision can parse. The server **does not start at all** on the next restart or reboot — not "on 8200 or not at all": the 0700 data-folder gate refuses the 0777 folder before argv is
even reached (§5.5, §4.3 item 9), so the argv bug is moot and the outcome is not port-dependent. Recovery (§8 P0) installs the corrected unit and wrapper, and sets the folder to 0700, before the first restart.""",
)

edit(
    "s1-recovery-count",
    """The per-job index itself (`/usr/lib/duplicati/data/BMXWPAOGLP.sqlite`) is intact under the
duplicati-owned data folder. §8 gives two recovery procedures — one that re-uses the whole data folder if the 09-18 key can be identified, one that rebuilds the job through the API from the snapshot and re-attaches the existing index. Neither needs a Recreate.""",
    """The per-job index itself (`/usr/lib/duplicati/data/BMXWPAOGLP.sqlite`) is intact under the
duplicati-owned data folder. §8 gives **four** recovery procedures, in cost order: **A0** restores a *cleartext* copy of the same database out of the 09-17 or 09-18 fileset (the snapshot lane writes inside the backup source, and the root database was unencrypted until 09-18 20:42), needing the escrowed passphrase and nothing else; **A** re-uses the whole data folder if the 09-18 key can be identified — which the offline key-hash test now says it cannot, from any
candidate this design named; **A2** wipes the encrypted fields and re-enters the two that matter; **B** rebuilds the job through the API from the snapshot. None needs a Recreate, and **all four** must move `BMXWPAOGLP.sqlite` into the new data folder and re-point `Backup.DBPath` before the first run — `DBPath` is stored absolute and is never relocated by the server, so a procedure that skips this fails its first backup read-only and loses the index to P4.""",
)

edit(
    "s1-secret-exposures",
    """**Three secret exposures must be handled with the recovery** (§6): the settings key delivered from `.env` is **byte-identical to the backup passphrase**; the wrapper's debug mode wrote every `.env` line — including commented-out lines carrying both backup passphrases — into the system journal 10 times over on 2026-09-20; and an earlier settings key is committed in a comment of `scripts/duplicati-wrapper.bash` and printed 23 times in the journal by systemd's own specifier error.""",
    """**Eight secret exposures must be handled with the recovery** (§6): the settings key delivered from `.env` is **byte-identical to the live Yamaguchi backup passphrase**; the wrapper's debug mode wrote every `.env` line — including commented-out lines carrying both backup passphrases — into the system journal **12 times** on 2026-09-20 (264 echoed lines, 60 of them commented-out assignments); an earlier settings key is committed in a comment of
`scripts/duplicati-wrapper.bash` and printed into the journal by systemd's own specifier error (23 `Invalid slot` lines = 22 `Failed to resolve specifiers` on the `Environment=` value plus one `Failed to resolve unit specifiers` on an `ExecStart` revision); a world-readable cleartext copy of **both** passphrases sits inside the backup source itself, in a worktree `.env` (S-7); and the escrow copy of both passphrases is synced to Dropbox. **rsyslog holds a complete
second copy of every journal exposure** (`/var/log/syslog*`, `syslog:adm` 0640, `pcalnon` is in `adm`), which a journal-only scrub does not touch — and so do this arc's own Claude Code transcripts, which are cloud-linked. "Local readers only" therefore means *every process running as* `pcalnon`, on a host where `pcalnon` is already root-equivalent (`sudo`, `docker`, `libvirt`, `kvm`).""",
)

# =====================================================================================
# §3 — record evaluation
# =====================================================================================

edit(
    "s34-conda-size",
    """`/var/lib/docker/volumes` (16 Juniper volumes) and `/opt/miniforge3/envs` (47 GB) are in **no** tier;""",
    """`/var/lib/docker/volumes` (16 Juniper volumes) and `/opt/miniforge3/envs` (**62 GB**, measured
2026-09-21; the record's 47 GB is stale) are in **no** tier;""",
)

# =====================================================================================
# §4.1 — component inventory
# =====================================================================================

edit(
    "s41-unit-row",
    """| `duplicati.service` (system) | vendor unit `/usr/lib/systemd/system/duplicati.service`, edited in place (09-21 01:44); no drop-in. A systemd reload at 03:23:44 **armed** the edited `ExecStart` (`'--daemon-opts="${DAEMON_OPTS}"'`); the running process used the older form | `duplicati:duplicati` | active since 09-20 18:19:42; PID 1397393; one argv element `"--webservice-port=8300 "` (trailing space); **the next restart runs the armed form** (§4.3 item 9) | `systemctl show`, `ps`, journal |""",
    """| `duplicati.service` (system) | vendor unit, edited in place 09-21 01:44:57; no drop-in. **`NeedDaemonReload=no`** — already reloaded, so the LOADED `ExecStart` is `'--daemon-opts="${DAEMON_OPTS}"'`; only the RUNNING process predates it (note a) | `duplicati:duplicati` | active since 09-20 18:19:42; PID 1397393; argv is one element `"--webservice-port=8300 "`; **the next restart runs the armed form** and fails the 0700 gate before argv matters (§4.3.9, §5.5) | `systemctl show`, `ps` |""",
)

edit(
    "s41-datafolder-row",
    """| Data folder in use | `/home/duplicati/.config/Duplicati/` (mode **0777**, files 0777) | duplicati | server DB created 18:19:43, schema **12**, **0 backups**, 4 `Failed to import backup` errors (18:39, 18:42) | forensics on a copy; `control_dir_v2/lock_v2` mtime 18:19:45 |""",
    """| Data folder in use | `/home/duplicati/.config/Duplicati/` (directory mode **0777**). "Files 0777" is true of the four copied DB files and the crashlog **only**: `.env` is 0660, `installation.txt`/`machineid.txt` 0664, subdirectories 0775, `temp/` root-owned 0755 | duplicati | server DB created 18:19:43, schema **12**, **0 backups**, 4 `Failed to import backup` errors (18:39:38/45, 18:42:39/47) | forensics on a copy; `control_dir_v2/lock_v2` mtime 18:19:45 |""",
)

edit(
    "s41-abandoned-row",
    """| Abandoned data folder | `/usr/lib/duplicati/data/` (0700, **now owned by `duplicati`**; whole `/usr/lib/duplicati` chowned to `duplicati`) | — | holds the real server DB (fields encrypted under an unidentified key since 09-18 21:03:34) and the per-job index `BMXWPAOGLP.sqlite` | `stat`; journal; snapshot journal |""",
    """| Abandoned data folder | `/usr/lib/duplicati/data/` (0700, **now owned by `duplicati`**). `/usr/lib/duplicati` and **every directory beneath it** (97) were chowned to `duplicati`; **no file was** — all 1,443 regular files, `duplicati-server` included, are still `root:root` (note b) | — | holds the real server DB (fields encrypted under an unidentified key, **between 09-18 21:03:27 and 21:08:06**) and the per-job index `BMXWPAOGLP.sqlite` | `stat`; journal; snapshot journal |""",
)

edit(
    "s41-snapshot-row",
    """| Server-DB snapshot (system timer, root) | `yamaguchi-server-db-snapshot.timer` 13:45 UTC | root | still firing daily; last 2026-09-20 08:45 CDT, `integrity ok (16 tables)`, 240 KiB → `~/.local/state/duplicati-server-db/` — **the recovery source** | `journalctl -u yamaguchi-server-db-snapshot` |""",
    """| Server-DB snapshot (system timer, root) | `yamaguchi-server-db-snapshot.timer` 13:45 UTC; `ExecStart` runs the **primary checkout's** script as root (note c) | root | still firing daily; last **2026-09-21 08:45:00**, `integrity ok (16 tables)`, 240 KiB → `~/.local/state/duplicati-server-db/` — **a recovery source, replaced every day at 13:45 UTC with a new inode**: copy it aside before P0 | `journalctl -u yamaguchi-server-db-snapshot` |""",
)

edit(
    "s41-defaults-row",
    """| `/etc/default/duplicati` | `DAEMON_OPTS="--webservice-port=8300"`; owned **`duplicati:duplicati`** 0644 | — | the service user can rewrite its own start options | `ls -la` |""",
    """| `/etc/default/duplicati` | `DAEMON_OPTS="--webservice-port=8300"`; owned **`duplicati:duplicati`** 0644 | — | the service user can rewrite its own next argv; → `root:root` in P0.5 | `ls -la` |""",
)

edit(
    "s41-tar-row-append",
    """| pcalnon profile | `/home/pcalnon/.config/Duplicati/` (0700) | — | orphaned since 08-25; `Duplicati-server.sqlite` = 4 KB stub + 112 MB WAL of an aborted local-DB Recreate; `Duplicati-server.backup` = last real profile DB (jobs `Ubuntu`, `Ubuntu-fresh`, `Schedule` empty); 57 GB of job-DB copies under `backups/` | forensics |""",
    """| pcalnon profile | `/home/pcalnon/.config/Duplicati/` (0700) | — | orphaned since 08-25; `Duplicati-server.sqlite` = 4 KB stub + 112 MB WAL of an aborted local-DB Recreate; `Duplicati-server.backup` = last real profile DB (jobs `Ubuntu`, `Ubuntu-fresh`, `Schedule` empty) and **itself `enc-v1:`** (11 blobs, one key — note d); 56 GiB of job-DB copies under `backups/`; `installation.txt` rewritten 09-20 18:10:32 | forensics |
| Second Dropbox client | `/mnt/Backups/Ubuntu/.dropbox-dist` (270.4.3312), owned `duplicati:duplicati` | — | a second, unused Dropbox distribution installed by or for the service user: directory born 09-15 15:26:22, content mtime 09-14 20:49:31, ownership last changed 09-18 20:30:49. The running daemons are pcalnon's. Retire in §7.11 | `stat`, `ls` |
| `duplicati` home | `/home/duplicati` (0755), created 2026-09-18 19:31:40 | — | `bin/` is 0777 and holds the live wrapper symlink; `.config/Duplicati` 0777 — until P0.5, any local user can rename-replace either | `stat` |""",
)

edit(
    "s41-adequacy-note",
    """### 4.2 Timeline, 2026-09-12 → 2026-09-21 (all times CDT unless marked Z)""",
    """Notes on the rows above:

- **(a)** The 03:23:44 reload time is the orchestrator's own journal reading; no validation lane measured it. When Lane A1 looked, the unit file was open in a live `vim` (pid 2318515) and two `su - duplicati` shells were running — both are sinks for the 09-18 key (§6). The live server's **last** journal lines are 09-20 18:47:44 and 18:51:33, ×4 each: `Failed to process the path: Access to the path '/media/pcalnon/temp_backups' is denied` — after the four
  import failures someone pointed it at the retired USB path.
- **(b)** `/usr/lib/duplicati` itself is `duplicati:duplicati 0755` with no sticky bit, so the service user can `mv` any entry aside and drop in its own `duplicati-cli`, `duplicati-database-tool` or `duplicati-server` — all of which root and `pcalnon` execute during P0. `/usr/bin/duplicati-*` are symlinks into it, and `webroot/` is writable the same way. This is why the chown moves to **P0.5**, ahead of the recovery, not to P2.
- **(c)** `sys.path[0]` is therefore a pcalnon-writable directory, and the unit runs as **root** at 13:45 UTC every day: a standing pcalnon→root code path that every branch switch in the primary checkout re-arms. Fixed in P0.5 (§7.7).
- **(d)** That the pcalnon `.backup` is itself `enc-v1:` — under a libsecret-minted key nobody typed (§5.4) — means every "the database stores the passphrase in cleartext" statement in the record is true of the **root** database only, and only before 09-18 21:03 (Appendix C item 9).

Every row above is a **Lane A subject**: each was re-measured on the live host by Lane A1 on
2026-09-21 (03:47–03:55 and 13:40–13:55 CDT) with the command named in its Evidence column, and §11
carries the instrument-adequacy statement for the class. Two readings that look like ACL or
ownership facts are neither: `ls` prints `+` on every `Backups/` entry because of Dropbox's
`user.com.dropbox.attrs` xattr, **not** an ACL (`getfacl` shows base entries only), and the
`/usr/lib/duplicati` chown covers directories only (row 3).

### 4.2 Timeline, 2026-09-12 → 2026-09-21 (all times CDT unless marked Z)""",
)

# =====================================================================================
# §4.2 — timeline
# =====================================================================================

edit(
    "s42-2103",
    """| 09-18 21:03:27 | Start **with** a settings key, no warning → fields of the root DB encrypted; `/usr/lib/duplicati/data` mtime 21:03:34 | journal, `stat` |""",
    """| 09-18 21:03:27 | Start **with** a settings key, no warning → fields of the root DB encrypted, **between 21:03:27 and 21:08:06**. The `/usr/lib/duplicati/data` mtime of 21:03:34 is *not* the encryption but the `-wal`/`-shm` creation (note 1) | journal, `stat` |""",
)

edit(
    "s42-2115",
    """| 09-18 21:15 → 21:29 | `Environment=SETTINGS_ENCRYPTION_KEY=…%6%x…` rejected by systemd (`Failed to resolve specifiers … Invalid slot`, 23 occurrences) → `SettingsEncryptionKeyMissingException`; one unit revision with the key inside `ExecStart` was fatal to load | journal |""",
    """| 09-18 21:15 → 21:29 | `Environment=SETTINGS_ENCRYPTION_KEY=…%6%x…` rejected by systemd (`Failed to resolve specifiers … Invalid slot`) → `SettingsEncryptionKeyMissingException` (first 21:16:18); the revision with the key inside `ExecStart` was fatal to load (21:23:25). **Only 5 `Invalid slot` lines fall on 09-18**, not 23 — the other 18 are on 09-19 (note 2) | journal |""",
)

edit(
    "s42-0919-2048",
    """| 09-19 20:48, 21:41–21:55 | Wrapper echoes `--webservice-port=8300 --portable-mode`; server fails 25 times with `Access to the path '/home/duplicati/.config/Duplicati/Duplicati-server.sqlite' is denied` — the options arrived as one argv word, so `--portable-mode` was inert and the home folder (holding a pcalnon-owned copy) was used; one attempt at 20:48 reaches the copy and reports `The database has version 19 but the largest supported version is 11` (2.3.0.4) | journal |""",
    """| 09-19 20:48, 21:41–21:55 | Wrapper echoes `--webservice-port=8300 --portable-mode`; the options arrived as one argv word, so `--portable-mode` was inert and the home folder (holding a pcalnon-owned copy) was used. **24** failed starts, not 25, in three kinds: 5 `… version is 11`, 5 `… is denied`, 14 `… is 12` (note 3) | journal |""",
)

edit(
    "s42-0920-0415",
    """| 09-20 04:15–04:43 | pcalnon profile files copied into `/home/duplicati/.config/Duplicati/` | inode birth times |""",
    """| 09-19 18:40 → 09-20 04:43 | pcalnon profile files copied into `/home/duplicati/.config/Duplicati/` in **three waves**, not one: 09-19 18:40:36–18:42:22, 09-19 21:57:36 (the 4 KB stub), 09-20 04:15:42–04:43:02 (note 4) | inode birth times |""",
)

edit(
    "s42-0920-1332",
    """| 09-20 13:32–13:37, 16:50, 17:30 | Four successful starts of the wrapper-launched server; the first (13:32:46) still echoes `--portable-mode` and listens on 8200 (options inert again); from 13:36:37 `DAEMON_OPTS` no longer carries `--portable-mode` and the server listens on 8300. Which data folder each of these starts opened cannot be read from the journal | journal |""",
    """| 09-20 13:32–13:37, 16:50, 17:30 | Four successful starts of the wrapper-launched server; the first (13:32:46) still echoes `--portable-mode` and listens on **8200**; from 13:36:37 it listens on 8300. Sixteen seconds *before* the 13:32:50 success, five starts of the **older** `wrapper.bash` died `KeyMissing` at 13:32:34 — two wrapper files were in play (note 5) | journal |""",
)

edit(
    "s42-0920-1639",
    """| 09-20 16:39–16:53 | `.env` created; `/etc/default/duplicati` rewritten; wrapper symlink created; 16:41 `encrypted, but no key`, 16:44 `Mismatch`; the wrapper in debug mode echoes every `.env` line to the journal (220 lines, 50 of them commented-out assignments) | journal, `stat`, counts |""",
    """| 09-20 16:39–16:53 | `.env` created (16:39:43); `/etc/default/duplicati` rewritten (16:39:58); wrapper symlink created (16:53:58); 16:41:16 `encrypted, but no key`, 16:44:29 `Mismatch`; the wrapper in debug mode echoes every `.env` line to the journal — **220/50/10/10 in this window, 264/60/12/12 over the day** (note 6) | journal, `stat`, counts |""",
)

edit(
    "s42-tail",
    """| 09-21 02:52 | Watchdog: `login failed (401)` | watchdog log |""",
    """| 09-20 18:47:44, 18:51:33 | The live server's last journal lines, ×4 each: `Access to the path '/media/pcalnon/temp_backups' is denied` — after the import failures it was pointed at the retired USB path | journal |
| 09-21 02:52, 12:00 | Watchdog: `login failed (401)` twice (the 12:00 run postdates this document's first draft) | watchdog log |
| undated, from ctimes | Destination chgrp: `/mnt/Backups` 09-18 20:36:53, `/mnt/Backups/Ubuntu` 20:37:41, 874 of 877 volumes 09-19 17:37. `Backups/lost+found` (2023-05-16) shows that directory was once a filesystem root. `/home/duplicati` created 09-18 19:31:40; `.dropbox-dist` chowned 09-18 20:30:49 | `stat` |

Notes on the timeline:

1. Re-encrypting fields rewrites the database file, not its directory; a **directory** mtime records an entry create/delete/rename. So 21:03:34 is the `-wal`/`-shm` **creation**, seven seconds after launch, and the encryption is bracketed only by the absent "no key" warning at 21:03:30 and the `Mismatch` at 21:08:06. That the mtime never moved again means the WAL was never removed by a clean close — so the main file alone may still hold the pre-21:03 **cleartext**
   state, which would be a second key-free recovery source. One command decides it: `sudo ls -la /usr/lib/duplicati/data/`.
2. 23 `Invalid slot` lines in total = 22 `Failed to resolve specifiers` (on the `Environment=` value: unit line 11 at 21:15:40 and 21:16:10, line 10 at 21:17:54 and 21:29:51) + 1 `Failed to resolve unit specifiers in … $DAEMON_OPTS` at 21:23:25, which carried `Unit configuration has fatal error, unit will not be started`. Only **5** of the 23 are on 09-18; the other 18 are on **09-19** (05:53:43–51 ×4, 17:46:13–23 ×3, 18:06:53–18:07:32 ×11) — i.e. the rejected
   `Environment=` line survived in the unit until at least 09-19 18:07:32, long after the operator had moved on.
3. The three kinds: 5 starts at 20:48 all `The database has version 19 but the largest supported version is 11` (2.3.0.4); 5 at 21:41 `Access to the path '/home/duplicati/.config/Duplicati/Duplicati-server.sqlite' is denied`; **14 at 21:43, 21:52 and 21:55** `… largest supported version is 12` (post-upgrade). Those 14 belong in §5.3's list of "is 12" refusals, which named only 09-20. The 20:48:12 line carries the journal identifier `wrapper.bash` — the *first* wrapper's name.
4. The middle wave matters: the 4 KB `Duplicati-server.sqlite` stub was born 09-19 **21:57:36**, so the "pcalnon-owned copy" that was denied at 21:41 was an *earlier* inode, not this one. The first wave (09-19 18:40:36–18:42:22) brought `backups/`, `control_dir_v2/`, the crashlog and `machineid.txt`; the third (09-20 04:15:42–04:43:02) brought `installation.txt`, `.backup` and `-shm`.
5. A `port 8200` line is itself the data-folder discriminator: an unusable option word falls back to port 8200 **and** makes the `--portable-mode` glued into it inert, so those starts ran on `$HOME/.config/Duplicati` (§5.4).
6. Window 16:40–16:46 exactly: 220 `LINE:` echoes, 50 commented-out assignments, 10 `Exporting Environment Variable`, 10 `Settings Encryption Key:`. Day total — the figure §1 and §6 use — is 264 / 60 / 12 / 12 across **12** passes: 16:41 and 16:44 (110 echoes each, the two crash loops) plus the successful starts at 16:50 and 17:30 (22 each), which also echoed the file and printed the key once each.""",
)

# =====================================================================================
# §4.3 — wrapper defects
# =====================================================================================

edit(
    "s43-item8",
    """8. The live symlink points into a developer checkout on a feature branch; `git checkout`, `git worktree remove` or an unfinished edit changes what the service runs on its next start. `/home/duplicati/bin` and `/home/duplicati/.config/Duplicati` are world-writable, so any local user can replace the script or the database.""",
    """8. The live symlink points into a developer checkout — today on `main` at `d721fc78`, clean for that file and byte-identical to `main:scripts/duplicati-wrapper.bash`, not on a feature branch as an earlier revision of this document said. The risk is unchanged and is about the *mechanism*, not the branch: `git checkout`, `git pull`, `git worktree remove` or an unfinished edit changes what the service runs on its next start. `/home/duplicati/bin` and
   `/home/duplicati/.config/Duplicati` are world-writable with no sticky bit, so any local user can rename-replace the script or the database until P0.5 closes them.""",
)

edit(
    "s43-item9",
    """   03:13:57 — extracts `"--webservice-port` (no value, stray quote) and ignores the
   `DAEMON_OPTS` environment entirely. **The next restart or reboot therefore brings the server up on Duplicati's default port 8200, or not at all**, and the watchdog reads `UNREACHABLE`. Do not restart the current unit before §8 P0 step 4 installs the corrected unit and wrapper.""",
    """   03:13:57 — extracts `"--webservice-port` (no value, stray quote) and ignores the
   `DAEMON_OPTS` environment entirely. **The next restart or reboot therefore does not bring the server up at all** — and that verdict does not rest on the argv bug: 2.4.0.0 checks the 0700 data-folder gate at every start, the folder has been 0777 since 09-20 18:33:45, and the gate refuses it *before* argv is parsed (§5.5). "On 8200, or not at all" was this document's earlier reading; the gate collapses it to "not at all". The watchdog reads `UNREACHABLE`
   either way. Do not restart the current unit before §8 P0 installs the corrected unit and wrapper and sets the folder to 0700.""",
)

# =====================================================================================
# §5.3 — Leg B
# =====================================================================================

edit(
    "s53-is12",
    """- The server-database schema has 16 tables (`Backup, Schedule, Filter, Option, Metadata, …`) at version 11 (2.3.0.4) or 12 (2.4.0.0). Both versions of Duplicati therefore refused the file: journal 2026-09-19 20:48 (`largest supported version is 11`), 2026-09-20 18:02 and 18:12 (`… is 12`).""",
    """- The server-database schema has 16 tables (`Backup, Schedule, Filter, Option, Metadata, …`) at version 11 (2.3.0.4) or 12 (2.4.0.0). Both versions of Duplicati therefore refused the file: journal 2026-09-19 20:48 ×5 (`largest supported version is 11`, pre-upgrade) and, post-upgrade, **2026-09-19 21:43, 21:52 and 21:55 (14 starts)** as well as 2026-09-20 18:02, 18:03 and 18:12 (`… is 12`).""",
)

edit(
    "s53-mechanism",
    """Mechanism: one second after Duplicati saved the profile server DB (`Duplicati-server.backup` and `backups/backup Duplicati-server 20260825021947.sqlite`, both 02:19:47), a **Recreate wrote a new local database into the server-database path**, and was cancelled. The main file was left at one page with every write in the WAL. This is consistent with the 2026-08-22 handoff's finding that the `Ubuntu` job's `DBPath` had been silently changed to the server DB path and with the
cancelled `Repair`/`Verify` at 02:19:19–02:19:46. From that moment the pcalnon profile had no server database at all; the production job was recreated on the root server the same morning (YAM §3).""",
    """Mechanism (sharpened by Lane B1 from the 2.4.0.0 source; neither 02:19:47 file is a "save"):

- `Duplicati-server.backup` is the **original profile-database inode**, born 2023-05-17 00:43:03 and *renamed* at 02:19:47.788. The producer is `RepairHandler.cs` 87–104: when `LocalRepairDatabase.CreateRepairDatabaseAsync` finds `knownRemotes <= 0` it does `baseName = Path.ChangeExtension(m_options.Dbpath, "backup"); File.Move(m_options.Dbpath, baseName)` and then runs a local repair. `RecreateDatabaseHandler` writes the stub in its place (same instant, 02:19:47.788)
  and its WAL at 02:19:48.142, `Operation='Recreate'`. So a **Recreate wrote a new local database into the server-database path**, and was cancelled; the main file was left at one page with every write in the WAL.
- `backups/backup Duplicati-server 20260825021947.sqlite` (02:19:47.693) is the **local-DB upgrader's** pre-upgrade copy — `DatabaseUpgrader.cs` 266–280, `BackupFilenamePrefix + " " + name + " " + yyyyMMddHHmmss + ".sqlite"` — which fires only when `Version < MAX`, i.e. only when the server file was opened *as a job database*. (`duplicati-database-tool`'s own backups are named `<name>-<ts>.bak`, so it is not that tool.)
- **The actor is unidentified.** The earlier reading — "consistent with the 2026-08-22 handoff's finding that the `Ubuntu` job's `DBPath` had been silently changed to the server DB path" — does not hold: the `.backup` this document itself reads shows `Ubuntu` already pointing at `SJTCQIIZSJ.sqlite` with no `dbpath` among its 7 job options, so the server's own job could not have supplied the server path. Something ran a Repair with an explicit `--dbpath` naming the server
  file; `~/.bash_history` holds 0 such lines and the user-lane logs name only `DQRVQNDIFX.sqlite`. Whether the pcalnon server was even running at 02:19:47 is doubtful — a WAL inode born at 02:19:48.142 means none existed, i.e. the old database had been cleanly closed. Root's shell history around 2026-08-25 02:19 is the one place left to look (§8 owner actions).
- The cancelled `Repair`/`Verify` that frame it are at **02:17:50, 02:18:37 and 02:19:24** (`Failed while executing Repair`; nine such failures in the `.backup` ErrorLog that morning, 02:05:17 → 02:19:24) and `Verify` at 02:13:07 and 02:19:46. Nothing happened at "02:19:19", which an earlier revision of this section asserted.

From that moment the pcalnon profile had no server database at all; the production job was recreated on the root server the same morning (YAM §3).""",
)

# =====================================================================================
# §5.4 — Leg C
# =====================================================================================

edit(
    "s54-body",
    """What the key at 21:03 was is not in the journal. One fact narrows it: `EnvironmentFile=` values are **not** specifier-expanded (`man systemd.exec`: an unquoted value is parsed with shell backslash rules, interior text preserved verbatim), so the 36-character literal placed in `/etc/default/duplicati` would have been delivered intact, where the same text in `Environment=` was rejected twelve minutes later — and that literal is the value the operator was demonstrably trying to
deliver at 21:15 and 21:23. The candidate order for Procedure A is therefore: (1) the 36-character literal from the wrapper's comment block, verbatim; (2) the `PASSPHRASE` value (today's `.env` key); (3) any other value the operator typed on 09-18 between 20:42 and 21:03 — the root shell's history is the only record. The later successful starts (09-19 21:20 and 21:57, 09-20 13:32–17:30) do **not** identify the key or the folder: the wrapper's single-argv defect made
`--portable-mode` inert on some of them, and a start on an empty folder creates a fresh database under whatever key is present without complaint. The `Mismatch` at 09-20 16:44 likewise says only that the folder in use then held fields encrypted under a key other than today's `.env` key. If no candidate opens the copy, the fields can be **wiped** rather than recovered: `duplicati-database-tool wipe-encryption` "removes or clears any encrypted strings from the server database
so it can be used without the original encryption key" (2.4.0.0 help; added in 2.3.0.108), after which the two wiped values that matter — `TargetURL` and the job passphrase — are re-entered from known sources (§8 P0, Procedure A2).""",
    """**What the key at 21:03 was is not recorded anywhere this design has looked, and the two candidates
this section used to rank are excluded — offline, without a server.** Every `enc-v1:` value carries
the SHA-256 of the key that wrote it (`EncryptedFieldHelper.cs` 129–139: `contentHash = value.Substring(0,
hashSizeInBytes); keyHash = value.Substring(hashSizeInBytes, hashSizeInBytes); … if (keyHash != key.Hash) throw
new SettingsEncryptionKeyMismatchException()`), so a candidate is tested against a database **copy** in
milliseconds. `util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py` (usage in its docstring; feed a
candidate ALONE on stdin — it keeps only the last uncommented `SETTINGS_ENCRYPTION_KEY=` line it reads)
returns, on copies of the 09-20 root snapshot and the pcalnon `.backup`:

- snapshot: 9 `enc-v1:` values, content hashes verified 9/9, **one** distinct key hash, **no** candidate matches;
- pcalnon `.backup`: 11 values, verified 11/11, one key hash, **no** candidate matches.

Candidates tested: the committed 36-character literal **and eleven shell-mangling variants** (quote-strip,
backslash-unescape, `$*`/`$@` removal, bash `"$…"` expansion, `%%`, CR/LF), `PASSPHRASE`, `PASSPHRASE_OLD`,
the `.env` active key and its three commented `SETTINGS_ENCRYPTION_KEY` spellings. That content hashes verify
9/9 and 11/11 proves the layout parse is right, so the test is discriminating, not vacuous. Three *different*
key hashes across snapshot, `.backup` and the live 0777 database close it from the other side: the live one is
under today's `.env` key, which is the backup passphrase, so the passphrase is excluded with no candidate test
at all.

The journal already pointed here and this section read it the wrong way round. Fifteen `Mismatch` restarts run
from 21:08:06 to 21:11:43 — **before** the first specifier error at 21:15:40. So a `%`-free or file-delivered
key that did *not* match the 21:03 key was already in play before the `%`-bearing literal could ever have been
loaded, and the `Mismatch` is equally evidence that the literal **is not** the 21:03 key. The earlier inference
("the operator was demonstrably trying to deliver the literal, therefore it is candidate 1") ignored that.

**Where the key could still be recorded**: root's `~/.bash_history` and `.viminfo`, and editor backups of the
unit (`/usr/lib/systemd/system/.duplicati.service.swp` — root 0644, world-readable, 0 `ENCRYPTION` lines when
checked; there is no `duplicati.service~` and no `duplicati.service.d/`), for the window 09-18 20:42–21:03.
Those are the only untested places; a candidate found there is tested with the probe in seconds. Both are
root-only reads and are listed as owner actions in §8.

**How a database comes to be `enc-v1:` with nobody typing a key**: on Linux the default secret provider is
`LibSecretLinuxProvider` (`SecretProviderLoader.cs` 195–205) and the server auto-generates a random key when a
provider is reachable (`Program.cs` 1212–1231). That is how the **pcalnon profile** database is encrypted
under a keyring-held key nobody escrowed. It does **not** explain 09-18: a root system unit has no session bus.

**The folder discriminator this section lacked.** `WebServerLoader.cs` 221–229 parses the port list and falls
back to `DEFAULT_OPTION_PORT` (8200) when nothing parses. A `Server has started … port 8200` line therefore
*proves* the option word was unusable — hence the `--portable-mode` glued into it was inert, hence
`GetDataFolder` fell through to `$HOME/.config/Duplicati`. The three 8200 starts (09-19 21:20:41, 21:57:41,
09-20 13:32:50) were on the duplicati **home** folder, not the root folder; the four 8300 starts had a working
option word that no longer carried `--portable-mode`. **The root folder was last opened at 09-19 19:15:01**
(a `Missing` failure), and no `Server has started` follows it. The `Missing` ×5 at 13:32:34 and the
`Missing`/`Mismatch` at 16:41/16:44 on 09-20 were the home folder's own fresh databases (its stub was born
09-19 21:57:36, five seconds before the 21:57:41 start).

(`EnvironmentFile=` values are indeed not specifier-expanded — `man systemd.exec` 259: an unquoted value is
parsed with POSIX-shell backslash rules, interior text preserved — so the literal placed in
`/etc/default/duplicati` would have arrived intact where the same text in `Environment=` was rejected twelve
minutes later. Correct, and moot: the literal is not the key.)

If no candidate is ever found, the fields can be **wiped** rather than recovered:
`duplicati-database-tool wipe-encryption` "removes or clears any encrypted strings from the server database so
it can be used without the original encryption key" (2.4.0.0 help; added in 2.3.0.108), after which the two
wiped values that matter — `TargetURL` and the job passphrase — are re-entered from known sources (§8
Procedure A2). But the cheapest route needs no key at all: **Procedure A0** restores a cleartext copy of this
same database out of the 09-17 or 09-18 fileset.""",
)

# =====================================================================================
# §5.5 — contributing factors
# =====================================================================================

edit(
    "s55-permissions",
    """- **Permissions by trial.** `/usr/lib/duplicati` (binaries included) and `/usr/lib/duplicati/data` were chowned to `duplicati`; the destination tree chgrp'd; the duplicati home dirs opened to 0777. Each removed a symptom; none was recorded.""",
    """- **Permissions by trial.** `/usr/lib/duplicati` and `/usr/lib/duplicati/data` were chowned to `duplicati` — **directories only**: all 1,443 regular files, the binaries included, are still `root:root`. The destination tree was chgrp'd (directories 09-18 20:36–20:37, 874 volumes 09-19 17:37); the duplicati home dirs were opened to 0777. Each removed a symptom; none was recorded.""",
)

edit(
    "s55-gate",
    """marker in the install folder). The migration chmod'ed the folder to 0777 *after* the 18:19 start; the next start may refuse it. §7.3.2 sets 0700.""",
    """marker in the install folder). The migration chmod'ed the folder to 0777 *after* the 18:19 start — the loosening is datable by ctime: three files at 18:25:47.326 and the directory at 18:33:45.057, so it was not a recursive chmod (`.env`, `backups/`, `installation.txt` are untouched). The 18:19:42 start therefore passed the gate, and the next start **will** refuse the folder — not "may". This is what collapses §4.3 item 9 and §1 from "on 8200, or not at all" to
  "not at all": the gate is checked before argv is parsed, so the verdict does not depend on the argv bug. §7.3.2 sets 0700.""",
)

# =====================================================================================
# §5.6 — refutation table
# =====================================================================================

edit(
    "s56-rowc",
    """| C | a `Started` line between 09-18 21:08 and 09-20 13:32 without a `Mismatch`/`Missing` error | `journalctl -u duplicati.service`, deduplicated | yes — it shows exactly such lines at 09-20 13:32 |""",
    """| C | a `Server has started` line on a start **whose data folder is the root folder** (the port discriminates — §5.4) | `journalctl -u duplicati.service`, deduplicated, read against `WebServerLoader.cs`'s port fallback | yes — and **none exists after 09-18 21:03:30** |

The Leg C row changed at reconciliation and is worth stating plainly, because as first written it was
not a refutation test at all: it named an observation that *exists* ("it shows exactly such lines at
09-20 13:32") and then explained it away. The repair is the port. A `Server has started … port 8200`
line proves the option word was unusable, hence the `--portable-mode` glued into it was inert, hence
the folder was `$HOME/.config/Duplicati` — so the 13:32:50 success is a *home*-folder start, not a
counter-example. The root folder was last opened at 09-19 19:15:01, a `Missing` failure, and no
`Server has started` follows it.""",
)

# =====================================================================================
# §5.7
# =====================================================================================

edit(
    "s57",
    """Listed in Appendix C; the load-bearing one: "schema-19 profile server DB" → "aborted local-DB Recreate stub written over the profile server DB at 2026-08-25 02:19:48; the last real profile server DB is `Duplicati-server.backup` of 02:19:47".""",
    """Listed in Appendix C; the load-bearing one: "schema-19 profile server DB" → "aborted local-DB Recreate stub written over the profile server DB at 2026-08-25 02:19:48; the last real profile server DB is `Duplicati-server.backup` of 02:19:47, which is the **original 2023 inode** renamed by a `RepairHandler` local repair, not a save". **Appendix C items 1–8 are corrections this document records; none is yet applied to its target document** — that is a tracked
follow-up, not a closed one.""",
)


# =====================================================================================
# §6 — secret exposure inventory
# =====================================================================================

edit(
    "s6-preamble",
    """## 6. Secret exposure inventory and remediation

| # | Secret | Where it is exposed | Since | Who can read it | Remediation |""",
    """## 6. Secret exposure inventory and remediation

**Read every "who can read it" cell against this host fact, which the first draft of this section did
not state**: `pcalnon` is in `duplicati(139)`, `adm`, `sudo`, `docker` (`/var/run/docker.sock` is
`srw-rw---- root:docker`, daemon active), `libvirt` and `kvm`. A hostile — or merely careless —
process running as `pcalnon` is already root-equivalent. So "local readers only" is not a small
set, and the boundaries this design can still buy are exactly four: **confined service vs host**,
**cloud account vs local disk**, **public repository vs local**, and **accidental or commodity
damage vs deliberate**. Nothing below buys "pcalnon cannot read it".

**And every journal exposure has a second copy.** `/usr/lib/systemd/journald.conf.d/syslog.conf`
sets `ForwardToSyslog=yes` and rsyslog is active and enabled, so `/var/log/syslog*` holds the same
lines — `syslog:adm` 0640, and `pcalnon` is in `adm`. Counted (never read): `syslog-20260921`
carries 264 `LINE: "` echoes, 12 `Settings Encryption Key:`, 12 `Exporting Environment Variable`
and 12 `PASSPHRASE=`, identical to the journal's counts; `syslog-20260919.gz` and
`syslog-20260920.gz` carry 4 and 18 specifier lines. logrotate keeps day files ~10 days. A journal
scrub that does not also scrub these removes nothing (D-8).

| # | Secret | Where it is exposed | Since | Who can read it | Remediation |""",
)

edit(
    "s6-s1",
    """| S-1 | Old settings key (36 chars) | `scripts/duplicati-wrapper.bash` comment, lines 38–57, in `main` since #1967; 23 systemd `Failed to resolve specifiers` journal lines | 2026-09-18 / 09-20 | anyone with the repository (public); local `adm`/`systemd-journal` members and root | Treat as burned: use it only to unlock the 09-18 database (Procedure A), then re-key (P1); remove the block from the script. A history rewrite is not worth its cost once the key is dead. Close the detection gap (below). |""",
    """| S-1 | Old settings key (36 chars) | `scripts/duplicati-wrapper.bash` comment line 49, in `main` since #1967 (`6708cb28`); 23 systemd `Invalid slot` journal lines, **and the same lines in `syslog-20260919.gz` (4) and `syslog-20260920.gz` (18)** | 2026-09-18 / 09-20 | anyone with the repository (public); every process running as `pcalnon`, via `adm`; root | Treat as burned; it unlocks nothing (note S-1a). Remove the block from the script (P1 step 3); close the detection gap (below) |""",
)

edit(
    "s6-s2",
    """| S-2 | Current settings key = **`PASSPHRASE`** (32 chars) | `.env` line 22 (0660 duplicati:duplicati — readable by group `duplicati`, i.e. `pcalnon`); journal: 10 `Exporting Environment Variable` lines and 10 `Settings Encryption Key:` lines on 09-20 16:41–16:44 | 2026-09-20 | same as S-1 (journal) | Never reuse the backup passphrase as the settings key: the key exists to protect the passphrase at rest. Generate a distinct key (P1), deliver it as a systemd credential, escrow it with the passphrases. |""",
    """| S-2 | Current settings key = **the live `Yamaguchi` backup passphrase** (32 chars) | `.env` line 22 (0660 duplicati:duplicati — readable by group `duplicati`, i.e. `pcalnon`); journal **and `/var/log/syslog*`**: 12 `Exporting Environment Variable` and 12 `Settings Encryption Key:` lines on 09-20 | 2026-09-20 | same as S-1 | Never reuse the backup passphrase as the settings key — the key exists to protect the passphrase at rest. Re-key in **P0.5 step 3** (note S-2a) |""",
)

edit(
    "s6-s3",
    """| S-3 | `PASSPHRASE`, `PASSPHRASE_OLD` | `.env` lines 17–18 as commented-out assignments; journal: 50 `LINE: "# export …"` echoes on 09-20 | 2026-09-20 | same | Delete the commented lines. **Rotation does not re-encrypt existing volumes**; the exposure is local (root, `adm`, group `duplicati`). Decision D-2: accept with a journal scrub, or start a new set under a new passphrase. |""",
    """| S-3 | `PASSPHRASE`, `PASSPHRASE_OLD` | `.env` lines 17–18 as commented-out assignments; journal **and `/var/log/syslog*`**: **60** `LINE: "# export …"` echoes on 09-20 = 12 `PASSPHRASE` + 12 `PASSPHRASE_OLD` + 36 `SETTINGS_ENCRYPTION_KEY`, each carrying text after the `=` | 2026-09-20 | root, `adm` (= every `pcalnon` process), group `duplicati` — and, through S-7, **every local user** | Delete the commented lines. **Rotation does not re-encrypt existing volumes.** **D-2 must be re-decided** (note S-3a) |""",
)

edit(
    "s6-s4",
    """| S-4 | Same passphrases in `/mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_keys/env` | now inside the Dropbox-synced tree | since the Dropbox root moved onto `sda1` | the Dropbox account | Move `_yamaguchi_keys/` out of the Dropbox root (a sibling of `Dropbox/` on `sda1`), or exclude it with `dropbox exclude add`. The sda1 escrow was accepted as a *machine-local* copy, not a cloud copy (its README). |""",
    """| S-4 | Same passphrases in `…/Dropbox/Backups/_yamaguchi_keys/env` (`-rwxrwx--- pcalnon:duplicati`, 388 B — **group-readable by the service user**, where YAM §8.19.2 recorded 0600 in a 0700 dir) | inside the Dropbox-synced tree; `dropbox filestatus` reads `up to date` | since the Dropbox root moved onto `sda1` (~09-15) | the Dropbox account and every device or app linked to it; locally, group `duplicati` | `chmod 0600` now; copy out, then delete forever and audit the account (note S-4a) |""",
)

edit(
    "s6-s5",
    """| S-5 | Web-UI credential | primary checkout `.env` (`DUPLICATI_WEB_CREDENTIAL`), **mode 0664 — world-readable**, now stale | since 2026-08-23 | every local user | New UI password on the rebuilt server, stored in `~/.config/duplicati-backup/web-credential` (0600); API client re-pointed (§7.6). Remove `util/ad-hoc/duplicati_api.py`'s bare-secret fallback (posts the whole file as the password when no candidate key matches; its list omits `DUPLICATI_WEB_CREDENTIAL`, so it takes that path today). |""",
    """| S-5 | Web-UI credential — **and twelve other secrets beside it** | primary checkout `.env` (`DUPLICATI_WEB_CREDENTIAL`), **mode 0664 — world-readable**, now stale; 12 other names in the same file, several of them Slack tokens. It holds **0** `PASSPHRASE=` lines, so S-3 is *not* world-readable through it | since 2026-08-23 | every local user | New UI password, stored 0600 at `~/.config/duplicati-backup/web-credential`; **both** API clients re-pointed in the same PR (note S-5a) |""",
)

edit(
    "s6-s6",
    """| S-6 | Sign-in token URL | journal 09-20 18:19:46 (`signin.html?token=…`, 5-minute lifetime, expired) | — | — | None needed; note that the server prints one on every start when no password is set — set the password. |""",
    """| S-6 | Sign-in token URLs | journal **and syslog**: **five** `signin.html?token=…` URLs (09-19 21:20:41, 21:57:41; 09-20 13:32:50, 13:36:40, 18:19:46), not one; all expired | 2026-09-19 | `adm` (= every `pcalnon` process) for each token's lifetime | Set the password on the first start, then pass `--webservice-disable-signin-tokens` (note S-6a) |
| S-7 | **Both passphrases, cleartext, world-readable, inside the backup source** | `juniper-ml/.claude/worktrees/curious-plotting-hummingbird/.env`, 114 B, **mode 0664**, 2026-08-23 | 2026-08-23 | **every local user**, and every restore of any fileset taken since | Reconcile fingerprints, then remove **the file only** (note S-7a). This is the exposure D-2 was ruled without |
| S-8 | `additional-report-url` bearer JWT | inside **every** copy of the server database: the daily snapshot in `~/.local/state`, the P0 evidence freeze, whatever Procedure A0/A/A2/B produces, and P4's tar | since the report URL was configured | anyone who reads any database copy | It is a credential, not merely a URL (YAM §8.18.4, §8.19.8 item 6); **rotate it if any copy leaves the machine** (note S-8a) |

Notes on the rows above:

- **(S-1a)** The burned key is **not** the key that encrypted the 09-18 database: the offline hash test excludes it and eleven shell-mangling variants (§5.4), so it unlocks nothing and Procedure A no longer depends on it. A history rewrite is not worth its cost once the key is dead — GitHub keeps `refs/pull/1967/head` regardless, and `forks_count` is 0.
- **(S-2a)** The `.env` comment labels this value "Ubuntu-fresh". **That label is stale**: `util/ad-hoc/2026-09-21_env_value_equality.py` shows it byte-identical to the live Yamaguchi passphrase. Read the value, never the comment. The replacement key is random, distinct from every passphrase, delivered as a systemd credential, and escrowed with the passphrases.
- **(S-3a)** D-2 was ruled "accept + scrub" against a *local journal* exposure. The reader set is now: every process running as `pcalnon` (via `adm`), `/var/log/syslog*` for another ~10 days, this arc's cloud-linked Claude Code transcripts, a world-readable cleartext file inside the backup source (S-7), and — through S-4 — a third party's cloud. Four different ways in which "local readers only" is false.
- **(S-4a)** `dropbox exclude add` is **not** an alternative to moving it: selective-sync exclusion removes the *local* copy and leaves the cloud one in place. So: `cp -a` the folder to a sibling outside the Dropbox root, sha256-verify both sides, delete the in-tree copy on owner sign-off, then **"Delete forever"** on dropbox.com and audit the account (2FA, linked devices, third-party apps, plan retention). The sda1 escrow was accepted as a *machine-local* copy, not a
  cloud copy — its own README says so. Exclude `_yamaguchi_records/` too if it lists paths.
- **(S-5a)** The UI credential is not a convenience: any authenticated API principal can point the job's `--run-script-before` at any path, and that script runs as `duplicati` with `CAP_DAC_READ_SEARCH`. It is **a host-wide read of everything the service can read** (§7.3.6). Also remove `util/ad-hoc/duplicati_api.py`'s bare-secret fallback, which posts the whole file as the password when no candidate key matches — and since its key list omits
  `DUPLICATI_WEB_CREDENTIAL`, that is the path it takes today. The twelve other values in that file are out of scope here but are in the same world-readable file.
- **(S-6a)** The server mints a token on **every** start while the password is still autogenerated (`Program.cs`: `if (Origin == "Server" && AutogeneratedPassphrase) … CreateSigninToken`), so every restart before the password is set writes a fresh *live* token into adm-readable logs — and with `CAP_DAC_READ_SEARCH` a token is root-read for its lifetime.
- **(S-7a)** Reconcile the sha256[:16] fingerprints per `HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §1 item 8 **first**, then remove the file. That worktree is **DO NOT SWEEP**: `git worktree remove` would delete it silently, and it is protected for unrelated reasons. Remove the file, never clean the directory.
- **(S-8a)** Procedure B must state whether the rebuild re-creates the report URL; if it does, the new JWT is a new secret and belongs in this table on the same terms.""",
)

edit(
    "s6-scrub",
    """Journal scrub (D-8): the journal cannot delete individual lines. `journalctl --rotate` followed by `journalctl --vacuum-time=1s` removes every archived file, i.e. all history older than the rotation; `--vacuum` never touches the active file, so run the rotate first and accept the loss of unrelated history, or leave the journal and rely on its `systemd-journal`/`adm` access control. Either way, S-1 and S-2 stop mattering once both keys are rotated; S-3 matters as long as the current set is in service.""",
    """Journal scrub (D-8) — **the journal is half the job**. The journal cannot delete individual lines:
`journalctl --rotate` followed by `journalctl --vacuum-time=1s` removes every archived file, i.e. all
history older than the rotation (`--vacuum` never touches the active file, so rotate first), and costs all
unrelated history. That leaves `/var/log/syslog*` completely intact, holding the same 264/12/12/12 counts,
`syslog:adm` 0640, for another ~10 days of logrotate. A scrub must therefore cover **both**: the plain day
files edited as root, the `.gz` files regenerated, then the journal rotate + vacuum. Verify with
`sudo ls -la /var/log/syslog-2026092*` afterwards — a scrub with no verification is a scrub that may have
missed a file. S-1 and S-2 stop mattering once both keys are rotated (P0.5 does the re-key); S-3 matters as
long as the current set is in service, which is what D-2 decides.

**Sink checklist** — every place a secret from this arc may still sit, beyond the rows above. The design's
first draft inventoried none of these:

| Sink | State when inspected | Action |
| --- | --- | --- |
| Two live `su - duplicati` shells (pids 3065639, 3117158) | started 09-19 18:24:50 / 18:52:00; `/home/duplicati/.bash_history` 0600, last written 09-19 18:51 — every command of the 09-20 migration is **in memory** and will be appended on exit | **Time-critical, owner**: `history -c; unset HISTFILE` in each shell *before* it exits |
| `/home/duplicati/.viminfo` | 14.7 KB, mtime 09-20 17:59 — vim was used as `duplicati` after `.env` was written; viminfo keeps registers and command history | wipe |
| Root's `~/.bash_history`, `~/.viminfo` | unreadable without root; the design *relies* on them as the last place the 09-18 key may be recorded | owner: count-grep first (`sudo grep -c ENCRYPTION /root/.bash_history`), then wipe once §5.4's search is done |
| `/usr/lib/systemd/system/.duplicati.service.swp` | root-owned but **0644, world-readable**; 0 `ENCRYPTION` lines when counted; the same editor carried the key into that unit on 09-18 | shred when the editor closes |
| CUPS spool | the escrow sheet was printed (USB HP OfficeJet, 32 completed jobs); job-file retention unknown | owner: `grep -i PreserveJobFiles /etc/cups/cupsd.conf`; `sudo ls -la /var/spool/cups` |
| Claude Code transcripts under `~/.claude/projects/…` | **cloud-linked**, and they capture every `journalctl` output this arc produced; the count grows with every tool call, so any figure is an upper bound | count-grep and purge; this is what makes D-2's "local exposure" framing false |
| World-readable server-DB copies | `Duplicati-server.backup` 0777, `backups/*pre-dbpath-fix.sqlite` 0644 — `enc-v1:` under the pcalnon-profile libsecret key, so encrypted but wrongly exposed | `chmod 0600` now |""",
)

# =====================================================================================
# §7.1 / §7.3 — design
# =====================================================================================

edit(
    "s71-principle3",
    """3. **Least privilege with one deliberate exception.** The server runs as `duplicati`, confined by systemd, and is granted `CAP_DAC_READ_SEARCH` so it can read every file under `/home/pcalnon` — the root-era coverage — without being root (D-4).""",
    """3. **Least privilege with one deliberate exception, and the exception is bigger than it looks.** The server runs as `duplicati`, confined by systemd, and is granted `CAP_DAC_READ_SEARCH` so it can read every file under `/home/pcalnon` — the root-era coverage — without being root (D-4). State the trade plainly: that capability bypasses **every** read and search check on the host, not only `/home/pcalnon` — `/etc/shadow`, `/etc/ssh/ssh_host_*_key`, `/etc/credstore/*` (every
   other service's secrets), `/root`, `/var/lib/docker`, the journal and `/var/log/syslog*` (which hold this arc's leaked passphrases), and every other user's home. `ProtectSystem=strict` and `ProtectHome=read-only` stop *writes* — they are mount flags, correctly not defeated by the capability — but hide nothing from a read. The alternative, recursive ACLs on `/home/pcalnon`, bounds the blast radius to that tree but is fragile in exactly the way AC-3 exists to catch: a
   `chmod 600`, a `mkdir -m 700`, or gpg's own permission checks reset the ACL mask and the file silently leaves the backup. So: the capability bounds the damage to *the whole host*, ACLs bound it to *one tree but unreliably*. D-4 is that choice, and it is the owner's. Whichever is chosen, §7.3.2's confinement set is what keeps the capability from also being an exfiltration channel, and the residual is recorded: **"duplicati uid inside the unit == root-read"**.""",
)

edit(
    "s731-tail",
    """- `/usr/lib/duplicati` returns to `root:root` (a service user must not own its own binaries); `/usr/lib/duplicati/data` is archived and removed after recovery (§8 P4).""",
    """- `/usr/lib/duplicati` returns to `root:root` **before P0 runs any Duplicati tool, not in P2** (§8 P0.5): the directory is `duplicati:duplicati 0755` with no sticky bit today, so the service user can move any entry aside and drop in its own `duplicati-cli`, `duplicati-server-util`, `duplicati-database-tool` or `duplicati-server` — which `root` and `pcalnon` then execute during recovery, and `/usr/bin/duplicati-*` are symlinks into it. `webroot/` is writable the same way,
  so injected JavaScript would load in the operator's browser. `/usr/lib/duplicati/data` is archived and removed after recovery (§8 P4).

**Trust domains, and the four crossings between them.** "The `duplicati` uid inside the unit" and "the
`duplicati` uid outside it" differ only by the capability and the mount view, which is why the table below is
worth writing down: every row is a way to become the other.

| Who can act as `duplicati` | How | What they gain |
| --- | --- | --- |
| root | `su`, `runuser` | everything |
| the service itself | — | capability + mount view |
| any run-script the job names | job option, set through the API | capability + mount view + the job's whole option set in its environment (§7.5) |
| **any local user, today** | `/home/duplicati/bin` and `/home/duplicati/.config/Duplicati` are 0777 with no sticky bit — rename-replace the wrapper or the database | the next start (closed by P0.5) |

| Crossing | Mechanism | Closed by |
| --- | --- | --- |
| `.env` → code in the capability-bearing process | an `LD_PRELOAD`/`DOTNET_STARTUP_HOOKS`/`PATH`/`BASH_ENV` line in a file the plain `duplicati` uid can write | the wrapper's **positive** export allow-list (§7.3.3) + `.env` mode (§7.3.5) |
| `/proc/<serverpid>/environ` → the settings key | same uid reads the server's environ | the secret-provider channel (§7.3.5), which keeps the key out of the environment entirely |
| readable DB + key → JWT → API → run-script | mint a signin token from the database, then set `--run-script-before` | UI credential hygiene + `--webservice-disable-signin-tokens` (§7.3.6) |
| entry replacement in `/usr/lib/duplicati` | 0755 duplicati-owned directory | P0.5 `chown -R root:root` |""",
)

edit(
    "s732-unit",
    """After=network-online.target local-fs.target
Wants=network-online.target
# The destination and the data folder must be mounted before the server starts, and the
# server stops if either is unmounted (an unmounted destination reads as "everything missing").""",
    """# No network-online.target: this server listens on loopback and its destination is file://,
# so it has no network dependency to order against.
After=local-fs.target
# The destination and the data folder must be mounted before the server starts, and the
# server stops if either is unmounted (an unmounted destination reads as "everything missing").""",
)

edit(
    "s732-unit-hardening",
    """ExecStart=/usr/local/lib/duplicati/duplicati-wrapper.bash $DAEMON_OPTS
Restart=on-failure
RestartSec=30s
# Read the whole backup Source without running as root.
AmbientCapabilities=CAP_DAC_READ_SEARCH
CapabilityBoundingSet=CAP_DAC_READ_SEARCH
NoNewPrivileges=yes
# Confinement. ReadWritePaths= punches the data folder, the tempdir and the destination
# through ProtectSystem=strict and ProtectHome=read-only (man systemd.exec: nest
# ReadWritePaths= inside read-only paths to provide writable subdirectories).
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/duplicati /mnt/Backups/Ubuntu/Dropbox/Backups
PrivateTmp=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictSUIDSGID=yes
LockPersonality=yes
RestrictRealtime=yes
SystemCallArchitectures=native""",
    """ExecStart=/usr/local/lib/duplicati/duplicati-wrapper.bash $DAEMON_OPTS
# on-failure, not the vendor's always: a clean exit 0 is the server being told to stop, and
# restarting it would fight the operator. A one-shot exit must not loop.
Restart=on-failure
RestartSec=30s
# Read the whole backup Source without running as root. NOTE (D-4): this bypasses every read
# and search check on the HOST, not only under /home/pcalnon -- see the residual in 7.1 p.3.
AmbientCapabilities=CAP_DAC_READ_SEARCH
CapabilityBoundingSet=CAP_DAC_READ_SEARCH
NoNewPrivileges=yes
# Confinement. ReadWritePaths= punches the data folder, the tempdir and the destination
# through ProtectSystem=strict and ProtectHome=read-only (man systemd.exec: nest
# ReadWritePaths= inside read-only paths to provide writable subdirectories).
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/duplicati /mnt/Backups/Ubuntu/Dropbox/Backups
PrivateTmp=yes
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectControlGroups=yes
RestrictSUIDSGID=yes
LockPersonality=yes
RestrictRealtime=yes
SystemCallArchitectures=native
# --- Confinement added by consensus round 1, Lane B3 (F-1, F-2). Without these the
# --- capability above is paired with an unrestricted exfiltration channel.
# No egress: the destination is file:// and Dropbox is a separate daemon, so the only
# legitimate network use is the update check and usage reporting, both disabled below.
IPAddressDeny=any
IPAddressAllow=localhost
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
# @system-service excludes @privileged, which is where open_by_handle_at(2) lives.
# CAP_DAC_READ_SEARCH explicitly grants that call, and it opens ANY inode of a mounted
# filesystem by handle -- bypassing InaccessiblePaths= and TemporaryFileSystem= entirely.
# Path masking without a syscall filter is therefore not a boundary at all.
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM
ProtectProc=invisible
ProcSubset=pid
PrivateDevices=yes
ProtectClock=yes
ProtectHostname=yes
ProtectKernelLogs=yes
RestrictNamespaces=yes
InaccessiblePaths=-/etc/shadow -/etc/gshadow -/etc/ssh -/etc/credstore.encrypted -/var/lib/docker -/var/log -/root
Environment=DUPLICATI__DISABLE_UPDATE_CHECK=true
Environment=DUPLICATI__USAGE_REPORTER_LEVEL=none""",
)

edit(
    "s732-notes",
    """Notes: `PrivateTmp=yes` gives the server a private `/tmp` that is still `tmpfs`; the job's `--tempdir` therefore moves to `/home/duplicati/.cache/duplicati-tmp` (ext4, inside `ReadWritePaths`). The old tempdir `/home/pcalnon/.cache/duplicati-tmp` is read-only to the service under `ProtectHome=read-only`, which is what we want — it was a root-era choice. `RequiresMountsFor=` also orders the unit after `mnt-Backups.mount`.""",
    """Notes: `PrivateTmp=yes` gives the server a private `/tmp` that is still `tmpfs`; the job's `--tempdir` therefore moves to `/home/duplicati/.cache/duplicati-tmp` (ext4, inside `ReadWritePaths`). The old tempdir `/home/pcalnon/.cache/duplicati-tmp` is read-only to the service under `ProtectHome=read-only`, which is what we want — it was a root-era choice. `RequiresMountsFor=` also orders the unit after `mnt-Backups.mount`.

`/etc/credstore` is deliberately **absent** from `InaccessiblePaths=` — `LoadCredential=` must be able
to read the key from it, and masking it would break the start. That is not a gap that masking could close
anyway: with `CAP_DAC_READ_SEARCH` the service can read `/etc/credstore/*` directly, and
`LoadCredentialEncrypted=` would not help, because this host has no usable TPM2
(`systemd-analyze has-tpm2`: partial, no firmware/driver) and no `/var/lib/systemd/credential.secret`, so an
encrypted credential would bind to a host key readable with the same capability. The credentials directory is
also readable by every process in the unit, run-scripts included (`man systemd.exec`). Record it as a
residual; the fix that actually removes it is the secret-provider channel (§7.3.5), which never puts the key
on disk in a form the service can re-read.

**None of the confinement directives above has been executed against 2.4.0.0 on this host.** That is
open item O-3, and AC-12 is what closes it: the server must complete a full backup under this exact set,
and any directive it cannot run under is removed **and recorded**, never silently dropped. Run it first
with `systemd-run` against the P0 probe copy, not against the live service.""",
)

# =====================================================================================
# §7.3.3 — wrapper
# =====================================================================================

edit(
    "s733-addopt",
    """add_opt() {
    # add_opt <source-label> <word>
    local src="$1" word="$2" name
    is_option "${word}" || die "${src}: not a Duplicati option: '${word}'"
    name="${word%%=*}\"""",
    """add_opt() {
    # add_opt <source-label> <word>
    # The rejection message prints the option NAME and the value's LENGTH, never the value:
    # a mistyped --webservice-password=<secret> line in .env must not reach the journal
    # through the fail-closed path. (Lane B3 F-5.)
    local src="$1" word="$2" name
    if ! is_option "${word}"; then
        die "${src}: not a Duplicati option: '${word%%=*}' (value length ${#word})"
    fi
    name="${word%%=*}\"""",
)

edit(
    "s733-header-note",
    """# No eval. No word-splitting of file content. No secret value is ever printed.
set -euo pipefail""",
    """# No eval. No word-splitting of file content. No secret value is ever printed -- including by
# the error paths, which print an option's NAME and its value's LENGTH only.
#
# Unknown options: this wrapper does NOT validate option names against the server's own list.
# A --option line in .env that the server does not know is passed through, and 2.4.0.0 exits
# on an unrecognised server option rather than ignoring it -- so a typo in .env is a start
# failure, not a silent misconfiguration. That is the intended direction (fail closed), but it
# means .env is part of the start path and a bad line takes the service down: change it with
# --print-command first. (Lane B2 C6.)
set -euo pipefail""",
)

# =====================================================================================
# §7.3.4 — installer
# =====================================================================================

edit(
    "s734-installer",
    """WRAPPER_SRC="${REPO_DIR}/scripts/duplicati-wrapper.bash"
UNIT_SRC="${REPO_DIR}/util/systemd/duplicati.service"
DEFAULTS_SRC="${REPO_DIR}/util/systemd/duplicati.default"
WRAPPER_DST=/usr/local/lib/duplicati/duplicati-wrapper.bash
UNIT_DST=/etc/systemd/system/duplicati.service
DEFAULTS_DST=/etc/default/duplicati
CRED_DST=/etc/credstore/duplicati-settings-key

[[ "$(id -u)" -eq 0 ]] || { echo "run with sudo" >&2; exit 2; }
for f in "${WRAPPER_SRC}" "${UNIT_SRC}" "${DEFAULTS_SRC}"; do
    [[ -f "${f}" ]] || { echo "missing source: ${f}" >&2; exit 2; }
done
bash -n "${WRAPPER_SRC}"

install -d -m 0755 -o root -g root /usr/local/lib/duplicati
install -d -m 0700 -o root -g root /etc/credstore
install -m 0755 -o root -g root "${WRAPPER_SRC}" "${WRAPPER_DST}"
install -m 0644 -o root -g root "${UNIT_SRC}" "${UNIT_DST}"
install -m 0644 -o root -g root "${DEFAULTS_SRC}" "${DEFAULTS_DST}"

for pair in "${WRAPPER_SRC}:${WRAPPER_DST}" "${UNIT_SRC}:${UNIT_DST}" "${DEFAULTS_SRC}:${DEFAULTS_DST}"; do""",
    """WRAPPER_SRC="${REPO_DIR}/scripts/duplicati-wrapper.bash"
UNIT_SRC="${REPO_DIR}/util/systemd/duplicati.service"
DEFAULTS_SRC="${REPO_DIR}/util/systemd/duplicati.default"
GUARD_SRC="${REPO_DIR}/util/yamaguchi-pre-backup-guard.bash"
WRAPPER_DST=/usr/local/lib/duplicati/duplicati-wrapper.bash
UNIT_DST=/etc/systemd/system/duplicati.service
DEFAULTS_DST=/etc/default/duplicati
GUARD_DST=/usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash
DATA_FOLDER=/home/duplicati/.config/Duplicati
CRED_DST=/etc/credstore/duplicati-settings-key

[[ "$(id -u)" -eq 0 ]] || { echo "run with sudo" >&2; exit 2; }
for f in "${WRAPPER_SRC}" "${UNIT_SRC}" "${DEFAULTS_SRC}" "${GUARD_SRC}"; do
    [[ -f "${f}" ]] || { echo "missing source: ${f}" >&2; exit 2; }
done
bash -n "${WRAPPER_SRC}"
bash -n "${GUARD_SRC}"

install -d -m 0755 -o root -g root /usr/local/lib/duplicati
install -d -m 0700 -o root -g root /etc/credstore
install -m 0755 -o root -g root "${WRAPPER_SRC}" "${WRAPPER_DST}"
install -m 0644 -o root -g root "${UNIT_SRC}" "${UNIT_DST}"
install -m 0644 -o root -g root "${DEFAULTS_SRC}" "${DEFAULTS_DST}"
# The guard is --run-script-before-REQUIRED: a missing file aborts every backup. It must be
# installed by the same script that installs the unit, or the first post-recovery run fails.
install -m 0755 -o root -g root "${GUARD_SRC}" "${GUARD_DST}"

# 2.4.0.0 refuses a pre-existing data folder with any group or other bit, at EVERY start.
install -d -m 0700 -o duplicati -g duplicati "${DATA_FOLDER}"
if [[ "$(stat -c '%U:%a' "${DATA_FOLDER}")" != "duplicati:700" ]]; then
    echo "${DATA_FOLDER} must be duplicati-owned mode 0700 (Duplicati refuses anything else)" >&2
    exit 1
fi

for pair in "${WRAPPER_SRC}:${WRAPPER_DST}" "${UNIT_SRC}:${UNIT_DST}" "${DEFAULTS_SRC}:${DEFAULTS_DST}" "${GUARD_SRC}:${GUARD_DST}"; do""",
)

edit(
    "s734-installer-tail",
    """echo "Next: sudo -u duplicati ${WRAPPER_DST} --print-command  (dry run, no server started)"
echo "      systemctl restart duplicati.service && journalctl -u duplicati.service -n 20"
echo "      systemd-analyze security duplicati.service\"""",
    """echo "Next: sudo -u duplicati ${WRAPPER_DST} --print-command  (dry run, no server started)"
echo "      sudo -u duplicati DUPLICATI__REMOTEURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi \\\\"
echo "           ${GUARD_DST}; echo \\"guard exit=\\$?\\"   (must be 0 BEFORE the job is resumed)"
echo "      systemctl restart duplicati.service && journalctl -u duplicati.service -n 20"
echo "      systemd-analyze security duplicati.service\"""",
)

edit(
    "s734-tail-note",
    """`util/systemd/duplicati.service` and `util/systemd/duplicati.default` are the repository copies of the two files shown in §7.3.2; the install script refuses to run unless they exist.""",
    """`util/systemd/duplicati.service` and `util/systemd/duplicati.default` are the repository copies of the two
files shown in §7.3.2, and `util/yamaguchi-pre-backup-guard.bash` is the repository source of the guard shown
in §7.5; the install script refuses to run unless all four exist. The **shadowing** must be stated because it
is not obvious: the loaded unit today is the vendor file `/usr/lib/systemd/system/duplicati.service`, edited
in place. Installing to `/etc/systemd/system/duplicati.service` **shadows** that file, it does not replace
it — the vendor copy stays on disk with its in-place edits, and a `dpkg` upgrade will rewrite it without
affecting what systemd loads. Anyone debugging this later reads `systemctl show -p FragmentPath`, not the
vendor path.

The T2 lane needs its own installer and does not have one: `util/install_duplicati_timer.bash` installs the
**old** CLI lane's five files by name. §7.8's three user units and two scripts are a P3 deliverable
(`util/install_juniper_backup_timer.bash`), not something the existing script can be pointed at.""",
)

# =====================================================================================
# §7.3.5 / §7.3.6
# =====================================================================================

edit(
    "s735-mode",
    """# file: home/duplicati/.config/Duplicati/.env
# Duplicati server: local overrides. Mode 0600, owner duplicati:duplicati.""",
    """# file: home/duplicati/.config/Duplicati/.env
# Duplicati server: local overrides.
# MODE IS AN OPEN OWNER DECISION (recorded as dissent in the design's section 11):
#   0600 duplicati:duplicati  -- Lane A3 / Lane B2 D15; the service user can rewrite its own
#                                tunables, which is the status quo.
#   0640 root:duplicati       -- Lane B3 F-5, and what this design RECOMMENDS: the wrapper
#                                only ever READS this file, so the service user needs no
#                                write, and a file the plain duplicati uid can write is a
#                                code-injection path into a process holding
#                                CAP_DAC_READ_SEARCH (see the crossings table in 7.3.1).
# Until the owner rules, install it 0640 root:duplicati.""",
)

edit(
    "s735-policy",
    """How Duplicati 2.4.0.0 handles the key (verified from `duplicati-server help` and `Duplicati/Server/Program.cs` `GetDatabaseConnection` by the step-2c agent):""",
    """**The delivery channel matters as much as the key.** The wrapper `export`s `SETTINGS_ENCRYPTION_KEY` and
then `exec`s, so the key sits in the server's environment for its whole lifetime and is inherited by *every*
child — including run-scripts and their children (§7.5). Duplicati's own secret-provider channel avoids that
entirely: `Program.cs`'s `ApplySecretProviderAsync` runs over the server's own options **before** startup, so
`--settings-encryption-key=$settings-key --secret-provider=file://…` resolves in-process, shows only the
`$name` placeholder on argv, and never enters the environment at all. That is the preferred delivery; the
`LoadCredential=` + wrapper-export form below is the fallback, and its residual (the key is readable in
`/proc/<serverpid>/environ` by anything running as `duplicati`) is recorded in §7.3.1's crossings table.

How Duplicati 2.4.0.0 handles the key (verified from `duplicati-server help` and `Duplicati/Server/Program.cs` `GetDatabaseConnection` by the step-2c agent):""",
)

edit(
    "s736-webui",
    """Loopback only (`--webservice-interface=loopback`); a UI password set once with `duplicati-server-util --hosturl http://127.0.0.1:8300/ change-password <new>` (or `--webservice-password-init=<new>` on a single start, which "sets the password only if not already set, and then exits") and stored in `~/.config/duplicati-backup/web-credential` (0600, pcalnon) for the watchdog; `--webservice-allowed-hostnames=localhost` if the record's `allowed-hostnames` setting does not already
cover it. Note that `duplicati-server-util` defaults to port 8200 — every invocation against this server needs `--hosturl`. Remote control and the cloud report URL stay as the owner left them (deferred item).""",
    """**The UI credential is a host-wide read credential, and the design must say so before it says anything
else about it.** Any authenticated API principal can set the job's `--run-script-before` to any path, or
create a job whose Source is `/` — and that script runs as `duplicati`, *inside* the unit, *with*
`CAP_DAC_READ_SEARCH` (`RunScript.cs` starts it via `Process.Start` with the inherited environment; run-script
paths are plain job options with no allow-list). So whoever holds the UI password can read everything the
service can read. It is stored 0600 outside any checkout, it is rotated, and AC-13 pins the job's run-script
option to the design's path so a change is visible.

Loopback only (`--webservice-interface=loopback`), plus `--webservice-allowed-hostnames=localhost` and
`--webservice-disable-signin-tokens` once a password exists (S-6: every start mints a fresh token into
adm-readable logs while the password is still autogenerated).

**Setting the password without putting it on a command line** — the design's own commands violated R-18 here,
in the section that exists to end that exposure:

- `duplicati-server-util … change-password <new>` takes the **new** secret as a positional argument, and
  `--password` takes the existing one the same way; `/proc/*/cmdline` is world-readable. Never use either.
- `--webservice-password-init` is a *Password-type* server option, so it **can** carry its value on argv
  too. It applies only while the password is still `AutogeneratedPassphrase`, exits 102 on success and 103
  otherwise — which means it must never sit in `DAEMON_OPTS`, because `Restart=on-failure` would loop it.
  Run it **once, by hand, with the service stopped**, and feed the value through `--secret-provider`
  (a `$name` placeholder on argv) or `--parameters-file`; the server applies both *before* it reads the init
  value. (`--settings-file` is a `duplicati-server-util` option, not a server one — an earlier reading named
  the wrong file channel.)
- Simplest and recommended: **set the first password in the web UI**, and do every later
  pause/resume/rotate through the in-process client `util/ad-hoc/yamaguchi_server_api.py`, which reads its
  credential from a file (§7.6).

`duplicati-server-util`'s own authentication chain, for the record, because two lanes disagreed about it and
the source settles it (`Duplicati/CommandLine/ServerUtil/Connection.cs` at the 2.4.0.0 tag): a saved refresh
token, else a signin token minted from a server database that is both **readable and decryptable** (`jwt-config`
is an encrypted field, so this needs the settings key too), else `--password`, else
`Utility.ReadSecretFromConsole("Enter server password: ")` — a console prompt **does** exist; `help` simply
does not list it. It also defaults to `--hosturl http://127.0.0.1:8200/` and to
`--server-datafolder=/home/pcalnon/.config/Duplicati/` (the orphaned profile), so every invocation against
this server must name both. The in-process client remains the fix. A recovered database carries the root-era
UI password until it is changed.

Remote control and the cloud report URL stay as the owner left them (deferred item) — but the report URL's
bearer JWT is a secret carried by every database copy (S-8).""",
)

# =====================================================================================
# §7.4 — destination and permissions
# =====================================================================================

edit(
    "s74-model-note",
    """| `_yamaguchi_keys/` | `pcalnon:duplicati` | `0700` and **moved out of the Dropbox root** (S-4) | escrow must not sync to the cloud |""",
    """| `_yamaguchi_keys/` | `pcalnon:duplicati` | `0700`, the `env` file **0600**, and the folder **copied out of the Dropbox root** then deleted from it on owner sign-off (S-4) | escrow must not sync to the cloud, and must not be group-readable by the service user |

**The group-write model above is itself an open owner decision — D-14.** As written it grants
**write and delete** on all 877 volumes to every process running as `pcalnon` (editors, browsers,
package hooks, agent sessions) and — by AC-7's own prerequisite — to the Dropbox daemon. A
cloud-side deletion (a compromised account, a linked phone, another machine) or a local `rm -rf`
therefore propagates *into the local master* and on to T1c. R-8 asks only for **read**. The
alternative is directories `duplicati:duplicati 2750`, files `0640`, `UMask=0027`, existing volumes
chowned to `duplicati`: `pcalnon` and Dropbox read through the group, remote→local writes fail
loudly instead of silently deleting the master, and hand maintenance goes through `sudo -u
duplicati` — which this design has already accepted for the data folder. Note honestly what this
buys: `pcalnon` is root-equivalent on this host (`sudo`, `docker`), so it is protection against
**accident and commodity malware**, not against a deliberate local adversary. D-14 is the owner's
call; the script below implements the R-7/R-8 group-write model as specified, and must be re-run
after a D-14 ruling that changes it.

Two facts to know before running it on a synced tree: `chmod 0660` over ~1,700 files strips an
executable bit Dropbox has already synced, so it produces ~1,700 metadata updates (bandwidth, not
correctness) — run it only when `dropbox status` reads up to date. And ext4's behaviour for
default-ACL creation modes has **not** been verified here: Lane B2's scratch test ran on tmpfs and
showed anomalous setuid/sticky bits on a new subdirectory, so test the `d:g:duplicati:rwX` default
on a scratch directory **on `sda1`** before P2 runs this over the real tree.""",
)

edit(
    "s74-script-escrow",
    """if [[ -d "${ROOT}/_yamaguchi_keys" ]]; then
    chmod 0700 "${ROOT}/_yamaguchi_keys"
    echo "NOTE: ${ROOT}/_yamaguchi_keys is inside the Dropbox root -- move it (design §6 S-4)" >&2
fi""",
    """if [[ -d "${ROOT}/_yamaguchi_keys" ]]; then
    chmod 0700 "${ROOT}/_yamaguchi_keys"
    # The find above set every regular file to 0660; the escrow env must not be group-readable
    # by the service user (design section 6, S-4).
    [[ -e "${ROOT}/_yamaguchi_keys/env" ]] && chmod 0600 "${ROOT}/_yamaguchi_keys/env"
    echo "NOTE: ${ROOT}/_yamaguchi_keys is inside the Dropbox root -- copy it out (design §6 S-4)" >&2
fi""",
)

# =====================================================================================
# §7.5 — job, replica, guard
# =====================================================================================

edit(
    "s75-aes",
    """Job settings are the certified ones (R-16) with three changes: `--tempdir=/home/duplicati/.cache/duplicati-tmp`; `--run-script-before-required=/usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash`; `TargetURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi`. Everything else""",
    """Job settings are the certified ones (R-16) with **four** changes: `--tempdir=/home/duplicati/.cache/duplicati-tmp`; `--run-script-before-required=/usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash`; `TargetURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi`; and **`--aes-version` pinned explicitly**. The fourth is new and is not cosmetic: the existing 877 volumes are AES Crypt **v2** (newest dlist header bytes `41455302`), whose KDF is the legacy
iterated SHA-256, while 2.4.0.0 defaults to `--aes-version=3` (PBKDF2, `--aes-v3-iterations` 300000). Left unpinned, the first post-recovery run silently changes the on-disk format mid-set. Pin **2** to keep the set homogeneous, or pin 3 and accept a mixed set — in which case AC-4 must drill one pre- and one post-upgrade fileset. This only matters if `PASSPHRASE` is not random: with 32 random characters both KDFs are irrelevant, with a human phrase v2 is GPU-crackable. Record the
passphrase's provenance (generator and length) with the decision. Everything else""",
)

edit(
    "s75-rules-tail",
    """5. Restore from the cloud copy: download `Yamaguchi/` to a scratch directory on a disk with ~250 GB free and run `duplicati-cli restore file:///<scratch>/Yamaguchi <pattern> --passphrase=<PASSPHRASE> --restore-path=<dir> --dbpath=<new-temp-db>` (local blocks are off by default in 2.4.0.0; never add `--restore-with-local-blocks`); the passphrase comes from escrow, never from the same cloud account (S-4).""",
    """5. Restore from the cloud copy: download `Yamaguchi/` to a scratch directory on a disk with ~250 GB free and run `duplicati-cli restore file:///<scratch>/Yamaguchi <pattern> --restore-path=<dir> --dbpath=<new-temp-db>` with the passphrase supplied through the environment (`PASSPHRASE`, sourced from a 0600 file in a subshell), **never** as `--passphrase=` on argv (local blocks are off by default in 2.4.0.0; never add `--restore-with-local-blocks`); the passphrase comes
   from escrow, never from the same cloud account (S-4).
6. **Write access to `Yamaguchi/` is a backup denial-of-service, not only a correctness risk.** Anyone who can write there — the Dropbox account, any linked device, any `pcalnon` process under the current group model — drops one file and the guard exits 5: no backup runs until a human removes it, and nothing notices for up to 26 h (the watchdog's staleness rule). D-14's read-only model removes the `pcalnon`/Dropbox half of that. Note also that the guard's stray-file check
   *duplicates* a check Duplicati already performs — a foreign file aborts the operation either way, and a file named `duplicati-*.dblock.zip.aes` passes the guard and is caught by Duplicati instead. The guard's real value is the **mount** and **`TargetURL`** checks, which Duplicati does not make.
7. **Cloud→local is a threat direction this design otherwise ignores.** Dropbox version history and Rewind are the *only* recovery from a mass delete of T1 and T1c together, which makes them a design item, not a footnote — and their corollary is that deleted ciphertext stays server-side restorable for the retention window (30 days on Basic/Plus/Family, 180 on Professional), so a "new set under a new passphrase" (D-2) must also **delete-forever** the old one. Retention and
   2FA state are owner observations (D-13's neighbours); this design records that Rewind was **not** evaluated and that Lane B3 dissents from leaving it that way (§11).""",
)

edit(
    "s75-guard-head",
    """set -euo pipefail
trap 'exit 5' ERR

DEST_MOUNT="${YAMAGUCHI_DEST_MOUNT:-/mnt/Backups}\"""",
    """set -euo pipefail
trap 'exit 5' ERR

# Duplicati's RunScript exports EVERY job option into this script's environment, unfiltered and
# prefixed DUPLICATI__ -- the job passphrase among them -- and the wrapper's exported settings
# key is inherited too. Both would then pass to every child (mountpoint, find, id). Drop them
# before anything else runs. (Lane B3 F-4.)
unset DUPLICATI__passphrase SETTINGS_ENCRYPTION_KEY
# STDOUT IS NOT A LOG. Duplicati parses a run-script's stdout as OPTION OVERRIDES
# (--option=value lines change the running job). Every message below goes to stderr; never
# add an echo to stdout, and never set -x.

DEST_MOUNT="${YAMAGUCHI_DEST_MOUNT:-/mnt/Backups}\"""",
)

edit(
    "s75-guard-stray",
    """stray="$(find "${DEST_DIR}" -mindepth 1 -maxdepth 1 \\
    ! -name 'duplicati-*.dblock.zip.aes' \\
    ! -name 'duplicati-*.dindex.zip.aes' \\
    ! -name 'duplicati-*.dlist.zip.aes' \\
    -print -quit)\"""",
    """# duplicati-verification.json is allow-listed: the job does not set
# --upload-verification-file today, so the file is not written -- but enabling that option
# later would otherwise make this guard refuse every run. (Lane B2 D19.)
stray="$(find "${DEST_DIR}" -mindepth 1 -maxdepth 1 \\
    ! -name 'duplicati-*.dblock.zip.aes' \\
    ! -name 'duplicati-*.dindex.zip.aes' \\
    ! -name 'duplicati-*.dlist.zip.aes' \\
    ! -name 'duplicati-verification.json' \\
    -print -quit)\"""",
)

edit(
    "s75-contract",
    """`DUPLICATI__LOCALPATH`, `DUPLICATI__EVENTNAME`, `DUPLICATI__PARSED_RESULT` and `DUPLICATI__RESULTFILE`. `--run-script-timeout` defaults to 60 s; the guard above finishes in well under a second.""",
    """`DUPLICATI__LOCALPATH`, `DUPLICATI__EVENTNAME`, `DUPLICATI__PARSED_RESULT` and `DUPLICATI__RESULTFILE` — but the set is **not** limited to those: `RunScript.cs` exports every job option (`foreach (kv in options) psi.EnvironmentVariables["DUPLICATI__" + …] = kv.Value`), which is why the guard's first statement unsets the two that are secrets. The vendor's own `/usr/lib/duplicati/run-script-example.sh` says the same at its line 75, and at line 85 documents the other half:
**a run-script's stdout is read back as option overrides.** `--run-script-timeout` defaults to 60 s; the guard above finishes in well under a second.

Two properties of the guard as written, stated so nobody has to re-derive them: the `TargetURL` comparison is
an exact match against `file://${DEST_DIR}`, so it **fails closed** on a trailing slash or a query-string
variant (acceptable, and deliberate); and `find -P … -maxdepth 1` does not follow symlinks, so a symlinked
stray is reported, not traversed. The stray file's *name* reaches the job log through stderr, so a
deliberately named file can inject newlines into that log — a nuisance, not a vulnerability, and open item
O-11 asks whether `SendStdOutToLogs` stores it verbatim.""",
)

# =====================================================================================
# §7.6 / §7.7 / §7.8 / §7.11
# =====================================================================================

edit(
    "s76-alerting",
    """- **Service level**: `OnFailure=duplicati-failure.service` is added to `duplicati.service` once a reporter exists for the system scope (the user-lane reporter `util/duplicati_backup_failure.bash` is the template; it writes a durable record first and notifies second).
- **Watchdog** (`util/ad-hoc/yamaguchi_watchdog.py`, user timer 12:00): read the UI credential from `~/.config/duplicati-backup/web-credential` (a file the operator rotates, instead of the primary checkout's `.env`); add the `ProgramState`/`SchedulerQueueIds` check from YAM §8.22 (`Paused` with a non-empty queue = fault); anchor freshness on the newest **Backup** operation, not any operation; add a Dropbox check (`dropbox filestatus` of the newest dlist must read `up to
  date` within 24 h); keep the 26 h staleness rule and the desktop notification as best-effort.
- **Deployment**: the watchdog unit keeps executing the primary checkout's script until the arc's own item (`HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §1.6) converts it to an installed copy; that conversion belongs to P2.""",
    """- **Service level**: `OnFailure=duplicati-failure.service` is added to `duplicati.service` once a reporter exists for the system scope (the user-lane reporter `util/duplicati_backup_failure.bash` is the template; it writes a durable record first and notifies second).
- **Watchdog** (`util/ad-hoc/yamaguchi_watchdog.py`, user timer 12:00): read the UI credential from `~/.config/duplicati-backup/web-credential` (a file the operator rotates, instead of the primary checkout's `.env`); add the `ProgramState`/`SchedulerQueueIds` check from YAM §8.22 (`Paused` with a non-empty queue = fault); anchor freshness on the newest **Backup** operation, not any operation; add a Dropbox check (`dropbox filestatus` of the newest dlist must read `up to
  date` within 24 h); keep the 26 h staleness rule and the desktop notification as best-effort.
- **One credential path, in both clients, in the same PR.** `util/ad-hoc/yamaguchi_server_api.py:41` hard-codes `CRED_FILE` to the primary checkout's `.env`, and `util/ad-hoc/duplicati_api.py`'s `PW_FILE` defaults to the same file; `util/ad-hoc/yamaguchi_reboot_verify.bash:73` calls the first and the census goes through the second. Re-pointing only one of them leaves every acceptance instrument 401-ing after the password rotates — which is exactly today's watchdog symptom.
  Both move to `~/.config/duplicati-backup/web-credential`, and P0 is ordered so that file exists **before** AC-2 runs.
- **The deployed watchdog unit takes no `--backup-id`**, so it uses the client's default of 2. If recovery assigns the job a different id (Procedure B always does — `sqlite_sequence` starts at 1), the unit must be redeployed with `--backup-id <id>` or it alerts `JOB_MISSING` forever.
- **Deployment**: the watchdog unit keeps executing the primary checkout's script until the arc's own item (`HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §1.6) converts it to an installed copy; that conversion belongs to P2 — with the same integrity argument as the snapshot timer in §7.7.""",
)

edit(
    "s77-snapshot",
    """`util/ad-hoc/yamaguchi_server_db_snapshot.py` keeps `SRC = /usr/lib/duplicati/data/Duplicati-server.sqlite`. After recovery it must read `/home/duplicati/.config/Duplicati/Duplicati-server.sqlite`. The unit can then run as `duplicati` instead of root (group read is enough for `sqlite3.backup()`; the destination `~/.local/state/duplicati-server-db/` needs a group-writable directory or the unit keeps root only for the `chown`). Its docstring lines 20 and 36 ("the encrypted
passphrase") are corrected to state the actual condition: encrypted only when the settings key is in force (D-1).""",
    """`util/ad-hoc/yamaguchi_server_db_snapshot.py` keeps `SRC = /usr/lib/duplicati/data/Duplicati-server.sqlite`.
After recovery it must read `/home/duplicati/.config/Duplicati/Duplicati-server.sqlite`. Its docstring lines
20 and 36 ("the encrypted passphrase") are corrected to state the actual condition: encrypted only when the
settings key is in force (D-1).

**The unit cannot simply become `User=duplicati`.** `/home/pcalnon/.local/state` is mode **0700**, so the
`duplicati` user cannot traverse to the snapshot destination however the leaf directory is chmod'ed — and the
design's own data-folder rule forbids group bits on the source side too. Two workable shapes: keep the unit
**root** on the new path (simplest, and what P2 does), or have root create a `2770 root:duplicati` staging
directory *inside* the backup source and let a `duplicati`-owned unit write there. Say which in the unit;
do not leave "the unit can then run as duplicati" standing, because it cannot.

**It is also a daily pcalnon→root code path, and that is the more urgent half.**
`/etc/systemd/system/yamaguchi-server-db-snapshot.service` runs as root with
`ExecStart=/usr/bin/python3 /home/pcalnon/…/util/ad-hoc/yamaguchi_server_db_snapshot.py`, so `sys.path[0]` is
a pcalnon-writable directory and every agent that switches a branch in the primary checkout changes what root
executes at 13:45 UTC. Fix it in **P0.5**, not P2: a root-owned installed copy under
`/usr/local/lib/duplicati/`, `ProtectSystem=strict`. The watchdog user unit has the same shape (integrity
only, since it already runs as `pcalnon`).""",
)

edit(
    "s78-path-unit",
    """```ini
# file: home/pcalnon/.config/systemd/user/juniper-backup.path
[Unit]
Description=Run the Juniper USB archive when a configured drive is mounted and a run is due

[Path]
PathExists=/run/media/pcalnon/EBC5-F0A3/Juniper-8.0.0.python
PathExists=/run/media/pcalnon/DFF3-2782/Juniper-8.0.0.python
Unit=juniper-backup.service

[Install]
WantedBy=default.target
```""",
    """**`PathExists=` cannot be used here, and this is the defect `systemd-analyze verify` cannot see.**
`systemd.path(5)` on this host (systemd 259), in the paragraph at lines 30–36: *"When a service unit triggered
by a path unit terminates (regardless whether it exited successfully or failed), monitored paths are checked
immediately again, and the service accordingly restarted instantly"* — and it exempts nothing. A `SKIPPED`
exit 0 therefore re-triggers at once and loops until the service start-rate limit trips, at which point
*"the error condition … is propagated … to the path unit and causes the path unit to fail as well, thus losing
the monitoring"*. The mount-detection lane would be dead seconds after the first plug-in, and again after
every login with a drive attached.

`PathChanged=` is the fix, and the man page is **not** where that is settled: its
"does not apply to `PathChanged=`/`PathModified=`" sentence (lines 96–97) is about *immediate activation when
the path already exists at unit activation*, a different paragraph — conflating the two is how an earlier
reading got this wrong in both directions. The behaviour on *termination* lives in systemd's `path.c`, and at
v259 it reads `good = !initial && !from_trigger_notify && b != s->previous_exists` for `PATH_CHANGED` and
`PATH_MODIFIED`, with `path_trigger_notify_impl` re-checking under `from_trigger_notify=true`. So
`PathChanged=` does **not** re-trigger on termination: the fix below is sound at v259, and a udev
`ENV{SYSTEMD_USER_WANTS}` rule on the two UUIDs is an alternative, not a requirement.

Test it rather than trusting it: plug a stamped drive and watch `systemctl --user status juniper-backup.path`
for 30 s. (`/run/media/pcalnon` exists — `root:root` 0750 with an ACL, currently empty.)

```ini
# file: home/pcalnon/.config/systemd/user/juniper-backup.path
[Unit]
Description=Run the Juniper USB archive when a configured drive is mounted and a run is due

[Path]
# PathChanged=, never PathExists=: a PathExists= oneshot re-triggers after EVERY termination
# (systemd.path(5)), so a "nothing due" exit 0 loops into the start-rate limit and the path
# unit itself then fails, losing the monitoring. Verified against systemd v259 path.c.
PathChanged=/run/media/pcalnon
Unit=juniper-backup.service

[Install]
WantedBy=default.target
```""",
)

edit(
    "s78-service-onfailure",
    """```ini
# file: home/pcalnon/.config/systemd/user/juniper-backup.service
[Unit]
Description=Juniper per-repo archive to attached USB drives
OnFailure=duplicati-backup-failure.service""",
    """The failure reporter must be a **new** unit. `duplicati-backup-failure.service` exists, but its `ExecStart`
is `duplicati-backup-failure.bash duplicati-backup.service` — it journal-tails the *disabled CLI lane* and
writes a `failures.log` record naming the wrong unit, so pointing T2's `OnFailure=` at it produces a report
about a lane that is not running. P3 adds `juniper-backup-failure.service`, whose reporter takes the unit name
as `$1` (defaulting to `duplicati-backup.service` so the existing lane is unaffected).

```ini
# file: home/pcalnon/.config/systemd/user/juniper-backup.service
[Unit]
Description=Juniper per-repo archive to attached USB drives
OnFailure=juniper-backup-failure.service""",
)

edit(
    "s78-install",
    """Installation follows `util/install_duplicati_timer.bash`: copies of the runner and scheduler into `~/.local/bin/`, the three units into `~/.config/systemd/user/`, `systemctl --user daemon-reload`, then `systemctl --user enable --now juniper-backup.timer juniper-backup.path`. Retention on the drives (every run mints a new UUID set; nothing prunes; ~135 GiB / ~67 GiB free per `HANDOFF_2026-08-27_backup-per-repo-review-and-arc-tail.md` §7) is D-10.""",
    """Installation follows the *pattern* of `util/install_duplicati_timer.bash` but needs its own script —
`util/install_juniper_backup_timer.bash`, a P3 deliverable — because the existing one installs the **old**
lane's five files by name. It copies the runner and scheduler into `~/.local/bin/`, the four units
(timer, path, service, failure) into `~/.config/systemd/user/`, runs `systemctl --user daemon-reload`, then
`systemctl --user enable --now juniper-backup.timer juniper-backup.path`.

**The scheduler and the runner must read one mount-root setting, and the runner must be fixed first.**
`util/juniper-backup.bash` still forces `/media/pcalnon/<name>` (lines 122–124, 303–305, 329) and has skipped
both drives since 2026-09-07 (§4.5), while the scheduler above defaults `MEDIA_ROOT=/run/media/${USER}`. Until
the runner changes, every "due" run the scheduler starts ends `FAILED runner rc=1` — so P3 cannot produce the
"one OK (plugged) run" it asks for until the runner's mount root is fixed. P3 is ordered accordingly.

Retention on the drives (every run mints a new UUID set; nothing prunes; ~135 GiB / ~67 GiB free per
`HANDOFF_2026-08-27_backup-per-repo-review-and-arc-tail.md` §7) is D-10.""",
)

edit(
    "s711-retire",
    """`/usr/lib/duplicati/data/` (archive a copy, then remove, once AC-1…AC-4 pass); `/home/duplicati/.config/Duplicati/{temp,temp1,backups}` (57 GB of copied pcalnon job databases — the originals in the pcalnon profile stay under the record's KEEP list); `Duplicati-OLE/` (unreadable to the investigators — owner to inspect); the disabled user CLI lane (the record's own removal item); the `.env` comment block; the wrapper's header comment.""",
    """`/usr/lib/duplicati/data/` (archive a copy, then remove, once AC-1…AC-4 pass); `/home/duplicati/.config/Duplicati/{temp,temp1,backups}` (56 GiB of copied pcalnon job databases — the originals in the pcalnon profile stay under the record's KEEP list); `Duplicati-OLE/` (unreadable to the investigators — owner to inspect); the disabled user CLI lane (the record's own removal item); the `.env` comment block; the wrapper's header comment; `/home/duplicati/bin/` entirely
(it holds only the symlink D-6 replaces with an installed copy — a "fallback" symlink into a developer checkout should not exist); and **`/mnt/Backups/Ubuntu/.dropbox-dist`**, a second, unused Dropbox client (270.4.3312) owned `duplicati:duplicati` that nothing runs — the live daemons are pcalnon's.""",
)

edit(
    "s735-rekey-pointer",
    """That two-start sequence is the re-key procedure in §8 P1.""",
    """That two-start sequence is the re-key procedure, and it runs in **§8 P0.5**, not P1 — the currently
  installed key is public (S-1's successor is the passphrase itself, S-2), so leaving it live "for a week"
  means a week in which the daily snapshot and every recovery copy are decryptable by anyone with the
  repository or the journal. Stop the snapshot timer for the duration: between the two starts every field is
  cleartext on disk, and a 13:45 UTC snapshot landing in that window puts the passphrase in cleartext into
  `~/.local/state` and into the next fileset. Afterwards, with the server stopped, run
  `PRAGMA wal_checkpoint(TRUNCATE); VACUUM;` — the decrypted values otherwise survive in free pages and the
  WAL — and delete the `-<ts>.bak` copy the database tool leaves beside any wiped database.""",
)

# =====================================================================================
# §8 — remediation plan
# =====================================================================================

edit(
    "s8-stop-block",
    """> **STOP — this runbook is not yet reconciled with consensus round 1 (2026-09-21) and must not be executed from this revision.** The validators' verbatim reports are in `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`. What they established about the steps below, in the order an operator would hit it:
>
> - **P0 step 3 (Procedure A) is refuted twice.** Lane B1 tested every named candidate offline — an `enc-v1:` field carries the SHA-256 of its key, so a candidate can be checked against a database copy without a server (`util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py`) — and **none matches**: neither the committed 36-character literal (with eleven shell-mangling variants) nor the backup passphrase encrypted the root database on 09-18. The §5.4 candidate order is therefore wrong, and the probe
> script as written can report `KEY ACCEPTED` for a wrong key (it copies the main file without its `-wal`, and a copy whose fields are not yet encrypted is re-encrypted under whatever key it is started with).
> - **A cheaper, key-free recovery exists and is missing (Procedure A0).** The daily snapshot lane copies the root server database into `~/.local/state/duplicati-server-db/`, which sits inside the backup source and is not covered by any filter; the root database was unencrypted until 09-18 20:42. The 09-17 and 09-18 14:00Z filesets therefore each hold a cleartext schema-11 server database. Restoring that one file from `duplicati-20260918T140000Z` with the escrowed passphrase needs no key, no wipe and no
> re-entry (Lane B1 finding 3).
> - **Procedures A0, A, A2 and B all leave `DBPath` absolute at `/usr/lib/duplicati/data/BMXWPAOGLP.sqlite`**, a folder the §7.3.2 unit makes read-only and P4 deletes; the first backup fails and the index is lost unless the index file is moved into the new data folder and the row re-pointed first (Lane B1 finding 4).
> - **P0 steps 3, 5, 7 and 9 put secrets on a command line** (`printf '%s' '<value>'` in step 3; `duplicati-server-util --password …` and `change-password <new>` in steps 5, 7 and 9 — Lane B2 defects D7 and D5), violating R-18 inside the section written to end that exposure. Step 5's re-entry of the target URL and passphrase names no tool (D9); step 6's rebuilt job will not be id 2, which the watchdog, census and AC-2/AC-5 assume (D10); AC-2 runs before the credential it needs exists (D11); step 3's copy
> omits the `-wal` (D6, see the first bullet) and step 4's "first start only" re-creates the 09-18 failure on the next restart (D8). Step 5's `duplicati-database-tool wipe-encryption` is correct as written: the subcommand's own `help` shows `--server-datafolder <dir>` (default `$HOME/.config/Duplicati`, i.e. the pcalnon profile when run as pcalnon — always name the copy's folder).
> - **The §7.8 `.path` unit is self-defeating** (`PathExists=` re-triggers after every termination, so a "nothing due" exit loops into the start-rate limit and the path unit fails); `OnFailure=` names the old lane's reporter; P3 step 1 cannot produce the "OK run" it expects before step 2 fixes the runner's mount root (Lane B2 defects D1–D3).
>
> None of this changes §5's three root-cause legs, which survived all six lanes; it changes how the job is recovered.

Phases are ordered; nothing in a later phase is a precondition of an earlier one. Every destructive step is preceded by a copy. **Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved by any step below**, and the pcalnon profile directory is not modified.""",
    """Phases are ordered; nothing in a later phase is a precondition of an earlier one — **but that is true of
phases, not of decisions**: P0 applies the recommendations of D-1 (credstore + `--require-db-encryption-key`),
D-4 (`AmbientCapabilities`), D-6 (installed copy) and D-9 (loopback) before the owner has ruled on any of
them. Either rule those four first, or accept that P0 applies them **provisionally** and a contrary ruling
means re-installing the unit. Step 0 makes that explicit.

Every destructive step is preceded by a copy. **Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved by
any step below, with exactly one exception, and it needs owner sign-off**: the passphrase escrow copy at
`…/Dropbox/Backups/_yamaguchi_keys/`, which P1 step 4 first **copies** to a sibling outside the Dropbox root
and only then deletes from the synced tree (S-4). The earlier revision of this preamble stated the rule
without the exception while P1 step 4 performed it — a contradiction inside one document. The pcalnon profile
directory is not modified by anything here.""",
)

edit(
    "s8-p0-steps",
    """### P0 — freeze and recover the job (target: same day)

1. **Freeze evidence.** `sudo cp -a /usr/lib/duplicati/data /home/duplicati/.cache/root-data-folder-2026-09-21` and `cp -p ~/.local/state/duplicati-server-db/Duplicati-server.sqlite ~/.local/state/duplicati-server-db/Duplicati-server.sqlite.2026-09-21-recovery`. Verify sizes match.
2. **Stop the empty server**: `sudo systemctl stop duplicati.service` (stop, not restart — the armed `ExecStart` cannot start the server correctly, §4.3 item 9). Move the fresh, empty data folder aside: `sudo mv /home/duplicati/.config/Duplicati /home/duplicati/.config/Duplicati.empty-2026-09-20`.
3. **Procedure A — identify the 09-18 key on a copy.** For each candidate (§5.4 order), as root:""",
    """### P0 — freeze and recover the job (target: same day)

**0. Owner gates — none of these is a session's to decide.** (a) Rule D-1, D-4, D-6, D-9, or record that P0
applies their recommendations provisionally. (b) Have the escrowed `PASSPHRASE` to hand, from the printed
sheet or the password manager — **not** from the Dropbox-synced copy, which is the thing S-4 is about. (c)
Confirm Procedure A0's premise with one read-only command, in a subshell so nothing reaches the shell history
and the passphrase never touches argv:

```bash
# file: util/ad-hoc/2026-09-22_confirm_a0_premise.bash
#!/usr/bin/env bash
# Confirm that the 2026-09-18 fileset carries the server-DB snapshot Procedure A0 restores.
# Read-only: lists one path inside one fileset. Never writes to the destination.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-22
# Status:     ad-hoc -- recovery
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md §8 P0
set -euo pipefail
ENV_FILE="${YAMAGUCHI_ENV_FILE:-${HOME}/.config/duplicati-backup/env}"
DEST="${YAMAGUCHI_DEST_URL:-file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi}"
TMPDB="$(mktemp -u "${TMPDIR:-/tmp}/a0-probe-XXXXXX.sqlite")"
[[ -r "${ENV_FILE}" ]] || { echo "no readable env file at ${ENV_FILE}" >&2; exit 2; }
# PASSPHRASE reaches duplicati-cli through the ENVIRONMENT, never through argv.
(
    set -a
    # shellcheck source=/dev/null
    . "${ENV_FILE}"
    set +a
    duplicati-cli list "${DEST}" --version=0 --no-local-db=true \\
        "--dbpath=${TMPDB}" '*duplicati-server-db*'
)
rm -f "${TMPDB}"
```

The 09-18 14:00Z fileset **is** version 0 (it is the newest), which is why `--version=0` is used rather than
a `--time=` string whose parsing would be one more thing to get wrong. Expect the snapshot path
`home/pcalnon/.local/state/duplicati-server-db/Duplicati-server.sqlite` in the listing. If it is absent, A0
is out and the decision tree starts at step 3.

1. **Freeze evidence.** `sudo cp -a /usr/lib/duplicati/data /home/duplicati/.cache/root-data-folder-2026-09-22`, and copy the snapshot aside **before anything else touches it** — `cp -p ~/.local/state/duplicati-server-db/Duplicati-server.sqlite ~/.local/state/duplicati-server-db/Duplicati-server.sqlite.recovery-$(date +%F)`. That file is **replaced every day at 13:45 UTC with a new inode**; if the timer fires mid-recovery the file under your hand changes.
   Verify sizes match. While root is available, settle two open questions with one listing each: `sudo ls -la --time-style=full-iso /usr/lib/duplicati/data/` — a `-wal`/`-shm` dated 09-18 21:03 means the main file may still be **cleartext**, a second key-free source (§4.2, §5.4) — and `sudo ls -la /usr/lib/systemd/system/ | grep -i duplicati` for editor backups of the unit.
2. **Stop the empty server**: `sudo systemctl stop duplicati.service` (stop, **never** restart — the armed `ExecStart` cannot start the server correctly and the 0700 gate refuses the 0777 folder regardless, §4.3 item 9). Move the fresh, empty data folder aside: `sudo mv /home/duplicati/.config/Duplicati /home/duplicati/.config/Duplicati.empty-2026-09-20`. Note that this folder is 0777 and 2.4.0.0 would refuse it, so it cannot simply be reused in place.
3. **Choose the procedure — the offline key-hash test is the discriminator, not a server probe.** Every `enc-v1:` value embeds the SHA-256 of its key, so run `util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py` against the **copy** from step 1 (usage in its docstring). It needs no root, no server and no live database, and it has already excluded every candidate this design named (§5.4): the committed literal with eleven shell-mangling variants, both
   passphrases, and the three commented key spellings. **Feed any new candidate ALONE on stdin** — the probe keeps only the last uncommented `SETTINGS_ENCRYPTION_KEY=` line it reads, so a concatenated file silently discards one. Write the candidate with `set +o history; read -rs key; install -m 0600 /dev/stdin <file> <<<"$key"` — **never** `printf '%s' '<value>' > file` at a root prompt, which is the same history channel §6 exists to close.
   If no candidate matches (the expected outcome today), go to **step 4 (A0)**; A0 is preferred over A2 and B even if a key *is* found, because it is the only route that needs no re-entry of anything.

   A server-based probe is **confirmation only**, and only with all four containments below — as written in an earlier revision it could report `KEY ACCEPTED` for a **wrong** key, because it copied the main file without its `-wal` and `Program.cs` re-encrypts a not-yet-encrypted copy under whatever key it is started with, printing `Server has started` either way:""",
)

edit(
    "s8-probe-script",
    """# file: util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash
#!/usr/bin/env bash
# Try ONE candidate settings key against a COPY of the abandoned root data folder's server DB.
# Never touches /usr/lib/duplicati/data or the live service. Run with sudo.
#   sudo bash 2026-09-21_probe_settings_key_on_copy.bash /path/to/file-holding-the-candidate
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-21
# Status:     ad-hoc — migration
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md §8 P0
set -euo pipefail
SRC="${SRC:-/usr/lib/duplicati/data/Duplicati-server.sqlite}"
WORK="${WORK:-/home/duplicati/.cache/keyprobe}"
PORT="${PORT:-8399}"
KEYFILE="${1:?usage: $0 <file-containing-candidate-key>}"
[[ "$(id -u)" -eq 0 ]] || { echo "run with sudo" >&2; exit 2; }
[[ -s "${SRC}" ]] || { echo "source DB missing: ${SRC}" >&2; exit 2; }
rm -rf "${WORK}"; install -d -m 0700 -o duplicati -g duplicati "${WORK}"
cp -p "${SRC}" "${WORK}/Duplicati-server.sqlite"
chown duplicati:duplicati "${WORK}/Duplicati-server.sqlite"
key="$(<"${KEYFILE}")"
[[ -n "${key}" ]] || { echo "candidate file is empty" >&2; exit 2; }
set +e
SETTINGS_ENCRYPTION_KEY="${key}" timeout 45 runuser -u duplicati -- /usr/bin/duplicati-server \\
    "--server-datafolder=${WORK}" --webservice-interface=loopback "--webservice-port=${PORT}" \\
    > "${WORK}/probe.log" 2>&1
set -e
if grep -q 'Server has started' "${WORK}/probe.log"; then
    echo "KEY ACCEPTED (${#key} chars): the copy opened; keep this candidate"
    exit 0
fi
echo "KEY REJECTED (${#key} chars):"; grep -E 'Exception|encrypt|version' "${WORK}/probe.log" | head -5
exit 1
```

   Write each candidate into a `0600` file with `printf '%s' '<value>' > file` (no trailing newline, no shell expansion — single quotes). The 45 s timeout ends the probe server; the job's `startup-delay` setting keeps it paused meanwhile, so it runs nothing.
4. **If a key is accepted (Procedure A)**: `sudo cp -a /usr/lib/duplicati/data /home/duplicati/.config/Duplicati`; `sudo chown -R duplicati:duplicati /home/duplicati/.config/Duplicati`; `chmod 0700` on the folder and `0600` on its files (§7.3.2); write the accepted key to `/etc/credstore/duplicati-settings-key` (0600 root) **for the first start only**; install §7.3 (unit, defaults, wrapper) with `util/install_duplicati_service.bash`; `sudo systemctl start duplicati.service`.
   Expect in the journal: schema upgrade 11→12, `Server has started`. The job appears with its existing index — no Recreate.
5. **If no candidate is accepted (Procedure A2 — wipe, keep everything else)**: on the **copy** made in step 1, run `duplicati-database-tool wipe-encryption <copy>/Duplicati-server.sqlite` (as `duplicati`, `--server-datafolder` pointing at the copy); install the copy as the data folder exactly as in step 4 but with a **new** settings key; start; then re-enter, through the UI or `PUT /api/v1/backup/2`, the two wiped job values —
   `TargetURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi` and the passphrase from `~/.config/duplicati-backup/env` — and set the UI password afresh (`change-password`). Sources, filters, schedule, options and the index path all survive the wipe.
6. **If the data folder itself is unusable (Procedure B — rebuild)**: start the empty server with the §7.3 unit and a **new** settings key; set the UI password; rebuild the job from the 09-20 snapshot — sources, filters, schedule and option names are readable in it (`2026-09-21_duplicati_server_db_forensics.py` prints them; option *values* come from the record: §7.5 list), `TargetURL` as above, passphrase from `~/.config/duplicati-backup/env`
   (`util/ad-hoc/yamaguchi_build_job.py` is the tool that built the job the first time and reads the passphrase in-process; update its defaults before use). Read the new job's assigned `DBPath` (`GET /api/v1/backup/<id>`), stop the server, copy `/usr/lib/duplicati/data/BMXWPAOGLP.sqlite` to that path (`chown duplicati`, `0600`), start, and run **Verify files** for the job before any backup. If verification reports the index inconsistent with the destination, run Repair (this
   index *is* the destination's own, last written 09-18; rule 11 does not apply) or, last resort, Recreate.
7. **Before the first run, whichever procedure**: the job still carries `--tempdir=/home/pcalnon/.cache/duplicati-tmp` (unwritable under the new confinement) and its schedule `Time` is in the past, so it will start on its own once the `startup-delay` pause lapses. Immediately after the server is up: `duplicati-server-util --hosturl http://127.0.0.1:8300/ pause`, then change `--tempdir` to `/home/duplicati/.cache/duplicati-tmp` (create it, 0700 duplicati) and add
   `--run-script-before-required` (§7.5), then `resume`.
8. **Prove it.** `AC-2`, then one backup run (`AC-3`), then a restore drill (`AC-4`).
9. **Re-arm alerting.** Set the UI password, write `~/.config/duplicati-backup/web-credential`, make the watchdog read it; confirm the next 12:00 fire reads `OK`.""",
    """# file: util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash
#!/usr/bin/env bash
# CONFIRMATION ONLY -- the discriminator is the offline hash probe
# (2026-09-21_duplicati_settings_key_hash_probe.py). Try ONE candidate settings key against a
# COPY of the abandoned root data folder's server DB. Never touches /usr/lib/duplicati/data or
# the live service. Run with sudo.
#   sudo bash 2026-09-21_probe_settings_key_on_copy.bash /path/to/file-holding-the-candidate
#
# Four containments, each of which this script lacked in the design's first revision:
#   1. copy the -wal and -shm siblings, not the main file alone: the folder's last writers died
#      on exceptions, so a WAL-mode database left by process death keeps its frames in -wal and
#      a main-file-only copy is an older or torn state;
#   2. assert the copy is ALREADY encrypted before starting anything -- on a copy whose
#      encrypted-fields flag is False, Program.cs's ReWriteAllFieldsIfEncryptionChanged
#      encrypts it under WHATEVER key is supplied and prints "Server has started", i.e. a
#      vacuous pass that also poisons the copy;
#   3. run a NEGATIVE CONTROL first: a random key MUST be rejected, or the test proves nothing;
#   4. neuter the copy before any server touches it -- DELETE FROM Schedule, and confine the
#      probe with systemd-run so it cannot reach the real destination or the real data folder
#      even if a schedule survives.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-21
# Status:     ad-hoc — migration
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md §8 P0
set -euo pipefail
SRCDIR="${SRCDIR:-/usr/lib/duplicati/data}"
WORK="${WORK:-/home/duplicati/.cache/keyprobe}"
PORT="${PORT:-8399}"
KEYFILE="${1:?usage: $0 <file-containing-candidate-key>}"
[[ "$(id -u)" -eq 0 ]] || { echo "run with sudo" >&2; exit 2; }
[[ -s "${SRCDIR}/Duplicati-server.sqlite" ]] || { echo "source DB missing under ${SRCDIR}" >&2; exit 2; }

rm -rf "${WORK}"; install -d -m 0700 -o duplicati -g duplicati "${WORK}"
# (1) main file PLUS its siblings.
for f in Duplicati-server.sqlite Duplicati-server.sqlite-wal Duplicati-server.sqlite-shm; do
    [[ -e "${SRCDIR}/${f}" ]] && cp -p "${SRCDIR}/${f}" "${WORK}/${f}"
done
chown -R duplicati:duplicati "${WORK}"

# (2) the copy must already be encrypted, or a "pass" means nothing.
flag="$(sqlite3 "file:${WORK}/Duplicati-server.sqlite?mode=ro" \\
    "SELECT Value FROM Option WHERE BackupID=-2 AND Name='encrypted-fields';" || true)"
url="$(sqlite3 "file:${WORK}/Duplicati-server.sqlite?mode=ro" \\
    "SELECT substr(TargetURL,1,7) FROM Backup LIMIT 1;" || true)"
if [[ "${flag}" != "True" || "${url}" != "enc-v1:" ]]; then
    echo "REFUSING: copy is not encrypted (encrypted-fields='${flag}', TargetURL prefix='${url}')." >&2
    echo "A probe against an unencrypted copy accepts ANY key and poisons the copy." >&2
    exit 3
fi
# (4) a schedule in the past would otherwise let the probe server start the overdue run.
sqlite3 "${WORK}/Duplicati-server.sqlite" "DELETE FROM Schedule;"

try_key() {
    local key="$1" label="$2" log="${WORK}/probe-${2}.log"
    printf 'probing: %s\\n' "${label}" >&2
    set +e
    SETTINGS_ENCRYPTION_KEY="${key}" timeout -k 10 45 \\
        systemd-run --wait --quiet --collect --pipe \\
            --uid=duplicati \\
            -p InaccessiblePaths=/mnt/Backups \\
            -p InaccessiblePaths="${SRCDIR}" \\
            -p "Environment=SETTINGS_ENCRYPTION_KEY=${key}" \\
            /usr/bin/duplicati-server "--server-datafolder=${WORK}" \\
            --webservice-interface=loopback "--webservice-port=${PORT}" \\
            --webservice-disable-signin-tokens > "${log}" 2>&1
    set -e
    grep -q 'Server has started' "${log}"
}

# (3) negative control.
if try_key "$(head -c 32 /dev/urandom | base64 | tr -d '\\n')" control; then
    echo "REFUSING: a RANDOM key was accepted -- this probe is not discriminating." >&2
    exit 4
fi
echo "negative control rejected the random key (good)"

key="$(<"${KEYFILE}")"
[[ -n "${key}" ]] || { echo "candidate file is empty" >&2; exit 2; }
if try_key "${key}" candidate; then
    echo "KEY ACCEPTED (${#key} chars): the copy opened; keep this candidate"
    exit 0
fi
echo "KEY REJECTED (${#key} chars):"
grep -E 'Exception|encrypt|version' "${WORK}/probe-candidate.log" | head -5
exit 1
```

   The 45 s timeout ends the probe server; the `DELETE FROM Schedule` and the two `InaccessiblePaths=`
   keep it from reaching anything real even so. (`startup-delay` **is** present by name among the server
   settings at `BackupID=-2`, but its *value* is not verifiable without opening the database, so it is not
   relied on — an unverified pause is not a containment.)

4. **Procedure A0 — restore a cleartext copy of the same database from the backup itself. This is the
   preferred route and it needs no settings key at all.** The snapshot lane writes into
   `~/.local/state/duplicati-server-db/`, which is inside the backup Source and matched by none of the 45
   filters (YAM §8.19.3), and the root database was still **unencrypted** through 09-18 20:42:38 (three
   journal lines say so: 09-17 01:31:01, 09-18 20:22:12, 20:42:38). So the 09-17 and 09-18 14:00Z filesets
   each hold a cleartext schema-11 server database carrying `TargetURL`, the passphrase, `DBPath`, the
   schedule, 45 filters and every option. Restore that **one file** to a scratch directory, with a **fresh
   `--dbpath`** so the live index is untouched and with the passphrase delivered through the environment:

```bash
# file: util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash
#!/usr/bin/env bash
# Procedure A0: restore the cleartext server database from the 2026-09-18 fileset.
# Read-only against the destination; writes only into the restore directory given as $1.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-22
# Status:     ad-hoc -- recovery
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md §8 P0
set -euo pipefail
ENV_FILE="${YAMAGUCHI_ENV_FILE:-${HOME}/.config/duplicati-backup/env}"
DEST="${YAMAGUCHI_DEST_URL:-file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi}"
OUT="${1:?usage: $0 <restore-directory>}"
SNAP_PATH='/home/pcalnon/.local/state/duplicati-server-db/Duplicati-server.sqlite'
TMPDB="$(mktemp -u "${TMPDIR:-/tmp}/a0-restore-XXXXXX.sqlite")"
[[ -r "${ENV_FILE}" ]] || { echo "no readable env file at ${ENV_FILE}" >&2; exit 2; }
install -d -m 0700 "${OUT}"
# PASSPHRASE reaches duplicati-cli through the ENVIRONMENT, never through argv.
(
    set -a
    # shellcheck source=/dev/null
    . "${ENV_FILE}"
    set +a
    duplicati-cli restore "${DEST}" "${SNAP_PATH}" \\
        --version=0 --no-local-db=true "--dbpath=${TMPDB}" "--restore-path=${OUT}"
)
rm -f "${TMPDB}"
echo "restored under ${OUT}; verify it with the forensics script before installing it."
```

   Verify the restored file with the forensics script before installing it: 16 server tables, `Version 11`,
   `Backup` id 2 `Yamaguchi`, 2 `Source` rows, 45 `Filter` rows, and a **cleartext** `TargetURL` (no
   `enc-v1:` prefix). Only `LastBackupDate` is one day stale. Then install it as the data folder per step 8.
5. **Procedure A — re-use the whole data folder (only if step 3 found a key).** `sudo cp -a /usr/lib/duplicati/data /home/duplicati/.config/Duplicati`; `sudo chown -R duplicati:duplicati /home/duplicati/.config/Duplicati`; `chmod 0700` on the folder and `0600` on its files (§7.3.2); write the accepted key to `/etc/credstore/duplicati-settings-key` (0600 root) **and leave it there until P0.5's re-key replaces it** — the earlier "for the first start only" would
   re-create the 09-18 `SettingsEncryptionKeyMissingException` loop on the very next restart. Then step 8.
6. **Procedure A2 — wipe the encrypted fields, keep everything else.** On the **copy** from step 1, as the copy's owner, in a 0700 directory:
   `duplicati-database-tool wipe-encryption --server-datafolder <copydir> --dry-run <copydir>/Duplicati-server.sqlite` first (expect `version 11 … Server database … 9 encrypted field(s) would be wiped`), then the same without `--dry-run`. Two traps: `--server-datafolder <dir>` **is** an option of the *subcommand* (`duplicati-database-tool help wipe-encryption`) even though the top-level `help` does not list it, and it defaults to
   `$HOME/.config/Duplicati` — i.e. the orphaned pcalnon profile when run as `pcalnon`, so **always name the copy's folder**; and `--dry-run` is **not read-only** — it flips the copy's header to WAL mode and changes its sha256, so hash the copy before, or re-copy after. What is cleared: `Backup.TargetURL`, `Source.Path`, `ConnectionString.BaseUrl`, `BackupTargetUrl.TargetURL` and password-typed `Option.Value` (the job `passphrase`, `jwt-config`, `pbkdf-config`,
   `remote-control-config`, ssl cert fields, `client-license-key`). The tool leaves a `-<ts>.bak` beside the database (delete it — it still holds the encrypted values) and refuses a non-server database. `Source` rows in the snapshot are cleartext, so sources survive; `server-passphrase`/`-salt` are **hashes** and not in the wipe list, so the **UI password survives** and "set the UI password afresh" is optional, not required.
   Re-enter the two values that matter — `TargetURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi` and the passphrase — through the **web UI** or `util/ad-hoc/yamaguchi_build_job.py`, which reads the passphrase in-process; never a `curl -X PUT` that puts the passphrase on argv. Then step 8.
7. **Procedure B — rebuild the job through the API.** Start the empty server with the §7.3 unit and a **new** settings key, in a data folder created `0700 duplicati:duplicati` (the one moved aside in step 2 is 0777 and 2.4.0.0 refuses it); set the UI password through the web UI; rebuild the job from the snapshot — sources, filters, schedule and option names are readable in it (`2026-09-21_duplicati_server_db_forensics.py` prints them; option *values* come from
   the record, §7.5), `TargetURL` as above, passphrase from `~/.config/duplicati-backup/env` (`util/ad-hoc/yamaguchi_build_job.py` built the job the first time and reads the passphrase in-process; update its defaults before use). **The rebuilt job is not id 2**: `sqlite_sequence` starts at 1, and the deployed watchdog, `yamaguchi_census.py`, AC-2, AC-5 and step 10 all default to 2. Record the assigned id and pass it explicitly everywhere, including
   `--backup-id <id>` on the redeployed watchdog unit. State in the rebuild whether it re-creates `additional-report-url`; if it does, that bearer JWT is a secret (S-8).
8. **Common to A0, A, A2 and B — move the index and re-point `DBPath` BEFORE the first run.** The snapshot's `Backup` row carries `DBPath=/usr/lib/duplicati/data/BMXWPAOGLP.sqlite`, an **absolute** path, and `RestConnection.cs`'s `ResolveDbPath` returns a rooted path unchanged — the server never relocates it. The §7.3.2 unit makes `/usr/lib/duplicati` read-only and P4 deletes it, so a procedure that skips this fails its first backup read-only and then
   loses the index. So: stop the server, `cp` `BMXWPAOGLP.sqlite` into the new data folder (`chown duplicati`, `0600`), and update the row — UI **Database → Placement → Save**, or `PUT /api/v1/backup/<id>` — after which 2.4.0.0 stores it *relative* (`GetRelativeDbPath`). Install §7.3 (unit, defaults, wrapper, guard) with `util/install_duplicati_service.bash`, then `sudo systemctl start duplicati.service`. Expect in the journal: schema upgrade 11→12 and
   `Server has started`. The job appears with its existing index — no Recreate. For Procedure B, run **Verify files** before any backup; if verification reports the index inconsistent with the destination, run Repair (this index *is* the destination's own, last written 09-18, so rule 11 does not apply) or, last resort, Recreate.
9. **Before the first run.** The job still carries `--tempdir=/home/pcalnon/.cache/duplicati-tmp` (unwritable under the new confinement) and its schedule `Time` is in the past, so it will start on its own once the startup pause lapses. Immediately after the server is up: **sample the scheduler state before touching it** — `GET /api/v1/serverstate`, recording `ProgramState`, `paused-until` and `SchedulerQueueIds` — then `pause`, change `--tempdir` to
   `/home/duplicati/.cache/duplicati-tmp` (create it, 0700 duplicati), add `--run-script-before-required` (§7.5), then `resume` and **sample `serverstate` again**. This is the 2026-08-30 stuck-pause class (`HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §1.7, YAM §8.22–§8.23): a first start under changed `DAEMON_OPTS` followed by pause/resume is the exact untested sequence that produced a 42.6 h silent outage, and without the two samples a
   recurrence is invisible. Pause and resume go through `util/ad-hoc/yamaguchi_server_api.py` (extended with `pause`/`resume`), **not** `duplicati-server-util`, which takes its secrets on argv. Before `resume`, dry-run the guard as the service user — `sudo -u duplicati DUPLICATI__REMOTEURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi /usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash; echo $?` — and require 0: it is
   `--run-script-before-**required**`, so a missing or failing guard aborts the first backup, which `resume` fires immediately.
10. **Re-arm alerting — before the acceptance checks, not after.** Set the UI password (web UI), write `~/.config/duplicati-backup/web-credential` (0600), and re-point **both** API clients at it (§7.6). AC-2 and AC-9 run through those clients, so a run order that proves the job first and creates the credential afterwards makes them fail 401 — today's watchdog symptom, reproduced by the plan itself. Redeploy the watchdog with `--backup-id <id>`; confirm the
    next 12:00 fire reads `OK`.
11. **Prove it.** `AC-2`, then one backup run (`AC-3`), then the two restore drills (`AC-4`), then `AC-12`.

### P0.5 — same session as the recovery (minutes, and none of it depends on the recovery)

These were scattered across P1 and P2 while the recovered server ran for days with the holes open. Each takes
minutes and has no dependency on which procedure step 3 chose.

1. **`sudo chown -R root:root /usr/lib/duplicati`** except `data/` (kept as the frozen copy until P4) — **before P0 step 3 runs any Duplicati tool**. The directory is duplicati-owned 0755 with no sticky bit, so the service user can replace `duplicati-cli`, `duplicati-database-tool` or `duplicati-server`, all of which root and `pcalnon` execute during recovery. Also `chown root:root /etc/default/duplicati` (today `duplicati:duplicati` 0644 — the service user
   can rewrite its own next argv), and remove `/home/duplicati/bin/` entirely: it holds only the symlink into a developer checkout that D-6 replaces with an installed copy.
2. **Install the snapshot timer's script as a root-owned copy** under `/usr/local/lib/duplicati/` and add `ProtectSystem=strict` to `yamaguchi-server-db-snapshot.service`. It runs as **root** today with `ExecStart` naming the primary checkout, so `sys.path[0]` is pcalnon-writable and every branch switch changes what root executes at 13:45 UTC (§7.7).
3. **Re-key now, not "same week" (P1 step 1's content, moved here).** The live settings key *is* the backup passphrase (S-2), and the burned key from S-1 is public. Stop the snapshot timer, do the two-start re-key back to back, then `PRAGMA wal_checkpoint(TRUNCATE); VACUUM;` with the server stopped, then restart the timer (§7.3.5).
4. **Scrub both log stores** — `/var/log/syslog*` *and* the journal, in that order (§6, D-8) — and verify with `sudo ls -la /var/log/syslog-2026092*`. A journal-only scrub leaves an identical copy behind.
5. **Handle S-7 and S-4.** Remove the world-readable `.env` inside `…/worktrees/curious-plotting-hummingbird/` after the fingerprint reconciliation (the file only — that worktree is do-not-sweep), `chmod 0600` the escrow `env`, and start the S-4 copy-out. The Dropbox "delete forever" and account audit are owner actions.
6. **Close the detection gap**: enable `secret_scanning_non_provider_patterns`, add a gitleaks **content** rule for `(SETTINGS_ENCRYPTION_KEY|PASSPHRASE(_OLD)?|DUPLICATI_WEB_CREDENTIAL|webservice-password|passphrase)=` with a non-placeholder value, and add a gitleaks pre-commit hook. The repository's current rule cannot match a value containing `* @ $ %`, which is why both PRs passed; CI runs gitleaks only *after* publication.""",
)

edit(
    "s8-p1",
    """1. Generate a new settings key (`umask 077; openssl rand -base64 48 | tr -d '\\n' > /etc/credstore/duplicati-settings-key`), then re-key the database in two starts: first with the **old** key still in the credential file and `--disable-db-encryption` appended to `DAEMON_OPTS` (every field is decrypted on that start), then with the new key in the credential file and the flag removed (every field is re-encrypted; add `--require-db-encryption-key` at this point). Escrow the new
   key with the passphrases (printed, password manager, machine-local copy outside the Dropbox root).
2. Delete the five commented lines from `.env`; set it to the §7.3.5 contract; `chmod 0600`.
3. Remove the commented "Old Unit file" block from `scripts/duplicati-wrapper.bash` (the wrapper is replaced by §7.3.3 in the same PR).
4. Move `_yamaguchi_keys/` out of the Dropbox root (S-4).
5. Rule on D-2 (passphrase exposure) and D-8 (journal scrub); execute the ruling.""",
    """1. *(Executed in P0.5 step 3 — kept here as the procedure of record.)* Generate a new settings key (`umask 077; openssl rand -base64 48 | tr -d '\\n' > /etc/credstore/duplicati-settings-key`), then re-key the database in two starts: first with the **old** key still in the credential file and `--disable-db-encryption` appended to `DAEMON_OPTS` (every field is decrypted on that start), then with the new key in the credential file and the flag removed (every field is
   re-encrypted; add `--require-db-encryption-key` at this point). Stop the snapshot timer across both starts and `VACUUM` afterwards (§7.3.5). Escrow the new key with the passphrases (printed, password manager, machine-local copy outside the Dropbox root).
2. Delete the five commented lines from `.env`; set it to the §7.3.5 contract. **Mode: `0640 root:duplicati` as recommended, or `0600 duplicati:duplicati` — this is the open dissent recorded in §11**; install the stricter form until the owner rules.
3. Remove the commented "Old Unit file" block from `scripts/duplicati-wrapper.bash` (the wrapper is replaced by §7.3.3 in the same PR).
4. **Copy** `_yamaguchi_keys/` out of the Dropbox root — `cp -a` to `/mnt/Backups/Ubuntu/_yamaguchi_keys/`, a sibling of `Dropbox/` — verify sha256 on both sides, and delete the in-tree copy **only on owner sign-off** (this is the single exception to the "nothing under `/mnt/Backups/Ubuntu/` is moved" rule; the preamble names it). Then, on dropbox.com, **Delete forever** and audit the account. `dropbox exclude add` is not a substitute: it removes the local copy
   and leaves the cloud one. Exclude `_yamaguchi_records/` too if it lists paths. (S-4)
5. **Re-decide D-2**, do not merely execute it: it was ruled "accept + scrub" against a local-journal exposure, and the same lines are in `/var/log/syslog*`, in cloud-linked Claude Code transcripts, and — as a cleartext passphrase file — in S-7 and in a third party's cloud (S-4). Then rule on D-8 and execute.""",
)

edit(
    "s8-p2p3p4",
    """1. `chown -R root:root /usr/lib/duplicati` except `data/` (kept as the frozen copy until P4); `chmod 0755 /home/duplicati/bin` or remove it; `chmod 0700 /home/duplicati/.config/Duplicati` and `0600` its files (Duplicati's own requirement, §7.3.2); `/etc/default/duplicati` → root:root.
2. Run `util/ad-hoc/2026-09-21_backup_destination_permissions.bash`; restart Dropbox in a session carrying gid 139; verify `AC-7`.""",
    """1. *(The chown, the `bin/` removal and `/etc/default/duplicati` moved to P0.5 step 1.)* Confirm `chmod 0700 /home/duplicati/.config/Duplicati` and `0600` its files (Duplicati's own requirement, §7.3.2) survived the recovery.
2. **After a D-14 ruling**, run `util/ad-hoc/2026-09-21_backup_destination_permissions.bash` — first on a scratch directory **on `sda1`** to check ext4's default-ACL creation modes, and only when `dropbox status` reads up to date (it produces ~1,700 metadata updates). Restart Dropbox in a session carrying gid 139; verify `AC-7`.""",
)

edit(
    "s8-p3",
    """1. Land `util/juniper-backup-scheduled.bash` and the three user units; install; enable; observe one SKIPPED (unplugged) and one OK (plugged) run; class-1 drill (`util/ad-hoc/2026-08-26_backup_restore_drill.bash`).
2. Rule on D-5; add the absolute-mount-root form to `util/juniper-backup.bash`; fstab line for the external drive; first `full` set; restore drill of one archive from it.""",
    """1. **Fix the runner's mount root first.** Add the absolute-mount-root form to `util/juniper-backup.bash` (a `MEDIA_NAMES` entry beginning with `/` is taken as an absolute mount root) and have the scheduler and the runner read **one** mount-root setting. Until this lands, every "due" run the scheduler starts ends `FAILED runner rc=1` and step 2 cannot produce its own OK run (§4.5, §7.8).
2. Land `util/juniper-backup-scheduled.bash`, the four user units (timer, path, service, **failure**) and `util/install_juniper_backup_timer.bash`; install; enable; observe one SKIPPED (unplugged) and one OK (plugged) run; watch `systemctl --user status juniper-backup.path` for 30 s after the plug-in to confirm the `.path` unit is still active; class-1 drill (`util/ad-hoc/2026-08-26_backup_restore_drill.bash`).
3. Rule on D-5; fstab line for the external drive; first `full` set; restore drill of one archive from it.""",
)

edit(
    "s8-p4",
    """1. Archive `/usr/lib/duplicati/data/` to the T1 source (`tar` into `~/.local/state/duplicati-server-db/root-data-folder-2026-09.tar`) and remove it; `chown root:root /usr/lib/duplicati` fully.""",
    """1. Archive `/usr/lib/duplicati/data/` and remove it. **Not** into `~/.local/state/` as an unencrypted tar: that directory is inside the backup source and group-shared, and the tar holds the server database (encrypted under the burned, public key) plus the per-job index, which carries the full path list of the whole home directory — backing that up in cleartext violates this design's own rule 8. Write it to a **root-only 0700 directory outside the backup source**,
   or encrypt the tar. `/usr/lib/duplicati` is already fully `root:root` from P0.5.""",
)

# =====================================================================================
# §9 — acceptance criteria
# =====================================================================================

edit(
    "s9-ac3",
    """| AC-3 | First post-recovery backup `ParsedResult=Success`, `SourceFilesCount` within 2 % of 1,024,167 and `SourceSizeString` within 5 % of 290.61 GiB (the 09-18 root-era values) — proves `CAP_DAC_READ_SEARCH` restored coverage; census `AGREE` | `python3 util/ad-hoc/yamaguchi_census.py --runs 1`; `Metadata` via the forensics script on a fresh snapshot |
| AC-4 | Restore drill from the new fileset with local blocks **off** (the 2.4.0.0 default; never pass `--restore-with-local-blocks`; `--no-local-blocks` is deprecated), SHA-256 and length match on ≥ 15 files, one negative control fails | `util/ad-hoc/yamaguchi_drill_watch.bash` lineage |""",
    """| AC-3 | First post-recovery backup `ParsedResult=Success`, **`Warnings=0` and `NotProcessedFiles=0`**, `SourceFilesCount` within 2 % of 1,024,167 and `SourceSizeString` within 5 % of 290.61 GiB, **plus a positive find of one `~/.ssh` and one `~/.gnupg` path**; census `AGREE` (note AC-3a) | `python3 util/ad-hoc/yamaguchi_census.py --runs 1`; `duplicati-cli find`; `Metadata` via the forensics script on a fresh snapshot |
| AC-4 | **Two** restore drills, not one: one from `duplicati-20260918T140000Z` (pre-recovery) and one from the first post-recovery fileset. Both with local blocks **off** (the 2.4.0.0 default; never pass `--restore-with-local-blocks`; `--no-local-blocks` is deprecated), SHA-256 and length match on ≥ 15 files, one negative control fails (note AC-4a) | `util/ad-hoc/yamaguchi_drill_watch.bash` lineage |""",
)

edit(
    "s9-ac8",
    """| AC-8 | No secret in the journal since the hardening timestamp: zero `LINE: "`, `Exporting Environment`, `Settings Encryption Key:` lines; `.env` has no commented assignment; wrapper has no credential-shaped literal | `journalctl -u duplicati.service --since <ts>`; `2026-09-21_env_file_shape.py`; `grep -c 'Environment=SETTINGS' scripts/duplicati-wrapper.bash` = 0 |""",
    """| AC-8 | No secret in **either log store** since the hardening timestamp: zero `LINE: "`, `Exporting Environment` and `Settings Encryption Key:` lines in the journal **and in `/var/log/syslog*`**; zero in the job log's run-script output; `.env` has no commented assignment; the wrapper has no credential-shaped literal; the P0.5 gitleaks rule passes tree-wide | `journalctl --since <ts>`; `sudo grep -c` over `/var/log/syslog*`; `2026-09-21_env_file_shape.py` |""",
)

edit(
    "s9-ac13",
    """| AC-12 | `systemd-analyze security duplicati.service` reports an exposure at or below the offline baseline of the §7.3.2 unit and no ✗ row beyond those the design accepts (`AmbientCapabilities=`, the `CAP_DAC_*` / `CAP_FOWNER` / `CAP_IPC_OWNER` bounding-set row, `ProtectHome=` read-only); the server completes AC-3 under every confinement directive the unit sets — a directive it cannot run under is removed **and recorded**, never silently | `systemd-analyze security`; journal of the first start |""",
    """| AC-12 | `systemd-analyze security duplicati.service` reports an exposure at or below the §7.3.2 unit's offline baseline (**5.2 MEDIUM** before the B3 directives) and no ✗ row beyond those the design accepts; the server completes AC-3 under every confinement directive the unit sets — one it cannot run under is removed **and recorded**, never silently (note AC-12a) | `systemd-analyze security`; journal of the first start; `systemd-run` trial on the probe copy first |
| AC-13 | The job's `--run-script-before-required` equals `/usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash` and nothing else; no other run-script option is set (note AC-13a) | `python3 util/ad-hoc/yamaguchi_server_api.py export <id>`; diff against the design's path |

Notes on the criteria above:

- **(AC-3a)** The count tolerance alone is not enough. From the snapshot's 45 filters, the large 0700 trees `Dropbox-OLD/` (327k entries) and `snap/` (256k) are *excluded*; the **unfiltered** 0700 trees (`.config/Slack` 54k, `.config/Code` 39.5k, `.mozilla` 23k, `.local/state` 22.6k, `.config/Cursor` 12k, `.amp`, `.claude/projects`, `.ssh` 31, `.gnupg` 98) sum to roughly 15 % of 1,024,167. So a ±2 % count check sees a *gross* loss but cannot see `~/.ssh` or
  `~/.gnupg` — the very trees §7.10 says the capability exists for; hence the explicit `find`. The baseline numbers are real but appear nowhere in the record, so cite their provenance: the snapshot's `Metadata` rows `SourceFilesCount=1024167` and `SourceSizeString=290.610 GiB`. Pre-flight the capability itself before the run: `systemd-run -p User=duplicati -p AmbientCapabilities=CAP_DAC_READ_SEARCH --wait cat ~/.ssh/known_hosts` (owner action — it needs root).
- **(AC-4a)** PLAN §7 criterion 3 asks for a second restore point after at least one incremental, and a single drill collapses it. The re-attached index serving the *old* filesets is exactly what one drill cannot see — which is the whole risk of Procedures A, A2 and B. If `--aes-version` is pinned to 3 rather than 2 (§7.5), one drill must be pre- and one post-format-change.
- **(AC-12a)** The §7.3.2 unit adds `IPAddressDeny`, `RestrictAddressFamilies`, `SystemCallFilter`, `ProtectProc`, `ProcSubset`, `PrivateDevices`, `ProtectClock`, `ProtectHostname`, `ProtectKernelLogs` and `RestrictNamespaces` on top of that baseline, **none of which has been executed against 2.4.0.0 on this host** (open item O-3). Trial them with `systemd-run` against the probe copy before the live unit.
- **(AC-13a)** Pinned as an acceptance check because a run-script path is a plain job option with no allow-list: anyone holding the UI credential can point it anywhere and have it execute as `duplicati` **with** `CAP_DAC_READ_SEARCH` (§7.3.6). A silent change to this option is a privilege escalation that no other check would catch.""",
)

# =====================================================================================
# §10 — owner decisions
# =====================================================================================

edit(
    "s10-decisions",
    """| D-1 | Settings-key policy: keep DB encryption with a distinct, escrowed key, or `--disable-db-encryption` | keep encryption; the record's objection (a third key) is accepted as the price |
| D-2 | `PASSPHRASE` exposure in the journal and `.env` comments: accept (local readers only) + scrub, or start a new set under a new passphrase | accept + scrub now; rotate at the next set rebuild |""",
    """| D-1 | **Rule before P0.** Settings-key policy: keep DB encryption with a distinct, escrowed key, or `--disable-db-encryption` | keep encryption; the record's objection (a third key) is accepted as the price |
| D-2 | **Re-decide** (§6 note S-3a). `PASSPHRASE` exposure: accept + scrub, or start a new set under a new passphrase. The original ruling assumed a journal-only, local exposure; four things falsify that | lean to a **new set under a new passphrase**, or record an explicit owner acceptance that names Dropbox as a reader. A new set must also **delete-forever** the old one server-side (§7.5 rule 7) |""",
)

edit(
    "s10-d4d6d9",
    """| D-4 | Read access to `/home/pcalnon`: `CAP_DAC_READ_SEARCH` on the service vs recursive ACLs on the home | capability |""",
    """| D-4 | **Rule before P0.** Read access to `/home/pcalnon`: `CAP_DAC_READ_SEARCH` on the service vs recursive ACLs on the home. The trade is asymmetric and §7.1 principle 3 states it in full | capability, **with** §7.3.2's confinement set, which is what stops it also being an exfiltration channel |""",
)

edit(
    "s10-d6",
    """| D-6 | Live wrapper: root-owned installed copy (recommended) vs the symlink into the checkout | copy |""",
    """| D-6 | **Rule before P0.** Live wrapper: root-owned installed copy (recommended) vs the symlink into the checkout | copy — and delete `/home/duplicati/bin/` rather than keeping the symlink as a "fallback" |""",
)

edit(
    "s10-d9-d12",
    """| D-9 | Web UI reachable from LAN (`any` + allowed hostnames) or loopback only | loopback |
| D-10 | T2 cadence (weekly proposed) and USB retention | weekly; prune sets older than 8 weeks after a drill |
| D-11 | Docker volumes and conda envs: export into the T1 source, or accept the gap | export docker volumes weekly; conda recipes only |
| D-12 | Inherited items: `sda` SMART, `sdc4` read-only probe, cloud reporting, user-lane removal PR, `records_sync` de-drift | unchanged from the record |""",
    """| D-9 | **Rule before P0.** Web UI reachable from LAN (`any` + allowed hostnames) or loopback only | loopback, plus `--webservice-disable-signin-tokens` once a password exists |
| D-10 | T2 cadence (weekly proposed) and USB retention | weekly; prune sets older than 8 weeks after a drill |
| D-11 | Docker volumes and conda envs: export into the T1 source, or accept the gap | export docker volumes weekly; conda recipes only |
| D-12 | Inherited items, **enumerated rather than gestured at** (note D-12a) | each item gets its own disposition in the P3/P4 review, not a blanket sentence |
| D-13 | **New.** Dropbox root policy: exclude everything except `Backups/`, or accept that personal files (9 jpg, 2 pdf, a lnk today) keep syncing beside the ciphertext (note D-13a) | exclude everything but `Backups/` — it costs nothing and removes a whole class of cross-contamination |
| D-14 | **New.** The destination permission model: the R-7/R-8 group-write form of §7.4 (directories `2770`, files `0660` — `pcalnon` and Dropbox can write and **delete** all 877 volumes) vs the read-only form (`duplicati:duplicati 2750`, files `0640`, `UMask=0027`, volumes chowned to `duplicati`) | the **read-only** form (note D-14a) |

Notes on the decisions above:

- **(D-12a)** The earlier row said "unchanged from the record" and then named five items, letting the rest dissolve — the failure shape `HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §6.1 recorded. Every open item of that handoff's §1 and of `JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md` §8.27.6 gets one of three dispositions — **carried**, **out of scope**, or **closed by §** — and none may be left unstated.
  Carried today: `sda` SMART never read (it guards the only local copy); the `sdc4` read-only loop probe; the sdc2 grow; cloud reporting (deferred); the user-lane removal PR (P4 step 4); the dead `yamaguchi_records_sync.bash`; the drift-guard tests in 7 repos; `yamaguchi_run_script_after.bash` as alerting candidate A, never revoked; `duplicati_first_backup.bash`'s hardcoded gate; the §8.21.5 residuals; the unconfirmed `sops-backup-key.sh` escrow run (inherited
  O-2). Closed by this design: the watchdog `ProgramState` check (§7.6).
- **(D-13a)** The owner prompt said "Dropbox syncs only the contents of `Backups/`"; §4.4 corrected that to nine excluded folders with everything else at the root syncing, and no decision item then asked what the root *should* be. This one does.
- **(D-14a)** R-8 asks only for **read**; the group-write form lets a cloud-side deletion (compromised account, linked phone, another machine) or an accidental local `rm -rf` propagate into the local master and on to T1c. State the limit honestly: `pcalnon` is root-equivalent via `sudo`/`docker` anyway, so the read-only form buys protection against **accident and commodity malware**, not against a deliberate local adversary. It conflicts with R-7's
  "read/write/execute as appropriate", which is exactly why it is the owner's call and not this design's.""",
)

# =====================================================================================
# Appendices
# =====================================================================================

edit(
    "appA1-note",
    """2026-09-20T18:19:46 duplicati-wrapper.bash: Server has started and is listening on localhost, port 8300
```""",
    """2026-09-20T18:19:46 duplicati-wrapper.bash: Server has started and is listening on localhost, port 8300
2026-09-20T18:47:44 duplicati-server: Failed to process the path: Access to the path '/media/pcalnon/temp_backups' is denied.   (last lines of the unit; x4, and again x4 at 18:51:33)
```

Two identifier notes, because they change what a line means: the `20:48:12` line was emitted under
`wrapper.bash` — the **first** wrapper's name — not `duplicati-server`, and at `13:32:34` on 09-20 five starts
of that same older `wrapper.bash` died `SettingsEncryptionKeyMissingException` sixteen seconds before the
`13:32:50` success from `duplicati-wrapper.bash`. Two wrapper files were in play that afternoon.""",
)

edit(
    "appA3-row",
    """| `/usr/lib/duplicati/data/` | 2026-08-25 02:38:43 | 2026-09-18 21:03:34 | 2026-09-19 19:15:00 |""",
    """| `/usr/lib/duplicati/data/` | 2026-08-25 02:38:43 | 2026-09-18 21:03:34 — **the `-wal`/`-shm` creation, not the encryption** (a directory mtime records an entry create/delete/rename; encrypting fields rewrites the database file). That it never moved again means the WAL was never removed by a clean close | 2026-09-19 19:15:00 |""",
)

edit(
    "appB-index",
    """| `util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash` | Procedure A probe | `bash -n`, shellcheck |""",
    """| `util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash` | Procedure A probe (confirmation only) | `bash -n`, shellcheck |
| `util/ad-hoc/2026-09-22_confirm_a0_premise.bash` | Procedure A0 premise check | `bash -n`, shellcheck |
| `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash` | Procedure A0 restore | `bash -n`, shellcheck |""",
)

edit(
    "appC-add",
    """8. The pcalnon crash log names `Duplicati.GUI.TrayIcon.Net10`; no assembly of that name ships in 2.4.0.0, so the binary that wrote it (the 2.3.0.4 package, by timing) is not verifiable from the installed tree. The message it carries matches the 2.3.0.4 journal lines exactly.""",
    """8. The pcalnon crash log names `Duplicati.GUI.TrayIcon.Net10`; no assembly of that name ships in 2.4.0.0, so the binary that wrote it (the 2.3.0.4 package, by timing) is not verifiable from the installed tree. The message it carries matches the 2.3.0.4 journal lines exactly.
9. **The pcalnon `Duplicati-server.backup` is itself `enc-v1:`** — 11 encrypted values under a single key hash, which the offline probe verified 11/11 and matched to no candidate. It is a libsecret-minted key (§5.4), which is how a database comes to be encrypted with nobody typing one. Every "the database stores the passphrase in cleartext" statement in the record (YAM §8.19.3, and item 3 above) is therefore true of the **root** database only, and only before 09-18 21:03.
10. YAM §8.20.2's record that the owner **rejected** `SETTINGS_ENCRYPTION_KEY` on 2026-08-30 was reversed without a record by the 09-18 unit edits and the 09-20 `.env`. D-1 asks the question again. (Already in §3.5; repeated here because Appendix C is the list a future reader diffs against the record.)

**None of items 1–10 has been applied to its target document.** That is tracked work, not a closed correction: item 1's targets are YAM §8.20.4 and `HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §1.8; item 4's are `util/ad-hoc/yamaguchi_server_db_snapshot.py:20,36` and `util/systemd/yamaguchi-server-db-snapshot.service:5`; item 5's is the destination README. Item 2's own text was rewritten by consensus round 1 (Lane A2) and item 9 is new in the reconciliation.""",
)

# =====================================================================================
# driver
# =====================================================================================

def join_wrapped_table_rows(text: str) -> str:
    """Re-join a markdown table row that was wrapped across lines.

    A newline inside a table cell ends the table: markdownlint then reports MD055/MD056 on
    every following row and the rendered table loses its data. Every legitimate row in this
    document is `leading_and_trailing`, so a line that starts with `|` and does not end with
    `|` is a wrapped row and its continuation lines belong to it. Fenced blocks are skipped,
    since a line inside one may legitimately start with `|`.
    """
    out: list[str] = []
    lines = text.split("\n")
    in_fence = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            out.append(line)
            i += 1
            continue
        if not in_fence and line.startswith("|") and not line.rstrip().endswith("|"):
            merged = line.rstrip()
            i += 1
            while i < len(lines):
                nxt = lines[i]
                merged = merged + " " + nxt.strip()
                i += 1
                if nxt.rstrip().endswith("|"):
                    break
            out.append(merged)
            continue
        out.append(line)
        i += 1
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="report only; write nothing")
    args = ap.parse_args()

    if not DESIGN.parent.is_dir():
        print(f"run from the repository root (no {DESIGN.parent})", file=sys.stderr)
        return 2

    text = subprocess.run(
        ["git", "show", f"{PRISTINE_REF}:{DESIGN}"],
        capture_output=True, text=True, check=True,
    ).stdout

    failures = 0
    for tag, old, new, count in EDITS:
        seen = text.count(old)
        if seen != count:
            print(f"FAIL {tag}: anchor occurs {seen}x, expected {count}x", file=sys.stderr)
            failures += 1
            continue
        text = text.replace(old, new, count)
        print(f"  ok  {tag}")

    if failures:
        print(f"\n{failures} anchor(s) failed; nothing written", file=sys.stderr)
        return 1

    text = join_wrapped_table_rows(text)

    over = [
        (i + 1, len(ln))
        for i, ln in enumerate(text.split("\n"))
        if ln.startswith("|") and len(ln) > 512
    ]
    if over:
        print(f"\n{len(over)} table row(s) exceed the 512-char MD013 limit:", file=sys.stderr)
        for lineno, width in over:
            print(f"  line {lineno}: {width} chars", file=sys.stderr)

    if args.check:
        print(f"\n--check: {len(EDITS)} edits would apply; nothing written")
        return 0

    DESIGN.write_text(text, encoding="utf-8")
    print(f"\nwrote {DESIGN} ({len(text)} bytes, {len(EDITS)} edits)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
