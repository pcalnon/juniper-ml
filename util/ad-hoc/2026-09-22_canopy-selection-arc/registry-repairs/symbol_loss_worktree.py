"""Run juniper-ci-tools 0.8.0's own symbol-loss classification over origin/main -> the UNCOMMITTED worktree.

The CLI needs a HEAD commit and this session may not create one, so this feeds the tool's own
``symbols_for`` / ``classify_file`` / ``apply_relocation`` with base text from ``git show
origin/main:<path>`` and head text from the working file. Same scope as canopy's CI screen
(``src/**/*.py``). Run in JuniperCascor1 (where juniper_ci_tools is installed). Scratch only.
"""

import subprocess
import sys

from juniper_ci_tools import symbol_loss_check as slc

WT = "/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--registry-record-repairs--20260922-2021--26e0546f"
changed = subprocess.run(["git", "-C", WT, "diff", "--name-only", "origin/main"], check=True, capture_output=True, text=True).stdout.split()
scoped = [p for p in changed if slc._match_scope(p, ["src/**/*.py"])]
base_invs, head_invs, findings = {}, {}, []
for path in scoped:
    base_src = subprocess.run(["git", "-C", WT, "show", f"origin/main:{path}"], check=True, capture_output=True, text=True).stdout
    with open(f"{WT}/{path}", encoding="utf-8") as fh:
        head_src = fh.read()
    b_inv, b_ok = slc.symbols_for(path, base_src)
    h_inv, h_ok = slc.symbols_for(path, head_src)
    assert b_ok and h_ok, path
    base_invs[path], head_invs[path] = b_inv, h_inv
    findings.extend(slc.classify_file(path, b_inv, h_inv, False))
    added = sorted(set(h_inv) - set(b_inv))
    print(f"{path}: base {len(b_inv)} symbols, head {len(h_inv)}; added {len(added)}")
    for key in added:
        print(f"    + {key}")
slc.apply_relocation(findings, base_invs, head_invs)
fails = [f for f in findings if f.severity == "FAIL"]
print(f"files_screened={len(scoped)} findings={len(findings)} fail={len(fails)}")
for f in findings:
    print(f"  {f.severity} {f.verdict} {f.path}::{f.symbol} {f.detail}")
sys.exit(1 if fails else 0)
