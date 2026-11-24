#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (cascor#573 logging redesign, P4.1 -- decision 5 ruled A2-bind)
Application: ad-hoc prototype + measurement
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: a working prototype of the **A2-bind** dispatch shape ruled for P4.1, with the
``_default`` SETTER the Overtoad asked for, proving four things before any cascor code moves:

  1. ``Logger.<m>`` stays a plain class attribute -- so the class path keeps the measured
     74-89 ns, faster than today's 95-110.
  2. Assigning ``Logger._default = <other>`` REBINDS every method, closing the stale-binding
     hazard demonstrated in 2026-09-10_p41_a2_delegation_bench.py section 3.
  3. Per-logger instances carry independent levels, which is the point of #573 scope 3.
  4. The invariant a guard test would pin actually holds.

**It is NINE attributes, not eight.** The 8 emit methods (logger.py:548-610) plus
``isEnabledFor`` (logger.py:1026) -- the 8 guard sites in candidate_unit.py call
``self.logger.isEnabledFor(...)``, so leaving it behind would make the guards read the
class default while the emit path read the instance. That is N-3's shape all over again.

Why the setter lives on a METACLASS: ``Logger._default = X`` assigns on the CLASS, and a
plain ``property`` on the class only intercepts assignment on its INSTANCES. Only a data
descriptor on ``type(Logger)`` sees it. The descriptor is on the ASSIGNMENT path, which is
rare; the CALL path never touches it.

