"""
CI-parity proofs for the D-14 fix-up: service-core's suite as ``CI -- juniper-service-core`` runs it (carrier and
clean main), the websockets versions the two table harnesses must run on without a deprecation warning, and a test
run from a freshly built service-core sdist.

Steps (``--step``, run in this order; each writes ``<out>/<step>.json`` and its logs):
  venvs    uv venvs under ``--venvs``: ``svc-ci`` and ``svc-main`` (CPython 3.13, ``-e juniper-model-core`` and
           ``-e "juniper-service-core/.[test]"`` from the carrier / the clean-main export, as CI installs them, plus
           juniper-ci-tools for the per-file gate), ``svc-floor`` (the same, with ``[test]``'s floors pinned:
           uvicorn 0.29.0, websockets 12.0), ``cascor-ci`` and ``cascor-floor`` (JuniperCascor1's interpreter with its
           site-packages, plus websockets 17.4 and uvicorn 0.54.0 as juniper-cascor's CI lock pins them / websockets
           12.0). Each venv's sys.version, sys.executable, sys.base_prefix and websockets / uvicorn versions are recorded.
  suite    CI's command, ``pytest juniper-service-core/tests/ -v --cov=juniper_service_core --cov-report=term-missing
           --cov-report=json:<json> --cov-fail-under=80`` from the repository root (so the root pyproject's coverage
           settings apply), then ``juniper-coverage-gap-map --coverage-json <json> --enforce``: carrier and clean main.
  versions The table test and the continuity tests in ``svc-floor``; juniper-cascor's table test in ``cascor-ci`` and
           ``cascor-floor``. Each log's "connect() must be used as a context manager" warnings are counted (and
           every DeprecationWarning line).
  sdist    ``uv build --sdist --wheel`` of a copy of juniper-service-core, with and without MANIFEST.in; the members
           of each archive; each sdist unpacked and its table test run with the venv's ``pytest`` (so the package is
           the installed sdist, not the unpacked source).

Every child run sets the six Sentry variables to "" and the session bus to a dead path. Paths outside the carriers
(venvs, exports, copies) belong in a scratch directory that is NOT a juniper-ml checkout's tmp/ (a pyproject.toml
there fails juniper-ml's tests/test_release_train_registry.py).

Usage:
    python3 util/ad-hoc/2026-11-16_flood4r2_d14_ci_parity.py --step venvs|suite|versions|sdist --ml <carrier>
        --ml-main <clean-main export root> --cascor <cascor carrier> --venvs <dir> --out <dir>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the owner's rulings of 2026-11-12 and 2026-11-13 (D-14: four cursor rules + one shared table)
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time
import zipfile
from pathlib import Path

JUNIPER_CASCOR1 = "/opt/miniforge3/envs/JuniperCascor1/bin/python3.14"
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
CONNECT_WARNING = "must be used as a context manager"
SVC_TABLE = "juniper-service-core/tests/test_websocket_resume_answer_table.py"
SVC_CONTINUITY = "juniper-service-core/tests/test_websocket_resume_continuity.py"
C_TABLE = "src/tests/unit/api/test_websocket_resume_answer_table.py"


def child_env(extra: dict | None = None) -> dict:
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}, "DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent/no-session-bus"}
    for name in ("JUNIPER_CASCOR_LOG_DIR", "GITHUB_ACTIONS", "JUNIPER_DRIFT_TEST_FORCE_LOCAL", "PYTHONPATH", "VIRTUAL_ENV"):
        env.pop(name, None)
    env.update(extra or {})
    return env


def run(argv: list, cwd: Path, log: Path, env: dict | None = None, timeout: int = 1800) -> dict:
    started = time.monotonic()
    with open(log, "w", encoding="utf-8") as handle:
        handle.write("$ " + " ".join(str(part) for part in argv) + f"\n(cwd {cwd})\n")
        handle.flush()
        code = subprocess.run([str(part) for part in argv], cwd=str(cwd), env=env or child_env(), stdout=handle, stderr=subprocess.STDOUT, timeout=timeout, check=False).returncode
    text = log.read_text(encoding="utf-8", errors="replace")
    counts = {key: int(match.group(1)) for key in ("failed", "passed", "error", "errors", "skipped", "warnings") for match in [re.search(rf"(\d+) {key}\b", text)] if match}
    total = re.search(r"TOTAL\s+\d+\s+\d+\s+\d+\s+\d+\s+([\d.]+%)", text)
    return {
        "argv": [str(part) for part in argv],
        "cwd": str(cwd),
        "exit": code,
        "seconds": round(time.monotonic() - started, 1),
        "counts": counts,
        "coverage_total": total.group(1) if total else None,
        "connect_deprecations": text.count(CONNECT_WARNING),
        "deprecation_warning_lines": len(re.findall(r"DeprecationWarning", text)),
        "log": str(log),
    }


def py(venvs: Path, name: str) -> Path:
    return venvs / name / "bin" / "python"


def describe(python: Path) -> dict:
    code = (
        "import sys, importlib.metadata as m\n"
        "print(sys.version.split()[0]); print(sys.executable); print(sys.base_prefix)\n"
        "for name in ('websockets', 'uvicorn'):\n"
        "    try:\n"
        "        print(m.version(name))\n"
        "    except m.PackageNotFoundError:\n"
        "        print('absent')\n"
    )
    lines = subprocess.run([str(python), "-c", code], capture_output=True, text=True, check=True, env=child_env()).stdout.splitlines()
    return dict(zip(("version", "executable", "base_prefix", "websockets", "uvicorn"), lines))


def step_venvs(args) -> dict:
    uv = shutil.which("uv")
    args.venvs.mkdir(parents=True, exist_ok=True)
    plans = {
        "svc-ci": (["--python", "3.13"], [f"-e{args.ml / 'juniper-model-core'}", f"-e{args.ml / 'juniper-service-core'}[test]", "juniper-ci-tools>=0.9.0,<0.10.0"]),
        "svc-main": (["--python", "3.13"], [f"-e{args.ml_main / 'juniper-model-core'}", f"-e{args.ml_main / 'juniper-service-core'}[test]", "juniper-ci-tools>=0.9.0,<0.10.0"]),
        "svc-floor": (["--python", "3.13"], [f"-e{args.ml / 'juniper-model-core'}", f"-e{args.ml / 'juniper-service-core'}[test]", "uvicorn==0.29.0", "websockets==12.0"]),
        "cascor-ci": (["--python", JUNIPER_CASCOR1, "--system-site-packages"], ["websockets==17.4", "uvicorn==0.54.0"]),
        "cascor-floor": (["--python", JUNIPER_CASCOR1, "--system-site-packages"], ["websockets==12.0"]),
    }
    result = {}
    for name, (venv_args, packages) in plans.items():
        target = args.venvs / name
        if not target.exists():
            run([uv, "venv", *venv_args, target], args.venvs, args.out / f"venv-{name}.log")
        install = run([uv, "pip", "install", "--python", py(args.venvs, name), *packages], args.venvs, args.out / f"install-{name}.log")
        result[name] = {"install_exit": install["exit"], "interpreter": describe(py(args.venvs, name)), "log": install["log"]}
    return result


def step_suite(args) -> dict:
    result = {}
    for name, root, venv in (("carrier", args.ml, "svc-ci"), ("main", args.ml_main, "svc-main")):
        coverage_json = args.out / f"coverage_{name}.json"
        env = child_env({"COVERAGE_FILE": str(args.out / f".coverage_{name}")})
        suite = run([py(args.venvs, venv), "-m", "pytest", "juniper-service-core/tests/", "-v", "--cov=juniper_service_core", "--cov-report=term-missing", f"--cov-report=json:{coverage_json}", "--cov-fail-under=80", "-p", "no:cacheprovider"], root, args.out / f"suite_{name}.log", env)
        gate = run([args.venvs / venv / "bin" / "juniper-coverage-gap-map", "--coverage-json", coverage_json, "--enforce"], root, args.out / f"gap_map_{name}.log", env)
        result[name] = {"suite": suite, "per_file_gate": {"exit": gate["exit"], "log": gate["log"]}, "interpreter": describe(py(args.venvs, venv))}
    return result


def step_versions(args) -> dict:
    env = child_env()
    return {
        "svc-ci (from the suite step's log)": "see suite.json carrier.connect_deprecations",
        "svc-floor": {"interpreter": describe(py(args.venvs, "svc-floor")), **run([py(args.venvs, "svc-floor"), "-m", "pytest", SVC_TABLE, SVC_CONTINUITY, "-p", "no:cacheprovider", "-W", "default"], args.ml, args.out / "versions_svc_floor.log", env)},
        "cascor-ci": {"interpreter": describe(py(args.venvs, "cascor-ci")), **run([py(args.venvs, "cascor-ci"), "-m", "pytest", "-m", "unit and not slow", C_TABLE, "--timeout=60", "-p", "no:cacheprovider", "-W", "default"], args.cascor, args.out / "versions_cascor_ci.log", env)},
        "cascor-floor": {"interpreter": describe(py(args.venvs, "cascor-floor")), **run([py(args.venvs, "cascor-floor"), "-m", "pytest", "-m", "unit and not slow", C_TABLE, "--timeout=60", "-p", "no:cacheprovider", "-W", "default"], args.cascor, args.out / "versions_cascor_floor.log", env)},
    }


def members(path: Path) -> list[str]:
    if path.suffix == ".whl":
        with zipfile.ZipFile(path) as archive:
            return archive.namelist()
    with tarfile.open(path) as archive:
        return archive.getnames()


def step_sdist(args) -> dict:
    uv = shutil.which("uv")
    result = {}
    ignore = shutil.ignore_patterns("__pycache__", "*.egg-info", ".pytest_cache", "build", "dist")
    for variant in ("with-manifest", "without-manifest"):
        work = args.out / f"sdist-{variant}"
        if work.exists():
            shutil.rmtree(work)
        source = work / "juniper-service-core"
        shutil.copytree(args.ml / "juniper-service-core", source, ignore=ignore)
        if variant == "without-manifest":
            (source / "MANIFEST.in").unlink()
        build = run([uv, "build", "--sdist", "--wheel", source, "-o", work / "dist"], work, work / "build.log")
        sdist = next((work / "dist").glob("*.tar.gz"))
        wheel = next((work / "dist").glob("*.whl"))
        sdist_members, wheel_members = members(sdist), members(wheel)
        with tarfile.open(sdist) as archive:
            archive.extractall(work / "unpacked", filter="data")
        unpacked = next((work / "unpacked").iterdir())
        venv = work / "venv"
        run([uv, "venv", "--python", "3.13", venv], work, work / "venv.log")
        install = run([uv, "pip", "install", "--python", venv / "bin" / "python", f"juniper-service-core[test] @ {sdist.resolve().as_uri()}", args.ml / "juniper-model-core"], work, work / "install.log")
        table = run([venv / "bin" / "pytest", "tests/test_websocket_resume_answer_table.py", "-q", "-p", "no:cacheprovider"], unpacked, work / "table_from_sdist.log")
        located = subprocess.run([str(venv / "bin" / "python"), "-c", "import juniper_service_core; print(juniper_service_core.__file__)"], cwd=str(work), capture_output=True, text=True, check=False, env=child_env()).stdout.strip()
        result[variant] = {
            "build_exit": build["exit"],
            "sdist": sdist.name,
            "sdist_fixture_members": [name for name in sdist_members if "fixtures" in name],
            "sdist_test_members": sum(1 for name in sdist_members if "/tests/" in name),
            "wheel_test_members": [name for name in wheel_members if "tests/" in name],
            "install_exit": install["exit"],
            "package_imported_from": located,
            "table_test_from_sdist": table,
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--step", choices=("venvs", "suite", "versions", "sdist"), required=True)
    parser.add_argument("--ml", type=Path, required=True)
    parser.add_argument("--ml-main", type=Path, required=True)
    parser.add_argument("--cascor", type=Path, required=True)
    parser.add_argument("--venvs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    steps = {"venvs": step_venvs, "suite": step_suite, "versions": step_versions, "sdist": step_sdist}
    result = steps[args.step](args)
    (args.out / f"{args.step}.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
