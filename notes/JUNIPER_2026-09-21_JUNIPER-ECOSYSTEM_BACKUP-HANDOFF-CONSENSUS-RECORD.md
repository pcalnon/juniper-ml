# Backup design handoff — consensus validation record (verbatim reports)

**Project**: Juniper (workstation backup infrastructure, host `yamaguchi`)
**Author**: Paul Calnon
**Date**: 2026-09-21
**Status**: RECORD — validation of the handoff prompt: round 1 (three lanes), round 2 (one lane), round 3 (one lane)
**Subject**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-21_backup-redesign-round-1-validated-reconciliation-pending.md`
**Procedure**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`
**Companion**: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md` (the six reports the handoff dispositions)

## Why this file exists

The owner asked for the handoff to be validated by consensus before it was archived and merged. Three
independent agents reviewed the handoff's first draft (Lane A re-derived every concrete claim against the
repository and the host; two Lane B lenses attacked completeness/fidelity and actionability); their
corrections were folded in, a fourth agent checked the corrected text (round 2), and a fifth checked round 2's
fixes (round 3). Round 3's five leftovers were applied and re-measured by the orchestrator; no fourth round was run. The handoff's own §6
summarises what was caught. The reports are archived here verbatim — each under
`<!-- markdownlint-disable -->` because it is external text — with trailing whitespace stripped by the
repository's pre-commit hook and nothing else changed. **No secret value appears in any report**; the file
was scanned for secret-shaped content before being committed.

Round-1 reports were delivered between 14:40 and 14:52 CDT against the handoff's first draft (mtime 14:26);
line numbers they cite refer to that draft.

---

## Report H-A — Lane A — measurement re-creation of every concrete claim in the handoff; entry point: the repository worktree and the live host (read-only)

Subagent id `a328494a4b82552da` (19,078 characters).

<!-- markdownlint-disable -->

All measurements are complete; nothing further depends on another result. Final report follows.

# Lane A validation — `HANDOFF_2026-09-21_backup-redesign-round-1-validated-reconciliation-pending.md`

Entry point: worktree `atomic-sauteeing-truffle` (HEAD `3ee84ebb`) + live host as `pcalnon` (no gid 139 in-process, `adm` for the journal). Read-only; scratch under `…/scratchpad/hvalA/` (`host_probe.py`, `journal_counts{,2}.py`, `db_probe{,2,3}.py`, `misc_probe.py`, DB **copies** opened `mode=ro`). No secret value read or printed; `git fetch` deliberately not run (state change).

## 1. Claim table

| Handoff location (short quote) | Measured value / evidence | Verdict |
| --- | --- | --- |
| Header: design, CON procedure, 2 record files, 6 `2026-09-21_*.py` instruments, `HANDOFF_2026-09-07…` (same dir) | `ls`: all present; the 6 named instruments are exactly the ones absent from `origin/main` (`git ls-tree`); superseded draft `…root-cause-found…` absent, `git log --all --` empty | AGREE |
| Header/§3: status line `reconciliation PENDING`; STOP warning atop §8; §11 names the three dissents; §12 rows; §0 names `wrap_long_markdown_lines.py`; Appendix C items 1–8 | design L6 status; L989 `> **STOP …**`; L1141–1143 (specifier count / exclude-vs-delete / 42 aliases); §12 = 3 rows; L34 wrap script; C.1–C.8 present | AGREE |
| "Lane A2's 15 and A3's 12 corrections applied"; record table A1 13 DISAGREE / 8 facts / 7 UNTRACEABLE, B1 17, B2 10+22, B3 20 | record L19–24; counted: A2 items 1–15, A3 1–12, A1 §2 1–13, B1 findings 1–17, B2 amputations 1–10 / defects 1–22, B3 F-1…F-20 | AGREE |
| §3: `grep -c '^## Report '` → 6 and 5; lane labels A1/A2/A3 (host / repo+docs / product+code), B1/B2/B3 (root cause+recovery / amputation+actionability / security) | 6 (L41,199,327,506,599,711) and 5 (1a,1b,2a,2b,2c); headings match | AGREE |
| §3 snippet linter `blocks: 12  failures: 0` | run into scratch workdir → `blocks: 12  failures: 0`; 12 `# file:` tags | AGREE |
| §3/§0: `ActiveState=active MainPID=1397393 ExecMainStartTimestamp=Sun 2026-09-20 18:19:42 CDT User=duplicati NeedDaemonReload=no`; only :8300 | `systemctl show` literal; `ss -tln` → `127.0.0.1:8300`, `[::1]:8300`, no 8200 | AGREE |
| §0 loaded `ExecStart … '--daemon-opts="${DAEMON_OPTS}"'`; running argv one word with trailing space; uid 133/gid 139 | `ExecStart={… argv[]=… --daemon-opts="${DAEMON_OPTS}"}`; `/proc/1397393/cmdline` argc=2, `[1]='--webservice-port=8300 '`; `id duplicati` 133/139; reload lines 09-21 03:23:44 | AGREE |
| §0 data folder 0777, 0 backups, schema 12; last journal lines 09-20 18:47/18:51 `temp_backups … denied` | dir `drwxrwxrwx`; copy of the 0777 DB: `Version 12`, `Backup` 0 rows, 4 `Failed to import backup`; stamps 18:47:44 ×2, 18:51:33 ×2; no 09-21 unit lines | AGREE |
| §0 Tier 1 DOWN since 09-18 14:12Z; `20260918T140000Z`; 877 files / 202.8 GiB; `ls -t \| head -1` | census 877 files, 217,760,949,689 B = 202.8 GiB; newest `duplicati-20260918T140000Z.dlist.zip.aes` mtime 09:12:00 CDT; snapshot `LastBackupFinished=20260918T141256Z` | AGREE |
| §0 snapshot 240 KiB, schema 11, `Yamaguchi` id 2, 2 sources, 45 filters, 14:00Z, `DBPath=/usr/lib/duplicati/data/BMXWPAOGLP.sqlite`; replaced daily 13:45 UTC / 08:45 CDT | copy: 245,760 B, `Version 11`, `(2,'Yamaguchi',…BMXWPAOGLP.sqlite)`, Source 2, Filter 45, `Time=1789740000` = 2026-09-18T14:00:00Z; `OnCalendar=*-*-* 13:45:00 UTC`; file mtime 08:45:00 today | AGREE |
| §0 "its four `enc-v1:` fields … content hashes verified 4/4 and 6/6, one key hash each" | probe selection reproduced: snapshot 4/4, `.backup` 6/6, 1 key hash; but ALL enc-v1 fields: snapshot **9** (+`client-license-key`, `remote-control-*`, `server-ssl-*`), `.backup` **11**, one key hash each; snapshot key hash ≠ live-DB key hash ≠ `.backup` key hash | DISAGREE (count), key exclusion AGREE |
| §0 `/usr/lib/duplicati/data/` "abandoned 0700 root folder", mtime 21:03:34 | `drwx------ duplicati:duplicati`, mtime 09-18 21:03:34.67, ctime 09-19 19:15:00, birth 08-25 02:38:43 — owned `duplicati`, not root | AGREE (nuance) |
| §0 watchdog user timer 12:00; UNREACHABLE 09-19/09-20; 401 09-21 02:52 and 12:00 | `list-timers --user`; log tail: 09-19/09-20 12:00:39 UNREACHABLE, 09-21 02:52:01 and 12:00:39 `(401)` | AGREE |
| §0 "A0 … root DB unencrypted until 09-18 20:42"; B1 findings 1/2/3/4/5/7/11 as cited | `No database encryption key` at 09-17 01:31:01, 09-18 20:22:12, 20:42:38; `Server has started` 21:03:30; first `Mismatch` 21:08:06; B1 numbering matches | AGREE |
| §1.1 F1: 15 `Mismatch` restarts 21:08:06–21:11:43 before first specifier error 21:15:40 | 30 Mismatch lines (2/restart) 21:08:06…21:11:43; first `Invalid slot` 21:15:40 | AGREE |
| F6: `port 8200` proves the option word unusable; root folder last opened 09-19 19:15:01; no root-folder start after 21:03:30 | `port 8200` at 09-19 21:20:41, 21:57:41, 09-20 13:32:50; last root-folder `KeyMissing` 19:15:01; last 09-18 `Server has started` 21:03:30 | AGREE |
| F8: rsyslog active; day files to 09-12; `syslog:adm` 0640; pcalnon in adm; 264/60/12/12 day, 220/50/10/10 window | `is-active` active; `syslog-20260912.gz…` all `-rw-r----- syslog adm`; `id -nG` has adm; journal 09-20: `LINE: "` 264, `# export X=` 60, `Exporting` 12, `Settings Encryption Key:` 12; 16:41–16:44: 220/50/10/10 | AGREE |
| F10 escrow `-rwxrwx--- pcalnon:duplicati` | `/mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_keys/env` `-rwxrwx---+` 388 B; `dropbox filestatus` → up to date | AGREE |
| F11: ctimes three files 18:25:47 / dir 18:33:45; "may refuse"; §4.3.9 "or not at all"; add env var to §5.5/§7.3.2 | `.backup`/`.sqlite`/crashlog ctime 18:25:47.326, dir 18:33:45.057; L283 "may refuse"; L208 "or not at all"; §5.5 L282 **already lists** `DUPLICATI__ALLOW_INSECURE_DATAFOLDER`; §7.3.2 L357 does not | DISAGREE (half stale) |
| F15: three copy waves; "§4.1 unit row's `NeedDaemonReload` sentence is wrong" | births `backups/` 09-19 18:40:36, crashlog/`control_dir_v2` 18:42:18, `machineid` 18:42:22; stub 09-19 21:57:36; `installation.txt` 09-20 04:15:42, `.backup` 04:41:07, `-shm` 04:43:02 ✓; §4.1 unit row now reads "A systemd reload at 03:23:44 armed the edited ExecStart…"; `grep -c 'differs from the loaded'` = 0 | DISAGREE (second half stale) |
| F16 preamble vs P1 step 4 | L1001 "Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved"; P1.4 "Move `_yamaguchi_keys/` out" | AGREE |
| A1: 12 passes; 24 failed starts (5/5/14); §5.3 lacks 09-19 21:43–21:55 | `Exporting` 12 (5+5+1+1); 09-19 20:48–21:56 `Main process exited` 24: `is 11` 5 (20:48:12–16), `denied` 5 (21:41:04–08), `is 12` 14 distinct (21:43:07–21:55:42); §5.3 names only 09-19 20:48 and 09-20 18:02/18:12 | AGREE |
| A1: "23 = 22 + 1 (✔ 09-18 → 09-21 13:00), only 4 on 09-18 and 18 on 09-19; survived until 09-19 18:07:32" | system journal that window: `Invalid slot` 23 = 22 + 1; per day **09-18: 5** (4 specifiers 21:15:40/21:16:10/21:17:54/21:29:51 + unit-specifiers 21:23:25), 09-19: 18; last 18:07:32 | DISAGREE (precision) |
| A1: Repair failures 02:17:50/02:18:37/02:19:24, Verify 02:19:46, not 02:19:19 | `.backup` ErrorLog (copy): Repair failures 02:05:17, 02:13:57, 02:14:42, 02:15:31, 02:16:17, 02:17:03, 02:17:50, 02:18:37, 02:19:24; Verify 02:13:07 and 02:19:46; nothing at 02:19:19; design L262 still says 02:19:19 | DISAGREE (incomplete) |
| A1: only 4 DB files + crashlog 0777; `.env` 0660; `installation.txt`/`machineid.txt` 0664; subdirs 0775; `temp/` root 0755 | `ls -la` of the 0777 dir: exactly so | AGREE |
| A1: only directories chowned; 1,443 regular files root:root; primary checkout `main` `d721fc78`; 13:32:34 five `wrapper.bash` `KeyMissing` 16 s before success; A.1 20:48:12 identifier `wrapper.bash` | walk: 1443 regular, 0 non-root; 96 duplicati dirs; `.git/HEAD`→main, `refs/heads/main`=`d721fc78`, `git worktree list` primary `d721fc78 [main]`; `KeyMissing` ×10 lines 13:32:34–38 under `wrapper.bash`, `Server has started` 13:32:50 under `duplicati-wrapper.bash`; 09-19 20:48:12 identifier `wrapper.bash` | AGREE |
| A1 facts: chgrp dirs 20:36:53/20:37:41, 874 volumes 09-19 17:37; `lost+found` 2023-05-16; `/home/duplicati` 09-18 19:31:40; `installation.txt` 18:10:32; envs 62 G (§3.4 says 47 GB); live `vim`; two `su - duplicati` | `/mnt/Backups` ctime 20:36:53, `Ubuntu` 20:37:41; ctime histogram 874 @ 17:37 (+2 @18:09, 1 @18:21); `lost+found` mtime 2023-05-16; birth 19:31:40.23; mtime 18:10:32.97; `du -sh` 62G, L133/L975 "47 GB"; `vim /usr/lib/systemd/system/duplicati.service` pid 2318515 (root, since 01:41:41) + `.duplicati.service.swp`; `su - duplicati` pids 3065637 (18:24:50), 3117156 (18:52:00) | AGREE |
| A1/B2 A10: `.dropbox-dist` 270.4.3312 "owned `duplicati:duplicati` since 09-14 20:49 (✔)" | `VERSION` 270.4.3312; `drwxrwxr-x duplicati:duplicati`; **birth 09-15 15:26:22, mtime 09-14 20:49:31, ctime 09-18 20:30:49** | DISAGREE |
| B2 A1: S-7 file 114 B, 0664, 2026-08-23; DO-NOT-SWEEP memory; 09-07 handoff §1 item 8 sha256[:16] | `-rw-rw-r--` 114 B mtime 2026-08-23 18:59:53; `reference_worktree_sweep_hazards_2026-09-12.md` L14 "DO NOT SWEEP"; 09-07 handoff L191/L218–221 | AGREE |
| B2 A6/A9/D2/D10/D12/D21: YAM §8.27.6; #1969 = `d721fc78`; failure service tails `duplicati-backup.service`; watchdog default id 2 (`:160`); baseline 1024167 / 290.610 GiB; `install_duplicati_timer.bash` installs old lane | YAM L2789; `gh pr view 1969` MERGED, merge `d721fc78…`, head `feat/backup-updates-and-redesign-work` (design L70 already says both); `duplicati-backup-failure.service:7`; `yamaguchi_watchdog.py:160 default="2"`; snapshot Metadata exact; installer names `duplicati-backup.{service,timer}`, `…-failure.service` | AGREE |
| B2 D1: `man systemd.path` "checked immediately again" paragraph (✔); PathChanged exemption NOT in man page; `/run/media/pcalnon` root:root 0750 + ACL, empty | paragraph present (wrapped: "checked / immediately again"); the only `PathChanged=` sentence concerns activation-time existence, not re-check-on-termination; `drwxr-x---+ root root`, `user:pcalnon:r-x`, empty; systemd 259.5 | AGREE |
| B2 D5/D9/D13/D15: server-util `--password <password>`, `change-password <new-password>`, hosturl default 8200; db-tool no `--server-datafolder`, `wipe-encryption <databases>`; `.local/state` 0700; P1.2 says 0640 | `help` outputs literal; `grep -c server-datafolder` 0; `drwx------`; L1065 `chmod 0640` | AGREE |
| B2 D22 "done: AC-12 row, wrap script in §0, **§12 lists the PR's files**" | AC-12 row has no `\|` inside code; §0 ✓; §12 names only the consensus record + the two B1 instruments — not the step-reports record, forensics/env-shape/lint/wrap scripts or this handoff (§1.3 itself still says "list the changed files in §12") | DISAGREE |
| B2 D22 dissent: 42 alias refs; "§0's alias table" | B2 says 42; aliases (PLAN/YAM/DMG/GPG/CON) are defined in the header **Companions** list L9–14, not in §0, not a table | DISAGREE (minor) |
| B3 F-1…F-3 list incl. "`InaccessiblePaths=` for the pcalnon profile" | B3 F-1's list is `/etc/shadow … /var/log -/root`; no pcalnon-profile entry anywhere in B3 | DISAGREE (attribution) |
| B3 F-9 sink checklist (✔ transcript "22 env-echo lines and 21 specifier lines"; tool-results holds more) | checklist is F-10; jsonl at 14:34 (grew 9.48→9.77 MB since 14:23): `LINE: \"` 24, `Exporting Environment Variable` 28, `Failed to resolve specifiers` 38, `Invalid slot` 31; tool-results 57 files, contaminated by validators' own outputs | DISAGREE/unstable |
| §1.5.1 A3 captured `TEST_TWINE_*` | record L341: captured "into `result_k.txt` and into that tool's output", swept; both names present in my env | AGREE (wording: "never printed" is not what A3 wrote) |
| §1.5.5 "Decisions D-1 … D-13 (§10)" | §10 rows D-1…D-12; D-13 exists only as B2 A8's proposal | DISAGREE (minor) |
| §1.6 `MEMORY.md` 25.2 KB | 25,356 B at 14:22:11; **21,750 B** since 14:26:13 (rewritten 22 s before this handoff's mtime 14:26:35); target memory file exists | DISAGREE (stale) |
| §2 traps: wrapper `exec "$SERVER" "$OPTS"`; DEBUG echoes; per-login gid (Dropbox 09-19 17:36, user manager); `.backup` original inode; `sg duplicati` | `scripts/duplicati-wrapper.bash:218`, `:131/:152/:215`; `getent` `duplicati:x:139:pcalnon,duplicati` yet `id -nG` lacks it; dropbox 2948130 (17:36:35) and systemd --user 13362 have no 139; `.backup` birth 2023-05-17 00:43:03; upgrader copy birth 02:19:47.693, stub 02:19:47.788, WAL 02:19:48.142 | AGREE |
| §1.2/§1.3: CON §4/§7 contents; `open_signed_pr.py`, `wait_for_checks.py`, `safe_merge.py --pr --execute` `MERGED` line | CON L102–122, L157–166 match; files exist; `--pr` required, `--execute` present, `MERGED #` string | AGREE |
| §3 `git log -3 origin/main` "handoff PR must be in it" | `53bc8e00 (#1987)`, `3ee84ebb`, `6a957be4`; no `docs/backup-infrastructure-integrated-design` branch; no backup notes on origin/main — expected pre-PR | AGREE (pre-merge) |
| §4 file list; `worktree-atomic-sauteeing-truffle` never pushed; symlink → primary `scripts/duplicati-wrapper.bash` | `git status`: 3 AM + 2 A + 5 `??` = the 10 named; no remote branch; `lrwxrwxrwx … -> /home/pcalnon/Development/python/Juniper/juniper-ml/scripts/duplicati-wrapper.bash` (mtime 03:13:57) | AGREE |
| §5 ml#1439/#1440 | both MERGED PRs `fix(backup)…`/`feat(backup)…` | AGREE |

## 2. DISAGREE — what the handoff should say instead

1. **§0 "its four `enc-v1:` fields" / F14 "six blobs":** "the snapshot carries **nine** `enc-v1:` values (`Backup.TargetURL`, job `passphrase`, and seven server options: `jwt-config`, `pbkdf-config`, `client-license-key`, `remote-control-config`, `remote-control-storage-api-key`, `server-ssl-certificate`, `server-ssl-certificate-password`), all under one key hash; the probe tests the four it selects (TargetURL, passphrase, jwt-config, pbkdf-config), 4/4 verified. The pcalnon `.backup` carries eleven (6/6 tested). Independently: the snapshot's key hash differs from the live 0777 database's (encrypted under today's `.env` key), so PASSPHRASE is excluded without any candidate test."
2. **F11:** "§5.5 already lists `DUPLICATI__ALLOW_INSECURE_DATAFOLDER` (L282); add it to §7.3.2 (L357 'the only overrides are …'), which still omits it."
3. **F15 second half:** delete "the unit row's `NeedDaemonReload` sentence is wrong (see §0)" — §4.1's unit row already reads "A systemd reload at 03:23:44 **armed** the edited `ExecStart` …; the running process used the older form". Only the three-wave copy dating remains to apply.
4. **A1 specifier split:** "of the 22 `Failed to resolve specifiers` lines, 4 are on 09-18 (21:15:40, 21:16:10, 21:17:54, 21:29:51) and 18 on 09-19; the single `Failed to resolve unit specifiers` line is 09-18 21:23:25, so 09-18 carries 5 `Invalid slot` lines and 09-19 18."
5. **A1 Repair times:** "the `.backup` ErrorLog holds nine `Failed while executing Repair "Ubuntu"` entries on 08-25 (02:05:17, 02:13:57, 02:14:42, 02:15:31, 02:16:17, 02:17:03, 02:17:50, 02:18:37, 02:19:24) and `Verify` failures at 02:13:07 and 02:19:46; nothing at 02:19:19."
6. **`.dropbox-dist`:** "a Dropbox client (270.4.3312) owned `duplicati:duplicati`; the directory was created 09-15 15:26:22 (birth), its content mtime is 09-14 20:49:31 (the distribution's own timestamp), and its ownership/mode last changed 09-18 20:30:49 (ctime) — the 'since 09-14 20:49' date is the mtime, not the chown."
7. **B2 D22 "§12 lists the PR's files":** "§12 names the consensus record and the two B1 instruments only; the step-reports record, `…forensics.py`, `…env_file_shape.py`, `…lint_design_snippets.py`, `…wrap_long_markdown_lines.py` and this handoff are still unlisted (§1.3 must add them)."
8. **"§0's alias table":** "the alias list in the design's header (**Companions**, L9–14)".
9. **B3 F-1/F-3:** drop "`InaccessiblePaths=` for the pcalnon profile" or mark it as the orchestrator's addition; B3's list is `-/etc/shadow -/etc/gshadow -/etc/ssh -/etc/credstore -/etc/credstore.encrypted -/var/lib/docker -/var/log -/root`.
10. **B3 F-9 transcript ✔:** "count-only at HH:MM with pattern P; the number changes with every tool call (24 `LINE: \"` / 38 `Failed to resolve specifiers` jsonl lines at 14:34) and `tool-results/` also holds the validators' own outputs" — do not quote 22/21 as a fact.
11. **§1.5 item 5:** "Decisions D-1 … D-12 (§10) plus the D-13 that B2 A8 adds".
12. **§1.6 MEMORY.md:** "MEMORY.md was 25,356 B at 14:22 and is 21,750 B (21.2 KiB) since 14:26:13 — a concurrent session compacted it; re-measure before acting."
13. **§1.5 item 1:** "A3's harness wrote the two values into a scratch file and one tool output (both regenerated/swept per its report)" rather than "values never printed".

## 3. UNTRACEABLE

- `/usr/lib/duplicati/data/` contents (`BMXWPAOGLP.sqlite`, `-wal`/`-shm`), root's history/viminfo, `/home/duplicati/{.bash_history,.viminfo}`, `/proc/1397393/{exe,environ,fd}` — root/duplicati-only (EACCES).
- The 2026-08-25 journal window (journal retention starts 09-05; syslog day files start 09-12) — the Repair/Verify times come only from the `.backup` ErrorLog.
- `duplicati-cli list … --time=2026-09-18T14:00:00Z` (A0's premise) — needs the passphrase; not run. `duplicati-server --version` starts a server — not run, by rule.
- All source citations (`path.c`, `EncryptedFieldHelper.cs`, `RepairHandler.cs`, `DatabaseUpgrader.cs`, `WipeEncryption.cs`, `Program.cs` exit 102) — not re-fetched.
- Owner quotes, "no live system state was changed", the `feat/…` → `main` history of the wrapper target between 02:15 and 03:14.
- The pinned markdownlint run (hook carries `--fix`; no local binary).

## 4. Instrument adequacy

- **Key exclusion (§0 / F1):** I re-implemented the blob parse from the archived probe's comment, not its code: `sha256(ciphertext)` must equal the first 64 hex chars. It verified 9/9, 11/11, 2/2 — a wrong slice would have failed the content-hash check, so the key-hash slice is real; the cross-DB inequality could have come back `True` if PASSPHRASE were the 09-18 key. Discriminating, and secret-free.
- **Journal counts (A1/F8):** counted on the raw system journal with per-day and per-window splits and printed timestamps only; the 5-vs-4 on 09-18 and the exact 264/60/12/12 vs 220/50/10/10 are both visible, so the instrument distinguishes the handoff's compressed wording from the reports' precise one. Its blind spot: it cannot tell which lines carry the literal (never read).
- **Stale-claim checks (F11/F15):** `grep -c` for the quoted sentence ("differs from the loaded", the env-var name) — would have returned ≥1 if the design still carried the defect; it returned 0 / 1-in-§5.5, so "still to apply" is refuted for those halves. The design mtime (14:17) is earlier than the handoff (14:26), so this is not a race.

## 5. Not checked

`git fetch origin main`; `dropbox exclude list` entry names (10 lines counted only); B3's syslog "99 key-bearing lines" (not re-counted — key-shaped pattern would risk reading a value); `systemd-analyze security` baseline 5.2; AES header bytes of the volumes; `--webservice-password-init` behaviour; Duplicati 2.4.0.0 source claims generally.

<!-- markdownlint-enable -->

---

## Report H-B1 — Lane B — completeness and fidelity of the handoff's dispositions against the six verbatim round-1 reports

Subagent id `a05c87e5127bffbf3` (16,679 characters).

<!-- markdownlint-disable -->

All checks are complete; nothing further to fetch. The last read settles D1: the termination re-check paragraph (`man systemd.path` ll. 30–36) carries no exemption, while the "does not apply to PathChanged= and PathModified=" sentence (l. 98) belongs to the activation-time rule — B2 conflated the two paragraphs, and the handoff's "not in the man page" is wrong in the letter. My index is at `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/227cf645-dd93-4802-91f7-23dcaa92c971/scratchpad/hvalB1/index.md`.

# Lane B validation — handoff completeness and fidelity

Artifact: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/atomic-sauteeing-truffle/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-21_backup-redesign-round-1-validated-reconciliation-pending.md` ("the handoff"), checked against `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md` ("the record") and `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` ("the design"), same worktree. Read-only; no repository file touched. Only host reads: `man systemd.path`, a linter run into my scratch dir, `git` metadata, and Lane A3's surviving scratch captures (`scratchpad/valA3/help_dbtool_wipe.txt`).

## 1. Coverage table

| lane | findings in the report (count, IDs) | dispositioned | delegated | DROPPED (IDs) |
| --- | --- | --- | --- | --- |
| A1 | 38: DISAGREE 1–13; unrecorded facts U1–U8; UNTRACEABLE T1–T8 (the record's header says 7; the report has 8 bullets); instrument-adequacy IA-a/b; could-not-verify-without-root R1–R5; table qualifications Q1 (S-5 "broader than stated": the 0664 primary `.env` carries 12 other names, "several Slack tokens/secrets"), Q2 (S-6: five sign-in URLs, not one) | 23 (1–13; U1–U8; R1, R3) + IA-a/b already folded into the design's §11 while the handoff calls A1 "not applied" | T1–T8 ("→ §11 cannot support") | **R2** (`/proc/1397393/{environ,fd,cwd}`), **R4** (temp WAL byte identity), **Q1**, **Q2** — 4 |
| B1 | 22: F1–F17; settling observations O1–O5 | 20 (F1–F17; O1 → §1.5 item 2 / F2; O2 → §1.5 item 3; O3 → §1.5 item 4) | 0 | **O4** (root's history around 2026-08-25 02:19 — identifies the Repair actor; §1.5 item 3 covers only 09-18 20:42–21:03), **O5** (post-scrub `ls /var/log/syslog-2026092*`) — 2 |
| B2 | 39: amputations A1–A10; defects D1–D22; could-not-determine C1–C7 | 34 (A1–A10; D1–D22 with D22 partly; C1 → §1.5 item 2; C2 → D12 pre-flight) | 0 | **C3** (value of `startup-delay` — B1 F12 already answers "present at BackupID −2"; the handoff records neither), **C6** (a `.env` `--option` line `--print-command` is forwarded to the server — a real wrapper defect), **C7** (B2's line numbers are stale; re-anchor by heading) — 3; C4 (Dropbox/ext4 ACL behaviour) only partly via D14 |
| B3 | 32: un-numbered preamble (pcalnon is in `duplicati`/`adm`/`sudo`/`docker`/`libvirt`/`kvm` = root-equivalent; the boundaries the design can still buy); F-1–F-20; O-1–O-11 | 22 (F-1…F-13, F-15, F-16, F-17, F-19; O-3 via AC-12; O-4 done; O-5 partly; O-7; O-9) | F-14, F-18, F-20 ("read the report") | **preamble**, **O-1**, **O-2**, **O-6** (does the world-readable primary `.env` hold `PASSPHRASE=`? — if yes S-3 has been world-readable since 08-25), **O-8**, **O-10** (`history -c; unset HISTFILE` in the two live `su - duplicati` shells before they exit — time-critical, A1 confirms both shells are still running), **O-11** — 7 |

Dropped total: **16**. Sub-items dropped inside accepted findings (not counted above): F-1 "disable update checks/usage reporting"; F-3 "pin the job's run-script option in the acceptance check"; F-4 "extend AC-8 to run-script output"; F-5 "`.env` 0640 root:duplicati"; F-9/F-12 "re-argue/re-decide D-2" (B3's top-1); F-12 "exclude `_yamaguchi_records/`"; F-13 cloud threat table, passphrase provenance, delete-forever the old set, Dropbox Rewind (§5 declares Rewind out of scope without recording B3's dissent); F-11 pre-commit gitleaks hook; D22 "no `## Requirements` section planned".

## 2. Fidelity defects

1. **§1.1 B2 D9, §2 trap 3, design §8 STOP bullet 4 — "✔ the tool has no `--server-datafolder`" is false.** A3's verbatim capture (`valA3/help_dbtool_wipe.txt`, `duplicati-database-tool help wipe-encryption`): `--server-datafolder <server-datafolder>  The folder with databases [default: <HOME>/.config/Duplicati]`, beside `--no-backups`, `--include-untracked-databases`, `--dry-run`, `--allow-insecure-datafolder`. The top-level `help` lists only `--allow-insecure-datafolder`/`--version` — that is what B2 read (record §B2 D9) and what the orchestrator's re-check repeated. An A3-vs-B2 conflict, unnamed in "cross-lane conflicts", resolved the wrong way; it rewrites a P0 step (5) that was correct. Replacement: "`wipe-encryption <db-path>` accepts `--server-datafolder <dir>` on the **subcommand** (A3 capture); the top-level `help` does not show it (B2 read that). Point it at the copy's folder explicitly — the default is `$HOME/.config/Duplicati`, i.e. the pcalnon profile when run as pcalnon or the moved-aside folder when run as `duplicati`."
2. **§1.1 B2 D1 and §2 trap 7 — "the exemption for `PathChanged=` is NOT in the man page text on this host".** `man systemd.path` l. 98 reads "Something similar does not apply to PathChanged= and PathModified=" — but it closes the *activation-time* paragraph ("If a path already exists … at the time the path unit is activated, then the configured unit is immediately activated as well"); the *termination re-check* paragraph (ll. 30–36) carries no exemption. B2 conflated the two; the handoff is right in substance and wrong in the letter, and any round-2 grep will mark it wrong. Replacement: "the man page exempts `PathChanged=`/`PathModified=` only from immediate activation when the path already exists at unit activation (l. 98); the termination re-check paragraph (l. 30) exempts nothing — record B2's citation as a conflation; the re-check behaviour of `PathChanged=` rests on `path.c` (`path_spec_check_good`), verify against the 259 source or use udev."
3. **§1.1 B1 F1 — "so a `%`-free or file-delivered key ≠ the literal was in play first".** B1: "a `%`-free or file-delivered key ≠ **K1** was in play before the `%`-literal was ever loaded … the Mismatch is equally evidence that L ≠ K1" (K1 = the 21:03 key). "≠ the literal" is trivially true and loses the inference. Replacement: "…so a `%`-free or file-delivered key that did **not** match the 21:03 key was in play before the `%`-literal could have been loaded; the Mismatch is equally evidence that the literal ≠ the 21:03 key."
4. **§1.1 B1 F2 — "`DELETE FROM Schedule` on the copy before any start (Lane B2 D17 …)".** D17's fix is "run the probe under `systemd-run --wait -p InaccessiblePaths=/mnt/Backups -p InaccessiblePaths=/usr/lib/duplicati/data`"; B3 F-17 adds "verify `startup-delay` in the snapshot's Option rows before probing; add `--webservice-disable-signin-tokens` to the probe"; `timeout -k 10 45` is B2 D6. `DELETE FROM Schedule` is the orchestrator's own idea presented as a lane's. Replacement: name it as the orchestrator's alternative, keep D17's `InaccessiblePaths` as the recorded fix, add F-17's two items, and record B1 F12's answer to O-1 (`startup-delay` is present, BackupID −2).
5. **§1.1 B3 F-1 — "`InaccessiblePaths=` for the pcalnon profile".** F-1 lists `-/etc/shadow -/etc/gshadow -/etc/ssh -/etc/credstore -/etc/credstore.encrypted -/var/lib/docker -/var/log -/root` (or `ProtectHome=tmpfs` + `BindReadOnlyPaths=/home/pcalnon` + `BindPaths=/home/duplicati`), plus "disable update checks / usage reporting (the only legitimate egress)". The pcalnon profile appears nowhere in F-1. Replace with F-1's list.
6. **§1.5 item 1 — "into a scratch file (deleted; values never printed). Precaution only."** A3: "printed `env | grep '^TEST_'` … into `result_k.txt` **and into that tool's output**" — a tool result is the subagent transcript, which B3 F-10(f) classes as a cloud-linked sink. Replacement: "the values reached a tool result (subagent transcript) and a scratch file since regenerated; rotate the token."
7. **§1.1 B1 F15 — "profile copy in three waves … (see §0)".** B1 F15 says "two rounds"; "three waves" is A1 DISAGREE 9 (same births, different grouping). Also the "unit row's `NeedDaemonReload` sentence" no longer exists: design §4.1 l. 151 already reads "A systemd reload at 03:23:44 armed the edited `ExecStart`…; the running process used the older form" — A1's correction is already in (the "03:23:44" time was measured by no lane). Replacement: attribute the waves to A1, note B1's two-round grouping is the same data, and drop the stale target.
8. **§1.1 B2 D22 — "done in this revision: … §12 lists the PR's files".** Design §12 lists only the two B1 instruments; the four orchestrator instruments, two record files and this handoff are not listed there. Replacement: "§12 still lists only the B1 instruments; add the full file list at the follow-up PR; B2's `## Requirements`-section point is open."
9. **§1.1 B2 A9 — "the prompt is on `main` via #1969 (`d721fc78`), not `feat/backup-updates-and-redesign-work`".** A2 verified `aab07eba` on that branch (`git branch -a --contains`), and design §2 l. 70 already states both. Replacement: "on `main` via #1969 as well as at `aab07eba` on the feature branch; the primary checkout is on `main`."
10. **§1.1 D5 and the F-15 line — `--webservice-password-init` "as a one-shot run by hand".** `--webservice-password-init=<new>` puts the new password on argv unless, as B3 F-15 states, it comes "from a credential/secret provider, or `--settings-file`". Replacement: add that delivery qualifier; also record the B1 F12 ("else `--password`/prompt") vs B2 D5 ("no prompt/stdin path is documented") difference the ✔ silently settled.
11. **§1.1 F-11 says "add `DUPLICATI__ALLOW_INSECURE_DATAFOLDER` to the override list (§5.5/§7.3.2)"** — §5.5 l. 282 already carries it (A3 #3 applied); only §7.3.2 ll. 357–358 ("the only overrides are …") lacks it. Name §7.3.2 only.
12. **A1's counts** (12 passes; 24 failed starts = 5/5/14; 23 = 22 + 1 with 4 on 09-18 and 18 on 09-19; three copy waves; Repair at 02:17:50/02:18:37/02:19:24, Verify 02:19:46): all **verified** against the record. **B2 D1's mechanism** (re-trigger on termination) and **B3 F-9/F-12** are reproduced faithfully; **B1 F3/F4 and B2 D5** are faithful.
13. **"Cross-lane conflicts" (§1.1 tail).** The specifier-count and exclude-vs-delete entries are correct; the third (alias-only references) is B2-vs-orchestrator, not cross-lane. Unnamed real conflicts: A3 vs B2 on `--server-datafolder` (item 1); B3 F-5 (`.env` 0640 root:duplicati) vs A3 #9 / B2 D15 (0600 duplicati-owned); B3 F-6 (2750/0640/`UMask=0027`, volumes chowned to `duplicati`) vs R-7/R-8's group-write model and B2 D14; B1 F12 vs B2 D5 on a prompt path; B2 D1's man-page citation vs the orchestrator's reading (item 2).

## 3. Applied claim (design text checked)

| # | correction | verdict | design line |
| --- | --- | --- | --- |
| A2 #1 | R-13 wording | APPLIED | 86 |
| A2 #2 | R-17 source → Y §8.10.2 + 08-22 handoff §3 | APPLIED | 90 |
| A2 #6 | rule 10 `dbconfig.json` characterisation | APPLIED | 124 |
| A2 #7 | §3.5 → YAM §8.20.2 | APPLIED | 140 |
| A2 #11 | §4.3 item 11 rename/`ea83bad7` text | APPLIED | 210–211 |
| A2 #12/#13 | linter: basename dispatch, extract-before-lint | APPLIED — script ll. 86–89, 168; my run: both extension-less blocks `[PASS] KEY=VALUE / --option grammar`, `blocks: 12  failures: 0` (§3's expectation holds) | — |
| A3 #1 | `/run/media` | APPLIED | 163, 222–233, 811, 882, 965 |
| A3 #2 | drop `--no-local-blocks=true` | APPLIED | 748 |
| A3 #3 | gate release history + env-var override | **PARTLY** — §5.5 l. 282 yes; §7.3.2 ll. 357–358 still "the only overrides are `--allow-insecure-datafolder` or an `insecure-permissions.txt` marker" | 357 |
| A3 #6 | libsecret only | APPLIED | 683 |
| A3 #9 | `.env` 0600 | **PARTLY** — §7.3.5 l. 662 yes; P1 step 2 l. 1065 still `chmod 0640` (B2 D15, in the handoff) | 1065 |
| A3 #10 | AC-12 wording | APPLIED | 1108 |

A3 #7 is moot (no schema-directory path remains in §5.3). Residual not in either list: §1 l. 52 and §4.3.9 l. 208 still say "port 8200, or not at all" (B1 F11: "not at all"); the handoff's F11 names §4.3 item 9 but not §1.

## 4. Internal contradictions and STOP-warning defects

1. **§0 "Design PR MERGED as PR_NUMBER_PLACEHOLDER"; §4 "Branch `docs/backup-infrastructure-integrated-design` was opened … and merged"; §3 expects the PR in `origin/main`.** Git now: design absent from `origin/main` (`git ls-tree` → 0), no such branch locally or remotely, every file staged/untracked on `worktree-atomic-sauteeing-truffle`. Past tense for a future event; §3 fails as written. Replacement: "to be merged as #<fill in before commit>; until then the design exists only on `worktree-atomic-sauteeing-truffle`".
2. **STOP bullet 4** — `printf '%s' '<value>'` is P0 step 3 (B2 D7), not "steps 5, 7 and 9"; "(D5–D11)" lumps D6 (WAL copy) and D8 ("first start only") which the bullet never describes; the `--server-datafolder` clause is wrong (fidelity 1). Replacement: "P0 steps 3, 5, 7 and 9 put secrets on a command line (D5, D7); step 5's re-entry names no tool (D9); step 6's job id (D10); AC-2 before the credential (D11); D6/D8 see bullet 1 and Procedure A."
3. **STOP bullet 3** names "Procedures A, A2 and B" — B1 F4 says "Same step for A0"; §0's own row says "every procedure". Add A0.
4. **Status line / §11 "A1, B1 … not applied"** vs the design already carrying A1 DISAGREE 1 (l. 151), A1's adequacy re-run and B1's hash-test result (§11 ll. 1135, 1144). Replacement: "partially folded: §4.1 unit row, §11 adequacy and 'cannot support' entries, the §8 warning".
5. **§0 "Root cause CLOSED and SURVIVED all six lanes … Only the *attribution* … changed"** vs §1.1 F6 ("as written §5.6 row C is not a refutation test") and F7 ("right conclusion, wrong evidence"). Replacement: "the three legs survive; §5.3's actor, §5.4's discriminator, §5.6 row C and the 21:03:34 marker are rewritten per B1 F5–F7".
6. **§0 Recovery source 1 "needs the escrowed passphrase and nothing else"** vs §0's index row and F4/step 7 (DBPath move, `--tempdir`, guard). Replacement: "nothing else *to decrypt it*".
7. **§2 trap "there is no `--server-datafolder`"** — false (fidelity 1); **§2 trap "`PathChanged=` does not (per source, not man page)"** — reword per fidelity 2.
8. **§5 "Dropbox Rewind … not evaluated"** vs B3 F-13, which makes Rewind/version history a design item (sole recovery from a mass delete; a new set must delete-forever the old). Record as dissent, not scope.
9. **§1.6 "Appendix C items 1–8 are unchanged"** — item 2 was rewritten by A2 #8 (l. 1221). Say "not yet applied to YAM / the 09-07 handoff / the snapshot script".
10. **§1.5 owner actions omit** O-10 (live `duplicati` shells), O-6 (primary `.env` `PASSPHRASE=` count), B1 O4 (08-25 Repair actor), and the D-2 re-decision (B3 top-1).
11. **§0 "data folder `/home/duplicati/.config/Duplicati/`"** stated as fact; A1 T4 says `/proc/1397393` is unreadable and the folder is inferred. Add "(inferred — A1)".

## 5. Five most consequential

1. Fidelity 1: a ✔-marked "no `--server-datafolder`" that A3's own capture refutes — it rewrites a correct P0 step, poisons §2 and the STOP block, and hides an A3-vs-B2 conflict.
2. Sixteen drops, four of them owner-time-critical: O-10 (shell history appends on exit), O-6 (a possibly world-readable `PASSPHRASE=` since 08-25), A1 Q1 (Slack tokens in the 0664 `.env`), the D-2 re-decision.
3. Fidelity 6: "values never printed" understates a TestPyPI token that transited a cloud-linked transcript.
4. Contradiction 1: the handoff asserts a merged PR that does not exist; its own §3 cannot pass.
5. Fidelity 2/3/4: three dispositions (D1 man page, F1 "≠ the literal", F2 `DELETE FROM Schedule`) misstate what the lanes said in exactly the places round 2 will re-check.

## 6. What I could not determine

- The transcript counts in F-9 (22 env-echo / 21 specifier lines) — I did not open the transcript (secret-shaped content).
- Whether `path.c`'s `path_spec_check_good` at systemd 259 behaves as the handoff states (no source fetched).
- The "03:23:44 global systemd reload" time (no lane measured it; the design states it three times).
- Whether `/var/log/syslog*` day files reach back to 09-12 (orchestrator ✔; B3 lists only 09-19/20/21).
- The semantics of `--server-datafolder` on `wipe-encryption` when an explicit DB path is also given (help text only, no run).
- Whether `duplicati-server-util` has a prompt path (B1 F12 vs B2 D5; no binary was run).

<!-- markdownlint-enable -->

---

## Report H-B2 — Lane B — actionability for a fresh thread, and refutation of the handoff's five most consequential claims

Subagent id `a46fb819739f3ec33` (14,082 characters).

<!-- markdownlint-disable -->

All probes are in; nothing further to request. Deliverable follows.

## 1. Actionability defects

1. **§3 line 1 — `cd /home/pcalnon/Development/python/Juniper/juniper-ml` / `git fetch origin main --quiet`.** A fresh worktree thread is refused by the isolation shim for both (`cd` to the primary and any `git -C <primary>`: *"a worktree-isolated session's git operations must target its own worktree"* — I hit it), and `git fetch` is a ref write. Replacement: run from the worktree root; `git ls-remote origin main` + `git log --oneline -3 origin/main`; read the primary's branch as a file: `cat /home/pcalnon/Development/python/Juniper/juniper-ml/.git/HEAD`.
2. **§4 — "`gh pr list --state merged --limit 5`".** This repo merged #1981–#1987 today alone; the design PR will be off the top five by the time a fresh thread starts. Replacement: `gh pr list --state merged --search 'head:docs/backup-infrastructure-integrated-design'`.
3. **§1.1 D9 "(✔ the tool has no `--server-datafolder`)" and §2 "there is no `--server-datafolder`" — wrong.** `duplicati-database-tool wipe-encryption --help` lists `--server-datafolder <dir>` (default **`/home/pcalnon/.config/Duplicati`** — the orphaned profile), `--no-backups`, `--include-untracked-databases`, `--dry-run`, `--allow-insecure-datafolder`. The ✔ was taken from the top-level `help`, which hides sub-command options (instrument answered an adjacent question). A reconciler would write a false fact into §11 and strip a valid option from P0 step 5, while missing the real hazard: with no database argument the tool targets the pcalnon profile's stub. Replacement: "`wipe-encryption <copy>/Duplicati-server.sqlite --dry-run` first (verified 2026-09-21 on a scratch copy of the snapshot: `version 11 … Server database … 9 encrypted field(s) would be wiped`); always pass the path; never rely on the default folder. **`--dry-run` still rewrites the copy's header** — `journal_mode` flips `delete → wal`, `-wal`/`-shm` appear, sha256 changes — so hash before, or re-copy after."
4. **§1.4 item 2 — "re-run the key-hash probe … candidate in a 0600 file".** The probe has no candidate-file argument: argv[1] = wrapper (literal `L`), argv[2] = pcalnon credential file (`PASSPHRASE`/`PASSPHRASE_OLD=` lines), argv[3:] = `label=dbcopy`; stdin lines matching `SETTINGS_ENCRYPTION_KEY=` become `ENV_ACTIVE_KEY`. A fresh thread would write a new script or put the value on argv. Replacement: "write one line `SETTINGS_ENCRYPTION_KEY=<value>` into a 0600 file; `cat <file> | python3 util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py scripts/duplicati-wrapper.bash ~/.config/duplicati-backup/env snap=<copy>` (the `.env` may be concatenated on the same stdin)".
5. **§1.5 item 5 — "Decisions D-1 … D-13 (§10)".** §10 holds D-1…D-12 (`grep -c D-13` → 0); D-13 is created by B2 A8 at reconciliation. Replacement: "D-1 … D-12, plus D-13 (Dropbox root policy) once §1.1 A8 lands".
6. **§1.5 item 3 — "`duplicati.service~`/`.swp`/drop-in" with no directory.** The loaded unit is the **vendor** file `/usr/lib/systemd/system/duplicati.service` (`FragmentPath`; `DropInPaths=` empty; edited in place), which the design's §7.3 block (`# file: etc/systemd/system/duplicati.service`) will shadow, not replace. Replacement: "`sudo ls -la /usr/lib/systemd/system/ | grep -i duplicati` (look for `.duplicati.service.swp`, `duplicati.service~`), `sudo ls /etc/systemd/system/duplicati.service.d/ 2>/dev/null`; `sudo grep -c ENCRYPTION /root/.bash_history` before reading".
7. **§1.5 item 1 — TestPyPI token.** The owner is not told where the value lives: `~/.bashrc` is the only startup file naming `TEST_TWINE_*` (grep -l; values unread), and both are in this session's environment. Replacement: "revoke at test.pypi.org → API tokens, mint a new one, replace the value in `~/.bashrc`; CI is OIDC, nothing in `.github/` changes".
8. **§1.5 item 4 — `duplicati-cli list …`.** Largely right: `list` is an accepted alias (`help list` prints the `find` usage: *"list shows only the latest version by default"*), `--time` takes absolute ISO, `--no-local-db` exists ("when listing contents … the local database can be skipped"), `PASSPHRASE` maps to `--passphrase`. Sharpen: the 09-18 14:00Z fileset **is** the latest (9 dlists, newest `20260918T140000Z`), so `--version=0` removes the `Z`-parsing doubt; add `--no-local-db=true`; keep `--dbpath` (without it Duplicati consults the orphan profile's `dbconfig.json`); load the passphrase with `set -a; . ~/.config/duplicati-backup/env; set +a` in a subshell, never `export PASSPHRASE=…` in a history-enabled shell.
9. **§1.2 — pool and done-criterion.** "Two or three fresh validators (one Lane A …; one Lane B …)" names two lanes and leaves the third unspecified; procedure §3's top-right cell (document of record, instrument previously wrong, universal quantifiers, a fix hangs on it) prescribes 3+ Lane A with distinct entry points + 2+ Lane B; termination is only by reference. Replacement: "Round 2 = Lane A ×2 (host: re-run §3 and every §4/§5 count that changed; product: 2.4.0.0 `help` + DLL-name scan for every option the reconciled P0 uses) + Lane B ×2 (actionability of reconciled §8; security of the P0.5 bucket), briefed only on the change list and dissent; archive verbatim to `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md`; done when a round changes no number, disposition or action; ≤3 subagents at once."
10. **§1.1 D22 dissent — "§0's alias table binds each alias to a filename".** No such table exists in §0 or anywhere; PLAN/YAM are bound in the header's source list (design lines 10–11, prose). 41 short-name references (29 `YAM §`, 9 `PLAN §`, 3 `CON §`). Also: **the shim refuses any command containing the word "alias"** (git-alias guard) — grep it from a script. Replacement: "the header source list (lines 8–16) binds PLAN/YAM/CON; write the dissent against that".
11. **§3 Expect "`MainPID=1397393`".** Absolute where the distrust order says it rots. Replacement: "MainPID unchanged from §0; if it differs, the armed `ExecStart` has fired — read `NRestarts`, `ss`, journal, and stop treating §0 as current".
12. **§1.6 — "MEMORY.md is 25.2 KB".** It is 21,750 B / 80 lines now (concurrent edits). Replacement: "`stat -c %s` it at start".
13. **§1.1 D5/F12 omit the documented non-argv channel.** `duplicati-server-util` accepts `--secret-provider` (`env`, `file-secret`, `libsecret`, …) with `--password='$name'`, and `SETTINGS_ENCRYPTION_KEY` from the environment for the signin-token path. Add as an option (untested whether `$name` substitution reaches the `change-password` positional).

## 2. §3 verification run

| Command | Printed | Holds |
| --- | --- | --- |
| `git log --oneline -3 origin/main` (+ `git ls-remote`) | `53bc8e00 fix(deps)… (#1987)`, `3ee84ebb`, `6a957be4`; remote = 53bc8e00 | N/A — design PR not yet opened (placeholder); `git fetch` skipped (ref write) |
| `ls -la notes/…BACKUP-*` | 3 files: 188,479 / 247,900 / 122,716 B | ✔ |
| status grep | line 6: `DRAFT — consensus round 1 COMPLETE (six validators), reconciliation PENDING` | ✔ |
| report counts | `6` / `5` | ✔ |
| lint (workdir in my scratch) | `blocks: 12  failures: 0` | ✔ |
| `systemctl show …` | `ActiveState=active NeedDaemonReload=no MainPID=1397393 ExecMainStartTimestamp=Sun 2026-09-20 18:19:42 CDT User=duplicati` | ✔ |
| `ss -tln` | `127.0.0.1:8300`, `[::1]:8300` only | ✔ |
| snapshot dir | `Duplicati-server.sqlite` 245,760 B 2026-09-21 08:45:00 (dir 0700, file 0600) | ✔ |
| watchdog tail | `2026-09-21T12:00:39-0500 ALERT UNREACHABLE backup=2 login failed: … (401)` | ✔ |
| `ls -t Yamaguchi \| head -1` | `duplicati-20260918T140000Z.dlist.zip.aes` | ✔ |

Shim refusals met: `git -C <primary>`; `sed` with a shell-variable filename; any command string containing "alias". Not refused: one-line `awk '{print …}'`, heredoc-python inside a scratch script.

## 3. Refutation attempts

1. **Armed hazard (§0/F15)** — `systemctl cat`: `ExecStart=/home/duplicati/bin/duplicati-wrapper.bash '--daemon-opts="${DAEMON_OPTS}"'`, `EnvironmentFile=-/etc/default/duplicati`, `Restart=always`, `NeedDaemonReload=no`, `NRestarts=0`; `/proc/1397393/cmdline` = 2 words, second ends `webservice-port=8300 ` (trailing space); journal "is denied" at 18:47:44 ×4 and 18:51:33 ×4. **SURVIVES.**
2. **"0 backups defined, schema 12" on :8300** — forensics tool on a copy of the 0777 stub+WAL: `Version (1,12)`, `Backup 0 row(s)`, `Schedule 0`, 4× `Failed to import backup`. **SURVIVES.**
3. **"no `--server-datafolder`" (D9, §2)** — sub-command help lists it; dry-run with `--server-datafolder <copydir>` ran, rc=0. **REFUTED** (see defect 3).
4. **§4 git/host claims** — primary `.git/HEAD` = `ref: refs/heads/main`, `git worktree list` → primary at `d721fc78 [main]`; `readlink -f` wrapper → `/home/pcalnon/Development/python/Juniper/juniper-ml/scripts/duplicati-wrapper.bash`; superseded draft: no file, no `git log --all` entry, no worktree copy. **SURVIVES** (add: primary is 2 commits behind origin/main, so a `git pull` there — not only a `checkout` — changes what the service runs).
5. **B2 D1 / `PathChanged=` (§1.1, §2)** — `man systemd.path` lines 30–36 carry the re-trigger paragraph; lines 96–98 "does not apply to PathChanged=" concern initial activation only, as the handoff says. **SURVIVES**; the source claim (`path_spec_check_good`: `good = !initial && !from_trigger_notify` for CHANGED/MODIFIED) is consistent with what I know of path.c but unverifiable on this host — a scratch user path unit + `touch` tests it without a drive.

Also tested and held: DOWN-since (dlist mtime 09:12:00 CDT = 14:12Z), 877 files, 9 dlists; `.local/state` 0700; `/run/media/pcalnon` 0750 root + ACL `user:pcalnon:r-x`, empty; escrow `-rwxrwx--- pcalnon:duplicati` at `…/Dropbox/Backups/_yamaguchi_keys/env`; hummingbird `.env` 0664/114 B/2026-08-23; `/usr/lib/duplicati/data` 0700 mtime 21:03:34; F11 ctimes (3 files 18:25:47, dir 18:33:45); `/home/duplicati/bin` 0777; A7's `+` = `user.com.dropbox.attrs` with no ACL entries; uid 133/gid 139; `sg duplicati` grants gid 139 without a password although this login lacks it; all cited option names (`webservice-password-init`, `webservice-disable-signin-tokens`, `require-db-encryption-key`, `disable-db-encryption`, `run-script-before-required`, `upload-verification-file`, `startup-delay`) exist in the 2.4.0.0 assemblies (UTF-16 scan — in `Duplicati.Server.Implementation.dll`, not `Duplicati.Server.dll`); routes `/api/v1/serverstate{,/pause,/resume}` and `/api/v1/backup/` exist. Weakened: D22 "alias table" (defect 10); MEMORY.md size (defect 12).

## 4. Missing

- The loaded unit's path (`/usr/lib/systemd/system/duplicati.service`, vendor, `enabled`) and that §7.3 shadows rather than replaces it.
- `/etc/default/duplicati` is `duplicati:duplicati` 0644 (in design §4.1) — absent from the P0.5 same-session bucket; the service user can rewrite its own next argv.
- `wipe-encryption --dry-run` side effect; the `--server-datafolder` default.
- The probe's stdin candidate format.
- `open_signed_pr.py` requires `--repo --branch --message --title --body-file` and one `--add LOCAL:REPOPATH` per file (whole-file uploads); `wait_for_checks.py --pr`; `safe_merge.py --pr N --execute` (six `MERGED` emitters).
- The pinned markdownlint hook runs with `--fix` (`.pre-commit-config.yaml` line 232) and no cached env exists — the first run installs node and mutates the design.
- D2 is a one-line unit: the reporter takes `$1` (`UNIT="${1:-duplicati-backup.service}"`); existing user units: `duplicati-backup.{service,timer}`, `duplicati-backup-failure.service`, `yamaguchi-watchdog.{service,timer}` (watchdog `ExecStart` runs the primary checkout's `yamaguchi_watchdog.py`, no `--backup-id`).
- `util/install_duplicati_service.bash` exists only as design line 598 (D4 reads as if it were in `util/`).
- `~/.config/duplicati-backup/web-credential` does not exist yet (D11 ordering is live).
- Round-2 archive filename; follow-up branch/PR naming.
- An offline instrument for option names (my `dll_names.py`, scratch) — the handoff's "Duplicati 2.4.0.0 source" is not on the host.

## 5. Five most consequential

1. D9/§2 `--server-datafolder` claim is false and inverts the real hazard (default = orphan profile).
2. §3/§4 commands are refused or fragile in a worktree session (`cd`, `git fetch`, `git -C`, `--limit 5`, the word "alias").
3. §1.2 round-2 pool is below procedure §3 and has no explicit done/archive criterion.
4. §1.4 item 2 cannot be executed as written (probe input format).
5. Owner items 1/3/5 lack their "where" (`~/.bashrc`; `/usr/lib/systemd/system/`; D-13 absent).

## 6. What I could not determine

Whether `--webservice-password-init` exits non-zero (cannot run the server); whether `--time=…Z` parses (untested without the passphrase); path.c semantics on this host (no source); whether `--secret-provider` substitution reaches `change-password`'s positional; `list` behaviour on a nonexistent `--dbpath` (I believe it falls back to the remote dlist; `--no-local-db=true` removes the doubt); whether pinned markdownlint passes (not run — `--fix`); the specifier-line counts (not re-counted); who pointed the empty server at `/media/pcalnon/temp_backups`.

**Changed**: nothing in the repository; scratch only (`…/scratchpad/hvalB2/{wipe_dryrun.bash,wipe_dryrun2.bash,dll_names.py,grep_alias.bash,snips/,wipe/,wipe2/,forensics/}`). **Referenced**: `HANDOFF_2026-09-21_backup-redesign-round-1-validated-reconciliation-pending.md`, `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`, `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`, `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`, `HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md`, `util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py`, `util/ad-hoc/2026-09-21_duplicati_server_db_forensics.py`, `util/ad-hoc/yamaguchi_server_api.py`, `util/ad-hoc/duplicati_api.py`, `util/duplicati_backup_failure.bash`, `.pre-commit-config.yaml`.

<!-- markdownlint-enable -->

---

## Report H-R2 — round 2 (verification of the corrections)

Briefed on round 1's fifteen corrections; verified each, two of them from source (systemd v259 `path.c`, Duplicati `ServerUtil/Connection.cs` at the 2.4.0.0 tag); found sixteen regressions or leftovers, all folded into the handoff before round 3. Subagent id `acb0c65b95a6d76b1` (16,046 characters).

<!-- markdownlint-disable -->

## Round 2 — verdict on the corrected handoff

All re-measurement was read-only (host, journal counts/timestamps only, scratch copies, `help` output, three source fetches from GitHub at the 2.4.0.0 tag / systemd v259). Handoff and design were unchanged from 14:49:43 CDT through the end of this review (`diff` rc 0). Scratch: `…/scratchpad/hvalR2/`.

### (1) Corrections applied?

| item | corrected passage (§, quote) | correct? | re-measured evidence |
|---|---|---|---|
| 1 | §1.1 D9 "DOES accept `--server-datafolder <dir>` on the subcommand … default `$HOME/.config/Duplicati`"; §2 trap "`--dry-run` is not read-only" | yes | `help wipe-encryption` lists `--server-datafolder` (default `/home/pcalnon/.config/Duplicati`), `--dry-run`; top-level `help` lists neither. Scratch `--dry-run` on today's snapshot: rc 0, "9 encrypted field(s) would be wiped. No changes were made", yet sha256 8ea9eba9…→423695da…, header `journal_mode`=wal (the `-wal`/`-shm` pair exists only while it runs). A 0775 folder was NOT refused when the DB path is explicit. |
| 2 | §1.1 D1 "ll. 30–36, which exempts nothing … l. 96–97 is about immediate activation … rests on `path.c` … verify" | yes, and now verified | `man systemd.path` ll. 30–36 = termination re-check, no exemption; ll. 95–97 = "If a path already exists … immediately activated … does not apply to PathChanged=". v259 `path.c`: `case PATH_CHANGED: case PATH_MODIFIED: b = access(s->path, F_OK) >= 0; good = !initial && !from_trigger_notify && b != s->previous_exists;` and `path_trigger_notify_impl` → `path_enter_waiting(p, false, /*from_trigger_notify=*/true)` → `PathChanged=` does not re-trigger on termination; `PathExists=` (`good = access(...) >= 0`) does. |
| 3 | §1.1 F1 "a `%`-free or file-delivered key that did **not** match … equally evidence that the literal ≠ the 21:03 key" | yes | Journal 09-18 21:08–21:12: 15 `Main process exited` (30 `Mismatch` lines, 21:08:06–21:11:43); first `Failed to resolve specifiers` 21:15:40. Matches record B1 F1 verbatim. |
| 4 | §1.1 F2 "B2 D17 … B3 F-17 … B2 D6 … the orchestrator's own addition is `DELETE FROM Schedule`" | yes | Record: D17 `systemd-run --wait -p InaccessiblePaths=…`, F-17 `startup-delay` + `--webservice-disable-signin-tokens`, D6 `timeout -k 10 45`; B1 F2 has no Schedule delete. `startup-delay` present by name at BackupID −2 (my census). |
| 5 | §1.1 B3 "InaccessiblePaths=-/etc/shadow … -/root … disable update checks and usage reporting" | yes | Verbatim in record F-1. |
| 6 | §1.5 item 1 "into a tool result — i.e. its subagent transcript … Where: `~/.bashrc`" | yes (two transcripts) | `grep -c TEST_TWINE`: `.bashrc` 2; `.profile`, `.bash_aliases`, `/etc/environment`, `/etc/profile` 0. Count-only: `agent-a7b00f28…jsonl` 1 line `TEST_TWINE_*=` + 1 `=pypi-`; `agent-acb0c65b…jsonl` 3 `=pypi-`/`__token__` lines. |
| 7 | §1.1 F15 "three waves (A1 item 9 …) — B1 groups the same births as two rounds … "03:23:44" … orchestrator's own reading" | yes | Record A1 item 9 "Three waves", B1 F15 "two rounds"; births re-measured 18:40:36 / 18:42:18–22 / 21:57:36 / 04:15:42 / 04:41:07 / 04:43:02; record has 0 hits for `03:23`; journal 09-21 03:23:44 `Reload requested from client PID 2481512 ('systemctl')`; design §4.1 row carries it. |
| 8 | §1.1 D22 "AC-12 row, `wrap_long…` in §0, full file list in §12 … **Companions** binds each alias" | mostly | AC-12 row now without `\|` in backticks; §0 names the four drafting instruments; header **Companions** binds PLAN/YAM/DMG/GPG/CON; `grep -o`: 29 `YAM §`, 9 `PLAN §`, 3 `CON §` — plus 4 `DMG §`, 1 `GPG §` (=46). See R5–R7. |
| 9 | §1.1 A9 "on `main` via #1969 (`d721fc78`) **and** at `aab07eba` on `feat/…`" | yes | `aab07eba` is a commit contained only by `feat/backup-updates-and-redesign-work` (+ origin); `gh pr view 1969`: MERGED 08:07:48Z, head that branch, mergeCommit d721fc78…; primary `.git/HEAD` → main = d721fc78. Design §2 l.71 says both; §4.3.8 still "feature branch" (pending, as stated). |
| 10 | §1.1 D5 "takes its value from a secret provider or `--settings-file`, never `=<new>` on argv … B1 F12 vs B2 D5 … unsettled … `--secret-provider`" | partly | `duplicati-server-util help`: `--password <password>`, `change-password <new-password>`, `--secret-provider`, `--secret-provider-pattern` default `$`. `Program.cs` (tag): `OPTION_WEBSERVICE_PASSWORD_INIT` is `ArgumentType.Password` (takes a value); `EXITCODE_INITPASSWORD_SUCCESS = 102`, `_FAILED = 103`; applied only while `AutogeneratedPassphrase`. `ServerUtil/Connection.cs` (tag): refresh token → DB-minted signin token → `Utility.ReadSecretFromConsole("Enter server password: ")` → "Password is required" → the dispute is settled for B1 (R8, R9). |
| 11 | §1.1 F11 "(§5.5 already has it; done in this revision) … §4.3 item 9 **and §1**" | yes | Design l.359 (§7.3.2) and l.283 (§5.5) carry `DUPLICATI__ALLOW_INSECURE_DATAFOLDER=true`; l.53 (§1) and l.209 (§4.3.9) still say "8200, or not at all" (pending). |
| 12 | A1 R1–R5 / S-5,S-6 qualifications; B1 O4/O5; B2 C3/C4/C6/C7; B3 preamble, O-1…O-11, F-3/F-4/F-5/F-6/F-9–F-13/F-11 sub-items | yes | All present; O-6 re-measured: primary `.env` 0664, 0 `^PASSPHRASE=`, 1 `DUPLICATI_WEB_CREDENTIAL=`, 13 assignments. |
| 13 | §0 "To be merged as PR_NUMBER_PLACEHOLDER"; Root cause row "F5 … F6 … F7"; source 1 "needs the escrowed passphrase and nothing else"; "inferred from `lock_v2` and the live WAL's birth" | yes, except §3's "first three checks" (R3) and §4 tense (R14) | — |
| 14 | §0 rows + §1.1 A1/B3 paragraphs | yes | Fresh copies: snapshot 9/9 `enc-v1:` (probe-selected 4/4), `.backup` 11/11 (6/6), live 2/2; three pairwise-disjoint key hashes; live matches `PASSPHRASE` and `ENV_ACTIVE_KEY` (probe, labels only). 09-18 `Invalid slot` 5 = 4 + 1 (21:15:40, 21:16:10, 21:17:54, 21:23:25, 21:29:51); 09-19 18, last 18:07:32; total 23. `.backup` ErrorLog 08-25: nine `Repair` 02:05:17…02:19:24, `Verify` 02:13:07/02:19:46 (the record's A1 "three" is the forensics tool's `ERRLOG_LIMIT = 5`). `.dropbox-dist` birth 09-15 15:26:22 / mtime 09-14 20:49:31 / ctime 09-18 20:30:49. Transcript pattern count now 48 (see R15). 24 failed starts 09-19 20:48–21:55 by `Main process exited` (14 in 21:43–21:55); 12/10 `Exporting`. |
| 15 | §3 comment, §4 `gh pr list --search`, MainPID relative, stdin candidate, D-13/D-14, `/usr/lib/systemd/system/` + `.d/`, `--version=0 --no-local-db=true`, pool/≤3/archive/done, `open_signed_pr.py` flags, no `--fix`, `/etc/default/duplicati`, vendor unit shadowed, `alias` | yes, with R2/R4/R13 | `systemctl show`: MainPID 1397393, NRestarts 0, NeedDaemonReload no, FragmentPath `/usr/lib/systemd/system/duplicati.service`, DropInPaths empty, Restart always; `ss`: 8300 only; `open_signed_pr.py --help` = `--repo --branch --add LOCAL:REPOPATH --message --title --body-file`; pinned hook rev v0.42.0 = `repoft72ba_k` binary, both files lint clean (rc 0); `/etc/default/duplicati` `-rw-r--r-- duplicati:duplicati`; `duplicati-cli help no-local-db`/`help passphrase` (env `PASSPHRASE`) as claimed; `.duplicati.service.swp` root 0644, no `.d/`; the shim refused two of my own compound commands. |
| (a) | §8 STOP bullet 3 "Procedures A0, A, A2 and B all leave `DBPath` absolute" | yes | l.996 |
| (b) | bullet 4 "steps 3, 5, 7 and 9 … D7 and D5 … (D9) … (D10) … (D11) … (D6 …) … (D8). Step 5's … is correct as written: the subcommand's own `help` shows `--server-datafolder <dir>`" | yes | ll. 997–998 |
| (c) | §7.3.2 "…, `DUPLICATI__ALLOW_INSECURE_DATAFOLDER=true` or an `insecure-permissions.txt` marker …, neither of which" | yes (grammar nit R12) | l.359 |
| (d) | P1 step 2 "`chmod 0600`" | yes | l.1067 |
| (e) | status "beyond the §4.1 unit row, §11 and the §8 warning"; §11 "except the §4.1 unit row (A1 item 1), this section's … and the §8 warning" | present but now incomplete (R1) | ll. 6, 1143 |
| (f) | §12 "this file, the two `…RECORD.md` files, `…BACKUP-HANDOFF-CONSENSUS-RECORD.md`, the handoff, six `util/ad-hoc/2026-09-21_*.py`" | present but disagrees with §4 (R7) | l.1158; `git status` shows no HANDOFF-CONSENSUS file |

### (2) Regressions / new defects

1. **Exception lists are stale** — handoff ll. 10–11 ("only the §4.1 unit row, the §11 … entries and the §8 STOP warning"), §1.1 intro ("none is applied"), design status line l.6 and §11 l.1143 — while F11, D15 and D22 say "done in this revision" and design §12's last row lists §7.3.2, P1 step 2, AC-12/§0/§12 as applied. Replace each with: "applied so far: the §4.1 unit row; the §11 adequacy and cannot-support entries; the §8 STOP warning; the §7.3.2 env override (B1 F11); P1 step 2 `chmod 0600` (B2 D15); the AC-12 row, §0 instrument list and §12 file list (B2 D22). Nothing else below is applied."
2. **§1.4 probe bullet** "(the `.env` may be concatenated on the same stdin …)" — the probe keeps only the LAST uncommented `SETTINGS_ENCRYPTION_KEY=` line (one label, `ENV_ACTIVE_KEY`; verified in code and by `candidates loaded`), so concatenation silently drops the candidate or the `.env` key. Replace with: "Feed the candidate ALONE on stdin: the probe keeps only the last uncommented `SETTINGS_ENCRYPTION_KEY=` line it reads, so a concatenated `.env` would discard one of the two; the `.env`'s own candidates are already excluded. Expect `candidates loaded: ['ENV_ACTIVE_KEY', 'L', 'PASSPHRASE', 'PASSPHRASE_OLD']`."
3. **§3 "The first three checks fail until the PR in §4 has merged."** — checks 1–2 cannot fail, and `git log origin/main` shows the last-fetched ref (today 53bc8e00 vs remote 739a233c; a fetch is refused). Replace with: "Until the PR in §4 has merged, `git ls-remote origin main` will not equal the PR's `mergeCommit` (`gh pr view <N> --json mergeCommit`; `git log origin/main` shows the LAST-FETCHED ref), and the five file checks — the `ls`, the three `grep`s, the snippet linter — pass only in a checkout carrying the branch, i.e. this worktree."
4. **§1.1 B3 paragraph attributes `/etc/default/duplicati` to F-7/F-8**; no B3 finding names it (record hits: A1 §4.1 row, A3 (j), B1 F6). Replace with: "…runs a pcalnon-writable script (F-8); and — the orchestrator's addition from A1's §4.1 row, not a B3 finding — `/etc/default/duplicati` is `duplicati:duplicati` 0644 (the service user can rewrite its own next argv) → root-owned;".
5. **§1.1 D22 count** "41–42 … (29 `YAM §`, 9 `PLAN §`, 3 `CON §`)" omits 4 `DMG §` + 1 `GPG §`. Replace with: "(29 `YAM §`, 9 `PLAN §`, 3 `CON §`, 4 `DMG §`, 1 `GPG §` = 46 by `grep -o`; B2's 42 covered `PLAN`/`YAM` on an earlier revision)". Same figure in design §11.
6. **Design §11 l.1145** "which §0's alias table is held to satisfy" — no such table; replace with "which the header's **Companions** list (alias → filename, in the same document) is held to satisfy".
7. **Design §12 vs handoff §4**: §12 names `…BACKUP-HANDOFF-CONSENSUS-RECORD.md`; §4's "Changed by that PR" does not, and the file does not exist. Either add to §4 "`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-HANDOFF-CONSENSUS-RECORD.md` (round-1 and round-2 handoff-validator reports, verbatim)" and create it before the commit, or delete the name from §12.
8. **§1.1 D5 wording** "takes its value from a secret provider or `--settings-file`, never `=<new>` on argv" misdescribes the option. Replace with: "is a Password-type option (`Program.cs`: applied only while `AutogeneratedPassphrase`; exit 102 on success, 103 otherwise — so `Restart=on-failure` loops it) that CAN carry the value on argv, which is why it must be fed through `--secret-provider` (`$name` placeholder) or `--settings-file` and run once by hand with the service stopped (B3 F-15); never in `DAEMON_OPTS`."
9. **B1 F12 vs B2 D5 is settled** (§1.1 D5/F12, §1.4 bullet 4, cross-lane list). Replace the cross-lane entry with: "B1 F12 vs B2 D5 — SETTLED for B1 (round 2): `Duplicati/CommandLine/ServerUtil/Connection.cs` at `v2.4.0.0_stable_2026-09-03` tries the refresh token, then a signin token minted from the local DB, then `Utility.ReadSecretFromConsole("Enter server password: ")`; `help` simply does not list it. The in-process client (D5) stays the fix." Drop "Settle B1 F12 vs B2 D5" from §1.4 (keep B3 O-2).
10. **§1.1 D1 / §2 trap** "verify against the 259 source": verified — append "verified (round 2): v259 `path.c` `path_spec_check_good` → `good = !initial && !from_trigger_notify && b != s->previous_exists` for `PATH_CHANGED`/`PATH_MODIFIED`, and `path_trigger_notify_impl` re-checks with `from_trigger_notify=true`, so `PathChanged=/run/media/pcalnon` is a sound fix; the udev rule is an alternative, not a requirement."
11. **§1.2 Lane A product entry** "scan of `Duplicati.Server.Implementation.dll`" misses `startup-delay`/`usage-reporter-level` (`Duplicati.Library.RestAPI.dll`), `secret-provider*` (`Duplicati.Library.Main.dll`) and the tools' `--server-datafolder`. Replace with "a UTF-16 option-name scan of every `/usr/lib/duplicati/*.dll` (549 files, seconds)".
12. Design §7.3.2: "neither of which this design uses" → "none of which this design uses" (three alternatives now).
13. **§1.5 item 4**: `sudo` is unnecessary for `ls -la /usr/lib/systemd/system/`, and `.duplicati.service.swp` is world-readable (root 0644, 12 KiB, 01:45) — `grep -c ENCRYPTION` = 0 today. Append: "(the swap file is world-readable — 0 `ENCRYPTION` lines at 15:05 CDT; no `duplicati.service~`, no `duplicati.service.d/`; only root's history/viminfo need the owner)".
14. §4 "Branch … is opened … and … merged as" → "will be opened … and merged as" (§0 already says "To be merged").
15. §1.1 B3 transcript sentence: the count matches pattern MENTIONS (every validator's own `grep` command text counts — 48 now). Append "(an upper bound: the pattern also matches the validators' own command text)".
16. §1.1 D9 nit: "`-wal`/`-shm` appear" → "the header flips to WAL (the `-wal`/`-shm` pair exists only while the tool runs) and the sha256 changes".

### (3) Verdict

**Yes — round 2 changes dispositions, actions and numbers**, so by §1.2's own done-criterion this is not the terminating round: (i) disposition — B1 F12 vs B2 D5 settled for B1 from source (R9); (ii) disposition — D1's `PathChanged=` behaviour verified from `path.c`, udev becomes optional (R10); (iii) action — §1.4's throwaway-server test narrows to B3 O-2 only (R9); (iv) numbers — alias-only references 46 not 41–42 (R5); token-shaped lines in two subagent transcripts (1 + 3), not one (item 6); (v) fact — `--webservice-password-init` is a value-taking option (R8); (vi) actionability — candidate must be alone on the probe's stdin (R2); (vii) consistency — exception lists and the §4/§12 file list (R1, R7). No §0 number, no root-cause leg and no owner action other than the narrowed F12/D5 test changes.

### (4) Could not determine

- Whether `Utility.ReadSecretFromConsole` accepts a piped (non-tty) stdin — moot for the design. The three source fetches came back as tool-summarised excerpts, not raw files; the quoted lines are specific but I did not read the whole files.
- Whether `wipe-encryption` gates on the folder mode when no DB path is given (a 0775 folder was accepted with an explicit path).
- `/opt/miniforge3/envs` 62 G (not re-measured); `/proc/1397393`, `/usr/lib/duplicati/data/`, root/duplicati histories (no root, same as A1).
- The record's A1 summary row says "7 UNTRACEABLE items" while the report body has 8 bullets; the handoff's 8 is right (verbatim archive, not a handoff defect).
- Item 6's "scratch file (since regenerated)".
- MEMORY.md: 21,982 B / 80 lines at 14:39:47 CDT — matches the handoff's "22.0 KB"; the loader banner's 24.5 KB/101 lines is a different measurement I cannot reconcile.

Files read, none changed: the handoff (`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-21_backup-redesign-round-1-validated-reconciliation-pending.md`), the design (`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`), the round-1 record (`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`), and the two archived instruments under `util/ad-hoc/`.

<!-- markdownlint-enable -->

---

## Report H-R3 — round 3 (verification of round 2's sixteen fixes)

Briefed on round 2's sixteen fixes; confirmed all sixteen; found five leftovers (folded in — see the handoff's §6). Subagent id `aef247cd40118f898` (7,148 characters).

<!-- markdownlint-disable -->

## Round 3 — verification of round 2's sixteen fixes

Read-only throughout; scratch `…/scratchpad/hvalR3/` (the R16 copy was 0600 in a 0700 dir and deleted after the run). Handoff = `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-21_backup-redesign-round-1-validated-reconciliation-pending.md`; design = `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`. Both unchanged at 15:13/15:14 CDT.

### (1) Fix table

| R# | passage (§, short quote) | fixed? | true? (evidence) |
|---|---|---|---|
| R1 | handoff l.10 "applied so far, and nothing else: the §4.1 unit row; … (B2 D22)"; §1.1 intro l.57 "none is applied beyond the list in the opening paragraph" (pointer, cannot drift); design status l.6 and §11 l.1143 name the identical seven items | yes | yes — §12's last row lists the same set; the F11 remainder is still unapplied (design ll. 54/210 "8200 or not at all", l.285 "may refuse") |
| R2 | §1.4 "Feed the candidate ALONE on stdin … Expect `candidates loaded: ['ENV_ACTIVE_KEY', 'L', 'PASSPHRASE', 'PASSPHRASE_OLD']`" | yes | yes — probe ll. 113–115 overwrite `cands["ENV_ACTIVE_KEY"]` per matching line (last wins); argv = wrapper, credential file, `label=path`; worktree wrapper carries the marker (1 line → `L`); credential file has 2 passphrase lines, 1 `PASSPHRASE_OLD` (counts only) |
| R3 | §3 "Until the PR in §4 has merged, `git ls-remote origin main` will not equal the PR's `mergeCommit` … five file checks … pass only in a checkout carrying the branch" | yes | yes — `ls-remote` 739a233c vs `origin/main` 53bc8e00; all five pass here: ls, status line, 6, 5, linter `blocks: 12 failures: 0` |
| R4 | B3 paragraph l.149 "the orchestrator's addition from A1's §4.1 row, not a B3 finding" | yes | yes — round-1 record hits at l.83 (A1 row), 319, 377, 546; none after l.711 (B3); live `/etc/default/duplicati` is `duplicati:duplicati` 0644 |
| R5 | D22 l.124 and design §11 l.1146 "46 … 29/9/3/4/1" | yes | **no** — re-count today: unanchored `grep -o` 49 (29/9/4/5/2); anchored `§[0-9A-Z]` 44 (28/8/3/4/1). 46 reproduces under neither; see defect 2 |
| R6 | design §11 "the header's **Companions** list (alias → filename, in the same document)" | yes | yes — no "§0 alias"/"alias table" left in either file |
| R7 | §4 l.328 lists `…BACKUP-HANDOFF-CONSENSUS-RECORD.md` | yes | yes — file exists (69,965 B), holds H-A, H-B1, H-B2, H-R2 and an H-R3 placeholder |
| R8 | D5 ll. 113–115 "Password-type option … `AutogeneratedPassphrase`; exit 102 … 103 … CAN carry the value on argv … `--secret-provider` … or `--settings-file` … once by hand with the service stopped" | yes | **partly** — `Program.cs` at the tag: `ArgumentType.Password`, 102/103, `AutogeneratedPassphrase` ✔; but the server has **no `--settings-file`** (see defect 1) |
| R9 | F12 l.77, D5 l.115, cross-lane l.178 "SETTLED for B1 … `Connection.cs`"; §1.4 asks only B3 O-2 | yes | yes — `Connection.cs` at the tag: refresh token → DB-minted signin token → `ReadSecretFromConsole("Enter server password: ")` |
| R10 | D1 ll. 107–108 and §2 l.259 "verified at v259 `path.c`: no re-trigger … udev … an alternative" | yes | yes — v259 `path_spec_check_good`: `good = !initial && !from_trigger_notify && b != s->previous_exists`; `path_trigger_notify_impl` → `path_enter_waiting(p, false, true)`; host runs 259.5 |
| R11 | §1.2 "every `/usr/lib/duplicati/*.dll` (549 files …)" | yes | yes — 549; UTF-16 scan puts `webservice-password-init` in Server.Implementation only, `secret-provider` in Library.Main + Server.Implementation |
| R12 | design §7.3.2 "none of which this design uses" | yes | yes (l.359) |
| R13 | §1.5 item 4 "no sudo needed … root 0644 … 0 `ENCRYPTION` lines … no `duplicati.service~`, no `.d/`" | yes | yes — swp `-rw-r--r-- root:root` 12288 B; 0 `ENCRYPTION`, 0 `Environment=`, 1 `ExecStart` (positive control); directory holds only the swp and the unit |
| R14 | §4 l.319 "will be opened … merged as PR_NUMBER_PLACEHOLDER" | yes | consistent with §0 "To be merged" |
| R15 | B3 paragraph l.154 "48 by 15:05 — an upper bound, since the pattern also matches the validators' own command text" | yes | yes — transcript exists (0600, 11 MB); `Failed to resolve specifiers` count 52 now (my own command text included) |
| R16 | D9 ll. 117–118 "the header flips to WAL — the `-wal`/`-shm` pair exists only while the tool runs — and the sha256 changes" | yes | yes — scratch copy: sha `8ea9eba9…` → `423695da…`, header bytes 18/19 `1 1` → `2 2`, no `-wal`/`-shm`/`.bak` after rc 0 (round 2's exact hashes reproduced) |

### (2) New defects introduced by the fixes

1. **R8 names a channel the server does not have.** `--settings-file` is `duplicati-server-util`'s persisted-settings JSON (`ServerUtil/Settings.cs`: `RefreshToken`, `HostUrl`); the server's `Program.cs` has "no occurrence of settings-file" and reads `--parameters-file` (`PARAMETERS_FILE_OPTION`) — order in `Main`: secret provider → parameters file → init-password check. Replace in handoff l.114: "…must be fed through `--secret-provider` (a `$name` placeholder) or `--parameters-file` — the server applies both before it reads the init value; `--settings-file` is `duplicati-server-util`'s refresh-token store, not a server option — and run once by hand…".
2. **The count of short-form references is 44, not 46.** Anchored count (`grep -o -E '(YAM|PLAN|CON|DMG|GPG) §[0-9A-Z]'`): 28 `YAM §`, 8 `PLAN §`, 3 `CON §`, 4 `DMG §`, 1 `GPG §`. The unanchored count is 49 because §11's own count sentence quotes all five pattern names; 46 was that unanchored count taken when the sentence quoted three of them and §11 held one fewer real `CON §` reference. Replace at handoff l.124, l.401 and design l.1146: "(44 by an anchored `grep -o` — 28 `YAM §`, 8 `PLAN §`, 3 `CON §`, 4 `DMG §`, 1 `GPG §`; a count that is not anchored on a section id also counts the pattern names quoted in this sentence)".
3. **§0 l.47** "the design, the two record files, this handoff and the six … instruments" contradicts §4/R7. Replace: "the design, the three record files, this handoff and the six…".
4. **§3 l.298** comment "# design + 2 record files" — the glob now lists four files. Replace: "# design + 3 record files".
5. **§6 l.399** "stale 'what is applied' lists in three places" — round 2's regression 1 named four passages. Replace: "in four places".

### (3) Verdict

**Yes.** Numbers: 46 → 44 (three sites), "three places" → four, "two record files" → three. Action/mechanism: the init-password file channel is `--parameters-file`, not `--settings-file`. No disposition changes; no §0 fact, root-cause leg or owner action changes.

### (4) Could not determine

- Whether the `.env`'s three commented key spellings (`ENV_C_KEY_1..3`) were ever fed to the probe — no archived `candidates loaded` line names them (records show only `ENV_ACTIVE_KEY`), so R2's "already excluded" clause rests on §0's exclusion of the literal and passphrase, not on a recorded run.
- The `-wal`/`-shm` pair during the tool's run (only its absence afterwards was observed).
- The exact §11 text at round-2 time; the 46 reconstruction above is inference, the 44 measurement is not.

<!-- markdownlint-enable -->
