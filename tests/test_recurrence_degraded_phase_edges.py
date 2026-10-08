#!/usr/bin/env python3
"""Edges of the W0.3 / W0.4 outcome and headline readers that the producer suites cannot see.

``tests/test_run_experiment.py`` drives ``derive_recurrence_outcome`` with well-formed
``{"status": ...}`` records and drives the aux phases with HTTP status codes. A missing
key, a non-mapping record, or a dropped connection never reaches those assertions, and a
regression that raises on the first or that lets the second escape as ``torn_down_early``
(exit 3) stays green.

``tests/test_run_suite.py`` reads headline metrics off the real ``build_stats`` shape and
prints one failed phase that carries a real error string. It does not plant the pre-W0.4
top-level ``r2`` / ``cv_r2`` keys beside the nested ones, does not keep ``n_windows == 0``,
and does not render a degraded cell whose phase record cannot be read.

No live stack. ``util/`` is not pre-commit-lint-gated, so this unittest is the gate.
"""

from __future__ import annotations

import json
import shutil
import socket
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "util"))

from experiments import run_experiment as rx  # noqa: E402
from experiments import run_suite  # noqa: E402

FAST_FLAGS = ["--poll-interval", "0.05", "--stall-seconds", "5", "--health-timeout", "2"]


def _recurrence_config() -> dict:
    return {
        "schema_version": 1,
        "experiment": {"name": "rec-edge", "description": "phase-edge stub", "seed": 777},
        "dataset": {"generator": "irregular_sine", "split": "train", "params": {"n_steps": 500, "lookback": 64}},
        "train": {"d": 8, "ridge": 1.0, "readout": "linear"},
        "crossval": {"enabled": True, "n_folds": 2, "scheme": "expanding", "embargo": 2},
        "predict": {"enabled": True, "from_dataset_split": "test"},
        "outputs": {"plots": [], "max_wall_seconds": 30},
    }


class _DropServer(ThreadingHTTPServer):
    """Loopback stand-in that resets one chosen POST and answers the rest."""

    daemon_threads = True

    def __init__(self, drop_path: str) -> None:
        super().__init__(("127.0.0.1", 0), _DropHandler)
        self.drop_path = drop_path
        self.posts: list[str] = []
        self.lock = threading.Lock()

    def handle_error(self, request, client_address) -> None:  # noqa: D102 - the dropped arm resets the socket on purpose
        pass

    @property
    def base_url(self) -> str:
        return f"http://127.0.0.1:{self.server_address[1]}"


class _DropHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:  # noqa: A003 - http.server API
        return

    def _state(self) -> _DropServer:
        server = self.server
        assert isinstance(server, _DropServer)
        return server

    def _send(self, code: int, payload: dict | list) -> None:
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
        if path == state.drop_path:
            # Reset after the request is fully read, so urllib sees a connection failure
            # rather than a short body. Do not close the listening socket: the next phase
            # still has to be answerable.
            self.close_connection = True
            try:
                self.connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                return
            return
        if path == "/v1/datasets":
            self._send(201, {"dataset_id": "ds-edge", "meta": {"generator_version": "1.0.0"}})
        elif path == "/v1/train":
            self._send(200, {"final_metrics": {"r2": 0.5, "mse": 0.02}, "n_epochs": 1, "stopped_reason": "converged", "dataset": {"n_windows": 4, "lookback": 64}})
        elif path == "/v1/predict":
            self._send(200, {"predictions": [[0.1]], "shape": [1, 1]})
        elif path == "/v1/crossval":
            self._send(200, {"task_type": "regression", "n_folds": 2, "eval_aggregate": {"r2": 0.4}, "eval_std": {"r2": 0.1}})
        else:
            self._send(404, {"detail": "not found"})


class _DropTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="rec-phase-edge-"))
        self.addCleanup(lambda: shutil.rmtree(self.tmp, ignore_errors=True))

    def _run(self, drop_path: str) -> tuple[int, dict, list[str]]:
        server = _DropServer(drop_path)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.shutdown)
        self.addCleanup(server.server_close)
        run_dir = self.tmp / "20261004T000000Z-edge"
        run_dir.mkdir()
        port = server.server_address[1]
        (run_dir / "ports.json").write_text(
            json.dumps({"run_id": run_dir.name, "data": port, "recurrence": port, "data_url": server.base_url}),
            encoding="utf-8",
        )
        config = self.tmp / "experiment.yaml"
        config.write_text(yaml.safe_dump(_recurrence_config(), sort_keys=False), encoding="utf-8")
        code = rx.main(["--config", str(config), "--run-dir", str(run_dir), *FAST_FLAGS])
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        return code, manifest, list(server.posts)


