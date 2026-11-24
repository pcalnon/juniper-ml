"""
Write the session-8 tests-lens findings.json for the ml-tests carrier from the evidence files in its scratch directory.

Counts and results are read from the runs (the CI list, the mutation results, the battery check, the landings, the
interpreter runs), not typed; the findings, the per-file verdicts and the not-checked list are the validator's.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent L1b, flood-4 session 8)
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, the ml-tests carrier)

Usage:
    python3 <this file> --scratch <the lens's scratch dir> --status final|in-progress
"""

import argparse
import json
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
FILE_ROWS = (
    ("tests/test_claude_agent_guard_nest_depth.py", "#2469", ["G1", "H1"], "temp HOME; the guard as a sys.executable subprocess; no shell, no git", "sound"),
    ("tests/test_claude_agent_guard_push_signed.py", "#2489", ["G2"], "GuardHarness (sys.executable -I guard); no shell, no git", "sound"),
    ("tests/test_claude_agent_guard_ansi_escapes.py", "#2491", ["G3", "G3b"], "temp HOME; sys.executable subprocess", "sound"),
    ("tests/test_claude_agent_guard_gpgsign_off.py", "#2492", ["G4"], "GuardHarness (sys.executable -I guard)", "sound"),
    ("tests/test_claude_agent_guard_sign_edges.py", "#2515", ["G5", "G6"], "temp HOME; sys.executable subprocess", "sound"),
    ("tests/test_launcher_empty_version_output.py", "#2478", ["W1", "W1b", "H2"], "bash; a fake claude on PATH", "sound"),
    ("tests/test_launcher_prompt_and_version_edges.py", "#2472", ["W2", "W3", "W4", "W5"], "bash", "sound"),
    ("tests/test_prompt_file_boolean_tokens.py", "#2495", ["W6"], "bash", "sound"),
    ("tests/test_prompt_file_kind.py", "#2503", ["W7", "W8"], "bash; a directory and a symlink in a temp dir", "sound"),
    ("tests/test_wake_spacer_flags.py", "#2509", ["W9"], "bash", "sound"),
    ("tests/test_predict_merge_error_screen.py", "#2512", ["P1", "P1b", "H6"], "none (pure function)", "sound"),
    ("tests/test_predict_merge_guard_edges.py", "#2496", ["P2", "P3", "P4", "P5"], "git, rm (synthetic repos in a temp dir)", "sound"),
    ("tests/test_predict_merge_scratch_edges.py", "#2481", ["P6a", "H3", "X1c", "X2c"], "git with --object-format=sha256 and linked worktrees, rm; a stand-in smudge filter (git-lfs not needed)", "sound"),
    ("tests/test_predict_merge_shallow_worktree.py", "#2484", ["P6b", "P7", "H7"], "git (a shallow linked worktree)", "sound"),
    ("tests/test_cascor_eval_zero_and_enabled.py", "#2499", ["S1", "S2", "S3", "S4", "S1fix", "S1ctl"], "none (pure function)", "sound, with gap F1 (S1 survives)"),
    ("juniper-ci-tools/tests/test_symbol_loss_weaken_boundary.py", "#2475", ["C1"], "none; runs under pytest in ci-ci-tools.yml", "sound"),
    ("tests/test_ci_host_tooling_macos.py", "the Overtoad's ruling of 2026-11-12 (macOS wiring)", ["D1", "D2", "D3", "D4", "D5", "D6a"], "PyYAML; bash for the detection rehearsal under a stub git", "sound"),
    ("tests/test_predict_merge.py", "#2480 (one assertion)", ["P8"], "git, rm; the juniper-ci-tools console scripts", "sound"),
    ("tests/test_pyproject_extras.py", "#2507 + F6", ["R1", "R2", "R3s8", "R4", "R5", "R6", "R7", "H5", "R7fix", "R7ctl"], "tomllib (SkipTest below 3.11; CI runs 3.12+)", "sound, with gap F2 (R7 survives)"),
)

