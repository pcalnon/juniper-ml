"""An ordinary param-validation 422 on a NON-truncatable generator: how is it described? (scratch)"""

from __future__ import annotations

import logging
import os
import sys
from unittest.mock import patch

ROOT = sys.argv[1]
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(__file__))
logging.basicConfig(level=logging.CRITICAL)

from fakejd import FakeJD  # noqa: E402

import api.lifecycle.manager as M  # noqa: E402

for flag in ("true", "false"):
    fake = FakeJD()
    fake.create_mode = "422_validation"
    os.environ["JUNIPER_DATA_URL"] = fake.url
    os.environ["JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS"] = flag
    M._TRUNCATABLE_GENERATORS.reset()
    m = M.TrainingLifecycleManager()
    try:
        m.stage_dataset_config(dataset_type="spirals", params={"n_spirals": 1})
        with patch.object(m, "_run_training"):
            try:
                m.start_training()
                out = "started"
            except Exception as exc:  # noqa: BLE001
                out = str(exc)
        print(f"flag={flag}: token={out.startswith('[dataset_shortfall_refused]')}")
        print("   ", out[:170])
        print("   ...", out[-330:])
    finally:
        m.shutdown()
        fake.close()
