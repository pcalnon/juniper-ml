#!/usr/bin/env python3
"""
Preserve the defect-register round-42 validators' probe scripts, which exist only on tmpfs.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register provenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use copier
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Every round-42 validation report names the probe scripts behind its measurements by their path in
a session scratchpad under /tmp, which is tmpfs and is reaped when the session or machine goes.
This copies each lane's OWN Python scripts (`*.py` at the lane root, plus a `scripts/`
subdirectory where the lane used one) into util/ad-hoc/2026-09-24_round42_probes/<dest>/, where
LANES names each lane's destination; a lane whose scratch directory is absent is skipped.
It deliberately skips the extracted repository trees the lanes built beside them (copies of code
already in git) and the lanes' shell runners (thin, environment-specific wrappers that do not pass
the repo's shellcheck hook). The copies are verbatim apart from the end-of-file newline the repo's
pre-commit hook adds.

The rounds 1-2 probes of the predecessor session were copied the same way into the sibling
`*-v428r2`, `*-v678`, `*-v678c` and `*-d428fix` directories.

Usage: python3 2026-09-24_copy_round42_probe_scripts.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42")
DST = Path(__file__).resolve().parent / "2026-09-24_round42_probes"
# Scratch lane directory -> the directory it is preserved as. The first seven kept a `round3-4_`
# prefix from when they were the only ones; later lanes are named after the report they back.
LANES = {
    **{lane: f"round3-4_{lane}" for lane in ["data428-laneA1", "data428-laneA2", "data428-laneB", "ml-laneA", "ml-laneB", "primer-laneA", "primer-laneB"]},
    "pr2074-laneA": "ml2074-round1-laneA",
    "pr2074-laneB": "ml2074-round1-laneB",
    "primer-r2-laneA": "primer-correction-round2-laneA",
    "primer-r2-laneB": "primer-correction-round2-laneB",
}
EXTS = {".py"}


def lint() -> int:
    """Run the repo's pre-commit hooks over every preserved file (`--lint`)."""
    files = sorted(str(p.relative_to(DST.parents[1])) for p in DST.rglob("*") if p.is_file())
    proc = subprocess.run(["/opt/miniforge3/bin/pre-commit", "run", "--files", *files], cwd=DST.parents[1], capture_output=True, text=True)
    for line in proc.stdout.splitlines():
        if "Failed" in line or "Passed" in line or line.startswith(("- hook id", "  ")) or "files were modified" in line:
            print(line)
    print(f"pre-commit over {len(files)} files: exit {proc.returncode}")
    return proc.returncode


def main() -> int:
    if "--lint" in sys.argv[1:]:
        return lint()
    copied, total = 0, 0
    for lane, dest in LANES.items():
        if not (SRC / lane).is_dir():
            print(f"  missing lane {lane}: skipped")
            continue
        roots = [SRC / lane]
        if (SRC / lane / "scripts").is_dir():
            roots.append(SRC / lane / "scripts")
        for root in roots:
            for f in sorted(root.iterdir()):
                if f.is_file() and f.suffix in EXTS and f.stat().st_size < 200_000:
                    out = DST / dest / f.name
                    out.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, out)
                    copied += 1
                    total += f.stat().st_size
    print(f"{copied} files, {round(total / 1024)} KB -> {DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
