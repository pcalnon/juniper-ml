# Backup system — state assessment and recovery plan, 2026-10-03

- **Project**: Juniper (workstation backup infrastructure, host `yamaguchi`)
- **Author**: Paul Calnon
- **Date**: 2026-10-03 (host measured 08:43 UTC; validation round 1 reported by 10:30 UTC)
- **Status**: VALIDATED (round 1) — three independent lanes (fact re-probe, consequence attack, continuity hunt) reported; every finding is folded in or recorded as dissent in §8. One judgement call of the first draft was refuted and reversed (§6.4, O-2).
- **What this is**: a re-measurement of the host twelve days after the design of record last measured it, a comparison of three things — the documented architecture, what the repository has built, and what the host is actually running — and an execution plan that gets a backup running again. It **does not supersede** the design of record; its §6 applies that design's §8 with the five procedure defects the 2026-09-24 STOP named closed in the artifacts rather than argued in prose.
- **Design of record** ("D"): [`JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`](JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md). Section numbers below without a filename are D's. "The branch" is the un-pushed `worktree-typed-skipping-salamander`, which carries the owner's 2026-09-24 STOP ruling (note 3b).
- **Successor-facing handoff**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_backup-arc-consolidated.md` (ml#2109, merged 2026-10-03 09:21Z, during this document's validation round). It supersedes the three handoffs this document was briefed on and **defers to this document for host measurements**. Division of labour: that file carries the session mechanics for landing the paused branch (its "Step 1 sub-steps 1a–1h") and the full carried-item inventory; this
  file carries the measured state, the issues register and the phase plan. Where they disagree, the newer host measurement wins.
- **Predecessor handoffs** (read item by item; each now carries a SUPERSEDED banner): `…/HANDOFF_2026-09-21_backup-redesign-round-1-validated-reconciliation-pending.md`, `…/HANDOFF_2026-09-24_backup-arc-seven-decisions-ruled-smart-passed-p0-is-next.md`, `…/HANDOFF_2026-09-24_backup-arc-d8-stop-change-paused-in-round-8.md`.
- **Secrets discipline**: no passphrase, key or credential value appears here. Secret files were described by `stat` and, for the service `.env`, by `util/ad-hoc/2026-09-21_env_file_shape.py` (names and lengths only — a deviation from the D-8 handoff's "stat only" rule, recorded in §8).

---

## 1. Summary

1. **The host has had no working backup of any kind since 2026-09-18.** Tier 1 (Duplicati, `/home/pcalnon` → `sda1`) last succeeded at 14:12 UTC that day; fourteen scheduled runs have since been missed. Tier 2 (tar + gpg to two USB sticks) has been unable to find its drives since 2026-09-07. Tier 3 (offline external drive) was never built. The only lane still running is T0, the daily server-database snapshot — and it copies the abandoned, key-locked database into a source tree that nothing backs up.
2. **The host is byte-for-byte where the 2026-09-24 handoffs left it, with five exceptions against D and four against the branch** (§3.1): the three long-lived `duplicati`-uid sessions have closed (the branch's note sink-b already records this), the service `.env` was rewritten on 09-22 19:17 CDT and now carries **two** active keys, the live wrapper symlink has resolved to wrapper v2 since 09-22 12:56, both Tier 2 drives are plugged in (and unmounted), and — the important
   one — **not one of the host actions the owner released on 2026-09-24 has been performed.** A sixth change happened by itself: logrotate has pruned the `/var/log/syslog*` copies of the 09-20 secret echoes (§3.1 item 6).
3. **The next start of `duplicati.service` still fails.** The record's verdict — the 0700 data-folder gate refuses the 0777 folder — stands; its reasoning about an argv word "neither wrapper can parse" is obsolete, because wrapper v2 passes that word through. And a new, **earlier** blocker has appeared: wrapper v2 **dies on the `.env` line `SETTINGS_ENCRYPTION_KEY_OLD`** (exit 78, reproduced in §3.2) before it reaches the folder at all. `Restart=always` turns either into a
   crash loop. The standing rule holds: **stop it, never restart it, until P0 installs the corrected unit.**
4. **The job is recoverable and the recovery is small.** The configuration survives in two places readable without the lost key: the daily snapshot (240 KiB, `integrity ok`, replaced every 13:45 UTC) and the 09-17/09-18 filesets (a cleartext copy, restorable with the escrowed passphrase — Procedure A0). The per-job index `BMXWPAOGLP.sqlite` is intact. What recovery needs is **one owner session with `sudo` and the escrowed passphrase, roughly two hours.** The first draft of
   this document proposed Procedure A2 (wipe the encrypted fields) as the cheaper default; validation refuted that in the product source — A2 also wipes the UI password's only home, and with D-9's signin-token flag installed the recovered server would be unreachable (§8, B-1). **A0 is the default**, as D had it.
5. **The arc stalled on process, not on the problem.** D is 2,548 lines and has been through eight validation rounds; rounds 4–7 found that its §8 procedure is not executable as written and the owner placed a STOP on it on 2026-09-24. That STOP, the owner's release list and the 1,212-line record of rounds 4–8 exist **only on the branch** (three un-pushed commits, paused mid-round-8) and in an archived handoff. **`main` still says "§8 is executable in this order and no
   other."** The five STOP defects are each a few lines of artifact change (§5, I-14 to I-18), plus three more the validation of this document found in the artifacts the plan would install (I-36 to I-38).
6. **The plan (§6)** is five phases: finish and land the paused branch so the owner's ruling is on `main` (one session of mechanical work, one narrow validation lane); fix the STOP defects and the three new artifact defects in code and clear the STOP (one PR, one three-lane round); the owner performs the released host actions, which need no passphrase (twenty minutes); the P0 recovery session, with a rehearsal on a throwaway data folder first; then the deferred hardening,
   secrets and tier work, in the order D already fixed. Consensus validation is spent on exactly two things — the artifact PR and the P0 checklist — because those are what touches the sole local copy.

---

## 2. The documented architecture

D §7 keeps the certified three-tier posture and adds the owner's 2026-09-21 direction. Condensed:

| Tier | Medium | Mechanism | Cadence | Key custody |
| --- | --- | --- | --- | --- |
| T0 | inside T1's source | daily copy of the server database into `~/.local/state/duplicati-server-db/` (root timer, 13:45 UTC) | daily | — |
| T1 | `sda1` → `/mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi/` | Duplicati 2.4.0.0 server, job `Yamaguchi`, run as the `duplicati` system user under a confined systemd unit; AES volumes under `PASSPHRASE` | daily 14:00 UTC | printed sheet, password manager, an `sda1` copy **outside** the Dropbox root |
| T1c | Dropbox cloud | the desktop client replicating `Backups/` from the T1 destination (ciphertext only) | continuous | same |
| T2 | USB sticks `EBC5-F0A3`, `DFF3-2782` | `util/juniper-backup.bash`: per-repo `tar` streamed into `gpg -e` for two YubiKey recipients; user-scope timer + path unit, runs when a drive is mounted | weekly | YubiKeys |
| T3 | offline external hard drive | same script, widened to the whole Juniper parent, label `full` | monthly, when attached | YubiKeys |

The service contract (D §7.3, rulings D-1/4/6/9/14 of §10.1, all binding since 2026-09-22):

- Unit at `/etc/systemd/system/duplicati.service` (never the vendor file edited in place); `User=duplicati`; `UMask=0027`; `RequiresMountsFor=/mnt/Backups`; `Restart=on-failure`; `AmbientCapabilities=CAP_DAC_READ_SEARCH` paired with the §7.3.2 confinement set (`ProtectSystem=strict`, `IPAddressDeny=any`, `SystemCallFilter=@system-service`, `InaccessiblePaths=` over the secret stores, …).
- Data folder named explicitly (`--server-datafolder=/home/duplicati/.config/Duplicati`), `0700 duplicati:duplicati`, files `0600` — the product refuses anything else at every start (the gate checks the folder, not the files inside it).
- The settings-encryption key is a **third secret**, random, distinct from both passphrases, at `/etc/credstore/duplicati-settings-key` (root, 0600), delivered by `LoadCredential=`, made mandatory by `--require-db-encryption-key`. It never sits in `.env`, in `Environment=`, or on argv.
- The `.env` file carries only tunables, no key and no commented assignment, and lives **outside** the data folder (`/etc/duplicati/env` in a `0755 root:root` directory, D §7.3.5 and round 3's D13) so the service user cannot unlink-and-recreate it.
- The wrapper is a root-owned **installed copy** at `/usr/local/lib/duplicati/`, checksum-blessed by `util/install_duplicati_service.bash`, which refuses drift unless told `--update-backup-behavior` (D-6). No `eval`; array argv; nothing printed that holds a value.
- Loopback only (`--webservice-interface=loopback`), signin tokens disabled once a password exists (D-9).
- Destination read-only to everyone but the service: directories `duplicati:duplicati 2750`, files `0640`, the 877 existing volumes chowned to `duplicati`; `pcalnon` and the Dropbox daemon read through the group (D-14).
- Every lane fails loudly: `OnFailure=`, a watchdog that asks from outside, a pre-backup guard that refuses an unmounted or foreign destination (`--run-script-before-required`).
- The passphrase is rotated **and the existing 877 volumes kept**, by `RecoveryTool recompress --reencrypt` on a staging copy under `/` (never `sda`), after the recovery is drill-verified (D-2, §10.2).

---

## 3. Measured state — 2026-10-03 08:43 UTC

Every row was re-measured this session with the command in its last column, and re-measured again by validation Lane A with its own commands (§8). Nothing below was copied from the record.

| Component | Measured | Delta vs D §4.1 / the 09-24 handoffs | Evidence |
| --- | --- | --- | --- |
| Host | up since 2026-09-07 23:12 (no reboot since the certification reboots) | none | `uptime -s` |
| `duplicati.service` | `active`, PID 1397393 since 09-20 18:19:42 CDT (12 d 9 h), `NRestarts=0`, `NeedDaemonReload=no`, `Restart=always`, `FragmentPath=/usr/lib/systemd/system/duplicati.service` (vendor file edited in place — `dpkg -V` flags it and `/etc/default/duplicati`), no drop-in, no `/etc/systemd/system/duplicati.service` | none | `systemctl show`, `dpkg -V duplicati` |
| Loaded `ExecStart` | `/home/duplicati/bin/duplicati-wrapper.bash '--daemon-opts="${DAEMON_OPTS}"'` (the armed form) | none | `systemctl show -p ExecStart` |
| Running argv | `/usr/lib/duplicati/duplicati-server` followed by the single word `--webservice-port=8300` with a trailing space; listening `127.0.0.1:8300` and `[::1]:8300` | none | `od -c /proc/1397393/cmdline`, `ss -ltnp` |
| Unit journal | last entry **2026-09-20 18:51:33 CDT**; `-- No entries --` for any `--since` from 09-21 on — the empty server has emitted nothing | none | `journalctl -u duplicati.service -n 1` |
| Data folder `/home/duplicati/.config/Duplicati` | **0777**; the four DB files 0777; `-wal`/`-shm` mtime **09-27 18:20** — seven days to the hour after the 09-20 start, consistent with the weekly update check writing its result (an inference; the journal is silent); `temp/` root-owned | WAL mtime new | `ls -la` |
| Service `.env` | **`0640 duplicati:duplicati`, 1,701 B, mtime 2026-09-22 19:17:37 CDT** — **two active lines**: `SETTINGS_ENCRYPTION_KEY_OLD` (32 chars inside its quotes) and `SETTINGS_ENCRYPTION_KEY` (64 chars inside its quotes); the **five commented-out assignments are still present** | **UNRECORDED** (note 3a) | `stat`; `sg duplicati -c cat \| 2026-09-21_env_file_shape.py` |
| Live wrapper | `/home/duplicati/bin` **0777**; symlink → the primary checkout's `scripts/duplicati-wrapper.bash`, which is byte-identical to `main` (wrapper v2, sha256 `18c36864…`, file mtime 09-22 12:56:56) | v2 since 09-22 (D §4.3 item 9 reasons about v1 revisions) | `readlink -f`, `sha256sum` |
| `/etc/default/duplicati` | `duplicati:duplicati 0644`, `DAEMON_OPTS="--webservice-port=8300"` | none (P0.5a item 1 not done) | `ls -la`, `cat` |
| `/usr/lib/duplicati` | `duplicati:duplicati 0755` (95 of its subdirectories `duplicati`, 21 `root`); `data/` `0700 duplicati` (unreadable to this session) | none (P0.5a item 1 not done) | `ls -ld`, `find -printf` |
| `/etc/credstore` | exists, `0700 root`, born 2024-10-23 (mtime 2024-10-04); contents unreadable to this session | — | `stat` |
| `duplicati` user | shell **`/bin/bash`**; `.bash_history` 8,261 B mtime **09-24 14:56**; the two `su - duplicati` shells (3065639, 3117158) and the `vim` (2318515) D §4.1 note a named **are gone**; no `duplicati`-uid process but the server | shells closed → P0.5a item 7's prerequisite is met (the branch's note sink-b records it; D on `main` does not); item 7 not done | `getent passwd`, `ps -u duplicati`, `ps -p …` |
| T0 snapshot lane | `yamaguchi-server-db-snapshot.timer` fires 13:45 UTC daily (`Persistent=true`); last 10-02 08:45:01 CDT, `integrity ok (16 tables)`, 240 KiB → `~/.local/state/duplicati-server-db/Duplicati-server.sqlite` (0600 pcalnon); **source still `/usr/lib/duplicati/data/`**; `ExecStart` still names the primary checkout's script, runs as **root**, no `ProtectSystem=` | none (P0.5a item 2 not done) | `journalctl -u yamaguchi-server-db-snapshot`, `systemctl cat` |
| Watchdog | user timer 12:00 CDT daily; **`ALERT UNREACHABLE … login failed (401)` every day 09-21 → 10-02** (19 ALERT lines in the log, 15 of them since 09-19); reads the UI credential from the primary checkout's `.env` (`0664`, 1,024 B, mtime 08-25) — S-5; `~/.config/duplicati-backup/web-credential` does not exist; `--backup-id` defaults to 2 | none | `~/.local/state/duplicati/server-watchdog.log`, `systemctl --user cat` |
| Log stores | the journal holds the 09-20 echoes in full (264 `LINE:` lines, 60 of them commented-out assignments, 12 + 12 export/key lines; 4 GB on disk); **`/var/log/syslog*` holds none** — 0 matches across all 15 files; `rsyslog` rotates daily and keeps 10, so the file that held the echoes was pruned about 10-01 | **S-3's syslog copy is gone by rotation**, not by any action (note 3c) | count-only `zgrep -c` per file; `journalctl --disk-usage`; `/etc/logrotate.d/rsyslog` |
| Destination | 877 files (434 dblock, 434 dindex, 9 dlist), newest `duplicati-20260918T140000Z` (mtime 09-18 09:12 CDT); every entry `pcalnon:duplicati 0770` (the `+` is Dropbox's xattr, `getfacl` shows base entries only); directories `drwxrwx---`; `sda1` ext4 3.6 T, 400 G used; Dropbox `Up to date`, its daemon without gid 139 | none | `ls`, `stat`, `getfacl`, `findmnt`, `dropbox status` |
| Escrow copies | **S-4** = `…/Dropbox/Backups/_yamaguchi_keys/env`, **`-rwxrwx--- pcalnon:duplicati`, 388 B, unchanged since 08-29 — still inside the Dropbox root, still not 0600**; no sibling at `/mnt/Backups/Ubuntu/_yamaguchi_keys/`. The scripts' credential file `~/.config/duplicati-backup/env` is a different file (0600, 519 B) | none (S-4's released `chmod 0600` **not** done; the first draft of this document closed it against the wrong file) | `ls -la` |
| S-7 | `…/worktrees/curious-plotting-hummingbird/.env` **still `0664`**, 114 B | none (P0.5a item 5 not done) | `ls -la` |
| T2 runner | `util/juniper-backup.bash` still `MOUNT_NAME="media"` → `/media/pcalnon/<UUID>`; udisks mounts under `/run/media/pcalnon/` since 09-07; **both sticks are attached** (`sdh1` = `EBC5-F0A3`, `sdf1` = `DFF3-2782`, exfat 239 G, Samsung) and **unmounted**; no `juniper-backup.*` user unit installed; `~/.local/state/juniper-backup/` absent (the scheduler has never run) | drives now attached | `lsblk`, `systemctl --user list-unit-files` |
| T3 | no drive configured, no fstab line, D-5 open. (A WD 3.6 T USB disk labelled `plex` is attached; nothing in the record names it as a backup target.) | none | `lsblk`, `/etc/fstab` |
| Tools | `sqlite3` and `gitleaks` **not installed** (P0 step 3 and AC-8 need them; Python's `sqlite3` module is present as a fallback for the `PRAGMA`s) | none | `which`, `python3 -c 'import sqlite3'` |
| Repository | D on `main` last changed 09-24 (#2067); its status line reads "VALIDATED (round 2)" and "§8 is executable in this order and no other"; §12 has no rows for #2029, #2041, #2057, #2067; the STOP, note 10.1g and the round-4 record exist only on the branch (note 3b); **no PR carries the branch**; ml#2109 (the handoff consolidation) merged 09:21Z | the branch is 9 days stale and un-pushed | `git log`, `gh pr list` |

Notes on the table:

- **(3a)** D §4.1 and the branch still describe `.env` as 0660 / 1,599 B / one active 32-char line. The `_OLD` value has exactly the length D records for that previous active key, and the directory's mtime (19:17:49) sits twelve seconds after the file write with no swap file left — this reads as an interactive edit that renamed the old key to `_OLD` and added a new 64-char one (an inference; it is O-1's question, answered as far as the host can answer it). The edit (00:17Z
  on 09-23) was made **24 minutes before** ml#2029's first commit and 87 minutes before its merge, so ml#2029 — which recorded that the new secret "does NOT go in `.env`" — did not know of it. `SETTINGS_ENCRYPTION_KEY_OLD` is read by nothing in 2.4.0.0 (§10.1 note b; 0 hits in either encoding across the installed assemblies) and kills wrapper v2 (§3.2). The five commented-out lines are the `PASSPHRASE_OLD`, `PASSPHRASE` and three settings-key assignments that S-3 is about.
- **(3b)** `worktree-typed-skipping-salamander` holds `2c9efe85`, `f90a87e7` and `2072e45a` over `6c23fdde` (#2077): 9 files, +3,256/−133, among them the design with the STOP block and note 10.1g, the round-4 record (rounds 4–8 verbatim) and the edit script `util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py`. The design file on `main` has not changed since that base, so the branch rebases clean. The 11 round reports' transcripts still exist under
  `~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/0a852d44-65ca-46ac-953b-84e8bae98e9c/subagents/` (22 files).
- **(3c)** D's S-3 remediation (P0.5a item 4, D-8 as amended) names both stores. The syslog half is now vacuous: D's own verification line, `sudo ls -la /var/log/syslog-2026092*`, lists only 09-24 to 09-30, and AC-8's syslog count can only ever read zero. The scrub that remains is journal-only. The `syslog.1–4.gz` files are a 2025-dated remnant of an older rotation scheme and hold nothing from 2026.

### 3.1 What changed since the 2026-09-24 handoffs

1. **The `.env` rewrite of 09-22 19:17 CDT** (two active keys, five commented secrets retained) is in no record (note 3a). Its effect on the next start is measured in §3.2.
2. **The three long-lived `duplicati`-uid sessions closed** by 09-24 14:56 (the `.bash_history` write). That was the one owner-side precondition of P0.5a item 7 (`nologin`). The branch's note sink-b records the closure; D on `main` does not. Both history files — root's and `duplicati`'s — are now the "one place left to look" for the 09-18 key (D §5.4), and the release's first limit (no history wiped before P0 step 3 tests it) is what protects them.
3. **The live wrapper is v2.** The primary checkout's file has matched `main` since 09-22 12:56. Wrapper v2 accepts the armed `--daemon-opts="…"` word as an unknown option and supplies its own `--webservice-port=8300` default, so the record's "neither wrapper revision can parse it" no longer describes the live symlink. The 0700 gate and the `.env` line do the refusing now.
4. **Both Tier 2 sticks are plugged in**, unmounted, under a runner that would not find them if they were mounted. Nothing in P3 has been started; P3's tier-2 fix was released on 09-24 (its step 3 waits on D-5).
5. **No released host action has run**: `/usr/lib/duplicati` and `/etc/default/duplicati` are still service-user-owned, `bin/` is still 0777, the shell is still `/bin/bash`, S-7 is still world-readable, the S-4 escrow is still 0770 and only inside Dropbox, `sqlite3` is still absent.
6. **The syslog copies of the 09-20 echoes rotated away** around 10-01 (note 3c). Nothing was scrubbed; the journal copy is intact.

### 3.2 The next-start failure, re-derived

Reproduced with wrapper v2 from `main`, a synthetic `.env` of the live file's **shape** (names only, dummy values, the `_OLD` line at its live position 22), a scratch data folder owned by the reader and `DUPLICATI_SERVER=/bin/true`, in `--print-command` mode:

| Case | Input | Result |
| --- | --- | --- |
| 1 | `.env` with `export SETTINGS_ENCRYPTION_KEY_OLD='…'` as the live file has | `FATAL: …:22: SETTINGS_ENCRYPTION_KEY_OLD is not an exportable name (allowed: ^(SETTINGS_ENCRYPTION_KEY\|DUPLICATI__[A-Z0-9_]+\|TMPDIR\|TZ\|LANG\|LC_ALL)$)`, **exit 78**, before any option is assembled |
| 2 | clean `.env` + the armed argv word `--daemon-opts="--webservice-port=8300"` | exit 0; would exec with `--webservice-interface=loopback --webservice-port=8300 --server-datafolder=… --daemon-opts=\"--webservice-port=8300\"` — the armed word is passed through as an unknown option, which 2.4.0.0 warns about and ignores (D §7.3.3) |
| 3 | clean `.env`, correct argv | exit 0, three options |

