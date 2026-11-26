"""
Derive the r27-val-code2 lens's fixes.json from (carrier file, validated patched file) pairs, then check it: every "old"
occurs exactly once in the carrier's file, and applying the fixes in order reproduces the validated file byte for byte.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 replacement code lens r27-val-code2

Usage:
    python <this file> <spec.json> <out fixes.json> <out check.json>
spec.json: a list of {"id", "severity", "file" (repo-relative), "carrier" (path of the carrier's copy),
"patched" (path of the validated, patched copy), "why"}. Each pair must differ by insertions only; each inserted run
becomes one fix whose "old" is the shortest run of preceding whole lines (at least one) that is unique in the
carrier's file, and whose "new" is that run plus the inserted lines.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import sys
from pathlib import Path


def derive(carrier: str, patched: str) -> list[tuple[str, str]]:
    a, b = carrier.splitlines(keepends=True), patched.splitlines(keepends=True)
    pairs = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if tag != "insert":
            raise SystemExit(f"not an insertion-only change: {tag} at carrier lines {i1 + 1}-{i2}")
        for k in range(1, i1 + 1):
            old = "".join(a[i1 - k : i1])
            if carrier.count(old) == 1:
                pairs.append((old, old + "".join(b[j1:j2])))
                break
        else:
            raise SystemExit(f"no unique context before carrier line {i1 + 1}")
    return pairs


def main() -> int:
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    fixes, checks = [], []
    for entry in spec:
        carrier = Path(entry["carrier"]).read_text(encoding="utf-8")
        patched = Path(entry["patched"]).read_text(encoding="utf-8")
        text = carrier
        for n, (old, new) in enumerate(derive(carrier, patched), 1):
            fixes.append({"id": entry["id"] if n == 1 else f"{entry['id']}.{n}", "severity": entry["severity"], "file": entry["file"], "old": old, "new": new, "why": entry["why"]})
            assert carrier.count(old) == 1, (entry["id"], "old not unique in the carrier file")
            text = text.replace(old, new, 1)
        checks.append({"id": entry["id"], "file": entry["file"], "reproduces_validated_file": text == patched, "sha256_after_fixes": hashlib.sha256(text.encode("utf-8")).hexdigest(), "sha256_validated": hashlib.sha256(patched.encode("utf-8")).hexdigest()})
    Path(sys.argv[2]).write_text(json.dumps(fixes, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    Path(sys.argv[3]).write_text(json.dumps(checks, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(checks, indent=1))
    return 0 if all(c["reproduces_validated_file"] for c in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
