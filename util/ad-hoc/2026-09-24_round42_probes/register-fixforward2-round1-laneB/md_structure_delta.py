#!/usr/bin/env python3
"""Lane B: run head's markdown structure screen (the one util/markdown_structure_delta.py gates on) over
main's and head's copies of the three changed markdown files, and report the per-file delta."""
import importlib.util
from pathlib import Path

S = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("msc", S / "head/util/ad-hoc/2026-09-05_markdown_structure_check.py")
screen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)
for rel in (
    "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md",
    "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md",
    "docs/REFERENCE.md",
):
    before = screen.check(S / "main" / rel)
    after = screen.check(S / "head" / rel)
    print(f"{rel.split('/')[-1][:60]:62} main={len(before)} head={len(after)} {'REGRESSED' if len(after) > len(before) else 'ok'}")
    for p in after[:5]:
        print("   ", str(p)[:200])
