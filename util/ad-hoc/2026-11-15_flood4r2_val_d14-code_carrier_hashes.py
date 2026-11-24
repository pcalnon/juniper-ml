"""
Hash every file of the two D-14 carriers against the sha256 their builder recorded in manifest.json.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (flood-4 round-2 validation, D-14 code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 disposition, D-14 (service-core resume cursor rules + shared answer table)

Usage: python3 <this file> [--out <json path>]
Reads only. Prints one line per file (OK / DIFFERS / MISSING) and exits 1 if any file differs.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
ML_CARRIER = JUNIPER / "juniper-ml" / ".claude" / "worktrees" / "agent-aa1160aea3f9c907d"
CASCOR_CARRIER = JUNIPER / "worktrees" / "juniper-cascor--test--ws-resume-shared-answer-table--20261115-0558--a1b0409d"


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def check(root: Path, entries: list) -> list:
    rows = []
    for entry in entries:
        target = root / entry["path"]
        if not target.is_file():
            rows.append({"path": entry["path"], "recorded": entry["sha256"], "actual": None, "verdict": "MISSING"})
            continue
        actual = sha256_of(target)
        verdict = "OK" if actual == entry["sha256"] else "DIFFERS"
        rows.append({"path": entry["path"], "recorded": entry["sha256"], "actual": actual, "verdict": verdict})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    report = {}
    for name, root in (("juniper-ml", ML_CARRIER), ("juniper-cascor", CASCOR_CARRIER)):
        with open(root / "tmp" / "flood4-fix" / "d14-resume" / "manifest.json", encoding="utf-8") as handle:
            manifest = json.load(handle)
        entries = list(manifest.get("files", [])) + list(manifest.get("provenance_helpers", []))
        report[name] = {"root": str(root), "base_sha": manifest.get("base_sha"), "rows": check(root, entries)}
    bad = 0
    for name, block in report.items():
        for row in block["rows"]:
            print(f"{name}\t{row['verdict']}\t{row['path']}\t{(row['actual'] or '-')[:16]}")
            bad += row["verdict"] != "OK"
    if args.out is not None:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
            handle.write("\n")
    print(f"files not matching their recorded sha256: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
