#!/usr/bin/env python3
"""Close register row APD-ML-002 (the owner's word, 2026-11-01): the register's close touches, as one idempotent edit.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-01
Status: ad-hoc — one-off (one close in notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/register_open_set.py and util/ad-hoc/register_status_crosscheck.py (the two counters the close is checked with);
         util/ad-hoc/2026-11-01_consolidated_plan_v1_15_10_apd_ml_002_closed.py (the plan revision that records it)

Why
---
APD-ML-002 was open only on ``test_accuracy``: "the row is open until that column exists". The column exists. Run
``20261030T084056Z-0ac7`` (suite ``test-accuracy-731-smoke-20261030T084056Z``, 2026-10-30) wrote ``eval_metrics.final`` on
``test`` with ``accuracy`` 0.575 to ``metrics_final.json``; ``stats.json`` carries it as ``cascor.eval_scalars`` (``held_out``
true); and the suite's ``aggregate.csv`` has ``test_accuracy`` 0.575 beside ``train_accuracy`` 0.515 and ``val_accuracy``
0.50625. The owner chose "Close it (signed PR)" when asked (session ``856140dc``).

The row has no §3 detail entry, so the register's protocol is four touches: the §4 row's ``**FIXED`` marker, a §5.1
verification row, the §2 status line (the enumeration and the open count, 36 -> 35, post-primer 21 -> 20) and the header
date. The whole-file read of every ``APD-ML-002`` hit found two more stale clauses, both "unreleased" (juniper-cascor#731 is
in 0.13.0, published 2026-10-28), and the 2026-10-26 ruling note, which ends "the row stays open on ``test_accuracy``" and
takes a closing sentence. The other hits (the provenance note, the park block, the sequencing constraint and the "needing one
before code is written" history) are history and stay as written.

Usage
-----
    python3 util/ad-hoc/2026-11-01_register_close_apd_ml_002.py [--root DIR] [--check]

An edit already present is skipped, so a re-run is a no-op. An anchor found zero times or more than once refuses the whole
run before anything is written. ``--check`` writes nothing and exits 1 while an edit is pending. Then run
``python3 util/ad-hoc/register_open_set.py`` (from the repo root) and ``python3 util/ad-hoc/register_status_crosscheck.py``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
REGISTER = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"

_ML2145 = "[juniper-ml#2145](https://github.com/pcalnon/juniper-ml/pull/2145)"
_ML2369 = "[juniper-ml#2369](https://github.com/pcalnon/juniper-ml/pull/2369)"
_C731 = "[juniper-cascor#731](https://github.com/pcalnon/juniper-cascor/pull/731)"
_ML2381 = "[juniper-ml#2381](https://github.com/pcalnon/juniper-ml/pull/2381)"
_FIXED_BY = f"{_ML2145} + {_ML2369} + {_C731} + {_ML2381}"

# Touch 4: the header date.
_DATE_OLD = "**Last Updated**: 2026-10-26\n"
_DATE_NEW = "**Last Updated**: 2026-11-01\n"

# Touch 3: the §2 status line -- the enumeration of closed post-primer ids, then the open counts and their history.
_S2_ENUM_OLD = (
    "`APD-ECO-015` ([juniper-ml#2187](https://github.com/pcalnon/juniper-ml/pull/2187) + [juniper-cascor#710](https://github.com/pcalnon/juniper-cascor/pull/710) "
    "+ [juniper-data#476](https://github.com/pcalnon/juniper-data/pull/476)) — and twenty-one are open — **36 open in all**, 15 primer + 21 post-primer ("
)
_S2_ENUM_NEW = (
    "`APD-ECO-015` ([juniper-ml#2187](https://github.com/pcalnon/juniper-ml/pull/2187) + [juniper-cascor#710](https://github.com/pcalnon/juniper-cascor/pull/710) "
    f"+ [juniper-data#476](https://github.com/pcalnon/juniper-data/pull/476)) and (2026-11-01) `APD-ML-002` ({_FIXED_BY}) — and twenty are open — "
    "**35 open in all**, 15 primer + 20 post-primer ("
)
_S2_HISTORY_OLD = "canopy's CORS ordering and juniper-data's unlocked batch-tags write — no ids here,"
_S2_HISTORY_NEW = "canopy's CORS ordering and juniper-data's unlocked batch-tags write, then 21 → 20 on 2026-11-01, with the close above — no ids here,"

# Touch 1: the §4 row's status, and its stale "in no juniper-cascor release yet".
_ROW_HEAD_OLD = "| APD-ML-002 | *(Partly fixed, and still OPEN on `test_accuracy`. The recurrence half by"
_ROW_HEAD_NEW = (
    f"| APD-ML-002 | **FIXED ({_FIXED_BY}; closed 2026-11-01 on the owner's word)** — "
    "*(Fixed in three parts, the last of them `test_accuracy`, which kept the row open until 2026-11-01. The recurrence half by"
)
_ROW_TAIL_OLD = (
    f"({_C731}, merged 2026-10-27 00:11Z and in no juniper-cascor release yet) and the labelled block "
    "[juniper-ml#2064](https://github.com/pcalnon/juniper-ml/issues/2064) adds to `build_stats` carries it, so the row is open until that column exists."
)
_ROW_TAIL_NEW = (
    f"({_C731}, merged 2026-10-27 00:11Z and released in juniper-cascor 0.13.0 on 2026-10-28) and the labelled block "
    f"[juniper-ml#2064](https://github.com/pcalnon/juniper-ml/issues/2064) adds to `build_stats` carries it ({_ML2381}, which closed #2064 on 2026-10-28), "
    "so the row was open until that column existed. It exists: run `20261030T084056Z-0ac7` (2026-10-30) wrote a final evaluation on `test` with "
    "`accuracy` 0.575, which its suite's `aggregate.csv` carries as `test_accuracy` (§5.1)."
)

# The whole-file read: the 2026-10-26 ruling note's "unreleased", and its last sentence.
_RULING_UNRELEASED_OLD = "(juniper-cascor#731, merged 2026-10-27 00:11Z, unreleased) and #2064 carries into `stats.json`;"
_RULING_UNRELEASED_NEW = "(juniper-cascor#731, merged 2026-10-27 00:11Z, released in 0.13.0 on 2026-10-28) and #2064 carries into `stats.json`;"
_RULING_END_OLD = "  > asks for; the row stays open on `test_accuracy`.\n"
_RULING_END_NEW = (
    "  > asks for; the row stays open on `test_accuracy`. **Closed 2026-11-01**, on the owner's word: run\n"
    "  > `20261030T084056Z-0ac7` filled `test_accuracy`, after juniper-cascor#731 (in 0.13.0) and juniper-ml#2381 (§5.1).\n"
)

# Touch 2: the §5.1 verification row, inserted after APD-ECO-015's (the table's last row).
_V51_AFTER_PREFIX = "| APD-ECO-015 | `FailedAuthThrottle.check()` inserted an entry per unseen source IP"
_V51_ROW = (
    "| APD-ML-002 | `_headline_metrics` read its metric names off the top of `stats.json`'s blocks, where none of them lives, so `aggregate.csv` carried no metric "
    f"| {_FIXED_BY} | **Closed 2026-11-01 on the owner's word**; `test_accuracy` was the last open part. Verified on run `20261030T084056Z-0ac7` "
    "(suite `test-accuracy-731-smoke-20261030T084056Z`, 2026-10-30; one spiral-smoke cell on the cascor primary's `src/`, which carries juniper-cascor#731): "
    "`metrics_final.json`'s `eval_metrics.final` is on `test` with `accuracy` 0.575; `stats.json` (`juniper-experiment-stats/2`) carries it as "
    "`cascor.eval_scalars`, `held_out` true; and the suite's `aggregate.csv` has `test_accuracy` 0.575, with `train_accuracy` 0.515 and `val_accuracy` "
    "0.50625 from the same run (#2369's half). The recurrence half shipped in #2145 (2026-10-04). |"
)

#: (old, new): ``old`` must occur exactly once, unless ``new`` is already there and ``old`` is gone.
REPLACEMENTS = [
    (_DATE_OLD, _DATE_NEW),
    (_S2_ENUM_OLD, _S2_ENUM_NEW),
    (_S2_HISTORY_OLD, _S2_HISTORY_NEW),
    (_ROW_HEAD_OLD, _ROW_HEAD_NEW),
    (_ROW_TAIL_OLD, _ROW_TAIL_NEW),
    (_RULING_UNRELEASED_OLD, _RULING_UNRELEASED_NEW),
    (_RULING_END_OLD, _RULING_END_NEW),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, default=_REPO)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    path = args.root / REGISTER
    text = path.read_text(encoding="utf-8")
    pending = refused = 0
    for old, new in REPLACEMENTS:
        site = old.strip()[:72]
        if new in text and text.count(old) <= text.count(new):
            # ``new`` may contain ``old`` (an insertion after an anchor); applied means each old sits inside a new.
            print(f"  = {site}... already applied")
            continue
        if text.count(old) != 1:
            print(f"  ! {site}... REFUSED: found {text.count(old)} times, expected 1")
            refused += 1
            continue
        text = text.replace(old, new, 1)
        pending += 1
        print(f"  ~ {site}... {'pending' if args.check else 'applied now'}")

    if _V51_ROW in text:
        print("  = the §5.1 verification row... already applied")
    else:
        lines = text.split("\n")
        hits = [i for i, line in enumerate(lines) if line.startswith(_V51_AFTER_PREFIX)]
        if len(hits) != 1:
            print(f"  ! the §5.1 anchor row... REFUSED: found {len(hits)} times, expected 1")
            refused += 1
        else:
            lines.insert(hits[0] + 1, _V51_ROW)
            text = "\n".join(lines)
            pending += 1
            print(f"  ~ the §5.1 verification row... {'pending' if args.check else 'applied now'}")

    if refused:
        print(f"REFUSED: {refused} anchor(s); nothing written", file=sys.stderr)
        return 1
    if args.check:
        return 1 if pending else 0
    if pending:
        path.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
