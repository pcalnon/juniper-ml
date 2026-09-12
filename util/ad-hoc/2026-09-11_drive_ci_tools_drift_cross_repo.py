#!/usr/bin/env python3
"""
Drive tests/test_ci_tools_drift.py's cross-repo assertion against the real ecosystem.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-11
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#1909, juniper-cascor#646

Drive ``tests/test_ci_tools_drift.py``'s cross-repo assertion against the REAL
ecosystem, from a worktree.

Why this exists: ``_find_ecosystem_root`` walks at most two directories up from
the test file. From ``juniper-ml/.claude/worktrees/<name>/tests/`` that reaches
``.claude/worktrees/`` and stops, so the cross-repo test auto-skips and the
widened scope goes unexercised in exactly the mode it was widened for. This
harness pins ``ecosystem_root`` to the real root and runs the assertion for real.

Usage:  python3 util/ad-hoc/2026-09-11_drive_ci_tools_drift_cross_repo.py [ecosystem_root]
Exit 0 = the fleet is clean; 1 = at least one stale pin (the failure names it).
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

os.environ["GITHUB_ACTIONS"] = "true"  # lift the local-skip gate
os.environ["JUNIPER_DRIFT_TEST_FORCE_LOCAL"] = "1"

from tests import test_ci_tools_drift as mod  # noqa: E402

ECOSYSTEM = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/pcalnon/Development/python/Juniper").resolve()


class CrossRepoLive(mod.JuniperCiToolsDriftTest):
    """Same assertions, with the sibling search short-circuited to the real root."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ecosystem_root = ECOSYSTEM


if __name__ == "__main__":
    print(f"ecosystem root: {ECOSYSTEM}")
    print(f"current juniper-ci-tools version: {mod._read_current_version(ROOT)}")
    total = 0
    for repo in mod._CONSUMER_REPOS:
        pins = mod._pins_in_repo(ECOSYSTEM / repo)
        total += len(pins)
        print(f"  {repo:<22} {len(pins)} pin(s)")
    print(f"  {'juniper-ml':<22} {len(mod._pins_in_repo(ROOT))} pin(s)  [this worktree]")
    print(f"total consumer pins scanned: {total}\n")

    suite = unittest.TestLoader().loadTestsFromName("test_consumer_repos_pin_current_version", CrossRepoLive)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(0 if result.wasSuccessful() else 1)
