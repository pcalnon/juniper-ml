#!/usr/bin/env python3
"""Plan v1.7.14: juniper-ml 0.11.0 is cut and parked at the owner's PyPI gate.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-21
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.13 -> v1.7.14);
         juniper-ml#2306 (the 0.11.0 proposal), util/ad-hoc/2026-10-21_juniper_ml_0_11_0_cut_cochanges.py;
         util/ad-hoc/2026-10-21_plan_v1_7_13_release_train_sees_pins_client_embargo.py (the revision this follows)

Usage
-----
    python3 util/ad-hoc/2026-10-21_plan_v1_7_14_juniper_ml_0_11_0_cut.py \
        --merge-sha <8+ hex> --ci-run <id> --archive-pr <N> --publish-run <id> [--plan PATH] [--check]

``--merge-sha`` is juniper-ml#2306's squash merge (the Release target), ``--ci-run`` main's ``ci.yml`` run on it,
``--archive-pr`` the ceremony's notes-archive PR and ``--publish-run`` the ``publish.yml`` run parked at the gate.
``--plan`` points the script at a copy of the plan (a fresh ``git show origin/main:<plan>`` when landing through the
API, so the upload is built on main's current file); the default is the repo's own copy. Every anchor must match
exactly once, or the script refuses and writes nothing; ``--check`` reports what is applied / pending without writing.
"""

from __future__ import annotations

import argparse
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

CUT = (
    "`util/release_train/propose.py --execute` opened juniper-ml#2306 (merged as `MERGE_SHA`): the generator's commit (the "
    "version, `[Unreleased]` -> `[0.11.0]`, the `AGENTS.md` Version line) and two more. One is `README.md`'s Ecosystem "
    "Compatibility lead-in: `tests/test_pyproject_extras.py` `ReadmeCompatTableTest` requires it to name the pyproject version and "
    "the generator does not edit `README.md`, so the bare proposal failed Regression Tests on a scratch copy "
    "(`'0.10.0' != '0.11.0'`) -- the first generated juniper-ml proposal since that guard (#1972); 0.10.0 was bumped by hand. "
    "The other is `docs/REFERENCE.md`: the compatibility sentence names 0.11.0's `[recurrence]` ranges, a `0.11.x` matrix row "
    "(data `>=0.17.0`, canopy `>=0.9.0`) and the stale `0.6.0` Version cell; both written by "
    "`util/ad-hoc/2026-10-21_juniper_ml_0_11_0_cut_cochanges.py`. Re-detected at `MERGE_SHA` as BUMPED_NOT_RELEASED; main CI "
    "(`ci.yml` run CI_RUN) green; `ceremony.py --execute --cross-repo --target-sha` cut Release `v0.11.0` at that commit "
    "(archive juniper-ml#ARCHIVE_PR; the notes are 91,522 B, 122,032 B base64 against the 125,000 B cap, so no condense); the "
    "`publish.yml` run PUBLISH_RUN is parked at the owner's `pypi` gate"
)


def _cut(merge_sha: str, ci_run: str, archive_pr: str, publish_run: str) -> str:
    return CUT.replace("MERGE_SHA", merge_sha).replace("CI_RUN", ci_run).replace("ARCHIVE_PR", archive_pr).replace("PUBLISH_RUN", publish_run)


