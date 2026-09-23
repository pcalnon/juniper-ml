"""Scratch pytest plugin (agent-s): repeat selected tests N times and record WS message order.

Not repository content. Loaded by run_repeat.py via pytest.main(plugins=[...]).

--wsr-repeat N   parametrize every collected test N times (pytest-repeat is not installed)
--wsr-log PATH   append one JSON line per WebSocketTestSession.receive_json() call
                 ({"node", "sid", "type"}) and one per test call outcome ({"node", "outcome"})
"""

import itertools
import json
import threading

import pytest

_counter = itertools.count(1)
_lock = threading.Lock()
_state = {"nodeid": None, "log": None}


def pytest_addoption(parser):
    group = parser.getgroup("wsrepeat")
    group.addoption("--wsr-repeat", type=int, default=1)
    group.addoption("--wsr-log", default=None)
    group.addoption("--wsr-drain", action="store_true", default=False)
    # Causal experiment: replace main.offload (asyncio.to_thread) with an in-coroutine call, i.e.
    # the pre-#567 (X7 slice 1a) shape of the /ws/training connect path. Scratch only.
    group.addoption("--wsr-sync-offload", action="store_true", default=False)


def _drain_types(session, max_msgs=12, quiet=0.15):
    """Read whatever the server already sent (or sends within `quiet` s) and return the frame types."""
    import anyio

    out = []
    for _ in range(max_msgs):

        async def _recv():
            with anyio.fail_after(quiet):
                return await session._send_rx.receive()

        try:
            message = session.portal.call(_recv)
        except TimeoutError:
            break
        except Exception as exc:  # stream closed etc.
            out.append(f"<{type(exc).__name__}>")
            break
        if message.get("type") != "websocket.send":
            out.append(f"<{message.get('type')}>")
            break
        text = message.get("text")
        if text is None:
            text = (message.get("bytes") or b"").decode("utf-8")
        try:
            body = json.loads(text)
            t = body.get("type")
            out.append(f"{t}*" if body.get("_test_via_broadcast") else t)
        except Exception:
            out.append("?")
    return out


@pytest.fixture
def _wsr_idx(request):
    return request.param


def pytest_generate_tests(metafunc):
    n = metafunc.config.getoption("--wsr-repeat")
    if n > 1:
        metafunc.fixturenames.append("_wsr_idx")
        metafunc.parametrize("_wsr_idx", range(n), indirect=True, ids=lambda i: f"r{i}")


def _append(rec):
    with _lock:
        with open(_state["log"], "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec) + "\n")


def pytest_configure(config):
    log = config.getoption("--wsr-log")
    if not log:
        return
    _state["log"] = log
    from starlette.testclient import WebSocketTestSession

    orig = WebSocketTestSession.receive_json

    def recording_receive_json(self, *args, **kwargs):
        msg = orig(self, *args, **kwargs)
        sid = getattr(self, "_wsr_sid", None)
        if sid is None:
            sid = next(_counter)
            self._wsr_sid = sid
        mtype = msg.get("type") if isinstance(msg, dict) else None
        if isinstance(msg, dict) and msg.get("_test_via_broadcast"):
            mtype = f"{mtype}*"  # '*' = frame carried the test's broadcast tag
        _append({"node": _state["nodeid"], "sid": sid, "type": mtype})
        return msg

    WebSocketTestSession.receive_json = recording_receive_json

    if config.getoption("--wsr-drain"):
        orig_exit = WebSocketTestSession.__exit__

        def draining_exit(self, *args):
            sid = getattr(self, "_wsr_sid", None)
            if sid is not None:
                _append({"node": _state["nodeid"], "sid": sid, "post": _drain_types(self)})
            return orig_exit(self, *args)

        WebSocketTestSession.__exit__ = draining_exit


def pytest_runtest_setup(item):
    _state["nodeid"] = item.nodeid
    if item.config.getoption("--wsr-sync-offload"):
        import main

        async def _sync_offload(fn, /, *args, **kwargs):
            return fn(*args, **kwargs)

        main.offload = _sync_offload


def pytest_runtest_logreport(report):
    if _state["log"] and report.when == "call":
        _append({"node": report.nodeid, "outcome": report.outcome})
