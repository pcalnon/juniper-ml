#!/usr/bin/env python3
"""Lane B: prove every register->primer line anchor still points at the same text.

Inputs (all read-only copies or worktree files):
  primer_HEAD.md   = git show HEAD:<primer>
  primer_WT.md     = worktree primer (with the uncommitted correction)
  register         = worktree defect register (unmodified vs HEAD)
Checks:
  1. Structural: the first N lines (N = len(HEAD)) are identical except marked lines, which
     equal HEAD.rstrip() + MARKER; nothing is inserted or deleted before the appendix.
  2. Every primer line cited by the register (Primer column, and every number in any prose
     line that mentions the primer / a line / a range) resolves to the same text.
  3. Rendering context of each marked line: in code fence? table row? blockquote? list item?
     paragraph-final (next line blank or fence)?
"""
import re
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/primer-laneB")
REG = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hazy-beaming-map/notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md")
MARKER = " **[Corrected: E.1](#e1-artifact-validator)**"

head = (S / "primer_HEAD.md").read_text(encoding="utf-8").split("\n")
wt = (S / "primer_WT.md").read_text(encoding="utf-8").split("\n")
if head and head[-1] == "":
    head = head[:-1]
if wt and wt[-1] == "":
    wt = wt[:-1]

# ---- 1. structural
changed = []
for i, (h, w) in enumerate(zip(head, wt), start=1):
    if h != w:
        changed.append(i)
        assert w == h.rstrip() + MARKER, f"line {i} changed beyond the marker"
print(f"HEAD lines={len(head)}  WT lines={len(wt)}  appended={len(wt) - len(head)}")
print(f"lines changed within HEAD span: {len(changed)} -> {changed}")

# ---- 2. register citations
reg = REG.read_text(encoding="utf-8").split("\n")
cited: dict[int, list[str]] = {}


def add(n: int, where: str) -> None:
    if 1 <= n <= len(head):
        cited.setdefault(n, []).append(where)


def nums(cell: str):
    for a, b in re.findall(r"(?<![\w.:/-])(\d{2,4})(?:\s*[-–]\s*(\d{2,4}))?(?![\w.])", cell):
        a = int(a)
        if b:
            b = int(b)
            if b >= a and b - a < 60:
                yield from range(a, b + 1)
                continue
        yield a


col = None
for i, ln in enumerate(reg, start=1):
    if ln.startswith("|"):
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if "Primer" in cells:
            col = cells.index("Primer")
            continue
        if col is not None and not set(ln.replace("|", "").strip()) <= set("-: ") and len(cells) > col:
            for n in nums(cells[col]):
                add(n, f"reg:{i}:col")
    else:
        col = None
        if re.search(r"primer|\bline\b|\bat \d{3,4}", ln, re.I):
            # exclude obvious non-primer numbers: file:line pairs (handled by the lookbehind on ':'),
            # PR numbers (#NNN), dates, versions
            clean = re.sub(r"#\d+|\d{4}-\d{2}-\d{2}|v?\d+\.\d+(\.\d+)?|`[^`]*`", " ", ln)
            for n in nums(clean):
                if n >= 100:
                    add(n, f"reg:{i}:prose")

bad = []
for n, where in sorted(cited.items()):
    h, w = head[n - 1], wt[n - 1]
    if h != w and w != h.rstrip() + MARKER:
        bad.append((n, where))
on_marked = sorted(set(cited) & set(changed))
print(f"distinct primer lines cited by the register: {len(cited)}")
print(f"cited lines whose text changed beyond the marker: {bad}")
print(f"cited lines that now carry the marker: {on_marked}")
for n in (3399, 3647, 4171, 4197, 4247, 3999, 4017):
    print(f"  cited {n}: {'yes' if n in cited else 'no'}; marker on it: {n in changed}")

# ---- 3. rendering context of each marked line
in_code = False
fence_state = {}
for i, ln in enumerate(wt, start=1):
    if ln.lstrip().startswith("```"):
        in_code = not in_code
        fence_state[i] = True
    fence_state.setdefault(i, in_code)
print("\nmarked-line rendering context:")
for n in changed:
    ln = wt[n - 1]
    nxt = wt[n] if n < len(wt) else ""
    prv = wt[n - 2]
    ctx = []
    if fence_state.get(n):
        ctx.append("IN-CODE-FENCE")
    if ln.lstrip().startswith("|"):
        ctx.append("TABLE-ROW")
    if ln.lstrip().startswith(">"):
        ctx.append("BLOCKQUOTE")
    if re.match(r"^\s*([-*+]|\d+\.)\s", ln):
        ctx.append("LIST-ITEM")
    elif re.match(r"^\s{2,}\S", ln):
        ctx.append("INDENTED-CONTINUATION")
    para_final = nxt.strip() == "" or nxt.lstrip().startswith("```")
    ctx.append("paragraph-final" if para_final else f"MID-PARAGRAPH (next: {nxt[:70]!r})")
    ends_colon = ln[: -len(MARKER)].rstrip().endswith(":")
    if ends_colon and nxt.strip() == "":
        ctx.append("marker-after-colon-introducing-next-block")
    print(f"  {n}: {', '.join(ctx)}")
