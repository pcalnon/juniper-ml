#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : juniper-canopy#631 -- packaging decision inputs
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Measure the three things canopy#631's open decisions actually turn on.

The issue lists a suggested ``py-modules`` set built from "imported by a SHIPPED wheel
member". That is the right set for making the CURRENT wheel importable and the wrong set
for deciding what the package should contain, because it stops at one hop: if ``main``
ships, whatever ``main`` imports has to ship too, and none of that appears in a census
anchored on today's members.

So this computes, from the checkout rather than from the wheel:

  1. **sdist coverage** -- does the source distribution already carry the modules the wheel
     drops? If it does, ``--no-binary`` is a real (if ugly) workaround and the severity of
     the wheel bug changes.
  2. **transitive closure** -- starting from the shipped packages AND from ``main``, which
     top-level modules are reachable? That is the true minimum ship set, and the gap
     between it and the one-hop set is the cost of answering decision 1 by inspection.
  3. **re-parenting cost** -- how many import statements across the repo would a move of
     these modules under ``juniper_canopy/`` have to rewrite, counting tests and the
     container's own entrypoint separately from library code.

Usage:
  python util/ad-hoc/2026-09-15_canopy_packaging_decision_inputs.py \\
      --repo /home/pcalnon/Development/python/Juniper/juniper-canopy --version 0.8.0
"""

import argparse
import ast
import io
import json
import re
import sys
import tarfile
import urllib.request
from pathlib import Path

PYPI = "https://pypi.org/pypi/{pkg}/{ver}/json"
WHEEL_PKGS = ("backend", "communication", "frontend", "logger", "juniper_canopy")


def top_level_modules(src: Path) -> "set[str]":
    return {p.stem for p in src.glob("*.py") if p.stem != "__init__"}


def imports_of(path: Path, universe: "set[str]") -> "set[str]":
    """Top-level modules from ``universe`` that this file imports.

    Uses the AST rather than a regex: a regex over source counts names inside strings,
    comments and docstrings, and this repo's modules are named in prose throughout.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError:
        return set()
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                root = a.name.split(".")[0]
                if root in universe:
                    found.add(root)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            root = node.module.split(".")[0]
            if root in universe:
                found.add(root)
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--package", default="juniper-canopy")
    ap.add_argument("--version", default="0.8.0")
    args = ap.parse_args()

    repo = Path(args.repo)
    src = repo / "src"
    universe = top_level_modules(src)

    # ── 1. sdist coverage ────────────────────────────────────────────────────
    with urllib.request.urlopen(PYPI.format(pkg=args.package, ver=args.version), timeout=60) as r:  # noqa: S310
        meta = json.load(r)
    sdists = [u for u in meta["urls"] if u["packagetype"] == "sdist"]
    print("=" * 78)
    print("1. SDIST COVERAGE")
    if not sdists:
        print("   no sdist published")
    else:
        with urllib.request.urlopen(sdists[0]["url"], timeout=180) as r:  # noqa: S310
            tf = tarfile.open(fileobj=io.BytesIO(r.read()), mode="r:gz")
        names = tf.getnames()
        in_sdist = {m for m in universe if any(n.endswith(f"src/{m}.py") for n in names)}
        print(f"   {sdists[0]['filename']}: {len(names)} members")
        print(f"   top-level src modules present: {len(in_sdist)}/{len(universe)}")
        missing = sorted(universe - in_sdist)
        print(f"   absent from sdist: {missing if missing else 'none'}")
        has_pyproject = any(n.endswith("pyproject.toml") for n in names)
        print(f"   carries pyproject.toml (so it rebuilds with the same bug): {has_pyproject}")

    # ── 2. transitive closure ────────────────────────────────────────────────
    print("=" * 78)
    print("2. TRANSITIVE CLOSURE OF TOP-LEVEL MODULES")
    graph = {m: imports_of(src / f"{m}.py", universe) for m in universe}

    def closure(seeds: "set[str]") -> "set[str]":
        seen, stack = set(), list(seeds)
        while stack:
            m = stack.pop()
            if m in seen:
                continue
            seen.add(m)
            stack.extend(graph.get(m, ()) - seen)
        return seen

    # seeds reached from the packages the wheel already ships
    pkg_seeds: "set[str]" = set()
    for pkg in WHEEL_PKGS:
        d = src / pkg if (src / pkg).is_dir() else repo / pkg
        if d.is_dir():
            for f in d.rglob("*.py"):
                pkg_seeds |= imports_of(f, universe)
    from_pkgs = closure(pkg_seeds)
    from_main = closure({"main"} & universe)
    both = from_pkgs | from_main

    print(f"   reachable from the SHIPPED packages : {len(from_pkgs)}  {sorted(from_pkgs)}")
    print(f"   reachable from main.py              : {len(from_main)}  {sorted(from_main)}")
    print(f"   union (minimum ship set)            : {len(both)}")
    print(f"   never reachable (genuinely unused)  : {sorted(universe - both)}")
    print(f"   extra that shipping `main` pulls in : {sorted(from_main - from_pkgs)}")

    # ── 3. re-parenting cost ─────────────────────────────────────────────────
    print("=" * 78)
    print("3. RE-PARENTING COST (move these modules under juniper_canopy/)")
    pat = re.compile(r"^\s*(?:from\s+(" + "|".join(sorted(universe)) + r")\b|import\s+(" +
                     "|".join(sorted(universe)) + r")\b)", re.M)
    buckets = {"src/tests": 0, "src (library)": 0, "other": 0}
    files = {"src/tests": set(), "src (library)": set(), "other": set()}
    for f in repo.rglob("*.py"):
        if any(part in {".git", "__pycache__", "build", "dist", ".venv"} for part in f.parts):
            continue
        rel = f.relative_to(repo).as_posix()
        n = len(pat.findall(f.read_text(encoding="utf-8", errors="replace")))
        if not n:
            continue
        key = "src/tests" if rel.startswith("src/tests/") else ("src (library)" if rel.startswith("src/") else "other")
        buckets[key] += n
        files[key].add(rel)
    for key, n in buckets.items():
        print(f"   {key:16s} {n:5d} import statements across {len(files[key]):4d} files")
    print(f"   TOTAL            {sum(buckets.values()):5d} import statements across "
          f"{sum(len(v) for v in files.values()):4d} files")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
