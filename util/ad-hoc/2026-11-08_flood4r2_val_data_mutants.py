"""
Apply one-line mutants to a juniper-data validation worktree, run named test files, record killed/survived.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round-2 carrier validation (tmp/flood4/BRIEF_VALIDATE_R2.txt); juniper-data data-tests and data-code carriers

Usage:
    python3 util/ad-hoc/2026-11-08_flood4r2_val_data_mutants.py <spec.json> <out_dir>

spec.json is a list of entries:
    {"id": "V1", "worktree": "<dir name under ~/Development/python/Juniper/worktrees>",
     "file": "<repo-relative path>",
     "old": "<exact text, must occur once>", "new": "<replacement>"      # a one-line mutant
       OR "replace_with": "<absolute path of a file whose bytes replace the target>",
     "tests": ["<repo-relative test path>", ...],
     "marker": "<optional pytest -m expression>",
     "expect": "killed" | "survived"}

Each mutant is applied, the tests run under the JuniperData interpreter with -B (no .pyc is
written, so a stale bytecode file can never mask the mutant), and the original bytes are put
back in a finally block. A mutant counts as KILLED only when pytest exits 1 (tests failed);
exit 2+ (collection error, usage error) is recorded as ERROR, never as a kill.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

PYTHON = "/opt/miniforge3/envs/JuniperData/bin/python"
WORKTREES = Path.home() / "Development" / "python" / "Juniper" / "worktrees"


def _summary(text: str) -> str:
    lines = [ln for ln in text.splitlines() if (" passed" in ln or " failed" in ln or " error" in ln or "no tests ran" in ln) and " in " in ln]
    return lines[-1].strip() if lines else "(no summary line)"


def _probe_import(worktree: Path) -> str:
    out = subprocess.run([PYTHON, "-B", "-c", "import juniper_data; print(juniper_data.__file__)"], cwd=worktree, capture_output=True, text=True, check=False)
    return out.stdout.strip()


def run(spec_path: Path, out_dir: Path) -> int:
    entries = json.loads(spec_path.read_text(encoding="utf-8"))
    out_dir.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    results = []
    for entry in entries:
        worktree = WORKTREES / entry["worktree"]
        target = worktree / entry["file"]
        imported = _probe_import(worktree)
        if not imported.startswith(str(worktree)):
            results.append({"id": entry["id"], "result": "ERROR", "why": f"juniper_data imports from {imported!r}, not the worktree"})
            continue
        original = target.read_bytes()
        if "replace_with" in entry:
            mutated = Path(entry["replace_with"]).read_bytes()
        else:
            text = original.decode("utf-8")
            count = text.count(entry["old"])
            if count != 1:
                results.append({"id": entry["id"], "result": "ERROR", "why": f"old text occurs {count} times in {entry['file']}"})
                continue
            mutated = text.replace(entry["old"], entry["new"]).encode("utf-8")
        cmd = [PYTHON, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-rA", "-q", "--timeout=120"]
        if entry.get("marker"):
            cmd += ["-m", entry["marker"]]
        cmd += entry["tests"]
        try:
            target.write_bytes(mutated)
            proc = subprocess.run(cmd, cwd=worktree, capture_output=True, text=True, env=env, check=False)
        finally:
            target.write_bytes(original)
        assert target.read_bytes() == original, f"restore failed for {target}"
        log = out_dir / f"mutant_{entry['id']}.log"
        log.write_text(f"$ (cwd={worktree}) {' '.join(cmd)}\n# mutant on {entry['file']}: {entry.get('old', '<whole file>')!r} -> {entry.get('new', entry.get('replace_with'))!r}\n# exit={proc.returncode}\n\n{proc.stdout}\n{proc.stderr}", encoding="utf-8")
        if proc.returncode == 1:
            verdict = "killed"
        elif proc.returncode == 0:
            verdict = "survived"
        else:
            verdict = "ERROR"
        failed = sorted(set(re.findall(r"^FAILED (\S+)", proc.stdout, re.MULTILINE)))
        results.append(
            {
                "id": entry["id"],
                "file": entry["file"],
                "mutant": f"{entry.get('old', '<whole file>')!r} -> {entry.get('new', entry.get('replace_with'))!r}",
                "tests": entry["tests"],
                "marker": entry.get("marker"),
                "exit": proc.returncode,
                "result": verdict,
                "expect": entry.get("expect", "killed"),
                "as_expected": verdict == entry.get("expect", "killed"),
                "summary": _summary(proc.stdout),
                "failed_tests": failed,
                "log": str(log),
            }
        )
    (out_dir / f"results_{spec_path.stem}.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    for row in results:
        print(f"{row['id']:6} {row['result']:9} expect={row.get('expect', '?'):9} {row.get('summary', row.get('why', ''))}")
    return 0 if all(row.get("as_expected") for row in results) else 1


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    sys.exit(run(Path(sys.argv[1]), Path(sys.argv[2])))
