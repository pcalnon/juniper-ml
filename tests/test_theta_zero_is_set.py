#!/usr/bin/env python3
"""A theta of zero is a value, not an unset theta.

juniper-ml#2366 labels ``recurrence.theta`` with ``is not None``, the same test
juniper-recurrence uses (``req.theta if req.theta is not None else settings.default_theta``).
``tests/test_stats_summary_render.py`` and ``tests/test_run_experiment.py`` pin that
precedence with ``0.5`` and ``91.0``. Both are truthy, so ``if train.get("theta")``
or ``if service.get("default_theta")`` would still pass them and would call a
zero theta data-driven, or would let a service default of zero fall through to
data-driven. A fit whose theta is 0 would then be described as resolved from
elapsed time.

``summary.md`` prints the value with no ``or`` stand-in, so ``0`` and ``0.0``
stay visible. Do not fold this into ``tests/test_stats_summary_render.py``.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import stats_summary as ss  # noqa: E402  (path-invoked util import)


def _manifest() -> dict:
    return {
        "run_id": "r-unit",
        "experiment": {"name": "e", "description": None},
        "config_sha256": "x",
        "seeds": {"experiment": 1},
        "git": {},
        "packages": {},
        "timings": {"total": 1.0},
        "outcome": "succeeded",
        "acceptance": {"ok": True, "reasons": []},
        "metrics_scraped": {},
        "dataset": {
            "dataset_id": "d",
            "generator": "spiral",
            "version": "1",
            "split": "train",
            "params": {},
            "meta": {},
        },
    }


class ThetaZeroIsSetTest(unittest.TestCase):
    def test_an_explicit_zero_outranks_the_service_default(self) -> None:
        for theta in (0, 0.0):
            with self.subTest(theta=theta):
                block = ss.theta_block({"theta": theta}, {"default_theta": 91.0})
                self.assertEqual(block["note"], ss.THETA_NOTE_EXPLICIT)
                self.assertIs(type(block["value"]), type(theta))
                self.assertEqual(block["value"], theta)

    def test_a_service_default_of_zero_is_not_data_driven(self) -> None:
        for default in (0, 0.0):
            for train in ({}, {"theta": None}):
                with self.subTest(default=default, train=train):
                    block = ss.theta_block(train, {"default_theta": default})
                    self.assertEqual(block["note"], ss.THETA_NOTE_SERVICE_DEFAULT)
                    self.assertIs(type(block["value"]), type(default))
                    self.assertEqual(block["value"], default)
                    self.assertNotEqual(block["note"], ss.THETA_NOTE_DATA_DRIVEN)

    def test_summary_md_prints_a_zero_theta(self) -> None:
        explicit = ss.build_stats(
            _manifest(),
            kind="recurrence",
            train_summary={},
            train_config={"theta": 0},
            service_config={"default_theta": 91.0},
        )
        rendered = ss.render_summary_md(explicit)
        self.assertIn("- theta: 0 (explicit)", rendered)
        self.assertNotIn("data-driven", rendered)

        service = ss.build_stats(
            _manifest(),
            kind="recurrence",
            train_summary={},
            train_config={"theta": None},
            service_config={"default_theta": 0.0},
        )
        rendered = ss.render_summary_md(service)
        self.assertIn(
            "- theta: 0.0 (service default from service.default_theta; train.theta is unset)",
            rendered,
        )
        self.assertNotIn("data-driven", rendered)


if __name__ == "__main__":
    unittest.main()
