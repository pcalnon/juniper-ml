# Backup infrastructure — integrated design, root-cause analysis and remediation plan

**Project**: Juniper (workstation backup infrastructure, host `yamaguchi`)
**Author**: Paul Calnon
**Date**: 2026-09-21
**Status**: VALIDATED (round 2) — consensus round 1 (six validators) and round 2 (four lanes) have
both reported, and every finding is applied or recorded as dissent in §11. Verbatim reports:
`JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md` and
`JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md`.
**§8 is executable in this order and no other**: **P0.5a** items 1–2, then **P0 step −1** (review and
merge the nine scripts §8 invokes that are now staged; the tenth is a P3 deliverable), then **P0 step 0**'s
owner gates, then **P0**, then **P0.5b** (the re-key, which needs the recovered data folder). Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved except the one escrow copy named
in P1 step 4.
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
`ExecStart=` names a later block resolves), `util/ad-hoc/2026-09-21_wrap_long_markdown_lines.py` (wraps over-long prose lines at word boundaries for MD013 without touching tables or fences). Validation round 1 added two more, both of which changed a conclusion: `util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py` (tests a candidate settings key against a database **copy** offline, from the SHA-256 of the key embedded in every `enc-v1:` value — it excluded both candidates §5.4 had ranked) and
`util/ad-hoc/2026-09-21_env_value_equality.py` (prints booleans only: which secret values are byte-identical to which). Reconciliation itself is `util/ad-hoc/2026-09-22_reconcile_backup_design.py`, which rebuilds this file from its pristine blob on every run so the edit set is re-derivable rather than remembered.

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

**One more restart makes it worse.** A global systemd reload (03:23:44 on 09-21 by the orchestrator's own journal reading; no validation lane measured that timestamp) armed the operator's latest unit edit, whose `ExecStart` hands the wrapper a single `--daemon-opts="…"` word that neither wrapper revision can parse. The server **does not start at all** on the next restart or reboot — not "on 8200 or not at all": the 0700 data-folder gate refuses the 0777 folder before argv is
even reached (§5.5, §4.3 item 9), so the argv bug is moot and the outcome is not port-dependent. Recovery (§8 P0) installs the corrected unit and wrapper, and sets the folder to 0700, before the first restart.

**Tier 2 has been silently broken since 2026-09-07 as well.** The USB archive script looks for its drives under
`/media/pcalnon/`; the udisks2 upgrade of that day moved automounts to `/run/media/pcalnon/`, so every run since skips
both drives and fails with "no usable device" (§4.5). Nothing reported it because the lane has no timer or alerting.

**The job definition is recoverable.** A consistent copy of the root server database, taken by the still-running root snapshot timer (last at 2026-09-21 08:45 CDT, still 240 KiB, `integrity ok`), sits at `~/.local/state/duplicati-server-db/Duplicati-server.sqlite` (240 KiB, schema 11). It holds the `Yamaguchi` job: 2 sources, 45 filters, 10 job options, the daily 14:00 UTC schedule and the per-job index path. The per-job index itself (`/usr/lib/duplicati/data/BMXWPAOGLP.sqlite`) is intact under the
duplicati-owned data folder. §8 gives **four** recovery procedures, in cost order: **A0** restores a *cleartext* copy of the same database out of the 09-17 or 09-18 fileset (the snapshot lane writes inside the backup source, and the root database was unencrypted until 09-18 20:42), needing the escrowed passphrase and nothing else; **A** re-uses the whole data folder if the 09-18 key can be identified — which the offline key-hash test now says it cannot, from any
candidate this design named; **A2** wipes the encrypted fields and re-enters the two that matter; **B** rebuilds the job through the API from the snapshot. None needs a Recreate, and **all four** must move `BMXWPAOGLP.sqlite` into the new data folder and re-point `Backup.DBPath` before the first run — `DBPath` is stored absolute and is never relocated by the server, so a procedure that skips this fails its first backup read-only and loses the index to P4.

**Eight secret exposures must be handled with the recovery** (§6): the settings key delivered from `.env` is **byte-identical to the live Yamaguchi backup passphrase**; the wrapper's debug mode wrote every `.env` line — including commented-out lines carrying both backup passphrases — into the system journal **12 times** on 2026-09-20 (264 echoed lines, 60 of them commented-out assignments); an earlier settings key is committed in a comment of
`scripts/duplicati-wrapper.bash` and printed into the journal by systemd's own specifier error (23 `Invalid slot` lines = 22 `Failed to resolve specifiers` on the `Environment=` value plus one `Failed to resolve unit specifiers` on an `ExecStart` revision); a world-readable cleartext copy of **both** passphrases sits inside the backup source itself, in a worktree `.env` (S-7); and the escrow copy of both passphrases is synced to Dropbox. **rsyslog holds a complete
second copy of every journal exposure** (`/var/log/syslog*`, `syslog:adm` 0640, `pcalnon` is in `adm`), which a journal-only scrub does not touch — and so do this arc's own Claude Code transcripts, which are cloud-linked. "Local readers only" therefore means *every process running as* `pcalnon`, on a host where `pcalnon` is already root-equivalent (`sudo`, `docker`, `libvirt`, `kvm`).

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
| R-6 | `duplicati` is a system user; shell only during development | O | Kept; `nologin` **immediately**, in §8 P0.5a item 7 — moved out of P4 because a duplicati-uid shell outside the unit escapes §7.3.2's mount mask through `/proc/<pid>/root` |
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

`/var/lib/docker/volumes` (16 Juniper volumes) and `/opt/miniforge3/envs` (**62 GB**, measured
2026-09-21; the record's 47 GB is stale) are in **no** tier; the tar lane covers ten repos but not `juniper-legacy` (18 GB, no `.git`) or the parent-level `notes/ prompts/ util/ backups/` (per `APPLICATION_REPOS` at `util/juniper-backup.bash:102`; the 08-21 handoff's §3 table marked both as tar-covered at the time); GitHub-side state has no local copy; the `sops-backup-key.sh` escrow was never confirmed run; offsite was never ruled on
(`HANDOFF_2026-08-21_backup-systematization-design-arc.md` §2.1, §3, O-2, O-5). Owner items still open from YAM §8.25–§8.27:
`sda` SMART **read 2026-09-23 and PASSED** (note 10.2a) — closed, the read-only loop probe of the destroyed `sdc4`, the sdc2 grow, cloud reporting (deferred), the user-lane removal PR, the watchdog `ProgramState` check, the dead `yamaguchi_records_sync.bash`.

### 3.5 Contradictions in the record that this design settles

- YAM §8.20.4 and the 2026-09-07 handoff call the pcalnon file "the schema-19 profile server DB". It is not a server database (§5.3). Corrected in Appendix C.
- YAM §8.20.2 (2026-08-30) records the owner's decision to **reject** `SETTINGS_ENCRYPTION_KEY` ("adds a third key needing escrow"). The 2026-09-18 unit edits and the 2026-09-20 `.env` reverse that decision without a record. This design asks for the decision again, explicitly (D-1).
- The certification's destination `/mnt/Backups/Ubuntu/Yamaguchi` and the README the record says lives at `/mnt/Backups/Ubuntu/README.md` no longer exist at those paths; the live destination and README are under `/mnt/Backups/Ubuntu/Dropbox/Backups/` (§4.4). The move is unrecorded in `notes/`.

---

## 4. Current state — 2026-09-21

### 4.1 Component inventory

| Component | Where | Runs as | State on 2026-09-21 | Evidence |
| --- | --- | --- | --- | --- |
| `duplicati.service` (system) | vendor unit, edited in place 09-21 01:44:57; no drop-in. **`NeedDaemonReload=no`** — already reloaded, so the LOADED `ExecStart` is `'--daemon-opts="${DAEMON_OPTS}"'`; only the RUNNING process predates it (note a) | `duplicati:duplicati` | active since 09-20 18:19:42; PID 1397393; argv is one element `"--webservice-port=8300 "`; **the next restart runs the armed form** and fails the 0700 gate before argv matters (§4.3 item 9, §5.5) | `systemctl show`, `ps` |
| Data folder in use | `/home/duplicati/.config/Duplicati/` (directory mode **0777**). "Files 0777" is true of the four copied DB files and the crashlog **only**: `.env` is 0660, `installation.txt`/`machineid.txt` 0664, subdirectories 0775 (`backups/`, `control_dir_v2/`, **`temp1/`**), `temp/` root-owned 0755 | duplicati | server DB created 18:19:43, schema **12**, **0 backups**, 4 `Failed to import backup` errors (18:39:38/45, 18:42:39/47) | forensics on a copy; `control_dir_v2/lock_v2` mtime 18:19:45 |
| Abandoned data folder | `/usr/lib/duplicati/data/` (0700, **now owned by `duplicati`**). **97 of 118 directories** were chowned; **21 are still `root:root`**, so the sweep was shallow. **No file was chowned at all**: all 1,443 regular files outside `data/` remain `root:root` (note b) | — | holds the real server DB (fields encrypted under an unidentified key, **between 09-18 21:03:27 and 21:08:06**) and the per-job index `BMXWPAOGLP.sqlite` | `stat`; journal; snapshot journal |
| Server-DB snapshot (system timer, root) | `yamaguchi-server-db-snapshot.timer` 13:45 UTC; `ExecStart` runs the **primary checkout's** script as root (note c) | root | still firing daily; last **2026-09-21 08:45:00**, `integrity ok (16 tables)`, 240 KiB → `~/.local/state/duplicati-server-db/` — **a recovery source, replaced every day at 13:45 UTC with a new inode**: copy it aside before P0 | `journalctl -u yamaguchi-server-db-snapshot` |
| Watchdog (user timer) | `yamaguchi-watchdog.timer` 12:00 local, `Linger=yes` | pcalnon | firing; `UNREACHABLE` 09-19/09-20 (connection refused), `401` 09-21 02:52 (new server, unknown UI credential) | `journalctl --user`, `~/.local/state/duplicati/server-watchdog.log` |
| Disabled CLI lane | `~/.config/systemd/user/duplicati-backup.*` | pcalnon | disabled; deployed runner lacks the 08-29 DB-holder fix; a copy was also run **as `duplicati`** on 09-20 19:07 and refused (`PASSPHRASE is unset`) | `~/.local/state/duplicati/last-run.status`, `/home/duplicati/.local/state/duplicati/` |
| Destination | `/mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi/` on `sda1` (`/dev/sda1` 3.6 T, 400 G used) | — | 877 files / 203 G, all `pcalnon:duplicati 0770`, no ACL entries, no setgid; 9 dlists, newest `20260918T140000Z`; no stray names | `ls`, `find`, `getfacl` |
| Dropbox | root `/mnt/Backups/Ubuntu/Dropbox` (Pro), daemon PID 2948130 | pcalnon, **without gid 139** | "Up to date"; 9 folders excluded, `Backups/` synced; the root also holds personal files, which sync too | `dropbox status`, `exclude list`, `/proc/<pid>/status` |
| Wrapper | `/home/duplicati/bin/duplicati-wrapper.bash` → symlink to the **primary checkout's** `scripts/duplicati-wrapper.bash`; `bin/` is **0777** | — | the target changed three times between 02:15 and 03:14 today (an uncommitted `--daemon-opts` revision → `#1968` → `main` `d721fc78`, i.e. `#1969`, merged 08:07 UTC); parses `.env` with `eval`; debug mode echoes secrets (§4.3) | `diff`, step-2b report |
| `/etc/default/duplicati` | `DAEMON_OPTS="--webservice-port=8300"`; owned **`duplicati:duplicati`** 0644 | — | the service user can rewrite its own next argv; → `root:root` in P0.5 | `ls -la` |
| `.env` | `/home/duplicati/.config/Duplicati/.env` 0660 duplicati:duplicati, 1,599 B | — | one active line (`SETTINGS_ENCRYPTION_KEY`, 32-char value, single-quoted, contains `$ @ & #`), five commented-out lines carrying `PASSPHRASE_OLD`, `PASSPHRASE` and three spellings of the key; **the active key equals `PASSPHRASE`** | `2026-09-21_env_file_shape.py` |
| Package | `duplicati 2.4.0.0` (upgraded from 2.3.0.4 at 2026-09-19 21:29, reinstalled 21:35) | — | server schema 12 (2.4.0.0) vs 11 (2.3.0.4) | `/var/log/dpkg.log`, forensics |
| Tar lane | `util/juniper-backup.bash` (manual; expects drives `EBC5-F0A3`, `DFF3-2782` under `/media/pcalnon/`) | pcalnon | no timer, path unit, cron or udev rule anywhere; **device detection broken since 2026-09-07** — udisks now mounts under `/run/media/pcalnon/` (§4.5); neither drive is attached now | agent 1b, `ls /media/pcalnon /run/media/pcalnon`, dpkg log |
| pcalnon profile | `/home/pcalnon/.config/Duplicati/` (0700) | — | orphaned since 08-25; `Duplicati-server.sqlite` = 4 KB stub + 112 MB WAL of an aborted local-DB Recreate; `Duplicati-server.backup` = last real profile DB (jobs `Ubuntu`, `Ubuntu-fresh`, `Schedule` empty) and **itself `enc-v1:`** (11 blobs, one key — note d); 56 GiB of job-DB copies under `backups/`; `installation.txt` rewritten 09-20 18:10:32 | forensics |
| Second Dropbox client | `/mnt/Backups/Ubuntu/.dropbox-dist` (270.4.3312), owned `duplicati:duplicati` | — | a second, unused Dropbox distribution installed by or for the service user: directory born 09-15 15:26:22, content mtime 09-14 20:49:31, ownership last changed 09-18 20:30:49. The running daemons are pcalnon's. Retire in §7.11 | `stat`, `ls` |
| `duplicati` home | `/home/duplicati` (0755), created 2026-09-18 19:31:40 | — | `bin/` is 0777 and holds the live wrapper symlink; `.config/Duplicati` 0777 — until P0.5, any local user can rename-replace either | `stat` |

Notes on the rows above:

- **(a)** The 03:23:44 reload was **not an operator action**: every `daemon-reload` after the 01:44:57 unit edit was requested by `snapd.service` (03:23:44, 10:53:47, 14:43:48, 20:43:55 on 09-21; the last operator-scoped reload was 09-20 16:41:03). The armed `ExecStart` therefore became the loaded one *by accident*, through a routine package reload — which strengthens the point rather than weakening it: nobody chose this, and nobody will choose the
  restart either. The unit file was open in a live `vim` (pid 2318515) and two `su - duplicati` shells (3065639, 3117158) were running when Lane A1 looked, and **all three were still alive 2 days 8 hours later** at round 2 — both shells' in-memory history is still unwritten and still recoverable (§6). The live server's **last** journal lines are 09-20 18:47:44 and 18:51:33, **×2 each — four lines in total**, since each event logs an outer
  `System.Exception: Failed to process the path: …` and its inner `System.UnauthorizedAccessException: Access to the path '/media/pcalnon/temp_backups' is denied`. After the import failures it was pointed at the retired USB path, and nothing has been emitted since.
- **(b)** `/usr/lib/duplicati` itself is `duplicati:duplicati 0755` with no sticky bit, so the service user can `mv` any entry aside and drop in its own `duplicati-cli`, `duplicati-database-tool` or `duplicati-server` — all of which root and `pcalnon` execute during P0. `/usr/bin/duplicati-*` are symlinks into it, and `webroot/` is writable the same way. This is why the chown moves to **P0.5**, ahead of the recovery, not to P2.
- **(c)** `sys.path[0]` is therefore a pcalnon-writable directory, and the unit runs as **root** at 13:45 UTC every day: a standing pcalnon→root code path that every branch switch in the primary checkout re-arms. Fixed in P0.5 (§7.7).
- **(d)** That the pcalnon `.backup` is itself `enc-v1:` — under a libsecret-minted key nobody typed (§5.4) — means every "the database stores the passphrase in cleartext" statement in the record is true of the **root** database only, and only before 09-18 21:03 (Appendix C item 9).

Every row above is a **Lane A subject**: each was re-measured on the live host by Lane A1 on
2026-09-21 (03:47–03:55 and 13:40–13:55 CDT) with the command named in its Evidence column, and §11
carries the instrument-adequacy statement for the class. Two readings that look like ACL or
ownership facts are neither: `ls` prints `+` on every `Backups/` entry because of Dropbox's
`user.com.dropbox.attrs` xattr, **not** an ACL (`getfacl` shows base entries only), and the
`/usr/lib/duplicati` chown covers directories only (row 3).

### 4.2 Timeline, 2026-09-12 → 2026-09-21 (all times CDT unless marked Z)

| When | Event | Source |
| --- | --- | --- |
| 09-12 → 09-15 | Destination relocated under the new Dropbox root. Scheduled runs 09-13 14:00Z and 09-14 14:00Z fail: `Found 861 files that are missing from the remote storage, please run repair` (the job still pointed at the old path). Ad-hoc run 09-15 08:56Z succeeds after re-pointing. | root-DB snapshot `ErrorLog`; watchdog log; dlist names |
| 09-15 15:27–15:38 | `.dropbox.cache` and `.dropbox` created under `/mnt/Backups/Ubuntu/Dropbox`; at 20:46Z the job fails again with `865 files missing`; two `TaskCanceled` aborts; ad-hoc run 20:48Z succeeds | same |
| 09-16 14:01Z | Scheduled run fails: `Found 6 remote files that are not recorded in local storage … two backups sharing a destination folder … or restoring an old database`. Ad-hoc run 18:33Z succeeds. No stray file remains today. | same |
| 09-17 01:31 | Root server start: `No database encryption key was found. The database will be stored unencrypted.` Runs 09-17 22:13Z and **09-18 14:00Z succeed** (the last success). | journal |
| 09-18 19:57 | Unit switched to `User=duplicati`. Crash loop: `Access to the path '/usr/lib/duplicati/data/installation.txt' is denied` (portable data folder root-owned). Repeats 20:02. | journal |
| 09-18 20:22 | Starts OK (data folder made accessible), still unencrypted. 20:26 `Failed to process the path: Access to the path '/mnt/Backups' is denied` (destination not yet group-readable). | journal |
| 09-18 21:03:27 | Start **with** a settings key, no warning → fields of the root DB encrypted, **between 21:03:27 and 21:08:06**. The `/usr/lib/duplicati/data` mtime of 21:03:34 is *not* the encryption but the `-wal`/`-shm` creation (note 1) | journal, `stat` |
| 09-18 21:08 → 21:11 | Three crash loops: `SettingsEncryptionKeyMismatchException: Encryption key used to encrypt target settings does not match current key` | journal |
| 09-18 21:15 → 21:29 | `Environment=SETTINGS_ENCRYPTION_KEY=…%6%x…` rejected by systemd (`Failed to resolve specifiers … Invalid slot`) → `SettingsEncryptionKeyMissingException` (first 21:16:18); the revision with the key inside `ExecStart` was fatal to load (21:23:25). **Only 5 `Invalid slot` lines fall on 09-18**, not 23 — the other 18 are on 09-19 (note 2) | journal |
| 09-19 19:14 | Same `Missing` loop; `/usr/lib/duplicati/data` chowned to `duplicati` (ctime 19:15:00) | journal, `stat` |
| 09-19 19:19–20:44 | First wrapper revision: 20 starts die with `wrapper.bash: line 30: --webservice-port=8300: command not found` | journal |
| 09-19 20:48, 21:41–21:55 | Wrapper echoes `--webservice-port=8300 --portable-mode`; the options arrived as one argv word, so `--portable-mode` was inert and the home folder (holding a pcalnon-owned copy) was used. **24** failed starts, not 25, in three kinds: 5 `… version is 11`, 5 `… is denied`, 14 `… is 12` (note 3) | journal |
| 09-19 21:20, 21:57 | Two starts succeed **on port 8200** — the port option was equally inert | journal |
| 09-19 21:20 | pcalnon TrayIcon crashes on its own profile with the same "version 19" message | `Duplicati.GUI.TrayIcon-crashlog.txt` |
| 09-19 21:29, 21:35 | Package upgrade 2.3.0.4 → 2.4.0.0 (twice) | `dpkg.log` |
| 09-19 18:40 → 09-20 04:43 | pcalnon profile files copied into `/home/duplicati/.config/Duplicati/` in **three waves**, not one: 09-19 18:40:36–18:42:22, 09-19 21:57:36 (the 4 KB stub), 09-20 04:15:42–04:43:02 (note 4) | inode birth times |
| 09-20 13:32–13:37, 16:50, 17:30 | Four successful starts of the wrapper-launched server; the first (13:32:46) still echoes `--portable-mode` and listens on **8200**; from 13:36:37 it listens on 8300. Sixteen seconds *before* the 13:32:50 success, five starts of the **older** `wrapper.bash` died `KeyMissing` across 13:32:34–13:32:38 — two wrapper files were in play (note 5) | journal |
| 09-20 16:39–16:53 | `.env` created (16:39:43); `/etc/default/duplicati` rewritten (16:39:58); wrapper symlink created (16:53:58); 16:41:16 `encrypted, but no key`, 16:44:29 `Mismatch`; the wrapper in debug mode echoes every `.env` line to the journal — **220/50/10/10 in this window, 264/60/12/12 over the day** (note 6) | journal, `stat`, counts |
| 09-20 17:57:56 | The 112 MB WAL copied next to the 4 KB stub; 18:02 and 18:12: `version 19 but the largest supported version is 12` | inode birth, journal |
| 09-20 18:19:26 | WAL moved into root-owned `temp/`; 18:19:42 start; 18:19:43 fresh WAL; 18:19:46 `Server has started` (a key **was** supplied — no "no key" warning); 18:39 and 18:42 four `Failed to import backup` | inode times, journal, forensics |
| 09-20 22:26Z, 22:59Z | PRs juniper-ml#1967 and #1968 merge the wrapper (#1968's body is the unfilled PR template; #1967's is one generated sentence plus the template) | `gh pr view` |
| 09-20 18:47:44, 18:51:33 | The live server's last journal lines — two events, each logged **twice** (outer + inner exception), **four lines in all**: `Access to the path '/media/pcalnon/temp_backups' is denied` | journal |
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
6. Window 16:40–16:46 exactly: 220 `LINE:` echoes, 50 commented-out assignments, 10 `Exporting Environment Variable`, 10 `Settings Encryption Key:`. Day total — the figure §1 and §6 use — is 264 / 60 / 12 / 12 across **12** passes: 16:41 and 16:44 (110 echoes each, the two crash loops) plus the successful starts at 16:50 and 17:30 (22 each), which also echoed the file and printed the key once each.

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
8. The live symlink points into a developer checkout — today on `main` at `d721fc78`, clean for that file and byte-identical to `main:scripts/duplicati-wrapper.bash`, not on a feature branch as an earlier revision of this document said. The risk is unchanged and is about the *mechanism*, not the branch: `git checkout`, `git pull`, `git worktree remove` or an unfinished edit changes what the service runs on its next start. `/home/duplicati/bin` and
   `/home/duplicati/.config/Duplicati` are world-writable with no sticky bit, so any local user can rename-replace the script or the database until P0.5 closes them.
9. The unit now loaded (`ExecStart=… '--daemon-opts="${DAEMON_OPTS}"'`, armed by a global systemd reload at 03:23:44 on 09-21) and both wrapper revisions are mutually incompatible: systemd unquotes first and substitutes second, so the wrapper receives the single word `--daemon-opts="--webservice-port=8300"` (inner quotes literal). `#1968` passes it through as an unknown option and suppresses the default port; `d721fc78` — the revision the live symlink has resolved to since
   03:13:57 — extracts `"--webservice-port` (no value, stray quote) and ignores the
   `DAEMON_OPTS` environment entirely. **The next restart or reboot therefore does not bring the server up at all** — and that verdict does not rest on the argv bug: 2.4.0.0 checks the 0700 data-folder gate at every start, the folder has been 0777 since 09-20 18:33:45, and the gate refuses it *before* argv is parsed (§5.5). "On 8200, or not at all" was this document's earlier reading; the gate collapses it to "not at all". The watchdog reads `UNREACHABLE`
   either way. Do not restart the current unit before §8 P0 installs the corrected unit and wrapper and sets the folder to 0700.
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
- The server-database schema has 16 tables (`Backup, Schedule, Filter, Option, Metadata, …`) at version 11 (2.3.0.4) or 12 (2.4.0.0). Both versions of Duplicati therefore refused the file: journal 2026-09-19 20:48 ×5 (`largest supported version is 11`, pre-upgrade) and, post-upgrade, **2026-09-19 21:43, 21:52 and 21:55 (14 starts)** as well as 2026-09-20 18:02, 18:03 and 18:12 (`… is 12`).

Mechanism (sharpened by Lane B1 from the 2.4.0.0 source; neither 02:19:47 file is a "save"):

- `Duplicati-server.backup` is the **original profile-database inode**, born 2023-05-17 00:43:03 and *renamed* at 02:19:47.788. The producer is `RepairHandler.cs` 87–104: when `LocalRepairDatabase.CreateRepairDatabaseAsync` finds `knownRemotes <= 0` it does `baseName = Path.ChangeExtension(m_options.Dbpath, "backup"); File.Move(m_options.Dbpath, baseName)` and then runs a local repair. `RecreateDatabaseHandler` writes the stub in its place (same instant, 02:19:47.788)
  and its WAL at 02:19:48.142, `Operation='Recreate'`. So a **Recreate wrote a new local database into the server-database path**, and was cancelled; the main file was left at one page with every write in the WAL.
- `backups/backup Duplicati-server 20260825021947.sqlite` (02:19:47.693) is the **local-DB upgrader's** pre-upgrade copy — `DatabaseUpgrader.cs` 266–280, `BackupFilenamePrefix + " " + name + " " + yyyyMMddHHmmss + ".sqlite"` — which fires only when `Version < MAX`, i.e. only when the server file was opened *as a job database*. (`duplicati-database-tool`'s own backups are named `<name>-<ts>.bak`, so it is not that tool.)
- **The actor is unidentified.** The earlier reading — "consistent with the 2026-08-22 handoff's finding that the `Ubuntu` job's `DBPath` had been silently changed to the server DB path" — does not hold: the `.backup` this document itself reads shows `Ubuntu` already pointing at `SJTCQIIZSJ.sqlite` with no `dbpath` among its 7 job options, so the server's own job could not have supplied the server path. Something ran a Repair with an explicit `--dbpath` naming the server
  file; `~/.bash_history` holds 0 such lines and the user-lane logs name only `DQRVQNDIFX.sqlite`. Whether the pcalnon server was even running at 02:19:47 is doubtful — a WAL inode born at 02:19:48.142 means none existed, i.e. the old database had been cleanly closed. Root's shell history around 2026-08-25 02:19 is the one place left to look (§8 owner actions).
