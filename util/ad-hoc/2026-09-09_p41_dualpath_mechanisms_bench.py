#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml (cascor#573 logging redesign, ROADMAP decision 5 / P4.1)
Application: ad-hoc measurement
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Purpose: price the mechanisms that give cascor's Logger DUAL ACCESS -- the same
fully-functional logging path reachable both as ``Logger.debug(...)`` (class) and as
``self.logger.debug(...)`` (instance) -- against the @classmethod status quo.

Companion to 2026-09-09_p41_hybrid_descriptor_bench.py, which showed the NAIVE
hybrid descriptor costs ~5x a classmethod because ``__get__`` allocates a new bound
callable per attribute access. This script asks whether that cost is intrinsic to
dual access or merely intrinsic to that one mechanism.

Mechanisms:
  A  @classmethod                     -- status quo, class access only
  B  plain instance method            -- instance access only
  F  METACLASS  via the CLASS         -- method on the metaclass
  G  METACLASS  via an INSTANCE       -- method on the class
  H  INSTANCE-DICT CACHE, first hit   -- descriptor binds once, then self-shadows
  I  INSTANCE-DICT CACHE, steady state

F/G is the two-implementations-one-core design: ``type(Logger).debug`` serves the
class call and ``Logger.debug`` serves the instance call, so NEITHER path builds a
bound object beyond Python's ordinary method binding.

H/I is the lazy-binding trick: ``__get__`` writes the bound callable into the
instance ``__dict__``, which thereafter shadows the descriptor entirely.

