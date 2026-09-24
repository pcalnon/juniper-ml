#!/usr/bin/env python3
"""Lane A: every primer line number in Appendix A's range (register-creation primer: 9335-9620)
that the PR-head register cites, with what the line holds at creation (68f62f5b) and at HEAD."""
import re

S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneA"
reg = open(f"{S}/head/notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md", encoding="utf-8").read()
old = open(f"{S}/primer_68f62f5b.md", encoding="utf-8").read().split("\n")
new = open(f"{S}/primer_HEAD.md", encoding="utf-8").read().split("\n")


def q_of(lines, n):
    for i in range(n - 1, max(n - 12, 0), -1):
        m = re.match(r"\*\*(Q\d+)\.", lines[i - 1] if i - 1 < len(lines) else "")
        if m:
            return m.group(1)
    return "?"


seen = set()
for m in re.finditer(r"(?<![\d.:/-])(9[3-6]\d\d)(?:-(9[3-6]\d\d))?(?![\d])", reg):
    a = int(m.group(1))
    if not 9330 <= a <= 9625 or m.group(0) in seen:
        continue
    seen.add(m.group(0))
    line_no = reg[: m.start()].count("\n") + 1
    ctx = reg[max(0, m.start() - 60): m.start()].replace("\n", " ")
    o = old[a - 1][:70] if a <= len(old) else ""
    n = new[a - 1][:70] if a <= len(new) else ""
    print(f"register:{line_no}: '{m.group(0)}' (…{ctx[-45:]})")
    print(f"    creation primer {a}: [{q_of(old, a + 1)}] {o!r}")
    print(f"    HEAD primer     {a}: [{q_of(new, a + 1)}] {n!r}")
