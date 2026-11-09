"""
Probe the flood-4 docs carrier's #2449 (measured-zero heartbeat) and #2460 (replay clamp, paused fit) claims.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-07
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 docs carrier validation (claims lens, slice B); drafts juniper-ml#2449, #2460

Run with PYTHONPATH=<checkout>/juniper-service-core. ``--stats-only`` runs only the
statistics.quantiles single-point check (stdlib), for interpreters without the service deps.
Prints one ``CHECK <name>: <value>`` line per observation; asserts nothing, so every line is evidence.
"""

from __future__ import annotations

import logging
import statistics
import sys
import threading
import time


def out(name: str, value: object) -> None:
    print(f"CHECK {name}: {value!r}")


def stats_probe() -> None:
    out("python", sys.version.split()[0])
    try:
        out("quantiles_one_point", statistics.quantiles([0.5], n=20, method="inclusive"))
    except statistics.StatisticsError as exc:
        out("quantiles_one_point_raises", f"StatisticsError: {exc}")
    out("quantiles_two_zero_idx9_idx18", (lambda q: (q[9], q[18]))(statistics.quantiles([0.0, 0.0], n=20, method="inclusive")))


class _ListHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


def registry_probe() -> None:
    from unittest import mock

    import juniper_service_core.workers.registry as regmod
    from juniper_service_core.workers.coordinator import JsonTaskProtocol, WorkerCoordinator
    from juniper_service_core.workers.metrics import WorkerRegistryCollector

    # --- zero overwrite, None preserve, copy, health score
    reg = regmod.WorkerRegistration(worker_id="w")
    reg.record_heartbeat(in_flight_tasks=3, last_task_completed_at=123.0, rss_mb=200.0, tasks_completed=5, tasks_failed=4, last_task_duration_seconds=7.5, recent_task_durations_seconds=[1.0, 2.0], gpu_utilization_pct=88.0)
    out("health_5_4", reg.health_score)
    src: list[float] = []
    reg.record_heartbeat(in_flight_tasks=0, last_task_completed_at=0.0, rss_mb=0.0, tasks_completed=0, tasks_failed=0, last_task_duration_seconds=0.0, recent_task_durations_seconds=src, gpu_utilization_pct=0)
    out("after_zero", dict(in_flight=reg.in_flight_tasks, ltca=reg.last_task_completed_at, rss=reg.rss_mb, tc=reg.tasks_completed, tf=reg.tasks_failed, ltd=reg.last_task_duration_seconds, window=reg.recent_task_durations_seconds, gpu=reg.gpu_utilization_pct))
    out("window_is_copy", reg.recent_task_durations_seconds is not src)
    out("health_after_zero", reg.health_score)
    reg.record_heartbeat()
    out("after_none_tick", dict(in_flight=reg.in_flight_tasks, ltca=reg.last_task_completed_at, rss=reg.rss_mb, tc=reg.tasks_completed, tf=reg.tasks_failed, ltd=reg.last_task_duration_seconds, window=reg.recent_task_durations_seconds, gpu=reg.gpu_utilization_pct))
    reg.record_heartbeat(tasks_completed=0, tasks_failed=4)
    out("health_0_4", reg.health_score)

    # --- liveness at equality (time.time patched; the registry calls time.time())
    t0 = 1_000_000.0
    r = regmod.WorkerRegistry()
    out("default_heartbeat_timeout", r.heartbeat_timeout)
    r.register("w1", {})
    r.get("w1").last_heartbeat = t0
    with mock.patch.object(regmod.time, "time", return_value=t0 + 30.0):
        out("eq_is_alive", r.get("w1").is_alive(30.0))
        out("eq_available_worker_count", r.available_worker_count)
        out("eq_idle_ids", [w.worker_id for w in r.get_idle_workers()])
        out("eq_stale_ids", [w.worker_id for w in r.get_stale_workers()])
        out("eq_worker_count", r.worker_count)
    with mock.patch.object(regmod.time, "time", return_value=t0 + 30.0 - 1e-6):
        out("one_us_inside_is_alive", r.get("w1").is_alive(30.0))

    # --- get_next_assignment hands a task to a worker aged exactly one timeout; the sweep then removes it
    coord = WorkerCoordinator(r, JsonTaskProtocol())
    coord.submit_tasks("round-1", [{"x": 1}, {"x": 2}])
    with mock.patch.object(regmod.time, "time", return_value=t0 + 30.0):
        assignment = coord.get_next_assignment("w1")
        out("eq_get_next_assignment_assigned", assignment is not None)
        out("eq_active_task", r.get("w1").active_task_id is not None)
        coord._check_stale_workers()
        out("after_sweep_registered", r.get("w1") is not None)

    # --- collector
    handler = _ListHandler()
    mlog = logging.getLogger("juniper_service_core.workers.metrics")
    mlog.addHandler(handler)
    mlog.setLevel(logging.DEBUG)
    r2 = regmod.WorkerRegistry()
    now = 2_000_000.0
    a = r2.register("a", {})
    a.last_heartbeat = now + 100.0  # ahead of the scrape clock
    a.gpu_utilization_pct = 0
    a.recent_task_durations_seconds = [0.7]  # one sample
    b = r2.register("b", {})
    b.last_heartbeat = now - 5.0
    b.recent_task_durations_seconds = [0.0, 0.0]
    b.last_task_duration_seconds = 0.0

    def fams(collector: WorkerRegistryCollector) -> dict[str, list[tuple[dict, float]]]:
        res: dict[str, list[tuple[dict, float]]] = {}
        for fam in collector.collect():
            res[fam.name] = [(s.labels, s.value) for s in fam.samples]
        return res

    got = fams(WorkerRegistryCollector(r2, time_source=lambda: now))
    out("collector_families_no_source", sorted(got))
    out("collector_samples_no_source", got)
    out("collector_error_records_no_source", [rec.getMessage() for rec in handler.records])
    handler.records.clear()
    out("collector_pending_zero", fams(WorkerRegistryCollector(r2, time_source=lambda: now, pending_tasks_source=lambda: 0)).get("juniper_service_pending_tasks"))

    def boom() -> int:
        raise RuntimeError("source down")

    got_raise = fams(WorkerRegistryCollector(r2, time_source=lambda: now, pending_tasks_source=boom))
    out("collector_pending_raise_has_gauge", "juniper_service_pending_tasks" in got_raise)
    out("collector_pending_raise_logs", [(rec.levelname, rec.getMessage()) for rec in handler.records])
    mlog.removeHandler(handler)


