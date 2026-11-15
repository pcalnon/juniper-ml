#!/usr/bin/env python3
"""
Mutation-check round 3 of the ml-propose carrier in a scratch copy: round 2's mutants, the final check's, and F2's.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (round 3 of the ml-propose carrier, flood-4 session 5)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14;
         util/ad-hoc/2026-11-08_flood4r2_ml-propose_mutation_check.py (round 2's 38 mutants, read from it)

WHY THIS EXISTS
The final check of round 2 found five behaviour-changing mutants of the co-change checklist that survived the
suite (its F3: S3 S5 S6 S7 S13), and a live-file control whose line count broke on a paragraph break (its F2).
Round 3 adds the tests. This script shows each one binds:

* ``r2``   -- round 2's 38 mutants, read from that round's script so the list cannot drift;
* ``own``  -- the final-check validator's 13 (S1-S13). Ten must die. Three are expected to survive and are
  listed with the reason (S8 and S11 are equivalent mutants, S12 is a disclosed low-value edge);
* ``live`` -- two mutants of each of the four writers, run against the live-file control ALONE
  (test_helpers_find_every_site_in_the_live_reference), so the rewritten control is shown to be non-vacuous.

It also runs the suite against main's propose.py and against round 2's, swapped in whole: the new tests must fail
on the code they are written for.

Everything happens in a scratch copy (``--tree``: a `git archive HEAD` extraction with this worktree's five
changed files copied in), never in the carrier, so the carrier's files are not touched while other checks run.
The copy holds a pyproject.toml with a [project] table, so it must be OUTSIDE every juniper-ml tmp/. Each run is a
fresh interpreter with ``-B``; the ``__pycache__`` beside propose.py and beside the tests is deleted first;
propose.py is restored byte for byte and its sha256 compared after every mutant.

With --override and --mutants-json the same machinery checks a VARIANT of the carrier's code (an open question's
proposed change, kept in the scratch directory and never in the carrier) against its own mutant list.

Usage:
    python3 <this> --tree <scratch copy, outside any juniper-ml tmp/> --out <scratch>/mut
                   --main-propose <main's propose.py> --r2-propose <round 2's propose.py> [--python <interpreter>]
    python3 <this> --tree <scratch copy> --out <dir> --override <repo-relative file>=<variant file> [--override ...]
                   --mutants-json <[[id, what, old, new], ...]>
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import re
import shutil
import subprocess  # nosec B404 - fixed argv: git archive in this script's own worktree, and child interpreters
import sys
import tarfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
R2_SCRIPT = Path(__file__).with_name("2026-11-08_flood4r2_ml-propose_mutation_check.py")
SUITE = "tests/test_release_train_propose.py"
TARGET_REL = "util/release_train/propose.py"
CARRIER_FILES = (
    "CHANGELOG.md",
    "docs/REFERENCE.md",
    "notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md",
    SUITE,
    TARGET_REL,
)
LIVE_CONTROL = "tests.test_release_train_propose.ReferenceCompatHelperTest.test_helpers_find_every_site_in_the_live_reference"

#: The final-check validator's mutants (its 2026-11-11_flood4r2_val_ml-propose-final_mutants.py), verbatim.
OWN_MUTANTS = (
    ("S1", "the clause note names the release, not the series", '    report["version"] = version\n', '    report["version"] = series\n'),
    ("S2", "the clause note only when the clause was EDITED (a current clause is not renamed)", '        if report.get("recurrence") == "edited":', '        if report.get("recurrence") in ("edited", "current"):'),
    ("S3", "the previous-row note only on a NEW series row (not an in-place edit)", '        if report.get("matrix_row") == "added":\n            notes.append(', '        if report.get("matrix_row") in ("added", "edited"):\n            notes.append('),
    ("S4", "the REVIEW line on the meta's own bump even when nothing moved", "    if meta_bump or done:\n        notes = [", "    if done:\n        notes = ["),
    ("S5", "a sub-package's unrenderable row is REQUIRED only when its pin moved", '(key == "matrix_row" and pins_moved and report.get(key) == "unexpected")', '(key == "matrix_row" and report.get(key) == "unexpected")'),
    ("S6", "the in-place note only when the row was edited", '        if report.get("matrix_row") == "edited":\n            notes.append(', '        if report.get("matrix_row") in ("edited", "current"):\n            notes.append('),
    ("S7", "the replaced-pins note follows recurrence_moved, not the clause's mere presence", '        if report.get("recurrence_moved"):', '        if report.get("recurrence_old"):'),
    ("S8", "an unreadable REFERENCE is REQUIRED on the meta's own bump only", "        elif entry.pypi_name == notes_render.META_PACKAGE:\n            reference_compat = _reference_compat_report(unreadable=True)", "        else:\n            reference_compat = _reference_compat_report(unreadable=True)"),
    ("S9", "the REFERENCE edit is appended only when the text changed", "        if ref_text is not None and ref_new != ref_text:\n            prop.edits.append(FileEdit(path=_REFERENCE_EXTRAS_REL", "        if ref_text is not None:\n            prop.edits.append(FileEdit(path=_REFERENCE_EXTRAS_REL"),
    ("S10", "the included line names a new row by its series", '            done.append(f"a new `{series}` matrix row (the older rows are not touched)")', '            done.append("a new matrix row (the older rows are not touched)")'),
    ("S11", "the clause regex refuses a two-part version tail (lookbehind)", '_REFERENCE_SETS_THEM = re.compile(r"(?<![0-9.])(\\d+\\.\\d+\\.\\d+) sets them to (', '_REFERENCE_SETS_THEM = re.compile(r"(\\d+\\.\\d+\\.\\d+) sets them to ('),
    ("S12", "the matrix search stops at the first non-table line", '            while j < len(lines) and lines[j].startswith("|"):', "            while j < len(lines) and lines[j].strip():"),
    ("S13", "a sub-package's moved pin that cannot reach its row is REQUIRED", ' or (key == "matrix_row" and pins_moved and report.get(key) == "unexpected")]', "]"),
)
#: Mutants the suite is NOT expected to kill, with the reason. Anything else that survives fails this script.
EXPECTED_SURVIVORS = {
    "S8": "equivalent: a sub-package's unreadable report owes nothing and has nothing done, so it yields no checklist line either way",
    "S11": "equivalent for every N.N.N version (round 2's CM3): the lookbehind only refuses a version that follows a digit or a dot",
    "S12": "disclosed low-value edge: differs only for a non-table, non-blank line directly under the matrix, which GitHub renders as a table row anyway",
}
#: Two mutants per writer, run against the live-file control alone: an anchor that stops matching, and a no-op write.
LIVE_MUTANTS = (
    ("LV1", "set_reference_version_cell: the cell anchor stops matching", '        if len(raw) < 4 or raw[1].strip() != "**Version**":', '        if len(raw) < 4 or raw[1].strip() != "**Release**":'),
    ("LV2", "set_reference_version_cell: a no-op write", "    raw[2] = _fit_cell(raw[2], f\"`{new_version}`\")", "    raw[2] = raw[2] + \"\""),
    ("LD1", "set_reference_declares_version: the sentence anchor stops matching", r"( declares the following pins\.)", r"( declares these pins\.)"),
    ("LD2", "set_reference_declares_version: a no-op write", "    return text[: m.start(2)] + new_version + text[m.end(2) :], m.group(2)", "    return text, m.group(2)"),
    ("LR1", "set_reference_matrix_row: the section anchor stops matching", r'_REFERENCE_COMPAT_HEADING = re.compile(r"^#{2,4}\s+Ecosystem Compatibility\s*$"', r'_REFERENCE_COMPAT_HEADING = re.compile(r"^#{2,4}\s+Ecosystem Compat Matrix\s*$"'),
    ("LR2", "set_reference_matrix_row: reports a row it did not add", '    return "".join(lines), "added"', '    return text, "added"'),
    ("LC1", "set_reference_recurrence_clause: the clause anchor stops matching", r"(\d+\.\d+\.\d+) sets them to (", r"(\d+\.\d+\.\d+) sets them at ("),
    ("LC2", "set_reference_recurrence_clause: a no-op write", '    return text[: m.start()] + f"{new_version} sets them to {_join_backticked(pins)}" + text[m.end() :], old_pins', "    return text, old_pins"),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_tree(tree: Path) -> None:
    """A `git archive HEAD` extraction with this worktree's five changed files copied in (HEAD is their base)."""
    if tree.exists():
        shutil.rmtree(tree)
    archive = subprocess.run(["git", "archive", "--format=tar", "HEAD"], cwd=REPO, capture_output=True, check=True)  # nosec B603 B607
    tree.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
        tar.extractall(tree, filter="data")
    for rel in CARRIER_FILES:
        shutil.copyfile(REPO / rel, tree / rel)


