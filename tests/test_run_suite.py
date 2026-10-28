"""Tests for ``util/experiments/run_suite.py`` (CLI experimentation plan §13.1/§13.2, Wave 7.1).

``util/`` is not pre-commit-lint-gated, so this unittest is the gate. Everything
is hermetic: the launcher and driver are PATH-less stub scripts injected via the
``JUNIPER_SUITE_LAUNCHER`` / ``JUNIPER_SUITE_DRIVER`` seams, and the run root is
redirected by patching the module's ``DEFAULT_RUN_ROOT`` — no live stack, no
live services, no writes outside tempdirs.
"""

from __future__ import annotations

import csv
import importlib.util
import io
import json
import math
import os
import re
import stat
import sys
import tempfile
import unittest
import unittest.mock
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

from tests.cascor_eval_fixtures import METRICS_FINAL_NULL_FINAL, METRICS_FINAL_PRE_SWITCH, METRICS_FINAL_TEST_SPLIT, METRICS_FINAL_VALIDATION_SPLIT, V1_STATS_CASCOR, with_final_accuracy
from tests.redacted_env import RedactedEnv

REPO_ROOT = Path(__file__).resolve().parent.parent
MODULE_PATH = REPO_ROOT / "util" / "experiments" / "run_suite.py"

spec = importlib.util.spec_from_file_location("run_suite", MODULE_PATH)
run_suite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(run_suite)


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

# per_run_timeout_seconds clears BASE_CONFIG's 390 s worst-case driver budget, or run_suite refuses the
# suite before any cell launches (juniper-ml#2210; the 180 s of health waits alone exceed the 60 it was).
SUITE_TEMPLATE = """\
schema_version: 1
suite:
  name: t-suite
  description: test
  app: cascor
  base_config:
    - {base}
  seed_policy: {seed_policy}
execution:
  mode: sequential
  continue_on_failure: {cof}
  per_run_timeout_seconds: 900
matrix:
  training.params.max_hidden_units: [2, 4]
outputs:
  suite_dir: {suite_dir}
"""


