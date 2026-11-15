#!/usr/bin/env python3
"""
Re-run a named sample of the ml-propose carrier's mutants on a rebuilt tree, and compare with the full run's record.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (finishing round 3 of the ml-propose carrier, flood-4 session 6)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14;
         util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3_mutation_check.py (the mutants and the machinery, read from it)

WHY THIS EXISTS
Round 3's full mutation run (59 mutants) was made on the carrier's base of that day. The carrier was then rebuilt
onto a newer main, with util/release_train/propose.py and tests/test_release_train_propose.py copied byte for
byte. The full run stands for those two files, so it is cited, not repeated. What a rebuild can still break is the
harness around them: the tree the suite runs in (the live-file control reads the rebuilt docs/REFERENCE.md), the
interpreter, the test selection. This script shows the harness still kills on the rebuilt tree:

* it refuses unless both files have the sha256 the full run recorded;
* it runs the three controls (the whole suite, round 2's selection, the live-file control alone), which must pass;
* it swaps main's propose.py in whole: the suite must fail on the code the new tests are written for. With
  --previous-propose it does the same with the previous build's propose.py, which this build's added assertions
  must fail on;
* it applies each sampled mutant with the same selectors the full run used, restores propose.py in a ``finally``
  block, compares its sha256 after EVERY mutant, and reports whether the result and the failing tests equal the
  full run's.

Everything happens in a scratch copy (``--tree``: a fresh archive of HEAD with the carrier's five changed files
copied in), never in the carrier. The copy holds a pyproject.toml with a [project] table, so it must be OUTSIDE
every juniper-ml tmp/. No child process may reach the error-reporting service: the six DSN variables are set to
the empty string for every child.

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3b_mutant_sample.py --tree <scratch copy> --out <dir>
        --full-run <the full run's mutation_results.json> --sample r2:V1 --sample own:S3 --sample live:LR2 ...
        [--previous-propose <the previous build's propose.py>] [--python <interpreter>]
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess  # nosec B404 - fixed argv: read-only plumbing in this script's own worktree
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
R3_SCRIPT = Path(__file__).with_name("2026-11-12_flood4r2_ml-propose-r3_mutation_check.py")
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")


def load_r3():
    spec = importlib.util.spec_from_file_location("flood4r2_ml_propose_r3_mutation_check", R3_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--full-run", required=True, type=Path)
    parser.add_argument("--sample", required=True, action="append", metavar="GROUP:ID")
    parser.add_argument("--previous-propose", type=Path, help="the previous build's propose.py, swapped in whole: the assertions this build added must fail on it")
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()
    if any(part == "tmp" for part in args.tree.resolve().parts) and "juniper-ml" in args.tree.resolve().parts:
        raise SystemExit("--tree holds a pyproject.toml with a [project] table: it must be outside every juniper-ml tmp/")
    os.environ.update(dict.fromkeys(SENTRY_DSN_NAMES, ""))
    args.out.mkdir(parents=True, exist_ok=True)

    r3 = load_r3()
    full = json.loads(args.full_run.read_text(encoding="utf-8"))
    full_rows = {(row["group"], row["id"]): row for row in full["mutants"]}
    carrier_mutants, selection = r3.r2_mutants()
    groups = {
        "r2": ({ident: (what, old, new) for ident, what, old, new in carrier_mutants}, tuple(selection)),
        "own": ({ident: (what, old, new) for ident, what, old, new in r3.OWN_MUTANTS}, (r3.SUITE,)),
        "live": ({ident: (what, old, new) for ident, what, old, new in r3.LIVE_MUTANTS}, (r3.LIVE_CONTROL,)),
    }

    here = {"propose": r3.sha256(ROOT / r3.TARGET_REL), "tests": r3.sha256(ROOT / r3.SUITE)}
    recorded = {"propose": full["target_sha256"], "tests": full["test_file_sha256"]}
    if here != recorded:
        raise SystemExit(f"the full run is for other bytes: here {here}, recorded {recorded}. Re-run all the mutants instead of a sample.")

    r3.build_tree(args.tree)
    target = args.tree / r3.TARGET_REL
    original = target.read_bytes()
    original_sha = r3.sha256(target)
    text = original.decode("utf-8")
    results = {
        "tree": str(args.tree),
        "head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip(),  # nosec B603 B607
        "python": args.python,
        "target_sha256": original_sha,
        "test_file_sha256": r3.sha256(args.tree / r3.SUITE),
        "bytes_equal_the_full_runs": here == recorded and original_sha == recorded["propose"],
        "full_run": str(args.full_run),
        "full_run_summary": full.get("summary"),
        "control_whole_suite": r3.run(args.python, args.tree, (r3.SUITE,), args.out / "control_whole_suite.log"),
        "control_selection": r3.run(args.python, args.tree, tuple(selection), args.out / "control_selection.log"),
        "control_live": r3.run(args.python, args.tree, (r3.LIVE_CONTROL,), args.out / "control_live.log"),
    }
    main_propose = subprocess.run(["git", "show", f"HEAD:{r3.TARGET_REL}"], cwd=ROOT, capture_output=True, check=True).stdout  # nosec B603 B607
    swaps = [("tests_on_main_propose", main_propose, "tests_on_main_propose")]
    if args.previous_propose is not None:
        swaps.append(("tests_on_previous_propose", args.previous_propose.read_bytes(), "tests_on_round2_propose"))
    for label, swapped_in, full_label in swaps:
        try:
            target.write_bytes(swapped_in)
            results[label] = r3.run(args.python, args.tree, (r3.SUITE,), args.out / f"{label}.log")
        finally:
            target.write_bytes(original)
        results[label]["swapped_in_sha256"] = hashlib.sha256(swapped_in).hexdigest()
        results[label]["restored"] = r3.sha256(target) == original_sha
        previous = full.get(full_label, {})
        results[label]["same_as_full_run"] = (results[label]["verdict"], results[label]["failing_tests"]) == (previous.get("verdict"), previous.get("failing_tests"))

    rows = []
    for item in args.sample:
        group, _, ident = item.partition(":")
        if group not in groups or ident not in groups[group][0]:
            raise SystemExit(f"--sample wants <group>:<id> from the full run, got {item!r}")
        what, old, new = groups[group][0][ident]
        selectors = groups[group][1]
        row = {"group": group, "id": ident, "what": what, "old": old, "new": new, "occurrences": text.count(old), "run_against": list(selectors)}
        if row["occurrences"] == 1:
            try:
                target.write_text(text.replace(old, new), encoding="utf-8")
                row.update(r3.run(args.python, args.tree, selectors, args.out / f"mut_{group}_{ident}.log"))
            finally:
                target.write_bytes(original)
            row["restored"] = r3.sha256(target) == original_sha
            row["result"] = "killed" if row["rc"] == 1 else ("survived" if row["rc"] == 0 else f"error: rc {row['rc']}")
        else:
            row["result"] = "NOT-APPLIED"
        before = full_rows.get((group, ident), {})
        row["full_run_result"] = before.get("result")
        row["same_as_full_run"] = (row["result"], row.get("failing_tests")) == (before.get("result"), before.get("failing_tests"))
        rows.append(row)
        results["mutants"] = rows
        (args.out / "mutant_sample_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
        print(group, ident, row["result"], row.get("verdict"), "same as the full run:", row["same_as_full_run"], row.get("failing_tests", [])[:2])
    r3.clear_caches(args.tree)
    controls_ok = all(results[key]["rc"] == 0 for key in ("control_whole_suite", "control_selection", "control_live"))
    results["summary"] = {
        "controls_ok": controls_ok,
        "controls_ran": {key: results[key]["ran"] for key in ("control_whole_suite", "control_selection", "control_live")},
        "tests_fail_on_main_propose": results["tests_on_main_propose"]["rc"] == 1,
        "swapped_in_runs_equal_the_full_runs": {label: results[label]["same_as_full_run"] and results[label]["restored"] for label, _bytes, _full in swaps},
        "sampled": len(rows),
        "killed": sum(row["result"] == "killed" for row in rows),
        "every_mutant_restored": all(row.get("restored", False) for row in rows),
        "every_result_equals_the_full_runs": all(row["same_as_full_run"] for row in rows),
        "target_restored": r3.sha256(target) == original_sha,
        "carrier_untouched": {"propose": r3.sha256(ROOT / r3.TARGET_REL) == recorded["propose"], "tests": r3.sha256(ROOT / r3.SUITE) == recorded["tests"]},
    }
    (args.out / "mutant_sample_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results["summary"], indent=2))
    summary = results["summary"]
    good = controls_ok and summary["tests_fail_on_main_propose"] and all(summary["swapped_in_runs_equal_the_full_runs"].values()) and summary["every_mutant_restored"] and summary["every_result_equals_the_full_runs"] and summary["target_restored"] and all(summary["carrier_untouched"].values())
    return 0 if good else 1


if __name__ == "__main__":
    sys.exit(main())
