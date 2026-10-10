# Round 1 — Lane A5 (citation fidelity)

<!-- markdownlint-disable -->

> **Archived verbatim.** A round-1 validation lane report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Its findings are dispositioned in `round1-reconciliation.md` in this directory. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

- **Instrument**: I read the plan (`notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`, sha256 `05d7a571d00e617d…`, re-hashed before reading) in full, and all ten `EX/` reports in full. I traced each in-scope claim to its report, then to the primary source through file reads at `cf711cf4`, `gh api` REST (PR, issue, compare, release, check-run and job-log endpoints), PyPI JSON, and read-only `ls`/`cat` on sibling worktrees and the host. I ran no scripts or tests and made no writes except this file.
- **Entry point**: the plan's claims → extraction reports → primary sources.
- **Sample**: about 190 in-scope claims traced to their reports, and about 80 of those re-traced to a primary source. **Mismatches: 0 BLOCKER, 2 MAJOR, 8 MINOR, 6 NIT.**

Aliases, each a filename: `…RECOVERY-PLAN.md` = `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`. `pr2114.md` = `.claude/worktrees/cached-swinging-summit/util/ad-hoc/2026-10-03_backup-phase-b-validation/pr2114.md`. `…round-42-consolidated.md`, `…ci-budget-arc-consolidated.md` and `…canopy-consolidated.md` = the `HANDOFF_2026-10-03_*` files in `prompts/thread-handoff_automated-prompts/`. `…EQUITIES-…-PLAN.md` = `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`. `…PROVENANCE-SPEC.md` = `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md`.

## Findings