def _write_stub_launcher(path: Path, marker_dir: Path, fail_up: bool = False) -> None:
    path.write_text("#!/usr/bin/env bash\n" f"MARKERS={marker_dir}\n" 'if [[ "$1" == "--up" ]]; then\n' f"  {'exit 1' if fail_up else ''}\n" '  touch "$MARKERS/up-$$"\n' '  echo "=== Experiment run stub-run-$$ is up ==="\n' "  exit 0\n" "fi\n" 'if [[ "$1" == "--down" ]]; then touch "$MARKERS/down-$2"; exit 0; fi\n' "exit 2\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


def _write_stub_driver(path: Path, outcome: str = "succeeded", per_cell: "dict | None" = None, manifest_extra: "dict | None" = None) -> None:
    """``manifest_extra`` maps an outcome to extra manifest keys written with it -- the W0.3 arms
    use it to give a ``degraded`` cell the per-phase record the real driver writes."""
    path.write_text(
        "#!/usr/bin/env python3\n"
        "import json, sys, pathlib\n"
        "args = dict(zip(sys.argv[1::2], sys.argv[2::2]))\n"
        "run_dir = pathlib.Path(args['--run-dir'])\n"
        "run_dir.mkdir(parents=True, exist_ok=True)\n"
        f"per_cell = {per_cell!r}\n"
        f"outcome = {outcome!r}\n"
        f"manifest_extra = {manifest_extra!r} or {{}}\n"
        "cfg = pathlib.Path(args['--config']).read_text()\n"
        "if per_cell:\n"
        "    for token, oc in per_cell.items():\n"
        "        if token in cfg:\n"
        "            outcome = oc\n"
        # argv is recorded so tests can assert what the suite actually forwarded to the
        # driver (e.g. --stall-seconds); run_suite reads only 'outcome' and 'phases' from the manifest.
        "(run_dir / 'manifest.json').write_text(json.dumps({'outcome': outcome, 'argv': sys.argv[1:], **manifest_extra.get(outcome, {})}))\n"
        "sys.exit(0 if outcome == 'succeeded' else 1)\n"
    )
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


class ExpandTest(unittest.TestCase):
    def _doc(self, extra: str = "") -> "tuple[dict, Path]":
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        (root / "base.yaml").write_text(BASE_CONFIG)
        suite_yaml = root / "suite.yaml"
        suite_yaml.write_text("schema_version: 1\n" "suite:\n  name: s\n  app: cascor\n  base_config: [base.yaml]\n" "matrix:\n  training.params.max_hidden_units: [4, 8, 16]\n  training.params.candidate_pool_size: [4, 8]\n" + extra)
        return run_suite.load_suite(suite_yaml), suite_yaml

    def test_product_exclude_include_and_determinism(self) -> None:
        doc, path = self._doc("exclude:\n  - {training.params.max_hidden_units: 16, training.params.candidate_pool_size: 8}\ninclude:\n  - name: extra\n    overrides: {training.params.max_hidden_units: 32}\n")
        cells = run_suite.expand_cells(doc, path)
        self.assertEqual(len(cells), 3 * 2 - 1 + 1)
        self.assertEqual(cells[-1]["name"], "extra")
        again = run_suite.expand_cells(doc, path)
        self.assertEqual([c["cell_id"] for c in cells], [c["cell_id"] for c in again])
        self.assertNotIn({"training.params.max_hidden_units": 16, "training.params.candidate_pool_size": 8}, [c["overrides"] for c in cells])

    def _resolve_with_project_dir(self, suite_yaml: "Path", config_rel: str, project_dir: "str | None"):
        """Call _resolve_base_config with JUNIPER_EXP_PROJECT_DIR set, restoring it after."""
        old = os.environ.get("JUNIPER_EXP_PROJECT_DIR")
        if project_dir is None:
            os.environ.pop("JUNIPER_EXP_PROJECT_DIR", None)
        else:
            os.environ["JUNIPER_EXP_PROJECT_DIR"] = project_dir
        try:
            return run_suite._resolve_base_config(suite_yaml, config_rel)
        finally:
            if old is None:
                os.environ.pop("JUNIPER_EXP_PROJECT_DIR", None)
            else:
                os.environ["JUNIPER_EXP_PROJECT_DIR"] = old

    def test_project_dir_override_beats_a_resolving_literal(self) -> None:
        """The override WINS over a literal that exists -- it is an override, not a fallback.

        Launched from the canonical juniper-ml checkout the literal always resolves, so while
        the override was consulted second, a campaign pinning cascor to a worktree took its
        CODE from the worktree and its CONFIG from the primary. Nothing in the manifest showed
        that mixed tree, which is why this is pinned rather than left to review.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "../cascor-checkouts/juniper-cascor/conf/experiments/base.yaml"
            suite_dir = root / "suites"
            suite_dir.mkdir(parents=True)
            suite_yaml = suite_dir / "suite.yaml"
            suite_yaml.write_text("schema_version: 1\n")

            primary = root / "cascor-checkouts" / "juniper-cascor" / "conf" / "experiments"
            primary.mkdir(parents=True)
            (primary / "base.yaml").write_text(BASE_CONFIG)
            # Precondition: the literal walk really does resolve, so the test is not vacuous.
            self.assertTrue((suite_yaml.parent / rel).resolve().is_file())

            pinned = root / "pinned" / "juniper-cascor" / "conf" / "experiments"
            pinned.mkdir(parents=True)
            (pinned / "base.yaml").write_text(BASE_CONFIG)

            self.assertEqual(self._resolve_with_project_dir(suite_yaml, rel, str(root / "pinned")), pinned / "base.yaml")
            # Unset, the literal still wins -- the override changes nothing when absent.
            self.assertEqual(self._resolve_with_project_dir(suite_yaml, rel, None), (primary / "base.yaml").resolve())

    def test_a_nonexistent_override_falls_back_to_the_literal(self) -> None:
        """A stale or mistyped override degrades to the literal rather than failing the suite."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rel = "../cascor-checkouts/juniper-cascor/conf/experiments/base.yaml"
            suite_dir = root / "suites"
            suite_dir.mkdir(parents=True)
            suite_yaml = suite_dir / "suite.yaml"
            suite_yaml.write_text("schema_version: 1\n")
            primary = root / "cascor-checkouts" / "juniper-cascor" / "conf" / "experiments"
            primary.mkdir(parents=True)
            (primary / "base.yaml").write_text(BASE_CONFIG)

            resolved = self._resolve_with_project_dir(suite_yaml, rel, str(root / "does-not-exist"))
            self.assertEqual(resolved, (primary / "base.yaml").resolve())

    def test_project_dir_rebase_for_sibling_base_configs(self) -> None:
        """Wave 7.3: from a worktree, sibling-relative base_config paths rebase onto
        JUNIPER_EXP_PROJECT_DIR from their first juniper-* component; cell ids hash
        the RELATIVE reference so they match the canonical checkout's."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            eco = root / "ecosystem" / "juniper-cascor" / "conf" / "experiments"
            eco.mkdir(parents=True)
            (eco / "base.yaml").write_text(BASE_CONFIG)
            suite_dir = root / "elsewhere" / "suites"
            suite_dir.mkdir(parents=True)
            suite_yaml = suite_dir / "suite.yaml"
            suite_yaml.write_text("schema_version: 1\nsuite:\n  name: s\n  app: cascor\n  base_config: [../../../../juniper-cascor/conf/experiments/base.yaml]\nmatrix:\n  training.params.max_hidden_units: [2]\n")
            doc = run_suite.load_suite(suite_yaml)
            old = os.environ.get("JUNIPER_EXP_PROJECT_DIR")
            os.environ["JUNIPER_EXP_PROJECT_DIR"] = str(root / "ecosystem")
            try:
                cells = run_suite.expand_cells(doc, suite_yaml)
            finally:
                if old is None:
                    os.environ.pop("JUNIPER_EXP_PROJECT_DIR", None)
                else:
                    os.environ["JUNIPER_EXP_PROJECT_DIR"] = old
            self.assertEqual(cells[0]["config_path"], str(eco / "base.yaml"))

    def test_validation_rejections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bad = root / "bad.yaml"
            for body, msg in (
                ("schema_version: 2\nsuite: {name: s, app: cascor, base_config: [b]}\n", "schema_version"),
                ("schema_version: 1\nsuite: {name: s, app: nope, base_config: [b]}\n", "app"),
                ("schema_version: 1\nsuite: {name: s, app: cascor, base_config: []}\n", "base_config"),
                ("schema_version: 1\nsuite: {name: s, app: cascor, base_config: [b]}\nexecution: {mode: bogus}\n", "sequential.*parallel"),
                # The cascor-parallel case moved to CascorParallelFloorTest: since the Q-6 floor
                # landed its outcome depends on the resolved cascor tree's VERSION, so asserted
                # here it would pass or fail according to whether the host happens to have a
                # juniper-cascor sibling — the environment-dependent-test class.
                ("schema_version: 1\nsuite: {name: s, app: recurrence, base_config: [b]}\nexecution: {mode: parallel, max_parallel: 0}\n", "max_parallel"),
                ("schema_version: 1\nsuite: {name: s, app: cascor, base_config: [b]}\nbogus: {}\n", "unknown"),
            ):
                bad.write_text(body)
                with self.assertRaisesRegex(run_suite.SuiteError, msg):
                    run_suite.load_suite(bad)


class GrafanaBridgeToggleTest(unittest.TestCase):
    """``JUNIPER_SUITE_GRAFANA_BRIDGE`` adds ``--grafana-bridge`` to ``--up``, and is off by default.

    PF-1's first execution produced ``metrics_scraped`` with no scrape because the launcher was
    never given the flag — `run_suite` had no way to pass it. These pin both directions, and pin
    that the toggle does NOT alter the cell YAML: it is an env toggle precisely so a bridged and an
    unbridged run of the same scenario keep an identical ``config_sha256`` and stay comparable.
    """

    STUB = "#!/usr/bin/env bash\n" 'printf "%s\\n" "$@" >> "$ARGV_LOG"\n' 'if [[ "$1" == "--up" ]]; then echo "=== Experiment run STUBRUN is up ==="; exit 0; fi\n' "exit 0\n"

    def _run_one(self, root: Path, bridge_value: "str | None") -> "list[str]":
        launcher = root / "stub_launcher.sh"
        launcher.write_text(self.STUB)
        launcher.chmod(launcher.stat().st_mode | stat.S_IEXEC)
        driver = root / "stub_driver.py"
        _write_stub_driver(driver)
        argv_log = root / "argv.txt"
        argv_log.write_text("")

        saved = os.environ.get("JUNIPER_SUITE_GRAFANA_BRIDGE")
        os.environ["ARGV_LOG"] = str(argv_log)
        if bridge_value is None:
            os.environ.pop("JUNIPER_SUITE_GRAFANA_BRIDGE", None)
        else:
            os.environ["JUNIPER_SUITE_GRAFANA_BRIDGE"] = bridge_value
        try:
            cell_yaml = root / "cell.yaml"
            cell_yaml.write_text(BASE_CONFIG)
            cell = {"cell_id": "c000-aaaa1111", "index": 0, "name": None, "overrides": {}}
            row = run_suite.execute_cell(cell, cell_yaml, "cascor", 60.0, launcher, driver, sys.executable)
            self.assertIn("grafana_bridge", row, "the registry row must record whether the bridge was on")
        finally:
            os.environ.pop("ARGV_LOG", None)
            if saved is None:
                os.environ.pop("JUNIPER_SUITE_GRAFANA_BRIDGE", None)
            else:
                os.environ["JUNIPER_SUITE_GRAFANA_BRIDGE"] = saved
        return argv_log.read_text().splitlines()

    def test_absent_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            argv = self._run_one(Path(tmp), None)
            self.assertIn("--up", argv)
            self.assertNotIn("--grafana-bridge", argv)

    def test_present_when_enabled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            argv = self._run_one(Path(tmp), "1")
            self.assertIn("--grafana-bridge", argv)

    def test_falsey_values_do_not_enable_it(self) -> None:
        """An unset-like value must not silently switch on a host-dependent capability."""
        for value in ("0", "", "false", "no"):
            with tempfile.TemporaryDirectory() as tmp:
                argv = self._run_one(Path(tmp), value)
                self.assertNotIn("--grafana-bridge", argv, f"{value!r} must not enable the bridge")

    def _row_for(self, root: Path, bridge_value: "str | None") -> dict:
        """Run one cell through execute_cell and return its registry row."""
        launcher = root / "stub_launcher.sh"
        launcher.write_text(self.STUB)
        launcher.chmod(launcher.stat().st_mode | stat.S_IEXEC)
        driver = root / "stub_driver.py"
        _write_stub_driver(driver)
        saved = os.environ.get("JUNIPER_SUITE_GRAFANA_BRIDGE")
        os.environ["ARGV_LOG"] = str(root / "argv.txt")
        if bridge_value is None:
            os.environ.pop("JUNIPER_SUITE_GRAFANA_BRIDGE", None)
        else:
            os.environ["JUNIPER_SUITE_GRAFANA_BRIDGE"] = bridge_value
        try:
            cell_yaml = root / "cell.yaml"
            cell_yaml.write_text(BASE_CONFIG)
            cell = {"cell_id": "c000-aaaa1111", "index": 0, "name": None, "overrides": {}}
            return run_suite.execute_cell(cell, cell_yaml, "cascor", 60.0, launcher, driver, sys.executable)
        finally:
            os.environ.pop("ARGV_LOG", None)
            if saved is None:
                os.environ.pop("JUNIPER_SUITE_GRAFANA_BRIDGE", None)
            else:
                os.environ["JUNIPER_SUITE_GRAFANA_BRIDGE"] = saved

    def test_toggle_does_not_change_the_cell_config_hash(self) -> None:
        """The comparability property, exercised through execute_cell rather than asserted.

        This is the reason the toggle is an env var and not a suite key: a bridged and an
        unbridged run of the same scenario must remain strictly comparable, which means the cell
        config — and therefore ``config_sha256`` — cannot differ between them. Hashing two files
        this test wrote itself would prove nothing; both rows must come from real calls.
        """
        with tempfile.TemporaryDirectory() as tmp_off, tempfile.TemporaryDirectory() as tmp_on:
            off = self._row_for(Path(tmp_off), None)
            on = self._row_for(Path(tmp_on), "1")
            self.assertFalse(off["grafana_bridge"])
            self.assertTrue(on["grafana_bridge"])
            self.assertEqual(off["config_sha256"], on["config_sha256"], "the bridge toggle must not perturb the cell config")


class CascorParallelFloorTest(unittest.TestCase):
    """Q-6: cascor parallel cells are gated on the LAUNCHED tree's version, and fail closed.

    Every case pins ``JUNIPER_EXP_CASCOR_SRC_DIR`` at a tree this test builds, so the outcome
    never depends on whether the host has a juniper-cascor sibling checkout. Asserting the old
    blanket refusal without that pin is what made the previous placement environment-dependent.
    """

    SUITE = "schema_version: 1\n" "suite: {{name: s, app: cascor, base_config: [b]}}\n" "execution: {{mode: {mode}, max_parallel: {par}}}\n"

    def setUp(self) -> None:
        self._saved = {k: os.environ.get(k) for k in ("JUNIPER_EXP_CASCOR_SRC_DIR", "JUNIPER_EXP_PROJECT_DIR")}

    def tearDown(self) -> None:
        for key, val in self._saved.items():
            if val is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = val

    def _tree(self, root: Path, version: "str | None") -> Path:
        tree = root / "juniper-cascor"
        (tree / "src").mkdir(parents=True, exist_ok=True)
        if version is not None:
            (tree / "pyproject.toml").write_text(f'[project]\nname = "juniper-cascor"\nversion = "{version}"\n')
        os.environ["JUNIPER_EXP_CASCOR_SRC_DIR"] = str(tree / "src")
        return tree

    def _suite(self, root: Path, mode: str = "parallel", par: int = 4) -> Path:
        path = root / "suite.yaml"
        path.write_text(self.SUITE.format(mode=mode, par=par))
        return path

    def test_at_floor_allows_parallel(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, ".".join(str(p) for p in run_suite.CASCOR_PARALLEL_FLOOR))
            doc = run_suite.load_suite(self._suite(root))
            self.assertIsInstance(doc, dict)
            self.assertIsNone(run_suite.check_cascor_parallel_floor(doc))

    def test_below_floor_refuses_and_names_the_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, "0.9.0")
            doc = run_suite.load_suite(self._suite(root))
            with self.assertRaisesRegex(run_suite.SuiteError, r"0\.9\.0"):
                run_suite.check_cascor_parallel_floor(doc)

    def test_unreadable_version_fails_closed(self) -> None:
        """An unknowable version must not resolve the same way as a compliant one."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, None)  # no pyproject.toml -> version unknowable
            doc = run_suite.load_suite(self._suite(root))
            with self.assertRaisesRegex(run_suite.SuiteError, "could not be read"):
                run_suite.check_cascor_parallel_floor(doc)

    def test_sequential_is_never_gated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, "0.9.0")  # below the floor, and irrelevant in sequential mode
            doc = run_suite.load_suite(self._suite(root, mode="sequential", par=1))
            self.assertIsInstance(doc, dict)
            self.assertIsNone(run_suite.check_cascor_parallel_floor(doc))

    def test_recurrence_parallel_is_never_gated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, "0.9.0")
            path = root / "rec.yaml"
            path.write_text("schema_version: 1\n" "suite: {name: s, app: recurrence, base_config: [b]}\n" "execution: {mode: parallel, max_parallel: 4}\n")
            doc = run_suite.load_suite(path)
            self.assertIsInstance(doc, dict)
            self.assertIsNone(run_suite.check_cascor_parallel_floor(doc))

    # ---- D5 (2026-09-11): the relocation itself, and that it did not weaken the guard --------

    def test_load_suite_does_NOT_gate_when_no_cascor_tree_is_resolvable(self) -> None:
        """THE POINT OF THE RELOCATION. This is the CI case, asserted directly.

        CI clones only juniper-ml, so no cascor sibling exists and the version is unknowable.
        Before D5 this raised from ``load_suite`` and turned the R-6 drift gate red for every
        checked-in parallel cascor suite. Structural validation must now succeed; the launch gate
        is a separate call, asserted to still refuse in the very next test.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, None)  # no pyproject.toml -> version unknowable, as in CI
            doc = run_suite.load_suite(self._suite(root))
            self.assertIsInstance(doc, dict)
            self.assertEqual(doc["execution"]["mode"], "parallel")

    def test_the_launch_gate_still_refuses_the_same_suite(self) -> None:
        """Paired with the test above: structural PASS and launch REFUSE on one identical doc.

        Asserting only the pass would be a vacuous relocation — it would look identical to having
        deleted the guard.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, None)
            doc = run_suite.load_suite(self._suite(root))
            with self.assertRaisesRegex(run_suite.SuiteError, "could not be read"):
                run_suite.check_cascor_parallel_floor(doc)

    def _run_main(self, suite_path: Path, *extra: str) -> "tuple[int, str]":
        """``main`` with output captured; returns (exit code, stdout+stderr).

        The text matters: exit 2 alone is NOT evidence this guard fired. ``main`` exits 2 for
        several unrelated reasons, and a mutation that deleted the call entirely still left this
        suite exiting 2 (its base_config path does not exist). Assert on the message.
        """
        buf_out, buf_err = io.StringIO(), io.StringIO()
        with redirect_stdout(buf_out), redirect_stderr(buf_err):
            code = run_suite.main(["--suite", str(suite_path), *extra])
        return code, buf_out.getvalue() + buf_err.getvalue()

    def test_main_refuses_below_floor_before_launching(self) -> None:
        """The guard is still pre-launch: main exits 2 naming the offending version."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, "0.9.0")
            code, text = self._run_main(self._suite(root))
            self.assertEqual(code, 2)
            self.assertIn("0.9.0", text, "exit 2 alone is not proof this guard fired")

    def test_main_refuses_below_floor_under_dry_run_too(self) -> None:
        """``--dry-run`` must report the refusal, not print a plan that could never run.

        This is the half most easily lost in a relocation: move the check past the ``--dry-run``
        early return and the operator gets a confident plan for a suite the runner would refuse.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, "0.9.0")
            code, text = self._run_main(self._suite(root), "--dry-run")
            self.assertEqual(code, 2)
            self.assertIn("0.9.0", text, "exit 2 alone is not proof this guard fired")
            self.assertNotIn("$ ", text, "a refused suite must not also print a launch plan")

    def test_main_dry_run_still_works_when_the_floor_is_met(self) -> None:
        """Negative control for the two above — the refusal is the version, not the dry run."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._tree(root, ".".join(str(p) for p in run_suite.CASCOR_PARALLEL_FLOOR))
            base = root / "b"
            base.write_text(BASE_CONFIG)
            path = root / "suite.yaml"
            path.write_text("schema_version: 1\n" f"suite: {{name: s, app: cascor, base_config: ['{base}']}}\n" "execution: {mode: parallel, max_parallel: 4}\n")
            code, text = self._run_main(path, "--dry-run")
            self.assertEqual(code, 0)
            self.assertIn("$ ", text, "a permitted dry run must actually print its plan")


class MaterialiseTest(unittest.TestCase):
    def test_overrides_and_per_cell_seed_applied_and_driver_validated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "base.yaml"
            base.write_text(BASE_CONFIG)
            cell = {"cell_id": "c003-abcd1234", "index": 3, "name": None, "config_path": str(base), "overrides": {"training.params.max_hidden_units": 8}}
            validate = run_suite._driver_validator()
            self.assertIsNotNone(validate, "the real driver's load_config must be importable")
            out = run_suite.materialise_cell(cell, {"name": "s", "seed_policy": "per_cell"}, root / "suite", validate)
            import yaml

            resolved = yaml.safe_load(out.read_text())
            self.assertEqual(resolved["training"]["params"]["max_hidden_units"], 8)
            self.assertEqual(resolved["experiment"]["seed"], 7 + 3)
            self.assertEqual(resolved["dataset"]["params"]["seed"], 7 + 3)
            self.assertEqual(resolved["experiment"]["name"], "s-c003-abcd1234")

    def test_bad_override_path_is_a_suite_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "base.yaml"
            base.write_text(BASE_CONFIG)
            cell = {"cell_id": "c000-ffff0000", "index": 0, "name": None, "config_path": str(base), "overrides": {"experiment.name.deep": 1}}
            with self.assertRaisesRegex(run_suite.SuiteError, "non-mapping"):
                run_suite.materialise_cell(cell, {"name": "s"}, root / "suite", None)


# The per-phase record run_experiment.py writes for the audited F-D1 cell: train and predict
# succeeded, the enabled crossval 422'd on the missing X_full key, save_model was not enabled.
X_FULL_ERROR = "HTTP 422: NPZ artifact is missing required key 'X_full'"
DEGRADED_PHASES = {"train": {"status": "ok"}, "predict": {"status": "ok"}, "crossval": {"status": "failed", "error": X_FULL_ERROR}, "save_model": {"status": "skipped"}}


class MainLoopTest(unittest.TestCase):
    def _setup(self, *, cof: str = "true", fail_marker: "str | None" = None, fail_up: bool = False, degraded_marker: "str | None" = None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "base.yaml").write_text(BASE_CONFIG)
        suite_dir = root / "suite-out"
        (root / "suite.yaml").write_text(SUITE_TEMPLATE.format(base=root / "base.yaml", seed_policy="fixed", cof=cof, suite_dir=suite_dir))
        markers = root / "markers"
        markers.mkdir()
        run_root = root / "runroot"
        run_root.mkdir()
        launcher = root / "stub_launcher.bash"
        _write_stub_launcher(launcher, markers, fail_up=fail_up)
        driver = root / "stub_driver.py"
        per_cell = {fail_marker: "failed"} if fail_marker else {}
        if degraded_marker:
            per_cell[degraded_marker] = "degraded"
        _write_stub_driver(driver, per_cell=per_cell or None, manifest_extra={"degraded": {"phases": DEGRADED_PHASES}})
        self._env = {"JUNIPER_SUITE_LAUNCHER": str(launcher), "JUNIPER_SUITE_DRIVER": str(driver), "JUNIPER_SUITE_PYTHON": sys.executable}
        self._old_run_root = run_suite.DEFAULT_RUN_ROOT
        run_suite.DEFAULT_RUN_ROOT = run_root  # type: ignore[attr-defined]
        self.addCleanup(lambda: setattr(run_suite, "DEFAULT_RUN_ROOT", self._old_run_root))
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

    def test_happy_path_registry_index_aggregate_and_teardown(self) -> None:
        root, suite_dir, markers, run_root = self._setup()
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0, msg=out)
        registry = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        self.assertEqual([r["outcome"] for r in registry], ["succeeded", "succeeded"])
        self.assertTrue(all(r["run_id"].startswith("stub-run-") for r in registry))
        self.assertEqual(len(list(markers.glob("down-*"))), 2, "every cell must be torn down")
        index = [json.loads(line) for line in (run_root / "index.jsonl").read_text().splitlines()]
        self.assertEqual(len(index), 2)
        csv_text = (suite_dir / "aggregate.csv").read_text()
        self.assertIn("training.params.max_hidden_units", csv_text)
        self.assertIn("REPORT.md", out)
        manifest = json.loads((suite_dir / "suite_manifest.json").read_text())
        self.assertEqual(manifest["schema"], "juniper-experiment-suite/1")

    def _driver_argvs(self, run_root: Path) -> "list[list[str]]":
        return [json.loads(m.read_text())["argv"] for m in sorted(run_root.glob("*/manifest.json"))]

    def test_stall_seconds_is_forwarded_to_the_driver(self) -> None:
        """execution.stall_seconds must reach the driver's Q-2 detector.

        The detector watches ``current_epoch``, which does not advance while the CANDIDATE
        pool trains, so a long candidate phase reads as a stall. Without this passthrough a
        suite cannot raise the window and healthy cells are killed at the 120 s default --
        the P4 E-A grid lost every ``candidate_pool_size >= 16`` cell that way.
        """
        root, _suite_dir, _markers, run_root = self._setup()
        suite_yaml = root / "suite.yaml"
        suite_yaml.write_text(suite_yaml.read_text().replace("  per_run_timeout_seconds: 900", "  per_run_timeout_seconds: 900\n  stall_seconds: 900"))
        rc, out = self._main("--suite", str(suite_yaml))
        self.assertEqual(rc, 0, msg=out)
        argvs = self._driver_argvs(run_root)
        self.assertTrue(argvs, "no driver invocations recorded")
        for argv in argvs:
            self.assertIn("--stall-seconds", argv)
            self.assertEqual(argv[argv.index("--stall-seconds") + 1], "900.0")

    def test_absent_stall_seconds_leaves_the_driver_default_alone(self) -> None:
        """Omitting the key must not pass the flag at all (the driver owns its default)."""
        root, _suite_dir, _markers, run_root = self._setup()
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0, msg=out)
        argvs = self._driver_argvs(run_root)
        self.assertTrue(argvs, "no driver invocations recorded")
        for argv in argvs:
            self.assertNotIn("--stall-seconds", argv)

    def test_max_wall_seconds_is_forwarded_to_the_driver(self) -> None:
        """execution.max_wall_seconds must reach the driver's Q-2 wall-clock budget.

        The ml#1069 class, one field over. A suite could always reach the budget through
        a dotted ``matrix`` / ``include`` override -- ``suites/p4/e-i-cascor-cap-ceiling
        .yaml`` sets ``outputs.max_wall_seconds`` exactly that way -- but an un-overridden
        cell silently inherited ``base_config``'s value (3600 s) with no signal. Measured
        on the E-I run (``20260814T091542Z``): cap 32 -> 1497.4 s, cap 64 -> 2907.1 s,
        cap 128 -> 4243.6 s, so the cap-128 cell would have been truncated by that
        inherited default and cap 64 cleared it by only 693 s.
        """
        root, _suite_dir, _markers, run_root = self._setup()
        suite_yaml = root / "suite.yaml"
        suite_yaml.write_text(suite_yaml.read_text().replace("  per_run_timeout_seconds: 900", "  per_run_timeout_seconds: 15600\n  max_wall_seconds: 14400"))
        rc, out = self._main("--suite", str(suite_yaml))
        self.assertEqual(rc, 0, msg=out)
        argvs = self._driver_argvs(run_root)
        self.assertTrue(argvs, "no driver invocations recorded")
        for argv in argvs:
            self.assertIn("--max-wall-seconds", argv)
            self.assertEqual(argv[argv.index("--max-wall-seconds") + 1], "14400.0")

    def test_absent_max_wall_seconds_leaves_the_driver_default_alone(self) -> None:
        """Omitting the key must not pass the flag at all (the driver owns its default)."""
        root, _suite_dir, _markers, run_root = self._setup()
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0, msg=out)
        argvs = self._driver_argvs(run_root)
        self.assertTrue(argvs, "no driver invocations recorded")
        for argv in argvs:
            self.assertNotIn("--max-wall-seconds", argv)

    def test_both_budget_flags_forward_independently(self) -> None:
        """stall_seconds and max_wall_seconds are orthogonal Q-2 knobs."""
        root, _suite_dir, _markers, run_root = self._setup()
        suite_yaml = root / "suite.yaml"
        suite_yaml.write_text(suite_yaml.read_text().replace("  per_run_timeout_seconds: 900", "  per_run_timeout_seconds: 15600\n  stall_seconds: 900\n  max_wall_seconds: 14400"))
        rc, out = self._main("--suite", str(suite_yaml))
        self.assertEqual(rc, 0, msg=out)
        argvs = self._driver_argvs(run_root)
        self.assertTrue(argvs, "no driver invocations recorded")
        for argv in argvs:
            self.assertEqual(argv[argv.index("--stall-seconds") + 1], "900.0")
            self.assertEqual(argv[argv.index("--max-wall-seconds") + 1], "14400.0")

    def test_max_wall_seconds_typo_still_rejected(self) -> None:
        """The allow-list widens by exactly one -- a near-miss spelling must still fail."""
        root, _suite_dir, _markers, _run_root = self._setup()
        suite_yaml = root / "suite.yaml"
        suite_yaml.write_text(suite_yaml.read_text().replace("  per_run_timeout_seconds: 900", "  per_run_timeout_seconds: 900\n  max_wall_second: 14400"))
        rc, _out = self._main("--suite", str(suite_yaml))
        self.assertEqual(rc, 2)

    def test_dry_run_shows_the_max_wall_flag(self) -> None:
        """The dry-run preview must show the budget an operator is about to spend."""
        root, _suite_dir, _markers, _run_root = self._setup()
        suite_yaml = root / "suite.yaml"
        suite_yaml.write_text(suite_yaml.read_text().replace("  per_run_timeout_seconds: 900", "  per_run_timeout_seconds: 15600\n  max_wall_seconds: 14400"))
        rc, out = self._main("--suite", str(suite_yaml), "--dry-run")
        self.assertEqual(rc, 0, msg=out)
        self.assertIn("--max-wall-seconds 14400.0", out)

    def test_unknown_execution_key_still_rejected(self) -> None:
        """The new key widens the allow-list by exactly one — typos must still fail."""
        root, _suite_dir, _markers, _run_root = self._setup()
        suite_yaml = root / "suite.yaml"
        suite_yaml.write_text(suite_yaml.read_text().replace("  per_run_timeout_seconds: 900", "  per_run_timeout_seconds: 900\n  stall_second: 900"))
        rc, out = self._main("--suite", str(suite_yaml))
        self.assertEqual(rc, 2, msg=out)
        self.assertIn("unknown execution: keys", out)

    def test_continue_on_failure_runs_all_and_exits_one(self) -> None:
        root, suite_dir, markers, _ = self._setup(fail_marker="max_hidden_units: 2")
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 1, msg=out)
        registry = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        self.assertEqual(len(registry), 2, "continue_on_failure must run the remaining cells")
        self.assertEqual({r["outcome"] for r in registry}, {"failed", "succeeded"})
        self.assertEqual(len(list(markers.glob("down-*"))), 2)

    def test_stop_on_failure_halts_the_loop(self) -> None:
        root, suite_dir, _, _ = self._setup(cof="false", fail_marker="max_hidden_units: 2")
        rc, _ = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 1)
        registry = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        self.assertEqual(len(registry), 1, "continue_on_failure=false must stop after the first failure")

    def test_resume_skips_succeeded_cells(self) -> None:
        root, suite_dir, markers, _ = self._setup()
        rc, _ = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0)
        ups_before = len(list(markers.glob("up-*")))
        rc, out = self._main("--suite", str(root / "suite.yaml"), "--resume", suite_dir.name)
        self.assertEqual(rc, 0, msg=out)
        self.assertEqual(len(list(markers.glob("up-*"))), ups_before, "resume must not re-run succeeded cells")
        self.assertIn("skipped (resume)", out)

    def test_launcher_up_failure_records_error_and_exits_one(self) -> None:
        root, suite_dir, markers, _ = self._setup(fail_up=True)
        rc, _ = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 1)
        registry = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        self.assertTrue(all("launcher --up failed" in (r.get("error") or "") for r in registry))
        self.assertEqual(len(list(markers.glob("down-*"))), 0, "no teardown without a run_id")

    def test_dry_run_writes_nothing(self) -> None:
        root, suite_dir, markers, run_root = self._setup()
        rc, out = self._main("--suite", str(root / "suite.yaml"), "--dry-run")
        self.assertEqual(rc, 0)
        self.assertIn("2 cells", out)
        self.assertFalse(suite_dir.exists(), "--dry-run must not create the suite dir")
        self.assertFalse((run_root / "index.jsonl").exists())
        self.assertEqual(len(list(markers.iterdir())), 0)

    def test_only_unknown_cell_id_exits_two(self) -> None:
        root, _, _, _ = self._setup()
        rc, out = self._main("--suite", str(root / "suite.yaml"), "--only", "c999-deadbeef")
        self.assertEqual(rc, 2)
        self.assertIn("not in the expansion", out)


class NestedBlockTypeTest(unittest.TestCase):
    """`or {}` is a FALSY guard; a truthy non-mapping walks straight through it.

    `load_suite` type-checks `doc` itself and then trusted `or {}` for every nested block, so
    a malformed suite reached the validation arithmetic and died with an INTERNAL traceback
    from the one function whose job is to turn malformed operator YAML into a `SuiteError`.
    Reproduced before the fix: `suite:` written as a list gave
    `TypeError: unhashable type: 'dict'` at the `set(suite) - SUITE_SUITE_KEYS` line.

    Each case below FAILS on the pre-fix code -- verified with
    `util/ad-hoc/2026-09-11_falsy_guard_census.py` and a direct mutation run -- so none of
    them is a test that would have passed anyway.
    """

    def _load(self, body: str):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "base.yaml").write_text(BASE_CONFIG)
        p = root / "suite.yaml"
        p.write_text(body)
        return run_suite.load_suite(p)

    _VALID = "schema_version: 1\nsuite:\n  name: s\n  app: cascor\n  base_config: [base.yaml]\n"

    def test_suite_block_as_a_list_is_a_clean_SuiteError(self) -> None:
        with self.assertRaisesRegex(run_suite.SuiteError, r"suite: must be a mapping, got list"):
            self._load("schema_version: 1\nsuite:\n  - app: cascor\n")

    def test_execution_block_as_a_string_is_a_clean_SuiteError(self) -> None:
        with self.assertRaisesRegex(run_suite.SuiteError, r"execution: must be a mapping, got str"):
            self._load(self._VALID + "execution: notamapping\n")

    def test_matrix_block_as_a_list_is_a_clean_SuiteError(self) -> None:
        with self.assertRaisesRegex(run_suite.SuiteError, r"matrix: must be a mapping, got list"):
            self._load(self._VALID + "matrix:\n  - a\n")

    def test_outputs_block_as_a_list_is_a_clean_SuiteError(self) -> None:
        with self.assertRaisesRegex(run_suite.SuiteError, r"outputs: must be a mapping, got list"):
            self._load(self._VALID + "outputs:\n  - a\n")

    def test_exclude_as_a_string_is_a_clean_SuiteError(self) -> None:
        # A string ITERATES as characters, so the downstream per-entry check would otherwise
        # report "entries must be non-empty mappings" about single letters.
        with self.assertRaisesRegex(run_suite.SuiteError, r"exclude: must be a list, got str"):
            self._load(self._VALID + "exclude: foo\n")

    def test_include_as_a_mapping_is_a_clean_SuiteError(self) -> None:
        with self.assertRaisesRegex(run_suite.SuiteError, r"include: must be a list, got dict"):
            self._load(self._VALID + "include:\n  a: 1\n")

    # --- the negative controls: the guard must not start rejecting valid suites ----------

    def test_a_valid_suite_still_loads(self) -> None:
        doc = self._load(self._VALID)
        self.assertEqual(doc["suite"]["app"], "cascor")

    def test_absent_optional_blocks_stay_legal(self) -> None:
        # Every caller writes `doc.get(k) or {}`; absent and empty are valid suites and must
        # not be caught by a check aimed at truthy non-mappings.
        doc = self._load(self._VALID)
        for key in ("execution", "matrix", "outputs", "include", "exclude"):
            self.assertNotIn(key, doc)

    def test_empty_optional_blocks_stay_legal(self) -> None:
        doc = self._load(self._VALID + "matrix: {}\nexclude: []\n")
        self.assertEqual(doc.get("matrix"), {})
        self.assertEqual(doc.get("exclude"), [])


if __name__ == "__main__":
    unittest.main()


PARALLEL_SUITE_TEMPLATE = """\
schema_version: 1
suite:
  name: p-suite
  description: test
  app: recurrence
  base_config:
    - {base}
