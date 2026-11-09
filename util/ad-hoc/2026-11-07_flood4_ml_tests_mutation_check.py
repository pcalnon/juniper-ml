"""
Mutation-check the flood-4 juniper-ml tests carrier: one one-line mutant per carried test file.

For each mutant in the JSON spec ({"pr", "test_file", "target", "old", "new"}):
  1. the selection is the test functions the CARRIER adds to `test_file` (`git diff origin/main -- <file>`,
     every added `def test_*`), so a kill is credited to the carried tests, not to main's;
  2. the selection must PASS on the real code first (baseline; pytest -k, rc 0);
  3. `old` must occur exactly once in `target`; it is replaced by `new`, stale __pycache__ next to the
     target and the test is deleted, and the selection re-runs: rc 1 (tests failed) = killed, rc 0 = survived;
  4. the target is restored byte-for-byte and its sha256 compared with the original (a mismatch aborts).
Sub-package tests (juniper-*/tests/) run with PYTHONPATH=<that sub-package> so the worktree's code is
imported, never an editable install of another checkout. Writes `<out-dir>/mutation_results.json` and
one log per mutant.

Usage: python3 util/ad-hoc/2026-11-07_flood4_ml_tests_mutation_check.py <spec.json> <out-dir>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md; auto-memory reference_mutation_check_stale_pyc_and_piped_exit.md
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


def _added_tests(test_file: str) -> list[str]:
    diff = subprocess.run(["git", "diff", "origin/main", "--", test_file], check=True, capture_output=True, text=True).stdout
    if not diff:  # a new file the index does not hold yet is still a diff against main once staged
        diff = subprocess.run(["git", "diff", "--cached", "origin/main", "--", test_file], check=True, capture_output=True, text=True).stdout
    return sorted(set(_ADDED_TEST.findall(diff)))


def _env_for(test_file: str) -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    first = Path(test_file).parts[0]
    if first.startswith("juniper-"):
        env["PYTHONPATH"] = str(ROOT / first) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    return env


def _clear_pycache(*paths: Path) -> None:
    for p in paths:
        cache = p.parent / "__pycache__"
        if cache.is_dir():
            shutil.rmtree(cache)


def _run(test_file: str, names: list[str], log: Path, label: str) -> int:
    argv = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", test_file, "-k", " or ".join(names)]
    proc = subprocess.run(argv, capture_output=True, text=True, env=_env_for(test_file), check=False, timeout=900)
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(f"===== {label}: {' '.join(argv)}\nrc={proc.returncode}\n{proc.stdout[-6000:]}\n{proc.stderr[-3000:]}\n")
    return proc.returncode


def main() -> int:
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for m in spec:
        target = ROOT / m["target"]
        log = out / f"mut_pr{m['pr']}_{Path(m['test_file']).stem}.log"
        log.write_text("", encoding="utf-8")
        names = m.get("names") or _added_tests(m["test_file"])
        row = {"pr": m["pr"], "test_file": m["test_file"], "target": m["target"], "old": m["old"], "new": m["new"], "selection": names, "log": str(log)}
        if not names:
            row["result"] = "error: no added tests found"
            results.append(row)
            print(f"#{m['pr']} {m['test_file']}: {row['result']}")
            continue
        _clear_pycache(target, ROOT / m["test_file"])
        base_rc = _run(m["test_file"], names, log, "baseline")
        row["baseline_rc"] = base_rc
        text = target.read_bytes()
        old, new = m["old"].encode(), m["new"].encode()
        if base_rc != 0:
            row["result"] = "error: baseline selection does not pass"
        elif text.count(old) != 1:
            row["result"] = f"error: old string occurs {text.count(old)} times"
        else:
            before = _sha(target)
            try:
                target.write_bytes(text.replace(old, new, 1))
                _clear_pycache(target, ROOT / m["test_file"])
                mut_rc = _run(m["test_file"], names, log, "mutant")
            finally:
                target.write_bytes(text)
                _clear_pycache(target, ROOT / m["test_file"])
            after = _sha(target)
            row.update({"mutant_rc": mut_rc, "sha256_before": before, "sha256_after": after, "restored": before == after})
            if before != after:
                print(f"RESTORE FAILED for {target}", file=sys.stderr)
                results.append(row)
                break
            row["result"] = "killed" if mut_rc == 1 else ("survived" if mut_rc == 0 else f"error: mutant rc {mut_rc}")
        results.append(row)
        print(f"#{m['pr']} {m['test_file']}: {row['result']} (baseline rc {base_rc}, {len(names)} selected)")
    with open(out / "mutation_results.json", "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    return 0 if all(r.get("result") == "killed" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
