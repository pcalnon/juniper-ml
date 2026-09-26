#!/usr/bin/env python3
"""Lane B r2: my own same-line mutants of the head primer, each run through all three instruments.

For each mutant: builds a scratch root <scratch>/m_<name>/ holding notes/<primer> (mutated) and copies of the
harness, the probe and the mutation check, then runs
  harness      (Appendix D, the primer's own suite)
  probe        (2026-09-24_primer_toy_error_paths_probe.py)
  mutation chk (2026-09-24_primer_toy_pin_mutation_check.py, which treats the mutated primer as its control)
and prints whether each noticed. "noticed" = a non-zero exit.

Usage: python3 b14_own_mutants.py <laneB dir> <venv>
"""
import shutil
import subprocess
import sys
from pathlib import Path

S = Path(sys.argv[1])
VENV = sys.argv[2]
REL = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
BASE = (S / "after" / REL).read_text(encoding="utf-8").split("\n")
TOOLS = ["2026-08-13_run_primer_examples.py", "2026-09-24_primer_toy_error_paths_probe.py", "2026-09-24_primer_toy_pin_mutation_check.py"]

L5502 = BASE[5501]
L5600 = BASE[5599]
L6120 = BASE[6119]
assert "StrictInt | StrictFloat]" in L5502 and "RecursionError" in L5600 and "bad_str" in L6120

MUTANTS = {
    # the delta's RecursionError catch reverted (the stated omission: only the probe pins it)
    "revert 5600": {5600: "    except (ValueError, KeyError, TypeError, binascii.Error) as exc:"},
    # booleans admitted: int(True) == 1, so `true` is a 201 again -- the 5502 comment says it is a 422
    "admit bool": {5502: L5502.replace("StrictInt | StrictFloat]", "StrictInt | StrictFloat | bool]")},
    # the pin itself disabled: bad_str still computed, no longer asserted
    "drop bad_str from 6120": {6120: L6120.replace("bad_extra, bad_str, ", "bad_extra, ")},
    # null admitted for every key: seed null accepted again, and n_samples null is a 500 again
    "admit None": {5502: L5502.replace("StrictInt | StrictFloat]", "StrictInt | StrictFloat | None]")},
    # a fraction ROUNDED rather than truncated: the primer says truncated; does anything check?
    "round not truncate": {5659: BASE[5658].replace("int(body.params.get(\"n_samples\", 512))", "round(body.params.get(\"n_samples\", 512))")},
}


def run(cmd, cwd):
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, env={"PATH": "/usr/bin:/bin", "TMPDIR": str(S / "tmp"), "HOME": str(Path.home())})
    tail = [l for l in (p.stdout + p.stderr).split("\n") if l.strip()][-1:] or [""]
    return p.returncode, tail[0][:110]


for name, edits in MUTANTS.items():
    root = S / f"m_{name.replace(' ', '_')}"
    shutil.rmtree(root, ignore_errors=True)
    (root / "notes").mkdir(parents=True)
    (root / "util/ad-hoc").mkdir(parents=True)
    lines = list(BASE)
    for n, text in edits.items():
        assert lines[n - 1] != text, (name, n)
        lines[n - 1] = text
    (root / REL).write_text("\n".join(lines), encoding="utf-8")
    for t in TOOLS:
        shutil.copy(S / "after/util/ad-hoc" / t, root / "util/ad-hoc" / t)
    h = run([sys.executable, "util/ad-hoc/2026-08-13_run_primer_examples.py", "--doc", REL, "--venv", VENV], root)
    pr = run([f"{VENV}/bin/python", "util/ad-hoc/2026-09-24_primer_toy_error_paths_probe.py", REL], root)
    mc = run([sys.executable, "util/ad-hoc/2026-09-24_primer_toy_pin_mutation_check.py", "--venv", VENV, "--scratch", str(root / "mc")], root)
    fmt = lambda r: ("NOTICED " if r[0] else "missed  ") + r[1]
    print(f"{name}\n   harness : {fmt(h)}\n   probe   : {fmt(pr)}\n   mut.chk : {fmt(mc)}")
    shutil.rmtree(root, ignore_errors=True)