| ID | Severity | Plan location | Plan says | Report says / primary source says | Proposed correction |
|---|---|---|---|---|---|
| A5-01 | MAJOR | §4 Wave 0 owner step 1 (P1-15); §10 P1 | "first run with **both** sticks … Then … SKIPPED …, then the class-1 drill (`…RECOVERY-PLAN.md` §6.3 step 8 …)". §10 P1 has no correction for that step. | The cited step says the opposite. `…RECOVERY-PLAN.md:255` reads "one run with no stick mounted (`SKIPPED`), one with a stick mounted (`OK`…)". `pr2114.md:13,20-23` (BLOCKER-1): one stick ends PARTIAL → FAILED rc 4, a multi-hour run with no stamp. `pr2114.md:92`: "reverse the order and say both sticks". `EX/extraction-P1-backup.md` §5 item 7 records this contradiction, but §10 dropped it. The plan's own text is right: the installer prints "OK run FIRST, with BOTH" (`util/install_juniper_backup_timer.bash:206`). | Cite the installer's acceptance text (`:205-212`) and P1-15 as the procedure. Add to §10 P1: "§6.3 step 8 (`:255`) on main is wrong: it says SKIPPED first and one stick. Follow the installer." |
| A5-02 | MAJOR | §2, P5 row, "Next item" | "S0.1(b); P5-01" | §3 row b is P1's tmpfs lane reports (P1-09). #434's uncommitted fixes are row c (`EX/extraction-P5-partition.md` §4 hazard 1, P5-09). A P5 session that follows §2 preserves the wrong artifact. S0.1's sweep of every row limits the damage. | "S0.1(c); P5-01" |
| A5-03 | MINOR | Overview point 2; §2 P3 row | "Two of those fixes (F2, F4) are not written yet" / "F2 and F4 are unwritten", framed as part of the obs/sc release | `…round-42-consolidated.md:43` lists three F-PRs (ml: F2, F6, F9, F10 + sc F3, F5; cascor: F3, F4, F5, F7, F9; data: F3, F5) and says "**None is fixed**". F4 is cascor's `src/tests/conftest.py` (`:211`), not an obs/sc fix. F2 and F4 are simply the two that must be validated before they reach a branch. | "None of round 42's F fixes is written (three PRs). F2 and F4 must be validated before they reach a branch." |
| A5-04 | MINOR | §10 P2 bullet 3 | "about 26 SHIP files, not 23" | `EX/extraction-P2-canopy.md` §5.2 marks 26 UNVERIFIED: it adds 3 for #694/#696/#697. `EX/extraction-P4-release-P11-k8s.md` §5.4 says those PRs did not move the count. `gh api …/juniper-canopy/compare/v0.8.1...main` finds 23 non-test `.py` files and 1 `.js` under `src/`, and 0 under `juniper_canopy/`. §10's own P4 bullet treats 23 as valid. | Drop the bullet, or write "23 ship-path `.py` files (24 with `ws_dash_bridge.js`); 58 commits". |
| A5-05 | MINOR | Success metric 4; §2 P4 row | 8 packages with unreleased fixes, including **ml** | `EX/extraction-P4-release-P11-k8s.md` §1b: ml "72; 0 pyproject". `pyproject.toml:113` has `packages = []`, and `MANIFEST.in` includes only `.gitignore`. `git log v0.10.0..HEAD -- pyproject.toml MANIFEST.in README.md` is empty. R-ML's content is unwritten. | 7. ml has nothing shippable until its floors and caps PR lands. |
| A5-06 | MINOR | §3 XC-MEM | "24.2–25.2 KB against a 24.4 KB read limit" | No report gives 24.2 or 24.4. The reports give 24,993 characters (`wc -m`) against a "~25,000" limit (P2-20, P3-30, P4-46) and 25,189 bytes (P1-22, P6-34). The plan sets decimal 25.2 KB against binary 24.4 KiB, which manufactures an overshoot. At 21:28Z, after the snapshot, the file measured 25,251 characters / 25,455 bytes. | "24,993 characters / 25,189 bytes against a ~25,000-character limit. Re-measure before any write." |
| A5-07 | MINOR | §2 P7 row; §10 P7 bullet 1 | "The census now discovers 39 consumers" | `EX/extraction-P7-logging.md` P7-02: a "`git grep` replication of discovery → … **39** at HEAD … Census not run". Its §8 says the counts were "replicated statically; the census was not run". | "A static replication finds 39; the census was not run." |
| A5-08 | MINOR | Overview point 1 headline | "There are no backups." | `…RECOVERY-PLAN.md:18` says "no working backup of any kind **since 2026-09-18**". `:23`: the 09-17/09-18 filesets survive and are the A0 recovery source (O-2, `:298`). | "No backup has completed since 2026-09-18." |
| A5-09 | MINOR | Appendix B row 17 | data#409 / cascor#582 / data#423 merges "P5-08/19/20" | P5-19 is **data#424** (generate-shortfall), a different question. §6 Group B asks it separately as P5 OD-8. | Remove P5-19 from row 17. |
| A5-10 | MINOR | §5, the R-DCLIENT → … → R-CANOPY-B row | "R-CANOPY-B 0.9.0", cut after R-CANOPY-A | `EX/extraction-P4-release-P11-k8s.md` P4-15 says the canopy cut now "(EQ targets 0.9.0)". `…EQUITIES-…-PLAN.md:32,407` reserves canopy 0.9.0 for W1.13. R-CANOPY-A goes first and consumes the next number. That is the R2-6 hazard (`EX/extraction-P5-partition.md` §4 item 6), which the plan applies only to P5 and DC-0.6. | Name R-CANOPY-B generically, or add a DC-0.6-style owner ruling. |
| A5-11 | NIT | Overview "Size" | "P3 36", total 374 | `EX/extraction-P3-defect-register.md` has 37 rows (P3-00..P3-36), and the plan's Appendix A places 37. P5 is counted by ID (32), not by table row (42 with P5-01a..j), though §12 says counts are table rows. | P3 37; total 375 IDs. |
| A5-12 | NIT | Overview point 4; metric 2; §3 rows a/f; XC-CLEAN | "At least eight" against ten rows a–j; "Any cleanup sweep would destroy them"; row a's "8 untracked files"; row f's "exist only in reflogs"; "worktrees … listed in Appendix B row 16" | Rows b and g die on reboot, row j on expiry, and row h by no sweep at all. The fold-in handoff (`…backup-phase-b-fold-in-pending.md:9`) says "8 untracked **paths**". `…canopy-consolidated.md:215-216` puts the four commits in reflogs **and worktree HEADs**. Row 16 lists item IDs, not worktrees. | "Ten artifacts, each lost to a sweep, a reboot or an expiry." Fix the row wording. |
| A5-13 | NIT | §4 Wave 0 owner order | P1-15 (step 8) first, then P1-16, then P1-14 (steps 1–7) | `…RECOVERY-PLAN.md:245` says "In this order", steps 1→9. `EX/extraction-P1-backup.md` §7 runs the owner items "in parallel". | State that the reorder is deliberate. |
| A5-14 | NIT | §5 DC-0.6 | P5's spec claims 0.6.0 for "W5/W11" | `…PROVENANCE-SPEC.md:527`: W5 = 0.6.0. `:532`: W11 = 0.6.1. | "W5 (W11 follows)" |
| A5-15 | NIT | §9 against §7.2 | §9 files P5-13 and P12-09 under "Quiet window"; §7.2 lists both as load-generating | P5-13's gate is WAIT-QUIET-WINDOW (`EX/extraction-P5-partition.md`). P12-09 *threatens* PF-3 through its load (`EX/extraction-P12-equities.md` §3). | Make P5-13 timing-sensitive in §7.2, and label P12-09 as load. |
| A5-16 | NIT | §2 P9 and P5 rows | "Round 6 never ran"; "ml#2064 skews every run's eval scalars" | `…ci-budget-arc-consolidated.md:1,32`: round 6 was launched 09-23 and killed before reporting. ml#2064's title says "a **cascor** run's eval scalars". | "Round 6 was killed before reporting"; "every cascor run's". |

