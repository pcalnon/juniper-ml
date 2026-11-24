"""
List every pull request number the rendered texts cite (#N and juniper-ml#N) and read its state with gh
(claims lens, session 8). Read-only.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round-2 disposition, ml-tests carrier validation (claims lens)
"""

import argparse
import json
import re
import subprocess  # nosec B404 - fixed argv: gh pr view, read-only
import sys
from pathlib import Path

CITE = re.compile(r"(?:juniper-ml)?#(\d{3,5})\b")


def main() -> int:
    parser = argparse.ArgumentParser(description="Read the state of every cited pull request.")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--skip", type=int, action="append", default=[])
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    numbers = set()
    for path in args.files:
        numbers.update(int(n) for n in CITE.findall(path.read_text(errors="replace")))
    rows = []
    for number in sorted(numbers - set(args.skip)):
        done = subprocess.run(  # nosec B603 B607
            ["gh", "pr", "view", str(number), "--repo", "pcalnon/juniper-ml", "--json", "number,state,isDraft,title,mergedAt"],
            capture_output=True,
            check=False,
        )
        row = json.loads(done.stdout.decode()) if done.returncode == 0 else {"number": number, "error": done.stderr.decode(errors="replace").strip()[:200]}
        rows.append(row)
        print(json.dumps(row))
    if args.out:
        with args.out.open("w") as handle:
            json.dump(rows, handle, indent=1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
