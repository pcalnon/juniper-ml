"""
Write changelog_entry.txt for round 3 of the juniper-cascor N-3 carrier from the carrier's own CHANGELOG.md, and
check where the entry sits.

The entry text is taken from `git diff HEAD -- CHANGELOG.md` in the carrier worktree (the added lines of each hunk,
in order), so the deliverable cannot drift from the file. The checks, each printed and returned in the exit status:

  * every added line is inside the top `## [Unreleased]` section;
  * the diff deletes no line;
  * under `### Fixed`, the carrier's entry comes after the paused-fit entry that juniper-cascor#753 (fix N-1) added,
    and after at least one entry that was already there (rule 9 of the common brief).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses;
         tmp/flood4/BRIEF_COMMON_R2.txt rule 9
"""

import re
import subprocess
import sys
from pathlib import Path

CARRIER = Path.home() / "Development" / "python" / "Juniper" / "worktrees" / "juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c"
OUT = CARRIER / "tmp" / "flood4-fix" / "n3-r3" / "changelog_entry.txt"

N1_ENTRY = "- **A fit that returns while its run is paused now settles `COMPLETED`."
N3_ENTRY = "- **A `/ws/training` client that resumes no longer misses broadcasts behind a `resume_ok`.**"


def main() -> int:
    diff = subprocess.run(["git", "-C", str(CARRIER), "diff", "--unified=0", "HEAD", "--", "CHANGELOG.md"], check=True, capture_output=True, text=True).stdout
    hunks, deleted = [], 0
    for line in diff.splitlines():
        if line.startswith("@@"):
            start = int(re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", line).group(1))
            hunks.append({"start": start, "lines": []})
        elif line.startswith("+") and not line.startswith("+++"):
            hunks[-1]["lines"].append(line[1:])
        elif line.startswith("-") and not line.startswith("---"):
            deleted += 1
    text = (CARRIER / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
    sections = [i for i, line in enumerate(text, 1) if line.startswith("## [")]
    unreleased_ok = text[sections[0] - 1] == "## [Unreleased]"
    last_added = max(h["start"] + len(h["lines"]) - 1 for h in hunks)
    inside = unreleased_ok and all(sections[0] < h["start"] for h in hunks) and last_added < sections[1]
    fixed_at = next(i for i, line in enumerate(text, 1) if line == "### Fixed")
    next_heading = next(i for i, line in enumerate(text, 1) if i > fixed_at and line.startswith("#"))
    entries = [(i, line) for i, line in enumerate(text, 1) if fixed_at < i < next_heading and line.startswith("- **")]
    n1 = next(i for i, line in entries if line.startswith(N1_ENTRY))
    n3 = next(i for i, line in entries if line.startswith(N3_ENTRY))
    position = [i for i, _ in entries].index(n3) + 1
    below_n1 = n3 > n1
    print(f"[Unreleased] spans lines {sections[0]}-{sections[1] - 1}; added lines {min(h['start'] for h in hunks)}-{last_added}; all inside: {inside}")
    print(f"deleted lines: {deleted}")
    print(f"### Fixed has {len(entries)} entries; N-1's is at line {n1}, N-3's at line {n3} (entry {position}); N-3 below N-1: {below_n1}")
    for i, line in entries:
        print(f"   {i}: {line[:110]}")
    labels = []
    for hunk in hunks:
        first = next(line for line in hunk["lines"] if line.strip())
        if first.startswith("### Added"):
            labels.append("[Unreleased] -> top of the section:")
        elif first.startswith(N3_ENTRY):
            labels.append(f"[Unreleased] -> ### Fixed, as its entry {position} of {len(entries)}, below the paused-fit entry (juniper-cascor#753) and the Bandit SARIF entry:")
        else:
            labels.append(f"[Unreleased] -> at line {hunk['start']}:")
    blocks = [label + "\n\n" + "\n".join(hunk["lines"]).strip("\n") + "\n" for label, hunk in zip(labels, hunks)]
    OUT.write_text("\n\n".join(blocks), encoding="utf-8")
    added_nonblank = sum(1 for h in hunks for line in h["lines"] if line.strip())
    print(f"{len(hunks)} hunks, {added_nonblank} non-blank added lines -> {OUT}")
    return 0 if inside and deleted == 0 and below_n1 and position > 1 else 1


if __name__ == "__main__":
    sys.exit(main())
