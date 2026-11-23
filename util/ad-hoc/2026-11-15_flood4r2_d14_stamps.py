"""
Every stamp, date and count site of the two D-14 carriers: check them against the main each carrier sits on, or re-derive them.

The juniper-ml carrier bumps docs/REFERENCE.md and docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md once from main's value,
adds one suite (AGENTS.md's count and REFERENCE's "Running every suite" sentence), and dates both documents; the
juniper-cascor carrier bumps docs/api/API_SCHEMAS.md once. Other pull requests move those values on main before these
land, so each site is derived, not remembered:

  version  = main's value at ``--main-ref`` with its last component + 1 (REFERENCE, cheatsheet, API_SCHEMAS)
  count    = the ``python3 -m unittest`` lines of ci.yml's "Run Python regression tests" step in the carrier tree
  date     = ``--date`` (the UTC day the pull request lands; default: today, UTC)

``--check`` (the default) finds every site in each carrier and compares it with the derived value; ``--apply``
rewrites the sites that differ (run it after rebuilding a carrier's shared files three-way on the new main), then
checks. Writes ``--out`` (stamps.json) with every site: file, line, value found, value derived, rule. Exit 0 when
every site holds its derived value, 1 otherwise.

The sites include each carrier's landing texts in ``tmp/flood4-fix/d14-resume/`` (``pr_body.txt``,
``commit_body.txt``, ``changelog_entry.txt``; added 2026-11-16), so no text the orchestrator lands carries a stale
version or count. A MEASURED number in those texts (a test count, a pass count) is not a site: each names the base it
was measured on and is re-run, not re-derived.

Usage (from the juniper-ml carrier root):
    python3 util/ad-hoc/2026-11-15_flood4r2_d14_stamps.py --cascor <cascor carrier> [--main-ref origin/main]
        [--date YYYY-MM-DD] [--apply] --out <stamps.json>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the owner's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table)
"""

import argparse
import datetime
import json
import re
import subprocess
from pathlib import Path

import yaml

REFERENCE = "docs/REFERENCE.md"
CHEATSHEET = "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"
AGENTS = "AGENTS.md"
CHANGELOG = "CHANGELOG.md"
SCHEMAS = "docs/api/API_SCHEMAS.md"
HISTORY_TEXT = "juniper-service-core's `/ws/training` resume handshake answers as juniper-cascor's does"
SCRATCH = "tmp/flood4-fix/d14-resume"
PR_BODY = f"{SCRATCH}/pr_body.txt"
COMMIT_BODY = f"{SCRATCH}/commit_body.txt"
CHANGELOG_ENTRY = f"{SCRATCH}/changelog_entry.txt"


def show(repo: Path, ref: str, path: str, own: bool) -> str:
    command = ["git", "show", f"{ref}:{path}"] if own else ["git", "-C", str(repo), "show", f"{ref}:{path}"]
    return subprocess.run(command, cwd=repo if own else Path.cwd(), capture_output=True, text=True, check=True).stdout


def bump(version: str) -> str:
    head, _dot, last = version.rpartition(".")
    return f"{head}.{int(last) + 1}"


def first(pattern: str, text: str) -> str:
    match = re.search(pattern, text, re.M)
    if match is None:
        raise SystemExit(f"pattern not found on main: {pattern}")
    return match.group(1)


