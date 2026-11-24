"""Append the republish job to publish.yml, splicing in the PyPI job's own dist-check and PyPI-check blocks verbatim.

Usage: python3 -I assemble_republish.py PUBLISH_YML PARTS_YML
Refuses when publish.yml already has a republish job, or a marker or block is not found exactly where expected.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- one-off (juniper-cascor#763 and its follow-up #767: one artifact for TestPyPI and PyPI)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-15_cascor_one_artifact_publish_edits.py, util/ad-hoc/2026-11-15_cascor_one_artifact_followup_tree.py
"""

import re
import sys
from pathlib import Path

STEP_LINE = re.compile(r"^      (?:- |# )")


def block_at(lines: list[str], start: int) -> str:
    """The template block starting at a marker comment line: through its step, up to the next step-level line."""
    first = next(j for j in range(start, len(lines)) if lines[j].startswith("      - "))
    end = first + 1
    while end < len(lines) and not STEP_LINE.match(lines[end]) and not (lines[end].strip() and len(lines[end]) - len(lines[end].lstrip(" ")) <= 2):
        end += 1
    return "".join(lines[start:end]).rstrip("\n") + "\n"


def main() -> int:
    publish, parts = Path(sys.argv[1]), Path(sys.argv[2])
    text = publish.read_text(encoding="utf-8")
    if "\n  republish:\n" in text:
        print("REFUSED: publish.yml already has a republish job")
        return 1
    lines = text.splitlines(keepends=True)
    t4_marker = "      # One-artifact publish template, step 4: before every upload.\n"
    t5_marker = "      # One-artifact publish template, step 5, after the PyPI upload: PyPI must serve the same sha256.\n"
    t4_at = [i for i, line in enumerate(lines) if line == t4_marker]
    t5_at = [i for i, line in enumerate(lines) if line == t5_marker]
    if len(t4_at) != 2 or len(t5_at) != 1:
        print(f"REFUSED: found {len(t4_at)} dist-check markers (want 2) and {len(t5_at)} PyPI-check markers (want 1)")
        return 1
    t4 = block_at(lines, t4_at[1])  # the PyPI job's copy
    t5 = block_at(lines, t5_at[0])
    job = parts.read_text(encoding="utf-8")
    if job.count("@@T4@@\n") != 1 or job.count("@@T5@@\n") != 1:
        print("REFUSED: the parts file must hold each placeholder once")
        return 1
    job = job.replace("@@T4@@\n", t4).replace("@@T5@@\n", t5)
    publish.write_text(text.rstrip("\n") + "\n" + job, encoding="utf-8")
    print(f"appended the republish job ({len(job.splitlines())} lines) with the dist check ({len(t4.splitlines())} lines) and the PyPI check ({len(t5.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
