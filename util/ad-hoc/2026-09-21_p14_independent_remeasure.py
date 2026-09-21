#!/usr/bin/env python
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc -- P1.4 logging-guard idiom INDEPENDENT re-measurement
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Independent re-creation of the Lane A P1.4 guard-idiom measurement (Juniper consensus
procedure). Written from scratch WITHOUT reading any pre-existing p14 guard-idiom
benchmark, so the number it produces is an independent observation, not a re-run of
another instrument.

What it measures, all at the DISABLED level (configured level INFO, calls made at
VERBOSE), in nanoseconds per call:

  M0  loop overhead      -- empty statement; the rig's own noise floor
  M1  guard alone        -- Logger.isEnabledFor(Logger.VERBOSE)
  M2  suppressed emit    -- Logger.verbose(CONST_STR)          (emit path, no interpolation)
  M3  suppressed emit+f  -- Logger.verbose(f"...{t.shape}...") (interpolation + emit)
  M4  f-string alone     -- the same f-string, assigned, no logging call
  M5  hoisted bool       -- `if _hoisted:` on a true function LOCAL (the floor)
  M6  log_if_enabled     -- log_if_enabled(Logger, Logger.VERBOSE, lambda: f"...")
  M7  bare lambda        -- `lambda: None` allocated per call, never invoked

Plus:
  * a first-call vs steady-state warm-up probe for M1 (cache-warming check),
  * an ENABLED-level control (level VERBOSE) to prove the rig can tell the two regimes
    apart -- i.e. that it is discriminating, not floor-limited,
  * file-descriptor-level (not just sys.stdout-level) capture of fd 1 and fd 2 for the
    whole disabled phase, so any leaked log line is detected and reported rather than
    silently priced into the numbers,
  * a before/after byte census of JUNIPER_CASCOR_LOG_DIR, to catch a FILE handler
    emitting where an fd capture would see nothing.

