<!-- markdownlint-disable -->
# Round 3, lane R3-A (Lane B)

**Entry point:** adversarial: attack the round-2 fix pass, plus a ledger of every earlier finding.

**Target:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` and the PRs named in the brief.

**Ran:** 2026-09-22T23:28:02Z to 2026-09-23T00:41:39Z, read-only. Agent `agent-a990b71e904da0866`.

**Paused:** 2026-09-22T23:52:45Z to 2026-09-23T00:31:20Z, stopped by a usage limit and resumed in place.

The sections below are verbatim: the brief as sent, any message sent mid-run, then the lane's final
report as returned.
Line numbers in the report refer to the revision it reviewed, not to the file as merged.

## Brief

You are round-3 Lane B (analysis review) in an independent-agent consensus review, run under `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` (juniper-ml repo). Rounds 1 and 2 found defects. After round 2 the author made a SECOND fix pass. Your brief: **the fix pass is the least trustworthy part of any document. Find what the round-2 corrections broke, over-claimed, got wrong, or silently dropped.** Default to REFUTED when you cannot verify a new claim against a primary source. A report that everything is fine is worth nothing.

READ-ONLY (hard): do not edit, create or delete files in any repo. Do not commit, push, comment, merge, close, approve, or approve deployments. The harness isolates this session to the juniper-ml worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/jolly-wibbling-pearl`. Inside it, run only read-only `git diff`, `git show` and `git log`. Use `gh api` or GraphQL for everything else. Use plain commands only: the harness refuses shell loops over variables that call gh or git, `$(...)` feeding a command, and complex one-liners. If a command is refused, write the logic into a small Python script under your scratch dir and run that. Scratch dir: `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/r3a/` (create it). **Everything below is FROZEN for this review.**

THE DOCUMENT. `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`. It is identical in the worktree and at juniper-ml PR #2020's head `4855bf8c` (branch `docs/handoff-2026-09-11-ci-tools-reevaluation`). Round 2 reviewed head `50430e02`. `git diff 50430e02 4855bf8c` in the worktree shows every change since; the objects are fetched. The round-2 reports are archived verbatim under `reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/`, and so are the round-1 reports. Read them to learn what round 2 asked for.

THE ROUND-2 FIX PASS, which is your target:
1. The Status banner, rewritten: the item table, the claim table, notes a–g, Corrections 1–6, the three remaining-work lists and the verification block. Key new claims:
   - the X7 flake: three stalls of 0.586, 0.743 and 0.726 s, plus a sibling at 0.696 s, all exceeding the stub's 0.4 s block, so "none carries the defect's signature";
   - 28 sibling worktrees plus 2 session worktrees;
   - 23 current-state lines, 22 of them fixed by six PRs;
   - 43 = 39 live + 4 comments;
   - data-client's workflow: 9 triggers since #197, 5 executed with the no-lockfile log, 4 skipped;
   - cascor#641 "extended an existing signed step";
   - the census's limits, including the AMBIGUOUS semantics;
   - item 1 "CLOSED" and item 4 "D-1 closed as re-scoped".
2. The dated in-place notes added to the original body below the banner. Find each by grepping for `2026-09-22`.
3. The new section `### Validation record for this banner`: sizing, conduct, the lane table, reconciliation, instrument and limits.
4. The worker `v0.6.1` updates. The new claims:
   - juniper-cascor-worker#194 merged 22:56 UTC and `v0.6.1` was cut 23:03 UTC;
   - the GHCR `0.6.1` image reports `__version__` 0.6.1;
   - the wheel waits on the owner's `pypi` approval;
   - juniper-deploy still pins worker 0.6.0;
   - pin drift is now "three times".
5. Two PR commits made after round 2:
   - juniper-canopy#655 `fdb9e2de`, the coverage-gate comment round 2 said was invisible to the census;
   - juniper-data-client#210 `ee1fb5d7`, which narrows the lockfile comment "to the runs actually checked".
