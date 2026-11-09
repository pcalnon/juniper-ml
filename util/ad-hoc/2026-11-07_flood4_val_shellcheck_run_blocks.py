"""
Flood-4 validation: shellcheck the `tests` job's run blocks of ci.yml on origin/main and on this worktree,
and diff the findings (actionlint's shellcheck pass hung on this host).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 tests carrier validation (fidelity, fixes and gates lens)
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parents[2]
BASE = "303ccc0b4613dadcbe5ef16985a862beccec7a1a"


def blocks(text: str) -> dict[str, str]:
    doc = yaml.safe_load(text)
    out = {}
    for job_id, job in doc["jobs"].items():
        for i, step in enumerate(job.get("steps", [])):
            if "run" in step:
                out[f"{job_id}/{i}:{step.get('name', '')}"] = step["run"]
    return out


def check(script: str) -> list[str]:
    with tempfile.NamedTemporaryFile("w", suffix=".bash", delete=False) as fh:
        fh.write("#!/usr/bin/env bash\nset -e\n" + script.replace("${{", "__GHA_EXPR_OPEN").replace("}}", "__GHA_EXPR_CLOSE"))
        name = fh.name
    try:
        r = subprocess.run(["shellcheck", "-f", "gcc", "-S", "warning", name], capture_output=True, text=True, timeout=120)
        return [l.split(":", 3)[-1].strip() for l in r.stdout.splitlines()]
    finally:
        Path(name).unlink()


def main() -> int:
    main_text = subprocess.run(["git", "show", f"{BASE}:.github/workflows/ci.yml"], cwd=HERE, capture_output=True, text=True, check=True).stdout
    car_text = (HERE / ".github/workflows/ci.yml").read_text()
    mb, cb = blocks(main_text), blocks(car_text)
    print("run blocks main/carrier:", len(mb), len(cb), "same keys:", sorted(mb) == sorted(cb))
    changed = [k for k in cb if mb.get(k) != cb[k]]
    print("changed run blocks:", changed)
    for k in changed:
        a, b = check(mb.get(k, "")), check(cb[k])
        print(f"{k}: shellcheck warnings main={len(a)} carrier={len(b)}; new in carrier: {sorted(set(b) - set(a))[:10]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
