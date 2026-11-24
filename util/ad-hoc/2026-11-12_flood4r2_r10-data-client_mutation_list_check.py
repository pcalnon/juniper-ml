#!/usr/bin/env python3
"""
Read a repository's shipped Gitleaks mutation check without running it: every pattern must match once, and tally its lists.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 session 6: the fix-up of the ruling-10 pilot port)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#530;
         the shipped script it reads, util/ad-hoc/2026-11-11_verify_gitleaks_pr_scan_tests_are_not_vacuous.py in juniper-data-client

WHY THIS EXISTS
The shipped mutation check edits the workflow in place and takes minutes, so it runs last and alone. Before that run,
this loads the script by path (it writes nothing and runs no test) and answers what a failed start would cost a run to
learn: does every mutation's every pattern occur exactly once in the unmutated file, is every name unique, and how many
mutations, mutation-test pairs and listed survivors does the list hold, per file. The run's own tally must equal these.

Usage:
  2026-11-12_flood4r2_r10-data-client_mutation_list_check.py <the shipped mutation script> [--json <out.json>]

Exit 0 = every pattern matches once and every name is unique; 1 otherwise.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path


def load(script: Path):
    spec = importlib.util.spec_from_file_location("shipped_mutation_check", script)
    module = importlib.util.module_from_spec(spec)
    # The script declares a dataclass, which looks its module up in sys.modules while the class body runs.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    script = Path(argv[1]).resolve()
    out = Path(argv[argv.index("--json") + 1]) if "--json" in argv else None
    # Loading the script must leave no bytecode beside it: the tree it sits in is an uncommitted carrier.
    sys.dont_write_bytecode = True
    module = load(script)
    problems: list[str] = []
    by_path: Counter[str] = Counter()
    for mutation in module.MUTATIONS:
        by_path[mutation.path] += 1
        target = module.REPO / mutation.path
        original = target.read_text(encoding="utf-8") if target.is_file() else ""
        try:
            module.mutated_text(original, mutation)
        except SystemExit as exc:
            problems.append(str(exc))
    names = Counter(mutation.name for mutation in module.MUTATIONS)
    problems += [f"the name {name!r} is used {count} times" for name, count in names.items() if count > 1]
    listed = sorted({node for mutation in module.MUTATIONS for node in mutation.must_fail + mutation.must_still_pass})
    record = {
        "script": str(script),
        "repo": str(module.REPO),
        "mutations": len(module.MUTATIONS),
        "by_path": dict(by_path),
        "mutation_test_pairs": sum(len(mutation.must_fail) for mutation in module.MUTATIONS),
        "survivors_listed": sum(len(mutation.must_still_pass) for mutation in module.MUTATIONS),
        "distinct_cases_listed": len(listed),
        "distinct_cases_a_mutation_must_fail": len({node for mutation in module.MUTATIONS for node in mutation.must_fail}),
        "names": [mutation.name for mutation in module.MUTATIONS],
        "problems": problems,
    }
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in record.items() if key != "names"}, indent=1))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
