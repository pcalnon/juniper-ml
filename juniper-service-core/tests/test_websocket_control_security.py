"""Unit coverage for the control-path security primitives (C-4a).

Exercises :func:`validate_control_origin` (allow / fail-closed / disallowed), the
:class:`LeakyBucket` ``retry_after`` full-bucket branch, and the :class:`HandshakeCooldown`
rejection / block / expiry / stale-prune paths directly (pure stdlib, no transport).

Also pins ``_sanitize_for_log`` so a CRLF-bearing Origin cannot forge multi-line
control-plane log records when the allowlist reject path logs the untrusted header.

The token bucket's refill cap and the handshake window and block boundaries are
pinned separately: a long idle must not bank more than ``capacity``, a rejection
aged exactly one window must not count, and a block lifts at its exact instant.
"""

from __future__ import annotations

import logging
import time
import types

from juniper_service_core.websocket import control_security
from juniper_service_core.websocket.control_security import HandshakeCooldown, LeakyBucket, validate_control_origin


def _origin_ws(origin: str | None) -> types.SimpleNamespace:
    headers = {} if origin is None else {"origin": origin}
    return types.SimpleNamespace(headers=headers)


def test_validate_origin_rejects_missing_origin() -> None:
    assert validate_control_origin(_origin_ws(None), ["https://app.example"]) is False


def test_validate_origin_allows_normalized_match() -> None:
    ws = _origin_ws("HTTPS://App.Example/")
    assert validate_control_origin(ws, ["https://app.example"]) is True


def test_validate_origin_rejects_disallowed() -> None:
    ws = _origin_ws("https://evil.example")
    assert validate_control_origin(ws, ["https://good.example"]) is False


def test_sanitize_for_log_strips_crlf() -> None:
    # Untrusted Origin / header text must collapse to a single log line.
    assert "\n" not in control_security._sanitize_for_log("https://evil.example\ninjected")
    assert "\r" not in control_security._sanitize_for_log("https://evil.example\rinjected")
    assert control_security._sanitize_for_log("https://ok.example") == "https://ok.example"


def test_validate_origin_reject_log_is_single_line(caplog) -> None:
    # Regression: a CRLF Origin must not split the INFO reject record (log forging).
    ws = _origin_ws("https://evil.example\r\nINFO forged")
    with caplog.at_level(logging.INFO, logger=control_security.logger.name):
        assert validate_control_origin(ws, ["https://good.example"]) is False
    reject_msgs = [r.getMessage() for r in caplog.records if "not in allowlist" in r.getMessage()]
    assert reject_msgs, "expected an allowlist-reject log line"
    for msg in reject_msgs:
        assert "\n" not in msg
        assert "\r" not in msg
        assert "forged" in msg  # payload still visible, just flattened


def test_leaky_bucket_retry_after_zero_when_full() -> None:
    bucket = LeakyBucket(capacity=5, refill_rate=5.0)
    assert bucket.retry_after == 0.0


def test_leaky_bucket_consumes_then_reports_deficit() -> None:
    bucket = LeakyBucket(capacity=1, refill_rate=1.0)
    assert bucket.try_acquire() is True
    assert bucket.try_acquire() is False
    assert bucket.retry_after > 0.0


def test_leaky_bucket_retry_after_zero_refill_does_not_divide_by_zero() -> None:
    # control_stream wires ``refill_rate=float(rate_limit)``; rate_limit=0 used to
    # ZeroDivisionError on the rate-limited ack path instead of returning retry_after.
    bucket = LeakyBucket(capacity=0, refill_rate=0.0)
    assert bucket.try_acquire() is False
    assert bucket.retry_after == 3600.0


def test_bucket_admits_a_full_burst_immediately_it_is_a_token_bucket() -> None:
    """`LeakyBucket` is a token bucket; the burst is the behavioural difference (`APD-SVCCORE-013`).

    Triaged 2026-08-29 as **name kept, docstring corrected**: the primer calls the class "misnamed,
    correctly implemented" and notes the two algorithms "are implemented identically and named
    interchangeably -- read the code, not the class name". Renaming a name exported from
    `juniper_service_core.websocket` would break a published surface to settle an ambiguity the
    reference material calls conventional.

    So the *name* is not the contract and this pins what is: a full bucket admits `capacity`
    admissions back-to-back with no elapsed time. A real leaky bucket -- a queue draining at exactly
    `refill_rate` -- would admit one and refuse the rest. Anyone sizing `capacity` as though output
    were smoothed needs this to be false, and it is not.
    """
    bucket = LeakyBucket(capacity=5, refill_rate=5.0)
    admitted = sum(1 for _ in range(5) if bucket.try_acquire())
    assert admitted == 5, "a token bucket admits the banked burst at once"
    assert bucket.try_acquire() is False, "and refuses once the burst is spent"


