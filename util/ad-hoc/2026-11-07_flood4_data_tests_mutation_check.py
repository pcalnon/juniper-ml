#!/usr/bin/env python3
"""
Mutation-check every test file the juniper-data flood-4 tests carrier carries, and run each file alone unmutated.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-data tests carrier)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#512 #513 #514 #516 #517; flood-4 common brief rule 11;
         auto-memory reference_mutation_check_stale_pyc_and_piped_exit.md (stale pyc, rotted anchors)

For each mutant: the anchor must occur EXACTLY once (otherwise the arm is a hard error, never a skip);
sha256 of the pinned file is taken; __pycache__ beside it is removed; the one-line mutant is written; the
named tests run under `conda run -n JuniperData python -B -m pytest` with PYTHONDONTWRITEBYTECODE=1; the
original bytes are written back and the sha256 must match. A mutant is KILLED when pytest exits non-zero
and its summary line reports a failure. The last line reads `<k>/<n> mutants killed, <m> baselines green,
<e> arms errored`, and the exit status is 0 only when every arm was measured, every mutant was killed and
every baseline passed.

    python3 2026-11-07_flood4_data_tests_mutation_check.py <tests worktree> <log dir>
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

CONDA = "/opt/miniforge3/bin/conda"
T = "juniper_data/tests/unit/"
NEW_517 = [
    f"{T}test_middleware.py::TestFailedAuthThrottle::test_the_entry_cap_drops_the_oldest_recorded_failures",
    f"{T}test_middleware.py::TestFailedAuthThrottle::test_cleanup_keeps_a_failure_until_two_windows_have_passed",
    f"{T}test_middleware.py::TestFailedAuthThrottle::test_a_rolled_over_window_records_the_next_failure_as_one",
]

BASELINES = [
    ("512", [f"{T}test_bandit_sarif_upload.py", f"{T}test_check_module_coverage.py", f"{T}test_run_coverage_gates.py"]),
    ("513", [f"{T}test_publish_image_manifest_identity.py"]),
    ("514", [f"{T}test_publish_manifest_tag_gates.py"]),
    ("516", [f"{T}test_testpypi_install_verify.py"]),
    ("517", NEW_517),
]

MUTANTS = [
    {
        "id": "M1-512-bandit-continue-on-error-true",
        "test_file": f"{T}test_bandit_sarif_upload.py",
        "tests": [f"{T}test_bandit_sarif_upload.py"],
        "path": ".github/workflows/ci.yml",
        "old": "        continue-on-error: ${{ github.event_name != 'pull_request' }}\n",
        "new": "        continue-on-error: true\n",
    },
    {
        "id": "M2-512-aggregate-lt-to-le",
        "test_file": f"{T}test_check_module_coverage.py",
        "tests": [f"{T}test_check_module_coverage.py"],
        "path": "scripts/check_module_coverage.py",
        "old": "    if aggregate < AGGREGATE_FAIL_UNDER:\n",
        "new": "    if aggregate <= AGGREGATE_FAIL_UNDER:\n",
    },
    {
        "id": "M3-512-gapmap-drops-enforce",
        "test_file": f"{T}test_run_coverage_gates.py",
        "tests": [f"{T}test_run_coverage_gates.py"],
        "path": "util/run_coverage.bash",
        "old": "juniper-coverage-gap-map --coverage-json reports/coverage.json --enforce\n",
        "new": "juniper-coverage-gap-map --coverage-json reports/coverage.json\n",
    },
    {
        "id": "M4-513-index-resolution-keeps-attestations",
        "test_file": f"{T}test_publish_image_manifest_identity.py",
        "tests": [f"{T}test_publish_image_manifest_identity.py"],
        "path": ".github/workflows/publish-image.yml",
        "old": """images="$(jq -r '[.manifests[]? | select(.platform.os=="linux") | .digest] | join(" ")' <<< "${manifest_json}")\"""",
        "new": """images="$(jq -r '[.manifests[]? | .digest] | join(" ")' <<< "${manifest_json}")\"""",
    },
    {
        "id": "M5-514-arch-check-only-empty",
        "test_file": f"{T}test_publish_manifest_tag_gates.py",
        "tests": [f"{T}test_publish_manifest_tag_gates.py"],
        "path": ".github/workflows/publish-image.yml",
        "old": 'if [ "${arches}" != "amd64,arm64" ]; then',
        "new": 'if [ -z "${arches}" ]; then',
    },
    {
        "id": "M6-516-extra-index-url-pypi",
        "test_file": f"{T}test_testpypi_install_verify.py",
        "tests": [f"{T}test_testpypi_install_verify.py"],
        "path": ".github/workflows/publish.yml",
        "old": "pip install --no-deps --index-url https://test.pypi.org/simple/ juniper-data==${VERSION}",
        "new": "pip install --no-deps --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ juniper-data==${VERSION}",
    },
    {
        "id": "M7-517-cleanup-cutoff-one-window",
        "test_file": f"{T}test_middleware.py",
        "tests": NEW_517,
        "path": "juniper_data/api/security.py",
        "old": "        cutoff = now - (2 * self._window)\n",
        "new": "        cutoff = now - (1 * self._window)\n",
    },
    {
        "id": "M8-517-cap-evicts-newest",
        "test_file": f"{T}test_middleware.py",
        "tests": NEW_517,
        "path": "juniper_data/api/security.py",
        "old": "            oldest = sorted(self._failures, key=lambda ip: self._failures[ip][1])\n",
        "new": "            oldest = sorted(self._failures, key=lambda ip: self._failures[ip][1], reverse=True)\n",
    },
]

