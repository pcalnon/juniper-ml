#!/usr/bin/env python3
"""W5.4 (F-D3 / F-SCI4): the suite ``acceptance:`` facility and the R5 band on the E-H row.

Plan: ``notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md``
W5.4 and rulings R5 / R6. Before this facility the audited E-H cell scored ``cv_r2 = -18081`` and
the suite called it ``succeeded`` -- a number the suite produced correctly, which nothing judged.

What is pinned here, hermetically (stub launcher + stub driver through the ``JUNIPER_SUITE_*``
seams, the run root redirected, no live stack):

- the schema: a list of ``{metric, min, max, mode}`` bands on the suite or on an ``include`` row;
  every malformed shape is a ``SuiteError`` at load, before any cell launches;
- the comparator reads the W0.4 headline keys and treats bounds as inclusive; ``0.0`` is a value;
- R6's outcome semantics: ``cv_r2 = -18081`` is ``failed`` under ``gate`` (exit 1) and ``flagged``
  under ``report`` (exit 0); a metric the band names that the cell did not produce follows the mode
  (``failed (cv_r2 absent (gate))`` / ``flagged``), distinct from ``degraded``;
- row scoping: a band on the E-H row never judges the irregular-sine control (``cv_r2 0.975`` would
  fail ``+0.5`` under a suite-level band -- and does, when the band is suite-level);
- ``flagged`` is complete: ``--resume`` skips it; the exit code counts it with ``succeeded``;
- the reporting surface: an ``acceptance`` column (last, so no earlier column moves) in
  ``aggregate.csv`` and the REPORT table, and a ``## Acceptance bands`` section;
- the shipped E-H suite carries the R5 band: ``cv_r2 in [-1.0, +0.5]`` and ``cv_r2_std <= 0.5``, both
  ``gate``, on the equities row only.
"""

from __future__ import annotations

import csv
import importlib.util
import io
import json
import os
import stat
import sys
import tempfile
import unittest
import unittest.mock
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "util" / "experiments" / "run_suite.py"
EH_SUITE = REPO_ROOT / "util" / "experiments" / "suites" / "p4" / "e-h-recurrence-real-data.yaml"

spec = importlib.util.spec_from_file_location("run_suite_acceptance", MODULE_PATH)
run_suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_suite)

# APD-ML-002: the cascor fixtures go through the REAL writer, so a change to its cascor block breaks them loudly.
STATS_SUMMARY_PATH = REPO_ROOT / "util" / "experiments" / "stats_summary.py"
_stats_spec = importlib.util.spec_from_file_location("stats_summary_for_acceptance_tests", STATS_SUMMARY_PATH)
stats_summary = importlib.util.module_from_spec(_stats_spec)
_stats_spec.loader.exec_module(stats_summary)

SuiteError = run_suite.SuiteError

# A driver-valid base config (the suite validates every materialised cell through the real driver's
# load_config). The app is cascor only because that is the smallest valid config; the stub driver
# writes recurrence-shaped stats.json, which `_headline_metrics` reads regardless of the app.
BASE_CONFIG = """\
schema_version: 1
experiment:
  name: fixture
  seed: 7
service:
  log_level: INFO
dataset:
  generator: spiral
  params:
    n_spirals: 2
    n_points_per_spiral: 100
    seed: 7
training:
  params:
    max_hidden_units: 2
outputs:
  plots: []
  max_wall_seconds: 60
"""

CONTROL_MARKER = "max_hidden_units: 2"
EQUITIES_MARKER = "max_hidden_units: 4"

R5_BAND = [{"metric": "cv_r2", "min": -1.0, "max": 0.5, "mode": "gate"}, {"metric": "cv_r2_std", "max": 0.5, "mode": "gate"}]


def _suite_yaml(base: Path, suite_dir: Path, *, row_bands: Any = None, suite_bands: Any = None) -> str:
    # `Any`: the malformed-schema tests pass deliberately wrong shapes (a mapping where a list belongs).
    doc: dict[str, Any] = {
        "schema_version": 1,
        "suite": {"name": "t-acc", "description": "acceptance fixture", "app": "cascor", "base_config": [str(base)], "seed_policy": "fixed"},
        "execution": {"mode": "sequential", "continue_on_failure": True, "per_run_timeout_seconds": 900},
        "include": [
            {"name": "control", "overrides": {"training.params.max_hidden_units": 2}},
            {"name": "equities", "overrides": {"training.params.max_hidden_units": 4}},
        ],
        "outputs": {"suite_dir": str(suite_dir)},
    }
    if row_bands is not None:
        doc["include"][1]["acceptance"] = row_bands
    if suite_bands is not None:
        doc["acceptance"] = suite_bands
    return json.dumps(doc)  # JSON is YAML


