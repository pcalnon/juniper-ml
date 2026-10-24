#!/usr/bin/env python3
"""
Build the round-13 mutant set of the line read, reports/2026-10-04_consolidated-development-plan/round13-mutants.json.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-10
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-08_line_read_mutation_run.py (which runs the set);
         util/ad-hoc/2026-10-05_masked_finding_shape.py (the read the set mutates);
         util/ad-hoc/2026-10-08_build_round12_mutants.py (the round-12 set's builder, this one's model);
         reports/2026-10-04_consolidated-development-plan/round13-laneA-reprobe.md and round13-laneB1-safety.md

The set is: round 12's 57 entries (reports/2026-10-04_consolidated-development-plan/round12-mutants.json), retargeted
where round 13's changes to the read moved their text (none had to be); the round-13 lanes' surviving mutants, each
given by its lane as an exact replacement (round13-mutants-laneA.json, round13-mutants-laneB1.json and
round13-mutants-laneB1-2.json in the same directory; round 13: R13A-12), with the two whose anchor round 13 removed
retargeted, ``len={len(text)} names=``, since an entry prints no count of names (R13B1-09); and twelve mutants of the
code round 13 added, each breaking one of its new pins. An entry with no replacement is not a mutant and is left
out, by name. Every replacement must match the read exactly once, in order, and change it; the script says which do
not.

The set is deduplicated by the read each entry builds (round 13: R13A-05: round 12's 57 entries built 53 distinct
reads): the first entry to build a read is kept, and the ids of the later ones are recorded in its ``collapsed``
list and printed.

Usage
-----
    python3 -B util/ad-hoc/2026-10-10_build_round13_mutants.py --r12 <round12-mutants.json> \\
        --lane-a <round13-mutants-laneA.json> --lane-b1 <round13-mutants-laneB1.json> \\
        --lane-b1-2 <round13-mutants-laneB1-2.json> --read <read.py> --out <round13-mutants.json>
Exit 0 when every entry builds a changed read; 1 otherwise.
"""
import argparse
import json
import sys
from pathlib import Path

# the round-12 entries whose anchor round 13 moved: none, because round 13's edits kept every anchor's text
RETARGET_R12 = {}
# the lanes' entries whose anchor round 13 removed: the entry's names= field (R13B1-09)
ENTRY_LEN = "len={len(text)} random-looking="
RETARGET_LANES = {
    "R13B1-M2-prefix-tail": [[ENTRY_LEN, "len={len(text)}{text[-3:]} random-looking="]],
    "R13B1-M2b-prefix-tail-alnum": [[ENTRY_LEN, "len={len(text)}{''.join(c for c in text[-3:] if c.isalnum())} random-looking="]],
}
ALT_UNDERSCORE = '"|(?<![A-Za-z0-9])_+(?:[A-Z][A-Z0-9_]*_)?(?:" + _ENV_WORDS + ")(?:_[A-Z0-9]+)*(?![A-Za-z0-9])"'
BAD_KEY = 'print(f"BAD KEY {where}: {mask(key)}", file=sys.stderr)'
NEW = [
    ("R13N-blanks-raw", "clause 3: blanks other than spaces and tabs print as they are (R13B1-14)",
     [['    return BLANK_RE.sub(lambda m: f"<S{len(m.group(0))}>", _mask_runs(text))', "    return _mask_runs(text)"]]),
    ("R13N-blanks-ascii-only", "clause 3: only CR, VT and FF are masked; 0x1C-0x1F, NEL, NBSP and the Unicode spaces print as they are (R13B1-14)",
     [['BLANK_RE = re.compile(r"[^\\S \\t]+")', 'BLANK_RE = re.compile(r"[\\r\\x0b\\x0c]+")']]),
    ("R13N-env-underscore-dropped", "clause 1: env names after leading underscores not listed (R13B1-08)", [[ALT_UNDERSCORE, '""']]),
    ("R13N-env-one-underscore", "clause 1: an env name after one underscore (_TOKEN) not listed (R13B1-08)",
     [['"|(?<![A-Za-z0-9])_+(?:[A-Z]', '"|(?<![A-Za-z0-9])__(?:[A-Z]']]),
    ("R13N-env-trailing-underscore", "clause 1: an env name with trailing underscores (__API_KEY__) not listed (R13B1-08)",
     [['(?:_[A-Z0-9]+)*(?![A-Za-z0-9])"', '(?:_[A-Z0-9]+)*(?![A-Za-z0-9_])"']]),
    ("R13N-names-count", "clause 3: an entry prints its count of names again (R13B1-09)",
     [[ENTRY_LEN, "len={len(text)} names={len(NAME_RE.findall(text))} random-looking="]]),
    ("R13N-bad-key-clear", "clause 3: a malformed KEY prints in clear (R13B1-10)", [[BAD_KEY, 'print(f"BAD KEY {where}: {key}", file=sys.stderr)']]),
    ("R13N-bad-key-unplaced", "clause 3: a malformed KEY prints without its place (R13B1-10)", [[BAD_KEY, 'print(f"BAD KEY {mask(key)}", file=sys.stderr)']]),
    ("R13N-keys-file-unchecked", "clause 4: --keys-file read without its lstat check, through a symlink or into a FIFO (R13B1-11)",
     [["    mode = os.lstat(name).st_mode\n", "    mode = stat.S_IFREG\n"]]),
    ("R13N-start-after-end", "clause 4: a START after its END is not named as such (R13B1-17)", [["        if first > last:\n", "        if False:\n"]]),
    ("R13N-col-past-end", "clause 4: a column past its line's end is read, clamped to the end (R13B1-17)",
     [['    return 0 <= off < len(text.encode("utf-8"))', "    return 0 <= off"]]),
    ("R13N-value-error", "clause 4: a number too long to read (or a NUL in a path) crashes KEY mode (R13B1-11)",
     [["except (Refused, OSError, ValueError) as exc:  # ValueError: a NUL", "except (Refused, OSError) as exc:  # ValueError: a NUL"]]),
]


