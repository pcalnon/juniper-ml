<!-- markdownlint-disable -->
# Round 2, lane R2-A (Lane B)

**Entry point:** adversarial: attack the round-1 fix pass.

**Target:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` and the PRs named in the brief.

**Ran:** 2026-09-22T20:41:29Z to 2026-09-22T21:17:07Z, read-only. Agent `agent-a3033e13e20bbc4d3`.

The sections below are verbatim: the brief as sent, any message sent mid-run, then the lane's final
report as returned.
Line numbers in the report refer to the revision it reviewed, not to the file as merged.

## Brief

You are round-2 Lane B (analysis review) in an independent-agent consensus review. Round 1 found defects; the author then made a FIX PASS. Your brief: **the fix pass is the least trustworthy part of any document — find what these corrections broke, over-claimed, or got wrong.** Default to REFUTED when you cannot verify a new claim against primary sources. A finding that everything is fine is worth nothing.

READ-ONLY (hard): do not edit/create/delete files in any repo; do not commit, push, comment, merge, close, approve anything. Worktree-isolated harness: only read-only `git diff`/`git show`/`git log` inside the juniper-ml worktree below; use `gh api` for everything else; plain commands only (the harness refuses shell loops over variables touching gh/git, and complex one-liners — put logic in a python script file under your scratch dir and run it). Scratch: /tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/r2a/ . Everything below is FROZEN for this review.

ARTIFACTS OF THE FIX PASS:
1. juniper-ml PR #2020 (branch `docs/handoff-2026-09-11-ci-tools-reevaluation`, head 50430e02; the worktree /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/jolly-wibbling-pearl holds identical content — `git diff origin/main` there shows it). Focus on `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`: the rewritten `## Status banner` (tables, notes a–g, "Corrections to this document" 1–6, "Where the remaining work lives", verification block) and the five short in-place notes. The `__VALIDATION_RECORD__` and `__ML_PR__` placeholders are intentional (to be filled after this round). Also the new `**Status**` line in `HANDOFF_2026-09-11_container-registry-oq1-ruled-and-the-two-pins-no-sweep-could-see.md`.
2. Second commits + rewritten bodies/titles on: juniper-deploy#227 (CHANGELOG correction commit 991e6653 + body), juniper-canopy#655 (commit aed6881a + body/title), juniper-cascor-client#170 (commit daa6c675 + body/title), juniper-data-client#210 (commit 8fc0a853 + body/title). And new PRs juniper-cascor#673, juniper-deploy#228.

