"""
Flood-4 validation: for every carried draft, compare the set of test functions/methods the DRAFT adds
(its merge-base -> head, per file) with the set the CARRIER adds (origin/main -> carrier tree), so a test
silently dropped or renamed in a rebuild shows up by name.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (fidelity, fixes and gates lens)
"""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
BASE = "303ccc0b4613dadcbe5ef16985a862beccec7a1a"
TREE = "ddfae11e73e0663bf798fef2834dfc559493e7fe"
DRAFTS = [2466, 2419, 2427, 2430, 2436, 2439, 2441, 2443, 2445, 2447, 2451, 2458, 2461, 2463, 2425, 2413, 2414, 2416, 2429, 2431, 2434, 2421, 2448, 2459, 2410, 2455, 2403, 2407]


def show(ref: str, path: str) -> str | None:
    r = subprocess.run(["git", "show", f"{ref}:{path}"], cwd=HERE, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def names(src: str | None) -> set[str]:
    if src is None:
        return set()
    out: set[str] = set()
    for node in ast.parse(src).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
            out.add(node.name)
        elif isinstance(node, ast.ClassDef):
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and sub.name.startswith("test"):
                    out.add(f"{node.name}.{sub.name}")
    return out


def main() -> int:
    total_draft = total_carried = 0
    for n in DRAFTS:
        head = f"refs/flood4/pr/{n}"
        mb = subprocess.run(["git", "merge-base", BASE, head], cwd=HERE, capture_output=True, text=True, check=True).stdout.strip()
        files = subprocess.run(["git", "diff", "--name-only", mb, head], cwd=HERE, capture_output=True, text=True, check=True).stdout.split()
        for f in files:
            if not f.endswith(".py"):
                continue
            d_add = names(show(head, f)) - names(show(mb, f))
            d_del = names(show(mb, f)) - names(show(head, f))
            c_add = names(show(TREE, f)) - names(show(BASE, f))
            c_del = names(show(BASE, f)) - names(show(TREE, f))
            total_draft += len(d_add)
            total_carried += len(d_add & c_add)
            flag = "" if (d_add == c_add and not c_del) else "  <-- DIFFERS"
            print(f"#{n} {f}: draft adds {len(d_add)} (deletes {sorted(d_del)}), carrier adds {len(c_add)} (deletes {sorted(c_del)}){flag}")
            if flag:
                print(f"     only in draft: {sorted(d_add - c_add)}")
                print(f"     only in carrier: {sorted(c_add - d_add)}")
    print(f"draft-added tests {total_draft}; of those carried by name {total_carried}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
