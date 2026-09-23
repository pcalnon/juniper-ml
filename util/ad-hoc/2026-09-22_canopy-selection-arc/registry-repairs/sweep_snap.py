"""Sweep the canopy worktree for present-tense claims of the sidebar enabled[0] snap (item 7c).

Prints every hit of the brief's patterns plus snap word-forms, grouped by file, with
variable-name uses (``snap = ...``, ``for snap in``) filtered out. Scratch analysis only.
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(sys.argv[1])
SCOPES = ["src", "docs", "notes", "README.md", "AGENTS.md", "conf", "util", "CHANGELOG.md"]
PATTERN = re.compile(r"enabled\[0\]|\bsnap(s|ped|ping)?\b|first compatible|\blands? on\b", re.IGNORECASE)
VARIABLE = re.compile(r"\b(snap|snaps|pre_snap|demo_snap|not_snap)\s*(=|\.|\[|\bin\b)|for\s+(i,\s*)?snap\b|var snaps|\"snap boom\"|snaps = \[\]|_auto_snap|auto-snap|Auto-snap", re.IGNORECASE)

hits: dict[str, list[tuple[int, str]]] = {}
for scope in SCOPES:
    base = ROOT / scope
    paths = [base] if base.is_file() else sorted(p for p in base.rglob("*") if p.is_file())
    for path in paths:
        if path.suffix not in {".py", ".md", ".yaml", ".yml", ".txt", ".bash", ".sh", ".json", ".js", ".css", ".toml", ""}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            if PATTERN.search(line) and not VARIABLE.search(line):
                hits.setdefault(str(path.relative_to(ROOT)), []).append((lineno, line.strip()[:220]))

for rel in sorted(hits):
    print(f"== {rel} ({len(hits[rel])})")
    for lineno, line in hits[rel]:
        print(f"  {lineno}: {line}")
