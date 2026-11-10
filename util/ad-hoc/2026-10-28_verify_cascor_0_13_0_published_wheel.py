#!/usr/bin/env python3
"""
Probe the PUBLISHED juniper-cascor wheel for juniper-cascor#731: the final evaluation computes ``accuracy``.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-28
Status: ad-hoc — one-off (post-publication check of juniper-cascor 0.13.0)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/releases/RELEASE_NOTES_juniper-cascor_v0.13.0.md (the release this checks);
         notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (v1.15.7 records this probe);
         util/ad-hoc/2026-10-27_verify_recurrence_client_0_3_1_published_wheel.py (the pattern this follows)

Why this exists
---------------
juniper-cascor#731 (``752a797f``) added ``compute_classification_accuracy`` to
``api/lifecycle/classification_metrics.py`` and made the final evaluation in ``api/lifecycle/manager.py``
(``_compute_final_eval_metrics``) call it, so a cascor run's final block carries ``accuracy``. That is the
producer of register row APD-ML-002's ``test_accuracy``, which juniper-ml#2381 carries into ``stats.json``.
A checkout is not a deployment, so this reads the wheel PyPI serves and never a git tree.

It reads the wheel statically: it downloads it into memory, checks its sha256 against PyPI's JSON, and
parses the two modules with ``ast``. Nothing is installed, imported or written to disk. Importing cascor
needs torch, and an import probe is a separate check. The wheel ships the package tree twice, at the top
level (``api/...``) and under ``src/`` (``src/api/...``), and 0.12.0's does too, so each check runs on
both copies:

1. ``api/lifecycle/classification_metrics.py`` defines ``compute_classification_accuracy`` at module level;
2. ``api/lifecycle/manager.py`` calls it inside ``_compute_final_eval_metrics`` (the innermost enclosing
   function of the call, by name or attribute).

The 0.12.0 run is the control: it must FAIL both checks, because #731 merged after 0.12.0 was cut.

    python3 -I util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py --version 0.13.0   # passes
    python3 -I util/ad-hoc/2026-10-28_verify_cascor_0_13_0_published_wheel.py --version 0.12.0   # the control: fails

Exit status: 0 when every check passes, 1 when any check fails, and 2 on anything else: the wheel cannot be
fetched, PyPI lists other than one wheel, the download's sha256 differs from PyPI's, or an unexpected error
(a malformed JSON or zip, a module that does not parse). So 1 always means a check ran and failed.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import sys
import urllib.request
import zipfile

PYPI_JSON = "https://pypi.org/pypi/juniper-cascor/{version}/json"
FUNCTION = "compute_classification_accuracy"
FINAL_EVAL = "_compute_final_eval_metrics"
METRICS_MODULE = "api/lifecycle/classification_metrics.py"
MANAGER_MODULE = "api/lifecycle/manager.py"
TREE_PREFIXES = ("", "src/")


def fetch_wheel(version: str) -> tuple[str, bytes]:
    """Return the wheel's filename and bytes, after checking its sha256 against PyPI's JSON."""
    try:
        with urllib.request.urlopen(PYPI_JSON.format(version=version), timeout=30) as resp:  # nosec B310 - fixed https URL
            meta = json.load(resp)
    except Exception as exc:  # noqa: BLE001 - any fetch failure is a provenance refusal
        print(f"REFUSED: cannot read PyPI's JSON for juniper-cascor {version}: {exc}")
        sys.exit(2)
    wheels = [u for u in meta["urls"] if u["filename"].endswith(".whl")]
    if len(wheels) != 1:
        print(f"REFUSED: PyPI lists {len(wheels)} wheels for juniper-cascor {version}, expected 1")
        sys.exit(2)
    wheel = wheels[0]
    try:
        with urllib.request.urlopen(wheel["url"], timeout=120) as resp:  # nosec B310 - an https URL from PyPI's JSON
            data = resp.read()
    except Exception as exc:  # noqa: BLE001 - a failed download must not exit 1, the control's failing status
        print(f"REFUSED: cannot download {wheel['filename']}: {exc}")
        sys.exit(2)
    digest = hashlib.sha256(data).hexdigest()
    if digest != wheel["digests"]["sha256"]:
        print(f"REFUSED: {wheel['filename']} downloaded with sha256 {digest}, PyPI says {wheel['digests']['sha256']}")
        sys.exit(2)
    print(f"wheel: {wheel['filename']} ({len(data)} bytes; sha256 {digest} = PyPI's; uploaded {wheel['upload_time_iso_8601']})")
    return wheel["filename"], data


def module_level_defs(source: str) -> list[int]:
    """Return the lines where FUNCTION is defined at module level."""
    return [node.lineno for node in ast.parse(source).body if isinstance(node, ast.FunctionDef) and node.name == FUNCTION]


def calls_by_enclosing_function(source: str) -> list[tuple[int, str]]:
    """Return (line, innermost enclosing function) for every call of FUNCTION, by name or attribute."""
    innermost: dict[int, str] = {}
    # ast.walk is breadth-first, so an inner function is visited after its outer one and overwrites it.
    for func in ast.walk(ast.parse(source)):
        if not isinstance(func, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for node in ast.walk(func):
            if not isinstance(node, ast.Call):
                continue
            target = node.func
            name = target.id if isinstance(target, ast.Name) else target.attr if isinstance(target, ast.Attribute) else None
            if name == FUNCTION:
                innermost[node.lineno] = func.name
    return sorted(innermost.items())


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--version", required=True, help="the juniper-cascor version whose PyPI wheel to read, e.g. 0.13.0")
    args = ap.parse_args()

    _, data = fetch_wheel(args.version)
    failures = 0
    with zipfile.ZipFile(io.BytesIO(data)) as wheel:
        names = set(wheel.namelist())
        for prefix in TREE_PREFIXES:
            metrics, manager = prefix + METRICS_MODULE, prefix + MANAGER_MODULE
            for member in (metrics, manager):
                if member not in names:
                    print(f"FAIL: {member} is not in the wheel")
                    failures += 1
            if metrics in names:
                defs = module_level_defs(wheel.read(metrics).decode("utf-8"))
                if defs:
                    print(f"PASS: {metrics} defines {FUNCTION} (line {', '.join(map(str, defs))})")
                else:
                    print(f"FAIL: {metrics} does not define {FUNCTION} at module level")
                    failures += 1
            if manager in names:
                calls = calls_by_enclosing_function(wheel.read(manager).decode("utf-8"))
                in_final = [line for line, func in calls if func == FINAL_EVAL]
                if in_final:
                    print(f"PASS: {manager} calls {FUNCTION} in {FINAL_EVAL} (line {', '.join(map(str, in_final))})")
                else:
                    print(f"FAIL: {manager} does not call {FUNCTION} in {FINAL_EVAL} (calls found: {calls or 'none'})")
                    failures += 1
    print(f"{'PASS' if not failures else 'FAIL'}: juniper-cascor {args.version}, {failures} failed check(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    try:
        status = main()
    except Exception as exc:  # noqa: BLE001 - an unexpected error must not exit 1, which means a failed check
        print(f"ERROR: {type(exc).__name__}: {exc}")
        status = 2
    raise SystemExit(status)
