#!/usr/bin/env python3
"""
List every #N the ml-docs carrier's texts (and its manifest's "carried" table, which the close comments are
generated from) cite, and read each one's state, title and merge time from GitHub, read-only.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation (Cursor flood-4 session 8: the ml-docs carrier's claims-lens validation, check E)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/ml-docs-s8/ (the validator's deliverables)

Only ``gh pr view`` / ``gh issue view`` reads are made. Run it outside an environment whose session bus is
disabled: gh reads its token from the desktop keyring.

Usage:
  2026-11-14_flood4r2_val_ml-docs_cited_prs.py --deliverables <dir> --docs-diff <file> --out <report.json>
"""

import argparse
import json
import re
import subprocess
from pathlib import Path

TEXTS = ("pr_title.txt", "pr_body.txt", "commit_body.txt", "changelog_entry.txt")
NUM_RE = re.compile(r"#(\d{3,5})\b")


def view(number: int) -> dict:
    fields = "number,title,state,mergedAt"
    done = subprocess.run(["gh", "pr", "view", str(number), "--repo", "pcalnon/juniper-ml", "--json", fields], capture_output=True, text=True, check=False)
    if done.returncode == 0:
        return {"kind": "pr", **json.loads(done.stdout)}
    done = subprocess.run(["gh", "issue", "view", str(number), "--repo", "pcalnon/juniper-ml", "--json", "number,title,state"], capture_output=True, text=True, check=False)
    if done.returncode == 0:
        return {"kind": "issue", **json.loads(done.stdout)}
    return {"kind": "missing", "number": number, "stderr": done.stderr.strip()[:200]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deliverables", required=True)
    ap.add_argument("--docs-diff", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    where: dict[int, list[str]] = {}
    root = Path(args.deliverables)
    for name in TEXTS:
        for n in NUM_RE.findall((root / name).read_text(encoding="utf-8")):
            where.setdefault(int(n), []).append(name)
    with open(root / "manifest.json", encoding="utf-8") as fh:
        carried = json.load(fh)["carried"]
    for n in NUM_RE.findall(json.dumps(carried)):
        where.setdefault(int(n), []).append("manifest.carried")
    added = "\n".join(line for line in Path(args.docs_diff).read_text(encoding="utf-8").splitlines() if line.startswith("+"))
    for n in NUM_RE.findall(added):
        where.setdefault(int(n), []).append("docs(+lines)")
    rows = []
    for number in sorted(where):
        row = view(number)
        row["cited_in"] = sorted(set(where[number]))
        rows.append(row)
        print(number, row.get("kind"), row.get("state"), (row.get("mergedAt") or "")[:16], row["cited_in"], "|", (row.get("title") or "")[:70])
    Path(args.out).write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