execution:
  mode: parallel
  max_parallel: 2
  continue_on_failure: true
  per_run_timeout_seconds: 900
matrix:
  training.params.max_hidden_units: [2, 4]
outputs:
  suite_dir: {suite_dir}
"""


class ParallelModeTest(MainLoopTest):
    """Wave 7.5: bounded-parallel execution (recurrence app; cascor refuses at load)."""

    def test_parallel_happy_path_records_budget_and_both_cells(self) -> None:
        root, suite_dir, markers, run_root = self._setup()
        (root / "suite.yaml").write_text(PARALLEL_SUITE_TEMPLATE.format(base=root / "base.yaml", suite_dir=suite_dir))
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0, msg=out)
        registry = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        self.assertEqual(len(registry), 2)
        self.assertEqual({r["outcome"] for r in registry}, {"succeeded"})
        for r in registry:
            self.assertIsNotNone(r["thread_budget"], "parallel cells must record the H-11 budget env")
            self.assertIn("OMP_NUM_THREADS", r["thread_budget"])
            self.assertNotIn("CASCOR_NUM_PROCESSES", r["thread_budget"], "recurrence budget must not carry the cascor knob")
        self.assertEqual(len(list(markers.glob("down-*"))), 2, "every parallel cell must be torn down")
        index = [json.loads(line) for line in (run_root / "index.jsonl").read_text().splitlines()]
        self.assertEqual(len(index), 2, "index appends must be lock-safe under parallelism")

    def test_sequential_rows_have_no_budget(self) -> None:
        root, suite_dir, _, _ = self._setup()
        rc, _ = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0)
        registry = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        self.assertTrue(all(r["thread_budget"] is None for r in registry))

    def test_budget_split_math(self) -> None:
        budget = run_suite.thread_budget_env("cascor", max_parallel=2)
        nproc = os.cpu_count() or 1
        self.assertEqual(budget["CASCOR_NUM_PROCESSES"], str(max(1, nproc // 4)))
        self.assertEqual(budget["OMP_NUM_THREADS"], "2")
        rec = run_suite.thread_budget_env("recurrence", max_parallel=2)
        self.assertEqual(rec["OMP_NUM_THREADS"], str(max(1, nproc // 4)))
        self.assertNotIn("CASCOR_NUM_PROCESSES", rec)


class ProvenanceEnvTest(unittest.TestCase):
    """D-C: the suite is the only layer that knows the cell id and the suite name.

    ``experiment_stack.bash`` forwards both into cascor's process env, so every snapshot a
    cell writes records which cell produced it. Without this the launcher is invoked with
    ``--experiment <cell_id>`` and the SUITE identity is lost -- which is exactly the half of
    "find the model from the E-I cap-128 cell" that the census could not answer.
    """

    def _capture_up_env(self, *, suite_name: "str | None") -> dict:
        import subprocess as _subprocess
        from unittest import mock

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        cell_yaml = Path(tmp.name) / "experiment.yaml"
        cell_yaml.write_text("schema_version: 1\n")
        captured: dict = {}

        def fake_run(argv, **kwargs):
            captured.setdefault("env", kwargs.get("env"))
            return _subprocess.CompletedProcess(argv, 1, stdout="", stderr="stub: no banner")

        cell = {"cell_id": "c007-9f3ab12c", "name": "cap-128", "overrides": {}}
        with mock.patch.object(run_suite.subprocess, "run", side_effect=fake_run):
            run_suite.execute_cell(cell, cell_yaml, "cascor", 5.0, Path("/bin/true"), Path("/bin/true"), sys.executable, None, None, None, suite_name)
        self.assertIsNotNone(captured.get("env"), "execute_cell must pass an explicit env so provenance reaches the launcher")
        return captured["env"]

    def test_cell_id_reaches_the_launcher(self) -> None:
        env = self._capture_up_env(suite_name="e-i-cap-ceiling")
        self.assertEqual(env["JUNIPER_CASCOR_CELL_ID"], "c007-9f3ab12c")

    def test_suite_name_is_the_experiment_not_the_cell_id(self) -> None:
        """The launcher receives ``--experiment <cell_id>``; without this override the
        recorded experiment would duplicate the cell id and the suite would be unrecoverable."""
        env = self._capture_up_env(suite_name="e-i-cap-ceiling")
        self.assertEqual(env["JUNIPER_CASCOR_EXPERIMENT"], "e-i-cap-ceiling")
        self.assertNotEqual(env["JUNIPER_CASCOR_EXPERIMENT"], env["JUNIPER_CASCOR_CELL_ID"])

    def test_absent_suite_name_leaves_the_launcher_default(self) -> None:
        """No suite name -> no override, so ``experiment_stack.bash`` falls back to its own
        ``EXPERIMENT``. Setting an empty string instead would blank the identity."""
        env = self._capture_up_env(suite_name=None)
        self.assertNotIn("JUNIPER_CASCOR_EXPERIMENT", env)
        self.assertEqual(env["JUNIPER_CASCOR_CELL_ID"], "c007-9f3ab12c")


class GateInputsInAggregateTest(MainLoopTest):
    """P2 item 1.4: the aggregate must not offer ``wall_seconds`` as the only number.

    ``wall_seconds`` is DE-RATIFIED -- it absorbs plot rendering and stack bring-up, and enabling
    the Grafana bridge alone moves it ~5%. Before this, it was the only timing column in
    ``aggregate.csv``, so a reader analysed the wrong quantity with nothing flagging it.
    """

    def test_aggregate_csv_carries_both_gate_inputs(self) -> None:
        root, suite_dir, _, _ = self._setup()
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0, msg=out)
        header = (suite_dir / "aggregate.csv").read_text().splitlines()[0]
        self.assertIn("step_count", header)
        self.assertIn("mean_step_seconds", header)
        self.assertIn("wall_seconds", header, "the de-ratified column stays for continuity")

    def test_report_states_that_wall_seconds_is_de_ratified(self) -> None:
        root, suite_dir, _, _ = self._setup()
        self._main("--suite", str(root / "suite.yaml"))
        report = (suite_dir / "REPORT.md").read_text()
        self.assertIn("DE-RATIFIED", report)
        self.assertIn("work invariant", report)
        self.assertIn("single workload", report)


class ComparisonReportingTest(MainLoopTest):
    """The verdict is REPORTED, never enforced by this tool."""

    def test_missing_baseline_is_reported_not_fatal(self) -> None:
        root, suite_dir, _, _ = self._setup()
        rc, out = self._main("--suite", str(root / "suite.yaml"), "--compare-baseline", "no-such-tag")
        self.assertEqual(rc, 0, msg=out)
        self.assertIn("comparison could not run", (suite_dir / "REPORT.md").read_text())

    def test_a_failing_verdict_does_NOT_change_the_suite_exit_code(self) -> None:
        """The load-bearing property of item 1.4.

        Wiring a comparator verdict to run_suite's exit status would silently make the run tier a
        gate -- and §6 of the P1 design records that as a SEPARATE owner decision, still open. If
        this test ever fails, someone has made that decision by accident.
        """
        root, suite_dir, _, _ = self._setup()

        def _always_fail(_tag, _suite_dir):
            return "verdict: FAIL  (baseline 'x')\n  work  MOVED step_count baseline=1 candidate=2"

        # run_suite is loaded via spec_from_file_location, so mypy sees a bare ModuleType and
        # cannot know its attributes -- same reason DEFAULT_RUN_ROOT is ignored above.
        original = run_suite._run_comparison  # type: ignore[attr-defined]
        run_suite._run_comparison = _always_fail  # type: ignore[attr-defined]
        self.addCleanup(lambda: setattr(run_suite, "_run_comparison", original))

        rc, out = self._main("--suite", str(root / "suite.yaml"), "--compare-baseline", "whatever")
        self.assertEqual(rc, 0, msg=f"a FAIL verdict must not fail the suite; got rc={rc}\n{out}")
        report = (suite_dir / "REPORT.md").read_text()
        self.assertIn("verdict: FAIL", report, "the verdict must still be visible")
        self.assertIn("exit code does NOT reflect this verdict", report)

    def test_no_comparison_section_without_the_flag(self) -> None:
        root, suite_dir, _, _ = self._setup()
        self._main("--suite", str(root / "suite.yaml"))
        self.assertNotIn("## Baseline comparison", (suite_dir / "REPORT.md").read_text())


class DegradedSuiteTest(MainLoopTest):
    """W0.3 (F-D1): a ``degraded`` cell is not a success -- not in the summary line, not in
    ``REPORT.md``, not in the exit code -- and the console names the phase it lost.

    The audited Scenario-A suite printed ``succeeded`` for a cell whose crossval 422'd, wrote
    ``2 succeeded`` into REPORT.md and exited 0, because the driver had recorded ``succeeded``.
    """

    def _registry(self, suite_dir: Path) -> "list[dict]":
        return [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]

    def test_a_degraded_cell_is_counted_reported_and_fails_the_suite(self) -> None:
        root, suite_dir, _markers, run_root = self._setup(degraded_marker="max_hidden_units: 4")
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertNotEqual(rc, 0, msg=out)
        self.assertEqual(rc, 1, msg=out)
        self.assertIn(f"degraded (crossval failed: {X_FULL_ERROR})", out)
        report = (suite_dir / "REPORT.md").read_text()
        self.assertIn("Cells: 2 total, 1 succeeded, 1 degraded, 0 failed/other, 0 not run.", report)
        self.assertIn("## Degraded cells", report)
        self.assertIn(f"crossval failed: {X_FULL_ERROR}", report)
        # Round trip: registry.jsonl and index.jsonl carry the outcome; the registry row carries the phase record.
        registry = self._registry(suite_dir)
        self.assertEqual(sorted(row["outcome"] for row in registry), ["degraded", "succeeded"])
        degraded_row = next(row for row in registry if row["outcome"] == "degraded")
        self.assertEqual(degraded_row["phases"], DEGRADED_PHASES)
        self.assertEqual(degraded_row["exit_code"], 1)
        index = [json.loads(line) for line in (run_root / "index.jsonl").read_text().splitlines()]
        self.assertEqual(sorted(row["outcome"] for row in index), ["degraded", "succeeded"])
        with (suite_dir / "aggregate.csv").open(newline="", encoding="utf-8") as handle:
            self.assertEqual(sorted(row["outcome"] for row in csv.DictReader(handle)), ["degraded", "succeeded"])

    def test_degraded_is_a_terminal_outcome(self) -> None:
        self.assertIn("degraded", run_suite.TERMINAL_OUTCOMES)

    def test_resume_reruns_a_degraded_cell(self) -> None:
        root, suite_dir, markers, _ = self._setup(degraded_marker="max_hidden_units: 4")
        rc, _ = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 1)
        ups_before = len(list(markers.glob("up-*")))
        rc, out = self._main("--suite", str(root / "suite.yaml"), "--resume", suite_dir.name)
        self.assertEqual(rc, 1, msg=out)  # the stub degrades the same cell again
        self.assertEqual(len(list(markers.glob("up-*"))), ups_before + 1, "resume must re-run the degraded cell, and only it")
        self.assertIn("skipped (resume)", out)

    def test_stop_on_failure_stops_after_a_degraded_cell(self) -> None:
        root, suite_dir, _, _ = self._setup(cof="false", degraded_marker="max_hidden_units: 2")
        rc, _ = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 1)
        self.assertEqual([row["outcome"] for row in self._registry(suite_dir)], ["degraded"], "continue_on_failure: false must stop after a degraded cell")


class OutcomeLineTest(unittest.TestCase):
    """The per-cell console line: a degraded cell names the phase it lost; nothing else changes."""

    def test_a_degraded_cell_names_the_failed_phase(self) -> None:
        self.assertEqual(run_suite._outcome_line({"outcome": "degraded", "phases": DEGRADED_PHASES, "error": None}), f"degraded (crossval failed: {X_FULL_ERROR})")

    def test_an_enabled_phase_left_not_reached_is_named_too(self) -> None:
        # The driver fails closed on it (derive_recurrence_outcome), so the summary must name it.
        phases = {"train": {"status": "ok"}, "predict": {"status": "not_reached"}, "crossval": {"status": "skipped"}}
        self.assertEqual(run_suite._outcome_line({"outcome": "degraded", "phases": phases}), "degraded (predict not_reached)")

    def test_a_degraded_cell_without_a_phase_record_prints_the_bare_outcome(self) -> None:
        self.assertEqual(run_suite._outcome_line({"outcome": "degraded", "error": None}), "degraded")

    def test_other_outcomes_keep_the_suite_level_error(self) -> None:
        self.assertEqual(run_suite._outcome_line({"outcome": "failed", "error": "unreadable manifest.json", "phases": DEGRADED_PHASES}), "failed (unreadable manifest.json)")
        self.assertEqual(run_suite._outcome_line({"outcome": "succeeded", "error": None}), "succeeded")


STATS_SUMMARY_PATH = REPO_ROOT / "util" / "experiments" / "stats_summary.py"
_stats_spec = importlib.util.spec_from_file_location("stats_summary_for_run_suite_tests", STATS_SUMMARY_PATH)
stats_summary = importlib.util.module_from_spec(_stats_spec)
_stats_spec.loader.exec_module(stats_summary)

# The dataset / outcome / recurrence blocks of the audited Scenario-A stats.json (the equities_seq
# AAPL cell, run 20261003T091414Z-4ba6), copied verbatim. Its crossval 422'd, so `crossval` is null.
# It carries TWO window counts: `dataset.shapes.n_windows` (1698, every partition) and the train
# descriptor's `n_windows` (1346). The headline reads the descriptor -- the number REPORT.md's
# "reported instead" line already prints -- and the fixture keeps both so that choice is pinned.
AUDITED_SCENARIO_A_STATS = {
    "schema": "juniper-experiment-stats/1",
    "dataset": {"generator": "equities_seq", "generator_version": "6.0.0", "split": "train", "task_type": "regression", "shapes": {"kind": "sequence", "lookback": 64, "n_features": 15, "n_test": 176, "n_train": 1346, "n_windows": 1698}},
    "outcome": {"outcome": "succeeded", "acceptance": {"ok": False, "reasons": ["crossval failed: HTTP 422: invalid dataset: NPZ artifact is missing required key 'X_full'"]}},
    "recurrence": {
        "crossval": None,
        "dataset_descriptor": {"dataset_id": "equities_seq-6.0.0-15505731cba5b86d", "has_seq_lengths": False, "has_target_dt": True, "lookback": 64, "n_features": 15, "n_windows": 1346, "name": None, "output_dim": 1, "split": "train"},
        "final_metrics": {"loss": 0.00029384856819352243, "mae": 0.011502149105555557, "mse": 0.00029384856819352243, "r2": 0.11632826498677562, "rmse": 0.017142011789563164},
        "n_epochs": 1,
        "readout": {"hyperparameters": {"d": 16, "rff_features": 256, "rff_gamma": "median", "ridge": 1.0}, "rung": "rff"},
        "stopped_reason": "converged",
        "theta": {"note": "data-driven (resolved from per-window elapsed time)", "value": None},
    },
}


def _recurrence_stats(*, train_r2: float, cv_r2: "float | None" = None, cv_r2_std: "float | None" = None) -> dict:
    """A stats dict made by the REAL writer, ``stats_summary.build_stats``, from driver-shaped
    payloads, then round-tripped through JSON the way the driver writes it. The crossval nesting
    was never observed in an audited artifact (that run's crossval failed), so these fixtures go
    through the writer rather than restating its shape -- a writer change breaks them loudly."""
    manifest = {"run_id": "r", "experiment": {"name": "e"}, "timings": {"train": 0.5}, "outcome": "succeeded", "acceptance": {"ok": True, "reasons": []}, "dataset": {"meta": {"sequence": True, "n_samples": 1698}}}
    train = {"final_metrics": {"r2": train_r2, "rmse": 0.017}, "n_epochs": 1, "stopped_reason": "converged", "dataset": {"n_windows": 1346, "lookback": 64}}
    crossval = None
    if cv_r2 is not None:
        crossval = {"task_type": "regression", "n_folds": 3, "folds": [{"fold": 0, "eval_metrics": {"r2": cv_r2}, "n_epochs": 1}], "eval_aggregate": {"r2": cv_r2, "rmse": 0.02}, "eval_std": {"r2": cv_r2_std, "rmse": 0.001}}
    return json.loads(json.dumps(stats_summary.build_stats(manifest, kind="recurrence", train_summary=train, crossval=crossval, train_config={"d": 16, "readout": "rff"})))


class HeadlineMetricsTest(unittest.TestCase):
    """W0.4 (F-D2): ``_headline_metrics`` reads the shape ``stats_summary.build_stats`` writes.

    It used to look for ``train_r2`` / ``cv_r2`` / ``r2`` at the TOP of ``stats["recurrence"]``,
    where no writer ever put them, so every recurrence cell's ``metrics`` was ``{}`` and
    aggregate.csv / REPORT.md carried no r2 at all. The four fixtures are the plan's: the audited
    ``crossval: null`` shape, a successful crossval, ``cv_r2 == 0.0`` and ``cv_r2 == -18081.0``.
    """

    def _run_dir(self, stats: dict) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        run_dir = Path(tmp.name) / "run"
        (run_dir / "artifacts" / "results").mkdir(parents=True)
        (run_dir / "artifacts" / "results" / "stats.json").write_text(json.dumps(stats))
        return run_dir

    def test_the_audited_shape_yields_train_r2_and_n_windows_and_no_cv_key(self) -> None:
        metrics = run_suite._headline_metrics(self._run_dir(AUDITED_SCENARIO_A_STATS))
        self.assertEqual(metrics, {"train_r2": 0.11632826498677562, "n_windows": 1346})
        self.assertEqual([key for key in metrics if key.startswith("cv_")], [], "a null crossval must yield NO cv_* key, not a zero")

    def test_a_successful_crossval_surfaces_cv_r2_and_its_std(self) -> None:
        metrics = run_suite._headline_metrics(self._run_dir(_recurrence_stats(train_r2=0.52, cv_r2=0.31, cv_r2_std=0.07)))
        self.assertEqual(metrics, {"train_r2": 0.52, "cv_r2": 0.31, "cv_r2_std": 0.07, "n_windows": 1346})

    def test_a_zero_cv_r2_is_surfaced_not_dropped(self) -> None:
        # The truthiness trap: `if value:` drops 0.0, and a 0.0 r2 is exactly the "no skill" result.
        metrics = run_suite._headline_metrics(self._run_dir(_recurrence_stats(train_r2=0.0, cv_r2=0.0, cv_r2_std=0.0)))
        self.assertIn("cv_r2", metrics)
        self.assertEqual(metrics, {"train_r2": 0.0, "cv_r2": 0.0, "cv_r2_std": 0.0, "n_windows": 1346})

    def test_a_large_negative_cv_r2_is_surfaced_verbatim(self) -> None:
        # The E-H blow-up class: a -18081 aggregate must reach the report as -18081.0, unclamped.
        metrics = run_suite._headline_metrics(self._run_dir(_recurrence_stats(train_r2=0.11, cv_r2=-18081.0, cv_r2_std=36000.5)))
        self.assertEqual(metrics["cv_r2"], -18081.0)
        self.assertEqual(repr(metrics["cv_r2"]), "-18081.0")
        self.assertEqual(metrics["cv_r2_std"], 36000.5)

    def test_non_numbers_are_not_surfaced(self) -> None:
        stats = _recurrence_stats(train_r2=0.5, cv_r2=0.3, cv_r2_std=0.1)
        stats["recurrence"]["final_metrics"]["r2"] = True  # bool is an int subclass, not a metric
        stats["recurrence"]["crossval"]["eval_aggregate"]["r2"] = None
        stats["recurrence"]["crossval"]["eval_std"]["r2"] = "0.1"
        self.assertEqual(run_suite._headline_metrics(self._run_dir(stats)), {"n_windows": 1346})

    def test_aggregate_csv_and_report_gain_the_recurrence_columns(self) -> None:
        audited = self._run_dir(AUDITED_SCENARIO_A_STATS)
        blown_up = self._run_dir(_recurrence_stats(train_r2=0.11, cv_r2=-18081.0, cv_r2_std=36000.5))
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        suite_dir = Path(tmp.name) / "suite"
        suite_dir.mkdir()
        rows = [
            {"cell_id": "c000", "run_dir": str(audited), "outcome": "degraded", "phases": DEGRADED_PHASES, "metrics": run_suite._headline_metrics(audited)},
            {"cell_id": "c001", "run_dir": str(blown_up), "outcome": "succeeded", "metrics": run_suite._headline_metrics(blown_up)},
        ]
        (suite_dir / "registry.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
        cells = [{"cell_id": "c000", "name": "audited", "overrides": {}}, {"cell_id": "c001", "name": "blown-up", "overrides": {}}]
        self.assertEqual(run_suite.aggregate(suite_dir, {"name": "t", "description": "headline columns"}, cells), 1)
        with (suite_dir / "aggregate.csv").open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            header = list(reader.fieldnames or [])
            csv_rows = list(reader)
        for column in ("train_r2", "cv_r2", "cv_r2_std", "n_windows"):
            self.assertIn(column, header)
        self.assertEqual(csv_rows[0]["train_r2"], "0.11632826498677562")
        self.assertEqual(csv_rows[0]["cv_r2"], "", "the audited cell has no crossval -- its cv_r2 cell must be empty, not 0")
        self.assertEqual(csv_rows[0]["n_windows"], "1346")
        self.assertEqual(csv_rows[1]["cv_r2"], "-18081.0")
        report = (suite_dir / "REPORT.md").read_text()
        self.assertIn("-18081.0", report)
        self.assertIn("0.11632826498677562", report)
        self.assertIn("Cells: 2 total, 1 succeeded, 1 degraded, 0 failed/other, 0 not run.", report)


# The `/v1/metrics` body of a real cascor run (run 20260916T002848Z-3959, its `metrics_final.json` top level;
# the eval scalars are rounded). `build_stats` copies the six training fields into `cascor.final` and the four
# eval scalars into `cascor.eval_scalars`.
LIVE_CASCOR_METRICS = {"epoch": 17, "train_loss": 0.06737957149744034, "train_accuracy": 0.905, "val_loss": 0.06876520812511444, "val_accuracy": 0.91875, "hidden_units": 16, "f1": 0.9187, "precision": 0.92, "recall": 0.9175, "roc_auc": 0.9808}


def _cascor_stats(**metrics_final: object) -> dict:
    """A cascor stats dict made by the REAL writer, ``stats_summary.build_stats(kind="cascor", metrics_final=...)``,
    round-tripped through JSON the way the driver writes it. ``metrics_final`` is the ``/v1/metrics`` body the
    driver collects; going through the writer means a change to its cascor block breaks these fixtures loudly
    instead of leaving them asserting a shape nothing produces -- the way APD-ML-002 began."""
    manifest = {"run_id": "r", "experiment": {"name": "e"}, "timings": {"drive": 5.0}, "outcome": "succeeded", "acceptance": {"ok": True, "reasons": []}, "dataset": {"meta": {"n_train": 800, "n_test": 120, "n_features": 2, "n_classes": 2}}}
    return json.loads(json.dumps(stats_summary.build_stats(manifest, kind="cascor", metrics_final=metrics_final)))


def _stats_run_dir(case: unittest.TestCase, stats: "dict | None", parent: "Path | None" = None, name: str = "run") -> Path:
    """A run dir holding ``stats`` as ``artifacts/results/stats.json`` (none when ``stats`` is None), under ``parent`` or a fresh tempdir."""
    if parent is None:
        tmp = tempfile.TemporaryDirectory()
        case.addCleanup(tmp.cleanup)
        parent = Path(tmp.name)
    run_dir = parent / name
    (run_dir / "artifacts" / "results").mkdir(parents=True)
    if stats is not None:
        (run_dir / "artifacts" / "results" / "stats.json").write_text(json.dumps(stats))
    return run_dir


class CascorHeadlineMetricsTest(unittest.TestCase):
    """APD-ML-002 (owner rulings, 2026-10-26): the cascor half of ``_headline_metrics``.

    It read ``final_accuracy`` / ``test_accuracy`` / ``val_accuracy`` off the TOP of ``stats["cascor"]``, where
    ``build_stats`` never wrote anything, so all 439 cascor registry rows on the run corpus carried
    ``metrics: {}`` and no cascor ``aggregate.csv`` had an accuracy column. It now reads ``final.train_accuracy``
    and ``final.val_accuracy`` through ``CASCOR_HEADLINE_PATHS``. ``eval_scalars`` are deliberately NOT mapped
    (live mid-training values; 19 corpus runs computed them on the TRAINING split), ``test_accuracy`` has no
    producer yet, and ``final_accuracy`` is gone. Every fixture comes from the real writer.
    """

    def test_the_writer_shape_yields_exactly_train_and_val_accuracy(self) -> None:
        # The exact dict: nothing else from `final` (epoch, the losses, hidden_units), nothing from `eval_scalars`.
        metrics = run_suite._headline_metrics(_stats_run_dir(self, _cascor_stats(**LIVE_CASCOR_METRICS)))
        self.assertEqual(metrics, {"train_accuracy": 0.905, "val_accuracy": 0.91875})

    def test_a_zero_accuracy_is_kept(self) -> None:
        # The truthiness trap: `if value:` would drop it, and 0.0 is a real (if dismal) result.
        metrics = run_suite._headline_metrics(_stats_run_dir(self, _cascor_stats(train_accuracy=0.0, val_accuracy=0.0)))
        self.assertEqual(metrics, {"train_accuracy": 0.0, "val_accuracy": 0.0})

    def test_bool_none_and_strings_are_dropped(self) -> None:
        cases = [((True, None), {}), (("0.9", False), {}), ((None, "0.91875"), {}), ((False, 0.5), {"val_accuracy": 0.5}), (("0.88", 1), {"val_accuracy": 1})]
        for (train, val), expected in cases:
            with self.subTest(train=train, val=val):
                stats = _cascor_stats(train_accuracy=train, val_accuracy=val)
                self.assertEqual(run_suite._headline_metrics(_stats_run_dir(self, stats)), expected)

    def test_a_run_without_a_val_split_yields_train_accuracy_alone(self) -> None:
        # 22 of 426 corpus cascor stats.json carry no number at final.val_accuracy: no column, not a zero.
        metrics = run_suite._headline_metrics(_stats_run_dir(self, _cascor_stats(train_accuracy=0.88, val_accuracy=None, f1=0.9)))
        self.assertEqual(metrics, {"train_accuracy": 0.88})

    def test_the_dead_names_at_the_top_of_the_block_yield_nothing(self) -> None:
        # The pre-fix reader looked HERE. A writer that also put them here, or a reader that fell back to them,
        # would report the decoys; and the eval scalars never become a headline.
        stats = _cascor_stats(epoch=3, f1=0.9, precision=0.9, recall=0.9, roc_auc=0.95)
        stats["cascor"].update({"final_accuracy": 0.99, "test_accuracy": 0.98, "val_accuracy": 0.97, "train_accuracy": 0.96})
        self.assertEqual(run_suite._headline_metrics(_stats_run_dir(self, stats)), {})

    def test_a_non_finite_accuracy_is_kept_as_a_value(self) -> None:
        # Kept, not dropped: a band must FAIL it (ruling 4), which it cannot do to a value it never sees.
        metrics = run_suite._headline_metrics(_stats_run_dir(self, _cascor_stats(train_accuracy=float("nan"), val_accuracy=float("-inf"))))
        self.assertEqual(sorted(metrics), ["train_accuracy", "val_accuracy"])
        self.assertTrue(math.isnan(metrics["train_accuracy"]))
        self.assertEqual(metrics["val_accuracy"], float("-inf"))

    def test_a_stats_file_with_both_blocks_reads_both_tables(self) -> None:
        stats = _cascor_stats(train_accuracy=0.7, val_accuracy=0.6)
        stats["recurrence"] = _recurrence_stats(train_r2=0.5, cv_r2=0.25, cv_r2_std=0.05)["recurrence"]
        self.assertEqual(run_suite._headline_metrics(_stats_run_dir(self, stats)), {"train_accuracy": 0.7, "val_accuracy": 0.6, "train_r2": 0.5, "cv_r2": 0.25, "cv_r2_std": 0.05, "n_windows": 1346})

    def test_aggregate_csv_and_report_gain_the_cascor_columns(self) -> None:
        live = _stats_run_dir(self, _cascor_stats(**LIVE_CASCOR_METRICS))
        no_val = _stats_run_dir(self, _cascor_stats(train_accuracy=0.5, val_accuracy=None))
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        suite_dir = Path(tmp.name) / "suite"
        suite_dir.mkdir()
        rows = [
            {"cell_id": "c000", "run_dir": str(live), "outcome": "succeeded", "metrics": run_suite._headline_metrics(live)},
            {"cell_id": "c001", "run_dir": str(no_val), "outcome": "succeeded", "metrics": run_suite._headline_metrics(no_val)},
        ]
        (suite_dir / "registry.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
        cells = [{"cell_id": "c000", "name": "live", "overrides": {}}, {"cell_id": "c001", "name": "no-val", "overrides": {}}]
        self.assertEqual(run_suite.aggregate(suite_dir, {"name": "t", "description": "cascor headline columns"}, cells), 0)
        with (suite_dir / "aggregate.csv").open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            header = list(reader.fieldnames or [])
            csv_rows = list(reader)
        self.assertEqual([column for column in header if column.endswith("_accuracy")], ["train_accuracy", "val_accuracy"], "no final_accuracy / test_accuracy column")
        self.assertEqual((csv_rows[0]["train_accuracy"], csv_rows[0]["val_accuracy"]), ("0.905", "0.91875"))
        self.assertEqual((csv_rows[1]["train_accuracy"], csv_rows[1]["val_accuracy"]), ("0.5", ""), "no val split -- an empty cell, not 0")
        report = (suite_dir / "REPORT.md").read_text()
        self.assertIn("| cell | outcome | step_count | mean step (ms) | wall (s) | train_accuracy | val_accuracy |", report)
        self.assertIn("| 0.905 | 0.91875 |", report)
        self.assertIn("Cells: 2 total, 2 succeeded, 0 degraded, 0 failed/other, 0 not run.", report)


class RowMetricsTest(unittest.TestCase):
    """``_row_metrics``: the run's stats.json while it is readable, the row's recorded ``metrics`` only when it is not."""

    def test_a_readable_stats_file_wins_over_the_recorded_metrics(self) -> None:
        # The pre-fix registry: `metrics: {}` beside a stats.json that always held the accuracies.
        run_dir = _stats_run_dir(self, _cascor_stats(**LIVE_CASCOR_METRICS))
        self.assertEqual(run_suite._row_metrics({"run_dir": str(run_dir), "metrics": {}}), {"train_accuracy": 0.905, "val_accuracy": 0.91875})

    def test_a_readable_file_with_no_headline_is_empty_even_if_the_row_recorded_some(self) -> None:
        run_dir = _stats_run_dir(self, {"schema": "juniper-experiment-stats/1"})
        self.assertEqual(run_suite._row_metrics({"run_dir": str(run_dir), "metrics": {"val_accuracy": 0.5}}), {})

    def test_a_pruned_or_unreadable_run_falls_back_to_the_recorded_metrics(self) -> None:
        missing = _stats_run_dir(self, None)
        corrupt = _stats_run_dir(self, None)
        (corrupt / "artifacts" / "results" / "stats.json").write_text("{")
        for run_dir in (str(missing), str(corrupt), str(missing / "gone")):
            with self.subTest(run_dir=run_dir):
                self.assertEqual(run_suite._row_metrics({"run_dir": run_dir, "metrics": {"val_accuracy": 0.5}}), {"val_accuracy": 0.5})

    def test_no_run_dir_and_a_non_mapping_record_are_empty(self) -> None:
        self.assertEqual(run_suite._row_metrics({}), {})
        self.assertEqual(run_suite._row_metrics({"run_dir": None, "metrics": None}), {})
        self.assertEqual(run_suite._row_metrics({"run_dir": "", "metrics": ["val_accuracy"]}), {})


class ReaggregateTest(unittest.TestCase):
    """APD-ML-002 ruling 3: ``--reaggregate SUITE_DIR`` re-renders ``aggregate.csv`` + ``REPORT.md`` from disk and LAUNCHES NOTHING.

    The fixture is a cascor suite exactly as the pre-fix driver left it: every registry row ``metrics: {}``,
    an ``aggregate.csv`` with no headline column, and run dirs whose ``stats.json`` held the accuracies all
    along. ``--resume`` could not backfill it -- it would re-run every incomplete cell (29 of the corpus's 116
    cascor suites have one) -- so every seam that could launch, materialise or append is patched to RECORD
    and raise, and the files ``--reaggregate`` must not write are compared byte for byte.
    """

    CELLS: list[dict[str, Any]] = [
        {"cell_id": "c000-aaaa1111", "index": 0, "name": None, "config_path": "/x/base.yaml", "overrides": {"training.params.max_hidden_units": 2}},
        {"cell_id": "c001-bbbb2222", "index": 1, "name": None, "config_path": "/x/base.yaml", "overrides": {"training.params.max_hidden_units": 4}},
    ]
    PRE_FIX_CSV = "cell_id,name,run_id,outcome,exit_code,wall_seconds,step_count,mean_step_seconds,training.params.max_hidden_units,acceptance\n"

    def _pre_fix_suite(self, accuracies: "tuple[tuple[float, float], ...]" = ((0.905, 0.91875), (0.8125, 0.8))) -> "tuple[Path, Path]":
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        run_root = Path(tmp.name) / "runroot"
        suite_dir = run_root / "suites" / "t-suite-20261026T000000Z"
        suite_dir.mkdir(parents=True)
        manifest = {"schema": "juniper-experiment-suite/1", "suite_id": suite_dir.name, "suite": {"name": "t-suite", "description": "pre-fix cascor", "app": "cascor", "base_config": ["base.yaml"], "seed_policy": "fixed"}, "execution": {"mode": "sequential"}, "cells": self.CELLS, "suite_yaml_sha256": "0" * 64}
        (suite_dir / "suite_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        rows: list[dict[str, Any]] = []
        for cell, (train, val) in zip(self.CELLS, accuracies):
            run_dir = _stats_run_dir(self, _cascor_stats(train_accuracy=train, val_accuracy=val, f1=0.9), parent=run_root, name=f"20261026T00000{cell['index']}Z-ab0{cell['index']}")
            rows.append({"cell_id": cell["cell_id"], "name": None, "overrides": cell["overrides"], "run_id": run_dir.name, "outcome": "succeeded", "exit_code": 0, "error": None, "metrics": {}, "run_dir": str(run_dir), "wall_seconds": 100.0, "suite_id": suite_dir.name})
        (suite_dir / "registry.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
        (run_root / "index.jsonl").write_text("".join(json.dumps({"suite_id": suite_dir.name, "cell_id": row["cell_id"], "run_id": row["run_id"], "outcome": "succeeded", "run_dir": row["run_dir"]}) + "\n" for row in rows))
        (suite_dir / "aggregate.csv").write_text(self.PRE_FIX_CSV + "".join(f"{row['cell_id']},,{row['run_id']},succeeded,0,100.0,,,{row['overrides']['training.params.max_hidden_units']},\n" for row in rows))
        (suite_dir / "REPORT.md").write_text("# Suite report — t-suite\n")
        return run_root, suite_dir

    def _main(self, run_root: Path, *argv: str) -> "tuple[int, str, list]":
        """``run_suite.main`` with every launch seam patched to record the call and raise."""
        launched: list = []

        def _launch(*args: object, **kwargs: object) -> None:
            launched.append(args)
            raise AssertionError(f"--reaggregate reached a launch seam: {args!r}")

        buf = io.StringIO()
        with ExitStack() as stack:
            stack.enter_context(unittest.mock.patch.object(run_suite, "DEFAULT_RUN_ROOT", run_root))
            for seam in ("execute_cell", "materialise_cell", "_driver_module", "_append_jsonl"):
                stack.enter_context(unittest.mock.patch.object(run_suite, seam, _launch))
            for seam in ("run", "Popen"):
                stack.enter_context(unittest.mock.patch.object(run_suite.subprocess, seam, _launch))
            stack.enter_context(redirect_stdout(buf))
            stack.enter_context(redirect_stderr(buf))
            rc = run_suite.main(list(argv))
        return rc, buf.getvalue(), launched

    @staticmethod
    def _snapshot(run_root: Path, suite_dir: Path) -> "dict[str, bytes]":
        return {name: path.read_bytes() for name, path in (("registry", suite_dir / "registry.jsonl"), ("manifest", suite_dir / "suite_manifest.json"), ("index", run_root / "index.jsonl"))}

    def test_a_pre_fix_cascor_suite_gains_the_columns_and_nothing_launches(self) -> None:
        run_root, suite_dir = self._pre_fix_suite()
        before = self._snapshot(run_root, suite_dir)
        rc, out, launched = self._main(run_root, "--reaggregate", str(suite_dir))
        self.assertEqual(launched, [], "nothing may launch, materialise or append")
        self.assertEqual(rc, 0, msg=out)
        self.assertIn("launched nothing", out)
        with (suite_dir / "aggregate.csv").open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            header = list(reader.fieldnames or [])
            csv_rows = list(reader)
        self.assertEqual(header[-3:], ["train_accuracy", "val_accuracy", "acceptance"], "the headline columns precede the LAST acceptance column")
        self.assertEqual([(r["cell_id"], r["train_accuracy"], r["val_accuracy"]) for r in csv_rows], [("c000-aaaa1111", "0.905", "0.91875"), ("c001-bbbb2222", "0.8125", "0.8")])
        report = (suite_dir / "REPORT.md").read_text()
        self.assertIn("| training.params.max_hidden_units | train_accuracy | val_accuracy |", report)
        self.assertIn("| 2 | 0.905 | 0.91875 |", report)
        self.assertIn("Cells: 2 total, 2 succeeded, 0 degraded, 0 failed/other, 0 not run.", report)
        self.assertEqual(self._snapshot(run_root, suite_dir), before, "registry.jsonl, suite_manifest.json and index.jsonl are read, never written")
        self.assertFalse((suite_dir / "cells").exists(), "no cell is materialised")

    def test_a_suite_id_resolves_under_the_run_root(self) -> None:
        run_root, suite_dir = self._pre_fix_suite()
        rc, out, launched = self._main(run_root, "--reaggregate", suite_dir.name)
        self.assertEqual((rc, launched), (0, []), msg=out)
        self.assertIn("val_accuracy", (suite_dir / "aggregate.csv").read_text().splitlines()[0])

    def test_an_incomplete_suite_keeps_its_exit_code_and_is_not_rerun(self) -> None:
        # The case --resume cannot serve: a failed cell. Re-rendering reports it; it never re-runs it.
        run_root, suite_dir = self._pre_fix_suite()
        rows = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        rows[1].update(outcome="failed", exit_code=1, error="driver exit 1")
        (suite_dir / "registry.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
        rc, out, launched = self._main(run_root, "--reaggregate", str(suite_dir))
        self.assertEqual((rc, launched), (1, []), msg=out)
        self.assertIn("Cells: 2 total, 1 succeeded, 0 degraded, 1 failed/other, 0 not run.", (suite_dir / "REPORT.md").read_text())

    def test_a_pruned_run_dir_keeps_the_recorded_metrics(self) -> None:
        run_root, suite_dir = self._pre_fix_suite()
        rows = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        rows[1]["run_dir"] = str(run_root / "pruned-run")
        rows[1]["metrics"] = {"val_accuracy": 0.75}
        (suite_dir / "registry.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
        rc, out, launched = self._main(run_root, "--reaggregate", str(suite_dir))
        self.assertEqual((rc, launched), (0, []), msg=out)
        with (suite_dir / "aggregate.csv").open(newline="", encoding="utf-8") as handle:
            csv_rows = list(csv.DictReader(handle))
        self.assertEqual([(r["train_accuracy"], r["val_accuracy"]) for r in csv_rows], [("0.905", "0.91875"), ("", "0.75")])

    def test_compare_baseline_is_honoured(self) -> None:
        run_root, suite_dir = self._pre_fix_suite()
        with unittest.mock.patch.object(run_suite, "_run_comparison", lambda tag, directory: f"verdict: PASS  (baseline {tag!r}, {directory.name})"):
            rc, out, launched = self._main(run_root, "--reaggregate", str(suite_dir), "--compare-baseline", "pf1")
        self.assertEqual((rc, launched), (0, []), msg=out)
        self.assertIn(f"verdict: PASS  (baseline 'pf1', {suite_dir.name})", (suite_dir / "REPORT.md").read_text())

    def test_the_execution_flags_are_refused_before_anything_is_written(self) -> None:
        for extra in (["--suite", "suite.yaml"], ["--dry-run"], ["--resume", "t-suite-20261026T000000Z"], ["--only", "c000-aaaa1111"], ["--shared-equities-cache", "/srv/equities-cache"]):
            with self.subTest(extra=extra):
                run_root, suite_dir = self._pre_fix_suite()
                rc, out, launched = self._main(run_root, "--reaggregate", str(suite_dir), *extra)
                self.assertEqual((rc, launched), (2, []), msg=out)
                self.assertIn(f"takes no {extra[0]}", out)
                self.assertNotIn("val_accuracy", (suite_dir / "aggregate.csv").read_text(), "a refused --reaggregate renders nothing")

    def test_a_dir_without_a_usable_manifest_is_refused(self) -> None:
        run_root, suite_dir = self._pre_fix_suite()
        cases = {"missing": None, "not json": "{", "no suite name": json.dumps({"suite": {}, "cells": self.CELLS}), "no cells": json.dumps({"suite": {"name": "t"}, "cells": []}), "a cell without overrides": json.dumps({"suite": {"name": "t"}, "cells": [{"cell_id": "c000"}]}), "a malformed band": json.dumps({"suite": {"name": "t"}, "cells": [{"cell_id": "c000", "overrides": {}, "acceptance": [{"metric": "val_accuracy"}]}]})}
        for label, text in cases.items():
            with self.subTest(label=label):
                manifest = suite_dir / "suite_manifest.json"
                manifest.unlink(missing_ok=True)
                if text is not None:
                    manifest.write_text(text)
                rc, out, launched = self._main(run_root, "--reaggregate", str(suite_dir))
                self.assertEqual((rc, launched), (2, []), msg=out)
                self.assertIn("suite error: --reaggregate", out)
                self.assertNotIn("val_accuracy", (suite_dir / "aggregate.csv").read_text())

    def test_a_missing_suite_dir_is_refused(self) -> None:
        run_root, _suite_dir = self._pre_fix_suite()
        rc, out, launched = self._main(run_root, "--reaggregate", "no-such-suite")
        self.assertEqual((rc, launched), (2, []), msg=out)
        self.assertIn("no such suite dir", out)

    def test_without_suite_or_reaggregate_is_misuse(self) -> None:
        # `--suite` stopped being an argparse `required=True` so --reaggregate can omit it; every other mode still needs it.
        buf = io.StringIO()
        with self.assertRaises(SystemExit) as ctx, redirect_stdout(buf), redirect_stderr(buf):
            run_suite.main([])
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("--suite is required", buf.getvalue())


def _v1_run_dir(case: unittest.TestCase, metrics_final: "dict | None", parent: "Path | None" = None, name: str = "run") -> Path:
    """A run dir as a driver before juniper-ml#2064 left it: a ``juniper-experiment-stats/1`` stats.json (the real cascor
    block, its ``eval_scalars`` the unlabelled in-loop values) and, when given, the ``metrics_final.json`` beside it."""
    run_dir = _stats_run_dir(case, {"schema": "juniper-experiment-stats/1", "cascor": json.loads(json.dumps(V1_STATS_CASCOR))}, parent=parent, name=name)
    if metrics_final is not None:
        (run_dir / "artifacts" / "results" / "metrics_final.json").write_text(json.dumps(metrics_final))
    return run_dir


class CascorHeldOutColumnsTest(unittest.TestCase):
    """juniper-ml#2064 (APD-ML-002 ruling 1's "test later"): the held-out ``test_*`` headline columns.

    They come from the labelled final-evaluation block (``stats["cascor"]["eval_scalars"]``) and ONLY when it scored
    the ``test`` split. With no test split loaded cascor scores validation, which early stopping read, and that block
    fills no ``test_*`` column; neither do the in-loop values nor a run with no final evaluation. A stats.json written
    before juniper-ml#2064 has no such block, so the reader re-derives it from the run's ``metrics_final.json`` -- the
    path ``--reaggregate`` gives an older suite its columns by, without rewriting a single run file.
    """

    TEST_COLUMNS_BEFORE_731 = {"test_f1": 0.899749373433584, "test_precision": 0.9020979020979021, "test_recall": 0.8994165045846069, "test_roc_auc": 0.9605445957210336}
    TRAIN_AND_VAL = {"train_accuracy": 0.905, "val_accuracy": 0.91875}

    def test_a_test_split_final_evaluation_yields_every_test_column(self) -> None:
        metrics = run_suite._headline_metrics(_stats_run_dir(self, _cascor_stats(**with_final_accuracy(METRICS_FINAL_TEST_SPLIT, 0.9))))
        self.assertEqual(metrics, {**self.TRAIN_AND_VAL, "test_accuracy": 0.9, **self.TEST_COLUMNS_BEFORE_731})

    def test_a_service_before_juniper_cascor_731_yields_every_test_column_but_accuracy(self) -> None:
        metrics = run_suite._headline_metrics(_stats_run_dir(self, _cascor_stats(**METRICS_FINAL_TEST_SPLIT)))
        self.assertEqual(metrics, {**self.TRAIN_AND_VAL, **self.TEST_COLUMNS_BEFORE_731})

    def test_a_validation_split_final_evaluation_fills_no_test_column(self) -> None:
        # Its accuracy is a real number: a reader that did not check the split would put a selected-on score in test_accuracy.
        metrics = run_suite._headline_metrics(_stats_run_dir(self, _cascor_stats(**with_final_accuracy(METRICS_FINAL_VALIDATION_SPLIT, 0.35))))
        self.assertEqual(metrics, {"train_accuracy": 0.571875, "val_accuracy": 0.35})

    def test_no_final_evaluation_and_the_in_loop_values_fill_no_test_column(self) -> None:
        disabled = json.loads(json.dumps(METRICS_FINAL_TEST_SPLIT))
        disabled["eval_metrics"].update(enabled=False, final=None)
        cases = [("a service before the final evaluation", METRICS_FINAL_PRE_SWITCH, {"train_accuracy": 0.505}), ("a null final", METRICS_FINAL_NULL_FINAL, {"train_accuracy": 0.48333333333333334}), ("eval metrics disabled", disabled, self.TRAIN_AND_VAL)]
        for label, body, expected in cases:
            with self.subTest(label):
                self.assertEqual(run_suite._headline_metrics(_stats_run_dir(self, _cascor_stats(**body))), expected)

    def test_undefined_bool_and_non_finite_test_values(self) -> None:
        # An undefined accuracy (None, with cascor's reason) and a bool are no column; NaN is a column, so a band FAILS it (ruling 4).
        body = with_final_accuracy(METRICS_FINAL_TEST_SPLIT, None, "empty_batch")
        body["eval_metrics"]["final"].update(f1=True, roc_auc=float("nan"))
        metrics = run_suite._headline_metrics(_stats_run_dir(self, _cascor_stats(**body)))
        self.assertEqual(sorted(column for column in metrics if column.startswith("test_")), ["test_precision", "test_recall", "test_roc_auc"])
        self.assertTrue(math.isnan(metrics["test_roc_auc"]))
        self.assertEqual([r["result"] for r in run_suite.evaluate_acceptance([{"metric": "test_roc_auc", "min": 0.5, "max": None, "mode": "gate"}], metrics)], ["fail"])

    def test_a_schema_1_stats_json_re_derives_the_block_from_metrics_final_json(self) -> None:
        # Run 20260916T002848Z-3959 as the /1 driver left it: its eval_scalars (f1 0.9187, in-loop) must appear nowhere.
        metrics = run_suite._headline_metrics(_v1_run_dir(self, METRICS_FINAL_TEST_SPLIT))
        self.assertEqual(metrics, {**self.TRAIN_AND_VAL, **self.TEST_COLUMNS_BEFORE_731})
        self.assertNotIn(V1_STATS_CASCOR["eval_scalars"]["f1"], metrics.values())

    def test_a_schema_1_stats_json_without_a_test_block_beside_it_fills_nothing(self) -> None:
        for label, body in (("a validation final block", METRICS_FINAL_VALIDATION_SPLIT), ("no final block", METRICS_FINAL_PRE_SWITCH), ("no metrics_final.json", None)):
            with self.subTest(label):
                self.assertEqual(run_suite._headline_metrics(_v1_run_dir(self, body)), self.TRAIN_AND_VAL)

    def test_a_labelled_stats_json_is_never_overruled_by_metrics_final_json(self) -> None:
        # The writer already derived the block, and it found none. A test-split metrics_final.json beside it is not read.
        run_dir = _stats_run_dir(self, _cascor_stats(**METRICS_FINAL_PRE_SWITCH))
        (run_dir / "artifacts" / "results" / "metrics_final.json").write_text(json.dumps(with_final_accuracy(METRICS_FINAL_TEST_SPLIT, 0.9)))
        self.assertEqual(run_suite._headline_metrics(run_dir), {"train_accuracy": 0.505})

    def test_row_metrics_re_derives_for_a_schema_1_row(self) -> None:
        run_dir = _v1_run_dir(self, METRICS_FINAL_TEST_SPLIT)
        self.assertEqual(run_suite._row_metrics({"run_dir": str(run_dir), "metrics": {}}), {**self.TRAIN_AND_VAL, **self.TEST_COLUMNS_BEFORE_731})

    def test_reaggregate_backfills_a_schema_1_suite_and_rewrites_no_run_file(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        run_root = Path(tmp.name) / "runroot"
        suite_dir = run_root / "suites" / "t-v1-suite-20260920T000000Z"
        suite_dir.mkdir(parents=True)
        cells = [{"cell_id": "c000-aaaa1111", "index": 0, "name": "test-split", "config_path": "/x/base.yaml", "overrides": {"training.params.max_hidden_units": 16}}, {"cell_id": "c001-bbbb2222", "index": 1, "name": "validation-split", "config_path": "/x/base.yaml", "overrides": {"training.params.max_hidden_units": 2}}]
        (suite_dir / "suite_manifest.json").write_text(json.dumps({"schema": "juniper-experiment-suite/1", "suite_id": suite_dir.name, "suite": {"name": "t-v1-suite", "description": "a cascor suite run before juniper-ml#2064", "app": "cascor"}, "cells": cells}))
        rows = []
        for cell, body in zip(cells, (METRICS_FINAL_TEST_SPLIT, METRICS_FINAL_VALIDATION_SPLIT)):
            run_dir = _v1_run_dir(self, body, parent=run_root, name=f"2026092000000{cell['index']}Z-ab0{cell['index']}")
            rows.append({"cell_id": cell["cell_id"], "name": cell["name"], "overrides": cell["overrides"], "run_id": run_dir.name, "outcome": "succeeded", "exit_code": 0, "error": None, "metrics": {}, "run_dir": str(run_dir), "wall_seconds": 30.0, "suite_id": suite_dir.name})
        (suite_dir / "registry.jsonl").write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows))
        before = {str(path): path.read_bytes() for path in sorted(run_root.rglob("*")) if path.is_file()}

        def _launch(*args: object, **kwargs: object) -> None:
            raise AssertionError(f"--reaggregate reached a launch seam: {args!r}")

        buf = io.StringIO()
        with ExitStack() as stack:
            stack.enter_context(unittest.mock.patch.object(run_suite, "DEFAULT_RUN_ROOT", run_root))
            for seam in ("execute_cell", "materialise_cell", "_driver_module", "_append_jsonl"):
                stack.enter_context(unittest.mock.patch.object(run_suite, seam, _launch))
            stack.enter_context(redirect_stdout(buf))
            stack.enter_context(redirect_stderr(buf))
            rc = run_suite.main(["--reaggregate", str(suite_dir)])
        self.assertEqual(rc, 0, msg=buf.getvalue())
        with (suite_dir / "aggregate.csv").open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            header = list(reader.fieldnames or [])
            table = {row["name"]: row for row in reader}
        self.assertEqual([column for column in header if column.startswith("test_")], ["test_f1", "test_precision", "test_recall", "test_roc_auc"], "no test_accuracy: these bodies predate juniper-cascor#731")
        self.assertEqual([table["test-split"][column] for column in ("test_f1", "test_roc_auc", "val_accuracy")], ["0.899749373433584", "0.9605445957210336", "0.91875"])
        self.assertEqual([table["validation-split"][column] for column in ("test_f1", "test_precision", "test_recall", "test_roc_auc")], ["", "", "", ""], "a validation block fills no test_* column")
        self.assertIn("| test_f1 | test_precision | test_recall | test_roc_auc |", (suite_dir / "REPORT.md").read_text())
        after = {str(path): path.read_bytes() for path in sorted(run_root.rglob("*")) if path.is_file() and path.name not in ("aggregate.csv", "REPORT.md")}
        self.assertEqual(after, before, "no stats.json, metrics_final.json, registry or manifest is written -- only the two rendered files change")


# =====================================================================================
# D2 (2026-09-22): the ``runtime:`` block binds
# =====================================================================================


def _restore_environ(saved: "dict[str, str]") -> None:
    """Restore ``os.environ`` in place.

    A named function rather than ``lambda: (os.environ.clear(), os.environ.update(saved))``:
    ``clear()`` returns ``None``, so the tuple form is a mypy ``func-returns-value`` error and,
    more to the point, reads as if it were building a value it then discards.
    """
    os.environ.clear()
    os.environ.update(saved)


class TestRuntimeBlockEnv(unittest.TestCase):
    """``runtime:`` -> process environment (owner decision D2).

    The failure this pins is not a crash, it is a **silent no-op**: before
    ``runtime_block_env`` existed, ``run_experiment`` validated all three ``RUNTIME_KEYS``
    and nothing read any of them, so a suite could set ``blas_threads`` and run 16-wide, and
    a matrix could *vary* the key and measure one configuration N times. Every assertion here
    is therefore about a value actually arriving somewhere, never about a call succeeding.
    """

    def test_absent_block_sets_nothing(self) -> None:
        """No ``runtime:`` must leave the launcher's inherited environment untouched."""
        self.assertEqual(run_suite.runtime_block_env({"experiment": {"name": "x"}}), {})

    def test_blas_threads_fans_out_to_all_three_families(self) -> None:
        """Pinning one BLAS family leaves the others at 'every core', so all three or none."""
        env = run_suite.runtime_block_env({"runtime": {"blas_threads": 2}})
        self.assertEqual(env, {"OMP_NUM_THREADS": "2", "MKL_NUM_THREADS": "2", "OPENBLAS_NUM_THREADS": "2"})

    def test_num_processes_maps_to_the_cascor_variable(self) -> None:
        self.assertEqual(run_suite.runtime_block_env({"runtime": {"num_processes": 4}}), {"CASCOR_NUM_PROCESSES": "4"})

    def test_eval_metrics_false_emits_the_word_not_a_blank(self) -> None:
        """cascor's ``_env_flag`` treats BLANK as the default, and that default is True.

        Emitting ``""`` for ``false`` would therefore ENABLE the thing the config disabled --
        a silent inversion, which is worse than the no-op this whole function replaces.
        """
        env = run_suite.runtime_block_env({"runtime": {"eval_metrics_enabled": False}})
        self.assertEqual(env, {"JUNIPER_CASCOR_EVAL_METRICS_ENABLED": "false"})
        self.assertNotEqual(env["JUNIPER_CASCOR_EVAL_METRICS_ENABLED"], "")

    def test_eval_metrics_true_emits_true(self) -> None:
        self.assertEqual(run_suite.runtime_block_env({"runtime": {"eval_metrics_enabled": True}}), {"JUNIPER_CASCOR_EVAL_METRICS_ENABLED": "true"})

    def test_all_three_keys_together(self) -> None:
        env = run_suite.runtime_block_env({"runtime": {"blas_threads": 8, "num_processes": 2, "eval_metrics_enabled": True}})
        self.assertEqual(env["OMP_NUM_THREADS"], "8")
        self.assertEqual(env["CASCOR_NUM_PROCESSES"], "2")
        self.assertEqual(env["JUNIPER_CASCOR_EVAL_METRICS_ENABLED"], "true")

    def test_non_mapping_runtime_is_refused(self) -> None:
        """``or {}`` guards ABSENCE, not TYPE -- a list is truthy-empty and would reach ``.get``."""
        for bad in ([], ["blas_threads"], "blas_threads: 2", 7):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(run_suite.SuiteError, "must be a mapping"):
                    run_suite.runtime_block_env({"runtime": bad})

    def test_non_positive_width_is_refused_not_dropped(self) -> None:
        """A dropped value reproduces the original defect one layer down: applied-looking, absent."""
        for bad in (0, -1, 1.5, "2"):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(run_suite.SuiteError, "positive integer"):
                    run_suite.runtime_block_env({"runtime": {"blas_threads": bad}})

    def test_null_CLEARS_a_key_rather_than_failing(self) -> None:
        """``null`` must mean "unpinned", not exit 2.

        ``_set_dotted`` cannot delete a key — it WRITES ``None`` — so
        ``matrix: {runtime.blas_threads: [2, null]}`` is the only way an author can express an
        unpinned cell. Rejecting ``None`` would mean the change that made ``blas_threads``
        matter simultaneously removed the only way to turn it off, and would do it by refusing
        the whole suite. The idiom is already in use on other keys
        (``suites/p4/e-e-recurrence-readout-spectrum.yaml`` clears ``train.rff_features``).
        """
        for key in ("blas_threads", "num_processes", "eval_metrics_enabled"):
            with self.subTest(key=key):
                self.assertEqual(run_suite.runtime_block_env({"runtime": {key: None}}), {})
        # …and a null alongside a real value clears only its own key.
        self.assertEqual(run_suite.runtime_block_env({"runtime": {"blas_threads": None, "num_processes": 2}}), {"CASCOR_NUM_PROCESSES": "2"})

    def test_cascor_only_knob_is_withheld_from_recurrence(self) -> None:
        """Same invariant ``thread_budget_env`` already holds: recurrence gets no cascor knob.

        It would otherwise land in the recurrence run's manifest ``thread_env`` and from there
        in a baseline's ``HOST.json.thread_budget``, which is a host-IDENTITY field — so a
        variable nothing reads could refuse a comparison.
        """
        self.assertEqual(run_suite.runtime_block_env({"runtime": {"num_processes": 4}}, "recurrence"), {})
        # Still validated, so a typo is not silently swallowed on the recurrence path either.
        with self.assertRaisesRegex(run_suite.SuiteError, "positive integer"):
            run_suite.runtime_block_env({"runtime": {"num_processes": 0}}, "recurrence")
        # blas_threads is NOT cascor-specific and must still apply.
        self.assertEqual(run_suite.runtime_block_env({"runtime": {"blas_threads": 4}}, "recurrence")["OMP_NUM_THREADS"], "4")

    def test_bool_is_not_accepted_as_a_width(self) -> None:
        """``bool`` is an ``int`` subclass, so ``blas_threads: true`` would silently mean 1."""
        with self.assertRaisesRegex(run_suite.SuiteError, "positive integer"):
            run_suite.runtime_block_env({"runtime": {"blas_threads": True}})
        with self.assertRaisesRegex(run_suite.SuiteError, "positive integer"):
            run_suite.runtime_block_env({"runtime": {"num_processes": False}})

    def test_non_bool_eval_metrics_is_refused(self) -> None:
        for bad in ("true", 1, 0):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(run_suite.SuiteError, "must be a boolean"):
                    run_suite.runtime_block_env({"runtime": {"eval_metrics_enabled": bad}})


