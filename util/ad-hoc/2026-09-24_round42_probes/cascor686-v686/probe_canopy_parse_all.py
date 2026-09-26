"""Every refusal branch of #686's describer through canopy origin/main's parser, verbatim (scratch).

canopy origin/main 5907713b src/frontend/dashboard_manager.py:8343-8365 is copied below unchanged.
"""

import os
import sys

sys.path.insert(0, os.path.join(sys.argv[1], "src"))

import api.lifecycle.manager as M  # noqa: E402

DATASET_SHORTFALL_REFUSAL_MARKER = "[dataset_shortfall_refused]"
DATASET_SHORTFALL_REFUSAL_SENTENCE = "could not produce the requested dataset in full"


def _is_dataset_shortfall_refusal(detail) -> bool:  # verbatim canopy 5907713b dashboard_manager.py:8344
    text = str(detail or "")
    return DATASET_SHORTFALL_REFUSAL_MARKER in text or DATASET_SHORTFALL_REFUSAL_SENTENCE in text


def _producer_detail_from_refusal(detail: str) -> str:  # verbatim canopy 5907713b dashboard_manager.py:8356
    marker = "Producer detail: "
    if marker not in detail:
        return ""
    tail = detail.split(marker, 1)[1]
    for stop in (" To accept it,", " The resulting dataset"):
        if stop in tail:
            tail = tail.split(stop, 1)[0]
    return tail.strip()


# juniper-data origin/main juniper_data/core/limits.py:168 and :189, as the data-client wraps a 422.
PRODUCERS = {
    "limits:168 (cap)": "Validation error (422): equities universe is 503 symbols, over the 14 symbols cap. Re-submit with allow_truncation=true (or set JUNIPER_DATA_ALLOW_TRUNCATION=true) to import the first 14 symbols. The resulting dataset will be permanently annotated as truncated.",
    "limits:189 (quality)": "Validation error (422): Shares outstanding could not be resolved. Affected (3): AIZ, EOG, XYZ. 1,234 row(s) would carry fabricated values. Re-submit with allow_truncation=true (or set JUNIPER_DATA_ALLOW_TRUNCATION=true) to accept them, or with incomplete_rows='drop' to exclude them. Either choice is recorded permanently in the dataset's metadata.",
}
BRANCHES = {
    "flag off, silent": dict(allow_truncated=False),
    "caller refused (flag off)": dict(allow_truncated=False, caller_refused=True),
    "caller refused (flag on)": dict(allow_truncated=False, caller_refused=True, deployment_flag_on=True),
    "null, flag off": dict(allow_truncated=False, opt_in_skipped=M._OPT_IN_SKIPPED_CALLER_DEFERRED),
    "null, flag on": dict(allow_truncated=False, opt_in_skipped=M._OPT_IN_SKIPPED_CALLER_DEFERRED, deployment_flag_on=True),
    "WITHHELD, path None": dict(allow_truncated=False, opt_in_skipped=M._OPT_IN_SKIPPED_LIST_UNREADABLE, deployment_flag_on=True),
    "WITHHELD, staged start": dict(allow_truncated=False, opt_in_skipped=M._OPT_IN_SKIPPED_LIST_UNREADABLE, deployment_flag_on=True, fetch_path=M._FETCH_PATH_STAGED_START),
    "WITHHELD, live swap": dict(allow_truncated=False, opt_in_skipped=M._OPT_IN_SKIPPED_LIST_UNREADABLE, deployment_flag_on=True, fetch_path=M._FETCH_PATH_LIVE_SWAP),
    "WITHHELD, auto-start": dict(allow_truncated=False, opt_in_skipped=M._OPT_IN_SKIPPED_LIST_UNREADABLE, deployment_flag_on=True, fetch_path=M._FETCH_PATH_AUTO_START),
    "flag on, no reason (unreachable)": dict(allow_truncated=False, deployment_flag_on=True),
    "not declared (flag on)": dict(allow_truncated=False, opt_in_skipped=M._OPT_IN_SKIPPED_NOT_TRUNCATABLE, deployment_flag_on=True),
}
for pname, ptext in PRODUCERS.items():
    print(f"== producer {pname}")
    for bname, kw in BRANCHES.items():
        msg = M.TrainingLifecycleManager._describe_dataset_fetch_failure(RuntimeError(ptext), **kw)
        # the route wraps it exactly like this (routes/training.py:130) and canopy prefixes the HTTP status
        wire = f"HTTP 409: Training cannot be started: {msg}"
        refusal = _is_dataset_shortfall_refusal(wire)
        extracted = _producer_detail_from_refusal(wire)
        opens = "To accept it," in msg
        names_flag = "JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS" in msg or "--allow-truncated-datasets" in msg
        ok = (extracted == ptext) if refusal else (extracted == "")
        print(f"  [{bname:34s}] refusal={refusal!s:5} remedy_has_phrase={opens!s:5} names_flag={names_flag!s:5} extracted==producer={extracted == ptext!s:5} {'OK' if ok else 'MISMATCH'}")
        if refusal and extracted != ptext:
            print(f"      canopy renders: {extracted!r}")
            print(f"      producer wrote: {ptext!r}")
