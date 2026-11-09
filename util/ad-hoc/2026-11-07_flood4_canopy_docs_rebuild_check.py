#!/usr/bin/env python3
"""
Prove the canopy flood-4 docs carrier equals main + the drafts' stripped hunks + one stamp bump + the wrap/MD038 edits, and nothing else.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: Cursor flood-4 consolidation, canopy docs carrier (#790 #791 #793 #796)

Usage: 2026-11-07_flood4_canopy_docs_rebuild_check.py <docs worktree> <base sha> <date> <stripped patch>...

Rebuilds every touched file IN MEMORY (nothing is written) from the base blob with the flood-3
assembler's own parse/merge functions, the flood-3 stamp bump, and this arc's wrap script, then
compares it byte-for-byte with the worktree file. A difference means something else edited the
tree (markdownlint's --fix runs over whole files) and is printed as a unified diff.
"""

import difflib
import importlib.util
import subprocess
import sys
from pathlib import Path

ADHOC = Path(__file__).resolve().parent


def load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, ADHOC / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main(argv: list[str]) -> int:
    # Optional last steps: each --then <fixes script> replays its EDITS (and MINOR) tables, in order
    # (round 1: {path: edits}; round 2: {"docs": {path: edits}}).
    rounds = []
    while "--then" in argv:
        i = argv.index("--then")
        mod = load(f"flood4_validator_fixes_{len(rounds)}", Path(argv[i + 1]).name)
        edits = mod.EDITS["docs"] if "docs" in mod.EDITS else mod.EDITS
        rounds.append((edits, getattr(mod, "MINOR", {}), getattr(mod, "VERSION", None)))
        argv = argv[:i] + argv[i + 2 :]
    fixes = rounds or None
    wt, base, date, patches = Path(argv[1]).resolve(), argv[2], argv[3], argv[4:]
    asm = load("flood3_assemble", "2026-10-08_flood3_canopy_docs_assemble.py")
    bump = load("flood3_bump", "2026-10-08_fleet_flood3_bump_doc_stamps.py")
    wrapper = load("flood4_wrap", "2026-11-07_flood4_canopy_docs_wrap.py")
    groups: dict[str, list] = {}
    for patch in patches:
        for path, ops in asm.parse_patch(Path(patch).read_text(encoding="utf-8")).items():
            groups.setdefault(path, []).append((Path(patch).name, ops))
    for edits, _minor, _version in fixes or []:
        for path in edits:
            if path != "CHANGELOG.md":
                groups.setdefault(path, [])
    bad = 0
    for path, group in sorted(groups.items()):
        blob = subprocess.run(["git", "-C", str(wt), "show", f"{base}:{path}"], check=True, capture_output=True, text=True).stdout
        if not group:
            # touched only by the validator fixes (comment edits in .gitleaks.toml / ci.yml / a test comment)
            text = blob
            for edits, _minor, _version in fixes:
                for old, new in edits.get(path, []):
                    assert text.count(old) == 1, (path, old[:60])
                    text = text.replace(old, new)
            actual = (wt / path).read_text(encoding="utf-8")
            same = actual == text
            bad += 0 if same else 1
            print(f"{'SAME' if same else 'DIFFERS'} {path} (validator fixes only)")
            if not same:
                sys.stdout.writelines(difflib.unified_diff(text.splitlines(keepends=True), actual.splitlines(keepends=True), "expected", "worktree", n=1))
            continue
        merged, conflicts = asm.merge_ops(blob.splitlines(keepends=True), group)
        assert merged is not None, (path, conflicts)
        text, _old, _new = bump.bump("".join(merged), date)
        for old, new in wrapper.REPHRASE.get(path, []):
            if old in text:
                text = text.replace(old, new)
        flagged = set()
        if path in wrapper.FILES:
            # wrap only the lines markdownlint flags: those over 512 with whitespace past column 512
            out = []
            for line in text.split("\n"):
                if len(line) > 512 and " " in line[512:]:
                    flagged.add(line[:60])
                    out.extend(wrapper.wrap(line))
                else:
                    out.append(line)
            text = "\n".join(out)
        for edits, minor, version in fixes or []:
            for old, new in edits.get(path, []):
                assert text.count(old) == 1, (path, old[:60])
                text = text.replace(old, new)
            if path in minor:
                new_v = minor[path][1]
                text = version.sub(lambda m: f"{m.group(1)}{new_v}{m.group(3)}", text)
        actual = (wt / path).read_text(encoding="utf-8")
        same = actual == text
        bad += 0 if same else 1
        print(f"{'SAME' if same else 'DIFFERS'} {path} (groups: {[g[0] for g in group]}, wrapped: {len(flagged)})")
        if not same:
            sys.stdout.writelines(difflib.unified_diff(text.splitlines(keepends=True), actual.splitlines(keepends=True), "expected", "worktree", n=1))
    print(f"files differing: {bad}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
