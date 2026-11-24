"""
Compare every file the ml-tests round-2 carrier's manifest lists with its recorded sha256 (read-only).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (tests-lens validator agent, flood-4 session 7)
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2, the ml-tests carrier)

Usage:
    python3 <this file> --carrier <carrier worktree> --manifest <manifest.json> --out <result.json> [--tree <other tree>]

With --tree the same paths are hashed in another tree too (a landed copy) and compared with the manifest's values.
Exit 0 when every file matches, 1 otherwise. Reads only; never runs the version-control tool.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--carrier", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--tree", help="another tree to hash the same paths in")
    args = parser.parse_args(argv)

    with open(args.manifest, encoding="utf-8") as fh:
        manifest = json.load(fh)

    carrier = Path(args.carrier)
    rows = []
    mismatches = 0
    for entry in manifest["files"]:
        rel = entry["path"]
        want = entry["sha256"]
        target = carrier / rel
        got = sha256_of(target) if target.is_file() else None
        row = {"path": rel, "manifest": want, "carrier": got, "carrier_matches": got == want}
        if args.tree:
            other = Path(args.tree) / rel
            other_hash = sha256_of(other) if other.is_file() else None
            row["tree"] = other_hash
            row["tree_matches"] = other_hash == want
        if got != want:
            mismatches += 1
        rows.append(row)

    result = {
        "manifest": str(args.manifest),
        "manifest_status": manifest.get("status"),
        "base_sha": manifest.get("base_sha"),
        "files": len(rows),
        "carrier_mismatches": mismatches,
        "tree": args.tree,
        "tree_mismatches": sum(1 for row in rows if args.tree and not row["tree_matches"]),
        "rows": rows,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
        fh.write("\n")
    print("files=%d carrier_mismatches=%d tree_mismatches=%d" % (len(rows), mismatches, result["tree_mismatches"]))
    for row in rows:
        if not row["carrier_matches"]:
            print("CARRIER MISMATCH", row["path"], row["carrier"])
        if args.tree and not row["tree_matches"]:
            print("TREE DIFFERS", row["path"], row["tree"])
    return 0 if mismatches == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
