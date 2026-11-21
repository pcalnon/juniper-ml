"""
Line up the wire-probe records of several targets and list every resume frame the targets answer differently.

Reads the JSON files ``2026-11-12_flood4r2_val_d14-resume_wire_probe.py`` wrote (one per target), reduces each case
to one signature (the frames after ``connection_established``, the close if the server closed, and what the socket
then received live), and writes:

  matrix.txt   every buffer state and case, one signature per target, targets with the same signature sharing a letter
  matrix.json  the same, structured, plus for each named pair of targets the cases on which the two differ

It also checks the probe itself: no probe timeout, the same server state before each case on every target, and the
witness client receiving the live broadcast.

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
import string
from pathlib import Path


def signature(record: dict) -> str:
    """One case as a single line: handshake frames, a server close if any, then the live frames."""
    parts = [" ".join(record["handshake"]) or "(nothing)"]
    closed = record["close_after_handshake"]
    if closed is not None:
        parts.append(f"CLOSED {closed['code']} {closed['reason']!r}")
    else:
        parts.append("live: " + (" ".join(record["live"]) or "(nothing)"))
        if record["close"] is not None:
            parts.append(f"CLOSED LATER {record['close']['code']} {record['close']['reason']!r}")
    return " | ".join(parts)


def load(path: Path) -> dict:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def probe_problems(targets: list[dict]) -> list[str]:
    """Anything that would make a record untrustworthy."""
    problems: list[str] = []
    reference: dict[tuple[str, str], dict] = {}
    for target in targets:
        for record in target["cases"]:
            key = (record["state"], record["case"])
            for label in ("close_after_handshake", "close"):
                closed = record[label]
                if closed is not None and closed["code"] is None:
                    problems.append(f"{target['target']} {key}: {closed['reason']}")
            before = {name: record["state_before"][name] for name in ("current_seq", "buffered_seqs", "capacity")}
            if reference.setdefault(key, before) != before:
                problems.append(f"{target['target']} {key}: server state before the case {before} differs from {reference[key]}")
            if record["witness_live"] is None:
                problems.append(f"{target['target']} {key}: the witness client did not receive the live broadcast")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--pair", action="append", default=[], help="two target names joined by a comma; repeatable")
    parser.add_argument("probe", type=Path, nargs="+", help="probe JSON files, in column order")
    args = parser.parse_args()

    targets = [load(path) for path in args.probe]
    names = [target["target"] for target in targets]
    by_target = {target["target"]: {(record["state"], record["case"]): record for record in target["cases"]} for target in targets}
    keys = [(record["state"], record["case"]) for record in targets[0]["cases"]]

    rows = []
    lines = ["targets: " + "; ".join(f"{name} ({target['files']['training_stream']['sha256'][:12]} / {target['files']['manager']['sha256'][:12]})" for name, target in zip(names, targets)), ""]
    current_state = None
    for state, case in keys:
        if state != current_state:
            current_state = state
            before = by_target[names[0]][(state, case)]["state_before"]
            lines.append(f"===== state {state}: capacity {before['capacity']}, last seq numbered {before['current_seq']}, buffered seqs {before['buffered_seqs']} =====")
        signatures = {name: signature(by_target[name][(state, case)]) for name in names}
        letters: dict[str, str] = {}
        for name in names:
            letters.setdefault(signatures[name], string.ascii_uppercase[len(letters)])
        classes = "".join(letters[signatures[name]] for name in names)
        rows.append({"state": state, "case": case, "sent": by_target[names[0]][(state, case)]["sent"], "classes": classes, "signatures": signatures})
        lines.append(f"[{classes}] {case}")
        for text, letter in letters.items():
            lines.append(f"      {letter}: {text}")

    pairs = {}
    for pair in args.pair:
        left, right = pair.split(",")
        differing = [{"state": row["state"], "case": row["case"], left: row["signatures"][left], right: row["signatures"][right]} for row in rows if row["signatures"][left] != row["signatures"][right]]
        pairs[pair] = {"differing_cases": len(differing), "of": len(rows), "cases": differing}
        lines.append("")
        lines.append(f"===== {left} vs {right}: {len(differing)} of {len(rows)} cases differ =====")
        for item in differing:
            lines.append(f"  {item['state']:10s} {item['case']}")
            lines.append(f"      {left}: {item[left]}")
            lines.append(f"      {right}: {item[right]}")

    problems = probe_problems(targets)
    lines.append("")
    lines.append(f"probe problems: {len(problems)}")
    lines.extend("  " + problem for problem in problems)

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with open(args.out_dir / "matrix.txt", "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    with open(args.out_dir / "matrix.json", "w", encoding="utf-8") as handle:
        json.dump({"targets": names, "rows": rows, "pairs": pairs, "probe_problems": problems}, handle, indent=1)
        handle.write("\n")
    summary = ", ".join(f"{pair}: {value['differing_cases']}/{value['of']}" for pair, value in pairs.items())
    print(f"{len(rows)} cases x {len(names)} targets; differing: {summary}; probe problems: {len(problems)}")


if __name__ == "__main__":
    main()
