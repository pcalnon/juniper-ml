#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Gate for the PF-8 ICV pair — ``util/ad-hoc/2026-09-11_omp_icv_checkpoint_probe.py`` and
``util/ad-hoc/2026-09-11_icv_trace_align.py`` — the instruments behind
``notes/JUNIPER_2026-09-11_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-BURST-TERMINATOR-AND-ICV-INSTRUMENT.md``.

``util/ad-hoc`` sits outside every pre-commit Python hook, and this pair carries conclusions that
OVERTURN two published ones — the attribution note's named suspect (candidate-pool creation) and
its §5.1 reading of the matmul — so the properties those conclusions rest on are pinned here.

What it pins
------------
1. **The checkpoint does not call ``torch.get_num_threads()`` by default.** That getter re-pins
   the calling thread's OpenMP ICV, so a checkpoint that read it would end the burst it exists to
   observe. The first draft did exactly that and every arm, control included, reported an
   identical instrument-caused re-pin. ``touch_torch`` must stay opt-in and default False.
2. **The icv-map keeps a do-nothing control arm.** Without it, an instrument footprint is
   indistinguishable from a result. The summary must shout when the control re-pins.
3. **Every icv-map arm runs on its OWN thread.** A re-pinned thread stays re-pinned, so a shared
   thread would let the first arm mask every later one.
4. **The output_pass arm does NOT construct its network on the arm thread.** Constructing there
   puts the constructor's ``torch.set_num_threads(2)`` on the measured thread, and the arm then
   measures the constructor pin instead of the pass — which is what the first draft did.
5. **The reducer scores claims (a) and (b) SEPARATELY.** "The drop ends the burst" (refuted) and
   "the drop is why later passes do not burst" (supported) are different claims about the same
   two series; a reducer that reported one verdict would license the wrong one.
6. **The growth mode reports which stages it did NOT wrap.** An absent checkpoint must never be
   readable as "this stage did not re-pin".
7. **The spiral stays at radius 10.0**, because a unit-radius spiral grows zero hidden units and
   the growth loop under test would never run.
8. **The hidden-unit readout reports None when absent**, not a ``-1`` sentinel that reads like a
   count. The first draft read a ``current_hidden_units`` attribute that does not exist on this
   build and printed its default as though it were a measurement.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROBE = REPO_ROOT / "util" / "ad-hoc" / "2026-09-11_omp_icv_checkpoint_probe.py"
ALIGN = REPO_ROOT / "util" / "ad-hoc" / "2026-09-11_icv_trace_align.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # Register BEFORE exec_module: a dataclass resolves its owner module through sys.modules at
    # class-creation time and gets None otherwise.
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _tree(path: Path) -> ast.Module:
    return ast.parse(_source(path))


def _func(tree: ast.Module, name: str) -> ast.FunctionDef:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"function {name!r} not found")


class TestFilesExist(unittest.TestCase):
    def test_both_instruments_are_present(self) -> None:
        self.assertTrue(PROBE.is_file(), f"missing {PROBE}")
        self.assertTrue(ALIGN.is_file(), f"missing {ALIGN}")


class TestCheckpointDoesNotPerturb(unittest.TestCase):
    """Item 1: the getter re-pins, so the checkpoint must not call it by default."""

    def test_touch_torch_defaults_to_false(self) -> None:
        fn = _func(_tree(PROBE), "checkpoint")
        names = [a.arg for a in fn.args.args]
        self.assertIn("touch_torch", names, "checkpoint lost its touch_torch guard")
        # Defaults align to the TAIL of the positional args.
        offset = len(names) - len(fn.args.defaults)
        default = fn.args.defaults[names.index("touch_torch") - offset]
        # `assert isinstance` rather than `assertIsInstance`: the latter does not narrow the type
        # for mypy, and `default.value` on a bare `ast.expr` is an attr-defined error.
        assert isinstance(default, ast.Constant), f"touch_torch default is {type(default).__name__}, not a literal"
        self.assertIs(default.value, False, "touch_torch must default to False")

    def test_torch_is_imported_only_under_the_guard(self) -> None:
        """The torch import sits inside `if touch_torch:`, so the default path cannot re-pin."""
        fn = _func(_tree(PROBE), "checkpoint")
        guarded = [node for node in ast.walk(fn) if isinstance(node, ast.If) for sub in ast.walk(node) if isinstance(sub, ast.Import) and any(a.name == "torch" for a in sub.names)]
        self.assertTrue(guarded, "torch import in checkpoint() is not inside the touch_torch guard")

    def test_docstring_records_why(self) -> None:
        doc = ast.get_docstring(_func(_tree(PROBE), "checkpoint")) or ""
        self.assertIn("RE-PINS", doc.upper())


