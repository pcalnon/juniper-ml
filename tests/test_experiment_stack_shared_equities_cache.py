#!/usr/bin/env python3
"""W5.6 (F-D6, plan H-9): ``--shared-equities-cache DIR`` on ``util/experiment_stack.bash`` and its ``run_suite.py`` passthrough.

Project:     Juniper
Sub-Project: juniper-ml
Application: regression tests (util/experiment_stack.bash, util/experiments/run_suite.py)
Author:      Paul Calnon
License:     MIT License

The equities end-to-end audit (plan §3.2, F-D6) found the launcher pinning juniper-data's
equities cache to ``${RUN_DIR}/equities-cache`` with no way out, so every cell of an equities
suite paid the cold Yahoo / SEC fetch again, while the experimentation plan's H-9 had promised a
``--shared-equities-cache`` opt-in for iterating on equities experiments. This is that opt-in.

What these pin:

- the contract text: usage and the header name the flag and ``JUNIPER_EXP_SHARED_EQUITIES_CACHE``;
  ``data_up`` resolves ``${EQUITIES_CACHE_DIR:-${RUN_DIR}/equities-cache}`` once and hands it to the
  announce line, ``env/launch.env`` and the launch; ``do_up`` prepares the cache after
  ``create_run_dir`` and before ``write_ports_json`` (fail-closed, locks released); teardown names
  no cache at all, so a shared directory can never be removed by ``--down``;
- misuse: a bare flag, a relative path on the flag and a relative path in the env each exit 2
  before any port is allocated (the data leg launches from the run dir, so a relative path would
  silently be per-run again);
- ``--dry-run --up``: the flag puts ``JUNIPER_DATA_EQUITIES_CACHE_DIR=DIR`` on the data launch and
  prints the ``mkdir -p`` without creating the directory; the default stays the per-run path; the
  env knob is the flag's equivalent; ``--shared-data`` makes the opt-in inert and says so;
- live ``data_up`` (PATH-stubbed, no network): the shared directory reaches the service's
  environment and ``env/launch.env`` and the per-run path does not;
- ``ports.json`` records ``equities_cache_dir`` and ``equities_cache_shared`` (true / false), with
  the globals unset too (the extracted-``recurrence_up`` shape the W1.9 edges suite runs);
- ``run_suite.py``: ``--shared-equities-cache DIR`` reaches every cell's ``--up`` and the registry row
  and ``suite_manifest.json``; ``JUNIPER_EXP_SHARED_EQUITIES_CACHE`` is honoured and passed
  explicitly; a relative path is refused (exit 2) before the suite dir exists; absent means absent;
  ``--dry-run`` prints it. Cell ids are unchanged -- the cache is not a suite key.

Reuses the sibling suites' helpers (``tests/test_experiment_stack_script.py`` for the launcher
harnesses, ``tests/test_run_suite_acceptance.py`` for the hermetic suite fixtures) through their
module objects, so none of their TestCases is collected here. Never brings a stack up, never
touches docker or the network.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import signal
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import tests.test_experiment_stack_script as stack
import tests.test_run_suite_acceptance as acceptance
from tests.process_cleanup import force_kill

run_suite = acceptance.run_suite
SANE = {"outcome": "succeeded", "cv_r2": -0.111, "cv_r2_std": 0.041}
ENV_KNOB = "JUNIPER_EXP_SHARED_EQUITIES_CACHE"


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _kill(pid: int) -> None:
    """``force_kill`` walks ``/proc`` (Linux); the stub listener is a single exec'd ``sleep``, so a plain SIGKILL covers a host without it."""
    if Path("/proc").is_dir():
        force_kill(pid)
        return
    # Already gone (the listener exited or was reaped) is the outcome wanted, not an error.
    with contextlib.suppress(ProcessLookupError):
        os.kill(pid, signal.SIGKILL)


def _data_announce_line(stdout: str) -> str:
    for line in stdout.splitlines():
        if "-m juniper_data --host 127.0.0.1 --port" in line:
            return line
    raise AssertionError(f"no juniper-data announce line in:\n{stdout}")


