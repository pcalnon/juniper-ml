"""conventions: AGENTS.md header + line-length + deliverable locations.

Injects the repo's standing conventions as facts so a generated prompt cites them rather
than misremembering (the value R2.5 of the rubric checks against).
"""

from __future__ import annotations

import re
from pathlib import Path

_HEADER_FIELDS = ("Project", "Repository", "Author", "License", "Version", "Last Updated")


def probe(repo_root: str) -> dict:
    agents = Path(repo_root) / "AGENTS.md"
    header = {}
    if agents.exists():
        text = agents.read_text(encoding="utf-8", errors="replace")
        for field in _HEADER_FIELDS:
            match = re.search(r"^\*\*" + re.escape(field) + r"\*\*\s*[:：]\s*(.+)$", text, re.MULTILINE)
            if match:
                header[field] = match.group(1).strip()
    return {
        "status": "ok" if header else "partial",
        "agents_md_header": header,
        "line_length": 512,
        "deliverable_locations": {"notes": "notes/", "generated_prompts": "prompts/generated/"},
        "handoff_threshold": "95-99%",
    }
