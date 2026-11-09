#!/usr/bin/env python3
"""
Round-3 corrections for the flood-4 juniper-ml docs carrier, applied as a fix-only layer on the rebased tree (bbdeb758).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 docs carrier, validator round 3)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-07_flood4_ml_docs_fixes.py (rounds 1-2, applied on 303ccc0b before the rebase);
         util/ad-hoc/2026-11-07_flood4_ml_docs_rebase_merge.py (the rebase onto bbdeb758)

These come after the rebase, so they live here rather than in the round-1/2 list: run the applier with no draft
numbers and this file's JSON as --fixes, on the rebased tree. pr 0 marks a correction of main's own wording.

Usage: 2026-11-07_flood4_ml_docs_fixes_round3.py <out.json>
"""

from __future__ import annotations

import json
import sys

REF = "docs/REFERENCE.md"
QS = "docs/QUICK_START.md"


def _fx(pr: int, path: str, old: str, new: str, why: str) -> dict:
    return {"pr": pr, "path": path, "old": old, "new": new, "why": why}


FIXES = [
    _fx(2442, REF, '`get_worker_stats(worker_id)["total_results"]` is that retained length, not a lifetime count.', '`get_worker_stats(worker_id)["total_results"]` is that retained length (a lifetime count only when the window is 0).', "round-3 F1: security.py:239-240 keeps everything at window 0; :263 total_results = len(history)"),
    _fx(0, REF, "**Published wheels do not have this yet** (PyPI, checked 2026-10-08). `juniper-service-core` is still **0.7.0** and `juniper-observability` is still **0.4.0**; both notes live under `[Unreleased]` (juniper-ml#2086). A service installed from those wheels still 500s on a non-ASCII key, still fails to throttle that flood, and can still send the configured key to Sentry. The fix is on `main` only.", "**Fixed in the published wheels** (PyPI, re-checked 2026-11-07): `juniper-service-core` **0.7.1** (2026-10-10) compares keys as bytes, and `juniper-observability` **0.4.1** (2026-10-10) passes `include_local_variables=False`. A service still on service-core **0.7.0** or observability **0.4.0** still 500s on a non-ASCII key, still fails to throttle that flood, and can still send the configured key to Sentry: upgrade both.", "round-3 F2, a fix to main's text: 0.7.1 wheel security.py:88-91 compares UTF-8 bytes; 0.4.1 wheel sentry.py:134 include_local_variables=False"),
    _fx(0, QS, "a 401 (WebSocket close 4001) on `main`; published service-core 0.7.0 still 500s, and that 500 can send the configured key to Sentry in a frame local", "a 401 (WebSocket close 4001) from service-core 0.7.1; 0.7.0 still 500s, and under observability 0.4.0 that 500 can send the configured key to Sentry in a frame local (0.4.1 drops frame locals)", "round-3 F2, a fix to main's text: same wheels"),
    _fx(0, REF, "so an under-declared `Content-Length` or a chunked body with none still hits 413.", "so an under-declared `Content-Length` (at the ASGI layer; under uvicorn the parser truncates the body to the declared length first) or a chunked body with none still hits 413.", "round-3 F3, a fix to main's text: the second CR-024 copy of round-2 F2"),
    _fx(0, REF, "binary attachments over 100 MB get `Binary frame too large`.", "binary attachments over 100 MiB get `Binary frame too large` (on stock uvicorn a frame over 16 MiB is closed 1009 first).", "round-3 F4, a fix to main's text: worker_stream.py:72 is 100 * 1024 * 1024; uvicorn ws_max_size 16 MiB"),
    _fx(2446, REF, "(logged at INFO) is 4003", "(visible only with an INFO handler) is 4003", "round-3 F5: the caveat the other two rows carry; control_security.py:44,49 are logger.info"),
    _fx(0, "CHANGELOG.md", "#2424 makes #2426's claim and is carried once, in\n  #2426's wording.", "#2424 makes #2426's claim; only #2426's\n  wording is carried.", "round-3 F7: #2424 itself is listed as not carried"),
]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    with open(argv[1], "w", encoding="utf-8") as fh:
        json.dump(FIXES, fh, indent=2)
    print(f"{len(FIXES)} round-3 fixes written to {argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