class TestControlArm(unittest.TestCase):
    """Items 2 and 3: a control arm exists, and every arm gets a fresh thread."""

    def test_icv_map_declares_a_none_control(self) -> None:
        src = _source(PROBE)
        self.assertIn('"none": _op_none', src)
        self.assertIn('"control_arm_must_not_repin": "none"', src)

    def test_summary_shouts_when_the_control_repins(self) -> None:
        src = _source(PROBE)
        self.assertIn("CONTROL ARM RE-PINNED", src)

    def test_each_arm_creates_its_own_thread(self) -> None:
        fn = _func(_tree(PROBE), "run_icv_map")
        creations = [node for node in ast.walk(fn) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "Thread"]
        self.assertTrue(creations, "run_icv_map no longer creates a thread per arm")
        # The creation must sit inside the per-arm loop, not before it.
        loops = [node for node in fn.body if isinstance(node, ast.For)]
        self.assertTrue(
            any(isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) and sub.func.attr == "Thread" for loop in loops for sub in ast.walk(loop)),
            "the Thread() call must be inside the per-arm loop",
        )


class TestOutputPassArmIsNotConfounded(unittest.TestCase):
    """Item 4: the measured pass must not construct on the thread being measured."""

    def test_network_is_prebuilt_outside_the_arm(self) -> None:
        src = _source(PROBE)
        self.assertIn("prebuilt = _build_network(", src)
        fn = _func(_tree(PROBE), "run_icv_map")
        arm = next(node for node in ast.walk(fn) if isinstance(node, ast.FunctionDef) and node.name == "_op_output_pass_prebuilt")
        builds = [node for node in ast.walk(arm) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "_build_network"]
        self.assertEqual(builds, [], "the output_pass arm must not construct the network on its own thread")

    def test_a_separate_arm_covers_constructing_on_the_thread(self) -> None:
        self.assertIn('"construct_here"', _source(PROBE))


class TestGrowthModeHonesty(unittest.TestCase):
    """Item 6: an unwrapped stage must be visible as unwrapped."""

    def test_result_reports_stages_absent_on_this_build(self) -> None:
        src = _source(PROBE)
        self.assertIn('"wrapped_methods"', src)
        self.assertIn('"not_wrapped_absent_on_this_build"', src)

    def test_the_localising_stages_are_wrapped(self) -> None:
        src = _source(PROBE)
        for stage in (
            "train_output_layer",
            "train_candidates",
            "_ensure_worker_pool",
            "_collect_training_results",
            "_validate_training_result",
            "_retrain_output_layer",
        ):
            self.assertIn(f'"{stage}"', src, f"stage {stage} dropped from the wrap list")

    def test_hidden_units_reports_none_not_a_sentinel(self) -> None:
        src = _source(PROBE)
        self.assertIn("hidden = len(units) if isinstance(units, list) else None", src)
        self.assertNotIn('getattr(network, "current_hidden_units", -1)', src)


class TestSpiralStaysAtRadiusTen(unittest.TestCase):
    """Item 7: a unit-radius spiral grows zero hidden units."""

    def test_radius_scale_default_is_ten(self) -> None:
        mod = _load(PROBE, "_pf8_icv_probe_under_test")
        fn = _func(_tree(PROBE), "make_spiral")
        default = fn.args.defaults[-1]
        assert isinstance(default, ast.Constant), f"radius_scale default is {type(default).__name__}, not a literal"
        self.assertEqual(default.value, 10.0)
        self.assertTrue(callable(mod.make_spiral))