def _write_stub_launcher(path: Path, marker_dir: Path) -> None:
    path.write_text("#!/usr/bin/env bash\n" f"MARKERS={marker_dir}\n" 'if [[ "$1" == "--up" ]]; then\n' '  touch "$MARKERS/up-$$"\n' '  echo "=== Experiment run stub-run-$$ is up ==="\n' "  exit 0\n" "fi\n" 'if [[ "$1" == "--down" ]]; then touch "$MARKERS/down-$2"; exit 0; fi\n' "exit 2\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _write_stub_driver(path: Path, per_cell: dict) -> None:
    """``per_cell`` maps a config-text marker to ``{"outcome": ..., "cv_r2": ..., "cv_r2_std": ...}``.

    Writes the manifest and a stats.json in the shape ``RECURRENCE_HEADLINE_PATHS`` reads. A cell whose
    ``cv_r2`` is ``None`` gets ``crossval: null`` -- the audited shape, which yields no ``cv_*`` key.
    """
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys, pathlib\n"
        "args = dict(zip(sys.argv[1::2], sys.argv[2::2]))\n"
        "run_dir = pathlib.Path(args['--run-dir'])\n"
        "(run_dir / 'artifacts' / 'results').mkdir(parents=True, exist_ok=True)\n"
        f"per_cell = {per_cell!r}\n"
        "cfg = pathlib.Path(args['--config']).read_text()\n"
        "spec = next((v for marker, v in per_cell.items() if marker in cfg), {})\n"
        "outcome = spec.get('outcome', 'succeeded')\n"
        "manifest = {'outcome': outcome, 'argv': sys.argv[1:]}\n"
        "if outcome == 'degraded':\n"
        "    manifest['phases'] = {'train': {'status': 'ok'}, 'crossval': {'status': 'failed', 'error': 'HTTP 422: boom'}}\n"
        "(run_dir / 'manifest.json').write_text(json.dumps(manifest))\n"
        "cv = None if spec.get('cv_r2') is None else {'eval_aggregate': {'r2': spec['cv_r2']}, 'eval_std': {'r2': spec.get('cv_r2_std', 0.01)}}\n"
        "stats = {'recurrence': {'final_metrics': {'r2': 0.11}, 'crossval': cv, 'dataset_descriptor': {'n_windows': 1522}}}\n"
        "(run_dir / 'artifacts' / 'results' / 'stats.json').write_text(json.dumps(stats))\n"
        "sys.exit(0 if outcome == 'succeeded' else 1)\n"
    )
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _write_cascor_stub_driver(path: Path, per_cell: dict) -> None:
    """``per_cell`` maps a config-text marker to the ``/v1/metrics`` body that cell's run ends with.

    The stub writes a succeeded manifest and a stats.json built by the REAL writer,
    ``stats_summary.build_stats(kind="cascor", metrics_final=...)``, imported by path -- the shape
    ``CASCOR_HEADLINE_PATHS`` reads, produced the way the driver produces it.
    """
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import importlib.util, json, sys, pathlib\n"
        "args = dict(zip(sys.argv[1::2], sys.argv[2::2]))\n"
        "run_dir = pathlib.Path(args['--run-dir'])\n"
        "(run_dir / 'artifacts' / 'results').mkdir(parents=True, exist_ok=True)\n"
        f"per_cell = {per_cell!r}\n"
        "cfg = pathlib.Path(args['--config']).read_text()\n"
        "final = next((v for marker, v in per_cell.items() if marker in cfg), {})\n"
        f"spec = importlib.util.spec_from_file_location('stats_summary_stub', {str(STATS_SUMMARY_PATH)!r})\n"
        "writer = importlib.util.module_from_spec(spec)\n"
        "spec.loader.exec_module(writer)\n"
        "manifest = {'outcome': 'succeeded', 'argv': sys.argv[1:]}\n"
        "(run_dir / 'manifest.json').write_text(json.dumps(manifest))\n"
        "(run_dir / 'artifacts' / 'results' / 'stats.json').write_text(json.dumps(writer.build_stats(manifest, kind='cascor', metrics_final=final)))\n"
        "sys.exit(0)\n"
    )
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _cascor_headline(case: unittest.TestCase, **metrics_final: object) -> dict:
    """``_headline_metrics`` of a run dir whose stats.json the real writer built from this ``/v1/metrics`` body."""
    tmp = tempfile.TemporaryDirectory()
    case.addCleanup(tmp.cleanup)
    run_dir = Path(tmp.name) / "run"
    (run_dir / "artifacts" / "results").mkdir(parents=True)
    manifest = {"run_id": "r", "outcome": "succeeded", "experiment": {"name": "e"}}
    (run_dir / "artifacts" / "results" / "stats.json").write_text(json.dumps(stats_summary.build_stats(manifest, kind="cascor", metrics_final=metrics_final)))
    return run_suite._headline_metrics(run_dir)


class ParseAcceptanceTest(unittest.TestCase):
    """The schema, and that a bad band refuses the suite at load."""

    def test_absent_is_an_empty_list_and_a_good_band_normalises(self) -> None:
        self.assertEqual(run_suite.parse_acceptance(None, "acceptance"), [])
        bands = run_suite.parse_acceptance([{"metric": "cv_r2", "min": -1.0, "max": 0.5, "mode": "gate"}, {"metric": "cv_r2_std", "max": 0.5, "mode": "report"}], "acceptance")
        self.assertEqual(bands, [{"metric": "cv_r2", "min": -1.0, "max": 0.5, "mode": "gate"}, {"metric": "cv_r2_std", "min": None, "max": 0.5, "mode": "report"}])

    def test_every_malformed_shape_is_a_suite_error_naming_the_position(self) -> None:
        bad = [
            ({"metric": "cv_r2", "max": 0.5, "mode": "gate"}, None),  # wrapped below: not a list
            [{"metric": "cv_r2", "max": 0.5}],  # no mode
            [{"metric": "cv_r2", "max": 0.5, "mode": "maybe"}],  # bad mode
            [{"metric": "r2", "max": 0.5, "mode": "gate"}],  # not a headline key
            [{"metric": "cv_r2", "mode": "gate"}],  # no bound
            [{"metric": "cv_r2", "min": 1.0, "max": -1.0, "mode": "gate"}],  # min above max
            [{"metric": "cv_r2", "max": True, "mode": "gate"}],  # bool is not a number
            [{"metric": "cv_r2", "max": float("nan"), "mode": "gate"}],  # not finite
            [{"metric": "cv_r2", "max": 0.5, "mode": "gate", "why": "x"}],  # unknown key
            ["cv_r2 <= 0.5"],  # not a mapping
        ]
        for spec_ in bad:
            with self.subTest(spec=spec_):
                with self.assertRaises(SuiteError) as ctx:
                    run_suite.parse_acceptance(spec_[0] if isinstance(spec_, tuple) else spec_, "include[1].acceptance")
                self.assertIn("include[1].acceptance", str(ctx.exception))

    def test_load_suite_refuses_a_malformed_row_band_before_any_launch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "base.yaml").write_text(BASE_CONFIG)
            suite = root / "suite.yaml"
            suite.write_text(_suite_yaml(root / "base.yaml", root / "out", row_bands=[{"metric": "cv_r2", "max": 0.5}]))
            with self.assertRaises(SuiteError) as ctx:
                run_suite.load_suite(suite)
            self.assertIn("include[1].acceptance[0].mode", str(ctx.exception))
            # And through main: exit 2, nothing written.
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(buf):
                rc = run_suite.main(["--suite", str(suite), "--dry-run"])
            self.assertEqual(rc, 2)
            self.assertFalse((root / "out").exists())

    def test_a_suite_level_band_is_validated_too(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "base.yaml").write_text(BASE_CONFIG)
            suite = root / "suite.yaml"
            suite.write_text(_suite_yaml(root / "base.yaml", root / "out", suite_bands={"metric": "cv_r2"}))
            with self.assertRaises(SuiteError) as ctx:
                run_suite.load_suite(suite)
            self.assertIn("acceptance: must be a list", str(ctx.exception))


