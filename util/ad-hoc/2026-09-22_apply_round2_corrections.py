#!/usr/bin/env python3
"""Apply consensus round 2's corrections to the backup design.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-09-22
Status:      ad-hoc -- reconciliation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md
             notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md
             util/ad-hoc/2026-09-22_reconcile_backup_design.py  (round 1; this script runs it first)

Stage 2 of a two-stage rebuild. It re-runs the round-1 reconciliation from the pristine
`origin/main` blob, then applies round 2's corrections on top, so one command reproduces the
final document byte-for-byte and neither stage's edit set has to be remembered.

Same discipline as stage 1: every anchor must occur exactly the expected number of times, table
rows are re-joined if an edit wrapped one, and any row over MD013's 512-char limit is reported.

Usage:  python3 util/ad-hoc/2026-09-22_apply_round2_corrections.py [--check]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

DESIGN = Path("notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md")
STAGE1 = Path("util/ad-hoc/2026-09-22_reconcile_backup_design.py")

EDITS: list[tuple[str, str, str, int]] = []


def edit(tag: str, old: str, new: str, count: int = 1) -> None:
    EDITS.append((tag, old, new, count))


# =====================================================================================
# Lane A (host) — counts, dates and modes that round 2 re-measured
# =====================================================================================

edit(
    "r2-chown-split",
    """| Abandoned data folder | `/usr/lib/duplicati/data/` (0700, **now owned by `duplicati`**). `/usr/lib/duplicati` and **every directory beneath it** (97) were chowned to `duplicati`; **no file was** — all 1,443 regular files, `duplicati-server` included, are still `root:root` (note b) |""",
    """| Abandoned data folder | `/usr/lib/duplicati/data/` (0700, **now owned by `duplicati`**). **97 of 118 directories** were chowned; **21 are still `root:root`**, so the sweep was shallow. **No file was chowned at all**: all 1,443 regular files outside `data/` remain `root:root` (note b) |""",
)

edit(
    "r2-chown-split-55",
    """- **Permissions by trial.** `/usr/lib/duplicati` and `/usr/lib/duplicati/data` were chowned to `duplicati` — **directories only**: all 1,443 regular files, the binaries included, are still `root:root`.""",
    """- **Permissions by trial.** `/usr/lib/duplicati` and `/usr/lib/duplicati/data` were chowned to `duplicati` — **directories only, and not even all of those**: 97 of 118 directories changed owner and 21 did not (the whole `runtimes/` subtree, 11 directories, and ten `licenses/<package>/` directories — `licenses/` itself *did* change, so this was a shallow or interrupted recursion, not a `find -type d` sweep). All 1,443 regular files outside `data/`, the binaries
  included, are still `root:root`. This matters for the P0.5 remediation: a `chown -R` that is verified by "did anything change?" will see 97 changes and 21 no-ops, and the 21 that look wrong are the ones that were already right.""",
)

edit(
    "r2-tempbackups-count-41",
    """- **(a)** The 03:23:44 reload time is the orchestrator's own journal reading; no validation lane measured it. When Lane A1 looked, the unit file was open in a live `vim` (pid 2318515) and two `su - duplicati` shells were running — both are sinks for the 09-18 key (§6). The live server's **last** journal lines are 09-20 18:47:44 and 18:51:33, ×4 each: `Failed to process the path: Access to the path '/media/pcalnon/temp_backups' is denied` — after the four
  import failures someone pointed it at the retired USB path.""",
    """- **(a)** The 03:23:44 reload was **not an operator action**: every `daemon-reload` after the 01:44:57 unit edit was requested by `snapd.service` (03:23:44, 10:53:47, 14:43:48, 20:43:55 on 09-21; the last operator-scoped reload was 09-20 16:41:03). The armed `ExecStart` therefore became the loaded one *by accident*, through a routine package reload — which strengthens the point rather than weakening it: nobody chose this, and nobody will choose the
  restart either. The unit file was open in a live `vim` (pid 2318515) and two `su - duplicati` shells (3065639, 3117158) were running when Lane A1 looked, and **all three were still alive 2 days 8 hours later** at round 2 — both shells' in-memory history is still unwritten and still recoverable (§6). The live server's **last** journal lines are 09-20 18:47:44 and 18:51:33, **×2 each — four lines in total**, since each event logs an outer
  `System.Exception: Failed to process the path: …` and its inner `System.UnauthorizedAccessException: Access to the path '/media/pcalnon/temp_backups' is denied`. After the import failures it was pointed at the retired USB path, and nothing has been emitted since.""",
)

edit(
    "r2-tempbackups-count-42",
    """| 09-20 18:47:44, 18:51:33 | The live server's last journal lines, ×4 each: `Access to the path '/media/pcalnon/temp_backups' is denied` — after the import failures it was pointed at the retired USB path | journal |""",
    """| 09-20 18:47:44, 18:51:33 | The live server's last journal lines — two events, each logged **twice** (outer + inner exception), **four lines in all**: `Access to the path '/media/pcalnon/temp_backups' is denied` | journal |""",
)

edit(
    "r2-tempbackups-appA",
    """2026-09-20T18:47:44 duplicati-server: Failed to process the path: Access to the path '/media/pcalnon/temp_backups' is denied.   (last lines of the unit; x4, and again x4 at 18:51:33)""",
    """2026-09-20T18:47:44 duplicati-server: Failed to process the path: Access to the path '/media/pcalnon/temp_backups' is denied.   (last lines of the unit; x2 -- outer + inner exception -- and again x2 at 18:51:33; 4 lines in total)""",
)

edit(
    "r2-syslog-split",
    """`syslog-20260920.gz` carry 4 and 18 specifier lines. logrotate keeps day files ~10 days. A journal
scrub that does not also scrub these removes nothing (D-8).""",
    """`syslog-20260920.gz` carry **5 and 18 `Invalid slot` lines** — 23, the journal's own
figure. (Under the narrower `Failed to resolve specifiers` predicate the split is 4 and 18 = 22; the extra line
in 09-19's file is the `Failed to resolve unit specifiers` of 21:23:25. Count with the same predicate or the
totals will not reconcile.) logrotate keeps day files ~10 days, so this set ages out around **2026-10-01**. A
journal scrub that does not also scrub these removes nothing (D-8).

Two operational notes for whoever writes the scrub. `delaycompress` means a day file gains its `.gz` one
rotation *after* it stops being written — `syslog-20260921` was plain when this document was drafted and is
`syslog-20260921.gz` now — so **glob the set, never name a file**. And re-measuring these counts is itself an
exposure: a `journalctl` capture large enough to count them is a fresh, complete copy of every leaked line.
Round 2's own host lane created an 876 MB one and deleted it eight minutes later; the D-8 scrub is only as
complete as the last agent who cleaned up after themselves.""",
)

edit(
    "r2-s1-syslog",
    """23 systemd `Invalid slot` journal lines, **and the same lines in `syslog-20260919.gz` (4) and `syslog-20260920.gz` (18)**""",
    """23 systemd `Invalid slot` journal lines, **and the same 23 lines in `syslog-20260919.gz` (5) and `syslog-20260920.gz` (18)**""",
)

edit(
    "r2-s2-group",
    """| S-2 | Current settings key = **the live `Yamaguchi` backup passphrase** (32 chars) | `.env` line 22 (0660 duplicati:duplicati — readable by group `duplicati`, i.e. `pcalnon`);""",
    """| S-2 | Current settings key = **the live `Yamaguchi` backup passphrase** (32 chars) | `.env` line 22 (0660 duplicati:duplicati — readable by any `pcalnon` process carrying gid 139 — note S-2b);""",
)

edit(
    "r2-s2b-note",
    """- **(S-2a)** The `.env` comment labels this value "Ubuntu-fresh".""",
    """- **(S-2b)** Group membership binds at **login**, not at `chmod` time: a `pcalnon` session older than the group grant does not carry gid 139 and cannot read this file — round 2's own host lane could not, and the Dropbox daemon cannot either (§4.4). That shrinks the exposure not at all, since `sudo` and `su - duplicati` are each one step away and the 0777 database copies need no group membership whatsoever. State it as a property of
  *processes*, never of the user.
- **(S-2a)** The `.env` comment labels this value "Ubuntu-fresh".""",
)

edit(
    "r2-1332-span-42",
    """Sixteen seconds *before* the 13:32:50 success, five starts of the **older** `wrapper.bash` died `KeyMissing` at 13:32:34 — two wrapper files were in play (note 5) |""",
    """Sixteen seconds *before* the 13:32:50 success, five starts of the **older** `wrapper.bash` died `KeyMissing` across 13:32:34–13:32:38 — two wrapper files were in play (note 5) |""",
)

edit(
    "r2-1332-span-54",
    """The `Missing` ×5 at 13:32:34 and the
`Missing`/`Mismatch` at 16:41/16:44 on 09-20 were the home folder's own fresh databases""",
    """The `Missing` ×5 across 13:32:34–13:32:38 and the
`Missing`/`Mismatch` at 16:41/16:44 on 09-20 were the home folder's own fresh databases""",
)

edit(
    "r2-1332-span-appA",
    """and at `13:32:34` on 09-20 five starts
of that same older `wrapper.bash` died `SettingsEncryptionKeyMissingException` sixteen seconds before the
`13:32:50` success from `duplicati-wrapper.bash`. Two wrapper files were in play that afternoon.""",
    """and from `13:32:34` to `13:32:38` on 09-20, five starts
of that same older `wrapper.bash` died `SettingsEncryptionKeyMissingException` — the first of them sixteen
seconds before the `13:32:50` success from `duplicati-wrapper.bash`. Two wrapper files were in play that
afternoon. (The older file is identifiable in the journal by its own error, `line 38:
/home/duplicati/.config/.env: No such file or directory` — a path the successor never reads.)""",
)

edit(
    "r2-datafolder-temp1",
    """`.env` is 0660, `installation.txt`/`machineid.txt` 0664, subdirectories 0775, `temp/` root-owned 0755 |""",
    """`.env` is 0660, `installation.txt`/`machineid.txt` 0664, subdirectories 0775 (`backups/`, `control_dir_v2/`, **`temp1/`**), `temp/` root-owned 0755 |""",
)

edit(
    "r2-churn-count",
    """Two facts to know before running it on a synced tree: `chmod 0660` over ~1,700 files strips an
executable bit Dropbox has already synced, so it produces ~1,700 metadata updates (bandwidth, not
correctness) — run it only when `dropbox status` reads up to date.""",
    """Two facts to know before running it on a synced tree: `chmod 0660` strips an executable bit Dropbox has
already synced from **1,784** files — every regular file under `…/Dropbox/Backups` carries one — so it
produces 1,784 metadata updates (bandwidth, not correctness); run it only when `dropbox status` reads up to
date.""",
)

edit(
    "r2-runmedia-tmpfs",
    """Test it rather than trusting it: plug a stamped drive and watch `systemctl --user status juniper-backup.path`
for 30 s. (`/run/media/pcalnon` exists — `root:root` 0750 with an ACL, currently empty.)""",
    """Test it rather than trusting it: plug a stamped drive and watch `systemctl --user status juniper-backup.path`
for 30 s. `/run/media/pcalnon` exists, `root:root` **0750** with a named ACL entry `user:pcalnon:r-x`, and is
currently empty — the `r-x` is exactly what a `--user` path unit needs to place its inotify watch, and
`pcalnon` deliberately has no write there because udisks2 owns the directory. One thing to know before the
first post-reboot trigger is read: **`/run` is tmpfs**, so `/run/media/pcalnon` does not survive a reboot and
is re-created by udisks2. A systemd path unit handles a missing path by watching the nearest existing
ancestor, so the unit still works — but a reader who assumes the directory is permanent will misread that
first trigger.""",
)

edit(
    "r2-sink-dbcopies",
    """| World-readable server-DB copies | `Duplicati-server.backup` 0777, `backups/*pre-dbpath-fix.sqlite` 0644 — `enc-v1:` under the pcalnon-profile libsecret key, so encrypted but wrongly exposed | `chmod 0600` now |""",
    """| World-readable server-DB copies, **by path** | Reachable by any local user, all under `/home/duplicati/.config/Duplicati/`: `Duplicati-server.backup` **0777**, `backups/Duplicati-server_2026-08-22_pre-dbpath-fix.sqlite` **0644**, `temp1/Duplicati.GUI.TrayIcon-crashlog.txt` **0644** (note S-9a) | `chmod 0600` the duplicati-home set — `enc-v1:` under the pcalnon-profile libsecret key, so encrypted but wrongly exposed |
| **Re-measuring the exposure creates a new copy of it** | A `journalctl` capture large enough to count these lines is itself a complete second copy. Round 2's host lane made an 876 MB one and removed it eight minutes later | Any agent or operator who re-verifies §6's counts deletes the capture in the same session, and says so |

- **(S-9a)** Every ancestor of those three is 0755 or 0777, so they need no group membership to read. `temp1/`
  holds a **second** full copy set (`.backup`, `.sqlite`, `-shm`, a 112 MB `-wal`) at 0600 and `temp/` a third
  112 MB `-wal`; neither directory is named in §4.1. The same-named files under
  `/home/pcalnon/.config/Duplicati/` are mode-loose but **path-protected** — that profile is 0700 — so a
  `chmod 0600` sweep scoped to *them* fixes nothing that was broken.""",
)

# =====================================================================================
# Lane A (product) — the four product corrections
# =====================================================================================

