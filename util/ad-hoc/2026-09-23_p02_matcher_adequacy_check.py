#!/usr/bin/env python3
"""Re-derive the P0.2 logging share under the instrument's matcher AND with the logger-only builtins it misses.

Project: juniper-ml
Sub-Project: ad-hoc tooling (cascor#573 logging arc, P0.2 instrument adequacy)
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — investigation (reconciles Lane A3 of the 2026-09-22 handoff validation)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-09-22_p02_logging_share_decompose.py (the instrument under test);
         notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md §13.1 decision 1

WHY THIS EXISTS

The gate that let P2 run -- 16.70 % of worker self time -- comes from a SUBSTRING matcher over
pstats labels. A validation lane reported that it undercounts: its ``(strftime)`` entry can never
match (pstats labels the C method ``~:0(<method 'strftime' of 'datetime.date' objects>)``), and
the per-record ``datetime.now`` / ``open`` / file ``__exit__`` / ``write`` / ``print`` calls that
``Logger._log_at_level`` makes are not in it at all. A lone lane's number is a lead, not a fact,
so this re-derives both figures independently -- and, unlike the lane, it attributes each builtin
by its CALLERS, counting only the calls made from ``logger.py``.

USAGE

    python3 util/ad-hoc/2026-09-23_p02_matcher_adequacy_check.py ~/.local/state/juniper-experiments/p01-logging-at8065ca0f-v3/prof

Exit 0 always; read the table.
"""

from __future__ import annotations

import pstats
import sys
from collections import Counter
from pathlib import Path

MATCHER = ["logger.py:", "constants_logging.py:", "log_config.py:", "(strftime)", "(currentframe)"]
BUILTINS = [
    "<built-in method now>",
    "<method 'strftime' of 'datetime.date' objects>",
    "<built-in method builtins.print>",
    "<built-in method _io.open>",
    "<method '__exit__' of '_io._IOBase' objects>",
    "<method '__enter__' of '_io._IOBase' objects>",
    "<method 'write' of '_io.TextIOWrapper' objects>",
]


def label(key) -> str:
    return f"{key[0]}:{key[1]}({key[2]})"


def main(argv: list[str]) -> int:
    profs = sorted(Path(argv[1]).expanduser().glob("*.prof"))
    print(f"corpus: {len(profs)} profiles under {argv[1]}")
    total = 0.0
    matched = 0.0
    dead = {pat: 0 for pat in MATCHER}
    builtin_from_logger: Counter[str] = Counter()
    builtin_total: Counter[str] = Counter()
    for prof in profs:
        stats = pstats.Stats(str(prof)).stats
        for key, (_cc, _nc, tt, _ct, callers) in stats.items():
            lab = label(key)
            total += tt
            hits = [pat for pat in MATCHER if pat in lab]
            if hits:
                matched += tt
                for pat in hits:
                    dead[pat] += 1
            name = key[2]
            if key[0] == "~" and name in BUILTINS:
                builtin_total[name] += tt
                # Split the builtin's self time across its callers in proportion to their call
                # counts, and keep only the share called from logger.py.
                calls = {label(c): (v[1] if isinstance(v, tuple) else v) for c, v in callers.items()}
                n_all = sum(calls.values()) or 1
                n_logger = sum(n for c, n in calls.items() if "log_config/logger/logger.py:" in c)
                builtin_from_logger[name] += tt * n_logger / n_all
    extra = sum(builtin_from_logger.values())
    print(f"worker self time (denominator):              {total:9.4f} s")
    print(f"instrument's matcher:                        {matched:9.4f} s  = {100 * matched / total:6.2f} %")
    print(f"+ logger-called builtins (caller-weighted):  {extra:9.4f} s")
    print(f"= corrected attributable share:              {matched + extra:9.4f} s  = {100 * (matched + extra) / total:6.2f} %")
    print("\nmatcher entries that never matched a label (dead):", [pat for pat, n in dead.items() if n == 0])
    print("\nbuiltin                                              total self   called from logger.py")
    for name in BUILTINS:
        print(f"  {name:<52} {builtin_total[name]:9.4f} s   {builtin_from_logger[name]:9.4f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
