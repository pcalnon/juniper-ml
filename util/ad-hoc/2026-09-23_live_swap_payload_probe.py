"""
Compare the payload canopy's live dataset swap POSTs with the one Apply Dataset POSTs, for the same form state.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy#668 (the restart modal dropped the registry seed); juniper-canopy#669 (the
         nn_model mirror, whose stated limitation is the live-swap and restart paths)

Read-only: builds a DashboardManager, mocks ``requests.post``, calls the two REAL handlers
(``_apply_dataset_handler`` and ``_accept_live_switch_handler``) with identical form values, and prints
the JSON each would have sent. #668 found the restart modal re-staged a seeded generator without its
seed; this asks whether the live swap -- the third path that stages a dataset -- does the same.

Usage (canopy env, canopy ``src/`` as cwd):
    LIBTORCH= LD_LIBRARY_PATH= /opt/miniforge3/envs/JuniperCanopy1/bin/python \\
        <juniper-ml>/util/ad-hoc/2026-09-23_live_swap_payload_probe.py
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

# JuniperCanopy1 carries an editable install of the PRIMARY canopy checkout, so pin the tree under test
# first, and print which file was imported -- a probe of the wrong tree answers the wrong question.
sys.path.insert(0, os.getcwd())
os.environ.setdefault("JUNIPER_CANOPY_DEMO_MODE", "1")

import frontend.dashboard_manager as dm_module  # noqa: E402
from frontend.dashboard_manager import DashboardManager  # noqa: E402

print("dashboard_manager imported from:", dm_module.__file__)


def _capture(call):
    sent = []

    def fake_post(url, json=None, **_kwargs):  # noqa: A002 -- mirrors requests.post's keyword
        sent.append({"url": url.rsplit("/api/", 1)[-1], "json": json})
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"data": {"status": "swapped"}}
        resp.text = ""
        return resp

    with patch("frontend.dashboard_manager.requests.post", side_effect=fake_post):
        call()
    return sent


def main() -> int:
    manager = DashboardManager({})
    # The sidebar's typed spiral inputs keep their mount values whichever dataset is picked.
    typed = {"n_samples": 200, "noise": 0.1, "rotations": 1.5, "n_spirals": 2}
    for dataset in ("spiral", "equities", "mnist", "moon"):
        apply_sent = _capture(lambda d=dataset: manager._apply_dataset_handler(1, d, typed["n_samples"], typed["noise"], typed["rotations"], typed["n_spirals"], gen_values=[], gen_ids=[]))
        swap_sent = _capture(lambda d=dataset: manager._accept_live_switch_handler(n_clicks=1, dataset_type=d, n_samples=typed["n_samples"], noise=typed["noise"], n_spirals=typed["n_spirals"], rotations=typed["rotations"]))
        print(f"== {dataset}")
        print("   apply:", json.dumps(apply_sent[0]["json"] if apply_sent else None, sort_keys=True))
        print("   swap: ", json.dumps(swap_sent[0]["json"] if swap_sent else None, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