edit(
    "r2-unknown-option",
    """# Unknown options: this wrapper does NOT validate option names against the server's own list.
# A --option line in .env that the server does not know is passed through, and 2.4.0.0 exits
# on an unrecognised server option rather than ignoring it -- so a typo in .env is a start
# failure, not a silent misconfiguration. That is the intended direction (fail closed), but it
# means .env is part of the start path and a bad line takes the service down: change it with
# --print-command first. (Lane B2 C6.)""",
    """# Unknown options: this wrapper does NOT validate option names against the server's own list,
# and NEITHER DOES THE SERVER. 2.4.0.0's CommandLineArgumentValidator.ValidateArguments logs
# "Unknown option supplied: <name>" as a WARNING and continues; the only non-zero exits in
# Server/Program.cs are 100 (unhandled exception) and 102/103 (--webservice-password-init).
# So a typo in .env is a SILENT MISCONFIGURATION, not a start failure: the service comes up
# with the option ignored, and the only trace is a warning. This fails OPEN, which is the
# opposite of what this contract wants, and it is what let the glued --daemon-opts word through
# on 09-20 (section 4.3 item 9) while the server started on 8200.
# Two consequences: (1) verify every .env option name against `duplicati-cli help advanced`
# and, for server-only names, against the string table of Duplicati.Server.Implementation.dll
# -- the spelling is `--webservice-token-duration`, hyphenated, even though the C# constant is
# OPTION_WEBSERVICE_TOKENDURATION, and a misspelling would be ignored rather than refused;
# (2) after any .env change, grep the journal for "Unknown option supplied" before calling the
# start good. AC-14 pins that grep. (Lane B2 C6, corrected by round 2 Lane A.)""",
)

edit(
    "r2-syscallfilter-rationale",
    """# @system-service excludes @privileged, which is where open_by_handle_at(2) lives.
# CAP_DAC_READ_SEARCH explicitly grants that call, and it opens ANY inode of a mounted
# filesystem by handle -- bypassing InaccessiblePaths= and TemporaryFileSystem= entirely.
# Path masking without a syscall filter is therefore not a boundary at all.""",
    """# @system-service does NOT exclude @privileged wholesale: 18 of @privileged's 53 calls are in
# its transitive closure (chown/fchown/lchown, capset, setfsuid, setgroups, setres*uid...),
# which is why `systemd-analyze security` prints a 0.2 "SystemCallFilter=~@privileged ...
# chown is allowed" row. That row is expected and is NOT evidence against this filter.
# What @system-service DOES exclude is open_by_handle_at(2) specifically: the closure allows
# name_to_handle_at (make a handle) and not open_by_handle_at (use one). That is the call
# CAP_DAC_READ_SEARCH explicitly grants, and it opens ANY inode of a mounted filesystem by
# handle -- bypassing InaccessiblePaths= and TemporaryFileSystem= entirely. Path masking
# without this filter is therefore not a boundary at all. Verified on systemd 259 by expanding
# the set transitively; a direct-member listing does not show it, because @system-service is
# mostly nested groups.""",
)

edit(
    "r2-serverutil-chain",
    """`duplicati-server-util`'s own authentication chain, for the record, because two lanes disagreed about it and
the source settles it (`Duplicati/CommandLine/ServerUtil/Connection.cs` at the 2.4.0.0 tag): a saved refresh
token, else a signin token minted from a server database that is both **readable and decryptable** (`jwt-config`
is an encrypted field, so this needs the settings key too), else `--password`, else
`Utility.ReadSecretFromConsole("Enter server password: ")` — a console prompt **does** exist; `help` simply
does not list it.""",
    """`duplicati-server-util`'s own authentication chain, for the record, because two lanes disagreed about it and
the source settles it (`Duplicati/CommandLine/ServerUtil/Connection.cs` at the 2.4.0.0 tag): a saved refresh
token; then, **only if `--password` was not given**, a signin token minted from a server database that is both
**readable and decryptable** (`Connection.cs:250-262` guards the whole branch with
`if (string.IsNullOrWhiteSpace(settings.Password))` and passes `settings-encryption-key` into
`GetDatabaseConnection`, so `jwt-config` being an encrypted field means this route needs the settings key);
then `--password`; then, if the password is still empty,
`Utility.ReadSecretFromConsole("Enter server password: ")` (`Connection.cs:304-305`). Two things follow that
an earlier reading had backwards. **`--password` does not come after the database branch — it pre-empts it**,
so supplying it means server-util never opens the database and needs no settings key at all. And the console
prompt, which **does** exist though `help` does not list it, is `Console.ReadKey(true)`
(`Library/Utility/Utility.cs:2167`): it throws *"Cannot read keys when either application does not have a
console or when console input has been redirected"* on any scripted, `systemd-run` or headless invocation —
reproduced against the installed binary. So the prompt is not a usable automation channel, which is the second
reason the in-process client is the fix.""",
)

edit(
    "r2-passwordinit-exit",
    """  otherwise — which means it must never sit in `DAEMON_OPTS`, because `Restart=on-failure` would loop it.""",
    """  otherwise. **Both** are non-zero, so under `Restart=on-failure` the *success* path loops too, not just the
  failure path — it must never sit in `DAEMON_OPTS`.""",
)

edit(
    "r2-gate-behaviours",
    """  "not at all": the gate is checked before argv is parsed, so the verdict does not depend on the argv bug. §7.3.2 sets 0700.""",
    """  "not at all": the gate is checked before argv is parsed, so the verdict does not depend on the argv bug. §7.3.2 sets 0700.

  **Two gate behaviours that decide whether a recovery step works**, measured on the installed 2.4.0.0 and
  recorded here because both fail in a misleading direction. (1) `duplicati-server-util` applies the gate and
  its refusal is **completely silent** — exit 1, zero bytes on stdout *and* stderr, before even the
  "Connecting to…" line. If a probe copy's directory is not 0700 owned by the invoking user or root, the
  command dies with no diagnostic at all; `chmod 0700` the copy directory first, or pass
  `--allow-insecure-datafolder`. (2) `duplicati-database-tool` does **not** apply the gate at all, despite
  advertising `--allow-insecure-datafolder` on every subcommand: it resolves the folder in
  `AccessMode.ProbeOnly`, which `DataFolderManager.cs` documents as "a no-op in ProbeOnly mode".
  `wipe-encryption --server-datafolder <0755 dir> --dry-run` runs normally with no override — so never read a
  successful `wipe-encryption` as evidence that a folder's permissions are acceptable to the **server**.""",
)


# =====================================================================================
# Lane B (actionability) — the runbook defects
# =====================================================================================

# --- D1: both A0 scripts must PARSE the credential file, never source it -------------
edit(
    "r2-a0-premise-parse",
    """set -euo pipefail
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
```""",
    """set -euo pipefail
ENV_FILE="${YAMAGUCHI_ENV_FILE:-${HOME}/.config/duplicati-backup/env}"
DEST="${YAMAGUCHI_DEST_URL:-file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi}"
# Temp index on ext4, NEVER tmpfs (rule 3): /tmp is tmpfs on this host.
WORKDIR="${YAMAGUCHI_WORKDIR:-${HOME}/.cache/yamaguchi-recovery}"
# --dbpath at a disposable COPY of the archived job index, NOT --no-local-db:
# util/ad-hoc/duplicati_drill_run.py records --no-local-db rebuilding the index from every
# dindex volume, ">30 minutes for a single small file here, without completing".
JOBDB="${YAMAGUCHI_JOB_DB:-/home/duplicati/.cache/root-data-folder-2026-09-22/BMXWPAOGLP.sqlite}"
[[ -r "${ENV_FILE}" ]] || { echo "no readable env file at ${ENV_FILE}" >&2; exit 2; }
[[ -s "${JOBDB}" ]] || { echo "no job index at ${JOBDB} (run P0 step 1's freeze first)" >&2; exit 2; }
install -d -m 0700 "${WORKDIR}"
TMPDB="$(mktemp -u "${WORKDIR}/a0-probe-XXXXXX.sqlite")"
cp -p "${JOBDB}" "${TMPDB}"

# The credential file is PARSED, never SOURCED. The live PASSPHRASE is UNQUOTED and carries
# '$', '&', '@', '#' and '^' (util/ad-hoc/2026-09-22_credential_file_shape.py reports
# dot-sourceable=NO), so `set -a; . "${ENV_FILE}"` under `set -u` dies
# "<fragment>: unbound variable" -- printing a piece of the passphrase to stderr, the exact
# channel section 6 exists to close -- before duplicati-cli is ever reached; and the '&' makes
# the shell run the tail of the value as a command. util/ad-hoc/yamaguchi_build_job.py:57-63
# already parses this file the right way.
PASSPHRASE="$(
    python3 - "${ENV_FILE}" <<'PY'
import re, sys
for line in open(sys.argv[1], encoding="utf-8"):
    m = re.match(r"^\\s*(?:export\\s+)?PASSPHRASE=(.*)$", line.rstrip("\\n"))
    if m and m.group(1).strip():
        sys.stdout.write(m.group(1).strip().strip('"').strip("'"))
        break
else:
    sys.exit("FATAL: no PASSPHRASE in " + sys.argv[1])
PY
)"
[[ -n "${PASSPHRASE}" ]] || { echo "no PASSPHRASE parsed from ${ENV_FILE}" >&2; exit 2; }
export PASSPHRASE
# PASSPHRASE reaches duplicati-cli through the ENVIRONMENT, never through argv.
duplicati-cli list "${DEST}" --version=0 "--dbpath=${TMPDB}" '*duplicati-server-db*'
unset PASSPHRASE
rm -f "${TMPDB}" "${TMPDB}-wal" "${TMPDB}-shm" "${TMPDB}-journal"
```""",
)

edit(
    "r2-a0-restore-parse",
    """set -euo pipefail
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
```""",
    """set -euo pipefail
ENV_FILE="${YAMAGUCHI_ENV_FILE:-${HOME}/.config/duplicati-backup/env}"
DEST="${YAMAGUCHI_DEST_URL:-file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi}"
OUT="${1:?usage: $0 <restore-directory>}"
SNAP_PATH='/home/pcalnon/.local/state/duplicati-server-db/Duplicati-server.sqlite'
WORKDIR="${YAMAGUCHI_WORKDIR:-${HOME}/.cache/yamaguchi-recovery}"
JOBDB="${YAMAGUCHI_JOB_DB:-/home/duplicati/.cache/root-data-folder-2026-09-22/BMXWPAOGLP.sqlite}"
[[ -r "${ENV_FILE}" ]] || { echo "no readable env file at ${ENV_FILE}" >&2; exit 2; }
[[ -s "${JOBDB}" ]] || { echo "no job index at ${JOBDB} (run P0 step 1's freeze first)" >&2; exit 2; }

# The restored file is a CLEARTEXT server database carrying the job passphrase (rule 8,
# Appendix C item 3). It must not land inside the backup Source, or the next run archives it --
# the S-7 shape, and the rule P4 step 1 states for the analogous tar.
case "$(readlink -f "${OUT}")/" in
    /home/pcalnon/*) echo "refusing: ${OUT} is inside the backup Source" >&2; exit 2 ;;
esac
install -d -m 0700 "${OUT}"
install -d -m 0700 "${WORKDIR}"
TMPDB="$(mktemp -u "${WORKDIR}/a0-restore-XXXXXX.sqlite")"
cp -p "${JOBDB}" "${TMPDB}"

# PARSED, never SOURCED -- see the premise-check script for why (dot-sourceable=NO).
PASSPHRASE="$(
    python3 - "${ENV_FILE}" <<'PY'
import re, sys
for line in open(sys.argv[1], encoding="utf-8"):
    m = re.match(r"^\\s*(?:export\\s+)?PASSPHRASE=(.*)$", line.rstrip("\\n"))
    if m and m.group(1).strip():
        sys.stdout.write(m.group(1).strip().strip('"').strip("'"))
        break
else:
    sys.exit("FATAL: no PASSPHRASE in " + sys.argv[1])
PY
)"
[[ -n "${PASSPHRASE}" ]] || { echo "no PASSPHRASE parsed from ${ENV_FILE}" >&2; exit 2; }
export PASSPHRASE
duplicati-cli restore "${DEST}" "${SNAP_PATH}" \\
    --version=0 "--dbpath=${TMPDB}" "--restore-path=${OUT}"
unset PASSPHRASE
rm -f "${TMPDB}" "${TMPDB}-wal" "${TMPDB}-shm" "${TMPDB}-journal"
echo "restored under ${OUT}; verify it with the forensics script before installing it."
echo "SHRED ${OUT} once step 8 has installed the database -- it is cleartext key material."
```""",
)

edit(
    "r2-step0-prose",
    """Confirm Procedure A0's premise with one read-only command, in a subshell so nothing reaches the shell history
and the passphrase never touches argv:""",
    """Confirm Procedure A0's premise with the read-only script below. **Run P0 step 1's freeze first** — it
needs the job index that step copies aside, because it points `--dbpath` at a throwaway copy of it rather
than using `--no-local-db`, which on this destination rebuilds the index from all 877 dindex volumes
(`util/ad-hoc/duplicati_drill_run.py`: ">30 minutes for a single small file here, without completing"). The
passphrase is **parsed** out of the credential file, never `.`-sourced, and never touches argv:""",
)

edit(
    "r2-step0-expect",
    """The 09-18 14:00Z fileset **is** version 0 (it is the newest), which is why `--version=0` is used rather than
a `--time=` string whose parsing would be one more thing to get wrong. Expect the snapshot path
`home/pcalnon/.local/state/duplicati-server-db/Duplicati-server.sqlite` in the listing. If it is absent, A0
is out and the decision tree starts at step 3.""",
    """The 09-18 14:00Z fileset **is** version 0 (it is the newest), which is why `--version=0` is used rather than
a `--time=` string whose parsing would be one more thing to get wrong — **but that is true only until the
first post-recovery backup runs**, after which version 0 is the new one. Assert the expected dlist name
before relying on it. Expect the snapshot path
`home/pcalnon/.local/state/duplicati-server-db/Duplicati-server.sqlite` in the listing. If it is absent, A0
is out and the decision tree starts at step 3.

One expected value to know in advance, because it will otherwise look like a failure: the snapshot **inside**
the 09-18 14:00Z fileset was taken at 13:45 UTC, *before* that day's backup, so its `LastBackupDate` reads
**`20260917T140000Z`**, not `20260918T140000Z`. (Appendix A.2's `20260918T140000Z` is the 09-20 on-disk
snapshot, a different file.) "Only `LastBackupDate` is one day stale" is measured from the 09-18 run.""",
)

