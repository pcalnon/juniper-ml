"""A blank-string allow_truncation (cascor reads it as 'deferring') against the REAL juniper-data main (scratch).

The CSV is WITHIN its cap, so nothing about the dataset is partial: any shortfall-refusal token is a misread.
usage: probe_realjd_blank.py <cascor-tree> <jd-url>
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
for flag in ("false", "true"):
    os.environ["JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS"] = flag
    M._TRUNCATABLE_GENERATORS.reset()
    for label, value in (("allow_truncation=''", ""), ("allow_truncation='  '", "  "), ("allow_truncation=null", None)):
        m = M.TrainingLifecycleManager()
        try:
            m.stage_dataset_config(dataset_type="csv_import", params={"file_path": "big.csv", "allow_truncation": value})
            with patch.object(m, "_run_training"):
                try:
                    m.start_training()
                    out = "STARTED (dataset delivered in full)"
                except Exception as exc:  # noqa: BLE001
                    out = str(exc)
            print(f"flag={flag} {label:24s} token={out.startswith('[dataset_shortfall_refused]')!s:5s} | {out!r}")
        finally:
            m.shutdown()
