#!/usr/bin/env python3
"""Plan v1.7.2: record that the juniper-ml [recurrence] floor is >=0.6.1, and what the Compose-pin decision now rests on.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-18
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.1 -> v1.7.2);
         juniper-ml#2243 (the floor); util/ad-hoc/2026-10-18_raise_recurrence_floor_0_6_1.py (its rewrite)

Why this exists
---------------
Concurrent sessions edit the plan, so a revision is applied as exact-string edits that each must match once,
re-runnable after a fast-forward. The merge SHA is a parameter because the script is written before the merge.

Usage
-----
    python3 util/ad-hoc/2026-10-18_plan_v1_7_2_recurrence_floor_landed.py --merge-sha <8+ hex> [--check]
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

_IMAGE = "the `0.6.1` image is on GHCR (`publish-image.yml` fires on the Release; index digest `sha256:d00478fb…`, revision `cad03ed5`, linux/amd64 + linux/arm64)"


def edits(sha: str) -> list[tuple[str, str]]:
    pr = f"juniper-ml#2243, `{sha}`"
    return [
        ("- **Version**: 1.7.1", "- **Version**: 1.7.2"),
        # Status line.
        (
            "the floors gap of v1.6.1 is closed on the index, and the juniper-ml `[recurrence]` floor move to `>=0.6.1` is the next landing).",
            f"the floors gap of v1.6.1 is closed on the index); **the juniper-ml `[recurrence]` floor is `>=0.6.1`** (v1.7.2: {pr}, 2026-10-18; every M1 landing but the owner's Compose-pin decision is on `main`).",
        ),
        # M1 milestone row.
        (
            "Left: the juniper-ml `[recurrence]` floor to `>=0.6.1` (the owner's ruling, lockstep files as in juniper-ml#2232), and whether the Compose pin follows, still the owner's |",
            f"**Later still on 2026-10-18**: the juniper-ml `[recurrence]` floor is `>=0.6.1` ({pr}; the seven lockstep sites of juniper-ml#2232; pre-flight 32 packages on Python 3.12–3.14, resolving recurrence 0.6.1, model 0.4.0, data-client 0.6.0). Left: whether the Compose pin follows to 0.6.1, the owner's; {_IMAGE}; the Helm chart carries no recurrence image, so it is one `docker-compose.yml` line plus the prose that names 0.6.0 |",
        ),
        # P1 status row.
        (
            "Still owed: the juniper-ml `[recurrence]` floor to `>=0.6.1`, then whether the Compose pin follows it; `docs/REFERENCE.md:177`'s pins sentence",
            f"**The juniper-ml `[recurrence]` floor is `>=0.6.1`** ({pr}, 2026-10-18; `util/ad-hoc/2026-10-18_raise_recurrence_floor_0_6_1.py`). Still owed: whether the Compose pin follows it ({_IMAGE}); `docs/REFERENCE.md:177`'s pins sentence",
        ),
        # Progress 2026-10-18, turing deploy-smokes session.
        (
            "Next landing: the juniper-ml `[recurrence]` floor to `>=0.6.1` (lockstep files as in juniper-ml#2232; pre-flight against PyPI on 3.12–3.14).",
            f"**The floor followed in the next turing session**: {pr} (the seven lockstep sites of juniper-ml#2232, applied by `util/ad-hoc/2026-10-18_raise_recurrence_floor_0_6_1.py`; "
            "pre-flight 32 packages on Python 3.12, 3.13 and 3.14, resolving recurrence 0.6.1, model 0.4.0, client 0.3.0, data-client 0.6.0, service-core 0.7.1; "
            f"`docs/REFERENCE.md` landed first try as its own signed commit, the link idle). The handoff's note that the publish workflow does not build the image was wrong: {_IMAGE}, so the Compose pin can follow when the owner rules.",
        ),
        # Risks & Assumptions: the owner's open list.
        (
            "- **Still the owner's**: cutting recurrence 0.6.1 and approving its PyPI gate; whether the Compose recurrence pin then follows to 0.6.1; whether M1 waits for 0.6.1.",
            f"- **Still the owner's**: whether the Compose recurrence pin follows to 0.6.1 ({_IMAGE}). Done 2026-10-18: 0.6.1 cut and gated; M1 does not wait for it (ruled, below); the juniper-ml `[recurrence]` floor is `>=0.6.1` ({pr}).",
        ),
        # The turing-session ruling line.
        (
            "the juniper-ml `[recurrence]` floor moves to `>=0.6.1` once it is published.",
            f"the juniper-ml `[recurrence]` floor moves to `>=0.6.1` once it is published. **Done 2026-10-18: {pr}.**",
        ),
    ]


def changelog_row(sha: str) -> str:
    return (
        f"| 2026-10-18 | 1.7.2 | **The juniper-ml `[recurrence]` floor is `>=0.6.1`** (juniper-ml#2243, `{sha}`; the owner's ruling of 2026-10-18, taken once 0.6.1 was on PyPI). "
        "The seven lockstep sites of juniper-ml#2232 moved by `util/ad-hoc/2026-10-18_raise_recurrence_floor_0_6_1.py`; the model `>=0.3.0` and data-client `>=0.5.0` floors kept, 0.6.1's own floors doing the forcing. "
        "Pre-flight against real PyPI: `[recurrence]` 32 packages on Python 3.12, 3.13 and 3.14, resolving recurrence 0.6.1, model 0.4.0, data-client 0.6.0. "
        f"Recorded for the Compose-pin decision: {_IMAGE}; the Helm chart has no recurrence image. "
        "Updated: Status line, M1 row, P1 status row, Progress 2026-10-18 (turing), the owner's open list, the turing-session ruling line. "
        "Owed: the Compose-pin ruling; then P5 (W5.10 → W5.8 (B) + W5.9; W5.2, W5.4; W5.7), P2–P4 alongside. | Paul Calnon |\n"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--merge-sha", required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not re.fullmatch(r"[0-9a-f]{8,40}", args.merge_sha):
        raise SystemExit("ERROR: --merge-sha must be 8 to 40 hex characters")
    sha = args.merge_sha[:8]

    text = _PLAN.read_text(encoding="utf-8")
    if "| 1.7.2 |" in text:
        print("  = plan already at v1.7.2")
        return 0
    for old, new in edits(sha):
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"ERROR: expected exactly 1 occurrence, found {n}: {old[:90]!r}")
        text = text.replace(old, new, 1)
        print(f"  + {old[:70]!r}")

    anchor = "| 2026-10-18 | 1.7.1 |"
    i = text.find(anchor)
    if i < 0 or text.count(anchor) != 1:
        raise SystemExit("ERROR: the 1.7.1 change-log row was not found exactly once")
    j = text.index("\n", i) + 1
    text = text[:j] + changelog_row(sha) + text[j:]
    print("  + change-log row 1.7.2")

    if args.check:
        print("  (check mode: nothing written)")
        return 0
    _PLAN.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