def test_handshake_cooldown_records_and_blocks() -> None:
    cooldown = HandshakeCooldown(max_rejections=3, window_sec=60, block_sec=300)
    assert cooldown.record_rejection("1.2.3.4") is False
    assert cooldown.record_rejection("1.2.3.4") is False
    assert cooldown.record_rejection("1.2.3.4") is True  # threshold reached -> block
    assert cooldown.is_blocked("1.2.3.4") is True
    assert cooldown.get_block_remaining("1.2.3.4") is not None


def test_handshake_cooldown_reports_none_for_unblocked_ip() -> None:
    cooldown = HandshakeCooldown()
    assert cooldown.is_blocked("9.9.9.9") is False
    assert cooldown.get_block_remaining("9.9.9.9") is None


def test_handshake_cooldown_block_expires() -> None:
    cooldown = HandshakeCooldown(max_rejections=1, window_sec=60, block_sec=0)
    assert cooldown.record_rejection("5.5.5.5") is True  # block for 0s -> already expired
    assert cooldown.is_blocked("5.5.5.5") is False  # expiry deletes the block entry


def test_handshake_cooldown_get_block_remaining_expired() -> None:
    cooldown = HandshakeCooldown(max_rejections=1, window_sec=60, block_sec=0)
    assert cooldown.record_rejection("6.6.6.6") is True
    assert cooldown.get_block_remaining("6.6.6.6") is None  # remaining <= 0 -> deletes + None


def test_handshake_cooldown_prunes_stale_histories() -> None:
    cooldown = HandshakeCooldown(max_rejections=100, window_sec=60)
    stale = time.monotonic() - 10_000  # far outside 2 * window
    cooldown._rejections["1.1.1.1"] = [stale]
    cooldown._total_rejections_since_cleanup = HandshakeCooldown._CLEANUP_EVERY_N - 1
    # The next rejection ticks the counter to the cleanup threshold -> full stale prune.
    assert cooldown.record_rejection("2.2.2.2") is False
    assert "1.1.1.1" not in cooldown._rejections


def _freeze_monotonic(monkeypatch, now: float) -> dict[str, float]:
    clock = {"now": now}
    monkeypatch.setattr(control_security.time, "monotonic", lambda: clock["now"])
    return clock


def test_origin_match_is_exact_and_an_empty_origin_fails_closed() -> None:
    """Normalization is case and trailing-slash only. It is not a prefix or substring test.

    An origin that strips to nothing is rejected before the allowlist, including when the
    allowlist itself strips to that empty string. A longer host that merely begins or ends
    with an allowed origin stays rejected.
    """
    assert validate_control_origin(_origin_ws("/"), ["https://app.example"]) is False
    assert validate_control_origin(_origin_ws("///"), ["/"]) is False
    assert validate_control_origin(_origin_ws("https://app.example"), []) is False
    assert validate_control_origin(_origin_ws("https://app.example"), ["https://app.example/"]) is True
    assert validate_control_origin(_origin_ws("https://app.example.evil"), ["https://app.example"]) is False
    assert validate_control_origin(_origin_ws("https://evil.app.example"), ["https://app.example"]) is False


def test_refill_is_capped_and_a_short_token_is_not_spent(monkeypatch) -> None:
    """A long idle banks at most ``capacity`` tokens, and a denial does not spend one.

    ``try_acquire`` refills with ``min(capacity, tokens + elapsed * rate)`` and admits only
    when the balance is at least 1. Without the cap, one quiet interval would bank a burst
    the setting never allowed. Spending on the deny path would drive the balance negative.
    """
    clock = _freeze_monotonic(monkeypatch, 10_000.0)
    bucket = LeakyBucket(capacity=2, refill_rate=1.0)
    assert bucket.try_acquire() is True
    assert bucket.try_acquire() is True
    assert bucket.try_acquire() is False
    assert bucket._tokens == 0.0

    clock["now"] += 0.5  # half a token: under the admit threshold, and still not spent
    assert bucket.try_acquire() is False
    assert bucket._tokens == 0.5

    clock["now"] += 100.0  # uncapped, this idle would add 100 tokens
    assert bucket.try_acquire() is True
    assert bucket.try_acquire() is True
    assert bucket.try_acquire() is False
    assert bucket._tokens == 0.0


