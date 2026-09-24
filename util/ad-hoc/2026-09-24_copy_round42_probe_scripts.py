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
This copies each lane's OWN scripts (`*.py`, `*.sh`, `*.bash` at the lane root, plus a `scripts/`
subdirectory where the lane used one) into util/ad-hoc/2026-09-24_round42_probes/round3-4_<lane>/.
It deliberately skips the extracted repository trees the lanes built beside them; those are copies
of code already in git.

The rounds 1-2 probes of the predecessor session were copied the same way into the sibling
`*-v428r2`, `*-v678`, `*-v678c` and `*-d428fix` directories.

Usage: python3 2026-09-24_copy_round42_probe_scripts.py
"""

import shutil
import sys
from pathlib import Path

SRC = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42")
DST = Path(__file__).resolve().parent / "2026-09-24_round42_probes"
LANES = ["data428-laneA1", "data428-laneA2", "data428-laneB", "ml-laneA", "ml-laneB", "primer-laneA", "primer-laneB"]
EXTS = {".py", ".sh", ".bash"}


def main() -> int:
    copied, total = 0, 0
    for lane in LANES:
        roots = [SRC / lane]
        if (SRC / lane / "scripts").is_dir():
            roots.append(SRC / lane / "scripts")
        for root in roots:
            for f in sorted(root.iterdir()):
                if f.is_file() and f.suffix in EXTS and f.stat().st_size < 200_000:
                    out = DST / f"round3-4_{lane}" / f.name
                    out.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, out)
                    copied += 1
                    total += f.stat().st_size
    print(f"{copied} files, {round(total / 1024)} KB -> {DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
