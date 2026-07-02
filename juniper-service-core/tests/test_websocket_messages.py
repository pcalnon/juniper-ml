"""Unit coverage for the generic WebSocket message builders (C-4a).

Targets the envelope ``seq`` / ``emitted_at_monotonic`` branches and the ``topology`` / ``event`` /
``chunked_message`` builders that the both-stacks-green contract test in ``test_t2_websocket.py``
does not exercise directly. Pure builders -- no async, no transport.
"""

from __future__ import annotations

from juniper_service_core.websocket.messages import (
    create_chunked_message,
    create_control_ack_message,
    create_event_message,
    create_initial_metrics_message,
    create_metrics_message,
    create_state_message,
    create_topology_message,
)


def test_metrics_message_includes_seq_and_monotonic() -> None:
    msg = create_metrics_message({"mse": 0.5}, seq=7, emitted_at_monotonic=123.5)
    assert msg["type"] == "metrics"
    assert msg["seq"] == 7
    assert msg["emitted_at_monotonic"] == 123.5
    assert msg["data"] == {"mse": 0.5}
    assert "timestamp" in msg


def test_state_message_omits_unset_seq_fields() -> None:
    msg = create_state_message({"phase": "running"})
    assert msg["type"] == "state"
    assert "seq" not in msg
    assert "emitted_at_monotonic" not in msg


def test_topology_message_carries_payload() -> None:
    msg = create_topology_message({"layers": [1, 2]})
    assert msg["type"] == "topology"
    assert msg["data"] == {"layers": [1, 2]}


def test_event_message_carries_payload() -> None:
    msg = create_event_message({"event_type": "epoch_end"})
    assert msg["type"] == "event"
    assert msg["data"] == {"event_type": "epoch_end"}


def test_chunked_message_shape() -> None:
    msg = create_chunked_message(chunk_id="cid", chunk_index=1, total_chunks=3, original_type="topology", payload="abc")
    assert msg["type"] == "chunked_message"
    data = msg["data"]
    assert data["chunk_id"] == "cid"
    assert data["chunk_index"] == 1
    assert data["total_chunks"] == 3
    assert data["original_type"] == "topology"
    assert data["payload"] == "abc"


def test_initial_metrics_message_defaults_current_seq() -> None:
    msg = create_initial_metrics_message([{"mse": 1.0}])
    assert msg["type"] == "initial_metrics"
    assert msg["data"]["count"] == 1
    assert msg["data"]["current_seq"] == 0


def test_initial_metrics_message_reports_current_seq() -> None:
    msg = create_initial_metrics_message([{"mse": 1.0}, {"mse": 0.5}], current_seq=42)
    assert msg["data"]["count"] == 2
    assert msg["data"]["current_seq"] == 42


def test_control_ack_message_full_payload() -> None:
    msg = create_control_ack_message("start", "success", data={"ok": True}, command_id="c1", code="none")
    assert msg["type"] == "command_response"
    payload = msg["data"]
    assert payload["command"] == "start"
    assert payload["status"] == "success"
    assert payload["result"] == {"ok": True}
    assert payload["command_id"] == "c1"
    assert payload["code"] == "none"


def test_control_ack_message_minimal_payload() -> None:
    msg = create_control_ack_message("stop", "error", error="boom")
    payload = msg["data"]
    assert payload["error"] == "boom"
    assert "result" not in payload
    assert "command_id" not in payload
    assert "code" not in payload
