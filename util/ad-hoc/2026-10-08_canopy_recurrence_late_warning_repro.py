"""
Reproduce the juniper-canopy ``main`` flake in ``TestA422DetailReachesTheOperator`` deterministically.

``RecurrenceBackend._run_fit`` flips ``_state`` to ``failed`` under the lock and logs its WARNING
AFTER releasing it. ``TestFailureHandling``'s tests end as soon as ``is_training_active()`` is
False, so on a slow runner the fit thread's WARNING is emitted after that test has finished and
lands in the NEXT test's ``caplog``. ``test_completion_reason_and_the_warning_carry_the_detail``
then sees a 503 WARNING it did not cause: ``(warning,) = ...`` raises "too many values to unpack",
or reads the wrong record. Observed on canopy ``main`` macOS legs at #702, #708 and #711, and on
PRs #715, #718 and #720 (2026-10-04..06).

This script delays ONLY the emission of that WARNING (the window a slow runner opens) and runs the
two tests in their file order. Delay 0 passes; a 0.3 s delay fails the same way CI does.
``--whole-module`` runs every test in the module under the same delay instead of the pair.

Usage (from a juniper-canopy checkout, in the JuniperCanopy1 environment):
    conda run -n JuniperCanopy1 python <this file> --repo <canopy checkout> --delay 0.3 [--whole-module]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-08
Status: ad-hoc — investigation (Cursor flood #3 evaluation, canopy test slice)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy #702 (introduced the test), #715 / #718 / #720 (inherited the red)
"""

from __future__ import annotations

import argparse
import os
import sys
import time

MODULE = "src/tests/unit/backend/test_recurrence_backend.py"
TESTS = (
    f"{MODULE}::TestFailureHandling::test_the_services_answer_still_reaches_completion_reason",
    f"{MODULE}::TestA422DetailReachesTheOperator::test_completion_reason_and_the_warning_carry_the_detail",
)


class _DelayLateWarning:
    """Pytest plugin: hold the fit thread's WARNING for ``delay`` seconds, as a loaded runner does."""

    def __init__(self, delay: float) -> None:
        self.delay = delay

    def pytest_sessionstart(self, session):  # noqa: ARG002 - pytest hook signature
        import backend.recurrence_backend as rb

        original = rb.logger.warning
        delay = self.delay

        def late_warning(*args, **kwargs):
            time.sleep(delay)
            return original(*args, **kwargs)

        rb.logger.warning = late_warning


def main() -> int:
    parser = argparse.ArgumentParser(description="Reproduce the late-WARNING caplog race in canopy's recurrence backend tests.")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--delay", type=float, default=0.3)
    parser.add_argument("--whole-module", action="store_true", help="run every test in the module, not just the pair")
    args = parser.parse_args()
    os.chdir(args.repo)
    import pytest

    targets = [MODULE] if args.whole_module else list(TESTS)
    return int(pytest.main(["-p", "no:cacheprovider", *targets], plugins=[_DelayLateWarning(args.delay)]))


if __name__ == "__main__":
    sys.exit(main())
