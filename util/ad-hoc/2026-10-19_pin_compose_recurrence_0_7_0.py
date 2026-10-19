#!/usr/bin/env python3
"""Move juniper-deploy's Compose pin for juniper-recurrence from 0.6.1 to 0.7.0, with the prose that names it.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-19
Status: ad-hoc — one-off (the juniper-deploy pin PR for recurrence 0.7.0)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: P5 of notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md;
         juniper-deploy#251 (the 0.6.1 pin this follows, the same five files);
         util/ad-hoc/2026-10-19_raise_recurrence_floor_0_7_0.py (the juniper-ml extras raise taken with it)

Why this exists
---------------
juniper-recurrence 0.7.0 published on 2026-10-19 (PyPI, and GHCR tags ``0.7.0`` / ``0.7`` / ``latest`` at one
index digest, revision ``5c576da4``). juniper-deploy's ``docker-compose.yml`` pins the image by exact tag, and
four prose sites name the pinned version. Sibling-repo git is refused in agent sessions, so this edits a scratch
copy fetched from juniper-deploy ``main`` by the API, and the result lands through ``util/open_signed_pr.py``.

Every edit asserts its exact expected text and must match exactly once; "new present once" counts as applied. The
CHANGELOG entry goes first under ``[Unreleased]`` -> ``### Changed``, the pattern of juniper-deploy#251.

Usage
-----
    python3 util/ad-hoc/2026-10-19_pin_compose_recurrence_0_7_0.py --root <scratch juniper-deploy tree> --ml-pr <N> [--check]
"""

from __future__ import annotations

import argparse
from pathlib import Path

#: (relative path, exact old text, exact new text)
_EDITS: list[tuple[str, str, str]] = [
    ("docker-compose.yml", "    image: ghcr.io/pcalnon/juniper-recurrence:0.6.1\n", "    image: ghcr.io/pcalnon/juniper-recurrence:0.7.0\n"),
    (
        "docker-compose.yml",
        "      # The pinned 0.6.1 image carries the snapshot routes (shipped in 0.6.0, juniper-recurrence#172):",
        "      # The pinned 0.7.0 image carries the snapshot routes (shipped in 0.6.0, juniper-recurrence#172):",
    ),
    (
        "README.md",
        "The pinned `juniper-recurrence:0.6.1` image **carries the snapshot routes** (shipped in 0.6.0, juniper-recurrence#172)",
        "The pinned `juniper-recurrence:0.7.0` image **carries the snapshot routes** (shipped in 0.6.0, juniper-recurrence#172)",
    ),
    (
        "README.md",
        "(the published 0.6.1 is `cad03ed5`; 0.6.0 was `535d1e78`)",
        "(the published 0.7.0 is `5c576da4`; 0.6.1 was `cad03ed5`)",
    ),
    (
        "docs/REFERENCE.md",
        "Read by the pinned 0.6.1 image (the routes shipped in 0.6.0); images through 0.5.0 ignore it |",
        "Read by the pinned 0.7.0 image (the routes shipped in 0.6.0); images through 0.5.0 ignore it |",
    ),
    (
        "scripts/test_recurrence_snapshots.sh",
        "#    pinned juniper-recurrence:0.6.1 carries the snapshot routes, which shipped in 0.6.0",
        "#    pinned juniper-recurrence:0.7.0 carries the snapshot routes, which shipped in 0.6.0",
    ),
]

