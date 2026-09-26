"""Is a caller-sent ``allow_truncation: null`` reachable through the stage / live-swap routes? (scratch)"""

import os
import sys

sys.path.insert(0, os.path.join(sys.argv[1], "src"))

from api.models.training import StageDatasetRequest, SwapDatasetLiveRequest  # noqa: E402

b = StageDatasetRequest.model_validate({"dataset_type": "equities", "params": {"allow_truncation": None, "tickers": ["AAPL"]}})
print("stage dump:", b.model_dump(exclude_none=True))
s = SwapDatasetLiveRequest.model_validate({"dataset_type": "equities", "params": {"allow_truncation": None}})
print("swap dump:", s.model_dump(exclude_none=True))
