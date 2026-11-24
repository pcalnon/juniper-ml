"""Apply validators' exact text fixes (old -> new, each old string unique) to the record update's files, in order.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (flood-4 session 11: the record update's fix pass)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (the record this pass updates);
    tmp/flood4/session11/record/val_claims/fixes.json and val_doc/ (the validators' fixes)

Each fixes file is a JSON list of {"id", "file", "old", "new"}. "file" names the target by key: a value containing
"changelog" (any case) is the CHANGELOG entry; anything else is the record. Every fix must find its old string exactly
once in the text as it stands after the fixes before it; otherwise nothing is written and the script exits 1.
--skip ID drops a fix (each skip is printed). --compare RECORD_PREVIEW [CHANGELOG_PREVIEW] checks the result against a
validator's preview copy. The inputs are never modified: the results go to --out.

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s11_apply_fixes.py --record IN.md --changelog IN.md --out DIR \
        FIXES.json [FIXES.json ...] [--skip ID ...] [--compare PREVIEW.md [PREVIEW.md]]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


def _key(name: str) -> str:
    return "changelog" if "changelog" in name.lower() else "record"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--record", required=True)
    parser.add_argument("--changelog", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--skip", action="append", default=[])
    parser.add_argument("--compare", nargs="+", default=[])
    parser.add_argument("--lenient", action="store_true", help="skip (and list) a fix whose old string is not found exactly once, instead of refusing")
    parser.add_argument("fixes", nargs="+")
    args = parser.parse_args(argv)
    texts = {"record": Path(args.record).read_text(encoding="utf-8"), "changelog": Path(args.changelog).read_text(encoding="utf-8")}
    applied = 0
    unapplied = []
    for fixes_path in args.fixes:
        for fix in json.loads(Path(fixes_path).read_text(encoding="utf-8")):
            if fix["id"] in args.skip:
                print(f"SKIPPED {fix['id']} ({fixes_path})")
                continue
            key = _key(fix.get("file") or fix.get("target") or "")
            count = texts[key].count(fix["old"])
            if count != 1 and args.lenient:
                unapplied.append(f"{fix['id']} ({key}, found {count}x)")
                continue
            if count != 1:
                print(f"REFUSED: {fix['id']} ({fixes_path}) finds its old string {count} times in the {key}; nothing written")
                return 1
            texts[key] = texts[key].replace(fix["old"], fix["new"], 1)
            applied += 1
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    names = {"record": Path(args.record).name, "changelog": Path(args.changelog).name}
    for key, text in texts.items():
        (out / names[key]).write_text(text, encoding="utf-8")
        print(f"{key}: {out / names[key]} sha256 {hashlib.sha256(text.encode('utf-8')).hexdigest()[:16]}")
    print(f"applied {applied} fixes")
    for item in unapplied:
        print(f"NOT APPLIED (lenient): {item}")
    for key, preview in zip(("record", "changelog"), args.compare, strict=False):
        same = texts[key] == Path(preview).read_text(encoding="utf-8")
        print(f"{key} == {preview}: {same}")
        if not same:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
