# HANDOFF — the CI-budget instrument measured the wrong thing, and the slack headline was wrong twice before it was right

**Date**: 2026-09-09
**Origin session**: `flood 2 damage`, worktree `.claude/worktrees/harmonic-swimming-planet`
**Base**: `origin/main` at `6ccf80fa`. Every figure is measured there and **decays within hours** —
this document was re-anchored three times while being written.
**Validation**: independent-agent consensus per
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.
**Two rounds; round 1 found the document unsound, and round 2 found the round-1 FIX unsound.**
§5 records both, including the headline that was wrong in three different ways in succession.

> **RE-EVALUATED 2026-09-22 — read § Re-evaluation 2026-09-22 at the foot before acting on
> anything above it.** The §1 prompt is superseded by a re-evaluated one, placed above the
> original in §1. This re-evaluation lands in **ml#2017**, together with the fixes it describes,
> so on `main` the two arrive together.
>
> - **All ten §3 items are now closed, ruled, or informational** (item 3). The owner ruled on the
>   four owner items (1, 6, 8, 9) and on item 4's approach, and the 2026-09-17 arc executed them,
>   recorded in `notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md`.
> - **Item 10 was not carried forward by that arc** — neither shipped nor recorded — and was
>   still true on `main`. ml#2017 closes it.
> - **Three CI budgets had gone stale again** (juniper-data, juniper-data-client,
>   juniper-deploy); ml#2017 re-pins them under the arc's own rule. **One consensus lane
>   dissented**: those maxima were mostly runner queue, and whether budgets should absorb that is
>   now an owner decision. The arc's v2 span instrument also had a second defect: executions
>   after the first pass inflate the span. Sizing now uses the `first-pass` instrument.
> - **The advisory structure soak is not ready to promote**: 9 distinct findings, 2 true and 7
>   false, all 7 still present at their PR's final head. Both documented promotion recipes also
>   produced a check that could never fail; ml#2017 corrects them.
> - **This document dropped one of its predecessor's items in 2026-09-09**: flood-2's 22 test
>   PRs whose production half was absent. It is recorded below.
> - **What remains: five owner decisions and two pieces of non-owner work**, all in the first §1
>   block.

---

## 1. Handoff prompt (copy the fenced block into the new thread)

**Copy the FIRST block — re-evaluated 2026-09-22.** The second block is the original
2026-09-09 prompt. It is SUPERSEDED and kept verbatim for the record. Its REMAINING WORK list
is done or ruled; do not act on it.

