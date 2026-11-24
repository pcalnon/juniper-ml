"""
Hash every file of a D-14 carrier (sha256) and record the result: a JSON file and one clock-stamped line per file in
each PROGRESS.txt named.

The file list comes from a carrier manifest (its ``files`` and ``provenance_helpers`` entries, repository-relative) or
from ``--paths``. With ``--expect`` the manifest's recorded sha256 values are compared too, and the exit status is 1
when any file differs from its record or is missing.

Usage:
    python3 util/ad-hoc/2026-11-16_flood4r2_d14_hashes.py --label <what> --root <carrier root>
        (--manifest <manifest.json> | --paths <p> [<p> ...]) [--expect] --out <hashes.json>
        [--progress <PROGRESS.txt> ...]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the owner's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table)
"""

import argparse
import datetime
import hashlib
import json
import sys
from pathlib import Path


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--label", required=True)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--paths", nargs="*", default=[])
    parser.add_argument("--expect", action="store_true", help="compare with the manifest's recorded sha256")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--progress", nargs="*", default=[], type=Path)
    args = parser.parse_args()

    recorded: dict[str, str] = {}
    paths: list[str] = list(args.paths)
    if args.manifest is not None:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        for entry in list(manifest.get("files", [])) + list(manifest.get("provenance_helpers", [])):
            paths.append(entry["path"])
            if entry.get("sha256"):
                recorded[entry["path"]] = entry["sha256"]

    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    differs = 0
    for rel in paths:
        target = args.root / rel
        row = {"path": rel, "exists": target.is_file(), "sha256": sha256_of(target) if target.is_file() else None}
        if args.expect:
            row["recorded"] = recorded.get(rel)
            row["matches_record"] = row["sha256"] is not None and row["sha256"] == recorded.get(rel)
            differs += 0 if row["matches_record"] else 1
        rows.append(row)

    result = {"label": args.label, "root": str(args.root), "at": stamp, "files": rows}
    if args.expect:
        result["differs"] = differs
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")

    lines = [f"{stamp} HASHES {args.label} ({len(rows)} files, root {args.root}):\n"]
    for row in rows:
        verdict = ""
        if args.expect:
            verdict = " = record" if row["matches_record"] else " DIFFERS FROM RECORD"
        lines.append(f"{stamp}   {row['sha256'] or 'MISSING'}  {row['path']}{verdict}\n")
    for progress in args.progress:
        with progress.open("a", encoding="utf-8") as handle:
            handle.writelines(lines)
    print("".join(lines), end="")
    return 1 if differs else 0


if __name__ == "__main__":
    sys.exit(main())
