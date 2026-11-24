#!/usr/bin/env python3
"""Make the symbol-cap suite's shares fixture reachable inside its 40-session frame (session scratch).

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
T_CAP = W / "juniper_data/tests/unit/test_equities_seq_symbol_cap.py"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL {path.name}: expected exactly 1 match, found {n} for:\n---\n{old[:300]}\n---")
    path.write_text(text.replace(old, new))
    print(f"edited {path.relative_to(W)}: {old.splitlines()[0][:70]!r}")


replace_once(
    T_CAP,
    "    The stale half was the FIXTURE, not the generator: a test's mock encodes the\n"
    "    production contract as it stood when the test was written.\n"
    '    """\n'
    "    return pd.DataFrame(\n"
    '        {"shares": [1_000_000_000.0, 1_100_000_000.0], "filed": [pd.Timestamp("2009-08-14"), pd.Timestamp("2010-08-13")]},\n'
    '        index=pd.to_datetime([pd.Timestamp("2009-06-30"), pd.Timestamp("2010-06-30")]),\n'
    "    )\n",
    "    The stale half was the FIXTURE, not the generator: a test's mock encodes the\n"
    "    production contract as it stood when the test was written.\n"
    "\n"
    "    Stale a second time on 2026-09-08, the same way: the filings were dated past the\n"
    "    40-session mocked frame (which ends in February 2008), so ``total_shares`` was\n"
    "    all-NaN in every test here and nothing noticed -- the sequence generator had no\n"
    "    incomplete-data policy. Now it does, and unreachable shares are a REFUSED\n"
    "    request, so the first filing lands inside the frame.\n"
    '    """\n'
    "    return pd.DataFrame(\n"
    '        {"shares": [1_000_000_000.0, 1_100_000_000.0], "filed": [pd.Timestamp("2008-01-15"), pd.Timestamp("2009-01-15")]},\n'
    '        index=pd.to_datetime([pd.Timestamp("2007-12-31"), pd.Timestamp("2008-12-31")]),\n'
    "    )\n",
)
print("CAP FIXTURE FIXED")
