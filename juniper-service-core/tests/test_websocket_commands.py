"""Unit coverage for the injectable control-command dispatch (C-4a).

Drives :class:`LifecycleCommandExecutor` directly (bypassing the transport) so every verb branch
-- including the ``start``-unbound reject, the ``set_params``-without-params reject, and the
unhandled-command fall-through -- is exercised deterministically. Also pins the
:class:`CommandExecutor` protocol's abstract-method bodies via a ``super()``-delegating subclass.
"""

from __future__ import annotations

from typing import Any

import pytest

from juniper_service_core.websocket.commands import DEFAULT_COMMANDS, CommandExecutor, LifecycleCommandExecutor


class _FakeManager:
    """Minimal manager stand-in recording the verb each executor call delegates to."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def stop_training(self) -> dict[str, str]:
        self.calls.append(("stop", None))
        return {"status": "stopped"}

    def pause_training(self) -> dict[str, str]:
        self.calls.append(("pause", None))
        return {"status": "paused"}

    def resume_training(self) -> dict[str, str]:
        self.calls.append(("resume", None))
        return {"status": "resumed"}

    def reset(self) -> dict[str, str]:
        self.calls.append(("reset", None))
        return {"status": "reset"}

    def update_params(self, params: dict[str, Any]) -> dict[str, Any]:
        self.calls.append(("set_params", params))
        return dict(params)


def test_start_unbound_drops_verb_and_rejects() -> None:
    mgr = _FakeManager()
    executor = LifecycleCommandExecutor(mgr)
    assert "start" not in executor.commands
    with pytest.raises(ValueError, match="start handler"):
        executor.execute("start")


def test_start_bound_delegates_to_callback() -> None:
    mgr = _FakeManager()
    executor = LifecycleCommandExecutor(mgr, start=lambda params: {"started": params})
    assert executor.commands == DEFAULT_COMMANDS
    assert executor.execute("start", {"epochs": 3}) == {"started": {"epochs": 3}}


def test_stop_and_resume_delegate_to_manager() -> None:
    mgr = _FakeManager()
    executor = LifecycleCommandExecutor(mgr)
    assert executor.execute("stop") == {"status": "stopped"}
    assert executor.execute("resume") == {"status": "resumed"}
    assert [c[0] for c in mgr.calls] == ["stop", "resume"]


def test_pause_and_reset_delegate_to_manager() -> None:
    mgr = _FakeManager()
    executor = LifecycleCommandExecutor(mgr)
    assert executor.execute("pause") == {"status": "paused"}
    assert executor.execute("reset") == {"status": "reset"}


def test_set_params_requires_params() -> None:
    mgr = _FakeManager()
    executor = LifecycleCommandExecutor(mgr)
    with pytest.raises(ValueError, match="params"):
        executor.execute("set_params", None)
    assert executor.execute("set_params", {"lr": 0.1}) == {"lr": 0.1}


def test_unhandled_command_raises() -> None:
    mgr = _FakeManager()
    executor = LifecycleCommandExecutor(mgr)
    with pytest.raises(ValueError, match="Unhandled command"):
        executor.execute("frobnicate")


def test_command_executor_protocol_abstract_bodies_raise() -> None:
    class _Impl(CommandExecutor):
        @property
        def commands(self) -> tuple[str, ...]:
            return super().commands

        def execute(self, command: str, params: dict[str, Any] | None) -> dict[str, Any]:
            return super().execute(command, params)

    impl = _Impl()
    with pytest.raises(NotImplementedError):
        _ = impl.commands
    with pytest.raises(NotImplementedError):
        impl.execute("start", None)
