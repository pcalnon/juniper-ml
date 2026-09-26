#!/usr/bin/env python3
"""Lane A round 2: discriminating controls for the II.11 toy pins (harness + repo probe), my own mutants.

Each mutant edits named lines of a primer copy (head, or e2f87aae) in scratch, then runs:
  - the Appendix D harness (head's util/ad-hoc/2026-08-13_run_primer_examples.py) with the pinned venv;
  - the repo probe (head's util/ad-hoc/2026-09-24_primer_toy_error_paths_probe.py) with the venv's python.
Prints CAUGHT/MISSED for each.
"""
import subprocess
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b2/laneA")
HEAD = S / "head"
VENV = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/primer-venv"
VPY = VENV + "/bin/python"
HARNESS = HEAD / "util/ad-hoc/2026-08-13_run_primer_examples.py"
PROBE = HEAD / "util/ad-hoc/2026-09-24_primer_toy_error_paths_probe.py"
PRI_HEAD = HEAD / "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
PRI_BASE = S / "base/notes/primer_e2f87aae.md"
OUT = S / "mut"
OUT.mkdir(exist_ok=True)
ENV = {"TMPDIR": str(S / "tmp"), "PATH": "/usr/bin:/bin"}

LAX = "    params: dict[str, int | float] = Field(default_factory=dict)"
MUTANTS = [
    ("lax union on e2f87aae (no numeric-string arm)", PRI_BASE, {5502: LAX}),
    ("lax union on head", PRI_HEAD, {5502: LAX}),
    ("StrictBool admitted on head", PRI_HEAD, {5400: "from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictFloat, StrictInt",
                                               5502: "    params: dict[str, StrictInt | StrictFloat | StrictBool] = Field(default_factory=dict)"}),
    ("RecursionError catch reverted on head", PRI_HEAD, {5600: "    except (ValueError, KeyError, TypeError, binascii.Error) as exc:"}),
    ("bad_str dropped from the loop, lax union, head", PRI_HEAD, {5502: LAX, 6120: "    for response in (bad_enum, bad_extra, bad_query, bad_nan):"}),
    ("head unmutated (control)", PRI_HEAD, {}),
]


def harness(doc):
    p = subprocess.run(["python3", str(HARNESS), "--doc", str(doc), "--venv", VENV], capture_output=True, text=True, env=ENV)
    tail = [ln for ln in p.stdout.split("\n") if " passed" in ln or " failed" in ln]
    return p.returncode, tail[-1].strip() if tail else p.stdout[-200:]


def probe(doc):
    p = subprocess.run([VPY, str(PROBE), str(doc)], capture_output=True, text=True, env=ENV)
    bad = [ln.strip() for ln in p.stdout.split("\n") if "UNEXPECTED" in ln]
    return p.returncode, bad


for name, src, edits in MUTANTS:
    lines = src.read_text(encoding="utf-8").split("\n")
    for n, t in edits.items():
        assert lines[n - 1] != t, (name, n)
        lines[n - 1] = t
    doc = OUT / (name.replace(" ", "_").replace("(", "").replace(")", "").replace(",", "") + ".md")
    doc.write_text("\n".join(lines), encoding="utf-8")
    hrc, htail = harness(doc)
    prc, pbad = probe(doc)
    print(f"{name}\n   harness: {'MISSED (passes)' if hrc == 0 else 'CAUGHT'} -- {htail}\n   probe:   {'MISSED' if prc == 0 else 'CAUGHT'} -- {pbad}")
    doc.unlink()
