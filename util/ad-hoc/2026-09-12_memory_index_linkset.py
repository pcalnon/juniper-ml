#!/usr/bin/env python3
"""
Snapshot and compare MEMORY.md's link SET, so a compaction cannot silently drop pointers.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-12
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: [[reference_memory_index_is_recoverable_from_transcripts]],
         [[reference_memory_md_concurrent_edits]], [[reference_vacuous_pass_check_class]]

Why this exists
---------------
An earlier condensation of this index DROPPED 38 pointers and nobody noticed, because
the natural instrument is a *count* (links before vs after) and count deltas are
set-blind: "+5 links" is equally consistent with "5 added, 0 dropped" and with
"K dropped, 5+K added". The only sound gate is a SET comparison.

Usage
-----
    ... 2026-09-12_memory_index_linkset.py snapshot before.txt     # dump the link set
    ... 2026-09-12_memory_index_linkset.py compare before.txt      # diff live vs snapshot
    ... 2026-09-12_memory_index_linkset.py orphans                 # files on disk with no pointer
    ... 2026-09-12_memory_index_linkset.py unreachable             # no pointer AND no inbound link

Reachability has three levels, and only the third is actually lost: an index row; an
inbound ``[[slug]]`` / ``(file.md)`` reference from another memory; or neither. The
``orphans`` view conflates the first two, so use ``unreachable`` to pick retirement
candidates -- on 2026-09-15 that was 36 of 89 row-less files.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

MEM = Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory")
INDEX = MEM / "MEMORY.md"
# Match the TARGET only, never the title. A title may itself contain brackets --
# "[juniper-data needs [api] extra](...)" is real -- and a title-anchored pattern
# silently skips those links, which would make this gate blind to exactly the
# pointers it exists to protect.
LINK = re.compile(r"\]\(([^)\s]+\.md)\)")


def link_set(text: str) -> set[str]:
    return {m.group(1) for m in LINK.finditer(text)}


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cmd = sys.argv[1]
    live = link_set(INDEX.read_text(encoding="utf-8"))

    if cmd == "snapshot":
        out = Path(sys.argv[2])
        out.write_text("\n".join(sorted(live)) + "\n", encoding="utf-8")
        print(f"{len(live)} links -> {out}  ({INDEX.stat().st_size} bytes)")
        return 0

    if cmd == "compare":
        before = set(Path(sys.argv[2]).read_text(encoding="utf-8").split())
        dropped = sorted(before - live)
        added = sorted(live - before)
        print(f"before={len(before)}  after={len(live)}  size={INDEX.stat().st_size} bytes")
        print(f"ADDED   ({len(added)}): " + (", ".join(added) or "none"))
        print(f"DROPPED ({len(dropped)}): " + (", ".join(dropped) or "none"))
        if dropped:
            print("\nFAIL: the compaction dropped the pointers listed above.")
            return 1
        print("\nOK: no pointer was dropped (before is a subset of after).")
        return 0

    if cmd == "unreachable":
        # A memory with no index row is still findable if another memory points at it
        # with [[slug]] or (file.md). "Unreachable" means NEITHER -- no index row and no
        # inbound link, so nothing can surface it. Those are the retirement candidates.
        on_disk = {p.name for p in MEM.glob("*.md")} - {"MEMORY.md"}
        texts = {p.name: p.read_text(encoding="utf-8", errors="ignore") for p in MEM.glob("*.md") if p.name != "MEMORY.md"}
        rows = []
        for name in sorted(on_disk - live):
            slug = name[:-3]
            inbound = sum(1 for other, t in texts.items() if other != name and (f"[[{slug}]]" in t or f"({name})" in t))
            if inbound == 0:
                rows.append(name)
        for name in rows:
            print(name)
        print(f"\n{len(rows)} unreachable of {len(on_disk)} on disk ({len(on_disk - live)} have no index row; the rest are reachable by inbound link)", file=sys.stderr)
        return 0

    if cmd == "orphans":
        on_disk = {p.name for p in MEM.glob("*.md")} - {"MEMORY.md"}
        missing_target = sorted(t for t in live if not (MEM / t).is_file())
        unlinked = sorted(on_disk - live)
        print(f"memory files on disk: {len(on_disk)}   distinct links: {len(live)}")
        print(f"\nDANGLING links (pointer with no file) ({len(missing_target)}):")
        for t in missing_target:
            print(f"    {t}")
        print(f"\nUNLINKED files (file with no pointer) ({len(unlinked)}):")
        for t in unlinked:
            print(f"    {t}")
        return 0

    print(f"unknown command {cmd!r}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
