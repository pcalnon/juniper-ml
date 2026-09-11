#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: Performance lane -- PF-8 follow-up
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Reducer for ``2026-09-11_omp_icv_checkpoint_probe.py --mode growth``.

It answers the question the raw checkpoint list cannot: **does the observed burst actually end
where the ICV drops?** An ICV reading is a statement about what a thread WOULD do; the burst is
what the process DID. Asserting the first settles the second is the "instrument answers an
adjacent question" failure -- so this aligns the two series and reports the gap.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--json", type=Path, required=True, help="a growth-mode result file")
    parser.add_argument("--busy-threshold", type=int, default=10, help="threads at/above this count a sample as bursting")
    args = parser.parse_args()

    data = json.loads(args.json.read_text(encoding="utf-8"))
    if data.get("mode") != "growth":
        print(f"not a growth-mode file: mode={data.get('mode')!r}")
        return 2

    checkpoints = [c for c in data["checkpoints"] if "omp_icv_max_threads" in c]
    train = [c for c in checkpoints if c["thread_name"] != "MainThread"]

    # The ICV transition on the TRAINING thread: first checkpoint whose ICV differs from entry.
    entry_icv = train[0]["omp_icv_max_threads"] if train else None
    transition = next((c for c in train if c["omp_icv_max_threads"] != entry_icv), None)

    samples = data["samples"]
    bursting = [s for s in samples if s["busy_threads"] >= args.busy_threshold]
    first_burst = bursting[0]["t"] if bursting else None
    last_burst = bursting[-1]["t"] if bursting else None

    print(f"file                  : {args.json}")
    print(f"training thread       : {train[0]['thread_name'] if train else '(none)'}  (ICV on entry {entry_icv})")
    if transition is None:
        print("ICV transition        : NONE -- the thread never left its entry width")
    else:
        print(
            f"ICV transition        : {entry_icv} -> {transition['omp_icv_max_threads']} "
            f"at t={transition['t']}  in `{transition['label']}`"
        )
    print(f"burst (>= {args.busy_threshold} threads) : {first_burst} -> {last_burst}  ({len(bursting)} of {len(samples)} samples)")
    # TWO DIFFERENT CLAIMS, and conflating them is the trap this block exists to prevent:
    #   (a) "the ICV drop ENDS the burst"      -- requires the drop to coincide with the burst end
    #   (b) "the ICV drop is why LATER passes do not burst" -- requires only that the drop
    #       precede the first later pass, and that nothing after it bursts
    # The measured answer is (b), NOT (a): the initial burst ends when the initial output pass
    # ends, and the drop lands ~3s later, inside candidate result collection.
    if transition is not None and last_burst is not None:
        gap = round(transition["t"] - last_burst, 4)
        print(f"\nclaim (a) 'the drop ENDS the burst': last burst sample -> ICV drop = {gap}s")
        print(f"  {'SUPPORTED' if abs(gap) <= 1.0 else 'REFUTED -- the burst was already over when the ICV dropped'}")

    after = [s for s in samples if transition is not None and s["t"] > transition["t"]]
    if after:
        peak_after = max(s["busy_threads"] for s in after)
        print(f"\nclaim (b) 'the drop is why LATER passes do not burst': peak busy threads after the drop = {peak_after}")
        print(f"  {'SUPPORTED' if peak_after < args.busy_threshold else 'REFUTED -- something bursts after the drop'} (over {len(after)} samples)")

    # Which stage was running during the burst, and which during the drop.
    def _stage_span(name: str) -> tuple[float, float] | None:
        starts = [c["t"] for c in train if c["label"] == f"{name}:before"]
        ends = [c["t"] for c in train if c["label"] == f"{name}:after"]
        return (starts[0], ends[0]) if starts and ends else None

    print("\nstage spans (first occurrence):")
    for name in ("train_output_layer", "train_candidates", "_ensure_worker_pool", "_collect_training_results", "_retrain_output_layer"):
        span = _stage_span(name)
        if span is None:
            continue
        covers_burst = first_burst is not None and span[0] <= first_burst and last_burst <= span[1]
        print(f"  {name:<28}{span[0]:>9} -> {span[1]:<9}{'   <-- contains the whole burst' if covers_burst else ''}")

    # Every stage that spans the transition, innermost last -- the localisation.
    if transition is not None:
        stage = transition["label"].rsplit(":", 1)[0]
        print(f"\nre-pin occurred inside : {stage}")
        open_stages = []
        for c in train:
            if c["t"] > transition["t"]:
                break
            label, _, edge = c["label"].rpartition(":")
            if edge == "before":
                open_stages.append(label)
            elif edge == "after" and open_stages and open_stages[-1] == label:
                open_stages.pop()
        print(f"enclosing stack        : {' > '.join(open_stages) if open_stages else '(none)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
