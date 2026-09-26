#!/usr/bin/env python3
"""Lane A: is the new line 5838 (and the new NaN arm at 6119-6120) what catches the reverts? My own mutants.

Mutants over the HEAD primer, each run through the Appendix D harness from the head tree with the pinned venv:
  A  POST create reverted (5671-5672 -> JSONResponse)                          expect CAUGHT
  B  A + line 5838 restored to its base text                                    expect MISSED (proves 5838 is the pin)
  C  NaN schema reverted (5400, 5498, 5502 -> base)                              expect CAUGHT
  D  C + lines 6119-6120 restored to base (no NaN arm)                           expect MISSED (proves the arm is the pin)
  E  only 5498 reverted (allow_inf_nan dropped; StrictFloat kept)                expect CAUGHT (StrictFloat alone admits NaN)
  F  only 5502 reverted (params back to Any; allow_inf_nan kept)                 expect CAUGHT
Also runs the harness on the unmutated base primer (df21367d) for its test count.
"""
import pathlib
import subprocess
import sys

S = pathlib.Path(__file__).resolve().parent
HEADTREE = S / "eco/juniper-ml"
HARNESS = HEADTREE / "util/ad-hoc/2026-08-13_run_primer_examples.py"
VENV = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/primer-venv"
P = "JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
head = (S / "head" / P).read_text(encoding="utf-8").split("\n")
base = (S / "base" / P).read_text(encoding="utf-8").split("\n")
OUT = S / "pinmut_mine"
OUT.mkdir(exist_ok=True)


def run(doc):
    p = subprocess.run([sys.executable, str(HARNESS), "--doc", str(doc), "--venv", VENV], capture_output=True, text=True)
    tail = [ln for ln in p.stdout.split("\n") if " passed" in ln or " failed" in ln]
    return p.returncode, (tail[-1].strip() if tail else f"exit {p.returncode}")


def mutant(name, edits):
    lines = list(head)
    for n, text in edits.items():
        lines[n - 1] = text
    doc = OUT / f"{name}.md"
    doc.write_text("\n".join(lines), encoding="utf-8")
    rc, tail = run(doc)
    print(f"  {name}: {'CAUGHT' if rc else 'MISSED'} -- {tail}")


create = {5671: "        return JSONResponse(", 5672: "            dataset.metadata(),"}
schema = {n: base[n - 1] for n in (5400, 5498, 5502)}
mutant("A_post_create", create)
mutant("B_post_create_plus_old_5838", {**create, 5838: base[5837]})
mutant("C_nan_schema", schema)
mutant("D_nan_schema_plus_no_nan_arm", {**schema, 6119: base[6118], 6120: base[6119]})
mutant("E_only_5498", {5498: base[5497]})
mutant("F_only_5502", {5502: base[5501]})
rc, tail = run(S / "base" / P)
print(f"  base df21367d unmutated: rc={rc} -- {tail}")