So on the live host: wrapper v2 exits 78 at `.env` line 22 **before** reaching `preflight()`; with `Restart=always` systemd retries until the start-rate limit. Were the `_OLD` line removed, the wrapper's own `preflight()` passes (folder exists, writable, owned by `duplicati`, `/mnt/Backups` mounted) and the **server's** data-folder gate then refuses the 0777 folder (D §5.5; the gate's name, `PrepareSecureDataFolder`, is in the installed Server assembly, and running it is the
one thing this session may not do). Two independent blockers, both closed by P0; neither is closed by anything that has happened since 09-24.

---

## 4. Gap analysis — documented, built, live

| Element | D specifies | Repository `main` has | Host runs |
| --- | --- | --- | --- |
| Unit | `/etc/systemd/system/duplicati.service`, confined, `Restart=on-failure`, `UMask=0027`, `LoadCredential=` | `util/systemd/duplicati.service` — byte-identical to its tagged block (the stage script reads `0 staged, 13 already current`) | the vendor unit edited in place, unconfined, `Restart=always`, no credential; the next package upgrade silently restores the upstream `ExecStart` with no `User=` — **demonstrated**: dpkg's recorded md5 equals the upstream text and the file is not a conffile |
| Defaults | `/etc/default/duplicati` root-owned, four options incl. `--server-datafolder`, **plus `--require-db-encryption-key`** (D-1) and D-9's two web-service options | `util/systemd/duplicati.default` — the require flag is **only in a comment** (STOP item 1); the D-9 options in no artifact | `duplicati:duplicati`, one option |
| Wrapper | installed copy, blessed checksum | `scripts/duplicati-wrapper.bash` v2, no credential-shaped literal, matches D §7.3.3; its `.env` default is still the data-folder path (D13 open) | symlink into the developer checkout from a 0777 directory |
| Installer | `util/install_duplicati_service.bash` with the D-6 drift gate | present; **exits silently with status 1 on a first install** — `blessed_for` returns 1 when no `.blessed.sha256` exists and `want="$(…)"` runs under `set -e` (reproduced; I-36) | never run |
| Settings key | random, in `/etc/credstore`, never in `.env` | wrapper reads `$CREDENTIALS_DIRECTORY/settings-key` first, `.env` second | in `.env`, twice, under names the product does not read for one of them |
| Data folder | `0700`, files `0600` | installer enforces it (and `install -d -m 0700` re-modes an existing 0777 folder) | `0777` / `0777` |
| Pre-backup guard | `--run-script-before-required` = installed guard | `util/yamaguchi-pre-backup-guard.bash` present | not installed; no job exists to carry the option |
| T0 | root-owned installed script, `ProtectSystem=strict` **with** `ReadWritePaths=` for its output dir, source = the new data folder | script present; unit has no hardening; STOP item 5: D's prescribed `strict` without `ReadWritePaths=` would break it | runs the checkout as root against the abandoned folder |
| Watchdog / API client | credential at `~/.config/duplicati-backup/web-credential`; `pause`/`resume`/`serverstate` verbs; explicit `--backup-id`; §7.6's `ProgramState` check | `yamaguchi_server_api.py` hard-codes the checkout `.env` (`CRED_FILE`, line 41); verbs are `status export abort delete import run progress log task` only (STOP item 3); `duplicati_api.py`'s `PW_FILE` defaults to the same `.env`; watchdog defaults `--backup-id 2` | alerting daily into a log nobody is paged by |
| Destination model | D-14 read-only form | `util/ad-hoc/2026-09-21_backup_destination_permissions.bash` present | 0770 group-write form; Dropbox daemon without gid 139 |
| T2 | `/run/media` or fstab roots; timer + path + scheduler + failure unit installed in `~/.local/bin` and user systemd | scheduler and three units present; installer `util/install_juniper_backup_timer.bash` and `juniper-backup-failure.service` **absent** (P3 deliverables); runner still `/media` | nothing installed; drives attached, unmounted |
| T3 | fstab-managed `/mnt/JuniperArchive`, monthly `full` set | nothing | nothing |
| Secrets | S-1 … S-8 remediated per §6 | the burned key literal is out of the wrapper (ml#1999); `.gitleaks.toml` is allowlist-only — no content rule, no pre-commit hook (P0.5a item 6) | journal unscrubbed (syslog copy rotated out, note 3c); `.env` still carries five commented secrets; S-4 and S-7 as on 09-21 |

---

## 5. Issues register

Severity: **P0** blocks recovery or risks the sole local copy; **P1** security exposure or a latent break of the recovered service; **P2** process/record defect that will mislead the next session; **P3** deferred by design. "Lane" names the validation lane that found an issue the first draft lacked (§8).

| ID | Sev | Issue | Evidence | Fix | Who | Phase |
| --- | --- | --- | --- | --- | --- | --- |
| I-1 | P0 | No tier has produced a backup since 09-18; T2 since 09-07; T3 never | §3 destination row, watchdog row, T2 row | §6 phases C–D (T1), B6 + C (T2), E (T3) | owner + session | C/D |
| I-2 | P0 | The empty server is the only thing running; the next start fails twice over (wrapper exit 78 on `_OLD`, then the 0777 gate) and `Restart=always` loops it | §3.2 | P0 step 2 stops it after step 1's freeze; the `.env` contract and `install -d -m 0700` close both | owner | D |
| I-3 | P0 | The service `.env` holds a key under a name the product never reads, keeps five commented secrets, sits inside the data folder where the service user can unlink-and-recreate it (D13), and no record knows it was rewritten (its `0640` mode is D's recommended contract; the dissent is O-12) | §3 `.env` row, note 3a | B8 moves it to `/etc/duplicati/env`; P0 step 9 writes the §7.3.5 contract there and shreds the old file; D §4.1 gets the 09-22 edit | session, owner | B, D |
| I-4 | P0 | The owner's STOP ruling and the round 4–8 record are not on `main`; `main` tells a reader §8 is executable | §3 repository row | Phase A | session | A |
| I-5 | P1 | `/usr/lib/duplicati` and `/etc/default/duplicati` are service-user-owned: the uid that will hold `CAP_DAC_READ_SEARCH` can replace the binaries root runs during recovery and rewrite its own argv | §3 rows | P0.5a item 1 — **released**, two commands | owner | C |
| I-6 | P1 | `duplicati` still has a login shell; the sessions that blocked item 7 are closed | §3 user row | `usermod -s /usr/sbin/nologin duplicati` — **released** | owner | C |
| I-7 | P1 | `/home/duplicati/bin` (0777) and `.config/Duplicati` (0777): any local user can rename-replace the wrapper or the database | §3 rows | item 1 removes `bin/`; P0 step 2 moves the folder aside and re-modes it | owner | C, D |
| I-8 | P1 | T0 snapshots the abandoned, key-locked database daily, as root, from a pcalnon-writable checkout, into a source nothing backs up; after P0 it would copy the **recovered** database — cleartext under A0 until the first start — into the next fileset (STOP item 4); `Persistent=true` fires on re-enable; a plain `stop` does not survive a reboot | §3 T0 row; STOP item 4; Lane B B-13 | B3; §6.4: `disable --now` first, `enable --now` after the first start has re-encrypted; O-10 | session, owner | B, D |
| I-9 | P1 | S-4: the passphrase escrow is synced to Dropbox beside the ciphertext, is `0770`, and the sibling copy outside the root does not exist | §3 escrow row | P0.5a item 5's copy-out in round 8's corrected form (§6.3 step 3) — **released**; the in-tree delete and "Delete forever" wait on P1 step 4 | owner | C, E |
| I-10 | P1 | S-7: a world-readable cleartext `.env` with both passphrases sits inside the backup source | §3 S-7 row | reconcile the fingerprints per D note S-7a, then remove the file (worktree stays, do-not-sweep) — **released** | owner | C |
| I-11 | P1 | S-3: the journal still carries the 264 echoed `.env` lines (60 of them secrets); the syslog copy has rotated away | §3 log-stores row, note 3c | D-8 as amended: one scrub, **journal-only now**, before P0 (P0.5a item 4, **held** until Phase B lands — note 10.1g); AC-8's syslog clause is vacuous and should say so | owner | D |
| I-12 | P1 | The watchdog and both API clients read the UI credential from the primary checkout's `0664` `.env` (S-5); no `pause`/`resume`/`serverstate` verbs; the watchdog defaults to backup id 2, which Procedure B would not reproduce; neither client checks `ProgramState` | §3 watchdog row; §4 | B2 | session | B |
| I-13 | P1 | `sqlite3` is absent (P0 step 3's `PRAGMA`/checkpoint, P0.5b's `VACUUM`); `gitleaks` absent (AC-8) | `which` | `sudo apt install sqlite3`; gitleaks via B9 | owner | C |
| I-14 | P1 | STOP 1: `--require-db-encryption-key` is in no shipped artifact; hand-adding it to `/etc/default/duplicati` trips the D-6 drift gate | `util/systemd/duplicati.default:4` (comment only) | B1: put the flag in `DAEMON_OPTS` in the repository copy, so the installer carries it | session | B |
| I-15 | P1 | STOP 2: P1 step 1 (run inside P0.5b) overwrites the credential file with the new key and then asks for a decrypt start "with the old key" — re-locks the database | D P1 step 1 text | B4: two files (`…-key` and `…-key.new`), swap after the decrypt start | session | B |
| I-16 | P1 | STOP 3: the API client has no `pause`/`resume`, so P0 step 10's guard dry-run can pass with an empty `TargetURL` | `util/ad-hoc/yamaguchi_server_api.py` | B2 | session | B |
| I-17 | P1 | STOP 4: `Persistent=true` on the snapshot timer fires a missed run the moment it is restarted | `util/systemd/yamaguchi-server-db-snapshot.timer:19` | ordering in §6.4 (re-enable only after the re-encrypting start is verified on a copy); no code change | session (checklist) | B/D |
| I-18 | P1 | STOP 5: D prescribes `ProtectSystem=strict` on the snapshot unit with no `ReadWritePaths=`; the unit writes under `~/.local/state` | `util/systemd/yamaguchi-server-db-snapshot.service` (no hardening yet) | B3 | session | B |
| I-19 | P1 | D-9's `--webservice-disable-signin-tokens` and §7.3.6's `--webservice-allowed-hostnames=localhost` are installed by no artifact. **The first is applied unconditionally at every start** (Server `Program.cs`) — it does not wait for a password, so D-9's "once a password exists" is an **order the procedure must keep** | branch STOP block; Lane B B-1 | B1 adds both to `DAEMON_OPTS`; §6.4 step 10 guarantees a known password before the unit's first start on every procedure | session | B, D |
| I-20 | P1 | T2 runner cannot find its drives (`/media` vs `/run/media`); no timer, path unit, scheduler or failure unit is installed; the installer does not exist | §3 T2 row; D §4.5, P3 | B6, then install (P3 steps 1–2 — **released**) | session, then owner | B, C |
| I-21 | P2 | D §4.1's `.env` row and §4.3 item 9's argv reasoning are stale (new facts); the status line, P1 step 5 / P2 step 2 wording, the missing §12 rows and "877 dindex volumes" are already repaired in the branch's edit script and land with Phase A | §3.1; the 09-24 handoff's items 4–5; Lane C | the two new facts go into the Phase B PR, which touches D anyway; the rest lands with Phase A | session | A, B |
| I-22 | P2 | The paused branch's round-8 to-do list is not all cosmetic: its item 1 (the §5.3 no-print caveat), item 4 (rebuild D through the edit script so D and the script agree) and the corrected text of P0.5a item 5 are substantive; landing the WIP commits without the rebuild would put a design on `main` that its own edit script changes on re-run | the D-8 handoff "Still to do"; Lane C rows 2, 4, 5 | Phase A executes the consolidated handoff's sub-steps 1a–1h as written | session | A |
| I-23 | P2 | `MEMORY.md` said `sda` was never SMART-tested (two lines); it passed on 2026-09-23 (ml#2041). The memory's 09-22 section still reads "D-8 scrub once, after P1" (amended 09-24 to one scrub before P0), and three reference files are unlinked from the index | memory index; the D-8 handoff "Memory" | the two lines and a 2026-10-03 section were fixed at 09:02Z (after this document's measurement, before the round reported); the D-8 line and the three links remain | session | A |
| I-24 | P3 | D-3, D-5, D-7, D-10, D-11, D-12 open; D-5 gates P3 step 3 (T3); D-13 (Dropbox root policy) is in §7.3.2's confinement set | D §10 | §6.6 | owner | E |
| I-25 | P3 | The vendor unit edited in place is restored by the next `duplicati` package upgrade; harmless once `/etc/systemd/system/duplicati.service` exists (it shadows the vendor file) | `dpkg -V`, dpkg md5 vs upstream | P0 step 9's installer; then `sudo dpkg --verify` after each upgrade | — | D |
| I-26 | P1 | D13: wrapper v2's `.env` default is the data-folder path; D §7.3.5 requires `/etc/duplicati/env` in a `0755 root:root` directory; the STOP's exit condition names it | branch note 12a; Lane C row 3; Lane B B-6 | B8 | session | B |
| I-27 | P1 | `InaccessiblePaths=` masks the escrow inside the Dropbox root but not the sibling copy Phase C step 3 creates at `/mnt/Backups/Ubuntu/_yamaguchi_keys/` | `util/systemd/duplicati.service`, the `InaccessiblePaths=` line; branch STOP "beside the five" | B1 adds the path (one token) | session | B |
| I-28 | P1 | `--disable-db-encryption` **satisfies** `--require-db-encryption-key` (Server `Program.cs`) and suppresses the "unencrypted database" notice, so a leftover flag decrypts the database silently on every later start and AC-14 cannot see it; in `/etc/default/duplicati` it trips D-6 forever | Lane B B-10 | B4 delivers the flag through a runtime drop-in the re-key script itself removes; exit gate = `encrypted-fields` True **and** no drop-in | session | B |
| I-29 | P1 | The old `.env` (two keys, five commented secrets) survives in the moved-aside 0777 folder until P4 | Lane B B-12; round-4 record B16 | §6.4 step 9 shreds it and re-modes the moved folder 0700 | owner | D |
| I-30 | P3 | S-3c: after the §10.2 rotation, the frozen set `_yamaguchi_frozen_20260826/` (811 volumes) and the ten old-archive dlists stay under the leaked passphrases | branch note S-3c; Lane C row 6 | O-9 | owner | E |
| I-31 | P1 | The TestPyPI token that a 09-21 validator harness captured into a cloud-linked transcript has never been recorded as rotated; dropped by every document since | 09-21 handoff §1.5 item 1; Lane C row 15 | O-11 | owner | C |
| I-32 | P2 | The §7.3.2 confinement set has never run against 2.4.0.0 on this host (D's O-12, AC-12a); `ProcSubset=pid` and `RestrictAddressFamilies` are its named likely failures; a crash after the schema upgrade and password upgrade have committed loops five times and the only mid-session fix is a hand edit that trips D-6 | Lane B B-4 | §6.4 step 0 rehearses the set with `systemd-run` against a scratch copy, `SystemCallErrorNumber=` unset, before the real first start | owner | D |
| I-33 | P2 | `util/ad-hoc/2026-09-22_stage_design_artifacts.py` without `--check` writes D's tagged blocks **over** the repository files; after Phase B changes an artifact, "N staged" would be read as drift and the documented remedy would revert the fix | Lane B B-5 | B7 re-extracts every changed artifact into its tagged block, or retires the script's write mode now that the repository is canonical | session | B |
| I-34 | P2 | `--aes-version` is unpinned; the 877 volumes are v2 and 2.4.0.0's default is v3, so the first post-recovery run would change the on-disk format by omission — the one outcome §7.5 says must be a recorded choice | Lane B B-7; D §7.5 | §6.4 step 11 pins it (O-14 picks the value) | owner | D |
| I-35 | P2 | `additional-report-url` (S-8) survives A0 and, under `IPAddressDeny=any`, its POST fails and the run logs report warnings — AC-3's bare `Warnings=0` would fail for a reason unrelated to the backup | Lane B B-8 | read both report URLs before the run; allow-list that warning or get the owner's ruling on the deferred URL (O-13) | owner | D |
| I-36 | P1 | **The installer cannot complete a first install**: with no `.blessed.sha256`, `blessed_for` returns 1 and `want="$(blessed_for …)"` under `set -euo pipefail` exits the script with status 1 and no message, before any `install`, `daemon-reload` or bless (reproduced on a scratch path; Lane B B-3) | `util/install_duplicati_service.bash`, the `blessed_for` helper and its call | B3: `want="$(blessed_for "${dst}" \|\| true)"`; Phase B's dry run must exercise the no-blessed-file path | session | B |
| I-37 | P0 | **Procedure A2 loses the UI password** (note 5a): `wipe-encryption` clears `pbkdf-config`, the only home of the UI password since 2.1; the first start then mints a random password, and with I-19's flag installed no signin token is accepted either; D §8 step 6 says the opposite | Duplicati `v2.4.0.0_stable` source; Lane B B-1 | A0 is the default; A2 and B get a password-init hand start before the unit's first start (§6.4 step 10); D step 6 corrected in B7 | session, owner | B, D |
| I-38 | P1 | On Procedure A (a matched 09-18 key), writing a fresh random key to the credential path before the first start re-locks the folder (`SettingsEncryptionKeyMismatchException`, exit 100, five restarts) | Lane B B-2; D step 5 | §6.4 step 9: on a match the accepted key goes to `…-key` and the random key to `…-key.new` | owner | D |
| I-39 | P2 | An indefinite API pause is persisted (`paused-until`) and restored across restarts and reboots; a session that ends between `pause` and `resume` reproduces the 42.6 h class the record already had once | Lane B B-14 | B2 adds the `ProgramState` check; §6.4 step 11 ends with `serverstate` reading Running | session, owner | B, D |
| I-40 | P2 | Until the new settings key is escrowed, its only copy is one 0600 file on `nvme0n1p5` that no backup covers, while the database it unlocks is already in the backup source | Lane B B-15 | §6.4 step 9 escrows (sheet, manager, `sda1` sibling) before step 10 and verifies by hash | owner | D |
| I-41 | P3 | Items the branch's rounds listed that this plan carries only by reference (note 5b) | Lane C rows 17, 21, 24, 31, 33, 35 | the consolidated handoff's inventory is the carrier; B7 records them as residue in the cleared-STOP note | session | B, E |

Notes on the register:

- **(5a)** Read in the Duplicati `v2.4.0.0_stable_2026-09-03` source by validation Lane B and re-read by the author: `Connection.PasswordFieldNames` includes `pbkdf-config`; `WipeEncryption` clears every `Option.Value` in that set that is `enc-v1:` (and the root database encrypts every password-named setting on every save, so the field is `enc-v1:` there); `ServerSettings.VerifyWebserverPassword` returns false when `pbkdf-config` is empty; `UpgradePasswordToKBDF` mints a
  random password and sets `autogenerated-passphrase=True` when `server-passphrase` is null — which it is since 2.1, because the upgrade nulls it; `DisableSigninTokens` is written from the option unconditionally.
- **(5b)** Appendix C's unapplied corrections (item 4 is the snapshot script's docstring, which B3 touches), round-4 B11/B13/B14/B15/B24/B27/U1/U3, the Dropbox account audit after "Delete forever", Procedure B's statement on `additional-report-url` (S-8), the sdc4 read-only loop probe and the frozen evidence mirror (D-12a).

---

## 6. Plan

### 6.0 Principles for the rest of this arc

1. **Execution over elaboration.** D is not edited further except to (a) land the owner's ruling, (b) clear the STOP once the artifacts carry the fixes, (c) correct the stale facts in I-21 and the wrong sentence in I-37, (d) re-extract changed tagged blocks (I-33). No new design sections.
2. **A procedure defect is fixed in the artifact that would execute it**, and the artifact is what gets validated. Prose that says "do X before Y" is replaced, wherever possible, by a script or unit that cannot do Y first.
3. **The owner's time is the scarce resource.** Everything the owner must do is collected in two lists — Phase C (twenty minutes, no passphrase, can happen today) and Phase D (one sitting, passphrase in hand) — with nothing else interleaved.
4. **Consensus is spent where a wrong line damages the sole local copy** — the Phase B artifact PR and the Phase D checklist — and nowhere else (§6.7).
5. **Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved** except the one escrow copy, on owner sign-off, in P1 step 4. The server is stopped once, by P0 step 2, after step 1's freeze — never restarted before step 10.
6. **No session runs a Duplicati binary, reads a secret file or greps a log for values.** Rehearsals that need a binary are the owner's, on a throwaway data folder (§6.4 step 0).

### 6.1 Phase A — put the owner's ruling on `main` (session, one sitting)

1. Execute the consolidated handoff's **step 1, sub-steps 1a–1h**, as written there: the §5.3 no-print caveat (1a), the round-numbering (1b) and STALE-phrase (1c) edits in the edit script, the **rebuild** of D from `6c23fdde` through the script until it reports "no change" and `--self-test` passes 8 of 8 (1d), the round-4 record's header (1e), the gates (1f), the PR/commit bodies (1g), and the signed PR from current `main` (1h). This lands: D with the STOP block and note
   10.1g; the round-4 record; the edit script and archiver; the SMART-script refactor the owner adopted (mode not adopted).
2. **Validation**: one narrow lane on the round-8 delta (the consolidated handoff's step 2 — the SOP requires it because the owner's sweeper arms open PRs): confirm the eleven reports are verbatim against the transcripts (note 3b), that the STOP block's held/released lists quote the owner's words, and that the rebuilt D equals the script's output. No consequence lens: the PR changes no artifact that runs.
3. This document lands in its own PR, with §8 filled, and the consolidated handoff's "READ FIRST" banner is updated to point at it on `main`.
4. Memory: the remaining half of I-23 (the D-8 line in the 09-22 section; link `reference_uutils_ls_plus_is_any_xattr.md`, `reference_soft_reset_to_a_moving_ref_stages_a_revert.md`, `reference_a_ruling_made_from_a_stale_recommendation_column.md`).
5. **Merging the round-4 record discharges the release's second limit** (no transcript purged before every round's report is archived on `main`) — say so in the PR body, so the owner knows when the transcript sink may be purged.

### 6.2 Phase B — close the STOP defects and the new artifact defects, in code (session, one PR, one three-lane round)

| # | Change | File(s) | Closes |
| --- | --- | --- | --- |
| B1 | `DAEMON_OPTS` gains `--require-db-encryption-key --webservice-disable-signin-tokens --webservice-allowed-hostnames=localhost` (all three present in the 2.4.0.0 Server assembly; an IP-literal `Host` is always allowed, so loopback clients cannot be locked out); the recommending comment goes. The unit's `InaccessiblePaths=` gains `-/mnt/Backups/Ubuntu/_yamaguchi_keys` | `util/systemd/duplicati.default`, `util/systemd/duplicati.service` (and their tagged blocks, I-33) | I-14, I-19, I-27 |
| B2 | `CRED_FILE` → `~/.config/duplicati-backup/web-credential` (0600, operator-rotated) in both clients; add `serverstate`, `pause`, `resume` verbs; `--backup-id` mandatory on anything job-scoped; the watchdog reads the same file and checks `ProgramState` and the scheduler queue (§7.6) | `util/ad-hoc/yamaguchi_server_api.py`, `util/ad-hoc/duplicati_api.py`, `util/ad-hoc/yamaguchi_watchdog.py`, `util/ad-hoc/yamaguchi_watchdog_deploy.bash` | I-12, I-16, I-39 |
| B3 | Snapshot lane hardened and installed (note 6d): the unit runs the installed copy under `ProtectSystem=strict` with `ReadWritePaths=` on its output directory; the script reads the new data folder; the installer carries both under the blessed-checksum gate, fixes its first-install bug (note 6c) and gains `--dry-run` | `util/systemd/yamaguchi-server-db-snapshot.service`, `util/ad-hoc/yamaguchi_server_db_snapshot.py`, `util/install_duplicati_service.bash` | I-8, I-18, I-36 |
| B4 | A re-key script for Procedure A only (note 6a): refuses to run with the server active or a backup in progress; pauses the scheduler first; the decrypt start runs under a runtime drop-in that appends `--disable-db-encryption`, old key in place, new key at `…-key.new`; one `mv` swaps them; the encrypt start runs with the drop-in reverted; exit gate = `encrypted-fields` True and no drop-in; then `resume` | `util/ad-hoc/2026-10-0X_rekey_settings_key.bash`, D P1 step 1 / P0.5b | I-15, I-28, I-38 |
| B5 | `.env` contract made testable: a `tests/` case runs the wrapper in `--print-command` mode against the §7.3.5 contract file (expect exit 0), against a file with a commented assignment (expect the AC-8 count non-zero) and against one with `_OLD` (expect exit 78), plus its line in `.github/workflows/ci.yml` (the suite list is hand-maintained; `tests/test_ci_test_wiring_drift.py` fails otherwise) | `tests/test_duplicati_wrapper_contract.py`, `.github/workflows/ci.yml` | I-3 |
| B6 | T2: `MEDIA_NAMES` entries beginning with `/` are absolute mount roots; default root `/run/media/pcalnon`; `util/install_juniper_backup_timer.bash` copies runner, scheduler and failure reporter into `~/.local/bin/` and installs the three user units plus `juniper-backup-failure.service` | `util/juniper-backup.bash`, `util/install_juniper_backup_timer.bash`, `util/systemd/juniper-backup*.{timer,path,service}` | I-20 |
| B7 | D: the STOP block becomes a dated "cleared by ml#NNNN" note that lists, as owner-accepted residue, every round-4–8 follow-up this phase does not implement (I-41); D §8 step 6's "the UI password survives" sentence is corrected (I-37); the two new facts of I-21 are recorded; every tagged block whose artifact changed is re-extracted (I-33) | D | I-4, I-21, I-33, I-37, I-41 |
| B8 | D13: wrapper v2's `DUPLICATI_ENV_FILE` default → `/etc/duplicati/env`; the installer creates `/etc/duplicati` `0755 root:root` and installs the contract file `0640 root:duplicati` **if absent** (never overwriting an operator's tunables); §7.3.5's tagged block names the new path | `scripts/duplicati-wrapper.bash`, `util/install_duplicati_service.bash`, D §7.3.5 | I-3, I-26 |
| B9 | P0.5a item 6 (released, repository-only): a gitleaks **content** rule for `(SETTINGS_ENCRYPTION_KEY\|PASSPHRASE(_OLD)?\|DUPLICATI_WEB_CREDENTIAL\|webservice-password\|passphrase)=` with a non-placeholder value, a gitleaks pre-commit hook, and `secret_scanning_non_provider_patterns` on the repository | `.gitleaks.toml`, `.pre-commit-config.yaml`, repository settings | I-13 (gitleaks half) |
| B10 | A password-init helper for the A2 and B paths (note 6b): builds a `0600` parameters file in-process carrying the new settings key and `--webservice-password-init=<new UI password>`, runs the server once by hand as `duplicati` with `--parameters-file` on an unused loopback port, expects **exit 102**, shreds the file, and verifies `autogenerated-passphrase=False` and `encrypted-fields=True` on a copy | `util/ad-hoc/2026-10-0X_password_init_hand_start.bash` | I-37 |
| B11 | A no-print key-candidate extractor for P0 step 3, built only if Phase C step 5's counts are non-zero: writes candidates from a history file to a 0600 file and prints a count | `util/ad-hoc/2026-10-0X_history_key_candidates.py` | the release's first limit |

Notes on the changes:

- **(6a)** B4's details: an indefinite API pause is persisted across both starts, which is why it is taken first (an overdue schedule is queued at every start — Lane B B-9); the drop-in lives in `/run/systemd/system/duplicati.service.d/` and is removed with `systemctl revert`, so nothing durable carries `--disable-db-encryption` (I-28); D's P1 step 1 and P0.5b text point at the script.
- **(6b)** B10's details: both secrets are read from 0600 files, never argv, never the environment; the hand start passes `--server-datafolder=<new folder> --parameters-file=<file> --webservice-interface=loopback --webservice-port=<unused>`. Exit 102 is returned only when the stored password is autogenerated; on a database that already has a real password — A0 — the option returns 103 and changes nothing, which is why A0 does not use this helper.
- **(6c)** The installer's `blessed_for` helper returns 1 when no `.blessed.sha256` exists, and `want="$(blessed_for …)"` under `set -euo pipefail` ends the script there with no message (I-36). The fix is `want="$(blessed_for "${dst}" || true)"`, and the dry run must cover the never-blessed path, which is this host's.
- **(6d)** B3's unit directives: `ExecStart=/usr/bin/python3 /usr/local/lib/duplicati/yamaguchi_server_db_snapshot.py`, `ProtectSystem=strict`, `ProtectHome=read-only`, `ReadWritePaths=/home/pcalnon/.local/state/duplicati-server-db`, `PrivateTmp=yes`. The script's `SRC` becomes `/home/duplicati/.config/Duplicati/Duplicati-server.sqlite` and its docstring drops the unconditional "encrypted passphrase" claim (Appendix C item 4).

B6 and B9 are independent of the rest and may ship first as their own PRs — B6 is the fastest route to *any* backup running (the sticks are plugged in).

**Validation**: one round, three lanes, on the B1–B5/B7/B8/B10 PR: (a) re-probe every option name against the installed assemblies with `util/ad-hoc/2026-09-22_duplicati_literal_scan.py` and every unit directive with `systemd-analyze verify`; (b) consequence lens on the §6.4 checklist with these artifacts in hand — "find the step that damages the sole copy, re-locks the database, or leaves the server unreachable"; (c) the installer, the re-key script and the password-init
helper run as a non-root `--dry-run` against a scratch tree, **including the no-blessed-file path**. Round N+1 only if round N refutes something, scoped to the delta. What a dry run cannot see — the product's behaviour on a real start — is rehearsed by the owner in §6.4 step 0.

### 6.3 Phase C — the released host actions (owner, ~20 minutes, no passphrase, no Duplicati binary run)

All of these were released by the owner on 2026-09-24 (note 10.1g) and none has run. In this order:

1. **P0.5a item 1** — `sudo chown root:root /usr/lib/duplicati; sudo find /usr/lib/duplicati -mindepth 1 -maxdepth 1 ! -name data -exec chown -R root:root {} +; sudo chown root:root /etc/default/duplicati; sudo rm -r /home/duplicati/bin` (the directory holds only the symlink; the running server does not re-read it). Expect **96** directories to change owner (95 below the top plus the top itself) and 21 to be no-ops; D's "97" counted `data/` and its subdirectory, which the command excludes by design.
2. **P0.5a item 7** — `sudo usermod -s /usr/sbin/nologin duplicati`. The shells that blocked it are closed (§3.1 item 2). `sudo -u duplicati <command>` keeps working.
3. **P0.5a item 5, in round 8's corrected form** — (a) reconcile the S-7 fingerprints per D note S-7a (`HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §1 item 8; compare, never print), **then** `rm …/worktrees/curious-plotting-hummingbird/.env` (the file only); (b) **S-4's released chmod**: `chmod 0600 /mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_keys/env`; (c) the copy-out: `test ! -e /mnt/Backups/Ubuntu/_yamaguchi_keys` first (`cp -a` into an existing directory
   nests), then `cp -a /mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_keys /mnt/Backups/Ubuntu/_yamaguchi_keys`, `chmod 0700` the copy and `0600` its files (`cp -a` carries the 0770), and compare `sha256sum` on both sides. **Do not delete the in-tree copy** — that is P1 step 4, held.
4. `sudo apt install sqlite3` (I-13).
5. **Count-only history probe**, never printed, never wiped: `sudo grep -c -i -e encryption -e passphrase -e password -e dbpath /root/.bash_history /root/.viminfo /home/duplicati/.bash_history /home/duplicati/.viminfo`. A non-zero count means P0 step 3 has candidates to extract (B11) and test offline; `dbpath` also catches the 2026-08-25 Repair actor D §5.3 asks about.
6. **The released read** `sudo ls -la --time-style=full-iso /usr/lib/duplicati/data/`: a `-wal`/`-shm` dated 09-18 21:03 means the main file may still hold the pre-encryption cleartext — a second key-free recovery source (D §4.2 note 1).
7. **The rest of §6's sink checklist** (released): the CUPS spool row, `chmod 0600` on the world-readable job-database copies, and the transcript **count** — purge nothing until Phase A's record has merged (the release's second limit).
8. Once B6 has merged: `bash util/install_juniper_backup_timer.bash`, then per AC-10 one run with no stick mounted (`SKIPPED`), one with a stick mounted (`OK`, verified archives) and a class-1 drill — the first Tier 2 archive since 08-28, and the first backup of any kind the host will have made since 09-18. It needs nothing from P0.
9. If O-10 is ruled yes: `sudo systemctl disable --now yamaguchi-server-db-snapshot.timer` today.

Still **held** by the owner's own ruling until Phase B lands and clears the STOP: P0.5a items 2 and 4, P0, P0.5b, P1, P2, P4.

### 6.4 Phase D — the P0 recovery session (owner with `sudo` and the escrowed passphrase, one sitting)

A checklist against D §8's step numbers. Only the deltas from D are spelled out; everything else is "as D says". Before starting: Phase B merged and the STOP cleared; Phase C done; the passphrase from the printed sheet or the password manager, **not** the Dropbox copy.

0. **Rehearsal on a throwaway data folder** (owner; the first time any of this runs a binary on this host): in a scratch `0700` folder with an empty database, (a) the password-init helper against `--server-datafolder=<scratch>` on an unused port — expect exit 102 and `autogenerated-passphrase=False` on the copy; (b) a `systemd-run` trial of the unit's full property set with `SystemCallErrorNumber=` unset, against the same scratch folder — the server must reach `Server has
   started`; a directive it cannot run under is removed **and recorded** (AC-12a), never left to be discovered at step 10. This is also where D's O-2 question (token minting without `--password`) is settled if B2 still needs it.
1. `sudo systemctl disable --now yamaguchi-server-db-snapshot.timer` (not `stop`: a reboot would re-fire a persistent timer). It stays disabled until step 13. The installer runs at step 9, not here — it refuses while the data folder is 0777 and the unit it installs must not be loaded while the old process runs.
2. **P0.5a item 4** (D-8 as amended): **journal-only** scrub (`--rotate` + `--vacuum-time=1s`); verify with the AC-8 journal counts. The syslog copy is already gone (note 3c).
3. **P0 step −1**: `python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py --check` must print `0 staged` (after B7 re-extracted the changed blocks); read the scripts that will run.
4. **P0 step 0(a)**: `grep -c -- --require-db-encryption-key /etc/default/duplicati` = 1 after step 9; the `.blessed.sha256` will list six paths (wrapper, unit, defaults, guard, snapshot script, snapshot unit).
5. **P0 step 1** — freeze: `sudo cp -a /usr/lib/duplicati/data /home/duplicati/.cache/root-data-folder-$(date +%F)` and copy today's snapshot aside with a `.recovery-<date>` suffix **before 13:45 UTC**, which replaces it. Note the freeze directory's date in `YAMAGUCHI_JOB_DB` for the A0 script — its default hard-codes `root-data-folder-2026-09-22`.
6. **P0 step 2** — `sudo systemctl stop duplicati.service` (not restart); `sudo mv /home/duplicati/.config/Duplicati /home/duplicati/.config/Duplicati.empty-2026-09-20; sudo chmod 0700` the moved folder. Its `.env` still holds both keys and the five commented secrets (I-29) — step 9 shreds it.
7. **P0 step 3** — the offline key-hash probe over the freeze copy, with every candidate B11 extracted from the histories (one candidate per 0600 file, on stdin, never argv). A match → **Procedure A** (D step 5). No match, the expected case → **Procedure A0** (D step 4): restore the cleartext server database from `duplicati-20260918T140000Z` with `--dbpath` on a throwaway copy of the index; this keeps the root-era UI password (`pbkdf-config` in cleartext) and the job as it
   was. **A2 is the fallback only if the 09-18 fileset cannot be read**, and then step 10's helper is mandatory (I-37).
8. **Procedure B** is the last resort; it starts no server before step 9's installer has run, and its rebuild must state whether it re-creates `additional-report-url` (S-8).
9. **P0 step 8** — place the database (`install -d -m 0700`, `install -m 0600`), move `BMXWPAOGLP.sqlite` in, **re-point `Backup.DBPath`** (stored absolute; `sqlite3` from Phase C); run `sudo bash util/install_duplicati_service.bash` (now that the folder is 0700 and the old unit is stopped) — it installs the unit, wrapper, defaults, guard, snapshot script and unit, writes `/etc/duplicati/env` if absent (B8), blesses six paths; write the settings key: **A0/A2/B** — `umask
   077; openssl rand -base64 48 \| tr -d '\n' \| sudo tee /etc/credstore/duplicati-settings-key >/dev/null; sudo chmod 0600 …`; **Procedure A** — the accepted key to `…-key` and the random one to `…-key.new` (I-38). **Escrow the new key now** (sheet, manager, `sda1` sibling) and verify by hash (I-40). Confirm `/etc/duplicati/env` has no key line and no commented assignment; `shred -u` the old `.env` in the moved-aside folder.
10. **Make a known UI password exist before the unit starts** (I-19, I-37): **A0** — the root-era password (the S-5 value) is in the restored database; nothing to do until step 11. **A2 / B** — run the B10 helper: one hand start with the parameters file, exit **102**, `autogenerated-passphrase=False` and `encrypted-fields=True` verified on a copy. Then `sudo -u duplicati /usr/local/lib/duplicati/duplicati-wrapper.bash --print-command` (dry run) and `sudo systemctl start
    duplicati.service`; `journalctl -u duplicati.service --since <ts>` shows `Server has started`, zero `Unknown option supplied` (AC-14) and no encryption warning. On A0/A2/B this start encrypts the placed database under the **new** key, which is why **P0.5b is not needed on those paths** (the database was never under a compromised key in the new folder; S-1 and S-2 never touch it). It stays needed on Procedure A only (O-7).
11. **P0 step 9** — log in (A0: the S-5 value; A2/B: the password from step 10), **change the password** through the UI, write `~/.config/duplicati-backup/web-credential` (0600), retire the S-5 line from the primary checkout's `.env`; `python3 util/ad-hoc/yamaguchi_server_api.py serverstate` works. **P0 step 10** — `pause`; fix `--tempdir`; **pin `--aes-version`** (O-14; I-34); read both report URLs and decide I-35; guard dry-run must pass **with** a non-empty `TargetURL`;
    `resume`; end with `serverstate` reading Running (I-39).
12. **Procedure A only**: P0.5b's two-start re-key with B4's script (pause spanning both starts, runtime drop-in, key swap, exit gate). Round-4 B15 and U1 apply here (the AC-12 trial target; whether the decrypt start logs values — check the journal count).
13. **Verify re-encryption on a copy** (`encrypted-fields` True, the `enc-v1:` key hash equals the credstore key's), then `sudo systemctl enable --now yamaguchi-server-db-snapshot.timer` (I-17: `Persistent=true` fires it at once, and now it copies an encrypted database into the source).
14. **P0 step 11** — AC-2; one backup (AC-3, with the `~/.ssh` / `~/.gnupg` positive finds; `Warnings` read with I-35 in mind); the two AC-4 drills (the first from `duplicati-20260918T140000Z`, which discharges §10.2 step 1 and unblocks the rotation); AC-12, AC-13. AC-1 at +24 h; AC-6 at the next 13:45 UTC.

### 6.5 Phase E — after recovery, in D's own order

1. **P1** — `/etc/duplicati/env` already at contract (step 9 above); S-4's in-tree delete and dropbox.com "Delete forever" on owner sign-off, then the **account audit** (2FA, linked devices, third-party apps, retention — D note S-4a); the user-lane removal PR owed since 08-30 (P4 step 4, nothing waits on it).
2. **P2** — D-14 destination permissions via the landed script (scratch directory on `sda1` first, Dropbox idle; the destination's `+` is an xattr, not an ACL); restart Dropbox in a session carrying gid 139 (AC-7); watchdog redeploy with the explicit backup id (AC-5); `systemd-analyze security` ≤ 2.0 (AC-12); reboot test (AC-9).
3. **§10.2** — the D-2 rotation: `recompress --reencrypt` on a staging copy under `/` (`nvme0n1p5`, 357 G free against ~203 G), verified, then swapped; the new passphrase to `/etc/credstore`, never `.env`; after AC-4's first drill has passed; O-9 decided first.
4. **P3 remainder** — D-5 ruling, T3's fstab line and first `full` set, AC-10/AC-11 drills.
5. **P4** — after seven consecutive successful daily runs: archive and remove `/usr/lib/duplicati/data` (encrypted, per D), remove the copied job databases (D-7), `Duplicati.empty-2026-09-20`.

### 6.6 Decisions the owner must make

| # | Decision | Recommendation | Gates |
| --- | --- | --- | --- |
| O-1 | The 09-22 `.env` rewrite: was the 64-char key meant as the new settings key, and `_OLD` as the previous one (note 3a's reading)? | Treat both as superseded: the settings key becomes the random credstore value of §6.4 step 9 and the `.env` carries none. If the 64-char value is escrowed anywhere as "the key", retire that entry. | D step 9 |
| O-2 | Recovery path. The first draft proposed A2 over A0; validation refuted it (I-37). | **A0**, as D ranked it; A2 only if the 09-18 fileset cannot be read, and then with the B10 helper. | D step 7 |
| O-3 | The release's phrase. The D-8 handoff quotes the owner as "Read-only steps may run"; the branch's note 10.1g paraphrases it as "only reads" and reads it narrowly. | Confirm the phrase. No widening is needed for P0 step 0(c): it depends on step 1's freeze anyway, so it runs inside P0 regardless of the reading. | A |
| O-4 | Disposition of the paused branch: land it after the mechanical rebuild (this plan) vs. drop it | land | A |
| O-5 | D-3, D-5 (T3 content), D-7, D-10 (T2 cadence/retention), D-11, D-12, D-13 (Dropbox root policy) | D's recommendations stand; none gates P0 | E |
| O-6 | Merge approval for the Phase A and Phase B PRs (the 09-24 session's approval covered that session's PRs only) | — | A, B |
| O-7 | P0.5b's fate (the STOP's open question) | needed on Procedure A only; not needed on A0/A2/B (§6.4 step 10) | D |
| O-8 | The D-1 flag's durable home | B1: in the repository's `DAEMON_OPTS`, so the installer carries it and the drift gate protects it | B |
| O-9 | S-3c: the frozen 811-volume set and the ten old-archive dlists after the rotation — re-encrypt as a second pass, move and delete-forever, or accept in writing | re-encrypt as a second pass of §10.2, same staging rules | E |
| O-10 | Release P0.5a item 2's timer stop on its own, today? The timer runs the primary checkout's script as root daily and snapshots a dead configuration | yes — `disable --now`; the snapshot's only remaining value is as a recovery source, which §6.4 step 5 copies aside | C |
| O-11 | Rotate the TestPyPI token captured into a 09-21 transcript (I-31) | rotate; it is a release-path credential and touches no workflow (CI publishes by OIDC) | C |
| O-12 | `.env` mode: `0640 root:duplicati` (D's recommendation; the service user cannot rewrite its own tunables) vs `0600 duplicati:duplicati` | 0640 root-owned, at `/etc/duplicati/env` (B8) | B |
| O-13 | S-8: keep `additional-report-url` (the deferred cloud report) and allow-list its warning under `IPAddressDeny=`, or clear it | clear it until a reporter exists; record the bearer JWT as retired | D |
| O-14 | `--aes-version` pin for the first post-recovery run: 2 (the format of the 877 existing volumes) or 3 (2.4.0.0's default) | 2 until §10.2 rewrites every volume anyway; move to 3 in the rotation and record it | D |

### 6.7 Where consensus validation is spent, and where it is not

- **Spent**: the Phase B artifact PR (three lanes, §6.2) — these files are what root executes against the sole copy; and this document's §3/§5/§6 before it landed (§8), because a wrong fact here redirects the owner's two hours — which round 1 showed it would have (I-37).
- **Not spent**: the Phase A record PR beyond its one verbatim/rebuild lane; the I-21 fact repairs; memory edits. A second round on any of these would cost more than the defects it could find.
- **Rule for the rest of the arc**: a round is launched only on an artifact that is frozen for its duration, with lanes told to pin a hash and cite by heading; a reconciliation gets its own narrow round only if it changed a step that runs on the host.

---

## 7. Verification commands

```bash
# Host (read-only; none starts, stops or restarts anything)
systemctl show duplicati.service -p ActiveState,MainPID,NRestarts,NeedDaemonReload,FragmentPath   # active, 1397393, 0, no, /usr/lib/...
journalctl -u duplicati.service -n 1 -o short-iso --no-pager                                       # 2026-09-20T18:51:33-05:00 ... (nothing since)
ls -ld /home/duplicati/.config/Duplicati /home/duplicati/bin /usr/lib/duplicati                     # 0777, 0777, duplicati:duplicati until Phase C
stat -c '%A %U:%G %s %y' /home/duplicati/.config/Duplicati/.env                                   # -rw-r----- duplicati:duplicati 1701 2026-09-22 19:17
getent passwd duplicati | cut -d: -f7                                                              # /bin/bash until Phase C step 2
ls -la /mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_keys/env                                     # -rwxrwx--- ... 388 until Phase C step 3
ls /mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi | wc -l; ls /mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi | grep dlist | tail -1   # 877; ...20260918T140000Z
tail -1 ~/.local/state/duplicati/server-watchdog.log                                               # ALERT ... 401 until P0 step 11
lsblk -o NAME,FSTYPE,LABEL,MOUNTPOINT | grep -E 'EBC5-F0A3|DFF3-2782'                              # attached, no mountpoint
which sqlite3 gitleaks                                                                              # nothing until Phase C step 4 / B9
# Secret-echo copies (count-only; the journal still holds them, syslog does not)
journalctl -u duplicati.service --since 2026-09-20 --until 2026-09-21 --no-pager -q | grep -c 'LINE: "'   # 264 until P0.5a item 4
# Repository
git log origin/main --oneline -1 -- notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md   # dcfc024f until Phase A
git log --oneline origin/main..worktree-typed-skipping-salamander | wc -l                          # 3 until Phase A
grep -c 'require-db-encryption-key' util/systemd/duplicati.default                                 # 1 (a comment) until B1
grep -c 'blessed_for "${dst}" || true' util/install_duplicati_service.bash                         # 0 until B3
# Wrapper v2 against the live .env SHAPE (dummy values); a scratch dir the reader OWNS, or preflight fails for the wrong reason
S="$HOME/.cache/wrapper-shape-check"; mkdir -p "$S"; printf "export SETTINGS_ENCRYPTION_KEY_OLD='x'\nexport SETTINGS_ENCRYPTION_KEY='y'\n" > "$S/shape.env"
DUPLICATI_ENV_FILE="$S/shape.env" DUPLICATI_DATA_FOLDER="$S" DUPLICATI_REQUIRE_MOUNT= DUPLICATI_SERVER=/bin/true bash scripts/duplicati-wrapper.bash --print-command; echo "exit=$?"   # FATAL ...:1: ... exit=78
```

---

## 8. Validation record

**Round 1 — 2026-10-03, three independent lanes, launched in one message against the frozen first draft** (sha256 `11789c8a…6540`, 293 lines; the artifact was not edited until all three had reported; each lane pinned the hash and cited by heading). Lanes: **A** fact re-probe (67 tool uses, re-measured every host and repository claim with its own commands); **B** consequence/procedure attack with the facts granted (104 tool uses; read the Duplicati
`v2.4.0.0_stable_2026-09-03` source and the installed assemblies, ran nothing); **C** continuity hunt against the three predecessor handoffs, the branch's STOP block and note 10.1g, the round-4 record and the memory (52 tool uses). All three were briefed to refute. Verdicts: **A PASS** (0 high; 2 medium; 7 low), **B FAIL** (1 high; 9 medium; 5 low), **C FAIL** (3 high; 11 medium; 22 low). The lenses barely overlapped: only the S-4/S-7 handling was found by two lanes.

**Folded in** (every finding above is applied unless listed as dissent):

- *Lane A*: the syslog copies rotated away (A-1 → §3 log-stores row, note 3c, I-11, §6.4 step 2; re-counted by the author, 0 across 15 files, 264 in the journal); the `.env` edit **pre-dates** ml#2029 by 24–87 minutes, not "post-dates by hours" (A-2 → note 3a); the shells' closure is in the branch's note sink-b (A-3 → §1, §3); PR #2109 was open with auto-merge armed and merged at 09:21Z (A-4 → front matter); `/etc/credstore` born 2024-10-23 (A-5); item 1 changes 96
  directories, not 97 (A-6 → §6.3); the reproduction's `:2:` was the recipe's line, not the live file's `:22:` (A-7 → §3.2, §7); §7's recipe needs a reader-owned scratch folder (A-8 → §7); I-23 was closed by the author at 09:02Z, after the freeze, in memory rather than in the document (A-9 → I-23); `journalctl` prints `-- No entries --` rather than nothing (A-10 → §3, §7); the vendor-unit restore on upgrade is demonstrated by dpkg's md5 (→ §4); the `_OLD` value is 32
  characters inside its quotes and the active key 64 (→ note 3a, O-1); Python's `sqlite3` module is a fallback (→ §3 tools row).
- *Lane B*: **B-1, high, CONFIRMED by the author in the fetched source** — `pbkdf-config` is in `Connection.PasswordFieldNames`, `WipeEncryption` clears it, `VerifyWebserverPassword` returns false on an empty config, `UpgradePasswordToKBDF` mints a random password, and `DisableSigninTokens` is set unconditionally at line 662 of the Server's `Program.cs` — so A2 as written ends in an unreachable server (→ I-37, I-19, O-2 reversed, §6.4 steps 7 and 10, B10, B7's correction of
  D step 6); B-2 Procedure A's key overwrite (→ I-38, step 9); **B-3 the installer's silent first-install exit, reproduced by the author on a scratch path** (→ I-36, B3); B-4 the un-rehearsed confinement set (→ I-32, step 0); B-5 the stage script's write mode (→ I-33, B7); B-6 the STOP's exit condition (→ B8, B11, I-27, B7's residue list); B-7 `--aes-version` (→ I-34, O-14); B-8 report-URL warnings (→ I-35, O-13); B-9 the overdue job firing during the decrypt start (→ B4
  pauses first); B-10 `--disable-db-encryption` satisfies the require flag — which also answers the round-4 record's U2 (→ I-28, B4); B-11 (→ §6.3 step 3); B-12 (→ I-29, step 6/9); B-13 `disable --now` (→ I-8, steps 1/13); B-14 the persisted pause (→ I-39, B2, step 11); B-15 escrow before the first start (→ I-40, step 9). The password-init helper's exit-code semantics (102 only when the stored password is autogenerated, else 103) were read by the author in `Program.cs` and
  shape B10 and step 10.
- *Lane C*: row 1 S-4's chmod closed against the wrong file (→ §3 escrow row, §6.3 step 3b); row 2 item 5's copy-out in round 8's corrected form (→ §6.3 step 3); row 3 D13 (→ I-26, B8, §2); rows 4–5 the round-8 list is not all cosmetic (→ I-22, §6.1); row 6 S-3c (→ I-30, O-9); row 7 the timer stop (→ O-10, §6.3 step 9); row 8 P0.5b's fate put to the owner (→ O-7); row 9 the sibling escrow mask (→ I-27); row 10 U2 (→ I-28); row 11 B16 (→ I-29); row 12 the installer's position
  restored to D's step 8 (→ §6.4 steps 1 and 9); row 13 O-3 reworded to the owner's phrase and the freeze dependency (→ O-3); row 14 the sink checklist's remaining rows and the second limit (→ §6.3 step 7, §6.1 item 5); row 15 the TestPyPI token (→ I-31, O-11); row 16 the `.env` mode dissent (→ I-3, O-12); row 17 the account audit (→ §6.5); row 18 the released `data/` listing (→ §6.3 step 6); row 19 Procedure B's start order (→ step 8); row 20 the extractor as a B
  deliverable (→ B11); row 22 the D-1 flag's home (→ O-8); row 23 limit 2 (→ §6.1 item 5); row 28 item 6 consistently in Phase B (→ B9); row 29 "P3's tier-2 fix" (→ §3.1 item 4); row 30 the memory items (→ I-23, §6.1 item 4); row 32 the §5.3/§5.4 citation and the `dbpath` pattern (→ §3.1 item 2, §6.3 step 5); row 33 S-8 in Procedure B (→ step 8); row 34 AC-10's terms (→ §6.3 step 8); rows 21, 24, 25, 27, 31, 35 carried by reference (→ I-41). Lane C's "reopened" table: the
  §12 rows, status line and "877 dindex" fix are on the branch and land with Phase A (→ I-21); the next-start verdict's 0700-gate half was already the record's (→ §1 item 3 reworded).

**Dissent and residue** (recorded, not resolved):

- The owner's release phrase — "Read-only steps may run" (the D-8 handoff) vs "only reads" (note 10.1g) — is settled only by the owner (O-3).
- Lane B's B-8: whether the report module's warnings reach the `Warnings` count the census reads is unproven either way; O-13 removes the question.
- Lane B's B-4: whether `ProcSubset=pid` breaks CoreCLR on this host is unknowable without the trial — which is why step 0 exists.
- Lane C rated landing the WIP commits "as-is" medium; §6.1 now requires the rebuild, so the finding is closed rather than disputed.
- Two method deviations by the author: the service `.env` was read through the sanctioned shape instrument (names and lengths only) against the D-8 handoff's "stat only" rule, and `MEMORY.md` plus the project memory were edited while the round ran (not the document under test; A-9 notes it).
- Not re-run after the fold-in: a round 2 on this document. The fold-in changed §6.4's procedure substantially (A0 default, step 0, step 10). Per §6.7 that procedure is validated again, with the artifacts in hand, as part of Phase B's round — which is the round that matters, because it is the one with the scripts the owner will actually run.

---

## 9. Document history

| Date | Change |
| --- | --- |
| 2026-10-03 | First draft from a live re-measurement of the host, the repository and the paused branch. Status DRAFT; three validation lanes launched against sha256 `11789c8a…6540`. |
| 2026-10-03 (later) | Round 1 folded in (§8): A2-over-A0 reversed (I-37, O-2); the S-4 row corrected; the syslog rotation, the `.env` edit timing, D13, the installer's first-install bug, the signin-token flag's semantics, the re-key hazards and fourteen carried items added (I-26 to I-41, O-7 to O-14); §6.4 rewritten; ml#2109 cross-referenced. **Changed**: this file; auto-memory `MEMORY.md` (two lines) and `project_backup_service_user_migration_2026-09-21.md` (a 2026-10-03 section). |
