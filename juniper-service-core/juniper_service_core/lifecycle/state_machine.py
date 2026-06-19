"""Model-agnostic training-lifecycle finite state machine (WS-2 / OUT-11 T2).

The de-cascored core of cascor's ``api/lifecycle/state_machine.py``. cascor's machine
carried cascade-specific *phases* (``OUTPUT`` / ``CANDIDATE``) baked into a closed enum, plus
snapshot-replay states (``RESUME_READY`` / ``INVESTIGATING`` / ``REPLAYING``) that belong to
its persistence feature. This generic base keeps only the **status** lifecycle every model
service shares -- ``STOPPED → STARTED → {PAUSED, COMPLETED, FAILED}`` -- and makes the
*phase* an open ``str`` (default ``"idle"``), matching the open-string ``phase`` carried by
:class:`juniper_model_core.events.TrainingEvent` of type ``phase_change`` (and the open
``model_type`` string in :mod:`juniper_model_core.topology`). A concrete service maps its own
phase vocabulary onto the string (cascor → ``"output"`` / ``"candidate"``; a fixed-order
regressor → ``"running"``); snapshot/replay states are a cascor-side extension, not the
shared contract.

Pure stdlib -- importing this module pulls no third-party dependency, so it is safe on the
dependency-free import path of :mod:`juniper_service_core`.
"""

from __future__ import annotations

import logging
from enum import Enum, auto

__all__ = [
    "LifecycleStatus",
    "LifecycleCommand",
    "LifecycleStateMachine",
    "PHASE_IDLE",
    "PHASE_RUNNING",
    "PHASE_INFERENCE",
]

logger = logging.getLogger("juniper_service_core.lifecycle.state_machine")

#: Conventional generic phase labels. ``phase`` is an open ``str`` -- a service may set any
#: label via :meth:`LifecycleStateMachine.set_phase` (typically from a ``phase_change``
#: :class:`~juniper_model_core.events.TrainingEvent`). These three cover the model-agnostic
#: cases; cascor layers ``"output"`` / ``"candidate"`` on top.
PHASE_IDLE = "idle"
PHASE_RUNNING = "running"
PHASE_INFERENCE = "inference"


class LifecycleStatus(Enum):
    """The model-agnostic training-lifecycle status.

    The closed set every Juniper model service shares. ``INVESTIGATING`` and ``RESUME_READY``
    are the snapshot-loaded states (added with the generic snapshot seam, OUT-11 T2 step 1b):
    a snapshot can be loaded for inspection (``INVESTIGATING`` -- training is rejected until a
    retrain/resume promotes it) or to continue training (``RESUME_READY`` -- the next ``START``
    resumes and the manager preserves the loaded history). ``REPLAYING`` plays a snapshot's
    stored history back as timed frames (OUT-11 T2 step 1c).
    """

    STOPPED = auto()
    STARTED = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    INVESTIGATING = auto()
    RESUME_READY = auto()
    REPLAYING = auto()


class LifecycleCommand(Enum):
    """A user/service control command driving a :class:`LifecycleStateMachine` transition."""

    START = auto()
    STOP = auto()
    PAUSE = auto()
    RESUME = auto()
    RESET = auto()


