"""
Print the wire-probe comparison as one short line per case: what two targets answer in each of the four buffer states.

Reads ``matrix.json`` (written by ``2026-11-12_flood4r2_val_d14-resume_compare.py``) and abbreviates each signature:

  ok(N)[a-b]     ``resume_ok`` with ``replayed_count`` N, then the replayed seqs a..b; no snapshot
  fail(R)+snap   ``resume_failed`` with reason R, then the fresh snapshot (initial_status, state, initial_metrics)
  snap           no resume reply at all, only the fresh snapshot
  CLOSED c       the server closed the socket with code c

A trailing ``!live`` marks a socket that did not receive the broadcast made after the handshake. Cases the two
targets answer alike in all four states are listed once, under SAME.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor#754; the design check of whether juniper-service-core follows cascor's two new resume answers
"""

import argparse
import json
import re
from pathlib import Path

SNAPSHOT = re.compile(r"initial_status state initial_metrics\(current_seq=\d+\)")
RESUME_OK = re.compile(r"resume_ok\(replayed_count=(\d+)\)")
RESUME_FAILED = re.compile(r"resume_failed\((\w+)\)")
SEQ = re.compile(r"#(\d+)")


def abbreviate(text: str) -> str:
    """A signature as a few characters; an unexpected shape is returned whole so it cannot hide."""
    parts = text.split(" | ")
    handshake = parts[0]
    closed = next((part for part in parts[1:] if part.startswith("CLOSED")), None)
    live = next((part for part in parts[1:] if part.startswith("live: ")), None)
    snapshot = bool(SNAPSHOT.search(handshake))
    rest = SNAPSHOT.sub("", handshake).strip()
    accepted = RESUME_OK.match(rest)
    refused = RESUME_FAILED.match(rest)
    if accepted and not snapshot:
        seqs = [int(found) for found in SEQ.findall(rest)]
        span = f"[{seqs[0]}-{seqs[-1]}]" if seqs else ""
        short = f"ok({accepted.group(1)}){span}"
    elif refused and snapshot and rest == refused.group(0):
        short = f"fail({refused.group(1)})+snap"
    elif snapshot and not rest:
        short = "snap"
    else:
        return text
    if closed is not None:
        return f"{short} {closed}"
    if live is None or "#" not in live:
        short += " !live"
    return short


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--matrix", type=Path, required=True)
    parser.add_argument("--left", required=True)
    parser.add_argument("--right", required=True)
    args = parser.parse_args()

    with open(args.matrix, encoding="utf-8") as handle:
        matrix = json.load(handle)
    states: list[str] = []
    cases: dict[str, dict[str, tuple[str, str]]] = {}
    for row in matrix["rows"]:
        if row["state"] not in states:
            states.append(row["state"])
        cases.setdefault(row["case"], {})[row["state"]] = (abbreviate(row["signatures"][args.left]), abbreviate(row["signatures"][args.right]))

    same = [case for case, cells in cases.items() if all(left == right for left, right in cells.values())]
    print(f"left = {args.left}; right = {args.right}; states = {states}")
    print(f"DIFFERENT in at least one state: {len(cases) - len(same)} of {len(cases)} cases")
    for case, cells in cases.items():
        if case in same:
            continue
        print(f"  {case}")
        for state in states:
            left, right = cells[state]
            mark = "==" if left == right else "!="
            print(f"      {state:10s} {left:34s} {mark} {right}")
    print(f"SAME in all four states: {len(same)} of {len(cases)} cases")
    for case in same:
        print(f"  {case}: " + "; ".join(f"{state} {cells[0]}" for state, cells in cases[case].items()))


if __name__ == "__main__":
    main()