## Checked and holds (short)

- **Overview.**
  - "19 → 11": `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md:1`.
  - The equities plan is referenced by no 10-03 or 10-04 handoff (grep finds 0). ml#2116 merged 10-03T19:06Z, after #2109 at 09:21Z.
  - No GitHub Release after 09-24 in any of the nine repos (releases API), and the PyPI spot-checks agree.
  - canopy v0.8.1 contains #532 (compare: ahead 91 / behind 0). The LEDGER's F-059 entry (`:9180`) blames #532.
  - Tier facts: `…RECOVERY-PLAN.md:18`, I-1.
- **§3.**
  - All 12 drafts are `cursor[bot]` drafts. Job logs: #2129 fails B105 on `OP_TOKEN` (tests `:61`); #2124 mypy + B106; #2127 black + B105; #2119, #2121, #2128 pass 22/22. #2125's body says "Do not merge #2122"; #698/#700 share a title; #699 is `dirty` (blob `2dd0b3d0`).
  - Rows a, c, d, e, g, h (32 `.prof`), i (103 files; `.git/info/exclude:18`) and j exist. Row c's worktree HEAD is #434's branch, `fix/arc-agi-review-round-429`.
  - XC-CRED sources: `HANDOFF_2026-09-21_backup-redesign-…:217`, `…canopy-consolidated.md:395`. The 20 KB ruling is dated 2026-09-15 (`feedback_memory_index_target_is_20kb.md`); the backup index line is corrected.
  - XC-P12: the four worktrees (15:59–16:02 CDT); the editable model 0.3.0 (15:56 CDT) and service-core's 0.5.0 dist-info; register `:1312–1330`. ml#2117 = `8b6edddd` at 11:16:51Z; every named file is under `HANDOFF_2026-09/`.
- **§4.**
  - The watchdog anchors: `yamaguchi_watchdog.py:296` (`required=True`) and test `:266`.
  - `isolated_stack.bash:507` sits inside `do_down`.
  - `safe_merge.py` holds nine budgets, four of them at 3300.
  - The data fix-forward branch is at `94ce8b1f`, diverged 2/6, with 0 PRs.
  - The T0 `SRC` re-point: main `:52` against worktree `:61`.
- **§5.** Every PR number and title checks out: ml#2086, #1974; data #436–#440 (9 ahead); cascor #659, #672, #683, #689, #690 (57 ahead, `main` = `95cdc562`); canopy #678, #683, #685, #694, #696, #697 (58 ahead). APD-OBS-001..004 sit under observability's `[Unreleased]`; F10 is at `CHANGELOG.md:64`; `dockerhub` holds 0 secrets.
- **§6 Group A, §9 and Appendix B** (except row 17): every ID resolves to its report with the meaning the plan gives it.
- **§10.** Every bullet checks out except A5-04 and A5-07. Probed directly: the STOP, note 6a `:233`, 169 against 172; FAQ `:11`, #684 = `f2147403`; the data lock (starlette 1.7.0, pydantic 2.13.5); #422 in v0.16.0; #178 closed via `workflow_dispatch`; the confirm step succeeded; the golden fixture path (old path 404); `ci.yml:1690`/`:1762`, ARCH `:42`, recurrence `starlette==1.6.0`; k8s `pushed_at` 10-03.

## Could not check

- Whether the 09-21 TestPyPI token (`TEST_TWINE_*`) and `JUNIPER_ML_TEST_PYPI` are the same credential. If they are, "rotate the four credentials" means three.
- Host-only claims: the watchdog being dark (the plan correctly hedges this), Phase C, and the quiet window after 21:05Z.
- Row b's location, given only as "tmpfs".
- Grants given in chat, and the contents of the in-flight P12 session.
- `detect.py`'s substantive-hunk count.
- The plan's "net −25 bytes" edit to `MEMORY.md`, which other sessions changed afterwards.

## What this report cannot support

- Appendix A, §7, §8, §11 and §12 were checked only where they bear on in-scope sections.
- GitHub was read at about 21:30Z, after the plan's snapshot. #701 is now `behind`, for example.
- No script or test was run, so every count is static.
- The severities are my judgement. A5-01 and A5-02 are MAJOR because following the cited row or step changes the action taken.