class EvaluateAndApplyTest(unittest.TestCase):
    """The comparator and R6's outcome semantics, on rows, with no process launched."""

    def test_the_audited_number_fails_the_r5_band_and_the_bounds_are_inclusive(self) -> None:
        results = run_suite.evaluate_acceptance(R5_BAND, {"cv_r2": -18081.0, "cv_r2_std": 36000.5})
        self.assertEqual([r["result"] for r in results], ["fail", "fail"])
        results = run_suite.evaluate_acceptance(R5_BAND, {"cv_r2": -1.0, "cv_r2_std": 0.5})
        self.assertEqual([r["result"] for r in results], ["pass", "pass"], "the bounds are inclusive")
        results = run_suite.evaluate_acceptance(R5_BAND, {"cv_r2": 0.0, "cv_r2_std": 0.0})
        self.assertEqual([r["result"] for r in results], ["pass", "pass"], "0.0 is a value, not an absence")
        results = run_suite.evaluate_acceptance(R5_BAND, {"cv_r2": 0.975, "cv_r2_std": 0.01})
        self.assertEqual([r["result"] for r in results], ["fail", "pass"], "the control's 0.975 fails +0.5 -- why the band is row-scoped")

    def test_an_absent_metric_is_absent_not_fail(self) -> None:
        results = run_suite.evaluate_acceptance(R5_BAND, {"train_r2": 0.11, "n_windows": 1522})
        self.assertEqual([r["result"] for r in results], ["absent", "absent"])
        self.assertEqual([r["value"] for r in results], [None, None])

    def test_gate_miss_fails_report_miss_flags_and_the_error_names_the_miss(self) -> None:
        row: dict[str, Any] = {"outcome": "succeeded", "metrics": {"cv_r2": -18081.0, "cv_r2_std": 36000.5}}
        run_suite.apply_acceptance(row, R5_BAND)
        self.assertEqual(row["outcome"], "failed")
        self.assertEqual(row["error"], "acceptance: cv_r2=-18081.0 outside [-1.0, 0.5] (gate); cv_r2_std=36000.5 outside <= 0.5 (gate)")
        self.assertEqual([r["result"] for r in row["acceptance"]], ["fail", "fail"])

        row = {"outcome": "succeeded", "metrics": {"cv_r2": -18081.0, "cv_r2_std": 0.01}}
        run_suite.apply_acceptance(row, [{"metric": "cv_r2", "min": -1.0, "max": 0.5, "mode": "report"}])
        self.assertEqual(row["outcome"], "flagged")
        self.assertEqual(row["error"], "acceptance: cv_r2=-18081.0 outside [-1.0, 0.5] (report)")

    def test_absent_follows_the_mode(self) -> None:
        row: dict[str, Any] = {"outcome": "succeeded", "metrics": {"train_r2": 0.11}}
        run_suite.apply_acceptance(row, [{"metric": "cv_r2", "min": -1.0, "max": 0.5, "mode": "gate"}])
        self.assertEqual((row["outcome"], row["error"]), ("failed", "acceptance: cv_r2 absent (gate)"))
        row = {"outcome": "succeeded", "metrics": {"train_r2": 0.11}}
        run_suite.apply_acceptance(row, [{"metric": "cv_r2", "min": -1.0, "max": 0.5, "mode": "report"}])
        self.assertEqual((row["outcome"], row["error"]), ("flagged", "acceptance: cv_r2 absent (report)"))

    def test_a_gate_miss_outranks_a_report_miss_and_a_pass_stays_succeeded(self) -> None:
        bands = [{"metric": "cv_r2", "min": -1.0, "max": 0.5, "mode": "report"}, {"metric": "cv_r2_std", "max": 0.5, "mode": "gate"}]
        row: dict[str, Any] = {"outcome": "succeeded", "metrics": {"cv_r2": -5.0, "cv_r2_std": 8.75}}
        run_suite.apply_acceptance(row, bands)
        self.assertEqual(row["outcome"], "failed")
        self.assertIn("cv_r2_std=8.75 outside <= 0.5 (gate)", row["error"])
        self.assertIn("cv_r2=-5.0 outside [-1.0, 0.5] (report)", row["error"], "the report miss is still named")
        row = {"outcome": "succeeded", "metrics": {"cv_r2": -0.111, "cv_r2_std": 0.041}}
        run_suite.apply_acceptance(row, R5_BAND)
        self.assertEqual(row["outcome"], "succeeded")
        self.assertNotIn("error", row)
        self.assertEqual([r["result"] for r in row["acceptance"]], ["pass", "pass"])

    def test_a_degraded_or_failed_cell_keeps_its_outcome_but_records_the_bands(self) -> None:
        for outcome in ("degraded", "failed", "timed_out"):
            row: dict[str, Any] = {"outcome": outcome, "error": "crossval failed", "metrics": {"train_r2": 0.11}}
            run_suite.apply_acceptance(row, R5_BAND)
            self.assertEqual(row["outcome"], outcome)
            self.assertEqual(row["error"], "crossval failed", "the phase failure stays the finding")
            self.assertEqual([r["result"] for r in row["acceptance"]], ["absent", "absent"])

    def test_no_bands_means_no_acceptance_key(self) -> None:
        row: dict[str, Any] = {"outcome": "succeeded", "metrics": {"cv_r2": -18081.0}}
        run_suite.apply_acceptance(row, [])
        self.assertEqual(row, {"outcome": "succeeded", "metrics": {"cv_r2": -18081.0}})

    def test_flagged_is_terminal_and_complete(self) -> None:
        self.assertIn("flagged", run_suite.TERMINAL_OUTCOMES)
        self.assertEqual(run_suite.COMPLETE_OUTCOMES, frozenset({"succeeded", "flagged"}))