- The cancelled `Repair`/`Verify` that frame it are at **02:17:50, 02:18:37 and 02:19:24** (`Failed while executing Repair`; nine such failures in the `.backup` ErrorLog that morning, 02:05:17 → 02:19:24) and `Verify` at 02:13:07 and 02:19:46. Nothing happened at "02:19:19", which an earlier revision of this section asserted.

From that moment the pcalnon profile had no server database at all; the production job was recreated on the root server the same morning (YAM §3).

The current server DB: created 2026-09-20 18:19:43 (WAL born 18:19:43.917, 90 frames, salts `0cd60a99/6d70864b`) on the same 4 KB stub after the 112 MB WAL was moved to `temp/` at 18:19:26; schema version 12; `Backup` 0 rows; `ErrorLog` 4 rows `Failed to import backup` — two `JsonReaderException: Unexpected character encountered while parsing value: S` (a file starting with `SQLite format 3` was offered as an export) and two `SharpAESCrypt.WrongPasswordException` (an
encrypted export or volume with the wrong password).

Refutation test: a server database with a `Backup` table cannot have the `Remotevolume` table; `sqlite3 -readonly` on the copy shows which tables exist.

### 5.4 Leg C — the production database was locked behind a key that changed

Journal sequence (Appendix A.1): unencrypted through 09-18 20:42 → first start with a key at 21:03:27 (no warning; data folder mtime 21:03:34) → `Mismatch` from 21:08 → `Missing` from 21:15 after systemd rejected `Environment=SETTINGS_ENCRYPTION_KEY=<36 chars with %6 and %x>` (`Failed to resolve specifiers … Invalid slot`; a `%` in a unit-file `Environment=` value is a specifier, and an unknown specifier voids the whole assignment) → same on 09-19 19:14 → the folder abandoned for the pcalnon copy.

**What the key at 21:03 was is not recorded anywhere this design has looked, and the two candidates
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
(a `Missing` failure), and no `Server has started` follows it. The `Missing` ×5 across 13:32:34–13:32:38 and the
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
same database out of the 09-17 or 09-18 fileset.

### 5.5 Contributing factors

- **Portable mode by flag, never by inference.** The vendor unit never named a data folder; `--portable-mode` lived in `DAEMON_OPTS` (still present in the 09-20 13:32 wrapper echo, gone at 13:36). Duplicati resolves the folder as `--server-datafolder` > `--portable-mode` (`<install dir>/data`) > `DUPLICATI_HOME` > `~/.config/Duplicati`, with no automatic detection of a `data/` directory (`DataFolderManager.GetDataFolder`; the step-2c agent also ran a sandboxed 2.4.0.0 server
  with `/usr/lib/duplicati/data` present and it wrote to `$HOME/.config/Duplicati`). So the 09-18 19:57 crash was the flag plus a root-owned folder, and every later switch of folder was a change to `DAEMON_OPTS` or to what the wrapper managed to pass through. Fixed by an explicit `--server-datafolder` (§7.3.2).
- **Data-folder permission gate.** Shipped in canary 2.3.0.107 (2026-07-13) and first stable in 2.4.0.0 — so on this host it first applied with the 09-19 package upgrade — the server refuses a pre-existing data folder at every start unless it is mode 0700 with no group/other bits and owned by the running user or root (`PrepareSecureDataFolder`; overrides: `--allow-insecure-datafolder`, the env form `DUPLICATI__ALLOW_INSECURE_DATAFOLDER=true`, or an `insecure-permissions.txt`
  marker in the install folder). The migration chmod'ed the folder to 0777 *after* the 18:19 start — the loosening is datable by ctime: three files at 18:25:47.326 and the directory at 18:33:45.057, so it was not a recursive chmod (`.env`, `backups/`, `installation.txt` are untouched). The 18:19:42 start therefore passed the gate, and the next start **will** refuse the folder — not "may". This is what collapses §4.3 item 9 and §1 from "on 8200, or not at all" to
  "not at all": the gate is checked before argv is parsed, so the verdict does not depend on the argv bug. §7.3.2 sets 0700.

  **Two gate behaviours that decide whether a recovery step works**, measured on the installed 2.4.0.0 and
  recorded here because both fail in a misleading direction. (1) `duplicati-server-util` applies the gate and
  its refusal is **completely silent** — exit 1, zero bytes on stdout *and* stderr, before even the
  "Connecting to…" line. If a probe copy's directory is not 0700 owned by the invoking user or root, the
  command dies with no diagnostic at all; `chmod 0700` the copy directory first, or pass
  `--allow-insecure-datafolder`. (2) `duplicati-database-tool` does **not** apply the gate at all, despite
  advertising `--allow-insecure-datafolder` on every subcommand: it resolves the folder in
  `AccessMode.ProbeOnly`, which `DataFolderManager.cs` documents as "a no-op in ProbeOnly mode".
  `wipe-encryption --server-datafolder <0755 dir> --dry-run` runs normally with no override — so never read a
  successful `wipe-encryption` as evidence that a folder's permissions are acceptable to the **server**.
- **Package upgrade mid-migration.** 2.3.0.4 → 2.4.0.0 on 09-19 21:29 raised the server schema from 11 to 12 and changed the `Backup` table (`OperationType` column). Any recovered database is upgraded on first open; keep the pre-upgrade copy.
- **Permissions by trial.** `/usr/lib/duplicati` and `/usr/lib/duplicati/data` were chowned to `duplicati` — **directories only, and not even all of those**: 97 of 118 directories changed owner and 21 did not (the whole `runtimes/` subtree, 11 directories, and ten `licenses/<package>/` directories — `licenses/` itself *did* change, so this was a shallow or interrupted recursion, not a `find -type d` sweep). All 1,443 regular files outside `data/`, the binaries
  included, are still `root:root`. This matters for the P0.5 remediation: a `chown -R` that is verified by "did anything change?" will see 97 changes and 21 no-ops, and the 21 that look wrong are the ones that were already right. The destination tree was chgrp'd (directories 09-18 20:36–20:37, 874 volumes 09-19 17:37); the duplicati home dirs were opened to 0777. Each removed a symptom; none was recorded.
- **Wrapper defects** (§4.3) turned a one-line configuration into a parser with `eval`, an argv bug and a debug mode that logs secrets.
- **No runbook** existed for "move the server to another user" although the record already contained every trap it hit (YAM §8.19.4, §8.20).

### 5.6 What refutes each leg, and the instruments

| Leg | Would be refuted by | Instrument used | Could the instrument have said otherwise? |
| --- | --- | --- | --- |
| A | `Yamaguchi` rows in a pcalnon-profile database, or `LastBackupDate` advancing in it after 08-25 | forensics on copies of `Duplicati-server.sqlite`+WAL and `Duplicati-server.backup`; snapshot journal | yes — it printed `Yamaguchi` from the root snapshot and would have printed it from the profile |
| B | a `Backup` table in the replayed WAL, or a `Version` row ≤ 12 | forensics (table list, `Version`, `Operation`) | yes — the same code printed 16 server tables for the other three databases |
| C | a `Server has started` line on a start **whose data folder is the root folder** (the port discriminates — §5.4) | `journalctl -u duplicati.service`, deduplicated, read against `WebServerLoader.cs`'s port fallback | yes — and **none exists after 09-18 21:03:30** |

