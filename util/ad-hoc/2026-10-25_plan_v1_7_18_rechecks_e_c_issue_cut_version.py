#!/usr/bin/env python3
"""Plan v1.7.18: the #2316 and #2320 post-merge re-checks passed, juniper-ml#2330 (the p4/e-c wall budget) is filed, and the meta-package cut's version is back with the owner.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-25
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.17 -> v1.7.18);
         juniper-ml#2330 (the finding it files into Next); juniper-ml#2328 (v1.7.17, which this follows);
         util/ad-hoc/2026-10-25_plan_v1_7_17_juniper_ml_0_11_1_published.py (the revision this follows)

Usage
-----
    python3 util/ad-hoc/2026-10-25_plan_v1_7_18_rechecks_e_c_issue_cut_version.py [--plan PATH] [--check]

Every fact is settled, so the script takes none. ``--plan`` points it at a copy of the plan (a fresh
``git show origin/main:<plan>`` when landing through the API); the default is the repo's own copy. Every anchor must
match exactly once, or the script refuses and writes nothing; ``--check`` reports what is applied / pending without
writing.
"""

from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

HEADLINE = "the #2316 and #2320 re-checks passed, juniper-ml#2330 filed, the cut's version back with the owner"

CHECKED = (
    "the post-merge re-check of juniper-ml#2316 (the v1.7.16 handoff's item 1) passed on `main` `899796d2`: its CHANGELOG "
    "entry, `docs/REFERENCE.md`'s \"Since juniper-ml#2211 the driver\" sentence and `_save_model_snapshot` are all still "
    "there (the three greps print 1, 1 and 2), and again on `f823b0b7`. The post-merge re-check of juniper-ml#2320 passed "
    "on `main` `c86a5e5e`, after juniper-ml#2325 to #2328 landed on top: `util/ad-hoc/2026-10-25_apply_driver_budget_docs.py "
    "--check` reports every docs edit applied, and `check_per_run_timeout`, `worst_case_budget` and the nine recurrence "
    "suites at 4,500 s are all present. A pre-existing finding that #2320 left out of scope is filed as juniper-ml#2330: "
    "with `JUNIPER_EXP_PROJECT_DIR` set, `WallBudgetContractTest` fails on `p4/e-c-cascor-noise-robustness.yaml` "
    "(`3600.0 not greater than 3600.0`). That suite sweeps `max_hidden_units: 64` on `spiral-baseline.yaml`'s 3,600 s wall "
    "budget, equal to the driver default the wide-cap contract requires it to exceed. It fails identically on pristine "
    "`899796d2`, and CI never sees it because the sibling base does not resolve there. The issue sets out three options: "
    "raise the budget, exempt the suite on its own 517 s-per-cell measurement, or re-derive the threshold. The cut's "
    "version moved: `util/release_train/detect.py` proposes 0.12.0, not the 0.11.2 the owner ruled, because "
    "`[Unreleased]` carries an `### Added` entry (juniper-ml#2327) and juniper-ml#2322's subject is `feat(guard)`, either "
    "of which it reads as a minor"
)

NEXT_OLD = (
    "  - **Next**: R-ML-SERVERS: the `[servers]` floors are on `main` (juniper-ml#2326), so what remains is the 0.11.2 cut, driven to `PENDING_PYPI_APPROVAL` with "
    "0.11.1's rating, as the owner ruled; its `pypi` gate stays the owner's. juniper-ml#2062's fix (`[servers]` installs no client) gets its own PR and a later release. "
)

NEXT_NEW = (
    "  - **Next**: R-ML-SERVERS: the `[servers]` floors are on `main` (juniper-ml#2326), so what remains is the meta-package cut, driven to `PENDING_PYPI_APPROVAL` with "
    "0.11.1's rating, as the owner ruled. Its version is the owner's call: the release train proposes 0.12.0, while the 2026-10-25 ruling named 0.11.2. Its `pypi` gate "
    "stays the owner's. juniper-ml#2062's fix (`[servers]` installs no client) gets its own PR and a later release. juniper-ml#2330 (the `p4/e-c` wall budget) waits on "
    "the owner's choice of option. "
)

_STATUS_TAIL = "it names 0.11.1 as the latest release and both server releases as served). The v1.4.0 plan edits follow that record"


def edits() -> list[tuple[str, str]]:
    return [
        ("- **Version**: 1.7.17", "- **Version**: 1.7.18"),
        # Status line: the v1.7.18 clause, after the v1.7.17 one.
        (
            _STATUS_TAIL,
            _STATUS_TAIL.replace(").", f"); **{HEADLINE}** (v1.7.18: {CHECKED}).", 1),
        ),
        # Progress block: the session bullet before the Next bullet, and the Next bullet's head rewritten (its tail is unchanged).
        (NEXT_OLD, f"  - **{HEADLINE[0].upper()}{HEADLINE[1:]} (turing session 11, 2026-10-25)**: {CHECKED}.\n{NEXT_NEW}"),
    ]


def row() -> str:
    return (
        f"| 2026-10-25 | 1.7.18 | **{HEADLINE[0].upper()}{HEADLINE[1:]}**: {CHECKED}. "
        "Updated: Status line, the Progress block (a turing session 11 bullet; Next's head rewritten). "
        "Owed: the meta-package cut (its version and its `pypi` gate are the owner's); juniper-ml#2330 (the owner's option); juniper-ml#2062's fix; "
        "the client 0.3.1 release; juniper-data's next release (W5.7); juniper-config-tools 0.2.0 (owner); W0.1's service-core half; the snapshot path's first live run. "
        "| Paul Calnon |\n"
    )


_ROW_ANCHOR_START = "| 2026-10-25 | 1.7.17 | **juniper-ml 0.11.1 published, juniper-ml#2210 closed, the 0.8.0 smokes pass; R-ML-SERVERS unblocked**:"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", type=Path, default=_PLAN, help="the plan file to edit (default: this repo's copy)")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 if anything would change)")
    args = ap.parse_args()
    text = args.plan.read_text(encoding="utf-8")

    pending = 0
    for old, new in edits():
        # `new` contains `old`'s text in rewritten form, so "new present" is the applied test.
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

    if "| 2026-10-25 | 1.7.18 |" in text:
        print("  = revision row already present")
    else:
        starts = [i for i in range(len(text)) if text.startswith(_ROW_ANCHOR_START, i)]
        if len(starts) != 1:
            raise SystemExit(f"ERROR: expected exactly one v1.7.17 revision row, found {len(starts)}")
        end = text.index("\n", starts[0]) + 1
        pending += 1
        if not args.check:
            text = text[:end] + row() + text[end:]
            print("  + revision row added after v1.7.17")
        else:
            print("  ~ WOULD add the revision row after v1.7.17")

    if args.check:
        return 1 if pending else 0
    args.plan.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
