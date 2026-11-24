"""
Write the claims lens's findings.json for the ml-tests round-2 carrier (claims lens, session 8), from the evidence
files in the scratch directory (the values below were read from them; this script only assembles the record).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_flood4r2_val_ml-tests-r2-claims_write_fixes.py
"""

import argparse
import json
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development/python/Juniper"
WT = str(JUNIPER / "worktrees/juniper-ml--val--flood4r2-ml-tests-r2-claims--20261114-1916--a949d504")
CARRIER = str(JUNIPER / "juniper-ml/.claude/worktrees/agent-a89a668e6d43bcee2")

FINDINGS = [
    {
        "id": "F1",
        "severity": "MAJOR",
        "where": "manifest.json carried[pr 2484].dropped[2]; templates/pr_body.txt:40 (Not carried, bullet 2); templates/commit_body.txt:25; templates/changelog_entry.txt:43-44 = CHANGELOG.md:103-104 of the L2 landing; dispositions.json round_1_open_questions[n=6]",
        "claim": "Every text attributes to #2484 'its docs/REFERENCE.md paragraph on the scratch copying the checkout's shallow graft'. #2484 has no such paragraph: it is stacked on #2480's branch (base cursor/critical-bug-resolution-68c6), its own commit 94becb77 changes only ci.yml (+5), docs/REFERENCE.md (+1, the run-list line) and its test file, and its body says 'The diff is the new suite plus its ci.yml and docs/REFERENCE.md invocation lines.' The paragraph is #2480's commit 406e7d80. So the CHANGELOG entry on main and #2484's close comment state a false attribution. Rated MAJOR, not BLOCKER: by the scale's letter a false statement in CHANGELOG.md on main is a BLOCKER, but only authorship is wrong (the paragraph is not carried either way, which the texts say truly). The ml-docs carrier's manifest uses the same attribution ('#2484's paragraph', its draft-2484 row): align the two before either close comment is posted (a lead; ml-docs' texts not read in full).",
        "evidence": "git diff 406e7d80 94becb77 --stat -> .github/workflows/ci.yml 5, docs/REFERENCE.md 1, tests/test_predict_merge_shallow_worktree.py 199; git diff 406e7d80 94becb77 -- docs/REFERENCE.md -> one line '+python3 -m unittest -v tests/test_predict_merge_shallow_worktree.py'; git diff 21a9dabc 406e7d80 -- docs/REFERENCE.md -> '+   When the checkout is shallow, the scratch copies that checkout's `.git/shallow` graft. ...'; gh pr view 2484 baseRefName cursor/critical-bug-resolution-68c6 (drafts/2484/gh.json)",
        "fix": "text_fixes.json T1-T5 (each old occurs once; previews in texts_fixed/)",
    },
    {
        "id": "F2",
        "severity": "MINOR",
        "where": "manifest.json carried[pr 2480].dropped[2]; templates/pr_body.txt:39",
        "claim": "#2480's row drops 'its CHANGELOG, docs/REFERENCE.md and fleet-supervisor.md hunks (they describe the superseded code)', and the body says its '.claude/agents/fleet-supervisor.md' hunk goes with the superseded code. #2480's own commit 406e7d80 has no fleet-supervisor.md hunk: the one its diff shows is the Overtoad commit 21a9dabc beneath it (#2474, squashed to main as 827199b6), which describes main's code. The row also omits that Overtoad commit, which the #2481 and #2496 rows list.",
        "evidence": "git diff 21a9dabc 406e7d80 --stat -> CHANGELOG.md, docs/REFERENCE.md, tests/test_predict_merge.py, util/fleet_triage/predict_merge.py (no .claude/); git diff 87181fed 21a9dabc --stat -> .claude/agents/fleet-supervisor.md 13; gh pr view 2474: commits 21a9dabc, 47b19f9d, ..., merge 827199b6",
        "fix": "text_fixes.json T6, T7",
    },
    {
        "id": "F3",
        "severity": "MINOR",
        "where": "templates/pr_body.txt:45 (rendered pr_body.txt:45)",
        "claim": "'Round 2 was built three times (two builders were stopped before finishing)': one was. Session 6's builder (agent-abd21f5554a19c89f) was stopped; session 7's finished ('AGENT H2 DONE at about 03:18Z'; its report: 'ml-tests round 2 is finished'), and session 8's finished. Session 8 changed the template's 'built twice (its first builder was stopped before finishing)'.",
        "evidence": "the orchestrator's tmp/flood4/session7/STATE_S7.txt:173; CD/REPORT.txt:181; CD/pre-s8/templates/pr_body.txt vs CD/templates/pr_body.txt (grep 'Round 2 was built')",
        "fix": "text_fixes.json T8",
    },
    {
        "id": "F4",
        "severity": "MINOR",
        "where": "templates/pr_body.txt:55",
        "claim": "'none in the four helpers the last session added': session 8 added five (battery, land, manifest, reverts, s8_inputs), and its own prescreen log says 5 files.",
        "evidence": "CD/REPORT.txt section 5 (five '(new)' helpers); CD/s8_codeql_prescreen.log '0 predicted alert(s) in 5 file(s)'",
        "fix": "text_fixes.json T9",
    },
    {
        "id": "F5",
        "severity": "MINOR",
        "where": "manifest.json carried[pr 2507].reason (feeds #2507's close comment)",
        "claim": "The reason calls #2558 'the 0.11.5 release proposal, open on 2026-11-13' and cites its head d4dcefbc. #2558 merged at 2026-11-13T10:08:14Z from head ddf88ea9 (two commits after d4dcefbc) as 48b66130, and 0.11.5 is released. On 2026-11-15 a close comment should say what is true now; the eight tests do pass on today's main (L2: tests/test_pyproject_extras.py 20 OK).",
        "evidence": "gh pr view 2558 -> state MERGED, mergedAt 2026-11-13T10:08:14Z, head ddf88ea9, commits 8764f5cf d4dcefbc 618839c9 ddf88ea9; readers_L2/summary.json tests/test_pyproject_extras.py exit 0, 20 tests",
        "fix": "text_fixes.json T10",
    },
    {
        "id": "F6",
        "severity": "MINOR",
        "where": "templates/pr_body.txt:20 (Carries, #2480); templates/commit_body.txt:24",
        "claim": "'its code is on main since juniper-ml#2474' / 'the code of #2480 (main has it since juniper-ml#2474)': #2480's code (_inherit_shallow_boundary, 406e7d80) is not on main; main does the same with #2474's own code (predict_merge.py:369-373, shutil.copyfile of the common dir's shallow file). The Not-carried bullet already says it right ('superseded, main copies the common directory's shallow file since juniper-ml#2474').",
        "evidence": "command grep -n shallow util/fleet_triage/predict_merge.py on L1 -> :369-373; no _inherit_shallow_boundary on main",
        "fix": "text_fixes.json T11, T12",
    },
    {
        "id": "F7",
        "severity": "MINOR",
        "where": "manifest.json carried[pr 2472].fixes[1]",
        "claim": "'black (the pinned hook joins the fake-claude and fake-wake scripts' implicit string concatenations onto one line ...)': the draft's fake-claude script was already one line; black re-quoted its second string (draft->landed hunk at :64). Only the fake-wake script was joined (:151). The fix is real (the pinned black reformats the draft's file), its description half wrong.",
        "evidence": "drafts/2472/tests__test_launcher_prompt_and_version_edges.py.diff hunks @@ -64 and @@ -151; precommit_drafts_L4.log 'reformatted tests/test_launcher_prompt_and_version_edges.py'",
        "fix": "text_fixes.json T13",
    },
    {
        "id": "F8",
        "severity": "MINOR",
        "where": "templates/pr_body.txt:10; templates/changelog_entry.txt:34-35 (CHANGELOG.md on main)",
        "claim": "UNCERTAIN. '(the record's next update adds it to its section 8)' / '(the next update of notes/...DISPOSITION.md adds it to its section 8)' says what a later PR will do, against 'no text promises a follow-up'. Brief H step 6 mandated the wording and the orchestrator kept the arc's same phrase on juniper-data#539 (STATE_S8, 00:41Z), so it is reported for a decision only.",
        "evidence": "the orchestrator's tmp/flood4/session6/briefs/H_ml_tests_round2.txt step 6; the orchestrator's tmp/flood4/session8/BRIEF_S8_ADDENDUM.txt section 5; STATE_S8.txt 00:41Z entry",
        "fix": "only if the precedent is reversed: text_fixes.json T15, T16 (optional)",
    },
    {
        "id": "F9",
        "severity": "MINOR",
        "where": "tests/test_pyproject_extras.py:89 (and :641)",
        "claim": "The comment '# docs/REFERENCE.md Package Overview cell: | **Version** | `0.11.4` |' shows a cell value main no longer has (docs/REFERENCE.md:108 is `0.11.5`); :641 'The 0.11.4 sentence records both >=0.8.1 (current) and >=0.8.0' describes a sentence main now words for 0.11.5. Known (the carrier's open question e, 'left as carried'); not a claim that 0.11.4 is the latest.",
        "evidence": "sed -n 89p and 641p of the landed file; command grep -n '0.11.[45]' docs/REFERENCE.md -> :108 `0.11.5`, :184 '0.11.5 declares'",
        "fix": "leave (a byte change voids the kept mutants on this file and needs a manifest regeneration), or at the freeze: COPY/tests/test_pyproject_extras.py ':89 `0.11.4` -> `X.Y.Z`' and re-run its suite and mutants 32-36",
    },
    {
        "id": "F10",
        "severity": "MINOR",
        "where": "manifest.json carried[pr 2489] (fixes: [], outcome 'carried')",
        "claim": "The landed Test Suite Reference entry for tests/test_claude_agent_guard_push_signed.py adds `none` to the denied values, which ON_VALUES pins and the draft's text omitted. The carrier's text is the truer one; the row says nothing of the change. Polish.",
        "evidence": "ref_lines.txt '#2489 ... draft->landed word changes: - `00` + `00`, + `0.0` - `0.0` + `none`'; tests/test_claude_agent_guard_push_signed.py:31 ON_VALUES includes 'none'",
        "fix": "optional: append to carried[2489].fixes 'its Test Suite Reference text lists `none` among the denied values, which the test pins and the draft's text left out' and set outcome carried-with-fix",
    },
    {
        "id": "F11",
        "severity": "MINOR",
        "where": "dispositions.json round_1_open_questions[n=3].why",
        "claim": "'(0.6.70 on f9582a74; 0.6.71 after ml-propose)' is stale: the landing takes 0.6.71 on a949d504 alone (L1) and 0.6.72 after ml-propose (L2). Internal deliverable only.",
        "evidence": "stamps_check.json: L1 version lines [5, 10021] 0.6.71; L2 [5, 10024] 0.6.72",
        "fix": "text_fixes.json T14",
    },
    {
        "id": "F12",
        "severity": "MINOR",
        "where": "CD/REPORT.txt session-8 section, :47 vs :151",
        "claim": "The report names the pull request tree twice: section 2 's8_pr3 ... a949d504', section 6 'the s8_pr2 worktree above' (s8_pr2 is on 16f2512b). Internal; the real landing is a fresh run of the one command on the main of the sitting in any case.",
        "evidence": "CD/REPORT.txt:47 and :151",
        "fix": "use the landing of the sitting; no shipped text changes",
    },
    {
        "id": "F13",
        "severity": "MINOR",
        "where": "manifest.json carried[*].taken (and carried_input.json): 15 items start 'session 8: '; 6 say 'the session-7 spec typed'",
        "claim": "The close comments are generated from these items, so 'session 8:' and 'the place the session-7 spec typed' (process jargon no PR reader can resolve) would be posted on 15 drafts. The statements themselves are true (every placement re-derived on L2 and L5).",
        "evidence": "command grep -oF '\"session 8: ' manifest.json -> 15, carried_input.json -> 15; ', at the place the session-7 spec typed:' -> 4 each; the two parentheticals -> 1 each",
        "fix": "mechanical, in manifest.json and carried_input.json: delete the leading 'session 8: ' of the 15 taken items; replace ', at the place the session-7 spec typed:' with ':' (4 items: #2478 #2495 #2503 #2509); delete the two parentheticals (text_fixes.json T17, T18: #2512 and #2515)",
    },
]

