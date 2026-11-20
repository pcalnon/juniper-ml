#!/usr/bin/env python3
"""Make juniper-deploy's pin edits for juniper-cascor 0.14.0 and juniper-canopy 0.10.0, into copies, for a signed PR.

Project: juniper-ml
Sub-Project: ad-hoc tooling (R-OBS-SC-2 follow-ups)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (the file edits of the juniper-deploy pin PR)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-deploy#266 (the precedent, cascor 0.13.0); util/open_signed_pr.py (which lands the copies as one
         GitHub-signed commit); util/ad-hoc/2026-11-15_probe_published_images_cascor_0_14_0_canopy_0_10_0.py (the images);
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-15_r-obs-sc-2-cascor-0-14-0-canopy-0-10-0-at-pypi-gates-guard-pr-plan-v1-15-16-next.md

Why
---
The juniper-ml session that lands this cannot commit in a juniper-deploy checkout, so it edits copies of the three files
taken from juniper-deploy's ``main`` and uploads them with ``util/open_signed_pr.py``. Each pin is replaced by its exact
text with an exact count, so a ``main`` that moved under the copies refuses instead of producing a partial pin:

- ``docker-compose.yml``: ``juniper-cascor:0.13.0`` twice and ``juniper-canopy:0.9.0`` three times;
- ``k8s/helm/juniper/values.yaml``: each ``tag:`` line directly under its ``DEPLOY-15`` comment for that repository;
- ``CHANGELOG.md``: the entry text (a file this script does not write) goes first under ``[Unreleased]`` / ``### Changed``.

Usage
-----
    python3 util/ad-hoc/2026-11-15_deploy_pin_cascor_0_14_0_canopy_0_10_0.py --src DIR --out DIR --entry FILE

``--src`` holds juniper-deploy's files at the commit the PR is based on; ``--out`` receives the three edited copies.
Exit 0 when every edit applied exactly; 2 (writing nothing) when any count is off.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

COMPOSE = (
    ("image: ghcr.io/pcalnon/juniper-cascor:0.13.0\n", "image: ghcr.io/pcalnon/juniper-cascor:0.14.0\n", 2),
    ("image: ghcr.io/pcalnon/juniper-canopy:0.9.0\n", "image: ghcr.io/pcalnon/juniper-canopy:0.10.0\n", 3),
)
_CASCOR_TAG = '    repository: juniper-cascor\n    # DEPLOY-15: pinned; bump with juniper-cascor releases.\n    tag: "{}"\n'
_CANOPY_TAG = '    repository: juniper-canopy\n    # DEPLOY-15: pinned; bump with juniper-canopy releases.\n    tag: "{}"\n'
VALUES = (
    (_CASCOR_TAG.format("0.13.0"), _CASCOR_TAG.format("0.14.0"), 1),
    (_CANOPY_TAG.format("0.9.0"), _CANOPY_TAG.format("0.10.0"), 1),
)
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
    out = {}
    out["docker-compose.yml"] = apply((args.src / "docker-compose.yml").read_text(encoding="utf-8"), COMPOSE, "docker-compose.yml", errors)
    out["values.yaml"] = apply((args.src / "k8s/helm/juniper/values.yaml").read_text(encoding="utf-8"), VALUES, "values.yaml", errors)
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
    args.out.mkdir(parents=True, exist_ok=True)
    for name, text in out.items():
        (args.out / name).write_text(text, encoding="utf-8")
        print(f"wrote {args.out / name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
