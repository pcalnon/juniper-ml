# HANDOFF 2026-10-03 — defect register round 42, both lanes (CONSOLIDATED): the evidence PRs are all on `main`, but none of the owed validations, fix-forwards or the closes PR has started, and observability is unreleased

**Consolidated sources** (both in `prompts/thread-handoff_automated-prompts/`):

| Source | Self-declared validation | Role here |
|---|---|---|
| `HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md` (on `main` via juniper-ml#2102) | Validated by consensus in four rounds (lanes F/O/P), every lane PASS WITH CORRECTIONS, all corrections applied | **Governing source.** Its Appendices A–J are carried below in substance |
| `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md` (on `main` via juniper-ml#2097) | Validated in 5 rounds (`reports/2026-09-24_defect-register-round-42/handoff-followup-lane-round*-*.md`) | Evidence index for Lane F; the consolidated source already overrode it |

**Supersedes:** both files above. Their own predecessors were already superseded by the governing source: `HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md` (Lane R, document 1), `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md` (document 3, stale) and `HANDOFF_2026-09-23_defect-register-round-42-four-prs-armed-by-an-unseen-actor-two-merged-unvalidated.md`.

**Live probe:** 2026-10-03 08:34Z–08:55Z UTC, from worktree `snappy-strolling-waterfall` at `origin/main` `afb02801`, using `gh` (PR/branch/compare/contents/code-scanning APIs), `curl` against PyPI, and local `ls`/`cat`/`find`. No source claim was taken on trust where a cheap probe existed.

**Headline of what changed since 2026-09-25 03:45Z** [VERIFIED 2026-10-03: gh pr list merged:>=2026-09-25 in ml/data/cascor/canopy/deploy]:
- The three handoff/evidence PRs merged: juniper-ml#2102 (the governing source, `512a4b46`, 2026-09-25 03:51Z), #2089 (probes, `4d17ed59`, 09-26 09:28Z) and #2097 (Lane F evidence, `d941e99d`, 09-26 10:13Z). The owner's account added only `main` merges to #2089 and #2097.
- CodeQL's 7 high alerts on #2089/#2097 (4 `py/overly-permissive-file` in `data438-fixforward-round1-laneB/stripe_probe.py`, 3 `py/clear-text-logging-sensitive-data` in `surrogate_config_probe.py`/`sentry_deep_probe.py`) were **dismissed "used in tests"** at 2026-09-26 09:28:16–22Z, by the shared `pcalnon` account.
- **Nothing else in round 42 moved.** No data fix-forward PR was opened, there is no cascor#690 or canopy#685 validation report, no F fix-forward was made, there is no closes PR, the register is unchanged, and juniper-observability/service-core were not released. Since then every merge in data, cascor, canopy and deploy has been dependabot or a lockfile bump.

## Goal statement (paste as the new thread's first prompt)

Continue defect-register round 42 for the Juniper ecosystem. The register is `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, and the API primer is `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`. This file (`HANDOFF_2026-10-03_defect-register-round-42-consolidated.md`) governs. Read its "Context the remaining work needs" in full before acting.

There are two lanes. One successor should own both. If two sessions split them, follow the split rules under "Context → Lanes".
- **Lane R (register):** the register and its closes PR, the primer, the juniper-data fix-forward of #438, the fork-drift gate (`tests/test_service_fork_drift.py` plus its `docs/REFERENCE.md` bullet), `MEMORY.md` and the later arc items C-A…D-G.
- **Lane F (follow-up):** validating cascor#690 and canopy#685, and the F fix-forwards from the bytes-compare validation. The owner's "Key leaks" ruling "Fix everywhere now (Recommended)" ends "**Releases stay yours.**", so Lane F validates and fixes forward, and it surfaces releases rather than cutting them.

**Completed so far** (all VERIFIED 2026-10-03 by `gh` merge state):
- Lane R merged juniper-ml#2088 (`5af9d722`, the second register and primer fix-forward), #2081 (`7e8c7ff9`) and juniper-data#438 (`0f0f7e0e`, merged before its fixes landed, hence Work 1).
- Lane F merged cascor#688 (`7f4a7213`; #686 CLOSED), canopy#683 (`7ab994e5`), canopy#685 (`dc5ea02e`, **unvalidated**), juniper-ml#2086 (`c061a99f`), #2072 and #2077, cascor#689 (`b9484fef`) and data#440 (`26491531`), the last two validated pre-merge, and cascor#690 (`0fbb447a`, **unvalidated**).
- The handoffs and evidence are on `main`: #2102, #2089 and #2097, which include the archived reports and the 506 probe files under `util/ad-hoc/2026-09-24_round42_probes/`.
- juniper-data 0.16.0 is on PyPI (2026-09-24 18:35Z).

**First actions:**
1. Run "Verification commands".
2. **Get your own merge grant from the owner, in YOUR session.** A handoff cannot carry it (`feedback_headless_merge_approval_policy.md`; the ml#1118 incident), and then only with checks green on the current head and the validators cleared. In the same turn, ask the Appendix-B-style questions listed under Remaining work item 10, except the releases.
3. Run `ListAgents`. If a session is already working either lane, agree the split. **Never message session `bc31e993` ("defect reg [042116]")**: that is its own standing request. Sessions `2fba4397` ("defect reg [24f8d8]") and `8f86dec2` have handed off, and their consolidation-PR coordination is moot because #2102 merged.

**Remaining work** (suggested order. Items 2-5 do not wait for item 1. Item 7 waits only for item 6's filing of APD-ECO-013. Keep at most ONE open PR that uploads the register or the primer, built from fresh `main`):
1. **[R] Finish the data fix-forward.** Branch `fix/conditional-requests-round4-followups` at `94ce8b1f` [VERIFIED 2026-10-03: git ref], no PR [VERIFIED: `gh pr list --head`]. It is now **2 ahead / 4 behind** data `main` (`diverged`) [CHANGED SINCE HANDOFF: main gained #440 plus 3 dependabot merges; the only overlapping file is `CHANGELOG.md`]. Run pre-PR round 2 (two lanes) on `94ce8b1f`, then open the PR, then merge it with your grant.
   Agent-doable; the merge is owner-gated. Detail: "Context → Data fix-forward".
2. **[F] Validate cascor#690 post-merge** at `0fbb447a` (commits `c4e002d2`, `78e99414`) with two lanes, then fix forward in a NEW PR from `main`. Agent-doable. No validation report exists on `main` [VERIFIED 2026-10-03: `git ls-tree` of the reports dir]. Gates APD-CASCOR-008/-013.
3. **[F] Validate canopy#685 post-merge** at `dc5ea02e` with two lanes from a fresh tree (not the #685 worktree), then fix forward in a NEW PR from `main`. Agent-doable, but owner calls (a)-(c) can change it. Not started [VERIFIED 2026-10-03: no `canopy685-validation*` report]. Gates APD-ECO-014, canopy's half of APD-ECO-013 and F-CANOPY-061/-062.
4. **[F] The F fix-forwards** (table under "Context → Lane F"), as NEW PRs from fresh `main`: one juniper-ml PR (F2, F6, F9, F10, plus service-core's F3 and F5), one cascor PR (F3, F4, F5, F7, F9) and one data PR (F3, F5). Validate each with two lanes. **F2 and F4 must be validated BEFORE they reach a PR branch.** Agent-doable. None is fixed [VERIFIED 2026-10-03: `before_send_transaction` absent from `juniper-observability/juniper_observability/sentry.py`;
   F10's sentence at `juniper-observability/CHANGELOG.md:64`; cascor `src/tests/conftest.py` has no SENTRY line; the cascor and data `_ENCODING_PROBES` lack the surrogate pair; the cascor F7 test is still an AST match].
5. **[R] Validate #2088's unvalidated delta** `990ef3f9..2439d049` with two lanes, archive, and fix forward. Agent-doable, independent of the other items. [NOT RE-PROBED — from `HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md`, validated in 4 rounds.]
6. **[R] Open the closes PR early.** File APD-ECO-013, APD-ECO-014 and APD-CASCOR-014 OPEN, make the APD-DATA-055 update, and record the residue. Close rows only as their gates clear. Agent-doable; a PR that CLOSES a row is validated before it reaches a branch. The register still reads **136 rows | 100 fixed | 36 open, AGREE**, and the three ids are unfiled [VERIFIED 2026-10-03: `register_open_set.py`, `register_status_crosscheck.py`, grep count 0].
7. **[R] The fork-drift `surrogatepass` marker**, after item 6 files APD-ECO-013. Agent-doable.
8. **[R] Verify on the real services, then file** (a) the 422-echo defect, (b) the primer toy's copy of it, and (c) primer lines 4742-4743, which are stale. Correct the primer IN PLACE. Agent-doable.
9. **[R] PATCH the bodies of juniper-ml#2080 and #2088** with `gh api -X PATCH`. Not done [VERIFIED 2026-10-03: #2088's body still has "Extended beyond the lanes"; #2080's still has the "A-nit on" bullet and no "Applied by #2088" row]. Agent-doable.
10. **[R/F] Owner decisions: surface them, decide none.** **[F]:** the observability and service-core releases (ask only after item 4's juniper-ml PR validates) and who opens the cap/lock/floor PRs; canopy#685 calls (a)-(c); the stray canopy branches `pr-63`/`pr-683` (both still at `4caf9389` [VERIFIED 2026-10-03]); whether to purge test events from live Sentry. **[R]:** #437's breaking marker; APD-DATA-055's `If-Match` half;
    APD-ML-008's silent-path remedy; the register's nine parked rows; whether the CodeQL `paths-ignore` question still matters now that the highs are dismissed; the next juniper-data release; when to start the later arc items; worktree and branch cleanup.
11. **[R] Canopy-ledger hand-over** (`[ALSO P2]`). F-CANOPY-060…062 are still not in `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md` (it stops at 059) [VERIFIED 2026-10-03: grep]. Send #685's validation outcome and the stale "Nothing was loaded" copies to the P2 (canopy) session. If there is none, record them yourself.
    **Update 2026-10-08, from P2** (no P3 session was running to tell): P2's side of this item is done. The canopy ledger's Phase 10
    (ml#2157, `200c1393`) filed:
    - F-CANOPY-060 (P2, OPEN, no owner);
    - F-CANOPY-061 and -062, FIXED by canopy#685 without a live re-drive. Neither is observable through the page, and each is
      verified by #685's diff and tests;
    - the stale "Nothing was loaded" copies as **F-CANOPY-063** (P2, test only, OPEN). canopy's own alert sentence at `:8381` was
      declined.

    Item 3's validation of #685 stays P3's. If it finds #685 wrong, tell P2, so that F-CANOPY-061/-062 can be reopened.

**Key context:**
- The PR sweeper belongs to the owner ("Mine: fix forward"). It un-drafts, arms and update-branches PRs as `pcalnon`, and its merges are intended. Do not draft or disarm to hold a PR.
- An open PR can merge at any moment. When a validated merge matters, validate before the change reaches a PR branch.
- Before any merge, re-read the PR's commits, merge with `util/safe_merge.py` and read its `MERGED` line.
- The observability release gates the Sentry frame-locals fix reaching any running service: PyPI still serves juniper-observability **0.4.0** (2026-06-14) and juniper-service-core **0.7.0** (2026-08-31), and every consumer lock pins those [VERIFIED 2026-10-03: PyPI JSON and the lock lines].

## Dependencies on other paths

- **P2 (canopy):** items 3 and 11. F-CANOPY-060/-061/-062 and the stale copies of the "Nothing was loaded" sentence belong in the canopy E2E ledger. The keeper of those records is now P2's source `HANDOFF_2026-09-24_canopy-combined-round-1-done-fix-pass-owed.md` (juniper-ml#2096, MERGED `5b1a7c28` 2026-09-26 [VERIFIED 2026-10-03: gh]); see its F9, F10 and A2(a).
  Byte copies are on `main` at `reports/2026-09-24_canopy-combined-handoff-consensus/r1/predecessors/HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md` (`:53-66`) and `…/r1/DRAFT_r1.md:165-170` [VERIFIED 2026-10-03: `git ls-tree`]. P2's F10 records 061/062 as FIXED-BY #685 only after item 3 validates. P2 also owns fixing F-CANOPY-060 (no owner yet).
- **P4 (release and distribution):** `[ALSO P4]`.
  - (i) The **next juniper-data release** (carrying #438, item 1, #440 and X8's `equities_seq` 6.0.0) waits on item 1 merging and validating. 0.16.0 is still the latest release [VERIFIED 2026-10-03: `gh release list`, PyPI].
  - (ii) The 0.16.0 notify-consumers job failed with a 403 on the dispatch token, so juniper-recurrence was never notified. That is P4's item, carried by `HANDOFF_2026-09-24_data-0-16-0-on-pypi-and-pinned-the-stack-generates-equities-wave-4-waits-on-the-token.md` item 2. The next data release fails the same way until the token is fixed.
  - (iii) The observability/service-core releases are Lane F's owner question, but cutting them is release-train work.
- **P7 (logging redesign):** possible. Any juniper-observability release would bundle whatever P7 has landed under observability `[Unreleased]` by then. Today `[Unreleased]` holds only #2086's change and service-core holds #1974 and #2086 [VERIFIED 2026-10-03: `git log origin/main -- juniper-observability juniper-service-core`]. Coordinate release timing with P7.
- **P5 (partition arc):** none direct. D-B…D-D share juniper-data `routes/datasets.py` with item 1's branch, so any P5 change to that file must sequence after item 1.

## Context the remaining work needs

[NOT RE-PROBED — from `HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md`, validated in 4 consensus rounds] unless a claim carries its own tag.

### Lanes, coordination, policy

- **If two sessions split the lanes:** each merges only its own lane's PRs. They address each other by `ListAgents` name plus `[ref]`, since several sessions are named "defect reg". They exchange every PR number, merge SHA, validation summary, owner ruling (verbatim), and every juniper-ml `docs/REFERENCE.md` or root `CHANGELOG.md` section a PR touches.
- Lane F stays out of: the register; `tests/test_service_fork_drift.py`; `docs/REFERENCE.md`'s drift-gate section; `util/ad-hoc/2026-09-24_round42_probes/README.md`; `util/ad-hoc/2026-09-24_archive_round42_reports.py`; and Lane R's juniper-data branch.
- Lane R stays out of `juniper_data/api/security.py` and Lane F's branches.
- Lane F heads its reports with the archive header and sends Lane R their filenames, agent ids and its session's full UUID (for `SESSION_IDS`). Lane R adds the `MISSING` entries.
- After a split, only the lane tagging an owner question asks it; the other lane records the answer verbatim.
- Record every owner question, its options and the answer verbatim in the register.

### Uploads, commits, merges (traps)

- **Uploads are WHOLE-FILE.** Before every push: `git fetch`, `git log <base>..origin/main -- <paths>`, then rebuild each file from `origin/main`. Compare with `git show origin/main:<p> | diff - <p>`; note that `git diff origin/main -- <untracked>` fakes deletions.
  - On an OPEN PR, re-read the PR head's copy first (`gh api 'repos/pcalnon/<repo>/contents/<path>?ref=<headRefOid>'`): owner commits and update-branch merges land there.
  - For a shared `CHANGELOG.md` `[Unreleased]`, prove `main`'s lines are a subset of yours.
- **Signed commits have ONE parent** (GraphQL `createCommitOnBranch`), so a textual conflict cannot be merged away. Supersede from fresh `main`, as #686 → #688 did.
- **Signed pushes:** `util/push_signed_commit.py --expected-head <FULL 40-hex sha from gh>`. Never pass `git rev-parse HEAD`, which in several worktrees is a local copy. A run can create nothing, so check the remote ref after; a re-run with the same head is safe. Prefer `--commit-body-file`.
- **Where fixes go:** an OPEN PR gets a signed fixup; a MERGED PR gets a new PR from fresh `main` (`util/open_signed_pr.py`). Read state with `gh pr view <N> --json state,headRefOid,mergeCommit` at push time.
- **Validate every fix** (fixup or fix-forward PR) and every non-evidence PR (the fork-drift marker; cap/lock/floor PRs) with at least two lanes. A row closes only once its fix-forward's validation also holds. Evidence-only commits need only the archiver's `--check` plus CI.
- **Squash bodies:** the sweeper stores the DEFAULT squash body, and GitHub appends `Co-authored-by`.
  - Put `Allow-Symbol-Loss:` waivers in a COMMIT body in the range.
  - `git log -1 --format='%(trailers:key=…)'` prints an empty line on a squash; use `grep -c`, or `juniper-symbol-loss-check --base <parent> --head <sha>`.
  - juniper-data and juniper-cascor squash with `COMMIT_MESSAGES`, so every commit message lands on `main`.
  - A curated re-arm is `gh pr merge --disable-auto`, then `--auto --squash --match-head-commit <validated sha> --subject … --body-file …`. It needs the grant, and `--auto` on a MERGEABLE PR merges at once.
- **Merging:** `python3 util/safe_merge.py --repo <repo> --pr <N> --execute`. Read the `MERGED` line; exit 0 does not mean it merged.
- **`strict: true`:** after every move on `main`, run `gh api -X PUT repos/pcalnon/<repo>/pulls/<N>/update-branch -f expected_head_sha=<PR's full headRefOid>`; an armed BEHIND PR waits forever. Update-branch BEFORE building a CHANGELOG over a release cut (a 3-way merge once silently duplicated `## [0.16.0]`).
- `gh pr edit` is broken; use `gh api -X PATCH`.

### Register and primer

- **Never name an OPEN id on the register's §2 status list.** That is L177, "**Eighty-one of the 96 have since been fixed**" [VERIFIED 2026-10-03: grep, line 177], because `util/ad-hoc/register_status_crosscheck.py` reads every id on it as closed.
- **The primer is cited by bare line number, so edit it in place only.**
  - Model an editor on `util/ad-hoc/2026-09-24_register_round42_second_fixforward_round2.py`, which refuses to run twice and refuses line moves.
  - `util/ad-hoc/2026-09-24_register_primer_citation_census.py` counts bare numbers past 5758 (69 citations, 82 numbers); name a retired anchor in words.
  - Harness: `util/ad-hoc/2026-08-13_run_primer_examples.py --doc <primer> --venv <venv>` (62 tests). `util/ad-hoc/2026-09-24_primer_toy_pin_mutation_check.py` needs `--venv` and `--scratch`.
  - Venv: CPython 3.13.13 (JuniperCanopy1's interpreter) with fastapi 0.141.1, starlette 1.6.0, pydantic 2.13.4, httpx 0.28.1 and pytest 8.4.2. The old copy at `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/primer-venv` still exists [VERIFIED 2026-10-03: ls] but lives on tmpfs. Build your own:
    `/opt/miniforge3/envs/JuniperCanopy1/bin/python -m venv <dir>`, then `<dir>/bin/pip install fastapi==0.141.1 starlette==1.6.0 pydantic==2.13.4 httpx==0.28.1 pytest==8.4.2`.

### Running lanes and archiving

- **Lane:** a background `general-purpose` Agent. Launch the lanes in ONE message: A re-derives every claim from source, and B refutes (defaulting to REFUTED). Give each its own scratch subdirectory. Each is read-only, with no secret or email egress, compound shell in a script, and `/tmp` pruned. Report format as in `reports/2026-09-24_defect-register-round-42/register-fixforward2-round2-lane{A-reprobe,B-refute}.md`.
- **Archiving:** `util/ad-hoc/2026-09-24_archive_round42_reports.py`.
  - Add your session's full UUID to `SESSION_IDS` and each report to `MISSING`. Change the hard-coded 2026-09-24 `HEADER` for new reports.
  - Run `--check`, then run it without. Header: `<!-- Archived verbatim YYYY-MM-DD from subagent a<16 hex> of session <8 hex> (final message). -->` plus a blank line.
  - It refuses credential-shaped text or the owner's email. A REFUSE can be a false positive: characterize a match without printing it (length, case, prefix), and never edit a report to pass the scan.
  - [CHANGED SINCE HANDOFF] With #2102 merged, `main`'s copy is the one with the narrowed patterns and "owner-email" naming. fizzy's copy is byte-identical to `main`'s [VERIFIED 2026-10-03: cmp]. The "archive nothing into another PR until the consolidation PR merges" rule is moot: build on `main`.
  - Four Lane F reports are headed "(turn-ending report k of 5 …)", and `--check` skipping them is expected: `cascor686-implementation-report.md`, `cascor686-fixup-implementation-report.md`, `cascor688-implementation-report.md` and `cascor690-implementation-report.md`. Byte-compare them by hand before citing.
  - Archive a report only if its transcript ENDS with it: the last record is an `assistant` text-only message, `stop_reason` `end_turn`, and not an `isApiErrorMessage` record.
- **Agents:** a usage limit kills subagents; resume them with SendMessage from the spawning session only. An agent the USER stopped cannot be resumed: relaunch it fresh.

### Environment traps

- **Sentry:** set `SENTRY_SDK_DSN` (the shell exports it), `SENTRY_DSN`, `JUNIPER_CASCOR_SENTRY_DSN`, `JUNIPER_DATA_SENTRY_DSN`, `CANOPY_SENTRY_DSN` and `JUNIPER_CANOPY_SENTRY_DSN` to `""` in every test run and server. Set them empty, never unset: `load_dotenv` re-injects. Never use ports 8100, 8201 or 8050.
- **`/tmp` is a ~1M-inode tmpfs**: 39% at probe time [VERIFIED 2026-10-03: `df -i`], and it hit 100% on 2026-09-24. Extract only what you need, prune, and keep probes in `util/ad-hoc/`.
- **`pkill -f '<pattern>'` matches its own shell.** Use `pkill -A -f …`, or bracket a character (`'…1879[7]'`) as its own command. A pattern starting with `-` needs `--`.
- **Typed JSON escapes become real characters** in Write, Edit and SendMessage. Build such text with `chr()` and check it with `od -c` (this matters for F5).
- **Worktree-sandbox refusals are heuristic.** Refused forms include: `$(...)` feeding git or gh; loops or variables around git, gh, sed, find, sort or python arguments; heredocs in compound commands; the word "git" inside `python3 -c`; `-C` relative to a `cd`; `bash -c` with computed text; and `git -C`/`cd &&` git into another juniper-ml worktree or the shared checkout (read those with `cat`). Use plain absolute-path commands or a script file.
- **Never run** `util/worktree_cleanup.bash` (it pushes and runs `gh pr create`, recreating deleted branches unsigned) or `util/remove_stale_worktrees.bash` (no staleness predicate).

### Data fix-forward (item 1, Lane R)

- **State** [VERIFIED 2026-10-03: ref `94ce8b1fa8e229c92e8674a1074d518e59142488`; compare `main...94ce8b1f` ahead 2 / behind 4]. Two signed commits on #438's merge `0f0f7e0e`, both pushed by executor `a46e715a6801b98ca`; no PR.
  - `d1c66a11` answered `data438-round1-lane{A-reprobe,B-refute}.md`.
  - Pre-PR round 1 REFUTED `d1c66a11`: `data438-fixforward-round1-laneA-reprobe.md` (2 LOW, 9 NIT) and `data438-fixforward-round1-laneB-refute.md` (1 MEDIUM, 5 LOW, 6 NIT).
  - The MEDIUM was a regression the branch itself introduced: `record_access` ran on the event loop and blocked on the process-global `_version_lock` held for a whole save. One 80 MB create froze the service for 6.6 s (0.01 s on `main`), past the readiness probe's 5 s timeout.
  - `94ce8b1f` answers round 1 and is **unvalidated**. Its disposition report is `reports/2026-09-24_defect-register-round-42/data438-fixforward-round1-fix-report.md` (on `main`).
    - The stage-before-lock save (`stage_save`). `record_access` moved to its own single-thread executor, shut down on exit; `GET /{id}/access` waits for pending recordings.
    - It fixed a self-introduced regression: the store now reopens the root by path, with arm M86.
    - L-3 / lane A L-1 are documented, not remapped: unparseable metadata stays a 400, and a timezone-naive cursor or `created_after` stays a 500, as known issues, along with lane A N-9.
    - Numbers: unit 1923; coverage 97.60%; api+integration 118; harness 89 arms PASS (132 caught, 0 vacuous, 135 controls OK); counter 111/111; symbol-loss 2 findings, both waived; docs screen 19 warnings, 0 fail. The new tests fail 17/123 on `d1c66a11` and 39 on `0f0f7e0e`. The equivalence sweep was not re-run (`http_cache.py` untouched).
    - Lane B probes, `d1c66a11` → `94ce8b1f`:
      - read during a create: 7.4 s → 0.66-0.74 s;
      - `xproc_stall_probe.py` GET: 4.693 → 0.011 s;
      - health: 4.686 → 0.014 s;
      - `stripe_probe.py` deletes on a full volume: fail → succeed;
      - `access_suppression_probe.py`: 0 → 1;
      - `fault_survey.py`: identical on all 95 rows.
    - `stall_probe2.py` cannot measure the new head.
- **Noticed, not changed (round 2 weighs them):**
  - a large create still blocks the loop once for about 0.73 s, because `compute_checksum` runs on the loop (`datasets.py:446`);
  - every lock repeats its warning while `locks/` cannot be created;
  - `/access` and shutdown wait for the recorder with no time limit;
  - `local_fs.py` lines 175, 183, 237, 243-248 and 325-326 are untested defensive branches;
  - batch-create still logs a traceback for a symlinked metadata file;
  - a forked child shares the root's lock;
  - the ad-hoc harness would reformat under `ruff format`.
- **Round 2 spec.** Two lanes on `94ce8b1f`: the new commit `d1c66a11..94ce8b1f` in full, and `0f0f7e0e..94ce8b1f` for regressions, checked against both round-1 reports and the fix report. Also check the trial merge with data `main` (now 4 commits ahead; only `CHANGELOG.md` overlaps [VERIFIED 2026-10-03: compare file lists]). What `94ce8b1f` was asked to fix:
  - **MEDIUM (lane B M-1, with lane A L-2 and lane B L-4):** nothing on the loop may wait on `_version_lock` or a stripe. That means a dedicated executor for `record_access` (not `to_thread`), exceptions logged by type only, temp files written before the locks, and a test proving a read stays fast while another thread holds the lock.
    It must also correct data `docs/REFERENCE.md:1357-1362`, `juniper_data/storage/constants.py:45-47` and `juniper_data/storage/local_fs.py:200-202`, and state the cost in `CHANGELOG.md`.
  - **LOW:**
    - B L-1, deletes on an inode-exhausted volume: an inode-free lock fallback, removing legacy `*.meta.json.lock` (exact pattern, root only) at startup, a test double that fails `mkdir`, and scoping `CHANGELOG.md:93-94` and data `docs/REFERENCE.md:1374-1375`.
    - B L-2 / A N-4: open `locks/` once with `O_DIRECTORY|O_NOFOLLOW` and each stripe via `dir_fd`; test MX13, MX14, MX23 and MX24.
    - B L-3 / A L-1: scope "a storage fault is a 500" to a stored file leading out of the root, in the title, `CHANGELOG.md:117-118` and `routes/datasets.py:546-547`.
    - B L-5: a two-process create, a late named create, and late different content (MX10, MX1, MX9).
  - **NIT:** B N-1…N-6; A N-1, N-3, N-5, N-7, N-8 and N-9; `routes/datasets.py:1282` (`record_access` fires only on `GET /{id}` and the artifact download); the PR body's counts (16 of 17 base failures are their own defect, and `[0.16.0]` is 261 lines); `[0.16.0]` must stay byte-identical to tag `v0.16.0` (`util/ad-hoc/2026-09-24_verify_data_0_16_0_notes_match_tag.py`).
  - **Bar:** unit, coverage and api+integration; the harness plus an arm per new fix, and the counter; `juniper-symbol-loss-check --scope 'juniper_data/**' --base 0f0f7e0e` and the docs screen; lane B's probes against both heads; pre-commit on the changed files; the equivalence runs if `http_cache.py` is touched.
    - The preserved lane B probes (`util/ad-hoc/2026-09-24_round42_probes/data438-fixforward-round1-laneB/`) do not run as kept. `common.py` pins `S` to the author's tmpfs and starts servers via `S/scripts/run_in_tree.bash`, which was not kept.
    - To run them: re-point `S` at your scratch; build `head` and `main` trees with `git archive`; copy `serve.py` to `S/scripts/serve.py` (`common.py:44`); recreate `run_in_tree.bash`. The runner `cd`s into the tree; sets `PYTHONPATH`, `PYTHONDONTWRITEBYTECODE=1`, `JUNIPER_DATA_API_KEYS=""` and the six DSNs to `""`; checks that `juniper_data` imports from the tree; and execs JuniperData's python.
  - **Out of scope:** data438's F8 (#437's marker, the owner's); L7 (a known issue); data428 round-3 A1 F2/F4 (the closes PR files or declines them); `juniper_data/api/security.py`.
- **Ownership:** Lane R's branch owns data `http_cache.py`, `routes/datasets.py`, `storage/*`, `test_conditional_requests.py`, `api/app.py`, `docs/REFERENCE.md` and `docs/api/JUNIPER_DATA_API.md`, and it edits `CHANGELOG.md`. Lane F's data PR (F3, F5) also edits `CHANGELOG.md` `[Unreleased]`: open it after the fix-forward merges, or build on its head, and update-branch before merging.
- **If round 2 refutes, or you apply corrections pre-PR:** brief a new `task-executor` in YOUR session on the data worktree. It makes one signed commit with `--expected-head` set to the branch's current head, opens no PR, and is followed by round 3. LOW and NIT findings may instead be disclosed in the PR body as residue rather than fixed pre-PR.
  - Inputs: the round-2 reports, both round-1 reports, the fix report, and `git diff 0f0f7e0e <head>`.
  - Model the brief on the first executor's `user` records at 19:37:50.383Z (the regime: an unsigned local scratch commit for screens, never pushed; a whole-file signed upload; trailers; no PR) and 23:48:49.313Z (the round-1 fixes), in `/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-a46e715a6801b98ca.jsonl`. It still exists [VERIFIED 2026-10-03: ls].
    The 00:29:28.847Z record is a compaction summary, not a brief. Extract with a script, never with `splitlines()`.
  - The four tmpfs spec files still exist in that session's scratchpad [VERIFIED 2026-10-03: ls]: `data_round3_original_brief.md`, `data_round4_spec.md`, `data_round4_redirect.md` and `old_executor_summary.md`. Copy them out of tmpfs before use.
  - Correct TWO things in the old briefs: (1) brief 1's step 5 `--expected-head` is wrong; pass the branch's current FULL head, read from `gh`; (2) brief 2 says to unset the DSN variables; set them to `""`, never unset.
- **Where round 2's reports go:** after merging, archive `data438-fixforward-round2-*` into the closes PR or its follow-up. The consolidation PR (#2102) has merged, so it is no longer an option.
- **Opening the PR:** `gh pr create --repo pcalnon/juniper-data --head fix/conditional-requests-round4-followups --title "<line 1 of the draft without '# '>" --body-file <line 3 onward>`. The draft is `reports/2026-09-24_defect-register-round-42/data438-fixforward-pr-draft.md` (on `main`). Paste the title literally. `open_signed_pr.py` refuses an existing branch. Add round 2's reports (`data438-fixforward-round2-lane{A-reprobe,B-refute}.md`) to the body first.
  The draft's own "## Round 2" heading is the executor's second fix round, not the validation round.
- **The squash body:** data squashes with `COMMIT_MESSAGES`. That keeps `94ce8b1f`'s waiver `Allow-Symbol-Loss: method:LocalFSDatasetStore.save func:_file_lock_is_held`, but also carries `d1c66a11`'s unscoped "a storage fault is a 500". Either take the default body and record that subject as residue, or hand-write the body keeping the `Allow-Symbol-Loss:` line verbatim; dropping it turns `main` red.

### Lane F detail (items 2-4)

- **Evidence on `main`** (#2097) [VERIFIED 2026-10-03: `git ls-tree`]:
  - Reports in `reports/2026-09-24_defect-register-round-42/`: `bytes-compare-ml2086-data440-cascor689-{implementation-report,validation}.md`, `canopy683-{implementation-report,validation}.md`, `canopy685-implementation-report.md`, `cascor686-*`, `cascor688-{implementation-report,validation}.md`, `cascor690-{implementation-report,fixup-implementation-report}.md` and `handoff-followup-lane-round*-*.md`.
  - Probes in `util/ad-hoc/2026-09-24_round42_probes/{cascor686-v686,canopy683-v683,cascor688-v688,bytes-compare-ml2086-data440-cascor689-vbytes}/`. Read each one's arguments first: `make_nv1_tree.py` deletes its second argument, `fix_probe_pairs.py` rewrites a `compare_probe.py` in the working directory, and some write `work/`/`out/` beside themselves. Pass only fresh scratch paths.
  - Five harnesses: `util/ad-hoc/2026-09-24_cascor688_*.py` and `2026-09-24_cascor690_*.py`. Extract them into ONE directory, because one imports another by path.
  - Four scripts: `2026-09-24_copy_followup_lane_probe_scripts.py`, `…_archive_followup_handoff_validation.py`, `…_open_followup_handoff_pr.py` and `…_serve_scratch_juniper_data.bash`.
- **Item 2, cascor#690:** #688's fix-forward answering `cascor688-validation.md` (2 MEDIUM, 3 LOW, 2 NIT). The owner's account merged `main` into it (`81154187`) and it squash-merged unvalidated at 02:06:36Z.
  - The implementer's evidence is not independent: `cascor690-implementation-report.md` and `cascor690-fixup-implementation-report.md`.
  - Harnesses for `c4e002d2`: `2026-09-24_cascor688_fixforward_mutation_check.py` and `…_cascor688_realjd_error_texts.py`. For `78e99414`: `2026-09-24_cascor690_bool_stance_producer_table.py`, `…_realjd_probe.py` and `…_as_bool_stance_mutation_check.py`.
  - What it changed: shortfall detection keys on "Re-submit with allow_truncation=true", so a juniper-data 400 for a bad param is no longer shown as a shortfall. `_as_bool_stance` now parses strings like pydantic-core's `str_as_bool`; the old reader took `"f"` and `"n"` as true.
  - The `probe_realjd_*.py` probes need a live juniper-data. Use `bash util/ad-hoc/2026-09-24_serve_scratch_juniper_data.bash <tree> <scratch-dir> <port>`.
    - `<tree>` must be a scratch `git archive origin/main` export, never a checkout; the script refuses one.
    - It runs JuniperData's python under `timeout 1500`, with no keys, cap or truncation switch, and with metrics, rate limiting and Sentry off.
    - Stop it with `pkill -A -f …`.
- **Item 3, canopy#685:** merged from `e70b54dc`; the two commits after `4a8af2a0` touch only a probe script.
  - It closes APD-ECO-014, canopy's half of APD-ECO-013 (`str` `compare_digest` at `security.py:115`, `:273` and `csrf.py:91` became bytes at `:137`, `:300` and `csrf.py:97`), and `canopy683-validation.md` LOW3/LOW4 (F-CANOPY-061/-062).
  - Report: `canopy685-implementation-report.md`. The anonymous rate-limiter 500 needs `rate_limit_enabled`, which is off by default.
  - Fold in the stale comment at canopy **`src/tests/unit/backend/test_cascor_service_adapter_gate_coverage.py:49-50`**: "in CI, where only the stub client is installed" is false, because CI installs the real one. [CHANGED SINCE HANDOFF: the sources gave the path without `backend/`; the text is still present, VERIFIED 2026-10-03 via the contents API.]
  - Fold in any of owner calls (a)-(c) that change behaviour.
- **Item 4, the F table.** F1 was fixed by canopy#685; F8 (a `break` after `matched = True`) is killed by F3.

| Item | Sev. | Where | Fix |
|---|---|---|---|
| F2 | MEDIUM | observability `sentry.py` | `before_send_transaction=_strip_sensitive_headers` plus a test. Transactions skip `before_send`, so under `send_pii=True` (data only) they carry the raw `x-api-key`. |
| F3 | MEDIUM | service-core, data, cascor (canopy has one) | A spy test: 2+ keys, match first, `len(calls) == len(keys)`, bytes args. Data marking: see note F3 below. |
| F4 | MEDIUM | cascor `src/tests/conftest.py` | After `import sysconfig` (line 37 [VERIFIED 2026-10-03]), set `SENTRY_SDK_DSN`, `JUNIPER_CASCOR_SENTRY_DSN`, `SENTRY_DSN` to `""`; never unset. |
| F5 | LOW | `_ENCODING_PROBES`: service-core `juniper-service-core/tests/test_security.py:101`, data `juniper_data/tests/unit/test_security.py:34`, cascor `src/tests/unit/api/test_api_security.py:31` | Add the surrogate PAIR `chr(0xD83D) + chr(0xDD11)`, not U+1F511 (all three hold that). See note F5 below. |
| F6 | LOW | observability `tests/test_sentry.py` `_frames` | Add `in_app: False` frames plus one wire test with `in_app_exclude`. |
| F7 | LOW | cascor `test_main_sentry_no_local_variables.py` | Replace the AST match (`:33-35`) with a subprocess test asserting `get_client().options["include_local_variables"] is False`. Symbol loss: `Allow-Symbol-Loss:` in a COMMIT body. |
| F9 | NIT | `juniper-service-core/CHANGELOG.md:57-58`; cascor `CHANGELOG.md`; #689's body | Write "rejected: ASGI close 4001, HTTP 403 on the wire" in the new cascor PR and its commit body; PATCH #689's body. data#440 carried no such text. |
| F10 | NIT | observability `CHANGELOG.md:64` | "Consumers inherit both on upgrade, with no code change" is false: every lock pins `==0.4.0`. |

- **Note F3:** in data, mark both the existing and the new spy test `unit`, or put the new one in the marked `TestNonAsciiApiKey` (`:206`). `TestAPIKeyAuth` (`test_security.py:37`) is unmarked, and CI's `-m "unit and not slow"` (`ci.yml:287`) deselects it.
- **Note F5:** the pair and U+1F511 collide under UTF-16-LE with `surrogatepass`, and that collision is what kills the mutant. The comment "only total AND injective" is false. Check the file with `od -c`: the Write, Edit and SendMessage paths turn a typed escape into U+1F511. Canopy is out of scope: its `NON_ASCII` (`:172`) is checked only against a fixed `"key1"`, so the pair is inert there. Source: `bytes-compare-ml2086-data440-cascor689-validation.md:63-64`, `:131`.

The line anchors in the table are [VERIFIED 2026-10-03] for F4, F5 (cascor `:31`, data `:34`) and F10 (`:64`); the others are [NOT RE-PROBED]. F5 note: in data the `_ENCODING_PROBES` parametrize is at `:218`, in cascor at `:206`.

- **Release facts** (for the [F] release question) [VERIFIED 2026-10-03: contents API]:
  - Locks pin `juniper-observability==0.4.0` / `juniper-service-core==0.7.0`: data `requirements.lock:88/:90`; cascor `requirements.lock:63/:65` and `requirements-cpu.lock:129/:133` (the image's lock, `Dockerfile:41-42`); canopy `requirements.lock:79/:81`. Also recurrence `juniper-recurrence/juniper-recurrence/requirements.lock:70/:74` [NOT RE-PROBED].
  - Caps: observability `<0.5.0` at canopy `pyproject.toml:109` (data `:100` and cascor `:80` have floors only), plus recurrence `:79` and its client `:41/:46` [NOT RE-PROBED]. service-core `<0.8.0` at data `:110`, cascor `:105` and canopy `:119`, plus recurrence `:51` and juniper-ml `pyproject.toml:94` (`[tools]`).
  - Order (`feedback_semver_beats_consumer_cap_2026-09-05.md`): a cap PR that a bump crosses lands BEFORE the Release; lock and floor PRs come after the wheel is on PyPI.
  - Recurrence initialises no Sentry, so the frame-locals fix is moot there; it needs only the service-core release.
  - cascor#689 fixed only the CLI init (`main.py`), not the service path at `src/api/app.py:335`, which uses the shared `configure_sentry` and so needs the observability release.
  - Record why `surrogatepass` was chosen over `surrogateescape`, from `bytes-compare-…-validation.md`.
  - The release question's options, verbatim: (1) the owner prepares and cuts both releases; or (2) an agent opens version-bump and release-notes PRs at versions the owner names, and the owner cuts the Releases. Ask separately who opens the cap, lock and floor PRs. Never approve a deploy gate (`feedback_deploy_approvals_paul_manages.md`). Ask only after the juniper-ml F-PR validates: an earlier release ships F2's leak and F10's false sentence.
    `canopy685-implementation-report.md` measured the gap: until then, any unhandled exception during a keyed request records the caller's key.

### The closes PR (item 6) — gates, rows, residue

- **Gates** (close a row only after its PR merges AND its validation holds):
  - APD-CASCOR-008 and -013: item 2.
  - APD-DATA-017, -029, -032 and -057: item 1 merges and validates.
  - APD-ECO-014, canopy's half of APD-ECO-013, and F-CANOPY-061/-062's FIXED-BY: item 3.
  - The governing source overrides #2097's "APD-CASCOR-014 closes when F4 lands", which drops F4's validation gate.
- **File OPEN** (reserved, unfiled [VERIFIED 2026-10-03]). Re-verify each against source at `main`. The filing evidence is `pending-items-snapshot-2026-09-24T1110Z.md:11-20` plus `canopy685-implementation-report.md`.
  - **APD-ECO-013 (S):** a non-ASCII `X-API-Key` made the `str` `compare_digest` raise, and the 500 went to Sentry with local-variable capture of the real key.
    - Fixes: ml#2086, canopy#685, data#440 and cascor#689, all merged.
    - It stays open until #685 validates AND F2 and F3 are fixed. F5–F10 go on the row as residue unless they are fixed first.
    - Source: `bytes-compare-ml2086-data440-cascor689-validation.md`.
  - **APD-ECO-014 (S):** canopy's padded outbound keys leaked into client errors, logs, Sentry and API bodies: the 409 at `main.py:3712/:3714`, `recurrence_backend.py:219` → `:287`, and the adapter's `{"error": str(e)}`. That includes an ANONYMOUS read of the cascor key via `POST /api/train/start` with auth on. Fix: #685; close it once item 3 is cited.
  - **APD-CASCOR-014 (S), F4:** cascor tests that `import main` start the REAL Sentry SDK when a DSN is exported; 9 files sent 25 envelopes to a sink. The cause is `src/tests/unit/test_cfg_03_sentry_dsn_resolution.py:25` → `src/main.py:231`. #689's `include_local_variables=False` strips locals, but the events are still sent. Close it when F4 merges and validates.
- **Update, do not close:** APD-DATA-055. #438 fixed its lock half (`batch_delete` and `delete_expired` go through `delete_under_lock`); its `If-Match` half awaits the owner.
- **Quote** the "Key leaks" ruling verbatim from `reports/2026-09-24_defect-register-round-42/owner-ruling-key-leaks-verbatim.md`, extracted with `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py --topic key-leaks`. It was asked 10:22:00.792Z and answered 18:30:09.820Z: "Fix everywhere now (Recommended)".
- **Residue to record:**
  - cascor shortfall messages: the flag-off 422 is no longer a shortfall (#688), and the bad-param 400 is fixed by #690 (pending item 2).
  - Auto-start binds wholesale (`cascor686-fixup-implementation-report.md` item 2; `pending-items-snapshot-2026-09-24T1110Z.md:40`).
  - `current_dataset` after a partial inline start names the fetch, as `owner-rulings-verbatim.md` intends; canopy reads only `.dataset_type`. Record it, no row.
  - canopy#683 item 3: a whitespace-only env key makes `/docs` answer 200 (a disclosed change).
  - canopy's `util/ad-hoc/2026-09-23_blank_api_key_warning_mutation_check.py` has met its retire condition. Record only; retiring it is the owner's call.
  - F9's residue: #689's "4001 close" message reached `main` in `b9484fef` (cascor `CHANGELOG.md:594` still reads "closes 4001" [VERIFIED 2026-10-03]).
  - canopy#685's residue: the frame-locals gap until the release; calls (a)-(c); the rate-limiter 500 behind `rate_limit_enabled`; the stale comment (item 3).
  - data428 round 3 (`data428-round3-laneA1-security.md`): F3 is APD-DATA-056. F2 (the 8,192-byte cap parsed under `_version_lock`) and F4 (header limits) are recorded nowhere: file or decline each, with a reason.
  - Work 9's note that `2439d049`'s commit message ("which no lane named") is false.
  - Every owner answer received so far.
  - Cite Lane F's reports by filename; they are on `main` now.
  - Already recorded: cascor#678's stale squash message (register, about L1616).
- **Canopy items** go to the canopy ledger, not the register (item 11).
  - F-CANOPY-060: the refusal cut at `" The resulting dataset"` drops juniper-data's last sentence. Still at canopy `dashboard_manager.py:8410` [VERIFIED 2026-10-03]. The fix is to cut only at `" To accept it,"`. No owner.
  - 061 and 062: LOW3 and LOW4, fixed by #685, pending item 3.
  - No id: canopy's copies of #687's "Nothing was loaded" sentence at `src/frontend/dashboard_manager.py:8381` [VERIFIED 2026-10-03] and `src/tests/unit/frontend/test_start_fresh_refusal_and_modal_text.py:42`. They have been stale since #690 reworded cascor's sentence (`manager.py:4766` → `:4841`).
- **Validation of register PRs:** two lanes. A re-derives every filed row and residue item from source at `main`; B refutes. A PR that only files rows OPEN may be validated after it merges. A PR that CLOSES a row is validated BEFORE it reaches a branch. #2074 and #2080 were validated after merge and both refuted; #2088 was validated pre-PR.

### Item 5: #2088's delta `990ef3f9..2439d049`

- Fetch `git fetch origin refs/pull/2088/head` (`1f116c38` = `2439d049` plus a `main` merge).
- Checklist:
  - primer lines 4199, 5330, 5378, 5399, 5455, 5464, 5600, 5618, 5622, 5658-5659, 5682, 5699, 6084-6087, 6091, 6117-6120, 9880 and 9943-9944;
  - the register's `GET /{id}` wording, APD-CASCOR-013's Source cell, the §4 note, the rulings-block ids and APD-DATA-057's park bullet;
  - the seven `util/ad-hoc/` files that `git diff --stat 990ef3f9 2439d049` lists.
- Its fix-forward merges before the closes PR opens, or rides in it, or goes in the ONE register/primer follow-up after it.

### Item 7: the fork-drift marker

Re-verify every anchor at `main` first.
- **Pin a PAIR:** `encode("utf-8", "surrogatepass")` and `compare_digest(presented,`.
  - Not the bare word: every copy also carries it in a comment (service-core `:82`, data `:108`, cascor `:78`, canopy `:49`), and the matcher is a whole-file substring test (`tests/test_service_fork_drift.py:289`).
  - Code anchors: service-core `juniper_service_core/security.py:88`/`:91`; canopy `src/security.py:52`/`:137`; data `:115`/`:118`; cascor `:84`/`:87` (measured at the PR heads).
- Canopy's `.encode` sits only in `_compare_bytes` (`:42-52`, also used at `:300`). A revert to `compare_digest(presented, candidate)` at `:134-137` that keeps `_compare_bytes` passes even the pair; only F3's bytes-argument spy catches it.
- Canopy's CSRF compare (`src/csrf.py:91`, `:97`) is outside the site file.
- **Mutation-check:** delete EVERY `.encode("utf-8", "surrogatepass")` in a copy of each site file (two each in service-core, data and cascor; one in canopy) and confirm the guard fails.
- **PR CI will not catch a premature marker.** `ci.yml:500` skips fork sites without siblings, so it fails the next weekly `docs-full-check` on `main` instead. Test with `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` against a SCRATCH ecosystem root: `git archive origin/main` of data, cascor and canopy, plus your tree at `<root>/juniper-ml`.
- The same change:
  - corrects `tests/test_service_fork_drift.py:205-209` ("no behavioural test can tell them apart", which the F3 spy refutes, since it kills F8);
  - cites APD-ECO-013, so it lands with or after the closes PR;
  - updates every guard count: `docs/REFERENCE.md` near L2977, the register near L240, L252, L1106 and L1751, and the §2.3 guard table.

### Item 8: real-service verification

- **(a) The 422 echo.** Starlette's `JSONResponse` (`ensure_ascii=False`) raises `UnicodeEncodeError`, a `ValueError`, on a lone surrogate.
  - FastAPI's default app gives a plain-text 500.
  - juniper-data gives 400 `{"detail":"Invalid request parameters"}`: per-field detail lost, no Sentry event. The handler is at `juniper_data/api/app.py:214` on data `main` [VERIFIED 2026-10-03]; item 1 moves it to `:220`.
  - cascor gives 400, `VALIDATION_ERROR`, `detail: null`. That was measured in-process on fastapi 0.137.0 / starlette 1.0.0, which is not its locked pair (the handler is at `src/api/app.py:918` at `0fbb447a`).
  - Source: `handoff-2fba4397-round3-laneF-reprobe.md`, with probes at `util/ad-hoc/2026-09-24_round42_probes/handoff-2fba4397-round3-laneF/probe_{data,cascor,primer}.py`.
  - To measure it: serve data with the scratch-serve script (JuniperData's python is fastapi 0.137.0 / starlette 0.50.0; record the pair). For cascor, build a launcher (an `origin/main` export, uvicorn on a free port, DSNs `""`, a venv from `requirements-cpu.lock`), or file it as measured in-process.
  - It is a sibling of APD-DATA-056 and input to D-C.
- **(b)** The primer's `idempotent_jobs.py` has the default-handler form: a lone surrogate in `dataset_id` gives a plain-text 500, again on retry. No key record is ever created, so there is no replay defect.
- **(c)** Primer lines 4742-4743 say juniper-data registers no such handler; that has been stale since data#281. Correct (b) and (c) in place, in the same edit.

### Item 9: PR-body PATCHes

- juniper-ml#2080: delete body L69 (the "A-nit on `APD-ML-008`" bullet under "Rejected, with reasons", L65). Add to the "## Corrected" table (L19-L41): `| A-nit | APD-ML-008: "the service-core sites still run" | Applied by #2088 (ml2080-round1-laneA-reprobe.md N6) |`.
- juniper-ml#2088: in body L47, replace "**Extended beyond the lanes:**" with "**Named by round-2 lane B** (`register-fixforward2-round2-laneB-refute.md` N11, line 120):".
- cascor#689: F9's body PATCH (it still says "4001" [VERIFIED 2026-10-03: grep count 2]).

### Owner decisions (item 10), full text

Ask each as a question with its options (yes/no where none are listed), and record the question, the options and the answer verbatim in the register.
- **[F] The releases:** see "Release facts" above.
- **[F] canopy#685 calls:**
  - (a) An error that carries an HTTP status still passes its upstream text through. Type-only is a one-line change in `src/outbound_errors.py:57-61` (the file is 62 lines [VERIFIED 2026-10-03]).
  - (b) The key rule refuses a space or tab inside a key, which the clients would send.
  - (c) A blank `*_API_KEY_FILE` that shadows a real env var now sends no key.
- **[F] Stray canopy branches** `pr-63` and `pr-683` (both `4caf9389`, unsigned, pushed 22:55Z on 09-24, no PR, no transcript records the push). Do not delete them unasked.
- **[F] Purge this round's test events from the live Sentry project?** (yes/no). One run ended "Sentry is attempting to send 2 pending events".
- **[R] #437's breaking marker:** data `[Unreleased]` carries `equities_seq` 6.0.0 (a `dataset_id` change), and the notes renderer computes breaking = NO.
- **[R] APD-DATA-055's `If-Match` half.**
- **[R] APD-ML-008's silent-path remedy:** a variable only the drift step sets.
- **[R] The nine parked rows** ("filed 2026-09-24; awaiting an owner ruling, do not action", register §4 notes about L1619-L1637; rows about L1298-L1306): APD-ECO-009, -010, -011; APD-DATA-054, -055, -056; APD-ML-007, -008; APD-ECO-012. No round-42 handoff records asking any of them. (APD-DATA-057's park bullet closes it at the closes-PR gate, item 6, instead.) This file carries -055's `If-Match` half and -008's remedy above; ask all nine together, each with its own question.
- **[R] CodeQL** [CHANGED SINCE HANDOFF]: the 7 highs on #2089/#2097 were dismissed "used in tests" (alerts 843-846 and 876-878, 2026-09-26 09:28Z), and both PRs merged. The account is shared by the owner and every session, so record who dismissed them only if the owner says. (Source: `HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md`, Appendix B, CodeQL bullet.)
  What remains: 207 open lesser alerts (121 note, 86 warning) on round-42 probe/ad-hoc paths [VERIFIED 2026-10-03: code-scanning API, path filter `round42_probes|2026-09-24`], and the never-ruled options (a `paths-ignore` config in `.github/workflows/codeql.yml`, which is advanced setup with `+security-and-quality` and no config file, or a tarball). Never dismiss alerts or edit preserved probes yourself.
- **[R] The next juniper-data release** (yes/no; the owner cuts it): cut it once item 1 merges and validates?
- **[R] FYI: MEMORY.md** is 24,929 characters [VERIFIED 2026-10-03: `wc -m`], about 70 under the hard ~25,000 load limit. Every new row must be paid for by retiring entries (`feedback_memory_index_target_is_20kb.md`).
- **[R] The later arc items**, all ruled; the order is §0 of `HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`, and the owner decides when.
  - D-B (caching) is under way via item 1.
  - D-C, the error surface (APD-DATA-030/-031/-022; RFC 9457 from all three sources; item 8(a) belongs here).
  - D-D, lists and pagination (APD-DATA-026/-027/-028/-008).
  - D-E, idempotency (APD-ECO-001), after D-F.
  - D-F, storage pushdown (APD-DATA-019), after item 1, which rewrites `save_versioned` and the lock stripes.
  - D-G (APD-DATA-048/-049/-051); APD-DATA-047 was ratified at 1e11 and is closed.
  - D-B…D-D share `routes/datasets.py`: sequence them.
  - C-A, a per-call timeout (APD-ECO-003): its forks were killed, so relaunch it fresh.
  - C-B, TypedDict responses (APD-ECO-004).
  - C-C, the recurrence client using its server's models (APD-RCLIENT-004).
  - C-A and C-B collide on 38 `def` lines: sequence them.
  - Round 39 §0.4's two no-row items: `equities_seq`'s `data_quality` has no consumer in juniper-recurrence, and `val_ratio`'s removal from canopy's sidebar is recorded only in the register's §4.9 preamble.
- **[R/F] Worktree and branch cleanup:** see "Git state".

## Verification commands

From a juniper-ml worktree fast-forwarded to `origin/main`:

```bash
git fetch origin && git merge-base --is-ancestor d941e99d HEAD && echo has-2097   # #2097, #2089, #2102 all on main
gh api graphql -f query='query { a: repository(owner:"pcalnon", name:"juniper-cascor") { p690: pullRequest(number:690) { state mergeCommit { oid } } } b: repository(owner:"pcalnon", name:"juniper-canopy") { p685: pullRequest(number:685) { state mergeCommit { oid } } } }'   # MERGED 0fbb447a / dc5ea02e
gh api repos/pcalnon/juniper-data/git/ref/heads/fix/conditional-requests-round4-followups --jq .object.sha   # 94ce8b1f… on 2026-10-03
gh pr list --repo pcalnon/juniper-data --head fix/conditional-requests-round4-followups --state all   # [] on 2026-10-03
gh api repos/pcalnon/juniper-data/compare/main...94ce8b1fa8e229c92e8674a1074d518e59142488 --jq '"ahead \(.ahead_by) behind \(.behind_by)"'   # ahead 2 behind 4 on 2026-10-03
gh pr list --repo pcalnon/juniper-ml --state open; gh pr list --repo pcalnon/juniper-cascor --state open; gh pr list --repo pcalnon/juniper-canopy --state open; gh pr list --repo pcalnon/juniper-data --state open   # only dependabot on 2026-10-03
ls reports/2026-09-24_defect-register-round-42/ | grep -e cascor690-valid -e canopy685-valid -e data438-fixforward-round2   # empty on 2026-10-03 = items 1-3 not started
python3 util/ad-hoc/register_open_set.py | grep 'rows |'    # 136 rows | 100 fixed | 36 open
python3 util/ad-hoc/register_status_crosscheck.py | tail -1   # AGREE
grep -c -e APD-ECO-013 -e APD-ECO-014 -e APD-CASCOR-014 notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md   # 0 = closes PR not opened
grep -n before_send_transaction juniper-observability/juniper_observability/sentry.py   # empty = F2 unfixed
curl -s https://pypi.org/pypi/juniper-observability/json | python3 -c 'import sys,json; print(json.load(sys.stdin)["info"]["version"])'   # 0.4.0 = unreleased
python3 util/ad-hoc/2026-09-24_archive_round42_reports.py --check | grep -c 'OK    '   # positive; 0 means it exited early (a cited transcript is gone)
python3 -m unittest tests/test_service_fork_drift.py   # Ran 11 tests … OK (skipped=3)
ls /home/pcalnon/Development/python/Juniper/worktrees/ | grep -e shortfall-mixed -e secret-leaks -e bytes-compare -e blank-key-678 -e sentry-locals -e round3-followups
df -i /tmp | tail -1
```

[VERIFIED 2026-10-03: run by validator] The archiver `--check` exited 0 with 73 `OK` lines, the four "turn-ending" reports skipped as predicted; the fork-drift unittest printed "Ran 11 tests … OK (skipped=3)".

## Dispositioned / closed items

In the Source column, "governing" means `HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md` and "follow-up" means `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`.

| Item | Source | Disposition | Evidence |
|---|---|---|---|
| First action 5: land #2097 | governing §First actions | Done | MERGED `d941e99d` 2026-09-26 10:13Z |
| First action 5: land the consolidation PR | governing | Done | #2102 MERGED `512a4b46` 2026-09-25 03:51Z |
| First action 5: land #2089 | governing | Done | MERGED `4d17ed59` 2026-09-26 09:28Z; `util/ad-hoc/2026-09-24_round42_probes/` holds 506 files on `main` (with #2081's and #2097's) |
| CodeQL blocks on #2089/#2097 | governing App. B | Highs dismissed, PRs merged; residual question kept (item 10) | Alerts 843-846, 876-878 "used in tests" |
| Contact [24f8d8] / coordinate the consolidation PR | governing First actions 2-3 | Moot | #2102 merged; fizzy content = `main` (cmp) |
| Follow-up lane Step 0 (message [24f8d8], get the consolidated path) | follow-up lane | Moot | Consolidated handoff on `main` |
| Ship fizzy's unarchived reports / frozen copies | governing Git status | Done | Round 1-4 reports and `handoff-frozen/` r1-r4 on `main` |
| Round 1-4 handoff-validation probes onto #2089 | governing Git status | Done | `86b497cb` in #2089, merged |
| Archive-only-into-consolidation-PR rule | governing Key context | Moot | #2102 merged; build on `main` |
| cascor#689 and data#440 validation | both | Done pre-merge | `bytes-compare-…-validation.md` |
| cascor#689 / data#440 fixups for F3/F5/F7/F9 (follow-up lane) | follow-up OPEN 4 | Superseded by new-PR fix-forwards (item 4) | Both MERGED |
| "APD-CASCOR-014 closes when F4 lands" | follow-up | Overridden: needs F4's validation too | governing App. A |
| Lane R files in fizzy, `happy-skipping-hollerith` files | both Git status | Shipped | #2102 and #2097 merged |
| F1 | follow-up OPEN 4 | Fixed by canopy#685 | — |
| F8 | follow-up OPEN 4 | Killed by F3 (item 4) | — |
| Document 3's items | governing App. I | History; mapped there | `HANDOFF_2026-09-24_…second-fixforward-owed.md` |
| #2096 keeper of canopy records | governing App. A | Merged; records on `main` | `5b1a7c28`; paths in Dependencies |
| juniper-data 0.16.0 publish | both | Done | PyPI 0.16.0, 2026-09-24 18:35Z |
| `/tmp` at 83% | governing | Now 39% | `df -i` |

## Git state

Probed 2026-10-03.
- **juniper-ml:** `main` at `afb02801`. No open PR [VERIFIED]. Branch `docs/canopy-e2e-handoff-2026-09-24` still exists (`dd4413e5`, P2's) [VERIFIED].
- **Session worktrees** (all exist [VERIFIED: ls]). Removal needs the owner's go-ahead (`feedback_worktree_cleanup_only_on_explicit_merge_2026-05-15.md`). Re-check `git status` first; never `--force`. `worktree remove` deletes ignored files.
  - `juniper-ml/.claude/worktrees/fizzy-hugging-dream` (Lane R): holds 3 unsigned local scratch commits (`4c7c5b3e`, `1bfff3cd`, `ee0b9382`; content = #2088's) — never push them. Nothing written after #2102 is unshipped [VERIFIED: `find -newermt` lists only 4 files, all identical on `main`]. Now a cleanup candidate.
  - `…/happy-skipping-hollerith` (Lane F): nothing newer than #2097 [VERIFIED: find]. #2097 merged, so it is a cleanup candidate.
  - `…/hazy-beaming-map` (document 3, session `8f86dec2`): no work lost; a cleanup candidate.
- **Shared worktrees** under `/home/pcalnon/Development/python/Juniper/worktrees/` (all 11 exist [VERIFIED: ls]; internal HEAD/dirty state [NOT RE-PROBED — the sandbox refuses `git -C` there]):
  - `juniper-data--fix--conditional-requests-round3-followups--20260924-0323--39d1cab2`: holds `fix/conditional-requests-round4-followups` at `94ce8b1f`. **Keep it** until item 1 merges. Never push an unsigned scratch commit from it.
  - `juniper-cascor--fix--shortfall-mixed-provenance-and-678-followups--20260924-0235--0e016a7c`: HEAD `78e99414`. Keep it until item 2 validates.
  - `juniper-canopy--fix--secret-leaks-683-validation--20260924-1333--8917fdac`: HEAD is the unsigned `4caf9389`, which the stray branches point at. Do not validate from it.
  - Cleanup candidates (their PRs merged): `juniper-cascor--fix--bytes-compare-no-500--20260924-1337--ec8b5bdb`, `juniper-data--fix--bytes-compare-no-500--20260924-1337--1afc3480`, `juniper-canopy--fix--blank-key-678-followups--20260924-0235--e9053227` and `juniper-ml--fix--sentry-locals-and-bytes-compare--20260924-1337--48fc09e5`.
  - Older and dirty (diff each against its PR's merged content and name what removal would lose before asking): `juniper-cascor--fix--nonshortcircuit-key-compare--20260921-0846--c6c848f2` (1 entry), `juniper-data--feature--tri-state-allow-truncation--20260922-0753--e8db3ba6` (16), `juniper-data--fix--cheatsheet-conflict-markers--20260922-0820--e8db3ba6` (1) and `juniper-cascor--docs--tri-state-truncation-prose--20260922-0822--8065ca0f` (5).
- **Remote branches:**
  - cascor `fix/shortfall-mixed-provenance-and-678-followups` still at `e452a660` (from closed #686; deleting it blocks reopening) [VERIFIED].
  - cascor `fix/shortfall-688-validation` and `fix/bytes-compare-no-500`, and data `fix/bytes-compare-no-500`, are deleted [VERIFIED: 404].
  - canopy `pr-63` and `pr-683` at `4caf9389` [VERIFIED]; deleting them is the owner's call.
  - Local cascor branches of the shortfall name and its `-v2` [NOT RE-PROBED].
- **This consolidation:** written on branch `docs/handoff-consolidation-2026-10-03` (worktree `snappy-strolling-waterfall`), uncommitted. The only edits are this file and the SUPERSEDED banners in the two source files.
