#!/usr/bin/env python3
"""Lane A (round 2) independent line-invariance classifier for juniper-ml PR #2075.

Compares the primer at base (dcfc024f) with the primer at head (b6129bf8), both
extracted with `git show <sha>:<path>` into this directory.

For every base line i (1..N_base):
  * UNCHANGED      head[i] == base[i]
  * MARKER-ONLY    base[i] survives verbatim inside head[i]; the only inserted
                   characters are one or more `**[Corrected: E.n](#...)**`
                   markers plus whitespace (character-level diff has only
                   'equal' and 'insert' opcodes, and every insert is marker/ws).
  * INSERT-OTHER   base[i] survives verbatim (only inserts) but some inserted
                   text is not a marker -- the old text is intact, new prose added.
  * REWRITE        any character of base[i] deleted or replaced.
Lines after N_base in head are reported as the appendix and checked to start
with the new Appendix E material.

Mutation self-test (--selftest): proves the classifier can report a moved line,
a rewrite and a marker, i.e. that a clean result is not vacuous.
"""
import difflib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
MARKER_RE = re.compile(r"\*\*\[Corrected: E\.\d+\]\(#[a-z0-9-]+\)\*\*")


def classify(base_line: str, head_line: str) -> tuple[str, list[str]]:
    if base_line == head_line:
        return "UNCHANGED", []
    sm = difflib.SequenceMatcher(a=base_line, b=head_line, autojunk=False)
    ops = sm.get_opcodes()
    inserted = []
    only_inserts = True
    for tag, i1, i2, j1, j2 in ops:
        if tag == "equal":
            continue
        if tag == "insert":
            inserted.append(head_line[j1:j2])
        else:
            only_inserts = False
    if not only_inserts:
        return "REWRITE", inserted
    # difflib may split one marker across several insert chunks when marker
    # characters also occur in the base text; verify by removing markers.
    stripped = MARKER_RE.sub("\x00", head_line)
    # Remove markers with optional adjacent single space on either side and test
    # whether any combination reproduces base_line.
    cands = set()
    for pat in (r" ?\x00 ?", r" \x00", r"\x00 ", r"\x00"):
        cands.add(re.sub(pat, "", stripped))
    # also the variant where the marker replaced exactly one space between words
    cands.add(re.sub(r" ?\x00 ?", " ", stripped))
    if base_line in cands:
        return "MARKER-ONLY", inserted
    return "INSERT-OTHER", inserted


def run(base_path: Path, head_path: Path) -> dict:
    base = base_path.read_text(encoding="utf-8").split("\n")
    head = head_path.read_text(encoding="utf-8").split("\n")
    # split("\n") on a file ending in \n yields a trailing "" element
    base_trailing_nl = base[-1] == ""
    head_trailing_nl = head[-1] == ""
    if base_trailing_nl:
        base = base[:-1]
    if head_trailing_nl:
        head = head[:-1]
    n = len(base)
    res = {"n_base": n, "n_head": len(head), "base_trailing_nl": base_trailing_nl,
           "head_trailing_nl": head_trailing_nl, "lines": {}}
    counts = {"UNCHANGED": 0, "MARKER-ONLY": 0, "INSERT-OTHER": 0, "REWRITE": 0, "MISSING": 0}
    for i in range(n):
        if i >= len(head):
            counts["MISSING"] += 1
            res["lines"][i + 1] = {"cls": "MISSING"}
            continue
        cls, ins = classify(base[i], head[i])
        counts[cls] += 1
        if cls != "UNCHANGED":
            res["lines"][i + 1] = {
                "cls": cls,
                "n_markers_head": len(MARKER_RE.findall(head[i])),
                "n_markers_base": len(MARKER_RE.findall(base[i])),
                "len_base": len(base[i]),
                "len_head": len(head[i]),
                "base": base[i],
                "head": head[i],
            }
    res["counts"] = counts
    res["appendix_first_lines"] = head[n:n + 12]
    res["appendix_len"] = len(head) - n
    res["markers_total_head"] = sum(len(MARKER_RE.findall(l)) for l in head)
    res["markers_in_first_n"] = sum(len(MARKER_RE.findall(l)) for l in head[:n])
    res["lines_with_markers_in_first_n"] = [i + 1 for i in range(n) if MARKER_RE.search(head[i])]
    res["markers_in_base"] = sum(len(MARKER_RE.findall(l)) for l in base)
    res["max_len_head_first_n"] = max(len(l) for l in head[:n])
    res["lines_over_512_head"] = [i + 1 for i, l in enumerate(head) if len(l) > 512]
    res["lines_over_512_base"] = [i + 1 for i, l in enumerate(base) if len(l) > 512]
    return res


def selftest(base_path: Path) -> None:
    base = base_path.read_text(encoding="utf-8")
    lines = base.split("\n")
    tmp = HERE / "_selftest_head.md"
    # 1) insert one line near the top: everything after must be flagged
    mut = lines[:10] + ["INSERTED"] + lines[10:]
    tmp.write_text("\n".join(mut), encoding="utf-8")
    r = run(base_path, tmp)
    assert r["counts"]["UNCHANGED"] < r["n_base"] - 1000, r["counts"]
    # 2) marker appended to one line
    mut = list(lines)
    mut[99] = mut[99] + " **[Corrected: E.1](#e1-artifact-validator)**"
    tmp.write_text("\n".join(mut), encoding="utf-8")
    r = run(base_path, tmp)
    assert r["counts"]["MARKER-ONLY"] == 1 and list(r["lines"]) == [100], r["counts"]
    # 3) marker inserted mid-line
    mut = list(lines)
    idx = next(i for i, l in enumerate(lines) if l.count(". ") >= 2 and len(l) > 200)
    parts = mut[idx].split(". ", 1)
    mut[idx] = parts[0] + ". **[Corrected: E.2](#e2-conditional-tag-writes)** " + parts[1]
    tmp.write_text("\n".join(mut), encoding="utf-8")
    r = run(base_path, tmp)
    assert r["counts"]["MARKER-ONLY"] == 1, (r["counts"], r["lines"])
    # 4) one character changed -> REWRITE
    mut = list(lines)
    mut[99] = mut[99].replace("e", "E", 1) if "e" in mut[99] else mut[99] + "x"
    tmp.write_text("\n".join(mut), encoding="utf-8")
    r = run(base_path, tmp)
    assert r["counts"]["REWRITE"] + r["counts"]["INSERT-OTHER"] == 1, r["counts"]
    # 5) marker plus other words -> INSERT-OTHER
    mut = list(lines)
    mut[99] = mut[99] + " extra words **[Corrected: E.1](#e1-artifact-validator)**"
    tmp.write_text("\n".join(mut), encoding="utf-8")
    r = run(base_path, tmp)
    assert r["counts"]["INSERT-OTHER"] == 1, r["counts"]
    tmp.unlink()
    print("selftest: PASS (insert-line, append-marker, mid-line-marker, 1-char-rewrite, marker+words all detected)")


if __name__ == "__main__":
    base_p = HERE / "primer_base.md"
    head_p = HERE / "primer_head.md"
    if "--selftest" in sys.argv:
        selftest(base_p)
        sys.exit(0)
    r = run(base_p, head_p)
    out = HERE / "line_invariance.json"
    out.write_text(json.dumps(r, indent=1), encoding="utf-8")
    print(json.dumps({k: v for k, v in r.items() if k != "lines"}, indent=1))
    for ln, d in r["lines"].items():
        print(f"L{ln}\t{d['cls']}\tmarkers={d.get('n_markers_head')}\tlen {d.get('len_base')}->{d.get('len_head')}")
