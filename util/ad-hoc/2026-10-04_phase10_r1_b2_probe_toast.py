# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10B2.eZmWfY/probe_toast.py
# Written by Lane 10-B2 (adversarial, claims beyond evidence), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, modified 2026-10-05 only to close the files it opens
# (CodeQL py/file-not-always-closed on juniper-ml#2157); what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase10_r1_probes_close_files.py.
# ---------------------------------------------------------------------------
"""Lane 10-B2 probe: what does canopy's apply toast say for the A-N2 answer, and for the answer a
partition-aware extractor would have produced? Executes DashboardManager._compose_apply_toast at 1b2dd438
on the ARCHIVED /api/set_params response body (02_gaussian/03_set_params_caps.json)."""

from __future__ import annotations

import copy
import json
import os
import sys

SCRATCH = os.path.dirname(os.path.abspath(__file__))
CANOPY_SRC, ARCHIVE = sys.argv[1], sys.argv[2]
os.chdir(SCRATCH)
sys.path.insert(0, CANOPY_SRC)
from frontend.dashboard_manager import DashboardManager  # noqa: E402

with open(ARCHIVE) as fh:
    rec = json.load(fh)
params = rec["request_body"]
sent = {k: v for k, v in params.items() if k != "nn_model"}


class Resp:
    def __init__(self, body):
        self._b = body

    def json(self):
        return self._b


archived = rec["response"]
print("archived answer keys      :", sorted(archived))
print("toast on the archived body:", repr(DashboardManager._compose_apply_toast(Resp(archived), sent, [])))
# What the response would carry had the extractor also read the WS ack's data.result (the o3 mutation arm's partition):
full = copy.deepcopy(archived)
full["applied"] = ["nn_max_iterations", "nn_max_hidden_units", "nn_output_epochs", "cn_training_iterations"]
full["skipped_detail"] = [{"key": "nn_max_total_epochs", "reason": "not-updatable"}]
print("toast with the WS partition:", repr(DashboardManager._compose_apply_toast(Resp(full), sent, [])))
# And with the WS keys lost but a REST-leg skip present: the count comes from `applied`.
rest_skip = copy.deepcopy(archived)
rest_skip["skipped_detail"] = [{"key": "cn_training_iterations", "reason": "null-value"}]
print("toast, REST skip, WS lost  :", repr(DashboardManager._compose_apply_toast(Resp(rest_skip), sent, [])))
