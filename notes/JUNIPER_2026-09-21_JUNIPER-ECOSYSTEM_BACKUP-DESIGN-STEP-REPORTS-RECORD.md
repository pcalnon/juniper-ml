# Backup design — the five step reports the design was reconciled from (verbatim)

**Project**: Juniper (workstation backup infrastructure, host `yamaguchi`)
**Author**: Paul Calnon
**Date**: 2026-09-21
**Status**: RECORD — inputs to `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` §0 steps 1a, 1b, 2a, 2b, 2c
**Companion**: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md` (the validator reports)

## Why this file exists

The design's §0 says it was reconciled from five independent step reports with different entry points. Those
reports were subagent results that otherwise live only in one machine's session transcript. They are archived
here verbatim so that a reconciler (or a later reader) can check the design against what its inputs actually
said — Lane B2's "amputation" lens depends on exactly that comparison. Each report is preceded by a
`<!-- markdownlint-disable -->` marker because it is verbatim external text; nothing in a report was re-flowed,
corrected or trimmed (only trailing whitespace at line ends was stripped, by the repository's pre-commit hook).
**No secret value appears in any report**; the archive was scanned for secret-shaped content before being
committed.

Reports were delivered 2026-09-21 between 02:49 and 03:16 CDT; the design was drafted from them after that, so
live-state figures in report 2a are as of ~03:00–03:15 CDT and the design's §4 re-checked several of them at
13:37 CDT.


---

## Report 1a — Evaluate the ORIGINAL (documented) design strictly from the documents of record

Subagent id `a6ba27489be3746d5` (60,995 characters).

<!-- markdownlint-disable -->

# Docs-lane report — the ORIGINAL (documented) Juniper backup design, reconstructed strictly from documents of record

**Scope discipline observed.** Read-only; no live probes (no systemctl/journalctl/ps/ss/lsblk, no `ls` of `/mnt`). Of the two permitted non-repo files, **`/mnt/Backups/Ubuntu/README.md` does NOT exist at that path** (`cat`: "No such file or directory") — **NO ARTIFACT** — while `/mnt/Backups/Ubuntu/Dropbox/Backups/README.md` exists and carries exactly the content the record describes as "the README at the archive root". Repo scripts/units are cited as CODE artifacts, distinguished from prose.

**Citation key** (all repo paths relative to the worktree root; every citation uses these tags):
- **PLAN** = `notes/JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-BACKUP-SET-PLAN.md`
- **DMG** = `notes/JUNIPER_2026-08-23_JUNIPER-ECOSYSTEM_DUPLICATI-ARCHIVE-DAMAGE-FINDINGS.md`
- **FSC** = `notes/JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-FRESH-SET-CERTIFICATION.md`
- **GPG** = `notes/JUNIPER_2026-08-24_JUNIPER-ECOSYSTEM_DUPLICATI-GPG-FLUSH-FAILURE-INVESTIGATION.md`
- **YAM** = `notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md` (2,810 lines, §1–§8.27, read in full)
- **RUN** = `notes/JUNIPER_2026-08-22_JUNIPER-ECOSYSTEM_DUPLICATI-DB-RESTORE-RUNBOOK.md` — **WITHDRAWN, confirmed from its own banner**: "⛔ WITHDRAWN — DO NOT EXECUTE … This runbook's premise is false. It is retained as a specimen, not as a plan. Withdrawn 2026-08-22, before any step was run; confirmed 2026-08-23" (RUN:3-6)
- **CON** = `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`
- **LIFE** = `notes/JUNIPER_2026-08-16_JUNIPER-ECOSYSTEM_SNAPSHOT-LIFECYCLE-MANAGEMENT-DESIGN.md`; **STOR** = `notes/JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_SNAPSHOT-STORAGE-CONVENTION-DESIGN.md`; **V3** = `notes/JUNIPER_2026-09-12_JUNIPER-ML_WORKTREE-CLEANUP-PROTOCOL-V3-DESIGN.md`
- **REF** = `docs/REFERENCE.md`; **SCRIPT** = `util/juniper-backup.bash`; **UNIT:x** = `util/systemd/x`
- **H0821 … H0907** = `prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-21_backup-systematization-design-arc.md`, `…08-22_duplicati-dbpath-and-recovery.md`, `…08-23_duplicati-fresh-set-and-purge.md`, `…08-24_duplicati-gpg-failure-and-scheduled-lane.md`, `…08-25_duplicati-yamaguchi-certified-open-tail.md` (**H0825c**), `…08-25_duplicati-widened-scope-recertified-paul-gated-tail.md` (**H0825w**), `…08-26_duplicati-decisions-executed-root-gated-tail.md` (**H0826a**), `…08-26_duplicati-migrated-to-sda1-criterion-6-closed.md` (**H0826b**), `…08-27_backup-per-repo-review-and-arc-tail.md`, `…08-28_duplicati-tempdir-moved-drill-de-drifted.md`, `…08-29_duplicati-reboot-and-root-tail.md`, `…08-30_duplicati-cleartext-passphrase-and-escrow-tail.md`, `…09-07_duplicati-arc-outstanding-work.md`
- **DBX-README** = `/mnt/Backups/Ubuntu/Dropbox/Backups/README.md`

Other `notes/` hits for "duplicati" were false positives on "de**duplicati**on" (memory proposals, API primer); the only additional relevant notes are LIFE, STOR, V3 (and one line in the soak ledger).

**Validation procedure the later steps must follow (CON, summarized).** Two lanes, never one agent doing both (CON:36-37): **Lane A** re-derives observations from primary artifacts with *independent entry points* ("Three agents all starting from the same summary paragraph are one agent with three seats", CON:46-49), artifact over prose (CON:50-52), "NO ARTIFACT"/"UNTRACEABLE" must be an allowed answer (CON:53-54), instrument adequacy is part of the observation (CON:55-57); **Lane B** attacks conclusions — prompt to REFUTE (CON:65-66), steelman both sides of any decision (CON:67-69), different lenses (CON:70-72), and only on the reconciled measurement (CON:73). Pool size scales with uncertainty × criticality (matrix CON:81-85); escalators: overturns a document of record, sample <5, new/previously-wrong instrument, universal quantifier, a fix hangs on it, convenient finding (CON:87-94); the **only** de-escalator is independent end-to-end reproduction by a different instrument (CON:96-98). Run a second round when round 1 produced corrections, reviewers disagreed, the conclusion changed, or the work is top-right cell; brief round 2 on the corrections; stop only when a round changes nothing (CON:104-119). The reconciler separates measurement from interpretation disputes, re-derives any lone load-bearing finding, records unresolved dissent, states residual uncertainty (CON:127-136). Minimum record: instrument (and whether it could have said otherwise), sample size, agents/lanes/entry points, iterations and what the last changed, dissent, what the evidence cannot support (CON:159-168). Named failure modes of the procedure itself: false consensus, outsourced assertion, confident wrongness, review theatre, cost (CON:144-153).

---

## 1. What IS the documented backup design

### 1.1 The intended tiering (design of record)
PLAN:65-72: "This Duplicati job is **one tier of a three-tier posture**, and the tiering is by design": (a) **Duplicati `Ubuntu`** — "a physically separate on-host drive", **daily**, "fast, frequent, many restore points"; (b) **full Juniper archives** — "external drive, kept offline", **infrequent**, "air-gapped; survives host compromise/failure"; (c) **project archives** — "USB drives", "more frequent than the full archives", "portable, per-project". `/mnt/Backups/Ubuntu` (`/dev/sda1`, SATA) "**is** the intended home for this tier … `/home` is on `sdc`" (PLAN:74-76). The USB drive `sdb1` (WD My Passport, USB 2.0 hub, 39.4 MiB/s) was "rejected on measurement" for tier (a) (PLAN:91-102). **There is no cloud backup tier anywhere in the record** — cloud appears only as Duplicati *report* upload (§1.9) and a password-manager key escrow (§1.8). NO ARTIFACT for a cloud copy of data.

What actually existed on 2026-08-21: "Two mechanisms, **neither of which covers the system**": `util/juniper-backup.bash` (`Juniper/` tree only → external drive `DFF3-2782`) and the Duplicati `Ubuntu` job (`%HOME%` → `/mnt/Backups/Ubuntu`) (H0821:63-69). Structural verdict: "`tar` covers `Juniper/` only. Duplicati covers `$HOME` only" (H0821:88), so constraint C-2 of STOR ("copy + extract → full functionality", STOR:99) "cannot hold today" (H0821:96). Tier (b), the offline full archive, has **no artifact of its own** in the record beyond the plan's table row; the only evidenced "full archive" is a **plaintext** 111 GB `juniper-8.0.0_python_2026-02-27.tgz` on the USB drive `EBC5-F0A3` (H0827:373-376; LIFE:583-585).

### 1.2 Tier (a) — the Duplicati `$HOME` lane, three generations

**Gen 0 — job `Ubuntu` / `SJTCQIIZSJ`** (job id **2** on the pcalnon profile server: "`2` is the `Ubuntu` job id" RUN:182; identifiers H0823:80-84).
- Process/user/scope: `/usr/bin/duplicati` on **:8300 as pcalnon**, config `/home/pcalnon/.config/Duplicati/` (H0821:75); it ran in a GNOME session — "`app-gnome-duplicati-2525453.scope`, 'Application launched by gnome-shell', and `loginctl show-user pcalnon` reports **`Linger=no`**. The process therefore dies at logout … This is the mechanical root cause of the 42-day silent outage" (DMG:347-351). A second, **root** `duplicati-server` on :8200 (config `/root/.config/Duplicati/`, job `yamaguchi`) "never completed a backup" (H0821:76).
- Source/dest: `%HOME%` with 37 exclusions; destination `file:///mnt/Backups/Ubuntu` (DMG:360-361; RUN:192).
- Settings: `--blocksize` 100 KB "a stale default", `--dblock-size` 1 GB, `--skip-files-larger-than=50MB`, `--allow-missing-source=true`, gpg encryption (PLAN:118-124); retention `1W:1D,1M:1W,6M:1M,20Y:1Y`, auto-compact on, `startup-delay=30m`, schedule daily 07:03 `Repeat=1D` (H0822:58-60); UI schedule later disabled and `Schedule` table at 0 rows (DMG:317-318).
- Encryption: **gpg symmetric passphrase** — proven from packets: "`:symkey enc packet` — symmetric passphrase encryption. Duplicati's GPG module used a passphrase, not a recipient key" (YAM:1339-1350); the passphrase existed "only as an `enc-v1:` blob in the server database" (PLAN:124; DMG:324-328).
- Fate: wedged 2026-07-13 after the destination hit 4 KiB free (RUN:74-78; H0821:13-15); an interrupted compact deleted 1,208 dblock/dindex pairs, breaking every 2026-07 restore point (DMG:13-16, 45-70); volumes purged 2026-08-28 under option (b), ten dlists retained (YAM:1472-1542; DBX-README:1-22).

**Gen 1 — job `Ubuntu-fresh` / `DQRVQNDIFX`** (job id **3** in the profile DB; H0823:76-78; FSC:153).
- Run by **`duplicati-cli`** from the scheduled lane shipped in ml#1292: `systemd --user` `duplicati-backup.timer` `OnCalendar=*-*-* 02:30:00`, `RandomizedDelaySec=30m`, `Persistent=true`; service `Type=oneshot`, `TimeoutStartSec=infinity`, `Nice=10`, `EnvironmentFile=%h/.config/duplicati-backup/env`, `OnFailure=duplicati-backup-failure.service` (REF:557-569; UNIT:duplicati-backup.timer:7-15; UNIT:duplicati-backup.service:6-26). Installer copies, never symlinks, and refuses unless `env` is 0600 with `PASSPHRASE=` and `Linger=yes` (REF:538-555).
- Dest `file:///media/pcalnon/temp_backups/Ubuntu` (sdc4), dbpath `~/.config/Duplicati/DQRVQNDIFX.sqlite`, tempdir `/media/pcalnon/temp_backups/_duplicati_tmp` (a sibling on ext4), state dir `~/.local/state/duplicati` (REF:575-584); settings `--blocksize=1MB --dblock-size=500MB --skip-files-larger-than=2GB --no-auto-compact=true --allow-missing-source=true` (H0824:230-232), gpg.
- Record: "0-for-3 on full runs, with three *distinct* failure modes (GPGFlushError; pre-flight `ConstraintException` …; and an idle deadlock at the scan boundary …)" (YAM:58-66); its only fileset was a synthetic, ~45 %-partial manifest (FSC:13-26). Superseded; timer left `disabled`; "fails safe" because its default paths no longer exist (YAM:1619-1624). Removal PR never opened (H0907:198-200).

**Gen 2 — job `Yamaguchi`** (job id **2 on the system server**, job DB **`BMXWPAOGLP.sqlite`**; H0825w:77; YAM:389). This is the production design of record.
- Server: "`/usr/bin/duplicati-server` 2.3.0.4, port 8300, `--portable-mode`, **root**, unit `duplicati.service` with `Nice=19`/`IOSchedulingClass=idle`" (YAM:43-45), `Restart=always`, started at boot, independent of desktop login (YAM:628-630). Data root `/usr/lib/duplicati/data/` (root-owned `drwx------`) holding both `Duplicati-server.sqlite` and `BMXWPAOGLP.sqlite` (H0825c:222; YAM:1823-1825). Bind narrowed 2026-08-30 to `DAEMON_OPTS="--webservice-port=8300 --portable-mode"`, listening on localhost (YAM:1905). Web credential `DUPLICATI_WEB_CREDENTIAL` lives in the **primary checkout's untracked `.env`** (H0825c:207-209, 223).
- Job as certified (08:29 snapshot): dest `file:///media/pcalnon/temp_backups/Yamaguchi/`; source `/home/pcalnon/` with 46 filters; `encryption-module=aes`, `compression-module=zip`, `--blocksize=1MB` (irreversible), `--dblock-size=500MB`, `--skip-files-larger-than=8GB`, `--no-auto-compact=true`, `--allow-missing-source=true`, `--asynchronous-upload-limit=1`, `--tempdir=/media/pcalnon/temp_backups/_duplicati_tmp`, `retention-policy=1W:1D,1M:1W,1Y:1M,3Y:2M`, "daily 13:00 schedule" (YAM:75-93).
- Widened 2026-08-25 14:14 by Paul via UI: sources 1→3 (two VDIs), filters 46→44 (`*.iso`/`*.vdi` removed), `--skip-files-larger-than` **removed entirely**, schedule `Time=…14:00:00Z, Repeat=1D` = **09:00 CDT daily** (YAM:199-224); the running win11 VDI removed again 08-26 → **2 sources, 44 filters, 10 settings** (YAM:508-522).
- Destination migrated 2026-08-26 to **`/mnt/Backups/Ubuntu/Yamaguchi`** (sda1, the "only fstab-managed backup-class filesystem on this host") (YAM:923-948); tempdir moved 2026-08-28 to **`/home/pcalnon/.cache/duplicati-tmp`** (fstab-managed, covered by exclude filter 36 so the job cannot scan its own temp volumes) (YAM:1218-1264).
- Encryption: Duplicati's built-in **AES module (SharpAESCrypt)** under a passphrase; chosen because gpg reproduced GPGFlushError "under root, in a calm-memory window" and "AES … eliminates the external process, the 5 s `Join`, and every root-context gpg coupling" (YAM:99-111). "Old sets … remain gpg-encrypted and restorable; both passphrases stay retained" (YAM:110-111).

### 1.3 Users and systemd scopes (all generations)
| Component | User | Scope/unit | Source |
|---|---|---|---|
| Gen 0 `Ubuntu` | pcalnon | GNOME app scope, `Linger=no` | DMG:347-351 |
| Root :8200 legacy server | root | `duplicati.service`, `Restart=always`, `Nice=19`/idle | DMG:352-355 |
| Gen 1 lane | pcalnon | `systemd --user` timer/oneshot, `Linger=yes` | REF:557-569; H0824:126 |
| Gen 2 `Yamaguchi` | **root** | **system** `duplicati.service` on :8300, `--portable-mode` | YAM:43-45 |
| Watchdog (alerting B) | pcalnon | `systemd --user` `yamaguchi-watchdog.timer` 12:00 daily `Persistent=true`, depends on `Linger=yes` | YAM:340-358; UNIT:yamaguchi-watchdog.timer:10-13 |
| Server-DB snapshot | **root** | **system** `yamaguchi-server-db-snapshot.timer` `13:45:00 UTC` `Persistent=true` | YAM:1779-1795; UNIT:yamaguchi-server-db-snapshot.service:9-15; H0907:177-178 ("the arc spans two systemd scopes") |
| Certification drills/validates | pcalnon | `systemd-run --user` transient units (lease-proof) | YAM:291-295; H0825c:194-196 |

