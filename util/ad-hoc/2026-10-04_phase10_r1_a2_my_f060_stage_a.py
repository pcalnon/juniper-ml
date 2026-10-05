# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10A2.g5NzBN/my_f060_stage_a.py
# Written by Lane 10-A2 (evidence and instruments), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 10-A2 independent F-CANOPY-060 reproduction, stage A (cascor env).

juniper-data 29be6d35 limits.InputTooLargeError / IncompleteDataError (real classes)
  -> juniper-data's route: HTTPException(422, detail=str(e))  (datasets.py:279-305) -- emulated as a 422 JSON body
  -> juniper-data-client origin/main JuniperDataClient._request (REAL, with session.request mocked to that response)
  -> cascor 95cdc562 TrainingLifecycleManager._describe_dataset_fetch_failure (REAL, imported from the module)
  -> cascor's start route wrapping: HTTPException(409, detail=f"Training cannot be started: {e}")
Writes the strings canopy would receive to a JSON file for stage B.

Usage: python my_f060_stage_a.py <scratch root> <out.json>
"""
import importlib.util
import json
import sys
from unittest import mock

ROOT, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, f"{ROOT}/dclient")  # data-client at origin/main, ahead of any installed copy
sys.path.insert(1, f"{ROOT}/cascor/src")
for k in [k for k in sys.modules if k.startswith("juniper_data_client")]:
    del sys.modules[k]

spec = importlib.util.spec_from_file_location("jd_limits_pin", f"{ROOT}/data/juniper_data/core/limits.py")
limits = importlib.util.module_from_spec(spec)
spec.loader.exec_module(limits)

import juniper_data_client  # noqa: E402
from juniper_data_client.client import JuniperDataClient  # noqa: E402
from juniper_data_client.exceptions import JuniperDataValidationError  # noqa: E402

print("data-client imported from:", juniper_data_client.__file__.replace(ROOT, "<scratch>"))

from api.lifecycle.manager import TrainingLifecycleManager  # noqa: E402

import api.lifecycle.manager as mgr  # noqa: E402

print("cascor manager imported from:", mgr.__file__.replace(ROOT, "<scratch>"))


class FakeResponse:
    def __init__(self, status, body):
        self.status_code = status
        self._body = body
        self.ok = 200 <= status < 300
        self.text = json.dumps(body)

    def json(self):
        return self._body


cases = {
    "cap_equities_503_over_14": limits.InputTooLargeError(source="The requested universe", unit=limits.UNIT_SYMBOLS, cap=14, actual=503, opt_in_env="JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION"),
    "cap_equities_40_over_7": limits.InputTooLargeError(source="The requested universe", unit=limits.UNIT_SYMBOLS, cap=7, actual=40, opt_in_env="JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION"),
    "cap_csv_bytes": limits.InputTooLargeError(source="Source 'big.csv'", unit=limits.UNIT_BYTES, cap=128 * 1024 * 1024, actual=300 * 1024 * 1024, opt_in_env="JUNIPER_DATA_CSV_IMPORT_ALLOW_TRUNCATION"),
    "incomplete_control": limits.IncompleteDataError(detail="2 symbols had no usable SEC share history.", unrescued=["XYZ", "QQQQ"], rows_affected=777, opt_in_env="JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION"),
}
out = {}
client = JuniperDataClient(base_url="http://127.0.0.1:9")
for name, data_exc in cases.items():
    with mock.patch.object(client.session, "request", return_value=FakeResponse(422, {"detail": str(data_exc)})):
        try:
            client._request("POST", "/v1/datasets", json={"generator": "equities"})
            raise SystemExit("no error raised")
        except JuniperDataValidationError as real_exc:
            client_exc = real_exc
    stances = {}
    for stance, kw in {
        "flag_off_silent_caller": {},
        "caller_refused": {"caller_refused": True},
        "flag_on_no_opt_in": {"deployment_flag_on": True},
        "caller_deferred": {"opt_in_skipped": mgr._OPT_IN_SKIPPED_CALLER_DEFERRED},
        "list_unreadable_staged": {"opt_in_skipped": mgr._OPT_IN_SKIPPED_LIST_UNREADABLE, "deployment_flag_on": True, "fetch_path": mgr._FETCH_PATH_STAGED_START},
    }.items():
        msg = TrainingLifecycleManager._describe_dataset_fetch_failure(client_exc, allow_truncated=False, **kw)
        stances[stance] = f"Training cannot be started: {RuntimeError(msg)}"
    out[name] = {"data_detail": str(data_exc), "client_str": str(client_exc), "client_type": type(client_exc).__name__, "client_status": client_exc.status_code, "canopy_receives": stances}
    print(f"{name}: client {type(client_exc).__name__}({client_exc.status_code}) str starts {str(client_exc)[:40]!r}; token in message: {all(mgr._PROJECT_API_SHORTFALL_REFUSAL_TOKEN in s for s in stances.values())}")
json.dump(out, open(OUT, "w"), indent=1)
print("wrote", OUT.replace(ROOT, "<scratch>"))