def suite_count(repo: Path) -> int:
    doc = yaml.safe_load((repo / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8"))
    step = next(s for s in doc["jobs"]["tests"]["steps"] if s.get("name") == "Run Python regression tests")
    return sum(1 for line in step["run"].splitlines() if line.strip().startswith("python3 -m unittest"))


def sites(ml: Path, cascor: Path, derived: dict) -> list[dict]:
    """(repo root, file, pattern whose group 1 is the value, derived value, rule, how many lines must match)."""
    ref_v, sheet_v, schema_v, date, count = derived["reference"], derived["cheatsheet"], derived["schemas"], derived["date"], str(derived["count"])
    return [
        {"repo": ml, "file": REFERENCE, "pattern": r"^\*\*Version:\*\* (\S+)$", "value": ref_v, "lines": 2, "rule": "main's REFERENCE version + 1, header and footer"},
        {"repo": ml, "file": REFERENCE, "pattern": r"^\*\*Last Updated:\*\* (\S+)$", "value": date, "lines": 2, "rule": "landing date, header and footer"},
        {"repo": ml, "file": REFERENCE, "pattern": r"^\| (\S+) +\| \S+ +\| " + re.escape(HISTORY_TEXT), "value": ref_v, "lines": 1, "rule": "the Version History row, directly after main's highest row"},
        {"repo": ml, "file": REFERENCE, "pattern": r"^\| \S+ +\| (\S+) +\| " + re.escape(HISTORY_TEXT), "value": date, "lines": 1, "rule": "the Version History row's date"},
        {"repo": ml, "file": REFERENCE, "pattern": r"\*\*(\d+)\*\* on \S+ with the shared resume table's drift gate", "value": count, "lines": 1, "rule": "the suite count after the new suite, in the Running every suite sentence"},
        {"repo": ml, "file": REFERENCE, "pattern": r"\*\*\d+\*\* on (\S+) with the shared resume table's drift gate", "value": date, "lines": 1, "rule": "the landing date in that sentence"},
        {"repo": ml, "file": REFERENCE, "pattern": r"^\| \S+ +\| \S+ +\| " + re.escape(HISTORY_TEXT) + r".*\(\*\*(\d+)\*\*\)\. \|$", "value": count, "lines": 1, "rule": "the suite count the new Version History row names"},
        {"repo": ml, "file": CHEATSHEET, "pattern": r"^\*\*Version\*\*: (\S+)$", "value": sheet_v, "lines": 1, "rule": "main's cheatsheet version + 1, header"},
        {"repo": ml, "file": CHEATSHEET, "pattern": r"^\*\*Version:\*\* (\S+)$", "value": sheet_v, "lines": 1, "rule": "the same, footer"},
        {"repo": ml, "file": CHEATSHEET, "pattern": r"^\*\*Date\*\*: (\S+)$", "value": date, "lines": 1, "rule": "landing date, header"},
        {"repo": ml, "file": CHEATSHEET, "pattern": r"^\*\*Last Updated:\*\* (\S+)$", "value": date, "lines": 1, "rule": "landing date, footer"},
        {"repo": ml, "file": AGENTS, "pattern": r"^\*\*Last Updated\*\*: (\S+)$", "value": date, "lines": 1, "rule": "landing date (agents-md-touch-up: it must equal the landing day or change in the PR)"},
        {"repo": ml, "file": AGENTS, "pattern": r"the full ordered list of (\d+) `python3 -m unittest`", "value": count, "lines": 1, "rule": "ci.yml's regression-step count"},
        {"repo": ml, "file": CHANGELOG, "pattern": r"`docs/REFERENCE\.md` \((\S+)\) and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML\.md` \(\S+\) describe the new answers", "value": ref_v, "lines": 1, "rule": "the REFERENCE version the CHANGELOG entry names"},
        {"repo": ml, "file": CHANGELOG, "pattern": r"`docs/REFERENCE\.md` \(\S+\) and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML\.md` \((\S+)\) describe the new answers", "value": sheet_v, "lines": 1, "rule": "the cheatsheet version the CHANGELOG entry names"},
        {"repo": cascor, "file": SCHEMAS, "pattern": r"^\*\*Version\*\*: (\S+)$", "value": schema_v, "lines": 1, "rule": "main's API_SCHEMAS version + 1, header"},
        {"repo": cascor, "file": SCHEMAS, "pattern": r"^\*\*Document Version\*\*: (\S+)$", "value": schema_v, "lines": 1, "rule": "the same, footer"},
        {"repo": cascor, "file": SCHEMAS, "pattern": r"^\*\*Last Updated\*\*: (\S+)$", "value": date, "lines": 2, "rule": "landing date, header and footer"},
        {"repo": cascor, "file": CHANGELOG, "pattern": r"`docs/api/API_SCHEMAS\.md` \((\S+)\) names the table in its resume section", "value": schema_v, "lines": 1, "rule": "the API_SCHEMAS version the CHANGELOG entry names"},
        # The landing texts (pull-request bodies, commit bodies, the CHANGELOG entry text), added 2026-11-16.
        {"repo": ml, "file": PR_BODY, "pattern": r"AGENTS\.md's count is (\d+)\.", "value": count, "lines": 1, "rule": "the suite count the juniper-ml PR body names"},
        {"repo": ml, "file": PR_BODY, "pattern": r"`docs/REFERENCE\.md` (\d+\.\d+\.\d+) \(", "value": ref_v, "lines": 1, "rule": "the REFERENCE version the juniper-ml PR body names"},
        {"repo": ml, "file": PR_BODY, "pattern": r"`docs/DEVELOPER_CHEATSHEET_JUNIPER-ML\.md` (\d+\.\d+\.\d+)", "value": sheet_v, "lines": 1, "rule": "the cheatsheet version the juniper-ml PR body names"},
        {"repo": ml, "file": COMMIT_BODY, "pattern": r"^docs/REFERENCE\.md (\S+) and docs/DEVELOPER_CHEATSHEET_JUNIPER-ML\.md \S+ describe", "value": ref_v, "lines": 1, "rule": "the REFERENCE version the juniper-ml commit body names"},
        {"repo": ml, "file": COMMIT_BODY, "pattern": r"^docs/REFERENCE\.md \S+ and docs/DEVELOPER_CHEATSHEET_JUNIPER-ML\.md (\S+) describe", "value": sheet_v, "lines": 1, "rule": "the cheatsheet version the juniper-ml commit body names"},
        {"repo": ml, "file": COMMIT_BODY, "pattern": r"(\d+) regression suites\.", "value": count, "lines": 1, "rule": "the suite count the juniper-ml commit body names"},
        {"repo": ml, "file": CHANGELOG_ENTRY, "pattern": r"`docs/REFERENCE\.md` \((\S+)\) and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML\.md` \(\S+\) describe the new answers", "value": ref_v, "lines": 1, "rule": "changelog_entry.txt: the REFERENCE version (mirrors CHANGELOG.md)"},
        {"repo": ml, "file": CHANGELOG_ENTRY, "pattern": r"`docs/REFERENCE\.md` \(\S+\) and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML\.md` \((\S+)\) describe the new answers", "value": sheet_v, "lines": 1, "rule": "changelog_entry.txt: the cheatsheet version (mirrors CHANGELOG.md)"},
        {"repo": cascor, "file": PR_BODY, "pattern": r"`docs/api/API_SCHEMAS\.md` \((\S+)\)", "value": schema_v, "lines": 1, "rule": "the API_SCHEMAS version the juniper-cascor PR body names"},
        {"repo": cascor, "file": COMMIT_BODY, "pattern": r"^(\S+) names the table in its resume section\.", "value": schema_v, "lines": 1, "rule": "the API_SCHEMAS version the juniper-cascor commit body names"},
        {"repo": cascor, "file": CHANGELOG_ENTRY, "pattern": r"`docs/api/API_SCHEMAS\.md` \((\S+)\) names the table in its resume section", "value": schema_v, "lines": 1, "rule": "changelog_entry.txt: the API_SCHEMAS version (mirrors CHANGELOG.md)"},
    ]


def evaluate(site: dict) -> list[dict]:
    lines = (site["repo"] / site["file"]).read_text(encoding="utf-8").splitlines()
    found = []
    for number, line in enumerate(lines, 1):
        match = re.search(site["pattern"], line)
        if match:
            found.append({"line": number, "value": match.group(1)})
    return found


def apply(site: dict, found: list[dict]) -> None:
    path = site["repo"] / site["file"]
    lines = path.read_text(encoding="utf-8").split("\n")
    for hit in found:
        line = lines[hit["line"] - 1]
        match = re.search(site["pattern"], line)
        lines[hit["line"] - 1] = line[: match.start(1)] + site["value"] + line[match.end(1) :]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--ml", type=Path, default=Path.cwd())
    parser.add_argument("--cascor", type=Path, required=True)
    parser.add_argument("--main-ref", default="origin/main")
    parser.add_argument("--date", default=datetime.datetime.now(datetime.timezone.utc).date().isoformat())
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    derived = {
        "reference": bump(first(r"^\*\*Version:\*\* (\S+)$", show(args.ml, args.main_ref, REFERENCE, own=True))),
        "cheatsheet": bump(first(r"^\*\*Version\*\*: (\S+)$", show(args.ml, args.main_ref, CHEATSHEET, own=True))),
        "schemas": bump(first(r"^\*\*Version\*\*: (\S+)$", show(args.cascor, args.main_ref, SCHEMAS, own=False))),
        "count": suite_count(args.ml),
        "date": args.date,
        "main_ref": args.main_ref,
    }
    report = []
    ok = True
    for site in sites(args.ml, args.cascor, derived):
        found = evaluate(site)
        if args.apply and found and any(hit["value"] != site["value"] for hit in found):
            apply(site, found)
            found = evaluate(site)
        expected_lines = site["lines"]
        good = bool(found) and all(hit["value"] == site["value"] for hit in found) and (expected_lines is None or len(found) == expected_lines)
        ok = ok and good
        report.append({"repo": site["repo"].name, "file": site["file"], "rule": site["rule"], "derived": site["value"], "found": found, "ok": good})
        print(f"{'OK  ' if good else 'FAIL'} {site['repo'].name}:{site['file']} {[hit['line'] for hit in found]} found {[hit['value'] for hit in found]} derived {site['value']} ({site['rule']})")
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump({"derived": derived, "sites": report, "ok": ok}, handle, indent=1)
        handle.write("\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
