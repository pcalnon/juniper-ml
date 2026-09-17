#!/usr/bin/env python3
"""Which soak run actually READ ledger CONTENT, as opposed to seeing its filename?

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc
Author:      Paul Calnon
License:     MIT License
Created:     2026-09-15
Status:      ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md Sec 5

Why
---
The owner ruled (2026-09-15) that the ledger leak invalidates ONLY the run that read ledger
CONTENT -- not the seven that saw only its filename. Acting on that means naming one `obs_id`
and retiring it from the instrument of record, so the identification has to be measured.

TWO INSTRUMENTS DISAGREE ABOUT WHAT THEY MEASURE, AND ONLY ONE ANSWERS THIS QUESTION:

  * `2026-09-08_soak_label_to_transcript.py`'s `ledger=N` column counts LEDGER_MARKERS, which
    includes the bare filename stem. It is NOT a content count -- reading it as one is a
    recorded error from this arc.
  * `2026-08-21_soak_probe_evidence.py::ledger_exposure` is three-valued and keys on
    LEDGER_CONTENT_KEYS ('"obs_id"', '"scored_by"', '"discriminator_ok"', '"miss_class"'),
    i.e. fields that only appear if a ledger RECORD came back.

This uses the second, per transcript, and prints the per-run split so the single content read
is named rather than inferred.

Read-only. Mutates nothing.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]


def load(path: pathlib.Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    binder = load(ROOT / "util" / "ad-hoc" / "2026-09-08_soak_label_to_transcript.py", "binder")
    screen = load(ROOT / "util" / "ad-hoc" / "2026-08-21_soak_probe_evidence.py", "screen")

    ledger_path = ROOT / "reports" / "soak" / "pointer_follow_soak.jsonl"
    obs = binder.load_ledger(ledger_path)
    transcripts = binder.discover_transcripts()
    bound = binder.bind(obs, transcripts)

    print(f"{'ts':<22}{'probe':<38}{'content':>8}{'filename':>9}  obs_id")
    print("-" * 110)
    content_rows = []
    for b in bound:
        p = b.get("transcript")
        if not p:
            continue
        r = screen.scan(pathlib.Path(p))
        c = r.get("ledger_content_hits", 0)
        f = r.get("ledger_filename_hits", 0)
        if not (c or f):
            continue
        probe = (b.get("probe_id") or "?")[:36]
        print(f"{b.get('ts',''):<22}{probe:<38}{c:>8}{f:>9}  {b.get('obs_id','')}")
        if c:
            content_rows.append(b)

    print("-" * 110)
    print(f"runs with any ledger contact : {sum(1 for b in bound if b.get('transcript'))}"
          f"  (of {len(bound)} bound)")
    print(f"runs that read ledger CONTENT: {len(content_rows)}")
    for b in content_rows:
        print(f"    -> obs_id={b.get('obs_id')}  ts={b.get('ts')}  "
              f"probe={b.get('probe_id')}  outcome={b.get('outcome')}")
    if len(content_rows) != 1:
        print("\n  *** NOT exactly one. The owner's ruling names ONE run; do not invalidate")
        print("      anything until this disagreement with Sec 5 is resolved. ***")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
