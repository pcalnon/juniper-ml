#!/usr/bin/env python3
"""Lane C round 3: run the archiver's own credential-shape screen (2026-09-22_archive_consensus_reports.py
`screen`) over the WHOLE frozen record, header included (the archiver screens report bodies only), and over
the new round-3 header template. Prints hit COUNTS and line numbers, never the matched text."""
import importlib.util
import sys
from pathlib import Path

F = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C/frozen")
spec = importlib.util.spec_from_file_location("archive_consensus_reports", F / "util/ad-hoc/2026-09-22_archive_consensus_reports.py")
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)
for rel in ("notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md", "util/ad-hoc/2026-10-04_backup-phase-b-round3/RECORD_HEADER.md.in",
            "notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md", "notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md"):
    text = (F / rel).read_text(encoding="utf-8")
    hits = mod.screen(rel, text)
    lines = [i for i, ln in enumerate(text.splitlines(), 1) if mod.SECRET_SHAPED.search(ln) or mod.JWT.search(ln)]
    print(f"{rel}: screen() problems={len(hits)} shaped lines={lines[:12]}")
