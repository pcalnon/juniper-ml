#!/usr/bin/env python3
# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 4 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, lane11R4A.mG5yhk/prescreen_sweep.py
# Written by Lane 11-R4A (measurement re-creation, artifact-first, on round 3's corrections), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round4.md
# Everything below this block is the lane's file, modified 2026-10-08 only for CodeQL (py/unused-global-variable: a binding nothing reads is gone),
# predicted before its PR by util/ad-hoc/2026-10-05_codeql_python_prescreen.py; what it computes is unchanged.
# The edits: util/ad-hoc/2026-10-05_phase11_probes_codeql_fixes.py.
# ---------------------------------------------------------------------------
"""Lane 11-R4A: run the adcba49f prescreen over (1) Phase 10's merged scripts at 200c1393, (2) every Phase 11 .py at
adcba49f, (3) the round-1/2 probes as frozen at 7af6a381, (4) round 3's probes as their scratch originals."""
import importlib.util
import subprocess
from collections import Counter
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")
OUT = Path(__file__).resolve().parent / "prescreen_tmp"
OUT.mkdir(exist_ok=True)
SP = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/06e8868d-0c1f-4457-b7cb-b35e525032ef/scratchpad")


def git(*a):
    return subprocess.run(["git", *a], cwd=W, check=True, capture_output=True, text=True).stdout


pre_src = git("show", "adcba49f:util/ad-hoc/2026-10-05_codeql_python_prescreen.py")
(OUT / "prescreen.py").write_text(pre_src)
spec = importlib.util.spec_from_file_location("pre", OUT / "prescreen.py")
pre = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pre)


def scan_rev(rev, paths, label):
    total, per = 0, Counter()
    hits = []
    for p in paths:
        t = OUT / (rev + "_" + p.replace("/", "__"))
        t.write_text(git("show", f"{rev}:{p}"))
        found = pre._scan(t)
        total += len(found)
        for ln, rule, msg in found:
            per[rule] += 1
            hits.append(f"   {p.split('/')[-1]}:{ln}: {rule}: {msg}")
    print(f"{label}: {len(paths)} files, {total} predicted alerts {dict(per)}")
    return hits


# (1) Phase 10's merge
p10 = [l for l in git("diff", "--name-only", "--diff-filter=AM", "200c1393^", "200c1393").splitlines() if l.endswith(".py")]
p10_named = [p for p in p10 if "phase10" in p]
h = scan_rev("200c1393", p10, "Phase 10 merge, all .py")
for x in h:
    print(x)
scan_rev("200c1393", p10_named, "Phase 10 merge, phase10-named .py")

# (2) every .py added or modified on this branch since 200c1393 (Phase 11), at adcba49f
p11 = [l for l in git("diff", "--name-only", "--diff-filter=AM", "200c1393", "adcba49f").splitlines() if l.endswith(".py")]
h = scan_rev("adcba49f", p11, "Phase 11 branch .py at adcba49f")
for x in h:
    print(x)

# (3) round-1/2 probes as frozen at 7af6a381
r12 = [l for l in git("ls-tree", "--name-only", "7af6a381", "util/ad-hoc/").splitlines() if "_phase11_r1_" in l or "_phase11_r2_" in l]
h = scan_rev("7af6a381", r12, "round-1/2 probes at 7af6a381")
files_hit = sorted({x.split(":")[0].strip() for x in h})
print("   files with alerts:", len(files_hit))

# (4) round-3 originals
r3 = [l for l in git("ls-tree", "--name-only", "adcba49f", "util/ad-hoc/").splitlines() if "_phase11_r3_" in l]
total = 0
per = Counter()
fh = set()
for p in r3:
    name = p.split("/")[-1]
    lane = name.split("_r3_")[1][0]
    srcname = name.split(f"_r3_{lane}_", 1)[1]
    src = (SP / "lane11R3A.THYyw0" / srcname) if lane == "a" else (SP / "lane_probes" / "r3b" / srcname)
    found = pre._scan(src)
    total += len(found)
    for ln, rule, msg in found:
        per[rule] += 1
        fh.add(name)
print(f"round-3 originals: {len(r3)} files, {total} predicted alerts {dict(per)} in {len(fh)} files: {sorted(fh)}")
