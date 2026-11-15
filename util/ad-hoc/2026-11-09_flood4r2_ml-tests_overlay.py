#!/usr/bin/env python3
"""
Build the "main + ml-code + ml-tests" test configuration in a scratch worktree of origin/main.

The ml-tests carrier lands AFTER the ml-code carrier, so its suites must pass both on main alone (the
carrier worktree) and with ml-code's changes overlaid. ml-code is an uncommitted tree built on an older
main (--mlcode-base); main has since moved two of its shared files. Per path:

  * only the carrier changed it  -> the carrier's copy;
  * only ml-code changed it      -> ml-code's copy (refused if main moved that path since ml-code's base);
  * both changed it              -> `git merge-file -p` of carrier (ours) / ml-code's base / ml-code (theirs),
                                    written to <scratch>/merge_raw/ with its conflict count, then resolved
                                    by --union and the explicit FIXUPS below, and refused if any conflict
                                    marker or duplicated count line survives.

The resolved shared files are also kept in <scratch>/post_mlcode/: they are what this carrier's shared
files look like on top of ml-code (a landing aid, not part of the carrier). util/ad-hoc/ paths are never
overlaid. Writes <scratch>/overlay.json.

Usage (from the carrier worktree root):
    python3 util/ad-hoc/2026-11-09_flood4r2_ml-tests_overlay.py --dest <scratch worktree> --scratch <dir>
        --mlcode-tree <abs> --mlcode-base <sha> --mlcode-manifest <path>

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (flood-4 round-2 ml-tests carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: tmp/flood4/session4/BRIEF_S4_ADDENDUM.txt (merge-file is the shared-file rebuild that works)
"""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Explicit resolutions for the lines both carriers rewrite. Each must apply exactly once after the union merge.
FIXUPS = {
    "AGENTS.md": [
        (
            "# Run all tests -- the full ordered list of 247 `python3 -m unittest`\n# Run all tests -- the full ordered list of 237 `python3 -m unittest`\n",
            "# Run all tests -- the full ordered list of 252 `python3 -m unittest`\n",
        ),
    ],
}


def _run(argv: list, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True, check=False, **kw)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _carrier_paths() -> list:
    changed = _run(["git", "diff", "--name-only", "HEAD"]).stdout.split()
    untracked = _run(["git", "ls-files", "--others", "--exclude-standard"]).stdout.split()
    return sorted(p for p in set(changed) | set(untracked) if not p.startswith("util/ad-hoc/"))


