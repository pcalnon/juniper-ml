# HANDOFF 2026-10-29 — backup arc: AC-11 passed, the transcript count read 0; Phase D next, in one sitting

Session "backup-tiers-2-3-running-record-landed-then-phase-d" (`ded2ed6d`, worktree `lively-finding-wand`), continuing `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-28_backup-tiers-2-3-running-record-landed-then-phase-d.md` (juniper-ml#2382). Host `yamaguchi`.

**Tier 1 (Duplicati) is still down**: no backup since 2026-09-18 14:12 UTC. Tier 2 and Tier 3 have run since 2026-10-27. Nothing Phase D waits on is still owed.

Every reference below carries its file. After this table, the long names are shortened:

| Short form | File |
| --- | --- |
| `…RECOVERY-PLAN.md` | `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md` — the phase plan: §6.3.1 is the execution record, §6.4 is Phase D, §6.6 holds the rulings, and §6.7 says when a validation round is owed |
| `…INTEGRATED-DESIGN.md` | `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` — the design of record ("D"); its §8 is the procedure `…RECOVERY-PLAN.md` §6.4 is a checklist against |
| `…ROUND-4-RECORD.md` | `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md` |
| `…10-28…md` | the predecessor handoff named above |
| `…lines-0-8…md` | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-26_backup-phase-c-lines-0-8-done-drives-then-phase-d.md` (juniper-ml#2371) — its Remaining §3 holds most of Phase D's deltas |

The item IDs this file uses each resolve to one file:
- **`…RECOVERY-PLAN.md`**: `O-` (its §6.6), `I-` (§5), `B11` (§6.2), and "Line N" and "finding N" (both §6.3.1).
- **`…INTEGRATED-DESIGN.md`**: `D-`, `AC-` and its §10.2. The design has its own O- series too; this file cites one entry as "D's O-12".
- **`…ROUND-4-RECORD.md`**, round 4, lens B: B14, B15 and U1. Later rounds in that file reuse the numbers.
- "P0 step N" is a step of `…INTEGRATED-DESIGN.md` §8.

## Continue

**Phase D** (`…RECOVERY-PLAN.md` §6.4), interactively with the owner, in one sitting of about two hours. On 2026-10-29 the owner chose to run it in a fresh thread. The owner needs `sudo` and the passphrase from the printed sheet or the password manager, **not** the Dropbox copy.

1. **Run the verify block below.** If any line differs from its comment, stop and show the owner; do not start step 0 until the owner rules. If a tool, path or flag is not where this file, `…RECOVERY-PLAN.md` or `…INTEGRATED-DESIGN.md` says, stop and report it; never substitute one. Where this file departs from D on purpose, this file wins. The departures include:
   - the probe's spec;
   - step 0(b)'s target;
   - the `TMPDIR` added to D's command lines;
   - the freeze date: `…RECOVERY-PLAN.md` §6.4 step 5's `$(date +%F)`, not D's `2026-09-22`.
2. **Read `…RECOVERY-PLAN.md` §6.4 in full**, and `…INTEGRATED-DESIGN.md` §8 wherever a step says "as D says".
3. **Before step 0, design with the owner the two commands no document gives**, and validate both (`…RECOVERY-PLAN.md` §6.7): step 0(b)'s trial, and Procedure A's key write (both in Remaining §1). The key write is needed only on a probe match, but designing it later would stall the sitting between steps 6 and 9.
4. **Then take the owner through steps 0 to 14**, with the deltas in Remaining §1.
5. **Who runs what.** The owner runs every step that changes the host or reaches the server, in the shell Key context's "Two shells" names. The owner pastes the output, never a raw journal from a server start (Key context). The session checks each step read-only and keeps a running record.
6. **Land the record** in `…RECOVERY-PLAN.md` in one signed PR at the end. If the record changes a §6.4 step, run one narrow validation lane on it first (`…RECOVERY-PLAN.md` §6.7).

Merge approval covered this session's PRs only. Ask again.

## Completed, 2026-10-28 and 10-29 (record: `…RECOVERY-PLAN.md` §6.3.1, juniper-ml#2385)

- **`…10-28…md`'s verify block held**, every line (2026-10-28, 21:00 CDT).
- **AC-11 passed** (10-28 21:01–21:02 CDT; the session ran it on the owner's instruction).
  - Tier 3's `backups` archive decrypted with the **3c** key (subkey `57E275E9F67430CE`, card 24955114; `GOODMDC`).
  - It matched the live tree under `diff -rq`: 226 files, 142 directories and 536,520,981 bytes on each side.
  - The restored copy was removed.
- **The transcript count read 0** (the owner, as root, 10-29). `util/ad-hoc/2026-10-28_transcript_secret_count.py` exited 0 over 10,768 files. **Phase D step 9 may now shred the service `.env`.**
  - The zero covers only verbatim and JSON-escaped copies.
  - It covers only `~pcalnon/.claude`, `~pcalnon/.claude.json` and juniper-ml's primary `tmp/`: no worktree's `tmp/` is in its roots.
  - The 08-25 and 09-21 transcripts that `…RECOVERY-PLAN.md` §6.3.1 finding 3 and I-31 name are gone from `~pcalnon/.claude`, as Claude Code's 30-day cleanup predicts (the documented default; `cleanupPeriodDays` is unset). The oldest session transcript was last written 10-02.
- **`…RECOVERY-PLAN.md` §6.3.1 finding 9 is closed.** The counter's grouping shows `SETTINGS_ENCRYPTION_KEY_OLD` holds the backup passphrase, which `…INTEGRATED-DESIGN.md` §5.4's 09-21 probe already excluded. Step 7's probe set is unchanged: the 64-character key is the one `.env` value no probe has tested.
- **Step 3's gate, as a baseline**: `python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py --check` printed `0 staged, 14 already current, 0 skipped` at `9b1f4db7` on 10-29.
- **Owner choices, 10-29**: Phase D in a fresh thread; the 3a-key test skipped.

## Remaining, in order

### 1. Phase D (`…RECOVERY-PLAN.md` §6.4, one owner sitting)

Every delta in `…lines-0-8…md` Remaining §3 and `…10-28…md` Remaining §3 still applies, except where a bullet below or "Corrections to the predecessor" supersedes it. Collected by step:

- **Before step 0**: set up the temporary directories (Key context, "Temp space"). Then, throughout, no reboot until step 10's start has been checked, and on Procedure A until step 12's re-key is done (Key context).
- **Step 0** is still owed: `…RECOVERY-PLAN.md` §6.4 calls it "the first time any of this runs a binary on this host". **Part (b) has no workable command yet.**
  - **Its target** is step 0(a)'s scratch folder and throwaway key (`…RECOVERY-PLAN.md` §6.4 step 0(b)). It is never the freeze, nor a copy of it.
    - Those hold the database under the unidentified 09-18 key and cannot open (B15).
    - Several sites in D still name a freeze or probe copy as the target: its §7.3.2 (its line 837), its O-12, its AC-12 row and note AC-12a. B15 refutes them.
    - `…RECOVERY-PLAN.md` §6.4 step 0 cites AC-12a for "removed and recorded", but that rule is in the AC-12 row.
  - **The scratch folder** goes under `/home/duplicati` (0700 `duplicati`). The unit masks `/root`, and `duplicati` cannot traverse it.
  - **The trial overrides six things**:
    - `ExecStart=`, because `/usr/local/lib/duplicati/` does not exist until step 9;
    - `EnvironmentFile=`, which would load the old `/etc/default/duplicati`;
    - the port, because 8300 is held by pid 1397393;
    - the credential path, because the credential is not written until step 9;
    - the data folder;
    - `SystemCallErrorNumber=`, left unset as `…RECOVERY-PLAN.md` §6.4 step 0(b) requires (the unit sets `EPERM`).

    `Restart=no` is advisable. Without these overrides, a missing file or a bind failure reads as a directive the server cannot run under, which AC-12 would then remove. D's O-12 (`…INTEGRATED-DESIGN.md`, near its line 3313) is this trial's question.
- **Step 1**: done (`…RECOVERY-PLAN.md` §6.3.1 Line 0). The timer stays disabled until step 13.
- **Step 2**: the **owner** takes the AC-8 journal counts (a session never greps a log for values: `…RECOVERY-PLAN.md` §6.0 item 6). If they read 0, skip the `--rotate` and `--vacuum-time=1s` (ruled 10-28).
- **Step 3**: the session may re-run the stage gate (it writes nothing); expect `0 staged`. The gate, the installer and every Phase D tool run from a checkout at `origin/main`.
- **Step 5**: "copy today's snapshot aside" is moot. The snapshot has held the empty server's database since 10-09; the recovery source is the freeze of `/usr/lib/duplicati/data`. Note the freeze directory's date, because A0's `YAMAGUCHI_JOB_DB` names it.
- **Step 6**: after the `mv`, the service `.env` is at `/home/duplicati/.config/Duplicati.empty-2026-09-20/.env`, in a folder step 6 makes `0700`.
- **Step 7** (O-1, O-2):
  - **The probe.** Run `util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py` as `…INTEGRATED-DESIGN.md` §8 P0 step 3 gives it: the wrapper path, the credential file, then a `label=path` spec, with the service `.env` piped on stdin.
    - Pipe that one file, step 6's moved `/home/duplicati/.config/Duplicati.empty-2026-09-20/.env`, and no other.
    - A wrong file, or one with an empty key line, still lists `ENV_ACTIVE_KEY` under `candidates loaded:` and reads "no match".

    Make two changes to D's line:
    - write `~pcalnon/.config/duplicati-backup/env` where it has `~/…`;
    - point the spec at a scratch copy of the freeze's `Duplicati-server.sqlite` in a root-only directory, never at the freeze itself.
  - **Trust "no match" only if all of these hold** for that copy:
    - `candidates loaded:` lists `ENV_ACTIVE_KEY`;
    - there is no `query error` line;
    - `encrypted blobs=` is at least 1, and `content-hash-verified=` equals it.

    The probe prints its counts and `key-hash match:` lines whatever candidates loaded, so those lines alone prove nothing.

    Three mistakes fake a "no match". Each would send the owner to A0 wrongly, after which step 9 shreds the only holder of the 64-character key:
    - a terminal on stdin loads no `.env` candidate;
    - so does an empty pipe, such as a mistyped `cat`;
    - a spec naming `BMXWPAOGLP.sqlite`, the job index in the same folder, finds no blob.
  - **The routing.** A match → Procedure A, with step 12's re-key. No match → A0.
    - `_OLD` needs no probe (`…RECOVERY-PLAN.md` §6.3.1 finding 9).
    - B11's history candidates are not used: O-1/O-2 ruled out a history-candidate search, so §6.4 step 7's "every candidate B11 extracted" does not apply.
  - **Procedure A's key write** (design it before step 0). No document gives a command that writes the matched form of the key into `/etc/credstore/duplicati-settings-key` without printing it, and without putting it on `sudo`'s argv (B14). It must run before step 9 shreds the `.env`, and a wrong form brings back I-38's mismatch loop.

    The wrapper reads the file with `$(<file)`, which drops trailing newlines, refuses edge whitespace and keeps quotes. So:
    - a `noquote` match is written without its quotes;
    - a quoted `raw` match keeps them;
    - a match only on the `newline` variant cannot be delivered through the file at all.
  - **A0's two scripts** need `sudo env YAMAGUCHI_ENV_FILE=… YAMAGUCHI_JOB_DB=… YAMAGUCHI_WORKDIR=… TMPDIR=…`, a work directory on ext4, and a restore directory outside `/home/pcalnon`. `…lines-0-8…md` Remaining §3 has both command lines; add `TMPDIR` to each.
  - **`OVFDREJHJT.sqlite`**: identify it from the scratch copy's `Backup` table, and record what it is (`…RECOVERY-PLAN.md` §6.3.1 finding 4).
- **Step 9**:
  - The transcript count has run.
  - **Running the installer.** Run it with `TMPDIR` passed through `sudo env`, because its `mktemp -d` otherwise lands in `/tmp`.
  - **The three UNBLESSED files.** The installer refuses `/etc/default/duplicati` and the installed `yamaguchi-server-db-snapshot.service` and `.timer` under `/etc/systemd/system`: all three differ from the repository. Read each difference, then re-run with `--update-backup-behavior`.
  - `/etc/duplicati/env` is `0640 root:duplicati` (O-12).
  - Escrow the new key, then `shred -u` the old `.env`.
  - **After printing the escrow sheet**, run `sudo ls -la /var/spool/cups`. `lpr` keeps its own `d…` copy, which lingers a day beside its `c…` file and forever without one (`…RECOVERY-PLAN.md` §6.3.1 finding 11). Shred that copy.
- **Steps 10 and 11**, in the `pcalnon` shell: the web-credential writes and reads, every `util/ad-hoc/yamaguchi_server_api.py` call, the guard dry run, and the watchdog redeploy.
  - Write the credential with `set +o history; umask 077; read -rs v`, then `printf 'DUPLICATI_WEB_CREDENTIAL=%s\n' "$v" > ~/.config/duplicati-backup/web-credential; unset v`. Mind step 11's outer-quote rule.
  - Step 11 pins `--aes-version=2` (O-14), keeps `additional-report-url` and expects its warning (O-13), and removes `retention-policy`. The watchdog's daily 401 ends there.
- **Step 12**, Procedure A only:
  - From the `pcalnon` shell, run `sudo bash util/ad-hoc/2026-10-03_rekey_settings_key.bash`. Its API calls go as `${SUDO_USER:-pcalnon}`. Typed as `sudo bash …` in the root shell, `SUDO_USER` becomes `root` and its pre-flight fails.
  - Its `sudo -u duplicati` VACUUM gets no `TMPDIR` and falls back to `/var/tmp`. Fold that into the Procedure A design.
  - B15 and `…RECOVERY-PLAN.md` §6.4 step 12's U1 apply.
- **Step 14**: after AC-4's first drill, copy the five dlists aside, then restore `2W:1D,6M:1W,2Y:1M,5Y:2M`.
  - **The drills**, in the `pcalnon` shell: `util/ad-hoc/duplicati_drill_fresh.py`'s `--cred-file` defaults to `~`. `util/ad-hoc/duplicati_drill_run.py` passes no `--tempdir`, so settle where its temporary files go before running it.
  - **The history files** are **not** wiped here; they go at the `…INTEGRATED-DESIGN.md` §10.2 rotation (ruled 10-28, against the recommendation).

### 2. After Phase D, and open items

- **Phase E** (`…RECOVERY-PLAN.md` §6.5): P1, then P2, then the `…INTEGRATED-DESIGN.md` §10.2 rotation (with O-9's second pass and the history-file wipe), then P4. P3 is done (`…RECOVERY-PLAN.md` §6.5 item 4).
- **O-11** (rotate the TestPyPI token) is open. I-31 calls the transcript that captured it cloud-linked: it is gone from `~pcalnon/.claude`, not necessarily from wherever else it went. The token stays live until rotated.
- **D-12** is unruled. juniper-recurrence runs no secret scan. juniper-data's `ARC_AGI_API` allowlist entry is unverified.
- **Tier 2's capacity**: D-10 keeps every set, and `DFF3-2782` has 65 GiB free, about 75 weekly sets (`…RECOVERY-PLAN.md` §6.6 note (c)).
- **The `.path` units cannot see fstab mounts** (`…RECOVERY-PLAN.md` §6.3.1 finding 15), so only the timers start a run. That is a design follow-up, if the owner wants a run to start when a drive is plugged in. A physical re-plug is untested.
- **Optional: prove the 3a key on a real archive.**
  - Remove the 3c card (24955114) and insert the 3a card (26881335).
  - Decrypt Tier 3's `backups` archive with `gpg --status-fd 2 --output <a file in the session worktree's tmp/>`. Expect `DECRYPTION_KEY 81E94B831F84B6C1CF08DC1691E9A12F226780E2 25B6B4B192636FDA147AEBAC12B62E52C2F6B4E4`.
  - List it with `tar -tjf <file> | wc -l` (expect 368), then remove the file at once.
- **Optional, after Phase D: `…RECOVERY-PLAN.md` §6.3.1 finding 3's lead.** Tier 1's filesets should still hold the 08-25 transcripts, because the job's filters leave `.claude/projects` in (`…INTEGRATED-DESIGN.md` note AC-3a; an inference). A count-and-timestamp search there gates nothing.

## Key context and traps

- **No reboot until step 10's start has been checked, and on Procedure A until step 12's re-key is done.** `duplicati.service` is `enabled` throughout; step 6 only stops it.
  - **Before step 9**, a reboot stops the running server (pid 1397393) and leaves a unit that cannot start. The installed `/usr/lib/systemd/system/duplicati.service` runs `/home/duplicati/bin/duplicati-wrapper.bash`, which Line 1 removed, under `Restart=always`.
  - **From step 9's install**, the boot link starts the new unit unwatched, before step 10's checks.
  - **During step 12's re-key**, a runtime drop-in sits under `/run`, and a reboot removes it. A reboot mid-re-key therefore re-encrypts under whatever key sits at the credential path.
  - If mounts are lost, the owner runs, as root, `systemctl start snapd.mounts.target` plus the unit-file mounts (`…RECOVERY-PLAN.md` §6.3.1 finding 17).
- **The Tier 1 server stays up** (pid 1397393, since 2026-09-20) until step 6, its one stop. Steps 10 and 11 stop and start the new unit.
- **Two shells.** In the owner's root shell `~` is `/root`.
  - **The `pcalnon` shell** is for anything that resolves `~` or calls the server API: the web credential (steps 10 and 11), `yamaguchi_server_api.py` (`expanduser`), the guard dry run, the watchdog deploy (`systemctl --user`), the re-key script (`SUDO_USER`), and the drills.
  - **A step that needs both root and the server API** runs as `sudo …` from the `pcalnon` shell.
  - **In the root shell**, write `~pcalnon` explicitly.
  - **In either shell**, never put a secret on a command line or on `sudo`'s argv.
    - Read it with `read -rs`, which keeps it out of history.
    - Pass it through a file or stdin. `sudo` logs its argv as `COMMAND=` in the journal and `/var/log/auth.log` (B14).
    - Phase D's tools read values from stdin or files, never from argv.
- **Temp space.** No Phase D file goes under `/tmp` or `/var/tmp` (the 2026-10-26 directive; `…INTEGRATED-DESIGN.md`'s "Never stage volumes on tmpfs"). No file that may hold cleartext goes under `/home/pcalnon`, the backup Source.
  - **For root's tools**: `install -d -m 0700 /root/phase-d-tmp`, then pass `TMPDIR=/root/phase-d-tmp` inside every root `sudo env …`. `sudo` resets the environment, so an exported `TMPDIR` is lost.

    Those tools are the A0 scripts, which pass no `--tempdir`, and the installer (`mktemp -d`). The stage gate runs as `pcalnon` at step 3. It removes its own extraction only when it succeeds; after a refusal, check the extraction it leaves and remove it.
  - **For anything run as `duplicati`**: a `0700 duplicati` directory under `/home/duplicati`. That covers step 0's scratch folder.
  - **At the end**, shred the files in both directories and remove them. They may hold the probe copy, A0's cleartext restore and step 13's copy.
- **Journals.** A server start logs a sign-in URL whenever its password is autogenerated, whatever the token flag says (`…ROUND-4-RECORD.md`, near its line 728; `…RECOVERY-PLAN.md` §5's carried items).
  - On the planned path, no start should log one: step 0(a) sets the trial's password, and A0 and A keep the root-era one. The count guards against a step going off-plan.
  - From step 0(b)'s trial on, the owner checks each start's journal with `grep -c` and pastes only the counts. For step 10 those strings are `Server has started` and `Unknown option supplied`.
  - §6.4 step 10 names no string for "no encryption warning", so settle with the owner how to check that one.
  - At step 12, count before anything else (U1).
- **Plugging in a drive starts nothing** while its fstab line exists (a physical re-plug is untested). The timers start runs, and only while the drive is mounted. Each window carries up to 15 minutes' random delay.
  - **Tier 2**, Sundays at 03:00: 11-01 skips; 11-08 is due. Detached, it reads `SKIPPED` until its last success is more than 21 days old, then `FAILED`, first at the 11-22 window.
  - **Tier 3**, the 1st at 04:00: 11-01 skips; 12-01 is due. Detached, it reads `SKIPPED` until more than 45 days, then `FAILED`, first at the 01-01 window.
- **To eject a backup drive**, use the desktop's Eject or `udisksctl unmount`, never `umount -a`.
- **The runner's own verify reads the page cache.** For a media-level check, use `util/ad-hoc/2026-10-27_backup_set_media_readback.py --uuid <set> [--expect N] DIR...` (`O_DIRECT`; exit 0, 1 or 2).
- **The harness refuses some shell forms.** Spell paths out and split commands. Refused:
  - a pipe into `tar -xjf -` (decrypt with `gpg --output <file>`, then `tar -xjf <file>`);
  - a pipe into an interpreter;
  - `cd <primary> && git …` or `git -C <primary>` (compare files with `cmp` instead);
  - compound shell with variables;
  - a computed value where an option may stand;
  - words like `trap` or `COMPLETE` inside a `grep` pattern;
  - `case` blocks that run `bash`;
  - `sed` with a computed program.
- **Write and Edit cannot reach the primary checkout's `tmp/`**, and a worktree session's scratchpad may sit there. Write into the worktree's own `tmp/`, which `.git/info/exclude` ignores.
- **The primary checkout can lag `main`.** On 10-28 it lacked that day's tools; another session pulled it to `c5350c98` on 10-29 at 15:48. Before the owner runs a tool from it, check that it is at `origin/main`.
- **`pinentry` is `pinentry-gnome3`**, so a decrypt the session runs prompts on the owner's desktop. It does not prompt if the card still holds a PIN entry, as on 10-28.
- **G5** refuses a `/home/pcalnon` literal in a script: write `~pcalnon` in examples, and `Path.home()` or `$HOME` in code.
- **`findmnt` given two paths** reads them as a source and a target; use `--mountpoint`.
- **Merging**:
  - `util/open_signed_pr.py` uploads whole files, so check the base blob first. Commit and PR bodies go in files, because a shell line eats backticks.
  - Then `util/wait_for_checks.py`, and `util/safe_merge.py --execute` (read its `MERGED` line).
  - pre-commit skips gitleaks for `prompts/`, so scan a handoff with CI's gitleaks v8.24.3 and `main`'s config.
- **Unchanged**: `curious-plotting-hummingbird` is DO NOT SWEEP; `grep` is `ugrep`; `cp -a` without gid 139 drops group `duplicati`.

## Corrections to the predecessor

- `…lines-0-8…md` Remaining §3 (step 7) calls `_OLD`'s exclusion "an inference". It is now a measurement (Completed above).
- `…10-28…md` says "**Never reboot** before step 6", and `…RECOVERY-PLAN.md` §6.3.1 finding 17 says "No reboot before §6.4". The window actually runs to step 10's start, and on Procedure A through step 12 (Key context). This file's PR widens finding 17 to match, and the memory hub says the same.

## Verify first

```bash
git fetch origin main && git log --oneline -1 origin/main
git log --oneline -1 origin/main -- prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-29_backup-ac11-passed-transcript-count-zero-then-phase-d.md   # the PR that landed this file
ps -o pid=,lstart= -u duplicati                                     # 1397393 Sun Sep 20 18:19:42 2026
systemctl is-enabled duplicati.service                              # enabled -- so no reboot
systemctl is-enabled yamaguchi-server-db-snapshot.timer             # disabled
systemctl --user list-timers 'juniper-backup*' --no-pager           # both timers listed
cat ~/.local/state/juniper-backup/last-run.status ~/.local/state/juniper-backup-full/last-run.status   # SKIPPED or OK; never FAILED
systemctl --user list-units --state=failed --no-legend 'juniper-backup*'                              # nothing
systemctl list-units --all --type=mount --no-legend --plain --state=inactive 'snap-*.mount' | wc -l    # 0
python3 util/ad-hoc/2026-09-22_stage_design_artifacts.py --check | tail -1                            # 0 staged, 14 already current, 0 skipped
ls -d /home/pcalnon/Development/python/Juniper/juniper-ml/tmp/ac11-restore-2026-10-28* 2>&1           # absent: removed 10-28
```

**Git state at handoff.** Worktree `lively-finding-wand`, branch `worktree-lively-finding-wand`, at `9b1f4db7`. It is behind `origin/main` by #2384 and #2385, and neither touches a Phase D tool. The worktree's changes are this file and `…RECOVERY-PLAN.md` (finding 17 widened, and the transcript count's coverage made exact). Both go to `main` through this file's signed PR.

**Files this session left in `tmp/`.** None is needed once this file's PR merges. The `tmp/` retention ruling then allows deleting them, and `git worktree remove` would delete the worktree's set.
- **In the worktree's `tmp/`**:
  - the two PRs' commit and PR bodies, both published on GitHub;
  - `main-gitleaks.toml` and `gitleaks-scan-final/`, the copies for the CI-parity scan;
  - `handoff-fix-markers.*`, the regression check, and `precommit-handoff-pr.log`.
- **In the primary's `tmp/claude-1000/`**:
  - this session's scratchpad (`…-juniper-ml/ded2ed6d-…/scratchpad/`): a pre-commit log, and two lanes' stage-gate extractions (`stage-check-validator/` and `stage-extract/`), which hold no secrets;
  - its task output (`…-juniper-ml--claude-worktrees-lively-finding-wand/ded2ed6d-…/tasks/`).

**Host changes this session**:
- AC-11's restore copy and decrypted tarball, created and then removed under juniper-ml's `tmp/`;
- the memory hub `project_backup_arc_hub.md` (a 10-29 paragraph) and its `MEMORY.md` line.

## Limits (unchanged; every lane brief must carry them)

- never start, stop, restart, enable, disable or reload a unit;
- never run a Duplicati binary, never contact 127.0.0.1:8300, no `sudo`;
- nothing under `/mnt/Backups/Ubuntu/` beyond `stat`;
- never read a secret file;
- never print an environment variable or a token;
- no `git stash`; no interactive shells; no host actions.

These bind the session and its lanes.
- **The owner may direct a named action in person**, as with AC-11 on 10-28, a gpg decrypt and a diff. That releases that action only.
- **It never releases one of `…RECOVERY-PLAN.md` §6.0 item 6's absolutes**: no session runs a Duplicati binary, reads a secret file, or greps a log for values.
- **Phase D's `sudo` steps, its server calls and its credential writes are the owner's.**