# --- D3/D4/D11: the probe -----------------------------------------------------------
edit(
    "r2-probe-trykey",
    """try_key() {
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
echo "negative control rejected the random key (good)\"""",
    """# The key is delivered by a 0600 EnvironmentFile, NEVER on argv: `-p Environment=<secret>` is
# world-readable in /proc/*/cmdline and is recorded by systemd -- the same exposure 7.3.6 bans
# for `duplicati-server-util --password`. (A `SETTINGS_ENCRYPTION_KEY=` prefix on `timeout`
# would also be dead: a transient unit does not inherit the caller's environment.)
try_key() {
    local key="$1" label="$2" log="${WORK}/probe-${2}.log" envf="${WORK}/probe-${2}.env" rc=0
    printf 'probing: %s\\n' "${label}" >&2
    ( umask 077; printf 'SETTINGS_ENCRYPTION_KEY=%s\\n' "${key}" > "${envf}" )
    chown duplicati:duplicati "${envf}"
    set +e
    timeout -k 10 90 \\
        systemd-run --wait --quiet --collect --pipe \\
            --uid=duplicati \\
            -p InaccessiblePaths=/mnt/Backups \\
            -p InaccessiblePaths="${SRCDIR}" \\
            -p "EnvironmentFile=${envf}" \\
            /usr/bin/duplicati-server "--server-datafolder=${WORK}" \\
            --webservice-interface=loopback "--webservice-port=${PORT}" \\
            --webservice-disable-signin-tokens > "${log}" 2>&1
    rc=$?
    set -e
    shred -u "${envf}" 2> /dev/null || rm -f "${envf}"
    # A verdict needs a POSITIVE signal for BOTH outcomes. A harness failure -- timeout 124, a
    # systemd-run property this host rejects, a missing binary -- is neither, and must never
    # read as "rejected": that is the direction that discards a CORRECT key and routes the
    # recovery to A2 (destructive) or B (new job id, every downstream default wrong).
    if grep -q 'Server has started' "${log}"; then return 0; fi
    if grep -qE 'SettingsEncryptionKeyMismatchException|does not match current key' "${log}"; then return 1; fi
    echo "INDETERMINATE (${label}): rc=${rc}; neither 'Server has started' nor a Mismatch in ${log}" >&2
    echo "The probe did not run. Fix the harness before reading any verdict." >&2
    exit 5
}

# (3) negative control -- meaningful only because try_key now distinguishes "rejected" from
# "did not run".
if try_key "$(head -c 32 /dev/urandom | base64 | tr -d '\\n')" control; then
    echo "REFUSING: a RANDOM key was accepted -- this probe is not discriminating." >&2
    exit 4
fi
echo "negative control rejected the random key (good)\"""",
)

edit(
    "r2-probe-sqlite3",
    """[[ "$(id -u)" -eq 0 ]] || { echo "run with sudo" >&2; exit 2; }
[[ -s "${SRCDIR}/Duplicati-server.sqlite" ]] || { echo "source DB missing under ${SRCDIR}" >&2; exit 2; }""",
    """[[ "$(id -u)" -eq 0 ]] || { echo "run with sudo" >&2; exit 2; }
# sqlite3 is NOT installed on this host by default. Without it the two containment queries
# below return EMPTY, and the refusal then misreports a query failure as "the copy is
# cleartext" -- which sections 4.2, 5.4 and 11 have primed the operator to read as "the second
# key-free recovery source has been found". Fail loudly instead.
command -v sqlite3 > /dev/null || {
    echo "sqlite3 is not installed; containments (2) and (4) cannot run. Install it first." >&2
    exit 2
}
[[ -s "${SRCDIR}/Duplicati-server.sqlite" ]] || { echo "source DB missing under ${SRCDIR}" >&2; exit 2; }""",
)

edit(
    "r2-probe-refusal",
    """if [[ "${flag}" != "True" || "${url}" != "enc-v1:" ]]; then
    echo "REFUSING: copy is not encrypted (encrypted-fields='${flag}', TargetURL prefix='${url}')." >&2
    echo "A probe against an unencrypted copy accepts ANY key and poisons the copy." >&2
    exit 3
fi""",
    """if [[ "${flag}" != "True" || "${url}" != "enc-v1:" ]]; then
    echo "REFUSING: the copy does not read as encrypted (encrypted-fields='${flag}', TargetURL prefix='${url}')." >&2
    echo "EMPTY values mean the QUERY failed, not that the copy is cleartext -- check the copy." >&2
    echo "A probe against a genuinely unencrypted copy accepts ANY key and poisons the copy." >&2
    exit 3
fi""",
)

edit(
    "r2-probe-srcdir",
    """SRCDIR="${SRCDIR:-/usr/lib/duplicati/data}\"""",
    """# Default to the P0 step 1 DATA-FOLDER FREEZE, not the live folder: the step that introduces
# this script says "the copy from step 1", and a default pointing at /usr/lib/duplicati/data
# would silently re-copy from the original instead.
SRCDIR="${SRCDIR:-/home/duplicati/.cache/root-data-folder-2026-09-22}\"""",
)

edit(
    "r2-hashprobe-invocation",
    """so run `util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py` against the **copy** from step 1 (usage in its docstring). It needs no root, no server and no live database, and it has already excluded every candidate this design named (§5.4): the committed literal with eleven shell-mangling variants, both
   passphrases, and the three commented key spellings. **Feed any new candidate ALONE on stdin** — the probe keeps only the last uncommented `SETTINGS_ENCRYPTION_KEY=` line it reads, so a concatenated file silently discards one. Write the candidate with `set +o history; read -rs key; install -m 0600 /dev/stdin <file> <<<"$key"` — **never** `printf '%s' '<value>' > file` at a root prompt, which is the same history channel §6 exists to close.""",
    """so run `util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py` against the **data-folder freeze** from step 1. It takes three argument groups — a wrapper path, a `.env` path, then one or more `label=path` database specs — and reads a candidate `.env` on **stdin**, so the invocation is:

   ```text
   sudo cat <candidate-file> | sudo python3 util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py \\
       scripts/duplicati-wrapper.bash ~/.config/duplicati-backup/env \\
       frozen=/home/duplicati/.cache/root-data-folder-2026-09-22/Duplicati-server.sqlite
   ```

   It needs **root** — the freeze lives under `/home/duplicati/.cache`, mode 0700 `duplicati` — but no server and no live database, and it has already excluded every candidate this design named (§5.4): the committed literal with eleven shell-mangling variants, both passphrases, and the three commented key spellings. **A new candidate must be written as a `SETTINGS_ENCRYPTION_KEY=<value>` line, not as a bare value**: stdin is parsed as a `.env`,
   so a bare-value file loads **no** candidate and prints a vacuous `NONE of the candidates/variants`. Feed it alone — only the **last** uncommented `SETTINGS_ENCRYPTION_KEY=` line survives. Write it with `set +o history; read -rs key; printf 'SETTINGS_ENCRYPTION_KEY=%s\\n' "$key" | sudo install -m 0600 /dev/stdin <file>; unset key` — **never** `printf '%s' '<value>' > file` at a root prompt, which is the same history channel §6 exists to close.""",
)

# --- D5: P0.5 ordering and the literal chown ----------------------------------------
edit(
    "r2-p05-chown",
    """1. **`sudo chown -R root:root /usr/lib/duplicati`** except `data/` (kept as the frozen copy until P4) — **before P0 step 3 runs any Duplicati tool**. The directory is duplicati-owned 0755 with no sticky bit, so the service user can replace `duplicati-cli`, `duplicati-database-tool` or `duplicati-server`, all of which root and `pcalnon` execute during recovery. Also `chown root:root /etc/default/duplicati` (today `duplicati:duplicati` 0644 — the service user
   can rewrite its own next argv), and remove `/home/duplicati/bin/` entirely: it holds only the symlink into a developer checkout that D-6 replaces with an installed copy.""",
    """1. **Return `/usr/lib/duplicati` to `root:root`, `data/` excepted** (it is the frozen copy until P4) — **before P0 step 0(c), which is the first command that executes a Duplicati binary**. `/usr/bin/duplicati-*` are symlinks into a `duplicati:duplicati` 0755 directory with no sticky bit, so the service user can rename any entry aside and drop in its own `duplicati-cli`, `duplicati-database-tool` or `duplicati-server` — all of which root and `pcalnon`
   execute during recovery (§4.1 note b). A plain `chown -R` would take `data/` with it, so exclude it explicitly rather than writing an instruction with no literal reading:

   ```text
   sudo chown root:root /usr/lib/duplicati
   sudo find /usr/lib/duplicati -mindepth 1 -maxdepth 1 ! -name data -exec chown -R root:root {} +
   ```

   Expect 97 directories to change owner and 21 (the `runtimes/` subtree and ten `licenses/<package>/`
   directories) to be no-ops — they were never chowned in the first place (§4.1 note b), so "nothing changed"
   is the *expected* result for those, not evidence the command failed. Also `chown root:root
   /etc/default/duplicati` (today `duplicati:duplicati` 0644 — the service user can rewrite its own next
   argv), and remove `/home/duplicati/bin/` entirely: it holds only the symlink into a developer checkout that
   D-6 replaces with an installed copy.""",
)

edit(
    "r2-p0-step0-p05-pointer",
    """**0. Owner gates — none of these is a session's to decide.**""",
    """**Run P0.5 items 1 and 2 before anything in P0.** They take minutes, depend on nothing in the recovery, and
item 1 closes the path by which the service user controls the very binaries steps 0(c), 3, 4 and 7 execute.
P0.5 is printed *after* P0 only because it also carries work that follows the recovery; an operator working
top to bottom would otherwise run the recovery with that path open.

**0. Owner gates — none of these is a session's to decide.**""",
)

# --- D6: place the recovered database ------------------------------------------------
edit(
    "r2-step8-place",
    """8. **Common to A0, A, A2 and B — move the index and re-point `DBPath` BEFORE the first run.**""",
    """8. **Common to A0, A, A2 and B — place the database, move the index, re-point `DBPath`, all BEFORE the first run.** **First, place the recovered database.** A0 and A2 produce a *file*, not a folder; Procedure A produced the folder in step 5 and B created one in step 7. For **A0** and **A2**:

   ```text
   sudo install -d -m 0700 -o duplicati -g duplicati /home/duplicati/.config/Duplicati
   sudo install -m 0600 -o duplicati -g duplicati \\
        <recovered>/Duplicati-server.sqlite /home/duplicati/.config/Duplicati/Duplicati-server.sqlite
   ```

   `<recovered>` is the A0 restore path (step 4) or the wiped copy (step 6). Do **not** copy a `-wal`/`-shm`
   sibling alongside it: the recovered file is a clean, closed database, and a stale WAL from another process
   would be replayed over it. Verify with the forensics script *after* the copy, as the `duplicati` user.
   Without this, A0 and A2 end with the recovered database still in a scratch directory and the server
   starting against the empty folder the installer created — `0 backups`, exactly where the arc began.""",
)

# --- D7: alerting before the pre-run work --------------------------------------------
edit(
    "r2-step9-credential",
    """9. **Before the first run.** The job still carries""",
    """9. **Re-arm alerting FIRST — every command in step 10 goes through the API client.** Set the UI password (§7.3.6, and read its "if the root-era password is unknown" paragraph *before* you need it), write `~/.config/duplicati-backup/web-credential` (0600), and re-point **both** API clients at it (§7.6). `util/ad-hoc/yamaguchi_server_api.py:41` hard-codes the primary checkout's `.env`, whose value §6 S-5 records as stale, so a run order that pauses the
   scheduler first and creates the credential afterwards makes step 10's `pause` 401 — and `resume` is what fires the overdue backup. Land the client changes (the credential path **and** the new `pause`/`resume` subcommands) in the same PR as §7.6's re-pointing, before P0 runs. Redeploy the watchdog with `--backup-id <id>`; confirm the next 12:00 fire reads `OK`.
10. **Before the first run.** The job still carries""",
)

edit(
    "r2-step10-old",
    """10. **Re-arm alerting — before the acceptance checks, not after.** Set the UI password (web UI), write `~/.config/duplicati-backup/web-credential` (0600), and re-point **both** API clients at it (§7.6). AC-2 and AC-9 run through those clients, so a run order that proves the job first and creates the credential afterwards makes them fail 401 — today's watchdog symptom, reproduced by the plan itself. Redeploy the watchdog with `--backup-id <id>`; confirm the
    next 12:00 fire reads `OK`.
11. **Prove it.** `AC-2`, then one backup run (`AC-3`), then the two restore drills (`AC-4`), then `AC-12`.""",
    """11. **Prove it.** `AC-2`, then one backup run (`AC-3`), then the two restore drills (`AC-4`), then `AC-12` and `AC-13`. `AC-6` cannot be proved here — it becomes provable only when the snapshot lane is re-pointed (P0.5 item 2), and `AC-1` needs 24 h.""",
)

edit(
    "r2-step10-guard",
    """add `--run-script-before-required` (§7.5), then `resume` and **sample `serverstate` again**.""",
    """add `--run-script-before-required` (§7.5), then `resume` and **sample `serverstate` again** (the credential this needs was created in step 9).""",
)

edit(
    "r2-guard-dryrun",
    """Before `resume`, dry-run the guard as the service user — `sudo -u duplicati DUPLICATI__REMOTEURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi /usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash; echo $?` — and require 0: it is
   `--run-script-before-**required**`, so a missing or failing guard aborts the first backup, which `resume` fires immediately.""",
    """Before `resume`, dry-run the guard as the service user, with `env` rather than a bare `VAR=value` prefix (sudoers refuses the prefix under the default `env_reset` with no `setenv`) and with the URL read **from the job** rather than typed:

   ```text
   sudo -u duplicati env \\
     DUPLICATI__REMOTEURL="$(python3 util/ad-hoc/yamaguchi_server_api.py export <id> \\
       | python3 -c 'import json,sys; print(json.load(sys.stdin)["Backup"]["TargetURL"])')" \\
     /usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash; echo "guard exit=$?"
   ```

   Require exit 0: it is `--run-script-before-**required**`, so a missing or failing guard aborts the first backup, which `resume` fires immediately. A **hand-typed** URL would make the guard's `TargetURL` comparison compare the operator's own string with itself — vacuous, and it is the one check §7.5 item 6 says the guard exists for.""",
)

