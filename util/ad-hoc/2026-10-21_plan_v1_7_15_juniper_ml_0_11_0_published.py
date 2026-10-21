#!/usr/bin/env python3
"""Plan v1.7.15: juniper-ml 0.11.0 is on PyPI.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-21
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.14 -> v1.7.15);
         util/ad-hoc/2026-10-21_plan_v1_7_14_juniper_ml_0_11_0_cut.py (the revision this follows)

Usage
-----
    python3 util/ad-hoc/2026-10-21_plan_v1_7_15_juniper_ml_0_11_0_published.py \
        --publish-run <id> --archive-sha <8+ hex> --recheck-sha <8+ hex> [--fix-pr <N>] [--plan PATH] [--check]

``--publish-run`` is the ``publish.yml`` run the owner approved, ``--archive-sha`` the archive PR's squash merge,
``--recheck-sha`` the ``main`` commit the post-merge re-check of juniper-ml#2306's co-changes ran on, and ``--fix-pr``
the concurrent session's ``propose.py`` PR once it is open (without it the fix is recorded as in flight).
``--plan`` points the script at a copy of the plan (a fresh ``git show origin/main:<plan>`` when landing through the
API, so the upload is built on main's current file); the default is the repo's own copy. Every anchor must match
exactly once, or the script refuses and writes nothing; ``--check`` reports what is applied / pending without writing.
"""

from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

PUBLISHED = (
    "the owner approved the `pypi` gate: `publish.yml` run PUBLISH_RUN is green (Publish to PyPI 21:08:22Z-21:08:55Z), and the "
    "index serves the 0.11.0 wheel and sdist with `requires_dist` carrying `juniper-recurrence<0.9.0,>=0.8.0`, "
    "`juniper-recurrence-model<0.7.0,>=0.6.0`, `juniper-data>=0.17.0` and `juniper-canopy>=0.9.0`; Release `v0.11.0` is the "
    "repo's latest. The archive PR juniper-ml#2307 merged as `ARCHIVE_SHA`. The post-merge re-check of juniper-ml#2306's "
    "co-changes passed on `main` `RECHECK_SHA`, twelve hours and four merges later: README's lead-in names 0.11.0 and "
    "`docs/REFERENCE.md` carries the `0.11.x` row. The `propose.py` fix (the v1.7.14 handoff's item 2) FIX_STATE. Its scope "
    "grew past the lead-in: step 5b-ii moves README's `### Extras` table but never the `## Ecosystem Compatibility` rows that "
    "`ReadmeCompatTableTest` also checks, so an in-repo bump that escapes a meta ceiling (juniper-config-tools 0.2.0 against "
    "`<0.2.0` is the likely next) would ship red as generated too"
)

_FIX_IN_FLIGHT = "is in flight in a concurrent turing session"


def _published(publish_run: str, archive_sha: str, recheck_sha: str, fix_pr: "str | None") -> str:
    fix_state = f"is juniper-ml#{fix_pr}, open from a concurrent turing session" if fix_pr else _FIX_IN_FLIGHT
    return PUBLISHED.replace("PUBLISH_RUN", publish_run).replace("ARCHIVE_SHA", archive_sha).replace("RECHECK_SHA", recheck_sha).replace("FIX_STATE", fix_state)


