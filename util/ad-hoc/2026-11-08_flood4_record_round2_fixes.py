#!/usr/bin/env python3
"""
Apply the flood-4 record PR's second, third and fourth validation rounds (V4, V5 and V6) and the next session's
update to the record.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off (flood-4 disposition record PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; the V4 validator's findings in the
         session worktree's tmp/flood4/val-record/v4/findings.json (and fix_old_strings.txt,
         changelog_entry_rewrapped.txt); util/ad-hoc/2026-11-08_flood4_record_round1_fixes.py (round 1, same shape)

WHY THIS EXISTS
Round 1's corrections were validated by a fourth validator (V4), whose 15 findings each came with exact text. The
session that lands the record also has to add what happened after round 1 was written up: the owner's rulings 8 to
14, #2460's provenance for the paused-fit row, four defects found while the first fixes were built, round 2's triage
outcome, and the fixes' validation status. This applies all of it as exact, single-occurrence replacements, in one
pass, and refuses the whole pass if any old text is missing or ambiguous, so a half-applied correction cannot ship.
The comment above each fix names its V4 finding, or "S3" for the next session's update; V5's and V6's fixes were
folded into those entries, and only V5C-F4, F8, F10, F11 and V6-F7 have comments of their own. V5's two BLOCKERs,
the CHANGELOG's three-way rebuild and five renames, were done outside this script. It also corrects the PR and
commit bodies, which live in the session worktree's tmp/flood4/push/ml-record/ and are uploaded, not committed.

Usage:
  2026-11-08_flood4_record_round2_fixes.py [--check]
"""

import sys

REC = "notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md"
CHG = "CHANGELOG.md"
RDM = "reports/2026-11-08_flood4-disposition/README.md"
TTL = "tmp/flood4/push/ml-record/title.txt"
PRB = "tmp/flood4/push/ml-record/pr_body.txt"
CMB = "tmp/flood4/push/ml-record/commit_body.txt"

SESSION_OLD = "https://claude.ai/code/session_016H76AnqPKQEJzToJwgFC3h"
SESSION_NEW = "https://claude.ai/code/session_016H76AjZYVKxwr19XfGm6kE"

RULINGS_8_TO_14 = (
    "8. **The agent guard's brace cap**: \"Fail closed\". `util/claude_agent_guard.py` expands a brace list only up to"
    " `MAX_BRACE_ALTERNATIVES` (64), so a word that spells `.ssh` or `.gnupg` only in its 65th or a later alternative"
    " passes its credential check. The guard is to refuse such a word instead. That inverts the test #2517 carried"
    " (`tests/test_claude_agent_guard_brace_cap.py:63-71`), and #2470, which documents the bypass as the cap to keep,"
    " is to be rewritten; both ride in round 2's juniper-ml carriers.\n"
    "9. **Retry-After**: \"Both in round 2\". Two services truncate a `Retry-After`:\n"
    "   - juniper-service-core's failed-auth throttle (`security.py:468` used `int()` where the rate limiter, at"
    " `:236`, rounds up), from #2514;\n"
    "   - juniper-data's `RateLimiter`, which can send `Retry-After: 0` (`juniper_data/api/security.py:250`, `int()`"
    " with no floor of 1; the allowed path's `X-RateLimit-Reset`, `:254`, truncates the same way), and its failed-auth"
    " throttle (`:427`).\n"
    "\n"
    "   Both fixes go into round 2, juniper-data's in a code carrier of its own. The service-core one was then carried"
    " outside this arc, by juniper-ml#2524 (merged 2026-11-08 15:53Z; it is in juniper-service-core 0.7.2, which PyPI"
    " did not yet serve when this was written), and #2514 was closed with a comment naming it.\n"
    "10. **gitleaks-action outside juniper-data**: \"All, after data's lands\". Ruling 5 was given on juniper-data's"
    " case, and the same scan runs, at the same SHA, in the seven other repositories that use the action (all but"
    " juniper-recurrence). Only juniper-ml has had pull requests longer than the 30-commit page. After this ruling, a"
    " validator of juniper-data's fix found that the action's `--first-parent` walk cuts a scan short at any length"
    " (§4): modelled over every pull request of 30 commits or fewer, it drops commits in five of the eight"
    " repositories. The ruling predates that finding. Once juniper-data's fix has run green"
    " live, it is ported to juniper-ml, juniper-canopy, juniper-cascor, juniper-data-client, juniper-cascor-client,"
    " juniper-cascor-worker and juniper-deploy, one PR each. A port is not a copy: the repositories differ in where"
    " the scan's report is uploaded, whether the engine's version is pinned, and their own Gitleaks tests.\n"
    "11. **Four more defects, found while ruling 5's fixes were built**: \"Fix all four now\", each in its own"
    " validated, signed PR:\n"
    "    - juniper-cascor's own lifecycle manager has the paused-fit wedge (found by reading it and probing its state"
    " machine; not yet run at the manager level);\n"
    "    - juniper-service-core's stop-then-start race: a start soon after a stop, before the old fit's next event,"
    " cancels the stop, and the old fit's return then marks the new run `COMPLETED` (reproduced with a probe);\n"
    "    - juniper-cascor's own WebSocket manager has both resume losses (`src/api/websocket/manager.py:829-830`; in"
    " `training_stream.py`, the replay at `:390-416` and the promotion at `:290`);\n"
    "    - juniper-service-core's broadcast drops a socket whose send fails without closing it; juniper-cascor already"
    " fixed its copy (F-CASCOR-004).\n"
    "\n"
    "    The next update of this record gives each one's evidence and PR.\n"
    "12. **The paused-fit fix, asked again with the missing context** (2026-11-09): \"Confirm the fix\". A side agent noted that a"
    " `docs/REFERENCE.md` text had called the behaviour an invariant to preserve, and that ruling 5 was given without"
    " that fact. The text came only from a Cursor draft, juniper-ml#2460, and `main` never carried it as one (§4); no"
    " person ruled it.\n"
    "13. **Approval for the session that lands this record** (2026-11-09): the owner wrote \"merge approval granted"
    " for this work arc\", then chose \"Merge, update, close\" again. Ruling 1's approval held for its own session"
    " only; this one covers the next session, and adds the gitleaks port PRs to ruling 1's set: this record's PR, the"
    " defect-fix PRs, the gitleaks port PRs and the round-2 carriers.\n"
    "14. **juniper-ml#2507** (2026-11-09), a round-2 tests draft that pins four `docs/REFERENCE.md` sites to"
    " `pyproject.toml` (the Package Overview Version cell, the \"declares the following pins\" sentence, the current"
    " series row of the Ecosystem Compatibility matrix and the recurrence \"sets them to\" clause): \"Carry + extend"
    " propose.py\". `util/release_train/propose.py` edits none of the four, so the tests alone would fail every"
    " juniper-ml release proposal, and any other that moves one of those pins, until someone fixed them by hand; the script is to be extended to rewrite them, in a small carrier of"
    " its own.\n"
)

