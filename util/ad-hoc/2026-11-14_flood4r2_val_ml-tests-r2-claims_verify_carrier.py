"""
Verify the ml-tests round-2 carrier's files against the sha256 its manifest records (claims lens, session 8).

Reads the carrier's tmp/flood4r2/ml-tests/r2/manifest.json, hashes every listed file in the carrier
(read-only), and prints one line per file that differs or is missing, then a summary line.
Optionally writes the full per-file result as JSON with --out.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round-2 disposition, ml-tests carrier validation (claims lens)
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify carrier files against the manifest sha256.")
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--manifest", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    manifest_path = args.manifest or args.carrier / "tmp/flood4r2/ml-tests/r2/manifest.json"
    with manifest_path.open() as handle:
        manifest = json.load(handle)
    rows = []
    bad = 0
    for entry in manifest["files"]:
        target = args.carrier / entry["path"]
        if not target.exists():
            rows.append({"path": entry["path"], "expected": entry["sha256"], "actual": None, "ok": False})
            bad += 1
            print(f"MISSING {entry['path']}")
            continue
        actual = sha256_of(target)
        ok = actual == entry["sha256"]
        rows.append({"path": entry["path"], "expected": entry["sha256"], "actual": actual, "ok": ok})
        if not ok:
            bad += 1
            print(f"DIFFERS {entry['path']} expected {entry['sha256'][:16]} actual {actual[:16]}")
    print(f"{len(rows)} manifest files; differing or missing: {bad}; manifest sha256 {sha256_of(manifest_path)[:16]}")
    if args.out:
        with args.out.open("w") as handle:
            json.dump({"manifest": str(manifest_path), "rows": rows, "bad": bad}, handle, indent=1)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