The Leg C row changed at reconciliation and is worth stating plainly, because as first written it was
not a refutation test at all: it named an observation that *exists* ("it shows exactly such lines at
09-20 13:32") and then explained it away. The repair is the port. A `Server has started … port 8200`
line proves the option word was unusable, hence the `--portable-mode` glued into it was inert, hence
the folder was `$HOME/.config/Duplicati` — so the 13:32:50 success is a *home*-folder start, not a
counter-example. The root folder was last opened at 09-19 19:15:01, a `Missing` failure, and no
`Server has started` follows it.

### 5.7 Corrections to the record

Listed in Appendix C; the load-bearing one: "schema-19 profile server DB" → "aborted local-DB Recreate stub written over the profile server DB at 2026-08-25 02:19:48; the last real profile server DB is `Duplicati-server.backup` of 02:19:47, which is the **original 2023 inode** renamed by a `RepairHandler` local repair, not a save". **Appendix C items 1–8 are corrections this document records; none is yet applied to its target document** — that is a tracked
follow-up, not a closed one.

---

## 6. Secret exposure inventory and remediation

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
`syslog-20260920.gz` carry **5 and 18 `Invalid slot` lines** — 23, the journal's own
figure. (Under the narrower `Failed to resolve specifiers` predicate the split is 4 and 18 = 22; the extra line
in 09-19's file is the `Failed to resolve unit specifiers` of 21:23:25. Count with the same predicate or the
totals will not reconcile.) logrotate keeps day files ~10 days, so this set ages out around **2026-10-01**. A
journal scrub that does not also scrub these removes nothing (D-8).

Two operational notes for whoever writes the scrub. `delaycompress` means a day file gains its `.gz` one
rotation *after* it stops being written — `syslog-20260921` was plain when this document was drafted and is
`syslog-20260921.gz` now — so **glob the set, never name a file**. And re-measuring these counts is itself an
exposure: a `journalctl` capture large enough to count them is a fresh, complete copy of every leaked line.
Round 2's own host lane created an 876 MB one and deleted it eight minutes later; the D-8 scrub is only as
complete as the last agent who cleaned up after themselves.

| # | Secret | Where it is exposed | Since | Who can read it | Remediation |
| --- | --- | --- | --- | --- | --- |
| S-1 | Old settings key (36 chars) | `scripts/duplicati-wrapper.bash` comment line 49, in `main` since #1967 (`6708cb28`); 23 systemd `Invalid slot` journal lines, **and the same 23 lines in `syslog-20260919.gz` (5) and `syslog-20260920.gz` (18)** | 2026-09-18 / 09-20 | anyone with the repository (public); every process running as `pcalnon`, via `adm`; root | Treat as burned; it unlocks nothing (note S-1a). The block is already removed in-tree (P1 step 3); close the detection gap (below) |
| S-2 | Current settings key = **the live `Yamaguchi` backup passphrase** (32 chars) | `.env` line 22 (0660 duplicati:duplicati — readable by any `pcalnon` process carrying gid 139 — note S-2b); journal **and `/var/log/syslog*`**: 12 `Exporting Environment Variable` and 12 `Settings Encryption Key:` lines on 09-20 | 2026-09-20 | same as S-1 | Never reuse the backup passphrase as the settings key — the key exists to protect the passphrase at rest. Re-key in **P0.5b** (note S-2a) |
| S-3 | `PASSPHRASE`, `PASSPHRASE_OLD` | `.env` lines 17–18 as commented-out assignments; journal **and `/var/log/syslog*`**: **60** `LINE: "# export …"` echoes on 09-20 = 12 `PASSPHRASE` + 12 `PASSPHRASE_OLD` + 36 `SETTINGS_ENCRYPTION_KEY`, each carrying text after the `=` | 2026-09-20 | root, `adm` (= every `pcalnon` process), group `duplicati` — and, through S-7, **every local user** | Delete the commented lines. **D-2 RULED 2026-09-22** (§10.1); rotation alone does not re-encrypt (note S-3b) |
| S-4 | Same passphrases in `…/Dropbox/Backups/_yamaguchi_keys/env` (`-rwxrwx--- pcalnon:duplicati`, 388 B — **group-readable by the service user**, where YAM §8.19.2 recorded 0600 in a 0700 dir) | inside the Dropbox-synced tree; `dropbox filestatus` reads `up to date` | since the Dropbox root moved onto `sda1` (~09-15) | the Dropbox account and every device or app linked to it; locally, group `duplicati` | `chmod 0600` now; copy out, then delete forever and audit the account (note S-4a) |
| S-5 | Web-UI credential — **and twelve other secrets beside it** | primary checkout `.env` (`DUPLICATI_WEB_CREDENTIAL`), **mode 0664 — world-readable**, now stale; 12 other names in the same file, several of them Slack tokens. It holds **0** `PASSPHRASE=` lines, so S-3 is *not* world-readable through it | since 2026-08-23 | every local user | New UI password, stored 0600 at `~/.config/duplicati-backup/web-credential`; **both** API clients re-pointed in the same PR (note S-5a) |
| S-6 | Sign-in token URLs | journal **and syslog**: **five** `signin.html?token=…` URLs (09-19 21:20:41, 21:57:41; 09-20 13:32:50, 13:36:40, 18:19:46), not one; all expired | 2026-09-19 | `adm` (= every `pcalnon` process) for each token's lifetime | Set the password on the first start, then pass `--webservice-disable-signin-tokens` (note S-6a) |
| S-7 | **Both passphrases, cleartext, world-readable, inside the backup source** | `juniper-ml/.claude/worktrees/curious-plotting-hummingbird/.env`, 114 B, **mode 0664**, 2026-08-23 | 2026-08-23 | **every local user**, and every restore of any fileset taken since | Reconcile fingerprints, then remove **the file only** (note S-7a). This is the exposure D-2 was ruled without |
| S-8 | `additional-report-url` bearer JWT | inside **every** copy of the server database: the daily snapshot in `~/.local/state`, the P0 evidence freeze, whatever Procedure A0/A/A2/B produces, and P4's tar | since the report URL was configured | anyone who reads any database copy | It is a credential, not merely a URL (YAM §8.18.4, §8.19.8 item 6); **rotate it if any copy leaves the machine** (note S-8a) |

Notes on the rows above:

- **(S-1a)** The burned key is **not** the key that encrypted the 09-18 database: the offline hash test excludes it and eleven shell-mangling variants (§5.4), so it unlocks nothing and Procedure A no longer depends on it. A history rewrite is not worth its cost once the key is dead — GitHub keeps `refs/pull/1967/head` regardless, and `forks_count` is 0.
- **(S-2b)** Group membership binds at **login**, not at `chmod` time: a `pcalnon` session older than the group grant does not carry gid 139 and cannot read this file — round 2's own host lane could not, and the Dropbox daemon cannot either (§4.4). That shrinks the exposure not at all, since `sudo` and `su - duplicati` are each one step away and the 0777 database copies need no group membership whatsoever. State it as a property of
  *processes*, never of the user.
- **(S-2a)** The `.env` comment labels this value "Ubuntu-fresh". **That label is stale**: `util/ad-hoc/2026-09-21_env_value_equality.py` shows it byte-identical to the live Yamaguchi passphrase. Read the value, never the comment. The replacement key is random, distinct from every passphrase, delivered as a systemd credential, and escrowed with the passphrases.
- **(S-3a)** D-2 was ruled "accept + scrub" against a *local journal* exposure. The reader set is now: every process running as `pcalnon` (via `adm`), `/var/log/syslog*` for another ~10 days, this arc's cloud-linked Claude Code transcripts, a world-readable cleartext file inside the backup source (S-7), and — through S-4 — a third party's cloud. Four different ways in which "local readers only" is false.
- **(S-3b)** "Rotation does not re-encrypt existing volumes" is true of a rotation and **not** of the product as a whole: `Duplicati.CommandLine.RecoveryTool.Implementation.dll` carries a `recompress` verb taking `--reencrypt` and `--new-passphrase`, which rewrites existing volumes under a new passphrase. That is what makes D-2's ruling — rotate **and keep** the existing sets — achievable rather than aspirational. §10.2 sequences it and names the three hazards that ride with it.
- **(S-4a)** `dropbox exclude add` is **not** an alternative to moving it: selective-sync exclusion removes the *local* copy and leaves the cloud one in place. So: `cp -a` the folder to a sibling outside the Dropbox root, sha256-verify both sides, delete the in-tree copy on owner sign-off, then **"Delete forever"** on dropbox.com and audit the account (2FA, linked devices, third-party apps, plan retention). The sda1 escrow was accepted as a *machine-local* copy, not a
  cloud copy — its own README says so. Exclude `_yamaguchi_records/` too if it lists paths.
- **(S-5a)** The UI credential is not a convenience: any authenticated API principal can point the job's `--run-script-before` at any path, and that script runs as `duplicati` with `CAP_DAC_READ_SEARCH`. It is **a host-wide read of everything the service can read** (§7.3.6). Also remove `util/ad-hoc/duplicati_api.py`'s bare-secret fallback, which posts the whole file as the password when no candidate key matches — and since its key list omits
  `DUPLICATI_WEB_CREDENTIAL`, that is the path it takes today. The twelve other values in that file are out of scope here but are in the same world-readable file.
- **(S-6a)** The server mints a token on **every** start while the password is still autogenerated (`Program.cs`: `if (Origin == "Server" && AutogeneratedPassphrase) … CreateSigninToken`), so every restart before the password is set writes a fresh *live* token into adm-readable logs — and with `CAP_DAC_READ_SEARCH` a token is root-read for its lifetime.
- **(S-7a)** Reconcile the sha256[:16] fingerprints per `HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §1 item 8 **first**, then remove the file. That worktree is **DO NOT SWEEP**: `git worktree remove` would delete it silently, and it is protected for unrelated reasons. Remove the file, never clean the directory.
- **(S-8a)** Procedure B must state whether the rebuild re-creates the report URL; if it does, the new JWT is a new secret and belongs in this table on the same terms.

Detection gap behind S-1: the repository has GitHub secret scanning and push protection enabled, but
`secret_scanning_non_provider_patterns` is **disabled** (`gh api repos/pcalnon/juniper-ml --jq .security_and_analysis`),
so a generic key literal is never flagged, and gitleaks passed both PRs. Enable the non-provider patterns and add a
gitleaks rule for `SETTINGS_ENCRYPTION_KEY=` / `PASSPHRASE=` assignments (inherited requirement JR-DEP-SEC-005 covers the
allowlist half of this class).

Journal scrub (D-8) — **the journal is half the job**. The journal cannot delete individual lines:
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
| Claude Code transcripts **and persisted tool-result files** under `~/.claude/projects/…` | **cloud-linked**, and **inside the backup Source** — note (AC-3a) lists `.claude/projects` among the *unfiltered* 0700 trees, so every capture is in every T1 fileset and in Dropbox (note sink-a) | count-grep and purge **both** the `.jsonl` transcripts and the `tool-results/` files; this is what makes D-2's "local exposure" framing false |
| Per-session agent scratch trees under `/tmp/claude-1000/…` | Round 1's six lanes and round 2's four each wrote captures, extracted units and analysis output there, `drwx------ pcalnon` | `/tmp` is **tmpfs**, so a reboot clears them and they are **not** in the backup Source — state that rather than leave it inferred; until a reboot they are readable by every `pcalnon` process |
| Ad-hoc instruments that **read** a secret file | `2026-09-21_env_value_equality.py`, `…_settings_key_hash_probe.py`, `2026-09-22_credential_file_shape.py`, `duplicati_api.py` (S-5a) | an instrument that reads a secret is itself a sink if it writes an artifact: each states in its header what it writes and where, and none writes into `notes/`, `util/` or the backup Source |
| World-readable server-DB copies, **by path** | Reachable by any local user, all under `/home/duplicati/.config/Duplicati/`: `Duplicati-server.backup` **0777**, `backups/Duplicati-server_2026-08-22_pre-dbpath-fix.sqlite` **0644**, `temp1/Duplicati.GUI.TrayIcon-crashlog.txt` **0644** (note S-9a) | `chmod 0600` the duplicati-home set — `enc-v1:` under the pcalnon-profile libsecret key, so encrypted but wrongly exposed |
| **Re-measuring the exposure creates a new copy of it** | A `journalctl` capture large enough to count these lines is itself a complete second copy. Round 2's host lane made an 876 MB one and removed it eight minutes later | Any agent or operator who re-verifies §6's counts deletes the capture in the same session, and says so |

- **(sink-a)** Large tool outputs are written as **separate files** under `<session>/tool-results/`, not inlined into the `.jsonl` — which is exactly where this arc's oversized `journalctl` captures landed, *because* they were too large to inline. A purge that walks only the transcripts misses them.
- **(S-9a)** Every ancestor of those three is 0755 or 0777, so they need no group membership to read. `temp1/`
  holds a **second** full copy set (`.backup`, `.sqlite`, `-shm`, a 112 MB `-wal`) at 0600 and `temp/` a third
  112 MB `-wal`; neither directory is named in §4.1. The same-named files under
  `/home/pcalnon/.config/Duplicati/` are mode-loose but **path-protected** — that profile is 0700 — so a
  `chmod 0600` sweep scoped to *them* fixes nothing that was broken.

---

## 7. Integrated design

### 7.1 Principles

1. **One explicit source of truth per path.** The data folder, the destination, the tempdir and the credential locations are named in one place each (unit + `/etc/default/duplicati`), never inferred from `HOME`, from a `data/` directory beside a binary, or from a hardcoded string in a tool.
2. **Secrets never pass through a shell parser or a log.** The settings key arrives as a systemd credential; the passphrase stays inside Duplicati's database and the escrow files; no script echoes a file or the environment.
3. **Least privilege with one deliberate exception, and the exception is bigger than it looks.** The server runs as `duplicati`, confined by systemd, and is granted `CAP_DAC_READ_SEARCH` so it can read every file under `/home/pcalnon` — the root-era coverage — without being root (D-4). State the trade plainly: that capability bypasses **every** read and search check on the host, not only `/home/pcalnon` — `/etc/shadow`, `/etc/ssh/ssh_host_*_key`, `/etc/credstore/*` (every
   other service's secrets), `/root`, `/var/lib/docker`, the journal and `/var/log/syslog*` (which hold this arc's leaked passphrases), and every other user's home. `ProtectSystem=strict` and `ProtectHome=read-only` stop *writes* — they are mount flags, correctly not defeated by the capability — but hide nothing from a read. The alternative, recursive ACLs on `/home/pcalnon`, bounds the blast radius to that tree but is fragile in exactly the way AC-3 exists to catch: a
   `chmod 600`, a `mkdir -m 700`, or gpg's own permission checks reset the ACL mask and the file silently leaves the backup. So: the capability bounds the damage to *the whole host*, ACLs bound it to *one tree but unreliably*. D-4 is that choice, and it is the owner's. Whichever is chosen, §7.3.2's confinement set is what keeps the capability from also being an exfiltration channel, and the residual is recorded: **"duplicati uid inside the unit == root-read"**.
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
- `/usr/lib/duplicati` returns to `root:root` **before P0 runs any Duplicati tool, not in P2** (§8 P0.5): the directory is `duplicati:duplicati 0755` with no sticky bit today, so the service user can move any entry aside and drop in its own `duplicati-cli`, `duplicati-server-util`, `duplicati-database-tool` or `duplicati-server` — which `root` and `pcalnon` then execute during recovery, and `/usr/bin/duplicati-*` are symlinks into it. `webroot/` is writable the same way,
  so injected JavaScript would load in the operator's browser. `/usr/lib/duplicati/data` is archived and removed after recovery (§8 P4).

**Trust domains, and the six crossings between them.** "The `duplicati` uid inside the unit" and "the
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
| `.env` → code in the capability-bearing process | an `LD_PRELOAD`/`DOTNET_STARTUP_HOOKS`/`PATH`/`BASH_ENV` line in a file the plain `duplicati` uid can write | the wrapper's **positive** export allow-list (§7.3.3); the `.env` **mode** closes it only once the file is outside the duplicati-owned data folder (§7.3.5) |
| `/proc/<serverpid>/environ` → the settings key | same uid reads the server's environ | the secret-provider channel (§7.3.5) **if adopted**; the unit as shipped uses the `LoadCredential=` + wrapper-export fallback, under which this crossing is **OPEN** |
| readable DB + key → JWT → API → run-script | mint a signin token from the database, then set `--run-script-before` | UI credential hygiene + `--webservice-disable-signin-tokens` (§7.3.6) |
| entry replacement in `/usr/lib/duplicati` | 0755 duplicati-owned directory | P0.5a's `chown` |
| **`$CREDENTIALS_DIRECTORY/settings-key` → any run-script → the job passphrase** | `LoadCredential=` exposes the key to **every** process in the unit, run-scripts included (`man systemd.exec`), and a run-script path is a plain job option. Chain: UI credential → API → `--run-script-before` → the key → the server DB → the passphrase → **every volume in T1 and T1c** | **NOT closed as shipped.** Only the secret-provider channel (§7.3.5) replacing `LoadCredential=`, plus AC-13 |
| capability-read data → the internet | write it into the Dropbox-synced destination; the daemon uploads it | `ReadWritePaths=` scoped to `Yamaguchi/` (§7.3.2) + D-13. **`IPAddressDeny=` does not close this** |

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
DAEMON_OPTS="--webservice-port=8300 --webservice-interface=loopback --server-datafolder=/home/duplicati/.config/Duplicati --disable-update-check"
```

The unit is a **full unit in `/etc/systemd/system/`**, which takes precedence over the vendor file and survives package upgrades (a drop-in would also work, but `ExecStart=` must then be reset with an empty assignment first; a complete file is easier to review).

```ini
# file: etc/systemd/system/duplicati.service
[Unit]
Description=Duplicati backup server (Yamaguchi job, dedicated service user)
Documentation=file:///home/pcalnon/Development/python/Juniper/juniper-ml/notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md
# No network-online.target: this server listens on loopback and its destination is file://,
# so it has no network dependency to order against.
After=local-fs.target
# The destination and the data folder must be mounted before the server starts, and the
# server stops if either is unmounted (an unmounted destination reads as "everything missing").
RequiresMountsFor=/mnt/Backups /home/duplicati
StartLimitIntervalSec=10min
StartLimitBurst=5

[Service]
Type=simple
User=duplicati
Group=duplicati
# D-14 (RULED 2026-09-22): 0027, not 0007. New volumes land 0640 duplicati:duplicati, so pcalnon
# and the Dropbox daemon read them through the group and neither can rewrite or unlink one.
UMask=0027
Nice=19
IOSchedulingClass=idle
IOSchedulingPriority=7
EnvironmentFile=-/etc/default/duplicati
# The settings encryption key: a root-only file, exposed to the service as
# $CREDENTIALS_DIRECTORY/settings-key (never in the environment block, never on argv).
LoadCredential=settings-key:/etc/credstore/duplicati-settings-key
ExecStart=/usr/local/lib/duplicati/duplicati-wrapper.bash $DAEMON_OPTS
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
# Scoped to the job's OWN destination, not the whole Backups/ tree. The parent holds
# _yamaguchi_keys/ (the passphrase escrow), _yamaguchi_frozen_20260826/ and ten
# .dlist.zip.gpg archives -- and every one of those directories is drwxrwx---
# pcalnon:duplicati with NO sticky bit, so a ReadWritePaths= on the parent would let this
# service read AND UNLINK the only key custody T1 and T1c have, with the deletion
# propagating to Dropbox. That would also contradict section 8's own "nothing under
# /mnt/Backups/Ubuntu/ is deleted or moved" rule. Duplicati needs write on the
# destination directory only.
ReadWritePaths=/home/duplicati /mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi
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
# Socket egress is denied. It is NOT the only egress, and the reason usually given --
# "Dropbox is a separate daemon" -- is precisely why: ReadWritePaths= below opens a
# directory that the pcalnon Dropbox daemon replicates to a third party (S-4 records
# `dropbox filestatus` reading "up to date" for this tree). Anything this service writes
# into the destination LEAVES THE MACHINE, and IPAddressDeny= cannot see that path, because
# the upload is another process's socket. Scoping ReadWritePaths= to Yamaguchi/ and D-13's
# Dropbox root policy are therefore confinement controls, not hygiene. What this block does
# close is the server's own sockets: the update check and usage reporting.
IPAddressDeny=any
IPAddressAllow=localhost
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
# @system-service does NOT exclude @privileged wholesale: 18 of @privileged's 53 calls are in
# its transitive closure (chown/fchown/lchown, capset, setfsuid, setgroups, setres*uid...),
# which is why `systemd-analyze security` prints a 0.2 "SystemCallFilter=~@privileged ...
# chown is allowed" row. That row is expected and is NOT evidence against this filter.
# What @system-service DOES exclude is open_by_handle_at(2) specifically: the closure allows
# name_to_handle_at (make a handle) and not open_by_handle_at (use one). That is the call
# CAP_DAC_READ_SEARCH explicitly grants, and it opens ANY inode of a mounted filesystem by
# handle -- bypassing InaccessiblePaths= and TemporaryFileSystem= entirely. Path masking
# without this filter is therefore not a boundary at all. Verified on systemd 259 by expanding
# the set transitively; a direct-member listing does not show it, because @system-service is
# mostly nested groups.
SystemCallFilter=@system-service
SystemCallErrorNumber=EPERM
ProtectProc=invisible
ProcSubset=pid
PrivateDevices=yes
ProtectClock=yes
ProtectHostname=yes
ProtectKernelLogs=yes
RestrictNamespaces=yes
# Bound, not boundary: a mount mask is escaped by resolving a path through
# /proc/<pid>/root of any process in another mount namespace that this uid may ptrace --
# i.e. any duplicati-uid process OUTSIDE this unit. ProtectProc=invisible does not stop it
# (man systemd.exec: it hides processes owned by OTHER users), and no special syscall is
# needed, just openat. So every `sudo -u duplicati` / `su - duplicati` session is, while it
# lives, a hole in the list below -- and section 7.3.1 prescribes exactly those as the
# administration model. Keep them transient; `usermod -s /usr/sbin/nologin duplicati` moves
# from P4 to P0.5a for this reason. What the mask reliably buys is protection from the
# service's own code paths and from accident, not from a deliberate same-uid adversary.
# /etc/credstore IS masked -- see the note below for why that does not break
# LoadCredential=. The shadow- / gshadow- backups hold the previous generation of the same
# hashes; /run/log/journal is the volatile journal, which -/var/log does not cover; and
# /var/spool/cups is named by section 6's own sink checklist as a place the printed escrow
# sheet may still sit, which makes it the one entry whose contents may be a live passphrase.
InaccessiblePaths=-/etc/shadow -/etc/shadow- -/etc/gshadow -/etc/gshadow- -/etc/ssh -/etc/credstore -/etc/credstore.encrypted -/var/lib/docker -/var/log -/run/log/journal -/var/spool/cups -/root -/mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_keys
# Disabled by the names the software ACTUALLY reads. DUPLICATI__DISABLE_UPDATE_CHECK and
# DUPLICATI__USAGE_REPORTER_LEVEL do NOT exist: a utf-8 AND utf-16le scan of all 1,443
# files under /usr/lib/duplicati finds neither in either encoding
# (util/ad-hoc/2026-09-22_duplicati_literal_scan.py). The generic DUPLICATI__ mapping is
# LOWER-case with '-' -> '_' (run-script-example.sh ll. 76-80); the upper-case forms in the
# product are hand-written specials, e.g. DUPLICATI__ALLOW_INSECURE_DATAFOLDER, which the
# same scan does find. An unread environment variable produces no "Unknown option supplied"
# line, so AC-14 structurally CANNOT catch a wrong name here -- which is why the option form
# below is also set, in /etc/default/duplicati, where AC-14 can see a typo.
#
# Note for anyone re-running that scan: the two names below are NOT literals either. The
# assemblies carry the templates AUTOUPDATER_{0}_SKIP_UPDATE (Duplicati.Library.AutoUpdater.dll)
# and USAGEREPORTER_{0}_LEVEL (Duplicati.Library.UsageReporter.dll); {0} resolves to
# "Duplicati" from the embedded manifest resource AutoUpdateAppName.txt. So a literal scan
# reports NOT FOUND for the substituted forms and that is CORRECT -- it is the templates plus
# the resource that establish them. DO_NOT_TRACK is a direct literal. (Round 3.)
Environment=AUTOUPDATER_Duplicati_SKIP_UPDATE=1
Environment=USAGEREPORTER_Duplicati_LEVEL=none
Environment=DO_NOT_TRACK=1

[Install]
WantedBy=multi-user.target
```

Notes: `PrivateTmp=yes` gives the server a private `/tmp` that is still `tmpfs`; the job's `--tempdir` therefore moves to `/home/duplicati/.cache/duplicati-tmp` (ext4, inside `ReadWritePaths`). The old tempdir `/home/pcalnon/.cache/duplicati-tmp` is read-only to the service under `ProtectHome=read-only`, which is what we want — it was a root-era choice. `RequiresMountsFor=` also orders the unit after `mnt-Backups.mount`.

`/etc/credstore` **is** masked, and an earlier revision of this paragraph argued the opposite on two
grounds that are both wrong. `LoadCredential=` is unaffected: `man systemd.exec` states that the credential
source *"must be accessible to the service manager, but **do not have to be directly accessible to the
unit's processes**"*, The manager reads the file and hands the unit a separate read-only copy at `$CREDENTIALS_DIRECTORY`.
(The manual's *"the system service manager … will search `/etc/credstore/`"* sentence is often quoted here
as well; it governs a **relative** `LoadCredential=` path, and this unit uses an absolute one, for which the
operative sentence is *"If the specified path is absolute it is opened as regular file and the credential
data is read from it."* The conclusion is the same either way — the manager opens it before the unit's
namespace exists — but cite the right clause.) And the
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
(`sudo systemd-run --unit=credtest -p LoadCredential=t:/etc/credstore/<file> -p InaccessiblePaths=-/etc/credstore --pipe --wait /bin/sh -c 'wc -c < "$CREDENTIALS_DIRECTORY/t"'`).

**None of the confinement directives above has been executed against 2.4.0.0 on this host.** That is
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
and record that switch. AC-12 is what closes it: the server must complete a full backup under this exact set,
and any directive it cannot run under is removed **and recorded**, never silently dropped. Run it first
with `systemd-run` against the P0 probe copy, not against the live service.

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
# No eval. No word-splitting of file content. No secret value is ever printed -- including by
# the error paths, which print an option's NAME and its value's LENGTH only.
#
# Unknown options: this wrapper does NOT validate option names against the server's own list,
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
# start good. AC-14 pins that grep. (Lane B2 C6, corrected by round 2 Lane A.)
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
    # The rejection message prints the option NAME and the value's LENGTH, never the value:
    # a mistyped --webservice-password=<secret> line in .env must not reach the journal
    # through the fail-closed path. (Lane B3 F-5.)
    local src="$1" word="$2" name
    if ! is_option "${word}"; then
        die "${src}: not a Duplicati option: '${word%%=*}' (value length ${#word})"
    fi
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

# --- D-6 drift gate (RULED 2026-09-22) -----------------------------------------------------
# The repository is canonical and what the unit executes is a COPY. Two different things can
# therefore drift, and they mean OPPOSITE things:
#
#   * the INSTALLED file no longer matches what was blessed -> someone edited /usr/local/lib
#     outside this installer. Never overwrite that silently; it is the only evidence.
#   * the REPOSITORY no longer matches what was blessed -> an intended behaviour change. That
#     is legitimate, and is exactly what --update-backup-behavior authorises.
#
# A symlink into the checkout was considered for this job and rejected: on a fresh host the
# checkout does not exist yet, so ExecStart= would resolve to a dangling target and the service
# would not start -- failing in the bare-metal recovery case the symlink was proposed for.
BLESSED=/usr/local/lib/duplicati/.blessed.sha256
UPDATE_BEHAVIOR=0
for arg in "$@"; do
    [[ "${arg}" == "--update-backup-behavior" ]] && UPDATE_BEHAVIOR=1
done

blessed_for() { [[ -s "${BLESSED}" ]] && awk -v d="$1" '$2 == d { print $1 }' "${BLESSED}"; }

drift=0
for pair in "${WRAPPER_SRC}:${WRAPPER_DST}" "${UNIT_SRC}:${UNIT_DST}" "${DEFAULTS_SRC}:${DEFAULTS_DST}" "${GUARD_SRC}:${GUARD_DST}"; do
    src="${pair%%:*}"; dst="${pair##*:}"
    want="$(blessed_for "${dst}")"
    [[ -n "${want}" ]] || continue          # never blessed: first install, nothing to compare
    if [[ -f "${dst}" ]] && [[ "$(sha256sum "${dst}" | cut -d' ' -f1)" != "${want}" ]]; then
        echo "DRIFT: installed ${dst} does not match its blessed checksum -- changed outside this installer" >&2
        drift=1
    fi
    if [[ "$(sha256sum "${src}" | cut -d' ' -f1)" != "${want}" ]]; then
        echo "BEHAVIOUR CHANGE: ${src} differs from the blessed checksum" >&2
        drift=1
    fi
done
if (( drift == 1 && UPDATE_BEHAVIOR == 0 )); then
    echo "Refusing to install. Inspect the differences, then re-run with --update-backup-behavior" >&2
    echo "to bless the current repository contents as what this host executes." >&2
    exit 4
fi

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

: > "${BLESSED}.new"
for pair in "${WRAPPER_SRC}:${WRAPPER_DST}" "${UNIT_SRC}:${UNIT_DST}" "${DEFAULTS_SRC}:${DEFAULTS_DST}" "${GUARD_SRC}:${GUARD_DST}"; do
    src="${pair%%:*}"; dst="${pair##*:}"
    cmp -s "${src}" "${dst}" || { echo "checksum mismatch after install: ${dst}" >&2; exit 1; }
    printf '%s  %s\n' "$(sha256sum "${dst}" | cut -d' ' -f1)" "${dst}" >> "${BLESSED}.new"
    echo "installed ${dst} ($(sha256sum "${dst}" | cut -c1-16))"
done
# Bless only after every copy verified. A blessed file written earlier would record a state that
# a later failure never reached, and the next run would compare against a fiction.
install -m 0644 -o root -g root "${BLESSED}.new" "${BLESSED}"
rm -f "${BLESSED}.new"
echo "blessed ${BLESSED} (re-bless deliberately with --update-backup-behavior)"

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
echo "      sudo -u duplicati DUPLICATI__REMOTEURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi \\"
echo "           ${GUARD_DST}; echo \"guard exit=\$?\"   (must be 0 BEFORE the job is resumed)"
echo "      systemctl restart duplicati.service && journalctl -u duplicati.service -n 20"
echo "      systemd-analyze security duplicati.service"
```

`util/systemd/duplicati.service` and `util/systemd/duplicati.default` are the repository copies of the two
files shown in §7.3.2, and `util/yamaguchi-pre-backup-guard.bash` is the repository source of the guard shown
in §7.5; the install script refuses to run unless all four exist. The **shadowing** must be stated because it
is not obvious: the loaded unit today is the vendor file `/usr/lib/systemd/system/duplicati.service`, edited
in place. Installing to `/etc/systemd/system/duplicati.service` **shadows** that file, it does not replace
it — the vendor copy stays on disk with its in-place edits, and a `dpkg` upgrade will rewrite it without
affecting what systemd loads. Anyone debugging this later reads `systemctl show -p FragmentPath`, not the
vendor path.

The T2 lane needs its own installer and does not have one: `util/install_duplicati_timer.bash` installs the
**old** CLI lane's five files by name. §7.8's three user units and two scripts are a P3 deliverable
(`util/install_juniper_backup_timer.bash`), not something the existing script can be pointed at.

#### 7.3.5 The `.env` contract and the settings key

```text
# file: home/duplicati/.config/Duplicati/.env
# Duplicati server: local overrides.
# MODE IS AN OPEN OWNER DECISION (recorded as dissent in the design's section 11):
#   0600 duplicati:duplicati  -- Lane A3 / Lane B2 D15; the service user can rewrite its own
#                                tunables, which is the status quo.
#   0640 root:duplicati       -- Lane B3 F-5, and what this design RECOMMENDS: the wrapper
#                                only ever READS this file, so the service user needs no
#                                write, and a file the plain duplicati uid can write is a
#                                code-injection path into a process holding
#                                CAP_DAC_READ_SEARCH (see the crossings table in 7.3.1).
# Until the owner rules, install it 0640 root:duplicati -- AND OUTSIDE THE DATA FOLDER.
# The mode only binds if the file leaves /home/duplicati/.config/Duplicati/: that directory
# must be 0700 duplicati:duplicati (Duplicati's own requirement) and the server must own it
# to write its database there, so the duplicati uid holds write on the DIRECTORY -- and in
# POSIX, delete permission comes from the parent directory, not the file. A 0640
# root:duplicati .env inside it is unlink-and-recreate-able by the service user, which
# defeats the whole point of the mode. Install it at /etc/duplicati/env in a 0755 root:root
# directory and point the wrapper's DUPLICATI_ENV_FILE default there. That also removes a
# second-order contradiction: section 7.3.2 requires files in the data folder to be 0600
# while this contract installs one at 0640.
# Grammar (enforced by the wrapper, which refuses anything else):
#   KEY=VALUE | export KEY=VALUE | --option[=value] | # comment | blank
# KEY=VALUE values are literal (no shell expansion; matching surrounding quotes are removed), and
# only these names may be exported: SETTINGS_ENCRYPTION_KEY, DUPLICATI__*, TMPDIR, TZ, LANG, LC_ALL.
# --option lines are passed to the server verbatim, quotes included; leading whitespace is ignored.
# NEVER keep a real secret in a comment. A commented-out assignment is still a secret on disk,
# and on 2026-09-20 every line of this file was echoed into the system journal.
# The settings encryption key is delivered by systemd (LoadCredential=) and must not be set
# here while the unit supplies it. For a hand run outside systemd, export it in the shell.
#
# The --option line below is INERT under the unit as shipped: DAEMON_OPTS (precedence 3) also
# sets --webservice-port, and a later source wins for the same option name. It is kept as a
# worked example of the grammar, not as a live tunable -- changing it here changes nothing.
# Declaring one setting in two artifacts is exactly what principle 1 of section 7.1 forbids;
# when the port must change, change /etc/default/duplicati.
--webservice-port=8300
```

Settings key policy (D-1, recommended): keep database encryption **on**, with a key that is (a) random and distinct from every passphrase, (b) stored at `/etc/credstore/duplicati-settings-key` root:root 0600 and delivered by `LoadCredential=`, (c) escrowed exactly where the passphrases are (printed sheet, password manager, machine-local copy outside the Dropbox root), and (d) made mandatory with `--require-db-encryption-key` in `DAEMON_OPTS`, so a missing credential stops
the server instead of silently starting it unencrypted. The record's 2026-08-30 objection — a third key to escrow — stands and is accepted as the price of not leaving the passphrase in cleartext in a database that is copied daily into `~/.local/state`. The alternative, `--disable-db-encryption` in `DAEMON_OPTS`, is one line and needs no escrow; it is the right choice if the owner prefers fewer keys over encryption at rest. Whichever is chosen, the choice is recorded in D-1
and in `/etc/default/duplicati`.

**The delivery channel matters as much as the key.** The wrapper `export`s `SETTINGS_ENCRYPTION_KEY` and
then `exec`s, so the key sits in the server's environment for its whole lifetime and is inherited by *every*
child — including run-scripts and their children (§7.5). Duplicati's own secret-provider channel avoids that
entirely: `Program.cs`'s `ApplySecretProviderAsync` runs over the server's own options **before** startup, so
`--settings-encryption-key=$settings-key --secret-provider=file://…` resolves in-process, shows only the
`$name` placeholder on argv, and never enters the environment at all. That is the preferred delivery; the
`LoadCredential=` + wrapper-export form below is the fallback, and its residual (the key is readable in
`/proc/<serverpid>/environ` by anything running as `duplicati`) is recorded in §7.3.1's crossings table.

How Duplicati 2.4.0.0 handles the key (verified from `duplicati-server help` and `Duplicati/Server/Program.cs` `GetDatabaseConnection` by the step-2c agent):

- The key is read from the environment variable `SETTINGS_ENCRYPTION_KEY` or the option `--settings-encryption-key` (the option lands on a world-readable command line, so this design uses the environment, populated by the wrapper from the credential file).
- What is encrypted: every option of type *Password* across all modules — the job `passphrase` among them — plus backup `TargetURL`s, JWT/PBKDF configuration and certificate material; the `enc-v1:` prefix embeds a hash of the key, which is how a wrong key is detected (`SettingsEncryptionKeyMismatchException`) and a missing one reported (`SettingsEncryptionKeyMissingException`).
- With no key and an unencrypted database, 2.4.0.0 first tries the OS secret store (libsecret only — `pass` exists solely as an explicit `--secret-provider`) to mint a random key; if none is available it logs "No database encryption key was found. The database will be stored unencrypted." — the message seen on every root-server start before 09-18 21:03.
- **Changing or removing the key**: `ReWriteAllFieldsIfEncryptionChanged` runs at every start. Starting once with the **old** key and `--disable-db-encryption` decrypts every field; starting again with the **new** key (and without the disable flag) re-encrypts them. That two-start sequence is the re-key procedure, and it runs in **§8 P0.5b**, not P1 — the currently
  installed key is public (S-1's successor is the passphrase itself, S-2), so leaving it live "for a week"
  means a week in which the daily snapshot and every recovery copy are decryptable by anyone with the
  repository or the journal. Stop the snapshot timer for the duration: between the two starts every field is
  cleartext on disk, and a 13:45 UTC snapshot landing in that window puts the passphrase in cleartext into
  `~/.local/state` and into the next fileset. Afterwards, with the server stopped, run
  `PRAGMA wal_checkpoint(TRUNCATE); VACUUM;` — the decrypted values otherwise survive in free pages and the
  WAL — and delete the `-<ts>.bak` copy the database tool leaves beside any wiped database.
- **Key lost**: `duplicati-database-tool wipe-encryption <Duplicati-server.sqlite>` clears the encrypted strings so the database opens without the key; the cleared values (`TargetURL`, `passphrase`, the UI password material) must be re-entered.
- A machine-derived default key existed only in canary 2.0.9.105 and was removed in 2.0.9.106; `machineid.txt` and `installation.txt` are identity files for the updater, not key material.

#### 7.3.6 Web UI

**The UI credential is a host-wide read credential, and the design must say so before it says anything
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
  otherwise. **Both** are non-zero, so under `Restart=on-failure` the *success* path loops too, not just the
  failure path — it must never sit in `DAEMON_OPTS`.
  Run it **once, by hand, with the service stopped**, and feed the value through `--secret-provider`
  (a `$name` placeholder on argv) or `--parameters-file`; the server applies both *before* it reads the init
  value. (`--settings-file` is a `duplicati-server-util` option, not a server one — an earlier reading named
  the wrong file channel.)
- Simplest and recommended: **set the first password in the web UI**, and do every later
  pause/resume/rotate through the in-process client `util/ad-hoc/yamaguchi_server_api.py`, which reads its
  credential from a file (§7.6).

`duplicati-server-util`'s own authentication chain, for the record, because two lanes disagreed about it and
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
reason the in-process client is the fix. It also defaults to `--hosturl http://127.0.0.1:8200/` and to
`--server-datafolder=/home/pcalnon/.config/Duplicati/` (the orphaned profile), so every invocation against
this server must name both. The in-process client remains the fix. A recovered database carries the root-era
UI password until it is changed.

**If the root-era UI password is not known, none of the routes above applies** — and this is not a corner
case: Procedures A0, A and A2 all recover a database whose `server-passphrase`/`-salt` hashes survive
(`wipe-encryption` does not clear them, §8 step 6), so the server does **not** consider the password
autogenerated, `--webservice-password-init` refuses it with exit 103, and the argv routes are banned. The
recovery is to clear the stored hash **on the copy, before step 8 installs it**, so the server treats it as
autogenerated again: with the server stopped,
`DELETE FROM Option WHERE BackupID=-2 AND Name IN ('server-passphrase','server-passphrase-salt','server-passphrase-trayicon','server-passphrase-trayicon-hash');`
then `--webservice-password-init` on a single hand start. Without this, P0 step 9 is unreachable for three of
the four procedures, and step 10, AC-2, AC-5, AC-9 and AC-13 all sit behind it.

Remote control and the cloud report URL stay as the owner left them (deferred item) — but the report URL's
bearer JWT is a secret carried by every database copy (S-8).

### 7.4 Destination and permission model

| Path | Owner:group | Mode | Why |
| --- | --- | --- | --- |
| `/mnt/Backups`, `/mnt/Backups/Ubuntu` | `pcalnon:duplicati` | `2750` | traverse for both; setgid keeps the group on new entries |
| `/mnt/Backups/Ubuntu/Dropbox` (Dropbox root) | `pcalnon:duplicati` | `2770` | Dropbox runs as `pcalnon` and must write its own root; the service only traverses (note D-14b) |
| `/mnt/Backups/Ubuntu/Dropbox/Backups` and every subdirectory | `duplicati:duplicati` | `2750` + default ACL `g:duplicati:r-x` | the service owns and writes; `pcalnon` and Dropbox **read** through the group |
| volumes (`duplicati-*.zip.aes`) | `duplicati:duplicati` | `0640` | service `UMask=0027` produces `0640`; Dropbox reads via group and cannot unlink |
| `_yamaguchi_keys/` | `pcalnon:duplicati` | `0700`, the `env` file **0600**, and the folder **copied out of the Dropbox root** then deleted from it on owner sign-off (S-4) | escrow must not sync to the cloud, and must not be group-readable by the service user |

**D-14 is RULED (2026-09-22): the read-only model above is in force** (§10.1). The rejected
alternative — the R-7/R-8 group-write form, directories `2770` and files `0660` — would have granted
**write and delete** on all 877 volumes to every process running as `pcalnon` (editors, browsers,
package hooks, agent sessions) and — by AC-7's own prerequisite — to the Dropbox daemon. A
cloud-side deletion (a compromised account, a linked phone, another machine) or a local `rm -rf`
therefore propagates *into the local master* and on to T1c. R-8 asks only for **read**. The
alternative is directories `duplicati:duplicati 2750`, files `0640`, `UMask=0027`, existing volumes
chowned to `duplicati`: `pcalnon` and Dropbox read through the group, remote→local writes fail
loudly instead of silently deleting the master, and hand maintenance goes through `sudo -u
duplicati` — which this design has already accepted for the data folder. Note honestly what this
buys: `pcalnon` is root-equivalent on this host (`sudo`, `docker`), so it is protection against
**accident and commodity malware**, not against a deliberate local adversary. That limit was stated
before the ruling and the ruling was made with it in view. The script below now implements the
read-only model, and must be run once against the existing tree: it chowns the 877 volumes to
`duplicati` and drops their group-write bit, which is the step that makes a cloud-side delete fail.

Two facts to know before running it on a synced tree: `chmod 0660` strips an executable bit Dropbox has
already synced from **1,784** files — every regular file under `…/Dropbox/Backups` carries one — so it
produces 1,784 metadata updates (bandwidth, not correctness); run it only when `dropbox status` reads up to
date. And ext4's behaviour for
default-ACL creation modes has **not** been verified here: Lane B2's scratch test ran on tmpfs and
showed anomalous setuid/sticky bits on a new subdirectory, so test the `d:g:duplicati:rwX` default
on a scratch directory **on `sda1`** before P2 runs this over the real tree.

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
# D-14 RULED 2026-09-22: the READ-ONLY model. pcalnon and Dropbox read through the group; only
# the service writes. The two mount parents keep 2750, and the Dropbox root keeps 2770 because
# the sync daemon runs as pcalnon and must write its own root -- narrowing that would break sync,
# not harden it. See section 10.1 and note D-14b.
chgrp duplicati /mnt/Backups /mnt/Backups/Ubuntu /mnt/Backups/Ubuntu/Dropbox
chmod 2750 /mnt/Backups /mnt/Backups/Ubuntu
chmod 2770 /mnt/Backups/Ubuntu/Dropbox
# The destination tree passes to the service user. This chown is the step that makes a cloud-side
# or accidental local delete FAIL: unlinking a volume needs write on its directory, and after this
# only duplicati has it.
chown -R duplicati:duplicati "${ROOT}"
find "${ROOT}" -type d -exec chmod 2750 {} +
find "${ROOT}" -type f -exec chmod 0640 {} +
setfacl -R -m g:duplicati:rX -m d:g:duplicati:rX "${ROOT}"
if [[ -d "${ROOT}/_yamaguchi_keys" ]]; then
    # Strip the named ACL entry the recursive setfacl above just applied here. chmod sets the
    # ACL MASK, not the entry, so `g:duplicati:rwX` would survive with an empty mask and any
    # later `chmod g+rx` would silently re-enable the service user's access.
    setfacl -R -b "${ROOT}/_yamaguchi_keys"
    chmod 0700 "${ROOT}/_yamaguchi_keys"
    # The find above set every regular file to 0640; the escrow env must not be group-readable
    # by the service user at all (design section 6, S-4).
    [[ -e "${ROOT}/_yamaguchi_keys/env" ]] && chmod 0600 "${ROOT}/_yamaguchi_keys/env"
    echo "NOTE: ${ROOT}/_yamaguchi_keys is inside the Dropbox root -- copy it out (design §6 S-4)" >&2
fi
echo "done; verify with: getfacl ${ROOT}/Yamaguchi | head; sudo -u duplicati test -w ${ROOT}/Yamaguchi && echo service-can-write"
```

Dropbox prerequisite: the daemon must run with gid 139. After `pcalnon` logs in again (or `newgrp duplicati` in the launching shell), `dropbox stop && dropbox start`, then `grep ^Groups /proc/$(pgrep -x dropbox | head -1)/status` must list `139`. Until then Dropbox can read only files whose `other` bits allow it — which the `0660` model deliberately does not grant.

### 7.5 The job, the Dropbox replica and the pre-backup guard

Job settings are the certified ones (R-16) with **four** changes: `--tempdir=/home/duplicati/.cache/duplicati-tmp`; `--run-script-before-required=/usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash`; `TargetURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi`; and **`--aes-version` pinned explicitly**. The fourth is new and is not cosmetic: the existing 877 volumes are AES Crypt **v2** (newest dlist header bytes `41455302`), whose KDF is the legacy
iterated SHA-256, while 2.4.0.0 defaults to `--aes-version=3` (PBKDF2, `--aes-v3-iterations` 300000). Left unpinned, the first post-recovery run silently changes the on-disk format mid-set. Pin **2** to keep the set homogeneous, or pin 3 and accept a mixed set — in which case AC-4 must drill one pre- and one post-upgrade fileset. This only matters if `PASSPHRASE` is not random: with 32 random characters both KDFs are irrelevant, with a human phrase v2 is GPU-crackable. Record the
passphrase's provenance (generator and length) with the decision. Everything else — sources, 45 filters, AES, `--blocksize=1MB`, `--dblock-size=500MB`, `--no-auto-compact=true`, `retention-policy=1W:1D,1M:1W,1Y:1M,3Y:2M`, `--asynchronous-upload-limit=1`,
`--allow-missing-source=true`, `compression-module=zip`, schedule 14:00 UTC daily — is taken from the 2026-09-20 snapshot.

Rules for a destination that is also a Dropbox-synced folder:

1. Duplicati assumes exclusive control of the destination: any file it did not write is a fatal pre-flight error (`remote files that are not recorded in local storage`, seen 09-16). Nothing else may create, rename or edit anything under `Yamaguchi/`; the folder must never be modified from another Dropbox client or the web UI.
2. The file backend writes each volume **in place under its final name** (streaming `FileCreate` on the target path; no temporary name and rename), and a failed upload attempt is retried under a **new** name, leaving the partial file behind (`RenameFileAfterError` in `Duplicati/Library/Main/Backend/BackendManager.PutOperation.cs`). Dropbox therefore uploads a volume while Duplicati is still writing it and re-uploads it when the write completes — bandwidth, not correctness —
   and a retry can leave a stray that the next run
   reports as a foreign file. Deletions (retention, compaction) propagate as deletions.
3. The guard below refuses to start a backup when the mount is absent, the directory is not writable, the job's `TargetURL` disagrees with the guarded path, or a foreign entry exists. It runs **before** Duplicati touches the destination.
4. Dropbox conflict copies, if they ever appear, must be removed by hand and the run repeated; never run `Repair` to "delete unknown files" without reading what they are (rule 11).
5. Restore from the cloud copy: download `Yamaguchi/` to a scratch directory on a disk with ~250 GB free and run `duplicati-cli restore file:///<scratch>/Yamaguchi <pattern> --restore-path=<dir> --dbpath=<new-temp-db>` with the passphrase supplied through the environment (`PASSPHRASE`, sourced from a 0600 file in a subshell), **never** as `--passphrase=` on argv (local blocks are off by default in 2.4.0.0; never add `--restore-with-local-blocks`); the passphrase comes
   from escrow, never from the same cloud account (S-4).
6. **Write access to `Yamaguchi/` is a backup denial-of-service, not only a correctness risk.** Anyone who can write there — the Dropbox account, any linked device, any `pcalnon` process under the current group model — drops one file and the guard exits 5: no backup runs until a human removes it, and nothing notices for up to 26 h (the watchdog's staleness rule). D-14's read-only model removes the `pcalnon`/Dropbox half of that. Note also that the guard's stray-file check
   *duplicates* a check Duplicati already performs — a foreign file aborts the operation either way, and a file named `duplicati-*.dblock.zip.aes` passes the guard and is caught by Duplicati instead. The guard's real value is the **mount** and **`TargetURL`** checks, which Duplicati does not make.
7. **Cloud→local is a threat direction this design otherwise ignores.** Dropbox version history and Rewind are the *only* recovery from a mass delete of T1 and T1c together, which makes them a design item, not a footnote — and their corollary is that deleted ciphertext stays server-side restorable for the retention window (30 days on Basic/Plus/Family, 180 on Professional), so a "new set under a new passphrase" (D-2) must also **delete-forever** the old one. Retention and
   2FA state are owner observations (D-13's neighbours); this design records that Rewind was **not** evaluated and that Lane B3 dissents from leaving it that way (§11).

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

# Duplicati's RunScript exports EVERY job option into this script's environment, unfiltered and
# prefixed DUPLICATI__ -- the job passphrase among them -- and the wrapper's exported settings
# key is inherited too. Both would then pass to every child (mountpoint, find, id). Drop them
# before anything else runs. (Lane B3 F-4.)
# A DENYLIST CANNOT BE COMPLETE over a set the comment above calls "every job option,
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
# clean slate the word "unset" suggests.
# STDOUT IS NOT A LOG. Duplicati parses a run-script's stdout as OPTION OVERRIDES
# (--option=value lines change the running job). Every message below goes to stderr; never
# add an echo to stdout, and never set -x.

DEST_MOUNT="${YAMAGUCHI_DEST_MOUNT:-/mnt/Backups}"
DEST_DIR="${YAMAGUCHI_DEST_DIR:-/mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi}"
# Duplicati exports the job's remote URL to run-scripts as DUPLICATI__REMOTEURL.
REMOTE_URL="${_keep_url}"
OPERATION="${_keep_op}"

fail() { echo "GUARD(${OPERATION}): $*" >&2; exit 5; }

mountpoint -q "${DEST_MOUNT}" || fail "${DEST_MOUNT} is not a mountpoint"
[[ -d "${DEST_DIR}" ]] || fail "${DEST_DIR} does not exist"
[[ -w "${DEST_DIR}" && -x "${DEST_DIR}" ]] || fail "${DEST_DIR} is not writable by $(id -un)"
if [[ -n "${REMOTE_URL}" ]]; then
    case "${REMOTE_URL%/}" in
        "file://${DEST_DIR}") ;;
        # Print a SHAPE, never the URL. This branch fires exactly when the TargetURL has
        # been changed -- and a non-file:// backend URL routinely embeds credentials
        # (--auth-password is a real option across the Backend assemblies), so echoing it
        # would write a credential into the job log and from there into whatever
        # additional-report-url POSTs (S-8). The guard's own diagnostic must not be the leak.
        *) fail "job TargetURL does not match the guarded destination file://${DEST_DIR}; got scheme='${REMOTE_URL%%:*}' length=${#REMOTE_URL} sha256-8=$(printf '%s' "${REMOTE_URL}" | sha256sum | cut -c1-8)" ;;
    esac
fi
# duplicati-verification.json is allow-listed: the job does not set
# --upload-verification-file today, so the file is not written -- but enabling that option
# later would otherwise make this guard refuse every run. (Lane B2 D19.)
stray="$(find "${DEST_DIR}" -mindepth 1 -maxdepth 1 \
    ! -name 'duplicati-*.dblock.zip.aes' \
    ! -name 'duplicati-*.dindex.zip.aes' \
    ! -name 'duplicati-*.dlist.zip.aes' \
    ! -name 'duplicati-verification.json' \
    -print -quit)"
# The stray's NAME is attacker-chosen and reaches the job log; sanitise it to a character
# class so it cannot inject newlines or control sequences (open item O-13 asks whether
# SendStdOutToLogs stores stderr verbatim -- this makes the answer not matter).
[[ -z "${stray}" ]] || fail "foreign entry in destination, name sanitised: $(printf '%s' "${stray##*/}" | LC_ALL=C tr -cd 'A-Za-z0-9._-' | cut -c1-64)"
exit 0
```

Contract, verified against `Duplicati/Library/Modules/Builtin/RunScript.cs` (lines 385–448 at the 2.4.0.0 tag) and `duplicati-cli help run-script-before-required` — the vendor's own `/usr/lib/duplicati/run-script-example.sh` states the opposite mapping for both forms and is wrong against the source, so do not cite it: for `--run-script-before-required` any non-zero exit or a timeout aborts the operation; for plain `--run-script-before` exit codes 0, 2 and 4 let the operation
run and 1, 3 and 5 stop it (2/3 log a warning, 4/5 an error). The variables the example script documents include `DUPLICATI__OPERATIONNAME`, `DUPLICATI__REMOTEURL`,
`DUPLICATI__LOCALPATH`, `DUPLICATI__EVENTNAME`, `DUPLICATI__PARSED_RESULT` and `DUPLICATI__RESULTFILE` — but the set is **not** limited to those: `RunScript.cs` exports every job option (`foreach (kv in options) psi.EnvironmentVariables["DUPLICATI__" + …] = kv.Value`), which is why the guard's first statement unsets the two that are secrets. The vendor's own `/usr/lib/duplicati/run-script-example.sh` says the same at its line 75, and at line 85 documents the other half:
**a run-script's stdout is read back as option overrides.** `--run-script-timeout` defaults to 60 s; the guard above finishes in well under a second.

Two properties of the guard as written, stated so nobody has to re-derive them: the `TargetURL` comparison is
an exact match against `file://${DEST_DIR}`, so it **fails closed** on a trailing slash or a query-string
variant (acceptable, and deliberate); and `find -P … -maxdepth 1` does not follow symlinks, so a symlinked
stray is reported, not traversed. The stray file's *name* reaches the job log through stderr, so a
deliberately named file could otherwise inject newlines into that log. Both the stray-file **name** and the
job's **`TargetURL`** are attacker-influenced strings, and a non-`file://` `TargetURL` can carry an
`auth-password` in the URL itself — so the guard prints a scheme, a length and a sha256 prefix for the URL,
and a character-class-sanitised basename for the stray. Open item O-13 (does `SendStdOutToLogs` store stderr
verbatim, and does the option-override parser see it?) stays open, but the guard no longer depends on its
answer.

