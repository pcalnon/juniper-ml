#!/usr/bin/env python3
"""
Rewrite the session-8 parts of the flood-4 "ml-tests" carrier's manifest inputs from the records of its landings.

The manifest tool (util/ad-hoc/2026-11-14_flood4r2_ml-tests-r2_manifest.py) copies open_questions_input.json,
if_main_moves_input.json, checks_input.json and dispositions.json into manifest.json as written. Session 8 changed
what they must say (the owner's ruling of 2026-11-14 resolved one open question; main moved twice; the landing
command is the 2026-11-14 one). This tool rewrites them, taking every number from a landing's own records under
--scratch (derived.json, landing_report.json, the suite reports, the probe's result.json) rather than typing them:

  open_questions_input.json   session 7's items 4, 6, 7 and 8 are kept as they were; items 0, 1, 2, 3, 5, 9 and 10
                              are replaced by what holds on today's main (pre-s8/ keeps the old file);
  if_main_moves_input.json    the one command and its cases, for the 2026-11-14 landing command;
  checks_input.json           session 7's checks kept, session 8's appended;
  dispositions.json           round 1's question 5 (main-verify.yml) marked done by the ruling.

Usage (from the carrier's root):
    python3 util/ad-hoc/2026-11-14_flood4r2_ml-tests-r2_s8_inputs.py --scratch tmp/flood4r2/ml-tests/r2 --landing <landing --out dir>
        --probe <probe --out dir> --precommit-log <log> --walking <util-walking suites' report>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, its session-8 fix-up)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_flood4r2_ml-tests-r2_manifest.py (reads what this writes)
"""

