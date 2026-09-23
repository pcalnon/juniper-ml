"""
Probe (a pytest module, copied into a THROWAWAY canopy worktree by the driver) for two claims the
corrected ``_explore`` comment in ``test_selection_reachability_guardrails.py`` will make.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-09-23_mutation_check_m1_m6.py (the driver);
         juniper-canopy#667 (⊥-at-mount), which made the helper's default start stale

Claims:
1. With the clears the layout ships, the reachable set does not depend on the start: every mount
   state canopy can land on (⊥, the ``unknown`` fallback's seeded pair, a hydrated pair) reaches the
   same set. So G1a / G1b are start-independent.
2. With BOTH clears withheld, a ``⊥`` start still reaches both components (at ``⊥`` every model's
   Select is enabled), so only a start that already holds a dataset exhibits the deadlock — which
   is why G2's "deadlock returns" case needs a seeded start.
"""

import pytest

from frontend.dashboard_manager import DashboardManager
from model_registry import DEFAULT_DATASET_TYPE, DEFAULT_MODEL_KEY
try:  # pytest prepends this file's directory (no __init__.py there), so the sibling imports bare
    from test_selection_reachability_guardrails import _explore
except ImportError:
    from tests.regression.test_selection_reachability_guardrails import _explore

TARGET = ("recurrence", "equities_seq")


@pytest.fixture(scope="module")
def manager():
    import frontend.dashboard_manager as dm_module

    print(f"\nPROBE imports dashboard_manager from {dm_module.__file__}")
    return DashboardManager({})


def test_claim1_reach_is_start_independent_with_the_shipped_clears(manager):
    default = _explore(manager)
    starts = {
        "bottom (none source)": (DEFAULT_MODEL_KEY, None),
        "unknown fallback": (DEFAULT_MODEL_KEY, DEFAULT_DATASET_TYPE),
        "hydrated recurrence pair": TARGET,
        "hydrated recurrence at bottom": ("recurrence", None),
    }
    for name, start in starts.items():
        reach = _explore(manager, start=start)
        print(f"PROBE claim1 start={name} {start}: |reach|={len(reach)} equal_to_default={reach == default}")
        assert reach == default, f"start {name} reaches a different set"


def test_claim2_bottom_start_escapes_without_any_clear(manager):
    seeded = _explore(manager, clearable=False, model_clearable=False)
    bottom = _explore(manager, clearable=False, model_clearable=False, start=(DEFAULT_MODEL_KEY, None))
    print(f"PROBE claim2 seeded start: target reachable={TARGET in seeded} |reach|={len(seeded)}")
    print(f"PROBE claim2 bottom start: target reachable={TARGET in bottom} |reach|={len(bottom)}")
    assert TARGET not in seeded
    assert TARGET in bottom