class TestStaticContract(unittest.TestCase):
    """The launcher text: flag, env knob, the one resolution site, the do_up order, teardown."""

    def test_usage_and_header_name_the_flag_and_the_env_knob(self) -> None:
        self.assertIn("[--shared-equities-cache DIR]", stack.SCRIPT_TEXT)
        self.assertIn("Env equivalent: JUNIPER_EXP_SHARED_EQUITIES_CACHE=DIR", stack.SCRIPT_TEXT)
        self.assertIn('SHARED_EQUITIES_CACHE="${JUNIPER_EXP_SHARED_EQUITIES_CACHE:-}"', stack.SCRIPT_TEXT)

    def test_data_up_resolves_the_cache_dir_once_with_the_per_run_default(self) -> None:
        data_up = stack._extract_experiment_fn("data_up")
        self.assertIn('cache_dir="${EQUITIES_CACHE_DIR:-${RUN_DIR}/equities-cache}"', data_up)
        self.assertEqual(data_up.count("JUNIPER_DATA_EQUITIES_CACHE_DIR=${cache_dir}"), 2, "the announce line and env/launch.env")
        self.assertIn('JUNIPER_DATA_EQUITIES_CACHE_DIR="${cache_dir}"', data_up, "the launch itself")
        self.assertNotIn("JUNIPER_DATA_EQUITIES_CACHE_DIR=${RUN_DIR}/equities-cache", data_up, "no site may bypass the resolved value")

    def test_do_up_prepares_the_cache_after_the_run_dir_and_before_ports_json(self) -> None:
        do_up = stack._extract_experiment_fn("do_up")
        self.assertIn("prepare_equities_cache || {", do_up, "fail-closed like the other staging steps")
        self.assertLess(do_up.index("create_run_dir || {"), do_up.index("prepare_equities_cache || {"))
        self.assertLess(do_up.index("prepare_equities_cache || {"), do_up.index("write_ports_json || {"), "ports.json must record the resolved cache")
        prepare = stack._extract_experiment_fn("prepare_equities_cache")
        self.assertIn("release_held_locks", do_up[do_up.index("prepare_equities_cache || {") :][:120])
        self.assertIn('[[ -n "${SHARED_DATA_URL}" ]]', prepare)
        self.assertIn("inert with --shared-data", prepare)
        self.assertIn("if is_dry; then return 0; fi", prepare, "a dry run creates nothing")

    def test_teardown_names_no_cache(self) -> None:
        for fn_name in ("teardown_run", "stop_service", "do_down"):
            body = stack._extract_experiment_fn(fn_name)
            self.assertNotIn("equities", body, f"{fn_name} must not know about the cache at all")
            self.assertNotIn("rm -r", body, f"{fn_name} deletes nothing")

    def test_relative_path_refusal_is_in_the_up_validation(self) -> None:
        self.assertIn('"${SHARED_EQUITIES_CACHE}" != /*', stack.SCRIPT_TEXT)
        self.assertIn("--shared-equities-cache needs an absolute path", stack.SCRIPT_TEXT)


class TestMisuse(stack._DryRunHarness):
    """Exit 2 before any allocation."""

    def _hermetic(self, root: Path) -> "dict[str, str]":
        return self._env(root, stack._stage_stub_bin(root), stack._stage_conda_fixture(root))

    def test_bare_flag_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = stack._run("--up", "--recurrence", "--shared-equities-cache", env_extra=self._hermetic(root))
            self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
            self.assertIn("--shared-equities-cache requires a value", result.stdout + result.stderr)
            self.assertFalse((root / "runs").exists())
            self.assertFalse((root / "locks").exists())

    def test_relative_flag_value_exits_2_before_any_allocation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = stack._run("--up", "--recurrence", "--shared-equities-cache", "shared/cache", env_extra=self._hermetic(root))
            self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
            self.assertIn("--shared-equities-cache needs an absolute path (got 'shared/cache')", result.stdout + result.stderr)
            self.assertFalse((root / "runs").exists(), "refused before the run root is touched")
            self.assertFalse((root / "locks").exists(), "refused before any port lock")

    def test_relative_env_value_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = self._hermetic(root)
            env[ENV_KNOB] = "relative-cache"
            result = stack._run("--up", "--recurrence", env_extra=env)
            self.assertEqual(result.returncode, 2, msg=result.stdout + result.stderr)
            self.assertIn("needs an absolute path (got 'relative-cache')", result.stdout + result.stderr)
            self.assertFalse((root / "locks").exists())

    def test_the_flag_does_not_disturb_down_or_status_parsing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = stack._run("--status", "--shared-equities-cache", "relative", env_extra=self._hermetic(root))
            self.assertNotEqual(result.returncode, 2, "the absolute-path rule is an --up rule; --status lists runs regardless")


