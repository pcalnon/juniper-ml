"""Pin ReplaySession speed and range boundaries (lifecycle/replay.py).

The playback daemon sleeps ``min(1/abs(speed), MAX_TICK_SECONDS)``. ``control("speed")``
clamps to ``[-10, 10]``; without that clamp a client can drive the sleep toward zero and
busy-loop the daemon. ``step()`` treats ``abs(speed) < 0.1`` as idle, so the threshold
itself must still advance. Negative speed steps backward and auto-pauses at the range
start instead of wrapping to the last frame. ``range`` clamps into the history and
collapses an inverted window (``end < start``) so the playback interval cannot run
backwards relative to its own bounds.

Synchronous only: ``control`` / ``step`` / ``state`` take the session lock and do not
need the daemon. Starting it would race ``step()`` the way
``test_replay_controls_are_synchronous`` already documents.
"""

from __future__ import annotations

import pytest

from juniper_service_core.lifecycle.replay import ReplaySession


def _history(n: int) -> list[dict]:
    return [{"epoch": i, "metrics": {"mse": 1.0 / (i + 1)}} for i in range(n)]


def test_speed_clamps_to_ten_and_keeps_the_current_value_when_omitted() -> None:
    session = ReplaySession("s", _history(4))
    assert session.control("speed", value=10)["speed"] == 10.0
    assert session.control("speed", value=10.1)["speed"] == 10.0
    assert session.control("speed", value=1e9)["speed"] == 10.0
    assert session.control("speed", value=-10)["speed"] == -10.0
    assert session.control("speed", value=-10.1)["speed"] == -10.0
    assert session.control("speed", value=-1e9)["speed"] == -10.0
    # An omitted value is "leave it", not a reset to the default of 1.
    assert session.control("speed")["speed"] == -10.0


def test_non_numeric_speed_raises_and_leaves_the_previous_speed() -> None:
    session = ReplaySession("s", _history(3))
    session.control("speed", value=2)
    with pytest.raises(ValueError):
        session.control("speed", value="fast")
    assert session.state()["speed"] == 2.0
    assert session.state()["time_index"] == 0


def test_speed_below_the_dead_zone_does_not_advance_and_the_boundary_does() -> None:
    session = ReplaySession("s", _history(4))
    session.control("play")
    session.control("seek", time_index=1)
    session.control("speed", value=0.05)
    assert session.step() is False
    state = session.state()
    assert state["time_index"] == 1
    assert state["paused"] is False  # idle magnitude is not a pause

    session.control("speed", value=0.1)
    assert session.step() is True
    assert session.state()["time_index"] == 2

    session.control("seek", time_index=2)
    session.control("speed", value=-0.1)
    assert session.step() is True
    assert session.state()["time_index"] == 1
    assert session.state()["paused"] is False


def test_negative_speed_auto_pauses_at_the_range_start_without_wrapping() -> None:
    session = ReplaySession("s", _history(5))
    session.control("range", start=1, end=4)
    session.control("seek", time_index=2)
    session.control("speed", value=-1)
    session.control("play")
    assert session.step() is True
    assert session.state()["time_index"] == 1
    # The next index would be 0, which is before the range. Stay put and pause.
    assert session.step() is False
    state = session.state()
    assert state["paused"] is True
    assert state["time_index"] == 1
    assert state["frame"]["epoch"] == 1


def test_range_clamps_into_the_history_and_an_inverted_window_collapses() -> None:
    session = ReplaySession("s", _history(5))
    assert session.control("range", start=-5, end=99)["range"] == {"start": 0, "end": 5}
    assert session.control("seek", time_index=-3)["time_index"] == 0

    session.control("range", start=2, end=5)
    assert session.control("seek", time_index=-1)["time_index"] == 2

    collapsed = session.control("range", start=4, end=1)
    assert collapsed["range"] == {"start": 4, "end": 4}
    # The playhead is pulled into the collapsed window; it does not stay at 2.
    assert collapsed["time_index"] == 4
    assert session.control("seek", time_index=0)["time_index"] == 4
