#!/usr/bin/env python3
"""
Stage 5: `equities` and `equities_seq` go to generator_version 4.0.0.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: the 2026-09-09 owner rulings (register §4.9); the ecosystem data contract in
         Juniper/AGENTS.md, which states every generator is at 3.0.0 and must now say otherwise

MAJOR, not minor, and the version is load-bearing rather than cosmetic: `generator_version` is
hashed into `dataset_id`, so it is the only thing stopping a cached artifact of the old shape from
being served for a request made against the new contract. Two changes here are breaking on their
own -- the default feature matrix loses a column (16 -> 15, `adj_close` out), and `cost_basis` is
NaN before the purchase date where it used to be a constant -- and three more change values
silently: the as-of publication history, the floor, and the causal median.

Ruled 2026-09-09 with the published wheels in view: only these two generators move, and the
ecosystem note that says every generator is 3.0.0 is corrected in the same change. Rejected were
bumping all generators to keep that sentence literally true, and holding the change for a release
window.
"""
from __future__ import annotations

import sys
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--equities-causal-data-quality--20260911-2310--20cd6788")

EDITS = [
    ("juniper_data/generators/equities/generator.py", 'VERSION = "3.0.0"\n', 'VERSION = "4.0.0"\n'),
    ("juniper_data/generators/equities_seq/generator.py", 'VERSION = "3.0.0"\n', 'VERSION = "4.0.0"\n'),
    (
        "juniper_data/generators/equities/params.py",
        "``EQUITIES_FEATURE_COLUMNS`` (``defaults.py``; 16 as of generator 3.0.0), a one-hot next-day",
        "``EQUITIES_FEATURE_COLUMNS`` (``defaults.py``; 15 as of generator 4.0.0 -- ``adj_close`` left the\n    DEFAULTS in 4.0.0, see the note beside the list), a one-hot next-day",
    ),
    (
        "juniper_data/generators/equities_seq/generator.py",
        "off then on, hashed to the SAME ``equities_seq-3.0.0-e9b10e26ed01ae0e``, so",
        "off then on, hashed to the SAME ``equities_seq-3.0.0-e9b10e26ed01ae0e`` (the id is quoted as\n        it was measured, under the generator version current at the time; the binder fix and the\n        4.0.0 bump have both changed it since), so",
    ),
]


def main() -> int:
    for rel, old, new in EDITS:
        path = W / rel
        text = path.read_text()
        n = text.count(old)
        if n != 1:
            sys.exit(f"FAIL: {rel}: expected 1 match, found {n} for {old[:60]!r}")
        path.write_text(text.replace(old, new))
        print(f"  ok  {rel}")

    for rel, want in (("juniper_data/generators/equities/generator.py", '"4.0.0"'), ("juniper_data/generators/equities_seq/generator.py", '"4.0.0"')):
        assert want in (W / rel).read_text(), rel
    stale = [rel for rel in {e[0] for e in EDITS} if 'VERSION = "3.0.0"' in (W / rel).read_text()]
    if stale:
        sys.exit(f"FAIL: a 3.0.0 VERSION survives in {stale}")
    print("both generators at 4.0.0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
