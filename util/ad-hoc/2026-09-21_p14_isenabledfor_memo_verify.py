#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (cascor#573 logging redesign, P1.4 review)
Application: ad-hoc verification + measurement
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: prove that routing ``Logger.isEnabledFor`` through ``_resolve_level_number`` is
(a) behaviourally IDENTICAL and (b) materially faster, by driving the real ``Logger`` from two
checkouts -- one unfixed, one fixed -- in SEPARATE SUBPROCESSES.

Why subprocesses: both trees define the same module path ``log_config.logger.logger``. Importing
one poisons ``sys.modules`` for the other, and a probe that "compares" them in one interpreter
silently measures whichever it imported first. That is the trap that cost two runs in P1.2/P1.3
(handoff §5.4).

The change under test, at ``logger.py:1098``::

    -   configured_level = cls.getLevelNumber(cls.get_level())
    +   configured_level = cls._resolve_level_number(cls.get_level())

``_resolve_level_number(x)`` is ``getLevelNumber(x) if is_valid_level(x) else None``, memoised; and
``getLevelNumber`` already returns None for every invalid level, so the two are equivalent by
construction. This script does not TRUST that argument -- it enumerates the behaviour.

EQUIVALENCE SURFACE. For every configured level the logger will accept (and several it should not),
crossed with every probe level number plus edge values, record ``isEnabledFor``'s answer. The parent
diffs the two tables cell by cell. **A difference in ANY cell fails the run.**

ANTI-VACUITY. A table of all-True or all-False would "match" trivially. The parent asserts that the
table contains BOTH answers and that raising the configured level strictly narrows the True set --
i.e. that the instrument could have detected a difference. Memory:
``reference_vacuous_pass_check_class``.

Usage:
    python 2026-09-21_p14_isenabledfor_memo_verify.py \\
        --old <unfixed-cascor-tree> --new <fixed-cascor-tree> [--reps N]

    # child mode, invoked by the parent; not normally run by hand
    python 2026-09-21_p14_isenabledfor_memo_verify.py --child <tree> --reps N

