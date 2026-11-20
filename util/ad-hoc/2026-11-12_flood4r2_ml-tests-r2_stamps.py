#!/usr/bin/env python3
"""
List every stamp, date and count site of the "ml-tests" carrier's tree, with its line, its value and its rule.

Three carriers are queued on juniper-ml and each lands on the main the one before it left, so this carrier's
document version, suite count and dates are re-derived at its landing (by the landing tool). This writes the
record that makes that mechanical and checkable: for each site, the file, the line it stands on now, the value it
holds, the rule that gives the value, and the tool that writes it. A site is found by its own pattern in the
working tree, and its value is compared with derived.json (what the tools derived from main's blobs); a site that
is missing, repeated or holds another value fails the run.

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_stamps.py --derived <derived.json> --out <stamps.json>

Exit 0 when every site was found exactly as often as its rule says, with the derived value.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier, the finish of round 2 of its build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_shared_edits.py (the tool that writes most of these sites)
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SHARED_EDITS = "util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_shared_edits.py"
LAND = "util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_land.py"
ML_PROPOSE_TOKEN = "<ML-PROPOSE-PR>"


def _head(path: str) -> str:
    return subprocess.run(["git", "show", f"HEAD:{path}"], capture_output=True, text=True, check=True).stdout


def _find(path: str, pattern: str) -> list:
    """[(line number, the match)] of every line of `path` the pattern matches."""
    found = []
    for number, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        match = re.search(pattern, line)
        if match:
            found.append((number, match))
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--derived", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    with open(args.derived, encoding="utf-8") as fh:
        derived = json.load(fh)
    reference, host = derived["docs/REFERENCE.md"], derived["host_tooling"]
    date, count, version = derived["date"], str(derived["suite_count"]), reference["version"]
    plan = [
        # (site, file, pattern with one group = the value, expected value, expected hits, rule, written by)
        ("document version, header and footer", "docs/REFERENCE.md", r"^\*\*Version:\*\* (\d+\.\d+\.\d+)$", version, 2, f"main's value at the landing ({reference['main_version']} on this base) with its patch raised by one; header == footer; no version twice", SHARED_EDITS),
        ("document date, header and footer", "docs/REFERENCE.md", r"^\*\*Last Updated:\*\* (\d{4}-\d{2}-\d{2})$", date, 2, "the UTC date of the day the pull request lands (--landing-date)", SHARED_EDITS),
        ("Version History row", "docs/REFERENCE.md", r"^\| (\d+\.\d+\.\d+)  \| \d{4}-\d{2}-\d{2} \| Cursor flood-4 round-2 tests carrier: ", version, 1, "one row, directly after the row of main's version; its version and date are the two stamps above", SHARED_EDITS),
        ("Version History row: date", "docs/REFERENCE.md", r"^\| \d+\.\d+\.\d+  \| (\d{4}-\d{2}-\d{2}) \| Cursor flood-4 round-2 tests carrier: ", date, 1, "the landing date", SHARED_EDITS),
        ("Version History row: suite count", "docs/REFERENCE.md", r"^\| \d+\.\d+\.\d+  \| \d{4}-\d{2}-\d{2} \| Cursor flood-4 round-2 tests carrier: fifteen suites registered \((\d+) in all\)", count, 1, f"main's count ({derived['main_suite_count']}) + this carrier's {derived['carried_suites']}, counted from ci.yml", SHARED_EDITS),
        ("Version History row: macOS list total", "docs/REFERENCE.md", r"Cursor flood-4 round-2 tests carrier: .* runs every agent-guard suite, (\d+) suites in all\. \|$", str(host["total"]), 1, "the number of names in ci.yml's HOST_TOOLING_SUITES", SHARED_EDITS),
        ("the 'Running every suite' tally", "docs/REFERENCE.md", r"\*\*(\d+)\*\* on \d{4}-\d{2}-\d{2} with the flood-4 round-2 tests carrier's fifteen", count, 1, "the suite count; the sentence keeps every earlier figure and gains this one at its end", SHARED_EDITS),
        ("the 'Running every suite' tally: date", "docs/REFERENCE.md", r"\*\*\d+\*\* on (\d{4}-\d{2}-\d{2}) with the flood-4 round-2 tests carrier's fifteen", date, 1, "the landing date", SHARED_EDITS),
        ("macOS gate's Test Suite Reference entry: added and total", "docs/REFERENCE.md", r"The agent guard's (\d+ other suites made it \d+) \(the Overtoad's ruling of 2026-11-12\)", f"{host['guard_suites_added']} other suites made it {host['total']}", 1, "the guard suites this carrier adds to the list, and the list's length", SHARED_EDITS),
        ("CI/CD Pipeline Reference item: guard files on disk", "docs/REFERENCE.md", r"\(`tests/test_claude_agent_guard\*\.py`, (\d+) files\) beside the turing suites", str(host["guard_suites_on_disk"]), 1, "the number of tests/test_claude_agent_guard*.py files", SHARED_EDITS),
        ("suite count in the 'Run all tests' comment", "AGENTS.md", r"^# Run all tests -- the full ordered list of (\d+) `python3 -m unittest`", count, 1, "the suite count", SHARED_EDITS),
        ("AGENTS.md date", "AGENTS.md", r"^\*\*Last Updated\*\*: (\d{4}-\d{2}-\d{2})$", date, 1, "the landing date; when main already holds it the line is not in the diff, and the AGENTS.md date check passes only while it runs on that UTC day", SHARED_EDITS),
        ("CHANGELOG entry: suite count", "CHANGELOG.md", r"new suites, wired into `ci\.yml` and `docs/REFERENCE\.md` \((\d+) in all\)", count, 1, "the suite count (template token @SUITE_COUNT@)", LAND),
        ("CHANGELOG entry: macOS list total", "CHANGELOG.md", r"and the five carried here; (\d+) suites in all\.", str(host["total"]), 1, "the macOS list's length (template token @HOST_TOOLING_TOTAL@)", LAND),
    ]
    sites, problems = [], []
    for site, path, pattern, expected, hits, rule, tool in plan:
        found = _find(path, pattern)
        values = [match.group(1) for _number, match in found]
        if len(found) != hits or any(value != expected for value in values):
            problems.append(f"{path}: {site}: expected {hits} x {expected!r}, found {values} at lines {[number for number, _match in found]}")
        sites.append({"site": site, "file": path, "lines": [number for number, _match in found], "value": expected, "rule": rule, "written_by": tool})
    main_agents_date = re.search(r"^\*\*Last Updated\*\*: (\d{4}-\d{2}-\d{2})$", _head("AGENTS.md"), re.M)
    token = _find("CHANGELOG.md", re.escape(ML_PROPOSE_TOKEN))
    report = {
        "base_sha": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip(),
        "derived": derived,
        "agents_md_last_updated_line_is_in_the_diff": bool(main_agents_date) and main_agents_date.group(1) != date,
        "sites": sites,
        "ml_propose_token": {"token": ML_PROPOSE_TOKEN, "tree_sites": [f"CHANGELOG.md:{number}" for number, _match in token], "rule": "the ml-propose pull request's number; the landing tool writes it with --ml-propose-pr N", "written_by": LAND},
        "dates_that_are_not_stamps": "2026-11-08, 2026-11-09 and 2026-11-12 in the CHANGELOG entry, ci.yml, docs/REFERENCE.md and tests/test_ci_host_tooling_macos.py are the days of Overtoad rulings; they do not move with the landing",
        "problems": problems,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
        fh.write("\n")
    for row in sites:
        print(f"{row['file']}:{','.join(str(number) for number in row['lines'])}  {row['site']} = {row['value']}")
    print(f"{ML_PROPOSE_TOKEN}: {report['ml_propose_token']['tree_sites'] or 'not in the tree'}")
    print("OK" if not problems else "PROBLEMS:\n" + "\n".join(problems))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
