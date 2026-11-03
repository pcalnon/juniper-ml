#!/usr/bin/env python3
"""
SHA-pin ``actions/checkout`` in an extracted repository's ``agents-md-touch-up.yml`` and record it in its CHANGELOG.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-03
Status: ad-hoc — one-off (flood-3: the seven remaining tag-only copies, owner ruling 2026-11-03)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-03_fetch_main_tarballs.py (makes the input trees);
         notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md (§9); juniper-data#503

    python3 -I util/ad-hoc/2026-11-03_pin_agents_md_touch_up_checkout.py <repo-tree> [<repo-tree> ...]

Each tree is edited in place. The workflow must hold exactly one ``uses: actions/checkout@v7.0.1`` line, and the
CHANGELOG an ``## [Unreleased]`` section; anything else is refused (exit 1) with the tree left untouched. The entry
goes first under the section's ``### Changed``, which is created in Keep-a-Changelog order when absent.
"""

from __future__ import annotations

import sys
from pathlib import Path

TAG_LINE = "uses: actions/checkout@v7.0.1"
PIN_LINE = "uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1"
ORDER = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]
ENTRY = """\
- **`agents-md-touch-up.yml` pins `actions/checkout` to a commit SHA (owner ruling 2026-11-03).** It checked out with
  the `v7.0.1` tag, the only tag-only `actions/checkout` in `.github/workflows/`. It now uses
  `3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1`, the commit that tag resolves to and the pin every other
  workflow here uses, so behaviour is unchanged. A census of the nine Juniper repositories' `main` on 2026-11-01 found
  249 `actions/checkout` uses, 242 pinned to that SHA; the seven tag-only ones were this workflow's copies, one per
  repository. juniper-data#503 pinned juniper-data's, and this change is one of the seven that pin the rest.
"""


def edit_changelog(text: str) -> str:
    lines = text.split("\n")
    start = next(i for i, ln in enumerate(lines) if ln.startswith("## [Unreleased]"))
    end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
    heads = {lines[i][4:].strip(): i for i in range(start + 1, end) if lines[i].startswith("### ")}
    entry = ENTRY.rstrip("\n").split("\n")
    if "Changed" in heads:
        at = heads["Changed"] + 1
        while at < end and not lines[at].strip():
            at += 1
        return "\n".join(lines[:at] + entry + lines[at:])
    later = [heads[h] for h in ORDER[ORDER.index("Changed") + 1 :] if h in heads]
    at = min(later) if later else end
    return "\n".join(lines[:at] + ["### Changed", ""] + entry + [""] + lines[at:])


def pin(tree: Path) -> None:
    wf = tree / ".github/workflows/agents-md-touch-up.yml"
    cl = tree / "CHANGELOG.md"
    wf_text = wf.read_text()
    if wf_text.count(TAG_LINE) != 1:
        raise SystemExit(f"{tree}: expected one {TAG_LINE!r}, found {wf_text.count(TAG_LINE)}")
    new_cl = edit_changelog(cl.read_text())
    wf.write_text(wf_text.replace(TAG_LINE, PIN_LINE))
    cl.write_text(new_cl)
    print(f"{tree.name}\tpinned")


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__, file=sys.stderr)
        return 1
    for arg in argv[1:]:
        pin(Path(arg))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
