#!/usr/bin/env python3
"""
Check a run_tests thin spec carries the old copy's module constants unchanged: the --help text, the OPT_IN table.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-11-28
Status: ad-hoc -- the run_tests rollout, step 4 of § 4.3 of
        notes/JUNIPER_2026-11-26_JUNIPER-ECOSYSTEM_RUN-TESTS-ENGINE-EXTRACTION-PROPOSAL.md
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-26_run_tests_engine_equivalence.py (whose --help case shows the option text the engine
         changes; this shows the description, epilog and tables it does not)

Why this exists
---------------
A conversion copies the old copy's ``_DESCRIPTION``, ``_EPILOG`` (and data-client's ``OPT_IN``) into the thin
spec, and each repo's docs test pins that text against its documentation. A transcription slip would change the
--help output and could still pass a docs test that only looks for option names. So both modules are loaded and
each named constant compared for equality. The old copy is loaded from a file outside the checkout (an export of
``main``), since the conversion replaced it.

Usage:
    python3 util/ad-hoc/2026-11-28_run_tests_conversion_help_text_check.py OLD_COPY.py NEW_SPEC.py NAME [NAME ...]

Run it with an interpreter that has juniper-ci-tools 0.10 (the spec imports the engine) and PyYAML (the old copy
does). Exit 0 when every constant is equal.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, Path(path).resolve())
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # @dataclass resolves annotations through sys.modules
    spec.loader.exec_module(module)
    return module


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        raise SystemExit(__doc__.split("Usage:")[1].strip())
    old = load(argv[0], "old_runner_copy")
    new = load(argv[1], "new_thin_spec")
    bad = 0
    for attr in argv[2:]:
        same = getattr(old, attr) == getattr(new, attr)
        bad += not same
        print(f"{'EQUAL  ' if same else 'DIFFERS'} {attr}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
