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
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "util" / "experiments" / "run_suite.py"
EH_SUITE = REPO_ROOT / "util" / "experiments" / "suites" / "p4" / "e-h-recurrence-real-data.yaml"

spec = importlib.util.spec_from_file_location("run_suite_acceptance", MODULE_PATH)
run_suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_suite)

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
