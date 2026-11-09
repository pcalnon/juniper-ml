#!/usr/bin/env python3
"""
Round-5 corrections for the flood-4 juniper-ml docs carrier: the API-key / Sentry release lineage shrunk to first-release facts, plus MINORs F3-F7.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 docs carrier, validator round 5)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-07_flood4_ml_docs_fixes_round4.py (the layer this one follows);
         util/ad-hoc/2026-11-07_flood4_ml_docs_wheel_probe.py (the per-release facts, from every published wheel)

Orchestrator ruling for this round: wherever the seven files discuss which releases carry the non-ASCII key /
Sentry frame-locals fixes, state only, per package, the FIRST published release that carries the fix, as read in
the wheels, and no cross-package advice; delete a sentence that cannot be both short and true. The facts used
(tmp/flood4/ml-docs/docs/wheel_probe.log):

- juniper-service-core: 0.1.0-0.7.0 call hmac.compare_digest(api_key, k) on str; 0.7.1 is the first byte compare.
- juniper-observability: no release before 0.4.1 passes include_local_variables or pops frame "vars"; 0.4.1 does both.
- juniper-cascor (own APIKeyAuth, src/api/security.py): 0.5.0-0.11.0 compare_digest(api_key, k) on str; 0.12.0 is
  the first byte compare.
- juniper-data (own APIKeyAuth, juniper_data/api/security.py): 0.7.0-0.16.0 compare_digest(api_key, candidate) on
  str (0.4.2 and 0.6.0 call no compare_digest); 0.17.0 is the first byte compare.

Same shape as the earlier layers: run the applier with no draft numbers and this file's JSON as --fixes. pr 0 marks a
correction of main's own wording (or of this carrier's CHANGELOG entry); a draft number, a line that draft added.

Usage: 2026-11-07_flood4_ml_docs_fixes_round5.py <out.json>
"""

from __future__ import annotations

import json
import sys

REF = "docs/REFERENCE.md"
CHEAT = "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"
OVERVIEW = "docs/DOCUMENTATION_OVERVIEW.md"
QS = "docs/QUICK_START.md"
SC_README = "juniper-service-core/README.md"

PROBE = "wheel_probe.log"
SC = f"service-core 0.1.0-0.7.0 str compare (k), 0.7.1 first byte compare ({PROBE})"
OBS = f"observability: include_local_variables=False and pop('vars') first in 0.4.1, in no earlier release ({PROBE})"
DATA_CASCOR = f"juniper-data 0.17.0 and juniper-cascor 0.12.0 are each package's first byte compare; every earlier release with APIKeyAuth compares str or calls no compare_digest ({PROBE})"
RULING = "round-5 ruling: first-release facts only, no cross-package advice"


def _fx(pr: int, path: str, old: str, new: str, why: str) -> dict:
    return {"pr": pr, "path": path, "old": old, "new": new, "why": why}


