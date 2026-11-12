#!/usr/bin/env python3
"""
Run juniper-ci-tools' symbol-loss classification on a base file and an UNCOMMITTED head file.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4, owner ruling 17 ("canopy: dead error path"); juniper-canopy's Sequence Safety
         symbol screen over src/tests/regression/test_lockfile_regen_empty_payload.py

The CI screen (``juniper-symbol-loss-check``) diffs two git refs. The ruling-17 tree is
uncommitted, so this calls the same ``symbols_for`` and ``classify_file`` from this
checkout's ``juniper-ci-tools/`` source on two file texts: main's copy (``--base``) and the
worktree file (``--head``). It reports every LOST / WEAKENED / DUPLICATED verdict and the
symbols the head adds.

Usage::

    python3 util/ad-hoc/2026-11-09_flood4r2_r17-canopy-lockfile_symbol_screen.py --base <main copy> --head <worktree file> --path <repo-relative path>

Exit 1 on any FAIL-severity finding.
"""

import argparse
import sys
from pathlib import Path

_CI_TOOLS = Path(__file__).resolve().parents[2] / "juniper-ci-tools"
sys.path.insert(0, str(_CI_TOOLS))
from juniper_ci_tools import symbol_loss_check as sym  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--head", type=Path, required=True)
    parser.add_argument("--path", required=True)
    args = parser.parse_args()
    base_inv, base_ok = sym.symbols_for(args.path, args.base.read_text(encoding="utf-8"))
    head_inv, head_ok = sym.symbols_for(args.path, args.head.read_text(encoding="utf-8"))
    if not (base_ok and head_ok) or base_inv is None or head_inv is None:
        print("unparseable input")
        return 1
    findings = sym.classify_file(args.path, base_inv, head_inv, args.path.endswith(".bash"))
    for finding in findings:
        print(f"{finding.severity} {finding.verdict} {finding.symbol} {finding.detail}")
    added = sorted(set(head_inv) - set(base_inv))
    print(f"base symbols {len(base_inv)}, head symbols {len(head_inv)}, findings {len(findings)}")
    print(f"added: {added}")
    print(f"ci-tools source: {_CI_TOOLS}")
    return 1 if any(f.severity == "FAIL" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
