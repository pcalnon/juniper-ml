#!/usr/bin/env python3
"""W0.3 / W0.4 edges the producer suites and the phase-record suite do not reach.

``tests/test_run_experiment.py`` times out ``POST /v1/train`` (outcome ``timed_out``) and
fails an aux phase with an HTTP status. A wall-clock timeout on ``/v1/crossval`` is a
different exception: ``RequestTimeout`` subclasses ``ServiceUnreachable``, and the train
handler turns that subclass into ``timed_out`` and does not continue. The aux handler
must keep it ``degraded``, exit 1, and still run ``save_model``.

Those suites also answer every 200 with an object. A list or JSON null must not raise
before ``derive_recurrence_outcome`` — that raise would leave the initial
``torn_down_early`` on a run whose phases actually succeeded.

``tests/test_run_suite.py`` and ``tests/test_recurrence_degraded_phase_edges.py`` do not
force a ``degraded`` outcome with an empty acceptance-reason list, so a regression that
keys the exit code on the reasons alone stays green. They also do not separate the
headline columns: a bad ``train_r2`` must not drop ``cv_r2``, and a missing ``eval_std``
must not raise.

No live stack. ``util/`` is not pre-commit-lint-gated, so this unittest is the gate.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import unittest
import unittest.mock as mock
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import run_experiment as rx  # noqa: E402
from experiments import run_suite  # noqa: E402

_UNSET = object()
FAST_FLAGS = ["--poll-interval", "0.05", "--stall-seconds", "5", "--health-timeout", "2"]
# Longer than --max-wall-seconds 0.2, short enough that a daemon handler does not linger.
_HANG_SECONDS = 1.0


def _recurrence_config(*, save_model: bool = False) -> dict:
    outputs: dict[str, Any] = {"plots": [], "max_wall_seconds": 30}
    if save_model:
        outputs["save_model"] = True
    return {
        "schema_version": 1,
        "experiment": {"name": "rec-aux-edge", "description": "aux-timeout stub", "seed": 777},
        "dataset": {"generator": "irregular_sine", "split": "train", "params": {"n_steps": 500, "lookback": 64}},
        "train": {"d": 8, "ridge": 1.0, "readout": "linear"},
        "crossval": {"enabled": True, "n_folds": 2, "scheme": "expanding", "embargo": 2},
        "predict": {"enabled": True, "from_dataset_split": "test"},
        "outputs": outputs,
    }


class _ScriptServer(ThreadingHTTPServer):
    """Loopback stand-in. One POST can sleep past the client's wall budget; the rest answer."""

    daemon_threads = True

    def __init__(self, hang_path: str | None, predict_body: Any, crossval_body: Any) -> None:
        super().__init__(("127.0.0.1", 0), _ScriptHandler)
        self.hang_path = hang_path
        self.predict_body = predict_body
        self.crossval_body = crossval_body
        self.posts: list[str] = []
        self.lock = threading.Lock()

    def handle_error(self, request, client_address) -> None:  # noqa: D102 - the hung arm is closed by the client timeout
        return

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server_address[1]}"


class _ScriptHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003 - http.server API
        return

    def _state(self) -> _ScriptServer:
        server = self.server
        assert isinstance(server, _ScriptServer)
        return server

    def _send(self, code: int, payload: Any) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> None:
        length = int(self.headers.get("Content-Length", "0") or "0")
        if length:
            self.rfile.read(length)

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        path = self.path.split("?", 1)[0]
        if path == "/v1/health":
            self._send(200, {"status": "ok"})
        elif path == "/v1/health/ready":
            self._send(200, {"status": "ready"})
        elif path == "/v1/generators":
            self._send(200, [{"name": "irregular_sine", "available": True, "version": "1.0.0"}])
        else:
            self._send(404, {"detail": "not found"})

    def do_POST(self) -> None:  # noqa: N802 - http.server API
        path = self.path.split("?", 1)[0]
        self._read_body()
        state = self._state()
        with state.lock:
            state.posts.append(path)
        if path == state.hang_path:
            # The client times out at max_wall and records RequestTimeout. Sleeping past
            # that, without a response, is what distinguishes a timeout from HTTP 500.
            time.sleep(_HANG_SECONDS)
            self.close_connection = True
            return
        if path == "/v1/datasets":
            self._send(201, {"dataset_id": "ds-aux", "meta": {"generator_version": "1.0.0"}})
        elif path == "/v1/train":
            self._send(200, {"final_metrics": {"r2": 0.5, "mse": 0.02}, "n_epochs": 1, "stopped_reason": "converged", "dataset": {"n_windows": 4, "lookback": 64}})
        elif path == "/v1/predict":
            self._send(200, state.predict_body)
        elif path == "/v1/crossval":
            self._send(200, state.crossval_body)
        else:
            self._send(404, {"detail": "not found"})


