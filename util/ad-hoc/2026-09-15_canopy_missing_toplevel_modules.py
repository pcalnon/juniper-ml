#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : release verification -- juniper-canopy packaging
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Which top-level modules under juniper-canopy's ``src/`` does the wheel fail to ship?

``[tool.setuptools.packages.find]`` with ``where = [".", "src"]`` finds **packages** --
directories carrying ``__init__.py``. A bare ``src/<name>.py`` is a top-level **module**,
which that mechanism never collects and which needs an explicit ``py-modules`` entry. So
every such module is silently dropped from the wheel while the packages that import it ship
fine, and the failure only appears at import time in an installed environment.

``canopy_constants`` is the one that bites first. This enumerates the whole set rather than
stopping there: a finding that names only the module you happened to hit sends the fix out
one module short, and the next one surfaces as a second incident.

Cross-references three things:
  1. every ``src/*.py`` that is not inside a package
  2. whether the published wheel ships it
  3. whether any SHIPPED wheel member imports it (an unshipped module nobody imports is
     dead weight; one that is imported is a broken install)

Usage:
  python util/ad-hoc/2026-09-15_canopy_missing_toplevel_modules.py \\
      --repo /home/pcalnon/Development/python/Juniper/juniper-canopy --version 0.8.0
"""

import argparse
import io
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

PYPI = "https://pypi.org/pypi/{pkg}/{ver}/json"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="juniper-canopy checkout root")
    ap.add_argument("--package", default="juniper-canopy")
    ap.add_argument("--version", default="0.8.0")
    args = ap.parse_args()

    src = Path(args.repo) / "src"
    if not src.is_dir():
        print(f"no src/ under {args.repo}", file=sys.stderr)
        return 2
    # A top-level module: src/<name>.py, not src/<pkg>/<name>.py, and not the package marker.
    modules = sorted(p.stem for p in src.glob("*.py") if p.stem != "__init__")

    with urllib.request.urlopen(PYPI.format(pkg=args.package, ver=args.version), timeout=60) as r:  # noqa: S310
        meta = json.load(r)
    url = next(u["url"] for u in meta["urls"] if u["packagetype"] == "bdist_wheel")
    with urllib.request.urlopen(url, timeout=180) as r:  # noqa: S310
        zf = zipfile.ZipFile(io.BytesIO(r.read()))
    members = [m for m in zf.namelist() if m.endswith(".py")]
    shipped_top = {m[:-3] for m in members if "/" not in m}

    # What do the SHIPPED sources import?
    text = {m: zf.read(m).decode("utf-8", "replace") for m in members}
    print(f"{args.package} {args.version}: {len(members)} .py members, "
          f"{len(modules)} top-level modules under src/\n")

    broken, dead, ok = [], [], []
    for mod in modules:
        pat = re.compile(rf"^\s*(?:from\s+{re.escape(mod)}\s+import|import\s+{re.escape(mod)}\b)", re.M)
        importers = [m for m, t in text.items() if pat.search(t)]
        if mod in shipped_top:
            ok.append((mod, importers))
        elif importers:
            broken.append((mod, importers))
        else:
            dead.append((mod, importers))

    for mod, imp in broken:
        print(f"  [BROKEN]   {mod:28s} NOT shipped, imported by {len(imp)} shipped member(s)")
        for m in imp[:4]:
            print(f"                 <- {m}")
        if len(imp) > 4:
            print(f"                 ... and {len(imp) - 4} more")
    for mod, _ in dead:
        print(f"  [UNUSED]   {mod:28s} not shipped, and no shipped member imports it")
    for mod, imp in ok:
        print(f"  [SHIPPED]  {mod:28s} imported by {len(imp)} shipped member(s)")

    print(f"\n{len(broken)} broken / {len(dead)} unshipped-but-unused / {len(ok)} shipped")
    if broken:
        print("\nAdd to pyproject.toml -- packages.find collects PACKAGES only:", file=sys.stderr)
        print("  [tool.setuptools]", file=sys.stderr)
        print(f"  py-modules = {[m for m, _ in broken]!r}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
