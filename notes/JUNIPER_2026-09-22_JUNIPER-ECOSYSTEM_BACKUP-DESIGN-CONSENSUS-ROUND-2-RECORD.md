# Backup design — consensus rounds 2 and 3, verbatim validator reports

**Project**: Juniper (workstation backup infrastructure, host `yamaguchi`)
**Author**: Paul Calnon
**Date**: 2026-09-22
**Procedure**: [`JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
**Artifact validated**: [`JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`](JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md)
**Round 1's reports**: [`JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`](JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md)

---

## What round 2 was for

Round 1's six lanes produced 13 + 15 + 12 + 17 + 32 + 20 findings. Lane A2's and A3's were
applied on 2026-09-21; the owner then paused the arc, and the remaining four lanes — A1, B1, B2
and B3 — were reconciled into the design on **2026-09-22** by
`util/ad-hoc/2026-09-22_reconcile_backup_design.py`.

Round 2 validated **that reconciliation**, not the original design. Four lanes, briefed only on
the change list and the recorded dissent, none seeing another's output:

| Lane | Entry point | Subagent |
| --- | --- | --- |
| A (host) | the live host only — systemd, the journal, `/var/log/syslog*` (counts only), filesystems, database copies | `aca4c9c3589d7ad83` |
| A (product) | Duplicati 2.4.0.0 as installed: `help` output and the option names present in the shipped assemblies | `a20bd5a975a5286ed` |
| B (actionability) | the reconciled §8 runbook, worked as a literal script | `a94c48d0a6519a0e0` |
| B (security) | what reconciliation added — P0.5, the §7.3.2 confinement set, the §7.3.1 trust tables, §6's S-7/S-8 and sink checklist, the §7.5 guard | `a5c54dfa185827c76` |

**Round 3** is a single-agent confirmation pass over round 2's edit set, reading a **frozen** document. It
confirmed 13 of the 20 corrections outright, found 6 present-but-incomplete, and swept every internal
cross-reference — 15 defects, all applied. Its sharpest finding was the one round 2 created: the
P0.5a/P0.5b split had been made by *adding headings* rather than by relocating content, so the re-key
procedure was still printed in full inside the list headed "before anything in P0" — the exact ordering
error the split exists to prevent. Its report is archived here too (`a84d1b8fcbaed0754`).

It earned its place. Round 2 found that the reconciliation had introduced defects of its own,
several of them in the exact areas round 1 had just corrected — the most consequential being
that **both Procedure A0 scripts could not run**, because they `.`-sourced a credential file
whose value is unquoted and carries `$ & @ # ^`, so `set -u` aborted them *and echoed a
fragment of the live passphrase to stderr*: the very channel §6 exists to close. The full list
is in §11 of the design.

## A procedure failure, recorded

The orchestrator applied corrections to the design **while two lanes were still reading it**.
The security lane saw it at three different sizes between 02:31 and 02:47 and handled it
correctly — it pinned a sha256 snapshot, anchored every citation by heading text, and reported
two of its own intended findings as AGREE-with-corroboration rather than claiming them, because
a concurrent edit had already closed them.

Two consequences stand, and they qualify everything below: **any line number in these reports is
void**, and a finding may be stale in either direction. Where a report disagrees with the design
as it now stands, the design was re-measured against the host before the disagreement was
resolved. The right fix is procedural, and the consensus procedure should say it: **freeze the
artifact for the duration of a round.** Round 1 did not hit this only because the owner paused
the arc before reconciliation began.

## Secrets screen

Each report was screened before archiving with
`util/ad-hoc/2026-09-22_archive_consensus_reports.py`, whose filter is tuned to the shape of
this arc's secrets (30–40 characters containing one of `* @ $ %`) rather than to generic
entropy — that character class is what the repository's own gitleaks rule provably misses (round
1, Lane B3 finding 11), and a generic screen buries a real hit in hundreds of hyphenated English
compounds. No secret value appears in any report. That is a claim about *these* secrets' shape,
not a general clean bill.

---

## Report A (host) — measurement re-creation; entry point: the LIVE HOST only

Subagent id `aca4c9c3589d7ad83` (45,542 characters). Archived verbatim.

<!-- markdownlint-disable -->

# Consensus round 2 — Lane A1 (measurement re-creation), LIVE HOST ONLY

**Agent**: round-2 Lane A1. **Host**: `yamaguchi`. **Measured**: 2026-09-22, 02:32–02:41 CDT (07:32–07:41 UTC).
**Document under review**: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`
(worktree `.claude/worktrees/buzzing-painting-meteor`).
**Brief**: `ROUND2_BRIEF.md` (round-2 consensus brief, scratchpad copy).
**Handoff whose §3 was re-run**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-21_backup-redesign-round-1-validated-reconciliation-pending.md`.

Scope obeyed: read-only on the host; the service was never stopped, started, reloaded or probed; nothing was
written under `/mnt/Backups/Ubuntu/`; no SQLite database was opened; `duplicati-server --version` was never
run; no secret value appears below. Scripts live in
`/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/1f771cb0-1009-4763-8a32-16517ac8b4b5/scratchpad/r2_A_host/`.
Nothing was written into the repository (`git status --porcelain` shows only the two entries that were already
present at session start).

---

## 0. THE TWO THINGS TO READ FIRST

### 0.1 **Both `su - duplicati` shells are STILL ALIVE. So is the `vim` on the unit file.** (time-critical)

```
$ ps -eo pid,ppid,user,lstart,etime,args | grep -Ei 'su .*duplicati|vim'
2318515 2978589 root     Mon Sep 21 01:41:41 2026  1-00:50:58 vim /usr/lib/systemd/system/duplicati.service
3065637 2979549 root     Sat Sep 19 18:24:50 2026  2-08:07:49 su - duplicati
3117156 3019332 root     Sat Sep 19 18:52:00 2026  2-07:40:40 su - duplicati

$ ps -o pid,ppid,user,lstart,etime,stat,args -p 3065639
3065639 3065637 duplica+ Sat Sep 19 18:24:50 2026  2-08:07:49 S+   -bash
$ ps -o pid,ppid,user,lstart,etime,stat,args -p 3117158
3117158 3117156 duplica+ Sat Sep 19 18:52:00 2026  2-07:40:39 S+   -bash
```

Design §6 sink-checklist row 1 (pids **3065639**, **3117158**, started 09-19 18:24:50 / 18:52:00) — **AGREE, and
still live 2 days 8 h later.** `/home/duplicati/.bash_history` is still `0600 duplicati:duplicati`, 310 B,
mtime **2026-09-19 18:51:58** — i.e. every command of the 09-20 migration is still only in memory and will be
appended on exit. The owner action (`history -c; unset HISTFILE` in each shell before it exits) is still
available and still unperformed. The `vim` (pid 2318515, root) on `/usr/lib/systemd/system/duplicati.service`
is also still open — §4.1 note (a) AGREE — and its swap file is still there.

### 0.2 **Today's 13:45 UTC snapshot has NOT fired yet. The recovery source is intact for another ~6 hours.**

```
$ systemctl list-timers yamaguchi-server-db-snapshot.timer --all --no-pager
NEXT                        LEFT LAST                         PASSED UNIT
Tue 2026-09-22 08:45:00 CDT   6h Mon 2026-09-21 08:45:00 CDT 17h ago yamaguchi-server-db-snapshot.timer

$ stat ~/.local/state/duplicati-server-db/Duplicati-server.sqlite
  size: 245760   Inode: 4609661     Links: 1
Access: (0600/-rw-------)  Uid: ( 1000/ pcalnon)   Gid: ( 1000/ pcalnon)
Modify: 2026-09-21 08:45:00.971726126 -0500
 Birth: 2026-09-21 08:45:00.907725979 -0500
```

Inode **4609661**, born 09-21 08:45:00, is the same one the design's P0 evidence freeze is meant to copy aside.
It will be replaced at **2026-09-22 08:45:00 CDT (13:45 UTC)**, ~6 h 12 m after this measurement. §4.1's
"replaced every day at 13:45 UTC with a new inode: copy it aside before P0" — **AGREE, and the deadline is
today at 08:45 CDT.**

---

## 1. §3 starting-state block — re-run

| Claim (handoff §3) | Verdict | Evidence |
| --- | --- | --- |
| `MainPID=1397393` unchanged | **AGREE** | `systemctl show duplicati.service …` → `MainPID=1397393` |
| `NRestarts=0` | **AGREE** | `NRestarts=0` |
| `NeedDaemonReload=no` | **AGREE** | `NeedDaemonReload=no` |
| `ActiveState=active`, `User=duplicati` | **AGREE** | `ActiveState=active`, `SubState=running`, `User=duplicati` |
| start time 09-20 18:19:42 | **AGREE** | `ExecMainStartTimestamp=Sun 2026-09-20 18:19:42 CDT` |
| port **8300 only** | **AGREE** | `ss -tln \| grep -E ':8200\|:8300'` → `LISTEN 0 512 127.0.0.1:8300` and `[::1]:8300`; nothing on 8200 |
| 13:45 UTC snapshot fired today, new inode | **DISAGREE — has not fired** | see §0.2 |
| newest fileset `duplicati-20260918T140000Z` | **AGREE** | `ls -t …/Yamaguchi/ \| head -1` → `duplicati-20260918T140000Z.dlist.zip.aes`; 9 dlists total, oldest `20260825T102739Z` |
| watchdog tail `UNREACHABLE`/401 | **AGREE** | `2026-09-21T12:00:39-0500 ALERT UNREACHABLE backup=2 login failed: FATAL: login failed (401)` — still the last line; next watchdog fire 2026-09-22 12:00 CDT, `Linger=yes` |

Additional, unchanged: `FragmentPath=/usr/lib/systemd/system/duplicati.service`, `Restart=always`, and
`/etc/systemd/system/duplicati.service.d/` **does not exist** (no drop-in) — §4.1's "vendor unit, edited in
place; no drop-in" AGREE. The unit file itself: `mode=644 root:root size=461 mtime=2026-09-21 01:44:57.196855038
birth=2026-09-21 01:44:57.196855038` — **AGREE** with "edited in place 09-21 01:44:57" (birth == mtime, so the
file was replaced, i.e. `vim`'s write-out, not an in-place patch).

The armed `ExecStart` is present and loaded:

```
$ cat -n /usr/lib/systemd/system/duplicati.service      (values masked; none present on these lines)
    13  # ExecStart=/usr/bin/duplicati-server $DAEMON_OPTS
    14  # ExecStart=/home/duplicati/bin/duplicati-wrapper.bash "${DAEMON_OPTS}"
    15  ExecStart=/home/duplicati/bin/duplicati-wrapper.bash '--daemon-opts="${DAEMON_OPTS}"'
    17  Restart=always
```

The *running* process still predates it:

```
$ tr '\0' '\n' < /proc/1397393/cmdline | cat -A
/usr/lib/duplicati/duplicati-server$
--webservice-port=8300 $
```

One argv element, `--webservice-port=8300` **with a trailing space** — §4.1's `"--webservice-port=8300 "`
**AGREE**, trailing space and all.

**New detail on §4.1 note (a).** The 03:23:44 reload is real, but it was *not* an operator action:

```
$ journalctl … | grep 'Reload requested'
2026-09-21T03:23:44-05:00 yamaguchi systemd[1]: Reload requested from client PID 2481512 ('systemctl') (unit snapd.service)...
```

Every `daemon-reload` after the 01:44:57 unit edit was requested by **`snapd.service`** (03:23:44, 10:53:47,
14:43:48, 20:43:55 on 09-21). The last operator-scoped reload was 09-20 16:41:03 (`unit session-c7.scope`).
So the armed `ExecStart` became the loaded one *by accident*, via snapd's routine reload — which strengthens,
rather than weakens, the point note (a) makes.

---

## 2. §4.1 rows and notes a–d

| Claim | Verdict | Evidence |
| --- | --- | --- |
| **1,443** regular files under `/usr/lib/duplicati`, all `root:root` | **AGREE** (scope caveat below) | `find /usr/lib/duplicati -type f \| wc -l` → `1443`; `… -user root -group root \| wc -l` → `1443`; `… ! \( -user root -group root \) \| wc -l` → `0` |
| **97** duplicati-owned directories | **AGREE as a count** | `find /usr/lib/duplicati -type d -user duplicati \| wc -l` → `97` |
| "`/usr/lib/duplicati` and **every directory beneath it** (97) were chowned" | **DISAGREE** | `find /usr/lib/duplicati -type d \| wc -l` → `118`; `… ! -user duplicati \| wc -l` → **`21`** (see §5, D-1) |
| `/usr/lib/duplicati` itself `duplicati:duplicati 0755`, **no sticky bit** | **AGREE** | `stat -c '%n %04a %U:%G'` → `/usr/lib/duplicati 0755 duplicati:duplicati` |
| `/usr/bin/duplicati-*` are symlinks into it; `webroot/` writable the same way (note b) | **AGREE** | 15 symlinks `-> ../lib/duplicati/duplicati-*`; `webroot 0755 duplicati:duplicati` |
| `/usr/lib/duplicati/data` `0700`, now `duplicati`-owned | **AGREE** | `mode=700 owner=duplicati:duplicati mtime=2026-09-18 21:03:34.671948331 ctime=2026-09-19 19:15:00.938495305 birth=2026-08-25 02:38:43` |
| data folder `/home/duplicati/.config/Duplicati/` directory **0777** | **AGREE** | `stat -c '%04a'` → `0777`, no sticky |
| "files 0777" true of **the four DB files + the crashlog only** | **AGREE, exactly** | `0777`: `Duplicati-server.backup`, `Duplicati-server.sqlite`, `-shm`, `-wal`, `Duplicati.GUI.TrayIcon-crashlog.txt`. Nothing else is 0777. |
| `.env` **0660**, 1,599 B | **AGREE** | `-rw-rw---- 1 duplicati duplicati 1599 2026-09-20 16:39:43` |
| `installation.txt` / `machineid.txt` **0664** | **AGREE** | `664 duplicati:duplicati 285` / `664 … 247` |
| subdirectories **0775** | **AGREE** (row omits one) | `backups 775`, `control_dir_v2 775`, **`temp1 775`** — `temp1/` is not named in the row |
| `temp/` root-owned **0755** | **AGREE** | `755 root:root`, holds the 112,587,272-byte `Duplicati-server.sqlite-wal` |
| `/etc/default/duplicati` **`duplicati:duplicati` 0644** | **AGREE** | `-rw-r--r-- 1 duplicati duplicati 404 …`; content: one active `DAEMON_OPTS="--webservice-port=8300"` plus three commented variants (incl. the `--portable-mode` one) |
| `.dropbox-dist` = 270.4.3312, `duplicati:duplicati`, birth 09-15 15:26:22, mtime 09-14 20:49:31, ctime 09-18 20:30:49 | **AGREE, all four** | `stat` → `mode=775 owner=duplicati:duplicati birth=2026-09-15 15:26:22.039963688 mtime=2026-09-14 20:49:31 ctime=2026-09-18 20:30:49.987214439`; `cat VERSION` → `270.4.3312`; sole tree `dropbox-lnx.x86_64-270.4.3312` |
| "The running daemons are pcalnon's" | **AGREE** | `2948130 pcalnon … /home/pcalnon/.dropbox-dist/dropbox-lnx.x86_64-270.4.3312/dropbox` (+ one defunct child 2949543) |
| Dropbox daemon runs **without gid 139** | **AGREE** | `/proc/2948130/status` → `Groups: 4 24 27 30 46 100 114 128 984 993 1000 1003` — no 139; `getent group duplicati` → `duplicati:x:139:pcalnon,duplicati` |
| `/home/duplicati` **0755**, created **2026-09-18 19:31:40** | **AGREE** | `mode=755 owner=duplicati:duplicati birth=2026-09-18 19:31:40.229397506` |
| `bin/` **0777**, holds the live wrapper symlink | **AGREE** | `drwxrwxrwx`, `duplicati-wrapper.bash -> /home/pcalnon/Development/python/Juniper/juniper-ml/scripts/duplicati-wrapper.bash`, symlink created 2026-09-20 16:53:58 |
| snapshot unit `ExecStart` runs the **primary checkout's** script **as root** (note c) | **AGREE** | `FragmentPath=/etc/systemd/system/yamaguchi-server-db-snapshot.service`; `ExecStart={ … argv[]=/usr/bin/python3 /home/pcalnon/Development/python/Juniper/juniper-ml/util/ad-hoc/yamaguchi_server_db_snapshot.py … }`; **`User=`** (empty ⇒ root) |
| note (c): `sys.path[0]` is pcalnon-writable | **AGREE** | `util/ad-hoc` → `mode=775 owner=pcalnon:pcalnon`; the script itself `775 pcalnon:pcalnon`. `cat …/juniper-ml/.git/HEAD` → `ref: refs/heads/main` |
| pcalnon profile `0700`; 56 GiB under `backups/`; `installation.txt` rewritten 09-20 18:10:32 | **AGREE** | `mode=700 pcalnon:pcalnon`; `du -sh` → `56G`; `installation.txt` mtime `2026-09-20 18:10:32.971578344` |
| destination: 877 files / 203 G, all `pcalnon:duplicati 0770`, no setgid | **AGREE** | `find -type f \| wc -l` → `877`; `du -sh` → `203G`; mode histogram → `877  770 pcalnon:duplicati`; `stat -c '%04a'` on the five ancestors → all `0770` (no `2`) |
| tar lane: no timer, path unit, cron or udev rule; neither drive attached | **AGREE** | no `juniper-backup.*` in `~/.config/systemd/user/`; `crontab -l` shows only two clamtk jobs; no udev rule matches `EBC5-F0A3`/`DFF3-2782`; `findmnt` shows no mount under `/media` or `/run/media` |
| disabled CLI lane | **AGREE** | `systemctl --user is-enabled duplicati-backup.timer` → `disabled`; `last-run.status` → `result=FAILED when=2026-08-25T05:13:35-05:00 reason=duplicati-cli rc=143` |
| note (a): live server's last journal lines 18:47:44 / 18:51:33 **"×4 each"** | **DISAGREE** | ×2 each, 4 lines total (see §5, D-2) |
| note (d) / §4.1 closing: `ls` `+` is the Dropbox xattr, not an ACL | **AGREE, and it generalises** | `getfacl -p …/_yamaguchi_keys/env` → base entries only (`user::rwx group::rwx other::---`); `getfattr -d` → `user.com.dropbox.attrs=0s…` |

**Scope caveat on the 1,443.** `find` as `pcalnon` cannot descend into `/usr/lib/duplicati/data` (0700
`duplicati`, and this login's process credentials lack gid 139 — see §7). The single error emitted was
`bfs: error: /usr/lib/duplicati/data: Permission denied.` So **1,443 is the file count of the tree *outside*
`data/`**, and the sentence "all 1,443 regular files … are still `root:root`" is true of exactly that set.
It is not a claim about the whole tree. That is a precision point, not a defect — the load-bearing half
(the binaries are still `root:root`) holds.

---

## 3. §4.2 — the six numbered notes

### Note 1 — the 21:03:34 relabel: **AGREE**

```
$ stat -c '%n mtime=%y ctime=%z' /usr/lib/duplicati/data
/usr/lib/duplicati/data mtime=2026-09-18 21:03:34.671948331 -0500 ctime=2026-09-19 19:15:00.938495305 -0500
```

Seven seconds after the 21:03:27 start ✓. The mtime has never moved since ✓ (the later ctime is the 09-19
chown, which does not touch mtime). The bracket holds from the journal:

```
2026-09-18T21:03:27 systemd[1]: Started duplicati.service - Duplicati web-server.
2026-09-18T21:03:30 duplicati-server[522433]: Server has started and is listening on localhost, port 8300
2026-09-18T21:08:06 duplicati-server[529093]: … SettingsEncryptionKeyMismatchException: Encryption key used t…
```

No `No database encryption key was found` line falls between 20:42:38 and 21:16:18 — so the 21:03:27 start
carried a key and emitted no warning. **AGREE** with "bracketed 21:03:27–21:08:06".

### Note 2 — 23 `Invalid slot` = 22 + 1; 5 on 09-18, 18 on 09-19: **AGREE, exactly — and the instrument matters**

Full journal (`journalctl --no-pager -o short-iso --since '2026-09-17'`, no `-u`):

```
Invalid slot total                       = 23
  of which 'Failed to resolve specifiers'      = 22
  of which 'Failed to resolve unit specifiers' =  1
by date:   5  2026-09-18      18  2026-09-19
```

Unit line numbers, 09-18 (value redacted):

```
21:15:40  …/duplicati.service:11        21:16:10  …/duplicati.service:11
21:17:54  …/duplicati.service:10        21:23:25  …/duplicati.service:12   ← the "unit specifiers" one
21:29:51  …/duplicati.service:10
```

09-19 (all at line **10**): `05:53:43, :45, :48, :51` (×4); `17:46:13, :21, :23` (×3);
`18:06:53, 18:06:56, 18:07:00, :04, :06, :10, :13, :15, :20, :23, :32` (**×11**).

Every figure in note 2 — the split, the dates, the four 09-18 line numbers, the three 09-19 clusters and
their multiplicities, and the terminal 18:07:32 — reproduces **exactly**.

**The recorded dissent is now explained mechanically, not just attributed.** The *same* grep, scoped with
`-u duplicati.service`, returns **22**:

```
$ journalctl -u duplicati.service … | grep -c 'Invalid slot'     → 22
$ comm -23 <full timestamps> <unit-scoped timestamps>            → 2026-09-19T18:07:32-05:00
```

Exactly one line — the last one, 18:07:32 — is dropped by the unit filter (systemd emitted it before the
reloaded unit was associated). So A1's 23 and B1's 21/22 are the same event set read through filters of
different width. The design's choice of 23 is the complete one. **AGREE with the dissent as recorded.**

### Note 3 — 24 failed starts on 09-19, split 5 / 5 / 14: **AGREE**

Raw line counts double every .NET error, because journald tags the same text under two identifiers
(`duplicati-server[pid]` and `wrapper.bash[pid]`). Counting **starts** (distinct pid) resolves it:

| Message | Lines | **Distinct pids (= starts)** | Times |
| --- | --- | --- | --- |
| `The database has version 19 but the largest supported version is 11` | 10 | **5** | 20:48:12–20:48:16 |
| `Access to the path '/home/duplicati/.config/Duplicati/Duplicati-server.sqlite' is denied` | 10 | **5** | 21:41:04–21:41:08 |
| `… largest supported version is 12` | 28 | **14** | 21:43 (4), 21:52 (5), 21:55 (5) |

5 + 5 + 14 = **24** ✓, and the 14 fall at 21:43 / 21:52 / 21:55 exactly as the note says. The "20 starts die
with `wrapper.bash: line 30: --webservice-port=8300: command not found`" row is also confirmed: **20 lines,
20 distinct pids**, at 19:19:55–56 (5), 20:39:31–32 (5), 20:39:43–44 (5), 20:44:36–37 (5) — a bash message, so
it is emitted once per start, not twice. The `20:48:12` line does carry the identifier `wrapper.bash` ✓.

### Note 4 — the profile copy came in **three waves**: **AGREE**

Inode birth times in `/home/duplicati/.config/Duplicati/`:

| Wave | Birth | Entries |
| --- | --- | --- |
| 1 | 09-19 **18:40:36** – **18:42:22** | `backups/` 18:40:36.682921314, `control_dir_v2/` 18:42:18.617369320, crashlog 18:42:18.800370112, `machineid.txt` 18:42:22.361385502 |
| 2 | 09-19 **21:57:36** | `Duplicati-server.sqlite` (the 4 KB stub) 21:57:36.085194666 |
| 3 | 09-20 **04:15:42** – **04:43:02** | `installation.txt` 04:15:42.068221220, `Duplicati-server.backup` 04:41:07.682130941, `-shm` 04:43:02.657697057 |

Each wave's membership matches the note verbatim. The note's inference also holds: the stub born 21:57:36 is
**later** than the 21:41 `is denied` failures, so the file denied at 21:41 was a different, earlier inode ✓.
(The `-wal` is born 09-20 18:19:43.917937740 — created by the live server, not copied; the 112 MB WAL now sits
in `temp/`, mtime 2026-08-25 02:20:46.)

### Note 5 — five `KeyMissing` starts of the **older** `wrapper.bash`: **AGREE on count and identifier; WEAKENED on "at 13:32:34"**

```
distinct pids with SettingsEncryptionKeyMissingException at 13:32:3x:
  [979072] [979142] [979159] [979176] [979194]          → 5
each preceded by:  wrapper.bash[<pid>]: /home/duplicati/bin/wrapper.bash: line 38: /home/duplicati/.config/.env: No such file or directory
```

Five starts ✓, all under identifier `wrapper.bash` (the *older* file, which reads `/home/duplicati/.config/.env`
at line 38), versus the successor `duplicati-wrapper.bash` ✓. Two wrapper files in play ✓.

But they were **started** at 13:32:33, :34, :35, :36, :37 and **died** at 13:32:34, :35, :36, :37, :38 — they
do not all sit at 13:32:34. Only the first does, which is what makes "sixteen seconds before 13:32:50" true.
See §5, W-1.

Also confirmed here, and worth recording because §4.2's row and §5.6 use two different timestamps for the same
start: **13:32:46** is the systemd `Started` + wrapper echo (`duplicati-wrapper.bash[979620]`, `Input
Parameters: --webservice-port=8300 --portable-mode`), and **13:32:50** is that same pid's `Server has started …
port 8200`. Both are right; they are different lines of one start. The 13:36:37 start (pid 985421) echoes
`--webservice-port=8300` with **no** `--portable-mode` and reaches port 8300 at 13:36:40 ✓ — §4.2's row is
correct as written.

### Note 6 — window vs day: **AGREE, every figure**

Full journal, 2026-09-20:

| Pattern | Window 16:40–16:46 | Day total |
| --- | --- | --- |
| `LINE: "` | **220** | **264** |
| `LINE: "# export …` (commented-out assignment) | **50** | **60** |
| `Exporting Environment Variable` | **10** | **12** |
| `Settings Encryption Key:` | **10** | **12** |

Per-minute echo distribution: `110 @ 16:41`, `110 @ 16:44`, `22 @ 16:50`, `22 @ 17:30` ✓ exactly as the note
describes. Distinct pids that echoed `LINE:` on 09-20 = **12** ✓ ("12 passes"). `Settings Encryption Key:`
timestamps: five in 16:41:15–16:41:20, five in 16:44:28–16:44:33, one at 16:50:12, one at 17:30:14 = 12 ✓.

§6's S-3 decomposition also reproduces: 60 commented `# export` lines = `PASSPHRASE=` **12** + `PASSPHRASE_OLD=`
**12** + `SETTINGS_ENCRYPTION_KEY=` **36** ✓ (total `SETTINGS_ENCRYPTION_KEY=` occurrences that day, active and
commented, = 76).

---

## 4. §5.5 — the ctime datings

**AGREE, to the nanosecond.**

```
$ find /home/duplicati/.config/Duplicati -maxdepth 1 -printf '%m %-4y %C… ctime | %p\n'
777 f  2026-09-20 18:25:47.326269 ctime | …/Duplicati.GUI.TrayIcon-crashlog.txt
777 f  2026-09-20 18:25:47.326269 ctime | …/Duplicati-server.backup
777 f  2026-09-20 18:25:47.326269 ctime | …/Duplicati-server.sqlite
777 d  2026-09-20 18:33:45.057912 ctime | /home/duplicati/.config/Duplicati
660 f  2026-09-20 16:39:43.794396 ctime | …/.env
775 d  2026-09-19 21:56:55.290575 ctime | …/backups
664 f  2026-09-20 18:11:59.937995 ctime | …/installation.txt
```

- **Three files at 18:25:47.326269604** ✓ (crashlog, `.backup`, `.sqlite` — a single `chmod` invocation).
- **Directory at 18:33:45.057912331** ✓, eight minutes later.
- **Not a recursive chmod** ✓: `.env` (16:39:43), `backups/` (09-19 21:56:55) and `installation.txt`
  (18:11:59) were untouched by either event — exactly the three the design names.
- **The 18:19:42 start therefore passed the gate** ✓. Both loosenings postdate it, and the start is
  independently confirmed successful (`18:19:46 duplicati-wrapper.bash[1397393]: Server has started … port
  8300`). The directory's mtime is 18:19:43.917937740 — identical to the `-wal` birth — and its ctime is
  *later* than that mtime, so the 18:33:45 metadata change created no entry; it was a pure `chmod`/`chown`.
  The "will refuse, not may" conclusion stands on measured ground.

---

## 5. §6 — the rsyslog second copy

| Claim | Verdict | Evidence |
| --- | --- | --- |
| `systemctl is-active rsyslog` | **AGREE** | `active` (and `enabled`) |
| `ForwardToSyslog=yes` in `/usr/lib/systemd/journald.conf.d/syslog.conf` | **AGREE** | file is `-rw-r--r-- root root 177`; `[Journal]` / `ForwardToSyslog=yes` |
| `syslog:adm` **0640** | **AGREE** | every `/var/log/syslog*` is `-rw-r----- 1 syslog adm` |
| `pcalnon` is in `adm` | **AGREE** | `id pcalnon` → `…,4(adm),27(sudo),128(libvirt),993(kvm),1003(docker),139(duplicati)`; `/var/run/docker.sock` is `srw-rw---- root docker`, docker `active` — §6's root-equivalence preamble AGREE in full |
| the secret-bearing day file carries **264 / 12 / 12 / 12** | **AGREE** | see table below |
| logrotate keeps day files **~10 days** | **AGREE** | `/etc/logrotate.d/rsyslog`: `rotate 10`, `daily`, `compress`, `delaycompress` |
| `syslog-20260919.gz` and `syslog-20260920.gz` carry **4 and 18** | **DISAGREE as used in S-1** | see D-3 |
| **five** `signin.html?token=` URLs | **AGREE** | 3 in `syslog-20260921.gz` + 2 in `syslog-20260920.gz` = 5; journal timestamps are exactly the five the design names: 09-19 21:20:41, 21:57:41; 09-20 13:32:50, 13:36:40, 18:19:46 |

Per-file counts (count-only; no matching line was printed):

```
FILE                           LINE:"  SettKey:  ExportEV  PASSPHR=  specifier  signin   InvalidSlot
syslog                              0         0         0         0          0       0        0
syslog-20260922                     0         0         0         0          0       0        0
syslog-20260921.gz                264        12        12        12          0       3        0
syslog-20260920.gz                  0         0         0         0         18       2       18
syslog-20260919.gz                  0         0         0         0          4       0        5
syslog-20260918.gz                  0         0         0         0          0       0        0
```

`syslog-20260921.gz` = 264 / 12 / 12 / 12, **identical to the journal's day totals** ✓ — the design's core
claim that the journal exposure has a complete second copy is confirmed exactly.

Sink-checklist rows I could measure without root:

| Sink | Claim | Verdict | Evidence |
| --- | --- | --- | --- |
| `/home/duplicati/.viminfo` | 14.7 KB, mtime 09-20 17:59 | **AGREE** | `size=14744 mode=600 owner=duplicati:duplicati mtime=2026-09-20 17:59:47.492305426` |
| `/usr/lib/systemd/system/.duplicati.service.swp` | root-owned but **0644**, 0 `ENCRYPTION` lines | **AGREE** | `-rw-r--r-- 1 root root 12288 2026-09-21 01:45:10`; `grep -ac ENCRYPTION` → `0` |
| World-readable DB copies: `Duplicati-server.backup` **0777**, `backups/*pre-dbpath-fix.sqlite` **0644** | **AGREE on modes; the row needs its paths** | see W-4 |
| Claude transcripts, cloud-linked | **AGREE** | `~/.claude/projects` is `0700 pcalnon:pcalnon`, **809** `.jsonl` files; files containing `Settings Encryption Key:` = **20**, `Exporting Environment Variable` = **18**, `PASSPHRASE=` = **71**, `Invalid slot` = **26**, `signin.html?token=` = **26**. A *file* count is a firmer unit than a line count; it is still an upper bound, since `PASSPHRASE=` matches valueless mentions too |
| Root's `~/.bash_history`, `~/.viminfo` | unreadable without root | **AGREE** | see §8 |
| CUPS spool | retention unknown | **AGREE — still unknown** | `/etc/cups/cupsd.conf`: Permission denied; `/var/spool/cups`: Permission denied |

Other §6 rows re-measured:

| Row | Claim | Verdict | Evidence |
| --- | --- | --- | --- |
| **S-4** | escrow `env` `-rwxrwx--- pcalnon:duplicati`, 388 B | **AGREE** | `mode=770 owner=pcalnon:duplicati size=388`, dir `_yamaguchi_keys` `770 pcalnon:duplicati`. Note it is group **rwx**, i.e. the service user can write and delete it, not merely read |
| **S-5** | primary `.env` **0664**, **0** `PASSPHRASE=`, `DUPLICATI_WEB_CREDENTIAL` + **12 other** names, several Slack | **AGREE, exactly** | `mode=664 pcalnon:pcalnon size=1024`; `grep -c 'PASSPHRASE='` → `0`; **13** distinct assignment names, of which 9 are `SLACK_*`; `DUPLICATI_WEB_CREDENTIAL` present ⇒ "twelve other" ✓ |
| **S-7** | `curious-plotting-hummingbird/.env`, 114 B, **0664**, 2026-08-23, **both** passphrases | **AGREE** | `mode=664 pcalnon:pcalnon size=114 mtime=2026-08-23 18:59:53`; exactly two assignment names: `PASSPHRASE`, `PASSPHRASE_OLD` |

---

## 6. §7.8 — `/run/media/pcalnon` and the systemd version

```
$ ls -la /run/media
drwxr-x---+ 2 root root   40 Sep 16 11:55 pcalnon
$ stat -c '%n mode=%a owner=%U:%G' /run/media/pcalnon
/run/media/pcalnon mode=750 owner=root:root
$ getfacl -p /run/media/pcalnon
user::rwx
user:pcalnon:r-x
group::r-x
mask::r-x
other::---
$ ls -A /run/media/pcalnon | wc -l
0
$ findmnt -rn -o TARGET,FSTYPE /run
/run tmpfs
$ systemctl --version | head -1
systemd 259 (259.5-0ubuntu3.4)
```

- **It exists**, is **`0750 root:root`** with a **named ACL entry `user:pcalnon:r-x`**, and is **empty**.
  **AGREE** with §7.8's premise. The r-x is exactly what a `pcalnon` user unit needs to place an inotify
  watch, so `PathChanged=/run/media/pcalnon` in a `--user` path unit is feasible as written. `pcalnon` has no
  write there, which is correct — udisks2 owns the directory.
- **systemd is v259** on this host. The `path.c` v259 citation in §7.8's comment block **applies to this
  host**, not merely to upstream. **AGREE.**
- One fact worth adding to the comment block, which I could not find stated anywhere in §7.8: **`/run` is
  tmpfs**, so `/run/media/pcalnon` does not survive a reboot and is re-created by udisks2. systemd path units
  handle a missing path by watching the nearest existing ancestor, so the unit still works — but a reader who
  assumes the directory is permanent will mis-read the first post-reboot trigger.
- §7.8's separate claim that the existing reporter is mis-pointed is **AGREE**:
  `systemctl --user show duplicati-backup-failure.service -p ExecStart` →
  `argv[]=/home/pcalnon/.local/bin/duplicati-backup-failure.bash duplicati-backup.service`, and
  `duplicati-backup.timer` is `disabled`.

---

## 7. Items the brief did not list that I could measure

| § | Claim | Verdict | Evidence |
| --- | --- | --- | --- |
| **§3.4** | `/opt/miniforge3/envs` **62 GB** (was 47) | **AGREE** | `du -sh /opt/miniforge3/envs` → `62G` |
| **§7.7** | `/home/pcalnon/.local/state` is **0700**, so the snapshot unit cannot simply become `User=duplicati` | **AGREE** | `/home/pcalnon/.local 755` → `/home/pcalnon/.local/state` **`700 pcalnon:pcalnon`** → `duplicati-server-db 700`. The 0700 is at the *middle* component, so no chmod of the leaf helps ✓ |
| **§7.4** | `chmod 0660` over **~1,700** files ⇒ ~1,700 metadata updates | **AGREE, and the exact number is 1,784** | under `…/Dropbox/Backups`: `find -type f` → **1784**; `find -type f -perm /111` → **1784** (every one carries an exec bit, so every one changes); `find -type d` → **64** |
| **§7.5** | existing volumes are **AES Crypt v2**, so `--aes-version` must be pinned against 2.4.0.0's v3 default | **AGREE** | `head -c 4 …/duplicati-20260918T140000Z.dlist.zip.aes \| od -An -tx1 -c` → `41 45 53 02` / `A E S 002` — magic `AES` + version byte **0x02** |
| **§4.2** | destination ctimes: `/mnt/Backups` 09-18 20:36:53, `/mnt/Backups/Ubuntu` 20:37:41, **874 of 877** volumes 09-19 17:37 | **AGREE, all three** | ctimes `2026-09-18 20:36:53.038611372` / `20:37:41.443664299`; volume ctime histogram → `874 @ 2026-09-19 17:37`, `2 @ 18:09`, `1 @ 18:21` |
| **§5.6** | Leg C: no `Server has started` on a **root-folder** start after 09-18 21:03:30 | **AGREE** | complete list since 09-17: `09-17 01:31:03 p8300`, `09-18 20:22:13 p8300`, `20:42:39 p8300`, **`21:03:30 p8300`**, `09-19 21:20:41 p8200`, `21:57:41 p8200`, `09-20 13:32:50 p8200`, `13:36:40 p8300`, `16:50:15 p8300`, `17:30:17 p8300`, `18:19:46 p8300`. The three p8200 starts are home-folder by the port discriminator; the four later p8300 starts are home-folder by independent physical evidence — the 18:19:46 start created `-wal` (birth 18:19:43.917937740) and `control_dir_v2/lock_v2` (18:19:45.109942301) **in `/home/duplicati/.config/Duplicati/`**. The last root-folder open is `09-19 19:15:01` — four `No database encryption key was found` + `SettingsEncryptionKeyMissingException` at 19:14:58–19:15:01, no `Server has started` after ✓ |
| **§4.1** | `/home/duplicati/.config/Duplicati` is world-writable with **no sticky bit** | **AGREE, and demonstrated** | `stat -c '%04a'` → `0777` (not `1777`); I read `Duplicati-server.sqlite` (`SQLite format 3`) from a process with **no** gid 139 — so "any local user" is literal, not theoretical |

---

## 8. DISAGREE — with exact replacement text

### D-1 — §4.1, "Abandoned data folder" row (and §5.5 "Permissions by trial")

**Measured**: `/usr/lib/duplicati` holds **118** directories; **97** are `duplicati`-owned; **21** are still
`root:root`. Those 21 are the whole `runtimes/` subtree (`runtimes`, its five arch directories, and their five
`native/` children = 11) plus ten `licenses/<package>/` directories (`StreamJsonRpc`, `NGettext`,
`JsonSignature`, `Handlebars.Net`, `Mono.Unix`, `SMBLibrary`, `DnsClient`, `Minio`, `SQLitePCLRaw`,
`ZstdSharp.Port`). `licenses/` itself *is* duplicati-owned, so this was not a `find -type d`-style sweep; it
looks like a shallow or interrupted recursion.

**Why it matters beyond precision.** The design uses this row to justify moving the chown to P0.5, and §7.3.1's
trust-domain tables reason from "every directory is already duplicati's". A reader who then runs a
`chown -R root:root /usr/lib/duplicati` will see 21 directories that *were already* correct and 97 that
change — if the remediation is verified by "did anything change?", the wrong 21 are the ones that look right.
State the split.

> **Replacement for the §4.1 row's first cell** (currently: "`/usr/lib/duplicati/data/` (0700, **now owned by
> `duplicati`**). `/usr/lib/duplicati` and **every directory beneath it** (97) were chowned to `duplicati`;
> **no file was** — all 1,443 regular files, `duplicati-server` included, are still `root:root` (note b)"):
>
> `/usr/lib/duplicati/data/` (0700, **now owned by `duplicati`**). `/usr/lib/duplicati` and **97 of the 118
> directories** in the tree were chowned to `duplicati`; the remaining **21 are still `root:root`** — the whole
> `runtimes/` subtree (11) and ten `licenses/<package>/` directories — so the sweep was shallow, not complete.
> **No file was chowned at all**: all 1,443 regular files outside `data/`, `duplicati-server` included, are
> still `root:root` (note b)

> **Replacement for the §5.5 "Permissions by trial" bullet's first sentence** (currently: "`/usr/lib/duplicati`
> and `/usr/lib/duplicati/data` were chowned to `duplicati` — **directories only**: all 1,443 regular files,
> the binaries included, are still `root:root`."):
>
> `/usr/lib/duplicati` and `/usr/lib/duplicati/data` were chowned to `duplicati` — **directories only, and not
> even all of those**: 97 of 118 directories changed owner, 21 (the `runtimes/` subtree and ten
> `licenses/<package>/` directories) did not, and all 1,443 regular files outside `data/`, the binaries
> included, are still `root:root`.

### D-2 — the `temp_backups` line multiplicity, in three places

**Measured**: the message appears **twice per event**, at 18:47:44 and 18:51:33 — **four lines in total**, not
eight. The pairing is an outer/inner exception, both under identifier `duplicati-wrapper.bash[1397393]`:

```
2026-09-20T18:47:44 … duplicati-wrapper.bash[1397393]:       System.Exception: Failed to process the path: Access to the path '/media/pcalnon/temp_backups' is denied.
2026-09-20T18:47:44 … duplicati-wrapper.bash[1397393]:        ---> System.UnauthorizedAccessException: Access to the path '/media/pcalnon/temp_backups' is denied.
2026-09-20T18:51:33 … (the same pair)
```

`grep -c "temp_backups' is denied"` → **4** in both the unit-scoped and the full journal. Confirmed as the
service's genuinely last output: the tail of `journalctl -u duplicati.service` ends in the 18:51:33 stack
trace; nothing has been emitted in the 3 days 8 hours since.

> **§4.1 note (a)** — replace "The live server's **last** journal lines are 09-20 18:47:44 and 18:51:33, ×4
> each: `Failed to process the path: Access to the path '/media/pcalnon/temp_backups' is denied`" with:
>
> The live server's **last** journal lines are 09-20 18:47:44 and 18:51:33, **×2 each — four lines in total**,
> since each event logs the outer `System.Exception: Failed to process the path: …` and its inner
> `System.UnauthorizedAccessException: Access to the path '/media/pcalnon/temp_backups' is denied`

> **§4.2 row** — replace "The live server's last journal lines, ×4 each: `Access to the path
> '/media/pcalnon/temp_backups' is denied`" with:
>
> The live server's last journal lines — two events, each logging the message twice (outer + inner exception),
> four lines in all: `Access to the path '/media/pcalnon/temp_backups' is denied`

> **Appendix A.1**, last excerpt line — replace the parenthetical `(last lines of the unit; x4, and again x4
> at 18:51:33)` with `(last lines of the unit; x2, and again x2 at 18:51:33 — 4 lines total)`

### D-3 — §6, S-1's syslog split does not sum to 23

**Measured**: under the `Invalid slot` predicate — the predicate the "23" is counted with — the two archives
carry **5** and **18**, which sums to 23. The "4" in the S-1 cell is a count under the *narrower*
`Failed to resolve specifiers` predicate, which by construction excludes the single
`Failed to resolve unit specifiers` line of 21:23:25. As written, S-1 says "the same lines" and then gives a
total of 22, so the cell contradicts itself and the §1 figure it is meant to corroborate.

```
syslog-20260919.gz : 'Invalid slot' = 5 ; 'Failed to resolve specifiers' = 4
syslog-20260920.gz : 'Invalid slot' = 18; 'Failed to resolve specifiers' = 18
                                    ---                                  ---
                                     23                                   22
```

> **§6 S-1 row** — replace "23 systemd `Invalid slot` journal lines, **and the same lines in
> `syslog-20260919.gz` (4) and `syslog-20260920.gz` (18)**" with:
>
> 23 systemd `Invalid slot` journal lines, **and the same 23 lines in `syslog-20260919.gz` (5) and
> `syslog-20260920.gz` (18)**

> **§6 preamble** — replace "`syslog-20260919.gz` and `syslog-20260920.gz` carry 4 and 18 specifier lines"
> with:
>
> `syslog-20260919.gz` and `syslog-20260920.gz` carry **5 and 18 `Invalid slot` lines** — 23, the journal's
> figure (4 and 18 under the narrower `Failed to resolve specifiers` predicate; the fifth line on 09-19's file
> is the `Failed to resolve unit specifiers` of 21:23:25)

---

## 9. WEAKENED — true as far as it goes, but the wording will mislead a re-checker

### W-1 — §4.2 note 5 / §5.4 / Appendix A.1: "five starts … at 13:32:34"

The five older-`wrapper.bash` starts were launched at 13:32:33, :34, :35, :36, :37 and died at 13:32:34, :35,
:36, :37, :38. Only the first died at :34.

> **§4.2 row** — replace "five starts of the **older** `wrapper.bash` died `KeyMissing` at 13:32:34" with
> "five starts of the **older** `wrapper.bash` died `KeyMissing` across 13:32:34–13:32:38 (the first at
> 13:32:34)".
> **§5.4** — replace "The `Missing` ×5 at 13:32:34" with "The `Missing` ×5 across 13:32:34–13:32:38".
> **Appendix A.1** — replace "at `13:32:34` on 09-20 five starts" with "from `13:32:34` to `13:32:38` on 09-20,
> five starts".

### W-2 — §6 names `syslog-20260921`, which is now `syslog-20260921.gz`

The counts are right and they are still in that file. But logrotate uses `delaycompress`, so the file was
plain when the design was written and is compressed now; `/var/log/syslog-20260922` (216 MB, plain) and
`/var/log/syslog` (18 MB) both carry **zero** of the six patterns. A D-8 scrub script that keys on the literal
name will silently no-op. Suggest "`syslog-20260921` (now `syslog-20260921.gz` — `delaycompress` means the
day file's name gains `.gz` one rotation later; glob it, do not name it)". The scrub instruction's own two
halves ("the plain day files edited as root, the `.gz` files regenerated") already anticipate this; only the
named example is stale. The `rotate 10`/`daily` retention means this file ages out around **2026-10-01** —
§6's "~10 days" ✓.

### W-3 — §6 S-2's "readable by group `duplicati`, i.e. `pcalnon`"

`id pcalnon` does list 139, but group membership binds at login, not at `chmod` time. My own session —
`pcalnon`, `sudo`-capable, on this host — has `Groups: 4 24 27 30 46 100 114 128 984 993 1000 1003`, **no 139**,
and therefore **could not read `.env`**:

```
$ head -c 0 /home/duplicati/.config/Duplicati/.env
head: cannot open '/home/duplicati/.config/Duplicati/.env' for reading: Permission denied
```

This is the same mechanism §4.1 already records for Dropbox ("pcalnon, **without gid 139**"). Recommend
"readable by group `duplicati` — i.e. by any `pcalnon` process whose credentials were established after the
group membership took effect; sessions older than that, the Dropbox daemon among them, do not carry gid 139".
Note this does **not** shrink the exposure: `sudo` and `su - duplicati` are both one step away, and the 0777 DB
copies need no group at all.

### W-4 — §6 sink checklist, "World-readable server-DB copies" needs its paths

Both modes are confirmed, but they live in two different profiles, and only one set is actually reachable:

| File | Mode | Reachable by other users? |
| --- | --- | --- |
| `/home/duplicati/.config/Duplicati/Duplicati-server.backup` | **0777** | **Yes** — every ancestor is 0755/0777 |
| `/home/duplicati/.config/Duplicati/backups/Duplicati-server_2026-08-22_pre-dbpath-fix.sqlite` | **0644** | **Yes** |
| `/home/duplicati/.config/Duplicati/temp1/Duplicati.GUI.TrayIcon-crashlog.txt` | **0644** | **Yes** — a fourth copy the row does not list |
| `/home/pcalnon/.config/Duplicati/backups/Duplicati-server_2026-08-22_pre-dbpath-fix.sqlite` | 0644 | **No** — `/home/pcalnon/.config/Duplicati` is 0700 |
| `/home/pcalnon/.config/Duplicati/Duplicati-server.backup` | 0600 | No |

The pcalnon-profile copies are *mode*-loose but *path*-protected; the duplicati-home copies are genuinely
exposed. Name the paths, or a `chmod 0600` sweep will be scoped to the harmless set. `/home/duplicati/.config/Duplicati/temp1/`
also holds a full second copy set (`Duplicati-server.backup`, `.sqlite`, `-shm`, the 112 MB `-wal`) at 0600,
and `temp/` holds a third 112 MB `-wal` — neither directory is named anywhere in §4.1 or §6.

---

## 10. Instrument adequacy — could this instrument have produced a different answer?

**For the counts, yes — and one instrument choice is exactly what the recorded dissent is about.** The
specifier-line figure is *made* by the filter: `journalctl -u duplicati.service` returns 22 and the unscoped
`journalctl` returns 23, differing by one line (2026-09-19T18:07:32) that systemd emitted before the unit was
associated. I ran both and diffed the timestamp sets, so the number is not an artefact of whichever I happened
to type. The same hazard bites the failure counts from the other side: a raw `grep -c` doubles every .NET error
because journald tags identical text under two `SYSLOG_IDENTIFIER`s, giving 10 / 10 / 28 where the design says
5 / 5 / 14; counting **distinct pids** — one pid per start — recovers 5 / 5 / 14 exactly. Both figures are
"correct" for their unit; only one answers "how many starts failed". I report the unit with every count.

**For the mode, ownership and timestamp facts, no.** `stat`, `find -printf` and `getfacl` report kernel inode
state; the only way they could mislead is by scope, and scope bit once: `find` as `pcalnon` cannot descend into
`/usr/lib/duplicati/data` (0700, and this session lacks gid 139), so "1,443 files" is the count *outside*
`data/` and I have said so rather than letting it read as a whole-tree figure. That same credential gap is a
positive result elsewhere: because my process genuinely lacks gid 139 and still read the 0777 databases, "any
local user can read them" is demonstrated, not inferred — whereas my failure to read the 0660 `.env` proves the
group barrier is real for a process, which is W-3.

**For the negative claims, the risk is vacuity.** "No drop-in", "no `juniper-backup` unit", "no udev rule",
"`/run/media/pcalnon` is empty", "no `Server has started` after 21:03:30" are all absence claims, and an
absence claim from a mistyped path reads identically to a true one. Each was paired with a positive control
from the same command: the drop-in check also listed the units that *do* exist; the udev grep was run over a
directory whose other rules matched fine; the `Server has started` enumeration printed all eleven hits since
09-17 rather than only counting the ones after a cut-off; the `/run/media/pcalnon` emptiness sits beside a
`getfacl` that returned a real named entry. The `Invalid slot` diff is itself such a control — `comm -23`
named the single missing line instead of leaving me with two counts and a shrug.

**Two things this instrument class structurally cannot settle.** First, a ctime dates the *last* metadata
change, so 18:33:45 proves a chmod/chown happened then, not that it was *the* chmod to 0777; the conclusion
survives only because the 18:19:42 start is independently known to have succeeded. Second, `NRestarts=0` and an
unchanged `MainPID` prove the armed `ExecStart` has not fired, but they say nothing about what the *next* fire
does — that verdict rests on §5.5's gate reasoning, which I re-measured the inputs to and did not re-derive.

**A sink I created and removed.** Capturing the journal for these counts wrote an 876 MB file containing 12
`Settings Encryption Key:` lines and 264 `LINE: "` echoes into the session scratchpad. I deleted it and the
unit-scoped capture as soon as the counts were taken (`rm -f …/all.txt …/dup_unit.txt …/full_ts.txt
…/unit_ts.txt`; the scratch directory now holds ten `.bash` scripts and no data file, and the only
`Settings Encryption Key:` strings left in it are grep *patterns*). It existed for roughly eight minutes. This
is worth adding to §6's sink checklist as a class: **any agent that re-verifies these counts creates a new
copy of the leak**, and the D-8 scrub's completeness depends on nobody leaving one behind.

---

## 11. What I could not determine (root or credentials required)

1. **`/usr/lib/duplicati/data/` contents** — `ls: cannot open directory … Permission denied` (0700 `duplicati`;
   this session lacks gid 139, and 0700 excludes the group anyway). So §4.2 note 1's decisive question —
   *does a `-wal` still sit beside the main file, i.e. is the pre-21:03 cleartext state a second key-free
   recovery source?* — **remains open**, and the design's `sudo ls -la /usr/lib/duplicati/data/` is still the
   one command that answers it. Likewise the real server DB and `BMXWPAOGLP.sqlite` are unverified by me.
2. **`/home/duplicati/.config/Duplicati/.env` shape** — 0660 `duplicati:duplicati`, unreadable from a process
   without gid 139. I confirmed its mode, size (1,599 B), mtime and ctime but **not** the "one active line /
   five commented-out lines / 32-char value" shape. Re-run `util/ad-hoc/2026-09-21_env_file_shape.py` under
   `sudo -u duplicati`.
3. **Root's `~/.bash_history` and `~/.viminfo`** — unreadable. The design *relies* on these as the last place
   the 09-18 key may be recorded; the count-grep it prescribes is still unrun.
4. **CUPS retention** — `/etc/cups/cupsd.conf` and `/var/spool/cups` both Permission denied. The escrow-sheet
   print job's retention is still unknown.
5. **Whether the 18:33:45 ctime was a `chmod` or a `chown`** — a ctime does not record which. The conclusion
   ("the folder was loosened after the start") holds either way.
6. **Whether the five older-wrapper starts at 13:32 used the home folder** — inferred from the wrapper's own
   `line 38: /home/duplicati/.config/.env` message and the 13:32:50 port-8200 success, not measured directly;
   they exited before writing anything datable.
7. **`readlink /proc/1397393/exe`** returned empty (no ptrace access to a `duplicati`-owned process from
   `pcalnon`). The argv came from `/proc/1397393/cmdline`, which is world-readable; the binary identity behind
   it is asserted by argv[0] (`/usr/lib/duplicati/duplicati-server`), not verified.
8. **Everything in §5.3's 08-25 Repair/Verify timeline** — those events predate this journal's oldest boot
   (`FIRST ENTRY Sun 2026-09-06 01:17:14 CDT`) and live in database copies, which is another lane's entry
   point. Not attempted.

<!-- markdownlint-enable -->

---

## Report A (product) — measurement re-creation; entry point: PRODUCT BEHAVIOUR only

Subagent id `a20bd5a975a5286ed` (40,846 characters). Archived verbatim.

<!-- markdownlint-disable -->

I have everything. Writing the final report.

---

# Consensus round 2 — Lane A (measurement re-creation, PRODUCT BEHAVIOUR ONLY)

**Document under review**: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` (worktree `buzzing-painting-meteor`).
**Brief**: `ROUND2_BRIEF.md` (scratch). **Changed**: nothing — findings only; no repository file was edited.

## 0. Provenance of the instrument

```
$ duplicati-server-util --version ; duplicati-database-tool --version
2.4.0.0-Stable-20260903+f04c49d78620d7f4d5e79f7dbb9ee393e6a128db
$ dpkg-query -W -f='${Package} ${Version} ${Status}\n' duplicati
duplicati 2.4.0.0 install ok installed
$ systemd-analyze --version | head -1
systemd 259 (259.5-0ubuntu3.4)
```

`duplicati-server` was **never** invoked in any form. 549 assemblies under `/usr/lib/duplicati`. Upstream source fetched read-only at tag `v2.4.0.0_stable_2026-09-03`, which the installed build's commit stamp (`+f04c49d7…`) matches; every source claim below was cross-checked against a string or symbol actually present in the shipped DLL.

---

## 1. Option-name existence scan

Method: `duplicati-cli help <topic>` / `duplicati-server-util help [<sub>]` / `duplicati-database-tool help [<sub>]` (224 distinct declared names harvested by `check_help_names.py`), then a UTF-16LE **and** UTF-8 byte scan of all 549 DLLs (`scan_assemblies.py`), then a prefix enumerator (`enum_prefix.py`) for any near-miss.

| Option | Verdict | Component it belongs to |
|---|---|---|
| `--server-datafolder` | FOUND-IN-HELP | **server** (`Program.cs:1590`), **server-util**, **database-tool** (on `wipe-encryption`/`upgrade`/`downgrade`), also `duplicati-cli help advanced` |
| `--portable-mode` | FOUND-IN-HELP | **server** (`Program.cs:1559`), server-util, CLI advanced |
| `--allow-insecure-datafolder` | FOUND-IN-HELP | **server** (`Program.cs:1591`), server-util (all subcommands), database-tool (top level **and** every subcommand) |
| `--require-db-encryption-key` | FOUND-IN-ASSEMBLY (`Duplicati.Server.Implementation.dll`, utf16le) | **server only** (`Program.cs:63`) |
| `--disable-db-encryption` | FOUND-IN-ASSEMBLY (`Duplicati.Server.Implementation.dll`, `Duplicati.Agent.Implementation.dll`) | **server** (`Program.cs:59`) + agent |
| `--settings-encryption-key` | FOUND-IN-HELP (server-util) + ASSEMBLY (`Duplicati.Server.Implementation.dll`) | **both** server (`Program.cs:65`, `1595`, `ArgumentType.Password`) **and** server-util |
| `--secret-provider` | FOUND-IN-HELP | **server** (`Program.cs:228`, `1538`), server-util, CLI |
| `--parameters-file` | FOUND-IN-HELP (`duplicati-cli help advanced` + `help password`) | **server** (`Program.cs:49`, `1558`, alias `parameterfile`) and CLI |
| `--settings-file` | FOUND-IN-HELP (server-util only) | **server-util** (+ agent). **NOT** a server option — `grep -c 'settings-file' Duplicati/Server/Program.cs` → `0`; absent from `Duplicati.Server.Implementation.dll` |
| `--webservice-password-init` | FOUND-IN-ASSEMBLY (`Duplicati.Server.Implementation.dll`) | **server** (`WebServerLoader.cs:68`) |
| `--webservice-disable-signin-tokens` | FOUND-IN-ASSEMBLY (server + agent) | **server** (`WebServerLoader.cs:96`) |
| `--webservice-allowed-hostnames` | FOUND-IN-ASSEMBLY (server + agent) | **server**, and it is the **primary** name (`WebServerLoader.cs:83`); `webservice-allowedhostnames` is the `_ALT` legacy form (`:87`) |
| `--webservice-interface` | FOUND-IN-ASSEMBLY | **server** (`WebServerLoader.cs:58`); `loopback` is a valid value **and the default** (`:187`) |
| `--webservice-port` | FOUND-IN-ASSEMBLY | **server** (`DEFAULT_OPTION_PORT = 8200`, `WebServerLoader.cs:137`) |
| `--webservice-tokenduration` | **NOT FOUND** | see §1a |
| `--aes-version` | FOUND-IN-HELP (`duplicati-cli help aes`) | **aes encryption module** (`Duplicati.Library.Encryption.dll`) |
| `--aes-v3-iterations` | FOUND-IN-HELP | aes module |
| `--run-script-before` | FOUND-IN-HELP (`help runscript`) | **runscript module** (`Duplicati.Library.Modules.Builtin.dll`) |
| `--run-script-before-required` | FOUND-IN-HELP | runscript module |
| `--run-script-timeout` | FOUND-IN-HELP (default `60s`) | runscript module |
| `--upload-verification-file` | FOUND-IN-HELP | `Duplicati.Library.Main.dll` (operation option) |
| `--no-local-db` | FOUND-IN-HELP | Main (list/restore) |
| `--restore-with-local-blocks` | FOUND-IN-HELP | Main (restore) |
| `--no-local-blocks` | FOUND-IN-HELP, **marked `[DEPRECATED]`** | Main (restore) |
| `--dbpath` | FOUND-IN-HELP | Main / CLI |
| `--version` | FOUND-IN-HELP — **two distinct options share the spelling** | (a) CLI list/restore selector, `(String) "The version to list/restore files"`; (b) System.CommandLine's "Show version information" on `duplicati-server-util` / `duplicati-database-tool` |
| `--time` | FOUND-IN-HELP (`duplicati-cli help restore` → `--time=<time>`) | Main (list/restore). NB `duplicati-cli help time` prints the *date-format topic*, not the option |
| `--tempdir` | FOUND-IN-HELP (default `/tmp/`) | Main; **also a server option** (`Program.cs:89`, handled at `:220`) |
| `--blocksize` | FOUND-IN-HELP (default `1mb`) | Main |
| `--dblock-size` | FOUND-IN-HELP (default `50mb`) | Main |
| `--no-auto-compact` | FOUND-IN-HELP | Main |
| `--asynchronous-upload-limit` | FOUND-IN-HELP (default `4`) | Main |
| `--allow-missing-source` | FOUND-IN-HELP | Main |
| `startup-delay` | FOUND-IN-ASSEMBLY (`Duplicati.Library.RestAPI.dll`) — **a server-settings DB key, not a CLI option** | It sits in the `ApplicationSettings` key block beside `update-check-interval`, `paused-until`, `autogenerated-passphrase`. No `--startup-delay` exists in any help output or in `Program.cs`. **This is exactly what the design says** ("`startup-delay` **is** present by name among the server *settings* at `BackupID=-2`") → AGREE |
| `wipe-encryption` | FOUND-IN-HELP | `duplicati-database-tool` subcommand |
| `--server-datafolder` **on `wipe-encryption`** | **FOUND-IN-HELP (subcommand level)** | AGREE with the design's §8 trap note |
| `--dry-run` **on `wipe-encryption`** | **FOUND-IN-HELP (subcommand level)** | AGREE |

```
$ duplicati-database-tool help wipe-encryption
Options:
  --server-datafolder <server-datafolder>  The folder with databases [default: /home/pcalnon/.config/Duplicati]
  --no-backups                             Do not create a backup before wiping [default: False]
  --include-untracked-databases            Include untracked databases in the wipe process [default: False]
  --dry-run                                Show what would be wiped without making changes [default: False]
  --allow-insecure-datafolder              Allow the data folder to have insecure permissions instead of rejecting it [default: False]
```

The design's §8 step-3 statement that `--server-datafolder` "**is** an option of the *subcommand* … even though the top-level `help` does not list it" is **exactly right**: the top-level `duplicati-database-tool help` shows only `--allow-insecure-datafolder` and `--version`.

### 1a. `--webservice-tokenduration` does not exist

```
$ python3 enum_prefix.py webservice-
  webservice-token-duration                    Duplicati.Server.Implementation.dll[utf-16-le]
  ... (23 distinct; no 'webservice-tokenduration')
```
```
$ grep -n 'TOKENDURATION' src/Duplicati_Server_WebServerLoader.cs
117:    public const string OPTION_WEBSERVICE_TOKENDURATION = "webservice-token-duration";
142:    public const string DEFAULT_OPTION_TOKENDURATION = "30D";
```

The **constant** is `OPTION_WEBSERVICE_TOKENDURATION`; its **value** — the option name — is `webservice-token-duration`. Reading the constant name rather than its value is how the unhyphenated form is produced.

**The design does not use it.** `grep -i 'tokenduration\|token-duration'` over the design returns nothing. So this is an advisory, not a defect: **if** the unit or `.env` ever gains it, it must be spelled `--webservice-token-duration`, and — per §D-1 below — a misspelling would *not* fail the start.

---

## 2. The three claims that decide an action

### 2(a) `--webservice-password-init` — **AGREE, on all four sub-claims**

```
$ grep -n 'password-init\|EXITCODE_INITPASSWORD' src/Duplicati_Server_Program.cs
 98:  public const int EXITCODE_INITPASSWORD_SUCCESS = 102;
102:  public const int EXITCODE_INITPASSWORD_FAILED = 103;
1571: new CommandLineArgument(WebServerLoader.OPTION_WEBSERVICE_PASSWORD_INIT, CommandLineArgument.ArgumentType.Password, …)
```
```csharp
// Program.cs ~675
var initPassword = commandlineOptions.GetValueOrDefault(WebServerLoader.OPTION_WEBSERVICE_PASSWORD_INIT);
if (!string.IsNullOrWhiteSpace(initPassword))
{
    // If initPassword is set, we want the initialization to stop now, so we throw an exception
    if (connection.ApplicationSettings.AutogeneratedPassphrase)
    {
        connection.ApplicationSettings.SetWebserverPassword(initPassword);
        return EXITCODE_INITPASSWORD_SUCCESS;
    }
    else
    {
        return EXITCODE_INITPASSWORD_FAILED;
    }
}
```

- **Password-type**: yes, `ArgumentType.Password` — and `ICommandLineArgument.Type` is presentation metadata only (`ICommandLineArgument.cs`); the value is read straight from the parsed argv dictionary, so it **can** sit on argv. AGREE.
- **Applies only while autogenerated**: yes, gated on `AutogeneratedPassphrase`. AGREE.
- **102 / 103**: exact. AGREE.
- **Must never sit in `DAEMON_OPTS` under `Restart=on-failure`**: AGREE, and stronger than the design says — 102 *and* 103 are both non-zero, so the **success** path also loops under `Restart=on-failure`, not just the failure path.

The design's further claim that "the server applies both [`--secret-provider` and `--parameters-file`] *before* it reads the init value" is **AGREE**:

```csharp
// Program.cs 227-237  (RealMain, before GetDatabaseConnection at :259)
ApplyEnvironmentVariables(commandlineOptions);
ApplySecretProviderAsync(applicationSettings, commandlineOptions, CancellationToken.None).Await();
var parameterFileOption = PARAMETERS_FILE_OPTION_EXTRAS.Prepend(PARAMETERS_FILE_OPTION) …
    ReadOptionsFromFile(filename, ref filter, args, commandlineOptions);