_PLAN = "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"
_MARKER = "**`juniper-recurrence` pinned to `0.7.0`**"
_ENTRY = f"""- {_MARKER} (P5 of juniper-ml
  `{_PLAN}`;
  approved 2026-10-19 with the session's merge approval, the ruling 0.7.0 reopened, taken with juniper-ml's
  `[recurrence]` floor moving to `>=0.7.0` in juniper-ml#ML_PR). The pin was `0.6.1`.
  - **What 0.7.0 is.** W5.8 (B), W5.9 and W5.10 of the plan: the service's `default_ridge` becomes
    `"gcv"` on juniper-recurrence-model 0.5.0, which standardises the linear readout's memory block with
    the train-fold statistics for any non-zero ridge (`ridge = 0` unchanged), so a `POST /v1/crossval`
    that names no ridge no longer blows up on the equities row (the W5.1 note's −2.1e4 becomes −0.195 on
    the E-H artifact); `POST /v1/train` and every crossval fold carry a `diagnostics` block (`readout`,
    `theta`, `ridge_mode` / `ridge_selected`, `gamma`, `gcv_at_edge` / `null_model`). Unlike 0.6.1 this
    changes the image's runtime: its lock pins model 0.5.0 (0.4.0 before). The snapshot routes, the auth
    posture, the port and the environment variables are unchanged.
  - **The image, verified on GHCR 2026-10-19**: tags `0.7.0` / `0.7` / `latest` resolve to one index,
    digest `sha256:8dbb693db50c6945fb8a7c8e2866a282dde7f9830b652c9c902c632d6bbd1acd`; linux/amd64
    `sha256:fbbd1c06…` and linux/arm64 `sha256:e60a91b0…`; `org.opencontainers.image.version` is `0.7.0`
    and `revision` is `5c576da4`, the `juniper-recurrence-v0.7.0` tag's commit. `publish-image.yml`
    (run 39194767477) is green.
  - **The Helm chart is untouched**: `k8s/helm/juniper/values.yaml` carries no recurrence image.
  - **Smokes not re-run for this pin.** This change's host cannot pull from GHCR. Both
    `scripts/test_recurrence_snapshots.sh` and `scripts/test_canopy_recurrence_smoke.sh` are owed on the
    0.7.0 image at the next bring-up on a host whose Docker reaches GHCR -- the first real-runtime change
    since they last passed (0.6.0's image, 2026-10-18); the default-ridge change alters numbers, not routes.
  - **Not 0.8.0.** juniper-recurrence 0.8.0 (W5.2: entity-grouped chronological CV over the `trainval`
    pool) is on an open PR behind the model 0.6.0 PyPI gate; the pin follows when it publishes. Note that
    0.7.0's own `[torch]` extra cannot resolve (its model floor was left at `<0.5.0`); the image installs
    the base distribution without torch and is unaffected.
  - Prose that named 0.6.1 as the pinned image (`docker-compose.yml`'s snapshot comment, `README.md`,
    `docs/REFERENCE.md`'s `JUNIPER_RECURRENCE_SNAPSHOTS_DIR` row, the header comment of
    `scripts/test_recurrence_snapshots.sh`) now names 0.7.0; the routes still shipped in 0.6.0.

"""


def _replace_once(path: Path, old: str, new: str, check: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    if text.count(new) == 1 and old not in text:
        print(f"  = {path.name} [{old.strip()[:50]}]: already applied")
        return False
    if text.count(old) != 1:
        raise SystemExit(f"ERROR: {path}: expected exactly one occurrence of {old.strip()[:60]!r}, found {text.count(old)}")
    if check:
        print(f"  ~ {path.name} [{old.strip()[:50]}]: WOULD rewrite")
        return True
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"  + {path.name} [{old.strip()[:50]}]: rewrote")
    return True


def _insert_changelog_entry(path: Path, entry: str, check: bool) -> bool:
    text = path.read_text(encoding="utf-8")
    if _MARKER in text:
        print("  = CHANGELOG.md: entry already present")
        return False
    start = text.find("## [Unreleased]\n")
    end = text.find("\n## [", start + 1)
    if start < 0 or end < 0:
        raise SystemExit("ERROR: CHANGELOG.md: no [Unreleased] section followed by a release")
    section = text[start:end]
    if section.count("\n### Changed\n\n") != 1:
        raise SystemExit(f"ERROR: CHANGELOG.md: expected one '### Changed' in [Unreleased], found {section.count(chr(10) + '### Changed' + chr(10))}")
    anchor = section.index("\n### Changed\n\n") + len("\n### Changed\n\n")
    if check:
        print("  ~ CHANGELOG.md: WOULD add the entry first under [Unreleased] '### Changed'")
        return True
    path.write_text(text[:start] + section[:anchor] + entry + section[anchor:] + text[end:], encoding="utf-8")
    print("  + CHANGELOG.md: added the entry first under [Unreleased] '### Changed'")
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True, type=Path, help="scratch tree laid out like the juniper-deploy repo root")
    ap.add_argument("--ml-pr", required=True, type=int, help="the juniper-ml extras-raise PR number the entry cites")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 if anything would change)")
    args = ap.parse_args()
    root = args.root.resolve()

    changed = False
    for rel, old, new in _EDITS:
        changed |= _replace_once(root / rel, old, new, args.check)
    changed |= _insert_changelog_entry(root / "CHANGELOG.md", _ENTRY.replace("ML_PR", str(args.ml_pr)), args.check)
    return 1 if (args.check and changed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