class DeriveRecurrenceOutcomeEdgesTest(unittest.TestCase):
    """Success needs a mapping whose status is ``ok`` or ``skipped``. Anything else degrades, and must not raise."""

    def test_a_missing_aux_key_fails_closed(self) -> None:
        phases = {"train": {"status": "ok"}, "predict": {"status": "ok"}, "save_model": {"status": "skipped"}}
        self.assertEqual(rx._incomplete_aux_phases(phases), ["crossval"])
        self.assertEqual(rx.derive_recurrence_outcome(phases), "degraded")

    def test_a_non_mapping_record_fails_closed_and_does_not_raise(self) -> None:
        for record in (None, "ok", ["ok"], 1, True):
            phases = {"predict": {"status": "ok"}, "crossval": record, "save_model": {"status": "skipped"}}
            self.assertEqual(rx.derive_recurrence_outcome(phases), "degraded", repr(record))
            self.assertEqual(rx._incomplete_aux_phases(phases), ["crossval"], repr(record))

    def test_an_empty_record_or_unknown_status_fails_closed(self) -> None:
        self.assertEqual(rx.derive_recurrence_outcome({"predict": {}, "crossval": {"status": "ok"}, "save_model": {"status": "skipped"}}), "degraded")
        self.assertEqual(rx.derive_recurrence_outcome({"predict": {"status": "OK"}, "crossval": {"status": "ok"}, "save_model": {"status": "skipped"}}), "degraded")

    def test_incomplete_names_follow_run_order_and_train_is_not_one_of_them(self) -> None:
        # Dict insertion order is the reverse of the run. The summary the driver logs
        # must still name predict before save_model, and a failed train is a different outcome.
        phases = {
            "save_model": {"status": "failed", "error": "cli"},
            "crossval": {"status": "ok"},
            "predict": {"status": "not_reached"},
            "train": {"status": "failed", "error": "HTTP 500"},
        }
        self.assertEqual(rx._incomplete_aux_phases(phases), ["predict", "save_model"])
        self.assertEqual(rx.derive_recurrence_outcome(phases), "degraded")

    def test_an_empty_phase_map_fails_closed_in_run_order(self) -> None:
        self.assertEqual(rx._incomplete_aux_phases({}), ["predict", "crossval", "save_model"])
        self.assertEqual(rx.derive_recurrence_outcome({}), "degraded")


class HeadlineMetricEdgesTest(unittest.TestCase):
    """The W0.4 reader must not fall back to the top-level keys it used to look for, and must not raise on a bad file."""

    def _run_dir(self, stats: object | None, *, raw: str | None = None) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        run_dir = Path(tmp.name) / "run"
        results = run_dir / "artifacts" / "results"
        results.mkdir(parents=True)
        if raw is not None or stats is not None:
            text = raw if raw is not None else json.dumps(stats)
            (results / "stats.json").write_text(text, encoding="utf-8")
        return run_dir

    def test_a_missing_corrupt_or_non_object_stats_file_yields_nothing(self) -> None:
        self.assertEqual(run_suite._headline_metrics(self._run_dir(None)), {})
        self.assertEqual(run_suite._headline_metrics(self._run_dir(None, raw="{")), {})
        self.assertEqual(run_suite._headline_metrics(self._run_dir(["not", "an", "object"])), {})

    def test_top_level_decoy_scores_are_ignored_and_a_zero_window_count_is_kept(self) -> None:
        # The pre-W0.4 reader looked for these names at the top of the block. A writer that
        # also left them there, or a reader that falls back to them, would report the decoy.
        stats = {
            "recurrence": {
                "r2": 0.99,
                "train_r2": 0.88,
                "cv_r2": 0.77,
                "final_metrics": {"r2": 0.11},
                "crossval": None,
                "dataset_descriptor": {"n_windows": 0},
            }
        }
        self.assertEqual(run_suite._headline_metrics(self._run_dir(stats)), {"train_r2": 0.11, "n_windows": 0})

    def test_a_bool_window_count_is_not_a_metric_and_a_non_mapping_level_does_not_raise(self) -> None:
        stats = {
            "recurrence": {
                "final_metrics": ["not-a-block"],
                "crossval": ["not-a-block"],
                "dataset_descriptor": {"n_windows": True},
            }
        }
        self.assertEqual(run_suite._headline_metrics(self._run_dir(stats)), {})

    def test_a_non_mapping_cascor_block_does_not_raise_or_drop_recurrence(self) -> None:
        stats = {"cascor": ["not-a-block"], "recurrence": {"final_metrics": {"r2": 0.2}, "dataset_descriptor": {"n_windows": 3}}}
        self.assertEqual(run_suite._headline_metrics(self._run_dir(stats)), {"train_r2": 0.2, "n_windows": 3})


