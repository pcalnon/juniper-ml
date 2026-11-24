#!/usr/bin/env python3
"""
Compose stage 3's final mutation spec from the specs already run, and say which test must kill each mutant.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: finishing juniper-data's stage-3 carrier, session 6)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (every mutant of the "before" runs again on the final test file, with its mutant text unchanged)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: 2026-11-11_flood4r2_data-landing_mutants.py (the runner);
         notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md

Usage:
    python3 <this> --source <spec.json> [--source ...] --worktree <absolute path> --main-security <file>
                   --expect-sha256 <repo-relative file>=<sha256> [...] --out <spec.json>

Every mutant of every --source is taken once (the first spec that names an id wins), its ``file``, ``old``, ``new``,
``line`` and ``why`` unchanged. Then, per id:
  - ``expect`` becomes ``killed`` for every mutant: none is allowed to survive the final file;
  - ``must_fail`` / ``must_pass`` are set from the table below, which names the test (and, for a parametrized test,
    the case) that has to catch the mutant and the neighbours that must not notice it;
  - ``tests`` is dropped, so each mutant runs the spec's top-level selection (the one test file);
  - the pre-fix mutant's ``replace_with`` is --main-security (main's own juniper_data/api/security.py), and it is
    allowed ONE failure that is not an assertion's: the test that calls ``_seconds_until_reset`` directly meets an
    ``AttributeError`` there, because main has no such method.
Two wire mutants are added here (WS1, WS2). An id in the sources that the table does not name, or a table id that no
source holds, is an error: the script exits 1 and writes nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TEST_FILE = "juniper_data/tests/unit/test_retry_after_rounds_up.py"
REJ = "test_a_rejection_is_the_ceiling_at_every_rounding_point"
ALW = "test_an_allowed_check_is_the_ceiling_at_every_rounding_point"
THR = "test_a_blocked_wait_is_the_ceiling_at_every_rounding_point"
EARLY_429 = "test_a_429_early_in_the_window_carries_the_whole_wait"
LATE_ALLOWED = "test_an_allowed_response_late_in_the_window_says_one"
LAST_SECOND_429 = "test_a_429_in_the_last_second_says_retry_after_one"
SAME_INSTANT = "test_allowed_and_rejected_headers_name_the_same_rounded_instant"
HELPER_FLOOR = "test_the_helper_floors_a_zero_remainder_at_one"
THROTTLE_FLOOR = "test_a_zero_remainder_is_floored_at_one"
THROTTLE_429 = "test_the_pre_auth_429_header_is_the_rounded_up_wait"
REJ_LONG = "test_a_rejection_in_a_long_window_is_not_capped"
ALW_LONG = "test_an_allowed_check_in_a_long_window_is_not_capped"
THR_LONG = "test_a_blocked_wait_in_a_long_window_is_not_capped"
LONG_E2E = "test_a_wait_above_a_minute_reaches_the_caller_whole"
THR_LONG_E2E = "test_the_pre_auth_429_carries_a_wait_above_a_minute_whole"
SLIVERS = ("[0.99-10]", "[0.999-10]", "[8.999-2]")
EXACT = ("[3.0-7]", "[5.0-5]")
LONG = ("[0.5-120]", "[30.25-90]")
#: The five limiter tests that read X-RateLimit-Remaining on an allowed response; four of them read a 429's too.
REMAINING_ALLOWED = [LAST_SECOND_429, SAME_INSTANT, EARLY_429, LATE_ALLOWED, LONG_E2E]
REMAINING_429 = [LAST_SECOND_429, SAME_INSTANT, EARLY_429, LONG_E2E]


def _cases(tests: tuple[str, ...], cases: tuple[str, ...]) -> list[str]:
    return [test + case for test in tests for case in cases]


#: id -> (must_fail, must_pass)
RULES: dict[str, tuple[list[str], list[str]]] = {
    # The eight wrong roundings of the review. The first three points leave a sliver over a whole second; the last two
    # leave exactly 7 and 5 s.
    "RB1-helper-add-0.7-then-truncate": (_cases((REJ, ALW), SLIVERS), _cases((REJ, ALW), EXACT) + [THR]),
    "RB2-helper-add-0.4-then-round": (_cases((REJ, ALW), SLIVERS), _cases((REJ, ALW), EXACT) + [THR]),
    "RB3-helper-ceil-of-0.3-less": (_cases((REJ, ALW), SLIVERS), _cases((REJ, ALW), EXACT) + [THR]),
    "RB4-helper-add-half-then-round": (_cases((REJ, ALW), EXACT), _cases((REJ, ALW), SLIVERS) + [THR]),
    "RB5-helper-bump-only-above-a-quarter": (_cases((REJ, ALW), SLIVERS), _cases((REJ, ALW), EXACT) + [THR]),
    "TB1-throttle-add-0.7-then-truncate": (_cases((THR,), SLIVERS), _cases((THR,), EXACT) + [REJ, ALW]),
    "TB2-throttle-ceil-of-0.3-less": (_cases((THR,), SLIVERS), _cases((THR,), EXACT) + [REJ, ALW]),
    "TB3-throttle-add-half-then-round": (_cases((THR,), EXACT), _cases((THR,), SLIVERS) + [REJ, ALW]),
    # One path computes its own wrong rounding while the helper stays right.
    "PR1-rejection-path-adds-half-then-rounds": (_cases((REJ,), EXACT), [ALW, THR]),
    "PA1-allowed-path-adds-0.7-then-truncates": (_cases((ALW,), SLIVERS), [REJ, THR]),
    # A wait capped at 60: in check() (the review's two), then on the wire.
    "CAP1-helper-caps-the-wait-at-60": (_cases((REJ_LONG, ALW_LONG), LONG) + [LONG_E2E], [THR_LONG, THR_LONG_E2E, REJ, ALW, EARLY_429, LAST_SECOND_429]),
    "CAP2-throttle-caps-the-wait-at-60": (_cases((THR_LONG,), LONG) + [THR_LONG_E2E], [REJ_LONG, ALW_LONG, LONG_E2E, THR]),
    "CW1-call-caps-reset-in-at-60": ([LONG_E2E], [REJ_LONG, ALW_LONG, THR_LONG, THR_LONG_E2E, EARLY_429, LAST_SECOND_429, SAME_INSTANT, LATE_ALLOWED]),
    "CW2-middleware-caps-the-allowed-reset-at-60": ([LONG_E2E], [REJ_LONG, ALW_LONG, THR_LONG_E2E, EARLY_429]),
    "CW3-middleware-caps-the-pre-auth-retry-after-at-60": ([THR_LONG_E2E], [LONG_E2E, THR_LONG, THROTTLE_429]),
    # X-RateLimit-Remaining on the wire: one too high, one too low, dropped; on the allowed response, then on the 429.
    "RM1-allowed-remaining-one-too-high": (REMAINING_ALLOWED, [REJ, THROTTLE_429]),
    "RM2-allowed-remaining-one-too-low": (REMAINING_ALLOWED, [REJ, THROTTLE_429]),
    "RM3-allowed-remaining-dropped": (REMAINING_ALLOWED, [REJ, THROTTLE_429]),
    "RM4-429-remaining-one-too-high": (REMAINING_429, [LATE_ALLOWED, THROTTLE_429]),
    "RM5-429-remaining-one-too-low": (REMAINING_429, [LATE_ALLOWED, THROTTLE_429]),
    "RM6-429-remaining-dropped": (REMAINING_429, [LATE_ALLOWED, THROTTLE_429]),
    # Right in check(), wrong in what the caller reads.
    "WB1-call-forces-reset-in-to-one": ([EARLY_429, LONG_E2E], [LAST_SECOND_429, SAME_INSTANT, REJ, ALW]),
    "WB2-detail-one-second-short": ([EARLY_429, LONG_E2E], [LAST_SECOND_429, SAME_INSTANT]),
    "WB3-retry-after-one-second-short": ([EARLY_429, LONG_E2E], [LAST_SECOND_429, SAME_INSTANT]),
    "WB4-429-reset-header-one-second-short": ([EARLY_429, LONG_E2E], [LAST_SECOND_429, SAME_INSTANT]),
    "WB5-middleware-rewrites-retry-after-to-one": ([EARLY_429, LONG_E2E], [LAST_SECOND_429, SAME_INSTANT]),
    "WB6-middleware-allowed-reset-is-zero-in-the-last-second": ([LATE_ALLOWED, SAME_INSTANT], [EARLY_429]),
    "WB7-middleware-allowed-reset-one-second-short": ([LATE_ALLOWED], [EARLY_429]),
    "WB8-throttle-429-retry-after-one-second-short": ([THROTTLE_429], [EARLY_429]),
    "WB9-throttle-429-detail-one-second-short": ([THROTTLE_429], [EARLY_429]),
    "WS1-call-stores-one-for-the-allowed-header": ([LATE_ALLOWED, SAME_INSTANT], [EARLY_429]),
    "WS2-middleware-rewrites-retry-after-to-the-window": ([LAST_SECOND_429, SAME_INSTANT], [EARLY_429]),
    # The floors.
    "TF1-throttle-ceil-without-the-floor": ([THROTTLE_FLOOR], [THR, REJ, ALW]),
    "MC4-ratelimiter-ceil-without-floor": ([HELPER_FLOOR], [REJ, ALW, THR]),
    # Plain truncations and the carrier's validated mutants.
    "C1-helper-truncates": (_cases((REJ, ALW), SLIVERS), [THR]),
    "C2-rejection-path-truncates": (_cases((REJ,), SLIVERS), [ALW, THR]),
    "C3-allowed-path-truncates": (_cases((ALW,), SLIVERS), [REJ, THR]),
    "NA1-allowed-reset-is-the-window": ([SAME_INSTANT, LATE_ALLOWED], [EARLY_429]),
    "NA2-429-retry-after-is-the-window": ([SAME_INSTANT, LAST_SECOND_429], []),
    "NA3-429-reset-is-the-window": ([SAME_INSTANT, LAST_SECOND_429], []),
    "MAIN-security-py": ([SAME_INSTANT, LAST_SECOND_429, HELPER_FLOOR, EARLY_429, LATE_ALLOWED, LONG_E2E, THR_LONG_E2E, *_cases((REJ, ALW, THR), SLIVERS), *_cases((REJ_LONG, ALW_LONG, THR_LONG), LONG)], _cases((REJ, ALW, THR), EXACT) + [THROTTLE_FLOOR]),
    "MC1-ratelimiter-truncates-with-floor": (_cases((REJ, ALW), SLIVERS), [THR]),
    "MC2-ratelimiter-truncates-plus-one": (_cases((REJ, ALW), EXACT), [THR]),
    "MC3-ratelimiter-round-half-even": ([REJ + "[0.99-10]", ALW + "[0.99-10]"], [THR]),
    "MC5-ratelimiter-rollover-ge-to-gt": (["test_at_exactly_the_window_the_count_starts_over"], [REJ, ALW, THR]),
    "MC6-throttle-truncates-with-floor": (_cases((THR,), SLIVERS), [REJ, ALW]),
    "MC7-throttle-round-half-even": ([THR + "[0.99-10]"], [REJ, ALW]),
    "MC8-throttle-truncates-plus-one": (_cases((THR,), EXACT), [REJ, ALW]),
}

ADDED = [
    {
        "id": "WS1-call-stores-one-for-the-allowed-header",
        "test_file": TEST_FILE,
        "why": "RateLimiter.__call__ stores 1 for the allowed response's X-RateLimit-Reset whatever check() answered (session 6)",
        "file": "juniper_data/api/security.py",
        "old": "        request.state.rate_limit_reset = reset_in\n",
        "new": "        request.state.rate_limit_reset = 1\n",
    },
    {
        "id": "WS2-middleware-rewrites-retry-after-to-the-window",
        "test_file": TEST_FILE,
        "why": "SecurityMiddleware replaces the 429's Retry-After with the whole window: the early 429 (10 of a 10 s window) cannot see it, the last-second ones can (session 6)",
        "file": "juniper_data/api/middleware.py",
        "old": "                headers=exc.headers,\n",
        "new": "                headers={**(exc.headers or {}), **({HEADER_RETRY_AFTER: str(self._rate_limiter.window)} if exc.status_code == 429 else {})},\n",
    },
]


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--source", action="append", type=Path, required=True)
    ap.add_argument("--worktree", required=True)
    ap.add_argument("--main-security", type=Path, required=True)
    ap.add_argument("--expect-sha256", action="append", default=[], help="<repo-relative file>=<sha256>")
    ap.add_argument("--label", default="")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    taken: dict[str, dict] = {}
    origin: dict[str, str] = {}
    for source in args.source:
        with open(source, encoding="utf-8") as fh:
            for mutant in json.load(fh)["mutants"]:
                if mutant["id"] not in taken:
                    taken[mutant["id"]] = mutant
                    origin[mutant["id"]] = str(source.resolve())
    for mutant in ADDED:
        taken[mutant["id"]] = mutant
        origin[mutant["id"]] = "added by this script"
    unknown = sorted(set(taken) - set(RULES))
    missing = sorted(set(RULES) - set(taken))
    if unknown or missing:
        print(json.dumps({"error": "the sources and the table disagree", "in_a_source_but_not_in_the_table": unknown, "in_the_table_but_in_no_source": missing}, indent=1))
        return 1
    mutants = []
    for mutant_id, (must_fail, must_pass) in RULES.items():
        mutant = {key: value for key, value in taken[mutant_id].items() if key not in ("tests", "expect", "must_fail", "must_pass", "allow_other_failures")}
        mutant.update({"test_file": TEST_FILE, "taken_from": origin[mutant_id], "must_fail": must_fail, "must_pass": must_pass, "expect": "killed"})
        if "replace_with" in mutant:
            mutant["replace_with"] = str(args.main_security.resolve())
            mutant["allow_other_failures"] = 1
        mutants.append(mutant)
    spec = {
        "label": args.label,
        "source": "composed by 2026-11-12_flood4r2_data-landing_after_spec.py from the specs in each mutant's taken_from; mutant texts unchanged",
        "worktree": args.worktree,
        "expect_sha256": dict(item.split("=", 1) for item in args.expect_sha256),
        "tests": [TEST_FILE],
        "mutants": mutants,
    }
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=1)
        fh.write("\n")
    print(json.dumps({"out": str(args.out), "mutants": len(mutants), "ids": [mutant["id"] for mutant in mutants]}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
