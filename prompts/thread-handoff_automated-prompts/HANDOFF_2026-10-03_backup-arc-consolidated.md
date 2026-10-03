# HANDOFF 2026-10-03 — P1 backup-infrastructure arc (CONSOLIDATED): D-8/STOP change unfinished in round 8 on a local-only branch; P0 HELD by owner STOP; Tier 1 still down

**Consolidated sources** (all in `prompts/thread-handoff_automated-prompts/`, oldest first):

| Alias used below | Source | Self-declared validation |
| --- | --- | --- |
| "the 09-21 handoff" | `HANDOFF_2026-09-21_backup-redesign-round-1-validated-reconciliation-pending.md` | Validated: 3 rounds of independent agents (`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-HANDOFF-CONSENSUS-RECORD.md`) |
| "the seven-decisions handoff" | `HANDOFF_2026-09-24_backup-arc-seven-decisions-ruled-smart-passed-p0-is-next.md` | Validated: three-lens re-probe; all three returned FAIL, 40 findings folded in (merged as ml#2073) |
| "the D-8 handoff" | `HANDOFF_2026-09-24_backup-arc-d8-stop-change-paused-in-round-8.md` | **Unvalidated handoff** (owner asked for minimal tokens; merged as ml#2099) |

Other aliases:

- **"the branch design"** is the design as it stands on the unpushed `worktree-typed-skipping-salamander` (read with `git show worktree-typed-skipping-salamander:<design>`).
- **"the SOP"** is the auto-memory file `feedback_multi_agent_adversarial_validation_sop.md`.

**Supersedes**: the three files above. **Live probe**: 2026-10-03T08:35Z (gh, `git` in this worktree, file reads). **No host state was probed**: the brief forbids `systemctl`, Duplicati binaries and journal reads, so every host claim below is a source claim.

**Document of record** for this arc, called "the design" below: `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`. In this file a bare `§` always means the design.

---

## Goal statement (paste as the new thread's first prompt)

Continue the **Juniper backup-infrastructure arc** (host `yamaguchi`, Duplicati 2.4.0.0). The design of record is `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` ("the design"). **Tier 1 backup has been DOWN since 2026-09-18 14:12Z** (last fileset `duplicati-20260918T140000Z`) [NOT RE-PROBED — from the 09-21 handoff and the seven-decisions handoff; no host probe allowed].
Tier 2 has been broken since 2026-09-07 [VERIFIED 2026-10-03: main's design, line 60 and §4.5]. **No session performs any host action.** Every held or released host step belongs to the owner. Sessions never run a Duplicati binary, never read secret or history files (`stat` only), and never grep the journal or syslog.

**HELD by the owner's 2026-09-24 STOP**: P0.5a items 2 and 4, P0, P0.5b, P1, P2, P4.
**Released (owner-executed)**: P0.5a items 1, 5, 6 and 7 (item 1 before item 4), P3 (step 3 still waits on D-5), §6's sink checklist, S-4's `chmod 0600`, and read-only steps (narrow reading), all within the two limits in item 6, which bind the whole release.
[UNVERIFIED — from the D-8 handoff; the same lists appear in the branch design's note 10.1g, confirmed 2026-10-03.]

**Main's design has NO STOP.** Its status line is `VALIDATED (round 2)`, and its §12 row at line 2461 records "the §8 STOP warning removed and replaced by P0 step 0's owner gates". `grep -c STOP` gives 2 on main (both history) against 27 on the branch design [VERIFIED 2026-10-03: `git show` + grep]. The hold exists only in the owner's 09-24 ruling and on the unpushed branch. **Do not read §8 on main as runnable.**

**Completed so far** [VERIFIED 2026-10-03: `gh pr view`; `git show origin/main`]:

- The round-1 reconciliation, round 2/3, the design's status flip to `VALIDATED (round 2)` and the staging of 13 design artifacts (`util/systemd/*`, `util/install_duplicati_service.bash`, `util/yamaguchi-pre-backup-guard.bash`, wrapper v2) all landed in ml#1999 (`43980f13`). Round 2's record is `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md`.
- All seven gating decisions were ruled on 2026-09-22 (ml#2029, `ab434c9b`, §10.1). The `sda` SMART test PASSED (ml#2041, `4b311619`). Drill ordering was settled (ml#2057, `d15e7c01`). The front-matter reformat re-landed (ml#2067, `dcfc024f`). ml#2045 was closed unmerged.
- The 09-24 handoffs were archived by ml#2073 (`fa951d39`) and ml#2099 (`dffa5bbd`, 2026-09-26T08:09Z).
- On 2026-09-24 the owner made final rulings on D-8 and the STOP scope, quoted under Context [UNVERIFIED — from the D-8 handoff].

**Remaining work, in order:**

1. **Finish round 8 of the D-8/STOP change and open its PR.** *Agent-doable; merge is owner-gated.* The change is three local-only WIP commits on `worktree-typed-skipping-salamander` (`2c9efe85`, `f90a87e7`, `2072e45a`) over pinned base `6c23fdde` [VERIFIED 2026-10-03: `git log origin/main..worktree-typed-skipping-salamander`; no PR exists].
   - Nothing on main has touched its nine files since that base [VERIFIED 2026-10-03: `git diff --stat 6c23fdde origin/main -- <files>` is empty; `git diff --name-only 6c23fdde worktree-typed-skipping-salamander` lists 9].
   - The sub-steps (1a–1h) are listed under Context [UNVERIFIED — from the D-8 handoff, which was not validated].

   This change also carries the 09-24 "seven decisions" handoff's items 3–5, which are therefore still open on main [VERIFIED 2026-10-03: grep on main]:
   - the ml#2045 SMART-script disposition: the owner's refactor is **adopted but for its mode**, so the 0755 mode was not adopted [VERIFIED 2026-10-03: the §12 row in E on the branch]. The "one clock read" detail is [UNVERIFIED — from the D-8 handoff];
   - the stale text in P1 step 5 (`**Re-decide D-2**`, line 2128) and P2 step 2 (`**After a D-14 ruling**`, line 2133);
   - the "all 877 dindex volumes" defect (lines 1739 and 2334; actually 434 dblock + 434 dindex + 9 dlist);
   - the missing §12 rows for ml#2029, ml#2041, ml#2057 and ml#2067 (§12 ends at "2026-09-22 (later)").
2. **Run a narrow validation round on round 8's corrections before opening the PR.** *Agent-doable.* The SOP (`feedback_multi_agent_adversarial_validation_sop.md`) applies because the owner's sweeper arms open PRs.
3. **Re-confirm merge approval with the owner.** *Owner-gated.* The owner granted merge approval for this arc's PRs in the 2026-09-24 session, and the D-8 handoff says to re-confirm it. Then arm with `gh pr merge N --squash --auto` and run `util/ad-hoc/2026-09-22_shepherd_automerge.bash N`.
4. **The §8 follow-up change, which removes the STOP.** *Agent-doable; it needs its own validation round.* Its scope is listed under Context ("§8 follow-up scope") [UNVERIFIED — from the D-8 handoff].
5. **Owner decisions** raised by round 4–8 [UNVERIFIED — from the D-8 handoff]:
   - confirm or widen the two narrow readings (note 10.1g);
   - the fate of P0.5b;
   - where the D-1 flag lives durably;
   - D13 (the `.env` path);
   - S-3c (the frozen 811 volumes and `PASSPHRASE_OLD`);
   - whether to release P0.5a item 2's timer stop on its own, since the snapshot timer still runs the primary checkout's script as root daily.
   - Still open from §10, and gating nothing in P0 or §10.2 [NOT RE-PROBED — from the 09-24 seven-decisions handoff, validated]: D-3, D-5 (gates P3 step 3), D-7, D-10, D-11, D-12 and D-13 (D-13 is named in §7.3.2's confinement set).
6. **Owner may act now, inside the release** [UNVERIFIED — from the D-8 handoff]:
   - P0.5a items 1, 5 (per its new text), 6 and 7, with item 1 still before item 4;
   - P3 (steps 1–2; step 3 waits on D-5);
   - §6's sink checklist and S-4's `chmod 0600`, **"with two limits: no history file is wiped before P0 step 3 tests the keys it may hold, and no transcript is purged before this arc's reports are archived."**;
   - the count-only `sudo grep -c -i -e encryption -e passphrase -e password /home/duplicati/.bash_history`. Never print it, and never wipe on the count.

   The branch design's narrow readings of the ruling (note 10.1g) [UNVERIFIED — these are the design's readings, not the owner's words; the text was confirmed on the branch 2026-10-03]:
   - **"Only reads"** means reads that write nothing and run no Duplicati binary. So P0 step 0(c), which runs `duplicati-cli` with the passphrase, is **HELD**.
   - **"This arc's validation reports"** means every round's reports, archived verbatim into a record merged to `main`. R is unmerged, so **no transcript may be purged now**.
7. **After the STOP lifts — owner-executed** [NOT RE-PROBED — from the seven-decisions handoff, validated; the STOP's provenance is UNVERIFIED — from the D-8 handoff]:
   - P0.5a items 2 and 4;
   - P0 step −1: review the nine scripts §8 invokes (all on main);
   - P0 step 0: verify installed artifacts against §10.1, obtain the escrowed passphrase, and confirm Procedure A0's premise *after* step 1's freeze;
   - P0 steps 1–8, then **P0.5b immediately after step 8, same session**;
   - P0 steps 9–11, including AC-4's two drills (the first discharges §10.2 step 1);
   - §10.2 steps 2–8 (the D-2 rotation);
   - P1, P2 and P4 per §8. Their order relative to §10.2 comes from the design; main's §10.2 step 2 row reads "D-8's journal scrub after P1". P3 is not held (item 6).
8. **Repository-only P0 preparation (no host commands); items still missing on main** [VERIFIED 2026-10-03: `git show origin/main:<file>`]:
   - `util/ad-hoc/yamaguchi_server_api.py` has no `pause`/`resume` and no shared credential path;
   - `util/ad-hoc/duplicati_api.py` still has `PW_FILE` defaulting to `.env`. The D-8 handoff's "step 9 client change unlanded" is the same item;
   - `juniper-backup-failure.service` and `util/install_juniper_backup_timer.bash` are absent (P3 step 2);
   - **Owner-gated, not session work:** B3 O-2 (can `duplicati-server-util --server-datafolder=<copy>` mint a token without `--password`?) is to be settled on a throwaway server with a scratch data folder, never the live one [NOT RE-PROBED — from the 09-21 handoff §1.4]. It runs a Duplicati binary, which the D-8 handoff's hard rules forbid to a session, so the owner runs it, after the STOP lifts (item 7).
9. **Owner items carried from 09-21 that the design does not record** [NOT RE-PROBED — from the 09-21 handoff §1.5, validated; current status unknown]:
   - Rotate the TestPyPI token. Lane A3's harness printed `TEST_TWINE_*` into a subagent transcript. `~/.bashrc` is the only startup file naming it.
   - Feed a root-history key candidate to the key-hash probe (see Context).
10. **Housekeeping.**
    - Appendix C items 1–8 are not yet applied to their targets, plus B1 F14 [NOT RE-PROBED — from the 09-21 handoff §1.6].
    - In auto-memory, MEMORY.md still says "sda … never SMART-tested" twice [VERIFIED 2026-10-03: grep], though `sda` PASSED on 09-23. Fix both.
    - Link the three new reference files from MEMORY.md (they exist, but 0 links) [VERIFIED 2026-10-03: `ls`, `grep -c`]: `reference_uutils_ls_plus_is_any_xattr.md`, `reference_soft_reset_to_a_moving_ref_stages_a_revert.md`, `reference_a_ruling_made_from_a_stale_recommendation_column.md`.
    - Append a 2026-09-24 section to `project_backup_service_user_migration_2026-09-21.md` (last modified 09-23) [VERIFIED 2026-10-03: mtime].
    - MEMORY.md is 25,125 B against a 20 KB target [VERIFIED 2026-10-03: `stat`]. Retire whole entries, never hooks, and re-measure first because other sessions edit it.

**Key context** — full detail is in `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_backup-arc-consolidated.md` § "Context the remaining work needs".

- **The service** is the EMPTY server on `127.0.0.1:8300` (PID 1397393, `Restart=always`). **Never start, stop or restart it.** The next start fails the 0700 gate. P0 step 2 is the only sanctioned stop.
- **Main's §8 is not runnable** — see the "no STOP on main" paragraph above.
- **P0.5a, by item** [NOT RE-PROBED — from the seven-decisions handoff, validated; confirmed against main's P0.5a text]:
  - item 3 (the re-key) moved to P0.5b;
  - item 4 is the two-log-store scrub that is the actual S-3 remediation;
  - item 6 closes the secret-detection gap;
  - item 7 is `usermod -s /usr/sbin/nologin duplicati`.
- **AC-1 needs 24 h**, and **AC-6 becomes provable only in P2**.
- **The active settings key on this host already equals `PASSPHRASE`** (§4.1). That conflation is part of what broke.
- **"A clean SMART report does not make an in-place rewrite safe"**: `sda` is drive-managed SMR.
- **Archived subagent reports**: scan them for secret-shaped content first, before committing them to `notes/`.

---

## Dependencies on other paths

- **No hard dependency** on P2–P10. The arc touches only juniper-ml `notes/`, `util/` and the host.
- **Shared with every path**: auto-memory `MEMORY.md` (item 10). Other sessions edit it concurrently, so re-read it before editing. It is over budget for everyone.
- **Shared PR mechanics** with P3/P4/P9: the owner's PR sweeper arms open PRs unseen, which is why item 2 validates *before* opening. `safe_merge.py` loses this lane (see Traps).
- `[ALSO P4]` item 9's TestPyPI token rotation is a release-path credential. Its rotation does not touch `.github/`, because CI publishes by OIDC.

---

## Context the remaining work needs

### Owner rulings of 2026-09-24 (final) [UNVERIFIED — from the D-8 handoff]

- **D-8 amended**: one scrub, run before P0, as P0.5a item 4. The 09-22 ruling ("scrub once after P1") was made from §10's stale Recommendation column.
- **P0 gate**: items 1, 2 and 4 before P0; items 5–7 "run in the same session".
- **Scope**: a narrow PR, with the §8 fixes in a follow-up. The SMART refactor is adopted (one clock read).
- **STOP scope, verbatim**: hold "P0.5a items 2 and 4, P0, P0.5b, P1, P2 and P4"; release "P0.5a items 1, 5, 6 and 7 (item 1 still runs before item 4), P3's tier-2 fix, §6's sink checklist and S-4's `chmod 0600`, with two limits: no history file is wiped before P0 step 3 tests the keys it may hold, and no transcript is purged before this arc's reports are archived. Read-only steps may run."
- **The branch design's two narrow readings** (note 10.1g, lines 2432–2445 of the branch design) [UNVERIFIED — the design's readings, not the owner's words; the owner may widen them; text confirmed on the branch 2026-10-03]:
  - **"Only reads"** means reads that write nothing and run no Duplicati binary. So P0 step 0(c) is HELD: it runs `duplicati-cli` with the passphrase, from binaries item 1 has not yet secured, after step 1's freeze, which writes.
  - **"This arc's validation reports"** means every round of the arc, archived verbatim into a record merged to `main`. R is unmerged, so no transcript may be purged now.
- **P3 on the branch design** is headed "*Released by the owner's 2026-09-24 ruling (note 10.1g); step 3 still waits on D-5.*" [VERIFIED 2026-10-03: `git show` on the branch].

### Owner rulings of 2026-09-22 (§10.1, on main) [VERIFIED 2026-10-03: ml#2029 merged]

- **D-1**: keep DB encryption, with a distinct key in `/etc/credstore` via `LoadCredential=` and `--require-db-encryption-key`.
- **D-2**: rotate the passphrase **and keep** the existing sets. `recompress --reencrypt --new-passphrase` re-encrypts the volumes; rotation alone does not.
- **D-4**: `CAP_DAC_READ_SEARCH` plus §7.3.2's confinement set.
- **D-6**: an installed copy plus a drift gate.
- **D-8**: superseded by the 09-24 amendment above.
- **D-9**: loopback only.
- **D-14**: a read-only destination (`2750`/`0640`/`UMask=0027`).

### Step 1 sub-steps (D-8 change) [UNVERIFIED — from the D-8 handoff]

Names used below:

- **E** = `util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py`. It holds anchor-asserted edits from `6c23fdde`, a double-apply guard, width/fence/stale-phrase gates and `--self-test`.
- **R** = `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md`, the rounds 4–8 reports verbatim. It exists only on the branch.

The change touches **nine files** [VERIFIED 2026-10-03: `git diff --name-only 6c23fdde worktree-typed-skipping-salamander`]. The D-8 handoff's "7" counted the braced entry as one.

1. `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`
2. `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md` (one sentence)
3. `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md` (R)
4. `util/ad-hoc/2026-09-22_backup-design-round2/COMMIT_BODY_D8.txt`
5. `util/ad-hoc/2026-09-22_backup-design-round2/PR_BODY_D8_AMENDMENT.md`
6. `util/ad-hoc/2026-09-22_backup-design-round2/ROUND4_RECORD_HEADER.md`
7. `util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py` (E)
8. `util/ad-hoc/2026-09-24_archive_round4_reports.py`
9. `util/ad-hoc/smart_checks_backup-sda.bash` (the owner's refactor, adopted but for its mode)

E (in `2072e45a`, **not yet rebuilt**) already carries round-8 lens A 1–5 and most of lens B. Still to do:

- **1a.** Lens B #3, the §5.3 sentence. Replace it with: "…the one place left to look, and only without printing a line — a Repair command there may carry `--passphrase`, and §6's row for the file says never print; no §8 step lists that search or a way to run it without printing, and once P0 step 3 has tested the file, the release's first limit no longer keeps it (note 10.1g)." In §11, change "(no shell history names it)" to "(pcalnon's shell history does not name it; root's is unread, §5.3)".
- **1b.** Change "Rounds 4–7" to "4–8" everywhere in E:
  - the front matter (×3), the STOP heading, the §11 state line, "seven rounds"→"eight", the §12 row, note 12b, "four rounds' reports", and the docstring;
  - add a §11 **Round 8** entry covering: a correction recorded as applied but never made; ruling wording that was not the owner's own; item 5's copy being group-writable; and two released instructions with no safe method.
- **1c.** Add STALE phrases for the replaced text: "P3 but its step 3", "count-grep now", "look before then", "except the one escrow copy named in P1 step 4", "step 3 still waits on D-5.*", and "`/home/duplicati/bin/` entirely\n(it holds".
- **1d.** Rebuild: `git restore --source=6c23fdde --worktree -- <design> <round-2 record>`, then run E. Fix any FAIL or OVER-WIDTH; table rows must be ≤512. Re-run until it reports "no change", then `--self-test` → 8 of 8.
- **1e.** Update R's header `ROUND4_RECORD_HEADER.md`:
  - add "What round 8 was for / found / Disposition of round 8";
  - round 8 lens A: 4 refuted, 1 unverifiable, 155 confirmed. Lens B: 11 refuted, 1 unverifiable, 95 confirmed, and 3 of round 7's 25 dispositions false;
  - the B13 row: §7.11 and P3 step 2 only in round 8;
  - the title line becomes rounds 4–8, "round 8 read `f90a87e7`".
  - Then regenerate R with the 11 `--report` ids. The `--tasks-dir` is now `~/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/0a852d44-65ca-46ac-953b-84e8bae98e9c/subagents` [CHANGED SINCE HANDOFF: the D-8 handoff's `…--claude-worktrees-typed-skipping-salamander/…` path no longer exists; all 11 ids found under the new path, 2026-10-03 `ls`]. The ids:
    - R4: A `a33654134593ec9e5`, B `a57877766ba2b23a2`, C `a8f24f03a0369020a`
    - R5: A `a966210ea522cee20`, B `a43c655c58fa3c7d3`
    - R6: A `a841de27cfb79b907`, B `a3c38866fe3a3c00e`
    - R7: A `a87a13ad93fbc1532`, B `a0467007773f20047`
    - R8: A `a3b34b2844d99f420`, B `aabb0e6fb4eee5891`
  - R already holds all eleven reports.
- **1f.** Gates:
  - `util/ad-hoc/2026-09-22_stage_design_artifacts.py --check`. It exits 0 even on drift, so read the "0 staged" line.
  - `util/ad-hoc/2026-09-21_lint_design_snippets.py --doc <design> --workdir <scratch>`.
  - The pinned markdownlint **without** `--fix`: `~/.cache/pre-commit/repo*/node_env-default/bin/markdownlint --config .markdownlint.yaml`. Pre-commit skips `notes/`.
  - `python3 -m flake8 --max-line-length=512`. Pre-commit skips `util/ad-hoc/`.
  - `/opt/miniforge3/bin/pre-commit run --files …`.
  - `util/markdown_structure_delta.py --base 6c23fdde --head <wip>`, and `juniper-symbol-loss-check` / `juniper-docs-additions-check` on the same refs.
- **1g.** Fill the placeholders (ROUND_LAST, EDIT_COUNT, VALIDATION_PLACEHOLDER) in the PR and commit bodies.
- **1h.** Re-check that `git diff --stat 6c23fdde origin/main -- <the 9 files listed above>` is empty. Then run `python3 util/open_signed_pr.py --repo juniper-ml --base main --branch <b>` with one `--add F:F` for each of the nine files:

  - `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`
  - `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md`
  - `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md`
  - `util/ad-hoc/2026-09-22_backup-design-round2/COMMIT_BODY_D8.txt`
  - `util/ad-hoc/2026-09-22_backup-design-round2/PR_BODY_D8_AMENDMENT.md`
  - `util/ad-hoc/2026-09-22_backup-design-round2/ROUND4_RECORD_HEADER.md`
  - `util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py`
  - `util/ad-hoc/2026-09-24_archive_round4_reports.py`
  - `util/ad-hoc/smart_checks_backup-sda.bash`

  The rest of the command: `--message … --commit-body-file …/COMMIT_BODY_D8.txt --title … --body-file …/PR_BODY_D8_AMENDMENT.md`.

### §8 follow-up scope (item 4) [UNVERIFIED — from the D-8 handoff]

- **STOP items 1–5**:
  1. the step 0(a) flag/blessed file, and a durable home for the D-1 flag under D-6;
  2. P1 step 1 overwrites the old key;
  3. step 10's guard dry-run on an empty `TargetURL`, plus step 9's unlanded client change;
  4. the timer restart after step 8 copies A0's cleartext DB;
  5. `ProtectSystem=strict` without `ReadWritePaths=`.
- **Other §8 fixes**:
  - D-9 flags are installed by nothing;
  - the D13 `.env` path;
  - a no-print key-candidate extraction for P0 step 3;
  - P1 step 4's `cp -a` nesting;
  - `InaccessiblePaths=` misses `/mnt/Backups/Ubuntu/_yamaguchi_keys`;
  - a transcript count-by-value method (sink-c);
  - P0.5b's need and placement;
  - Procedure B starts before step 8;
  - the triggers for items 5 and 7.
- **R's follow-up rows**:
  - round 4's B11, B13–B18, B24, B26, B27 and U1–U4;
  - AC-8 "hardening timestamp";
  - wrapper v2's `die` path;
  - `confirm_a0_premise.bash` "here" (the tagged block and the landed copy together);
  - P0 step 8's mode sentence;
  - the sign-in URL is logged regardless of the flag;
  - §10.2 step 7's local set;
  - AC-14's raw `\|`;
  - P0 step 1's second listing;
  - §4.1/§7.3.1 "P0.5 closes 0777 .config".

### Host facts and recovery sources [NOT RE-PROBED — from the 09-21 and 09-24 handoffs, validated]

- **Service**: `duplicati.service` runs as `duplicati` (uid 133 / gid 139), PID 1397393, active since 2026-09-20 18:19:42 CDT, on `127.0.0.1:8300`, with **0 backups defined**.
  - Its data folder `/home/duplicati/.config/Duplicati` is `0777`.
  - The *loaded* `ExecStart` is already the new `'--daemon-opts="${DAEMON_OPTS}"'` form; only the running process predates it. **The next start "does not start"** because of the 0700 gate. **Stop, never restart** until the §7.3 unit and a 0700 folder are in place. P0 step 2 stops it, after step 1's freeze.
- **Recovery source A0 (key-free)**: the 09-17 and 09-18 14:00Z filesets each hold a cleartext schema-11 root server DB at `home/pcalnon/.local/state/duplicati-server-db/Duplicati-server.sqlite`.
  - Restore that single file with the escrowed passphrase and a fresh `--dbpath`.
  - `util/ad-hoc/2026-09-22_confirm_a0_premise.bash` (on main) checks the premise.
- **Snapshot file**: `~/.local/state/duplicati-server-db/Duplicati-server.sqlite` is **replaced daily at 13:45 UTC** (a new inode). Copy it aside before P0.
- **The job index** is `BMXWPAOGLP.sqlite` in `/usr/lib/duplicati/data/`. **Every procedure must move it into the new data folder and re-point `Backup.DBPath` before the first run.** `DBPath` is stored ABSOLUTE; if it is not moved, the first backup fails read-only and P4 deletes the index.
  - A drill needs this *job* index, not the server DB. `--no-local-db` was measured at >30 min for one small file (on the old `Ubuntu` archive, ml#1268).
- **The 09-18 settings key is unrecorded.** The only untested candidate sources are root's `~/.bash_history` and `.viminfo` for 09-18 20:42–21:03. `SETTINGS_ENCRYPTION_KEY` is the server-DB key, NOT the backup passphrase.
  - To test a candidate, write one `SETTINGS_ENCRYPTION_KEY=<value>` line to a 0600 file and feed it **alone** on stdin:
    `cat <file> | python3 util/ad-hoc/2026-09-21_duplicati_settings_key_hash_probe.py scripts/duplicati-wrapper.bash ~/.config/duplicati-backup/env snap=<copy>`
  - Expect `candidates loaded: ['ENV_ACTIVE_KEY', 'L', 'PASSPHRASE', 'PASSPHRASE_OLD']`. Never put a candidate on argv.
- **The new passphrase does NOT go in `.env`**. It goes to `/etc/credstore`, as a value distinct from D-1's key.
- **Rotation re-encryption hazards**: `--reupload` deletes the destination originals; the local DB must be deleted before and recreated after (an aborted Recreate started this arc); and `--new-passphrase=` on argv is visible in `/proc/*/cmdline`.
- **Disks**: `sda` is a drive-managed SMR disk (`WDC WD40EZAZ-00SF3B0`) holding the **sole local copy**. Stage on `nvme0n1p5` (`/`), never on `sda` or `sdc3`.
- **The owner must supply** the escrowed `PASSPHRASE` (from the printed sheet or password manager, **never** the Dropbox-synced copy, which is S-4), plus root and a window.

### Traps (carried verbatim in substance)

#### Duplicati and host

- **`duplicati-server --version` STARTS a server** on port 8200. Use `util/ad-hoc/2026-09-22_duplicati_literal_scan.py` and `util/ad-hoc/2026-09-22_recoverytool_verbs.py` instead.
- **`duplicati-server-util`** defaults to `--hosturl http://127.0.0.1:8200/` and takes `--password` / `change-password <new>` on argv. Never use it for anything secret-bearing. It *does* have a console prompt (`ServerUtil/Connection.cs`). The fix is the in-process client.
- **`duplicati-database-tool help` hides subcommand options**: `wipe-encryption` takes `--server-datafolder` on the subcommand, and defaults to the pcalnon profile. **`--dry-run` is not read-only**: it flips the copy to WAL and changes its hash, and with no DB argument it targets the default folder.
- **`enc-v1:` fields carry the SHA-256 of their key.** Test candidates offline on a copy. A server-based probe on an unencrypted copy "accepts" any key and poisons the copy.
- **`%` in a unit's `Environment=` is a specifier**: an unknown one voids the assignment and prints the value to the journal **and** `/var/log/syslog`. `EnvironmentFile=` is not a shell.
- **`PathExists=` re-triggers a oneshot after every termination**; `PathChanged=` does not (systemd v259 `path.c`).
- **Opening a live SQLite DB in place can checkpoint its WAL**. Use `util/ad-hoc/2026-09-21_duplicati_server_db_forensics.py`. A 4 KB `.sqlite` is not empty.
- **The wrapper passes every option as ONE argv word.** `DEBUG_MODE` echoes every `.env` line into the journal. Never enable it.
- **Never delete or move anything under `/mnt/Backups/Ubuntu/`.** The one owner-signed exception is P1 step 4's escrow copy-out. Never copy anything INTO `…/Backups/Yamaguchi/`.
- **`.claude/worktrees/curious-plotting-hummingbird` is DO NOT SWEEP.** It holds S-7, a world-readable `.env`. Remove only the file, after the fingerprint check; `git worktree remove` deletes it silently.
- **Hard rules from the D-8 handoff** [UNVERIFIED]:
  - never run a Duplicati binary;
  - never read secret files (`.env`, `~/.config/duplicati-backup/*`, `/etc/credstore/*`, `_yamaguchi_keys/`, history/viminfo files — `stat` only);
  - no journal or syslog greps.

#### Edit and PR mechanics

- **Never `git reset --soft origin/main`** on the salamander branch: it stages a revert of others' work. Rebuild from the pinned `6c23fdde` [UNVERIFIED — from the D-8 handoff]. Use two-dot `git diff origin/main..HEAD` to see what a stale branch would revert.
- **Anchored bulk edits can apply TWICE** when `old` is a substring of `new`. E's `edit()` guards this.
- **`open_signed_pr.py --add` splits on the first `:`**. Use `util/ad-hoc/2026-09-22_append_signed_commit.py` for paths containing `HH:MM:SS`.
- **`reports/` is excluded from pre-commit**, including `detect-private-key`. Screen additions there by hand.
- **`safe_merge.py` loses this lane** (it pins to a SHA). Use `gh pr merge N --squash --auto` plus `util/ad-hoc/2026-09-22_shepherd_automerge.bash`.
- **`tests/test_isolated_stack_script.py` `Errno 39` is a cleanup flake.** Re-run the job.
- **The isolation shim refuses compound shell**, `cd` or `git -C` to other checkouts, `git fetch` in some sessions, and anything containing the word `alias`. Put non-trivial logic in a scratch script.
- **Launch at most three subagents at a time** and archive their reports verbatim in `notes/` as they land.

### Primary-checkout coupling [NOT RE-PROBED — from the 09-21 handoff §4]

The live wrapper symlink `/home/duplicati/bin/duplicati-wrapper.bash` resolves into the owner's primary checkout. The snapshot timer also runs the primary's script as root. So a `git checkout` or `git pull` there changes what the service and root run next.

---

## Verification commands

```bash
# from a juniper-ml worktree
git fetch -q origin
git log --oneline origin/main..worktree-typed-skipping-salamander    # expect 2072e45a f90a87e7 2c9efe85
git merge-base origin/main worktree-typed-skipping-salamander         # expect 6c23fdde...
git diff --stat 6c23fdde origin/main -- notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md util/ad-hoc/smart_checks_backup-sda.bash util/ad-hoc/2026-09-22_backup-design-round2/   # expect empty
D=notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md
git show origin/main:$D | grep -c 'Re-decide D-2'        # 1 until the D-8 change lands
git show origin/main:$D | grep -c 'all 877 dindex'       # 2 until the D-8 change lands
git show origin/main:$D | grep -c '^### 10.1 Owner rulings'   # 1
gh pr list -R pcalnon/juniper-ml --state all --search "D-8 in:title"   # baseline: only #2099 (the handoff); any other PR means step 1 moved on
# in the salamander worktree only:
python3 util/ad-hoc/2026-09-24_amend_d8_and_repair_backup_design.py --self-test | tail -1
systemctl show -p ActiveState,MainPID,NRestarts duplicati.service   # read-only; expect active, MainPID=1397393 -- never stop/restart
```

If `MainPID` differs from 1397393, the armed `ExecStart` has fired. Stop treating the host facts as current and read `NRestarts` and `ss -tln` first.

---

## Dispositioned / closed items

| Item | Source | Disposition | Evidence |
| --- | --- | --- | --- |
| §1.1 reconcile lanes A1/B1/B2/B3 | 09-21 | DONE | ml#1999 `43980f13`; design §12 row "2026-09-22 Consensus round 1 reconciled in full" [VERIFIED 2026-10-03] |
| §1.2 round 2, §11, §12 | 09-21 | DONE (rounds 2 and 3) | round-2 record on main [VERIFIED 2026-10-03] |
| §1.3 flip status, remove §8 STOP, follow-up PR | 09-21 | DONE; the STOP is **re-introduced** by the 09-24 D-8 change (a different STOP) | status `VALIDATED (round 2)` on main [VERIFIED 2026-10-03] |
| §1.4 stage artifacts under `util/`, `util/systemd/`, `scripts/` | 09-21 | DONE | 13 artifacts on main [VERIFIED 2026-10-03] |
| §1.4 pause/resume client, `PW_FILE`, D2 unit, O-2 | 09-21 | OPEN → Remaining item 8 | [VERIFIED 2026-10-03: absent on main] |
| §1.5 owner items 2–6 (shell history, `data/` listing, root history, A0 premise, CUPS/Dropbox) | 09-21 | MOVED INTO DESIGN: §6 sink checklist, P0.5a, P0 steps 0/3 | design lines 506/510; P0.5a [VERIFIED 2026-10-03] |
| §1.5 owner item 1, TestPyPI rotation | 09-21 | OPEN → Remaining item 9 (not in the design) | grep `TestPyPI` on the design = 0 [VERIFIED 2026-10-03] |
| §1.5 item 7, decisions D-1…D-14 | 09-21 | 7 RULED (ml#2029); D-3/5/7/10/11/12/13 OPEN → item 5 | §10.1 [VERIFIED 2026-10-03] |
| §1.6 Appendix C corrections, MEMORY compaction | 09-21 | OPEN → item 10 | MEMORY.md 25,125 B [VERIFIED 2026-10-03] |
| 1. shepherd ml#2067 | 09-24 seven | DONE | merged `dcfc024f` 2026-09-24T08:19Z [VERIFIED 2026-10-03] |
| 2. archive that handoff | 09-24 seven | DONE | ml#2073 merged `fa951d39` [VERIFIED 2026-10-03] |
| 3. ml#2045 SMART divergence | 09-24 seven | RULED: adopted **but for its mode** (the 0755 mode was not adopted); lands with the D-8 change | E's §12 row on the branch; the branch diff touches the script [VERIFIED 2026-10-03] |
| P0.5a item 3 placement; the two `su - duplicati` shells (O-10) | 09-21 / seven-decisions | Item 3 MOVED to P0.5b. The shells are "since gone" per the branch design's note 10.1g (note sink-b), so `history -c` is moot | branch design note 10.1g [VERIFIED 2026-10-03 as branch text] |
| 4. stale P1 step 5 / P2 step 2 text | 09-24 seven | FOLDED INTO the D-8 change, still on main | E STALE list [VERIFIED 2026-10-03] |
| 5. "877 dindex" plus missing §12 rows | 09-24 seven | FOLDED INTO the D-8 change, still on main | E rows for ml#2029/2041/2057/2067 [VERIFIED 2026-10-03] |
| "P0 is the next action" | 09-24 seven | SUPERSEDED by the 09-24 STOP ruling: P0 is HELD | D-8 handoff [UNVERIFIED] |
| D-8 "scrub once after P1" | 09-24 seven / §10.1 | SUPERSEDED by the D-8 amendment (scrub = P0.5a item 4, before P0) | D-8 handoff [UNVERIFIED] |
| Archive the D-8 handoff | 09-24 D-8 | DONE | ml#2099 merged 2026-09-26 [VERIFIED 2026-10-03] |
| Six-subagent usage-limit trap, specifier-line count dissent, alias-reference dissent | 09-21 | HISTORY: recorded in the design's §11 by ml#1999 | — |

---

## Git state

All rows [VERIFIED 2026-10-03: `git worktree list`, `git log`].

- **`origin/main`**: `afb02801`.
- **`worktree-typed-skipping-salamander`**: worktree `juniper-ml/.claude/worktrees/typed-skipping-salamander`, tip `2072e45a`. It has **3 local-only commits, never pushed**, over `6c23fdde` (now 22 commits behind main). This is the only copy of the D-8 change and of R. The worktree's cleanliness was not probed, because the isolation shim refuses git against other worktrees.
- **`worktree-buzzing-painting-meteor`**: tip `af8111a5`. The 09-24 seven-decisions session's worktree. Its uncommitted handoff has since landed via ml#2073. A cleanup candidate, but only on an explicit owner merge signal.
- **`worktree-atomic-sauteeing-truffle`**: tip `3ee84ebb`. The 09-21 session's worktree. Its content landed via ml#1989. Same cleanup caveat.
- **`curious-plotting-hummingbird`** (`fix/handoff-passphrase-resolved`, `8f82ea5d`): **DO NOT SWEEP** (it holds S-7).
- **This consolidation** wrote only this file plus SUPERSEDED banners in the three source handoffs, on branch `docs/handoff-consolidation-2026-10-03`. It made no commits.
