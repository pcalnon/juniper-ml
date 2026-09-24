#!/usr/bin/env python3
"""Lane A r2: run the PR's toy ETag probe (pr_toy_probe.py, extracted from b6129bf8) over
{head, base} x {Appendix-D-pinned venv, harness-built latest venv, JuniperData env}.
Expected per the PR body: head MATCH 4/4, base MISMATCH 4/4 (negative control)."""
import subprocess
from pathlib import Path

S = Path(__file__).resolve().parent
PYS = {
    "pinned(3.13.13/starlette1.6.0)": S / "venv_pinned/bin/python",
    "latest(3.14.7/starlette1.7.0)": S / "tmp_harness/juniper-api-primer-examples-1hn3r36p/.venv/bin/python",
    "JuniperData(3.14.2/starlette0.50.0)": Path("/opt/miniforge3/envs/JuniperData/bin/python"),
}
for label, py in PYS.items():
    for doc in ("primer_head.md", "primer_base.md"):
        p = subprocess.run([str(py), str(S / "pr_toy_probe.py"), str(S / doc)], capture_output=True, text=True)
        lines = [l.strip() for l in p.stdout.splitlines() if l.strip()]
        n_match = sum(l.startswith("MATCH") for l in lines)
        print(f"{label:36s} {doc:15s} rc={p.returncode} MATCH {n_match}/{len(lines)} :: {' | '.join(lines)}")
        if p.stderr.strip():
            print("   stderr:", p.stderr.strip().splitlines()[-1])
