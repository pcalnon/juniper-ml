"""Lane B probe: does each rendered Juniper NetworkPolicy's podSelector match its workload's pod labels?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (written by validation lane B, container-registry session, 2026-09-24)
Created: 2026-09-24
Status: ad-hoc — investigation (provenance copy of a validation-lane probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-deploy#232 (confirmed that the data policy selects only the data pods, including
         under nameOverride and values-production)

Usage: python3 util/ad-hoc/2026-09-24_laneB_helm_selector_match.py <helm-template-output.yaml> [...]

Reads one or more `helm template` outputs given on the command line and, for each render,
reports which Deployment pod templates each NetworkPolicy selects. Ephemeral scratch probe.
"""

import sys

import yaml


def matches(selector: dict, labels: dict) -> bool:
    ml = (selector or {}).get("matchLabels") or {}
    if (selector or {}).get("matchExpressions"):
        return False  # not used by this chart; flag rather than guess
    return all(labels.get(k) == v for k, v in ml.items())


for path in sys.argv[1:]:
    docs = [d for d in yaml.safe_load_all(open(path, encoding="utf-8")) if d]
    pods = {d["metadata"]["name"]: (d["spec"]["template"]["metadata"].get("labels") or {}) for d in docs if d.get("kind") in ("Deployment", "StatefulSet")}
    pods.update({d["metadata"]["name"]: (d["metadata"].get("labels") or {}) for d in docs if d.get("kind") == "Pod"})
    print(f"== {path}")
    for d in docs:
        if d.get("kind") != "NetworkPolicy":
            continue
        sel = d["spec"].get("podSelector")
        hit = sorted(n for n, lab in pods.items() if matches(sel, lab))
        print(f"  {d['metadata']['name']:40s} selects {hit}")
