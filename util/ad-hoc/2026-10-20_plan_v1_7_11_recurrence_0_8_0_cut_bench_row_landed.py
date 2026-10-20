#!/usr/bin/env python3
"""Plan v1.7.11: model 0.6.0 published, the W5.2 service half merged, recurrence 0.8.0 cut to its gate, the bench row landed.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-20
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.10 -> v1.7.11);
         juniper-recurrence#215 (W5.2 service half), #220 (the 0.8.0 proposal), #219 (the bench row);
         juniper-ml#2283 (docs tidy), #2284 (handoff), #2285 (the 0.8.0 archive);
         util/ad-hoc/2026-10-20_plan_v1_7_10_w5_5_w5_6_landed.py (the revision this follows)

Usage
-----
    python3 util/ad-hoc/2026-10-20_plan_v1_7_11_recurrence_0_8_0_cut_bench_row_landed.py --bench-sha <8+ hex> [--plan PATH] [--check]

``--bench-sha`` is juniper-recurrence#219's squash-merge sha. ``--plan`` points the script at a copy of the plan (a fresh
``git show origin/main:<plan>`` when landing through the API, so the upload is built on main's current file); the default
is the repo's own copy. Every anchor must match exactly once, or the script refuses and writes nothing; ``--check``
reports what is applied / pending without writing.
"""

from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

CUT = (
    "the owner approved the model 0.6.0 `pypi` gate (run 39197693617 green; the index serves 0.6.0 with 0.5.0's `requires_dist`); "
    "juniper-recurrence#215 (W5.2's service half + the `[torch]` extra fix) merged as `5e0e2b2e` once its lanes resolved 0.6.0 "
    "(one lane first saw a stale PyPI edge and was re-run); proposal juniper-recurrence#220 merged as `6a98515e`; "
    "Release `juniper-recurrence-v0.8.0` cut at that commit (archive juniper-ml#2285; `publish-image.yml` run 39411081827 green — "
    "GHCR `0.8.0` / `0.8` / `latest` at index `sha256:f3bc2a4c…`, revision `6a98515e`); the PyPI publish run 39411081775 is parked at the owner's `pypi` gate"
)
BENCH = (
    "juniper-recurrence#219 (the bench row) merged as `BENCH_SHA` after the cut: refreshed onto main by pushing main's CHANGELOG verbatim, "
    "`update-branch`, then re-applying the entry under the fresh `[Unreleased]` (`util/ad-hoc/2026-10-19_apply_w5_2_bench_multi_ticker.py`); "
    "its red Sequence Safety was the symbol-loss screen on `bench/datasets.py::_full` (its body moved into the new `_composed`, 29 -> 8 lines), waived with an enumerated `Allow-Symbol-Loss: func:_full` trailer"
)
PINS = (
    "the 0.8.0 pins wait on the gate: `util/ad-hoc/2026-10-20_raise_recurrence_floor_0_8_0.py` (juniper-ml `[recurrence]` -> recurrence `>=0.8.0,<0.9.0`, model `>=0.6.0,<0.7.0`; "
    "also moves `docs/QUICK_START.md`'s pip-list lines) and `util/ad-hoc/2026-10-20_pin_compose_recurrence_0_8_0.py` (juniper-deploy `juniper-recurrence:0.8.0`; GHCR facts as arguments) are written and dry-checked"
)


