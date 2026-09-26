"""cascor#688 item 4 against the REAL juniper-data main app (scratch server on :18765).

For each staged request, with the flag off and on: does the start's failure carry the
[dataset_shortfall_refused] token, and what status did juniper-data answer?
usage: probe_realjd_refusals.py <cascor-tree> <jd-url>
"""

from __future__ import annotations

import logging
import os
import sys
from unittest.mock import patch

ROOT, URL = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(ROOT, "src"))
logging.basicConfig(level=logging.CRITICAL)
for _n in ("", "api", "cascor", "juniper_cascor"):
    logging.getLogger(_n).setLevel(logging.CRITICAL)

import api.lifecycle.manager as M  # noqa: E402

os.environ["JUNIPER_DATA_URL"] = URL
CASES = [
    ("spiral n_spirals=1 (param error)", "spiral", {"n_spirals": 1}),
    ("equities incomplete_rows='keep' (param error naming the field)", "equities", {"symbols": ["AAPL", "MSFT"], "incomplete_rows": "keep"}),
    ("equities incomplete_rows='Drop' (case typo)", "equities", {"symbols": ["AAPL", "MSFT"], "incomplete_rows": "Drop"}),
    ("csv_import max_bytes=-1 (param error naming neither)", "csv_import", {"file_path": "big.csv", "max_bytes": -1}),
    ("csv_import over cap, caller silent (REAL refusal)", "csv_import", {"file_path": "big.csv", "max_bytes": 40}),
    ("csv_import over cap, allow_truncation=null (REAL refusal)", "csv_import", {"file_path": "big.csv", "max_bytes": 40, "allow_truncation": None}),
    ("csv_import over cap, allow_truncation=false (REAL refusal)", "csv_import", {"file_path": "big.csv", "max_bytes": 40, "allow_truncation": False}),
    ("equities 3 symbols over max_symbols=2 (REAL refusal)", "equities", {"symbols": ["AAPL", "MSFT", "NVDA"], "max_symbols": 2}),
]
for flag in ("false", "true"):
    os.environ["JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS"] = flag
    M._TRUNCATABLE_GENERATORS.reset()
    print(f"\n=== flag={flag}")
    for label, gen, params in CASES:
        m = M.TrainingLifecycleManager()
        try:
            m.stage_dataset_config(dataset_type=gen, params=dict(params))
            with patch.object(m, "_run_training"):
                try:
                    m.start_training()
                    out = "STARTED"
                    sf = m.get_status()["dataset_shortfall"]
                    out += f" shortfall={None if sf is None else sf.get('summary')}"
                except Exception as exc:  # noqa: BLE001
                    out = str(exc)
            token = out.startswith("[dataset_shortfall_refused]")
            status = "400" if "(400)" in out else "422" if "(422)" in out else "-"
            names_knob = "JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS" in out
            print(f"  {label:62s} jd={status} token={token!s:5s} names_flag={names_knob!s:5s} | {out[:150]}")
        finally:
            m.shutdown()
