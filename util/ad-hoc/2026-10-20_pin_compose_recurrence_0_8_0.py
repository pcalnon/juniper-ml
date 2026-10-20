#!/usr/bin/env python3
"""Move juniper-deploy's Compose pin for juniper-recurrence from 0.7.0 to 0.8.0, with the prose that names it.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-20
Status: ad-hoc — one-off (the juniper-deploy pin PR for recurrence 0.8.0)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: P5 / W5.2 of notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md;
         util/ad-hoc/2026-10-19_pin_compose_recurrence_0_7_0.py (the 0.7.0 pin this follows, the same five files);
         util/ad-hoc/2026-10-20_raise_recurrence_floor_0_8_0.py (the juniper-ml extras raise taken with it)

Why this exists
---------------
juniper-recurrence 0.8.0 was cut on 2026-10-20 at ``6a98515e`` (juniper-recurrence#220, W5.2's service half #215 plus the
``[torch]`` fix). juniper-deploy's ``docker-compose.yml`` pins the image by exact tag, and four prose sites name the
pinned version. Sibling-repo git is refused in agent sessions, so this edits a scratch copy fetched from juniper-deploy
``main`` by the API, and the result lands through ``util/open_signed_pr.py``.

The GHCR facts (index digest, per-arch digests, the publish-image run id) are arguments rather than constants because the
script is written before the image exists: ``publish-image.yml`` fires on ``release: published`` and its Dockerfile
installs ``juniper-recurrence`` from PyPI, so the image follows the owner's ``pypi`` gate. Verify on GHCR first
(``docker buildx imagetools inspect ghcr.io/pcalnon/juniper-recurrence:0.8.0`` or the registry API) and pass what it says.

Every edit asserts its exact expected text and must match exactly once; "new present once" counts as applied. The
CHANGELOG entry goes first under ``[Unreleased]`` -> ``### Changed``, the pattern of juniper-deploy#251 and the 0.7.0 pin.

Usage
-----
    python3 util/ad-hoc/2026-10-20_pin_compose_recurrence_0_8_0.py --root <scratch juniper-deploy tree> --ml-pr <N> \\
        --index-digest sha256:... --amd64-digest sha256:... --arm64-digest sha256:... --publish-run <id> [--check]
"""

from __future__ import annotations

import argparse
from pathlib import Path

#: (relative path, exact old text, exact new text)
_EDITS: list[tuple[str, str, str]] = [
    ("docker-compose.yml", "    image: ghcr.io/pcalnon/juniper-recurrence:0.7.0\n", "    image: ghcr.io/pcalnon/juniper-recurrence:0.8.0\n"),
    (
        "docker-compose.yml",
        "      # The pinned 0.7.0 image carries the snapshot routes (shipped in 0.6.0, juniper-recurrence#172):",
        "      # The pinned 0.8.0 image carries the snapshot routes (shipped in 0.6.0, juniper-recurrence#172):",
    ),
    (
        "README.md",
        "The pinned `juniper-recurrence:0.7.0` image **carries the snapshot routes** (shipped in 0.6.0, juniper-recurrence#172)",
        "The pinned `juniper-recurrence:0.8.0` image **carries the snapshot routes** (shipped in 0.6.0, juniper-recurrence#172)",
    ),
    (
        "README.md",
        "(the published 0.7.0 is `5c576da4`; 0.6.1 was `cad03ed5`)",
        "(the published 0.8.0 is `6a98515e`; 0.7.0 was `5c576da4`)",
    ),
    (
        "docs/REFERENCE.md",
        "Read by the pinned 0.7.0 image (the routes shipped in 0.6.0); images through 0.5.0 ignore it |",
        "Read by the pinned 0.8.0 image (the routes shipped in 0.6.0); images through 0.5.0 ignore it |",
    ),
    (
        "scripts/test_recurrence_snapshots.sh",
        "#    pinned juniper-recurrence:0.7.0 carries the snapshot routes, which shipped in 0.6.0",
        "#    pinned juniper-recurrence:0.8.0 carries the snapshot routes, which shipped in 0.6.0",
    ),
]

