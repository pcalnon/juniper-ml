#!/usr/bin/env python3
# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   flood-4 round-2 validation (ad hoc)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
"""Prove a carrier's edits to .gitleaks.toml and .github/workflows/ci.yml are comment-only.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation (a flood-4 validator's probe)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-canopy#802 docs carrier, validation round 2, item 2: the comment-only config edits (findings: tmp/flood4/canopy/val-round2/)

For each file: main's blob (git show <base>:<path> in the canopy primary, read-only) vs the
carrier's working-tree file. Parses both (tomllib / yaml.safe_load) and compares the data, and
lists every changed line, classifying each as comment-only or not (after stripping, the line
starts with '#'). Also checks that no changed line is inside a YAML block scalar where '#'
would be literal text (a `run: |` body): for each changed ci.yml line, reports the nearest
enclosing key line with a smaller indent.

Usage: python3 <this> <canopy primary> <base sha> <carrier worktree> <out json>
"""
import difflib
import json
import pathlib
import subprocess
import sys
import tomllib

import yaml


def main() -> int:
    primary, base, carrier, out = sys.argv[1:5]
    report = {}
    for path in (".gitleaks.toml", ".github/workflows/ci.yml"):
        old = subprocess.run(["git", "-C", primary, "show", f"{base}:{path}"], capture_output=True, text=True, check=True).stdout
        new = (pathlib.Path(carrier) / path).read_text()
        if path.endswith(".toml"):
            d_old, d_new = tomllib.loads(old), tomllib.loads(new)
        else:
            d_old, d_new = yaml.safe_load(old), yaml.safe_load(new)
        changed = []
        new_lines = new.splitlines()
        sm = difflib.SequenceMatcher(a=old.splitlines(), b=new_lines, autojunk=False)
        for tag, i1, i2, j1, j2 in sm.get_opcodes():
            if tag == "equal":
                continue
            for ln in old.splitlines()[i1:i2]:
                changed.append({"side": "-", "line": ln, "comment": ln.strip().startswith("#")})
            for k, ln in enumerate(new_lines[j1:j2]):
                entry = {"side": "+", "lineno": j1 + k + 1, "line": ln, "comment": ln.strip().startswith("#")}
                if path.endswith(".yml"):
                    indent = len(ln) - len(ln.lstrip())
                    for back in range(j1 + k - 1, -1, -1):
                        prev = new_lines[back]
                        if prev.strip() and not prev.strip().startswith("#") and (len(prev) - len(prev.lstrip())) < indent:
                            entry["enclosing"] = f"{back + 1}: {prev.strip()}"
                            entry["inside_block_scalar"] = prev.rstrip().endswith(("|", ">", "|-", ">-", "|+", ">+"))
                            break
                changed.append(entry)
        report[path] = {
            "parsed_data_equal": d_old == d_new,
            "changed_lines": changed,
            "all_changed_lines_are_comments": all(c["comment"] for c in changed),
            "any_inside_block_scalar": any(c.get("inside_block_scalar") for c in changed),
        }
    pathlib.Path(out).write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