CHANGELOG_OLD = (
    "- **The Cursor flood-4 disposition record, with its render inputs and provenance scripts (round 1 complete).**\n"
    "  `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md` records how the 74-PR census was\n"
    "  disposed of: six carriers (juniper-data#518 and #519, juniper-canopy#797 and #802, juniper-ml#2517 and #2519) merged,\n"
    "  and all 68 census drafts assigned to them closed, 67 of them carried. It also records each carrier's 2 to 6 independent validation rounds, the\n"
    "  defects found on `main`, the per-PR disposition (§5), the process traps, and the owner's rulings of 2026-11-08:\n"
    "  round 2 takes 48 drafts; the launcher's effort default becomes `max`, and an explicit `auto` will send no\n"
    "  `--effort` flag; the three open defects get their own fixes; and juniper-ml#2271's one setting moved to user\n"
    "  settings, with its branch deleted. §5's six manifests and render config are archived under\n"
    "  `reports/2026-11-08_flood4-disposition/`, from which §5 re-rendered byte for byte (the renderer also reads each\n"
    "  PR's live state). The arc's 159 `util/ad-hoc/2026-11-07_flood4_*` and `2026-11-08_flood4_*` scripts, harvested\n"
    "  from the nine of its worktrees that held them, are kept as provenance. Before upload they were made to pass\n"
    "  gates G-TMP and G-PATH and the secret scan, 21 of 28 predicted CodeQL alerts were fixed (the other 7 are pydantic\n"
    "  fields the prescreen misreads), and 29 probes gained provenance headers; nothing they compute changed. Round 1's closing handoff is archived under\n"
    "  `prompts/thread-handoff_automated-prompts/`.\n"
)

# V4-F12's re-wrap (lines <= 115), plus the next session's update: the later rulings, 160 scripts, two handoffs.
CHANGELOG_NEW = (
    "- **The Cursor flood-4 disposition record, with its render inputs and provenance scripts (round 1 complete).**\n"
    "  `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md` records how the 74-PR census was\n"
    "  disposed of: six carriers (juniper-data#518 and #519, juniper-canopy#797 and #802, juniper-ml#2517 and #2519)\n"
    "  merged, and all 68 census drafts assigned to them closed, 67 of them carried. It also records each carrier's 2 to\n"
    "  6 independent validation rounds, the defects found on `main`, the per-PR disposition (§5), the process traps, and\n"
    "  the owner's rulings 1–7 of 2026-11-08: round 2 takes 48 drafts; the launcher's effort default becomes `max`, and\n"
    "  an explicit `auto` will send no `--effort` flag; three of the four open defect rows in §4 get their own fixes\n"
    "  now; and juniper-ml#2271's one setting moved to user settings, with its branch deleted. Later rulings decide that\n"
    "  the agent guard's brace cap is to fail closed, that the gitleaks fix is to be ported to the seven other\n"
    "  repositories that run the action, and that four more defects found while the first fixes were built are to be\n"
    "  fixed, each in its own PR; none of these has landed yet. §5's six manifests and render config are archived under\n"
    "  `reports/2026-11-08_flood4-disposition/`, from which §5 re-rendered byte for byte (the renderer also reads each\n"
    "  PR's live state). The arc's 160 `util/ad-hoc/2026-11-07_flood4_*` and `2026-11-08_flood4_*` scripts, from the\n"
    "  nine of its worktrees that held them, are kept as provenance. Before upload they were made to pass gates G-TMP\n"
    "  and G-PATH and the secret scan, 21 of 28 predicted CodeQL alerts were fixed (the other 7 are pydantic fields the\n"
    "  prescreen misreads), and 29 probes gained provenance fields; nothing they compute changed. Round 1's closing\n"
    "  handoff and its successor are archived under `prompts/thread-handoff_automated-prompts/`.\n"
)