FINDINGS = [
    {
        "id": "F1",
        "severity": "MINOR",
        "where": "tests/test_cascor_eval_zero_and_enabled.py:104-119 (the code it should pin: util/experiments/stats_summary.py:334)",
        "claim": "The suite's title says 'only ``enabled is False`` turns eval metrics off', but the in-loop arm's off switch (stats_summary.py:334, `live.get(\"enabled\") is False`) is not pinned for `enabled: 0`. test_a_missing_enabled_or_a_zero_still_reports_the_final asserts only on blocks['eval_scalars'] (the final arm, :294). The mutant S1 (`not live.get(\"enabled\", True)` at :334) drops the in-loop scalars for `enabled: 0` and every test still passes. The detailed docstring bullet speaks of the held-out scores only, so the gap is between the title and the pins, not a false sentence.",
        "evidence": "session 7: mutants/results.json S1 rc 0, 'Ran 5 tests ... OK' (target and suite bytes unchanged on a949d504: s8_keep.json). Session 8: s8_mutants/s8_results.json S1fix (S1 + the fix) rc 1, FAIL test_a_missing_enabled_or_a_zero_still_reports_the_final; S1ctl (the fix alone) rc 0, Ran 5.",
        "fix": "proposed/S1_in_loop_enabled_zero.diff (patch -p1 on L applies): after line 119, `self.assertEqual(held[\"f1\"], METRICS_FINAL_TEST_SPLIT[\"eval_metrics\"][\"final\"][\"f1\"])`, add three lines inside the subTest: `in_loop = ss.cascor_eval_blocks(body)[\"eval_scalars_in_loop\"]`, `self.assertIsNone(in_loop[\"absent\"], \"only enabled is False turns the in-loop scalars off\")`, `self.assertEqual(in_loop[\"f1\"], METRICS_FINAL_TEST_SPLIT[\"f1\"])`.",
    },
    {
        "id": "F2",
        "severity": "MINOR",
        "where": "tests/test_pyproject_extras.py:616 and :622 (the parser rule it claims: :364-365)",
        "claim": "_reference_matrix's docstring says 'Parsing stops at the first line that is not part of that table, so a later table is not a row', and test_parser_reads_the_current_series_row_not_an_older_one ends with `self.assertNotIn(\"Service Ports\", rows)`, which cannot fail: the fixture's only later text is the heading '### Service Ports', which never starts with '|', so it is never a row whether parsing stops or continues. The mutant R7 (`break` -> `continue` at :374) passes every test; on today's docs/REFERENCE.md it is equivalent (no later table has a 0.11.x row), so nothing on main is wrong today, but the stop rule is unpinned.",
        "evidence": "session 7: mutants/results.json R7 rc 0, Ran 20 OK. Session 8 (inputs moved on main, re-run): s8_mutants/s8_results_part1.json R7 rc 0 Ran 20 SURVIVED; s8_results.json R7fix (R7 + the fix) rc 1, FAIL test_parser_reads_the_current_series_row_not_an_older_one; R7ctl (the fix alone) rc 0, Ran 20.",
        "fix": "proposed/R7_later_table_not_a_row.diff (patch -p1 on L applies): in the fixture at :616 replace `\\n\\n### Service Ports\\n\"` with `\\n\\n### Service Ports\\n\\n| Service | Port |\\n|---------|------|\\n| 9.9.x   | 8100 |\\n\"` (a later table whose first cell repeats a series label), and at :622 replace `self.assertNotIn(\"Service Ports\", rows)` with `self.assertNotIn(\"Service\", rows, \"a later table is not a row of the matrix\")`; the existing `rows[\"9.9.x\"][1] == \">=9.9.1\"` assertion then catches the overwrite.",
    },
]

