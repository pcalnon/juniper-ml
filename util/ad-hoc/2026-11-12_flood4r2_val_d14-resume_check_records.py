"""
Count, across the wire-probe outputs, server closes, sockets that missed the live broadcast, and differences by family.

Reads the JSON files ``2026-11-12_flood4r2_val_d14-resume_wire_probe.py`` wrote. For each target it prints the number
of cases, of server closes, of sockets that did not receive the broadcast made after the handshake, and of witness
clients that missed it. Then, for the first two files given (juniper-cascor's main and juniper-service-core's main),
it prints how many (buffer state, frame) pairs the two answer differently, grouped by the kind of frame:

  1  a negative integer ``last_seq``
  2  a resume frame whose ``data`` is not an object
  3  an integer ``last_seq`` above the last seq numbered
  4  a ``last_seq`` that is not a plain integer
  5  a stale ``server_instance_id`` together with a non-integer ``last_seq`` (the order of the two checks)

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11; juniper-cascor#754; the design check of whether juniper-service-core follows cascor's two new resume answers
"""

import json
import sys


def signature(record: dict) -> tuple:
    return (tuple(record["handshake"]), json.dumps(record["close_after_handshake"], sort_keys=True), tuple(record["live"]))


def family(case: str) -> str:
    if case in ("last_seq=-1", "last_seq=-5", "last_seq=-1000000000000000000000000000000"):
        return "1 negative integer"
    if case.startswith("data-") and case not in ("data-absent", "data-empty-object"):
        return "2 data not an object"
    if case in ("last_seq=6", "last_seq=1000"):
        return "3 above the last seq"
    if case.startswith("id-stale+"):
        return "5 check order"
    if case.startswith("last_seq="):
        return "4 not a plain integer"
    return "other"


def main() -> None:
    targets = []
    for path in sys.argv[1:]:
        with open(path, encoding="utf-8") as handle:
            targets.append(json.load(handle))
    for target in targets:
        cases = target["cases"]
        closes = sum(1 for record in cases if record["close_after_handshake"] is not None or record["close"] is not None)
        no_live = sum(1 for record in cases if not any("#" in label for label in record["live"]))
        witness = sum(1 for record in cases if record["witness_live"] is None)
        print(f"{target['target']:28s} cases {len(cases)}  server closes {closes}  no live frame {no_live}  witness missed live {witness}  stopped cleanly {target['server_stopped_cleanly']}")
    left = {(record["state"], record["case"]): record for record in targets[0]["cases"]}
    right = {(record["state"], record["case"]): record for record in targets[1]["cases"]}
    counts: dict[str, int] = {}
    frames: dict[str, set] = {}
    for key, record in left.items():
        if signature(record) != signature(right[key]):
            name = family(key[1])
            counts[name] = counts.get(name, 0) + 1
            frames.setdefault(name, set()).add(key[1])
    print(f"{targets[0]['target']} vs {targets[1]['target']}: {sum(counts.values())} differing pairs")
    for name in sorted(counts):
        print(f"  {name}: {counts[name]} pairs in {len(frames[name])} frames")


if __name__ == "__main__":
    main()