### 1.4 Encryption model per tier
| Tier | Model | Source |
|---|---|---|
| Duplicati old archive + fresh set | gpg **symmetric** passphrase (`--symmetric`, `--passphrase-fd 0`; user's `~/.gnupg/gpg.conf` governs — ZLIB tax) | YAM:1339-1350; GPG:94-102 |
| Duplicati Yamaguchi | built-in **AES** (SharpAESCrypt), passphrase; password passed on argv by the validate tool (accepted deviation) | YAM:83, 99-111, 162-164 |
| tar/USB lane | **asymmetric** OpenPGP `gpg -r <uid> -e` to **two YubiKey-backed recipients**; no YubiKey to write, any one to read | SCRIPT:27-31, 170-173; REF:669 |
| Server settings DB | **no** `SETTINGS_ENCRYPTION_KEY` → passphrase stored **cleartext** (owner accepted) | YAM:1919-1943 |

### 1.5 Credentials — where they live, how escrowed
- Authoritative: `~/.config/duplicati-backup/env` (388 B, 0600) holding `PASSPHRASE` (fresh/Yamaguchi) and `PASSPHRASE_OLD` (old archive), both 32 chars — "select by NAME" (H0824:128-131; H0823:174-197; H0825c:47-48). Filter 43 **excludes it from the backup** (YAM:1662-1663).
- Origin/sprawl: the worktree `.env` at `…/.claude/worktrees/curious-plotting-hummingbird/.env` still holds both in cleartext, is git-ignored and inside the Source, so it is "(accidentally) the only in-backup copy of `PASSPHRASE_OLD`" (YAM:1700-1706; H0829:51-56).
- Escrow (owner decision 08-29 "Both — an offline/printed copy and a copy on sda1", YAM:1738): sda1 copy `/mnt/Backups/Ubuntu/_yamaguchi_keys/env` (0600 in 0700) written by `yamaguchi_key_escrow.py`, whose three gates (inside a Source / same filesystem / **same physical disk** via `/sys/class/block`) were each demonstrated to fire (YAM:1745-1762); sheet in a synced password manager 08-31 (YAM:2313-2320); **printed 09-08, sheet shredded** (YAM:2781-2787). The value was also "banked … outside the machine" by the owner on 08-23 (H0823:37).
- Server brain: `Duplicati-server.sqlite` (job definition, 2 sources, 44 filters, 10 settings, schedule, **cleartext** passphrase) snapshotted daily via `sqlite3.backup()` + `PRAGMA integrity_check` into `~/.local/state/duplicati-server-db/`, which the 08-31 run demonstrably captured (YAM:1787-1795, 2209-2226). "This is not key escrow … It is a circle" (YAM:1797-1799).
- Web UI credential: `DUPLICATI_WEB_CREDENTIAL` in primary-checkout `.env` (H0825c:223). Cloud report URL embeds "a long-lived bearer JWT (issuer `api.duplicati.com`, expiring 2028) — it is a credential" (YAM:1888-1890).
- tar lane keys: "owner confirms multiple offline key backups exist in several modalities. A second recipient (Yubikey-3a) was added in #1223" (H0821:244-248). SOPS age key escrow script `juniper-deploy/util/sops-backup-key.sh` exists; "Whether it has ever been run is unknown (O-2)" (H0821:121-123).

### 1.6 Alerting / watchdog design
- Gen 1: `OnFailure` reporter writes `failures.log` (journal tail + `last-run.status`) then best-effort `notify-send`; "proven on a REAL failure at 23:48:24" (REF:567-569; H0824:127). Skip-escalation: a skip overwrites `result=OK`, so the next skip always escalates (REF:601-608).
- Gen 2, **candidate B (deployed 2026-08-26 12:30 CDT)**: `yamaguchi_watchdog.py` on a user timer, "Asks the server from outside, so it also catches … never ran, job definition vanished (the portable-mode trap presents as `JOB_MISSING`), server down, run stuck"; states `OK/RUNNING/STALE/JOB_MISSING/UNREACHABLE`, `--max-age-hours 26`, writes `~/.local/state/duplicati/server-watchdog.{status,log}` and `server-failures.log`, desktop notification (YAM:340-358, 493-506; UNIT:yamaguchi-watchdog.timer:6-13). Known gaps: "It never inspects `ProgramState`" and "anchors on the newest log entry of ANY `MainOperation`", so a 42.6 h paused-server outage went unreported (YAM:2192-2205). Candidate **A** (`--run-script-after`, root-owned under `/usr/local/lib/duplicati/`) drafted, never deployed, never revoked (YAM:359-365; H0907:231-232).
- Duplicati's own post-run sample test ("`TestResults: Success on 3 file(s)`") is used as run-level evidence (YAM:939, 1112).
- Census invariant: `yamaguchi_census.py` reconciles filesystem count/bytes vs server `TargetFilesCount/Size` — "only `AGREE`/`DIVERGE` carries signal" (YAM:963-975; H0907:13-15).
- Cloud reporting: `remote-control-enabled = True` with `additional-report-url = https://ingress.duplicati.com/backupreports/…` (YAM:1720-1722) — owner-deferred, not rejected (YAM:1888-1890).

### 1.7 Retention / compaction policy
- Gen 0: `1W:1D,1M:1W,6M:1M,20Y:1Y` with auto-compact on (H0822:59-60; DMG:339-341); the survivors "are **not** explained by the retention ladder" (DMG:262-266).
- Plan: "`--no-auto-compact` **`true`** initially — An interrupted compact is what destroyed the existing archive. Do not enable until a restore has been proven" and "retention policy — **none** initially, then generous" (PLAN:121-122).
- Gen 2: `1W:1D,1M:1W,1Y:1M,3Y:2M` **paired with** `--no-auto-compact=true` — "the pairing is load-bearing"; retention thinning "removes only the dlist (`FilesDeleted: 1` …); with `--no-auto-compact=true` a thinned fileset's exclusive dblock/dindex volumes remain until an explicit compact"; `1W:1D` "keeps the earliest fileset of each 1-day interval … plus always the newest" (YAM:90-91, 250-259; H0825c:49-54). "a manual compact is a separately-decided future operation, not a space-reclaim shortcut" (H0825w:53-55). Any purge on the old archive "must pass `--no-auto-compact=true` explicitly — the CLI default would compact the last 5 intact restore points" (H0825c:175-177).

### 1.8 Destination paths and identifiers
| Thing | Path / id | Source |
|---|---|---|
| Old archive (Gen 0) | `/mnt/Backups/Ubuntu` root, sda1 (mountpoint; `/mnt/Backups` is NOT one) | H0822:78-80 |
| Old archive residue after purge | 10 `duplicati-*.dlist.zip.gpg` + `README.md` at archive root; 2nd copy `~/.local/state/yamaguchi-old-archive-dlists/` (09-02) | YAM:1519-1528, 2548; DBX-README:42-47 |
| Fresh set (Gen 1) | `/media/pcalnon/temp_backups/Ubuntu` (sdc4); job DB `~/.config/Duplicati/DQRVQNDIFX.sqlite` — both retired 08-26 | H0823:77-78; YAM:1036-1038 |
| Yamaguchi live | `/media/pcalnon/temp_backups/Yamaguchi` → `/mnt/Backups/Ubuntu/Yamaguchi` (08-26) | YAM:75, 923-941 |
| Frozen pre-migration copy | `/mnt/Backups/Ubuntu/_yamaguchi_frozen_20260826` (811 volumes, AES) + sibling README (09-01/02) | YAM:2430-2441, 2550; DBX-README:58-62 |
| Records mirror / keys | `/mnt/Backups/Ubuntu/_yamaguchi_records/` (0775; frozen at 08-30) and `_yamaguchi_keys/` (0700) | YAM:1745-1748, 2576-2578 |
| Job ids | `Ubuntu`=id 2 (profile server), `Ubuntu-fresh`=id 3, `Yamaguchi`=id 2 (system server) — "**job 2 is a COLLISION**" | H0825c:185-187 |
| Orphan mapping | `dbconfig.json` once pointed the old archive at `KCSYQNVYOP.sqlite`, later the Yamaguchi destination at `DQRVQNDIFX.sqlite`; deleted 08-26 | FSC:151-155; YAM:668-702, 938 |
| Legacy root job | `yamaguchi` job on :8200 root profile, never completed | H0821:76 |

### 1.9 Plan §6 structural fixes → what the design of record did with them
Linger + user unit (PLAN:200-201) → lane shipped with `Linger=yes` (H0824:126), then superseded by the root system service; remove root `duplicati.service` (PLAN:202-204) → **reversed**: it became production ("repurposed to 8300 rather than removed", YAM:1973); alerting (PLAN:205-206) → watchdog B; server-DB backup (PLAN:207-209) → snapshot timer; stale description (PLAN:210-211) → NO ARTIFACT of correction.

---

## 2. Plan §7 acceptance criteria — CLOSED vs OPEN, per the record's own closure statements

The plan file itself **never ticks a box** — all six remain `- [ ]` in PLAN:219-230; closure lives only in YAM §8.7 and §8.27.

| # | Criterion (PLAN:219-230) | Record status | Closure statement (quoted) |
|---|---|---|---|
| 1 | Full backup completed | **CLOSED** | "[x] A full backup has completed successfully (task 5; and the widened scope, task 8)" (YAM:424); task 5: "726,130 files / 201.1 GB … `IsFullBackup: True`" (YAM:14-18) |
| 2 | Restore drill, checksum match | **CLOSED** | "[x] A restore drill has recovered real files with matching checksums (drill 1, §5.3)" (YAM:425); 14/15 + symlink proven (YAM:130-153) |
| 3 | Second drill, different restore point, after ≥1 incremental | **CLOSED** | "[x] … drill 2 (§8.4-3): fileset `20260825T191449Z`, 17/17" (YAM:426-428); "This is plan §7 criterion 3 … satisfied" (YAM:295-297) |
| 4 | Failure notification observed firing | **CLOSED 2026-08-26** | "[x] … B **deployed** 2026-08-26 12:30:59 CDT … closing test fired `JOB_MISSING` at 12:31:30 with the durable record and a desktop notification" (YAM:429-432); "**Plan §7 criterion 4 is closed**" (YAM:505). Caveat: the closing test was synthetic (`--backup-id 999`), and the earlier Gen-1 lane proof was on a real failure (H0824:127) |
| 5 | Survives logout/login and reboot | **OPEN until 2026-09-08, then CLOSED** | Open: "[ ] Logout/login and reboot survival — not yet exercised" (YAM:433-442); §8.23 refuted only a *hazard* ("it did not discharge the *criterion*", YAM:2593-2597). Closed: "Criterion 5 is CLOSED — the second half landed the same day … the `2026-09-08T14:00:00Z` run fired unattended and clean" and "**Criterion 5 — the last unexercised acceptance criterion in … §7 — is CLOSED**" (YAM:2660-2684). Two honest limits recorded: `pre` never ran; graphical login preceded `post` (YAM:2649-2658) |
| 6 | Migrated back to `/mnt/Backups/Ubuntu` + full backup + drill there | **CLOSED 2026-08-26** | "[x] Migration to a physically separate drive — **CLOSED 2026-08-26 (§8.13)** … copy … 811/811 … PUT 200 … proof run … census … AGREE, and a drill … 17/17" (YAM:443-449); "**Plan §7 criterion 6 is CLOSED**" (YAM:1024); scheduled-path proof 08-27 (YAM:1102-1118) |

Residuals the closures explicitly left behind (H0907:33-43): §8.21.5 residuals 2–3; §8.23.3 `paused-until` baseline; §8.24.3 re-verify rule; §8.25.6 `sda` health never verified.

---

## 3. Defects, traps and lessons any successor design must carry forward (imperative rules)

### A. Duplicati operation
1. **Never run `Repair` against a database that disagrees with its archive** — it "can re-upload volumes reconstructed *from the database* and delete remote volumes it does not recognise. It is the UI's default suggestion" (H0822:72-74; H0824:285-286).
2. **Never `kill -9` Duplicati**; TERM then wait — "a shrinking `-wal` beside a growing `.sqlite` means it is working" (H0822:75-77; H0824:287-291). An OOM kill "is functionally `kill -9`" (DMG:356-359).
3. **Run retention only with `--no-auto-compact=true`**; an interrupted compact under disk-full pressure "repacks … before deleting" and here did not (DMG:49-70); the pairing is load-bearing (H0825c:49-54). Never treat compact as a space-reclaim shortcut (H0825w:53-55).
4. **Do not let a size cap be the policy.** The 50 MB cap silently dropped four irreplaceable `.vdi` images and ~30 GiB of non-reproducible experiment logs while keeping 750 GiB of game data; exclude by identity (PLAN:188-193). The cap also excluded the job's own recovery databases — "Recovery files too large to be included in the recovery" (RUN:307-309).
5. **Pin `--blocksize` deliberately before the first run** — "cannot be changed after remote files are created"; 100 KB produced a 13 GB DB and a 49-day Recreate; verify the effective value rather than assuming inheritance (PLAN:118; H0824:228-233).
6. **Do not restore the archived job DB into a live job** — it "already contains the wedge", is six schema migrations old, disagrees with the archive by ~1.2 TB, and was taken mid-Compact (RUN:8-16; H0822:92-105). Read it only `immutable=1` (DMG:281-283).
7. **Duplicati has no dequeue verb**; queued tasks die with the process, and a completing Recreate would release 13 queued backups against a damaged archive (DMG:332-338; H0824:242-248).
8. **A timeout is not a result** — `list-broken-files` (90 min) and `purge-broken-files --dry-run` (8 h, rc 124) never finished; the offline census did in ~10 min (H0823:133-142).
9. **`--dbpath` is essential** on any CLI op; without it the CLI builds a DB from scratch or honours a hand-written `dbconfig.json` (H0822:154-155; YAM:668-702). Always pass `--dbpath`; the CLI expects `dbconfig.json` as a JSON *array* (YAM:377-385).
10. **`startup-delay` pauses the server for 30 min after any restart**; `Paused` + **non-empty** `SchedulerQueueIds` "is always a fault, whatever the uptime" (YAM:2187-2190). Read `paused-until` before resuming (YAM:2289-2296).
11. **Portable mode is a data-root switch.** Dropping `--portable-mode` makes the server "look in root's profile instead, find no job, and come up **empty**: … It presents as total loss and is merely a wrong data directory"; never activate the commented `/etc/default/duplicati` line (YAM:1823-1831; YAM:47-56).
12. **Backup reports may leak to a cloud endpoint with an embedded bearer token** — treat `additional-report-url` as a credential (YAM:1720-1722, 1888-1890).
13. **A retention-thinned dlist is not loss** — expect dlist counts to move; census on `AGREE`, not on fixed numbers (YAM:250-259; H0825w:72).

### B. Restore-drill validity
14. **`--no-local-blocks=true` is mandatory** — default false means Duplicati "rebuilds files from blocks found on the local disk … a false pass indistinguishable from proof" (DMG:216-218; FSC:106-108).
15. **Judge restores by SHA-256 + length, never exit code** — Duplicati "emits files and reports success even when they are empty" (DMG:200-212); rc 1 and 2 are success variants, only rc ≥ 3 fails (FSC:125-129).
16. **Select filesets by `--time=<timestamp>`, never positional `--version`** — the DB, not the destination, resolves versions; the "intact" arm read a damaged fileset (DMG:155-195).
17. **Drill destination-only** (`--dbpath` at a nonexistent path) with a **dual, job-DB-independent oracle** (manifest hash + live-source re-hash gated on pre-backup mtime); a vacuous oracle is INCONCLUSIVE, not PASS (FSC:100-116).
18. **Drill the NEWEST dlist, never `dlists[0]`**, and refuse if the newest changes mid-restore (YAM:301-305).
19. **A synthetic manifest is not a restore point** — a dlist written by a *different* run's reconciliation pass omitted ≥45 % of in-scope files "silently: absence is invisible by construction to the coverage check" (FSC:33-64).
20. **Partial restores need parent directories and in-tree symlink targets** under the 2.3.0.4 engine (YAM:140-149).
21. **A restore drill's `--run-root` must refuse volatile filesystems** — `ismount()` passed `/tmp` (tmpfs) and 1.5 GB went resident; "'Is a mountpoint' and 'is somewhere it is safe to write 64 GB' are different questions" (YAM:1189-1216).
22. **Keep restore drills paired with a negative control** (a flipped byte must fail) or the pass is vacuous (LIFE:507-509).

### C. Process, mount, filesystem
23. **No backup may run in a login-session scope without linger** — the 42-day outage mechanism (DMG:347-351; REF:527). Re-check `Linger=yes` after any reboot (YAM:356-358).
24. **Verify the mount before ANY destination operation**; "an unmounted destination reads as 'everything is missing', not as an error" and would fill `/` (H0823:209-215; YAM:628-635). Every destination path must be **fstab-managed** — sdc4 was only "observed" by systemd (YAM:611-622). Tools that move the job must refuse a non-durable target (`rc 7`, YAM:910-920).
25. **Never stage volumes on tmpfs** — `/tmp` staging put 8.4 GB in RAM with swap at 17/20 GB (H0824:132-134; DMG:356-359); guard 3b (REF:593). The same lesson must be carried into every later tool (YAM:1213-1216).
26. **Do not start backups in a memory-collapsed state** — the GPGFlushError mechanism is a hardcoded 5 s `Join` on the pump thread under writeback throttling, unretryable by construction, killing the whole queue; gpg is innocent (GPG:13-31, 76-116, 172-180). If gpg is used at all: `--compress-algo none`, `--asynchronous-upload-limit=1` (GPG:279-297); the design of record removed gpg instead (YAM:99-111).
27. **`pgrep -f` self-matches; bare `pgrep duplicati` matches the root daemon (`comm=duplicati-serve`)**; gate on who holds the DB open via `/proc/*/fd`, not on process names (H0823:100-103; REF:595-597). Never `ps` the duplicati family with a cmdline column during an AES validate — the passphrase is on argv (H0825w:158-159; H0907:246-249).
28. **`ps %CPU` is a lifetime average**, PSI decays, block-I/O counters are blind to tmpfs, a 110 s window extrapolates wrongly (H0824:158-162).
29. **Long jobs need `setsid`/transient units** — the background-task lease killed a 196 GB rsync at 190 GB (YAM:2447-2449).
30. **Never TimeoutStart a backup unit** — `TimeoutStartSec=infinity`, or systemd leaves a partial fileset (REF:564).
31. **Pin `OnCalendar` to UTC when the backup schedule is UTC** — a local time drifts across DST and silently misses its own backup by a day (YAM:1792-1795; UNIT:yamaguchi-server-db-snapshot.timer:9-15).
32. **A first `enable` of a `Persistent=true` timer does not catch up a same-day fire** (H0826a:40).
33. **Reboot verification must use checks that can fail** — `is-enabled` and `Linger` read persisted config; the evidence is that `systemctl --user` connects and a forced oneshot refreshes its artifact (YAM:1843-1851).
34. **Never delete a partition, or the second copy, before drive health is checked** — sdc4 was destroyed "with every gate bypassed" and "before the one check … named as owed *first*: `sda` drive health" (YAM:2686-2727). `ext4 errors_count = 0` is not drive health (YAM:2756-2771).

### D. Credentials
35. **Record the passphrase outside the backup and off the source disk** — the arc "certified restores … without ever asking where the key lives"; the key file shared physical disk `sdc` with the sources and was excluded by filter 43 (YAM:1644-1668). Do not "fix" it by moving the key inside a Source (YAM:1716-1717).
36. **`st_dev` does not distinguish partitions of one disk** — resolve the parent block device (YAM:1757; H0830:191-194).
37. **A file-vs-process secret divergence is invisible to file-only checks** — for 74 minutes the fresh set's key existed only inside one PID; run `duplicati_secret_check.py` around long secret-holding jobs (H0823:19-50).
38. **Name the passphrase key explicitly; two 32-char values are indistinguishable by length**; rotating never re-encrypts existing volumes, so retain `PASSPHRASE_OLD` indefinitely (H0823:174-197).
39. **Any GET/modify/PUT of a job must replace the 15-char passphrase mask with the real value**, guarded by a fingerprint check; never "simplify" it (YAM:366-373, 508-517).
40. **The server settings DB stores the passphrase in cleartext without `SETTINGS_ENCRYPTION_KEY`** — "treat this DB as key material"; never dump/diff it into a transcript; keep copies in 0700 dirs (YAM:1919-1943; H0907:246-249). Owner rejected the encryption key because it "adds a third key needing escrow" (YAM:1940-1942).
41. **Escrow before sweeping stray secrets** — the git-ignored worktree `.env` is deleted silently by `git worktree remove` (YAM:1683-1684, 1700-1706).
42. **Root-run backups include 0000-mode files a user run skipped** (e.g. the release-train private key); decide inclusion deliberately (YAM:319-325; H0824:263-266).

### E. Checker/tooling hygiene (the "stale checker" and "vacuous pass" classes)
43. **A tool that reports on a resource must locate it the way the system does (ask `TargetURL`)** — a hardcoded path "produces a confident, well-formatted, wrong answer"; the census printed a false `DIVERGE` (YAM:963-982). **Destination-only disaster tools instead take `--dest` with no default** (YAM:1179-1187). Five instances recorded (YAM:2583-2587).
44. **Sweep for the mount path, not the job name** — a `temp_backups/Yamaguchi` grep structurally missed `temp_backups/Ubuntu` (YAM:1963-1966).
45. **An existential test is not a universal one** — a `grep -q VERIFIED` gate would have authorised deleting the last fallback on 1 pass + 16 failures (YAM:1058-1077).
46. **Zero items must be a refusal, not a pass** — an empty destination printed "ALL VOLUMES DECRYPT-VALID" (YAM:2039-2057); a tool "returned exit 0 'all clear' on an unmounted destination" (H0823:253-254).
47. **A refused run must leave no trace** — `build_job` overwrote a provenance record before its guards ran (YAM:1266-1282).
48. **A verification flag that cannot change the outcome is cost without information** (`rsync --checksum` on an empty target) (YAM:867-890).
49. **A retirement tool must check what the standing sync does NOT cover** (YAM:1595-1604); a silent sync is the shape of a vacuous pass (YAM:1562-1568).
50. **Editors that write to live config must be `--dry-run`-opt-in aware** — the three live-config editors PUT by default (H0829:216-217).
51. **Deployed units execute the PRIMARY checkout's script** — merging changes nothing until it is pulled; editing the primary puts unreviewed code into the only alerting lane (H0907:171-176).
52. **Status files are not live state** — `last-run.status` is written only at run END (H0825c:188-190); `server-watchdog.status` has no freshness component (H0829:177-178).
53. **A filename set-diff across dblock/dindex is meaningless** — they are independent GUID spaces (YAM:1422-1435). **Check the packet type before reasoning about keys** — the expired YubiKey key was a red herring for a symmetric archive (YAM:1331-1350). **Pair every zero-result query with a known-present control** (YAM:1491-1498, 2223-2226).
54. **A grep for the NAME of a secret does not find the secret** (YAM:2393-2398); a loose alternation (`lid` in va**lid**ate) produces confident noise (YAM:2280-2283).

### F. Method — the "correct mechanism / wrong consequence" class (explicitly)
55. "The recurring failure shape in this arc is *a correct mechanism paired with a wrong consequence*" (DMG:289). Named instances: "the hyphen/setuptools claim, 'coverage is fine', 'no backup script exists', 'the job is orphaned', and 'the archive is untouched'. Every premise was individually true" (H0822:221-224); the withdrawn runbook "is an instance of it" (RUN:26-28); nine by 08-23 (H0823:258-259); the ZIP-warning "second damage class" that was refuted (DMG:225-236); a lifetime CPU average read as live load, a stale record read as the live schedule (H0825w:228-232); "a synthetic manifest called a restore point before the drill that would prove it" (H0824:392-397). **Rules:** "State what you *ran* separately from what you *reasoned*" (H0821:315-317); "Verify the conclusion separately from the premises" (H0822:224); "Prefer running the thing over reasoning about it — and check that what you ran is in the same regime as what failed" (H0824:396-397); "Never ship a prohibition on checking" (H0821:136); "Running a sweep is not reading it" (H0821:318); "quoting a section is not reading it" (YAM:1927-1929); "a record written the day before is not a record of today" (YAM:2609-2610); a finding "that lives only in a session handoff does not survive the handoff" (YAM:1648-1649, 2540-2542). Overstatement is the mirror failure — the arc "made that same class of overstatement three times" (YAM:2521-2522).

### G. tar/USB lane (see §7 for detail)
56. Prove every exclusion by output size, not by reading — "not one of the three exclusion mechanisms actually excludes anything" while shellcheck-clean (H0827:250-255; SCRIPT:70-73). 57. Name the extension after the compressor actually used (SCRIPT:144-149). 58. Judge COMPLETE on cross-repo totals (SCRIPT:55-57). 59. `--dry-run` must exit before the build loop (REF:651). 60. Unattended verify (`--list-packets`) "does **not** prove the tar is intact" (REF:685). 61. Add recipients before writing archives; none can be retro-fitted (SCRIPT:29-31).

---

## 4. Where the documents contradict each other or themselves (pairs, both citations)

1. **Yamaguchi schedule**: YAM:90-91 (§3) "daily 13:00 schedule" vs YAM:220-224 "the job now fires **daily at 09:00 CDT** … not the 13:00 CDT §3 describes" (§3 carries a superseded banner, YAM:70-73; §3's "13:00" itself is 18:00Z, H0825c:147-149).
2. **`additional-report-url`**: PLAN:205 "`additional-report-url` is empty" vs YAM:1720-1722 "`additional-report-url = https://ingress.duplicati.com/backupreports/…`". Different servers (pcalnon profile vs root portable) — never reconciled in text.
3. **Plan never updated**: PLAN:6 "Status: Destination CHOSEN (`/media/pcalnon/temp_backups`, temporary)" and PLAN:238 "SETTLED — `/media/pcalnon/temp_backups` interim" and all six §7 boxes unticked (PLAN:219-230) vs YAM:443-449 migration CLOSED and YAM:2683-2684 criterion 5 CLOSED. H0825w:128 instructed "Record the decision in the plan's §8" — NO ARTIFACT of that edit.
4. **Root service: remove vs production**: "Remove or repurpose the root `duplicati.service` on port 8200" (PLAN:202-204), "Candidate for removal rather than migration" (DMG:352-355; H0821:256-258; H0822:196-197; H0824:250) vs "that unit, now on 8300, IS the production backup server; never remove it" (H0825c:14-17; H0825w:55-56). YAM:1973 records it as an orphaned §7 item, "repurposed to 8300 rather than removed".
5. **"Encrypted" vs cleartext passphrase in the server DB**: original YAM §8.6-7 / §8.18.2 / §8.19.3, H0825w:121-122 "it carries the encrypted passphrase blob", H0829:112 "and the **encrypted passphrase**" vs YAM:1919-1925 "The passphrase is stored in CLEARTEXT … 'No database encryption key was found'". Corrected in place (YAM:397-402, 1693-1694, 1801-1804), but **still uncorrected in code**: `util/ad-hoc/yamaguchi_server_db_snapshot.py:20` (YAM:2570-2572; H0907:209-211) and UNIT:yamaguchi-server-db-snapshot.service:5 ("the encrypted passphrase"). Separately: the pcalnon profile DB **did** hold `enc-v1:` blobs (PLAN:124; DMG:320-328; H0821:118-119) while the portable root DB is cleartext — the record never explains the difference.
6. **sdc4 intact vs destroyed**: YAM:2551 "sdc4 unmounted — partition **intact** … retired from service, not destroyed" and H0907:27 "EXISTS … **not destroyed**" vs YAM:2686-2699 "sdc4 is DESTROYED … 1.845 TiB is now unallocated" (marked SUPERSEDED in place).
7. **Restore point "lost" vs manifest only**: YAM:2359-2361 "Deleting sdc4 therefore **permanently loses one restore point**, not merely a copy" vs YAM:2510-2519 "That is right about the **manifest** and wrong about the **data** … 0 of its 1,216,100 blocks are absent from the live index".
8. **Tool defaults**: YAM:2126-2129 "`--encryption` still defaults to `gpg` in both tools" vs YAM:2560-2563 "`duplicati_dlist_query.py` has defaulted to **aes** since its introduction" (H0907:255-258).
9. **Escrow claims**: YAM:1769-1771, 1984-1986 "`PASSPHRASE_OLD` still has no copy outside `sdc` + sda1" vs YAM:2317-2320 "is now false … A synced password manager is off-machine".
10. **"Root-only" key material**: YAM:1674-1676 / H0829:33-34 "`PASSPHRASE` survives only as root-only material in a single unbacked-up DB" vs H0830:134-136 "now false three ways … the value was never root-*only*".
11. **Archive-root README location**: YAM:1540-1542 "A `README.md` was written at the archive root", YAM:2503-2504 "`/mnt/Backups/Ubuntu/README.md` asserts …", YAM:2549 "`/mnt/Backups/Ubuntu/README.md` corrected" vs the live path absent and the documented content at `/mnt/Backups/Ubuntu/Dropbox/Backups/README.md`, whose own text says `--dest /mnt/Backups/Ubuntu` (DBX-README:26-28). NO ARTIFACT at the documented path.
12. **Server DB size** stated variously: 192 KB (H0821:112, 118), ~470 KB (PLAN:207; H0822:207), 479 KB (DMG:314; H0822:29), 180 KB (RUN:68; H0824:258), 160 KB (YAM:1906) — different files/times, never disambiguated by name.
13. **Fresh-runner exclusion count**: H0824:267-268 "`duplicati_first_backup.bash:116` prints `exclusions : 44`; there are 43" vs YAM:80-81 "the Ubuntu-fresh exclusion set parsed live from the runner (44)".
14. **"Schedule closed and verified"**: DMG:317-318 "the `Schedule` table now holds **0 rows** … no further runs are enqueued" vs H0824:336-338 "The `Schedule` table … is EMPTY … the predecessor's 'schedule closed and verified' does not hold" — same fact, opposite framing of what it proves.
15. **tar lane status**: H0827:20-30 "B1 … STILL BROKEN … B2 … STILL PRESENT … B5 … STILL INVERTED" (main `99df9bf0`) vs REF:680-696 / LIFE:552 (all fixed by juniper-ml#1439). Time-ordered, but H0827 — the last handoff on the lane — carries no supersession banner.
16. **"Nothing else is outstanding"**: YAM:1640-1641 "Every retirement tier is executed …" vs YAM:1644-1649 "§8.17.5's 'Nothing else is outstanding' is superseded by this section" (the key-excluded finding).
17. **Frozen copy "different physical disk"**: YAM:1043-1048 "a second … copy of the live set on a different physical disk" (sdc4 vs sda1 — true) vs the §8.18 framing that the sdc4 copy "is not a second disk" relative to the *sources* (YAM:1656-1657; H0829:206-207) — both true, different referents; a reader takes "second copy" as source-independent.
18. **Deviations from plan (not contradictions, but unrecorded in the plan)**: skip cap 2 GB (PLAN:120) → 8 GB → removed (YAM:85, 214-215); retention "none initially" (PLAN:122) → set from day one, "Paul's choice" (YAM:90-91); decision 6 "same passphrase or new" (PLAN:243) → new key for fresh/Yamaguchi, old retained (H0823:174-197).

---

## 5. What the documented design left UNCOVERED or deferred, and pending owner decisions

**Coverage gaps (by design or by omission)**
- **`/var/lib/docker/volumes`** — "16 juniper Docker volumes exist, including `…_juniper-cascor-snapshots` … C-1 material, zero copies" — outside both legs (H0821:90-91, 185). NO ARTIFACT of any later remedy.
- **`/opt/miniforge3/envs`** — 47 GB, 11 envs, outside both legs; "Regenerable in principle — confirm the recipes are in git" (H0821:92, 186). NO ARTIFACT of confirmation.
- **Credentials outside `Juniper/`** (13 SSH keys, `~/.gnupg`, `gh`, `.kaggle`, SOPS age key) — covered by Duplicati only, never by tar (H0821:93-94, 187-190).
- **GitHub-side state** — "issues, PRs, releases, Actions secrets has no local copy at all" (H0821:192). NO ARTIFACT of remedy.
- **`juniper-legacy`** (18 GB, no `.git`) — "**not** in the default list" of the tar lane (REF:657; H0827:213-214); Duplicati covers it only as part of `$HOME`.
- **Duplicati's own state under `~/.config/Duplicati/`** is excluded by live filter 41 (YAM:1398), yet the KEEP list says never sweep `backup SJTCQIIZSJ 20260712033545.sqlite` (13 GB, "the only pre-deletion state of the old archive") and the orphaned profile server DB (YAM:478-485). *Inference from these two cited facts*: those files exist in **one copy on sdc3**, in no backup.
- **The passphrase file** `~/.config/duplicati-backup/env` is excluded by filter 43 (YAM:1662-1663) — by design, mitigated by escrow (§1.5).
- **`.cache/`** (filter 36) holds the regenerable escrow sheet and the tempdir by design (YAM:1764-1766, 1227-1229).
- **The running win11 VM image** was excluded 08-26; only the static win10 VDI is backed up (YAM:508-529). `VirtualMachines/` otherwise excluded (filter 40), plus Steam, StarfieldData, Downloads, `juniper-data/data`, rust build dirs (YAM:1388-1399).
- **`/usr/lib/duplicati/data/BMXWPAOGLP.sqlite`** (job index) is in no backup; "Recreate rebuilds it … Slow, not fatal" (H0829:108-110). The server DB is covered only via the snapshot lane (YAM:2209-2226).
- **Off-host / offsite**: O-5 "is offsite in scope, or is on-site redundancy the accepted posture?" (H0821:251-252) — **never answered in the record**. After sdc4's destruction "everything backup-related is on sda1 alone" (YAM:2400-2403, 2686-2727); the only off-machine artifacts are the escrow copies.
- **Retention depth for short-lived files**: as of 09-12 "9 filesets, 18 days max depth, ~7 days for a short-lived file"; "The **tar** archive covers none of it" (V3:218).
- **tar lane excludes** `.claude` (hence worktrees), `data`, `logs`, `reports`, `resources`, `venv`, `dist`, `build` per repo (SCRIPT:111); loose parent-level files are not archived (LIFE:577-578).
- **The stale job description** ("Development and Documents folders") — PLAN:210-211; NO ARTIFACT of correction.

**Owner decisions recorded as pending (latest state in the record, 2026-09-08 / 09-12)**
1. `sudo smartctl -H -A /dev/sda` — "the single highest-value unchecked fact in the arc: … it guards the only remaining copy" (YAM:2773-2777, 2799).
2. Read-only loop probe of the deleted sdc4 extent, then decide on recovering 2.3 KB and/or the 196 GB copy (YAM:2729-2754, 2800).
3. The sdc2 NTFS-on-GPT grow beside live `/home` (YAM:2481-2495, 2801; H0907:98-108).
4. Cloud reporting — "owner-**deferred, not rejected**" (YAM:1888-1890; H0907:223-225).
5. Removal PR for the disabled user lane (`util/systemd/duplicati-backup.*`, `~/.local/bin` copies) — "still unopened"; deployed copy diverges from repo (H0907:193-200; YAM:2530-2533).
6. Watchdog `ProgramState` + queue check — "still worth building" (YAM:2302-2303; H0907:162-178); `paused-until` baseline sample (YAM:2289-2296).
7. De-drift `yamaguchi_records_sync.bash` or label the mirror historical — two bodies of certification evidence "exist **only as prose in this note**" (YAM:2574-2587).
8. Three Duplicati exclusion filters for regenerable classes under worktree roots — V3 Q4 **OPEN** (V3:696-701, 1038).
9. `--run-script-before` mount guard (remedy iii) "never applied or refused"; alerting A never revoked (H0907:229-232).
10. Reconcile/delete the stray worktree `.env` (H0907:218-222).
11. From H0821: O-1 (is `juniper-data` regenerable — treated as re-downloadable in YAM:1394 but never formally closed), **O-2** (has `sops-backup-key.sh` ever run — NO ARTIFACT), **O-5** (offsite — NO ARTIFACT), O-8 (resolved in effect by removing the cap).
12. tar lane: delete the 111 GB plaintext `.tgz` on `EBC5-F0A3` "Once the owner is satisfied with the set" (LIFE:580-585) — NO ARTIFACT of deletion.
13. PLAN decision 7 (retention) was "Deferred until restores are proven" (PLAN:244) — set by Paul instead; no plan amendment.
14. Drift-guard test port across seven repos (H0907:123-149) — not backup-specific.

---

## 6. Server data folders, settings key, and process/user ownership over time (documents only)

| Date | State | Source |
|---|---|---|
| ≤ 2026-07-09 | pcalnon instance `/usr/bin/duplicati` on **:8300**, data `~/.config/Duplicati/` (job `Ubuntu`), launched by gnome-shell, `Linger=no`; root `duplicati-server` on **:8200**, data `/root/.config/Duplicati/`, job `yamaguchi` never completed. Last successful backup 2026-07-09 | H0821:73-76; DMG:347-355; RUN:74 |
| 2026-07-12/13 | Pre-upgrade auto-snapshots of both DBs (schema-migration pairs, 2023-06 / 2025-08 / 2026-07); `BackendQuotaNear` 4 KiB; strict-mode wedge 07-13 | RUN:63-68, 74-78, 278-293 |
| 2026-08-21 | Owner frees 1.1 TB, runs Repair + Resume ("server had been **PAUSED**"), scheduled run fails, starts Recreate 19:27:16; owner's manual copy `Duplicati-server_2026-08-21.sqlite` (not automatic); `Backup.DBPath` silently changed to the **server** DB between 18:19 and 19:27 | H0821:17-29; DMG:370; H0822:18-36, 204-206 |
| 2026-08-22/23 | DBPath corrected in UI (pid unchanged); `Schedule` table 0 rows; the two same-length `enc-v1` re-encryptions prove the stored passphrase intact | DMG:314-328 |
| 2026-08-23 | Fresh job `Ubuntu-fresh` (id 3, `DQRVQNDIFX`) run by `duplicati-cli` as pcalnon; creds in a worktree `.env`; tmpfs staging; run 1 hang / run 2 rc=100 | H0823:74-85; H0824:42-47, 132-134 |
| 2026-08-24 | Scheduled lane (`systemd --user`, `Linger=yes`); creds moved to `~/.config/duplicati-backup/env`; `dbconfig.json` maps old archive → `KCSYQNVYOP.sqlite` (orphan) | H0824:113-134; FSC:151-155 |
| 2026-08-25 02:30–02:46 | TrayIcon (2.0.8-era binary from a **stale autoupdater shadow install** `~/.config/Duplicati/updates/`) crashes after a 2.3.0.4 run upgraded the profile server DB schema 11→19; shadow renamed `updates.disabled-2026-08-25`; **root system `duplicati.service` restarted on :8300 with `--portable-mode`** → data root **`/usr/lib/duplicati/data/`** | YAM:33-45 |
| 2026-08-25 04:10 | `/etc/default/duplicati` edited to loopback **without** `--portable-mode` — the RESTART TRAP (running process still portable) | YAM:47-56 |
| 2026-08-25 ~03:13 | Hand-written `dbconfig.json` (BOM, single object) mapping Yamaguchi dest → `DQRVQNDIFX.sqlite` | YAM:668-689 |
| 2026-08-25 14:14 | Paul: `DAEMON_OPTS="--webservice-interface=any --webservice-port=8300 --portable-mode"`; trap closed; loopback survives only as a comment lacking `--portable-mode` | YAM:225-228, 1614-1618 |
| 2026-08-25 | Job `Yamaguchi` id 2 imported on the portable server; job DB `BMXWPAOGLP.sqlite`; profile server DB (`~/.config/Duplicati/Duplicati-server.sqlite`, schema 19, jobs `Ubuntu`/`Ubuntu-fresh`) left **orphaned from any running server** | YAM:94, 194-195; H0825w:77 |
| 2026-08-26 | `dbconfig.json` deleted (archived); `updates.disabled-2026-08-25/` deleted in Tier 1 | YAM:938, 854-857 |
| 2026-08-29 | Escrow tooling; server-DB snapshot tooling; narrow-bind script ("Deleting the flag is sufficient" — DB already stores `server-listen-interface = loopback`) | YAM:1745-1748, 1812-1833 |
| 2026-08-30 01:08 | Owner: `DAEMON_OPTS="--webservice-port=8300 --portable-mode"`, rollback file kept, "listening on localhost, port 8300"; `yamaguchi-server-db-snapshot.timer` (system, root) enabled, snapshot 160 KB `integrity_check ok`; **settings encryption key**: "No database encryption key was found. The database will be stored unencrypted. Supply … `SETTINGS_ENCRYPTION_KEY` or … `--disable-db-encryption`" — owner **rejects** the key ("adds a third key needing escrow") and accepts cleartext; recipe target moved to `_yamaguchi_keys/` | YAM:1901-1943; H0830:24-30, 68-71 |
| 2026-08-30/31 | Server `Paused` past `startup-delay` for 42.6 h with a queued job; resumed by API; restart test shows normal auto-resume; root cause unknown | YAM:2142-2166, 2239-2287 |
| 2026-09-07/08 | Three reboots; `duplicati.service` returns 33 s after boot; user manager up before any graphical session (linger proven); `ProposedSchedule` survived; `NRestarts=0` | YAM:2612-2647, 2674-2680 |

Which process/user owned the live server at each stage: pcalnon GNOME-scope server (to 08-25 02:30) → none for the profile world thereafter → **root system service** (08-25 02:46 onward). The user-lane CLI runs (08-23/24) were pcalnon processes outside any server (H0824:44-47).

---

## 7. The `util/juniper-backup.bash` tar/USB lane

- **Role**: "archives **each Juniper application repo** as its own bzip2 + OpenPGP file, builds the ciphertext **once**, and copies that finished file onto every attached configured drive. It is the project-tree / external-media leg. It is **not** the Duplicati `$HOME` lane" (REF:635). Archives from one run share a UUID + timestamp; "restoring a coherent snapshot means taking every archive bearing the same UUID" (SCRIPT:15-17).
- **Devices**: `MEDIA_NAMES=( "EBC5-F0A3" "DFF3-2782" )`, mounted at `/media/pcalnon/<NAME>/`, `BACKUP_DIR="Juniper-8.0.0.python"` (SCRIPT:121-124, code); `EBC5-F0A3` = `/dev/sdf1`, `DFF3-2782` = `/dev/sdg1` (LIFE:535); ~135 GiB / ~67 GiB free (H0827:371). The mount check is on the mount root, not `BACKUP_DIR` (SCRIPT:83-85; REF:692); one missing drive degrades, zero is fatal (REF:693); `--dest DIR` bypasses the fan-out and is not mount-checked (REF:653).
- **Encryption recipient**: asymmetric to two YubiKey-backed UIDs ("…Yubikey-3c_2026-08-06" and "…Yubikey-3a_2026-08-11", SCRIPT:170-173, code); second recipient added in juniper-ml#1223 "so no single key loss can strand an archive written from now on" (H0821:244-248). `gpg --compress-algo=none -z 0` (REF:682). Unattended verify is `--list-packets` + recipient count only (REF:685).
- **Schedule/trigger**: **manual** — usage is a command line (REF:642-646; cheatsheet lines 35-36); exit 4 is "Visible to cron" (SCRIPT:55-56) but **no cron/timer unit exists in the repo** for it (`util/systemd/` holds none) — schedule: NO ARTIFACT.
- **Coverage**: ten repos `juniper-canopy … juniper-slacker` (SCRIPT:102); `juniper-legacy` not in the default list (REF:657); per-repo `EXCLUDE_DIRS` = `.amp .benchmarks .claude .mypy_cache .playwright-mcp .pytest_cache .ruff_cache .serena .trunk dist logs reports resources data build venv` (SCRIPT:111); `cascor-snapshots` archived by default — the flag's `TRUE` is `0` (SCRIPT:106-116; REF:691); `--exclude-backups`, `--exclude-caches-all`, `--ignore-failed-read` (SCRIPT:155-163). Measured footprint after the exclude fix: **2.8 GB for 10 repos** vs 113 GB unexcluded (LIFE:552-562).
- **Known defects (history)**: it "had **never produced an artifact**: it assigned `ENCRPYTED` but used `${ENCRYPTED}`, so `gpg -o ""`, and with no `set -u` it exited 0" — fixed in juniper-ml#1221 (H0821:235-241); the multi-device loop wrote both copies to the same path on the first drive while logging "OK" (SCRIPT:78-81); mount check on a subdirectory FATALed every run (SCRIPT:83-85); `--dry-run` once "fell through and wrote real archives while printing COMPLETE" (REF:651); the 2026-08-27 review of merged ml#1427: **B1** excludes inert three ways (literal quotes + trailing space; absolute vs relative member names; earlier string-splitting) — "~17,000× inflation, silently", `juniper-data` 97 GB → ">75 GB on the drive" (H0827:60-142; SCRIPT:70-73); **B2** `.tgz` name with bzip2 content — "Every archive this version writes is undecompressable by the documented recipe" (H0827:144-157); **B3** per-repo counters reset so COMPLETE printed over a failed repo (H0827:159-170); **B4** bzip2 3.8× slower for the same size (H0827:172-183); **B5** `INCLUDE_CASCOR_SNAPSHOTS` inverted (H0827:185-199); **B6** unanchored excludes would drop `src/**/data/` (H0827:201-207); **B8** legacy absent; `project_stats.bash` inert `du --exclude` (H0827:224-255). All B1–B6 recorded fixed on `origin/main` per REF:680-696 (relative anchored excludes, `.tbz2`, cross-repo totals, `EXCLUDE_CASCOR_SNAPSHOTS`) and LIFE:552 (juniper-ml#1439). bzip2 was **kept** (REF:661) despite B4's recommendation of gzip — a design choice the record leaves unexplained.
- **Drills**: class 1 (pipeline) — `util/ad-hoc/2026-08-26_backup_restore_drill.bash` round-trips a synthetic tree with throwaway keys and a byte-flip negative control; **PASSES**, "re-drilled 2026-08-28 against the corrected bzip2 pipeline" (LIFE:494-511); class 2 (key) — "**CLOSED 2026-08-28**. All 15 archives of the `snapshot-2026-02-27` backup set were decrypted with the documented recipe … byte-identical across both devices … this exercised the real hardware path" (LIFE:513-519; juniper-ml#1442 per H0830:181). The drill once tested `tar -czf` while the script did `-cjf` (H0827:295-306) — corrected by the 08-28 re-drill.
- **The plaintext archive**: a pre-existing **unencrypted** 111 GB `juniper-8.0.0_python_2026-02-27.tgz` on `EBC5-F0A3` — "both the exposure this script's asymmetric encryption exists to prevent and the capacity problem" (H0827:373-376); re-archived 08-28 as the labelled set `snapshot-2026-02-27` ("15 archives, 186 MB, on both devices, all verified by restore"); deletion of the plaintext remains "an owner decision" (LIFE:564-585). NO ARTIFACT of deletion.
- **Relationship to Duplicati**: LIFE:487-489 "It is **unrelated to the Duplicati path**"; H0830:179-182 and H0907:320-322 "a different mechanism this arc never covers". V3:218 notes the tar archive covers none of the worktree material (`.claude` excluded).

---

## Contradictions and residual uncertainty

The pairwise contradictions are in §4. Residual uncertainties the record leaves open:
1. **Archive-root README path** — documented at `/mnt/Backups/Ubuntu/README.md` (YAM:2549), found only at `/mnt/Backups/Ubuntu/Dropbox/Backups/README.md`. Either sda1's layout changed after 09-08, or the mount state differs from the record; the documents cannot say. (Only the live-system lane can settle it; I did not probe.)
2. **The old root-profile `yamaguchi` job** (:8200, never completed, H0821:76) is never explicitly dispositioned; the new `Yamaguchi` job id 2 was *imported* on the portable server (YAM:94, 158-160). Whether the old definition still exists in `/root/.config/Duplicati/` is unstated.
3. **Why the profile server DB held `enc-v1:` blobs while the portable root DB is cleartext** — unexplained; whether the `enc-v1` values (key material "beside `machineid.txt`", H0821:119) remain decryptable is unstated.
4. **The 2026-08-30 stuck pause** — "a single unexplained event, not a reproducible fault, and nothing in the record explains it" (YAM:2285-2287); third candidate ("first start after a `DAEMON_OPTS` change") untested (H0907:180-185).
5. **Recreate's dblock path** despite 2,682 dindexes present — "Unanswered, and it is the real defect" (RUN:331-332; H0824:246-248).
6. **`sda` drive health** — SMART never read (YAM:2773-2777).
7. **Whether the plan (PLAN) was ever amended** for the migration decision, the retention choice, or the cap removal — no artifact; the plan is stale relative to YAM.
8. **Deployed vs repo `duplicati_scheduled_backup.bash`** diverge by a 2026-08-29 DB-holder fix (H0907:193-197) — the deployed lane "ships a silently-failing corruption guard" but is disabled.
9. **Two certification bodies live only as prose** (§8.21.4 live crosscheck; §8.25.1 frozen-set ladder) because the records mirror froze on 08-30 (YAM:2574-2587).
10. **Job-count and filter-count drift** across snapshots (37 → 43/44 → 46 → 44) are consistent in sequence but each document quotes the number of its own moment.

## What the documents cannot tell us

- Anything after **2026-09-12** (V3's census: filesets through `20260911T140000Z`, 859 volumes, 202 GB, V3:27-29): whether daily runs still succeed, whether the watchdog still fires, whether `Linger` still reads yes, whether sda1 is mounted and healthy.
- Whether the owner has executed any of §5's pending items (smartctl, loop probe, sdc2 grow, plaintext `.tgz` deletion, user-lane removal PR, cloud-reporting decision, `ProgramState` check, worktree filters, records-mirror de-drift).
- The **actual** current content of `/etc/default/duplicati`, the live job's `TargetURL`/filters/schedule, `ProgramState`, or the server DB — the docs record snapshots (latest 09-08), not state; V3:74-77 warns even the snapshot DB is "at least one run stale".
- Whether the escrow copies (password manager, printed sheet, sda1 `_yamaguchi_keys/env`) still match the live `env` — last verified byte-identical 08-29 (YAM:1745-1748) and present 09-08 (YAM:2785-2787).
- Whether the offline "full Juniper archive" tier (PLAN:71) exists as anything other than the plaintext `.tgz` and the `snapshot-2026-02-27` set on the two USB drives; whether any copy is physically kept offline/air-gapped.
- Whether `juniper-deploy/util/sops-backup-key.sh` has ever been run (O-2), whether offsite is in scope (O-5), and whether the Docker volumes / conda envs / GitHub-side state were ever brought under any backup (H0821 §2.1, §3) — all NO ARTIFACT.
- Whether the tar lane has been run on any cadence since 2026-08-28 (no schedule artifact; the record shows only repair-time runs and the re-archive of the February snapshot).
- Which physical medium, if any, holds a copy of the ten old-archive dlists **off** `sda`+`sdc` (the `/home` second copy is on `sdc3`, DBX-README:42-47); a third location was recommended (YAM:2414-2417), NO ARTIFACT of one.
- What the `_yamaguchi_frozen_20260826.README.md` sibling says (outside my permitted read set) and whether the `Dropbox/Backups` location is a relocation, a reorganization, or a mount anomaly.

**Changed by this step**: nothing in the repository or on the host; scratch files only under `…/scratchpad/agent1-docs/` (`checkpoint-1.md`, `checkpoint-2.md`).

<!-- markdownlint-enable -->

---

## Report 1b — Reconstruct the AS-BUILT design from the session handoffs and the repository tooling

Subagent id `ac6eec7508a6dcbeb` (49,098 characters).

<!-- markdownlint-disable -->

# Juniper backup infrastructure — AS-BUILT reconstruction from handoffs + tooling (entry points A and B)

Reconstructed 2026-09-21 from the 13 handoff prompts and the repository tooling only. `notes/*DUPLICATI*` was deliberately not read. The only host state inspected was `ls -la ~/.config/systemd/user/` and `diff ~/.local/bin/duplicati-scheduled-backup.bash util/duplicati_scheduled_backup.bash`. Nothing was run, probed or written outside the scratch directory (a copy of this report is at `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/227cf645-dd93-4802-91f7-23dcaa92c971/scratchpad/agent2-asbuilt/AS-BUILT_REPORT.md`).

Repository root for every `file:line` below: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/atomic-sauteeing-truffle/`

## Citation legend

Handoffs (chronological; the two 08-25 files are ordered by content — the "widened-scope" file names "yamaguchi-certified" as its predecessor at its line 19, so the task's listing order is reversed for that pair):

| Code | File (`prompts/thread-handoff_automated-prompts/`) |
|---|---|
| H1 | HANDOFF_2026-08-21_backup-systematization-design-arc.md |
| H2 | HANDOFF_2026-08-22_duplicati-dbpath-and-recovery.md |
| H3 | HANDOFF_2026-08-23_duplicati-fresh-set-and-purge.md |
| H4 | HANDOFF_2026-08-24_duplicati-gpg-failure-and-scheduled-lane.md |
| H5 | HANDOFF_2026-08-25_duplicati-yamaguchi-certified-open-tail.md |
| H6 | HANDOFF_2026-08-25_duplicati-widened-scope-recertified-paul-gated-tail.md |
| H7 | HANDOFF_2026-08-26_duplicati-decisions-executed-root-gated-tail.md |
| H8 | HANDOFF_2026-08-26_duplicati-migrated-to-sda1-criterion-6-closed.md |
| H9 | HANDOFF_2026-08-27_backup-per-repo-review-and-arc-tail.md |
| H10 | HANDOFF_2026-08-28_duplicati-tempdir-moved-drill-de-drifted.md |
| H11 | HANDOFF_2026-08-29_duplicati-reboot-and-root-tail.md |
| H12 | HANDOFF_2026-08-30_duplicati-cleartext-passphrase-and-escrow-tail.md |
| H13 | HANDOFF_2026-09-07_duplicati-arc-outstanding-work.md |

`H5 §0:39-43` = section 0, lines 39-43 of that file. Repo short names: **RUN** = `util/duplicati_scheduled_backup.bash`, **FAIL** = `util/duplicati_backup_failure.bash`, **INST** = `util/install_duplicati_timer.bash`, **JB** = `util/juniper-backup.bash`, **WRAP** = `scripts/duplicati-wrapper.bash`, **WD** = `util/ad-hoc/yamaguchi_watchdog.py`, **SNAP** = `util/ad-hoc/yamaguchi_server_db_snapshot.py`; units by bare filename under `util/systemd/`.

DEPLOYED / REPO-ONLY / DISABLED / UNKNOWN are **handoff claims** unless marked "(observed)" — only the two permitted host reads count as observation.

---

## 1. As-built mechanism inventory

### Lane A — Yamaguchi server-run job (the production backup)

| Aspect | As-built | Citation |
|---|---|---|
| What runs | Duplicati 2.3.0.4 (dpkg) `duplicati-server` started by the **system** unit `duplicati.service`, `--portable-mode`, web service on 8300; job **Yamaguchi**, id 2 | H5 §0:39-41; H5 §4:219-222 |
| User | **root** (claim). The wrapper's commented "old unit" shows `User=duplicati`/`Group=duplicati` (WRAP:46-47), consistent with the owner's 08-21 wish to move off root (H1 §2.0:82) but contradicting every handoff through 09-07 → whether a `duplicati` user runs it now is **UNKNOWN** | H5 §0:39-40; H11 item 2:105-113 |
| systemd scope | system | H5 §6:258; H13 §1.6:177-178 |
| Trigger | Duplicati's **internal scheduler**: `Schedule.Time=…T14:00:00Z, Repeat=1D` = daily 09:00 CDT, confirmed by Paul; `startup-delay=30m` after any server start | H6 §1:75; H7 §0:17; H11 item 4:183-185; H12:130-132 |
| Reads | `/home/pcalnon/` plus the win10 VDI; win11 VDI removed 08-26 → "2 Sources, 44 filters, 10 settings" | H5 §0:55-60; H7 §0:18; H11 §0:20, item 2:110 |
| Notable filters | filter 43 excludes `~/.config/duplicati-backup/` (the key file); filter 36 `~/.cache/`; `~/.config/Duplicati/` excluded; `--skip-files-larger-than` **removed entirely** | H11 §0:26-27; H12 item 2:148-149; H4 loose ends:261-262; H5 §0:57-60 |
| Writes | `file:///mnt/Backups/Ubuntu/Yamaguchi` on **sda1** (moved 08-26 from `/media/pcalnon/temp_backups/Yamaguchi`, sdc4) | H8:9-11; H8 §0:19 |
| Tempdir | `/home/pcalnon/.cache/duplicati-tmp` (moved 08-28 from sdc4 `_duplicati_tmp`) | H10 §0:17 |
| Engine settings | AES built-in; retention `1W:1D,1M:1W,1Y:1M,3Y:2M` **with** `--no-auto-compact=true` (load-bearing pairing); `--blocksize=1MB` (irreversible), `--dblock-size=500MB`, `--asynchronous-upload-limit=1`, `--allow-missing-source=true` | H5 §0:44-54; H4 §4 item 5:228-233; `util/ad-hoc/yamaguchi_build_job.py:17-26`; `util/ad-hoc/yamaguchi_switch_aes.py:10-16` |
| Local DB / brain | `/usr/lib/duplicati/data/BMXWPAOGLP.sqlite` (per-job index) and `/usr/lib/duplicati/data/Duplicati-server.sqlite` (definition, schedule, filters, passphrase) — root-only `drwx------` | H6 §1:77; H11 item 2:105-113 |
| Secret it needs | `PASSPHRASE` (AES). Stored **in cleartext** in the server DB `Option` table (BackupID=2); the server logs "No database encryption key was found" on every start. Operator copy: `~/.config/duplicati-backup/env` (0600) with `PASSPHRASE` + `PASSPHRASE_OLD`, both 32 chars, select by NAME | H12 §0:15-30; H4 §2:128-130; H5 §4:224 |
| Web-UI credential | `DUPLICATI_WEB_CREDENTIAL` in the **primary checkout's** untracked `.env`, read by absolute path | `util/ad-hoc/yamaguchi_server_api.py:41-42`; H5 §4:223 |
| Bind | loopback since 08-30: `DAEMON_OPTS="--webservice-port=8300 --portable-mode"` (the `--webservice-interface=any` flag deleted; the DB already stored `server-listen-interface=loopback`). `/etc/default/duplicati` still carries a **commented** line lacking `--portable-mode` — the restart trap | H12:111,115-119; H11 item 3:124-145; `util/ad-hoc/yamaguchi_narrow_bind.bash:19-43` |
| Outbound | `remote-control-enabled=True`; `additional-report-url` → Duplicati cloud with a long-lived bearer JWT (exp "2028") — owner-deferred | H11 item 3:141-145; H12 item 6:168-170; H13 §1.8:223-225 |
| Status | **DEPLOYED** (claim): `LastRun=2026-09-07T14:00:00Z`, census 848 files → AGREE. Certified twice on the full ladder incl. post-migration drill 17/17. **Criterion 5 (reboot/logout survival) NEVER exercised** — one boot ID since 2026-08-16 | H13 §0:25; H6 §1:73; H8 §0:19; H13 §1.1:49-72 |

### Lane B — the disabled `systemd --user` CLI lane ("Ubuntu-fresh")

| Aspect | As-built | Citation |
|---|---|---|
| What runs | RUN → `duplicati-cli backup "${DEST_URL}" "${SOURCE_PATH}"` with `--encryption-module=gpg`, `--gpg-encryption-switches=--compress-algo none`, `--asynchronous-upload-limit=1`, `--compression-module=zip`, `--blocksize=1MB`, `--dblock-size=500MB`, `--skip-files-larger-than=2GB`, `--no-auto-compact=true`, `--allow-missing-source=true`, 44 hard-coded `--exclude=` lines | RUN:216-273 |
| Defaults | dest `file:///media/pcalnon/temp_backups/Ubuntu` (sdc4), mount `/media/pcalnon/temp_backups`, dbpath `~/.config/Duplicati/DQRVQNDIFX.sqlite`, source `/home/pcalnon`, tempdir `/media/pcalnon/temp_backups/_duplicati_tmp`, state `~/.local/state/duplicati/` (`backup.lock`, `backup-<ts>.log`, `last-run.status`) | RUN:47-63 |
| Units | `duplicati-backup.service` (oneshot, `EnvironmentFile=%h/.config/duplicati-backup/env`, `ExecStart=%h/.local/bin/duplicati-scheduled-backup.bash`, `TimeoutStartSec=infinity`, Nice 10 / best-effort 7, hardening, `OnFailure=duplicati-backup-failure.service`); `duplicati-backup.timer` (`OnCalendar=*-*-* 02:30:00`, `RandomizedDelaySec=30m`, `Persistent=true`); `duplicati-backup-failure.service` (`ExecStart=%h/.local/bin/duplicati-backup-failure.bash duplicati-backup.service`, no further OnFailure) | duplicati-backup.service:1-33; duplicati-backup.timer:5-20; duplicati-backup-failure.service:1-11 |
| Reporter | FAIL appends `failures.log` (status file + `journalctl --user` tail) **first**, then best-effort `notify-send`, always exit 0 | FAIL:26-62 |
| Installer | INST copies (never symlinks) runner + reporter to `~/.local/bin/` and three units to `~/.config/systemd/user/`; refuses unless cred file is 0600 with `PASSPHRASE=` and `Linger=yes`; **does not** enable the timer | INST:40-91 |
| User / scope | pcalnon / **user** | RUN:11-12; INST:11-17 |
| Trigger | timer 02:30 daily — **disabled** | duplicati-backup.timer:7; H4 §7:357; H6 §6:206 |
| Secret | `PASSPHRASE` via `EnvironmentFile`, gpg symmetric | duplicati-backup.service:12-14; RUN:85-87 |
| Status | **DEPLOYED-BUT-DISABLED** (claim). Units present (observed: `duplicati-backup.service`, `.timer`, `duplicati-backup-failure.service` in `~/.config/systemd/user/`, all Aug 24 16:16). Record 0-for-3; last run FAILED 2026-08-25. The deployed runner **lacks** the 2026-08-29 DB-holder fix (observed: the diff is exactly the `db_holder_pids` rewrite at RUN:157-180 vs a per-fd `readlink` loop). Fails safe only because its default dest/tempdir now point at deleted/unmounted directories — "do not repair its paths". Removal PR (§8.11.3) never opened. Shipped in ml#1292 | H5 §0:41-43; H13 §1.8:193-200; H11:218-223; H13 §0:27; git log `4e64878b` |

### Lane C — the watchdog (alerting candidate B)

| Aspect | As-built | Citation |
|---|---|---|
| What runs | `/usr/bin/python3 /home/pcalnon/Development/python/Juniper/juniper-ml/util/ad-hoc/yamaguchi_watchdog.py` (the **PRIMARY checkout** path) | yamaguchi-watchdog.service:13,16-17 |
| Checks | UNREACHABLE / JOB_MISSING / NO_RUNS / NOT_SUCCESS / STALE (>26 h) / STUCK (>6 h) / RUNNING=OK / EXCEPTION=UNDETERMINED; exit 0/1/2 | WD:24-37, 85-134, 161-162, 172 |
| Writes | `~/.local/state/duplicati/server-watchdog.log`, `server-watchdog.status`, `server-failures.log` on non-OK; best-effort `notify-send` | WD:137-154, 163 |
| Reads | server REST API at `http://127.0.0.1:8300` through `yamaguchi_server_api.py` | WD:58-59, 87-119; `yamaguchi_server_api.py:40` |
| Secret | web-UI credential only; passphrase never | yamaguchi-watchdog.service:11-12 |
| User / scope / trigger | pcalnon / **user** / `OnCalendar=*-*-* 12:00:00` local, `Persistent=true` | yamaguchi-watchdog.timer:10-14 |
| Deploy path | `util/ad-hoc/yamaguchi_watchdog_deploy.bash`: asserts Linger=yes, installs both units from PRIMARY, `daemon-reload`, `enable --now`, runs one check | yamaguchi_watchdog_deploy.bash:20-46 |
| Status | **DEPLOYED** (claim): 12:30:59 CDT 08-26; first unattended fire 08-27 12:00:04 OK; "This script is DEPLOYED" 09-07. Consistent with observation: both units dated Aug 26 12:30 and `timers.target.wants/` mtime Aug 26 12:30 (symlink contents **not** inspected). Gaps: never inspects `ProgramState`/`SchedulerQueueIds`; a Compact refreshes the freshness clock; status file has no freshness component; `notify-send` has no session bus under linger | H7 §0:16; H10 §0:20; H13 §1.6:163-178; H11 item 4:176-181 |

### Lane D — server-DB snapshot timer (root, system scope)

| Aspect | As-built | Citation |
|---|---|---|
| What runs | `/usr/bin/python3 <PRIMARY>/util/ad-hoc/yamaguchi_server_db_snapshot.py`: `sqlite3.backup()` of `/usr/lib/duplicati/data/Duplicati-server.sqlite` → `/home/pcalnon/.local/state/duplicati-server-db/Duplicati-server.sqlite`, `PRAGMA integrity_check`, 0600 in a 0700 dir chowned to pcalnon; refuses unless root | yamaguchi-server-db-snapshot.service:13-24; SNAP:52-54, 76-89, 105-145 |
| Why that path | inside Source `/home/pcalnon/`, matched by none of the 44 filters | SNAP:28-33; service:4-7 |
| User / scope / trigger | root / **system** (`/etc/systemd/system`) / `OnCalendar=*-*-* 13:45:00 UTC` (15 min before the 14:00Z backup; UTC suffix load-bearing for DST), `Persistent=true` | `util/ad-hoc/yamaguchi_server_db_deploy.bash:24-46`; yamaguchi-server-db-snapshot.timer:6-19; H12:195-197 |
| Secret | none to run; the copy **contains the cleartext passphrase** (SNAP:20 and :36 still say "encrypted" — uncorrected) | H12 §0; H13 §1.8:209-211 |
| Status | **DEPLOYED** (claim, 08-30): timer enabled, first snapshot 160 KB, integrity ok. "Capture in a completed backup not yet confirmed" at H12; H13 never closes it → **UNKNOWN**. Not observable by me (system scope) | H12:121-126, 161-163; H13 §1.6:177-178 |

### Lane E — the tar / USB lane (`util/juniper-backup.bash`)

| Aspect | As-built | Citation |
|---|---|---|
| What runs | JB: per-repo `tar -cjf - … -C <parent> <repo> \| gpg --batch --yes -r K1 -r K2 --compress-algo=none -z 0 -e -o <dest>/<name>.tbz2.gpg`; build on first usable device, `cp` ciphertext to the rest, verify each | JB:12-31, 523-565 |
| User / scope / trigger | pcalnon (`USER_NAME="pcalnon"`, own gpg keyring) / **none** / **manual only** — no timer, `.path`, udev rule or crontab in the repo, none in `~/.config/systemd/user/` (observed). The header's "visible to cron" is aspirational: **NO ARTIFACT** | JB:123, 56, 574; repo `find` (5 systemd files, none for JB) |
| Reads | `${HOME}/Development/python/Juniper/<repo>` for 10 repos; excludes 16 top-level names per repo; `cascor-snapshots` **included** by default | JB:99-102, 111, 109 |
| Writes | `/media/pcalnon/{EBC5-F0A3,DFF3-2782}/Juniper-8.0.0.python/Juniper[_<label>]_<repo>_<uuid>_<stamp>.tbz2.gpg` | JB:121-124, 303-305, 315-322, 434 |
| Secret | **none to run** — asymmetric to two YubiKey-backed public keys; YubiKey needed only to restore | JB:27-31, 170-173 |
| Status | in repo; **has been run** — owner reported symptoms from real runs under #1427; class-2 YubiKey drill CLOSED (ml#1442); both drives mounted 08-26 with 135 G / 67 G free | H9 §0:3-8; H12:179-182; H13 §5; H9 §6:357-359 |

### Lane F — other elements

| # | Element | Status | Citation |
|---|---|---|---|
| F1 | **Key escrow** (manual): `yamaguchi_key_escrow.py` copies `~/.config/duplicati-backup/env` → `/mnt/Backups/Ubuntu/_yamaguchi_keys/env`, refusing a destination on the same physical disk (`/sys/class/block` parent + `st_dev`); writes a printable sheet `~/.cache/yamaguchi-key-escrow-sheet.txt` (filter 36 keeps it out of the archive) | sda1 copy DONE; **print owed**; password-manager copy accepted interim | `yamaguchi_key_escrow.py:48-51, 148-173, 217-231`; H12:109, 224-226; H13 §0:30, §1.3 |
| F2 | **Frozen pre-migration set** (811 files), now `/mnt/Backups/Ubuntu/_yamaguchi_frozen_20260826/` + README; sdc4 **unmounted, not destroyed** | data (claim) | H8 §1:28-32; H10 §0:18; H13 §0:27-28 |
| F3 | **Old-archive dlists**: ten `.dlist.zip.gpg` at `/mnt/Backups/Ubuntu/` + `README.md`; second copy `~/.local/state/yamaguchi-old-archive-dlists/`; need `PASSPHRASE_OLD`; cannot restore | data (claim) | H11:77-79, 197-198; H13 §0:29, §2:238-243 |
| F4 | **Records mirror** `/mnt/Backups/Ubuntu/_yamaguchi_records/` via `yamaguchi_records_sync.bash` (`SRC_ROOT=/media/pcalnon/temp_backups`, mountpoint-guarded) | tool **DEAD** since the sdc4 unmount; frozen at 2026-08-30 | `yamaguchi_records_sync.bash:20-32`; H13 §1.5 |
| F5 | **Alerting candidate A**: `yamaguchi_run_script_after.bash`, root inside duplicati-server via `--run-script-after`, writes `/var/local/duplicati-yamaguchi/` | REPO-ONLY, never deployed or revoked | `yamaguchi_run_script_after.bash:9, 14-23, 37`; H13 §1.8:231-232 |
| F6 | **Orphaned pcalnon-profile world**: `~/.config/Duplicati/Duplicati-server.sqlite` (schema 19) with jobs `Ubuntu` (id 2) / `Ubuntu-fresh` (id 3); the GNOME-tray `/usr/bin/duplicati` instance on 8300; Recreate "dead"; `dbconfig.json` deleted | DISABLED / orphaned | H1 §2.0:73-76; H5 §1:79-81; H8 §0:21; H13 §1.8:226-228 |
| F7 | Root **8200** `duplicati-server` **repurposed to 8300**, not removed | informational | H12 item 8:173-177; H13 §1.8:226-227 |
| F8 | Outside this repo: `juniper-deploy/util/sops-backup-key.sh` (age-key escrow; "ever run?" never answered); `juniper-legacy/JuniperLegacy/util/backup_conda_dotfiles.bash` | UNKNOWN | H1 §2.5:142-147, O-2:243 |
| F9 | **`scripts/duplicati-wrapper.bash`** (2026-09-20, PRs 1967/1968) — §5 | REPO-ONLY; deployment UNKNOWN (post-dates every handoff) | git log `6708cb28`, `52571621` |
| F10 | Duplicati-native `Schedule` table in the profile DB was **EMPTY** — before the pivot nothing scheduled either profile job | historical | H4 §6:336-338; RUN:17-18 |

---

## 2. Chronology

| Date | Change | Reacting to | Citation |
|---|---|---|---|
| ≤07-09 | Last success of the pcalnon-profile `Ubuntu` job (gpg, `/mnt/Backups/Ubuntu` sda1, 50 MB skip, 37 filters) | — | H1 banner:13-14; §2.2:101-112 |
| 07-12/13 | Destination filled (4 KiB free); a dblock wedged; an **interrupted compact** deleted 1,208 dblock/dindex pairs → five 2026-07 restore points destroyed | quota exhaustion | H1 banner:13-16; H3 §1:60-67 |
| 08-21 (H1) | Two instances identified: **8300** `/usr/bin/duplicati` as pcalnon (real job) and **8200** `duplicati-server` as root (`yamaguchi`, never completed). Owner: off root to a dedicated user; O-7 asks whether to **remove** 8200. JB had never produced an artifact (`ENCRPYTED` typo) → #1221 (streamed `tar\|gpg`, mount guard, free-space, `--dry-run`) and #1223 (second recipient); single drive `DFF3-2782` | 42-day silent outage found while verifying C-1 | H1 §2.0:71-84; O-0:235-241; O-7:256-258; git `42ecac3d`, `486d6f6e` |
| 08-22 (H2) | `Backup.DBPath` corrupted (pointing at the server DB); schedule to be disabled; standing prohibitions (never Repair, never `kill -9`, `/mnt/Backups` is not a mountpoint); Jul-12 DB-restore runbook **withdrawn**; ~1.2 TB deleted 07-13 | Recreate ~49 days | H2 §1-§5 |
| 08-23 (H3) | **`Ubuntu-fresh`** (id 3) started by CLI to `/media/pcalnon/temp_backups/Ubuntu` (**sdc4**, same disk as `/home`), dbpath `DQRVQNDIFX.sqlite`; passphrase file-vs-process divergence; `.env` holds `PASSPHRASE` + `PASSPHRASE_OLD`; plan: linger + user unit, alerting, migrate to sda1, remove root 8200 | archive damage proven; Schedule empty; `Linger=no` as outage mechanism | H3 §0; §1a:72-86; §3:144-155 |
| 08-24 (H4) | Fresh backup failed twice (hang; `GPGFlushError` rc=100). **User lane shipped** (ml#1292): RUN 6 guards, FAIL, INST, units; `Linger=yes`; creds → `~/.config/duplicati-backup/env`; `--tempdir` off tmpfs to sdc4; three CRITICAL guard defects fixed; **timer held disabled**. Direction: investigate GPG, no AES yet | tmpfs staging; gpg flush failure | H4 §1:40-110; §2:113-152; git `4e64878b`, `22949055` |
| 08-25 (H5) | **PIVOT** to the **system `duplicati-server`** (root, 8300, `--portable-mode`, data `/usr/lib/duplicati/data/`); "remove 8200" **superseded**; user lane superseded (0-for-3). **gpg → AES**. Retention + `--no-auto-compact`. Paul widened scope 14:14 (two VDIs, size cap removed). Restart trap closed; autoupdater shadow neutralised; `dbconfig.json` mis-mapping | GPG class unfixable; session-bound tray instance | H5 §0:37-64; §1:66-82 |
| 08-25/26 (H6) | Widened scope re-certified (coverage 1,241,950/…; HMAC 780/780; drill 17/17). Alerting **B** recommended over **A**; neither deployed. Schedule 14:00Z. Server-brain recipe. Migration options a/b/c. Retirement list incl. user lane | plan §7 criteria | H6 §0-§2 |
| 08-26 (H7) | **B DEPLOYED** 12:30:59 CDT; win11 VDI **excluded**; 09:00 CDT confirmed; release-train key kept; first scheduled run Success 25 m | Paul's decisions | H7 §0:11-25 |
| 08-26 (H8) | **Destination → `/mnt/Backups/Ubuntu/Yamaguchi` (sda1)**, criterion 6 CLOSED (copy → 811/811 decrypt-validate → PUT → proof run → AGREE → drill 17/17); `dbconfig.json` deleted; Tier 1+2 retirements (128 GB); sdc4 copy kept; two tools found hard-coding the old path | physically separate drive; sdc4 not in fstab | H8:9-11; §0-§2 |
| 08-27 (H9) | JB **per-repo rewrite** merged (#1427; drives `EBC5-F0A3` + `DFF3-2782`); review finds B1 (excludes inert), B2 (`.tgz`/bzip2), B3 (counters reset), B4 (bzip2 slower), B5 (flag inverted), B6 (unanchored); drill drifted; unencrypted 111 GB `.tgz` on `EBC5-F0A3` | owner-reported slowness / >75 GB archives | H9 §0, §2, §4, §7 |
| 08-28 | B1-B4 fixed, `--dry-run` made inert (#1439); `--repos`/`--label` (#1440); dry-run fall-through caught by `2026-08-28_backup_exclude_e2e.bash` | H9 | git `72cb4db6`, `870ccb37`; JB:490-495 |
| 08-28 (H10) | **`--tempdir` → `~/.cache/duplicati-tmp`**; watchdog's first unattended fire; two scheduled runs Success from sda1; three stale-path tools fixed; purge = gating decision | non-durable sdc4 | H10 §0-§1 |
| 08-29 (H11) | **Purge executed** (5,356 volumes / 2.3 TiB; 10 dlists kept); Tier 3 retired; key file **excluded from the backup and on disk `sdc`** with the sources; two DBs with opposite loss profiles; loopback plan = delete the `any` flag; cloud reporting noticed; criterion 5 deferred; user lane "fails safe — do not repair" | consolidation onto sda1; restorability audit | H11 §0; :69-81; :102-193 |
| 08-29 | RUN guard 5 rewritten: resolve `DBPATH` (symlinked parent had let a live holder pass) and one `find` instead of per-fd `readlink` (59 s → 0.4 s) | verification on host | RUN:157-181; git `ed82c1f6`, `00c90942` |
| 08-30 (H12) | Passphrase **cleartext** in the server DB (owner accepts; `SETTINGS_ENCRYPTION_KEY` rejected); two harnesses hard-code the sdc4 mount; **loopback DONE**; **server-DB snapshot timer DEPLOYED**; escrow HALF; `Paused` = `startup-delay`; class-2 tar drill confirmed closed | validation of the note's premises | H12 §0-§1; :105-177 |
| 09-02 (in H13) | dlist second copy relocated; README corrected; sdc4 **unmounted**; frozen set moved to sda1 | clearing sdc4 | H13 §0:27-29; §1.8:201-204 |
| 09-07 (H13) | 848 files AGREE; criterion 5 still never exercised; sda SMART never read; `records_sync` dead; watchdog lacks `ProgramState`; 08-30 stuck-pause unknown; deployed-vs-repo runner divergence; removal PR unopened | closeout audit | H13 §0-§1 |
| 09-20 | `scripts/duplicati-wrapper.bash` added (#1967) and revised (#1968): wrapper for a `duplicati.service` `ExecStart`, a `/home/duplicati/` home, `SETTINGS_ENCRYPTION_KEY`, default port 8300 | not covered by any handoff | git log; WRAP:17-57 |

Trajectories: **ports** 8300 (tray) + 8200 (root) → 8200 unit repurposed to 8300 → bound `any` → loopback (H1 §2.0:73-76; H12:174-175, 115-119). **User** pcalnon profile → root system server (dedicated user wanted, not done by 09-07) → wrapper hints `User=duplicati` (UNKNOWN). **Destination** `/mnt/Backups/Ubuntu` → `/media/pcalnon/temp_backups/Ubuntu` → `…/Yamaguchi` (sdc4) → `/mnt/Backups/Ubuntu/Yamaguchi` (sda1). **Data folder** `~/.config/Duplicati/` and `/root/.config/Duplicati/` → `/usr/lib/duplicati/data/`. **Encryption** gpg → AES; old sets stay gpg; both passphrases retained. **Size cap** 50 MB → 2 GB (RUN:226) → 8 GB (`yamaguchi_build_job.py:26`) → removed. **Tempdir** `/tmp` → sdc4 → `~/.cache`. **sdc4** temporary → "KEEP" → unmounted 09-02.

---

## 3. Guards catalogue

### 3a. `util/duplicati_scheduled_backup.bash`

| Guard | Lines | Failure it encodes | Exercised per the handoffs? |
|---|---|---|---|
| 1. `PASSPHRASE` non-empty, ≥ 12 chars | RUN:85-87 | a timer job hanging on a prompt, or a set encrypted under a truncated credential; cannot detect a *wrong* value | Floor dropped then **restored** by validation (H4 §2:139-140); never recorded firing live; pinned `tests/test_duplicati_scheduled_backup.py:313-334` |
| 2. `DEST_MOUNT` mountpoint; `DEST_PATH` exists, writable | RUN:90-94 | an unmounted path is an empty dir on `/` read as "everything is missing" | Never recorded firing; H11:218-223 says it is what makes the disabled lane fail safe now. Tests :335-368 |
| 3. dest empty **or** holds `duplicati-*` | RUN:97-100 | mount onto the wrong filesystem | Never recorded firing; proves only that *some* volumes exist (H4 §2a:149-150). Tests :369 |
| 3b. tempdir not tmpfs/ramfs | RUN:106-111 | 500 MB volumes staged in RAM (08-23: 8.4 GB resident, swap 17/20 GB) | Defect observed (H4 §2:132-134); guard firing not recorded. Tests :380 |
| `skip_or_fail` + `STALE_DAYS=3` | RUN:123-138 | a skip that reports success and freezes `last-run.status` | Found CRITICAL and fixed pre-merge (H4 §2:135-140); H5 §3:189-190 records the *misread* of a run-END status file that triggered the pivot. Tests :403-451 |
| 4. non-blocking `flock`, never `pgrep -f` | RUN:141-144 | two runs on one DB; `pgrep -f` self-matches | Not recorded firing; the self-match trap is recorded (H3 §2:100-103; H4 §3:166-167). Tests :254-267 |
| 5. no live process holds `DBPATH` | RUN:172-186 | hand-started `duplicati-cli`, absolute-path invocation, in-process server runs — invisible to name checks | **Found failing twice**: name-anchored version (H4 §2:135-138); verbatim-path version missed a symlinked parent — "a live holder went undetected and the corruption guard passed" (RUN:166-171; H13 §1.8:193-197). **Deployed copy still has the second defect** (observed diff). Pinned `tests/test_duplicati_db_holder_guard.py:113-190` |
| RC propagation / status stamping | RUN:216-285 | a failed run leaving no record | **Exercised on a real failure**: run 2 rc=100 at 23:48:24 stamped `FAILED` and fired OnFailure (H4 §1:44-48; §2:127; §7:361) |
| Unit-level: `EnvironmentFile`, `TimeoutStartSec=infinity`, `Persistent=true`, `OnFailure`, reporter not chained | service:14,21,6; timer:15; failure.service:9-11 | passphrase on argv; start timeout killing a healthy run; missed windows; silent failure | OnFailure proven on the real failure (H4 §2:127); `Persistent`/`Linger` **never tested across a boot** (H4 item 6:238-239). Tests :268-283 |
| Installer: cred 0600 + `PASSPHRASE=`; `Linger=yes`; copies; no enable | INST:60-81, 45-58, 26-32 | lane that cannot start; worktree removal breaking it; second run mid-first-backup | Linger enabled/verified (H4:8,126); installed 08-24 16:16 (observed mtimes). Tests :296-312 |

### 3b. `util/juniper-backup.bash`

| Guard | Lines | Failure it encodes | Exercised? |
|---|---|---|---|
| `set -euo pipefail` | JB:91 | the `ENCRPYTED`/`${ENCRYPTED}` typo that ran `gpg -o ""` and exited 0 | founding defect (H1 O-0:235-241; JB:75-76) |
| `--label` / repo names match `[A-Za-z0-9._-]+`, not `.`/`..`; empty `--repos` exit 2 | JB:203-210 | `--repos ../../etc`; `/` or space in filenames | added in #1440; no firing recorded |
| source exists; zero repos FATAL, missing repo WARNING | JB:376, 220-228, 380-382 | archiving nothing while reporting success | none recorded |
| every recipient resolves before tar; `:pubkey enc packet:` count == `${#ENCRYPT_KEYS[@]}` | JB:386-391, 358-364 | a missing key silently halving redundancy | added #1223 (H1 O-0:239); none recorded |
| device usable = `mountpoint -q` on mount root, then `-d`/`-w` on backup dir; missing = SKIP; zero = FATAL | JB:327-346, 421-424 | unmounted path filling `/`; the earlier form tested `BACKUP_DIR` and "FATALed on every run even with both drives attached" | wrong-form guard exercised as a **false positive every run** (JB:83-85; #1422 `b884ac7b`) |
| `--dest` writable, not mount-checked | JB:398-406 | — | none recorded |
| free-space warn `< SOURCE/2`, warn `< SOURCE` (warn only) | JB:448-454 | incompressible `.h5`/`.npz` tree | capacity was live: 111 GB plaintext tgz, 135 G / 67 G free (H9 §7:371-376) |
| `verify_archive` on build **and** each copy | JB:351-367, 532, 553 | empty / non-OpenPGP artifact; copy that did not land | structural only (JB:350); pipeline proven by the 08-26 drill; YubiKey half by ml#1442 (H12:181-182) |
| `cleanup_partial` removes only `IN_PROGRESS` | JB:290-299 | partial write left looking like a backup; deleting a good copy after a later failure | none recorded |
| `--dry-run` exits 0 before the build loop | JB:490-495 | the preview wrote ~100 GB of real archives while printing COMPLETE | **caught by** `util/ad-hoc/2026-08-28_backup_exclude_e2e.bash` (JB:492-493) |
| relative, anchored excludes; one list for `du` and `tar` | JB:254-265, 270-273 | three shellcheck-clean revisions whose excludes matched nothing (`du` ~205 MB vs `tar` ~103 GB) | B1 live on `main` (H9 §2.1); repro `2026-08-28_exclude_arg_repro.bash` (JB:73, 246) |
| cross-repo totals → PARTIAL exit 4 | JB:510-513, 586-590 | per-repo counters printed COMPLETE over a missing archive (B3) | H9 §2.3; fixed #1439 |
| `TAR_COMPRESS_FLAG`/`TAR_EXT` paired; preview rendered from them | JB:144-149, 478-479 | `.tgz` name over bzip2 content (B2) | H9 §2.2; fixed #1439 |

---

## 4. `util/juniper-backup.bash` in depth

**Device identification.** `MEDIA_NAMES=( "EBC5-F0A3" "DFF3-2782" )` (JB:121). No `blkid`/`UUID=`/label lookup: each is expected to be mounted at `/${MOUNT_NAME}/${USER_NAME}/<NAME>` = `/media/pcalnon/<NAME>` (JB:122-124, 303-305, 329) and to already contain `Juniper-8.0.0.python` (JB:124, 337-339 — no `mkdir`). The `XXXX-XXXX` shape is the form udisks gives an unlabelled FAT-family automount (inference from shape, not probed). A drive mounted anywhere else (e.g. fstab under `/mnt`) is `SKIP … not a mount point` (JB:332-336). H9 §6:357-359 confirms both mounted under `/media` on 08-26; the single-drive era is H1 §2:68.

**Mount detection.** `mountpoint -q` on the mount root, then `-d`/`-w` on the backup dir (JB:332-344). One missing drive degrades; zero usable is fatal (JB:420-424). `--dest DIR` bypasses the fan-out and is deliberately **not** mount-checked (JB:394-406).

**Encryption.** `gpg --batch --yes -r <K1> -r <K2> --compress-algo=none -z 0 -e -o <path>` (JB:531) to two YubiKey-backed UIDs (`…Yubikey-3c_2026-08-06`, `…Yubikey-3a_2026-08-11`, JB:170-173). No key or passphrase to write; any one key restores; recipients cannot be retro-fitted (JB:27-31, 167-169). Compression is tar-side bzip2 (JB:148-149).

**Coverage.** Ten repos (JB:102). Per-repo top-level excludes: `.amp .benchmarks .claude .mypy_cache .playwright-mcp .pytest_cache .ruff_cache .serena .trunk dist logs reports resources data build venv` (JB:111, anchored per JB:248-249). `cascor-snapshots` archived by default (JB:106-116; the script's TRUE is `0`). **Not covered:** `juniper-legacy` unless via `--repos` (JB:39-49; H1 §3:183); the **parent-level** `Juniper/{backups,notes,prompts,resources,util,worktrees}` that the pre-rewrite whole-tree design captured (H1 §3:193-194) — the loop only touches `${PROJECT_DIR}/${REPO}` (JB:222, 432); inside every repo `.claude/` (so `.claude/worktrees/`), `data/` (juniper-data's ~96 GB, by design — H9 §2.1:107-110), `resources/`, `logs/`, `reports/`; anything outside `~/Development/python/Juniper` (H1 §3 items 2-10).

**Dry-run semantics.** Runs every preflight (repos, recipients, devices, size/free-space), prints per repo the exact `tar args:`, the `would build once: tar -cjf - … | gpg …` line, the restore recipe, the size, and `build ->`/`copy ->` targets, then `no archives were written.` and `exit 0` (JB:464-496); rendered from the same variables as the build (JB:475-479).

**Verification.** Unattended: `gpg --list-packets --list-only` + recipient count on build and copies, then `sync` (JB:351-367, 532-533, 553-560). Drills: pipeline byte-for-byte `util/ad-hoc/2026-08-26_backup_restore_drill.bash` (JB:350; `docs/REFERENCE.md:686` "PASSES"); `2026-08-28_backup_exclude_e2e.bash` (:10-21); `2026-08-28_exclude_arg_repro.bash`; `2026-08-28_backup_footprint.bash`; class-2 YubiKey decrypt closed in ml#1442 (H12:179-182; H13 §5; `docs/REFERENCE.md:687`). **No unit test covers JB** — `tests/` holds only the four `test_duplicati_*` suites and neither JB nor its drills appear in `.github/workflows/` → the test H9 §3:282-286 asked for is **NO ARTIFACT**.

**Trigger today.** Manual only (see Lane E). "Visible to cron" (JB:56, 574) is an exit-code contract, not a deployment.

**Documented defects.** #1221 typo/streamed pipeline (JB:63-65, 75-76; H1 O-0); #1223 second recipient + count; #1422 stale `GPG_PATH` across the loop and mount check on `BACKUP_DIR` (JB:78-85); #1427 shipping B1-B6 (H9 §2); #1439 B1/B2/B3/B4 + inert `--dry-run` (JB:70-73, 144-149, 233-252, 490-495, 506-509); #1440 `--repos`/`--label` (JB:34-49); B5 → `EXCLUDE_CASCOR_SNAPSHOTS` (JB:106-109); B6 closed by anchoring. Open per H9 §7: capacity and the unencrypted 111 GB `juniper-8.0.0_python_2026-02-27.tgz` on `EBC5-F0A3` — `util/ad-hoc/2026-08-28_extract_feb_archive.bash:10-15, 28` exists to re-archive it encrypted; whether it ran is **NO ARTIFACT**.

### 4a. Analysis: running JB on a schedule, only when specific USB drives are mounted

Reused unchanged: `MEDIA_NAMES` (JB:121); `validate_external_media` skip/fatal (JB:327-346, 420-424); `--repos` (JB:190), `--label` (JB:188), `--dry-run` (JB:185); the exit-code contract (JB:51-57).

Would have to change:
1. **A trigger** — the pattern already deployed twice: a `systemd --user` `.timer` (`OnCalendar`, `Persistent=true`, `RandomizedDelaySec`) + oneshot `.service` (cf. `duplicati-backup.timer:5-17`, `yamaguchi-watchdog.timer:5-14`). A mount-triggered unit (`WantedBy=media-pcalnon-<escaped>.mount` or a `.path` on the backup dir) fires on plug-in, but `/media/<user>/` automounts come from the desktop's udisks session; under `Linger=yes` with no graphical session there is no automount — the same "no session bus" caveat FAIL:19-23 and H11 item 4:179-181 record. So "schedule + only when mounted" reduces to: timer fires, service checks mounts, absent drives are a benign skip.
2. **Distinguish "no drive" from a real fatal** — both are `exit 1` today (JB:422-423 vs 376/388/404). A distinct exit code or an `ExecCondition=`/`mountpoint -q` pre-check is needed so `OnFailure=` does not fire nightly while unplugged, and the skip cannot become the permanent state (RUN:123-138's `skip_or_fail`/`STALE_DAYS` is the existing answer to that class).
3. **Concurrency** — JB has no `flock` (RUN:141-144 is the pattern).
4. **Retention** — every run mints a new UUID set (JB:135-136); nothing prunes; free-space only warns (JB:448-454); 135 G / 67 G drives fill (H9 §7:371).
5. **Status/alerting** — no status file or reporter; reuse RUN:69-78 / FAIL:28-57.
6. **Keyring** — recipients resolve in the invoking user's keyring (JB:386-391); public keys suffice (JB:27-28); the unit must run as pcalnon.
7. **`ExecStart` path** — the deployed timers point at the PRIMARY checkout with the documented "merged is not live until pulled" consequence (yamaguchi-watchdog.service:16-17; H13 §1.6:171-176); INST's copy-not-symlink (INST:19-24) is the alternative.

### 4b. Analysis: additionally writing an archive to an external hard drive

Existing knobs: `MEDIA_NAMES` fan-out, first usable = build device (JB:120-121, 410-416, 523); `--dest` **replaces** the fan-out (JB:38, 394-406); `BACKUP_DIR` (JB:124); `target_dir_for` (JB:303-305).

Would have to change:
1. `target_dir_for` hard-codes `/media/pcalnon/<NAME>/Juniper-8.0.0.python` (JB:304); an fstab HDD under `/mnt` cannot be a `MEDIA_NAMES` entry, and `--dest` cannot coexist with the fan-out (JB:398-417 is either/or). Either entries accept absolute mount roots, or a parallel destination list is added, each under the same `mountpoint -q` + `-d`/`-w` checks (JB:327-346).
2. Build order: first usable device is where `tar|gpg` writes, the rest get `cp` (JB:523-565) — an internal HDD listed first becomes the build target.
3. Placement on sda1: never copy INTO `/mnt/Backups/Ubuntu/Yamaguchi/`; siblings only; nothing under `/mnt/Backups/Ubuntu/` may be deleted or moved (H13 §2:238-245). `BACKUP_DIR` must resolve to a pre-existing sibling (JB:337-339).
4. `--repos`/`--label` unchanged (JB:186-190).
5. Retention as 4a-4; HDD free space judged by the same warn-only check (JB:442-454).
6. Whether the USB-2.0 "My Passport" (H5 §2 item 9:157-160) is `EBC5-F0A3` or `DFF3-2782` is **UNKNOWN**.

---

## 5. `scripts/duplicati-wrapper.bash`

**PR-body claims.** PR 1967 (merged 2026-09-20T22:26:28Z): "Introduced a new wrapper script for managing the Duplicati server, designed to be called by a systemd unit file. The script sets up necessary environment variables, parses input parameters, and handles configuration from global and local environment files … streamline the deployment and management" — the remainder is the untouched PR template. PR 1968 (22:59:23Z): **only** the empty template. Both commits touch **only** `scripts/duplicati-wrapper.bash` (`git show --stat`: 1967 = 210 insertions; 1968 = 56+/67−, gating previously unconditional `echo`s behind `DEBUG_MODE`). No other repo file references it, no unit file ships with it, no CHANGELOG entry, no test. It post-dates H13 by 13 days.

**Header claims.** Layout: `/etc/default/duplicati`; `/usr/lib/systemd/system/duplicati.service`; local env `/home/duplicati/.config/Duplicati/.env`; wrapper at `/home/duplicati/bin/duplicati-wrapper.bash` (WRAP:17-24). Precedence: 1 input params `${*}` > 2 `DAEMON_OPTS` from `/etc/default/duplicati` > 3 local `.env` > 4 script constants (WRAP:26-30); example `DAEMON_OPTS="--webservice-port=8300"` (WRAP:32-33). Quoted "Old Unit file" (WRAP:38-57): `Nice=19`, **`User=duplicati`/`Group=duplicati`**, `EnvironmentFile=-/etc/default/duplicati`, an `Environment=SETTINGS_ENCRYPTION_KEY=…` line, `ExecStart=` the wrapper, a stray `/usr/bin/duplicati-server $DAEMON_OPTS` line (WRAP:51), `Restart=always`. This diverges from the handoff-era unit (`ExecStart=/usr/bin/duplicati-server $DAEMON_OPTS`, root — `yamaguchi_narrow_bind.bash:28-31`; H5 §0:39-40) and the header's `DAEMON_OPTS` example lacks `--portable-mode` (H12:115-117 has it).

**Does the code implement the claimed precedence? (read, not run)**
- *Layer order — yes, mechanically*: inputs (WRAP:154-163) → `DAEMON_OPTS` (165-174) → local options (176-185) → default port if absent (187-189); earlier layers win.
- *Layers are not tokenised*: `("${*}")` and `("${DAEMON_OPTS}")` are **one-element** arrays holding the whole string (WRAP:102, 105); the dedup key is the text before the first `=` of the blob (156-159), so only the first option of a multi-option layer participates and the blob is kept or dropped whole.
- *Dedup is substring*: `grep -- "${KEY}"` over the accumulated string (160, 171, 182, 187) — a prefix key (e.g. `--log-file` vs `--log-file-log-level`) suppresses a later layer's distinct option.
- *The exec collapses everything into one argv element*: `exec "${DUPLICATI_SERVER}" "${DUPLICATI_OPTS}"` (WRAP:199) passes the space-joined string, trailing space included, as a **single argument** — the same "space-joined string quoted into one argv element" shape JB's header records as rev-1 of its own exclude bug (JB:70-71, 236). Whether duplicati-server tolerates it is unverifiable without running (not done).
- *Layer 2 is never read by the script*: `DUPLICATI_ENV_GLOBAL` is defined (WRAP:76) but never sourced; `${DAEMON_OPTS}` is consumed from the inherited environment (104). Precedence 2 holds only under systemd's `EnvironmentFile=`; by hand it vanishes.
- *Local `.env`*: non-option lines are `eval "export KEY=VALUE"`-ed (134-135) — the file is executed as shell; "already defined" is `env | grep "${KEY}"` (131), a substring over all names and values; values are cut at the first `=` (122-124).
- *No `--portable-mode` default*: only the port is injected (83-84, 187-189). If `DAEMON_OPTS` is absent and `.env` lacks it, the server starts without `--portable-mode` — the restart trap that "cost this arc a full session" (H11 item 3:124-136; `yamaguchi_narrow_bind.bash:31-38`), reintroduced by construction.
- *Binary path*: `/usr/lib/duplicati/duplicati-server` (WRAP:75) vs the handoff-era `/usr/bin/duplicati-server`; which exists is **UNKNOWN**.

**Credential-shaped literal.** WRAP:49, inside the commented "Old Unit file" block, is an `Environment=SETTINGS_ENCRYPTION_KEY=<value>` line whose value is a 36-character mixed string (12 upper, 14 lower, 5 digits, 5 symbols); present at line 49 in both the 1967 and 1968 versions; not quoted here. WRAP:196 prints `env | grep SETTINGS_ENCRYPTION_KEY` — gated behind `DEBUG_MODE` in HEAD but **unconditional** in 1967 (its line 207), so the first merged revision echoed the key to stdout/journal on every start. `SETTINGS_ENCRYPTION_KEY` is exactly the mechanism the owner **rejected** on 2026-08-30 ("adds a third key needing escrow … worse recovery story", H12 §0:68-71); the wrapper implies that decision was reversed or is being revisited — the handoffs cannot say.

---

## 6. Open items as of 2026-09-07, and superseded items

### 6a. Open at H13

| # | Item | Citation |
|---|---|---|
| 1 | **Criterion 5 — reboot/logout survival NEVER exercised**; `yamaguchi_reboot_verify.bash pre/post` prepared; owner reboots on his schedule; post-reboot sdc4 absent so several tools refuse by design | H13 §1.1:49-72; H11 item 4:147-185 |
| 2 | **sdc4 reclaim**: cleared by content but "the literal claim is FALSE; the operational claim holds" (5 paths/17 dirs only on sdc4, one zero-byte notebook vacuously matched); **`sda` health never checked**; re-verify sda1 after each move; sdc2 grow is NTFS on the disk carrying live `/home` — rescue boot only | H13 §1.2:74-108 |
| 3 | **Print the escrow sheet** (sheet present ⇒ owed); password-manager copy interim; third copy `/mnt/Backups/Ubuntu/_yamaguchi_keys/env` | H13 §0:30, §1.3:110-121; H12 item 2:146-151 |
| 4 | Drift-guard tests missing in seven repos (CI item carried in the handoff, not backup infrastructure) | H13 §1.4 |
| 5 | **`yamaguchi_records_sync.bash` dead**; mirror frozen at 08-30; §8.21.4/§8.25.1 evidence is prose only | H13 §1.5:150-160 |
| 6 | **Watchdog lacks `ProgramState` + `SchedulerQueueIds`** (`Paused` + non-empty queue is always a fault); redeploy only via the deploy script; `ExecStart` = primary checkout | H13 §1.6:162-178 |
| 7 | **2026-08-30 stuck pause — root cause unknown**; read `paused-until` before resuming; capture the in-window baseline at the reboot | H13 §1.7:180-189 |
| 8a | **Deployed-vs-repo runner divergence** (08-29 DB-holder fix absent from `~/.local/bin`); do not repair paths; **removal PR (§8.11.3) unopened** | H13 §1.8:193-200; H12 item 7:171-172 (observed diff agrees) |
| 8b | No §8.26 existed for the 09-02 relocation/README/unmount (that PR adds it — verify) | H13 §1.8:201-204 |
| 8c | `duplicati_dlist_crosscheck.py` residuals (gpg seam rebinding under aes; same-fs workdir only WARNING) | H13 §1.8:205-208 |
| 8d | `yamaguchi_server_db_snapshot.py:20` still says "encrypted" (confirmed at SNAP:20 and :36) | H13 §1.8:209-211 |
| 8e | `duplicati_first_backup.bash` hard-codes `MOUNT` while `DESTDIR` is `$3` (confirmed :32, :38, :40, :44, :49); no test | H13 §1.8:212-215 |
| 8f | `.env` reconciliation for `curious-plotting-hummingbird/.env` (cleartext passphrases inside a Source; git-ignored → `worktree remove` deletes silently) | H13 §1.8:218-222; H11 §0:51-56 |
| 8g | **Cloud reporting** (bearer JWT to `api.duplicati.com`, exp "2028") — deferred, not rejected | H13 §1.8:223-225 |
| 8h | Two orphans: 8200 repurposed to 8300; schema-19 profile DB | H13 §1.8:226-228 |
| 8i | `--run-script-before` mount guard never applied or refused | H13 §1.8:229-230 |
| 8j | Candidate A drafted, undeployed, never revoked | H13 §1.8:231-232 |
| — | Server-DB snapshot **capture in a completed backup** "not yet confirmed" at H12, never closed in H13 → UNKNOWN | H12:121-126, 161-163 |
| — | Tar lane (outside the Duplicati arc): unencrypted 111 GB `.tgz` on `EBC5-F0A3`; capacity; no regression test for JB | H9 §7:371-376; §3:282-286; H13 §5 |

### 6b. Superseded / corrected along the chain

| Earlier | Superseded by | Citations |
|---|---|---|
| Remove root 8200 (O-7, "candidate for removal") | That unit, now on 8300, **IS production — never remove** | H1 O-7:256-258; H2 §9:196-199; H3:155; H4:250 → H5:14-18, §0:39-43; H6 §0:55-56 |
| User CLI lane as the replacement | Superseded by the server pivot; 0-for-3; retirement candidate | H3:144-145; H4 §2 → H5 §0:41-43 |
| "Investigate GPG first; no AES" | AES adopted after gpg reproduced `GPGFlushError` under root | H4 §0:30-37 → H5 §0:44-48 |
| Destination `/media/pcalnon/temp_backups/Yamaguchi` | `/mnt/Backups/Ubuntu/Yamaguchi` | H5 §4:220 → H8:9-11 |
| Tempdir sdc4 `_duplicati_tmp` | `~/.cache/duplicati-tmp` | H4 §2:132-134 → H10 §0:17 |
| "Under 10 minutes" | A ~9-10.5 min class, not a floor | H8 §0:20 → H10:8-9, 32-34 |
| "Records mirror NOT re-synced" | Already current | H10:92 → H11:63-65 |
| "PR #1433 open" | Merged 08-28 | H10 §0:16 → H11:62 |
| "Loopback already staged" | Stale; done 08-30 by deleting the `any` flag | H11:66-67; H12:111, 115-119 |
| "Encrypted passphrase in `Duplicati-server.sqlite`" (note sections, snapshot unit comment, SNAP:20/36) | **Cleartext**; owner accepts and documents | H11:110-113; yamaguchi-server-db-snapshot.service:5 → H12 §0:13-76 |
| "`PASSPHRASE` survives only as root-only material in one unbacked-up DB" | False three ways | H11 §0:34-36 → H12:134-136 |
| `ProgramState=Paused` as incident | `startup-delay=30m`; no reboot | H12:130-133 |
| Census 818 | 823 → 848; only AGREE/DIVERGE signals | H11:254 → H12:137-138 → H13 §0:13-16, 25 |
| Schedule "13:00 CDT / 18:00Z?" | 14:00Z = 09:00 CDT confirmed | H5 item 8:148-151 → H7 §0:17 |
| win11 VDI added | Excluded 08-26 | H5 §0:55-60 → H7 §0:18 |
| Recreate "defer" | Recreate dead | H4 item 7:242-248 → H5 §1:79 |
| Purge pending | Executed option (b) | H4 item 4:217-221 → H11:77-79 |
| `dbconfig.json` delete vs rewrite | Deleted | H6 item 6 → H8 §0:21 |
| 196 GB sdc4 copy "KEEP" | sdc4 unmounted 09-02; frozen set relocated to sda1 | H8 §1:28-32; H10 §0:18 → H13 §0:27-28 |
| "Class-2 tar drill still owed" | Closed ml#1442 | H9 §7:369-370 → H12:179-182; H13 §5 |
| "Both dlist tools default to gpg" | crosscheck gpg (`:144`), query aes (`:103`) | H13 §2:255-258 |
| Size cap 50 MB → 2 GB → 8 GB | Removed | H1 §2.2; RUN:226; `yamaguchi_build_job.py:26` → H5 §0:57-60 |
| Single tar drive `DFF3-2782` | `EBC5-F0A3` + `DFF3-2782` | H1 §2:68 → JB:121; H9 §6:359 |

---

## 7. What this entry point cannot tell us

1. **Anything in `notes/`** — the certification note's §8.x record, the plan's §7 criteria, the findings/investigation notes; every "§8.x" above is a handoff's pointer, not a verified section.
2. **System-scope units**: whether `/etc/systemd/system/yamaguchi-server-db-snapshot.{service,timer}` are installed/enabled, whether the timer has fired since 08-30, and whether a snapshot was ever captured in a completed backup.
3. **The live `duplicati.service`**: which unit file is active, which **user** it runs as now (root per handoffs; `User=duplicati` per the wrapper's comment), whether `/home/duplicati/…` paths or `/usr/lib/duplicati/duplicati-server` exist, and the current `/etc/default/duplicati` — including whether `--portable-mode` and the commented trap line are still there.
4. Whether the **wrapper is deployed at all**, and whether `SETTINGS_ENCRYPTION_KEY` is now in use (reversing H12 §0:68-71).
5. **`timers.target.wants/` contents** — not listed; which timers are actually enabled is unverified beyond the directory mtime.
6. The **live job configuration** (sources, 44 filters, settings, `TargetURL`, schedule, `remote-control-enabled`, report URL) — handoff claims only; the config-of-record JSONs under `_yamaguchi_check/` and the sda1 mirror were not inspected.
7. Whether **criterion 5** has been exercised since 09-07, whether the escrow sheet was printed/shredded, whether `sda` SMART was read, whether sdc4 still exists.
8. Whether the **primary checkout** is synced (both deployed timers execute its scripts, so the live watchdog/snapshot code version is unknown) and whether its `.env` still holds `DUPLICATI_WEB_CREDENTIAL`.
9. The **tar lane's last real run**, what is on the two USB drives now, whether the 111 GB plaintext `.tgz` was replaced, whether both drives still automount under `/media/pcalnon/`.
10. The state of `curious-plotting-hummingbird/.env` and the other stale arc worktrees (H7 §1 item 9:33).
11. Whether `juniper-deploy/util/sops-backup-key.sh` has ever been run (H1 O-2 unanswered throughout) — the SOPS age key's escrow is outside every mechanism inventoried here.
12. Any **secret contents**: passphrase values were never seen; fingerprints and the wrapper's header literal were deliberately not reproduced.

---

### Files read (under the worktree root above)
Handoffs: all 13 `prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-2*_*.md`, `…08-30_*.md`, `…09-07_duplicati-arc-outstanding-work.md` (fully). Tooling: `util/juniper-backup.bash` (592 lines), `util/duplicati_scheduled_backup.bash` (285), `util/duplicati_backup_failure.bash` (62), `util/install_duplicati_timer.bash` (92), `scripts/duplicati-wrapper.bash` (199), all seven `util/systemd/{duplicati-backup*,yamaguchi-*}` units (the soak units mention neither name). Headers + argument parsing of all 45 `util/ad-hoc/{duplicati_*,yamaguchi_*}.{py,bash}`; `yamaguchi_watchdog.py`, `yamaguchi_server_db_snapshot.py`, `yamaguchi_watchdog_deploy.bash`, `yamaguchi_server_db_deploy.bash`, `yamaguchi_run_script_after.bash` in full; headers of the five tar-lane ad-hoc drills; `tests/test_duplicati_*.py` docstrings/test names; `docs/REFERENCE.md:523-720`. Git: `git log` over the four paths; `git show --stat` of `6708cb28`/`52571621`; `gh pr view 1967`/`1968`. Host (permitted only): `ls -la ~/.config/systemd/user/`; `diff ~/.local/bin/duplicati-scheduled-backup.bash util/duplicati_scheduled_backup.bash`.

<!-- markdownlint-enable -->

---

## Report 2a — Determine the CURRENT LIVE STATE by probing the host directly (read-only)

Subagent id `aa2c4b32ab5b27615` (40,062 characters).

<!-- markdownlint-disable -->

All probes are complete; nothing further is needed. Here is the report.

# Yamaguchi backup infrastructure — live-state probe (2026-09-21 03:00–03:15 CDT)

Probed read-only from `uid=1000(pcalnon)`; scratch copies only under `/tmp/claude-1000/…/scratchpad/agent3-live/`. Host up since `2026-09-07 23:12:17`. No value of any secret appears below (shapes only). Two shapes of key material surfaced in tool output during the probe (a literal in a repo file header, and bash/wrapper echoes in the journal); both are described, neither is reproduced.

---

## 1. Identity

```
$ id
uid=1000(pcalnon) gid=1000(pcalnon) groups=1000(pcalnon),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),100(users),114(lpadmin),128(libvirt),984(vboxusers),993(kvm),1003(docker)
$ id -G
1000 4 24 27 30 46 100 114 128 984 993 1003            <- NO 139
$ getent passwd duplicati
duplicati:x:133:139:System user to run the Duplicati backup service:/home/duplicati:/bin/bash
$ getent group duplicati
duplicati:x:139:pcalnon,duplicati
$ pgrep -x dropbox
2948130
2949543                      (<defunct> zombie)
$ grep -E '^(Name|Uid|Gid|Groups)' /proc/2948130/status
Name:   dropbox
Uid:    1000 1000 1000 1000
Gid:    1000 1000 1000 1000
Groups: 4 24 27 30 46 100 114 128 984 993 1000 1003    <- NO 139
```

`/etc/group` says pcalnon is a member of `duplicati`; the running processes say otherwise. Supplementary groups are copied into a process's credentials once, at login (`initgroups`), and inherited by children; `usermod -aG` (journal: `2026-09-18T19:27:38 usermod[384091]: add 'pcalnon' to group 'duplicati'`) edits the file only. Every process descended from a session that started before 19:27 on 09-18 — the user manager `systemd --user` (PID 13362, started 09-07 23:13:03, `Groups:` lacks 139), Dropbox (its PPid is 13362), the watchdog timer's children, and my own shell — still lacks gid 139. Processes started from a fresh login *do* have it: `gdm-session-worker`, `gnome-session`, a `su -l pcalnon` bash (PID 3082725), a `clamscan` from 09-18 evening. `sg duplicati -c id` shows `gid=139(duplicati)` because `sg` consults `/etc/group` at invocation; that is why `sg` is needed for anything group-gated (§8).

## 2. The systemd unit

`systemctl cat duplicati.service` begins with: `# Warning: duplicati.service changed on disk, the version systemd has loaded is outdated.` On-disk fragment (`/usr/lib/systemd/system/duplicati.service`, `-rw-r--r-- root root 461`, **mtime 2026-09-21 01:44:57**):

```
[Unit]
Description=Duplicati web-server
After=network.target
[Service]
Nice=19
IOSchedulingClass=idle
IOSchedulingPriority=7
User=duplicati
Group=duplicati
EnvironmentFile=-/etc/default/duplicati
# ExecStart=/usr/bin/duplicati-server $DAEMON_OPTS
# ExecStart=/home/duplicati/bin/duplicati-wrapper.bash "${DAEMON_OPTS}"
ExecStart=/home/duplicati/bin/duplicati-wrapper.bash '--daemon-opts="${DAEMON_OPTS}"'
Restart=always
[Install]
WantedBy=multi-user.target
```

`systemctl show` (loaded state):

```
ActiveState=active  SubState=running  UnitFileState=enabled  NeedDaemonReload=yes
FragmentPath=/usr/lib/systemd/system/duplicati.service  DropInPaths=   (none; /etc/systemd/system/duplicati.service.d/ does not exist)
MainPID=1397393  NRestarts=0  ExecMainStartTimestamp=Sun 2026-09-20 18:19:42 CDT
ExecStart={ path=/home/duplicati/bin/duplicati-wrapper.bash ; argv[]=/home/duplicati/bin/duplicati-wrapper.bash ${DAEMON_OPTS} ; ... }
EnvironmentFiles=/etc/default/duplicati (ignore_errors=yes)   User=duplicati  Group=duplicati
Environment=            (property length 0 — the LOADED unit carries no Environment= line)
UMask=0022  Restart=always  RestartUSec=100ms  StartLimitBurst=5  StartLimitIntervalUSec=10s
ProtectHome=no ProtectSystem=no PrivateTmp=no DynamicUser=no SupplementaryGroups=
```

**Loaded vs on-disk ExecStart differ.** Running instance was launched as `duplicati-wrapper.bash ${DAEMON_OPTS}` (word-split → argv `--webservice-port=8300`). The file now says `'--daemon-opts="${DAEMON_OPTS}"'` (one argv element, literal double quotes included). A root `vim /usr/lib/systemd/system/duplicati.service` (PID 2318515) has been open since **2026-09-21 01:41:41** — the unit is being edited right now.

`/etc/default/duplicati` (`-rw-r--r-- duplicati duplicati 404`, mtime **2026-09-20 16:39:58** — owned by the service user, not root):

```
# DAEMON_OPTS="--webservice-interface=loopback --webservice-port=8300"
# DAEMON_OPTS="--webservice-port=8300 --portable-mode"
DAEMON_OPTS="--webservice-port=8300"
# DAEMON_OPTS=""
```

`--portable-mode` is commented out; the journal shows it was live until 2026-09-20 13:32 (§4).

## 3. The running server

```
$ ps -o pid,ppid,user,group,etimes,lstart,args -p 1397393
1397393  1  duplica+ duplica+ 31280  Sun Sep 20 18:19:42 2026  /usr/lib/duplicati/duplicati-server --webservice-port=8300
                                                                  ^ single argv element WITH trailing space (wrapper's exec "$SERVER" "$OPTS")
/proc/1397393/status: Uid 133  Gid 139  Groups: 139        (only the duplicati group; cwd/exe/fd unreadable to me)
$ ss -tlnp | grep -E ':8200|:8300'
LISTEN 0 512 127.0.0.1:8300   LISTEN 0 512 [::1]:8300        (nothing on 8200; loopback only)
$ curl -s -o /dev/null -w '%{http_code}' http://localhost:8300/            -> 200
$ curl -s -i http://localhost:8300/api/v1/serverstate | head -5
HTTP/1.1 401 Unauthorized / Content-Length: 0 / Server: Kestrel / WWW-Authenticate: Bearer
$ ls -ld /usr/lib/duplicati/data /usr/lib/duplicati
drwx------ 3 duplicati duplicati   4096 2026-09-18 21:03:34 /usr/lib/duplicati/data     (birth 2026-08-25 02:38:43, ctime 2026-09-19 19:15:00)
drwxr-xr-x 21 duplicati duplicati 135168 2026-09-19 21:35:07 /usr/lib/duplicati
```

Other duplicati-user processes: two `bash` shells under `su` (PIDs 3065639, 3117158) alive since 09-19 18:24:50 and 18:52:00 — the operator's working shells.

`/home/duplicati/.config/Duplicati/` (`ls -la`, then `stat '%w | %y | %z | %s | %U:%G %a'` = birth | mtime | ctime):

```
drwxrwxrwx duplicati:duplicati 4096  .                              birth 09-19 18:40:11 | mtime 09-20 18:19:43.917 | ctime 09-20 18:33:45 | 777
-rw-rw---- .env                                    1599             birth 09-20 16:39:43 | mtime 09-20 16:39:43 | 660
-rwxrwxrwx Duplicati-server.backup               479232             birth 09-20 04:41:07 | mtime 08-25 02:19:47 | ctime 09-20 18:25:47 | 777
-rwxrwxrwx Duplicati-server.sqlite                 4096             birth 09-19 21:57:36 | mtime 08-25 02:19:48 | ctime 09-20 18:25:47 | 777
-rwxrwxrwx Duplicati-server.sqlite-shm            32768             birth 09-20 04:43:02 | mtime 09-20 18:43:41 | 777
-rwxrwxrwx Duplicati-server.sqlite-wal           370832             birth 09-20 18:19:43.917 | mtime 09-20 18:42:47 | 777
-rwxrwxrwx Duplicati.GUI.TrayIcon-crashlog.txt     3700             birth 09-19 18:42:18 | mtime 09-19 21:20:56 | ctime 09-20 18:25:47 | 777
drwxrwxr-x backups/                                                 birth 09-19 18:40:36 | mtime 09-19 21:56:55
drwxrwxr-x control_dir_v2/                                          birth 09-19 18:42:18 | mtime 09-20 18:19:45.107
   -rw-r--r-- lock_v2  8 bytes                                      mtime 09-20 18:19:45.109
-rw-rw-r-- installation.txt                         285             birth 09-20 04:15:42 | mtime 09-20 18:11:25
-rw-rw-r-- machineid.txt                            247             birth 09-19 18:42:22 | mtime 2025-08-31 05:20:19
drwxr-xr-x root:root temp/                                          birth 09-20 18:18:49 | mtime 09-20 18:19:26
   -rw------- duplicati:duplicati Duplicati-server.sqlite-wal 112587272   birth 09-20 17:57:56 | mtime 08-25 02:20:46   (birth PREDATES its directory -> moved in, not copied)
drwxrwxr-x temp1/                                                   birth 09-20 18:05:05 | mtime 09-20 18:08:41 | ctime 18:14:29
   five files (crashlog, .backup, .sqlite, -shm, -wal 112587272) all birth 09-20 18:08:41, 0600 duplicati:duplicati (unreadable to me)
```

`/home/duplicati/.config/` also holds `Duplicati-OLE/` (`drwx------`, birth 09-19 18:34:43, mtime 09-19 21:21:41, ctime 21:23:42 — contents unreadable) and the parent dir's mtime is 09-20 13:00:41 (an entry was created/renamed/removed then). `/home/duplicati/bin/` is `777` and contains only `duplicati-wrapper.bash -> /home/pcalnon/Development/python/Juniper/juniper-ml/scripts/duplicati-wrapper.bash` (symlink birth 09-20 16:53:58). Path to the target, all traversable: `/home drwxr-xr-x root`, `/home/pcalnon drwxr-xr-x`, then `Development`, `python`, `Juniper`, `juniper-ml`, `scripts` all `drwxrwxr-x pcalnon:pcalnon`; target `-rwxrwxr-x pcalnon:pcalnon`.

`/home/pcalnon/.config/Duplicati/` (top level, `drwx------ pcalnon 700`): `Duplicati-server.backup 479232 (mtime 08-25 02:19:47)`, `Duplicati-server.sqlite 4096 (mtime 08-25 02:19:48, ctime 09-19 21:20:55)`, `-shm 32768 (mtime 09-19 21:20:56)`, `-wal 112587272 (mtime 08-25 02:20:46)`, `Duplicati.GUI.TrayIcon-crashlog.txt (mtime 09-19 21:20:56)`, `installation.txt (mtime 09-20 18:10:32)`, `machineid.txt`, `backups/`, `control_dir_v2/lock_v2 (mtime 08-21 16:25:38)`. `cmp` shows `installation.txt`, `machineid.txt` and the crashlog are byte-identical between the two directories; `sha256` of the 4096-byte `Duplicati-server.sqlite` is identical in both (`352a9bb2…`), as is `Duplicati-server.backup` (`e10e28d1…`).

**Data-folder inference.** Service start 18:19:42; new WAL born 18:19:43.917 (= data dir mtime); `control_dir_v2/lock_v2` mtime 18:19:45.109; wrapper logged "Server has started" 18:19:46; the live DB's `ErrorLog` rows are stamped 18:39–18:42 and the `-shm` was written 18:43:41. Everything the running server has written since start landed in `/home/duplicati/.config/Duplicati`. Limits: the lock mtime alone proves only that *some* Duplicati instance initialised this folder 3 s after the start; it cannot exclude the server also touching `/usr/lib/duplicati/data` (700, unreadable to me). Root can settle it with `ls -l /proc/1397393/fd`.

## 4. The journal

Captured to scratch: 4391 raw lines since 2026-09-17 (3219 after the stack-frame filter). The wrapper ran once with `DEBUG_MODE` on and echoed the `.env` line by line; counts of lines that carry key material (never printed): `LINE:` 264, `SETTINGS_ENCRYPTION_KEY=` 98, `Environment Variable:` 25, `Settings Encryption Key` 12, `Exporting Environment Variable` 12, `ENV_FILE_VAR_VALUE` 12, `EXPORT_CMD` 2, bash `export: … not a valid identifier` lines that quote the `.env` value verbatim 5 (16:41:15–20 on 09-20), sign-in URLs with a token 5. `/var/log/journal/*/system.journal` is `-rw-r----- root systemd-journal` with an ACL that admits `adm` (I read it unprivileged).

**Digest of all 129 start attempts since 09-17** (one row per collapsed run; 11 reached "Server has started"; 23 hit `Start request repeated too quickly` = StartLimitBurst 5/10 s):

| Start (CDT) | × | Outcome / verbatim reason line |
|---|---|---|
| 09-17 01:31:00 | 1 | UP 01:31:03 on 8300, after `No database encryption key was found. The database will be stored unencrypted. Supply an encryption key via the environment variable SETTINGS_ENCRYPTION_KEY or disable database encryption with the option --disable-db-encryption`. Stopped 09-18 19:57:16; `Consumed 1h 34min 50.891s CPU time over 1d 18h 26min 46.708s wall clock time, 10.8G memory peak, 3.9G memory swap peak.` |
| 09-18 19:57:47–49, 20:02:24–26 | 10 | `Crash!` / `Unhandled exception. System.UnauthorizedAccessException: Access to the path '/usr/lib/duplicati/data/installation.txt' is denied.` → `code=killed, status=6/ABRT` |
| 09-18 20:22:11 | 1 | UP 20:22:13 (no key); later `System.Exception: Failed to process the path: Access to the path '/mnt/Backups' is denied.`; stopped 20:42:07 |
| 09-18 20:42:37 | 1 | UP 20:42:39 (no key); stopped 21:02:27 |
| 09-18 21:03:27 | 1 | UP 21:03:30 — **no "no key" warning: a key was present**; stopped 21:07:35 |
| 09-18 21:08:05–21:11:42 | 15 | `A serious error occurred in Duplicati: Duplicati.Library.Interface.SettingsEncryptionKeyMismatchException: Encryption key used to encrypt target settings does not match current key.` → `status=100` |
| 09-18 21:16:17 → 09-19 19:15:01 | 23 | `The database appears to be encrypted, but no key was specified. Opening the database will likely fail. Use the environment variable SETTINGS_ENCRYPTION_KEY to specify the key.` / `SettingsEncryptionKeyMissingException: Encryption key is missing.` |
| 09-19 19:19:55–20:44:37 | 20 | `/home/duplicati/bin/wrapper.bash: line 30: --webservice-port=8300: command not found` → `status=127` |
| 09-19 20:48:11–15, 21:41–21:55 | 25 | wrapper echoes `Input Parameters: --webservice-port=8300 --portable-mode` / `EXEC_START: /usr/bin/duplicati-server`; server: `Error message: Access to the path '/home/duplicati/.config/Duplicati/Duplicati-server.sqlite' is denied.` → `status=100` |
| 09-19 21:20:37 | 1 | UP 21:20:41 **on port 8200** (options not actually passed); stopped 21:23:02 |
| 09-19 21:57:35 | 1 | UP 21:57:41 **on 8200**; stopped 09-20 04:06:07 |
| 09-20 13:32:33–37 | 5 | `/home/duplicati/bin/wrapper.bash: line 38: /home/duplicati/.config/.env: No such file or directory` |
| 09-20 13:32:46 | 1 | UP 13:32:50 on 8200 (still `--portable-mode` echoed); stopped 13:36:20 |
| 09-20 13:36:37 | 1 | UP 13:36:40 on 8300, `DAEMON_OPTS: --webservice-port=8300` (portable-mode gone); stopped 13:37:19 |
| 09-20 16:41:15–20 | 5 | bash `export: … not a valid identifier` (the `.env` value echoed) then `SettingsEncryptionKeyMissingException` |
| 09-20 16:44:28–33 | 5 | `SettingsEncryptionKeyMismatchException: Encryption key used to encrypt target settings does not match current key.` |
| 09-20 16:50:12 | 1 | UP 16:50:15; stopped 16:50:56 |
| 09-20 17:30:14 | 1 | UP 17:30:17 with DEBUG echoes of `.env`; stopped 17:30:28 |
| 09-20 18:02:54–59, 18:12:25–31 | 10 | `Failed to create, open or upgrade the database.` / `The database has version 19 but the largest supported version is 12.` / `…there is likely a backup file of the previous database version in the folder /home/duplicati/.config/Duplicati.` |
| 09-20 18:19:42 | 1 | **current**: `Executing Duplicati Server: "/usr/lib/duplicati/duplicati-server --webservice-port=8300 "` (89 chars, no datafolder/portable flag), UP 18:19:46 on 8300, sign-in link printed (5-min token, expired 18:24:46); 18:47:44 `Failed to process the path: Access to the path '/media/pcalnon/temp_backups' is denied.` and `…'/media/pcalnon' is denied.` Nothing logged after 19:00. |

Window 17:30–19:00 in full = the last five rows above (544 raw lines; 22 `LINE:` echoes and 1 `Settings Encryption Key` echo redacted).

`journalctl --user -u yamaguchi-watchdog.service`: `09-17 12:00:39 OK OK backup=2 newest run 2026-09-17T14:00:00.0717854Z ParsedResult=Success age=3.0h`; `09-18 12:00:39 OK … newest run 2026-09-18T14:00:00.1394552Z … Success`; `09-19 12:00:39 ALERT UNREACHABLE backup=2 login raised URLError: <urlopen error [Errno 111] Connection refused>`; same 09-20 12:00:39; `09-21 02:52:01 ALERT UNREACHABLE backup=2 login failed: FATAL: login failed (401): {"error": "{\"Error\":\"Failed to log in\",\"Code\":401}"}` (each ALERT → `status=1/FAILURE`, unit now `failed`).

`journalctl -u yamaguchi-server-db-snapshot.service` (readable): daily 08:45 runs 09-15…09-20, all `integrity : ok (16 tables)`, `source : /usr/lib/duplicati/data/Duplicati-server.sqlite` growing 208.0 → 240.0 KiB, `wrote : /home/pcalnon/.local/state/duplicati-server-db/Duplicati-server.sqlite (240.0 KiB, mode 0600, owner pcalnon)`. Last: **2026-09-20 08:45:01**.

`journalctl _COMM=sudo --since 2026-09-18` (11 lines, 4 commands): `09-18 20:10:00 root : TTY=/dev/pts/21 ; PWD=/mnt/Backups/Ubuntu/Dropbox/Backups ; USER=duplicati ; COMMAND=/usr/bin/vim /usr/lib/duplicati/data/installation.txt`; `20:14:13 pcalnon … COMMAND=/usr/bin/su -`; `20:41:44 … /usr/bin/su -`; `09-19 17:43:06 … /usr/bin/su -`. Everything else was done inside those root shells (invisible to the sudo log). `_COMM=su` adds ~15 `su - duplicati` sessions 09-19 17:44–18:52 (two never closed) and one `su duplicati` at 09-20 19:07:38. Account changes: `09-18 19:25:09 groupadd duplicati GID=139`, `19:27:38 usermod add 'pcalnon' to group 'duplicati'`, `19:29:07 useradd duplicati UID=133 home=/nonexistent shell=/bin/false`, `19:30:36 home → /home/duplicati`, `19:53:27 add 'duplicati' to group 'duplicati'`, `09-19 17:46:52 shell → /bin/bash`.

## 5. Timers and units

```
system : yamaguchi-server-db-snapshot.timer  NEXT Mon 09-21 08:45:00 CDT  LAST Sun 09-20 08:45:01   enabled
user   : yamaguchi-watchdog.timer            NEXT Mon 09-21 12:00:00 CDT  LAST Sun 09-20 12:00:39   enabled ; yamaguchi-watchdog.service: loaded failed failed
user   : duplicati-backup.timer disabled (preset enabled); duplicati-backup.service / duplicati-backup-failure.service static
duplicati.service enabled ; loginctl Linger=yes
~/.config/systemd/user/: duplicati-backup{,-failure}.service, duplicati-backup.timer (08-24), yamaguchi-watchdog.{service,timer} (08-26); timers.target.wants -> yamaguchi-watchdog.timer only; dir mtime 09-20 19:00:30
~/.local/state/duplicati/last-run.status:  result=FAILED / when=2026-08-25T05:13:35-05:00 / reason=duplicati-cli rc=143 / log=…backup-20260824-222158.log
~/.local/state/duplicati/server-watchdog.status: 2026-09-21T02:52:01-0500 ALERT UNREACHABLE backup=2 login failed: … (401)
```

Scripts named by ExecStart, and what the move to a `duplicati` system user breaks:

- `/home/duplicati/bin/duplicati-wrapper.bash → …/juniper-ml/scripts/duplicati-wrapper.bash` (deployed target is a file in the developer's live checkout; it changed twice *during this probe*: 12863 B/218 lines at 02:15:30 with `--daemon-opts` parsing, then 11537 B/199 lines at 03:04:40 byte-identical to worktree HEAD `52571621`). Hardcodes `/usr/lib/duplicati/duplicati-server`, `/etc/default/duplicati`, `/home/duplicati/.config/Duplicati/.env`, port default 8300. Parses `.env`: `export K=V` lines are `eval`ed into the environment, `--option` lines become server options; final `exec "${DUPLICATI_SERVER}" "${DUPLICATI_OPTS}"` passes **all options as one argv element** (hence the trailing space in `ps`; works only while there is exactly one option). The committed version has **no `--daemon-opts` handling**, yet the on-disk unit now passes `'--daemon-opts="${DAEMON_OPTS}"'`. Its header comment reproduces an "Old Unit file" including a literal `Environment=SETTINGS_ENCRYPTION_KEY=<36 chars: upper/lower/digit, punctuation set $ % * @>` — committed in `6708cb28` (#1967) and `52571621` (#1968) on `origin git@github.com-juniper-ml:pcalnon/juniper-ml.git`.
- `util/ad-hoc/yamaguchi_watchdog.py` (user unit, runs as pcalnon): `--base` default `api.BASE = "http://127.0.0.1:8300"`, `--backup-id` default `"2"`, credential read in-process from `/home/pcalnon/Development/python/Juniper/juniper-ml/.env` key `DUPLICATI_WEB_CREDENTIAL`, state dir `~/.local/state/duplicati`. Broken by the move: the new server DB has its own `server-passphrase`/`server-passphrase-salt` (§9 (b)) → 401 today; if the job is re-imported under a new ID, `JOB_MISSING`. Port unchanged.
- `util/ad-hoc/yamaguchi_server_db_snapshot.py` (root unit): `SRC = "/usr/lib/duplicati/data/Duplicati-server.sqlite"`, `DEST_DIR = "/home/pcalnon/.local/state/duplicati-server-db"`, `OWNER = "pcalnon"`; docstring says the source dir is `drwx------ root root` (now `duplicati:duplicati`). Broken by the move: it keeps snapshotting a DB the live server no longer opens — which, right now, is what preserves the only consistent copy of the Yamaguchi job.
- `~/.local/bin/duplicati-scheduled-backup.bash` (user lane, disabled): defaults `DEST=/media/pcalnon/temp_backups/Ubuntu` (**not a mountpoint any more**, sdc4 is gone), `DBPATH=/home/pcalnon/.config/Duplicati/DQRVQNDIFX.sqlite`, `STATE_DIR=${HOME}/.local/state/duplicati`, `EnvironmentFile=%h/.config/duplicati-backup/env`. Run as duplicati at 09-20 19:07:38 it wrote `/home/duplicati/.local/state/duplicati/last-run.status`: `result=FAILED … reason=PASSPHRASE … unset or empty; refusing to run`.

## 6. Storage and destination

```
sda 3.6T WDC WD40EZAZ-00SF3B0 sata -> sda1 ext4 /mnt/Backups (label Backups, UUID 41508769-…)   df: 3.6T, 400G used, 12%
sdc 7.3T WDC WD8002FZWX-00BKUA0 sata -> sdc1 16M | sdc2 1.8T ntfs (WindowsPrograms) | sdc3 3.7T ext4 /home (66%)   NO sdc4
nvme0n1 1.8T WD_BLACK SN850X -> p5 728.1G ext4 / (44%), p6 swap, p1/p2 ntfs, p3 vfat
findmnt: /mnt/Backups /dev/sda1 ext4 rw,relatime ; /home /dev/sdc3 ext4 rw,relatime ; / /dev/nvme0n1p5 ext4 rw,relatime
fstab (4 lines): / , swap, /home, /mnt/Backups — all by-uuid, ext4 defaults
/media/pcalnon: random_drive/ (2025-12-21), temp_backups/ (09-09, EMPTY, "is not a mountpoint")
```

Destination chain — every dir `drwxrwx--- pcalnon:duplicati` (`/mnt/Backups`, `Ubuntu`, `Dropbox`, `Backups`, `Yamaguchi`); `getfacl -p` shows only `user::rwx group::rwx other::---` on all five and `user::rwx group::rwx other::---` on `duplicati-20260918T140000Z.dlist.zip.aes` (no default ACL entries, no setgid bit, although `ls` prints a `+`). ctime of the chgrp/chmod: `/mnt/Backups` 09-18 20:36:53, `Ubuntu` 20:37:41, `Dropbox` 09-19 17:37:24, `Backups` and `Yamaguchi` 09-20 12:55:54 / 12:56:10 (an entry was created or removed then; nothing remains). `test -w`: all five **writable** for pcalnon (owner) and under `sg duplicati` (group).

`Yamaguchi/`: **877 files, `du -sh` 203G**, census `877 pcalnon:duplicati 770`, extensions `877 aes` (0 gpg), types `434 .dblock. / 434 .dindex. / 9 .dlist.`; ctime histogram `874 @ 2026-09-19 17h, 3 @ 18h`; mtime by day: 09-09 407, 09-10 444, 09-11 2, 09-12 3, 09-15 10, 09-16 3, 09-17 5, **09-18 3 (last)**. Newest: `09-18 09:12:00 duplicati-20260918T140000Z.dlist.zip.aes (80211869)`, `09:11:31 duplicati-i023104c4…dindex`, `09:11:30 duplicati-b0ad5018…dblock (151562109)`, `09-17 17:25:56 duplicati-20260917T221344Z.dlist`. All dlists: `20260825T102739Z, 20260901T140000Z, 20260908T140000Z, 20260912T140000Z, 20260915T085649Z, 20260915T204850Z, 20260916T183346Z, 20260917T221344Z, 20260918T140000Z` (9 = the job DB's `BackupListCount 9`, §9 (e)).

`Backups/` also holds `_yamaguchi_frozen_20260826/` (811 files, `pcalnon:duplicati 770`), `_yamaguchi_keys/` (`README.md 1131`, `env 388` — names only), `_yamaguchi_records/`, ten `duplicati-2024…2026….dlist.zip.gpg` (56–165 MB each), `lost+found`. `/mnt/Backups/Ubuntu/README.md`: `No such file or directory`. `/mnt/Backups/Ubuntu/Dropbox/Backups/README.md` (verbatim, trimmed to its load-bearing lines):

> `# Old Duplicati gpg archive -- dlists retained, volumes purged` … `What was removed: 5356 volumes (2.3 TiB). What is kept: the 10 .dlist files below` … `These dlists are self-contained … What they can no longer do is RESTORE` … `Second copy (CORRECTED 2026-09-02) … The second copy is now: /home/pcalnon/.local/state/yamaguchi-old-archive-dlists/ … Verified 2026-09-02: all ten files byte-identical` … `Also on this disk: _yamaguchi_frozen_20260826/ -- a FROZEN, self-contained Duplicati destination (811 volumes, AES). Do NOT delete it as stale: it is the only copy of restore point 20260826T181206Z`.

(`~/.local/state/yamaguchi-old-archive-dlists/` does hold the ten `.gpg` dlists.)

## 7. Dropbox

```
2948130 /home/pcalnon/.dropbox-dist/dropbox-lnx.x86_64-270.4.3312/dropbox  (2949543 [dropbox] <defunct>)
dropbox status: Up to date        version: daemon 270.4.3312 / CLI 2026.05.06
exclude list: Apps, Camera Uploads, Data, Mobile Uploads, Operations, Photos, Public, Screenshots, Sent files   (Backups is NOT excluded)
info.json: {'personal': '/mnt/Backups/Ubuntu/Dropbox'}
filestatus: …/Backups/Yamaguchi: up to date ; …/Backups: up to date ; the 09-18 dlist and 4 newest files: up to date
```

`/mnt/Backups/Ubuntu/Dropbox` **is the Dropbox root** (info.json path; `.dropbox` and `.dropbox.cache` live there; `~/Dropbox` does not exist), so `Backups/Yamaguchi` is a synced subfolder — the 203 GB set is going to the cloud. Group question: the daemon's `Groups:` lacks 139, so a file `duplicati:duplicati 770` is **unreadable** to it (owner ≠ 1000, not in group, no other-bits). Today that is moot — all 877 files are `pcalnon:duplicati`. A file the new server writes would be `duplicati:duplicati` with mode governed by the service `UMask=0022` (process `Umask: 0022`) → `0644` unless Duplicati tightens it; `0644` would be readable via the other-bits. Oddity: `/mnt/Backups/Ubuntu/.dropbox-dist/` is owned `duplicati:duplicati` (09-14); the running daemon is from `~/.dropbox-dist`.

## 8. `.env` shape

`-rw-rw---- 1 duplicati duplicati 1599 2026-09-20 16:39:43 /home/duplicati/.config/Duplicati/.env`. Plain `cat` → `Permission denied` (rc=1) because my process lacks gid 139 (§1); `sg duplicati -c cat` succeeded. Shape (values never read into output):

```
lines 1-14: comments (a bash shebang-style header block; lengths 19,246,1,77,1,246,8,1,115,1,74,142,1,246)
line 15: blank ; lines 16-21: comments (22,56,52,68,68,68)
line 22: assign  export SETTINGS_ENCRYPTION_KEY   len 32  quoted single  has= no  specials $,@,&,#
total lines: 22; ends with newline: True
```

The 32-char value also contains `^` (seen only as a character class in the 16:41 bash error echo; `^` was not in the analyzer's probe set). Its length (32) and punctuation set differ from the 36-char literal in the wrapper header (§5) — **they are not the same string**.

## 9. Database forensics (scratch copies, `mode=ro`)

| | (a) `~pcalnon/.config/Duplicati/Duplicati-server.sqlite` | (b) LIVE `~duplicati/.config/Duplicati/…sqlite` (copied 03:04:34) | (c) `temp1/` | (d) `…/Duplicati-server.backup` | (e) root snapshot `~/.local/state/duplicati-server-db/…sqlite` (from `/usr/lib/duplicati/data`, 09-20 08:45) |
|---|---|---|---|---|---|
| sizes | 4096 / wal 112587272 / shm 32768 | 4096 / wal 370832 / shm 32768 | **not copied**: `cp: cannot open … Permission denied` (0600 duplicati, also under `sg`) | 479232, no wal/shm | 245760, no wal/shm |
| header | page 4096, bytes18/19 = 2/2 (WAL), change_counter 1, **page_count 1**, schema_cookie 0 (an EMPTY main file) | identical bytes to (a) (`sha256 352a9bb2…`) | — | page 4096, 2/2, change_counter 4254, page_count 117, schema_cookie 20 | page 4096, **1/1** (rollback journal, `journal_mode=delete`), page_count 60 |
| WAL header | magic 0x377f0682, ver 3007000, page 4096, ckpt_seq **0**, salt1 0xc6552d1f, salt2 0x69ed4ebf, **frames 27327**, remainder 0 | magic 0x377f0682, ckpt_seq 0, salt1 0x0cd60a99, salt2 0x6d70864b, frames 90 | — | — | — |
| quick_check / user_version | ok / 0 | ok / 0 | — | ok / 0 | ok / 0 |
| tables | **20: Block, BlocklistHash, Blockset, BlocksetEntry, ChangeJournalData, Configuration, DeletedBlock, DuplicateBlock, File, FileLookup, Fileset, FilesetEntry, IndexBlockLink, LogData, Metadataset, Operation, PathPrefix, RemoteOperation, Remotevolume, Version** | 16: Backup, BackupTargetUrl, ConnectionString, ErrorLog, Filter, Log, Metadata, Notification, Option, Schedule, Source, TempFile, TokenFamily, UIStorage, Version, sqlite_sequence | — | same 16 as (b) | same 16 as (b) |
| `Version` | `[(1, 19)]` | `[(1, 12)]` | — | `[(1, 11)]` | `[(1, 11)]` |
| `Backup` rows | **table absent** (this is a per-job LOCAL database, not a server database) | **0** | — | 2: `ID 2 'Ubuntu' DBPath /home/pcalnon/.config/Duplicati/SJTCQIIZSJ.sqlite`; `ID 3 'Ubuntu-fresh' DBPath …/DQRVQNDIFX.sqlite`; TargetURL both `enc-v1:<hex ciphertext>` | — | **1: `ID 2 'Yamaguchi' DBPath /usr/lib/duplicati/data/BMXWPAOGLP.sqlite`, TargetURL `enc-v1:<hex ciphertext>`** |
| `Schedule` | absent | 0 rows | — | 0 rows | 1: `(1, 'ID=2', 1789740000, '1D', 1789740000, 'AllowedWeekDays=Monday,…,Sunday')` = Time and LastRun both **2026-09-18T14:00:00Z** |
| `Metadata` | absent | 0 | — | backup 2: BackupListCount 21, LastBackupDate 20260709T142349Z, LastErrorDate 20260825T071946Z `A task was canceled.`, SourceSize 1.288 TB, TargetSize 3.384 TB | backup 2: **BackupListCount 9, LastBackupDate 20260918T140000Z, LastBackupFinished 20260918T141256Z, LastBackupDuration 00:12:56, SourceSizeString 290.610 GiB, TargetSizeString 202.806 GiB**, LastErrorDate 20260916T140106Z `Found 6 remote files that are not recorded in local storage…` |
| `Option` (count; names only) | absent | 52, all BackupID −2 server settings incl. `server-passphrase`, `server-passphrase-salt`, `jwt-config`, `pbkdf-config`, `encrypted-fields` | — | 66 incl. job 2/3: `passphrase`, `encryption-module`, `dblock-size`, `--no-auto-compact` (3) | 58 incl. job 2: `passphrase`, `encryption-module`, `dblock-size`, `retention-policy`, `--blocksize`, `--no-auto-compact`, `--tempdir`, `--asynchronous-upload-limit`, `--allow-missing-source`; global `--disable-on-battery`, `--restore-permissions` |
| `Filter` | absent | 0 | — | 80 (`%HOME%/…` form, jobs 2 and 3) | 45 for job 2 (`/home/pcalnon/…` absolute; #41 `/home/pcalnon/.config/Duplicati/`, #43 `/home/pcalnon/.config/duplicati-backup/`, #44 `/home/pcalnon/Dropbox-OLD/`) |
| `Source` | absent | 0 | — | `(2,'%HOME%'), (3,'%HOME%')` | `(2,'/home/pcalnon/'), (2,'/home/pcalnon/VirtualMachines/VirtualBox/win10_vm_2023-04-29/win10_vm_2023-04-29.vdi')` |
| `Log` / `ErrorLog` | absent | Log 0; **ErrorLog 4: `Failed to import backup` at 1789947585/…759/…767 = 2026-09-20 18:39:45, 18:42:39, 18:42:47 CDT** | — | Log 0; ErrorLog 28, newest 1787642386 (08-25 02:19:46) `Failed while executing Verify "Ubuntu" (id: 2)` | Log 0; ErrorLog 20, newest 1789567266 (09-16 09:01:06) `Failed while executing Backup "Yamaguchi" (id: 2)` |
| `Notification` | absent | 0 | — | 1: `Error while running Ubuntu` / `A task was canceled.` | 0 |

`temp/Duplicati-server.sqlite-wal`: `head: cannot open … Permission denied` both plain and under `sg` (0600, dir root 755). The `.backup` in pcalnon's dir is byte-identical to (d).

## 10. Other observations bearing on "no backups defined, yet the config dir matches `~pcalnon/.config/Duplicati`"

Observations (O) kept apart from inferences (I; each with the single observation that would refute it):

- **O**: the two 4096-byte `Duplicati-server.sqlite` files are byte-identical, empty (1 page, schema cookie 0). All of pcalnon's DB content lives in a never-checkpointed WAL (ckpt_seq 0, 27327 frames, last written 2026-08-25 02:20:46) whose applied view is a **local** (per-job) schema at version 19 — no `Backup` table exists to copy. The TrayIcon crashlog (`The database has version 19 but the largest supported version is 11 … folder /home/pcalnon/.config/Duplicati`) and the 18:02/18:12 `…is 12` loops are the same file being read by 2.3.0.4 and 2.4.0.0 respectively.
- **O**: `/etc/default/duplicati` lost `--portable-mode` (journal: last echoed 09-20 13:32:46, absent 13:36:37; file mtime 16:39:58). `/usr/lib/duplicati/data` was born 2026-08-25 02:38:43 and is where the snapshot unit found a 16-table, 240 KiB server DB through 09-20 08:45:01.
- **O**: `dpkg.log`: `2025-08-31 install duplicati 2.1.0.5`; `2026-09-19 21:29:28 upgrade duplicati 2.3.0.4 2.4.0.0`; `21:35:03 upgrade 2.4.0.0 2.4.0.0`. Unpacked files (`duplicati-server`, `Duplicati.Server.dll`) are `root:root`; directories `duplicati:duplicati` (an earlier `chown -R` that the reinstall partially undid).
- **O**: the live data dir and every DB file in it are mode **777** (ctimes 18:25:47 / 18:33:45 on 09-20); `/home/duplicati/bin` and the symlink 777; `/etc/default/duplicati` owned by the service user.
- **O**: `SETTINGS_ENCRYPTION_KEY` material is present in the system journal in four forms (§4 counts) and a 36-char key literal is committed to the public-remote repo in the wrapper header (§5). The two candidate keys differ (36 vs 32 chars).
- **O**: (d) and (e) both use `ID 2` (`Ubuntu` vs `Yamaguchi`); the watchdog hardcodes `--backup-id 2`.
- **I-1** The server on :8300 has no jobs because at 18:19:42 it opened an empty 1-page main file whose WAL had been moved (as root) into `temp/` between 18:18:49 and 18:19:26, and so initialised a fresh v12 schema (WAL born 18:19:43.917, 90 frames, 0 `Backup` rows). *Refuter*: the (b) WAL copy containing `Backup` rows — it contains none.
- **I-2** Even with that WAL in place the copy could never have produced the Yamaguchi job: `~pcalnon/.config/Duplicati/` holds only a misfiled local DB (v19) and a v11 `.backup` naming `Ubuntu`/`Ubuntu-fresh`. The Yamaguchi definition exists in `/usr/lib/duplicati/data/Duplicati-server.sqlite` (last independently seen 09-20 08:45:01) and, consistently, in `~/.local/state/duplicati-server-db/Duplicati-server.sqlite` (quick_check ok). *Refuter*: root finding that file absent or of a different size than 240 KiB.
- **I-3** Removing `--portable-mode` is what redirected the data folder from `/usr/lib/duplicati/data` to `~duplicati/.config/Duplicati` (Duplicati's portable mode selects `<exe dir>/data`). *Refuter*: a root `ls -la /usr/lib/duplicati/data/control_dir_v2/lock_v2` with mtime ≈ 18:19:45.
- **I-4** The real DB's sensitive fields have been encrypted with an *explicit* key since the 09-18 21:03:27 start (first start without the "no key" warning; followed by `Mismatch` when the key changed and `Missing` when it was removed), and that key is **not** the current `.env` key (16:44 on 09-20 produced `Mismatch` with the `.env` key against a DB created under the unit-supplied key). Whether it equals the committed 36-char literal is undetermined. *Refuter*: the server opening `/usr/lib/duplicati/data` under the `.env` key without `SettingsEncryptionKeyMismatchException`.
- **I-5** The on-disk unit (01:44:57) and the currently deployed wrapper (03:04:40 = HEAD, no `--daemon-opts` parsing) are mutually inconsistent; the next `daemon-reload` + restart would hand `duplicati-server` the single argument `--daemon-opts="--webservice-port=8300"` and lose the port (the 09-19 8200 listeners show what "port not passed" looks like). *Refuter*: the wrapper changing again before that restart (it is being edited live), or a restart that logs `listening on localhost, port 8300`.
- **I-6** The watchdog's 401 today is the new empty server's own `server-passphrase`, not a network problem. *Refuter*: the repo credential logging in successfully.
- **I-7** If the real DB is put back in front of the server, the schedule row (`Time` = 2026-09-18T14:00Z, in the past) will fire immediately. *Refuter*: Duplicati advancing `Time` without running.

## Reconstructed timeline (2026-09-18 → now; timestamp kind in brackets)

- **09-18** 19:25–19:53 group/user `duplicati` created, pcalnon added [journal]; 19:31:40 `/home/duplicati` [birth]; 19:57:16 the 1d18h server (no key, `/usr/lib/duplicati/data`) stopped [journal]; 19:57–20:02 ten crashes `installation.txt denied` [journal]; 20:10:00 `sudo -u duplicati vim /usr/lib/duplicati/data/installation.txt` [journal]; 20:14 `sudo su -` [journal]; 20:22:11 UP (no key) [journal], 20:22:12 `~duplicati/.aspnet/DataProtection-Keys` [birth]; 20:36:53/20:37:41 `/mnt/Backups`, `/Ubuntu` regrouped [ctime]; 20:42:37 UP (no key) [journal]; 20:45:32 `~/.config/duplicati-backup/env` edited [mtime]; 20:46:19 `~duplicati/.config` [birth]; **21:03:27 UP with a key** [journal]; 21:03:34 entry change in `/usr/lib/duplicati/data` [mtime]; 21:07:35 stop; 21:08–21:11 `Mismatch` ×15; 21:16–21:23 `Missing` ×19 [journal].
- **09-19** 16:32:33 `~duplicati/bin` [birth]; 17:36:46–17:37:24 the whole `Dropbox/Backups` tree regrouped `pcalnon:duplicati 770` (874+811 files) [ctime]; 17:43:06 `sudo su -` [journal] → root shell that still owns the two open `su - duplicati` sessions (18:24:51, 18:52:00) [journal, ps]; 17:46:52 shell → bash [journal]; 18:34:43 `Duplicati-OLE` [birth]; 18:40:11–18:42:22 `~duplicati/.config/Duplicati` populated from pcalnon's dir [birth]; 19:14:58–19:15:01 `Missing` ×4 [journal]; 19:15:00 `/usr/lib/duplicati/data` chowned `duplicati` [ctime]; 19:19–20:44 wrapper syntax error ×20 [journal]; 20:48, 21:41–21:55 `Duplicati-server.sqlite … denied` ×25 [journal]; 21:20:37–21:23:02 UP on 8200 [journal]; 21:20:55–56 pcalnon TrayIcon (2.3.0.4) crash on the v19 file [crashlog mtime, sqlite ctime]; 21:21:41 `Duplicati-OLE` written [mtime]; 21:29:28 apt 2.3.0.4→2.4.0.0, 21:35:03 reinstall [dpkg.log]; 21:55:18–21:56:55 the copied DB set renamed into `backups/*-backup` [filenames, dir mtime]; 21:57:35 UP on 8200 [journal]; 21:57:36 new `Duplicati-server.sqlite` inode [birth].
- **09-20** 04:06:07 stop [journal]; 04:15:42 `installation.txt` [birth]; 04:41:07 `.backup` copied in, 04:43:02 `-shm` copied in, `.sqlite` overwritten in place [birth/mtime]; **08:45:01 last successful root snapshot of `/usr/lib/duplicati/data/Duplicati-server.sqlite`** [journal, mtime]; 12:00:39 watchdog UNREACHABLE [journal]; 12:55:54/12:56:10 entry churn in `Backups/`, `Yamaguchi/` [dir mtime]; 13:00:41 entry churn in `~duplicati/.config` [mtime]; 13:32:33 `.env` missing ×5, 13:32:46 UP 8200, 13:36:37 UP 8300 without portable-mode [journal]; **16:39:43 `.env` created, 16:39:58 `/etc/default/duplicati` written** [birth/mtime]; 16:41 export bug (value echoed) ×5, 16:44 `Mismatch` ×5, 16:50:12 UP [journal]; 16:53:58 wrapper symlink [birth]; 17:26:27 / 17:59:22 PRs #1967/#1968 [git]; 17:30:14 UP with DEBUG echoes [journal]; **17:57:56 112 MB WAL copied in** [birth]; 18:02:54 `version 19` ×5 [journal]; 18:05:05 `temp1/`, 18:08:41 five files copied there [birth]; 18:12:25 `version 19` ×5 [journal]; **18:18:49 root `temp/`, ≤18:19:26 WAL moved into it** [birth, dir mtime]; **18:19:42 current server starts; 18:19:43.917 new WAL; 18:19:45 lock; 18:19:46 listening** [journal, birth, mtime]; 18:25:47 / 18:33:45 chmod 777 [ctime]; 18:39:45–18:42:47 `Failed to import backup` ×4 [ErrorLog]; 18:47:44 UI browse of `/media/pcalnon` denied [journal]; 19:07:38 user-lane runner run as duplicati → refused [journal, birth].
- **09-21** 01:41:41 root `vim` on the unit file opens [ps]; 01:44:57 unit rewritten (`NeedDaemonReload=yes`) [mtime]; 02:15:30 wrapper edited (218 lines) [mtime, observed 03:02]; 02:52:01 watchdog → 401 [journal]; 03:04:40 wrapper reverted to HEAD (199 lines) [mtime, observed 03:13].

## What could not be verified without root (command a root operator should run)

1. Is the Yamaguchi server DB still in place, and is it what the live server ignores? `ls -la --time-style=full-iso /usr/lib/duplicati/data/ /usr/lib/duplicati/data/control_dir_v2/` and `sha256sum /usr/lib/duplicati/data/Duplicati-server.sqlite /home/pcalnon/.local/state/duplicati-server-db/Duplicati-server.sqlite`; confirm `BMXWPAOGLP.sqlite` exists and its size (avoids a full Recreate).
2. Which folder the running server actually holds open: `ls -l /proc/1397393/fd | grep -iE 'sqlite|lock'` and `readlink /proc/1397393/cwd`.
3. Whether the running server got a key from the environment (name/count only): `tr '\0' '\n' < /proc/1397393/environ | grep -c '^SETTINGS_ENCRYPTION_KEY='`.
4. Identity of the moved WAL: `sha256sum /home/duplicati/.config/Duplicati/temp/Duplicati-server.sqlite-wal` (expected to equal pcalnon's `488c3223…` if it is the same 112 MB local-DB WAL) and `ls -la /home/duplicati/.config/Duplicati/temp1/ /home/duplicati/.config/Duplicati-OLE/ /home/duplicati/.cache/`.
5. Why the four imports failed: on a *copy* of the live DB, `sqlite3 -readonly copy.sqlite "SELECT Timestamp, Message, substr(Exception,1,400) FROM ErrorLog ORDER BY Timestamp DESC LIMIT 4"`.
6. What overwrote pcalnon's server DB with a local schema on 2026-08-25 02:19:48: on a copy of `~pcalnon/.config/Duplicati/Duplicati-server.sqlite`(+wal), `SELECT ID, Description, Timestamp FROM Operation` (I did not query `Operation`; it is outside the allowed list).
7. Key lineage: the operator's own shell history — `/root/.bash_history` and `/home/duplicati/.bash_history` (310 B, 09-19 18:00–18:51) — records the `chown`/`mv`/`cp`/key edits that the sudo log cannot see.
8. The job's `--tempdir` value (an `Option` value, not read here): if it points under `/media/pcalnon/temp_backups` (no longer a mountpoint), the next run fails.

<!-- markdownlint-enable -->

---

## Report 2b — Static and behavioural analysis of the new Duplicati systemd wrapper lane, plus deployment drift

Subagent id `a4e2d16232cb9d787` (42,465 characters).

<!-- markdownlint-disable -->

# Duplicati systemd wrapper lane — static + behavioural analysis

**Scope.** `scripts/duplicati-wrapper.bash` at worktree HEAD `52571621` (PR #1968), compared against GitHub `main` `d721fc78` (PR #1969, merged 08:07Z today, which changed the same file) and against the primary checkout that the live symlink resolves to. Everything below was done read-only, with synthetic inputs only; the real `.env`, `/etc/default/duplicati`, systemd, the journal and processes were never read or probed. Line numbers are the **worktree** copy unless prefixed `M:` (main; `M = W+19` for `W>=107`, `M:109–123` is the new `--daemon-opts` block). Raw transcripts are saved under `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/227cf645-dd93-4802-91f7-23dcaa92c971/scratchpad/agent4-static/` (`results.txt`, `results_extra.txt`, `results_extra2.txt`, `results_main.txt`, `shellcheck.txt`).

## Headline findings

1. **`scripts/duplicati-wrapper.bash:49` carries a credential-shaped literal in a PUBLIC repository** (`gh repo view`: `"isPrivate":false,"visibility":"PUBLIC"`). Present in PR #1967's diff, on `main` right now (line 49 of `d721fc78`), and in 5 commits. Shape only: 36 chars, unquoted, 12 upper / 14 lower / 5 digits / 5 non-alphanumerics from the set `$ % * @`; not base64, not hex, not a placeholder pattern. Gitleaks (`Security Scan`) passed on both PRs; GitHub secret-scanning alerts: `[]`. **Critical.**
2. **The `.env` parser is `eval`-based command execution** (W:134–135 / M:153–154). `TEST_SEMI=a;echo INJECTED` printed `INJECTED`; `$(…)` and backticks execute; a key named `DUPLICATI_SERVER` in the `.env` redirects the `exec` target (`ARGV[0]=</tmp/not-duplicati>`). The `.env` lives in a **0777 directory** (`/home/duplicati/.config/Duplicati`), so any local user can unlink/replace it. **Critical.**
3. **The on-disk unit and the wrapper on `main` are mutually incompatible.** The on-disk `ExecStart=… '--daemon-opts="${DAEMON_OPTS}"'` delivers ONE argv element `--daemon-opts="--webservice-port=8300"`; main's wrapper turns that into `ARGV[1]=< "--webservice-port >` (no port, stray quote, leading space); the worktree wrapper turns it into `ARGV[1]=<--daemon-opts="--webservice-port=8300" >` and **suppresses** both the env-derived and default port. The service only works while the previously loaded unit (`${DAEMON_OPTS}` bare) is still in memory; the next `daemon-reload`/reboot brings Duplicati up with no port option. **Critical (availability).**
4. **`exec "${DUPLICATI_SERVER}" "${DUPLICATI_OPTS}"` (W:199 / M:218) always passes exactly one argv element** containing every option plus a trailing space; two options can never be delivered as two arguments through this wrapper, whatever the unit does. **High.**
5. **The live ExecStart is a symlink into the owner's git working tree** (`/home/duplicati/bin/duplicati-wrapper.bash -> /home/pcalnon/Development/python/Juniper/juniper-ml/scripts/duplicati-wrapper.bash`, directory `/home/duplicati/bin` is `drwxrwxrwx`). The target's content changed three times between 02:15 and 03:14 local today (uncommitted → HEAD → main). **High.**
6. **The vendor unit was edited in place** (`dpkg` md5 `e989e07f…` vs on-disk `9fe951a5…`, not a conffile) — the next `duplicati` package upgrade silently restores `ExecStart=/usr/bin/duplicati-server $DAEMON_OPTS` and drops the wrapper (and with it the `.env`-sourced settings key). **High.**
7. **`util/ad-hoc/yamaguchi_server_db_snapshot.py:52` still snapshots `/usr/lib/duplicati/data/Duplicati-server.sqlite`** while the migrated server's DB is at `/home/duplicati/.config/Duplicati/Duplicati-server.sqlite`; its 0700 pcalnon-owned destination (`:105–107`, `:139`) is unreadable by a `duplicati`-user server, so the snapshot cannot ride along in the backup either way. The identical unit is installed under `/etc/systemd/system/`. **High.**

---

## 1. Provenance

| Item | Evidence |
|---|---|
| PR #1967 | `feat(duplicati): add duplicati-wrapper.bash script for Duplicati serv…`, author `pcalnon`, merged `2026-09-20T22:26:28Z`, files: `scripts/duplicati-wrapper.bash +210/-0`. Body: one LLM-style paragraph + the **unfilled** PR template (Summary/Requirements/Test plan placeholders left verbatim, incl. the `_e.g._ Closes JR-CAS-WS-014` example line). |
| PR #1968 | `Feat/duplicati wrapper script for systemd unit`, merged `2026-09-20T22:59:23Z` (33 min later), `scripts/duplicati-wrapper.bash +56/-67`. Body: template only, no summary, no test plan. |
| PR #1969 (follow-up, touches the file under review) | `feat(backup): add backup tests script and documentation for duplicati…`, merged `2026-09-21T08:07:48Z`; files `notes/backup_tests_pre-and-post_reboot.md +0/-0` (629 B), `prompts/manual/prompt132_2026-09-21.md +65/-0`, `scripts/duplicati-wrapper.bash +32/-13`. The body describes "a new script for backup tests that securely prints and shreds the key escrow sheet" — **no such script is in the diff** (title/body vs diff disagree; believe the diff). The notes filename does not follow the `JUNIPER_<date>_JUNIPER-<REPO>_…` convention (filename only observed; not read). |
| `git log -- scripts/duplicati-wrapper.bash` (worktree) | `52571621 2026-09-20 17:59:22 -0500 Feat/duplicati wrapper script for systemd unit (#1968)`; `6708cb28 2026-09-20 17:26:27 -0500 feat(duplicati): add … (#1967)`. `git log --all -S'SETTINGS_ENCRYPTION_KEY='` additionally finds pre-squash commits `b4aeed52` and `60d1c45d` on `feat/duplicati-wrapper-script-for-systemd-unit` (local + `origin`). |
| Repo visibility | `{"isPrivate":false,"url":"https://github.com/pcalnon/juniper-ml","visibility":"PUBLIC"}` |
| CI on #1967/#1968 | All 21 checks `pass` including `Security Scan` (gitleaks-action v3.0.0 with `.gitleaks.toml`), `Pre-commit (3.12/3.13/3.14)`, `CodeQL`. |
| Primary vs worktree `diff` | At my first probe the primary (`12863 B`, mtime `02:15`) already held the `--daemon-opts` revision, uncommitted; at `03:04:40` it was byte-identical to HEAD `52571621` (`7f5db338…`); at `03:13:57` it became identical to main `d721fc78` (`09018fba…`, 218 lines). `diff worktree main` = the block shown in §3(c)/§4 (arrays initialised as `()`, new `DAEMON_OPTS_SWITCH` parsing, removal of the `if [[ "${DAEMON_OPTS}" != "" ]]` block). `diff primary main` exit 0 now. |
| Live symlink | `lrwxrwxrwx duplicati duplicati /home/duplicati/bin/duplicati-wrapper.bash -> /home/pcalnon/Development/python/Juniper/juniper-ml/scripts/duplicati-wrapper.bash`; `/home/duplicati/bin` is `drwxrwxrwx`; `namei -l` shows every path component traversable (`/home/pcalnon` 755, file `-rwxrwxr-x pcalnon pcalnon`). |

**Findings**

- `scripts/duplicati-wrapper.bash:49` — credential-shaped literal inside the "Old Unit file" comment (`Environment=SETTINGS_ENCRYPTION_KEY=<36 chars>`), public since `2026-09-20T22:26Z`, still on `main` — evidence: `gh pr diff 1967 | grep -c 'SETTINGS_ENCRYPTION_KEY='` = 1; `gh api …/contents/…?ref=d721fc78 | grep -n` = `line 49`; `git grep -l` finds no other tracked file (notes/prompts excluded) — **critical** — treat as compromised: rotate the Duplicati settings-encryption key (re-encrypt the server DB), strip the line, rewrite history on `main` + the feature branch, request GitHub cache purge, add a gitleaks rule for `SETTINGS_ENCRYPTION_KEY=|--settings-encryption-key=`.
- `.gitleaks.toml:38–41` — allowlist is fine; the miss is most plausibly the generic-api-key rule's value charset (the literal contains `$%*@`) — **medium** (inference, see cannot-establish) — add an explicit rule.
- `/home/duplicati/bin` (0777) and the symlink into the owner's working tree — any process running as pcalnon (every Claude session, `git checkout/stash/pull`) rewrites the code that runs as `duplicati`; any local user can replace the symlink — **high** — `install -o root -g root -m 0755` a copy under `/usr/local/lib/duplicati/` and point `ExecStart` there; `chmod 0755 /home/duplicati/bin`.

## 2. Lint (raw)

```
/usr/bin/shellcheck -> version: 0.11.0
~/.cache/pre-commit/repowbna9euw/py_env-python3.14/bin/shellcheck (pinned v0.10.0.1 hook) -> version: 0.10.0
shellcheck -S style -f gcc scripts/duplicati-wrapper.bash          (no output) rc=0
shellcheck --severity=warning -f gcc  (repo hook args, .pre-commit-config.yaml:213-220)   (no output) rc=0
pinned 0.10.0 --severity=warning                                   (no output) rc=0
shellcheck -f json scripts/duplicati-wrapper.bash                  []
sanity probe (file containing `echo $foo`):
  sc_probe.sh:2:6: warning: foo is referenced but not assigned. [SC2154]
  sc_probe.sh:2:6: note: Double quote to prevent globbing and word splitting. [SC2086]   rc=1
shellcheck -o all (optional checks, worktree):
  scripts/duplicati-wrapper.bash:104:8: warning: DAEMON_OPTS is referenced but not assigned. [SC2154]
  17 x note SC2312 (masked return value in $(...)) at 113:56 113:102 118:35 121:35 130:47 131:32 135:108 135:114 157:49 160:41 168:49 171:41 179:49 182:41 187:37 196:72 196:78
shellcheck -o all (main d721fc78): SC2250 at 114:71 (+ SC2312 notes)
bash -n worktree: exit 0 ; bash -n primary/main: exit 0 ; bash 5.x ; file: 0 CR bytes, 0 trailing-space lines
```

Finding: **shellcheck is clean at every severity on both revisions while the script contains eval injection and a single-argv exec** — the repo's `--severity=warning` gate cannot see this class — **medium** — add a `bash`-semantics test (the harness in §4 is a starting point) rather than relying on the linter.

## 3. Semantics review (by reading)

**(a) `${*}` / `DAEMON_OPTS` parsing — W:100–106 / M:107–124.** `DUPLICATI_INPUT_PARAMS=("${*}")` (W:102) is a one-element array holding all positional parameters joined with the first character of `IFS` (a space) — never many elements (case x-g: two argv elements became `ARGV[1]=<--webservice-port=8300 --webservice-interface=loopback >`). In the worktree, W:91–93 initialise the arrays as **scalars** (`""`), so when no argv/no `DAEMON_OPTS` is given, `"${DUPLICATI_INPUT_PARAMS[@]}"` at W:154 yields one empty element, `grep -- ""` matches the empty `DUPLICATI_OPTS`, and a bare space is appended: `ARGV[1]=< --webservice-port=8300 >` (leading space). Main fixes the initialisation (`()`, M:97–99) but its `--daemon-opts` extraction (M:113 `cut -d '=' -f 2`) yields `"--webservice-port` for `--daemon-opts="--webservice-port=8300"`, and M:114 `"${DUPLICATI_INPUT_PARAMS[@]/$PARAM}"` blanks the element instead of removing it (re-introducing the leading space). Main also **deletes** the `if [[ "${DAEMON_OPTS}" != "" ]]` block, so the `DAEMON_OPTS` environment variable is no longer consulted at all (M-x-d: env `--webservice-port=8300 --webservice-interface=loopback` → `ARGV[1]=<--webservice-port=8300 >`, interface option gone). **High.**

**(b) `.env` parser — W:107–148 / M:126–167.**
- W:122/124 `cut -d '=' -f 1|2`: value truncated at the **second** `=` — `TEST_EQ=abc=def==` → `TEST_EQ=abc`; `--log-file=/tmp/a=b.log` → `--log-file=/tmp/a`. **Medium.**
- W:134–135 `eval "export KEY=VALUE"` on an unquoted value: `$` expands (`ab$HOME$1cd` → `ab/FAKEHOMEcd`; `$1` reads the script's argv), spaces word-split (`hello world` → `hello`, and a variable literally named `world` is marked for export), `;` runs a command (`INJECTED` printed), `$(…)`/backticks run, a value such as `$(cat)` consumes the rest of the `.env` from the loop's stdin (`TEST_STDIN=TEST_NEVER=1`), unbalanced quotes abort that line with `eval: line 135: unexpected EOF` and the variable is silently not set; `a*b` survives only because bash treats `export NAME=…` as an assignment word (no globbing) — under `bash --posix`/`sh` it would glob. **Critical.**
- W:131 `env | grep "${KEY}"` — unanchored substring over `NAME=VALUE` lines: an inherited `TEST_PLAIN_OTHER=1` or `SOMEVAR=contains_TEST_PLAIN_here` suppresses `TEST_PLAIN` entirely; earlier exports feed later checks (`PATH=/usr/bin` then `ATH=1` → `ATH` never set; `PASSPHRASE_FILE=` before `PASSPHRASE=` would suppress the latter). **Medium.**
- W:118–119 `${line//export /}` strips the substring **anywhere**: `export TEST_MSG=do export it` → `TEST_MSG=do` (strip + word-split compound). `TEST_exporter=1` is unaffected (no trailing space). **Low.**
- CRLF: `read -r` keeps `\r` — `TEST_CRLF=abc^M`, `--log-level=Verbose^M` (an invalid log level reaches Duplicati). **Medium.**
- Last line without a trailing newline is never processed (`read` returns non-zero at EOF): `TEST_NONL=2` absent. **Medium.**
- Option lines (`--x=y`, W:130 `grep "^-"`): appended to argv, never exported; a trailing comment becomes part of the option (`--log-level=Verbose # comment`); a valueless `--portable-mode` is passed through (correct).
- Namespace collision: the `.env` is `eval`'d into the wrapper's own scope, so `DUPLICATI_SERVER=/tmp/not-duplicati` changes the exec target (`ARGV[0]=</tmp/not-duplicati>`), `DEBUG_MODE=0` switches debug printing on mid-run (secret printed four times afterwards), `DUPLICATI_PORT_DEFAULT=9999` changes the port. **High** (same trust boundary as the injection, but silent).

**(c) Dedupe — W:154–189 / M:173–208.** `grep -- "${KEY}"` against the accumulated string is an unanchored substring test. `--webservice-port-x=1` before `--webservice-port=8301` drops the second **and** suppresses the default at W:187 (`ARGV[1]=< --webservice-port-x=1 >`); `--log-file=…` then `--log=x` drops `--log`; the on-disk `--daemon-opts="--webservice-port=8300"` element contains `--webservice-port` as a substring, so the env-derived and default ports are both dropped (x-c). Precedence: the implementation is **first occurrence kept**, in the order argv → `DAEMON_OPTS` → `.env` → constant, which matches the header (W:26–30) as "highest first" (x-h: 8300 argv beat 8301 env and 8302 file). On main, tier 2 is reachable only through argv `--daemon-opts=` (broken by `cut`), so `/etc/default/duplicati` can influence the command only when systemd expands it into a bare option — indistinguishable from tier 1. **High.**

**(d) `exec "${DUPLICATI_SERVER}" "${DUPLICATI_OPTS}"` — W:199 / M:218.** argv is always two elements:

| Input | argv delivered to duplicati-server |
|---|---|
| one option (`--webservice-port=8300` via argv) | `[/usr/lib/duplicati/duplicati-server, "--webservice-port=8300 "]` (trailing space) |
| two options (any route) | `[…, "--webservice-port=8300 --webservice-interface=loopback "]` — one element |
| nothing (worktree) | `[…, " --webservice-port=8300 "]` — leading space, so the element does not start with `--` |

A parser that splits each argv element at the first `=` sees, for the two-option case, option `webservice-port` = `8300 --webservice-interface=loopback ` (the interface option is swallowed; the port fails integer parsing) — Duplicati's `CommandLineParser.ExtractOptions` behaves this way to my knowledge, but it was not executed here. **High** — use an array and `exec "${DUPLICATI_SERVER}" "${OPTS[@]}"`.

**(e) DEBUG line W:196 / M:215** prints `Settings Encryption Key: SETTINGS_ENCRYPTION_KEY=<value>` to stdout (journald); with DEBUG on, W:112, 116, 125, 133, 134, 135 print every `.env` value as well (four copies of the key in xv). Independently of DEBUG, **W:197 / M:216 unconditionally echoes the full option string**, so any secret supplied in option form (`--webservice-password=`, `--settings-encryption-key=`) lands in the journal every start (xvi) and in `/proc/<pid>/cmdline` (world-readable). **High** — drop the debug key print, redact W:197, and never accept secret-bearing options from the `.env` (pass them as env/credentials).

**(f) `TRUE=0/FALSE=1` and top-level `[[ … ]] && echo`.** With DEBUG off every such line leaves `$?=1`; no `set -e`, so no effect, and `exec` replaces the process so the script has no exit status of its own. `&&`-lists are exempt from `errexit`, so adding `set -e` later would not trip on them; but the `eval` failures in (b) would still not be fatal (they return non-zero from `eval` inside a plain command — `set -e` would then abort the whole start on a stray apostrophe). `TRUE`/`FALSE`/`DEBUG_MODE` are not `readonly` and are rewritable from the `.env` (xxvii). **Low.**

**(g) No `set -euo pipefail`; quoting; path choice.** Every failure mode observed (eval errors, truncated values, dropped options) ends with `exit=0` and the server starting misconfigured — no signal reaches systemd. Quoting is consistent (`"${var}"` everywhere), which is why shellcheck is silent; the defects are semantic. `/usr/lib/duplicati/duplicati-server` is the ELF apphost; `/usr/bin/duplicati-server -> ../lib/duplicati/duplicati-server` is the packaged public entry point (both 2.4.0.0). Same binary today; `/usr/bin` is the stable interface across package-layout changes and the form the vendor unit uses. **Low.**

**(h) Header claim W:12–30 ("contents of the .env file are parsed and all defined constants are exported").** Does not hold: an inherited variable is never overridden (viii: `TEST_PLAIN=preset` wins), a key that is a substring of any existing name or value is skipped, values are truncated at `=` and at spaces, CR is kept, the last line without a newline is dropped, quoted values with `=`/`'` fail silently, and option lines are not exported at all. The "already defined" branch means the `.env` **cannot** override anything systemd put in the environment (`Environment=`, `EnvironmentFile=`), so tier 3 can never beat tier 2 for environment variables — consistent with the header only if "precedence" is read as tier 2 > tier 3, which the header does say, but it means `.env` is a defaults file, not a config file. **Medium** — replace the parser with `set -a; . <file>; set +a` on a **trusted, root-owned** file, or a strict `KEY=VALUE` reader with no `eval`.

## 4. Behavioural tests (synthetic; exec-neutered copies; `env -i`)

Harness: copy of the wrapper with `DUPLICATI_SERVER` → `/nonexistent/duplicati-server`, `DUPLICATI_ENV_LOCAL` → `<scratch>/synthetic.env`, and the `exec` line replaced by an `ARGV[n]=<…>` / `OPTS=<…>` / `env | grep ^TEST_` printer (`0` exec lines remain; safety gates asserted no real path survives). Every run exited 0. Literal outputs (`cat -v`; `^M` = CR):

| # | Input (`.env` / env / argv) | Literal result | Verdict vs header intent |
|---|---|---|---|
| i | `TEST_PLAIN=abc` | `TEST_PLAIN=abc`; `ARGV[1]=< --webservice-port=8300 >` | PASS (note leading space) |
| ii | `TEST_EQ=abc=def==` | `TEST_EQ=abc` | FAIL (truncated at 2nd `=`) |
| iii | `TEST_DOLLAR=ab$HOME$1cd` | `TEST_DOLLAR=ab/FAKEHOMEcd` | FAIL (`$HOME`, `$1` expanded) |
| iii' | `TEST_DOLLARQ='ab$HOME$1cd'` | `TEST_DOLLARQ=ab$HOME$1cd` | PASS (only when quoted) |
| iv | `TEST_GLOB=a*b` (cwd has `axb`,`ayyb`), `TEST_AT=x@y%z` | `TEST_GLOB=a*b`, `TEST_AT=x@y%z` | PASS (bash assignment-word rule; not portable) |
| v | `TEST_SPACE=hello world` | `TEST_SPACE=hello` | FAIL |
| v' | `TEST_SPACEQ="hello world"` | `TEST_SPACEQ=hello world` | PASS |
| vi | `TEST_SEMI=a;echo INJECTED` | first output line `INJECTED`; `TEST_SEMI=a` | FAIL — **command injection** |
| vi' | `TEST_CS=$(echo INJECTED2)`, ``TEST_BT=`echo INJECTED3` `` | `TEST_CS=INJECTED2`, `TEST_BT=INJECTED3` | FAIL — command substitution executes |
| vii | `export TEST_EXPORTED=1`; `TEST_exporter=1`; `export TEST_MSG=do export it` | `TEST_EXPORTED=1`; `TEST_exporter=1`; `TEST_MSG=do` | PASS / PASS / FAIL |
| viii | env `TEST_PLAIN=preset`, file `TEST_PLAIN=abc` | `TEST_PLAIN=preset` | file does NOT override (by design per W:26–30, contradicts W:12 claim) |
| viii' | env `TEST_PLAIN_OTHER=1`, file `TEST_PLAIN=abc` | only `TEST_PLAIN_OTHER=1` | FAIL (substring suppression) |
| viii'' | env `SOMEVAR=contains_TEST_PLAIN_here` | no `TEST_*` exported | FAIL (key inside another value) |
| ix | `--log-level=Verbose`, `--webservice-interface=loopback`, `--portable-mode` | `ARGV[1]=< --log-level=Verbose --webservice-interface=loopback --portable-mode --webservice-port=8300 >` | pass-through OK, but one argv element |
| ix' | `--log-file=/tmp/a=b.log` | `--log-file=/tmp/a` | FAIL |
| x-a | env `DAEMON_OPTS=--webservice-port=8300` | `ARGV[1]=< --webservice-port=8300 >` | PASS (leading space) |
| x-b | argv `--webservice-port=8300` (loaded-unit form) | `ARGV[1]=<--webservice-port=8300 >` | PASS (trailing space) |
| x-c | argv `--daemon-opts="--webservice-port=8300"` (+env) — on-disk-unit form | `ARGV[1]=<--daemon-opts="--webservice-port=8300" >` — no port option at all | **FAIL** |
| x-d | env two options | `ARGV[1]=< --webservice-port=8300 --webservice-interface=loopback >` | FAIL (one element) |
| x-e | argv `'--webservice-port=8300 --webservice-interface=loopback'` | same string, one element | FAIL |
| x-f | argv `--daemon-opts="…two options…"` | `<--daemon-opts="--webservice-port=8300 --webservice-interface=loopback" >` | FAIL |
| x-g | argv `--webservice-port=8300` `--webservice-interface=loopback` (two elements, `$DAEMON_OPTS` form) | joined into one element | FAIL (`("${*}")`) |
| x-h | argv 8300 / env 8301 / file 8302 | `<--webservice-port=8300 >` | PASS (argv wins; first-kept) |
| x-i | nothing | `< --webservice-port=8300 >` | leading space |
| xi | `TEST_CRLF=abc\r\n`, `--log-level=Verbose\r\n` | `TEST_CRLF=abc^M`; `< --log-level=Verbose^M --webservice-port=8300 >` | FAIL |
| xii | `TEST_TC=abc # comment` | `TEST_TC=abc` | PASS by accident (`#` parsed as comment by eval) |
| xx | `--log-level=Verbose # comment` | `< --log-level=Verbose # comment --webservice-port=8300 >` | FAIL |
| xiii | `--webservice-port-x=1`, `--webservice-port=8301` | `< --webservice-port-x=1 >` (explicit AND default port dropped) | FAIL |
| xiii' | `--log-file=/tmp/d.log`, `--log=x` | `--log=x` dropped | FAIL |
| xiv | `TEST_EMPTY=`, blank, whitespace, `# comment`, `TEST_AFTER=1` | `TEST_EMPTY=`, `TEST_AFTER=1` | PASS |
| xv | DEBUG on, `SETTINGS_ENCRYPTION_KEY=SYNTHETIC-KEY-VALUE-123` | stdout contains `Exporting Environment Variable SETTINGS_ENCRYPTION_KEY=SYNTHETIC-KEY-VALUE-123`, `EXPORT_CMD: export SETTINGS_ENCRYPTION_KEY=…`, `Environment Variable: SETTINGS_ENCRYPTION_KEY=…`, `Settings Encryption Key: SETTINGS_ENCRYPTION_KEY=SYNTHETIC-KEY-VALUE-123` | FAIL (4 copies to journald) |
| xvi | DEBUG off, `--webservice-password=SYNTHETIC-UI-PW`, `--settings-encryption-key=SYNTHETIC-SEK` | `Executing Duplicati Server: "/nonexistent/duplicati-server  --webservice-password=SYNTHETIC-UI-PW --settings-encryption-key=SYNTHETIC-SEK --webservice-port=8300 "` | FAIL (secrets echoed unconditionally + on argv) |
| xvii | `TEST_QEQ="a=b"` | `eval: line 135: unexpected EOF while looking for matching '"'`; not exported; exit 0 | FAIL |
| xviii | `TEST_APOS=it's` | `eval: … matching '''`; not exported | FAIL |
| xix | leading space / tab before key | exported | PASS |
| xxi | last line `TEST_NONL=2` without newline | absent | FAIL |
| xxii | `TEST_STDIN=$(cat)` then `TEST_NEVER=1` | `TEST_STDIN=TEST_NEVER=1` | FAIL (eval consumed the file) |
| xxiii/xxiv | env `DAEMON_OPTS=` / argv `''` (unset-variable expansion) | `< --webservice-port=8300 >` | leading space |
| xxv | `PATH=/usr/bin`, `ATH=1` | `ATH` never exported | FAIL |
| xxvi | `DUPLICATI_SERVER=/tmp/not-duplicati` | `ARGV[0]=</tmp/not-duplicati>` | FAIL (exec target hijack) |
| xxvii | `DEBUG_MODE=0` then a key | debug output switches on; `Settings Encryption Key: SETTINGS_ENCRYPTION_KEY=SYNTHETIC-KEY-2` | FAIL |
| xxviii | `DUPLICATI_PORT_DEFAULT=9999` | `< --webservice-port=9999 >` | FAIL |

**Main `d721fc78` (the live revision)** — same results for i, ii, v, vi, viii, ix, x-b, x-g, x-h, xiii, xvi; differences: no leading space when argv is empty (`M-x-i: <--webservice-port=8300 >`); **env `DAEMON_OPTS` ignored** (`M-x-d: <--webservice-port=8300 >` — interface option lost, default substituted); on-disk unit form **`M-x-c: ARGV[1]=< "--webservice-port >`** (no port, stray quote, leading space; same with two options `M-x-f`); `--daemon-opts=""` → `< "" --webservice-port=8300 >`.

Raw `[[` sanity: `[[ ( $(true) != "" ) ]]` parses (rc=1), so W:113's unquoted substitutions are valid empty operands, not syntax errors.

## 5. systemd command-line semantics (`systemd 259.5`, `man systemd.service`)

Quoted from `COMMAND LINES`: *"Each command line is unquoted using the rules described in "Quoting" section in systemd.syntax(7). The first item becomes the command to execute, and the subsequent items the arguments."* — *"Basic environment variable substitution is supported. Use "${FOO}" as part of a word, or as a word of its own, on the command line, in which case it will be erased and replaced by the exact value of the environment variable (if any) including all whitespace it contains, always resulting in exactly a single argument. Use "$FOO" as a separate word on the command line, in which case it will be replaced by the value of the environment variable split at whitespace, resulting in zero or more arguments. For this type of expansion, quotes are respected when splitting into words, and afterwards removed."* — *"Variables whose value is not known at expansion time are treated as empty strings."* — and from `systemd.syntax` QUOTING: *"double quotes ("...") and single quotes ('...') may be used to wrap a whole item … in which case everything until the next matching quote becomes part of the same item. Quotes themselves are removed."*

| ExecStart form | argv the wrapper receives (with `DAEMON_OPTS="--webservice-port=8300"`) |
|---|---|
| **Loaded** (per `systemctl show`, as given): `…/duplicati-wrapper.bash ${DAEMON_OPTS}` | exactly one argument `--webservice-port=8300` (whitespace preserved; two options arrive as ONE element; unset → one empty argument) → harness x-b / x-e / xxiv |
| **On disk** (after `daemon-reload`): `…/duplicati-wrapper.bash '--daemon-opts="${DAEMON_OPTS}"'` | unquoting first yields the single item `--daemon-opts="${DAEMON_OPTS}"` (the inner double quotes are ordinary characters inside the single-quoted item); substitution then runs on that item, `${…}` "as part of a word", so the result is **one** argument `--daemon-opts="--webservice-port=8300"` with two literal `"` characters — systemd has no shell notion of "single quotes suppress expansion"; only the `:` executable prefix suppresses it. → harness x-c (worktree) / M-x-c (main), both broken. Empty `DAEMON_OPTS` → `--daemon-opts=""` → M-x-c3. |
| **Previously commented**: `…/duplicati-wrapper.bash "${DAEMON_OPTS}"` | identical to the loaded form: quotes removed, one argument with the exact value |
| **Vendor original**: `/usr/bin/duplicati-server $DAEMON_OPTS` | split at whitespace, zero or more arguments — the only form that delivers two options as two arguments, which the wrapper's `("${*}")` then re-joins (x-g) |

`EnvironmentFile=-/etc/default/duplicati` (`man systemd.exec`): *"The text file should contain newline-separated variable assignments. Empty lines, lines without an "=" separator, or lines starting with ";" or "#" will be ignored … an unquoted value after the "=" is parsed with the same backslash-escape rules as POSIX shell unquoted text, but unlike in a shell, interior whitespace is preserved and quotes after the first non-whitespace character are preserved … To make the file optional, prefix the path with "-", which causes all errors related to the file to be silently ignored … Settings from these files override settings made with Environment=."* So `DAEMON_OPTS="--webservice-port=8300"` (wrapper header W:33) is fine; but `$VAR`, `$(…)`, `export KEY=` (invalid variable name, dropped) and comments after a value are **not** shell-interpreted, and a missing/unreadable file is silent. The file is parsed by PID 1, not by the wrapper (W:76 `DUPLICATI_ENV_GLOBAL` is assigned and never used).

## 6. Unit-file hardening review — `/usr/lib/systemd/system/duplicati.service`

On disk (0644 root, 461 B, mtime `2026-09-21 01:44`): `[Unit] Description=Duplicati web-server / After=network.target` — `[Service] Nice=19 IOSchedulingClass=idle IOSchedulingPriority=7 User=duplicati Group=duplicati EnvironmentFile=-/etc/default/duplicati`, two commented ExecStart forms, `ExecStart=/home/duplicati/bin/duplicati-wrapper.bash '--daemon-opts="${DAEMON_OPTS}"'`, `Restart=always` — `[Install] WantedBy=multi-user.target`. Enabled via `/etc/systemd/system/multi-user.target.wants/duplicati.service -> /usr/lib/systemd/system/duplicati.service`; no `/etc/systemd/system/duplicati.service`, no `duplicati.service.d/`.

| Item | Finding | Evidence | Sev | Remedy |
|---|---|---|---|---|
| Vendor file edited in place | `dpkg -L duplicati` ships `/lib/systemd/system/duplicati.service` (merged-usr alias of the edited file) and it is **not** in `duplicati.conffiles` (only `/etc/default/duplicati` is); recorded md5 `e989e07f…` ≠ on-disk `9fe951a5…` | `/var/lib/dpkg/info/duplicati.{conffiles,md5sums}` | high | `systemctl edit duplicati` → `/etc/systemd/system/duplicati.service.d/override.conf` with `ExecStart=` (blank) + new `ExecStart=`, or a full copy in `/etc/systemd/system/` — `man systemd.unit`: *"Unit files found in directories listed earlier override files with the same name in directories lower in the list"* (`/etc/systemd/system` above `/usr/lib/systemd/system`); *"a "drop-in" directory foo.service.d/ may exist. All files with the suffix ".conf" … merged … parsed after the main unit file itself"* |
| `Restart=always` without `RestartSec`/`StartLimit*` | `DefaultRestartSec` 100 ms, `DefaultStartLimitIntervalSec=10s`, `DefaultStartLimitBurst=5` (`man systemd-system.conf`); a fast-failing wrapper hits the limit in ~0.5 s and *"units which … reach the start limit are not attempted to be restarted anymore"* — `always` is defeated | man text | medium | `RestartSec=5s`, `StartLimitIntervalSec=5min`, `StartLimitBurst=10` |
| Ordering vs `/mnt/Backups` | `After=network.target` only; `/mnt/Backups` is `/dev/sda1` ext4 from fstab (`defaults 0 1`, no `nofail`) so boot ordering happens to work via `local-fs.target`, but a manual start after an unmount, or a future `nofail`/automount, is unguarded | `findmnt`, `/etc/fstab:18` | medium | `RequiresMountsFor=/mnt/Backups /home/duplicati` (*"Automatically adds dependencies of type Requires= and After= for all mount units required to access the specified path"*) |
| `ProtectSystem`/`ProtectHome` | absent. Cannot be `ProtectHome=yes`/`read-only` today: the ExecStart target is under `/home/pcalnon` and the data folder under `/home/duplicati` (*"the directories /home/, /root, and /run/user are made inaccessible and empty"*) | man text; `namei -l` | medium | relocate script (root-owned, outside /home) and data (`StateDirectory=duplicati` → `/var/lib/duplicati`, `--server-datafolder=%S/duplicati`); then `ProtectSystem=strict`, `ProtectHome=yes`, `ReadWritePaths=/mnt/Backups`. Interim: `ProtectHome=tmpfs` + `BindPaths=/home/duplicati` + `BindReadOnlyPaths=<script dir>` |
| `ReadWritePaths` | none; with `ProtectSystem=strict` add `/mnt/Backups` (owner `pcalnon:duplicati` 0770 — group write suffices) and the tempdir | `ls -ld /mnt/Backups` | medium | as above |
| `NoNewPrivileges` | absent; Duplicati needs no setuid | — | low | `NoNewPrivileges=yes` |
| `PrivateTmp` vs `--tempdir` | `/tmp` is tmpfs here (the 2026-08-23 RAM-staging incident, `util/duplicati_scheduled_backup.bash:102–111`); `PrivateTmp=yes` would also delete in-flight volumes on stop. `/home/duplicati/.config/Duplicati/temp` is **root-owned `drwxr-xr-x`** — unwritable by the service user | `ls -la` | medium | `--tempdir` on a disk-backed dir owned by `duplicati`; then `PrivateTmp=yes` |
| `UMask` | default 0022; the data dir and all DB files are already **0777** (`Duplicati-server.sqlite -rwxrwxrwx`), `.env` is 0660 in a 0777 dir (deletable/replaceable by anyone) | `ls -la /home/duplicati/.config/Duplicati/` | high | `UMask=0077`; `chmod 0700` dir, `0600` files, `0600 .env` |
| `SupplementaryGroups` | `id duplicati` → groups `139(duplicati)` only; `/mnt/Backups` is group-`duplicati`, so writes work; **reading pcalnon's home as source** will silently skip anything not other-readable | `getent`, `namei` | medium | `SupplementaryGroups=pcalnon` only if files are group-readable; otherwise `AmbientCapabilities=CAP_DAC_READ_SEARCH` (still with `NoNewPrivileges=yes`) |
| `Environment=` for secrets | the old unit (W:40–57) carried the key in `Environment=`: `/usr/lib/systemd/system` is 0644 and *"Environment variables set for a unit are exposed to unprivileged clients via D-Bus IPC … Use LoadCredential=, LoadCredentialEncrypted= or SetCredentialEncrypted= … to pass data to unit processes securely"* (`man systemd.exec`). `EnvironmentFile=` avoids D-Bus exposure but still propagates to every child (gpg, run-scripts) | man text; `ls -l` | high | `LoadCredential=settings-key:/etc/credstore/duplicati-settings-key` (root 0600) → `$CREDENTIALS_DIRECTORY/settings-key` / `%d/settings-key`, readable only by `User=`. `SetCredential=` is explicitly *"not … for data that is supposed to be secret"*; `SetCredentialEncrypted=` (via `systemd-creds -p`) is acceptable inside a unit file |
| Can Duplicati consume `%d/…`? | not verifiable here (no docs fetched, binary not run). Verifiable design: the wrapper reads the credential file itself (`SETTINGS_ENCRYPTION_KEY="$(<"${CREDENTIALS_DIRECTORY}/settings-key")"; export …`) so the value exists only in the service's own environment; whether `duplicati-secret-tool` / `--secret-provider` (both shipped) can read it natively is a question for the owner | `dpkg -L` shows `/usr/bin/duplicati-secret-tool` | — | — |
| `/etc/default/duplicati` | conffile now owned **`duplicati:duplicati` 0644** (404 B, mtime `2026-09-20 16:39:58`; not read) — the service account can rewrite its own start options; anything secret in it is world-readable | `stat` | medium | `chown root:root`, `chmod 0644`, no secrets; or `0640 root:duplicati` |
| `duplicati` account | login shell `/bin/bash` for a system service user | `getent passwd` | low | `usermod -s /usr/sbin/nologin duplicati` |
| `Nice=19`/`IOSchedulingClass=idle` | a backup server at idle I/O class can starve under contention — but this is the vendor default | — | low | keep, or `best-effort`/7 as the user lane does |

## 7. Deployment drift — older lanes

Diffs (installed vs repo): `~/.config/systemd/user/{duplicati-backup.service,duplicati-backup.timer,duplicati-backup-failure.service,yamaguchi-watchdog.service,yamaguchi-watchdog.timer}` — **identical** (exit 0). `/etc/systemd/system/yamaguchi-server-db-snapshot.{service,timer}` (root, `Aug 30`) — **identical** to `util/systemd/`. `~/.local/bin/duplicati-backup-failure.bash` — identical. **`~/.local/bin/duplicati-scheduled-backup.bash` (regular file, `Aug 24`) is STALE** — it lacks the repo's 2026-08-29 rewrite of the DB-holder guard (`util/duplicati_scheduled_backup.bash:157–180`: one `find` over `/proc/*/fd` instead of a per-fd `readlink` loop that cost 59 s and *"silently matched nothing whenever DBPATH reached the database through a symlinked directory"*). The lane is described as disabled (`util/systemd/yamaguchi-server-db-snapshot.service:9–11`), so impact is latent — **medium**; re-`install` before any re-enable. `tests/test_duplicati_db_holder_guard.py:39` tests the repo copy, not the installed one.

Hardcoded assumptions and what the migration to a dedicated `duplicati` system user with data folder `/home/duplicati/.config/Duplicati` breaks:

| file:line | assumption | migration effect | sev |
|---|---|---|---|
| `util/ad-hoc/yamaguchi_server_db_snapshot.py:13,52` | server DB at `/usr/lib/duplicati/data/Duplicati-server.sqlite` | **BROKEN** — live DB is now `/home/duplicati/.config/Duplicati/Duplicati-server.sqlite` (present, WAL `Sep 20 18:42`); old dir still exists (`drwx------ duplicati:duplicati`, mtime `Sep 18`, contents unknown) → the daily 13:45Z snapshot copies a stale DB or fails with `REFUSE: source DB genuinely absent` | high |
| `…snapshot.py:40,76–89`; `util/systemd/yamaguchi-server-db-snapshot.service:15` | "root-only, drwx------ root root" | wrong now (dir is duplicati-owned); root still reads it | low |
| `…snapshot.py:53–54,105–107,139–141` | dest `/home/pcalnon/.local/state/duplicati-server-db` chmod 0700/0600 owner pcalnon, "rides along in the next backup" | **BROKEN** — a server running as `duplicati` cannot read a 0700 pcalnon dir; the snapshot never enters the archive | high |
| `util/ad-hoc/yamaguchi_server_api.py:11,27,40` | `http://127.0.0.1:8300` | holds only while the wrapper delivers `--webservice-port=8300`; after a `daemon-reload` (§4 x-c/M-x-c) the server would start on Duplicati's default port and every client here reads UNREACHABLE | medium |
| `…server_api.py:41–42` | `CRED_FILE=/home/pcalnon/Development/python/Juniper/juniper-ml/.env` (primary checkout, gitignored `.gitignore:189`, **mode 0664 = world-readable**), key `DUPLICATI_WEB_CREDENTIAL` | a new server instance/DB may carry a different UI password → login 401; file mode leaks the credential to every local user | medium |
| `util/ad-hoc/yamaguchi_watchdog.py:59,87–89` | inherits the above | same | medium |
| `…watchdog.py:160` / `yamaguchi_census.py:78` | `--backup-id 2` | job IDs live in the server DB; a fresh DB (4 KB + WAL) may not carry id 2 → `JOB_MISSING` alert (correct behaviour, but it will fire) | info |
| `…watchdog.py:163`; `yamaguchi_watchdog_deploy.bash:22` | state under `~/.local/state/duplicati` (pcalnon user timer) | unaffected | — |
| `util/ad-hoc/duplicati_api.py:49,53` | `127.0.0.1:8300`; `PW_FILE` default `.env` **relative to cwd** | a run from a worktree reads that worktree's `.env` (absent → crash) | low |
| `…duplicati_api.py:69–84` | key candidates `DUPLICATI_UI_PASSWORD, UI_PASSWORD, PASSPHRASE_OLD, PASSPHRASE`; **bare-secret fallback sends the whole file as the password** | wrong-key silently posts the entire `.env` in the login body | medium |
| `util/ad-hoc/yamaguchi_watchdog_deploy.bash:20,34`; `util/systemd/yamaguchi-watchdog.service:13`; `…db-snapshot.service:16` | ExecStart paths into the PRIMARY checkout | same class as the wrapper symlink: `git checkout/stash/pull` changes deployed code | medium |
| `util/ad-hoc/yamaguchi_census.py:26,97–109` | derives destination from `TargetURL` (good); docstring still names `/media/pcalnon/temp_backups` | unaffected | — |
| `util/duplicati_scheduled_backup.bash:47–50,58,270` | `/media/pcalnon/temp_backups/*`, `DBPATH=/home/pcalnon/.config/Duplicati/DQRVQNDIFX.sqlite`, excludes `/home/pcalnon/.config/Duplicati/` | this lane targets pcalnon's own user instance, not the system server; unaffected but points at the pre-migration destination | low |
| `util/systemd/duplicati-backup.service:14` | `EnvironmentFile=%h/.config/duplicati-backup/env` (exists, `0600`, `Sep 18`; not read) | unaffected | — |

## 8. `util/juniper-backup.bash`

- Device detection: `:121 MEDIA_NAMES=( "EBC5-F0A3" "DFF3-2782" )`, `:122–124 MOUNT_NAME=media USER_NAME=pcalnon BACKUP_DIR=Juniper-8.0.0.python`, `:303–305 target_dir_for` → `/media/pcalnon/<name>/Juniper-8.0.0.python`. Validity `:327–346 validate_external_media`: `mountpoint -q /media/pcalnon/<name>` (`:332`), then `-d` (`:337`) and `-w` (`:341`) on the backup dir; skipped devices degrade to PARTIAL, zero usable devices is fatal (`:421–424`). Relies on udisks auto-mounting under the desktop user's `/media/pcalnon`; no by-UUID/`lsblk` identity check, no auto-mount. `--dest` bypasses the mount check (`:394–406`).
- Trigger: **none in the repo** — `grep -rn 'juniper-backup' util/systemd .github scripts util/*.bash` hits only the script's own header (`:5,:34,:48`); no unit/timer under `util/systemd/` or `~/.config/systemd/user/`, `crontab -l` has no backup entry, no udev rule mentions juniper. Manual invocation only (references from docs/tests/ad-hoc harnesses).
- Exit/verification: `:91 set -euo pipefail`; codes `:51–57` (0 complete, 1 fatal, 2 misuse, 4 PARTIAL on cross-repo totals `:586–588`); `trap cleanup_partial EXIT` (`:290–299`) removes the in-progress archive only; `verify_archive` (`:351–367`) = non-empty + `gpg --list-packets --list-only` + recipient-count == `${#ENCRYPT_KEYS[@]}` — proves OpenPGP structure and 2 recipients, **not** tar integrity nor build/copy byte-identity (`:350` says so; no `cmp` after `cp` `:546`); `sync` after each write (`:533,:560`); free-space checks are warnings only (`:448–454`); `--ignore-failed-read` (`:155`) lets unreadable files drop silently with exit 0. **Low/medium** — add `cmp -- BUILD COPY`, make the space check fatal below 1:1, wire a timer or document manual-only status.

## What this analysis cannot establish

- **How Duplicati 2.4.0.0 parses the malformed argv** (` --webservice-port=8300 `, `--webservice-port=8300 --webservice-interface=loopback `, `--daemon-opts="…"`, ` "--webservice-port `): the binary was never executed; the "one option per argv element, split at the first `=`" behaviour is from knowledge of Duplicati's `CommandLineParser`, not observation. The journal (owned by another agent) will show the effective port and any "unsupported option" warning.
- Whether the line-49 literal is the key **currently** in use, and whether `/home/duplicati/.config/Duplicati/.env` or `/etc/default/duplicati` contain it — neither file was read (stat only).
- What the **loaded** unit actually is — taken from the task statement (`systemctl show`), not probed.
- Empirical confirmation that systemd expands `${DAEMON_OPTS}` inside a single-quoted word — derived from the documented unquote-then-substitute pipeline; a transient `systemd-run` test was outside my write boundary. Verify with: `systemd-run --user -P -q -p 'Environment=DAEMON_OPTS=--webservice-port=8300' /bin/echo '--daemon-opts="${DAEMON_OPTS}"'`.
- Whether `/usr/lib/duplicati/data/` still holds a `Duplicati-server.sqlite` (dir is 0700, not listable as pcalnon).
- The vendor unit's full original text (no cached `.deb`; only the dpkg md5 mismatch proves modification).
- Why gitleaks missed the literal (charset inference), and whether GitHub secret scanning is enabled for the repo (`alerts` returned `[]`, which is also what a disabled feature can look like).
- Whether Duplicati can consume `$CREDENTIALS_DIRECTORY`/`%d` files natively (`--secret-provider`, `duplicati-secret-tool` are shipped but were not run or documented here).
- Whether the yamaguchi job (id 2) exists in the new server DB and what the watchdog status file currently says.

No file was written into the repository; all artefacts are under the scratch directory named at the top.

<!-- markdownlint-enable -->

---

## Report 2c — Authoritative Duplicati 2.x product facts from primary sources

Subagent id `a09ff23b7b3b4ec19` (50,620 characters).

<!-- markdownlint-disable -->

All research is complete; nothing further depends on another result. Final report follows.

# Duplicati 2.x facts for the backup-infrastructure design (host: `duplicati 2.4.0.0 amd64`)

Scratch directory for every quoted local artefact: `S = /tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/227cf645-dd93-4802-91f7-23dcaa92c971/scratchpad/agent5-research/` (help outputs in `S/help*/`, man pages in `S/man/`, upstream sources in `S/src/` and `S/tagged/`, packaging copies in `S/pkg/`, GitHub JSON in `S/gh/`, docs in `S/docs/`). Nothing was written into the repository. No sudo; nothing under `/home/duplicati`, `~/.config/Duplicati`, `/mnt/Backups` or `/usr/lib/duplicati/data` was touched.

## 0. Sandbox run findings (important operational surprises)

- **`duplicati-server --version` is not a version flag — it starts the server.** Output (`S/help/server-version.txt`): `Server has started and is listening on localhost, port 8200` plus a sign-in URL; `timeout 60` killed it (exit 124). It created, in the fake HOME only, `.config/Duplicati/{Duplicati-server.sqlite,machineid.txt,installation.txt,control_dir_v2}` and `.aspnet/DataProtection-Keys/`. It bound `127.0.0.1:8200` for ≤60 s (the real service is on 8300, so no clash). Verified afterwards: no leftover `duplicati` processes; `/usr/lib/duplicati/data` untouched (it is `drwx------ duplicati duplicati`, i.e. owned by `duplicati`, not root, on this host; `ls` as pcalnon → `Permission denied`).
- **`duplicati-cli --version` prints the help of the `--version` job option**, not the build version (`S/help/cli-version.txt`). Version comes from `duplicati-cli help` footer `Version: 2.4.0.0 - 2.4.0.0_stable_2026-09-03` (`S/help/cli-help.txt` L22-23), `duplicati-cli system-info` (`S/help2/system-info.txt`: `.Net Version: 10.0.1`, `SQLite: 3.53.4`, `Default data folder: <HOME>/.config/Duplicati/`, `Install folder: /usr/lib/duplicati/`), and `duplicati-server-util --version` = `2.4.0.0-Stable-20260903+f04c49d78620d7f4d5e79f7dbb9ee393e6a128db`.
- `duplicati-server help` and `duplicati-server help advanced` are byte-identical (51 lines, `S/help/server-help.txt`).
- `duplicati-service --help` does not print help: it spawns `duplicati-server --help --ping-pong-keepalive=true` and restarts it in a loop (`S/help/service-help.txt`) — matching docs: "a small helper program that simply runs the Server executable and restarts it if it exits" (https://docs.duplicati.com/duplicati-programs/service.md, `S/docs/duplicati-programs_service.md` L7).
- Live service on this host (`S/pkg/systemctl-show.txt`): `User=duplicati Group=duplicati`, `ExecStart=/home/duplicati/bin/duplicati-wrapper.bash …`, pid 1397393 `/usr/lib/duplicati/duplicati-server --webservice-port=8300`, listening `127.0.0.1:8300` and `[::1]:8300`.

## 1. Data-folder resolution (`duplicati-server` 2.x)

Implementing code: `Duplicati/Library/AutoUpdater/DataFolderManager.cs` — https://raw.githubusercontent.com/duplicati/duplicati/master/Duplicati/Library/AutoUpdater/DataFolderManager.cs (the v2.4.0.0 copy https://raw.githubusercontent.com/duplicati/duplicati/v2.4.0.0_stable_2026-09-03/Duplicati/Library/AutoUpdater/DataFolderManager.cs differs from master only in ID-caching helpers and `ResolveDataFolderRelativePath`, not in the resolution order — diff in `S/tagged/`).

```
104 public static string GetDataFolder(AccessMode mode)
107     PORTABLE_MODE = ParseBoolSlim(ExtractOptionSlim(PORTABLE_MODE_OPTION));
111     // The environment variable is a legacy setting
112     var envOverride = Environment.GetEnvironmentVariable(DATAFOLDER_ENV_NAME);   // DUPLICATI_HOME (L84)
115     var datafolderArg = ExtractOptionSlim(SERVER_DATAFOLDER_OPTION);
117     // Prefer the command line argument over the environment variable
118     if (!string.IsNullOrWhiteSpace(datafolderArg)) { … dataFolder = … datafolderArg … }
123     // Portable mode is prefered over the environment variable
124     else if (PORTABLE_MODE) { … dataFolder = Path.Combine(UpdaterManager.INSTALLATIONDIR, "data") … }
129     // Use the legacy environment variable, if set
130     else if (!string.IsNullOrWhiteSpace(envOverride)) { … }
135     // Use the default location
136     else { … DataFolderLocator.GetDefaultStorageFolderInternal(SERVER_DATABASE_FILENAME, APPNAME) }
```

Precedence: **`--server-datafolder` > `--portable-mode` (`<install dir>/data/`, where `INSTALLATIONDIR` = directory of the entry assembly, `UpdaterManager.cs` L118) > `DUPLICATI_HOME` > OS default**. Each option also has an environment form: `ExtractOptionSlim` falls back to `DUPLICATI__<OPTION>` (L360-362: `$"{AppName}__{option.Replace('-', '_')}".ToUpperInvariant()`), i.e. `DUPLICATI__SERVER_DATAFOLDER`, `DUPLICATI__PORTABLE_MODE`. Docs agree: "If both are supplied, the commandline options are used." (https://docs.duplicati.com/duplicati-programs/server.md, `S/docs/duplicati-programs_server.md` L192-204).

**No automatic portable mode.** The only "data-dir-beside-executable" logic is behind the explicit flag; `ParseBoolSlim` (L385-399) returns `true` for a missing value **only in DEBUG builds** ("In debug builds, we default to portable mode"). Grep of v2.4.0.0 `Server/Program.cs`, `DataFolderManager.cs`, `UpdaterManager.cs`, `AutoUpdateSettings.cs` for `"data"`/`portable` finds nothing else. Empirically confirmed: the sandboxed 2.4.0.0 server, with `/usr/lib/duplicati/data` present, wrote to `$HOME/.config/Duplicati`.

Default location (`Duplicati/Library/AutoUpdater/DataFolderLocator.cs` L86-90): `Path.Combine(Environment.GetFolderPath(SpecialFolder.ApplicationData), "Duplicati")` — "`%LOCALAPPDATA%` on Windows, `~/.config` on Linux"; if the account has no home folder the result is rooted to `/var/lib/Duplicati` (L136-158; changelog 2.4.0.101: "the data folder was stored as the relative path `var/lib/Duplicati` … Relative paths are now resolved correctly"). Docs: "The default location when running Duplicati on Linux is `~/.config/Duplicati`" (https://docs.duplicati.com/database-and-storage/the-server-database.md L90).

Permission gate (2.3.1.0+): `PrepareSecureDataFolder` (L225-260) creates and `chmod 0700`s a missing folder, and for a pre-existing folder *verifies without modifying*: "A pre-existing folder is never modified … otherwise it is rejected" (L208-211), throwing `InsecureDataFolderPermissions` (L335-341) unless `--allow-insecure-datafolder` / `DUPLICATI__ALLOW_INSECURE_DATAFOLDER=true` / `insecure-permissions.txt` in the **installation** folder (docs L58-66). The Linux check (`Duplicati/Library/Common/IO/SystemIOLinux.cs` L500-539): mode must include 0700, no group/other bits, and "The owner must be the current user or root. A root-owned folder is trusted" (L522-526).

**Answer for `duplicati` with `HOME=/home/duplicati`, no data-folder flag, `/usr/lib/duplicati/data` root-owned 0700:** the server never looks at `/usr/lib/duplicati/data` — it resolves `/home/duplicati/.config/Duplicati/` (or `$XDG_CONFIG_HOME/Duplicati` if set), creates it 0700 if absent, and refuses to start if it pre-exists with wrong mode/owner. Only if `--portable-mode` (or `DUPLICATI__PORTABLE_MODE=true`) were given would it use `/usr/lib/duplicati/data/`; that folder would *pass* the permission check (root owner is trusted) and the server would then fail on the first write (`installation.txt`/`machineid.txt`, L147-157, no try/catch) with an access-denied exception → `ServerCrashed`, exit 100 (`Program.cs` L392-404).

## 2. `SETTINGS_ENCRYPTION_KEY` / `--settings-encryption-key` / `--disable-db-encryption`

Server help (`S/help/server-help.txt`): L43 `--settings-encryption-key: Use this option to set the encryption key for the settings database. This option can also be set with the environment variable SETTINGS_ENCRYPTION_KEY.`; L40 `--disable-db-encryption: Use this option to disable database encryption of sensitive fields`; L42 `--require-db-encryption-key: … not rely on the serial number.`; L41 `--disable-default-secret-provider`.

**What is encrypted** — `Duplicati/Library/RestAPI/Database/Connection.cs` (https://raw.githubusercontent.com/duplicati/duplicati/master/Duplicati/Library/RestAPI/Database/Connection.cs; identical block at the v2.4.0.0 tag) L66-89: `_encryptedFields` = every option of type `Password` from all backends, encryption/compression/generic/web/source/restore-destination modules and `Options` (name and aliases, bare and `--`-prefixed) plus `JWT_CONFIG, PBKDF_CONFIG, REMOTE_CONTROL_CONFIG, SERVER_SSL_CERTIFICATE, SERVER_SSL_CERTIFICATEPASSWORD, SERVER_CA_CERTIFICATE_KEY, SERVER_CA_CERTIFICATE_PASSWORD, REMOTE_CONTROL_STORAGE_API_KEY, CLIENT_LICENSE_KEY`. `--passphrase` is type `Password` (`S/help2/opt-passphrase.txt` L1), so **the backup passphrase is encrypted when encryption is on**, as are backup `TargetURL`s (L865) and connection-string base URLs (L1671). Applied in `SetSettings` L394-400 / `EncryptSensitiveFields` L1600-1608. With encryption off the fields are cleartext: "No database encryption key was found. The database will be stored unencrypted." (`Library/RestAPI/Strings.cs` L109). Field format (`Library/Encryption/EncryptedFieldHelper.cs` L82, L157-175): `enc-v1:` + SHA256(ciphertext) + SHA256(key) + AES hex.

**Startup paths** — `Server/Program.cs` `GetDatabaseConnection` (master L1117-1281; region identical at v2.4.0.0 except the later `--webservice-dont-autocreate-database` addition):
- key absent, DB already encrypted: warning L1178-1185 "The database appears to be encrypted, but no key was specified. Opening the database will likely fail." → then `Decrypt` throws `SettingsEncryptionKeyMissingException` ("Encryption key is missing.", `Library/Interface/CustomExceptions.cs` L223-228, `Interface/Strings.cs` L52) → caught L392-404 as `ServerCrashed`, exit 100. Docs: "If any fields are already encrypted, Duplicati will refuse to start without the encryption key." (server.md L49).
- key absent, DB not encrypted: tries the **default secret provider** (L1194-1236; `Library/Main/SecretProviderHelper.cs` L94-114, opt-out `--disable-default-secret-provider`); if it can store secrets it generates a random 32-byte key under the name `duplicati-server-encryption-key` (L107, L1211) and encrypts; otherwise `disableDbEncryption = true` with the warning above (L1249-1259). Linux default provider per changelog 2.2.0.102/103: "Linux: libSecret (Gnome Keyring), or commandline `pass` if available" (`S/src/changelog.txt` L1310-1314).
- key present but different/wrong: `Decrypt` checks the embedded key hash — `if (keyHash != key.Hash) throw new SettingsEncryptionKeyMismatchException();` (EncryptedFieldHelper L138-139) → "Encryption key used to encrypt target settings does not match current key." (Interface/Strings L51) → startup failure (the `ReWriteAllFieldsIfEncryptionChanged` comment L133-135: "In case the password has changed, this will fail … but will crash before reaching this point").
- state change: `connection.ReWriteAllFieldsIfEncryptionChanged()` is called at startup (Program.cs L324) and, when `ApplicationSettings.EncryptedFields != m_encryptSensitiveFields`, re-saves every backup and all settings then `VACUUM` (Connection L131-151). So `--disable-db-encryption` **with the old key** decrypts everything; restarting with a new key re-encrypts. Docs server.md L51-57; changelog 2.0.9.106 L3202-3203.
- `--require-db-encryption-key` without key → "Database encryption key is required…" (L1241-1242, Strings L107). Blacklisted (old device-derived) keys are decrypted and disabled (L1262-1268).

**Key derivation when none is supplied:** none in 2.4.0.0 — see above (random key in the OS secret store, else unencrypted). `machineid.txt`/`installation.txt` are updater/identity files (DataFolderManager L51-56, L147-157), not key material. The machine-serial derivation existed only in **2.0.9.105_canary_2024-08-29** ("The key used to encrypt is derived from the machine serial number, so the database cannot be decrypted on another machine", changelog L3251) and was **removed in 2.0.9.106_canary_2024-09-03** ("did not produce secure results. This feature has now been removed", L3207-3208).

**Supported move procedure:** docs the-server-database.md L45-50: "1. Stop Duplicati 2. Move the `Duplicati` folder from the old location to the new location 3. Change the startup parameters (environment variables, commandline arguments, or preload.json) 4. Start Duplicati again" — the same `SETTINGS_ENCRYPTION_KEY` must be supplied on the new host (env var, `--settings-encryption-key`, `preload.json` L23-33, or secret provider). If the key was the auto-generated one it lives in the source host's secret store; either extract it or decrypt first (`--disable-db-encryption` run, then move, then re-key). Last resort: `duplicati-database-tool wipe-encryption <databases>` "Removes or clears any encrypted strings from the server database so it can be used without the original encryption key" (`S/help3/dbtool-help.txt` L19; added 2.3.0.108, changelog L400-402). The destination folder must satisfy the 0700/owner rule (or run `duplicati-configure secure-datafolder [--for-service]` — `--for-service` sets owner root, `SecureDataFolderCommand.cs` L107/L145 → `excludeCurrentUser`).

**Release that introduced it:** 2.0.9.105 canary (2024-08-29; "Settings database version updated to v8 … Encrypting data in `Duplicati-server.sqlite`", L3236-3237) with server schema script `8. Encrypted fields.sql`; user-supplied-key form from 2.0.9.106 canary; present in every stable from 2.1.0.4 (schema 8 at that tag). Docs "Version 8: Duplicati 2.1.0.0" (https://docs.duplicati.com/technical-details/database-versions.md L21). Default auto-encryption via secret provider: 2.2.0.102 canary (2025-12-12).

## 3. Schema versions, releases, and what the crash log implies

**Upgrader** — `Duplicati/Library/SQLiteHelper/DatabaseUpgrader.cs` (identical at v2.4.0.0 and master): L235-236 `if (dbversion > versions.Count) throw new … UserInformationException(Strings.DatabaseUpgrader.InvalidVersionError(dbversion, versions.Count, Path.GetDirectoryName(sourcefile)), "DatabaseVersionNotSupportedError");` where `versions.Count` is the number of numbered `N. ….sql` embedded scripts. Exact string (`Library/SQLiteHelper/Strings.cs` L26-30): `"The database has version {0} but the largest supported version is {1}.\n\nThis is likely caused by upgrading to a newer version and then downgrading.\nIf this is the case, there is likely a backup file of the previous database version in the folder {2}."`. The prefix "Failed to create, open or upgrade the database.\nError message: {0}" is `Library/RestAPI/Strings.cs` L30-31 and is used **only** in `Server.Program.GetDatabaseConnection` (L1135, L1154, L1162): `databasePath = Path.Combine(applicationSettings.DataFolder, DataFolderManager.SERVER_DATABASE_FILENAME)` (`Duplicati-server.sqlite`) → `DatabaseUpgrader.UpgradeDatabase(con, databasePath, typeof(Library.RestAPI.Database.DatabaseSchemaMarker))` — the **server** database (same line at v2.3.0.4 L1053 and v2.4.0.0 L1148). The local job DB is upgraded from `Library/Main/Database/Local/LocalDatabase.cs` L206 without that prefix.

**Numbered scripts today** (GitHub tree, `S/gh/tree_master.txt`): server `Duplicati/Library/RestAPI/Database/Database schema/1…12` (`12. Add OperationType to Backup.sql`; older releases kept the same folder, never `Duplicati/Server/Database/Database schema` in any tag checked); local `Duplicati/Library/Main/Database/Local/Database schema/1…21` (moved from `Main/Database/Database schema` between 2.3.0.4 and 2.3.0.106).

**Max schema per tag** (GitHub contents API, `S/gh/schema/`):

| Tag | server max | local max |
|---|---|---|
| v2.0.9.111_canary_2024-11-14, v2.1.0.4_stable, v2.1.0.5_stable | 8 | 13 |
| v2.1.1.0_experimental_2025-07-17 | 8 | 17 |
| v2.1.2.3_beta, v2.2.0.0/0.1/0.3_stable, v2.2.0.103_canary | 9 | 17 (2.2.0.103: 18) |
| v2.2.0.104_canary_2026-02-06 | 9 | **19** (first) |
| v2.2.0.105_canary_2026-02-20 (first with 11), v2.2.0.106, v2.2.1.0_beta, v2.2.0.107_canary, v2.3.0.0_stable, **v2.3.0.4_stable** | **11** | 19 |
| v2.3.0.106_canary_2026-07-03 (earliest checked with 12), v2.3.0.107/108/109, v2.3.1.0_beta, v2.3.1.1_beta, **v2.4.0.0_stable** | **12** | 19 |
| v2.3.0.110_canary, v2.4.0.100/101_canary | 12 | 20 |
| master (2026-09-21) | 12 | 21 |

(2.3.0.100–105 canaries were not listed; docs page only goes to "Version 9: Duplicati 2.2.0.0" / "Version 17: 2.2.0.0".)

**Releases 2.3.0.x / 2.4.0.x with neighbours** (https://api.github.com/repos/duplicati/duplicati/releases, 268 releases, `S/gh/releases_table.tsv`; channel from tag; GitHub `prerelease` = false only for `_stable_`):

| Tag | Published (UTC) | Channel |
|---|---|---|
| v2.2.1.0_beta_2026-03-05 | 2026-03-05 | beta |
| v2.2.0.107_canary_2026-03-20 (immediately before 2.3.0.0) | 2026-03-20 | canary |
| v2.3.0.0_stable_2026-04-14 | 2026-04-14 | stable |
| v2.3.0.100_canary_2026-04-23 | 2026-04-23 | canary |
| v2.3.0.1_stable_2026-04-24 | 2026-04-24 | stable |
| v2.3.0.101_canary_2026-05-04 | 2026-05-04 | canary |
| v2.3.0.102_canary_2026-05-09 | 2026-05-09 | canary |
| v2.3.0.103_canary_2026-05-22 | 2026-05-22 | canary |
| v2.3.0.104_canary_2026-06-04 | 2026-06-04 | canary |
| v2.3.0.2_stable_2026-06-10 | 2026-06-10 14:19 | stable |
| v2.3.0.3_stable_2026-06-10 | 2026-06-10 17:09 | stable |
| v2.3.0.105_canary_2026-06-24 | 2026-06-24 | canary |
| v2.3.0.106_canary_2026-07-03 | 2026-07-03 | canary |
| v2.3.0.4_stable_2026-07-09 | 2026-07-09 | stable |
| v2.3.0.107_canary_2026-07-13 | 2026-07-13 | canary |
| v2.3.0.108_canary_2026-07-20 | 2026-07-20 | canary |
| v2.3.1.0_beta_2026-07-28 | 2026-07-28 | beta |
| v2.3.0.109_canary_2026-08-14 | 2026-08-14 | canary |
| v2.3.0.110_canary_2026-08-25 | 2026-08-25 | canary |
| v2.3.1.1_beta_2026-08-26 (immediately before 2.4.0.0) | 2026-08-26 | beta |
| v2.4.0.0_stable_2026-09-03 | 2026-09-03 | stable |
| v2.4.0.100_canary_2026-09-04 | 2026-09-04 | canary |
| v2.4.0.101_canary_2026-09-11 (latest; nothing after) | 2026-09-11 | canary |

**Could a 2.3.0.4-written DB be at version 19 while 2.4.0.0 supports only 11?** No, on both counts: 2.3.0.4 writes server schema **11** (local 19); 2.4.0.0 supports server **12** (local 19) and would say "largest supported version is 12". The observed message is only producible by a binary whose *server* script count is 11 (2.2.0.105-canary … 2.3.0.4-stable, e.g. the 2.3.0.4 noted on 2026-08-21) opening, at `<datafolder>/Duplicati-server.sqlite`, a file whose `Version` table says 19 — a value no server schema has ever reached, but exactly the **local job-database** schema of 2.2.0.104-canary…2.4.0.0. Inference: the file at the server-DB path was a local job database (copied/misplaced/pointed to via `--server-datafolder`/`DUPLICATI_HOME`), and the log was **not produced by 2.4.0.0**. Supporting detail: crash logs are named `{EntryAssemblyName}-crashlog.txt` (`Library/Crashlog/CrashlogHelper.cs` L120, L132), written to the system temp dir until `GetDatabaseConnection` sets `CrashlogHelper.DefaultLogDir = applicationSettings.DataFolder` (Program.cs L1123); the installed 2.4.0.0 ships `Duplicati.GUI.TrayIcon.dll` and no `*.Net10*` assembly exists in the tree or `/usr/lib/duplicati`, so the `Duplicati.GUI.TrayIcon.Net10` name in the log cannot be matched to this package (.NET 10 since 2.2.0.101_canary_2025-11-20, changelog L1419). Downgrade tooling: `duplicati-database-tool downgrade` (defaults `--server-version 9`, `--local-version 14`, `S/help3/dbtool-downgrade-help.txt` L12-13; docs https://docs.duplicati.com/duplicati-programs/command-line-interface-cli-1/databasetool.md L12 "must be in the most-recent version for the downgrade to work").

## 4. Packaging

Upstream files are under `ReleaseBuilder/Resources/`, not `Installer/` (all `Installer/*` paths 404). `ReleaseBuilder/Resources/debian/systemd/duplicati.service` is identical at master and v2.4.0.0 and its md5 (`e989e07f6014ca27556c99af42c5e7f9`) matches this host's `dpkg` md5sums for `lib/systemd/system/duplicati.service` (`S/pkg/dpkg-maintainer-scripts.txt` L1606):

```
[Unit]
Description=Duplicati web-server
After=network.target

[Service]
Nice=19
IOSchedulingClass=idle
IOSchedulingPriority=7
EnvironmentFile=-/etc/default/duplicati
ExecStart=/usr/bin/duplicati-server $DAEMON_OPTS
Restart=always

[Install]
WantedBy=multi-user.target
```
(https://raw.githubusercontent.com/duplicati/duplicati/v2.4.0.0_stable_2026-09-03/ReleaseBuilder/Resources/debian/systemd/duplicati.service). **No `User=`: the vendor unit runs as root.** `/etc/default/duplicati` (`…/systemd/duplicati.default`, md5 `43a59355…` matches): header comments then `DAEMON_OPTS=""`. Package assembly (`ReleaseBuilder/Build/Command.CreatePackage.cs` L1141-1150) installs them to `etc/default/duplicati` and `lib/systemd/system/duplicati.service`; `DEBIAN/conffiles` is generated from everything under `etc/` (L1199-1209) — the unit is **not** a conffile; only `DEBIAN/preinst` is shipped for the server/GUI/CLI packages (L1211-1226; it only warns about missing ICU — `S/pkg/dpkg-maintainer-scripts.txt` L3057-3078), while `postinst`/`prerm` exist **only for the Agent package** (L1228-1249; `postinst-agent` runs `systemctl enable duplicati-agent` + `start`). Consequently the deb creates no user and does not enable the service; docs tell the admin to `sudo systemctl enable duplicati.service …` (https://docs.duplicati.com/platform-specific-guides/using-duplicati-with-linux.md L80-87) and warn "Make sure you only edit the configuration file and not the service file as it will be overwritten when a new version is installed" (L63). Fedora: same unit but `EnvironmentFile=-/etc/sysconfig/duplicati`, `Restart=on-failure`; spec uses `%systemd_post/%systemd_preun/%systemd_postun_with_restart` and `%config(noreplace) /etc/sysconfig/duplicati`.

On this host the unit file has been edited locally (md5 `9fe951a5…`, mtime 2026-09-21 01:44; adds `User=duplicati`, `Group=duplicati`, a wrapper `ExecStart`) and `/etc/default/duplicati` holds `DAEMON_OPTS="--webservice-port=8300"` (`S/pkg/duplicati.service`, `S/pkg/duplicati`).

Upstream-documented non-root path: docs state "the service runs in the `root` user context, so files will be stored in `/root/.config/Duplicati` … Use the `DAEMON_OPTS` to add `--server-datafolder=<path>`" (L91) and, under "Linux systemd service and supplementary groups": "When Duplicati runs under a dedicated service account on Linux … use the edit functionality: `sudo systemctl edit duplicati.service` … `[Service] SupplementaryGroups=group1 group2` … This method ensures that a package upgrade does not erase your edits." (L99-123). No upstream page prescribes `User=` itself (NOT FOUND); the supporting tooling is `duplicati-configure secure-datafolder --datafolder … --apply --for-service` (`S/help2/configure-secure-help.txt`; "Restrict the permissions on the data folder so only root and the current user can access it"), and the permission check's acceptance of root-owned 0700 folders "for example a system service reading a configuration folder provisioned by an installer running as root" (SystemIOLinux L489-493). `duplicati-configure` commands: `https`, `secure-datafolder` (`S/help/configure-help.txt` L11-13).

## 5. `duplicati-server-util` and the export format

Commands (`S/help/serverutil-help.txt` L25-38): `pause <duration>`, `resume`, `delete <backup>`, `list-backups` (`--detailed`), `run <backup>` (`--wait`, `--skip-queue`, `--poll-interval`, `--quiet`), `login`, `change-password <new-password>`, `logout`, `import <file> <passphrase>`, `export <backups>`, `health`, `issue-forever-token`, `status`. Global options (L7-23): `--password`, `--hosturl` (default `http://127.0.0.1:8200/`), `--server-datafolder … [default: <HOME>/.config/Duplicati/]`, `--portable-mode`, `--allow-insecure-datafolder`, `--settings-file`, `--insecure`, `--settings-encryption-key … Can also be supplied with environment variable SETTINGS_ENCRYPTION_KEY` (this one encrypts ServerUtil's *own* settings/refresh-token file, docs serverutil.md L31), `--secret-provider*`, `--host-cert`, `--ignore-revocation-failure`, `--json`. Auto-login works by reading the server DB and minting a sign-in token (`CommandLine/ServerUtil/Connection.cs` L248-272 via `Server.Program.GetDatabaseConnection`); docs: "if you run Duplicati as a service, you should invoke ServerUtil as Administrat/root … `duplicati-server-util login --server-datafolder=<database folder path>`" (https://docs.duplicati.com/duplicati-programs/command-line-interface-cli-1/serverutil.md L17-23).

`export` options (`S/help2/serverutil-export-help.txt` L10-15): `--encryption-passphrase`, `--export-passwords` ("Flag toggling the inclusion of sensitive values, such as passwords, defaults to true if a passphrase is supplied"), `--overwrite`, `--unencrypted`, `--destination`. Logic (`CommandLine/ServerUtil/Commands/Export.cs` L92-126): unencrypted → passwords excluded unless `--export-passwords` ("Warning: Exporting unencrypted configurations with sensitive keys included"); encrypted → `exportPasswords ??= true`; output `"{backup.ID}-{backup.Name}.json{(unencrypted ? "" : ".aes")}"` (L138). `import` (`Import.cs` L40-53): `--import-metadata`, `--backup-passphrase` ("Use this option if the configuration was exported without secrets"), `--backup-url`; AES detection by `"AES"` header (L112-119). Docs: "If you do not supply a passphrase, the exported configuration will not include the passphrase or storage credentials. Use `--export-passwords=true` to force export the passwords to a plain-text file." (serverutil.md L63).

JSON format = `Duplicati.Server.Serializable.ImportExportStructure` (`Library/RestAPI/Serializable/ImportExportStructure.cs` L27-33): `{ CreatedByVersion, Schedule, Backup, DisplayNames }`, `Backup` fields (`Library/RestAPI/Database/Backup.cs` L63-123): `ID, ExternalID, Name, Description, Tags, TargetURL, DBPath (relative), ConnectionStringID, OperationType, Sources, Settings[], Filters[], Metadata, AdditionalTargetURLs`. Serialized by `BackupImportExportHandler.ExportToJSON` and AESCrypt-encrypted when a passphrase is given (L40-57). Web UI: `GET /backup/{id}/export?export-passwords=&passphrase=&token=` plus `export-cmdline` and `export-argsonly` (`WebserverCore/Endpoints/V1/Backup/BackupGet.cs` L60-75); without `export-passwords` `RemovePasswords` → `Backup.RemoveSensitiveInformation()` strips every `PasswordFieldNames` entry from the target URL query, `Settings`, `Sources` and additional target URLs (Backup.cs L131-193). Import: `POST /backups/import` with `cmdline, import_metadata, direct, temporary, passphrase, replace_settings` (`Endpoints/V1/Backups.cs` L38-43). Docs page: https://docs.duplicati.com/configuration-and-management/import-and-export-backup-configurations.md ("The file is in JSON format and optionally encrypted with AESCrypt", L21; "Export passwords" checkbox, L17).

## 6. Server options in 2.4.0.0 (`S/help/server-help.txt`, line = help line)

| Option | Status | Help text |
|---|---|---|
| `--webservice-interface` | PRESENT L17 | "The interface the webserver listens on. The special values "*" and "any" means any interface. The special value "loopback" means the loopback adapter." |
| `--webservice-port` | PRESENT L12 | "The port the webserver listens on. Multiple values may be supplied with a comma in between." |
| `--webservice-allowed-hostnames` | PRESENT L20 | "The hostnames that are accepted, separated with semicolons. If any of the hostnames are "*", all hostnames are allowed and the hostname checking is disabled." |
| `--webservice-password` | PRESENT L18 | "The password required to access the webserver. This option is saved so you do not need to set it on each run. An access password is mandatory." (also `--webservice-password-init` L19: "Sets the password only if not already set, and then exits.") |
| `--webservice-disable-signin-tokens` | PRESENT L25 | "Disable the use of signin tokens" |
| `--webservice-enable-forever-token` | PRESENT L22 | "Enable the use of long-lived access tokens" |
| `--webservice-api-only` | PRESENT L24 | "Disable the web interface and only allow API access" |
| `--tempdir` | PRESENT L4 | "Use this option to supply an alternative folder for temporary storage. … Note that also SQLite will put temporary files in this temporary folder." |
| `--log-file` / `--log-level` / `--log-console` | PRESENT L8-10 | "Output log information to the file given" / "Determine the amount of information written in the log file" / "Output log information to the console" |
| `--log-retention` | PRESENT L37 | "Set the time after which log data will be purged from the database." |
| `--server-datafolder` | PRESENT L38 | "Duplicati needs to store a small database with all settings. Use this option to choose where the settings are stored. This option can also be set with the environment variable DUPLICATI_HOME." |
| `--portable-mode` | PRESENT L7 | "Activate portable mode where the database is placed below the program executable" |
| `--allow-insecure-datafolder` | PRESENT L39 | "…bypasses the security check that prevents using a world-readable folder for the database and configuration…" |
| `--settings-encryption-key` | PRESENT L43 | (quoted in §2) |
| `--disable-db-encryption` | PRESENT L40 | "Use this option to disable database encryption of sensitive fields" |
| `--require-db-encryption-key` | PRESENT L42 | "…require a custom provided key … and not rely on the serial number." |
| `--server-encryption-key` | NOT PRESENT | only orphaned strings `ServerencryptionkeyShort/Long` remain in `Library/RestAPI/Strings.cs` L73-74; 0 uses in `Server/Program.cs` |
| `--startup-delay` | NOT PRESENT | — |
| `--pause-resume` | NOT PRESENT | pausing is `duplicati-server-util pause [<duration>]` / `resume` |
| `--register-remote-control`, `--register-remote-control-force` | PRESENT L44-45 | "Register for remote control using the pre-authenticated url…" / "Forces a re-registration…" |
| `--allowed-backend-modules` / `--allowed-encryption-modules` / `--allowed-compression-modules` | PRESENT L46-48 | "Set the allowed backends for remote control. … comma-separated list…" |
| `--secret-provider`, `--secret-provider-pattern`, `--secret-provider-cache`, `--disable-default-secret-provider` | PRESENT L49-51, L41 | — |
| `--disable-update-check` | PRESENT L36 | "Use this option to disable the automatic update check. Manual update checks can still be performed." |
| `--disable-signin-tokens` | NOT PRESENT | correct name is `--webservice-disable-signin-tokens` |
| `--webservice-dont-autocreate-database` | NOT PRESENT in 2.4.0.0 | exists only on master (`WebServerLoader.cs` L127, changelog 2.4.0.101) |
| `--ping-pong-keepalive`, `--webservice-reset-jwt-config`, `--webservice-pre-auth-tokens`, `--webservice-token-duration`, `--webservice-cors-origins`, `--webservice-timezone`, `--webservice-spa-paths`, `--webservice-webroot`, `--webservice-disable-https`, `--webservice-sslcertificatefile/-password`, `--webservice-remove-sslcertificate`, `--configure-https[-hostnames]`, `--webservice-suppress-welcome-page`, `--webservice-enable-folder-status-service`, `--webservice-disable-api-extensions`, `--parameters-file` | PRESENT L6-35 | — |

Every option can also be given as `DUPLICATI__<UPPER_SNAKE>` env var; command line wins (Program.cs `ApplyEnvironmentVariables` L971-988; docs server.md L206-218).

## 7. File backend on a Dropbox-synced folder, verification, scripts, Dropbox facts

**How Duplicati writes** (`Duplicati/Library/Backend/File/FileBackend.cs`, identical logic at v2.4.0.0):
- Streaming path (default): L393-397 `string targetFilePath = GetRemoteName(targetFilename); … using (var targetStream = systemIO.FileCreate(targetFilePath)) … CopyStreamAsync(...)` then `VerifyMatchingSize` — i.e. **the final file name is created and filled in place; there is no temp-name-then-rename on the destination.** Non-streaming path L429-450 copies (or with `--use-move-for-put` moves) the local temp file onto the final name. `RenameAsync` exists (L568-577) but is not used for uploads. Uploads are issued by `BackendManager.PutOperation.PerformUploadAsync` (L286-305) under the final `dblock/dindex/dlist` name; on a **retry after a failed attempt the volume is renamed to a fresh name** (`RenameFileAfterError` L419-431: `"Renaming \"{0}\" to \"{1}\""`), so a partially written file can remain behind. Docs: "it will make a temporary file, and then copy the temporary file to the new location. This enables various retry mechanisms…" (https://docs.duplicati.com/backup-destinations/standard-based-destinations/file-destination, corpus `S/docs/llms-full.txt` L5871-5877). Backend options (`S/help2/topic-file.txt`): `--use-move-for-put` ("This option has no effect unless the option --disable-streaming-transfers is activated"), `--disable-length-verification` ("the uploaded file length will be checked against the local source length"), `--alternate-target-paths` / `--alternate-destination-marker` (marker-file check for removable drives), `--read-write-timeout = 30s`, `--list-timeout = 10m`.
- **Out-of-band changes are detected as errors:** `FilelistProcessor.VerifyRemoteListAsync` (L165-207) logs `Extra unknown file: {0}` / `Missing file: {0}` per file, then throws `RemoteListVerificationException`: "Found {0} remote files that are not recorded in local storage. This can be caused by having two backups sharing a destination folder which is not supported. It can also be caused by restoring an old database…" or "Found {0} files that are missing from the remote storage, please run repair". `--no-backend-verification` skips this compare ("the local database is not compared to the remote filelist on startup", `S/help2/opt-no-backend-verification.txt`). An explicit docs sentence "the destination must not be modified by anything else" / guidance on sync clients or online-only placeholders for a local file destination: **NOT FOUND** in the docs corpus (only the generic "the backup files will generally be visible as part of the synchronization files" for the API-based Dropbox/OneDrive backends, L5812-5819).
- Verification options (`S/help2/`): `--upload-verification-file (Boolean) … The file is not encrypted and contains the size and SHA256 hashes of all the remote files … * default value: false`; `--backup-test-samples (Integer) … If this value is set to 0 or the option --no-backend-verification is set, no remote files are verified. * default value: 1`; `--backup-test-percentage (Decimal) … percentage (between 0 and 100) of samples … the number of samples tested is the maximum implied by the two options … * default value: 0.1`; `--full-remote-verification` (advanced help L306-314).
- **Scripts** (`S/help2/topic-runscript.txt`): `--run-script-before (Path)`, `--run-script-after (Path)`, `--run-script-post-backup (Path)` (new: "after the backup data has been written … but before the remote verification"), `--run-script-before-required (Path): … If the script returns a non-zero error code or times out, the operation will be aborted.`, `--run-script-timeout (Timespan) … * default value: 60s` ("it will continue to execute but the operation will continue too"), `--run-script-with-arguments`, `--run-script-result-output-format`, `--run-script-log-level`, `--run-script-log-filter`. Exit-code contract (`Duplicati/Library/Modules/Builtin/RunScript.cs`): required script — `if (!p.HasExited) throw … ScriptTimeoutError … else if (p.ExitCode != 0) throw new UserInformationException(Strings.RunScript.InvalidExitCodeError(scriptpath, p.ExitCode), "RunScriptInvalidExitCode");` (L390-396: **any non-zero code or timeout aborts**); non-required `--run-script-before` — `case 0: // OK, run operation`, `case 2: // Warning, run operation`, `case 4: // Error, run operation`, `case 1: // OK, don't run operation` → abort Normal, `case 3: // Warning, don't run operation` → abort Warning, `default: // Error don't run operation` → abort Error (L436-448); codes 2/3 log a warning, 4/5/other an error (L412-431); `timeout <= 0` waits forever (L385-388). Docs agree: "The backup will only be run if the script completes with an allowed exit code (0, 2, or 4). A timeout or any other exit code will abort the backup." (https://docs.duplicati.com/automation-and-integration/scripts.md L73-76; same text in `/usr/lib/duplicati/run-script-example.sh`).
- **Dropbox (help.dropbox.com):** "Files uploaded through the desktop app or mobile apps must be 2 TB or smaller and files uploaded to dropbox.com must be 50 GB or smaller." and "Files uploaded through the API must be 350 GB or smaller." (https://help.dropbox.com/sync/files-not-syncing); "The maximum file size you can upload to Dropbox is 2 TB (2,199,019,061,248 bytes)." and "Uploading files larger than 375 GB in a web browser may cause timeouts" (https://help.dropbox.com/sync/upload-limitations — note the 50 GB vs 375 GB web figures disagree between the two pages). Files written by other processes: "Some applications will put restrictions in place that can prevent other applications (like Dropbox) from accessing your files while that other application has them open." and "If your file is read-only or is locked by a non-Dropbox application, you can't sync your file to Dropbox." (files-not-syncing). Linux CLI (https://help.dropbox.com/installs/linux-commands): `dropbox exclude [list]` ("display a list of directories that are currently excluded from syncing"), `dropbox exclude add [DIRECTORY]…`, `dropbox exclude remove [DIRECTORY]…`, `dropbox status`, `dropbox filestatus [-l] [-a] [FILE]…`, `dropbox running`. Selective sync: "You can only select folders … You can't select individual files" and settings "are unique to each computer" (https://help.dropbox.com/sync/selective-sync-overview). Ignore a file on Linux: `attr -s com.dropbox.ignored -V 1 '/home/yourname/Dropbox (Personal)/YourFileName.pdf'` (https://help.dropbox.com/sync/ignored-files; "Online-only files, and folders containing online-only files can't be ignored"). Online-only: "An online-only file is stored in the cloud and won't take up storage space on your computer" and opening one "will automatically download" it (https://help.dropbox.com/sync/make-files-online-only).

## 8. Job options in 2.4.0.0 (`duplicati-cli help <option>`, `S/help2/opt-*.txt`; advanced listing `S/help/cli-help-advanced.txt`)

| Option | Status | Quote |
|---|---|---|
| `--no-auto-compact` | PRESENT | "(Boolean): Disable automatic compacting … only compact when running the compact command. * default value: false" |
| `--asynchronous-upload-limit` | PRESENT | "(Integer): The number of concurrent uploads allowed … Set to zero to disable the limit. * aliases: --asynchronous-concurrent-upload-limit * default value: 4" |
| `--gpg-encryption-switches` | PRESENT | "(String): Extra GPG commandline options for encryption … You cannot specify the --passphrase-fd option here. The --encrypt option is always specified." (gpg module also has `--gpg-program-path = /usr/bin/gpg2`, `--gpg-encryption-command = --symmetric`) |
| `--encryption-module=aes\|gpg` | PRESENT | "(String): Select what module to use for encryption … * default value: aes"; modules listed `aes, gpg` (`cli-help.txt` L15) |
| `--blocksize` | PRESENT | "(Size): Block size used in hashing … Note that the value cannot be changed after remote files are created. * default value: 1mb" |
| `--dblock-size` | PRESENT | "(Size): Limit the size of the volumes … * aliases: --remote-volume-size * default value: 50mb" |
| `--skip-files-larger-than` | PRESENT | "(Size): Limit the size of files being backed up or restored … When restoring, files larger than this value are not restored." |
| `--allow-missing-source` | PRESENT | "(Boolean): Ignore missing source elements … no warning is emitted for missing sources. * default value: false" |
| `--no-local-blocks` | PRESENT but DEPRECATED | "[DEPRECATED]: The default is now to not use local blocks for restore. To opt-in for using local blocks, set the option --restore-with-local-blocks." |
| `--no-backend-verification` | PRESENT | "(Boolean): Do not query backend at startup … the local database is not compared to the remote filelist on startup." |
| `--retention-policy` | PRESENT | "(String): Reduce number of versions by deleting old intermediate backups … e.g. "7D:0s,3M:1D,10Y:2M" … specifier "U"" |
| `--keep-time` | PRESENT | "(Timespan): Keep all versions within a timespan" |
| `--keep-versions` | PRESENT | "(Integer): Keep a number of versions … Supply -1 to keep all versions. * default value: 0" |
| `--upload-verification-file` | PRESENT | (quoted in §7) |
| `--concurrency-max-threads` / `-block-hashers` / `-compressors` / `-fileprocessors` | PRESENT | defaults 0 / 8 / 8 / 8 ("Setting this value to zero or less will dynamically balance…") |
| `--log-level` (job option) | PRESENT but DEPRECATED | "[DEPRECATED]: Use the options --log-file-log-level and --console-log-level instead." (server-side `--log-level` is separate and current) |
| `--tempdir`, `--log-file`, `--log-retention`, `--passphrase` (env `PASSPHRASE`) | PRESENT | — |

Return codes (`S/help2/topic-returncodes.txt`): 0 success; 1 success, no files changed; 2 warnings; 3 backup finished with errors / test found errors; 50 uploaded some files but did not finish; 100 error; 200 invalid arguments.

## 9. systemd facts (systemd 259 on this host; `man -P cat` dumps in `S/man/<page>.txt`, line numbers below)

- **Credentials** (`systemd.exec` L3665-3678): "LoadCredential=ID[:PATH], LoadCredentialEncrypted=ID[:PATH] Pass a credential to the unit … The data is only accessible to the user associated with the unit, via the User=/DynamicUser= settings (as well as the superuser). When available, the location of credentials is exported as the $CREDENTIALS_DIRECTORY environment variable"; search path when PATH is omitted: "/etc/credstore/, /run/credstore/ and /usr/lib/credstore/ … If LoadCredentialEncrypted= is used /run/credstore.encrypted/, /etc/credstore.encrypted/, and /usr/lib/credstore.encrypted/ are searched as well" (L3696-3702). L3728-3738: "LoadCredentialEncrypted= … credential data is decrypted and authenticated before being passed on … encrypted/authenticated with a secret key derived from the system's TPM2 security chip, or with a secret key stored in /var/lib/systemd/credential.secret, or with both." L3764-3770: use `"${CREDENTIALS_DIRECTORY}/mycred"` in ExecStart, `%d/mycred` in Environment=, or `/run/credentials/UNITNAME`. `$CREDENTIALS_DIRECTORY` (L4035-4041): "read-only and is placed in unswappable memory (if supported and permitted), and is only accessible to the UID associated with the unit". `SetCredential=` (L3869-3878): "Do not use this option for data that is supposed to be secret, as it is accessible to unprivileged processes via IPC … For everything else use LoadCredential=." `systemd-creds encrypt input output` (`systemd-creds` L66-97) produces files for `LoadCredentialEncrypted=`; name embedding via `--name=` (L227-249); `systemd-creds cat credential…` (L43-46).
- **`RequiresMountsFor=`** (`systemd.unit` L794-801): "Automatically adds dependencies of type Requires= and After= for all mount units required to access the specified path. Mount points marked with noauto are not mounted automatically … but are still honored for the purposes of this option".
- **`ProtectHome=`** (`systemd.exec` L1364-1386): "Takes a boolean argument or the special values "read-only" or "tmpfs". If true, the directories /home/, /root, and /run/user are made inaccessible and empty … The value "tmpfs" is useful to hide home directories not relevant … while still allowing necessary directories to be made visible when listed in BindPaths= or BindReadOnlyPaths=. Setting this to "yes" is mostly equivalent to setting the three directories in InaccessiblePaths=". Interaction with `ReadWritePaths=` (L1620-1640): "Paths listed in ReadWritePaths= are accessible from within the namespace with the same access modes … Use ReadWritePaths= in order to allow-list specific paths for write access if ProtectSystem=strict is used … Paths listed in InaccessiblePaths= will be made inaccessible … it is not possible to nest ReadWritePaths=, ReadOnlyPaths=, BindPaths=, or BindReadOnlyPaths= inside it." ⇒ with `ProtectHome=yes` a `ReadWritePaths=/home/duplicati` cannot punch through; use `ProtectHome=tmpfs` + `BindPaths=`, or `ProtectHome=read-only` + `ReadWritePaths=` (read-only is "mostly equivalent to ReadOnlyPaths=", inside which ReadWritePaths= may be nested, L1624-1625).
- **`SupplementaryGroups=`** (L728-737): "space-separated list of group names or IDs … does not override, but extends the list of supplementary groups configured in the system group database for the user. This does not affect commands prefixed with "+"." **`UMask=`** (L1125-1127): "Takes an access mode in octal notation … Defaults to 0022 for system units."
- **`RestartSec=`** (`systemd.service` L513-516): "time to sleep before restarting a service … Defaults to 100ms." **`StartLimitIntervalSec=interval, StartLimitBurst=burst`** (`systemd.unit` L983-1008): "Units which are started more than burst times within an interval time span are not permitted to start any more … may be set to 0 to disable any kind of rate limiting … units which are configured for Restart=, and which reach the start limit are not attempted to be restarted anymore … systemctl reset-failed will cause the restart rate counter … to be flushed".
- **`ExecStartPre=` with `+`** (`systemd.service` L345-356: "Syntax is the same as for ExecStart= … ExecStart= commands are only run after all ExecStartPre= commands that were not prefixed with a "-" exit successfully."; prefix table L1209-1219: ""+" If the executable path is prefixed with "+" then the process is executed with full privileges. In this mode privilege restrictions configured with User=, Group=, CapabilityBoundingSet= or the various file system namespacing options … are not applied").
- **`systemd-analyze security [UNIT…]`** (`systemd-analyze` L559-580): "analyzes the security and sandboxing settings of one or more specified service units … calculates an overall exposure level … in the range 0.0...10.0"; example `systemd-analyze security --no-pager systemd-logind.service` (L599); `--threshold=` L1023.
- **Path units** (`systemd.path` L71-98): "PathExists= may be used to watch the mere existence of a file or directory. If the file specified exists, the configured unit is activated. PathExistsGlob= works similarly, but checks for the existence of at least one file matching the globbing pattern … If a path already exists … at the time the path unit is activated, then the configured unit is immediately activated as well." `Unit=` defaults to the same-named `.service` (L107-111). `ConditionPathIsMountPoint=` (`systemd.unit` L1413-1415).
- **Mount/automount** (`systemd.mount`): `x-systemd.automount` "An automount unit will be created for the file system" (L213-215); `x-systemd.device-timeout=` "how long systemd should wait for a device to show up before giving up on an entry from /etc/fstab … can only be used in /etc/fstab" (L225-231); `nofail` "this mount will be only wanted, not required, by local-fs.target or remote-fs.target … the boot will continue without waiting for the mount unit" (L337-342); `x-systemd.mount-timeout=` (L235-242); `x-systemd.idle-timeout=` (L219). `Where=` "must be reflected in the unit filename" (`systemd.mount` L387-394; `systemd.automount` L87-91); `TimeoutIdleSec=` (`systemd.automount` L107-111).
- **Triggering on a USB disk by UUID:** device units "are named after the /sys/ and /dev/ paths they control. Example: the device /dev/sda5 is exposed in systemd as dev-sda5.device" and only for devices "marked with the "systemd" udev tag (by default all block and network devices…)" (`systemd.device` L21-33); `SYSTEMD_WANTS=` "Adds dependencies of type Wants= from the device unit to the specified units … may be used to activate arbitrary units when a specific device becomes available … systemd will only act on Wants= dependencies when a device first becomes active" (L55-71; udev rule side: "provide a service unit and pull it in from a udev device using the SYSTEMD_WANTS device property", `udev` L339-344). Escaping (`systemd.unit` L255-265): "any "/" character is replaced by "-", and all other characters which are not ASCII alphanumerics, ":", "_" or "." are replaced by C-style "\x2d" escapes … Use systemd-escape --path to escape path strings" — hence `/dev/disk/by-uuid/UUID` → `dev-disk-by\x2duuid-UUID.device`; `systemd-escape -p --suffix=mount /mnt/Backups` → `mnt-Backups.mount` (`systemd-escape` L31-34, L48-53). `BindsTo=` "in addition to the effects of Requires= … it also does so when a listed unit stops unexpectedly … the backing device of a device unit might be unplugged … in many cases it is best to combine BindsTo= with After=" (`systemd.unit` L612-633).

## NOT FOUND / could not verify

- No upstream documentation page prescribing `User=` for `duplicati.service`; only the "dedicated service account" + `systemctl edit` drop-in guidance and `secure-datafolder --for-service`.
- No docs sentence stating the file destination must not be modified by other software / sync clients / online-only placeholders; the behaviour is established from `FilelistProcessor.cs` only.
- The `Duplicati.GUI.TrayIcon.Net10` assembly name in the host crash log matches no file in `/usr/lib/duplicati` (2.4.0.0) nor any path in the upstream tree; which package/build wrote that log is unverified (crash-log naming rule cited in §3).
- `/usr/lib/duplicati/data` on this host is owned by `duplicati:duplicati`, not root as the brief assumed; who created it (a `--portable-mode` run is commented out in `/etc/default/duplicati`) was not investigated (out of scope; directory not readable by pcalnon).
- Schema listings for canaries 2.3.0.100–2.3.0.105 and 2.3.0.1–2.3.0.3 stables were not fetched (bracketing tags were), and the docs "Database versions" page stops at server v9 / local v17.
- Dropbox web-upload limit: two help pages disagree (50 GB vs 375 GB caution); both quoted, not reconciled.
- context7 (`/duplicati/documentation`) was consulted but every claim above is backed by the fetched primary page or source file; forum threads were not used as evidence.

**Changed**: no repository files. Scratch artefacts only, under `S` (`run_local.bash`, `run_local2.bash`, `run_local3.bash`, `fetch_sources.bash`, `fetch2.bash`, `schema_hist.bash`, `schema_hist2.bash`, `man_extract.py`, and the captured outputs listed above).

<!-- markdownlint-enable -->
