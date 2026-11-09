#!/usr/bin/env python3
"""
Validator's own mutation check of the juniper-data flood-4 tests carrier (mutants distinct from the builder's).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-data tests carrier VALIDATION)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#512 #513 #514 #516 #517; flood-4 validation brief (non-vacuity lens)

Runs ONLY in the validator's own juniper-data worktree (never the carrier). For each mutant: sha256 the
target, require the old text to occur exactly once, write the mutant, drop __pycache__, run the named tests
under `conda run -n JuniperData python -B -m pytest -p no:cacheprovider` with PYTHONPATH=<worktree>,
restore the original bytes and re-check the sha256. A mutant counts as KILLED only when pytest reports at
least one FAILED test (a collection error is reported as ERROR, not as a kill). "variant" rows change the
test harness instead and are expected to PASS.

    python3 2026-11-07_flood4_val_data_tests_mutants.py <validation worktree> <log dir>
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

U = "juniper_data/tests/unit/"
NEW517 = [
    U + "test_middleware.py::TestFailedAuthThrottle::test_the_entry_cap_drops_the_oldest_recorded_failures",
    U + "test_middleware.py::TestFailedAuthThrottle::test_cleanup_keeps_a_failure_until_two_windows_have_passed",
    U + "test_middleware.py::TestFailedAuthThrottle::test_a_rolled_over_window_records_the_next_failure_as_one",
]
OLD517 = [U + "test_middleware.py::TestFailedAuthThrottle"]

BASELINES = [
    ("base-512", [U + "test_bandit_sarif_upload.py", U + "test_check_module_coverage.py", U + "test_run_coverage_gates.py"]),
    ("base-513", [U + "test_publish_image_manifest_identity.py"]),
    ("base-514", [U + "test_publish_manifest_tag_gates.py"]),
    ("base-516", [U + "test_testpypi_install_verify.py"]),
    ("base-517-new", NEW517),
]

MUTANTS = [
    {
        "id": "V1-512-scan-writes-elsewhere",
        "file": ".github/workflows/ci.yml",
        "old": "-f sarif -o reports/security/bandit.sarif --exit-zero",
        "new": "-f sarif -o reports/bandit.sarif --exit-zero",
        "tests": [U + "test_bandit_sarif_upload.py"],
    },
    {
        "id": "V2-512-module-threshold-le",
        "file": "scripts/check_module_coverage.py",
        "old": "        if pct < MODULE_FAIL_UNDER:",
        "new": "        if pct <= MODULE_FAIL_UNDER:",
        "tests": [U + "test_check_module_coverage.py"],
    },
    {
        "id": "V3-512-run-coverage-drops-errexit",
        "file": "util/run_coverage.bash",
        "old": "set -euo pipefail",
        "new": "set -uo pipefail",
        "tests": [U + "test_run_coverage_gates.py"],
    },
    {
        "id": "V4-513-identity-ignores-arch-mismatch",
        "file": ".github/workflows/publish-image.yml",
        "old": '[ "$(wc -w <<< "${images}")" -ne 1 ] || [ "${image_arch}" != "${arch_file}" ]',
        "new": '[ "$(wc -w <<< "${images}")" -ne 1 ]',
        "tests": [U + "test_publish_image_manifest_identity.py"],
    },
    {
        "id": "V5-514-release-regex-unanchored",
        "file": ".github/workflows/publish-image.yml",
        "old": 'select(test(":[0-9]+\\\\.[0-9]+\\\\.[0-9]+$"))',
        "new": 'select(test(":[0-9]+\\\\.[0-9]+\\\\.[0-9]+"))',
        "tests": [U + "test_publish_manifest_tag_gates.py"],
    },
    {
        "id": "V6-514-zero-tag-guard-never-fires",
        "file": ".github/workflows/publish-image.yml",
        "old": 'if [ "${tag_count}" -eq 0 ]; then',
        "new": 'if [ "${tag_count}" -lt 0 ]; then',
        "tests": [U + "test_publish_manifest_tag_gates.py"],
    },
    {
        "id": "V7-516-pip-failure-swallowed",
        "file": ".github/workflows/publish.yml",
        "old": "juniper-data==${VERSION}\n",
        "new": "juniper-data==${VERSION} || true\n",
        "tests": [U + "test_testpypi_install_verify.py"],
    },
    {
        "id": "V8-517-rollover-keeps-old-count",
        "file": "juniper_data/api/security.py",
        "old": "                self._failures[client_ip] = (1, now)",
        "new": "                self._failures[client_ip] = (count + 1, now)",
        "tests": NEW517,
        "also_old_tests": True,
    },
    {
        "id": "V9-517-retry-after-floor-dropped",
        "file": "juniper_data/api/security.py",
        "old": "return (True, max(1, int(self._window - (now - window_start))))",
        "new": "return (True, int(self._window - (now - window_start)))",
        "tests": NEW517,
        "also_old_tests": True,
    },
    {
        "id": "V10-517-check-boundary-strict",
        "file": "juniper_data/api/security.py",
        "old": "        with self._lock:\n            count, window_start = self._failures.get(client_ip, (0, 0.0))\n            if now - window_start >= self._window:\n                return (False, 0)",
        "new": "        with self._lock:\n            count, window_start = self._failures.get(client_ip, (0, 0.0))\n            if now - window_start > self._window:\n                return (False, 0)",
        "tests": NEW517,
        "also_old_tests": True,
    },
    {
        "id": "VAR-513-harness-bash-e-only (production shell, expect PASS)",
        "file": U + "test_publish_image_manifest_identity.py",
        "old": '["bash", "-eo", "pipefail", "-c", script]',
        "new": '["bash", "-e", "-c", script]',
        "tests": [U + "test_publish_image_manifest_identity.py"],
        "variant": True,
    },
    {
        "id": "VAR-514-harness-bash-e-only (production shell, expect PASS)",
        "file": U + "test_publish_manifest_tag_gates.py",
        "old": '[bash, "-e", "-o", "pipefail", "-c", _relocate(script, tmp_path)]',
        "new": '[bash, "-e", "-c", _relocate(script, tmp_path)]',
        "tests": [U + "test_publish_manifest_tag_gates.py"],
        "variant": True,
    },
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def drop_pycache(root: Path) -> None:
    for d in list((root / "juniper_data").rglob("__pycache__")) + list((root / "scripts").rglob("__pycache__")):
        shutil.rmtree(d, ignore_errors=True)


def run_pytest(root: Path, tests: list[str], log: Path) -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(root)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = ["conda", "run", "-n", "JuniperData", "python", "-B", "-m", "pytest", "-p", "no:cacheprovider", "-rfE", *tests]
    proc = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True, check=False, timeout=900)
    text = f"$ (cwd={root}) PYTHONPATH={root} {' '.join(cmd)}\nexit={proc.returncode}\n{proc.stdout}\n{proc.stderr}"
    log.write_text(text, encoding="utf-8")
    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ""
    counts = {k: int(v) for v, k in re.findall(r"(\d+) (failed|passed|error|errors|skipped)", tail)}
    failed_ids = re.findall(r"^FAILED (\S+)", proc.stdout, flags=re.M)
    return {"exit": proc.returncode, "summary": tail, "counts": counts, "failed": failed_ids}


def main() -> int:
    root = Path(sys.argv[1]).resolve()
    logdir = Path(sys.argv[2]).resolve()
    logdir.mkdir(parents=True, exist_ok=True)
    results: dict = {"worktree": str(root), "import_origin": None, "baselines": [], "mutants": []}

    env = dict(os.environ)
    env["PYTHONPATH"] = str(root)
    probe = subprocess.run(
        ["conda", "run", "-n", "JuniperData", "python", "-c", "import juniper_data, sys; print(juniper_data.__file__); print(sys.version.split()[0]); print(sys.executable)"],
        cwd=str(logdir),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    results["import_origin"] = {"cwd": str(logdir), "PYTHONPATH": str(root), "stdout": probe.stdout.strip(), "exit": probe.returncode}
    print("import origin (cwd = log dir, PYTHONPATH = worktree):", probe.stdout.strip().replace("\n", " | "))
    if not probe.stdout.startswith(str(root)):
        print("ABORT: juniper_data does not import from the validation worktree")
        return 2

    for label, tests in BASELINES:
        drop_pycache(root)
        r = run_pytest(root, tests, logdir / f"{label}.log")
        r["label"] = label
        results["baselines"].append(r)
        print(f"{label}: exit={r['exit']} {r['summary']}")
        if r["exit"] != 0:
            print("ABORT: a baseline is red")
            return 3

    for m in MUTANTS:
        target = root / m["file"]
        before = sha(target)
        original = target.read_bytes()
        text = original.decode("utf-8")
        n = text.count(m["old"])
        row = {"id": m["id"], "file": m["file"], "old": m["old"], "new": m["new"], "occurrences": n}
        if n != 1:
            row["result"] = f"SKIPPED: old text occurs {n} times"
            results["mutants"].append(row)
            print(f"{m['id']}: {row['result']}")
            continue
        try:
            target.write_bytes(text.replace(m["old"], m["new"], 1).encode("utf-8"))
            drop_pycache(root)
            safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", m["id"])
            r = run_pytest(root, m["tests"], logdir / f"mutant_{safe}.log")
            if m.get("also_old_tests"):
                drop_pycache(root)
                r_old = run_pytest(root, [t for t in OLD517 if True], logdir / f"mutant_{safe}_wholeclass.log")
                row["whole_class"] = {"summary": r_old["summary"], "failed": r_old["failed"]}
        finally:
            target.write_bytes(original)
            drop_pycache(root)
        after = sha(target)
        row.update({"tests": m["tests"], "summary": r["summary"], "failed": r["failed"], "exit": r["exit"], "sha_before": before, "sha_after": after, "restored": before == after})
        if m.get("variant"):
            row["result"] = "PASS (as expected)" if r["exit"] == 0 else "FAIL (variant broke the file)"
        elif r["counts"].get("failed", 0) > 0:
            row["result"] = "KILLED"
        elif r["exit"] != 0:
            row["result"] = "ERROR (not a kill)"
        else:
            row["result"] = "SURVIVED"
        results["mutants"].append(row)
        extra = f" | whole TestFailedAuthThrottle: {row['whole_class']['summary']} failed={row['whole_class']['failed']}" if "whole_class" in row else ""
        print(f"{m['id']}: {row['result']} | {r['summary']} | failed={r['failed']} | restored={row['restored']}{extra}")

    (logdir / "val_mutation_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    bad = [r for r in results["mutants"] if not r.get("restored", True)]
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
