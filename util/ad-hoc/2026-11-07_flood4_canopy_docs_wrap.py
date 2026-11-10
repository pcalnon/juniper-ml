#!/usr/bin/env python3
"""
Wrap the canopy flood-4 docs carrier's over-512-character lines and fix two MD038 code spans, without changing rendered prose.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 consolidation, canopy docs carrier (#790 CICD_MANUAL, #793 x4, #796 x3)

Usage: 2026-11-07_flood4_canopy_docs_wrap.py <docs worktree>

Each flagged line (MD013 at 512, from the pinned markdownlint-cli v0.48.0) is split at sentence
boundaries ('. ' outside code spans) into lines of at most 400 characters; a list item's
continuation lines are indented two spaces; a split that would start a block construct is refused.
Markdown joins the lines into the same paragraph, so the rendered text is unchanged.

MD038: markdownlint's --fix rewrites the code span `## ` (trailing space) to `##`, which changes
#793's statement of the header rule (juniper_ci_tools.lint_agents_md_header ends the header at a
line where `line.strip() == "---" or line.startswith("## ")`). Both sentences are reworded so the
space is stated in prose instead of inside a code span.
"""

import re
import sys
from pathlib import Path

LIMIT = 400
BLOCK_START = re.compile(r"^(\d+[.)] |[-*+] |#|>|\||=+\s*$|-+\s*$)")

REPHRASE = {
    "docs/ci_cd/CICD_MANUAL.md": [
        ("everything before the first line that is `---` or starts with `##`. It exits", "everything before the first line that is `---` or that starts an H2 heading (`##` followed by a space). It exits"),
        ("everything before the first line that is `---` or starts with `## `. It exits", "everything before the first line that is `---` or that starts an H2 heading (`##` followed by a space). It exits"),
    ],
    "docs/ci_cd/CICD_REFERENCE.md": [
        ("the block before the first `---` or `##` holds", "the block before the first `---` line or H2 heading holds"),
        ("the block before the first `---` or `## ` holds", "the block before the first `---` line or H2 heading holds"),
    ],
}

FILES = [
    "docs/ci_cd/CICD_MANUAL.md",
    "docs/ci_cd/CICD_REFERENCE.md",
    "docs/DEVELOPER_CHEATSHEET.md",
    "docs/QUICK_START.md",
    "docs/api/API_REFERENCE.md",
]


def split_points(line: str) -> list[int]:
    """Indices just after a sentence-ending '. ' that lies outside a code span."""
    points = []
    in_code = False
    for i, ch in enumerate(line):
        if ch == "`":
            in_code = not in_code
        elif ch == " " and not in_code and i > 0 and line[i - 1] == "." and i + 1 < len(line):
            points.append(i + 1)
    return points


def wrap(line: str) -> list[str]:
    indent = "  " if re.match(r"^[-*+] ", line) else ""
    points = [p for p in split_points(line) if not BLOCK_START.match(line[p:])]
    out: list[str] = []
    start = 0
    last_ok = None
    for p in points + [len(line) + 1]:
        candidate_len = p - 1 - start + (len(indent) if out else 0)
        if candidate_len > LIMIT and last_ok is not None:
            out.append((indent if out else "") + line[start : last_ok - 1])
            start = last_ok
        last_ok = p
    out.append((indent if out else "") + line[start:])
    return out


def main(argv: list[str]) -> int:
    root = Path(argv[1]).resolve()
    for rel in FILES:
        path = root / rel
        text = path.read_text(encoding="utf-8")
        for old, new in REPHRASE.get(rel, []):
            if old in text:
                assert text.count(old) == 1, (rel, old)
                text = text.replace(old, new)
                print(f"{rel}: MD038 rephrase applied: {new[:70]!r}...")
        lines = text.split("\n")
        result: list[str] = []
        for n, line in enumerate(lines, 1):
            if len(line) > 512:
                wrapped = wrap(line)
                assert " ".join(w.strip() for w in wrapped) == line.strip(), (rel, n)
                assert all(len(w) <= 512 for w in wrapped), (rel, n, [len(w) for w in wrapped])
                print(f"{rel}:{n}: {len(line)} chars -> {len(wrapped)} lines {[len(w) for w in wrapped]}")
                result.extend(wrapped)
            else:
                result.append(line)
        path.write_text("\n".join(result), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
