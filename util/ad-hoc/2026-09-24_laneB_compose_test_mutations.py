"""Lane B probe: do juniper-deploy#231's compose tests catch semantically-equivalent defects?

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (written by validation lane B, container-registry session, 2026-09-24)
Created: 2026-09-24
Status: ad-hoc — investigation (provenance copy of a validation-lane probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-deploy#231's compose tests (lane B finding m4). Against #231 it passed P1-P7.
         juniper-deploy#233 closed P1, P2, P4, P6 and P7; #234 closed P3 and P5 (every case CAUGHT,
         re-run 2026-09-24 against that tree); #235 then pinned data-egress's whole definition.

Paths are relative to the lane's scratch directory, which was NOT retained. To re-run, extract a
juniper-deploy tree into d_post/ beside this file (docker-compose.yml, .env.observability and
tests/) and run with PYTHONPATH=d_post/tests.

Loads the merged docker-compose.yml, applies in-memory mutations, and runs the four
tests in tests/test_compose_data_egress.py plus the subnet-pinning test in
tests/test_compose_metrics_subnet_alignment.py against each mutated document.
Ephemeral scratch probe (READ-ONLY review lane); nothing in any repo is modified.
"""

import copy
import importlib.util
import os

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


egress = load("d_post/tests/test_compose_data_egress.py", "egress")
subnet = load("d_post/tests/test_compose_metrics_subnet_alignment.py", "subnet")
BASE = yaml.safe_load(open("d_post/docker-compose.yml", encoding="utf-8"))

EGRESS_TESTS = [n for n in dir(egress) if n.startswith("test_")]
SUBNET_TESTS = ["test_every_network_pins_a_unique_static_subnet"]


def run(label, mutate):
    doc = copy.deepcopy(BASE)
    mutate(doc)
    egress._load_compose = lambda _d=doc: copy.deepcopy(_d)
    subnet._load_compose = lambda _d=doc: copy.deepcopy(_d)
    fails = []
    for mod, names in ((egress, EGRESS_TESTS), (subnet, SUBNET_TESTS)):
        for n in names:
            try:
                getattr(mod, n)()
            except AssertionError:
                fails.append(n)
    print(f"{label:70s} -> {'CAUGHT by ' + ','.join(fails) if fails else 'ALL PASS'}")


print("services without a `networks:` key:", sorted(k for k, v in BASE["services"].items() if not (v or {}).get("networks")))
print("services with network_mode:", sorted(k for k, v in BASE["services"].items() if (v or {}).get("network_mode")))

run("control (as merged)", lambda d: None)
run("P1 sidecar with network_mode: service:juniper-data (shares data-egress)", lambda d: d["services"].__setitem__("sidecar", {"image": "busybox", "network_mode": "service:juniper-data"}))
run("P2 data-egress internal: 'true' (quoted string)", lambda d: d["networks"]["data-egress"].__setitem__("internal", "true"))
run("P3 data-egress internal: '${EGRESS_INTERNAL:-true}' (interpolated)", lambda d: d["networks"]["data-egress"].__setitem__("internal", "${EGRESS_INTERNAL:-true}"))
run("P4 data-egress masquerade disabled via driver_opts", lambda d: d["networks"]["data-egress"].__setitem__("driver_opts", {"com.docker.network.bridge.enable_ip_masquerade": "false"}))
run("P5 juniper-data ALSO joins non-internal `frontend`", lambda d: d["services"]["juniper-data"]["networks"].append("frontend"))
run("P6 new service with NO networks key (lands on dynamic-IPAM `default`)", lambda d: d["services"].__setitem__("newsvc", {"image": "busybox"}))
run("P7 new service on network_mode: bridge (docker0, dynamic)", lambda d: d["services"].__setitem__("newsvc", {"image": "busybox", "network_mode": "bridge"}))
run("P8 PR's own: demo-seed attached to data-egress", lambda d: d["services"]["demo-seed"]["networks"].append("data-egress"))
run("P9 PR's own: juniper-data publishes a port", lambda d: d["services"]["juniper-data"].__setitem__("ports", ["127.0.0.1:8100:8100"]))
