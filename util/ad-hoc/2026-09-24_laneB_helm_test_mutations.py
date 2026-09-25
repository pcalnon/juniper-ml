"""Lane B probe: do juniper-deploy#232's render tests catch strictly-broader egress rules?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (written by validation lane B, container-registry session, 2026-09-24)
Created: 2026-09-24
Status: ad-hoc — investigation (provenance copy of a validation-lane probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-deploy#232's render tests against strictly broader egress rules (lane B finding M2;
         fixed in juniper-deploy#233, whose strengthened tests util/ad-hoc/2026-09-24_helm_data_egress_mutation_check.py
         proves against the same nine shapes)

Paths are relative to the lane's scratch directory, which was NOT retained. To re-run, extract
juniper-deploy at 7ff6ff32 into d_post/ beside this file and save `helm template` of its chart as
render_post.yaml. Against #233's tests the TESTS tuple below no longer names existing tests; the
mutations are what this file preserves.

Loads the merged render (render_post.yaml), applies in-memory mutations, and runs the
three test functions from the merged test module against each mutated render.
Ephemeral scratch probe (READ-ONLY review lane); nothing in any repo is modified.
"""

import copy
import importlib.util
import os

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)

spec = importlib.util.spec_from_file_location("t", "d_post/tests/test_helm_networkpolicy_data_egress.py")
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
DOCS = [d for d in yaml.safe_load_all(open("render_post.yaml")) if d]
TESTS = (
    "test_data_policy_allows_https_to_public_addresses_only",
    "test_no_other_policy_gains_public_https",
    "test_policies_off_renders_no_policy",
)


def pol(ds, comp):
    return [d for d in ds if d.get("kind") == "NetworkPolicy" and (d["metadata"].get("labels") or {}).get("app.kubernetes.io/component") == comp][0]


def run(label, mutate):
    ds = copy.deepcopy(DOCS)
    mutate(ds)

    def fake_render(*, set_values=None, _ds=ds):
        return [] if set_values else copy.deepcopy(_ds)

    t._render_chart = fake_render
    res = []
    for name in TESTS:
        try:
            getattr(t, name)()
            res.append("PASS")
        except AssertionError:
            res.append("FAIL")
    print(f"{label:60s} data_only={res[0]} no_other={res[1]} off={res[2]}")


def data_egress(ds):
    return pol(ds, "data")["spec"]["egress"]


def cascor_egress(ds):
    return pol(ds, "cascor")["spec"]["egress"]


run("control (as merged)", lambda ds: None)
run("M1 data rule: endPort 65535 (443-65535 public)", lambda ds: data_egress(ds)[1]["ports"][0].__setitem__("endPort", 65535))
run("M2 data: extra rule 443 to ALL peers (no `to`)", lambda ds: data_egress(ds).append({"ports": [{"protocol": "TCP", "port": 443}]}))
run("M3 data: extra rule 0.0.0.0/0 ALL ports, no except", lambda ds: data_egress(ds).append({"to": [{"ipBlock": {"cidr": "0.0.0.0/0"}}]}))
run("M4 cascor: 0.0.0.0/0 on ALL ports", lambda ds: cascor_egress(ds).append({"to": [{"ipBlock": {"cidr": "0.0.0.0/0"}}]}))
run("M5 cascor: 443 to ALL peers (no `to`)", lambda ds: cascor_egress(ds).append({"ports": [{"protocol": "TCP", "port": 443}]}))
run("M6 cascor: 443 to ::/0 (IPv6)", lambda ds: cascor_egress(ds).append({"to": [{"ipBlock": {"cidr": "::/0"}}], "ports": [{"protocol": "TCP", "port": 443}]}))
run("M7 cascor: 443 to 0.0.0.0/1 + 128.0.0.0/1", lambda ds: cascor_egress(ds).append({"to": [{"ipBlock": {"cidr": "0.0.0.0/1"}}, {"ipBlock": {"cidr": "128.0.0.0/1"}}], "ports": [{"protocol": "TCP", "port": 443}]}))
run("M8 cascor: named port 'https' to 0.0.0.0/0", lambda ds: cascor_egress(ds).append({"to": [{"ipBlock": {"cidr": "0.0.0.0/0"}}], "ports": [{"protocol": "TCP", "port": "https"}]}))
run("M9 cascor: exact data rule copied (PR's own mutation)", lambda ds: cascor_egress(ds).append(copy.deepcopy(data_egress(ds)[1])))