# --- D8: the snapshot lane -----------------------------------------------------------
edit(
    "r2-p05-snapshot",
    """2. **Install the snapshot timer's script as a root-owned copy** under `/usr/local/lib/duplicati/` and add `ProtectSystem=strict` to `yamaguchi-server-db-snapshot.service`. It runs as **root** today with `ExecStart` naming the primary checkout, so `sys.path[0]` is pcalnon-writable and every branch switch changes what root executes at 13:45 UTC (§7.7).""",
    """2. **Install the snapshot timer's script as a root-owned copy** under `/usr/local/lib/duplicati/` and add `ProtectSystem=strict` to `yamaguchi-server-db-snapshot.service`. It runs as **root** today with `ExecStart` naming the primary checkout, so `sys.path[0]` is pcalnon-writable and every branch switch changes what root executes at 13:45 UTC (§7.7). In the **same installed copy**, re-point `SRC` to
   `/home/duplicati/.config/Duplicati/Duplicati-server.sqlite`, and **stop the timer** (`systemctl stop yamaguchi-server-db-snapshot.timer`) until P0 step 8 has placed the recovered database; restart it only then. Leaving it pointed at `/usr/lib/duplicati/data` means every 13:45 UTC fire copies the **abandoned** database — the one encrypted under the unidentified 09-18 key — over `~/.local/state/duplicati-server-db/` and into the 14:00 UTC fileset, which
   silently destroys Procedure A0's own source for any later re-run and makes AC-6 unprovable until P2. Note also that after this step the unit no longer executes the repository file, so a later repository edit plus `daemon-reload` changes nothing: move changes into production by re-running the installer.""",
)

edit(
    "r2-p2-snapshot",
    """3. Re-point `yamaguchi_server_db_snapshot.py` (§7.7) and redeploy the system timer; confirm the next 13:45 UTC snapshot reads the new path.""",
    """3. Confirm the snapshot lane: the **installed** copy under `/usr/local/lib/duplicati/` (not the repository file — P0.5 item 2 made the unit execute the copy) reads the new data folder, the timer is running again, and the next 13:45 UTC snapshot lands with a fresh mtime. **AC-6 is a P2 criterion**, not a P0 one, for exactly this reason.""",
)

# --- D9: the unknown root-era UI password --------------------------------------------
edit(
    "r2-uipassword-route",
    """Remote control and the cloud report URL stay as the owner left them (deferred item) — but the report URL's
bearer JWT is a secret carried by every database copy (S-8).""",
    """**If the root-era UI password is not known, none of the routes above applies** — and this is not a corner
case: Procedures A0, A and A2 all recover a database whose `server-passphrase`/`-salt` hashes survive
(`wipe-encryption` does not clear them, §8 step 6), so the server does **not** consider the password
autogenerated, `--webservice-password-init` refuses it with exit 103, and the argv routes are banned. The
recovery is to clear the stored hash **on the copy, before step 8 installs it**, so the server treats it as
autogenerated again: with the server stopped,
`DELETE FROM Option WHERE BackupID=-2 AND Name IN ('server-passphrase','server-passphrase-salt','server-passphrase-trayicon','server-passphrase-trayicon-hash');`
then `--webservice-password-init` on a single hand start. Without this, P0 step 9 is unreachable for three of
the four procedures, and step 10, AC-2, AC-5, AC-9 and AC-13 all sit behind it.

Remote control and the cloud report URL stay as the owner left them (deferred item) — but the report URL's
bearer JWT is a secret carried by every database copy (S-8).""",
)

# --- D10/D12: the preamble ------------------------------------------------------------
edit(
    "r2-preamble-decisions",
    """Phases are ordered; nothing in a later phase is a precondition of an earlier one — **but that is true of
phases, not of decisions**: P0 applies the recommendations of D-1 (credstore + `--require-db-encryption-key`),
D-4 (`AmbientCapabilities`), D-6 (installed copy) and D-9 (loopback) before the owner has ruled on any of
them. Either rule those four first, or accept that P0 applies them **provisionally** and a contrary ruling
means re-installing the unit. Step 0 makes that explicit.""",
    """**Nine of the paths below do not exist yet.** §8 names `util/install_duplicati_service.bash`,
`util/yamaguchi-pre-backup-guard.bash`, `util/systemd/duplicati.{service,default}`,
`util/ad-hoc/2026-09-22_confirm_a0_premise.bash`, `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash`,
`util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash`,
`util/ad-hoc/2026-09-21_backup_destination_permissions.bash`, `util/juniper-backup-scheduled.bash` and
`util/install_juniper_backup_timer.bash` — all of which exist today only as tagged blocks in this document.
**P0 step −1 is to land them**, extracted with `util/ad-hoc/2026-09-21_lint_design_snippets.py` (Appendix B
maps block → path) and reviewed in a PR, not pasted onto a root prompt during the recovery. `sqlite3` and
`gitleaks` are **not installed** on this host either; step 3 needs the first and AC-8 the second.

Phases are ordered; nothing in a later phase is a precondition of an earlier one — **but that is true of
phases, not of decisions**: P0 applies the recommendations of D-1 (credstore + `--require-db-encryption-key`),
D-4 (`AmbientCapabilities`), D-6 (installed copy), D-9 (loopback) **and D-14** (the §7.3.2 unit sets
`UMask=0007`, the group-write value, while D-14 recommends the read-only `0027`) before the owner has ruled on
any of them. **D-2 is a sixth**: P0 step 11 runs a full backup under the very passphrase D-2 asks whether to
retire, and P1 step 5 re-decides it afterwards. Either rule those six first, or accept that P0 applies them
**provisionally** — a contrary ruling on D-1/D-4/D-6/D-9/D-14 means re-installing the unit, and a contrary
ruling on D-2 means the first post-recovery fileset is written under a passphrase that is then replaced. Step
0 makes that explicit.""",
)

edit(
    "r2-step0a",
    """(a) Rule D-1, D-4, D-6, D-9, or record that P0
applies their recommendations provisionally.""",
    """(a) Rule D-1, D-4, D-6, D-9 **and D-14**, decide whether
D-2 is re-decided before or after the first run, or record that P0 applies their recommendations
provisionally.""",
)

# --- D13: shred the A0 restore directory ---------------------------------------------
edit(
    "r2-a0-shred",
    """   `Backup` id 2 `Yamaguchi`, 2 `Source` rows, 45 `Filter` rows, and a **cleartext** `TargetURL` (no
   `enc-v1:` prefix). Only `LastBackupDate` is one day stale. Then install it as the data folder per step 8.""",
    """   `Backup` id 2 `Yamaguchi`, 2 `Source` rows, 45 `Filter` rows, and a **cleartext** `TargetURL` (no
   `enc-v1:` prefix). Then install it as the data folder per step 8 — and afterwards **shred the restore
   directory**: `sudo find <restore-dir> -type f -exec shred -u {} + && sudo rmdir <restore-dir>`. Nothing
   later in this plan removes it, and until it is gone it is a cleartext copy of the passphrase on disk, which
   is the sink class §6's checklist exists to enumerate. The script refuses a restore path under
   `/home/pcalnon/` for the same reason: that is the backup Source, and a restore into it would archive the
   cleartext database on the next run (the S-7 shape).""",
)

# --- D15: the guard's unset list ------------------------------------------------------
edit(
    "r2-guard-unset",
    """unset DUPLICATI__passphrase SETTINGS_ENCRYPTION_KEY""",
    """# Both spellings: built-in names are upper-case, option-derived ones follow the option's own
# case, and an unset naming the wrong spelling silently does nothing. The report-URL bearer JWT
# is a credential too (S-8), not merely a URL.
unset DUPLICATI__passphrase DUPLICATI__PASSPHRASE \\
      DUPLICATI__additional_report_url DUPLICATI__ADDITIONAL_REPORT_URL \\
      SETTINGS_ENCRYPTION_KEY""",
)

# --- D19: T2 ---------------------------------------------------------------------------
edit(
    "r2-p3-runner",
    """1. **Fix the runner's mount root first.** Add the absolute-mount-root form to `util/juniper-backup.bash` (a `MEDIA_NAMES` entry beginning with `/` is taken as an absolute mount root) and have the scheduler and the runner read **one** mount-root setting. Until this lands, every "due" run the scheduler starts ends `FAILED runner rc=1` and step 2 cannot produce its own OK run (§4.5, §7.8).
2. Land `util/juniper-backup-scheduled.bash`, the four user units (timer, path, service, **failure**) and `util/install_juniper_backup_timer.bash`; install; enable; observe one SKIPPED (unplugged) and one OK (plugged) run; watch `systemctl --user status juniper-backup.path` for 30 s after the plug-in to confirm the `.path` unit is still active; class-1 drill (`util/ad-hoc/2026-08-26_backup_restore_drill.bash`).""",
    """1. **Fix the runner's mount root first — and install it.** Add the absolute-mount-root form to `util/juniper-backup.bash` (a `MEDIA_NAMES` entry beginning with `/` is taken as an absolute mount root) and have the scheduler and the runner read **one** mount-root setting. Note that the scheduler executes `~/.local/bin/juniper-backup.bash`, which **does not exist** — `~/.local/bin/` holds only the old lane's two scripts — so the repository fix cannot
   reach production until step 2's installer copies it there. Until both land, every "due" run ends `FATAL: runner missing` or `FAILED runner rc=1`, and step 2 cannot produce its own OK run (§4.5, §7.8).
2. Land `util/juniper-backup-scheduled.bash`, `util/install_juniper_backup_timer.bash` (it must copy the runner, the scheduler **and** the failure reporter into `~/.local/bin/`, as `util/install_duplicati_timer.bash` already does for the old lane), the three user units above **and** `juniper-backup-failure.service` — which must carry `Environment=DUPLICATI_STATE_DIR=%h/.local/state/juniper-backup` and
   `ExecStart=%h/.local/bin/duplicati-backup-failure.bash juniper-backup.service`, or it writes its record into the *duplicati* lane's `failures.log` and tails that lane's `last-run.status`, reproducing the very defect it exists to avoid. The reporter itself already takes the unit name as `$1` (`util/duplicati_backup_failure.bash:31`), so no reporter change is needed. Install; enable; observe one SKIPPED (unplugged) and one OK (plugged) run; watch
   `systemctl --user status juniper-backup.path` for 30 s after the plug-in to confirm the `.path` unit is still active; class-1 drill (`util/ad-hoc/2026-08-26_backup_restore_drill.bash`).""",
)

# --- D20: the .env port line is inert -------------------------------------------------
edit(
    "r2-env-port-inert",
    """# The settings encryption key is delivered by systemd (LoadCredential=) and must not be set
# here while the unit supplies it. For a hand run outside systemd, export it in the shell.
--webservice-port=8300""",
    """# The settings encryption key is delivered by systemd (LoadCredential=) and must not be set
# here while the unit supplies it. For a hand run outside systemd, export it in the shell.
#
# The --option line below is INERT under the unit as shipped: DAEMON_OPTS (precedence 3) also
# sets --webservice-port, and a later source wins for the same option name. It is kept as a
# worked example of the grammar, not as a live tunable -- changing it here changes nothing.
# Declaring one setting in two artifacts is exactly what principle 1 of section 7.1 forbids;
# when the port must change, change /etc/default/duplicati.
--webservice-port=8300""",
)

# =====================================================================================
# Lane B (actionability) — cross-reference integrity, acceptance criteria, §11, §12
# =====================================================================================

edit(
    "r2-status-line",
    """**Status**: VALIDATED (round 2) — consensus round 1 (six validators) and round 2 (four lanes) are
COMPLETE and **fully reconciled**: every Lane A1, A2, A3, B1, B2 and B3 correction is applied or
recorded as dissent in §11. Verbatim reports:
`JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md` (round 1) and
`JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md` (round 2).
§8 may now be executed — **P0 step 0 first** (the owner gates in §8's preamble), and nothing under
`/mnt/Backups/Ubuntu/` is deleted or moved except the one escrow copy named in P1 step 4.""",
    """**Status**: VALIDATED (round 2) — consensus round 1 (six validators) and round 2 (four lanes) have
both reported, and every finding is applied or recorded as dissent in §11. Verbatim reports:
`JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md` and
`JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md`.
**§8 is executable in this order and no other**: P0.5 items 1–2, then **P0 step −1** (land the nine
scripts §8 invokes — they exist today only as tagged blocks here), then **P0 step 0**'s owner gates,
then P0. Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved except the one escrow copy named
in P1 step 4.""",
)

edit(
    "r2-appendixC-ref",
    """> **STOP""",
    """> **STOP""",
    0,
)

edit(
    "r2-ac2-id",
    """| AC-2 | The job `Yamaguchi` exists with `TargetURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi`, 2 sources, 45 filters, schedule `1D` at 14:00 UTC, `--blocksize=1MB` | `python3 util/ad-hoc/yamaguchi_server_api.py status` and `export 2` |""",
    """| AC-2 | The job `Yamaguchi` exists with `TargetURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi`, 2 sources, 45 filters, schedule `1D` at 14:00 UTC, `--blocksize=1MB` | `python3 util/ad-hoc/yamaguchi_server_api.py status` and `export <id>` — **`<id>` is 2 only if P0 step 7 (Procedure B) did not assign another**; record the assigned id in the validation record and pass it here, to the census, to AC-5 and to the watchdog unit |""",
)

