# Backup infrastructure — integrated design, root-cause analysis and remediation plan

**Project**: Juniper (workstation backup infrastructure, host `yamaguchi`)
**Author**: Paul Calnon
**Date**: 2026-09-21
**Status**: DRAFT — consensus round 1 COMPLETE (six validators), reconciliation PENDING. Lane A2 and A3 corrections are applied; Lane A1, B1, B2 and B3 corrections are **not** — beyond the §4.1 unit row; the §11 adequacy and cannot-support entries; the §8 STOP warning; §7.3.2's env override (B1 F11); P1 step 2's `chmod 0600` (B2 D15); the AC-12 row, §0's instrument list and §12's file list (B2 D22) — (verbatim reports: `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`;
remaining work: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-21_backup-redesign-round-1-validated-reconciliation-pending.md`). **Do not execute §8 from this revision** —
see the warning at the top of §8 and the record in
§11.
**Supersedes in part**: the *Dropbox-era* operating state; does **not** supersede the certification record
**Companions**:
[`JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-BACKUP-SET-PLAN.md`](JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-BACKUP-SET-PLAN.md) (the design of record, "PLAN"),
[`JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md`](JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md) (the certification record, "YAM"),
[`JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md`](JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md) ("DMG"),
[`JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md`](JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md) ("GPG"),
[`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md) ("CON", the validation procedure this document is held to).

---

## 0. How this document was produced

Three steps, each carried out by independent agents with **different entry points**, then reconciled here (CON §2 Lane A / §5):

| Step | Entry point | Agent lens |
| --- | --- | --- |
| 1a. Evaluate the documented design | the seven `notes/` documents of record | documented design, certification status, contradictions, rules to carry forward |
| 1b. Reconstruct the as-built design | the thirteen session handoffs + every script and unit in `util/`, `util/systemd/`, `util/ad-hoc/`, `scripts/` | mechanism inventory, chronology, guards catalogue, tar-lane analysis |
| 2a. Determine the live state | the host only: systemd, journal, processes, filesystems, databases (copies), Dropbox | observations vs inferences, timeline from inode timestamps |
| 2b. Static and behavioural analysis of the new wrapper lane | the repository, GitHub, shellcheck, synthetic inputs | defects with severity and evidence |
| 2c. Product behaviour | Duplicati source, docs, releases; systemd man pages; sandboxed `help` runs | verified option names, data-folder rules, schema versions |
| 3. This design | all of the above plus the orchestrator's own forensics (§5, Appendix A) | reconciliation, design, remediation |

Instruments written for step 2/3 and kept as provenance: `util/ad-hoc/2026-09-21_duplicati_server_db_forensics.py` (read-only inspection of **copies** of every candidate server database), `util/ad-hoc/2026-09-21_env_file_shape.py` (shape of a secret file without printing a value), `util/ad-hoc/2026-09-21_lint_design_snippets.py` (extracts every tagged code block of this document, then runs the real linter on each — extraction completes before any lint so a unit whose
`ExecStart=` names a later block resolves), `util/ad-hoc/2026-09-21_wrap_long_markdown_lines.py` (wraps over-long prose lines at word boundaries for MD013 without touching tables or fences).

Secrets discipline: no passphrase, key or credential value appears in this document. Where one is discussed it is described by length and character class only.

---

## 1. Executive summary

**The backup is down; the last successful run of the `Yamaguchi` job started 2026-09-18 14:00 UTC and finished at 14:12 UTC** (fileset `duplicati-20260918T140000Z.dlist.zip.aes`, 877 files / 202.8 GiB at the destination). The scheduled runs of 2026-09-19 and 2026-09-20 did not happen; the watchdog has alerted `UNREACHABLE` on 09-19 and 09-20 and `login failed (401)` on 09-21. The server now listening on `localhost:8300` runs as the new `duplicati` user against a database created
from scratch at 2026-09-20 18:19:43 CDT that holds **zero** backup definitions.

**Root cause of "no backups defined" — three independent legs, each sufficient on its own** (§5):

- **Leg A — wrong source.** The configuration copied into `/home/duplicati/.config/Duplicati/` came from `/home/pcalnon/.config/Duplicati/`, which has been **orphaned since 2026-08-25**. The production job was rebuilt that day on the root system server in **portable mode**, whose data folder is `/usr/lib/duplicati/data/`. The pcalnon profile never held the `Yamaguchi` job; its own `Schedule` table was empty and its last real content (`Duplicati-server.backup`, 2026-08-25
  02:19:47) lists only the retired `Ubuntu` and `Ubuntu-fresh` jobs.
- **Leg B — the copied file is not a server database.** `Duplicati-server.sqlite` in the pcalnon profile is a 4 KB, one-page file whose entire content lives in a 112 MB write-ahead log; replayed, it is a **per-job (local) database schema, version 19, containing a single aborted `Recreate` operation started 2026-08-25 02:19:48** and nothing else. Duplicati 2.3.0.4 refused it ("version 19 but the largest supported version is 11"), 2.4.0.0 refused it ("… is 12"). The operator
  moved the WAL aside at 18:19:26 on 09-20; the server started 16 s later on the empty 4 KB file and initialised a fresh, empty schema (version 12). Four attempts to import a backup through the web UI then failed (two JSON parse errors on a file beginning with `S` — a SQLite file, not an export — and two AES wrong-password errors).
- **Leg C — the real database was locked away by a key mix-up.** On 2026-09-18 at 21:03:27 the root data folder's server database was, for the first time, opened **with** a `SETTINGS_ENCRYPTION_KEY`, which encrypted its sensitive fields under that key. Every later start supplied a different key or none: `SettingsEncryptionKeyMismatchException` (21:08), `SettingsEncryptionKeyMissingException` (21:15 onwards, after systemd rejected the `Environment=` line because the key
  contains `%` — "Failed to resolve specifiers … Invalid slot"). The operator then abandoned that data folder without recovering it.

**One more restart makes it worse.** A global systemd reload at 03:23:44 on 09-21 armed the operator's latest unit edit, whose `ExecStart` hands the wrapper a single `--daemon-opts="…"` word that neither wrapper revision can parse; the next restart or reboot starts the server on port 8200 or not at all (§4.3 item 9). Recovery (§8 P0) installs the corrected unit and wrapper before the first restart.

**Tier 2 has been silently broken since 2026-09-07 as well.** The USB archive script looks for its drives under
`/media/pcalnon/`; the udisks2 upgrade of that day moved automounts to `/run/media/pcalnon/`, so every run since skips
both drives and fails with "no usable device" (§4.5). Nothing reported it because the lane has no timer or alerting.

**The job definition is recoverable.** A consistent copy of the root server database, taken by the still-running root snapshot timer (last at 2026-09-21 08:45 CDT, still 240 KiB, `integrity ok`), sits at `~/.local/state/duplicati-server-db/Duplicati-server.sqlite` (240 KiB, schema 11). It holds the `Yamaguchi` job: 2 sources, 45 filters, 10 job options, the daily 14:00 UTC schedule and the per-job index path. The per-job index itself (`/usr/lib/duplicati/data/BMXWPAOGLP.sqlite`) is intact under the
duplicati-owned data folder. §8 gives two recovery procedures — one that re-uses the whole data folder if the 09-18 key can be identified, one that rebuilds the job through the API from the snapshot and re-attaches the existing index. Neither needs a Recreate.

**Three secret exposures must be handled with the recovery** (§6): the settings key delivered from `.env` is **byte-identical to the backup passphrase**; the wrapper's debug mode wrote every `.env` line — including commented-out lines carrying both backup passphrases — into the system journal 10 times over on 2026-09-20; and an earlier settings key is committed in a comment of `scripts/duplicati-wrapper.bash` and printed 23 times in the journal by systemd's own specifier error.

**The integrated design** (§7) keeps the certified three-tier posture and the owner's new direction (dedicated `duplicati` service user, systemd unit, wrapper, group-shared destination, Dropbox cloud replica, scheduled USB archives, an additional offline external-drive archive) and fixes what the migration broke: the data folder becomes explicit, the settings key travels through a systemd credential instead of shell `eval`, the wrapper is rewritten without `eval` and with
array argv, the destination permission model is defined so both `duplicati` (write) and `pcalnon`/Dropbox (read) work, the watchdog and snapshot lanes are re-pointed, and the tar lane gains a timer plus mount detection.

---

## 2. Requirements — integrated