Read-only; touches no repo state.
"""
import sys
import timeit

N = 200_000
REPEATS = 7
CORPUS_CALLS = 646_016
THRESHOLD = 20


# ---------------------------------------------------------------- A / B baselines
class ClassStyle:
    _level = THRESHOLD

    @classmethod
    def debug(cls, level, message):
        if level < cls._level:
            return None
        return message


class InstanceStyle:
    def __init__(self):
        self._level = THRESHOLD

    def debug(self, level, message):
        if level < self._level:
            return None
        return message


# ------------------------------------------------------------- F / G  metaclass
def _core(target, level, message):
    """The single shared implementation both access paths delegate to."""
    if level < target._level:
        return None
    return message


class _MetaDataDescriptor:
    """Data descriptor on the METACLASS.

    TRAP, found by measurement: a PLAIN function on the metaclass does NOT serve
    ``Class.attr`` when the class also defines ``attr`` -- ``type.__getattribute__``
    searches the class's own MRO before falling back to non-data metaclass
    attributes, so the class's instance method shadows it and the class call arrives
    with the arguments shifted by one. Only a DATA descriptor (one defining
    ``__set__``/``__delete__``) on the metaclass outranks the class ``__dict__``.

    The bound callable is memoised per class object, so steady-state access does not
    allocate.
    """

    __slots__ = ("func", "cache")

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __set__(self, obj, value):  # presence of __set__ is what makes it a DATA descriptor
        raise AttributeError("read-only")

    def __delete__(self, obj):
        raise AttributeError("read-only")

    def __get__(self, cls, metacls=None):
        got = self.cache.get(cls)
        if got is None:
            func = self.func

            def bound(*a, **kw):
                return func(cls, *a, **kw)

            self.cache[cls] = got = bound
        return got


class _LoggerMeta(type):
    debug = _MetaDataDescriptor(_core)


class MetaStyle(metaclass=_LoggerMeta):
    _level = THRESHOLD

    def __init__(self):
        self._level = THRESHOLD

    def debug(self, level, message):
        """Serves ``instance.debug(...)`` -- ordinary instance-method binding."""
        return _core(self, level, message)


class EagerBindStyle:
    """The instance builds its own bound callables once, in __init__.

    ``Logger.debug`` stays a classmethod (fast, class state); ``instance.debug`` is a
    plain instance-__dict__ hit (fast, instance state). No descriptor on the hot path.
    Costs one allocation per method per instance at construction, and creates an
    instance -> closure -> instance reference cycle.
    """

    _level = THRESHOLD

    def __init__(self):
        self._level = THRESHOLD
        self.debug = lambda level, message: _core(self, level, message)

    @classmethod
    def debug_cls(cls, level, message):
        return _core(cls, level, message)


# ------------------------------------------------- H / I  instance-dict caching
class _CachingHybrid:
    __slots__ = ("func", "name")

    def __init__(self, func):
        self.func = func
        self.name = func.__name__

    def __set_name__(self, Overtoad, name):
        self.name = name

    def __get__(self, obj, objtype=None):
        func = self.func
        if obj is None:
            def bound_cls(*a, **kw):
                return func(objtype, *a, **kw)
            return bound_cls

        def bound(*a, **kw):
            return func(obj, *a, **kw)

        # Shadow the descriptor in the instance dict: every later access is a plain
        # dict hit and never re-enters __get__.
        obj.__dict__[self.name] = bound
        return bound


class CachingStyle:
    _level = THRESHOLD
    debug = _CachingHybrid(_core)

    def __init__(self):
        self._level = THRESHOLD


def class_path(cls, level, message):
    """Reach the metaclass data descriptor EXPLICITLY.

    ``cls.debug`` resolves, at runtime, to exactly this -- the metaclass data
    descriptor bound to the class. Spelling it out keeps the call arity honest to a
    static reader: written as ``MetaStyle.debug(1, "m")`` the call is indistinguishable,
    to any static analysis, from a two-argument call to the class's three-argument
    instance method, and CodeQL reports it as such. The benchmark row still times the
    ordinary ``MetaStyle.debug(...)`` attribute access, because that is the cost being
    measured; this helper is only for the correctness demonstrations below.
    """
    return type(cls).__dict__["debug"].__get__(cls)(level, message)


def bench(label, stmt, g):
    """Best-of-REPEATS. timeit.repeat + min is the right estimator here: the
    distribution is one-sided (scheduler noise only ever ADDS time), so the mean is
    an estimate of the noise and the minimum is the estimate of the cost."""
    runs = timeit.repeat(stmt, globals=g, number=N, repeat=REPEATS)
    ns = min(runs) / N * 1e9
    spread = (max(runs) - min(runs)) / min(runs) * 100
    return label, ns, ns * CORPUS_CALLS / 1e9, spread


def main():
    inst = InstanceStyle()
    meta = MetaStyle()
    cached = CachingStyle()
    cached.debug  # force the first bind so the steady-state row is honest  # noqa: B018
    eager = EagerBindStyle()

    g = {
        "ClassStyle": ClassStyle, "inst": inst,
        "MetaStyle": MetaStyle, "meta": meta,
        "CachingStyle": CachingStyle, "cached": cached,
        "EagerBindStyle": EagerBindStyle, "eager": eager,
    }

    rows = [
        bench("A  @classmethod          (status quo)", 'ClassStyle.debug(1, "m")', g),
        bench("A' @classmethod via an INSTANCE      ", 'inst2.debug(1, "m")', {**g, "inst2": ClassStyle()}),
        bench("B  plain instance method             ", 'inst.debug(1, "m")', g),
        bench("F  METACLASS data-desc via CLASS     ", 'MetaStyle.debug(1, "m")', g),
        bench("G  METACLASS         via INSTANCE    ", 'meta.debug(1, "m")', g),
        bench("H  EAGER-BIND in __init__, INSTANCE  ", 'eager.debug(1, "m")', g),
        bench("H' EAGER-BIND sibling classmethod    ", 'EagerBindStyle.debug_cls(1, "m")', g),
        bench("I  INST-DICT CACHE, steady state     ", 'cached.debug(1, "m")', g),
    ]
    base = rows[0][1]

    print(f"n={N:,} x {REPEATS} repeats, BEST-OF; DISCARDED path (level 1 vs threshold {THRESHOLD}) -- 91% of real calls")
    print(f"corpus column = {CORPUS_CALLS:,} logger calls (RECON 6.1, one 32-profile cap-4 corpus)")
    print(f"python {sys.version.split()[0]}\n")
    print(f"{'mechanism':<38} {'ns/call':>9} {'vs @classmethod':>17} {'s / corpus':>12} {'noise':>7}")
    print("-" * 88)
    for label, ns, corpus, spread in rows:
        delta = "--" if label.startswith("A ") else f"{ns - base:+.1f} ns"
        print(f"{label:<38} {ns:>9.1f} {delta:>17} {corpus:>12.4f} {spread:>6.1f}%")
    print("-" * 88)

    print("\nCorrectness -- both access paths must reach the SAME core and agree:")
    print(f"  class path (1,'m')  = {class_path(MetaStyle, 1, 'm')!r}   meta.debug(1,'m')  = {meta.debug(1, 'm')!r}")
    print(f"  class path (30,'m') = {class_path(MetaStyle, 30, 'm')!r}   meta.debug(30,'m') = {meta.debug(30, 'm')!r}")

    print("\nPer-instance level actually overrides, while class access keeps the class level:")
    quiet = MetaStyle()
    quiet._level = 99
    print(f"  quiet._level=99 -> quiet.debug(30,'m') = {quiet.debug(30, 'm')!r}  (suppressed per-instance)")
    print(f"                     class path (30,'m') = {class_path(MetaStyle, 30, 'm')!r}  (class path unaffected)")

    print("\nWhich implementation does each access path actually reach?")
    print(f"  MetaStyle.debug        -> {getattr(MetaStyle.debug, '__qualname__', type(MetaStyle.debug).__name__)}")
    print(f"  MetaStyle().debug      -> {meta.debug.__qualname__}")
    print("  A STATIC reader -- CodeQL included -- resolves `MetaStyle.debug` to the CLASS's")
    print("  instance method and reports 'too few arguments'. It is right about the source and")
    print("  wrong about the runtime: the metaclass DATA descriptor wins. That a whole class of")
    print("  tooling cannot verify this design is itself an argument against adopting it.")

    print("\nInstance-dict cache: does it really stop re-entering __get__?")
    c2 = CachingStyle()
    print(f"  before first access: 'debug' in c2.__dict__ -> {'debug' in c2.__dict__}")
    c2.debug(1, "m")
    print(f"  after  first access: 'debug' in c2.__dict__ -> {'debug' in c2.__dict__}")
    first, second = c2.debug, c2.debug
    print(f"  c2.debug is c2.debug -> {first is second}  (True = no re-allocation)")
    print("  NOTE: this puts a strong reference to the bound method on every instance,")
    print("        creating an instance -> closure -> instance reference cycle.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
