# HANDOFF 2026-10-26 (second) — backup arc: Phase C lines 0–8 done; the Tier 2 and Tier 3 runs, then Phase D

Session "backup work arc 1" (`d96fe0a3`, worktree `moonlit-wobbling-beacon`), continuing the prior handoff below. Host `yamaguchi`.

**Backups are still down.** Tier 1 (Duplicati) has made no backup since 2026-09-18 14:12 UTC. The newest Tier 2 archive is from 2026-08-28. Tier 3 has never run.

Every reference below carries its file. After this table, the three long names are shortened:

| Short form | File |
| --- | --- |
| `…RECOVERY-PLAN.md` | `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` — the phase plan: §6.3 is Phase C, §6.4 Phase D, §6.5 Phase E, §6.6 the owner decisions |
| `…INTEGRATED-DESIGN.md` | `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` — the design of record |
| `…lines-3-to-8…md` | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_backup-phase-c-lines-3-to-8-then-drives-then-phase-d.md` — the prior handoff (juniper-ml#2344) |

## Continue

Continue the backup arc **interactively with the owner**, in the order the owner set on 2026-10-25:

1. **The Tier 2 lane, then the Tier 3 lane** (Remaining §1 and §2). All three drives are mounted. The session may run each installer and first run itself, but only on the owner's explicit go, **asked for each tier**. Never hand either to a subagent.
2. **Phase D** (`…RECOVERY-PLAN.md` §6.4) in one owner sitting, with the rulings and deltas below. The owner needs `sudo` and the passphrase from the printed sheet or the password manager, **not** the Dropbox copy.
3. **The decision-record PR** (Remaining §4). It gates nothing, so it fits Tier 3's hours-long first run.
4. **Phase C's last row**, the transcript count (Remaining §5). Its tool does not exist yet, and it must run **before Phase D step 9** if it is to count the values only the service `.env` holds.

Merge approval covered this session's handoff PR only. Ask again for the next session's PRs.

## Completed: Phase C (`…RECOVERY-PLAN.md` §6.3), 2026-10-25 and 2026-10-26

The owner ran each line in their own terminal; the session checked it read-only afterwards. "Line N" is the sessions' numbering; the `…RECOVERY-PLAN.md` §6.3 item is in brackets. Lines 0–2 are the prior session's (`…lines-3-to-8…md`), re-measured 2026-10-26.

| Line | Result |
| --- | --- |
| 0 (item 9) | `yamaguchi-server-db-snapshot.timer` reads `disabled` (O-10). |
| 1 (item 1) | `/usr/lib/duplicati` and `/etc/default/duplicati` are `root:root`; `/home/duplicati/bin` is gone. |
| 2 (item 2) | `duplicati`'s shell is `/usr/sbin/nologin`. The server (pid 1397393, up since 2026-09-20) is that user's only process. |
| 3 (item 4) | `sqlite3` `3.46.1-9ubuntu0.3`, `/usr/bin/sqlite3`, `ii`. The owner considered PostgreSQL and kept SQLite: Phase D edits Duplicati's own SQLite files, and `duplicati 2.4.0.0` ships SQLite providers only (no assembly references Npgsql). |
| 4 (item 5) | Lines matching `encryption`/`passphrase`/`password`/`dbpath`: root `.bash_history` 2, `.viminfo` 3; duplicati `.bash_history` 20, `.viminfo` 10. Root, `dbpath` alone: 0 and 0. The duplicati files' size and mtime still match `…INTEGRATED-DESIGN.md` §6's record (which holds no counts). |
| 5 (item 6) | `/usr/lib/duplicati/data/`: `BMXWPAOGLP.sqlite` 1,365,446,656 B (09-18 09:12:56 CDT), `Duplicati-server.sqlite` 245,760 B (09-18 21:03:34.670), `OVFDREJHJT.sqlite` 1,114,112 B (08-25 04:00:33), `control_dir_v2/` (09-18 21:08:05), `installation.txt`, `machineid.txt`. **No `-wal`, `-shm` or `-journal`.** |
| 6 (item 7) | The four duplicati-home copies read `600`. CUPS: `PreserveJobFiles` is unset, so documents are kept one day (`cupsd.conf(5)`). |
| 6b (new) | Five orphaned spool documents, with no matching `c…` file: three copies of the escrow sheet printed 08-30 and two test pages (the owner checked). The owner shredded all five; `ls -la /var/spool/cups \| grep ' d0'` prints nothing. |
| 7 (item 3a) | Both `PASSPHRASE` and `PASSPHRASE_OLD` match their 08-25 fingerprints (quotes stripped) and equal the live credential file: `VERDICT: remove the file (the file only)`. The S-7 `.env` is gone; `curious-plotting-hummingbird` is intact. |
| 8 (items 3b, 3c) | `/mnt/Backups/Ubuntu/_yamaguchi_keys/` is `0700`, its `env` and `README.md` `0600`, all `pcalnon:pcalnon`: `cp -a` ran in a shell without gid 139, so it could not keep group `duplicati` (the user is a member). `cmp`: both SAME. The Dropbox `env` is `0600`. |

Closed in `…lines-3-to-8…md`, recorded here so it is not lost: `secret_scanning_non_provider_patterns` returns 200 on PATCH but stays `disabled`, so it is not offered for this repo. B9's rule and hook carry that control, and nothing is owed.

What the results establish:

- **Note 1's key-free source does not exist.** `…INTEGRATED-DESIGN.md` §4.2 note 1 read the data folder's 21:03:34 mtime as a `-wal`/`-shm` that was created and never removed, so the main file might still hold pre-encryption cleartext.
  - No side file exists, which is note 1's own test.
  - The server DB's mtime (21:03:34.670) comes 1 ms before the folder's (21:03:34.671): a final write, then a side file's *removal*.
  - The folder never changed again, although `control_dir_v2` shows the 21:08 starts used it. So those starts only read (an inference).
  - Recovery: Procedure A on a match, otherwise A0. A2 (only if the 09-18 fileset cannot be read) and Procedure B (the last resort) remain the fallbacks (`…RECOVERY-PLAN.md` §6.4 steps 7 and 8).
- **The encryption window narrows** (an inference from the same timestamps): the fields were encrypted by 21:03:34.67, not "between 21:03:27 and 21:08:06" (`…INTEGRATED-DESIGN.md` §4.1 and §4.2).
- **`…INTEGRATED-DESIGN.md` §5.3's last lead is negative.** Root's retained history holds no `dbpath` line, and `…INTEGRATED-DESIGN.md` §5.3 found none in `pcalnon`'s. The journal cannot help: it now starts 2026-10-18. Agent sessions write no `.bash_history`, so the 08-25 Claude Code transcripts are the one source nobody has examined. A search there must count and timestamp, never print. It gates nothing.
- **The credential file A0 reads still holds the 08-25 passphrases.** The S-7 values match both their fingerprints and `~/.config/duplicati-backup/env`, so that file's 2026-09-18 20:45 rewrite changed neither passphrase.
- **The CUPS sink was real.** `lpr` hands CUPS its own copy of the document, so the `shred -u` in `notes/backup_tests_pre-and-post_reboot.md` destroyed only the source. A document whose `c…` file is gone is never purged by the one-day default: `d00045-001` dated from 2025-09-23. The count-only verbatim-line check returned 0 on all five, because the sheet lays the values out differently; the owner identified them by inspection.
- **The journal has aged out the 09-20 secret echoes.** It holds one boot (up since 2026-09-07), whose first entry is Sun 2026-10-18 08:22:47 CDT, at 3.9G: journald has rotated the older entries out. That changes Phase D step 2 (Remaining §3).
- **The Tier 2 installer's dry run is clean** (Remaining §1).

## Owner rulings, 2026-10-10 to 2026-10-26 — not yet written into `…RECOVERY-PLAN.md`

| # | Ruling | Against the recommendation? |
| --- | --- | --- |
| O-1, O-2 | In Phase D, after the freeze, **probe the 64-character `SETTINGS_ENCRYPTION_KEY`** from the moved-aside service `.env` offline. A **match → Procedure A** plus P0.5b's two-start re-key to a fresh `/etc/credstore` key. **No match → A0.** No history-candidate search (B11 is not built). Then both `.env` keys are superseded and the `.env` is shredded. | partly (note a) |
| O-9 | Re-encrypt the frozen set and the old dlists as a second pass of the rotation (`…INTEGRATED-DESIGN.md` §10.2). | no |
| O-10 | Disable the snapshot timer now. **Done** (Line 0). | no |
| O-11 | The owner rotates the TestPyPI token (I-31). **Open.** | no |
| O-12 | `/etc/duplicati/env` is `0640 root:duplicati`. | no |
| O-13 | **Keep** `additional-report-url`. Its per-run warning under `IPAddressDeny=` is expected and allow-listed. | **yes** — the recommendation was to clear it |
| O-14 | `--aes-version=2` until the rotation. | no |
| D-3, D-7, D-11, D-13 | `…INTEGRATED-DESIGN.md`'s recommendations. | no |
| D-5 | Tier 3 is `…INTEGRATED-DESIGN.md` §7.9's default: the 10 repos plus `juniper-legacy` and the parent's `notes/ prompts/ util/ backups/`, label `full`, monthly while the drive is attached. It keeps the last 3 sets and deletes an older one only after a restore drill of the newest. Target: `Juniper/Backups` on "Blackbox Part 1" (UUID `dee46823-4119-4914-ac15-08194ee27d81`). | no |
| D-10 | Tier 2 runs weekly and keeps everything. | **yes** (retention) — `…INTEGRATED-DESIGN.md`'s D-10 row recommends pruning sets older than 8 weeks after a drill |
| drives | `/etc/fstab` is the primary reference for external drives. `extruder` is not a backup target. `/mnt/JuniperArchive` is deprecated. | — |
| 2026-10-26 | Keep `sqlite3` for Phase D; PostgreSQL rejected (Line 3 above). | no |
| 2026-10-26 | Remove the orphaned spool documents (Line 6b). **Done** by the owner. | — |

- **(a)** The O-1/O-2 ruling adds the probe and, on a match, Procedure A, because the owner wants to keep the root-era history. Its end state is still the recommendation's: a fresh credstore key, with both `.env` keys retired.

The **2026-10-08 retention ruling** still holds. Retention is suspended through recovery. After AC-4's first drill, the five dlists it would delete are copied aside, then retention is restored as `2W:1D,6M:1W,2Y:1M,5Y:2M`. The `keep-time` and `keep-versions` defaults are never restored.

## Remaining, in order

### 1. Tier 2 (`…RECOVERY-PLAN.md` §6.3 item 8; AC-10 in `…INTEGRATED-DESIGN.md`; no `sudo`)

**Dry run, measured 2026-10-26** from `moonlit-wobbling-beacon` at `31b34c39`:

- Preflight passes: not root, 7 source files, `systemctl`, `Linger=yes`.
- It would install `juniper-backup.bash` and `juniper-backup-scheduled.bash` (new) and the four units (new).
- It would update the shared reporter `~/.local/bin/duplicati-backup-failure.bash` (`changed`, 1.0.0 → 1.1.0). Only comments and the notification title differ; the title now names the failed unit. The old Duplicati user lane also calls it, and that lane's timer is `disabled`.
- It then runs `daemon-reload` and `enable --now` on `juniper-backup.timer` and `juniper-backup.path`.
- Both gpg recipients (`…Yubikey-3c_2026-08-06`, `…Yubikey-3a_2026-08-11`) are in the keyring with ultimate trust; their encryption subkeys are valid to 2028-08-05 and 2028-08-10.

Steps:

1. Get the owner's go for the install **and** the first run. Run the installer from a checkout whose `util/` matches `origin/main`: it copies from its own folder (`REPO_UTIL`), so a lagging primary checkout installs stale scripts. `bash util/install_juniper_backup_timer.bash --dry-run`, then without `--dry-run`.
2. Nothing starts by itself:
   - The `.path` unit is `PathChanged=/run/media/pcalnon`, which does not fire when the unit starts.
   - The timer's first window is Sunday 2026-11-01 03:00, plus up to 15 minutes. `Persistent=true` should not catch up on a fresh install, which has no stamp; check with `systemctl --user list-timers juniper-backup.timer`.
   - With both sticks mounted, start the OK run: `systemctl --user start --no-block juniper-backup.service`.
   - Poll `systemctl --user show -p ActiveState,Result juniper-backup.service`. The scheduler writes `~/.local/state/juniper-backup/last-run.status` only when a run ends. For the log, the session uses `journalctl --user -u juniper-backup.service -n 50 --no-pager`; `-f` never returns in its non-interactive shell.
3. Verify a new archive under `Juniper-8.0.0.python/` on **both** sticks. With one stick the run is PARTIAL (rc 4) and reads `FAILED`.
4. Then, with no stick mounted, `systemctl --user start juniper-backup.service` should read `SKIPPED`. It only does so after the first success.
5. Then the class-1 pipeline drill: `bash util/ad-hoc/2026-08-26_backup_restore_drill.bash`. Read it first.
6. Then **the owner** decrypts one real archive with the YubiKey (PIN and touch). This is the key class the drill cannot cover.

### 2. Tier 3 (`…INTEGRATED-DESIGN.md` §7.9; D-5; no `sudo`)

1. The owner's go, then `bash util/install_juniper_backup_timer.bash --lane full --dry-run`, then for real. **Install it only when ready to start its first set**, and after Tier 2's no-stick step. Its `.path` unit watches the same directory as Tier 2's. Until Tier 3's first success, any trigger runs its check: with the drive attached it starts the first set; with the drive detached it reads `FAILED` and fires `OnFailure=`.
2. The drive is already mounted, so no mount event comes. Start the first set by hand: `systemctl --user start --no-block juniper-backup-full.service`. Poll `systemctl --user show -p ActiveState,Result juniper-backup-full.service`; `~/.local/state/juniper-backup-full/last-run.status` appears when the run ends. It is large: 15 archives, label `full`, with `juniper-legacy` alone about 18 G.
3. Verify the `full` set under `Juniper/Backups/`. Disconnect the drive only after `last-run.status` reads `result=OK`.
4. AC-11: restore one archive and diff it against the live tree. The owner's YubiKey decrypts.
5. Retention is manual: keep the last three full sets, and delete an older set only after a restore drill of the newest.

### 3. Phase D: `…RECOVERY-PLAN.md` §6.4, in one owner sitting

Run `…RECOVERY-PLAN.md` §6.4 as written, with these deltas. The first nine carry over from `…lines-3-to-8…md`; the rest are new.

- **Step 0** (the rehearsal on a throwaway data folder) is still owed: `…RECOVERY-PLAN.md` calls it "the first time any of this runs a binary on this host".
- **Step 1 is done** (Line 0). The timer stays disabled until step 13. Step 9's installer then installs a root-owned copy, so the re-enabled timer no longer runs the checkout.
- **Step 3**: re-run the stage gate. Expect `0 staged`.
- **Step 5**: "copy today's snapshot aside" is moot. The snapshot has held the *empty* server's database since 2026-10-09 (ml#2199 re-pointed the script, and the root timer ran the primary checkout's copy). The freeze of `/usr/lib/duplicati/data` is the recovery source. Note the freeze directory's date.
- **Step 7, per O-1/O-2.** The probe is `util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py`. It reads the duplicati `.env` on **stdin**, never argv.
  - Its parser takes the active `SETTINGS_ENCRYPTION_KEY` line as `ENV_ACTIVE_KEY`, the 64-character value. It ignores `SETTINGS_ENCRYPTION_KEY_OLD`, whose 32 characters match the length of the key the 2026-09-21 probe already excluded (note 3a in `…RECOVERY-PLAN.md`; an inference).
  - After step 6's `mv`, the `.env` (`0640 duplicati`) is at `/home/duplicati/.config/Duplicati.empty-2026-09-20/.env`, in a folder step 6 makes `0700`. The freeze is `0700 duplicati` too. So the probe runs under `sudo`, against a scratch **copy** of the server DB in a root-only directory, never against the freeze itself.
  - A **match → Procedure A**: at step 9 the accepted key goes to `…-key` and a random one to `…-key.new` (I-38), and step 12's re-key is `util/ad-hoc/2026-10-03_rekey_settings_key.bash`. **No match → A0.**
  - `util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash` is a different tool: a server-based probe that is "confirmation only" (`…INTEGRATED-DESIGN.md` §8 P0 step 3). It starts a Duplicati binary, so only the owner may run it, and the ruling does not need it.
- **A0's two scripts** default their job DB into the step-5 freeze (`0700 duplicati`), and under sudo-rs `HOME=/root`. Pass the variables explicitly, with a work directory on ext4, never tmpfs (`confirm_a0_premise.bash`'s rule 3; the job DB is 1.37 GB):
  - `sudo env YAMAGUCHI_ENV_FILE=/home/pcalnon/.config/duplicati-backup/env YAMAGUCHI_JOB_DB=/home/duplicati/.cache/root-data-folder-<date>/BMXWPAOGLP.sqlite YAMAGUCHI_WORKDIR=<a root-only directory> bash util/ad-hoc/2026-09-22_confirm_a0_premise.bash`
  - the same `sudo env …` prefix, then `bash util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash <restore-directory>`. The positional restore directory is required, and the script refuses one inside `/home/pcalnon` (the backup Source).
- **Step 9**: the installer refuses `/etc/default/duplicati` as **UNBLESSED**; read the difference, then re-run it with `--update-backup-behavior`. `/etc/duplicati/env` is `0640 root:duplicati` (O-12). Escrow the new key, then `shred -u` the old `.env`, which retires both of its keys.
- **Step 11**: pin `--aes-version=2` (O-14). **Keep** `additional-report-url` and record its warning as expected (O-13). Remove `retention-policy`; retention stays suspended. The watchdog already checks backup 2 (its `--backup-id 2` deploy ran 2026-10-05 19:03 CDT); its daily 401 is expected until this step.
- **Step 14**: after AC-4's first drill, copy the five dlists aside, then restore `2W:1D,6M:1W,2Y:1M,5Y:2M`.
- **New — step 2's journal scrub may be moot.** The journal now starts 2026-10-18, so the 09-20 echoes it was to remove have aged out. Take the AC-8 journal counts first (expect 0). The owner then decides whether to skip the `--rotate` + `--vacuum-time=1s`, which would now delete only unrelated history.
- **New — the root-era folder has no side files.** So step 7's scratch copy of its server DB is the main file alone, and step 9 copies `BMXWPAOGLP.sqlite` with any side file beside it: today none. Any other database the plan copies still takes its `-wal`/`-shm`. The job DB's mtime is the last Tier 1 backup (09-18 14:12:56 UTC).
- **New — no WAL route.** Note 1's second key-free source is refuted (Completed above). The primary routes are Procedure A (on a match) or A0; A2 and Procedure B remain the fallbacks.
- **New — identify `OVFDREJHJT.sqlite`.** It is in neither document. `…INTEGRATED-DESIGN.md` §5.2 read the 2026-09-20 snapshot: its `Backup` ID 2 `Yamaguchi` points at `BMXWPAOGLP.sqlite`. So this index, last written 08-25 04:00:33, the morning the job was recreated, is likely a deleted job 1's (an inference). Check the scratch copy's `Backup` table and record what you find. The freeze takes the whole folder, so nothing is lost meanwhile.
- **New — the history files are never tested under O-2.** `…INTEGRATED-DESIGN.md` §6 (its history rows and note sink-b) wipes them "once P0 step 3 has tested what they hold", which O-2 removes, so they have no wipe trigger. Recommended: keep them until AC-4's first drill passes, as a fallback for the root-era key, then wipe them at step 14. **Needs the owner's ruling** (Remaining §6).
- **New — the owner works in a root shell.** Every command typed there lands in `/root/.bash_history` at exit, which is why Phase D's tools read values from stdin or files. Anything that resolves `~` runs as `pcalnon`.

### 4. A decision-record PR (gates nothing)

Write the rulings table above into `…RECOVERY-PLAN.md` §6.6, with O-13's and D-10's dissents. Then record these findings:

- the snapshot overwrite (2026-10-09 onwards);
- the watchdog deploy is done (2026-10-05);
- A0's freeze-permission and `HOME` issue, and its restore directory's positional-argument rule;
- the probe ignores `SETTINGS_ENCRYPTION_KEY_OLD`;
- `~/.config/duplicati-backup/env` was rewritten 2026-09-18 20:45 CDT, after the fingerprints, **and the rewrite changed neither passphrase** (Line 7);
- the gitleaks fleet fix: juniper-ml#2203, #2327, #2329; juniper-deploy#259, juniper-data#490, juniper-canopy#764;
- the Tier 3 lane (juniper-ml#2331, `900eb93a`);
- `secret_scanning_non_provider_patterns` is not offered for this repo, which closes that item of `…RECOVERY-PLAN.md` §6.2's B9 row;
- Phase C Lines 0–8 and 6b, with the results table above;
- note 1 refuted, and the narrowed encryption window (`…INTEGRATED-DESIGN.md` §4.1 and §4.2);
- `…INTEGRATED-DESIGN.md` §5.3's root-history lead negative, and the agent transcripts unexamined;
- `OVFDREJHJT.sqlite`, unrecorded until 2026-10-26;
- the journal now starts 2026-10-18, and what that does to Phase D step 2;
- the CUPS sink: the escrow sheet's spool copies, the orphan mechanism and the purge. `…INTEGRATED-DESIGN.md` §6's CUPS row can close;
- two defects in `…INTEGRATED-DESIGN.md` §6's checklist:
  - its CUPS row omits `sudo` (so did `…lines-3-to-8…md`'s Line 6), and `/etc/cups/cupsd.conf` is `0640 root:lp`;
  - its server-DB copies row lacks the top-level `Duplicati.GUI.TrayIcon-crashlog.txt` (`0777`), which Line 6 chmodded;
- the history-file wipe trigger, once ruled.

### 5. Phase C's last row: the transcript count

`…INTEGRATED-DESIGN.md` §6's transcript row and its note sink-c: count Claude transcripts **and** the persisted `tool-results/` files (`…INTEGRATED-DESIGN.md` note sink-a) by value, never with a value on argv. Purge only within the release's transcript limit (`…RECOVERY-PLAN.md` §6.1 item 5). No tool does this yet ("the method is follow-up", note sink-c).

- The session can write one under `util/ad-hoc/`: it reads the values from the credential files by path and prints per-file counts only. The owner runs it, because it reads secrets.
- **Sequence:** Phase D step 9 shreds the service `.env`, the only holder of the 64-character key and its commented secrets, so a count after step 9 covers only `PASSPHRASE` and `PASSPHRASE_OLD`.

### 6. Owner questions and actions still open

- **O-11**: rotate the TestPyPI token.
- **The history-file wipe trigger** (Phase D's "New" delta above). Recommended: Phase D step 14, after AC-4's first drill.
- **Phase D step 2**: skip the journal vacuum if the AC-8 counts read 0?
- **The transcript counter** (§5): build and run it before Phase D step 9, or count only the two passphrases later?
- **D-12** (inherited items, each with its own disposition in the P3/P4 review) has no recorded ruling. `…RECOVERY-PLAN.md` §6.6 O-5 recommends that the design's recommendation stand.
- **juniper-recurrence runs no secret scan** in any workflow (2026-10-25 survey). Does the owner want a follow-up PR?
- **juniper-data** has an older commit allowlist that hides a 36-character UUID-shaped value assigned to `ARC_AGI_API`. Its comment calls it a public identifier, and nobody has verified that. Is it a public identifier or a key?
- Optional: search the 08-25 agent transcripts for `…INTEGRATED-DESIGN.md` §5.3's Repair actor, count and timestamp only.

### 7. Later: Phase E (`…RECOVERY-PLAN.md` §6.5)

- **P1**: S-4's in-tree delete on sign-off (the Dropbox copy of `_yamaguchi_keys`; the out-of-Dropbox copy now exists, Line 8), and the Dropbox account audit.
- **P2**: D-14's destination permissions, then AC-7, AC-5, AC-12 and AC-9.
- **The rotation** (`…INTEGRATED-DESIGN.md` §10.2), with O-9's second pass.
- **P3's remainder** is §1 and §2 above.
- **P4**, after seven consecutive successful daily runs.

## Key context and traps

- **A unit that runs a checkout deploys every merge.** The root snapshot timer ran the primary checkout's script, so ml#2199's merge changed what root ran. The Tier 2/3 installers *copy* their scripts into `~/.local/bin`, so re-run an installer to update them. Either lane's installer rewrites all three shared scripts.
- **The `.path` units fire only when an entry under `/run/media/pcalnon` is created or removed.**
  - A desktop automount does that; the internal Windows NTFS partition, `848099D78099CFD2`, is automounted there.
  - An fstab mount on an existing mount point may not: systemd creates a missing mount point but does not remove it, and an empty `raspi-drive` directory (root, 2026-10-09) sits there now.
  - So whether re-plugging a stick fires a run is untested; `…INTEGRATED-DESIGN.md` §7.8 says to test it. The weekly timer is the backstop.
- **A second trigger during a run.** A second start of the running oneshot is merged by systemd. A separate scheduler process that loses the flock goes through `skip_or_fail`. Before the lane's first success, or past `STALE_DAYS`, that reads `FAILED`, exits 1, fires `OnFailure=`, and overwrites `last-run.status` while the other run continues.
- **The Tier 1 server must stay up.** It has run since 2026-09-20 (pid 1397393). Never restart it: Phase D step 6 is the one stop.
- **`curious-plotting-hummingbird` is DO NOT SWEEP.** Its `.env` is gone; the worktree stays.
- **A count-only match can read 0 on a real copy.** The spool check matched the escrow's assignment lines verbatim and found none, because the sheet's layout differs. A zero there proved nothing.
- **A PR can fail Security Scan.** A squash merge mints a new SHA, so a commit-scoped `.gitleaksignore` entry cannot pre-silence a PR's own finding. Use `gitleaks:allow` on the line, or restructure it. gitleaks 8.24.3 silently ignores a top-level `[[allowlists]]`; use a rule-level `[[rules.allowlists]]` with `condition = "AND"`. Predict the scan locally: pre-commit's cached `v8.24.3` binary plus `main`'s `.gitleaks.toml`, with `--redact` (memory note `reference_ci_parity_gitleaks_local_scan`).
- **The harness refuses some shell forms.** Worktree isolation refuses compound shell with variables or loops, a variable where an option may stand (`sed … $DIR/file`), `sleep` chains, and `git -C` into the primary checkout. Spell paths out, or write a small script.
- **`grep` in the session's shell is `ugrep`.** A pattern like `.{0,140}` exceeds its complexity limit. Use simple patterns.
- **`cp` is GNU 9.7** (`/usr/bin/gnucp`). `cp -a` from a process without the group's gid silently drops that group. `pcalnon` is in `duplicati`, but the shells here do not carry gid 139.
- **Merge mechanics.**
  - `gh pr checks --json` is not supported by this `gh`; use `--required`, or `util/wait_for_checks.py`.
  - Commit only through `util/open_signed_pr.py` / `util/push_signed_commit.py`, with message bodies in files (backticks are eaten on a shell line).
  - Merge with `util/safe_merge.py`, and read its `MERGED` line.

## Verify first

```bash
git fetch origin main
git log --oneline -1 origin/main
getent passwd duplicati | cut -d: -f7                                    # /usr/sbin/nologin   (Line 2)
systemctl is-enabled yamaguchi-server-db-snapshot.timer                  # disabled            (Line 0)
stat -c '%U:%G %n' /usr/lib/duplicati /etc/default/duplicati             # root:root           (Line 1)
dpkg-query -W -f='${db:Status-Abbrev}\n' sqlite3                         # ii                  (Line 3)
stat -c '%a %n' /home/duplicati/.config/Duplicati/Duplicati-server.backup # 600                 (Line 6)
test ! -e ~/Development/python/Juniper/juniper-ml/.claude/worktrees/curious-plotting-hummingbird/.env && echo absent   # absent (Line 7)
stat -c '%a %n' /mnt/Backups/Ubuntu/_yamaguchi_keys /mnt/Backups/Ubuntu/_yamaguchi_keys/env /mnt/Backups/Ubuntu/_yamaguchi_keys/README.md /mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_keys/env   # 700 600 600 600 (Line 8)
ps -o pid=,lstart= -u duplicati                                          # 1397393 Sun Sep 20 18:19:42 2026 (the Tier 1 server)
journalctl --list-boots --no-pager | head -2                             # one boot, FIRST ENTRY Sun 2026-10-18 08:22:47 CDT
findmnt -rn -o TARGET,SOURCE | grep /run/media/pcalnon                  # EBC5-F0A3, DFF3-2782, dee46823-…; also extruder and 848099D78099CFD2 (not targets)
systemctl --user list-unit-files 'juniper-backup*'                       # 0 unit files until the Tier 2 install
python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py --check         # 0 staged, 14 already current, 0 skipped
```

The owner, in a root shell: the spool directory's mtime moved again at 18:20:49 CDT, after the 18:03 shred. Confirm no new document file:

```bash
ls -la /var/spool/cups | grep ' d0'                                      # no output
```

**Git state at handoff.** This worktree is `moonlit-wobbling-beacon`, on branch `worktree-moonlit-wobbling-beacon` at `31b34c39`, behind `origin/main` by commits that touch no backup file. Nothing is staged. This handoff is the only new file, and it lands on `main` with its own PR. Nothing else in the repository changed this session.

## Limits (unchanged; every lane brief must carry them)

- never start, stop, restart, enable, disable or reload a unit;
- never run a Duplicati binary, never contact 127.0.0.1:8300, no `sudo`;
- nothing under `/mnt/Backups/Ubuntu/` beyond `stat`;
- never read a secret file;
- never print an environment variable or a token;
- no `git stash`; no interactive shells; no host actions.
