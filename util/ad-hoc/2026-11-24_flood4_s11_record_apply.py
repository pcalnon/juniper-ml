#!/usr/bin/env python3
"""
Apply the 2026-11-24 update (rulings 15-48 and the later outcomes of rulings 1-14) to the flood-4 disposition record.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 disposition record, session 11)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- one-off editor for the record update; every edit is exact and must match once
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (the record; main 5a049144);
         util/ad-hoc/2026-11-24_flood4_s11_record_{dialogs,census,prs,rulings_json}.py (the facts it states)

What it does
------------
Reads the record as main holds it (``--in``), applies EDITS in order and writes ``--out``. Four kinds of edit:
``sub`` (an exact substring, which must occur once), ``line`` (replace the one line starting with a prefix),
``after`` (insert text after the one line starting with a prefix) and ``block`` (replace from the one line starting
with a prefix up to, not including, the one line starting with another). Any miss or double match stops it with
exit 1 and writes nothing. Section 5's tables are never touched. ``--check`` reports without writing.

Usage
-----
    git show origin/main:notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md > <in.md>
    python3 util/ad-hoc/2026-11-24_flood4_s11_record_apply.py --in <in.md> --out <out.md>
"""

from __future__ import annotations

import argparse


def t(s: str) -> str:
    """A block literal without its first and last newline."""
    return s[1:-1] if s.startswith("\n") and s.endswith("\n") else s


STATUS = t(r"""
**Status**: In progress — rounds 1 to 3 are closed (every carrier merged; no draft of the arc is open), and every defect fix and check built so far has merged; the 2026-11-12 rulings' follow-ups, owed reads, `JuniperCanopy1`'s upgrade and the worktree cleanup are open (§8)
""")

S0_OLD = "Later rulings (§8, 2026-11-08 and 2026-11-09) make the agent guard's brace cap fail closed, put both Retry-After fixes in round 2, port the gitleaks fix to the seven other repositories, fix four more defects that building the fixes found, confirm the paused-fit fix, and carry juniper-ml#2507 with `propose.py` extended."
S0_ADD = t(r"""
 Rulings 15–48 (§8, 2026-11-09 to 2026-11-24) give each of four more defects a fix of its own (ruling 17, one ruling over the four), take the agent guard through 1.3.0 and 1.4.0, settle the designs the fixes chose, order follow-ups to the gaps their validation found, close round 3 and add a check on the compatibility paragraph. By 2026-11-24 every carrier and every defect fix built had merged and no draft of the three rounds was open; §8 lists what is left.
""")

SEC6_NEW = t(r"""
- **A blind rename rewrote the carriers on disk.** The "owner" → "Overtoad" substitution run on this host from 2026-11-20 to 2026-11-22 (the rename behind juniper-ml#2606) rewrote tracked and untracked files, and much of `tmp/`, in every juniper-ml worktree that existed then: 2,629 tracked files in the D-14 juniper-ml carrier and 2,619 in the guard carrier, and 11 symlinks in each became copies. Git objects were untouched. Session 10 restored the D-14 carrier's 35 files, each proven against the sha256 its builder had recorded on 2026-11-16, and the guard's 16 from the index; the juniper-cascor carrier was untouched. Never land from a working tree that existed then.
- **An Overtoad dialog blocks the session that asks it.** Rulings 15–17 waited 7 h 43 min, ruling 37's last answer 9 h 18 min, rulings 39–42 9 h 57 min, rulings 43–45 12 h 42 min and rulings 46–48 3 h 45 min. Background agents and landings ran on meanwhile (juniper-cascor#776 and juniper-ml#2618 merged during the last), and ruling 37 was overtaken during its wait. Start what must merge before asking.
- **`util/safe_merge.py` has reported no review threads since juniper-ml#2606.** Its probe (`util/safe_merge.py:599`) asks GraphQL for `repository(Overtoad: …)`, which fails, and it returns no threads on any failure, so an unresolved CodeQL thread no longer shows in its output; the ruleset still refuses that merge. Until juniper-ml#2632 (open since 2026-11-24 12:39Z) lands, check review threads by hand before a merge.
- **Usage limits killed 13 agents.** The weekly limits stopped sessions 4, 6 and 7 with five, five and three background agents mid-task. A new session cannot message a dead session's agents, so each was relaunched fresh against its partial work, after its tree was checked: a killed mutation run can leave a mutant in a carrier.
- **A running log's time is not always UTC.** Session 3's log puts the answer to rulings 15–17 at "~03:00Z"; its transcript shows the session waiting on that dialog from 01:32Z to 09:15:39Z. This update takes every ruling's time from its transcript (§7).
""")

