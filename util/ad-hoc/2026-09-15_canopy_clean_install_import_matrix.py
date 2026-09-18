#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : juniper-canopy#631 -- choosing the publish-time guard's module list
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Which modules can a CLEAN install of the fixed wheel actually import?

The publish-time guard is only useful if its module list is one a correct wheel passes in
a fresh environment. Picking that list from a developer environment would bake in whatever
else happens to be installed there, and picking it by reading source would miss import-time
side effects -- a module that builds a FastAPI app or reads a config file at import can fail
for reasons that have nothing to do with packaging, and a guard that trips on those gets
disabled the first time it cries wolf.

So: build a real venv, `pip install` the wheel WITH its declared dependencies, `cd` out of
the source tree, and import every candidate in a separate interpreter. Report each as OK,
MISSING (a canopy module the wheel omits -- what the guard exists to catch) or ERROR (imports
fine but raises, e.g. needs configuration -- excluded from the guard, with the reason kept).

Usage:
  python util/ad-hoc/2026-09-15_canopy_clean_install_import_matrix.py \\
      --wheel /path/to/juniper_canopy-*.whl --venv /tmp/canopy-smoke
"""

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# Deps of an OPTIONAL extra. A wheel installed WITHOUT its extras is expected to miss these,
# so a module that needs one is not a packaging defect -- it is correctly optional. The first
# draft's allowlist held only base deps, so it reported `demo_mode` (torch, the `demo` extra)
# and `backend.service_backend` (juniper_cascor_client, the `juniper-cascor` extra) as defects.
OPTIONAL_EXTRA_DEPS = {
    "torch", "juniper_cascor_client", "juniper_data_client", "sentry_sdk",
    "playwright", "pytest_playwright",
}

CANDIDATES = [
    # packages
    "juniper_canopy", "backend", "communication", "frontend", "logger",
    # the module the four broken releases died on, and its heaviest consumers
    "canopy_constants", "settings", "frontend.dashboard_manager",
    "frontend.components.candidate_metrics_panel", "backend.service_backend",
    "communication.websocket_manager", "logger.logger",
    # the rest of the ship set
    "audit_log", "config_manager", "csrf", "dataset_import", "dataset_schema",
    "demo_mode", "discovery", "health", "main", "middleware", "model_registry",
    "observability", "provenance", "secrets_util", "security", "validation_gate",
    "ws_security",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--wheel", required=True)
    ap.add_argument("--venv", default="/tmp/canopy-smoke")
    ap.add_argument("--python", default="/usr/bin/python3")
    ap.add_argument("--reuse", action="store_true", help="skip venv creation + install")
    args = ap.parse_args()

    venv = Path(args.venv)
    py = venv / "bin" / "python"
    if not args.reuse:
        shutil.rmtree(venv, ignore_errors=True)
        subprocess.run([args.python, "-m", "venv", str(venv)], check=True)
        r = subprocess.run([str(venv / "bin" / "pip"), "install", "--quiet", args.wheel],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print("pip install FAILED:", file=sys.stderr)
            print(r.stderr[-2000:], file=sys.stderr)
            return 2
    sandbox = tempfile.mkdtemp(prefix="canopy-import-cwd-")
    print(f"venv: {venv}\nwheel: {Path(args.wheel).name}\ncwd:  {sandbox}\n")

    ok, missing, errored, optional = [], [], [], []
    for mod in CANDIDATES:
        # A WRITABLE temp dir, not "/". Nothing can resolve out of a source tree either way,
        # but canopy's logger creates its log directory relative to cwd at import time, so
        # running from "/" turns an ordinary side effect into a PermissionError and makes two
        # perfectly importable modules look broken.
        r = subprocess.run([str(py), "-c", f"import {mod}"], cwd=sandbox, capture_output=True, text=True)
        if r.returncode == 0:
            ok.append(mod)
            print(f"  [OK]      {mod}")
            continue
        m = re.search(r"ModuleNotFoundError: No module named '([^']+)'", r.stderr)
        # A ModuleNotFoundError naming the module itself (or a canopy sibling) is the
        # packaging defect. One naming a third-party package is a missing dependency;
        # one raising anything else is an import-time side effect.
        root = m.group(1).split(".")[0] if m else ""
        if m and root in OPTIONAL_EXTRA_DEPS:
            optional.append((mod, root))
            print(f"  [EXTRA]   {mod:45s} needs {root!r} from an optional extra")
        elif m and (root in CANDIDATES or root.startswith(("juniper_canopy", "canopy_"))):
            missing.append((mod, m.group(1)))
            print(f"  [MISSING] {mod:45s} no module named {m.group(1)!r} -- PACKAGING DEFECT")
        elif m:
            optional.append((mod, root))
            print(f"  [DEP]     {mod:45s} needs third-party {root!r} (not installed here)")
        else:
            tail = (r.stderr.strip().splitlines() or [""])[-1]
            errored.append((mod, tail))
            print(f"  [ERROR]   {mod:45s} {tail[:80]}")

    print(f"\n{len(ok)} ok / {len(missing)} packaging-defect / {len(optional)} needs-a-dep / "
          f"{len(errored)} error-on-import")
    if optional:
        print("\nNeeds an optional extra or an uninstalled dep -- correctly absent from a bare")
        print("install, so EXCLUDE from the publish guard:")
        for mod, dep in optional:
            print(f"  {mod}: {dep}")
    if errored:
        print("\nEXCLUDE from the publish guard (import-time side effects, not packaging):")
        for mod, tail in errored:
            print(f"  {mod}: {tail[:110]}")
    if missing:
        print("\nPACKAGING DEFECT:", file=sys.stderr)
        for mod, name in missing:
            print(f"  {mod} -> {name}", file=sys.stderr)
        return 1
    print("\nGuard list (every candidate that a clean install imports):")
    print("  " + " ".join(ok))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
