"""
The session-8 tests-lens mutation run for the ml-tests carrier: the predecessor's mutants whose bytes moved, plus new ones.

It loads the session-7 driver (util/ad-hoc/2026-11-12_flood4r2_val_ml-tests-r2-tests_mutants.py) for its audited
pieces -- the exact-text edit, the suite runner with the six Sentry variables empty and a dead session bus -- and
runs, in --tree (the validator's own mutation copy, never the carrier):

- the 16 session-7 mutants whose target or suite inputs main moved (by id, unchanged), with R3 re-pointed from the
  0.11.4 Version cell to the 0.11.5 one main now carries (R3s8);
- X1c / X2c: the session-7 draft-claim edits (each LFS protection of the scratch removed alone) against the CARRIED
  tests/test_predict_merge_scratch_edges.py, which must kill both;
- S1fix / R7fix: the two session-7 survivors with the validator's proposed test fix applied (must be killed), and
  S1ctl / R7ctl: the fix alone on unmutated code (must pass); each fix is also written to --proposed as a unified
  diff that applies with `patch -p1` on the landed tree;
- B1: one of the fifteen new Regression Battery lines deleted from main-verify.yml, with every suite that names
  main-verify.yml run (expected to PASS: the carrier's texts say no test compares the battery with ci.yml).

Every touched file's sha256 is written to --progress before the first mutant, every edit is undone in a
``finally:`` block, and the hashes are compared after EVERY mutant (a mismatch stops the run, exit 3).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent L1b, flood-4 session 8)
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_val_ml-tests-r2-tests_mutants.py (the session-7 driver it reuses)

Usage:
    python3 <this file> --tree <mutation copy> --out <dir> --progress <PROGRESS.txt> --proposed <dir> [--only ID ...]
"""

import argparse
import difflib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

S7_DRIVER = Path(__file__).resolve().parent / "2026-11-12_flood4r2_val_ml-tests-r2-tests_mutants.py"
RERUN_IDS = ("R1", "R2", "R4", "R5", "R6", "R7", "H5", "D1", "D2", "D3", "D4", "D5", "D6a", "D6b", "D6c")
MAIN_VERIFY_SUITES = (
    "tests/test_ci_precommit_g4.py",
    "tests/test_ci_tools_drift.py",
    "tests/test_main_verify_battery_paths.py",
    "tests/test_main_verify_catchup_base.py",
    "tests/test_main_verify_notify_dedup.py",
    "tests/test_main_verify_screen_verdicts.py",
    "tests/test_main_verify_workflow_guard.py",
    "tests/test_pr_budget_alarm.py",
    "tests/test_predict_merge.py",
    "tests/test_release_train_registry.py",
)
CASCOR_TEST = "tests/test_cascor_eval_zero_and_enabled.py"
EXTRAS_TEST = "tests/test_pyproject_extras.py"
S1_FIX_OLD = '                self.assertEqual(held["f1"], METRICS_FINAL_TEST_SPLIT["eval_metrics"]["final"]["f1"])\n\n    def test_held_out_is_the_exact_split_test'
S1_FIX_NEW = (
    '                self.assertEqual(held["f1"], METRICS_FINAL_TEST_SPLIT["eval_metrics"]["final"]["f1"])\n'
    '                in_loop = ss.cascor_eval_blocks(body)["eval_scalars_in_loop"]\n'
    '                self.assertIsNone(in_loop["absent"], "only enabled is False turns the in-loop scalars off")\n'
    '                self.assertEqual(in_loop["f1"], METRICS_FINAL_TEST_SPLIT["f1"])\n'
    "\n    def test_held_out_is_the_exact_split_test"
)
R7_FIX_EDITS = (
    ('| 9.9.x      | >=9.9.1      |\\n\\n### Service Ports\\n"', '| 9.9.x      | >=9.9.1      |\\n\\n### Service Ports\\n\\n| Service | Port |\\n|---------|------|\\n| 9.9.x   | 8100 |\\n"'),
    ('        self.assertNotIn("Service Ports", rows)\n', '        self.assertNotIn("Service", rows, "a later table is not a row of the matrix")\n'),
)


