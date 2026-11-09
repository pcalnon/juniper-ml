"""
Run one-line mutants of production code against the test files that claim to pin it, restoring each file byte-for-byte.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator agent, flood-4 tests carrier, slice B)
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 carrier validation (BRIEF_VALIDATE.txt); juniper-ml tests carrier on origin/main 303ccc0b

Usage: python3 <this> --python <interpreter> --root <repo root> --spec <spec.json> --out <log dir> [--only ID[,ID...]]

spec.json is a list of {"id", "target", "old", "new", "test_file", "run" (optional list of unittest ids; default the whole
file, as ci.yml runs it), "expect" (optional list of test-method names that must be among the failures), "kind"
("mutant" -> must be killed; "probe" -> records the outcome only)}. For each entry: sha256 the target, require `old`
to occur exactly once, write the mutant, clear every __pycache__ under tests/, util/ and the six sub-packages, run,
restore the original bytes in a finally block, verify the sha256, clear __pycache__ again. Mutants run one at a time.
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
import time
from pathlib import Path

_CACHE_TOPS = ("tests", "util", "juniper-ci-tools", "juniper-config-tools", "juniper-doc-tools", "juniper-model-core", "juniper-observability", "juniper-service-core")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _clear_pycache(root: Path) -> None:
    for top in _CACHE_TOPS:
        base = root / top
        if base.is_dir():
            for cache in base.rglob("__pycache__"):
                shutil.rmtree(cache, ignore_errors=True)


def _run(python: str, root: Path, entry: dict) -> tuple[int, str, float]:
    argv = [python, "-m", "unittest", "-v"] + (entry.get("run") or [entry["test_file"]])
    started = time.monotonic()
    proc = subprocess.run(argv, cwd=root, capture_output=True, text=True, check=False)  # nosec B603 -- fixed argv
    return proc.returncode, f"$ {' '.join(argv)}\n" + proc.stdout + proc.stderr, round(time.monotonic() - started, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--only", default="")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(args.spec, encoding="utf-8") as fh:
        spec = json.load(fh)
    only = {item for item in args.only.split(",") if item}
    results = []
    for entry in spec:
        if only and entry["id"] not in only:
            continue
        target = root / entry["target"]
        original = target.read_bytes()
        before = _sha(target)
        text = original.decode("utf-8")
        count = text.count(entry["old"])
        row = {"id": entry["id"], "kind": entry.get("kind", "mutant"), "target": entry["target"], "test_file": entry["test_file"], "sha256_before": before}
        if count != 1:
            row.update(result="inapplicable", detail=f"old string occurs {count} times")
            results.append(row)
            print(f"{entry['id']}: inapplicable ({count} occurrences)")
            continue
        try:
            target.write_bytes(text.replace(entry["old"], entry["new"], 1).encode("utf-8"))
            _clear_pycache(root)
            rc, log_text, seconds = _run(args.python, root, entry)
        finally:
            target.write_bytes(original)
            _clear_pycache(root)
        after = _sha(target)
        failing = sorted({name for name, _cls in re.findall(r"^(?:FAIL|ERROR): (\S+) \(([^)]+)\)", log_text, re.MULTILINE)})
        ran = re.findall(r"^Ran (\d+) tests? in", log_text, re.MULTILINE)
        expect = entry.get("expect") or []
        missing = [name for name in expect if name not in failing]
        if row["kind"] == "probe":
            verdict = "probe"
        else:
            verdict = "killed" if rc != 0 and not missing else ("killed-other" if rc != 0 else "survived")
        log = out / f"mutant_{entry['id']}.log"
        log.write_text(f"mutant {entry['id']}: {entry['target']}\n--- old\n{entry['old']}\n--- new\n{entry['new']}\nexit {rc}, {seconds}s, sha256 before {before} after {after}\n\n{log_text}", encoding="utf-8")
        row.update(result=verdict, rc=rc, seconds=seconds, ran=int(ran[-1]) if ran else None, failing=failing, expected_missing=missing, sha256_after=after, restored=after == before, log=str(log))
        results.append(row)
        print(f"{entry['id']}: {verdict} rc={rc} {seconds}s restored={after == before} failing={failing} missing={missing}")
    summary = out / ("mutants_summary.json" if not only else f"mutants_summary_{'_'.join(sorted(only))}.json")
    summary.write_text(json.dumps(results, indent=1), encoding="utf-8")
    bad = [r for r in results if r.get("restored") is False]
    print(f"{len(results)} entries -> {summary}; restore failures: {len(bad)}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