### 7.6 Alerting

- **Service level**: `OnFailure=duplicati-failure.service` is added to `duplicati.service` once a reporter exists for the system scope (the user-lane reporter `util/duplicati_backup_failure.bash` is the template; it writes a durable record first and notifies second).
- **Watchdog** (`util/ad-hoc/yamaguchi_watchdog.py`, user timer 12:00): read the UI credential from `~/.config/duplicati-backup/web-credential` (a file the operator rotates, instead of the primary checkout's `.env`); add the `ProgramState`/`SchedulerQueueIds` check from YAM §8.22 (`Paused` with a non-empty queue = fault); anchor freshness on the newest **Backup** operation, not any operation; add a Dropbox check (`dropbox filestatus` of the newest dlist must read `up to
  date` within 24 h); keep the 26 h staleness rule and the desktop notification as best-effort.
- **One credential path, in both clients, in the same PR.** `util/ad-hoc/yamaguchi_server_api.py:41` hard-codes `CRED_FILE` to the primary checkout's `.env`, and `util/ad-hoc/duplicati_api.py`'s `PW_FILE` defaults to the same file; `util/ad-hoc/yamaguchi_reboot_verify.bash:73` calls the first and the census goes through the second. Re-pointing only one of them leaves every acceptance instrument 401-ing after the password rotates — which is exactly today's watchdog symptom.
  Both move to `~/.config/duplicati-backup/web-credential`, and P0 is ordered so that file exists **before** AC-2 runs.
- **The deployed watchdog unit takes no `--backup-id`**, so it uses the client's default of 2. If recovery assigns the job a different id (Procedure B always does — `sqlite_sequence` starts at 1), the unit must be redeployed with `--backup-id <id>` or it alerts `JOB_MISSING` forever.
- **Deployment**: the watchdog unit keeps executing the primary checkout's script until the arc's own item (`HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §1.6) converts it to an installed copy; that conversion belongs to P2 — with the same integrity argument as the snapshot timer in §7.7.