def r2_mutants() -> tuple:
    """Round 2's MUTANTS tuple, read from that round's script (id, helper, old, new)."""
    spec = importlib.util.spec_from_file_location("flood4r2_ml_propose_r2_mutation_check", R2_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.MUTANTS, module.SELECTION


def clear_caches(tree: Path) -> None:
    for cache in (tree / "util" / "release_train" / "__pycache__", tree / "tests" / "__pycache__"):
        if cache.is_dir():
            shutil.rmtree(cache)


def run(python: str, tree: Path, selectors: tuple, log: Path) -> dict:
    clear_caches(tree)
    done = subprocess.run([python, "-B", "-m", "unittest", *selectors], cwd=tree, capture_output=True, text=True, check=False, timeout=900)  # nosec B603
    output = done.stdout + done.stderr
    log.write_text(output[-30000:], encoding="utf-8")
    ran = re.search(r"^Ran (\d+) tests?", output, re.MULTILINE)
    verdict = re.search(r"^(OK|FAILED.*)$", output, re.MULTILINE)
    failing = sorted(set(re.findall(r"^(FAIL|ERROR): (test_\w+) \(([\w.]+)\)", output, re.MULTILINE)))
    return {
        "rc": done.returncode,
        "ran": int(ran.group(1)) if ran else None,
        "verdict": verdict.group(1) if verdict else None,
        "failing_tests": sorted({f"{owner(cls, name)}.{name}" for _, name, cls in failing}),
        "kinds": sorted({kind for kind, _, _ in failing}),
    }


def owner(dotted: str, name: str) -> str:
    """The test's class from unittest's ``(module.Class.test)`` (3.11+) or ``(module.Class)`` header."""
    parts = dotted.split(".")
    if parts[-1] == name:
        parts = parts[:-1]
    return parts[-1]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--tree", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--main-propose", type=Path, help="main's propose.py, swapped in whole: the suite must fail on it")
    parser.add_argument("--r2-propose", type=Path, help="round 2's propose.py, swapped in whole")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--override", action="append", default=[], metavar="REL=PATH", help="after building the tree, replace this file with PATH (a variant under study)")
    parser.add_argument("--mutants-json", type=Path, help="run ONLY these mutants, [[id, what, old, new], ...], each against the whole suite, instead of the built-in groups")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    build_tree(args.tree)
    for item in args.override:
        rel, _, source = item.partition("=")
        if rel not in CARRIER_FILES or not Path(source).is_file():
            raise SystemExit(f"--override wants one of {CARRIER_FILES}=<existing file>, got {item!r}")
        shutil.copyfile(source, args.tree / rel)
    target = args.tree / TARGET_REL
    original = target.read_bytes()
    original_sha = sha256(target)
    text = original.decode("utf-8")
    carrier_mutants, selection = r2_mutants()
    results = {
        "tree": str(args.tree),
        "python": args.python,
        "overrides": args.override,
        "target_sha256": original_sha,
        "test_file_sha256": sha256(args.tree / SUITE),
        "selection": list(selection),
        "control_whole_suite": run(args.python, args.tree, (SUITE,), args.out / "control_whole_suite.log"),
        "control_selection": run(args.python, args.tree, tuple(selection), args.out / "control_selection.log"),
        "control_live": run(args.python, args.tree, (LIVE_CONTROL,), args.out / "control_live.log"),
    }
    for label, swap in (("tests_on_main_propose", args.main_propose), ("tests_on_round2_propose", args.r2_propose)):
        if swap is None:
            continue
        try:
            target.write_bytes(swap.read_bytes())
            results[label] = dict(run(args.python, args.tree, (SUITE,), args.out / f"{label}.log"), swapped_in_sha256=sha256(swap))
        finally:
            target.write_bytes(original)
        results[label]["restored"] = sha256(target) == original_sha
    if args.mutants_json is not None:
        groups = (("extra", [tuple(item) for item in json.loads(args.mutants_json.read_text(encoding="utf-8"))], (SUITE,)),)
    else:
        groups = (
            ("r2", [(ident, what, old, new) for ident, what, old, new in carrier_mutants], tuple(selection)),
            ("own", list(OWN_MUTANTS), (SUITE,)),
            ("live", list(LIVE_MUTANTS), (LIVE_CONTROL,)),
        )
    rows = []
    for group, mutants, selectors in groups:
        for ident, what, old, new in mutants:
            row = {"group": group, "id": ident, "what": what, "old": old, "new": new, "occurrences": text.count(old), "run_against": list(selectors)}
            if row["occurrences"] == 1:
                try:
                    target.write_text(text.replace(old, new), encoding="utf-8")
                    row.update(run(args.python, args.tree, selectors, args.out / f"mut_{group}_{ident}.log"))
                finally:
                    target.write_bytes(original)
                row["restored"] = sha256(target) == original_sha
                row["result"] = "killed" if row["rc"] == 1 else ("survived" if row["rc"] == 0 else f"error: rc {row['rc']}")
            else:
                row["result"] = "NOT-APPLIED"
            if ident in EXPECTED_SURVIVORS:
                row["expected_survivor"] = EXPECTED_SURVIVORS[ident]
            rows.append(row)
            results["mutants"] = rows
            (args.out / "mutation_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
            print(group, ident, row["result"], row.get("verdict"), row.get("failing_tests", [])[:3])
    clear_caches(args.tree)
    controls_ok = all(results[key]["rc"] == 0 for key in ("control_whole_suite", "control_selection", "control_live"))
    unexpected = [row["id"] for row in rows if (row["result"] != "killed") != (row["id"] in EXPECTED_SURVIVORS) or row["result"] not in ("killed", "survived") or not row.get("restored", False)]
    results["summary"] = {
        "controls_ok": controls_ok,
        "killed": sum(row["result"] == "killed" for row in rows),
        "survived": [row["id"] for row in rows if row["result"] == "survived"],
        "not_as_expected": unexpected,
        "by_group": {group: {"mutants": sum(r["group"] == group for r in rows), "killed": sum(r["group"] == group and r["result"] == "killed" for r in rows)} for group, _, _ in groups},
        "target_restored": sha256(target) == original_sha,
    }
    (args.out / "mutation_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results["summary"], indent=2))
    return 0 if controls_ok and not unexpected and results["summary"]["target_restored"] else 1


if __name__ == "__main__":
    sys.exit(main())