def _reference_fixups(text: str) -> tuple:
    """Merge the two `Running every suite` tally lines, and give each carrier its own doc stamp."""
    notes = []
    lines = text.split("\n")
    tally = [i for i, ln in enumerate(lines) if ln.startswith("The complete ordered list, generated from")]
    if len(tally) == 2:
        mine, theirs = lines[tally[0]], lines[tally[1]]
        if "**247**" not in mine:
            mine, theirs = theirs, mine
        m = re.search(r", \*\*237\*\* on [^;]*", theirs)
        if not m:
            raise SystemExit("REFERENCE: ml-code's 237 tally entry not found")
        merged = mine.replace(", **247** on", m.group(0) + ", **252** on", 1)
        lines[tally[0]] = merged
        del lines[tally[1]]
        notes.append("tally lines merged: 237 (ml-code) then 252 (ml-tests)")
    text = "\n".join(lines)
    # Stamps: main 0.6.65 -> ml-code 0.6.66 -> ml-tests 0.6.67 (both carriers bump once from what they land on).
    # The union keeps both sides' header and footer lines; each pair becomes the one 0.6.67 line.
    for old, new in (
        ("**Version:** 0.6.66\n**Version:** 0.6.65\n", "**Version:** 0.6.67\n"),
        ("**Version:** 0.6.65\n**Version:** 0.6.66\n", "**Version:** 0.6.67\n"),
    ):
        if text.count(old) in (1, 2):
            notes.append(f"stamp fix x{text.count(old)}: {old!r} -> {new!r}")
            text = text.replace(old, new)
    ours = re.search(r"^\| 0\.6\.66  \| 2026-11-09 \| Cursor flood-4 round-2 tests carrier.*\n", text, re.M)
    theirs = re.search(r"^\| 0\.6\.65  \| 2026-11-09 \| Cursor flood-4 round-2 code carrier.*\n", text, re.M)
    if ours and theirs:
        tests_row = ours.group(0).replace("| 0.6.66  |", "| 0.6.67  |", 1)
        code_row = theirs.group(0).replace("| 0.6.65  |", "| 0.6.66  |", 1)
        text = text.replace(ours.group(0), "", 1).replace(theirs.group(0), code_row + tests_row, 1)
        notes.append("history rows: ml-code 0.6.66, then ml-tests 0.6.67")
    return text, notes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", required=True)
    ap.add_argument("--scratch", required=True)
    ap.add_argument("--mlcode-tree", required=True)
    ap.add_argument("--mlcode-base", required=True)
    ap.add_argument("--mlcode-manifest", required=True)
    args = ap.parse_args()
    dest, scratch, mlcode = Path(args.dest), Path(args.scratch), Path(args.mlcode_tree)
    for sub in ("merge_raw", "post_mlcode"):
        (scratch / sub).mkdir(parents=True, exist_ok=True)
    with open(args.mlcode_manifest, encoding="utf-8") as fh:
        ml_files = {f["path"]: f for f in json.load(fh)["files"] if not f["path"].startswith("util/ad-hoc/")}
    mine = set(_carrier_paths())
    report = []
    for path in sorted(mine | set(ml_files)):
        target = dest / path
        target.parent.mkdir(parents=True, exist_ok=True)
        row = {"path": path}
        if path in mine and path not in ml_files:
            shutil.copyfile(path, target)
            row["source"] = "ml-tests"
        elif path in ml_files and path not in mine:
            base = _run(["git", "show", f"{args.mlcode_base}:{path}"])
            main_now = _run(["git", "show", f"HEAD:{path}"])
            if ml_files[path]["status"] != "added" and base.stdout != main_now.stdout:
                raise SystemExit(f"{path}: main moved it since ml-code's base; a copy would revert main")
            shutil.copyfile(mlcode / path, target)
            row["source"] = "ml-code"
        else:
            flat = path.replace("/", "__")
            base_file = scratch / "merge_raw" / f"{flat}.base"
            base_file.write_text(_run(["git", "show", f"{args.mlcode_base}:{path}"]).stdout, encoding="utf-8")
            raw = _run(["git", "merge-file", "-p", path, str(base_file), str(mlcode / path)])
            (scratch / "merge_raw" / f"{flat}.raw").write_text(raw.stdout, encoding="utf-8")
            row["raw_conflicts"] = raw.returncode
            union = _run(["git", "merge-file", "-p", "--union", path, str(base_file), str(mlcode / path)])
            text = union.stdout
            notes = []
            for old, new in FIXUPS.get(path, []):
                if text.count(old) != 1:
                    raise SystemExit(f"{path}: fixup anchor found {text.count(old)} times")
                text = text.replace(old, new)
                notes.append("fixup applied")
            if path == "docs/REFERENCE.md":
                text, more = _reference_fixups(text)
                notes += more
            if re.search(r"^(<<<<<<<|=======|>>>>>>>)( |$)", text, re.M):
                raise SystemExit(f"{path}: conflict marker survived")
            target.write_text(text, encoding="utf-8")
            (scratch / "post_mlcode" / flat).write_text(text, encoding="utf-8")
            row.update({"source": "merged", "fixups": notes})
        row["sha256"] = _sha(target)
        report.append(row)
        print(json.dumps(row))
    with open(scratch / "overlay.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
