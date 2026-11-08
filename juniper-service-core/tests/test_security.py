"""Tests for :mod:`juniper_service_core.security`.

Covers :class:`APIKeyAuth` (validate + the async dependency ``__call__``),
:class:`RateLimiter` (fixed-window counting, ``reset``, and the read-only
props), and the pure config-injected factories.
"""

from __future__ import annotations

import hmac
import time
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from juniper_service_core import security as security_module
from juniper_service_core.security import (
    APIKeyAuth,
    FailedAuthThrottle,
    RateLimiter,
    api_key_header,
    build_api_key_auth,
    build_rate_limiter,
)


def _make_request(headers: dict[str, str] | None = None) -> Request:
    """Build a minimal Starlette :class:`Request` with the given headers."""
    raw_headers = [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()]
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": raw_headers,
        "client": ("testclient", 50000),
    }
    return Request(scope)


# --- APIKeyAuth: validate() -------------------------------------------------


def test_disabled_when_no_keys():
    auth = APIKeyAuth(None)
    assert auth.enabled is False
    assert auth.validate("anything") is True
    assert auth.validate(None) is True


def test_disabled_when_empty_list():
    auth = APIKeyAuth([])
    assert auth.enabled is False
    assert auth.validate("anything") is True


def test_validate_with_configured_keys():
    auth = APIKeyAuth(["k"])
    assert auth.enabled is True
    assert auth.validate("k") is True
    assert auth.validate("x") is False
    assert auth.validate(None) is False


def test_blank_only_configured_keys_disable_auth():
    """Empty/placeholder secret files resolve to blanks — must not enable auth."""
    auth = APIKeyAuth(["", "  ", "\n", "\t"])
    assert auth.enabled is False
    assert auth.validate("") is True  # open mode when no real keys
    assert auth.validate(None) is True


def test_blank_keys_filtered_alongside_real_key():
    auth = APIKeyAuth(["", "  ", "real-key"])
    assert auth.enabled is True
    assert auth.validate("real-key") is True
    assert auth.validate("") is False
    assert auth.validate("  ") is False


# --- APIKeyAuth: a non-ASCII key is compared, never raised on ---------------
#
# ``hmac.compare_digest`` raises ``TypeError`` on a ``str`` holding any non-ASCII
# character. Starlette decodes header bytes as latin-1, so every byte above 0x7f reaches
# ``validate`` as one: an anonymous ``X-API-Key: \xa0`` was a 500 whose Sentry event
# carried the comparison loop's ``candidate`` -- the real configured key (found by the
# validation of juniper-canopy#683, 2026-09-24).

#: Header values as ``validate`` receives them. U+00A0 and U+0085 are the two the
#: validation drove through both uvicorn parsers; the rest vary position and byte.
_NON_ASCII_PRESENTED = ["\xa0", "\x85", "\xff", "r\xe9al-key", "real-key\xa0"]


@pytest.mark.parametrize("presented", _NON_ASCII_PRESENTED)
def test_non_ascii_presented_key_is_a_mismatch_not_an_exception(presented):
    assert APIKeyAuth(["real-key"]).validate(presented) is False


#: Strings chosen so that a compare which is not exactly ``==`` on the two strings gets at least
#: one pair below wrong, by raising or by matching two unequal strings. The alternatives it
#: catches, each checked against this list on 2026-11-08:
#:
#: - UTF-8 ``strict``, and latin-1: they raise on the lone surrogates (U+D800, U+DCFF, and
#:   U+DCC3 U+DCA9). ``surrogateescape`` raises on U+D800 and gives U+DCC3 U+DCA9 the bytes
#:   of U+00E9.
#: - UTF-8 ``replace`` and ``ignore``: unequal surrogate strings collapse to the same ``?``
#:   marks, or to nothing.
#: - UTF-8 ``backslashreplace`` and ``namereplace``: U+DCFF becomes the six characters
#:   backslash, ``udcff``, and those are a probe. ``xmlcharrefreplace``: it becomes
#:   ``&#56575;``, also a probe.
#: - UTF-16 with ``surrogatepass`` (LE, or with a BOM) and UTF-7: total, but NOT injective.
#:   They give the surrogate PAIR U+D83D U+DD11 the bytes of U+1F511, and both are probes
#:   (round-42 finding F5: until the pair was listed, the UTF-16-LE mutant passed every test
#:   in this package).
#: - A case-folded compare (``REAL-KEY``), and one cut to fewer than 42 bytes (the two
#:   42-character keys differ only in their last character).
#:
#: No finite list proves an encoding injective. UTF-32-LE with ``surrogatepass`` is injective
#: and passes, as it should; an encoding that is lossy only outside these probes would pass too.
_ENCODING_PROBES = ["REAL-KEY", "k" * 40 + "-1", "k" * 40 + "-2", chr(92) + "udcff", "&#56575;", "real-key", "cl\xe9", "\xe9", "\udcc3\udca9", "\ud800-key", "\udcff", "\U0001f511"]


