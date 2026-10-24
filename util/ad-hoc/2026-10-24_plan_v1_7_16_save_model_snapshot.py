#!/usr/bin/env python3
"""Plan v1.7.16: save_model saves the recurrence model the run scored (juniper-ml#2211), and juniper-ml#2313's re-check passed.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-24
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.15 -> v1.7.16);
         juniper-ml#2316 (the #2211 fix it records), util/ad-hoc/2026-10-24_apply_save_model_snapshot_docs.py;
         util/ad-hoc/2026-10-21_plan_v1_7_15_juniper_ml_0_11_0_published.py (the revision this follows)

Usage
-----
    python3 util/ad-hoc/2026-10-24_plan_v1_7_16_save_model_snapshot.py \
        --recheck-sha <8+ hex> --save-pr <N> [--save-sha <8+ hex>] [--plan PATH] [--check]

``--recheck-sha`` is the ``main`` commit the post-merge re-check of juniper-ml#2313 ran on, ``--save-pr`` the #2211 PR
and ``--save-sha`` its squash merge; without ``--save-sha`` the fix is recorded as open. ``--plan`` points the script at a
copy of the plan (a fresh ``git show origin/main:<plan>`` when landing through the API); the default is the repo's own
copy. Every anchor must match exactly once, or the script refuses and writes nothing; ``--check`` reports what is
applied / pending without writing.
"""

from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

SAVED = (
    "the post-merge re-check of juniper-ml#2313 passed on `main` `RECHECK_SHA` (2026-10-24): its CHANGELOG entry and "
    "`set_readme_compat_version` are both still there. juniper-ml#2211 SAVE_STATE: `save_model` now calls "
    "`POST /v1/model/snapshots` with the train response's `operation_id` as `expect_operation_id` (the route's contract read "
    "from the `juniper-recurrence-v0.8.0` tag), copies the service's `<snapshots_dir>/<id>.npz` "
    "(`recurrence_launch.snapshots_dir`, else `$RUN_DIR/snapshots`) to `artifacts/results/model.npz`, size-checked against "
    "`size_bytes`, and records its `sha256`. A 409 fails the phase (`degraded`, exit 1) with no re-fit standing in; an "
    "unusable id or a size mismatch fails it and removes the copy; a snapshot the run cannot read is recorded with a note; "
    "only a train response without an `operation_id` (a pre-W1.5 service) still re-fits through the launcher-recorded CLI. "
    "`manifest.save_model.source` names the path. Eight new cases in "
    "`tests/test_recurrence_operation_identity_and_dataset_budget.py`, all failing against the old driver; on turing the "
    "eight driver suites fail only the 13 macOS-only names pristine `main` fails too. `docs/REFERENCE.md`, the cheatsheet, "
    "`docs/QUICK_START.md` and `docs/DOCUMENTATION_OVERVIEW.md` follow "
    "(`util/ad-hoc/2026-10-24_apply_save_model_snapshot_docs.py`)"
)

NEXT_OLD = (
    "  - **Next**: the parent `Juniper/AGENTS.md` RELEASED paragraph (juniper-ml 0.11.0, recurrence 0.8.0, model 0.6.0; the owner's, since that file is not on turing). "
    "A juniper-config-tools 0.2.0 cut (the owner's call) no longer needs a hand co-change; its `[Unreleased]` needs backfilling first. The driver follow-ups are juniper-ml#2211 "
    "(`save_model` persists the scored model through `POST /v1/model/snapshots` with `expect_operation_id`, juniper-recurrence#192) and juniper-ml#2210 (`per_run_timeout_seconds` "
    "against the summed driver budgets). The juniper-recurrence-client 0.3.1 release (owner's cut) carries the embargo fix. juniper-data's next release carries W5.7 (owner's cut). "
    "The W0.1 service-core half and the W1.12 / W1.11 smokes (owed on the 0.8.0 image, on a host whose Docker reaches GHCR) stay open."
)