class LifecycleStateMachine:
    """Deterministic finite state machine for training control.

    Tracks a :class:`LifecycleStatus` plus an open-string ``phase``. The legal transitions
    mirror cascor's proven machine (the CLEAN extraction), minus the cascade phases and the
    snapshot-replay states:

    * ``STOPPED`` → ``STARTED`` on :attr:`LifecycleCommand.START`
    * terminal (``COMPLETED`` / ``FAILED``) auto-resets to ``STOPPED`` then starts on ``START``
    * ``STARTED`` → ``PAUSED`` on ``PAUSE`` (the active phase is remembered)
    * ``PAUSED`` → ``STARTED`` on ``RESUME`` or ``START`` (the remembered phase is restored)
    * ``STARTED`` / ``PAUSED`` → ``STOPPED`` on ``STOP``
    * any → ``STOPPED`` on ``RESET`` (always valid)
    * ``STARTED`` → ``COMPLETED`` via :meth:`mark_completed` (normal ``fit`` completion)
    * ``STARTED`` / ``PAUSED`` → ``FAILED`` via :meth:`mark_failed` (exception / user stop)

    The machine carries no model reference and no I/O; it is a pure state guard. The
    orchestration (threading, the actual ``model.fit`` call, monitor wiring) lives in
    :class:`~juniper_service_core.lifecycle.manager.ServiceLifecycleManager`.
    """

    def __init__(self) -> None:
        self._status = LifecycleStatus.STOPPED
        self._phase = PHASE_IDLE
        self._paused_phase: str | None = None

    @property
    def status(self) -> LifecycleStatus:
        """The current lifecycle status."""
        return self._status

    @property
    def phase(self) -> str:
        """The current open-string phase (``"idle"`` when not running)."""
        return self._phase

    @property
    def paused_phase(self) -> str | None:
        """The phase that was active when the machine entered ``PAUSED`` (``None`` otherwise)."""
        return self._paused_phase

    def is_stopped(self) -> bool:
        return self._status is LifecycleStatus.STOPPED

    def is_started(self) -> bool:
        return self._status is LifecycleStatus.STARTED

    def is_paused(self) -> bool:
        return self._status is LifecycleStatus.PAUSED

    def is_completed(self) -> bool:
        return self._status is LifecycleStatus.COMPLETED

    def is_failed(self) -> bool:
        return self._status is LifecycleStatus.FAILED

    def is_investigating(self) -> bool:
        return self._status is LifecycleStatus.INVESTIGATING

    def is_resume_ready(self) -> bool:
        return self._status is LifecycleStatus.RESUME_READY

    def is_replaying(self) -> bool:
        return self._status is LifecycleStatus.REPLAYING

    def is_active(self) -> bool:
        """True while a run can make progress (``STARTED`` or ``PAUSED``)."""
        return self._status in (LifecycleStatus.STARTED, LifecycleStatus.PAUSED)

    def handle_command(self, command: LifecycleCommand) -> bool:
        """Apply ``command`` and perform the transition.

        Returns ``True`` if the transition was legal and applied, ``False`` otherwise (the
        caller surfaces an invalid transition as a ``409``/``RuntimeError`` at its boundary).
        """
        handler = {
            LifecycleCommand.START: self._handle_start,
            LifecycleCommand.STOP: self._handle_stop,
            LifecycleCommand.PAUSE: self._handle_pause,
            LifecycleCommand.RESUME: self._handle_resume,
            LifecycleCommand.RESET: self._handle_reset,
        }.get(command)
        if handler is None:  # pragma: no cover - exhaustive enum dispatch
            logger.error("Unknown command: %s", command)
            return False
        return handler()

    def _handle_start(self) -> bool:
        # A loaded-for-inspection snapshot / an active replay must be exited first.
        if self._status in (LifecycleStatus.INVESTIGATING, LifecycleStatus.REPLAYING):
            logger.warning("Invalid transition: START while %s -- exit it first (retrain/resume, or stop replay)", self._status.name)
            return False
        if self._status in (LifecycleStatus.FAILED, LifecycleStatus.COMPLETED):
            logger.info("Auto-resetting from terminal state %s before start", self._status.name)
            self._reset_to_stopped()
        # STOPPED (a fresh run) and RESUME_READY (continue from a loaded snapshot) both start;
        # the history difference is the manager's concern, not the FSM's.
        if self._status in (LifecycleStatus.STOPPED, LifecycleStatus.RESUME_READY):
            prev = self._status.name
            self._status = LifecycleStatus.STARTED
            self._phase = PHASE_RUNNING
            self._paused_phase = None
            logger.info("State transition: %s -> Started", prev)
            return True
        if self._status is LifecycleStatus.PAUSED:
            return self._restore_from_paused()
        logger.warning("Invalid transition: START while already Started")
        return False

    def _handle_stop(self) -> bool:
        if self._status in (LifecycleStatus.STARTED, LifecycleStatus.PAUSED):
            prev = self._status.name
            self._reset_to_stopped()
            logger.info("State transition: %s -> Stopped", prev)
            return True
        logger.warning("Invalid transition: STOP while already Stopped")
        return False

    def _handle_pause(self) -> bool:
        if self._status is LifecycleStatus.STARTED:
            self._status = LifecycleStatus.PAUSED
            self._paused_phase = self._phase
            logger.info("State transition: Started -> Paused (saved phase: %s)", self._phase)
            return True
        logger.warning("Invalid transition: PAUSE while %s", self._status.name)
        return False

    def _handle_resume(self) -> bool:
        if self._status is LifecycleStatus.PAUSED:
            return self._restore_from_paused()
        logger.warning("Invalid transition: RESUME while %s", self._status.name)
        return False

    def _handle_reset(self) -> bool:
        prev = self._status.name
        self._reset_to_stopped()
        logger.info("State transition: %s -> Stopped (RESET)", prev)
        return True

    def _restore_from_paused(self) -> bool:
        self._status = LifecycleStatus.STARTED
        self._phase = self._paused_phase or PHASE_RUNNING
        logger.info("State transition: Paused -> Started (restored phase: %s)", self._phase)
        self._paused_phase = None
        return True

    def _reset_to_stopped(self) -> None:
        self._status = LifecycleStatus.STOPPED
        self._phase = PHASE_IDLE
        self._paused_phase = None

    def set_phase(self, phase: str) -> None:
        """Set the current phase string. No-op unless the machine is ``STARTED``.

        Typically driven by a ``phase_change`` :class:`~juniper_model_core.events.TrainingEvent`
        emitted from inside ``model.fit`` (the model maps its native phase onto the string).
        """
        if self._status is not LifecycleStatus.STARTED:
            logger.warning("Cannot set phase to %r while status is %s", phase, self._status.name)
            return
        prev = self._phase
        self._phase = phase
        logger.debug("Phase change: %s -> %s", prev, phase)

    def mark_completed(self) -> bool:
        """Move ``STARTED`` → ``COMPLETED`` (terminal). Returns ``False`` from any other state."""
        if self._status is LifecycleStatus.STARTED:
            self._status = LifecycleStatus.COMPLETED
            self._phase = PHASE_IDLE
            self._paused_phase = None
            logger.info("State transition: Started -> Completed")
            return True
        logger.warning("Invalid transition: mark_completed while %s", self._status.name)
        return False

    def mark_failed(self, reason: str = "Unknown error") -> bool:
        """Move ``STARTED`` / ``PAUSED`` → ``FAILED`` (terminal). Returns ``False`` otherwise."""
        if self._status in (LifecycleStatus.STARTED, LifecycleStatus.PAUSED):
            prev = self._status.name
            self._status = LifecycleStatus.FAILED
            self._phase = PHASE_IDLE
            self._paused_phase = None
            logger.info("State transition: %s -> Failed (%s)", prev, reason)
            return True
        logger.warning("Invalid transition: mark_failed while %s", self._status.name)
        return False

    def mark_investigating(self) -> bool:
        """Enter ``INVESTIGATING`` -- a snapshot loaded for inspection (training rejected until a
        retrain/resume). Permitted only from a non-active state (not ``STARTED`` / ``PAUSED``)."""
        if self.is_active():
            logger.warning("Invalid transition: mark_investigating while %s", self._status.name)
            return False
        self._status = LifecycleStatus.INVESTIGATING
        self._phase = PHASE_IDLE
        self._paused_phase = None
        logger.info("State transition: -> Investigating")
        return True

    def mark_resume_ready(self) -> bool:
        """Enter ``RESUME_READY`` -- a snapshot loaded to continue training; the next ``START``
        resumes (the manager preserves the loaded history). Permitted only from a non-active state."""
        if self.is_active():
            logger.warning("Invalid transition: mark_resume_ready while %s", self._status.name)
            return False
        self._status = LifecycleStatus.RESUME_READY
        self._phase = PHASE_IDLE
        self._paused_phase = None
        logger.info("State transition: -> ResumeReady")
        return True

    def mark_replaying(self) -> bool:
        """Enter ``REPLAYING`` -- a snapshot's history is being played back. Permitted only from a
        non-active state (not ``STARTED`` / ``PAUSED``)."""
        if self.is_active():
            logger.warning("Invalid transition: mark_replaying while %s", self._status.name)
            return False
        self._status = LifecycleStatus.REPLAYING
        self._phase = PHASE_IDLE
        self._paused_phase = None
        logger.info("State transition: -> Replaying")
        return True

    def get_state_summary(self) -> dict:
        """The machine's state as a JSON-ready dict.

        ``status`` is the UPPERCASE enum ``.name`` (e.g. ``"STARTED"``); ``phase`` /
        ``paused_phase`` are the open strings. Downstream consumers should normalize status
        case-insensitively (canopy's ``state_sync`` is the reference normalizer).
        """
        return {
            "status": self._status.name,
            "phase": self._phase,
            "paused_phase": self._paused_phase,
        }