class SuiteLoopAcceptanceTest(unittest.TestCase):
    """End to end through ``main`` with the stubs: registry, index, console, aggregate.csv, REPORT.md, exit code, resume."""

    CONTROL = {"outcome": "succeeded", "cv_r2": 0.975, "cv_r2_std": 0.01}
    BLOWUP = {"outcome": "succeeded", "cv_r2": -18081.0, "cv_r2_std": 36000.5}
    SANE = {"outcome": "succeeded", "cv_r2": -0.111, "cv_r2_std": 0.041}
    NO_CROSSVAL = {"outcome": "succeeded", "cv_r2": None}
    DEGRADED = {"outcome": "degraded", "cv_r2": None}

    def _setup(self, equities: dict, *, row_bands: "list[dict] | None" = None, suite_bands: "list[dict] | None" = None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "base.yaml").write_text(BASE_CONFIG)
        suite_dir = root / "suite-out"
        (root / "suite.yaml").write_text(_suite_yaml(root / "base.yaml", suite_dir, row_bands=row_bands, suite_bands=suite_bands))
        markers = root / "markers"
        markers.mkdir()
        run_root = root / "runroot"
        run_root.mkdir()
        launcher = root / "stub_launcher.bash"
        _write_stub_launcher(launcher, markers)
        driver = root / "stub_driver.py"
        _write_stub_driver(driver, {CONTROL_MARKER: self.CONTROL, EQUITIES_MARKER: equities})
        self._env = {"JUNIPER_SUITE_LAUNCHER": str(launcher), "JUNIPER_SUITE_DRIVER": str(driver), "JUNIPER_SUITE_PYTHON": sys.executable}
        old_root = run_suite.DEFAULT_RUN_ROOT
        run_suite.DEFAULT_RUN_ROOT = run_root  # type: ignore[attr-defined]
        self.addCleanup(lambda: setattr(run_suite, "DEFAULT_RUN_ROOT", old_root))
        return root, suite_dir, markers, run_root

    def _main(self, *argv: str) -> "tuple[int, str]":
        buf = io.StringIO()
        old = {k: os.environ.get(k) for k in self._env}
        os.environ.update(self._env)
        try:
            with redirect_stdout(buf), redirect_stderr(buf):
                rc = run_suite.main(list(argv))
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        return rc, buf.getvalue()

    @staticmethod
    def _registry(suite_dir: Path) -> "dict[str, dict]":
        return {row["name"]: row for row in (json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines())}

    @staticmethod
    def _csv(suite_dir: Path) -> "dict[str, dict]":
        with (suite_dir / "aggregate.csv").open(newline="", encoding="utf-8") as handle:
            return {row["name"]: row for row in csv.DictReader(handle)}

    def test_a_gate_miss_fails_the_row_only_and_the_suite_exits_one(self) -> None:
        root, suite_dir, _, run_root = self._setup(self.BLOWUP, row_bands=R5_BAND)
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 1, msg=out)
        rows = self._registry(suite_dir)
        self.assertEqual(rows["control"]["outcome"], "succeeded", "row-scoped: the control's 0.975 is never judged")
        self.assertNotIn("acceptance", rows["control"])
        self.assertEqual(rows["equities"]["outcome"], "failed")
        self.assertEqual(rows["equities"]["exit_code"], 0, "the DRIVER succeeded; the band failed the row")
        self.assertEqual(rows["equities"]["error"], "acceptance: cv_r2=-18081.0 outside [-1.0, 0.5] (gate); cv_r2_std=36000.5 outside <= 0.5 (gate)")
        self.assertIn("failed (acceptance: cv_r2=-18081.0 outside [-1.0, 0.5] (gate)", out)
        index = [json.loads(line) for line in (run_root / "index.jsonl").read_text().splitlines()]
        # Three cells: the bare base-config cell (the empty matrix yields one), then the two include rows.
        self.assertEqual(sorted(r["outcome"] for r in index), ["failed", "succeeded", "succeeded"], "index.jsonl sees the judged outcome")
        table = self._csv(suite_dir)
        self.assertEqual(table["equities"]["outcome"], "failed")
        self.assertEqual(table["equities"]["acceptance"], rows["equities"]["error"].removeprefix("acceptance: "))
        self.assertEqual(table["control"]["acceptance"], "")
        with (suite_dir / "aggregate.csv").open(newline="", encoding="utf-8") as handle:
            self.assertEqual(next(csv.reader(handle))[-1], "acceptance", "the new column is LAST; nothing before it moves")
        report = (suite_dir / "REPORT.md").read_text()
        self.assertIn("Cells: 3 total, 2 succeeded, 0 degraded, 1 failed/other, 0 not run.", report)
        self.assertIn("## Acceptance bands", report)
        self.assertIn("| cv_r2 | [-1.0, 0.5] | gate | -18081.0 | fail |", report)
        self.assertIn("| cv_r2_std | <= 0.5 | gate | 36000.5 | fail |", report)
        self.assertNotIn("| cv_r2 | [-1.0, 0.5] | gate | 0.975 |", report, "no band row for the control")

    def test_a_report_miss_flags_the_row_and_the_suite_exits_zero(self) -> None:
        band = [{"metric": "cv_r2", "min": -1.0, "max": 0.5, "mode": "report"}]
        root, suite_dir, markers, _ = self._setup(self.BLOWUP, row_bands=band)
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0, msg=out)
        rows = self._registry(suite_dir)
        self.assertEqual(rows["equities"]["outcome"], "flagged")
        self.assertIn("flagged (acceptance: cv_r2=-18081.0 outside [-1.0, 0.5] (report))", out)
        report = (suite_dir / "REPORT.md").read_text()
        self.assertIn("Cells: 3 total, 2 succeeded, 1 flagged, 0 degraded, 0 failed/other, 0 not run.", report)
        self.assertIn("| cv_r2 | [-1.0, 0.5] | report | -18081.0 | fail |", report)
        # Resume: a flagged cell is complete and is not re-run.
        ups = len(list(markers.glob("up-*")))
        rc, out = self._main("--suite", str(root / "suite.yaml"), "--resume", suite_dir.name)
        self.assertEqual(rc, 0, msg=out)
        self.assertEqual(len(list(markers.glob("up-*"))), ups, "resume must not re-run a flagged cell")
        self.assertIn("already flagged — skipped (resume)", out)

    def test_an_absent_metric_follows_the_mode_and_is_not_degraded(self) -> None:
        root, suite_dir, _, _ = self._setup(self.NO_CROSSVAL, row_bands=R5_BAND)
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 1, msg=out)
        row = self._registry(suite_dir)["equities"]
        self.assertEqual((row["outcome"], row["error"]), ("failed", "acceptance: cv_r2 absent (gate); cv_r2_std absent (gate)"))
        self.assertNotIn("phases", row, "absent is a metric judgement, not a phase record")
        self.assertIn("| cv_r2 | [-1.0, 0.5] | gate |  | absent |", (suite_dir / "REPORT.md").read_text())

        root, suite_dir, _, _ = self._setup(self.NO_CROSSVAL, row_bands=[{"metric": "cv_r2", "min": -1.0, "max": 0.5, "mode": "report"}])
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0, msg=out)
        self.assertEqual(self._registry(suite_dir)["equities"]["outcome"], "flagged")

    def test_a_degraded_cell_stays_degraded_with_its_bands_recorded(self) -> None:
        root, suite_dir, _, _ = self._setup(self.DEGRADED, row_bands=R5_BAND)
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 1, msg=out)
        row = self._registry(suite_dir)["equities"]
        self.assertEqual(row["outcome"], "degraded")
        self.assertIn("degraded (crossval failed: HTTP 422: boom)", out)
        self.assertEqual([r["result"] for r in row["acceptance"]], ["absent", "absent"])
        self.assertIn("## Degraded cells", (suite_dir / "REPORT.md").read_text())

    def test_a_sane_row_passes_and_the_report_says_pass(self) -> None:
        root, suite_dir, _, _ = self._setup(self.SANE, row_bands=R5_BAND)
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0, msg=out)
        rows = self._registry(suite_dir)
        self.assertEqual(rows["equities"]["outcome"], "succeeded")
        self.assertEqual([r["result"] for r in rows["equities"]["acceptance"]], ["pass", "pass"])
        self.assertEqual(self._csv(suite_dir)["equities"]["acceptance"], "pass")
        report = (suite_dir / "REPORT.md").read_text()
        self.assertIn("| cv_r2 | [-1.0, 0.5] | gate | -0.111 | pass |", report)
        self.assertIn("| cv_r2_std | <= 0.5 | gate | 0.041 | pass |", report)

    def test_a_suite_level_band_judges_every_cell_which_is_why_r5_is_row_scoped(self) -> None:
        root, suite_dir, _, _ = self._setup(self.SANE, suite_bands=R5_BAND)
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 1, msg=out)
        rows = self._registry(suite_dir)
        self.assertEqual(rows["control"]["outcome"], "failed", "the irregular-sine control's 0.975 fails +0.5")
        self.assertEqual(rows["control"]["error"], "acceptance: cv_r2=0.975 outside [-1.0, 0.5] (gate)")
        self.assertEqual(rows["equities"]["outcome"], "succeeded")

    def test_dry_run_and_the_manifest_show_the_bands_and_the_cell_id_ignores_them(self) -> None:
        root, suite_dir, _, _ = self._setup(self.SANE, row_bands=R5_BAND)
        rc, out = self._main("--suite", str(root / "suite.yaml"), "--dry-run")
        self.assertEqual(rc, 0, msg=out)
        self.assertIn('acceptance=[{"max": 0.5, "metric": "cv_r2", "min": -1.0, "mode": "gate"}', out)
        self.assertEqual(out.count("acceptance="), 1, "only the equities row carries bands")
        doc_with = run_suite.load_suite(root / "suite.yaml")
        with_bands = run_suite.expand_cells(doc_with, root / "suite.yaml")
        (root / "suite.yaml").write_text(_suite_yaml(root / "base.yaml", suite_dir))
        without = run_suite.expand_cells(run_suite.load_suite(root / "suite.yaml"), root / "suite.yaml")
        self.assertEqual([c["cell_id"] for c in with_bands], [c["cell_id"] for c in without], "a band judges the result; it does not change the experiment or its id")
        (root / "suite.yaml").write_text(_suite_yaml(root / "base.yaml", suite_dir, row_bands=R5_BAND))
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0, msg=out)
        manifest = json.loads((suite_dir / "suite_manifest.json").read_text())
        self.assertEqual([len(c["acceptance"]) for c in manifest["cells"]], [0, 0, 2], "the bare base cell, the control row, the equities row")


