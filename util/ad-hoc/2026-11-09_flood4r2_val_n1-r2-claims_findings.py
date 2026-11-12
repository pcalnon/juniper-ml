"""
Build the N1 round-2 claims-lens findings.json and prove every text fix's `old` occurs exactly once.

Reads the carrier's files (worktree path given on the command line), checks each EXACT old -> new
pair against the file it names (old must occur once, new must not already be there), and writes
<scratch>/findings.json. Exit 1 if any old string does not occur exactly once.

Usage: python3 -I <this> <carrier-worktree> <scratch-dir>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 round 2, N1 (juniper-cascor paused-fit wedge) claims-lens validation;
         juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8
"""

import json
import sys
from pathlib import Path

CHANGELOG = "CHANGELOG.md"
PR_BODY = "tmp/flood4-fix/n1-r2/pr_body.txt"
REPRO = "util/ad-hoc/2026-11-08_stop_then_start_race_repro.py"

F1_FIXES = [
    (CHANGELOG, 'The owner ruled on 2026-11-09 ("Fix all four now") that it gets its own fix, in a separate PR: a per-run stop signal, or a start that refuses or fences a live fit.', 'The owner ruled on 2026-11-09 ("cascor: stop-then-start") that it gets its own fix, in its own PR. Candidate fixes, which no ruling chose: a per-run stop signal, or a start that refuses or fences a live fit.'),
    (PR_BODY, 'The owner ruled on 2026-11-09 ("Fix all four now") that it gets its own fix, in a separate PR. A reproducer is included.', 'The owner ruled on 2026-11-09 ("cascor: stop-then-start", a ruling given after the record\'s rulings 1-14) that it gets its own fix, in its own PR. A reproducer is included.'),
    (PR_BODY, 'The owner ruled on 2026-11-09 ("Fix all four now") that this race gets its own fix, in a separate PR: a per-run stop signal, or a start that refuses or fences a live fit.', 'The owner ruled on 2026-11-09 ("cascor: stop-then-start") that this race gets its own fix, in its own PR. Candidate fixes, which no ruling chose: a per-run stop signal, or a start that refuses or fences a live fit.'),
    (REPRO, '"Fix all four now", that it gets its own fix, in a separate PR)', '"cascor: stop-then-start", that it gets its own fix, in its own PR)'),
]

F2_FIXES = [
    (CHANGELOG, "Unlike juniper-service-core, where the new run starts at once and the old fit's return completes it, cascor's queue keeps the new run from starting until the old fit returns, so the old fit is still the owner when it settles.", "Unlike juniper-service-core, where the new run starts at once on its own thread and already owns the lifecycle when the old fit returns, cascor's queue keeps the new run from starting until the old fit returns, so the old fit is still the owner when it settles."),
    (PR_BODY, "juniper-service-core's fix for the same wedge, built before this one and not merged as of this PR, needed such a check", "juniper-service-core's fix for the same wedge, built before this one and merged as juniper-ml#2531 (`7b3b91b7`), needed such a check"),
    (PR_BODY, "juniper-service-core's fix for the same wedge (unmerged; its `main`, juniper-ml `4bae7520`, has no such guard) checks", "juniper-service-core's fix for the same wedge (juniper-ml#2531, `7b3b91b7`) checks"),
    (PR_BODY, "There the new run starts at once on its own thread and the old fit's return completes it.", "There the new run starts at once on its own thread, so it already owns the lifecycle when the old fit returns: since juniper-ml#2531 that return settles nothing (juniper-service-core 0.7.2, published before #2531, still completes the new run)."),
    (REPRO, "where the new run starts on its own thread at once and the old\nfit's return marks it COMPLETED while it trains,", "where the new run starts on its own thread at once and so\nalready owns the lifecycle when the old fit returns (juniper-ml#2531's thread check),"),
]

F3_FIXES = [
    (PR_BODY, ", which lands in juniper-ml separately.", ", on juniper-ml `main` since juniper-ml#2530 (`734aab58`)."),
    (PR_BODY, "`main` has not moved since.", "`main` has moved once since, by juniper-cascor#748 (`7640d42`), which changes only `CHANGELOG.md` and the two lock files; this change's `CHANGELOG.md` merges onto it with no conflict."),
]

F4_FIXES = [
    (REPRO, "Retire when: that PR has merged (a per-run stop signal, or a start that refuses or fences a\n             live fit)", "Retire when: that PR has merged"),
]