SEC7_NEW = t(r"""
- **Later sessions' landing helpers** are on `main`, and each session's handoff describes its own (`prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-11_flood4-seven-landed-validations-pending.md` through `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-24_flood4-session10-d14-pair-landed-guard-1-4-0-landing-record-next.md`). Among them are session 4's `util/ad-hoc/2026-11-09_flood4r2_land_snapshot.py` (a freeze on the current `main`, CHANGELOGs merged three ways), `util/ad-hoc/2026-11-09_flood4r2_land_gitleaks.py` (a secret scan with a planted-token control) and `util/ad-hoc/2026-11-09_flood4r2_land_open_pr.py`, and session 6's `util/ad-hoc/2026-11-12_flood4r2_s6_seqsafety_probe.py` (CI's sequence-safety screens, run before a signed push). juniper-ml#2545 (2026-11-12 01:19Z, `9063ebf3`) and #2606 (2026-11-24 05:06Z, `5a049144`) brought the flood-4 helpers dated 2026-11-07 to 2026-11-16 onto `main`, the five jd-gitleaks scripts included; session 10's and 11's ride this update's PR (§9).
- **This update's checks** (new; §9): `util/ad-hoc/2026-11-24_flood4_s11_record_dialogs.py` lists every AskUserQuestion dialog in juniper-ml's transcripts with its asked and answered times, taking the first entry that carries a timestamp (an answer can also sit in an untimed entry, and `util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py`, which keeps the last, can print "answered None"); its `--text` mode finds a typed ruling such as 38. `…_record_census.py` lists every "ruling N" citation in snapshots of the nine repositories' `main` and two release tags, `…_record_prs.py` reads each pull request's state, merge time and merge commit with read-only GraphQL queries, `…_record_rulings_json.py` assembles the per-ruling ledger from those three, `…_record_apply.py` makes this update's edits, and `…_record_pathcheck.py` checks that every repository path they add exists on `main`.
""")

