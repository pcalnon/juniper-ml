#!/usr/bin/env python3
"""Plant a NameError in each changed II.11 route (one per copy) to prove the harness EXECUTES the line.

Scratch instrument for round-2 Lane B. Writes primer_ne_<route>.md next to this file.
"""
from pathlib import Path

HERE = Path(__file__).resolve().parent
text = (HERE / "primer_head.md").read_text(encoding="utf-8")
SITES = {
    "reuse": "                canonical_json(existing.metadata()), media_type=\"application/json\",",
    "create": "            canonical_json(dataset.metadata()), media_type=\"application/json\",\n            status_code=201,",
    "get": "        return Response(canonical_json(dataset.metadata()), media_type=\"application/json\", headers=headers)",
    "patch": "            canonical_json(dataset.metadata()), media_type=\"application/json\",\n            headers={\"ETag\": metadata_etag(dataset),",
}
for name, anchor in SITES.items():
    assert text.count(anchor) == 1, (name, text.count(anchor))
    (HERE / f"primer_ne_{name}.md").write_text(text.replace(anchor, anchor.replace("canonical_json(", "canonical_jsn(", 1), 1), encoding="utf-8")
    print("wrote", f"primer_ne_{name}.md")
