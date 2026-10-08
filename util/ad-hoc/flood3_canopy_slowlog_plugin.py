# Project:       Juniper
# Sub-Project:   juniper-ml
# Application:   ad-hoc (Cursor fleet flood #3 evaluation, canopy docs slice)
# Author:        Paul Calnon
# Version:       0.1.0
# License:       MIT License
#
# Single-use pytest plugin (load with `-p flood3_canopy_slowlog_plugin`, this directory on
# PYTHONPATH). It reproduces, deterministically, the macOS-only failure seen on canopy#717 and
# canopy#725: RecurrenceBackend._run_fit flips its state to "failed" under the lock and logs the
# WARNING *after* releasing it, so a test that waits only for `not is_training_active()` returns
# while its daemon thread still owes a WARNING. That record then lands in the NEXT test's caplog.
# A slow runner widens the gap; this plugin widens it on purpose by delaying the backend logger's
# WARNING emission. It changes no repository file.
"""Delay juniper_canopy.backend.recurrence_backend WARNINGs to expose the cross-test caplog leak."""

import logging
import time

# The 503 record belongs to TestFailureHandling::test_the_services_answer_still_reaches_completion_reason,
# which returns as soon as the state flips. Delaying it 0.15 s and every other backend WARNING 0.3 s
# makes the earlier test's record reach the later test's caplog first -- the ordering a starved
# macOS runner produced by accident.
_DELAY_503_S = 0.15
_DELAY_OTHER_S = 0.3
_orig_warning = logging.Logger.warning


def _slow_warning(self, msg, *args, **kwargs):
    if self.name == "juniper_canopy.backend.recurrence_backend":
        text = msg % args if args else str(msg)
        time.sleep(_DELAY_503_S if "status=503" in text else _DELAY_OTHER_S)
    return _orig_warning(self, msg, *args, **kwargs)


def pytest_configure(config):
    logging.Logger.warning = _slow_warning


def pytest_unconfigure(config):
    logging.Logger.warning = _orig_warning
