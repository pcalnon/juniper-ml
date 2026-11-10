# HANDOFF 2026-10-28 — backup arc: Tiers 2 and 3 running, the decision record landed; AC-11, the transcript count, then Phase D

Session "backup-phase-c-lines-0-8-done-drives-then-phase-d" (`9afd298c`, worktree `humble-hatching-dawn`), continuing `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_backup-phase-c-lines-0-8-done-drives-then-phase-d.md` (juniper-ml#2371). Host `yamaguchi`.

**Tier 1 (Duplicati) is still down**: no backup since 2026-09-18 14:12 UTC. Tier 2 and Tier 3 are back as of 2026-10-27.

Every reference below carries its file. After this table, the long names are shortened:

| Short form | File |
| --- | --- |
| `…RECOVERY-PLAN.md` | `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` — the phase plan: §6.3.1 (new) is this session's record, §6.4 is Phase D, §6.6 holds the rulings |
| `…INTEGRATED-DESIGN.md` | `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` — the design of record ("D") |
| `…lines-0-8…md` | the predecessor handoff named above |

## Continue

Interactively with the owner, in this order:

1. **AC-11** (owner, YubiKey): restore Tier 3's `backups` archive and diff it against the live tree (Remaining §1), then remove the restored copy and record the result in `…RECOVERY-PLAN.md` §6.3.1.
2. **The transcript count** (owner, root): `util/ad-hoc/2026-10-28_transcript_secret_count.py`, **before Phase D step 9** (Remaining §2; owner ruling 2026-10-28).
3. **Phase D** (`…RECOVERY-PLAN.md` §6.4) in one owner sitting, with the deltas in Remaining §3. The owner needs `sudo` and the passphrase from the printed sheet or the password manager, **not** the Dropbox copy.

Merge approval covered this session's PRs only. Ask again.

## Completed, 2026-10-27 and 10-28 (full record: `…RECOVERY-PLAN.md` §6.3.1)

- **`…lines-0-8…md`'s verify block** held, with two moves: the journal's first entry keeps advancing (10-18 12:42:13 CDT, measured 10-27), and the CUPS spool changed overnight. It holds no `c…` or `d…` file, and its `tmp/` holds only an empty `cups-dbus-notifier-lockfile` (00:18:15, the second `logrotate.service` failed). The CUPS row closes.
- **Tier 2 accepted (AC-10).** Installed 17:24 CDT. The OK run 17:25:58–17:38:43 wrote set `801a3ef5-57b8-48ec-9d07-767193ce97da`: 10 archives, 918,941,308 B per stick. The new `util/ad-hoc/2026-10-27_backup_set_media_readback.py` read both sticks back with `O_DIRECT`: identical. The no-stick run read `SKIPPED`, the class-1 drill passed 7/7, and the owner's YubiKey decrypt gave `pipe: 0 0 0` (which key did it was not recorded).
- **Tier 3's first set.** Installed 20:32; started by hand at 20:32:13, `OK` at 21:24:46. Set `ce92857f-852d-468e-9688-125ff7753226`: 15 archives, 14,905,974,648 B on Blackbox, read back complete. AC-11 is owed.
- **The decision record** in `…RECOVERY-PLAN.md`: §6.3.1 (new), §6.6's rulings sub-table, a §1 status line and a §9 row, landing with this file and the two tools in one PR. No step of §6.4 changed.
- juniper-ml#2376 (another session) fixed `main`'s red Guard 3b tests (the runners' tmpfs temp dir); merged 2026-10-28 01:21Z.

## Owner rulings, 2026-10-28 (written into `…RECOVERY-PLAN.md` §6.6)

- Build the transcript counter now (done); the owner runs it before Phase D step 9.
- Wipe root's and duplicati's history files at the §10.2 rotation, **against** the recommendation (Phase D step 14).
- Skip Phase D step 2's `--rotate` and `--vacuum-time=1s` when its AC-8 counts read 0.
- Keep each repository's `tmp/` in both tiers' archives (final).
- Still unruled: D-12.

## Remaining, in order

### 1. AC-11 (owner, normal shell, YubiKey plugged in)

First confirm the tree has not moved since the set began: `find /home/pcalnon/Development/python/Juniper/backups -newermt '2026-10-27 20:32:13' | wc -l` should print 0 (it did on 10-28 05:08). Then:

```bash
mkdir /home/pcalnon/Development/python/Juniper/juniper-ml/tmp/ac11-restore-2026-10-28
gpg --decrypt /run/media/pcalnon/dee46823-4119-4914-ac15-08194ee27d81/Juniper/Backups/Juniper_full_backups_ce92857f-852d-468e-9688-125ff7753226_20261027_203213.660287620-CDT.tbz2.gpg | tar -xjf - -C /home/pcalnon/Development/python/Juniper/juniper-ml/tmp/ac11-restore-2026-10-28; echo "pipe: ${PIPESTATUS[*]}"
diff -r /home/pcalnon/Development/python/Juniper/juniper-ml/tmp/ac11-restore-2026-10-28/backups /home/pcalnon/Development/python/Juniper/backups && echo IDENTICAL
```

Expect `pipe: 0 0` and `IDENTICAL`. The restored copy is plaintext inside a tree Tier 2 archives: `rm -r` that directory once the result is recorded (the tmp/ retention ruling; it is then no longer needed).

### 2. The transcript count (owner, root shell, before Phase D step 9)

From a checkout at or after this file's merge commit:

```bash
python3 util/ad-hoc/2026-10-28_transcript_secret_count.py --home ~pcalnon --env-file ~duplicati/.config/Duplicati/.env --env-file ~pcalnon/.config/duplicati-backup/env
```

- Exit 0: no value found. Exit 1: found (per-file lines, counts only). Exit 2: refused.
- It searches `~pcalnon/.claude` (the transcripts and `tool-results/`), `~pcalnon/.claude.json` and juniper-ml's `tmp/` alone. It never prints a value. It was tested on synthetic values only; no session has run it on the real files, and none may.
- After Phase D step 6's `mv`, the service `.env` is at `~duplicati/.config/Duplicati.empty-2026-09-20/.env`.
- A purge of any hit is a separate step, only within the release's transcript limit (`…RECOVERY-PLAN.md` §6.1 item 5). Never purge a validation report.

### 3. Phase D (`…RECOVERY-PLAN.md` §6.4, one owner sitting)

Every delta in `…lines-0-8…md` Remaining §3 still applies: steps 0, 1, 3, 5, 7, A0's `sudo env` variables, 9, 11 and 14, and its "New" items. Four changes:

- **Step 2**: take the AC-8 counts; if they read 0, skip the `--rotate` and `--vacuum-time=1s` (ruled).
- **The history files** are wiped at the §10.2 rotation, not at step 14 (ruled).
- **Never reboot** before step 6. `duplicati.service` is `enabled`, so a reboot restarts Tier 1. If mounts are lost, run `systemctl start snapd.mounts.target` plus the unit-file mounts (`…RECOVERY-PLAN.md` §6.3.1 finding 17).
- **The transcript count** must have run before step 9.

### 4. Later (Phase E, `…RECOVERY-PLAN.md` §6.5) and open items

- Tier 2's capacity: D-10 keeps everything, and `DFF3-2782` has 65 GiB free, about 75 weekly sets (`…RECOVERY-PLAN.md` §6.6 note (c)).
- The `.path` units cannot see fstab mounts (finding 15), so only the timers trigger. A design follow-up, if the owner wants plug-in runs.
- O-11 (the TestPyPI rotation); D-12; juniper-recurrence runs no secret scan; juniper-data's `ARC_AGI_API` allowlist entry is unverified.
- Optional: decrypt a real archive with the *other* YubiKey, so both recipients are proven.

## Key context and traps

- **Plugging in a drive starts nothing.** The sticks and Blackbox now remount through the owner's fstab lines (2026-10-24), whose mount points persist, and `PathChanged=/run/media/pcalnon` sees only an entry created or removed. The timers trigger instead: Tier 2 Sundays 03:00 (the 11-01 window skips; the next run is due from 11-03), Tier 3 the 1st at 04:00 (due 30 days after 10-27).
- **To eject a backup drive**, use the desktop's Eject or `udisksctl unmount`, never `umount -a`. On 10-27 at 17:55:25 a root `umount -a`-like event took down 299 snap mounts and the kernel pseudo-filesystems; it was repaired without a reboot.
- **The runner's own verify reads the page cache.** For a media-level check, use `util/ad-hoc/2026-10-27_backup_set_media_readback.py --uuid <set> [--expect N] DIR...` (`O_DIRECT`; exit 0, 1 or 2).
- **The harness refuses some shell forms**: a computed value where an option may stand; words like `trap` or `COMPLETE` inside a `grep` pattern; `case` blocks that run `bash`; `sed` with a computed program. Spell paths out and split commands.
- **`findmnt` given two paths** reads them as a source and a target, and prints nothing. Use `--mountpoint`.
- **G5** refuses a `/home/pcalnon` literal in a script: write `~pcalnon` in examples, `Path.home()` or `$HOME` in code.
- **Merging**: `util/open_signed_pr.py` uploads whole files, so check the base blob first; then `util/wait_for_checks.py`, and `util/safe_merge.py --execute` (read its `MERGED` line).
- **Unchanged from `…lines-0-8…md`**: the Tier 1 server stays up (pid 1397393); `curious-plotting-hummingbird` is DO NOT SWEEP; `grep` is `ugrep`; `cp -a` without gid 139 drops group `duplicati`.

## Verify first

```bash
git fetch origin main && git log --oneline -1 origin/main
git log --oneline -1 origin/main -- prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-28_backup-tiers-2-3-running-record-landed-then-phase-d.md   # the PR that landed this file
ps -o pid=,lstart= -u duplicati                                     # 1397393 Sun Sep 20 18:19:42 2026
systemctl is-enabled duplicati.service                              # enabled -- so no reboot
systemctl is-enabled yamaguchi-server-db-snapshot.timer             # disabled
systemctl --user list-timers 'juniper-backup*' --no-pager           # both timers listed
cat ~/.local/state/juniper-backup/last-run.status ~/.local/state/juniper-backup-full/last-run.status   # SKIPPED or OK; never FAILED
systemctl --user list-units --state=failed --no-legend 'juniper-backup*'                              # nothing
systemctl list-units --all --type=mount --no-legend --plain --state=inactive 'snap-*.mount' | wc -l    # 0
ls util/ad-hoc/2026-10-27_backup_set_media_readback.py util/ad-hoc/2026-10-28_transcript_secret_count.py
ls /home/pcalnon/Development/python/Juniper/juniper-ml/tmp/ac11-restore-2026-10-28 2>&1             # absent until AC-11 runs
```

**Git state at handoff.** Worktree `humble-hatching-dawn`, branch `worktree-humble-hatching-dawn`, at `05b716b5`. That is behind `origin/main` by commits that touch no backup file. This file, `…RECOVERY-PLAN.md` and the two tools are staged there and land on `main` in one signed PR (branch `docs/backup-tiers-2-3-record-2026-10-28`). Nothing else in the repository changed.

Host changes this session:
- the Tier 2 and Tier 3 user units in `~/.config/systemd/user/juniper-backup*`;
- the two scripts in `~/.local/bin/juniper-backup*.bash`, and the reporter, now 1.1.0;
- the state directories `~/.local/state/juniper-backup{,-full}/`;
- the two sets on the drives;
- the memory hub `project_backup_arc_hub.md` and its `MEMORY.md` line.

## Limits (unchanged; every lane brief must carry them)

- never start, stop, restart, enable, disable or reload a unit;
- never run a Duplicati binary, never contact 127.0.0.1:8300, no `sudo`;
- nothing under `/mnt/Backups/Ubuntu/` beyond `stat`;
- never read a secret file;
- never print an environment variable or a token;
- no `git stash`; no interactive shells; no host actions.
