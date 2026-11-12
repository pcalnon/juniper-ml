"""WebSocket handler for ``/ws/training`` -- the real-time training-metrics stream (step 2).

The de-cascored core of cascor's ``api/websocket/training_stream.py``. Server-to-client
streaming with optional resume. On connect:

1. ``connection_established`` (from ``manager.connect_pending``).
2. Optional resume handshake: the client sends a ``resume`` frame within the timeout.
3. On resume success: ``resume_ok``, the replayed events, then whatever was broadcast while they
   were being sent, then promote to active: every seq after the client's ``last_seq`` up to the
   promotion arrives once, in seq order, before the first live frame. A resume that cannot be
   kept continuous after ``resume_ok`` is not promoted: the server stops sending and closes the
   socket **1011** ``Resume replay incomplete`` (when the transport can still carry a close), so
   what the client holds is a gap-free prefix, and the client reconnects.
4. On a fresh connect: promote + ``initial_status`` + ``state`` + an ``initial_metrics`` burst.
5. Ongoing ``metrics`` / ``state`` broadcasts during training (pushed by the lifecycle bridge).

After promotion, the server sends application-level ``{"type":"ping","ts":<float>}`` heartbeats
every ``ws_heartbeat_interval_sec`` (default 30s); the client must reply ``{"type":"pong"}``
within ``ws_heartbeat_pong_timeout_sec`` (default 10s) or the connection is closed with close
code **1011** and reason ``"Heartbeat timeout: no pong or traffic within <N>s"``. It is
deliberately not 1006: RFC 6455 Section 7.4.1 reserves that value and forbids an endpoint from
setting it as a Close-frame status, and the ``websockets`` server raises rather than serialize
it -- so a 1006 close sends no frame at all and leaves the peer on a silent half-open socket.

A live socket whose broadcast send fails or times out is closed **1011** ``"Broadcast send failed
or timed out"`` by the manager, so the client reconnects (and can resume) rather than keep answering
heartbeats on a stream nothing is sent to. After any close by the server, the receive loop drains
until the ASGI server reports the disconnect, so the close frame is not dropped on the way out.

De-cascored from cascor: reads the live state through the generic
:class:`~juniper_service_core.lifecycle.manager.ServiceLifecycleManager` query surface
(``get_status`` / ``monitor.get_state`` / ``get_metrics_history``), drops cascor's
``api.observability`` emissions, and reads tunables off ``app.state.settings`` (with cascor's
defaults) instead of importing a service settings module.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
import logging
import time
from typing import NoReturn

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from juniper_service_core.websocket.manager import ReplayOutOfRange, ws_authenticate
from juniper_service_core.websocket.messages import create_initial_metrics_message, create_state_message
from juniper_service_core.websocket.tunables import resolve

__all__ = ["training_stream_handler"]

logger = logging.getLogger("juniper_service_core.websocket.training")

#: The close for a resume answered ``resume_ok`` whose continuity could not then be kept: a send
#: failed, or the replay buffer evicted a message the client still needed before it could be
#: delivered. 1011, as for this handler's other server-side failures. The client reconnects and
#: resumes again, or gets ``resume_failed`` ``out_of_range`` and a fresh snapshot.
_RESUME_INCOMPLETE_CLOSE_CODE = 1011
_RESUME_INCOMPLETE_CLOSE_REASON = "Resume replay incomplete"


def _setting(websocket: WebSocket, name: str):
    """Resolve a declared tunable off ``app.state.settings`` (no service settings import).

    The default now lives in :data:`~juniper_service_core.websocket.tunables.WS_TUNABLES`
    rather than at each call site, and a miss that looks like a misspelling is logged
    loudly instead of silently defaulting -- see that module for why (APD-SVCCORE-003).
    """
    return resolve(getattr(websocket.app.state, "settings", None), name)


async def _await_resume_frame(websocket: WebSocket, ws_manager, resume_timeout: float) -> tuple[bool, bool]:
    """Wait for an optional resume frame.

    Returns ``(resumed, disconnected)``. If ``disconnected`` is ``True``, the caller should
    return without further work.
    """
    try:
        raw = await asyncio.wait_for(websocket.receive_text(), timeout=resume_timeout)
        msg = json.loads(raw)
        if msg.get("type") == "resume":
            return await _handle_resume(websocket, ws_manager, msg), False
    except asyncio.TimeoutError:
        pass  # No resume frame -- fresh connect
    except json.JSONDecodeError:
        logger.debug("Non-JSON frame during resume handshake, treating as fresh connect")
    except WebSocketDisconnect:
        return False, True
    except Exception:  # noqa: BLE001 - any handshake error degrades to a fresh connect
        logger.debug("Error during resume handshake, treating as fresh connect")
    return False, False


async def _send_initial_state(websocket: WebSocket, ws_manager, lifecycle, initial_metrics_count: int = 100) -> None:
    """Send initial status + state + a recent-metrics burst to a freshly-connected client.

    ``initial_metrics`` is sent after ``state`` so a client can paint its time-series chart
    without a parallel REST poll. ``initial_metrics_count=0`` disables the burst.
    """
    if lifecycle is None:
        return
    status = lifecycle.get_status()
    await ws_manager.send_personal_message(websocket, {"type": "initial_status", "data": status})
    state_data = lifecycle.monitor.get_state()
    await ws_manager.send_personal_message(websocket, create_state_message(state_data))
    if initial_metrics_count > 0:
        await _send_metrics_burst(websocket, ws_manager, lifecycle, initial_metrics_count)


async def _send_metrics_burst(websocket: WebSocket, ws_manager, lifecycle, count: int) -> None:
    """Send an ``initial_metrics`` burst with the most-recent metrics."""
    try:
        metrics = lifecycle.get_metrics_history(count=count)
    except Exception:  # noqa: BLE001 - a history read must not abort the connect path
        logger.debug("Training WS: get_metrics_history failed; sending empty burst", exc_info=True)
        metrics = []
    if metrics is None:
        metrics = []
    await ws_manager.send_personal_message(websocket, create_initial_metrics_message(metrics, current_seq=ws_manager.current_seq))


async def _heartbeat_ping_loop(websocket: WebSocket, hb_interval: float, hb_timeout: float, pong_received: asyncio.Event) -> None:
    """Application-level ping/pong loop closing the connection on pong timeout."""
    while True:
        await asyncio.sleep(hb_interval)
        pong_received.clear()
        try:
            await websocket.send_json({"type": "ping", "ts": time.time()})
        except Exception:  # noqa: BLE001 - connection already closed
            return
        try:
            await asyncio.wait_for(pong_received.wait(), timeout=hb_timeout)
        except asyncio.TimeoutError:
            logger.info("Training WS: heartbeat timeout, closing -- no pong or traffic within %.0fs of ping (interval=%.0fs)", hb_timeout, hb_interval)
            try:
                # 1011, not 1006 -- RFC 6455 Section 7.4.1 forbids an endpoint from setting 1006
                # as a Close-frame status, and the ``websockets`` server raises rather than
                # serialize it, so the peer would be left with a silent half-open socket.
                # See the fuller note at the matching site in ``control_stream.py``.
                await websocket.close(code=1011, reason=f"Heartbeat timeout: no pong or traffic within {hb_timeout:.0f}s")
            except Exception:  # noqa: BLE001 - close after timeout is best-effort
                logger.debug("Training WS: close after heartbeat timeout failed", exc_info=True)
            return


async def _recv_pong_loop(websocket: WebSocket, pong_received: asyncio.Event, ws_manager=None, lifecycle=None, subscribe_metrics_max_count: int = 100) -> None:
    """Receive-loop dispatcher.

    Forwards ``pong`` frames to the heartbeat event and handles ``subscribe_metrics`` requests
    by replying with an ``initial_metrics`` envelope. All other frame types are ignored.

    Once the server has closed the socket -- the manager closes one whose broadcast send failed or
    timed out, and the heartbeat closes a silent one -- the loop starts no further
    ``receive_text()`` and drains instead (:func:`_drain_until_disconnect`). A ``receive_text()``
    already in progress when the server closed still completes, and the frame that completes it is
    dispatched as usual: a ``subscribe_metrics`` there reads the history, and its reply fails on
    the closed socket. Every later frame is discarded. The loop cannot call ``receive_text()``
    again: after the app's own close, Starlette refuses that with ``RuntimeError``, not
    ``WebSocketDisconnect``, so a frame the peer already had in flight would end the handler with
    an unhandled exception.
    """
    try:
        while True:
            if getattr(websocket, "application_state", None) is WebSocketState.DISCONNECTED:
                await _drain_until_disconnect(websocket)
                return
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except (json.JSONDecodeError, AttributeError):
                continue  # Non-JSON keep-alive frames are fine
            mtype = msg.get("type") if isinstance(msg, dict) else None
            if mtype == "pong":
                pong_received.set()
            elif mtype == "subscribe_metrics" and ws_manager is not None and lifecycle is not None:
                await _handle_subscribe_metrics(websocket, ws_manager, lifecycle, msg, subscribe_metrics_max_count)
    except WebSocketDisconnect:
        logger.debug("Training WS: receive loop ended due to client disconnect")
        return


async def _drain_until_disconnect(websocket: WebSocket) -> None:
    """After the server's own close, discard what arrives until the ASGI server reports the disconnect.

    ``receive()`` checks only the peer's side of the socket, so unlike ``receive_text()`` it still
    works after the app's close. The handler must not return before the disconnect: uvicorn's
    sans-I/O protocol holds a close frame while its write buffer is full and drops the transport if
    the app returns first, which turns a clean close into an abnormal 1006 on the peer's side. The
    ASGI server reports the disconnect once the close frame is written or the connection is lost.
    What arrives meanwhile is not dispatched: the stream is over.

    Known limit: the drain has no time bound of its own. With a peer that has stopped reading it
    lasts for as long as the ASGI server takes to give up on the connection, and the handler,
    which ``endpoint_counts()`` still counts, lasts with it.
    """
    while True:
        message = await websocket.receive()
        if message.get("type") == "websocket.disconnect":
            return


async def _handle_subscribe_metrics(websocket: WebSocket, ws_manager, lifecycle, msg: dict, default_count: int) -> None:
    """Respond to a client ``subscribe_metrics`` with a metrics burst.

    Used when a client reconnects via the resume path (which only replays ``seq>last_seq`` from
    the broadcast buffer) but also wants the rolling metrics window.
    """
    data = msg.get("data") or {}
    requested = data.get("max_count")
    try:
        count = int(requested) if requested is not None else default_count
    except (TypeError, ValueError):
        count = default_count
    count = max(1, min(count, default_count))
    await _send_metrics_burst(websocket, ws_manager, lifecycle, count)


async def training_stream_handler(websocket: WebSocket) -> None:
    """Handle ``/ws/training`` WebSocket connections with optional resume.

    Protocol flow:
    1. Authenticate via the API-key header.
    2. Accept as pending (``connect_pending`` -- not broadcast-eligible).
    3. Wait for an optional ``resume`` frame within the handshake timeout.
    4. On resume: validate ``server_instance_id``, replay buffered events, deliver any broadcast
       that landed meanwhile, and promote to active with no gap (``_handle_resume``) -- or close
       1011 and return when that cannot be kept.
    5. On fresh connect / failed resume: promote to active, then send ``initial_status`` +
       ``state``.
    6. Heartbeat + keep-alive recv loop.
    """
    if not await ws_authenticate(websocket):
        return

    ws_manager = getattr(websocket.app.state, "ws_manager", None)
    lifecycle = getattr(websocket.app.state, "lifecycle", None)

    if ws_manager is None:
        await websocket.close(code=1011, reason="WebSocket manager not available")
        return

    # Capture the serving loop so the training thread's broadcast_from_thread can reach it. The
    # handler runs on the app's event loop, so this needs no separate startup hook (idempotent).
    ws_manager.set_event_loop(asyncio.get_running_loop())

    connected = await ws_manager.connect_pending(websocket)
    if not connected:
        return

    resume_timeout = _setting(websocket, "ws_resume_handshake_timeout_s")
    initial_metrics_count = _setting(websocket, "ws_initial_metrics_count")

    try:
        resumed, disconnected = await _await_resume_frame(websocket, ws_manager, resume_timeout)
        if disconnected:
            return

        if not resumed:
            # Promote to active (now eligible for broadcasts). A resumed socket is active already:
            # _handle_resume promoted it once its replay, and anything broadcast meanwhile, was
            # delivered.
            await ws_manager.promote_to_active(websocket)
        ws_manager.register_endpoint_connection(websocket, "training")

        if not resumed:
            await _send_initial_state(websocket, ws_manager, lifecycle, initial_metrics_count)

        # Broadcasts come from the training thread via ws_manager.broadcast_from_thread() (wired
        # by the lifecycle bridge). The recv loop handles pong responses and subscribe_metrics.
        hb_interval = _setting(websocket, "ws_heartbeat_interval_sec")
        hb_timeout = _setting(websocket, "ws_heartbeat_pong_timeout_sec")
        pong_received = asyncio.Event()
        pong_received.set()  # No outstanding ping at start

        ping_task = asyncio.create_task(_heartbeat_ping_loop(websocket, hb_interval, hb_timeout, pong_received))
        try:
            await _recv_pong_loop(websocket, pong_received, ws_manager=ws_manager, lifecycle=lifecycle, subscribe_metrics_max_count=initial_metrics_count or 100)
        finally:
            ping_task.cancel()
            # CancelledError is expected when awaiting a task after explicit cancellation.
            with contextlib.suppress(asyncio.CancelledError):
                await ping_task
    finally:
        ws_manager.unregister_endpoint_connection(websocket)
        await ws_manager.disconnect(websocket)


async def _abort_resume(websocket: WebSocket, why: str, *, level: int = logging.WARNING, exc_info: BaseException | None = None) -> NoReturn:
    """End a resume whose continuity can no longer be kept: close the socket, report a disconnect.

    ``resume_ok`` may already be on the wire, so a ``resume_failed`` could contradict it; the
    close is the signal left. It is best effort: a transport that is already gone carries no
    close frame. Raising ``WebSocketDisconnect`` takes the handler down its disconnected path
    (``_await_resume_frame`` returns ``disconnected``), so the socket is never promoted.
    """
    logger.log(level, "Resume aborted after resume_ok: %s; closing %d so the client reconnects", why, _RESUME_INCOMPLETE_CLOSE_CODE, exc_info=exc_info)
    with contextlib.suppress(Exception):
        await websocket.close(code=_RESUME_INCOMPLETE_CLOSE_CODE, reason=_RESUME_INCOMPLETE_CLOSE_REASON)
    raise WebSocketDisconnect(code=_RESUME_INCOMPLETE_CLOSE_CODE, reason=_RESUME_INCOMPLETE_CLOSE_REASON)


async def _deliver_resume(websocket: WebSocket, ws_manager, last_seq: int, events: list[dict]) -> None:
    """Send ``resume_ok`` and the replay, then promote through the manager's catch-up.

    A frame that fails to send would leave a hole the client cannot see, so the resume ends
    there instead of skipping it (:func:`_abort_resume`). That end is logged at INFO: a send
    fails most often because the client went away, and the manager has already logged a send
    that timed out at WARNING.
    """
    if not await ws_manager.send_personal_message(
        websocket,
        {"type": "resume_ok", "timestamp": time.time(), "data": {"replayed_count": len(events)}},
    ):
        await _abort_resume(websocket, "resume_ok was not delivered", level=logging.INFO)
    # ``replayed_through`` is the last seq the client now holds.
    replayed_through = last_seq
    for event in events:
        if not await ws_manager.send_personal_message(websocket, event):
            await _abort_resume(websocket, f"replayed seq {event.get('seq')} was not delivered", level=logging.INFO)
        replayed_through = event["seq"]
    # A broadcast that landed while the replay was being sent is buffered, but went only to the
    # sockets already active. The manager sends those, then activates the socket with no gap.
    if not await ws_manager.promote_to_active(websocket, replayed_through=replayed_through):
        # WebSocketManager has logged why: a WARNING for an eviction, INFO for a failed send or a
        # socket closed meanwhile (a send that timed out also has its own WARNING). A service's own
        # manager may log nothing, so this line can be the only record.
        await _abort_resume(websocket, "the catch-up after the replay did not complete", level=logging.INFO)


async def _handle_resume(websocket: WebSocket, ws_manager, msg: dict) -> bool:
    """Handle a resume request. Returns ``True`` if resume succeeded.

    On success the socket is already active: every buffered seq after the client's ``last_seq``
    assigned before the promotion has been sent to it once, in seq order, and every later one is
    in the live fan-out. If that cannot be kept after ``resume_ok`` -- a send fails, the replay
    buffer evicts a frame the client still needs, or the manager raises -- the socket is closed
    1011 and ``WebSocketDisconnect`` is raised instead.
    """
    data = msg.get("data", {})
    last_seq = data.get("last_seq")
    client_server_id = data.get("server_instance_id")

    if last_seq is None or client_server_id is None:
        await ws_manager.send_personal_message(
            websocket,
            {"type": "resume_failed", "timestamp": time.time(), "data": {"reason": "malformed_resume"}},
        )
        logger.debug("Resume failed: malformed resume frame (missing last_seq or server_instance_id)")
        return False

    # Server-restart detection via UUID mismatch.
    if client_server_id != ws_manager.server_instance_id:
        await ws_manager.send_personal_message(
            websocket,
            {"type": "resume_failed", "timestamp": time.time(), "data": {"reason": "server_restarted"}},
        )
        logger.info("Resume failed: server_instance_id mismatch (server restarted)")
        return False

    try:
        events = ws_manager.replay_since(last_seq)
    except ReplayOutOfRange as e:
        await ws_manager.send_personal_message(
            websocket,
            {"type": "resume_failed", "timestamp": time.time(), "data": {"reason": "out_of_range"}},
        )
        logger.info("Resume failed: %s", e)
        return False

    # Resume succeeded. From here ``resume_ok`` may be on the wire, so a failure must close the
    # socket: ``_await_resume_frame`` turns any other exception into a fresh connect, which would
    # follow ``resume_ok`` with a snapshot, and promote without the catch-up. (A manager whose
    # ``promote_to_active`` predates ``replayed_through`` raises TypeError here, for one.)
    try:
        await _deliver_resume(websocket, ws_manager, last_seq, events)
    except WebSocketDisconnect:
        raise
    except Exception as exc:  # noqa: BLE001 - after resume_ok, any failure ends the resume
        await _abort_resume(websocket, f"{type(exc).__name__} while resuming", exc_info=exc)
    logger.info("Resume succeeded: replayed %d events from seq %d", len(events), last_seq)
    return True
