"""
Read the stamps, counts and positions the ml-tests carrier's texts state, on a main tree and a landed tree
(claims lens, session 8): ci.yml's HOST_TOOLING_SUITES, the agent-guard suites on disk, docs/REFERENCE.md's Version
and Last Updated sites and Version History rows, AGENTS.md's date / version / suite-count lines, CHANGELOG.md's
headings above the carrier's entry (and ml-propose's), and the test count of one class. Read-only.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round-2 disposition, ml-tests carrier validation (claims lens)
"""

import argparse
import ast
import json
import re
import sys
from pathlib import Path

CI = ".github/workflows/ci.yml"


def host_tooling(tree: Path) -> list:
    text = (tree / CI).read_text()
    start = text.find("HOST_TOOLING_SUITES: >-")
    end = text.find("HOST_TOOLING_PATHS: >-", start)
    if start < 0 or end < 0:
        return []
    body = text[start + len("HOST_TOOLING_SUITES: >-") : end]
    return [f"tests/test_{word}.py" for word in body.split()]


def reference(tree: Path) -> dict:
    lines = (tree / "docs/REFERENCE.md").read_text().splitlines()
    out: dict = {"version_lines": [], "date_lines": [], "history_rows": []}
    for number, line in enumerate(lines, 1):
        if re.match(r"^\*\*Version:\*\*", line) or re.match(r"^\*\*Version\*\*:", line):
            out["version_lines"].append((number, line))
        if re.match(r"^\*\*Last Updated:?\*\*:?", line):
            out["date_lines"].append((number, line))
        if re.match(r"^\| 0\.6\.(6[5-9]|7[0-9]) ", line):
            out["history_rows"].append((number, line[:260]))
    versions = [re.match(r"^\| (0\.6\.\d+) ", row[1]).group(1) for row in out["history_rows"]]
    out["history_versions_twice"] = sorted({v for v in versions if versions.count(v) > 1})
    return out


def agents(tree: Path) -> dict:
    lines = (tree / "AGENTS.md").read_text().splitlines()
    picks = []
    for number, line in enumerate(lines, 1):
        if line.startswith("**Last Updated**") or line.startswith("**Version**") or re.search(r"\b(239|242|254|257)\b", line):
            picks.append((number, line[:300]))
    return {"lines": picks}


def changelog(tree: Path, needles: list) -> dict:
    lines = (tree / "CHANGELOG.md").read_text().splitlines()
    heads = [(n, line) for n, line in enumerate(lines, 1) if line.startswith("## [") or line.startswith("### ")]
    out: dict = {"top_headings": [], "needles": {}}
    for n, line in heads:
        out["top_headings"].append((n, line))
        if line.startswith("## [") and "Unreleased" not in line:
            break
    for needle in needles:
        hits = [n for n, line in enumerate(lines, 1) if needle in line]
        info = []
        for hit in hits:
            above = [h for h in heads if h[0] < hit]
            release = next((h for h in reversed(above) if h[1].startswith("## [")), None)
            group = next((h for h in reversed(above) if h[1].startswith("### ")), None)
            info.append({"line": hit, "release": release, "group": group})
        out["needles"][needle] = info
    return out


def class_tests(path: Path, name: str) -> int:
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return sum(1 for item in node.body if isinstance(item, ast.FunctionDef) and item.name.startswith("test"))
    return -1


def main() -> int:
    parser = argparse.ArgumentParser(description="Read stamps, counts and positions.")
    parser.add_argument("--tree", action="append", required=True, help="label=path")
    parser.add_argument("--needle", action="append", default=[])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    report = {}
    for spec in args.tree:
        label, path = spec.split("=", 1)
        tree = Path(path)
        host = host_tooling(tree)
        guards = sorted(str(p.relative_to(tree)) for p in (tree / "tests").glob("test_claude_agent_guard*.py"))
        report[label] = {
            "host_tooling_suites": host,
            "host_tooling_count": len(host),
            "guard_files_on_disk": guards,
            "guard_files_not_in_host_list": [g for g in guards if g not in host],
            "reference": reference(tree),
            "agents": agents(tree),
            "changelog": changelog(tree, args.needle),
            "ReferenceCompatibilityMatrixTest_tests": class_tests(tree / "tests/test_pyproject_extras.py", "ReferenceCompatibilityMatrixTest"),
        }
    text = json.dumps(report, indent=1)
    print(text)
    if args.out:
        args.out.write_text(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