### 7.7 The server-DB snapshot lane

`util/ad-hoc/yamaguchi_server_db_snapshot.py` keeps `SRC = /usr/lib/duplicati/data/Duplicati-server.sqlite`.
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
only, since it already runs as `pcalnon`).

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

**`PathExists=` cannot be used here, and this is the defect `systemd-analyze verify` cannot see.**
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
for 30 s. `/run/media/pcalnon` exists, `root:root` **0750** with a named ACL entry `user:pcalnon:r-x`, and is
currently empty — the `r-x` is exactly what a `--user` path unit needs to place its inotify watch, and
`pcalnon` deliberately has no write there because udisks2 owns the directory. One thing to know before the
first post-reboot trigger is read: **`/run` is tmpfs**, so `/run/media/pcalnon` does not survive a reboot and
is re-created by udisks2. A systemd path unit handles a missing path by watching the nearest existing
ancestor, so the unit still works — but a reader who assumes the directory is permanent will misread that
first trigger.

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
```

The failure reporter must be a **new** unit. `duplicati-backup-failure.service` exists, but its `ExecStart`
is `duplicati-backup-failure.bash duplicati-backup.service` — it journal-tails the *disabled CLI lane* and
writes a `failures.log` record naming the wrong unit, so pointing T2's `OnFailure=` at it produces a report
about a lane that is not running. P3 adds `juniper-backup-failure.service`, whose reporter takes the unit name
as `$1` (defaulting to `duplicati-backup.service` so the existing lane is unaffected).

```ini
# file: home/pcalnon/.config/systemd/user/juniper-backup.service
[Unit]
Description=Juniper per-repo archive to attached USB drives
OnFailure=juniper-backup-failure.service

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

Installation follows the *pattern* of `util/install_duplicati_timer.bash` but needs its own script —
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
`HANDOFF_2026-08-27_backup-per-repo-review-and-arc-tail.md` §7) is D-10.

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

`/usr/lib/duplicati/data/` (archive a copy, then remove, once AC-1…AC-4 pass); `/home/duplicati/.config/Duplicati/{temp,temp1,backups}` (56 GiB of copied pcalnon job databases — the originals in the pcalnon profile stay under the record's KEEP list); `Duplicati-OLE/` (unreadable to the investigators — owner to inspect); the disabled user CLI lane (the record's own removal item); the `.env` comment block; the wrapper's header comment; `/home/duplicati/bin/` entirely
(it holds only the symlink D-6 replaces with an installed copy — a "fallback" symlink into a developer checkout should not exist); and **`/mnt/Backups/Ubuntu/.dropbox-dist`**, a second, unused Dropbox client (270.4.3312) owned `duplicati:duplicati` that nothing runs — the live daemons are pcalnon's.

---

## 8. Remediation plan

**Ten paths are named below; nine are landed and one is not.** Landed, and byte-identical to their tagged
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
second.

Phases are ordered; nothing in a later phase is a precondition of an earlier one — **but that is true of
phases, not of decisions**. That distinction mattered while the gates were open; **they were ruled on
2026-09-22 and §10.1 records them**, so P0 now applies decisions rather than recommendations: D-1
(credstore + `--require-db-encryption-key`), D-4 (`AmbientCapabilities`), D-6 (installed copy **plus the
drift gate**), D-9 (loopback) and D-14 (the §7.3.2 unit now sets `UMask=0027`, the ruled read-only value).
**D-2 no longer forces a choice at this point.** It was ruled *rotate and keep*, and §10.2 sequences the
rotation to run **after** the recovery is complete and drill-verified — so P0 step 11's full backup is
written under the current passphrase deliberately, not by default, and is re-encrypted later rather than
discarded. Step 0 verifies the artifacts match §10.1 instead of asking for a decision.

Every destructive step is preceded by a copy. **Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved by
any step below, with exactly one exception, and it needs owner sign-off**: the passphrase escrow copy at
`…/Dropbox/Backups/_yamaguchi_keys/`, which P1 step 4 first **copies** to a sibling outside the Dropbox root
and only then deletes from the synced tree (S-4). The earlier revision of this preamble stated the rule
without the exception while P1 step 4 performed it — a contradiction inside one document. The pcalnon profile
directory is not modified by anything here.

### P0 — freeze and recover the job (target: same day)

**Run P0.5a items 1 and 2 before anything in P0.** They take minutes, depend on nothing in the recovery, and
item 1 closes the path by which the service user controls the very binaries steps 0(c), 3, 4 and 7 execute.
P0.5 is printed *after* P0 only because it also carries work that follows the recovery; an operator working
top to bottom would otherwise run the recovery with that path open.

**0. Owner gates — RULED 2026-09-22 (§10.1); this step is now a verification, not a decision.** (a) Confirm the
installed artifacts match the rulings: `UMask=0027` in the unit (D-14), `AmbientCapabilities=CAP_DAC_READ_SEARCH`
with the §7.3.2 confinement set (D-4), `--webservice-interface=loopback` (D-9),
`--require-db-encryption-key` (D-1), and a `.blessed.sha256` written by the installer (D-6). D-2's rotation is
**not** part of P0 — it runs after recovery, per §10.2. (b) Have the escrowed `PASSPHRASE` to hand, from the printed
sheet or the password manager — **not** from the Dropbox-synced copy, which is the thing S-4 is about. (c)
Confirm Procedure A0's premise with the read-only script below. **Run P0 step 1's freeze first** — it
needs the job index that step copies aside, because it points `--dbpath` at a throwaway copy of it rather
than using `--no-local-db`, which on this destination rebuilds the index from all 877 dindex volumes
(`util/ad-hoc/duplicati_drill_run.py`: ">30 minutes for a single small file here, without completing"). The
passphrase is **parsed** out of the credential file, never `.`-sourced, and never touches argv:

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
    m = re.match(r"^\s*(?:export\s+)?PASSPHRASE=(.*)$", line.rstrip("\n"))
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
```

The 09-18 14:00Z fileset **is** version 0 (it is the newest), which is why `--version=0` is used rather than
a `--time=` string whose parsing would be one more thing to get wrong — **but that is true only until the
first post-recovery backup runs**, after which version 0 is the new one. Assert the expected dlist name
before relying on it. Expect the snapshot path
`home/pcalnon/.local/state/duplicati-server-db/Duplicati-server.sqlite` in the listing. If it is absent, A0
is out and the decision tree starts at step 3.

One expected value to know in advance, because it will otherwise look like a failure: the snapshot **inside**
the 09-18 14:00Z fileset was taken at 13:45 UTC, *before* that day's backup, so its `LastBackupDate` reads
**`20260917T140000Z`**, not `20260918T140000Z`. (Appendix A.2's `20260918T140000Z` is the 09-20 on-disk
snapshot, a different file.) "Only `LastBackupDate` is one day stale" is measured from the 09-18 run.

1. **Freeze evidence.** `sudo cp -a /usr/lib/duplicati/data /home/duplicati/.cache/root-data-folder-2026-09-22`, and copy the snapshot aside **before anything else touches it** — `cp -p ~/.local/state/duplicati-server-db/Duplicati-server.sqlite ~/.local/state/duplicati-server-db/Duplicati-server.sqlite.recovery-$(date +%F)`. That file is **replaced every day at 13:45 UTC with a new inode**; if the timer fires mid-recovery the file under your hand changes.
   Verify sizes match. While root is available, settle two open questions with one listing each: `sudo ls -la --time-style=full-iso /usr/lib/duplicati/data/` — a `-wal`/`-shm` dated 09-18 21:03 means the main file may still be **cleartext**, a second key-free source (§4.2, §5.4) — and `sudo ls -la /usr/lib/systemd/system/ | grep -i duplicati` for editor backups of the unit.
2. **Stop the empty server**: `sudo systemctl stop duplicati.service` (stop, **never** restart — the armed `ExecStart` cannot start the server correctly and the 0700 gate refuses the 0777 folder regardless, §4.3 item 9). Move the fresh, empty data folder aside: `sudo mv /home/duplicati/.config/Duplicati /home/duplicati/.config/Duplicati.empty-2026-09-20`. Note that this folder is 0777 and 2.4.0.0 would refuse it, so it cannot simply be reused in place.
3. **Choose the procedure — the offline key-hash test is the discriminator, not a server probe.** Every `enc-v1:` value embeds the SHA-256 of its key, so run `util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py` against the **data-folder freeze** from step 1. It takes three argument groups — a wrapper path, a `.env` path, then one or more `label=path` database specs — and reads a candidate `.env` on **stdin**, so the invocation is:

   ```text
   sudo cat <candidate-file> | sudo python3 util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py \
       scripts/duplicati-wrapper.bash ~/.config/duplicati-backup/env \
       frozen=/home/duplicati/.cache/root-data-folder-2026-09-22/Duplicati-server.sqlite
   ```

   It needs **root** — the freeze lives under `/home/duplicati/.cache`, mode 0700 `duplicati` — but no server and no live database, and it has already excluded every candidate this design named (§5.4): the committed literal with eleven shell-mangling variants, both passphrases, and the three commented key spellings. **A new candidate must be written as a `SETTINGS_ENCRYPTION_KEY=<value>` line, not as a bare value**: stdin is parsed as a `.env`,
   so a bare-value file loads **no** candidate and prints a vacuous `NONE of the candidates/variants`. Feed it alone — only the **last** uncommented `SETTINGS_ENCRYPTION_KEY=` line survives. Write it with `set +o history; read -rs key; printf 'SETTINGS_ENCRYPTION_KEY=%s\n' "$key" | sudo install -m 0600 /dev/stdin <file>; unset key` — **never** `printf '%s' '<value>' > file` at a root prompt, which is the same history channel §6 exists to close.
   If no candidate matches (the expected outcome today), go to **step 4 (A0)**; A0 is preferred over A2 and B even if a key *is* found, because it is the only route that needs no re-entry of anything.

   If you reach for `duplicati-server-util` at any point in this step, note that its 0700-gate refusal is **completely silent** — exit 1, zero bytes on stdout *and* stderr, before even the "Connecting to…" line (§5.5). A silent exit 1 there is a permissions problem, not a missing server.

   A server-based probe is **confirmation only**, and only with all four containments below — as written in an earlier revision it could report `KEY ACCEPTED` for a **wrong** key, because it copied the main file without its `-wal` and `Program.cs` re-encrypts a not-yet-encrypted copy under whatever key it is started with, printing `Server has started` either way:

```bash
# file: util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash
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
# Default to the P0 step 1 DATA-FOLDER FREEZE, not the live folder: the step that introduces
# this script says "the copy from step 1", and a default pointing at /usr/lib/duplicati/data
# would silently re-copy from the original instead.
SRCDIR="${SRCDIR:-/home/duplicati/.cache/root-data-folder-2026-09-22}"
WORK="${WORK:-/home/duplicati/.cache/keyprobe}"
PORT="${PORT:-8399}"
KEYFILE="${1:?usage: $0 <file-containing-candidate-key>}"
[[ "$(id -u)" -eq 0 ]] || { echo "run with sudo" >&2; exit 2; }
# sqlite3 is NOT installed on this host by default. Without it the two containment queries
# below return EMPTY, and the refusal then misreports a query failure as "the copy is
# cleartext" -- which sections 4.2, 5.4 and 11 have primed the operator to read as "the second
# key-free recovery source has been found". Fail loudly instead.
command -v sqlite3 > /dev/null || {
    echo "sqlite3 is not installed; containments (2) and (4) cannot run. Install it first." >&2
    exit 2
}
[[ -s "${SRCDIR}/Duplicati-server.sqlite" ]] || { echo "source DB missing under ${SRCDIR}" >&2; exit 2; }

