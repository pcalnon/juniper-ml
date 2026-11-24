"""
Run n3's contention fuzz and a retargeted copy of the builder's seed sweep against the fix and n3's mutant trees.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-09_flood4r2_val_n3-code_resume_probes.py
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(Path.home(), "Development/python/Juniper/juniper-ml/.claude/worktrees/humming-stargazing-papert")
S = REPO / "tmp/flood4r2-val/n3-code-lens"
PY = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
FIX_SRC = Path(Path.home(), "Development/python/Juniper/worktrees/juniper-cascor--validate--ws-resume-losses-n3-code--20261109-0324--f3dfee8c/src")
MAIN_SRC = str(S / "main-tree/src")


def src_of(variant: str) -> str:
    return {"fix": FIX_SRC, "main": MAIN_SRC}.get(variant, str(S / "mutant-trees" / variant / "src"))


def env() -> dict:
    e = dict(os.environ)
    e.pop("JUNIPER_CASCOR_LOG_DIR", None)
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    return e


def fuzz(variant: str, seeds: int, start: int, accept_yields: int = 0) -> dict:
    out = S / f"fuzz_churn_{variant}_{start}_{seeds}_ay{accept_yields}.json"
    cmd = [PY, str(REPO / "util/ad-hoc/2026-11-09_flood4r2_val_n3-code_resume_probes.py"), "--src", src_of(variant), "--label", variant, "--only", "none", "--fuzz-seeds", str(seeds), "--fuzz-start", str(start), "--accept-yields", str(accept_yields), "--out", str(out)]
    subprocess.run(cmd, cwd=REPO, env=env(), capture_output=True, text=True, check=True)
    with open(out, encoding="utf-8") as fh:
        d = json.load(fh)["fuzz"]
    return {k: d[k] for k in ("accept_yields", "seeds", "start", "violating_seeds", "aborted_resumes", "resume_ok")} | {"first": d["first_violations"][:2]}


def sweep(variant: str, seeds: int, start: int) -> dict:
    e = env()
    e["SWEEP_SRC"] = src_of(variant)
    proc = subprocess.run([PY, str(S / "builder_seed_sweep_copy.py"), str(start), str(seeds)], cwd=REPO, env=e, capture_output=True, text=True)
    (S / f"builder_sweep_{variant}_{start}_{seeds}.json").write_text(proc.stdout, encoding="utf-8")
    d = json.loads(proc.stdout)
    return {"code_under_test": d["code_under_test"], "n": d["n"], "violations": d["violations"], "outcomes": d["outcomes"], "elapsed_s": d["elapsed_s"], "first": d["first_violations"][:2]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", choices=["fuzz", "sweep"], required=True)
    ap.add_argument("--variants", nargs="+", required=True)
    ap.add_argument("--seeds", type=int, required=True)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--accept-yields", type=int, default=0)
    args = ap.parse_args()
    for v in args.variants:
        res = fuzz(v, args.seeds, args.start, args.accept_yields) if args.kind == "fuzz" else sweep(v, args.seeds, args.start)
        print(v, json.dumps(res, default=str)[:900], flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
