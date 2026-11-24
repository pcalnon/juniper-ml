#!/usr/bin/env python3
"""
One-line mutants of the code juniper-data's newly selected tests pin: each must fail at least one of them.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4: the Overtoad's ruling of 2026-11-12 on juniper-data's unrun tests)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (non-vacuity of the tests the change hands to a CI lane)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#529 (the precedent)

Usage:
    python3 <this> --python <venv interpreter> --out <dir> --mode new-tests --tree <the changed juniper-data tree>
    python3 <this> --python <venv interpreter> --out <dir> --mode main-lane --tree <a clean tree of main> [--only M1 ...]
    python3 <this> --python <venv interpreter> --out <dir> --mode main-integration-lane --tree <a clean tree of main>

MODES
    new-tests  In the changed tree, apply each mutant alone and run the tests the change newly hands to a lane for that
               test file (by node id, no ``-m``). ``killed`` means at least one of them fails.
    main-lane  In a clean tree of main, apply each mutant alone and run CI's unit lane as main selects it
               (``-m "unit and not slow" juniper_data/tests/unit``, no coverage, ``--maxfail=1``). ``caught`` means some
               test main already ran fails; ``not caught`` means the lane passes with the break in place. Several trees
               may be given: the mutants are dealt out to them and at most four run at once.
    main-integration-lane
               The same in a clean tree of main with CI's integration lane as main selects it
               (``-m "integration and not slow" juniper_data/tests/integration``, ``--maxfail=1``).

Each mutant replaces exactly one line, named by number, after checking that the line still reads as recorded. The
original bytes go back in a ``finally:`` block, and the file's sha256 is compared with its value before the mutant
after EVERY run; a mismatch stops the script. Compiled caches of the mutated module are deleted first (a stale .pyc
can hide a same-size edit), and no run writes bytecode. The six Sentry DSN variables are set to "", three token
variables are removed, and TMPDIR is left as the session gave it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess  # nosec B404 - fixed argv: a chosen interpreter running pytest
import sys
import xml.etree.ElementTree as ET  # nosec B405 - parses JUnit files this script's own pytest runs just wrote
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
DROPPED_TOKEN_NAMES = ("HF_TOKEN", "JUNIPER_ML_PYPI", "JUNIPER_ML_TEST_PYPI")
SUMMARY_RE = re.compile(r"^=*\s*(\d+ (?:passed|failed|errors?|skipped|deselected)\b.*? in [0-9.]+s.*?)\s*=*$")
UNIT = "juniper_data/tests/unit/"
MUTANTS: list[dict] = [
    {
        "id": "M1",
        "test_file": UNIT + "test_phase1d_security.py",
        "nodes": [UNIT + "test_phase1d_security.py"],
        "target": "juniper_data/api/app.py",
        "line": 191,
        "old": "            MetricsAuthMiddleware(get_prometheus_app(), settings.metrics_trusted_ips),\n",
        "new": "            get_prometheus_app(),\n",
        "what": "the /metrics mount loses its trusted-IP wrapper (SEC-16): any client can scrape",
    },
    {
        "id": "M2",
        "test_file": UNIT + "test_local_fs_path_traversal.py",
        "nodes": [UNIT + "test_local_fs_path_traversal.py"],
        "target": "juniper_data/storage/local_fs.py",
        "line": 54,
        "old": '    if ".." in dataset_id:\n',
        "new": '    if "..." in dataset_id:\n',
        "what": "_validate_dataset_id stops refusing a parent reference inside an id (JD-SEC-01)",
    },
    {
        "id": "M3",
        "test_file": UNIT + "test_metadata_cache.py",
        "nodes": [UNIT + "test_metadata_cache.py::TestCacheAgainstRealStores"],
        "target": "juniper_data/storage/local_fs.py",
        "line": 249,
        "old": "        self._invalidate_metadata_cache()\n",
        "new": "        pass\n",
        "what": "LocalFSDatasetStore.save stops invalidating the metadata cache (read-your-writes, JD-PERF-02)",
    },
    {
        "id": "M4",
        "test_file": UNIT + "test_api_app.py",
        "nodes": [UNIT + "test_api_app.py::TestErrorSurfaceContract"],
        "target": "juniper_data/api/app.py",
        "line": 194,
        "old": "    @app.exception_handler(RequestValidationError)\n",
        "new": "    # mutant: the handler below is defined and never registered\n",
        "what": "the app stops owning the RequestValidationError handler (APD-DATA-013): FastAPI's default answers",
    },
    {
        "id": "M5",
        "test_file": UNIT + "test_r2_1_2_wire_compat.py",
        "nodes": [UNIT + "test_r2_1_2_wire_compat.py"],
        "target": "juniper_data/api/routes/health.py",
        "line": 239,
        "old": '        dependencies={"storage": storage_dep},\n',
        "new": '        dependencies={"store": storage_dep},\n',
        "what": "/v1/health/ready renames its one dependency key (the R2.1.2 wire snapshot)",
    },
    {
        "id": "M6",
        "test_file": "juniper_data/tests/integration/test_security_integration.py",
        "nodes": ["juniper_data/tests/integration/test_security_integration.py"],
        "target": "juniper_data/api/middleware.py",
        "line": 246,
        "old": "        return path in EXEMPT_PATHS\n",
        "new": "        return False\n",
        "what": "SecurityMiddleware exempts no path: health probes need a key and spend rate-limit budget",
    },
    {
        "id": "M7",
        "test_file": UNIT + "test_batch_operations.py",
        "nodes": [UNIT + "test_batch_operations.py"],
        "target": "juniper_data/api/routes/datasets.py",
        "line": 705,
        "old": "        response.status_code = status.HTTP_200_OK\n",
        "new": "        response.status_code = status.HTTP_201_CREATED\n",
        "what": "batch-create answers 201 Created when it created nothing (APD-DATA-009 reverted)",
    },
]


def _env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in DROPPED_TOKEN_NAMES}
    env.update({"PYTHONDONTWRITEBYTECODE": "1", **dict.fromkeys(SENTRY_DSN_NAMES, "")})
    return env


def _sha(path: Path) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def _summary(text: str) -> str:
    hits = [m.group(1) for ln in text.splitlines() if (m := SUMMARY_RE.match(ln.strip()))]
    return hits[-1] if hits else "<no summary line>"


def _not_passed(junit: Path) -> list[str]:
    if not junit.is_file():
        return []
    bad = []
    for case in ET.parse(junit).getroot().iter("testcase"):  # nosec B314
        if {child.tag for child in case} & {"failure", "error"}:
            bad.append(f"{(case.get('classname') or '').rsplit('.', 1)[-1]}::{case.get('name')}")
    return bad


def _one(mutant: dict, wt: Path, python: str, out: Path, mode: str) -> dict:
    target = wt / mutant["target"]
    with open(target, "rb") as fh:
        original = fh.read()
    before = hashlib.sha256(original).hexdigest()
    lines = original.decode("utf-8").splitlines(keepends=True)
    index = mutant["line"] - 1
    record: dict = {k: mutant[k] for k in ("id", "test_file", "target", "line", "what")}
    record.update({"mutant": f"{mutant['target']}:{mutant['line']}: {mutant['old'].strip()!r} -> {mutant['new'].strip()!r}", "tree": str(wt), "mode": mode, "sha256_before": before})
    if lines[index] != mutant["old"]:
        record.update({"result": "not-applied", "reason": f"line {mutant['line']} reads {lines[index]!r}"})
        return record
    stale = sorted(target.parent.glob(f"__pycache__/{target.stem}.*.pyc"))
    for pyc in stale:
        pyc.unlink()
    record["stale_pyc_deleted"] = len(stale)
    lines[index] = mutant["new"]
    junit = out / f"{mode}_{mutant['id']}.xml"
    log = out / f"{mode}_{mutant['id']}.log"
    if mode == "new-tests":
        argv = [python, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-rA", f"--junitxml={junit}", *mutant["nodes"]]
    elif mode == "main-lane":
        argv = [python, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-m", "unit and not slow", "juniper_data/tests/unit", "--timeout=60", "--maxfail=1", f"--junitxml={junit}"]
    else:
        argv = [python, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-m", "integration and not slow", "juniper_data/tests/integration", "--timeout=120", "--maxfail=1", f"--junitxml={junit}"]
    try:
        with open(target, "wb") as fh:
            fh.write("".join(lines).encode("utf-8"))
        record["sha256_mutated"] = _sha(target)
        proc = subprocess.run(argv, cwd=wt, env=_env(), capture_output=True, text=True, check=False, timeout=3000)  # nosec B603
    finally:
        with open(target, "wb") as fh:
            fh.write(original)
    after = _sha(target)
    with open(log, "w", encoding="utf-8") as fh:
        fh.write(f"$ (cwd={wt}) {' '.join(argv)}\n# exit={proc.returncode}\n\n{proc.stdout}\n--- stderr ---\n{proc.stderr}")
    failed = _not_passed(junit)
    record.update({"argv": argv, "exit": proc.returncode, "summary": _summary(proc.stdout), "failed_tests": failed[:25], "failed_count": len(failed), "log": str(log), "sha256_after": after, "restored_byte_for_byte": after == before})
    if mode == "new-tests":
        record["result"] = "killed" if proc.returncode == 1 and failed else "survived" if proc.returncode == 0 else "inconclusive"
    else:
        lane = "unit" if mode == "main-lane" else "integration"
        record["result"] = f"caught by main's {lane} lane" if proc.returncode == 1 and failed else f"not caught by main's {lane} lane" if proc.returncode == 0 else "inconclusive"
    if after != before:
        raise SystemExit(f"{target} was not restored after {mutant['id']}: {after} != {before}")
    return record


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--python", required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--mode", required=True, choices=["new-tests", "main-lane", "main-integration-lane"])
    ap.add_argument("--tree", action="append", required=True, type=Path)
    ap.add_argument("--only", nargs="*", default=[])
    args = ap.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    trees = [t.resolve() for t in args.tree]
    chosen = [m for m in MUTANTS if not args.only or m["id"] in args.only]
    if args.mode == "new-tests" and len(trees) != 1:
        ap.error("new-tests takes exactly one --tree")
    # One queue per tree: two mutants never sit in the same tree at once, and two of them edit the same file.
    queues: list[list[dict]] = [chosen[i :: len(trees)] for i in range(len(trees))]

    def drain(pair: tuple[Path, list[dict]]) -> list[dict]:
        return [_one(m, pair[0], args.python, out, args.mode) for m in pair[1]]

    with ThreadPoolExecutor(max_workers=min(4, len(trees))) as pool:
        records = [r for batch in pool.map(drain, zip(trees, queues)) for r in batch]
    records.sort(key=lambda r: r["id"])
    dest = out / f"mutants_{args.mode}.json"
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump({"mode": args.mode, "python": args.python, "sentry_dsn_names_set_to_empty": list(SENTRY_DSN_NAMES), "token_names_removed": list(DROPPED_TOKEN_NAMES), "mutants": records}, fh, indent=1)
        fh.write("\n")
    for r in records:
        print(json.dumps({k: r.get(k) for k in ("id", "mutant", "result", "exit", "summary", "failed_count", "failed_tests", "restored_byte_for_byte", "stale_pyc_deleted", "reason") if k in r})[:900])
    print(f"wrote {dest}")
    want = "killed" if args.mode == "new-tests" else None
    ok = all(r.get("restored_byte_for_byte") for r in records) and (want is None or all(r["result"] == want for r in records))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
