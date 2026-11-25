"""
Survey the active interpreter, its test dependencies, and each sub-package's pytest and coverage configuration: the runner's design input.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc — one-off (a record of the local test runner arc)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2615

Archived on 2026-11-24 from the worktree's tmp/run-tests-design/, where it was written and run; a script does
not belong in tmp/ (AGENTS.md § Script placement). Files it names beside itself (upload-snapshot/, rehome2/,
rehome3/ and the like) stayed in that directory, which moved to the primary checkout's
tmp/run-tests-design--delegated-questing-bentley/.

Original docstring, verbatim:

Scratch: survey the active interpreter, its test deps, and each sub-package's pytest/coverage config.
"""
import importlib.util as u
import os
import shutil
import sys
import tomllib
from pathlib import Path

print("sys.executable:", sys.executable, sys.version.split()[0])
print("python on PATH:", shutil.which("python"), "| python3 on PATH:", shutil.which("python3"))
for k in ("CONDA_DEFAULT_ENV", "VIRTUAL_ENV", "TMPDIR", "GIT_CEILING_DIRECTORIES", "PYTHONPATH", "DBUS_SESSION_BUS_ADDRESS"):
    print(f"  {k}={os.environ.get(k, '')}")
print("cpu_count:", os.cpu_count())
mods = ["yaml", "packaging", "juniper_ci_tools", "numpy", "matplotlib", "h5py", "setuptools", "wheel", "cryptography",
        "pytest", "pytest_cov", "coverage", "fastapi", "httpx", "prometheus_client",
        "juniper_doc_tools", "juniper_observability", "juniper_service_core", "juniper_model_core", "juniper_config_tools"]
for m in mods:
    s = u.find_spec(m)
    print(f"  {m:24s} {'OK  ' + str(s.origin) if s else 'MISSING'}")
print("juniper-coverage-gap-map:", shutil.which("juniper-coverage-gap-map"))

for d in ["juniper-ci-tools", "juniper-config-tools", "juniper-doc-tools", "juniper-model-core", "juniper-observability", "juniper-service-core"]:
    t = tomllib.loads((Path(d) / "pyproject.toml").read_text())
    p = t.get("project", {})
    tool = t.get("tool", {})
    print(f"=== {d}")
    print("  requires-python:", p.get("requires-python"))
    print("  deps:", p.get("dependencies"))
    print("  test extra:", (p.get("optional-dependencies") or {}).get("test"))
    print("  pytest:", (tool.get("pytest") or {}).get("ini_options"))
    print("  coverage:", tool.get("coverage"))
    print("  tests/__init__.py:", (Path(d) / "tests" / "__init__.py").exists(), "| conftest:", (Path(d) / "tests" / "conftest.py").exists())
