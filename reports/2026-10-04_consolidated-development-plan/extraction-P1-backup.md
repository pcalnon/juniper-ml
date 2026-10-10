# Extraction — P1 backup-infrastructure arc

<!-- markdownlint-disable -->

> **Archived verbatim.** An extraction report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Corrections found by validation are in the `round*-reconciliation.md` files in this directory, and the plan's §10. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

measured_at: 2026-10-04T20:52Z–21:05Z (gh REST, `git` read-only in this worktree, file reads; no host probe)

Aliases, each a filename suffix: `…fold-in-pending.md` = `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_backup-phase-b-fold-in-pending.md` (current goal); `…arc-consolidated.md` = `…/HANDOFF_2026-10-03_backup-arc-consolidated.md`; `…RECOVERY-PLAN.md` = `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`; `…INTEGRATED-DESIGN.md` = `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`; `…ROUND-4-RECORD.md` = `notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-4-RECORD.md`. Lane reports `A.md`, `B.md`, `C.md`, `pr2114.md`, `pr2115.md`, `handoff_validation.md` live UNTRACKED in `.claude/worktrees/cached-swinging-summit/util/ad-hoc/2026-10-03_backup-phase-b-validation/`.

## 0. Sources read

- `…fold-in-pending.md`: full. `…arc-consolidated.md`: full. `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: full.
- `…RECOVERY-PLAN.md`: full (383 lines; §5 register, §6 phases A–E, §6.6 O-1..O-14, §8).
- `…INTEGRATED-DESIGN.md`: L1–30, §8 STOP block L1731–1825, P3/P4 L2270–2290, §10 table L2327–2360, Appendix C L2804–2817, plus greps. **Not read in full** (2,817 lines); §10.1 rulings were not re-read.
- `…ROUND-4-RECORD.md`: L1–100 (round-4 disposition, including the follow-up rows). Rounds 5–8 were not read.
- Phase B lane reports: `handoff_validation.md`, `pr2115.md` and `pr2114.md` in full. `A.md` L140–191, `B.md` L59–87 and `C.md` L93–143, plus all finding headings. `MANIFEST.sha256` was hash-checked. **Not read**: `BRIEF_COMMON.md`, `PR_BODY.md`, `COMMIT_BODY.txt`.
- Worktree artifacts, spot-read: `util/systemd/duplicati-env.contract` L18–41, plus greps of the wrapper, the test suite, the snapshot script and the re-key script.
- `HANDOFF_2026-10-03_ci-budget-arc-consolidated.md` L100–108 (its P1 hand-over). The 09-21 handoff was read by grep only.
- Auto-memory, read only: `project_backup_service_user_migration_2026-09-21.md` L73–215, and `MEMORY.md` (in session context, plus `stat`).
- GitHub: PRs #2109, #2111, #2113, #2114, #2115, #2119, #2121, #2122, #2124, #2125, #2127, #2128 and #2129 (state, files, bodies, CI, failing job logs), plus REST searches.
- **Not read**: the D-8 and seven-decisions handoffs (superseded; their items are carried by `…arc-consolidated.md` and by `…RECOVERY-PLAN.md` §8 Lane C), and the ml#2029 PR body.

## 1. Work items

| ID | Item | Source | Live status | Gate | Depends on | Repo(s) | Effort | Criticality |
|---|---|---|---|---|---|---|---|---|
| P1-01 | Make `yamaguchi_server_api.py export` obtain the single-operation token (or use Bearer `GET /backup/{id}`); make the stub refuse a token-less export; fix tests :216/:323 | `…fold-in-pending.md` item 1(a); `pr2115.md` B-1 | [VERIFIED 2026-10-04: main `:331` sends Bearer only; no `issuetoken`]. Fleet draft **#2129** (cursor[bot]) changes client + tests only; stub untouched; CI RED — bandit B105 on `OP_TOKEN` (tests:61); 1 commit behind main [VERIFIED: pulls/2129, check-runs, job log] | STARTABLE | — | juniper-ml | S | SAFETY |
| P1-02 | Set watchdog `--backup-id` `default=""` so a missing id writes a durable `JOB_MISSING`; update `tests/test_yamaguchi_watchdog.py:266`; say "deploy right after the primary sync" | `…fold-in-pending.md` item 1(b); `pr2115.md` D-1 | [VERIFIED: main `yamaguchi_watchdog.py:296` `required=True`; :266 pins "writes no record"; no PR]. Primary checkout at `cf711cf4` (contains 77ef6692) [VERIFIED: `git worktree list`] ⇒ installed unit (no `--backup-id` per lane, 10-03) now exits 2 with no record [NOT RE-PROBED — host state; documents only] | STARTABLE | ship with P1-01 | juniper-ml | S | SAFETY |
| P1-03 | Run one narrow validation lane on the fix-forward delta, then merge | `…fold-in-pending.md` item 1 | not run [VERIFIED: no PR beyond #2129] | BLOCKED-ON P1-01, P1-02 (merge on 10-03 approval [UNVERIFIED — transcript only]) | P1-01, P1-02 | juniper-ml | S | SAFETY |
| P1-04 | Record residue: six scripts default to job 2 (census:78, edit_setting:184, edit_sources:104, edit_target:139, config_record:45, build_fresh_job:118) | `…fold-in-pending.md` item 1 | [VERIFIED 2026-10-04: all six at cited lines]; draft #2128 documents them | STARTABLE | P1-01 | juniper-ml | S | HYGIENE |
| P1-05 | Update clearing script + `…INTEGRATED-DESIGN.md` prose per item 2's list; regenerate (`--from-repo`, then the clearing script); run every gate | `…fold-in-pending.md` item 2 | Worktree `cached-swinging-summit` (`6a1514e4`) holds it; manifest 10 OK / 8 changed = handoff [VERIFIED: hash check]; prose staleness per `handoff_validation.md` [NOT RE-PROBED line-by-line] | STARTABLE | P1-01 (item-3 wording) | juniper-ml | M | SAFETY |
| P1-06 | Correct `…RECOVERY-PLAN.md`: note 6a (rm, not revert), B4/B10/B11 names, B4 row, step 10/12 placement, §6.3 step 8, §8 round entry, §9, I-41 | `…fold-in-pending.md` item 3 | [VERIFIED: main :233 `systemctl revert`; :222/228/229 `2026-10-0X_`; :255 one-stick OK] | STARTABLE | — | juniper-ml | S | SAFETY |
| P1-07 | Fold uncarried lane residue R1–R6 (§6) into P1-05/P1-06 | `B.md`, `A.md`, `C.md`, `pr2114.md` | Absent from `…fold-in-pending.md` [VERIFIED: text]; worktree `…RECOVERY-PLAN.md` :275 still "blesses six paths" [VERIFIED] | STARTABLE | P1-05, P1-06 | juniper-ml | S | SAFETY |
| P1-08 | Run narrow round N+1 on the frozen fold-in delta (8 host-run artifacts + prose) | `…RECOVERY-PLAN.md` §6.2 L241 ("Round N+1 only if round N refutes"), §6.7 | Round N refuted (BLOCKER) [VERIFIED: `A.md`/`B.md`/`C.md`]; 8 artifacts changed after freeze [VERIFIED: manifest]; **not carried** | BLOCKED-ON P1-05..07 | P1-05..P1-07 | juniper-ml | M | SAFETY |
| P1-09 | Secret-scan, then archive Phase B reports verbatim into a `notes/` round record; first reconcile `C.md`/`pr2114.md` with lane originals | `…fold-in-pending.md` L14; `handoff_validation.md` DEFECT-5 | Untracked, this worktree only [VERIFIED: ls]; both files rewritten 10-04 14:26 CDT — whether restored UNVERIFIED; originals on tmpfs [NOT RE-PROBED — host] | STARTABLE | P1-08 | juniper-ml | S | DATA-INTEGRITY |
| P1-10 | Open Phase B PR from current main via `open_signed_pr.py` (rebuild ci.yml, REFERENCE.md, AGENTS.md, CHANGELOG from origin/main); merge — lifts the STOP | `…fold-in-pending.md` item 4 | No PR [VERIFIED: search]; `wip/backup-phase-a` local-only (branches API 404), 10 behind main [VERIFIED]; main moved on those 4 files [VERIFIED: diff] | BLOCKED-ON P1-08, P1-09; merge OWNER-ACTION (explicit OK advised) | P1-03 | juniper-ml | M | UNBLOCKER |
| P1-11 | B9: gitleaks content rule + pre-commit hook in own PR; owner enables `secret_scanning_non_provider_patterns` | `…RECOVERY-PLAN.md` B9; `…fold-in-pending.md` item 4 | Not started: `.gitleaks.toml` last changed ml#1999; no PR [VERIFIED] | STARTABLE (setting: OWNER-ACTION) | — | juniper-ml | S | SAFETY |
| P1-12 | B11: no-print history key-candidate extractor (0600 output, count only) | `…RECOVERY-PLAN.md` B11; `B.md` DEFECT-5 | Absent on main and worktree [VERIFIED: ls] | BLOCKED-ON P1-14 step-5 count ≠ 0 (or build speculatively) | P1-14 | juniper-ml | S | SAFETY |
| P1-13 | Triage the six backup fleet drafts: finish/supersede #2129; fix #2124/#2127 CI; land #2119/#2128 docs only after P1-01/02 | brief; `…fold-in-pending.md` item 1 | All OPEN drafts. #2119/#2121/#2128 green 22/22; #2124 red (mypy, bandit B106); #2127 red (black, bandit B105) [VERIFIED 2026-10-04] | OWNER-DECISION (fleet merges); CI fixes STARTABLE | P1-01 | juniper-ml | S | HYGIENE |
| P1-14 | Owner Phase C: P0.5a items 1, 7, 5 (S-7 rm, S-4 chmod 0600, escrow copy-out + sha compare); `apt install sqlite3`; count-only history probe; `data/` listing; sink checklist (purge nothing) | `…RECOVERY-PLAN.md` §6.3 steps 1–7 | None run at 2026-10-03 08:43Z [NOT RE-PROBED — host state; documents only] | OWNER-ACTION (host) | — | host | S (~20 min) | SAFETY |
| P1-15 | Owner: install tier 2; OK run FIRST with BOTH sticks mounted, then SKIPPED, then class-1 drill — first backup since 09-18 | `…RECOVERY-PLAN.md` §6.3 step 8; `pr2114.md` BLOCKER-1 | Unblocked: ml#2114 merged 2026-10-03T19:27Z; installer prints both-sticks/OK-first in both modes (main :198–217) [VERIFIED]; install [NOT RE-PROBED — host] | OWNER-ACTION (host) | — | host | S (+hours unattended) | SAFETY |
| P1-16 | Owner: rule O-10; `disable --now` the T0 snapshot timer before P1-10 merges and the primary syncs | `…RECOVERY-PLAN.md` §6.3 step 9, O-10 | Phase B re-points SRC to the empty server's DB (worktree `yamaguchi_server_db_snapshot.py:61` vs main `:52`) [VERIFIED]; root runs the primary's copy [NOT RE-PROBED — host] | OWNER-DECISION → OWNER-ACTION | before P1-10 merge | host | S | DATA-INTEGRITY |
| P1-17 | Owner: rotate the TestPyPI token captured in a 09-21 transcript | `…RECOVERY-PLAN.md` O-11/I-31 | No rotation recorded [VERIFIED: grep notes/; P4 handoff 0 hits] [NOT RE-PROBED — owner credential] | OWNER-ACTION (secrets) | — | PyPI | S | SAFETY |
| P1-18 | Owner Phase D: P0 per `…RECOVERY-PLAN.md` §6.4 steps 0–14 (rehearsal, A0, DBPath, credstore key + escrow, non-empty-TargetURL guard, AC-1/2/3/4/6/12/13) | `…RECOVERY-PLAN.md` §6.4 | HELD: STOP on main (`…INTEGRATED-DESIGN.md` L6, L1733) [VERIFIED] | BLOCKED-ON P1-10, P1-03, P1-14; O-1/2/7/13/14 | P1-10, P1-03, P1-14 | host | L | SAFETY |
| P1-19 | Phase E in design order: P1 (S-4 delete-forever, Dropbox audit), P2 (AC-5/7/9/12), §10.2 D-2 rotation, T3, P4 cleanup + user-lane removal PR | `…RECOVERY-PLAN.md` §6.5 | HELD [VERIFIED] | BLOCKED-ON P1-18 (+O-9, D-5) | P1-18 | host, juniper-ml | L | SAFETY |
| P1-20 | Apply Appendix C items 1–10 to their targets (README target is a host path) | `…INTEGRATED-DESIGN.md` L2817; `…arc-consolidated.md` item 10 | "None of items 1–10 has been applied" [VERIFIED main] | STARTABLE (README: OWNER-ACTION) | — | juniper-ml, host | S | HYGIENE |
| P1-21 | Disposition each D-12a inherited item (sdc4 probe, sdc2 grow, cloud reporting, records_sync, 7-repo drift tests, run_script_after, first_backup gate, YAM §8.21.5, sops escrow run) | `…INTEGRATED-DESIGN.md` note D-12a; `B.md` DEFECT-5 | "Carried today" on main [VERIFIED] | OWNER-DECISION (D-12) | — | juniper-ml, host | M | HYGIENE |
| P1-22 | Correct auto-memory ("Phase A/B landed; STOP cleared", "#2114/#2115 unmerged", "installer 1.1.0"); shrink MEMORY.md | discovered; `…arc-consolidated.md` item 10 | [VERIFIED 2026-10-04: project file L182 heading; MEMORY.md index line; MEMORY.md 25,189 B vs 20 KB] | STARTABLE | — | memory | S | SAFETY |
| P1-23 | Clean up superseded worktrees on owner signal (salamander, buzzing-painting-meteor, atomic-sauteeing-truffle, agent-ac10a004…, agent-ae6bdb20…) | `…arc-consolidated.md` Git state | All still registered [VERIFIED] | OWNER-DECISION | P1-10 (for cached-swinging-summit) | juniper-ml | S | HYGIENE |
| P1-24 | Rename, move or retire `notes/backup_tests_pre-and-post_reboot.md` (shell script, non-conforming name; pipes escrow sheet to `lpr`) | `HANDOFF_2026-10-03_ci-budget-arc-consolidated.md` L104 | On main since #1969 [VERIFIED] | OWNER-DECISION | — | juniper-ml | S | HYGIENE |
| P1-25 | Fix `pr2115.md` nits: `--base` override (N-2); `_unquote` sentence for P0 step 9 (N-5); watchdog usage exit 2 vs UNDETERMINED 2 | `pr2115.md` NIT, D-1 | Not carried; main unchanged [VERIFIED] | STARTABLE | P1-01 | juniper-ml | S | HYGIENE |
| P1-26 | Owner rules tier-2 scheduler semantics: pass only the mounted set, or keep the both-sticks rule; log absolute entries as unsupported (both are tagged blocks) | `pr2114.md` BLOCKER-1 (last para), DEFECT-2 | Main scheduler header :11 unchanged; both-sticks documented [VERIFIED] | OWNER-DECISION | — | juniper-ml | S | DATA-INTEGRITY |

**Session vs owner**:

- **Sessions may do**: P1-01..P1-13, P1-20 (repo part), P1-22 and P1-25, all repository-only.
- **Owner only**: P1-14..P1-19, the fleet merges, the worktree signal, the repository setting and every host action. Tier 1 stays down until P1-18.

## 2. Owner decisions pending

| ID | Question | Options; source recommendation | Blocks | Source |
|---|---|---|---|---|
| O-1 | 09-22 `.env` rewrite (64-char key, `_OLD`) | Treat both as superseded; random credstore key; retire any escrow entry calling it "the key" | P1-18 step 9 | `…RECOVERY-PLAN.md` §6.6 |
| O-2 | Recovery path | **A0**; A2 only if the 09-18 fileset is unreadable, then with the B10 helper | P1-18 step 7 | same |
| O-3 | Release phrase: "Read-only steps may run" vs "only reads" | Confirm; no widening needed | nothing in P0 | same |
| O-4 | Paused branch | RESOLVED de facto: owner merged ml#2113 [VERIFIED] | — | same |
| O-5 | D-3, D-5, D-7, D-10, D-11, D-12, D-13 | §10 table's recommendations | D-5 → T3 (P1-19); D-12 → P1-21 | `…INTEGRATED-DESIGN.md` §10 |
| O-6 | Merge approval for the fix-forward and Phase B | Granted 10-03 per `…fold-in-pending.md` [UNVERIFIED — transcript only]; P1-10 lifts the owner's own STOP, so confirm explicitly | P1-03, P1-10 | `…fold-in-pending.md` L9 |
| O-7 | P0.5b's fate (STOP exit condition) | Needed on Procedure A only | P1-10, P1-18 | `…RECOVERY-PLAN.md` §6.6 |
| O-8 | D-1 flag's durable home | Repository `DAEMON_OPTS` (B1, in worktree) | P1-10 | same |
| O-9 | S-3c: 811 frozen volumes + 10 old dlists | Re-encrypt as a second §10.2 pass | P1-19 | same |
| O-10 | Stop the T0 timer now | Yes, `disable --now` | P1-16 | same |
| O-11 | TestPyPI token | Rotate | P1-17 | same |
| O-12 | `.env` mode | `0640 root:duplicati` at `/etc/duplicati/env` (B8, in worktree) | P1-10 | same |
| O-13 | S-8 `additional-report-url` | Clear it; record the JWT retired | P1-18 step 11 (AC-3) | same |
| O-14 | `--aes-version` pin | 2 until §10.2, then 3 | P1-18 step 11 | same |
| N-1 | Restore the watchdog's durable record now | P1-02 (lane's recommendation), or owner deploys with an explicit id (a P2 step, which the STOP holds) | P1-02 | `pr2115.md` D-1 |
| N-2 | Tier-2 scheduler semantics | Lane: "owner decision; do not make it here" | P1-26 | `pr2114.md` |
| N-3 | Credential reader `O_NOFOLLOW` + uid check | Optional two-line hardening | P1-25 | `pr2115.md` N-1 |
| N-4 | Six fleet drafts on the backup clients | No source recommendation; land after the arc's fix-forward | P1-13 | brief |
| N-5 | Cleanup signal for five worktrees | — | P1-23 | `…arc-consolidated.md` |
| N-6 | `notes/backup_tests_pre-and-post_reboot.md` | P9 says it is P1's to resolve, and it is the owner's file | P1-24 | P9 handoff L104 |

## 3. Cross-path dependencies

- **P1 → P4**: P1-17's TestPyPI token is a release-path credential. `HANDOFF_2026-10-03_release-and-distribution-consolidated.md` never mentions it [VERIFIED: grep]. Rotating it touches no workflow, because CI publishes by OIDC.
- **P1 ↔ P2**: canopy docs drafts #2122/#2125 and backup drafts #2119/#2128 bump the same `docs/REFERENCE.md`, cheatsheet, overview and QUICK_START version headers in a coordinated sequence (#2128 body). P1-10's shared-file edits must rebase on whichever lands first.
- **P9 → P1**: P9 handed over P1-24. P9 is also soft-coupled through `ci.yml`, where P1-10, #2121, #2124 and #2127 each add suites.
- **P8/All → P1**: the rounds P1-03 and P1-08 share the account's usage windows, so launch them when no arc is mid-round. MEMORY.md is shared (P1-22), and the owner's sweeper arms drafts (P1-13).
- **P1 → others**: none hard.

## 4. Hazards

1. **Phase B's only copy is uncommitted.** It is 14 modified + 8 untracked files in `cached-swinging-summit`; branch `wip/backup-phase-a` was never pushed. Do not sweep it: `git worktree remove` would destroy it. The lane-report originals exist only on tmpfs.
2. **Main's plan text can destroy the installed unit.** `…RECOVERY-PLAN.md` note 6a on main says `systemctl revert`, which deletes the installed unit because a vendor unit exists. Nothing in Phase B's `main` text is runnable until P1-05/P1-06 land.
3. **The primary checkout is coupled to the host.** The primary sits at main's tip, so the watchdog is probably dark now (P1-02). After P1-10 merges and the primary syncs, root's T0 timer copies the empty server's DB over the recovery-source snapshot unless O-10 stops it first. The live wrapper symlink also resolves into the primary.
4. **`open_signed_pr.py --add` sends whole files.** The worktree's copies of ci.yml, REFERENCE.md, AGENTS.md and CHANGELOG predate #2114/#2115 and the fleet PRs.
5. **`stage_design_artifacts.py` can revert the fixes.** Without `--check`/`--from-repo` it writes the design's stale blocks over the fixed artifacts (I-33). `--check` exits 0 on drift; only "0 staged" means clean.
6. **Standing limits.**
   - Never start, stop or restart `duplicati.service`, and never run a Duplicati binary (`--version` starts a server). Never read a secret file.
   - Release limit 1: no history file is wiped before P0 step 3.
   - Release limit 2: no transcript is purged until every round, Phase B's included, is archived on main.
   - Nothing under `/mnt/Backups/Ubuntu/` moves.
7. **The sweeper can merge docs that go stale.** #2128 calls the pre-fix `export` "the live contract", and #2119 says the watchdog id has "no default". Either goes stale if merged before or after P1-01/P1-02 without an update.
8. **Memory says "STOP cleared".** A session that trusts it could start Phase D under the owner's STOP (P1-22).
9. **The two handoffs disagree on the merge tool.** `…fold-in-pending.md` says `safe_merge.py --execute`; `…arc-consolidated.md` says safe_merge loses this lane. Per memory, use native auto-merge only after safe_merge refuses.

## 5. Discrepancies

1. `…fold-in-pending.md` item 4 says "AGENTS.md's suite count is 172 on main". Main's AGENTS.md says "list of 169"; ci.yml has 172 `unittest` invocations [VERIFIED].
2. Its item 1 names only #2119/#2121 as fleet PRs on shared files. Also open: #2124 and #2127 (ci.yml, REFERENCE.md), #2128 (REFERENCE + 3 docs) and #2129 (the client itself, a partial fix-forward). #2119 touches 4 docs, not REFERENCE.md alone [VERIFIED].
3. Item 1 says to start a "new branch from current main". Fleet draft #2129 already exists: it covers 1(a) only, its CI is red, and it changes no stub [VERIFIED].
4. Auto-memory says "Phase A/B landed; STOP cleared". Its body says #2114/#2115 are "open… unmerged" (they merged 10-03) and the installer is "1.1.0" (the worktree has 1.2.0) [VERIFIED]. Main's design still has the STOP (28 hits; status HELD).
5. `handoff_validation.md` DEFECT-3 says step 9 "never said six". Main's and the worktree's `…RECOVERY-PLAN.md` :275 both say "blesses six paths" [VERIFIED], so `B.md` DEFECT-4.2 stands, and file 1 dropped the edit.
6. `…arc-consolidated.md` is stale on several points:
   - "Main's design has NO STOP" is false since ml#2113.
   - Items 1–3 are done (ml#2113).
   - Item 8's client and tier-2 deliverables are done (ml#2115/#2114).
   - Item 10's memory sub-items are done.
   - Its verification greps now return 0/0 [VERIFIED].
7. Two passages on main contradict ml#2114 [VERIFIED]:
   - `…INTEGRATED-DESIGN.md` L2277 says the installer and the failure unit "have not" landed, and "no reporter change is needed". The reporter is now 1.1.0 and retitled.
   - `…RECOVERY-PLAN.md` :255 says a one-stick run is OK.

## 6. Residue (open items the consolidated handoffs do not carry)

- **R1**: `…RECOVERY-PLAN.md` :275 still says "six". It should say seven (`B.md` DEFECT-4.2).
- **R2**: the artifacts' "P0 step N" uses the plan's numbering, not the design's (`B.md` DEFECT-4.1).
- **R3**: the creation of `/root/.ui-password.new` without a history trace, and its shred point, are undocumented (`B.md` NIT-1). The rehearsal also needs a throwaway key file (NIT-2).
- **R4**: `…INTEGRATED-DESIGN.md` P3 steps 1–2 are stale. The scheduler header (L1601 = `util/juniper-backup-scheduled.bash:11`) must change in both places (`pr2114.md` check 6).
- **R5**: the 102 path binds no port, yet the plan says "on an unused loopback port" (`A.md` NIT-1). Whether this is fixed is UNVERIFIED.
- **R6**: the re-key dry run prints its fallback `ExecStart` without saying it is the fallback (`C.md` N-6). Whether this is fixed is UNVERIFIED.
- **R7**: the post-fold-in round (P1-08).
- **R8**: report fidelity (P1-09).
- **R9**: memory (P1-22).
- **R10**: P9's notes file (P1-24).
- **R11**: `pr2115.md` nits (P1-25).
- **R12**: `pr2114.md` owner calls (P1-26).
- **R13**: the T0 SRC re-point combined with a primary sync (P1-16).
- **R14**: the watchdog is likely dark now (P1-02).

## 7. Path assessment

**Urgency: highest.**

- No tier has backed up since 09-18. Tier 2 has failed since 09-07, and Tier 3 was never built [NOT RE-PROBED — host].
- The sole local copy is on an SMR disk.

**Leverage**:

- P1-15 makes the first backup of any kind, at no session cost and with no P0 dependency.
- The fix-forward and Phase B unblock the only Tier 1 recovery (P1-18).

**Cost**:

- Sessions: about 2 S plus 3 M items, and two narrow rounds.
- Owner: about 20 min (Phase C), a few hours of an unattended tier-2 run, and about 2 h for Phase D.

**Next actions, in order**:

1. **Session**: one fix-forward PR covering P1-01, P1-02 and P1-04:
   - finish or supersede #2129;
   - rename `OP_TOKEN` to a `*_MARKER` name for bandit;
   - make the stub refuse a token-less export;
   - set `default=""` and update :266.

   Then P1-03 (lane, then merge).
2. **Owner, in parallel, now**: P1-15 (both sticks), P1-14, the O-10 ruling and P1-16, and P1-17.
3. **Session**:
   - First protect the Phase B worktree's only copy (hazard 1).
   - Then P1-05/06/07, then P1-08, then P1-09.
   - Then P1-10, merged on the owner's explicit OK. That lifts the STOP and opens P1-18.

## 8. What this report cannot support

- Any host fact: the service state, tier status, whether Phase C ran, the watchdog's output, the sticks' mounts, the timer, and the state of S-4/S-7. All of these come from `…RECOVERY-PLAN.md`, measured 2026-10-03 08:43Z.
- What the owner's 10-03 approval covers. That rests on a transcript only.
- The Phase B worktree's `git status`. The shim refused git there, so that state comes from `ls` and manifest hashes only.
- Line-level state of the worktree's prose beyond the greps cited.
- Whether `C.md`/`pr2114.md` were restored to the lane originals.
- Duplicati's token behaviour, which comes from the lanes' reading of the 2.4.0.0 source and was not re-read.
- The TestPyPI token's status.
- The effort estimates, which are judgement.

**Changed**: this file only (`reports/2026-10-04_consolidated-development-plan/extraction-P1-backup.md`).