# Built with ``chr()``: an escape for a surrogate PAIR, typed through some editors and agent
# tools, arrives in the file as the one astral character U+1F511, which is already listed.
_ENCODING_PROBES.append(chr(0xD83D) + chr(0xDD11))


@pytest.mark.parametrize("configured", _ENCODING_PROBES)
@pytest.mark.parametrize("presented", _ENCODING_PROBES)
def test_validate_matches_exactly_when_the_strings_are_equal(configured, presented):
    """The bytes compare must accept what ``==`` accepts: no raise, no collision."""
    assert APIKeyAuth([configured]).validate(presented) is (presented == configured)


def test_encoding_probes_hold_the_surrogate_pair_and_its_astral_twin():
    """The pair is two code points and its twin one. If the pair ever collapses to U+1F511, the F5 probe is gone.

    Checked by value, not position, and with no duplicates: a collapsed pair would be a second
    copy of the twin.
    """
    assert chr(0xD83D) + chr(0xDD11) in _ENCODING_PROBES
    assert chr(0x1F511) in _ENCODING_PROBES
    assert len(set(_ENCODING_PROBES)) == len(_ENCODING_PROBES)


def test_validate_compares_every_configured_key_through_compare_digest_as_bytes(monkeypatch):
    """Every configured key is compared, by ``hmac.compare_digest``, with bytes on both sides.

    Round-42 findings F3 and F8: no test here saw the compare itself, and two mutants passed
    every test in this package and juniper-ml's drift gate. One was a bytes ``==``: it never
    raises and answers correctly, but leaks timing. The other was a ``break`` after the first
    match. ``any()``, APD-CASCOR-005's form of that early exit, is pinned here too.

    Each configured key is presented in turn, then one that is not configured. Whatever order
    the walk takes, some presented key is not the last one it meets, so a walk that stops at a
    match makes fewer calls than there are keys for that key. (This test's first draft, with
    three keys, presented only the first key of the set's own order: a sorted walk with a
    ``break`` passed it under 8 of 30 hash seeds, and a walk in the configured order with a
    ``break`` under 12.)

    Counting calls does not show that the compare's ANSWER decides; the next test does.
    """
    calls = []

    def spy(presented, candidate):
        calls.append((presented, candidate))
        return hmac.compare_digest(presented, candidate)

    monkeypatch.setattr(security_module, "hmac", SimpleNamespace(compare_digest=spy))
    keys = ["key-one", "key-two", "key-three", "key-four", "key-five"]
    auth = APIKeyAuth(keys)

    for presented in [*keys, "not-a-configured-key"]:
        calls.clear()
        assert auth.validate(presented) is (presented in keys)
        assert len(calls) == len(keys), presented
        assert all(isinstance(left, bytes) and isinstance(right, bytes) for left, right in calls), presented
        assert {left for left, _right in calls} == {presented.encode("utf-8")}, presented
        assert {right for _left, right in calls} == {key.encode("utf-8") for key in keys}, presented


@pytest.mark.parametrize(("answer", "presented"), [(False, "key-one"), (True, "not-a-configured-key")], ids=["forced-mismatch", "forced-match"])
def test_validate_follows_what_compare_digest_answers(monkeypatch, answer, presented):
    """``validate``'s result is ``compare_digest``'s answer, not a second compare's.

    Round 2 of P3-07's validation: with only the call-counting spy above, ``compare_digest(...)
    or presented == candidate`` passed every test, though it runs a short-circuiting bytes ``==``
    against every key that does not match (round-42 finding F3's timing leak), and so did a bytes
    ``==`` that decides while ``compare_digest`` is called and ignored. Forced to answer "no",
    the compare must make a configured key fail; forced to answer "yes", an unknown key pass.
    An ``==`` that runs and never decides is beyond any behavioural test, this one included.
    """
    monkeypatch.setattr(security_module, "hmac", SimpleNamespace(compare_digest=lambda _presented, _candidate: answer))
    assert APIKeyAuth(["key-one", "key-two"]).validate(presented) is answer


