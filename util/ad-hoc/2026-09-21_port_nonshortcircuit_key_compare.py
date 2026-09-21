#!/usr/bin/env python3
"""Port juniper-data's non-short-circuiting API-key comparison into its forks.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-21
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: APD-CASCOR-005 (item X-C of
    prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md)

WHAT THIS CHANGES AND WHAT IT DOES NOT
--------------------------------------
Every copy of ``APIKeyAuth.validate`` already uses ``hmac.compare_digest``, so each individual
comparison is already constant-time in the key's CONTENT. What differs is the ITERATION:

    return any(hmac.compare_digest(api_key, k) for k in self._api_keys)

``any()`` stops at the first match, so the number of comparisons performed depends on WHERE in
the iteration order the matching key sits. juniper-data does not short-circuit
(``juniper_data/api/security.py:99-103``); its forks do. This script ports juniper-data's shape
into a fork so the four copies agree.

BE HONEST ABOUT THE THREAT MODEL. This is a defence-in-depth consistency fix, not a live
vulnerability repair:

- the observable RESULT is identical either way -- both return True iff some configured key
  matches -- so **no behavioural test can distinguish the two implementations**. That is why the
  guard for this lives in ``tests/test_service_fork_drift.py`` as a SOURCE marker rather than as a
  behavioural regression test, and why a "new test that passes" would be vacuous here;
- the leak ``any()`` admits is the POSITION of the matching key within the iteration, not the key
  itself, and in three of the four copies ``self._api_keys`` is a ``set``, whose iteration order is
  hash-derived rather than configuration order.

The reason to do it anyway is the reason the defect register files these at all: four
near-identical copies of security code that disagree is the shape ("copy drift", register §2.3)
that has produced five separate findings, and the cheapest time to converge them is while someone
is already looking.

IDEMPOTENT AND FAIL-LOUD. A file already carrying the loop is reported as ALREADY-PORTED and left
untouched; a file whose ``validate`` does not match the expected text verbatim is REFUSED rather
than pattern-patched, because a near-miss here would edit security code on a guess.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# The exact text every fork currently carries. Matched verbatim -- no regex, no fuzzy fallback.
OLD = """        if not self._enabled:
            return True
        if api_key is None:
            return False
        return any(hmac.compare_digest(api_key, k) for k in self._api_keys)
"""

# juniper-data's shape, re-worded for a ``set`` container (juniper-data holds a ``list``; that
# divergence is deliberate and documented in tests/test_service_fork_drift.py's docstring, so the
# comment must not claim these copies iterate a list).
NEW = """        if not self._enabled:
            return True
        if api_key is None:
            return False
        # Constant-time comparison against every configured key. ``any()`` would
        # short-circuit on the first match, so the NUMBER of comparisons would
        # depend on where the matching key falls in the iteration; hmac.compare_digest
        # itself already runs in time proportional to the input length regardless of
        # where a mismatching byte appears, so walking the whole key set preserves
        # that property per key while still accepting on a match. Mirrors
        # juniper-data's reference implementation (juniper_data/api/security.py).
        matched = False
        for candidate in self._api_keys:
            if hmac.compare_digest(api_key, candidate):
                matched = True
        return matched
"""

# The markers tests/test_service_fork_drift.py asserts. Kept here so the script and the guard
# cannot drift apart silently.
GUARD_MARKERS = ("matched = False", "return matched")


def port(path: Path, *, dry_run: bool) -> int:
    """Rewrite ``path``'s validate() to the non-short-circuiting form.

    Returns 0 on success or already-ported, 2 when the file does not carry the expected text.
    """
    if not path.is_file():
        print(f"REFUSED  {path}: not a file")
        return 2

    source = path.read_text(encoding="utf-8")

    if all(marker in source for marker in GUARD_MARKERS) and OLD not in source:
        print(f"ALREADY-PORTED  {path}")
        return 0

    if OLD not in source:
        print(f"REFUSED  {path}: validate() does not match the expected text verbatim.")
        print("         Refusing to pattern-patch security code on a guess. Inspect by hand.")
        return 2

    if source.count(OLD) != 1:
        print(f"REFUSED  {path}: expected text appears {source.count(OLD)} times, wanted exactly 1")
        return 2

    updated = source.replace(OLD, NEW)

    if dry_run:
        print(f"WOULD-PORT  {path}")
        return 0

    path.write_text(updated, encoding="utf-8")
    print(f"PORTED  {path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+", type=Path, help="security.py files to port (absolute paths)")
    parser.add_argument("--dry-run", action="store_true", help="resolve and report without writing")
    args = parser.parse_args()

    worst = 0
    for path in args.paths:
        worst = max(worst, port(path, dry_run=args.dry_run))
    return worst


if __name__ == "__main__":
    sys.exit(main())
