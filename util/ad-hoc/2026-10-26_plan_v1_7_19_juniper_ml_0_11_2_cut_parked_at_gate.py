#!/usr/bin/env python3
"""Plan v1.7.19: juniper-ml 0.11.2 is cut and parked at the owner's `pypi` gate.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-26
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.18 -> v1.7.19);
         util/ad-hoc/2026-10-25_plan_v1_7_18_rechecks_e_c_issue_cut_version.py (the revision this follows);
         util/ad-hoc/2026-10-25_plan_v1_7_17_juniper_ml_0_11_1_published.py (the pattern)

Usage
-----
    python3 util/ad-hoc/2026-10-26_plan_v1_7_19_juniper_ml_0_11_2_cut_parked_at_gate.py \
        [--archive-sha <8+ hex>] [--plan PATH] [--check]

``--archive-sha`` is the squash merge of the archive PR juniper-ml#2341; without it the PR is recorded as open
and armed. ``--plan`` points the script at a copy of the plan; the default is the repo's own copy. Every anchor
must match exactly once, or the script refuses and writes nothing; ``--check`` reports what is applied / pending
without writing.

Every fact below was probed on 2026-10-25/26 against ``gh``, PyPI and the published Release, not taken from the
handoff that asked for this revision.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

_HEADLINE = "juniper-ml 0.11.2 cut, parked at the `pypi` gate"

RECORD = (
    "the owner-approved 0.11.2 cut ran on the Linux host. The proposal juniper-ml#2339 merged as `e8d38732` "
    "(2026-10-25 23:53Z). It opened only after juniper-ml#2335 (`1e4db700`) and #2331 (`900eb93a`) had landed, and its "
    "merge waited for #2338 (`95634772`), so all three CHANGELOG entries ride 0.11.2: each sat in `[Unreleased]`, and "
    "one merged after the proposal would have filed its entry under the released heading with no conflict. The "
    "version is 0.11.2 by the owner's ruling, although `util/release_train/detect.py` proposes 0.12.0; it has no "
    "override, so the manifest's `proposed_version` / `proposed_bump` were set to `0.11.2` / `patch` before "
    "`propose.py --execute`. The proposal's second signed commit `4fdfb177` is `docs/REFERENCE.md`'s co-change, written "
    "by `util/ad-hoc/2026-10-25_juniper_ml_0_11_2_cut_cochanges.py`: the Version cell, the compatibility sentence "
    "(0.11.0's and 0.11.1's `juniper-data>=0.17.0` / `juniper-cascor>=0.11.0` kept as history) and the `0.11.x` row "
    "(`>=0.17.1` / `>=0.12.0`). `util/ad-hoc/2026-10-21_simulate_release_proposal.py` regressed 0 of 17 suites, and "
    "after the last update-branch the CHANGELOG was `main`'s plus exactly one line, `## [0.11.2] - 2026-10-25` (none "
    "of its 2,206 non-blank lines lost). The ceremony (`--target-sha e8d38732… --release-date 2026-10-25`, after the "
    "merge commit's `ci.yml` run 40246738192 went green) cut Release `v0.11.2` (2026-10-26 00:07:09Z, tag at "
    "`e8d38732`, the repo's latest) and opened the archive juniper-ml#2341, ARCHIVE_STATE. Its second signed commit "
    "`c7447a05` fills the security placeholders with 0.11.1's rating (Medium; CWE-201, CWE-755, CWE-770; priority "
    "High), the same text as the Release body (`diff -B` clean). The intro says plainly that the data floor carries no "
    "security change for `[servers]`: PyPI's metadata shows juniper-data 0.17.1 flooring the two patches only under "
    "`extra == \"api\"`, and juniper-cascor 0.12.0 flooring them unconditionally. The notes render Added 2, Changed 2, "
    "Fixed 1, Security 3. Publish run 40247789317 (created 2026-10-26 00:07:10Z): `Build and Validate` and `Publish to "
    "TestPyPI` succeeded, and `Publish to PyPI` waits at the `pypi` gate, the owner's: it can be re-run until "
    "2026-11-25 00:07Z, and GitHub cancels it on 2026-11-30 00:07Z. After the cut, "
    "`util/ad-hoc/2026-10-25_apply_driver_budget_docs.py --check` stays clean (it looks for its CHANGELOG marker "
    "file-wide), while `util/ad-hoc/2026-10-25_raise_servers_floors_cascor_0_12_0_data_0_17_1.py` refuses, by design, "
    "because its entry now sits outside `[Unreleased]` (the turing session's erratum E-CUT)"
)

_STATUS_ANCHOR = "juniper-ml#2334)). The v1.4.0 plan edits follow that record"

NEXT_HEAD_OLD = (
    "  - **Next**: R-ML-SERVERS: the `[servers]` floors are on `main` (juniper-ml#2326), so what remains is the 0.11.2 "
    "cut, driven to `PENDING_PYPI_APPROVAL` with 0.11.1's rating, as the owner ruled; the owner kept 0.11.2 on "
    "2026-10-25 although the release train proposes 0.12.0. Its `pypi` gate stays the owner's. "
)
NEXT_HEAD_NEW = (
    "  - **Next**: the owner's `pypi` approval of juniper-ml 0.11.2's publish run 40247789317 (re-runnable until "
    "2026-11-25 00:07Z; GitHub cancels it on 2026-11-30 00:07Z). Once it publishes, confirm "
    "`https://pypi.org/pypi/juniper-ml/0.11.2/json`, then bring the parent `Juniper/AGENTS.md` RELEASED paragraph up "
    "to date (`[servers]` ships in 0.11.2) and the consolidated plan's §5 R-ML-SERVERS row, whose revision is the "
    "owner's call. "
)
#: The unchanged tail of the Next bullet, asserted so the head edit cannot land on a rewritten bullet.
_NEXT_TAIL = "juniper-ml#2062's fix (`[servers]` installs no client) is juniper-ml#2333, open, for a later release."

_ROW_ANCHOR_START = "| 2026-10-25 | 1.7.18 | **The #2316 and #2320 re-checks passed, juniper-ml#2330 filed, the cut stays 0.11.2**:"
_ROW_START = "| 2026-10-26 | 1.7.19 | "
_SHA_RE = re.compile(r"^[0-9a-f]{8,40}$")


def _record(archive_sha: "str | None") -> str:
    state = f"which merged as `{archive_sha[:8]}`" if archive_sha else "open and armed"
    return RECORD.replace("ARCHIVE_STATE", state)


def edits(archive_sha: "str | None") -> list[tuple[str, str]]:
    record = _record(archive_sha)
    bullet = f"  - **{_HEADLINE} (Linux host, 2026-10-25/26)**: {record}.\n"
    return [
        ("- **Version**: 1.7.18", "- **Version**: 1.7.19"),
        (_STATUS_ANCHOR, _STATUS_ANCHOR.replace("juniper-ml#2334)). The v1.4.0", f"juniper-ml#2334)); **{_HEADLINE}** (v1.7.19: {record}). The v1.4.0")),
        # Progress block: the session bullet before the Next bullet, and the head of the Next bullet rewritten.
        (NEXT_HEAD_OLD + _NEXT_TAIL, bullet + NEXT_HEAD_NEW + _NEXT_TAIL),
    ]


def row(archive_sha: "str | None") -> str:
    return (
        f"{_ROW_START}**{_HEADLINE}**: {_record(archive_sha)}. "
        "Updated: Status line, the Progress block (a session bullet before **Next**; the head of **Next** rewritten, its "
        "tail unchanged). | Paul Calnon |"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--archive-sha", help="the squash merge of the archive PR juniper-ml#2341, once it has merged")
    ap.add_argument("--plan", type=Path, default=_PLAN, help="the plan file to edit (default: the repo's own copy)")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 while an edit is owed)")
    args = ap.parse_args()
    if args.archive_sha and not _SHA_RE.match(args.archive_sha):
        raise SystemExit(f"ERROR: --archive-sha must be 8-40 lowercase hex, got {args.archive_sha!r}")

    text = args.plan.read_text(encoding="utf-8")
    original = text
    owed = 0
    for old, new in edits(args.archive_sha):
        if new in text and old not in text:
            print(f"  = already applied: {new[:80]!r}")
            continue
        if text.count(old) != 1:
            raise SystemExit(f"ERROR: expected exactly one occurrence of {old[:90]!r}, found {text.count(old)}")
        owed += 1
        print(f"  {'~ WOULD apply' if args.check else '+ applied'}: {old[:80]!r}")
        text = text.replace(old, new, 1)

    if _ROW_START in text:
        print("  = revision row already present")
    else:
        starts = [m.start() for m in re.finditer(re.escape(_ROW_ANCHOR_START), text)]
        if len(starts) != 1:
            raise SystemExit(f"ERROR: expected exactly one v1.7.18 revision row, found {len(starts)}")
        end = text.find("\n", starts[0])
        end = len(text) if end < 0 else end
        owed += 1
        text = text[:end] + "\n" + row(args.archive_sha) + text[end:]
        print(f"  {'~ WOULD add' if args.check else '+ added'} the revision row after v1.7.18")

    if args.check:
        print(f"--check: {owed} edit(s) owed; nothing written")
        return 1 if owed else 0
    if text != original:
        args.plan.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