6. PR #2020's description, rewritten after round 2. Read it with `gh api repos/pcalnon/juniper-ml/pulls/2020 --jq .body`. Also check the bodies of #655, #673 (juniper-cascor), #170 (juniper-cascor-client), #210 (juniper-data-client), #228 and #227 (juniper-deploy) against their current diffs.

REQUIRED, in addition to attacking the list above:
- **An applied / not-applied ledger.** Cover every finding in the five round-1 and three round-2 archived reports. For each one, give: applied correctly / applied wrongly / not applied / not applicable, with the evidence. Flag any finding dropped with no trace. A dropped finding that changes a number, a disposition or an action is MAJOR.
- **Naming.** The ecosystem rule: once two or more documents are cited, every reference carries its filename. That covers references by section number, by role ("the plan", "the tip handoff") and by implication. List every violation in the banner and in the #2020 body.

OUTPUT. Only your final message is returned. Give numbered findings. Each has: the claim tested (quoted, with its line number in the frozen file), a verdict (CONFIRMED / REFUTED / PARTIAL / OVER-CLAIM / CONTRADICTION / DROPPED / NAMING), a severity (CRITICAL / MAJOR / MINOR), the evidence (a command and its output, or file:line), and a minimal fix. Then the ledger as a compact table. End with **Overall verdict** (SAFE / SAFE WITH FIXES / UNSAFE TO MERGE) and a **Changed:** line naming any file you wrote. Anything you write should be under your scratch dir only.

## Message sent mid-run

The coordinator sent a message while you were working:
A usage limit stopped you mid-review. Continue from where you stopped, and deliver the FINAL REPORT exactly as your brief specifies: numbered findings, the applied / not-applied ledger, the naming list, then the overall verdict and the Changed: line. Everything under review is still frozen: juniper-ml#2020 head 4855bf8c, juniper-canopy#655 fdb9e2de, juniper-cascor#673 a824829b, juniper-cascor-client#170 daa6c675, juniper-data-client#210 ee1fb5d7, juniper-deploy#228 e6091c46 and #227 991e6653. It is now 2026-09-23 00:30 UTC. If an external fact has moved since the banner was written, report it as STALE rather than as an artifact change.

Address this before completing your current task.

## Final report

**Round 3, Lane B: review of the round-2 fix pass**

This covers juniper-ml#2020 at head `4855bf8c`, and the sibling PRs at canopy#655 `fdb9e2de`, cascor#673 `a824829b`, cascor-client#170 `daa6c675`, data-client#210 `ee1fb5d7`, deploy#228 `e6091c46` and deploy#227 `991e6653`. External probes ran from 2026-09-22 23:30Z to 2026-09-23 00:35Z. Every bare `L` number refers to `HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` at `4855bf8c`, which I confirmed is byte-identical to the worktree copy.

## Findings