CHECKED = [
    "Release history, per tag (util/ad-hoc/2026-11-09_flood4r2_val_n1-r2-claims_release_history.py -> release_history.log): each of the 10 tags' own state_machine.py EXECUTED (mark_completed refuses PAUSED in all 10; START from that PAUSED -> STARTED; RESUME -> STARTED); each manager.py read (one mark_completed site per tag, result ignored; 'Training already in progress' refusal in all 10; 'Cannot start training while paused' only from v0.10.0; _check_for_interrupt absent only in v0.3.17, which has no _pause_event.wait anywhere under src). 4710cc1 = cascor#584, first tag v0.10.0; f4453fa = cascor#244, first tag v0.5.0. PyPI juniper-cascor = exactly the 10 tags, latest 0.13.0. v0.9.0's create-on-start PAUSED refusal (_create_network_locked) does not fire for a plain or start_fresh start with a network present. Every 'How far back' / '0.10.0 to 0.13.0' / '0.3.17 to 0.9.0' text (CHANGELOG, PR body, commit body, JUNIPER_CASCOR_API_REFERENCE.md, API_SCHEMAS.md, cheatsheet) is TRUE. No text names a next release number.",
    "Owner rulings: the record on juniper-ml origin/main (#2530) §4 and §8 read via gh api; ruling 11 = 2026-11-08, \"Fix all four now\" (HANDOFF_2026-11-08 table row 11), listing cascor's paused-fit wedge. Every ruling-11 citation for the wedge (CHANGELOG 'Where it was found', PR body :8, commit body, test module docstring, manager.py _run_training docstring, mutation-check header, repro 'Related') is accurate. Ruling 17 (2026-11-09) labels from BRIEF_S4_ADDENDUM.txt and HANDOFF_2026-11-09 :121 -> F1.",
    "Line citations on main f3dfee8c: manager.py :1992, :2042, :2085, :2526, :2532, :3052-3061, :3058, :3059, :3107, :3117, :3758 (inside swap_dataset_live's `with self._lock` from :3680), :3805, :3832; state_machine.py :262-271/:264/:270; app.py:469; routes/training.py :145-154 / :157-166 and their 409 texts; the HTTPException envelope (error.message, app.py:941-990); juniper-canopy src/main.py:3784-3789 at 63a2f3d7; CCN cadence `epoch % 25 == 0 or epoch == epochs - 1` (cascade_correlation.py:2186); monitored_fit / _install_monitoring_hooks gone from main (comments only); lifecycle and routes unchanged v0.13.0 -> f3dfee8c -> 7640d42.",
    "juniper-service-core statements against juniper-ml origin/main 7b3b91b7 (#2531): its settle, pause_training and resume_training all hold self._lock (TRUE, as the texts say); its settle is guarded by `self._thread is threading.current_thread()` (makes 'unmerged' and 'the old fit's return completes it' false -> F2); PyPI service-core latest 0.7.2 uploaded 09:52Z, before #2531.",
    "New tests, my worktree juniper-cascor--val--flood4r2-n1-r2-claims--20261109-0825--f3dfee8c, JuniperCascor1 3.14.7, JUNIPER_CASCOR_LOG_DIR unset, provenance = the worktree's own src: the 23 new tests on main's lifecycle files: 13 failed, 10 passed (the 4 controls and the 6 refusals) -- matches the texts (newtests_on_main_mine.log). Carrier code: the new module + the whole FSM suite, 88 passed (newtests_and_fsm_suite_on_carrier.log). 15 + 8 = 23 matches; the 6 refusal params reach their named states (mark_resume_ready/investigating/replaying accept STOPPED).",
    "Mutation check re-run in my worktree (util/ad-hoc/2026-11-08_paused_fit_wedge_mutation_check.py --base f3dfee8c): CONTROL green, provenance ok, 24/24 caught; every per-mutant failure count equals the PR body's table (M00 13, M01 6, M02 4, M03 4, M04 1, M05 1, M06-M09 2/1/1/1, M10-M12 5 each, M13 13, M14 1, M15 2, M16 5, M17-M20 2/1/1/1, M21-M23 2 each) (mutation_mine.log). The builder's own logs also match the texts' unit (5885/1/15), coverage (96.60%; manager 2246/32/33, state_machine 215/4/2) and integration (177/21) figures, but those suites were not re-run.",
    "The state-machine lock text vs the code: _atomic wraps handle_command (so _handle_resume -> _restore_from_paused run inside it), set_phase, save/get_candidate_state, mark_completed/failed/resume_ready/investigating/replaying and get_state_summary; is_* and properties unlocked, as stated; no src code outside the FSM writes its private fields; no custom logging.Handler subclass in src (stock console/file handlers). The forced-resume story (check PAUSED, switch, settle completes, resume writes STARTED over COMPLETED, every start refused) describes what the pre-lock code does, and the lock closes it at the FSM level.",
    "Stamps and placement: cheatsheet 1.0.8 -> 1.0.9 / 2026-11-09 (header only, no footer stamp); API_REFERENCE.md and API_SCHEMAS.md Last Updated bumped once, header = footer = 2026-11-09, Version 0.3.21 untouched; JUNIPER_CASCOR_API_REFERENCE.md carries no stamp. CHANGELOG entry under [Unreleased] / ### Fixed, below 'Load from HDF5', above 'Bandit SARIF'; `git merge-file -p carrier base 7640d42` exit 0, entry still under Fixed above #748's new ### Security (CHANGELOG.merged.md).",
    "Round 1's C1-C14: each present in the carrier (C1 ruling-11 citations at all 7 sites; C2 release history, extended, true; C3 overlap/shutdown wording at all 8 sites; C4 API_REFERENCE section rewritten + stamps + listed in PR/CHANGELOG; C5 error.message for pause, resume and stop; C6 placement; C7 no title line in commit_body; C8 no trailers; C9 'port' wording gone; C10 unguarded stale effects named; C11 log-location note; C12 API_SCHEMAS stamps; C13 race named in API_SCHEMAS + PR + CHANGELOG; C14 'begins a new run', 'all 24 of its mutants', hook wording, FSM state names). C9's replacement and C13's update are now stale or misquoted: F2, F1.",
    "Env facts in the texts: installed juniper-cascor metadata 0.11.0 vs pyproject 0.13.0 (test_version_matches_pyproject's environmental failure).",
]