class TestDryRun(stack._DryRunHarness):
    """``--dry-run --up`` prints the choice and creates nothing."""

    def test_flag_puts_the_shared_dir_on_the_data_launch_and_creates_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared = root / "shared-cache"
            result = self._dry_up(root, "--recurrence", "--shared-equities-cache", str(shared))
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn(f"JUNIPER_DATA_EQUITIES_CACHE_DIR={shared} ", _data_announce_line(result.stdout))
            self.assertIn(f"mkdir -p {shared}   # --shared-equities-cache (W5.6)", result.stdout)
            self.assertFalse(shared.exists(), "a dry run creates nothing, the shared dir included")
            self.assertFalse((root / "runs").exists())

    def test_default_stays_per_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            result = self._dry_up(root, "--recurrence")
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            line = _data_announce_line(result.stdout)
            self.assertIn(f"JUNIPER_DATA_EQUITIES_CACHE_DIR={root / 'runs'}/", line)
            self.assertIn("/equities-cache PYTHON_GIL=0", line, "the per-run path, directly under RUN_DIR")
            self.assertNotIn("--shared-equities-cache (W5.6)", result.stdout)
            self.assertNotIn("SHARED at", result.stdout)

    def test_env_knob_is_the_flags_equivalent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared = root / "shared-cache"
            env = self._env(root, stack._stage_stub_bin(root), stack._stage_conda_fixture(root))
            env[ENV_KNOB] = str(shared)
            result = stack._run("--dry-run", "--up", "--recurrence", env_extra=env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn(f"JUNIPER_DATA_EQUITIES_CACHE_DIR={shared} ", _data_announce_line(result.stdout))
            self.assertIn(f"mkdir -p {shared}", result.stdout)
            self.assertFalse(shared.exists())

    def test_flag_wins_over_the_env_knob(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = self._env(root, stack._stage_stub_bin(root), stack._stage_conda_fixture(root))
            env[ENV_KNOB] = str(root / "from-env")
            result = stack._run("--dry-run", "--up", "--recurrence", "--shared-equities-cache", str(root / "from-flag"), env_extra=env)
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn(f"JUNIPER_DATA_EQUITIES_CACHE_DIR={root / 'from-flag'} ", _data_announce_line(result.stdout))

    def test_inert_with_shared_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shared = root / "shared-cache"
            result = self._dry_up(root, "--recurrence", "--shared-data", "http://127.0.0.1:8100", "--shared-equities-cache", str(shared))
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            self.assertIn(f"NOTE: --shared-equities-cache {shared} is inert with --shared-data", result.stdout)
            self.assertNotIn(f"mkdir -p {shared}", result.stdout)
            self.assertNotIn("-m juniper_data --host", result.stdout, "no data leg of our own")


class TestDataUpLiveSharedCache(stack._LiveUpHarness):
    """Live ``data_up`` with ``EQUITIES_CACHE_DIR`` resolved to a shared directory (PATH stubs, no network)."""

    def test_shared_dir_reaches_the_service_env_and_launch_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "run"
            marker_dir = root / "markers"
            listeners_dir = root / "listeners"
            project_dir = root / "project"
            conda_dir = root / "conda"
            shared = root / "shared-cache"
            shared.mkdir()
            (project_dir / "juniper-cascor" / "src").mkdir(parents=True)
            stub_bin = stack._stage_live_path_stubs(root, listeners_dir)
            stack._write_listening_env_bin(conda_dir / "envs" / "JuniperData" / "bin" / "python", listeners_dir=listeners_dir, marker_dir=marker_dir, label="data")
            harness = self._common_prelude(run_dir=run_dir, conda_dir=conda_dir, project_dir=project_dir) + f'EQUITIES_CACHE_DIR="{shared}"\n' + stack._extract_experiment_fn("data_up") + "data_up\n"
            result = self._run_harness(harness, stub_bin=stub_bin)
            child_pid: "int | None" = None
            try:
                self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
                self.assertIn(f"JUNIPER_DATA_EQUITIES_CACHE_DIR={shared} ", result.stdout, "the announce line")
                pid_path = run_dir / "juniper-data.pid"
                self.assertTrue(pid_path.is_file(), "the F-6 listener pid is still recorded")
                child_pid = int(pid_path.read_text().strip())
                self.assertTrue(_alive(child_pid))
                env_text = (marker_dir / "data.env").read_text()
                cache_lines = stack._env_lines_for_key(env_text, "JUNIPER_DATA_EQUITIES_CACHE_DIR")
                self.assertEqual(cache_lines, [f"JUNIPER_DATA_EQUITIES_CACHE_DIR={shared}"], "the service sees the shared dir, and only it")
                self.assertIn(f"JUNIPER_DATA_STORAGE_PATH={run_dir}/data", stack._env_lines_for_key(env_text, "JUNIPER_DATA_STORAGE_PATH"), "storage stays per-run (H-8)")
                launch_env = (run_dir / "env" / "launch.env").read_text()
                self.assertIn(f"JUNIPER_DATA_EQUITIES_CACHE_DIR={shared}\n", launch_env)
                self.assertNotIn(f"{run_dir}/equities-cache", launch_env)
            finally:
                if child_pid is not None:
                    _kill(child_pid)


class TestPortsJsonRecord(unittest.TestCase):
    """``render_ports_json`` records the cache dir and whether it is the shared opt-in."""

    def _render(self, prelude: str) -> dict:
        script = "set -euo pipefail\n" + prelude + stack._extract_experiment_fn("json_number_or_null") + stack._extract_experiment_fn("json_string_or_null") + stack._extract_experiment_fn("render_ports_json") + 'render_ports_json false ""\n'
        result = subprocess.run(["/bin/bash", "-c", script], capture_output=True, text=True, timeout=stack.SCRIPT_TIMEOUT_SECONDS)
        self.assertEqual(result.returncode, 0, msg=result.stderr + result.stdout)
        return json.loads(result.stdout)

    def _base(self) -> str:
        return 'RUN_DIR="/tmp/run-w56"\nRUN_ID="20261019T000000Z-ab12"\nDATA_PORT=8110\nCASCOR_PORT=\nRECURRENCE_PORT=8260\nDATA_URL="http://127.0.0.1:8110"\nEXPERIMENT="cell-01"\n'

    def test_shared_records_the_dir_and_true(self) -> None:
        ports = self._render(self._base() + 'SHARED_EQUITIES_CACHE="/srv/equities-cache"\nEQUITIES_CACHE_DIR="/srv/equities-cache"\n')
        self.assertEqual(ports["equities_cache_dir"], "/srv/equities-cache")
        self.assertIs(ports["equities_cache_shared"], True)

    def test_default_records_the_per_run_dir_and_false(self) -> None:
        ports = self._render(self._base() + 'SHARED_EQUITIES_CACHE=""\nEQUITIES_CACHE_DIR="/tmp/run-w56/equities-cache"\n')
        self.assertEqual(ports["equities_cache_dir"], "/tmp/run-w56/equities-cache")
        self.assertIs(ports["equities_cache_shared"], False)

    def test_unset_globals_still_render_the_per_run_default(self) -> None:
        ports = self._render(self._base() + "unset SHARED_EQUITIES_CACHE EQUITIES_CACHE_DIR WANT_BRIDGE\n")
        self.assertEqual(ports["equities_cache_dir"], "/tmp/run-w56/equities-cache")
        self.assertIs(ports["equities_cache_shared"], False)

    def test_existing_keys_are_untouched_and_the_path_is_json_escaped(self) -> None:
        ports = self._render(self._base() + 'SHARED_EQUITIES_CACHE="/srv/with \\"quote\\""\nEQUITIES_CACHE_DIR="/srv/with \\"quote\\""\n')
        self.assertEqual(ports["equities_cache_dir"], '/srv/with "quote"')
        self.assertEqual(set(ports), {"run_id", "data", "cascor", "recurrence", "data_url", "experiment", "equities_cache_dir", "equities_cache_shared", "grafana_bridge"})
        self.assertEqual((ports["run_id"], ports["data"], ports["cascor"], ports["recurrence"], ports["experiment"], ports["grafana_bridge"]), ("20261019T000000Z-ab12", 8110, None, 8260, "cell-01", False))


def _write_argv_launcher(path: Path, marker_dir: Path) -> None:
    """A stub launcher that records every ``--up`` argv and prints the RUN_ID banner the suite parses."""
    path.write_text("#!/usr/bin/env bash\n" f"MARKERS={marker_dir}\n" 'if [[ "$1" == "--up" ]]; then\n' '  printf "%s\\n" "$@" >"$MARKERS/up-$$-$RANDOM.args"\n' '  echo "=== Experiment run stub-run-$$ is up ==="\n' "  exit 0\n" "fi\n" 'if [[ "$1" == "--down" ]]; then touch "$MARKERS/down-$2"; exit 0; fi\n' "exit 2\n")
    path.chmod(0o755)


class TestSuitePassthrough(unittest.TestCase):
    """``run_suite.py`` hands the flag to every ``--up`` and records it; a relative path is refused first."""

    def _setup(self) -> "tuple[Path, Path, Path]":
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "base.yaml").write_text(acceptance.BASE_CONFIG)
        suite_dir = root / "suite-out"
        (root / "suite.yaml").write_text(acceptance._suite_yaml(root / "base.yaml", suite_dir))
        markers = root / "markers"
        markers.mkdir()
        run_root = root / "runroot"
        run_root.mkdir()
        launcher = root / "stub_launcher.bash"
        _write_argv_launcher(launcher, markers)
        driver = root / "stub_driver.py"
        acceptance._write_stub_driver(driver, {acceptance.CONTROL_MARKER: SANE, acceptance.EQUITIES_MARKER: SANE})
        self._env = {"JUNIPER_SUITE_LAUNCHER": str(launcher), "JUNIPER_SUITE_DRIVER": str(driver), "JUNIPER_SUITE_PYTHON": sys.executable}
        old_root = run_suite.DEFAULT_RUN_ROOT
        run_suite.DEFAULT_RUN_ROOT = run_root  # type: ignore[attr-defined]
        self.addCleanup(lambda: setattr(run_suite, "DEFAULT_RUN_ROOT", old_root))
        return root, suite_dir, markers

    def _main(self, *argv: str, env_knob: "str | None" = None) -> "tuple[int, str]":
        buf = io.StringIO()
        keys = list(self._env) + [ENV_KNOB]
        old = {key: os.environ.get(key) for key in keys}
        os.environ.update(self._env)
        os.environ.pop(ENV_KNOB, None)
        if env_knob is not None:
            os.environ[ENV_KNOB] = env_knob
        try:
            with redirect_stdout(buf), redirect_stderr(buf):
                rc = run_suite.main(list(argv))
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        return rc, buf.getvalue()

    @staticmethod
    def _up_argvs(markers: Path) -> "list[list[str]]":
        return [path.read_text().splitlines() for path in sorted(markers.glob("up-*.args"))]

    @staticmethod
    def _cell_count(root: Path) -> int:
        # The fixture expands to the base cell plus its two include rows; derive it rather than assume it.
        return len(run_suite.expand_cells(run_suite.load_suite(root / "suite.yaml"), root / "suite.yaml"))

    def test_flag_reaches_every_up_and_the_records(self) -> None:
        root, suite_dir, markers = self._setup()
        shared = str(root / "shared-cache")
        rc, out = self._main("--suite", str(root / "suite.yaml"), "--shared-equities-cache", shared)
        self.assertEqual(rc, 0, out)
        argvs = self._up_argvs(markers)
        self.assertEqual(len(argvs), self._cell_count(root), "every cell launched")
        for argv in argvs:
            self.assertIn("--shared-equities-cache", argv)
            self.assertEqual(argv[argv.index("--shared-equities-cache") + 1], shared)
            self.assertEqual(argv[:2], ["--up", "--cascor"], "the flag is appended; the fixed prefix is unchanged")
        rows = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        self.assertEqual({row["shared_equities_cache"] for row in rows}, {shared})
        manifest = json.loads((suite_dir / "suite_manifest.json").read_text())
        self.assertEqual(manifest["shared_equities_cache"], shared)

    def test_env_knob_is_honoured_and_passed_explicitly(self) -> None:
        root, suite_dir, markers = self._setup()
        shared = str(root / "shared-cache")
        rc, out = self._main("--suite", str(root / "suite.yaml"), env_knob=shared)
        self.assertEqual(rc, 0, out)
        for argv in self._up_argvs(markers):
            self.assertEqual(argv[argv.index("--shared-equities-cache") + 1], shared, "passed as the flag, so the launcher's record and the suite's agree")
        rows = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        self.assertEqual({row["shared_equities_cache"] for row in rows}, {shared})

    def test_relative_path_is_refused_before_anything_exists(self) -> None:
        root, suite_dir, markers = self._setup()
        rc, out = self._main("--suite", str(root / "suite.yaml"), "--shared-equities-cache", "relative/cache")
        self.assertEqual(rc, 2, out)
        self.assertIn("--shared-equities-cache needs an absolute path (got 'relative/cache')", out)
        self.assertEqual(self._up_argvs(markers), [], "no cell launched")
        self.assertFalse(suite_dir.exists(), "refused before the suite dir is created")
        rc, out = self._main("--suite", str(root / "suite.yaml"), env_knob="relative-too")
        self.assertEqual(rc, 2, out)
        self.assertFalse(suite_dir.exists())

    def test_absent_means_absent(self) -> None:
        root, suite_dir, markers = self._setup()
        rc, out = self._main("--suite", str(root / "suite.yaml"))
        self.assertEqual(rc, 0, out)
        for argv in self._up_argvs(markers):
            self.assertNotIn("--shared-equities-cache", argv)
        rows = [json.loads(line) for line in (suite_dir / "registry.jsonl").read_text().splitlines()]
        self.assertEqual({row["shared_equities_cache"] for row in rows}, {None})
        self.assertIsNone(json.loads((suite_dir / "suite_manifest.json").read_text())["shared_equities_cache"])

    def test_dry_run_prints_it_and_writes_nothing(self) -> None:
        root, suite_dir, markers = self._setup()
        shared = str(root / "shared-cache")
        rc, out = self._main("--suite", str(root / "suite.yaml"), "--dry-run", "--shared-equities-cache", shared)
        self.assertEqual(rc, 0, out)
        self.assertEqual(out.count(f" --shared-equities-cache {shared}"), self._cell_count(root), "once per cell's --up line")
        self.assertFalse(suite_dir.exists())
        self.assertEqual(self._up_argvs(markers), [])

    def test_cell_ids_do_not_depend_on_the_cache(self) -> None:
        root, _suite_dir, _markers = self._setup()
        doc = run_suite.load_suite(root / "suite.yaml")
        ids = [cell["cell_id"] for cell in run_suite.expand_cells(doc, root / "suite.yaml")]
        rc, out = self._main("--suite", str(root / "suite.yaml"), "--dry-run", "--shared-equities-cache", str(root / "x"))
        self.assertEqual(rc, 0, out)
        for cell_id in ids:
            self.assertIn(cell_id, out, "the same ids with the cache as without: it is not a suite key")


if __name__ == "__main__":
    unittest.main()
