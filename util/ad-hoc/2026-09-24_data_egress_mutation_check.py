#!/usr/bin/env python3
"""
Mutation-check juniper-deploy's `data-egress` guards: each planted defect must turn its test red.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-deploy `tests/test_compose_data_egress.py` (new) and the `EXPECTED_NETWORKS` /
         declared-set change to `tests/test_compose_metrics_subnet_alignment.py`, which give
         juniper-data an outbound-only network (owner ruling 2026-09-24).

A guard that passes on the tree it was written against proves nothing about the defect it names.
This copies the given juniper-deploy tree into a scratch directory once per mutation, rewrites
`docker-compose.yml` with one planted defect, and runs the two network test files there. The run
passes only if the unmutated CONTROL is green and every mutation is red, and red in the test that
names that defect (not merely somewhere). The rewrite is plain text replacement with an assertion
that the anchor exists exactly once, so a moved anchor stops the check instead of silently
mutating nothing.

Usage
-----
    python3 util/ad-hoc/2026-09-24_data_egress_mutation_check.py \
        --deploy-tree <path to an edited juniper-deploy tree> --python <interpreter with pytest+pyyaml>

Exit 0 = control green and every mutation caught by its named test; 1 = otherwise.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TEST_FILES = ["tests/test_compose_data_egress.py", "tests/test_compose_metrics_subnet_alignment.py"]

DATA_NETS = "      - backend\n      - data\n      # For outbound fetches: equities / equities_seq (Yahoo Finance, SEC EDGAR) and\n      # mnist / arc_agi (Hugging Face Hub) fetch at request time, and `backend` / `data`\n      # are internal. See the `data-egress` network definition.\n      - data-egress\n"
EGRESS_DEF = "  data-egress:\n    driver: bridge\n    ipam:\n      config:\n        - subnet: 172.27.0.0/16\n"
BACKEND_DEF = "  backend:\n    driver: bridge\n    internal: true\n"
DEMO_SEED_NETS = "    networks:\n      - backend\n    restart: \"no\"\n"
EVERY = "test_every_service_declares_its_networks"
NOT_INTERNAL = "test_data_egress_is_declared_and_not_internal"

# (name, anchor, replacement, the test that must go red)
# M1-M7 are the first round's. M8-M12 are the gaps validation lane B showed passing the first
# version of the tests: a namespace-sharing sidecar, a quoted boolean, disabled masquerade, and a
# service on an undeclared network (juniper-deploy#233). M13-M14 are the two that #233's tests
# still passed: an interpolated boolean and a second non-internal network on juniper-data.
MUTATIONS = [
    ("drop data-egress from juniper-data", DATA_NETS, "      - backend\n      - data\n", "test_only_juniper_data_attaches_to_data_egress"),
    ("make data-egress internal", EGRESS_DEF, EGRESS_DEF.replace("    driver: bridge\n", "    driver: bridge\n    internal: true\n"), NOT_INTERNAL),
    ("publish a juniper-data port", "    container_name: juniper-data\n", '    container_name: juniper-data\n    ports:\n      - "127.0.0.1:8100:8100"\n', "test_juniper_data_publishes_no_port"),
    ("attach demo-seed to data-egress", DEMO_SEED_NETS, "    networks:\n      - backend\n      - data-egress\n    restart: \"no\"\n", "test_only_juniper_data_attaches_to_data_egress"),
    ("make backend non-internal", BACKEND_DEF, "  backend:\n    driver: bridge\n", "test_juniper_data_keeps_its_internal_networks"),
    ("unpin data-egress", EGRESS_DEF, "  data-egress:\n    driver: bridge\n", "test_every_network_pins_a_unique_static_subnet"),
    ("declare a sixth, unpinned network", EGRESS_DEF, EGRESS_DEF + "  scratch-net:\n    driver: bridge\n", "test_every_network_pins_a_unique_static_subnet"),
    ("make data-egress internal with a quoted boolean", EGRESS_DEF, EGRESS_DEF.replace("    driver: bridge\n", '    driver: bridge\n    internal: "true"\n'), NOT_INTERNAL),
    ("disable masquerade on data-egress", EGRESS_DEF, EGRESS_DEF.replace("    driver: bridge\n", '    driver: bridge\n    driver_opts:\n      com.docker.network.bridge.enable_ip_masquerade: "false"\n'), NOT_INTERNAL),
    ("a sidecar sharing juniper-data's namespace", "\nservices:\n", "\nservices:\n  data-sidecar:\n    image: busybox\n    network_mode: service:juniper-data\n\n", EVERY),
    ("demo-seed with no networks key", DEMO_SEED_NETS, "    restart: \"no\"\n", EVERY),
    ("demo-seed on network_mode bridge", DEMO_SEED_NETS, "    network_mode: bridge\n    restart: \"no\"\n", EVERY),
    # M13-M14: the two probes lane B's own script still passed after the first hardening.
    ("make data-egress internal through an interpolation", EGRESS_DEF, EGRESS_DEF.replace("    driver: bridge\n", '    driver: bridge\n    internal: "${EGRESS_INTERNAL:-true}"\n'), NOT_INTERNAL),
    ("juniper-data also joins the non-internal frontend", DATA_NETS, DATA_NETS + "      - frontend\n", "test_juniper_data_keeps_its_internal_networks"),
    # M15-M21: round-2 lane R2's keys and R1's undeclared-network case, which #234's tests passed
    # (they checked two keys by value). juniper-deploy#235 pins the whole definition instead.
    ("R2: gateway_mode_ipv4 routed (no NAT)", EGRESS_DEF, EGRESS_DEF.replace("    driver: bridge\n", "    driver: bridge\n    driver_opts:\n      com.docker.network.bridge.gateway_mode_ipv4: routed\n"), NOT_INTERNAL),
    ("R2: gateway_mode_ipv4 nat-unprotected (reopens direct routing)", EGRESS_DEF, EGRESS_DEF.replace("    driver: bridge\n", "    driver: bridge\n    driver_opts:\n      com.docker.network.bridge.gateway_mode_ipv4: nat-unprotected\n"), NOT_INTERNAL),
    ("R2: inhibit_ipv4 (no gateway address)", EGRESS_DEF, EGRESS_DEF.replace("    driver: bridge\n", '    driver: bridge\n    driver_opts:\n      com.docker.network.bridge.inhibit_ipv4: "true"\n'), NOT_INTERNAL),
    ("R2: an interpolated gateway mode", EGRESS_DEF, EGRESS_DEF.replace("    driver: bridge\n", '    driver: bridge\n    driver_opts:\n      com.docker.network.bridge.gateway_mode_ipv4: "${DATA_EGRESS_GW_MODE:-nat}"\n'), NOT_INTERNAL),
    ("R2: an interpolated driver", EGRESS_DEF, EGRESS_DEF.replace("    driver: bridge\n", '    driver: "${DATA_EGRESS_DRIVER:-bridge}"\n'), NOT_INTERNAL),
    ("R2: a service extending juniper-data inherits data-egress", "\nservices:\n", "\nservices:\n  data-extended:\n    extends:\n      service: juniper-data\n    networks:\n      - backend\n\n", "test_no_service_uses_extends"),
    ("R1: demo-seed on the undeclared default network", DEMO_SEED_NETS, "    networks:\n      - default\n    restart: \"no\"\n", EVERY),
    # M22-M25: round-3 lane R3's shapes that passed #235's tests (juniper-deploy#236 is the fix).
    ("R3: a top-level include", "\nservices:\n", "\ninclude:\n  - extra.yml\nservices:\n", "test_compose_file_includes_nothing"),
    ("R3: monitoring made an external alias of the egress network", "  monitoring:\n    driver: bridge\n    ipam:\n      config:\n        - subnet: 172.31.0.0/16\n", "  monitoring:\n    external: true\n    name: juniper-deploy_data-egress\n", "test_no_declared_network_is_an_external_alias"),
    ("R3: juniper-data resolves through 127.0.0.1", "    container_name: juniper-data\n", "    container_name: juniper-data\n    dns:\n      - 127.0.0.1\n", "test_juniper_data_has_no_dns_or_host_overrides"),
    ("R3: juniper-data maps a fetch host to 127.0.0.1", "    container_name: juniper-data\n", '    container_name: juniper-data\n    extra_hosts:\n      - "query2.finance.yahoo.com:127.0.0.1"\n', "test_juniper_data_has_no_dns_or_host_overrides"),
]


def run_tests(tree: Path, python: str) -> subprocess.CompletedProcess:
    return subprocess.run([python, "-m", "pytest", *TEST_FILES, "-q", "-p", "no:cacheprovider", "-rf"], cwd=tree, capture_output=True, text=True, check=False)


def scratch_copy(src: Path, dst: Path) -> None:
    shutil.copytree(src / "tests", dst / "tests")
    # pyproject.toml carries `pythonpath = ["tests"]`; without it conftest.py cannot import `constants`.
    for name in ("docker-compose.yml", ".env.observability", "pyproject.toml"):
        if (src / name).exists():
            shutil.copy2(src / name, dst / name)
    if (src / "prometheus").exists():
        shutil.copytree(src / "prometheus", dst / "prometheus")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    parser.add_argument("--deploy-tree", required=True, type=Path)
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args()
    compose_text = (args.deploy_tree / "docker-compose.yml").read_text(encoding="utf-8")
    ok = True
    with tempfile.TemporaryDirectory(prefix="egress-mut-") as tmp:
        control = Path(tmp) / "control"
        scratch_copy(args.deploy_tree, control)
        res = run_tests(control, args.python)
        print(f"  CONTROL: {'green' if res.returncode == 0 else 'RED'} ({res.stdout.strip().splitlines()[-1] if res.stdout.strip() else res.stderr.strip()[-200:]})")
        ok &= res.returncode == 0
        for i, (name, anchor, replacement, must_fail) in enumerate(MUTATIONS):
            count = compose_text.count(anchor)
            if count != 1:
                print(f"  M{i + 1} {name}: ANCHOR found {count} times -- stopped, nothing mutated")
                ok = False
                continue
            tree = Path(tmp) / f"m{i + 1}"
            scratch_copy(args.deploy_tree, tree)
            (tree / "docker-compose.yml").write_text(compose_text.replace(anchor, replacement), encoding="utf-8")
            res = run_tests(tree, args.python)
            failed = [line for line in res.stdout.splitlines() if line.startswith("FAILED")]
            caught = any(f"::{must_fail}" in line for line in failed)
            verdict = "CAUGHT" if res.returncode != 0 and caught else "MISSED"
            print(f"  M{i + 1} {name}: {verdict} (expected red: {must_fail}; red: {[line.split('::')[-1].split(' ')[0] for line in failed]})")
            ok &= verdict == "CAUGHT"
    print("  ALL MUTATIONS CAUGHT" if ok else "  MUTATION CHECK FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