def _success_cli(capture: Path) -> str:
    return "#!/bin/bash\n" f"printf '%s\\n' \"$*\" > '{capture}'\n" "prev=''\nout=''\n" 'for a in "$@"; do [ "$prev" = "--out" ] && out="$a"; prev="$a"; done\n' '[ -n "$out" ] && : > "$out"\n' "exit 0\n"


def _silent_failure_cli() -> str:
    return "#!/bin/bash\nexit 1\n"


class AuxTimeoutAndBodyTest(unittest.TestCase):
    """Drive the recurrence path against the loopback stub. No live stack."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="rec-aux-timeout-"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))

    def _run(
        self,
        *,
        hang_path: str | None = None,
        predict_body: Any = _UNSET,
        crossval_body: Any = _UNSET,
        save_model: bool = False,
        cli_script: str | None = None,
        max_wall: str | None = None,
        force_outcome: str | None = None,
    ) -> tuple[int, dict, str, list[str]]:
        predict = {"predictions": [[0.1]], "shape": [1, 1]} if predict_body is _UNSET else predict_body
        crossval = {"task_type": "regression", "n_folds": 2, "eval_aggregate": {"r2": 0.4}, "eval_std": {"r2": 0.1}} if crossval_body is _UNSET else crossval_body
        server = _ScriptServer(hang_path, predict, crossval)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        self.addCleanup(server.server_close)
        run_dir = self.tmp / "20261004T000000Z-aux"
        run_dir.mkdir()
        port = server.server_address[1]
        (run_dir / "ports.json").write_text(
            json.dumps({"run_id": run_dir.name, "data": port, "recurrence": port, "data_url": server.base_url}),
            encoding="utf-8",
        )
        config = self.tmp / "experiment.yaml"
        config.write_text(yaml.safe_dump(_recurrence_config(save_model=save_model), sort_keys=False), encoding="utf-8")
        extra = ["--max-wall-seconds", max_wall] if max_wall is not None else []
        argv = ["--config", str(config), "--run-dir", str(run_dir), *FAST_FLAGS, *extra]

        def _invoke() -> tuple[int, str]:
            stdout = io.StringIO()
            with contextlib.redirect_stdout(stdout):
                code = rx.main(argv)
            return code, stdout.getvalue()

        with contextlib.ExitStack() as stack:
            if cli_script is not None:
                bindir = self.tmp / "bin"
                bindir.mkdir()
                stub = bindir / "juniper-recurrence"
                stub.write_text(cli_script, encoding="utf-8")
                stub.chmod(0o755)
                stack.enter_context(mock.patch.dict(os.environ, {"PATH": f"{bindir}:{os.environ.get('PATH', '')}"}))
            if force_outcome is not None:
                stack.enter_context(mock.patch.object(rx, "derive_recurrence_outcome", return_value=force_outcome))
            code, stdout = _invoke()
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        return code, manifest, stdout, list(server.posts)

    def test_a_crossval_timeout_is_degraded_and_save_model_still_runs(self) -> None:
        capture = self.tmp / "cli-cmd.txt"
        code, manifest, stdout, posts = self._run(
            hang_path="/v1/crossval",
            save_model=True,
            cli_script=_success_cli(capture),
            max_wall="0.2",
        )
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        self.assertNotEqual(code, rx.EXIT_UNREACHABLE)
        self.assertEqual(manifest["outcome"], "degraded")
        self.assertNotEqual(manifest["outcome"], "timed_out")
        crossval = manifest["phases"]["crossval"]
        self.assertEqual(crossval["status"], "failed")
        self.assertNotEqual(crossval["error"], rx.PHASE_CUT_SHORT)
        self.assertIn("timed out", crossval["error"])
        self.assertIn("/v1/crossval", crossval["error"])
        self.assertNotIn("wall-clock budget", crossval["error"])
        self.assertEqual(manifest["phases"]["train"], {"status": "ok"})
        self.assertEqual(manifest["phases"]["predict"], {"status": "ok"})
        self.assertEqual(manifest["phases"]["save_model"], {"status": "ok"})
        self.assertTrue(capture.is_file(), "save_model must run after the timed-out crossval")
        self.assertIn("--dataset ds-aux", capture.read_text(encoding="utf-8"))
        self.assertTrue((self.tmp / "20261004T000000Z-aux" / "artifacts" / "results" / "model.npz").is_file())
        self.assertEqual(posts.count("/v1/predict"), 1)
        self.assertEqual(posts.count("/v1/crossval"), 1)
        self.assertFalse(manifest["acceptance"]["ok"])
        self.assertTrue(any("crossval failed" in reason and "timed out" in reason for reason in manifest["acceptance"]["reasons"]))
        self.assertIn("outcome    : degraded", stdout)
        self.assertIn("crossval=failed", stdout)
        self.assertIn("save_model=ok", stdout)
        self.assertTrue((self.tmp / "20261004T000000Z-aux" / "artifacts" / "results" / "predict_response.json").is_file())
        self.assertFalse((self.tmp / "20261004T000000Z-aux" / "artifacts" / "results" / "crossval_response.json").exists())

    def test_a_non_object_200_stays_succeeded_and_writes_the_manifest(self) -> None:
        code, manifest, stdout, posts = self._run(predict_body=[0.1, 0.2], crossval_body=None)
        self.assertEqual(code, rx.EXIT_SUCCESS, stdout)
        self.assertEqual(manifest["outcome"], "succeeded")
        self.assertNotEqual(manifest["outcome"], "torn_down_early")
        self.assertEqual(manifest["phases"]["predict"], {"status": "ok"})
        self.assertEqual(manifest["phases"]["crossval"], {"status": "ok"})
        self.assertEqual(manifest["phases"]["train"], {"status": "ok"})
        self.assertIsNone(manifest["predict"])
        self.assertIsNone(manifest["crossval"])
        self.assertTrue(manifest["acceptance"]["ok"])
        self.assertEqual(manifest["acceptance"]["reasons"], [])
        results = self.tmp / "20261004T000000Z-aux" / "artifacts" / "results"
        self.assertEqual(json.loads((results / "predict_response.json").read_text(encoding="utf-8")), [0.1, 0.2])
        self.assertIsNone(json.loads((results / "crossval_response.json").read_text(encoding="utf-8")))
        self.assertEqual(posts.count("/v1/crossval"), 1)
        self.assertIn("outcome    : succeeded", stdout)

    def test_save_model_empty_stderr_records_the_return_code(self) -> None:
        code, manifest, _, _posts = self._run(save_model=True, cli_script=_silent_failure_cli())
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        self.assertEqual(manifest["outcome"], "degraded")
        save = manifest["phases"]["save_model"]
        self.assertEqual(save, {"status": "failed", "error": "1"})
        self.assertNotEqual(save["error"], rx.PHASE_CUT_SHORT)
        rerun = manifest["save_model_rerun"]
        self.assertFalse(rerun["ok"])
        self.assertEqual(rerun["returncode"], 1)
        self.assertEqual(rerun.get("stderr_tail", ""), "")
        self.assertTrue(any(reason == "save_model re-run failed: 1" for reason in manifest["acceptance"]["reasons"]))
        self.assertEqual(manifest["phases"]["predict"], {"status": "ok"})
        self.assertEqual(manifest["phases"]["crossval"], {"status": "ok"})

    def test_forced_degraded_with_no_acceptance_reason_still_exits_non_zero(self) -> None:
        # Every real phase failure also appends a reason, so `exit = 0 if not reasons`
        # would still fail those tests. This arm is the outcome conjunct on its own.
        code, manifest, stdout, _posts = self._run(force_outcome="degraded")
        self.assertEqual(manifest["acceptance"]["reasons"], [])
        self.assertTrue(all(record["status"] in ("ok", "skipped") for record in manifest["phases"].values()))
        self.assertEqual(manifest["outcome"], "degraded")
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        self.assertNotEqual(code, rx.EXIT_SUCCESS)
        self.assertFalse(manifest["acceptance"]["ok"])
        self.assertIn("outcome    : degraded", stdout)
        self.assertIn("exit=1", stdout)


class HeadlineColumnIndependenceTest(unittest.TestCase):
    """One bad headline column must not drop or crash its siblings."""

    def _run_dir(self, stats: dict) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        run_dir = Path(tmp.name) / "run"
        results = run_dir / "artifacts" / "results"
        results.mkdir(parents=True)
        (results / "stats.json").write_text(json.dumps(stats), encoding="utf-8")
        return run_dir

    def test_a_string_train_r2_and_a_missing_std_leave_the_int_cv_r2(self) -> None:
        stats = {
            "recurrence": {
                "final_metrics": {"r2": "0.91"},
                "crossval": {"eval_aggregate": {"r2": 0}},
                "dataset_descriptor": {"n_windows": 4},
            }
        }
        metrics = run_suite._headline_metrics(self._run_dir(stats))
        self.assertEqual(metrics, {"cv_r2": 0, "n_windows": 4})
        self.assertIsInstance(metrics["cv_r2"], int)
        self.assertNotIn("train_r2", metrics)
        self.assertNotIn("cv_r2_std", metrics)

    def test_a_non_mapping_std_does_not_raise_or_drop_cv_r2(self) -> None:
        stats = {
            "recurrence": {
                "final_metrics": {"r2": 0.2},
                "crossval": {"eval_aggregate": {"r2": 0.3}, "eval_std": 0.1},
                "dataset_descriptor": {"n_windows": 2},
            }
        }
        self.assertEqual(run_suite._headline_metrics(self._run_dir(stats)), {"train_r2": 0.2, "cv_r2": 0.3, "n_windows": 2})


if __name__ == "__main__":
    unittest.main()
