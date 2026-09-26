#!/usr/bin/env python
"""Ask a REAL juniper-data server how it answers each failure class cascor's refusal describer must tell apart.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor#688's validation, finding 1 (a 400 that NAMES a truncation field was read as a
         shortfall refusal); the fix-forward's tests quote the texts this prints, so they are
         juniper-data's own words rather than a stand-in.

usage: 2026-09-24_cascor688_realjd_error_texts.py <juniper-data-url> [--describe <cascor-tree>]

Drives juniper-data-client (whatever the running interpreter imports) against <juniper-data-url> --
a scratch server of juniper-data main with an import directory holding ``big.csv`` (a small CSV
with a ``label`` column; ``max_bytes=40`` puts it over the cap). For every case it prints the
exception type, its ``status_code`` and ``str(exc)`` verbatim (repr, so newlines survive).

``--describe <cascor-tree>`` also imports that tree's ``api.lifecycle.manager`` and feeds each real
exception to ``TrainingLifecycleManager._describe_dataset_fetch_failure`` with the flag off and the
caller silent -- the position in which a misread 400 names the flag -- and prints whether the
result carries the refusal token. Nothing is written anywhere; the server is not started or
stopped by this script.
"""

from __future__ import annotations

import os
import sys
from typing import Any, List, Tuple

CASES: List[Tuple[str, str, Any, str]] = [
    # (label, generator, params, what juniper-data should answer)
    ("spiral n_spirals=1", "spiral", {"n_spirals": 1}, "400 parameter error"),
    ("equities incomplete_rows='keep'", "equities", {"symbols": ["AAPL", "MSFT"], "incomplete_rows": "keep"}, "400 naming incomplete_rows"),
    ("csv_import allow_truncation=''", "csv_import", {"file_path": "big.csv", "allow_truncation": ""}, "400 naming allow_truncation"),
    ("csv_import allow_truncation='  '", "csv_import", {"file_path": "big.csv", "allow_truncation": "  "}, "400 naming allow_truncation"),
    ("equities incomplete_rows quoting the remedy", "equities", {"symbols": ["AAPL"], "incomplete_rows": "Re-submit with allow_truncation=true"}, "400 whose text carries the remedy sentence"),
    ("spiral params not a mapping", "spiral", "not-a-mapping", "422 request-schema error"),
    ("csv_import over cap, caller silent", "csv_import", {"file_path": "big.csv", "max_bytes": 40}, "422 InputTooLargeError"),
    ("csv_import over cap, allow_truncation=null", "csv_import", {"file_path": "big.csv", "max_bytes": 40, "allow_truncation": None}, "422 InputTooLargeError"),
    ("csv_import over cap, allow_truncation=false", "csv_import", {"file_path": "big.csv", "max_bytes": 40, "allow_truncation": False}, "422 InputTooLargeError"),
    ("equities 3 symbols over max_symbols=2", "equities", {"symbols": ["AAPL", "MSFT", "NVDA"], "max_symbols": 2}, "422 InputTooLargeError"),
]


def main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    url = argv[0]
    describe = None
    if "--describe" in argv:
        tree = argv[argv.index("--describe") + 1]
        sys.path.insert(0, os.path.join(tree, "src"))
        from api.lifecycle.manager import TrainingLifecycleManager  # noqa: E402 - the tree is chosen at run time

        describe = TrainingLifecycleManager._describe_dataset_fetch_failure

    from juniper_data_client import JuniperDataClient

    client = JuniperDataClient(base_url=url, retries=0, timeout=120)
    for label, generator, params, expected in CASES:
        print(f"### {label}  (expected: {expected})")
        try:
            result = client.create_dataset(generator=generator, params=params, persist=False)
        except Exception as exc:  # noqa: BLE001 - every failure class is the subject here
            print(f"    {type(exc).__name__} status_code={getattr(exc, 'status_code', 'n/a')}")
            print(f"    {str(exc)!r}")
            if describe is not None:
                message = describe(exc, allow_truncated=False)
                print(f"    describer (flag off, caller silent): token={message.startswith('[dataset_shortfall_refused]')} | {message[:110]!r}")
            continue
        print(f"    delivered: dataset_id={result.get('dataset_id')} meta={result.get('meta')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
