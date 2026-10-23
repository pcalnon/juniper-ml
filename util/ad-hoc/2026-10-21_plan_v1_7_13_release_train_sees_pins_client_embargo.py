#!/usr/bin/env python3
"""Plan v1.7.13: the release train sees the juniper-ml pins again; the recurrence client's embargo default is fixed.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-21
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.12 -> v1.7.13);
         juniper-ml#2296 (detect.py), juniper-ml#2298 (propose.py), juniper-recurrence#221 (the client);
         util/ad-hoc/2026-10-20_plan_v1_7_12_recurrence_0_8_0_published_pins_landed.py (the revision this follows)

Usage
-----
    python3 util/ad-hoc/2026-10-21_plan_v1_7_13_release_train_sees_pins_client_embargo.py \
        --detect-sha <8+ hex> --propose-sha <8+ hex> --client-sha <8+ hex> [--plan PATH] [--check]

The three shas are the squash merges of juniper-ml#2296, juniper-ml#2298 and juniper-recurrence#221. ``--plan`` points
the script at a copy of the plan (a fresh ``git show origin/main:<plan>`` when landing through the API, so the upload
is built on main's current file); the default is the repo's own copy. Every anchor must match exactly once, or the
script refuses and writes nothing; ``--check`` reports what is applied / pending without writing.
"""

from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

DETECT = (
    "juniper-ml#2296 (merged as `DETECT_SHA`) fixes `util/release_train/detect.py`'s `classify_pyproject_patch`: it took a "
    "hunk's TOML table only from a `[table]` line inside the hunk or from its `@@` trailer, and git's default trailer is the "
    "nearest line that starts with a letter (`doc-tools = [`), never a `[table]`, so every `[servers]` / `[recurrence]` range "
    "change since v0.10.0 read as tooling and juniper-ml (`ship_paths: []`) as UP_TO_DATE -- step 3's release train had "
    "nothing to propose; each hunk now takes its table from the aligned HEAD file, and an unresolved one is UNCERTAIN, never "
    "NON-SHIP (measured on the seven in-repo packages: juniper-ml UP_TO_DATE -> UNRELEASED_CHANGES 0.11.0, and "
    "juniper-config-tools UP_TO_DATE -> UNRELEASED_CHANGES, its `Typing :: Typed` classifier unreleased since 0.1.0 with an "
    "empty `[Unreleased]`; the other five unchanged)"
)
PROPOSE = (
    "juniper-ml#2298 (merged as `PROPOSE_SHA`) keeps `util/release_train/propose.py`'s proposal PR body under GitHub's "
    "65,536-character limit: the 0.11.0 body inlined the 88,548 B notes draft (90,219 characters), which GitHub refuses only "
    "after the release branch and its commit exist; a draft that would not fit is now a pointer to the PR's own CHANGELOG diff "
    "(the 0.11.0 body is 1,909 B), and `execute_proposal` refuses an over-long body before any write. The 0.11.0 dry run's "
    "archive is 118,064 B base64 against the ceremony's 125,000 B cap -- 6,936 B of headroom, so a cut made a few CHANGELOG "
    "entries later needs the condense path"
)
CLIENT = (
    "juniper-recurrence#221 (merged as `CLIENT_SHA`) fixes juniper-recurrence-client's `crossval`, which defaulted `embargo` "
    "to 0 and always sent it, so against 0.8.0 (which honours an explicit value) every client caller who omitted it ran "
    "unembargoed and W5.2's look-back default never applied; `embargo` now defaults to `None` and is sent only when given, and "
    "the `train` / `crossval` docstrings and the README name `metrics_scope`, `operation_id`, `diagnostics`, `folding` and the "
    "`trainval` pool (the client-docstring follow-up). It ships in the client's next release, a 0.3.1 patch inside "
    "juniper-ml's `<0.4.0` ceiling; an `embargo_days` passthrough would make it a minor and is left to the owner"
)


def _texts(detect_sha: str, propose_sha: str, client_sha: str) -> tuple[str, str, str]:
    return DETECT.replace("DETECT_SHA", detect_sha), PROPOSE.replace("PROPOSE_SHA", propose_sha), CLIENT.replace("CLIENT_SHA", client_sha)