def message_loop_probe() -> None:
    """Drive /ws/workers' _message_loop with a fake socket: the doc's zero tick, then a bare tick."""
    import asyncio
    import json

    from juniper_service_core.websocket import worker_stream
    from juniper_service_core.workers.coordinator import JsonTaskProtocol, WorkerCoordinator
    from juniper_service_core.workers.registry import WorkerRegistry

    class _Stop(Exception):
        pass

    frames = [
        {"text": json.dumps({"type": "heartbeat", "gpu_utilization_pct": 0, "last_task_duration_seconds": 0, "recent_task_durations_seconds": [], "in_flight_tasks": 0, "tasks_completed": 0, "tasks_failed": 0})},
        {"text": json.dumps({"type": "heartbeat"})},
        {"text": json.dumps({"type": "heartbeat", "gpu_utilization_pct": None})},
    ]
    sent: list = []

    class _WS:
        async def receive(self):
            if not frames:
                raise _Stop
            return frames.pop(0)

        async def send_json(self, msg):
            sent.append(msg)

        async def send_bytes(self, data):
            sent.append(("bytes", len(data)))

    registry = WorkerRegistry()
    reg = registry.register("w", {})
    reg.record_heartbeat(gpu_utilization_pct=77.0, last_task_duration_seconds=3.0, recent_task_durations_seconds=[1.0, 2.0], in_flight_tasks=2, tasks_completed=1, tasks_failed=4)
    coord = WorkerCoordinator(registry, JsonTaskProtocol())

    async def run() -> None:
        try:
            await worker_stream._message_loop(_WS(), "w", registry, coord)
        except _Stop:
            pass  # the fake socket ran out of frames: the loop has processed every tick

    asyncio.run(run())
    reg = registry.get("w")
    out("loop_after_three_ticks", dict(gpu=reg.gpu_utilization_pct, ltd=reg.last_task_duration_seconds, window=reg.recent_task_durations_seconds, in_flight=reg.in_flight_tasks, tc=reg.tasks_completed, tf=reg.tasks_failed, health=reg.health_score))
    out("loop_sent_types", [m.get("type") if isinstance(m, dict) else m for m in sent])