NEXT_NEW = (
    "  - **Next**: the parent `Juniper/AGENTS.md` RELEASED paragraph (juniper-ml 0.11.0, recurrence 0.8.0, model 0.6.0; the owner's, since that file is not on turing). "
    "juniper-ml#2210 is the next driver task: `per_run_timeout_seconds` against the summed driver budgets, where `save_model` is now one `max_wall`-bounded HTTP call on the "
    "snapshot path and the 600 s re-fit only for a pre-W1.5 service. A juniper-config-tools 0.2.0 cut (the owner's call) needs its `[Unreleased]` backfilled first. "
    "The juniper-recurrence-client 0.3.1 release (owner's cut) carries the embargo fix. juniper-data's next release carries W5.7 (owner's cut). The W0.1 service-core half "
    "and the W1.12 / W1.11 smokes (owed on the 0.8.0 image, on a host whose Docker reaches GHCR) stay open, and the next real recurrence run with `save_model` enabled is the "
    "snapshot path's first live exercise."
)


def _saved(recheck_sha: str, save_pr: str, save_sha: "str | None") -> str:
    state = f"landed as juniper-ml#{save_pr} (merged as `{save_sha}`)" if save_sha else f"is juniper-ml#{save_pr}, open"
    return SAVED.replace("SAVE_STATE", state).replace("RECHECK_SHA", recheck_sha)


def edits(recheck_sha: str, save_pr: str, save_sha: "str | None") -> list[tuple[str, str]]:
    saved = _saved(recheck_sha, save_pr, save_sha)
    return [
        ("- **Version**: 1.7.15", "- **Version**: 1.7.16"),
        # Status line: the v1.7.16 clause, after the v1.7.15 one.
        (
            "the three release-train suites pass on `8357ca50` (263 tests)). The v1.4.0 plan edits follow that record",
            f"the three release-train suites pass on `8357ca50` (263 tests)); **save_model saves the scored model** (v1.7.16: {saved}). The v1.4.0 plan edits follow that record",
        ),
        # Progress block: the session bullet before the Next bullet, and the Next bullet rewritten.
        (NEXT_OLD, f"  - **save_model saves the scored model (turing session 10, 2026-10-24)**: {saved}.\n{NEXT_NEW}"),
    ]


def row(recheck_sha: str, save_pr: str, save_sha: "str | None") -> str:
    saved = _saved(recheck_sha, save_pr, save_sha)
    owed_fix = "" if save_sha else f"juniper-ml#{save_pr}'s merge; "
    return (
        f"| 2026-10-24 | 1.7.16 | **save_model saves the scored model**: {saved}. "
        "Updated: Status line, the Progress block (session 10 bullet, Next rewritten). "
        f"Owed: {owed_fix}the parent AGENTS.md paragraph; juniper-ml#2210; the client 0.3.1 release; juniper-data's next release (W5.7); juniper-config-tools 0.2.0 (owner); "
        "W0.1's service-core half; the W1.12 / W1.11 smokes on the 0.8.0 image. | Paul Calnon |\n"
    )


_ROW_ANCHOR_START = "| 2026-10-21 | 1.7.15 | **juniper-ml 0.11.0 published**:"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--recheck-sha", required=True, help="the main commit the post-merge re-check of juniper-ml#2313 ran on (8 or more hex)")
    ap.add_argument("--save-pr", required=True, help="the juniper-ml#2211 PR number")
    ap.add_argument("--save-sha", help="that PR's squash-merge sha (8 or more hex), once it has landed")
    ap.add_argument("--plan", type=Path, default=_PLAN, help="the plan file to edit (default: this repo's copy)")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 if anything would change)")
    args = ap.parse_args()
    facts = (args.recheck_sha[:8], args.save_pr, args.save_sha[:8] if args.save_sha else None)
    text = args.plan.read_text(encoding="utf-8")

    pending = 0
    for old, new in edits(*facts):
        # `new` may contain `old` (the Status-line clause is inserted before the anchor's tail), so "new present" is the test.
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

    if "| 2026-10-24 | 1.7.16 |" in text:
        print("  = revision row already present")
    else:
        starts = [i for i in range(len(text)) if text.startswith(_ROW_ANCHOR_START, i)]
        if len(starts) != 1:
            raise SystemExit(f"ERROR: expected exactly one v1.7.15 revision row, found {len(starts)}")
        end = text.index("\n", starts[0]) + 1
        pending += 1
        if not args.check:
            text = text[:end] + row(*facts) + text[end:]
            print("  + revision row added after v1.7.15")
        else:
            print("  ~ WOULD add the revision row after v1.7.15")

    if args.check:
        return 1 if pending else 0
    args.plan.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