CARRIED = [
    {"draft": 2469, "verdict": "right", "what_is_wrong": "", "re_derived": "test file = head blob + 4 annotation lines; pinned mypy on the draft: 10 attr-defined errors; battery after test_check_conda_env_torch.py"},
    {"draft": 2472, "verdict": "right-with-fix", "what_is_wrong": "fixes[1] says black joined the fake-claude script; it re-quoted it (F7)", "re_derived": "pinned black reformats the draft file; mypy :250 var-annotated; Overtoad commit 07271912 is #2468's (merged fc533642)"},
    {"draft": 2475, "verdict": "right", "what_is_wrong": "", "re_derived": "byte-identical; its suite passes under pytest from juniper-ci-tools/ on L2 (4 tests)"},
    {"draft": 2478, "verdict": "right", "what_is_wrong": "", "re_derived": "pinned black reformats the draft file (two fake-claude joins); Overtoad commits 07271912, ca8224a9 are #2468's"},
    {"draft": 2480, "verdict": "right-with-fix", "what_is_wrong": "dropped[2] attributes #2474's fleet-supervisor.md hunk to #2480 and omits the Overtoad commit 21a9dabc beneath it (F2); 'its code is on main' in the body (F6)", "re_derived": "own commit 406e7d80 = CHANGELOG, REFERENCE paragraph, test (docstring, one assertion, missing-parent test), predict_merge.py; the one assertion is at tests/test_predict_merge.py:478 on L1"},
    {"draft": 2481, "verdict": "right", "what_is_wrong": "", "re_derived": "tests/test_env_repr_safety.py refuses the draft's os.environ.copy() at :36; Overtoad commit 21a9dabc is #2474's; tree line re-worded"},
    {"draft": 2484, "verdict": "wrong-in-part", "what_is_wrong": "dropped[2] gives #2484 a docs/REFERENCE.md paragraph that is #2480's (F1)", "re_derived": "the draft's test 2 fails on main and test 1 passes (drafts_shallow_worktree.log); own commit = ci.yml, REFERENCE run-list line, test file"},
    {"draft": 2489, "verdict": "right", "what_is_wrong": "the REFERENCE text gained `none`, unmentioned (F10, polish)", "re_derived": "byte-identical test; _git_push_requests_signature at util/claude_agent_guard.py:1793"},
    {"draft": 2491, "verdict": "right", "what_is_wrong": "", "re_derived": "pinned mypy on the draft: 15 attr-defined errors"},
    {"draft": 2492, "verdict": "right", "what_is_wrong": "", "re_derived": "byte-identical test; the REFERENCE entry made top-level, its values (a key with no value, none, nope) all in the test"},
    {"draft": 2495, "verdict": "right", "what_is_wrong": "", "re_derived": "pinned black reformats the draft file (quote normalization)"},
    {"draft": 2496, "verdict": "right", "what_is_wrong": "", "re_derived": "pinned black reformats the draft file; the CodeQL prescreen predicts import-and-import-from on the draft (:24) and nothing on the landed file; the draft added no Test Suite Reference entry"},
    {"draft": 2499, "verdict": "right", "what_is_wrong": "", "re_derived": "pinned flake8: C420 at :64 and :141 on the draft"},
    {"draft": 2503, "verdict": "right", "what_is_wrong": "", "re_derived": "pinned black reformats the draft file"},
    {"draft": 2507, "verdict": "right-with-fix", "what_is_wrong": "reason calls #2558 open and cites a non-final head (F5)", "re_derived": "ReferenceCompatibilityMatrixTest has 8 tests; F6 fixtures 9.8.x/9.9.x and >=9.9.0/>=9.9.1 at :616-636; #2482's body:272 says no test guards the sentence or matrix; tests/test_pyproject_extras.py 20 OK on L2; <ML-PROPOSE-PR> filled everywhere by --ml-propose-pr (99999 stand-in)"},
    {"draft": 2509, "verdict": "right", "what_is_wrong": "", "re_derived": "pinned black reformats the draft file"},
    {"draft": 2512, "verdict": "right", "what_is_wrong": "", "re_derived": "the ERROR-row sentence matches screen_coverage (predict_merge.py:622-657) and triage_batch's row (gates {} at :596-604); battery after test_predict_merge_guard_edges.py"},
    {"draft": 2515, "verdict": "right", "what_is_wrong": "", "re_derived": "the docstring's 'the main suite names the short -S for commit and rebase alone' holds (tests/test_claude_agent_guard.py:370, :376); battery after gpgsign_off, before test_configure_commit_signing.py"},
]

