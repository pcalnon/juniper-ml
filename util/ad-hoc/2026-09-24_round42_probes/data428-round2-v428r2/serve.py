"""Launch the PR-head app on a local port for a live event-loop probe (validator scratch)."""

import sys

ROOT = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v428r2/pr"
sys.path.insert(0, ROOT)

import uvicorn  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402

port = int(sys.argv[1])
storage = sys.argv[2]
settings = Settings(storage_path=storage, api_keys=["probe-key"], rate_limit_enabled=False, metrics_enabled=False)
app = create_app(settings=settings)
uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
