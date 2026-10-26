# HANDOFF 2026-10-26 — backup arc: Phase C lines 0–2 done; lines 3–8, the Tier 2 and Tier 3 runs, then Phase D

Session "backup, b9" (`60164a37`), continuing `HANDOFF_2026-10-08_backup-phase-b-merged-b9-next.md`. Host `yamaguchi`.

**Backups are still down.** Tier 1 (Duplicati) has made no backup since 2026-09-18 14:12 UTC. The newest Tier 2 archive is from 2026-08-28. Tier 3 has never run.

Every reference below carries its file. After this table, the two long names are shortened:

| Short form | File |
| --- | --- |
| `…RECOVERY-PLAN.md` | `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` — the phase plan: §6.3 is Phase C, §6.4 Phase D, §6.5 Phase E, §6.6 the owner decisions |
| `…INTEGRATED-DESIGN.md` | `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` — the design of record |

## Continue

Continue the backup arc **interactively with the owner**, in the order the owner set on 2026-10-25:

1. **Finish Phase C** (`…RECOVERY-PLAN.md` §6.3) **from Line 3**, one line at a time. The owner runs each line in their own terminal. The session checks it read-only, then presents the next. "Line N" is this session's numbering, not §6.3's item numbers; the mapping is under Remaining §1.
2. **Run the Tier 2 and Tier 3 lanes.** All three drives are attached and mounted (re-measured 2026-10-26).
3. **Run Phase D** (`…RECOVERY-PLAN.md` §6.4) with the owner's rulings below. The owner needs `sudo` and the passphrase from the printed sheet or the password manager, **not** the Dropbox copy.

Merge approval covered this session's PRs only. Ask again for the next session's.

## Completed (2026-10-10 → 2026-10-26)

Seven PRs, all merged, with green post-merge runs on each `main`:

| PR | Merge commit | What it did |
| --- | --- | --- |
| juniper-ml#2203 | `bf595395` (10-10) | B9. CI's gitleaks had loaded **zero rules** since 2026-08-13, because a `.gitleaks.toml` without `[extend] useDefault = true` loads only its own rules. Now it runs the default rules plus the `juniper-secret-assignment` content rule, with a pre-commit hook at `v8.24.3` (= `ci.yml`'s `GITLEAKS_VERSION`) and commit-scoped `.gitleaksignore` entries. |
| juniper-ml#2327 | `fc65c2d7` (10-25) | The nine-repo survey and the probe driver: `util/ad-hoc/2026-10-25_gitleaks_fleet_survey.py`, `util/ad-hoc/2026-10-25_gitleaks_probe_for_repo.py`. |
| juniper-ml#2329 | `2f96a051` (10-25) | The rule now fires on a quoted value that contains spaces. |
| juniper-ml#2331 | `900eb93a` (10-25) | Tier 3 becomes a scheduled lane: `install_juniper_backup_timer.bash --lane full`, the units `juniper-backup-full.{timer,path,service}` and `juniper-backup-full-failure.service`, and state under `~/.local/state/juniper-backup-full`. `JUNIPER_BACKUP_DIR` may now be a path (`Juniper/Backups`). `…INTEGRATED-DESIGN.md` §7.8/§7.9 were re-extracted. |
| juniper-deploy#259, juniper-data#490, juniper-canopy#764 | `7b4454b0`, `97c5aeb8`, `da08414f` (10-25) | The same zero-rule gitleaks defect in the three siblings. Their histories held only false positives (2, 27, 18), each ignored per commit with its class named. data and canopy also carry a narrow rule-level allowlist for conda build strings. |

On the host, verified read-only on 2026-10-26:

- **Line 0** (O-10): `yamaguchi-server-db-snapshot.timer` reads `disabled`.
- **Line 1** (P0.5a item 1): `/usr/lib/duplicati` and `/etc/default/duplicati` are `root:root`, and `/home/duplicati/bin` is gone.
- **Line 2** (P0.5a item 7): `duplicati`'s shell is `/usr/sbin/nologin`. The server (pid 1397393, `--webservice-port=8300`, up since 2026-09-20) is still that user's only process.

Also measured:

