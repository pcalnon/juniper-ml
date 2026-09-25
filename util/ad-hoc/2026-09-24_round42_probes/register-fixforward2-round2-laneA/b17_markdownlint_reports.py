#!/usr/bin/env python3
"""Lane A round 2: run the pre-commit-pinned markdownlint-cli (v0.42.0, from the local pre-commit cache) WITHOUT
--fix on the two archived round-1 reports as they are in the head tree, with the head's .markdownlint.yaml.
Also on e2f87aae-era sibling reports for comparison (same directory, earlier archived files)."""
import os
import subprocess
from pathlib import Path

HEAD = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b2/laneA/head")
BIN = "/home/pcalnon/.cache/pre-commit/repoft72ba_k/node_env-default/bin"
env = dict(os.environ, PATH=BIN + ":" + os.environ["PATH"])
files = [
    "reports/2026-09-24_defect-register-round-42/register-fixforward2-round1-laneA-reprobe.md",
    "reports/2026-09-24_defect-register-round-42/register-fixforward2-round1-laneB-refute.md",
    "reports/2026-09-24_defect-register-round-42/ml2080-round1-laneA-reprobe.md",
    "reports/2026-09-24_defect-register-round-42/ml2080-round1-laneB-refute.md",
]
for f in files:
    p = subprocess.run([BIN + "/markdownlint", "--config=./.markdownlint.yaml", f], cwd=HEAD, capture_output=True, text=True, env=env)
    print(f"== {f}: rc={p.returncode}")
    print((p.stdout + p.stderr).strip()[:1500] or "   (clean)")