**1. L151: "It has failed three times: 0.586 s, 0.743 s and, on 2026-09-22, 0.726 s."**
- **Verdict:** REFUTED. **MAJOR.**
- **Evidence:** I scanned canopy `ci.yml` runs since 09-05: 312 runs, 53 of them failed or re-run. I grepped every failed Unit Tests job log. `test_initialize_sync_does_not_block_the_loop` failed at least **five** times:

  | stall | run / job | where |
  | --- | --- | --- |
  | 0.715 s | 34154880308 / 101844898303 | `d3ce6a82`, 3.12 macOS, 09-07 |
  | **0.807 s** | 34397237323 / 102620457412 | **canopy `main` @95284f37**, 09-09 |
  | 0.586 s | 34418776436 / 102690169053 | `0bdec6d1`, 09-09 |
  | 0.743 s | 34600043077 / 103266276082 | `chore/raise-ci-tools-floor` (canopy#619) |
  | 0.726 s | 35780782107 / 106926744764 | canopy#655 |

  - `gh api repos/pcalnon/juniper-canopy/actions/jobs/102620457412/logs | grep 'stalled the loop'` returns `initialize() stalled the loop for 0.807s`.
  - The source, the memory file `reference_canopy_x7_timing_tests_flake_on_ci_runners.md`, merges the `main` failure (0.807 s) and the PR failure (0.586 s) into one reading.
  - So "The third was on canopy#655" (L152) is really the fifth.
- **Fix:** "at least five times in CI since canopy#585 (0.715, 0.807, 0.586, 0.743, 0.726 s; runs above), once on `main`."

**2. L153–156: "Every one of those stalls exceeds the stub's own 0.4 s block … So none of these failures carries the defect's signature. They are runner suspension, or other on-loop work inside the call under test."**
- **Verdict:** REFUTED / CONTRADICTION. **MAJOR.**
- **Evidence:** the canopy test file `src/tests/regression/test_x7_sites_outside_main_gate.py` at `main`:
  - L27–28 says "an inline call leaves a gap of the whole stall".
  - The sensitivity control (L298–299) asserts `worst_gap >= BLOCK_SECONDS * 0.8`. That is a floor, not a band.
  - A `sync()` running on the loop reads 0.4 s plus any other delay. So 0.586–0.807 s is consistent with the defect. Only a reading between 0.2 and 0.4 s rules out an on-loop block.
  - "Other on-loop work inside the call under test" is itself "a blocking call running on the loop" in L154's own words. The note contradicts itself.
  - It also contradicts L414, which says the record cannot support "any cause for the X7 flake".
  - The real evidence against a deterministic regression is that four of the five failing heads went green on rerun (attempt 2 succeeded for runs 34154880308, 34418776436, 34600043077 and 35780782107). That bounds only a deterministic regression.
  - The argument is R2-A's lone mechanism (`round2-laneB-attack-the-fix-pass.md` #1). It was adopted without being re-derived, which contradicts L395–396.
- **Fix:** "Every reading exceeds 0.4 s, so the readings cannot separate an on-loop `sync()` plus 0.2–0.4 s of other delay from an off-loop one plus 0.6–0.8 s of suspension. Green reruns rule out only a deterministic regression."

**3. L165–166: "That file was last changed 2026-05-31 and is equally unowned."**
- **Verdict:** REFUTED (a wrong disposition). **MINOR.**
- **Evidence:**
  - `HANDOFF_2026-09-22_canopy-selection-four-decisions-shipped-residue-is-owner-scoped.md` §E item 13 (L199–203) carries exactly this keepalive test. It has been on `main` since #2018 (20:44Z), before this fix pass.
  - The X7-sites test appears nowhere in that file: a grep for `x7_sites|initialize_sync` returns nothing.
- **Fix:** say the keepalive test is carried as that handoff's §E item 13, and that only the X7-sites test is unowned.

**4. L171–173: "Thirteen from `HANDOFF_2026-09-08_…`. Ten are its own; the other three it carried from `HANDOFF_2026-09-07_…`."**
- **Verdict:** PARTIAL. **MINOR.**
- **Evidence:**
  - `HANDOFF_2026-09-08_container-registry-rollout-wave-2-opened-and-the-cuda-class-in-three-shapes.md` L439 carries "the predecessor's three arc worktrees **and two older worker worktrees**".
  - `HANDOFF_2026-09-07_container-registry-rollout-wave-1-complete.md` L368–369 names those two.
  - Both still exist: `worktrees/juniper-cascor-worker--docs--handoff-word-count--20260830-2339--44358bf0` and `worktrees/juniper-cascor-worker--fix--mv-screened-base--20260902`.
  - The 28 is verified: the L354 glob prints 28. But it holds only for the chain's own worktrees, and a cleanup driven by note g would miss these two.
- **Fix:** "fifteen carried by 09-08; the two older worker worktrees are excluded from the 28."

**5. L202–209, the census's "Its limits": "It lists such a range as AMBIGUOUS", and "It sees a bare release only in a present-tense install claim, such as …"**
- **Verdict:** REFUTED as a universal. **MAJOR** (latent: no instance exists at `main` today).
- **Evidence:**
  - An unattributed range becomes AMBIGUOUS only when its section matches `ci[-_]tools|screen pin|sequence[-_]safety` (census L138, L470–475, and its own docstring L61–62). Anything else is dropped with no output.
  - Crafted inputs (`crafted.py`) that produce no hit at all:
    - `The CI pin is \`>=0.8.0,<0.9.0\` for the screens.`
    - a YAML comment `# juniper-ci-tools` / `#` / `# pinned >=0.8.0,<0.9.0`
    - `CI installs juniper-ci-tools 0.8.0 today.`
    - `The preflight step installs ci-tools 0.8.0.`
    - `juniper-ci-tools is pinned to 0.8.0 in CI.`
  - The self-test itself pins a silent drop: census L649, "a paragraph break ends attribution" expects an empty set.
  - R2-B #5 asked for attribution by enclosing section. That was done only for markdown headings and table columns.
- **Fix:** state the real rules. AMBIGUOUS is reported only when the paragraph, comment block or section contains those words; otherwise the range is dropped silently. A bare release is seen only in the form `<name> 0.X.Y is|are [already|now] installed|pinned|in use|required`.

**6. L198–200 and L406–407: "15 of 15 code mutations fail that self-test", "The self-test discriminates."**
- **Verdict:** OVER-CLAIM; part of R2-B #2 was dropped. **MAJOR.**
- **Evidence:**
  - Reproduced: 81 of 81 self-test cases pass and 15 of 15 mutations are killed. But those 15 are the author's own chosen anchors.
  - I wrote 21 more single-rule mutants (`extra_mutations.py`). **15 survive:**
    - `util/ad-hoc/` no longer HISTORICAL (R2-B named this one: "removing it adds 14 stale lines");
    - CHANGELOG, `prompts/` and `reports/` no longer historical;
    - the OWN-EXTRA branch;
    - the ADJUDICATED lookup, and the ADJUDICATED table emptied;
    - composite actions no longer treated as workflows;
    - the `/` in-path branch and the `- #` comment branch;
    - the floor-only AMBIGUOUS skip;
    - the per-repo zero-files guard, the zero-live-pins guard and the 1.0 guard;
    - **the passing-AMBIGUOUS listing that `4855bf8c` itself added.**
- **Fix:** add cases, or say "15 of the 15 chosen mutants; 15 of a further 21 survive (list)".

**7. L219: "`bca33c99` on the open worker#194."**
- **Verdict:** CONTRADICTION, introduced by the fix pass. **MINOR.**
- **Evidence:** L32 says #194 merged at 22:56Z. `gh pr view 194 --repo pcalnon/juniper-cascor-worker` shows MERGED at 22:56:12Z.
- **Fix:** "on worker#194 (merged 22:56Z)".

**8. L16: "Since juniper-ml#2019 it carries its own status banner, and that banner agrees with this one."**
- **Verdict:** CONTRADICTION at freeze time, since resolved from outside (STALE). **MINOR.**
- **Evidence:**
  - At `4855bf8c`, the banner of `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md` on `main` still said the published image "still holds … waiting for the owner's merge and Release".
  - This document's L31–36 says it is resolved.
  - juniper-ml#2025 (`a7568f78`, 23:40Z, after the freeze) brought the two into agreement.
  - They still differ on item 1's precondition (see finding 9).
- **Fix:** name #2025, or drop "agrees".

**9. L284–285: "Message the containers session before starting it: two sessions evaluated it on 2026-09-22, and neither started it."**
- **Verdict:** UNTRACEABLE and not executable. **MINOR.**
- **Evidence:**
  - No session ID or channel is given, and the memory file `reference_cross_session_sendmessage_undeliverable.md` records that such messages fail.
  - The ten-prs-landed handoff's banner gives a checkable step instead: "Check open PRs in the five image repos."
- **Fix:** use that check.

**10. L103: "That session reports it did so on the owner's instruction."**
- **Verdict:** UNTRACEABLE. **MINOR.**
- **Evidence:** neither the ml#2011 body and diff nor §5.2B of `JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md` says so. R2-A #18 flagged this; the wording changed but no source was added.
- **Fix:** cite a source or drop the sentence.

**11. L22–24: "each `publish-image.yml` imports its application's main module … cascor's imports only `cascade_correlation`."**
- **Verdict:** PARTIAL; R2-A #11 was applied by half. **MINOR.**
- **Evidence:** cascor's `publish-image.yml` imports only `cascade_correlation` on the publish path (L238). The service module `api` is imported only in the build-only smoke step (L205). So the "each" is false for cascor, by the banner's own next sentence.
- **Fix:** drop "main module", or name cascor as the exception.

**12. The worker v0.6.1 claims (L32–36, L83, L94–95, L272–273, L297–298).**
- **Verdict:** CONFIRMED, with two caveats. **MINOR.**
- **What holds:**
  - #194 merged at 22:56:12Z as `38f39cb8`.
  - The Release was published at 23:03:30Z.
  - The GHCR index is `sha256:c15764723c8d…`, and its label revision is `38f39cb8`.
  - The layer's `__init__.py` derives `__version__` from metadata, and its `METADATA` says 0.6.1.
  - At 00:35Z PyPI still serves 0.6.0. Run 35795531350 is still waiting on the `pypi` environment; TestPyPI finished at 23:04:33Z.
  - deploy still pins worker 0.6.0: `docker-compose.yml:364`, `values.yaml:301`. No repin PR exists.
  - "Three times" holds: the only image releases since 09-16 are canopy v0.8.1, data v0.15.0 and worker v0.6.1.
- **Caveat 1:** the 0.6.1 tag appeared about 23:08Z (the manifest job completed 23:08:23Z), not 23:03Z. 23:03Z is the Release time.
- **Caveat 2:** "matching its metadata" is true by construction now. deploy#227's body says the same about juniper-data. The check discriminates only because a pre-#192 build would print 0.4.0.
- **Fix:** give the image time, and add the caveat.

**13. L159: "`memory/reference_canopy_x7_timing_tests_flake_on_ci_runners.md` has the detail."**
- **Verdict:** Not resolvable from the stated root. **MINOR.**
- **Evidence:**
  - There is no `memory/` directory under `/home/pcalnon/Development/python/Juniper` or under `juniper-ml`.
  - The file lives in the unversioned auto-memory directory. It was modified at 20:55:27Z, during round 2.
  - It carries both the miscount in finding 1 and the argument in finding 2.
- **Fix:** cite the CI runs directly.

**14. L375–376 ("2+ Lane B with opposing briefs") and L395–396 ("Every load-bearing finding that only one lane reported was re-derived").**
- **Verdict:** OVER-CLAIM. **MINOR.**
- **Evidence:**
  - Every lane had a refute brief; none argued the other side, which §2 L67–69 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` asks for.
  - Round 2 had a single Lane B.
  - Findings 2 and 3 are lone R2-A claims that were applied without being re-derived.
- **Fix:** record both deviations.

**15. PR #2020 title: "…and 19 lines still named old ci-tools ranges".**
- **Verdict:** CONTRADICTION with its own body. **MINOR.**
- **Evidence:** the body says 23 lines, 22 of them fixed (L41, L57). The first commit, `23238fe8`, also says "19", and a squash merge would carry that number to `main`.
- **Fix:** retitle with `gh api -X PATCH`.

**16. #2020 body L68–71: "Round 2 had three lanes, briefed on the corrections. It found the fix pass wrong in two places."**
- **Verdict:** OVER-CLAIM (it under-reports what round 2 found). **MINOR.**
- **Evidence:**
  - R2-C (`round2-laneA-full-read-artifact-first.md`) was briefed on the whole document. It found 5 refuted claims and 4 that were stale but unmarked.
  - R2-B (`round2-laneA-census-adequacy.md`) was briefed on the census and found 5 MAJOR defects.
- **Fix:** list the lanes' briefs and all the MAJOR findings.

**17. #2020 body L45: "`predict_merge.py`: lines 57, 180 and 234, the printed install hints."**
- **Verdict:** DROPPED (R2-A #18). **MINOR.**
- **Evidence:** `predict_merge.py:57` is inside the module docstring; only 180 and 234 are printed hints.
- **Fix:** "57 (docstring); 180 and 234 (printed)".

**18. deploy#227 body L59–60: "`--fail-on-stale` … exit 0".**
- **Verdict:** STALE; an external fact moved. **MINOR.**
- **Evidence:** re-run at `991e6653` now, it reports `1 of 6 pins are BEHIND … juniper-cascor-worker:0.6.0 -> 0.6.1 available` and exits 1. It was true when written. The merge itself is unaffected.
- **Fix:** add a timestamp.

**19. NAMING.** Violations are listed in their own section below. **MINOR.**

**20. Other new claims I re-derived: all CONFIRMED.**
- The X7 constants; that file unchanged since #585; the 0.696 s sibling failure (run 34292213310, job 102281408117).
- 28 sibling worktrees plus 2 session worktrees. The session worktree's untracked scripts are byte-identical to `main`.
- The census at `main` exits 1 with 23 STALE lines across six repos. Over the six PR heads it leaves exactly `docs/QUICK_START.md:92` plus two passing AMBIGUOUS lines, `REFERENCE.md:3023` and `test_ci_tools_drift.py:461`. That gives 22 of 23 fixed, and the six-PR split is 10/3/2/3/2/2.
- The ceiling pass: 47 lines in 30 files; 43 lines in 26 workflow files, 39 live and 4 comments. By repo the live pins are 6/4/5/5/5/5/3/6, so 54 = 13 + 39 + 2.
- data-client ran 9 times since #197: 5 executed and each logged both notices; 4 were skipped. Of all 48 runs, none committed a lockfile.
- cascor#641's base (`53c0338b`) already used `createCommitOnBranch`.
- Item 1 is closed (§5 of the 09-15 handoff records canopy's package as public). D-1 as re-scoped is recorded in `JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CONTAINER-REGISTRY-PUBLISHING-PLAN.md` L20 and L272.
- Every verification command runs and matches its comment.
- The new comment in canopy#655 `fdb9e2de` is accurate: `ci.yml` L202 and L278 both pin `>=0.9.0,<0.10.0`, and CI was green on the first attempt. The narrowed comment in data-client#210 `ee1fb5d7` is accurate. The bodies of #655, #673, #170, #210 and #228 match their diffs.
- The conda environments hold ci-tools 0.8.0 (both trees) and 0.6.0. The longest line is 417 characters.

## Applied / not-applied ledger

"Applied" means applied correctly unless the row says otherwise. Confirmation-only findings are grouped as n/a.

| report | finding | status |
| --- | --- | --- |
| `round1-laneA1-github-api.md` | 1 census not on main · 2 worker#180 ran · 3 ml#1869 SHA · 4 47/26 · 5 "now fixed" · 6 provenance · 7 file types · 8 probe coverage · 9 item 1 | applied (L219 now stale, finding 7). `.truncated` n/a. 10–19 n/a |
| `round1-laneA2-published-artifacts.md` | 3 circular `__version__` | applied in #227; not carried to the worker claim (finding 12) |
| same | 4 · 12 · 18 · 20 · 28 · 29 · (c) Helm | applied / disclosed. Others n/a |
| `round1-laneA3-independent-census.md` | 4 · 5 · 6 · 7 · 9 | applied |
| same | 8 blind spots | mostly applied; a range held only in an env var is still invisible (mitigated by UNRESOLVED). **The drift guard's narrower `_PIN_PATTERN` was DROPPED, no trace** (MINOR) |
| same | 3 | n/a |
| `round1-laneB1-refute-conclusions.md` | 1 · 2 · 3 · 5 · 7 · 8 · 9 | applied (9's worktree count: finding 4) |
| same | 4 X7 | superseded by R2-A #1 |
| same | 6 | applied, but the throwaway-repo test B1 called startable is filed owner-gated (L277–279) and the dissent is not recorded (MINOR) |
| `round1-laneB2-amputation-executability.md` | 1–5 · 7–11 · 14–17 | applied |
| same | 6 naming | partial (naming list below) |
| same | 12 oq1 handoff Status line | applied; "Option B" still has no procedure filename |
| same | 13 | applied; "who created the environments" is now untraceable (finding 10) |
| `round2-laneB-attack-the-fix-pass.md` | 1 X7 | **applied wrongly** (findings 1, 2) |
| same | 2 · 3 · 4 · 5 · 6 · 7 · 8 · 10 · 12 · 14 · 15 · 16 · 17 | applied (6 narrowed better than the lane proposed: run 30406940791 took the token-gate branch) |
| same | 9 | partial (finding 4) |
| same | 11 | partial (finding 11) |
| same | 13 | **applied wrongly** (finding 3) |
| same | 18 | partial: "owner's instruction" (finding 10); **`predict_merge.py:57` DROPPED** (finding 17) |
| same | 19 naming | partial |
| `round2-laneA-census-adequacy.md` | 1 · 3 · 4 · 6 · 7 · 8 · 9 · 11 · 13 · 14 | applied |
| same | 10 · 12 · 15 | applied in code, **untested** (their mutants survive) |
| same | 2 self-test | **partial; the named `util/ad-hoc` rule and 14 others unguarded** (MAJOR, finding 6) |
| same | 5 | partial (finding 5) |
| `round2-laneA-full-read-artifact-first.md` | REFUTED 1–5; STALE-UNMARKED 1, 2, 4; both omissions; the verification markers | applied |
| same | STALE-UNMARKED 3 | applied, but the count is still wrong (finding 1) |
| same | nits | `#163's` at the start of L475 **DROPPED** (trivial); the "paste" heading got a note but kept its text |

## Naming violations

Self-references to this document's own sections and notes are excluded.

**In `HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`:**
- L16 "it … that banner"
- L21 "Its items 3 and 4"
- L22 "its item 1"
- L28 "that document's banner"
- L31 "Its 'published image…'"
- L100 "its §3"
- L107 "that procedure"
- L108 "its §5.2B"
- L109 "Its §6"
- L110 "its §7"
- L111 "its §10"
- L130–131 "later handoff or plan section"
- L191 "That document"; L192 "Its table"
- L240 "The census's" (also "the census" at L205, L294, L303, L319, L385, L387, L390, L413)
- L263–264 "that procedure's §6 … §7"
- L369 "that procedure"
- L389 "the tip handoff"
- L394 "(§5)"
- The oq1 handoff's new Status line cites "Option B, juniper-ml#2009" without the procedure's filename.

**In the #2020 body:**
- L7 "That handoff's headline"
- L14 "Its 'want 0'"
- L14–15 "The new status banner … its items"
- L57–58 "the banner lists it … Its whole"
- L63–64 "that procedure's top-right cell"
- L64 "the banner's section"
- L72 "recorded in the banner"

## Overall verdict

**SAFE WITH FIXES.** Before merging, fix findings 1, 2, 5 and 6, all in the banner text, and retitle the PR (finding 15). The six sibling PRs are safe to merge as they stand. Under §4 of `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`, this round changed numbers (3 failures become 5; 13 worktrees become 15) and a disposition (finding 3). So the next fix pass needs its own round before the "Round 3" line at L419 is closed.

**Changed:** no repository files. Everything I wrote is under `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/r3a/`:
- `x7_runs.py` and `x7_logs.py` (with `x7_runs.json` and `x7_logs.json`), `dc_runs.py`, `dc_all_runs.py`, `ghcr.py`, `releases.py`, `prs.py` and `prs/`, `pass_counts.py`
- `census/extra_mutations.py`, `census/crafted.py`, and the census copies and outputs in `census/`
- `deploy227/`, plus fetched copies of the frozen files
