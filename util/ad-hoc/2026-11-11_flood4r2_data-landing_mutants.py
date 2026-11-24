#!/usr/bin/env python3
"""
Re-run the carriers' validated mutants on a landing stage tree, restoring every mutated file byte for byte.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: landing prep for juniper-data's three carriers)
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (a carried test must still be non-vacuous on the tree that lands)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt rule 12; adapted from 2026-11-08_flood4r2_fix_mutants.py (which runs the
         JuniperData conda interpreter; this one takes the interpreter as an argument)

Usage:
    python3 <this> --python <venv interpreter> --spec <spec.json> --out <dir>

spec.json:
    {"worktree": "<absolute path>", "label": "<stage>", "tests": ["<repo-relative test file>", ...],
     "expect_sha256": {"<repo-relative file>": "<sha256 it must have before the run starts>", ...}   (optional),
     "mutants": [{"id": "...", "file": "<repo-relative>", "old": "<exact text, once>", "new": "...",
                  "line": <1-based line> (optional: mutate only that line, which must equal ``old``),
                  "replace_with": "<absolute path whose bytes replace the file>"   (instead of old/new),
                  "tests": [...] (optional; default: the top-level list),
                  "must_fail": ["<substring of a test id that must be among the failures>", ...],
                  "must_pass": ["<substring of a test id that must NOT be among the failures>", ...],
                  "allow_other_failures": <how many failures may be something other than an assertion; default 0>,
                  "expect": "killed" | "survived"}]}

A baseline run of the top-level selection comes first and must exit 0. Each mutant then: deletes the target's stale
``__pycache__`` entries, records its sha256, writes the mutant, runs its selection, restores the original bytes in a
``finally`` block, checks the sha256 again and deletes the cache entries again. KILLED means pytest exited 1 with
failures (exit 2 or more is an ERROR, never a kill), every ``must_fail`` substring names a failed test, no
``must_pass`` substring does, the run held as many tests as the baseline has for the same files, and every failure
is an ASSERTION's (JUnit message starting ``assert `` or ``AssertionError``) apart from ``allow_other_failures``: a
mutant that makes the code raise, or breaks an import, has not been caught by a test. Runs use ``-B`` and
``-p no:cacheprovider`` from the worktree root, after a probe shows ``juniper_data`` imports from that worktree. The
six Sentry DSN variables are set to "" for every run (the consolidated plan's H-14). One run at a time.

A ``finally`` block does not run when the process is killed, and on 2026-11-12 23:11Z a kill between "apply" and
"restore" left a mutant in a carrier's source file. Two guards were added that day for it:
  - ``expect_sha256``: every file it names must have that sha256 before the baseline, or the run refuses (exit 2),
    so a file a killed run left mutated is never taken for the original;
  - a journal: before a mutant is written, the original bytes go to ``<out>/in_flight_original.bin`` and
    ``<out>/IN_FLIGHT.json`` names the file, the mutant and the sha256 to restore to. Both are removed once the
    restore is verified. A run that finds ``IN_FLIGHT.json`` in its --out refuses (exit 2) and says what to restore.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess  # nosec B404 - fixed argv: a chosen interpreter running pytest
import sys
import xml.etree.ElementTree as ET  # nosec B405 - parses JUnit files this script's own pytest runs just wrote
from pathlib import Path


SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _purge(path: Path) -> list[str]:
    removed = []
    cache = path.parent / "__pycache__"
    if cache.is_dir():
        for pyc in sorted(cache.glob(path.stem + ".*.pyc")):
            pyc.unlink()
            removed.append(pyc.name)
    return removed


def _failed(junit: Path) -> tuple[list[str], dict[str, int], list[str], list[str]]:
    """(failed or errored ids, counts, those of them that are NOT an assertion's failure, every id that ran)."""
    failed: list[str] = []
    not_assertions: list[str] = []
    ran: list[str] = []
    counts = {"passed": 0, "failed": 0, "skipped": 0}
    if not junit.is_file():
        return failed, counts, not_assertions, ran
    for case in ET.parse(junit).getroot().iter("testcase"):  # nosec B314
        node = f"{case.get('classname')}::{case.get('name')}"
        ran.append(node)
        failure = case.find("failure")
        if failure is not None or case.find("error") is not None:
            failed.append(node)
            counts["failed"] += 1
            if failure is None or not (failure.get("message") or "").startswith(("assert ", "AssertionError")):
                not_assertions.append(node)
        elif case.find("skipped") is not None:
            counts["skipped"] += 1
        else:
            counts["passed"] += 1
    return sorted(failed), counts, sorted(not_assertions), ran


def _run(python: str, wt: Path, out: Path, tag: str, tests: list[str]) -> dict:
    junit = out / f"junit_{tag}.xml"
    if junit.exists():
        junit.unlink()
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **dict.fromkeys(SENTRY_DSN_NAMES, "")}
    probe = subprocess.run([python, "-B", "-c", "import juniper_data; print(juniper_data.__file__)"], cwd=wt, capture_output=True, text=True, check=False, env=env)  # nosec B603
    cmd = [python, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-rA", "--timeout=120", f"--junitxml={junit}", *tests]
    proc = subprocess.run(cmd, cwd=wt, capture_output=True, text=True, check=False, env=env)  # nosec B603
    log = out / f"log_{tag}.txt"
    log.write_text(f"$ (cwd={wt}) {' '.join(cmd)}\n# exit={proc.returncode}\n\n{proc.stdout}\n--- stderr ---\n{proc.stderr}", encoding="utf-8")
    failed, counts, not_assertions, ran = _failed(junit)
    return {"tag": tag, "exit": proc.returncode, "counts": counts, "failed": failed, "failed_not_on_an_assertion": not_assertions, "ran": ran, "log": str(log), "juniper_data_from": probe.stdout.strip(), "imported_inside_wt": probe.stdout.strip().startswith(str(wt) + os.sep)}


def _expected_tests(baseline_ran: list[str], tests: list[str]) -> int:
    """How many of the baseline's tests live in the selected files (a selection is a list of test FILES here)."""
    modules = tuple(test.removesuffix(".py").replace("/", ".") + "." for test in tests)
    return sum(1 for node in baseline_ran if node.startswith(modules))


def _mutated(mutant: dict, original: bytes) -> tuple[bytes | None, str]:
    """The mutated bytes and where the change is; (None, why) when the spec does not fit the file."""
    if "replace_with" in mutant:
        return Path(mutant["replace_with"]).read_bytes(), f"whole file <- {mutant['replace_with']}"
    text = original.decode("utf-8")
    if "line" in mutant:
        lines = text.splitlines(keepends=True)
        index = mutant["line"] - 1
        if not 0 <= index < len(lines) or lines[index] != mutant["old"]:
            return None, f"line {mutant['line']} is not the old text"
        lines[index] = mutant["new"]
        return "".join(lines).encode("utf-8"), f"{mutant['file']}:{mutant['line']}"
    count = text.count(mutant["old"])
    if count != 1:
        return None, f"old text occurs {count} times"
    return text.replace(mutant["old"], mutant["new"]).encode("utf-8"), f"{mutant['file']}:{text[: text.index(mutant['old'])].count(chr(10)) + 1}"


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--python", required=True)
    ap.add_argument("--spec", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    wt = Path(spec["worktree"]).resolve()
    journal = out / "IN_FLIGHT.json"
    backup = out / "in_flight_original.bin"
    if journal.exists():
        print(f"REFUSED: {journal} exists: an earlier run was killed between apply and restore. Restore the file it names from {backup}, check its sha256, then remove both.")
        return 2
    wrong = {name: _sha(wt / name) for name, want in spec.get("expect_sha256", {}).items() if _sha(wt / name) != want}
    if wrong:
        print(f"REFUSED: not at the sha256 the spec expects: {json.dumps(wrong)}")
        return 2
    baseline = _run(args.python, wt, out, "baseline", spec["tests"])
    summary: dict = {"label": spec.get("label"), "python": args.python, "worktree": str(wt), "tests": spec["tests"], "sentry_dsn_names_set_to_empty": list(SENTRY_DSN_NAMES), "sha256_checked_before_the_run": spec.get("expect_sha256", {}), "baseline": baseline, "mutants": []}
    print(f"baseline: exit={baseline['exit']} {baseline['counts']} inside_wt={baseline['imported_inside_wt']}")
    ok = baseline["exit"] == 0 and baseline["imported_inside_wt"]
    for mutant in spec.get("mutants", []):
        target = wt / mutant["file"]
        original = target.read_bytes()
        before = hashlib.sha256(original).hexdigest()
        mutated, where = _mutated(mutant, original)
        if mutated is None:
            summary["mutants"].append({"id": mutant["id"], "result": "ERROR", "why": where})
            print(f"{mutant['id']}: ERROR {where}")
            ok = False
            continue
        purged = _purge(target)
        backup.write_bytes(original)
        journal.write_text(json.dumps({"mutant": mutant["id"], "file": str(target), "restore_to_sha256": before, "original_bytes": str(backup)}, indent=1) + "\n", encoding="utf-8")
        try:
            target.write_bytes(mutated)
            run = _run(args.python, wt, out, mutant["id"], mutant.get("tests", spec["tests"]))
        finally:
            target.write_bytes(original)
            purged += _purge(target)
        after = _sha(target)
        restored = after == before
        if restored:
            journal.unlink()
            backup.unlink()
        must = mutant.get("must_fail", [])
        missing = [m for m in must if not any(m in node for node in run["failed"])]
        must_pass = mutant.get("must_pass", [])
        wrongly_failed = [m for m in must_pass if any(m in node for node in run["failed"])]
        expected_tests = _expected_tests(baseline["ran"], mutant.get("tests", spec["tests"]))
        tests_run = len(run["ran"])
        too_many_other = len(run["failed_not_on_an_assertion"]) > mutant.get("allow_other_failures", 0)
        if run["exit"] == 1 and run["failed"] and tests_run != expected_tests:
            verdict = f"failed-but-ran {tests_run} tests, not the baseline's {expected_tests}"
        elif run["exit"] == 1 and run["failed"] and too_many_other:
            verdict = f"failed-but-not-on-assertions {run['failed_not_on_an_assertion']}"
        elif run["exit"] == 1 and run["failed"] and not missing and not wrongly_failed:
            verdict = "killed"
        elif run["exit"] == 0 and not missing:
            verdict = "survived"
        elif run["exit"] == 1:
            verdict = f"killed-but-not-by {missing}" if missing else f"killed-and-also-failed {wrongly_failed}"
        else:
            verdict = "ERROR"
        expect = mutant.get("expect", "killed")
        row = {
            "id": mutant["id"],
            "test_file": mutant.get("test_file"),
            "mutant": where + ("" if "replace_with" in mutant else f": {mutant['old'].strip()!r} -> {mutant['new'].strip()!r}"),
            "why": mutant.get("why"),
            "result": verdict,
            "expect": expect,
            "as_expected": verdict == expect,
            "exit": run["exit"],
            "counts": run["counts"],
            "tests_run": tests_run,
            "baseline_tests_in_the_same_files": expected_tests,
            "failed": run["failed"],
            "failed_not_on_an_assertion": run["failed_not_on_an_assertion"],
            "other_failures_allowed": mutant.get("allow_other_failures", 0),
            "must_fail": must,
            "must_pass": must_pass,
            "sha256_before": before,
            "sha256_after": after,
            "restored": restored,
            "pyc_purged": purged,
            "imported_inside_wt": run["imported_inside_wt"],
            "log": run["log"],
        }
        summary["mutants"].append(row)
        ok = ok and restored and row["as_expected"] and run["imported_inside_wt"]
        print(f"{mutant['id']}: {verdict} (expect {expect}) exit={run['exit']} failed={len(run['failed'])} of {sum(run['counts'].values())} restored={restored}")
    summary["all_as_expected_and_restored"] = ok
    with open(out / "mutants_summary.json", "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=1)
        fh.write("\n")
    print(f"ok={ok} summary={out / 'mutants_summary.json'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