_PLAN = "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"
_MARKER = "**`juniper-recurrence` pinned to `0.8.0`**"
_ENTRY = f"""- {_MARKER} (W5.2 / P5 of juniper-ml
  `{_PLAN}`;
  approved 2026-10-20 with the session's merge approval, the ruling 0.7.0 reopened, taken with juniper-ml's
  `[recurrence]` floor moving to `>=0.8.0` in juniper-ml#ML_PR). The pin was `0.7.0`.
  - **What 0.8.0 is.** W5.2 of the plan: `POST /v1/crossval` selects over juniper-recurrence-model 0.6.0's
    composed `trainval` pool, so the reserved `test` partition is never in a fold; a multi-ticker artifact's
    folds are cut on the global date per entity (`ticker_code` / `window_end_date`) with the embargo purged
    per entity; `embargo` defaults to the look-back; the optional `embargo_days`; a `folding` block on the
    response and on `GET /v1/crossval/status`; `dataset.split` reads `trainval`. The `[torch]` extra resolves
    again (0.7.0's was disjoint from its base floor; the image ships no torch and was unaffected). This changes
    the image's runtime: its lock pins model 0.6.0 (0.5.0 before). The snapshot routes, the auth posture, the
    port and the environment variables are unchanged.
  - **The image, verified on GHCR 2026-10-20**: tags `0.8.0` / `0.8` / `latest` resolve to one index,
    digest `INDEX_DIGEST`; linux/amd64 `AMD64_DIGEST` and linux/arm64 `ARM64_DIGEST`;
    `org.opencontainers.image.version` is `0.8.0` and `revision` is `6a98515e`, the `juniper-recurrence-v0.8.0`
    tag's commit. `publish-image.yml` (run PUBLISH_RUN) is green.
  - **The Helm chart is untouched**: `k8s/helm/juniper/values.yaml` carries no recurrence image.
  - **Smokes not re-run for this pin.** This change's host cannot pull from GHCR. Both
    `scripts/test_recurrence_snapshots.sh` and `scripts/test_canopy_recurrence_smoke.sh` are owed on the
    0.8.0 image at the next bring-up on a host whose Docker reaches GHCR (they were last green on 0.6.0's
    image, 2026-10-18; the 0.7.0 pin shipped the same way). The crossval change alters fold membership and
    the response shape (`folding`), not the snapshot routes.
  - Prose that named 0.7.0 as the pinned image (`docker-compose.yml`'s snapshot comment, `README.md`,
    `docs/REFERENCE.md`'s `JUNIPER_RECURRENCE_SNAPSHOTS_DIR` row, the header comment of
    `scripts/test_recurrence_snapshots.sh`) now names 0.8.0; the routes still shipped in 0.6.0.

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
    ap.add_argument("--index-digest", required=True, help="the multi-arch index digest the three tags resolve to (sha256:...)")
    ap.add_argument("--amd64-digest", required=True, help="the linux/amd64 manifest digest (sha256:..., may be abbreviated with an ellipsis)")
    ap.add_argument("--arm64-digest", required=True, help="the linux/arm64 manifest digest (sha256:..., may be abbreviated with an ellipsis)")
    ap.add_argument("--publish-run", required=True, help="the green publish-image.yml run id")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 if anything would change)")
    args = ap.parse_args()
    root = args.root.resolve()

    entry = _ENTRY.replace("ML_PR", str(args.ml_pr)).replace("INDEX_DIGEST", args.index_digest).replace("AMD64_DIGEST", args.amd64_digest).replace("ARM64_DIGEST", args.arm64_digest).replace("PUBLISH_RUN", str(args.publish_run))
    changed = False
    for rel, old, new in _EDITS:
        changed |= _replace_once(root / rel, old, new, args.check)
    changed |= _insert_changelog_entry(root / "CHANGELOG.md", entry, args.check)
    return 1 if (args.check and changed) else 0


if __name__ == "__main__":
    raise SystemExit(main())
