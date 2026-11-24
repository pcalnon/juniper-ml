#!/usr/bin/env python3
"""
Build the manifest 2026-11-07_flood4_close_carried.py reads from a carrier's fix-up manifest and the build manifest
before it, so that a draft the fix-up pass did not touch is closed with what the BUILD recorded about it.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 session 5: closing the drafts juniper-data#534 carried)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-07_flood4_close_carried.py (reads the manifest this writes)

Why this exists
A round-2 fix-up manifest records, for a draft the fix-up did not change, ``"taken": null, "fixes": null`` and the
reason "unchanged by this pass; see previous_manifest". The close tool renders a missing ``fixes`` as "nothing --
carried as drafted", which is false for a draft the build carried with fixes: the dry run for juniper-data#534 said so
of #522 and #524, both carried with fixes. This fills each such entry from the previous manifest.

Usage:
  2026-11-11_flood4r2_s5_merge_close_manifest.py <fix-up manifest.json> <previous manifest.json> <out.json>

For each ``carried`` entry of the fix-up manifest: when its ``taken`` and ``fixes`` are both null, the previous
manifest's entry for the same PR is used whole (the fix-up's ``outcome`` must equal it, or this refuses); otherwise the
fix-up's entry is used, with ``head_sha`` taken from the previous manifest when the fix-up's entry has none. A PR the
previous manifest lacks refuses. Reads both manifests, writes only <out.json>. Exit 0 = written; 1 = refused.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(__doc__)
        return 2
    fixup = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    previous = json.loads(Path(argv[2]).read_text(encoding="utf-8"))
    by_pr = {int(entry["pr"]): entry for entry in previous["carried"]}
    merged: list[dict] = []
    for entry in fixup["carried"]:
        number = int(entry["pr"])
        before = by_pr.get(number)
        if before is None:
            print(f"REFUSED: #{number} is not in the previous manifest")
            return 1
        if entry.get("taken") is None and entry.get("fixes") is None:
            if entry.get("outcome") != before.get("outcome"):
                print(f"REFUSED: #{number}: the fix-up says {entry.get('outcome')!r}, the previous manifest {before.get('outcome')!r}")
                return 1
            chosen = dict(before)
            source = "previous manifest"
        else:
            chosen = dict(entry)
            if not chosen.get("head_sha") and before.get("head_sha"):
                chosen["head_sha"] = before["head_sha"]
            source = "fix-up manifest"
        merged.append(chosen)
        print(f"#{number}: {chosen.get('outcome')}; taken {len(chosen.get('taken') or [])}, fixes {len(chosen.get('fixes') or [])}, " f"dropped {len(chosen.get('dropped') or [])}; head {str(chosen.get('head_sha'))[:8]} ({source})")
    out = Path(argv[3])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"carried": merged, "built_from": [argv[1], argv[2]]}, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"carried: {len(merged)} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