Sources: **O** = owner prompt of 2026-09-21 (archived as `prompts/manual/prompt132_2026-09-21.md` on the primary checkout's `feat/backup-updates-and-redesign-work` branch, commit `aab07eba`, and on `main` since `d721fc78`, #1969); **P** = PLAN §3/§6/§7; **Y** = YAM (the as-certified job).

| ID | Requirement | Source | Disposition in this design |
| --- | --- | --- | --- |
| R-1 | Tier 1: daily Duplicati backup of `/home/pcalnon` to a physically separate on-host disk (`/dev/sda1`, `/mnt/Backups`) | P §3, O | Kept. Destination path per O: `/mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi/` |
| R-2 | The Duplicati server runs as a systemd **system** service, as a dedicated `duplicati` user and group, not root | O (supersedes YAM's root server) | Kept; §7.3 |
| R-3 | Unit file specifies user/group; defaults in `/etc/default/duplicati`; a wrapper script launches the server | O | Kept, with the unit moved to `/etc/systemd/system/` and the wrapper installed as a root-owned copy (§7.3.4) — the symlink form is retained only as a fallback (D-6) |
| R-4 | Wrapper input precedence: argv words after `DAEMON_OPTS` > `DAEMON_OPTS` > `.env` > script defaults; `.env` constants exported | O | Kept exactly; implemented without `eval` (§7.3.3) |
| R-5 | `.env` in the duplicati home holds `SETTINGS_ENCRYPTION_KEY` | O | Changed: the key is delivered by systemd `LoadCredential=`; `.env` keeps the same grammar and may carry it only for hand runs (§7.3.5, D-1) |
| R-6 | `duplicati` is a system user; shell only during development | O | Kept; `nologin` at the end of the migration (§8 P4) |
| R-7 | `pcalnon` (member of group `duplicati`) has read/write/execute as appropriate on all backup files and scripts | O | Kept for the destination tree, the scripts and the daily server-DB snapshot copy (group ownership, setgid dirs, `0007` umask; §7.4). **Not** for the live data folder: 2.4.0.0 refuses one with any group/other bit (§7.3.2); `pcalnon` uses `sudo -u duplicati` or the snapshot copy. The installed wrapper is changed via repository + install script, not in place (D-6) |
| R-8 | Destination writable+executable by `duplicati`; readable+executable by `pcalnon` so Dropbox can sync | O | Kept; §7.4 gives the exact mode/ACL model and the Dropbox-daemon group prerequisite |
| R-9 | `/mnt/Backups/Ubuntu/Dropbox` is a live Dropbox root; the synced copy is the cloud-hosted backup instance | O | Kept as **tier 1c**; guarded by a pre-backup hook and a stray-file check (§7.5); `duplicati-sync-tool` offered as the alternative (D-3) |
| R-10 | Tier 2: a dedicated script writes compressed, encrypted tar archives of the project to two external USB drives | P §3, O (`util/juniper-backup.bash`) | Kept |
| R-11 | Tier 2 runs on a preset schedule, but only when the valid USB drives are detected as mounted | O | New; §7.8 (user-scope timer + path unit + due-check scheduler) |
| R-12 | Tier 3: an additional archive to an external hard drive | O (sentence truncated in the prompt) | New; §7.9 proposes the default; **D-5** asks the owner to complete the requirement |
| R-13 | Alerting: a backup that silently stops must not be indistinguishable from one that works (PLAN §6 item 3: "A backup that silently stops is indistinguishable from one that works") | P §6 item 3, Y | Kept; watchdog re-pointed and extended (§7.6) |
| R-14 | Server database backed up daily into the backup source | P §6 item 4, Y §8.19 | Kept; re-pointed to the new data folder (§7.7) |
| R-15 | Passphrase escrowed off the source disk and off-machine | Y §8.18 | Kept; extended to the settings key (§6, §7.3.5) |
| R-16 | Retention paired with `--no-auto-compact=true`; `--blocksize=1MB`; AES module | Y §3/§4 (AES, the pairing); PLAN §4 (`--blocksize`; PLAN §4 itself specified gpg and no initial retention) | Kept unchanged (§7.5) |
| R-17 | Every destination path fstab-managed; mount verified before any destination operation | Y §8.10.2; `HANDOFF_2026-08-22_duplicati-dbpath-and-recovery.md` §3 | Kept; `RequiresMountsFor=`, wrapper preflight, `--run-script-before-required` guard |
| R-18 | No secret on a command line or in a log | Y, GPG | Kept; and now *enforced* by design after the 09-20 exposure (§6) |
| R-19 | Generated content validated by independent agents per CON | owner standing instruction | §11 |

---

## 3. The original design as documented — evaluation

### 3.1 What the record specifies

PLAN §3 fixes a **three-tier posture**: (a) a daily Duplicati job on a physically separate on-host drive, (b) infrequent full Juniper archives on an external drive kept offline, (c) more frequent per-project archives on USB drives. No cloud tier exists anywhere in the record — the cloud appears only as Duplicati's report upload (YAM §8.18.4) and as a password-manager escrow copy (YAM §8.24.1). The Dropbox replica is therefore **new** in this design.

The Duplicati tier went through three generations: the pcalnon GNOME-session job `Ubuntu` (destroyed by an interrupted compact on 2026-07-13, DMG §2), the `systemd --user` CLI lane `Ubuntu-fresh` (0-for-3, superseded; YAM §2), and the production job **`Yamaguchi`** on the root system server in portable mode (YAM §2–§8). As certified: source `/home/pcalnon/` plus one VDI, 44–45 filters, `encryption-module=aes`, `--blocksize=1MB`, `--dblock-size=500MB`,
`--no-auto-compact=true` paired with `retention-policy=1W:1D,1M:1W,1Y:1M,3Y:2M`, `--asynchronous-upload-limit=1`, schedule 14:00 UTC daily, destination `/mnt/Backups/Ubuntu/Yamaguchi` after the 2026-08-26 migration to `sda1`, tempdir `/home/pcalnon/.cache/duplicati-tmp` since 2026-08-28.

### 3.2 Certification status

All six PLAN §7 acceptance criteria are recorded CLOSED in YAM: full backup (§8.7), two restore drills with checksums (§5.3, §8.4), failure alerting via the deployed watchdog (§8.7, 2026-08-26), reboot/logout survival (§8.27, 2026-09-08), and the migration to `sda1` with a passing drill (§8.13). The PLAN file itself was never updated — all six boxes are still unticked there, and its "Destination CHOSEN (temp_backups)" status line is stale. This document does not re-open
those closures; it records that **the state they certified no longer exists** (§4).

### 3.3 Rules the record established that this design carries forward

Each rule below is load-bearing for §7/§8. Citations name the document that recorded the failure.

1. Never let a backup run in a login-session scope without linger; the 42-day silent outage was a `Linger=no` GNOME scope (DMG §9).
2. Verify the mount before **any** destination operation; an unmounted destination reads as "everything is missing", not as an error (YAM §8.10). Every destination must be fstab-managed (YAM §8.10.2).
3. Never stage volumes on tmpfs (GPG §9; the scheduled runner's guard 3b).
4. Retention runs only with `--no-auto-compact=true`; the pairing is load-bearing (YAM §3, DMG §2).
5. `--blocksize` is irreversible; pin it explicitly (PLAN §4).
6. A restore drill must not rebuild files from local blocks, must compare SHA-256 + length, select by `--time=`, and include a negative control; exit code is not evidence (DMG §4a, YAM §5 item 3). In 2.4.0.0 `--no-local-blocks` is **deprecated** because not using local blocks is now the default; the drill must simply never pass `--restore-with-local-blocks` (`duplicati-cli help no-local-blocks`).
7. Portable mode is a data-root switch: with `--portable-mode` the server reads `<install>/data`; without it, the profile of the running user. "Job disappeared" after a restart is a wrong data directory, not data loss (YAM §8.19.4). The 2.4.0.0 resolution order is `--server-datafolder` > `--portable-mode` > `DUPLICATI_HOME` > `~/.config/Duplicati`, and **there is no automatic portable mode** (`Duplicati/Library/AutoUpdater/DataFolderManager.cs`, `GetDataFolder`). **This
   design removes the ambiguity by always passing `--server-datafolder`** (§7.3.2).
8. The server database is key material: without a settings key it stores the backup passphrase in cleartext (YAM §8.19.3 correction block; primary statement §8.20.2). Never dump or diff it into a transcript.
9. Record the passphrase outside the backup and off the source disk; a key file excluded from the backup on the same disk as the sources is not escrow (YAM §8.18).
10. `--dbpath` on every CLI operation; a hand-written `dbconfig.json` is a stale locator the CLI would fail to parse or ignore, creating a fresh random database rather than opening the intended one (YAM §8.6-5, §8.12.4: "Misleading rather than dangerous … Always pass `--dbpath` regardless").
11. Never run `Repair` against a database that disagrees with its archive; never `kill -9` Duplicati (`HANDOFF_2026-08-22_duplicati-dbpath-and-recovery.md` §3).
12. `Paused` plus a non-empty `SchedulerQueueIds` is always a fault; `startup-delay=30m` alone is not (YAM §8.22).
13. A tool that reports on a resource must locate it the way the system does (read `TargetURL`); a hardcoded path produces a confident wrong answer (YAM §8.14). Zero items must be a refusal, not a pass (YAM §8.21).
14. Deployed units execute the **primary checkout's** script by absolute path; merging changes nothing until the primary is pulled, and editing the primary puts unreviewed code into production (`HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §1.6). Copies, not symlinks, was already the rule for the user lane (`util/install_duplicati_timer.bash` header).
15. A correct mechanism paired with a wrong consequence is the arc's recurring failure shape; state what was *run* separately from what was *reasoned* (`HANDOFF_2026-08-21_backup-systematization-design-arc.md` §9, `HANDOFF_2026-08-22_duplicati-dbpath-and-recovery.md` §10).

### 3.4 What the record leaves uncovered (inherited gaps)

`/var/lib/docker/volumes` (16 Juniper volumes) and `/opt/miniforge3/envs` (47 GB) are in **no** tier; the tar lane covers ten repos but not `juniper-legacy` (18 GB, no `.git`) or the parent-level `notes/ prompts/ util/ backups/` (per `APPLICATION_REPOS` at `util/juniper-backup.bash:102`; the 08-21 handoff's §3 table marked both as tar-covered at the time); GitHub-side state has no local copy; the `sops-backup-key.sh` escrow was never confirmed run; offsite was never ruled on
(`HANDOFF_2026-08-21_backup-systematization-design-arc.md` §2.1, §3, O-2, O-5). Owner items still open from YAM §8.25–§8.27:
`sda` SMART never read (it now guards the only local copy), the read-only loop probe of the destroyed `sdc4`, the sdc2 grow, cloud reporting (deferred), the user-lane removal PR, the watchdog `ProgramState` check, the dead `yamaguchi_records_sync.bash`.

### 3.5 Contradictions in the record that this design settles

- YAM §8.20.4 and the 2026-09-07 handoff call the pcalnon file "the schema-19 profile server DB". It is not a server database (§5.3). Corrected in Appendix C.
- YAM §8.20.2 (2026-08-30) records the owner's decision to **reject** `SETTINGS_ENCRYPTION_KEY` ("adds a third key needing escrow"). The 2026-09-18 unit edits and the 2026-09-20 `.env` reverse that decision without a record. This design asks for the decision again, explicitly (D-1).
- The certification's destination `/mnt/Backups/Ubuntu/Yamaguchi` and the README the record says lives at `/mnt/Backups/Ubuntu/README.md` no longer exist at those paths; the live destination and README are under `/mnt/Backups/Ubuntu/Dropbox/Backups/` (§4.4). The move is unrecorded in `notes/`.

---

## 4. Current state — 2026-09-21

### 4.1 Component inventory

| Component | Where | Runs as | State on 2026-09-21 | Evidence |
| --- | --- | --- | --- | --- |
| `duplicati.service` (system) | vendor unit `/usr/lib/systemd/system/duplicati.service`, edited in place (09-21 01:44); no drop-in. A systemd reload at 03:23:44 **armed** the edited `ExecStart` (`'--daemon-opts="${DAEMON_OPTS}"'`); the running process used the older form | `duplicati:duplicati` | active since 09-20 18:19:42; PID 1397393; one argv element `"--webservice-port=8300 "` (trailing space); **the next restart runs the armed form** (§4.3 item 9) | `systemctl show`, `ps`, journal |
| Data folder in use | `/home/duplicati/.config/Duplicati/` (mode **0777**, files 0777) | duplicati | server DB created 18:19:43, schema **12**, **0 backups**, 4 `Failed to import backup` errors (18:39, 18:42) | forensics on a copy; `control_dir_v2/lock_v2` mtime 18:19:45 |
| Abandoned data folder | `/usr/lib/duplicati/data/` (0700, **now owned by `duplicati`**; whole `/usr/lib/duplicati` chowned to `duplicati`) | — | holds the real server DB (fields encrypted under an unidentified key since 09-18 21:03:34) and the per-job index `BMXWPAOGLP.sqlite` | `stat`; journal; snapshot journal |
| Server-DB snapshot (system timer, root) | `yamaguchi-server-db-snapshot.timer` 13:45 UTC | root | still firing daily; last 2026-09-20 08:45 CDT, `integrity ok (16 tables)`, 240 KiB → `~/.local/state/duplicati-server-db/` — **the recovery source** | `journalctl -u yamaguchi-server-db-snapshot` |
| Watchdog (user timer) | `yamaguchi-watchdog.timer` 12:00 local, `Linger=yes` | pcalnon | firing; `UNREACHABLE` 09-19/09-20 (connection refused), `401` 09-21 02:52 (new server, unknown UI credential) | `journalctl --user`, `~/.local/state/duplicati/server-watchdog.log` |
| Disabled CLI lane | `~/.config/systemd/user/duplicati-backup.*` | pcalnon | disabled; deployed runner lacks the 08-29 DB-holder fix; a copy was also run **as `duplicati`** on 09-20 19:07 and refused (`PASSPHRASE is unset`) | `~/.local/state/duplicati/last-run.status`, `/home/duplicati/.local/state/duplicati/` |
| Destination | `/mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi/` on `sda1` (`/dev/sda1` 3.6 T, 400 G used) | — | 877 files / 203 G, all `pcalnon:duplicati 0770`, no ACL entries, no setgid; 9 dlists, newest `20260918T140000Z`; no stray names | `ls`, `find`, `getfacl` |
| Dropbox | root `/mnt/Backups/Ubuntu/Dropbox` (Pro), daemon PID 2948130 | pcalnon, **without gid 139** | "Up to date"; 9 folders excluded, `Backups/` synced; the root also holds personal files, which sync too | `dropbox status`, `exclude list`, `/proc/<pid>/status` |
| Wrapper | `/home/duplicati/bin/duplicati-wrapper.bash` → symlink to the **primary checkout's** `scripts/duplicati-wrapper.bash`; `bin/` is **0777** | — | the target changed three times between 02:15 and 03:14 today (an uncommitted `--daemon-opts` revision → `#1968` → `main` `d721fc78`, i.e. `#1969`, merged 08:07 UTC); parses `.env` with `eval`; debug mode echoes secrets (§4.3) | `diff`, step-2b report |
| `/etc/default/duplicati` | `DAEMON_OPTS="--webservice-port=8300"`; owned **`duplicati:duplicati`** 0644 | — | the service user can rewrite its own start options | `ls -la` |
| `.env` | `/home/duplicati/.config/Duplicati/.env` 0660 duplicati:duplicati, 1,599 B | — | one active line (`SETTINGS_ENCRYPTION_KEY`, 32-char value, single-quoted, contains `$ @ & #`), five commented-out lines carrying `PASSPHRASE_OLD`, `PASSPHRASE` and three spellings of the key; **the active key equals `PASSPHRASE`** | `2026-09-21_env_file_shape.py` |
| Package | `duplicati 2.4.0.0` (upgraded from 2.3.0.4 at 2026-09-19 21:29, reinstalled 21:35) | — | server schema 12 (2.4.0.0) vs 11 (2.3.0.4) | `/var/log/dpkg.log`, forensics |
| Tar lane | `util/juniper-backup.bash` (manual; expects drives `EBC5-F0A3`, `DFF3-2782` under `/media/pcalnon/`) | pcalnon | no timer, path unit, cron or udev rule anywhere; **device detection broken since 2026-09-07** — udisks now mounts under `/run/media/pcalnon/` (§4.5); neither drive is attached now | agent 1b, `ls /media/pcalnon /run/media/pcalnon`, dpkg log |
| pcalnon profile | `/home/pcalnon/.config/Duplicati/` (0700) | — | orphaned since 08-25; `Duplicati-server.sqlite` = 4 KB stub + 112 MB WAL of an aborted local-DB Recreate; `Duplicati-server.backup` = last real profile DB (jobs `Ubuntu`, `Ubuntu-fresh`, `Schedule` empty); 57 GB of job-DB copies under `backups/` | forensics |

### 4.2 Timeline, 2026-09-12 → 2026-09-21 (all times CDT unless marked Z)

| When | Event | Source |
| --- | --- | --- |
| 09-12 → 09-15 | Destination relocated under the new Dropbox root. Scheduled runs 09-13 14:00Z and 09-14 14:00Z fail: `Found 861 files that are missing from the remote storage, please run repair` (the job still pointed at the old path). Ad-hoc run 09-15 08:56Z succeeds after re-pointing. | root-DB snapshot `ErrorLog`; watchdog log; dlist names |
| 09-15 15:27–15:38 | `.dropbox.cache` and `.dropbox` created under `/mnt/Backups/Ubuntu/Dropbox`; at 20:46Z the job fails again with `865 files missing`; two `TaskCanceled` aborts; ad-hoc run 20:48Z succeeds | same |
| 09-16 14:01Z | Scheduled run fails: `Found 6 remote files that are not recorded in local storage … two backups sharing a destination folder … or restoring an old database`. Ad-hoc run 18:33Z succeeds. No stray file remains today. | same |
| 09-17 01:31 | Root server start: `No database encryption key was found. The database will be stored unencrypted.` Runs 09-17 22:13Z and **09-18 14:00Z succeed** (the last success). | journal |
| 09-18 19:57 | Unit switched to `User=duplicati`. Crash loop: `Access to the path '/usr/lib/duplicati/data/installation.txt' is denied` (portable data folder root-owned). Repeats 20:02. | journal |
| 09-18 20:22 | Starts OK (data folder made accessible), still unencrypted. 20:26 `Failed to process the path: Access to the path '/mnt/Backups' is denied` (destination not yet group-readable). | journal |
| 09-18 21:03:27 | Start **with** a settings key, no warning → fields of the root DB encrypted; `/usr/lib/duplicati/data` mtime 21:03:34 | journal, `stat` |
| 09-18 21:08 → 21:11 | Three crash loops: `SettingsEncryptionKeyMismatchException: Encryption key used to encrypt target settings does not match current key` | journal |
| 09-18 21:15 → 21:29 | `Environment=SETTINGS_ENCRYPTION_KEY=…%6%x…` rejected by systemd (`Failed to resolve specifiers … Invalid slot`, 23 occurrences) → `SettingsEncryptionKeyMissingException`; one unit revision with the key inside `ExecStart` was fatal to load | journal |
| 09-19 19:14 | Same `Missing` loop; `/usr/lib/duplicati/data` chowned to `duplicati` (ctime 19:15:00) | journal, `stat` |
| 09-19 19:19–20:44 | First wrapper revision: 20 starts die with `wrapper.bash: line 30: --webservice-port=8300: command not found` | journal |
| 09-19 20:48, 21:41–21:55 | Wrapper echoes `--webservice-port=8300 --portable-mode`; server fails 25 times with `Access to the path '/home/duplicati/.config/Duplicati/Duplicati-server.sqlite' is denied` — the options arrived as one argv word, so `--portable-mode` was inert and the home folder (holding a pcalnon-owned copy) was used; one attempt at 20:48 reaches the copy and reports `The database has version 19 but the largest supported version is 11` (2.3.0.4) | journal |
| 09-19 21:20, 21:57 | Two starts succeed **on port 8200** — the port option was equally inert | journal |
| 09-19 21:20 | pcalnon TrayIcon crashes on its own profile with the same "version 19" message | `Duplicati.GUI.TrayIcon-crashlog.txt` |
| 09-19 21:29, 21:35 | Package upgrade 2.3.0.4 → 2.4.0.0 (twice) | `dpkg.log` |
| 09-20 04:15–04:43 | pcalnon profile files copied into `/home/duplicati/.config/Duplicati/` | inode birth times |
| 09-20 13:32–13:37, 16:50, 17:30 | Four successful starts of the wrapper-launched server; the first (13:32:46) still echoes `--portable-mode` and listens on 8200 (options inert again); from 13:36:37 `DAEMON_OPTS` no longer carries `--portable-mode` and the server listens on 8300. Which data folder each of these starts opened cannot be read from the journal | journal |
| 09-20 16:39–16:53 | `.env` created; `/etc/default/duplicati` rewritten; wrapper symlink created; 16:41 `encrypted, but no key`, 16:44 `Mismatch`; the wrapper in debug mode echoes every `.env` line to the journal (220 lines, 50 of them commented-out assignments) | journal, `stat`, counts |
| 09-20 17:57:56 | The 112 MB WAL copied next to the 4 KB stub; 18:02 and 18:12: `version 19 but the largest supported version is 12` | inode birth, journal |
| 09-20 18:19:26 | WAL moved into root-owned `temp/`; 18:19:42 start; 18:19:43 fresh WAL; 18:19:46 `Server has started` (a key **was** supplied — no "no key" warning); 18:39 and 18:42 four `Failed to import backup` | inode times, journal, forensics |
| 09-20 22:26Z, 22:59Z | PRs juniper-ml#1967 and #1968 merge the wrapper (#1968's body is the unfilled PR template; #1967's is one generated sentence plus the template) | `gh pr view` |
| 09-21 02:52 | Watchdog: `login failed (401)` | watchdog log |

### 4.3 The wrapper lane as built (defects)

Read from `scripts/duplicati-wrapper.bash` at `#1968` (`52571621`, line numbers below) and at `main` `d721fc78` (`#1969`, which adds a `--daemon-opts` block at its lines 110–123 and drops the `DAEMON_OPTS` environment branch). The step-2b agent ran shellcheck 0.10.0 and 0.11.0 at every severity (clean on both revisions) and 40 synthetic-input cases against an exec-neutered copy; the literal outputs are in its report (§11). The findings:

1. `exec "${DUPLICATI_SERVER}" "${DUPLICATI_OPTS}"` (line 199) passes **all** options as **one** argv element with a trailing space. It works today only because there is exactly one option; two options arrive glued (`ARGV[1]=<--webservice-port=8300 --webservice-interface=loopback >`). This is not theoretical: on 09-19 the same construction made `--portable-mode` and `--webservice-port` inert (§4.2).
2. `DUPLICATI_INPUT_PARAMS=("${*}")` and `DUPLICATI_ENV_VARS_GLOBAL=("${DAEMON_OPTS}")` (lines 102, 105) are one-element arrays; the dedup logic keys on the text before the first `=` of the whole blob, and `grep -- "${KEY}"` matches substrings, so `--webservice-port-x=1` suppresses `--webservice-port=8301` **and** the default port, and `--log-file` suppresses `--log`.
3. The `.env` parser (lines 107–148) runs `eval "export KEY=VALUE"`: `TEST_SEMI=a;echo INJECTED` prints `INJECTED`; `$(…)` and backticks execute; `$HOME` and `$1` expand; a value with a space is truncated at the space; values are cut at the second `=`; a `.env` line `DUPLICATI_SERVER=/tmp/x` redirects the `exec` target and `DEBUG_MODE=0` switches secret printing on. "Already defined" is `env | grep KEY`, a substring over every name and value (`PASSPHRASE_FILE=` set earlier
   suppresses `PASSPHRASE`). CR bytes are kept; the last line without a newline is dropped; an unbalanced quote makes `eval` print `unexpected EOF while looking for matching` to stderr (the journal), drop the line and continue with exit status 0. The current key survives only because it is single-quoted.
4. `DEBUG_MODE` (line 196) prints `env | grep SETTINGS_ENCRYPTION_KEY`, and lines 112/133 echo every `.env` line and every export; in PR #1967's first revision the key print was unconditional; line 197 echoes the full option string unconditionally, so any secret passed as an option (`--webservice-password=`) reaches the journal and `/proc/<pid>/cmdline`. The journal shows the consequence (§6).
5. No `set -euo pipefail`; every failure above exits 0 and the server starts misconfigured. `DUPLICATI_ENV_GLOBAL` is defined and never read (precedence level 2 exists only because systemd sets `DAEMON_OPTS`).
6. No default data folder: the server falls back to `~/.config/Duplicati` of whichever user runs it, or to `<install>/data` when `--portable-mode` is given. The 08-25 restart trap is reintroduced by construction.
7. The header comment (lines 38–57) carries a credential-shaped 36-character literal (an old settings key). The repository is **public** (`gh repo view`: `visibility: PUBLIC`); gitleaks passed both PRs.
8. The live symlink points into a developer checkout on a feature branch; `git checkout`, `git worktree remove` or an unfinished edit changes what the service runs on its next start. `/home/duplicati/bin` and `/home/duplicati/.config/Duplicati` are world-writable, so any local user can replace the script or the database.
9. The unit now loaded (`ExecStart=… '--daemon-opts="${DAEMON_OPTS}"'`, armed by a global systemd reload at 03:23:44 on 09-21) and both wrapper revisions are mutually incompatible: systemd unquotes first and substitutes second, so the wrapper receives the single word `--daemon-opts="--webservice-port=8300"` (inner quotes literal). `#1968` passes it through as an unknown option and suppresses the default port; `d721fc78` — the revision the live symlink has resolved to since
   03:13:57 — extracts `"--webservice-port` (no value, stray quote) and ignores the
   `DAEMON_OPTS` environment entirely. **The next restart or reboot therefore brings the server up on Duplicati's default port 8200, or not at all**, and the watchdog reads `UNREACHABLE`. Do not restart the current unit before §8 P0 step 4 installs the corrected unit and wrapper.
10. The vendor unit was edited in place (`dpkg` md5 mismatch; not a conffile): the next package upgrade silently restores `ExecStart=/usr/bin/duplicati-server $DAEMON_OPTS` as root.
11. PR #1969's body describes "a new script for backup tests that securely prints and shreds the key escrow sheet"; the only such thing in its diff is `notes/backup_tests_pre-and-post_reboot.md`, a 100 %-similarity rename of the repo-root file `____TODO__DO-ME-AFTER-REBOOT____` (added in `ea83bad7`, #1494, 2026-08-30): 14 lines of bash that print (`lpr`) and `shred -u` the escrow sheet, then run the census and `yamaguchi_reboot_verify.bash`. It carries a `.md` extension,
    lives in `notes/`, and does not follow the notes naming convention.

### 4.4 Destination, Dropbox, permissions

- `/mnt/Backups`, `/mnt/Backups/Ubuntu`, `/mnt/Backups/Ubuntu/Dropbox`, `…/Backups`, `…/Backups/Yamaguchi` are all `drwxrwx--- pcalnon:duplicati`, no default ACLs, no setgid bit. All 877 volumes are `-rwxrwx--- pcalnon:duplicati` (0770 on data files; the execute bit is unnecessary).
- New volumes written by the `duplicati` user will be owned `duplicati:duplicati`; their mode follows the service umask. Dropbox runs as `pcalnon` **without** the `duplicati` supplementary group (the daemon predates the group membership; group membership is granted at login, not retroactively), so it can read those files only through the `other` bits or after a restart in a session that carries gid 139. This is a latent break in R-8 (§7.4 fixes it).
- The Dropbox root is the whole `/mnt/Backups/Ubuntu/Dropbox`; the statement "syncs only the contents of Backups/" is not what the client is configured to do — nine named folders are excluded and everything else at the root (personal photos and PDFs included) syncs.
- Personal, unrelated files live beside the backup tree in the same Dropbox root; the `Backups/` tree also holds the frozen set (`_yamaguchi_frozen_20260826/`, 811 volumes), the ten retained old-archive dlists, `_yamaguchi_keys/` (a passphrase escrow copy) and `_yamaguchi_records/`. **The key escrow copy is therefore now synced to the cloud** beside the ciphertext it unlocks — the "same seizure yields both" limitation the escrow README accepted for `sda1` now extends to the Dropbox account (§6).

---

### 4.5 Tier 2 device detection has been broken since 2026-09-07

`util/juniper-backup.bash` finds its drives at `/media/pcalnon/<UUID>` (`MOUNT_NAME="media"`, `USER_NAME="pcalnon"`,
`target_dir_for`; lines 122–124 and 303–305) and requires each to be a mountpoint. On 2026-09-07 17:09 the host's
`udisks2` was upgraded to 2.10.91-1ubuntu2.1, whose Debian changelog reads "Use /run/media instead of /media as mountpoint
for removable media"; the daemon binary now carries only `/run/media/%s`; `/run/media/pcalnon/` was created at the first
automount after the upgrade (2026-09-11 22:17) and last changed 2026-09-16; `/media/pcalnon/` holds only two hand-made
directories. Every tar-lane run since 09-07 therefore reads `SKIP … not a mount point` for both drives and exits 1 with
"no usable device", whatever is plugged in. The record's last drills (2026-08-26, 2026-08-28) predate the change. Found by
the step-3 validation (Lane A3), not by any monitor — the lane has no timer or alerting, which is what §7.8 adds. Fix:
§7.8 and §7.9 move the mount root to `/run/media/pcalnon/` for the automount case and, preferably, to UUID-keyed fstab
entries under `/mnt/` that do not depend on a desktop session at all (D-10).

## 5. Root-cause analysis: "the server on :8300 has no backups defined"

### 5.1 The premise under test

The owner's premise: the new config directory is identical to the previously used one, therefore the new server should show the same backups. The premise is true byte-for-byte for `Duplicati-server.sqlite` (identical SHA-256) and false in what it assumes: that directory was not the running server's data folder, and the file is not a server database.

### 5.2 Leg A — the copied profile was not the production data folder

Observations:

- The snapshot timer's journal reads `source : /usr/lib/duplicati/data/Duplicati-server.sqlite (240.0 KiB)` every day through 2026-09-20 08:45. That is the folder a `--portable-mode` server uses; `/etc/default/duplicati` still carries the commented `DAEMON_OPTS="--webservice-port=8300 --portable-mode"` variant.
- The 2026-09-20 snapshot (copied and read read-only) holds `Backup` ID 2 `Yamaguchi`, `DBPath=/usr/lib/duplicati/data/BMXWPAOGLP.sqlite`, `Schedule Time=1789740000 (2026-09-18T14:00:00Z) Repeat=1D`, 2 `Source` rows, 45 `Filter` rows, 10 job `Option` names, `Metadata.LastBackupDate=20260918T140000Z`, `BackupListCount=9`, `TargetFilesCount=877`.
- The pcalnon profile's `Duplicati-server.sqlite` and its WAL have not been modified since 2026-08-25 02:20:46, while backups continued daily through 09-18 (dlists 08-25 … 09-18).
- The pcalnon profile's `Duplicati-server.backup` (2026-08-25 02:19:47, schema 11) lists `Ubuntu` (id 2, `SJTCQIIZSJ.sqlite`) and `Ubuntu-fresh` (id 3, `DQRVQNDIFX.sqlite`), an **empty** `Schedule` table and a final notification `Error while running Ubuntu: A task was canceled.` at 02:19:46. `Yamaguchi` does not appear.

Refutation test: a server started on a copy of `/usr/lib/duplicati/data/` with the right key lists `Yamaguchi`; a server started on a copy of the pcalnon profile can list it under no key. The first half is Procedure A in §8.

### 5.3 Leg B — the copied `Duplicati-server.sqlite` is an aborted per-job Recreate

`2026-09-21_duplicati_server_db_forensics.py` on a copy of the three files (`.sqlite` 4,096 B, `-wal` 112,587,272 B / 27,327 frames, `-shm`):

- SQLite header: page size 4096, WAL mode, **database size 1 page**, schema cookie 0.
- After WAL replay: 45 pages, 19 tables — `Block, BlocklistHash, Blockset, BlocksetEntry, ChangeJournalData, Configuration, DeletedBlock, DuplicateBlock, FileLookup, Fileset, FilesetEntry, IndexBlockLink, LogData, Metadataset, Operation, PathPrefix, RemoteOperation, Remotevolume, Version` — the **local (per-job) database** schema, `Version = 19`. `Operation` holds one row: `(1, 'Recreate', 1787642388)` = 2026-08-25 02:19:48 CDT. `Configuration` holds only
  `repair-in-progress`. `Remotevolume` and `Fileset` are empty.
- The server-database schema has 16 tables (`Backup, Schedule, Filter, Option, Metadata, …`) at version 11 (2.3.0.4) or 12 (2.4.0.0). Both versions of Duplicati therefore refused the file: journal 2026-09-19 20:48 (`largest supported version is 11`), 2026-09-20 18:02 and 18:12 (`… is 12`).

Mechanism: one second after Duplicati saved the profile server DB (`Duplicati-server.backup` and `backups/backup Duplicati-server 20260825021947.sqlite`, both 02:19:47), a **Recreate wrote a new local database into the server-database path**, and was cancelled. The main file was left at one page with every write in the WAL. This is consistent with the 2026-08-22 handoff's finding that the `Ubuntu` job's `DBPath` had been silently changed to the server DB path and with the
cancelled `Repair`/`Verify` at 02:19:19–02:19:46. From that moment the pcalnon profile had no server database at all; the production job was recreated on the root server the same morning (YAM §3).

The current server DB: created 2026-09-20 18:19:43 (WAL born 18:19:43.917, 90 frames, salts `0cd60a99/6d70864b`) on the same 4 KB stub after the 112 MB WAL was moved to `temp/` at 18:19:26; schema version 12; `Backup` 0 rows; `ErrorLog` 4 rows `Failed to import backup` — two `JsonReaderException: Unexpected character encountered while parsing value: S` (a file starting with `SQLite format 3` was offered as an export) and two `SharpAESCrypt.WrongPasswordException` (an
encrypted export or volume with the wrong password).

Refutation test: a server database with a `Backup` table cannot have the `Remotevolume` table; `sqlite3 -readonly` on the copy shows which tables exist.

### 5.4 Leg C — the production database was locked behind a key that changed

Journal sequence (Appendix A.1): unencrypted through 09-18 20:42 → first start with a key at 21:03:27 (no warning; data folder mtime 21:03:34) → `Mismatch` from 21:08 → `Missing` from 21:15 after systemd rejected `Environment=SETTINGS_ENCRYPTION_KEY=<36 chars with %6 and %x>` (`Failed to resolve specifiers … Invalid slot`; a `%` in a unit-file `Environment=` value is a specifier, and an unknown specifier voids the whole assignment) → same on 09-19 19:14 → the folder abandoned for the pcalnon copy.

What the key at 21:03 was is not in the journal. One fact narrows it: `EnvironmentFile=` values are **not** specifier-expanded (`man systemd.exec`: an unquoted value is parsed with shell backslash rules, interior text preserved verbatim), so the 36-character literal placed in `/etc/default/duplicati` would have been delivered intact, where the same text in `Environment=` was rejected twelve minutes later — and that literal is the value the operator was demonstrably trying to
deliver at 21:15 and 21:23. The candidate order for Procedure A is therefore: (1) the 36-character literal from the wrapper's comment block, verbatim; (2) the `PASSPHRASE` value (today's `.env` key); (3) any other value the operator typed on 09-18 between 20:42 and 21:03 — the root shell's history is the only record. The later successful starts (09-19 21:20 and 21:57, 09-20 13:32–17:30) do **not** identify the key or the folder: the wrapper's single-argv defect made
`--portable-mode` inert on some of them, and a start on an empty folder creates a fresh database under whatever key is present without complaint. The `Mismatch` at 09-20 16:44 likewise says only that the folder in use then held fields encrypted under a key other than today's `.env` key. If no candidate opens the copy, the fields can be **wiped** rather than recovered: `duplicati-database-tool wipe-encryption` "removes or clears any encrypted strings from the server database
so it can be used without the original encryption key" (2.4.0.0 help; added in 2.3.0.108), after which the two wiped values that matter — `TargetURL` and the job passphrase — are re-entered from known sources (§8 P0, Procedure A2).

### 5.5 Contributing factors

- **Portable mode by flag, never by inference.** The vendor unit never named a data folder; `--portable-mode` lived in `DAEMON_OPTS` (still present in the 09-20 13:32 wrapper echo, gone at 13:36). Duplicati resolves the folder as `--server-datafolder` > `--portable-mode` (`<install dir>/data`) > `DUPLICATI_HOME` > `~/.config/Duplicati`, with no automatic detection of a `data/` directory (`DataFolderManager.GetDataFolder`; the step-2c agent also ran a sandboxed 2.4.0.0 server
  with `/usr/lib/duplicati/data` present and it wrote to `$HOME/.config/Duplicati`). So the 09-18 19:57 crash was the flag plus a root-owned folder, and every later switch of folder was a change to `DAEMON_OPTS` or to what the wrapper managed to pass through. Fixed by an explicit `--server-datafolder` (§7.3.2).
- **Data-folder permission gate.** Shipped in canary 2.3.0.107 (2026-07-13) and first stable in 2.4.0.0 — so on this host it first applied with the 09-19 package upgrade — the server refuses a pre-existing data folder at every start unless it is mode 0700 with no group/other bits and owned by the running user or root (`PrepareSecureDataFolder`; overrides: `--allow-insecure-datafolder`, the env form `DUPLICATI__ALLOW_INSECURE_DATAFOLDER=true`, or an `insecure-permissions.txt`
  marker in the install folder). The migration chmod'ed the folder to 0777 *after* the 18:19 start; the next start may refuse it. §7.3.2 sets 0700.
- **Package upgrade mid-migration.** 2.3.0.4 → 2.4.0.0 on 09-19 21:29 raised the server schema from 11 to 12 and changed the `Backup` table (`OperationType` column). Any recovered database is upgraded on first open; keep the pre-upgrade copy.
- **Permissions by trial.** `/usr/lib/duplicati` (binaries included) and `/usr/lib/duplicati/data` were chowned to `duplicati`; the destination tree chgrp'd; the duplicati home dirs opened to 0777. Each removed a symptom; none was recorded.
- **Wrapper defects** (§4.3) turned a one-line configuration into a parser with `eval`, an argv bug and a debug mode that logs secrets.
- **No runbook** existed for "move the server to another user" although the record already contained every trap it hit (YAM §8.19.4, §8.20).

### 5.6 What refutes each leg, and the instruments

| Leg | Would be refuted by | Instrument used | Could the instrument have said otherwise? |
| --- | --- | --- | --- |
| A | `Yamaguchi` rows in a pcalnon-profile database, or `LastBackupDate` advancing in it after 08-25 | forensics on copies of `Duplicati-server.sqlite`+WAL and `Duplicati-server.backup`; snapshot journal | yes — it printed `Yamaguchi` from the root snapshot and would have printed it from the profile |
| B | a `Backup` table in the replayed WAL, or a `Version` row ≤ 12 | forensics (table list, `Version`, `Operation`) | yes — the same code printed 16 server tables for the other three databases |
| C | a `Started` line between 09-18 21:08 and 09-20 13:32 without a `Mismatch`/`Missing` error | `journalctl -u duplicati.service`, deduplicated | yes — it shows exactly such lines at 09-20 13:32 |

### 5.7 Corrections to the record

Listed in Appendix C; the load-bearing one: "schema-19 profile server DB" → "aborted local-DB Recreate stub written over the profile server DB at 2026-08-25 02:19:48; the last real profile server DB is `Duplicati-server.backup` of 02:19:47".

---

## 6. Secret exposure inventory and remediation

| # | Secret | Where it is exposed | Since | Who can read it | Remediation |
| --- | --- | --- | --- | --- | --- |
| S-1 | Old settings key (36 chars) | `scripts/duplicati-wrapper.bash` comment, lines 38–57, in `main` since #1967; 23 systemd `Failed to resolve specifiers` journal lines | 2026-09-18 / 09-20 | anyone with the repository (public); local `adm`/`systemd-journal` members and root | Treat as burned: use it only to unlock the 09-18 database (Procedure A), then re-key (P1); remove the block from the script. A history rewrite is not worth its cost once the key is dead. Close the detection gap (below). |
| S-2 | Current settings key = **`PASSPHRASE`** (32 chars) | `.env` line 22 (0660 duplicati:duplicati — readable by group `duplicati`, i.e. `pcalnon`); journal: 10 `Exporting Environment Variable` lines and 10 `Settings Encryption Key:` lines on 09-20 16:41–16:44 | 2026-09-20 | same as S-1 (journal) | Never reuse the backup passphrase as the settings key: the key exists to protect the passphrase at rest. Generate a distinct key (P1), deliver it as a systemd credential, escrow it with the passphrases. |
| S-3 | `PASSPHRASE`, `PASSPHRASE_OLD` | `.env` lines 17–18 as commented-out assignments; journal: 50 `LINE: "# export …"` echoes on 09-20 | 2026-09-20 | same | Delete the commented lines. **Rotation does not re-encrypt existing volumes**; the exposure is local (root, `adm`, group `duplicati`). Decision D-2: accept with a journal scrub, or start a new set under a new passphrase. |
| S-4 | Same passphrases in `/mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_keys/env` | now inside the Dropbox-synced tree | since the Dropbox root moved onto `sda1` | the Dropbox account | Move `_yamaguchi_keys/` out of the Dropbox root (a sibling of `Dropbox/` on `sda1`), or exclude it with `dropbox exclude add`. The sda1 escrow was accepted as a *machine-local* copy, not a cloud copy (its README). |
| S-5 | Web-UI credential | primary checkout `.env` (`DUPLICATI_WEB_CREDENTIAL`), **mode 0664 — world-readable**, now stale | since 2026-08-23 | every local user | New UI password on the rebuilt server, stored in `~/.config/duplicati-backup/web-credential` (0600); API client re-pointed (§7.6). Remove `util/ad-hoc/duplicati_api.py`'s bare-secret fallback (posts the whole file as the password when no candidate key matches; its list omits `DUPLICATI_WEB_CREDENTIAL`, so it takes that path today). |
| S-6 | Sign-in token URL | journal 09-20 18:19:46 (`signin.html?token=…`, 5-minute lifetime, expired) | — | — | None needed; note that the server prints one on every start when no password is set — set the password. |

Detection gap behind S-1: the repository has GitHub secret scanning and push protection enabled, but
`secret_scanning_non_provider_patterns` is **disabled** (`gh api repos/pcalnon/juniper-ml --jq .security_and_analysis`),
so a generic key literal is never flagged, and gitleaks passed both PRs. Enable the non-provider patterns and add a
gitleaks rule for `SETTINGS_ENCRYPTION_KEY=` / `PASSPHRASE=` assignments (inherited requirement JR-DEP-SEC-005 covers the
allowlist half of this class).

Journal scrub (D-8): the journal cannot delete individual lines. `journalctl --rotate` followed by `journalctl --vacuum-time=1s` removes every archived file, i.e. all history older than the rotation; `--vacuum` never touches the active file, so run the rotate first and accept the loss of unrelated history, or leave the journal and rely on its `systemd-journal`/`adm` access control. Either way, S-1 and S-2 stop mattering once both keys are rotated; S-3 matters as long as the current set is in service.

---

## 7. Integrated design

### 7.1 Principles

1. **One explicit source of truth per path.** The data folder, the destination, the tempdir and the credential locations are named in one place each (unit + `/etc/default/duplicati`), never inferred from `HOME`, from a `data/` directory beside a binary, or from a hardcoded string in a tool.
2. **Secrets never pass through a shell parser or a log.** The settings key arrives as a systemd credential; the passphrase stays inside Duplicati's database and the escrow files; no script echoes a file or the environment.
3. **Least privilege with one deliberate exception.** The server runs as `duplicati`, confined by systemd, and is granted `CAP_DAC_READ_SEARCH` so it can read every file under `/home/pcalnon` — the root-era coverage — without being root (D-4).
4. **Copies, not symlinks, for anything a unit executes**, installed by a script that verifies a checksum. Development happens in the repository; deployment is a step.
5. **Group `duplicati` is the sharing boundary.** Directories are setgid, files are group-writable, umask `0007`; `pcalnon` gets everything through membership.
6. **Every lane fails loudly.** `OnFailure=` on the service, a watchdog that asks from outside, a pre-backup guard that refuses an unmounted or foreign destination, status files with timestamps.
7. **Restore drills, not exit codes, prove a tier** — carried from PLAN §7 and YAM §5.3 unchanged.

### 7.2 Tier architecture

| Tier | Medium | Mechanism | Cadence | Encryption | Key custody |
| --- | --- | --- | --- | --- | --- |
| T1 | `/dev/sda1` → `/mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi/` (on-host, separate spindle) | Duplicati server job `Yamaguchi`, `duplicati` user | daily 14:00 UTC | AES (built-in) under `PASSPHRASE` | escrow: printed sheet, password manager, `sda1` copy *outside* the Dropbox root |
| T1c | Dropbox (cloud) | Dropbox desktop client replicating `Backups/` from the T1 destination (alternative: `duplicati-sync-tool`, D-3) | continuous | ciphertext as written by T1 | same |
| T2 | two USB drives `EBC5-F0A3`, `DFF3-2782` | `util/juniper-backup.bash`, per-repo `tar -cj` streamed into `gpg -e` for two YubiKey-backed recipients | weekly window, catch-up on plug-in (§7.8) | OpenPGP asymmetric | YubiKeys (two), offline backups per the record |
| T3 | external hard drive, kept offline | same script, `--repos` widened to the whole Juniper parent (`juniper-legacy`, `notes`, `prompts`, `util`, `backups`) plus `--label full` | monthly, when attached (§7.9, D-5) | OpenPGP asymmetric | same |
| T0 | server brain | `Duplicati-server.sqlite` snapshot into the T1 source, daily 13:45 UTC | daily | inside T1 | — |

### 7.3 Tier 1 — the Duplicati service

#### 7.3.1 Identity and privilege

- User `duplicati` (uid 133, gid 139), home `/home/duplicati`, shell `/usr/sbin/nologin` once the migration is accepted (R-6). Administrative work: `sudo -u duplicati -- <cmd>` or `runuser -u duplicati --`.
- Group `duplicati` members: `duplicati`, `pcalnon`. Membership takes effect at the next login of `pcalnon`; long-running processes started before (the Dropbox daemon, terminal sessions) must be restarted to carry gid 139 — verify with `grep ^Groups /proc/<pid>/status`.
- The service receives `AmbientCapabilities=CAP_DAC_READ_SEARCH` with `CapabilityBoundingSet=CAP_DAC_READ_SEARCH` and `NoNewPrivileges=yes`: it can read and traverse any file (0700 directories under `/home/pcalnon` included) but cannot write outside its own permissions. Without this the first `duplicati`-user backup would silently omit every mode-0700 tree (`~/.ssh`, `~/.gnupg`, `~/.config/*`, `~/.cache/*`), reporting *Warning*, not *Fatal*. Acceptance criterion AC-3 measures this.
- `/usr/lib/duplicati` returns to `root:root` (a service user must not own its own binaries); `/usr/lib/duplicati/data` is archived and removed after recovery (§8 P4).

#### 7.3.2 Data folder, defaults file, unit

Data folder: `/home/duplicati/.config/Duplicati/` (owner's choice), **always** passed as `--server-datafolder=` so neither `HOME` nor `--portable-mode` can redirect it. Mode **`0700 duplicati:duplicati`**, files `0600`: Duplicati 2.4.0.0 verifies a pre-existing data folder at every start and refuses one with any group or other bit ("A pre-existing folder is never modified … otherwise it is rejected", `DataFolderManager.PrepareSecureDataFolder`; the only overrides are `--allow-insecure-datafolder`,
`DUPLICATI__ALLOW_INSECURE_DATAFOLDER=true` or an `insecure-permissions.txt` marker in the install folder, none of which this design uses). `pcalnon`'s read access to the server database (R-7) is through `sudo -u duplicati` or the daily snapshot copy in `~/.local/state/duplicati-server-db/` — the database is key material (rule 8), so this is the right boundary.

```ini
# file: etc/default/duplicati
# Read by systemd (EnvironmentFile=), NOT by a shell: no variable expansion, no command
# substitution, no secrets. Each whitespace-separated word of DAEMON_OPTS becomes one argv
# element of the wrapper ($DAEMON_OPTS, unbraced, in ExecStart=). Owned root:root 0644.
# Under decision D-1 "keep encryption", append --require-db-encryption-key so a missing
# credential stops the server instead of silently starting it unencrypted.
DAEMON_OPTS="--webservice-port=8300 --webservice-interface=loopback --server-datafolder=/home/duplicati/.config/Duplicati"
```

The unit is a **full unit in `/etc/systemd/system/`**, which takes precedence over the vendor file and survives package upgrades (a drop-in would also work, but `ExecStart=` must then be reset with an empty assignment first; a complete file is easier to review).

```ini
# file: etc/systemd/system/duplicati.service
[Unit]
Description=Duplicati backup server (Yamaguchi job, dedicated service user)
Documentation=file:///home/pcalnon/Development/python/Juniper/juniper-ml/notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md
After=network-online.target local-fs.target
Wants=network-online.target
# The destination and the data folder must be mounted before the server starts, and the
# server stops if either is unmounted (an unmounted destination reads as "everything missing").
RequiresMountsFor=/mnt/Backups /home/duplicati
StartLimitIntervalSec=10min
StartLimitBurst=5

[Service]
Type=simple
User=duplicati
Group=duplicati
UMask=0007
Nice=19
IOSchedulingClass=idle
IOSchedulingPriority=7
EnvironmentFile=-/etc/default/duplicati
# The settings encryption key: a root-only file, exposed to the service as
# $CREDENTIALS_DIRECTORY/settings-key (never in the environment block, never on argv).
LoadCredential=settings-key:/etc/credstore/duplicati-settings-key
ExecStart=/usr/local/lib/duplicati/duplicati-wrapper.bash $DAEMON_OPTS
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
SystemCallArchitectures=native

[Install]
WantedBy=multi-user.target
```

Notes: `PrivateTmp=yes` gives the server a private `/tmp` that is still `tmpfs`; the job's `--tempdir` therefore moves to `/home/duplicati/.cache/duplicati-tmp` (ext4, inside `ReadWritePaths`). The old tempdir `/home/pcalnon/.cache/duplicati-tmp` is read-only to the service under `ProtectHome=read-only`, which is what we want — it was a root-era choice. `RequiresMountsFor=` also orders the unit after `mnt-Backups.mount`.

#### 7.3.3 The wrapper, rewritten

Requirements it meets: R-4 precedence, no `eval`, arrays for argv, fail-closed parsing, credential-first key delivery, preflight of the data folder and the destination mount, a `--print-command` mode that redacts.

```bash
# file: usr/local/lib/duplicati/duplicati-wrapper.bash
#!/usr/bin/env bash
# Duplicati server launcher for duplicati.service (runs as the duplicati user).
#
# Project:      juniper-ml
# Sub-Project:  backup infrastructure
# Author:       Paul Calnon
# Version:      2.0.0 (design draft 2026-09-21)
# License:      MIT
#
# Option precedence, lowest to highest -- a later source overrides an earlier one for the SAME
# option name; distinct options accumulate:
#   1. DEFAULT_OPTS below
#   2. --option lines in the .env file        (/home/duplicati/.config/Duplicati/.env)
#   3. DAEMON_OPTS, delivered by systemd as separate argv words (EnvironmentFile=/etc/default/duplicati)
#   4. further argv words appended after DAEMON_OPTS
# KEY=VALUE lines in the .env file are exported if the name is on the allow-list below; a variable
# already present in the environment is NOT overridden (systemd's environment wins). The settings encryption key is read from
# $CREDENTIALS_DIRECTORY/settings-key when systemd supplies it (LoadCredential=), otherwise from
# SETTINGS_ENCRYPTION_KEY if the environment or the .env file set it.
# No eval. No word-splitting of file content. No secret value is ever printed.
set -euo pipefail

readonly DUPLICATI_SERVER="${DUPLICATI_SERVER:-/usr/bin/duplicati-server}"
readonly ENV_FILE="${DUPLICATI_ENV_FILE:-/home/duplicati/.config/Duplicati/.env}"
readonly DATA_FOLDER="${DUPLICATI_DATA_FOLDER:-/home/duplicati/.config/Duplicati}"
readonly REQUIRE_MOUNT="${DUPLICATI_REQUIRE_MOUNT:-/mnt/Backups}"
readonly CRED_NAME="settings-key"
readonly ENV_EXPORT_ALLOW='^(SETTINGS_ENCRYPTION_KEY|DUPLICATI__[A-Z0-9_]+|TMPDIR|TZ|LANG|LC_ALL)$'
DEFAULT_OPTS=(
    "--webservice-interface=loopback"
    "--webservice-port=8300"
    "--server-datafolder=${DATA_FOLDER}"
)

declare -A OPT_VALUE=()   # option name -> the full word ("--name=value" or bare "--name")
declare -a OPT_ORDER=()   # first-seen order, for a stable command line
PRINT_ONLY=0

log() { printf '%s: %s\n' "${0##*/}" "$*" >&2; }
die() { log "FATAL: $*"; exit 78; }   # 78 = EX_CONFIG

is_option() { [[ "$1" =~ ^--[A-Za-z0-9][A-Za-z0-9-]*(=.*)?$ ]]; }

add_opt() {
    # add_opt <source-label> <word>
    local src="$1" word="$2" name
    is_option "${word}" || die "${src}: not a Duplicati option: '${word}'"
    name="${word%%=*}"
    if [[ -z "${OPT_VALUE[${name}]+x}" ]]; then
        OPT_ORDER+=("${name}")
    fi
    OPT_VALUE["${name}"]="${word}"
}

strip_quotes() {
    local v="$1"
    if [[ ${#v} -ge 2 && ( "${v:0:1}" == "'" || "${v:0:1}" == '"' ) && "${v: -1}" == "${v:0:1}" ]]; then
        v="${v:1:${#v}-2}"
    fi
    printf '%s' "${v}"
}

load_env_file() {
    # Accepted lines: KEY=VALUE | export KEY=VALUE | --option[=value] | # comment | blank.
    # Anything else is a configuration error: a malformed secret line must not silently
    # become "no key".
    local file="$1" line key value n=0
    if [[ ! -e "${file}" ]]; then
        log "no env file at ${file} (skipping)"
        return 0
    fi
    [[ -r "${file}" ]] || die "env file ${file} exists but is not readable by $(id -un)"
    while IFS= read -r line || [[ -n "${line}" ]]; do
        n=$((n + 1))
        line="${line%$'\r'}"
        line="${line#"${line%%[![:space:]]*}"}"   # drop leading whitespace
        if [[ -z "${line}" || "${line}" == \#* ]]; then
            continue
        fi
        if is_option "${line}"; then
            add_opt "${file}:${n}" "${line}"
        elif [[ "${line}" =~ ^(export[[:space:]]+)?([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
            key="${BASH_REMATCH[2]}"
            value="$(strip_quotes "${BASH_REMATCH[3]}")"
            # Only names the server is meant to read may be exported: this file must not be
            # able to inject LD_PRELOAD, DOTNET_STARTUP_HOOKS or PATH into a process that
            # holds CAP_DAC_READ_SEARCH.
            [[ "${key}" =~ ${ENV_EXPORT_ALLOW} ]] || die "${file}:${n}: ${key} is not an exportable name (allowed: ${ENV_EXPORT_ALLOW})"
            if [[ -n "${!key+x}" ]]; then
                log "${file}:${n}: ${key} already set in the environment; file value ignored"
            else
                export "${key}=${value}"
            fi
        else
            die "${file}:${n}: unparseable line (allowed: KEY=VALUE, export KEY=VALUE, --option[=value], # comment)"
        fi
    done < "${file}"
}

load_settings_key() {
    local cred="${CREDENTIALS_DIRECTORY:-}/${CRED_NAME}" key
    if [[ -n "${CREDENTIALS_DIRECTORY:-}" && -r "${cred}" ]]; then
        key="$(<"${cred}")"
        [[ -n "${key}" ]] || die "systemd credential ${CRED_NAME} is empty"
        export SETTINGS_ENCRYPTION_KEY="${key}"
        log "settings encryption key: systemd credential ${CRED_NAME} (${#key} chars)"
    elif [[ -n "${SETTINGS_ENCRYPTION_KEY:-}" ]]; then
        log "settings encryption key: environment/.env (${#SETTINGS_ENCRYPTION_KEY} chars)"
    else
        log "settings encryption key: NOT SET (the server encrypts nothing new and refuses an encrypted database)"
    fi
}

preflight() {
    # preflight <effective data folder> -- the folder the server will actually receive
    # (--server-datafolder after all sources are merged), not the wrapper's default.
    local folder="$1" owner
    [[ -x "${DUPLICATI_SERVER}" ]] || die "server binary not executable: ${DUPLICATI_SERVER}"
    [[ -d "${folder}" ]] || die "data folder missing: ${folder}"
    [[ -w "${folder}" ]] || die "data folder not writable by $(id -un): ${folder}"
    owner="$(stat -c '%U' "${folder}")"
    [[ "${owner}" == "$(id -un)" ]] || die "data folder ${folder} is owned by ${owner}, not $(id -un)"
    if [[ -n "${REQUIRE_MOUNT}" ]]; then
        mountpoint -q "${REQUIRE_MOUNT}" || die "${REQUIRE_MOUNT} is not a mountpoint; refusing to start a server whose destination lives there"
    fi
}

main() {
    local word name
    local -a argv=()
    for word in "${DEFAULT_OPTS[@]}"; do add_opt "default" "${word}"; done
    load_env_file "${ENV_FILE}"
    for word in "$@"; do
        case "${word}" in
            --print-command) PRINT_ONLY=1 ;;
            *) add_opt "argv" "${word}" ;;
        esac
    done
    load_settings_key
    local eff_folder="${DATA_FOLDER}"
    if [[ -n "${OPT_VALUE[--server-datafolder]+x}" ]]; then
        eff_folder="${OPT_VALUE[--server-datafolder]#--server-datafolder=}"
    fi
    preflight "${eff_folder}"
    for name in "${OPT_ORDER[@]}"; do argv+=("${OPT_VALUE[${name}]}"); done
    if (( PRINT_ONLY )); then
        printf 'would exec: %q' "${DUPLICATI_SERVER}"
        for word in "${argv[@]}"; do
            if [[ "${word}" =~ (password|passphrase|key|token)= ]]; then
                printf ' %q' "${word%%=*}=<redacted>"
            else
                printf ' %q' "${word}"
            fi
        done
        printf '\n'
        exit 0
    fi
    log "exec ${DUPLICATI_SERVER} with ${#argv[@]} option(s): ${OPT_ORDER[*]}"
    exec -- "${DUPLICATI_SERVER}" "${argv[@]}"
}

main "$@"
```

#### 7.3.4 Installation (copies, checksums, no symlink)

```bash
# file: util/install_duplicati_service.bash
#!/usr/bin/env bash
# Install the duplicati.service lane from this repository: wrapper, unit, defaults file.
#
# Project:      juniper-ml
# Sub-Project:  backup infrastructure
# Author:       Paul Calnon
# Version:      1.0.0 (design draft 2026-09-21)
# License:      MIT
#
# Copies, never symlinks: a symlink into a git checkout turns a branch switch or a worktree
# removal into a silent change of what the service executes. Run with sudo. Does NOT restart
# the service; prints the verification commands instead.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WRAPPER_SRC="${REPO_DIR}/scripts/duplicati-wrapper.bash"
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

for pair in "${WRAPPER_SRC}:${WRAPPER_DST}" "${UNIT_SRC}:${UNIT_DST}" "${DEFAULTS_SRC}:${DEFAULTS_DST}"; do
    src="${pair%%:*}"; dst="${pair##*:}"
    cmp -s "${src}" "${dst}" || { echo "checksum mismatch after install: ${dst}" >&2; exit 1; }
    echo "installed ${dst} ($(sha256sum "${dst}" | cut -c1-16))"
done

if [[ ! -s "${CRED_DST}" ]]; then
    printf '%s\n' "NOTE: ${CRED_DST} is absent or empty. Create it before starting:" \
        "      umask 077; openssl rand -base64 48 | tr -d '\\n' > ${CRED_DST}; chmod 0600 ${CRED_DST}" \
        "      and escrow it with the passphrases (it is a third key)." >&2
else
    [[ "$(stat -c '%U:%a' "${CRED_DST}")" == "root:600" ]] || { echo "${CRED_DST} must be root-owned mode 0600" >&2; exit 1; }
fi

systemctl daemon-reload
systemd-analyze verify "${UNIT_DST}"
echo
echo "Next: sudo -u duplicati ${WRAPPER_DST} --print-command  (dry run, no server started)"
echo "      systemctl restart duplicati.service && journalctl -u duplicati.service -n 20"
echo "      systemd-analyze security duplicati.service"
```

`util/systemd/duplicati.service` and `util/systemd/duplicati.default` are the repository copies of the two files shown in §7.3.2; the install script refuses to run unless they exist.

#### 7.3.5 The `.env` contract and the settings key

```text
# file: home/duplicati/.config/Duplicati/.env
# Duplicati server: local overrides. Mode 0600, owner duplicati:duplicati.
# Grammar (enforced by the wrapper, which refuses anything else):
#   KEY=VALUE | export KEY=VALUE | --option[=value] | # comment | blank
# KEY=VALUE values are literal (no shell expansion; matching surrounding quotes are removed), and
# only these names may be exported: SETTINGS_ENCRYPTION_KEY, DUPLICATI__*, TMPDIR, TZ, LANG, LC_ALL.
# --option lines are passed to the server verbatim, quotes included; leading whitespace is ignored.
# NEVER keep a real secret in a comment. A commented-out assignment is still a secret on disk,
# and on 2026-09-20 every line of this file was echoed into the system journal.
# The settings encryption key is delivered by systemd (LoadCredential=) and must not be set
# here while the unit supplies it. For a hand run outside systemd, export it in the shell.
--webservice-port=8300
```

Settings key policy (D-1, recommended): keep database encryption **on**, with a key that is (a) random and distinct from every passphrase, (b) stored at `/etc/credstore/duplicati-settings-key` root:root 0600 and delivered by `LoadCredential=`, (c) escrowed exactly where the passphrases are (printed sheet, password manager, machine-local copy outside the Dropbox root), and (d) made mandatory with `--require-db-encryption-key` in `DAEMON_OPTS`, so a missing credential stops
the server instead of silently starting it unencrypted. The record's 2026-08-30 objection — a third key to escrow — stands and is accepted as the price of not leaving the passphrase in cleartext in a database that is copied daily into `~/.local/state`. The alternative, `--disable-db-encryption` in `DAEMON_OPTS`, is one line and needs no escrow; it is the right choice if the owner prefers fewer keys over encryption at rest. Whichever is chosen, the choice is recorded in D-1
and in `/etc/default/duplicati`.

How Duplicati 2.4.0.0 handles the key (verified from `duplicati-server help` and `Duplicati/Server/Program.cs` `GetDatabaseConnection` by the step-2c agent):

- The key is read from the environment variable `SETTINGS_ENCRYPTION_KEY` or the option `--settings-encryption-key` (the option lands on a world-readable command line, so this design uses the environment, populated by the wrapper from the credential file).
- What is encrypted: every option of type *Password* across all modules — the job `passphrase` among them — plus backup `TargetURL`s, JWT/PBKDF configuration and certificate material; the `enc-v1:` prefix embeds a hash of the key, which is how a wrong key is detected (`SettingsEncryptionKeyMismatchException`) and a missing one reported (`SettingsEncryptionKeyMissingException`).
- With no key and an unencrypted database, 2.4.0.0 first tries the OS secret store (libsecret only — `pass` exists solely as an explicit `--secret-provider`) to mint a random key; if none is available it logs "No database encryption key was found. The database will be stored unencrypted." — the message seen on every root-server start before 09-18 21:03.
- **Changing or removing the key**: `ReWriteAllFieldsIfEncryptionChanged` runs at every start. Starting once with the **old** key and `--disable-db-encryption` decrypts every field; starting again with the **new** key (and without the disable flag) re-encrypts them. That two-start sequence is the re-key procedure in §8 P1.
- **Key lost**: `duplicati-database-tool wipe-encryption <Duplicati-server.sqlite>` clears the encrypted strings so the database opens without the key; the cleared values (`TargetURL`, `passphrase`, the UI password material) must be re-entered.
- A machine-derived default key existed only in canary 2.0.9.105 and was removed in 2.0.9.106; `machineid.txt` and `installation.txt` are identity files for the updater, not key material.

#### 7.3.6 Web UI

Loopback only (`--webservice-interface=loopback`); a UI password set once with `duplicati-server-util --hosturl http://127.0.0.1:8300/ change-password <new>` (or `--webservice-password-init=<new>` on a single start, which "sets the password only if not already set, and then exits") and stored in `~/.config/duplicati-backup/web-credential` (0600, pcalnon) for the watchdog; `--webservice-allowed-hostnames=localhost` if the record's `allowed-hostnames` setting does not already
cover it. Note that `duplicati-server-util` defaults to port 8200 — every invocation against this server needs `--hosturl`. Remote control and the cloud report URL stay as the owner left them (deferred item).

### 7.4 Destination and permission model

| Path | Owner:group | Mode | Why |
| --- | --- | --- | --- |
| `/mnt/Backups`, `/mnt/Backups/Ubuntu` | `pcalnon:duplicati` | `2770` | traverse for both; setgid keeps the group on new entries |
| `/mnt/Backups/Ubuntu/Dropbox` (Dropbox root) | `pcalnon:duplicati` | `2770` | Dropbox (pcalnon) owns it; the service traverses |
| `/mnt/Backups/Ubuntu/Dropbox/Backups` and every subdirectory | `pcalnon:duplicati` | `2770` + default ACL `g:duplicati:rwx` | new directories inherit; the service can create/rename/delete |
| volumes (`duplicati-*.zip.aes`) | creator`:duplicati` | `0660` | service umask `0007` produces `0660`; Dropbox reads via group |
| `_yamaguchi_keys/` | `pcalnon:duplicati` | `0700` and **moved out of the Dropbox root** (S-4) | escrow must not sync to the cloud |

```bash
# file: util/ad-hoc/2026-09-21_backup_destination_permissions.bash
#!/usr/bin/env bash
# Apply the §7.4 permission model to the T1 destination tree. Run with sudo. Idempotent.
#
# Project:    juniper-ml
# Sub-Project: ad-hoc tooling
# Author:     Paul Calnon
# Created:    2026-09-21
# Status:     ad-hoc — migration
# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related:    notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md §7.4
set -euo pipefail
ROOT=/mnt/Backups/Ubuntu/Dropbox/Backups
[[ "$(id -u)" -eq 0 ]] || { echo "run with sudo" >&2; exit 2; }
mountpoint -q /mnt/Backups || { echo "/mnt/Backups is not a mountpoint; refusing" >&2; exit 3; }
[[ -d "${ROOT}" ]] || { echo "${ROOT} missing; refusing" >&2; exit 3; }
chgrp duplicati /mnt/Backups /mnt/Backups/Ubuntu /mnt/Backups/Ubuntu/Dropbox
chmod 2770 /mnt/Backups /mnt/Backups/Ubuntu /mnt/Backups/Ubuntu/Dropbox
chgrp -R duplicati "${ROOT}"
find "${ROOT}" -type d -exec chmod 2770 {} +
find "${ROOT}" -type f -exec chmod 0660 {} +
setfacl -R -m g:duplicati:rwX -m d:g:duplicati:rwX "${ROOT}"
if [[ -d "${ROOT}/_yamaguchi_keys" ]]; then
    chmod 0700 "${ROOT}/_yamaguchi_keys"
    echo "NOTE: ${ROOT}/_yamaguchi_keys is inside the Dropbox root -- move it (design §6 S-4)" >&2
fi
echo "done; verify with: getfacl ${ROOT}/Yamaguchi | head; sudo -u duplicati test -w ${ROOT}/Yamaguchi && echo service-can-write"
```

Dropbox prerequisite: the daemon must run with gid 139. After `pcalnon` logs in again (or `newgrp duplicati` in the launching shell), `dropbox stop && dropbox start`, then `grep ^Groups /proc/$(pgrep -x dropbox | head -1)/status` must list `139`. Until then Dropbox can read only files whose `other` bits allow it — which the `0660` model deliberately does not grant.

### 7.5 The job, the Dropbox replica and the pre-backup guard

Job settings are the certified ones (R-16) with three changes: `--tempdir=/home/duplicati/.cache/duplicati-tmp`; `--run-script-before-required=/usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash`; `TargetURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi`. Everything else — sources, 45 filters, AES, `--blocksize=1MB`, `--dblock-size=500MB`, `--no-auto-compact=true`, `retention-policy=1W:1D,1M:1W,1Y:1M,3Y:2M`, `--asynchronous-upload-limit=1`,
`--allow-missing-source=true`, `compression-module=zip`, schedule 14:00 UTC daily — is taken from the 2026-09-20 snapshot.

Rules for a destination that is also a Dropbox-synced folder:

1. Duplicati assumes exclusive control of the destination: any file it did not write is a fatal pre-flight error (`remote files that are not recorded in local storage`, seen 09-16). Nothing else may create, rename or edit anything under `Yamaguchi/`; the folder must never be modified from another Dropbox client or the web UI.
2. The file backend writes each volume **in place under its final name** (streaming `FileCreate` on the target path; no temporary name and rename), and a failed upload attempt is retried under a **new** name, leaving the partial file behind (`RenameFileAfterError` in `Duplicati/Library/Main/Backend/BackendManager.PutOperation.cs`). Dropbox therefore uploads a volume while Duplicati is still writing it and re-uploads it when the write completes — bandwidth, not correctness —
   and a retry can leave a stray that the next run
   reports as a foreign file. Deletions (retention, compaction) propagate as deletions.
3. The guard below refuses to start a backup when the mount is absent, the directory is not writable, the job's `TargetURL` disagrees with the guarded path, or a foreign entry exists. It runs **before** Duplicati touches the destination.
4. Dropbox conflict copies, if they ever appear, must be removed by hand and the run repeated; never run `Repair` to "delete unknown files" without reading what they are (rule 11).
5. Restore from the cloud copy: download `Yamaguchi/` to a scratch directory on a disk with ~250 GB free and run `duplicati-cli restore file:///<scratch>/Yamaguchi <pattern> --passphrase=<PASSPHRASE> --restore-path=<dir> --dbpath=<new-temp-db>` (local blocks are off by default in 2.4.0.0; never add `--restore-with-local-blocks`); the passphrase comes from escrow, never from the same cloud account (S-4).

```bash
# file: usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash
#!/usr/bin/env bash
# Duplicati --run-script-before-required hook for the Yamaguchi job.
# Exit 0: proceed. Any other exit: Duplicati aborts the operation before touching the
# destination. 5 is used deliberately ("error, do not run" in the run-script contract), and an
# unexpected failure inside this script is converted to 5 too, so a bug here can only stop a
# backup, never wave one through.
#
# Project:      juniper-ml
# Sub-Project:  backup infrastructure
# Author:       Paul Calnon
# Version:      1.0.0 (design draft 2026-09-21)
# License:      MIT
set -euo pipefail
trap 'exit 5' ERR

DEST_MOUNT="${YAMAGUCHI_DEST_MOUNT:-/mnt/Backups}"
DEST_DIR="${YAMAGUCHI_DEST_DIR:-/mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi}"
# Duplicati exports the job's remote URL to run-scripts as DUPLICATI__REMOTEURL.
REMOTE_URL="${DUPLICATI__REMOTEURL:-}"
OPERATION="${DUPLICATI__OPERATIONNAME:-unknown}"

fail() { echo "GUARD(${OPERATION}): $*" >&2; exit 5; }

mountpoint -q "${DEST_MOUNT}" || fail "${DEST_MOUNT} is not a mountpoint"
[[ -d "${DEST_DIR}" ]] || fail "${DEST_DIR} does not exist"
[[ -w "${DEST_DIR}" && -x "${DEST_DIR}" ]] || fail "${DEST_DIR} is not writable by $(id -un)"
if [[ -n "${REMOTE_URL}" ]]; then
    case "${REMOTE_URL%/}" in
        "file://${DEST_DIR}") ;;
        *) fail "job TargetURL '${REMOTE_URL}' is not the guarded destination file://${DEST_DIR}" ;;
    esac
fi
stray="$(find "${DEST_DIR}" -mindepth 1 -maxdepth 1 \
    ! -name 'duplicati-*.dblock.zip.aes' \
    ! -name 'duplicati-*.dindex.zip.aes' \
    ! -name 'duplicati-*.dlist.zip.aes' \
    -print -quit)"
[[ -z "${stray}" ]] || fail "foreign entry in destination: ${stray}"
exit 0
```

Contract, verified against `Duplicati/Library/Modules/Builtin/RunScript.cs` (lines 385–448 at the 2.4.0.0 tag) and `duplicati-cli help run-script-before-required` — the vendor's own `/usr/lib/duplicati/run-script-example.sh` states the opposite mapping for both forms and is wrong against the source, so do not cite it: for `--run-script-before-required` any non-zero exit or a timeout aborts the operation; for plain `--run-script-before` exit codes 0, 2 and 4 let the operation
run and 1, 3 and 5 stop it (2/3 log a warning, 4/5 an error). The variables the example script documents include `DUPLICATI__OPERATIONNAME`, `DUPLICATI__REMOTEURL`,
`DUPLICATI__LOCALPATH`, `DUPLICATI__EVENTNAME`, `DUPLICATI__PARSED_RESULT` and `DUPLICATI__RESULTFILE`. `--run-script-timeout` defaults to 60 s; the guard above finishes in well under a second.

### 7.6 Alerting

- **Service level**: `OnFailure=duplicati-failure.service` is added to `duplicati.service` once a reporter exists for the system scope (the user-lane reporter `util/duplicati_backup_failure.bash` is the template; it writes a durable record first and notifies second).
- **Watchdog** (`util/ad-hoc/yamaguchi_watchdog.py`, user timer 12:00): read the UI credential from `~/.config/duplicati-backup/web-credential` (a file the operator rotates, instead of the primary checkout's `.env`); add the `ProgramState`/`SchedulerQueueIds` check from YAM §8.22 (`Paused` with a non-empty queue = fault); anchor freshness on the newest **Backup** operation, not any operation; add a Dropbox check (`dropbox filestatus` of the newest dlist must read `up to
  date` within 24 h); keep the 26 h staleness rule and the desktop notification as best-effort.
- **Deployment**: the watchdog unit keeps executing the primary checkout's script until the arc's own item (`HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §1.6) converts it to an installed copy; that conversion belongs to P2.

### 7.7 The server-DB snapshot lane

`util/ad-hoc/yamaguchi_server_db_snapshot.py` keeps `SRC = /usr/lib/duplicati/data/Duplicati-server.sqlite`. After recovery it must read `/home/duplicati/.config/Duplicati/Duplicati-server.sqlite`. The unit can then run as `duplicati` instead of root (group read is enough for `sqlite3.backup()`; the destination `~/.local/state/duplicati-server-db/` needs a group-writable directory or the unit keeps root only for the `chown`). Its docstring lines 20 and 36 ("the encrypted
passphrase") are corrected to state the actual condition: encrypted only when the settings key is in force (D-1).

### 7.8 Tier 2 — the USB archive lane, scheduled and mount-aware

Mechanism: a `systemd --user` timer defines the cadence; a `.path` unit fires the same service when either drive appears; the service runs a scheduler that decides whether a run is *due* and only then invokes `util/juniper-backup.bash`. `Linger=yes` is already in force for `pcalnon`. The drives are automounted by udisks under `/run/media/pcalnon/<UUID>` (since the 2026-09-07 udisks2 upgrade, §4.5 — `util/juniper-backup.bash` must be changed to the same root before any of
this works) and only while a graphical session exists; the more robust form is an fstab entry per drive keyed by UUID with `noauto,nofail,x-systemd.automount` under `/mnt/`, which mounts on first access without a session and works with the same units (D-10); the scheduler treats "no valid drive mounted" as a benign skip, and escalates to a
failure (so `OnFailure=` fires) only when no run has succeeded within `STALE_DAYS`.

```ini
# file: home/pcalnon/.config/systemd/user/juniper-backup.timer
[Unit]
Description=Weekly window for the Juniper per-repo USB archives (skips when no valid drive is mounted)

[Timer]
OnCalendar=Sun *-*-* 03:00:00
RandomizedDelaySec=15m
Persistent=true
Unit=juniper-backup.service

[Install]
WantedBy=timers.target
```

```ini
# file: home/pcalnon/.config/systemd/user/juniper-backup.path
[Unit]
Description=Run the Juniper USB archive when a configured drive is mounted and a run is due

[Path]
PathExists=/run/media/pcalnon/EBC5-F0A3/Juniper-8.0.0.python
PathExists=/run/media/pcalnon/DFF3-2782/Juniper-8.0.0.python
Unit=juniper-backup.service

[Install]
WantedBy=default.target
```

```ini
# file: home/pcalnon/.config/systemd/user/juniper-backup.service
[Unit]
Description=Juniper per-repo archive to attached USB drives
OnFailure=duplicati-backup-failure.service

[Service]
Type=oneshot
ExecStart=%h/.local/bin/juniper-backup-scheduled.bash
TimeoutStartSec=infinity
Nice=10
IOSchedulingClass=best-effort
IOSchedulingPriority=7
```

```bash
# file: util/juniper-backup-scheduled.bash
#!/usr/bin/env bash
# Decide whether a Juniper USB archive run is due and, if so, run util/juniper-backup.bash.
#
# Project:      juniper-ml
# Sub-Project:  backup infrastructure
# Author:       Paul Calnon
# Version:      1.0.0 (design draft 2026-09-21)
# License:      MIT
#
# Invoked by juniper-backup.timer (cadence) and juniper-backup.path (a drive appeared).
#   * no configured drive mounted            -> SKIPPED, exit 0 (escalates to FAILED after STALE_DAYS)
#   * drives mounted but none due            -> SKIPPED, exit 0
#   * a due drive is mounted                 -> run the archive script; exit with its code;
#                                               stamp every mounted drive on exit 0
# "Due" = no success stamp for that drive newer than PERIOD_DAYS. State lives in
# ~/.local/state/juniper-backup/. The archive script itself decides which mounted drives
# receive copies (all of them); this wrapper only decides whether to run at all.
set -euo pipefail

RUNNER="${JUNIPER_BACKUP_RUNNER:-${HOME}/.local/bin/juniper-backup.bash}"
STATE_DIR="${JUNIPER_BACKUP_STATE_DIR:-${HOME}/.local/state/juniper-backup}"
MEDIA_ROOT="${JUNIPER_BACKUP_MEDIA_ROOT:-/run/media/${USER}}"   # udisks2 >= 2.10.91 (design §4.5)
BACKUP_DIR="${JUNIPER_BACKUP_DIR:-Juniper-8.0.0.python}"
PERIOD_DAYS="${JUNIPER_BACKUP_PERIOD_DAYS:-7}"
STALE_DAYS="${JUNIPER_BACKUP_STALE_DAYS:-21}"
read -r -a DEVICES <<< "${JUNIPER_BACKUP_DEVICES:-EBC5-F0A3 DFF3-2782}"

mkdir -p "${STATE_DIR}"
STATUS_FILE="${STATE_DIR}/last-run.status"
LOCK_FILE="${STATE_DIR}/run.lock"
NOW="$(date +%s)"

log() { printf '%s %s\n' "$(date -Is)" "$*"; }
write_status() { printf 'result=%s\nwhen=%s\nreason=%s\n' "$1" "$(date -Is)" "$2" > "${STATUS_FILE}"; }

newest_success_age_days() {
    # Age in days of the newest success stamp across all devices; 100000 when none exists.
    local newest=0 f
    for f in "${STATE_DIR}"/last-success.*; do
        [[ -e "${f}" ]] || continue
        local m; m="$(stat -c '%Y' "${f}")"
        (( m > newest )) && newest="${m}"
    done
    if (( newest == 0 )); then echo 100000; else echo $(( (NOW - newest) / 86400 )); fi
}

skip_or_fail() {
    local reason="$1" age
    age="$(newest_success_age_days)"
    if (( age > STALE_DAYS )); then
        log "FAILED: ${reason}; no successful run in ${age} days (limit ${STALE_DAYS})"
        write_status FAILED "${reason}; stale ${age}d"
        exit 1
    fi
    log "SKIPPED: ${reason}"
    write_status SKIPPED "${reason}"
    exit 0
}

exec 9>"${LOCK_FILE}"
flock -n 9 || skip_or_fail "another run holds ${LOCK_FILE}"
[[ -x "${RUNNER}" ]] || { log "FATAL: runner missing: ${RUNNER}"; write_status FAILED "runner missing"; exit 1; }

mounted=()
unusable=()
due=()
for dev in "${DEVICES[@]}"; do
    root="${MEDIA_ROOT}/${dev}"
    mountpoint -q "${root}" || continue
    [[ -d "${root}/${BACKUP_DIR}" && -w "${root}/${BACKUP_DIR}" ]] || { log "WARN: ${root} mounted but ${BACKUP_DIR} missing or read-only"; unusable+=("${dev}"); continue; }
    mounted+=("${dev}")
    stamp="${STATE_DIR}/last-success.${dev}"
    if [[ ! -e "${stamp}" ]] || (( (NOW - $(stat -c '%Y' "${stamp}")) / 86400 >= PERIOD_DAYS )); then
        due+=("${dev}")
    fi
done

(( ${#mounted[@]} > 0 )) || skip_or_fail "no configured drive usable under ${MEDIA_ROOT} (wanted: ${DEVICES[*]}; mounted but unusable: ${unusable[*]:-none})"
(( ${#due[@]} > 0 )) || skip_or_fail "mounted (${mounted[*]}) but none due within ${PERIOD_DAYS} days"

log "running ${RUNNER}: mounted=${mounted[*]} due=${due[*]}"
set +e
"${RUNNER}" "$@"
rc=$?
set -e
if (( rc == 0 )); then
    for dev in "${mounted[@]}"; do touch "${STATE_DIR}/last-success.${dev}"; done
    write_status OK "devices ${mounted[*]}"
    log "OK (stamped ${mounted[*]})"
else
    write_status FAILED "runner rc=${rc}"
    log "FAILED rc=${rc} (no stamp written)"
fi
exit "${rc}"
```

Installation follows `util/install_duplicati_timer.bash`: copies of the runner and scheduler into `~/.local/bin/`, the three units into `~/.config/systemd/user/`, `systemctl --user daemon-reload`, then `systemctl --user enable --now juniper-backup.timer juniper-backup.path`. Retention on the drives (every run mints a new UUID set; nothing prunes; ~135 GiB / ~67 GiB free per `HANDOFF_2026-08-27_backup-per-repo-review-and-arc-tail.md` §7) is D-10.

### 7.9 Tier 3 — the offline external hard drive

The owner's sentence for this tier ends at "the additional backup should". Proposed default until D-5 rules:

- **Content**: the ten repos **plus** `juniper-legacy` (18 GB, no `.git`, in no tier today) **plus** the parent-level `notes prompts util backups` directories — all children of the Juniper parent, so `util/juniper-backup.bash --repos "…"` archives them without code changes — labelled `full`.
- **Cadence**: monthly, when the drive is attached; the same scheduler with `JUNIPER_BACKUP_DEVICES` set to the drive's mount name, `JUNIPER_BACKUP_PERIOD_DAYS=30` and a second timer/path pair (`juniper-backup-full.*`).
- **Mounting**: the drive gets an fstab line keyed by UUID with `noauto,nofail,x-systemd.automount,x-systemd.device-timeout=10s` under `/mnt/JuniperArchive`, so it is fstab-managed (rule 2) and appears the same way whether or not a desktop session exists. `util/juniper-backup.bash` needs one change for this: a `MEDIA_NAMES` entry beginning with `/` is taken as an absolute mount root (today every entry is forced under `/media/pcalnon/`, a path udisks stopped using on
  2026-09-07, §4.5 — so the change is required for Tier 2 as well, not only for the external drive).
- **Retention**: keep the last three `full` sets; delete older sets by UUID only after a restore drill of the newest passes.
- **Offline discipline**: the drive is connected for the run and disconnected afterwards; the scheduler's `.path` unit makes the run happen on connection.

### 7.10 Coverage gaps — disposition

| Gap | Disposition |
| --- | --- |
| `/var/lib/docker/volumes` (16 Juniper volumes) | not in scope of any tier; proposed: a `docker run --rm -v <vol>:/v -v /home/pcalnon/backup-staging/docker:/out alpine tar` export into the T1 source, weekly — owner decision D-11 |
| `/opt/miniforge3/envs` (47 GB) | regenerable from the recorded recipes; export `conda env export` files into the T1 source instead — D-11 |
| credentials outside `Juniper/` (`~/.ssh`, `~/.gnupg`, `~/.config/gh`, SOPS age key) | covered by T1 once `CAP_DAC_READ_SEARCH` restores root-era coverage (AC-3 proves it); the SOPS escrow script remains unconfirmed (inherited O-2) |
| `juniper-legacy`, parent-level dirs | T3 (§7.9) |
| GitHub-side state | out of scope; inherited |
| the per-job index `BMXWPAOGLP.sqlite` | still in no tier; a Recreate rebuilds it; acceptable |

### 7.11 Transitional artifacts to retire after acceptance

`/usr/lib/duplicati/data/` (archive a copy, then remove, once AC-1…AC-4 pass); `/home/duplicati/.config/Duplicati/{temp,temp1,backups}` (57 GB of copied pcalnon job databases — the originals in the pcalnon profile stay under the record's KEEP list); `Duplicati-OLE/` (unreadable to the investigators — owner to inspect); the disabled user CLI lane (the record's own removal item); the `.env` comment block; the wrapper's header comment.

---

## 8. Remediation plan

> **STOP — this runbook is not yet reconciled with consensus round 1 (2026-09-21) and must not be executed from this revision.** The validators' verbatim reports are in `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`. What they established about the steps below, in the order an operator would hit it:
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

Phases are ordered; nothing in a later phase is a precondition of an earlier one. Every destructive step is preceded by a copy. **Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved by any step below**, and the pcalnon profile directory is not modified.

### P0 — freeze and recover the job (target: same day)

1. **Freeze evidence.** `sudo cp -a /usr/lib/duplicati/data /home/duplicati/.cache/root-data-folder-2026-09-21` and `cp -p ~/.local/state/duplicati-server-db/Duplicati-server.sqlite ~/.local/state/duplicati-server-db/Duplicati-server.sqlite.2026-09-21-recovery`. Verify sizes match.
2. **Stop the empty server**: `sudo systemctl stop duplicati.service` (stop, not restart — the armed `ExecStart` cannot start the server correctly, §4.3 item 9). Move the fresh, empty data folder aside: `sudo mv /home/duplicati/.config/Duplicati /home/duplicati/.config/Duplicati.empty-2026-09-20`.
3. **Procedure A — identify the 09-18 key on a copy.** For each candidate (§5.4 order), as root:

```bash
# file: util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash
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
SETTINGS_ENCRYPTION_KEY="${key}" timeout 45 runuser -u duplicati -- /usr/bin/duplicati-server \
    "--server-datafolder=${WORK}" --webservice-interface=loopback "--webservice-port=${PORT}" \
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
9. **Re-arm alerting.** Set the UI password, write `~/.config/duplicati-backup/web-credential`, make the watchdog read it; confirm the next 12:00 fire reads `OK`.

### P1 — secrets (same week)

1. Generate a new settings key (`umask 077; openssl rand -base64 48 | tr -d '\n' > /etc/credstore/duplicati-settings-key`), then re-key the database in two starts: first with the **old** key still in the credential file and `--disable-db-encryption` appended to `DAEMON_OPTS` (every field is decrypted on that start), then with the new key in the credential file and the flag removed (every field is re-encrypted; add `--require-db-encryption-key` at this point). Escrow the new
   key with the passphrases (printed, password manager, machine-local copy outside the Dropbox root).
2. Delete the five commented lines from `.env`; set it to the §7.3.5 contract; `chmod 0600`.
3. Remove the commented "Old Unit file" block from `scripts/duplicati-wrapper.bash` (the wrapper is replaced by §7.3.3 in the same PR).
4. Move `_yamaguchi_keys/` out of the Dropbox root (S-4).
5. Rule on D-2 (passphrase exposure) and D-8 (journal scrub); execute the ruling.

### P2 — hardening and re-pointing (same week)

1. `chown -R root:root /usr/lib/duplicati` except `data/` (kept as the frozen copy until P4); `chmod 0755 /home/duplicati/bin` or remove it; `chmod 0700 /home/duplicati/.config/Duplicati` and `0600` its files (Duplicati's own requirement, §7.3.2); `/etc/default/duplicati` → root:root.
2. Run `util/ad-hoc/2026-09-21_backup_destination_permissions.bash`; restart Dropbox in a session carrying gid 139; verify `AC-7`.
3. Re-point `yamaguchi_server_db_snapshot.py` (§7.7) and redeploy the system timer; confirm the next 13:45 UTC snapshot reads the new path.
4. Watchdog changes (§7.6); redeploy with `util/ad-hoc/yamaguchi_watchdog_deploy.bash`.
5. `systemd-analyze security duplicati.service`; record the score in the validation record.
6. Reboot test (`util/ad-hoc/yamaguchi_reboot_verify.bash pre` / `post`; AC-9).

### P3 — tiers 2 and 3 (following week)

1. Land `util/juniper-backup-scheduled.bash` and the three user units; install; enable; observe one SKIPPED (unplugged) and one OK (plugged) run; class-1 drill (`util/ad-hoc/2026-08-26_backup_restore_drill.bash`).
2. Rule on D-5; add the absolute-mount-root form to `util/juniper-backup.bash`; fstab line for the external drive; first `full` set; restore drill of one archive from it.

### P4 — cleanup (after seven consecutive successful daily runs)

1. Archive `/usr/lib/duplicati/data/` to the T1 source (`tar` into `~/.local/state/duplicati-server-db/root-data-folder-2026-09.tar`) and remove it; `chown root:root /usr/lib/duplicati` fully.
2. Remove `/home/duplicati/.config/Duplicati/{temp,temp1,backups}` after confirming the pcalnon originals exist (`ls -la /home/pcalnon/.config/Duplicati/backups/`), and `Duplicati.empty-2026-09-20`.
3. `usermod -s /usr/sbin/nologin duplicati`.
4. Open the user-lane removal PR the record has owed since 2026-08-30.

---

## 9. Acceptance criteria

| ID | Criterion | Verification |
| --- | --- | --- |
| AC-1 | `duplicati.service` is the `/etc/systemd/system` unit, active as `duplicati`, `NeedDaemonReload=no`, `NRestarts=0` over 24 h | `systemctl show duplicati.service -p FragmentPath,User,NeedDaemonReload,NRestarts,ActiveState` |
| AC-2 | The job `Yamaguchi` exists with `TargetURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi`, 2 sources, 45 filters, schedule `1D` at 14:00 UTC, `--blocksize=1MB` | `python3 util/ad-hoc/yamaguchi_server_api.py status` and `export 2` |
| AC-3 | First post-recovery backup `ParsedResult=Success`, `SourceFilesCount` within 2 % of 1,024,167 and `SourceSizeString` within 5 % of 290.61 GiB (the 09-18 root-era values) — proves `CAP_DAC_READ_SEARCH` restored coverage; census `AGREE` | `python3 util/ad-hoc/yamaguchi_census.py --runs 1`; `Metadata` via the forensics script on a fresh snapshot |
| AC-4 | Restore drill from the new fileset with local blocks **off** (the 2.4.0.0 default; never pass `--restore-with-local-blocks`; `--no-local-blocks` is deprecated), SHA-256 and length match on ≥ 15 files, one negative control fails | `util/ad-hoc/yamaguchi_drill_watch.bash` lineage |
| AC-5 | Watchdog reads `OK` three consecutive days; a deliberate `--backup-id 999` fires `JOB_MISSING` | `~/.local/state/duplicati/server-watchdog.log` |
| AC-6 | Snapshot lane reads the new data folder; the snapshot file's mtime advances daily; it appears in the next fileset | snapshot journal; `duplicati-cli list` / UI search |
| AC-7 | Dropbox daemon carries gid 139; newest dlist `up to date` within 24 h of its write; `_yamaguchi_keys/` outside the Dropbox root | `/proc/<pid>/status`; `dropbox filestatus`; `ls` |
| AC-8 | No secret in the journal since the hardening timestamp: zero `LINE: "`, `Exporting Environment`, `Settings Encryption Key:` lines; `.env` has no commented assignment; wrapper has no credential-shaped literal | `journalctl -u duplicati.service --since <ts>`; `2026-09-21_env_file_shape.py`; `grep -c 'Environment=SETTINGS' scripts/duplicati-wrapper.bash` = 0 |
| AC-9 | Reboot: service back within 60 s of boot, job present, next scheduled run fires unattended | `yamaguchi_reboot_verify.bash post` |
| AC-10 | T2: timer fires weekly; a run with no drive reads `SKIPPED`; a run with a drive attached (mounted under the root `util/juniper-backup.bash` is configured for — `/run/media/pcalnon/` or the fstab paths, §4.5) produces verified archives on every mounted drive; class-1 drill passes | `~/.local/state/juniper-backup/last-run.status`; drill script |
| AC-11 | T3: first `full` set written; one archive restored and diffed against the live tree | manual |
| AC-12 | `systemd-analyze security duplicati.service` reports an exposure at or below the offline baseline of the §7.3.2 unit and no ✗ row beyond those the design accepts (`AmbientCapabilities=`, the `CAP_DAC_*` / `CAP_FOWNER` / `CAP_IPC_OWNER` bounding-set row, `ProtectHome=` read-only); the server completes AC-3 under every confinement directive the unit sets — a directive it cannot run under is removed **and recorded**, never silently | `systemd-analyze security`; journal of the first start |

---

## 10. Owner decisions

| ID | Decision | Recommendation |
| --- | --- | --- |
| D-1 | Settings-key policy: keep DB encryption with a distinct, escrowed key, or `--disable-db-encryption` | keep encryption; the record's objection (a third key) is accepted as the price |
| D-2 | `PASSPHRASE` exposure in the journal and `.env` comments: accept (local readers only) + scrub, or start a new set under a new passphrase | accept + scrub now; rotate at the next set rebuild |
| D-3 | Cloud replica mechanism: Dropbox desktop client on the T1 destination (as built) vs `duplicati-sync-tool` (shipped in 2.4.0.0, not studied here) or Duplicati's native Dropbox backend from a job that owns the copy | keep the desktop client for now with the §7.5 guard; evaluate `duplicati-sync-tool` separately — it would remove the sync client from the write path and the group-membership prerequisite |
| D-4 | Read access to `/home/pcalnon`: `CAP_DAC_READ_SEARCH` on the service vs recursive ACLs on the home | capability |
| D-5 | Tier 3 content, cadence, retention (the truncated requirement) | §7.9 default |
| D-6 | Live wrapper: root-owned installed copy (recommended) vs the symlink into the checkout | copy |
| D-7 | Keep or delete the 57 GB of copied job databases under the duplicati home | delete after P4 step 2's check |
| D-8 | Journal scrub (`--rotate` + `--vacuum-time=1s`, loses all history) vs leave | scrub once, after P1 |
| D-9 | Web UI reachable from LAN (`any` + allowed hostnames) or loopback only | loopback |
| D-10 | T2 cadence (weekly proposed) and USB retention | weekly; prune sets older than 8 weeks after a drill |
| D-11 | Docker volumes and conda envs: export into the T1 source, or accept the gap | export docker volumes weekly; conda recipes only |
| D-12 | Inherited items: `sda` SMART, `sdc4` read-only probe, cloud reporting, user-lane removal PR, `records_sync` de-drift | unchanged from the record |

---

## 11. Validation record (CON §7)

**State of the record: round 1 delivered in full; reconciliation paused by the owner on 2026-09-21 before Lanes A1, B1, B2 and B3 were folded in.** The verbatim reports are archived in `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`; the five step reports the design was drafted from are in `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-STEP-REPORTS-RECORD.md`.

- **Instruments and whether each could have produced a different answer**: §5.6 for the three root-cause legs (Lane A1 re-ran the database forensics twice, 13:40 and 13:49 CDT, byte-identical copies, and confirmed both adequacy arguments: the WAL replay that produced the 19-table local schema would have shown a server schema the same way, and a torn copy would have shown a broken frame chain or a `quick_check` error). Lane B2 notes that no adequacy statement exists for the §4.1 observations the plan acts
  on — an open item.
- **Sample sizes**: system journal 2026-09-17 → 2026-09-21 (complete, re-read by two lanes); five server-database copies (four re-inspected by Lane A1, two by Lane B1 with an offline key-hash test); 877 destination files (re-counted); `/var/log/syslog*` back to 09-12 (Lane B1, counts only); 13 handoffs and 7 documents of record (Lane A2); Duplicati source at tag `v2.4.0.0_stable_2026-09-03` (Lanes A3 and B1); systemd 259.5 man pages.
- **Agents per lane and entry points**: drafting — five step agents (1a documents of record; 1b handoffs + tooling; 2a live host; 2b repository + synthetic wrapper tests; 2c product sources). Validation — six agents, launched together, none seeing another's output: Lane A ×3 (A1 live host only; A2 repository and documents only; A3 product behaviour and code execution — the design's own tagged blocks run against synthetic inputs); Lane B ×3 (B1 refute the root cause and the recovery; B2 amputation and
  actionability; B3 security). All six were killed mid-run by a session usage limit and resumed in place with context intact.
- **Iterations and what the last one changed**: one round. Lane A2's 15 and Lane A3's 12 corrections were applied to this revision (among them: §4.5, the udisks `/run/media` breakage of Tier 2; the wrapper's export allow-list and `.env` 0600 contract; libsecret-only secret provider; the run-script and file-backend citations; two defects in the snippet linter — an order-dependent verdict and a vacuous "no linter" pass — fixed). Lane A1 (13 disagreements, mostly counts and dates, plus 8 unrecorded facts),
  Lane B1 (17 findings; 3 refutations that change P0 — see the warning at the top of §8), Lane B2 (10 amputations, 22 actionability defects) and Lane B3 (20 security findings) are **not applied** — except the §4.1 unit row (A1 item 1), this section's adequacy and cannot-support entries, the §8 warning, §7.3.2's env override (B1 F11), P1 step 2's `chmod 0600` (B2 D15) and the AC-12 row, §0 instrument list and §12 file list (B2 D22). Round 2 (CON §4, briefed on the corrections) has not run.
- **Unresolved dissent** (to be settled at reconciliation): the count of systemd specifier-rejection lines (A1: 23 `Invalid slot` = 22 `Failed to resolve specifiers` + 1 `… unit specifiers`; B1: 21 in the journal, 22 in syslog; the orchestrator's own count over 2026-09-18 → 09-21 13:00: 22 + 1 = 23 — the instruments differ in pattern and window, not in fact); B2 proposes `dropbox exclude add` for the escrow folder while B3 argues an exclusion leaves the cloud copy in place and calls for a permanent delete
  plus an account audit; B2 flags the alias-only section references (44 by an anchored `grep -o` on the design — 28 `YAM §`, 8 `PLAN §`, 3 `CON §`, 4 `DMG §`, 1 `GPG §`; an unanchored count also picks up the pattern names quoted in the counting sentence itself) against the name-every-document convention, which the header's **Companions** list (alias → filename, in the same document) is held to satisfy.
- **What the evidence cannot support**: which key encrypted the root database on 2026-09-18 21:03 — the offline test excludes every candidate the design named, so the key is unrecorded anywhere the design looked (root's shell history and editor backups of the unit are the last untested places); whether the abandoned folder's main file is itself still cleartext with the encryption only in its `-wal` (needs `sudo ls -la /usr/lib/duplicati/data/`); what the six foreign files of 2026-09-16 were (deleted before
  this investigation); whether `Duplicati-OLE/` holds anything relevant (unreadable without root); who or what ran the 2026-08-25 02:19 Repair that renamed the profile server database (no shell history names it); whether ambient `CAP_DAC_READ_SEARCH` reaches the .NET server process (untested without privilege).

---

## 12. Document history

| Date | Change |
| --- | --- |
| 2026-09-21 | First draft, from steps 1–2 and the orchestrator's forensics. |
| 2026-09-21 (later) | Consensus round 1: Lane A2 (15) and A3 (12) corrections applied (§4.5 added; wrapper allow-list; `.env` 0600; AC-10/AC-12 reworded; linter fixed). Lanes A1/B1/B2/B3 paused by the owner, reports archived verbatim in `…BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`; status → reconciliation-pending; §8 warning and §11 record written. |
| 2026-09-21 (later) | Lane B1's two instruments archived: `util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py`, `util/ad-hoc/2026-09-21_env_value_equality.py`. |
| 2026-09-21 (later) | Landed with the archive PR (number in the handoff's §4): this file, the two `…BACKUP-DESIGN-*-RECORD.md` files, `…BACKUP-HANDOFF-CONSENSUS-RECORD.md`, `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-21_backup-redesign-round-1-validated-reconciliation-pending.md`, six `util/ad-hoc/2026-09-21_*.py` instruments (§0 names the four drafting instruments; the row above names Lane B1's two). |
| 2026-09-21 (later) | Handoff-validation Lane B1 corrections applied here: §8 warning (steps 3/5/7/9; Procedure A0; `wipe-encryption` does take `--server-datafolder` on the subcommand), §7.3.2 env override, P1 step 2 (0600), status line, §11. |

---

## Appendix A — evidence excerpts

### A.1 Journal, `duplicati.service` (deduplicated; stack frames removed)

```text
2026-09-17T01:31:01 duplicati-server: No database encryption key was found. The database will be stored unencrypted. ...
2026-09-18T19:57:47 duplicati-server: Crash! System.UnauthorizedAccessException: Access to the path '/usr/lib/duplicati/data/installation.txt' is denied.
2026-09-18T20:22:13 duplicati-server: Server has started and is listening on localhost, port 8300
2026-09-18T20:26:54 duplicati-server: System.Exception: Failed to process the path: Access to the path '/mnt/Backups' is denied.
2026-09-18T21:03:30 duplicati-server: Server has started and is listening on localhost, port 8300      (no "no key" warning)
2026-09-18T21:08:06 duplicati-server: Duplicati.Library.Interface.SettingsEncryptionKeyMismatchException: Encryption key used to encrypt target settings does not match current key.
2026-09-18T21:15:40 systemd[1]: /usr/lib/systemd/system/duplicati.service:11: Failed to resolve specifiers in SETTINGS_ENCRYPTION_KEY=<36 chars>, ignoring: Invalid slot
2026-09-18T21:16:18 duplicati-server: The database appears to be encrypted, but no key was specified. ... SettingsEncryptionKeyMissingException: Encryption key is missing.
2026-09-19T20:48:12 duplicati-server: The database has version 19 but the largest supported version is 11. ... folder /home/duplicati/.config/Duplicati.
2026-09-20T13:32:50 duplicati-wrapper.bash: Server has started and is listening on localhost, port 8200
2026-09-20T16:41:15 duplicati-wrapper.bash: LINE: "#   PASSPHRASE_OLD -> the OLD archive at /mnt/Backups/Ubuntu. ..."   (one of 220 echoed lines)
2026-09-20T16:44:29 duplicati-server: SettingsEncryptionKeyMismatchException: Encryption key used to encrypt target settings does not match current key.
2026-09-20T18:02:55 duplicati-server: The database has version 19 but the largest supported version is 12.
2026-09-20T18:19:46 duplicati-wrapper.bash: Server has started and is listening on localhost, port 8300
```

### A.2 Forensics summary (`2026-09-21_duplicati_server_db_forensics.py`, copies)

| Database | Schema tables | `Version` | `Backup` rows | Notable |
| --- | --- | --- | --- | --- |
| pcalnon profile `Duplicati-server.sqlite` + 112 MB WAL | 19 local-DB tables (`Block`, `Remotevolume`, `Fileset`, …) | 19 | n/a | `Operation = (1, 'Recreate', 2026-08-25 02:19:48)`, `Configuration = repair-in-progress`, no volumes, no filesets |
| pcalnon profile `Duplicati-server.backup` (2026-08-25 02:19:47) | 16 server tables | 11 | 2: `Ubuntu` (id 2), `Ubuntu-fresh` (id 3) | `Schedule` 0 rows; notification `Error while running Ubuntu: A task was canceled.` 02:19:46 |
| root snapshot 2026-09-20 08:45 | 16 server tables | 11 | 1: `Yamaguchi` (id 2), `DBPath=/usr/lib/duplicati/data/BMXWPAOGLP.sqlite` | `LastBackupDate=20260918T140000Z`, 9 filesets, 877 files, 45 filters, `enc-v1:` TargetURL |
| live duplicati DB (created 2026-09-20 18:19:43) | 16 server tables | 12 | 0 | 4 × `Failed to import backup` (JSON `S` ×2, AES wrong password ×2) |

### A.3 Inode timestamps that fix the 2026-09-20 order

| File | Birth | Modified | Changed |
| --- | --- | --- | --- |
| `/home/duplicati/.config/Duplicati/temp/` (root:root) | 18:18:49 | 18:19:26 | 18:19:26 |
| `temp/Duplicati-server.sqlite-wal` (112 MB) | 17:57:56 | 2026-08-25 02:20:46 | 18:19:26 |
| `Duplicati-server.sqlite-wal` (370 KB, live) | 18:19:43.917 | 18:42:47 | 18:42:47 |
| `control_dir_v2/lock_v2` | 18:19:45 | 18:19:45 | 18:19:45 |
| `.env` | 16:39:43 | 16:39:43 | 16:39:43 |
| `bin/duplicati-wrapper.bash` (symlink) | 16:53 | — | — |
| `/usr/lib/duplicati/data/` | 2026-08-25 02:38:43 | 2026-09-18 21:03:34 | 2026-09-19 19:15:00 |

## Appendix B — index of code artifacts in this document

| Tagged block | Purpose | Linted by |
| --- | --- | --- |
| `etc/default/duplicati` | systemd `EnvironmentFile` | `KEY=VALUE` / `--option` grammar (keyed on the path, since the file has no extension) |
| `etc/systemd/system/duplicati.service` | the service unit | `systemd-analyze verify` |
| `usr/local/lib/duplicati/duplicati-wrapper.bash` | wrapper v2 | `bash -n`, shellcheck |
| `util/install_duplicati_service.bash` | installer | `bash -n`, shellcheck |
| `home/duplicati/.config/Duplicati/.env` | `.env` contract | `KEY=VALUE` / `--option` grammar (keyed on the basename `.env`) |
| `util/ad-hoc/2026-09-21_backup_destination_permissions.bash` | permission model | `bash -n`, shellcheck |
| `usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash` | pre-backup guard | `bash -n`, shellcheck |
| `home/pcalnon/.config/systemd/user/juniper-backup.{timer,path,service}` | T2 units | `systemd-analyze verify` |
| `util/juniper-backup-scheduled.bash` | T2 scheduler | `bash -n`, shellcheck |
| `util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash` | Procedure A probe | `bash -n`, shellcheck |

Run: `python3 util/ad-hoc/2026-09-21_lint_design_snippets.py --doc notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md --workdir <scratch>`.

## Appendix C — corrections to the record

1. YAM §8.20.4 / `HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §1.8: "the schema-19 profile server DB … orphaned from any running server" → the file is an aborted local-database Recreate (schema 19 is the **local** schema) written over the profile server DB at 2026-08-25 02:19:48; the last real profile server DB is `Duplicati-server.backup` (02:19:47, schema 11, jobs `Ubuntu` and `Ubuntu-fresh`).
2. YAM §2 (line 39): "the TrayIcon crash of 02:30 was that same era's binary refusing the profile server DB after a 2.3.0.4 run upgraded it (schema 11→19; pre-upgrade copy preserved as `Duplicati-server.backup`)", repeated as "schema 19" at YAM §7 (line 194) and §8.20.4 (line 1974): no server schema 19 exists in 2.3.0.4 (max 11) or 2.4.0.0 (max 12); the crash the TrayIcon reported was caused by the local-DB content above.
3. YAM §8.19.3: "the passphrase is stored in cleartext" was true of the root database **until 2026-09-18 21:03:34**; since then its sensitive fields are `enc-v1:` under the key discussed in §5.4. Copies taken by the snapshot lane before 09-18 are cleartext; the 09-20 copy is not.
4. `util/ad-hoc/yamaguchi_server_db_snapshot.py:20,36` and `util/systemd/yamaguchi-server-db-snapshot.service:5` still say "encrypted passphrase" unconditionally — now conditionally true; rewrite per §7.7.
5. The record's destination `/mnt/Backups/Ubuntu/Yamaguchi` and README `/mnt/Backups/Ubuntu/README.md` moved under `/mnt/Backups/Ubuntu/Dropbox/Backups/` between 2026-09-08 and 2026-09-15 without a note; the README's own "second copy" section and `--dest /mnt/Backups/Ubuntu` example are now stale.
6. The 2026-09-07 handoff's "criterion 5 NEVER exercised" was superseded by YAM §8.27 (closed 2026-09-08); the as-built reconstruction from handoffs alone could not see that closure — an instance of the record living in more than one place.
7. YAM §8.19.4's "portable-mode trap" is correct as far as it goes; the mechanism is the explicit flag, not any inference from a `data/` directory (`DataFolderManager.GetDataFolder`), and 2.4.0.0 adds the 0700 data-folder gate that the record predates.
8. The pcalnon crash log names `Duplicati.GUI.TrayIcon.Net10`; no assembly of that name ships in 2.4.0.0, so the binary that wrote it (the 2.3.0.4 package, by timing) is not verifiable from the installed tree. The message it carries matches the 2.3.0.4 journal lines exactly.
