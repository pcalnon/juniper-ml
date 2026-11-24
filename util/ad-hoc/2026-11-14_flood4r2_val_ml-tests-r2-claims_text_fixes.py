"""
Verify the claims lens's text fixes for the ml-tests round-2 carrier and preview them on the rendered texts
(claims lens, session 8).

Reads <scratch>/text_fixes.json, a list of {"id", "finding", "file", "old", "new"[, "op"]} where "file" is
TEMPLATE/<name> (the carrier's tmp/flood4r2/ml-tests/r2/templates/<name>), DELIVERABLES/<name> (that directory's
<name>), MANIFEST/carried/<pr>/<field> (a string or list-of-strings field of manifest.json's carried entry) or
COPY/<repo path> (the carrier's file). For each: counts the occurrences of "old" (it must be exactly 1; an "append"
op needs none) and, for a TEMPLATE fix, also in the rendered text of --rendered. Writes <scratch>/text_fixes_check.json
and, with --preview, copies of the rendered texts with every TEMPLATE fix applied under <scratch>/texts_fixed/.
Read-only on the carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: flood-4 round-2 disposition, ml-tests carrier validation (claims lens)
"""

import argparse
import json
import sys
from pathlib import Path

SCRATCH_REL = "tmp/flood4r2/ml-tests/r2"


def target_text(carrier: Path, manifest: dict, spec: str):
    kind, _, rest = spec.partition("/")
    if kind == "TEMPLATE":
        return (carrier / SCRATCH_REL / "templates" / rest).read_text(encoding="utf-8")
    if kind == "DELIVERABLES":
        return (carrier / SCRATCH_REL / rest).read_text(encoding="utf-8")
    if kind == "COPY":
        return (carrier / rest).read_text(encoding="utf-8")
    if kind == "MANIFEST":
        _, pr, field = rest.split("/")
        entry = next(e for e in manifest["carried"] if str(e["pr"]) == pr)
        value = entry[field]
        return value if isinstance(value, str) else "\n".join(value)
    raise ValueError(spec)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify and preview the text fixes.")
    parser.add_argument("--carrier", required=True, type=Path)
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--rendered", type=Path, help="a landing's <out>/texts directory")
    parser.add_argument("--preview", action="store_true")
    args = parser.parse_args()
    with (args.carrier / SCRATCH_REL / "manifest.json").open() as handle:
        manifest = json.load(handle)
    with (args.scratch / "text_fixes.json").open() as handle:
        fixes = json.load(handle)
    rows = []
    bad = 0
    previews: dict = {}
    for fix in fixes:
        text = target_text(args.carrier, manifest, fix["file"])
        count = text.count(fix["old"]) if fix.get("op") != "append" else None
        row = {"id": fix["id"], "file": fix["file"], "occurrences": count}
        ok = fix.get("op") == "append" or count == 1
        if fix["file"].startswith("TEMPLATE/") and args.rendered:
            name = fix["file"].split("/", 1)[1]
            rendered_path = args.rendered / name
            rendered = previews.get(name, rendered_path.read_text(encoding="utf-8"))
            row["occurrences_in_rendered"] = rendered.count(fix["old"])
            ok = ok and row["occurrences_in_rendered"] == 1
            # The preview holds the recommended fixes only; an "optional" one is checked but not applied.
            previews[name] = rendered if fix.get("optional") else rendered.replace(fix["old"], fix["new"], 1)
        if fix.get("also_apply_to"):
            other = target_text(args.carrier, manifest, fix["also_apply_to"])
            row["occurrences_in_also_apply_to"] = other.count(fix["old"])
            ok = ok and row["occurrences_in_also_apply_to"] == 1
        row["ok"] = ok
        bad += 0 if ok else 1
        rows.append(row)
        print(json.dumps(row))
    if args.preview and previews:
        out = args.scratch / "texts_fixed"
        out.mkdir(exist_ok=True)
        for name, text in previews.items():
            (out / name).write_text(text, encoding="utf-8")
    with (args.scratch / "text_fixes_check.json").open("w") as handle:
        json.dump({"rows": rows, "bad": bad}, handle, indent=1)
    print(f"{len(rows)} fixes; not exactly once: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