def edits(publish_run: str, archive_sha: str, recheck_sha: str, fix_pr: "str | None") -> list[tuple[str, str]]:
    published = _published(publish_run, archive_sha, recheck_sha, fix_pr)
    fix_next = f"juniper-ml#{fix_pr}" if fix_pr else "a concurrent turing session"
    return [
        ("- **Version**: 1.7.14", "- **Version**: 1.7.15"),
        # Status line: the v1.7.15 clause, after the v1.7.14 one.
        (
            "is parked at the owner's `pypi` gate). The v1.4.0 plan edits follow that record",
            f"is parked at the owner's `pypi` gate); **juniper-ml 0.11.0 published** (v1.7.15: {published}). The v1.4.0 plan edits follow that record",
        ),
        # Progress block: the session bullet before the Next bullet, and the Next bullet rewritten.
        (
            "  - **Next**: the owner approves the juniper-ml 0.11.0 `pypi` gate (run 39577119562); after the publish, the parent `Juniper/AGENTS.md` RELEASED paragraph (juniper-ml 0.11.0, recurrence 0.8.0, model 0.6.0; "
            "that file is not on turing). `util/release_train/propose.py` should co-update README's compatibility lead-in when it bumps juniper-ml (the gap juniper-ml#2306 met). The juniper-recurrence-client 0.3.1 "
            "release (owner's cut) carries the embargo fix. juniper-data's next release carries W5.7 (owner's cut). The W0.1 service-core half and the W1.12 / W1.11 smokes (owed on the 0.8.0 image, on a host whose "
            "Docker reaches GHCR) stay open.",
            f"  - **juniper-ml 0.11.0 published (turing session 9, 2026-10-21)**: {published}.\n"
            "  - **Next**: the parent `Juniper/AGENTS.md` RELEASED paragraph (juniper-ml 0.11.0, recurrence 0.8.0, model 0.6.0; the owner's, since that file is not on turing). The `propose.py` fix for README's "
            f"lead-in and compatibility rows lands from {fix_next}. The driver follow-ups are juniper-ml#2211 (`save_model` persists the scored model through `POST /v1/model/snapshots` with "
            "`expect_operation_id`, juniper-recurrence#192) and juniper-ml#2210 (`per_run_timeout_seconds` against the summed driver budgets). The juniper-recurrence-client 0.3.1 release (owner's cut) carries the "
            "embargo fix. juniper-data's next release carries W5.7 (owner's cut). The W0.1 service-core half and the W1.12 / W1.11 smokes (owed on the 0.8.0 image, on a host whose Docker reaches GHCR) stay open.",
        ),
    ]


def row(publish_run: str, archive_sha: str, recheck_sha: str, fix_pr: "str | None") -> str:
    published = _published(publish_run, archive_sha, recheck_sha, fix_pr)
    return (
        f"| 2026-10-21 | 1.7.15 | **juniper-ml 0.11.0 published**: {published}. "
        "Updated: Status line, the Progress block (session 9 bullet, Next rewritten). "
        "Owed: the parent AGENTS.md paragraph; the propose.py README fix; juniper-ml#2211 and #2210; the client 0.3.1 release; juniper-data's next release (W5.7); W0.1's service-core half; "
        "the W1.12 / W1.11 smokes on the 0.8.0 image. | Paul Calnon |\n"
    )


_ROW_ANCHOR_START = "| 2026-10-21 | 1.7.14 | **juniper-ml 0.11.0 cut, parked at the PyPI gate**:"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--publish-run", required=True, help="the publish.yml run id the owner approved")
    ap.add_argument("--archive-sha", required=True, help="the archive PR's squash-merge sha (8 or more hex)")
    ap.add_argument("--recheck-sha", required=True, help="the main commit the post-merge re-check ran on (8 or more hex)")
    ap.add_argument("--fix-pr", help="the concurrent session's propose.py PR number, once it is open")
    ap.add_argument("--plan", type=Path, default=_PLAN, help="the plan file to edit (default: this repo's copy)")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 if anything would change)")
    args = ap.parse_args()
    facts = (args.publish_run, args.archive_sha[:8], args.recheck_sha[:8], args.fix_pr)
    text = args.plan.read_text(encoding="utf-8")

    pending = 0
    for old, new in edits(*facts):
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

    if "| 2026-10-21 | 1.7.15 |" in text:
        print("  = revision row already present")
    else:
        starts = [i for i in range(len(text)) if text.startswith(_ROW_ANCHOR_START, i)]
        if len(starts) != 1:
            raise SystemExit(f"ERROR: expected exactly one v1.7.14 revision row, found {len(starts)}")
        end = text.index("\n", starts[0]) + 1
        pending += 1
        if not args.check:
            text = text[:end] + row(*facts) + text[end:]
            print("  + revision row added after v1.7.14")
        else:
            print("  ~ WOULD add the revision row after v1.7.14")

    if args.check:
        return 1 if pending else 0
    args.plan.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
