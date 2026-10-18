"""
Wire one new regression suite into ci.yml, docs/REFERENCE.md, CHANGELOG.md and AGENTS.md, the same way every time.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-17
Status: ad-hoc — one-off (the turing bring-up Session 1 PRs: F5a, G2, B7, A5 and the C8 agent guard)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§6 "CI wiring rule");
         tests/test_ci_test_wiring_drift.py (the gate these edits must keep green)

Why: every suite-adding PR in this work arc edits the same four files in the same places, and they land
serially, each rebuilt on the previous merge. Doing it by hand five times invites a missed list entry,
which the drift gate catches only after a slow upload through turing's VPN. Per the plan's wiring rule:

  1. .github/workflows/ci.yml: the comment block plus invocation goes at the end of the
     `Run Python regression tests` step, just before the `Run bash regression tests` step.
  2. docs/REFERENCE.md:
     - the invocation goes into "### Running every suite", before `bash scripts/test_resume_file_safety.bash`;
     - the suite bullet goes into "## Test Suite Reference", before the `scripts/test.bash` bullet;
     - each utility bullet goes into "## Utility Script Reference", after the last bullet that names
       the turing bring-up.
  3. CHANGELOG.md: the entry goes at the top of `## [Unreleased]` / `### Added`.
  4. AGENTS.md: the "full ordered list of N `python3 -m unittest`" count is recomputed from the
     REFERENCE.md list.

Each edit refuses (exit 2) if its anchor is missing or the suite is already present, so a stale base
fails loudly instead of producing a half-wired file.

Usage:
    python3 util/ad-hoc/2026-10-17_turing_wire_suite.py --suite tests/test_macvm_ctl.py \\
        --ci-block CI.txt --test-bullet TEST.txt --util-bullet UTIL.txt [--util-bullet ...] --changelog CL.txt
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class WireError(Exception):
    pass


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def block(path: Path) -> str:
    """A text fragment with exactly one trailing newline."""
    return read(path).rstrip("\n") + "\n"


def wire_ci(text: str, suite: str, ci_block: str) -> str:
    invocation = f"python3 -m unittest -v {suite}"
    if re.search(rf"^\s+{re.escape(invocation)}\s*$", text, re.M):
        raise WireError(f"ci.yml already invokes {suite}")
    if invocation not in ci_block:
        raise WireError(f"the ci block does not contain `{invocation}`")
    anchor = "\n\n      - name: Run bash regression tests\n"
    if text.count(anchor) != 1:
        raise WireError("ci.yml: expected exactly one `Run bash regression tests` step after a blank line")
    return text.replace(anchor, "\n" + ci_block.rstrip("\n") + anchor, 1)


def section_bounds(lines: list[str], heading: str) -> tuple[int, int]:
    """[start, end) of a markdown section: from its heading to the next heading of the same or a higher
    level. Lines inside ``` fences are skipped, because the suite list is a bash block full of `# ...`."""
    level = len(heading.split(" ", 1)[0])
    if lines.count(heading) != 1:
        raise WireError(f"REFERENCE.md: expected exactly one heading {heading!r}")
    start = lines.index(heading)
    in_fence = False
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("```"):
            in_fence = not in_fence
            continue
        m = re.match(r"(#{1,6}) ", lines[i])
        if not in_fence and m and len(m.group(1)) <= level:
            return start, i
    return start, len(lines)


def wire_reference(text: str, suite: str, test_bullet: str, util_bullets: list[str]) -> str:
    lines = text.split("\n")
    invocation = f"python3 -m unittest -v {suite}"
    if invocation in lines:
        raise WireError(f"REFERENCE.md already lists {suite}")

    start, end = section_bounds(lines, "### Running every suite")
    marker = "bash scripts/test_resume_file_safety.bash"
    hits = [i for i in range(start, end) if lines[i] == marker]
    if len(hits) != 1:
        raise WireError("REFERENCE.md: `Running every suite` must contain the resume-file-safety line exactly once")
    lines.insert(hits[0], invocation)

    start, end = section_bounds(lines, "## Test Suite Reference")
    hits = [i for i in range(start, end) if lines[i].startswith("- `scripts/test.bash` --")]
    if len(hits) != 1:
        raise WireError("REFERENCE.md: no `scripts/test.bash` bullet in the Test Suite Reference")
    lines[hits[0]:hits[0]] = test_bullet.rstrip("\n").split("\n")

    if util_bullets:
        start, end = section_bounds(lines, "## Utility Script Reference")
        hits = [i for i in range(start, end) if lines[i].startswith("- `util/") and "uring bring-up" in lines[i]]
        if not hits:
            raise WireError("REFERENCE.md: no turing bring-up bullet in the Utility Script Reference to anchor on")
        at = hits[-1] + 1
        for bullet in util_bullets:
            new = bullet.rstrip("\n").split("\n")
            lines[at:at] = new
            at += len(new)
    return "\n".join(lines)


def wire_changelog(text: str, entry: str) -> str:
    head = "## [Unreleased]\n\n### Added\n\n"
    if text.count(head) != 1:
        raise WireError("CHANGELOG.md: expected `## [Unreleased]` followed by `### Added` exactly once")
    return text.replace(head, head + entry.rstrip("\n") + "\n\n", 1)


def wire_agents(text: str, reference: str) -> str:
    start, end = section_bounds(reference.split("\n"), "### Running every suite")
    count = sum(1 for line in reference.split("\n")[start:end] if line.startswith("python3 -m unittest "))
    new, n = re.subn(r"the full ordered list of \d+ `python3 -m unittest`", f"the full ordered list of {count} `python3 -m unittest`", text)
    if n != 1:
        raise WireError("AGENTS.md: the `full ordered list of N` sentence was not found exactly once")
    return new


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--suite", required=True, help="repo-relative path, e.g. tests/test_macvm_ctl.py")
    ap.add_argument("--ci-block", required=True, type=Path)
    ap.add_argument("--test-bullet", required=True, type=Path)
    ap.add_argument("--util-bullet", action="append", default=[], type=Path)
    ap.add_argument("--changelog", required=True, type=Path)
    args = ap.parse_args(argv)
    if not re.fullmatch(r"tests/test_[A-Za-z0-9_]+\.py", args.suite) or not (ROOT / args.suite).is_file():
        print(f"ERROR: --suite must name an existing tests/test_*.py (got {args.suite!r})", file=sys.stderr)
        return 2
    paths = {
        "ci": ROOT / ".github" / "workflows" / "ci.yml",
        "ref": ROOT / "docs" / "REFERENCE.md",
        "cl": ROOT / "CHANGELOG.md",
        "agents": ROOT / "AGENTS.md",
    }
    try:
        ci = wire_ci(read(paths["ci"]), args.suite, block(args.ci_block))
        ref = wire_reference(read(paths["ref"]), args.suite, block(args.test_bullet), [block(p) for p in args.util_bullet])
        cl = wire_changelog(read(paths["cl"]), block(args.changelog))
        agents = wire_agents(read(paths["agents"]), ref)
    except (OSError, WireError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    for key, text in (("ci", ci), ("ref", ref), ("cl", cl), ("agents", agents)):
        paths[key].write_text(text, encoding="utf-8")
        print(f"wired {paths[key].relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
