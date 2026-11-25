#!/usr/bin/env python3
"""
Check the ruling-26 frozen file sets against a fresh clone of each repository's main (V26 claims lens).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 ruling 26 ports, session 11, validator V26 claims lens)
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc -- investigation (checks the facts the six PR texts state about their own diffs)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 26);
         juniper-canopy#814 (the model fix)

What it does
------------
Given the builder's deliverables directory (``--r26``, holding ``<repo>/final/``, ``<repo>/paths.txt`` and
``<repo>/final.sha256``) and a directory of fresh clones of each repository's main (``--clones``), for each repository:

1. checks every frozen file's sha256 against ``final.sha256`` and lists each changed path with its +/- line counts
   against main (a new file counts every line as added);
2. for ``.github/workflows/lockfile-update.yml``: prints the diff hunks' line ranges, the banner ``Version`` and
   ``Last Modified`` before and after, every ``- name:`` step before and after (and whether the list is identical),
   the line of the bare ``gh api graphql`` call on main, the ``on:`` / ``permissions:`` / ``uses:`` lines (identical
   or not), every absolute path the file names before and after, and whether the step's block from the
   ``# `gh api graphql` exits 1`` comment to the 401 hint's ``fi`` equals canopy main's block (``--canopy-clone``),
   printing every differing line.

Read-only on the clones and the deliverables; writes ``--out`` (JSON) when given.

Usage
-----
    python3 util/ad-hoc/2026-11-24_flood4_s11_v26_claims_diffcheck.py --r26 DIR --clones DIR \
        --canopy-clone DIR [--out FILE]
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path

REPOS = ["juniper-data", "juniper-cascor", "juniper-data-client", "juniper-cascor-client", "juniper-cascor-worker", "juniper-canopy"]
WORKFLOW = ".github/workflows/lockfile-update.yml"
BLOCK_START = "# `gh api graphql` exits 1, not 0"
BLOCK_END_MARK = "HTTP 401: CROSS_REPO_DISPATCH_TOKEN is invalid or expired."


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def _block(lines: list[str]) -> list[str]:
    start = next((i for i, line in enumerate(lines) if BLOCK_START in line), None)
    if start is None:
        return []
    end = next((i for i in range(start, len(lines)) if BLOCK_END_MARK in lines[i]), None)
    if end is None:
        return []
    # the 401 hint's closing `fi` is the next line that is a bare `fi`
    close = next((i for i in range(end, len(lines)) if lines[i].strip() == "fi"), end)
    return [line.strip() for line in lines[start : close + 1]]


def _banner(lines: list[str]) -> dict[str, str]:
    out = {}
    for line in lines[:40]:
        match = re.match(r"#\s*(Version|Last Modified):\s*(.+)$", line)
        if match:
            out[match.group(1)] = match.group(2).strip()
    return out


def _steps(lines: list[str]) -> list[str]:
    return [line.strip() for line in lines if re.match(r"\s*- name:", line)]


def _structural(lines: list[str]) -> list[str]:
    picked = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("uses:", "- uses:")) or re.match(r"^(on|permissions):", line) or re.match(r"^\s+(push|pull_request|branches|paths|contents|pull-requests):", line):
            picked.append(stripped)
    return picked


ABS_PATH = re.compile(r"(?<![\w.$}/:])(?:/[A-Za-z0-9_.*-]+){2,}")


def _abs_paths(lines: list[str]) -> list[str]:
    """Every absolute path of two or more components the file names (a URL's path is excluded by the lookbehind)."""
    found = []
    for line in lines:
        found.extend(ABS_PATH.findall(line))
    return sorted(set(found))


def _hunks(old: list[str], new: list[str]) -> list[str]:
    out = []
    for group in difflib.SequenceMatcher(a=old, b=new, autojunk=False).get_grouped_opcodes(0):
        a0, a1 = group[0][1], group[-1][2]
        b0, b1 = group[0][3], group[-1][4]
        out.append(f"main {a0 + 1}-{a1} -> final {b0 + 1}-{b1}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--r26", type=Path, required=True)
    parser.add_argument("--clones", type=Path, required=True)
    parser.add_argument("--canopy-clone", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    canopy_block = _block(_lines(args.canopy_clone / WORKFLOW))
    report: dict[str, dict] = {}
    for repo in REPOS:
        rdir = args.r26 / repo
        clone = args.clones / repo
        paths = [p for p in (rdir / "paths.txt").read_text(encoding="utf-8").split() if p]
        recorded = {}
        for line in (rdir / "final.sha256").read_text(encoding="utf-8").splitlines():
            digest, _, rel = line.partition("  ")
            recorded[rel.strip()] = digest.strip()
        entry: dict[str, object] = {"files": {}}
        print(f"==================== {repo}")
        for rel in paths:
            final = rdir / "final" / rel
            base = clone / rel
            old, new = _lines(base), _lines(final)
            diff = list(difflib.unified_diff(old, new, lineterm="", n=0))
            plus = sum(1 for d in diff if d.startswith("+") and not d.startswith("+++"))
            minus = sum(1 for d in diff if d.startswith("-") and not d.startswith("---"))
            sha_ok = recorded.get(rel) == _sha(final)
            info = {"sha256_ok": sha_ok, "new_file": not base.exists(), "plus": plus, "minus": minus, "hunks": _hunks(old, new)}
            entry["files"][rel] = info
            print(f"  {rel}: sha256 {'OK' if sha_ok else 'MISMATCH'}; {'NEW FILE; ' if not base.exists() else ''}+{plus} -{minus}; hunks {info['hunks']}")
            if rel == WORKFLOW:
                bold, bnew = _banner(old), _banner(new)
                sold, snew = _steps(old), _steps(new)
                gh_line = next((i + 1 for i, line in enumerate(old) if line.strip().startswith("gh api graphql")), None)
                errors_line = next((i + 1 for i, line in enumerate(old) if "jq -e '.errors'" in line), None)
                block = _block(new)
                bdiff = [d for d in difflib.unified_diff(canopy_block, block, lineterm="", n=0) if d[:1] in "+-" and d[:3] not in ("+++", "---")]
                wf = {
                    "banner_main": bold,
                    "banner_final": bnew,
                    "steps_identical": sold == snew,
                    "steps_main": sold,
                    "bare_gh_line_main": gh_line,
                    "errors_check_line_main": errors_line,
                    "structural_identical": _structural(old) == _structural(new),
                    "abs_paths_main": _abs_paths(old),
                    "abs_paths_final": _abs_paths(new),
                    "block_lines_canopy": len(canopy_block),
                    "block_lines_final": len(block),
                    "block_diff_vs_canopy_main": bdiff,
                }
                entry["workflow"] = wf
                print(f"    banner main {bold} -> final {bnew}")
                print(f"    step names identical: {sold == snew}")
                for step in sold:
                    print(f"      {step}")
                print(f"    bare gh call on main at :{gh_line}; .errors check at :{errors_line}")
                print(f"    on:/permissions:/uses: lines identical: {_structural(old) == _structural(new)}")
                print(f"    absolute paths identical: {_abs_paths(old) == _abs_paths(new)}; main {_abs_paths(old)}")
                print(f"    block vs canopy main: {len(canopy_block)} vs {len(block)} lines; differing lines:")
                for line in bdiff:
                    print(f"      {line}")
        report[repo] = entry
    if args.out is not None:
        with args.out.open("w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
