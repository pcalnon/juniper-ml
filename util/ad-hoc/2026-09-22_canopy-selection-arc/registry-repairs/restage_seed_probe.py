"""Finding probe (out of scope to fix): does the restart modal's re-stage carry the registry seed that Apply carries?

Read-only: builds both payloads with requests.post mocked and prints them. Run from canopy src/. Scratch only.
"""

import os
import sys
from unittest import mock
from unittest.mock import MagicMock

# JuniperCanopy1 carries an editable install of the MAIN canopy checkout; pin the worktree first.
sys.path.insert(0, "/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--registry-record-repairs--20260922-2021--26e0546f/src")
os.environ.setdefault("JUNIPER_CANOPY_DEMO_MODE", "1")

import frontend.dashboard_manager as dm_module  # noqa: E402
from frontend.dashboard_manager import DashboardManager  # noqa: E402

print("dashboard_manager imported from:", dm_module.__file__)


def payload(call):
    with mock.patch("frontend.dashboard_manager.requests.post") as post:
        post.return_value = MagicMock(ok=True, status_code=200, text="{}")
        post.return_value.json.return_value = {}
        call(DashboardManager({}))
    return post.call_args.kwargs["json"]


for value in ("equities", "mnist"):
    apply_sent = payload(lambda dm, v=value: dm._apply_dataset_handler(1, v, 100, 0.1, 2.0, 2))
    restage_sent = payload(lambda dm, v=value: dm._restage_dataset({"dataset_type": v, "n_samples": 100, "noise": 0.1}))
    print(f"{value}: Apply        -> {apply_sent}")
    print(f"{value}: restart modal -> {restage_sent}")
