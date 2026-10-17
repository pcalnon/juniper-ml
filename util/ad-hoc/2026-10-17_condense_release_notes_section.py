#!/usr/bin/env python3
"""
Condense one section of a rendered release-notes file to the bold lead of each top-level entry.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-17
Status: ad-hoc — one-off (W1.13: the juniper-canopy 0.9.0 notes archive)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md (W1.13),
         util/ad-hoc/2026-09-12_ceremony_notes_preview.py (renders the input),
         util/release_train/ceremony.py (create_signed_commit / open_archive_pr)

Why this exists
---------------
juniper-canopy 0.9.0's rendered notes are ~103 KB, because its CHANGELOG ``[0.9.0]`` section is
(63 KB of it is the 33 ``### Fixed`` entries). The archive must reach juniper-ml ``main`` as a
GitHub-signed commit, and the only signed path is the GraphQL ``createCommitOnBranch`` mutation,
which carries the whole file base64-encoded in one request. Measured 2026-10-17 from turing: a
GraphQL request body of 130,000 bytes is accepted and one of 131,000 is refused (HTTP 499), and
``ceremony.py``'s ``create_signed_commit`` passes the base64 as ONE ``gh`` argument, which a Linux
runner caps at 128 KiB (``MAX_ARG_STRLEN``). So neither this host nor the CI ceremony can commit the
full file. The owner ruled (2026-10-17): condense ``### Fixed`` to one line per entry, link the
CHANGELOG for the full text, keep every other section verbatim.

What it does
------------
Within the named ``### <section>``, each top-level ``- `` entry (with its indented continuation and
sub-bullets) is replaced by ``- **<its bold lead>**`` on one line, and a note naming the CHANGELOG
link is inserted under the heading. An entry that does not open with a ``**bold**`` lead keeps its
first sentence instead. Everything outside the section is copied byte for byte, and the script
refuses (exit 1) if that is not so, or if the entry count changes.

Usage
-----
    python3 util/ad-hoc/2026-10-17_condense_release_notes_section.py \\
        --input <rendered notes> --output <archive path> --section Fixed \\
        --changelog-url https://github.com/pcalnon/juniper-canopy/blob/v0.9.0/CHANGELOG.md \\
        --version 0.9.0
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_BOLD_LEAD = re.compile(r"^- \*\*(.+?)\*\*")
_FIRST_SENTENCE = re.compile(r"^- (.+?[.!?])(\s|$)")


def split_section(text: str, section: str) -> tuple[str, str, str]:
    """Return (before, body, after) around ``### <section>``; body excludes the heading line."""
    heading = f"\n### {section}\n"
    start = text.find(heading)
    if start < 0:
        raise SystemExit(f"no '### {section}' heading in the input")
    body_start = start + len(heading)
    rest = text[body_start:]
    match = re.search(r"(?m)^(### |## |---$)", rest)
    end = body_start + (match.start() if match else len(rest))
    return text[: body_start], text[body_start:end], text[end:]


def entries(body: str) -> list[str]:
    """The top-level ``- `` entries of a section body, each with its continuation lines."""
    blocks: list[list[str]] = []
    for line in body.splitlines():
        if line.startswith("- "):
            blocks.append([line])
        elif blocks:
            blocks[-1].append(line)
    return ["\n".join(block).rstrip() for block in blocks]


def lead(entry: str) -> str:
    flat = " ".join(part.strip() for part in entry.splitlines() if part.strip())
    bold = _BOLD_LEAD.match(flat)
    if bold:
        return f"- **{bold.group(1).strip()}**"
    sentence = _FIRST_SENTENCE.match(flat)
    return f"- {sentence.group(1).strip()}" if sentence else flat


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--section", default="Fixed")
    ap.add_argument("--changelog-url", required=True)
    ap.add_argument("--version", required=True)
    args = ap.parse_args()

    text = args.input.read_text(encoding="utf-8")
    before, body, after = split_section(text, args.section)
    found = entries(body)
    leads = [lead(entry) for entry in found]
    note = (
        f"\n{len(found)} entries. Each line below is the entry's lead; the full text of every entry is in "
        f"[CHANGELOG.md `[{args.version}]`]({args.changelog_url}). This section is condensed so that the archive fits one "
        "GitHub-signed commit (owner ruling 2026-10-17); every other section is complete.\n\n"
    )
    condensed = before + note + "\n".join(leads) + "\n\n" + after
    out = condensed
    # Refuse unless only the section body changed and the entry count held.
    if not (out.startswith(before) and out.endswith(after)) or len(entries("\n".join(leads))) != len(found):
        print("REFUSED: the condensed output does not preserve the text outside the section, or the entry count changed")
        return 1
    args.output.write_text(out, encoding="utf-8")
    print(f"{args.section}: {len(found)} entries, {len(body.encode())} -> {len(chr(10).join(leads).encode())} bytes; file {len(text.encode())} -> {len(out.encode())} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
