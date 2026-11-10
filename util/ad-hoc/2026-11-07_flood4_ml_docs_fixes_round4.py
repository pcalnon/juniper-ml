#!/usr/bin/env python3
"""
Round-4 corrections for the flood-4 juniper-ml docs carrier, applied as a fix-only layer on the rebased tree (bbdeb758).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 docs carrier, validator round 4)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-07_flood4_ml_docs_fixes.py (rounds 1-2, applied on 303ccc0b before the rebase);
         util/ad-hoc/2026-11-07_flood4_ml_docs_fixes_round3.py (round 3, the layer this one follows)

Same shape as the round-3 layer: run the applier with no draft numbers and this file's JSON as --fixes, on the tree
the round-3 layer produced. pr 0 marks a correction of main's own wording (or of this carrier's CHANGELOG entry);
a draft number marks a correction of a line that draft added. Evidence for each entry is in its `why`: the published
wheels were read from PyPI's JSON API on 2026-11-07 (upload dates are PyPI's), the merge dates from `gh pr view`.

Usage: 2026-11-07_flood4_ml_docs_fixes_round4.py <out.json>
"""

from __future__ import annotations

import json
import sys

REF = "docs/REFERENCE.md"
CHEAT = "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"

SC_WHEELS = "service-core 0.7.0 wheel security.py:66 any(hmac.compare_digest(api_key, k) ...); 0.7.1 wheel (PyPI 2026-10-10) security.py:88-91 compares UTF-8 bytes in a `for candidate` loop; #2086 merged 2026-09-24, after 0.7.0 (2026-08-31), and no release sits between 0.7.0 and 0.7.1"
OBS_WHEELS = "observability 0.4.0 wheel sentry.py:68-74 calls sentry_sdk.init without include_local_variables and its before_send only scrubs headers; 0.4.1 wheel (PyPI 2026-10-10) sentry.py:134 include_local_variables=False and :65 frame.pop('vars')"


def _fx(pr: int, path: str, old: str, new: str, why: str) -> dict:
    return {"pr": pr, "path": path, "old": old, "new": new, "why": why}


