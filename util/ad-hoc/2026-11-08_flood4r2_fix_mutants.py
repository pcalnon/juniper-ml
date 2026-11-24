#!/usr/bin/env python3
"""
Run a carrier's changed test files, then one-line mutants of the code they pin, restoring every file byte for byte.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 round 2: verifying the validators' fixes on the carriers)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt rule 12; adapted from 2026-11-08_flood4r2_val_canopy-tests_mutants.py and
         2026-11-08_flood4r2_val_data_mutants.py

Usage:
  2026-11-08_flood4r2_fix_mutants.py <spec.json> <out dir>

spec.json:
  {"repo": "canopy" | "data", "worktree": "<absolute path>", "label": "<carrier>",
   "tests": ["<repo-relative test file>", ...],
   "mutants": [{"id": "...", "file": "<repo-relative>", "old": "<exact text, once>", "new": "...",
                "line": <1-based line> (optional: mutate only that line, which must equal ``old``),
                "replace_with": "<absolute path whose bytes replace the file>"   (instead of old/new),
                "tests": [...] (optional; default: the top-level list),
                "must_fail": ["<substring of a test id that must be among the failures>", ...],
                "must_pass": ["<substring of a test id that must NOT be among the failures>", ...],
                "expect": "killed" | "survived"}]}

A baseline run of the top-level selection comes first and must exit 0. Each mutant then: purges the target's
__pycache__ entries, records its sha256, writes the mutant, runs the selection, restores the original bytes in a
``finally`` block, checks the sha256 again and purges again. KILLED means pytest exited 1 with failures (exit 2+ is
an ERROR, never a kill), every ``must_fail`` substring names a failed test, and no ``must_pass`` substring does.

canopy: run with the venv over JuniperCanopy1 that carries pytest 9.2.0 (tmp/flood4r2-fix/venv-canopy-py313-pytest92,
so nothing is installed into JuniperCanopy1), in ``-I -B`` mode, through 2026-11-08_flood4r2_val_canopy-tests_fenced_pytest.py:
every connect to 8050-8059, 8100 and 8200-8202 is refused and recorded, as on CI's empty runner, so no run reaches
this host's live E2E legs or the :8050 listener. CI's marker expression and its three gating variables ("0").
data: the JuniperData interpreter, ``-B``, from the worktree root, after checking ``juniper_data`` imports from it.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ADHOC = Path(__file__).resolve().parent
REPO = ADHOC.parents[1]
CANOPY_PY = str(REPO / "tmp" / "flood4r2-fix" / "venv-canopy-py313-pytest92" / "bin" / "python")
CANOPY_RUNNER = str(ADHOC / "2026-11-08_flood4r2_val_canopy-tests_fenced_pytest.py")
CANOPY_MARKERS = "not requires_cascor and not requires_server and not slow"
DATA_PY = "/opt/miniforge3/envs/JuniperData/bin/python"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _purge(path: Path) -> list[str]:
    removed = []
    cache = path.parent / "__pycache__"
    if cache.is_dir():
        for pyc in sorted(cache.glob(path.stem + ".*.pyc")):
            pyc.unlink()
            removed.append(pyc.name)
    return removed


def _failed(junit: Path) -> tuple[list[str], dict[str, int]]:
    failed: list[str] = []
    counts = {"passed": 0, "failed": 0, "skipped": 0}
    if not junit.is_file():
        return failed, counts
    for case in ET.parse(junit).getroot().iter("testcase"):
        tags = {child.tag for child in case}
        node = f"{case.get('classname')}::{case.get('name')}"
        if "failure" in tags or "error" in tags:
            failed.append(node)
            counts["failed"] += 1
        elif "skipped" in tags:
            counts["skipped"] += 1
        else:
            counts["passed"] += 1
    return sorted(failed), counts


def _run(spec: dict, out: Path, tag: str, tests: list[str]) -> dict:
    wt = Path(spec["worktree"])
    junit = out / f"junit_{tag}.xml"
    if junit.exists():
        junit.unlink()
    record: dict = {}
    if spec["repo"] == "canopy":
        fence = out / f"fence_{tag}.json"
        cmd = [CANOPY_PY, "-I", "-B", CANOPY_RUNNER, "--wt", str(wt), "--out", str(fence), "--", "-m", CANOPY_MARKERS, "--timeout=60", "-p", "no:cacheprovider", "-q", "-rA", f"--junitxml={junit}", *tests]
        # The loader reads LD_LIBRARY_PATH at process start, so it is emptied for the child (the canopy LIBTORCH collision).
        env = {**os.environ, "LD_LIBRARY_PATH": "", "LIBTORCH": ""}
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False, env=env)
        if fence.is_file():
            fenced = json.loads(fence.read_text(encoding="utf-8"))
            record = {"fence_refusals": len(fenced.get("fence_refusals", [])), "imported_outside_wt": fenced.get("imported_outside_wt"), "python": fenced.get("python")}
    else:
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
        probe = subprocess.run([DATA_PY, "-B", "-c", "import juniper_data; print(juniper_data.__file__)"], cwd=wt, capture_output=True, text=True, check=False, env=env)
        record = {"juniper_data_from": probe.stdout.strip(), "imported_inside_wt": probe.stdout.strip().startswith(str(wt) + os.sep)}
        cmd = [DATA_PY, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "-rA", "--timeout=120", f"--junitxml={junit}", *tests]
        proc = subprocess.run(cmd, cwd=wt, capture_output=True, text=True, check=False, env=env)
    log = out / f"log_{tag}.txt"
    log.write_text(f"$ (cwd={wt}) {' '.join(cmd)}\n# exit={proc.returncode}\n\n{proc.stdout}\n--- stderr ---\n{proc.stderr}", encoding="utf-8")
    failed, counts = _failed(junit)
    return {"tag": tag, "exit": proc.returncode, "counts": counts, "failed": failed, "log": str(log), **record}


def main(argv: list[str]) -> int:
    spec = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    out = Path(argv[2]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    wt = Path(spec["worktree"]).resolve()
    summary: dict = {"label": spec.get("label"), "repo": spec["repo"], "worktree": str(wt), "tests": spec["tests"], "baseline": None, "mutants": []}
    baseline = _run(spec, out, "baseline", spec["tests"])
    summary["baseline"] = baseline
    print(f"baseline: exit={baseline['exit']} {baseline['counts']}")
    ok = baseline["exit"] == 0
    for mutant in spec.get("mutants", []):
        target = wt / mutant["file"]
        original = target.read_bytes()
        before = hashlib.sha256(original).hexdigest()
        if "replace_with" in mutant:
            mutated = Path(mutant["replace_with"]).read_bytes()
            where = f"whole file <- {mutant['replace_with']}"
        elif "line" in mutant:
            # The same text stands on several lines: mutate only the named one, which must equal ``old`` exactly.
            lines = original.decode("utf-8").splitlines(keepends=True)
            index = mutant["line"] - 1
            if not 0 <= index < len(lines) or lines[index] != mutant["old"]:
                summary["mutants"].append({"id": mutant["id"], "result": "ERROR", "why": f"line {mutant['line']} is not the old text"})
                ok = False
                continue
            lines[index] = mutant["new"]
            mutated = "".join(lines).encode("utf-8")
            where = f"{mutant['file']}:{mutant['line']}"
        else:
            text = original.decode("utf-8")
            count = text.count(mutant["old"])
            if count != 1:
                summary["mutants"].append({"id": mutant["id"], "result": "ERROR", "why": f"old text occurs {count} times"})
                ok = False
                continue
            mutated = text.replace(mutant["old"], mutant["new"]).encode("utf-8")
            where = f"{mutant['file']}:{text[: text.index(mutant['old'])].count(chr(10)) + 1}"
        purged = _purge(target)
        try:
            target.write_bytes(mutated)
            run = _run(spec, out, mutant["id"], mutant.get("tests", spec["tests"]))
        finally:
            target.write_bytes(original)
            purged += _purge(target)
        after = _sha(target)
        restored = after == before
        must = mutant.get("must_fail", [])
        missing = [m for m in must if not any(m in node for node in run["failed"])]
        must_pass = mutant.get("must_pass", [])
        wrongly_failed = [m for m in must_pass if any(m in node for node in run["failed"])]
        if run["exit"] == 1 and run["failed"] and not missing and not wrongly_failed:
            verdict = "killed"
        elif run["exit"] == 0 and not missing:
            verdict = "survived"
        elif run["exit"] == 1:
            verdict = f"killed-but-not-by {missing}" if missing else f"killed-and-also-failed {wrongly_failed}"
        else:
            verdict = "ERROR"
        expect = mutant.get("expect", "killed")
        row = {
            "id": mutant["id"],
            "mutant": where + ("" if "replace_with" in mutant else f": {mutant['old'].strip()!r} -> {mutant['new'].strip()!r}"),
            "why": mutant.get("why"),
            "result": verdict,
            "expect": expect,
            "as_expected": verdict == expect,
            "exit": run["exit"],
            "counts": run["counts"],
            "failed": run["failed"],
            "must_fail": must,
            "must_pass": must_pass,
            "sha256_before": before,
            "sha256_after": after,
            "restored": restored,
            "pyc_purged": purged,
            "log": run["log"],
            **{k: v for k, v in run.items() if k in ("fence_refusals", "imported_outside_wt", "juniper_data_from", "imported_inside_wt", "python")},
        }
        summary["mutants"].append(row)
        ok &= restored and row["as_expected"]
        print(f"{mutant['id']}: {verdict} (expect {expect}) exit={run['exit']} failed={len(run['failed'])} restored={restored}")
    summary["all_as_expected_and_restored"] = ok
    (out / "mutants_summary.json").write_text(json.dumps(summary, indent=1) + "\n", encoding="utf-8")
    print(f"ok={ok} summary={out / 'mutants_summary.json'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
