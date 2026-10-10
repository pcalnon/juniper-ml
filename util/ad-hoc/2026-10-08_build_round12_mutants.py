#!/usr/bin/env python3
"""
Build the round-12 mutant set of the line read, reports/2026-10-04_consolidated-development-plan/round12-mutants.json.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-08
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-08_line_read_mutation_run.py (which runs the set);
         util/ad-hoc/2026-10-05_masked_finding_shape.py (the read the set mutates);
         reports/2026-10-04_consolidated-development-plan/round12-reconciliation.md

The set is: round 11's 23 mutants, retargeted where round 12's redesign of the read moved their text; Lane A's seven
survivors (its six recorded mutants plus X4, which drops SECRET from the env words); Lane B1's sixteen, retargeted
likewise; and eleven mutants of the code round 12 added. Its inputs were the three rounds' mutant files in the session
scratchpads, which do not outlive the sessions: the archived JSON is the record, and this script shows how it was made.
Every replacement must match the read exactly once; the script says which do not.

Usage
-----
    python3 -B util/ad-hoc/2026-10-08_build_round12_mutants.py --r11 <mutants_r11c.json> --lane-a <mutants_r12a.json> \\
        --lane-b1 <mutants_r12b1.json> --read <read.py> --out <round12-mutants.json>
"""
import argparse
import json
import sys
from pathlib import Path

LISTED = 'random-looking={random_looking(text)}: {mask(text)}")\n            below'
ALL = '                print(f"{rel}:{n} random-looking={random_looking(text)}: {mask(text)}")'
KEYP = '            print(f"    L{n} len={len(text)}{offset} random-looking={random_looking(text)}: {mask(text)}")'
MASK_RET = '    return MASK_RE.sub(lambda m: _cls(m.group(0)) if RUN_RE.fullmatch(m.group(0)) else f"<P{len(m.group(0))}>", text)'
NAMES_IN_CLEAR = [[MASK_RET, "    parts, pos = [], 0\n    for nm in NAME_RE.finditer(text):\n"
                   "        parts.append(MASK_RE.sub(lambda m: _cls(m.group(0)) if RUN_RE.fullmatch(m.group(0)) else f\"<P{len(m.group(0))}>\", text[pos:nm.start()]))\n"
                   "        parts.append(nm.group(0))\n        pos = nm.end()\n"
                   "    parts.append(MASK_RE.sub(lambda m: _cls(m.group(0)) if RUN_RE.fullmatch(m.group(0)) else f\"<P{len(m.group(0))}>\", text[pos:]))\n"
                   "    return \"\".join(parts)"]]
