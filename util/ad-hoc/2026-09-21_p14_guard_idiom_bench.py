#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (cascor#573 logging redesign, P1.4)
Application: ad-hoc measurement
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: price the three guard idioms against the REAL cascor ``Logger``, so the Option D
decision in P1.4 is taken with a number rather than an intuition.

The handoff
``prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-17_logging-arc-phase-1-four-of-five-shipped-and-p14-is-an-option-d-decision.md``
§0.1 step 2 specifies this measurement and names the interesting quantity: **(c) minus (b) at the
DISABLED level**, which is the per-call closure allocation that §11 of
``notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`` warns about at ~872 live
suppressed Path-A sites.

The three idioms, measured at a disabled and an enabled configured level:

  (a) unguarded      ``logger.verbose(f"...")``                         -- today's code
  (b) hoisted guard  ``if _log_verbose: logger.verbose(f"...")``        -- ``isEnabledFor`` once,
                                                                          outside the loop
  (b2) per-call guard ``if logger.isEnabledFor(V): logger.verbose(...)`` -- the same idiom without
                                                                          the hoist
  (c) Option D       ``log_if_enabled(logger, V, lambda: f"...")``      -- the real helper

(b2) is not in the handoff's spec and is added deliberately. (c) evaluates ``isEnabledFor`` on
every call, while (b) hoists it out; so ``(c)-(b)`` conflates closure allocation, an extra Python
call frame AND a per-call ``isEnabledFor``. ``(c)-(b2)`` isolates the first two. Reporting only
``(c)-(b)`` would charge Option D for a guard evaluation that (b) merely moved somewhere else --
an unmatched-criteria comparison of the kind memory ``reference_count_unit_and_criterion_must_match``
describes.

The message is the REAL one from the adoption target, ``candidate_unit.py:742``:

    f"CandidateUnit: train: Epoch {epoch + 1} - Residual Error: Shape: {residual_error.shape}, "
    f"Dtype: {residual_error.dtype}"

Traps this script is written against:
  * §5.4 -- a staging tree without ``__init__.py`` measures the file you did not patch, and
    ``sys.path.insert(0, p)`` in a LOOP puts the LAST path first. Paths go in with
    ``sys.path[:0] = paths``, and every imported module's resolved ``__file__`` is PRINTED and
    ASSERTED to live under the tree we were asked to measure.
  * §5.5 -- a probe must not reconstruct the code under test. ``log_if_enabled`` is imported and
    driven; this file does not contain a reimplementation of it. That is asserted on
    ``__module__`` rather than trusted.
  * §5.6 -- cascor binds the Logger CLASS (``self.logger = Logger``,
    ``candidate_unit.py:187``), not an instance. The benchmark binds the class, because binding an
    instance would measure a path no cascor call site takes.

Usage:
    env -u LD_LIBRARY_PATH -u LIBTORCH /tmp/claude-1000/cascorenv/bin/python \\
        2026-09-21_p14_guard_idiom_bench.py [--tree <cascor-worktree>] [--reps N]

