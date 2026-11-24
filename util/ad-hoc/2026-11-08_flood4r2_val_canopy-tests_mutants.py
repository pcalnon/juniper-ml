"""
One-line mutants of the code juniper-canopy's flood-4 round-2 canopy-tests carrier pins (#800, #801).

Validator helper (tests/code/CI lens). The mutants are the validator's own, distinct from the builder's five.
Each one replaces a single line that must occur exactly once, purges the mutated module's bytecode (a same-size
edit inside one mtime second would otherwise run the stale .pyc), runs the carried test file plus main's
control suites through the fenced runner, then restores the file byte for byte (sha256 checked) and purges the
bytecode again. A baseline run of the same selection, unmutated, comes first.

Usage:
  python3 <this file> <canopy worktree holding the carrier's files> <out dir>

Writes <out dir>/mutants_summary.json and one junit XML + one fence JSON per run. Exit 0 when every file was
restored, 1 otherwise.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-canopy#800, #801 (flood-4 round 2), canopy-tests carrier validation
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

PYTHON = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
RUNNER = Path(__file__).resolve().parent / "2026-11-08_flood4r2_val_canopy-tests_fenced_pytest.py"
MARKERS = "not requires_cascor and not requires_server and not slow"

DRIFT = "util/check_juniper_data_generator_schemas.py"
ADAPTER = "src/backend/cascor_service_adapter.py"
DRIFT_TESTS = ["src/tests/unit/test_schema_drift_nested_equality.py", "src/tests/unit/test_check_juniper_data_generator_schemas.py"]
ADAPTER_TESTS = [
    "src/tests/unit/backend/test_apply_partition_flat_legs.py",
    "src/tests/integration/test_n5_apply_params_ux.py",
    "src/tests/unit/test_phase_c_set_params_adapter.py",
    "src/tests/unit/backend/test_cascor_service_adapter.py",
    "src/tests/unit/backend/test_cascor_service_adapter_mutations.py",
    "src/tests/unit/backend/test_cascor_service_adapter_param_mapping_regression.py",
]

MUTANTS = [
    {
        "id": "D1-list-elementwise-eq",
        "file": DRIFT,
        "old": "        return len(a) == len(b) and all(json_equal(x, y) for x, y in zip(a, b, strict=True))\n",
        "new": "        return len(a) == len(b) and all(x == y for x, y in zip(a, b, strict=True))\n",
        "why": "the list branch stops recursing but compares elements with the == operator (no identity shortcut)",
    },
    {
        "id": "D2-dict-branch-python-eq",
        "file": DRIFT,
        "old": "        return a.keys() == b.keys() and all(json_equal(a[key], b[key]) for key in a)\n",
        "new": "        return a == b\n",
        "why": "an object inside an array (anyOf's {minimum: ...}) is compared with Python's ==",
    },
    {
        "id": "D3-diff-json-asks-eq-first",
        "file": DRIFT,
        "old": "    if json_equal(fixture, upstream):\n",
        "new": "    if fixture == upstream or json_equal(fixture, upstream):\n",
        "why": "TestTheDriftReport's docstring: diff_json must not compare an array with == before asking json_equal",
    },
    {
        "id": "D4-bool-rule-dropped",
        "file": DRIFT,
        "old": "        return isinstance(a, bool) and isinstance(b, bool) and a == b\n",
        "new": "        return a == b\n",
        "why": "the scalar bool rule itself (true is not 1)",
    },
    {
        "id": "A1-last-leg-skipped-replaces",
        "file": ADAPTER,
        "old": "            skipped_detail += [d for d in leg_skipped if d not in skipped_detail]\n",
        "new": "            skipped_detail = leg_skipped\n",
        "why": "the second leg's skipped list replaces the first's instead of being unioned",
    },
    {
        "id": "A2-only-the-last-leg",
        "file": ADAPTER,
        "old": "        for leg_result in leg_results:\n",
        "new": "        for leg_result in leg_results[-1:]:\n",
        "why": "only the last leg's partition is read",
    },
    {
        "id": "A3-unwrap-returns-inner-data",
        "file": ADAPTER,
        "line": 1874,  # the same text also stands at :319 and :466; only _unwrap_control_ack's copy is mutated
        "old": "            return result if isinstance(result, dict) else {}\n",
        "new": "            return result if isinstance(result, dict) else data\n",
        "why": "a non-dict data.result unwraps to the ack's inner data dict (command, status, result)",
    },
    {
        "id": "C1-merged-dict-claim-check",
        "file": ADAPTER,
        "old": "        for leg_result in leg_results:\n",
        "new": "        for leg_result in [result_data]:\n",
        "why": "NOT a new mutant: the builder's, re-run to re-derive the CHANGELOG claim that main's mixed-apply test stays green under it",
    },
    {
        "id": "A4-unwrap-envelope-marker-loosened",
        "file": ADAPTER,
        "old": '        if isinstance(data, dict) and "command" in data:\n',
        "new": "        if isinstance(data, dict):\n",
        "why": "any dict data is treated as the command envelope (a dict whose data lacks command no longer passes through)",
    },
]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _purge_bytecode(wt: Path, rel: str) -> list[str]:
    source = wt / rel
    removed = []
    for pyc in sorted((source.parent / "__pycache__").glob(source.stem + ".*.pyc")):
        pyc.unlink()
        removed.append(str(pyc.relative_to(wt)))
    return removed


def _junit_outcomes(path: Path) -> dict:
    outcomes: dict = {}
    if not path.is_file():
        return outcomes
    for case in ET.parse(path).getroot().iter("testcase"):
        node = f"{case.get('classname')}::{case.get('name')}"
        tags = {child.tag for child in case}
        outcomes[node] = "failed" if ("failure" in tags or "error" in tags) else ("skipped" if "skipped" in tags else "passed")
    return outcomes


def _by_file(outcomes: dict, files: list[str]) -> dict:
    summary = {}
    for rel in files:
        dotted = rel[: -len(".py")].replace("/", ".")
        mine = {node: result for node, result in outcomes.items() if node.split("::")[0] == dotted or node.split("::")[0].startswith(dotted + ".")}
        failed = sorted(node for node, result in mine.items() if result == "failed")
        summary[rel] = {"passed": sum(1 for r in mine.values() if r == "passed"), "failed": len(failed), "skipped": sum(1 for r in mine.values() if r == "skipped"), "failed_ids": failed}
    return summary


def _run(wt: Path, out: Path, tag: str, tests: list[str]) -> dict:
    junit = out / f"junit_{tag}.xml"
    fence = out / f"fence_{tag}.json"
    command = [PYTHON, "-I", str(RUNNER), "--wt", str(wt), "--out", str(fence), "--", "-m", MARKERS, "--timeout=60", "-p", "no:cacheprovider", "-q", f"--junitxml={junit}", *tests]
    # The dynamic loader reads LD_LIBRARY_PATH at process start, so it is emptied HERE, for the child; emptying it
    # inside the runner is too late (a host LD_LIBRARY_PATH otherwise makes torch load a foreign libtorch_python.so).
    child_env = {**os.environ, "LD_LIBRARY_PATH": "", "LIBTORCH": ""}
    proc = subprocess.run(command, capture_output=True, text=True, check=False, env=child_env)
    (out / f"log_{tag}.txt").write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr, encoding="utf-8")
    record = json.loads(fence.read_text(encoding="utf-8")) if fence.is_file() else {}
    return {"exit": proc.returncode, "by_file": _by_file(_junit_outcomes(junit), tests), "fence_refusals": len(record.get("fence_refusals", [])), "imported_outside_wt": record.get("imported_outside_wt")}


def _mutated(text: str, mutant: dict) -> tuple[str | None, int | None, str | None]:
    """The mutated text and the 1-based line changed; with ``line``, only that line (which must equal ``old``)."""
    if "line" in mutant:
        lines = text.splitlines(keepends=True)
        index = mutant["line"] - 1
        if not 0 <= index < len(lines) or lines[index] != mutant["old"]:
            return None, None, f"line {mutant['line']} is not the old text"
        lines[index] = mutant["new"]
        return "".join(lines), mutant["line"], None
    count = text.count(mutant["old"])
    if count != 1:
        return None, None, f"old line occurs {count} times"
    return text.replace(mutant["old"], mutant["new"]), text[: text.index(mutant["old"])].count("\n") + 1, None


def main() -> int:
    wt = Path(sys.argv[1]).resolve()
    out = Path(sys.argv[2]).resolve()
    only = set(sys.argv[3].split(",")) if len(sys.argv) > 3 and sys.argv[3] else None
    extra = [arg for arg in sys.argv[4:]]  # extra test files appended to the ADAPTER selection (validator probes)
    out.mkdir(parents=True, exist_ok=True)
    summary: dict = {"worktree": str(wt), "only": sorted(only) if only else None, "extra_tests": extra, "baseline": {}, "mutants": []}
    adapter_tests = ADAPTER_TESTS + extra
    for rel in (DRIFT, ADAPTER):
        _purge_bytecode(wt, rel)
    summary["baseline"]["drift"] = _run(wt, out, "baseline_drift", DRIFT_TESTS)
    summary["baseline"]["adapter"] = _run(wt, out, "baseline_adapter", adapter_tests)
    all_restored = True
    for mutant in MUTANTS:
        if only is not None and mutant["id"].split("-")[0] not in only:
            continue
        path = wt / mutant["file"]
        original = path.read_bytes()
        before = hashlib.sha256(original).hexdigest()
        text = original.decode("utf-8")
        entry = {k: mutant[k] for k in ("id", "file", "why")}
        entry["old"], entry["new"] = mutant["old"].rstrip("\n"), mutant["new"].rstrip("\n")
        mutated, line_no, error = _mutated(text, mutant)
        if mutated is None:
            entry["error"] = error
            summary["mutants"].append(entry)
            continue
        entry["line"] = line_no
        tests = DRIFT_TESTS if mutant["file"] == DRIFT else adapter_tests
        try:
            path.write_text(mutated, encoding="utf-8")
            entry["purged_before"] = _purge_bytecode(wt, mutant["file"])
            entry["run"] = _run(wt, out, mutant["id"], tests)
        finally:
            path.write_bytes(original)
            entry["purged_after"] = _purge_bytecode(wt, mutant["file"])
            entry["restored_sha256_equal"] = _sha(path) == before
            all_restored = all_restored and entry["restored_sha256_equal"]
        target = entry["run"]["by_file"][tests[0]]
        entry["verdict"] = "killed" if target["failed"] else "survived"
        summary["mutants"].append(entry)
        print(f"{mutant['id']}: {entry['verdict']} (target failed {target['failed']}); controls failed {[(f, v['failed']) for f, v in entry['run']['by_file'].items() if f != tests[0]]}; restored={entry['restored_sha256_equal']}")
    (out / "mutants_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return 0 if all_restored else 1


if __name__ == "__main__":
    sys.exit(main())
