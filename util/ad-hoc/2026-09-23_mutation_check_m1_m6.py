"""
Reproduce two of the ship map's agent-run mutants (M1, M6) and run the ``_explore`` start probe, in a
THROWAWAY canopy worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: reports/2026-09-23_canopy-selection-design-ship-map/SHIP_MAP.md (M1, M6 — "not independently
         reproduced"); util/ad-hoc/2026-09-23_explore_start_probe_test.py

Modes:
  probe   copy the start probe into src/tests/regression/, run it (-s), delete it.
  m1      revert the dataset dropdown's ``clearable=True`` (the §4.1 keyword) and run the guardrails
          module. The ship map says only ``test_g2_either_clear_alone_opens_the_graph[withheld1]``
          catches it, which makes the G1a helper's docstring ("revert the one-keyword change ...
          which is exactly the deadlock") stale.
  m6      regate the restart modal's dataset list against the DEFAULT model instead of the selected
          one (§4.5 / X2) and run ``--tests`` (default: the CI unit lane). The ship map says nothing
          catches it.

Each anchor must match exactly once (else the script refuses); the file is restored byte-for-byte in
a ``finally`` and verified.

Usage:
    python util/ad-hoc/2026-09-23_mutation_check_m1_m6.py <canopy-worktree> {probe,m1,m6} [--tests PATH ...]
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

PYTHON = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
DM = "src/frontend/dashboard_manager.py"
GUARDRAILS = "src/tests/regression/test_selection_reachability_guardrails.py"
CI_LANE = ["src/tests/unit/", "src/tests/regression/", "src/tests/contract/", "src/tests/performance/"]
PROBE_SRC = Path(__file__).with_name("2026-09-23_explore_start_probe_test.py")
PROBE_DST = "src/tests/regression/test_zz_explore_start_probe.py"

M1 = (
    "so ``I-cover`` is gained without weakening ``I-safe``.\n" + " " * 92 + "clearable=True,",
    "so ``I-cover`` is gained without weakening ``I-safe``.\n" + " " * 92 + "clearable=False,",
)
M6 = (
    "ds_options = apply_availability_gate(gated_dataset_options(model_key or DEFAULT_MODEL_KEY), self._fetch_generators())",
    "ds_options = apply_availability_gate(gated_dataset_options(DEFAULT_MODEL_KEY), self._fetch_generators())",
)


def pytest(repo, tests, extra=()):
    env = dict(os.environ, LIBTORCH="", LD_LIBRARY_PATH="")
    cmd = [PYTHON, "-m", "pytest", "-m", "not requires_cascor and not requires_server and not slow", *tests, "--timeout=60", "-q", "--no-header", "-p", "no:cacheprovider", "-rfE", *extra]
    proc = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, check=False)
    failed = [line for line in proc.stdout.splitlines() if line.startswith(("FAILED", "ERROR"))]
    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else proc.stderr.strip()[-300:]
    return proc.returncode, failed, tail, proc.stdout


def mutate_and_run(repo, anchor, replacement, tests):
    target = repo / DM
    original = target.read_bytes()
    text = original.decode()
    if text.count(anchor) != 1:
        print(f"anchor found {text.count(anchor)} times, expected 1 -- REFUSING")
        return 2
    try:
        target.write_text(text.replace(anchor, replacement))
        code, failed, tail, _ = pytest(repo, tests)
    finally:
        target.write_bytes(original)
    assert target.read_bytes() == original, "restore failed"
    print(f"mutant run: exit={code} :: {tail}")
    print(f"failed ({len(failed)}):")
    for line in failed:
        print(f"  {line}")
    print("restored byte-for-byte")
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("mode", choices=["probe", "m1", "m6"])
    ap.add_argument("--tests", nargs="*", default=None)
    a = ap.parse_args()
    repo = Path(a.repo).resolve()
    if a.mode == "probe":
        dst = repo / PROBE_DST
        shutil.copyfile(PROBE_SRC, dst)
        try:
            code, failed, tail, out = pytest(repo, [PROBE_DST], extra=("-s",))
        finally:
            dst.unlink()
        print("\n".join(line for line in out.splitlines() if line.startswith("PROBE") or "passed" in line or "failed" in line))
        print(f"probe: exit={code} :: {tail}; failed={failed}")
        return code
    if a.mode == "m1":
        code, failed, tail, _ = pytest(repo, [GUARDRAILS])
        print(f"baseline: exit={code} :: {tail}")
        if code != 0:
            return 2
        return mutate_and_run(repo, *M1, [GUARDRAILS])
    tests = a.tests or CI_LANE
    code, failed, tail, _ = pytest(repo, [GUARDRAILS])
    print(f"baseline (guardrails only): exit={code} :: {tail}")
    if code != 0:
        return 2
    return mutate_and_run(repo, *M6, tests)


if __name__ == "__main__":
    sys.exit(main())
