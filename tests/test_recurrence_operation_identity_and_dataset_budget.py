#!/usr/bin/env python3
"""W1.5, driver half: the dataset-create budget and operation identity on the recurrence path.

Plan of record: ``notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md``
(W1.5; findings F-D5, F-S6, F-S9, F-CON1, F-CON2). The service half is juniper-recurrence#192.

What this module pins, against one loopback stub that plays both juniper-data and juniper-recurrence:

* **Two separate budgets.** ``POST /v1/datasets`` is bounded by ``dataset_create_timeout_seconds``
  (CLI > YAML ``outputs`` > 120 s) and train / predict / crossval by the wall budget, each
  independent of the other. A dataset budget that expires is ``timed_out`` (exit 1) naming the knob,
  on both paths, instead of the "service unreachable" exit 3 a ``RequestTimeout`` used to become.
* **The acceptance case.** A juniper-data that sleeps 40 s per call no longer fails inside
  recurrence. The service's inner fetch is modelled on juniper-recurrence#192's contract: it
  downloads the artifact through a client whose timeout is ``JUNIPER_RECURRENCE_JUNIPER_DATA_TIMEOUT_SECONDS``
  and answers ``502 juniper-data unreachable: ...`` when that runs out (``routers/_common.py``
  ``map_data_error``). With the client's old 30 s default the run fails inside the service while the
  driver's own budgets are untouched (F-D5 / F-S9 as audited). With the budget ``run_suite`` exports
  -- the driver's dataset budget -- the same run succeeds.
* **Operation identity.** ``POST /v1/train`` sends ``X-Request-ID``; the ``operation_id`` it returns
  rides back on predict as ``expect_operation_id`` (never on crossval, which does not use the
  in-memory model); a model another caller replaced is refused and the run is ``degraded``; a service
  that returns no usable ``operation_id`` (juniper-recurrence 0.5.0) is never sent the key; the
  manifest's ``operation`` block records all of it, including that a timed-out fit is not cancelled.

**Time is scaled 1:100** so a real 40 s sleep is not needed: the 40 s data server sleeps 0.4 s, the
client's old 30 s default is 0.3 s and the driver's 120 s default budget is 1.2 s. Only ordering
matters to the code under test -- each socket timeout either expires before the reply or not -- so
the scaling preserves every outcome. The expiring arms cannot flake (a reply can only arrive later
than its sleep, never earlier); the succeeding arms keep at least 0.8 s of slack.

No live services. ``util/`` is not pre-commit-lint-gated, so this unittest is the gate.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import run_experiment as rx  # noqa: E402  (path-invoked util import)
from experiments import run_suite  # noqa: E402

FAST_FLAGS = ["--poll-interval", "0.05", "--stall-seconds", "5", "--health-timeout", "2"]

#: 1:100 -- see the module docstring. Rounded so each constant is the decimal it reads as.
SCALE = 0.01
FORTY_SECOND_DATA_SERVER = round(40.0 * SCALE, 6)  # 0.4
OLD_CLIENT_DEFAULT = round(30.0 * SCALE, 6)  # 0.3: juniper-data-client's default before juniper-recurrence#192
DRIVER_DEFAULT_BUDGET = round(rx.DEFAULT_DATASET_CREATE_TIMEOUT_SECONDS * SCALE, 6)  # 1.2

OUR_OPERATION = "a" * 32
OTHER_OPERATION = "b" * 32
REQUEST_ID_RE = re.compile(r"run_experiment:[A-Za-z0-9._-]+:[0-9a-f]{12}")


class _State:
    """What the stub answers, and what it saw."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.requests: list[dict[str, Any]] = []
        self.create_delay = 0.0
        self.artifact_delay = 0.0
        self.train_delay = 0.0
        # None: the train response carries no operation_id key at all (juniper-recurrence 0.5.0).
        # Anything else is sent as-is, including shapes the driver must refuse to echo.
        self.operation_id: Any = OUR_OPERATION
        self.send_operation_id = True
        # When set, another caller's fit replaces the model right after ours (F-CON1).
        self.model_after_train: "str | None" = None
        self.model_operation_id: "str | None" = None
        self.train_busy = False
        # When set, /v1/train downloads the artifact first with this client timeout, as the service does.
        self.inner_timeout: "float | None" = None


