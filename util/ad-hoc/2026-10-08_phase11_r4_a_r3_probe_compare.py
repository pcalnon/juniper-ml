#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R4A.mG5yhk/r3_probe_compare.py
# Written by Lane 11-R4A (measurement re-creation, artifact-first, on round 3's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-import: an import nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-R4A: compare the 19 round-3 archived probes at adcba49f with their scratch originals.

Body = archived file minus shebang and the header block between the two '# ----' bars. Untouched probes must be
byte-identical to their source (minus the source's shebang); CodeQL-edited ones must be AST-equivalent after undoing
the with-wrap and the dropped names (via ast_compare's helpers).
"""
import ast
import copy
import importlib.util
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ac", HERE / "ast_compare.py")
ac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ac)

W = ac.W
SP = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad")
SRC = {"a": SP / "lane11R3A.THYyw0", "b": SP / "lane_probes" / "r3b"}
ORIG_B = Path("/tmp/tmp.cIFAKjB6BD")


def body_of(text):
    lines = text.split("\n")
    if lines[0].startswith("#!"):
        lines = lines[1:]
    bars = [i for i, l in enumerate(lines) if l.startswith("# ----")]
    assert len(bars) >= 2, "no header bars"
    return "\n".join(lines[bars[1] + 1:]), "\n".join(lines[bars[0]:bars[1] + 1])


def strip_shebang(text):
    return text.split("\n", 1)[1] if text.startswith("#!") else text


files = sorted(l for l in subprocess.run(["git", "ls-tree", "--name-only", "adcba49f", "util/ad-hoc/"], cwd=W, capture_output=True, text=True, check=True).stdout.splitlines() if "2026-10-08_phase11_r3_" in l)
print(len(files), "round-3 probes at adcba49f")
for f in files:
    name = f.split("/")[-1]
    lane = name.split("_r3_")[1][0]
    srcname = name.split(f"_r3_{lane}_", 1)[1]
    arch = ac.show("adcba49f", f)
    body, hdr = body_of(arch)
    src = (SRC[lane] / srcname).read_text(encoding="utf-8")
    srcb = strip_shebang(src)
    edited = "modified 2026-10-08 only for CodeQL" in hdr
    same_bytes = body == srcb
    line = f"{'EDITED ' if edited else 'verbatim'} bytes_equal={same_bytes} {name}"
    if lane == "b" and (ORIG_B / srcname).exists():
        line += f" copy==tmp_original:{(ORIG_B / srcname).read_bytes() == (SRC['b'] / srcname).read_bytes()}"
    if edited or not same_bytes:
        rep = []
        to, tn = ast.parse(srcb), ast.parse(body)
        tn2 = ac.Unwith().visit(copy.deepcopy(tn))
        to2 = ac.strip_dropped(copy.deepcopy(to), tn2, rep)
        line += f" AST-equiv={ast.dump(to2) == ast.dump(tn2)}"
        print(line)
        for r in rep:
            print(r)
    else:
        print(line)