RETARGET_R11 = {
    "M6 listed line cut to 70 characters": [[LISTED, LISTED.replace("{mask(text)}", "{mask(text[:70])}")]],
    "M7 KEY mode byte column ignored": [['offset = f" offset={char_col(text, col, n == 1)}"', 'offset = f" offset={col - 1}"']],
    "M8 Authorization removed": [['"key|(?<![A-Za-z0-9])authori" + "zation(?![A-Za-z0-9]))"', '"key)"']],
    "M12 KEY mode text before the column unmasked": [[KEYP, KEYP.replace("{mask(text)}", "{text if n == first else mask(text)}")]],
    "M18 name parts unmasked": NAMES_IN_CLEAR,
    "M22 --all prints nothing": [[ALL, "                pass"]],
    "M23 --all prints a 70-character window": [[ALL, ALL.replace("{mask(text)}", "{mask(text[:70])}")]],
}
RETARGET_B1 = {
    "C3g": [[KEYP, KEYP.replace("{mask(text)}", "{mask(text) if n == first else text}")]],
    "C4f": [["    if root.is_symlink() or not root.is_dir():\n        return [], ", "    if not root.is_dir():\n        return [], "]],
    "Xrl": [[ALL, ALL.replace("random-looking={random_looking(text)}", "random-looking=0")]],
}
X4 = [['"API_KEYS?|TOK" + "EN|PASS" + "WORD|SEC" + "RET"', '"API_KEYS?|TOK" + "EN|PASS" + "WORD"']]
NEW = [
    ("R12N-names-in-clear", "names printed in clear (the frozen read's behaviour, R12A-02, R12B1-06)", NAMES_IN_CLEAR),
    ("R12N-key-symlink", "KEY mode follows a symlink (R12B1-04)", [["        if stat.S_ISLNK(st.st_mode):\n            raise", "        if False:\n            raise"]]),
    ("R12N-key-special", "KEY mode opens a special file (R12B1-04)", [["    if not stat.S_ISREG(st.st_mode):\n        raise", "    if False:\n        raise"]]),
    ("R12N-key-window", "KEY mode prints a 100-character window again (R12B1-10)", [[KEYP, KEYP.replace("{mask(text)}", "{mask(text[:100])}")]]),
    ("R12N-key-offset", "KEY mode prints no offset (R12B1-10)", [['offset = f" offset={char_col(text, col, n == 1)}" if n == first else ""', 'offset = ""']]),
    ("R12N-argv-pass", "openssl's argv-list -pass spelling not a marker (R12B1-05)", [["(?:[ \\\\t]+[\\\"']?|[\\\"'][ \\\\t]*,[ \\\\t]*[\\\"'])pass:", "(?:[ \\\\t]+[\\\"']?)pass:"]]),
    ("R12N-password", "-password not a marker (R12B1-05)", [['-pass(?:in|out|w" + "ord)?', "-pass(?:in|out)?"]]),
    ("R12N-argv-k", "-k as a list item not a marker (R12B1-05)", [["(?=[ \\\\t=]|[\\\"'][ \\\\t]*,)", "(?=[ \\\\t=])"]]),
    ("R12N-underscore-auth", "authorization after _ not a name (R12B1-05)", [['"key|(?<![A-Za-z0-9])authori"', '"key|\\\\bauthori"']]),
    ("R12N-hex", "hex keys and UUIDs not counted (R12B1-11)", [["        if HEX_RE.search(tok) or UUID_RE.search(tok):", "        if False:"]]),
    ("R12N-uuid", "UUIDs not counted (R12B1-11)", [["        if HEX_RE.search(tok) or UUID_RE.search(tok):", "        if HEX_RE.search(tok):"]]),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--r11", required=True, type=Path, help="round 11's mutants: an object of id -> reps")
    ap.add_argument("--lane-a", required=True, type=Path, help="round 12 Lane A's recorded mutants: an object of id -> reps")
    ap.add_argument("--lane-b1", required=True, type=Path, help="round 12 Lane B1's mutants: a list of {id, desc, reps}")
    ap.add_argument("--read", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()
    read = args.read.read_text(encoding="utf-8")
    out = []
    for k, reps in json.loads(args.r11.read_text(encoding="utf-8")).items():
        out.append({"id": "R11-" + k.split(" ", 1)[0], "desc": "round 11 " + k + (" (retargeted)" if k in RETARGET_R11 else ""), "reps": RETARGET_R11.get(k, reps)})
    lane_a = [{"id": "A" + k, "desc": "Lane A " + k + ": " + k, "reps": v} for k, v in json.loads(args.lane_a.read_text(encoding="utf-8")).items()]
    lane_a.append({"id": "AX4", "desc": "Lane A X4: SECRET dropped", "reps": X4})
    out += [dict(m, id="R12" + m["id"]) for m in lane_a]
    for m in json.loads(args.lane_b1.read_text(encoding="utf-8")):
        if m["reps"] and m["id"] not in ("K6", "K19"):  # B1's controls are round 11's M6 and M19, already in the set
            out.append({"id": "R12B1-" + m["id"], "desc": "B1 " + m["desc"] + (" (retargeted)" if m["id"] in RETARGET_B1 else ""), "reps": RETARGET_B1.get(m["id"], m["reps"])})
    out += [{"id": i, "desc": d, "reps": r} for i, d, r in NEW]
    unmatched = [m["id"] for m in out for old, _ in m["reps"] if read.count(old) != 1]
    args.out.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"{len(out)} mutants written; replacements not matching exactly once: {unmatched or 'none'}")
    return 1 if unmatched else 0


if __name__ == "__main__":
    sys.exit(main())