FIXES = [
    _fx(0, REF, "could ship the configured key. `juniper-service-core` 0.7.0 still has the `str` compare; 0.7.1 is the first release with the bytes compare. Operator surface:", "could ship the configured key. The bytes compare is first released in 0.7.1. Operator surface:", f"{RULING}: {SC}"),
    _fx(0, REF, "Both are from **0.4.1**; **0.4.0** uses the SDK default (`True`), and its hook leaves frame `vars` in place.", "Both are first released in **0.4.1**.", f"{RULING}: {OBS}"),
    _fx(0, REF, "the local holding the **configured** key is not — `k` in 0.7.0's generator expression, `candidate` in the loop that replaced it (juniper-ml#1974, first released in 0.7.1) and in juniper-data's copy.", "the local holding the **configured** key (`k` or `candidate`, depending on the copy) is not.", f"round-5 F3 under the ruling: no published service-core sent `candidate` (0.7.1 ships the loop already comparing bytes); the str copies use k (service-core <=0.7.0, cascor <=0.11.0) or candidate (juniper-data 0.7.0-0.16.0) ({PROBE})"),
    _fx(0, REF, "**Fixed in the published wheels** (PyPI, re-checked 2026-11-07): `juniper-service-core` **0.7.1** (2026-10-10) compares keys as bytes, and `juniper-observability` **0.4.1** (2026-10-10) passes `include_local_variables=False`. A service still on service-core **0.7.0** still 500s on a non-ASCII key and still fails to throttle that flood; if it is also on observability **0.4.0**, that 500 can send the configured key to Sentry. Upgrade both. Do not catch", "**First releases with the fix** (read in the PyPI wheels, 2026-11-07): `juniper-service-core` **0.7.1** compares keys as bytes; `juniper-observability` **0.4.1** passes `include_local_variables=False` and deletes frame `vars`. Do not catch", f"round-5 F1/F4 under the ruling: the mixed-install sentence and 'Upgrade both' deleted (false for juniper-cascor <=0.11.0 and juniper-data <=0.16.0, which carry their own str compare); {SC}; {OBS}"),
    _fx(0, REF, "juniper-data carries its own `APIKeyAuth` (`juniper_data/api/security.py`). The same byte compare landed there in juniper-data#440 (merged 2026-09-25), after juniper-data 0.16.0 was published; juniper-data **0.17.0** (PyPI 2026-10-10) is the first release that carries it. juniper-data's `configure_sentry` is juniper-observability's.", "juniper-data and juniper-cascor carry their own `APIKeyAuth` (`juniper_data/api/security.py`; juniper-cascor's `src/api/security.py`). The byte compare is first released in juniper-data **0.17.0** (juniper-data#440) and juniper-cascor **0.12.0**.", f"round-5 F1 under the ruling: names cascor's copy; the cross-package configure_sentry sentence deleted; {DATA_CASCOR}"),
    _fx(0, REF, "| `juniper-service-core` 0.7.0 compares keys as `str`; `hmac.compare_digest` raises `TypeError`, which is not an `HTTPException`. Fixed in 0.7.1 (UTF-8 bytes, `surrogatepass`; juniper-ml#2086): upgrade. Do not catch the `TypeError`. |", "| Before `juniper-service-core` 0.7.1, `APIKeyAuth` compares keys as `str`, and `hmac.compare_digest` raises `TypeError`, which is not an `HTTPException`. 0.7.1 compares UTF-8 bytes (`surrogatepass`; juniper-ml#2086). Do not catch the `TypeError`. |", f"round-5 F4 under the ruling: {SC}"),
    _fx(0, REF, "`juniper-observability` 0.4.0 uses the SDK default; from 0.4.1 `configure_sentry` passes `include_local_variables=False`, with no switch to re-enable: upgrade. |", "From `juniper-observability` 0.4.1, `configure_sentry` passes `include_local_variables=False`, with no switch to re-enable. |", f"round-5 F4 under the ruling: {OBS}"),
    _fx(0, CHEAT, "Tip: a non-ASCII `X-API-Key` is a **401** on HTTP and close **4001** on a WebSocket, never a 500, from `juniper-service-core` **0.7.1**. **0.7.0** still compares keys as `str` (`hmac.compare_digest` raises `TypeError`, a 500 that `FailedAuthThrottle` never counts). Do not catch that error, and do not turn Sentry frame locals back on — the comparison frame's locals hold the configured key. `juniper-observability` **0.4.0** still captures locals; **0.4.1** does not.", "Tip: from `juniper-service-core` **0.7.1** a non-ASCII `X-API-Key` is a **401** on HTTP and close **4001** on a WebSocket, not a 500; earlier releases compare `str`, and `hmac.compare_digest` raises `TypeError`. Do not catch that error, and do not turn Sentry frame locals back on — the comparison frame's locals hold the configured key. `juniper-observability`'s `configure_sentry` sends no frame locals from **0.4.1**.", f"round-5 F4 under the ruling: {SC} (0.7.1 security.py:118-122 401, websocket/manager.py:72-73 close 4001); the throttle parenthetical deleted (service-core has no FailedAuthThrottle before 0.6.0); {OBS}"),
    _fx(0, CHEAT, "| `juniper-service-core` 0.7.0: `hmac.compare_digest` raises on a non-ASCII `str`, which is not an `HTTPException`. 0.7.1 compares UTF-8 bytes (`surrogatepass`, juniper-ml#2086): upgrade.", "| Before `juniper-service-core` 0.7.1, `hmac.compare_digest` raises on a non-ASCII `str`, which is not an `HTTPException`. The byte compare (`surrogatepass`) is first released in service-core 0.7.1, juniper-data 0.17.0 and juniper-cascor 0.12.0, each in its own copy.", f"round-5 F1/F4 under the ruling: {SC}; {DATA_CASCOR}"),
    _fx(0, OVERVIEW, "a non-ASCII `X-API-Key` is a 401 from 0.7.1 (0.7.0 still 500s), and Sentry does not capture frame locals:", "a non-ASCII `X-API-Key` is a 401 from service-core 0.7.1, and observability 0.4.1's `configure_sentry` sends no frame locals:", f"round-5 F2 under the ruling: the Sentry clause named no release; {SC}; {OBS}"),
    _fx(0, QS, "a non-ASCII `X-API-Key` is a 401 (WebSocket close 4001) from service-core 0.7.1; 0.7.0 still 500s, and under observability 0.4.0 that 500 can send the configured key to Sentry in a frame local (0.4.1 drops frame locals)", "a non-ASCII `X-API-Key` is a 401 (WebSocket close 4001) from service-core 0.7.1, and observability 0.4.1's `configure_sentry` sends no frame locals; juniper-data's and juniper-cascor's own copies compare bytes from 0.17.0 and 0.12.0", f"round-5 F4 under the ruling: the mixed-install clause deleted; {SC}; {OBS}; {DATA_CASCOR}"),
    _fx(0, SC_README, "Releases up to and including **0.7.0** compare `str` and still return a 500 on such a header; **0.7.1** is the first release with the bytes compare (juniper-ml#2086 made the change). Do not catch the `TypeError`. The Sentry half of the same incident — frame locals, including the one holding the configured key — is `juniper-observability`'s `configure_sentry`.", "**0.7.1** is the first release with the bytes compare (juniper-ml#2086). Do not catch the `TypeError`. The Sentry half of the same incident — frame locals, including the one holding the configured key — is `juniper-observability`'s `configure_sentry`, first fixed in 0.4.1.", f"{RULING}: {SC}; {OBS}"),
    _fx(0, "CHANGELOG.md", "  Also corrected in `main`'s own pages: the non-ASCII API-key and Sentry frame-locals fixes are released, in\n  `juniper-service-core` 0.7.1 and `juniper-observability` 0.4.1 (PyPI 2026-10-10), and juniper-data's copy in\n  juniper-data 0.17.0; the CR-024 413 for an under-declared `Content-Length` holds only at the ASGI layer; and the\n  worker binary-frame cap is 100 MiB.\n", "  Also corrected in `main`'s own pages: the first releases with the non-ASCII API-key and Sentry frame-locals\n  fixes (`juniper-service-core` 0.7.1 and `juniper-observability` 0.4.1; juniper-data 0.17.0 and juniper-cascor\n  0.12.0 for their own key compare); `accuracy` (juniper-cascor#731) first ships in juniper-cascor 0.13.0; the\n  CR-024 413 for an under-declared `Content-Length` holds only at the ASGI layer; and juniper-data's HTTP body\n  limit and the worker binary-frame cap are 10 MiB and 100 MiB.\n", "this carrier's CHANGELOG entry, kept in step with the round-5 corrections of main's text"),
    _fx(2442, REF, "- An older different score blocks the flag until it ages out.", "- An older different score blocks the flag until it ages out. At a window of 0 nothing ages out, so it blocks the flag until `clear_worker` drops the row.", "round-5 F5: juniper_service_core/workers/security.py:239-240 never trims at window 0 (history[-0:] is the whole list); clear_worker (:273) pops the row"),
    _fx(2442, REF, "The flag waits until that score ages out, and until at least three retained scores print the same |", "The flag waits until that score ages out (at a window of 0, until `clear_worker` drops the row), and until at least three retained scores print the same |", "round-5 F5: same code"),
    _fx(2422, REF, "Two class constants bound the map. Neither is a constructor argument.", "Two class constants bound the map. Neither is a constructor argument. This is 0.7.1's table: in 0.6.0 and 0.7.0 the map was a `defaultdict`, so `check()` inserted every unseen source IP and the table had no high-water mark.", f"round-5 F6: service-core 0.6.0/0.7.0 FailedAuthThrottle builds a defaultdict and check() reads self._failures[client_ip] (:428), which inserts; prune runs only from record_failure; 0.7.1 has neither, and its class is identical to main's ({PROBE}; wheel_probe_fat_0.7.0.log; fat_0.7.1_vs_main.diff empty)"),
    _fx(0, REF, "new in [juniper-cascor#731](https://github.com/pcalnon/juniper-cascor/pull/731), which is in no release on 2026-10-27 (PyPI's latest is 0.12.0).", "new in [juniper-cascor#731](https://github.com/pcalnon/juniper-cascor/pull/731), first released in juniper-cascor 0.13.0 (PyPI 2026-10-28).", "round-5 F7, a fix to main's text: #731 merged 2026-10-27T00:11Z (752a797f); gh compare: v0.12.0 is behind it, v0.13.0 ahead 5 / behind 0; PyPI 0.13.0 uploaded 2026-10-28T11:43Z"),
    _fx(0, REF, "This is **not** the 10 MB HTTP body limit.", "This is **not** the 10 MiB HTTP body limit.", f"round-5 F7, a fix to main's text: juniper_data/api/constants.py MAX_REQUEST_BODY_BYTES = 10 * 1024 * 1024 in every release that has it, 0.7.0-0.17.1 ({PROBE})"),
]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    with open(argv[1], "w", encoding="utf-8") as fh:
        json.dump(FIXES, fh, indent=2)
    print(f"{len(FIXES)} round-5 fixes written to {argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
