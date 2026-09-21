# HANDOFF 2026-09-21 — backup redesign: consensus round 1 complete, reconciliation pending, §8 must not be executed

Continue the Juniper backup-infrastructure redesign arc. The design document is the document of
record for everything below; every bare `§` refers to it unless another file is named:
`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`.

**Where the arc stopped.** The design was drafted from five step reports and then validated by six
independent agents under `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`
(three Lane A entry points, three Lane B lenses). Lane A2's 15 and Lane A3's 12 corrections were
applied. The owner paused the arc before Lanes A1, B1, B2 and B3 were folded in (applied so far, and nothing else: the §4.1 unit row; the §11 adequacy and cannot-support entries; the §8 STOP warning; §7.3.2's env override (B1 F11); P1 step 2's `chmod 0600` (B2 D15); the AC-12 row, §0's instrument list and §12's file list (B2 D22)).
Their reports — and the five step reports — are archived **verbatim** in
`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md` and
`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-STEP-REPORTS-RECORD.md`; the design
carries a `reconciliation PENDING` status line and a STOP warning at the top of §8. Read the
record file before touching the design: §1.1 below gives the orchestrator's disposition of every
finding, but the findings' evidence lives only in the record.

**Your job, in order**: (1) reconcile the four pending lanes into the design (§1.1); (2) run
consensus round 2 on the corrected revision and complete the design's §11 and §12 (§1.2); (3) flip
the status line, remove the §8 warning, open and merge the follow-up PR (§1.3); (4) prepare what a
session can prepare for the owner-gated P0 and list the owner actions (§1.4–§1.5). Nothing in §8
is to be executed by a session; nothing under `/mnt/Backups/Ubuntu/` is to be changed.

**Distrust order — re-derive before acting.** Rots on any restart of `duplicati.service`: which
port the server listens on, which data folder it uses, whether a job is defined, whether the
service is up at all (see the armed hazard in §0). Rots daily: the snapshot copy's inode (replaced
every day at 13:45 UTC), the watchdog verdict. Rots on one owner action: the mode of the data
folder, the content of `.env`, the unit file (it was open in a live `vim` when Lane A1 looked).
Stable: the journal record of 09-17 → 09-21, the forensics of the database copies, the 09-18 dlist
as the last restore point, the six validator reports.

---

## §0 — What is true now, and what is CLOSED