- **The stage gate** (`util/ad-hoc/2026-09-22_stage_design_artifacts.py --check`) read `0 staged, 14 already current, 0 skipped` on `main` at `900eb93a`. Nothing backup-related has merged since.
- **`secret_scanning_non_provider_patterns`**: the owner said enable it. The PATCH returns 200, but the setting stays `disabled`, so it is not offered for this repo. B9's rule and hook carry that control. Nothing is owed.

**This handoff's own PR** also commits `util/ad-hoc/2026-10-10_s7_env_reconcile.py`, Line 7's checker, which has sat untracked since 10-10. It prints names and booleans only. Its two recorded fingerprints were already on `main`, in four files.

## Owner rulings, 2026-10-10 and 2026-10-25 — not yet written into `…RECOVERY-PLAN.md`

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
| D-10 | Tier 2 runs weekly and keeps everything. | — |
| drives | `/etc/fstab` is the primary reference for external drives. `extruder` is not a backup target. `/mnt/JuniperArchive` is deprecated. | — |

- **(a)** The O-1/O-2 ruling adds the probe and, on a match, Procedure A, because the owner wants to keep the root-era history. Its end state is still the recommendation's: a fresh credstore key, with both `.env` keys retired.

The **2026-10-08 retention ruling** still holds. Retention is suspended through recovery. After AC-4's first drill, the five dlists it would delete are copied aside, then retention is restored as `2W:1D,6M:1W,2Y:1M,5Y:2M`. The `keep-time` and `keep-versions` defaults are never restored.

## Remaining, in order

### 1. Phase C, Lines 3–8 (the owner's terminal)

This session numbered the block differently from `…RECOVERY-PLAN.md` §6.3:

| This session's Line | §6.3 item |
| --- | --- |
| 0 | 9 (O-10) |
| 1, 2 | 1, 2 |
| 3, 4, 5, 6 | 4, 5, 6, 7 |
| 7, 8 | 3(a), and 3(b) with 3(c) |
| the drives step (§2 below) | 8 |

This is the block the owner already has, from Line 3 on:

```bash
# 3. sqlite3 for P0 steps 3 and 8
sudo apt install -y sqlite3
# 4. count-only history probe — prints counts, never lines; wipe nothing
sudo grep -c -i -e encryption -e passphrase -e password -e dbpath /root/.bash_history /root/.viminfo /home/duplicati/.bash_history /home/duplicati/.viminfo
# 5. the released read of the root-era data folder
sudo ls -la --time-style=full-iso /usr/lib/duplicati/data/
# 6. sink checklist: CUPS spool + the world-readable server-DB copies
grep -i PreserveJobFiles /etc/cups/cupsd.conf; sudo ls -la /var/spool/cups
sudo chmod 0600 /home/duplicati/.config/Duplicati/Duplicati-server.backup /home/duplicati/.config/Duplicati/Duplicati.GUI.TrayIcon-crashlog.txt /home/duplicati/.config/Duplicati/temp1/Duplicati.GUI.TrayIcon-crashlog.txt /home/duplicati/.config/Duplicati/backups/Duplicati-server_2026-08-22_pre-dbpath-fix.sqlite
# 7. S-7: reconcile (names and True/False only), then remove the FILE only — its worktree is DO NOT SWEEP
python3 /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/precious-toasting-twilight/util/ad-hoc/2026-10-10_s7_env_reconcile.py && rm /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/curious-plotting-hummingbird/.env
# 8. S-4: chmod the escrow, copy it out of the Dropbox root, compare without printing
chmod 0600 /mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_keys/env
test ! -e /mnt/Backups/Ubuntu/_yamaguchi_keys && cp -a /mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_keys /mnt/Backups/Ubuntu/_yamaguchi_keys
chmod 0700 /mnt/Backups/Ubuntu/_yamaguchi_keys && chmod 0600 /mnt/Backups/Ubuntu/_yamaguchi_keys/*
for f in env README.md; do cmp -s "/mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_keys/$f" "/mnt/Backups/Ubuntu/_yamaguchi_keys/$f" && echo "$f SAME" || echo "$f DIFFERS"; done
```

