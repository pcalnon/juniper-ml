"""
Write the unified diff of every D-14 carrier file against a clean tree of today's main, one file per diff.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc — investigation (flood-4 round-2 validation, D-14 code lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 disposition, D-14 (service-core resume cursor rules + shared answer table)

Usage: python3 <this file> --clean <clean tree> --carrier <carrier tree> --out <dir> [--repo ml|cascor]
Reads only the two trees; writes <out>/<path with / replaced by __>.diff (an empty file when identical).
"""

import argparse
import difflib
import sys
from pathlib import Path

ML_FILES = (
    ".github/workflows/ci.yml",
    ".github/workflows/docs-full-check.yml",
    ".github/workflows/main-verify.yml",
    "AGENTS.md",
    "CHANGELOG.md",
    "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
    "docs/REFERENCE.md",
    "juniper-service-core/CHANGELOG.md",
    "juniper-service-core/juniper_service_core/websocket/manager.py",
    "juniper-service-core/juniper_service_core/websocket/training_stream.py",
    "juniper-service-core/pyproject.toml",
    "juniper-service-core/tests/test_websocket_resume_continuity.py",
)
CASCOR_FILES = (
    "CHANGELOG.md",
    "docs/api/API_SCHEMAS.md",
)


def read_lines(path: Path) -> list:
    if not path.is_file():
        return []
    with open(path, encoding="utf-8") as handle:
        return handle.readlines()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--clean", type=Path, required=True)
    parser.add_argument("--carrier", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--repo", choices=("ml", "cascor"), default="ml")
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for rel in ML_FILES if args.repo == "ml" else CASCOR_FILES:
        old, new = read_lines(args.clean / rel), read_lines(args.carrier / rel)
        diff = list(difflib.unified_diff(old, new, fromfile=f"main/{rel}", tofile=f"carrier/{rel}", n=3))
        target = args.out / (rel.replace("/", "__") + ".diff")
        with open(target, "w", encoding="utf-8") as handle:
            handle.writelines(diff)
        added = sum(1 for line in diff if line.startswith("+") and not line.startswith("+++"))
        removed = sum(1 for line in diff if line.startswith("-") and not line.startswith("---"))
        print(f"{rel}\t+{added}\t-{removed}\t{target.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