edit(
    "r2-ac6-p2",
    """| AC-6 | Snapshot lane reads the new data folder;""",
    """| AC-6 | **(A P2 criterion — not provable at the end of P0.)** Snapshot lane reads the new data folder;""",
)

edit(
    "r2-ac8-gitleaks",
    """the P0.5 gitleaks rule passes tree-wide |""",
    """the P0.5 gitleaks rule passes (note AC-8a) |""",
)

edit(
    "r2-ac12-gate",
    """| AC-12 | `systemd-analyze security duplicati.service` reports an exposure at or below the §7.3.2 unit's offline baseline (**5.2 MEDIUM** before the B3 directives) and no ✗ row beyond those the design accepts; the server completes AC-3 under every confinement directive the unit sets — one it cannot run under is removed **and recorded**, never silently (note AC-12a) | `systemd-analyze security`; journal of the first start; `systemd-run` trial on the probe copy first |""",
    """| AC-12 | `systemd-analyze security duplicati.service` reports an exposure **at or below 2.0** and no ✗ row outside the accepted set in note AC-12a; the server completes AC-3 under every confinement directive the unit sets — one it cannot run under is removed **and recorded**, never silently | `systemd-analyze security`; journal of the first start; a `systemd-run` trial against the **P0 step 1 data-folder freeze** first |""",
)

edit(
    "r2-ac12a-note",
    """- **(AC-12a)** The §7.3.2 unit adds `IPAddressDeny`, `RestrictAddressFamilies`, `SystemCallFilter`, `ProtectProc`, `ProcSubset`, `PrivateDevices`, `ProtectClock`, `ProtectHostname`, `ProtectKernelLogs` and `RestrictNamespaces` on top of that baseline, **none of which has been executed against 2.4.0.0 on this host** (open item O-3). Trial them with `systemd-run` against the probe copy before the live unit.""",
    """- **(AC-8a)** `gitleaks` is **not installed on this host**, so that half of the criterion can only run once P0.5 item 6 adds the pre-commit hook — until then AC-8 is the journal, syslog, `.env` and wrapper checks only, and says so.
- **(AC-12a)** Measured offline on the unit as designed: **1.7 OK**, against **5.2 MEDIUM** for the same unit with round 1's Lane B3 directives removed. That is why the gate is 2.0 and not 5.2 — a 5.2-shaped gate is passed by a unit with `IPAddressDeny`, `SystemCallFilter`, `ProtectProc`, `ProcSubset`, `PrivateDevices`, `ProtectClock`, `ProtectHostname`, `ProtectKernelLogs` and `RestrictNamespaces` **all deleted**, i.e. by exactly the silent drop this
  criterion exists to prevent. The run produces **15** ✗ rows; the accepted set is `AmbientCapabilities=`, `CapabilityBoundingSet=~CAP_(DAC_*|FOWNER|IPC_OWNER)`, `SystemCallFilter=~@privileged`, `SystemCallFilter=~@resources`, `RestrictAddressFamilies=~AF_UNIX`, `RestrictAddressFamilies=~AF_(INET|INET6)`, `PrivateNetwork=`, `PrivateUsers=`, `ProtectHome=`, `RootDirectory=/RootImage=`, `RemoveIPC=`, `MemoryDenyWriteExecute=`, `DeviceAllow=`,
  `IPAddressDeny=` and `UMask=` (the last pending D-14). The `~@privileged` row is a **set-wide** test and does not contradict §7.3.2's narrower, correct claim about `open_by_handle_at`. `MemoryDenyWriteExecute=` would break the .NET JIT and `PrivateUsers=` conflicts with `AmbientCapabilities=`, so neither is a candidate; `RemoveIPC=yes` is free and unclaimed. **None of the added directives has been executed against 2.4.0.0 on this host** (open item
  O-12) — trial them with `systemd-run` against the P0 step 1 freeze copy, not against a probe copy that only exists if step 3's confirmation probe was run.""",
)

edit(
    "r2-ac14",
    """| AC-13 | The job's `--run-script-before-required` equals""",
    """| AC-14 | After any `.env` or `DAEMON_OPTS` change, `journalctl -u duplicati.service --since <ts>` contains **zero** `Unknown option supplied` lines. 2.4.0.0 logs an unrecognised option as a warning and **continues** (§7.3.3), so a typo is a silent misconfiguration and this grep is the only thing that catches it | `journalctl -u duplicati.service --since <ts> \\| grep -c 'Unknown option supplied'` = 0 |
| AC-13 | The job's `--run-script-before-required` equals""",
)

edit(
    "r2-o3-renumber",
    """**None of the confinement directives above has been executed against 2.4.0.0 on this host.** That is
open item O-3, and AC-12 is what closes it:""",
    """**None of the confinement directives above has been executed against 2.4.0.0 on this host.** That is
open item **O-12** (this document continues the O-numbering of
`HANDOFF_2026-08-21_backup-systematization-design-arc.md`, which defines O-0…O-8; §11 lists O-12
and O-13), and AC-12 is what closes it:""",
)

edit(
    "r2-o11-renumber",
    """O-11 asks whether `SendStdOutToLogs` stores it verbatim.""",
    """**O-13** asks whether `SendStdOutToLogs` stores it verbatim.""",
)

edit(
    "r2-yam-filters",
    """which is inside the backup Source and matched by none of the 45
   filters (YAM §8.19.3)""",
    """which is inside the backup Source and matched by none of the
   filters (`JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md` §8.19.3 verified this against the **44** filters of that date; the job carries 45 today, and the one added since does not cover `.local/state/` either)""",
)

edit(
    "r2-step7-ac2",
    """**The rebuilt job is not id 2**: `sqlite_sequence` starts at 1, and the deployed watchdog, `yamaguchi_census.py`, AC-2, AC-5 and step 10 all default to 2.""",
    """**The rebuilt job is not id 2**: `sqlite_sequence` starts at 1, and the deployed watchdog, `yamaguchi_census.py`, AC-2 and AC-5 all default to 2 (step 9 already takes `--backup-id <id>` explicitly).""",
)

edit(
    "r2-section11",
    """**State of the record: round 1 delivered in full; reconciliation paused by the owner on 2026-09-21 before Lanes A1, B1, B2 and B3 were folded in.** The verbatim reports are archived in `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`; the five step reports the design was drafted from are in `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-STEP-REPORTS-RECORD.md`.""",
    """**State of the record: two rounds delivered and fully reconciled.** Round 1's six verbatim reports are
archived in `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`, round 2's four in
`JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md`, and the five step reports the
design was drafted from in `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-STEP-REPORTS-RECORD.md`.""",
)

edit(
    "r2-section11-iterations",
    """- **Iterations and what the last one changed**: one round. Lane A2's 15 and Lane A3's 12 corrections were applied to this revision (among them: §4.5, the udisks `/run/media` breakage of Tier 2; the wrapper's export allow-list and `.env` 0600 contract; libsecret-only secret provider; the run-script and file-backend citations; two defects in the snippet linter — an order-dependent verdict and a vacuous "no linter" pass — fixed). Lane A1 (13 disagreements, mostly counts and dates, plus 8 unrecorded facts),
  Lane B1 (17 findings; 3 refutations that change P0 — see the warning at the top of §8), Lane B2 (10 amputations, 22 actionability defects) and Lane B3 (20 security findings) are **not applied** — except the §4.1 unit row (A1 item 1), this section's adequacy and cannot-support entries, the §8 warning, §7.3.2's env override (B1 F11), P1 step 2's `chmod 0600` (B2 D15) and the AC-12 row, §0 instrument list and §12 file list (B2 D22). Round 2 (CON §4, briefed on the corrections) has not run.""",
    """- **Iterations and what each one changed**: **two rounds**, plus a third single-agent confirmation pass.
  **Round 1** (six agents, launched together, none seeing another's output) produced Lane A1's 13
  disagreements and 8 unrecorded facts, Lane A2's 15 and Lane A3's 12 corrections, Lane B1's 17 findings,
  Lane B2's 10 amputations and 22 actionability defects, and Lane B3's 20 security findings. A2's and A3's
  were applied on 2026-09-21; the owner then paused the arc, and **the remaining four lanes were reconciled
  on 2026-09-22** — the reconciliation is `util/ad-hoc/2026-09-22_reconcile_backup_design.py`, which rebuilds
  this document from its pristine blob so the edit set is re-derivable rather than remembered. The
  load-bearing changes: §5.4's candidate ordering replaced by the offline key-hash test (both named
  candidates excluded); Procedure A0 added ahead of A; `DBPath` re-pointing made common to all four
  procedures; the P0.5 bucket created; §7.3.2's confinement set; S-7 and S-8 added to §6; D-13 and D-14
  created.
  **Round 2** (four lanes — host, product, actionability, security — briefed only on the change list and the
  dissent) found that the reconciliation had introduced defects of its own, and it is worth recording which,
  because they are the reason a second round exists: both Procedure A0 scripts **could not run** (they
  `.`-sourced a credential file whose value is unquoted and carries `$ & @ # ^`, so `set -u` aborted them and
  echoed a fragment of the live passphrase to stderr — the very channel §6 exists to close); the step-3
  probe's negative control **could not fail** (a harness error read as "key rejected", the direction that
  discards a correct key); that same probe put the candidate key on `systemd-run`'s argv, **regressing** a
  round-1 fix; `sqlite3` is not installed, so the probe's containment queries returned empty and its refusal
  misreported a query failure as "the copy is cleartext"; §7.3.3 asserted that 2.4.0.0 **exits** on an
  unrecognised option when it warns and continues; Procedures A0 and A2 never placed their product; and the
  header claimed "fully reconciled" while this section still said four lanes were not applied. All are fixed
  above, and `util/ad-hoc/2026-09-22_apply_round2_corrections.py` carries the edit set.
  **Round 3** (one agent, briefed on round 2's corrections) confirmed them; §12 records what it changed.
- **A procedure failure in round 2, recorded because it changes how much weight its reports carry.** The
  orchestrator applied corrections to this document **while two lanes were still reading it**. The security
  lane saw it at three different sizes (1,882 → 2,126 → 1,882 lines between 02:31 and 02:47) and handled it
  correctly — it pinned a sha256 snapshot, anchored every citation by heading text, and reported two of its
  own intended findings as AGREE-with-corroboration rather than claiming them, because a concurrent edit had
  already closed them. Two consequences stand: any line number in the round-2 reports is void, and a finding
  of theirs may be stale in either direction. Where round 2's reports disagree with this document, the
  document was re-measured against the host before the disagreement was resolved — but the right fix is
  procedural, and `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` should say
  it: **freeze the artifact for the duration of a round.** Round 1 did not hit this because the owner paused
  the arc before reconciliation began.""",
)

edit(
    "r2-section11-dissent",
    """- **Unresolved dissent** (to be settled at reconciliation): the count of systemd specifier-rejection lines (A1: 23 `Invalid slot` = 22 `Failed to resolve specifiers` + 1 `… unit specifiers`; B1: 21 in the journal, 22 in syslog; the orchestrator's own count over 2026-09-18 → 09-21 13:00: 22 + 1 = 23 — the instruments differ in pattern and window, not in fact); B2 proposes `dropbox exclude add` for the escrow folder while B3 argues an exclusion leaves the cloud copy in place and calls for a permanent delete
  plus an account audit; B2 flags the alias-only section references (44 by an anchored `grep -o` on the design — 28 `YAM §`, 8 `PLAN §`, 3 `CON §`, 4 `DMG §`, 1 `GPG §`; an unanchored count also picks up the pattern names quoted in the counting sentence itself) against the name-every-document convention, which the header's **Companions** list (alias → filename, in the same document) is held to satisfy.""",
    """- **Unresolved dissent, and how each was settled or left open**:
  1. **The specifier-line count.** A1 measured 23 `Invalid slot` = 22 `Failed to resolve specifiers` + 1
     `… unit specifiers`; B1 measured 21 in the journal and 22 in syslog. Round 2 settled the *mechanism*
     rather than picking a number: the same grep returns **23** unscoped and **22** under
     `journalctl -u duplicati.service`, and `comm` names the single missing line — 2026-09-19T18:07:32,
     which systemd emitted before the reloaded unit was associated. Same event set, filters of different
     width. This document uses 23 and says which predicate produced it.
  2. **The escrow copy.** B2 proposed `dropbox exclude add`; B3 showed that selective-sync exclusion removes
     the local copy and leaves the cloud one. **B3 prevails**; B2's suggestion is not adopted, and S-4a says
     so explicitly so nobody re-proposes it.
  3. **`.env` mode — OPEN, owner decision.** B3 F-5 wants `0640 root:duplicati` (the wrapper only reads the
     file, and a file the plain `duplicati` uid can write is a code-injection path into a process holding
     `CAP_DAC_READ_SEARCH`); A3 #9 and B2 D15 want `0600 duplicati:duplicati`. This design **recommends
     F-5** and installs it that way pending a ruling (§7.3.5, P1 step 2).
  4. **The destination permission model — OPEN**, promoted to **D-14** (§10).
  5. **The `duplicati-server-util` prompt path.** B1 F12 said a prompt exists; B2 D5 said no prompt path is
     documented. **Settled for B1** from `ServerUtil/Connection.cs` at the 2.4.0.0 tag, and round 2
     reproduced it against the installed binary. Round 2 also corrected the *order* this document gave:
     `--password` **pre-empts** the database branch rather than following it, and the prompt is
     `Console.ReadKey(true)`, so it throws on any redirected stdin. The in-process client remains the fix
     either way — which is why the dissent never changed an action.
  6. **Alias-only section references — OPEN, orchestrator vs B2.** B2 flags the 44 `YAM §` / `PLAN §` /
     `CON §` / `DMG §` / `GPG §` references (28 / 8 / 3 / 4 / 1 by an anchored `grep -o`; an unanchored
     count also picks up the pattern names quoted in the counting sentence itself) against the
     name-every-document convention. The orchestrator holds that the header's **Companions** list binds each
     alias to a filename *within this document*, and that the convention targets summaries, PR bodies and
     handoffs. **Recorded, not adopted.** Round 2 did apply it in one place where the citation was also
     factually loose (§8 step 4's filter count).""",
)

