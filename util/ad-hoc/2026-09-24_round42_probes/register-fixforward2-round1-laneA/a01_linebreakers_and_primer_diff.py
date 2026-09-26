#!/usr/bin/env python3
"""Lane A: (1) raw code points of the editor's LINE_BREAKERS; (2) primer base-vs-head line diff by my own method.

My own method: compare base and head with difflib opcodes on splitlines() AND split('\n'), report every
non-equal opcode, line counts both ways, and whether any changed head line holds a splitlines() breaker.
"""
import ast
import difflib
import pathlib

S = pathlib.Path(__file__).resolve().parent
ed = (S / "head/2026-09-24_register_round42_second_fixforward.py").read_text(encoding="utf-8")
for node in ast.parse(ed).body:
    if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == "LINE_BREAKERS":
        v = ast.literal_eval(node.value)
        print("LINE_BREAKERS code points:", [hex(ord(c)) for c in v])

# the full set of characters str.splitlines() breaks on, derived empirically over the BMP
breakers = [chr(i) for i in range(0x110000) if len(("a" + chr(i) + "b").splitlines()) == 2 and chr(i) != "\n"]
print("splitlines() breakers besides \\n:", [hex(ord(c)) for c in breakers])
missing = [hex(ord(c)) for c in breakers if c not in v]
print("breakers the editor does NOT refuse:", missing)

P = "JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
b = (S / "base" / P).read_text(encoding="utf-8")
h = (S / "head" / P).read_text(encoding="utf-8")
print("primer bytes base/head:", len(b.encode()), len(h.encode()))
print("split('\\n') base/head:", len(b.split("\n")), len(h.split("\n")))
print("splitlines() base/head:", len(b.splitlines()), len(h.splitlines()))
print("trailing newline base/head:", b.endswith("\n"), h.endswith("\n"))
bl, hl = b.split("\n"), h.split("\n")
sm = difflib.SequenceMatcher(a=bl, b=hl, autojunk=False)
changed = []
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag != "equal":
        print(f"opcode {tag}: base {i1+1}-{i2} -> head {j1+1}-{j2}")
        if tag == "replace" and (i2 - i1) == (j2 - j1) and i1 == j1:
            changed.extend(range(i1 + 1, i2 + 1))
print("positional changed lines:", [i + 1 for i, (x, y) in enumerate(zip(bl, hl)) if x != y])
print("count positional:", sum(1 for x, y in zip(bl, hl) if x != y))
for i, (x, y) in enumerate(zip(bl, hl)):
    if x != y:
        bad = [hex(ord(c)) for c in y if c in breakers]
        if bad:
            print("BREAKER in head line", i + 1, bad)
# any breaker anywhere in head that is not in base?
hb = sum(1 for c in h if c in breakers)
bb = sum(1 for c in b if c in breakers)
print("breaker chars total base/head:", bb, hb)