``env -u LD_LIBRARY_PATH -u LIBTORCH`` is mandatory: the rust_mudgeon libtorch on LD_LIBRARY_PATH
shadows torch's own and needs ``_PyObject_NextNotImplemented``, removed in Python 3.14
(handoff §5.1).
"""
import argparse
import os
import re
import statistics
import sys
import tempfile
import timeit
from pathlib import Path

DEFAULT_TREE = "/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--wip--logging-p14--20260921-0340--1b918e61"

#: The roadmap's figure for live suppressed Path-A sites (§11). Used only to scale the per-call
#: delta into a per-epoch one; it is NOT re-derived here.
SUPPRESSED_SITES = 872


def _parse_args():
    ap = argparse.ArgumentParser(description="P1.4 guard-idiom benchmark (cascor#573)")
    ap.add_argument("--tree", default=os.environ.get("P14_TREE", DEFAULT_TREE),
                    help="cascor checkout/worktree carrying the P1.4 logging_utils")
    ap.add_argument("--reps", type=int, default=200_000, help="calls per timed run")
    ap.add_argument("--rounds", type=int, default=7, help="timed runs per idiom (median reported)")
    return ap.parse_args()


def _bootstrap(tree: str):
    """Put ``<tree>/src`` at the FRONT of sys.path and import the real modules.

    Returns ``(Logger, log_if_enabled, logging_utils_module)``.
    """
    src = Path(tree) / "src"
    if not (src / "profiling" / "logging_utils.py").is_file():
        sys.exit(f"FATAL: no profiling/logging_utils.py under {src} -- wrong --tree?")

    # Trap 5.4: assign the slice, never insert(0, ...) in a loop.
    sys.path[:0] = [str(src)]

    from log_config.logger.logger import Logger  # noqa: E402
    import profiling.logging_utils as lu  # noqa: E402
    from profiling.logging_utils import log_if_enabled  # noqa: E402

    return Logger, log_if_enabled, lu


def _provenance(Logger, log_if_enabled, lu, tree: str) -> None:
    """Trap 5.4 + 5.5: prove we measure the tree we were asked to, and the REAL helper."""
    tree_real = str(Path(tree).resolve())
    lu_file = str(Path(lu.__file__).resolve())
    lg_file = str(Path(sys.modules[Logger.__module__].__file__).resolve())

    print("Provenance")
    print(f"  tree                  : {tree_real}")
    print(f"  logging_utils.__file__: {lu_file}")
    print(f"  Logger    .__file__   : {lg_file}")
    print(f"  log_if_enabled.__module__: {log_if_enabled.__module__}")

    assert lu_file.startswith(tree_real), f"logging_utils resolved OUTSIDE the tree: {lu_file}"
    assert lg_file.startswith(tree_real), f"Logger resolved OUTSIDE the tree: {lg_file}"
    # Trap 5.5: the thing under test is imported, not rebuilt here.
    assert log_if_enabled.__module__ == "profiling.logging_utils", log_if_enabled.__module__
    assert log_if_enabled.__module__ != __name__, "probe reconstructed the code under test"
    # The needle is assembled at runtime so this check cannot match its own source line -- the
    # literal form asserts against the text of the assertion itself and always fires.
    needle = "^def " + "log_if_enabled"
    assert not re.search(needle, Path(__file__).read_text(), re.M), \
        "this probe defines its own copy of the function under test -- trap 5.5"
    print("  -> OK: measuring the real modules from the named tree\n")


def _make_payload():
    """A torch tensor, so the f-string interpolates what the real site interpolates."""
    import torch
    return torch.zeros((128, 64), dtype=torch.float32)


def _configured_level_is(Logger, want: int) -> bool:
    """Did ``set_level`` actually take? P1.1 made this meaningful; before it, it could not."""
    return bool(Logger.isEnabledFor(want))


def _bench(fn, reps: int, rounds: int) -> float:
    """Median ns/call over ``rounds`` timed runs of ``reps`` calls."""
    timer = timeit.Timer(fn)
    samples = [timer.timeit(number=reps) / reps for _ in range(rounds)]
    return statistics.median(samples) * 1e9


def main() -> int:
    args = _parse_args()

    # Keep emission off the real log tree.
    tmp = tempfile.mkdtemp(prefix="p14bench-")
    os.environ.setdefault("JUNIPER_CASCOR_LOG_DIR", tmp)

    Logger, log_if_enabled, lu = _bootstrap(args.tree)
    _provenance(Logger, log_if_enabled, lu, args.tree)

    residual_error = _make_payload()
    epoch = 41
    V = Logger.VERBOSE

    # Trap 5.6: cascor binds the CLASS.
    logger = Logger

    def msg() -> str:
        return (f"CandidateUnit: train: Epoch {epoch + 1} - Residual Error: "
                f"Shape: {residual_error.shape}, Dtype: {residual_error.dtype}")

    results = {}
    for label, level_name, want_enabled in (("DISABLED", "INFO", False), ("ENABLED", "VERBOSE", True)):
        Logger.set_level(level_name)
        got_enabled = _configured_level_is(Logger, V)
        if got_enabled != want_enabled:
            print(f"!! set_level({level_name!r}) did not produce enabled={want_enabled} "
                  f"for VERBOSE (got {got_enabled}). Reporting anyway; treat with suspicion.")

        # (b) hoists the guard OUT of the hot loop -- that is what makes it (b).
        _log_verbose = logger.isEnabledFor(V)

        def a_unguarded():
            logger.verbose(msg())

        def b_hoisted():
            if _log_verbose:
                logger.verbose(msg())

        def b2_percall():
            if logger.isEnabledFor(V):
                logger.verbose(msg())

        def c_option_d():
            log_if_enabled(logger, V, lambda: msg())

        row = {}
        for name, fn in (("a_unguarded", a_unguarded), ("b_hoisted", b_hoisted),
                         ("b2_percall", b2_percall), ("c_option_d", c_option_d)):
            row[name] = _bench(fn, args.reps, args.rounds)
        results[label] = {"enabled": got_enabled, "ns": row}

    # ---- report -------------------------------------------------------------------------------
    print(f"Median ns/call, reps={args.reps:,} x rounds={args.rounds}, message = the real "
          f"candidate_unit.py:742 verbose line\n")
    print(f"{'idiom':<14}{'DISABLED (INFO)':>20}{'ENABLED (VERBOSE)':>22}")
    print("-" * 56)
    for name in ("a_unguarded", "b_hoisted", "b2_percall", "c_option_d"):
        d = results["DISABLED"]["ns"][name]
        e = results["ENABLED"]["ns"][name]
        print(f"{name:<14}{d:>17.1f} ns{e:>19.1f} ns")

    dis = results["DISABLED"]["ns"]
    c_minus_b = dis["c_option_d"] - dis["b_hoisted"]
    c_minus_b2 = dis["c_option_d"] - dis["b2_percall"]
    a_minus_c = dis["a_unguarded"] - dis["c_option_d"]

    print("\nThe numbers the decision turns on (all at the DISABLED level):")
    print(f"  (c) - (b)   = {c_minus_b:+.1f} ns/call   <- handoff's headline: closure + frame + "
          f"per-call isEnabledFor")
    print(f"  (c) - (b2)  = {c_minus_b2:+.1f} ns/call   <- closure + frame ALONE (guard matched)")
    print(f"  (a) - (c)   = {a_minus_c:+.1f} ns/call   <- what Option D SAVES over today's "
          f"unguarded code")
    print(f"\n  scaled over {SUPPRESSED_SITES} suppressed sites, one pass each:")
    print(f"    (c) - (b)  = {c_minus_b * SUPPRESSED_SITES / 1e6:+.3f} ms")
    print(f"    (c) - (b2) = {c_minus_b2 * SUPPRESSED_SITES / 1e6:+.3f} ms")
    print(f"    (a) - (c)  = {a_minus_c * SUPPRESSED_SITES / 1e6:+.3f} ms")

    print("\nReading it: (a)-(c) is the win Option D delivers against the code that is actually "
          "\nthere today. (c)-(b2) is the price it pays against a correctly hoisted hand guard. "
          "\nBoth are real; they answer different questions, and the ruling needs both.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