```

Corroborating S-6: the signin-token URL is emitted only while the password is autogenerated — `Program.cs:338`, `if (applicationSettings.Origin == "Server" && connection.ApplicationSettings.AutogeneratedPassphrase)`.

### 2(b) `--settings-file` is a `duplicati-server-util` option, not a server option — **AGREE**

```
$ duplicati-server-util help          # and help login|logout|change-password|status|run|…
  --settings-file <settings-file>                      The settings file to use []
$ grep -c 'settings-file' src/Duplicati_Server_Program.cs
0
$ python3 scan_assemblies.py 'settings-file'
FOUND [utf16le] 'settings-file' in 2 file(s): Duplicati.Agent.Implementation.dll, Duplicati.CommandLine.ServerUtil.Implementation.dll
```

It is absent from `Duplicati.Server.Implementation.dll` in both encodings. The server's file channel is `--parameters-file`, which **is** declared there (`Program.cs:1558`, `ArgumentType.Path`, alias `parameterfile`) and is applied before the init value is read. AGREE with the design's parenthetical "an earlier reading named the wrong file channel".

### 2(c) `duplicati-server-util`'s auth chain including the console prompt — **AGREE on existence, WEAKENED on ordering**

Source (`Duplicati/CommandLine/ServerUtil/Connection.cs`, tag `v2.4.0.0_stable_2026-09-03`):

```csharp
:228  if (!string.IsNullOrWhiteSpace(settings.RefreshToken))            // 1. saved refresh token
:250  if (string.IsNullOrWhiteSpace(settings.Password))                 // 2. ONLY if no --password
      {   …
:256      if (settings.Key != null) opts["settings-encryption-key"] = settings.Key.Key;
:260      using (var connection = Server.Program.GetDatabaseConnection(new ApplicationSettings(), opts, true, false))
:262          cfg = connection.ApplicationSettings.JWTConfig;           //    needs readable AND decryptable DB
:267          var signinjwt = new JWTTokenProvider(…).CreateSigninToken("server-cli");
      }
:304  if (string.IsNullOrWhiteSpace(settings.Password))                 // 3. console prompt
:305      settings = settings with { Password = Library.Utility.Utility.ReadSecretFromConsole("Enter server password: ") };
:310  … LoginWithPasswordAsync(client, settings.Password, obtainRefreshToken)
```

**And I reproduced the prompt from the installed binary**, which settles round 1 from the product, not only the source:

```
$ duplicati-server-util status --server-datafolder <scratch>/sutest --hosturl http://127.0.0.1:1/ < /dev/null
Connecting to http://127.0.0.1:1/...
No database found in …/sutest/
Enter server password: Failed to connect to server: Cannot read keys when either application does not
have a console or when console input has been redirected. Try Console.Read.
EXIT=2
```

The design (§7.3.6) is correct that the prompt exists and that `help` does not list it. Two precisions:

1. **`--password` does not come *after* the signin-token branch — it *prevents* it.** The DB branch is inside `if (string.IsNullOrWhiteSpace(settings.Password))`. So supplying `--password` means server-util never opens the database and never needs the settings key at all. The design's "…else a signin token … else `--password` …" reads the other way round.
2. **`ReadSecretFromConsole` uses `Console.ReadKey(true)`** (`Duplicati/Library/Utility/Utility.cs:2167-2204`), so it throws whenever stdin is redirected — which is every scripted, `systemd-run`, or headless invocation. The prompt is not a usable non-interactive channel. This *strengthens* the design's conclusion that the in-process client is the fix.

---

## 3. The 0700 data-folder gate — **AGREE on all three overrides, AGREE on "every start", plus two behaviours the design does not state**

Overrides, from `Duplicati/Library/Common/IO/Util.cs` (its literals are the only copies in `Duplicati.Library.Common.dll`, at `0x0000a6c8`/`0x0000a70a`/`0x0000a754`):

```csharp
:43  public const string AllowInsecureDatafolderOption  = "allow-insecure-datafolder";
:50  public const string AllowInsecureDatafolderEnvVar  = "DUPLICATI__ALLOW_INSECURE_DATAFOLDER";
:55  public const string InsecurePermissionsMarkerFile  = "insecure-permissions.txt";
:68  public static bool AllowInsecureDataFolder()
:72      var args = Environment.GetCommandLineArgs().Skip(1).ToArray();   // raw process argv
:98      var envValue = Environment.GetEnvironmentVariable(AllowInsecureDatafolderEnvVar);
:103     var installfolder = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
:106     var path = Path.Combine(installfolder, InsecurePermissionsMarkerFile);
```

Exactly three, in that precedence, marker file in the **install folder** (= `/usr/lib/duplicati`). AGREE.

"Every start": `Server/Program.cs:1143`, inside `GetDatabaseConnection`, which `RealMain` calls at `:259` on every start —

```csharp
// Ensure the directory holding the database exists and has secure permissions.
DataFolderManager.PrepareSecureDataFolder(System.IO.Path.GetDirectoryName(databasePath), createIfMissing: true);
```

and `PrepareSecureDataFolder` recomputes `folderPreExisted = Directory.Exists(dataFolder)` per call, then `VerifyDataFolderSecurity(dataFolder, folderPreExisted)` unless overridden. The predicate (`SystemIOLinux.cs:500-539`) is: mode must contain 0700, **no** group or other bits (`& 077 == 0`), owner ∈ {current uid, root}. AGREE with §5.5/§7.3.2.

**Behavioural confirmation on this host** (`test_datafolder_gate2.bash`, `test_gate_control.bash`) — one factor varied at a time, `--hosturl` pointed at a closed port, never running the server:

| case | folder | DB present | override | result |
|---|---|---|---|---|
| 1 | 0700 | no | – | proceeds (EXIT=2 at the prompt) |
| 2 | **0755** | **no** | – | **EXIT=1, stdout 0 B, stderr 0 B** |
| 3 | 0700 | yes | – | proceeds |
| 4 | 0755 | yes | – | **EXIT=1, 0 B** |
| 5 | 0755 | yes | `--allow-insecure-datafolder` | proceeds |
| 6 | 0755 | yes | `DUPLICATI__ALLOW_INSECURE_DATAFOLDER=true` | proceeds |
| 7 | 0750 (group bit only) / 0701 (other-exec only) | yes | – | EXIT=1, 0 B |
| 8 | same folder 0700 → then `chmod 755` | yes | – | first run proceeds, **second refuses** → the gate is re-evaluated per invocation |

Two things the design does not say and should:

- **The refusal is completely silent in `duplicati-server-util`**: exit 1, nothing on stdout or stderr. An operator following §8's probe steps against a copy directory that is not 0700 gets no diagnostic at all.
- **`duplicati-database-tool` does NOT apply the gate**, despite advertising `--allow-insecure-datafolder` on every subcommand. `wipe-encryption --server-datafolder <0755 dir> --dry-run` ran normally with no override (`test_wipe_encryption_gate.bash`, case 2, EXIT=0, "Dry run complete: 0 encrypted field(s) would be wiped"). Cause: `GetDataFolder` only calls `PrepareSecureDataFolder` when `mode == AccessMode.ReadWritePermissionSet`, and the database-tool paths resolve in `ProbeOnly` ("This is a no-op in ProbeOnly mode", `DataFolderManager.cs:140-145`).

---

## 4. AES — **AGREE on all three**

```
$ duplicati-cli help aes
  --aes-version (Enumeration): Set the AES file format version
    * values: 2, 3
    * default value: 3
  --aes-v3-iterations (Integer): Set the number of iterations used for AES v3 key derivation
    * default value: 300000
```

Both defaults are printed from the *runtime* values (`AESEncryption.cs:232` emits `SharpAESCrypt.EncryptionOptions.Default.FileVersion.ToString()`), so "3" and "300000" are the installed build's actual defaults, not documentation. `PBKDF2`/`Rfc2898`/`KdfIterations` are all present in the shipped `SharpAESCrypt.dll`.

Volume headers, read-only, **all 877 volumes** (`read_aes_headers.py`; every file opened `'rb'`, nothing written under `/mnt/Backups/`):

```
  duplicati-20260825T102739Z.dlist.zip.aes    first8=4145530200002143  -> magic=AES v2
  …
# tally over every volume:
    877  41455302  magic=b'AES' version=2