NOT_CHECKED = [
    "The full CI unit job (5885 passed / 1 failed / 15 deselected), coverage 96.60% and the per-file statement/miss/partial figures, and quick integration 177: not re-run (about 9 minutes on this host; time box). Only the 23 new tests and the FSM suite were run.",
    "The 5 failures against round 1's exact files; the 500-run stress figures (3750/3750 twice); the probe figures (178/200, 23/200, 0/200, 0/300, the 800 resume-race runs); the golden-lane test; the Sequence Safety replica; pre-commit and markdownlint; the CodeQL prescreen and home-path check of the carrier's own util/ad-hoc scripts.",
    "Python 3.12 / 3.13 and the macOS leg; a free-threaded build.",
    "Code correctness beyond what a claim states (the code lens's remit).",
]


def check(root: Path, fixes: list) -> list:
    out = []
    for rel, old, new in fixes:
        text = (root / rel).read_text()
        n_old = text.count(old)
        n_new = text.replace(old, "").count(new)  # outside the old text (a new may be a prefix of its old)
        out.append({"file": rel, "old": old, "new": new, "old_count": n_old, "new_already_present": n_new})
    return out


def main() -> int:
    root = Path(sys.argv[1])
    scratch = Path(sys.argv[2])
    findings = [
        {
            "id": "F1",
            "severity": "BLOCKER",
            "where": "CHANGELOG.md ([Unreleased] / Fixed, the paused-fit entry, 'Evidence and next step.' bullet); tmp/flood4-fix/n1-r2/pr_body.txt:6 and :129; util/ad-hoc/2026-11-08_stop_then_start_race_repro.py:8-9",
            "claim": "The cascor stop-then-start race was ruled on 2026-11-09 with the words \"Fix all four now\", and (CHANGELOG, PR body :129) that ruling named the fix: \"a per-run stop signal, or a start that refuses or fences a live fit\". Both are false. \"Fix all four now\" is ruling 11's label, given on 2026-11-08, and ruling 11 lists juniper-SERVICE-CORE's stop-then-start race, not cascor's (record §8 item 11, second bullet). cascor's race was ruled on 2026-11-09 as ruling 17, a multiSelect whose chosen label is \"cascor: stop-then-start\"; it is not in the record (#2530 covers rulings 1-14). No ruling names a mechanism. The CHANGELOG instance lands on main.",
            "evidence": "gh api repos/pcalnon/juniper-ml/contents/notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (origin/main) §8 item 11: '\"Fix all four now\", each in its own validated, signed PR: ... juniper-service-core's stop-then-start race ...'; prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-08_flood4-record-validated-fixes-built-round2-triaged.md:112-126 ('The owner's rulings of 2026-11-08' ... '| 11 | N-1..N-4 | \"Fix all four now\" |'); HANDOFF_2026-11-09_flood4-record-merged-fixes-corrected-landing-next.md:121 ('| 17 | New defects (multiSelect) | all four: \"data: 44 unrun tests\", \"cascor: stop-then-start\", ...'); tmp/flood4/session4/BRIEF_S4_ADDENDUM.txt ruling 17 (same labels). The M-3 landing already removed the same mechanism attribution from service-core's texts (tmp/flood4/session4/land/m3/edits.json:7-14).",
            "fix": check(root, F1_FIXES),
        },
        {
            "id": "F2",
            "severity": "MAJOR",
            "where": "CHANGELOG.md (stop-then-start 'Why the ownership check does not help.' bullet); tmp/flood4-fix/n1-r2/pr_body.txt:5, :28, :127; util/ad-hoc/2026-11-08_stop_then_start_race_repro.py:27-28",
            "claim": "juniper-service-core's paused-fit fix is 'not merged as of this PR' / 'unmerged; its main ... has no such guard', and in service-core's stop-then-start race 'the old fit's return completes it'. juniper-ml#2531 merged that fix at 2026-11-09T11:22:24Z (7b3b91b7), with the guard `self._thread is threading.current_thread()` on every settle, so on service-core main a superseded thread's return settles nothing and no longer completes the new run (the M-3 PR body itself says it 'closes the consequence'). The statement stays true only of the published juniper-service-core 0.7.2 (PyPI 2026-11-09T09:52Z, before the merge). The CHANGELOG instance lands on main in the present tense.",
            "evidence": "gh api 'repos/pcalnon/juniper-ml/commits?per_page=8': '7b3b91b7 2026-11-09T11:22:24Z fix(service-core): a fit that returns while paused settles COMPLETED ... (#2531)'; juniper-service-core/juniper_service_core/lifecycle/manager.py@7b3b91b7:309-341 (`with self._lock:` / `if not self._stop_event.is_set() and self._thread is threading.current_thread():` before RESUME + mark_completed); start_training:191 assigns the new thread under the same lock; PyPI juniper-service-core latest 0.7.2 uploaded 2026-11-09T09:52:45Z.",
            "fix": check(root, F2_FIXES),
        },
        {
            "id": "F3",
            "severity": "MINOR",
            "where": "tmp/flood4-fix/n1-r2/pr_body.txt:8 and :73",
            "claim": "The record 'lands in juniper-ml separately' (it merged as juniper-ml#2530, 734aab58, 2026-11-09T10:31:40Z), and cascor 'main has not moved since' f3dfee8c (it moved to 7640d42, juniper-cascor#748, 2026-11-09T10:14:22Z). #748 touches only CHANGELOG.md and the two lock files, so no line citation or test result moves, and `git merge-file -p <carrier> <base> <7640d42>` rebuilds CHANGELOG.md with 0 conflicts, the entry still under [Unreleased] / ### Fixed above #748's new ### Security; but the orchestrator must rebase onto 7640d42 and the PR text must not say main is unchanged.",
            "evidence": "git -C <carrier> ls-remote origin refs/heads/main -> 7640d420be43...; git log f3dfee8c..7640d42 -> one commit (#748); git diff --name-only f3dfee8c 7640d42 -> CHANGELOG.md, requirements-cpu.lock, requirements.lock; git diff --stat f3dfee8c 7640d42 -- src/ -> empty; merge-file exit 0 (CHANGELOG.merged.md in this scratch dir).",
            "fix": check(root, F3_FIXES),
        },
        {
            "id": "F4",
            "severity": "MINOR",
            "where": "util/ad-hoc/2026-11-08_stop_then_start_race_repro.py:10-11",
            "claim": "'Retire when: that PR has merged (a per-run stop signal, or a start that refuses or fences a live fit)' presents an unchosen design as what the ruled PR will be. The script ships to main as provenance.",
            "evidence": "No ruling (record §8 1-14; rulings 15-18 in BRIEF_S4_ADDENDUM.txt) names a mechanism for the cascor race.",
            "fix": check(root, F4_FIXES),
        },
    ]
    bad = [(f["id"], fx["file"], fx["old_count"]) for f in findings for fx in f["fix"] if fx["old_count"] != 1 or fx["new_already_present"]]
    payload = {
        "carrier": "N-1 juniper-cascor paused-fit wedge (round 2), worktree juniper-cascor--fix--paused-fit-wedge--20261108-1815--f3dfee8c, base f3dfee8c",
        "lens": "claims",
        "checked": [],
        "not_checked": [],
        "findings": findings,
        "fix_uniqueness_failures": bad,
    }
    out = scratch / "findings.json"
    payload["checked"] = CHECKED
    payload["not_checked"] = NOT_CHECKED
    with open(out, "w") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
    print("findings:", len(findings), "fix pairs:", sum(len(f["fix"]) for f in findings), "uniqueness failures:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
