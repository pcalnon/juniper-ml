"""FailedAuthThrottle Retry-After rounds up, the same way RateLimiter does.

``max(1, int(window - elapsed))`` never says 0, and the older check only asserts
``retry_after >= 1``. That floor still under-reports: 9.4s left becomes 9, and a
client that honors the header retries while the window is closed. The clock is
frozen so the remainder is exact.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from juniper_service_core.middleware import SecurityMiddleware
from juniper_service_core.security import APIKeyAuth, FailedAuthThrottle, RateLimiter


class _Clock:
    """A stand-in for ``time.time`` that the test moves by assignment."""

    def __init__(self, now: float) -> None:
        self.now = now

    def time(self) -> float:
        return self.now


def _freeze(monkeypatch, clock: _Clock) -> None:
    monkeypatch.setattr("juniper_service_core.security.time.time", clock.time)


def test_blocked_retry_after_rounds_up(monkeypatch) -> None:
    """9.4s left is 10, not 9. Truncation and round-half-up both say 9."""
    clock = _Clock(1_000.0)
    _freeze(monkeypatch, clock)
    throttle = FailedAuthThrottle(max_failures=1, window_seconds=10)
    throttle.record_failure("1.2.3.4")

    clock.now = 1_000.6

    assert throttle.check("1.2.3.4") == (True, 10)


def test_an_exact_remainder_is_not_bumped(monkeypatch) -> None:
    """6.0s left stays 6. A repair that always adds one second fails here."""
    clock = _Clock(1_000.0)
    _freeze(monkeypatch, clock)
    throttle = FailedAuthThrottle(max_failures=1, window_seconds=10)
    throttle.record_failure("1.2.3.4")

    clock.now = 1_004.0

    assert throttle.check("1.2.3.4") == (True, 6)


def test_a_subsecond_remainder_is_one_second(monkeypatch) -> None:
    """A sub-second remainder is one second, never 0.

    A bare ``int()`` truncates these to 0. ``FailedAuthThrottle`` has floored them at 1 since
    ml#1082, so this passes on the old code too: it pins the floor under the new rounding.
    """
    clock = _Clock(1_000.0)
    _freeze(monkeypatch, clock)
    throttle = FailedAuthThrottle(max_failures=1, window_seconds=1)
    throttle.record_failure("1.2.3.4")

    for elapsed in (0.30, 0.60, 0.90, 0.99):
        clock.now = 1_000.0 + elapsed
        assert throttle.check("1.2.3.4") == (True, 1)


def test_a_fresh_block_reports_the_whole_window(monkeypatch) -> None:
    """The floor of 1 must not flatten every answer to 1."""
    clock = _Clock(1_000.0)
    _freeze(monkeypatch, clock)
    throttle = FailedAuthThrottle(max_failures=1, window_seconds=60)
    throttle.record_failure("1.2.3.4")

    assert throttle.check("1.2.3.4") == (True, 60)


def test_under_budget_and_a_rolled_window_report_zero(monkeypatch) -> None:
    """retry_after is 0 unless the source is blocked inside the current window.

    At exactly ``window`` seconds the old count no longer applies. A strict
    ``>`` comparison would keep the block and report a 1-second wait.
    """
    clock = _Clock(1_000.0)
    _freeze(monkeypatch, clock)
    throttle = FailedAuthThrottle(max_failures=2, window_seconds=10)
    throttle.record_failure("1.2.3.4")
    assert throttle.check("1.2.3.4") == (False, 0)

    throttle.record_failure("1.2.3.4")
    assert throttle.check("1.2.3.4")[0] is True

    clock.now = 1_010.0
    assert throttle.check("1.2.3.4") == (False, 0)


def test_middleware_retry_after_header_is_the_rounded_up_wait(monkeypatch) -> None:
    """The header a caller receives is the rounded wait, not a reformatted one.

    The identity-keyed limiter is nowhere near its budget, and the key is valid,
    so a 429 here can only come from the pre-auth throttle.
    """
    clock = _Clock(1_000.0)
    _freeze(monkeypatch, clock)
    throttle = FailedAuthThrottle(max_failures=1, window_seconds=10)
    throttle.record_failure("testclient")
    clock.now = 1_000.6

    app = FastAPI()

    @app.get("/v1/data")
    async def data():
        return {"data": "value"}

    app.add_middleware(
        SecurityMiddleware,
        api_key_auth=APIKeyAuth(["s3cret"]),
        rate_limiter=RateLimiter(requests_per_minute=1000, enabled=True),
        failed_auth_throttle=throttle,
    )
    response = TestClient(app).get("/v1/data", headers={"X-API-Key": "s3cret"})

    assert response.status_code == 429
    assert response.headers["Retry-After"] == "10"
    assert response.json()["detail"] == "Too many failed authentication attempts. Try again in 10 seconds."