rm -rf "${WORK}"; install -d -m 0700 -o duplicati -g duplicati "${WORK}"
# (1) main file PLUS its siblings.
for f in Duplicati-server.sqlite Duplicati-server.sqlite-wal Duplicati-server.sqlite-shm; do
    [[ -e "${SRCDIR}/${f}" ]] && cp -p "${SRCDIR}/${f}" "${WORK}/${f}"
done
chown -R duplicati:duplicati "${WORK}"

# (2) the copy must already be encrypted, or a "pass" means nothing.
flag="$(sqlite3 "file:${WORK}/Duplicati-server.sqlite?mode=ro" \
    "SELECT Value FROM Option WHERE BackupID=-2 AND Name='encrypted-fields';" || true)"
url="$(sqlite3 "file:${WORK}/Duplicati-server.sqlite?mode=ro" \
    "SELECT substr(TargetURL,1,7) FROM Backup LIMIT 1;" || true)"
if [[ "${flag}" != "True" || "${url}" != "enc-v1:" ]]; then
    echo "REFUSING: the copy does not read as encrypted (encrypted-fields='${flag}', TargetURL prefix='${url}')." >&2
    echo "EMPTY values mean the QUERY failed, not that the copy is cleartext -- check the copy." >&2
    echo "A probe against a genuinely unencrypted copy accepts ANY key and poisons the copy." >&2
    exit 3
fi
# (4) a schedule in the past would otherwise let the probe server start the overdue run.
sqlite3 "${WORK}/Duplicati-server.sqlite" "DELETE FROM Schedule;"

# The key is delivered by a 0600 EnvironmentFile, NEVER on argv: `-p Environment=<secret>` is
# world-readable in /proc/*/cmdline and is recorded by systemd -- the same exposure 7.3.6 bans
# for `duplicati-server-util --password`. (A `SETTINGS_ENCRYPTION_KEY=` prefix on `timeout`
# would also be dead: a transient unit does not inherit the caller's environment.)
try_key() {
    local key="$1" label="$2" log="${WORK}/probe-${2}.log" envf="${WORK}/probe-${2}.env" rc=0
    printf 'probing: %s\n' "${label}" >&2
    ( umask 077; printf 'SETTINGS_ENCRYPTION_KEY=%s\n' "${key}" > "${envf}" )
    chown duplicati:duplicati "${envf}"
    set +e
    timeout -k 10 90 \
        systemd-run --wait --quiet --collect --pipe \
            --uid=duplicati \
            -p InaccessiblePaths=/mnt/Backups \
            -p InaccessiblePaths="${SRCDIR}" \
            -p "EnvironmentFile=${envf}" \
            /usr/bin/duplicati-server "--server-datafolder=${WORK}" \
            --webservice-interface=loopback "--webservice-port=${PORT}" \
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
if try_key "$(head -c 32 /dev/urandom | base64 | tr -d '\n')" control; then
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

   The 90 s timeout ends the probe server (`timeout -k 10 90` — raised from 45 s because a cold .NET start under `systemd-run` can exceed it, and a timeout that fires early is indistinguishable from a rejected key unless `try_key` is careful, which is why it now reports `INDETERMINATE`); the `DELETE FROM Schedule` and the two `InaccessiblePaths=`
   keep it from reaching anything real even so. (`startup-delay` **is** present by name among the server
   settings at `BackupID=-2`, but its *value* is not verifiable without opening the database, so it is not
   relied on — an unverified pause is not a containment.)

4. **Procedure A0 — restore a cleartext copy of the same database from the backup itself. This is the
   preferred route and it needs no settings key at all.** The snapshot lane writes into
   `~/.local/state/duplicati-server-db/`, which is inside the backup Source and matched by none of the
   filters (`JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md` §8.19.3 verified this against the **44** filters of that date; the job carries 45 today, and the one added since does not cover `.local/state/` either), and the root database was still **unencrypted** through 09-18 20:42:38 (three
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
    m = re.match(r"^\s*(?:export\s+)?PASSPHRASE=(.*)$", line.rstrip("\n"))
    if m and m.group(1).strip():
        sys.stdout.write(m.group(1).strip().strip('"').strip("'"))
        break
else:
    sys.exit("FATAL: no PASSPHRASE in " + sys.argv[1])
PY
)"
[[ -n "${PASSPHRASE}" ]] || { echo "no PASSPHRASE parsed from ${ENV_FILE}" >&2; exit 2; }
export PASSPHRASE
duplicati-cli restore "${DEST}" "${SNAP_PATH}" \
    --version=0 "--dbpath=${TMPDB}" "--restore-path=${OUT}"
unset PASSPHRASE
rm -f "${TMPDB}" "${TMPDB}-wal" "${TMPDB}-shm" "${TMPDB}-journal"
echo "restored under ${OUT}; verify it with the forensics script before installing it."
echo "SHRED ${OUT} once step 8 has installed the database -- it is cleartext key material."
```

   Verify the restored file with the forensics script before installing it: 16 server tables, `Version 11`,
   `Backup` id 2 `Yamaguchi`, 2 `Source` rows, 45 `Filter` rows, and a **cleartext** `TargetURL` (no
   `enc-v1:` prefix). Then install it as the data folder per step 8 — and afterwards **shred the restore
   directory**: `sudo find <restore-dir> -type f -exec shred -u {} + && sudo rmdir <restore-dir>`. Nothing
   later in this plan removes it, and until it is gone it is a cleartext copy of the passphrase on disk, which
   is the sink class §6's checklist exists to enumerate. The script refuses a restore path under
   `/home/pcalnon/` for the same reason: that is the backup Source, and a restore into it would archive the
   cleartext database on the next run (the S-7 shape).
5. **Procedure A — re-use the whole data folder (only if step 3 found a key).** `sudo cp -a /usr/lib/duplicati/data /home/duplicati/.config/Duplicati`; `sudo chown -R duplicati:duplicati /home/duplicati/.config/Duplicati`; `chmod 0700` on the folder and `0600` on its files (§7.3.2); write the accepted key to `/etc/credstore/duplicati-settings-key` (0600 root) **and leave it there until P0.5b's re-key replaces it** — the earlier "for the first start only" would
   re-create the 09-18 `SettingsEncryptionKeyMissingException` loop on the very next restart. Then step 8.
6. **Procedure A2 — wipe the encrypted fields, keep everything else.** On the **copy** from step 1, as the copy's owner, in a 0700 directory:
   `duplicati-database-tool wipe-encryption --server-datafolder <copydir> --dry-run <copydir>/Duplicati-server.sqlite` first (expect `version 11 … Server database … 9 encrypted field(s) would be wiped`), then the same without `--dry-run`. Three traps. First, one §5.5 measures and §8 must not leave implicit:
   `duplicati-database-tool` does **not** apply the 0700 data-folder gate at all — it resolves the folder in
   `ProbeOnly` mode — so a clean run here is **no** evidence that the copy's folder is acceptable to the
   *server*; step 8's `install -d -m 0700` is what makes it so. Second, `--server-datafolder <dir>` **is** an option of the *subcommand* (`duplicati-database-tool help wipe-encryption`) even though the top-level `help` does not list it, and it defaults to
   `$HOME/.config/Duplicati` — i.e. the orphaned pcalnon profile when run as `pcalnon`, so **always name the copy's folder**; and `--dry-run` is **not read-only** — it flips the copy's header to WAL mode and changes its sha256, so hash the copy before, or re-copy after. What is cleared: `Backup.TargetURL`, `Source.Path`, `ConnectionString.BaseUrl`, `BackupTargetUrl.TargetURL` and password-typed `Option.Value` (the job `passphrase`, `jwt-config`, `pbkdf-config`,
   `remote-control-config`, ssl cert fields, `client-license-key`). The tool leaves a `-<ts>.bak` beside the database (delete it — it still holds the encrypted values) and refuses a non-server database. `Source` rows in the snapshot are cleartext, so sources survive; `server-passphrase`/`-salt` are **hashes** and not in the wipe list, so the **UI password survives** and "set the UI password afresh" is optional, not required.
   Re-enter the two values that matter — `TargetURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi` and the passphrase — through the **web UI** or `util/ad-hoc/yamaguchi_build_job.py`, which reads the passphrase in-process; never a `curl -X PUT` that puts the passphrase on argv. Then step 8.
7. **Procedure B — rebuild the job through the API.** Start the empty server with the §7.3 unit and a **new** settings key, in a data folder created `0700 duplicati:duplicati` (the one moved aside in step 2 is 0777 and 2.4.0.0 refuses it); set the UI password through the web UI; rebuild the job from the snapshot — sources, filters, schedule and option names are readable in it (`2026-09-21_duplicati_server_db_forensics.py` prints them; option *values* come from
   the record, §7.5), `TargetURL` as above, passphrase from `~/.config/duplicati-backup/env` (`util/ad-hoc/yamaguchi_build_job.py` built the job the first time and reads the passphrase in-process; update its defaults before use). **The rebuilt job is not id 2**: `sqlite_sequence` starts at 1, and the deployed watchdog, `yamaguchi_census.py`, AC-2 and AC-5 all default to 2 (step 9 already takes `--backup-id <id>` explicitly). Record the assigned id and pass it explicitly everywhere, including
   `--backup-id <id>` on the redeployed watchdog unit. State in the rebuild whether it re-creates `additional-report-url`; if it does, that bearer JWT is a secret (S-8).
8. **Common to A0, A, A2 and B — place the database, move the index, re-point `DBPath`, all BEFORE the first run.** **First, place the recovered database.** A0 and A2 produce a *file*, not a folder; Procedure A produced the folder in step 5 and B created one in step 7. For **A0** and **A2**:

   ```text
   sudo install -d -m 0700 -o duplicati -g duplicati /home/duplicati/.config/Duplicati
   sudo install -m 0600 -o duplicati -g duplicati \
        <recovered>/Duplicati-server.sqlite /home/duplicati/.config/Duplicati/Duplicati-server.sqlite
   ```

   `<recovered>` is the A0 restore path (step 4) or the wiped copy (step 6). Do **not** copy a `-wal`/`-shm`
   sibling alongside it: the recovered file is a clean, closed database, and a stale WAL from another process
   would be replayed over it. Verify with the forensics script *after* the copy, as the `duplicati` user.
   Without this, A0 and A2 end with the recovered database still in a scratch directory and the server
   starting against the empty folder the installer created — `0 backups`, exactly where the arc began. The snapshot's `Backup` row carries `DBPath=/usr/lib/duplicati/data/BMXWPAOGLP.sqlite`, an **absolute** path, and `RestConnection.cs`'s `ResolveDbPath` returns a rooted path unchanged — the server never relocates it. The §7.3.2 unit makes `/usr/lib/duplicati` read-only and P4 deletes it, so a procedure that skips this fails its first backup read-only and then
   loses the index. So: stop the server, `cp` `BMXWPAOGLP.sqlite` into the new data folder (`chown duplicati`, `0600`), and update the row — UI **Database → Placement → Save**, or `PUT /api/v1/backup/<id>` — after which 2.4.0.0 stores it *relative* (`GetRelativeDbPath`). Install §7.3 (unit, defaults, wrapper, guard) with
   **`sudo bash util/install_duplicati_service.bash`** — through `bash`, not directly. Every script this
   document landed was committed through GitHub's `createCommitOnBranch` API, which **carries no file
   mode**, so each arrives `100644` and is not executable whatever the working tree said. That is a
   property of any API-signed commit, not a one-off to fix: the next one lands the same way. Then
   `sudo systemctl start duplicati.service`. Expect in the journal: schema upgrade 11→12 and
   `Server has started`. The job appears with its existing index — no Recreate. For Procedure B, run **Verify files** before any backup; if verification reports the index inconsistent with the destination, run Repair (this index *is* the destination's own, last written 09-18, so rule 11 does not apply) or, last resort, Recreate.
9. **Re-arm alerting FIRST — every command in step 10 goes through the API client.** Set the UI password (§7.3.6, and read its "if the root-era password is unknown" paragraph *before* you need it), write `~/.config/duplicati-backup/web-credential` (0600), and re-point **both** API clients at it (§7.6). `util/ad-hoc/yamaguchi_server_api.py:41` hard-codes the primary checkout's `.env`, whose value §6 S-5 records as stale, so a run order that pauses the
   scheduler first and creates the credential afterwards makes step 10's `pause` 401 — and `resume` is what fires the overdue backup. Land the client changes (the credential path **and** the new `pause`/`resume` subcommands) in the same PR as §7.6's re-pointing, before P0 runs. Redeploy the watchdog with `--backup-id <id>`; confirm the next 12:00 fire reads `OK`.
10. **Before the first run.** The job still carries `--tempdir=/home/pcalnon/.cache/duplicati-tmp` (unwritable under the new confinement) and its schedule `Time` is in the past, so it will start on its own once the startup pause lapses. Immediately after the server is up: **sample the scheduler state before touching it** — `GET /api/v1/serverstate`, recording `ProgramState`, `paused-until` and `SchedulerQueueIds` — then `pause`, change `--tempdir` to
   `/home/duplicati/.cache/duplicati-tmp` (create it, 0700 duplicati), add `--run-script-before-required` (§7.5), then `resume` and **sample `serverstate` again** (the credential this needs was created in step 9). This is the 2026-08-30 stuck-pause class (`HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §1.7, YAM §8.22–§8.23): a first start under changed `DAEMON_OPTS` followed by pause/resume is the exact untested sequence that produced a 42.6 h silent outage, and without the two samples a
   recurrence is invisible. Pause and resume go through `util/ad-hoc/yamaguchi_server_api.py` (extended with `pause`/`resume`), **not** `duplicati-server-util`, which takes its secrets on argv. Before `resume`, dry-run the guard as the service user, with `env` rather than a bare `VAR=value` prefix (sudoers refuses the prefix under the default `env_reset` with no `setenv`) and with the URL read **from the job** rather than typed:

   ```text
   sudo -u duplicati env \
     DUPLICATI__REMOTEURL="$(python3 util/ad-hoc/yamaguchi_server_api.py export <id> \
       | python3 -c 'import json,sys; print(json.load(sys.stdin)["Backup"]["TargetURL"])')" \
     /usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash; echo "guard exit=$?"
   ```

   Require exit 0: it is `--run-script-before-**required**`, so a missing or failing guard aborts the first backup, which `resume` fires immediately. A **hand-typed** URL would make the guard's `TargetURL` comparison compare the operator's own string with itself — vacuous, and it is the one check §7.5 item 6 says the guard exists for.
11. **Prove it.** `AC-2`, then one backup run (`AC-3`), then the two restore drills (`AC-4`), then `AC-12` and `AC-13`. `AC-6` cannot be proved here — it becomes provable only when the snapshot lane is re-pointed (P0.5a item 2), and `AC-1` needs 24 h.

### P0.5a — before anything in P0 (minutes; depends on nothing)

Items 1, 2, 4, 5, 6 and 7 below. These were scattered across P1, P2 and P4 while the recovered server ran for
days with the holes open. None touches the recovery, each takes minutes, and item 1 closes the path by which
the service user controls the very binaries P0 steps 0(c), 3, 4 and 7 execute.

**Item 3 is not one of them** — see P0.5b at the end of this list. An earlier revision put all six under one
heading that claimed "none of it depends on the recovery", which is true of five and false of the one that
closes S-1 and S-2.

1. **Return `/usr/lib/duplicati` to `root:root`, `data/` excepted** (it is the frozen copy until P4) — **before P0 step 0(c), which is the first command that executes a Duplicati binary**. `/usr/bin/duplicati-*` are symlinks into a `duplicati:duplicati` 0755 directory with no sticky bit, so the service user can rename any entry aside and drop in its own `duplicati-cli`, `duplicati-database-tool` or `duplicati-server` — all of which root and `pcalnon`
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
   D-6 replaces with an installed copy.
2. **Install the snapshot timer's script as a root-owned copy** under `/usr/local/lib/duplicati/` and add `ProtectSystem=strict` to `yamaguchi-server-db-snapshot.service`. It runs as **root** today with `ExecStart` naming the primary checkout, so `sys.path[0]` is pcalnon-writable and every branch switch changes what root executes at 13:45 UTC (§7.7). In the **same installed copy**, re-point `SRC` to
   `/home/duplicati/.config/Duplicati/Duplicati-server.sqlite`, and **stop the timer** (`systemctl stop yamaguchi-server-db-snapshot.timer`) until P0 step 8 has placed the recovered database; restart it only then. Leaving it pointed at `/usr/lib/duplicati/data` means every 13:45 UTC fire copies the **abandoned** database — the one encrypted under the unidentified 09-18 key — over `~/.local/state/duplicati-server-db/` and into the 14:00 UTC fileset, which
   silently destroys Procedure A0's own source for any later re-run and makes AC-6 unprovable until P2. Note also that after this step the unit no longer executes the repository file, so a later repository edit plus `daemon-reload` changes nothing: move changes into production by re-running the installer.