| Fact | Value |
| --- | --- |
| Tier 1 backup | **DOWN since 2026-09-18 14:12 UTC** — last fileset `duplicati-20260918T140000Z`, 877 files / 202.8 GiB at `/mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi/` (re-counted by Lane A1 13:40 CDT) |
| Live server | `duplicati.service` as `duplicati` (uid 133 / gid 139), PID 1397393 since 09-20 18:19:42, `localhost:8300`, data folder `/home/duplicati/.config/Duplicati/` (0777; inferred from `lock_v2` and the live WAL's birth — `/proc/1397393` is unreadable, A1), **0 backups defined**, schema 12; its last journal lines (09-20 18:47, 18:51) are `Access to the path '/media/pcalnon/temp_backups' is denied` — someone pointed it at the old USB path after the import failures |
| Armed hazard (corrected by A1/B1) | `NeedDaemonReload=no`; the LOADED `ExecStart` is already `… '--daemon-opts="${DAEMON_OPTS}"'`; only the RUNNING process (argv `--webservice-port=8300` plus a trailing space, one word) predates it. The next restart executes the new form for the first time; the 0700 gate then refuses the 0777 folder regardless of argv (B1 finding 11): "does not start", not "8200 or fails". **Stop, never restart**, until the §7.3 unit and a 0700 folder are in place |
| Recovery source 1 — A0 (key-free, MISSING from §8) | The 09-17 and 09-18 14:00Z filesets each contain a cleartext schema-11 copy of the root server DB at `home/pcalnon/.local/state/duplicati-server-db/Duplicati-server.sqlite` (the snapshot lane writes inside the backup source; the root DB was unencrypted until 09-18 20:42). Decrypting that one file needs the escrowed passphrase and nothing else; the index move in the row below still applies (Lane B1 finding 3) |
| Recovery source 2 — the snapshot file | `~/.local/state/duplicati-server-db/Duplicati-server.sqlite` (240 KiB, schema 11, job `Yamaguchi` id 2, 2 sources, 45 filters, schedule 14:00Z, `DBPath=/usr/lib/duplicati/data/BMXWPAOGLP.sqlite`); nine `enc-v1:` values under one key hash that no candidate matches (next two rows), so it needs `wipe-encryption` (Procedure A2) or the API rebuild (Procedure B) |
| The index, whichever source is used | `BMXWPAOGLP.sqlite` lives in the abandoned root-era data folder `/usr/lib/duplicati/data/` (0700, now owned `duplicati:duplicati`) — every procedure (A0 included) must move it into the new data folder and re-point `Backup.DBPath` before the first run, or the first backup fails read-only and P4 deletes the index (Lane B1 finding 4) |
| The 09-18 key | **Unrecorded anywhere the design looked.** The committed 36-char literal (11 shell-mangling variants) and the backup passphrase are excluded by `util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py` on copies of the snapshot and the pcalnon `.backup` (B1 finding 1: content hashes verify 4/4 and 6/6 on the fields the probe selects). Last untested places: root's shell history and editor backups of the unit for 09-18 20:42–21:03 |
| Key-hash cross-check (this handoff's Lane A) | 9/9 and 11/11 `enc-v1:` values verify on the snapshot and the `.backup`; one key hash per database, and three different hashes across snapshot, `.backup` and the live 0777 database — the live one is under today's `.env` key (= the backup passphrase), so the passphrase is excluded without any candidate test |
| Watchdog | `yamaguchi-watchdog.timer` (user, 12:00) alerts `UNREACHABLE` 09-19/09-20 and `login failed (401)` 09-21 02:52 and 12:00 |
| Design PR | To be merged as PR_NUMBER_PLACEHOLDER (the number is filled in by a fixup commit on the PR branch; the owner approved the merge in-session: "handoff should be validated by consensus, archived, merged, and PR'd"). Until that merge the design, the three record files, this handoff and the six `util/ad-hoc/2026-09-21_*.py` instruments exist only on the never-pushed worktree branch `worktree-atomic-sauteeing-truffle`; §3's first checks assume the merge has happened |
| Root cause | **The three legs of §5 SURVIVED all six lanes** (Leg A wrong source, Leg B aborted per-job Recreate stub with local schema 19, Leg C real DB encrypted 09-18 between 21:03:27 and 21:08:06 under a key no later start reproduced). What Lane B1 rewrites is around them: §5.3's actor (unidentified; F5), §5.4's discriminator (the port-8200 test; F6), §5.6 row C's refuter (F6) and the 21:03:34 folder-mtime marker (it is the `-wal`/`-shm` creation; F7) |

---

## §1 — Remaining work, in order

### 1.1 Reconcile Lanes A1, B1, B2, B3 into the design

Work from the record file. Dispositions below were decided by the orchestrator on 2026-09-21 after
re-checking the host (count-only probes; the checks are marked ✔); none is applied beyond the list in the opening paragraph. Where a lane's
proposed fix was **not** adopted, the record must say so in the design's §11 "unresolved dissent".
One ✔ in the first draft of this handoff was wrong (B2 D9, below) — re-make every ✔ you rely on.

**Lane B1 (root cause / recovery) — accept all 17.**

- F1 §5.4: replace the candidate order with the offline key-hash test (script archived; usage in its docstring); state that both named candidates fail; name root's shell history / unit editor backups as the only remaining candidate sources; add B1's observation that 15 `Mismatch` restarts (21:08:06–21:11:43) preceded the first specifier error (21:15:40), so a `%`-free or file-delivered key that did **not** match the 21:03 key was in play before the `%`-literal could have been loaded — the Mismatch is
  equally evidence that the literal ≠ the 21:03 key. Add the libsecret auto-generated-key mechanism (why the pcalnon profile is `enc-v1:` under a keyring key; a root unit has no session bus, so it does not explain 09-18).
- F2 P0 step 3: the hash test is the discriminator; keep the server probe only as confirmation, copying `.sqlite`+`-wal`+`-shm`, asserting `Option(-2,'encrypted-fields')='True'` and `TargetURL LIKE 'enc-v1:%'` on the copy first, with a negative control (a random key must produce `Mismatch`). The lanes' recorded containment fixes are B2 D17 (`systemd-run --wait -p InaccessiblePaths=/mnt/Backups -p InaccessiblePaths=/usr/lib/duplicati/data`), B3 F-17 (verify `startup-delay` in the snapshot's Option rows
  first — present by name at BackupID −2 per B1 F12 and the orchestrator's name-only check, value unverified — and add `--webservice-disable-signin-tokens` to the probe) and B2 D6 (`timeout -k 10 45`); the orchestrator's own addition is `DELETE FROM Schedule` on the copy before any start. Use all four.
- F3 add **Procedure A0** ahead of A: restore the single file `home/pcalnon/.local/state/duplicati-server-db/Duplicati-server.sqlite` from `duplicati-20260918T140000Z` with the escrowed passphrase and a fresh `--dbpath` (so the live index is untouched); only `LastBackupDate` is one day stale. Confirm first with `duplicati-cli list … --time=2026-09-18T14:00:00Z` (owner: needs the passphrase — from the env file, never on argv).
- F4 every procedure (A0/A/A2/B): move `BMXWPAOGLP.sqlite` into the new data folder and re-point `Backup.DBPath` (UI Database → Placement, or `PUT /api/v1/backup/<id>`) before the first run; 2.4.0.0 then stores it relative. Add to AC-4.
- F5 §5.3: rewrite the mechanism — `Duplicati-server.backup` is the ORIGINAL inode (birth 2023-05-17) renamed by `RepairHandler` when the local repair found zero known remotes; `backups/backup Duplicati-server 20260825021947.sqlite` is the LOCAL-DB upgrader's pre-upgrade copy (fires only when a local-schema upgrade runs, i.e. the server file was opened as a job DB). Drop "consistent with the 2026-08-22 DBPath finding" (the `.backup` already shows `Ubuntu` re-pointed); the actor is unidentified. Appendix
  C.1 stands.
- F6 §5.4/§5.6: a `Server has started … port 8200` line proves the option word was unusable (port parse falls back to 8200), so `--portable-mode` glued into it was inert and the folder was `$HOME/.config/Duplicati`; the root folder was last opened 09-19 19:15:01. Rewrite §5.6 row C's refuter as "a `Server has started` on a start whose folder is the root folder — none exists after 09-18 21:03:30".
- F7 relabel the `/usr/lib/duplicati/data` mtime 21:03:34 (§4.2, A.3, C.3): it is the `-wal`/`-shm` creation, not the encryption; encryption is bracketed "between 21:03:27 and 21:08:06". The same mtime means the WAL was never removed by a clean close — the main file alone may still be cleartext (owner check: `sudo ls -la /usr/lib/duplicati/data/`).
- F8 add `/var/log/syslog*` to S-1/S-2/S-3 "where exposed" and to D-8 (✔ rsyslog active; day files back to 09-12, `syslog:adm` 0640; pcalnon is in `adm`); correct the counts to 264 echo lines / 60 commented assignments / 12 `Exporting` / 12 key prints for 09-20 (window 16:41–16:44: 220/50/10/10 stays exact).
- F9 S-2: say the active key IS the live Yamaguchi backup passphrase (the `.env` comment's "Ubuntu-fresh" label is stale); `util/ad-hoc/2026-09-21_env_value_equality.py` is the instrument.
- F10 S-4: the escrow file `_yamaguchi_keys/env` is `-rwxrwx--- pcalnon:duplicati` — group-readable by the service user; chmod 0600 (also B2 D14).
- F11 §7.3.2: add `DUPLICATI__ALLOW_INSECURE_DATAFOLDER=true` to the override sentence (§5.5 already has it; done in this revision); the loosening is dated by ctimes (three files 18:25:47, directory 18:33:45, not recursive); "may refuse" → "will refuse"; §4.3 item 9 **and §1** say "on 8200, or not at all" → "not at all".
- F12 P0 step 7: `duplicati-server-util` auth = saved refresh token, else a signin token minted from a readable **and decryptable** DB (needs the settings key), else `--password` — B1 said it falls back to a prompt, B2 D5 said no prompt path is documented; SETTLED for B1 in round 2 from `ServerUtil/Connection.cs` (see D5). The recovered DB carries the root-era UI password until step 9 changes it.
- F13 Procedure A2: `wipe-encryption` clears `Backup.TargetURL`, `Source.Path`, `ConnectionString.BaseUrl`, `BackupTargetUrl.TargetURL` and password-typed `Option.Value`; the UI password (hash + salt) survives, so "set the UI password afresh" is optional; the tool makes a `-<ts>.bak` and refuses non-server DBs.
- F14 C.3: the pcalnon `.backup` is itself `enc-v1:` (six blobs tested, eleven in total, one key) — "cleartext" statements are true of the root DB only.
- F15 §4.1/§4.2: profile copy in three waves (A1 item 9: 09-19 18:40–18:42; 09-19 21:57:36 the stub; 09-20 04:15–04:43 — B1 groups the same births as two rounds); the §4.1 unit row already carries the reload/running-process correction, and its "03:23:44" reload time is the orchestrator's own journal reading, measured by no lane.
- F16 §8 preamble "nothing under `/mnt/Backups/Ubuntu/` is moved" contradicts P1 step 4 — see B2 A3 for the fix.
- F17 the `EnvironmentFile=` paragraph in §5.4 is correct but moot once F1 lands; shorten it.
- Also carried from B1's "observations that would settle what is left open": O4 — root's shell history around 2026-08-25 02:19 for a `--dbpath=/home/pcalnon/.config/Duplicati/Duplicati-server.sqlite` invocation identifies the Repair actor (owner, §1.5); O5 — after any scrub, `sudo ls -la /var/log/syslog-2026092*` confirms the second copy is gone (add to D-8's verification).

**Lane A1 (live host) — accept all 13 DISAGREE items, record the 8 unrecorded facts and the two table qualifications.**
Counts and dates: 12 debug passes on 09-20 (not 10); 24 failed starts on 09-19 20:48–21:55 (5 "is 11", 5 "denied", 14 "is 12" — §5.3 must list the 09-19 21:43–21:55 "is 12" refusals); 23 `Invalid slot` lines = 22 `Failed to resolve specifiers` + 1 `Failed to resolve unit specifiers` (✔ re-counted 09-18 → 09-21 13:00), 4 specifier lines on 09-18 (21:15:40, 21:16:10, 21:17:54, 21:29:51 — plus the one `unit specifiers` line at 21:23:25, so 5 `Invalid slot` lines that day) and 18 on 09-19 (the rejected
`Environment=` line survived until at least 09-19 18:07:32); nine `Repair` failures in the `.backup` ErrorLog on 08-25 (02:05:17, 02:13:57, 02:14:42, 02:15:31, 02:16:17, 02:17:03, 02:17:50, 02:18:37, 02:19:24) and `Verify` failures at 02:13:07 and 02:19:46 — nothing at "02:19:19", which §5.3 still says; only the four copied DB files and the crashlog are 0777 (`.env` 0660, `installation.txt`/`machineid.txt` 0664, subdirs 0775, `temp/` root 0755); only directories under `/usr/lib/duplicati` were chowned — all
1,443 regular files, binaries included, are still `root:root` (also fixes §5.5); the primary checkout is on `main` `d721fc78`, not a feature branch (§4.3.8); at 09-20 13:32:34 five starts of the OLDER `wrapper.bash` died `KeyMissing` sixteen seconds before the `duplicati-wrapper.bash`
success — two wrapper files were in play; A.1's 20:48:12 line carries identifier `wrapper.bash`. Table qualifications: S-5 is **broader than stated** — the 0664 primary checkout `.env` carries 12 other names, several of them Slack tokens/secrets (✔ it holds 0 `PASSPHRASE=` lines and 1 `DUPLICATI_WEB_CREDENTIAL=` line, count-only — so S-3 is *not* world-readable there, which answers B3 O-6); S-6 has five sign-in-token URLs in the journal, not one. Unrecorded facts to add to §4: destination chgrp datable
(dirs 09-18 20:36:53 / 20:37:41, 874 volumes 09-19 17:37); `Backups/lost+found` (2023-05-16); `/mnt/Backups/Ubuntu/.dropbox-dist` is a second Dropbox client (270.4.3312) owned `duplicati:duplicati` — directory born 09-15 15:26:22, content mtime 09-14 20:49:31 (the distribution's own stamp), ownership last changed 09-18 20:30:49 (✔; retire it in §7.11); `/home/duplicati` created 09-18 19:31:40; the pcalnon profile's `installation.txt` was rewritten 09-20 18:10:32; `/opt/miniforge3/envs` is 62 G (§3.4 says 47
GB); the unit file was open in a live `vim` and two `su - duplicati` shells were running. A1's UNTRACEABLE list
(8 items) and "could not verify without root" list (R1–R5: the abandoned folder's contents, `/proc/1397393/{environ,fd,cwd,exe}`, the `duplicati` user's history/viminfo, the temp WAL's byte identity with the profile WAL, the credential store) → §11 "cannot support".

**Lane B2 (amputation / actionability) — accept A1–A10 and D1–D21; D22 partly.**

- A1 → new **S-7**: `juniper-ml/.claude/worktrees/curious-plotting-hummingbird/.env`, 114 B, **0664**, 2026-08-23 (✔) — a cleartext copy of both passphrases inside the backup source, world-readable. That worktree is **DO NOT SWEEP** (memory `reference_worktree_sweep_hazards_2026-09-12`); remove only the file, after the sha256[:16] fingerprint check in `HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md` §1 item 8 (same directory as this file); `git worktree remove` deletes it silently.
- A2 → P0 step 7: `GET /api/v1/serverstate` before `pause` and after `resume`; record `ProgramState`, `paused-until`, `SchedulerQueueIds`; step 8 waits for the run to begin (the 2026-08-30 stuck-pause class).
- A3 → replace P1 step 4 and the §8 preamble: the escrow copy is COPIED (`cp -a`) to a sibling outside the Dropbox root (e.g. `/mnt/Backups/Ubuntu/_yamaguchi_keys/`), sha256 verified both sides, and the Dropbox-tree copy deleted only on owner sign-off, followed by a **permanent delete in Dropbox and an account audit** — `dropbox exclude add` leaves the cloud copy in place (Lane B3 F-12 prevails over B2's exclude suggestion; record the dissent). B3 F-12 also wants `_yamaguchi_records/` excluded from the
  synced tree.
- A4 → AC-4 = two drills: one from `20260918T140000Z` (pre-recovery, proves the re-attached index serves old filesets), one from the first post-recovery fileset.
- A5 → §6: the `additional-report-url` bearer JWT is a secret carried by every DB copy (snapshot, tar, A0/A/A2/B); rotate if a copy leaves the machine; Procedure B states whether the rebuild re-creates it.
- A6 → D-12 enumerates every open item of the 09-07 handoff §1 and `notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md` §8.27.6 with carried / out-of-scope / closed-by-§.
- A7 → §11 gets an instrument-adequacy statement per §4.1 row (or marks §4 as a Lane A subject); note `ls` shows `+` on `Backups/` entries because of the `user.com.dropbox.attrs` xattr, not an ACL.
- A8 → new D-13: Dropbox root policy (exclude everything but `Backups/`, or accept personal files syncing beside the ciphertext).
- A9 → §2 provenance: the prompt is on `main` via #1969 (`d721fc78`) **and** at `aab07eba` on `feat/backup-updates-and-redesign-work` (A2 verified both; §2 already says so) — the only fix is §4.3.8's present-tense "feature branch" for the primary checkout.
- A10 → §4.1/§7.11: the second Dropbox client (above).
- D1 → §7.8 `.path`: `PathExists=` re-triggers after every termination (✔ `man systemd.path`, the "checked immediately again" paragraph, ll. 30–36, which exempts nothing); the man page's "does not apply to `PathChanged=` and `PathModified=`" sentence (l. 96–97) is about immediate activation when the path already exists at unit activation — B2's citation conflated the two paragraphs. Whether `PathChanged=/run/media/pcalnon` re-triggers on termination rests on systemd's `path.c` (`path_spec_check_good`: for
  `PATH_CHANGED`/`PATH_MODIFIED` `good = !initial && !from_trigger_notify && …`) — verified in round 2 from v259 `path.c`: `good = !initial && !from_trigger_notify && b != s->previous_exists` for `PATH_CHANGED`/`PATH_MODIFIED`, and `path_trigger_notify_impl` re-checks with `from_trigger_notify=true`, so `PathChanged=/run/media/pcalnon` is a sound fix; a udev `ENV{SYSTEMD_USER_WANTS}` rule on the two UUIDs is an alternative, not a requirement. Test: plug a stamped drive and watch `systemctl --user status
  juniper-backup.path` for 30 s. (✔ `/run/media/pcalnon` exists: `root:root` 0750 with an ACL, empty.)
- D2 → a `juniper-backup-failure.service` that passes `juniper-backup.service` to the reporter (the existing one journal-tails the disabled CLI lane).
- D3 → reorder P3: fix `util/juniper-backup.bash`'s mount root first; scheduler and runner read ONE mount-root setting.
- D4 → the guard gets a repository source path (`util/…`) and an install line in `util/install_duplicati_service.bash` (0755 root:root); P0 step 7 dry-runs it as `duplicati` with `DUPLICATI__REMOTEURL` set before `resume`.
- D5 → no `duplicati-server-util … --password`/`change-password <new>` on argv anywhere (✔ `help` shows both take the secret as an argument): pause/resume through the in-process client (`util/ad-hoc/yamaguchi_server_api.py`, extend with `pause`/`resume`), the first password through the web UI; `--webservice-password-init` is a Password-type option (`Program.cs` at the 2.4.0.0 tag: applied only while `AutogeneratedPassphrase`; exit 102 on success, 103 otherwise — so `Restart=on-failure` loops it) that CAN
  carry the value on argv, which is why it must be fed through `--secret-provider` (a `$name` placeholder) or `--parameters-file` — the server applies both before it reads the init value; `--settings-file` is `duplicati-server-util`'s refresh-token store, not a server option (round 3, `Program.cs` at the tag — B3 F-15 named the wrong file option) — and run once by hand with the service stopped (B3 F-15) — never in `DAEMON_OPTS`. For `duplicati-server-util` the documented non-argv channel is
  `--secret-provider <env|file-secret|libsecret|…> --password='$name'` (and `SETTINGS_ENCRYPTION_KEY` in the environment for the signin-token path); whether the `$name` substitution reaches `change-password`'s positional is untested. Round 2
  settled the B1-vs-B2 prompt question from `Duplicati/CommandLine/ServerUtil/Connection.cs` at the tag: after the refresh token and the DB-minted signin token it calls `Utility.ReadSecretFromConsole("Enter server password: ")` — a prompt exists, `help` just does not list it; the in-process client stays the fix.
- D6 → see B1 F2. D7 → candidate keys via `read -rs`/`install -m 0600 /dev/stdin` after `set +o history`, never `printf '<value>'` (also B3 F-17). D8 → "until P1 step 1 replaces it", not "first start only". D9 → **corrected**: `duplicati-database-tool wipe-encryption <db-path>` DOES accept `--server-datafolder <dir>` on the subcommand (✔ `duplicati-database-tool help wipe-encryption`; default `$HOME/.config/Duplicati`, i.e. the pcalnon profile when run as pcalnon); the top-level `help` does not list it,
  which is what B2 read — an A3-vs-B2 conflict that this handoff's first draft resolved the wrong way. Always name the copy's folder and run `--dry-run` first (B2 verified on a scratch copy of the snapshot: `version 11 … Server database … 9 encrypted field(s) would be wiped`); with no database argument the tool targets the default folder — the orphaned pcalnon profile's stub — and **`--dry-run` still rewrites the copy's header** (the header flips to WAL — the `-wal`/`-shm` pair exists only while the tool
  runs — and the sha256 changes): hash
  before, or re-copy after. Re-entry through the UI or `yamaguchi_build_job.py`'s in-process read. D10 → the rebuilt job is not id 2: every later command, AC and the watchdog unit (`--backup-id <id>`) take the assigned id. D11 → one credential path (`~/.config/duplicati-backup/web-credential`) in `yamaguchi_server_api.py` and `duplicati_api.py` in the same PR; order P0 so the file exists before AC-2.
- D12 → AC-3 adds `Warnings=0`, `NotProcessedFiles=0` and a `duplicati-cli find` of one `~/.ssh` and one `~/.gnupg` path; pre-flight `systemd-run -p User=duplicati -p AmbientCapabilities=CAP_DAC_READ_SEARCH --wait cat ~/.ssh/known_hosts`; cite the baseline (`SourceFilesCount=1024167`, `290.610 GiB`, snapshot Metadata).
- D13 → §7.7: `/home/pcalnon/.local/state` is **0700** (✔), so the `duplicati` user cannot reach the snapshot target however the leaf is chmod'ed; keep the snapshot unit root, or use a root-created 2770 staging directory inside the source.
- D14 → §7.4 script: chmod the escrow file 0600 explicitly; run only when `dropbox status` is up to date; note ~1,700 mode-bit changes will sync as metadata updates. D15 → `.env` is 0600 everywhere (P1 step 2 corrected in this revision; but see the B3 F-5 conflict below). D16 → P4 step 1's tar of `/usr/lib/duplicati/data/` (the index holds the full path list) goes to a root-only 0700 directory outside the backup source, never to `~/.local/state`. D17 → see B1 F2. D18 → §10: mark D-1/D-4/D-6/D-9 "rule
  before P0" or state that P0 applies the recommendations provisionally. D19 → the guard allow-lists `duplicati-verification.json` and states that the exact `file://` match fails closed on variants. D20 → state why `Restart=on-failure` (a one-shot exit must not loop) and drop `network-online.target` (loopback server). D21 → P3 gains a deliverable: an installer for the three T2 units and two scripts (`util/install_duplicati_timer.bash` installs the OLD lane by name).
- D22 → done in this revision: the AC-12 table row, `wrap_long_markdown_lines.py` in §0, the full file list in §12; the PR body carries a `## Requirements` section. **Dissent recorded, not adopted**: the alias-only references (44 by an anchored `grep -o` on the design — 28 `YAM §`, 8 `PLAN §`, 3 `CON §`, 4 `DMG §`, 1 `GPG §`; an unanchored count also picks up the pattern names quoted in the counting sentence itself) — the alias list in the design's header (**Companions**) binds each alias to a filename
  within the same document; the name-every-document rule
  targets summaries, PR bodies and handoffs (this is an
  orchestrator-vs-B2 disagreement, not cross-lane).
- Also carried from B2's "could not determine": C3 — the value of `startup-delay` (present by name; see F2); C4 — Dropbox's handling of a setgid/0770 root and ~1,700 mode-bit changes, and ext4 default-ACL creation modes (B2's scratch test ran on tmpfs) — test on ext4 before P2; C6 — the current wrapper forwards a `.env` `--option` line such as `--print-command` to the server unchanged: wrapper v2 must either refuse options it does not know or the design must state how the server treats an unknown option;
  C7 — B2's line numbers are stale (the document changed twice during its review) — re-anchor every B2 citation by heading text.

**Lane B3 (security) — accept F-1 … F-20; read the report for the full list.** The ones with a
decided shape: **preamble** — pcalnon is root-equivalent (`sudo`, `docker`, `libvirt`, `kvm`
groups), so the design must state which boundaries it can still buy and which it cannot; F-1/F-2/F-3
state the `CAP_DAC_READ_SEARCH` trade-off in D-4 and add `IPAddressDeny=any` +
`IPAddressAllow=localhost`, `RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6`,
`SystemCallFilter=@system-service`, `ProtectProc=invisible`, `ProcSubset=pid`, `PrivateDevices=yes`,
`ProtectClock=yes`, `ProtectHostname=yes`, `ProtectKernelLogs=yes`, `RestrictNamespaces=yes`,
`InaccessiblePaths=-/etc/shadow -/etc/gshadow -/etc/ssh -/etc/credstore -/etc/credstore.encrypted -/var/lib/docker -/var/log -/root`
(or `ProtectHome=tmpfs` + `BindReadOnlyPaths=/home/pcalnon` + `BindPaths=/home/duplicati`), disable
update checks and usage reporting (the only legitimate egress), and the sentence "a UI credential is
a host-wide read of everything the service can read"; F-3 also pins the job's run-script option in
an acceptance check; F-4 the guard `unset`s `DUPLICATI__passphrase` and `SETTINGS_ENCRYPTION_KEY`
before doing anything, never writes to stdout (Duplicati parses run-script stdout as option
overrides), mentions the secret-provider channel, and AC-8 is extended to run-script output; F-5 `.env`
**0640 root:duplicati** — conflicts with A3 #9 / B2 D15 (0600 duplicati-owned); the orchestrator
recommends F-5 (stricter, and the wrapper only reads it) — owner decision; F-6 reconsider the
group-write model (2750 / 0640 / `UMask=0027`, volumes chowned to `duplicati`) — conflicts with
R-7/R-8 and B2 D14; make it **D-14** for the owner; F-7/F-8 a **P0.5 same-session** bucket:
`chown root:root /usr/lib/duplicati`, remove `/home/duplicati/bin/duplicati-wrapper.bash` (a symlink
into a developer checkout), data folder 0700 in Procedure B, the root snapshot timer runs a pcalnon-writable script (F-8); and — the orchestrator's addition from A1's §4.1 row, not a B3 finding — `/etc/default/duplicati` is `duplicati:duplicati` 0644 (the service user can rewrite its own next argv) → root-owned; F-9/F-10 the scrub covers `/var/log/syslog*` (F-9) and F-10's sink checklist — the live
`duplicati` shells' `.bash_history`/`.viminfo`, root's history, the unit swap files, the CUPS spool
(the escrow sheet was printed), world-readable DB copies, and **Claude Code transcripts** (✔ this
session's own transcript
`~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-atomic-sauteeing-truffle/227cf645-dd93-4802-91f7-23dcaa92c971.jsonl`
held 22 env-echo and 21 specifier lines at 13:56 CDT, count-only — the number grows with every tool call (38 specifier lines by 14:34, 48 by 15:05 — an upper bound, since the pattern also matches the validators' own command text) and the `tool-results/` cache also holds the validators' own outputs; B3 O-4 answered: yes, a cloud-linked sink exists); F-9/F-10/F-12 want **D-2 re-argued and re-decided** on that basis (B3's top finding);
F-11 fold the P1.1 re-key into P0 and add a gitleaks content rule as a pre-commit hook; F-12
permanent delete + account audit for the escrow copy (see B2 A3); F-13 a cloud threat table, the
passphrase's provenance, delete-forever the OLD frozen set, pin `--aes-version`, and Dropbox
Rewind/version history as a design item (the sole recovery from a mass delete) — B3 dissents from
§5's "Rewind not evaluated"; F-15 `--webservice-password-init` together with
`--webservice-disable-signin-tokens`, no `change-password` on argv; F-16 stop the snapshot timer
during the re-key, then `PRAGMA wal_checkpoint(TRUNCATE); VACUUM;`; F-17 `read -rs` for candidates;
F-19 a trust table (who can read what, after P1/P2); F-14, F-18, F-20 — read the report. B3's open
observations O-1 (answered: `startup-delay` present), O-2 (can `duplicati-server-util
--server-datafolder=<copy>` mint a token as the server's uid without `--password`? test on the probe
copy), O-3 (does 2.4.0.0 run under the F-1 confinement set? `systemd-run` against the probe copy,
then `systemd-analyze security`), O-4 (answered above), O-5 (CUPS: `grep -i PreserveJobFiles
/etc/cups/cupsd.conf`; `sudo ls -la /var/spool/cups`), O-6 (answered in the A1 paragraph), O-7
(Dropbox account: 2FA, linked devices, plan retention — sets F-12's severity), O-8 (AES Crypt v2
KDF — only matters if the passphrase is not random), O-9 (root's `.viminfo`/`.bash_history`/unit
swap: root-only count greps for `SETTINGS_ENCRYPTION_KEY=`), O-10 (**time-critical**: `history -c;
unset HISTFILE` in the two live `su - duplicati` shells before they exit), O-11 (does RunScript's
`SendStdOutToLogs` store the guard's stderr verbatim? a log-injection nuisance).

**Cross-lane conflicts to settle in §11:** the specifier-line count (A1 23 = 22 + 1; B1 21 journal /
22 syslog; orchestrator 22 + 1 — pattern and window differences, not fact); `dropbox exclude add`
(B2) vs permanent delete + audit (B3); A3 vs B2 on `wipe-encryption --server-datafolder` (A3 is
right — it is on the subcommand); B3 F-5 (`.env` 0640 root:duplicati) vs A3 #9 / B2 D15 (0600
duplicati-owned); B3 F-6 (2750/0640/`UMask=0027`) vs R-7/R-8 and B2 D14 (group-write model); B1 F12 vs B2 D5 on whether `duplicati-server-util` has a prompt path — SETTLED for B1 (round 2, `Connection.cs` at the 2.4.0.0 tag); the in-process client (D5) stays the fix; B2 D1's man-page citation vs the
orchestrator's reading (a conflation of two paragraphs, above). Orchestrator-vs-lane: the
alias-only references (B2 D22, dissent recorded).

### 1.2 Round 2, §11, §12

Per the procedure's §3 sizing (document of record, an instrument previously wrong, universal quantifiers, a fix hanging on it) and §4: round 2 = Lane A ×2 (host — re-run §3 and every §4/§5 count that changed; product — 2.4.0.0 `help` plus a UTF-16 option-name scan of every `/usr/lib/duplicati/*.dll` (549 files; the names are spread across `Duplicati.Server.Implementation.dll`, `Duplicati.Library.RestAPI.dll`, `Duplicati.Library.Main.dll` and the tools), since the source is not on the host — for every option
the reconciled P0 uses) + Lane B ×2 (actionability of the reconciled §8; security of the P0.5 bucket), briefed only on the change list and the
dissent, at most three subagents at a time; archive their reports verbatim to `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md`; done when a round changes no number, disposition or action; then write §11 to
the §7 minimum record (instrument + adequacy, sample sizes, agents/lanes/entry points, iterations
and what the last one changed, unresolved dissent, what the evidence cannot support), add a §12 row,
re-run `util/ad-hoc/2026-09-21_lint_design_snippets.py` (expect `failures: 0` — the count of tagged
blocks will grow with Procedure A0, the failure unit and the guard/installer changes) and the pinned markdownlint run WITHOUT `--fix` from the pre-commit cache (`~/.cache/pre-commit/repo*/node_env-default/bin/markdownlint --config .markdownlint.yaml <file>`; the hook itself runs `--fix` and rewrites files). Every code block you change or add must carry a `# file:` tag so the linter sees it.

### 1.3 Follow-up PR

Flip the status line to `VALIDATED (round 2)`, delete the STOP block at the top of §8, list the
changed files in §12, open the PR on a branch such as `docs/backup-design-round-2` through `util/open_signed_pr.py --repo juniper-ml --branch <b> --add LOCAL:REPOPATH … --message … --title … --body-file …` (one `--add` per file, whole-file uploads; local commit signing hangs headless), wait with `util/wait_for_checks.py`, merge with `util/safe_merge.py --pr <N> --execute`
(read the `MERGED` line). Merge approval for the design's follow-up must be re-obtained from the
owner: the in-session approval of 2026-09-21 covered the merge that landed this handoff.

### 1.4 P0 preparation a session CAN do (no sudo, no live change)

- Extract the code blocks with the snippet linter and stage the reconciled artifacts under
  `util/`, `util/systemd/`, `scripts/` in the follow-up PR (today every artifact exists only inside
  the design).
- Re-run the key-hash probe if the owner supplies a new candidate from root's history: write one line `SETTINGS_ENCRYPTION_KEY=<value>` into a 0600 file and pipe it on stdin — `cat <file> | python3 util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py scripts/duplicati-wrapper.bash ~/.config/duplicati-backup/env snap=<copy>` — the probe has no candidate-file argument. Feed the candidate ALONE on stdin: the probe keeps only the last uncommented `SETTINGS_ENCRYPTION_KEY=` line it reads, so a
  concatenated `.env` would discard one of the two (the `.env`'s own candidates are already excluded). Expect `candidates loaded: ['ENV_ACTIVE_KEY', 'L', 'PASSPHRASE', 'PASSPHRASE_OLD']`. Never on argv.
- Extend `util/ad-hoc/yamaguchi_server_api.py` with `pause`/`resume` and the shared credential
  path; re-point `util/ad-hoc/duplicati_api.py`'s `PW_FILE`; write the `.path`-unit plug-in test.
- Settle B3 O-2 (can `duplicati-server-util --server-datafolder=<copy>` mint a token as the server's uid without `--password`?) against a throwaway server on a scratch data folder — never against the live server.
- Write the D2 unit (`juniper-backup-failure.service`; the reporter takes the unit name as `$1`, default `duplicati-backup.service`); note that the watchdog user unit runs the PRIMARY checkout's `yamaguchi_watchdog.py` with no `--backup-id`, and that `util/install_duplicati_service.bash` and `~/.config/duplicati-backup/web-credential` exist only inside the design today.

### 1.5 Owner actions (each blocks something)

1. **Rotate the TestPyPI token.** Lane A3's harness printed `env | grep '^TEST_'` into a scratch file
   (since regenerated) **and into a tool result** — i.e. its subagent transcript, a cloud-linked sink (round 2, count-only: one `TEST_TWINE_*=` line and one token-shaped line in A3's transcript).
   Nothing was printed into the design or the record; rotate anyway. Where: `~/.bashrc` is the only startup file naming `TEST_TWINE_*`; revoke at test.pypi.org → API tokens, mint a new one, replace the value there; CI publishes by OIDC, so nothing under `.github/` changes.
2. **Time-critical**: in the two live `su - duplicati` shells, run `history -c; unset HISTFILE`
   before they exit (their in-memory history is unobservable until then — B3 O-10).
3. `sudo ls -la --time-style=full-iso /usr/lib/duplicati/data/` — a `-wal`/`-shm` dated 09-18
   21:03 means the main file may be cleartext (a second key-free source; B1 findings 2/7).
4. Root's `~/.bash_history` and `.viminfo` (`sudo grep -c ENCRYPTION /root/.bash_history` first — count only), `ls -la /usr/lib/systemd/system/ | grep -i duplicati` (no sudo needed: the `.duplicati.service.swp` there is root 0644 and world-readable — 0 `ENCRYPTION` lines at 15:05 CDT; no `duplicati.service~`, no `duplicati.service.d/`; the loaded unit is the vendor file there — so only root's history and viminfo need the owner), for 09-18 20:42–21:03 (the only remaining candidate sources for the 09-18 key;
   a candidate goes into a 0600 file), and around 2026-08-25 02:19 for the `--dbpath=…Duplicati-server.sqlite`
   invocation that identifies the Repair actor (B1 O4).
5. In a subshell — `( set -a; . ~/.config/duplicati-backup/env; set +a; duplicati-cli list file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi --version=0 --no-local-db=true --dbpath=<fresh temp db> '*duplicati-server-db*' )` — the 09-18 14:00Z fileset IS the latest (version 0), which removes the `--time` parsing doubt; never `export PASSPHRASE=…` in a history-enabled shell. Confirms Procedure A0's premise (B2 checked `list`, `--no-local-db` and the `PASSPHRASE` → `--passphrase` mapping against 2.4.0.0's
   `help`).
6. CUPS: `grep -i PreserveJobFiles /etc/cups/cupsd.conf`; `sudo ls -la /var/spool/cups` (the escrow
   sheet was printed — B3 O-5); the Dropbox account's 2FA, linked devices and plan retention (B3 O-7).
7. Decisions D-1 … D-12 (§10 today) plus D-13 (Dropbox root policy, B2 A8) and D-14 (the group-write model, B3 F-6), which reconciliation creates;
   D-1 (encryption key custody) and D-4 (`CAP_DAC_READ_SEARCH` vs ACLs) gate the unit P0 installs;
   **D-2 (accept-and-scrub for the journal exposure) must be re-decided** now that the same lines sit
   in `/var/log/syslog*` and in cloud-linked transcripts (B3's top finding).
8. Execute P0 only from the reconciled, round-2-validated revision.

### 1.6 Record corrections and housekeeping

Appendix C items 1–8 are not yet applied to their targets (YAM §8.20.4 "schema-19 profile server DB",
`yamaguchi_server_db_snapshot.py:20,36` "encrypted passphrase" unconditional, the moved destination,
…; item 2's own text was rewritten by A2 #8); add B1 F14 (the pcalnon `.backup` is `enc-v1:` too).
`MEMORY.md` in the auto-memory directory was 25.4 KB against a 20 KB target; compacted to 22.0 KB on
2026-09-21 by retiring 21 closed entries (retire whole entries, never strip hooks) — still ~1.5 KB over. Re-measure with `stat -c %s` before acting; other sessions edit it.

---

## §2 — Traps (each cost time this arc or is one restart away)

- **`duplicati-server --version` STARTS a server** on port 8200 — never run it; use
  `duplicati-cli system-info` or `duplicati-server-util --version`.
- **`duplicati-server-util` defaults to `--hosturl http://127.0.0.1:8200/`** and takes `--password`
  and `change-password <new>` on argv — never use it for anything secret-bearing.
- **`duplicati-database-tool help` hides subcommand options**: `wipe-encryption` takes database
  PATHS and, on the subcommand (`help wipe-encryption`), `--server-datafolder <dir>` — default
  `$HOME/.config/Duplicati`, the pcalnon profile when run as pcalnon. Always name the copy's folder.
- **An `enc-v1:` field carries the SHA-256 of its key** — test candidates offline on a copy; a
  server-based probe on a copy whose fields are not yet encrypted "accepts" any key and poisons the copy.
- **A `%` in a unit-file `Environment=` value is a specifier**; an unknown one voids the whole
  assignment ("Invalid slot") and prints the value into the journal AND `/var/log/syslog` (rsyslog is active).
- **`EnvironmentFile=` is parsed by systemd, not a shell**: no `$VAR`, no `export`, no `$(…)`.
- **`PathExists=` re-triggers a oneshot after every termination** until the start-rate limit fails
  the path unit — a "nothing due" exit is a loop. The man page's `PathChanged=` exemption sentence is
  about activation time, not termination; the termination behaviour of `PathChanged=` is in `path.c` (verified at v259: no re-trigger).
- **The 0700 data-folder gate is checked at every start**; a pre-existing folder with any
  group/other bit is refused regardless of argv. `/home/pcalnon/.local/state` is 0700 too, so the
  service user cannot reach the snapshot target.
- **Opening a live SQLite database in place can checkpoint or truncate its WAL.** Use
  `util/ad-hoc/2026-09-21_duplicati_server_db_forensics.py`, which copies `.sqlite`+`-wal`+`-shm`
  first and opens the copy `mode=ro`. **A 4 KB `Duplicati-server.sqlite` is not empty.**
- **The snapshot file is replaced daily at 13:45 UTC** (new inode) — copy it aside before P0.
- **`DBPath` is stored ABSOLUTE and is never relocated by the server**; a data-folder move must
  move the index and re-point the row, or the first backup fails read-only and P4 deletes the index.
- **`Duplicati-server.backup` is the ORIGINAL profile DB inode**, renamed by a Repair; the
  `backups/backup … .sqlite` file is the local-DB upgrader's copy — neither is a "save".
- **The wrapper passes every option as ONE argv element** (`exec "$SERVER" "$OPTS"`); the
  `DEBUG_MODE` echoes every `.env` line into the journal (264 lines on 09-20). Never enable it.
- **Group membership is per login.** Use `sg duplicati -c '…'` for group-gated reads; the Dropbox
  daemon (started 09-19 17:36) and the user manager lack gid 139.
- **The isolation shim refuses compound shell** (functions, `$(…)` feeding a command, `HOME=` prefixes, `awk` programs, `sed -n "${n}p"`), any `cd` to the primary checkout, `git -C <primary>`, `git fetch`, and **any command line containing the word `alias`** (a git-alias guard). Put anything non-trivial in a script under the scratch
  dir and run that; tell subagents the same.
- **Six subagents in one launch tripped the session usage limit**; they were resumed with
  `SendMessage` (context intact). Launch at most three at a time; give each its own scratch subdirectory.
- **Subagent reports live only in the session transcript** — archive them verbatim in `notes/`
  (with `<!-- markdownlint-disable -->`) as soon as they land; scan for secret-shaped content first.
- **A ✔ made against the wrong `help` level is still a ✔** — this handoff's first draft carried
  one (B2 D9). Re-make any check you act on.
- **`wipe-encryption --dry-run` is not read-only**: it flips the copy to WAL mode and changes its hash, and with no database argument it targets the DEFAULT folder — the orphaned pcalnon profile.
- **The pinned markdownlint hook runs with `--fix`** and rewrites files; lint with the cached binary and no `--fix`.
- Never delete or move anything under `/mnt/Backups/Ubuntu/` (the ONE exception, on owner
  sign-off, is the escrow copy per B2 A3); never copy anything INTO `…/Backups/Yamaguchi/`.
- The worktree `.claude/worktrees/curious-plotting-hummingbird` is **DO NOT SWEEP**; it holds S-7.

---

## §3 — Verify starting state

```bash
# Run from YOUR worktree root: a worktree-isolated session refuses `cd` to the primary checkout,
# `git -C <primary>` and `git fetch` (a ref write). Read the primary's branch as a file.
git ls-remote origin main; git log --oneline -3 origin/main                  # the handoff PR must be in origin/main
cat /home/pcalnon/Development/python/Juniper/juniper-ml/.git/HEAD           # the primary's branch
ls -la notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-*                    # design + 3 record files
grep -n '^\*\*Status\*\*' notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md
grep -c '^## Report ' notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md   # 6
grep -c '^## Report ' notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-STEP-REPORTS-RECORD.md        # 5
python3 util/ad-hoc/2026-09-21_lint_design_snippets.py \
    --doc notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md --workdir /tmp/snips | tail -1
systemctl show duplicati.service -p ActiveState,MainPID,ExecMainStartTimestamp,User,NeedDaemonReload
ss -tln | grep -E ':8200|:8300'                                     # 8300 = still the empty server
ls -la --time-style=full-iso ~/.local/state/duplicati-server-db/   # recovery source; replaced daily 08:45 CDT
tail -1 ~/.local/state/duplicati/server-watchdog.log               # UNREACHABLE/401 until P0 step 9
ls -t /mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi/ | head -1     # newer than 20260918T140000Z means P0 ran
```

Expect: status line contains `reconciliation PENDING`; report counts 6 and 5; the snippet linter
reports `blocks: 12  failures: 0`; `NeedDaemonReload=no`; `MainPID` unchanged from §0 (1397393) — if it differs, the armed `ExecStart` has fired: read `NRestarts`, `ss` and the journal, and stop treating §0 as current; port 8300 only. Until the PR in §4 has merged, `git ls-remote origin main` will not equal the PR's `mergeCommit` (`gh pr view <N> --json mergeCommit`; `git log origin/main` shows the LAST-FETCHED ref), and the five file checks — the `ls`, the three `grep`s, the snippet linter — pass only in a
checkout carrying the branch.

---

## §4 — Git / session state

Branch `docs/backup-infrastructure-integrated-design` will be opened by GitHub-signed API commit
(`util/open_signed_pr.py`) from `origin/main` and, with the owner's in-session approval of
2026-09-21 ("handoff should be validated by consensus, archived, merged, and PR'd"), merged as
PR_NUMBER_PLACEHOLDER. Derive both ends yourself: `git rev-parse --short origin/main`;
`gh pr view <N> --json state,mergedAt,mergeCommit`; `gh pr list --state merged --search 'head:docs/backup-infrastructure-integrated-design'` (this repo merges several PRs a day; `--limit 5` will not find it).

**Changed by that PR** (all new): `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`,
`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`,
`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-STEP-REPORTS-RECORD.md`,
`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-HANDOFF-CONSENSUS-RECORD.md`,
`util/ad-hoc/2026-09-21_duplicati_server_db_forensics.py`, `util/ad-hoc/2026-09-21_env_file_shape.py`,
`util/ad-hoc/2026-09-21_lint_design_snippets.py`, `util/ad-hoc/2026-09-21_wrap_long_markdown_lines.py`,
`util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py`, `util/ad-hoc/2026-09-21_env_value_equality.py`,
and this file. No live system state was changed by the session. The worktree used was
`.claude/worktrees/atomic-sauteeing-truffle` (branch `worktree-atomic-sauteeing-truffle`, never
pushed); an earlier handoff draft (`HANDOFF_2026-09-21_backup-redesign-root-cause-found-recovery-runbook-written.md`)
was superseded before it was ever committed and exists nowhere.

The owner's primary checkout is on `main` (`d721fc78` at 13:48 CDT) and is what the live wrapper
symlink `/home/duplicati/bin/duplicati-wrapper.bash` resolves to — a `git checkout` or a `git pull` there (the primary is behind `origin/main`) changes what the service runs next. The LOADED unit is the vendor file `/usr/lib/systemd/system/duplicati.service` (edited in place, `Restart=always`, no drop-in); the design's `etc/systemd/system/duplicati.service` will SHADOW it, not replace it — the installer must say so.

---

## §5 — Out of scope

The tar/USB lane's historical defects (ml#1439/#1440) and its class-2 drill are closed and were not
re-derived; §7.8/§7.9 add a scheduler and a third destination on top of the script as it is, and
its `/run/media` breakage (§4.5) is a new finding. The Dropbox account's own security posture was
not evaluated beyond B3's O-7 asks. Dropbox Rewind was not evaluated — **B3 F-13 dissents**: Rewind
and version history are a design item (the sole recovery from a mass delete), and a new set must
delete-forever the old one; carried as dissent, not as scope. The five step reports were not
re-validated as such; the design drafted from them was.

---

## §6 — What the validation of THIS handoff caught (read before trusting it)

Three independent agents reviewed the first draft of this handoff (reports archived verbatim in
`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-HANDOFF-CONSENSUS-RECORD.md`; the procedure is
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`), then one
agent checked the corrected text (round 2). What round 1 caught, most consequential first:

1. **A ✔ that was wrong.** The draft said `duplicati-database-tool wipe-encryption` has no
   `--server-datafolder` — measured against the TOP-LEVEL `help`, which hides subcommand options; the
   subcommand's help lists it (default: the orphaned pcalnon profile). Two lanes caught it (Lane B1 from
   Lane A3's archived capture, Lane B2 by running `--dry-run` on a scratch copy). It would have stripped a
   correct option from P0 step 5 and written a false fact into §11. Every ✔ now says which instrument
   made it.
2. **Sixteen findings dropped**, four of them owner-time-critical: `history -c; unset HISTFILE` in the two
   live `su - duplicati` shells (B3 O-10), the possibly world-readable `PASSPHRASE=` in the primary
   checkout `.env` (B3 O-6 — answered: zero such lines, but twelve other secrets), the Slack tokens in
   that same 0664 file (A1 Q1), and the re-decision of D-2 now that the journal lines also sit in
   `/var/log/syslog*` and in cloud-linked transcripts (B3's top finding). All sixteen are now carried.
3. **Three dispositions misstated what the lanes said** where round 2 would re-check them: the
   `PathChanged=` man-page claim (a conflation of two paragraphs — B2's, repeated by the draft), B1 F1's
   "≠ the literal" (trivially true; the inference is "≠ the 21:03 key"), and `DELETE FROM Schedule`
   presented as a lane's fix (it is the orchestrator's addition; the lanes' fixes are D17/F-17/D6).
4. **The TestPyPI-token note understated the exposure**: the values reached a subagent transcript (a
   cloud-linked sink), not only a scratch file.
5. **The draft asserted a merged PR that did not exist yet**, so its own §3 could not pass; §0/§3/§4 now
   say "to be merged" and which checks fail until then.
6. **Commands a fresh worktree session cannot run** (`cd` to the primary checkout, a fetch,
   `git -C <primary>`, anything containing the word `alias`), a `gh pr list --limit 5` that would not
   find the PR, a probe invocation with no candidate-file argument, owner items without a "where"
   (`~/.bashrc`, `/usr/lib/systemd/system/`), decisions D-13/D-14 that do not exist in §10 yet, a
   round-2 pool below the procedure's §3 sizing with no done-criterion.
7. **Counts and dates**: nine `enc-v1:` values in the snapshot (four tested) and eleven in the `.backup`,
   with three different key hashes across snapshot / `.backup` / live database (which excludes the
   passphrase without any candidate test); five `Invalid slot` lines on 09-18, not four; nine Repair
   failures on 08-25, not three; `.dropbox-dist`'s "since 09-14" was an mtime; transcript line counts
   grow with every tool call and are not a fact.

Unresolved after round 1, carried as dissent in §1.1: the specifier-line count (instrument
differences), exclude-vs-delete for the escrow copy, `.env` 0600 vs 0640 root:duplicati, the
group-write model, the server-util prompt path, the alias-only references.

**Round 2** (one agent, briefed on the fifteen corrections above) confirmed every correction was applied
and true, verified two of them from source (systemd v259 `path.c`: `PathChanged=` does not re-trigger on
termination, so the §7.8 fix is sound; Duplicati `ServerUtil/Connection.cs` at the 2.4.0.0 tag: a console
password prompt exists, settling B1 F12 vs B2 D5 for B1), and found sixteen regressions or leftovers — all
folded in: stale "what is applied" lists in four places; the probe must take the candidate ALONE on stdin
(it keeps only the last key line); §3's "first three checks" wording; an `/etc/default/duplicati` fix
mis-attributed to B3; the alias-reference count (44 anchored, not 41–42); `--webservice-password-init` CAN carry
its value on argv (a Password-type option, exit 102/103); the option-name scan must cover every
`/usr/lib/duplicati/*.dll`; `sudo` is unnecessary for the unit-directory listing and the vim swap file is
world-readable; transcript pattern counts are an upper bound. By §1.2's own criterion that round changed
dispositions and numbers, so a third, single-agent pass re-checked those sixteen fixes.

**Round 3** (one agent, briefed on round 2's sixteen fixes) confirmed all sixteen applied and true,
reproduced round 2's hashes for the `wipe-encryption --dry-run` side effect, and found five leftovers:
`--settings-file` is a `duplicati-server-util` option, not a server one — the server's file channel for
`--webservice-password-init` is `--parameters-file` (B3 F-15 had named the wrong option); the short-form
reference count is 44, not 46 (an anchored `grep -o`; the orchestrator re-counted); "two record
files" → three; a `# design + 2 record files` comment; "three places" → four. All five are folded in. A
fourth round was not run: the three changes were two counts and one option name, each re-measured by the
orchestrator after the edit (the count above, and a UTF-16 scan of the 2.4.0.0 assemblies for
`parameters-file`); the loop's "changes nothing" criterion is met to that extent and no further, and
the record says so.
