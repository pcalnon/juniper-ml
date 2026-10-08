#!/usr/bin/env python3
"""How a failed recurrence phase turns an HTTP body into the text the suite prints.

``tests/test_run_experiment.py`` scripts short string ``detail`` values. It does not
choose among ``detail`` / ``message`` / ``error``, cut a long body at 500 characters,
or keep a sibling ``input`` echo out of the phase record. A validation-error *list*
(the real FastAPI 422 shape) and a non-JSON body are the same hole: both must stay
``degraded`` at exit 1, not become a config error (exit 2).

``tests/test_run_suite.py`` prints one failed phase that already carries a real error
string. It does not fall through to the suite-level error when that summary is empty,
does not drop an error hanging off ``not_reached``, and does not count succeeded /
degraded / failed / not-run in the same report.

No live stack. ``util/`` is not pre-commit-lint-gated, so this unittest is the gate.
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import run_experiment as rx  # noqa: E402
from experiments import run_suite  # noqa: E402

FAST_FLAGS = ["--poll-interval", "0.05", "--stall-seconds", "5", "--health-timeout", "2"]
# Echoed request fields a phase record must not copy. Named *_MARKER: bandit B105 keys on a
# constant NAME containing "secret", whatever the value.
PREDICT_ECHO_MARKER = "ECHO-PREDICT-INPUT"
CROSSVAL_ECHO_MARKER = "ECHO-CROSSVAL-INPUT"
FALSY_ECHO_MARKER = "ECHO-FALSY-INPUT"
TAILMARKER = "TAILMARKER"

_TRAIN_OK = json.dumps({"final_metrics": {"r2": 0.5, "mse": 0.02}, "n_epochs": 1, "stopped_reason": "converged", "dataset": {"n_windows": 4, "lookback": 64}}).encode("utf-8")
_PREDICT_OK = json.dumps({"predictions": [[0.1]], "shape": [1, 1]}).encode("utf-8")
_CROSSVAL_OK = json.dumps({"task_type": "regression", "n_folds": 2, "eval_aggregate": {"r2": 0.4}, "eval_std": {"r2": 0.1}}).encode("utf-8")
_DATASET_OK = json.dumps({"dataset_id": "ds-body", "meta": {"generator_version": "1.0.0"}}).encode("utf-8")


def _recurrence_config() -> dict:
    return {
        "schema_version": 1,
        "experiment": {"name": "rec-body", "description": "phase-error body stub", "seed": 777},
        "dataset": {"generator": "irregular_sine", "split": "train", "params": {"n_steps": 500, "lookback": 64}},
        "train": {"d": 8, "ridge": 1.0, "readout": "linear"},
        "crossval": {"enabled": True, "n_folds": 2, "scheme": "expanding", "embargo": 2},
        "predict": {"enabled": True, "from_dataset_split": "test"},
        "outputs": {"plots": [], "max_wall_seconds": 30},
    }


class _BodyServer(ThreadingHTTPServer):
    """Loopback stand-in. Each POST path can answer with a scripted status and raw body."""

    daemon_threads = True

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _BodyHandler)
        self.replies: dict[str, tuple[int, bytes]] = {}
        self.posts: list[str] = []
        self.lock = threading.Lock()

    def handle_error(self, request, client_address) -> None:  # noqa: D102 - a client disconnect is not a test failure
        pass

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server_address[1]}"


class _BodyHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003 - http.server API
        return

    def _state(self) -> _BodyServer:
        server = self.server
        assert isinstance(server, _BodyServer)
        return server

    def _send(self, code: int, body: bytes) -> None:
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
            self._send(200, b'{"status": "ok"}')
        elif path == "/v1/health/ready":
            self._send(200, b'{"status": "ready"}')
        elif path == "/v1/generators":
            self._send(200, b'[{"name": "irregular_sine", "available": true, "version": "1.0.0"}]')
        else:
            self._send(404, b'{"detail": "not found"}')

    def do_POST(self) -> None:  # noqa: N802 - http.server API
        path = self.path.split("?", 1)[0]
        self._read_body()
        state = self._state()
        with state.lock:
            state.posts.append(path)
            reply = state.replies.get(path)
        if reply is not None:
            self._send(reply[0], reply[1])
            return
        if path == "/v1/datasets":
            self._send(201, _DATASET_OK)
        elif path == "/v1/train":
            self._send(200, _TRAIN_OK)
        elif path == "/v1/predict":
            self._send(200, _PREDICT_OK)
        elif path == "/v1/crossval":
            self._send(200, _CROSSVAL_OK)
        else:
            self._send(404, b'{"detail": "not found"}')


class _BodyTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="rec-phase-body-"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))

    def _run(self, replies: dict[str, tuple[int, bytes]]) -> tuple[int, dict, str, list[str]]:
        server = _BodyServer()
        server.replies.update(replies)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        self.addCleanup(server.server_close)
        run_dir = self.tmp / "20261004T000000Z-body"
        run_dir.mkdir()
        port = server.server_address[1]
        (run_dir / "ports.json").write_text(
            json.dumps({"run_id": run_dir.name, "data": port, "recurrence": port, "data_url": server.base_url}),
            encoding="utf-8",
        )
        config = self.tmp / "experiment.yaml"
        config.write_text(yaml.safe_dump(_recurrence_config(), sort_keys=False), encoding="utf-8")
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = rx.main(["--config", str(config), "--run-dir", str(run_dir), *FAST_FLAGS])
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        return code, manifest, stdout.getvalue(), list(server.posts)

    def _results(self) -> Path:
        return self.tmp / "20261004T000000Z-body" / "artifacts" / "results"


class PhaseErrorBodyTest(_BodyTestCase):
    """The text stored on the phase is the chosen field, cut at 500, and nothing else in the body."""

    def test_both_aux_failures_keep_their_own_bodies(self) -> None:
        # predict has no detail and no message, so the envelope `error` key is the text.
        # crossval's string detail wins over message, and the 600th character plus the
        # echoed input must not reach the manifest. One run, so a driver that stopped
        # after the first failure, or kept only the last error, cannot pass.
        predict_error = "HTTP 500: predict down"
        crossval_error = "HTTP 422: " + ("A" * 500)
        crossval_body = {"detail": ("A" * 600) + TAILMARKER, "message": "should-not-win", "input": CROSSVAL_ECHO_MARKER}
        with self.assertLogs(rx.log, level="ERROR") as logs:
            code, manifest, stdout, posts = self._run(
                {
                    "/v1/predict": (500, json.dumps({"error": "predict down", "input": PREDICT_ECHO_MARKER}).encode("utf-8")),
                    "/v1/crossval": (422, json.dumps(crossval_body).encode("utf-8")),
                }
            )
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        self.assertNotEqual(code, rx.EXIT_MISUSE)
        self.assertEqual(manifest["outcome"], "degraded")
        self.assertEqual(manifest["phases"]["train"], {"status": "ok"})
        self.assertEqual(manifest["phases"]["predict"], {"status": "failed", "error": predict_error})
        self.assertEqual(manifest["phases"]["crossval"], {"status": "failed", "error": crossval_error})
        self.assertEqual(manifest["phases"]["save_model"], {"status": "skipped"})
        self.assertEqual(posts.count("/v1/predict"), 1)
        self.assertEqual(posts.count("/v1/crossval"), 1)
        reasons = manifest["acceptance"]["reasons"]
        self.assertIn(f"predict failed: {predict_error}", reasons)
        self.assertIn(f"crossval failed: {crossval_error}", reasons)
        self.assertLess(reasons.index(f"predict failed: {predict_error}"), reasons.index(f"crossval failed: {crossval_error}"))
        logged = "\n".join(logs.output)
        self.assertLess(logged.index("predict failed:"), logged.index("crossval failed:"))
        rendered = json.dumps(manifest)
        for marker in (PREDICT_ECHO_MARKER, CROSSVAL_ECHO_MARKER, TAILMARKER, "should-not-win"):
            self.assertNotIn(marker, rendered)
            self.assertNotIn(marker, stdout)
        self.assertIn("predict=failed", stdout)
        self.assertIn("crossval=failed", stdout)
        self.assertTrue((self._results() / "train_response.json").is_file())
        self.assertFalse((self._results() / "predict_response.json").exists())
        self.assertFalse((self._results() / "crossval_response.json").exists())

    def test_a_falsy_detail_falls_through_to_message(self) -> None:
        # `if payload.get(key)` treats 0 as absent. Keeping it would hide the message,
        # and skipping ahead to `error` would hide it the other way.
        code, manifest, _stdout, posts = self._run(
            {
                "/v1/crossval": (
                    422,
                    json.dumps({"detail": 0, "message": "from-message", "error": "from-error", "input": FALSY_ECHO_MARKER}).encode("utf-8"),
                )
            }
        )
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        self.assertEqual(manifest["outcome"], "degraded")
        self.assertEqual(manifest["phases"]["predict"], {"status": "ok"})
        self.assertEqual(manifest["phases"]["crossval"], {"status": "failed", "error": "HTTP 422: from-message"})
        self.assertEqual(posts.count("/v1/crossval"), 1)
        rendered = json.dumps(manifest)
        self.assertNotIn(FALSY_ECHO_MARKER, rendered)
        self.assertNotIn("from-error", manifest["phases"]["crossval"]["error"])
        self.assertNotIn("HTTP 422: 0", manifest["phases"]["crossval"]["error"])

    def test_a_non_json_422_is_degraded_and_cut_at_500(self) -> None:
        body = b"plain-body:" + (b"Z" * 600)
        code, manifest, _stdout, _posts = self._run({"/v1/crossval": (422, body)})
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        self.assertNotEqual(code, rx.EXIT_MISUSE)
        self.assertEqual(manifest["outcome"], "degraded")
        error = manifest["phases"]["crossval"]["error"]
        kept = body[:500].decode("utf-8")
        self.assertEqual(error, "HTTP 422: " + kept)
        # The tail is more of the same Z, so compare a count: 600 would mean the cut was dropped.
        self.assertEqual(error.count("Z"), kept.count("Z"))
        self.assertLess(error.count("Z"), 600)
        self.assertEqual(manifest["phases"]["predict"], {"status": "ok"})
        self.assertTrue((self._results() / "predict_response.json").is_file())
        self.assertFalse((self._results() / "crossval_response.json").exists())

    def test_a_validation_list_422_stays_degraded_not_a_config_error(self) -> None:
        # Train's 422 is exit 2. An aux-phase 422, even in FastAPI's list shape, is a
        # failed phase: exit 1, outcome degraded, and the list text is the phase error.
        item = {"type": "missing", "loc": ["body", "X_full"], "msg": "Field required"}
        code, manifest, _stdout, _posts = self._run({"/v1/crossval": (422, json.dumps({"detail": [item]}).encode("utf-8"))})
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        self.assertNotEqual(code, rx.EXIT_MISUSE)
        self.assertNotEqual(code, rx.EXIT_RUN_FAILED)
        self.assertEqual(manifest["outcome"], "degraded")
        self.assertEqual(manifest["phases"]["crossval"], {"status": "failed", "error": "HTTP 422: " + str([item])})
        self.assertEqual(manifest["phases"]["train"], {"status": "ok"})
        self.assertIn("Field required", manifest["phases"]["crossval"]["error"])
        self.assertTrue(any("crossval failed:" in reason for reason in manifest["acceptance"]["reasons"]))


class OutcomeLineFallbackTest(unittest.TestCase):
    """The console uses the phase summary when it has one, and the suite error when it does not."""

    def test_an_empty_phase_summary_falls_through_to_the_suite_error(self) -> None:
        self.assertEqual(
            run_suite._outcome_line({"outcome": "degraded", "phases": None, "error": "unreadable manifest.json"}),
            "degraded (unreadable manifest.json)",
        )
        phases = {name: {"status": "ok"} for name in ("train", "predict", "crossval", "save_model")}
        line = run_suite._outcome_line({"outcome": "degraded", "phases": phases, "error": "stale launcher error"})
        self.assertEqual(line, "degraded (stale launcher error)")
        self.assertNotIn("predict", line)

    def test_a_not_reached_error_is_not_printed(self) -> None:
        # Only `failed` interpolates `error`. A not_reached record left over from the
        # cut-short placeholder must not carry that text into the suite line.
        phases = {
            "predict": {"status": "not_reached", "error": "SECRET-PHASE-CUT"},
            "crossval": {"status": "failed", "error": "HTTP 422: missing X_full"},
            "save_model": {"status": "skipped"},
        }
        summary = run_suite._failed_phase_summary(phases)
        self.assertEqual(summary, "predict not_reached; crossval failed: HTTP 422: missing X_full")
        self.assertNotIn("SECRET-PHASE-CUT", summary)
        self.assertEqual(
            run_suite._outcome_line({"outcome": "degraded", "phases": phases, "error": "stale launcher error"}),
            "degraded (predict not_reached; crossval failed: HTTP 422: missing X_full)",
        )


class DegradedCountBucketsTest(unittest.TestCase):
    """`degraded` is its own bucket. A missing row and a null outcome stay `not run`."""

    def test_degraded_is_counted_apart_from_failed_and_not_run(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        suite_dir = Path(tmp.name) / "suite"
        suite_dir.mkdir()
        rows = [
            {"cell_id": "c000", "outcome": "succeeded"},
            {"cell_id": "c001", "outcome": "degraded", "phases": {"crossval": {"status": "failed", "error": "HTTP 422: x"}}},
            {"cell_id": "c002", "outcome": "failed", "phases": {"train": {"status": "failed", "error": "HTTP 409: busy"}}},
            {"cell_id": "c004", "outcome": None},
        ]
        (suite_dir / "registry.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        cells = [{"cell_id": cell_id, "name": cell_id, "overrides": {}} for cell_id in ("c000", "c001", "c002", "c003", "c004")]
        self.assertEqual(run_suite.aggregate(suite_dir, {"name": "t", "description": "four buckets"}, cells), 1)
        report = (suite_dir / "REPORT.md").read_text(encoding="utf-8")
        self.assertIn("Cells: 5 total, 1 succeeded, 1 degraded, 1 failed/other, 2 not run.", report)
        self.assertIn("- c001: crossval failed: HTTP 422: x", report)
        self.assertNotIn("- c000:", report)
        self.assertNotIn("- c002:", report)
        self.assertNotIn("- c003:", report)
        self.assertNotIn("- c004:", report)
        self.assertNotIn("HTTP 409: busy", report.split("## Degraded cells", 1)[1])


class SummaryPhaseGuardTest(unittest.TestCase):
    """The closing summary reads phase status best-effort. A non-mapping record must not raise or be printed."""

    def test_a_non_mapping_phase_record_does_not_crash_the_summary(self) -> None:
        stdout = io.StringIO()
        phases = {
            "train": {"status": "ok"},
            "predict": "SECRET-STATUS",
            "crossval": {"status": "failed", "error": "HTTP 422: x"},
            "save_model": {"status": "skipped"},
        }
        with contextlib.redirect_stdout(stdout):
            rx._print_summary(
                "run-body",
                "rec-body",
                "irregular_sine",
                {"dataset_id": "ds-body"},
                "degraded",
                rx.EXIT_ACCEPTANCE,
                ["crossval failed: HTTP 422: x"],
                {"train": 0.1},
                {},
                Path("/tmp/rec-phase-body-summary"),
                kind="recurrence",
                phases=phases,
            )
        rendered = stdout.getvalue()
        self.assertIn("outcome    : degraded", rendered)
        self.assertIn("train=ok", rendered)
        self.assertIn("predict=None", rendered)
        self.assertIn("crossval=failed", rendered)
        self.assertIn("save_model=skipped", rendered)
        self.assertNotIn("SECRET-STATUS", rendered)


if __name__ == "__main__":
    unittest.main()