RULINGS_15_48 = t(r"""

**Rulings 15–48** (2026-11-09 to 2026-11-24; labels as above). Each time is when the answer reached the session that asked, from that session's transcript, in UTC. The numbers are the ones the arc's running logs and handoffs gave, and every merged text that cites one agrees with them (§7). Two answers in the same dialogs set the subagent load and were not numbered ("2-3 Fable agents", 2026-11-13; "Opus, 2 at a time", 2026-11-14); neither is the merge approval each later session's opening message gave. On 2026-11-12 at 00:19Z the Overtoad declined a batch of four questions, to clarify them first; rulings 20, 23, 25 and 29 answer them, asked again with the rest.

15. **A brace sequence with a step passed the guard** (2026-11-09 09:15Z): "Carry in ml-code". The ml-code builder found `cat ~/.{r..t..1}sh/config` allowed on `main`, because `util/claude_agent_guard.py` did not expand a brace sequence that carries a step; the question was whether ml-code, already changing brace handling under ruling 8, carries the fix. It did, as a port of bash 5.3's brace-sequence code rather than the 3-line fix first proposed, which refused only the stepped form: guard 1.3.0, juniper-ml#2554 (merged 2026-11-13 00:34Z, `b6b843b6`). Its first cut, #2552, failed CI's Sequence Safety job and was closed and re-cut as #2554.
16. **The fail-closed cap's false refusals** (2026-11-09 09:15Z): "Ship strict, fix later". Replayed over recent session transcripts, ruling 8's cap would refuse 21 of 44,660 Bash commands, 19 of them for a list inside quoted text that bash never expands. The cap shipped strict in juniper-ml#2554, and guard 1.4.0 (ruling 18) stopped counting quoted and escaped lists: juniper-ml#2625 (merged 2026-11-24 03:16Z, `a4d9e9c8`).
17. **Four more defects** (2026-11-09 09:15Z): "data: 44 unrun tests", "cascor: stop-then-start", "canopy: tests hit :8050" and "canopy: dead error path". One ruling over four fixes: builders and validators had found defects that no ruling covered, and the Overtoad chose all four, each to be fixed in its own validated, signed PR:
    - juniper-data#529 (2026-11-09 15:43Z, `97138bd6`): the 44 tests of `test_security.py` lacked the `unit` mark, so no CI lane ran them;
    - juniper-cascor#756 (2026-11-13 00:40Z, `44b60af2`): cascor's own stop-then-start race, in which a start right after a stop cancelled the stop and the old fit trained on, then wrote Completed; its design is ruling 22's;
    - juniper-canopy#815 (2026-11-12 08:24Z, `ee265fde`): 20 unit-lane tests connected to 127.0.0.1:8050 with no mock; the unit lane now refuses connects to ports 8050–8059 and 8200–8211, and juniper-data's `:8100` was left to ruling 27;
    - juniper-canopy#814 (2026-11-12 02:06Z, `51426d9c`): `lockfile-update.yml`'s own failure message could never print, because `gh api graphql` exited 1 first.
18. **The escape gap** (2026-11-09 14:14Z): "Own PR, right after". `cat ~/.ss{h,b\}c}/config` passed the guard on `main` and in the ml-code carrier: the guard expanded braces after quote removal, so it could not see the escaped `\}`. ml-code landed at its own scope, and one word-structure PR then took the escape gap together with rulings 16, 20 and 36: guard 1.4.0, juniper-ml#2625 (merged 2026-11-24 03:16Z, `a4d9e9c8`). That PR was parked on 2026-11-15, when a safety classifier stopped one of its builders, until ruling 38.
19. **N-2's design** (2026-11-12 23:28Z): "Accept the 409". service-core's stop-then-start fix (ruling 11) refuses a new start with HTTP 409 until the stopped run's thread has ended; a bounded wait and per-run fencing were the alternatives. It landed as built: juniper-ml#2557 (2026-11-13 01:42Z, `f9582a74`).
20. **Guard bypasses F3 and F4** (2026-11-12 23:28Z): "In ruling 18's PR". After an `X/..` hop, an unbalanced `{` inside `$(...)` in a brace list, or an empty `$(:)` spliced into a protected name, reached `~/.ssh/config` past the guard on `main`; neither was an ml-code regression. Guard 1.4.0 closes both: juniper-ml#2625, whose `docs/REFERENCE.md` entry lists them as closed.
21. **The open bypasses' exact spellings** (2026-11-12 23:28Z): "Keep them". ml-code printed F3's and F4's exact spellings, such as `~/X/../.ss$(:)h/config`, in `CHANGELOG.md`, the guard's docstring, a provenance script and its PR body, and juniper-ml is public. juniper-ml#2554 landed as written, and ruling 36 kept the same rule for 1.4.0.
22. **cascor's stop-then-start design** (2026-11-12 23:28Z): "Keep fence-and-queue". cascor's fix (ruling 17) gives each run its own stop signal and queues a new start behind the stopped fit, so no HTTP answer changes, where service-core's refuses with a 409 (ruling 19); a 409 would break canopy's Restart, which never retries. juniper-cascor#756 landed as built, so the two differ on purpose.
23. **service-core follow-ups** (2026-11-12 23:34Z): "WebSocket gaps beside N-4", "Lifecycle races beside N-2" and "Match cascor's resume answers", with the Overtoad's note "we should verify that follow up 3 is the right apprach". Validating N-2, N-4 and cascor's resume fix had found defects beside them, each pre-existing or documented as unfixed; each chosen item is one validated, signed service-core PR:
    - "WebSocket gaps beside N-4": an unserialisable broadcast closes every socket, `/ws/control` crashes after a server close, and a dropped socket's per-IP slot is freed before it has closed. Not built.
    - "Lifecycle races beside N-2": a stop followed at once by a snapshot load, and a leftover replay session's stop resetting a running run. Not built.
    - "Match cascor's resume answers": the design check the note asked for went back to the Overtoad as rulings 30 and 31, and landed as one table of resume frames and answers shared by both repositories: juniper-cascor#776 (2026-11-23 22:12Z, `36dd6f2d`) and juniper-ml#2618 (22:31Z, `eeaa191c`).
24. **The guard's suites on macOS** (2026-11-12 23:34Z): "In the ml-tests carrier". juniper-ml's macOS host-tooling job did not run the agent guard's other suites, so a macOS-only guard regression could reach `main` unseen. juniper-ml#2581 (2026-11-15 05:29Z, `4f53e69a`) added the eight, so the job runs every `tests/test_claude_agent_guard*.py`.
25. **juniper-data's other unrun tests** (2026-11-12 23:34Z): "A follow-up PR now". 137 tests, 75 of them security tests, and 41 benchmarks sat in unmarked classes or modules that no CI lane ran. juniper-data#539 (2026-11-15 00:50Z, `706f14a2`) gave the 137 a lane (125 unit, 12 integration); the benchmarks are ruling 33's.
26. **The lockfile print in five more repositories, and a canopy docs line** (2026-11-12 23:34Z): "Port to all five + doc line". The defect juniper-canopy#814 fixed is also in juniper-data, juniper-cascor, juniper-data-client, juniper-cascor-client and juniper-cascor-worker, and canopy's `docs/ci_cd/CICD_MANUAL.md` describes the `[dependabot skip]` tag wrongly. One small PR per repository and a one-line canopy docs PR; none is built.
27. **canopy's `:8100` unit-lane connects** (2026-11-12 23:46Z): "A follow-up PR". #815's guard deferred juniper-data's port: 124 unit tests in 38 files still connect to `:8100` through the app's own startup and readiness probes. The PR is to mock the data client at app startup for the unit lane and add 8100 to the guard; it is not built.
28. **canopy's load-sensitive relay test** (2026-11-12 23:46Z): "A follow-up PR". `test_relay_cascade_add_does_not_block_the_loop` failed CI on two of this arc's PRs, juniper-canopy#807 and #814, under runner load, and passed on re-run. Not built.
29. **The PR-commit scan's force-push gap** (2026-11-12 23:46Z): "Open one juniper-data issue". juniper-data#530's scan never reaches commits that a force-push removed from a pull request, and ruling 10's ports inherit that limit. Issue juniper-data#536 was opened on 2026-11-13 at 00:10Z; it is open.
30. **How service-core answers a resume frame** (2026-11-13 02:12Z): "Four rules + shared table". Ruling 23's design check: juniper-cascor and juniper-service-core answered malformed `/ws/training` resume frames differently on 131 of 240 driven cases. Chosen over the advised "All four cascor rules", it is that change, service-core taking juniper-cascor#754's four cursor rules (refusing a `last_seq` above the newest message reverses `docs/REFERENCE.md`'s "A future seq is not an error, and it is trusted"), plus one table of frames and expected answers that both repositories test against. It landed as juniper-cascor#776 and juniper-ml#2618 (ruling 23).
31. **A negative `last_seq`** (2026-11-13 02:12Z): "Read as 0". A negative cursor means the client holds nothing, as juniper-cascor has read it since #754, so juniper-cascor was not reopened for it. In juniper-ml#2618.
32. **juniper-cascor#756's side effect** (2026-11-13 02:12Z): "Fix it + document". When a pause passed its state check just before a stop and a start landed, the new run froze at its first checkpoint; the cause, an unlocked check-then-act in `pause_training`, predates #756. juniper-cascor#764 (2026-11-15 12:32Z, `7802aef5`) listed it as known, not fixed, and juniper-cascor#769 (2026-11-16 09:20Z, `a011f21e`) fixed it under rulings 39–41, its CHANGELOG entry replacing #764's.
33. **juniper-data's 41 benchmarks** (2026-11-14 23:51Z): "Daily smoke run". They ran in no workflow. `performance` joins the daily scheduled lane's selector, untimed, so a run catches breakage, not slowdowns, and never gates a pull request: juniper-data#540 (2026-11-15 03:38Z, `22a59e58`).
34. **ml-tests and `main-verify.yml`** (2026-11-14 23:51Z): "Add all fifteen". The ml-tests carrier added 15 suites to `ci.yml`, and `main-verify.yml`'s own comment asks for each to be mirrored in its Regression Battery, where the carrier had put six. Chosen over the advised "Keep the six": juniper-ml#2581 mirrors all fifteen.
35. **The blocking-wiring pins in juniper-data** (2026-11-14 23:51Z): "Yes, with ruling 10's ports". The validator of ruling 10's pilot, juniper-data-client#260, had found its blocking wiring unpinned (twelve mutants survived), and juniper-data's own Gitleaks test predated that fix. All twelve mutants survived juniper-data's merged test too, and juniper-data#542 (2026-11-15 06:17Z, `fefd1895`) added the pins.
36. **Seven more ways past the guard** (2026-11-15 11:38Z): "Close here, public". An earlier builder had found seven more spellings on `main` (N1–N7) that reach a guarded file, one of them making bash run a command the guard never judges. Ruling 18's PR closes each one its design covers, pins it in the committed tests, and names any left open in `docs/REFERENCE.md` with its exact spelling, as ruling 21 did; juniper-ml#2625 closes all seven.
37. **The scheduled-tests lanes that pytest 9.2.0 broke** (2026-11-15): "Small worker PR" (11:38Z), then "Register slow, x3" (11:55Z), then "Worker via conftest.py" (21:28Z). juniper-cascor-worker's daily lane had failed since pytest 9.2.0 (2026-10-28) with "Unknown marker(s) in '-m' expression: slow". The first answer was given on a question whose onset and scope were wrong; asked again with juniper-data-client and juniper-cascor-client failing the same way, the Overtoad chose to register the marker in all three over the advised "Selector -> integration, x3", and then, for the worker alone, whose lockfile workflow would have regenerated its locks onto the PR, to register it in `tests/conftest.py`. Overtaken: while that last dialog waited, PRs from outside this arc took the selector route in all three repositories, juniper-cascor-worker#231 (12:23Z, `3975d9ac`), juniper-data-client#263 (12:23Z, `225dd6bb`) and juniper-cascor-client#198 (12:23Z, `e8aa7361`), and each lane's first scheduled run on `main` passed on 2026-11-16. The arc's worker carrier was not landed.
38. **The parked guard PR** (2026-11-15 21:56Z, typed): "let's verify that agent guard fix is reworded as necessary to complete this task. blocking a hardening task that closes loopholes is counter-productive. assumptions behind this request, the loopholes involved, and the efficacy of these tasks should all be validated during this process." A safety classifier had stopped the third builder of ruling 18's PR while it read an earlier builder's bypass notes (the first two had died at the usage limits, §6), and the orchestrator had parked the PR rather than reword its way past the stop. The brief was then reworded defensively (the guard is fed JSON payloads; bash only prints expansions, in a scratch home), the assumptions, each loophole on `main` and the fix's efficacy were validated, and the three agents that ran under it met no stop. The result is juniper-ml#2625.
39. **A pause that loses its race** (2026-11-16 08:03Z): "Keep the 409". In juniper-cascor's pause fix, a pause whose state change loses a race with a stop is refused with a 409, where `main` answered 200 "paused" although the run had stopped; consumers already surface the 409, and nothing retries. In juniper-cascor#769.
40. **A pause after a timed-out live swap** (2026-11-16 08:03Z): "Refuse it: 409". The code lens found that, after a live swap whose 10 s join timed out, a pause answered 200 but never paused the swapped run. The fix refuses a pause while the lifecycle-owning run's stop is raised. In juniper-cascor#769.
41. **The pause fix's scope** (2026-11-16 08:03Z): "Wider fix + resume 409". Start, the live swap and every settle a run owns also reopen the pause gate under its new lock, which closing #764's second route needs, and a resume that loses the same race answers 409 like a pause. In juniper-cascor#769.
42. **Round 3** (2026-11-16 08:03Z): "Close both, superseded". juniper-ml#2404 and #2406, launcher docs that `main` contradicts, were closed at 08:06Z, each with a comment naming, by file and line, what on `main` supersedes it.
43. **The D-14 drift gate** (2026-11-16 22:11Z): "Keep FAIL". `tests/test_ws_resume_answer_table_drift.py` compares juniper-ml's and juniper-cascor's copies of the shared table; a juniper-cascor checkout without its copy fails the weekly docs-full-check rather than skipping, since a skip would pass forever on a deleted copy. In juniper-ml#2618.
44. **Where the D-14 helpers land** (2026-11-16 22:11Z): "In the juniper-ml PR". The builder's provenance scripts ride the juniper-ml PR beside the code they prove, as earlier carriers' did: juniper-ml#2618 carries 19 of them, dated 2026-11-15 and 2026-11-16 (the question said ten).
45. **The D-14 test dependencies** (2026-11-16 22:11Z): "Keep, no cap". juniper-service-core's `[test]` extra gains uvicorn and websockets, with minimums and no upper bound, because the shared-table test drives every row over a real loopback WebSocket; neither is a runtime dependency. In juniper-ml#2618.
46. **What guard 1.4.0 leaves open** (2026-11-24 01:47Z): "Land 1.4.0, name gaps". 1.4.0 still passes printing substitutions, in which part of a command, option or path is printed at run time (`d$(printf %s o)as id`), and the code review's generator still found 218 unsafe words. The claims review's 31 text fixes were applied, so `docs/REFERENCE.md` and the guard's docstring name every spelling still open and no claim overstates, and 1.4.0 landed: juniper-ml#2625. Closing the class is left to the Overtoad.
47. **1.4.0's time cap** (2026-11-24 01:47Z): "Keep 3 s". 1.4.0 refuses a Bash command whose analysis runs past 3 s (`ANALYSIS_TIME_BUDGET`). None of the 44,678 real commands in its census came near it, the slowest taking 0.110 s; only synthetic 24–30 KB brace commands reach it. In juniper-ml#2625.
48. **A check on the compatibility paragraph** (2026-11-24 01:47Z): "Add a paragraph check". R55 of `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md`: tests keep `docs/REFERENCE.md`'s compatibility-table row for the current series in step with `pyproject.toml` between a floor PR and its release, and nothing checked that the paragraph above the table says so. juniper-ml#2631 (merged 2026-11-24 13:06Z, `9a9ef3fb`) adds that sentence and one assertion in `tests/test_pyproject_extras.py`.
""")

