#!/usr/bin/env python3
"""
Round-6 corrections for the flood-4 juniper-ml docs carrier: juniper-canopy's own APIKeyAuth joins every list of the copies, and the Sentry passage drops its variable names.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 docs carrier, validator round 6)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-07_flood4_ml_docs_fixes_round5.py (the layer this one follows);
         util/ad-hoc/2026-11-07_flood4_ml_docs_wheel_probe.py (now also reads every juniper-canopy wheel)

Facts, read in the published wheels on 2026-11-07 (tmp/flood4/ml-docs/docs/wheel_probe.log):

- juniper-canopy 0.3.0-0.8.0 wheels define no APIKeyAuth. 0.8.1 (2026-09-18) does, in security.py (validate at
  :61, `return any(hmac.compare_digest(api_key, k) for k in self._api_keys)` at :74, a str compare), and
  middleware.py:16 imports it. 0.9.0 (2026-10-17) is the first byte compare: `_compare_bytes` returns
  `text.encode("utf-8", "surrogatepass")` (:42-52), and validate compares `_compare_bytes(api_key)` with
  `_compare_bytes(candidate)` (:134-137). The repo path is src/security.py.
- No other published Juniper package defines APIKeyAuth or calls hmac.compare_digest in any release (every wheel of
  juniper-recurrence, -recurrence-model, -recurrence-client, -cascor-worker, -cascor-client, -data-client,
  -model-core, -cascor-protocol, -cascor-model, -ci-tools, -config-tools, -doc-tools and juniper-ml), so
  service-core plus the data, cascor and canopy copies is every published copy.

Usage: 2026-11-07_flood4_ml_docs_fixes_round6.py <out.json>
"""

from __future__ import annotations

import json
import sys

REF = "docs/REFERENCE.md"
CANOPY = "juniper-canopy 0.8.1 security.py:74 str compare (k); 0.9.0 :52 encode('utf-8', 'surrogatepass') in _compare_bytes, :134-137 bytes; 0.3.0-0.8.0 define no APIKeyAuth (wheel_probe.log)"


def _fx(pr: int, path: str, old: str, new: str, why: str) -> dict:
    return {"pr": pr, "path": path, "old": old, "new": new, "why": why}


FIXES = [
    _fx(0, REF, "the local holding the **configured** key (`k` or `candidate`, depending on the copy) is not.", "the local holding the **configured** key is not.", "round-6 F2: the names came before any copy is introduced and did not say which copy uses which; dropped"),
    _fx(0, REF, "juniper-data and juniper-cascor carry their own `APIKeyAuth` (`juniper_data/api/security.py`; juniper-cascor's `src/api/security.py`). The byte compare is first released in juniper-data **0.17.0** (juniper-data#440) and juniper-cascor **0.12.0**.", "juniper-data, juniper-cascor and juniper-canopy carry their own `APIKeyAuth` (`juniper_data/api/security.py`; juniper-cascor's `src/api/security.py`; juniper-canopy's `src/security.py`). The byte compare is first released in juniper-data **0.17.0** (juniper-data#440), juniper-cascor **0.12.0** and juniper-canopy **0.9.0**.", f"round-6 F1: {CANOPY}"),
    _fx(0, "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md", "The byte compare (`surrogatepass`) is first released in service-core 0.7.1, juniper-data 0.17.0 and juniper-cascor 0.12.0, each in its own copy.", "The byte compare (`surrogatepass`) is first released in service-core 0.7.1; juniper-data, juniper-cascor and juniper-canopy carry their own copies, first comparing bytes in 0.17.0, 0.12.0 and 0.9.0.", f"round-6 F1: {CANOPY}; the completeness wording 'each in its own copy' dropped"),
    _fx(0, "docs/QUICK_START.md", "juniper-data's and juniper-cascor's own copies compare bytes from 0.17.0 and 0.12.0", "juniper-data's, juniper-cascor's and juniper-canopy's own copies compare bytes from 0.17.0, 0.12.0 and 0.9.0", f"round-6 F1: {CANOPY}"),
    _fx(0, "CHANGELOG.md", "  fixes (`juniper-service-core` 0.7.1 and `juniper-observability` 0.4.1; juniper-data 0.17.0 and juniper-cascor\n  0.12.0 for their own key compare); `accuracy` (juniper-cascor#731) first ships in juniper-cascor 0.13.0; the\n  CR-024 413 for an under-declared `Content-Length` holds only at the ASGI layer; and juniper-data's HTTP body\n  limit and the worker binary-frame cap are 10 MiB and 100 MiB.\n", "  fixes (`juniper-service-core` 0.7.1 and `juniper-observability` 0.4.1; juniper-data 0.17.0, juniper-cascor\n  0.12.0 and juniper-canopy 0.9.0 for their own key compare); `accuracy` (juniper-cascor#731) first ships in\n  juniper-cascor 0.13.0; the CR-024 413 for an under-declared `Content-Length` holds only at the ASGI layer; and\n  juniper-data's HTTP body limit and the worker binary-frame cap are 10 MiB and 100 MiB.\n", f"round-6 F1, this carrier's CHANGELOG entry: {CANOPY}"),
]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    with open(argv[1], "w", encoding="utf-8") as fh:
        json.dump(FIXES, fh, indent=2)
    print(f"{len(FIXES)} round-6 fixes written to {argv[1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
