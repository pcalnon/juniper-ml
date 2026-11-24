#!/usr/bin/env python3
"""Probe the flood-4 round-2 "ml-propose" carrier's REFERENCE composer on release shapes beyond patch and minor.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation (adversarial validation, claims/docs/conventions lens)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2507; Overtoad ruling "Carry + extend propose.py"; util/release_train/propose.py step 5b-v;
         util/ad-hoc/2026-11-08_flood4r2_val_ml-propose_scenarios.py (the whole-proposal scenarios)

In memory only (nothing is written): the carrier's ``apply_reference_compat_cochanges`` and
``_reference_compat_items`` run on the live docs/REFERENCE.md and pyproject.toml of ``--tree``, edited as each
case says, and the statuses and checklist lines are printed:

(a) a fourth [recurrence] pin added, then a patch; (b) a column package removed from every extra, then a minor;
(c) a pre-release meta version; (d) the MERGEABLE hand column-floor raise (current row rewritten in place under
the published version), then a patch -- does the REVIEW line still name the in-place row?; (e) the same for a
hand [recurrence] raise (clause pins rewritten under the published version) -- does it name the old pins?

Usage: python3 -B util/ad-hoc/2026-11-08_flood4r2_val_ml-propose_edge_probe.py --tree <carrier copy>
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tree", required=True)
    args = ap.parse_args()
    tree = Path(args.tree).resolve()
    sys.path.insert(0, str(tree / "util" / "release_train"))
    import propose as pr  # noqa: E402,PLC0415 - the carrier's own module is the code under test

    ref = (tree / "docs" / "REFERENCE.md").read_text(encoding="utf-8")
    py = (tree / "pyproject.toml").read_text(encoding="utf-8")
    keys = ("version_cell", "declares", "matrix_row", "recurrence", "recurrence_moved", "moved")

    a = py.replace('version = "0.11.4"', 'version = "0.11.5"').replace('    "juniper-recurrence-client>=0.3.0,<0.4.0",\n', '    "juniper-recurrence-client>=0.3.0,<0.4.0",\n    "juniper-recurrence-bench>=0.1.0,<0.2.0",\n')
    out, rep = pr.apply_reference_compat_cochanges(ref, a)
    i = out.find("The three `recurrence` pins")
    print("(a) fourth [recurrence] pin, patch:", {k: rep[k] for k in keys})
    print("    ", out[i : i + 360])

    b = py.replace('version = "0.11.4"', 'version = "0.12.0"').replace('    "juniper-cascor-worker>=0.4.0",\n', "")
    _, rep = pr.apply_reference_compat_cochanges(ref, b)
    print("(b) column package removed, minor:", {k: rep[k] for k in keys})
    print("    checklist:", pr._reference_compat_items(rep, meta_bump=True, pins_moved=False)[:2])

    c = py.replace('version = "0.11.4"', 'version = "0.12.0rc1"')
    out, rep = pr.apply_reference_compat_cochanges(ref, c)
    print("(c) pre-release meta version:", {k: rep[k] for k in keys})

    d0 = py.replace('"juniper-data[api]>=0.17.1"', '"juniper-data[api]>=0.18.0"')
    _, specs, _ = pr.meta_reference_pins(d0)
    ref_hand, status = pr.set_reference_matrix_row(ref, "0.11.4", specs)
    _, rep = pr.apply_reference_compat_cochanges(ref_hand, d0.replace('version = "0.11.4"', 'version = "0.11.5"'))
    items = pr._reference_compat_items(rep, meta_bump=True, pins_moved=False)
    print(f"(d) hand column raise (row {status} under 0.11.4), then patch:", {k: rep[k] for k in keys})
    print("    a REVIEW line names the in-place row:", any("moved in place" in item for item in items))

    e0 = py.replace('"juniper-recurrence>=0.8.1,<0.9.0"', '"juniper-recurrence>=0.8.2,<0.9.0"')
    _, _, recurrence = pr.meta_reference_pins(e0)
    ref_hand, old = pr.set_reference_recurrence_clause(ref, "0.11.4", recurrence)
    _, rep = pr.apply_reference_compat_cochanges(ref_hand, e0.replace('version = "0.11.4"', 'version = "0.11.5"'))
    items = pr._reference_compat_items(rep, meta_bump=True, pins_moved=False)
    print("(e) hand [recurrence] raise (clause pins rewritten under 0.11.4), then patch:", {k: rep[k] for k in keys}, "recurrence_old:", rep["recurrence_old"])
    print("    a REVIEW line names the previously published pins:", any("[recurrence] pins moved" in item for item in items))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