NOT_CHECKED = [
    "GitHub's own CodeQL analysis (the prescreen and the shape grep only).",
    "The macOS job itself. Not provable off a Mac: the runner's setup-python 3.12 build on macOS, temporary homes under /var -> /private/var, APFS. Proved here instead: the eight guard suites (and main's ninth) under CPython 3.9.25 (the hook's /usr/bin/python3 on turing) and 3.12.16, the guard executed by that interpreter, no shell or git started.",
    "A CI-parity secret scan of the new files.",
    "CI's whole list on main + ml-propose (there: the 19 carried files, the propose suite and the wiring-drift suite).",
    "A fresh line-by-line re-read of all 19 test bodies against the code under test: L1 read them in session 7 on the same bytes but left no written per-file verdict. Re-read here: the two survivors' code paths, the macOS pin's additions, the guard harness, the three predict_merge LFS / graft tests and the dropped draft tests; the other files rest on the 40 kept and 16 re-run mutants, every one killed or sound except S1 and R7.",
    "The 18 drafts' live GitHub state and every PR or commit the texts name (the claims lens).",
    "The texts' wording (pr_body.txt, commit_body.txt, changelog_entry.txt) beyond where the entry lands: the claims lens. The one test-claim in them checked here: 'no test compares that battery with ci.yml' is TRUE (B1).",
]


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--scratch", required=True)
    parser.add_argument("--status", required=True, choices=("final", "in-progress"))
    args = parser.parse_args(argv)
    s = Path(args.scratch)

    s7 = {m["id"]: m for m in load(s / "mutants" / "results.json")["mutants"]}
    s8 = {}
    for name in ("s8_results_part1.json", "s8_results.json"):
        for m in load(s / "s8_mutants" / name)["mutants"]:
            s8[m["id"]] = m
    keep = load(s / "s8_keep.json")
    ci = load(s / "s8_ci_list_L_run.json")
    clean = load(s / "s8_ci_fail4_clean_main.json")
    battery = load(s / "s8_battery_check.json")
    dryrun = load(s / "s8_battery_dryrun.json")
    dryrun_fail = load(s / "s8_battery_dryrun_fail.json")
    py39 = load(s / "s8_py39_guard_suites.json")
    py312 = load(s / "s8_py312_carried.json")
    flake = load(s / "s8_flake5_L.json")
    pp_suites = load(s / "s8_pp" / "suites.json")
    seq = load(s / "s8_seqsafety" / "result.json")
    land = load(s / "s8_land_main" / "landing_report.json")
    land_pp = load(s / "s8_pp" / "ml_tests" / "landing_report.json")

    ci_rows = {row["suite"]: row for row in ci["rounds"][0]["parallel"]}
    per_file = []
    for rel, draft, ids, host, verdict in FILE_ROWS:
        results = {}
        for mid in ids:
            if mid in s8:
                results[mid] = "%s (session 8)" % s8[mid]["result"]
            elif mid in s7:
                results[mid] = "%s (kept from session 7, bytes unchanged)" % s7[mid]["result"]
        ran = ci_rows[rel]["ran"] if rel in ci_rows else 4
        per_file.append({"file": rel, "draft": draft, "tests_counted": ran, "ran_equals_def_test": True, "mutants": results, "host_dependences": host, "verdict": verdict})

    alone = {row["suite"]: row for row in ci["rounds"][0]["alone"]}
    clean_rows = {row["suite"]: row for row in clean["rounds"][0]["parallel"] + clean["rounds"][0]["alone"]}
    failures = [{"suite": suite, "failing_ids_on_L": len(row["failing_ids"]), "fails_alone_on_clean_main_with_identical_ids": set(row["failing_ids"]) == set(clean_rows[suite]["failing_ids"])} for suite, row in alone.items()]

    out = {
        "carrier": "ml-tests round 2: C = %s (uncommitted, base f9582a74, 64 files; manifest 88bf8351)" % (JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "agent-a89a668e6d43bcee2"),
        "lens": "tests",
        "validator": "L1b (flood-4 session 8, Opus), finishing L1 (session 7) in place",
        "status": args.status,
        "verdict": "SHIP-WITH-FIXES",
        "counts": {"BLOCKER": 0, "MAJOR": 0, "MINOR": len(FINDINGS)},
        "main": land["main_sha"],
        "trees": {
            "L (judged)": land["dest"],
            "clean main": str(JUNIPER / "worktrees" / "juniper-ml--val--flood4r2-ml-tests-r2-tests-s8-clean--20261114-1913--a949d504"),
            "mutation copy (== L on all 64 files)": str(JUNIPER / "worktrees" / "juniper-ml--val--flood4r2-ml-tests-r2-tests-s8-mut--20261114-1913--a949d504"),
            "new main e8c97956": str(JUNIPER / "worktrees" / "juniper-ml--val--flood4r2-ml-tests-r2-tests-s8-e8c9--20261114-1941--e8c97956"),
            "main + ml-propose + carrier": land_pp["dest"],
        },
        "checked": [
            "A: carrier 64/64 == manifest sha256 at start (s8_verify_carrier_start.json) and at the end (s8_verify_carrier_end.json); L's change list == the manifest's 64 paths; 60 byte-identical, the 4 re-derived shared files byte-identical to H3's pull-request tree; the three changed tests are additions only (+23/-0, +1/-0, +227/-0) as the manifest describes; removed lines are re-derived stamps / counts and superset lines only.",
            "B: Ran N == def_test for all 19, nothing after __main__, 0 skipped; 40 session-7 mutants kept on unchanged bytes, 16 re-run, 9 new; dropped draft tests checked against main's code.",
            "C: ci.yml 242 -> 257 (+15, no duplicate, no missing file); the battery (main-verify.yml) by an independent checker and a stub-python dry run of the step; the ci-tools file's lane collected by pytest; list-drift 0/0; wiring-drift 14 OK.",
            "D: HOST_TOOLING_SUITES 12 -> 20, all 9 guard suites on disk listed; D1-D6a re-run (killed / sound); the nine guard suites under CPython 3.9.25 and 3.12.16.",
            "E: F6's two tests killed by their mutants (R5, R6) and unmoved by a real floor raise (R4 expect_pass True/True).",
            "F: main + ml-propose landed by F.5 steps 1-2 + the session-8 changelog helper, then this carrier with --ml-propose-pr 99999 (a stand-in): exit 0; #2558 is main.",
            "G: CI's whole list on L, failures alone on clean main; 5 rounds of the carried suites; pinned pre-commit on 64 files; CodeQL prescreen + shape grep on 59 .py; G-PATH and G-TMP on 40 helpers; both sequence-safety screens on a probe commit.",
        ],
        "not_checked": NOT_CHECKED,
        "findings": FINDINGS,
        "per_file": per_file,
        "mutants": {
            "kept_from_session_7": {"ids": keep["keep"], "evidence": str(s / "mutants" / "results.json"), "why": "every edited file and the suite byte-identical on L (s8_keep.json), none a file main moved since ae801a70; L1's mutation copy holds no leftover mutant (all 18 'before' hashes match)"},
            "re_run_session_8": {mid: s8[mid]["result"] for mid in keep["re_run"] + ["R3s8"] if mid in s8},
            "new_session_8": {mid: s8[mid]["result"] for mid in ("X1c", "X2c", "S1fix", "S1ctl", "R7fix", "R7ctl", "B1")},
            "unanalysed_five": {
                "S1": "SURVIVED: a real gap, finding F1",
                "R7": "SURVIVED: equivalent on today's docs/REFERENCE.md; the fixture assertion meant to pin it is vacuous, finding F2",
                "X0": "PASSES: control, the draft #2481 LFS test as submitted",
                "X1": "PASSES with the scratch's smudge-skip variable removed: '* -filter' alone keeps the smudge from running",
                "X2": "PASSES with the scratch's '* -filter' removed: the skip-smudge variable alone makes the stand-in pass. So the draft's test pinned neither protection, exactly the manifest's reason (carried[2481].fixes[0]); the carried rewrite kills each removal alone (X1c, X2c).",
            },
        },
        "wiring": {
            "ci_yml": {"suite_lines_main": battery["ci_list_lines"]["main"], "suite_lines_L": battery["ci_list_lines"]["landed"], "added": len(battery["ci_added"]), "verdict": "right: each of the 15 once, no duplicate, no missing file; list-drift 0/0; wiring-drift suite OK"},
            "main_verify_battery": {
                "lines_main": battery["battery_lines"]["main"],
                "lines_L": battery["battery_lines"]["landed"],
                "added": len(battery["battery_added"]),
                "lost": len(battery["battery_lost"]),
                "all_fifteen_once": battery["added_suites_all_once"],
                "in_ci_order_among_themselves": battery["added_suites_keep_ci_order_among_themselves"],
                "each_locally_in_ci_order": all(row["locally_in_order"] for row in battery["added_rows"]),
                "out_of_ci_order_main": battery["main_tree"]["battery_out_of_ci_order"],
                "out_of_ci_order_L": battery["landed"]["battery_out_of_ci_order"],
                "bash_n_rc": battery["landed"]["bash_n_rc"],
                "step_shell": battery["landed"]["step_shell"],
                "dry_run": {"lines_reached": dryrun["calls"], "of": dryrun["expected_lines"], "in_order": dryrun["calls_in_order_as_expected"], "exit": dryrun["step_exit"]},
                "dry_run_with_new_line_failing": {"stops_after": dryrun_fail["calls"], "exit": dryrun_fail["step_exit"]},
                "tests_naming_main_verify": "10 suites (182 tests) pass on L and still pass with a new battery line deleted (B1): 'no test compares that battery with ci.yml' is TRUE",
                "verdict": "right: the placement rule puts each of the 15 between ci.yml-ordered neighbours, main's three out-of-order lines are untouched, the step runs all 90 and fails on a failing new suite",
            },
            "ci_tools_file": "ci-ci-tools.yml job test: pull_request on juniper-ci-tools/**, working-directory juniper-ci-tools, python -m pytest (testpaths tests, python_files test_*.py), matrix 3.11-3.14 + 3.15 experimental; collect-only selects its 4 tests (309 total); 4 passed",
            "macos_eight": "right: HOST_TOOLING_SUITES = main's 12 + the 8 guard suites; every tests/test_claude_agent_guard*.py on disk (9) is listed; the pin fails on a removed suite (D1), an unpinned addition (D2), lost trigger coverage (D3), a new unlisted guard suite (D5); CD/REPORT.txt section 5's log lines are the right list (ci.yml + the five carried guard suites as hits; 20 groups; Ran 25/2/2/4/3/4/3/4)",
        },
        "landing": {
            "command": "/opt/miniforge3/envs/JuniperCascor1/bin/python3.14 C/util/ad-hoc/2026-11-14_flood4r2_ml-tests-r2_land.py --carrier C --dest <clean worktree of main> --landing-date 2026-11-15 --out <dir> [--ml-propose-pr N], through runenv.bash",
            "on_main": "a949d504: exit 0, OK, problems []; 257 suites, battery 90, REFERENCE 0.6.70 -> 0.6.71 (header :5 == footer :10021, row :9466 after main's 0.6.70), AGENTS.md 257 / 2026-11-15 in the diff; entry under [Unreleased] / ### Added (:61), [0.11.5] at :116; <ML-PROPOSE-PR> at CHANGELOG.md:78 + three texts",
            "on_main_plus_ml_propose": "a949d504 + ml-propose (F.5 step 1 exit 1, one PROBLEM, the CHANGELOG one; step 2 exit 1, 22 files; the session-8 changelog helper exit 0, its entry at :71 under ### Fixed) + probe 0832627a: exit 0, OK, REFERENCE 0.6.71 -> 0.6.72 (header == footer, row :9469 after :9468), token filled with the stand-in 99999 everywhere; entries under ### Added (:61) and ### Fixed (:116), one heading each; 20 suites / %d tests pass there (the 18 carried, propose 188, wiring drift 14) + the ci-tools file 4" % sum(row["ran"] or 0 for row in pp_suites["rounds"][0]["parallel"]),
            "on_2558": "#2558 is merged (0.11.5 cut on main): see on_main; the entry is never inside [0.11.5]; #2507's tests 20/20 against the real 0.11.5 lines",
            "on_new_main_e8c97956": "main moved during this run (juniper-ml#2569, e8c97956: CHANGELOG.md +20 with a new ### Changed group, one docs/REFERENCE.md line, backup files). Re-landed on a fresh worktree of it: exit %s, last line OK; entry at :61 under [Unreleased] / ### Added, [0.11.5] at :136; REFERENCE 0.6.71 (header == footer, row :9466 after 0.6.70); %d suites / %d tests pass there (the 18 carried, wiring drift, AGENTS.md version drift, battery paths)" % (load(s / "s8_land_e8c9" / "landing_report.json")["problems"] or 0, len(load(s / "s8_e8c9_suites.json")["rounds"][0]["parallel"]), sum(row["ran"] or 0 for row in load(s / "s8_e8c9_suites.json")["rounds"][0]["parallel"])),
        },
        "ci_list": {
            "L": {"suites": len(ci["rounds"][0]["parallel"]), "tests": sum(row["ran"] or 0 for row in ci["rounds"][0]["parallel"]), "interpreter": ci["interpreter"], "wall_secs": ci["total_wall_secs"]},
            "failing_alone_on_L": failures,
            "fifteen_added_wall_secs_serial": round(sum(ci_rows[name]["wall_secs"] for name in battery["ci_added"]), 1),
        },
        "interpreters": {"py39": py39["python"], "py39_all_pass": all(all(rc == 0 for rc in row["rc"]) for row in py39["summary"]), "py312": py312["python"], "py312_all_pass": all(all(rc == 0 for rc in row["rc"]) for row in py312["summary"])},
        "flakes": {"rounds": len(flake["rounds"]), "failures": sum(1 for item in flake["rounds"] for row in item["parallel"] if not row["ok"])},
        "sequence_safety": {"probe_commit": seq["probe_commit"], "main": seq["main"], "adds": seq["adds"], "symbol_exit": seq["symbol_exit"], "docs_exit": seq["docs_exit"], "summary": "symbol-loss 58 files 0 findings; docs-additions 8 small-deletion warnings 0 failures; no Allow-Symbol-Loss / Allow-Docs-Rewrite value needed"},
    }
    with open(s / "findings.json", "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
        fh.write("\n")
    print("findings.json written: status=%s verdict=%s counts=%s" % (out["status"], out["verdict"], out["counts"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
