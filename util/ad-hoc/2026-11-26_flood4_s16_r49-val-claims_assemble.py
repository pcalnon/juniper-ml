#!/usr/bin/env python3
"""
Resolve the one CHANGELOG conflict of carrier r49 on today's juniper-canopy main (r49's entry above #845's) and check it.

Input: the output of `git merge-file -L main -L base -L carrier <main copy> <base> <carrier>` (one conflict block, main's
side first), the carrier's CHANGELOG and main's CHANGELOG. Output: the resolved CHANGELOG, with the carrier's side placed
BEFORE main's side (newest first), and a JSON report: no conflict markers left; the carrier's entry block byte-identical
to the carrier's own; removing that block gives main's CHANGELOG back exactly; one `## [Unreleased]`, and the entry is
the first bullet of the first `### Fixed` under it, above main's previous first bullet.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-26
Status: ad-hoc -- investigation (flood-4 session 16, carrier r49 claims lens)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 49)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="resolve r49's CHANGELOG conflict, carrier entry first")
    ap.add_argument("--merged", required=True, help="git merge-file output with one conflict block")
    ap.add_argument("--carrier", required=True, help="the carrier's CHANGELOG.md")
    ap.add_argument("--main", required=True, help="main's CHANGELOG.md")
    ap.add_argument("--out", required=True, help="resolved CHANGELOG to write")
    ap.add_argument("--report", required=True, help="JSON report to write")
    args = ap.parse_args()

    merged = Path(args.merged).read_text(encoding="utf-8").splitlines(keepends=True)
    starts = [i for i, ln in enumerate(merged) if ln.startswith("<<<<<<< ")]
    mids = [i for i, ln in enumerate(merged) if ln.rstrip("\n") == "======="]
    ends = [i for i, ln in enumerate(merged) if ln.startswith(">>>>>>> ")]
    report: dict = {"conflict_blocks": len(starts)}
    if not (len(starts) == len(mids) == len(ends) == 1):
        report["error"] = "expected exactly one conflict block"
        Path(args.report).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
        return 1
    s, m, e = starts[0], mids[0], ends[0]
    main_side = merged[s + 1 : m]
    carrier_side = merged[m + 1 : e]
    resolved = merged[:s] + carrier_side + main_side + merged[e + 1 :]
    Path(args.out).write_text("".join(resolved), encoding="utf-8")

    carrier = Path(args.carrier).read_text(encoding="utf-8").splitlines(keepends=True)
    main_cl = Path(args.main).read_text(encoding="utf-8").splitlines(keepends=True)
    text = "".join(resolved)
    report.update(
        {
            "conflict_lines": {"start": s + 1, "mid": m + 1, "end": e + 1},
            "main_side_lines": len(main_side),
            "carrier_side_lines": len(carrier_side),
            "markers_left": sum(1 for ln in resolved if ln.startswith(("<<<<<<< ", ">>>>>>> ")) or ln.rstrip("\n") == "======="),
            "carrier_block_in_carrier_file": "".join(carrier_side) in "".join(carrier),
            "carrier_block_first_line_in_resolved": s + 1,
            "removing_carrier_block_gives_main": "".join(merged[:s] + main_side + merged[e + 1 :]) == "".join(main_cl),
            "unreleased_headings": sum(1 for ln in resolved if ln.startswith("## [Unreleased]")),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "lines": len(resolved),
        }
    )
    unreleased = next(i for i, ln in enumerate(resolved) if ln.startswith("## [Unreleased]"))
    next_release = next(i for i, ln in enumerate(resolved) if i > unreleased and ln.startswith("## ["))
    fixed = [i for i in range(unreleased, next_release) if resolved[i].rstrip("\n") == "### Fixed"]
    report["fixed_headings_in_unreleased"] = len(fixed)
    report["unreleased_group_headings"] = [resolved[i].rstrip("\n") for i in range(unreleased, next_release) if resolved[i].startswith("### ")]
    if fixed:
        first_bullet = next(i for i in range(fixed[0] + 1, next_release) if resolved[i].startswith("- "))
        bullets = [i for i in range(fixed[0] + 1, next_release) if resolved[i].startswith("- ") and not resolved[i].startswith("### ")]
        report["first_fixed_bullet_line"] = first_bullet + 1
        report["first_fixed_bullet"] = resolved[first_bullet][:120]
        report["second_fixed_bullet"] = resolved[bullets[1]][:120] if len(bullets) > 1 else None
        report["carrier_entry_is_first_fixed_bullet"] = first_bullet == s
    Path(args.report).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0 if report["markers_left"] == 0 and report["carrier_block_in_carrier_file"] and report["removing_carrier_block_gives_main"] else 1


if __name__ == "__main__":
    sys.exit(main())
