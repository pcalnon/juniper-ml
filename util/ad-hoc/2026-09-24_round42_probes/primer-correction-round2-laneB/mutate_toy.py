#!/usr/bin/env python3
"""Mutation-check the II.11 toy's ETag/body fix against both instruments.

Scratch instrument for round-2 Lane B. Writes mutated COPIES of the head primer into this
directory (never touches a repository), then the caller runs the toy probe and the Appendix D
harness on each. Each mutation must change exactly one line, found by exact text.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE / "primer_head.md"

MUTATIONS = {
    # M1: GET re-broken exactly as it was before the fix (JSONResponse re-renders the body).
    "m1_get_jsonresponse": (
        '        return Response(canonical_json(dataset.metadata()), media_type="application/json", headers=headers)',
        "        return JSONResponse(dataset.metadata(), headers=headers)",
    ),
    # M2: PATCH sends one trailing space more than the ETag hashes -- still valid JSON.
    "m2_patch_trailing_space": (
        '            canonical_json(dataset.metadata()), media_type="application/json",\n            headers={"ETag": metadata_etag(dataset), "Cache-Control": METADATA_CACHE_CONTROL, "Vary": "Accept"},',
        '            canonical_json(dataset.metadata()) + " ", media_type="application/json",\n            headers={"ETag": metadata_etag(dataset), "Cache-Control": METADATA_CACHE_CONTROL, "Vary": "Accept"},',
    ),
    # M3: create-reuse path sends a pretty-printed body (JSONResponse of the same dict).
    "m3_reuse_jsonresponse": (
        '            return Response(\n                canonical_json(existing.metadata()), media_type="application/json",',
        '            return JSONResponse(\n                existing.metadata(),',
    ),
}


def main() -> int:
    text = SRC.read_text(encoding="utf-8")
    for name, (old, new) in MUTATIONS.items():
        n = text.count(old)
        if n != 1:
            print(f"{name}: anchor found {n} times; refusing", file=sys.stderr)
            return 2
        out = HERE / f"primer_{name}.md"
        out.write_text(text.replace(old, new, 1), encoding="utf-8")
        print(f"wrote {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