def load_s7():
    spec = importlib.util.spec_from_file_location("flood4r2_val_ml_tests_r2_tests_mutants_s7", S7_DRIVER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def build(s7):
    by_id = {mutant["id"]: mutant for mutant in s7.MUTANTS}
    chosen = [dict(by_id[name], origin="session 7, re-run") for name in RERUN_IDS]
    edit = s7.edit
    s1 = by_id["S1"]["edits"][0]
    r7 = by_id["R7"]["edits"][0]
    s1_fix = edit(CASCOR_TEST, S1_FIX_OLD, S1_FIX_NEW)
    r7_fix = [edit(EXTRAS_TEST, old, new) for old, new in R7_FIX_EDITS]
    chosen += [
        {"id": "R3s8", "origin": "session 7 R3, re-pointed to 0.11.5", "kind": "product", "suite": EXTRAS_TEST, "claim": "one Version cell", "edits": [edit(s7.REF, "| **Version**            | `0.11.5`     |\n", "| **Version**            | `0.11.5`     |\n| **Version**            | `0.11.5`     |\n")]},
        {"id": "X1c", "origin": "session 7 X1's edit, against the carried rewrite", "kind": "product", "suite": "tests/test_predict_merge_scratch_edges.py", "claim": "the carried rewrite pins the smudge-skip variable alone", "edits": [edit(s7.PM, '    env["GIT_LFS_SKIP_SMUDGE"] = "1"\n', "")]},
        {"id": "X2c", "origin": "session 7 X2's edit, against the carried rewrite", "kind": "product", "suite": "tests/test_predict_merge_scratch_edges.py", "claim": "the carried rewrite pins the scratch's * -filter alone", "edits": [edit(s7.PM, '        (clone / ".git" / "info" / "attributes").write_text("* -filter\\n", encoding="utf-8")\n', "")]},
        {"id": "S1fix", "origin": "S1 survivor + proposed fix", "kind": "product", "suite": CASCOR_TEST, "claim": "with the fix, enabled 0 keeps the in-loop scalars (S1 killed)", "edits": [s1, s1_fix]},
        {"id": "S1ctl", "origin": "proposed fix alone", "kind": "fix-control", "suite": CASCOR_TEST, "claim": "the fix passes on unmutated code", "edits": [s1_fix]},
        {"id": "R7fix", "origin": "R7 survivor + proposed fix", "kind": "harness-parser", "suite": EXTRAS_TEST, "claim": "with the fix, a later table after the matrix is not a row (R7 killed)", "edits": [r7, *r7_fix]},
        {"id": "R7ctl", "origin": "proposed fix alone", "kind": "fix-control", "suite": EXTRAS_TEST, "claim": "the fix passes on unmutated code", "edits": list(r7_fix)},
        {"id": "B1", "origin": "session 8 battery claim", "kind": "claim-passes", "suite": list(MAIN_VERIFY_SUITES), "claim": "no test compares the battery with ci.yml: a deleted new battery line fails none of the suites that name main-verify.yml", "edits": [edit(".github/workflows/main-verify.yml", "          python3 -m unittest -v " + CASCOR_TEST + "\n", "")]},
    ]
    return chosen


def run_many(s7, tree, suites, timeout):
    argv = [sys.executable, "-B", "-m", "unittest", "-v", *suites]
    try:
        proc = subprocess.run(argv, cwd=str(tree), capture_output=True, text=True, timeout=timeout, check=False, env=s7.child_env())
        rc, text = proc.returncode, proc.stdout + proc.stderr
    except subprocess.TimeoutExpired as exc:
        rc, text = 124, "TIMEOUT after %ss\n%s%s" % (timeout, exc.stdout or "", exc.stderr or "")
    ran = s7.RAN_RE.findall(text)
    ids = sorted({"%s %s (%s)" % (m.group("kind"), m.group("name"), m.group("where")) for m in s7.ID_RE.finditer(text)})
    return rc, text, (int(ran[-1]) if ran else None), ids


def write_proposed(tree, proposed, name, edits):
    by_path = {}
    for item in edits:
        by_path.setdefault(item["path"], []).append(item)
    chunks = []
    for rel, items in by_path.items():
        original = (Path(tree) / rel).read_text(encoding="utf-8")
        changed = original
        for item in items:
            if changed.count(item["old"]) != 1:
                raise SystemExit("%s: old text occurs %d times in %s" % (name, changed.count(item["old"]), rel))
            changed = changed.replace(item["old"], item["new"], 1)
        chunks.append("".join(difflib.unified_diff(original.splitlines(keepends=True), changed.splitlines(keepends=True), "a/" + rel, "b/" + rel)))
    Path(proposed).mkdir(parents=True, exist_ok=True)
    target = Path(proposed) / (name + ".diff")
    target.write_text("".join(chunks), encoding="utf-8")
    return str(target)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--progress", required=True)
    parser.add_argument("--proposed", required=True)
    parser.add_argument("--only", nargs="*")
    parser.add_argument("--timeout", type=int, default=900)
    args = parser.parse_args(argv)

    s7 = load_s7()
    tree, out = Path(args.tree).resolve(), Path(args.out)
    if "-s8-mut--" not in tree.name:
        raise SystemExit("--tree must be the validator's own session-8 mutation copy, got %s" % tree)
    out.mkdir(parents=True, exist_ok=True)
    chosen = [m for m in build(s7) if not args.only or m["id"] in args.only]
    proposals = {
        "S1_in_loop_enabled_zero": write_proposed(tree, args.proposed, "S1_in_loop_enabled_zero", [m for m in chosen if m["id"] == "S1ctl"][0]["edits"]) if any(m["id"] == "S1ctl" for m in chosen) else None,
        "R7_later_table_not_a_row": write_proposed(tree, args.proposed, "R7_later_table_not_a_row", [m for m in chosen if m["id"] == "R7ctl"][0]["edits"]) if any(m["id"] == "R7ctl" for m in chosen) else None,
    }

    touched = sorted({e["path"] for m in chosen for e in m["edits"]})
    before = {path: s7.sha256_of(tree / path) for path in touched}
    with open(args.progress, "a", encoding="utf-8") as fh:
        fh.write("%s S8 MUTATION RUN START in %s (%d mutants: %s). sha256 BEFORE of every file it may touch: %s\n" % (s7.stamp(), tree, len(chosen), " ".join(m["id"] for m in chosen), json.dumps(before, sort_keys=True)))

    results = {"tree": str(tree), "interpreter": "%s (%s)" % (sys.executable, sys.version.split()[0]), "before": before, "proposed": proposals, "mutants": []}
    for mutant in chosen:
        row = {key: mutant[key] for key in ("id", "origin", "kind", "suite", "claim")}
        row["edits"] = [{k: v for k, v in e.items() if k != "text"} for e in mutant["edits"]]
        originals = {}
        created = []
        try:
            problem = None
            for e in mutant["edits"]:
                target = tree / e["path"]
                if e.get("create"):
                    if target.exists():
                        problem = "%s already exists" % e["path"]
                        break
                    created.append(target)
                    target.write_bytes(e["text"].encode("utf-8"))
                    continue
                originals.setdefault(target, target.read_bytes())
                current = target.read_bytes()
                old = e["old"].encode("utf-8")
                if current.count(old) != 1:
                    problem = "%s: old text occurs %d times" % (e["path"], current.count(old))
                    break
                target.write_bytes(current.replace(old, e["new"].encode("utf-8"), 1))
            if problem:
                row.update({"result": "SPEC-ERROR", "detail": problem})
            else:
                suites = mutant["suite"] if isinstance(mutant["suite"], list) else [mutant["suite"]]
                if len(suites) == 1:
                    rc, text, ran, ids = s7.run_suite(tree, suites[0], args.timeout)
                else:
                    rc, text, ran, ids = run_many(s7, tree, suites, args.timeout)
                (out / ("s8mut_%s.log" % mutant["id"])).write_text(text, encoding="utf-8")
                row.update({"rc": rc, "ran": ran, "failing_ids": ids, "tail": text.strip().splitlines()[-3:]})
                if mutant["kind"] in ("fix-control", "claim-passes"):
                    row["result"] = "passes (as expected)" if rc == 0 else "FAILS"
                elif mutant["kind"] == "harness":
                    row["result"] = "test fails (sound)" if rc != 0 else "TEST STILL PASSES (vacuous?)"
                else:
                    row["result"] = "killed" if rc != 0 else "SURVIVED"
                if mutant.get("expect_pass"):
                    row["expect_pass"] = {name: (name + " (") in text and not any(name in failing for failing in ids) for name in mutant["expect_pass"]}
        finally:
            for target, data in originals.items():
                target.write_bytes(data)
            for target in created:
                if target.exists():
                    target.unlink()
        after ={path: s7.sha256_of(tree / path) for path in touched}
        row["restored"] = after == before
        results["mutants"].append(row)
        print("%-6s %-15s %-24s restored=%s ran=%s | %s" % (row["id"], row["kind"], row.get("result"), row["restored"], row.get("ran"), "; ".join(row.get("failing_ids", [])[:3])[:220] or row.get("detail", "")), flush=True)
        with open(out / "s8_results.json", "w", encoding="utf-8") as fh:
            json.dump(results, fh, indent=1)
            fh.write("\n")
        if not row["restored"]:
            with open(args.progress, "a", encoding="utf-8") as fh:
                fh.write("%s S8 MUTATION RUN STOPPED: after %s a hash differs: %s\n" % (s7.stamp(), row["id"], json.dumps(after, sort_keys=True)))
            return 3

    after = {path: s7.sha256_of(tree / path) for path in touched}
    with open(args.progress, "a", encoding="utf-8") as fh:
        fh.write("%s S8 MUTATION RUN END: %d mutants; every touched file restored=%s (sha256 after == before); results %s\n" % (s7.stamp(), len(chosen), after == before, out / "s8_results.json"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