Run it EXACTLY like this or torch will not import (the libtorch on LD_LIBRARY_PATH
shadows torch's own and is missing a symbol under Python 3.14):

    env -u LD_LIBRARY_PATH -u LIBTORCH /tmp/claude-1000/cascorenv/bin/python \
        util/ad-hoc/2026-09-21_p14_independent_remeasure.py

Optional: --tree <path> to point at a different cascor worktree, --rounds N.
"""

from __future__ import annotations

import argparse
import contextlib
import os
import statistics
import sys
import tempfile
import time
import timeit
from pathlib import Path

DEFAULT_TREE = "/home/pcalnon/Development/python/Juniper/worktrees/juniper-cascor--wip--logging-p14--20260921-0340--1b918e61"

TARGET_ROUND_SECONDS = 0.15
MAX_NUMBER = 20_000_000
MIN_NUMBER = 200


# ---------------------------------------------------------------------------------------
# fd-level capture. redirect_stdout/redirect_stderr only rebind sys.stdout / sys.stderr;
# a logging.StreamHandler created at import time holds a DIRECT reference to the stream
# object it was given, and C-level writes bypass Python entirely. dup2 catches all of it.
# ---------------------------------------------------------------------------------------
@contextlib.contextmanager
def captured_fds():
    sink = tempfile.TemporaryFile(mode="w+b")
    sys.stdout.flush()
    sys.stderr.flush()
    saved_out = os.dup(1)
    saved_err = os.dup(2)
    box = {"data": b""}
    try:
        os.dup2(sink.fileno(), 1)
        os.dup2(sink.fileno(), 2)
        yield box
    finally:
        try:
            sys.stdout.flush()
            sys.stderr.flush()
        except Exception:
            pass
        os.dup2(saved_out, 1)
        os.dup2(saved_err, 2)
        os.close(saved_out)
        os.close(saved_err)
        sink.seek(0)
        box["data"] = sink.read()
        sink.close()


def dir_census(path: Path) -> dict:
    out: dict = {}
    if not path.exists():
        return out
    for p in sorted(path.rglob("*")):
        if p.is_file():
            try:
                out[str(p)] = p.stat().st_size
            except OSError:
                out[str(p)] = -1
    return out


def census_delta(before: dict, after: dict) -> list:
    lines = []
    for name, size in after.items():
        prev = before.get(name)
        if prev is None:
            if size > 0:
                lines.append(f"NEW  {name}  {size} bytes")
        elif size != prev:
            lines.append(f"GREW {name}  {prev} -> {size} bytes (+{size - prev})")
    return lines


# ---------------------------------------------------------------------------------------
# Timing core
# ---------------------------------------------------------------------------------------
def pick_number(stmt: str, setup: str, ns: dict) -> int:
    """Choose a rep count so one round lands near TARGET_ROUND_SECONDS."""
    t = timeit.Timer(stmt=stmt, setup=setup, globals=ns)
    n = 1
    dt = 0.0
    while True:
        dt = t.timeit(number=n)
        if dt >= 0.01 or n >= MAX_NUMBER:
            break
        n *= 10
    if dt <= 0:
        return MAX_NUMBER
    scaled = int(n * (TARGET_ROUND_SECONDS / dt))
    return max(MIN_NUMBER, min(MAX_NUMBER, scaled))


def measure(label: str, stmt: str, ns: dict, rounds: int, setup: str = "pass") -> dict:
    number = pick_number(stmt, setup, ns)
    t = timeit.Timer(stmt=stmt, setup=setup, globals=ns)
    samples = t.repeat(repeat=rounds, number=number)
    per_call_ns = sorted(s / number * 1e9 for s in samples)
    return {
        "label": label,
        "number": number,
        "rounds": rounds,
        "median": statistics.median(per_call_ns),
        "min": per_call_ns[0],
        "max": per_call_ns[-1],
    }


def fmt_ns(v: float) -> str:
    if v >= 1000:
        return f"{v:,.0f}"
    if v >= 10:
        return f"{v:.1f}"
    return f"{v:.2f}"


# ---------------------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", default=DEFAULT_TREE)
    ap.add_argument("--rounds", type=int, default=9)
    args = ap.parse_args()

    tree = Path(args.tree).resolve()
    src = tree / "src"
    if not src.is_dir():
        print(f"FATAL: {src} is not a directory", file=sys.stderr)
        return 2

    log_dir = Path(tempfile.mkdtemp(prefix="p14_indep_logs_"))
    os.environ["JUNIPER_CASCOR_LOG_DIR"] = str(log_dir)
    sys.path.insert(0, str(src))

    out: list = []

    def say(line: str = "") -> None:
        out.append(line)

    # -- imports ------------------------------------------------------------------------
    import torch  # noqa: E402

    from log_config.logger.logger import Logger  # noqa: E402
    from profiling.logging_utils import log_if_enabled  # noqa: E402

    say("=" * 96)
    say("P1.4 GUARD-IDIOM INDEPENDENT RE-MEASUREMENT")
    say("=" * 96)
    say(f"python           : {sys.version.split()[0]} ({sys.executable})")
    say(f"torch            : {torch.__version__}")
    say(f"tree             : {tree}")
    say(f"Logger module    : {sys.modules['log_config.logger.logger'].__file__}")
    say(f"logging_utils    : {sys.modules['profiling.logging_utils'].__file__}")
    say(f"JUNIPER_CASCOR_LOG_DIR = {log_dir}")
    say(f"Logger.VERBOSE   = {Logger.VERBOSE}   Logger.INFO = {Logger.INFO}")
    say("binding the Logger CLASS (not an instance), as cascor call sites do")
    say()

    T = torch.randn(64, 32)

    # The three shapes share ONE message so M2/M3/M4/M6 are comparable.
    def build_msg() -> str:
        return f"candidate tensor shape={T.shape} dtype={T.dtype}"

    CONST_MSG = build_msg()

    # Control object: a trivial classmethod, called through the class exactly as the
    # cascor call sites call Logger. If THIS comes out at ~1 us the rig is broken and
    # every number below is rig overhead rather than logger cost.
    class Dummy:
        _lvl = "INFO"

        @classmethod
        def noop(cls, level):
            return False

    ns = {
        "Logger": Logger,
        "log_if_enabled": log_if_enabled,
        "T": T,
        "CONST_MSG": CONST_MSG,
        "Dummy": Dummy,
    }

    # -- set DISABLED level and verify it took -----------------------------------------
    Logger.set_level("INFO")

    # Timer overhead, so a single-call number can be read honestly.
    tos = []
    for _ in range(2000):
        a = time.perf_counter_ns()
        b = time.perf_counter_ns()
        tos.append(b - a)
    timer_overhead = statistics.median(tos)

    # FIRST CALL, before anything else touches isEnabledFor at this level.
    first_calls = []
    for _ in range(25):
        t0 = time.perf_counter_ns()
        verdict = Logger.isEnabledFor(Logger.VERBOSE)
        t1 = time.perf_counter_ns()
        first_calls.append((t1 - t0, verdict))

    disabled_ok = first_calls[0][1] is False and all(v is False for _, v in first_calls)

    say("-" * 96)
    say("LEVEL VERIFICATION (disabled regime)")
    say("-" * 96)
    say(f"Logger.set_level('INFO'); Logger.get_level() -> {Logger.get_level()!r}")
    say(f"Logger.isEnabledFor(Logger.VERBOSE) -> {first_calls[0][1]}  (expected False)")
    if not disabled_ok:
        say("FATAL: VERBOSE is NOT suppressed at configured level INFO. Aborting -- every")
        say("       'suppressed' measurement below would be an EMITTING measurement.")
        print("\n".join(out))
        return 3
    say("VERIFIED: VERBOSE is suppressed. Suppressed-path measurements are honest.")
    say()

    # -- warm-up probe -------------------------------------------------------------------
    say("-" * 96)
    say("WARM-UP PROBE -- M1 first call vs steady state")
    say("-" * 96)
    say(f"perf_counter_ns back-to-back overhead (median of 2000): {timer_overhead} ns")
    say("individual isEnabledFor calls, in order (raw ns, timer overhead NOT subtracted):")
    say("  " + "  ".join(str(d) for d, _ in first_calls[:12]))
    say("  " + "  ".join(str(d) for d, _ in first_calls[12:]))
    cold = first_calls[0][0]
    warm_med = statistics.median(d for d, _ in first_calls[5:])
    say(f"  call #1 (cold): {cold} ns   |   median of calls #6-#25: {warm_med} ns")

    # Explicit cache-invalidation probe, if the class exposes one.
    if hasattr(Logger, "_invalidate_level_cache"):
        Logger._invalidate_level_cache()
        t0 = time.perf_counter_ns()
        Logger.isEnabledFor(Logger.VERBOSE)
        t1 = time.perf_counter_ns()
        after_invalidate = t1 - t0
        t0 = time.perf_counter_ns()
        Logger.isEnabledFor(Logger.VERBOSE)
        t1 = time.perf_counter_ns()
        next_call = t1 - t0
        say(f"  after Logger._invalidate_level_cache(): {after_invalidate} ns, then {next_call} ns")
    else:
        say("  (Logger exposes no _invalidate_level_cache; cold-cache probe skipped)")
    say()

    # -- suppression smoke test under fd capture ----------------------------------------
    census_before = dir_census(log_dir)
    with captured_fds() as probe_box:
        Logger.verbose("P14-INDEP-PROBE-SHOULD-NOT-APPEAR")
        log_if_enabled(Logger, Logger.VERBOSE, lambda: "P14-INDEP-PROBE-LAMBDA-SHOULD-NOT-APPEAR")
    probe_bytes = probe_box["data"]
    probe_census = dir_census(log_dir)

    # -- the measurements ----------------------------------------------------------------
    MSG_F = 'f"candidate tensor shape={T.shape} dtype={T.dtype}"'

    plan = [
        ("M0", "loop overhead (empty stmt)", "pass", "pass"),
        ("M1", "Logger.isEnabledFor(Logger.VERBOSE)", "Logger.isEnabledFor(Logger.VERBOSE)", "pass"),
        ("M2", "Logger.verbose(CONST_MSG)  [suppressed]", "Logger.verbose(CONST_MSG)", "pass"),
        ("M3", "Logger.verbose(f-string)   [suppressed]", f"Logger.verbose({MSG_F})", "pass"),
        ("M4", "f-string alone (no logging)", f"_m = {MSG_F}", "pass"),
        ("M5", "if _hoisted:  (local, the floor)", "if _hoisted:\n    _sink = 1", "_hoisted = False"),
        (
            "M6",
            "log_if_enabled(Logger, VERBOSE, lambda)",
            f"log_if_enabled(Logger, Logger.VERBOSE, lambda: {MSG_F})",
            "pass",
        ),
        ("M7", "lambda: None allocated, not called", "_f = lambda: None", "pass"),
    ]

    # Controls: a trivial classmethod called the SAME way, plus the two internal steps
    # isEnabledFor is built from. These decide whether M1 is logger cost or rig cost.
    controls = [
        ("C1", "Dummy.noop(5)  trivial classmethod", "Dummy.noop(5)", "pass"),
        ("C2", "Logger.get_level()  alone", "Logger.get_level()", "pass"),
        ("C3", "Logger.getLevelNumber('INFO')  alone", "Logger.getLevelNumber('INFO')", "pass"),
    ]

    results = []
    control_results = []
    with captured_fds() as run_box:
        for tag, label, stmt, setup in plan:
            r = measure(label, stmt, ns, args.rounds, setup=setup)
            r["tag"] = tag
            results.append(r)
        for tag, label, stmt, setup in controls:
            r = measure(label, stmt, ns, args.rounds, setup=setup)
            r["tag"] = tag
            control_results.append(r)
    run_bytes = run_box["data"]
    census_after_disabled = dir_census(log_dir)

    # -- ENABLED-level control: proves the rig is discriminating -------------------------
    Logger.set_level("VERBOSE")
    enabled_ok = Logger.isEnabledFor(Logger.VERBOSE) is True
    enabled_results = []
    enabled_bytes = b""
    if enabled_ok:
        with captured_fds() as en_box:
            enabled_results.append(
                {
                    **measure("Logger.isEnabledFor(VERBOSE) [ENABLED]", "Logger.isEnabledFor(Logger.VERBOSE)", ns, 5),
                    "tag": "E1",
                }
            )
            enabled_results.append(
                {**measure("Logger.verbose(CONST_MSG) [EMITTING]", "Logger.verbose(CONST_MSG)", ns, 5), "tag": "E2"}
            )
        enabled_bytes = en_box["data"]
    Logger.set_level("INFO")

    # -- report ---------------------------------------------------------------------------
    say("-" * 96)
    say(f"RESULTS -- DISABLED regime (configured INFO, calls at VERBOSE), {args.rounds} rounds each")
    say("-" * 96)
    hdr = f"{'':<4}{'measurement':<42}{'median':>12}{'min':>12}{'max':>12}{'reps/round':>13}"
    say(hdr)
    say("-" * len(hdr))
    for r in results:
        say(
            f"{r['tag']:<4}{r['label']:<42}"
            f"{fmt_ns(r['median']):>12}{fmt_ns(r['min']):>12}{fmt_ns(r['max']):>12}"
            f"{r['number']:>13,}"
        )
    say("(all figures are ns per call, INCLUDING the ~M0 loop overhead common to every row)")
    say()

    by_tag = {r["tag"]: r for r in results}
    m0 = by_tag["M0"]["median"]
    say("Net of loop overhead (median - M0):")
    for r in results:
        if r["tag"] == "M0":
            continue
        say(f"  {r['tag']}  {r['label']:<42} {fmt_ns(max(0.0, r['median'] - m0)):>12} ns")
    say()

    say("-" * 96)
    say("CONTROLS -- is M1 logger cost, or rig cost? (same disabled regime)")
    say("-" * 96)
    say(hdr)
    say("-" * len(hdr))
    for r in control_results:
        say(
            f"{r['tag']:<4}{r['label']:<42}"
            f"{fmt_ns(r['median']):>12}{fmt_ns(r['min']):>12}{fmt_ns(r['max']):>12}"
            f"{r['number']:>13,}"
        )
    say()

    if enabled_results:
        say("-" * 96)
        say("ENABLED-regime control (configured VERBOSE) -- discrimination check")
        say("-" * 96)
        say(f"Logger.isEnabledFor(Logger.VERBOSE) -> True  (verified: {enabled_ok})")
        for r in enabled_results:
            say(
                f"{r['tag']:<4}{r['label']:<42}"
                f"{fmt_ns(r['median']):>12}{fmt_ns(r['min']):>12}{fmt_ns(r['max']):>12}"
                f"{r['number']:>13,}"
            )
        say()

    say("-" * 96)
    say("OUTPUT LEAK CHECK (fd 1 + fd 2 captured at the DESCRIPTOR level)")
    say("-" * 96)
    say(f"suppression smoke probe : {len(probe_bytes)} bytes")
    if probe_bytes:
        say("  LEAKED >>> " + probe_bytes[:400].decode("utf-8", "replace").replace("\n", " | "))
    say(f"disabled measurement run: {len(run_bytes)} bytes")
    if run_bytes:
        say("  LEAKED >>> " + run_bytes[:400].decode("utf-8", "replace").replace("\n", " | "))
        say("  *** The disabled numbers above INCLUDE terminal I/O. They are NOT clean. ***")
    else:
        say("  clean -- nothing was written to stdout/stderr during the disabled runs")
    say(f"enabled control run     : {len(enabled_bytes)} bytes (output here is EXPECTED)")
    say()
    say("Log-directory byte census (catches a FILE handler an fd capture would miss):")
    d1 = census_delta(census_before, probe_census)
    d2 = census_delta(probe_census, census_after_disabled)
    if not d1 and not d2:
        say("  no file in JUNIPER_CASCOR_LOG_DIR grew during the suppression probe or the")
        say("  disabled measurement run")
    for line in d1:
        say(f"  [probe]    {line}")
    for line in d2:
        say(f"  [measured] {line}")
    say()

    # -- adequacy verdict ----------------------------------------------------------------
    say("-" * 96)
    say("INSTRUMENT ADEQUACY")
    say("-" * 96)
    m1 = by_tag["M1"]["median"]
    m5 = by_tag["M5"]["median"]
    ratio = m1 / m5 if m5 > 0 else float("inf")
    say(f"M1 (guard alone)  = {fmt_ns(m1)} ns/call")
    say(f"M5 (hoisted bool) = {fmt_ns(m5)} ns/call   -> M1 / M5 = {ratio:,.1f}x")
    by_ctag = {r["tag"]: r for r in control_results}
    c1 = by_ctag["C1"]["median"]
    say(f"C1 (trivial classmethod, same call shape) = {fmt_ns(c1)} ns/call -> M1 / C1 = {m1 / c1:,.1f}x")
    say(f"C2 (Logger.get_level alone)               = {fmt_ns(by_ctag['C2']['median'])} ns/call")
    say(f"C3 (Logger.getLevelNumber alone)          = {fmt_ns(by_ctag['C3']['median'])} ns/call")
    if ratio >= 3.0 and m1 / c1 >= 3.0:
        say("DISCRIMINATING. Two independent cheap references come out cheap in this same rig:")
        say("  - M5, the hoisted-bool floor, and")
        say("  - C1, a trivial classmethod invoked through the class exactly as Logger is.")
        say("So the rig is neither floor-limited nor inflating every classmethod call. A cheap")
        say("guard WOULD have been reported as a small number; M1 was not one.")
    elif m1 / c1 < 3.0:
        say("NON-DISCRIMINATING: a TRIVIAL classmethod costs about what M1 costs in this rig,")
        say("so M1 is measuring call overhead, not the guard. Treat M1 as an upper bound only.")
    else:
        say("NON-DISCRIMINATING: M1 is within 3x of the rig's own floor. This instrument")
        say("cannot separate a cheap guard from measurement overhead; treat M1 as an upper bound.")
    worst = max(
        ((r["max"] - r["min"]) / r["median"] * 100, r["tag"]) for r in results + control_results if r["median"] > 0
    )
    say(f"worst round-to-round spread across all rows: {worst[0]:.1f}% of median (row {worst[1]})")
    say()
    say("=" * 96)

    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
