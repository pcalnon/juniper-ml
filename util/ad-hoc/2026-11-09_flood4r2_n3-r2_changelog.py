"""
Place the N-3 round-2 CHANGELOG entries in the juniper-cascor carrier, and simulate its landing beside fix N-1.

apply     Replace the [Unreleased] `### Added` block with tmp/.../n3-r2/changelog_added_block.txt, remove round 1's entry
          from the TOP of `### Fixed`, and insert tmp/.../n3-r2/changelog_fixed_entry.txt after the second existing
          `### Fixed` entry (the Bandit SARIF one). Fix N-1 (the paused-fit carrier) inserts its own entry after the
          FIRST one, so the two insertions are separated by unchanged lines and cannot conflict. Every anchor must
          occur exactly once. Writes changelog_entry.txt: the two blocks exactly as placed.
measured  Replace the `@@MEASURED@@` line in the CHANGELOG (and changelog_entry.txt) with a text file's content.
simulate  Three-way merges (`git merge-file`) of every file both carriers change, in both landing orders, on the
          current origin/main: conflicts, and the stamps each result carries.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor fix/ws-resume-losses
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
CARRIER = JUNIPER / "worktrees" / "juniper-cascor--fix--ws-resume-losses--20261108-1816--f3dfee8c"
N1 = JUNIPER / "worktrees" / "juniper-cascor--fix--paused-fit-wedge--20261108-1815--f3dfee8c"
SCRATCH = CARRIER / "tmp" / "flood4-fix" / "n3-r2"
CHANGELOG = CARRIER / "CHANGELOG.md"
N1_BASE = "f3dfee8c10ede0fbef6b4b61cb36af2b02307fd1"
SHARED = ["CHANGELOG.md", "docs/DEVELOPER_CHEATSHEET.md", "docs/api/API_SCHEMAS.md", "docs/api/JUNIPER_CASCOR_API_REFERENCE.md"]

FIXED_START = "- **A `/ws/training` client that resumes no longer misses broadcasts behind a `resume_ok`.**"
ROUND1_FIXED_END = "    Owner ruling: fix now.\n\n"
INSERT_BEFORE = "- **The nightly performance smoke runs on pytest 9.2 again: its `pytest<9.2` cap is gone.**"
BANDIT_START = "- **The Bandit SARIF upload's comment and its survey's docstring no longer claim that every upload succeeded.**"


def once(text: str, needle: str, what: str) -> int:
    count = text.count(needle)
    if count != 1:
        raise SystemExit(f"{what}: anchor occurs {count} times, expected 1")
    return text.index(needle)


def git_show(rev: str, rel: str) -> str:
    return subprocess.run(["git", "-C", str(CARRIER), "show", f"{rev}:{rel}"], check=True, capture_output=True, text=True).stdout


def merge(current: str, base: str, other: str, label: str) -> tuple:
    paths = []
    for name, text in (("current", current), ("base", base), ("other", other)):
        path = SCRATCH / "merge-sim" / f"{label}.{name}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        paths.append(str(path))
    proc = subprocess.run(["git", "merge-file", "-p", *paths], capture_output=True, text=True)
    (SCRATCH / "merge-sim" / f"{label}.result.txt").write_text(proc.stdout, encoding="utf-8")
    return proc.returncode, proc.stdout


def stamps(text: str) -> list:
    return [ln for ln in text.splitlines() if re.match(r"^\*\*(Version|Document Version|Last Updated|Version covered|Compiled)\*\*", ln)]


def cmd_apply() -> int:
    text = CHANGELOG.read_text(encoding="utf-8")
    added_new = (SCRATCH / "changelog_added_block.txt").read_text(encoding="utf-8")
    fixed_new = (SCRATCH / "changelog_fixed_entry.txt").read_text(encoding="utf-8")
    # 1. The Added block of [Unreleased]: from its "### Added" to the "### Changed" that follows it.
    u0 = once(text, "\n## [Unreleased]\n", "## [Unreleased]")
    u1 = text.index("\n## [", u0 + 1)
    unreleased = text[u0:u1]
    a0 = u0 + once(unreleased, "\n### Added\n", "[Unreleased] ### Added") + 1
    a1 = text.index("\n### Changed\n", a0) + 1
    if a1 > u1:
        raise SystemExit("[Unreleased] has no ### Changed after its ### Added")
    text = text[:a0] + added_new + text[a1:]
    # 2. Round 1's Fixed entry, at the top of ### Fixed: cut it whole.
    f0 = once(text, FIXED_START, "round-1 Fixed entry")
    f1 = once(text, ROUND1_FIXED_END, "round-1 Fixed entry end") + len(ROUND1_FIXED_END)
    if not text[:f0].endswith("### Fixed\n\n"):
        raise SystemExit("round 1's entry is not at the top of ### Fixed")
    text = text[:f0] + text[f1:]
    # 3. Insert below the second existing entry, before the third.
    b0 = once(text, BANDIT_START, "Bandit SARIF entry")
    i0 = once(text, INSERT_BEFORE, "nightly performance smoke entry")
    if not (b0 < i0 and text[:i0].endswith("\n\n")):
        raise SystemExit("unexpected layout around the insertion point")
    text = text[:i0] + fixed_new + "\n" + text[i0:]
    CHANGELOG.write_text(text, encoding="utf-8")
    (SCRATCH / "changelog_entry.txt").write_text("[Unreleased] -> top of the section:\n\n" + added_new + "\n[Unreleased] -> ### Fixed, after its second entry (the Bandit SARIF one):\n\n" + fixed_new, encoding="utf-8")
    print("applied")
    return 0


def cmd_measured(path: str) -> int:
    measured = Path(path).read_text(encoding="utf-8").rstrip("\n")
    for target in (CHANGELOG, SCRATCH / "changelog_entry.txt"):
        text = target.read_text(encoding="utf-8")
        once(text, "@@MEASURED@@\n", f"@@MEASURED@@ in {target.name}")
        target.write_text(text.replace("@@MEASURED@@", measured), encoding="utf-8")
    print("measured bullet placed")
    return 0


def cmd_simulate() -> int:
    main_sha = subprocess.run(["git", "-C", str(CARRIER), "rev-parse", "origin/main"], check=True, capture_output=True, text=True).stdout.strip()
    report = {"origin_main": main_sha, "n1_worktree": str(N1), "n1_base": N1_BASE, "files": {}}
    for rel in SHARED:
        main_text = git_show(main_sha, rel)
        n1_base_text = git_show(N1_BASE, rel)
        n1_text = (N1 / rel).read_text(encoding="utf-8")
        mine = (CARRIER / rel).read_text(encoding="utf-8")
        tag = rel.replace("/", "_")
        # N-1 rebuilt onto the current main, as the orchestrator would before landing it.
        n1_rc, n1_on_main = merge(n1_text, n1_base_text, main_text, f"{tag}.n1-on-main")
        # Order A: N-1 lands first, then this carrier is rebuilt onto it.
        a_rc, a_text = merge(mine, main_text, n1_on_main, f"{tag}.n1-first-then-n3")
        # Order B: this carrier lands first, then N-1 is rebuilt onto it.
        b_rc, b_text = merge(n1_on_main, main_text, mine, f"{tag}.n3-first-then-n1")
        report["files"][rel] = {
            "n1_rebuilt_on_main_conflicts": n1_rc,
            "order_n1_first_conflicts": a_rc,
            "order_n3_first_conflicts": b_rc,
            "orders_agree": a_text == b_text,
            "stamps_main": stamps(main_text),
            "stamps_n1": stamps(n1_on_main),
            "stamps_n3": stamps(mine),
            "stamps_after_both": stamps(a_text),
            "n3_deletes_main_lines": sum(1 for ln in subprocess.run(["git", "diff", "--no-index", "--unified=0", str(SCRATCH / "merge-sim" / f"{tag}.n1-first-then-n3.base.txt"), str(CARRIER / rel)], capture_output=True, text=True).stdout.splitlines() if ln.startswith("-") and not ln.startswith("---")),
        }
    with open(SCRATCH / "merge_simulation.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
        fh.write("\n")
    for rel, row in report["files"].items():
        print(rel, {k: row[k] for k in ("n1_rebuilt_on_main_conflicts", "order_n1_first_conflicts", "order_n3_first_conflicts", "orders_agree", "n3_deletes_main_lines")})
        print("   stamps main", row["stamps_main"], "| n1", row["stamps_n1"], "| n3", row["stamps_n3"], "| both", row["stamps_after_both"])
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("apply")
    m = sub.add_parser("measured")
    m.add_argument("text_file")
    sub.add_parser("simulate")
    args = ap.parse_args()
    if args.cmd == "apply":
        return cmd_apply()
    if args.cmd == "measured":
        return cmd_measured(args.text_file)
    return cmd_simulate()


if __name__ == "__main__":
    sys.exit(main())