edit(
    "r2-section11-cannot",
    """- **What the evidence cannot support**: which key encrypted the root database on 2026-09-18 21:03""",
    """- **Open items, and the observation that settles each** (this document's numbering continues
  `HANDOFF_2026-08-21_backup-systematization-design-arc.md`'s O-0…O-8):
  **O-12** — does 2.4.0.0 run under the §7.3.2 confinement set (`SystemCallFilter=@system-service`,
  `IPAddressDeny=any`, `ProtectProc=invisible`, `PrivateDevices=yes`, …)? A `systemd-run` trial against the
  P0 step 1 freeze copy, then `systemd-analyze security`. AC-12 closes it.
  **O-13** — does RunScript's `SendStdOutToLogs` store the guard's stderr verbatim, carrying an
  attacker-chosen stray-file name into the job log? Read `RunScript.cs`. A log-injection nuisance only.
- **What the evidence cannot support**: which key encrypted the root database on 2026-09-18 21:03""",
)

edit(
    "r2-section12",
    """| 2026-09-21 (later) | Handoff-validation Lane B1 corrections applied here: §8 warning (steps 3/5/7/9; Procedure A0; `wipe-encryption` does take `--server-datafolder` on the subcommand), §7.3.2 env override, P1 step 2 (0600), status line, §11. |""",
    """| 2026-09-21 (later) | Handoff-validation Lane B1 corrections applied here: the §8 STOP warning (Procedure A0; `wipe-encryption` does take `--server-datafolder` on the subcommand), §7.3.2's env override, P1 step 2's mode, the status line, §11. |
| 2026-09-22 | **Consensus round 1 reconciled in full.** Lanes A1, B1, B2 and B3 folded in; the §8 STOP warning removed and replaced by P0 step 0's owner gates; Procedure A0 added; P0 renumbered 0–11 with a new P0.5 bucket; §7.3.2's confinement set; S-7 and S-8; D-13 and D-14; AC-13. Applied by `util/ad-hoc/2026-09-22_reconcile_backup_design.py`. **Changed**: this file. **Added**: that script. |
| 2026-09-22 (later) | **Consensus round 2 reconciled** — four lanes (host, product, actionability, security); see §11 for what it found and `util/ad-hoc/2026-09-22_apply_round2_corrections.py` for the edit set. **Changed**: this file. **Added**: that script, `util/ad-hoc/2026-09-22_credential_file_shape.py`. |""",
)

# =====================================================================================
# Lane B (security) — R2B-1 … R2B-16
# =====================================================================================

# --- R2B-1 + R2B-7 + R2B-4: the unit's write scope and its mask ----------------------
edit(
    "r2b-readwritepaths",
    """ReadWritePaths=/home/duplicati /mnt/Backups/Ubuntu/Dropbox/Backups""",
    """# Scoped to the job's OWN destination, not the whole Backups/ tree. The parent holds
# _yamaguchi_keys/ (the passphrase escrow), _yamaguchi_frozen_20260826/ and ten
# .dlist.zip.gpg archives -- and every one of those directories is drwxrwx---
# pcalnon:duplicati with NO sticky bit, so a ReadWritePaths= on the parent would let this
# service read AND UNLINK the only key custody T1 and T1c have, with the deletion
# propagating to Dropbox. That would also contradict section 8's own "nothing under
# /mnt/Backups/Ubuntu/ is deleted or moved" rule. Duplicati needs write on the
# destination directory only.
ReadWritePaths=/home/duplicati /mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi""",
)

edit(
    "r2b-inaccessible",
    """InaccessiblePaths=-/etc/shadow -/etc/gshadow -/etc/ssh -/etc/credstore.encrypted -/var/lib/docker -/var/log -/root""",
    """# /etc/credstore IS masked -- see the note below for why that does not break
# LoadCredential=. The shadow- / gshadow- backups hold the previous generation of the same
# hashes; /run/log/journal is the volatile journal, which -/var/log does not cover; and
# /var/spool/cups is named by section 6's own sink checklist as a place the printed escrow
# sheet may still sit, which makes it the one entry whose contents may be a live passphrase.
InaccessiblePaths=-/etc/shadow -/etc/shadow- -/etc/gshadow -/etc/gshadow- -/etc/ssh -/etc/credstore -/etc/credstore.encrypted -/var/lib/docker -/var/log -/run/log/journal -/var/spool/cups -/root -/mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_keys""",
)

edit(
    "r2b-env-names",
    """Environment=DUPLICATI__DISABLE_UPDATE_CHECK=true
Environment=DUPLICATI__USAGE_REPORTER_LEVEL=none""",
    """# Disabled by the names the software ACTUALLY reads. DUPLICATI__DISABLE_UPDATE_CHECK and
# DUPLICATI__USAGE_REPORTER_LEVEL do NOT exist: a utf-8 AND utf-16le scan of all 1,443
# files under /usr/lib/duplicati finds neither in either encoding
# (util/ad-hoc/2026-09-22_duplicati_literal_scan.py). The generic DUPLICATI__ mapping is
# LOWER-case with '-' -> '_' (run-script-example.sh ll. 76-80); the upper-case forms in the
# product are hand-written specials, e.g. DUPLICATI__ALLOW_INSECURE_DATAFOLDER, which the
# same scan does find. An unread environment variable produces no "Unknown option supplied"
# line, so AC-14 structurally CANNOT catch a wrong name here -- which is why the option form
# below is also set, in /etc/default/duplicati, where AC-14 can see a typo.
Environment=AUTOUPDATER_Duplicati_SKIP_UPDATE=1
Environment=USAGEREPORTER_Duplicati_LEVEL=none
Environment=DO_NOT_TRACK=1""",
)

edit(
    "r2b-daemon-opts",
    """DAEMON_OPTS="--webservice-port=8300 --webservice-interface=loopback --server-datafolder=/home/duplicati/.config/Duplicati\"""",
    """DAEMON_OPTS="--webservice-port=8300 --webservice-interface=loopback --server-datafolder=/home/duplicati/.config/Duplicati --disable-update-check\"""",
)

edit(
    "r2b-egress-comment",
    """# No egress: the destination is file:// and Dropbox is a separate daemon, so the only
# legitimate network use is the update check and usage reporting, both disabled below.""",
    """# Socket egress is denied. It is NOT the only egress, and the reason usually given --
# "Dropbox is a separate daemon" -- is precisely why: ReadWritePaths= below opens a
# directory that the pcalnon Dropbox daemon replicates to a third party (S-4 records
# `dropbox filestatus` reading "up to date" for this tree). Anything this service writes
# into the destination LEAVES THE MACHINE, and IPAddressDeny= cannot see that path, because
# the upload is another process's socket. Scoping ReadWritePaths= to Yamaguchi/ and D-13's
# Dropbox root policy are therefore confinement controls, not hygiene. What this block does
# close is the server's own sockets: the update check and usage reporting.""",
)

edit(
    "r2b-credstore-note",
    """`/etc/credstore` is deliberately **absent** from `InaccessiblePaths=` — `LoadCredential=` must be able
to read the key from it, and masking it would break the start. That is not a gap that masking could close
anyway: with `CAP_DAC_READ_SEARCH` the service can read `/etc/credstore/*` directly, and
`LoadCredentialEncrypted=` would not help, because this host has no usable TPM2
(`systemd-analyze has-tpm2`: partial, no firmware/driver) and no `/var/lib/systemd/credential.secret`, so an
encrypted credential would bind to a host key readable with the same capability. The credentials directory is
also readable by every process in the unit, run-scripts included (`man systemd.exec`). Record it as a
residual; the fix that actually removes it is the secret-provider channel (§7.3.5), which never puts the key
on disk in a form the service can re-read.""",
    """`/etc/credstore` **is** masked, and an earlier revision of this paragraph argued the opposite on two
grounds that are both wrong. `LoadCredential=` is unaffected: `man systemd.exec` states that the credential
source *"must be accessible to the service manager, but **do not have to be directly accessible to the
unit's processes**"*, and that it is *"the **system service manager**"* that searches `/etc/credstore/`. The
manager reads the file and hands the unit a separate read-only copy at `$CREDENTIALS_DIRECTORY`. And the
"capability defeats masking" argument proves too much: §7.1 principle 3 already establishes that
`ProtectSystem=`/`ProtectHome=` are **mount flags, correctly not defeated by the capability**, and
`InaccessiblePaths=` is the same class of control — if it did not bind, the `/etc/shadow`, `/root` and
`/var/log` entries in this very unit would be decorative. Masking therefore costs nothing and removes the
service's capability-read of **every other service's** secrets in that directory.

What masking does **not** remove is the run-script's read of `$CREDENTIALS_DIRECTORY/settings-key` itself —
`man systemd.exec` makes the credentials directory readable by every process in the unit, run-scripts
included. That residual is real, it is a crossing in §7.3.1's table, and the only thing that removes it is the
secret-provider channel (§7.3.5), which never puts the key on disk in a form the service can re-read.
`LoadCredentialEncrypted=` would not help either: this host has no usable TPM2 (`systemd-analyze has-tpm2`:
partial, no firmware/driver) and no `/var/lib/systemd/credential.secret`, so an encrypted credential binds to
a host key readable with the same capability. **Verify the mask before trusting this paragraph** — it is part
of O-12's `systemd-run` trial, not a tested fact
(`sudo systemd-run --unit=credtest -p LoadCredential=t:/etc/credstore/<file> -p InaccessiblePaths=-/etc/credstore --pipe --wait /bin/sh -c 'wc -c < "$CREDENTIALS_DIRECTORY/t"'`).""",
)

edit(
    "r2b-o3-trial",
    """**None of the confinement directives above has been executed against 2.4.0.0 on this host.** That is
open item **O-12** (this document continues the O-numbering of
`HANDOFF_2026-08-21_backup-systematization-design-arc.md`, which defines O-0…O-8; §11 lists O-12
and O-13), and AC-12 is what closes it:""",
    """**None of the confinement directives above has been executed against 2.4.0.0 on this host.** That is
open item **O-12** (this document continues the O-numbering of
`HANDOFF_2026-08-21_backup-systematization-design-arc.md`, which defines O-0…O-8; §11 lists O-12
and O-13). Two directives are the likely failures, and the **order of the trial matters**.
`ProcSubset=pid` hides `/proc/meminfo`, `/proc/stat` and `/proc/sys/` from a **.NET** server
(`libcoreclr.so` is in the install, and CoreCLR sizes its GC from `/proc/meminfo`); `man systemd.exec`
says of that directive, in terms, that it *"is not suitable for most non-trivial programs"*. And
`RestrictAddressFamilies=` as written denies `AF_NETLINK`, which glibc's `getaddrinfo` and
`getifaddrs` use. **Run the trial first with `SystemCallErrorNumber=` unset**: the default `SIGSYS`
kill makes a blocked call a visible crash, whereas `EPERM` lets the runtime fall back silently — and
a silent fallback is how AC-12 passes on a degraded server, which is the vacuous-pass shape AC-12
exists to prevent. Switch to `EPERM` only after the trial has shown what the server actually needs,
and record that switch. AC-12 is what closes it:""",
)

edit(
    "r2b-mask-caveat",
    """RestrictNamespaces=yes""",
    """RestrictNamespaces=yes
# Bound, not boundary: a mount mask is escaped by resolving a path through
# /proc/<pid>/root of any process in another mount namespace that this uid may ptrace --
# i.e. any duplicati-uid process OUTSIDE this unit. ProtectProc=invisible does not stop it
# (man systemd.exec: it hides processes owned by OTHER users), and no special syscall is
# needed, just openat. So every `sudo -u duplicati` / `su - duplicati` session is, while it
# lives, a hole in the list below -- and section 7.3.1 prescribes exactly those as the
# administration model. Keep them transient; `usermod -s /usr/sbin/nologin duplicati` moves
# from P4 to P0.5a for this reason. What the mask reliably buys is protection from the
# service's own code paths and from accident, not from a deliberate same-uid adversary.""",
)

# --- R2B-5: the .env location ---------------------------------------------------------
edit(
    "r2b-env-location",
    """# Until the owner rules, install it 0640 root:duplicati.""",
    """# Until the owner rules, install it 0640 root:duplicati -- AND OUTSIDE THE DATA FOLDER.
# The mode only binds if the file leaves /home/duplicati/.config/Duplicati/: that directory
# must be 0700 duplicati:duplicati (Duplicati's own requirement) and the server must own it
# to write its database there, so the duplicati uid holds write on the DIRECTORY -- and in
# POSIX, delete permission comes from the parent directory, not the file. A 0640
# root:duplicati .env inside it is unlink-and-recreate-able by the service user, which
# defeats the whole point of the mode. Install it at /etc/duplicati/env in a 0755 root:root
# directory and point the wrapper's DUPLICATI_ENV_FILE default there. That also removes a
# second-order contradiction: section 7.3.2 requires files in the data folder to be 0600
# while this contract installs one at 0640.""",
)

# --- R2B-8 + R2B-9: the guard ---------------------------------------------------------
edit(
    "r2b-guard-positive",
    """# Both spellings: built-in names are upper-case, option-derived ones follow the option's own
# case, and an unset naming the wrong spelling silently does nothing. The report-URL bearer JWT
# is a credential too (S-8), not merely a URL.
unset DUPLICATI__passphrase DUPLICATI__PASSPHRASE \\
      DUPLICATI__additional_report_url DUPLICATI__ADDITIONAL_REPORT_URL \\
      SETTINGS_ENCRYPTION_KEY""",
    """# A DENYLIST CANNOT BE COMPLETE over a set the comment above calls "every job option,
# unfiltered" -- section 8 Procedure A2 alone names passphrase, jwt-config, pbkdf-config,
# remote-control-config and the ssl cert fields, and jwt-config is the server's JWT signing
# key (with it, mint any API token, then set --run-script-before to anything). Keep only what
# this guard uses, the same POSITIVE shape the wrapper uses in section 7.3.3.
_keep_op="${DUPLICATI__OPERATIONNAME:-unknown}"
_keep_url="${DUPLICATI__REMOTEURL:-}"
while IFS='=' read -r _n _; do
    case "${_n}" in DUPLICATI__*) unset "${_n}" ;; esac
done < <(env)
unset SETTINGS_ENCRYPTION_KEY _n _
# This does NOT put the settings key out of reach: $CREDENTIALS_DIRECTORY is inherited and
# /run/credentials/duplicati.service is a fixed path, readable by every process in the unit
# (man systemd.exec). Section 7.3.2 records that residual; the secret-provider channel
# (section 7.3.5) is what removes it. `unset` also does not rewrite /proc/<pid>/environ, so
# the original block persists for this process's lifetime -- no NEW exposure, but not the
# clean slate the word "unset" suggests.""",
)

