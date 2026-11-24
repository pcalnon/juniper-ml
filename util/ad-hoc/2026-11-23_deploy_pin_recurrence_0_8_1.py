#!/usr/bin/env python3
"""Make juniper-deploy's edits for its juniper-recurrence 0.8.0 -> 0.8.1 pin, into copies, for a signed PR.

Project: juniper-ml
Sub-Project: ad-hoc tooling (R-OBS-SC-2 follow-ups: the items left with the Overtoad)
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc -- one-off (the file edits of the juniper-deploy recurrence pin PR)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_deploy_pin_cascor_0_14_0_canopy_0_10_0.py (the precedent this follows);
         juniper-deploy#257 (the 0.8.0 pin, whose prose sites this moves); util/open_signed_pr.py (which lands the
         copies as one GitHub-signed commit);
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_r-obs-sc-2-cascor-one-artifact-landed-ports-plan-v1-15-17-next.md
         ("Still open with the Overtoad": juniper-deploy's juniper-recurrence:0.8.0 pin)

Why
---
juniper-deploy#278 left ``docker-compose.yml`` at ``juniper-recurrence:0.8.0`` while 0.8.1 is published, so
``scripts/verify_published_images.py --fail-on-stale`` exits 1 on every run. The Overtoad ruled on 2026-11-23 to move it
("Move it now"). A juniper-ml session cannot commit in a juniper-deploy checkout, so this edits copies of the files
taken from juniper-deploy's ``main``, and ``util/open_signed_pr.py`` uploads them. Each edit replaces exact text with an
exact count, so a ``main`` that moved under the copies refuses instead of producing a partial pin:

- ``docker-compose.yml``: the ``image:`` line, and the snapshot comment that names the pinned image;
- ``README.md``: the snapshot paragraph's pinned image, and its revision-label example;
- ``docs/REFERENCE.md``: the ``JUNIPER_RECURRENCE_SNAPSHOTS_DIR`` row;
- ``docs/USER_MANUAL.md``: the snapshot smoke's entry;
- ``scripts/test_recurrence_snapshots.sh``: its header comment;
- ``CHANGELOG.md``: the entry text (a file this script does not write) goes first under ``[Unreleased]`` / ``### Changed``.

The Helm chart carries no recurrence image (``k8s/helm/juniper/values.yaml``), as juniper-deploy#257 recorded.

Usage
-----
    python3 util/ad-hoc/2026-11-23_deploy_pin_recurrence_0_8_1.py --src DIR --out DIR --entry FILE

``--src`` holds juniper-deploy's files at the commit the PR is based on; ``--out`` receives the edited copies, at
their repository paths. Exit 0 when every edit applied exactly; 2 (writing nothing) when any count is off.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

EDITS: dict[str, tuple[tuple[str, str, int], ...]] = {
    "docker-compose.yml": (
        ("    image: ghcr.io/pcalnon/juniper-recurrence:0.8.0\n", "    image: ghcr.io/pcalnon/juniper-recurrence:0.8.1\n", 1),
        ("# The pinned 0.8.0 image carries the snapshot routes", "# The pinned 0.8.1 image carries the snapshot routes", 1),
    ),
    "README.md": (
        ("The pinned `juniper-recurrence:0.8.0` image **carries the snapshot routes**", "The pinned `juniper-recurrence:0.8.1` image **carries the snapshot routes**", 1),
        ("(the published 0.8.0 is `6a98515e`; 0.7.0 was `5c576da4`)", "(the published 0.8.1 is `2a467adb`; 0.8.0 was `6a98515e`)", 1),
    ),
    "docs/REFERENCE.md": (("Read by the pinned 0.8.0 image (the routes shipped in 0.6.0)", "Read by the pinned 0.8.1 image (the routes shipped in 0.6.0)", 1),),
    "docs/USER_MANUAL.md": (("so it needs 0.6.0 or later; the pinned 0.8.0 carries them.", "so it needs 0.6.0 or later; the pinned 0.8.1 carries them.", 1),),
    "scripts/test_recurrence_snapshots.sh": (("pinned juniper-recurrence:0.8.0 carries the snapshot routes, which shipped in 0.6.0", "pinned juniper-recurrence:0.8.1 carries the snapshot routes, which shipped in 0.6.0", 1),),
}
CHANGED_ANCHOR = "\n### Changed\n\n"


def apply(text: str, edits: tuple, name: str, errors: list[str]) -> str:
    for old, new, count in edits:
        seen = text.count(old)
        if seen != count:
            errors.append(f"{name}: {old.strip()!r} found {seen} times, expected {count}")
            continue
        text = text.replace(old, new)
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--src", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--entry", required=True, type=Path, help="the CHANGELOG entry: markdown list item(s), ending in a newline")
    args = ap.parse_args()
    errors: list[str] = []
    out: dict[str, str] = {}
    for rel, edits in EDITS.items():
        out[rel] = apply((args.src / rel).read_text(encoding="utf-8"), edits, rel, errors)
    changelog = (args.src / "CHANGELOG.md").read_text(encoding="utf-8")
    unreleased = changelog.find("\n## [Unreleased]\n")
    next_release = changelog.find("\n## [", unreleased + 1)
    at = changelog.find(CHANGED_ANCHOR, unreleased, next_release)
    entry = args.entry.read_text(encoding="utf-8")
    if unreleased < 0 or at < 0:
        errors.append("CHANGELOG.md: no '### Changed' under '## [Unreleased]'")
    elif not entry.startswith("- ") or not entry.endswith("\n"):
        errors.append("the entry must start with '- ' and end with a newline")
    else:
        cut = at + len(CHANGED_ANCHOR)
        out["CHANGELOG.md"] = changelog[:cut] + entry + changelog[cut:]
    if errors:
        print("\n".join(f"refusing: {e}" for e in errors))
        return 2
    for rel, text in out.items():
        dest = args.out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text, encoding="utf-8")
        print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
