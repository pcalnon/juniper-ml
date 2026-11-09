#!/usr/bin/env python3
"""
pytest plugin: record where every loaded module came from (validation worktree vs the canopy primary).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-canopy tests carrier VALIDATION)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy#789 #792 #794 #795; flood-4 validation brief (test correctness lens)

JuniperCanopy1 carries an EDITABLE juniper-canopy install whose finder maps backend/, frontend/,
logger/ ... to the PRIMARY checkout, so a run from a worktree can silently test the primary's code.
At session end this plugin appends, to $VAL_ORIGIN_FILE, the __file__ of the canopy modules that
matter and a count of modules loaded from the primary. Load with `-p 2026-11-07_flood4_val_canopy_origin_plugin`
and this directory on PYTHONPATH.
"""

from __future__ import annotations

import os
import sys

PRIMARY = os.path.expanduser("~/Development/python/Juniper/juniper-canopy/")
KEY_MODULES = ("settings", "config_manager", "canopy_constants", "main", "backend", "frontend", "logger", "juniper_canopy")


def pytest_sessionfinish(session, exitstatus):  # noqa: ARG001 - pytest hook signature
    out = os.environ.get("VAL_ORIGIN_FILE")
    root = os.environ.get("VAL_ROOT", "")
    lines = [f"exitstatus={int(exitstatus)} python={sys.version.split()[0]} executable={sys.executable}"]
    from_primary = []
    from_root = 0
    for name, module in sorted(sys.modules.items()):
        path = getattr(module, "__file__", None) or ""
        if path.startswith(PRIMARY):
            from_primary.append(f"{name} -> {path}")
        elif root and path.startswith(root):
            from_root += 1
    for name in KEY_MODULES:
        module = sys.modules.get(name)
        lines.append(f"KEY {name}: {getattr(module, '__file__', None) if module else '(not loaded)'}")
    for name, module in sorted(sys.modules.items()):
        if name.endswith("conftest") or name.startswith("test_") or ".test_" in name:
            path = getattr(module, "__file__", "") or ""
            if "test_bandit_sarif" in path or "test_codecov_token" in path or "test_lockfile_regen" in path or "test_agents_md_date" in path or name.endswith("conftest"):
                lines.append(f"MOD {name}: {path}")
    lines.append(f"modules-from-validation-root={from_root}")
    lines.append(f"modules-from-primary={len(from_primary)}")
    lines.extend(f"PRIMARY {row}" for row in from_primary)
    text = "\n".join(lines) + "\n"
    if out:
        with open(out, "a", encoding="utf-8") as handle:
            handle.write(text)
    else:
        sys.stderr.write(text)
