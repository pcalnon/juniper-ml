"""
Flood-4 validation: independently re-derive whether setuptools ships an UNDECLARED py.typed.

Builds every in-repo sub-package three ways in a temp copy (under TMPDIR, never the system temp dir): as committed,
with the WHOLE [tool.setuptools.package-data] table deleted (not just its entry emptied), and with the
table deleted AND include-package-data forced false. Each build runs in its own interpreter
(setuptools keeps state on the process). Prints whether <import>/py.typed is in each wheel and the
setuptools version that built it. Writes nothing in the repository.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2410 negative control; tests/test_subpackage_py_typed.py
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parents[2]
SUBS = ["juniper-ci-tools", "juniper-config-tools", "juniper-doc-tools", "juniper-model-core", "juniper-observability", "juniper-service-core"]
BUILD = r"""
import contextlib, io, json, os, sys, zipfile
from pathlib import Path
import setuptools, setuptools.build_meta as bm
project, out_dir, out = (Path(a) for a in sys.argv[1:4])
os.chdir(project)
with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    name = bm.build_wheel(str(out_dir))
with zipfile.ZipFile(out_dir / name) as z:
    names = z.namelist()
Path(out).write_text(json.dumps({"setuptools": setuptools.__version__, "names": names}))
"""


def import_name(project: Path) -> str:
    with open(project / "pyproject.toml", "rb") as fh:
        return next(iter(tomllib.load(fh)["tool"]["setuptools"]["package-data"]))


def build(project: Path, mode: str) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix=f"val-py-typed-{project.name}-") as tmp:
        copy = Path(tmp) / "p"
        shutil.copytree(project, copy, ignore=shutil.ignore_patterns("build", "dist", "*.egg-info", "__pycache__"))
        pp = copy / "pyproject.toml"
        text = pp.read_text()
        if mode in ("no-table", "no-table-no-include"):
            new = re.sub(r"(?ms)^\[tool\.setuptools\.package-data\]\n(?:[^\[\n].*\n|\n)*", "", text)
            if new == text:
                raise SystemExit(f"{project.name}: package-data table not found")
            text = new
        if mode == "no-table-no-include":
            if re.search(r"(?m)^include-package-data\s*=", text):
                text = re.sub(r"(?m)^include-package-data\s*=.*$", "include-package-data = false", text)
            else:
                text = text.replace("[tool.setuptools]\n", "[tool.setuptools]\ninclude-package-data = false\n", 1)
        pp.write_text(text)
        data = tomllib.loads(text)
        has_table = "package-data" in data.get("tool", {}).get("setuptools", {})
        outd = Path(tmp) / "dist"
        outd.mkdir()
        res = Path(tmp) / "r.json"
        proc = subprocess.run([sys.executable, "-c", BUILD, str(copy), str(outd), str(res)], capture_output=True, text=True, timeout=120)
        if proc.returncode != 0:
            return {"mode": mode, "error": proc.stderr[-400:]}
        payload = json.loads(res.read_text())
        return {"mode": mode, "package_data_table_present": has_table, "include_package_data": data.get("tool", {}).get("setuptools", {}).get("include-package-data"), "setuptools": payload["setuptools"], "marker_in_wheel": None, "names": payload["names"]}


def main() -> int:
    rows = []
    for sub in SUBS:
        p = HERE / sub
        imp = import_name(p)
        src_marker = (p / imp / "py.typed").is_file() or (p / "src" / imp / "py.typed").is_file()
        for mode in ("as-committed", "no-table", "no-table-no-include"):
            r = build(p, mode)
            if "names" in r:
                names = r.pop("names")
                r["marker_in_wheel"] = f"{imp}/py.typed" in names
            r.update({"sub": sub, "import": imp, "marker_in_source": src_marker})
            rows.append(r)
            print(json.dumps(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
