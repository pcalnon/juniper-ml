"""
A pytest plugin that prints, at the end of a session, which file each WebSocket module under test was imported from.

The JuniperCascor1 env holds editable installs of juniper-cascor and juniper-service-core that point at the PRIMARY
checkouts, so a run from a worktree or a scratch copy can import the wrong tree without any error. Load it with
``-p 2026-11-15_flood4r2_d14_provenance_plugin`` and this directory on ``PYTHONPATH``; it prints one
``PROVENANCE <module> <file> <sha256>`` line per module already imported, and imports nothing itself.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table)
"""

import hashlib
import sys

MODULES = (
    "api.websocket.training_stream",
    "api.websocket.manager",
    "juniper_service_core.websocket.training_stream",
    "juniper_service_core.websocket.manager",
)


def pytest_sessionfinish(session, exitstatus):
    for name in MODULES:
        module = sys.modules.get(name)
        if module is None:
            continue
        path = module.__file__
        with open(path, "rb") as handle:
            digest = hashlib.sha256(handle.read()).hexdigest()
        sys.stdout.write(f"\nPROVENANCE {name} {path} {digest}\n")