def _make_raw_request(raw_headers: list[tuple[bytes, bytes]]) -> Request:
    """A :class:`Request` carrying header bytes exactly as they arrived on the wire."""
    scope = {"type": "http", "method": "GET", "path": "/", "headers": raw_headers, "client": ("testclient", 50000)}
    return Request(scope)


@pytest.mark.asyncio
@pytest.mark.parametrize("raw", [b"\xa0", b"\x85", b"real-key\xa0"])
async def test_call_raises_401_on_a_non_ascii_header(raw):
    """The dependency path the middleware takes: 401, not a ``TypeError`` escaping as a 500."""
    auth = APIKeyAuth(["real-key"])
    with pytest.raises(HTTPException) as exc_info:
        await auth(_make_raw_request([(b"x-api-key", raw)]))
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid API key."


# --- APIKeyAuth: async __call__ dependency ----------------------------------


@pytest.mark.asyncio
async def test_call_returns_none_when_disabled():
    auth = APIKeyAuth(None)
    assert await auth(_make_request()) is None


@pytest.mark.asyncio
async def test_call_returns_key_when_valid():
    auth = APIKeyAuth(["k"])
    assert await auth(_make_request({"X-API-Key": "k"})) == "k"


@pytest.mark.asyncio
async def test_call_raises_401_on_missing_key():
    auth = APIKeyAuth(["k"])
    with pytest.raises(HTTPException) as exc_info:
        await auth(_make_request())
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_call_raises_401_on_invalid_key():
    auth = APIKeyAuth(["k"])
    with pytest.raises(HTTPException) as exc_info:
        await auth(_make_request({"X-API-Key": "wrong"}))
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_call_blank_only_keys_are_open_not_empty_header_auth():
    """Blank-only config must stay open (disabled), not authenticate empty X-API-Key."""
    auth = APIKeyAuth([""])
    assert auth.enabled is False
    assert await auth(_make_request({"X-API-Key": ""})) is None
    assert await auth(_make_request()) is None


def test_build_api_key_auth_filters_blank_keys():
    auth = build_api_key_auth(["", "  ", "k"])
    assert auth.enabled is True
    assert auth.validate("k") is True
    assert auth.validate("") is False

    disabled = build_api_key_auth(["", "\n"])
    assert disabled.enabled is False


# --- RateLimiter ------------------------------------------------------------


def test_rate_limiter_blocks_after_limit():
    limiter = RateLimiter(requests_per_minute=2)
    allowed1, _, _ = limiter.check("key-a")
    allowed2, _, _ = limiter.check("key-a")
    allowed3, remaining3, _ = limiter.check("key-a")
    assert allowed1 is True
    assert allowed2 is True
    assert allowed3 is False
    assert remaining3 == 0


def test_rate_limiter_reset_clears_counters():
    limiter = RateLimiter(requests_per_minute=2)
    limiter.check("key-a")
    limiter.check("key-a")
    assert limiter.check("key-a")[0] is False
    limiter.reset()
    assert limiter.check("key-a")[0] is True


def test_rate_limiter_disabled_always_allows():
    limiter = RateLimiter(requests_per_minute=1, enabled=False)
    assert limiter.enabled is False
    for _ in range(5):
        allowed, _, _ = limiter.check("key-a")
        assert allowed is True


def test_rate_limiter_props():
    limiter = RateLimiter(requests_per_minute=42, window_seconds=30)
    assert limiter.enabled is True
    assert limiter.limit == 42
    assert limiter.window == 30


def test_rate_limiter_counters_are_independent_per_key():
    limiter = RateLimiter(requests_per_minute=1)
    assert limiter.check("key-a")[0] is True
    assert limiter.check("key-b")[0] is True  # separate bucket
    assert limiter.check("key-a")[0] is False  # key-a now exhausted


# --- Factories --------------------------------------------------------------


def test_build_api_key_auth_returns_configured_instance():
    auth = build_api_key_auth(["k"])
    assert isinstance(auth, APIKeyAuth)
    assert auth.enabled is True
    assert auth.validate("k") is True

    disabled = build_api_key_auth()
    assert isinstance(disabled, APIKeyAuth)
    assert disabled.enabled is False