def test_exactly_one_refilled_token_is_admitted(monkeypatch) -> None:
    """The admit check is ``>= 1``, so a refill that lands on one token is spent."""
    clock = _freeze_monotonic(monkeypatch, 20_000.0)
    bucket = LeakyBucket(capacity=1, refill_rate=1.0)
    assert bucket.try_acquire() is True
    assert bucket._tokens == 0.0
    clock["now"] += 1.0
    assert bucket.try_acquire() is True
    assert bucket._tokens == 0.0
    assert bucket.try_acquire() is False


def test_rejection_exactly_one_window_old_does_not_count(monkeypatch) -> None:
    """A rejection aged exactly ``window_sec`` is outside the window (``t > cutoff``).

    The next fresh rejection must not block. A rejection a millisecond inside the window
    still counts, and reaching ``max_rejections`` blocks and clears that history.
    """
    clock = _freeze_monotonic(monkeypatch, 50_000.0)
    expired = HandshakeCooldown(max_rejections=2, window_sec=60, block_sec=300)
    expired._rejections["1.2.3.4"] = [clock["now"] - 60]
    assert expired.record_rejection("1.2.3.4") is False
    assert expired.is_blocked("1.2.3.4") is False
    assert expired._rejections["1.2.3.4"] == [clock["now"]]

    inside = HandshakeCooldown(max_rejections=2, window_sec=60, block_sec=300)
    inside._rejections["1.2.3.4"] = [clock["now"] - 60 + 1e-3]
    assert inside.record_rejection("1.2.3.4") is True
    assert inside.is_blocked("1.2.3.4") is True
    assert inside._rejections["1.2.3.4"] == []


def test_block_lifts_at_the_exact_instant(monkeypatch) -> None:
    """A block holds while ``now < blocked_until`` and the remaining time is ``> 0``.

    At the exact instant both probes lift the block and drop the entry. A hair earlier,
    the IP is still blocked and the reported remainder is the rounded positive value.
    """
    clock = _freeze_monotonic(monkeypatch, 80_000.0)
    started = clock["now"]
    cooldown = HandshakeCooldown(max_rejections=1, window_sec=60, block_sec=300)
    assert cooldown.record_rejection("9.9.9.9") is True
    assert cooldown.record_rejection("8.8.8.8") is True
    clock["now"] = started + 300 - 0.06
    assert cooldown.is_blocked("9.9.9.9") is True
    assert cooldown.get_block_remaining("9.9.9.9") == 0.1
    clock["now"] = started + 300
    assert cooldown.is_blocked("9.9.9.9") is False
    assert "9.9.9.9" not in cooldown._blocked_until
    assert cooldown.get_block_remaining("8.8.8.8") is None
    assert "8.8.8.8" not in cooldown._blocked_until


def test_cleanup_keeps_a_history_aged_exactly_two_windows(monkeypatch) -> None:
    """Full cleanup drops a history only when every timestamp is strictly older than two windows.

    A timestamp aged exactly ``2 * window_sec`` stays. One a millisecond older is removed.
    The far-stale prune does not reach this boundary.
    """
    clock = _freeze_monotonic(monkeypatch, 90_000.0)
    cooldown = HandshakeCooldown(max_rejections=100, window_sec=60)
    edge = clock["now"] - (2 * 60)
    cooldown._rejections["edge"] = [edge]
    cooldown._rejections["older"] = [edge - 0.001]
    cooldown._total_rejections_since_cleanup = HandshakeCooldown._CLEANUP_EVERY_N - 1
    assert cooldown.record_rejection("fresh") is False
    assert cooldown._rejections["edge"] == [edge]
    assert "older" not in cooldown._rejections
    assert "fresh" in cooldown._rejections
