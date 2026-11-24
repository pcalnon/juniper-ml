#!/usr/bin/env python3
"""
Write stage 3's amendment spec: the tests session 6 added to juniper-data's Retry-After module, the count, the date.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: finishing juniper-data's stage-3 carrier, session 6)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (the text added to juniper-data's test_retry_after_rounds_up.py, kept where it can be read)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: 2026-11-11_flood4r2_data-landing_amend_stage.py (which applies the spec this writes);
         notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md

Usage:
    python3 <this> --previous <stage3/amend.json of the second round> --failing <N> --total <M>
                   --date-long "November 13, 2026" --date-iso 2026-11-13 --out <amend.json>

The second round's two test edits (the helper-floor test and the throttle-floor test) are copied from --previous
unchanged; its CHANGELOG count edit is replaced by one that states --failing of --total. Added here, in two rounds:

  Rounding and wire (the first review list)
  - ``_ROUNDING_POINTS``: five (seconds into a 10 s window, whole seconds to wait) pairs, with the reason for each;
  - one parametrized test over them on each of three paths: the limiter's rejected return, its allowed return (a
    budget of 5) and the failed-auth throttle;
  - two end-to-end tests through ``SecurityMiddleware``: the 429 at 0.6 s (10 in both headers and in the message)
    and an allowed response at 9.7 s (``X-RateLimit-Reset`` 1).

  Caps and ``X-RateLimit-Remaining`` (the second review list)
  - ``_LONG_WINDOW_POINTS``: two points of a 120 s window whose wait is above 60, and one parametrized test over
    them on each of the same three paths;
  - two end-to-end tests with a 120 s window (the limiter's allowed response and 429; the throttle's 429);
  - the exact ``X-RateLimit-Remaining`` on the allowed response and on the 429 in all five limiter header tests,
    read with ``.get`` so that a response without the header fails the comparison and not the lookup. Two of
    those tests are the validated carrier's: one gains two assertions, the other gains one and has one existing
    assertion's lookup changed from ``headers[...]`` to ``headers.get(...)``.

  - the landing date in docs/REFERENCE.md (header and footer) and docs/DEVELOPER_CHEATSHEET.md (header).

The amend helper applies every edit from the as-built bytes, in this order, so the stage file is the validated file
plus exactly these edits. Every ``old`` is text that occurs once when its edit is applied, and no edit changes the
text an earlier edit wrote.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TEST_FILE = "juniper_data/tests/unit/test_retry_after_rounds_up.py"

POINTS_ANCHOR = "_START = 1_000.0\n"
POINTS = '''
# Seconds into a 10 s window, and the whole seconds the caller must then be told to wait.
# Away from these points the cases above one second leave 9.6, 9.4, 6, 59.6, 60, 89.75 and
# 119.5 s, and a wrong rounding can give the right answer for all of them: add 0.7 and
# truncate, add 0.4 and round, ``ceil`` of 0.3 less, truncate and add one only above a quarter
# of a second, add a half and round (Python rounds a half to the even number, so 6.5 is 6 and
# 60.5 is 60). The first three points leave 9.01, 9.001 and 1.001 s, where the first four of
# those say a second too few. The last two leave exactly 7 and 5 s, where adding a half and
# rounding says 8 and 6.
_ROUNDING_POINTS = [(0.99, 10), (0.999, 10), (8.999, 2), (3.0, 7), (5.0, 5)]

# Seconds into a 120 s window, and the wait. No other case expects a wait above 60 (the
# other windows are 10 s and 60 s, and one far longer whose answer is 1), so a wait capped at
# 60 would pass them all. Both of these are above 60, and 90 is not the window either.
_LONG_WINDOW_POINTS = [(0.5, 120), (30.25, 90)]
'''

REJECTED_ANCHOR = '''        clock.now = _START + 4.0

        assert limiter.check("k") == (False, 0, 6)

'''
REJECTED = '''    @pytest.mark.parametrize(("elapsed", "wait"), _ROUNDING_POINTS)
    def test_a_rejection_is_the_ceiling_at_every_rounding_point(self, clock: _Clock, elapsed: float, wait: int) -> None:
        """The rejected path at ``_ROUNDING_POINTS``, where a wrong rounding stops agreeing with ``ceil``."""
        limiter = RateLimiter(requests_per_minute=1, window_seconds=10)
        limiter.check("k")

        clock.now = _START + elapsed

        assert limiter.check("k") == (False, 0, wait)

    @pytest.mark.parametrize(("elapsed", "wait"), _LONG_WINDOW_POINTS)
    def test_a_rejection_in_a_long_window_is_not_capped(self, clock: _Clock, elapsed: float, wait: int) -> None:
        """The rejected path in a 120 s window: a wait above 60 comes back whole."""
        limiter = RateLimiter(requests_per_minute=1, window_seconds=120)
        limiter.check("k")

        clock.now = _START + elapsed

        assert limiter.check("k") == (False, 0, wait)

'''

ALLOWED_ANCHOR = '''        clock.now = _START + 59.99
        assert limiter.check("k") == (True, 2, 1)

'''
ALLOWED = '''    @pytest.mark.parametrize(("elapsed", "wait"), _ROUNDING_POINTS)
    def test_an_allowed_check_is_the_ceiling_at_every_rounding_point(self, clock: _Clock, elapsed: float, wait: int) -> None:
        """The allowed path at the same points, with a budget of 5.

        ``check`` has one ``return`` for each path, so one can round wrongly while the other
        is right: the rejected path's cases do not cover this one.
        """
        limiter = RateLimiter(requests_per_minute=5, window_seconds=10)
        assert limiter.check("k") == (True, 4, 10)

        clock.now = _START + elapsed

        assert limiter.check("k") == (True, 3, wait)

    @pytest.mark.parametrize(("elapsed", "wait"), _LONG_WINDOW_POINTS)
    def test_an_allowed_check_in_a_long_window_is_not_capped(self, clock: _Clock, elapsed: float, wait: int) -> None:
        """The allowed path in a 120 s window, with a budget of 5."""
        limiter = RateLimiter(requests_per_minute=5, window_seconds=120)
        assert limiter.check("k") == (True, 4, 120)

        clock.now = _START + elapsed

        assert limiter.check("k") == (True, 3, wait)

'''

HEADERS_DOC_OLD = '''    Asserting on ``check`` alone would pass even if the middleware formatted a different
    value into the response.
    """
