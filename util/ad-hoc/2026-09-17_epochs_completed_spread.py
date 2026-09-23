#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: Performance lane -- owner decision D6
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

WHAT THIS IS
------------
The measurement gating owner decision **D6**
(`notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-SIX-OWNER-DECISIONS-RULED.md`).

D6 asks whether a work-style **exact-match** gate on ``epochs_completed`` is safe for the candidate
micro-benchmarks — the micro analogue of the run tier's split gate. It was ruled "re-measure
first", because the reference value looked unstable: the 2026-09-07 validation observed
requested-100 completing **52** in one round and **68** in another. A gate whose reference moves
with ambient conditions is a flaky gate.

THE HYPOTHESIS THIS TESTS, WHICH IS NOT "IS IT RANDOM"
-----------------------------------------------------
``test_micro_candidate.py`` calls ``torch.manual_seed(42)`` inside the benchmarked function and
``_make_data`` seeds again, so the arithmetic is fully seeded. Variance therefore is **not** seed
noise. cascor#531 supplies a mechanism that fits exactly: thread count changes BLAS reduction
order, hence floating-point results, hence **where a patience-based early-stopping loop
terminates** (`parallelism/blas_threads.py`). ``train_detailed`` early-stops when correlation
plateaus, which is precisely such a loop.

So the question is not "is ``epochs_completed`` random" but **"is it a function of thread width?"**
Those have opposite consequences:

- deterministic at a fixed width, varying across widths  -> an exact-match gate IS safe, PROVIDED
  it pins the width. That is an actionable, cheap fix.
- varying at a fixed width                               -> genuinely nondeterministic; exact-match
                                                            is unsafe and the decision is closed.

WHAT IT DOES
------------
Runs the benchmark's own workload — same helpers, same seeds, same learning rate — at several
thread widths, repeating each width, and reports whether the value is constant WITHIN a width and
whether it differs ACROSS widths.

Width is set with ``torch.set_num_threads`` in-process. That is legitimate here and NOT the
mistake the thread-width sweep made: each measurement is a fresh call in a single-threaded main
flow, so there is no worker thread whose pin could be silently reverted, and the value being read
back is ``epochs_completed`` rather than a thread width.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--widths", type=int, nargs="+", default=[1, 2, 4, 8, 16])
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--epochs", type=int, nargs="+", default=[10, 50, 100, 200], help="the benchmark's own parametrisation")
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    sys.path.insert(0, os.getcwd())
    import torch

    from candidate_unit.candidate_unit import CandidateUnit

    def make_data(input_size: int, n_samples: int, output_size: int = 2):
        # Verbatim from tests/performance/test_micro_candidate.py::_make_data
        torch.manual_seed(42)
        x = torch.randn(n_samples, input_size)
        residual = torch.randn(n_samples, output_size)
        return x, residual

    def one_run(epochs: int):
        # Verbatim from the benchmark's `run()` closure.
        torch.manual_seed(42)
        candidate = CandidateUnit(CandidateUnit__input_size=2, CandidateUnit__activation_function=torch.nn.Tanh())
        return candidate.train_detailed(x=x, epochs=epochs, residual_error=residual, learning_rate=0.005, display_frequency=0)

    x, residual = make_data(input_size=2, n_samples=100)

    observations: dict[tuple[int, int], list[int]] = defaultdict(list)
    for width in args.widths:
        torch.set_num_threads(width)
        effective = torch.get_num_threads()
        for epochs in args.epochs:
            for _ in range(args.repeats):
                result = one_run(epochs)
                observations[(width, epochs)].append(int(result.epochs_completed))
        if effective != width:
            print(f"note: requested width {width}, torch reports {effective}")

    print(f"{'requested':<11}{'epochs':>8}{'n':>4}{'values observed':>34}{'constant?':>12}")
    per_epoch_across_widths: dict[int, set[int]] = defaultdict(set)
    any_within_variance = False
    for (width, epochs), values in sorted(observations.items()):
        unique = sorted(set(values))
        constant = len(unique) == 1
        any_within_variance = any_within_variance or not constant
        per_epoch_across_widths[epochs].update(unique)
        print(f"{width:<11}{epochs:>8}{len(values):>4}{str(unique):>34}{('YES' if constant else 'NO -- VARIES'):>12}")

    print()
    print("Across widths, at each requested epoch count:")
    varies_across = False
    for epochs in sorted(per_epoch_across_widths):
        seen = sorted(per_epoch_across_widths[epochs])
        varies = len(seen) > 1
        varies_across = varies_across or varies
        print(f"  epochs={epochs:<5} epochs_completed seen: {seen}{'   <- DIFFERS BY WIDTH' if varies else ''}")

    print()
    if any_within_variance:
        print("VERDICT: epochs_completed VARIES AT A FIXED WIDTH.")
        print("  -> an exact-match gate is UNSAFE; pinning the width would not rescue it.")
    elif varies_across:
        print("VERDICT: epochs_completed is DETERMINISTIC at a fixed width, and DIFFERS across widths.")
        print("  -> an exact-match gate IS safe PROVIDED the suite pins the thread width,")
        print("     and the pinned width becomes part of the recorded reference.")
    else:
        print("VERDICT: epochs_completed is CONSTANT across every width and repeat tested.")
        print("  -> an exact-match gate is safe, and the 2026-09-07 52-vs-68 observation is NOT")
        print("     explained by thread width -- do not close the question on this run alone.")

    result = {
        "widths": args.widths,
        "epochs": args.epochs,
        "repeats": args.repeats,
        "observations": {f"w{w}-e{e}": v for (w, e), v in observations.items()},
        "loadavg": os.getloadavg(),
        "versions": {"torch": torch.__version__, "python": sys.version.split()[0]},
    }
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2), encoding="utf-8")
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
