#!/usr/bin/env python3
"""Plan v1.7.12: recurrence 0.8.0 published, the juniper-ml [recurrence] extras and the Compose pin followed.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-20
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.11 -> v1.7.12);
         juniper-ml#2292 (the [recurrence] extras), juniper-deploy#257 (the Compose pin);
         util/ad-hoc/2026-10-20_raise_recurrence_floor_0_8_0.py and util/ad-hoc/2026-10-20_pin_compose_recurrence_0_8_0.py (the two pin scripts);
         util/ad-hoc/2026-10-20_plan_v1_7_11_recurrence_0_8_0_cut_bench_row_landed.py (the revision this follows)

Usage
-----
    python3 util/ad-hoc/2026-10-20_plan_v1_7_12_recurrence_0_8_0_published_pins_landed.py --ml-sha <8+ hex> --deploy-sha <8+ hex> [--plan PATH] [--check]

``--ml-sha`` is juniper-ml#2292's squash-merge sha and ``--deploy-sha`` juniper-deploy#257's. ``--plan`` points the script
at a copy of the plan (a fresh ``git show origin/main:<plan>`` when landing through the API, so the upload is built on
main's current file); the default is the repo's own copy. Every anchor must match exactly once, or the script refuses
and writes nothing; ``--check`` reports what is applied / pending without writing.
"""

from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

PUBLISHED = (
    "the owner approved the recurrence 0.8.0 `pypi` gate (run 39411081775 green; the index serves 0.8.0 with "
    "`juniper-recurrence-model>=0.6.0,<0.7.0` and the `[torch]` extra `juniper-recurrence-model[torch]>=0.6.0,<0.7.0`)"
)
ML_PINS = (
    "juniper-ml#2292 (merged as `ML_SHA`; `util/ad-hoc/2026-10-20_raise_recurrence_floor_0_8_0.py` then "
    "`util/ad-hoc/2026-09-21_sync_readme_compat_table.py`) moves `[recurrence]` to `juniper-recurrence>=0.8.0,<0.9.0` and "
    "`juniper-recurrence-model>=0.6.0,<0.7.0` (client floor unchanged) across `pyproject.toml`, the exact-string test, the four "
    "documented tables and `docs/QUICK_START.md`'s pip-list block; pre-flighted against real PyPI on 2026-10-20 "
    "(`util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py`: `[recurrence]` 32 packages and `[all]` 76 on 3.12 / 3.13 / 3.14, "
    "recurrence 0.8.0 / model 0.6.0, every other version as for 0.7.0)"
)
COMPOSE_PIN = (
    "juniper-deploy#257 (merged as `DEPLOY_SHA`; `util/ad-hoc/2026-10-20_pin_compose_recurrence_0_8_0.py` on a scratch copy of "
    "juniper-deploy `main` `5d987d83`) pins `juniper-recurrence:0.8.0` (GHCR index `sha256:f3bc2a4c…` re-read before the PR; "
    "linux/amd64 `sha256:481360f6…`, linux/arm64 `sha256:79f1d241…`; revision `6a98515e`) and moves the four prose sites; "
    "the smokes are owed on the 0.8.0 image (this host cannot pull from GHCR)"
)


