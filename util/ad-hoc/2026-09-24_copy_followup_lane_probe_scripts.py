#!/usr/bin/env python3
"""
Preserve the round-42 follow-up lane's validator probe scripts, which exist only on tmpfs.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register provenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use copier
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

The follow-up lane of defect-register round 42 (session bc31e993) validated juniper-cascor#686 and
#688, juniper-canopy#683, and the bytes-compare trio (juniper-ml#2086, juniper-data#440,
juniper-cascor#689). Its four validation reports, archived verbatim in
reports/2026-09-24_defect-register-round-42/, cite their probes by paths in that session's
scratchpad under /tmp, which is tmpfs and is reaped when the session or machine goes.

This copies each lane's OWN Python scripts (`*.py` at the lane root, plus the lane's `probes/`
subdirectory) into util/ad-hoc/2026-09-24_round42_probes/<dest>/, the directory juniper-ml#2081
created for the rest of round 42's probes, and in its naming scheme (the report stem, then the
scratch directory). It skips, as #2081's copier does, the extracted repository trees and the
shell runners, plus four whole-file copies of repository code that the lanes kept beside their
probes (EXCLUDE). The copies are verbatim apart from the end-of-file newline the repo's
pre-commit hook adds.

Usage: python3 2026-09-24_copy_followup_lane_probe_scripts.py [--lint]
"""

import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad")
DST = Path(__file__).resolve().parent / "2026-09-24_round42_probes"
# Scratch lane directory -> the directory it is preserved as, named after the report it backs.
LANES = {
    "v686": "cascor686-v686",
    "v683": "canopy683-v683",
    "v688": "cascor688-v688",
    "vbytes": "bytes-compare-ml2086-data440-cascor689-vbytes",
}
# Copies of repository code, not probes: two of canopy's dashboard_manager.py, one of its main.py,
# and one of juniper-data's generators route. Git already holds each at its commit.
EXCLUDE = {"canopy_dm_5907713b.py", "canopy_dm_e9053227.py", "canopy_main_5907713b.py", "jd_generators_route.py"}
EXTS = {".py"}


def lint() -> int:
    """Run the repo's pre-commit hooks over every file this copier preserved (`--lint`)."""
    files = sorted(str(p.relative_to(DST.parents[1])) for dest in LANES.values() for p in (DST / dest).rglob("*") if p.is_file())
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
        if (SRC / lane / "probes").is_dir():
            roots.append(SRC / lane / "probes")
        for root in roots:
            for f in sorted(root.iterdir()):
                if f.is_file() and f.suffix in EXTS and f.name not in EXCLUDE and f.stat().st_size < 200_000:
                    out = DST / dest / f.name
                    if out.exists() and root != SRC / lane:
                        print(f"  name clash {f.name} in {lane}: the lane-root copy is kept")
                        continue
                    out.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, out)
                    copied += 1
                    total += f.stat().st_size
    print(f"{copied} files, {round(total / 1024)} KB -> {DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