def replay_probe() -> None:
    from juniper_service_core.lifecycle.replay import MAX_TICK_SECONDS, ReplaySession
    from juniper_service_core.routes.models import ReplayControlRequest

    hist = [{"epoch": i, "metrics": {"mse": 1.0}} for i in range(10)]
    s = ReplaySession("s", hist)
    st = s.state()
    out("initial", (st["paused"], st["time_index"], st["speed"], st["range"]))
    out("speed_50", s.control("speed", value=50)["speed"])
    out("speed_-50", s.control("speed", value=-50)["speed"])
    out("speed_omitted_keeps", s.control("speed")["speed"])
    out("route_omitted_value_params", ReplayControlRequest(action="speed").model_dump(exclude_none=True, exclude={"action"}))
    out("MAX_TICK_SECONDS", MAX_TICK_SECONDS)
    out("sleep_table", {v: min(1.0 / abs(v), MAX_TICK_SECONDS) for v in (10.0, -10.0, 2.0, 1.0, 0.1, -0.1)})
    for v in (0.1, -0.1, 0.099, -0.099, 0.0):
        s2 = ReplaySession("s", hist)
        s2.control("seek", time_index=5)
        s2.control("speed", value=v)
        s2.control("play")
        adv = s2.step()
        st2 = s2.state()
        out(f"step_speed_{v}", (adv, st2["time_index"], st2["paused"]))
    s3 = ReplaySession("s", hist)
    s3.control("seek", time_index=2)
    st3 = s3.control("range", start=5, end=1)
    out("range_5_1_len10", (st3["range"], st3["time_index"]))
    for v in (1.0, -1.0):
        s3.control("speed", value=v)
        s3.control("play")
        adv = s3.step()
        out(f"collapsed_first_step_{v}", (adv, s3.state()["paused"], s3.state()["time_index"]))
    out("range_neg_start_big_end", ReplaySession("s", hist).control("range", start=-3, end=99)["range"])
    s4 = ReplaySession("s", hist)
    s4.control("range", start=1, end=4)
    out("seek_10_in_1_4", s4.control("seek", time_index=10)["time_index"])
    for n in (5, 4):
        out(f"range_5_1_len{n}", ReplaySession("s", hist[:n]).control("range", start=5, end=1)["range"])


