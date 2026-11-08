#!/usr/bin/env python3
"""Exact bounds of two host gates that the G1 suite never lands on.

Project:     Juniper
Sub-Project: juniper-ml
Application: host tooling regression tests
Author:      Paul Calnon
License:     MIT License

``util/host_state_check.py`` (turing bring-up G1) decides two gates by a comparison the existing
suite only exercises away from the bound:

- G-TOOLS kubectl passes when ``abs(client minor - cluster minor) <= max_minor_skew``. The green
  host is an exact match (gap 0) and the failures are 2 and 14 minors off, so replacing ``<=``
  with ``<`` still passes that suite. A client exactly one allowed minor off must pass, in both
  directions, and Kubernetes' trailing ``+`` on the minor (``37+``) still counts.
- G-NET throughput fails only when the recorded Mb/s is strictly below ``min_mbps``. The suite
  fails 412.5 against a floor of 800 and passes 941, so a measurement equal to the floor is
  untested.

Production behavior is unchanged. Run: python3 -m unittest -v tests/test_host_state_gate_boundaries.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT_PATH = REPO_ROOT / "util" / "host_state_check.py"


def _load():
    spec = importlib.util.spec_from_file_location("host_state_check_boundaries", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # dataclasses resolve their module through sys.modules
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


HSC = _load()

CLUSTER = "1.36"


def _client(major: str, minor: str) -> str:
    """kubectl's ``version --client -o json``, including a minor that still carries its ``+``."""
    return json.dumps({"clientVersion": {"major": major, "minor": minor, "gitVersion": f"v{major}.{minor.rstrip('+')}.0"}})


def _kubectl(major: str, minor: str, *, cluster: str = CLUSTER, skew: int = 1):
    probe = {"tools": {"kubectl_version": {"argv": ["kubectl", "version", "--client", "-o", "json"], "found": True, "rc": 0, "timed_out": False, "stdout": _client(major, minor), "stderr": ""}}}
    expected = {"gates": {"G-TOOLS": {"kubectl": {"cluster": cluster, "max_minor_skew": skew}}}}
    ctx = HSC.Context(host="testhost", expected=expected, record_base=Path("."), probe=probe)
    return HSC._kubectl(ctx)


class KubectlSkewBoundaryTest(unittest.TestCase):
    """``abs(gap) <= max_minor_skew`` admits the exact allowance and refuses one minor past it."""

    def test_exactly_the_allowed_skew_passes_either_way(self) -> None:
        for minor in ("37", "35"):
            with self.subTest(minor=minor):
                cond = _kubectl("1", minor)
                self.assertEqual(cond.status, "pass", cond.message)
                self.assertIn("within 1 minor of the cluster's 1.36", cond.message)
                self.assertIsNone(cond.remediation)

    def test_one_minor_past_the_allowance_fails_either_way(self) -> None:
        ahead = _kubectl("1", "38")
        self.assertEqual(ahead.status, "fail")
        self.assertIn("2 minors ahead of the cluster's 1.36 (allowed: 1)", ahead.message)
        self.assertTrue(ahead.remediation.startswith("task D3 (owner) first:"), ahead.remediation)
        behind = _kubectl("1", "34")
        self.assertEqual(behind.status, "fail")
        self.assertIn("2 minors behind the cluster's 1.36 (allowed: 1)", behind.message)

    def test_a_zero_skew_admits_only_the_cluster_minor(self) -> None:
        exact = _kubectl("1", "36", skew=0)
        self.assertEqual(exact.status, "pass", exact.message)
        self.assertIn("within 0 minor of the cluster's 1.36", exact.message)
        off = _kubectl("1", "37", skew=0)
        self.assertEqual(off.status, "fail")
        self.assertIn("1 minors ahead of the cluster's 1.36 (allowed: 0)", off.message)

    def test_a_plus_suffix_on_the_exact_edge_still_counts(self) -> None:
        """kubectl prints the minor as ``37+``. Only the digits count, so that client is one minor ahead and allowed."""
        cond = _kubectl("1", "37+")
        self.assertEqual(cond.status, "pass", cond.message)
        self.assertIn("v1.37.0", cond.message)
        past = _kubectl("1", "38+")
        self.assertEqual(past.status, "fail")
        self.assertIn("2 minors ahead of the cluster's 1.36 (allowed: 1)", past.message)

    def test_a_different_major_fails_when_the_minor_matches(self) -> None:
        cond = _kubectl("2", "36")
        self.assertEqual(cond.status, "fail")
        self.assertIn("kubectl v2.36.0 is not major version 1", cond.message)


class ThroughputFloorTest(unittest.TestCase):
    """A recorded rate equal to ``min_mbps`` passes; one below the floor fails."""

    def _judge(self, base: Path, mbps: float):
        cfg = {"min_mbps": 800, "throughput": {"date": "2026-10-27", "mbps": mbps, "record": "reports/iperf3.txt"}}
        ctx = HSC.Context(host="testhost", expected={}, record_base=base, probe={})
        return HSC._throughput(ctx, cfg)

    def test_a_measurement_equal_to_the_floor_passes_and_one_below_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "reports").mkdir()
            (base / "reports" / "iperf3.txt").write_text("iperf\n", encoding="utf-8")
            equal = self._judge(base, 800)
            self.assertEqual(equal.status, "pass", equal.message)
            self.assertIn("800 Mb/s on 2026-10-27", equal.message)
            above = self._judge(base, 800.1)
            self.assertEqual(above.status, "pass", above.message)
            below = self._judge(base, 799.9)
            self.assertEqual(below.status, "fail")
            self.assertIn("799.9 Mb/s on 2026-10-27 is below 800 Mb/s", below.message)


if __name__ == "__main__":
    unittest.main()
