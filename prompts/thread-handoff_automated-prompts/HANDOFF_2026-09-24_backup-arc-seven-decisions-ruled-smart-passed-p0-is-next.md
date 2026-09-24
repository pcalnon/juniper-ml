# HANDOFF 2026-09-24 — backup arc: seven decisions ruled, sda SMART passed, P0 is the next action

Continue the **Juniper backup-infrastructure arc** (host `yamaguchi`, Duplicati 2.4.0.0). The design of
record is
[`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`](../../notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md).
**Tier 1 backup has been DOWN since 2026-09-18 14:12Z.**

## What THIS SESSION may do next

No **host** action in §8 or §10.2 is a session's to perform. These are:

1. **Shepherd ml#2067 to merge** — `mergeable_state=blocked`, 4 files. Needs owner merge approval.
2. **Archive and commit this handoff.** It is committed nowhere (see Git state).
3. **Record a disposition for a dropped change.** Closing ml#2045 dropped a real `+56/−50` divergence in
   `util/ad-hoc/smart_checks_backup-sda.bash` (its copy `export`s every constant and is mode 0755).
   Nothing records whether that was intended. Decide: adopt, or state why not.
4. **Repair stale text in §8 that the 2026-09-22 rulings closed**: P1 step 5 still says "**Re-decide D-2**,
   do not merely execute it" and P2 step 2 still says "**After a D-14 ruling**". Both were ruled in §10.1.
5. **Fix two defects the design carries**: it says `--no-local-db` rebuilds "from all 877 dindex volumes"
   (877 is the *total* destination file count, of which **9 are dlists**), and §12 Document history has no
   row for ml#2029, ml#2041 or ml#2057.

## What the OWNER must supply before P0 can start

- The escrowed `PASSPHRASE`, from the printed sheet or password manager — **never** the Dropbox-synced
  copy (that is S-4).
- root/sudo, and a window: P0 stops the running server and does not return it to service until step 8.

## Completed so far