```

`41 45 53` = `AES`, byte 3 = `0x02` ⇒ AES Crypt **v2**, uniformly, with no v3 volume anywhere in the set. The design's "existing volumes are AES Crypt v2; 2.4.0.0 defaults to v3; pin `--aes-version`" is correct and the pin is load-bearing.

---

## 5. systemd — **AGREE on all four sub-claims**

```
$ systemd --version | head -1        (via systemctl --version / systemd-analyze --version)
systemd 259 (259.5-0ubuntu3.4)
```

**(i) The re-check paragraph exempts nothing.** `man systemd.path`, DESCRIPTION:

> "When a service unit triggered by a path unit terminates (regardless whether it exited successfully or failed), monitored paths are checked immediately again, and the service accordingly restarted instantly. As protection against busy looping in this trigger/start cycle, a start rate limit is enforced on the service unit…"

No directive is named; no exemption is stated. AGREE.

**(ii) The "does not apply" sentence is about activation, not termination.** It sits inside the `PathExists=…` option description and its antecedent is the immediately preceding sentence:

> "If a path already exists (in case of `PathExists=` and `PathExistsGlob=`) or a directory already is not empty (in case of `DirectoryNotEmpty=`) **at the time the path unit is activated**, then the configured unit is immediately activated as well. Something similar does not apply to `PathChanged=` and `PathModified=`."

So it governs start-of-watch activation. AGREE that the man page conflates the two for a careless reader, and AGREE that the design is right to call it out.

**(iii) The `path.c` predicate.** `src/core/path.c` at upstream tag `v259`:

```c
:226        case PATH_CHANGED:
:227        case PATH_MODIFIED:
:228                b = access(s->path, F_OK) >= 0;
:229                good = !initial && !from_trigger_notify && b != s->previous_exists;
:230                s->previous_exists = b;
:231                break;
```

Character-for-character the design's quoted predicate. AGREE.

**(iv) `path_trigger_notify_impl` re-checks with `from_trigger_notify=true`.**

```c
:823 static void path_trigger_notify_impl(Unit *u, Unit *other, bool on_defer) {
:860         path_enter_waiting(p, /* initial= */ false, /* from_trigger_notify= */ true);
```

AGREE. Net effect, which the design has right: the re-check *does* run after the triggered service terminates, but for `PathChanged=`/`PathModified=` `good` is forced false, so there is no instant re-trigger. (Note `path_enter_waiting` calls `path_check_good` **twice** — once before `path_watch()` and again after, `:593` and `:610` — and both carry `from_trigger_notify` through, so the exemption holds on both.)

**Binding the upstream source to the installed build** (Ubuntu patches are not visible in a GitHub tag):

```
$ strings -a /usr/lib/x86_64-linux-gnu/systemd/libsystemd-core-259.so | grep -F …
Got triggered by '%s'.
Failed to enter waiting state: %m
Got notified about unit deactivation.
Got notified about unit activation.
path_trigger_notify_impl
path_trigger_notify_on_defer
path_spec_check_good
```

All four literals and all three symbol names from upstream `path.c` are present in the shipped core library.

---

## 6. `systemd-analyze` on the §7.3.2 unit

Extraction (unmodified, via the design's own linter):

```
$ python3 util/ad-hoc/2026-09-21_lint_design_snippets.py --doc notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md --workdir <scratch>/snippets
tagged blocks found: 14
etc/systemd/system/duplicati.service  (lang=ini, doc line 561, 74 lines)
  [PASS] systemd-analyze verify
…
blocks: 14  failures: 0
```

As written, unmodified:

```
$ systemd-analyze verify aswritten/duplicati.service
duplicati.service: Command /usr/local/lib/duplicati/duplicati-wrapper.bash is not executable: No such file or directory
VERIFY_EXIT=1
```

With **only** the `ExecStart` binary swapped for `/bin/true` (one-line diff shown):

```
$ systemd-analyze verify aswritten2/duplicati.service
VERIFY_EXIT=0
```

**No directive the design added fails to parse on systemd 259.** The sole verify complaint is the not-yet-installed wrapper. Every one of `IPAddressDeny=`, `IPAddressAllow=`, `RestrictAddressFamilies=`, `SystemCallFilter=`, `SystemCallErrorNumber=`, `ProtectProc=`, `ProcSubset=`, `PrivateDevices=`, `ProtectClock=`, `ProtectHostname=`, `ProtectKernelLogs=`, `RestrictNamespaces=`, `InaccessiblePaths=` and both `Environment=` lines parses clean.

```
$ systemd-analyze security --offline=true --no-pager aswritten/duplicati.service
→ Overall exposure level for duplicati.service: 1.7 OK 🙂
```

**15 ✗ rows, 66 ✓ rows.** Every ✗, verbatim:

| ✗ | exposure |
|---|---|
| `SystemCallFilter=~@resources` — allow list defined, and `@resources` is included (e.g. `ioprio_set`) | 0.2 |
| `SystemCallFilter=~@privileged` — allow list defined, and `@privileged` is included (e.g. `chown`) | 0.2 |
| `RemoveIPC=` — Service user may leave SysV IPC objects around | 0.1 |
| `RootDirectory=/RootImage=` — Service runs within the host's root directory | 0.1 |
| `AmbientCapabilities=` — Service process receives ambient capabilities | 0.1 |
| `CapabilityBoundingSet=~CAP_(DAC_*\|FOWNER\|IPC_OWNER)` — may override UNIX file/IPC permission checks | 0.2 |
| `MemoryDenyWriteExecute=` — may create writable executable memory mappings | 0.1 |
| `RestrictAddressFamilies=~AF_UNIX` — may allocate local sockets | 0.1 |
| `RestrictAddressFamilies=~AF_(INET\|INET6)` — may allocate Internet sockets | 0.3 |
| `ProtectHome=` — read-only access to home directories | 0.1 |
| `PrivateNetwork=` — has access to the host's network | 0.5 |
| `PrivateUsers=` — has access to other users | 0.2 |
| `DeviceAllow=` — device ACL with some special devices: `char-rtc:r` | 0.1 |
| `IPAddressDeny=` — defines IP address allow list with only localhost entries | 0.1 |
| `UMask=` — files created by service are group-writable by default | 0.1 |

Twelve of the fifteen are deliberate design choices already argued in §7.1/§7.3.2/§7.4 (`AmbientCapabilities`/`CAP_DAC_READ_SEARCH` per D-4; `ProtectHome=read-only` so the Source is readable; `UMask=0007` per the D-14 group model; `AF_UNIX`+`AF_INET*` and `IPAddressAllow=localhost` for the loopback web UI). Three are genuine, cheap, unclaimed hardening the design could add and does not mention: **`MemoryDenyWriteExecute=`** (would break the .NET JIT — do **not** add), **`RemoveIPC=yes`** (free), **`PrivateUsers=yes`** (would conflict with `AmbientCapabilities=` — do not add). The only free one is `RemoveIPC=yes`.

---

## DISAGREE — with exact replacement text

### D-1 (REFUTED, consequential). §7.3.3's header note inverts the product's actual unknown-option behaviour.

The design's `usr/local/lib/duplicati/duplicati-wrapper.bash` header block currently reads (doc lines 683–688):

```
# Unknown options: this wrapper does NOT validate option names against the server's own list.
# A --option line in .env that the server does not know is passed through, and 2.4.0.0 exits
# on an unrecognised server option rather than ignoring it -- so a typo in .env is a start
# failure, not a silent misconfiguration. That is the intended direction (fail closed), but it
# means .env is part of the start path and a bad line takes the service down: change it with
# --print-command first. (Lane B2 C6.)
```

2.4.0.0 does **not** exit on an unrecognised option. `Duplicati/Library/Utility/CommandLineArgumentValidator.cs`:

```csharp
foreach (var (key, value) in options.Where(x => !IgnoredOptions.Contains(x.Key)))
{
    if (!allOptions.TryGetValue(key, out var option) || option == null)
    {
        Logging.Log.WriteWarningMessage(LOGTAG, "UnknownOption", null, $"Unknown option supplied: {key}");
        continue;
    }
```

`Server/Program.cs:243` is the only call site, and the only non-zero returns in the whole file are `100` (unhandled exception) and `102`/`103` (the init-password path). Empirically, on the shipped binaries:

```
$ duplicati-cli system-info --this-option-does-not-exist=1
Duplicati: Duplicati.CommandLine, Version=2.4.0.0, …
Version name: "2.4.0.0_stable_2026-09-03" (2.4.0.0)
…
EXIT=0
```

The `"Unknown option supplied: "` literal exists in exactly one assembly, `Duplicati.Library.Utility.dll`, which `Duplicati.Server.Implementation.dll` references — so the CLI result is the server's code path. The design's own §4.3.9 corroborates it: `--daemon-opts="--webservice-port=8300"` was "passed through as an unknown option" and the server **started** (on 8200).

**Exact replacement text** for those six lines:

```
# Unknown options: this wrapper does NOT validate option names against the server's own list,
# and neither does the server. 2.4.0.0's CommandLineArgumentValidator.ValidateArguments logs
# "Unknown option supplied: <name>" as a WARNING and continues (Duplicati/Library/Utility/
# CommandLineArgumentValidator.cs; the only non-zero exits in Server/Program.cs are 100 for an
# unhandled exception and 102/103 for --webservice-password-init). So a typo in .env is a
# SILENT MISCONFIGURATION, not a start failure: the service comes up with the option ignored,
# and the only trace is a warning that reaches the configured log targets. This fails OPEN,
# which is the opposite of what this contract wants. Two consequences: (1) verify every .env
# option name against `duplicati-cli help advanced` and, for server-only names, against the
# string table of Duplicati.Server.Implementation.dll -- `--webservice-token-duration` is
# hyphenated even though the C# constant is OPTION_WEBSERVICE_TOKENDURATION; (2) after any
# .env change, grep the journal for "Unknown option supplied" before declaring the start good.
# AC-14 should pin that grep. (Lane B2 C6, corrected by round 2 Lane A.)
```

Downstream: §7.3.3's opening prose and any §9 acceptance criterion that leans on "fail closed" for `.env` need the same correction; the safety property has to be bought with a post-start journal check, because the product will not provide it.

### D-2 (WEAKENED). §7.3.2's `SystemCallFilter` rationale states a false premise; the conclusion survives.

Current text (doc line 617): `# @system-service excludes @privileged, which is where open_by_handle_at(2) lives.`

```
$ python3 expand_syscall_set.py @system-service open_by_handle_at name_to_handle_at
# transitive closure of @system-service: 395 syscalls
  open_by_handle_at        NOT in closure -> BLOCKED
  name_to_handle_at        ALLOWED (in closure)
# @privileged closure: 53 syscalls
# @system-service INTERSECT @privileged: 18
    capset, chown, chown32, fchown, fchown32, fchownat, lchown, lchown32, setfsuid,
    setfsuid32, setgroups, setgroups32, setresuid, setresuid32, setreuid, setreuid32, setuid, setuid32
# => '@system-service excludes @privileged' is FALSE (partial overlap)
```

This is also why `systemd-analyze security` prints `✗ SystemCallFilter=~@privileged … @privileged is included (e.g. chown is allowed)` — a reviewer will hit that row, read line 617, and conclude the design is wrong about the whole mechanism. It is not: `open_by_handle_at` really is blocked.

**Exact replacement text** for that one line:

```
# @system-service does NOT exclude @privileged wholesale -- 18 of @privileged's 53 calls are in
# its closure (@chown, capset, setfsuid/setgroups/setres*uid...), which is why
# `systemd-analyze security` prints a 0.2 "✗ SystemCallFilter=~@privileged (e.g. chown is
# allowed)" row. What it DOES exclude is open_by_handle_at(2) specifically: @system-service
# allows name_to_handle_at (make a handle) and not open_by_handle_at (use one). Verified on
# systemd 259 by expanding the set transitively, not from the direct member list.
```

### D-3 (WEAKENED). §7.3.6's server-util auth chain: `--password` pre-empts the database branch rather than following it.

Current text: "…a saved refresh token, else a signin token minted from a server database that is both **readable and decryptable** (`jwt-config` is an encrypted field, so this needs the settings key too), else `--password`, else `Utility.ReadSecretFromConsole("Enter server password: ")` — a console prompt **does** exist; `help` simply does not list it."

**Exact replacement text:**

```
…a saved refresh token; then, **only if `--password` was not given**, a signin token minted from a
server database that is both **readable and decryptable** (`jwt-config` is an encrypted field, so this
needs the settings key too — `Connection.cs:250-262` guards the whole branch with
`if (string.IsNullOrWhiteSpace(settings.Password))` and passes `settings-encryption-key` into
`Server.Program.GetDatabaseConnection`); then `--password`; then, if the password is still empty,
`Utility.ReadSecretFromConsole("Enter server password: ")` (`Connection.cs:304-305`). A console prompt
**does** exist; `help` simply does not list it — but it is `Console.ReadKey(true)`
(`Library/Utility/Utility.cs:2167`), so it throws "Cannot read keys when either application does not
have a console or when console input has been redirected" on any scripted, `systemd-run` or headless
invocation. Practical consequence: supplying `--password` makes server-util skip the database entirely,
so that route needs no settings key at all; and the prompt is not a usable automation channel, which is
the second reason the in-process client is the fix.
```

### D-4 (GAP, not a contradiction). §8's probe and recovery steps should state two gate behaviours.

Add to §8 step 3 / Procedures A0, A, A2, B, wherever a copy directory is passed:

```
Two behaviours of the 0700 gate that decide whether a step works (round 2 Lane A, measured on the
installed 2.4.0.0):
  - `duplicati-server-util` applies the gate and its refusal is COMPLETELY SILENT: exit 1, zero bytes
    on stdout and zero on stderr, before even the "Connecting to ..." line. If the probe copy directory
    is not mode 0700 owned by the invoking user or root, the command dies with no diagnostic at all.
    `chmod 700` the copy directory first, or pass `--allow-insecure-datafolder`.
  - `duplicati-database-tool` does NOT apply the gate at all, despite offering
    `--allow-insecure-datafolder` on every subcommand: it resolves the folder in
    `AccessMode.ProbeOnly`, documented in `DataFolderManager.cs` as "a no-op in ProbeOnly mode".
    `wipe-encryption --server-datafolder <0755 dir> --dry-run` runs normally with no override. Do not
    treat a successful `wipe-encryption` as evidence that the folder's permissions are acceptable to
    the server.
```

### D-5 (ADVISORY). `--webservice-tokenduration` does not exist.

The design does not use it, so nothing needs changing today. Record it where the option names are listed: the C# constant is `OPTION_WEBSERVICE_TOKENDURATION` but the option is `--webservice-token-duration` (`WebServerLoader.cs:117`, default `30D` at `:142`). Given D-1, a misspelling here would be ignored with a warning, not refused — so the token lifetime would silently stay at 30 days.

---

## Instrument adequacy — could this instrument have produced a different answer?

Three of my instruments could have, and one did.

**It did once.** My first 0700-gate probe (`test_datafolder_gate.bash`, `duplicati-database-tool verify --datafolder …`) returned `EXIT=0` for 0700, 0755, 0750 **and** the override cases — seven cases, all passing. That is a textbook non-discriminating result, and reading it as "the gate is lenient" would have been wrong in the opposite direction from round 1. The tell was that the *negative* case passed too. Reading `DataFolderManager.GetDataFolder` showed why: `PrepareSecureDataFolder` is called only under `AccessMode.ReadWritePermissionSet`, and `verify` resolves in `ProbeOnly`. The replacement probe (`duplicati-server-util` + a seeded `Duplicati-server.sqlite`) separates every factor, and the control run (`test_gate_control.bash`) varies mode and DB-presence one at a time, so the 0755-refusal is attributable to the mode alone. I am reporting the first probe as a discarded instrument rather than deleting it, because its failure mode is the same one that produced round 1's wrong verdict.

**The assembly scan can produce a false NOT-FOUND but not a false FOUND.** A name spelled as a runtime-composed string, or stored compressed in an embedded resource, would be invisible to a raw byte search. That is exactly the shape of the one NOT-FOUND I got, so I did not stop there: `enum_prefix.py` enumerated all 23 `webservice-*` strings and found the hyphenated neighbour, and the upstream `WebServerLoader.cs` then explained the discrepancy (constant name vs. constant value). Had I trusted the single scan, I would have reported "`--webservice-tokenduration` not found" without discovering that a *correctly spelled* option exists — a materially weaker answer. Conversely, a FOUND could in principle be a substring of some longer unrelated literal; `enum_prefix.py` anchors on `^prefix[a-z0-9-]*$`, and for the load-bearing names I confirmed the declaration site in source as well.

**The "@system-service excludes @privileged" check would have given the wrong answer** had I run only `systemd-analyze syscall-filter @system-service | grep open_by_handle_at` (a direct-member list — `@system-service`'s 62 entries are mostly nested groups) or only read `systemd-analyze security`'s ✗ row (which answers "does the allow list contain *any* `@privileged` call", an adjacent question, not "is `open_by_handle_at` reachable"). Both narrower instruments point away from the truth: the first would have missed nested members, the second says "@privileged is included" and would have made the design look wrong where it is right. Only the transitive closure separates the false premise from the true conclusion.

**D-1 is the claim I would most want a second opinion on**, and it is the one whose instrument is strongest: three independent lines agree — the source at the exact tag, an empirical run of the shipped binaries, and the design's own §4.3.9 observation that an unknown `--daemon-opts=…` did not stop the server. The one residual is that I exercised the validator through `duplicati-cli`, not `duplicati-server`. I bound that gap by showing the `"Unknown option supplied: "` literal exists in exactly one assembly (`Duplicati.Library.Utility.dll`) which `Duplicati.Server.Implementation.dll` references, so both binaries run the same compiled code — but I did not execute the server, by rule, and I say so rather than claiming I did.

**systemd**: the fetched source is upstream `v259`, not Ubuntu's `259.5-0ubuntu3.4`, and a distro patch to `path.c` would not appear in it. I bound that by confirming the four debug literals and three symbol names from that exact file in the shipped `libsystemd-core-259.so`. That establishes the functions exist and are named as upstream; it does not prove the predicate's *body* is unpatched. A stronger instrument would be the Ubuntu source package, which I did not fetch.

---

## What I could not determine

1. **Whether the server rejects an unknown option under a configuration I did not test.** I proved warn-and-continue from source and from `duplicati-cli`; I never ran `duplicati-server`. If the owner wants D-1 confirmed on the server itself, it needs a sandboxed run (`systemd-run` on a scratch `--server-datafolder`, a bogus option, a 30 s timeout) — which is a Lane-B-shaped action, not a Lane-A read.
2. **Whether the "Unknown option supplied" warning reaches the journal under the design's unit as written.** It is a `Log.WriteWarningMessage`, so visibility depends on `--log-level` / `--log-file` / `--log-console`, none of which the §7.3.2 unit or `/etc/default/duplicati` sets. I did not establish the default console/journal log level for a `duplicati-server` started under systemd. D-1's replacement text therefore prescribes a journal grep without promising the line will be there — that has to be verified once on the first post-recovery start.
3. **The non-read-only side effect of `wipe-encryption --dry-run`.** The design's §8/A2 says `--dry-run` is not read-only. My test database had no `Version` table, so the code returned at "Error reading database … no such table: Version" before reaching any backup-copy step. Confirming or refuting the side effect needs a structurally real server database, which I would not create under the read-only rule.
4. **Whether Ubuntu patched `path.c`.** See above — symbols and literals match upstream v259; the predicate body was not byte-verified against the distro source.
5. **The AES v2-vs-v3 KDF characterisation.** I confirmed `--aes-version` default 3, `--aes-v3-iterations` 300000, that `PBKDF2`/`Rfc2898`/`KdfIterations` are in the shipped `SharpAESCrypt.dll`, and that all 877 volumes are v2. I did **not** verify the design's specific claim that v2's KDF is "the legacy iterated SHA-256" — that lives in the third-party SharpAESCrypt, whose source I did not read. The decision-relevant half (v2 on disk, v3 by default, pin it) is fully established regardless.
6. **`--secret-provider` as an actual delivery channel for `--webservice-password-init`.** I confirmed the ordering (`ApplySecretProviderAsync` at `Program.cs:228`, before the init read) and that `libsecret`/`file-secret`/`env` providers are advertised by `duplicati-cli help secret`. I did not execute a `$name` substitution end-to-end, because doing so means starting a server.
7. **Whether any of the 15 ✗ rows changes once the unit runs against 2.4.0.0.** `systemd-analyze security --offline` is a static read of the unit file; the design's own note that "no directive has been executed against 2.4.0.0" still stands. In particular I cannot say whether `SystemCallFilter=@system-service` is sufficient for the .NET runtime under this workload — a filter that is too tight fails at runtime, not at verify time.

## Artifacts (scratch, `…/scratchpad/r2_A_product/`)

Scripts: `check_help_names.py`, `scan_assemblies.py`, `enum_prefix.py`, `dump_strings.py`, `fetch_src.py`, `read_aes_headers.py`, `expand_syscall_set.py`, `test_datafolder_gate.bash` (discarded — non-discriminating), `test_datafolder_gate2.bash`, `test_gate_control.bash`, `test_wipe_encryption_gate.bash`.
Captures: `help_cli_top.txt`, `help_cli_topics.txt`, `help_per_option.txt`, `help_serverutil{,_subs}.txt`, `help_dbtool{,_subs}.txt`, `scan_out.txt`, `enum_webservice.txt`, `aes_headers.txt`, `man_systemd_path.txt`, `path_v259.c`, `sec_offline.txt`, `syscall_closure.txt`, `gate2_out.txt`, `gate_control_out.txt`, `wipe_gate_out.txt`, `src/` (13 upstream files at the tag).

Nothing was written to the repository, to `/mnt/Backups/`, or to any live Duplicati data folder; `duplicati.service` was never started, stopped, reloaded or contacted (every probe used `--hosturl http://127.0.0.1:1/`).

<!-- markdownlint-enable -->

---

## Report B (actionability) — adversarial review; lens: the reconciled §8 runbook

Subagent id `a94c48d0a6519a0e0` (72,478 characters). Archived verbatim.

<!-- markdownlint-disable -->

I have everything. Writing up the report now.

---

# Consensus round 2 — Lane B (adversarial analysis review), lens: **ACTIONABILITY of the reconciled §8 runbook**

**Artifact reviewed**: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`, working-tree copy in worktree `buzzing-painting-meteor`, 1,882 lines, mtime 2026-09-22 02:31 (`git status`: `M` that file, `?? util/ad-hoc/2026-09-22_reconcile_backup_design.py`). Every citation below is anchored by **heading text**, never by line number.

**Inputs cross-read**: `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md` (reports B1 F1–F17 and B2 A1–A10 / D1–D22 in full), `prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-21_backup-systematization-design-arc.md`, `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-HANDOFF-CONSENSUS-RECORD.md`, and the repository's own instruments.

**Instruments I ran** (all read-only; nothing written outside my scratch dir; no server started; nothing under `/mnt/Backups/Ubuntu/` written): the design's `util/ad-hoc/2026-09-21_lint_design_snippets.py`; `bash -n` + `shellcheck -S style -o all` on the three new blocks; a synthetic-SQLite exercise of `2026-09-21_probe_settings_key_on_copy.bash` with a `systemd-run` tripwire; `util/ad-hoc/2026-09-21_env_file_shape.py` on `~/.config/duplicati-backup/env` (shape only, no value); a synthetic reproduction of `set -a; . <file>` against a stand-in with the same metacharacter classes; `systemd-analyze security --offline` on the extracted unit; `systemd-analyze syscall-filter`; a read-only `os.scandir` census of the destination against the guard's allow-list; a tool-availability probe; coreutils-idiom verification.

---

## 1. Claim table (one line per checked claim)

| # | Claim checked | Verdict | Command / evidence |
|---|---|---|---|
| 1 | All tagged blocks lint clean | **AGREE** | `python3 util/ad-hoc/2026-09-21_lint_design_snippets.py --doc <design> --workdir <scratch>/snips` → `tagged blocks found: 14` … `blocks: 14  failures: 0` |
| 2 | The three new/changed bash blocks pass `bash -n` + shellcheck | **AGREE** (with SC2310/SC2312 at `-o all`, see #12) | `shellcheck -S style -o all …2026-09-22_confirm_a0_premise.bash` → no output; `…restore_server_db_from_fileset.bash` → no output |
| 3 | Appendix B's block count matches the document | **AGREE** | 11 rows + the 3-in-1 T2 row = 14 = linter's count |
| 4 | Probe containment (2): refusal fires when `encrypted-fields != 'True'` | **AGREE** | synthetic cleartext DB → `REFUSING: copy is not encrypted (encrypted-fields='False', TargetURL prefix='file://').` `-> exit code: 3`, before any server start (tripwire never armed) |
| 5 | Probe containment (4): `DELETE FROM Schedule` runs before any server start | **AGREE** | encrypted variant reached `probing: control` only after the DELETE executed |
| 6 | Probe containment (3): "a random key MUST be rejected, or the test proves nothing" | **REFUTED — the control is vacuous** | tripwire `systemd-run` exited 97 (never started a server) and the script still printed `negative control rejected the random key (good)`; shellcheck `SC2310` on both `if try_key …` |
| 7 | "PASSPHRASE reaches duplicati-cli through the ENVIRONMENT, never through argv" (both A0 scripts) | **REFUTED — the scripts abort before `duplicati-cli` runs** | `2026-09-21_env_file_shape.py` on `~/.config/duplicati-backup/env` → `key='PASSPHRASE' … quoted=False metachars='$@&#'`; synthetic repro → `line 2: Zk: unbound variable`, subshell `rc=1` |
| 8 | `--no-local-db=true` is the safe way to avoid `--dbpath` doubt | **REFUTED on this host** | `util/ad-hoc/duplicati_drill_run.py:31-36`: *"`--no-local-db` rebuilds a temporary index from every dindex volume in the destination on **each** invocation — measured at >30 minutes for a single small file here, without completing."* |
| 9 | The probe's SQL containments are executable | **REFUTED — `sqlite3` is not installed** | `command -v sqlite3` → empty; `ls /usr/bin/sqlite3` → No such file; `dpkg -l sqlite3` → no packages found. Refusal then reads `encrypted-fields='', TargetURL prefix=''` — a misdiagnosis |
| 10 | `install_duplicati_service.bash` installs the guard from `util/yamaguchi-pre-backup-guard.bash` | **REFUTED — the file does not exist** | `ls util/yamaguchi-pre-backup-guard.bash` → MISSING; also MISSING: `util/systemd/duplicati.service`, `util/systemd/duplicati.default`, `util/install_duplicati_service.bash`, `util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash`, `util/ad-hoc/2026-09-22_confirm_a0_premise.bash`, `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash`, `util/ad-hoc/2026-09-21_backup_destination_permissions.bash`, `util/install_juniper_backup_timer.bash`, `util/juniper-backup-scheduled.bash` |
| 11 | "`/usr/lib/duplicati` is duplicati-owned 0755, and `/usr/bin/duplicati-*` are symlinks into it" | **AGREE** | `ls -lad /usr/lib/duplicati` → `drwxr-xr-x 21 duplicati duplicati`; `/usr/bin/duplicati-cli -> ../lib/duplicati/duplicati-cli` |
| 12 | P0.5 step 1 "before P0 **step 3** runs any Duplicati tool" | **DISAGREE — too late, and contradicts §4.1 note (b)** | §4.1 note (b) says "all of which root and `pcalnon` execute during **P0**"; P0 step 0(c) runs `duplicati-cli` |
| 13 | §7.3.2: "`@system-service` excludes `@privileged`, which is where `open_by_handle_at(2)` lives" | **AGREE** | `systemd-analyze syscall-filter @system-service \| grep open_by_handle_at` → not listed; `@privileged` → `open_by_handle_at` |
| 14 | AC-12 baseline "**5.2 MEDIUM** before the B3 directives" gates the hardened unit | **WEAKENED — unfalsifiable** | `systemd-analyze security --offline=true <extracted unit>` → **`1.7 OK`**. A unit with every B3 directive deleted scores 5.2 and still passes "at or below 5.2" |
| 15 | AC-12 "no ✗ row beyond those the design accepts" | **WEAKENED — no accepted-row list exists** | same run: **15** `✗` rows (`SystemCallFilter=~@privileged`, `AmbientCapabilities=`, `PrivateNetwork=`, `UMask=`, …); the design enumerates none |
| 16 | Guard allow-list matches the live destination | **AGREE** | read-only `os.scandir` census with the guard's four `-name` patterns → `877 entries; 0 would trip the guard` |
| 17 | `yamaguchi_server_api.py` hard-codes the checkout `.env` (§7.6) | **AGREE** | `CRED_FILE = "/home/pcalnon/Development/python/Juniper/juniper-ml/.env"`; `duplicati_api.py`: `PW_FILE = os.environ.get("DUPLICATI_PW_FILE", ".env")` — a **relative** path, worse than §7.6 states |
| 18 | Watchdog default `--backup-id 2` (step 7's warning) | **AGREE** | `util/ad-hoc/yamaguchi_watchdog.py:160` → `ap.add_argument("--backup-id", default="2")` |
| 19 | §7.8: "P3 adds `juniper-backup-failure.service`, whose reporter takes the unit name as `$1`" | **AGREE but already done** | `util/duplicati_backup_failure.bash:31` → `UNIT="${1:-duplicati-backup.service}"`; installed copy at `~/.local/bin/` is `IDENTICAL` |
| 20 | Header "Status: VALIDATED (round 2) … fully reconciled" | **REFUTED by §11 of the same document** | §11: *"reconciliation paused by the owner on 2026-09-21 before Lanes A1, B1, B2 and B3 were folded in"*; *"Lane A1 …, Lane B1 …, Lane B2 … and Lane B3 … are **not applied**"* |
| 21 | Header cites `JUNIPER_2026-09-22_…BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md` | **REFUTED — file does not exist** | `ls notes/ \| grep BACKUP-DESIGN` → only `…ROUND-1-RECORD.md` and `…STEP-REPORTS-RECORD.md` |
| 22 | "the warning at the top of §8" (§11 ×2, §12 ×2) | **REFUTED — dangling** | §8 opens with *"Phases are ordered; nothing in a later phase…"*; no warning block exists (the change list confirms "the STOP block **removed**") |
| 23 | O-3 / O-11 resolve to a defined open item | **REFUTED — collision and out-of-range** | `HANDOFF_2026-08-21_backup-systematization-design-arc.md` defines **O-0…O-8**; its **O-3** is *"PARTLY ANSWERED. Archive encryption uses YubiKey-backed public keys…"*, not "the confinement directives are untested". No O-11 anywhere |
| 24 | AC-2 is parameterised on the recovered job id (P0 step 7's instruction) | **REFUTED — AC-2 still reads `export 2`** | §9 AC-2 verification column: `python3 util/ad-hoc/yamaguchi_server_api.py status` and `export 2` |
| 25 | §3.3 rules 2, 7, 8, 11 and §7.1 principle 3 say what their citations claim | **AGREE** | all five targets read as cited |
| 26 | All `AC-`, `D-`, `S-`, `R-` identifiers resolve to a table row | **AGREE** | AC-1…AC-13 + 4 notes; D-1…D-14 + 3 notes; S-1…S-8 + 8 notes; R-1…R-19 — all present |
| 27 | coreutils idioms (`install -m 0600 /dev/stdin`, `stat -c '%U:%a'`, `install -d -o/-g`, `cmp -s`, `timeout -k`, `ls --time-style=full-iso`, `mktemp` with suffix) work on this host's **uutils coreutils 0.8.0** | **AGREE** | all six probes rc=0; `install -m 0600 /dev/stdin` → mode 600, round-trip length preserved after newline strip |
| 28 | `/etc/credstore` exists for P0 step 5's write | **AGREE** | `drwx------ 2 root root /etc/credstore` |
| 29 | `~/.local/bin/juniper-backup.bash` (the T2 scheduler's default `RUNNER`) exists | **REFUTED** | `ls ~/.local/bin/` → only `duplicati-backup-failure.bash`, `duplicati-scheduled-backup.bash` |
| 30 | Recorded dissent is recorded honestly | **AGREE** | §11 carries all six dissent items (specifier count 23=22+1; B3 prevails on the escrow; `.env` mode open; D-14 open; `ServerUtil/Connection.cs` settles for B1; the 44 alias-only refs vs the Companions list) |

---

## 2. DISAGREE section — defects, with exact replacement text

### D1. `set -a; . "${ENV_FILE}"` breaks **both** A0 scripts and leaks passphrase material to stderr

**Location**: §8 → *P0 — freeze and recover the job* → step **0**, tagged block `util/ad-hoc/2026-09-22_confirm_a0_premise.bash`; and step **4**, tagged block `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash`. Same pattern echoed in §7.5 rule 5.

**What an operator would do**: run the step-0(c) premise check, then the step-4 restore.

**What actually happens**: `~/.config/duplicati-backup/env` line 9 is **unquoted** and carries `$`, `@`, `&`, `#`:

```
  9: key='PASSPHRASE' export=False val_len=32 quoted=False has_eq=False metachars='$@&#'
 10: key='PASSPHRASE_OLD' export=False val_len=32 quoted=False has_eq=False metachars='$*%'
```
(`util/ad-hoc/2026-09-21_env_file_shape.py`, values never printed.)

Sourcing that under `set -euo pipefail` performs parameter expansion on `$…`. Reproduced with a synthetic 32-char stand-in of the same metacharacter classes:

```
--- what a subshell doing 'set -a; . file; set +a' actually exports ---
…/envtest/env-noamp: line 2: Zk: unbound variable
  subshell rc=1
--- with '&' also present ---
…/envtest/env-amp: line 2: Zk: unbound variable
…/envtest/env-amp: line 2: mB2#pL7xN4vC8jH5sD1gF: command not found
  subshell rc=127
```

So: **Procedure A0 — the design's *preferred* route, and the step-0 gate that decides whether A0 is available at all — cannot run.** Worse, `set -u` prints the identifier following the `$` to stderr, i.e. **a fragment of the live backup passphrase goes to the terminal and the journal** — the S-1/S-3 channel §6 exists to close. And the operator, seeing a bash error rather than a duplicati error, has no reason to suspect the credential file and will conclude A0's premise is untestable, routing to the key hunt / A2 / B.

The repository already holds the correct idiom: `util/ad-hoc/yamaguchi_build_job.py:57-63` **parses** this file with a regex rather than sourcing it — precisely because the value is shell-hostile. (The `set -a; .` form was inherited from `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-HANDOFF-CONSENSUS-RECORD.md` item 8; that document is wrong and this design baked it into two executable blocks.)

**Exact replacement** — in **both** blocks, replace

```bash
# PASSPHRASE reaches duplicati-cli through the ENVIRONMENT, never through argv.
(
    set -a
    # shellcheck source=/dev/null
    . "${ENV_FILE}"
    set +a
```
…through the closing `)` …with:

```bash
# PASSPHRASE reaches duplicati-cli through the ENVIRONMENT, never through argv -- and the
# credential file is PARSED, never SOURCED. The live PASSPHRASE is UNQUOTED and carries
# '$', '@', '&' and '#' (util/ad-hoc/2026-09-21_env_file_shape.py), so
# `set -a; . "${ENV_FILE}"` under `set -u` dies "<fragment>: unbound variable" -- printing a
# piece of the passphrase to stderr -- before duplicati-cli is ever reached, and with '&'
# present it also runs the tail of the value as a command.
# util/ad-hoc/yamaguchi_build_job.py:57-63 already parses this file the right way.
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
<the duplicati-cli invocation, unindented>
unset PASSPHRASE
```

Add to §7.5 rule 5, replacing *"(`PASSPHRASE`, sourced from a 0600 file in a subshell)"*:

> (`PASSPHRASE`, **parsed** out of a 0600 file and exported — never `.`-sourced: the live value is unquoted and contains `$`, `@`, `&` and `#`, so a source under `set -u` aborts and echoes part of the value.)

Also record the new fact in §4.1, which measures the *duplicati* `.env` shape but never the pcalnon one:

> | `~/.config/duplicati-backup/env` | 0600 `pcalnon:pcalnon`, 519 B | — | two active assignments, **both unquoted**: `PASSPHRASE` (32 chars, contains `$ @ & #`) and `PASSPHRASE_OLD` (32 chars, `$ * %`). **Not `.`-sourceable.** | `2026-09-21_env_file_shape.py` |

---

### D2. `--no-local-db=true` turns the step-0 gate into a >30-minute, possibly non-terminating operation

**Location**: §8 → P0 step **0**, and P0 step **4**'s restore block. Step 0 calls it *"one read-only command"*.

**What an operator would do**: run it and wait.

**What actually happens**: the repository's own instrument, written on this host, records the measurement:

> `util/ad-hoc/duplicati_drill_run.py:31-36` — *"Why `--dbpath` and not `--no-local-db`: `--no-local-db` rebuilds a temporary index from every dindex volume in the destination on **each** invocation — measured at >30 minutes for a single small file here, without completing. Pointing at a *copy* of the archived job database pays that cost once."*

877 volumes, 203 GB. The temp index also lands in `${TMPDIR:-/tmp}`, which is **tmpfs** on this host — against §3.3 rule 3's spirit and §7.3.2's own reason for moving `--tempdir` off tmpfs. And P0 step 1 has *already made* the copy that fixes it: `BMXWPAOGLP.sqlite` is inside `/home/duplicati/.cache/root-data-folder-2026-09-22`.

**Exact replacement** — in both blocks, replace the `--no-local-db=true` argument and the `TMPDB` line:

```bash
# Temp index on ext4, never tmpfs (design rule 3); /tmp here is tmpfs.
TMPDB="$(mktemp -u "${YAMAGUCHI_TMPDIR:-/home/duplicati/.cache}/a0-probe-XXXXXX.sqlite")"
# --dbpath at a disposable COPY of the archived job index, NOT --no-local-db:
# util/ad-hoc/duplicati_drill_run.py records --no-local-db rebuilding the index from every
# dindex volume, ">30 minutes for a single small file here, without completing".
JOBDB="${YAMAGUCHI_JOB_DB:-/home/duplicati/.cache/root-data-folder-2026-09-22/BMXWPAOGLP.sqlite}"
[[ -s "${JOBDB}" ]] || { echo "no job index at ${JOBDB} (run P0 step 1 first)" >&2; exit 2; }
cp -p "${JOBDB}" "${TMPDB}"
…
    duplicati-cli list "${DEST}" --version=0 "--dbpath=${TMPDB}" '*duplicati-server-db*'
…
rm -f "${TMPDB}" "${TMPDB}-wal" "${TMPDB}-shm" "${TMPDB}-journal"
```

and in step 0's prose replace *"Confirm Procedure A0's premise with one read-only command"* with:

> Confirm Procedure A0's premise with the read-only script below. **Run P0 step 1's freeze first** — the script needs the job index it copies aside. Expect it to finish in seconds against that index; if you drop `--dbpath` for `--no-local-db`, budget >30 minutes and expect it not to complete (`util/ad-hoc/duplicati_drill_run.py`).

*(This re-orders step 0 and step 1 — see D5.)*

---

### D3. The probe's negative control is vacuous, and it puts the candidate key on argv

**Location**: §8 → P0 step **3**, tagged block `util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash`, containment **(3)** and the `try_key` function.

**What an operator would do**: trust `negative control rejected the random key (good)` as proof the probe discriminates.

**What actually happens**: `try_key` ends `grep -q 'Server has started' "$log"`, and `set -e` is disabled inside it (shellcheck `SC2310` on both call sites). So **every** harness failure — `systemd-run` refusing a property, the 45 s `timeout` firing on a cold .NET start, `--uid=duplicati` failing, `duplicati-server` missing — reads as "key rejected". My tripwire proves it: `systemd-run` exited 97 without ever starting a server, and the script printed

```
negative control rejected the random key (good)
probing: candidate
KEY REJECTED (33 chars):
TRIPWIRE: systemd-run was invoked with: … -p Environment=SETTINGS_ENCRYPTION_KEY=a-candidate-key-value-not-printed …
```

A control that passes when the instrument is broken is not a control — and the consequence is directional: a **correct** key reported as rejected sends the operator to A2 (destructive on the copy) or B (full rebuild, new job id, every downstream default wrong).

The same output shows the second defect: `-p "Environment=SETTINGS_ENCRYPTION_KEY=${key}"` places the candidate key on `systemd-run`'s **argv** — world-readable in `/proc/*/cmdline` and recorded by systemd. That violates §7.1 principle 2 and R-18, which §7.3.6 enforces against `duplicati-server-util --password` two sections earlier. (The `SETTINGS_ENCRYPTION_KEY="${key}"` prefix on `timeout` is separately dead: a transient unit does not inherit the caller's environment.)

**Exact replacement** for `try_key` and the control:

```bash
# The key is delivered by a 0600 EnvironmentFile, never on argv: `-p Environment=<secret>`
# is world-readable in /proc/*/cmdline, which is the exposure 7.3.6 bans for
# duplicati-server-util --password.
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
    # A verdict needs a POSITIVE signal for BOTH outcomes. A harness failure (timeout 124,
    # systemd-run refusing a property, a missing binary) is neither, and must not read as
    # "rejected" -- that is the direction that loses a CORRECT key.
    if grep -q 'Server has started' "${log}"; then return 0; fi
    if grep -qE 'SettingsEncryptionKeyMismatchException|does not match current key' "${log}"; then return 1; fi
    echo "INDETERMINATE (${label}): rc=${rc}, neither 'Server has started' nor a Mismatch in ${log}" >&2
    echo "The probe did not run. Fix the harness before reading any verdict." >&2
    exit 5
}
```

and add a preflight after the euid gate (see D4):

```bash
command -v sqlite3 > /dev/null || { echo "sqlite3 is not installed; containments (2) and (4) cannot run" >&2; exit 2; }
```

---

### D4. `sqlite3` is not installed, and the probe's refusal then reads as "the main file is cleartext"

**Location**: same block, containments **(2)** and **(4)**.

**What an operator would do**: run the probe, read `REFUSING: copy is not encrypted (encrypted-fields='', TargetURL prefix='').`

**What actually happens**: `command -v sqlite3` → empty; `ls /usr/bin/sqlite3` → No such file; `dpkg -l sqlite3` → no packages found. Both SELECTs are wrapped `|| true`, so `flag` and `url` come back empty and the refusal fires **with a diagnosis that is false**. And it is false in the worst possible direction: §4.2, §5.4 and §11's *"What the evidence cannot support"* all tell the operator that **a cleartext main file would be a second key-free recovery source**. An operator handed "copy is not encrypted" will conclude they have found it.

**Exact replacement**: the `command -v sqlite3` preflight above, plus tighten the refusal message:

```bash
if [[ "${flag}" != "True" || "${url}" != "enc-v1:" ]]; then
    echo "REFUSING: the copy does not read as encrypted (encrypted-fields='${flag}', TargetURL prefix='${url}')." >&2
    echo "EMPTY values mean the QUERY failed, not that the copy is cleartext -- check sqlite3 and the copy." >&2
    echo "A probe against a genuinely unencrypted copy accepts ANY key and poisons the copy." >&2
    exit 3
fi
```

Add to §8 P0 step 1, after the `sudo ls -la --time-style=full-iso` sentence:

> `sqlite3` is **not installed on this host** (`dpkg -l sqlite3` → no packages found), so install it before step 3 or the probe's two containment queries return empty and its refusal misreports a query failure as a cleartext database.

---

### D5. P0.5 step 1 fires too late, contradicts §4.1 note (b), and cannot be executed as written

**Location**: §8 → *P0.5 — same session as the recovery…* → item **1**.

Two defects in one sentence:

> **`sudo chown -R root:root /usr/lib/duplicati`** except `data/` (kept as the frozen copy until P4) — **before P0 step 3 runs any Duplicati tool**.

(a) **The command includes what the sentence excludes.** `chown -R root:root /usr/lib/duplicati` chowns `data/`. There is no way to follow both halves.

(b) **"before P0 step 3" is too late.** P0 step **0(c)** runs `duplicati-cli`, which is `/usr/bin/duplicati-cli -> ../lib/duplicati/duplicati-cli` inside a `drwxr-xr-x duplicati duplicati` directory with no sticky bit. §4.1 note (b) says it correctly — *"all of which root and `pcalnon` execute during **P0**"* — so §8 and §4.1 disagree inside one document. P0 step 4's A0 restore runs `duplicati-cli` too.

(c) Structurally, P0.5 is printed **after** P0 while three of its six items are P0 preconditions. The preamble *"none of it depends on the recovery"* states the weaker, non-actionable half of the relation.

**Exact replacement** — P0.5 item 1:

> 1. **Return `/usr/lib/duplicati` to `root:root`, `data/` excepted** (`data/` is the frozen copy until P4) — **before P0 step 0(c), which is the first command that executes a Duplicati binary**. `/usr/bin/duplicati-*` are symlinks into a `duplicati:duplicati 0755` directory with no sticky bit, so the service user can rename any entry aside and drop in its own `duplicati-cli`, `duplicati-database-tool` or `duplicati-server` — all of which root and `pcalnon` execute during recovery (§4.1 note b). A recursive chown would take `data/` with it, so exclude it explicitly:
>
> ```bash
> sudo chown root:root /usr/lib/duplicati
> sudo find /usr/lib/duplicati -mindepth 1 -maxdepth 1 ! -name data \
>      -exec chown -R root:root {} +
> ```
>
> Also `sudo chown root:root /etc/default/duplicati` (today `duplicati:duplicati` 0644 — the service user can rewrite its own next argv), and remove `/home/duplicati/bin/` entirely.

and add to P0 step **0**, as a new first sentence:

> **Run P0.5 items 1 and 2 before anything in P0.** They take minutes, depend on nothing here, and item 1 closes a path by which the service user controls the very binaries steps 0(c), 3, 4 and 6 execute. P0.5 is printed after P0 only because it also contains work that follows the recovery.

---

### D6. Steps 4 (A0) and 6 (A2) never place their product; step 8 only moves the index

**Location**: §8 → P0 step **4** (*"Then install it as the data folder per step 8."*), step **6** (*"Then step 8."*), step **8** (*"Common to A0, A, A2 and B — move the index and re-point `DBPath` BEFORE the first run."*).

**What an operator would do**: follow A0, restore `Duplicati-server.sqlite` into a scratch directory, go to step 8 for the installation instruction.

**What actually happens**: step 8 contains exactly one `cp` and it is of `BMXWPAOGLP.sqlite`, the **index**. Only Procedure A (step 5) contains a copy of the server database into `/home/duplicati/.config/Duplicati`. For A0 the restored file is still in the operator's scratch directory, owned by `pcalnon`, and for A2 the wiped database is still in the step-1 freeze copy. The server then starts against the empty folder the installer created and the operator is back where they started — `0 backups`.

**Exact replacement** — insert as the first sentences of step 8, before *"The snapshot's `Backup` row carries…"*:

> **First, place the recovered database.** A0 and A2 produce a file, not a folder; Procedure A produced the folder in step 5 and B creates one in step 7. For **A0** and **A2**:
>
> ```bash
> sudo install -d -m 0700 -o duplicati -g duplicati /home/duplicati/.config/Duplicati
> sudo install -m 0600 -o duplicati -g duplicati \
>      <recovered>/Duplicati-server.sqlite /home/duplicati/.config/Duplicati/Duplicati-server.sqlite
> ```
>
> `<recovered>` is the A0 restore path (§8 step 4) or the wiped copy (step 6). Do **not** copy a `-wal`/`-shm` sibling alongside it: the recovered file is a clean, closed database and a stale WAL from another process would be replayed over it. Verify with the forensics script *after* the copy, as the `duplicati` user.

---

### D7. P0 step 9 calls the API client before step 10 creates the credential it reads

**Location**: §8 → P0 step **9** (*"Pause and resume go through `util/ad-hoc/yamaguchi_server_api.py` (extended with `pause`/`resume`)"*) and step **10** (*"write `~/.config/duplicati-backup/web-credential` (0600), and re-point **both** API clients at it"*).

§7.6 states the rule — *"P0 is ordered so that file exists **before** AC-2 runs"* — and the reconciliation moved alerting from after the proof to before it, which fixes AC-2. It does **not** fix step 9, which is the *earlier* consumer. `yamaguchi_server_api.py` hard-codes `CRED_FILE = "/home/pcalnon/Development/python/Juniper/juniper-ml/.env"`, and §6 S-5 records that value as *"now stale"*. So step 9's `pause`, the tempdir change and the `resume` all 401 — and `resume` is what fires the overdue first backup.

Also unassigned: *"(extended with `pause`/`resume`)"* is a code change with no PR, no step and no owner.

**Exact replacement** — renumber so alerting precedes the pre-run work, i.e. make today's step 10 the new step 9, and open the new step 10 with:

> 10. **Before the first run.** The credential file from step 9 must already exist and both clients must already read it — every command below goes through `util/ad-hoc/yamaguchi_server_api.py`, whose `CRED_FILE` is the primary checkout's `.env` until that PR lands, and whose value §6 S-5 records as stale. Land the client changes (credential path **and** the new `pause`/`resume` subcommands) in the same PR as §7.6's re-pointing, before P0 runs; a step 10 that reaches for a client that 401s cannot pause the scheduler, and the overdue schedule fires the moment the server is up.

---

### D8. Nothing in P0/P0.5 re-points or stops the snapshot lane; P2 step 3 does — so the design's own key-free fallback is silently wrong for a week

**Location**: §8 → P0 step **1** (copies the snapshot aside), P0.5 step **3** (*"Stop the snapshot timer … then restart the timer"*), P2 step **3** (*"Re-point `yamaguchi_server_db_snapshot.py` (§7.7) and redeploy the system timer"*).

**What an operator would do**: complete P0 and P0.5, leave the timer running as P0.5 step 3 instructs.

**What actually happens**: `yamaguchi_server_db_snapshot.py` keeps `SRC = /usr/lib/duplicati/data/Duplicati-server.sqlite` (§7.7). The timer is `enabled` (`systemctl list-unit-files` → `yamaguchi-server-db-snapshot.timer enabled enabled`). So every day at 13:45 UTC until P2 step 3, it overwrites `~/.local/state/duplicati-server-db/Duplicati-server.sqlite` with a copy of the **abandoned** database — the one whose fields are encrypted under the unidentified 09-18 key — and that file then rides into the 14:00 UTC fileset. Two consequences the plan does not name:

* If the operator has to re-run A0 later in the week, the on-disk copy and every fileset from the recovery onward hold the **wrong** database.
* AC-6 (*"Snapshot lane reads the new data folder"*) is unprovable until P2 step 3, and nothing says so.

**Second-order defect**: P0.5 step **2** installs the snapshot script as a root-owned copy under `/usr/local/lib/duplicati/` and changes `ExecStart`. P2 step 3 then says *"Re-point `yamaguchi_server_db_snapshot.py` … and redeploy the system timer"* — but after P0.5 step 2 the unit no longer executes the repository file, so editing it and reloading the timer changes nothing.

**Exact replacement** — P0.5 item 2, appended:

> Re-point `SRC` to `/home/duplicati/.config/Duplicati/Duplicati-server.sqlite` **in the same installed copy**, and install it disabled (`systemctl stop yamaguchi-server-db-snapshot.timer`) until P0 step 8 has placed the recovered database. Restart it only then. Leaving it pointed at `/usr/lib/duplicati/data` copies the **abandoned** database into `~/.local/state` and into every fileset until P2 — which silently destroys Procedure A0's own source for any later re-run, and makes AC-6 unprovable for a week.

and P2 item 3:

> 3. Confirm the snapshot lane: the **installed** copy under `/usr/local/lib/duplicati/` (not the repository file — P0.5 step 2 made the unit execute the copy, so a repo edit plus `daemon-reload` changes nothing) reads the new data folder, and the next 13:45 UTC snapshot lands with a fresh mtime. Re-run `util/install_duplicati_service.bash` — or the snapshot installer P0.5 step 2 names — to move a repository change into production.

---

### D9. Step 10 assumes web-UI access the plan never establishes

**Location**: §8 → P0 step **10** (*"Set the UI password (web UI)"*), against §7.3.6 (*"A recovered database carries the root-era UI password until it is changed"*) and §6 S-5 (the checkout `.env` credential is *"now stale"*).

For A0, A and A2 the recovered database's `server-passphrase`/`-salt` are hashes that `wipe-encryption` does not clear (B1 F13, carried correctly into step 6). So the UI password is the **root-era** one. The design bans `duplicati-server-util change-password` and `--password` (argv), and `--webservice-password-init` *"applies only while the password is still `AutogeneratedPassphrase`"* — which a recovered database is not. If the root-era value is not recoverable from S-5's stale file, **there is no documented route to step 10**, and step 9, AC-2, AC-5, AC-9 and AC-13 all sit behind it.

**Exact replacement** — add to §7.3.6, after *"A recovered database carries the root-era UI password until it is changed."*:

> **If that password is not known, none of the routes above applies** — `--webservice-password-init` refuses a non-autogenerated password and the argv routes are banned. The recovery path is to clear the stored hash on the *copy* before it is installed, so the server treats it as autogenerated again: with the server stopped, `DELETE FROM Option WHERE BackupID=-2 AND Name IN ('server-passphrase','server-passphrase-salt','server-passphrase-trayicon','server-passphrase-trayicon-hash');` then `--webservice-password-init` on a single hand start. Record this as a step, not a footnote: P0 step 10 is otherwise unreachable for Procedures A0, A and A2.

and to P0 step 10, as the first sentence:

> Confirm first that you can authenticate to the recovered server at all (§7.3.6). A0/A/A2 carry the root-era UI password; if it is unknown, clear the stored hash on the copy **before** step 8 installs it.

---

### D10. D-14 is a fifth decision P0 applies provisionally, and step 0(a) does not name it

**Location**: §8 preamble (*"P0 applies the recommendations of D-1 …, D-4 …, D-6 … and D-9 … before the owner has ruled"*), P0 step **0(a)**, against §7.1 principle 5, §7.3.2's `UMask=0007`, and §10 D-14.

§7.1 principle 5 and the unit's `UMask=0007` encode the **group-write** model. D-14 recommends the **read-only** form with `UMask=0027`. P0 step 8 installs that unit; a read-only ruling therefore means re-installing it — exactly the cost step 0(a) exists to surface for D-1/D-4/D-6/D-9. `systemd-analyze security` flags it independently: the unit's single remaining style failure is `✗ UMask= — Files created by service are group-writable by default`.

The same applies to **D-2**, marked *"Re-decide"* in §10 but re-decided only in **P1 step 5** — after P0 has already run a full backup under the passphrase whose exposure is in question.

**Exact replacement** — §8 preamble, first paragraph:

> …P0 applies the recommendations of D-1 (credstore + `--require-db-encryption-key`), D-4 (`AmbientCapabilities`), D-6 (installed copy), D-9 (loopback) **and D-14 (the unit's `UMask=`, which the §7.3.2 unit sets to the group-write value `0007` while D-14 recommends the read-only `0027`)** before the owner has ruled on any of them. **D-2 is a sixth**: P0 step 11 runs a full backup under the passphrase D-2 asks whether to retire, and P1 step 5 re-decides it afterwards. Either rule those six first, or accept that P0 applies them **provisionally** — a contrary ruling on D-1/D-4/D-6/D-9/D-14 means re-installing the unit, and a contrary ruling on D-2 means the first post-recovery fileset is written under a passphrase that is then replaced. Step 0 makes that explicit.

and P0 step 0(a): *"Rule D-1, D-4, D-6, D-9 **and D-14**, and decide whether D-2 is re-decided before or after the first run, or record that P0 applies their recommendations provisionally."*

---

### D11. P0 step 3's hash-probe instruction does not produce an invocable command, and its candidate file is one the probe ignores

**Location**: §8 → P0 step **3**: *"run `util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py` against the **copy** from step 1 (usage in its docstring) … **Feed any new candidate ALONE on stdin** … Write the candidate with `set +o history; read -rs key; install -m 0600 /dev/stdin <file> <<<"$key"`"*.

Three problems, from the probe's own source:

* Its signature is `WRAPPER = sys.argv[1]; PC_ENV = sys.argv[2]; DBS = sys.argv[3:]`, and each DB is `label=path` (`spec.split("=", 1)`). "Run it against the copy" with one argument raises `IndexError`; with a bare path it raises `ValueError`.
* **Stdin is parsed as a `.env` file.** The only stdin lines it reads are `SETTINGS_ENCRYPTION_KEY=` / `PASSPHRASE=` / `PASSPHRASE_OLD=`, commented or active. A file written by `install -m 0600 /dev/stdin <file> <<<"$key"` holds a **bare value** and matches none of them — the probe loads no new candidate and prints `NONE of the candidates/variants`. A vacuous negative at the single decision point that routes the whole recovery.
* *"It needs no root"* is false for the copy step 1 makes: `/home/duplicati/.cache` is `drwx------ duplicati duplicati`, so neither `pcalnon` nor `sg duplicati` can traverse it.

(The one claim that **does** hold: `ENV_ACTIVE_KEY` is overwritten by each later active line, so *"the probe keeps only the last uncommented `SETTINGS_ENCRYPTION_KEY=` line"* — **AGREE**.)

**Exact replacement** for that passage:

> …so run `util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py` against the **copy** from step 1. It takes three argument groups and reads a `.env` on stdin, so the invocation is:
>
> ```bash
> sudo cat /home/duplicati/.cache/root-data-folder-2026-09-22/../candidate.env | \
>   sudo python3 util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py \
>     scripts/duplicati-wrapper.bash ~/.config/duplicati-backup/env \
>     frozen=/home/duplicati/.cache/root-data-folder-2026-09-22/Duplicati-server.sqlite
> ```
>
> It needs **root** — the copy sits in `/home/duplicati/.cache`, mode 0700 `duplicati` — but no server and no live database. It has already excluded every candidate this design named (§5.4). **A new candidate must be written as a `SETTINGS_ENCRYPTION_KEY=<value>` line, not as a bare value**: stdin is parsed as a `.env`, and a bare-value file loads no candidate and prints a vacuous `NONE`. Feed it alone, because only the **last** uncommented `SETTINGS_ENCRYPTION_KEY=` line survives. Write it with `set +o history; read -rs key; printf 'SETTINGS_ENCRYPTION_KEY=%s\n' "$key" | sudo install -m 0600 /dev/stdin <file>; unset key` — **never** `printf '%s' '<value>' > file` at a root prompt.

---

### D12. Every repository path §8 invokes is absent, and no step creates any of them

**Location**: §8 throughout; Appendix B.

| Path §8 tells the operator to run / install | In the repo? |
|---|---|
| `util/ad-hoc/2026-09-22_confirm_a0_premise.bash` (P0 step 0) | **no** |
| `util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash` (P0 step 3) | **no** |
| `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash` (P0 step 4) | **no** |
| `util/install_duplicati_service.bash` (P0 step 8) | **no** |
| `util/yamaguchi-pre-backup-guard.bash` (installer's `GUARD_SRC`) | **no** |
| `util/systemd/duplicati.service`, `util/systemd/duplicati.default` (installer) | **no** |
| `util/ad-hoc/2026-09-21_backup_destination_permissions.bash` (P2 step 2) | **no** |
| `util/juniper-backup-scheduled.bash`, `util/install_juniper_backup_timer.bash` (P3 step 2) | **no** |

**What happens on the installer's first run** specifically: `for f in "${WRAPPER_SRC}" "${UNIT_SRC}" "${DEFAULTS_SRC}" "${GUARD_SRC}"; do [[ -f "${f}" ]] || { echo "missing source: ${f}"; exit 2; }` — it exits 2 naming `util/yamaguchi-pre-backup-guard.bash` (and, on a fresh tree, the two `util/systemd/` files). That is fail-closed and correct behaviour for the script; the defect is that §8 step 8 presents `util/install_duplicati_service.bash` as a thing to run, on the day of the recovery, when the PR creating it has not landed.

There is also a spelling gap: §7.3.4's prose names the repository source of the unit, the defaults file and the guard, then says *"the install script refuses to run unless all four exist"* — the **wrapper's** repository path (`scripts/duplicati-wrapper.bash`, per `WRAPPER_SRC` and P1 step 3) is the fourth and is never named in that sentence.

**Exact replacement** — §8 preamble, as a new second paragraph:

> **Nine of the paths below do not exist yet.** §8 names `util/install_duplicati_service.bash`, `util/yamaguchi-pre-backup-guard.bash`, `util/systemd/duplicati.{service,default}`, `util/ad-hoc/2026-09-22_confirm_a0_premise.bash`, `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash`, `util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash`, `util/ad-hoc/2026-09-21_backup_destination_permissions.bash`, `util/juniper-backup-scheduled.bash` and `util/install_juniper_backup_timer.bash`. All nine exist today only as tagged blocks in this document. **P0 step −1 is to land them**, extracted with `util/ad-hoc/2026-09-21_lint_design_snippets.py` (Appendix B gives the block→path map) and reviewed in a PR — not pasted onto a root prompt during the recovery.

and §7.3.4's sentence: *"`util/systemd/duplicati.service` and `util/systemd/duplicati.default` are the repository copies of the two files shown in §7.3.2, `scripts/duplicati-wrapper.bash` is the repository source of the wrapper shown in §7.3.3, and `util/yamaguchi-pre-backup-guard.bash` is the repository source of the guard shown in §7.5; the install script refuses to run unless all four exist."*

---

### D13. A0 restores a **cleartext** server database and nothing keeps it out of the backup source, or removes it afterwards

**Location**: §8 → P0 step **4** (*"Restore that **one file** to a scratch directory"*), the `restore_server_db_from_fileset.bash` block, and §8 P4 (which cleans `/usr/lib/duplicati/data` and `Duplicati.empty-2026-09-20` and nothing else).

The restored file is the pre-09-18 root database — the design's own §3.3 rule 8 says the server database *is* key material, and §5/Appendix C item 3 say this particular one holds the passphrase **in cleartext**. The script takes `$1` unchecked. The obvious scratch directory for an operator working as `pcalnon` is under `/home/pcalnon/`, which is the backup **Source** — so the next run ingests a cleartext passphrase file into the archive. That is S-7's exact shape, and P4 step 1 already articulates the rule for the analogous tar.

**Exact replacement** — in the block, after `OUT="${1:?…}"`:

```bash
# The restored file is a CLEARTEXT server database: it carries the job passphrase (rule 8,
# Appendix C item 3). It must not land inside the backup Source, or the next run archives it
# -- the S-7 shape, and the rule P4 step 1 states for the analogous tar.
case "$(readlink -f "${OUT}")/" in
    /home/pcalnon/*) echo "refusing: ${OUT} is inside the backup Source" >&2; exit 2 ;;
esac
```

and at the end of step 4, after *"Then install it as the data folder per step 8."*:

> Then **shred the restore directory**: `sudo find <restore-dir> -type f -exec shred -u {} + && sudo rmdir <restore-dir>`. Nothing later in this plan removes it, and until it is gone it is a cleartext copy of the passphrase on disk — the sink §6's checklist exists to enumerate.

---

### D14. P0 step 9's guard dry-run passes the one check §7.5 says is the guard's real value — vacuously

**Location**: §8 → P0 step **9**: `sudo -u duplicati DUPLICATI__REMOTEURL=file:///mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi /usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash; echo $?` (same form printed by `install_duplicati_service.bash`).

Two problems:

* The `TargetURL` check compares `${DUPLICATI__REMOTEURL%/}` against `file://${DEST_DIR}`. In the dry-run the operator **supplies both sides**, so it can only agree. §7.5 item 6 says *"The guard's real value is the **mount** and **`TargetURL`** checks"* — the dry-run proves the mount and the stray census (that one is real: my read-only census of the live destination gives `877 entries; 0 would trip the guard`) and proves nothing about the `TargetURL` comparison against what Duplicati actually exports.
* `sudo -u <user> VAR=value <cmd>` requires the sudoers `setenv` tag or `env_keep`; with Ubuntu's default `Defaults env_reset` and no `setenv`, sudo refuses: *"sorry, you are not allowed to set the following environment variables"*. I could not execute this (no passwordless sudo), so it is a probable, not a proven, failure — but the `env` form costs nothing.

**Exact replacement** — step 9:

> Before `resume`, dry-run the guard as the service user:
>
> ```bash
> sudo -u duplicati env \
>   DUPLICATI__REMOTEURL="$(python3 util/ad-hoc/yamaguchi_server_api.py export <id> \
>                           | python3 -c 'import json,sys; print(json.load(sys.stdin)["Backup"]["TargetURL"])')" \
>   /usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash; echo "guard exit=$?"
> ```
>
> `env` rather than a bare `VAR=value` prefix (sudoers refuses the prefix under the default `env_reset` with no `setenv`), and the URL read **from the job** rather than typed: a hand-typed URL makes the guard's `TargetURL` comparison compare the operator's string with itself, which is the one check §7.5 item 6 says the guard exists for. Require exit 0: it is `--run-script-before-**required**`, so a missing or failing guard aborts the first backup, which `resume` fires immediately.

---

### D15. The guard's `unset` list is incomplete by the design's own standard

**Location**: §7.5, `usr/local/lib/duplicati/yamaguchi-pre-backup-guard.bash`: `unset DUPLICATI__passphrase SETTINGS_ENCRYPTION_KEY`.

§6 S-8 rules that the `additional-report-url` bearer JWT **is a credential**. `RunScript.cs` exports *every* job option, so `DUPLICATI__additional_report_url` is in the guard's environment and passes to `mountpoint`, `find` and `id` — the precise argument the block's own header makes for the two names it does unset. The case of option-derived names is also unverified (built-ins are upper-case; option-derived ones follow the option's case), and an `unset` that names the wrong case silently does nothing.

**Exact replacement**:

```bash
# Duplicati's RunScript exports EVERY job option into this script's environment, unfiltered and
# prefixed DUPLICATI__ -- the job passphrase and the additional-report-url bearer JWT (S-8) among
# them -- and the wrapper's exported settings key is inherited too. All of them would pass to
# every child (mountpoint, find, id). Drop them before anything else runs, in BOTH cases:
# built-in names are upper-case, option-derived names follow the option's own case, and an
# unset that names the wrong spelling silently does nothing. (Lane B3 F-4; S-8.)
unset DUPLICATI__passphrase DUPLICATI__PASSPHRASE \
      DUPLICATI__additional_report_url DUPLICATI__ADDITIONAL_REPORT_URL \
      SETTINGS_ENCRYPTION_KEY
```

---

### D16. Cross-reference integrity — dangling and mis-aimed references

All by heading text. Each was checked against its target.

| # | Where | Says | Target actually |
|---|---|---|---|
| a | Header **Status** | "VALIDATED (round 2) … COMPLETE and **fully reconciled**: every Lane A1, A2, A3, B1, B2 and B3 correction is applied or recorded as dissent in §11" | **§11 says the opposite**: *"reconciliation paused by the owner on 2026-09-21 before Lanes A1, B1, B2 and B3 were folded in"* and *"Lane A1 …, Lane B1 …, Lane B2 … and Lane B3 … are **not applied**"*. The only place a reader checks whether §8 is safe to execute now contradicts the banner authorising it. |
| b | Header **Status** | cites `JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md` | **does not exist** (`ls notes/`) |
| c | Header **Status** | "the owner gates in §8's **preamble**" | the gates are **P0 step 0**; the preamble names the decisions but issues no gate |
| d | §11 ×2, §12 ×2 | "the warning at the top of §8", "the §8 warning" | **no warning exists** — the STOP block was removed |
| e | §12 last row | "§8 warning (**steps 3/5/7/9**; Procedure A0; …)" | old numbering. P0 is now 0–11 plus P0.5; today's 3/5/7/9 are the hash test / Procedure A / Procedure B / pre-first-run |
| f | §11 | "**P1 step 2's `chmod 0600`** (B2 D15)" applied | P1 step 2 now reads *"**Mode: `0640 root:duplicati` as recommended**, or `0600 duplicati:duplicati`"* — the stated applied change is no longer what the target says |
| g | §7.3.2, AC-12a | "open item **O-3**" | `HANDOFF_2026-08-21_backup-systematization-design-arc.md` defines **O-0…O-8**, and its **O-3** is *"PARTLY ANSWERED. Archive encryption uses YubiKey-backed public keys…"*. §3.4 and §11 cite that same O-numbering, so a reader resolving O-3 lands on a different item. |
| h | §7.5 | "open item **O-11**" | out of range — no O-9, O-10 or O-11 exists anywhere in the arc |
| i | P0 step 7 | "the deployed watchdog, `yamaguchi_census.py`, AC-2, AC-5 and **step 10** all default to 2" | **step 10 does not** — it reads *"Redeploy the watchdog with `--backup-id <id>`"*. **AC-2 does**, and was not updated |
| j | §9 AC-2 | verification `… and `export 2`` | contradicts step 7's *"pass it explicitly everywhere, including AC-2"* |
| k | §12 | no row for the 2026-09-22 reconciliation; no row listing `util/ad-hoc/2026-09-22_{confirm_a0_premise,restore_server_db_from_fileset}.bash` or `2026-09-22_reconcile_backup_design.py` | §11 claims "§0 instrument list and §12 file list (B2 D22)" were applied; §0 names the reconcile script, §12 names none of the three |
| l | §8 step 4 | "matched by none of the **45** filters (YAM §8.19.3)" | B1's verbatim quote of YAM §8.19.3 says *"verified against all **44** filters"*. The snapshot itself carries 45; the **citation** is to a 44-filter statement |
| m | §7.8 | "P3 adds `juniper-backup-failure.service`, whose reporter takes the unit name as `$1`" | already true: `util/duplicati_backup_failure.bash:31` → `UNIT="${1:-duplicati-backup.service}"`, and the installed `~/.local/bin/` copy is byte-identical |

**Exact replacement for (a)/(b)/(c)/(d)** — header **Status** block:

> **Status**: ROUND-2 RECONCILED — consensus round 1 (six validators) is applied in full or recorded as dissent in §11; round 2 (four lanes) has reported and its corrections are reflected here. Verbatim reports: `JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`. **Round 2's verbatim reports are not yet archived**; when they are, the file is `JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md` and this line names it. §8 may be executed once **P0 step −1** has landed the nine scripts it invokes and **P0 step 0's owner gates** are cleared; nothing under `/mnt/Backups/Ubuntu/` is deleted or moved except the one escrow copy named in P1 step 4.

and §11's first line must be rewritten to match, replacing *"reconciliation paused by the owner on 2026-09-21 before Lanes A1, B1, B2 and B3 were folded in"* and the whole *"are **not applied** — except…"* clause with the actual applied/dissent split. Every *"the warning at the top of §8"* becomes *"the owner gates in §8 P0 step 0"*.

**For (g)/(h)** — either renumber to `O-12` / `O-13` (continuing past the handoff's O-8) **and add an open-item table to §11**, or drop the O-prefix: *"open item **O-12** (this document's numbering continues `HANDOFF_2026-08-21_backup-systematization-design-arc.md`'s O-0…O-8)"*.

**For (i)/(j)** — P0 step 7: *"…the deployed watchdog, `yamaguchi_census.py`, AC-2 and AC-5 all default to 2 (step 10 already takes `--backup-id <id>`)."*; §9 AC-2 verification: `` `python3 util/ad-hoc/yamaguchi_server_api.py status` and `export <id>` (2 unless step 7 assigned another — record it in the validation record) ``.

---

### D17. AC-12's numeric gate is satisfied by the unit it exists to protect

**Location**: §9 AC-12 — *"reports an exposure at or below the §7.3.2 unit's offline baseline (**5.2 MEDIUM** before the B3 directives) and no ✗ row beyond those the design accepts"*.

Measured on the extracted unit:

```
→ Overall exposure level for duplicati.service: 1.7 OK 🙂
```

The B3 confinement set moves the score from 5.2 to **1.7**. "At or below 5.2" is therefore passed by a unit with `IPAddressDeny`, `SystemCallFilter`, `ProtectProc`, `ProcSubset`, `PrivateDevices`, `ProtectClock`, `ProtectHostname`, `ProtectKernelLogs` and `RestrictNamespaces` **all deleted** — the exact silent drop AC-12a says must never happen. And *"no ✗ row beyond those the design accepts"* has no list to compare against; the run produces **15** `✗` rows, including four the design necessarily accepts (`AmbientCapabilities=`, `CapabilityBoundingSet=~CAP_(DAC_*|…)`, `SystemCallFilter=~@privileged` — a broad test that does **not** contradict §7.3.2's narrower and correct `open_by_handle_at` claim — and `RestrictAddressFamilies=~AF_(INET|INET6)`).

**Exact replacement** — AC-12 criterion cell:

> `systemd-analyze security duplicati.service` reports an exposure **at or below 2.0** — the §7.3.2 unit as designed measures **1.7 OK** offline, against **5.2 MEDIUM** for the same unit without the round-1 Lane B3 directives, so a 5.2-shaped gate would pass a unit with every one of them deleted — and **no ✗ row outside this accepted set**: `AmbientCapabilities=`, `CapabilityBoundingSet=~CAP_(DAC_*|FOWNER|IPC_OWNER)`, `SystemCallFilter=~@privileged` (a set-wide test; `open_by_handle_at` is specifically absent from `@system-service`, verified with `systemd-analyze syscall-filter`), `SystemCallFilter=~@resources`, `RestrictAddressFamilies=~AF_UNIX`, `RestrictAddressFamilies=~AF_(INET|INET6)`, `PrivateNetwork=`, `PrivateUsers=`, `ProtectHome=`, `RootDirectory=/RootImage=`, `RemoveIPC=`, `MemoryDenyWriteExecute=`, `DeviceAllow=`, `IPAddressDeny=` and `UMask=` (the last pending D-14). The server completes AC-3 under every confinement directive the unit sets — one it cannot run under is removed **and recorded**, never silently (note AC-12a).

---

### D18. Acceptance criteria as a set — what cannot be executed in the order P0 leaves the system in

| AC | Executable after P0? | Blocker |
|---|---|---|
| AC-1 | no (by design) | `NRestarts=0` over 24 h; correctly omitted from step 11 |
| AC-2 | yes, **but** | `export 2` is wrong after Procedure B (D16 i/j); needs the step-9/10 credential (D7) |
| AC-3 | yes | its pre-flight `systemd-run -p AmbientCapabilities=… cat ~/.ssh/known_hosts` sits in note AC-3a marked "owner action — it needs root" and **no P0 step schedules it**; the capability is untested when the run starts |
| AC-4 | yes | drills `duplicati-20260918T140000Z`; unaffected by D2 because `yamaguchi_drill_watch.bash` exists and uses `--dbpath` |
| AC-5 | 3 days | fine |
| AC-6 | **no, until P2 step 3** | D8 — the snapshot lane still reads `/usr/lib/duplicati/data`; nothing in §9 or §8 records that AC-6 is a P2 criterion |
| AC-7 | no, until P2 step 2 | depends on **D-14**, unruled |
| AC-8 | partly | `gitleaks` is **not installed** (`command -v gitleaks` → empty); the P0.5 step 6 rule can only be exercised through the pre-commit hook that same step adds. `.gitleaks.toml` exists; `.pre-commit-config.yaml` has no gitleaks hook |
| AC-9 | yes | needs the step-10 credential; `yamaguchi_reboot_verify.bash` calls `yamaguchi_server_api.py` |
| AC-10 | **no** | D19 below |
| AC-11 | no | depends on **D-5**, unruled |
| AC-12 | **instrument missing** | *"`systemd-run` trial on **the probe copy** first"* — the probe copy `/home/duplicati/.cache/keyprobe` exists only if step 3's *confirmation-only* server probe ran, which step 3 says is not the route. Name the step-1 freeze copy instead |
| AC-13 | yes | fine |

**Exact replacement** for AC-12's verification cell: `` `systemd-analyze security`; journal of the first start; `systemd-run` trial against the P0 step 1 freeze copy (`/home/duplicati/.cache/root-data-folder-2026-09-22`) — **not** the step 3 probe copy, which exists only if the confirmation probe was run ``.

**Exact replacement** for AC-6's criterion cell, prefixed: *"**(P2 criterion — not provable at the end of P0; see P0.5 step 2.)** Snapshot lane reads the new data folder…"*.

---

### D19. Tier 2 cannot produce the OK run P3 step 2 requires, because nothing installs the runner

**Location**: §7.8 (`ExecStart=%h/.local/bin/juniper-backup-scheduled.bash`; scheduler `RUNNER="${JUNIPER_BACKUP_RUNNER:-${HOME}/.local/bin/juniper-backup.bash}"`), P3 steps **1** and **2**, AC-10.

* `ls ~/.local/bin/` holds `duplicati-backup-failure.bash` and `duplicati-scheduled-backup.bash` only. **`juniper-backup.bash` is not there**, so the scheduler's first act is `log "FATAL: runner missing: …"; write_status FAILED`.
* P3 step 1 says *"Add the absolute-mount-root form to `util/juniper-backup.bash`"* — the **repository** file. The unit runs `~/.local/bin/`. Nothing in §7.8 or P3 says the runner is copied there, and `util/install_juniper_backup_timer.bash` (which would do it) is a step-2 deliverable that does not exist. So step 1's fix cannot reach production before step 2, while step 1 is explicitly ordered first.
* P3 step 2 names *"the four user units (timer, path, service, **failure**)"* but only **three** are tagged blocks; `juniper-backup-failure.service` and its reporter installation are prose only.
* The failure reporter writes to `${DUPLICATI_STATE_DIR:-${HOME}/.local/state/duplicati}` and tails that lane's `last-run.status`; AC-10 verifies `~/.local/state/juniper-backup/last-run.status`. A `juniper-backup-failure.service` that does not set `Environment=DUPLICATI_STATE_DIR=%h/.local/state/juniper-backup` reports on the wrong lane — the same defect §7.8 identifies in `duplicati-backup-failure.service` and then reproduces.

**Exact replacement** — P3 steps 1–2:

> 1. **Fix the runner's mount root first, and install it.** Add the absolute-mount-root form to `util/juniper-backup.bash` (a `MEDIA_NAMES` entry beginning with `/` is taken as an absolute mount root) and have the scheduler and the runner read **one** mount-root setting. The scheduler executes `~/.local/bin/juniper-backup.bash`, which **does not exist today** — `util/install_juniper_backup_timer.bash` (step 2) must copy the runner, the scheduler and the failure reporter into `~/.local/bin/`, as `util/install_duplicati_timer.bash` already does for the old lane. Until both land, every "due" run ends `FATAL: runner missing` or `FAILED runner rc=1` and step 2 cannot produce its own OK run (§4.5, §7.8).
> 2. Land `util/juniper-backup-scheduled.bash`, `util/install_juniper_backup_timer.bash`, the three user units above **and** `juniper-backup-failure.service` — which must carry `Environment=DUPLICATI_STATE_DIR=%h/.local/state/juniper-backup` and `ExecStart=%h/.local/bin/duplicati-backup-failure.bash juniper-backup.service`, or it records the failure into the *duplicati* lane's `failures.log` and tails that lane's `last-run.status`, which is the defect this unit exists to avoid. The reporter already takes the unit name as `$1` (`util/duplicati_backup_failure.bash:31`) — no reporter change is needed. Install; enable; observe one SKIPPED (unplugged) and one OK (plugged) run; watch `systemctl --user status juniper-backup.path` for 30 s after the plug-in; class-1 drill.

---

### D20. Things an operator would reasonably misread

* **"the copy" is ambiguous — step 1 makes two.** Step 1 freezes `/usr/lib/duplicati/data` **and** copies the snapshot aside. Steps 3 and 6 say *"the copy from step 1"*. Worse, step 3's own script defaults `SRCDIR="${SRCDIR:-/usr/lib/duplicati/data}"` — it re-copies from the **live** folder, not from step 1's frozen copy, contradicting the sentence that introduces it. Fix: call them "the **data-folder freeze**" and "the **snapshot copy**" throughout, and set the probe's `SRCDIR` default to the freeze path.
* **The port is declared in two artifacts.** `etc/default/duplicati` sets `DAEMON_OPTS="--webservice-port=8300 …"` and the `.env` block ends `--webservice-port=8300`. `DAEMON_OPTS` wins (precedence 3 over 2), so changing the `.env` line has no effect — against §7.1 principle 1, in the design's own files. Delete the `.env` line or comment it as inert.
* **"the one moved aside in step 2" is `Duplicati.empty-2026-09-20` while step 1's freeze is `root-data-folder-2026-09-22`.** Two dates, two conventions, in adjacent steps; the 09-20 refers to the folder's birth and the 09-22 to the copy's. State that.
* **P0.5 step 5 "start the S-4 copy-out" vs P1 step 4 "the procedure of record".** P1 step 1 is explicitly flagged *"(Executed in P0.5 step 3 — kept here as the procedure of record.)"*; P1 step 4 is not, so it reads as a second, independent copy-out. Flag it the same way.
* **`util/juniper-backup-scheduled.bash` vs `%h/.local/bin/juniper-backup-scheduled.bash`** — one artifact, two spellings, no stated copy step (D19).
* **`--version=0` is correct only while no backup has run.** Step 0's note justifies it ("it is the newest"). Both A0 scripts depend on that and neither asserts it. Add `duplicati-cli list … --version=0` output inspection, or assert the expected `20260918T140000Z` dlist name before restoring.
* **The A0 verification list will look wrong.** Step 4 says to expect *"`LastBackupDate` … one day stale"*, and Appendix A.2 records `LastBackupDate=20260918T140000Z` for the 09-20 snapshot. But the snapshot inside the **09-18 14:00Z** fileset was taken at 13:45 UTC, *before* that day's backup — so it reads `20260917T140000Z`. Name the expected value.

---

## 3. Amputation check on the reconciliation itself

Every round-1 finding the change list claims is applied, checked against the document.

**Applied and intact (no action)** — B1 F1 (offline hash test replaces the candidate ordering, §5.4 + step 3), F3 (Procedure A0 exists and is preferred), F4 (step 8 re-points `DBPath` for all four, with `ResolveDbPath`/`GetRelativeDbPath` cited), F5 (§5.3 rewritten: `RepairHandler.cs` 87–104 rename, `DatabaseUpgrader.cs` pre-upgrade copy, actor unidentified), F6 (port discriminator in §5.4; §5.6 Leg C refuter rewritten), F7 (A.3 relabels 21:03:34 as the `-wal`/`-shm` creation), F8 (`/var/log/syslog*` in S-1/S-2/S-3 and D-8; P0.5 step 4 scrubs both stores in order), F9 (S-2a's stale-label warning), F11 (§7.3.2 environment override), F13 (A2's precision, incl. "the UI password survives"), F14/F16/F17 as recorded. B2 A1 (S-7), A2 (`serverstate` sampling in step 9), A3 (the escrow exception stated in the preamble), A4 (AC-4 two drills), A5 (S-8), A6 (D-12 enumerated), A8 (D-13), A10 (`.dropbox-dist` in §4.1/§7.11). B2 D1 (`PathChanged=` with the `path.c` evidence), D2 (new failure unit named), D12 (AC-3 + note AC-3a), D13 (§7.7 states the unit cannot become `User=duplicati`), D14 (§7.4's two facts + the escrow chmod in the script), D16 (P4 step 1 rewritten), D17 (`systemd-run` containment), D18 (D-1/4/6/9 "rule before P0"), D19 (`duplicati-verification.json` allow-listed; the exact-match property stated), D20 (`Restart=on-failure` rationale; `network-online.target` dropped), D21 (§7.3.4's T2-installer paragraph), D22 recorded as dissent.

**Applied in a form that loses the finding's point** — three:

| Round-1 id | What it asked for | What the document does |
|---|---|---|
| **B1 F2 / B2 D6** | *"if a server probe is kept … add a negative control (a random key must produce `Mismatch`)"* | The control exists but is **vacuous** (D3): `try_key` returns a `grep` result with `set -e` disabled, so a harness failure reads as "rejected". B1 F2 asked specifically for `Mismatch`; the implementation greps for the *absence* of success. **WEAKENED.** |
| **B2 D5 / B2 top-five #2** | *"the plan's own commands put the UI password, the new password and the candidate settings key on command lines … (R-18 self-violation, three places)"* | Two of three are fixed (§7.3.6 bans `change-password`/`--password`; step 3's candidate write uses `install /dev/stdin`). The third is **re-introduced**: the reconciliation's own `systemd-run … -p "Environment=SETTINGS_ENCRYPTION_KEY=${key}"` puts the candidate key on argv (D3). **REGRESSED.** |
| **B2 D11** | *"One credential path … in both clients, same PR; **order P0 so the file exists before AC-2**"* | AC-2 is fixed by moving alerting to step 10. **Step 9's own `yamaguchi_server_api.py` calls still precede it** (D7). **WEAKENED** — the finding's point was ordering, and the earliest consumer was missed. |

**Claimed applied but not in the document** — two:

| Round-1 id | Claim | Reality |
|---|---|---|
| **B2 D4** | change list: *"§7.3.4 — installer now installs the **guard** (`util/yamaguchi-pre-backup-guard.bash` → 0755 root:root)"* | The installer references it; **the file does not exist in the repository** and no step creates it. B2 D4's point was *"the guard has no repository source path and no install step"*; half of it (the source) is still open (D12). |
| **B2 D22 (partial)** | §11: *"§0 instrument list and §12 file list (B2 D22)"* applied | §12's file list names none of the three 2026-09-22 artifacts and has no reconciliation row (D16 k). |

**Recorded dissent — honestly recorded**: all six brief items are in §11 with both positions and the ruling. **AGREE.** One nit: §11's *"B2 proposes `dropbox exclude add`"* is accurate, and S-4a states B3's refutation as design text, so the dissent and the adopted position do not contradict.

---

## 4. Instrument adequacy — could this instrument have produced a different answer?

* **The `. "${ENV_FILE}"` reproduction (D1)** is the strongest result here and the one most worth attacking. I did **not** source the real file — I measured its shape with the design's own `2026-09-21_env_file_shape.py` and then reproduced the failure on a synthetic stand-in. Could it have come out differently? Only if the shape report is wrong about `quoted=False` or about `$` being present. The instrument reports both independently (`quoted` is a separate field from `metachars`), it was written for this arc and is named by AC-8, and the failure I reproduced (`set -u` + `$` → `unbound variable`) is a bash language property, not a host property. A second, weaker possibility: if the `$` happened to be the file's **last** character, `$` alone is literal and the script would survive. That is a 1-in-32 shape I cannot exclude without reading the value, and I did not. It would not rescue the `&`: `metachars` reports `&` present, and `&` in an unquoted assignment terminates the command regardless of position. **Verdict: adequate, with one enumerated escape (a trailing `$`) that `&` closes anyway.**
* **The probe exercise (D3, D4)** ran against a synthetic **journal-mode** SQLite with stub `-wal`/`-shm`, through a Python `sqlite3` shim, because the host has no `sqlite3` binary. So I proved the *control flow* (refusal fires at the right place, exit 3, no server start; control passes vacuously) but **not** the WAL-mode read path: a real WAL copy opened `mode=ro` needs a writable `-shm`, which the script has as root but which my shim never exercised. A different answer is possible on the real copy only in the direction of *more* failure (a `mode=ro` open error → empty `flag` → the same misleading refusal), never less. The `systemd-run` tripwire is conclusive about argv (it printed the key) and about the control (it exited 97 and the control still said "good").
* **`systemd-analyze security --offline` (D17)** was run on the linter's extracted copy with `ExecStart` rewritten to the scratch wrapper. `--offline` cannot see host state (cgroup delegation, the real `DeviceAllow` ACL), so the live score may differ by a tenth or two. It cannot differ by 3.5, which is the gap the finding turns on.
* **The destination census (#16)** used `os.scandir` with the guard's literal four patterns, so it answers exactly the guard's question. It cannot see a *newly arrived* stray between my run and the real run — which is the whole point of running the guard, not of my census.
* **Existence checks (D12, D19)** are `ls` on a worktree at one moment. A concurrent session could land any of the nine files; `git status` showed only the design file modified and the reconcile script untracked, so at review time none existed on any branch checked out here. I did **not** check other branches or open PRs.
* **Cross-reference sweep (D16)** used an anchored regex over the whole document for `§N`, `P* step N`, `AC-N`, `D-N`, `S-N`, `R-N`, `O-N`, `rule N`, `note X`, `principle N`, then resolved each target by reading it. It cannot catch a reference expressed purely in prose ("as established earlier") — and §8 contains several of those, which is itself the ecosystem convention's concern.

---

## 5. Five most consequential

1. **D1 — both Procedure A0 scripts abort before `duplicati-cli` runs, and echo a fragment of the live passphrase to stderr doing it.** A0 is the *preferred* route and the only one needing no key, no wipe and no re-entry; the step-0 gate that decides whether A0 is even available uses the same broken idiom. The operator sees a bash error, not a duplicati error, and routes to the key hunt or to Procedure B. Proven: `key='PASSPHRASE' … quoted=False metachars='$@&#'` + a synthetic repro giving `unbound variable` / `command not found`, rc 1 / 127. The correct idiom is already in `util/ad-hoc/yamaguchi_build_job.py:57-63`.
2. **D2 — `--no-local-db=true` makes the step-0 "one read-only command" a >30-minute, possibly non-terminating index rebuild, with its temp DB on tmpfs.** Measured on this host and written down in `util/ad-hoc/duplicati_drill_run.py:31-36`; the fix (`--dbpath` at a copy of `BMXWPAOGLP.sqlite`) is already in the operator's hand from P0 step 1.
3. **D5 — P0.5 step 1 is both mis-ordered and un-executable.** It points at "before P0 step 3" while §4.1 note (b) says "during P0" and step **0(c)** already executes `duplicati-cli` from a `duplicati`-owned directory; and `chown -R root:root /usr/lib/duplicati` **except `data/`** is an instruction with no literal reading. P0.5 is printed after P0, so an operator working top-to-bottom never runs it first.
4. **D6 — Procedures A0 and A2 never place their product.** Both end "Then step 8", and step 8 moves only the index. Two of four recovery routes complete with the recovered database still sitting in a scratch directory and the server starting against an empty data folder.
5. **D3 + D4 — the step-3 probe's negative control cannot fail, and its `sqlite3` refusal misdiagnoses in the most dangerous direction.** A harness failure or a slow .NET start reads as `KEY REJECTED`, which routes a correct key to A2/B; and with `sqlite3` absent the refusal reads `encrypted-fields=''` → "copy is not encrypted", which §4.2/§5.4/§11 have primed the operator to read as *"the second key-free recovery source has been found"*. The reconciliation also put the candidate key on `systemd-run`'s argv while adding the containment.

**Close behind**: D16 a/b (the header says "fully reconciled" while §11 says four lanes are "not applied", and cites a round-2 record that does not exist — the only place a reader checks whether §8 is safe to run); **D7** (step 9's API calls precede the credential step 10 creates); **D12** (nine invoked paths, none in the repository); **D8** (the snapshot lane copies the abandoned database into every fileset until P2).

---

## 6. What I could not determine, and why

* **Whether `sudo -u duplicati VAR=value <cmd>` is refused on this host** (D14). It needs `/etc/sudoers` or a sudo invocation; `sudo -n ls` returned *"interactive authentication is required"* and I did not authenticate. The `env` form is correct either way, so the replacement text is safe regardless.
* **The size of `BMXWPAOGLP.sqlite`**, which decides whether my D2 replacement's `cp -p "${JOBDB}" "${TMPDB}"` fits in the suggested `/home/duplicati/.cache`. `sudo -n ls -la /usr/lib/duplicati/data/` → interactive authentication required. P0 step 1's `sudo ls -la --time-style=full-iso` answers it and should be extended to record the size.
* **Whether the abandoned folder's main file is itself cleartext** — the same root-gated listing. This matters because it is the input to my D4 finding: if the real copy *is* cleartext, the probe's refusal is correct and only the empty-value case misdiagnoses.
* **Whether the real copy's `mode=ro` WAL open succeeds.** My synthetic database was journal-mode with stub siblings, and I used a Python `sqlite3` shim because the host has no `sqlite3`. The failure direction is bounded (an open error produces the same empty-value refusal), but the success path is untested.
* **The exact case of Duplicati's option-derived `DUPLICATI__` variable names** (D15) — I did not read `RunScript.cs`; Lane A3 and B1 did, and neither states the casing rule for option-derived names. Unsetting both spellings costs nothing.
* **Whether `duplicati-cli list --version=0` genuinely names the 09-18 fileset today.** Running it would have triggered the D1 failure or the D2 30-minute rebuild, and the brief forbids neither but the cost/benefit is poor; `duplicati-cli list --version=0` without a passphrase would still contact the destination. I relied on §4.1's "9 dlists, newest `20260918T140000Z`", which Lane A1 and B2 both re-measured.
* **Whether any of the nine missing scripts exist on another branch or in an open PR.** I checked only this worktree; `git fetch` is refused by the isolation shim and I did not run `gh`.
* **Whether the `--aes-version` pin (§7.5) interacts with A0.** Out of my lens and untested; AC-4a already conditions the drill split on it.

*Scratch evidence for this run: `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/1f771cb0-1009-4763-8a32-16517ac8b4b5/scratchpad/r2_B_action/` — `lint_run.txt`, `snips/`, `probe.neutered.bash` (3-line diff from the design's block, printed in `run_probe_test.bash`'s output), `make_fake_db.py`, `shim/{sqlite3,systemd-run}`, `test_source_env.bash`, `coreutils_idioms.bash`, `guard_allowlist_census.py`, `toolcheck.bash`. Nothing was written into the repository, no Duplicati server was started, and no secret value was printed or recorded.*

<!-- markdownlint-enable -->

---

## Report B (security) — adversarial review; lens: what reconciliation added

Subagent id `a5c54dfa185827c76` (57,480 characters). Archived verbatim.

<!-- markdownlint-disable -->

---

# Lane B (SECURITY) — consensus round 2, adversarial review of the reconciliation

**Document under review**: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`
**Snapshot reviewed**: sha256 `ac48092c78c390e095b07bbfb119f7b93f86293162995c8bd5dd731353dcc8ee`, 228,905 bytes, mtime `2026-09-22 02:47:12 -0500`, copied to `…/scratchpad/r2_B_sec/design_snapshot.md`.
**Predecessor**: Lane B3's 20 findings in `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`.
**Rules honoured**: read-only on the host; `duplicati.service` never touched; nothing written under `/mnt/Backups/`; no secret value printed (everything by length/class/count); no live SQLite opened; `duplicati-server --version` never run.

> **The document was being edited by other lanes while I read it.** At 02:31 it was 1,882 lines / ~219 KB; at 02:46 it was 2,126 lines / 221,492 B mid-write; at 02:47 it settled at 1,882 lines / 228,905 B. §11 reveals a round 2 *and* a round 3 have already folded corrections in. Everything below is anchored to the 02:47 snapshot and cited by **heading text**; two of my intended findings (AC-12's 5.2 gate, the guard's missing `additional_report_url` unset) were closed by a concurrent lane between my first and second read, and I record them as AGREE with independent corroboration rather than claiming them.

---

## Part A — disposition of round 1's Lane B3 findings

| B3 | Verdict | Evidence in the 02:47 snapshot |
| --- | --- | --- |
| **F-1** capability + no confinement | **ADDRESSED, one element silently dropped** | §7.1 principle 3 states the ACL-vs-capability trade in full; §7.3.2 carries the whole directive set. Offline score independently reproduced: `systemd-analyze security --offline --root=./unitroot duplicati.service` → **`Overall exposure level … 1.7 OK 🙂`** (B3 measured 5.2 MEDIUM without them). **Dropped without record**: B3's fix list named `InaccessiblePaths=… -/etc/credstore -/etc/credstore.encrypted`; the unit kept only `.encrypted`. See R2B-4. |
| **F-2** `open_by_handle_at` | **ADDRESSED — AGREE, independently verified transitively** | `expand_syscall_set.py @system-service` → 18 groups reached, **395 distinct syscalls**, `open_by_handle_at: NOT in set`, `name_to_handle_at: ALLOWED`. `overlap.py` → `|@privileged closure| = 53`, `overlap = 18` (`capset chown chown32 fchown … setuid32`), exactly the count and character the design's new comment asserts. |
| **F-3** UI credential = host-wide read | **ADDRESSED** | §6 note S-5a ("a host-wide read of everything the service can read"), §7.3.6, AC-13 + note AC-13a. |
| **F-4** RunScript env | **ADDRESSED, still a denylist** | §7.5 guard now unsets `DUPLICATI__passphrase DUPLICATI__PASSPHRASE DUPLICATI__additional_report_url DUPLICATI__ADDITIONAL_REPORT_URL SETTINGS_ENCRYPTION_KEY`; stdout contract stated. `additional-report-url` confirmed a real 2.4.0.0 server-setting key (utf-16 literal in `Duplicati.Library.RestAPI.dll`, adjacent to `encrypted-fields`, `jwt-config`). Residual: R2B-8, R2B-11. |
| **F-5** `.env` mode / `die` path | **PARTIALLY — the mode is defeated** | `die` now prints name + value length ✓; wrapper has a positive export allow-list ✓. But `.env` lives at `home/duplicati/.config/Duplicati/.env` — **inside the data folder that must be `0700 duplicati:duplicati`** — so `0640 root:duplicati` is rename-replaceable. See R2B-5. |
| **F-6** group-write model | **HONESTLY RECORDED** | Became D-14; §7.4 states the trade and says the script implements the *current* model and must be re-run after a ruling. |
| **F-7** `/usr/lib/duplicati` chown ordering | **ADDRESSED — ordering now unambiguous** | §8 P0 opens with **"Run P0.5 items 1 and 2 before anything in P0."** plus the reason it is printed later. Also §7.3.1 bullet 4 and §4.1 note (b). |
| **F-8** root timer → pcalnon-writable script | **ADDRESSED** | P0.5 item 2 + §7.7 ("a standing pcalnon→root code path that every branch switch re-arms"), covered by the same forward reference. |
| **F-9** scrub misses `/var/log/syslog*` | **ADDRESSED** | §6 preamble names `ForwardToSyslog=yes` and the counts; the D-8 paragraph says "the journal is half the job"; P0.5 item 4 orders syslog *then* journal; AC-8 greps both. |
| **F-10** uninventoried sinks | **ADDRESSED, incomplete** | Sink checklist exists (8 rows) and has already gained a "re-measuring creates a new copy" row. Still missing three sinks — R2B-13. |
| **F-11** burned key becomes the live key | **ADDRESSED, bucket label false** | Procedure A keeps the key "until P0.5's re-key replaces it"; P0.5 item 3 does the re-key; item 6 closes the detection gap. But P0.5's heading claims "none of it depends on the recovery" — false for item 3. See R2B-12. |
| **F-12** escrow synced to Dropbox | **ADDRESSED** | S-4a deletes the `exclude` alternative, orders copy-out → sha256 → Delete forever → account audit; §7.5 rule 7; D-13. |
| **F-13** AES version / cloud threat | **ADDRESSED** | `--aes-version` pinned as the fourth job change; §7.5 rule 7. `aes-version` / `aes-v3-iterations` confirmed as real literals in `Duplicati.Library.Encryption.dll`. |
| **F-14** guard write-access DoS | **ADDRESSED** | §7.5 rule 6, incl. the honest admission that the stray check duplicates Duplicati's own. |
| **F-15** sign-in tokens / server-util argv | **ADDRESSED** | §7.3.6 rewritten. Both option names confirmed real (utf-16 literals in `Duplicati.Server.Implementation.dll`: `webservice-password-init`, `webservice-disable-signin-tokens`). |
| **F-16** re-key window | **ADDRESSED** | P0.5 item 3: stop snapshot timer, two starts back to back, `wal_checkpoint(TRUNCATE); VACUUM` with the server stopped. |
| **F-17** candidate key at a root prompt | **ADDRESSED** | `set +o history; read -rs key; printf … \| sudo install -m 0600 /dev/stdin` — with "**never** `printf '%s' '<value>' > file` at a root prompt". §11 also records that round 2 caught a regression that put the key back on `systemd-run`'s argv. |
| **F-18** P0.5 bucket | **ADDRESSED** | Bucket created, 6 items, P1/P2/P3/P4 re-ordered. |
| **F-19** trust-domain tables | **ADDRESSED, incomplete and over-claiming** | Two tables exist. Missing a fifth crossing; the "Closed by" column claims closures the shipped unit does not implement. See R2B-11. |
| **F-20** credstore readable under the capability | **ADDRESSED AS RESIDUAL, on a false rationale** | See R2B-4. |

**Nothing from B3 was quietly dropped except `InaccessiblePaths=-/etc/credstore`**, and that one was dropped *with* a stated reason — which is the problem, because the reason is wrong.

---

## Part B — new findings

Format: threat/actor | claim in the design | attack or gap | evidence | severity | **exact replacement text**.

---

### R2B-1 — `ReadWritePaths=` hands the confined service write and delete over the passphrase escrow and the frozen evidence set — HIGH

**Threat/actor**: (c) a compromised Duplicati server, or any run-script an API principal names (§7.3.1 table row 3).

**Claim**: §8 preamble — *"Nothing under `/mnt/Backups/Ubuntu/` is deleted or moved by any step below, with exactly one exception, and it needs owner sign-off"*. §7.3.2 — `ReadWritePaths=/home/duplicati /mnt/Backups/Ubuntu/Dropbox/Backups` (heading "Data folder, defaults file, unit").

**Gap**: `ReadWritePaths=` is set one directory level above the job's destination. The tree it opens is not just `Yamaguchi/`:

```
$ stat -c '%A %U:%G %n' /mnt/Backups/Ubuntu/Dropbox/Backups …
drwxrwx--- pcalnon:duplicati /mnt/Backups/Ubuntu/Dropbox/Backups
drwxrwx--- pcalnon:duplicati /mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_keys
drwxrwx--- pcalnon:duplicati /mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_frozen_20260826
$ id duplicati
uid=133(duplicati) gid=139(duplicati) groups=139(duplicati)
$ find /mnt/Backups/Ubuntu/Dropbox/Backups -maxdepth 1 -type d -perm -1000 | wc -l
0
$ ls -l /mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_keys/
-rwxrwx---+1 pcalnon duplicati 1131 Aug 29 15:39 README.md
-rwxrwx---+1 pcalnon duplicati  388 Aug 29 15:39 env
```

Group `duplicati` holds `rwx` on every one of those directories and there is **no sticky bit**, so the service user can unlink and replace any entry. The escrow `env` is itself group-`rwx`. Therefore, from the moment the §7.3.2 unit is installed until P2's permission script runs:

1. The service can **read both passphrases** out of `_yamaguchi_keys/env` with no capability involved — pure group membership.
2. The service can **delete the escrow** and the 09-18 frozen set `_yamaguchi_frozen_20260826/` and the ten `duplicati-*.dlist.zip.gpg` archives — and, because the tree is Dropbox-synced, the deletions propagate to the cloud.
3. That directly contradicts the §8 preamble's "nothing … is deleted or moved" rule, which the reconciliation added specifically to make the escrow exception visible.

The design's own §7.3.1 crossings table lists run-scripts as a way to become the service — so this is reachable by anyone holding the UI credential, which §6 S-5 says is world-readable today.

**Severity**: HIGH (the escrow is the only key custody for the whole of T1 and T1c; §7.5 rule 5 says the restore passphrase "comes from escrow").

**Exact replacement text** — in §7.3.2's unit, replace

```ini
ReadWritePaths=/home/duplicati /mnt/Backups/Ubuntu/Dropbox/Backups
```

with

```ini
# Scoped to the job's own destination, not the whole Backups/ tree. The parent holds
# _yamaguchi_keys/ (the passphrase escrow, group duplicati rwx, no sticky bit),
# _yamaguchi_frozen_20260826/ and ten .dlist.zip.gpg archives -- all of which a
# ReadWritePaths= on the parent would let this service unlink, with the deletion
# propagating to Dropbox. Duplicati needs write on the destination directory only.
ReadWritePaths=/home/duplicati /mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi
InaccessiblePaths=… -/mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_keys
```

and add to §8 P0.5 item 5, first sentence: *"…, `chmod 0700` the escrow **directory** as well as `chmod 0600` the `env` file — the directory's group-`w` bit, not the file's mode, is what lets the service user unlink it."*

---

### R2B-2 — "No egress" is false by construction: the Dropbox daemon is a file-triggered exfiltration channel that `IPAddressDeny=any` cannot reach — HIGH (claim), MEDIUM (residual)

**Threat/actor**: (c) a compromised server holding `CAP_DAC_READ_SEARCH`.

**Claim**: §7.3.2 unit comment — *"# No egress: the destination is file:// and Dropbox is a separate daemon, so the only legitimate network use is the update check and usage reporting, both disabled below."* This sentence is the justification for the entire `IPAddressDeny=any` / `RestrictAddressFamilies` block, and §7.1 principle 3 closes with *"§7.3.2's confinement set is what keeps the capability from also being an exfiltration channel"*.

**Gap**: the reason given for there being no network need — *Dropbox is a separate daemon* — is precisely why egress is **not** closed. The service has `ReadWritePaths=` into a directory that a live, authenticated, internet-connected daemon replicates to a third party. §6 S-4 records `dropbox filestatus` reading `up to date` for that tree. So a server that can read `/etc/shadow`, `~/.ssh`, `/root` (capability) and can write one file into the destination has a high-bandwidth, unauthenticated, out-of-band path to the internet. `IPAddressDeny=any` bounds **socket** egress only; it is silent about a write-and-let-another-process-upload channel. The document discusses cloud→local propagation at length (§7.5 rule 7) and never states the local→cloud direction as a *confinement* consequence.

Note this is not hypothetical plumbing: it is the same channel that already carried the passphrase escrow into a third party's cloud (S-4).

**Severity**: HIGH for the claim (it makes a residual invisible); MEDIUM for the residual itself, because writes are bounded by R2B-1's fix.

**Exact replacement text** — replace the unit comment with

```ini
# Socket egress is denied. It is NOT the only egress: ReadWritePaths= below opens a
# directory that the pcalnon Dropbox daemon replicates to a third party (S-4 records
# `dropbox filestatus` reading "up to date" for this tree). Anything this service writes
# into the destination leaves the machine, and IPAddressDeny= cannot see that path --
# the upload is another process's socket. Scoping ReadWritePaths= to Yamaguchi/ and
# D-13's Dropbox root policy are therefore confinement controls, not hygiene.
# The update check and usage reporting are the only SOCKET uses; see the note below on
# how they are actually disabled.
IPAddressDeny=any
IPAddressAllow=localhost
```

and add a row to §7.3.1's crossings table:

```
| capability-read data → the internet | write it into the Dropbox-synced destination; the daemon uploads it | ReadWritePaths= scoped to Yamaguchi/ (§7.3.2) + D-13; `IPAddressDeny=` does NOT close this |
```

---

### R2B-3 — both `Environment=DUPLICATI__*` lines are inert: neither name exists in the 2.4.0.0 install — HIGH (correctness of a security claim)

**Threat/actor**: none directly; this is a vacuous control that the design leans on.

**Claim**: §7.3.2 unit —

```ini
Environment=DUPLICATI__DISABLE_UPDATE_CHECK=true
Environment=DUPLICATI__USAGE_REPORTER_LEVEL=none
```

— and the comment above them, *"the only legitimate network use is the update check and usage reporting, both disabled below."*

**Gap**: neither string appears anywhere in the 646-file install, in either encoding a .NET assembly uses:

```
$ python3 scan2.py            # utf-8 AND utf-16le over /usr/lib/duplicati, 646 files
DUPLICATI__DISABLE_UPDATE_CHECK       0  []
DUPLICATI__USAGE_REPORTER_LEVEL       0  []
DUPLICATI__disable_update_check       0  []
DUPLICATI__usage_reporter_level       0  []
```

What the software actually reads:

- **Update check** — `Duplicati.Library.AutoUpdater.dll` carries the template `AUTOUPDATER_{0}_SKIP_UPDATE` (with `AUTOUPDATER_{0}_URLS`, `AUTOUPDATER_{0}_CHANNEL`), i.e. `AUTOUPDATER_Duplicati_SKIP_UPDATE`. There *is* a real startup option `--disable-update-check`, a utf-16 literal in `Duplicati.Server.Implementation.dll` next to `disable-db-encryption`, `require-db-encryption-key`, `settings-encryption-key`.
- **Usage reporting** — `Duplicati.Library.UsageReporter.dll` carries `USAGEREPORTER_{0}_LEVEL`, `DO_NOT_TRACK`, the value `none`, and the endpoint `https://usage-reporter.duplicati.com/api/v1/report`. `usage-reporter-level` in `Duplicati.Library.RestAPI.dll` sits in the **ServerSettings database-key list** (beside `encrypted-fields`, `jwt-config`, `paused-until`), i.e. it is a stored setting, not a command-line option.
- The uppercase `DUPLICATI__` form the design generalises from is a **hand-written special**: `DUPLICATI__ALLOW_INSECURE_DATAFOLDER` is a literal in `Duplicati.Library.Common.dll`, two strings away from `--allow-insecure-datafolder`. The *generic* mapping is documented by the vendor at `/usr/lib/duplicati/run-script-example.sh` lines ~76-80: *"all Duplicati options are exposed as environment variables with the prefix `DUPLICATI__`. … the dash (-) character is … replaced with underscore (_)"*, example `$DUPLICATI__encryption_module` — **lower case**. `Duplicati.Library.Modules.Builtin.dll` emits exactly that: `DUPLICATI__backup_name` alongside the uppercase specials `DUPLICATI__EVENTNAME`, `DUPLICATI__OPERATIONNAME`, `DUPLICATI__REMOTEURL`.

And the failure is **silent**: §11 records that round 2 corrected §7.3.3's claim that 2.4.0.0 exits on an unrecognised option — *"it warns and continues"* — and AC-14 exists to grep for `Unknown option supplied`. An unread environment variable produces no such line at all, so AC-14 cannot see this class.

**Consequence**: the sentence justifying the whole no-egress block is unsupported; AC-12's "the server completes AC-3 under every confinement directive the unit sets" passes with two directives inert — a vacuous pass of exactly the class AC-12 was written to catch; and if `IPAddressDeny=any` is ever removed under O-3's "a directive it cannot run under is removed and recorded", both channels come back live with nothing in the document saying so.

**Severity**: HIGH for the claim; MEDIUM operationally (the deny rule currently masks the effect).

**Exact replacement text** — delete both `Environment=` lines and replace with

```ini
# Update check and usage reporting, disabled by the names the software actually reads.
# DUPLICATI__DISABLE_UPDATE_CHECK / DUPLICATI__USAGE_REPORTER_LEVEL do NOT exist: a
# utf-8 AND utf-16le scan of all 646 files under /usr/lib/duplicati finds neither, in
# either case. The generic DUPLICATI__ mapping is lower-case with '-'→'_'
# (run-script-example.sh ll. 76-80; Modules.Builtin emits DUPLICATI__backup_name);
# the upper-case forms in the product are hand-written specials
# (DUPLICATI__ALLOW_INSECURE_DATAFOLDER). An unread env var produces no
# "Unknown option supplied" line, so AC-14 cannot catch a wrong name here.
Environment=AUTOUPDATER_Duplicati_SKIP_UPDATE=1
Environment=DO_NOT_TRACK=1
Environment=USAGEREPORTER_Duplicati_LEVEL=none
```

and append `--disable-update-check` to `DAEMON_OPTS` in `etc/default/duplicati`, where AC-14's grep *can* see a typo. Add to AC-12: *"and `journalctl -u duplicati.service` shows no outbound attempt to `usage-reporter.duplicati.com` or the update URL on the first start — an `IPAddressDeny` refusal in the log proves the env names were wrong, not that reporting was disabled."*

---

### R2B-4 — `/etc/credstore` is left unmasked on a rationale the systemd manual refutes — MEDIUM-HIGH

**Threat/actor**: (c) the service, or any run-script.

**Claim**: §7.3.2, the paragraph beginning *"`/etc/credstore` is deliberately **absent** from `InaccessiblePaths=`"* — two reasons are given: (i) *"`LoadCredential=` must be able to read the key from it, and masking it would break the start"*; (ii) *"That is not a gap that masking could close anyway: with `CAP_DAC_READ_SEARCH` the service can read `/etc/credstore/*` directly."*

**Gap**: **both reasons are wrong, and (ii) contradicts the document's own §7.1 principle 3.**

(i) `man systemd.exec` on this host (systemd 259), under `LoadCredential=`:

> *"The credential files/IPC sockets **must be accessible to the service manager, but do not have to be directly accessible to the unit's processes**: the credential data is read and copied into separate, read-only copies for the unit…"*

and, on the search path: *"…the **system service manager** will search the directories `/etc/credstore/`, `/run/credstore/` and `/usr/lib/credstore/`…"*. The manager reads the source; the unit reads `$CREDENTIALS_DIRECTORY`. Masking the source in the unit's namespace does not break the start.

(ii) §7.1 principle 3 states the correct rule two sections earlier: *"`ProtectSystem=strict` and `ProtectHome=read-only` stop *writes* — they are **mount flags, correctly not defeated by the capability**"*. `InaccessiblePaths=` is the same class of control. If masking did not bind the capability, `InaccessiblePaths=-/etc/shadow -/root -/var/log` in the very same unit would be decorative — and the design clearly does not believe that. The capability argument proves too much.

`/etc/credstore` on this host is `drwx------ root:root` and holds every *other* service's secrets; with the capability and no mask, the Duplicati service reads all of them.

**Severity**: MEDIUM-HIGH — a closable hole left open, plus an internal contradiction that will be copied forward by anyone reasoning from it.

**Exact replacement text** — in the unit:

```ini
InaccessiblePaths=-/etc/shadow -/etc/shadow- -/etc/gshadow -/etc/gshadow- -/etc/ssh -/etc/credstore -/etc/credstore.encrypted -/var/lib/docker -/var/log -/run/log/journal -/var/spool/cups -/root
```

and replace the paragraph with:

> `/etc/credstore` **is** masked. `LoadCredential=` is unaffected: `man systemd.exec` states that the credential source "must be accessible to the service manager, but **do not have to be directly accessible to the unit's processes**", and that it is "the system service manager" that searches `/etc/credstore/`. The manager reads the file and hands the unit a separate read-only copy at `$CREDENTIALS_DIRECTORY`. Masking therefore costs nothing and removes the service's capability-read of **every other service's** secrets in that directory — `InaccessiblePaths=` is a mount flag, and §7.1 principle 3 already establishes that mount flags are not defeated by `CAP_DAC_READ_SEARCH`. An earlier revision of this paragraph argued the opposite and was wrong on both halves. What masking does **not** remove is the run-script's read of `$CREDENTIALS_DIRECTORY/settings-key` itself (`man systemd.exec`: readable by every process in the unit) — that residual is real, it is a crossing in §7.3.1's table, and the fix for it is the secret-provider channel (§7.3.5). `LoadCredentialEncrypted=` would not help either: no usable TPM2 (`systemd-analyze has-tpm2`: partial) and no `/var/lib/systemd/credential.secret`. **Verify the mask does not break the start before trusting this paragraph** — it is part of O-3's `systemd-run` trial, not a tested fact.

---

### R2B-5 — the recommended `.env` mode buys nothing: the file sits in a directory the service user must own — MEDIUM-HIGH

**Threat/actor**: (c) the plain `duplicati` uid, i.e. the service itself or any run-script.

**Claim**: §7.3.5 — *"`0640 root:duplicati` — Lane B3 F-5, and what this design RECOMMENDS: the wrapper only ever READS this file, so the service user needs no write, and a file the plain `duplicati` uid can write is a code-injection path into a process holding `CAP_DAC_READ_SEARCH`"*; §7.3.1's crossings table closes the `.env` crossing with *"the wrapper's **positive** export allow-list (§7.3.3) + `.env` mode (§7.3.5)"*.

**Gap**: the file is at `home/duplicati/.config/Duplicati/.env` — **inside the data folder**. §7.3.2 requires that folder to be `0700 duplicati:duplicati` because *"Duplicati 2.4.0.0 verifies a pre-existing data folder at every start and refuses one with any group or other bit"*, and the server must own it to write its database there. A `0640 root:duplicati` file in a `0700 duplicati:duplicati` directory is **unlink-and-recreate-able by the duplicati uid**: POSIX delete permission comes from the *parent directory's* write bit, not the file's mode. The service can therefore replace `.env` with its own content at any time, and the mode recommendation is decorative. The wrapper's positive allow-list still bounds *what names* can be exported (that half holds), but the design presents the mode as the second half of the closure and it is not.

There is also a **live contradiction inside §7.3.2 and §7.3.5**: §7.3.2 says the data folder's *files* are `0600`; §7.3.5 says install `.env` `0640`. If `PrepareSecureDataFolder` checks file modes as well as the directory's, a `0640` `.env` is a start refusal at every boot.

**Severity**: MEDIUM-HIGH — the design's answer to a code-injection path into a capability-bearing process does not bind.

**Exact replacement text** — in §7.3.5, change the file header path and add:

```text
# file: etc/duplicati/env        (NOT inside the data folder -- see below)
```

and insert after the mode block:

> **The mode only binds if the file leaves the data folder.** `/home/duplicati/.config/Duplicati/` must be `0700 duplicati:duplicati` (§7.3.2, Duplicati's own requirement) and the service must own it to write its database — so the `duplicati` uid holds write on the *directory*, and delete permission in POSIX comes from the directory, not the file. A `0640 root:duplicati` `.env` inside it can be unlinked and recreated by the service user, which defeats the whole point of the mode. Put it at `/etc/duplicati/env`, `0640 root:duplicati`, in a `0755 root:root` directory, and point the wrapper's `DUPLICATI_ENV_FILE` default there. This also removes the second-order problem that §7.3.2 requires files in the data folder to be `0600` while this section installs one at `0640`.

Update §7.3.1's crossings table row 1 "Closed by" to: *"the wrapper's **positive** export allow-list (§7.3.3); the `.env` mode closes it **only** once the file is outside the duplicati-owned data folder (§7.3.5)"*.

---

### R2B-6 — path masking is defeated by `/proc/<pid>/root` of any same-uid process outside the unit, and the design prescribes creating them — MEDIUM

**Threat/actor**: (c) the service, while any `sudo -u duplicati` / `su - duplicati` process exists.

**Claim**: §7.3.2's `InaccessiblePaths=` line and the comment above `SystemCallFilter=` — *"Path masking without this filter is therefore not a boundary at all"*, implying that *with* the filter it is one.

**Gap**: `InaccessiblePaths=`, `ProtectHome=`, `ProtectSystem=` and `PrivateTmp=` are all mount-namespace controls. A process can leave its own namespace's view by resolving a path through `/proc/<pid>/root/…` of a process in a *different* namespace, subject only to a ptrace-mode check — which same-uid passes. `ProtectProc=invisible` does not close this: `man systemd.exec` says it hides *"processes owned by **other** users"*. `@system-service` does not close it either — no special syscall is needed, just `openat`. My transitive expansion also shows `setns` and `open_tree` are in the allowed set (`RestrictNamespaces=yes` blocks the first; `move_mount` and `mount` are absent, so the second is not a mount escape).

So the mask holds only while **no `duplicati`-uid process exists outside the unit**. §7.3.1 bullet 1 prescribes exactly such processes as the administration model — *"Administrative work: `sudo -u duplicati -- <cmd>` or `runuser -u duplicati --`"* — §6's sink checklist records **two live `su - duplicati` shells (pids 3065639, 3117158)** right now, and `usermod -s /usr/sbin/nologin duplicati` is deferred to **P4 item 3**, after seven successful daily runs.

**Severity**: MEDIUM — it does not defeat the capability trade (the capability is the bigger hole), but it means the masked list is a best-effort hygiene control, not the boundary the §7.3.2 comment implies.

**Exact replacement text** — append to the `InaccessiblePaths=` comment block:

```ini
# Bound, not boundary: a mount mask is escaped by resolving through /proc/<pid>/root of
# any process in another mount namespace that this uid may ptrace -- i.e. any
# duplicati-uid process OUTSIDE the unit. ProtectProc=invisible does not stop it
# (man systemd.exec: it hides processes owned by OTHER users). So every
# `sudo -u duplicati` / `su - duplicati` session is, while it lives, a hole in this
# list. Keep such sessions transient, and move `usermod -s /usr/sbin/nologin duplicati`
# from P4 to P0.5. What the mask reliably buys is protection from the service's own
# code paths and from accident -- not from a deliberate same-uid adversary.
```

and move P4 item 3 (`usermod -s /usr/sbin/nologin duplicati`) into P0.5 as item 7, with the note *"after the two live `su - duplicati` shells in §6's checklist have been closed per their own row"*.

---

### R2B-7 — the mask list misses five paths, including one the design's own sink checklist names — MEDIUM

**Threat/actor**: (c) the service with `CAP_DAC_READ_SEARCH`.

**Claim**: `InaccessiblePaths=-/etc/shadow -/etc/gshadow -/etc/ssh -/etc/credstore.encrypted -/var/lib/docker -/var/log -/root`.

**Gap**, each verified read-only on the host:

| Missing | State | Why it matters |
| --- | --- | --- |
| `/etc/shadow-`, `/etc/gshadow-` | `-rw-r----- root:shadow`, 1775 B / 1397 B | the previous generation of the same hashes; masking `/etc/shadow` alone leaves them |
| `/var/spool/cups` | `drwx--x--- root:lp` | §6's own sink checklist row: *"the escrow sheet was printed (USB HP OfficeJet, 32 completed jobs); job-file retention unknown"*. The design identifies this as a place the **passphrase** may sit and then does not mask it from the one process it is confining |
| `/run/log/journal` | `drwxr-sr-x+ root:systemd-journal`, exists on this host | `-/var/log` does not cover the volatile journal |
| `/etc/credstore` | `drwx------ root:root` | R2B-4 |

**Severity**: MEDIUM. `/var/spool/cups` is the sharp one — it is the only entry whose contents the design itself says may be a live passphrase.

**Exact replacement text**: the single `InaccessiblePaths=` line given in R2B-4 above, plus in §6's CUPS sink row, change the Action cell to: *"owner: `grep -i PreserveJobFiles /etc/cups/cupsd.conf`; `sudo ls -la /var/spool/cups`. Independently, mask `/var/spool/cups` in §7.3.2 — this row identifies it as a possible cleartext-passphrase sink and the service holds `CAP_DAC_READ_SEARCH`."*

---

### R2B-8 — the guard's secret-dropping is a denylist over a set the design itself calls unbounded — MEDIUM

**Threat/actor**: (c) any child of the guard; anyone who reads the job log.

**Claim**: §7.5 guard — `unset DUPLICATI__passphrase DUPLICATI__PASSPHRASE DUPLICATI__additional_report_url DUPLICATI__ADDITIONAL_REPORT_URL SETTINGS_ENCRYPTION_KEY`, with the comment *"Duplicati's RunScript exports **EVERY** job option into this script's environment, unfiltered"*.

**Gap**: a denylist cannot be complete over a set the same comment calls "every job option, unfiltered", and the design's own §8 Procedure A2 names a wider password-typed set that `wipe-encryption` clears: *"password-typed `Option.Value` (the job `passphrase`, `jwt-config`, `pbkdf-config`, …)"*. `jwt-config` is the **server's JWT signing configuration** — with it, an attacker mints arbitrary API tokens and then sets `--run-script-before` to anything, which is §7.3.1's third crossing executed from inside the guard's own environment. `additional-activity-url` sits immediately beside `additional-report-url` in the same ServerSettings key list in `Duplicati.Library.RestAPI.dll` and is equally likely to carry a token. The wrapper (§7.3.3) already uses a **positive** allow-list for exactly this reason; the guard should not use the opposite shape.

Two secondary notes, both true as written and worth stating so they are not re-derived: `unset` on a never-set name is a no-op and does not trip `set -u`, so the order (`set -euo pipefail` → `trap` → `unset`) is safe; and `unset` does **not** rewrite `/proc/<guardpid>/environ`, which keeps the original block for the process's lifetime — no new exposure (the server's environ already has it) but not the clean slate the comment implies. And `unset SETTINGS_ENCRYPTION_KEY` does not remove the key from the guard's reach: `CREDENTIALS_DIRECTORY` is inherited and the path is well known, which §7.3.2 records as a residual while §7.5's comment reads as though the two unsets close it.

**Severity**: MEDIUM.

**Exact replacement text** — replace the `unset` statement and its comment with:

```bash
# Duplicati's RunScript exports EVERY job option into this script's environment,
# unfiltered, prefixed DUPLICATI__ (RunScript.cs; run-script-example.sh l.75). A denylist
# cannot be complete over "every option" -- see the password-typed set section 8
# Procedure A2 enumerates (passphrase, jwt-config, pbkdf-config, ...). Keep only what
# this guard uses, the same POSITIVE shape the wrapper uses in section 7.3.3.
_keep_op="${DUPLICATI__OPERATIONNAME:-unknown}"; _keep_url="${DUPLICATI__REMOTEURL:-}"
while IFS='=' read -r _n _; do
    case "${_n}" in DUPLICATI__*) unset "${_n}" ;; esac
done < <(env)
unset SETTINGS_ENCRYPTION_KEY _n _
# NOTE: this does NOT put the settings key out of reach -- $CREDENTIALS_DIRECTORY is
# inherited and /run/credentials/duplicati.service is a fixed path (man systemd.exec:
# readable by every process in the unit, run-scripts included). Section 7.3.2 records that
# residual; the secret-provider channel (section 7.3.5) is what removes it.
```

then use `${_keep_op}` / `${_keep_url}` in place of the two `DUPLICATI__` reads below.

---

### R2B-9 — the guard prints the job's remote URL verbatim into the job log — MEDIUM

**Threat/actor**: (b)/(c) anyone holding the UI credential (§6 S-5: world-readable today).

**Claim**: §7.1 principle 2 — *"Secrets never pass through a shell parser or a log … no script echoes a file or the environment."* AC-8 — *"zero in the job log's run-script output"*.

**Gap**: the guard's third check is

```bash
*) fail "job TargetURL '${REMOTE_URL}' is not the guarded destination file://${DEST_DIR}" ;;
```

`REMOTE_URL` is `DUPLICATI__REMOTEURL`. For `file://` it is harmless — but the branch that prints it is *precisely the branch that fires when the TargetURL is not `file://${DEST_DIR}`, i.e. when someone has changed it*. Duplicati backend URLs routinely embed credentials (`--auth-password` is a real option: 6 utf-8 / 12 utf-16 literals across `Duplicati.Library.Backend.*.dll`). So an API principal who repoints the job at `ftp://user:pass@host/` causes the guard to write that credential into the job log — and from there into whatever `additional-report-url` POSTs (S-8). The guard's own diagnostic is the leak. The same applies, less sharply, to the attacker-chosen `${stray}` filename, which the design currently dismisses as *"a nuisance, not a vulnerability"* while its own open item O-13 says it has not checked whether `SendStdOutToLogs` stores stderr verbatim — I confirmed `Duplicati.Library.Modules.Builtin.dll` contains both `SendStdOutToLogs` and `set_RedirectStandardError`, so stderr *is* captured; whether it reaches the option-override parser is unsettled.

**Severity**: MEDIUM (conditional on a TargetURL change, which is the failure this check exists to detect).

**Exact replacement text** — in the guard:

```bash
        *) fail "job TargetURL does not match the guarded destination file://${DEST_DIR}; \
got scheme='${REMOTE_URL%%:*}' length=${#REMOTE_URL} sha256-8=$(printf '%s' "${REMOTE_URL}" | sha256sum | cut -c1-8)" ;;
```

and, for the stray name:

```bash
[[ -z "${stray}" ]] || fail "foreign entry in destination, name sanitised: $(printf '%s' "${stray##*/}" | LC_ALL=C tr -cd 'A-Za-z0-9._-' | cut -c1-64)"
```

with the §7.5 prose changed from *"a nuisance, not a vulnerability"* to: *"Both the stray-file **name** and the job's **TargetURL** are attacker-influenced strings that would otherwise reach the job log verbatim, and a non-`file://` TargetURL can carry `auth-password` in the URL itself. The guard therefore prints a scheme, a length and a sha256 prefix for the URL, and a character-class-sanitised basename for the stray. O-13 (does `SendStdOutToLogs` store stderr verbatim, and does the override parser see it?) remains open, but the guard no longer depends on its answer."*

---

### R2B-10 — `ProcSubset=pid` on a .NET server, with `SystemCallErrorNumber=EPERM` blunting the test that would catch it — MEDIUM

**Threat/actor**: none; availability + the adequacy of AC-12.

**Claim**: §7.3.2 sets `ProcSubset=pid`; AC-12 says the server must complete AC-3 *"under every confinement directive the unit sets"*.

**Gap**: `man systemd.exec` on `ProcSubset=`:

> *"Note that Linux exposes various kernel APIs via `/proc/`, which are made unavailable with this setting. Since these APIs are used frequently this option is useful only in a few, specific cases, and **is not suitable for most non-trivial programs**."*

Duplicati 2.4.0.0 is self-contained .NET — `/usr/lib/duplicati/libcoreclr.so` (7,095,944 B) and `Duplicati.Server.runtimeconfig.json` are both present. CoreCLR's GC sizing reads `/proc/meminfo` through `sysconf(_SC_PHYS_PAGES)`; `ProcSubset=pid` removes `/proc/meminfo`, `/proc/stat`, `/proc/cpuinfo` and `/proc/sys/`. This is the single most likely directive in the set to fail O-3's trial.

Compounding it: `SystemCallErrorNumber=EPERM` converts a blocked syscall from `SIGSYS`-and-die into a returned error. That is the friendlier choice in production and the **worse** choice for the trial AC-12 describes — a .NET runtime that gets `EPERM` from a filter-blocked call typically falls back or logs, so the server can complete AC-3 while quietly degraded, and AC-12's "the server completes AC-3 under this exact set" passes vacuously.

**Severity**: MEDIUM (availability + instrument adequacy).

**Exact replacement text** — add to §7.3.2's O-3 paragraph:

> Two directives in this set are the likely failures, and the order of the trial matters. `ProcSubset=pid` hides `/proc/meminfo`, `/proc/stat` and `/proc/sys/` from a **.NET** server (`libcoreclr.so` is present in the install); `man systemd.exec` says of it, in terms, that it *"is not suitable for most non-trivial programs"*. And `RestrictAddressFamilies=` as written denies `AF_NETLINK`, which glibc's `getaddrinfo`/`getifaddrs` use. **Run the `systemd-run` trial first with `SystemCallErrorNumber=` unset** — the default `SIGSYS` kill makes a blocked call a visible crash, whereas `EPERM` lets the runtime fall back silently and lets AC-12 pass on a degraded server. Switch to `EPERM` only after the trial has shown which calls are actually needed, and record that switch.

and add to note **(AC-12a)**: *"the trial is run twice — once with `SystemCallErrorNumber=` unset (fail-loud) to enumerate what the server needs, then once as shipped."*

---

### R2B-11 — the crossings table is missing its fifth row, and two of its four "Closed by" cells claim closures the shipped design does not implement — MEDIUM

**Threat/actor**: (c) any run-script the job names — the table's own row 3.

**Claim**: §7.3.1, the four-row crossings table.

**Gap**, three parts:

1. **The missing fifth crossing.** The table's row 2 closes `/proc/<serverpid>/environ → the settings key` with *"the secret-provider channel (§7.3.5), which keeps the key out of the environment entirely"*. But the shipped unit in §7.3.2 uses `LoadCredential=` + the wrapper's `export`, and §7.3.5 itself says the secret provider is *"the preferred delivery; the `LoadCredential=` + wrapper-export form below is **the fallback**"*. Under the design **as shipped**, the key is reachable two ways: the server's environ *and* `$CREDENTIALS_DIRECTORY/settings-key`, which `man systemd.exec` makes readable by every process in the unit — run-scripts included. §7.3.2 records that as prose; the table does not have a row for it, and the table is what §7.1 principle 3 points at.
2. **Row 2's "Closed by" is aspirational**, not shipped.
3. **Row 1's "Closed by" cites the `.env` mode**, which R2B-5 shows does not bind at its current location.

The full chain the table never states end to end: world-readable UI credential → API → `--run-script-before` → runs as `duplicati` **inside the unit** → reads `$CREDENTIALS_DIRECTORY/settings-key` → decrypts `Duplicati-server.sqlite` → the job `passphrase` → **every volume in T1 and T1c**. That is one credential to the whole backup, and §6 S-5 says that credential is in a 0664 file today.

**Severity**: MEDIUM (documentation, but it is the frame every other §7.3 control is justified against).

**Exact replacement text** — add a fifth row and amend two:

```
| `$CREDENTIALS_DIRECTORY/settings-key` → any run-script → the job passphrase | LoadCredential= exposes the key to EVERY process in the unit, run-scripts included (man systemd.exec); a run-script path is a plain job option (AC-13). Chain: UI credential → API → --run-script-before → read the key → decrypt the server DB → the passphrase → every volume in T1 and T1c | NOT closed by the unit as shipped. Closed only by the secret-provider channel (§7.3.5) replacing LoadCredential=, plus AC-13 pinning the run-script path |
```

and change row 1's cell to *"the wrapper's **positive** export allow-list (§7.3.3) — the `.env` mode closes it only once the file leaves the duplicati-owned data folder (§7.3.5)"*, row 2's to *"the secret-provider channel (§7.3.5) **if adopted**; the unit as shipped in §7.3.2 uses the `LoadCredential=` + wrapper-export fallback, under which this crossing is OPEN"*. Change the heading from *"the four crossings"* to *"the five crossings"*.

---

### R2B-12 — P0.5's own heading claims an independence its item 3 does not have — LOW-MEDIUM

**Claim**: heading *"### P0.5 — same session as the recovery (minutes, and none of it depends on the recovery)"*, and the body *"Each takes minutes and has no dependency on which procedure step 3 chose."*

**Gap**: item 3 is the re-key — *"Stop the snapshot timer, do the two-start re-key back to back"*. A two-start re-key runs the **server against the recovered data folder**, which does not exist until P0 steps 4–8 have placed it. It depends on the recovery completely. The bucket therefore has two halves with opposite ordering constraints: items 1, 2, 4, 5, 6 must run *before* P0 step 3; item 3 must run *after* P0 step 8. The new forward reference at the head of P0 already says "items 1 and 2", which implicitly concedes this — but the heading still tells an operator that item 3 is order-free, and item 3 is the one that closes S-1/S-2.

**Severity**: LOW-MEDIUM (ordering, not a hole).

**Exact replacement text** — split the heading and preamble:

```markdown
### P0.5a — before anything in P0 (minutes; depends on nothing)

Items 1, 2, 4, 5 and 6 below. None touches the recovery, each takes minutes, and item 1 closes
the path by which the service user controls the binaries P0 steps 0(c), 3, 4 and 7 execute.

### P0.5b — immediately after P0 step 8, same session

Item 3 (the re-key) only. It runs the server against the **recovered** data folder, so it cannot
precede the recovery — an earlier revision of this heading said the whole bucket was independent
of it, which is true of five of the six items and false of the one that closes S-1 and S-2.
```

---

### R2B-13 — three sinks this arc created are still uninventoried, and one of them is inside the backup source — LOW-MEDIUM

**Claim**: §6's sink checklist — *"every place a secret from this arc may still sit"* — with a row for *"Claude Code transcripts under `~/.claude/projects/…` — **cloud-linked**"*.

**Gap**:

1. **Persisted tool-result files.** Large tool outputs are written to disk as separate files, not just into the transcript: this session alone produced `/home/pcalnon/.claude/projects/-home-…-buzzing-painting-meteor/<session>/tool-results/bd2fx0i2k.txt`. `find /home/pcalnon/.claude/projects -maxdepth 3 -type d -name tool-results | wc -l` → **67**. These are exactly where the oversized `journalctl` dumps land — *because* they were too large to inline. The checklist's transcript row does not name them.
2. **They are inside the backup source.** The design's own note **(AC-3a)** lists `.claude/projects` among the **unfiltered** 0700 trees that the capability exists to capture. So every persisted `journalctl` capture from this arc is (a) cloud-linked *and* (b) in every T1 fileset *and* (c) in Dropbox as ciphertext. §6's row says only "cloud-linked".
3. **The lanes' scratch trees.** `/tmp/claude-1000/-home-pcalnon-…-juniper-ml/` holds **95** per-session roots (`drwx------ pcalnon`). B3's own closing line says its scratch held "help-text captures, the extracted unit, the security-analysis output, and a copy of the archived owner prompt". Mitigating: `/tmp` is tmpfs, so a reboot clears them — that is worth *stating*, not leaving to inference.
4. **The ad-hoc instruments.** `util/ad-hoc/2026-09-21_env_value_equality.py`, `…_duplicati_settings_key_hash_probe.py`, `duplicati_api.py` (whose bare-secret fallback S-5a already flags) read secret files. Nothing in §6 says "an instrument that reads a secret file is itself a sink if it writes an artifact".

**Secret-shaped content scan** (counts only, as required; scripts in `…/scratchpad/r2_B_sec/`):

| File | Tokens of known-secret shape (len 30-40, contains one of `* @ $ %`, ≥3 char classes, non-path) | `enc-v1:` values | JWT-shaped | Credential assignment with non-placeholder RHS |
| --- | --- | --- | --- | --- |
| the design | 7 | 0 | 0 | 0 |
| the round-1 record | 4 | 0 | 0 | 3 |
| `util/ad-hoc/2026-09-22_reconcile_backup_design.py` | 3 | 0 | 0 | 0 |
| `util/ad-hoc/2026-09-22_apply_round2_corrections.py` | 2 | 0 | 0 | 0 |
| `util/ad-hoc/2026-09-22_credential_file_shape.py` | 0 | 0 | 0 | 0 |

I classified every one of the 16 by reading its line: all are option names (`SystemCallFilter=@system-service`, `--server-datafolder=${DATA_FOLDER}`), shell variable *references* (`SETTINGS_ENCRYPTION_KEY="${key}"`), a regex, and the two USB device UUIDs `EBC5-F0A3 DFF3-2782`. The three "assignments" in the record are the deliberate test placeholders `SETTINGS_ENCRYPTION_KEY=abc%6%xdef` and `envfilekey-16ch`. **No secret value is present in the design, the round-1 record, or any of the three new ad-hoc scripts.**

**Severity**: LOW-MEDIUM.

**Exact replacement text** — replace the transcript row and add one:

```
| Claude Code transcripts **and persisted tool-result files** under `~/.claude/projects/…` | cloud-linked, and **inside the backup Source**: note (AC-3a) lists `.claude/projects` among the *unfiltered* 0700 trees, so every capture is in every T1 fileset and in Dropbox as ciphertext. Large outputs are separate files under `<session>/tool-results/`, which is where this arc's oversized `journalctl` dumps landed; 67 such directories exist | count-grep and purge **both** the `.jsonl` transcripts and the `tool-results/` files; this is what makes D-2's "local exposure" framing false |
| Per-session agent scratch trees `/tmp/claude-1000/-home-…-juniper-ml/<id>/scratchpad/` | 95 roots, `drwx------ pcalnon`; round 1's six lanes each wrote captures, extracted units and analysis output there | `/tmp` is tmpfs, so a reboot clears them and they are **not** in the backup Source — state that rather than leave it inferred; until a reboot they are readable by every `pcalnon` process |
| Ad-hoc instruments that READ a secret file | `2026-09-21_env_value_equality.py`, `…_settings_key_hash_probe.py`, `duplicati_api.py` (bare-secret fallback, S-5a) | an instrument that reads a secret is a sink if it writes an artifact; each must state in its header what it writes and where, and none may write into `notes/`, `util/` or any path under the backup Source |
```

---

### R2B-14 — `RestrictAddressFamilies=` denies `AF_NETLINK` — LOW (availability, O-3 input)

`systemd-analyze security --offline` on the extracted unit reports `✓ RestrictAddressFamilies=~AF_NETLINK  Service cannot allocate netlink sockets`. glibc's `getaddrinfo` (`__check_pf`, `AI_ADDRCONFIG`) and `getifaddrs` use netlink; Kestrel binding a loopback listener may call them. Usually it degrades gracefully; it is the second-most-likely O-3 failure after `ProcSubset=pid`. **Replacement text**: covered by the R2B-10 paragraph above, which names it.

### R2B-15 — P0.5 item 1's literal command contradicts its own exception — LOW

Item 1 reads **`sudo chown -R root:root /usr/lib/duplicati`** *except* `data/` — but the command as given chowns `data/` too; the exception has no implementation. Harmless in effect (Procedure A `cp -a`s and re-chowns it anyway) but it is the one command in P0.5 an operator will paste verbatim. **Replacement text**: `sudo find /usr/lib/duplicati -mindepth 1 -maxdepth 1 ! -name data -exec chown -R root:root {} + && sudo chown root:root /usr/lib/duplicati` — *"`data/` is deliberately left as-is: it is the frozen evidence copy until P4."*

### R2B-16 — §7.4's script leaves a named ACL on the escrow that a later `chmod` silently re-enables — LOW

`setfacl -R -m g:duplicati:rwX -m d:g:duplicati:rwX "${ROOT}"` runs over the **whole** `Backups/` tree, *then* the `if` block chmods `_yamaguchi_keys` to 0700 and `env` to 0600. That works today only because `chmod`'s group bits set the ACL **mask** — the `g:duplicati:rwX` named entry survives with an empty mask. Any later `chmod g+rx` on those paths silently restores the service user's access. **Replacement text**: add `setfacl -R -b "${ROOT}/_yamaguchi_keys"` immediately before the two `chmod`s, and to the `echo NOTE` line: *"(the recursive `setfacl` above also touched this directory; `-b` strips the named entry, because a later `chmod g+rx` would otherwise re-enable it through the mask)"*.

---

## Top five

1. **R2B-1** — `ReadWritePaths=` is one level too high: the confined service can read *and unlink* the passphrase escrow (`_yamaguchi_keys/env`, group `duplicati` `rwx`, no sticky bit) and the frozen evidence set, with deletions propagating to Dropbox. This contradicts the §8 preamble's own "nothing is deleted or moved" rule, and the escrow is the sole key custody for T1 and T1c.
2. **R2B-3** — both `Environment=DUPLICATI__*` lines are inert. Neither name exists in either encoding across 646 files; the real names are `AUTOUPDATER_Duplicati_SKIP_UPDATE`, `USAGEREPORTER_Duplicati_LEVEL` / `DO_NOT_TRACK`, and `--disable-update-check` as an option. The sentence they justify — "the only legitimate network use … both disabled below" — is unsupported, and AC-14's `Unknown option supplied` grep structurally cannot see it.
3. **R2B-2** — "No egress" is false by construction. The reason given (Dropbox is a separate daemon) is exactly why a file write is an internet upload; `IPAddressDeny=any` bounds sockets only, and the capability-read surface is the whole host.
4. **R2B-4 + R2B-5** — two closures that do not bind, each on a stated reason that the document's own text refutes: `/etc/credstore` unmasked because "masking would break the start" (the manual says the *manager* reads it), and `.env` at `0640 root:duplicati` inside a directory the service user must own (delete permission comes from the parent).
5. **R2B-11** — the crossings table is missing the row that completes the kill chain: `$CREDENTIALS_DIRECTORY/settings-key` → any run-script → the server DB → the job passphrase → every volume in T1 and T1c, reachable from a UI credential that §6 S-5 says is world-readable today; and it marks two crossings "closed" by a channel the shipped unit does not use.

---

## Instrument adequacy — could my instruments have produced a different answer?

**Where they could not.** The syscall expansion is decisive: `expand_syscall_set.py` walks nested groups to a fixed point (18 groups, 395 calls) and `overlap.py` independently reproduces the design's `18`-member `@privileged` intersection member-for-member — a single-level `systemd-analyze syscall-filter @system-service` listing, which is what an unwary check would run, shows `name_to_handle_at` and no `open_by_handle_at` for the wrong reason (the nested groups are unexpanded), so the transitive form is the only one that answers the question asked. The literal scan is likewise strong in the direction it fired: my **first** pass grepped the DLLs as ASCII and returned `aes-version 0`, `webservice-password-init 0`, `webservice-disable-signin-tokens 0` — all **false negatives**, because .NET user-string literals are UTF-16LE in the `#US` heap while metadata names are UTF-8. Every conclusion in R2B-3 rests on the two-encoding scan, and the counts are *presence per file*, not occurrences.

**Where they could not settle the question.** My `LoadCredential=` + `InaccessiblePaths=` experiment (`systemd-run --user -p LoadCredential=… -p InaccessiblePaths=…`) returned "credential arrived, source still readable" — which looks like a clean answer and is **non-discriminating**, because the negative control failed: `systemd-run --user -p ProtectHome=yes /bin/ls /home/pcalnon` **listed the directory**, proving mount namespacing does not apply to user units on this host at all. The test therefore proved nothing and I discarded it; R2B-4 rests on the `man systemd.exec` text ("must be accessible to the service manager, but do not have to be directly accessible to the unit's processes"; "the **system service manager** will search … `/etc/credstore/`") plus the document's own §7.1 principle 3, not on that experiment. I am recording the failed control rather than the result.

**Where they over- and under-fire.** My first secret-shape scan (`secret_shape_scan.py`, 32-40 char mixed-class runs) returned 152 hits in the design and 196 in the record — essentially all English hyphenated compounds and option names; an entropy filter at 3.6 bits/char barely helped, because hyphenated prose has the same entropy as a key. Only the **known-shape** filter — length 30-40 **and** containing one of `* @ $ %` (the character class that B3's F-11 showed defeats the repo's gitleaks rule) **and** ≥3 classes **and** non-path — got to 16 hits across five files, each of which I classified by hand. A scan tuned to a *known* secret's shape is the only one that discriminated; a generic one would have buried a real hit in 350 false positives. Conversely it would **miss** a secret that happens to contain none of `* @ $ %`, so "no secret value present" is a claim about *these* secrets' shape, not a general clean bill.

**Where the target moved under the instrument.** The document changed three times while I read it — 1,882 → 2,126 → 1,882 lines, 02:31 → 02:47, and §11 shows rounds 2 and 3 already applied. Two findings I had drafted (AC-12's 5.2 gate; the guard's missing `additional_report_url` unset) were closed by a concurrent lane between reads, and I have reported them as AGREE rather than as my own. Any line number in this report is void; every citation is by heading text against sha256 `ac48092c…`.

---

## Open items, and the observation that settles each

| # | Question | Settling observation |
| --- | --- | --- |
| **B-O-1** | Does `InaccessiblePaths=-/etc/credstore` break `LoadCredential=` in a **system** unit on this host? | `sudo systemd-run --unit=credtest -p LoadCredential=t:/etc/credstore/<any-file> -p InaccessiblePaths=-/etc/credstore --pipe --wait /bin/sh -c 'wc -c < "$CREDENTIALS_DIRECTORY/t"'`. A byte count proves the manual's ordering; anything else refutes R2B-4's fix. Needs root. My user-unit attempt was non-discriminating (see instrument adequacy). |
| **B-O-2** | Does Duplicati 2.4.0.0 start and complete a backup under `ProcSubset=pid`? | O-3's `systemd-run` trial, run **first with `SystemCallErrorNumber=` unset** so a blocked call is a visible `SIGSYS` rather than a silent `EPERM` fallback. Decides R2B-10. |
| **B-O-3** | Is `AF_NETLINK` needed? | Same trial with `RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6` — a `getaddrinfo`/`getifaddrs` failure in the first-start journal answers it. Decides R2B-14. |
| **B-O-4** | What is the correct env-var name for a generic Duplicati option, upper or lower case? | `sudo -u duplicati DUPLICATI__disable_update_check=true /usr/local/lib/duplicati/duplicati-wrapper.bash --print-command` vs the upper-case form, or decompile `Duplicati.Library.Encryption.dll`'s `DUPLICATI__`-building method. Confirms the exact spelling for R2B-3; the *conclusion* (neither of the design's two names exists at all) is already settled by the scan. |
| **B-O-5** | Does `jwt-config` reach the job's option dictionary and therefore RunScript's environment? | On the P0 evidence-freeze copy: list `Option.Name` for the job **and** for `BackupID=-2` via `util/ad-hoc/2026-09-21_duplicati_server_db_forensics.py` (names only). Sizes R2B-8. |
| **B-O-6** | Does `SendStdOutToLogs` capture stderr, and does the option-override parser see it? | Read `RunScript.cs` `SendStdOutToLogs` at the 2.4.0.0 tag. Both `SendStdOutToLogs` and `set_RedirectStandardError` are literals in `Duplicati.Library.Modules.Builtin.dll`, so stderr **is** captured; only the parser question is open. The R2B-9 fix makes the answer irrelevant. |
| **B-O-7** | Does `PrepareSecureDataFolder` check **file** modes, not just the directory's? | `sudo -u duplicati` start against a scratch data folder containing one `0640` file, under `systemd-run` with the design's confinement. Decides whether §7.3.5's `0640 .env` is a start refusal as well as an ineffective mode. |
| **B-O-8** | How many `duplicati`-uid processes exist outside the unit at any moment, and for how long? | `pgrep -u duplicati` sampled across a day, plus `readlink /proc/<pid>/ns/mnt` compared against the unit's. Sizes R2B-6; §6 already records two live shells. |
| **B-O-9** | Is there a `duplicati-verification.json`-class option already set that carries a credential? | `python3 util/ad-hoc/yamaguchi_server_api.py export <id>` and list option **names** only, against R2B-8's allow-list. |

---

## What I could not determine

- Whether masking `/etc/credstore` is safe in practice (B-O-1) — documentary evidence only, root required.
- Whether the server survives `ProcSubset=pid` / no-`AF_NETLINK` — the design's own O-3, still open, and the reason I phrased R2B-10 as an instrument finding rather than a defect.
- The exact case convention of Duplicati's generic `DUPLICATI__` reader (B-O-4). What I *did* determine, and it is sufficient for the finding: neither `DUPLICATI__DISABLE_UPDATE_CHECK` nor `DUPLICATI__USAGE_REPORTER_LEVEL` exists in the install in any encoding, and the real mechanisms are `AUTOUPDATER_{0}_SKIP_UPDATE`, `USAGEREPORTER_{0}_LEVEL`, `DO_NOT_TRACK`, and the option `--disable-update-check`.
- Whether `additional-report-url` and `jwt-config` actually land in the *job's* option dictionary (B-O-5). Both are ServerSettings keys; the guard's unset now covers the first either way.
- Nothing was written outside `/tmp/claude-1000/…/scratchpad/r2_B_sec/` (scripts, the design snapshot, the extracted unit, the man-page dump, the syscall-set dump, and a 26-byte non-secret test credential). No repository file was modified; no secret value was read, printed or copied.

<!-- markdownlint-enable -->

---

## Report C (round 3) — confirmation pass over round 2's corrections

Subagent id `a84d1b8fcbaed0754` (36,854 characters). Archived verbatim.

<!-- markdownlint-disable -->

---

# Consensus round 3 — confirmation pass over round 2's corrections

**Document under review**: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`
**Repo**: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/buzzing-painting-meteor`
**Changed by this round**: **nothing.** No repository file was created, edited or deleted. All scratch output is under `/tmp/claude-1000/…/scratchpad/r3/`. The service was not touched, `duplicati-server` was never run in any form, nothing was written under `/mnt/Backups/Ubuntu/`, and no secret value was printed — the one credential probe reports lengths and character classes only.

---

## 1. Mandated instrument runs — literal results

**Pinned markdownlint** (`/home/pcalnon/.cache/pre-commit/repoft72ba_k/node_env-default/bin/markdownlint --config .markdownlint.yaml <doc>`, no `--fix`):

```
MARKDOWNLINT-EXIT=0
(node:1310259) [DEP0176] DeprecationWarning: fs.R_OK is deprecated, use fs.constants.R_OK instead
(Use `node --trace-deprecation ...` to show where the warning was created)
```

**Zero rule violations.** The two lines are a Node deprecation warning on stderr, not a finding. (Exit status captured directly, not through a pipe.)

**Snippet linter** (`python3 util/ad-hoc/2026-09-21_lint_design_snippets.py --doc <doc> --workdir /tmp/claude-1000/…/scratchpad/r3/lintwork` — absolute workdir, as instructed):

```
shellcheck: /usr/bin/shellcheck
tagged blocks found: 14
...
blocks: 14  failures: 0
RC=0
```

All 14 blocks pass: 8 × (`bash -n` + `shellcheck`), 4 × `systemd-analyze verify`, 2 × the `KEY=VALUE` / `--option` grammar. The `systemd-analyze verify` runs rewrote both `ExecStart=` paths into the absolute workdir and resolved.

**Bonus instrument (not requested, decisive for AC-12a)** — `systemd-analyze security --offline=true util/systemd/duplicati.service`:

```
→ Overall exposure level for duplicati.service: 1.7 OK 🙂
```
15 `✗` rows, and they are **exactly** the 15 named in note AC-12a, including `✗ SystemCallFilter=~@privileged … (e.g. chown is allowed)  0.2`. AC-12a's numbers are reproducible.

**Artifact drift check (not requested)** — I diffed all 14 extracted blocks against their landed repository copies. **Every one is byte-identical.** No drift between the design and what has been staged.

---

## 2. The 20 items

| # | Item | Verdict |
|---|---|---|
| 1 | §7.3.3 "warns and continues"; AC-14 exists and greps `Unknown option supplied` | **CONFIRMED** (AC-14 is mis-ordered in the table — see D7) |
| 2 | `Environment=` names corrected; `DUPLICATI__*` forms absent; `--disable-update-check` real | **CONFIRMED** (with an instrument caveat) |
| 3 | `@system-service` ≠ excludes `@privileged` wholesale (18/53); does exclude `open_by_handle_at` | **CONFIRMED** — reproduced exactly |
| 4 | `--password` pre-empts the DB branch; prompt is `Console.ReadKey(true)` | **CONFIRMED** (cited line numbers unverified) |
| 5 | server-util gate refusal silent; database-tool skips the gate | **PRESENT-BUT-MISLOCATED** — it is in §5.5, not §8 |
| 6 | `ReadWritePaths=` scoped to `…/Yamaguchi`; fix was necessary | **CONFIRMED** — parent is `0770`, no sticky bit |
| 7 | New `InaccessiblePaths=` entries all exist on this host | **CONFIRMED** — all 13 exist |
| 8 | `LoadCredential=` read by the service manager; masking is safe | **CONFIRMED** (one supporting quote is aimed at the wrong clause) |
| 9 | `.env` mode only binds outside the data folder (delete comes from the parent) | **CONFIRMED as reasoning; PRESENT-BUT-WRONG as shipped** — the remedy is unimplemented |
| 10 | Guard uses a positive filter; no URL/stray echo; `_keep_*` before the loop; lints clean | **CONFIRMED** on every sub-claim |
| 11 | §7.3.1 crossings table has six rows incl. the credentials-directory row | **CONFIRMED** — exactly six |
| 12 | P0.5 split into P0.5a/P0.5b; `usermod` moved from P4 | **PRESENT-BUT-WRONG** — copied, not moved; item 3's body duplicated |
| 13 | Both A0 scripts parse rather than `.`-source; premise holds | **CONFIRMED** — `dot-sourceable=NO`, no `set -a` |
| 14 | Neither A0 script uses `--no-local-db`; both `--dbpath` a copy | **CONFIRMED** |
| 15 | Step-3 probe: sqlite3 preflight, `encrypted-fields='True'`, `EnvironmentFile`, INDETERMINATE | **CONFIRMED**, but the block contradicts its own prose on the timeout |
| 16 | P0 step 8 places the recovered database for A0 and A2 | **CONFIRMED** |
| 17 | P0's alerting step precedes the credential-using step | **CONFIRMED** (9 before 10) |
| 18 | §8 preamble names nine missing scripts + P0 step −1; all now exist | **PRESENT-BUT-WRONG** — ten paths, not nine; one still missing and has no block |
| 19 | Cross-reference integrity | **15 defects** — see §3 |
| 20 | Status line / §11 / §12 agree with the document's actual state | **PRESENT-BUT-WRONG** — three-way inconsistency |

### Evidence, item by item

**1 — CONFIRMED.** §7.3.3's wrapper header states: *"2.4.0.0's `CommandLineArgumentValidator.ValidateArguments` logs `"Unknown option supplied: <name>"` as a WARNING and continues; the only non-zero exits in `Server/Program.cs` are 100 (unhandled exception) and 102/103 (`--webservice-password-init`)."* AC-14 exists in the §9 table with verification `journalctl -u duplicati.service --since <ts> | grep -c 'Unknown option supplied'` = 0. The literal `Unknown option supplied: ` is present in `/usr/lib/duplicati/Duplicati.Library.Utility.dll` — **utf-16le only**, so an ASCII grep misses it — and sits in the string heap immediately beside `UnknownOption` and `OptionValidationError`, i.e. a log tag, not an exit path. Independent behavioural corroboration from the document's own evidence: on 09-20 the glued `--daemon-opts="…"` word was accepted and the server started on 8200 (§4.2, §4.3 item 9). `webservice-password-init` is confirmed present in `Duplicati.Server.Implementation.dll`.

**2 — CONFIRMED, with a caveat that matters for anyone re-running the check.** My independent scan reported `scanned 1443 readable files under /usr/lib/duplicati` — matching the document's "all 1,443 files" exactly. `DUPLICATI__DISABLE_UPDATE_CHECK` and `DUPLICATI__USAGE_REPORTER_LEVEL`: **NOT FOUND**, utf-8 and utf-16le. The negative half is true.

The positive half is true but **the document's own cited instrument cannot show it**: `AUTOUPDATER_Duplicati_SKIP_UPDATE` and `USAGEREPORTER_Duplicati_LEVEL` are **also NOT FOUND** as complete literals. What exists are the format templates `AUTOUPDATER_{0}_SKIP_UPDATE` (`Duplicati.Library.AutoUpdater.dll`) and `USAGEREPORTER_{0}_LEVEL` (`Duplicati.Library.UsageReporter.dll`). I resolved `{0}` by extracting the embedded manifest resource `Duplicati.Library.AutoUpdater.AutoUpdateAppName.txt`: at offset 60684 a 4-byte LE length of **12**, payload `EF BB BF 44 75 70 6C 69 63 61 74 69` = UTF-8 BOM + **`Duplicati`**. So the substituted names are correct. `DO_NOT_TRACK` is a direct literal in `Duplicati.Library.UsageReporter.dll`, adjacent to `USAGEREPORTER_{0}_LEVEL`, `1`, `none`.

`--disable-update-check` **is** in `DAEMON_OPTS` (the §7.3.2 block and the landed `util/systemd/duplicati.default`), and it **is** a real server option: `disable-update-check` appears in `Duplicati.Server.Implementation.dll` inside the server option-name run alongside `tempdir`, `parameters-file`, `webservice-suppress-welcome-page`, `configure-https`, `ping-pong-keepalive`, `server-cli`.

**3 — CONFIRMED with numeric precision.** On systemd **259 (259.5-0ubuntu3.4)**, transitively expanded:

- `@privileged` closure = **53** calls (document: "53") ✓
- `@system-service` closure = 395 calls; overlap with `@privileged` = **18** (document: "18 of 53") ✓
  `capset, chown, chown32, fchown, fchown32, fchownat, lchown, lchown32, setfsuid, setfsuid32, setgroups, setgroups32, setresuid, setresuid32, setreuid, setreuid32, setuid, setuid32` — matching the document's exemplars (`chown/fchown/lchown`, `capset`, `setfsuid`, `setgroups`, `setres*uid`).
- `open_by_handle_at`: **not** in the `@system-service` closure, **is** in `@privileged` ✓. `name_to_handle_at`: allowed ✓. Exactly the asymmetry the comment claims.
- The direct-member listing has 61 entries of which 16 are nested groups; `name_to_handle_at` is a direct member and `open_by_handle_at` appears nowhere directly — so a direct listing genuinely cannot settle it, as the comment says.
- The predicted `systemd-analyze security` row exists verbatim at the predicted weight: `✗ SystemCallFilter=~@privileged  …(e.g. chown is allowed)  0.2`.

**4 — CONFIRMED (mechanism); line numbers unverified.** From `Duplicati/CommandLine/ServerUtil/Connection.cs` at tag `v2.4.0.0_stable_2026-09-03`: the signin-token-from-database branch is guarded by `if (string.IsNullOrWhiteSpace(settings.Password))`, so supplying `--password` **skips** it — `--password` pre-empts the DB branch, exactly as round 2 corrected. `opts["settings-encryption-key"] = settings.Key.Key;` sits inside that branch and is passed to `GetDatabaseConnection`, confirming that route needs the settings key. `Utility.ReadSecretFromConsole("Enter server password: ")` follows. `ReadSecretFromConsole` in `Duplicati/Library/Utility/Utility.cs` uses `Console.ReadKey(true)` in its loop. The exception text `Cannot read keys when either application does not have a console or when console input has been redirected` is present in the installed `System.Console.dll` — so the throw-on-redirected-stdin claim is the runtime's own behaviour, not an inference.

Offline corroboration from the installed `Duplicati.CommandLine.ServerUtil.Implementation.dll` string heap, in order: `…auth/signin` → `No database found in ` → `Failed to obtain a signin token: ` → `Enter server password: ` → `Password is required`.

**Not confirmed**: the cited line numbers `Connection.cs:250-262`, `Connection.cs:304-305`, `Utility.cs:2167`. The upstream file places them near 181-217, 236-237 and 2220. Markdown conversion may shift line numbers, so I will not call them wrong — but they are unverified.

**5 — PRESENT-BUT-MISLOCATED.** Both facts are recorded, correctly worded, and include the failure direction:
> "(1) `duplicati-server-util` applies the gate and its refusal is **completely silent** — exit 1, zero bytes on stdout *and* stderr… (2) `duplicati-database-tool` does **not** apply the gate at all… it resolves the folder in `AccessMode.ProbeOnly`… so never read a successful `wipe-encryption` as evidence that a folder's permissions are acceptable to the **server**."

But they are in **§5.5**, not §8, and **§8 never cross-references them**. That is a live gap: P0 step 6 is the only step that runs `duplicati-database-tool`, and it lists two other traps for that command without this one.

I did not re-execute either tool — `duplicati-server-util` defaults to `--hosturl http://127.0.0.1:8200/` and running it is a live-server interaction the brief bars. Offline corroboration: `Duplicati.CommandLine.DatabaseTool.Implementation.dll` carries `--allow-insecure-datafolder`, `server-datafolder`, `wipe-encryption` and the exact expected fragment `encrypted field(s) would be wiped`; `ProbeOnly` exists as an enum in `Duplicati.Library.Utility.dll`. The quoted phrase *"a no-op in ProbeOnly mode"* is a **source comment**, not a shipped string, so its absence from the scan is expected and is not a refutation. `/usr/lib/duplicati/changelog.txt` confirms the gate and all three overrides — including that the `insecure-permissions.txt` marker must be in the **installation** folder, which the document states correctly in both §5.5 and §7.3.2.

**6 — CONFIRMED, and the fix was necessary.** The unit reads `ReadWritePaths=/home/duplicati /mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi`. Measured:

```
drwxrwx--- 770 pcalnon:duplicati  /mnt/Backups/Ubuntu/Dropbox/Backups
drwxrwx--- 770 pcalnon:duplicati  /mnt/Backups/Ubuntu/Dropbox/Backups/Yamaguchi
```

The parent is group-writable by `duplicati` with **no sticky bit** — which under POSIX is precisely the permission needed to unlink any entry in it. Its entries include `_yamaguchi_keys/` (the passphrase escrow), `_yamaguchi_frozen_20260826/` (811 volumes) and ten `.dlist.zip.gpg` archives. A `ReadWritePaths=` on the parent would have let the service delete the only key custody T1 and T1c have, with the deletion propagating to Dropbox. The comment's reasoning is exactly right.

**7 — CONFIRMED.** Every path exists: `/etc/credstore` (`drwx------ root:root`), `/etc/shadow-` and `/etc/gshadow-` (`-rw-r----- root:shadow`), `/run/log/journal` (`drwxr-sr-x root:systemd-journal`), `/var/spool/cups` (`drwx--x--- root:lp`), `/mnt/Backups/Ubuntu/Dropbox/Backups/_yamaguchi_keys`, plus the pre-existing `/etc/shadow`, `/etc/gshadow`, `/etc/ssh`, `/etc/credstore.encrypted`, `/var/lib/docker`, `/var/log`, `/root`. Every entry carries the `-` prefix, so a later absence is non-fatal regardless.

**8 — CONFIRMED, with one mis-aimed supporting citation.** From `/usr/share/man/man5/systemd.exec.5.gz`, verbatim:

> "The credential files/IPC sockets must be accessible to the service manager, but do not have to be directly accessible to the unit's processes: the credential data is read and copied into separate, read-only copies for the unit that are accessible to appropriately privileged processes."

The document's first quote is verbatim from this sentence. ✓ The second quote — that it is *"the system service manager"* that searches `/etc/credstore/` — is also verbatim, but **that sentence governs the case where the `LoadCredential=` path is NOT absolute**. The unit uses an absolute path, for which the operative sentence is *"If the specified path is absolute it is opened as regular file and the credential data is read from it."* The **conclusion is unchanged** (the manager opens it before the unit's namespace exists, so masking does not break the start), but the second citation points at the wrong clause. The document already hedges correctly — *"Verify the mask before trusting this paragraph — it is part of O-12's `systemd-run` trial, not a tested fact"* — and supplies the trial command.

**9 — CONFIRMED as reasoning; PRESENT-BUT-WRONG as shipped.** The POSIX reasoning is correct: unlink permission comes from write+execute on the **parent directory**, not the file's mode; the data folder must be `0700 duplicati:duplicati` and owned by the service user so the server can write its database, so the `duplicati` uid can unlink-and-recreate a `0640 root:duplicati` `.env` inside it. No sticky bit would help — a directory's owner can always delete.

**But the remedy §7.3.5 issues is not implemented by the document's own artifacts.** §7.3.5 says *"Install it at `/etc/duplicati/env` in a 0755 root:root directory and point the wrapper's `DUPLICATI_ENV_FILE` default there."* Yet:
- §7.3.3's wrapper still reads `readonly ENV_FILE="${DUPLICATI_ENV_FILE:-/home/duplicati/.config/Duplicati/.env}"` (landed copy `scripts/duplicati-wrapper.bash:40`);
- `util/install_duplicati_service.bash` never creates `/etc/duplicati/` and installs no env file;
- the tagged block is still keyed `home/duplicati/.config/Duplicati/.env`, and Appendix B still lists that path.

`/etc/duplicati/env` occurs **exactly once** in the whole document — in the paragraph that mandates it.

**10 — CONFIRMED on every sub-claim.** `_keep_op` and `_keep_url` are assigned on the two lines immediately **before** the loop; the loop then blanket-unsets every `DUPLICATI__*` name read from `env` — a keep-list over that namespace, not a denylist. The `TargetURL` mismatch branch prints `scheme='…' length=… sha256-8=…`, never the URL. The stray filename is `printf '%s' "${stray##*/}" | LC_ALL=C tr -cd 'A-Za-z0-9._-' | cut -c1-64`. `bash -n` and `shellcheck` both PASS (block at doc line 1269), and the landed `util/yamaguchi-pre-backup-guard.bash` is byte-identical. Worth noting in its favour: `set -euo pipefail` + `trap 'exit 5' ERR` means a malformed env name reaching `unset` fails **closed** (exit 5 aborts the backup) — the correct direction for a `--run-script-before-required` hook.

**11 — CONFIRMED.** The §7.3.1 crossings table has exactly six data rows, and row 5 is `**$CREDENTIALS_DIRECTORY/settings-key → any run-script → the job passphrase**`, marked *"**NOT closed as shipped.**"* The prose header reads "the six crossings between them" — count agrees.

**12 — PRESENT-BUT-WRONG.** The split itself is real and correct (`### P0.5a — before anything in P0`, `### P0.5b — immediately after P0 step 8, same session`, and P0 step 8 exists). Four defects:
- (a) **`usermod` was copied, not moved.** P0.5a item 7 says "(moved here from P4)" — but **P4 step 3 still reads `usermod -s /usr/sbin/nologin duplicati`** verbatim.
- (b) **R-6's disposition cell is stale**: "Kept; `nologin` at the end of the migration (§8 P4)". §7.3.2's own comment gets it right ("moves from P4 to P0.5a").
- (c) **Item 3's full body is still printed inside the P0.5a list**, between items 2 and 4, and repeated in P0.5b. The list is headed "before anything in P0" and the item says "**Re-key now**" with the complete procedure. The disclaimer sits two paragraphs above the list, unattached. An operator working the list top-to-bottom executes the one step the split exists to defer.
- (d) P0.5a's items are printed **1, 2, 3, 4, 5, 7, 6**.

**13 — CONFIRMED.** Premise re-measured with the named instrument:
```
file: /home/pcalnon/.config/duplicati-backup/env  mode=0600  size=519  uid=1000 gid=1000
  line   9: ACTIVE  name='PASSPHRASE'      export=False len=32 quoted=False metachars='#$&@^' dot-sourceable=NO
  line  10: ACTIVE  name='PASSPHRASE_OLD'  export=False len=32 quoted=False metachars='$%*'   dot-sourceable=NO
```
Exactly the shape the scripts' comments assert (`'$', '&', '@', '#' and '^'`, `dot-sourceable=NO`). No value printed. Neither A0 script contains `set -a` or a `.`/`source` of the credential file — the only `set -a` hit is inside the explanatory comment at `util/ad-hoc/2026-09-22_confirm_a0_premise.bash:29`. Both use the same heredoc `re.match(r"^\s*(?:export\s+)?PASSPHRASE=(.*)$")` parser and export via the environment.

**14 — CONFIRMED.** `--no-local-db` occurs three times in the document, all three as prose explaining what is **not** used. Both scripts do `TMPDB="$(mktemp -u …)"; cp -p "${JOBDB}" "${TMPDB}"` and pass `"--dbpath=${TMPDB}"`, then `rm -f` the copy plus its `-wal`/`-shm`/`-journal` siblings. Both guard `[[ -s "${JOBDB}" ]] || … "(run P0 step 1's freeze first)"`.

**15 — CONFIRMED on all four sub-claims; one internal contradiction.**
- `command -v sqlite3 > /dev/null || { …; exit 2; }` ✓ — and `which sqlite3` returns nothing on this host, so the preflight is load-bearing, not decorative. (The Python `sqlite3` module *is* present, 3.53.4; the script uses the CLI.)
- Asserts `encrypted-fields` = `True` **and** `TargetURL` prefix `enc-v1:`, with the explicit "EMPTY values mean the QUERY failed, not that the copy is cleartext" refusal ✓.
- Key delivered by `EnvironmentFile`: `( umask 077; printf 'SETTINGS_ENCRYPTION_KEY=%s\n' "${key}" > "${envf}" )`, `chown duplicati:duplicati`, `-p "EnvironmentFile=${envf}"`, `shred -u` after. No `-p Environment=` anywhere ✓.
- `try_key` returns 0 only on `Server has started`, 1 only on a Mismatch, otherwise prints `INDETERMINATE (${label}): rc=${rc}` and `exit 5` ✓.
- **Contradiction**: the code sets `timeout -k 10 90` (90 s); the prose immediately after the block says *"The 45 s timeout ends the probe server"*.

**16 — CONFIRMED.** Step 8 opens "**First, place the recovered database.**" and gives `sudo install -d -m 0700 -o duplicati -g duplicati …` plus `sudo install -m 0600 -o duplicati -g duplicati <recovered>/Duplicati-server.sqlite /home/duplicati/.config/Duplicati/Duplicati-server.sqlite`, with an explicit "Do **not** copy a `-wal`/`-shm` sibling alongside it" and the failure it prevents ("`0 backups`, exactly where the arc began"). The index move and `DBPath` re-point follow in the same step.

**17 — CONFIRMED.** Step **9** = "Re-arm alerting FIRST — every command in step 10 goes through the API client"; step **10** = "Before the first run", which says "(the credential this needs was created in step 9)". Ordering correct and self-documenting.

**18 — PRESENT-BUT-WRONG on three counts.**
- The preamble names **ten** paths, not nine (`util/systemd/duplicati.{service,default}` is two files).
- **Nine of the ten now exist**, all staged (`A` in `git status`), and all **byte-identical** to their tagged blocks. So "**Nine of the paths below do not exist yet**" is now false:
  `util/install_duplicati_service.bash` (0755), `util/yamaguchi-pre-backup-guard.bash` (0755), `util/systemd/duplicati.service` (0644), `util/systemd/duplicati.default` (0644), `util/ad-hoc/2026-09-22_confirm_a0_premise.bash` (0755), `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash` (0755), `util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash` (0755), `util/ad-hoc/2026-09-21_backup_destination_permissions.bash` (0755), `util/juniper-backup-scheduled.bash` (0755).
- The tenth, **`util/install_juniper_backup_timer.bash`, does NOT exist** — and unlike the other nine it has **no tagged block** and **no Appendix B row**, so "all of which exist today only as tagged blocks in this document" is false for it and "P0 step −1 is to land them" is unexecutable for it. §7.3.4 and §7.8 both call it a **P3 deliverable**, contradicting its listing as a P0 step −1 item.
- Minor: "(Appendix B maps block → path)" — Appendix B maps block tag → purpose → linter, and its tags are *deployed* paths. The **repository** destinations for the four that differ appear only in §7.3.4 prose.
- Minor: "P0 step −1" has no item in the P0 list, which runs 0…11. It exists only in the header and this preamble.
- "`sqlite3` and `gitleaks` are **not installed**" — **CONFIRMED**, both absent.

---

## 3. Cross-reference defects, with exact replacement text

**Clean families.** Every `AC-N` (1–14), `D-N` (1–14), `R-N` (1–19) and `S-N` (1–8) reference in the document resolves to a defined row — **zero dangles** across all four. Every `P0 step N` / `P1 step N` / `P2 step N` / `P3 step N` / `P4 step N` reference resolves to an existing step. `note 1`…`note 6` resolve to §4.2's "Notes on the timeline" list; "note below" (§7.3.2) resolves to the paragraph that follows. `O-0…O-8`, `O-2`, `O-5` are explicitly external (the document states they are defined in `HANDOFF_2026-08-21_backup-systematization-design-arc.md`); `O-12` and `O-13` are defined in §11. All three companion records the status line and §11 cite exist on disk.

**D1 — §4.1, `duplicati.service` row.** `§4.3.9` is not a section; §4.3 is a numbered list. The document writes `§4.3 item 9` in three other places.
Replace `(§4.3.9, §5.5)` → `(§4.3 item 9, §5.5)`

**D2 — note D-12a, "Carried today" list.** Bare `§8.21.5`, no alias, no such section here; the target is YAM's. This is the one place the alias-only pattern (§11 dissent 6) actually breaks a lookup — every other `§8.x` in the document carries `YAM`/`Y` or a filename.
Replace `the §8.21.5 residuals` → ``the YAM §8.21.5 residuals``

**D3 — §2 requirements table, R-6 disposition.** Stale phase after the split.
Replace `Kept; `nologin` at the end of the migration (§8 P4)` → ``Kept; `nologin` immediately, in §8 P0.5a item 7 (moved out of P4 — a duplicati-uid shell outside the unit escapes §7.3.2's mount mask)``

**D4 — P4 step 3.** Duplicates P0.5a item 7, whose text claims it was "moved here from P4".
Replace ``3. `usermod -s /usr/sbin/nologin duplicati`.`` → ``3. *(Executed in P0.5a item 7 — kept here as the procedure of record; verify with `getent passwd duplicati`.)*``

**D5 — P0.5a item 3.** The re-key body is printed in full inside a list headed "before anything in P0", and repeated in P0.5b.
Replace the entire item with a stub carrying no procedure:
``3. **Moved to P0.5b — do NOT run this here.** The re-key runs the server against the *recovered* data folder, so it cannot precede P0 step 8; the procedure is in P0.5b below. (The number is kept so that §6's S-2 row, §7.3.5 and P1 step 1 still land.)``

**D6 — P0.5a list order.** Items print 1, 2, 3, 4, 5, **7, 6**. Swap the last two so the list reads 1–7.

**D7 — §9 acceptance table.** Row order is AC-1…AC-12, **AC-14, AC-13**. Move the `| AC-13 | The job's --run-script-before-required … |` row above the `| AC-14 | After any .env or DAEMON_OPTS change … |` row. (Notes AC-12a and AC-13a are correct as written; only the row order is wrong.)

**D8 — nine bare `P0.5` step/item references** now that the headings are `P0.5a` / `P0.5b`. All resolve loosely; **two are actively misleading** because they land on the P0.5a copy of item 3:
- header: `P0.5 items 1–2` → `P0.5a items 1–2`
- §6, S-2 remediation: `Re-key in **P0.5 step 3**` → `Re-key in **P0.5b**` ← **matters**
- P0 preamble: `Run P0.5 items 1 and 2` → `Run P0.5a items 1 and 2`
- P0 step 11: `(P0.5 item 2)` → `(P0.5a item 2)`
- §7.3.5: `it runs in **§8 P0.5**, not P1` → `it runs in **§8 P0.5b**, not P1` ← **matters**
- P0 step 5: `until P0.5's re-key replaces it` → `until P0.5b's re-key replaces it`
- P1 step 1: `*(Executed in P0.5 step 3 — kept here as the procedure of record.)*` → `*(Executed in P0.5b — kept here as the procedure of record.)*` ← **matters**
- P2 step 1: `moved to P0.5 step 1` → `moved to P0.5a item 1`
- P2 step 3 and note AC-8a: `P0.5 item 2` / `P0.5 item 6` → `P0.5a item 2` / `P0.5a item 6`

(Phase-level narrative uses of "P0.5" — §4.1 rows, §4.3 item 8, §5.5, §7.3.1, §7.7, P4 step 1, §11, §12 — are fine as they stand.)

**D9 — §11, Iterations bullet.** `**Round 3** … confirmed them; §12 records what it changed.` §12 has **no round-3 row**, and the sentence states round 3's verdict before round 3 ran.
Replace → ``**Round 3** (one agent, briefed on round 2's corrections) is a confirmation pass over that edit set; its verdict and any changes it caused are recorded in §12.``

**D10 — §8 preamble.** Replace the first sentence and the trailing clause with:
``**Ten paths are named below; nine have been landed in the repository and one has not.** §8 names `util/install_duplicati_service.bash`, `util/yamaguchi-pre-backup-guard.bash`, `util/systemd/duplicati.service`, `util/systemd/duplicati.default`, `util/ad-hoc/2026-09-22_confirm_a0_premise.bash`, `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash`, `util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash`, `util/ad-hoc/2026-09-21_backup_destination_permissions.bash` and `util/juniper-backup-scheduled.bash` — all nine now exist and are byte-identical to their tagged blocks here. The tenth, `util/install_juniper_backup_timer.bash`, has **no tagged block** in this document and is a **P3 deliverable** (§7.3.4, §7.8), not a P0 item. **P0 step −1 is to review and merge the nine**, extracted with `util/ad-hoc/2026-09-21_lint_design_snippets.py`; Appendix B lists every block by its *deployed* path, and §7.3.4 gives the repository destination for the four that differ. `sqlite3` and `gitleaks` are **not installed** on this host; step 3 needs the first and AC-8 the second.``

**D11 — §12, missing artifact row.** Add:
``| 2026-09-22 (later) | **Design artifacts landed (P0 step −1, nine of ten).** **Added**: `util/install_duplicati_service.bash`, `util/yamaguchi-pre-backup-guard.bash`, `util/juniper-backup-scheduled.bash`, `util/systemd/duplicati.service`, `util/systemd/duplicati.default`, `util/systemd/juniper-backup.timer`, `util/systemd/juniper-backup.path`, `util/systemd/juniper-backup.service`, `util/ad-hoc/2026-09-21_backup_destination_permissions.bash`, `util/ad-hoc/2026-09-21_probe_settings_key_on_copy.bash`, `util/ad-hoc/2026-09-22_confirm_a0_premise.bash`, `util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash`, `util/ad-hoc/2026-09-22_stage_design_artifacts.py`, `util/ad-hoc/2026-09-22_archive_consensus_reports.py`, `util/ad-hoc/2026-09-22_duplicati_literal_scan.py`, `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md`. **Changed**: `scripts/duplicati-wrapper.bash` (replaced by §7.3.3's v2 wrapper — this also executes P1 step 3). **Not landed**: `util/install_juniper_backup_timer.bash` (P3). |``

**D12 — P1 step 3 and S-1 are already executed in the working tree.** `scripts/duplicati-wrapper.bash` is now byte-identical to §7.3.3's wrapper v2 and holds **no** credential-shaped literal — its single `SETTINGS_ENCRYPTION_KEY=` is the legitimate `export` at line 126. Mark P1 step 3 and S-1's "Remove the block from the script (P1 step 3)" as executed-in-tree, pending merge. The S-1 exposure in `main`'s **history** is untouched; that half of the row stands.

**D13 — §7.3.5 vs §7.3.3 `.env` path.** (Item 9.) Minimum fix: change the wrapper's default to `readonly ENV_FILE="${DUPLICATI_ENV_FILE:-/etc/duplicati/env}"`; add `install -d -m 0755 -o root -g root /etc/duplicati` plus an env install to `util/install_duplicati_service.bash`; retag the block `etc/duplicati/env`; update Appendix B's row. Otherwise delete the instruction and record the residual instead.

**D14 — the probe timeout.** `timeout -k 10 90` vs "The 45 s timeout ends the probe server". `90` is what runs; fix the prose (or the code, deliberately).

**D15 — §8 does not point at §5.5's gate behaviours.** Add to P0 step 6, after "Two traps": ``and a third: `duplicati-database-tool` does **not** apply the 0700 data-folder gate (§5.5), so a clean run here is **no** evidence that the copy's folder is acceptable to the server — step 8's `install -d -m 0700` is what makes it so.`` And to step 3's server-probe paragraph: ``If `duplicati-server-util` is used at any point, note that its gate refusal is completely silent — exit 1, zero bytes on stdout *and* stderr (§5.5).``

---

## 4. What round 2 broke that round 1 had right

One structural regression, and it is the P0.5 split itself.

§11 records that **round 1** created the P0.5 bucket as a single ordered list. **Round 2** split it into P0.5a and P0.5b — correctly, because the re-key genuinely cannot precede P0 step 8 — but the split was performed **by adding headings and a disclaimer, not by relocating the content**. The consequences:

- Item 3's complete procedure is still printed inside the P0.5a list (D5), under a heading that reads "before anything in P0", and duplicated in P0.5b.
- `usermod` was announced as moved from P4 but only copied; **P4 step 3 still carries it** (D4), and R-6's disposition still points at P4 (D3).
- Nine references still say bare "P0.5" (D8), three of which now resolve to the wrong half.
- P0.5a's items print out of order (D6).

Round 1's single P0.5 was internally consistent; round 2's split is correct in intent and incomplete in execution. Nothing else I checked regressed — every product-fact correction round 2 made (items 1–5) holds up, the `--disable-update-check` addition is new and correct, and every landed artifact matches its block byte for byte.

---

## 5. Instrument adequacy

Each instrument here could have returned the opposite answer, and several did on some sub-claim.

The **literal scan** is the load-bearing one for item 2, and it is asymmetric by construction: a FOUND is strong (the byte sequence is present), a NOT-FOUND is weak (a name composed at runtime is invisible). That asymmetry bit in exactly the predicted place — it returned NOT FOUND for `AUTOUPDATER_Duplicati_SKIP_UPDATE`, the document's own chosen replacement. Had I stopped there I would have reported the correction as wrong. What settled it was a different instrument on a different layer: extracting the length-prefixed manifest resource `AutoUpdateAppName.txt` and reading its payload (`BOM + "Duplicati"`). Two of my own intermediate scripts returned false negatives from decoding the whole DLL as UTF-16LE — misaligned at odd byte offsets — which the byte-pattern search did not; the byte-pattern form is the correct instrument and is what the shipped `util/ad-hoc/2026-09-22_duplicati_literal_scan.py` uses.

The **syscall expansion** is discriminating rather than vacuous: the same code that returned `open_by_handle_at ∉ @system-service` returned `name_to_handle_at ∈ @system-service`, and independently produced 53 and 18 — three numbers that would all have had to be wrong together for a false confirmation. The direct-member listing (61 entries, 16 groups) shows why a shallower instrument reports nothing.

The **`systemd-analyze security --offline=true`** run reproduced AC-12a's 1.7, its 15 ✗ rows and the exact `@privileged` row text, so AC-12a is not a remembered figure. It is offline only — it cannot tell whether the server *runs* under the set, which is precisely what O-12 says is untested.

The **byte-for-byte diff** of all 14 blocks against the landed copies is the check that separates "the design says X" from "the repository does X". It is what found that the wrapper rewrite (P1 step 3) is already executed and that §12 does not record it.

The **cross-reference sweep** over-reported at first: 68 raw hits, of which 51 were external `YAM §` / `PLAN §` / handoff `§` references my first alias filter did not catch, and 6 were `note 1`–`note 6` resolving to a numbered list rather than a `**(x)**` label. Refining to "internal section refs with no alias in the prefix" left two — one malformed (§4.3.9) and one genuinely alias-less (§8.21.5). The `AC`/`D`/`R`/`S`/step families needed no refinement: all five resolved cleanly on the first pass, which is a real positive result given that P0 was renumbered twice.

Where an instrument was **not** available I have said so rather than inferring: the two gate behaviours (item 5) rest on shipped literals plus the changelog, not on execution.

---

## 6. What I could not determine

1. **The two gate behaviours in §5.5 (item 5) were not re-executed.** `duplicati-server-util` defaults to a live-server connection and `duplicati-database-tool`'s behaviour needs a data folder to run against; the brief bars server runs. Offline corroboration is consistent but is not a measurement. Round 2's own measurement stands unchallenged, not confirmed.
2. **The source line numbers** cited in §7.3.6 (`Connection.cs:250-262`, `:304-305`) and §7.3.6's `Utility.cs:2167`. The mechanisms are confirmed from the v2.4.0.0 source; the numbers did not match the file I fetched (≈181-217, ≈236-237, ≈2220), but markdown conversion can shift them, so I will not call them wrong.
3. **Whether `AUTOUPDATER_Duplicati_SKIP_UPDATE` is read at the right moment** for a systemd-launched server. I confirmed the name; I did not trace the call site.
4. **O-12 in full** — whether 2.4.0.0 actually runs under the §7.3.2 confinement set. Untested, and the document says so and gives the trial procedure.
5. **Everything in §4 and §5 that is a host-history claim** — journal and syslog counts, inode timestamps, the identity of the 09-18 key. Out of scope for this round, and §6 warns that re-measuring the counts creates a fresh complete copy of every leaked line.
6. **§4.2 note 1 / P0 step 1's open question** — whether `/usr/lib/duplicati/data/`'s main file is still cleartext with the encryption only in its `-wal`. Needs `sudo ls -la`; not attempted.
7. **Whether any of the 15 defects above were already known to round 2** — I was briefed on round 2's corrections, not its reports, so a defect I list may be one round 2 raised and the orchestrator deferred.

---

## 7. Bottom line

Of the 20 corrections: **13 CONFIRMED**, **6 PRESENT-BUT-WRONG or incomplete** (5, 9, 12, 15, 18, 20), **1 is the sweep** (19), which found 15 defects. **None is MISSING** — every round-2 correction is present in the document in some form, and every product fact I could re-verify independently is true, several to the digit (53/18, 1,443 files, 1.7 OK, 15 ✗ rows, `AutoUpdateAppName` = `Duplicati`).

The highest-value defects, in order: **D5** (the re-key procedure is printed under a heading that says to run it before P0 — the exact ordering error the split exists to prevent), **D10/D11** (§8 says nine scripts do not exist when nine of ten do, and §12 records none of them), **D4/D3** (`usermod` duplicated, R-6 stale), **D13** (§7.3.5 mandates a `.env` relocation that none of the document's own artifacts implement), and **D9/D14** (§11 claims a round-3 result that had not happened, and the probe contradicts itself on its timeout).

**Documents referenced**: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` (the subject), `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md`, `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md` and `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-STEP-REPORTS-RECORD.md` (existence verified on disk; not read this round).
**Documents changed by this round**: none.

<!-- markdownlint-enable -->