class TestReducerSeparatesTheTwoClaims(unittest.TestCase):
    """Item 5: (a) and (b) are different claims and are scored separately."""

    def test_source_names_both_claims(self) -> None:
        src = _source(ALIGN)
        self.assertIn("claim (a)", src)
        self.assertIn("claim (b)", src)

    def _run(self, payload: dict) -> str:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump(payload, handle)
            path = handle.name
        proc = subprocess.run(  # noqa: S603 -- our own interpreter, our own script
            [sys.executable, str(ALIGN), "--json", path],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return proc.stdout

    @staticmethod
    def _payload(drop_t: float, last_burst_t: float) -> dict:
        """A minimal growth-mode result: burst early, ICV drop at `drop_t`."""
        checkpoints = [
            {"label": "main:after_construction", "t": 0.0, "thread_name": "MainThread", "tid": 1, "omp_icv_max_threads": 2},
            {"label": "train_thread:entry", "t": 0.1, "thread_name": "cascor-train-probe", "tid": 2, "omp_icv_max_threads": 16},
            {"label": "train_output_layer:before", "t": 0.2, "thread_name": "cascor-train-probe", "tid": 2, "omp_icv_max_threads": 16},
            {"label": "train_output_layer:after", "t": last_burst_t + 0.1, "thread_name": "cascor-train-probe", "tid": 2, "omp_icv_max_threads": 16},
            {"label": "_collect_training_results:before", "t": drop_t - 0.1, "thread_name": "cascor-train-probe", "tid": 2, "omp_icv_max_threads": 16},
            {"label": "_validate_training_result:before", "t": drop_t, "thread_name": "cascor-train-probe", "tid": 2, "omp_icv_max_threads": 2},
        ]
        samples = [{"t": 0.5, "busy_threads": 14, "cores": 10.0, "alive_threads": 20}]
        samples.append({"t": last_burst_t, "busy_threads": 14, "cores": 10.0, "alive_threads": 20})
        samples.append({"t": drop_t + 1.0, "busy_threads": 2, "cores": 1.9, "alive_threads": 20})
        return {"mode": "growth", "checkpoints": checkpoints, "samples": samples}

    def test_a_late_drop_refutes_claim_a_and_supports_claim_b(self) -> None:
        out = self._run(self._payload(drop_t=10.0, last_burst_t=7.0))
        self.assertIn("REFUTED", out)
        self.assertIn("SUPPORTED", out)
        self.assertIn("_collect_training_results", out)

    def test_a_coincident_drop_supports_claim_a(self) -> None:
        """The verdicts are computed, not hard-coded: a drop at the burst end must flip (a)."""
        out = self._run(self._payload(drop_t=7.2, last_burst_t=7.0))
        claim_a = out.split("claim (a)")[1].split("claim (b)")[0]
        self.assertIn("SUPPORTED", claim_a)

    def test_non_growth_file_is_refused(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            json.dump({"mode": "icv-map", "arms": []}, handle)
            path = handle.name
        proc = subprocess.run(  # noqa: S603 -- our own interpreter, our own script
            [sys.executable, str(ALIGN), "--json", path],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(proc.returncode, 2)


class TestProbeRunsEndToEnd(unittest.TestCase):
    """The getter side-effect mode needs no cascor and no network: run it for real."""

    def test_getter_side_effect_mode_executes(self) -> None:
        try:
            import torch  # noqa: F401, PLC0415
        except ImportError:
            self.skipTest("torch is not importable in this environment")
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "getter.json"
            proc = subprocess.run(  # noqa: S603 -- our own interpreter, our own script
                [sys.executable, str(PROBE), "--mode", "torch-getter-side-effect", "--json", str(out)],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
            data = json.loads(out.read_text(encoding="utf-8"))
            arms = {a["arm"]: a for a in data["arms"]}
            self.assertFalse(
                arms["read_icv_twice"]["repinned"],
                "reading the ICV twice must not change it -- the instrument is perturbing",
            )
            # The getter arm is expected to re-pin on a libgomp build. It is NOT asserted, because
            # a non-OpenMP or MKL-threaded torch would legitimately differ; what must hold is the
            # control above.
            self.assertIn("repinned", arms["read_getter_between"])


if __name__ == "__main__":
    unittest.main()
