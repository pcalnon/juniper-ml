#!/usr/bin/env python3
"""Plan v1.7.20: juniper-ml 0.11.2 is published, and juniper-ml#2330 is ruled (its fix is juniper-ml#2345).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-26
Status: ad-hoc — one-off (one plan revision)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (v1.7.19 -> v1.7.20);
         util/ad-hoc/2026-10-26_plan_v1_7_19_juniper_ml_0_11_2_cut_parked_at_gate.py (the revision this follows, and the pattern);
         util/ad-hoc/2026-10-26_consolidated_plan_v1_15_2_r_ml_servers_shipped.py (the consolidated plan's matching revision)

Usage
-----
    python3 util/ad-hoc/2026-10-26_plan_v1_7_20_juniper_ml_0_11_2_published.py \
        [--fix-sha <8+ hex>] [--plan PATH] [--check]

``--fix-sha`` is the squash merge of juniper-ml#2345 (juniper-ml#2330's fix); without it the PR is recorded as open
and armed. ``--plan`` points the script at a copy of the plan; the default is the repo's own copy. Every anchor must
match exactly once, or the script refuses and writes nothing; ``--check`` reports what is applied / pending without
writing.

Every fact below was probed on 2026-10-26 against ``gh``, PyPI and pip's resolver, not taken from the handoff that
asked for this revision. The #2330 ruling was taken in a turing session and relayed; #2345's content was read from
its diff.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_PLAN = _REPO / "notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md"

_HEADLINE = "juniper-ml 0.11.2 published, juniper-ml#2330 ruled"

RECORD = (
    "the owner approved the `pypi` gate of publish run 40247789317 on 2026-10-26, and `Publish to PyPI` succeeded "
    "(08:38:21Z-08:38:43Z). `https://pypi.org/pypi/juniper-ml/0.11.2/json` serves the wheel (08:38:39Z) and the sdist "
    "(08:38:40Z), and its 17 `requires_dist` entries equal, as requirements, `pyproject.toml`'s at the tag `e8d38732`: "
    "`[servers]` floors `juniper-cascor>=0.12.0` and `juniper-data>=0.17.1`, beside `juniper-canopy>=0.9.0`. "
    "The aggregate endpoint names 0.11.2 the latest. Resolved from the published metadata against real PyPI (`pip "
    "install --dry-run --ignore-installed --no-cache-dir --only-binary=:all:`, Python 3.14.7, Linux x86_64), "
    "`juniper-ml[servers]==0.11.2` takes 61 packages besides juniper-ml itself, among them cascor 0.12.0, data 0.17.1, "
    "canopy 0.9.0, observability 0.4.1 and service-core 0.7.1, and no Juniper client: juniper-ml#2062's defect holds in "
    "0.11.2 (the issue closed at 09:10:08Z with juniper-ml#2333, which ships in 0.11.3); `juniper-ml[all]==0.11.2` "
    "takes 95, among them worker 0.6.1, recurrence 0.8.0, model 0.6.0 and data-client 0.6.0. pip's first pass, minutes after the upload, "
    "was served an index that listed versions only to 0.11.1; `--no-cache-dir` cleared it. The parent "
    "`Juniper/AGENTS.md` RELEASED paragraph names 0.11.2 the latest and its `[servers]` floors (re-probed against PyPI "
    "on 2026-10-26; nothing else in it had moved), and the consolidated plan records R-ML-SERVERS shipped (v1.15.2). "
    "juniper-ml#2330: the owner chose the issue's option 1 on 2026-10-26 (ruled in a turing session, relayed here), "
    "and juniper-ml#2345, FIX_STATE, sets `util/experiments/suites/p4/e-c-cascor-noise-robustness.yaml`'s "
    "`execution.max_wall_seconds` to 5400, so E-C's worst-case driver budget is 5,850 s against its 7,200 s "
    "`per_run_timeout_seconds`; every cell id and `config_sha256` is unchanged, and "
    "`WallBudgetContractTest.test_e_c_stays_above_its_surveyed_budget` pins both bounds in CI"
)

_STATUS_ANCHOR = "(the turing session's erratum E-CUT)). The v1.4.0 plan edits follow that record"

NEXT_HEAD_OLD = (
    "  - **Next**: the owner's `pypi` approval of juniper-ml 0.11.2's publish run 40247789317 (re-runnable until "
    "2026-11-25 00:07Z; GitHub cancels it on 2026-11-30 00:07Z). Once it publishes, confirm "
    "`https://pypi.org/pypi/juniper-ml/0.11.2/json`, then bring the parent `Juniper/AGENTS.md` RELEASED paragraph up "
    "to date (`[servers]` ships in 0.11.2) and the consolidated plan's §5 R-ML-SERVERS row, whose revision is the "
    "owner's call. juniper-ml#2062's fix (`[servers]` installs no client) is juniper-ml#2333, open, for a later "
    "release. juniper-ml#2330 (the `p4/e-c` wall budget) waits on the owner's choice of option. "
)
NEXT_HEAD_NEW = (
    "  - **Next**: juniper-ml#2062's fix (`[servers]` installs no client, as 0.11.2's still does), juniper-ml#2333, "
    "merged as `da5e8de3` (2026-10-26 09:10Z); it ships in juniper-ml 0.11.3 (owner ruling 2026-10-25), whose `pypi` "
    "gate is the owner's. FIX_NEXT"
)
#: The unchanged tail of the Next bullet, asserted so the head edit cannot land on a rewritten bullet.
_NEXT_TAIL = "The juniper-recurrence-client 0.3.1 release (owner's cut) carries the embargo fix."

_ROW_ANCHOR_START = "| 2026-10-26 | 1.7.19 | **juniper-ml 0.11.2 cut, parked at the `pypi` gate**:"
_ROW_START = "| 2026-10-26 | 1.7.20 | "
_SHA_RE = re.compile(r"^[0-9a-f]{8,40}$")


def _record(fix_sha: "str | None") -> str:
    state = f"merged as `{fix_sha[:8]}`" if fix_sha else "open and armed"
    return RECORD.replace("FIX_STATE", state)


def _next_head(fix_sha: "str | None") -> str:
    tail = "" if fix_sha else "juniper-ml#2345, juniper-ml#2330's fix, merges once its checks pass. "
    return NEXT_HEAD_NEW.replace("FIX_NEXT", tail)


def edits(fix_sha: "str | None") -> list[tuple[str, str]]:
    record = _record(fix_sha)
    bullet = f"  - **{_HEADLINE} (Linux host, 2026-10-26)**: {record}.\n"
    return [
        ("- **Version**: 1.7.19", "- **Version**: 1.7.20"),
        (_STATUS_ANCHOR, _STATUS_ANCHOR.replace("E-CUT)). The v1.4.0", f"E-CUT)); **{_HEADLINE}** (v1.7.20: {record}). The v1.4.0")),
        # Progress block: the session bullet before the Next bullet, and the head of the Next bullet rewritten.
        (NEXT_HEAD_OLD + _NEXT_TAIL, bullet + _next_head(fix_sha) + _NEXT_TAIL),
    ]


def row(fix_sha: "str | None") -> str:
    return (
        f"{_ROW_START}**{_HEADLINE}**: {_record(fix_sha)}. "
        "Updated: Status line, the Progress block (a session bullet before **Next**; the head of **Next** rewritten, its "
        "tail unchanged). | Paul Calnon |"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fix-sha", help="the squash merge of juniper-ml#2345 (juniper-ml#2330's fix), once it has merged")
    ap.add_argument("--plan", type=Path, default=_PLAN, help="the plan file to edit (default: the repo's own copy)")
    ap.add_argument("--check", action="store_true", help="report only; write nothing (exit 1 while an edit is owed)")
    args = ap.parse_args()
    if args.fix_sha and not _SHA_RE.match(args.fix_sha):
        raise SystemExit(f"ERROR: --fix-sha must be 8-40 lowercase hex, got {args.fix_sha!r}")

    text = args.plan.read_text(encoding="utf-8")
    original = text
    owed = 0
    for old, new in edits(args.fix_sha):
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
            raise SystemExit(f"ERROR: expected exactly one v1.7.19 revision row, found {len(starts)}")
        end = text.find("\n", starts[0])
        end = len(text) if end < 0 else end
        owed += 1
        text = text[:end] + "\n" + row(args.fix_sha) + text[end:]
        print(f"  {'~ WOULD add' if args.check else '+ added'} the revision row after v1.7.19")

    if args.check:
        print(f"--check: {owed} edit(s) owed; nothing written")
        return 1 if owed else 0
    if text != original:
        args.plan.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
