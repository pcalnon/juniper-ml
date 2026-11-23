"""
Apply a validator's text_fixes.json (pairs of exact old -> new strings) to the D-14 carriers, all-or-nothing per file.

For each file, every pair must hold BEFORE anything is written: the old string occurs exactly ``old_count`` times
(1) and the new string exactly ``new_count`` times (0). If any pair of a file fails, no pair of that file is applied
and the file is reported. Otherwise the pairs are applied in order and re-checked: each old string gone, each new
string present. ``--root <repo>=<path>`` maps each pair's ``repo`` key to the tree it is applied to (the rebuilt
carrier, which may not be the path the validator read). Without ``--apply`` it only checks.

Usage:
    python3 util/ad-hoc/2026-11-16_flood4r2_d14_text_fixes.py --fixes <text_fixes.json> --root ml=<path>
        --root cascor=<path> --out <report.json> [--apply]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the owner's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table)
"""

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--fixes", required=True, type=Path)
    parser.add_argument("--root", action="append", default=[], help="<repo key>=<tree path>")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    roots = dict(item.split("=", 1) for item in args.root)
    fixes = json.loads(args.fixes.read_text(encoding="utf-8"))["fixes"]
    by_file: "OrderedDict[tuple[str, str], list[dict]]" = OrderedDict()
    for fix in fixes:
        by_file.setdefault((fix["repo"], fix["file"]), []).append(fix)

    report = {"fixes": len(fixes), "files": [], "applied": 0, "refused_files": 0}
    for (repo, rel), pairs in by_file.items():
        path = Path(roots[repo]) / rel
        text = path.read_text(encoding="utf-8")
        checks = []
        for fix in pairs:
            checks.append(
                {
                    "finding": fix["finding"],
                    "old_count": text.count(fix["old"]),
                    "new_count": text.count(fix["new"]),
                    "ok": text.count(fix["old"]) == fix.get("old_count", 1) and text.count(fix["new"]) == fix.get("new_count", 0),
                }
            )
        row = {"repo": repo, "file": rel, "path": str(path), "pairs": checks, "all_hold": all(check["ok"] for check in checks)}
        if row["all_hold"] and args.apply:
            for fix in pairs:
                if text.count(fix["old"]) != 1:
                    raise SystemExit(f"{path}: {fix['finding']} no longer occurs once after an earlier pair")
                text = text.replace(fix["old"], fix["new"], 1)
            path.write_text(text, encoding="utf-8")
            after = path.read_text(encoding="utf-8")
            row["after"] = [{"finding": fix["finding"], "old_gone": after.count(fix["old"]) == 0 or fix["old"] in fix["new"], "new_present": fix["new"] in after} for fix in pairs]
            row["applied"] = all(item["old_gone"] and item["new_present"] for item in row["after"])
            report["applied"] += len(pairs) if row["applied"] else 0
        elif not row["all_hold"]:
            report["refused_files"] += 1
        report["files"].append(row)
        state = "APPLIED" if row.get("applied") else ("HOLDS" if row["all_hold"] else "REFUSED")
        print(f"{state:8} {repo}:{rel} {[check['finding'] for check in checks]}")
    args.out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"pairs {report['fixes']}, applied {report['applied']}, files refused {report['refused_files']}")
    return 0 if report["refused_files"] == 0 and (not args.apply or report["applied"] == report["fixes"]) else 1


if __name__ == "__main__":
    sys.exit(main())
