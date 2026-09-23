#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: Performance lane -- D1 scope check
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License
Status:      ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/ad-hoc/2026-09-23_d1_scope_large_first_pass.yaml

Print each run's final metrics and completion for a suite built from
``2026-09-23_d1_scope_large_first_pass.yaml``, grouped by ``runtime.blas_threads``.

WHY: that suite's ``step_count`` is 8 in every cell, but 8 is BUDGET-BOUND under ``spiral-smoke``'s
budgets (the PF-2 re-spec §4.1 records "8 and 50 purely by budget"), so an identical step_count
there proves nothing. The final metrics are the only numerics fingerprint the suite path emits. If
they are identical across the two widths, the width did not reach the arithmetic. If they differ,
it did, even though the budget-pinned count could not show it.

Usage::

    python3 util/ad-hoc/2026-09-23_d1_scope_reduce.py ~/.local/state/juniper-experiments/suites/d1-scope-large-first-pass-<stamp>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

RUN_ROOT = Path.home() / ".local/state/juniper-experiments"

#: Fields that change on every run whatever the arithmetic did.
VOLATILE_FIELDS = frozenset({"timestamp"})


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("suite_dir", type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in (args.suite_dir / "registry.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    manifest = json.loads((args.suite_dir / "suite_manifest.json").read_text(encoding="utf-8"))
    overrides = {c["cell_id"]: c["overrides"] for c in manifest["cells"]}
    by_width: dict[str, list[dict]] = {}
    for row in rows:
        run_dir = RUN_ROOT / row["run_id"]
        final = json.loads((run_dir / "artifacts/results/metrics_final.json").read_text(encoding="utf-8"))
        run_manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        width = str(overrides[row["cell_id"]].get("runtime.blas_threads"))
        # `timestamp` differs on every run by construction. The first version of this script kept
        # it, reported "DIFFER" on four records whose every metric was bit-identical, and so
        # nearly turned a formatting field into a finding.
        flat = {k: v for k, v in final.items() if k not in VOLATILE_FIELDS and isinstance(v, (int, float, str)) and not isinstance(v, bool)}
        record = {"cell": row["cell_id"], "completion": run_manifest.get("completion_reason"), "thread_env": run_manifest.get("environment", {}).get("thread_env"), "final": flat}
        by_width.setdefault(width, []).append(record)
        print(f"{row['cell_id']}  blas_threads={width:<5} completion={record['completion']}")
        print(f"    thread_env={record['thread_env']}")
        print(f"    final={json.dumps(flat, sort_keys=True)[:600]}")
    print()
    finals = {w: {json.dumps(r["final"], sort_keys=True) for r in recs} for w, recs in by_width.items()}
    for width, distinct in finals.items():
        print(f"blas_threads={width}: {len(distinct)} distinct final-metric record(s) across {len(by_width[width])} run(s)")
    all_distinct = set().union(*finals.values()) if finals else set()
    print(f"ACROSS widths: {len(all_distinct)} distinct final-metric record(s) -> {'IDENTICAL' if len(all_distinct) == 1 else 'DIFFER'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