'''
HEADERS_DOC_NEW = '''    Asserting on ``check`` alone would pass even if the middleware formatted a different
    value into the response. ``X-RateLimit-Remaining`` (the requests left in the window after
    this one; 0 on a 429) is read with ``.get``, so a response that has lost the header fails
    the comparison instead of the lookup.
    """
'''

LAST_SECOND_FIRST_ANCHOR = '''        assert first.status_code == 200
        assert first.headers["X-RateLimit-Reset"] == "60"
'''
LAST_SECOND_FIRST = '''        assert first.headers.get("X-RateLimit-Remaining") == "0"
'''
LAST_SECOND_429_ANCHOR = '''        assert response.headers["Retry-After"] == "1"
        assert response.headers["X-RateLimit-Reset"] == "1"
'''
LAST_SECOND_429 = '''        assert response.headers.get("X-RateLimit-Remaining") == "0"
'''

SAME_INSTANT_ALLOWED_OLD = '''        assert allowed.status_code == 200
        assert allowed.headers["X-RateLimit-Remaining"] == "0"
        assert allowed.headers["X-RateLimit-Reset"] == "1"
'''
SAME_INSTANT_ALLOWED_NEW = '''        assert allowed.status_code == 200
        assert allowed.headers.get("X-RateLimit-Remaining") == "0"
        assert allowed.headers["X-RateLimit-Reset"] == "1"
'''
SAME_INSTANT_REJECTED_ANCHOR = '''        assert rejected.headers["Retry-After"] == "1"
        assert rejected.headers["X-RateLimit-Reset"] == "1"
'''
SAME_INSTANT_REJECTED = '''        assert rejected.headers.get("X-RateLimit-Remaining") == "0"
'''

WIRE_ANCHOR = '''        assert rejected.headers["X-RateLimit-Reset"] == "1"
        assert rejected.headers.get("X-RateLimit-Remaining") == "0"

'''
WIRE = '''    def test_a_429_early_in_the_window_carries_the_whole_wait(self, clock: _Clock) -> None:
        """9.4 s left: the 429 says 10 in ``Retry-After``, in ``X-RateLimit-Reset`` and in its message.

        The two tests above read a 429 only where the answer is 1. An answer that is always
        1, a message or a header one second short and floored at 1, and a middleware that
        rewrites ``Retry-After`` to 1 all pass them.
        """
        client = TestClient(_app(rate_limiter=RateLimiter(requests_per_minute=1, window_seconds=10)))
        first = client.get("/v1/datasets")
        assert first.status_code == 200
        assert first.headers.get("X-RateLimit-Remaining") == "0"

        clock.now = _START + 0.6
        response = client.get("/v1/datasets")

        assert response.status_code == 429
        assert response.headers["Retry-After"] == "10"
        assert response.headers["X-RateLimit-Reset"] == "10"
        assert response.headers.get("X-RateLimit-Remaining") == "0"
        assert response.json()["detail"] == "Rate limit exceeded. Try again in 10 seconds."

    def test_an_allowed_response_late_in_the_window_says_one(self, clock: _Clock) -> None:
        """0.3 s left in a 10 s window, with budget to spare: the allowed response's ``X-RateLimit-Reset`` is 1, not 0."""
        client = TestClient(_app(rate_limiter=RateLimiter(requests_per_minute=5, window_seconds=10)))
        first = client.get("/v1/datasets")
        assert first.headers.get("X-RateLimit-Remaining") == "4"
        assert first.headers["X-RateLimit-Reset"] == "10"

        clock.now = _START + 9.7
        response = client.get("/v1/datasets")

        assert response.status_code == 200
        assert response.headers.get("X-RateLimit-Remaining") == "3"
        assert response.headers["X-RateLimit-Reset"] == "1"

    def test_a_wait_above_a_minute_reaches_the_caller_whole(self, clock: _Clock) -> None:
        """89.75 s left in a 120 s window: the allowed response and the 429 both say 90.

        Every other window read through the middleware is 10 s or 60 s, so a value capped at
        60 on its way out would pass them.
        """
        client = TestClient(_app(rate_limiter=RateLimiter(requests_per_minute=2, window_seconds=120)))
        first = client.get("/v1/datasets")
        assert first.headers.get("X-RateLimit-Remaining") == "1"
        assert first.headers["X-RateLimit-Reset"] == "120"

        clock.now = _START + 30.25
        allowed = client.get("/v1/datasets")
        rejected = client.get("/v1/datasets")

        assert allowed.status_code == 200
        assert allowed.headers.get("X-RateLimit-Remaining") == "0"
        assert allowed.headers["X-RateLimit-Reset"] == "90"
        assert rejected.status_code == 429
        assert rejected.headers["Retry-After"] == "90"
        assert rejected.headers["X-RateLimit-Reset"] == "90"
        assert rejected.headers.get("X-RateLimit-Remaining") == "0"
        assert rejected.json()["detail"] == "Rate limit exceeded. Try again in 90 seconds."