edit(
    "r2b-guard-vars",
    """REMOTE_URL="${DUPLICATI__REMOTEURL:-}"
OPERATION="${DUPLICATI__OPERATIONNAME:-unknown}\"""",
    """REMOTE_URL="${_keep_url}"
OPERATION="${_keep_op}\"""",
)

edit(
    "r2b-guard-url-leak",
    """        *) fail "job TargetURL '${REMOTE_URL}' is not the guarded destination file://${DEST_DIR}" ;;""",
    """        # Print a SHAPE, never the URL. This branch fires exactly when the TargetURL has
        # been changed -- and a non-file:// backend URL routinely embeds credentials
        # (--auth-password is a real option across the Backend assemblies), so echoing it
        # would write a credential into the job log and from there into whatever
        # additional-report-url POSTs (S-8). The guard's own diagnostic must not be the leak.
        *) fail "job TargetURL does not match the guarded destination file://${DEST_DIR}; got scheme='${REMOTE_URL%%:*}' length=${#REMOTE_URL} sha256-8=$(printf '%s' "${REMOTE_URL}" | sha256sum | cut -c1-8)" ;;""",
)

edit(
    "r2b-guard-stray-name",
    """[[ -z "${stray}" ]] || fail "foreign entry in destination: ${stray}\"""",
    """# The stray's NAME is attacker-chosen and reaches the job log; sanitise it to a character
# class so it cannot inject newlines or control sequences (open item O-13 asks whether
# SendStdOutToLogs stores stderr verbatim -- this makes the answer not matter).
[[ -z "${stray}" ]] || fail "foreign entry in destination, name sanitised: $(printf '%s' "${stray##*/}" | LC_ALL=C tr -cd 'A-Za-z0-9._-' | cut -c1-64)\"""",
)

edit(
    "r2b-guard-prose",
    """deliberately named file can inject newlines into that log — a nuisance, not a vulnerability, and open item
**O-13** asks whether `SendStdOutToLogs` stores it verbatim.""",
    """deliberately named file could otherwise inject newlines into that log. Both the stray-file **name** and the
job's **`TargetURL`** are attacker-influenced strings, and a non-`file://` `TargetURL` can carry an
`auth-password` in the URL itself — so the guard prints a scheme, a length and a sha256 prefix for the URL,
and a character-class-sanitised basename for the stray. Open item O-13 (does `SendStdOutToLogs` store stderr
verbatim, and does the option-override parser see it?) stays open, but the guard no longer depends on its
answer.""",
)

# --- R2B-11: the fifth crossing -------------------------------------------------------
edit(
    "r2b-fifth-crossing",
    """| entry replacement in `/usr/lib/duplicati` | 0755 duplicati-owned directory | P0.5 `chown -R root:root` |""",
    """| entry replacement in `/usr/lib/duplicati` | 0755 duplicati-owned directory | P0.5a's `chown` |
| **`$CREDENTIALS_DIRECTORY/settings-key` → any run-script → the job passphrase** | `LoadCredential=` exposes the key to **every** process in the unit, run-scripts included (`man systemd.exec`), and a run-script path is a plain job option. Chain: UI credential → API → `--run-script-before` → the key → the server DB → the passphrase → **every volume in T1 and T1c** | **NOT closed as shipped.** Only the secret-provider channel (§7.3.5) replacing `LoadCredential=`, plus AC-13 |
| capability-read data → the internet | write it into the Dropbox-synced destination; the daemon uploads it | `ReadWritePaths=` scoped to `Yamaguchi/` (§7.3.2) + D-13. **`IPAddressDeny=` does not close this** |""",
)

edit(
    "r2b-crossing-rows",
    """| `.env` → code in the capability-bearing process | an `LD_PRELOAD`/`DOTNET_STARTUP_HOOKS`/`PATH`/`BASH_ENV` line in a file the plain `duplicati` uid can write | the wrapper's **positive** export allow-list (§7.3.3) + `.env` mode (§7.3.5) |
| `/proc/<serverpid>/environ` → the settings key | same uid reads the server's environ | the secret-provider channel (§7.3.5), which keeps the key out of the environment entirely |""",
    """| `.env` → code in the capability-bearing process | an `LD_PRELOAD`/`DOTNET_STARTUP_HOOKS`/`PATH`/`BASH_ENV` line in a file the plain `duplicati` uid can write | the wrapper's **positive** export allow-list (§7.3.3); the `.env` **mode** closes it only once the file is outside the duplicati-owned data folder (§7.3.5) |
| `/proc/<serverpid>/environ` → the settings key | same uid reads the server's environ | the secret-provider channel (§7.3.5) **if adopted**; the unit as shipped uses the `LoadCredential=` + wrapper-export fallback, under which this crossing is **OPEN** |""",
)

edit(
    "r2b-crossings-heading",
    """**Trust domains, and the four crossings between them.**""",
    """**Trust domains, and the six crossings between them.**""",
)

# --- R2B-12: split P0.5 ---------------------------------------------------------------
edit(
    "r2b-p05-split",
    """### P0.5 — same session as the recovery (minutes, and none of it depends on the recovery)

These were scattered across P1 and P2 while the recovered server ran for days with the holes open. Each takes
minutes and has no dependency on which procedure step 3 chose.""",
    """### P0.5a — before anything in P0 (minutes; depends on nothing)

Items 1, 2, 4, 5, 6 and 7 below. These were scattered across P1, P2 and P4 while the recovered server ran for
days with the holes open. None touches the recovery, each takes minutes, and item 1 closes the path by which
the service user controls the very binaries P0 steps 0(c), 3, 4 and 7 execute.

**Item 3 is not one of them** — see P0.5b at the end of this list. An earlier revision put all six under one
heading that claimed "none of it depends on the recovery", which is true of five and false of the one that
closes S-1 and S-2.""",
)

edit(
    "r2b-p05b",
    """6. **Close the detection gap**:""",
    """7. **`usermod -s /usr/sbin/nologin duplicati`** (moved here from P4). While a `duplicati`-uid shell exists outside the unit, the §7.3.2 mount mask can be escaped through `/proc/<pid>/root`, so every such session is a hole in `InaccessiblePaths=` for as long as it lives. Do this **after** the two live `su - duplicati` shells in §6's sink checklist have been closed per their own row — closing the shell is the owner's time-critical action; this makes the next one impossible.
6. **Close the detection gap**:""",
)

edit(
    "r2b-p05b-heading",
    """### P1 — secrets (same week)""",
    """### P0.5b — immediately after P0 step 8, same session

**Item 3 (the re-key) only.** It runs the server against the **recovered** data folder, so it cannot precede
the recovery: stop the snapshot timer, do the two-start re-key back to back, then
`PRAGMA wal_checkpoint(TRUNCATE); VACUUM;` with the server stopped, then restart the timer (§7.3.5). This is
the item that closes S-1 and S-2, so it is not deferrable to P1 — but it is also not runnable before step 8.

### P1 — secrets (same week)""",
)

# --- R2B-13: sinks --------------------------------------------------------------------
edit(
    "r2b-sinks",
    """| Claude Code transcripts under `~/.claude/projects/…` | **cloud-linked**, and they capture every `journalctl` output this arc produced; the count grows with every tool call, so any figure is an upper bound | count-grep and purge; this is what makes D-2's "local exposure" framing false |""",
    """| Claude Code transcripts **and persisted tool-result files** under `~/.claude/projects/…` | **cloud-linked**, and **inside the backup Source** — note (AC-3a) lists `.claude/projects` among the *unfiltered* 0700 trees, so every capture is in every T1 fileset and in Dropbox (note sink-a) | count-grep and purge **both** the `.jsonl` transcripts and the `tool-results/` files; this is what makes D-2's "local exposure" framing false |
| Per-session agent scratch trees under `/tmp/claude-1000/…` | Round 1's six lanes and round 2's four each wrote captures, extracted units and analysis output there, `drwx------ pcalnon` | `/tmp` is **tmpfs**, so a reboot clears them and they are **not** in the backup Source — state that rather than leave it inferred; until a reboot they are readable by every `pcalnon` process |
| Ad-hoc instruments that **read** a secret file | `2026-09-21_env_value_equality.py`, `…_settings_key_hash_probe.py`, `2026-09-22_credential_file_shape.py`, `duplicati_api.py` (S-5a) | an instrument that reads a secret is itself a sink if it writes an artifact: each states in its header what it writes and where, and none writes into `notes/`, `util/` or the backup Source |

- **(sink-a)** Large tool outputs are written as **separate files** under `<session>/tool-results/`, not inlined into the `.jsonl` — which is exactly where this arc's oversized `journalctl` captures landed, *because* they were too large to inline. A purge that walks only the transcripts misses them.""",
)

# --- R2B-16: the escrow ACL -----------------------------------------------------------
edit(
    "r2b-setfacl-b",
    """if [[ -d "${ROOT}/_yamaguchi_keys" ]]; then
    chmod 0700 "${ROOT}/_yamaguchi_keys\"""",
    """if [[ -d "${ROOT}/_yamaguchi_keys" ]]; then
    # Strip the named ACL entry the recursive setfacl above just applied here. chmod sets the
    # ACL MASK, not the entry, so `g:duplicati:rwX` would survive with an empty mask and any
    # later `chmod g+rx` would silently re-enable the service user's access.
    setfacl -R -b "${ROOT}/_yamaguchi_keys"
    chmod 0700 "${ROOT}/_yamaguchi_keys\"""",
)

# =====================================================================================
# Round 3 — confirmation pass; D1 … D15
# =====================================================================================

# --- D5 + D6: the P0.5a list still printed the re-key it exists to defer --------------
edit(
    "r3-p05a-item3-stub",
    """3. **Re-key now, not "same week" (P1 step 1's content, moved here).** The live settings key *is* the backup passphrase (S-2), and the burned key from S-1 is public. Stop the snapshot timer, do the two-start re-key back to back, then `PRAGMA wal_checkpoint(TRUNCATE); VACUUM;` with the server stopped, then restart the timer (§7.3.5).
4. **Scrub both log stores**""",
    """3. **Moved to P0.5b — do NOT run this here.** The re-key runs the server against the *recovered* data folder, so it cannot precede P0 step 8; the procedure is in P0.5b below. The number is kept so that §6's S-2 row, §7.3.5 and P1 step 1 still land on something.
4. **Scrub both log stores**""",
)

edit(
    "r3-p05a-order",
    """7. **`usermod -s /usr/sbin/nologin duplicati`** (moved here from P4). While a `duplicati`-uid shell exists outside the unit, the §7.3.2 mount mask can be escaped through `/proc/<pid>/root`, so every such session is a hole in `InaccessiblePaths=` for as long as it lives. Do this **after** the two live `su - duplicati` shells in §6's sink checklist have been closed per their own row — closing the shell is the owner's time-critical action; this makes the next one impossible.
6. **Close the detection gap**:""",
    """6. **Close the detection gap**:""",
)

edit(
    "r3-p05a-item7",
    """which is why both PRs passed; CI runs gitleaks only *after* publication.""",
    """which is why both PRs passed; CI runs gitleaks only *after* publication.
7. **`usermod -s /usr/sbin/nologin duplicati`** (moved here from P4, which no longer performs it). While a `duplicati`-uid shell exists outside the unit, §7.3.2's mount mask can be escaped through `/proc/<pid>/root`, so every such session is a hole in `InaccessiblePaths=` for as long as it lives. Do this **after** the two live `su - duplicati` shells in §6's sink checklist have been closed per their own row — closing those is the owner's time-critical action; this makes
   the next one impossible.""",
)

edit(
    "r3-p4-usermod",
    """3. `usermod -s /usr/sbin/nologin duplicati`.""",
    """3. *(Executed in P0.5a item 7 — kept here as the procedure of record; verify with `getent passwd duplicati`.)* `usermod -s /usr/sbin/nologin duplicati`.""",
)

edit(
    "r3-r6-disposition",
    """| R-6 | `duplicati` is a system user; shell only during development | O | Kept; `nologin` at the end of the migration (§8 P4) |""",
    """| R-6 | `duplicati` is a system user; shell only during development | O | Kept; `nologin` **immediately**, in §8 P0.5a item 7 — moved out of P4 because a duplicati-uid shell outside the unit escapes §7.3.2's mount mask through `/proc/<pid>/root` |""",
)

# --- D8: bare P0.5 references now that the bucket is split ----------------------------
edit(
    "r3-ref-header",
    """**§8 is executable in this order and no other**: P0.5 items 1–2, then **P0 step −1** (land the nine
scripts §8 invokes — they exist today only as tagged blocks here), then **P0 step 0**'s owner gates,
then P0.""",
    """**§8 is executable in this order and no other**: **P0.5a** items 1–2, then **P0 step −1** (review and
merge the nine scripts §8 invokes that are now staged; the tenth is a P3 deliverable), then **P0 step 0**'s
owner gates, then **P0**, then **P0.5b** (the re-key, which needs the recovered data folder).""",
)

edit(
    "r3-ref-s2",
    """Re-key in **P0.5 step 3** (note S-2a) |""",
    """Re-key in **P0.5b** (note S-2a) |""",
)