def edits(bench_sha: str) -> list[tuple[str, str]]:
    bench = BENCH.replace("BENCH_SHA", bench_sha)
    return [
        ("- **Version**: 1.7.10", "- **Version**: 1.7.11"),
        # Status line: the v1.7.11 clause, after the v1.7.10 one.
        (
            ". The v1.4.0 plan edits follow that record",
            f"; **model 0.6.0 published, recurrence 0.8.0 cut, the bench row landed** (v1.7.11: {CUT}; {bench}; {PINS}). The v1.4.0 plan edits follow that record",
        ),
        # W5.2 row: the service half's sha and the proposal; the bench row closed.
        (
            "service half juniper-recurrence#215, recurrence 0.8.0; driver juniper-ml#2256)",
            "service half juniper-recurrence#215, `5e0e2b2e`, recurrence 0.8.0 cut via #220, `6a98515e`; bench row juniper-recurrence#219, `BENCH_SHA`; driver juniper-ml#2256)".replace("BENCH_SHA", bench_sha),
        ),
        (
            "**The bench row is juniper-recurrence#219** (opened 2026-10-19, behind juniper-recurrence#215 for the model 0.6.0 floor):",
            f"**The bench row landed 2026-10-20** (juniper-recurrence#219, `{bench_sha}`, after the 0.8.0 cut):",
        ),
        # Roadmap P5 status row for W5.2.
        (
            "| **P5** | Entity-grouped chronological CV via model-core `order`/`groups` (W5.2) | Planned | 5 | recurrence 0.6.x, model 0.4.x |",
            f"| **P5** | Entity-grouped chronological CV via model-core `order`/`groups` (W5.2) | **Done** (model half #214 2026-10-19; service half #215 `5e0e2b2e` and bench row #219 `{bench_sha}` 2026-10-20; recurrence 0.8.0 cut at `6a98515e`, model 0.6.0 on PyPI) | 5 | recurrence 0.8.x, model 0.6.x |",
        ),
        # Progress block: the session bullet before the Next bullet, and the Next bullet rewritten.
        (
            "  - **Next**: the `pypi` gate on model 0.6.0, then juniper-recurrence#215 (re-run its failed lanes), recurrence 0.8.0, then juniper-recurrence#219; the extras / Compose pins follow 0.8.0 (recurrence `>=0.8.0,<0.9.0`, model `>=0.6.0,<0.7.0`, image `0.8.0`); juniper-data's next release carries W5.7 (owner's cut). The W0.1 service-core half, the parent `Juniper/AGENTS.md` paragraph, the W1.12 / W1.11 smokes (now on the 0.7.0 image) and the client-docstring follow-up stay open.",
            f"  - **Model 0.6.0 published, #215 merged, recurrence 0.8.0 cut, the bench row landed (turing session 5, 2026-10-20)**: {CUT}. {bench}. Gate-independent first: juniper-ml#2283 merged `[Unreleased]`'s two `### Changed` headings and refreshed `docs/QUICK_START.md`'s pip-list block to what 0.10.0 resolves (`[all]` 76 packages on 3.12 / 3.13 / 3.14). {PINS}.\n"
            "  - **Next**: the owner's `pypi` gate on recurrence 0.8.0 (run 39411081775), then the two pin scripts above (pre-flight with `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py`; the README compat table via `util/ad-hoc/2026-09-21_sync_readme_compat_table.py`); juniper-data's next release carries W5.7 (owner's cut). The W0.1 service-core half, the parent `Juniper/AGENTS.md` paragraph (recurrence 0.8.0, model 0.6.0), the W1.12 / W1.11 smokes (now owed on the 0.8.0 image) and the client-docstring follow-up (`crossval`'s `folding` / `diagnostics`, after 0.8.0) stay open.",
        ),
    ]


def row(bench_sha: str) -> str:
    return (
        f"| 2026-10-20 | 1.7.11 | **Model 0.6.0 published, recurrence 0.8.0 cut, the bench row landed; P5 / W5.2 Done**: {CUT}; {BENCH.replace('BENCH_SHA', bench_sha)}; {PINS}. "
        "Updated: Status line, the W5.2 row (both cells), the roadmap P5 W5.2 status row, the Progress 2026-10-20 block. "
        "Owed: the recurrence 0.8.0 gate, then the two pin scripts; juniper-data's next release (W5.7); W0.1's service-core half; the parent AGENTS.md paragraph; the W1.12 / W1.11 smokes on the 0.8.0 image; the client docstrings. | Paul Calnon |\n"
    )


_ROW_ANCHOR_START = "| 2026-10-20 | 1.7.10 | **W5.5 / W5.6 built**:"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bench-sha", required=True, help="juniper-recurrence#219's squash-merge sha (8 or more hex)")
    ap.add_argument("--plan", type=Path, default=_PLAN, help="the plan file to edit (default: this repo's copy)")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 if anything would change)")
    args = ap.parse_args()
    sha = args.bench_sha[:8]
    text = args.plan.read_text(encoding="utf-8")

    pending = 0
    for old, new in edits(sha):
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

    new_row = row(sha)
    if "| 2026-10-20 | 1.7.11 |" in text:
        print("  = revision row already present")
    else:
        starts = [i for i in range(len(text)) if text.startswith(_ROW_ANCHOR_START, i)]
        if len(starts) != 1:
            raise SystemExit(f"ERROR: expected exactly one v1.7.10 revision row, found {len(starts)}")
        end = text.index("\n", starts[0]) + 1
        pending += 1
        if not args.check:
            text = text[:end] + new_row + text[end:]
            print("  + revision row added after v1.7.10")
        else:
            print("  ~ WOULD add the revision row after v1.7.10")

    if args.check:
        return 1 if pending else 0
    args.plan.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