def edits(ml_sha: str, deploy_sha: str) -> list[tuple[str, str]]:
    ml = ML_PINS.replace("ML_SHA", ml_sha)
    compose = COMPOSE_PIN.replace("DEPLOY_SHA", deploy_sha)
    return [
        ("- **Version**: 1.7.11", "- **Version**: 1.7.12"),
        # Status line: the v1.7.12 clause, after the v1.7.11 one.
        (
            "are written and dry-checked). The v1.4.0 plan edits follow that record",
            f"are written and dry-checked); **recurrence 0.8.0 published and the 0.8.0 pins landed** (v1.7.12: {PUBLISHED}; {ml}; {compose}). The v1.4.0 plan edits follow that record",
        ),
        # Roadmap P5 status row for W5.2: the pins.
        (
            "recurrence 0.8.0 cut at `6a98515e`, model 0.6.0 on PyPI) | 5 | recurrence 0.8.x, model 0.6.x |",
            f"recurrence 0.8.0 cut at `6a98515e` and on PyPI, model 0.6.0 on PyPI; pins juniper-ml#2292 `{ml_sha}` and juniper-deploy#257 `{deploy_sha}`) | 5 | recurrence 0.8.x, model 0.6.x |",
        ),
        # Progress block: the session bullet before the Next bullet, and the Next bullet rewritten.
        (
            "  - **Next**: the owner's `pypi` gate on recurrence 0.8.0 (run 39411081775), then the two pin scripts above (pre-flight with `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py`; "
            "the README compat table via `util/ad-hoc/2026-09-21_sync_readme_compat_table.py`); juniper-data's next release carries W5.7 (owner's cut). The W0.1 service-core half, the parent `Juniper/AGENTS.md` paragraph "
            "(recurrence 0.8.0, model 0.6.0), the W1.12 / W1.11 smokes (now owed on the 0.8.0 image) and the client-docstring follow-up (`crossval`'s `folding` / `diagnostics`, after 0.8.0) stay open.",
            f"  - **Recurrence 0.8.0 published, the 0.8.0 pins landed (turing session 6, 2026-10-20)**: {PUBLISHED}. {ml}. {compose}. Both landed from turing through `util/open_signed_pr.py` with `docs/REFERENCE.md` and `CHANGELOG.md` as their own retried commits (`util/ad-hoc/2026-10-17_push_signed_with_retry.py`), each built from a fresh `origin/main` copy.\n"
            "  - **Next**: juniper-data's next release carries W5.7 (owner's cut). The W0.1 service-core half, the parent `Juniper/AGENTS.md` paragraph (recurrence 0.8.0, model 0.6.0), the W1.12 / W1.11 smokes "
            "(owed on the 0.8.0 image, on a host whose Docker reaches GHCR) and the client-docstring follow-up (`train` / `crossval`'s `diagnostics` / `folding`, a juniper-recurrence-client doc touch with its own "
            "CHANGELOG line) stay open. The release train cuts the juniper-ml version that carries the pins (0.11.0 in the plan).",
        ),
    ]


def row(ml_sha: str, deploy_sha: str) -> str:
    return (
        f"| 2026-10-20 | 1.7.12 | **Recurrence 0.8.0 published; the 0.8.0 pins landed**: {PUBLISHED}; {ML_PINS.replace('ML_SHA', ml_sha)}; {COMPOSE_PIN.replace('DEPLOY_SHA', deploy_sha)}. "
        "Updated: Status line, the roadmap P5 W5.2 status row, the Progress 2026-10-20 block. "
        "Owed: juniper-data's next release (W5.7); W0.1's service-core half; the parent AGENTS.md paragraph; the W1.12 / W1.11 smokes on the 0.8.0 image; the client docstrings; the juniper-ml release that carries the pins. | Paul Calnon |\n"
    )


_ROW_ANCHOR_START = "| 2026-10-20 | 1.7.11 | **Model 0.6.0 published, recurrence 0.8.0 cut, the bench row landed; P5 / W5.2 Done**:"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ml-sha", required=True, help="juniper-ml#2292's squash-merge sha (8 or more hex)")
    ap.add_argument("--deploy-sha", required=True, help="juniper-deploy#257's squash-merge sha (8 or more hex)")
    ap.add_argument("--plan", type=Path, default=_PLAN, help="the plan file to edit (default: this repo's copy)")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 if anything would change)")
    args = ap.parse_args()
    ml_sha = args.ml_sha[:8]
    deploy_sha = args.deploy_sha[:8]
    text = args.plan.read_text(encoding="utf-8")

    pending = 0
    for old, new in edits(ml_sha, deploy_sha):
        # `new` may contain `old` (the Status-line clause is inserted BEFORE the anchor), so "new present" is the test.
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

    new_row = row(ml_sha, deploy_sha)
    if "| 2026-10-20 | 1.7.12 |" in text:
        print("  = revision row already present")
    else:
        starts = [i for i in range(len(text)) if text.startswith(_ROW_ANCHOR_START, i)]
        if len(starts) != 1:
            raise SystemExit(f"ERROR: expected exactly one v1.7.11 revision row, found {len(starts)}")
        end = text.index("\n", starts[0]) + 1
        pending += 1
        if not args.check:
            text = text[:end] + new_row + text[end:]
            print("  + revision row added after v1.7.11")
        else:
            print("  ~ WOULD add the revision row after v1.7.11")

    if args.check:
        return 1 if pending else 0
    args.plan.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