WHAT ROUND 1 FOUND (the corrections were made in response to these): the banner over-claimed closure (missing items 1 and 6f, X7 unowned, D-1 "pull test" not actually pulling); census missed prose-form ranges; "worker #180 never ran" was false (it made signed commit 695d64e8, head of worker#184); "floor bump inert, CONFIRMED by a CI log" was refuted by the same push (job 103226938137 installed 0.6.0); "not owner-gated" for unmerged PRs; "now fixed" for open PRs; "47 pin lines across 26 files" mixed scopes; OQ-3 narrowed; deploy#227's equities rationale wrong (data image has no yfinance) and its __version__ check circular; missing full filenames.

ATTACK, specifically:
(a) Every NEW factual claim in the banner and the PR bodies: re-derive it from `gh api`/PyPI/GHCR/docker (`docker run --rm --entrypoint python <image> -c "..."` is allowed; never `sh -c`). Examples to hit: "All 20 cited merge SHAs"; "43 pin lines in 26 workflow files, plus 4 in 4 AGENTS.md files … floor pass … 50 in 31"; "19 current-state lines in six repos"; the environments' creation times; "no later handoff or plan section carries 6f"; "a seeded arc_agi request resolves to the same dataset_id under 0.14.0 and 0.15.0"; "EQUITIES_DEPS_AVAILABLE is False"; "JuniperCascor1 holds juniper-ci-tools 0.8.0 and JuniperCanopy1 0.6.0" (check /opt/miniforge3/envs/*/lib/python3.*/site-packages); "25 of the chain's worktrees"; the X7 constants and the 09-12 canopy-selection handoff's item 10 wording (`HANDOFF_2026-09-12_canopy-selection-section-12-closed-residue-remains.md`).
(b) Contradictions the fix pass introduced: between the banner and the untouched body of the same document, between the banner and the later chain (HANDOFF_2026-09-15_all-five-images-published-and-the-pi-gate-wave-3-still-owes.md, HANDOFF_2026-09-17_container-registry-wave-3-complete-and-everything-left-is-owner-gated.md, HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md — all in the same directory), and between a PR body and its own diff.
(c) Over-claim / self-serving framing remaining anywhere; any claim stated as done that is only in an open PR; any "startable" item that is really owner-gated or vice versa.
(d) Naming rule: with two or more documents cited, every reference to a document must carry its filename (section numbers, role references like "the tip handoff", "the procedure", "plan §5.1"). List every violation in the banner.
(e) The sibling PR second commits: did the new text introduce any error (e.g. the lockfile comments' factual claims — verify cascor-client's workflow has 0 runs and its regen step is unconditional; data-client run 34126070406's notices)?

OUTPUT (final message only is returned): numbered findings — location, verdict (REFUTED / PARTIAL / CONTRADICTION / NAMING / OVER-CLAIM / OK), severity (CRITICAL/MAJOR/MINOR), evidence (command + short output), minimal fix. Then an overall verdict: SAFE / SAFE WITH FIXES / NOT SAFE. Terse, no preamble.

## Final report

1. **Banner note f (L124-128), and "canopy's X7 structural fix" in the Startable list.** OVER-CLAIM / CONTRADICTION. **MAJOR.**
   - **Evidence:** canopy#655 run 35780782107, attempt 1, job 106926744764, at 20:41:35Z: `initialize() stalled the loop for 0.726s`. That makes three recorded failures, not "both". All three exceed `BLOCK_SECONDS = 0.4` (`test_x7_sites_outside_main_gate.py:71`). If `sync()` were running on the loop, the stall would read about 0.4 s, so the stub is not what stalls it. The cause is not diagnosed: it could be runner suspension or other on-loop work in `initialize()`.
   - The author's own memory, `project_container_registry_rollout_2026-09-08.md:376-379`, says "Diagnose before raising thresholds".
   - The banner calls the stall "noise" and prescribes raising the block and the bound together. That change would permanently hide a real 0.6–0.7 s on-loop stall.
   - **Fix:** say three failures (0.586, 0.743, 0.726 s), cause undiagnosed, diagnose before touching any bound.

2. **Corrections 1 ("Use the census instead… judges prose as well as pins"), the "19 current-state lines" figure, and the verification comment "then exits 0".** REFUTED (the completeness claim). **MAJOR.**
   - **Evidence:** `juniper-canopy/.github/workflows/ci.yml:270-271` at main `886147b5` says "ci-tools 0.8.0 is already installed by the preflight step". The preflight (L197/L202) installs `>=0.9.0,<0.10.0`.
   - `SPEC_RE` only matches a version that follows an operator, so a bare version is invisible to the census.
   - canopy#655 leaves this line unfixed, and the census will report exit 0 after the merges with it still stale.
   - **Fix:** add the line to canopy#655, say "≥20 lines", and state that the census is blind to bare versions such as `0.8.0` or `0.8.x`.

3. **Corrections 4, "43 pin lines in 26 workflow files".** PARTIAL. MINOR.
   - **Evidence:** 4 of the 43 added lines are comments: data `main-verify.yml:26` and `sequence-safety.yml:26`, recurrence `main-verify.yml:25` and `sequence-safety.yml:26`. That leaves 39 live pins.
   - The figures reconcile as 54 = 13 (juniper-ml) + 39 + 2 (cascor's stale pins). This is the same scope-mixing the correction is about.
   - **Fix:** "43 lines (39 live pins + 4 comments)".

4. **PR #2020 body, "fixed the next day, cascor#646".** REFUTED. MINOR.
   - **Evidence:** #646 merged 2026-09-11T22:32:49Z. The handoff was committed as `9515b827` at 2026-09-11T19:56Z, the same day.
   - **Fix:** "later the same day".

5. **canopy#655 body, "+1/-1 in each file".** CONTRADICTION with its own diff. MINOR.
   - **Evidence:** `AGENTS.md` is +2/-2 (the hint plus `Last Updated`). The body mentions the date change itself.

6. **data-client#210's new `lockfile-update.yml` comment, "every run takes the 'No requirements.lock' branches".** OVER-CLAIM. MINOR.
   - **Evidence:** the workflow has 48 runs: 24 failures, 6 skipped, 18 successes. Every failure is dated 2026-07-27 or earlier and died at `Checkout Code` (for example run 30269229770).
   - **Fix:** "every run since the 2026-07-28 token gate".

7. **Table row "…conversions have never executed | TRUE", and the L504-506 note "cannot execute yet".** PARTIAL, and inconsistent with Corrections 2. MINOR.
   - **Evidence:** data-client's converted workflow has run 5 times since #197 merged (14 Sept ×3, 21 Sept ×2, including 35604787525). Each run took the no-lockfile skip branch. What has never fired is the signed-commit path.

8. **PR #2020 claim: "Five short in-place notes mark the passages the banner corrects".** OVER-CLAIM. MINOR.
   - **Evidence:** these corrected passages have no note:
     - L313 (dates)
     - L322 ("47 pin lines across 26 files per pass, both passes identical in shape")
     - L356-358 ("all nine repos began installing 0.9.0")
     - L384-387 (X7)
     - L496-497 ("every changed line checked to be a pin or an AGENTS.md date"). This is false: cascor#645 added 3 test lines, and each pass added 4 comment lines.
   - L322 and L356 sit inside the goal block that gets pasted.

9. **Table row, note g and L452: "all 25 of the chain's worktrees".** REFUTED as worded. MINOR.
   - **Evidence:** the three worktrees from `HANDOFF_2026-09-07_container-registry-rollout-wave-1-complete.md` still exist: `…worker--feat--publish-container-image--20260905-1846--1080015f`, `…cascor-client--docs--changelog-section-order--20260905-1523--714e544a` and `…canopy--chore--pin-cascor-client-floor--20260905-1441--482281ac`. `HANDOFF_2026-09-08_container-registry-rollout-wave-2-opened-and-the-cuda-class-in-three-shapes.md` L439 carries them.
   - **Fix:** "the 25 these three documents list".

10. **Note b, D-1.** CONTRADICTION / OVER-CLAIM. MINOR.
    - **Evidence:** `HANDOFF_2026-09-15_all-five-images-published-and-the-pi-gate-wave-3-still-owes.md` L36 marks D-1 **CLOSED** via #217. The banner does not reconcile its "re-scoped" with that.
    - "No CI job pulls and runs the published images" is too broad. Every image repo's `publish-image.yml` pulls the pushed image by digest and runs checks in it (for example cascor `:210-238`), and deploy's own `publish-image.yml:238-251` does the same for its test runner.
    - **Fix:** "no juniper-deploy job runs the published stack".

11. **L20-22, "every publish-image.yml imports its application on the publish path".** PARTIAL. MINOR.
    - **Evidence:** cascor's publish path imports only `cascade_correlation` (`:238`). Its smoke step imports `cascade_correlation, api, snapshots` (`:205`), so the service module `api` is never imported on the path that ships.

12. **Note c's §10 summary and the Startable list.** Omission. MINOR.
    - **Evidence:** §10 of `JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md` lists an open row, "A drift gate for `dockerhub`": `tests/test_publish_env_policy_drift.py` reads only `pypi`/`testpypi`. ml#2011 also flags it. It is startable and appears nowhere in the banner.

13. **Note f, "item 10".** Ambiguous reference, plus a dropped item. MINOR.
    - **Evidence:** `HANDOFF_2026-09-12_canopy-selection-section-12-closed-residue-remains.md` has two items numbered 10: the table row at L33 and the list item at L268. L268 also names `test_main_import_and_lifespan.py::test_keepalive_loop_survives_broadcast_error`.
    - That file was last changed on 2026-05-31, canopy#649 did not touch it, and the flake is equally unowned.

14. **L223, "data#401 changed arc_agi's task_type".** MINOR.
    - **Evidence:** #401 is an issue. The code change is juniper-data#402 (`f3797634`, "…(#401) (#402)").

15. **Unnamed PRs.** NAMING. MINOR.
    - L23-26: "the containers session undertook to correct, in its own PR" should name juniper-ml#2019, which was open at 20:35:42Z, before this PR's 20:40 commits.
    - L226-228: "Report on the stack" duplicates what #2019 already folds into §5.2.
    - canopy#655's body says "the handoff-banner PR"; it should say juniper-ml#2020.

16. **L28-30 provenance statement.** OVER-CLAIM. MINOR. The host facts are not only "the Pi probe and the worktree directories". The conda-env facts (Corrections 6) and the Docker measurements (note a's torch version; arc_agi "Measured in both images") are host facts too.

17. **L154, "Of the four this arc converted".** MINOR.
    - **Evidence:** cascor#641's body says it was already on `createCommitOnBranch` (the mutation "carries two `fileChanges.additions`"). `HANDOFF_2026-09-09_container-registry-item-6-closed-and-a-whole-file-clobber-caught-by-ci.md` L33-34 separates #180's "plus converting".
    - **Fix:** "three conversions plus cascor#641's extension to both locks".

18. **Smaller wording errors.** MINOR.
    - Table row 7 says OQ-2/3/4 are each "awaiting an owner design ruling", but note e says OQ-3's gate is the Pi pull.
    - Note e quotes 09-08 as "Pi disk/bandwidth"; `HANDOFF_2026-09-08_container-registry-rollout-wave-2-opened-and-the-cuda-class-in-three-shapes.md` L283 says "disk/bandwidth as well as RAM".
    - "On the owner's instruction" (environment creation) is not in ml#2011 or the procedure. UNVERIFIED.
    - The alias is anyio's, not starlette's (recurrence#154 title).
    - The self-test is 29 crafted cases plus 2 aggregate checks, not "31-case".
    - `predict_merge.py:57` is a docstring, not a printed hint.

19. **Banner naming violations** (two or more documents are cited, so each reference needs a filename). NAMING. MINOR.
    - L19-22: "That tip handoff…", "Its items 3 and 4", "its item 1"
    - L34-35: "its predecessor's", "The tip handoff"
    - L80: "its §3 Option B"
    - L83: "§5.2B steps 1–2"
    - L86-88: "Step 3", "the procedure's §6", "its §7", "Its §10"
    - L100-101: "plan section"
    - L148-150: "That document… corrected there"
    - L183: "The census's"
    - L206: "Wave 4 step 3, then its verification"
    - L221: "The tip handoff's item 1"
    - The oq1 handoff's new Status line: "Option B" with no procedure filename.
    - PR #2020 body: "The handoff's headline", "The new banner", "The banner's own ### Validation record".

20. **Verified and OK:**
    - All 20 cited merge SHAs, plus a5cbdcd1, 63a29e87 and ee57a892. Publish runs 34579752944 and 34461928708, all jobs green.
    - Corrections 3 merge times. Corrections 4 counts (47/30 and 50/31). 19 = 18 STALE + REFERENCE.md:3023. 54 live pins, one range. 10 AMBIGUOUS entries (only :3023 stale). Self-test prints 31 passed.
    - Jobs 103226938997 (0.9.0) and 103226938137 (0.6.0) on the same push, bbdcbb6a. Signed commits 695d64e8, bca33c99 and d7b5ea1f, all verified. cascor-client: 0 runs, and no Dependabot pip PR ever. Its regen step writes an untracked lockfile that `git diff --quiet` misses (the token gate passes, since the PAT is in the Dependabot store). Run 34126070406's two notices.
    - The five environments created 19:45:59–19:46:21Z with `v*` and `juniper-*-v*` tag policies, 0 secrets, no `DOCKERHUB_*` in any of the nine repos.
    - GHCR tags. Release and PyPI dates. data 0.15.0 wheel 97/201. Worker image reports "0.4.0 0.6.0 2.14.0+cpu".
    - In both data images: `EQUITIES_DEPS_AVAILABLE=False`, no yfinance. arc_agi resolves to `arc_agi-3.0.0-5cbabfa9a9026f82` in both. Equities versions 3.0.0 → 5.0.0.
    - JuniperCascor1 holds 0.8.0 and JuniperCanopy1 holds 0.6.0.
    - The X7 constants, and canopy#649's single file.
    - No later handoff or plan section mentions 6f; the only record is the recurrence `pyproject.toml` comment.
    - deploy#227: revision label `46894ba1` equals the v0.15.0 tag commit, digest `2da73f06bbd3`, Helm tags and line numbers.
    - Every line number cited in the sibling PRs.
    - turing unreachable, no arm64 binfmt handler, host is yamaguchi.
    - Every sibling PR is green now; canopy#655 needed a rerun.

**Overall verdict: SAFE WITH FIXES.** Findings 1 and 2 need correcting before merge; the rest are minor edits.
