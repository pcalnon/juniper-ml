#!/usr/bin/env python3
"""Lane A: re-derive §2's two newly recorded blind spots of the register tools by my own mutations.

M7  put `**FIXED` into an OPEN row's Source cell (APD-RCLIENT-004)   claim: open-set counts it fixed, crosscheck AGREE
M8  duplicate an OPEN row (APD-RCLIENT-004) right after itself        claim: invisible to both
C1  control: drop `**FIXED` from a FIXED row's status cell (APD-SVCCORE-011 §4 row)  expect both tools to move / DISAGREE
Each runs register_open_set.py (cwd-relative register) and register_status_crosscheck.py (script-relative) from
the head tree on a mutated copy of the head register.
"""
import pathlib
import re
import shutil
import subprocess
import sys

S = pathlib.Path(__file__).resolve().parent
HEAD = S / "eco/juniper-ml"
REG = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
TOOLS = ["util/ad-hoc/register_open_set.py", "util/ad-hoc/register_status_crosscheck.py"]
text = (HEAD / REG).read_text(encoding="utf-8")
lines = text.split("\n")


def row_index(rid):
    hits = [i for i, ln in enumerate(lines) if ln.startswith(f"| {rid} |")]
    return hits


def cells(line):
    return re.split(r"(?<!\\)\|", line)


def run(name, new_lines):
    root = S / "mut" / name / "juniper-ml"
    if root.parent.exists():
        shutil.rmtree(root.parent)
    for rel in TOOLS:
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(HEAD / rel, root / rel)
    (root / REG).parent.mkdir(parents=True, exist_ok=True)
    (root / REG).write_text("\n".join(new_lines), encoding="utf-8")
    o = subprocess.run([sys.executable, TOOLS[0]], cwd=root, capture_output=True, text=True).stdout
    summary = next((ln for ln in o.split("\n") if " rows | " in ln), "?")
    c = subprocess.run([sys.executable, TOOLS[1]], cwd=root, capture_output=True, text=True)
    verdict = [ln for ln in c.stdout.split("\n") if ln.strip()][-1]
    tables = next((ln for ln in c.stdout.split("\n") if ln.startswith("§4 tables")), "?")
    print(f"{name:12} open_set: {summary:32} crosscheck: {verdict} ({tables.strip()})")
    shutil.rmtree(root.parent)


run("baseline", lines)
i = row_index("APD-RCLIENT-004")
assert len(i) == 1, i
i = i[0]
cs = cells(lines[i])
print("RCLIENT-004 cells:", [c.strip()[:40] for c in cs])
cs7 = list(cs)
cs7[4] = " **FIXED** " + cs7[4].strip() + " "  # Source cell (ID, Finding, Sev, Source, Primer, Conf)
m7 = list(lines)
m7[i] = "|".join(cs7)
run("M7", m7)
m8 = list(lines)
m8.insert(i + 1, lines[i])
run("M8", m8)
j = [k for k in row_index("APD-SVCCORE-011") if "**FIXED" in lines[k]][0]
c1 = list(lines)
c1[j] = lines[j].replace("**FIXED (ml#1441)**", "(ml#1441)", 1)
assert c1[j] != lines[j]
run("C1-control", c1)
