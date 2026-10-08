#!/usr/bin/env python3
"""Apply exact-string edits from a JSON list to one file; refuse unless each anchor occurs once.

Project:      Juniper
Sub-Project:  juniper-ml (ad-hoc evaluation helper for juniper-data)
Application:  Cursor-fleet flood #3 evaluation (agent data-docs)
Author:       Paul Calnon (generated with Claude Code)
Version:      0.1.0
License:      MIT License

Single-use. Builds the "no #454" variant of the juniper-data docs consolidation (the telemetry
hunks removed) so a reverse patch can be offered if the owner declines juniper-data#454.

    python3 util/ad-hoc/2026-10-08_data_docs_apply_edits.py FILE EDITS.json

EDITS.json: [[old, new], ...]. An `old` that is a substring of its `new` is refused (it would
re-apply on a second run), as is an `old` that does not occur exactly once.
"""

import json
import sys


def main() -> int:
    path, edits_path = sys.argv[1], sys.argv[2]
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    with open(edits_path, encoding="utf-8") as fh:
        edits = json.load(fh)
    for old, new in edits:
        if old in new:
            raise SystemExit(f"non-idempotent edit (old is a substring of new): {old[:80]!r}")
        count = text.count(old)
        if count != 1:
            raise SystemExit(f"anchor occurs {count} times: {old[:80]!r}")
        text = text.replace(old, new)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"{path}: applied {len(edits)} edit(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
