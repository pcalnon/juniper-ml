#!/usr/bin/env python3
"""Probe the two honesty-contract gaps the validator's surviving mutants exposed, and the proposed test inputs.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation (independent validation of the Cursor flood-4 round-2 "ml-propose" carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the ml-propose carrier; util/ad-hoc/2026-11-08_flood4r2_val_ml-propose_mutants.py (CM4, RM5 survived)

Loads ``--propose`` (the carrier's propose.py) as a module twice per mutant, in memory only (the file is never
written): once as it is, once with the mutant's one substring replaced. For each proposed new assertion it prints
what the carrier returns and what the mutant returns, so a reader can see the assertion passes on the carrier and
fails on the mutant. The fixtures are read from ``--tests`` (the carrier's test file) by executing only its
module-level ``_COMPAT_*`` constants. Read-only.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import sys
import types
from pathlib import Path


def load_module(name: str, source: str, path: Path) -> types.ModuleType:
    spec = importlib.util.spec_from_loader(name, loader=None)
    mod = importlib.util.module_from_spec(spec)
    mod.__file__ = str(path)
    sys.modules[name] = mod
    exec(compile(source, str(path), "exec"), mod.__dict__)  # nosec B102 - the carrier's own module text, in memory
    return mod


def fixtures(tests_path: Path) -> dict:
    tree = ast.parse(tests_path.read_text(encoding="utf-8"))
    keep = [n for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id.startswith("_COMPAT_") for t in n.targets)]
    ns: dict = {}
    exec(compile(ast.Module(body=[ast.parse("import textwrap").body[0], *keep], type_ignores=[]), str(tests_path), "exec"), ns)  # nosec B102 - constants only
    return ns


def main(argv: "list[str] | None" = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--propose", required=True)
    ap.add_argument("--tests", required=True)
    args = ap.parse_args(argv)
    path = Path(args.propose)
    sys.path.insert(0, str(path.parent))
    source = path.read_text(encoding="utf-8")
    fx = fixtures(Path(args.tests))
    ref, row06, specs = fx["_COMPAT_REFERENCE"], fx["_COMPAT_ROW_06"], fx["_COMPAT_SPECS"]
    mutants = {
        "CM4": ("    if not pins or any(re.fullmatch(_REFERENCE_CLAUSE_PIN_BODY, pin) is None for pin in pins):", "    if not pins or all(re.fullmatch(_REFERENCE_CLAUSE_PIN_BODY, pin) is None for pin in pins):"),
        "RM5": ("        if len(raw) != len(header) + 2:", "        if len(raw) < len(header) + 2:"),
    }
    carrier = load_module("propose_carrier_probe", source, path)
    mixed = ["juniper-recurrence>=0.5.0,<0.6.0", "juniper-recurrence-model~=0.3"]
    wider = ref.replace(row06, row06.rstrip("\n") + " extra |\n")
    raised = dict(specs, **{"juniper-observability": ">=0.3.0"})
    for mid, (old, new) in mutants.items():
        if source.count(old) != 1:
            print(mid, "NOT APPLIED")
            continue
        mutant = load_module(f"propose_{mid}_probe", source.replace(old, new), path)
        if mid == "CM4":
            c = carrier.set_reference_recurrence_clause(ref, "0.7.0", mixed)
            m = mutant.set_reference_recurrence_clause(ref, "0.7.0", mixed)
            print("CM4 mixed pins: carrier untouched+None =", c == (ref, None), "| mutant untouched+None =", m == (ref, None))
        else:
            c = carrier.set_reference_matrix_row(wider, "0.6.1", raised)
            m = mutant.set_reference_matrix_row(wider, "0.6.1", raised)
            print("RM5 wider row: carrier =", (c[0] == wider, c[1]), "| mutant =", (m[0] == wider, m[1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
