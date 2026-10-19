#!/usr/bin/env python3
"""Plan v1.7.3: the Compose recurrence pin followed to 0.6.1 (juniper-deploy#251); every M1 landing is on main.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-19
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.2 -> v1.7.3);
         util/ad-hoc/2026-10-18_plan_v1_7_2_recurrence_floor_landed.py (the revision this follows); juniper-deploy#251

Usage
-----
    python3 util/ad-hoc/2026-10-19_plan_v1_7_3_compose_pin_followed.py --merge-sha <8+ hex> [--check]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"
_HANDOFF = _REPO / "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-18_recurrence-equities-floor-0-6-1-landed-compose-pin-ruling-and-p5-next.md"

_IMAGE = "the `0.6.1` image is on GHCR (`publish-image.yml` fires on the Release; index digest `sha256:d00478fb…`, revision `cad03ed5`, linux/amd64 + linux/arm64)"
_SMOKES = "the W1.12 snapshot and W1.11 canopy smokes are owed on a host whose Docker reaches GHCR at the next bring-up, the image differing from 0.6.0's in package metadata only"


def plan_edits(sha: str) -> list[tuple[str, str]]:
    pr = f"juniper-deploy#251, `{sha}`"
    return [
        ("- **Version**: 1.7.2", "- **Version**: 1.7.3"),
        (
            "every M1 landing but the owner's Compose-pin decision is on `main`).",
            f"every M1 landing but the owner's Compose-pin decision is on `main`); **the Compose pin followed to 0.6.1** (v1.7.3: {pr}, ruled and merged 2026-10-19 UTC; **every M1 landing is on `main`**).",
        ),
        (
            f"Left: whether the Compose pin follows to 0.6.1, the owner's; {_IMAGE}; the Helm chart carries no recurrence image, so it is one `docker-compose.yml` line plus the prose that names 0.6.0 |",
            f"**Ruled yes and landed 2026-10-19 UTC**: {pr} pins `juniper-recurrence:0.6.1` in `docker-compose.yml` and re-words the prose that named 0.6.0 (`README.md`, `docs/REFERENCE.md`, `scripts/test_recurrence_snapshots.sh`); {_IMAGE}; the Helm chart carries no recurrence image. **Every M1 landing is on `main`**; {_SMOKES} |",
        ),
        (
            f"Still owed: whether the Compose pin follows it ({_IMAGE}); `docs/REFERENCE.md:177`'s pins sentence",
            f"**The Compose pin followed** ({pr}, 2026-10-19 UTC; {_SMOKES}). Still owed: `docs/REFERENCE.md:177`'s pins sentence",
        ),
        (
            f"- **Still the owner's**: whether the Compose recurrence pin follows to 0.6.1 ({_IMAGE}). Done 2026-10-18:",
            f"- **Still the owner's**: nothing on this list. The Compose recurrence pin followed to 0.6.1 (ruled yes 2026-10-19 UTC; {pr}; {_IMAGE}). Done 2026-10-18:",
        ),
    ]


def changelog_row(sha: str) -> str:
    return (
        f"| 2026-10-19 | 1.7.3 | **The Compose recurrence pin followed to 0.6.1** (owner ruling 2026-10-19 UTC; juniper-deploy#251 merged as `{sha}`): `docker-compose.yml` pins `juniper-recurrence:0.6.1`, and the prose naming 0.6.0 in `README.md`, `docs/REFERENCE.md` and `scripts/test_recurrence_snapshots.sh` now names 0.6.1 with the routes shipped in 0.6.0; the Helm chart has no recurrence image. "
        f"**Every M1 landing is on `main`.** {_SMOKES[0].upper() + _SMOKES[1:]}. "
        "Updated: Status line, M1 row, P1 status row, the owner's open list. Owed: P5 (W5.10 → W5.8 (B) + W5.9; W5.2, W5.4; W5.7) with P2–P4 alongside; the owner's W0.1 service-core half and the parent AGENTS.md paragraph; the open follow-ups. | Paul Calnon |\n"
    )


def handoff_edits(sha: str) -> list[tuple[str, str]]:
    return [
        (
            "1. **Owner: whether the Compose recurrence pin follows to 0.6.1** (juniper-deploy; open on the plan's M1 row). The inputs are all in hand:",
            f"1. **Done 2026-10-19 UTC — the owner ruled yes and juniper-deploy#251 merged as `{sha}`** (`docker-compose.yml` pins `juniper-recurrence:0.6.1`; the prose in `README.md`, `docs/REFERENCE.md` and `scripts/test_recurrence_snapshots.sh` follows; plan v1.7.3). **Owed from it**: the W1.12 snapshot smoke and W1.11 canopy smoke on a host whose Docker reaches GHCR, at the next bring-up. The inputs that were in hand when this was written:",
        ),
        (
            "Continue the arc from plan v1.7.2. **Every M1 landing except the owner's Compose-pin decision is on `main`**:",
            "Continue the arc from plan v1.7.3. **Every M1 landing is on `main`** (the Compose pin followed in juniper-deploy#251 after this handoff was first written; step 1 below records it):",
        ),
    ]


def apply(text: str, edits: list[tuple[str, str]], what: str) -> str:
    for old, new in edits:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"ERROR: {what}: expected exactly 1 occurrence, found {n}: {old[:90]!r}")
        text = text.replace(old, new, 1)
        print(f"  + {what}: {old[:70]!r}")
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--merge-sha", required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not re.fullmatch(r"[0-9a-f]{8,40}", args.merge_sha):
        raise SystemExit("ERROR: --merge-sha must be 8 to 40 hex characters")
    sha = args.merge_sha[:8]

    plan = _PLAN.read_text(encoding="utf-8")
    if "| 1.7.3 |" in plan:
        print("  = plan already at v1.7.3")
        return 0
    plan = apply(plan, plan_edits(sha), "plan")
    anchor = "| 2026-10-18 | 1.7.2 |"
    i = plan.find(anchor)
    if i < 0 or plan.count(anchor) != 1:
        raise SystemExit("ERROR: the 1.7.2 change-log row was not found exactly once")
    j = plan.index("\n", i) + 1
    plan = plan[:j] + changelog_row(sha) + plan[j:]
    print("  + plan: change-log row 1.7.3")

    handoff = apply(_HANDOFF.read_text(encoding="utf-8"), handoff_edits(sha), "handoff")

    if args.check:
        print("  (check mode: nothing written)")
        return 0
    _PLAN.write_text(plan, encoding="utf-8")
    _HANDOFF.write_text(handoff, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
