<!-- markdownlint-disable -->
# Round 4, lane R4-B (Lane B, opposing brief)

**Entry point:** the ship side: argue the merge, and find over-correction and noise.

**Target:** `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` and the PRs named in the brief.

**Ran:** 2026-09-23T01:02:10Z to 2026-09-23T01:27:46Z, read-only. Agent `agent-a7190f019f5237b36`.

The sections below are verbatim: the brief as sent, any message sent mid-run, then the lane's final
report as returned.
Line numbers in the report refer to the revision it reviewed, not to the file as merged.

## Brief

You are round-4 Lane B with the OPPOSING brief in an independent-agent consensus review, run under `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` (juniper-ml repo). §2 of that procedure says: "Steelman both directions when a decision is at stake. For a ship/hold decision, run one agent arguing each side on the same evidence." Every earlier lane in this review had a refute brief. **You argue the SHIP side.** Make the strongest honest case that these seven PRs should merge now, as they stand. Then attack the review itself: find where the corrections went too far.

Specifically, hunt for:
- **over-correction** — a claim weakened, hedged or deleted when the original was right, or a fix that made a statement less accurate or less useful;
- **noise** — text a successor must read that adds no decision or action, or a document so long that the actionable items are hard to find. Say what a successor needs from it in the first minute, and whether it gets that;
- **unjustified blockers** — a finding elsewhere treated as blocking that should not block a docs merge;
- **process debt** — places where the review's own process imposes a cost out of proportion to the risk, per §6 of the procedure ("Cost … Do not apply the top-right cell to routine work").

This is not a license to wave defects through. If you find a real defect that should block, say so plainly. That is part of an honest ship case.

READ-ONLY (hard): do not edit, create or delete files in any repo. Do not commit, push, comment, merge, close, approve, or approve deployments. The harness isolates this session to the juniper-ml worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/jolly-wibbling-pearl`. Inside it, run only read-only `git diff`, `git show` and `git log`, and do not run `git fetch`. Use `gh api` for everything else. Use plain commands only; if the harness refuses a command, put the logic into a Python script under your scratch dir. Scratch dir: `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/r4b/` (create it). **Everything below is FROZEN for this review.**

THE SEVEN PRs, at these heads:
- juniper-ml#2020 `f68380dd`;
- juniper-canopy#655 `fdb9e2de`;
- juniper-cascor#673 `a824829b`;
- juniper-cascor-client#170 `daa6c675`;
- juniper-data-client#210 `ee1fb5d7`;
- juniper-deploy#228 `e6091c46`;
- juniper-deploy#227 `991e6653`.

#2020's main artifact is the status banner of `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`. It runs from its top to `## Handoff goal`, and includes its `### Validation record for this banner`. The review history is in `reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/`, eleven lane reports over three rounds. `git diff d0582a21 f68380dd` shows everything #2020 changes against the `main` it branched from. The sibling diffs come from `gh api repos/pcalnon/<repo>/pulls/<n>/files`.