class _Handler(BaseHTTPRequestHandler):
    server: "_Server"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003 - http.server API
        return

    def _send(self, code: int, payload: Any, content_type: str = "application/json") -> None:
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _body(self) -> "dict | None":
        length = int(self.headers.get("Content-Length") or 0)
        if not length:
            return None
        try:
            return json.loads(self.rfile.read(length).decode("utf-8"))
        except ValueError:
            return None

    def _record(self, method: str, body: "dict | None") -> None:
        state = self.server.state
        with state.lock:
            state.requests.append({"method": method, "path": self.path.split("?", 1)[0], "request_id": self.headers.get("X-Request-ID"), "body": body})

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        state = self.server.state
        path = self.path.split("?", 1)[0]
        self._record("GET", None)
        if path in ("/v1/health", "/v1/health/ready"):
            self._send(200, {"status": "ok"})
        elif path == "/v1/generators":
            self._send(200, [{"name": name, "version": "3.0.0", "available": True, "schema": {}} for name in ("irregular_sine", "spiral")])
        elif path.startswith("/v1/datasets/") and path.endswith("/artifact"):
            time.sleep(state.artifact_delay)
            self._send(200, b"NPZ-stand-in", content_type="application/octet-stream")
        else:
            self._send(404, {"detail": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - http.server API
        state = self.server.state
        path = self.path.split("?", 1)[0]
        body = self._body()
        self._record("POST", body)
        if path == "/v1/datasets":
            time.sleep(state.create_delay)
            meta = {"dataset_id": "ds-w15", "generator": (body or {}).get("generator"), "generator_version": "3.0.0", "n_train": 8, "n_val": 2, "n_test": 2}
            self._send(201, {"dataset_id": "ds-w15", "generator": (body or {}).get("generator"), "meta": meta, "artifact_url": "/v1/datasets/ds-w15/artifact"})
        elif path == "/v1/train":
            self._train(state)
        elif path == "/v1/predict":
            expected = (body or {}).get("expect_operation_id")
            if expected is not None and expected != state.model_operation_id:
                # juniper-recurrence#192 OperationMismatchDetail, message verbatim from require_expected_operation.
                message = f"expect_operation_id {expected} does not match the operation that produced the in-memory model ({state.model_operation_id}); another caller may have trained or restored since"
                self._send(409, {"detail": {"message": message, "expected_operation_id": expected, "model_operation_id": state.model_operation_id}})
            else:
                self._send(200, {"predictions": [[0.1], [0.2]], "shape": [2, 1]})
        elif path == "/v1/crossval":
            self._send(200, {"task_type": "regression", "n_folds": 2, "folds": [{"fold": 0, "eval_metrics": {"r2": 0.1}}], "eval_aggregate": {"r2": 0.1}, "eval_std": {"r2": 0.0}})
        else:
            self._send(404, {"detail": "not found"})

    def _train(self, state: _State) -> None:
        if state.train_busy:
            # juniper-recurrence#192 BusyDetail.
            self._send(409, {"detail": {"message": "a training run is already in progress", "operation_id": OTHER_OPERATION, "operation": "train", "busy_since": "2026-10-08T17:00:00.000Z", "requested_by": "canopy:start-7", "dataset_id": "ds-other"}})
            return
        if state.inner_timeout is not None:
            # The service's own data fetch (load_sequence_data with a dataset_id ref is an artifact
            # download), through a client whose timeout is the service's setting.
            try:
                with urllib.request.urlopen(f"{self.server.base_url}/v1/datasets/ds-w15/artifact", timeout=state.inner_timeout) as resp:  # nosec B310 - loopback stub
                    resp.read()
            except OSError as exc:  # a socket timeout and urllib's URLError are both OSErrors
                self._send(502, {"detail": f"juniper-data unreachable: {exc}"})
                return
        time.sleep(state.train_delay)
        state.model_operation_id = state.model_after_train or (state.operation_id if isinstance(state.operation_id, str) else "internal-id")
        payload: dict[str, Any] = {"final_metrics": {"r2": 0.5}, "metrics_scope": "in_sample", "n_epochs": 1, "stopped_reason": "converged", "dataset": {"dataset_id": "ds-w15", "split": "train", "n_windows": 8}}
        if state.send_operation_id:
            payload["operation_id"] = state.operation_id
        self._send(200, payload)


class _Server(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _Handler)
        self.state = _State()

    def handle_error(self, request, client_address) -> None:  # noqa: D102 - an expired client leaves a broken pipe behind
        return

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server_address[1]}"


def _recurrence_config(*, budget: "float | None" = None, max_wall: float = 30.0, predict: bool = True, crossval: bool = True) -> dict:
    outputs: dict[str, Any] = {"plots": [], "max_wall_seconds": max_wall}
    if budget is not None:
        outputs["dataset_create_timeout_seconds"] = budget
    cfg: dict[str, Any] = {
        "schema_version": 1,
        "experiment": {"name": "w15-driver", "description": "W1.5 driver half stub run", "seed": 515},
        "dataset": {"generator": "irregular_sine", "split": "train", "params": {"n_steps": 200, "lookback": 16}},
        "train": {"d": 4, "ridge": 1.0, "readout": "linear"},
        "outputs": outputs,
    }
    if predict:
        cfg["predict"] = {"enabled": True, "from_dataset_split": "test"}
    if crossval:
        cfg["crossval"] = {"enabled": True, "n_folds": 2, "scheme": "expanding", "embargo": 1}
    return cfg


def _cascor_config(*, budget: "float | None" = None) -> dict:
    outputs: dict[str, Any] = {"plots": [], "max_wall_seconds": 30.0}
    if budget is not None:
        outputs["dataset_create_timeout_seconds"] = budget
    return {"schema_version": 1, "experiment": {"name": "w15-cascor", "seed": 516}, "dataset": {"generator": "spiral", "params": {"n_spirals": 2}}, "training": {"params": {"max_iterations": 2}}, "outputs": outputs}


class _Case(unittest.TestCase):
    RUN_ID = "20261008T170000Z-w15d"

    def setUp(self) -> None:
        self.server = _Server()
        thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.tmp = Path(tempfile.mkdtemp(prefix="w15-driver-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.run_dir = self.tmp / self.RUN_ID
        self.run_dir.mkdir()
        port = urlparse(self.server.base_url).port
        (self.run_dir / "ports.json").write_text(json.dumps({"run_id": self.RUN_ID, "data": port, "cascor": port, "recurrence": port, "data_url": self.server.base_url, "experiment": "w15", "grafana_bridge": False}), encoding="utf-8")

    @property
    def state(self) -> _State:
        return self.server.state

    def _run(self, cfg: dict, *extra: str) -> "tuple[int, dict]":
        config = self.tmp / "experiment-in.yaml"
        config.write_text(yaml.safe_dump(cfg, sort_keys=False), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            code = rx.main(["--config", str(config), "--run-dir", str(self.run_dir), "--ecosystem-root", str(self.tmp), *FAST_FLAGS, *extra])
        return code, json.loads((self.run_dir / "manifest.json").read_text(encoding="utf-8"))

    def _calls(self, method: str, path: str) -> "list[dict[str, Any]]":
        return [req for req in self.state.requests if req["method"] == method and req["path"] == path]


class DatasetBudgetResolutionTest(unittest.TestCase):
    """CLI > YAML ``outputs.dataset_create_timeout_seconds`` > 120 s, validated on both routes."""

    def _load(self, outputs: dict) -> dict:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cfg.yaml"
            cfg = _recurrence_config()
            cfg["outputs"] = {"plots": [], **outputs}
            path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
            return rx.load_config(path)

    def test_the_default_is_the_value_creation_always_had(self) -> None:
        self.assertEqual(rx.DEFAULT_DATASET_CREATE_TIMEOUT_SECONDS, 120.0)
        config = self._load({})
        self.assertEqual(config["outputs"]["dataset_create_timeout_seconds"], 120.0)
        self.assertEqual(rx._dataset_create_timeout(rx.build_parser().parse_args(["--config", "c", "--run-dir", "r"]), config), 120.0)

    def test_yaml_beats_the_default_and_the_flag_beats_yaml(self) -> None:
        config = self._load({"dataset_create_timeout_seconds": 600})
        self.assertEqual(config["outputs"]["dataset_create_timeout_seconds"], 600.0)
        parser = rx.build_parser()
        self.assertEqual(rx._dataset_create_timeout(parser.parse_args(["--config", "c", "--run-dir", "r"]), config), 600.0)
        self.assertEqual(rx._dataset_create_timeout(parser.parse_args(["--config", "c", "--run-dir", "r", "--dataset-create-timeout-seconds", "45.5"]), config), 45.5)

    def test_the_two_budgets_do_not_feed_each_other(self) -> None:
        config = self._load({"max_wall_seconds": 7, "dataset_create_timeout_seconds": 900})
        self.assertEqual((config["outputs"]["max_wall_seconds"], config["outputs"]["dataset_create_timeout_seconds"]), (7.0, 900.0))
        args = rx.build_parser().parse_args(["--config", "c", "--run-dir", "r", "--max-wall-seconds", "3"])
        self.assertEqual(rx._dataset_create_timeout(args, config), 900.0, "the wall flag must not move the dataset budget")

    def test_a_bad_yaml_budget_is_a_config_error(self) -> None:
        for bad in (0, -1, True, "120", float("inf"), float("nan"), None, [5]):
            with self.subTest(bad=bad), self.assertRaisesRegex(rx.ConfigError, "dataset_create_timeout_seconds must be a positive, finite number"):
                self._load({"dataset_create_timeout_seconds": bad})

    def test_a_bad_flag_is_a_usage_error(self) -> None:
        # The usage message is asserted, not just the exit code: a missing config is exit 2 too, so
        # the code alone cannot tell the flag's own validation from the run failing later.
        for bad in ("0", "-3", "nan", "inf", "abc", ""):
            with self.subTest(bad=bad):
                stderr = io.StringIO()
                with contextlib.redirect_stderr(stderr):
                    code = rx.main(["--config", "c", "--run-dir", "r", "--dataset-create-timeout-seconds", bad])
                self.assertEqual(code, rx.EXIT_MISUSE)
                self.assertIn("argument --dataset-create-timeout-seconds", stderr.getvalue())
                self.assertRegex(stderr.getvalue(), r"must be a positive, finite number of seconds|not a number of seconds")

    def test_the_key_is_allowed_only_under_outputs(self) -> None:
        self.assertIn("dataset_create_timeout_seconds", rx.OUTPUTS_KEYS)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "cfg.yaml"
            cfg = _recurrence_config()
            cfg["dataset"]["dataset_create_timeout_seconds"] = 600
            path.write_text(yaml.safe_dump(cfg), encoding="utf-8")
            with self.assertRaisesRegex(rx.ConfigError, "unknown key"):
                rx.load_config(path)


class DatasetBudgetDriveTest(_Case):
    """Each budget bounds its own calls, and an expired dataset budget is ``timed_out``."""

    def test_creation_waits_out_a_slow_data_server_inside_its_budget_whatever_the_wall_budget(self) -> None:
        self.state.create_delay = FORTY_SECOND_DATA_SERVER
        code, manifest = self._run(_recurrence_config(budget=DRIVER_DEFAULT_BUDGET), "--max-wall-seconds", "0.3")
        self.assertEqual(code, rx.EXIT_SUCCESS, manifest["acceptance"])
        self.assertEqual(manifest["outcome"], "succeeded")
        self.assertGreaterEqual(manifest["timings"]["dataset_create"], FORTY_SECOND_DATA_SERVER)
        self.assertEqual(manifest["driver"]["dataset_create_timeout_seconds"], DRIVER_DEFAULT_BUDGET)
        self.assertEqual(manifest["driver"]["max_wall_seconds"], 0.3, "a 0.3 s wall budget would have cut a 0.4 s create")

    def test_an_expired_dataset_budget_is_timed_out_and_names_the_knob(self) -> None:
        self.state.create_delay = 3 * FORTY_SECOND_DATA_SERVER
        code, manifest = self._run(_recurrence_config(budget=600), "--dataset-create-timeout-seconds", "0.2")
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        self.assertEqual(manifest["outcome"], "timed_out")
        reasons = " ".join(manifest["acceptance"]["reasons"])
        self.assertIn("outputs.dataset_create_timeout_seconds", reasons)
        self.assertIn("--dataset-create-timeout-seconds", reasons)
        self.assertIn("0.2s dataset-create budget", reasons, "the flag beat the YAML's 600")
        self.assertNotIn("unreachable", reasons)
        self.assertEqual(manifest["phases"]["train"], {"status": "not_reached"})
        self.assertEqual(self._calls("POST", "/v1/train"), [], "nothing trains on a dataset that never arrived")
        self.assertEqual(manifest["driver"]["dataset_create_timeout_seconds"], 0.2)
        self.assertGreaterEqual(manifest["timings"]["dataset_create"], 0.2)

    def test_train_is_bounded_by_the_wall_budget_not_the_dataset_budget(self) -> None:
        self.state.train_delay = FORTY_SECOND_DATA_SERVER
        code, manifest = self._run(_recurrence_config(budget=0.2, max_wall=DRIVER_DEFAULT_BUDGET))
        self.assertEqual(code, rx.EXIT_SUCCESS, manifest["acceptance"])
        self.assertEqual(manifest["phases"]["train"], {"status": "ok"})

    def test_the_cascor_path_shares_the_budget_and_the_classification(self) -> None:
        self.state.create_delay = 3 * FORTY_SECOND_DATA_SERVER
        code, manifest = self._run(_cascor_config(budget=0.2))
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        self.assertEqual(manifest["outcome"], "timed_out")
        self.assertIn("0.2s dataset-create budget", " ".join(manifest["acceptance"]["reasons"]))
        self.assertEqual(manifest["driver"]["dataset_create_timeout_seconds"], 0.2)
        self.assertEqual(self._calls("POST", "/v1/training/dataset"), [], "nothing is staged after a timed-out create")

    def test_create_dataset_raises_the_named_timeout(self) -> None:
        self.state.create_delay = 3 * FORTY_SECOND_DATA_SERVER
        with self.assertRaises(rx.DatasetCreateTimeout) as caught:
            rx.create_dataset(self.server.base_url, {"generator": "irregular_sine", "params": {}, "persist": True, "tags": []}, timeout=0.2)
        self.assertIsInstance(caught.exception, rx.RequestTimeout, "still a timeout to any handler that does not know the subclass")
        self.assertIn("irregular_sine", str(caught.exception))


class FortySecondDataServerTest(_Case):
    """The plan's acceptance case: a juniper-data that sleeps 40 s no longer fails inside recurrence.

    Both arms run the same slow data server (create and artifact download each take "40 s") under
    the same driver budgets; only the service's inner budget differs. Scaled 1:100.
    """

    def setUp(self) -> None:
        super().setUp()
        self.state.create_delay = FORTY_SECOND_DATA_SERVER
        self.state.artifact_delay = FORTY_SECOND_DATA_SERVER
        self.cfg = _recurrence_config(budget=DRIVER_DEFAULT_BUDGET)

    def test_with_the_old_30_second_client_default_it_fails_inside_recurrence(self) -> None:
        # F-S9: the client's 30 s default, which no setting reached before juniper-recurrence#192.
        self.state.inner_timeout = OLD_CLIENT_DEFAULT
        code, manifest = self._run(self.cfg)
        self.assertEqual(code, rx.EXIT_RUN_FAILED)
        self.assertEqual(manifest["outcome"], "failed")
        self.assertTrue(manifest["phases"]["train"]["error"].startswith("HTTP 502: juniper-data unreachable"), manifest["phases"]["train"])
        # F-D5's shape: every outer timer was still green when the inner one fired.
        self.assertGreaterEqual(manifest["timings"]["dataset_create"], FORTY_SECOND_DATA_SERVER)
        self.assertLess(manifest["timings"]["train"], manifest["driver"]["max_wall_seconds"])

    def test_with_the_budget_run_suite_exports_it_succeeds(self) -> None:
        env = run_suite.recurrence_data_timeout_env("recurrence", self.cfg, None)
        self.assertEqual(env, {run_suite.RECURRENCE_DATA_TIMEOUT_ENV: "1.2"})
        self.state.inner_timeout = float(env[run_suite.RECURRENCE_DATA_TIMEOUT_ENV])
        self.assertGreater(self.state.inner_timeout, FORTY_SECOND_DATA_SERVER)
        code, manifest = self._run(self.cfg)
        self.assertEqual(code, rx.EXIT_SUCCESS, manifest["acceptance"])
        self.assertEqual(manifest["outcome"], "succeeded")
        self.assertEqual(manifest["phases"]["train"], {"status": "ok"})


class OperationIdentityTest(_Case):
    """``X-Request-ID`` out, ``operation_id`` back, ``expect_operation_id`` on predict only."""

    def test_the_train_id_rides_back_on_predict_and_nowhere_else(self) -> None:
        code, manifest = self._run(_recurrence_config())
        self.assertEqual(code, rx.EXIT_SUCCESS, manifest["acceptance"])
        (train,) = self._calls("POST", "/v1/train")
        self.assertRegex(train["request_id"], REQUEST_ID_RE)
        self.assertIn(f":{self.RUN_ID}:", train["request_id"])
        (predict,) = self._calls("POST", "/v1/predict")
        self.assertEqual(predict["body"]["expect_operation_id"], OUR_OPERATION)
        self.assertEqual(predict["body"]["dataset"], {"dataset_id": "ds-w15", "split": "test"})
        (crossval,) = self._calls("POST", "/v1/crossval")
        self.assertNotIn("expect_operation_id", crossval["body"], "crossval fits its own folds and never reads the model")
        self.assertIsNone(predict["request_id"], "X-Request-ID belongs to the lock-taking train only")
        self.assertEqual(manifest["operation"], {"request_id": train["request_id"], "operation_id": OUR_OPERATION, "expect_operation_id_sent": True, "note": None})
        self.assertEqual(manifest["outcome"], "succeeded")

    def test_a_service_that_returns_no_operation_id_is_tolerated(self) -> None:
        # juniper-recurrence 0.5.0, the published release: no operation_id key at all.
        self.state.send_operation_id = False
        with self.assertLogs(rx.log, level="WARNING") as logs:
            code, manifest = self._run(_recurrence_config())
        self.assertEqual(code, rx.EXIT_SUCCESS, manifest["acceptance"])
        self.assertEqual(manifest["outcome"], "succeeded")
        (predict,) = self._calls("POST", "/v1/predict")
        self.assertNotIn("expect_operation_id", predict["body"])
        operation = manifest["operation"]
        self.assertIsNone(operation["operation_id"])
        self.assertIs(operation["expect_operation_id_sent"], False)
        self.assertIn("0.5.0", operation["note"])
        self.assertRegex(operation["request_id"], REQUEST_ID_RE, "the header is still sent; an older service ignores it")
        self.assertTrue(any("no usable operation_id" in line for line in logs.output))

    def test_an_unusable_operation_id_is_never_echoed(self) -> None:
        for value in ("", "   ", 123, None, ["x"], {"id": OUR_OPERATION}):
            with self.subTest(value=value):
                self.state.requests.clear()
                self.state.operation_id = value
                code, manifest = self._run(_recurrence_config(crossval=False))
                self.assertEqual(code, rx.EXIT_SUCCESS, manifest["acceptance"])
                (predict,) = self._calls("POST", "/v1/predict")
                self.assertNotIn("expect_operation_id", predict["body"], "an empty id is a 422 (min_length=1); a coerced one names nothing")
                self.assertIsNone(manifest["operation"]["operation_id"])

    def test_a_model_another_caller_replaced_is_refused_not_scored(self) -> None:
        self.state.model_after_train = OTHER_OPERATION
        code, manifest = self._run(_recurrence_config())
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        self.assertEqual(manifest["outcome"], "degraded")
        error = manifest["phases"]["predict"]["error"]
        self.assertTrue(error.startswith("HTTP 409: "), error)
        self.assertIn(OUR_OPERATION, error)
        self.assertIn(OTHER_OPERATION, error)
        self.assertEqual(manifest["phases"]["crossval"], {"status": "ok"}, "crossval still runs: it never reads the model")
        self.assertIn("no longer this run's", manifest["operation"]["note"])
        self.assertFalse((self.run_dir / "artifacts" / "results" / "predict_response.json").exists())
        self.assertIsNone(manifest["predict"])

    def test_a_timed_out_train_records_that_the_fit_was_not_cancelled(self) -> None:
        self.state.train_delay = 3 * FORTY_SECOND_DATA_SERVER
        code, manifest = self._run(_recurrence_config(), "--max-wall-seconds", "0.2")
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        self.assertEqual(manifest["outcome"], "timed_out")
        (train,) = self._calls("POST", "/v1/train")
        operation = manifest["operation"]
        self.assertEqual(operation["request_id"], train["request_id"], "the id to look the fit up by in GET /v1/training/status")
        self.assertIsNone(operation["operation_id"], "the response never arrived")
        self.assertIsNone(operation["expect_operation_id_sent"])
        self.assertIn("does not cancel the fit", operation["note"])
        self.assertIn("train_lock", operation["note"])

    def test_a_busy_service_names_its_holder(self) -> None:
        self.state.train_busy = True
        code, manifest = self._run(_recurrence_config())
        self.assertEqual(code, rx.EXIT_RUN_FAILED)
        self.assertEqual(manifest["outcome"], "failed")
        error = manifest["phases"]["train"]["error"]
        self.assertTrue(error.startswith("HTTP 409: "), error)
        for fact in (OTHER_OPERATION, "2026-10-08T17:00:00.000Z", "canopy:start-7"):
            self.assertIn(fact, error)
        self.assertIn("another operation holds the service's train_lock", manifest["operation"]["note"])
        self.assertEqual(manifest["phases"]["predict"], {"status": "not_reached"})

    def test_with_predict_disabled_nothing_is_expected(self) -> None:
        code, manifest = self._run(_recurrence_config(predict=False))
        self.assertEqual(code, rx.EXIT_SUCCESS, manifest["acceptance"])
        self.assertEqual(manifest["operation"]["operation_id"], OUR_OPERATION)
        self.assertIsNone(manifest["operation"]["expect_operation_id_sent"])
        self.assertEqual(self._calls("POST", "/v1/predict"), [])


class RequestIdShapeTest(unittest.TestCase):
    """The ``X-Request-ID`` value: safe as a header, distinct per call, still naming the run."""

    def test_unsafe_run_id_characters_are_replaced(self) -> None:
        value = rx._train_request_id("run id\r\nX-Injected: 1é")
        self.assertRegex(value, r"\Arun_experiment:[A-Za-z0-9._-]+:[0-9a-f]{12}\Z")
        self.assertIn("run_id__X-Injected__1_", value)

    def test_the_run_id_is_capped_and_an_empty_one_still_names_something(self) -> None:
        self.assertEqual(len(rx._train_request_id("x" * 500).split(":")[1]), 96)
        self.assertTrue(rx._train_request_id("").startswith("run_experiment:run:"))

    def test_two_calls_never_share_an_id(self) -> None:
        self.assertNotEqual(rx._train_request_id("r"), rx._train_request_id("r"))

    def test_the_header_reaches_the_wire(self) -> None:
        seen: list = []

        class _Echo(BaseHTTPRequestHandler):
            def log_message(self, fmt: str, *args) -> None:  # noqa: A003 - http.server API
                return

            def do_POST(self) -> None:  # noqa: N802 - http.server API
                seen.append(self.headers.get(rx.REQUEST_ID_HEADER))
                self.send_response(200)
                self.send_header("Content-Length", "2")
                self.end_headers()
                self.wfile.write(b"{}")

        server = ThreadingHTTPServer(("127.0.0.1", 0), _Echo)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            rx._http_json("POST", f"http://127.0.0.1:{server.server_address[1]}/v1/train", body={}, headers={rx.REQUEST_ID_HEADER: "run_experiment:r:0123456789ab"})
        finally:
            server.shutdown()
            server.server_close()
        self.assertEqual(seen, ["run_experiment:r:0123456789ab"])


if __name__ == "__main__":
    unittest.main()
