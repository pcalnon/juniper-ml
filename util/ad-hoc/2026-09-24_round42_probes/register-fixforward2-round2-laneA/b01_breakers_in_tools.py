#!/usr/bin/env python3
"""Lane A round 2: which files in the delta hold a raw str.splitlines() line-breaker (besides \n)?

Reports, for each file in the head tree, split("\n") vs splitlines() counts and every breaker by line.
"""
from pathlib import Path
import sys

HEAD = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42b2/laneA/head")
FILES = [
    "util/ad-hoc/2026-09-24_register_round42_second_fixforward_corrections.py",
    "util/ad-hoc/2026-09-24_register_round42_second_fixforward.py",
    "util/ad-hoc/2026-09-24_register_primer_citation_census.py",
    "util/ad-hoc/2026-09-24_primer_toy_error_paths_probe.py",
    "util/ad-hoc/2026-09-24_primer_toy_pin_mutation_check.py",
    "util/ad-hoc/2026-09-24_archive_round42_reports.py",
    "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md",
    "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md",
    "reports/2026-09-24_defect-register-round-42/register-fixforward2-round1-laneA-reprobe.md",
    "reports/2026-09-24_defect-register-round-42/register-fixforward2-round1-laneB-refute.md",
]
BRK = "\r\x0b\x0c\x1c\x1d\x1e\x85  "
root = Path(sys.argv[1]) if len(sys.argv) > 1 else HEAD
for f in FILES:
    t = (root / f).read_text(encoding="utf-8")
    hits = [(i + 1, "U+%04X" % ord(c)) for i, line in enumerate(t.split("\n")) for c in line if c in BRK]
    print(f"{f}\n    split('\\n')={len(t.split(chr(10)))} splitlines()={len(t.splitlines())} breakers={hits}")
