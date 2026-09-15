#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : release verification -- juniper-canopy packaging
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Can anything in a published juniper-canopy wheel actually be imported?

A member listing proves a file is absent; it does not prove the absence BITES. This
extracts the wheel to an empty directory, puts ONLY that directory on the path, and runs
each import in a fresh interpreter -- so nothing resolves through the repo checkout, which
is what makes the same import succeed locally and fail for an installer.

``frontend/dashboard_manager.py`` opens with
``from canopy_constants import CascorPatchBounds, DashboardConstants, TrainingConstants``
and no wheel ships ``canopy_constants.py``. This measures whether that is fatal.

Third-party dependencies are deliberately NOT installed: a `ModuleNotFoundError` naming
`dash` is expected and is reported as SKIP, while one naming a canopy module is the finding.
Distinguishing them is the whole point -- an "it does not import" verdict that cannot say
WHICH module is missing answers an adjacent question.

Usage:
  python util/ad-hoc/2026-09-15_canopy_wheel_import_probe.py --version 0.8.0
  python util/ad-hoc/2026-09-15_canopy_wheel_import_probe.py --version 0.7.0   # is it new?
"""

import argparse
import io
import json
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

PYPI = "https://pypi.org/pypi/{pkg}/{ver}/json"
# Everything the wheel declares as a runtime dependency; a failure naming one of these is
# the probe's own missing environment, not a packaging defect.
THIRD_PARTY = re.compile(
    r"^(dash|dash_bootstrap_components|fastapi|uvicorn|plotly|numpy|scipy|yaml|pydantic|"
    r"pydantic_settings|websockets|nest_asyncio|requests|httpx|a2wsgi|colorama|networkx|"
    r"psutil|multipart|prometheus_client|juniper_observability|juniper_service_core|"
    r"juniper_cascor_protocol|juniper_data_client|juniper_cascor_client|sentry_sdk|torch)$"
)

IMPORTS = [
    "import juniper_canopy; print(juniper_canopy.__version__)",
    "import canopy_constants",
    "import frontend",
    "import frontend.dashboard_manager",
    "import backend",
    "import logger.logger",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--package", default="juniper-canopy")
    ap.add_argument("--version", default="0.8.0")
    ap.add_argument("--python", default=sys.executable)
    args = ap.parse_args()

    with urllib.request.urlopen(PYPI.format(pkg=args.package, ver=args.version), timeout=60) as r:  # noqa: S310
        meta = json.load(r)
    url = next(u["url"] for u in meta["urls"] if u["packagetype"] == "bdist_wheel")
    with urllib.request.urlopen(url, timeout=180) as r:  # noqa: S310
        blob = r.read()

    root = Path(tempfile.mkdtemp(prefix=f"{args.package}-{args.version}-"))
    zipfile.ZipFile(io.BytesIO(blob)).extractall(root)
    print(f"{args.package} {args.version} extracted to {root}")

    env = {"PATH": "/usr/bin:/bin", "PYTHONPATH": str(root), "HOME": str(Path.home())}
    verdicts = []
    for stmt in IMPORTS:
        r = subprocess.run([args.python, "-c", stmt], capture_output=True, text=True, env=env)
        if r.returncode == 0:
            print(f"  [OK]      {stmt:42s} {r.stdout.strip()}")
            verdicts.append(("ok", stmt, ""))
            continue
        m = re.search(r"ModuleNotFoundError: No module named '([^']+)'", r.stderr)
        missing = m.group(1) if m else ""
        root_mod = missing.split(".")[0]
        if missing and THIRD_PARTY.match(root_mod):
            print(f"  [SKIP]    {stmt:42s} needs third-party {missing!r} (probe env, not a defect)")
            verdicts.append(("skip", stmt, missing))
        elif missing:
            print(f"  [MISSING] {stmt:42s} no module named {missing!r} -- SHIPPED BY NO WHEEL MEMBER")
            verdicts.append(("missing", stmt, missing))
        else:
            tail = (r.stderr.strip().splitlines() or [""])[-1]
            print(f"  [ERROR]   {stmt:42s} {tail[:90]}")
            verdicts.append(("error", stmt, tail))

    missing = [v for v in verdicts if v[0] == "missing"]
    print(f"\n{sum(1 for v in verdicts if v[0]=='ok')} ok / {len(missing)} missing-canopy-module / "
          f"{sum(1 for v in verdicts if v[0]=='skip')} skipped-on-deps / "
          f"{sum(1 for v in verdicts if v[0]=='error')} other")
    if missing:
        print("\nPACKAGING DEFECT -- a canopy module the wheel does not ship:", file=sys.stderr)
        for _, stmt, name in missing:
            print(f"  {stmt}  ->  {name}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