FIXES = [
    # ---------------------------------------------------------------- the record
    # S3: the header.
    (REC, "round 2, round 3 and the §4 defect fixes are open (§8)",
          "round 2, round 3, the §4 defect fixes and four more defect fixes are open (§8)"),
    (REC, "**Updated**: 2026-11-08", "**Updated**: 2026-11-09"),
    # S3: sec 0 names the later rulings.
    (REC, "settle the fourth (the launcher's effort default), and settle juniper-ml#2271's setting.",
          "settle the fourth (the launcher's effort default), and settle juniper-ml#2271's setting. Later rulings (§8,"
          " 2026-11-08 and 2026-11-09) make the agent guard's brace cap fail closed, put both Retry-After fixes in round"
          " 2, port the gitleaks fix to the seven other repositories, fix four more defects that building the fixes"
          " found, confirm the paused-fit fix, and carry juniper-ml#2507 with `propose.py` extended."),
    # S3: #2514 left round 2 for another arc's PR.
    (REC, "Round 2 therefore holds 48 drafts, two more of them code fixes (#2513 and #2514).",
          "Round 2 therefore holds 48 drafts, two more of them code fixes (#2513 and #2514). #2514 was then carried"
          " outside this arc, by juniper-ml#2524 (§8, ruling 9)."),
    # V4-F4.
    (REC, "The builder added it before #2519 opened, checked by its own census; no seventh round ran.",
          "The builder added it before #2519 opened. The only check of that correction was the orchestrator's census of"
          " the copies (`…_api_key_copies_census.py`, 03:15Z); no seventh round ran."),
    # V4-F5.
    (REC, "Every finding was re-derived by the builder before it was applied. The builders applied one finding"
          " elsewhere: R8 targeted a tests-carrier docstring, so it moved to that carrier.",
          "Every finding was re-derived by the builder before it was acted on. Four of the juniper-ml docs carrier's were"
          " left to the orchestrator by design (two dependency findings and two merge-time ones), and one was applied"
          " elsewhere: R8 targeted a tests-carrier docstring, so it moved to that carrier."),
    # V4-F11; S3 (ruling 12's context): where the "invariant" wording came from.
    (REC, "and `mark_completed` refuses any state but `STARTED` (`lifecycle/state_machine.py:239-247`)."
          " `docs/REFERENCE.md` listed it as an invariant to preserve |",
          "and `mark_completed` refuses any state but `STARTED` (`lifecycle/state_machine.py:239-248`). Cursor draft"
          " juniper-ml#2460 (2026-11-04), titled \"… a paused fit stays paused\", had filed the behaviour in"
          " `docs/REFERENCE.md`'s shared service-core contracts, its list of load-bearing invariants. No person ruled"
          " that, and `main` never carried it as one: #2519 carried #2460 with the clause rewritten as a known defect."
          " Neither the lifecycle's design, juniper-ml#468, nor its build PR, juniper-ml#473 (both 2026-06-19), addresses"
          " a fit that returns while paused. No consumer imports service-core's lifecycle manager; juniper-cascor runs"
          " its own (§8, ruling 11) |"),
    # S3: the wedge fix's status (rulings 5 and 12; its validators).
    (REC, "**ruled: fix now** (owner, 2026-11-08; §8). A fix is built and under validation; no PR yet. Until it lands,"
          " #2519 describes the wedge as current behaviour |",
          "**ruled: fix now** (owner, 2026-11-08; §8), and confirmed once the owner had #2460's provenance (ruling 12)."
          " A fix was built. Its two validators returned SHIP-WITH-FIXES, and one found a regression in it: a stale fit"
          " returning while a new run is paused resumed or completed the new run. On 2026-11-09 the corrected fix was"
          " rebuilt on `main` `4bae7520` and put through a second validation round. Its code validator returned"
          " SHIP-WITH-FIXES with one more regression, a MINOR: on a paused completion, releasing the shared pause gate"
          " also wakes a stopped run's `fit` that the stop-then-start race (ruling 11) left parked there. Its docs"
          " validator returned REFUTED as written, with one MAJOR: the docs say a stale fit leaves the newer run's"
          " monitor alone, but only the settle is fenced. Its PR opens once both are corrected, after this record merges."
          " Until it lands, #2519 describes the wedge as current behaviour |"),
    # S3: the resume_ok fix's status.
    (REC, "**ruled: fix now** (owner, 2026-11-08; §8). A fix is built and under validation; no PR yet. The race was"
          " reproduced",
          "**ruled: fix now** (owner, 2026-11-08; §8). A fix was built, and its two validators returned SHIP-WITH-FIXES;"
          " among their findings, its new `replayed_through` keyword is public API, so it ships in a minor release of"
          " juniper-service-core, and juniper-ml's `[tools]` cap (`<0.8.0`) must rise when that release ships;"
          " juniper-cascor, juniper-data (its `[api]` extra), juniper-canopy and juniper-recurrence cap it `<0.8.0` too,"
          " on `main` and in their latest releases, so `juniper-ml[all]` stays on 0.7.x until theirs rise. No"
          " consumer imports service-core's `websocket` package; juniper-cascor runs its own copy (§8, ruling 11). On"
          " 2026-11-09 the corrected fix was rebuilt on `main` `4bae7520` and put through a second validation round: its"
          " code validator returned SHIP-WITH-FIXES with no correctness regression, and its docs validator returned"
          " REFUTED as written, with one MAJOR (the PR's session link is misspelt). Its PR opens once both are"
          " corrected, after this record merges. The race was reproduced"),
    # V4-F1 and V4-F2's row half; S3: both M-1 validators (A: mechanism, B: claims) -- the --first-parent loss
    # happens at any length (B-F1, A-04, confirmed from the two job logs), and #370's lost commits were scanned only
    # in the zero-rule era (A-04), so no "their own scans covered them" mitigation is claimed.
    (REC, "| juniper-data | gitleaks-action's pull-request scan reads one unpaginated page of the PR's commits (30 by"
          " default), so a longer PR would not be fully scanned | **ruled: fix now** (owner, 2026-11-08; §8). A fix is"
          " built and under validation; no PR yet. The fix's builder found the page to be the PR's **oldest** 30"
          " commits, so commit 31 onward, the head included, is never scanned, and `--first-parent` also drops commits"
          " a merge brought in (`src/gitleaks.js:113-117, 160-172` at the pinned SHA). juniper-ml#1797's run scanned 12"
          " commits of its 88. Seven Juniper repositories run the action the same way |",
          "| juniper-data | gitleaks-action's pull-request scan reads one unpaginated page of the PR's commits (30 by"
          " default), so a longer PR would not be fully scanned, and it walks that page with `--first-parent`, which"
          " drops the commits a merge brought in | **ruled: fix now** (owner, 2026-11-08; §8), for juniper-data. A fix"
          " was built. Its two validators returned SHIP-WITH-FIXES, none of their findings a regression, and on"
          " 2026-11-09 its corrections were applied, among them scanning a merge commit's own changes"
          " (`--remerge-diff`); its PR opens after this record merges. The fix's builder found the page to be the PR's"
          " **oldest** 30 commits, so the pull-request scan never reaches commit 31 onward, the head included. The"
          " action passes `--no-merges --first-parent` on every pull-request scan, whatever its length, so at any length"
          " the walk skips the commits a merge brought in as a second parent; and its range runs from the parent of the"
          " page's oldest commit, not from the merge base, so it can also walk into the base branch"
          " (`src/gitleaks.js:113-117, 160-172` at the pinned SHA)."
          " juniper-ml#1797's run (88 commits) logged `12 commits scanned.`, but only one of the 12, its commit 30, was"
          " the pull request's own; the other 11 were already on `main`. juniper-data#370 (18 commits, nine of them"
          " merges) logged `14 commits scanned.`: one of its nine non-merge commits, and 13 already on `main`. The"
          " seven other Juniper repositories that run Gitleaks in CI (all but juniper-recurrence) run the action the"
          " same way, at the same SHA, and the one fix built changes juniper-data alone: its `ci.yml`, its Gitleaks test"
          " file, two CI docs and its CHANGELOG (ruling 10). Only"
          " juniper-ml has had pull requests over 30 commits: four (#729, #1100, #1797 and #2045) |"),
    # V5C-F11: V4-F5's rewrite left "They" pointing at the findings.
    (REC, "They also replaced one validator's wording", "The builders also replaced one validator's wording"),
    # V5C-F10: #2522, not #2360, made the hook skip tmp/, and the checker reads .txt too.
    (REC, "The doc-link hook scans `tmp/` until juniper-ml#2360 lands, and one validator's 54 scratch `.md` copies had to"
          " be renamed `.md.txt` before any pre-commit run in that worktree.",
          "Until juniper-ml#2522 (merged 2026-11-09 00:27Z) the doc-link hook scanned `tmp/`, and it reads `.txt` as well"
          " as markdown, so neither keeping scratch as `.txt` nor renaming one validator's 54 scratch `.md` copies to"
          " `.md.txt` kept them out of it: all 13,857 broken links its last run here reported were under `tmp/`."),
    # V5C-F8: #2514 is closed, so 47 of the 48 are open.
    (REC, "- **Round 2**, 48 drafts:\n",
          "- **Round 2**, 48 drafts, 47 of them open (#2514 is closed, carried by juniper-ml#2524):\n"),
    # V4-F6 (sec 5 intro).
    (REC, "and each PR's live state. A re-render therefore shows the states at that moment,",
          "and each PR's live state and title. A re-render therefore shows the states and titles at that moment,"),
    # V4-F14.
    (REC, "The record PR's validator found two failures of required checks in the harvested scripts:",
          "Two of the record PR's validators ran them on the harvested scripts and found two failures the required"
          " checks would have reported:"),
    (REC, "The paths now come from `os.path.expanduser` or `Path.home()`, which give the same strings on this host;"
          " one line of recorded findings text keeps its literal under G-PATH's pragma.",
          "Six code paths now come from `os.path.expanduser` or `Path.home()`, which give the same strings on this host,"
          " a docstring usage line now says `~/`, and one line of recorded findings text keeps its literal under"
          " G-PATH's pragma."),
    # V4-F10.
    (REC, "A run with `TMPDIR` elsewhere has not isolated it.",
          "No run with `TMPDIR` outside a checkout has been made to confirm it."),
    # V4-F6 (sec 7).
    (REC, "The archived inputs re-render §5 byte for byte.",
          "With an authenticated `gh`, the archived inputs re-rendered §5 byte for byte on 2026-11-08; a later re-render"
          " shows each PR's live state and title (§5)."),
    # S3: this script, and the count it brings.
    (REC, "  - `…_record_round1_fixes.py` applies this record's first validation round.\n",
          "  - `…_record_round1_fixes.py` applies this record's first validation round.\n"
          "  - `…_record_round2_fixes.py` applies the second, third and fourth validation rounds (V4's, V5's and V6's"
          " findings) and the next session's update: rulings 8–14, the new defects, round 2's triage outcome and the"
          " fixes' status.\n"),
    (REC, "With these, the PR ships 159 scripts.", "With these, the PR ships 160 scripts."),
    # S3: the rulings header now spans two days.
    (REC, "**The owner's rulings of 2026-11-08** (option labels verbatim):",
          "**The owner's rulings of 2026-11-08 and 2026-11-09** (option labels verbatim, less the \"(Recommended)\""
          " marker on the option each question advised):"),
    # V4-F7.
    (REC, "Claude Code reads `.claude/settings.local.json`, which 2.1.319 resolves, for a worktree session, to the main"
          " checkout's untracked copy (as `main`'s `docs/REFERENCE.md` also says). That copy holds no `idleCompaction`"
          " key.",
          "Claude Code reads `.claude/settings.local.json`: 2.1.319 resolves it, for a worktree session, to the main"
          " checkout's untracked copy (as `main`'s `docs/REFERENCE.md` also says), and also reads the worktree's own"
          " copy, if it has one, as \"the legacy local settings file\". Neither that copy nor the four byte-identical"
          " copies in older worktrees holds an `idleCompaction` key."),
    # V4-F15.
    (REC, "It lives in `JuniperCascor1`, which supplies the `pre-commit` and `juniper-check-doc-links` on `PATH`, and"
          " that environment got its own check:",
          "It lives in `JuniperCascor1`, which supplies the `pre-commit` and `juniper-check-doc-links` on `PATH`"
          " (`JuniperCanopy1` holds a separate 0.6.0, untouched), and `JuniperCascor1` got its own check:"),
    # S3: rulings 8-14 (V4-F2's "no ruling covers them" is now ruling 10).
    (REC, "Each goes only after its PR is confirmed merged and its `tmp/` is checked under the retention rule.\n",
          "Each goes only after its PR is confirmed merged and its `tmp/` is checked under the retention rule.\n"
          + RULINGS_8_TO_14),
    # V4-F9; S3: round 2's triage outcome in one line.
    (REC, "They were triaged against `main` on 2026-11-08 and are carried in per-repository tests, docs and code"
          " carriers; the launcher's effort fix rides in the juniper-ml code carrier. #2484 is stacked on #2480's own"
          " branch, and #2513 follows up #2474. The next update of this record holds the triage table.",
          "All 48 were triaged against `main` on 2026-11-08, and the carried ones are to land in per-repository tests,"
          " docs and code carriers; the launcher's effort fix rides in the juniper-ml code carrier. #2484 is stacked on"
          " #2480's own branch, and #2513 follows up #2474. The triage leaves seven uncarried, still open and to be"
          " closed as superseded or duplicates (#2471,"
          " #2476, #2477, #2486, #2488, #2500 and #2501), and puts the other 40, whole, in part or rewritten, into"
          " juniper-ml's code, tests and docs carriers and juniper-data's and juniper-canopy's tests and docs carriers;"
          " #2514 went to juniper-ml#2524 instead, and juniper-data's code carrier holds ruling 9's fix and no draft."
          " The next update of this record holds the triage table."),
    # V4-F13; S3: rulings 10, 11 and 14 add open work.
    (REC, "- **The three defect fixes** (ruling 5) and the deferred `JuniperCanopy1` upgrade (ruling 6).\n",
          "- **The three defect fixes** (ruling 5), and the `JuniperCanopy1` upgrade, not done because its check failed,"
          " which waits for the owner (ruling 6).\n"
          "- **The four further defect fixes** (ruling 11), and the gitleaks fix's port to the seven other repositories"
          " once juniper-data's has run green live (ruling 10).\n"
          "- **#2507's tests, with `util/release_train/propose.py` extended** (ruling 14), in the juniper-ml carriers.\n"),
    # V4-F8.
    (REC, "- **The manifests' evidence.** The archived manifests cite their builders' `tmp/` logs (194 paths, such as"
          " `claim_check.log`), which are not in `reports/`. They are archived before the worktree cleanup (ruling 7)"
          " removes them.",
          "- **The evidence in `tmp/`.** The archived manifests cite 167 paths under `tmp/flood4/` (194 references, such"
          " as `claim_check.log`): the juniper-data and juniper-canopy manifests' in the orchestrator's worktree, the"
          " juniper-ml manifests' in their builders'. This PR's own corrections rest on `tmp/flood4/val-record/`,"
          " `tmp/flood4/round2-triage/`, `tmp/flood4/round2-fixes/pristine/` and `tmp/flood4/round2-session/codeql_orig/`"
          " in the orchestrator's worktree, on"
          " each fix's validator findings under `tmp/flood4-fix/` in that fix's worktrees (each service-core fix has two:"
          " its first build's and its rebuild's), and on `tmp/val-a-m1/` in juniper-ml's primary checkout. None is in"
          " `reports/`. Each worktree copy is to be archived before the worktree cleanup (ruling 7) removes it, and"
          " `tmp/val-a-m1/`, which that cleanup does not touch, falls under the retention rule."),
    # S3: sec 9 lists the second handoff this PR ships.
    (REC, "- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_flood4-round1-carriers-landed-record-next.md`"
          " (new), round 1's closing handoff;\n",
          "- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_flood4-round1-carriers-landed-record-next.md`"
          " (new), round 1's closing handoff;\n"
          "- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_flood4-record-validated-fixes-built-round2-triaged.md`"
          " (new), its successor's, archived as written: where it differs from this record (its table lists ruling 12"
          " among the rulings of 2026-11-08, it calls #473 the lifecycle's design PR, and its title calls the three fixes"
          " validated), this record is current;\n"),
    # V6-F7: round 2's helper scripts need a stated home before the cleanup.
    (REC, "- **Any drafts this record's PR draws.** None had followed a PR since 00:58Z (§6). Any that do are covered by no"
          " ruling.\n",
          "- **Any drafts this record's PR draws.** None had followed a PR since 00:58Z (§6). Any that do are covered by no"
          " ruling.\n"
          "- **Round 2's helper scripts.** The `util/ad-hoc/2026-11-0[89]_flood4r2_*.py` scripts round 2's agents wrote"
          " into the orchestrator's worktree are untracked there. Among them are the juniper-data gitleaks fix's five,"
          " renamed out of this PR's glob. They are to be committed as provenance before the worktree cleanup (ruling 7),"
          " which checks only `tmp/`, removes that worktree. Those five still fail G-PATH and G-TMP"
          " (`…_jd-gitleaks_run_pytest.py:50-51` and `:16`).\n"),
    # ---------------------------------------------------------------- the reports README
    # V4-F8.
    (RDM, "The manifests cite their builders' `tmp/` logs as evidence (such as `claim_check.log`); those logs are not"
          " part of this archive.",
          "The manifests cite logs under `tmp/flood4/` as evidence (such as `claim_check.log`): the juniper-data and"
          " juniper-canopy manifests' in the orchestrator's worktree, the juniper-ml manifests' in their builders'."
          " Those logs are not part of this archive."),
    # ---------------------------------------------------------------- the CHANGELOG
    # V4-F12, plus S3.
    (CHG, CHANGELOG_OLD, CHANGELOG_NEW),
    # ---------------------------------------------------------------- the PR title, body and commit body
    (TTL, "round 1 complete, rulings of 2026-11-08, render inputs", "round 1 complete, rulings 1-14, render inputs"),
    # V5C-F4: rulings 1-7 are not the only rulings of 2026-11-08.
    (PRB, "- Records the owner's rulings of 2026-11-08 (§8):", "- Records the owner's rulings 1–7 of 2026-11-08 (§8):"),
    # V4-F3 items 1-5.
    (PRB, "All 68 census drafts they carry are closed, each with a comment naming its carrier.",
          "All 68 census drafts assigned to them are closed, each with a comment naming its carrier: 67 are carried,"
          " and #2440 was closed with #2519 without being carried."),
    (PRB, "The manifests are archived under `reports/2026-11-08_flood4-disposition/`, from which §5 re-renders byte"
          " for byte.",
          "The manifests are archived under `reports/2026-11-08_flood4-disposition/`, from which §5 re-rendered byte"
          " for byte on 2026-11-08. The renderer reads each PR's live state and title through an authenticated `gh`;"
          " without one it still exits 0, printing every carrier as \"(open)\" and every state as \"?\"."),
    (PRB, "  - the three open defect rows of §4 are fixed in their own PRs;",
          "  - three of §4's four open rows (the paused-fit wedge, the `resume_ok` broadcast losses and gitleaks-action's"
          " unpaginated commit list) are to be fixed now, each in its own validated, signed PR; each was built, its two"
          " validators returned SHIP-WITH-FIXES (one finding in the paused-fit fix was a regression), and each is"
          " corrected and validated again before its PR opens, after this record merges;"),
    (PRB, "  - the host's juniper-ci-tools is upgraded to CI's 0.9.1; `JuniperCanopy1` waits, because four live canopy"
          " E2E legs run from it.",
          "  - host state: the ruling's check failed for `JuniperCanopy1`, from which four live canopy E2E legs"
          " (another arc's) run, so its juniper-observability 0.4.0 and juniper-service-core 0.5.0 stay until the owner"
          " decides; on a per-environment reading of the ruling, the host's juniper-ci-tools in `JuniperCascor1` went"
          " from 0.8.0 to CI's 0.9.1.\n"
          "- Records the later rulings (§8, 8–14; 8–11 of 2026-11-08, 12–14 of 2026-11-09): the agent guard's brace cap"
          " is to fail closed; both Retry-After fixes were put in round 2, and the service-core one has since landed"
          " outside this arc, in juniper-ml#2524; the gitleaks fix is to be ported to the seven other repositories once"
          " juniper-data's has run green live; four more defects, found while the first fixes were built, are to be"
          " fixed now, each in its own PR; the paused-fit fix is confirmed with #2460's provenance in hand; the landing"
          " session's approval is \"Merge, update, close\" again; and #2507 is to be carried with `propose.py`"
          " extended.\n"
          "- Records round 2's triage outcome in one line (§8); the next update of this record holds the table."),
    (PRB, "- Ships the arc's 157 provenance scripts, harvested from its nine worktrees before they are cleaned up, and"
          " round 1's closing handoff.",
          "- Ships the arc's 160 provenance scripts, from the nine of its worktrees that held them before those are"
          " cleaned up, and two handoffs: round 1's closing one and its successor."),
    # S3: the CHANGELOG is rebuilt on the PR's base; the second handoff ships.
    (PRB, "one `[Unreleased]` / `### Added` entry, built on `main` `8d73d441`.",
          "one `[Unreleased]` / `### Added` entry, merged three ways onto the PR's base `main`."),
    (PRB, "- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_flood4-round1-carriers-landed-record-next.md`"
          " (new).",
          "- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_flood4-round1-carriers-landed-record-next.md`"
          " and `…_flood4-record-validated-fixes-built-round2-triaged.md` (both new)."),
    # V4-F3 items 6-11.
    (PRB, "(157, new; record §7):", "(160, new; record §7):"),
    (PRB, "  - Changes to harvested scripts before upload, none behavioural:",
          "  - Changes to harvested scripts before upload; none changes what a script computes:"),
    (PRB, "The detector lines carry `# tmp-path-literal: allow`, and the docstrings were reworded.",
          "The detector and guard lines carry `# tmp-path-literal: allow`, and the docstrings were reworded.\n"
          "    - Gate G-PATH (`util/home_path_literal_check.py`, on `main`; the required Pre-commit and Regression Tests"
          " jobs run it): 8 lines in 7 scripts spelled the owner's home directory. Six code paths now come from"
          " `os.path.expanduser` or `Path.home()`, which give the same strings on this host; a docstring usage line says"
          " `~/`; one line of recorded findings text keeps its literal under `# home-path-literal: allow`.\n"
          "    - One probe sent RFC 6455's sample `Sec-WebSocket-Key` nonce, which gitleaks' generic-api-key rule"
          " matches; it is now built at run time from its decoded text, so the request is byte-identical."),
    (PRB, "unread names dropped or underscored", "unread names underscored"),
    (PRB, "    - 29 validator probes got the `util/ad-hoc/README.md` provenance header.",
          "    - 29 validator probes gained the `util/ad-hoc/README.md` provenance fields: 26 the full header, and three"
          " round-5 probes only `Related:`, which their usage text (they print their docstring) now shows too.\n"
          "  - The record's two correction passes are scripts too: `…_record_round1_fixes.py` and"
          " `…_record_round2_fixes.py`."),
    # V4-F3 items 12-16, 18.
    (PRB, "re-renders §5 byte for byte: 74 rows",
          "re-rendered §5 byte for byte on 2026-11-08, with an authenticated `gh`: 74 rows"),
    (PRB, "on all 157 scripts: clean.", "on all 160 scripts: clean."),
    (PRB, "on all 157 scripts: 7 predicted alerts, down from 28.", "on all 160 scripts: 7 predicted alerts, down from 28."),
    (PRB, "0 literal lines in the 157 scripts.",
          "0 literal lines in the 160 scripts.\n"
          "- `util/home_path_literal_check.py` (gate G-PATH) on the 160 scripts: PASS, 0 literal lines.\n"
          "- gitleaks 8.24.3 (the pinned engine) `dir` with the repo's `.gitleaks.toml` and `.gitleaksignore` on every"
          " file this PR adds: no leaks; the same `dir` scan of a copy with one planted token reports it, so the scan"
          " reads the files."),
    (PRB, "157 of 157 scripts.", "160 of 160 scripts."),
    # V4-F3 item 17: the pre-commit and link-check line is re-measured on the final files.
    (PRB, "- The pinned pre-commit hooks on the record, the CHANGELOG, the handoff and the `reports/` files: all pass"
          " except the link check. Its whole-tree scan also reads the session's untracked `tmp/` scratch copies, which"
          " CI never sees. `juniper-check-doc-links` with CI's arguments plus `--exclude tmp`: all links valid across"
          " 1622 files.",
          "- The pinned pre-commit hooks on the record, the CHANGELOG, `…_record_round2_fixes.py` and `…_record_freeze.py`,"
          " on the PR's base `main`: every hook in scope passes, the link check included (since juniper-ml#2522 it skips"
          " `tmp/`), and none changes a byte. The markdown linter's scope excludes `notes/` and `CHANGELOG.md`, and the"
          " secrets hook scans staged changes only, so its pass says nothing here; the gitleaks line above is the real"
          " scan. `prompts/` and `reports/` are in pre-commit's global exclude, so no hook is run on the handoffs or the"
          " archived files by name; only the link check, which walks the tree, reads the handoffs and the archive's"
          " README, and it passed.\n"
          "- `juniper-check-doc-links` with CI's arguments plus `--exclude tmp`, on the PR's base `main` with this PR's"
          " files: all links valid across 1638 files."),
    # V4-F3 item 19; ## Requirements.
    (PRB, "VALIDATION_PLACEHOLDER",
          "Independent rounds, each re-deriving its claims from the source of truth (BLOCKER / MAJOR / MINOR):\n"
          "\n"
          "- V1, the facts: 0 / 2 / 12.\n"
          "- V2, the conclusions and untested assumptions: 2 / 2 / 17.\n"
          "- V3, the files that ship and their structure: 2 / 0 / 7. The BLOCKERs were G-PATH in 7 scripts and a"
          " gitleaks match on RFC 6455's sample nonce.\n"
          "- V4, round 1's 36 corrections and the G-PATH and secret pass: 0 / 3 / 12.\n"
          "- V5, this update (V4's corrections, rulings 8–14, the new defects and the fixes' status), two lenses: facts"
          " 2 / 0 / 13, conclusions 2 / 2 / 13. Both lenses found the same two BLOCKERs: the CHANGELOG had been built on"
          " an older `main` and would have reverted juniper-ml#2522's entry, and five helper scripts a fix-up agent wrote"
          " into this worktree matched this PR's script glob. The CHANGELOG was rebuilt three ways on the PR's base, and"
          " the five were renamed out of the glob.\n"
          "- V6, V5's corrections and their blast radius: 0 / 1 / 7, each applied as given (one CHANGELOG line"
          " re-wrapped); no seventh round ran.\n"
          "\n"
          "Every finding was applied, or is answered in the record, by `util/ad-hoc/2026-11-08_flood4_record_round1_fixes.py`,"
          " `…_gpath_secret_pass.py` and `…_record_round2_fixes.py`, except V5's two BLOCKERs, which were actions: the"
          " CHANGELOG's three-way rebuild on the PR's base and the five renames.\n"
          "\n"
          "## Requirements\n"
          "\n"
          "None."),
    (PRB, SESSION_OLD, SESSION_NEW),
    # V4-F3 items 20-22; S3.
    (CMB, "Records the flood-4 disposition after round 1: six signed carriers\n"
          "merged (juniper-data#518/#519, juniper-canopy#797/#802, juniper-ml\n"
          "#2517/#2519), all 68 census drafts they carry closed, the 74-row\n"
          "per-PR table rendered from the archived manifests\n"
          "(reports/2026-11-08_flood4-disposition/), and the owner's rulings of\n"
          "2026-11-08. Ships the arc's 157 provenance scripts and round 1's\n"
          "closing handoff.\n",
          "Records the flood-4 disposition after round 1: six signed carriers\n"
          "merged (juniper-data#518/#519, juniper-canopy#797/#802, juniper-ml\n"
          "#2517/#2519), all 68 census drafts assigned to them closed (67\n"
          "carried), the 74-row per-PR table rendered from the archived\n"
          "manifests (reports/2026-11-08_flood4-disposition/) and each PR's\n"
          "live state, the owner's rulings 1-14 of 2026-11-08 and 2026-11-09,\n"
          "four more defects found while the first fixes were built, and round\n"
          "2's triage outcome. Ships the arc's 160 provenance scripts and two\n"
          "handoffs.\n"),
    (CMB, SESSION_OLD, SESSION_NEW),
]


def main():
    check = "--check" in sys.argv[1:]
    texts = dict()
    for path, _, _ in FIXES:
        if path not in texts:
            with open(path, encoding="utf-8") as fh:
                texts[path] = fh.read()
    done = 0
    for path, old, new in FIXES:
        s = texts[path]
        # Already applied. Test the NEW text, not the old one: an insertion keeps its anchor line, so its old text
        # still occurs once after the edit, and an old-text test would insert it again.
        if new in s:
            continue
        if s.count(old) != 1:
            raise SystemExit("REFUSING (nothing written): %d occurrences in %s of: %r" % (s.count(old), path, old[:100]))
        texts[path] = s.replace(old, new)
        done += 1
    if not check:
        for path, s in texts.items():
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(s)
    print("%s: %d of %d corrections %s" % ("check" if check else "apply", done, len(FIXES), "pending" if check else "applied"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
