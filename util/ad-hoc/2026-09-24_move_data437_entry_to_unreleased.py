#!/usr/bin/env python3
"""
Move juniper-data#437's CHANGELOG entry out of the released [0.16.0] section and into [Unreleased].

Project: juniper-ml
Sub-Project: ad-hoc tooling (cross-repo release hygiene, APD-ML-007's failure class)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use; writes one file for util/push_signed_commit.py to upload
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

juniper-data v0.16.0 was tagged at `39d1cab2` at 08:52Z on 2026-09-24. juniper-data#437 (the
`equities_seq` relabel, generator 6.0.0) merged at 09:14Z and filed its entry under `## [0.16.0]`, so
main's CHANGELOG credits 0.16.0 with code the tag does not carry, and the next release's notes, rendered
from `[Unreleased]`, would leave #437 out -- the release-notes drift APD-ML-007 records.

This reads the CHANGELOG at a juniper-data ref (the head of juniper-data#438, which fixes forward the
same release), removes #437's bullet from [0.16.0]'s `### Changed`, and files it under [Unreleased] in a
`### Changed` block placed in Keep-a-Changelog order. It PROVES the result: the new [0.16.0] section is
byte-identical to the [0.16.0] section at the `v0.16.0` tag, and the moved bullet is unchanged apart from
the one dated note it gains.

Usage: python3 util/ad-hoc/2026-09-24_move_data437_entry_to_unreleased.py --ref <sha> --out <path>
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

REPO = "pcalnon/juniper-data"
TAG = "v0.16.0"
START = "- **`equities_seq` is declared `regression`, not `classification`, and its `generator_version`"
NEXT = "- **The access counters are no longer part of any metadata representation** (APD-DATA-032)."
NOTE = "  - *Moved here from `[0.16.0]`: #437 merged at 09:14Z on 2026-09-24, after `v0.16.0` was tagged at `39d1cab2`, so 0.16.0 does not carry it.*"


def fetch(ref: str) -> str:
    return subprocess.run(["gh", "api", f"repos/{REPO}/contents/CHANGELOG.md?ref={ref}", "-H", "Accept: application/vnd.github.raw"], check=True, capture_output=True, text=True).stdout


def section(lines: list[str], heading_prefix: str) -> tuple[int, int]:
    """[start, end) of the `## ` section whose heading starts with the prefix."""
    starts = [i for i, line in enumerate(lines) if line.startswith(heading_prefix)]
    if len(starts) != 1:
        raise SystemExit(f"REFUSED: {len(starts)} headings start with {heading_prefix!r}")
    end = next((j for j in range(starts[0] + 1, len(lines)) if lines[j].startswith("## ")), len(lines))
    return starts[0], end


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--ref", required=True, help="the juniper-data commit whose CHANGELOG to rewrite")
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    lines = fetch(args.ref).split("\n")
    tagged = fetch(TAG).split("\n")

    # 1. Cut the bullet out of [0.16.0].
    s, e = section(lines, "## [0.16.0]")
    starts = [i for i in range(s, e) if lines[i] == START]
    ends = [i for i in range(s, e) if lines[i] == NEXT]
    if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]:
        raise SystemExit("REFUSED: #437's bullet is not where it was expected in [0.16.0]")
    bullet = lines[starts[0]:ends[0]]
    del lines[starts[0]:ends[0]]

    # 2. Proof: [0.16.0] is now exactly what the tag carries.
    s, e = section(lines, "## [0.16.0]")
    ts, te = section(tagged, "## [0.16.0]")
    if lines[s:e] != tagged[ts:te]:
        raise SystemExit("REFUSED: after the move, [0.16.0] still differs from the v0.16.0 tag's section")

    # 3. File it under [Unreleased], in a `### Changed` block after `### Added` and before `### Fixed`.
    us, ue = section(lines, "## [Unreleased]")
    if any(lines[i] == "### Changed" for i in range(us, ue)):
        raise SystemExit("REFUSED: [Unreleased] already has a ### Changed block; merge by hand")
    fixed = [i for i in range(us, ue) if lines[i] == "### Fixed"]
    if len(fixed) != 1:
        raise SystemExit("REFUSED: [Unreleased] has no single ### Fixed block to insert before")
    if lines[fixed[0] - 1] != "":
        raise SystemExit("REFUSED: no blank line before [Unreleased]'s ### Fixed")
    text = list(bullet)
    while text and text[-1] == "":
        text.pop()
    block = ["### Changed", "", *text, NOTE, ""]
    lines[fixed[0]:fixed[0]] = block
    if block[2:-2] != [line for line in bullet if line != ""] and block[2:-2] != text:
        raise SystemExit("REFUSED: the moved bullet's text changed")
    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"moved {len(bullet)} lines of #437's entry into [Unreleased] ### Changed; [0.16.0] == the {TAG} tag's section, byte for byte -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
