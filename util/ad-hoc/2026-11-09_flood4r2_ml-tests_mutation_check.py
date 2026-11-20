"""
Mutation-check the flood-4 round-2 juniper-ml tests carrier: one-line mutants of the code each carried test file pins.

A copy of `2026-11-07_flood4_ml_tests_mutation_check.py` (round 1) with two additions:
  * `names` may be given explicitly (a carried ASSERTION inside an existing test has no `def test_*` of its own);
  * `control_root` re-runs the same mutant in a clean-main checkout against main's copy of the test file. A kill
    the carrier credits to an assertion it ADDED is shown by "killed here, survived there".
For each mutant in the JSON spec ({"pr", "test_file", "target", "old", "new"[, "names"][, "control_root"]}):
  1. the selection is `names`, or every `def test_*` the carrier adds to `test_file` (`git diff origin/main`);
  2. the selection must PASS on the real code first (baseline; pytest -k, rc 0);
  3. `old` must occur exactly once in `target`; it is replaced by `new`, stale __pycache__ next to the target and
     the test is deleted (PYTHONDONTWRITEBYTECODE=1 as well), and the selection re-runs: rc 1 = killed, rc 0 = survived;
  4. the target is restored byte-for-byte and its sha256 compared with the original (a mismatch aborts the run).
Sub-package tests (juniper-*/tests/) run with PYTHONPATH=<that sub-package>, so the checkout's code is imported and
not an installed copy. Writes `<out-dir>/mutation_results.json` and one log per mutant.

Usage: python3 util/ad-hoc/2026-11-09_flood4r2_ml-tests_mutation_check.py <spec.json> <out-dir>   (from the worktree root)

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: auto-memory reference_mutation_check_stale_pyc_and_piped_exit.md; BRIEF_COMMON_R2 rule 12
"""

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd()
_ADDED_TEST = re.compile(r"^\+\s*(?:async\s+)?def (test_[A-Za-z0-9_]+)\(", re.M)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _added_tests(test_file: str) -> list:
    diff = subprocess.run(["git", "diff", "origin/main", "--", test_file], check=True, capture_output=True, text=True).stdout
    return sorted(set(_ADDED_TEST.findall(diff)))


def _env_for(root: Path, test_file: str) -> dict:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    first = Path(test_file).parts[0]
    if first.startswith("juniper-"):
        env["PYTHONPATH"] = str(root / first) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return env


def _clear_pycache(*paths: Path) -> None:
    for p in paths:
        cache = p.parent / "__pycache__"
        if cache.is_dir():
            shutil.rmtree(cache)


def _run(root: Path, test_file: str, names: list, log: Path, label: str) -> int:
    argv = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", test_file, "-k", " or ".join(names)]
    proc = subprocess.run(argv, cwd=str(root), capture_output=True, text=True, env=_env_for(root, test_file), check=False, timeout=900)
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(f"===== {label} (cwd {root}): {' '.join(argv)}\nrc={proc.returncode}\n{proc.stdout[-6000:]}\n{proc.stderr[-3000:]}\n")
    return proc.returncode


def _mutate_and_run(root: Path, m: dict, names: list, log: Path, label: str) -> dict:
    target = root / m["target"]
    text = target.read_bytes()
    old, new = m["old"].encode(), m["new"].encode()
    if text.count(old) != 1:
        return {"error": f"old string occurs {text.count(old)} times in {target}"}
    before = _sha(target)
    try:
        target.write_bytes(text.replace(old, new, 1))
        _clear_pycache(target, root / m["test_file"])
        rc = _run(root, m["test_file"], names, log, label)
    finally:
        target.write_bytes(text)
        _clear_pycache(target, root / m["test_file"])
    after = _sha(target)
    return {"rc": rc, "sha256_before": before, "sha256_after": after, "restored": before == after}


def main() -> int:
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for k, m in enumerate(spec):
        log = out / f"mut{k:02d}_pr{m['pr']}_{Path(m['test_file']).stem}.log"
        log.write_text("", encoding="utf-8")
        names = m.get("names") or _added_tests(m["test_file"])
        row = {"pr": m["pr"], "test_file": m["test_file"], "target": m["target"], "old": m["old"], "new": m["new"], "selection": names, "log": str(log)}
        if not names:
            row["result"] = "error: no selected tests"
            results.append(row)
            continue
        _clear_pycache(ROOT / m["target"], ROOT / m["test_file"])
        row["baseline_rc"] = _run(ROOT, m["test_file"], names, log, "baseline")
        if row["baseline_rc"] != 0:
            row["result"] = "error: baseline selection does not pass"
            results.append(row)
            print(f"#{m['pr']} {m['test_file']}: {row['result']}")
            continue
        got = _mutate_and_run(ROOT, m, names, log, "mutant")
        row.update({"mutant_" + key: value for key, value in got.items()})
        if not got.get("restored", False) and "error" not in got:
            print(f"RESTORE FAILED for {m['target']}", file=sys.stderr)
            results.append(row)
            break
        rc = got.get("rc")
        row["result"] = got["error"] if "error" in got else ("killed" if rc == 1 else ("survived" if rc == 0 else f"error: mutant rc {rc}"))
        if m.get("control_root"):
            control = _mutate_and_run(Path(m["control_root"]), m, names, log, "control (main's test file)")
            row.update({"control_" + key: value for key, value in control.items()})
            crc = control.get("rc")
            row["control_result"] = control["error"] if "error" in control else ("killed" if crc == 1 else ("survived" if crc == 0 else f"error: rc {crc}"))
        results.append(row)
        print(f"#{m['pr']} {m['test_file']} [{m['target']}]: {row['result']}" + (f" (control on main's file: {row['control_result']})" if "control_result" in row else ""))
    with open(out / "mutation_results.json", "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    return 0 if all(r.get("result") == "killed" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