3. **Moved to P0.5b — do NOT run this here.** The re-key runs the server against the *recovered* data folder, so it cannot precede P0 step 8; the procedure is in P0.5b below. The number is kept so that §6's S-2 row, §7.3.5 and P1 step 1 still land on something.
4. **Scrub both log stores** — `/var/log/syslog*` *and* the journal, in that order (§6, D-8) — and verify with `sudo ls -la /var/log/syslog-2026092*`. A journal-only scrub leaves an identical copy behind.
5. **Handle S-7 and S-4.** Remove the world-readable `.env` inside `…/worktrees/curious-plotting-hummingbird/` after the fingerprint reconciliation (the file only — that worktree is do-not-sweep), `chmod 0600` the escrow `env`, and start the S-4 copy-out. The Dropbox "delete forever" and account audit are owner actions.
6. **Close the detection gap**: enable `secret_scanning_non_provider_patterns`, add a gitleaks **content** rule for `(SETTINGS_ENCRYPTION_KEY|PASSPHRASE(_OLD)?|DUPLICATI_WEB_CREDENTIAL|webservice-password|passphrase)=` with a non-placeholder value, and add a gitleaks pre-commit hook. The repository's current rule cannot match a value containing `* @ $ %`, which is why both PRs passed; CI runs gitleaks only *after* publication.
7. **`usermod -s /usr/sbin/nologin duplicati`** (moved here from P4, which no longer performs it). While a `duplicati`-uid shell exists outside the unit, §7.3.2's mount mask can be escaped through `/proc/<pid>/root`, so every such session is a hole in `InaccessiblePaths=` for as long as it lives. Do this **after** the two live `su - duplicati` shells in §6's sink checklist have been closed per their own row — closing those is the owner's time-critical action; this makes
   the next one impossible.

### P0.5b — immediately after P0 step 8, same session

**Item 3 (the re-key) only.** It runs the server against the **recovered** data folder, so it cannot precede
the recovery: stop the snapshot timer, do the two-start re-key back to back, then
`PRAGMA wal_checkpoint(TRUNCATE); VACUUM;` with the server stopped, then restart the timer (§7.3.5). This is
the item that closes S-1 and S-2, so it is not deferrable to P1 — but it is also not runnable before step 8.

### P1 — secrets (same week)

1. *(Executed in P0.5b — kept here as the procedure of record.)* Generate a new settings key (`umask 077; openssl rand -base64 48 | tr -d '\n' > /etc/credstore/duplicati-settings-key`), then re-key the database in two starts: first with the **old** key still in the credential file and `--disable-db-encryption` appended to `DAEMON_OPTS` (every field is decrypted on that start), then with the new key in the credential file and the flag removed (every field is
   re-encrypted; add `--require-db-encryption-key` at this point). Stop the snapshot timer across both starts and `VACUUM` afterwards (§7.3.5). Escrow the new key with the passphrases (printed, password manager, machine-local copy outside the Dropbox root).
2. Delete the five commented lines from `.env`; set it to the §7.3.5 contract. **Mode: `0640 root:duplicati` as recommended, or `0600 duplicati:duplicati` — this is the open dissent recorded in §11**; install the stricter form until the owner rules.
3. *(**Executed in-tree**, pending merge: `scripts/duplicati-wrapper.bash` has been replaced by §7.3.3's wrapper v2 and carries no credential-shaped literal — its one `SETTINGS_ENCRYPTION_KEY=` is the legitimate `export` of a variable. Verify with `grep -c 'Environment=SETTINGS' scripts/duplicati-wrapper.bash` = 0, which is AC-8's own check.)* Remove the commented "Old Unit file" block from `scripts/duplicati-wrapper.bash`. **The exposure in `main`'s git
   history is untouched by this and stays untouched** — the key is dead, and S-1 records why a history rewrite is not worth its cost.
4. **Copy** `_yamaguchi_keys/` out of the Dropbox root — `cp -a` to `/mnt/Backups/Ubuntu/_yamaguchi_keys/`, a sibling of `Dropbox/` — verify sha256 on both sides, and delete the in-tree copy **only on owner sign-off** (this is the single exception to the "nothing under `/mnt/Backups/Ubuntu/` is moved" rule; the preamble names it). Then, on dropbox.com, **Delete forever** and audit the account. `dropbox exclude add` is not a substitute: it removes the local copy
   and leaves the cloud one. Exclude `_yamaguchi_records/` too if it lists paths. (S-4)
5. **Re-decide D-2**, do not merely execute it: it was ruled "accept + scrub" against a local-journal exposure, and the same lines are in `/var/log/syslog*`, in cloud-linked Claude Code transcripts, and — as a cleartext passphrase file — in S-7 and in a third party's cloud (S-4). Then rule on D-8 and execute.

### P2 — hardening and re-pointing (same week)

1. *(The chown, the `bin/` removal and `/etc/default/duplicati` moved to P0.5a item 1.)* Confirm `chmod 0700 /home/duplicati/.config/Duplicati` and `0600` its files (Duplicati's own requirement, §7.3.2) survived the recovery.
2. **After a D-14 ruling**, run `util/ad-hoc/2026-09-21_backup_destination_permissions.bash` — first on a scratch directory **on `sda1`** to check ext4's default-ACL creation modes, and only when `dropbox status` reads up to date (it produces ~1,700 metadata updates). Restart Dropbox in a session carrying gid 139; verify `AC-7`.
3. Confirm the snapshot lane: the **installed** copy under `/usr/local/lib/duplicati/` (not the repository file — P0.5a item 2 made the unit execute the copy) reads the new data folder, the timer is running again, and the next 13:45 UTC snapshot lands with a fresh mtime. **AC-6 is a P2 criterion**, not a P0 one, for exactly this reason.
4. Watchdog changes (§7.6); redeploy with `util/ad-hoc/yamaguchi_watchdog_deploy.bash`.
5. `systemd-analyze security duplicati.service`; record the score in the validation record.
6. Reboot test (`util/ad-hoc/yamaguchi_reboot_verify.bash pre` / `post`; AC-9).

### P3 — tiers 2 and 3 (following week)

1. **Fix the runner's mount root first — and install it.** Add the absolute-mount-root form to `util/juniper-backup.bash` (a `MEDIA_NAMES` entry beginning with `/` is taken as an absolute mount root) and have the scheduler and the runner read **one** mount-root setting. Note that the scheduler executes `~/.local/bin/juniper-backup.bash`, which **does not exist** — `~/.local/bin/` holds only the old lane's two scripts — so the repository fix cannot
   reach production until step 2's installer copies it there. Until both land, every "due" run ends `FATAL: runner missing` or `FAILED runner rc=1`, and step 2 cannot produce its own OK run (§4.5, §7.8).
2. Land `util/juniper-backup-scheduled.bash`, `util/install_juniper_backup_timer.bash` (it must copy the runner, the scheduler **and** the failure reporter into `~/.local/bin/`, as `util/install_duplicati_timer.bash` already does for the old lane), the three user units above **and** `juniper-backup-failure.service` — which must carry `Environment=DUPLICATI_STATE_DIR=%h/.local/state/juniper-backup` and
   `ExecStart=%h/.local/bin/duplicati-backup-failure.bash juniper-backup.service`, or it writes its record into the *duplicati* lane's `failures.log` and tails that lane's `last-run.status`, reproducing the very defect it exists to avoid. The reporter itself already takes the unit name as `$1` (`util/duplicati_backup_failure.bash:31`), so no reporter change is needed. Install; enable; observe one SKIPPED (unplugged) and one OK (plugged) run; watch
   `systemctl --user status juniper-backup.path` for 30 s after the plug-in to confirm the `.path` unit is still active; class-1 drill (`util/ad-hoc/2026-08-26_backup_restore_drill.bash`).
3. Rule on D-5; fstab line for the external drive; first `full` set; restore drill of one archive from it.

### P4 — cleanup (after seven consecutive successful daily runs)

1. Archive `/usr/lib/duplicati/data/` and remove it. **Not** into `~/.local/state/` as an unencrypted tar: that directory is inside the backup source and group-shared, and the tar holds the server database (encrypted under the burned, public key) plus the per-job index, which carries the full path list of the whole home directory — backing that up in cleartext violates this design's own rule 8. Write it to a **root-only 0700 directory outside the backup source**,
   or encrypt the tar. `/usr/lib/duplicati` is already fully `root:root` from P0.5.
2. Remove `/home/duplicati/.config/Duplicati/{temp,temp1,backups}` after confirming the pcalnon originals exist (`ls -la /home/pcalnon/.config/Duplicati/backups/`), and `Duplicati.empty-2026-09-20`.
3. *(Executed in P0.5a item 7 — kept here as the procedure of record; verify with `getent passwd duplicati`.)* `usermod -s /usr/sbin/nologin duplicati`.
4. Open the user-lane removal PR the record has owed since 2026-08-30.

---

## 9. Acceptance criteria

| ID | Criterion | Verification |
| --- | --- | --- |
| AC-1 | `duplicati.service` is the `/etc/systemd/system` unit, active as `duplicati`, `NeedDaemonReload=no`, `NRestarts=0` over 24 h | `systemctl show duplicati.service -p FragmentPath,User,NeedDaemonReload,NRestarts,ActiveState` |
| AC-2 | The job `Yamaguchi` exists with `TargetURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi`, 2 sources, 45 filters, schedule `1D` at 14:00 UTC, `--blocksize=1MB` | `python3 util/ad-hoc/yamaguchi_server_api.py status` and `export <id>` — **`<id>` is 2 only if P0 step 7 (Procedure B) did not assign another**; record the assigned id in the validation record and pass it here, to the census, to AC-5 and to the watchdog unit |
| AC-3 | First post-recovery backup `ParsedResult=Success`, **`Warnings=0` and `NotProcessedFiles=0`**, `SourceFilesCount` within 2 % of 1,024,167 and `SourceSizeString` within 5 % of 290.61 GiB, **plus a positive find of one `~/.ssh` and one `~/.gnupg` path**; census `AGREE` (note AC-3a) | `python3 util/ad-hoc/yamaguchi_census.py --runs 1`; `duplicati-cli find`; `Metadata` via the forensics script on a fresh snapshot |
| AC-4 | **Two** restore drills, not one: one from `duplicati-20260918T140000Z` (pre-recovery) and one from the first post-recovery fileset. Both with local blocks **off** (the 2.4.0.0 default; never pass `--restore-with-local-blocks`; `--no-local-blocks` is deprecated), SHA-256 and length match on ≥ 15 files, one negative control fails (note AC-4a) | `util/ad-hoc/yamaguchi_drill_watch.bash` lineage |
| AC-5 | Watchdog reads `OK` three consecutive days; a deliberate `--backup-id 999` fires `JOB_MISSING` | `~/.local/state/duplicati/server-watchdog.log` |
| AC-6 | **(A P2 criterion — not provable at the end of P0.)** Snapshot lane reads the new data folder; the snapshot file's mtime advances daily; it appears in the next fileset | snapshot journal; `duplicati-cli list` / UI search |
| AC-7 | Dropbox daemon carries gid 139; newest dlist `up to date` within 24 h of its write; `_yamaguchi_keys/` outside the Dropbox root | `/proc/<pid>/status`; `dropbox filestatus`; `ls` |
| AC-8 | No secret in **either log store** since the hardening timestamp: zero `LINE: "`, `Exporting Environment` and `Settings Encryption Key:` lines in the journal **and in `/var/log/syslog*`**; zero in the job log's run-script output; `.env` has no commented assignment; the wrapper has no credential-shaped literal; the P0.5 gitleaks rule passes (note AC-8a) | `journalctl --since <ts>`; `sudo grep -c` over `/var/log/syslog*`; `2026-09-21_env_file_shape.py` |
| AC-9 | Reboot: service back within 60 s of boot, job present, next scheduled run fires unattended | `yamaguchi_reboot_verify.bash post` |
| AC-10 | T2: timer fires weekly; a run with no drive reads `SKIPPED`; a run with a drive attached (mounted under the root `util/juniper-backup.bash` is configured for — `/run/media/pcalnon/` or the fstab paths, §4.5) produces verified archives on every mounted drive; class-1 drill passes | `~/.local/state/juniper-backup/last-run.status`; drill script |
| AC-11 | T3: first `full` set written; one archive restored and diffed against the live tree | manual |
| AC-12 | `systemd-analyze security duplicati.service` reports an exposure **at or below 2.0** and no ✗ row outside the accepted set in note AC-12a; the server completes AC-3 under every confinement directive the unit sets — one it cannot run under is removed **and recorded**, never silently | `systemd-analyze security`; journal of the first start; a `systemd-run` trial against the **P0 step 1 data-folder freeze** first |
| AC-13 | The job's `--run-script-before-required` equals `/usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash` and nothing else; no other run-script option is set (note AC-13a) | `python3 util/ad-hoc/yamaguchi_server_api.py export <id>`; diff against the design's path |
| AC-14 | After any `.env` or `DAEMON_OPTS` change, `journalctl -u duplicati.service --since <ts>` contains **zero** `Unknown option supplied` lines — 2.4.0.0 logs an unrecognised option as a warning and **continues** (§7.3.3), so a typo is otherwise silent (note AC-14a) | `journalctl -u duplicati.service --since <ts> \| grep -c 'Unknown option supplied'` = 0 |

Notes on the criteria above:

- **(AC-3a)** The count tolerance alone is not enough. From the snapshot's 45 filters, the large 0700 trees `Dropbox-OLD/` (327k entries) and `snap/` (256k) are *excluded*; the **unfiltered** 0700 trees (`.config/Slack` 54k, `.config/Code` 39.5k, `.mozilla` 23k, `.local/state` 22.6k, `.config/Cursor` 12k, `.amp`, `.claude/projects`, `.ssh` 31, `.gnupg` 98) sum to roughly 15 % of 1,024,167. So a ±2 % count check sees a *gross* loss but cannot see `~/.ssh` or
  `~/.gnupg` — the very trees §7.10 says the capability exists for; hence the explicit `find`. The baseline numbers are real but appear nowhere in the record, so cite their provenance: the snapshot's `Metadata` rows `SourceFilesCount=1024167` and `SourceSizeString=290.610 GiB`. Pre-flight the capability itself before the run: `systemd-run -p User=duplicati -p AmbientCapabilities=CAP_DAC_READ_SEARCH --wait cat ~/.ssh/known_hosts` (owner action — it needs root).
- **(AC-4a)** PLAN §7 criterion 3 asks for a second restore point after at least one incremental, and a single drill collapses it. The re-attached index serving the *old* filesets is exactly what one drill cannot see — which is the whole risk of Procedures A, A2 and B. If `--aes-version` is pinned to 3 rather than 2 (§7.5), one drill must be pre- and one post-format-change.
- **(AC-8a)** `gitleaks` is **not installed on this host**, so that half of the criterion can only run once P0.5a item 6 adds the pre-commit hook — until then AC-8 is the journal, syslog, `.env` and wrapper checks only, and says so.
- **(AC-12a)** Measured offline on the unit as designed: **1.7 OK**, against **5.2 MEDIUM** for the same unit with round 1's Lane B3 directives removed. That is why the gate is 2.0 and not 5.2 — a 5.2-shaped gate is passed by a unit with `IPAddressDeny`, `SystemCallFilter`, `ProtectProc`, `ProcSubset`, `PrivateDevices`, `ProtectClock`, `ProtectHostname`, `ProtectKernelLogs` and `RestrictNamespaces` **all deleted**, i.e. by exactly the silent drop this
  criterion exists to prevent. The run produces **15** ✗ rows; the accepted set is `AmbientCapabilities=`, `CapabilityBoundingSet=~CAP_(DAC_*|FOWNER|IPC_OWNER)`, `SystemCallFilter=~@privileged`, `SystemCallFilter=~@resources`, `RestrictAddressFamilies=~AF_UNIX`, `RestrictAddressFamilies=~AF_(INET|INET6)`, `PrivateNetwork=`, `PrivateUsers=`, `ProtectHome=`, `RootDirectory=/RootImage=`, `RemoveIPC=`, `MemoryDenyWriteExecute=`, `DeviceAllow=`,
  `IPAddressDeny=` and `UMask=` (the last now RULED at `0027`, D-14, §10.1). The `~@privileged` row is a **set-wide** test and does not contradict §7.3.2's narrower, correct claim about `open_by_handle_at`. `MemoryDenyWriteExecute=` would break the .NET JIT and `PrivateUsers=` conflicts with `AmbientCapabilities=`, so neither is a candidate; `RemoveIPC=yes` is free and unclaimed. **None of the added directives has been executed against 2.4.0.0 on this host** (open item
  O-12) — trial them with `systemd-run` against the P0 step 1 freeze copy, not against a probe copy that only exists if step 3's confirmation probe was run.
- **(AC-14a)** An **environment variable** the server does not read logs nothing at all, so AC-14 is blind to that class — which is why §7.3.2's two `Environment=` names were verified against the shipped assemblies rather than trusted to this grep.
- **(AC-13a)** Pinned as an acceptance check because a run-script path is a plain job option with no allow-list: anyone holding the UI credential can point it anywhere and have it execute as `duplicati` **with** `CAP_DAC_READ_SEARCH` (§7.3.6). A silent change to this option is a privilege escalation that no other check would catch.

---

## 10. Owner decisions

| ID | Decision | Recommendation |
| --- | --- | --- |
| D-1 | **Rule before P0.** Settings-key policy: keep DB encryption with a distinct, escrowed key, or `--disable-db-encryption` | keep encryption; the record's objection (a third key) is accepted as the price |
| D-2 | **Re-decide** (§6 note S-3a). `PASSPHRASE` exposure: accept + scrub, or start a new set under a new passphrase. The original ruling assumed a journal-only, local exposure; four things falsify that | lean to a **new set under a new passphrase**, or record an explicit owner acceptance that names Dropbox as a reader. A new set must also **delete-forever** the old one server-side (§7.5 rule 7) |
| D-3 | Cloud replica mechanism: Dropbox desktop client on the T1 destination (as built) vs `duplicati-sync-tool` (shipped in 2.4.0.0, not studied here) or Duplicati's native Dropbox backend from a job that owns the copy | keep the desktop client for now with the §7.5 guard; evaluate `duplicati-sync-tool` separately — it would remove the sync client from the write path and the group-membership prerequisite |
| D-4 | **Rule before P0.** Read access to `/home/pcalnon`: `CAP_DAC_READ_SEARCH` on the service vs recursive ACLs on the home. The trade is asymmetric and §7.1 principle 3 states it in full | capability, **with** §7.3.2's confinement set, which is what stops it also being an exfiltration channel |
| D-5 | Tier 3 content, cadence, retention (the truncated requirement) | §7.9 default |
| D-6 | **Rule before P0.** Live wrapper: root-owned installed copy (recommended) vs the symlink into the checkout | copy — and delete `/home/duplicati/bin/` rather than keeping the symlink as a "fallback" |
| D-7 | Keep or delete the 57 GB of copied job databases under the duplicati home | delete after P4 step 2's check |
| D-8 | Journal scrub (`--rotate` + `--vacuum-time=1s`, loses all history) vs leave | scrub once, after P1 |
| D-9 | **Rule before P0.** Web UI reachable from LAN (`any` + allowed hostnames) or loopback only | loopback, plus `--webservice-disable-signin-tokens` once a password exists |
| D-10 | T2 cadence (weekly proposed) and USB retention | weekly; prune sets older than 8 weeks after a drill |
| D-11 | Docker volumes and conda envs: export into the T1 source, or accept the gap | export docker volumes weekly; conda recipes only |
| D-12 | Inherited items, **enumerated rather than gestured at** (note D-12a) | each item gets its own disposition in the P3/P4 review, not a blanket sentence |
| D-13 | **New.** Dropbox root policy: exclude everything except `Backups/`, or accept that personal files (9 jpg, 2 pdf, a lnk today) keep syncing beside the ciphertext (note D-13a) | exclude everything but `Backups/` — it costs nothing and removes a whole class of cross-contamination |
| D-14 | **New.** The destination permission model: the R-7/R-8 group-write form of §7.4 (directories `2770`, files `0660` — `pcalnon` and Dropbox can write and **delete** all 877 volumes) vs the read-only form (`duplicati:duplicati 2750`, files `0640`, `UMask=0027`, volumes chowned to `duplicati`) | the **read-only** form (note D-14a) |

Notes on the decisions above:

- **(D-12a)** The earlier row said "unchanged from the record" and then named five items, letting the rest dissolve — the failure shape `HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §6.1 recorded. Every open item of that handoff's §1 and of `JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md` §8.27.6 gets one of three dispositions — **carried**, **out of scope**, or **closed by §** — and none may be left unstated.
  Closed 2026-09-23: `sda` SMART — run and PASSED (note 10.2a). Carried today: the `sdc4` read-only loop probe; the sdc2 grow; cloud reporting (deferred); the user-lane removal PR (P4 step 4); the dead `yamaguchi_records_sync.bash`; the drift-guard tests in 7 repos; `yamaguchi_run_script_after.bash` as alerting candidate A, never revoked; `duplicati_first_backup.bash`'s hardcoded gate; the YAM §8.21.5 residuals; the unconfirmed `sops-backup-key.sh` escrow run (inherited
  O-2). Closed by this design: the watchdog `ProgramState` check (§7.6).
- **(D-13a)** The owner prompt said "Dropbox syncs only the contents of `Backups/`"; §4.4 corrected that to nine excluded folders with everything else at the root syncing, and no decision item then asked what the root *should* be. This one does.
- **(D-14a)** R-8 asks only for **read**; the group-write form lets a cloud-side deletion (compromised account, linked phone, another machine) or an accidental local `rm -rf` propagate into the local master and on to T1c. State the limit honestly: `pcalnon` is root-equivalent via `sudo`/`docker` anyway, so the read-only form buys protection against **accident and commodity malware**, not against a deliberate local adversary. It conflicts with R-7's
  "read/write/execute as appropriate", which is why it was the owner's call and not this design's.
  **Ruled 2026-09-22: the read-only form** (§10.1).

---

### 10.1 Owner rulings — 2026-09-22

All seven open gates were ruled by the owner in one interactive session on 2026-09-22. **The Ruling
column below is binding and the Recommendation column above is historical.** D-3, D-5, D-7, D-10, D-11,
D-12 and D-13 remain open and keep their recommendations.

| ID | Ruling | Effect in this document |
| --- | --- | --- |
| D-1 | **Keep database encryption.** A random key distinct from every passphrase, at `/etc/credstore/duplicati-settings-key` root:root 0600, delivered by `LoadCredential=`, made mandatory by `--require-db-encryption-key` | §7.3.5's recommendation becomes binding; the 2026-08-30 objection is accepted as the price |
| D-2 | **Rotate the passphrase and KEEP the existing sets.** Scrub first, then re-encrypt all 877 volumes with the RecoveryTool, staged and verified before any swap | §6 note S-3 corrected; new §10.2 carries the order of operations |
| D-4 | **`CAP_DAC_READ_SEARCH`**, paired with §7.3.2's confinement set | §7.1 principle 3 becomes binding; the "duplicati uid == root-read" residual stands |
| D-6 | **Root-owned installed copy, plus a drift gate.** A blessed sha256 per installed file, checked every run; `--update-backup-behavior` is the escape hatch | §7.3.4's installer gains the gate; `/home/duplicati/bin/` is deleted |
| D-8 | **Scrub once, after P1** (`--rotate` + `--vacuum-time=1s`) | unchanged from the recommendation |
| D-9 | **Loopback only**, plus `--webservice-disable-signin-tokens` once a password exists | §7.3.6 becomes binding |
| D-14 | **Read-only destination model.** Directories `duplicati:duplicati 2750`, files `0640`, `UMask=0027`, existing volumes chowned to `duplicati` | §7.4's table and its script rewritten; the unit's `UMask=` goes `0007` → `0027` |

- **(10.1a)** **D-6's ruling is stronger than the recommendation it replaces.** The recommendation was a
  bare copy. The owner added a no-change gate with an explicit `--update-backup-behavior` switch, which
  catches two things a bare copy cannot: an installed artifact edited outside the installer, and a
  repository that has moved ahead of what is deployed. The symlink form was considered and rejected on
  one decisive fact — on a fresh host the checkout does not exist yet, so a symlink at the install path
  is **dangling and `ExecStart` fails**, defeating the bare-metal recovery case it was proposed for.
- **(10.1b)** **D-2's ruling required correcting two variable names before it could be recorded.**
  `SETTINGS_ENCRYPTION_KEY` encrypts the **server database**; the backup volumes are encrypted with the
  job's **`PASSPHRASE`**. `SETTINGS_ENCRYPTION_KEY_OLD` and `PASSPHRASE_OLD` **do not exist in 2.4.0.0** —
  scanned across 1,443 files in UTF-8 and UTF-16LE, zero hits each
  (`util/ad-hoc/2026-09-22_duplicati_literal_scan.py`). Writing the new passphrase into
  `SETTINGS_ENCRYPTION_KEY` would have re-keyed the database and left all 877 volumes under the leaked
  passphrase. §4.1 records that on this host the active `SETTINGS_ENCRYPTION_KEY` **already equals
  `PASSPHRASE`** — the same conflation, already made once, and part of what broke.
- **(10.1c)** **The new passphrase does not go in `.env`.** That file is `0660 duplicati:duplicati` and the
  wrapper echoed every one of its lines into the journal and syslog — 60 echoes on 09-20, which is S-3,
  the exposure being remediated. It goes to `/etc/credstore` under `LoadCredential=`: the same custody
  model as D-1's settings key, and a **distinct value** from it.
- **(10.1d)** **D-14b.** The Dropbox root keeps `2770` while everything beneath `Backups/` moves to
  `duplicati:duplicati 2750`. The sync daemon runs as `pcalnon` and must write its own root; narrowing
  that would break synchronisation rather than harden anything. The protection comes from the
  destination tree below it, where only `duplicati` holds write on the directories — which is what an
  unlink requires.

### 10.2 D-2 execution: scrub, rotate, re-encrypt — order of operations

The owner set two criteria: **access to backup data is never lost**, and **the new passphrase does not
leak**. The sequence below is ordered by those and not by convenience. **None of it is a session's to
execute** — it is owner-gated exactly as §8 is, and it runs *after* the recovery, not during it.

**The mechanism exists in the product.** `Duplicati.CommandLine.RecoveryTool.Implementation.dll` carries a
`recompress` verb (strings read from the assembly rather than by running it —
`util/ad-hoc/2026-09-22_recoverytool_verbs.py`):

```text
recompress <targetcompression> <remoteurl> <localfolder> --reupload --reencrypt [options]
3) If --reencrypt is supplied, again reencrypts using same passphrase. If the
   --new-passphrase option is present, encryption happens using the new passphrase
4) If --reupload is supplied, files with old compression are deleted and recompressed
   files are uploaded back to remote storage
Warning: Before recompress delete local database and after recompress recreate local
database before executing any operation on backup.
```

So an existing fileset **can** cross a passphrase rotation, which is what makes "rotate without losing
the backups" a real option rather than a wish. Three hazards ride with it, and each touches one of the
owner's two criteria:

1. **`--reupload` deletes the originals at the destination.** The sole local copy sits on `sda`, whose
   SMART state was unknown when this was written and is now **read and PASSED** (2026-09-23, note 10.2a).
   A healthy disk does **not** make an in-place rewrite safe, for a second reason the health report
   itself supplies: `sda` is a **drive-managed SMR** drive (`WDC WD40EZAZ-00SF3B0`, "Western Digital
   Blue (SMR)"), so `--reupload` against the live destination is a full band-rewrite of the only copy —
   slow enough that it must not be mistaken for a hung operation. This is why the ruling is
   **stage → verify → swap** and not in-place, and why nothing here contradicts §8's rule that nothing
   under `/mnt/Backups/Ubuntu/` is deleted or moved.
2. **The local database must be deleted before and recreated after.** A Recreate across 877 volumes is
   long, and §5.3 records that an *aborted* per-job Recreate is precisely what produced the database
   this whole arc began by misreading.
3. **`--new-passphrase=` on argv is world-readable** through `/proc/*/cmdline` — the same defect class
   §7.3.6 already forbids for `duplicati-server-util change-password`. The new passphrase must reach the
   tool by a channel that is not argv, or the rotation leaks the secret it exists to protect.

| # | Step | Gate before proceeding |
| --- | --- | --- |
| 1 | SMART test `sda` — **DONE 2026-09-23, PASSED** (note 10.2a). Restore-drill the CURRENT set — outstanding, and **discharged by AC-4's pre-recovery drill inside §8 P0 step 11**, not before P0 (note 10.2c) | AC-4's first drill passes on the current passphrase |
| 2 | Scrub the leaked copies: the S-7 file, the `.env` comment block, and D-8's journal scrub after P1 | S-3, S-6 and S-7 counts all read zero |
| 3 | Mint the new passphrase; place it at `/etc/credstore/duplicati-passphrase` root:root 0600 | never in `.env`, never on argv, never echoed |
| 4 | Copy the 877 volumes to staging on **`nvme0n1p5` (`/`)** — **not** `sda` (note 10.2b); ≈203 GiB required | per-file hashes match the source |
| 5 | `recompress … --reencrypt --new-passphrase` against the **staging** copy only | exit 0, and every volume re-encrypted |
| 6 | Recreate the local database against staging; restore-drill from staging | a drill passes on the NEW passphrase |
| 7 | Swap staging in as the live destination | the old set is retained untouched until step 6 passed |
| 8 | Delete-forever the old ciphertext server-side (Dropbox retains deleted files 30 d on Basic/Plus/Family, 180 d on Professional) | only after step 7 is verified |

**Step 1 is first, is not optional, and is currently HALF DONE**: the SMART half passed on
2026-09-23; the drill half is AC-4's and runs inside P0 (note 10.2c), so step 2 is not unblocked and
**the next action in this arc is §8's P0 recovery, not anything in §10.2**. Steps 4–7 remain a bulk
rewrite of the only local copy of 202.8 GiB. A rotation that loses the data it was protecting has
failed at the thing it was for.

- **(10.2a)** **`sda` SMART, read 2026-09-23 — PASSED.** Evidence:
  `reports/smart/smart-xall_results-sda_2026-09-23_07:53:18.out`, produced by
  `util/ad-hoc/smart_checks_backup-sda.bash`. An **Extended offline** self-test completed without error
  at lifetime **28,938 h** against **28,941 h** at capture, so the scan is current and covered the
  surface. The header alone does **not** show this: `Self-test execution status: (0)` also means *"no
  self-test has ever been run"*, and only the self-test **log** disambiguates the two — read the log,
  never the status line. `Reallocated_Sector_Ct`, `Current_Pending_Sector`, `Offline_Uncorrectable`,
  `Reallocated_Event_Count` and `UDMA_CRC_Error_Count` are all **0**; the ATA error log and the Pending
  Defects log are both empty; every SATA Phy event counter is 0; temperature 39 °C with an
  under/over-limit count of 0/0. Age is the only soft spot and it reads better than the hours suggest —
  28,941 power-on hours (~3.3 years) but only **1,803 Head Flying Hours** and ~10.4 TB written in life.
  This **closes** the §12 / D-12a carried item "sda SMART never read".
- **(10.2c)** **Step 1's drill cannot precede P0, and does not add a second drill.** The SMART half ran
  early and correctly; the drill half cannot, for a reason that is easy to miss because the two halves sit
  in one row. A drill needs a **job index**, and P0 step 0(c) already records that the index must come from
  **P0 step 1's freeze** — `--no-local-db` rebuilds it from all 877 dindex volumes and was measured at
  ">30 minutes for a single small file here, without completing"
  (`util/ad-hoc/duplicati_drill_run.py`). The distinction that makes a drill possible at all is that the
  **server** database is the file locked under an unmatched key (§5.4), while the **job** index —
  `BMXWPAOGLP.sqlite`, last written 09-18 — is a separate file and is what a drill reads. So the drill is
  **AC-4's first one** — from `duplicati-20260918T140000Z`, the pre-recovery fileset — run at §8 P0 step 11
  alongside the post-recovery drill. §10.2 step 1 names that drill as its gate; it does not ask for another.
  Its terms are §3.3 item 6's and are not negotiable by whoever runs it: never pass
  `--restore-with-local-blocks` (`--no-local-blocks` is **deprecated** in 2.4.0.0 because not using local
  blocks is now the default), select by `--time=`, compare **SHA-256 and length** on ≥ 15 files, include a
  negative control that must fail, and treat the **exit code as not evidence**.
- **(10.2b)** **Staging goes on `nvme0n1p5` (`/`), not on `sda`.** `sda1` has 3.1 TiB free and is the
  obvious-looking target, which is exactly the trap: it holds the sole local copy, so staging there puts
  the original and the re-encrypted copy in **one failure domain** for the whole of steps 4–7. The clean
  SMART report above does not change that — it lowers the probability, not the consequence, and the
  criterion the owner set is that access is *never* lost. `/` has 376 GiB free against the ~203 GiB
  needed, sits on a different physical device, is **ext4** so ownership and modes survive for D-14's
  read-only model, and is **outside the `/home/pcalnon` backup source**. `sdc3` (`/home`, 1.2 TiB free)
  satisfies the failure-domain test but fails the last one: staging there would sweep 203 GiB of
  ciphertext into the next fileset unless an exclusion were added first — the same class of mistake as
  S-7.

---

## 11. Validation record (CON §7)

**State of the record: two rounds delivered and fully reconciled.** Round 1's six verbatim reports are
archived in `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`, round 2's four in
`JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md`, and the five step reports the
design was drafted from in `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-STEP-REPORTS-RECORD.md`.

- **Instruments and whether each could have produced a different answer**: §5.6 for the three root-cause legs (Lane A1 re-ran the database forensics twice, 13:40 and 13:49 CDT, byte-identical copies, and confirmed both adequacy arguments: the WAL replay that produced the 19-table local schema would have shown a server schema the same way, and a torn copy would have shown a broken frame chain or a `quick_check` error). Lane B2 notes that no adequacy statement exists for the §4.1 observations the plan acts
  on — an open item.
- **Sample sizes**: system journal 2026-09-17 → 2026-09-21 (complete, re-read by two lanes); five server-database copies (four re-inspected by Lane A1, two by Lane B1 with an offline key-hash test); 877 destination files (re-counted); `/var/log/syslog*` back to 09-12 (Lane B1, counts only); 13 handoffs and 7 documents of record (Lane A2); Duplicati source at tag `v2.4.0.0_stable_2026-09-03` (Lanes A3 and B1); systemd 259.5 man pages.
- **Agents per lane and entry points**: drafting — five step agents (1a documents of record; 1b handoffs + tooling; 2a live host; 2b repository + synthetic wrapper tests; 2c product sources). Validation — six agents, launched together, none seeing another's output: Lane A ×3 (A1 live host only; A2 repository and documents only; A3 product behaviour and code execution — the design's own tagged blocks run against synthetic inputs); Lane B ×3 (B1 refute the root cause and the recovery; B2 amputation and
  actionability; B3 security). All six were killed mid-run by a session usage limit and resumed in place with context intact.
- **Iterations and what each one changed**: **two rounds**, plus a third single-agent confirmation pass.
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
  **Round 3** (one agent, briefed on round 2's corrections, reading a **frozen** document) confirmed 13 of
  the 20 corrections outright, found 6 present-but-incomplete, and swept every internal cross-reference —
  15 defects, all applied. Its own instruments reproduced AC-12a's `1.7 OK` and all 15 ✗ rows, the 53/18
  syscall-set numbers, the 1,443-file scan and the byte-identity of all 14 tagged blocks against their
  landed repository copies. Its sharpest finding was structural and is the one round 2 created: the
  P0.5a/P0.5b split was made by **adding headings**, not by relocating content, so the re-key procedure was
  still printed in full inside the list headed "before anything in P0" — the exact ordering error the split
  exists to prevent. §12 records the result.
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
  the arc before reconciliation began.
- **Unresolved dissent, and how each was settled or left open**:
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
     factually loose (§8 step 4's filter count).
- **Open items, and the observation that settles each** (this document's numbering continues
  `HANDOFF_2026-08-21_backup-systematization-design-arc.md`'s O-0…O-8):
  **O-12** — does 2.4.0.0 run under the §7.3.2 confinement set (`SystemCallFilter=@system-service`,
  `IPAddressDeny=any`, `ProtectProc=invisible`, `PrivateDevices=yes`, …)? A `systemd-run` trial against the
  P0 step 1 freeze copy, then `systemd-analyze security`. AC-12 closes it.
  **O-13** — does RunScript's `SendStdOutToLogs` store the guard's stderr verbatim, carrying an
  attacker-chosen stray-file name into the job log? Read `RunScript.cs`. A log-injection nuisance only.
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
| 2026-09-21 (later) | Handoff-validation Lane B1 corrections applied here: the §8 STOP warning (Procedure A0; `wipe-encryption` does take `--server-datafolder` on the subcommand), §7.3.2's env override, P1 step 2's mode, the status line, §11. |
| 2026-09-22 | **Consensus round 1 reconciled in full.** Lanes A1, B1, B2 and B3 folded in; the §8 STOP warning removed and replaced by P0 step 0's owner gates; Procedure A0 added; P0 renumbered 0–11 with a new P0.5 bucket; §7.3.2's confinement set; S-7 and S-8; D-13 and D-14; AC-13. Applied by `util/ad-hoc/2026-09-22_reconcile_backup_design.py`. **Changed**: this file. **Added**: that script. |
| 2026-09-22 (later) | **Consensus round 2 reconciled** — four lanes (host, product, actionability, security); see §11 for what it found and `util/ad-hoc/2026-09-22_apply_round2_corrections.py` for the edit set. **Changed**: this file. **Added**: that script, `util/ad-hoc/2026-09-22_credential_file_shape.py`. |

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
2026-09-20T18:47:44 duplicati-server: Failed to process the path: Access to the path '/media/pcalnon/temp_backups' is denied.   (last lines of the unit; x2 -- outer + inner exception -- and again x2 at 18:51:33; 4 lines in total)
```

Two identifier notes, because they change what a line means: the `20:48:12` line was emitted under
`wrapper.bash` — the **first** wrapper's name — not `duplicati-server`, and from `13:32:34` to `13:32:38` on 09-20, five starts
of that same older `wrapper.bash` died `SettingsEncryptionKeyMissingException` — the first of them sixteen
seconds before the `13:32:50` success from `duplicati-wrapper.bash`. Two wrapper files were in play that
afternoon. (The older file is identifiable in the journal by its own error, `line 38:
/home/duplicati/.config/.env: No such file or directory` — a path the successor never reads.)

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
| `/usr/lib/duplicati/data/` | 2026-08-25 02:38:43 | 2026-09-18 21:03:34 — **the `-wal`/`-shm` creation, not the encryption** (a directory mtime records an entry create/delete/rename; encrypting fields rewrites the database file). That it never moved again means the WAL was never removed by a clean close | 2026-09-19 19:15:00 |

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
| `util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash` | Procedure A probe (confirmation only) | `bash -n`, shellcheck |
| `util/ad-hoc/2026-09-22_confirm_a0_premise.bash` | Procedure A0 premise check | `bash -n`, shellcheck |
| `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash` | Procedure A0 restore | `bash -n`, shellcheck |

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
9. **The pcalnon `Duplicati-server.backup` is itself `enc-v1:`** — 11 encrypted values under a single key hash, which the offline probe verified 11/11 and matched to no candidate. It is a libsecret-minted key (§5.4), which is how a database comes to be encrypted with nobody typing one. Every "the database stores the passphrase in cleartext" statement in the record (YAM §8.19.3, and item 3 above) is therefore true of the **root** database only, and only before 09-18 21:03.
10. YAM §8.20.2's record that the owner **rejected** `SETTINGS_ENCRYPTION_KEY` on 2026-08-30 was reversed without a record by the 09-18 unit edits and the 09-20 `.env`. D-1 asks the question again. (Already in §3.5; repeated here because Appendix C is the list a future reader diffs against the record.)

**None of items 1–10 has been applied to its target document.** That is tracked work, not a closed correction: item 1's targets are YAM §8.20.4 and `HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §1.8; item 4's are `util/ad-hoc/yamaguchi_server_db_snapshot.py:20,36` and `util/systemd/yamaguchi-server-db-snapshot.service:5`; item 5's is the destination README. Item 2's own text was rewritten by consensus round 1 (Lane A2) and item 9 is new in the reconciliation.
