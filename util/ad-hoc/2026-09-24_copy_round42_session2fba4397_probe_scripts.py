#!/usr/bin/env python3
"""
Preserve the probe scripts of session 2fba4397's round-42 validation lanes, which exist only on tmpfs.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register provenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use copier
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

The sibling util/ad-hoc/2026-09-24_copy_round42_probe_scripts.py (juniper-ml#2081) preserved the probes
of session 8f86dec2's lanes and is hard-coded to that session's scratchpad. Session 2fba4397 ran six
more lanes: the two pre-PR rounds of the second register and primer fix-forward (juniper-ml#2088), and
round 1 of juniper-data#438's fix-forward. Their reports, archived verbatim in
reports/2026-09-24_defect-register-round-42/, cite their scripts by paths under this session's scratchpad
on tmpfs. The handoff validation of 2026-09-24 flagged those 196 files as the only copies. On 2026-09-25
the same was true of the lanes that validated the session's two handoffs (its own, and the consolidated
one of both round-42 lanes), so their six probe directories were added; a re-run skips a file an earlier
run already copied byte-for-byte, and still refuses one that differs.

This copies each lane's own Python scripts (`*.py` at the lane root, plus its `scripts/` subdirectory)
into util/ad-hoc/2026-09-24_round42_probes/<report stem>/, by the same rules as the sibling: shell runners
and extracted trees are not kept, and nothing over 200 KB is copied. A lane whose scratch directory is
absent is skipped. `--lint` runs the repo's pre-commit hooks over what was copied.

Usage: python3 util/ad-hoc/2026-09-24_copy_round42_session2fba4397_probe_scripts.py [--lint]
"""

import shutil
import subprocess
import sys
from pathlib import Path

SRC = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad")
DST = Path(__file__).resolve().parent / "2026-09-24_round42_probes"
# Scratch lane directory -> the directory it is preserved as, named after the report it backs.
LANES = {
    "r42b/laneA": "register-fixforward2-round1-laneA",
    "r42b/laneB": "register-fixforward2-round1-laneB",
    "r42b2/laneA": "register-fixforward2-round2-laneA",
    "r42b2/laneB": "register-fixforward2-round2-laneB",
    "r42d/laneA": "data438-fixforward-round1-laneA",
    "r42d/laneB": "data438-fixforward-round1-laneB",
    # Added 2026-09-25: the lanes that validated this session's two handoffs. Their reports ship in the
    # consolidation PR (branch docs/handoff-round42-consolidated) and cite these probes by scratch path.
    "hv1/laneF": "handoff-2fba4397-round1-laneF",
    "hv2/laneF2": "handoff-2fba4397-round2-laneF",
    "hv3/laneD": "handoff-2fba4397-round3-laneF",
    "hc1/laneF": "handoff-consolidated-round1-laneF",
    "hc2/laneF": "handoff-consolidated-round2-laneF",
    "hc2/laneP": "handoff-consolidated-round2-laneP",
    "hc3/laneF": "handoff-consolidated-round3-laneF",
    "hc3/laneP": "handoff-consolidated-round3-laneP",
}
EXTS = {".py"}


def copied_files() -> "list[Path]":
    return sorted(p for dest in LANES.values() for p in (DST / dest).rglob("*") if p.is_file())


def lint() -> int:
    """Run the repo's pre-commit hooks over every file this copier preserved (`--lint`)."""
    files = [str(p.relative_to(DST.parents[1])) for p in copied_files()]
    proc = subprocess.run(["/opt/miniforge3/bin/pre-commit", "run", "--files", *files], cwd=DST.parents[1], capture_output=True, text=True)
    for line in proc.stdout.split("\n"):
        if "Failed" in line or line.startswith(("- hook id", "  ")) or "files were modified" in line:
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
        n = 0
        for root in roots:
            for f in sorted(root.iterdir()):
                if f.is_file() and f.suffix in EXTS and f.stat().st_size < 200_000:
                    out = DST / dest / f.name
                    if out.exists():
                        if out.read_bytes() == f.read_bytes():
                            continue  # copied, byte-identical, by an earlier run
                        raise SystemExit(f"{out}: exists and differs from {f}; nothing more copied")
                    out.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(f, out)
                    copied += 1
                    n += 1
                    total += f.stat().st_size
        print(f"  {lane:12} -> {dest}: {n} files")
    print(f"{copied} files, {round(total / 1024)} KB -> {DST}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
