# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 6 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r6b.lTWETu/pyc_header.py
# Written by Lane 11-R6B (adversarial, on round 5's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round6.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R6B: read the worktree bytecode caches' headers (source mtime/size) against their sources and file mtimes."""

import datetime as dt
import os
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
A = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite/util/ad-hoc")
UTC = dt.timezone.utc
for pyc in sorted((A / "__pycache__").glob("*.pyc")):
    src = A / (pyc.name.split(".cpython-")[0] + ".py")
    with open(pyc, "rb") as fh:
        head = fh.read(16)
    flags = struct.unpack("<I", head[4:8])[0]
    smtime, ssize = struct.unpack("<II", head[8:16])
    st = os.stat(src) if src.exists() else None
    fresh = st is not None and int(st.st_mtime) & 0xFFFFFFFF == smtime and st.st_size & 0xFFFFFFFF == ssize
    print(
        f"{pyc.name}: written {dt.datetime.fromtimestamp(pyc.stat().st_mtime, UTC):%Y-%m-%dT%H:%M:%S.%f}Z; "
        f"compiled from source mtime {dt.datetime.fromtimestamp(smtime, UTC):%Y-%m-%dT%H:%M:%S}Z size {ssize}; "
        f"flags {flags}; valid for today's source: {fresh}"
    )