| Line | State on 2026-10-26 | The session's check afterwards | What the owner pastes |
| --- | --- | --- | --- |
| 3 | `sqlite3` not installed | `dpkg-query -W -f='${db:Status-Abbrev}\n' sqlite3` reads `ii` | — |
| 4 | — | none (root's files) | The four counts. Under O-2 a non-zero count changes nothing (there is no B11 extraction), but record them. The `dbpath` count also bears on the 2026-08-25 Repair actor that `…INTEGRATED-DESIGN.md` §5.3 asks about. |
| 5 | — | none | The listing. Any `BMXWPAOGLP.sqlite-wal`, `-journal` or `-shm` is copied with the index at Phase D step 9. A server-DB `-wal`/`-shm` dated 09-18 21:03 is a second key-free source (`…INTEGRATED-DESIGN.md` §4.2 note 1). |
| 6 | the four copies are `777`, `777`, `644`, `644` | `stat -c '%a %n'` on the four reads `600` | the CUPS output |
| 7 | the S-7 `.env` exists (`0664`, 2026-08-23) | `test ! -e` on it | The checker's output. On `do NOT remove`, the `&&` keeps the file: stop and reconcile with the owner. |
| 8 | the Dropbox `env` is `770`; there is no copy outside the Dropbox root | `stat` only: `0700` on the new directory, `0600` on its files and on the Dropbox `env` | `env SAME`, `README.md SAME` |

- **Line 7's path is this session's worktree.** Any checkout at or after this PR's merge commit carries the checker too.
- **One sink-checklist row is left** (`…INTEGRATED-DESIGN.md` §6, note sink-c): the owner's count of Claude transcripts. Count by value, and never put a value on argv. Purge only within the release's transcript limit (`…RECOVERY-PLAN.md` §6.1 item 5).

### 2. Drives: Tier 2, then Tier 3 (no `sudo`)

**Measured on 2026-10-26.** All three drives are mounted per `/etc/fstab`:

- **Tier 2 sticks.** `EBC5-F0A3` (`/dev/sdj1`, 237 G free) and `DFF3-2782` (`/dev/sdh1`, 66 G free). Each holds a 764 MB `Juniper-8.0.0.python` set from 2026-08-28.
- **Tier 3.** "Blackbox Part 1" at `/run/media/pcalnon/dee46823-4119-4914-ac15-08194ee27d81` (`/dev/sdb1`, 1.6 T free), with an empty `Juniper/Backups/` created on 10-24.
- **Units.** `Linger=yes`. **No `juniper-backup*` user unit is installed yet.**

**Tier 2** (`…RECOVERY-PLAN.md` §6.3 item 8; AC-10 in `…INTEGRATED-DESIGN.md`):

1. Run `bash util/install_juniper_backup_timer.bash --dry-run`, then the same without `--dry-run`. The real run `enable --now`s `juniper-backup.timer` and `juniper-backup.path`.
2. With both sticks mounted, the first run is the OK run: `systemctl --user start --no-block juniper-backup.service`, then `cat ~/.local/state/juniper-backup/last-run.status`.
3. Verify a new archive on **both** sticks. With one stick the run is PARTIAL (rc 4) and reads `FAILED`.
4. Then a run with no stick should read `SKIPPED`. It only does so after the first success.
5. Then the class-1 pipeline drill: `bash util/ad-hoc/2026-08-26_backup_restore_drill.bash`.
6. Then **the owner** decrypts one real archive with the YubiKey (PIN and touch). This is the key class the drill cannot cover.

**Tier 3** (`…INTEGRATED-DESIGN.md` §7.9; D-5):

1. Run `bash util/install_juniper_backup_timer.bash --lane full --dry-run`, then for real.
2. Start the first set with `systemctl --user start --no-block juniper-backup-full.service`. It is large (`juniper-legacy` alone is about 18 G), so poll `cat ~/.local/state/juniper-backup-full/last-run.status`.
3. Verify the `full` set under `Juniper/Backups/`.
4. Run AC-11: restore one archive and diff it against the live tree.

**Who runs the installers.** On 2026-10-10 the session offered to run the Tier 2 install and first run itself on the owner's go: these are user units and need no `sudo`. Get that go explicitly, for each tier. Never hand it to a subagent, whose limits forbid enabling a unit.

### 3. Phase D: `…RECOVERY-PLAN.md` §6.4, in one owner sitting

Run §6.4 as written, with these deltas:

- **Step 0** (the rehearsal on a throwaway data folder) is still owed. It is the first time any binary runs on this host.
- **Step 1 is done** (Line 0). The timer stays disabled until step 13. Step 9's installer then installs a root-owned copy, so the re-enabled timer no longer runs the checkout.
- **Step 3**: re-run the stage gate. Expect `0 staged`.
- **Step 5**: "copy today's snapshot aside" is moot. The snapshot has held the *empty* server's database since 2026-10-09, because ml#2199 re-pointed the script and the root timer ran the primary checkout's copy. The freeze of `/usr/lib/duplicati/data` is the recovery source. Note the freeze directory's date.
- **Step 7, per O-1/O-2.** The probe is `util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py`. It reads the duplicati `.env` on **stdin**, never argv.
  - Its parser takes the active `SETTINGS_ENCRYPTION_KEY=` line as `ENV_ACTIVE_KEY`, which is the 64-character value.
  - It ignores `SETTINGS_ENCRYPTION_KEY_OLD`. That 32-character value has the length of the active key the 2026-09-21 probe already excluded (note 3a in `…RECOVERY-PLAN.md`; this is an inference).
  - After step 6's `mv`, the `.env` is at `/home/duplicati/.config/Duplicati.empty-2026-09-20/.env`. Both it and the freeze are `0700 duplicati`, so the probe runs under `sudo`, against a scratch **copy** of the server DB together with its `-wal`/`-shm`, in a root-only directory. Never run it against the freeze itself.
  - A **match → Procedure A**: at step 9 the accepted key goes to `…-key` and a random one to `…-key.new` (I-38), and step 12's re-key is `util/ad-hoc/2026-10-03_rekey_settings_key.bash`.
  - **No match → A0.**
  - `util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash` is a different tool: a server-based probe that is "confirmation only" (`…INTEGRATED-DESIGN.md` §8 P0 step 3). It starts a Duplicati binary, so only the owner may run it, and the ruling does not need it.
- **A0's two scripts** (`util/ad-hoc/2026-09-22_confirm_a0_premise.bash`, `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash`) default their job DB into the step-5 freeze, which is `0700 duplicati`, and under sudo-rs `HOME=/root`. Run them as `sudo env YAMAGUCHI_ENV_FILE=/home/pcalnon/.config/duplicati-backup/env YAMAGUCHI_JOB_DB=/home/duplicati/.cache/root-data-folder-<date>/BMXWPAOGLP.sqlite YAMAGUCHI_WORKDIR=<a root-only directory> bash <script>`.
- **Step 9**:
  - The installer refuses `/etc/default/duplicati` as **UNBLESSED**. Read the difference, then re-run it with `--update-backup-behavior`.
  - `/etc/duplicati/env` is `0640 root:duplicati` (O-12).
  - Escrow the new key, then `shred -u` the old `.env`, which retires both of its keys.
- **Step 11**:
  - Pin `--aes-version=2` (O-14).
  - **Keep** `additional-report-url` and record its warning as expected (O-13).
  - Remove `retention-policy`; retention stays suspended.
  - The watchdog already checks backup 2: its `--backup-id 2` deploy ran on 2026-10-05 at 19:03 CDT. Its daily 401 is expected until this step.
- **Step 14**: after AC-4's first drill, copy the five dlists aside, then restore `2W:1D,6M:1W,2Y:1M,5Y:2M`.

### 4. A decision-record PR (gates nothing)

Write the rulings table above into `…RECOVERY-PLAN.md` §6.6, with O-13's dissent. Then record these findings:

- the snapshot overwrite;
- the watchdog deploy is done;
- A0's freeze-permission and `HOME` issue;
- the probe ignores `SETTINGS_ENCRYPTION_KEY_OLD`;
- `~/.config/duplicati-backup/env` was rewritten on 2026-09-18 at 20:45 CDT, after the 08-25/26 fingerprints were recorded;
- the gitleaks fleet fix;
- Phase C's progress.

### 5. Owner questions and actions still open

- **O-11**: rotate the TestPyPI token.
- **juniper-recurrence runs no secret scan** in any workflow (10-25 survey). Does the owner want a follow-up PR?
- **juniper-data** has an older commit allowlist that hides a 36-character UUID-shaped value assigned to `ARC_AGI_API`. Its comment calls it a public identifier, and nobody has verified that. Is it a public identifier or a key?

### 6. Later: Phase E (`…RECOVERY-PLAN.md` §6.5)

- **P1**: S-4's in-tree delete on sign-off, and the Dropbox account audit.
- **P2**: D-14's destination permissions, then AC-7, AC-5, AC-12 and AC-9.
- **The rotation** (`…INTEGRATED-DESIGN.md` §10.2), with O-9's second pass.
- **P3's remainder** is §2 above. D-5 is ruled and the owner has written T3's fstab line, which leaves the first `full` set and the AC-10/AC-11 drills.
- **P4**, after seven consecutive successful daily runs.

## Key context and traps

- **A unit that runs a checkout deploys every merge.** The root snapshot timer ran the primary checkout's script, so ml#2199's merge changed what root ran. The Tier 2/3 installers *copy* their scripts into `~/.local/bin`, so re-run an installer to update its lane.
- **A PR can now fail Security Scan.** A squash merge mints a new SHA, so a commit-scoped `.gitleaksignore` entry cannot pre-silence a PR's own finding. Use `gitleaks:allow` on the line, or restructure it. gitleaks 8.24.3 silently ignores a top-level `[[allowlists]]`; use a rule-level `[[rules.allowlists]]` with `condition = "AND"`.
- **Predict the scan locally.** pre-commit's cached `v8.24.3` binary plus `main`'s `.gitleaks.toml`, with `--redact`, per the memory note `reference_ci_parity_gitleaks_local_scan`.
- **`curious-plotting-hummingbird` is DO NOT SWEEP.** Line 7 removes one file in it, never the worktree.
- **The harness refuses some shell forms.** This session's worktree isolation refuses compound shell with variables or loops, `sleep` chains, and `git -C` into the primary checkout. Write a small script in the scratchpad instead.
- **Merge mechanics.**
  - `gh pr checks --json` is not supported by this `gh`; use `--required`.
  - Commit only through `util/open_signed_pr.py` / `util/push_signed_commit.py`.
  - Merge with `util/safe_merge.py`, and read its `MERGED` line.
- **The Tier 1 server must stay up.** It has run since 2026-09-20. Never restart it: Phase D step 6 is the one stop.

## Verify first

```bash
git fetch origin main
git log --oneline -1 origin/main
getent passwd duplicati | cut -d: -f7                                    # /usr/sbin/nologin   (Line 2 done)
systemctl is-enabled yamaguchi-server-db-snapshot.timer                  # disabled            (Line 0 done)
stat -c '%U:%G %n' /usr/lib/duplicati /etc/default/duplicati             # root:root           (Line 1 done)
dpkg-query -W -f='${db:Status-Abbrev}\n' sqlite3                         # "no packages found" until Line 3
stat -c '%a %n' /home/duplicati/.config/Duplicati/Duplicati-server.backup # 777 until Line 6
stat -c '%a %n' ~/Development/python/Juniper/juniper-ml/.claude/worktrees/curious-plotting-hummingbird/.env  # 664 until Line 7
stat -c '%a %n' /mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_keys/env  # 770 until Line 8
findmnt -rn -o TARGET,SOURCE | grep /run/media/pcalnon                  # EBC5-F0A3, DFF3-2782, dee46823-… (and extruder, not a target)
systemctl --user list-unit-files 'juniper-backup*'                       # 0 unit files until the drives step
python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py --check         # 0 staged, 14 already current, 0 skipped
```

**Git state at handoff.** This worktree is `precious-toasting-twilight`, on branch `worktree-precious-toasting-twilight` at `900eb93a`, seven commits behind `origin/main`, none of them backup files. Nothing is staged. The one untracked file, `util/ad-hoc/2026-10-10_s7_env_reconcile.py`, lands on `main` with this handoff's PR.

## Limits (unchanged; every lane brief must carry them)

- never start, stop, restart, enable, disable or reload a unit;
- never run a Duplicati binary, never contact 127.0.0.1:8300, no `sudo`;
- nothing under `/mnt/Backups/Ubuntu/` beyond `stat`;
- never read a secret file;
- never print an environment variable or a token;
- no `git stash`; no interactive shells; no host actions.