STILL_OPEN = t(r"""
**Still open** (each checked on 2026-11-24):

- **The 2026-11-12 rulings' follow-ups**, none built; no pull request for any of them exists in its repository:
  - the two service-core PRs of ruling 23, "WebSocket gaps beside N-4" and "Lifecycle races beside N-2";
  - ruling 26's five lockfile-print ports, and canopy's `[dependabot skip]` paragraph (`docs/ci_cd/CICD_MANUAL.md:795` on juniper-canopy's `main`, unchanged since #814);
  - canopy's `:8100` unit-lane connects (ruling 27) and its load-sensitive relay test (ruling 28).
- **The agent guard.** Closing the printing-substitution class, and the other spellings `docs/REFERENCE.md` names as open in 1.4.0, waits for the Overtoad (ruling 46). 1.4.0 reaches turing only when the Overtoad re-runs `util/install_claude_agent_guard.bash` there, on Claude Code v2.1.295 or later; it is not installed on the Linux host. `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md:1297` still gives the guard entry as 1.3.0, the version the brace cap arrived in.
- **Owed reads.** The first Dependabot pull request after the scan changes in juniper-data (#544, after #542's pins), juniper-data-client (#265), juniper-cascor-client (#200) and juniper-ml (#2598), all of 2026-11-16, concluded its Security Scans job `success`, but its log (the engine version, and the commits the pull-request scan reports) has not been read. The other four repositories' reads were done on 2026-11-16.
- **`JuniperCanopy1`** (ruling 6): not upgraded. At 12:49Z it held juniper-observability 0.4.0 and juniper-service-core 0.5.0, below juniper-canopy's floors on `main` (`>=0.4.2`, `>=0.7.2`); no process ran from it and nothing listened on any port from 8000 to 8099, so the E2E legs that failed the check on 2026-11-08 were down then. The upgrade waits for the Overtoad.
- **Ruling 7's cleanup**, not started. 151 worktrees under `worktrees/` carry `flood4` in their names, besides the fix and port worktrees named for their branches and the carriers' and agents' under `.claude/worktrees/`. Each one's `tmp/` is archived first: the evidence the archived manifests cite, each fix's validator findings, and sessions 1–11's logs and briefs, parts of which the 2026-11-20..22 rename rewrote (§6). `tmp/val-a-m1/`, in juniper-ml's primary checkout, falls under the retention rule.
- **A follow-up the docs carrier left.** `main`'s `CHANGELOG.md` entry for #2517 says #2424's Test Suite Reference line lacks "its link to a section only the docs carrier adds". That holds for #2432, but not for #2424, whose own section was not carried. #2426's equivalent section is `#the-firewall-gate-reads-getblockall`, and the line still has no link to it (round 4's F6; the juniper-ml docs manifest's `open_questions`).

""")

