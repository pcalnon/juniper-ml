"""
Assemble the N-4 round-2 carrier: copy the round-1 carrier's files onto current main, three-way where main moved.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 fix N-4, round 2 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8)

Reads the round-1 manifest (tmp/flood4-fix/n4/manifest.json in the round-1 carrier worktree, a sibling of this one
under .claude/worktrees/), checks each listed file's sha256 against it, and for each file:

- main did not change it since the round-1 base (same blob at the base and at HEAD, or absent at both): the carrier's
  copy is copied in;
- main changed it: `git merge-file -p <carrier's copy> <base's copy> <main's copy>` rebuilds it, and the conflict count
  is recorded (the copy is NOT written when there is a conflict).

Run from anywhere: `python3 util/ad-hoc/2026-11-11_flood4r2_n4-r2_assemble.py [--write]`. Without `--write` it only
reports, into tmp/flood4-fix/n4-r2/assemble-report.json. It never runs git outside this worktree.

It was run once with `--write`, at the start of round 2, on main 9063ebf3 (the record is assemble.json): only
CHANGELOG.md had moved since the round-1 base. Three of the fourteen files it copied were dropped later in the round
as superseded (round 1's mutation, doc-apply and manifest helpers), and the others were then edited by hand, so
writing again would undo round 2.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ROUND1 = REPO.parent / "agent-ab006c2d3dc68fe8c"
ROUND1_MANIFEST = ROUND1 / "tmp" / "flood4-fix" / "n4" / "manifest.json"
SCRATCH = REPO / "tmp" / "flood4-fix" / "n4-r2"


def _git(*args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, check=False)


def _blob_at(rev: str, path: str) -> bytes | None:
    done = _git("show", f"{rev}:{path}")
    return done.stdout if done.returncode == 0 else None


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--write", action="store_true", help="copy the files in (overwrites the worktree's copies); without it, only report")
    args = parser.parse_args()

    manifest = json.loads(ROUND1_MANIFEST.read_text(encoding="utf-8"))
    base = manifest["base_sha"]
    head = _git("rev-parse", "HEAD").stdout.decode().strip()
    SCRATCH.mkdir(parents=True, exist_ok=True)
    threeway_dir = SCRATCH / "threeway"
    threeway_dir.mkdir(exist_ok=True)

    records = []
    problems = 0
    for entry in manifest["files"]:
        path = entry["path"]
        carrier_bytes = (ROUND1 / path).read_bytes()
        record = {"path": path, "round1_status": entry["status"], "carrier_sha256": _sha256(carrier_bytes)}
        record["carrier_matches_round1_manifest"] = record["carrier_sha256"] == entry["sha256"]
        if not record["carrier_matches_round1_manifest"]:
            problems += 1
        base_bytes = _blob_at(base, path)
        main_bytes = _blob_at(head, path)
        record["at_base"] = None if base_bytes is None else _sha256(base_bytes)
        record["at_main"] = None if main_bytes is None else _sha256(main_bytes)
        if base_bytes == main_bytes:
            record["how"] = "copied (main unchanged since the round-1 base)"
            result = carrier_bytes
        elif base_bytes is None or main_bytes is None:
            record["how"] = "REFUSED: added or deleted on one side only"
            problems += 1
            records.append(record)
            continue
        else:
            stem = path.replace("/", "__")
            carrier_copy = threeway_dir / f"{stem}.carrier"
            base_copy = threeway_dir / f"{stem}.base"
            main_copy = threeway_dir / f"{stem}.main"
            carrier_copy.write_bytes(carrier_bytes)
            base_copy.write_bytes(base_bytes)
            main_copy.write_bytes(main_bytes)
            merged = _git("merge-file", "-p", str(carrier_copy), str(base_copy), str(main_copy))
            record["how"] = "three-way: git merge-file -p <carrier> <base> <main>"
            record["merge_file_exit"] = merged.returncode
            record["conflicts"] = merged.returncode if merged.returncode >= 0 else None
            result = merged.stdout
            (threeway_dir / f"{stem}.merged").write_bytes(result)
            if merged.returncode != 0:
                problems += 1
                record["written"] = False
                records.append(record)
                continue
        record["result_sha256"] = _sha256(result)
        record["written"] = args.write
        if args.write:
            target = REPO / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(result)
        records.append(record)

    out = {"round1_base": base, "main_head": head, "wrote": args.write, "files": records, "problems": problems}
    (SCRATCH / ("assemble.json" if args.write else "assemble-report.json")).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    for record in records:
        print(f"{record['how']:<60} {record['path']}")
    print(f"problems: {problems}; main HEAD {head}; round-1 base {base}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
