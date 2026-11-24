#!/usr/bin/env python3
"""
Re-derive the countable and historical claims of the ml-propose carrier's texts from the landed tree, tags and commits.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, validation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (quick check of the ml-propose carrier, round 3b, flood-4 session 7)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14

WHY THIS EXISTS
The PR body, the commit body, the CHANGELOG entry and a comment in propose.py state numbers (tests per class, how
the new tests fail on main's propose.py) and history (which release's pins a matrix row holds; what four merged
pull requests did to the matrix). Each is re-derived here from the source of truth:

* the test counts, by parsing the landed test file and main's;
* the failures on main's propose.py, from the log of that run in the validator's twin;
* the series rows, from docs/REFERENCE.md at tag v0.11.4 against pyproject.toml at every release tag;
* the pull requests, from their squash commits on main (the matrix before and after each);
* the pins that can escape a ceiling, from main's pyproject.toml;
* wordings the final check asked to be gone, by counting them in the landed files.

Usage:
    python3 <this> --landed <landing worktree> --main-log <the MAIN suite log> --out <json>
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess  # nosec B404 - fixed argv: read-only plumbing in the validator's own landing worktree
import sys
import tomllib
from pathlib import Path

TESTS = "tests/test_release_train_propose.py"
REFERENCE = "docs/REFERENCE.md"
NEW_CLASSES = ("ReferenceCompatHelperTest", "BuildProposalReferenceCompatTest")
TAGS = ("v0.6.0", "v0.7.0", "v0.7.1", "v0.8.0", "v0.9.0", "v0.10.0", "v0.11.0", "v0.11.1", "v0.11.2", "v0.11.3", "v0.11.4")
COMMITS = {"1991": "594bb5dd", "2306": "0b714d90", "2319": "d7a1908d", "2339": "e8d38732", "2349": "a771a5b8", "2473": "84569b4a", "2482": "957f0e94"}
REQ = re.compile(r"^(?P<pkg>juniper-[a-z0-9-]+)(?:\[[^\]]*\])?(?P<spec>[<>=!~].*)$")
PROBLEM = re.compile(r"^(FAIL|ERROR): (\S+) \((\S+?)\)", re.MULTILINE)
GONE = ("carried in the round-2 tests carrier", "merges before this PR", "restore the pins that series published", "NOT edited by the train", "four Ecosystem Compatibility release sites")


def show(root: Path, spec: str) -> "str | None":
    done = subprocess.run(["git", "show", spec], cwd=root, capture_output=True, check=False)  # nosec B603 B607
    return done.stdout.decode("utf-8", "replace") if done.returncode == 0 else None


def test_methods(source: str) -> dict:
    counts = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.ClassDef):
            counts[node.name] = sorted(item.name for item in node.body if isinstance(item, ast.FunctionDef) and item.name.startswith("test"))
    return counts


def matrix(text: str) -> "tuple | None":
    """(header cells, {series: cells}) of the first `| juniper-ml |` table in the text."""
    lines = text.splitlines()
    for index, line in enumerate(lines):
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells[:1] == ["juniper-ml"] and index + 1 < len(lines) and set(lines[index + 1]) <= set("|-: "):
            rows = {}
            for row in lines[index + 2 :]:
                if not row.startswith("|"):
                    break
                parts = [cell.strip() for cell in row.strip().strip("|").split("|")]
                rows[parts[0]] = parts[1:]
            return cells[1:], rows
    return None


def specs(pyproject: str) -> dict:
    extras = (tomllib.loads(pyproject).get("project") or {}).get("optional-dependencies") or {}
    found: dict = {}
    for name, requirements in extras.items():
        if name == "all":
            continue
        for requirement in requirements:
            hit = REQ.match(requirement.strip())
            if hit:
                found.setdefault(hit.group("pkg"), set()).add(hit.group("spec").strip())
    return {package: sorted(values) for package, values in found.items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--landed", required=True, type=Path)
    parser.add_argument("--main-log", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    landed = args.landed.resolve()
    report: dict = {}

    landed_tests = test_methods((landed / TESTS).read_text(encoding="utf-8"))
    main_tests = test_methods(show(landed, f"HEAD:{TESTS}") or "")
    report["tests"] = {
        "methods_on_main": sum(len(names) for names in main_tests.values()),
        "methods_landed": sum(len(names) for names in landed_tests.values()),
        "new_classes": {name: len(landed_tests.get(name, [])) for name in NEW_CLASSES},
        "new_classes_on_main": {name: len(main_tests.get(name, [])) for name in NEW_CLASSES},
        "methods_added_to_existing_classes": {name: sorted(set(landed_tests[name]) - set(main_tests.get(name, []))) for name in landed_tests if name not in NEW_CLASSES and set(landed_tests[name]) - set(main_tests.get(name, []))},
        "methods_removed": {name: sorted(set(main_tests[name]) - set(landed_tests.get(name, []))) for name in main_tests if set(main_tests[name]) - set(landed_tests.get(name, []))},
    }

    log = args.main_log.read_text(encoding="utf-8")
    failing = sorted({(m.group(3).rsplit(".", 1)[-1] if m.group(3).rsplit(".", 1)[-1] != m.group(2) else m.group(3).rsplit(".", 2)[-2], m.group(2)) for m in PROBLEM.finditer(log)})
    failing_names = {name for _, name in failing}
    new_methods = {name for cls in NEW_CLASSES for name in landed_tests.get(cls, [])}
    report["on_main_propose"] = {
        "result_line": (re.findall(r"^(?:OK|FAILED).*$", log, re.MULTILINE) or [None])[-1],
        "ran": (re.findall(r"^Ran (\d+) tests?", log, re.MULTILINE) or [None])[-1],
        "distinct_failing_tests": len(failing_names),
        "failing_outside_the_new_classes": sorted(failing_names - new_methods),
        "new_tests_that_pass": sorted(new_methods - failing_names),
        "new_tests_that_fail": len(new_methods & failing_names),
    }

    reference = show(landed, f"v0.11.4:{REFERENCE}") or ""
    located = matrix(reference[reference.find("Ecosystem Compatibility") :])
    history: dict = {"rows_at_v0.11.4": {}, "tags": {}}
    if located:
        header, rows = located
        history["header"] = header
        history["rows_at_v0.11.4"] = rows
        for tag in TAGS:
            pins = specs(show(landed, f"{tag}:pyproject.toml") or "[project]\n")
            cells = [" / ".join(pins.get(package, ["-"])) for package in header]
            history["tags"][tag] = {"cells": cells, "equals_rows": [series for series, row in rows.items() if row == cells]}
    report["series_row_history"] = history

    commits = {}
    for number, sha in COMMITS.items():
        subject =subprocess.run(["git", "log", "-1", "--format=%s", sha], cwd=landed, capture_output=True, text=True, check=False).stdout.strip()  # nosec B603 B607
        body = subprocess.run(["git", "log", "-1", "--format=%b", sha], cwd=landed, capture_output=True, text=True, check=False).stdout  # nosec B603 B607
        names = subprocess.run(["git", "show", "--format=", "--name-only", sha], cwd=landed, capture_output=True, text=True, check=False).stdout.split()  # nosec B603 B607
        before_text, after_text = show(landed, f"{sha}^:{REFERENCE}") or "", show(landed, f"{sha}:{REFERENCE}") or ""
        before = matrix(before_text[before_text.find("Ecosystem Compatibility") :])
        after = matrix(after_text[after_text.find("Ecosystem Compatibility") :])
        entry = {"commit": sha, "subject": subject[:110], "files": len(names), "touches_reference": REFERENCE in names, "touches_pyproject": "pyproject.toml" in names, "says_added_to_rather_than_rewritten": "ADDED TO rather than rewritten" in body}
        if before and after:
            entry["rows_added"] = sorted(set(after[1]) - set(before[1]))
            entry["rows_rewritten"] = {series: {"before": before[1][series], "after": after[1][series]} for series in before[1] if series in after[1] and before[1][series] != after[1][series]}
            entry["rows_removed"] = sorted(set(before[1]) - set(after[1]))
        commits[number] = entry
    report["pull_requests"] = commits

    pins = specs(show(landed, "HEAD:pyproject.toml") or "[project]\n")
    main_reference = show(landed, f"HEAD:{REFERENCE}") or ""
    main_matrix = matrix(main_reference[main_reference.find("\n## Ecosystem Compatibility") :])
    in_repo = ("juniper-ci-tools", "juniper-config-tools", "juniper-doc-tools", "juniper-model-core", "juniper-observability", "juniper-service-core")
    report["escaping_pins_on_main"] = {package: {"spec": pins.get(package), "has_ceiling": any("<" in spec for spec in pins.get(package, [])), "has_matrix_column": bool(main_matrix) and package in main_matrix[0]} for package in in_repo}
    report["cut_cochanges_scripts"] = sorted(path.name for path in (landed / "util" / "ad-hoc").glob("*_cut_cochanges.py"))

    counted = {}
    for rel in ("CHANGELOG.md", REFERENCE, "notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md", "util/release_train/propose.py", TESTS):
        text = (landed / rel).read_text(encoding="utf-8")
        counted[rel] = {phrase: text.count(phrase) for phrase in GONE}
        counted[rel]["ReferenceCompatibilityMatrixTest"] = text.count("ReferenceCompatibilityMatrixTest")
        counted[rel]["restore the pins that series' last release published"] = text.count("restore the pins that series' last release published")
    report["wordings_in_the_landed_files"] = counted
    args.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("tests", "on_main_propose", "escaping_pins_on_main", "cut_cochanges_scripts")}, indent=1))
    print("rows at v0.11.4 and the tags whose pyproject equals each:")
    for tag, row in history["tags"].items():
        print(" ", tag, "->", row["equals_rows"])
    for number, entry in commits.items():
        print(f"  #{number} {entry['commit']}: reference {entry['touches_reference']}, pyproject {entry['touches_pyproject']}, rows added {entry.get('rows_added')}, rewritten {sorted(entry.get('rows_rewritten', {}))}, removed {entry.get('rows_removed')}, quote {entry['says_added_to_rather_than_rewritten']}")
    print(json.dumps(counted, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
