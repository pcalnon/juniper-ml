"""
Apply one-line mutants to source files, run a test command per mutant, and restore each file byte-for-byte.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier, round-2 validation (corrections and their blast radius)

Usage (from the validator's own worktree root):
    python3 util/ad-hoc/2026-11-07_flood4_val_round2_mutate.py SPEC.json OUT.log

SPEC.json is a list of {"id", "file", "old", "new", "cmd": [argv...], "env": {optional extra env}}.
"old" must occur exactly once in "file". Each mutant: sha256 before, write the mutant, delete
__pycache__ dirs under the file's directory and under tests/, run cmd, restore, sha256 after
(must equal before). A mutant is "killed" when cmd exits non-zero, "survived" when it exits 0.
"cmd" may be run with "baseline": true to record the unmutated exit status instead.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess  # nosec B404 -- fixed argv from a local spec file
import sys
from pathlib import Path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _clear_pycache(root: Path) -> None:
    for cache in root.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def _run(cmd: list[str], extra_env: dict[str, str]) -> tuple[int, str]:
    env = dict(os.environ)
    env.update(extra_env)
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, check=False, timeout=900)  # nosec B603
    tail = (proc.stdout + proc.stderr).strip().splitlines()[-12:]
    return proc.returncode, "\n".join(tail)


def main(argv: list[str]) -> int:
    with open(argv[0], encoding="utf-8") as fh:
        spec = json.load(fh)
    out_lines: list[str] = []
    bad = 0
    for item in spec:
        cmd = item["cmd"]
        extra_env = item.get("env", {})
        if item.get("baseline"):
            rc, tail = _run(cmd, extra_env)
            out_lines.append(f"[{item['id']}] BASELINE rc={rc} cmd={' '.join(cmd)}\n{tail}\n")
            continue
        path = Path(item["file"])
        original = path.read_bytes()
        before = _sha(path)
        text = original.decode("utf-8")
        count = text.count(item["old"])
        if count != 1:
            out_lines.append(f"[{item['id']}] ERROR old string occurs {count} times in {path}\n")
            bad += 1
            continue
        try:
            path.write_text(text.replace(item["old"], item["new"]), encoding="utf-8")
            _clear_pycache(path.parent)
            _clear_pycache(Path("tests"))
            rc, tail = _run(cmd, extra_env)
        finally:
            path.write_bytes(original)
            _clear_pycache(path.parent)
            _clear_pycache(Path("tests"))
        after = _sha(path)
        verdict = "killed" if rc != 0 else "survived"
        restored = "restored-ok" if after == before else "RESTORE-MISMATCH"
        if after != before:
            bad += 1
        out_lines.append(f"[{item['id']}] {verdict} rc={rc} {restored} {path}: {item['old']!r} -> {item['new']!r}\n  cmd={' '.join(cmd)}\n{tail}\n")
    text_out = "\n".join(out_lines)
    with open(argv[1], "w", encoding="utf-8") as fh:
        fh.write(text_out)
    sys.stdout.write(text_out)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
