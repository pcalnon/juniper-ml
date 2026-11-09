#!/usr/bin/env python3
"""
Round-5 validator: save the base (7bc9d3e2) copies of the docs carrier's 7 files and the source files the docs
describe, and write a unified diff of each frozen carrier file against its base copy.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 docs carrier, validator round 5)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-ml#2519 docs carrier, validation round 5 (findings: tmp/flood4/ml-docs/val-round5/)

Usage: python3 2026-11-07_flood4_val_round5_base_and_diff.py <frozen_dir> <out_dir>   (run from a juniper-ml checkout)
"""

from __future__ import annotations

import difflib
import os
import subprocess  # nosec B404 - fixed git argv
import sys

BASE = "7bc9d3e2"
DOCS = ["CHANGELOG.md", "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md", "docs/DOCUMENTATION_OVERVIEW.md", "docs/QUICK_START.md", "docs/REFERENCE.md", "juniper-config-tools/README.md", "juniper-service-core/README.md"]
SOURCES = ["juniper-service-core/juniper_service_core/workers/security.py", "juniper-service-core/juniper_service_core/websocket/worker_stream.py", "juniper-service-core/juniper_service_core/security.py", "juniper-service-core/juniper_service_core/middleware.py", "juniper-observability/juniper_observability/sentry.py"]


def _show(path: str) -> str:
    return subprocess.run(["git", "show", f"{BASE}:{path}"], check=True, capture_output=True, text=True).stdout  # nosec B603 B607


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    frozen, out = argv[1], argv[2]
    os.makedirs(os.path.join(out, "base"), exist_ok=True)
    summary = []
    for path in DOCS + SOURCES:
        text = _show(path)
        flat = path.replace("/", "__")
        with open(os.path.join(out, "base", flat + ".txt"), "w", encoding="utf-8") as fh:
            fh.write(text)
        if path in DOCS:
            with open(os.path.join(frozen, path), encoding="utf-8") as fh:
                new = fh.read()
            diff = list(difflib.unified_diff(text.splitlines(keepends=True), new.splitlines(keepends=True), fromfile=f"{BASE}:{path}", tofile=f"carrier:{path}", n=0))
            with open(os.path.join(out, flat + ".patch"), "w", encoding="utf-8") as fh:
                fh.writelines(diff)
            plus = sum(1 for d in diff if d.startswith("+") and not d.startswith("+++"))
            minus = sum(1 for d in diff if d.startswith("-") and not d.startswith("---"))
            summary.append(f"{path}: +{plus} -{minus}")
    print("\n".join(summary))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
