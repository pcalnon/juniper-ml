#!/usr/bin/env python3
"""Mutation-check register_open_set.py and register_status_crosscheck.py against scratch copies of the
PR-head register. Each mutant lives in its own tree mut/<name>/{notes,util/ad-hoc}; both scripts run with
cwd = that tree (open_set is CWD-relative; crosscheck resolves parents[2] of its own path).
Reports what each instrument prints, so we can see which mutants are DETECTED and which are INVISIBLE."""
import os
import shutil
import subprocess
import sys

S = os.path.dirname(os.path.abspath(__file__))
HEAD = os.path.join(S, "head")
REGREL = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
SCRIPTS = ["util/ad-hoc/register_open_set.py", "util/ad-hoc/register_status_crosscheck.py"]
base_text = open(os.path.join(HEAD, REGREL), encoding="utf-8").read()

# splitlines-only separator census (crosscheck uses splitlines, open_set uses split("\n"))
seps = ["\r", "\x0b", "\x0c", "\x1c", "\x1d", "\x1e", "\x85", " ", " "]
print("splitlines-only separators present:", [hex(ord(c)) for c in seps if c in base_text])
print("split(\\n):", len(base_text.split("\n")), " splitlines():", len(base_text.splitlines()))


def sub_once(text, old, new):
    n = text.count(old)
    assert n == 1, f"anchor {old[:60]!r} matched {n} times"
    return text.replace(old, new)


ECO8_ROW_51 = next(l for l in base_text.split("\n") if l.startswith("| APD-ECO-008 | canopy's"))
PHANTOM = "| APD-ECO-099 | phantom open row | S | nowhere | — | High |"
eco9 = next(l for l in base_text.split("\n") if l.startswith("| APD-ECO-009 |"))

mutants = {
    "M0-unmutated": lambda t: t,
    "M1-prose-open-count-34-to-35": lambda t: sub_once(t, "**34 open in all**", "**35 open in all**"),
    "M2-prose-filed-38-to-39": lambda t: sub_once(t, "thirty-eight filed", "thirty-nine filed"),
    "M3-prose-split-19-to-20": lambda t: sub_once(t, "15 primer + 19 post-primer", "15 primer + 20 post-primer"),
    "M4-prose-eighty-one-to-eighty": lambda t: sub_once(t, "**Eighty-one of the 96 have since been fixed**", "**Eighty of the 96 have since been fixed**"),
    "M5-drop-ECO-008-from-s2-list (control)": lambda t: sub_once(
        t,
        " and (2026-09-24) `APD-ECO-008` ([juniper-canopy#660](https://github.com/pcalnon/juniper-canopy/pull/660) + [juniper-ml#2059](https://github.com/pcalnon/juniper-ml/pull/2059))",
        "",
    ),
    "M6-drop-ECO-008-s51-row (control)": lambda t: sub_once(t, ECO8_ROW_51 + "\n", ""),
    "M7-phantom-open-row": lambda t: sub_once(t, eco9 + "\n", eco9 + "\n" + PHANTOM + "\n"),
    "M8-ECO-009-sev-S-to-M (prose says three S)": lambda t: sub_once(t, eco9, eco9.replace("| S | `juniper-canopy/src/middleware.py:59-74`", "| M | `juniper-canopy/src/middleware.py:59-74`")),
    "M9-unmark-ECO-008-in-s4 (control)": lambda t: sub_once(
        t,
        "| APD-ECO-008 | **FIXED ([juniper-canopy#660]",
        "| APD-ECO-008 | ([juniper-canopy#660]",
    ),
}

outdir = os.path.join(S, "mut")
shutil.rmtree(outdir, ignore_errors=True)
for name, fn in mutants.items():
    tree = os.path.join(outdir, name.split(" ")[0])
    os.makedirs(os.path.join(tree, "notes"), exist_ok=True)
    os.makedirs(os.path.join(tree, "util/ad-hoc"), exist_ok=True)
    for sc in SCRIPTS:
        shutil.copy(os.path.join(HEAD, sc), os.path.join(tree, sc))
    with open(os.path.join(tree, REGREL), "w", encoding="utf-8") as fh:
        fh.write(fn(base_text))
    r1 = subprocess.run([sys.executable, SCRIPTS[0]], cwd=tree, capture_output=True, text=True)
    r2 = subprocess.run([sys.executable, SCRIPTS[1]], cwd=tree, capture_output=True, text=True)
    head1 = r1.stdout.split("\n")[0]
    ml = [l.strip() for l in r1.stdout.split("\n") if l.strip().startswith("APD-ML ")]
    verdict = (r2.stdout.strip().split("\n") or [""])[-1]
    print(f"{name:48} open_set: {head1:34} {ml} | crosscheck: {verdict} (rc={r2.returncode})")