def build(read: str, reps: list) -> str:
    """The read each entry builds, or "" when a replacement does not match exactly once or nothing changes."""
    text = read
    for old, new in reps:
        if text.count(old) != 1:
            return ""
        text = text.replace(old, new)
    return "" if text == read else text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--r12", required=True, type=Path, help="round 12's set: a list of {id, desc, reps}")
    ap.add_argument("--lane-a", required=True, type=Path, help="round 13 Lane A's mutants: a list of {id, desc, reps}")
    ap.add_argument("--lane-b1", required=True, type=Path, help="round 13 Lane B1's first mutants file")
    ap.add_argument("--lane-b1-2", required=True, type=Path, help="round 13 Lane B1's second mutants file")
    ap.add_argument("--read", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    read = args.read.read_text(encoding="utf-8")
    entries = []
    for m in json.loads(args.r12.read_text(encoding="utf-8")):
        entries.append({"id": m["id"], "desc": m["desc"] + (" (retargeted in round 13)" if m["id"] in RETARGET_R12 else ""), "reps": RETARGET_R12.get(m["id"], m["reps"])})
    no_reps = []
    for path in (args.lane_a, args.lane_b1, args.lane_b1_2):
        for m in json.loads(path.read_text(encoding="utf-8")):
            if not m.get("reps"):
                no_reps.append(m["id"])
                continue
            entries.append({"id": m["id"], "desc": m["desc"] + (" (retargeted)" if m["id"] in RETARGET_LANES else ""), "reps": RETARGET_LANES.get(m["id"], m["reps"])})
    entries += [{"id": i, "desc": d, "reps": r} for i, d, r in NEW]
    out, kept, unbuilt = [], {}, []
    for m in entries:
        text = build(read, m["reps"])
        if not text:
            unbuilt.append(m["id"])
            out.append(m)
        elif text in kept:
            kept[text].setdefault("collapsed", []).append(m["id"])
        else:
            kept[text] = m
            out.append(m)
    args.out.write_text(json.dumps(out, indent=1), encoding="utf-8")
    collapsed = [f"{m['id']} <- {', '.join(m['collapsed'])}" for m in out if m.get("collapsed")]
    print(f"{len(entries)} entries read, {len(out)} written ({len(kept)} distinct reads); left out with no replacement: {no_reps or 'none'}")
    print(f"collapsed by built read: {collapsed or 'none'}")
    print(f"replacements not matching exactly once, or changing nothing: {unbuilt or 'none'}")
    return 1 if unbuilt else 0


if __name__ == "__main__":
    sys.exit(main())