LANDING = {
    "main_built_on": "L1 and L2 on a949d5045f912ae907acb35cc8104247b1494a48 (juniper-ml#2567). MAIN MOVED during this run: e8c97956 (juniper-ml#2569, merged 2026-11-15T01:35:24Z: CHANGELOG.md +20, a new ### Changed group in [Unreleased] between ### Added and ### Fixed; docs/REFERENCE.md one utility line, its stamp still 0.6.70; no ci.yml, main-verify.yml or AGENTS.md change), so L5 repeats L2 on it",
    "L5_new_main": {
        "tree": str(JUNIPER / "worktrees/juniper-ml--val--flood4r2-ml-tests-r2-claims--20261114-1949--e8c97956-L5"),
        "how": "e8c97956 + ml-propose by F.5 steps 1-3 (dry and land exit 1 with the one CHANGELOG PROBLEM; step 3 exit 0, entry :91 under ### Fixed), landing_check with --since e8c97956 and the six above (exit 0, no PROBLEM), probe commit 8c0f18d5; the one command --landing-date 2026-11-15 --ml-propose-pr 99999: exit 0, OK",
        "REFERENCE": "0.6.72; header :5 == footer :10024; dates 2026-11-15 at :7 and :10023; rows 0.6.70 :9467, 0.6.71 (ml-propose) :9468, 0.6.72 :9469; no version twice",
        "AGENTS_md": "**Last Updated**: 2026-11-15 (in the diff); :70 '257'",
        "CHANGELOG": "entry at :61, end of ## [Unreleased] / ### Added; ### Changed (#2569) :106; ### Fixed :126 (ml-propose's entry); ## [0.11.5] :183",
        "checks": "reverts: nothing lost (CHANGELOG.md gained 198, removes 0); sequence safety on probe of L5: symbol 58 files 0 findings, docs 8 small-deletion, 0 failures, exit 0; texts byte-identical to L2's except the main sha in pr_body.txt:45; reader suites: 110 (91 readers by name + the 24 carried), 2,664 tests, 0 failed (readers_L5/summary.json)",
    },
    "L1": {
        "tree": WT + "-L1",
        "how": "the one command, --landing-date 2026-11-15, no --ml-propose-pr: exit 0, OK (L1_land.stdout)",
        "REFERENCE": "0.6.70 -> 0.6.71; header :5 == footer :10021; Last Updated 2026-11-15 at :7 and :10020; history row 0.6.71 at :9466 directly after 0.6.70 (:9465); no version twice",
        "AGENTS_md": "**Last Updated**: 2026-11-14 -> 2026-11-15 (:8, in the diff); :70 '242' -> '257'; **Version**: 0.11.5 untouched",
        "CHANGELOG": "entry at :61, end of ## [Unreleased] / ### Added; ### Fixed :106; ## [0.11.5] - 2026-11-13 :116; <ML-PROPOSE-PR> at CHANGELOG.md:78 and in the three rendered texts",
    },
    "L2": {
        "tree": WT + "-L2",
        "how": "ml-propose by F.5 steps 1-2 (dry: exit 1, one PROBLEM, the CHANGELOG; land: exit 1, same), step 3 changelog_into_unreleased_group --group '### Fixed' (exit 0, entry :71), landing_check --since a949d504 76488449 48b66130 f9582a74 26ea0ecb b6b843b6 (exit 0, no PROBLEM), unsigned local probe commit 0c6afa55; then the one command --landing-date 2026-11-15 --ml-propose-pr 99999 (a stand-in number): exit 0, OK, token nowhere",
        "REFERENCE": "0.6.71 (ml-propose) -> 0.6.72; header :5 == footer :10024; Last Updated 2026-11-15 at :7 and :10023; rows 0.6.70 :9467, 0.6.71 (ml-propose) :9468, 0.6.72 :9469; no version twice",
        "AGENTS_md": "**Last Updated**: 2026-11-15 (in the diff); :70 '257'",
        "CHANGELOG": "entry at :61, end of ## [Unreleased] / ### Added; ml-propose's entry under the same section's ### Fixed; ## [0.11.5] - 2026-11-13 at :163; never inside [0.11.5]",
    },
    "slip_case": {"tree": WT + "-L3slip", "how": "--landing-date 2026-11-16 on a949d504: exit 0; both REFERENCE dates, the history row's date, the tally ('**257** on 2026-11-16') and AGENTS.md's date are 2026-11-16, as if_main_moves says"},
    "one_command_unaided": "yes on L1, L2, L5 and the slip case: every stamp, date, count and CHANGELOG position right with no hand step (the manifest's #2507 reason still takes the number by hand)",
}