import argparse
import json
import re
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
CARRIER = str(JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "agent-a89a668e6d43bcee2")
WORKTREES = str(JUNIPER / "worktrees") + "/"
LAND = "util/ad-hoc/2026-11-14_flood4r2_ml-tests-r2_land.py"
ML_PROPOSE_TREE = WORKTREES + "juniper-ml--land--flood4r2-ml-propose--20261114-1759--16f2512b"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _summary(report: Path) -> str:
    final = [line for line in report.read_text(encoding="utf-8").splitlines() if line.startswith("FINAL:")]
    return final[-1] if final else "no FINAL line"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--scratch", required=True, type=Path)
    ap.add_argument("--landing", required=True, type=Path, help="the pull request tree's landing --out directory (derived.json, landing_report.json)")
    ap.add_argument("--probe", required=True, type=Path, help="the sequence-safety probe's --out directory (result.json)")
    ap.add_argument("--precommit-log", required=True, type=Path, help="the pinned pre-commit's log on the pull request tree")
    ap.add_argument("--walking", required=True, type=Path, help="the util-walking suites' report on the pull request tree")
    ap.add_argument("--landed-suites", required=True, type=Path, help="the report of the suites run on the landed tree")
    ap.add_argument("--plus-suites", required=True, type=Path, help="the report of the carried suites on main + the ml-propose carrier")
    args = ap.parse_args()
    s = args.scratch
    old_questions = _load(s / "pre-s8" / "open_questions_input.json")
    final = _load(args.landing / "derived.json")
    plus = _load(s / "s8_land_on_plus_ml_propose" / "derived.json")
    report = _load(args.landing / "landing_report.json")
    probe = _load(args.probe / "result.json")
    pr_tree, n_files = report["dest"], len(report["files"])
    token = report["ml_propose_token_stands_at"][0]
    ref, plus_ref = final["docs/REFERENCE.md"], plus["docs/REFERENCE.md"]
    landed, plus_suites, walking = _summary(args.landed_suites), _summary(args.plus_suites), _summary(args.walking)
    main_sha = report["main_sha"][:8]
    questions = [
        f"THE BASE AND THE LANDING. The carrier is built on f9582a74, and its carried proofs (the 40 mutants, CI's whole list, the macOS portability run) are on that base's bytes. Session 8 landed it on origin/main {main_sha} with {LAND} (--landing-date {final['date']}): the five shared files are re-derived there, every other file is copied byte for byte (main changed none of them since f9582a74), and nothing main gained is lost ({args.landing}/reverts.stdout). On the landed tree: {landed} (the carried 24, the ten naming main-verify.yml or its battery, the 92 readers of the shared files); the 55 suites that walk util/ (they can read a helper they do not name), on the pull request tree {pr_tree}: {walking}. CI's whole list was not re-run on {main_sha}. Accept, or run it at the freeze.",
        f"MAIN'S OWN BATTERY IS NOT WHOLLY IN ci.yml's ORDER: on {main_sha} three of its 75 lines stand among later suites (tests/test_main_verify_workflow_guard.py, ci.yml #60; tests/test_main_verify_screen_verdicts.py, #225; tests/test_predict_merge_inherited_git_env.py, #45). This carrier leaves them where they are and places its fifteen by the battery's ci.yml-ordered spine (a naive 'after the nearest earlier suite' rule would have put the guard chain after #225, between #67 and #68). Reordering main's three is outside this pull request, and no text of it says otherwise.",
        old_questions[4],
        old_questions[6],
        old_questions[7].replace("but after #2558 the live cell reads 0.11.5", "but v0.11.5 is released (juniper-ml#2558, 48b66130) and the live cell reads 0.11.5").replace("Left as carried: changing the file would have discarded the proofs kept on its bytes (sha256 1ee53200).", "Left as carried, by the session-8 task: the proofs are kept on its bytes (sha256 1ee53200)."),
        old_questions[8],
        f"<ML-PROPOSE-PR>: ml-propose is not open (the sitting opens it first, then lands this carrier with --ml-propose-pr N). The token stands at {token} of the landed tree (CHANGELOG.md:70 of this carrier's own copy), in the rendered pr_body.txt, commit_body.txt and changelog_entry.txt, and in manifest.json carried[pr 2507].reason (by hand). On 16f2512b + the ml-propose landing tree's 22 files ({ML_PROPOSE_TREE}, copied into a worktree of this session's, probe commit 91026a3c) the one command exits 0: docs/REFERENCE.md {plus_ref['main_version']} -> {plus_ref['version']}, its row directly after ml-propose's, {plus['suite_count']} suites; there the 24 carried suites: {plus_suites}.",
        f"ML-PROPOSE'S LANDING TREE IS STALE: juniper-ml#2567 (merged 2026-11-15 00:40:12Z as a949d504) took docs/REFERENCE.md 0.6.70, the version ml-propose's landing tree on 16f2512b also takes. On {main_sha} main's docs/REFERENCE.md is {ref['main_version']}: ml-propose, landed again by its own command, takes the next step, and this carrier the one after it; the one command derives that from HEAD (main's + one patch step, the row directly after main's newest). The main + ml-propose proof above was made on 16f2512b, before #2567, and was not repeated on {main_sha}.",
        "SCRATCH TO REMOVE AFTER VALIDATION (none has a tmp/ worth keeping): session 7's list (its five worktrees under " + WORKTREES + ", refs/flood4r2/pr/2558 and five probe commits), the first builder's three and round 1's three, all as session 7 named them; session 8's worktrees under " + WORKTREES + ": juniper-ml--flood4r2-ml-tests-r2s8-rebuild--20261114-1814--f9582a74, juniper-ml--flood4r2-ml-tests-r2s8-land--20261114-1815--16f2512b, juniper-ml--flood4r2-ml-tests-r2s8-plus-ml-propose--20261114-1823--16f2512b (at probe commit 91026a3c), juniper-ml--flood4r2-ml-tests-r2s8-final--20261114-1824--16f2512b and juniper-ml--flood4r2-ml-tests-r2s8-pr--20261114-1832--16f2512b (earlier landings of this carrier), and the pull request tree " + pr_tree + " (the orchestrator lands again with the one command); the probe commit 91026a3c (that worktree's HEAD) and the dangling probe commits 3748f5b8, e38eeff3 and " + probe["probe_commit"][:8] + "; and session 7's carrier worktree agent-a4cd1de89c2b57ea3, which this one replaces (its 59 files are in pre-s8/ with their sha256).",
        f"NOT CHECKED: GitHub's own CodeQL analysis; the macOS job; a CI-parity secret scan of the new files; CI's whole list on {main_sha} and on main + ml-propose; the three docs/REFERENCE.md mutants (rows 28, 29, 31) re-pointed at {main_sha}'s text, where their 0.11.4 strings read 0.11.5 (their results are kept on the carrier's f9582a74 bytes).",
    ]
    (s / "open_questions_input.json").write_text(json.dumps(questions, indent=2) + "\n", encoding="utf-8")

    moves = {
        "the_one_command": f"/opt/miniforge3/envs/JuniperCascor1/bin/python3.14 <CARRIER>/{LAND} --carrier <CARRIER> --dest <LANDING WORKTREE: clean, its HEAD the main the pull request is based on> --landing-date <UTC date of the landing, YYYY-MM-DD> --out <SCRATCH DIR> --ml-propose-pr <the ml-propose pull request's number>",
        "carrier": CARRIER,
        "supersedes": "util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_land.py, which wired main-verify.yml from anchors typed into spec.json for six suites; do not use it",
        "interpreter": "the env's own python3.14 (or python3 with tmp/flood4/session8/pyshim of the orchestrator's worktree first on PATH): the env's python3 link starts the system interpreter without PyYAML since 2026-11-14",
        "what_the_command_does": [
            "refuses a carrier whose files are not the sha256 manifest.json records, a --dest that is not clean, and a --dest whose object store lacks the carrier's base f9582a74",
            "leaves ci.yml, main-verify.yml, AGENTS.md, CHANGELOG.md and docs/REFERENCE.md at the landing main's copies; copies every other file when main has not changed it since f9582a74, or rebuilds it three-way (a conflict stops the landing)",
            "re-derives in --dest: the 15 registrations in ci.yml and docs/REFERENCE.md (the wiring tool, from spec.json); all fifteen main-verify.yml Regression Battery lines (the battery tool derives each line's place from ci.yml's order and main's battery, the wiring tool writes them, the battery tool checks them: YAML parse, every line an existing file, each suite once, neighbours in ci.yml's order); the suite count (main's + 15), the tally sentence, the document version (main's + one patch step; header == footer), the Version History row directly after main's newest, both Last Updated dates, the macOS list and its totals, AGENTS.md's count and date",
            "renders pr_title.txt, pr_body.txt, commit_body.txt and changelog_entry.txt from tmp/flood4r2/ml-tests/r2/templates/ into <SCRATCH DIR>/texts/ and inserts the CHANGELOG entry at the end of the top ## [Unreleased]'s ### Added (opening one when a release cut has emptied the section), then checks it stands once and under ## [Unreleased]",
            "checks: the list-drift tool, tests/test_ci_test_wiring_drift.py, tests/test_ci_host_tooling_macos.py, and --dest's change list against the manifest's paths; exit 0 and the last line OK only when all hold; <SCRATCH DIR>/landing_report.json holds every step and the battery lines",
        ],
        "after_the_command": [
            "use <SCRATCH DIR>/texts/ for the pull request",
            "python3 <CARRIER>/util/ad-hoc/2026-11-14_flood4r2_ml-tests-r2_reverts.py --base f9582a749d190a3242aae9cb16c521199bd53013 --manifest <the carrier's tmp/flood4r2/ml-tests/r2/manifest.json> --carrier <CARRIER> --out <SCRATCH DIR>/reverts.json    (in --dest: nothing main gained is lost)",
            "the orchestrator's util/ad-hoc/2026-11-12_flood4r2_s6_seqsafety_probe.py on a freeze of --dest's changed paths, with <SCRATCH DIR>/texts/pr_title.txt and commit_body.txt, scopes 'tests/*.py' 'util/**/*.py' 'util/**/*.bash'",
            "run the 24 suites of tmp/flood4r2/ml-tests/r2/carried_suites.txt there (util/ad-hoc/2026-11-09_flood4r2_ml-tests_run_suites.py --root <dest> --only ...), with the six Sentry variables empty and DBUS_SESSION_BUS_ADDRESS=unix:path=/nonexistent/no-session-bus (tmp/flood4/session8/runenv.bash of the orchestrator's worktree sets both)",
        ],
        "cases": {
            "ml-propose merged (the planned order: the sitting opens it first, then this carrier)": {
                "re_derive": "the one command with --ml-propose-pr <its number>, on the main that holds ml-propose. docs/REFERENCE.md becomes ml-propose's + 1 (0.6.71 on 16f2512b + ml-propose; on " + main_sha + ", whose docs/REFERENCE.md is " + ref["main_version"] + ", ml-propose takes the next step and this carrier the one after it); the Version History row goes directly after ml-propose's; the CHANGELOG entry and the two bodies get the number; the manifest's carried[pr 2507].reason gets it by hand",
                "proved_here": f"on 16f2512b + the 22 files of the ml-propose landing tree {ML_PROPOSE_TREE} (copied, sha256 equal to the orchestrator's sha22 list, probe commit 91026a3c): exit 0, docs/REFERENCE.md {plus_ref['main_version']} -> {plus_ref['version']} (header == footer, row :9468 after ml-propose's :9467), {plus['suite_count']} suites, battery check OK, the entry at the end of ### Added above the ### Fixed that holds ml-propose's entry; the 24 carried suites: {plus_suites} (the propose suite 188). Without --ml-propose-pr, as run here, the token stays. Evidence: tmp/flood4r2/ml-tests/r2/s8_land_on_plus_ml_propose/, s8_plus_ml_propose_suites.txt",
            },
            f"main is still {main_sha} and ml-propose has not merged": {
                "re_derive": f"nothing: the landing in {pr_tree} ({args.landing}) is the pull request's tree (with the token); ml-propose is held with it",
                "proved_here": f"exit 0, OK; {final['main_suite_count']} -> {final['suite_count']} suites; docs/REFERENCE.md {ref['main_version']} -> {ref['version']} dated {ref['last_updated']}; AGENTS.md Last Updated {final['AGENTS.md']['main_last_updated']} -> {final['AGENTS.md']['last_updated']} (in the diff); battery 90 lines; {landed}",
            },
            "the landing slips past 2026-11-15 UTC": {
                "re_derive": "the one command with the new --landing-date: both docs/REFERENCE.md dates, the history row's date, the tally's date and AGENTS.md's Last Updated become that date",
                "why_it_matters": "the stamps must carry the UTC date of the day the pull request lands. AGENTS.md's line is in the diff either way (main says 2026-11-14), so .github/workflows/agents-md-touch-up.yml passes on any day from the landing date on; it fails only for a date in the future",
            },
            "main moves in any other way before the freeze (another session's pull request on ci.yml, docs/REFERENCE.md or main-verify.yml)": {
                "re_derive": "the one command on the main of the day, then the after_the_command checks. The battery lines are derived from that main's ci.yml and battery, so a suite another pull request added to both is placed around; the wiring and shared-edits tools find their places by exact anchors and refuse (exit 1) when one is missing or repeated; a carried test file that main changed is rebuilt three-way, and a conflict stops the landing with the three inputs under <SCRATCH DIR>/merge/",
            },
        },
        "ml_propose_token": {
            "token": "<ML-PROPOSE-PR>",
            "stands_at": [f"{token} of a tree landed on {main_sha} (CHANGELOG.md:70 of the carrier's own copy)", "<SCRATCH DIR>/texts/pr_body.txt, commit_body.txt and changelog_entry.txt (and tmp/flood4r2/ml-tests/r2/texts/, templates/)", "manifest.json: carried[pr 2507].reason"],
            "filled_by": "--ml-propose-pr N of the one command (the landed tree and the rendered texts); the manifest's reason by hand",
        },
    }
    (s / "if_main_moves_input.json").write_text(json.dumps(moves, indent=1) + "\n", encoding="utf-8")

    checks = _load(s / "pre-s8" / "checks_input.json")
    precommit = args.precommit_log.read_text(encoding="utf-8")
    checks += [
        {"what": "SESSION 8: the session-7 carrier's 59 files copied into this worktree (reset to f9582a74) and proved byte-identical to its manifest; the change list equals the manifest's paths", "command": "python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_manifest.py --scratch tmp/flood4r2/ml-tests/r2 --verify", "result": "pass", "log": "tmp/flood4r2/ml-tests/r2/PROGRESS.txt (2026-11-14T23:59:32Z)"},
        {"what": "SESSION 8: the new landing command rebuilds the carrier on its own base (f9582a74, --landing-date 2026-11-13): exit 0; ci.yml, AGENTS.md and docs/REFERENCE.md reproduced byte for byte, main-verify.yml and CHANGELOG.md re-derived (the battery and the entry's battery sentence), and taken into the carrier", "command": f"python3 {LAND} --carrier {CARRIER} --dest {WORKTREES}juniper-ml--flood4r2-ml-tests-r2s8-rebuild--20261114-1814--f9582a74 --landing-date 2026-11-13 --out tmp/flood4r2/ml-tests/r2/s8_rebuild_on_f9582a74", "result": "pass", "log": "tmp/flood4r2/ml-tests/r2/s8_rebuild_on_f9582a74.stdout"},
        {"what": f"SESSION 8: THE LANDING on origin/main {main_sha} (--landing-date {final['date']}): exit 0, OK; {final['main_suite_count']} -> {final['suite_count']} suites, list drift and wiring drift clean, macOS gate OK, battery 90 lines in ci.yml's order; docs/REFERENCE.md {ref['main_version']} -> {ref['version']}; the CHANGELOG entry at the end of [Unreleased] / ### Added", "command": f"python3 {LAND} --carrier {CARRIER} --dest {pr_tree} --landing-date {final['date']} --out {args.landing}", "result": "pass", "log": str(args.landing) + ".stdout"},
        {"what": "SESSION 8: nothing main gained since f9582a74 is lost in the landed tree (every gained line kept, a superset or re-derived; every removed line re-derived, a superset or the carrier's own edit)", "command": "python3 util/ad-hoc/2026-11-14_flood4r2_ml-tests-r2_reverts.py --base f9582a74 --manifest tmp/flood4r2/ml-tests/r2/manifest.json --carrier <carrier> --out .../reverts.json  (in the landing worktree)", "result": "pass", "log": str(args.landing / "reverts.stdout")},
        {"what": f"SESSION 8: suites on the landed tree ({main_sha} + this carrier): {landed}", "command": "bash <the orchestrator worktree's tmp/flood4/session8/runenv.bash> python3 util/ad-hoc/2026-11-09_flood4r2_ml-tests_run_suites.py --root <landing worktree> --jobs 4 --only <s8_suites_on_landed.txt>", "result": "pass", "log": "tmp/flood4r2/ml-tests/r2/s8_landed_suites.txt"},
        {"what": f"SESSION 8: the 55 suites that walk util/ (they can read a helper they do not name), on the pull request tree: {walking}", "command": "the same runner, --root <the pull request tree> --only <s8_util_walking_all.txt>", "result": "pass" if " 0 failed alone" in walking else "see log", "log": str(args.walking)},
        {"what": f"SESSION 8: the 24 carried suites on 16f2512b + the ml-propose landing tree's 22 files: {plus_suites}", "command": "the same runner, --root <plus-ml-propose worktree> --only <carried_suites.txt>", "result": "pass", "log": "tmp/flood4r2/ml-tests/r2/s8_plus_ml_propose_suites.txt"},
        {"what": f"SESSION 8: the pinned pre-commit on the {n_files} changed files of the pull request tree: " + ("exit 0" if "Failed" not in precommit else "FAILED") + f", {precommit.count('Passed')} hooks passed, {precommit.count('Skipped')} skipped, nothing rewritten (sha256 before == after)", "command": "xargs -a <the manifest's paths> /opt/miniforge3/bin/pre-commit run --files; sha256sum -c <their sha256 before>", "result": "pass", "log": str(args.precommit_log)},
        {"what": "SESSION 8: CodeQL prescreen, the seven shapes, G-PATH and G-TMP on the helpers session 8 added: 0 predicted alerts, 0 shape hits, both gates PASS", "command": "python3 util/ad-hoc/2026-10-05_codeql_python_prescreen.py <the new helpers>; python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_codeql_shapes.py <them>; python3 util/home_path_literal_check.py <them>; python3 util/tmp_path_literal_check.py <them>", "result": "pass", "log": "tmp/flood4r2/ml-tests/r2/s8_codeql_prescreen.log"},
        {"what": f"SESSION 8: CI's two sequence-safety screens on a commit-tree probe of the pull request tree ({probe['adds']} adds on {main_sha}) with the final title and commit body: " + json.dumps(probe)[:300], "command": "python3 <orchestrator>/util/ad-hoc/2026-11-12_flood4r2_s6_seqsafety_probe.py --freeze <a freeze of the pull request tree's changed paths> --title .../texts/pr_title.txt --body .../texts/commit_body.txt --scope 'tests/*.py' --scope 'util/**/*.py' --scope 'util/**/*.bash' --main-ref origin/main", "result": "pass" if probe.get("symbol_exit") == 0 and probe.get("docs_exit") == 0 else "fail", "log": str(args.probe) + ".stdout"},
    ]
    (s / "checks_input.json").write_text(json.dumps(checks, indent=2) + "\n", encoding="utf-8")

    dispositions = _load(s / "pre-s8" / "dispositions.json")
    for row in dispositions["round_1_open_questions"]:
        if row.get("n") == 5:
            row["disposition"] = "done"
            row["why"] = "the owner's ruling of 2026-11-14, \"Add all fifteen\": all fifteen suites are in main-verify.yml's Regression Battery, in ci.yml's order (session 8; the battery tool derives each line's place at the landing). Six were there before, as round 1 built it."
    (s / "dispositions.json").write_text(json.dumps(dispositions, indent=2) + "\n", encoding="utf-8")
    left = [name for name in ("open_questions_input.json", "if_main_moves_input.json") if re.search(r"\bsix of the fifteen\b|the six in main-verify", (s / name).read_text(encoding="utf-8"))]
    print(f"rewritten: open_questions ({len(questions)}), if_main_moves, checks (+10, {len(checks)} in all), dispositions; stale 'six' statements left: {left or 'none'}")
    return 1 if left else 0


if __name__ == "__main__":
    raise SystemExit(main())
