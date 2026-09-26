"""Lane B (r42d): serve an extracted juniper-data tree on a given port and storage dir.

Usage: run_in_tree.bash <tree> serve.py <tree> <port> <storage>
Secrets are stubbed (no key file is read), the .env file is not read, rate limiting is off.
"""

import os
import sys

tree, port, storage = sys.argv[1], int(sys.argv[2]), sys.argv[3]

import juniper_data  # noqa: E402

assert os.path.realpath(juniper_data.__file__).startswith(os.path.realpath(tree) + os.sep), juniper_data.__file__

import juniper_data.api.settings as settings_module  # noqa: E402

settings_module.get_secret = lambda _name: None  # never read a secret file

import uvicorn  # noqa: E402

from juniper_data.api.app import create_app  # noqa: E402
from juniper_data.api.settings import Settings  # noqa: E402

settings = Settings(storage_path=storage, rate_limit_enabled=False, api_keys=None, _env_file=None)
app = create_app(settings=settings)
uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