CHECKED = [
    "carrier: 64 manifest files, 0 differing (util/ad-hoc/2026-11-14_flood4r2_val_ml-tests-r2-claims_verify_carrier.py, at the start and at the end)",
    "the 18 drafts: heads fetched (refs/flood4r2v/pr/<N>) = manifest head_sha for all 18; all OPEN drafts (gh); each draft's diff from its merge base and every file against the landed tree (drafts/<N>/; ..._drafts.py); each draft's shared-document additions against the landed tree (shared_adds_a.txt, ref_lines.txt); Overtoad commits beneath #2472/#2478 (#2468) and #2480/#2481/#2484/#2496 (#2474) traced with gh",
    "the fixes re-derived on the drafts AS SUBMITTED in a scratch worktree of main (L4drafts): pinned black (6 files), flake8 C420 (2), mypy (26 errors in 3 files), test_env_repr_safety (#2481), #2484's two tests on main's code, the CodeQL prescreen (#2496)",
    "the main-verify.yml battery on main and L2: 75 -> 90, each of the 15 once, in ci.yml's order, main's three out-of-order lines by a longest increasing subsequence = the three the texts name, every 'after X' of the carried table, sign_edges before test_configure_commit_signing.py, the SYNC NOTE, no test reading the battery's list (..._battery.py, battery_L2.json)",
    "stamps, dates, counts and CHANGELOG position on main, L1, L2 and the slip case (..._stamps.py, stamps_check.json, stamps_L3slip.json); agents-md-touch-up.yml's rule read",
    "the ERROR row against screen_coverage and triage_batch on main; byte-equal to the 'main' side of ml-docs' recorded resolution on L1 and L2",
    "the macOS list: 12 -> 20, the eight named, 9 guard files on disk, test_every_agent_guard_suite_on_disk_is_listed exists, brace_cap added by #2517",
    "every #N the rendered texts and the carried table cite: exists, state as stated (cited_prs.json); #2064 is a closed issue",
    "the texts on L1 and L2, sentence by sentence (pr_title, pr_body, commit_body, changelog_entry); <ML-PROPOSE-PR> places and the filled sentences (L2, 99999)",
    "ml-propose's propose.py renders the four sites (util/release_train/propose.py:829-921 on L2)",
    "gates: juniper-check-doc-links (AGENTS.md's command, --cross-repo skip) on L1 and L2: PASS, 1661 files; memory budget on L1 and L2: 27413 / 28000, delta +0; pinned pre-commit IN each tree on all 64 files: exit 0, 22 passed, 4 skipped, sha256 unchanged; sequence safety on probes 4ed5e259 (L1) and c35f0a8e (L2) with the rendered title and commit body: symbol-loss 58 files 0 findings, docs 2 files 8 small-deletion warnings (AGENTS.md 2, REFERENCE 6), 0 failures, no Allow-Docs-Rewrite or Allow-Symbol-Loss needed; CodeQL prescreen on L2's 59 changed .py: 1 alert, tests/test_predict_merge.py:45 (main's)",
    "suites on L2: the 91 tests/ files naming a changed document or workflow plus the 24 carried (110 suites), one process each, 4 at a time: 2,664 tests, 0 failed; the 24 carried: 382 tests (readers_L2/summary.json)",
    "nothing main gained is lost on L2 (the carrier's reverts tool: ci.yml 38, CHANGELOG.md 178, REFERENCE 22, AGENTS.md 3 gained; removals re-derived, supersets or the carrier's own edit)",
    "dispositions.json: each entry against the tree",
]

