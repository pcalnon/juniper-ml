# Extraction — P9 CI-budget arc + P10 ci-tools re-evaluation

<!-- markdownlint-disable -->

> **Archived verbatim.** An extraction report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Corrections found by validation are in the `round*-reconciliation.md` files in this directory, and the plan's §10. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

measured_at: 2026-10-04T20:56:26Z – 21:02:55Z (juniper-ml `origin/main` = `cf711cf4` after `git fetch`; GitHub REST and PyPI only; no repo scripts run)

## 0. Sources read

Abbreviations below stand for these files (all paths from the juniper-ml root):

| Key | File | Read |
|---|---|---|
| P9C | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_ci-budget-arc-consolidated.md` | full |
| P10C | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_ci-tools-reevaluation-consolidated.md` | full |
| IDX | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md` | full |
| H0909 | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md` (**moved here by ml#2117**) | full (1281 lines) |
| H0911 | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` (**moved here by ml#2117**) | full (828 lines) |
| WALK | `notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md` | full |
| H0924B | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_ci-budget-arc-consensus-round-6-and-merge-ml2035.md` (superseded source) | full |
| H0924T | `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_ci-tools-reevaluation-all-nine-prs-merged-and-the-banner-still-says-three-are-open.md` (superseded source) | full |
| RREADME | `reports/2026-09-22_ci-budget-reeval-consensus/README.md` | full; the 16 lane reports: diff of line 4 only, bodies not read |
| CPROC | `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` | §4 only |
| ARCH | `util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/round4-fix/archive_round_reports.py` | grep `:42`, `:47`, `:138` |
| — | `.github/workflows/ci.yml` `:1600-1620`, `:1650-1763`; `util/safe_merge.py` (AST of the constants, `:268`) | partial |
| — | Cross-path greps only: P1 `HANDOFF_2026-10-03_backup-arc-consolidated.md` and `HANDOFF_2026-10-03_backup-phase-b-fold-in-pending.md`; P2 `HANDOFF_2026-10-03_canopy-consolidated.md` and `HANDOFF_2026-10-04_canopy-replay-player-fixed-and-live-verified-p2-items-2-to-7-next.md`; P4 `HANDOFF_2026-10-03_release-and-distribution-consolidated.md`; P6 `HANDOFF_2026-10-03_perf-lane-consolidated.md`; P8 `HANDOFF_2026-10-03_dynamic-workflow-harness-consolidated.md` | grep |
| — | Memory, read-only: `project_container_registry_rollout_2026-09-08.md` `:395-396` | partial |

**Not read**: the ci-tools lane reports in `reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/` (closed history); `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md` (OWNER 5's source); `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md` beyond a grep (P4-owned); the 19 round-6 scratch scripts and the killed session's transcripts (listed, not opened).

## 1. Work items

| ID | Item | Source | Live status | Gate | Depends on | Repo(s) | Effort | Criticality |
|---|---|---|---|---|---|---|---|---|
| P9-01 | Run consensus round 6: one background reviewer, briefed on round-5 corrections only, frozen at `c2bcb96c` | P9C item 1; H0909 `:1202` | [VERIFIED 2026-10-04: `git show origin/main:<H0909>` → `:1202` still the placeholder; no `round6.md` under `reports/…`; no open ml PR or remote branch for it] | STARTABLE (soft: P8 asks that rounds launch when no other arc is mid-round) | — | juniper-ml | M | HYGIENE |
| P9-02 | Repoint ARCH's `HANDOFF` constant to the moved H0909 path before archiving anything | NEW (ml#2117) | [VERIFIED 2026-10-04: ARCH `:42` holds the pre-move path; `:138` writes it as the `../../{HANDOFF}` header link; the link check at ci.yml `:1610-1620` excludes no `reports/`] | STARTABLE | before P9-03 | juniper-ml | S | UNBLOCKER |
| P9-03 | Archive round 6 as `reports/2026-09-22_ci-budget-reeval-consensus/round6.md` with a README row, in its own invocation and session id | P9C item 2 | [VERIFIED 2026-10-04: absent on main] | BLOCKED-ON P9-01, P9-02 | P9-01, P9-02 | juniper-ml | S | HYGIENE |
| P9-04 | Record round 6 in H0909 at its NEW path, in a follow-up PR; if it changed a number, disposition or action, apply the corrections and run round 7 | P9C item 3; CPROC §4 | [VERIFIED 2026-10-04: placeholder unchanged] | BLOCKED-ON P9-01 | P9-01 | juniper-ml | S (M with round 7) | HYGIENE |
| P9-05 | Optionally PATCH merged ml#2035's body, line 40 "[ ] consensus round 6 … in progress" | P9C item 3 | [VERIFIED 2026-10-04: `gh api pulls/2035 .body` line 40 unchanged] | BLOCKED-ON P9-01 | P9-01 | juniper-ml | S | HYGIENE |
| P9-06 | Merge the round-6 follow-up PR | P9C item 4 | [NOT RE-PROBED — no PR exists yet] | OWNER-ACTION (merge) | P9-04 | juniper-ml | S | HYGIENE |
| P9-07 | OWNER 1: add `SLACK_WEBHOOK_URL` to the eight sibling repos | H0909 `:88-95`; WALK §7.1 | [VERIFIED 2026-10-04: `actions/secrets` on all nine repos → only juniper-ml holds it; the 8 siblings hold none] | OWNER-ACTION (secrets) | — | 8 siblings | S | SAFETY (detection only) |
| P9-08 | OWNER 2: should CI budgets absorb runner queue? (4 of 9 at the 3300 ceiling) | H0909 `:96-125`; `util/safe_merge.py` dissent comment | [VERIFIED 2026-10-04: AST `REPO_TIMEOUTS` ml 2800, data 3300, cascor 2800, worker 2400, canopy 3300, cascor-client 3300, data-client 3300, deploy 1400, recurrence 2000; `TIMEOUT_CEILING` 3300; `safe_merge.py` unchanged since `c2bcb96c`] | OWNER-DECISION | input: P9-13 | juniper-ml (governs 9) | S | UNBLOCKER |
| P9-09 | OWNER 3: promote "Markdown Structure (advisory soak)" to required? Evidence says not yet | H0909 `:126-141`; ci.yml PROMOTION PATH | [CHANGED SINCE HANDOFF: still advisory, but the job name moved to ci.yml `:1690` (was `:1661`) and the final `exit 0` to `:1762` (was `:1733`); its base is still `pull_request.base.sha` (`:1711`), and `HEAD^1` is only the non-PR fallback (`:1713`)] | OWNER-DECISION; the "yes" path is BLOCKED-ON P9-12 plus its validation | P9-12 | juniper-ml | S | HYGIENE |
| P9-10 | OWNER 4: put cascor-client back into the budget pin? (ruled OUT 2026-09-15; the 09-22 re-measure says it would pass) | H0909 `:142-144`; WALK §1, §7.3 | [VERIFIED 2026-10-04: 3300 in `REPO_TIMEOUTS`; p90 1264 / max 1626 NOT RE-PROBED] | OWNER-DECISION | P9-13 (re-measure first) | juniper-ml | S | HYGIENE |
| P9-11 | OWNER 5: confirm the 22 flood-2 test PRs (production half absent) were abandoned deliberately, or reopen | H0909 `:145-151`, `:855-866` | [NOT RE-PROBED — closed-history census; from H0909, validated rounds 1-5] | OWNER-DECISION | — | juniper-ml, fleet | S | RESEARCH |
| P9-12 | NON-OWNER 1: stop `md_structure_check.py` (the ADVISORY engine) failing correct edits (C4 in-place renames, C2 wrapped prose) under the binding ACCEPTANCE, the 22-fence corpus control at `ba035cc9`, and the replay; then consensus-validate | H0909 `:154-225` | [VERIFIED 2026-10-04: engine and `tests/test_md_structure_check.py` last changed by #1955 `e7c191c1`, 2026-09-17] | STARTABLE | unblocks P9-09 "yes" | juniper-ml | L | UNBLOCKER |
| P9-13 | NON-OWNER 2: re-measure all nine budgets with `…_reprobe.py first-pass -n 30`. All OK → dated line in H0909 by PR. Otherwise report repo, max PR and queue share, and do not re-pin | H0909 `:226-242` | [NOT RE-PROBED — running scripts was out of scope here. Last measured 2026-09-22/23, and already tripped once: ml 2800 > 4×p90 2720] | STARTABLE | feeds P9-08, P9-10 | juniper-ml (reads 9 repos) | S | UNBLOCKER |
| P9-14 | Re-check the lockfile App-token arm on the next weekly PR | P9C item 8; H0909 `:245-246` | [VERIFIED 2026-10-04: n = 2, #1970 (09-21) and #2106 (opened 09-28, merged 10-02), both `juniper-release-train[bot]`; next weekly run due Mon 2026-10-05 ~08:26Z] | STARTABLE after 2026-10-05 | — | juniper-ml | S | HYGIENE |
| P9-15 | Repoint the pre-move references to H0909: its own PREFLIGHT and "THIS DOCUMENT IS" (`:56`, `:82`), `safe_merge.py:268`, ci.yml `:1674`, the reprobe and `wait_budget_mutation_check` docstrings (`:12`), and P9C's verification block | NEW (ml#2117) | [VERIFIED 2026-10-04: `git grep`] | STARTABLE (fold into P9-04's PR) | — | juniper-ml | S | HYGIENE |
| P9-16 | Clean up worktrees `ancient-yawning-biscuit` (unsigned `18d3d5e3`, never push; 19 round-6 scratch scripts) and `harmonic-swimming-planet` | P9C Git state; harmonic is NEW | [VERIFIED 2026-10-04: `git worktree list` → both exist (`18d3d5e3`, `6ccf80fa`); `round6/` holds 19 `.py` plus `__pycache__`] | OWNER-ACTION (cleanup signal) | after P9-01 | juniper-ml | S | HYGIENE |
| P9-17 | Disposition `notes/backup_tests_pre-and-post_reboot.md`, a shell script with a `.md` name and no `JUNIPER_` prefix | P9C Dependencies [ALSO P1]; H0909 `:1061-1063` | [VERIFIED 2026-10-04: on main (added #1969 `d721fc78`); 0 hits in P1's two handoffs] | STARTABLE (route to P1) | P1 | juniper-ml | S | HYGIENE |
| P10-01 | Make the post-merge edit to H0911's banner: three PRs merged (word it "byte-identical to final head"); drop the done and closed items; correct `:14` (tip → P4 file) and `:142`/`:382` (starlette 1.7.0) | P10C item 1 | [VERIFIED 2026-10-04: content last changed by `b6580529`; ml#2117 only renamed the file (100%); anchors still at `:14`, `:36`, `:45`, `:108`, `:142`, `:329`, `:333`, `:336`, `:343`, `:360`, `:382`] | STARTABLE | — | juniper-ml | S | HYGIENE |
| P10-02 | Merge that PR | P10C item 2 | [NOT RE-PROBED — no PR yet] | OWNER-ACTION (merge) | P10-01 | juniper-ml | S | HYGIENE |
| P10-03 | Diagnose the X7 flake (canopy#661): find where the worst gap falls against the stub's timeline before changing any bound | P10C item 3a; H0911 note f `:167-188` | [VERIFIED 2026-10-04: #661 open, 0 comments, last updated 2026-09-23 06:06Z; the test is unchanged since canopy#585 (2026-09-05); no open canopy PR names it] | STARTABLE | P2 (canopy files) | juniper-canopy | M | HYGIENE |
| P10-04 | 6f: add a `starlette>=1.7.0` floor to recurrence's `[test]` deps, drop the BlockingPortal ignore (`pyproject.toml:186`), run the suite under `error`, close #182 | P10C item 3b; H0911 note d | [VERIFIED 2026-10-04: #182 open; the starlette 1.7.0 wheel's testclient uses only `anyio.from_thread.BlockingPortal` (`:53`, `:388`, `:431`); main CI run 37066556852, job Test-3.12, installed starlette-1.7.0, anyio-4.15.1, fastapi-0.142.2; service-core 0.7.0 needs only `fastapi>=0.110`; but `requirements.lock:108` still pins `starlette==1.6.0` (last re-locked #163, 2026-09-10)] | STARTABLE | — | juniper-recurrence | S | HYGIENE |
| P10-05 | Optional: record outcomes in memory file `project_container_registry_rollout_2026-09-08.md` `:395` ("PRs opened: …") | P10C item 4 | [VERIFIED 2026-10-04: line unchanged; file mtime 2026-09-24] | STARTABLE (memory, outside git) | — | memory | S | HYGIENE |
| P10-06 | Owner cleanup signal for `jolly-wibbling-pearl` and H0911 note g's set | P10C item 5; H0911 note g | [VERIFIED 2026-10-04: `jolly-wibbling-pearl` at `d0582a21`, `luminous-inventing-crystal` and `tender-splashing-wigderson` exist; 30 of 30 sibling worktrees exist] | OWNER-ACTION | — | ecosystem | S | HYGIENE |
| P10-07 | Decide R4-B's proposal: add a §6 failure mode to CPROC for "a target that moves faster than a round" | H0911 `:541-544` | [VERIFIED 2026-10-04: no such text in CPROC] | OWNER-DECISION | — | juniper-ml | S | HYGIENE |
| P10-08 | Decide R4-B's proposal: graduate `ci_tools_pin_census_remote.py` into `util/`, with its self-test in CI | H0911 `:545-546` | [VERIFIED 2026-10-04: still under `util/ad-hoc/`; no `.github/` or `tests/` reference] | OWNER-DECISION | — | juniper-ml | M | HYGIENE |
| P10-09 | Decide whether H0911's termination deviation stands: round 5 changed a disposition and three numbers, and was confirmed by self-check, not a round 6 | H0911 `:443-447` ("The owner may judge that differently") | [NOT RE-PROBED — text only; unchanged on main] | OWNER-DECISION | — | juniper-ml | S | HYGIENE |
| P10-10 | Create the throwaway repository that tests empty-environment-name behaviour, only if Wave 4 takes the conditional shape | H0911 `:303-305`; DOCKERHUB procedure `:175` | [VERIFIED 2026-10-04: P10C files it under "MOVED TO P4", but P4's file has 0 hits for "throwaway" or "conditional"] | OWNER-ACTION (creates a repo); BLOCKED-ON P4's Wave-4 shape choice | P4 | new repo | S | UNBLOCKER |

## 2. Owner decisions pending

| ID | Question | Options; the source's recommendation | Blocks | Source |
|---|---|---|---|---|
| OD-1 (P9-07) | Set `SLACK_WEBHOOK_URL` on the 8 siblings? | Set it, or accept Actions-tab `::warning::` only. WALK §7.1: "the gap between … enforceable and … decorative" | Breach notification on 8 repos | H0909 OWNER 1; WALK §7 |
| OD-2 (P9-08) | Should budgets absorb runner queue? | Keep the raises and decide only the at-ceiling case; size on queue-free span; size on uncontended heads; raise the ceiling (risk above ~3600 s, the worker lease); keep the auto-merge net armed on a timeout refusal. No recommendation: HOLD and SHIP each carry one "against it" | Any re-pin of a stale at-ceiling budget; P9-13's re-pin branch | H0909 `:96-125` |
| OD-3 (P9-09) | Promote the advisory soak? | NOT YET (8 false findings in 62 PRs). If yes: P9-12 first, `exit "$rc"`, a ruleset context (never `needs:`), decide rc 2 and the early `exit 0`, base `HEAD^1` | Nothing urgent | H0909 `:126-141`; WALK §7.2 |
| OD-4 (P9-10) | Re-include cascor-client in the pin? | Ruled OUT 2026-09-15; the 09-22 re-measure says it would pass; "re-measure first" | — | H0909 `:142-144`, `:633-635` |
| OD-5 (P9-11) | The 22 flood-2 test PRs: abandoned deliberately? | Confirm or reopen; no recommendation | — | H0909 `:145-151` |
| OD-6 | Merge approval: P9-06, P10-02 | Per-session approval; the sweeper may merge unseen | Closing both records | P9C item 4; P10C item 2 |
| OD-7 | Worktree cleanup signal (P9-16, P10-06) | — | Disk hygiene | P9C, P10C Git state |
| OD-8 (P10-07, P10-08) | R4-B's two proposals | "left for a separate decision" | — | H0911 `:541-546` |
| OD-9 (P10-09) | Accept the ci-tools banner's termination deviation? | R5 recommended self-check; "the owner may judge that differently" | — | H0911 `:443-447` |
| OD-10 (P10-10) | Throwaway repo for Wave 4's conditional shape | B1 dissented ("startable"); filed owner-gated | P4 Wave 4 (conditional shape only) | H0911 `:549-551` |

## 3. Cross-path dependencies

- **P9-01 → P8 (soft)**: P8's file (`:86`) asks that consensus rounds launch only when no other arc is mid-round, because all paths share the usage windows.
- **P9 ↔ P10**: no shared item. They share merge mechanics: the owner's sweeper, strict rulesets, signed commits.
- **P9-12 ↔ P6**: adjacent engines, one word apart. P6's only structure-screen item is closed (ml#2000, perf-lane file `:233`), so the advisory engine has no live collision [VERIFIED 2026-10-04: grep].
- **P9-17 → P1**: the misnamed backup script is P1's artifact, and P1 does not carry it.
- **P10-03 ↔ P2**: X7 / canopy#661 is carried only by P10. P2's two handoffs have 0 hits for `661`/`X7` [VERIFIED 2026-10-04]. The sibling keepalive test belongs to P2's canopy-selection residue [NOT RE-PROBED].
- **P10 → P4**: Wave 4 step 3 (all five `dockerhub` environments still hold 0 secrets [VERIFIED 2026-10-04]), the Pi pull and OQ-2/3/4 (P4 carries them [VERIFIED: grep]), and P10-10 (P4 does not carry it).
- **P10-04 ↔ P4**: recurrence's image lock still pins starlette 1.6.0. A re-lock or release is P4's cadence. It does not block P10-04, because CI resolves fresh.
- **All paths ↔ ml#2117**: references to top-level `HANDOFF_2026-09-*` paths in any consolidated file may be stale.

## 4. Hazards

1. **ml#2117 moved both artifacts into `HANDOFF_2026-09/`.** Whole-file uploaders (`util/push_signed_commit.py --add LOCAL:PATH`) aimed at the old path would re-create a stale duplicate of a document of record. `ancient-yawning-biscuit` and `jolly-wibbling-pearl` hold copies at the old paths. Diff against `origin/main` before every push.
2. **ARCH as-is writes a dead link** into `round6.md`. The required `Documentation Links` check scans `reports/`. Re-taking rounds 1-5 would also revert ml#2117's header fix in 16 report files.
3. **Things to keep out of round 6**: never push `18d3d5e3` (unsigned); never upload the stale `round2-laneA/r2a_spans.py`; never brief the round-6 reviewer with the 19 scratch scripts.
4. **The sweeper arms and merges open PRs as `pcalnon`** with the default squash body, which is built from commit messages. Validate a branch before opening its PR.
5. **Strict ruleset, and `allow_update_branch=false`** [VERIFIED 2026-10-04]. An armed PR that falls BEHIND waits forever, so use `update-branch` one PR at a time. A `safe_merge` refusal disarms the net. Read the `MERGED` line, not the exit status.
6. **Promotion trap (OD-3)**: deleting the final `exit 0` alone leaves a check that cannot fail. Promote through the ruleset, never through `needs:`.
7. **Do not drop the 6f ignore before the floor exists**: the lock and local envs can still resolve starlette 1.6.0.
8. **The ceiling is filling**: a stale budget among the four at 3300 cannot be raised without OD-2.
9. **`worktree remove` deletes ignored files silently** (P9-16, P10-06).

## 5. Discrepancies

1. **Both consolidated files point at the pre-move paths.** P9C and P10C name `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_…` and `…HANDOFF_2026-09-11_…`, but ml#2117 (`8b6edddd`, 2026-10-04 11:16Z) renamed both into `HANDOFF_2026-09/`. The verification commands now mislead:
   - P9C's `git log -3 -- <old path>` shows `8b6edddd` on top. That falsely reads as "round 6 recorded".
   - P9C's `grep` hits no file.
   - P9C's "expect empty" `git diff --stat c2bcb96c origin/main -- …` is no longer empty.
   - P10C's `git log -2` shows `8b6edddd` on top, which reads as "banner edited". [VERIFIED 2026-10-04: `git show --stat -M 8b6edddd`]
2. **ml#2117 also edited line 4 of all 16 "verbatim" lane reports and of RREADME.** That is the header link, above each body's rule at `:10`, so the bodies are intact. RREADME `:17` names the archiver's one presentational change and does not mention this second edit.
3. **P9C's anchors for the soak moved**: `ci.yml:1661/:1733` are now `:1690/:1762`, shifted by the backup PRs #2114 and #2115.
4. **P10C's AMBIGUOUS anchor `REFERENCE.md:3029` no longer holds a ci-tools line.** The file grew by 51 net lines since `afb02801`; `:3085` is a candidate, unconfirmed because the census was not run. `test_ci_tools_drift.py:461` is unchanged.
5. **P10C 6f's fallback "or confirm its lock pins >=1.7.0" fails**: the lock pins `starlette==1.6.0`. CI already resolves 1.7.0, so only the floor route works.
6. **P10C's "the tip's banner is stale … P4's consolidation carries it" is moot, not carried.** The ten-prs-landed tip is itself marked "SUPERSEDED 2026-09-23", and P4's file never names it.

## 6. Residue: open items that neither consolidated file carries

- P10-07 and P10-08 (R4-B's proposals) and P10-09 (the termination deviation), from H0911.
- P10-10 (the throwaway repo): P10C moved it to P4, and P4 lacks it.
- P9-16's `harmonic-swimming-planet` worktree, the 09-09 origin session's worktree, still at `6ccf80fa`.
- P9-17: P9C disclaims it and P1 omits it.
- Accepted but never actioned test gaps (H0909 `:976-978`, `:1012`):
  - no mutation covers the reprobe's `sys.modules` registration;
  - first-pass's no-healthy-head branch is exercised by no check;
  - the 857 and 733 readings rest on uncommitted lane scratch.
- Two `.github/workflows/release-train.yml` sites keep the effect-level "GITHUB_TOKEN suppressed" wording. H0909 `:813-815` declares them outside the arc.
- Five floor-only ci-tools lines state a floor below CI's (H0911 `:233-236`). They were "deliberately not rewritten", so this is a record, not an action.

## 7. Path assessment

**P9.** Urgency is medium.
- The decaying part is the budget health (P9-13). Budgets went stale twice in 13 days, the last re-measure is 12 days old, and four sit at the ceiling. A stale budget refuses healthy PRs and disarms auto-merge.
- Round 6 is record hygiene. It has been pending 11 days, and its only cost so far is an "in progress" line.
- Leverage: P9-13 feeds OD-2 and OD-4, and P9-12 is the only route to OD-3's "yes".

Next actions:
1. **P9-13**: re-measure the budgets. Read-only, S.
2. **P9-02, then P9-01**: fix the archiver's path, then launch round 6 at a quiet point. Ship P9-03, P9-04, P9-05 and P9-15 in one follow-up PR.
3. **Surface OD-1 to OD-5**, with P9-13's output attached.

**P10.** Urgency is low.
- The banner is record hygiene.
- 6f is now verifiably unblocked and S.
- X7 costs CI re-runs and has never been diagnosed.

Next actions:
1. **P10-04**: 6f floor, drop the ignore, close #182.
2. **P10-01**: the banner edit at the new path. Its merge (P10-02) is owner-gated.
3. **P10-03**: X7 diagnosis, coordinated with P2.

## 8. What this report cannot support

- Current budget health. Nothing was re-measured.
- The census's current output. It was not run, and the `REFERENCE.md` line location is an inference.
- Any X7 failure since 2026-09-23. No CI logs were scanned.
- That every supported resolution gets starlette 1.7.0. Only one job, Python 3.12, was read.
- That no session is working P9 or P10 locally. Only remote branches and open PRs were checked.
- OWNER 5's facts, or round 6's outcome.
- That ARCH's stale link would fail CI. That is inferred from the exclude list, not executed.

**Changed**: this file only (new): `reports/2026-10-04_consolidated-development-plan/extraction-P9-ci-budget-P10-ci-tools.md`.
