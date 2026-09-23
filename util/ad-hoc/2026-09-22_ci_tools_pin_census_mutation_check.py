#!/usr/bin/env python3
"""
Check that the ci-tools pin census's --self-test fails when a listed rule is removed, one rule at a time.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-22
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py (the script under test);
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_ci-tools-0-9-0-shipped-and-every-no-owner-item-is-closed.md
         (its Corrections 1 and validation record cite this check)

A self-test that still passes with a branch deleted does not test that branch. Round 2 of the
banner's consensus review found exactly that: with the DOC/COMMENT verdict removed, the census's
earlier self-test still passed 31 of 31 while the real census dropped from 18 stale lines to 0.
Each mutation below removes or neuters one rule the census relies on; most are the blind spots
round 2 named. A mutation "survives" when the self-test still passes, and any survivor fails
this check (exit 1). An anchor that no longer matches exactly once also fails it, so an edit to
the census cannot silently retire a mutation.

**A kill here proves only the rules listed.** The mutants are chosen, not exhaustive.
- In rounds 3 and 4 the review lanes applied mutants of their own, and some still survive.
- The groups added at the end of MUTATIONS are the ones this self-test now kills.
- Among the survivors are the lookback and attribution constants, the pre-filter, the
  bare-release verbs, composite-action handling, the ADJUDICATED lookup and keys, the
  floor-only skip and some comment-branch shapes.
- Each lane report lists its own survivors, in
  reports/2026-09-22_ci-tools-handoff-reevaluation-consensus/: round3-laneA-census-adequacy.md,
  round3-laneB-attack-the-round2-fix-pass.md and round4-laneB-attack-the-round3-fix-pass.md.

The mutants are written to a temporary directory and deleted afterwards. Nothing in the tree
changes.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

CENSUS = Path(__file__).with_name("2026-09-22_ci_tools_pin_census_remote.py")

MUTATIONS = {
    "DOC/COMMENT verdict removed": ('        elif h.cls in ("DOC", "COMMENT") and not admits_same(h.spec):\n            bad.append(where)\n', ""),
    "LIVE verdict removed": ('        if h.cls == "LIVE" and h.spec != normalise(expect):\n            bad.append(where)\n        elif', "        if"),
    "latest-lag guard neutered": ("    if Version(latest) not in SpecifierSet(expect):\n        return f", "    if False:\n        return f"),
    "table-column attribution removed": ('    if is_md and lines[lineno - 1].lstrip().startswith("|"):\n        return table_owner(lines, lineno - 1, col)\n', ""),
    "exceptions keyed without the specifier": ("s in raw and sp == spec", "s in raw"),
    "tests/ docstrings treated as fixture": ('            if path.endswith((".md", ".rst")) or lineno in doc_lines:\n                return "COMMENT"\n', ""),
    "PR/URL tokens not transparent": ('    return (\n        after.startswith("#")', '    return False and (\n        after.startswith("#")'),
    "snapshot locks not historical": (" or SNAPSHOT_RE.search(base):", ":"),
    "markdown fences/headings do not bound lookback": ("            if bounds:\n                floor = max(floor, offsets[max(bounds) + 1])\n", ""),
    "variable pins treated as unresolved": ("                if not in_path and not variable_pin:", "                if not in_path:"),
    "arithmetic read as a specifier": ('    if COMPARISON_RE.search(before):\n        return "other"', '    if False:\n        return "other"'),
    "bare 'ci-tools 0.8.0' mentions ignored": ('    for m in BARE_VERSION_RE.finditer(text):\n        found.append((line_of(m.start()), m.start(), f"=={m.group(1)}", "ci-tools"))\n', ""),
    "heading naming another package drops the range": ('            return None\n    return None\n\n\nCOMPARISON_RE', '            return "other"\n    return None\n\n\nCOMPARISON_RE'),
    "comment block inherits a code line's name": ("        if is_comment_line(lineno) or col >= comment_start(raw):\n", "        if False:\n"),
    "unresolved installs ignore continuations": ('            if body.rstrip().endswith("\\\\"):\n                buf += body.rstrip()[:-1] + " "\n                continue\n', ""),
    # Added after round 3, whose lanes found each of these surviving the 81-case self-test.
    "OWN-EXTRA matches any range": ("            elif extra is not None and spec == extra:\n", "            elif extra is not None:\n"),
    "util/ad-hoc/ not history": ('path.startswith("util/ad-hoc/") or ', ""),
    "CHANGELOG not history": ('base.startswith("CHANGELOG") or ', ""),
    "prompts/ and reports/ not history": ('HISTORICAL_SEGMENTS = {"notes", "prompts", "reports", "releases", "history", "legacy"}', 'HISTORICAL_SEGMENTS = {"notes", "releases", "history", "legacy"}'),
    "main() exits 0 whatever it finds": ("    return 1 if bad else 0\n\n\ndef run(", "    return 0\n\n\ndef run("),
    "a lagging --expect not counted": ("    if lag:\n        bad.insert(0, lag)\n", ""),
    "a repo with no install accepted": ("        if installs == 0:\n", "        if False:\n"),
    "misspelt --ref/--local keys accepted": ("    if unknown:\n        raise ValueError", "    if False:\n        raise ValueError"),
    "candidates omit the next releases": ("    return sorted(set(released) | set(extra), key=Version)", "    return sorted(set(released), key=Version)"),
    # Added after round 4, whose lanes found each of these surviving the 93-case self-test.
    "the command line bypasses run()": ("    raise SystemExit(run())", "    raise SystemExit(main())"),
    "misspelt --local keys accepted": ("unknown = sorted((set(refs) | set(locals_)) - set(REPOS))", "unknown = sorted(set(refs) - set(REPOS))"),
    "repeated --ref/--local keys accepted": ("    if repeated:\n        raise ValueError", "    if False:\n        raise ValueError"),
    "the install guard fires only on a repo with no hits": ("        if installs == 0:\n", "        if not hits:\n"),
    "an unpinned install counted as no install": ('        installs = live + sum(1 for h in hits if h.cls == "UNRESOLVED")\n', "        installs = live\n"),
    "an empty read not refused as such": ("        if not members:\n            raise RuntimeError", "        if False:\n            raise RuntimeError"),
    ".md files never read": ('TEXT_SUFFIXES = (".yml", ".yaml", ".md", ".rst",', 'TEXT_SUFFIXES = (".yml", ".yaml", ".rst",'),
    ".py files never read": ('".ini", ".py", ".bash"', '".ini", ".bash"'),
    "the own extra read from any range": (r'm = re.search(r"juniper[-_]ci[-_]tools\s*(" + SPEC_RE.pattern', r'm = re.search(r"(" + SPEC_RE.pattern'),
    "passing AMBIGUOUS lines not listed": ("    if unread:\n        print(", "    if False:\n        print("),
}


def main() -> int:
    src = CENSUS.read_text(encoding="utf-8")
    baseline = subprocess.run([sys.executable, str(CENSUS), "--self-test"], capture_output=True, text=True)
    if baseline.returncode != 0:
        print(f"the unmutated census fails its own self-test (exit {baseline.returncode}); fix that first")
        return 2
    survivors = []
    with tempfile.TemporaryDirectory() as tmp:
        mutant = Path(tmp) / CENSUS.name
        for name, (old, new) in MUTATIONS.items():
            if src.count(old) != 1:
                print(f"  STALE     {name}: anchor found {src.count(old)} times")
                survivors.append(name)
                continue
            mutant.write_text(src.replace(old, new, 1), encoding="utf-8")
            rc = subprocess.run([sys.executable, str(mutant), "--self-test"], capture_output=True, text=True).returncode
            print(f"  {'killed  ' if rc != 0 else 'SURVIVED'}  {name}")
            if rc == 0:
                survivors.append(name)
    print(f"{len(MUTATIONS) - len(survivors)} of {len(MUTATIONS)} mutations killed")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