def edits(detect_sha: str, propose_sha: str, client_sha: str) -> list[tuple[str, str]]:
    detect, propose, client = _texts(detect_sha, propose_sha, client_sha)
    return [
        ("- **Version**: 1.7.12", "- **Version**: 1.7.13"),
        # Status line: the v1.7.13 clause, after the v1.7.12 one.
        (
            "the smokes are owed on the 0.8.0 image (this host cannot pull from GHCR)). The v1.4.0 plan edits follow that record",
            f"the smokes are owed on the 0.8.0 image (this host cannot pull from GHCR)); **the release train sees the juniper-ml pins again, and the client's embargo default is fixed** (v1.7.13: {detect}; {propose}; {client}). The v1.4.0 plan edits follow that record",
        ),
        # Progress block: the session bullet before the Next bullet, and the Next bullet rewritten.
        (
            "  - **Next**: juniper-data's next release carries W5.7 (owner's cut). The W0.1 service-core half, the parent `Juniper/AGENTS.md` paragraph (recurrence 0.8.0, model 0.6.0), the W1.12 / W1.11 smokes "
            "(owed on the 0.8.0 image, on a host whose Docker reaches GHCR) and the client-docstring follow-up (`train` / `crossval`'s `diagnostics` / `folding`, a juniper-recurrence-client doc touch with its own "
            "CHANGELOG line) stay open. The release train cuts the juniper-ml version that carries the pins (0.11.0 in the plan).",
            "  - **The release train sees the pins again; the client's embargo default fixed (turing session 7, 2026-10-21)**: step 2's post-merge re-check passed (every juniper-ml#2292 line intact on `main` `b16121ac`). "
            f"{detect}. {propose}. {client}. All three landed from turing through `util/open_signed_pr.py`, the juniper-ml `CHANGELOG.md` entries as their own retried commits built from a fresh `origin/main` copy "
            "(`util/ad-hoc/2026-10-21_apply_detect_pyproject_table_changelog.py`, `util/ad-hoc/2026-10-21_apply_propose_pr_body_limit_changelog.py`).\n"
            "  - **Next**: the juniper-ml 0.11.0 cut (the owner's call on timing): `util/release_train/detect.py --package juniper-ml --json` on a tree at `origin/main`, `propose.py --execute`, merge the proposal, "
            "re-detect at its merge sha, then `ceremony.py --execute --cross-repo --target-sha` (condense the notes first if the archive tops 125,000 B base64); `docs/REFERENCE.md:177`'s pins sentence and a `0.11.x` "
            "matrix row go with the cut. The juniper-recurrence-client 0.3.1 release (owner's cut) carries the embargo fix. juniper-data's next release carries W5.7 (owner's cut). The W0.1 service-core half, the "
            "parent `Juniper/AGENTS.md` paragraph (recurrence 0.8.0, model 0.6.0) and the W1.12 / W1.11 smokes (owed on the 0.8.0 image, on a host whose Docker reaches GHCR) stay open.",
        ),
    ]


def row(detect_sha: str, propose_sha: str, client_sha: str) -> str:
    detect, propose, client = _texts(detect_sha, propose_sha, client_sha)
    return (
        f"| 2026-10-21 | 1.7.13 | **The release train sees the juniper-ml pins again; the client's embargo default is fixed**: {detect}; {propose}; {client}. "
        "Updated: Status line, the Progress block (session 7 bullet, Next rewritten). "
        "Owed: the juniper-ml 0.11.0 cut and the client 0.3.1 release (owner's calls); juniper-data's next release (W5.7); W0.1's service-core half; the parent AGENTS.md paragraph; the W1.12 / W1.11 smokes on the 0.8.0 image. | Paul Calnon |\n"
    )


_ROW_ANCHOR_START = "| 2026-10-20 | 1.7.12 | **Recurrence 0.8.0 published; the 0.8.0 pins landed**:"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--detect-sha", required=True, help="juniper-ml#2296's squash-merge sha (8 or more hex)")
    ap.add_argument("--propose-sha", required=True, help="juniper-ml#2298's squash-merge sha (8 or more hex)")
    ap.add_argument("--client-sha", required=True, help="juniper-recurrence#221's squash-merge sha (8 or more hex)")
    ap.add_argument("--plan", type=Path, default=_PLAN, help="the plan file to edit (default: this repo's copy)")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 if anything would change)")
    args = ap.parse_args()
    shas = (args.detect_sha[:8], args.propose_sha[:8], args.client_sha[:8])
    text = args.plan.read_text(encoding="utf-8")

    pending = 0
    for old, new in edits(*shas):
        # `new` may contain `old` (the Status-line clause is inserted BEFORE the anchor's tail), so "new present" is the test.
        if new in text:
            print(f"  = already applied: {old[:70]!r}")
            continue
        if text.count(old) != 1:
            raise SystemExit(f"ERROR: expected exactly one occurrence of {old[:90]!r}, found {text.count(old)}")
        pending += 1
        if not args.check:
            text = text.replace(old, new, 1)
            print(f"  + applied: {old[:70]!r}")
        else:
            print(f"  ~ WOULD apply: {old[:70]!r}")

    if "| 2026-10-21 | 1.7.13 |" in text:
        print("  = revision row already present")
    else:
        starts = [i for i in range(len(text)) if text.startswith(_ROW_ANCHOR_START, i)]
        if len(starts) != 1:
            raise SystemExit(f"ERROR: expected exactly one v1.7.12 revision row, found {len(starts)}")
        end = text.index("\n", starts[0]) + 1
        pending += 1
        if not args.check:
            text = text[:end] + row(*shas) + text[end:]
            print("  + revision row added after v1.7.12")
        else:
            print("  ~ WOULD add the revision row after v1.7.12")

    if args.check:
        return 1 if pending else 0
    args.plan.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
