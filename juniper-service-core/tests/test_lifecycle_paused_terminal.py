"""Pin terminal transitions around PAUSE and the non-active snapshot states.

``mark_completed`` is legal only from STARTED. A completion signal that arrives while
the run is paused must not declare the fit finished: the training thread is still
inside ``fit``, and ``paused_phase`` is what RESUME restores. ``mark_failed`` is the
opposite arm — PAUSED is an active state, so a failure (exception or user stop) from
pause must settle FAILED and clear the remembered phase. Collapsing the two checks
into ``is_active()`` would either complete a paused run or refuse to fail one.

PAUSE, failure, and completion are also refused from REPLAYING, INVESTIGATING, and
RESUME_READY. Those states are not a live fit; entering PAUSED from one of them would
make ``is_active()`` true and let a later RESUME start training against a snapshot
session. A second PAUSE must not replace the phase remembered by the first one.

Hermetic: the state machine imports no third-party code.
"""

from __future__ import annotations

import pytest

from juniper_service_core.lifecycle.state_machine import (
    LifecycleCommand,
    LifecycleStateMachine,
    LifecycleStatus,
)


def _paused(phase: str = "candidate") -> LifecycleStateMachine:
    sm = LifecycleStateMachine()
    assert sm.handle_command(LifecycleCommand.START) is True
    sm.set_phase(phase)
    assert sm.handle_command(LifecycleCommand.PAUSE) is True
    assert sm.paused_phase == phase
    return sm


def test_mark_completed_while_paused_keeps_the_remembered_phase() -> None:
    sm = _paused("candidate")
    assert sm.mark_completed() is False
    assert sm.status is LifecycleStatus.PAUSED
    assert sm.is_paused() is True
    assert sm.paused_phase == "candidate"
    assert sm.phase == "candidate"
    # The remembered phase is still what a later resume restores.
    assert sm.handle_command(LifecycleCommand.RESUME) is True
    assert sm.is_started() is True
    assert sm.phase == "candidate"


def test_mark_failed_while_paused_settles_failed_and_clears_the_phase() -> None:
    sm = _paused("warmup")
    assert sm.mark_failed("fit raised") is True
    assert sm.status is LifecycleStatus.FAILED
    assert sm.is_failed() is True
    assert sm.is_paused() is False
    assert sm.phase == "idle"
    assert sm.paused_phase is None
    # A failed run is not still active, so a second failure is refused.
    assert sm.mark_failed("again") is False
    assert sm.status is LifecycleStatus.FAILED


def test_second_pause_does_not_replace_the_remembered_phase() -> None:
    sm = _paused("candidate")
    assert sm.handle_command(LifecycleCommand.PAUSE) is False
    assert sm.status is LifecycleStatus.PAUSED
    assert sm.paused_phase == "candidate"
    assert sm.phase == "candidate"


@pytest.mark.parametrize("enter", ["mark_replaying", "mark_investigating", "mark_resume_ready"])
def test_pause_failure_and_completion_rejected_outside_an_active_fit(enter: str) -> None:
    sm = LifecycleStateMachine()
    assert getattr(sm, enter)() is True
    status = sm.status

    assert sm.handle_command(LifecycleCommand.PAUSE) is False
    assert sm.mark_failed("boom") is False
    assert sm.mark_completed() is False

    assert sm.status is status
    assert sm.paused_phase is None
    assert sm.phase == "idle"
    assert sm.is_paused() is False
