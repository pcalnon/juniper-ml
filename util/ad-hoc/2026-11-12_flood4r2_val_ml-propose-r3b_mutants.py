#!/usr/bin/env python3
"""
Mutants of what round 3 of the ml-propose carrier changed, run in the validator's own twin of the landed tree.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, validation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (quick check of the ml-propose carrier, round 3b, flood-4 session 7)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14

WHY THIS EXISTS
Round 3 changed propose.py's REVIEW string and three groups of tests after the last independent review: the
live-file control (it no longer counts physical lines), the checklist assertions, and the "last release" wording.
This runs, in a twin worktree that holds the landed carrier and never in the carrier itself:

* K1..K14 -- the validator's own mutants of propose.py, aimed at those tests;
* S3 S5 S6 S7 S13 -- the five checklist mutants that survived round 2's tests (the final check's definitions);
* R1..R5 -- changes to the LIVE docs/REFERENCE.md the live-file control reads: R1 parts the clause from the
  sentence with a paragraph break and must PASS, R2..R5 remove or double a site and must FAIL;
* MAIN -- main's propose.py under the carrier's tests (the new tests must fail on the code they are for);
* R2TEST -- round 2's test file, its live-file control alone, on R1's parted REFERENCE (the defect F2 named).

Each mutant is applied to one file, both the live-file control alone and the whole suite are run, and the file is
restored in a ``finally`` block; its sha256 is compared with the original after every mutant, and the run stops
if it differs. The interpreter runs with -B and the byte-code caches are removed first.

Usage:
    python3 <this> --twin <worktree> --out <dir> --expect-propose <sha256> --expect-tests <sha256>
                   --expect-reference <sha256> [--python <interpreter>] [--only ID ...]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess  # nosec B404 - fixed argv: the interpreter and unittest in the validator's own twin worktree
import sys
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
# No test run may reach the desktop session bus: an older tree's scheduled-backup suite runs the real notify-send.
QUIET_DESKTOP = {"DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent/no-session-bus"}
PROPOSE = "util/release_train/propose.py"
TESTS = "tests/test_release_train_propose.py"
REFERENCE = "docs/REFERENCE.md"
SUITE = "tests/test_release_train_propose.py"
LIVE_CONTROL = "tests.test_release_train_propose.ReferenceCompatHelperTest.test_helpers_find_every_site_in_the_live_reference"
ROUND2_TESTS = Path.home() / "Development" / "python" / "Juniper" / "juniper-ml" / ".claude" / "worktrees" / "agent-a89a45162cee4b2e8" / TESTS
RAN = re.compile(r"^Ran (\d+) tests? in ", re.MULTILINE)
RESULT = re.compile(r"^(OK|FAILED)(?: \((.*)\))?\s*$", re.MULTILINE)
PROBLEM = re.compile(r"^(FAIL|ERROR): (\S+) \((\S+?)\)", re.MULTILINE)
CLAUSE = re.compile(r"(?<![0-9.])(\d+\.\d+\.\d+) sets them to ")

# (id, aimed at, what, file, old, new, expect the live control alone, expect the whole suite)
CODE_MUTANTS = (
    ("K1", "F2 live control: only the site lines", "the sentence writer replaces the old version everywhere in the file", "    return text[: m.start(2)] + new_version + text[m.end(2) :], m.group(2)", "    return text.replace(m.group(2), new_version), m.group(2)", "FAIL", "FAIL"),
    ("K2", "F2 live control: one row added", "a new series row is inserted twice", '    return "".join(lines), "added"', '    lines.insert(last + 1, lines[last + 1])\n    return "".join(lines), "added"', "FAIL", "FAIL"),
    ("K3", "F2 live control: the added line is the new series' row", "the series label is N.N.X", '    return f"{m.group(1)}.{m.group(2)}.x" if m else None', '    return f"{m.group(1)}.{m.group(2)}.X" if m else None', "FAIL", "FAIL"),
    ("K4", "F2 live control: what it does not check (position)", "a new series row goes above the older rows", "    last = rows[-1] if rows else header_idx + 1", "    last = header_idx + 1", "PASS", "FAIL"),
    (
        "K5",
        "F2 live control: the parted layout",
        "the clause is found only on the line that holds the sentence",
        "    matches = list(_REFERENCE_SETS_THEM.finditer(text))",
        '    matches = [hit for hit in _REFERENCE_SETS_THEM.finditer(text) if "declares the following pins." in text[text.rfind("\\n", 0, hit.start()) + 1 : hit.start()]]',
        "FAIL",
        "FAIL",
    ),
    ("K6", "F2 live control: what it does not check (cell width)", "the Version cell is written unpadded", "    raw[2] = _fit_cell(raw[2], f\"`{new_version}`\")", '    raw[2] = f" `{new_version}` "', "PASS", "FAIL"),
    ("K7", "F3 checklist", "the REVIEW line only on the meta's own bump", "    if meta_bump or done:\n        notes = [", "    if meta_bump:\n        notes = [", "PASS", "FAIL"),
    ("K8", "F3 checklist: 'nothing is owed'", "a row a sub-package's pin DID reach is REQUIRED too", '(key == "matrix_row" and pins_moved and report.get(key) == "unexpected")', '(key == "matrix_row" and pins_moved and report.get(key) in ("unexpected", "edited"))', "PASS", "FAIL"),
    ("K9", "F3 checklist: the REQUIRED reason", "the two REQUIRED reasons are swapped", 'if report.get("unreadable") else "not found exactly once', 'if not report.get("unreadable") else "not found exactly once', "PASS", "FAIL"),
    ("K10", "F8 wording", "the REVIEW note names the series' FIRST release", "restore the pins that series' last release published\")", "restore the pins that series' first release published\")", "PASS", "FAIL"),
    ("K11", "F3 checklist: a sub-package owes the row only", "every unresolved site is REQUIRED on any in-repo bump", '(meta_bump and report.get(key) not in ("edited", "added", "current"))', '(report.get(key) not in ("edited", "added", "current"))', "PASS", "FAIL"),
    ("K12", "F3 checklist: the replaced-pins note", "recurrence_moved is true when the pins did NOT move", "old_pins is not None and set(old_pins) != set(recurrence)", "old_pins is not None and set(old_pins) == set(recurrence)", "PASS", "FAIL"),
    ("K13", "F3 checklist: the included line", "an in-place row edit is named without its moved cells", "matrix row, in place ({'; '.join(report.get('moved') or [])})\")", 'matrix row, in place")', "PASS", "FAIL"),
    ("K14", "step 5b-v", "the sites are rendered from the pyproject the proposal READ, not the one it leaves", '        final_root = next((e.new_text for e in reversed(prop.edits) if e.path == "pyproject.toml"), root_pyproject)', "        final_root = root_pyproject", "PASS", "FAIL"),
    ("S3", "F3 (final check's)", "the previous-row note also on an in-place edit", '        if report.get("matrix_row") == "added":\n            notes.append(', '        if report.get("matrix_row") in ("added", "edited"):\n            notes.append(', "PASS", "FAIL"),
    ("S5", "F3 (final check's)", "a sub-package's unrenderable row is REQUIRED even when no pin moved", '(key == "matrix_row" and pins_moved and report.get(key) == "unexpected")', '(key == "matrix_row" and report.get(key) == "unexpected")', "PASS", "FAIL"),
    ("S6", "F3 (final check's)", "the in-place note also when the row was current", '        if report.get("matrix_row") == "edited":\n            notes.append(', '        if report.get("matrix_row") in ("edited", "current"):\n            notes.append(', "PASS", "FAIL"),
    ("S7", "F3 (final check's)", "the replaced-pins note whenever a clause exists", '        if report.get("recurrence_moved"):', '        if report.get("recurrence_old"):', "PASS", "FAIL"),
    ("S13", "F3 (final check's)", "the sub-package REQUIRED path removed", ' or (key == "matrix_row" and pins_moved and report.get(key) == "unexpected")]', "]", "PASS", "FAIL"),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def part_clause(text: str) -> str:
    hit = CLAUSE.search(text)
    if hit is None or len(CLAUSE.findall(text)) != 1:
        raise SystemExit("the live REFERENCE does not hold exactly one clause")
    return text[: hit.start()].rstrip(" ") + "\n\n" + text[hit.start() :]


def once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly one occurrence, found {text.count(old)}: {old[:70]!r}")
    return text.replace(old, new, 1)


def reference_mutants(text: str) -> tuple:
    sentence = re.search(r"`juniper-ml` \d+\.\d+\.\d+ declares the following pins\.", text)
    cell = re.search(r"^\| \*\*Version\*\* .*$", text, re.MULTILINE)
    return (
        ("R1", "F2: the layout the round-2 control broke on", "a paragraph break between the sentence and the clause", part_clause(text), "PASS", "PASS"),
        ("R2", "F2 vacuity: the control reads the live file", "the sentence loses its period", once(text, sentence.group(0), sentence.group(0)[:-1] + ":"), "FAIL", "FAIL"),
        ("R3", "F2 vacuity", "a second Version cell", once(text, cell.group(0) + "\n", cell.group(0) + "\n" + cell.group(0) + "\n"), "FAIL", "FAIL"),
        ("R4", "F2 vacuity", "the section heading is renamed", once(text, "\n## Ecosystem Compatibility\n", "\n## Ecosystem Compat\n"), "FAIL", "FAIL"),
        ("R5", "F2 vacuity", "the clause's verb is plural (no clause)", text[: CLAUSE.search(text).start()] + CLAUSE.search(text).group(0).replace(" sets them to ", " set them to ") + text[CLAUSE.search(text).end() :], "FAIL", "FAIL"),
    )


class Runner:
    def __init__(self, twin: Path, python: str, out: Path):
        self.twin, self.python, self.out = twin, python, out
        self.env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}, **QUIET_DESKTOP}

    def clean(self) -> None:
        for cache in (self.twin / "util" / "release_train" / "__pycache__", self.twin / "tests" / "__pycache__"):
            shutil.rmtree(cache, ignore_errors=True)

    def unittest(self, target: str, log: Path) -> dict:
        self.clean()
        done = subprocess.run([self.python, "-B", "-m", "unittest", "-v", target], cwd=self.twin, env=self.env, capture_output=True, text=True, timeout=900, check=False)  # nosec B603
        output = done.stdout + done.stderr
        log.write_text(output, encoding="utf-8")
        ran, result = RAN.findall(output), RESULT.findall(output)
        return {
            "exit": done.returncode,
            "ran": int(ran[-1]) if ran else None,
            "result": (result[-1][0] + (f" ({result[-1][1]})" if result[-1][1] else "")) if result else None,
            "failing": sorted({f"{m.group(3).rsplit('.', 1)[-1]}.{m.group(2)}" for m in PROBLEM.finditer(output)}),
            "verdict": "PASS" if done.returncode == 0 else "FAIL",
        }

    def both(self, ident: str) -> dict:
        return {"live_control": self.unittest(LIVE_CONTROL, self.out / f"{ident}.live.log"), "suite": self.unittest(SUITE, self.out / f"{ident}.suite.log")}


def with_file(target: Path, original: bytes, mutated: bytes, action) -> tuple:
    """Write ``mutated`` to ``target``, run ``action``, and put ``original`` back whatever happens."""
    try:
        target.write_bytes(mutated)
        result = action()
    finally:
        target.write_bytes(original)
    restored = sha256(target.read_bytes()) == sha256(original)
    return result, restored


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--twin", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--python", default="/opt/miniforge3/bin/python3.12")
    parser.add_argument("--expect-propose", required=True)
    parser.add_argument("--expect-tests", required=True)
    parser.add_argument("--expect-reference", required=True)
    parser.add_argument("--only", action="append", default=[])
    args = parser.parse_args()
    twin, out = args.twin.resolve(), args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    files = {PROPOSE: args.expect_propose, TESTS: args.expect_tests, REFERENCE: args.expect_reference}
    originals = {}
    for rel, expected in files.items():
        originals[rel] = (twin / rel).read_bytes()
        if sha256(originals[rel]) != expected:
            raise SystemExit(f"{rel}: sha256 {sha256(originals[rel])} is not the expected {expected}; not starting")
    runner = Runner(twin, args.python, out)
    report = {"twin": str(twin), "python": args.python, "sha256_before": {rel: sha256(data) for rel, data in originals.items()}, "rows": []}
    results_path = out / "mutants.json"

    def save() -> None:
        results_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    def wanted(ident: str) -> bool:
        return not args.only or ident in args.only

    report["control"] = runner.both("control")
    save()
    if report["control"]["live_control"]["verdict"] != "PASS" or report["control"]["suite"]["verdict"] != "PASS":
        raise SystemExit("the unmutated twin does not pass; not starting")

    def record(ident: str, aimed: str, what: str, rel: str, got: dict, restored: bool, expect_live: str, expect_suite: str) -> None:
        row = {
            "id": ident,
            "aimed_at": aimed,
            "what": what,
            "file": rel,
            "expected": {"live_control": expect_live, "suite": expect_suite},
            "live_control": got["live_control"],
            "suite": got["suite"],
            "as_expected": got["live_control"]["verdict"] == expect_live and got["suite"]["verdict"] == expect_suite,
            "restored_sha256_ok": restored,
        }
        report["rows"].append(row)
        save()
        print(f"{ident}: live {got['live_control']['verdict']} (expected {expect_live}), suite {got['suite']['verdict']} {got['suite']['result']} (expected {expect_suite}); killed by {got['suite']['failing'][:4]}{' ...' if len(got['suite']['failing']) > 4 else ''}; restored {restored}")
        if not restored:
            raise SystemExit(f"{ident}: {rel} was not restored byte for byte; stopping")

    propose_text = originals[PROPOSE].decode("utf-8")
    for ident, aimed, what, old, new, expect_live, expect_suite in CODE_MUTANTS:
        if not wanted(ident):
            continue
        got, restored = with_file(twin / PROPOSE, originals[PROPOSE], once(propose_text, old, new).encode("utf-8"), lambda ident=ident: runner.both(ident))
        record(ident, aimed, what, PROPOSE, got, restored, expect_live, expect_suite)

    reference_text = originals[REFERENCE].decode("utf-8")
    parted = None
    for ident, aimed, what, mutated, expect_live, expect_suite in reference_mutants(reference_text):
        if ident == "R1":
            parted = mutated
        if not wanted(ident):
            continue
        got, restored = with_file(twin / REFERENCE, originals[REFERENCE], mutated.encode("utf-8"), lambda ident=ident: runner.both(ident))
        record(ident, aimed, what, REFERENCE, got, restored, expect_live, expect_suite)

    if wanted("MAIN"):
        main_propose = subprocess.run(["git", "show", f"HEAD:{PROPOSE}"], cwd=twin, capture_output=True, check=False).stdout  # nosec B603 B607
        report["main_propose_sha256"] = sha256(main_propose)
        got, restored = with_file(twin / PROPOSE, originals[PROPOSE], main_propose, lambda: runner.both("MAIN"))
        record("MAIN", "the new tests fail on the code they are for", "main's propose.py under the carrier's tests", PROPOSE, got, restored, "FAIL", "FAIL")

    if wanted("R2TEST") and parted is not None:
        round2 = ROUND2_TESTS.read_bytes()
        report["round2_tests_sha256"] = sha256(round2)

        def old_control_on_the_parted_file() -> dict:
            inner, inner_restored = with_file(twin / REFERENCE, originals[REFERENCE], parted.encode("utf-8"), lambda: {"live_control": runner.unittest(LIVE_CONTROL, out / "R2TEST.live.log"), "suite": {"exit": None, "ran": None, "result": "not run", "failing": [], "verdict": "NOT RUN"}})
            if not inner_restored:
                raise SystemExit("R2TEST: docs/REFERENCE.md was not restored; stopping")
            return inner

        got, restored = with_file(twin / TESTS, originals[TESTS], round2, old_control_on_the_parted_file)
        record("R2TEST", "F2: the defect, reproduced", "round 2's live-file control (5 changed lines) on the parted REFERENCE", TESTS, got, restored, "FAIL", "NOT RUN")

    report["sha256_after"] = {rel: sha256((twin / rel).read_bytes()) for rel in files}
    report["all_restored"] = report["sha256_after"] == report["sha256_before"]
    report["final_control"] = runner.both("final-control")
    runner.clean()
    save()
    unexpected = [row["id"] for row in report["rows"] if not row["as_expected"]]
    killed = [row["id"] for row in report["rows"] if row["file"] == PROPOSE and row["id"] != "MAIN" and row["suite"]["verdict"] == "FAIL"]
    print(f"code mutants killed by the suite: {len(killed)} of {sum(1 for row in report['rows'] if row['file'] == PROPOSE and row['id'] != 'MAIN')}; not as expected: {unexpected}; all restored: {report['all_restored']}; final control: live {report['final_control']['live_control']['verdict']}, suite {report['final_control']['suite']['result']} ({report['final_control']['suite']['ran']})")
    return 0 if report["all_restored"] and not unexpected else 1


if __name__ == "__main__":
    sys.exit(main())
