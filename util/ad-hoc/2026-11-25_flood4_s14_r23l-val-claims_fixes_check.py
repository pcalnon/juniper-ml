"""
Check a claims lens's fixes.json against carrier r23l: each "old" occurs exactly once, and all apply together.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — investigation (flood-4 session 14, claims lens r23l-val-claims)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23)

A fix's "file" is repo-relative (read from the carrier's final/ copy), or "texts/<name>" / "stamps.json" (read from
the carrier directory itself). Every fix of a file is applied in list order to one copy; each "old" must occur
exactly once in the carrier's file AND once at the point it is applied, and each "new" must occur in the result.
With --also, a second fixes list (another lens's) is applied after this one, minus the "ID:file" pairs --skip
names, so a conflict between the two lists shows up. Patched copies go under --out-dir; the carrier is only read.
A patched .py file must still compile and a patched .json file must still parse.

Usage: python3 -I <this file> --fixes FIXES.json --carrier <r23l dir> --out-dir DIR [--also OTHER.json] [--skip ID:file ...]
Exit: 0 when every fix applies; 1 otherwise.
"""

import argparse
import json
from pathlib import Path


def _source(carrier: Path, name: str) -> Path:
    if name.startswith("texts/") or name == "stamps.json":
        return carrier / name
    return carrier / "final" / name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--fixes", required=True, type=Path)
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--out-dir", required=True, type=Path)
    parser.add_argument("--also", type=Path)
    parser.add_argument("--skip", nargs="*", default=[])
    args = parser.parse_args()
    fixes = [dict(fix, list="mine") for fix in json.loads(args.fixes.read_text(encoding="utf-8"))]
    if args.also is not None:
        skip = set(args.skip)
        fixes += [dict(fix, list="also") for fix in json.loads(args.also.read_text(encoding="utf-8")) if f"{fix['id']}:{fix['file']}" not in skip]
    originals: dict[str, str] = {}
    patched: dict[str, str] = {}
    failures = 0
    for index, fix in enumerate(fixes):
        name = fix["file"]
        if name not in originals:
            originals[name] = _source(args.carrier, name).read_text(encoding="utf-8")
            patched[name] = originals[name]
        in_original = originals[name].count(fix["old"])
        at_apply = patched[name].count(fix["old"])
        ok = in_original == 1 and at_apply == 1
        if ok:
            patched[name] = patched[name].replace(fix["old"], fix["new"], 1)
        else:
            failures += 1
        print(f"{'OK  ' if ok else 'FAIL'} {fix['list']:4} #{index:02d} {fix['id']:8} {fix.get('severity', ''):6} {name}  old in carrier x{in_original}, at apply x{at_apply}")
    for fix in fixes:
        if fix["new"] and fix["new"] not in patched[fix["file"]]:
            failures += 1
            print(f"FAIL {fix['list']} {fix['id']} {fix['file']}: its new text is not in the patched result")
    for name, text in patched.items():
        out = args.out_dir / name
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        if name.endswith(".py"):
            try:
                compile(text, name, "exec")
            except SyntaxError as exc:
                failures += 1
                print(f"FAIL {name}: the patched file does not compile: {exc}")
        if name.endswith(".json"):
            try:
                json.loads(text)
            except ValueError as exc:
                failures += 1
                print(f"FAIL {name}: the patched file does not parse: {exc}")
    print(f"fixes={len(fixes)} files={len(patched)} failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
