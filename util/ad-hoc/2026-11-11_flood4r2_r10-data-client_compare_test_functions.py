#!/usr/bin/env python3
"""
Compare a port's secret-scan test file with juniper-data's, function by function: identical, changed, new, not ported.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation (ruling 10: the port of juniper-data#530 to juniper-data-client)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 (ruling 10); juniper-data#530

WHY THIS EXISTS
juniper-data#530's test cases were validated three times. A port should carry them unchanged wherever the
repository allows, and say exactly where it could not. This reads both files' top-level functions with `ast`,
compares their source text by name, and prints four lists and a zero-context diff of each changed function, so
the port's "these cases are juniper-data's" is a measured statement. It reads two files and writes --out.

Usage:
    python3 <this> --port <the port's test file> --data <juniper-data's test file> --out <json>
"""

from __future__ import annotations

import argparse
import ast
import difflib
import json
import sys
from pathlib import Path


def functions(path: Path) -> dict[str, str]:
    source = path.read_text(encoding="utf-8")
    return {node.name: ast.get_source_segment(source, node) or "" for node in ast.parse(source).body if isinstance(node, ast.FunctionDef)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--port", type=Path, required=True)
    ap.add_argument("--data", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    port, data = functions(args.port), functions(args.data)
    result = {
        "identical": sorted(name for name in port if name in data and port[name] == data[name]),
        "changed": {name: [line for line in difflib.unified_diff(data[name].splitlines(), port[name].splitlines(), lineterm="", n=0) if not line.startswith(("---", "+++"))] for name in sorted(port) if name in data and port[name] != data[name]},
        "only_in_port": sorted(name for name in port if name not in data),
        "only_in_juniper_data": sorted(name for name in data if name not in port),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
        fh.write("\n")
    print(f"identical to juniper-data's: {len(result['identical'])}")
    print(f"changed: {sorted(result['changed'])}")
    print(f"only in the port: {result['only_in_port']}")
    print(f"only in juniper-data (not ported): {len(result['only_in_juniper_data'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