class TestRuntimeBlockReachesTheLauncher(unittest.TestCase):
    """End-to-end: the resolved value must arrive in the launcher's PROCESS ENVIRONMENT.

    Unit-testing the mapping proves the dict is right; it does not prove anything is exported.
    These tests run a real suite against a stub launcher that dumps ``environ`` to disk, which
    is the only form of evidence that distinguishes "wired" from "computed and discarded" --
    the precise distinction this whole decision exists to repair.
    """

    BASE = """\
schema_version: 1
experiment:
  name: fixture
  seed: 7
service:
  log_level: INFO
dataset:
  generator: spiral
  params:
    n_points_per_spiral: 50
    n_spirals: 2
    noise: 0.1
training:
  params:
    max_hidden_units: 2
    max_iterations: 2
    output_epochs: 5
runtime:
  blas_threads: 3
  num_processes: 5
  eval_metrics_enabled: false
outputs:
  max_wall_seconds: 60
"""

    SUITE = """\
schema_version: 1
suite:
  name: d2-suite
  description: test
  app: cascor
  base_config:
    - {base}
  seed_policy: fixed
execution:
  mode: {mode}
  max_parallel: {par}
  continue_on_failure: true
  per_run_timeout_seconds: 900
matrix:
  training.params.max_hidden_units: [2]
{extra_matrix}
outputs:
  suite_dir: {suite_dir}
"""

    @staticmethod
    def _launched(dump: Path) -> "dict[str, str | None]":
        """Parse the stub launcher's KEY=VALUE dump. ``<UNSET>`` becomes ``None``.

        Last occurrence wins, so a multi-cell suite reports the final launch rather than
        silently blending appended rows from several cells.
        """
        parsed: "dict[str, str | None]" = {}
        for line in dump.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            key, _, value = line.partition("=")
            parsed[key] = None if value == "<UNSET>" else value
        return parsed

    def _run(self, mode: str, par: int, extra_matrix: str = ""):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "base.yaml").write_text(self.BASE)
        suite_dir = root / "out"
        (root / "suite.yaml").write_text(self.SUITE.format(base=root / "base.yaml", mode=mode, par=par, suite_dir=suite_dir, extra_matrix=extra_matrix))
        dump = root / "launcher-env.txt"
        launcher = root / "stub_launcher.bash"
        # Dump, from the launcher's OWN environment on --up, exactly the five variables under
        # test, as KEY=VALUE. This is the measurement.
        #
        # Deliberately NOT a python child that serialises the whole environment as a mapping:
        # `tests/test_env_repr_safety.py` forbids raw os.environ-derived mappings anywhere under
        # `tests/` (it greps line-by-line, so even naming the construct in a comment trips it),
        # because such a mapping sits as a frame-local and `--showlocals` renders real secrets at
        # the head of a failure paste. Naming the five is the sharper assertion anyway --
        # `${!v-<UNSET>}` distinguishes
        # UNSET from EMPTY, and that is the exact distinction both `runtime_block_env` (which
        # emits nothing for a cleared key) and the launcher's `runtime_env` array turn on.
        launcher.write_text("#!/usr/bin/env bash\n" 'if [[ "$1" == "--up" ]]; then\n' "  for v in OMP_NUM_THREADS MKL_NUM_THREADS OPENBLAS_NUM_THREADS CASCOR_NUM_PROCESSES JUNIPER_CASCOR_EVAL_METRICS_ENABLED; do\n" '    val="${!v-<UNSET>}"\n' f'    printf \'%s=%s\\n\' "$v" "$val" >> "{dump}"\n' "  done\n" '  echo "=== Experiment run stub-run-$$ is up ==="\n' "  exit 0\n" "fi\n" 'if [[ "$1" == "--down" ]]; then exit 0; fi\n' "exit 2\n")
        launcher.chmod(launcher.stat().st_mode | stat.S_IEXEC)
        driver = root / "stub_driver.py"
        _write_stub_driver(driver)
        run_root = root / "runroot"
        run_root.mkdir()
        old = run_suite.DEFAULT_RUN_ROOT
        run_suite.DEFAULT_RUN_ROOT = run_root  # type: ignore[attr-defined]
        self.addCleanup(lambda: setattr(run_suite, "DEFAULT_RUN_ROOT", old))
        # Pin a fake cascor tree at the parallel floor, as the D5 tests above do.
        #
        # Without it these cases are HOST-DEPENDENT and pass only by accident: `app: cascor`
        # with `max_parallel > 1` is gated by `check_cascor_parallel_floor`, which probes for a
        # juniper-cascor sibling ABOVE the repo. A developer checkout has one, so the parallel
        # cases went green locally; a CI runner does not, so the guard refused the suite (exit
        # 2) and the assertions failed on `rc`, not on the thing under test. Building the tree
        # makes the outcome a property of the code rather than of where it was cloned.
        cascor_tree = root / "juniper-cascor"
        (cascor_tree / "src").mkdir(parents=True, exist_ok=True)
        (cascor_tree / "pyproject.toml").write_text('[project]\nname = "juniper-cascor"\nversion = "' + ".".join(str(p) for p in run_suite.CASCOR_PARALLEL_FLOOR) + '"\n')
        env = {
            "JUNIPER_SUITE_LAUNCHER": str(launcher),
            "JUNIPER_SUITE_DRIVER": str(driver),
            "JUNIPER_SUITE_PYTHON": sys.executable,
            "JUNIPER_EXP_CASCOR_SRC_DIR": str(cascor_tree / "src"),
        }
        old_environ = RedactedEnv(os.environ)
        os.environ.update(env)
        self.addCleanup(_restore_environ, old_environ)
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            rc = run_suite.main(["--suite", str(root / "suite.yaml")])
        return rc, dump, suite_dir, buf.getvalue()

    def test_sequential_run_exports_the_configured_width(self) -> None:
        """Serial mode sets NO H-11 budget, so before D2 a serial suite ran fully unpinned."""
        rc, dump, _suite_dir, out = self._run("sequential", 1)
        self.assertEqual(rc, 0, msg=out)
        self.assertTrue(dump.is_file(), msg=f"launcher never ran\n{out}")
        launched = self._launched(dump)
        self.assertEqual(launched.get("OMP_NUM_THREADS"), "3")
        self.assertEqual(launched.get("MKL_NUM_THREADS"), "3")
        self.assertEqual(launched.get("OPENBLAS_NUM_THREADS"), "3")
        self.assertEqual(launched.get("CASCOR_NUM_PROCESSES"), "5")

    def test_a_matrix_override_beats_the_h11_parallel_budget(self) -> None:
        """PF-3's second axis IS per-cell thread width.

        ``thread_budget_env`` hard-codes cascor's BLAS vars to "2" for every parallel cell. If
        that won, every cell of PF-3 would run at width 2 and the axis would be inert -- the
        same defect that wasted PF-2's dataset axis. So a width the SUITE names must beat the
        H-11 split, and the registry row must make the override legible.
        """
        rc, dump, suite_dir, out = self._run("parallel", 2, extra_matrix="  runtime.blas_threads: [7]")
        self.assertEqual(rc, 0, msg=out)
        launched = self._launched(dump)
        self.assertEqual(launched.get("OMP_NUM_THREADS"), "7", msg="the H-11 split must not overwrite a width the matrix names")
        row = json.loads((suite_dir / "registry.jsonl").read_text().splitlines()[0])
        self.assertEqual(row["runtime_env"]["OMP_NUM_THREADS"], "7")
        self.assertEqual(row["thread_budget"]["OMP_NUM_THREADS"], run_suite.thread_budget_env("cascor", 2)["OMP_NUM_THREADS"], msg="both must be recorded, or the override is invisible in the evidence")

    def test_an_INHERITED_width_does_NOT_beat_the_h11_budget(self) -> None:
        """The override is scoped to intent, and an inherited value carries none.

        The base config here sets ``blas_threads: 3`` and the suite never mentions it — exactly
        the shape of `spiral-baseline.yaml`, which sets ``num_processes: 4``. If an inherited
        value won, any parallel cascor suite built on that base would silently disarm the H-11
        split: 4 cells x 4 processes on a 16-core host, 2x oversubscribed, and invisible because
        `REPORT.md` prints neither budget. H-11 is a safety budget; only a suite that ASKS for a
        width gets to spend it.
        """
        rc, dump, _suite_dir, out = self._run("parallel", 2)
        self.assertEqual(rc, 0, msg=out)
        launched = self._launched(dump)
        # Expected values are DERIVED from `thread_budget_env`, never written as literals: its
        # split is `max(1, nproc // (2 * max_parallel))`, so a hard-coded "4" encodes this
        # 16-core host and reads '1' on a 2-core CI runner. That is the same host-dependence
        # that made these cases vacuous before the cascor tree was pinned, one layer down —
        # and the literal would have failed loudly rather than silently, but only in CI.
        expected = run_suite.thread_budget_env("cascor", 2)
        self.assertEqual(launched.get("OMP_NUM_THREADS"), expected["OMP_NUM_THREADS"], msg="an inherited width must lose to the H-11 split")
        self.assertEqual(launched.get("CASCOR_NUM_PROCESSES"), expected["CASCOR_NUM_PROCESSES"], msg="H-11's split, not the base config's 5")
        # …and the point of the test: the base config's values are the ones that must NOT win.
        self.assertNotEqual(launched.get("OMP_NUM_THREADS"), "3", msg="the base config's inherited blas_threads must not reach the launcher")
        self.assertNotEqual(launched.get("CASCOR_NUM_PROCESSES"), "5", msg="the base config's inherited num_processes must not reach the launcher")

    def test_eval_metrics_is_exempt_from_the_h11_contest(self) -> None:
        """H-11 is a THREAD budget and has no opinion about eval metrics.

        The parallel filter must not sweep up a key the budget never contests. The base config
        sets ``eval_metrics_enabled: false`` and the suite never names it, so it is inherited —
        yet it must still reach the launcher in parallel mode, unlike the inherited width above.
        """
        rc, dump, _suite_dir, out = self._run("parallel", 2)
        self.assertEqual(rc, 0, msg=out)
        launched = self._launched(dump)
        self.assertEqual(launched.get("JUNIPER_CASCOR_EVAL_METRICS_ENABLED"), "false", msg="an inherited non-thread key must survive the parallel filter")
        # …while, in the same run, the inherited THREAD keys did lose to H-11.
        self.assertEqual(launched.get("OMP_NUM_THREADS"), run_suite.thread_budget_env("cascor", 2)["OMP_NUM_THREADS"])

    def test_a_bad_runtime_value_refuses_the_suite_before_any_cell_launches(self) -> None:
        """Fail-closed, and fail EARLY -- the D5 lesson: a late guard has already written evidence."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "base.yaml").write_text(self.BASE.replace("blas_threads: 3", "blas_threads: 0"))
        suite_dir = root / "out"
        (root / "suite.yaml").write_text(self.SUITE.format(base=root / "base.yaml", mode="sequential", par=1, suite_dir=suite_dir, extra_matrix=""))
        dump = root / "launcher-env.json"
        launcher = root / "stub_launcher.bash"
        launcher.write_text("#!/usr/bin/env bash\n" f'touch "{dump}"\n' 'echo "=== Experiment run stub-run-$$ is up ==="\n' "exit 0\n")
        launcher.chmod(launcher.stat().st_mode | stat.S_IEXEC)
        driver = root / "stub_driver.py"
        _write_stub_driver(driver)
        old_environ = RedactedEnv(os.environ)
        os.environ.update({"JUNIPER_SUITE_LAUNCHER": str(launcher), "JUNIPER_SUITE_DRIVER": str(driver), "JUNIPER_SUITE_PYTHON": sys.executable})
        self.addCleanup(_restore_environ, old_environ)
        buf = io.StringIO()
        with redirect_stdout(buf), redirect_stderr(buf):
            rc = run_suite.main(["--suite", str(root / "suite.yaml")])
        self.assertEqual(rc, 2, msg=buf.getvalue())
        self.assertIn("positive integer", buf.getvalue())
        self.assertFalse(dump.exists(), "the launcher must never have been invoked")


class TestDatasetBudgetReachesDriverAndService(unittest.TestCase):
    """W1.5 (F-D5 / F-S9): the dataset-create budget reaches the driver and, for recurrence, the service.

    ``execution.dataset_create_timeout_seconds`` is forwarded as ``--dataset-create-timeout-seconds`` on
    the ``max_wall_seconds`` rule: omitted when unset, so the driver owns its default. A recurrence cell's
    budget -- that key, else the cell's own ``outputs.dataset_create_timeout_seconds`` -- is exported to
    ``--up`` as ``JUNIPER_RECURRENCE_JUNIPER_DATA_TIMEOUT_SECONDS``. It is read back from the stub
    launcher's own environment, which tells "exported" apart from "computed and dropped", and by name
    (``${VAR-<UNSET>}``), never as a dumped mapping (``tests/test_env_repr_safety.py``).
    """

    VAR = "JUNIPER_RECURRENCE_JUNIPER_DATA_TIMEOUT_SECONDS"

    RECURRENCE_BASE = "schema_version: 1\nexperiment:\n  name: fixture\n  seed: 7\ndataset:\n  generator: irregular_sine\n  split: train\n  params:\n    n_steps: 200\n    lookback: 16\ntrain:\n  d: 4\n  ridge: 1.0\n  readout: linear\noutputs:\n  max_wall_seconds: 60\n"

    SUITE = "schema_version: 1\nsuite:\n  name: w15-suite\n  description: test\n  app: {app}\n  base_config:\n    - {base}\n  seed_policy: fixed\nexecution:\n  mode: sequential\n  continue_on_failure: true\n  per_run_timeout_seconds: 1800\n{execution_extra}matrix:\n  {matrix_key}: [{matrix_value}]\noutputs:\n  suite_dir: {suite_dir}\n"

    def _run(self, *, app: str = "recurrence", suite_budget: "str | None" = None, cell_budget: "str | None" = None, ambient: "str | None" = None, dry_run: bool = False) -> "tuple[int, str, list, list, list]":
        """One suite; returns ``(rc, output, launcher values, driver argvs, registry rows)``."""
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        base = root / "base.yaml"
        if app == "recurrence":
            base.write_text(self.RECURRENCE_BASE + (f"  dataset_create_timeout_seconds: {cell_budget}\n" if cell_budget is not None else ""))
            matrix_key, matrix_value = "train.d", 4
        else:
            base.write_text(BASE_CONFIG)
            matrix_key, matrix_value = "training.params.max_hidden_units", 2
        suite_dir = root / "out"
        execution_extra = f"  dataset_create_timeout_seconds: {suite_budget}\n" if suite_budget is not None else ""
        (root / "suite.yaml").write_text(self.SUITE.format(app=app, base=base, execution_extra=execution_extra, matrix_key=matrix_key, matrix_value=matrix_value, suite_dir=suite_dir))
        dump = root / "launcher-env.txt"
        launcher = root / "stub_launcher.bash"
        launcher.write_text("#!/usr/bin/env bash\n" 'if [[ "$1" == "--up" ]]; then\n' "  printf '%s\\n' \"${" + self.VAR + '-<UNSET>}" >> "' + str(dump) + '"\n' '  echo "=== Experiment run stub-run-$$ is up ==="\n' "  exit 0\n" "fi\n" 'if [[ "$1" == "--down" ]]; then exit 0; fi\n' "exit 2\n")
        launcher.chmod(launcher.stat().st_mode | stat.S_IEXEC)
        driver = root / "stub_driver.py"
        _write_stub_driver(driver)
        run_root = root / "runroot"
        run_root.mkdir()
        old_run_root = run_suite.DEFAULT_RUN_ROOT
        run_suite.DEFAULT_RUN_ROOT = run_root  # type: ignore[attr-defined]
        self.addCleanup(lambda: setattr(run_suite, "DEFAULT_RUN_ROOT", old_run_root))
        argv = ["--suite", str(root / "suite.yaml")] + (["--dry-run"] if dry_run else [])
        buf = io.StringIO()
        with unittest.mock.patch.dict(os.environ, {"JUNIPER_SUITE_LAUNCHER": str(launcher), "JUNIPER_SUITE_DRIVER": str(driver), "JUNIPER_SUITE_PYTHON": sys.executable}):
            os.environ.pop(self.VAR, None)
            if ambient is not None:
                os.environ[self.VAR] = ambient
            with redirect_stdout(buf), redirect_stderr(buf):
                rc = run_suite.main(argv)
        launched = dump.read_text().splitlines() if dump.exists() else []
        argvs = [json.loads(m.read_text())["argv"] for m in sorted(run_root.glob("*/manifest.json"))]
        registry = suite_dir / "registry.jsonl"
        rows = [json.loads(line) for line in registry.read_text().splitlines()] if registry.exists() else []
        return rc, buf.getvalue(), launched, argvs, rows

    def test_a_suite_budget_reaches_the_driver_flag_and_the_service_env(self) -> None:
        rc, out, launched, argvs, rows = self._run(suite_budget="600")
        self.assertEqual(rc, 0, msg=out)
        self.assertEqual(launched, ["600"])
        (argv,) = argvs
        self.assertEqual(argv[argv.index("--dataset-create-timeout-seconds") + 1], "600.0")
        self.assertEqual(rows[0]["service_env"], {self.VAR: "600"}, "the registry row records what --up was given")

    def test_a_cell_budget_reaches_the_service_while_the_driver_reads_it_itself(self) -> None:
        rc, out, launched, argvs, _rows = self._run(cell_budget="300.5")
        self.assertEqual(rc, 0, msg=out)
        self.assertEqual(launched, ["300.5"])
        self.assertNotIn("--dataset-create-timeout-seconds", argvs[0], "the YAML key reaches the driver through the cell YAML")

    def test_the_suite_budget_beats_the_cell_budget(self) -> None:
        rc, out, launched, argvs, _rows = self._run(suite_budget="900", cell_budget="300")
        self.assertEqual(rc, 0, msg=out)
        self.assertEqual(launched, ["900"])
        self.assertEqual(argvs[0][argvs[0].index("--dataset-create-timeout-seconds") + 1], "900.0")

    def test_no_budget_exports_nothing_and_leaves_an_operator_export_alone(self) -> None:
        rc, out, launched, argvs, rows = self._run()
        self.assertEqual(rc, 0, msg=out)
        self.assertEqual(launched, ["<UNSET>"], "the driver and service defaults are both 120 s")
        self.assertNotIn("--dataset-create-timeout-seconds", argvs[0])
        self.assertIsNone(rows[0]["service_env"])
        rc, out, launched, _argvs, _rows = self._run(ambient="77")
        self.assertEqual(rc, 0, msg=out)
        self.assertEqual(launched, ["77"], "with nothing configured, the operator's own export passes through")

    def test_a_cascor_suite_forwards_the_flag_but_exports_no_recurrence_env(self) -> None:
        rc, out, launched, argvs, rows = self._run(app="cascor", suite_budget="600")
        self.assertEqual(rc, 0, msg=out)
        self.assertEqual(launched, ["<UNSET>"])
        self.assertEqual(argvs[0][argvs[0].index("--dataset-create-timeout-seconds") + 1], "600.0")
        self.assertIsNone(rows[0]["service_env"])

    def test_dry_run_shows_the_flag_and_the_up_env(self) -> None:
        rc, out, launched, _argvs, _rows = self._run(suite_budget="600", dry_run=True)
        self.assertEqual(rc, 0, msg=out)
        self.assertRegex(out, rf"\$ {self.VAR}=600 \S+ --up --recurrence ")
        self.assertIn("--dataset-create-timeout-seconds 600.0", out)
        self.assertEqual(launched, [], "a dry run launches nothing")

    def test_a_bad_suite_budget_is_refused_before_any_cell_launches(self) -> None:
        for bad in ("0", "-1", "true", "'600'", ".inf", ".nan"):
            with self.subTest(bad=bad):
                rc, out, launched, _argvs, _rows = self._run(suite_budget=bad)
                self.assertEqual(rc, 2, msg=out)
                self.assertIn("execution.dataset_create_timeout_seconds must be a positive, finite number", out)
                self.assertEqual(launched, [])

    def test_a_bad_cell_budget_is_refused_by_the_driver_validator(self) -> None:
        rc, out, launched, _argvs, _rows = self._run(cell_budget="0")
        self.assertEqual(rc, 2, msg=out)
        self.assertIn("outputs.dataset_create_timeout_seconds must be a positive, finite number", out)
        self.assertEqual(launched, [])

    def test_the_mapping_itself(self) -> None:
        env = run_suite.recurrence_data_timeout_env
        self.assertEqual(env("cascor", {"outputs": {"dataset_create_timeout_seconds": 600}}, 900.0), {})
        self.assertEqual(env("recurrence", {"outputs": {"dataset_create_timeout_seconds": 600}}, 900.0), {self.VAR: "900"})
        self.assertEqual(env("recurrence", {"outputs": {"dataset_create_timeout_seconds": 600}}, None), {self.VAR: "600"})
        malformed_docs: "list[object]" = [{}, None, [], {"outputs": None}, {"outputs": [600]}]
        for doc in malformed_docs:
            self.assertEqual(env("recurrence", doc, None), {}, doc)
        bad_values: "list[object]" = [True, "600", 0, -5, float("inf"), float("nan")]
        for value in bad_values:
            self.assertEqual(env("recurrence", {"outputs": {"dataset_create_timeout_seconds": value}}, None), {}, value)

    def test_the_exported_text_is_the_form_the_launcher_accepts(self) -> None:
        """``_seconds_text`` mirrors ``experiment_stack.bash``'s ``data_timeout_re``, read from the script."""
        script = (REPO_ROOT / "util" / "experiment_stack.bash").read_text(encoding="utf-8")
        match = re.search(r"local data_timeout_re='([^']+)'", script)
        self.assertIsNotNone(match, "the launcher's data_timeout_re moved; update this mirror")
        pattern = match.group(1)
        for value, text in ((600, "600"), (600.0, "600"), (0.5, "0.5"), (300.5, "300.5"), (1.2, "1.2"), (1e-7, "0.0000001"), (1e22, "10000000000000000000000")):
            with self.subTest(value=value):
                self.assertEqual(run_suite._seconds_text(value), text)
                self.assertRegex(text, pattern)
                self.assertRegex(text, "[1-9]", "the launcher's second test: not all zeros")
                self.assertEqual(float(text), float(value))