class FailedPhaseSummaryEdgesTest(unittest.TestCase):
    """The report names every lost phase, and a blank error is not the word ``None``."""

    def test_a_blank_or_missing_error_is_named_and_ok_phases_are_omitted(self) -> None:
        phases = {
            "train": {"status": "ok", "error": "must not be printed"},
            "predict": {"status": "failed", "error": ""},
            "crossval": {"status": "failed"},
            "save_model": {"status": "skipped", "error": "must not be printed"},
            "noise": "not-a-record",
        }
        self.assertEqual(
            run_suite._failed_phase_summary(phases),
            "predict failed: no error recorded; crossval failed: no error recorded",
        )
        line = run_suite._outcome_line({"outcome": "degraded", "phases": phases, "error": "launcher --up failed"})
        self.assertEqual(line, "degraded (predict failed: no error recorded; crossval failed: no error recorded)")

    def test_an_unreadable_phase_block_summarises_to_empty(self) -> None:
        self.assertEqual(run_suite._failed_phase_summary(None), "")
        self.assertEqual(run_suite._failed_phase_summary(["crossval"]), "")
        self.assertEqual(run_suite._failed_phase_summary("crossval failed"), "")

    def test_report_says_when_a_degraded_cell_has_no_usable_phase_record(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        suite_dir = Path(tmp.name) / "suite"
        suite_dir.mkdir()
        rows: list[dict[str, Any]] = [
            {"cell_id": "c000", "outcome": "degraded", "phases": None},
            {"cell_id": "c001", "outcome": "degraded", "phases": ["not-a-map"]},
            {"cell_id": "c002", "outcome": "degraded", "phases": {"predict": {"status": "failed", "error": ""}, "crossval": {"status": "not_reached"}}},
        ]
        (suite_dir / "registry.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        cells = [{"cell_id": row["cell_id"], "name": row["cell_id"], "overrides": {}} for row in rows]
        self.assertEqual(run_suite.aggregate(suite_dir, {"name": "t", "description": "unusable phase records"}, cells), 1)
        report = (suite_dir / "REPORT.md").read_text(encoding="utf-8")
        self.assertIn("- c000: no phase record in the registry row", report)
        self.assertIn("- c001: no phase record in the registry row", report)
        self.assertIn("- c002: predict failed: no error recorded; crossval not_reached", report)
        self.assertNotIn("None", report)


class ConnectionDropPhaseTest(_DropTestCase):
    """A reset socket is not an HTTP status. The aux phase must record it and continue; train must re-raise it."""

    def test_a_dropped_predict_is_degraded_and_crossval_still_runs(self) -> None:
        code, manifest, posts = self._run("/v1/predict")
        self.assertEqual(code, rx.EXIT_ACCEPTANCE)
        self.assertNotEqual(code, rx.EXIT_UNREACHABLE)
        self.assertEqual(manifest["outcome"], "degraded")
        predict = manifest["phases"]["predict"]
        self.assertEqual(predict["status"], "failed")
        self.assertNotEqual(predict["error"], rx.PHASE_CUT_SHORT)
        self.assertIn("/v1/predict", predict["error"])
        self.assertEqual(manifest["phases"]["crossval"], {"status": "ok"})
        self.assertEqual(manifest["phases"]["train"], {"status": "ok"})
        self.assertEqual(manifest["train"]["final_metrics"]["r2"], 0.5)
        self.assertEqual(posts.count("/v1/predict"), 1)
        self.assertEqual(posts.count("/v1/crossval"), 1)
        self.assertTrue(any("predict failed" in reason for reason in manifest["acceptance"]["reasons"]))

    def test_a_dropped_train_is_unreachable_and_names_the_connection_error(self) -> None:
        code, manifest, posts = self._run("/v1/train")
        self.assertEqual(code, rx.EXIT_UNREACHABLE)
        self.assertEqual(manifest["outcome"], "torn_down_early")
        train = manifest["phases"]["train"]
        self.assertEqual(train["status"], "failed")
        self.assertNotEqual(train["error"], rx.PHASE_CUT_SHORT)
        self.assertIn("/v1/train", train["error"])
        self.assertEqual(manifest["phases"]["predict"], {"status": "not_reached"})
        self.assertEqual(manifest["phases"]["crossval"], {"status": "not_reached"})
        self.assertTrue(any("unreachable mid-run" in reason for reason in manifest["acceptance"]["reasons"]))
        self.assertNotIn("/v1/predict", posts)
        self.assertNotIn("/v1/crossval", posts)
        self.assertTrue((self.tmp / "20261004T000000Z-edge" / "manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()
