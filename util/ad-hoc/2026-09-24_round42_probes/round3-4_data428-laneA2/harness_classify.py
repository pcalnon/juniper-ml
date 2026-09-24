"""Run the SHIPPED harness unchanged, but record WHY each test failed, and add three negative controls.

The harness scores CAUGHT on any non-zero pytest exit -- an assertion, an error, a timeout alike.
This wrapper loads the shipped module from inside a private tree copy (so its REPO is that copy),
replaces only ``run_tests`` with one that also keeps the failure's reason, and appends:

  X1 a VACUOUS arm   -- edits a comment only; the harness must say VACUOUS and FAIL.
  X2 an OVERBROAD arm -- breaks http_cache's import; must_fail goes red for the wrong reason and the
                        control must go OVERBRD, so the harness must FAIL.
  X3 a missing node  -- a test id that does not exist; the baseline must show it RED.

usage: harness_classify.py <tree-copy>
"""

import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

tree = Path(sys.argv[1]).resolve()
path = tree / "util/ad-hoc/2026-09-22_verify_conditional_request_tests_are_not_vacuous.py"
spec = importlib.util.spec_from_file_location("harness_shipped", path)
h = importlib.util.module_from_spec(spec)
sys.modules["harness_shipped"] = h
spec.loader.exec_module(h)
assert h.REPO == tree, (h.REPO, tree)

REASONS: dict[str, list[tuple[str, bool, str]]] = {}
current = {"arm": "baseline"}


def classify(out: str, rc: int) -> str:
    if rc == 0:
        return "pass"
    if rc in (4, 5) or "ERROR: not found" in out or "no tests ran" in out:
        return "NODE-NOT-FOUND"
    if "Failed: Timeout" in out:
        return "TIMEOUT(pytest-timeout)"
    if re.search(r"^E\s+(AssertionError|assert )", out, re.M):
        return "assertion"
    last = out.strip().splitlines()[-1] if out.strip() else ""
    m = re.search(r"^E\s+(\w+(?:Error|Exception|Exit))", out, re.M)
    if "error" in last:
        return "ERROR:" + (m.group(1) if m else "?")
    first_e = next((ln for ln in out.splitlines() if ln.startswith("E ")), "")
    return f"EXCEPTION:{m.group(1)}" if m else f"other:{first_e[:60]}"


def run_tests(node_ids):
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    results = {}
    for node_id in node_ids:
        proc = subprocess.run([h.PYTHON, "-m", "pytest", node_id, "-q", "--no-header", "-p", "no:cacheprovider"], cwd=h.WORK, capture_output=True, text=True, env=env)
        out = proc.stdout + proc.stderr
        results[node_id] = proc.returncode == 0
        REASONS.setdefault(current["arm"], []).append((node_id.split("::")[-1], proc.returncode == 0, classify(out, proc.returncode)))
    return results


h.run_tests = run_tests

# Track which arm is running: wrap apply(), which the harness calls once per mutation.
real_apply = h.apply
names = iter([m.name for m in h.MUTATIONS] + ["X1", "X2", "X3"])


def apply(edits):
    current["arm"] = next(names).split(":")[0]
    return real_apply(edits)


h.apply = apply

CACHE = h.CACHE
h.MUTATIONS.append(h.Mutation(
    name="X1: a comment-only edit (must be VACUOUS)",
    why="negative control for the harness itself",
    edits=[(CACHE, "#: ``Cache-Control`` for the three validated reads. See the module docstring.", "#: (edited comment, no behaviour)")],
    must_fail=[h.node(h.META, "test_etag_is_strong_and_is_the_hash_of_the_exact_body")],
    must_still_pass=[h.node(h.META, "test_body_carries_no_access_counter")],
))
h.MUTATIONS.append(h.Mutation(
    name="X2: http_cache cannot import (must be OVERBRD)",
    why="negative control for the harness itself",
    edits=[(CACHE, 'CACHE_CONTROL_REVALIDATE = "private, no-cache"', "CACHE_CONTROL_REVALIDATE = undefined_name_lane_a2")],
    must_fail=[h.node(h.META, "test_etag_is_strong_and_is_the_hash_of_the_exact_body")],
    must_still_pass=[h.node(h.META, "test_body_carries_no_access_counter")],
))
h.MUTATIONS.append(h.Mutation(
    name="X3: a node id that does not exist (baseline must be RED)",
    why="negative control for the harness itself",
    edits=[(CACHE, 'CACHE_CONTROL_NO_STORE = "no-store"', 'CACHE_CONTROL_NO_STORE = "no-store"')],
    must_fail=[h.node(h.META, "test_this_test_does_not_exist_lane_a2")],
    must_still_pass=[],
))

rc = h.main()
print("\nHARNESS EXIT (expected 1 because of X1-X3):", rc)
Path(tree.parent / "harness_classify_reasons.json").write_text(json.dumps(REASONS, indent=1))
print("\nPer-arm failure reasons for must_fail tests (non-pass):")
for arm, rows in REASONS.items():
    kinds = sorted({k for _, ok, k in rows if not ok})
    print(f"  {arm:9s} {kinds}")
