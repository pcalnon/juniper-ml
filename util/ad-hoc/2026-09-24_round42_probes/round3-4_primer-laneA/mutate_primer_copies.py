"""Build two MUTATED copies of the worktree primer (in scratch) to prove register_primer_cites_v2.py can fail:
M1 inserts one line at line 500 (everything after moves); M2 edits the text of cited line 3647 in place."""

from pathlib import Path

SRC = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hazy-beaming-map/notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md")
OUT = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/primer-laneA")
lines = SRC.read_text(encoding="utf-8").split("\n")
m1 = lines[:499] + ["INSERTED LINE"] + lines[499:]
(OUT / "primer_mut_insert.md").write_text("\n".join(m1), encoding="utf-8")
m2 = list(lines)
m2[3646] = m2[3646].replace("juniper-data computes", "juniper-data compute")
assert m2[3646] != lines[3646]
(OUT / "primer_mut_edit3647.md").write_text("\n".join(m2), encoding="utf-8")
print("wrote primer_mut_insert.md and primer_mut_edit3647.md")