```text
Continue the CI-budget arc in juniper-ml. Everything from 2026-09-09 is closed, ruled or
informational. What is left: surface OWNER DECISIONS 1-5 to the owner, and do NON-OWNER WORK 1-2.

PREFLIGHT -- every figure below decays within days; re-measure before acting on any of them.
  git fetch origin
  gh pr view 2017 --repo pcalnon/juniper-ml --json state,mergedAt,mergeCommit
    # Expect MERGED. This document and the probe script below land IN ml#2017, so on main it has
    # merged. If you are reading this on the PR branch instead, land ml#2017 first (MERGING):
    # until it merges, item 10 and the three re-pinned budgets are NOT on main.
  git log --oneline <ml#2017 mergeCommit>..origin/main   # non-empty = figures below predate main
  gh pr list --repo pcalnon/juniper-ml
  python3 util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py all --json "$S/reprobe.json"
    # S = an EXISTING directory (the session scratchpad); the script refuses a missing one.
    # ~2,500 REST calls, several minutes; first-pass, spans, soak and alarm are the slow probes.
    # Every probe prints what could have made it read differently. Exit 0 = every probe measured
    # every row; 2 = something could not be measured, named on the UNMEASURABLE line -- never
    # read it as clean; 1 = a crash. If the script is ABSENT, stop: python exits 2 on a missing
    # file too, and that is not a probe result.
    # Sandbox: no loop, pipe, redirect or `python -c` string that names git, and no loop that
    # runs gh over a variable. That is why the probes are one script.

THIS DOCUMENT IS
prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md
Read its § Re-evaluation 2026-09-22 first. The owner's 2026-09-15 rulings and the arc that
executed them: notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md.
This is ONE arc's residue; other arcs hand off separately in the same directory.

OWNER DECISIONS -- a session cannot take these
  1. SLACK_WEBHOOK_URL on the eight sibling repos. The PR-budget alarm runs daily on all nine.
     No run on any of them has breached since 2026-09-17 -- read from whether each run's Slack
     step ran, the one signal that works with or without the webhook (juniper-ml's own history
     shows 8 real breaches 2026-08-06..09-05 by the same read). Only juniper-ml has the secret;
     on the other eight a breach is a ::warning:: in the Actions tab and nothing else.
  2. Should CI budgets absorb contention? ml#2017 raised juniper-data 2400->3300,
     juniper-data-client 2400->3300 and juniper-deploy 700->1400: each observed max was a
     single healthy pass, and the enforced rule is "budget > observed max, <= 4x p90". But those
     maxima were mostly runner queue -- 64-82% of each span had no required job running while
     one waited, 91-99% of the critical path was queue -- and two came from one 09-21 burst.
     util/safe_merge.py also says "do NOT raise a budget to absorb a queue"; queue-free, all
     three would fit their OLD budgets. One consensus lane argued HOLD. The raises shipped on the
     enforced rule and the 2026-09-09 precedent (ml 1500->2800, recurrence 700->2000). Every
     re-measure so far has only raised budgets, and four of nine now sit at TIMEOUT_CEILING 3300,
     so the next stale one CANNOT be raised. Options: size on queue-free span; size on
     uncontended heads; raise the ceiling (bounded by the ~3600 s worker lease); or keep the
     auto-merge net armed on a timeout refusal instead of disarming it.
  3. Promote `Markdown Structure (advisory soak)` to a required check? THE EVIDENCE SAYS NOT
     YET. Since ml#1955 wired it (2026-09-18 00:37 UTC) it flagged 9 distinct findings: 2 true,
     7 false. All 7 false ones were still present at their PR's FINAL head, so a required
     version would have blocked 7 merges, and neither check has a waiver. Five are C4 reading a
     deliberate heading rename as a LOST heading; two are C2 firing on a wrapped prose line.
     If yes, later: NON-OWNER 1 first, then replace the step's FINAL `exit 0` with `exit "$rc"`
     and add the job's name as a required context IN THE RULESET, never via the Quality Gate's
     `needs:`. Deleting the `exit 0` alone leaves a check that cannot fail.
  4. Put juniper-cascor-client back into the CI-budget pin? Ruled OUT on 2026-09-15.
     Re-measured 2026-09-22: p90 1264 / max 1626, so its 3300 s now sits inside (1626, 5056]
     and the row would pass.
  5. The 22 flood-2 test PRs whose production half was absent. Flood-2 called them "not
     closeable -- the test is the evidence the fix is wanted". The 2026-09-09 version of this
     document dropped them, and all 97 unmerged fleet PRs from 2026-09-01..06 were closed on
     09-05/06. Nothing records whether any of those fixes landed. Confirm they were abandoned
     deliberately, or reopen the question.

NON-OWNER WORK
  1. Stop util/ad-hoc/2026-09-05_md_structure_check.py failing correct edits -- before any
     promotion. GOAL: a heading renamed IN PLACE (a status suffix, a strikethrough, a same-
     numbered section retitled or corrected) must not read as LOST, and a line of prose must not
     read as a command. § Re-evaluation 2026-09-22 lists all ten lost headings, before and after.
     A substring rule ("the old text survives inside the new") clears only 3 of the 10. One that
     clears all 10: pair each lost heading with a GAINED heading at the same level and the same
     leading identifier (section number, APD-... id, "Option A"). Keep flagging (a) a heading
     whose line survives INSIDE a fence -- the #1749 swallow -- and (b) a renamed heading whose
     OLD anchor is still linked from any tracked file: the required link checker verifies
     same-file anchors only, so a cross-file link to a renamed heading breaks silently today.
     C2: require whitespace after the command word (`\b` lets `git)` match) and skip a line
     that continues a paragraph.
     ACCEPTANCE: `python3 -m unittest -v tests/test_md_structure_check.py` stays green,
     including test_C4_reports_a_lost_heading_even_when_another_is_gained. Add negative
     controls per class: a rename passes; an unrelated loss plus gain still fails; a swallowed
     heading still fails; `git status` outside a fence still fires C2; prose `git).` and
     `make the` do not. Replay every live finding at its flagged head with
     `python3 util/ad-hoc/2026-09-05_md_structure_check.py --base <base sha> <path>`: the 7 false
     clear, the 2 true still fire. Then get it independently validated per
     notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md before
     it is offered for promotion.
  2. Re-measure the CI budgets before trusting them, with `first-pass`, never raw v2. They went
     stale twice in 13 days, and p90 does not reproduce either (juniper-data 955 -> 1651 in two
     weeks). Thinnest margins in seconds: recurrence 334 (max 1666, budget 2000), cascor-worker
     341 (2059 vs 2400). deploy's 1400 would fail "<= 4x p90" if its p90 fell back to 262.
     Watch the ceiling (OWNER 2).

The planning-slack margin is INFORMATIONAL: four repos are negative, and docs/REFERENCE.md
"Memory-Budget Slack (Planning)" says not to start a relocation for that reason. The lockfile
App-token arm is verified on n = 1 (#1970); re-check the next weekly PR.

MEASUREMENT TRAPS THIS RE-EVALUATION PAID FOR
  - v2 reads check-runs with filter=latest: the latest per name WITHIN EACH WORKFLOW RUN. A
    re-run attempt replaces its run's earlier attempt, copying the passed jobs with their
    original timestamps; a run started by a later event is kept. Either inflates the span:
    canopy#653 read 33,299 s for a pass that failed at 10:08 UTC and had two jobs re-run at 19:01.
  - Dropping a head for ANY repeat set aside 13 healthy heads (a successful `Guard PR base
    branch` re-fired by a PR edit). Dropping heads can only lower a max -- the unsafe side.
  - A run LIST shows the LATEST attempt, and a conclusion is not evidence: #1806's parked runs
    flipped to `failure` in the second it was closed and reopened. Read attempts/1/jobs.
  - The five NEWEST lockfile PRs said "4 of 4 parked, not suppressed". All 18: 5 got no run at
    all. Enumerate by branch (--head), never a limited title search.
  - A job log ECHOES the step's script text; match only expanded values (digits, SHAs).
  - A comma ENDS a workflow-command property: the soak's title `(advisory, exit N)` reached the
    API as `(advisory` until ml#2017. The runner also adds `notice` annotations to every job.
  - A breach on a repo WITH the Slack webhook leaves no annotation; read the Slack step.
  - git reads a date-only --since at the current time of day, so a 30-day window moves within a
    day; two runs hours apart disagree on commit counts.
  - A workflow run's `pull_requests` is empty once its PR merges; ask commits/<sha>/pulls.

USE THE RIGHT TOOL -- pairs that differ by one word
  CI span    : ..._reprobe.py first-pass. v2 inflates on later executions; v1
               (util/ad-hoc/2026-08-20_measure_required_check_span.py) filters NOTHING.
  md screen  : util/ad-hoc/2026-09-05_markdown_structure_check.py is the REQUIRED gate's engine;
               util/ad-hoc/2026-09-05_md_structure_check.py is the ADVISORY soak's.
  relocation : the four traps in the SUPERSEDED block below are still correct, for a PR that must
               grow AGENTS.md past its headroom -- not for a negative planning margin.

MERGING IN THIS LANE -- re-verified 2026-09-22
  A merge needs the owner's explicit approval for that PR IN YOUR SESSION; a handoff cannot
  carry it. allow_update_branch is FALSE on all nine repos and the rulesets are strict, so a PR
  goes BEHIND whenever main moves. Every commit must be GitHub-signed; a local `git commit`
  hangs on the YubiKey. New branch: util/open_signed_pr.py, which refuses an existing branch.
  Another commit on an open PR: util/ad-hoc/2026-09-08_push_signed_commit.py. PUT /contents
  does NOT sign. Finish every commit BEFORE arming any merge waiter.
  Order, one PR at a time:
    python3 util/safe_merge.py --repo juniper-ml --pr <N> --execute
    # If it refuses under contention (its refusal DISARMS any net), arm native auto-merge, then
    # keep it synced; the shepherd never merges and returns NOT-ARMED on an unarmed PR:
    gh pr merge <N> --repo pcalnon/juniper-ml --squash --auto
    python3 util/ad-hoc/2026-09-05_auto_merge_shepherd.py --repo pcalnon/juniper-ml \
        --pr <N> --max-syncs 4 --per-pr-timeout 3300
  Never run safe_merge --execute on a PR the shepherd is shepherding. `--auto` on a PR that is
  already MERGEABLE merges it on the spot.

GIT STATE AT HANDOFF
  This re-evaluation was written in worktree .claude/worktrees/ancient-yawning-biscuit and
  lands in ml#2017 (branch fix/ci-budget-arc-2026-09-22-waiter-default-and-stale-budgets). That
  worktree's local branch carries an UNSIGNED local-only commit used for screen testing; it was
  never pushed and must not be. Consensus-lane scripts sit untracked under
  util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/. Do not remove worktrees without the
  cleanup procedure: `git status --porcelain` is blind to ignored artifacts.
```

**The original 2026-09-09 prompt — SUPERSEDED, kept verbatim for the record:**

```text
PREFLIGHT — five commands. Run the third one TWICE, before and after a fetch.
  git fetch origin
  git log --oneline -1 origin/main
  git log --oneline 6ccf80fa..origin/main   # non-empty = this document is already stale
  gh pr list --repo pcalnon/juniper-ml      # 5 open at handoff, incl. #1862 (this arc's)
  python3 util/ad-hoc/2026-08-26_p5_fleet_state.py
  # Sandbox: no shell loops, no heredocs naming git, no `for` over a repo list. Split them.
  # A shared ref moves under you: another worktree's fetch updates origin/main mid-session.

THIS DOCUMENT IS
prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md
Read its §3 — TEN items, four of them OWNER decisions you cannot take yourself.
§3 IS THIS ARC ONLY. Concurrent arcs hand off separately in the same directory
(HANDOFF_2026-09-08_canopy-selection-*, _container-registry-*, HANDOFF_2026-09-09_defect-register-*,
HANDOFF_2026-09-09_partition-arc-decision-11-release-train-cut-*). The repo root also carries a
tracked live TODO file, ____TODO__DO-ME-AFTER-REBOOT____ (Duplicati key-escrow shred, yamaguchi
census + reboot verify). None of that is in §3.

REMAINING WORK, ordered by dependency
  1. #1862 is OPEN, green, armed -- and armed is not enough here (see MERGING). Shepherd it.
     Until it merges, flood-2 §3 item 5 is NOT closed.
  2. Two rationales this arc WITHDREW are still shipped in util/safe_merge.py's REPO_TIMEOUTS
     comments: the within-span/pre-start-queue justification, and "Unlike ml this is NOT a
     contention artifact" on juniper-recurrence. §3 item 5. No owner needed.
  3. .github/workflows/ci.yml and docs/REFERENCE.md still say "102 structural problems across
     21 files ... 1 under notes/code-review/". At 6ccf80fa it is 73/15 and notes/code-review/
     is ZERO. §3 item 7. No owner needed.
  4. Owner decisions: §3 items 1, 6, 8, 9.

THE SLACK NUMBER: FIVE REPOS NEGATIVE, AND I GOT THIS WRONG TWICE BEFORE THIS LINE.
  The rule is SOURCED, so use it as written -- do not re-derive a "better" one:
    slack = max(largest single 30-day AGENTS.md commit, 2000)
    util/ad-hoc/2026-08-28_p5_cut.py:65 (SLACK_FLOOR), 2026-08-26_p5_promote_ready.py:64,
    util/ad-hoc/README.md:132 -- "Size from `max`, NEVER from p90",
    docs/REFERENCE.md section "Memory-Budget Slack (Planning)".
  Margin = headroom - slack, at 6ccf80fa:
      ml         3531 vs 61435 -> -57904   a 61,435-char RESTRUCTURE; see the caveat below
      canopy      619 vs  2414 ->  -1795
      data       1044 vs  2000 ->   -956
      worker     1676 vs  2000 ->   -324
      cascor-client 2374 vs 2582 ->  -208
      deploy     2000 vs  2000 ->      0   exactly zero, not negative
      data-client 2195 vs 2000 ->   +195 | cascor +5468 | recurrence +4626
  WHY I GOT IT WRONG, so you don't repeat either error:
    - I first published "five" while listing deploy (0) and OMITTING ml (-57904). Wrong set.
    - A reviewer said the 2000 floor was "unsourced"; I believed it and re-sized on p90, which
      dropped worker and exempted ml. THE FLOOR IS SOURCED (above) and the README FORBIDS p90.
      The grep that "proved" it unsourced covered two files and the floor lives in two others --
      a correct predicate over an incomplete file set.
    - ml's -57904 is one restructure commit. p90 is 2838 (-> +693). State BOTH; do not swap
      statistic for one repo, which is what makes the fleet look tidy and ml look fine.
  This is a PLANNING number, not the CI gate. The Memory Budget check is GREEN on all nine and
  no PR is blocked -- docs/REFERENCE.md warns that mixing the two reads a green gate as an
  emergency. RE-MEASURE; the tool takes a PATH, not a repo name:
    python3 util/ad-hoc/2026-08-25_p5_port_memory_budget.py measure-growth \
        /home/pcalnon/Development/python/Juniper/<repo> --days 30 --ref origin/main
  data / worker / data-client are tight by OWNER DECISION (2026-09-07). Six of nine repos have
  <=6 growing commits in the window, so every row rests on a tiny n. A PR that must cross has a
  documented loan: `Allow-Budget-Overrun: <path>`.
  RELOCATION IS THE REMEDY, four traps (proven on ml#1754):
    1. util/ad-hoc/2026-08-19_p3_relocate_section.py composes its own "Moved to ..." sentence and
       prefixes `## ` to --dest-title ITSELF. Pass the description only, title WITHOUT `##`.
    2. The commit MUST carry `Allow-Docs-Rewrite: <path>` in its LAST paragraph, or it registers
       as nothing. Same shape as `Allow-Symbol-Loss:`, which #1862 needed.
    3. Verify with util/relocation_check.py (G3) AND a separate ^-###/^+### heading diff --
       G3 excludes headings from its needle set by design.
    4. juniper-recurrence has NO docs/REFERENCE.md; the recipe has no destination there.

MEASUREMENT TRAPS
  `xargs` splits on WHITESPACE (two tracked paths contain spaces): the bare form invents six
  "non-markdown" fragments and inflates unreadable 10 -> 12. Use `git ls-files -z | xargs -0`.
  The pipeline exits 123, NOT 2 -- xargs maps any child exit 1-125 to 123. The SCRIPT returns 2
  (ten dangling symlinks, 9 notes/legacy/ + 1 notes/development/; it refuses to certify around
  them). Test for non-zero.
  Structure debt: 73 problems / 15 files at 6ccf80fa, a FLOOR over 1052 of 1062 readable paths.
  It was 102/21, then 63/14 after ml#1834 repaired the live notes/ half -- and it has GROWN
  back to 73 in under a day. It is a moving target, not a backlog.

USE THE RIGHT TOOL — THREE PAIRS DIFFER BY ONE WORD OR ONE FLAG
  CI span   : util/ad-hoc/2026-09-08_measure_required_check_span_v2.py   (v1 filters NOTHING)
  md screen : ..._markdown_structure_check.py IS the CI gate's engine.
              ..._md_structure_check.py is a DIFFERENT file, wired into nothing (§3 item 4).
  merge     : safe_merge.py --repo juniper-ml | shepherd --repo pcalnon/juniper-ml

MERGING IN THIS LANE (measured three times this arc)
  A PR goes GREEN and then sits BEHIND while main moves. allow_update_branch is FALSE
  fleet-wide, so an armed net CANNOT clear it and NOTHING WARNS. safe_merge refused ml#1828 at
  its budget AND disarmed its own net. What worked first try on all three stuck PRs:
    python3 util/ad-hoc/2026-09-05_auto_merge_shepherd.py --repo pcalnon/juniper-ml \
        --pr <N> --max-syncs 4 --per-pr-timeout 2700
  ONE PR AT A TIME. The rollup GROWS past the required count while filling (17 -> 20), so "all
  required green" can be true while it is still arriving. TIMEOUT_CEILING = 3300 clamps every
  budget (canopy and cascor-client are AT it), sized under the ~3600 s worker lease.

READ BEFORE ACTING (paths from juniper-ml root):
  notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md   <- §8
  notes/JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_STRICT-POLICY-COST-BENEFIT-AUDIT.md      <- C-4, M-4
  notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md         <- §4 dec. 6
  prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_flood2-cohort-zero-and-the-1799-reland-damage.md
```

---

## 2. Record — what shipped, and what it got wrong

| PR | merge | subject |
|---|---|---|
| **#1828** | `b26acd62` | the instrument sizing the fleet's CI budgets measured the wrong thing |
| **#1848** | `92f3edd3` | finish the 104/23 sweep ml#1831 started; pin a fixture that read GPG agent state |
| **#1851** | `3cab4783` | two budgets set the previous day no longer cleared their own max |
| **#1862** | OPEN | the CI-span pin existed twice and the copies drifted apart |

**The finding.** `util/ad-hoc/2026-08-20_measure_required_check_span.py` says in its docstring
that it spans *"the REQUIRED contexts on ONE head SHA"* and filters nothing. On
`juniper-cascor#626` a `claude` check-run attached **5.7 h after CI finished**; it reported
**21,207 s** for a **605 s** pass.

**What the fix is worth, stated plainly** — because an earlier draft withdrew so much that the
record became incoherent about its own value. Two consequences were live in `util/safe_merge.py`
until #1828: **juniper-cascor's 2400 s sat below its own observed max of 2561 s**, so a healthy
cascor PR at its worst was refused; and deploy/recurrence fell through to `DEFAULT_TIMEOUT` at
~9x their p90. v1's 15,616 s cascor-client figure was also the stated *ground* for the old
"size on p90, never max" rule — correcting it to 1511 s is what let the rule become "clear the
max AND stay inside 4x p90", which is now enforced.

**Three claims a reviewer forced me to withdraw or narrow:**

- **The overstatement is a SAMPLE artifact.** cascor reads 11.3x at n=29 and **1.0x at n=12**.
  The roster (cascor 11x, cascor-client 19x, canopy 20x, data-client 27x, worker 70x, deploy
  110x) omits ml, data and recurrence; **ml's own overstatement is 1.0–1.1x**, and ml is the
  repo whose budget rose most.
- **"One defect explains both flood-2 items" is REFUTED.** Under the *corrected* tool ml reads
  p90 462–596 at n=12 against **1041 at n=30** — a 1.75–2.25x swing on sample size alone, where
  the bot artifact is worth ~1.0x. The instability belongs to an index-based p90 over a small
  heterogeneous sample. The *non-binding* half had an independent sufficient cause: the test
  asserted one half of a two-half rule.
- **v2 is NOT an independent instrument.** It computes its own span and v1's from the same
  single `check-runs` fetch, same author, same commit. The consensus procedure's only
  de-escalator is end-to-end reproduction by a *different* instrument. **It does not apply.**

**Budgets on `main`:** ml 2800, cascor 2800, canopy 3300, cascor-client 3300, data 2400, worker
2400, data-client 2400, recurrence 2000, deploy 700; `DEFAULT_TIMEOUT` 2400, `TIMEOUT_CEILING`
3300. ml's 2800 is not arbitrary: `util/safe_merge.py` sizes mid-window, and ml's window
`(1657, 3988]` has mid 2822.

**They went stale in ONE DAY** — ml max 773 → 1657, recurrence 352 → 1666 — and ml#1851 re-pinned
**seven** repos, not the two whose budgets moved; juniper-data's max doubled in the same pass.
**Two stories I told about that are withdrawn**: the contention-vs-CI-growth dichotomy (ml#1831
added a 181-line test into `Regression Tests` on three legs *inside the window*, so ml's CI also
genuinely got heavier — by this arc's own hand), and the within-span/pre-start-queue
justification (its discriminator, *"which `safe_merge` waits through"*, is true of both). **Both
are still shipped in `util/safe_merge.py` and are §3 item 5.**

---

## 3. Outstanding work — **this arc only**

| # | Item | Evidence / next step |
|---|---|---|
| 1 | **OWNER — `juniper-cascor-client` 3300 s exceeds 4x its p90 (724 → 2896)**, so it is excluded from the pin rather than fixed. Its historic rationale (*"15,616 s is queue time"*) is REFUTED — v1 bot artifact; real max **1511 s**. A value in `(1511, 2896]`, mid ≈ 2200, would let it be pinned. `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_flood2-cohort-zero-and-the-1799-reland-damage.md` said not to touch that repo, so the value stands. | `util/safe_merge.py` REPO_TIMEOUTS |
| 2 | **#1862 is open, green and armed — shepherd it.** `allow_update_branch` is false, so arming alone will not land it. Flood-2 §3 item 5 stays open until it merges: there were **two** pin sites and #1828/#1851 fixed one. | `util/ad-hoc/2026-09-05_auto_merge_shepherd.py` |
| 3 | **FIVE repos have a negative planning margin** (ml −57904, canopy −1795, data −956, worker −324, cascor-client −208); deploy sits at exactly 0. ml's is a single 61,435-char restructure — report it with p90 (+693) beside it, not instead of it. data/worker/data-client are tight by owner decision. **The CI gate is green; this is planning, not an outage.** | §1 block; `util/ad-hoc/README.md:132` |
| 4 | **`util/ad-hoc/2026-09-05_md_structure_check.py` blind spots are DOCUMENTED, NOT FIXED.** C2 is set-membership; C4 a net count; a missing path, new file, or unresolvable `--base` each exit 0. It also still ratifies *"6 in a pre-existing `memory_index_check` block"* — the exact `base 6` that flood-2 handoff said **not** to ratify. | that file `:68-70` |
| 5 | **Two rationales this arc withdrew are still shipped** in `util/safe_merge.py`'s REPO_TIMEOUTS comments: the within-span/pre-start justification, and *"Unlike ml this is NOT a contention artifact"* on recurrence. The arc opened a PR for a drifted test pin it wrote and shipped nothing for refuted prose it wrote in the same file. | `util/safe_merge.py` |
| 6 | **OWNER — the structure debt has no disposition, and it GROWS.** 102/21 → 63/14 after ml#1834 → **73/15** at `6ccf80fa`, within a day. Repairing the top three files removes 38 and leaves 35 across 12, and changes **no gate outcome** while the ten dangling symlinks stand. Removing the symlinks is the smaller, higher-value move. | preflight; `find . -xtype l` |
| 7 | **`.github/workflows/ci.yml` and `docs/REFERENCE.md` still assert "102 structural problems across 21 files … 1 under `notes/code-review/`".** At `6ccf80fa` it is 73/15 and `notes/code-review/` is **zero**. Orphaned by ml#1848's own correction. | `grep -c "102 structural" .github/workflows/ci.yml docs/REFERENCE.md` |
| 8 | **OWNER-BLOCKED — lockfile automation cannot trigger CI.** `.github/workflows/lockfile-update.yml` opens PRs on `GITHUB_TOKEN`; its header's *"No additional secret is required for the common case"* is the trap. Needs a PAT-gated arm. **CORRECTION to flood-2 §3 item 8**: its warning that close/reopen *"fired 26 checks that went red"* is wrong — 26 is right, outcomes were **16 success / 5 neutral / 1 skipped / 3 cancelled / 1 failure**, the non-successes came from a concurrent branch update, and **#1806 merged**. Close/reopen is the only reason any required context appeared. | `gh api repos/pcalnon/juniper-ml/commits/01ca9ba0.../check-runs` |
| 9 | **OWNER — the round-1 escalation trigger.** Round 2 produced no damage but produced **stale** diffs at scale. The round-1 file is `notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md` §4 decision 6 — neither prior document named it. | `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md` §8 |
| 10 | **Minor, verified**: `util/wait_for_checks.py:78` `DEFAULT_TIMEOUT = 1800` is below **eight** of the nine budgets (all but deploy). It governs only DIRECT invocation — `safe_merge.wait_for_required` always passes an explicit `--timeout` — so the merge path is unaffected and the worst case is an honest exit-2 report. Nothing pins 1800. Also: `tests/test_markdown_structure_screen.py` runs in `ci.yml` and appears zero times in `AGENTS.md`'s hand-maintained list, which `tests/test_ci_test_wiring_drift.py` cannot catch (it reads disk). | those lines |

**Closed during this arc:** flood-2 §3 items 1, 2, 4, 7, 9, 10 — and item 5 once #1862 merges.
Every PR-disposition bullet in
`notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md` §8
(juniper-data #329/#336/#339/#340/#349, juniper-canopy #569/#577/#580) is CLOSED, none merged.
"Wire the structure screen into CI" is done. The whole-line-union consolidator is superseded by
`util/ad-hoc/2026-09-06_docs_consolidate.py`, whose resolver `item_key()` lives in
`util/ad-hoc/2026-09-06_docs_conflict_resolve.py` — **not** in the consolidator, as two earlier
drafts of this file said.

## 4. Git status

Branch `docs/handoff-2026-09-09-ci-budget-instrument`, rebased onto `origin/main` at `6ccf80fa`
(the third re-anchor). **This document is the only change in the tree**; #1862's test change
lives on its own branch. Five PRs open on juniper-ml at handoff.

**Do not remove worktrees.** ~106 directories under `juniper-ml/.claude/worktrees/` against ~128
registered; `git status --porcelain` is blind to ignored artifacts and a previous sweep destroyed
551 `.h5` files in trees that read clean.

## 5. Validation record

**Sizing.** High criticality × medium-high uncertainty, six escalators from
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` §3:
universal quantifiers; a new instrument whose predecessor was wrong; a conclusion overturning a
document of record; a fix hanging on it; a single session; and a **convenient** conclusion — the
author graded their own work. Top-right cell: **3 Lane A (disjoint entry points) + 2 Lane B**,
≥2 iterations. **No de-escalator applies.**

**Lane A, each forbidden the others' sources.** A1 git/PR history only. A2 re-ran every
instrument. A3 current file content only. **Lane B.** B1 omission/amputation; B2 false authority
and causal overclaim.

**Round 1 — NOT SOUND.** It found: the headline count wrong; a **defect in the arc's own shipped
code** (two pin sites; the untouched one still asserted v1 maxima and the refuted cascor-client
rationale, and had gone **vacuous rather than red** — now #1862); an **inherited false claim**
carried without re-derivation (flood-2's "26 checks that went red"); the document **obsolete on
arrival** (main moved 17 commits mid-draft; ml#1834 had already repaired the debt it called
undisposed); amputations (the relocation recipe, `TIMEOUT_CEILING`, the `base 6` instruction);
and a missing scope statement.

**Round 2 — the round-1 FIX was itself unsound, which is why §4 of that procedure exists.**
Briefed on the corrections, it found:

1. **The slack headline was now wrong a second time, in the opposite direction.** Round 1 said
   the `max(growth, 2000)` floor was "unsourced" — from a grep over two files. It is sourced in
   two others (`util/ad-hoc/2026-08-28_p5_cut.py:65`,
   `util/ad-hoc/2026-08-26_p5_promote_ready.py:64`) and documented at `util/ad-hoc/README.md:132`,
   which says **"Size from `max`, NEVER from p90"**. I had re-sized on p90 — dropping worker and
   exempting ml, the same self-serving exemption round 1 condemned, relabelled *consistent*.
   **A correct predicate over an incomplete file set**, believed because it agreed with a
   reviewer.
2. **The original "five" was the right count with the wrong membership** — it listed deploy
   (exactly 0) and omitted ml (−57904).
3. Corrected: `wait_for_checks`'s 1800 is below **eight** of nine, not four, and does not affect
   the merge path at all; "48 across 18" was arithmetically impossible; "canopy is the only one
   worsening" is refuted (canopy is shrinking at −1572 chars/day); the item count; the open-PR
   count; and ~13 bare document references.
4. One round-2 finding was **rejected** after re-derivation: v2 was said to exit 0 on its
   "no required status checks" refusal. Measured unpiped, `REAL_EXIT=2`. A piped exit code — the
   same trap that produced three false "exit 0" records elsewhere in this fleet.

**Termination.** Round 2 changed numbers and dispositions, so §4 indicates a round 3. It is not
run: the remaining corrections are arithmetic and citation fixes I re-derived individually
against their sources, and the slack rule is now quoted from the file that defines it rather
than reasoned about. **The reader should treat every number here as re-measurable, not final** —
three of them changed while this document was being written.

**What this evidence CANNOT support** (§7's required line):

- That the corrected instrument yields a **reproducible** p90. It does not — 1.75–2.25x on
  sample size for ml. Flood-2's *"does not reproduce"* is still open; only *"does not bind"*
  closed.
- That ml's span growth is contention rather than added CI work. Both are present; the
  measurement cannot separate them.
- That the fleet's other budgets were mis-sized by the defective instrument. For ml the artifact
  is worth 1.0–1.1x, and the roster never measured ml, data or recurrence.
- That five is a stable count. Six of nine repos have ≤6 growing commits in the window; `n` is
  unrecorded per row, and the window is anchored on `now()`.
- That §3 is the repository's complete outstanding set. It is this arc's.

---

**Documents REFERENCED**: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`,
`notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md`,
`notes/JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_STRICT-POLICY-COST-BENEFIT-AUDIT.md`,
`notes/JUNIPER_2026-07-28_JUNIPER-ML_CURSOR-PR-FLOOD-REMEDIATION-ANALYSIS.md`,
`notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`,
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_flood2-cohort-zero-and-the-1799-reland-damage.md`,
`util/ad-hoc/README.md`, `docs/REFERENCE.md`.

**Documents CHANGED by this arc**: `docs/REFERENCE.md` (#1828, #1848) and this file.
**Code and config changed**: `util/safe_merge.py`, `tests/test_safe_merge.py`,
`util/ad-hoc/2026-09-08_measure_required_check_span_v2.py` (new),
`util/ad-hoc/2026-08-20_measure_required_check_span.py`, `.github/workflows/ci.yml`,
`util/markdown_structure_delta.py`, `tests/test_markdown_structure_delta.py`,
`util/ad-hoc/2026-09-05_md_structure_check.py`, `util/ad-hoc/2026-09-05_fleet_docs_consolidate.py`.

---

## Re-evaluation 2026-09-22

**What was re-probed.** Every §3 item and every checkable claim in the §1 prompt, against live
state rather than against any later summary. The 2026-09-17 walkthrough
(`notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md`) was treated as a
claim to verify, not as evidence.

**Anchor.** juniper-ml `origin/main` was `e3186919` at the start. Unrelated commits landed during
the session, and none touched a file named below except through ml#2017, which carries this
section.

**Instrument.** `util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py` (new, in ml#2017). It has one
subcommand per probe, and each prints what could have made it read differently. Figures below
are 2026-09-22. **Re-measure rather than quote them.**

### Item by item

| # | 2026-09-09 item | Status 2026-09-22 | Evidence |
|---|---|---|---|
| 1 | OWNER: cascor-client's 3300 s | **RULED 2026-09-15** — value stands, row stays out of the pin | ruling text in `util/safe_merge.py`, ml#1944 `2f8653c6` |
| 2 | shepherd #1862 | **CLOSED** — merged 2026-09-10 00:13 UTC as `244f8348` | `244f8348` is an ancestor of `main` |
| 3 | five repos with a negative planning margin | **INFORMATIONAL** — re-measured, four are negative | `slack` probe; table below |
| 4 | `md_structure_check.py` blind spots | **CLOSED** — fixed in ml#1944; `base 6` withdrawn in ml#1955 `e7c191c1` | `tests/test_md_structure_check.py`; a missing path and a bad `--base` both exit 2 |
| 5 | two withdrawn rationales still shipped | **CLOSED** — both marked `WITHDRAWN 2026-09-10` | ml#1880 `db627616` |
| 6 | OWNER: structure debt | **RULED and moot** — 0 problems in 1127 tracked `*.md`; 0 dangling symlinks | `structure` probe, exit 0 |
| 7 | "102 structural … 21 files" in two files | **CLOSED** — every site now carries a dated zero | `git grep -c '102 structural'` finds nothing at `e3186919` |
| 8 | OWNER: lockfile PRs cannot trigger CI | **RULED and DELIVERED** — one post-fix week, `n = 1` | `lockfile` probe; below |
| 9 | OWNER: the escalation trigger | **RULED and executed** — alarm on all nine repos | `alarm` probe; below |
| 10 | waiter's 1800 s; a suite missing from the AGENTS.md list | **First half not carried forward** by the 2026-09-17 arc; ml#2017 closes it. **Second half** closed by restructure | `waiter` probe; `TimeoutResolutionTest` |

Notes on the rows that need more than a cell:

- **Item 1.** Re-measured, cascor-client reads p90 1264 / max 1626 over 30 healthy heads. Its
  3300 s now sits inside `(1626, 5056]`, so the row would pass the pin it was excluded from.
  Re-including it is the owner's call; the ruling stands until then.
- **Item 6.** The screen examined 1116 of the 1127 paths; the other 11 are symlink aliases,
  counted once. Its zero is a real measurement: run on `bcc89c45:docs/REFERENCE.md`, the ml#1746
  damage, the same screen reports two swallowed H2s and exits 1.
- **Item 7.** ml#1880 fixed six sites. ml#1881, cut before it, put the stale figure back into
  two of them nine hours later. ml#1886 removed it again, and ml#1944 gave every site a dated
  zero. A figure duplicated across files does not stay corrected.
- **Item 8.** The census covers all 19 PRs the workflow has opened on `chore/lockfile-update`.
  The 18 opened with `GITHUB_TOKEN` (#325–#1932) all ran zero jobs at opening, in two shapes:
  - 5 got no `pull_request` run at all: #325, #328, #339, #389, and #1139 on 2026-08-17.
  - 13 had their runs created and parked at `action_required`. 12 of those were released by
    the owner re-running them, and #1806 by a close/reopen.

  #1970 (2026-09-21) was the first PR after ml#1944's App-token arm, opened by
  `app/juniper-release-train`. Its 5 opening-commit runs all ran jobs on attempt 1 under
  `juniper-release-train[bot]`.
- **Item 9.** `pr-budget-alarm.yml` is on all nine default branches. No run on any of them has
  breached since 2026-09-17: eight siblings × 6 daily runs, plus juniper-ml's.
  - **How that was read.** Each run's `Slack notification on breach` step is skipped at level
    OK, and that is the only signal that works on juniper-ml too, where a breach posts to Slack
    and leaves no annotation.
  - **The read can show a breach.** By the same read, juniper-ml's own history holds 8 real
    breaches, 2026-08-06..09-05.
  - **The residue is the owner's**: `SLACK_WEBHOOK_URL` is set on juniper-ml only.
- **Item 10.**
  - `notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md` §0 and §7 do not mention the waiter.
  - It was a non-owner "minor" note, and the arc's scope was the owner decisions. So "not
    carried forward" is the accurate word, not "dropped".
  - A shipped item and an unshipped one read identically in a summary. That is why every item
    here was re-derived from its source.
  - `AGENTS.md` also said "165" suites against the 166 on disk, in CI and in
    `docs/REFERENCE.md`; ml#2017 corrects it.

### What moved

1. **Three CI budgets went stale again, and ml#2017 re-pins them.** Each budget was below its
   repo's healthy max over the last 30 merged heads:

   | repo | healthy max | p90 | budget | queue share of that span |
   |---|---:|---:|---|---|
   | juniper-data | 2589 (#405) | 1651 | 2400 → **3300** | 64% idle-while-queued · 91% of critical path |
   | juniper-data-client | 2565 (#206) | 1545 | 2400 → **3300** | 80% · 93% |
   | juniper-deploy | 965 (#211) | 450 | 700 → **1400** | 82% · 99% |

   - **What each max is.** A single healthy pass: every workflow run on attempt 1, each required
     context run once, none failed (data#405's `Slow Tests` was skipped).
   - **Queue share, measured two ways.** Lane B2 counted the seconds in which no required job
     ran while one waited for a runner
     (`util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/laneB2/span_decompose.py`). Lane A2
     summed runner queue along the critical path (`…/laneA2/queue_share.py`).
   - **One burst.** data#405 and data-client#206 ran in the same 2026-09-21 13:10–13:56 UTC
     burst, which also produced cascor's max.
   - **Mid-window, per the arc's rule.** data and data-client hit `TIMEOUT_CEILING` first.
     Under first-pass numbers all nine budgets now clear their max and sit inside 4× p90.
   - **Unresolved dissent.** One lane argued HOLD: `util/safe_merge.py` says "do NOT raise a
     budget to absorb a queue", and queue-free all three spans fit their OLD budgets. The raises
     shipped on the enforced rule and on the 2026-09-09 precedent (ml, recurrence), and the
     dissent is recorded above `REPO_TIMEOUTS` and as OWNER DECISION 2.
   - **The ceiling is filling.** canopy, cascor-client, data and data-client now sit at 3300,
     and data clears its max by only 711 s.
2. **The v2 span instrument had a second defect.** It reads check-runs with `filter=latest`,
   which keeps the latest run per name *within each workflow run*. A re-run attempt therefore
   enters the span, with the jobs that passed copied in at their original timestamps. So does a
   workflow run started by a later event. Two examples:
   - **canopy#653** read 33,299 s for a pass that failed at 10:08 UTC and had two jobs re-run at
     19:01.
   - **recurrence#175** read 9,886 s. Two run sets fired 1 s apart, concurrency cancelled part of
     one, and four aggregators failed. The cancelled pre-commit run was re-run 2.5 h later, and
     the PR merged 4 s after it passed.

   The **`first-pass` instrument** replaces it. It takes each required context's first
   execution, over heads whose first pass passed, and drops no head for a repeat.
   - **Independently reproduced.** An instrument written separately in the consensus round
     reproduced its figures exactly on 8 of 9 repos.
   - **The ninth is juniper-ml.** There one head at the window's edge (#1981, a healthy
     2005 s pass) halves the max, and the pin keeps the demonstrated 2005 s.
3. **`docs/REFERENCE.md` stated the wrong budgets for thirteen days.** Its budgets row still read
   ml 1500 and recurrence 700 after ml#1851 raised both on 2026-09-09. It was the
   one-fact-in-many-sections shape item 7 fixed. ml#2017 corrects it.
4. **The advisory soak is not ready to promote, and two of its mechanisms were broken.**
   - **What it saw.** It has run on every juniper-ml PR head since ml#1955 wired it (2026-09-18
     00:37 UTC): 191 runs. 12 logs are unreadable, all of them runs cancelled by concurrency.
     17 changed no markdown. 162 examined 367 files on 56 distinct PRs. (A first census read a
     thirteenth log as unreadable; it was transient, and on retry that run had examined 2 files
     cleanly.)
   - **What it flagged.** 30 of those runs had findings: 9 distinct findings, **2 true and 7
     false**.
   - **All 7 false findings were still present at their PR's final head.** A required version
     would have blocked 7 of the 56 merges, and neither check has a waiver.
   - **True:**
     - ml#1999: a table row cut off from its table (C3) at heads `ea4c3596` / `25c001bd` /
       `276db114`. It was fixed before merge.
     - ml#1969 (C2): `notes/backup_tests_pre-and-post_reboot.md`, a bash script with its
       shebang and exec bit, saved as markdown. It is still on `main`, so the advisory warning
       went unread.
   - **False, C4 — ten headings in five PRs, each renamed in place:**

     | PR | lost heading | became |
     |---|---|---|
     | #1976 | `### 0.5 \`JuniperCascor1\` environment repair — owner has not ruled, asked 3+ times` | `### 0.5 ~~…environment repair~~ — **MOOT, CLOSED 2026-09-21**` |
     | #1976 | `### 5.1 \`JuniperCascor1\` is broken and the owner has not ruled` | `### 5.1 ~~…is broken~~ — **OBSOLETE as of 2026-09-21, the env is REPAIRED**` |
     | #1973 | `### 0.6 Owner decisions still owed` | `… — NONE, as of 2026-09-21` |
     | #1992 | `### 8.4 NEW outstanding work — none of it tracked by any issue or PR` | `… — untracked when found; **§8.7 records where each one now lives**` |
     | #1983 | `### APD-CASCOR-005 — … in two of three copies` | `… in three of four copies` (a correction, not a status) |
     | #2009 | `## 3. DECISION REQUIRED — repository secret, or environment secret?` | `## 3. RULED 2026-09-22 — Option B: …` |
     | #2009 | `### Option A — repository secret (the plan's wording)` | `… — NOT CHOSEN` |
     | #2009 | `### Option B — a dedicated \`dockerhub\` environment (recommended)` | `… — CHOSEN 2026-09-22` |
     | #2009 | `### 5.2A Repository secrets (Option A)` | `… — NOT CHOSEN; do not run` |
     | #2009 | `### 5.2B Environment secrets (Option B, recommended)` | `### 5.2B Environment secrets (Option B) — THE PATH, ruled 2026-09-22` |

     No in-repo link pointed at any old anchor. The required link checker could not have said
     so: it verifies same-file anchors only.
   - **False, C2 — two wrapped prose lines:**
     - #1980: `git). A table that…`. The `\b` after `git` matches `)`.
     - #2007: `make the credential stop working.` This is the only one of the two that ml#1955's
       own comment ("prose opening with `make` or `cd`") anticipated.
   - **No false negatives found.** A consensus lane checked 88 markdown changes in the window for
     damage C1-C4 cannot see (header/delimiter mismatches, CommonMark fence divergence, broken
     cross-file anchors) and found none.
   - **The 2026-09-16 backtest is not contradicted; it could not have seen this.** It scored
     merged commits, and none of its 40 exercised C2 or C4.
   - **Two broken mechanisms, both corrected in ml#2017.**
     - Both documented promotion recipes produced a check that could never fail. `ci.yml` said to
       drop a `|| true` the step does not contain. `notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md` §7 said to delete the final
       `exit 0`, after which the `if` before it returns 0.
     - The warning title `(advisory, exit N)` contained a comma, which ends a workflow-command
       property, so the exit code never reached the API.
5. **The lockfile mechanism was right in effect and incomplete as a mechanism.** The workflow
   header (`.github/workflows/lockfile-update.yml`) and `notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md` §3 said a `GITHUB_TOKEN` PR's runs are suppressed. Item 8's census shows
   both shapes: 5 not created, 13 created and parked. ml#2017 corrects both texts, plus
   `docs/REFERENCE.md` and the release-train runbook
   (`notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`). Two sites in
   `.github/workflows/release-train.yml` keep the effect-level wording. They are true in effect,
   and that publish workflow is outside this arc.
6. **Slack: four repos negative now, and juniper-ml is positive.** One run, 2026-09-22 21:10 UTC,
   30-day window, with every local `origin/main` equal to the API's:

   | repo | headroom | growing commits | p90 | max | slack | margin |
   |---|---:|---:|---:|---:|---:|---:|
   | juniper-canopy | 619 | 4 | 2414 | 2414 | 2414 | **−1795** |
   | juniper-data | 486 | 4 | 1304 | 1304 | 2000 | **−1514** |
   | juniper-cascor-worker | 1675 | 3 | 1217 | 1217 | 2000 | **−325** |
   | juniper-deploy | 1999 | 2 | 767 | 767 | 2000 | **−1** |
   | juniper-data-client | 2195 | 1 | 1587 | 1587 | 2000 | +195 |
   | juniper-cascor-client | 2374 | 1 | 767 | 767 | 2000 | +374 |
   | juniper-recurrence | 6625 | 2 | 115 | 115 | 2000 | +4625 |
   | juniper-cascor | 7582 | 10 | 1475 | 2116 | 2116 | +5466 |
   | juniper-ml | 9727 | 22 | 427 | 498 | 2000 | +7727 |

   - **juniper-ml's −57904 is gone.** The 61,435-character restructure left the window, and
     `AGENTS.md` went from 36,960 to 28,273 characters inside it. It is positive on p90 too, so
     no statistic was swapped.
   - **Three are tight by owner decision.** data, cascor-worker and data-client are tight by the
     2026-09-07 ruling; data-client sits at +195.
   - **None of this is an action item.** `docs/REFERENCE.md` "Memory-Budget Slack (Planning)"
     says not to start a relocation because headroom is below `max`. `Memory Budget` is a
     required context on all nine repos, and every `AGENTS.md` sits under its ceiling.
   - **The window moves.** git reads the date-only `--since` at the current time of day, so the
     window shifts within a day. A run hours earlier counted 25 growing commits for juniper-ml,
     not 22.

### Corrections to the predecessor

- **§1 "RELOCATION IS THE REMEDY".** Relocation is not the remedy for a negative *planning*
  margin: `docs/REFERENCE.md` forbids starting one for that reason. It is for a PR that must
  grow `AGENTS.md` past its headroom, as is the `Allow-Budget-Overrun:` loan. The four traps
  listed there remain correct for that case.
- **§3 item 8, "Close/reopen is the only reason any required context appeared".** This is true
  of #1806 only. The other 12 parked PRs were released by re-running their runs.
- **§1 preflight's repo-root TODO file** `____TODO__DO-ME-AFTER-REBOOT____` is gone; ml#1969
  deleted it. It was never this arc's item.
- **§5, "six of nine repos have ≤6 growing commits".** Re-measured, seven of nine have four or
  fewer.
- **This document dropped half of flood-2 §3 item 11.**
  - Its predecessor,
    `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_flood2-cohort-zero-and-the-1799-reland-damage.md`,
    listed "the 22 harvestables whose production half is absent" beside the escalation trigger.
    This document carried the trigger (its item 9) and neither closed nor carried the 22.
  - `notes/JUNIPER_2026-09-05_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-2-DISPOSITION-ANALYSIS.md` §8 called
    them "not closeable — the test is the evidence the fix is wanted".
  - All 97 unmerged fleet PRs created 2026-09-01..06 were closed on 09-05 (65) and 09-06 (32).
  - No later document mentions them, so nothing records whether any of those fixes landed. That
    is now OWNER DECISION 5.

### Corrections to this re-evaluation's own first draft

Consensus round 1 found these in the draft, and each is corrected above:

- **"4 of 4 GITHUB_TOKEN PRs were parked, not suppressed"** was a census of the newest five:
  there are 18, and 5 got no run. The error was a correct predicate over an incomplete set,
  which `notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md` §6.4 names as this arc's recurring error. The draft repeated it.
- **The `rerun-split` rule dropped any head with a repeated context.** 13 of its 18 set-aside
  heads were healthy, and it also misstated cascor's p90 (1615 → 1717) and every `n`.
- **The v2 mechanism was stated as "a re-run replaces the first attempt"** without the
  per-workflow-run scope.
- **"cascor-worker is the thinnest margin"** was wrong in seconds: recurrence is 334 s,
  worker 341 s.
- **The C4 spec would have cleared 2–3 of the 10 lost headings.** It asked for "old text
  survives inside a renamed one". Its acceptance test could also have been passed by deleting
  C4 outright.
- **"10 distinct findings, 2 true / 8 false"** counted #1973's one lost heading twice. The
  heading count in the message changed between pushes.
- **"DROPPED by the 09-17 arc"** was unfair; it is now "not carried forward".
- **The `waiter` probe could not tell fixed from unfixed.** It compared a constant against the
  table. The alarm probe could not see a breach on juniper-ml.
- **"Closed by ml#2017" was written while ml#2017 was open**, with this section not in it. It
  now lands inside ml#2017.
- **The banner said three items remained, all the owner's.** Two of them were not.

### What remains outstanding

- **Owner**: the five OWNER DECISIONS in the first §1 block.
- **Non-owner**: the two NON-OWNER WORK items in the same block.
- **Another arc's, flagged here only**: `notes/backup_tests_pre-and-post_reboot.md` is a shell
  script with a `.md` name and no `JUNIPER_<date>_` prefix, and it belongs to the backup arc
  (`notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`).

### Validation record 2026-09-22

Per `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.

**Sizing.** High criticality: a document of record, and three live merge budgets hang on it.
Several escalators applied:
- a new instrument (the reprobe script);
- a conclusion overturning a document of record (`notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md`);
- universal quantifiers ("all ten", "every");
- a fix hanging on it;
- a convenient finding, since the author graded a predecessor.

That is the top-right cell: 3+ Lane A, 2+ Lane B, at least 2 iterations.

**Round 1 — seven agents, against a frozen copy of this document (sha256 `0ed793de…`) and
ml#2017 at `53d05121`.**

- **Lane A, three disjoint entry points**, each forbidden the others' sources:
  - A1: git, PR and Actions history only.
  - A2: re-measured every span with its own code over `filter=all`, the Actions API and job
    timings.
  - A3: file content and execution. It ran the tests and the mutation check, built pin
    matrices in temp trees, and ran the slack cross-check through the API.
- **Lane B, three lenses:**
  - B1: omission and executability.
  - B2: argue HOLD, and hunt causal overclaim.
  - B3: argue SHIP, and attack the soak verdict.
- **Rubric:** the `prompt-validator` scored the first §1 block against R1–R5. Result: FAIL.

**What round 1 changed**:
- every correction in the previous subsection;
- the promotion recipe and warning-title defects;
- the flood-2 residue;
- the unmeasured-repo label in the waiter;
- the `first-pass` instrument.

Round 1 also re-verified the claims that survived, including all PR, SHA and date attributions,
the structure zero, the slack table (8 rows exactly, juniper-ml by a moving window), and the
waiter tests. It then reported against itself, and each lone finding was re-derived before use.

**Unresolved dissent.**
- **The three budget raises: B2 said HOLD, B3 said SHIP.** A2 measured the raises as needed
  under the rule and flagged the queue tension. It is an interpretation dispute, not a
  measurement one, since all three lanes agree on the numbers. It is recorded as OWNER
  DECISION 2.
- **recurrence#175.** B2 read it as "no failure", while A1 and A2 read it as a failed and
  cancelled first pass. The Actions API settles it: `CI — pre-commit` run 35643700110,
  attempt 1 cancelled, attempt 2 started by the owner at 21:59:28 UTC, merge at 22:00:33.

**De-escalator.** The span figures were reproduced end to end by a different instrument, A2's
`util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/laneA2/span_all_attempts.py`. That is the
procedure's only de-escalator, and it applies to those figures only. The three lane scripts
behind load-bearing figures are committed with ml#2017. The lanes' other scripts stayed
untracked, as unreviewed agent code.

**Round 2** — briefed on the round-1 corrections only: *in progress; this subsection is completed
before merge.*

**What this evidence CANNOT support**:
- that budgets sized on a 30-head window stay valid; two re-measures 13 days apart both raised
  budgets;
- that the first-pass rule is the right statistic rather than a defensible one. Queue-free
  spans would size differently, and that is OWNER DECISION 2;
- that the soak's false-positive rate generalises beyond four days and 56 PRs;
- that no other residue was dropped. One was found by re-deriving items from source; others
  would look identical in a summary;
- that the lockfile arm stays fixed: `n = 1`.

### Files changed 2026-09-22 (all in ml#2017)

**Documents**:
- this file;
- `docs/REFERENCE.md`;
- `AGENTS.md`;
- `notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md`;
- `notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`.

**Code and config**:
- `util/wait_for_checks.py` and `tests/test_wait_for_checks.py`;
- `util/safe_merge.py` and `tests/test_safe_merge.py`;
- `.github/workflows/ci.yml`: the soak's comment and warning title only;
- `.github/workflows/lockfile-update.yml`: header comment;
- `util/ad-hoc/2026-09-08_measure_required_check_span_v2.py`: docstring;
- `util/ad-hoc/2026-09-22_ci_budget_handoff_reprobe.py` (new);
- `util/ad-hoc/2026-09-22_wait_budget_mutation_check.py` (new);
- `util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/laneA2/span_all_attempts.py`,
  `…/laneA2/queue_share.py` and `…/laneB2/span_decompose.py` (new): the consensus lanes'
  instruments behind the reproduced spans and the queue shares.