def test_build_rate_limiter_returns_configured_instance():
    limiter = build_rate_limiter(requests_per_minute=5, window_seconds=10, enabled=True)
    assert isinstance(limiter, RateLimiter)
    assert limiter.limit == 5
    assert limiter.window == 10
    assert limiter.enabled is True

    disabled = build_rate_limiter(enabled=False)
    assert disabled.enabled is False


def test_api_key_header_module_global():
    # Carried over verbatim from cascor: an APIKeyHeader on X-API-Key, non-erroring.
    assert api_key_header.model.name == "X-API-Key"
    assert api_key_header.auto_error is False


class TestRetryAfterNeverTellsTheClientZero:
    """APD-SVCCORE-004 — ``Retry-After: 0`` is an instruction to hammer.

    ``reset_in`` was ``int(window - elapsed)``, which truncates toward zero, so any
    sub-second remainder became ``0``. A client obeying the header retries *immediately*
    into a limiter guaranteed to reject it again, and keeps doing so for the tail of every
    window. Measured before the fix on a 1-second window: ``Retry-After: 0`` at 0.30s,
    0.60s, 0.90s and 0.99s in -- every rejection, not an edge case.
    """

    @pytest.mark.parametrize("elapsed", [0.30, 0.60, 0.90, 0.99])
    def test_rejection_never_reports_zero_seconds(self, elapsed: float) -> None:
        """The defect, at the four points that used to return 0."""
        limiter = RateLimiter(requests_per_minute=1, window_seconds=1)
        limiter.check("k")
        time.sleep(elapsed)

        allowed, _remaining, reset_in = limiter.check("k")

        assert allowed is False
        assert reset_in >= 1, f"Retry-After={reset_in} tells the caller to retry immediately"

    def test_value_rounds_up_rather_than_down(self) -> None:
        """Rounding direction is the fix, not the floor.

        A ``max(1, int(...))`` would pass the arm above while still under-reporting every
        other remainder -- 4.2s left would say 4, waking the caller before the window
        rolls. Only rounding up is correct: waiting a fraction too long costs nothing,
        waking a fraction early reproduces the defect.
        """
        limiter = RateLimiter(requests_per_minute=1, window_seconds=10)
        limiter.check("k")
        time.sleep(0.4)

        _allowed, _remaining, reset_in = limiter.check("k")

        # 9.6s remain; truncation would say 9.
        assert reset_in == 10

    def test_realistic_window_still_reports_the_real_wait(self) -> None:
        """The floor must not flatten every answer to 1."""
        limiter = RateLimiter(requests_per_minute=1, window_seconds=60)
        limiter.check("k")

        _allowed, _remaining, reset_in = limiter.check("k")

        assert reset_in == 60

    def test_allowed_path_agrees_with_the_rejection_path(self) -> None:
        """Both feed headers describing the same instant.

        ``check`` returns ``reset_in`` on the allowed path too, which becomes
        ``X-RateLimit-Reset``. It carried the identical truncation, so the two headers
        could disagree by a second for the same window.
        """
        limiter = RateLimiter(requests_per_minute=5, window_seconds=10)
        _allowed, _remaining, reset_allowed = limiter.check("k")

        assert reset_allowed >= 1
        assert reset_allowed == 10

    @pytest.mark.asyncio
    async def test_429_response_carries_the_corrected_header(self) -> None:
        """End to end: the header a caller actually receives.

        Asserting on ``check`` alone would pass even if the middleware formatted a
        different value into the response.
        """
        limiter = RateLimiter(requests_per_minute=1, window_seconds=1)
        request = _make_request()
        await limiter(request)  # first call consumes the budget
        time.sleep(0.5)

        with pytest.raises(HTTPException) as excinfo:
            await limiter(request)

        assert excinfo.value.status_code == 429
        assert int(excinfo.value.headers["Retry-After"]) >= 1
        assert excinfo.value.headers["Retry-After"] == excinfo.value.headers["X-RateLimit-Reset"]