FIXES = [
    _fx(0, REF, "could ship the configured key. Published `juniper-service-core` 0.7.0 still has the `str` compare.", "could ship the configured key. `juniper-service-core` 0.7.0 still has the `str` compare; 0.7.1 is the first release with the bytes compare.", f"round-4 F1, a fix to main's text: {SC_WHEELS}"),
    _fx(0, REF, "and its `before_send` hook also deletes frame `vars`. Published **0.4.0** still uses the SDK default (`True`).", "and its `before_send` hook also deletes frame `vars`. Both are from **0.4.1**; **0.4.0** uses the SDK default (`True`), and its hook leaves frame `vars` in place.", f"round-4 F1, a fix to main's text: {OBS_WHEELS}"),
    _fx(0, REF, "`k` in published 0.7.0's generator expression, `candidate` in the loop that replaced it (juniper-ml#1974, unreleased) and in juniper-data's copy.", "`k` in 0.7.0's generator expression, `candidate` in the loop that replaced it (juniper-ml#1974, first released in 0.7.1) and in juniper-data's copy.", "round-4 F1, a fix to main's text: #1974 merged 2026-09-21; 0.7.0 wheel security.py:66 (`k`), 0.7.1 wheel :90 (`candidate`); juniper-data 0.16.0 api/security.py:100 and 0.17.0 :116 (`candidate`)"),
    _fx(0, REF, "A service still on service-core **0.7.0** or observability **0.4.0** still 500s on a non-ASCII key, still fails to throttle that flood, and can still send the configured key to Sentry: upgrade both.", "A service still on service-core **0.7.0** still 500s on a non-ASCII key and still fails to throttle that flood; if it is also on observability **0.4.0**, that 500 can send the configured key to Sentry. Upgrade both.", "round-4 F2 (round 3's rewrite of main's text): the 500 and the throttle miss follow service-core alone (0.7.1 security.py:88-91 encodes with surrogatepass, which cannot raise); the key reaches Sentry only when 0.4.0's frame locals ride on that 500 (0.4.1 sentry.py:134); the same statement as QUICK_START's link line"),
    _fx(0, REF, "after juniper-data 0.16.0 was published, so no juniper-data release carries it yet; juniper-data's", "after juniper-data 0.16.0 was published; juniper-data **0.17.0** (PyPI 2026-10-10) is the first release that carries it. juniper-data's", "round-4 F1 sweep, a fix to main's text: juniper-data#440 merged 2026-09-25T01:57Z, after 0.16.0 (2026-09-24T18:35Z); the 0.16.0 wheel's api/security.py:100-101 compares str, the 0.17.0 wheel's (2026-10-10) :114-117 UTF-8 bytes with surrogatepass; PyPI has no release between them"),
    _fx(0, REF, "| Published `juniper-service-core` 0.7.0 compares keys as `str`; `hmac.compare_digest` raises `TypeError`, which is not an `HTTPException`. Fixed on `main` (UTF-8 bytes, `surrogatepass`; juniper-ml#2086, unreleased). Do not catch the `TypeError`. |", "| `juniper-service-core` 0.7.0 compares keys as `str`; `hmac.compare_digest` raises `TypeError`, which is not an `HTTPException`. Fixed in 0.7.1 (UTF-8 bytes, `surrogatepass`; juniper-ml#2086): upgrade. Do not catch the `TypeError`. |", f"round-4 F1, a fix to main's text: {SC_WHEELS}"),
    _fx(0, REF, "`configure_sentry` on `main` passes `include_local_variables=False` with no switch to re-enable; published `juniper-observability` 0.4.0 still uses the SDK default. |", "`juniper-observability` 0.4.0 uses the SDK default; from 0.4.1 `configure_sentry` passes `include_local_variables=False`, with no switch to re-enable: upgrade. |", f"round-4 F1, a fix to main's text: {OBS_WHEELS}"),
    _fx(0, CHEAT, "never a 500 — on `main`. Published `juniper-service-core` **0.7.0** still compares keys as `str`", "never a 500, from `juniper-service-core` **0.7.1**. **0.7.0** still compares keys as `str`", f"round-4 F1, a fix to main's text: {SC_WHEELS}"),
    _fx(0, CHEAT, "Published `juniper-observability` **0.4.0** still captures locals.", "`juniper-observability` **0.4.0** still captures locals; **0.4.1** does not.", f"round-4 F1, a fix to main's text: {OBS_WHEELS}"),
    _fx(0, CHEAT, "| Published `juniper-service-core` 0.7.0: `hmac.compare_digest` raises on a non-ASCII `str`, which is not an `HTTPException`. `main` compares UTF-8 bytes (`surrogatepass`, juniper-ml#2086, unreleased).", "| `juniper-service-core` 0.7.0: `hmac.compare_digest` raises on a non-ASCII `str`, which is not an `HTTPException`. 0.7.1 compares UTF-8 bytes (`surrogatepass`, juniper-ml#2086): upgrade.", f"round-4 F1, a fix to main's text: {SC_WHEELS}"),
    _fx(
        2442,
        REF,
        'records after each append. The flag needs a window of 3 or more: with 1 or 2 it never fires, and 0 disables trimming (`history[-0:]` is the whole list), so every result the worker has sent is compared and `total_results` is then a lifetime count. `get_worker_stats(worker_id)["total_results"]` is that retained length (a lifetime count only when the window is 0).',
        'records after each append; a window of 0 disables trimming (`history[-0:]` is the whole list). The flag can fire only with a window of 0 or of at least 3: with 1 or 2 the history never holds the three scores the flag needs, and with 0 it compares every result recorded for the worker. `get_worker_stats(worker_id)["total_results"]` is the history\'s length: how many results it has recorded, capped at `duplicate_window` (no cap at 0).',
        "round-4 F3/F4: juniper_service_core/workers/security.py:239-240 trims only when len > window, and history[-0:] keeps everything; :242-247 need len >= 3 and one six-decimal string over history[-window:], so windows 1-2 never flag and window 0 compares all; :263 total_results = len(history) = min(results, window), uncapped at 0 (val-round4 anomaly_window.txt: w10/5 -> 5, w10/14 -> 10, w0/25 -> 25, w0 five identical -> flags on results 3-5)",
    ),
    _fx(2456, REF, "It is not the 100 MB worker binary-frame cap", "It is not the 100 MiB worker binary-frame cap", "round-4 F5: juniper_service_core/websocket/worker_stream.py:72 _MAX_BINARY_SIZE = 100 * 1024 * 1024"),
    _fx(0, "CHANGELOG.md", "had swallowed existing text were moved.\n", "had swallowed existing text were moved.\n  Also corrected in `main`'s own pages: the non-ASCII API-key and Sentry frame-locals fixes are released, in\n  `juniper-service-core` 0.7.1 and `juniper-observability` 0.4.1 (PyPI 2026-10-10), and juniper-data's copy in\n  juniper-data 0.17.0; the CR-024 413 for an under-declared `Content-Length` holds only at the ASGI layer; and the\n  worker binary-frame cap is 100 MiB.\n", "round-4 F1, this carrier's CHANGELOG entry: records the rounds-3/4 corrections of main's text (REFERENCE, cheatsheet, QUICK_START) for a reader of the entry"),
]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    with open(argv[1], "w", encoding="utf-8") as fh:
        json.dump(FIXES, fh, indent=2)
    print(f"{len(FIXES)} round-4 fixes written to {argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
