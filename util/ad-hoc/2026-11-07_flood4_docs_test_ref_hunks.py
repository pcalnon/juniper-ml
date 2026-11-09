"""
List every flood-4 docs draft hunk that lands in docs/REFERENCE.md's `## Test Suite Reference` section.

That section (which holds `### Running every suite` and the per-suite entries) belongs to the tests
carrier, so the docs carrier left any hunk there to it. For each draft: its head (refs/flood4/pr/<N>,
checked against GitHub's headRefOid), its merge-base with origin/main, the section's line range in the
draft's BASE copy of REFERENCE.md, and each `git diff -U0` hunk whose old range (or insertion point)
falls inside it. Writes every matching hunk verbatim to `<out>` (text) and prints a one-line summary
per draft. Read-only on git.

Usage: python3 util/ad-hoc/2026-11-07_flood4_docs_test_ref_hunks.py <out.log> N [N ...]

Write the output as .log, not .txt: juniper-check-doc-links scans .md/.markdown/.rst/.txt under tmp/
too, and the drafts' hunks carry anchors that exist only in the docs carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — one-off (flood-4 tests carrier build, the docs carrier's hand-off)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: HANDOFF_2026-11-06_open-pr-sweep-triaged-owner-rulings-consolidation-next.md (flood-4 consolidation)
"""

import json
import re
import subprocess
import sys
from pathlib import Path

DOC = "docs/REFERENCE.md"
SECTION = "## Test Suite Reference"
_HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


def run(*args: str) -> str:
    return subprocess.run(list(args), check=True, capture_output=True, text=True).stdout


def section_range(text: str) -> tuple[int, int]:
    lines = text.splitlines()
    start = next(i for i, line in enumerate(lines, 1) if line.strip() == SECTION)
    end = next((i - 1 for i, line in enumerate(lines, 1) if i > start and line.startswith("## ")), len(lines))
    return start, end


def main() -> int:
    out = Path(sys.argv[1])
    heads = {row["number"]: row["headRefOid"] for row in json.loads(run("gh", "pr", "list", "--repo", "pcalnon/juniper-ml", "--state", "open", "--limit", "200", "--json", "number,headRefOid"))}
    report = []
    for n in sys.argv[2:]:
        ref = f"refs/flood4/pr/{n}"
        head = run("git", "rev-parse", ref).strip()
        base = run("git", "merge-base", "origin/main", ref).strip()
        fresh = heads.get(int(n)) == head
        try:
            start, end = section_range(run("git", "show", f"{base}:{DOC}"))
        except StopIteration:
            report.append(f"#{n}: base has no {SECTION!r}")
            continue
        diff = run("git", "diff", "-U0", base, head, "--", DOC)
        hits = []
        current: list[str] = []
        inside = False
        for line in diff.splitlines():
            m = _HUNK.match(line)
            if m:
                if inside and current:
                    hits.append("\n".join(current))
                old_start, old_len = int(m.group(1)), int(m.group(2) or "1")
                lo, hi = (old_start, old_start) if old_len == 0 else (old_start, old_start + old_len - 1)
                inside = lo <= end and hi >= start
                current = [line]
            elif current and not line.startswith(("diff --git", "index ", "--- ", "+++ ")):
                current.append(line)
        if inside and current:
            hits.append("\n".join(current))
        summary = f"#{n}: head {head[:10]} (matches GitHub: {fresh}) base {base[:10]} section {start}-{end}: {len(hits)} hunk(s) in {SECTION!r}"
        print(summary)
        report.append(summary)
        report.extend(hits)
        report.append("")
    out.write_text("\n".join(report) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
