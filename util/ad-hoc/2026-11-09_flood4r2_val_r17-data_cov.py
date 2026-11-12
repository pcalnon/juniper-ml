"""
Compare two juniper-data coverage.json reports, and list which tests executed given source lines.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator session, Cursor flood-4 round 2)
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: owner ruling 17 ("data: 44 unrun tests"); independent validation of the r17-data-unit-marks carrier

Subcommands (run with an interpreter that has ``coverage`` installed):
  diff      --before B.json --after A.json        per-file statement / branch changes between two reports
  contexts  --data .coverage --line FILE:LINE ...  the dynamic contexts (pytest-cov ``--cov-context=test``)
                                                   that executed each line; FILE is matched as a path suffix
"""

import argparse
import json
import sys
from pathlib import Path


def cmd_diff(args: argparse.Namespace) -> int:
    before = json.loads(Path(args.before).read_text(encoding="utf-8"))
    after = json.loads(Path(args.after).read_text(encoding="utf-8"))
    print(f"totals before: {before['totals']['percent_covered_display']}%  after: {after['totals']['percent_covered_display']}%")
    for key in ("num_statements", "covered_lines", "missing_lines", "num_branches", "covered_branches", "num_partial_branches", "missing_branches"):
        print(f"  {key:22s} {before['totals'].get(key)} -> {after['totals'].get(key)}")
    changed = 0
    for path in sorted(set(before["files"]) | set(after["files"])):
        b = before["files"].get(path)
        a = after["files"].get(path)
        if b is None or a is None:
            print(f"  only in one report: {path}")
            changed += 1
            continue
        newly_lines = sorted(set(a["executed_lines"]) - set(b["executed_lines"]))
        lost_lines = sorted(set(b["executed_lines"]) - set(a["executed_lines"]))
        b_missing_br = {tuple(x) for x in b.get("missing_branches", [])}
        a_missing_br = {tuple(x) for x in a.get("missing_branches", [])}
        newly_br = sorted(b_missing_br - a_missing_br)
        lost_br = sorted(a_missing_br - b_missing_br)
        if newly_lines or lost_lines or newly_br or lost_br:
            changed += 1
            print(f"  {path}: {b['summary']['percent_covered_display']}% -> {a['summary']['percent_covered_display']}%; lines +{newly_lines} -{lost_lines}; branches +{newly_br} -{lost_br}")
    print(f"files changed: {changed}")
    return 0


def cmd_contexts(args: argparse.Namespace) -> int:
    from coverage import CoverageData

    data = CoverageData(basename=args.data)
    data.read()
    measured = list(data.measured_files())
    out: dict = {}
    for spec in args.line:
        suffix, line_text = spec.rsplit(":", 1)
        line = int(line_text)
        matches = [f for f in measured if f.endswith(suffix)]
        if len(matches) != 1:
            print(f"{spec}: {len(matches)} measured files match the suffix")
            continue
        by_line = data.contexts_by_lineno(matches[0])
        contexts = sorted({c.rsplit("|", 1)[0] for c in by_line.get(line, []) if c})
        out[spec] = contexts
        files = sorted({c.split("::", 1)[0] for c in contexts})
        print(f"{spec}: executed by {len(contexts)} test contexts in {len(files)} files")
        for f in files:
            print(f"    {f}: {sum(1 for c in contexts if c.startswith(f + '::'))}")
    if args.out:
        Path(args.out).write_text(json.dumps(out, indent=1), encoding="utf-8")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="coverage helpers")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("diff")
    p.add_argument("--before", required=True)
    p.add_argument("--after", required=True)
    p = sub.add_parser("contexts")
    p.add_argument("--data", required=True)
    p.add_argument("--line", action="append", required=True)
    p.add_argument("--out", default=None)
    args = parser.parse_args()
    return {"diff": cmd_diff, "contexts": cmd_contexts}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
