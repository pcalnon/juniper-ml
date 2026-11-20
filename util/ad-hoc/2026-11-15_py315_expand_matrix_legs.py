#!/usr/bin/env python3
"""Expand the Python-version matrices of the given workflow files and print each leg's check name and its
continue-on-error value, so a change's leg names can be compared before and after (base vs worktree).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-15
Status: ad-hoc -- investigation (verification for the Python 3.15 informational-leg PRs, juniper-cascor#759 and
        juniper-cascor-worker#228)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_py315_informational_juniper-cascor.py and ..._juniper-cascor-worker.py (the edits
         whose leg names this checked); util/ad-hoc/2026-11-15_py315_compare_legs.bash (its caller)

Helper for the Python 3.15 informational-leg rollout (2026-11-14). Implements GitHub's documented matrix
semantics for the shapes used here: the cartesian product of the non-include keys, then each ``include`` entry is
merged into every ORIGINAL combination it would not overwrite, or else appended as a new combination. A ``name:``
that references ``matrix.*`` is rendered; a static name gets the combination's values appended in parentheses.

Usage: expand_matrix_legs.py <workflow.yml> [...]
"""

from __future__ import annotations

import itertools
import re
import sys
from pathlib import Path

import yaml

EXPR = re.compile(r"\$\{\{\s*matrix\.([A-Za-z0-9_-]+)\s*\}\}")
COE = re.compile(r"^\$\{\{\s*matrix\.experimental\s*==\s*true\s*\}\}$")


def expand(matrix: dict) -> list[dict]:
    base_keys = [k for k in matrix if k not in ("include", "exclude")]
    combos = [dict(zip(base_keys, vals)) for vals in itertools.product(*(matrix[k] for k in base_keys))] if base_keys else []
    originals = len(combos)
    for inc in matrix.get("include", []) or []:
        merged = False
        for c in combos[:originals]:
            if all(c.get(k, v) == v for k, v in inc.items() if k in base_keys):
                for k, v in inc.items():
                    if k not in base_keys:
                        c[k] = v
                merged = True
        if not merged:
            combos.append(dict(inc))
    return combos


def leg_name(job_name: str, combo: dict) -> str:
    if EXPR.search(job_name):
        return EXPR.sub(lambda m: str(combo.get(m.group(1), "")), job_name)
    return f"{job_name} ({', '.join(str(v) for v in combo.values())})"


def coe_value(job: dict, combo: dict) -> str:
    raw = job.get("continue-on-error")
    if raw is None:
        return "false (absent)"
    if isinstance(raw, bool):
        return str(raw).lower()
    if COE.match(str(raw).strip()):
        return str(combo.get("experimental") is True).lower()
    return f"UNEVALUATED: {raw}"


def main(paths: list[str]) -> int:
    for p in paths:
        data = yaml.safe_load(Path(p).read_text(encoding="utf-8"))
        for job_id, job in (data.get("jobs") or {}).items():
            matrix = (job.get("strategy") or {}).get("matrix")
            if not isinstance(matrix, dict) or not any("python" in str(k) for k in matrix):
                continue
            ff = (job.get("strategy") or {}).get("fail-fast")
            print(f"{Path(p).name}:{job_id}  fail-fast={ff}  needs={job.get('needs')}")
            for combo in expand(matrix):
                print(f"    {leg_name(str(job.get('name', job_id)), combo)!r:70}  continue-on-error={coe_value(job, combo)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
