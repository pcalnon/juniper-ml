"""
Check a claims lens's fixes.json against a carrier: every "old" occurs exactly once, and the fixes apply cleanly.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 27 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 claims lens of carrier r27 (juniper-canopy unit-lane :8100 connects)

Usage:
    python -I <this file> <fixes.json> <carrier dir> <output dir>

A fix's "file" is repo-relative (resolved under <carrier dir>/final/) or "texts/<name>" (resolved under <carrier dir>/).
The carrier is only read. For each file the fixes are applied in list order to an in-memory copy; each "old" must occur
exactly once in the copy as it stands when that fix is applied, and each "new" must then occur at least once. The
patched copies are written under <output dir>/patched/<same relative path>, with a unified diff per file in
<output dir>/patched.diff, and a JSON report to stdout. Exit 0 only when every fix applies.
"""

from __future__ import annotations

import difflib
import json
import sys
from pathlib import Path


def _resolve(carrier: Path, name: str) -> Path:
    return carrier / name if name.startswith("texts/") else carrier / "final" / name


def main() -> int:
    fixes_path, carrier, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    fixes = json.loads(fixes_path.read_text(encoding="utf-8"))
    originals: dict[str, str] = {}
    patched: dict[str, str] = {}
    results = []
    ok = True
    for fix in fixes:
        name = fix["file"]
        if name not in patched:
            originals[name] = _resolve(carrier, name).read_text(encoding="utf-8")
            patched[name] = originals[name]
        count = patched[name].count(fix["old"])
        applied = count == 1
        if applied:
            patched[name] = patched[name].replace(fix["old"], fix["new"], 1)
            applied = fix["new"] in patched[name]
        ok = ok and applied
        results.append({"id": fix["id"], "file": name, "old_occurrences": count, "applied": applied})
    diffs = []
    for name, text in patched.items():
        target = out / "patched" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        diffs.extend(difflib.unified_diff(originals[name].splitlines(keepends=True), text.splitlines(keepends=True), fromfile=f"a/{name}", tofile=f"b/{name}"))
    (out / "patched.diff").write_text("".join(diffs), encoding="utf-8")
    print(json.dumps({"all_applied": ok, "fixes": results}, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