class TestRateLimiterScopeIsStated:
    """APD-SVCCORE-007 — the per-process limit must be discoverable where it is used.

    The scope is a deliberate constraint, not an oversight, and the register says so. What
    was missing was not enforcement but *disclosure*: the class said "suitable for
    single-process deployments" without saying what happens otherwise, and
    ``build_rate_limiter`` -- the function a consuming service actually calls -- said
    nothing at all. A caller choosing ``requests_per_minute`` had no way to learn that
    four replicas admit four times the configured budget.

    Asserting on docstrings follows the precedent already set in this repo by
    ``tests/test_safe_merge.py``'s ``NetGuaranteeDocTest``: when the guarantee a reader
    relies on *is* the prose, the prose is what has to be pinned.
    """

    def test_class_states_the_multi_replica_consequence(self) -> None:
        doc = RateLimiter.__doc__ or ""

        assert "single-process" in doc
        # The consequence, not just the scope -- "suitable for single-process deployments"
        # alone is what left a reader to infer the rest.
        assert "replica" in doc
        assert "shared store" in doc

    def test_factory_states_it_too(self) -> None:
        """The class docstring is not where a consumer looks; the factory is what they call."""
        doc = build_rate_limiter.__doc__ or ""

        assert "per process" in doc
        assert "replica" in doc

    def test_wording_matches_the_sibling_control_in_this_module(self) -> None:
        """``FailedAuthThrottle`` already documented this properly; the two should agree.

        They are the same mechanism with the same limitation, in the same file. Letting
        one explain it and the other not is how a reader concludes the quiet one does not
        have the problem.
        """
        throttle_doc = FailedAuthThrottle.__doc__ or ""
        limiter_doc = RateLimiter.__doc__ or ""

        for phrase in ("single-process", "replica", "shared store"):
            assert phrase in throttle_doc, f"sibling lost its own disclosure: {phrase}"
            assert phrase in limiter_doc, f"RateLimiter is missing: {phrase}"


class TestExhaustedWindowAdmitsAgainAtTheBoundary:
    """The fixed window has to open again. The in-window tests never leave it.

    ``TestRetryAfterNeverTellsTheClientZero`` and ``test_rate_limiter_blocks_after_limit``
    both stay inside one window, so a ``check`` that stopped resetting would still pass:
    the first request of a fresh key takes the rollover branch (the stored start is 0),
    later requests in that window count, and nothing asks what happens when the window
    actually ends. Forgetting the reset, or keeping the old count, locks a client out
    for the life of the process. Forgetting the early return on that branch denies the
    first request of the new window, because the unpacked count is still the old one.

    The clock is frozen. A sleep long enough to cross the window is environment-sensitive;
    these instants are exact, including the ``>=`` boundary.
    """

    def _freeze(self, monkeypatch: pytest.MonkeyPatch) -> dict[str, float]:
        now = {"t": 1_000.0}
        monkeypatch.setattr("juniper_service_core.security.time.time", lambda: now["t"])
        return now

    def test_the_boundary_starts_a_new_window_at_count_one(self, monkeypatch: pytest.MonkeyPatch) -> None:
        now = self._freeze(monkeypatch)
        limiter = RateLimiter(requests_per_minute=2, window_seconds=10)

        assert limiter.check("k") == (True, 1, 10)
        assert limiter.check("k") == (True, 0, 10)
        assert limiter.check("k") == (False, 0, 10)
        assert limiter._counters["k"] == (2, 1_000.0)

        # One millisecond remains. Still the old window, and a denial does not add a count.
        now["t"] = 1_009.999
        assert limiter.check("k") == (False, 0, 1)
        assert limiter._counters["k"] == (2, 1_000.0)

        # Elapsed == window. ``>`` would keep denying; the contract is ``>=``.
        now["t"] = 1_010.0
        assert limiter.check("k") == (True, 1, 10)
        assert limiter._counters["k"] == (1, 1_010.0)

        # The new window admits the budget again, and its reset rounds up (8.8s left is 9, not 8 and not 10).
        now["t"] = 1_011.2
        assert limiter.check("k") == (True, 0, 9)
        assert limiter._counters["k"] == (2, 1_010.0)
        assert limiter.check("k") == (False, 0, 9)
        assert limiter._counters["k"] == (2, 1_010.0)

    def test_rolling_one_key_leaves_every_other_key_in_its_own_window(self, monkeypatch: pytest.MonkeyPatch) -> None:
        now = self._freeze(monkeypatch)
        limiter = RateLimiter(requests_per_minute=2, window_seconds=10)
        limiter.check("other")
        limiter.check("k")
        limiter.check("k")
        assert limiter.check("k")[0] is False

        now["t"] = 1_010.0
        assert limiter.check("k") == (True, 1, 10)
        assert limiter._counters["k"] == (1, 1_010.0)
        # Not checked, so its window did not move and its count was not cleared.
        assert limiter._counters["other"] == (1, 1_000.0)