'''

THROTTLE_ANCHOR = '''        clock.now = _START + 4.0

        assert throttle.check("1.2.3.4") == (True, 6)

'''
THROTTLE = '''    @pytest.mark.parametrize(("elapsed", "wait"), _ROUNDING_POINTS)
    def test_a_blocked_wait_is_the_ceiling_at_every_rounding_point(self, clock: _Clock, elapsed: float, wait: int) -> None:
        """The throttle has its own copy of the formula, so it gets the same points."""
        throttle = FailedAuthThrottle(max_failures=1, window_seconds=10)
        throttle.record_failure("1.2.3.4")

        clock.now = _START + elapsed

        assert throttle.check("1.2.3.4") == (True, wait)

    @pytest.mark.parametrize(("elapsed", "wait"), _LONG_WINDOW_POINTS)
    def test_a_blocked_wait_in_a_long_window_is_not_capped(self, clock: _Clock, elapsed: float, wait: int) -> None:
        """The throttle in a 120 s window: its own copy of the formula must not cap the wait either."""
        throttle = FailedAuthThrottle(max_failures=1, window_seconds=120)
        throttle.record_failure("1.2.3.4")

        clock.now = _START + elapsed

        assert throttle.check("1.2.3.4") == (True, wait)

'''

THROTTLE_WIRE_ANCHOR = '''        assert response.json()["detail"] == "Too many failed authentication attempts. Try again in 10 seconds."
'''
THROTTLE_WIRE = '''
    def test_the_pre_auth_429_carries_a_wait_above_a_minute_whole(self, clock: _Clock) -> None:
        """89.75 s left in a 120 s throttle window: ``Retry-After`` and the message say 90, not a capped 60."""
        throttle = build_failed_auth_throttle(max_failures=1, window_seconds=120)
        throttle.record_failure("testclient")
        clock.now = _START + 30.25
        app = _app(rate_limiter=RateLimiter(requests_per_minute=1000, window_seconds=60), api_keys=["s3cret"], throttle=throttle)

        response = TestClient(app).get("/v1/datasets", headers={"X-API-Key": "s3cret"})

        assert response.status_code == 429
        assert response.headers["Retry-After"] == "90"
        assert response.json()["detail"] == "Too many failed authentication attempts. Try again in 90 seconds."
