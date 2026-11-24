"""
Run juniper-cascor#753's own mutation check with the carrier's new test module added to its detector.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator session, flood-4 round 2, ruling 17 cascor stop-then-start, code lens)
Created: 2026-11-12
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (ruling 17, "cascor: stop-then-start"; ruling 11 for #753)

Usage: <JuniperCascor1 python> <this> <carrier copy tree> <base ref for M00>

Loads <tree>/util/ad-hoc/2026-11-08_paused_fit_wedge_mutation_check.py by path (unmodified), appends
src/tests/unit/api/test_lifecycle_stop_then_start.py to its TESTS tuple, and calls its ``main``. The
shipped script, run as it is, uses #753's two test files alone; the difference between the two runs is
the set of #753 mutants that only the carrier's new module still catches. The shipped script is
hermetic (it mutates a copy under the session's temp root), so the tree is not edited.
"""

import importlib.util
import sys
from pathlib import Path

NEW_MODULE = "src/tests/unit/api/test_lifecycle_stop_then_start.py"


def main() -> int:
    tree = Path(sys.argv[1]).resolve()
    base = sys.argv[2]
    script = tree / "util" / "ad-hoc" / "2026-11-08_paused_fit_wedge_mutation_check.py"
    spec = importlib.util.spec_from_file_location("r17val_paused_fit_wedge_mutation_check", script)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.TESTS = (*module.TESTS, NEW_MODULE)
    print(f"detector: {module.TESTS}", flush=True)
    sys.argv = [str(script), "--base", base]
    return module.main()


if __name__ == "__main__":
    sys.exit(main())