def edits(merge_sha: str, ci_run: str, archive_pr: str, publish_run: str) -> list[tuple[str, str]]:
    cut = _cut(merge_sha, ci_run, archive_pr, publish_run)
    return [
        ("- **Version**: 1.7.13", "- **Version**: 1.7.14"),
        # Status line: the v1.7.14 clause, after the v1.7.13 one.
        (
            "is left to the owner). The v1.4.0 plan edits follow that record",
            f"is left to the owner); **juniper-ml 0.11.0 cut, parked at the PyPI gate** (v1.7.14: {cut}). The v1.4.0 plan edits follow that record",
        ),
        # Progress block: the session bullet before the Next bullet, and the Next bullet rewritten.
        (
            "  - **Next**: the juniper-ml 0.11.0 cut (the owner's call on timing): `util/release_train/detect.py --package juniper-ml --json` on a tree at `origin/main`, `propose.py --execute`, merge the proposal, "
            "re-detect at its merge sha, then `ceremony.py --execute --cross-repo --target-sha` (condense the notes first if the archive tops 125,000 B base64); `docs/REFERENCE.md:177`'s pins sentence and a `0.11.x` "
            "matrix row go with the cut. The juniper-recurrence-client 0.3.1 release (owner's cut) carries the embargo fix. juniper-data's next release carries W5.7 (owner's cut). The W0.1 service-core half, the "
            "parent `Juniper/AGENTS.md` paragraph (recurrence 0.8.0, model 0.6.0) and the W1.12 / W1.11 smokes (owed on the 0.8.0 image, on a host whose Docker reaches GHCR) stay open.",
            f"  - **juniper-ml 0.11.0 cut (turing session 8, 2026-10-21)**: the owner approved the cut and the merge. {cut}. The proposal went BEHIND once during its CI (#2305, two handoff prompts) and "
            "`util/safe_merge.py` refreshed it server-side; `[Unreleased]` was empty at the merge sha, and none of the 56 `[0.11.0]` bullets appears in an earlier juniper-ml release's notes.\n"
            f"  - **Next**: the owner approves the juniper-ml 0.11.0 `pypi` gate (run {publish_run}); after the publish, the parent `Juniper/AGENTS.md` RELEASED paragraph (juniper-ml 0.11.0, recurrence 0.8.0, model 0.6.0; "
            "that file is not on turing). `util/release_train/propose.py` should co-update README's compatibility lead-in when it bumps juniper-ml (the gap juniper-ml#2306 met). The juniper-recurrence-client 0.3.1 "
            "release (owner's cut) carries the embargo fix. juniper-data's next release carries W5.7 (owner's cut). The W0.1 service-core half and the W1.12 / W1.11 smokes (owed on the 0.8.0 image, on a host whose "
            "Docker reaches GHCR) stay open.",
        ),
    ]


def row(merge_sha: str, ci_run: str, archive_pr: str, publish_run: str) -> str:
    cut = _cut(merge_sha, ci_run, archive_pr, publish_run)
    return (
        f"| 2026-10-21 | 1.7.14 | **juniper-ml 0.11.0 cut, parked at the PyPI gate**: {cut}. "
        "Updated: Status line, the Progress block (session 8 bullet, Next rewritten). "
        f"Owed: the owner's `pypi` gate approval (run {publish_run}); the parent AGENTS.md paragraph; the propose.py README lead-in gap; the client 0.3.1 release; juniper-data's next release (W5.7); W0.1's "
        "service-core half; the W1.12 / W1.11 smokes on the 0.8.0 image. | Paul Calnon |\n"
    )


_ROW_ANCHOR_START = "| 2026-10-21 | 1.7.13 | **The release train sees the juniper-ml pins again; the client's embargo default is fixed**:"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--merge-sha", required=True, help="juniper-ml#2306's squash-merge sha (8 or more hex)")
    ap.add_argument("--ci-run", required=True, help="main's ci.yml run id on that commit")
    ap.add_argument("--archive-pr", required=True, help="the ceremony's notes-archive PR number")
    ap.add_argument("--publish-run", required=True, help="the publish.yml run id parked at the pypi gate")
    ap.add_argument("--plan", type=Path, default=_PLAN, help="the plan file to edit (default: this repo's copy)")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 if anything would change)")
    args = ap.parse_args()
    facts = (args.merge_sha[:8], args.ci_run, args.archive_pr, args.publish_run)
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

    if "| 2026-10-21 | 1.7.14 |" in text:
        print("  = revision row already present")
    else:
        starts = [i for i in range(len(text)) if text.startswith(_ROW_ANCHOR_START, i)]
        if len(starts) != 1:
            raise SystemExit(f"ERROR: expected exactly one v1.7.13 revision row, found {len(starts)}")
        end = text.index("\n", starts[0]) + 1
        pending += 1
        if not args.check:
            text = text[:end] + row(*facts) + text[end:]
            print("  + revision row added after v1.7.13")
        else:
            print("  ~ WOULD add the revision row after v1.7.13")

    if args.check:
        return 1 if pending else 0
    args.plan.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
