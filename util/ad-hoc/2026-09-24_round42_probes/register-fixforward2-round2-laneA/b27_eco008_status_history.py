#!/usr/bin/env python3
"""Lane A round 2: APD-ECO-008's row status at each register revision from its filing to round 42."""
import subprocess

WT = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
REG = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
for rev in ("836393cf^", "836393cf", "370c51eb", "8541f4fe", "6aabe4cc"):
    t = subprocess.run(["git", "show", f"{rev}:{REG}"], cwd=WT, capture_output=True, text=True).stdout
    rows = [l for l in t.split("\n") if l.startswith("| APD-ECO-008 |")]
    print(rev, "rows:", len(rows), "| first row starts:", rows[0][:70] if rows else "-", "| FIXED:", any("**FIXED" in r for r in rows))
