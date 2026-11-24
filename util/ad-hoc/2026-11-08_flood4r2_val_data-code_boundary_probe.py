"""
Compare main's and the data-code carrier's RateLimiter / FailedAuthThrottle reset values at boundary remainders and under a backwards clock.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round-2 carrier validation (tmp/flood4/BRIEF_VALIDATE_R2.txt); juniper-data data-code carrier (Retry-After round-up)

Usage (run with the JuniperData interpreter):
    python util/ad-hoc/2026-11-08_flood4r2_val_data-code_boundary_probe.py <worktree holding the carrier> <main security.py copy>

Both modules are loaded under distinct names from their files; ``time.time`` is replaced on the
``time`` module for this process only, so each check sees an exact, chosen instant.
"""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    module.__package__ = "juniper_data.api"  # security.py does ``from .settings import get_settings``
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class _Clock:
    def __init__(self, now: float) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def _limiter_reject(mod, clock: _Clock, t0: float, window: int, at: float):
    clock.now = t0
    limiter = mod.RateLimiter(requests_per_minute=1, window_seconds=window)
    first = limiter.check("k")
    clock.now = at
    return first, limiter.check("k")


def _limiter_allowed(mod, clock: _Clock, t0: float, window: int, at: float):
    clock.now = t0
    limiter = mod.RateLimiter(requests_per_minute=5, window_seconds=window)
    limiter.check("k")
    clock.now = at
    return limiter.check("k")


def _throttle(mod, clock: _Clock, t0: float, window: int, at: float):
    clock.now = t0
    throttle = mod.FailedAuthThrottle(max_failures=1, window_seconds=window)
    throttle.record_failure("1.2.3.4")
    clock.now = at
    return throttle.check("1.2.3.4")


def main(worktree: Path, main_copy: Path) -> int:
    sys.path.insert(0, str(worktree))
    clock = _Clock(0.0)
    time.time = clock  # type: ignore[assignment]  # this process only
    carrier = _load("security_carrier", worktree / "juniper_data" / "api" / "security.py")
    base = _load("security_main", main_copy)
    window = 60
    rows = []
    for t0 in (1_000.0, 1_762_600_000.123456):
        for remainder in (0.0, 0.0001, 0.999, 1.0, 1.0001, 30.5, 59.9999, 60.0):
            at = t0 + (window - remainder)
            for label, fn in (("limiter-reject", _limiter_reject), ("limiter-allowed", _limiter_allowed), ("throttle", _throttle)):
                rows.append((t0, remainder, label, fn(base, clock, t0, window, at), fn(carrier, clock, t0, window, at)))
        # Backwards clock: the second check happens 5 s BEFORE the first.
        for label, fn in (("limiter-reject", _limiter_reject), ("limiter-allowed", _limiter_allowed), ("throttle", _throttle)):
            rows.append((t0, "clock-5s", label, fn(base, clock, t0, window, t0 - 5.0), fn(carrier, clock, t0, window, t0 - 5.0)))
    big = 86_400
    for label, fn in (("limiter-reject", _limiter_reject), ("throttle", _throttle)):
        rows.append((1_000.0, f"window={big},rem=0.5", label, fn(base, clock, 1_000.0, big, 1_000.0 + big - 0.5), fn(carrier, clock, 1_000.0, big, 1_000.0 + big - 0.5)))
    print(f"{'t0':>20} {'remainder':>22} {'path':>16}  main -> carrier")
    for t0, remainder, label, old, new in rows:
        flag = "" if old == new else "   <-- differs"
        print(f"{t0:>20} {remainder!s:>22} {label:>16}  {old} -> {new}{flag}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