SUMMARY = re.compile(r"^=*\s*(.*\b(?:passed|failed|error|errors|no tests ran)\b.*?)\s*=*$", re.M)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clear_pycache(path: Path) -> None:
    cache = path.parent / "__pycache__"
    if cache.is_dir():
        shutil.rmtree(cache)


def pytest(root: Path, tests: list[str], log: Path) -> tuple[int, str]:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    cmd = [CONDA, "run", "--no-capture-output", "-n", "JuniperData", "python", "-B", "-m", "pytest", "-p", "no:cacheprovider", *tests]
    proc = subprocess.run(cmd, cwd=root, env=env, capture_output=True, text=True, check=False, timeout=900)
    log.write_text(f"$ (cwd={root}) {' '.join(cmd)}\nexit={proc.returncode}\n\n{proc.stdout}\n{proc.stderr}", encoding="utf-8")
    found = SUMMARY.findall(proc.stdout)
    return proc.returncode, (found[-1] if found else "<no summary line>")


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve()
    logs = Path(argv[2]).resolve()
    logs.mkdir(parents=True, exist_ok=True)
    results: dict[str, list[dict[str, object]]] = {"baselines": [], "mutations": []}
    green = errored = killed = 0
    for pr, tests in BASELINES:
        log = logs / f"baseline_{pr}.log"
        rc, summary = pytest(root, tests, log)
        ok = rc == 0 and "failed" not in summary and "passed" in summary
        green += ok
        results["baselines"].append({"pr": pr, "tests": tests, "exit": rc, "summary": summary, "result": "pass" if ok else "fail", "log": str(log)})
        print(f"BASELINE #{pr}: exit={rc} {summary}")
    for m in MUTANTS:
        target = root / str(m["path"])
        original = target.read_bytes()
        before = sha256(target)
        text = original.decode("utf-8")
        count = text.count(str(m["old"]))
        log = logs / f"mutation_{m['id']}.log"
        record: dict[str, object] = {"id": m["id"], "test_file": m["test_file"], "mutant": f"{m['path']}: {str(m['old']).strip()!r} -> {str(m['new']).strip()!r}", "log": str(log)}
        if count != 1:
            errored += 1
            record.update(result="error", detail=f"anchor matched {count} times, expected 1")
            results["mutations"].append(record)
            print(f"ERROR {m['id']}: anchor matched {count} times, expected 1")
            continue
        clear_pycache(target)
        try:
            target.write_text(text.replace(str(m["old"]), str(m["new"]), 1), encoding="utf-8")
            rc, summary = pytest(root, list(m["tests"]), log)  # type: ignore[arg-type]
        finally:
            target.write_bytes(original)
            clear_pycache(target)
        after = sha256(target)
        if after != before:
            errored += 1
            record.update(result="error", detail=f"restore mismatch {before} != {after}")
            print(f"ERROR {m['id']}: restore mismatch")
            results["mutations"].append(record)
            continue
        is_killed = rc != 0 and "failed" in summary
        killed += is_killed
        record.update(result="killed" if is_killed else "survived", exit=rc, summary=summary, sha256_before=before, sha256_after=after)
        results["mutations"].append(record)
        print(f"{'KILLED  ' if is_killed else 'SURVIVED'} {m['id']}: exit={rc} {summary} (sha256 restored {after[:12]})")
    (logs / "mutation_results.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"{killed}/{len(MUTANTS)} mutants killed, {green}/{len(BASELINES)} baselines green, {errored} arms errored")
    return 0 if (killed == len(MUTANTS) and green == len(BASELINES) and errored == 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
