"""
Run pytest in process and record which juniper_service_core WebSocket modules the session imported (path + sha256).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, code lens r23w-val-code: validate ruling 23's "WebSocket gaps beside N-4")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23); juniper-ml#2547 (N-4)

pytest's default "prepend" import mode puts the first ancestor of a test file without an __init__.py at the front
of sys.path, so the code a run measures is decided by WHERE the test file sits, not by PYTHONPATH. This wrapper
prints the imported manager.py / control_stream.py / training_stream.py paths and sha256 prefixes at session end,
so each arm names the code it ran.

Usage (from the directory pytest should run in):
  python <this file> --where-out WHERE.txt -- <pytest args...>
"""

from __future__ import annotations

import hashlib
import sys

import pytest

_MODULES = (
    "juniper_service_core.websocket.manager",
    "juniper_service_core.websocket.control_stream",
    "juniper_service_core.websocket.training_stream",
)


class Where:
    def __init__(self, out: str) -> None:
        self.out = out

    def pytest_sessionfinish(self, session, exitstatus) -> None:  # noqa: ARG002 - pytest hook signature
        lines = []
        for name in _MODULES:
            mod = sys.modules.get(name)
            if mod is None or not getattr(mod, "__file__", None):
                lines.append(f"{name}: NOT IMPORTED")
                continue
            with open(mod.__file__, "rb") as fh:
                digest = hashlib.sha256(fh.read()).hexdigest()
            lines.append(f"{name}: {mod.__file__} sha256={digest[:12]}")
        lines.append(f"exitstatus={int(exitstatus)} python={sys.version.split()[0]} executable={sys.executable}")
        with open(self.out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")


def main(argv: list[str]) -> int:
    if "--" not in argv or argv[1] != "--where-out":
        print(__doc__)
        return 2
    out = argv[2]
    args = argv[argv.index("--") + 1 :]
    return int(pytest.main(args, plugins=[Where(out)]))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