class CascorBandMetricsTest(unittest.TestCase):
    """APD-ML-002 (owner rulings 1 and 2, 2026-10-26): which names a band may use, now that cascor has columns.

    ``val_accuracy`` became a column (from ``stats["cascor"]["final"]``), so a band on it judges a number
    instead of reading ``absent`` on every cascor cell; ``train_accuracy`` joined it. ``test_accuracy`` stayed
    ACCEPTED with no producer, pending cascor's final evaluation (juniper-cascor#731) and the labelled
    stats block juniper-ml#2064 adds, and said so before any launch. Since juniper-ml#2064 it is a column
    (``CASCOR_TEST_COLUMNS``, with ``test_f1`` / ``test_precision`` / ``test_recall`` / ``test_roc_auc``),
    read only from a final evaluation of the ``test`` split, so it no longer warns. ``final_accuracy``
    exists nowhere and is REFUSED.
    """

    def test_acceptance_metrics_is_the_union_of_the_column_tables_plus_the_pending_names(self) -> None:
        # Stated explicitly, then derived: the literal set is the contract, the union is why it is that set.
        # Until juniper-ml#2064 test_accuracy was the one PENDING name; it now has a column, and the pending set is empty.
        self.assertEqual(run_suite.ACCEPTANCE_METRICS, frozenset({"train_r2", "cv_r2", "cv_r2_std", "n_windows", "train_accuracy", "val_accuracy", "test_accuracy", "test_f1", "test_precision", "test_recall", "test_roc_auc"}))
        tables = {column for column, _ in run_suite.RECURRENCE_HEADLINE_PATHS} | {column for column, _ in run_suite.CASCOR_HEADLINE_PATHS} | {column for column, _ in run_suite.CASCOR_TEST_COLUMNS}
        self.assertEqual(run_suite.ACCEPTANCE_METRICS, frozenset(tables) | frozenset(run_suite.PENDING_ACCEPTANCE_METRICS))
        self.assertEqual(run_suite.PENDING_ACCEPTANCE_METRICS, {}, "test_accuracy, the only pending name, has a column since juniper-ml#2064")
        self.assertIn("test_accuracy", tables)
        self.assertEqual(dict(run_suite.CASCOR_HEADLINE_PATHS), {"train_accuracy": ("final", "train_accuracy"), "val_accuracy": ("final", "val_accuracy")})
        self.assertEqual(dict(run_suite.CASCOR_TEST_COLUMNS), {"test_accuracy": "accuracy", "test_f1": "f1", "test_precision": "precision", "test_recall": "recall", "test_roc_auc": "roc_auc"})
        self.assertEqual(run_suite.CASCOR_HELD_OUT_SPLIT, "test")
        self.assertNotIn("final_accuracy", run_suite.ACCEPTANCE_METRICS)

    def test_final_accuracy_is_refused_with_its_reason_and_a_suite_naming_it_exits_two(self) -> None:
        with self.assertRaises(SuiteError) as ctx:
            run_suite.parse_acceptance([{"metric": "final_accuracy", "min": 0.9, "mode": "gate"}], "acceptance")
        self.assertIn("acceptance[0].metric", str(ctx.exception))
        self.assertIn("got 'final_accuracy' (removed 2026-10-26 (APD-ML-002): no writer has ever produced it", str(ctx.exception))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "base.yaml").write_text(BASE_CONFIG)
            suite = root / "suite.yaml"
            suite.write_text(_suite_yaml(root / "base.yaml", root / "out", row_bands=[{"metric": "final_accuracy", "min": 0.9, "mode": "report"}]))
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(buf):
                rc = run_suite.main(["--suite", str(suite), "--dry-run"])
            self.assertEqual(rc, 2, msg=buf.getvalue())
            self.assertIn("include[1].acceptance[0].metric", buf.getvalue())
            self.assertFalse((root / "out").exists())

    def test_a_val_accuracy_band_passes_or_fails_and_is_never_absent(self) -> None:
        metrics = _cascor_headline(self, train_accuracy=0.905, val_accuracy=0.91875, f1=0.9187)
        self.assertEqual(metrics, {"train_accuracy": 0.905, "val_accuracy": 0.91875})
        bands = [{"metric": "val_accuracy", "min": 0.9, "max": None, "mode": "gate"}, {"metric": "val_accuracy", "min": 0.95, "max": None, "mode": "gate"}, {"metric": "val_accuracy", "min": None, "max": 0.91875, "mode": "gate"}, {"metric": "train_accuracy", "min": 0.91, "max": None, "mode": "report"}]
        results = run_suite.evaluate_acceptance(bands, metrics)
        self.assertEqual([(r["result"], r["value"]) for r in results], [("pass", 0.91875), ("fail", 0.91875), ("pass", 0.91875), ("fail", 0.905)])
        row: dict[str, Any] = {"outcome": "succeeded", "metrics": metrics}
        run_suite.apply_acceptance(row, bands[:2])
        self.assertEqual((row["outcome"], row["error"]), ("failed", "acceptance: val_accuracy=0.91875 outside >= 0.95 (gate)"))

    def test_test_accuracy_is_accepted_and_reads_absent_until_its_producer_lands(self) -> None:
        bands = run_suite.parse_acceptance([{"metric": "test_accuracy", "min": 0.5, "mode": "gate"}], "acceptance")
        self.assertEqual(bands, [{"metric": "test_accuracy", "min": 0.5, "max": None, "mode": "gate"}])
        # A full writer-built cascor block, eval scalars and all: still no test_accuracy anywhere.
        metrics = _cascor_headline(self, train_accuracy=0.905, val_accuracy=0.91875, f1=0.9187, precision=0.92, recall=0.9175, roc_auc=0.9808)
        row: dict[str, Any] = {"outcome": "succeeded", "metrics": metrics}
        run_suite.apply_acceptance(row, bands)
        self.assertEqual((row["outcome"], row["error"]), ("failed", "acceptance: test_accuracy absent (gate)"))
        row = {"outcome": "succeeded", "metrics": metrics}
        run_suite.apply_acceptance(row, [{**bands[0], "mode": "report"}])
        self.assertEqual((row["outcome"], row["error"]), ("flagged", "acceptance: test_accuracy absent (report)"))

    def test_a_band_on_test_accuracy_no_longer_warns(self) -> None:
        # juniper-ml#2064 gave test_accuracy a column, so it left the pending set and its pre-launch warning went with it.
        cells = [{"acceptance": [{"metric": "test_accuracy", "min": 0.5, "max": None, "mode": "gate"}]}, {"acceptance": [{"metric": "test_f1", "min": 0.6, "max": None, "mode": "report"}]}]
        self.assertEqual(run_suite.pending_band_warnings(cells), [])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "base.yaml").write_text(BASE_CONFIG)
            suite = root / "suite.yaml"
            suite.write_text(_suite_yaml(root / "base.yaml", root / "out", suite_bands=[{"metric": "test_accuracy", "min": 0.5, "mode": "report"}]))
            buf = io.StringIO()
            with redirect_stdout(buf), redirect_stderr(buf):
                rc = run_suite.main(["--suite", str(suite), "--dry-run"])
            out = buf.getvalue()
            self.assertEqual(rc, 0, msg=out)
            self.assertIn("suite t-acc (cascor): 3 cells", out)
            self.assertNotIn("[suite] warning", out)

    def test_a_pending_name_warns_once_before_anything_launches(self) -> None:
        # The facility outlives its first name (test_accuracy, until juniper-ml#2064): a name a ruling accepts ahead of
        # its producer still warns once per metric, before the plan, under --dry-run. `future_accuracy` stands in for it.
        pending = {"future_accuracy": "a ruling accepted it ahead of its producer"}
        with unittest.mock.patch.dict(run_suite.PENDING_ACCEPTANCE_METRICS, pending), unittest.mock.patch.object(run_suite, "ACCEPTANCE_METRICS", run_suite.ACCEPTANCE_METRICS | frozenset(pending)):
            cells = [{"acceptance": [{"metric": "future_accuracy", "min": 0.5, "max": None, "mode": "gate"}, {"metric": "val_accuracy", "min": 0.5, "max": None, "mode": "gate"}]}, {"acceptance": [{"metric": "future_accuracy", "min": 0.6, "max": None, "mode": "report"}]}, {"acceptance": []}]
            warnings = run_suite.pending_band_warnings(cells)
            self.assertEqual(len(warnings), 1, warnings)
            self.assertIn("names future_accuracy on 2 of 3 cell(s), and no run produces it yet: a ruling accepted it ahead of its producer", warnings[0])
            self.assertIn("a `gate` band fails its cell", warnings[0])
            self.assertEqual(run_suite.pending_band_warnings([{"acceptance": [{"metric": "val_accuracy", "min": 0.5, "max": None, "mode": "gate"}]}]), [])
            with tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / "base.yaml").write_text(BASE_CONFIG)
                suite = root / "suite.yaml"
                suite.write_text(_suite_yaml(root / "base.yaml", root / "out", suite_bands=[{"metric": "future_accuracy", "min": 0.5, "mode": "report"}]))
                buf = io.StringIO()
                with redirect_stdout(buf), redirect_stderr(buf):
                    rc = run_suite.main(["--suite", str(suite), "--dry-run"])
                out = buf.getvalue()
                self.assertEqual(rc, 0, msg=out)
                self.assertEqual(out.count("[suite] warning: an acceptance band names future_accuracy on 3 of 3 cell(s)"), 1, out)
                self.assertLess(out.index("[suite] warning:"), out.index("suite t-acc (cascor): 3 cells"), "the warning comes before the plan")


