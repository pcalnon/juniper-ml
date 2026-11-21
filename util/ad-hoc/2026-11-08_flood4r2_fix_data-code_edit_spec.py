#!/usr/bin/env python3
"""
Write the edit spec that applies the round-2 validators' findings to the juniper-data data-code carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 round 2: validator findings -> data-code carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/data-tests-lens/findings.json F1; tmp/flood4r2-val/data-claims-lens/findings.json F1

Usage:
  2026-11-08_flood4r2_fix_data-code_edit_spec.py <data-code worktree> <out edits.json>

tests-lens F1 is the validator's exact replacement: the allowed/rejected header test moves its clock to
``_START + 59.5``, where the rounded value (1) differs from both truncation (0) and the window (60). claims-lens F1
adds § Failed-Auth Throttle Retention to the CHANGELOG's list of changed sections; that sub-bullet is re-flowed at
the entry's own width (118, four-space continuation). The section itself arrives with the data-docs carrier and is
changed by the edit in apply_after_data_docs.json, not here. Applied with 2026-11-08_flood4r2_fix_apply_edits.py.
"""

from __future__ import annotations

import json
import sys
import textwrap
from pathlib import Path


def main(argv: list[str]) -> int:
    worktree, out = argv[1], Path(argv[2])
    header_test_old = (
        "        clock.now = _START + 0.4\n"
        "        allowed = client.get(\"/v1/datasets\")\n"
        "        rejected = client.get(\"/v1/datasets\")\n"
        "\n"
        "        assert allowed.status_code == 200\n"
        "        assert allowed.headers[\"X-RateLimit-Remaining\"] == \"0\"\n"
        "        assert allowed.headers[\"X-RateLimit-Reset\"] == \"60\"\n"
        "        assert rejected.status_code == 429\n"
        "        assert rejected.headers[\"Retry-After\"] == \"60\"\n"
        "        assert rejected.headers[\"X-RateLimit-Reset\"] == \"60\"\n"
    )
    header_test_new = (
        "        clock.now = _START + 59.5\n"
        "        allowed = client.get(\"/v1/datasets\")\n"
        "        rejected = client.get(\"/v1/datasets\")\n"
        "\n"
        "        assert allowed.status_code == 200\n"
        "        assert allowed.headers[\"X-RateLimit-Remaining\"] == \"0\"\n"
        "        assert allowed.headers[\"X-RateLimit-Reset\"] == \"1\"\n"
        "        assert rejected.status_code == 429\n"
        "        assert rejected.headers[\"Retry-After\"] == \"1\"\n"
        "        assert rejected.headers[\"X-RateLimit-Reset\"] == \"1\"\n"
    )
    changelog_old = (
        "  - `test_retry_after_rounds_up.py` pins it with a frozen clock, through `SecurityMiddleware`'s headers too. 11 of\n"
        "    its 20 tests fail on the old code. `docs/REFERENCE.md` (§ Rate-Limit Window, § Non-ASCII API Keys) and\n"
        "    `docs/DEVELOPER_CHEATSHEET.md` say how the wait is rounded.\n"
    )
    joined = " ".join(line.strip() for line in changelog_old.splitlines())[2:]
    fixed = joined.replace("(§ Rate-Limit Window, § Non-ASCII API Keys)", "(§ Rate-Limit Window, § Failed-Auth Throttle Retention, § Non-ASCII API Keys)")
    if fixed == joined:
        raise SystemExit("section list not found")
    # A no-break space keeps each "§ <section>" marker on the line of its section name; it is turned back after.
    wrapped = textwrap.wrap(fixed.replace("§ ", "§ "), width=118, initial_indent="  - ", subsequent_indent="    ", break_long_words=False, break_on_hyphens=False)
    changelog_new = "\n".join(wrapped).replace("§ ", "§ ") + "\n"
    edits = [
        {"id": "tests-F1", "file": "juniper_data/tests/unit/test_retry_after_rounds_up.py", "old": header_test_old, "new": header_test_new},
        {"id": "claims-F1-changelog", "file": "CHANGELOG.md", "old": changelog_old, "new": changelog_new},
    ]
    out.write_text(json.dumps({"worktree": worktree, "edits": edits}, indent=1) + "\n", encoding="utf-8")
    print(changelog_new, end="")
    print(f"line lengths: {[len(line) for line in changelog_new.splitlines()]}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