NOT_CHECKED = [
    "CI's whole regression list (257 suites) on L1 or L2 (the tests lens's; the builder kept its f9582a74 run)",
    "the 40 mutants (kept by the builder; the tests lens's)",
    "the macOS job and the strace exec census (kept from the first builder's run)",
    "ml-docs' texts in full (only its manifest's draft-2484 row and its ERROR-row resolution were read)",
    "a CI-parity secret scan of the new files",
    "GitHub's own CodeQL analysis",
]


def main() -> int:
    parser = argparse.ArgumentParser(description="Write findings.json.")
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--status", default="in-progress")
    args = parser.parse_args()
    record = {
        "carrier": f"ml-tests round 2 ({CARRIER}, base f9582a74, 64 files)",
        "lens": "claims (L2b, session 8)",
        "status": args.status,
        "verdict": "SHIP-WITH-FIXES",
        "counts": {"BLOCKER": 0, "MAJOR": sum(f["severity"] == "MAJOR" for f in FINDINGS), "MINOR": sum(f["severity"] == "MINOR" for f in FINDINGS)},
        "checked": CHECKED,
        "not_checked": NOT_CHECKED,
        "findings": FINDINGS,
        "carried_table": CARRIED,
        "landing": LANDING,
        "error_row": {
            "true": True,
            "detail": "the carrier's ERROR row is true on main's code: triage_batch writes gates {} (predict_merge.py:596-604), screen_coverage counts the row absent on every gate, keeps it in the denominator and out of evaluated, so an all-ERROR batch reports screened_fraction 0.0, and unscreened is the skip set (:622-657). Nit, NOT proposed: 'each of that row's gates' reads oddly when gates is empty ('that row as absent on every gate' would be exact).",
            "collision": "none proposed. The landed row is byte-equal on L1 and L2 to the 'main' side of ml-docs' content/resolutions.json, so ml-docs' exact-match resolution applies if this row lands unchanged; any rewording here would break it",
        },
        "worktrees": [WT + suffix for suffix in ("-L1", "-L2", "-L3slip", "-L4drafts")] + [str(JUNIPER / "worktrees/juniper-ml--val--flood4r2-ml-tests-r2-claims--20261114-1949--e8c97956-L5")],
        "local_commits": "unsigned, never pushed: probe commits 0c6afa55 (L2 HEAD) and 8c0f18d5 (L5 HEAD); dangling commit-tree probes 4ed5e259 (L1), c35f0a8e (L2) and the L5 probe in seq_L5/result.json; refs refs/flood4r2v/pr/<N> for the 18 drafts in this validator's worktree",
        "text_fixes": "text_fixes.json (18: T1-T14 and T17-T18 recommended, T15-T16 optional for F8); every 'old' occurs exactly once in its file, for a template also in the L2 rendered text, for a MANIFEST field also in carried_input.json (text_fixes_check.json); texts_fixed/ = the L2 texts with the recommended fixes applied; F13's 19 repeated items are a mechanical rule in its fix",
    }
    with (args.scratch / "findings.json").open("w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=1, ensure_ascii=False)
        handle.write("\n")
    print(f"findings.json written: {record['counts']}, status {args.status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