class NonFiniteBandValueTest(unittest.TestCase):
    """APD-ML-002 ruling 4 (2026-10-26): a NaN or infinite value fails ANY band.

    The plain comparison let each of them through somewhere -- every comparison with NaN is false, so NaN
    passed ``min`` and ``max`` alike; ``+inf`` passed a ``min`` band and ``-inf`` a ``max`` band.
    """

    BANDS = [{"metric": "val_accuracy", "min": 0.9, "max": None, "mode": "gate"}, {"metric": "val_accuracy", "min": None, "max": 0.99, "mode": "gate"}, {"metric": "val_accuracy", "min": 0.0, "max": 1.0, "mode": "gate"}]

    def test_nan_and_both_infinities_fail_min_max_and_two_sided_bands(self) -> None:
        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                results = run_suite.evaluate_acceptance(self.BANDS, {"val_accuracy": value})
                self.assertEqual([r["result"] for r in results], ["fail", "fail", "fail"])
                for result in results:
                    self.assertIs(result["value"], value, "the value is kept so the report prints it, not blanked as absent")

    def test_finite_values_still_compare_and_a_huge_int_does_not_overflow(self) -> None:
        self.assertEqual([r["result"] for r in run_suite.evaluate_acceptance(self.BANDS, {"val_accuracy": 0.95})], ["pass", "pass", "pass"])
        self.assertEqual([r["result"] for r in run_suite.evaluate_acceptance([{"metric": "n_windows", "min": 1.0, "max": None, "mode": "gate"}], {"n_windows": 10**400})], ["pass"])

    def test_a_nan_fails_the_cell_under_gate_and_flags_it_under_report(self) -> None:
        row: dict[str, Any] = {"outcome": "succeeded", "metrics": {"val_accuracy": float("nan")}}
        run_suite.apply_acceptance(row, [self.BANDS[0]])
        self.assertEqual((row["outcome"], row["error"]), ("failed", "acceptance: val_accuracy=nan outside >= 0.9 (gate)"))
        row = {"outcome": "succeeded", "metrics": {"cv_r2": float("inf")}}
        run_suite.apply_acceptance(row, [{"metric": "cv_r2", "min": -1.0, "max": None, "mode": "report"}])
        self.assertEqual((row["outcome"], row["error"]), ("flagged", "acceptance: cv_r2=inf outside >= -1.0 (report)"))

    def test_a_nan_in_stats_json_reaches_the_band_as_a_fail(self) -> None:
        metrics = _cascor_headline(self, train_accuracy=0.9, val_accuracy=float("nan"))
        self.assertEqual([r["result"] for r in run_suite.evaluate_acceptance([self.BANDS[0]], metrics)], ["fail"])


