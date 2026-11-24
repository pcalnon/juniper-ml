#!/usr/bin/env python3
"""
Write the ml-docs carrier's own diff (its files on disk against a base commit's blobs) without running git in the
carrier's worktree, and say what main changed in the same files since that base.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (Cursor flood-4 session 8: the ml-docs carrier's claims-lens validation, checks A and C)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/ml-docs-s8/ (the validator's deliverables)

Run from a juniper-ml checkout that shares the carrier's object store (any juniper-ml worktree does).

Usage:
  2026-11-14_flood4r2_val_ml-docs_carrierdiff.py --carrier <dir> --base <sha> --main origin/main --out <dir> <path> ...
"""

import argparse
import json
import subprocess
from pathlib import Path


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], capture_output=True, check=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--carrier", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--main", default="origin/main")
    ap.add_argument("--out", required=True)
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()
    out = Path(args.out)
    (out / "base").mkdir(parents=True, exist_ok=True)
    main_sha = git("rev-parse", args.main).stdout.decode().strip()
    summary = {"base": args.base, "main": main_sha, "files": []}
    combined = []
    for rel in args.paths:
        base_copy = out / "base" / rel.replace("/", "__")
        base_copy.write_bytes(git("show", f"{args.base}:{rel}").stdout)
        diff = git("diff", "--no-index", "--no-color", "-U3", str(base_copy), str(Path(args.carrier) / rel)).stdout.decode("utf-8")
        combined.append(f"##### {rel}\n{diff}")
        main_stat = git("diff", "--numstat", args.base, main_sha, "--", rel).stdout.decode().strip()
        added = sum(1 for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in diff.splitlines() if line.startswith("-") and not line.startswith("---"))
        summary["files"].append({"path": rel, "carrier_added": added, "carrier_removed": removed, "main_changed_since_base": main_stat})
    (out / "carrier_vs_base.diff").write_text("\n".join(combined), encoding="utf-8")
    (out / "carrierdiff.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
