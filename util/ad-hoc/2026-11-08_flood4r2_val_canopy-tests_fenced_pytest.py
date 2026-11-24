"""
Run pytest in a juniper-canopy worktree, in-process, with a socket fence and an import-origin record.

Validator helper for the flood-4 round-2 canopy-tests carrier (tests/code/CI lens). CI's runner has no
service on canopy's, data's or cascor's ports, so an unmocked connect there is refused; this host has live
listeners on several of them (canopy 8050 and the E2E legs 8052/8053/8058/8059, data 8100, cascor 8200-8202).
The fence refuses every AF_INET/AF_INET6 connect to those ports, as CI's empty runner would, and records each
attempt with the test that made it, so a run here neither reaches a live service nor hides a test that would.
It also records where ``backend.cascor_service_adapter`` and the drift script's test copies were imported
from, so a run is shown to have exercised THIS worktree's code, not the primary checkout's.

Usage (run with -I so neither this directory nor the user site is on sys.path):
  /opt/miniforge3/envs/JuniperCanopy1/bin/python -I <this file> --wt <canopy worktree> --out <json> -- <pytest args>

Writes <json>: {"exit": N, "fence_refusals": [...], "import_origins": {...}, "args": [...]}.
Exits with pytest's exit status.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-canopy#800, #801 (flood-4 round 2), canopy-tests carrier validation
"""

from __future__ import annotations

import argparse
import errno
import json
import os
import socket
import sys
from pathlib import Path

FENCED_PORTS = frozenset([8050, 8051, 8052, 8053, 8054, 8055, 8056, 8057, 8058, 8059, 8100, 8200, 8201, 8202])
# CI's unit step environment (ci.yml "Run Unit Tests with Coverage Gate"), plus the empty LIBTORCH /
# LD_LIBRARY_PATH the canopy verify note prescribes for this host.
CI_ENV = {"CASCOR_BACKEND_AVAILABLE": "0", "RUN_SERVER_TESTS": "0", "ENABLE_SLOW_TESTS": "0", "LIBTORCH": "", "LD_LIBRARY_PATH": ""}


class Fence:
    """A pytest plugin object: refuses fenced connects and records them per test."""

    def __init__(self, all_ports: bool = False) -> None:
        self.current = "<collection or session>"
        self.refusals: list[dict] = []
        self._orig_connect = socket.socket.connect
        self._orig_connect_ex = socket.socket.connect_ex
        fence = self

        def _fenced(address) -> bool:
            return isinstance(address, tuple) and len(address) >= 2 and isinstance(address[1], int) and (all_ports or address[1] in FENCED_PORTS)

        def connect(sock, address):
            if sock.family in (socket.AF_INET, socket.AF_INET6) and _fenced(address):
                fence.refusals.append({"test": fence.current, "address": [str(address[0]), address[1]], "call": "connect"})
                raise ConnectionRefusedError(errno.ECONNREFUSED, "refused by the validator's socket fence")
            return fence._orig_connect(sock, address)

        def connect_ex(sock, address):
            if sock.family in (socket.AF_INET, socket.AF_INET6) and _fenced(address):
                fence.refusals.append({"test": fence.current, "address": [str(address[0]), address[1]], "call": "connect_ex"})
                return errno.ECONNREFUSED
            return fence._orig_connect_ex(sock, address)

        socket.socket.connect = connect
        socket.socket.connect_ex = connect_ex

    def pytest_runtest_logstart(self, nodeid, location):
        self.current = nodeid


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--wt", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--all-ports", action="store_true", help="refuse and record EVERY AF_INET/AF_INET6 connect, not only the service ports")
    parser.add_argument("pytest_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    pytest_args = args.pytest_args[1:] if args.pytest_args[:1] == ["--"] else args.pytest_args

    os.environ.update(CI_ENV)
    for name in ("GITHUB_ACTIONS", "GITHUB_STEP_SUMMARY"):
        os.environ.pop(name, None)
    os.chdir(args.wt)

    import pytest  # imported after the environment is set

    fence = Fence(all_ports=args.all_ports)
    code = int(pytest.main(pytest_args, plugins=[fence]))
    origins = {}
    for name in ("backend.cascor_service_adapter", "check_juniper_data_generator_schemas", "check_juniper_data_generator_schemas_nested", "test_apply_partition_flat_legs"):
        module = sys.modules.get(name)
        origins[name] = getattr(module, "__file__", None) if module is not None else None
    wt = str(args.wt.resolve())
    outside = {name: path for name, path in origins.items() if path is not None and not str(Path(path).resolve()).startswith(wt + os.sep)}
    record = {"exit": code, "wt": wt, "args": pytest_args, "python": sys.version.split()[0], "fence_refusals": fence.refusals, "import_origins": origins, "imported_outside_wt": outside}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=1), encoding="utf-8")
    print(f"[fenced_pytest] exit={code} refusals={len(fence.refusals)} outside_wt={outside}")
    return code


if __name__ == "__main__":
    sys.exit(main())