class CascorSuiteLoopAcceptanceTest(unittest.TestCase):
    """End to end through ``main`` on a CASCOR suite (stub launcher + a stub driver that writes stats.json with the real writer)."""

    LIVE = {"epoch": 17, "train_loss": 0.067, "train_accuracy": 0.905, "val_loss": 0.069, "val_accuracy": 0.91875, "hidden_units": 16, "f1": 0.9187}
    WEAK = {"epoch": 9, "train_loss": 0.21, "train_accuracy": 0.86, "val_loss": 0.24, "val_accuracy": 0.85, "hidden_units": 8, "f1": 0.84}
    # juniper-ml#2064: `/v1/metrics` bodies carrying cascor's final evaluation, keyed as juniper-cascor main's
    # `_compute_final_eval_metrics` builds it (#731 adds `accuracy`). LIVE's final block scored the TEST split; WEAK's
    # scored VALIDATION (no test split loaded), with an accuracy that would pass the band below if it were misread.
    LIVE_HELD_OUT = {**LIVE, "eval_metrics": {"enabled": True, "average": "macro", "split": "validation", "n_samples": 160, "n_classes": 2, "undefined": {}, "final": {"f1": 0.8997, "precision": 0.902, "recall": 0.8994, "roc_auc": 0.9605, "average": "macro", "n_samples": 120, "n_classes": 2, "undefined": {}, "accuracy": 0.9, "split": "test", "final": True}}}
    WEAK_VALIDATION_ONLY = {**WEAK, "eval_metrics": {"enabled": True, "average": "macro", "split": "validation", "n_samples": 80, "n_classes": 2, "undefined": {}, "final": {"f1": 0.96, "precision": 0.96, "recall": 0.96, "roc_auc": 0.99, "average": "macro", "n_samples": 80, "n_classes": 2, "undefined": {}, "accuracy": 0.97, "split": "validation", "final": True}}}

    def _run(self, *, suite_bands: "list[dict]", bodies: "dict | None" = None) -> "tuple[int, str, Path]":
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "base.yaml").write_text(BASE_CONFIG)
        suite_dir = root / "suite-out"
        (root / "suite.yaml").write_text(_suite_yaml(root / "base.yaml", suite_dir, suite_bands=suite_bands))
        markers = root / "markers"
        markers.mkdir()
        run_root = root / "runroot"
        run_root.mkdir()
        _write_stub_launcher(root / "stub_launcher.bash", markers)
        _write_cascor_stub_driver(root / "stub_driver.py", bodies if bodies is not None else {CONTROL_MARKER: self.LIVE, EQUITIES_MARKER: self.WEAK})
        env = {"JUNIPER_SUITE_LAUNCHER": str(root / "stub_launcher.bash"), "JUNIPER_SUITE_DRIVER": str(root / "stub_driver.py"), "JUNIPER_SUITE_PYTHON": sys.executable}
        old_root = run_suite.DEFAULT_RUN_ROOT
        run_suite.DEFAULT_RUN_ROOT = run_root  # type: ignore[attr-defined]
        self.addCleanup(lambda: setattr(run_suite, "DEFAULT_RUN_ROOT", old_root))
        old_env = {key: os.environ.get(key) for key in env}
        os.environ.update(env)
        buf = io.StringIO()
        try:
            with redirect_stdout(buf), redirect_stderr(buf):
                rc = run_suite.main(["--suite", str(root / "suite.yaml")])
        finally:
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        return rc, buf.getvalue(), suite_dir

    def test_a_val_accuracy_gate_band_passes_and_fails_real_cascor_cells(self) -> None:
        rc, out, suite_dir = self._run(suite_bands=[{"metric": "val_accuracy", "min": 0.9, "mode": "gate"}])
        self.assertEqual(rc, 1, msg=out)
        rows = {row["name"]: row for row in (json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines())}
        self.assertEqual(rows["control"]["metrics"], {"train_accuracy": 0.905, "val_accuracy": 0.91875})
        self.assertEqual((rows["control"]["outcome"], [r["result"] for r in rows["control"]["acceptance"]]), ("succeeded", ["pass"]))
        self.assertEqual((rows["equities"]["outcome"], rows["equities"]["error"]), ("failed", "acceptance: val_accuracy=0.85 outside >= 0.9 (gate)"))
        with (suite_dir / "aggregate.csv").open(newline="", encoding="utf-8") as handle:
            table = {row["name"]: row for row in csv.DictReader(handle)}
        self.assertEqual((table["control"]["val_accuracy"], table["equities"]["val_accuracy"], table["equities"]["train_accuracy"]), ("0.91875", "0.85", "0.86"))
        report = (suite_dir / "REPORT.md").read_text()
        self.assertIn("| val_accuracy | >= 0.9 | gate | 0.91875 | pass |", report)
        self.assertIn("| val_accuracy | >= 0.9 | gate | 0.85 | fail |", report)
        self.assertNotIn("| absent |", report, "a cascor val_accuracy band never reads absent any more")

    def test_a_test_accuracy_band_reads_absent_without_a_held_out_block_and_flags_every_cell(self) -> None:
        # LIVE / WEAK carry in-loop scalars and no final evaluation: test_accuracy is absent on every cell. Until
        # juniper-ml#2064 this also printed a pending-metric warning; test_accuracy has a column now, so it does not.
        rc, out, suite_dir = self._run(suite_bands=[{"metric": "test_accuracy", "min": 0.5, "mode": "report"}])
        self.assertEqual(rc, 0, msg=out)
        self.assertNotIn("[suite] warning", out)
        outcomes = [json.loads(line)["outcome"] for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        self.assertEqual(outcomes, ["flagged", "flagged", "flagged"])
        self.assertIn("| test_accuracy | >= 0.5 | report |  | absent |", (suite_dir / "REPORT.md").read_text())

    def test_a_test_accuracy_band_judges_the_held_out_test_block_and_never_a_validation_one(self) -> None:
        # juniper-ml#2064: the band judges the final evaluation of the TEST split. The validation-split block's 0.97
        # would pass the band; it must read absent instead, so the gate fails that cell.
        rc, out, suite_dir = self._run(suite_bands=[{"metric": "test_accuracy", "min": 0.85, "mode": "gate"}], bodies={CONTROL_MARKER: self.LIVE_HELD_OUT, EQUITIES_MARKER: self.WEAK_VALIDATION_ONLY})
        self.assertEqual(rc, 1, msg=out)
        self.assertNotIn("[suite] warning", out)
        rows = {row["name"]: row for row in (json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines())}
        self.assertEqual(rows["control"]["metrics"], {"train_accuracy": 0.905, "val_accuracy": 0.91875, "test_accuracy": 0.9, "test_f1": 0.8997, "test_precision": 0.902, "test_recall": 0.8994, "test_roc_auc": 0.9605})
        self.assertEqual((rows["control"]["outcome"], [r["result"] for r in rows["control"]["acceptance"]]), ("succeeded", ["pass"]))
        self.assertEqual(rows["equities"]["metrics"], {"train_accuracy": 0.86, "val_accuracy": 0.85}, "a validation block fills no test_* column")
        self.assertEqual((rows["equities"]["outcome"], rows["equities"]["error"]), ("failed", "acceptance: test_accuracy absent (gate)"))
        with (suite_dir / "aggregate.csv").open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            header = list(reader.fieldnames or [])
            table = {row["name"]: row for row in reader}
        self.assertEqual([column for column in header if column.startswith("test_")], ["test_accuracy", "test_f1", "test_precision", "test_recall", "test_roc_auc"])
        self.assertEqual([table["control"][column] for column in ("test_accuracy", "test_f1", "test_roc_auc")], ["0.9", "0.8997", "0.9605"])
        self.assertEqual([table["equities"][column] for column in ("test_accuracy", "test_f1", "test_precision", "test_recall", "test_roc_auc")], ["", "", "", "", ""])
        report = (suite_dir / "REPORT.md").read_text()
        self.assertIn("| test_accuracy | >= 0.85 | gate | 0.9 | pass |", report)
        self.assertIn("| test_accuracy | >= 0.85 | gate |  | absent |", report, "the validation block's 0.97 reaches no column and no band")


class ShippedEHBandTest(unittest.TestCase):
    """The E-H recurrence suite on disk carries R5's band, on the equities row only."""

    def test_the_eh_equities_row_carries_the_r5_band_and_nothing_else_does(self) -> None:
        doc = run_suite.load_suite(EH_SUITE)
        cells = run_suite.expand_cells(doc, EH_SUITE)
        banded = [c for c in cells if c["acceptance"]]
        self.assertEqual([c["name"] for c in banded], ["equities-seq-aapl"])
        self.assertEqual(
            banded[0]["acceptance"],
            [{"metric": "cv_r2", "min": -1.0, "max": 0.5, "mode": "gate"}, {"metric": "cv_r2_std", "min": None, "max": 0.5, "mode": "gate"}],
        )
        self.assertEqual(doc.get("acceptance"), None, "no suite-level band: the irregular-sine control's cv_r2 0.975 would fail +0.5")


if __name__ == "__main__":
    unittest.main()
