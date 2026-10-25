#!/usr/bin/env python3
"""Run util/ad-hoc/2026-10-10_gitleaks_probe.py against ANOTHER repository's checkout, unchanged.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-25
Status: ad-hoc -- investigation (gitleaks zero-rule configuration, fleet follow-up to juniper-ml#2203)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2203; util/ad-hoc/2026-10-10_gitleaks_probe.py (the instrument this drives);
         util/ad-hoc/2026-10-25_gitleaks_fleet_survey.py (the nine-repo survey)

WHY THIS EXISTS

The probe's `scan` mode resolves its scope against `REPO`, a module global fixed to the juniper-ml checkout the file
lives in (`Path(__file__).resolve().parents[2]`). Copying the probe into each sibling repository would fork the
instrument. This wrapper loads the probe module from this directory, points `REPO` at the checkout named by --repo,
and hands the remaining arguments to the probe's own `main()`, so every scope rule -- `ci-dispatch` is every branch
head and tag on that checkout's `origin`, each SHA required to be present locally -- is the probe's, not a copy's.

A history scan reads `.gitleaks.toml` and `.gitleaksignore` from --repo's WORKING TREE (gitleaks auto-discovers
both at --source), so point --repo at the worktree holding the configuration under test.

Usage:
    python3 util/ad-hoc/2026-10-25_gitleaks_probe_for_repo.py --repo CHECKOUT scan --gitleaks BIN --scope ci-dispatch --report R.json
    python3 util/ad-hoc/2026-10-25_gitleaks_probe_for_repo.py --repo CHECKOUT vacuity --gitleaks BIN

Exit codes: the probe's own (see its docstring); 3 when --repo is missing or is not a git checkout.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

PROBE = Path(__file__).resolve().parent / "2026-10-10_gitleaks_probe.py"


def main() -> int:
    argv = sys.argv[1:]
    if len(argv) < 3 or argv[0] != "--repo":
        print(__doc__, file=sys.stderr)
        return 3
    repo = Path(argv[1]).resolve()
    if not (repo / ".git").exists():
        print(f"not a git checkout: {repo}", file=sys.stderr)
        return 3
    spec = importlib.util.spec_from_file_location("gitleaks_probe", PROBE)
    if spec is None or spec.loader is None:
        print(f"cannot load {PROBE}", file=sys.stderr)
        return 3
    probe = importlib.util.module_from_spec(spec)
    sys.modules["gitleaks_probe"] = probe
    spec.loader.exec_module(probe)
    probe.REPO = repo
    print(f"probe: {PROBE.name}; REPO -> {repo}")
    sys.argv = [str(PROBE), *argv[2:]]
    return probe.main()


if __name__ == "__main__":
    sys.exit(main())
