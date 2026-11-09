#!/usr/bin/env python3
"""
Make the harvested flood-4 validator probes clean under gate G-TMP before they ship in the record PR.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off (flood-4 disposition record PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (sec 7);
         util/tmp_path_literal_check.py on juniper-ml#2360's branch (gate G-TMP, not yet on main)

WHY THIS EXISTS
Four of the validators' probes name the system temp directory. None writes there: two DETECT writes there
(strace scans of a workflow step's mutant run), one refuses a TMPDIR that points there, and the rest is
docstring text. G-TMP counts any such line against a per-file baseline recorded when the gate lands, and a
file the baseline does not list may hold none, so these files would fail it once #2360 merges. A detector
line keeps its literal and gets G-TMP's own allow pragma; a docstring is reworded so it no longer carries
one. No behaviour changes. --check reports the G-TMP count (G-TMP's pattern, copied) and changes nothing.

Usage:
  2026-11-08_flood4_gtmp_pragma_pass.py [--check]
"""

import glob
import re
import sys

# G-TMP's own pattern and pragma (util/tmp_path_literal_check.py, juniper-ml#2360 head 0b256139).
PATTERN = re.compile(r"(?<![\w.~$})\]/])/(?:var/|private/)?tmp(?![\w-])")
PRAGMA = "tmp-path-literal: allow"
NOTE = "  # " + PRAGMA + " (detector: reads the system temp dir, never writes it)"

# Every line below that names the system temp directory is a string this script searches for, so it
# carries G-TMP's allow pragma itself.
REWORD = {
    "util/ad-hoc/2026-11-07_flood4_val_r2_canopy_tests_run.py": [
        ("afterwards the trace is searched for any path under /tmp or /var/tmp opened for writing or",  # tmp-path-literal: allow
         "afterwards the trace is searched for any path under the system temp dirs opened for writing or"),
        ("created, and for every open of a lockfile-commit*.json path. Also: a listing of /tmp lockfile",  # tmp-path-literal: allow
         "created, and for every open of a lockfile-commit*.json path. Also: a listing of the system temp dirs' lockfile"),
    ],
    "util/ad-hoc/2026-11-07_flood4_val_r2_canopy_tf1_mutant.py": [
        ("tmp_path (and fail on `not result.body.exists()`) rather than under /tmp?",  # tmp-path-literal: allow
         "tmp_path (and fail on `not result.body.exists()`) rather than under the system temp dir?"),
        ("lockfile-commit*.json open, and any /tmp or /var/tmp write.",  # tmp-path-literal: allow
         "lockfile-commit*.json open, and any write under the system temp dirs."),
    ],
    "util/ad-hoc/2026-11-07_flood4_val_canopy_tests_matrix.py": [
        ("tmp/, never /tmp); config files and logs go to the scratch dir (argument 2).",  # tmp-path-literal: allow
         "tmp/, never the system temp dir); config files and logs go to the scratch dir (argument 2)."),
    ],
    "util/ad-hoc/2026-11-07_flood4_val_py_typed_probe.py": [
        ("in a temp copy (under TMPDIR, never /tmp): as committed,",  # tmp-path-literal: allow
         "in a temp copy (under TMPDIR, never the system temp dir): as committed,"),
    ],
}
PRAGMA_LINES = {
    "util/ad-hoc/2026-11-07_flood4_val_r2_canopy_tests_run.py": [
        'for root in ("/tmp", "/var/tmp"):',  # tmp-path-literal: allow
        'if (path.startswith("/tmp/") or path.startswith("/var/tmp/")) and',  # tmp-path-literal: allow
    ],
    "util/ad-hoc/2026-11-07_flood4_val_r2_canopy_tf1_mutant.py": [
        'if path.startswith(("/tmp/", "/var/tmp/")) and re.search(',  # tmp-path-literal: allow
        '"tmp_lockfile_entries_after": sorted(n for n in os.listdir("/tmp")',  # tmp-path-literal: allow
    ],
    "util/ad-hoc/2026-11-07_flood4_val_canopy_tests_matrix.py": [
        'assert tmp_root and not tmp_root.startswith(("/tmp", "/var/tmp"))',  # tmp-path-literal: allow
    ],
}


def count():
    hits = []
    for p in sorted(glob.glob("util/ad-hoc/2026-11-0[78]_flood4_*.py")):
        with open(p, encoding="utf-8") as fh:
            for i, line in enumerate(fh.read().split("\n"), 1):
                if "tmp" in line and PATTERN.search(line) and PRAGMA not in line:
                    hits.append("%s:%d: %s" % (p, i, line.strip()[:160]))
    return hits


def main():
    if "--check" not in sys.argv[1:]:
        for path, pairs in REWORD.items():
            with open(path, encoding="utf-8") as fh:
                s = fh.read()
            for old, new in pairs:
                if s.count(new) == 1 and s.count(old) == 0:
                    continue  # already applied
                if s.count(old) != 1:
                    raise SystemExit("REFUSING: %r occurs %d times in %s" % (old, s.count(old), path))
                s = s.replace(old, new)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(s)
        for path, starts in PRAGMA_LINES.items():
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().split("\n")
            for st in starts:
                idx = [i for i, ln in enumerate(lines) if st in ln]
                if len(idx) != 1:
                    raise SystemExit("REFUSING: %r matches lines %s in %s" % (st, idx, path))
                if PRAGMA not in lines[idx[0]]:
                    lines[idx[0]] = lines[idx[0]].rstrip() + NOTE
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("\n".join(lines))
    hits = count()
    for h in hits:
        print(h)
    print("G-TMP literal lines: %d" % len(hits))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
