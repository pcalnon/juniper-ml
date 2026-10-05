# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10A2.g5NzBN/mutate.py
# Written by Lane 10-A2 (evidence and instruments), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, modified 2026-10-05 only to close the files it opens
# (CodeQL py/file-not-always-closed on juniper-ml#2157); what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase10_r1_probes_close_files.py.
# ---------------------------------------------------------------------------
"""Apply the lane's canopy mutations to the scratch copies (never to a repo checkout)."""
import sys

ROOT = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8e5d77a0-a8a3-4dc3-bd37-7d6bc3afebdc/scratchpad/lane10A2.g5NzBN"


def patch(path, old, new):
    with open(path) as fh:
        text = fh.read()
    assert text.count(old) == 1, (path, old[:60], text.count(old))
    with open(path, "w") as fh:
        fh.write(text.replace(old, new))
    print("patched", path.split("lane10A2.")[1], "::", old.strip()[:70])


which = sys.argv[1]
if which == "o2":
    p = f"{ROOT}/canopy_mut_o2/src/backend/cascor_service_adapter.py"
    # carry ``kind`` through both normalizers when the source row has it
    patch(p, '            "eval_metrics": eval_metrics,\n        }', '            "eval_metrics": eval_metrics,\n            **({"kind": entry["kind"]} if "kind" in entry else {}),\n        }')
    patch(p, '            "eval_metrics": flat.get("eval_metrics"),\n        }', '            "eval_metrics": flat.get("eval_metrics"),\n            **({"kind": flat["kind"]} if "kind" in flat else {}),\n        }')
elif which == "o2chart":
    p = f"{ROOT}/canopy_mut_o2/src/frontend/components/metrics_panel.py"
    # plot the accuracy chart on the step numbering only (needs ``kind`` carried: the o2 mutation)
    patch(
        p,
        '        for metric in metrics_data:\n            epochs.append(metric.get("epoch", 0))\n            acc = metric.get("metrics", {}).get("accuracy", 0)\n',
        '        for metric in metrics_data:\n            if metric.get("kind") == "output_epoch":\n                continue\n            epochs.append(metric.get("epoch", 0))\n            acc = metric.get("metrics", {}).get("accuracy", 0)\n',
    )
elif which == "backstop":
    p = f"{ROOT}/canopy_mut_backstop/src/backend/cascor_service_adapter.py"
    patch(p, '_DERIVED_READONLY_CASCOR_PARAMS: frozenset = frozenset({"epochs_max"})', "_DERIVED_READONLY_CASCOR_PARAMS: frozenset = frozenset()")
elif which == "o3b":
    p = f"{ROOT}/canopy_mut_o3b/src/backend/cascor_service_adapter.py"
    # unwrap the WS ack in _apply_params_hot (the ledger's other fix option)
    patch(
        p,
        '            logger.info(f"Cascor params updated via WS: {list(params.keys())}")\n            return result if isinstance(result, dict) else {}\n',
        '            logger.info(f"Cascor params updated via WS: {list(params.keys())}")\n            if isinstance(result, dict) and isinstance((result.get("data") or {}).get("result"), dict):\n                return result["data"]["result"]\n            return result if isinstance(result, dict) else {}\n',
    )
elif which == "o3":
    p = f"{ROOT}/canopy_mut_o3/src/backend/cascor_service_adapter.py"
    # the extractor also scans the WS ack's data.result
    patch(
        p,
        '        if isinstance(inner, dict):\n            containers.append(inner)\n',
        '        if isinstance(inner, dict):\n            containers.append(inner)\n            if isinstance(inner.get("result"), dict):\n                containers.append(inner["result"])\n',
    )