- **All seven gating decisions RULED** 2026-09-22 (ml#2029, `ab434c9b`), recorded in **§10.1**: **D-1**
  keep DB encryption (distinct key, `/etc/credstore`, `LoadCredential=`, `--require-db-encryption-key`);
  **D-2** rotate the passphrase **and keep** the existing sets; **D-4** `CAP_DAC_READ_SEARCH` + §7.3.2's
  confinement set; **D-6** installed copy **plus a drift gate** (`--update-backup-behavior`); **D-8** scrub
  once after P1; **D-9** loopback only; **D-14** read-only destination (`2750`/`0640`/`UMask=0027`).
- **`sda` SMART: RUN and PASSED 2026-09-23** (ml#2041, `4b311619`). Nine readings committed under
  `reports/smart/` plus `util/ad-hoc/smart_checks_backup-sda.bash`. Extended offline test completed
  without error at lifetime 28,938 h against 28,941 h at capture; reallocated / pending / uncorrectable /
  CRC all **0**. This closes the **D-12a** carried item "sda SMART never read".
  **It does NOT unblock the rotation.** §10.2 step 1 is **HALF DONE** — its drill half is AC-4's first
  drill, inside P0 step 11 — so **§10.2 step 2 remains blocked**.
- **Drill ordering clarified** (ml#2057, `d15e7c01`): §10.2 step 1's drill *is* AC-4's first drill, from
  `duplicati-20260918T140000Z`, and **cannot precede P0** — it needs the job index P0 step 1's freeze
  copies aside.
- **ml#2045 CLOSED unmerged.** Its net effect against `main` was **two** files: the design's front-matter
  reformat, and the `smart_checks_backup-sda.bash` divergence above. 614 of 615 `added` paths and 53 of 54
  `modified` paths were byte-identical to `main`.
- **ml#2067 OPEN** — re-lands the front-matter reformat **only**. Four files: the design doc (+16/−18),
  `PR_BODY_FRONTMATTER.md`, `2026-09-23_pr2045_net_effect.py`, `2026-09-24_reformat_design_frontmatter.py`.

## Remaining work, in order — P0 scope only

1. **§8 P0.5a items 1, 2, 4, 5, 6 and 7** (not just 1–2; item 3 moved to P0.5b). Item 4 is the two-log-store
   scrub that is the actual S-3 remediation; item 6 closes the secret-detection gap; item 7 is
   `usermod -s /usr/sbin/nologin duplicati`.
2. **P0 step −1** — review the nine scripts §8 invokes. It is defined in the **§8 preamble paragraph**, not
   in the numbered P0 list. **All nine are already merged on `main`**, so only the review remains.
3. **P0 step 0** — (a) verify installed artifacts against §10.1 (a verification now, not a decision);
   (b) obtain the escrowed passphrase; (c) confirm Procedure A0's premise — which §8 requires you to run
   **after P0 step 1's freeze**, because it needs the job index that step copies aside.
4. **P0 steps 1–8**, then **P0.5b** (the re-key), then **P0 steps 9–11**. §8's heading is explicit:
   "P0.5b — **immediately after P0 step 8, same session**" — it closes S-1 and S-2 and is not deferrable,
   but is not runnable before step 8. Deferring it past step 11 would run the first backup and both drills
   with the compromised settings key still installed.
5. **AC-4's two restore drills at P0 step 11.** The first discharges §10.2 step 1 and unblocks §10.2 step 2.
6. **§10.2 steps 2–8** — the D-2 rotation, after recovery is drill-verified.

**Not in this list, and still live**: P0.5a items 4–7 are above but P1, P2, P3, P4 are not; AC-1 needs 24 h;
AC-6 becomes provable only in P2. Seven decisions remain open and **gate nothing in P0 or §10.2**: D-3,
D-5, D-7, D-10, D-11, D-12, D-13 — but **D-5 gates P3 step 3**, and **D-13 is named in §7.3.2's confinement
set**, so "gate nothing" is true only of P0 and the rotation.

## Key context — do not re-derive or re-litigate

- **The service is RUNNING.** `duplicati.service` has been `active` since 2026-09-20 18:19:42 CDT, PID
  1397393, listening on `127.0.0.1:8300`. It is the **empty** server holding zero backup definitions.
  **Never start or restart it** — `/home/duplicati/.config/Duplicati` is `drwxrwxrwx`, so the next start
  fails the 0700 gate. **P0 step 2 stops it**, after step 1's freeze. Do not stop it before then.
- **Nothing under `/mnt/Backups/Ubuntu/` is DELETED OR MOVED**, with exactly one owner-signed exception:
  P1 step 4 copies the passphrase escrow out of the Dropbox root, then deletes the in-tree copy (S-4).
  ("Changed" is the wrong word — §7.4's script chowns the tree under D-14, and §10.2 step 7 swaps staging
  in as the live destination.)
- **`duplicati-server --version` STARTS A SERVER** on port 8200. Read capability out of the assemblies
  instead: `util/ad-hoc/2026-09-22_duplicati_literal_scan.py` (literals, UTF-8 + UTF-16LE) and
  `util/ad-hoc/2026-09-22_recoverytool_verbs.py` (RecoveryTool usage strings).
- **`SETTINGS_ENCRYPTION_KEY` is the SERVER-DATABASE key, not the backup passphrase.** The volume secret is
  the job's `PASSPHRASE`. Scanning 1,443 files in both encodings finds **no literal** for
  `SETTINGS_ENCRYPTION_KEY_OLD` or `PASSPHRASE_OLD` — treat that as "no literal", not as "no such feature";
  a name composed at runtime is invisible to the scanner. §4.1 records that the active key on this host
  **already equals `PASSPHRASE`**; that conflation is part of what broke.
- **The new passphrase must NOT go in `.env`** (`0660 duplicati:duplicati`; the wrapper echoed every line of
  it to the journal and syslog — 60 echoes on 09-20, which is S-3). It goes to `/etc/credstore` under
  `LoadCredential=`, a **distinct value** from D-1's settings key.
- **Rotation does not re-encrypt existing volumes — `recompress --reencrypt --new-passphrase` does.** Three
  hazards: `--reupload` deletes the destination originals; the local database must be deleted before and
  recreated after (§5.3 — an *aborted* Recreate started this arc); and `--new-passphrase=` on argv is
  world-readable via `/proc/*/cmdline`.
- **`sda` is a drive-managed SMR disk** (`WDC WD40EZAZ-00SF3B0`). A clean SMART report does not make an
  in-place rewrite safe.
- **Staging goes on `nvme0n1p5` (`/`), never `sda`** (note 10.2b): ~375 GiB free against the ~203 GiB
  needed, a different device, ext4, and outside the `/home/pcalnon` backup source — which `sdc3` (`/home`)
  is not. `sda1` has 3.1 TiB free and is the trap: it holds the sole local copy.
- **A drill needs the JOB index, not the server database.** The *server* DB is the file locked under an
  unmatched key; the *job* index (`BMXWPAOGLP.sqlite`, last written 09-18) is separate and is what a drill
  reads. `--no-local-db` rebuilds from the destination's dlist+dindex volumes (877 files total, 9 of them
  dlists) and was measured at ">30 minutes for a single small file, without completing".

## Traps that cost time

- **Anchored bulk edits can apply TWICE** when `old` is a substring of `new` — the anchor still matches and
  the usual "already applied" test cannot see it (count is 1, not 0). The edit scripts carry a fatal guard
  in `edit()`; widen the anchor to **span** the insertion point.
- **Validate before writing.** An over-width (MD013) check after `write_text` is a report, not a gate.
- **`git diff origin/main...HEAD` (three dots) cannot show what a stale branch would revert.** Use two dots:
  this worktree branch reads `857 files changed, +631/−562,783` two-dot versus a tidy 40-file three-dot.
  Build PRs from current `main` (`util/open_signed_pr.py --base main`, run from the repo root).
- **`open_signed_pr.py --add` parses `LOCAL:REPOPATH` with `partition(":")`**, so a path containing
  `HH:MM:SS` cannot round-trip. Use `util/ad-hoc/2026-09-22_append_signed_commit.py` for those.
- **`reports/` is globally excluded from pre-commit** — safe to commit raw tool output verbatim *as far as
  formatting goes*, but the same exclude skips `detect-private-key` and `check-added-large-files`, so
  **screen `reports/` additions for credential-shaped content by hand**.
- **`tests/test_isolated_stack_script.py` flakes** with `Errno 39 … /markers` inside
  `TemporaryDirectory.__exit__` — an async writer racing teardown. That is **cleanup, not an assertion**.
  Re-run the failed jobs before editing anything.
- **`safe_merge.py` loses this lane** — it pins its net to a SHA, so each `update-branch` strands it. Use
  `gh pr merge N --squash --auto` plus `util/ad-hoc/2026-09-22_shepherd_automerge.bash`, which syncs BEHIND
  and can neither arm nor merge.

## Verify your starting state

Each assertion below is separate on purpose — an OR'd `grep -c` over several patterns passes even when one
is entirely absent.

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml
git fetch origin main && git log origin/main --oneline -1
D=notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md
git show origin/main:$D | grep -c '^### 10.1 Owner rulings'   # expect 1
git show origin/main:$D | grep -c 'UMask=0027'                # expect >=1  (D-14 ruled)
git show origin/main:$D | grep -c '^### 10.2 D-2 execution'   # expect 1
git show origin/main:$D | grep -c 'nvme0n1p5'                 # expect 2    (note 10.2b)
git ls-tree -r --name-only origin/main -- reports/smart/ | wc -l   # expect 9
systemctl is-active duplicati.service   # expect ACTIVE, PID 1397393 -- do NOT stop or restart it
gh pr view 2067 --json state,mergeable,mergeStateStatus
```

## Git state at handoff

- Branch `worktree-buzzing-painting-meteor`, worktree at `juniper-ml/.claude/worktrees/buzzing-painting-meteor`.
  **66 behind / 2 ahead** of `origin/main` — never use it as a PR base; open PRs from `main` instead.
- `origin/main`: `f9c81d80` at handoff time; it moves every ~10–28 min.
- **9 uncommitted paths.** Eight are byte-identical to `main` or to ml#2067 (the lone modified entry,
  `smart_checks_backup-sda.bash`, is a 100644→100755 **mode** change only). The ninth is **this handoff,
  which is committed nowhere — archive it before the worktree is touched.**
- Merged this session: ml#1999 `43980f13`, ml#2029 `ab434c9b`, ml#2041 `4b311619`, ml#2057 `d15e7c01`.
  Closed: ml#2045. Open: ml#2067.

## Validation record

Three independent agents re-probed this document against the live host, repo and `gh` (fact-checker;
procedure auditor role-playing a fresh session; adversarial reviewer). **All three returned FAIL**, with
40 findings between them and three-way convergence on: the service being `active` rather than inactive,
P0.5b belonging inside P0, the "§12" citation being dead (it is D-12a), and this handoff being unbacked.
Every finding above is folded in. The predecessor draft's claim that ml#2045's net effect was "one file"
was itself a measurement defect — `added` paths were compared by path while `modified` paths were compared
by content — now repaired in `util/ad-hoc/2026-09-23_pr2045_net_effect.py`.