OUTPUT. Only your final message is returned.
1. **The ship case.** Per PR: merge now, or hold (with the one thing that must change first). One or two sentences each.
2. **Numbered findings.** Each has the passage (quoted, with its line number), a verdict (OVER-CORRECTION / NOISE / UNJUSTIFIED-BLOCKER / PROCESS-DEBT / REAL-DEFECT), a severity (CRITICAL / MAJOR / MINOR), the evidence, and a minimal change. A minimal change is often "cut" or "move to the validation record".
3. **The first-minute test.** Write, in at most five bullets, what a fresh session needs from the banner. Say whether the banner's first screen delivers it.
4. **Overall verdict**: SHIP / SHIP WITH CHANGES / HOLD. Add a sentence on whether any finding changes a number, a disposition or an action (the procedure's termination test for further rounds). End with a **Changed:** line.

## Final report

**Round 4, Lane B (ship side): #2020 should ship once L510 is filled, with one pointer fixed in the same commit. Nothing else blocks, and I'd stop the review here, with no round 5.**

Conventions: bare `L` numbers refer to `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md` at `f68380dd`, read from GitHub (the local worktree holds different, uncommitted content). Repo paths are juniper-ml-relative. Lane reports are in `reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/`. External probes ran 2026-09-23 01:05–01:22 UTC.

**What moved while this round ran (recorded as stale, not as defects in the frozen text):**
- The owner merged five of the seven PRs between 01:02:51Z and 01:12:14Z: cascor-client#170, data-client#210, deploy#227, deploy#228 and canopy#655. The last two merged at update-branch commits with unchanged diffs.
- The worker `0.6.1` wheel reached PyPI at 00:37:07Z.
- juniper-ml `main` is now `7b226ca0`.

## 1. The ship case

- **juniper-ml#2020 (`f68380dd`): hold for one close-out commit, then update-branch and merge.** L510 is a placeholder that has to be filled before merge anyway. Put finding 1's pointer in the same commit. Touch only the handoff files and the mutation-check header, not `docs/REFERENCE.md`. Everything else ships as it stands. I re-ran the instruments from the frozen head:
  - self-test: 93 passed, 0 failed;
  - mutation check: 24 of 24 killed;
  - census at the six frozen heads: exit 0, 54 live pins in one range, two passing AMBIGUOUS lines, exactly as L371–373 predicts;
  - census at `main` now: exit 1 on 13 lines, which are the 11 that #2020 fixes and the 2 that cascor#673 fixes;
  - the 18 package versions in the new `docs/QUICK_START.md` block match PyPI;
  - CI at `f68380dd`: 22 success, 5 neutral, 1 skipped.
- **juniper-cascor#673 (`a824829b`): merge now.** It changes two comment lines, has 26 checks passing and auto-merge armed. It only needs update-branch, because it is behind.
- **juniper-canopy#655: already merged.** Its body still says the QUICK_START block is "reported rather than fixed", which #2020 has since made stale. Not worth an edit.
- **juniper-cascor-client#170, juniper-data-client#210, juniper-deploy#228: already merged.** No follow-up needed.
- **juniper-deploy#227: already merged.** The worker-0.6.1 repin that was queued behind it is now unblocked, and no juniper-deploy PR is open. Its CHANGELOG phrase "a seeded `arc_agi` request" is accurate, because a default request is seeded with 42.

## 2. Findings

**1. Three open items live only in this banner, and the tip never points to it. REAL-DEFECT, MAJOR.**
- **Passage:** L14–16 "Continue the arc from `HANDOFF_2026-09-22_ten-prs-landed-…`. Its own status banner (juniper-ml#2019, brought up to date by juniper-ml#2025) agrees with this one." The items are at L333–341: "Diagnose the X7 flake", "The `dockerhub` drift gate", "A report to juniper-data about arc_agi", "Watching 6f".
- **Evidence:**
  - `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md` at `7b226ca0` (last written by #2025) has 0 matches for `x7|6f|starlette|anyio|arc_agi|drift gate|test_publish_env_policy|ci-tools-0-9-0|#2020`.
  - Its predecessor is the 09-17 handoff, so this document is four hops back. None of the six open juniper-ml PRs touches it.
  - Issue search finds no tracker in canopy (X7 test names), data (`arc_agi dataset_id`) or recurrence (`BlockingPortal`); the only hits are closed PRs.
  - Only the drift gate has another record: §10 of `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`.
  - This repeats note d's own diagnosis for 6f ("The record dropped it", L142–151), one level up.
  - The role-plays in `round2-laneA-full-read-artifact-first.md` and `round3-laneA-record-and-new-numbers.md` both started from this document, not from the tip, which is where the next session starts.
- **Minimal change:**
  - Add one line to the tip's banner: "Three open items from the 09-22 re-evaluation live only in the banner of `HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md`: the canopy X7 flake, the arc_agi report to juniper-data, and the 6f watch."
  - At L16, add "…, but does not carry the Startable items below".
  - Run the staleness pre-flight first: another session wrote the tip last.

**2. The first screen is spent restating the tip. NOISE, MAJOR (it decides the first-minute test).**
- **Passage:** L19–47, "> **What has moved since `HANDOFF_2026-09-22_ten-prs-landed-…` was written.**" (332 words).
- **Evidence:**
  - The tip's own banner (its lines 13–34) carries the same facts: items 3 and 4 done, item 1 narrowed to a liveness serve check plus a version check, v0.6.1 resolved, deploy still on 0.6.0 with the repin taken. L16 itself says the two agree.
  - The blockquote was the right answer to finding 3 of `round1-laneB2-amputation-executability.md` at a time when no PR had updated the tip. #2019 and #2025 removed that premise.
  - It is now a second copy of a moving fact, and one line of it is already stale (finding 3).
- **Minimal change:**
  - Replace L19–47 with the five bullets in section 3.
  - Move the two facts the tip lacks: cascor's publish path imports only `cascade_correlation` (into the serve-check bullet at L329–332), and the revision label `38f39cb8`, not `__version__`, is what identifies the 0.6.1 image (into note b).
  - Update L319's "(the blockquote above)".

**3. One owner-gated item was already done when it was written. REAL-DEFECT, MINOR.**
- **Passage:** L319–320 "The `0.6.1` wheel waits on the owner's `pypi` deployment approval (run `35795531350`)." Also L44–45.
- **Evidence:**
  - The wheel uploaded at 00:37:07Z, and run 35795531350 finished `success` at 00:37:13Z.
  - The "(run `35795531350`)" text was added in the round-3 fix pass, committed at 01:00:40Z.
  - After the freeze, and so not defects: 5 of the 7 PRs in the "awaiting merge" list (L347–357) have merged, and L499's "23 stale lines" at `main` now measures 13.
  - L49 says every fact was "re-probed on 2026-09-22", but L44 and L143 were probed on 09-23.
- **Minimal change:** mark the wheel as published at 00:37 UTC. Rewrite L49 to "re-probed between 2026-09-22 19:54 and 2026-09-23 00:46 UTC; later moves are not reflected". Don't chase the lists; the date line makes them correct as of a stated time.

**4. The termination test (§4) cannot close on a live-status banner the way this review runs it. PROCESS-DEBT, MAJOR.**
- **Passage:** L510 "**Round 4:** pending. This line is replaced when round 4 reports."
- **Evidence:**
  - Each fix pass re-probes facts that moved during the round, and the next round then finds the new text stale. Finding 3 is this round's instance: a lane's 00:35 probe (`round3-laneB-attack-the-round2-fix-pass.md` #12) was committed 23 minutes after the wheel shipped.
  - The mid-run messages to R3-A and R3-C already said to report post-freeze moves as stale. The fix passes chased them anyway.
  - The banner grew 2,610 → 3,954 → 4,893 words over two fix passes and never shrank. It is now 2.8 times the original document (1,765 words) and 11 times the tip's banner (449).
  - Every fix pass writes a "Round N+1: pending" line that only another round can clear.
  - §6 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` lists no failure mode for a target that moves faster than a round.
- **Minimal change:** freeze with finding 3's date line. Fill L510 with round 4's result, stating that its fixes were pointer and date edits, self-checked by reading them and re-running the verification block. Propose the missing §6 failure mode in a separate PR against that procedure.

**5. The procedure's only de-escalator was met in round 3, and the record does not use it. PROCESS-DEBT, MAJOR.**
- **Passage:** L419–424, "The census is a new instrument, and it was wrong in round 1 … That is the top-right cell."
- **Evidence:**
  - §3 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` (L96–98) lowers the required rigour when a result is "independently reproduced end-to-end by a different instrument".
  - `round3-laneA-census-adequacy.md`'s independent instrument "misses 0 lines and misjudges 0 lines", and it reproduced the post-merge prediction exactly.
  - R3-A and R3-C each rebuilt the five-run X7 list from 312 canopy runs with their own scripts.
  - I reproduced the census's post-merge result a third time.
- **Minimal change:** add one line to the sizing block: "After round 3 the census result and the X7 run list were reproduced end-to-end by independent instruments (§3 de-escalator); later checks re-run the instrument." Don't brief further census-adequacy or X7 lanes.

**6. "Seven merges hang on it" overstated the coupling, and the owner has now answered it. PROCESS-DEBT, MAJOR.**
- **Passage:** L418 "**Criticality is high.** This is a document of record, and seven merges hang on it."
- **Evidence:**
  - No sibling PR depends on the banner. Five are comment- or doc-only diffs of 2–9 added lines, each checked line by line (`round1-laneA3-independent-census.md` #10–11, `round2-laneB-attack-the-fix-pass.md` #20, `round3-laneB-attack-the-round2-fix-pass.md` #20).
  - deploy#227 was verified against the published image by 20:13Z on 09-22 (`round1-laneA2-published-artifacts.md`).
  - The owner merged five of them mid-round.
  - Of #2020's 3,642 added lines, 38 are edits to other files. The rest is the banner and in-place notes (551), the census and its mutation check (1,012) and the lane archive (2,041).
- **Minimal change:** change L418 to "seven PRs were reviewed alongside it; none depends on it".

**7. The round-3 merge gates changed no successor action. UNJUSTIFIED-BLOCKER, MAJOR (it bears on how round 4 is reconciled).**
- **Passage:** `round3-laneB-attack-the-round2-fix-pass.md`: "Before merging, fix findings 1, 2, 5 and 6".
- **Evidence:**
  - #1 (five X7 failures, not three): `round3-laneA-record-and-new-numbers.md` #6 found the same, rated it MINOR, and said "the conclusion stands and is stronger".
  - #5 (the wording of the census's limits): the banner had said since round 2 that exit 0 is not proof.
  - #6 ("15 of 15" over-stated): a three-word rewording would have closed it. Together with `round3-laneA-census-adequacy.md` #2, it was answered with 12 self-test cases, 9 mutants and 103 more census lines (816 → 919).
  - #2 fixed a real self-contradiction, but the action ("do not raise the bound") never changed.
- **Minimal change:** when reconciling round 4, treat "the census silently drops shape X" and "an evidence count is off" as post-merge docstring or record updates, not merge gates. The gate is the disclaimer at L250 and L372–373.

**8. Corrections 5 counts a canopy flake that predates the arc against the arc. OVER-CORRECTION (scope), MINOR.**
- **Passage:** L295 "the X7 flake had no owner (note f)."
- **Evidence:**
  - The test has been unchanged since canopy#585 (L168–169), and it failed on other branches before this arc's PRs tripped it (canopy#619, canopy#655).
  - The banner itself calls the original's handling "Sound advice for a PR" (L76).
  - L293–294 (the two live stale pins, and 6f) already falsify the headline.
  - Treating X7 as an arc item is what brings a 335-word canopy analysis (note f, L165–198) into a ci-tools handoff.
- **Minimal change:** drop L295. Cut note f to its heading plus "unowned; record where the worst gap falls before changing any bound", and move the run list to the validation record. Finding 1's pointer still names X7.

**9. Corrections 6 widens a CI claim in order to refute it. OVER-CORRECTION, MINOR.**
- **Passage:** L303–305 "**False for any environment that already holds an older release.** … `JuniperCascor1` holds … 0.8.0 and `JuniperCanopy1` holds 0.6.0 today; only a floor moves them."
- **Evidence:** the claim being corrected is about CI. The original says so itself: "The next green CI run in any of the nine repos settles it" (L752–754). L301–302 refutes it for CI (job 103226938137 installed 0.6.0). The conda environments are on a dev box that no CI floor touches.
- **Minimal change:** keep L298–302. Recast L303–305 as a separate aside: "Separately, a pre-populated environment keeps its release until someone installs with the new floor."

**10. Bookkeeping corrections that gate nothing. NOISE, MINOR.**
- **Passages:**
  - L279–281, Corrections 3 (CDT versus UTC dates);
  - L282–289, Corrections 4 (43/26/4/39/47/30/50/31, and 54 = 13 + 39 + 2);
  - L89–92, a CDT reconciliation of the worker's PyPI date;
  - note g's worktree count, which went 25 → 28 → 30 over three rounds.
- **Evidence:**
  - Both passes merged on 2026-09-11, and no action depends on their counts or dates.
  - The in-place notes at L548–550 and L554–556 already mark the wrong text where it stands.
  - At least ten lane findings re-derived these figures: `round1-laneA1-github-api.md` #4, #14; `round1-laneB1-refute-conclusions.md` #9; `round1-laneB2-amputation-executability.md` #9; `round2-laneB-attack-the-fix-pass.md` #3, #9; `round2-laneA-full-read-artifact-first.md` pass sizes; `round3-laneB-attack-the-round2-fix-pass.md` #4, #20; `round3-laneA-record-and-new-numbers.md` #5.
  - Worktree cleanup is owner-gated, and whoever does it will enumerate with `git worktree list`, not from a banner count.
- **Minimal change:** reduce Corrections 3 and 4 to one line each pointing at the in-place notes. Keep the numbering, because "Corrections 5/6" are cited at L13, L528, L595 and elsewhere.

**11. The census's figures are stated in several places, and one copy has already drifted. REAL-DEFECT, MINOR.**
- **Passage:** `util/ad-hoc/2026-09-22_ci_tools_pin_census_mutation_check.py:12–13` "(its Corrections 1 and validation record cite "15 of 15")". The banner cites 24 of 24 (L243, L369, L497).
- **Evidence:**
  - The re-run printed "self-test: 93 passed, 0 failed" and "24 of 24 mutations killed".
  - "93" appears at L241, L368 and L496; "24" at L243–244, L369 and L497–498.
  - Each fix pass had to edit every copy (31 → 81 → 93, 15 → 24). This one missed the script header.
- **Minimal change:** remove the number from that parenthetical. Cut the self-test and mutant history (L241–249) from Corrections 1. The Instrument block (L494–501) and the verification comments keep the figures.

**12. An ad-hoc script was hardened to reusable-tool standards, with no new real yield. PROCESS-DEBT, MINOR.**
- **Passage:** L241–249, "Round-3 lanes wrote 47 more, and 36 of those survived …".
- **Evidence:**
  - The census grew 432 → 816 → 919 lines, and its mutation check from nothing to 76 to 93.
  - Every real stale line that v3 catches and v2 missed had already been found by a lane reading the file:
    - `tests/test_coverage_gap_mapper_drift.py:53` (`round1-laneB1-refute-conclusions.md` #5);
    - `docs/QUICK_START.md:92` (`round1-laneA3-independent-census.md` #6);
    - canopy `ci.yml:270` (`round2-laneB-attack-the-fix-pass.md` #2).
  - It stays in `util/ad-hoc/` with no `tests/` suite and no `ci.yml` wiring.
- **Minimal change:** nothing in #2020 beyond finding 11. Later, either leave it as a documented one-off, or, before the next ci-tools minor, graduate it to `util/` with its self-test under `tests/` and wired into CI.

**13. The validation record carries process detail no successor needs. NOISE, MINOR.**
- **Passages:** L438–456 (Conduct: minute-level timestamps of the author's memory writes, a stray `.pyc`, a `git fetch`) and L488–489 ("**Declined.** A line in § What shipped begins `#163's` …").
- **Evidence:**
  - §7 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` asks for the instrument, sample, lanes and entry points, iterations, dissent and limits, not conduct timestamps.
  - The record is 1,292 words, 26% of the banner, though it is placed last.
  - "Declined" records a lint nit in `prompts/`, which markdownlint doesn't lint.
- **Minimal change:**
  - Keep one sentence: "R2-A's X7 finding was not independent of the author; round 3 re-derived it."
  - Move the rest to `reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/README.md`.
  - After this round, update L434–436: a ship-side lane has now run, and round 4's lanes also ran concurrently.

**14. The `juniper-data#319` citation should not gate the merge. UNJUSTIFIED-BLOCKER (pre-emptive), MINOR.**
- **Passage:** L338 "(42, since juniper-data#319)"; L484–485.
- **Evidence:** #319 is an issue, and PR #322 (merged 2026-09-03) made the change. That is the shape `round2-laneA-full-read-artifact-first.md` refuted for #401/#402. Here, though, #322's own field description in `juniper_data/generators/arc_agi/params.py` cites "(juniper-data#319)".
- **Minimal change:** none. If round 4's Lane A raises it, write "(juniper-data#322, for issue #319)".

## 3. The first-minute test

A fresh session needs:
1. This handoff is superseded, and its title and goal were false when written. Don't paste the goal or run its two greps.
2. Continue from `HANDOFF_2026-09-22_ten-prs-landed-and-the-published-worker-still-reports-0-4-0.md`; its banner is current.
3. Three open items exist only here: the canopy X7 flake (unowned; diagnose before touching a bound), a report to juniper-data about arc_agi's unchanged `dataset_id`, and the 6f watch (starlette is still 1.6.0). The `dockerhub` drift gate is also in §10 of `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_DOCKERHUB-SECRET-REGISTRATION-PROCEDURE.md`.
4. Still in flight: #2020, cascor#673, and the claimed worker-0.6.1 repin, now unblocked. Don't duplicate them. Every merge needs the owner's explicit approval in your session.
5. For stale ci-tools text, use the census. Exit 0 means "none of the shapes it parses", not "clean".

**The first screen delivers part of this.** L1–17 deliver bullets 1 and 2 well, and half of 5 (L13–14 say the greps are wrong, not what replaces them). L46–47 carry bullet 4's repin claim. The rest of the screen, L19–47, restates the tip the reader is about to open. Bullet 4's PR list and approval rule are at L347–357, and bullet 3 is about 300 lines down (L333–341) and absent from the tip. The swap in finding 2 fixes both in one edit.

## 4. Overall verdict: SHIP WITH CHANGES

The work is sound. Every load-bearing number I re-derived held: 93/93, 24/24, 54 live pins, post-merge exit 0, the 13 lines at `main`, and the QUICK_START block. The owner has already shipped five of the seven. Nothing blocks beyond the L510 edit the author has to make anyway. Finding 1 should go in that commit, and findings 2, 3 and 11 are cheap enough to go with it. The rest can follow later, or not at all.

**Termination test:** findings 1 and 3 change an action or a disposition. Finding 1 changes where a successor finds three open items; finding 3 moves the worker wheel from owner-gated to done. No other finding changes a number, disposition or action. By the letter of §4, that reopens the loop. By §3 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`, both are low-uncertainty pointer and date edits, checked by reading them, grepping the tip and re-running the verification block. That calls for a self-check, not a round 5.

**Changed:** no repository file, PR, comment, merge or deployment; the worktree's status is identical to the session start. Everything I wrote is under `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/97c72736-b353-43fe-9e6f-efaa8cf3be0c/scratchpad/lanes/r4b/`:
- scripts: `fetch_pr_files.py`, `pr_meta.py`, `checks.py`, `measure.py`, `pypi_check.py`, `census_sizes.py`, `open_prs_tip.py`, `issue_search.py`;
- fetched copies: `ml/` (#2020 at `f68380dd` plus the procedure), `prs/`, `base_handoff.md`, `banner_23238fe8.md`, `banner_50430e02.md`, `banner_4855bf8c.md`, `tip_main.md`;
- outputs: `r3fix.diff`, `census_postmerge.txt`, `census_main_now.txt`.
