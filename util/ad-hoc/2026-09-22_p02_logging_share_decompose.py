#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (cascor#573 logging redesign, P0.2)
Application: ad-hoc measurement
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: decompose the logging share of worker self time over a P0.1 profile corpus, so decision 1's
**10 % threshold** can be applied. Below it, P2 is cancelled and recorded as cancelled.

DENOMINATOR. Worker self time is the sum of ``tottime`` over every function in every profile. That
is the same denominator ``JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_GATED-MEASUREMENTS-RESULTS.md``
section 3 used (84.96 s there), and it is what "share of worker self time" means.

NUMERATOR, and the caveat that governs it. Per ROADMAP section 3.1, this may report the **emitted**
share and the **discard count**, and **must not** promise the construction cost of discarded
records: an f-string's construction is inline in its calling function's own self time and is not
separately attributable from this corpus. Raising the level does not measure it either, because the
arguments evaluate at the call site regardless. The disabled-logging A/B was considered and
REJECTED for the same reason -- do not reach for it.

So the components below are split into two groups, and only the first is a defensible share:

  ATTRIBUTABLE -- functions whose own tottime is logging work:
      _filter_by_level, _log_at_level, _resolve_level_number, _logging_message, _frame_info,
      _console_dict, _file_dict, isEnabledFor, getLevelNumber, strftime, currentframe, and the
      emit methods themselves.
  NOT ATTRIBUTABLE -- named, counted, and deliberately NOT summed into the share:
      Tensor.__format__ (cumulative, and charged to emitted records only), and the f-string
      construction cost of discarded records (invisible here by construction).

Usage: 2026-09-22_p02_logging_share_decompose.py <PROF_DIR> [--top N]
"""
import argparse
import pstats
import sys
from collections import Counter
from pathlib import Path

#: Substrings matched against "<file>:<line>(<func>)" keys. Each is logging work whose tottime is
#: charged to the logger itself rather than to its caller.
LOGGING_FUNCS = [
    "logger.py:",              # every Logger method, incl. the filter and the emit path
    "constants_logging.py:",
    "log_config.py:",
    "(strftime)",
    "(currentframe)",
]

#: Counted and reported, never summed into the share -- see the module docstring.
NOT_ATTRIBUTABLE = ["__format__"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prof_dir")
    ap.add_argument("--top", type=int, default=15)
    args = ap.parse_args()

    profs = sorted(Path(args.prof_dir).glob("*.prof"))
    if not profs:
        sys.exit(f"FATAL: no .prof under {args.prof_dir} -- a share computed over zero profiles "
                 f"is not a measurement")

    total_self = 0.0
    per_func = Counter()
    per_calls = Counter()
    for p in profs:
        st = pstats.Stats(str(p))
        for key, (_cc, nc, tt, _ct, _callers) in st.stats.items():
            label = f"{key[0]}:{key[1]}({key[2]})"
            total_self += tt
            per_func[label] += tt
            per_calls[label] += nc

    def matches(label, pats):
        return any(pat in label for pat in pats)

    logging_self = sum(tt for lbl, tt in per_func.items() if matches(lbl, LOGGING_FUNCS))
    logging_calls = sum(per_calls[lbl] for lbl in per_func if matches(lbl, LOGGING_FUNCS))
    notattr_self = sum(tt for lbl, tt in per_func.items() if matches(lbl, NOT_ATTRIBUTABLE))

    print(f"corpus            : {len(profs)} profiles under {args.prof_dir}")
    print(f"worker self time  : {total_self:.2f} s  (sum of tottime over every function)")
    print()
    print(f"ATTRIBUTABLE logging self time : {logging_self:.2f} s over {logging_calls:,} calls")
    share = 100.0 * logging_self / total_self if total_self else 0.0
    print(f"                        share  : {share:.2f} %")
    print()
    print(f"NOT attributable (named, NOT summed):")
    print(f"  __format__ self time         : {notattr_self:.2f} s "
          f"({100.0 * notattr_self / total_self if total_self else 0:.2f} % -- emitted records only)")
    print(f"  f-string construction for discarded records: NOT SEPARATELY ATTRIBUTABLE from this")
    print(f"    corpus (ROADMAP 3.1). It is inline in each calling function's own tottime.")
    print()
    print(f"=== decision 1's gate: threshold 10 % ===")
    verdict = "AT OR ABOVE -> P2 RUNS" if share >= 10.0 else "BELOW -> P2 is CANCELLED and recorded as cancelled"
    print(f"  measured {share:.2f} %  ->  {verdict}")
    print(f"  NOTE: this is the share the instrument can ATTRIBUTE. It is a LOWER BOUND on total")
    print(f"  logging cost, because discarded-record construction is invisible here by construction.")
    print(f"  Decision 1 says the 10 % is 'measured on what the instrument can attribute', so this")
    print(f"  is the figure it asks for -- but do not restate it as 'logging costs {share:.1f} %'.")
    print()
    print(f"=== top {args.top} logging functions by self time ===")
    rows = [(lbl, tt) for lbl, tt in per_func.items() if matches(lbl, LOGGING_FUNCS)]
    for lbl, tt in sorted(rows, key=lambda r: -r[1])[:args.top]:
        print(f"  {tt:8.3f} s  {per_calls[lbl]:>10,}  {lbl}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