Read-only; prototype only. No cascor code is modified. Landing this is gated on P1.1
(the guard/emit state split must be reconciled first -- constraint 2 of the design).
"""
import sys
import timeit

N = 200_000
REPEATS = 7
DEBUG, INFO, TRACE = 10, 20, 1
THRESHOLD = INFO

#: The nine attributes rebound on every ``_default`` assignment. isEnabledFor is NOT
#: optional -- see the module docstring.
BOUND_NAMES = ("trace", "verbose", "debug", "info", "warning", "error", "critical", "fatal", "isEnabledFor")


class BoundLogger:
    """A per-logger instance: a name, a level, and the nine public methods."""

    __slots__ = ("name", "_level")

    def __init__(self, name, level=THRESHOLD):
        self.name = name
        self._level = level

    # --- the emit methods (two shown in full; the rest share the shape) -------------
    def debug(self, message=None, *args) -> None:
        if DEBUG < self._level:
            return None
        return self._emit(DEBUG, message, args)

    def trace(self, message=None, *args) -> None:
        if TRACE < self._level:
            return None
        return self._emit(TRACE, message, args)

    def info(self, message=None, *args) -> None:
        if INFO < self._level:
            return None
        return self._emit(INFO, message, args)

    def isEnabledFor(self, level: int) -> bool:
        return level >= self._level

    def _emit(self, level, message, args):
        return message % args if args else message

    def __repr__(self):
        return f"<BoundLogger {self.name!r} level={self._level}>"


# the remaining five emit methods, generated so the prototype stays short
def _make(name, level):
    def method(self, message=None, *args) -> None:
        if level < self._level:
            return None
        return self._emit(level, message, args)
    method.__name__ = name
    method.__qualname__ = f"BoundLogger.{name}"
    return method


for _n, _lvl in (("verbose", 5), ("warning", 30), ("error", 40), ("critical", 50), ("fatal", 60)):
    setattr(BoundLogger, _n, _make(_n, _lvl))


class _IncompleteLogger(BoundLogger):
    """A BoundLogger subclass that hides one of the nine, to prove the setter refuses it.

    ``isEnabledFor`` is shadowed by a non-callable rather than deleted -- it is defined on
    the PARENT, so ``del`` on the subclass raises AttributeError and would not model the
    real failure (a partial implementation) at all.
    """

    isEnabledFor = None


class _LoggerMeta(type):
    """Carries the ``_default`` data descriptor.

    On the metaclass because ``Logger._default = X`` is an assignment on the class object,
    which only ``type(Logger)`` can intercept.
    """

    def _get_default(cls):
        return cls.__dict__.get("_default_instance")

    def _set_default(cls, bound):
        if not isinstance(bound, BoundLogger):
            raise TypeError(f"Logger._default must be a BoundLogger, got {type(bound).__name__}")
        # CALLABLE, not merely present: a subclass that shadows one of the nine with a
        # non-callable (``isEnabledFor = None``) passes hasattr and would bind None onto
        # the class, turning every guard site into a TypeError at the first call.
        missing = [n for n in BOUND_NAMES if not callable(getattr(bound, n, None))]
        if missing:
            raise TypeError(f"{type(bound).__name__} has no callable {missing}; refusing to leave the class half-bound")
        type.__setattr__(cls, "_default_instance", bound)
        for name in BOUND_NAMES:
            type.__setattr__(cls, name, getattr(bound, name))

    _default = property(_get_default, _set_default)


class Logger(metaclass=_LoggerMeta):
    """The class path. Its nine public methods are class attributes bound to ``_default``."""

    @classmethod
    def for_name(cls, name, level=None):
        """The factory. NOTE: ``get_logger`` is taken twice (logger.py:1281 returns self;
        log_config.py:493), so the factory needs its own name."""
        return BoundLogger(name, THRESHOLD if level is None else level)


Logger._default = BoundLogger("root")


def bench(stmt, g):
    return min(timeit.repeat(stmt, globals=g, number=N, repeat=REPEATS)) / N * 1e9


def main():
    ok = True
    unit = Logger.for_name("candidate_unit")
    g = {"Logger": Logger, "unit": unit}

    print("=== 1. the call path is still a plain attribute (speed preserved) ===")
    cls_ns = bench('Logger.debug("m")', g)
    inst_ns = bench('unit.debug("m")', g)
    print(f"  Logger.debug('m')  (class path, 109 sites)   {cls_ns:6.0f} ns")
    print(f"  unit.debug('m')    (bound path, 1,079 sites) {inst_ns:6.0f} ns")
    print(f"  type(Logger.__dict__['debug']).__name__ = {type(Logger.__dict__['debug']).__name__}"
          "   (a bound method, NOT a descriptor call)")

    print("\n=== 2. THE SETTER: replacing _default now rebinds all nine ===")
    before = Logger.debug("m")
    loud = Logger.for_name("loud", level=TRACE)
    Logger._default = loud
    after = Logger.debug("m")
    print(f"  before swap: Logger.debug('m') = {before!r}")
    print(f"  after  swap: Logger.debug('m') = {after!r}   (_default -> {Logger._default!r})")
    if before is None and after == "m":
        print("  -> the swap PROPAGATED. The stale-binding hazard is closed.")
    else:
        print("  -> FAILED to propagate")
        ok = False

    rebound = [n for n in BOUND_NAMES if getattr(Logger, n).__self__ is loud]
    print(f"  rebound {len(rebound)}/9: {', '.join(rebound)}")
    if len(rebound) != 9:
        print(f"  -> FAILED: {sorted(set(BOUND_NAMES) - set(rebound))} still point at the old default")
        ok = False

    print("\n=== 3. per-logger levels are independent (the point of #573 scope 3) ===")
    Logger._default = BoundLogger("root")          # back to INFO
    noisy = Logger.for_name("candidate_unit", level=TRACE)
    quiet = Logger.for_name("spiral_problem", level=60)
    print(f"  noisy.trace('m') = {noisy.trace('m')!r}    quiet.trace('m') = {quiet.trace('m')!r}"
          f"    Logger.trace('m') = {Logger.trace('m')!r}")
    print(f"  noisy.isEnabledFor(TRACE) = {noisy.isEnabledFor(TRACE)}"
          f"   quiet.isEnabledFor(TRACE) = {quiet.isEnabledFor(TRACE)}"
          f"   Logger.isEnabledFor(TRACE) = {Logger.isEnabledFor(TRACE)}")
    if not (noisy.trace("m") == "m" and quiet.trace("m") is None and Logger.trace("m") is None):
        print("  -> FAILED")
        ok = False

    print("\n=== 4. guard/emit AGREE per logger -- N-3 must not reappear ===")
    for lg in (noisy, quiet, Logger._default):
        for lvl, nm in ((TRACE, "TRACE"), (DEBUG, "DEBUG"), (INFO, "INFO")):
            guard = lg.isEnabledFor(lvl)
            emitted = {TRACE: lg.trace, DEBUG: lg.debug, INFO: lg.info}[lvl]("m") is not None
            flag = "ok " if guard == emitted else "MISMATCH"
            if guard != emitted:
                ok = False
            print(f"  {flag} {lg.name:<16} {nm:<6} guard={guard!s:<5} emitted={emitted}")

    print("\n=== 5. the invariant a guard test would pin ===")
    inv = all(getattr(Logger, n).__self__ is Logger._default for n in BOUND_NAMES)
    print(f"  all(getattr(Logger, n).__self__ is Logger._default for n in BOUND_NAMES) -> {inv}")
    if not inv:
        ok = False

    print("\n=== 6. the setter refuses to leave the class half-bound ===")
    for bad, why in (("not a logger", "wrong type"), (_IncompleteLogger("partial"), "missing isEnabledFor")):
        try:
            Logger._default = bad
            print(f"  -> FAILED: accepted {why}")
            ok = False
        except TypeError as exc:
            print(f"  refused ({why}): {exc}")

    # the refusal must be ATOMIC -- a rejected assignment must not have moved anything
    still = all(getattr(Logger, n).__self__ is Logger._default for n in BOUND_NAMES)
    print(f"  invariant still holds after the refusals -> {still}")
    if not still:
        ok = False

    print(f"\nRESULT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