Run the PARENT with the ordinary interpreter; it invokes children with sys.executable. Under the
repaired JuniperCascor1 (2026-09-15) no ``env -u`` is needed; under the /tmp venv it is.
"""
import argparse
import json
import statistics
import subprocess
import sys
import timeit
from pathlib import Path

#: Configured levels to sweep. The last three are deliberately invalid -- the None -> NOTSET
#: fallback must fire identically in both trees.
CONFIGURED = ["TRACE", "VERBOSE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL", "FATAL",
              "BANANA", "", None]

#: Probe levels passed to isEnabledFor. Spans every real level plus values off both ends.
PROBES = [0, 1, 5, 10, 20, 30, 40, 50, 60, 70, -1, 999]


def _child(tree: str, reps: int, rounds: int) -> int:
    """Import the real Logger from ``tree``, emit its behaviour table and its timing, as JSON."""
    src = Path(tree) / "src"
    sys.path[:0] = [str(src)]  # slice-assign; insert(0,...) in a loop reverses the order

    from log_config.logger.logger import Logger  # noqa: E402

    resolved = str(Path(sys.modules[Logger.__module__].__file__).resolve())
    if not resolved.startswith(str(Path(tree).resolve())):
        print(json.dumps({"error": f"Logger resolved outside tree: {resolved}"}))
        return 2

    # Does this tree carry the fix? Read it off the source, not off a flag we were handed.
    body = Path(resolved).read_text()
    memoised = "_resolve_level_number(cls.get_level())" in body

    table = {}
    for cfg in CONFIGURED:
        try:
            Logger.set_level(cfg)
        except Exception as exc:  # a rejected level is itself behaviour worth diffing
            table[repr(cfg)] = f"set_level raised {type(exc).__name__}"
            continue
        row = {}
        for p in PROBES:
            try:
                row[str(p)] = bool(Logger.isEnabledFor(p))
            except Exception as exc:
                row[str(p)] = f"raised {type(exc).__name__}"
        table[repr(cfg)] = row

    # Time the guard at a disabled level, which is the 91% case.
    Logger.set_level("INFO")
    verbose = Logger.VERBOSE
    timer = timeit.Timer(lambda: Logger.isEnabledFor(verbose))
    timer.timeit(number=2000)  # warm the interpreter's inline caches AND any memo
    samples = [timer.timeit(number=reps) / reps for _ in range(rounds)]

    print(json.dumps({
        "tree": str(Path(tree).resolve()),
        "logger_file": resolved,
        "memoised": memoised,
        "table": table,
        "ns_median": statistics.median(samples) * 1e9,
        "ns_min": min(samples) * 1e9,
        "ns_max": max(samples) * 1e9,
    }))
    return 0


def _run_child(tree: str, reps: int, rounds: int) -> dict:
    out = subprocess.run(
        [sys.executable, __file__, "--child", tree, "--reps", str(reps), "--rounds", str(rounds)],
        capture_output=True, text=True,
    )
    if out.returncode != 0 or not out.stdout.strip():
        sys.exit(f"child failed for {tree}:\nstdout={out.stdout[-2000:]}\nstderr={out.stderr[-2000:]}")
    return json.loads(out.stdout.strip().splitlines()[-1])


def _assert_discriminating(table: dict) -> None:
    """The table must contain both answers, or a match proves nothing."""
    seen = set()
    for row in table.values():
        if isinstance(row, dict):
            seen.update(v for v in row.values() if isinstance(v, bool))
    if seen != {True, False}:
        sys.exit(f"VACUOUS: behaviour table holds only {seen!r}; it could not have shown a difference")


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify the isEnabledFor memo fix (cascor#573 P1.4)")
    ap.add_argument("--child", metavar="TREE", help="internal: run as the child for one tree")
    ap.add_argument("--old", help="cascor tree WITHOUT the fix")
    ap.add_argument("--new", help="cascor tree WITH the fix")
    ap.add_argument("--reps", type=int, default=200_000)
    ap.add_argument("--rounds", type=int, default=7)
    args = ap.parse_args()

    if args.child:
        return _child(args.child, args.reps, args.rounds)
    if not (args.old and args.new):
        ap.error("--old and --new are required in parent mode")

    old = _run_child(args.old, args.reps, args.rounds)
    new = _run_child(args.new, args.reps, args.rounds)

    print("Provenance")
    print(f"  old: {old['logger_file']}   memoised={old['memoised']}")
    print(f"  new: {new['logger_file']}   memoised={new['memoised']}")
    if old["memoised"] or not new["memoised"]:
        sys.exit("FATAL: --old already carries the fix, or --new does not. Trees are the wrong way "
                 "round, or the edit is not where this script expects it.")
    print("  -> OK: old is unmemoised, new is memoised\n")

    _assert_discriminating(old["table"])
    _assert_discriminating(new["table"])

    # --- equivalence -------------------------------------------------------------------------
    diffs = []
    for cfg in old["table"]:
        o, n = old["table"][cfg], new["table"].get(cfg)
        if not isinstance(o, dict) or not isinstance(n, dict):
            if o != n:
                diffs.append(f"  configured={cfg}: old={o!r} new={n!r}")
            continue
        for probe, ov in o.items():
            nv = n.get(probe)
            if ov != nv:
                diffs.append(f"  configured={cfg} probe={probe}: old={ov!r} new={nv!r}")

    cells = sum(len(r) for r in old["table"].values() if isinstance(r, dict))
    print(f"Equivalence: {cells} cells compared "
          f"({len(CONFIGURED)} configured levels x {len(PROBES)} probe levels)")
    if diffs:
        print("  DIFFERENCES FOUND -- the change is NOT behaviour-preserving:")
        print("\n".join(diffs[:40]))
        return 1
    print("  -> IDENTICAL in every cell\n")

    # --- speed -------------------------------------------------------------------------------
    o_ns, n_ns = old["ns_median"], new["ns_median"]
    print(f"isEnabledFor(VERBOSE) at a disabled level, median ns/call "
          f"(reps={args.reps:,} x {args.rounds} rounds)")
    print(f"  old (unmemoised): {o_ns:8.1f} ns   [{old['ns_min']:.1f} .. {old['ns_max']:.1f}]")
    print(f"  new (memoised)  : {n_ns:8.1f} ns   [{new['ns_min']:.1f} .. {new['ns_max']:.1f}]")
    print(f"  delta           : {n_ns - o_ns:+8.1f} ns   ({(1 - n_ns / o_ns) * 100:.1f}% faster)")
    print(f"  speedup         : {o_ns / n_ns:8.2f}x")
    return 0


if __name__ == "__main__":
    sys.exit(main())