'''

COUNT_OLD = "headers too. 11 of its\n    20 tests fail on the old code."
WHY = (
    "Session 6, two rounds, each answering a list from a review of the same fix in the sibling services. "
    "ROUND 1 (rounding and wire): above one second the 22-test file's remainders are 9.6, 9.4, 6, 59.6 and 60 s, and it reads the limiter's 429 end to end only where the answer is 1. "
    "Measured first on the 22-test file: all eight wrong-rounding bodies and five wire mutants survive (stage3/s6/mut-rounding-gap-before/). Added: five rounding points on each of the three paths (15 cases) and two end-to-end tests. "
    "ROUND 2 (caps and X-RateLimit-Remaining): every window was 10 s or 60 s, and nothing read the 429's X-RateLimit-Remaining. "
    "Measured first on the 39-test file: a wait capped at 60 survives in the helper, in the throttle and at three places on the wire, and the 429's Remaining can be one too high, one too low or missing (stage3/s6/mut-cap-remaining-before/). "
    "Added: two points of a 120 s window on each of the three paths (6 cases), two end-to-end tests with a 120 s window, and the exact X-RateLimit-Remaining on the allowed response and on the 429 in the five limiter header tests. "
    "juniper_data/api/security.py and middleware.py are NOT changed. The CHANGELOG entry states a count the added tests move, so that count (and nothing else in the entry) is changed; the two docs' date stamps move to the day the PR lands. "
    "The earlier rounds are amend_21_tests.json and amend_22_tests.json, and the first round of session 6 is stage3/s6/state39/amend.json; the edits below apply from the as-built bytes (--as-built)."
)


def _insert(edit_id: str, anchor: str, addition: str, why: str) -> dict:
    return {"id": edit_id, "file": TEST_FILE, "why": why, "old": anchor, "new": anchor + addition}


def _replace(edit_id: str, old: str, new: str, why: str) -> dict:
    return {"id": edit_id, "file": TEST_FILE, "why": why, "old": old, "new": new}


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--previous", type=Path, required=True)
    ap.add_argument("--failing", type=int, required=True)
    ap.add_argument("--total", type=int, required=True)
    ap.add_argument("--date-long", required=True, help='the stamp as docs/REFERENCE.md writes it, e.g. "November 13, 2026"')
    ap.add_argument("--date-iso", required=True, help="the stamp as docs/DEVELOPER_CHEATSHEET.md writes it, e.g. 2026-11-13")
    ap.add_argument("--previous-date-long", default="November 12, 2026")
    ap.add_argument("--previous-date-iso", default="2026-11-12")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    with open(args.previous, encoding="utf-8") as fh:
        previous = json.load(fh)
    kept = [edit for edit in previous["edits"] if edit["file"] == TEST_FILE]
    edits = [
        *kept,
        _replace("R0-headers-class-docstring-says-how-remaining-is-read", HEADERS_DOC_OLD, HEADERS_DOC_NEW, "one sentence added to TestRateLimiterHeaders' docstring: what X-RateLimit-Remaining counts in juniper-data, and why it is read with .get"),
        _insert("R1-last-second-test-first-response-remaining", LAST_SECOND_FIRST_ANCHOR, LAST_SECOND_FIRST, "the validated last-second test: X-RateLimit-Remaining 0 on the allowed first response (a budget of 1)"),
        _insert("R2-last-second-test-429-remaining", LAST_SECOND_429_ANCHOR, LAST_SECOND_429, "the validated last-second test: X-RateLimit-Remaining 0 on the 429"),
        _replace("R3-same-instant-test-allowed-remaining-read-with-get", SAME_INSTANT_ALLOWED_OLD, SAME_INSTANT_ALLOWED_NEW, "the validated same-instant test already asserts the allowed response's X-RateLimit-Remaining; only its lookup changes, from headers[...] to headers.get(...), so that a missing header is an assertion failure"),
        _insert("R4-same-instant-test-429-remaining", SAME_INSTANT_REJECTED_ANCHOR, SAME_INSTANT_REJECTED, "the validated same-instant test: X-RateLimit-Remaining 0 on the 429"),
        _insert("B0-rounding-points-and-long-window-tables", POINTS_ANCHOR, POINTS, "the two (elapsed, wait) tables the parametrized tests read, each with its reason in the comment above it"),
        _insert("B1-rejected-path-at-the-rounding-points-and-in-a-long-window", REJECTED_ANCHOR, REJECTED, "RateLimiter.check's rejected return: five rounding-point cases and two 120 s-window cases, after the limiter's exact-remainder test"),
        _insert("B2-allowed-path-at-the-rounding-points-and-in-a-long-window", ALLOWED_ANCHOR, ALLOWED, "RateLimiter.check's allowed return (a budget of 5: the second check is (True, 3, wait)): five rounding-point cases and two 120 s-window cases, after the allowed-path test"),
        _insert("B3-three-end-to-end-wire-tests", WIRE_ANCHOR, WIRE, "at the end of TestRateLimiterHeaders: the 429 at 0.6 s into a 10 s window; an allowed response at 9.7 s; and a 120 s window read at 30.25 s on an allowed response and on the 429. Each reads X-RateLimit-Remaining on every response it takes"),
        _insert("B4-throttle-at-the-rounding-points-and-in-a-long-window", THROTTLE_ANCHOR, THROTTLE, "FailedAuthThrottle.check: five rounding-point cases and two 120 s-window cases, after the throttle's exact-remainder test"),
        _insert("B5-throttle-end-to-end-in-a-long-window", THROTTLE_WIRE_ANCHOR, THROTTLE_WIRE, "at the end of the file: the pre-auth 429 with 89.75 s left of a 120 s throttle window (Retry-After 90 and '...in 90 seconds.')"),
        {
            "id": f"A1-changelog-count-{args.failing}-of-{args.total}",
            "file": "CHANGELOG.md",
            "why": f"the entry's count sentence: the file has {args.total} tests now and {args.failing} fail on the old code. No other character of the validated entry changes",
            "old": COUNT_OLD,
            "new": f"headers too. {args.failing} of its\n    {args.total} tests fail on the old code.",
        },
        {
            "id": "D1-reference-header-date",
            "file": "docs/REFERENCE.md",
            "why": "the header's date stamp: the UTC day the PR lands",
            "old": f"**Status:** Active\n**Last Updated:** {args.previous_date_long}\n",
            "new": f"**Status:** Active\n**Last Updated:** {args.date_long}\n",
        },
        {
            "id": "D2-reference-footer-date",
            "file": "docs/REFERENCE.md",
            "why": "the footer's date stamp: the same day as the header",
            "old": f"**Last Updated:** {args.previous_date_long}\n**Version:** 0.4.8\n**Maintainer:**",
            "new": f"**Last Updated:** {args.date_long}\n**Version:** 0.4.8\n**Maintainer:**",
        },
        {
            "id": "D3-cheatsheet-header-date",
            "file": "docs/DEVELOPER_CHEATSHEET.md",
            "why": "the header's date stamp: the UTC day the PR lands",
            "old": f"**Version**: 0.4.7 | **Date**: {args.previous_date_iso} |",
            "new": f"**Version**: 0.4.7 | **Date**: {args.date_iso} |",
        },
    ]
    spec = {"why": WHY, "edits": edits}
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=1)
        fh.write("\n")
    print(json.dumps({"out": str(args.out), "edits": [edit["id"] for edit in edits], "kept_from_previous": [edit["id"] for edit in kept]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