SEC9_NEW = t(r"""

This update's PR (2026-11-24):

- `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`: rulings 15–48, with ruling 17 as one ruling over its four fixes as R54 of `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md` asks, and the later outcomes of rulings 1–14 (§8); §4's changed rows; short additions to the header, §0, §1, §6 and §7. §5's tables are as rendered on 2026-11-08;
- `CHANGELOG.md`, for its entry;
- `util/ad-hoc/2026-11-24_flood4_s11_record_dialogs.py`, `…_record_census.py`, `…_record_prs.py`, `…_record_rulings_json.py`, `…_record_apply.py` and `…_record_pathcheck.py` (new; §7);
- SESSION_HELPERS_PLACEHOLDER

The pull requests of rounds 2 and 3, of the defect fixes and of the rulings' follow-ups are named in §8 with their merge commits; each lists its own files.
""")

EDITS: list[tuple] = [
    ("line", "**Status**: ", STATUS),
    ("line", "**Updated**: 2026-11-09", "**Updated**: 2026-11-24"),
    ("sub", S0_OLD, S0_OLD + S0_ADD),
    ("sub", "juniper-ml#2360 (armed and `DIRTY` on purpose; it merges last)", "juniper-ml#2360 (armed and `DIRTY` on purpose at the census; it merged on 2026-11-12 at 02:18Z, `187e3258`)"),
    ("sub", "#2514 was then carried outside this arc, by juniper-ml#2524 (§8, ruling 9).", "#2514 was then carried outside this arc, by juniper-ml#2524 (§8, ruling 9). By 2026-11-15 all 48 were closed: 41 carried, whole or in part (#2514 by juniper-ml#2524), and seven uncarried, as superseded or duplicates (§8)."),
    ("sub", "each is to be considered individually.", "each is to be considered individually. Both were closed as superseded on 2026-11-16 (§8, ruling 42)."),
    # section 4
    (
        "sub",
        "| **ruled** (Overtoad, 2026-11-08): the default becomes `max` (line 258 restored), and an explicit `auto` sends no `--effort` flag at all. The fix rides in round 2's launcher code carrier (§8). The tests carrier pinned neither |",
        "| **fixed** — juniper-ml#2554 (merged 2026-11-13 00:34Z, `b6b843b6`), round 2's code carrier, as the Overtoad ruled on 2026-11-08 (§8, ruling 3): the default is `max` again, and an explicit `auto` sends no `--effort` flag at all. Round 1's tests carrier pinned neither |",
    ),
    (
        "sub",
        "| **ruled: fix now** (Overtoad, 2026-11-08; §8), and confirmed once the Overtoad had #2460's provenance (ruling 12). A fix was built.",
        "| **fixed** — juniper-ml#2531 (merged 2026-11-09 11:22Z, `7b3b91b7`), not yet in a release (juniper-service-core's latest is v0.7.2, of 2026-11-08); juniper-cascor's own copy by juniper-cascor#753 (§8, ruling 11). Ruled \"Fix now\" (Overtoad, 2026-11-08; §8), and confirmed once the Overtoad had #2460's provenance (ruling 12). A fix was built.",
    ),
    ("sub", "Its PR opens once both are corrected, after this record merges. Until it lands, #2519 describes the wedge as current behaviour |", "Both were corrected, and checked once more, before #2531 opened |"),
    (
        "sub",
        "| **ruled: fix now** (Overtoad, 2026-11-08; §8). A fix was built, and its two validators returned SHIP-WITH-FIXES;",
        "| **fixed** — juniper-ml#2534 (merged 2026-11-09 15:13Z, `f85fbc8b`), not yet in a release; juniper-cascor's copy by juniper-cascor#754 (§8, ruling 11). Ruled \"Fix now\" (Overtoad, 2026-11-08; §8). A fix was built, and its two validators returned SHIP-WITH-FIXES;",
    ),
    ("sub", "Its PR opens once both are corrected, after this record merges. The race was reproduced", "Both were corrected, and checked once more, before #2534 opened. The race was reproduced"),
    (
        "sub",
        "| **ruled: fix now** (Overtoad, 2026-11-08; §8), for juniper-data. A fix was built.",
        "| **fixed** — juniper-data#530 (merged 2026-11-09 16:03Z, `05c1f446`), and ported to the seven other repositories that run the action under ruling 10, the last on 2026-11-15 (§8). Ruled \"Fix now\" (Overtoad, 2026-11-08; §8), for juniper-data. A fix was built.",
    ),
    ("sub", "its PR opens after this record merges.", "#530 opened after this record merged."),
    # section 6
    ("sub", "Whether this record's PR draws any is open (§8).", "None followed this record's PR or any later one: no Cursor pull request has been opened in any of the nine repositories since 2026-11-08 00:22Z (checked on 2026-11-24)."),
    ("after", "- **The isolated session's classifier refused a `grep`", SEC6_NEW),
    # section 7
    ("after", "  - 29 probes gained the `util/ad-hoc/README.md` provenance fields", SEC7_NEW),
    # section 8, rulings 1-14
    ("sub", "So `EFFORT_DEFAULT` becomes `max`, and `auto` sends no `--effort` flag. The change rides in round 2's launcher code carrier.", "So `EFFORT_DEFAULT` becomes `max`, and `auto` sends no `--effort` flag. The change landed in round 2's code carrier, juniper-ml#2554 (2026-11-13 00:34Z, `b6b843b6`)."),
    ("line", "   - the paused-fit wedge;", "   - the paused-fit wedge: juniper-ml#2531 (2026-11-09 11:22Z, `7b3b91b7`);"),
    ("line", "   - the `resume_ok` broadcast losses, both the no-client case and the replay race;", "   - the `resume_ok` broadcast losses, both the no-client case and the replay race: juniper-ml#2534 (15:13Z, `f85fbc8b`);"),
    ("line", "   - gitleaks-action's unpaginated commit list.", "   - gitleaks-action's unpaginated commit list: juniper-data#530 (16:03Z, `05c1f446`)."),
    ("sub", "both below canopy's floors, stay until the Overtoad decides.", "both below canopy's floors, stay until the Overtoad decides. On 2026-11-24 at 12:49Z it still held both, while no process ran from it and nothing listened on any port from 8000 to 8099 (Still open, below)."),
    ("sub", "Each goes only after its PR is confirmed merged and its `tmp/` is checked under the retention rule.", "Each goes only after its PR is confirmed merged and its `tmp/` is checked under the retention rule. It had not started by 2026-11-24 (Still open, below)."),
    ("sub", "both ride in round 2's juniper-ml carriers.", "both ride in round 2's juniper-ml carriers. Done: juniper-ml#2554 (2026-11-13 00:34Z, `b6b843b6`) made the cap fail closed and inverted that test, and juniper-ml#2584 (2026-11-15 05:48Z, `725c6343`) carried #2470 rewritten."),
    ("sub", "Both fixes go into round 2, juniper-data's in a code carrier of its own.", "Both fixes go into round 2, juniper-data's in a code carrier of its own: juniper-data#537 (2026-11-13 02:54Z, `3cf8867c`) rounds `Retry-After` up in its `RateLimiter` and failed-auth throttle and never sends 0."),
    (
        "sub",
        "and their own Gitleaks tests.",
        "and their own Gitleaks tests. Done: juniper-data's new scan ran green live on Dependabot's juniper-data#532 (2026-11-11 23:16Z), and the seven ports merged: juniper-data-client#260, the pilot (2026-11-13 00:37Z, `b45aafbb`); juniper-cascor-client#196 (2026-11-15 03:41Z, `29d2f814`); juniper-cascor-worker#230 (04:42Z, `a7a2cd08`); juniper-cascor#761 (04:45Z, `f5ffefb7`); juniper-deploy#277 (05:30Z, `6c9e57f8`); juniper-canopy#822 (06:02Z, `4f59aeb0`); and juniper-ml#2587 (07:17Z, `57c76b63`).",
    ),
    (
        "line",
        "    The next update of this record gives each one's evidence and PR.",
        "    Done, each in its own PR: juniper-cascor#753 (2026-11-09 15:43Z, `96cf891b`), the paused-fit wedge; juniper-ml#2557 (2026-11-13 01:42Z, `f9582a74`), the stop-then-start race, refused with a 409 (ruling 19); juniper-cascor#754 (2026-11-12 08:38Z, `b9167bdc`), the resume losses; and juniper-ml#2547 (2026-11-12 08:59Z, `15b5d9bb`), which closes such a socket with 1011.",
    ),
    ("sub", "the script is to be extended to rewrite them, in a small carrier of its own.", "the script is to be extended to rewrite them, in a small carrier of its own. Done: juniper-ml#2579 (2026-11-15 04:25Z, `11cac1af`) makes `propose.py` render the four sites, juniper-ml#2581 (05:29Z, `4f53e69a`) carries the tests, and #2507 was closed at 05:30Z."),
    # section 8, rulings 15-48 and Still open
    ("after", "14. **juniper-ml#2507** (2026-11-09)", RULINGS_15_48),
    ("block", "**Still open:**", "## §9 Documents created or modified", STILL_OPEN),
    # section 9
    ("after", "Outside any repository: the Overtoad's", SEC9_NEW),
]