class PerRunTimeoutBudgetTest(MainLoopTest):
    """juniper-ml#2210: ``per_run_timeout_seconds`` must exceed every cell's worst-case driver budget.

    BASE_CONFIG's cells come to 390 s: the health waits (2 x 90) + dataset creation (120) + the 60 s
    wall budget + the 30 s teardown settle. The refusal comes before the first ``--up``, so it leaves
    no launcher marker and no registry row.
    """

    def _set_timeout(self, root: Path, value: str, extra: str = "") -> None:
        suite_yaml = root / "suite.yaml"
        suite_yaml.write_text(suite_yaml.read_text().replace("  per_run_timeout_seconds: 900", f"  per_run_timeout_seconds: {value}{extra}"))

    def test_a_timeout_at_or_below_the_budget_refuses_the_suite_before_any_launch(self) -> None:
        for value in ("60", "390"):
            with self.subTest(per_run_timeout_seconds=value):
                root, suite_dir, markers, _run_root = self._setup()
                self._set_timeout(root, value)
                rc, out = self._main("--suite", str(root / "suite.yaml"))
                self.assertEqual(rc, 2, msg=out)
                self.assertIn(f"execution.per_run_timeout_seconds={value} does not exceed the worst-case driver budget of 2 of 2 cell(s)", out)
                self.assertIn("at 390s (health_wait 180 + dataset_create 120 + drive 60 + teardown_preempt 30)", out)
                self.assertEqual(list(markers.glob("up-*")), [], "refused before the first --up")
                self.assertFalse((suite_dir / "registry.jsonl").exists())

    def test_a_timeout_above_the_budget_runs(self) -> None:
        root, suite_dir, _markers, _run_root = self._setup()
        self._set_timeout(root, "391")
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0, msg=out)
        self.assertEqual(len((suite_dir / "registry.jsonl").read_text().splitlines()), 2)

    def test_the_forwarded_budgets_are_the_ones_summed(self) -> None:
        """``execution.max_wall_seconds`` and the dataset budget reach the driver as flags, and the
        flags beat the cell YAML, so the sum uses them."""
        root, _suite_dir, _markers, _run_root = self._setup()
        self._set_timeout(root, "14000", "\n  max_wall_seconds: 14400\n  dataset_create_timeout_seconds: 300")
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 2, msg=out)
        self.assertIn("at 14910s (health_wait 180 + dataset_create 300 + drive 14400 + teardown_preempt 30)", out)

    def test_the_default_is_named_as_the_default(self) -> None:
        root, _suite_dir, _markers, _run_root = self._setup()
        suite_yaml = root / "suite.yaml"
        suite_yaml.write_text(suite_yaml.read_text().replace("  per_run_timeout_seconds: 900\n", "  max_wall_seconds: 3600\n"))
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 2, msg=out)
        self.assertIn("execution.per_run_timeout_seconds=3600 (the default: the suite sets none) does not exceed", out)

    def test_without_the_driver_module_the_skipped_check_is_announced(self) -> None:
        root, _suite_dir, _markers, _run_root = self._setup()
        self._set_timeout(root, "60")
        with unittest.mock.patch.object(run_suite, "_driver_module", return_value=None):
            rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0, msg=out)
        self.assertIn("per_run_timeout_seconds was not checked against the cells' driver budgets", out)

    def test_the_refusal_names_the_largest_cell(self) -> None:
        """The cell with the largest sum is the one named, so its number is the one to beat."""
        budgets = {"c000-small": {"health_wait": 180.0, "drive": 60.0}, "c001-large": {"health_wait": 180.0, "drive": 900.0}}
        with self.assertRaises(run_suite.SuiteError) as caught:
            run_suite.check_per_run_timeout(1000.0, budgets)
        self.assertIn("of 1 of 2 cell(s); the largest is c001-large at 1080s (health_wait 180 + drive 900)", str(caught.exception))
        run_suite.check_per_run_timeout(1081.0, budgets)