def lifecycle_probe() -> None:
    import numpy as np
    from fastapi.testclient import TestClient
    from juniper_model_core.conformance.reference import ReferenceLinearModel, ReferenceLinearSerializer
    from juniper_model_core.events import TrainingEvent
    from juniper_model_core.interfaces import TrainableModel, TrainResult

    from juniper_service_core.app import create_app
    from juniper_service_core.lifecycle import LifecycleStateMachine, ServiceLifecycleManager
    from juniper_service_core.lifecycle.state_machine import LifecycleCommand
    from juniper_service_core.routes import build_routers

    class _GateModel(TrainableModel):
        """Emits training_start + phase_change(candidate), parks on a gate, then returns (or emits/raises)."""

        def __init__(self, after: str) -> None:
            self.task_type = "regression"
            self.random_seed = 0
            self.after = after
            self.at_gate = threading.Event()
            self.gate = threading.Event()
            self.fit_calls = 0

        def fit(self, X, y, *, X_val=None, y_val=None, on_event=None, **kw) -> TrainResult:
            self.fit_calls += 1
            on_event(TrainingEvent("training_start", {}, 0))
            on_event(TrainingEvent("phase_change", {"phase": "candidate"}, 0))
            self.at_gate.set()
            self.gate.wait(5.0)
            if self.after == "raise":
                raise RuntimeError("fit raised while paused")
            if self.after == "emit":
                on_event(TrainingEvent("epoch_end", {"epoch": 0, "metrics": {"mse": 1.0}}, 0))
            return TrainResult(final_metrics={"mse": 0.1}, n_epochs=1)

        def predict(self, X, **kw):
            return np.zeros((X.shape[0], 1))

        def metrics(self):
            return {"mse": 0.1}

        def describe_topology(self):
            return {"model_type": "gate", "nodes": [], "edges": [], "meta": {"n_units": 0, "task_type": "regression"}}

        @property
        def input_shape(self):
            return (1,)

        @property
        def output_shape(self):
            return (1,)

    X = np.zeros((4, 1), np.float32)
    y = np.zeros((4, 1), np.float32)

    def pick(status: dict) -> dict:
        return dict(sm=status["state_machine"], mon=(status["monitor"]["status"], status["monitor"]["phase"]), active=status["training_active"])

    # fit returns while PAUSED
    m = _GateModel("return")
    mgr = ServiceLifecycleManager(m)
    mgr.start_training(X, y)
    m.at_gate.wait(5.0)
    out("pause_from_started", pick(mgr.pause_training()))
    m.gate.set()
    out("thread_joined", mgr.join(timeout=5.0))
    out("status_after_fit_returned_paused", pick(mgr.get_status()))
    out("thread_alive", mgr._thread.is_alive())
    out("resume_after", pick(mgr.resume_training()))
    time.sleep(0.2)
    out("after_resume_thread_alive_fit_calls", (mgr._thread.is_alive(), m.fit_calls))
    out("after_resume_start_training_refused", _try(lambda: mgr.start_training(X, y)))
    time.sleep(0.2)
    out("after_resume_still_active_later", pick(mgr.get_status()))
    out("recover_stop", pick(mgr.stop_training()))
    out("recover_start_again", _try(lambda: mgr.start_training(X, y)))
    out("recover_join", mgr.join(timeout=5.0))
    out("recover_status", (pick(mgr.get_status()), m.fit_calls))
    mgr.shutdown()

    # a model that emits another event stays parked in _pause_event.wait()
    m2 = _GateModel("emit")
    mgr2 = ServiceLifecycleManager(m2)
    mgr2.start_training(X, y)
    m2.at_gate.wait(5.0)
    mgr2.pause_training()
    m2.gate.set()
    time.sleep(0.3)
    out("emit_after_pause_thread_parked", mgr2._thread.is_alive())
    mgr2.resume_training()
    out("emit_after_resume_joined", mgr2.join(timeout=5.0))
    out("emit_after_resume_status", pick(mgr2.get_status()))
    mgr2.shutdown()

    # fit raises while PAUSED
    m3 = _GateModel("raise")
    mgr3 = ServiceLifecycleManager(m3)
    logging.getLogger("juniper_service_core.lifecycle.manager").setLevel(logging.CRITICAL)
    mgr3.start_training(X, y)
    m3.at_gate.wait(5.0)
    mgr3.pause_training()
    m3.gate.set()
    mgr3.join(timeout=5.0)
    out("raise_while_paused_status", pick(mgr3.get_status()))
    mgr3.shutdown()

    # state-machine arms from the three snapshot states
    for enter in ("mark_replaying", "mark_investigating", "mark_resume_ready"):
        sm = LifecycleStateMachine()
        getattr(sm, enter)()
        out(f"sm_{enter}", (sm.handle_command(LifecycleCommand.PAUSE), sm.mark_completed(), sm.mark_failed("x"), sm.status.name))

    # HTTP: replay control codes, pause 409 in REPLAYING / INVESTIGATING / RESUME_READY
    import tempfile
    from pathlib import Path

    base = Path(__file__).resolve().parents[2] / "tmp"
    with tempfile.TemporaryDirectory(dir=base) as tdir:
        lin = ReferenceLinearModel()
        man = ServiceLifecycleManager(lin, serializer=ReferenceLinearSerializer(), snapshot_dir=tdir)
        app = create_app(routers=build_routers())
        app.state.lifecycle = man
        rng = np.random.default_rng(0)
        Xr = rng.normal(size=(16, 2)).astype(np.float32)
        yr = (Xr @ np.array([[1.0], [2.0]], np.float32)).astype(np.float32)
        man.start_training(Xr, yr)
        man.join(timeout=5.0)
        with TestClient(app) as client:
            sid = client.post("/v1/snapshots", json={"description": "p"}).json()["data"]["id"]
            out("ctl_no_session_unknown_action", client.post(f"/v1/snapshots/{sid}/replay/control", json={"action": "frobnicate"}).status_code)
            out("ctl_no_session_status", client.post(f"/v1/snapshots/{sid}/replay/control", json={"action": "status"}).status_code)
            out("start_replay", client.post(f"/v1/snapshots/{sid}/replay").status_code)
            r = client.post(f"/v1/snapshots/{sid}/replay/control", json={"action": "speed", "value": 50}).json()
            out("ctl_speed_50_body_keys", (sorted(r), sorted(r["data"])[:8], r["data"]["replay"]["speed"]))
            out("ctl_unknown_action_with_session", client.post(f"/v1/snapshots/{sid}/replay/control", json={"action": "frobnicate"}).status_code)
            p = client.post("/v1/training/pause")
            out("pause_during_replay", (p.status_code, p.json().get("detail")))
            out("ctl_pause_keeps_replaying", client.post(f"/v1/snapshots/{sid}/replay/control", json={"action": "pause"}).json()["data"]["state_machine"]["status"])
            stop = client.post(f"/v1/snapshots/{sid}/replay/control", json={"action": "stop"}).json()["data"]
            out("ctl_stop", (stop["state_machine"]["status"], stop["monitor"]["status"], stop["replay"]["stopped"]))
            out("ctl_after_stop", client.post(f"/v1/snapshots/{sid}/replay/control", json={"action": "play"}).status_code)
            client.post(f"/v1/snapshots/{sid}/restore")
            p = client.post("/v1/training/pause")
            out("pause_investigating", (p.status_code, p.json().get("detail")))
            client.post(f"/v1/snapshots/{sid}/resume")
            p = client.post("/v1/training/pause")
            out("pause_resume_ready", (p.status_code, p.json().get("detail")))
        man.shutdown()
        man2 = ServiceLifecycleManager(ReferenceLinearModel())
        app2 = create_app(routers=build_routers())
        app2.state.lifecycle = man2
        with TestClient(app2) as client2:
            out("ctl_disabled", client2.post("/v1/snapshots/x/replay/control", json={"action": "status"}).status_code)


def _try(fn) -> str:
    try:
        fn()
        return "ok"
    except Exception as exc:  # noqa: BLE001 - probe records the refusal text
        return f"{type(exc).__name__}: {exc}"


def main() -> int:
    stats_probe()
    if "--stats-only" in sys.argv:
        return 0
    registry_probe()
    message_loop_probe()
    replay_probe()
    lifecycle_probe()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