def one_line(lines: list[str], prefix: str) -> int:
    hits = [i for i, line in enumerate(lines) if line.startswith(prefix)]
    if len(hits) != 1:
        raise ValueError(f"line prefix {prefix[:70]!r}: {len(hits)} matches")
    return hits[0]


def apply(text: str) -> str:
    for n, edit in enumerate(EDITS, 1):
        kind = edit[0]
        if kind == "sub":
            _, old, new = edit
            count = text.count(old)
            if count != 1:
                raise ValueError(f"edit {n} (sub {old[:70]!r}): {count} matches")
            text = text.replace(old, new)
            continue
        lines = text.split("\n")
        if kind == "line":
            _, prefix, new = edit
            lines[one_line(lines, prefix)] = new
        elif kind == "after":
            _, prefix, new = edit
            i = one_line(lines, prefix)
            lines[i + 1 : i + 1] = new.split("\n")
        elif kind == "block":
            _, start, end, new = edit
            i, j = one_line(lines, start), one_line(lines, end)
            if j <= i:
                raise ValueError(f"edit {n}: block end before start")
            lines[i:j] = new.split("\n")
        else:
            raise ValueError(f"edit {n}: unknown kind {kind}")
        text = "\n".join(lines)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in", dest="src", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--check", action="store_true", help="apply in memory and report; write nothing")
    args = ap.parse_args()
    with open(args.src, encoding="utf-8") as fh:
        before = fh.read()
    try:
        after = apply(before)
    except ValueError as exc:
        print(f"REFUSED: {exc}")
        return 1
    sec5 = lambda s: s[s.index("## §5 Per-PR disposition") : s.index("## §6 Process traps")]  # noqa: E731
    if sec5(before) != sec5(after):
        print("REFUSED: section 5 changed")
        return 1
    print(f"{len(EDITS)} edits applied; {before.count(chr(10))} -> {after.count(chr(10))} lines; section 5 unchanged")
    if not args.check:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(after)
        print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