class ExecuteCellTimeoutTest(unittest.TestCase):
    """What the subprocess kill leaves behind: the path ``check_per_run_timeout`` keeps an in-budget driver out of.

    juniper-ml#2210 found no test reaching it, because every ``execute_cell`` call here used a stub
    that exits at once. This driver sleeps through a 0.5 s ceiling.
    """

    def test_a_killed_driver_leaves_a_timed_out_row_without_the_manifest_evidence(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        markers = root / "markers"
        markers.mkdir()
        launcher = root / "stub_launcher.bash"
        _write_stub_launcher(launcher, markers)
        driver = root / "sleeping_driver.py"
        driver.write_text("import time\ntime.sleep(60)\n")
        cell_yaml = root / "experiment.yaml"
        cell_yaml.write_text(BASE_CONFIG)
        cell = {"cell_id": "c000-sleeper", "name": None, "overrides": {}}
        with unittest.mock.patch.object(run_suite, "DEFAULT_RUN_ROOT", root / "runroot"):
            row = run_suite.execute_cell(cell, cell_yaml, "cascor", 0.5, launcher, driver, sys.executable)
        self.assertEqual((row["outcome"], row["exit_code"], row["error"]), ("timed_out", None, "driver exceeded per_run_timeout_seconds=0.5"))
        for key in ("run_dir", "phases", "metrics"):
            self.assertNotIn(key, row, f"the kill returns before the manifest read, so the row carries no {key}")
        self.assertTrue(row["teardown_ok"])
        self.assertEqual(len(list(markers.glob("down-*"))), 1, "the stack is still torn down")
        self.assertNotIn("timed_out", run_suite.COMPLETE_OUTCOMES, "--resume runs the cell again")
