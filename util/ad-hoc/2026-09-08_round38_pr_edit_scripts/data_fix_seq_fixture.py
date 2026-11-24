#!/usr/bin/env python3
"""Make the seq test fixtures' filings reachable inside the mocked frame (session scratch).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-08
Status: ad-hoc — one-off (applied once, on 2026-09-08, to the PR worktree named below; the paths inside are that session's)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-data#388 (worktree juniper-data--fix--equities-seq-deployment-defaults-and-incomplete-policy--20260908-0730--03b7548f);
         HANDOFF_2026-09-08_defect-register-round-38-the-three-way-prompt-built-and-the-annotation-made-truthful.md
"""
from __future__ import annotations

import sys
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--equities-seq-deployment-defaults-and-incomplete-policy--20260908-0730--03b7548f")
T_SEQ = W / "juniper_data/tests/unit/test_equities_seq_generator.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL {path.name}: expected exactly 1 match, found {n} for:\n---\n{old[:300]}\n---")
    path.write_text(text.replace(old, new))
    print(f"edited {path.relative_to(W)}: {old.splitlines()[0][:70]!r}")


replace_once(
    T_SEQ,
    'def _shares(start: str = "2009-06-30"):\n'
    '    """Synthetic shares-outstanding history, as ``_fetch_shares`` now returns it.\n'
    "\n"
    "    A DataFrame of ``shares`` + ``filed``, not a bare Series: the filing date is\n"
    "    what feeds ``report_date`` / ``days_since_report``, and it is deliberately\n"
    "    LATER than the period end it describes, because that lag is the thing those\n"
    "    columns exist to represent.\n"
    '    """\n'
    "    return pd.DataFrame(\n"
    '        {"shares": [1_000_000_000.0, 1_100_000_000.0], "filed": [pd.Timestamp("2009-08-14"), pd.Timestamp("2010-08-13")]},\n'
    '        index=pd.to_datetime([pd.Timestamp(start), pd.Timestamp("2010-06-30")]),\n'
    "    )\n",
    'def _shares(start: str = "2007-12-31"):\n'
    '    """Synthetic shares-outstanding history, as ``_fetch_shares`` now returns it.\n'
    "\n"
    "    A DataFrame of ``shares`` + ``filed``, not a bare Series: the filing date is\n"
    "    what feeds ``report_date`` / ``days_since_report``, and it is deliberately\n"
    "    LATER than the period end it describes, because that lag is the thing those\n"
    "    columns exist to represent.\n"
    "\n"
    "    The first filing lands INSIDE the mocked 400-session frame (which ends in July\n"
    "    2009). Until 2026-09-08 it was filed 2009-08-14 -- past the frame's last trade\n"
    "    date -- so ``total_shares`` was all-NaN in every test here, and nothing noticed:\n"
    "    the sequence generator had no incomplete-data policy. Now it does, and a fixture\n"
    "    whose shares are unreachable is a fixture for a REFUSED request; the tests that\n"
    "    want that case pass ``shares=None`` explicitly.\n"
    '    """\n'
    "    return pd.DataFrame(\n"
    '        {"shares": [1_000_000_000.0, 1_100_000_000.0], "filed": [pd.Timestamp("2008-01-15"), pd.Timestamp("2009-01-15")]},\n'
    '        index=pd.to_datetime([pd.Timestamp(start), pd.Timestamp("2008-12-31")]),\n'
    "    )\n",
)
print("SEQ FIXTURE FIXED")