edit(
    "r3-ref-p0-preamble",
    """**Run P0.5 items 1 and 2 before anything in P0.**""",
    """**Run P0.5a items 1 and 2 before anything in P0.**""",
)

edit(
    "r3-ref-735",
    """That two-start sequence is the re-key procedure, and it runs in **§8 P0.5**, not P1""",
    """That two-start sequence is the re-key procedure, and it runs in **§8 P0.5b**, not P1""",
)

edit(
    "r3-ref-proca",
    """**and leave it there until P0.5's re-key replaces it**""",
    """**and leave it there until P0.5b's re-key replaces it**""",
)

edit(
    "r3-ref-p1step1",
    """1. *(Executed in P0.5 step 3 — kept here as the procedure of record.)*""",
    """1. *(Executed in P0.5b — kept here as the procedure of record.)*""",
)

edit(
    "r3-ref-p2step1",
    """1. *(The chown, the `bin/` removal and `/etc/default/duplicati` moved to P0.5 step 1.)*""",
    """1. *(The chown, the `bin/` removal and `/etc/default/duplicati` moved to P0.5a item 1.)*""",
)

edit(
    "r3-ref-p2step3",
    """the **installed** copy under `/usr/local/lib/duplicati/` (not the repository file — P0.5 item 2 made the unit execute the copy)""",
    """the **installed** copy under `/usr/local/lib/duplicati/` (not the repository file — P0.5a item 2 made the unit execute the copy)""",
)

edit(
    "r3-ref-ac8a",
    """so that half of the criterion can only run once P0.5 item 6 adds the pre-commit hook""",
    """so that half of the criterion can only run once P0.5a item 6 adds the pre-commit hook""",
)

edit(
    "r3-ref-step11",
    """it becomes provable only when the snapshot lane is re-pointed (P0.5 item 2)""",
    """it becomes provable only when the snapshot lane is re-pointed (P0.5a item 2)""",
)

# --- D1, D2: two malformed section references ----------------------------------------
edit(
    "r3-ref-439",
    """and fails the 0700 gate before argv matters (§4.3.9, §5.5) | `systemctl show`, `ps` |""",
    """and fails the 0700 gate before argv matters (§4.3 item 9, §5.5) | `systemctl show`, `ps` |""",
)

edit(
    "r3-ref-yam8215",
    """the §8.21.5 residuals;""",
    """the YAM §8.21.5 residuals;""",
)

# --- D7: acceptance-table row order ---------------------------------------------------
edit(
    "r3-ac-order",
    """| AC-14 | After any `.env` or `DAEMON_OPTS` change, `journalctl -u duplicati.service --since <ts>` contains **zero** `Unknown option supplied` lines. 2.4.0.0 logs an unrecognised option as a warning and **continues** (§7.3.3), so a typo is a silent misconfiguration and this grep is the only thing that catches it | `journalctl -u duplicati.service --since <ts> \\| grep -c 'Unknown option supplied'` = 0 |
| AC-13 | The job's `--run-script-before-required` equals `/usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash` and nothing else; no other run-script option is set (note AC-13a) | `python3 util/ad-hoc/yamaguchi_server_api.py export <id>`; diff against the design's path |""",
    """| AC-13 | The job's `--run-script-before-required` equals `/usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash` and nothing else; no other run-script option is set (note AC-13a) | `python3 util/ad-hoc/yamaguchi_server_api.py export <id>`; diff against the design's path |
| AC-14 | After any `.env` or `DAEMON_OPTS` change, `journalctl -u duplicati.service --since <ts>` contains **zero** `Unknown option supplied` lines — 2.4.0.0 logs an unrecognised option as a warning and **continues** (§7.3.3), so a typo is otherwise silent (note AC-14a) | `journalctl -u duplicati.service --since <ts> \\| grep -c 'Unknown option supplied'` = 0 |""",
)

# --- D10: the preamble's script inventory --------------------------------------------
edit(
    "r3-ac14a-note",
    """- **(AC-13a)** Pinned as an acceptance check because a run-script path is a plain job option""",
    """- **(AC-14a)** An **environment variable** the server does not read logs nothing at all, so AC-14 is blind to that class — which is why §7.3.2's two `Environment=` names were verified against the shipped assemblies rather than trusted to this grep.
- **(AC-13a)** Pinned as an acceptance check because a run-script path is a plain job option""",
)

edit(
    "r3-installer-invocation",
    """Install §7.3 (unit, defaults, wrapper, guard) with `util/install_duplicati_service.bash`, then `sudo systemctl start duplicati.service`.""",
    """Install §7.3 (unit, defaults, wrapper, guard) with
   **`sudo bash util/install_duplicati_service.bash`** — through `bash`, not directly. Every script this
   document landed was committed through GitHub's `createCommitOnBranch` API, which **carries no file
   mode**, so each arrives `100644` and is not executable whatever the working tree said. That is a
   property of any API-signed commit, not a one-off to fix: the next one lands the same way. Then
   `sudo systemctl start duplicati.service`.""",
)

edit(
    "r3-preamble-scripts",
    """**Nine of the paths below do not exist yet.** §8 names `util/install_duplicati_service.bash`,
`util/yamaguchi-pre-backup-guard.bash`, `util/systemd/duplicati.{service,default}`,
`util/ad-hoc/2026-09-22_confirm_a0_premise.bash`, `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash`,
`util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash`,
`util/ad-hoc/2026-09-21_backup_destination_permissions.bash`, `util/juniper-backup-scheduled.bash` and
`util/install_juniper_backup_timer.bash` — all of which exist today only as tagged blocks in this document.
**P0 step −1 is to land them**, extracted with `util/ad-hoc/2026-09-21_lint_design_snippets.py` (Appendix B
maps block → path) and reviewed in a PR, not pasted onto a root prompt during the recovery. `sqlite3` and
`gitleaks` are **not installed** on this host either; step 3 needs the first and AC-8 the second.""",
    """**Ten paths are named below; nine are landed and one is not.** Landed, and byte-identical to their tagged
blocks here: `util/install_duplicati_service.bash`, `util/yamaguchi-pre-backup-guard.bash`,
`util/systemd/duplicati.service`, `util/systemd/duplicati.default`,
`util/ad-hoc/2026-09-22_confirm_a0_premise.bash`, `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash`,
`util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash`,
`util/ad-hoc/2026-09-21_backup_destination_permissions.bash` and `util/juniper-backup-scheduled.bash`. The
tenth, `util/install_juniper_backup_timer.bash`, has **no tagged block** in this document and is a **P3
deliverable** (§7.3.4, §7.8), not a P0 item — do not look for it here. **P0 step −1 is to review and merge the
nine**, re-extracted with `util/ad-hoc/2026-09-21_lint_design_snippets.py` and re-staged with
`util/ad-hoc/2026-09-22_stage_design_artifacts.py`, rather than pasted onto a root prompt during the recovery.
Appendix B lists every block by its **deployed** path; §7.3.4 gives the repository destination for the four
that differ. `sqlite3` and `gitleaks` are **not installed** on this host; step 3 needs the first and AC-8 the
second.""",
)

# --- D15: §8 must point at §5.5's gate behaviours --------------------------------------
edit(
    "r3-step6-gate",
    """Two traps: `--server-datafolder <dir>` **is** an option of the *subcommand*""",
    """Three traps. First, one §5.5 measures and §8 must not leave implicit:
   `duplicati-database-tool` does **not** apply the 0700 data-folder gate at all — it resolves the folder in
   `ProbeOnly` mode — so a clean run here is **no** evidence that the copy's folder is acceptable to the
   *server*; step 8's `install -d -m 0700` is what makes it so. Second, `--server-datafolder <dir>` **is** an option of the *subcommand*""",
)

edit(
    "r3-step3-gate",
    """   A server-based probe is **confirmation only**, and only with all four containments below""",
    """   If you reach for `duplicati-server-util` at any point in this step, note that its 0700-gate refusal is **completely silent** — exit 1, zero bytes on stdout *and* stderr, before even the "Connecting to…" line (§5.5). A silent exit 1 there is a permissions problem, not a missing server.

   A server-based probe is **confirmation only**, and only with all four containments below""",
)

# --- D14: the probe's own timeout --------------------------------------------------------
edit(
    "r3-probe-timeout",
    """   The 45 s timeout ends the probe server; the `DELETE FROM Schedule` and the two `InaccessiblePaths=`""",
    """   The 90 s timeout ends the probe server (`timeout -k 10 90` — raised from 45 s because a cold .NET start under `systemd-run` can exceed it, and a timeout that fires early is indistinguishable from a rejected key unless `try_key` is careful, which is why it now reports `INDETERMINATE`); the `DELETE FROM Schedule` and the two `InaccessiblePaths=`""",
)

# --- D12: P1 step 3 and S-1 are already executed in-tree --------------------------------
edit(
    "r3-p1step3-done",
    """3. Remove the commented "Old Unit file" block from `scripts/duplicati-wrapper.bash` (the wrapper is replaced by §7.3.3 in the same PR).""",
    """3. *(**Executed in-tree**, pending merge: `scripts/duplicati-wrapper.bash` has been replaced by §7.3.3's wrapper v2 and carries no credential-shaped literal — its one `SETTINGS_ENCRYPTION_KEY=` is the legitimate `export` of a variable. Verify with `grep -c 'Environment=SETTINGS' scripts/duplicati-wrapper.bash` = 0, which is AC-8's own check.)* Remove the commented "Old Unit file" block from `scripts/duplicati-wrapper.bash`. **The exposure in `main`'s git
   history is untouched by this and stays untouched** — the key is dead, and S-1 records why a history rewrite is not worth its cost.""",
)

edit(
    "r3-s1-done",
    """Remove the block from the script (P1 step 3); close the detection gap (below) |""",
    """The block is already removed in-tree (P1 step 3); close the detection gap (below) |""",
)

# --- D9: §11 must not state round 3's verdict before round 3 ran -----------------------
edit(
    "r3-s11-round3",
    """  **Round 3** (one agent, briefed on round 2's corrections) confirmed them; §12 records what it changed.""",
    """  **Round 3** (one agent, briefed on round 2's corrections, reading a **frozen** document) confirmed 13 of
  the 20 corrections outright, found 6 present-but-incomplete, and swept every internal cross-reference —
  15 defects, all applied. Its own instruments reproduced AC-12a's `1.7 OK` and all 15 ✗ rows, the 53/18
  syscall-set numbers, the 1,443-file scan and the byte-identity of all 14 tagged blocks against their
  landed repository copies. Its sharpest finding was structural and is the one round 2 created: the
  P0.5a/P0.5b split was made by **adding headings**, not by relocating content, so the re-key procedure was
  still printed in full inside the list headed "before anything in P0" — the exact ordering error the split
  exists to prevent. §12 records the result.""",
)

# --- item 2 caveat: the AUTOUPDATER name is a template substitution ---------------------
edit(
    "r3-autoupdater-caveat",
    """# same scan does find. An unread environment variable produces no "Unknown option supplied"
# line, so AC-14 structurally CANNOT catch a wrong name here -- which is why the option form
# below is also set, in /etc/default/duplicati, where AC-14 can see a typo.""",
    """# same scan does find. An unread environment variable produces no "Unknown option supplied"
# line, so AC-14 structurally CANNOT catch a wrong name here -- which is why the option form
# below is also set, in /etc/default/duplicati, where AC-14 can see a typo.
#
# Note for anyone re-running that scan: the two names below are NOT literals either. The
# assemblies carry the templates AUTOUPDATER_{0}_SKIP_UPDATE (Duplicati.Library.AutoUpdater.dll)
# and USAGEREPORTER_{0}_LEVEL (Duplicati.Library.UsageReporter.dll); {0} resolves to
# "Duplicati" from the embedded manifest resource AutoUpdateAppName.txt. So a literal scan
# reports NOT FOUND for the substituted forms and that is CORRECT -- it is the templates plus
# the resource that establish them. DO_NOT_TRACK is a direct literal. (Round 3.)""",
)

# --- item 8 caveat: the LoadCredential citation aimed at the wrong clause ---------------
edit(
    "r3-loadcredential-clause",
    """and that it is *"the **system service manager**"* that searches `/etc/credstore/`. The
manager reads the file and hands the unit a separate read-only copy at `$CREDENTIALS_DIRECTORY`.""",
    """The manager reads the file and hands the unit a separate read-only copy at `$CREDENTIALS_DIRECTORY`.
(The manual's *"the system service manager … will search `/etc/credstore/`"* sentence is often quoted here
as well; it governs a **relative** `LoadCredential=` path, and this unit uses an absolute one, for which the
operative sentence is *"If the specified path is absolute it is opened as regular file and the credential
data is read from it."* The conclusion is the same either way — the manager opens it before the unit's
namespace exists — but cite the right clause.)""",
)

# =====================================================================================
# driver
# =====================================================================================

def join_wrapped_table_rows(text: str) -> str:
    """Re-join a markdown table row that an edit wrapped across lines (see stage 1)."""
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
    ap.add_argument("--skip-stage1", action="store_true", help="assume stage 1 already ran")
    args = ap.parse_args()

    if not args.skip_stage1:
        rc = subprocess.run([sys.executable, str(STAGE1)], capture_output=True, text=True)
        if rc.returncode != 0:
            print("stage 1 failed:\n" + rc.stdout + rc.stderr, file=sys.stderr)
            return 1
        print(f"stage 1: {rc.stdout.strip().splitlines()[-1]}")

    text = DESIGN.read_text(encoding="utf-8")

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
    for lineno, width in over:
        print(f"  OVER-WIDE table row at line {lineno}: {width} chars", file=sys.stderr)

    if args.check:
        print(f"\n--check: {len(EDITS)} stage-2 edits would apply; nothing written")
        return 0

    DESIGN.write_text(text, encoding="utf-8")
    print(f"\nwrote {DESIGN} ({len(text)} bytes, {len(EDITS)} stage-2 edits)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
