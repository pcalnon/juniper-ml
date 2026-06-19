"""Generic snapshot replay (WS-2 / OUT-11 T2 step 1c).

Plays a snapshot's stored metric history back as timed frames -- the de-cascored core of
cascor's ``_ReplaySession``. cascor's replay also carries cascade-specific topology-evolution
metadata and per-sample weight playback (CAN-015g); this generic session replays only the
model-agnostic metric history captured in the snapshot sidecar (the ``LifecycleMonitor``
history). An injected ``on_frame`` sink lets a transport push frames -- the step-2 websocket
wires it; without one, the session still advances its position over wall-clock, readable via
:meth:`state` and pollable through the routes.

Pure stdlib -- no third-party import, safe on the dependency-free import path.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable
from typing import Any

__all__ = ["ReplaySession", "MAX_TICK_SECONDS", "REPLAY_ACTIONS"]

logger = logging.getLogger("juniper_service_core.lifecycle.replay")

#: Upper bound on a single inter-frame sleep, so pause/stop are observed within this window.
MAX_TICK_SECONDS = 0.5
#: The control actions :meth:`ReplaySession.control` accepts.
REPLAY_ACTIONS = ("play", "pause", "seek", "speed", "range", "stop", "status")


class ReplaySession:
    """A background-threaded playback of a snapshot's metric ``history``.

    Starts **paused** at ``time_index`` 0 (deterministic). While playing, a daemon advances
    ``time_index`` by ``sign(speed)`` on a speed-derived cadence and emits each frame to the
    injected ``on_frame`` sink, auto-pausing at a range boundary. All control actions
    (play/pause/seek/speed/range/stop/status) mutate state under a lock and return :meth:`state`.
    """

    def __init__(
        self,
        snapshot_id: str,
        history: list[dict[str, Any]],
        *,
        on_frame: Callable[[dict[str, Any]], None] | None = None,
        on_complete: Callable[[], None] | None = None,
    ) -> None:
        self.snapshot_id = snapshot_id
        self._history: list[dict[str, Any]] = [dict(entry) for entry in history]
        self._on_frame = on_frame
        self._on_complete = on_complete
        self._lock = threading.RLock()
        self._length = len(self._history)
        self._time_index = 0
        self._speed = 1.0
        self._paused = True
        self._range_start = 0
        self._range_end = self._length
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._started = False
        self._thread = threading.Thread(target=self._run, name=f"replay-{snapshot_id}", daemon=True)

    def start(self) -> dict[str, Any]:
        """Start the playback daemon (paused at frame 0) and emit the initial frame."""
        with self._lock:
            if not self._started:
                self._started = True
                self._thread.start()
        self._emit_frame()
        return self.state()

    def control(self, action: str, **params: Any) -> dict[str, Any]:
        """Apply a control action; returns the resulting :meth:`state`. Raises on an unknown action."""
        if action not in REPLAY_ACTIONS:
            raise ValueError(f"Unknown replay action: {action!r}")
        emit = False
        with self._lock:
            if action == "play":
                self._paused = False
            elif action == "pause":
                self._paused = True
            elif action == "seek":
                self._time_index = self._clamp(int(params.get("time_index", self._time_index)))
                emit = True
            elif action == "speed":
                self._speed = max(-10.0, min(10.0, float(params.get("value", self._speed))))
            elif action == "range":
                start = max(0, min(int(params.get("start", self._range_start)), self._length))
                end = max(start, min(int(params.get("end", self._range_end)), self._length))
                self._range_start, self._range_end = start, end
                self._time_index = self._clamp(self._time_index)
            elif action == "stop":
                self.stop()
                return self.state()
            # "status" is a pure read -- falls through to state()
        self._wake.set()
        if emit:
            self._emit_frame()
        return self.state()

    def step(self) -> bool:
        """Advance one frame by ``sign(speed)``; auto-pause at a range boundary.

        Returns ``True`` if it advanced. Synchronous -- the daemon calls this on a cadence, and
        tests call it directly for deterministic coverage.
        """
        with self._lock:
            if self._paused or abs(self._speed) < 0.1:
                return False
            nxt = self._time_index + (1 if self._speed > 0 else -1)
            if nxt < self._range_start or nxt >= self._range_end:
                self._paused = True  # auto-pause at the boundary
                advanced = False
            else:
                self._time_index = nxt
                advanced = True
        if advanced:
            self._emit_frame()
        return advanced

    def stop(self) -> None:
        """Signal the daemon to exit (idempotent) and fire the ``on_complete`` hook."""
        already = self._stop.is_set()
        self._stop.set()
        self._wake.set()
        if not already and self._on_complete is not None:
            try:
                self._on_complete()
            except Exception:  # noqa: BLE001 - a sink error must not wedge stop; the manager owns the FSM
                logger.debug("replay on_complete hook raised", exc_info=True)

    def join(self, timeout: float | None = None) -> bool:
        """Wait for the daemon to exit. Returns ``True`` if it is no longer alive."""
        if not self._started:
            return True
        self._thread.join(timeout)
        return not self._thread.is_alive()

    def state(self) -> dict[str, Any]:
        """A JSON-ready snapshot of the playback position + the current frame."""
        with self._lock:
            return {
                "snapshot_id": self.snapshot_id,
                "length": self._length,
                "time_index": self._time_index,
                "speed": self._speed,
                "paused": self._paused,
                "range": {"start": self._range_start, "end": self._range_end},
                "frame": self._frame_at(self._time_index),
                "stopped": self._stop.is_set(),
            }

    def _clamp(self, index: int) -> int:
        upper = max(self._range_start, self._range_end - 1)
        return max(self._range_start, min(index, upper))

    def _frame_at(self, index: int) -> dict[str, Any] | None:
        if 0 <= index < self._length:
            entry = self._history[index]
            return {
                "time_index": index,
                "epoch": entry.get("epoch", index),
                "metrics": dict(entry.get("metrics", {})),
                "replay": True,
                "snapshot_id": self.snapshot_id,
            }
        return None

    def _emit_frame(self) -> None:
        if self._on_frame is None:
            return
        with self._lock:
            frame = self._frame_at(self._time_index)
        if frame is not None:
            try:
                self._on_frame(frame)
            except Exception:  # noqa: BLE001 - a transport error must not crash the replay daemon
                logger.debug("replay on_frame sink raised", exc_info=True)

    def _run(self) -> None:
        while not self._stop.is_set():
            with self._lock:
                idle = self._paused or abs(self._speed) < 0.1
                speed = abs(self._speed)
            if idle:
                self._wake.wait(MAX_TICK_SECONDS)
                self._wake.clear()
                continue
            self.step()
            self._stop.wait(min(1.0 / speed, MAX_TICK_SECONDS) if speed else MAX_TICK_SECONDS)
