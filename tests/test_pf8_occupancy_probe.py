#!/usr/bin/env python3
"""
Project:     Juniper
Sub-Project: juniper-ml
Application: tests
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Gate for the PF-8 occupancy probe pair — ``util/ad-hoc/2026-09-10_pf8_occupancy_sampler.py``
and ``util/ad-hoc/2026-09-10_pf8_occupancy_analyse.py`` (perf lane P2 item 4.1 residue).

``util/ad-hoc`` sits outside every pre-commit Python hook, and the probe's output is the number
that decides whether a two-arm PF-8 pair is worth an Overtoad's host time, so the arithmetic that
turns ``/proc`` jiffies into cores (read as sweep workers only by a stated assumption) is pinned
here rather than trusted.

What it pins
------------
1. **``/proc/<pid>/stat`` is split around the LAST ``)``.** ``comm`` may itself contain spaces
   and parentheses (``python -m (x)``); splitting on the first would shift every field by the
   number of words in the name and read a wrong ppid, utime and starttime with no error.
2. **Roles follow the process tree, not names.** The forkserver's descendants are the candidate
   pool; any other child of the listener is ``cascor_other``; data and driver are their own
   trees; an unrelated process with the same parent as the listener is nobody's.
3. **Accounting counts a pid from birth only if it was born inside the interval.** A pid first
   seen with a ``starttime`` before the previous tick is a baseline (0), not a windfall of its
   whole history; a pid that exited is COUNTED as vanished, never invented.
4. **``/proc/stat`` busy excludes iowait**, and busy cores scale by nproc.
5. **The readout thresholds are the sweep's, with both edges pinned** — 3.99 and 8.01 (on the
   sweep's worker axis) both say "pair NOT worth running", 4.0 and 8.0 both say "worth running";
   the band names and the sweep percentages are the ones §8.4 published.
6. **The drive window keeps only rows whose interval midpoint is inside it**, and occupancy is
   Σcpu / Σwall — not a mean of per-second ratios, which would weight a short final tick like a
   full one.
7. **End to end on a synthetic suite**: registry + run dir + series + trace → the expected
   core-occupancy figure and readout.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLER = REPO_ROOT / "util" / "ad-hoc" / "2026-09-10_pf8_occupancy_sampler.py"
ANALYSE = REPO_ROOT / "util" / "ad-hoc" / "2026-09-10_pf8_occupancy_analyse.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # A dataclass resolves its Overtoad module through sys.modules at class-creation time, so a
    # path-loaded module MUST be registered first or `@dataclass` raises inside exec_module.
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


sampler = _load(SAMPLER, "pf8_occupancy_sampler")
analyse = _load(ANALYSE, "pf8_occupancy_analyse")


def _stat_line(pid: int, comm: str, ppid: int, utime: int, stime: int, starttime: int) -> str:
    # fields 3..22 of proc(5), then padding for the rest of the line
    fields = ["S", str(ppid), "1", "1", "0", "-1", "4194304", "470", "0", "0", "0", str(utime), str(stime), "0", "0", "20", "0", "3", "0", str(starttime)]
    return f"{pid} ({comm}) " + " ".join(fields) + " " + " ".join(["0"] * 30)


def _proc(pid: int, ppid: int, cpu: int = 0, start: int = 0):
    return sampler.ProcStat(pid, f"p{pid}", ppid, cpu, start)


class StatParsingTests(unittest.TestCase):
    def test_comm_with_spaces_and_parentheses_does_not_shift_fields(self):
        st = sampler.parse_stat(_stat_line(4242, "python -m (x)", 4200, 150, 50, 19149812))
        self.assertEqual(st.pid, 4242)
        self.assertEqual(st.comm, "python -m (x)")
        self.assertEqual(st.ppid, 4200)
        self.assertEqual(st.cpu_ticks, 200)
        self.assertEqual(st.start_ticks, 19149812)

    def test_plain_comm(self):
        st = sampler.parse_stat(_stat_line(7, "cat", 1, 3, 4, 99))
        self.assertEqual((st.pid, st.comm, st.ppid, st.cpu_ticks, st.start_ticks), (7, "cat", 1, 7, 99))

    def test_garbage_returns_none(self):
        self.assertIsNone(sampler.parse_stat("not a stat line"))
        self.assertIsNone(sampler.parse_stat("12 (x) S 1"))


class RoleClassificationTests(unittest.TestCase):
    def setUp(self):
        self.procs = {
            1: _proc(1, 0),
            10: _proc(10, 1),  # cascor uvicorn listener
            11: _proc(11, 10),  # forkserver
            12: _proc(12, 10),  # some other child (plotting)
            13: _proc(13, 11),  # candidate worker
            14: _proc(14, 11),  # candidate worker
            15: _proc(15, 13),  # grandchild of the forkserver
            20: _proc(20, 1),  # data listener
            21: _proc(21, 20),
            30: _proc(30, 2),  # driver
            31: _proc(31, 30),
            99: _proc(99, 1),  # unrelated sibling of the listener
        }
        self.cmdlines = {11: "python -c from multiprocessing.forkserver import main; main(...)", 12: "python plots"}

    def test_tree_roles(self):
        roles = sampler.classify_roles(10, 20, 30, self.procs, lambda pid: self.cmdlines.get(pid, ""))
        self.assertEqual(roles["cascor_uvicorn"], {10})
        self.assertEqual(roles["cascor_forkserver"], {11})
        self.assertEqual(roles["cascor_workers"], {13, 14, 15})
        self.assertEqual(roles["cascor_other"], {12})
        self.assertEqual(roles["data"], {20, 21})
        self.assertEqual(roles["driver"], {30, 31})
        self.assertNotIn(99, set().union(*roles.values()))

    def test_missing_pids_yield_empty_roles(self):
        roles = sampler.classify_roles(None, 20, 4444, self.procs, lambda pid: "")
        self.assertEqual(roles["cascor_uvicorn"], set())
        self.assertEqual(roles["cascor_workers"], set())
        self.assertEqual(roles["data"], {20, 21})
        self.assertEqual(roles["driver"], set())

    def test_find_driver_by_run_dir(self):
        cmd = {30: "python3 /x/util/experiments/run_experiment.py --config a.yaml --run-dir /root/20260910T000000Z-abcd", 31: "bash launcher --down 20260910T000000Z-abcd"}
        self.assertEqual(sampler.find_driver_pid(Path("/root/20260910T000000Z-abcd"), self.procs, lambda pid: cmd.get(pid, "")), 30)
        self.assertIsNone(sampler.find_driver_pid(Path("/root/20260910T000000Z-ffff"), self.procs, lambda pid: cmd.get(pid, "")))


class AccountingTests(unittest.TestCase):
    def test_deltas_births_baselines_and_vanished(self):
        clk = 100
        procs = {
            10: _proc(10, 1, cpu=180, start=500),  # tracked before: 100 -> 180
            13: _proc(13, 11, cpu=90, start=500),  # tracked before: 50 -> 90
            14: _proc(14, 11, cpu=30, start=1005),  # born after the previous tick (uptime 1000): counts all 30
            15: _proc(15, 11, cpu=70, start=900),  # existed before we attached: baseline, counts 0
        }
        roles = {"cascor_uvicorn": {10}, "cascor_forkserver": set(), "cascor_workers": {13, 14, 15}, "cascor_other": set(), "data": set(), "driver": set()}
        seconds, vanished = sampler.account({10: 100, 13: 50, 16: 40}, 1000.0, procs, roles, clk_tck=clk)
        self.assertAlmostEqual(seconds["cascor_uvicorn"], 0.80)
        self.assertAlmostEqual(seconds["cascor_workers"], (40 + 30 + 0) / clk)
        self.assertEqual(seconds["data"], 0.0)
        self.assertEqual(vanished, 1)  # pid 16 was tracked and is gone

    def test_first_tick_is_all_baseline(self):
        procs = {10: _proc(10, 1, cpu=180, start=5)}
        roles = {"cascor_uvicorn": {10}, "cascor_forkserver": set(), "cascor_workers": set(), "cascor_other": set(), "data": set(), "driver": set()}
        seconds, vanished = sampler.account({}, None, procs, roles, clk_tck=100)
        self.assertEqual(seconds["cascor_uvicorn"], 0.0)
        self.assertEqual(vanished, 0)

    def test_counter_going_backwards_is_clamped(self):
        procs = {10: _proc(10, 1, cpu=5, start=5)}
        roles = {"cascor_uvicorn": {10}, "cascor_forkserver": set(), "cascor_workers": set(), "cascor_other": set(), "data": set(), "driver": set()}
        seconds, _ = sampler.account({10: 50}, 1.0, procs, roles, clk_tck=100)
        self.assertEqual(seconds["cascor_uvicorn"], 0.0)


class HostTests(unittest.TestCase):
    def test_busy_excludes_idle_and_iowait(self):
        with tempfile.TemporaryDirectory() as tmp:
            stat = Path(tmp) / "stat"
            stat.write_text("cpu  100 0 50 800 20 0 5 0 0 0\ncpu0 1 2 3 4 5 6 7 8 9 10\n", encoding="utf-8")
            busy, total = sampler.read_cpu_jiffies(stat)
        self.assertEqual(total, 975)
        self.assertEqual(busy, 155)

    def test_busy_cores_scale_by_nproc(self):
        self.assertAlmostEqual(sampler.host_busy_cores((1000, 2000), (1100, 2400), 16), 4.0)
        self.assertEqual(sampler.host_busy_cores((1000, 2000), (1000, 2000), 16), 0.0)

    def test_run_discovery_filters_by_timestamp_and_shape(self):
        from datetime import datetime, timezone

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("20260910T050000Z-aaaa", "20260909T000000Z-bbbb", "suites", "not-a-run", "20260910T060000Z-cccc"):
                (root / name).mkdir()
            (root / "index.jsonl").write_text("", encoding="utf-8")
            known, done = {}, {"20260910T060000Z-cccc"}
            sampler.discover_runs(root, datetime(2026, 9, 10, 4, 59, tzinfo=timezone.utc), known, done)
        self.assertEqual(set(known), {"20260910T050000Z-aaaa"})


class ReadoutTests(unittest.TestCase):
    def test_band_edges(self):
        self.assertFalse(analyse.readout(3.99)["pair_worth_running"])
        self.assertTrue(analyse.readout(4.0)["pair_worth_running"])
        self.assertTrue(analyse.readout(8.0)["pair_worth_running"])
        self.assertFalse(analyse.readout(8.01)["pair_worth_running"])

    def test_window_overlap(self):
        ov = analyse.window_overlap((100.0, 160.0), (110.0, 170.0))
        self.assertEqual(ov["shared_s"], 50.0)
        self.assertAlmostEqual(ov["fraction_of_a"], 50.0 / 60.0, places=3)
        self.assertEqual(ov["start_offset_s"], 10.0)
        self.assertEqual(analyse.window_overlap((0.0, 10.0), (20.0, 30.0))["shared_s"], 0.0)
        self.assertEqual(analyse.window_overlap((0.0, 10.0), (2.0, 5.0))["fraction_of_b"], 1.0)

    def test_band_names_and_sweep_percentages(self):
        self.assertEqual(analyse.readout(2.0)["band"], "below-knee")
        self.assertEqual(analyse.readout(5.9)["band"], "below-knee")
        self.assertEqual(analyse.readout(6.0)["band"], "knee")
        self.assertEqual(analyse.readout(7.99)["band"], "knee")
        self.assertEqual(analyse.readout(8.0)["band"], "plateau")
        self.assertEqual(analyse.readout(12.0)["band"], "beyond-plateau")
        self.assertIn("+19.9%", analyse.readout(2.0)["second_run_cost"])
        self.assertIn("20.5%", analyse.readout(2.0)["second_run_cost"])
        self.assertIn("+86.1%", analyse.readout(9.0)["second_run_cost"])
        self.assertIn("+181.6%", analyse.readout(13.0)["second_run_cost"])


def _row(epoch_s: float, wall_dt: float, tree: float, total: float = None, busy: float = 8.0, load: float = 6.0, workers: int = 3, vanished: int = 0, run_id: str = "r1") -> dict:
    total = tree if total is None else total
    return {"run_id": run_id, "epoch_s": epoch_s, "wall_dt": wall_dt, "cascor_tree": tree, "total": total, "host_busy_cores": busy, "load_1m": load, "n_workers": workers, "vanished": vanished}


class ReductionTests(unittest.TestCase):
    def test_window_uses_interval_midpoint(self):
        rows = [_row(100.0, 1.0, 1.0), _row(101.0, 1.0, 2.0), _row(102.0, 1.0, 3.0), _row(103.0, 1.0, 4.0)]
        # window [100.4, 102.4]: midpoints 99.5, 100.5, 101.5, 102.5 -> rows 2 and 3 only
        kept = analyse.in_window(rows, (100.4, 102.4))
        self.assertEqual([r["cascor_tree"] for r in kept], [2.0, 3.0])

    def test_occupancy_is_sum_over_sum_not_mean_of_ratios(self):
        rows = [_row(1.0, 1.0, 4.0), _row(1.2, 0.2, 0.2)]  # a full tick at 4.0 and a 0.2 s tick at 1.0
        red = analyse.reduce_rows(rows)
        self.assertAlmostEqual(red["occupancy"], 4.2 / 1.2, places=3)
        self.assertEqual(red["samples"], 2)
        self.assertAlmostEqual(red["max"], 4.0)

    def test_ambient_is_host_minus_this_run(self):
        rows = [_row(1.0, 1.0, 3.0, total=3.5, busy=9.0), _row(2.0, 1.0, 3.0, total=3.5, busy=11.0)]
        red = analyse.reduce_rows(rows)
        self.assertAlmostEqual(red["host_busy_cores"], 10.0)
        self.assertAlmostEqual(red["ambient_cores"], 6.5)
        self.assertEqual(red["n_workers_mode"], 3)

    def test_empty_rows(self):
        self.assertEqual(analyse.reduce_rows([])["samples"], 0)

    def test_phase_split_shares_and_means(self):
        # three seconds at 12 (output phase, above the plateau), one at 2 (candidate phase)
        rows = [_row(1.0, 1.0, 12.0), _row(2.0, 1.0, 12.0), _row(3.0, 1.0, 12.0), _row(4.0, 1.0, 2.0)]
        red = analyse.reduce_rows(rows)
        self.assertAlmostEqual(red["occupancy"], 9.5)
        self.assertAlmostEqual(red["share_at_or_above_knee"], 0.75)
        self.assertAlmostEqual(red["share_at_or_above_plateau"], 0.75)
        self.assertAlmostEqual(red["occupancy_above_knee"], 12.0)
        self.assertAlmostEqual(red["occupancy_below_knee"], 2.0)
        # exactly-at-knee counts as above; just below does not
        edge = analyse.reduce_rows([_row(1.0, 1.0, 6.0), _row(2.0, 1.0, 5.99)])
        self.assertAlmostEqual(edge["share_at_or_above_knee"], 0.5)
        self.assertAlmostEqual(edge["share_at_or_above_plateau"], 0.0)


def _cell(step_ms: float, occ: float, steps: int = 1770, env: "dict | None" = None, outcome: str = "succeeded") -> dict:
    return {"cell_id": "c", "outcome": outcome, "mean_step_ms": step_ms, "step_count": steps, "thread_env": {"OMP_NUM_THREADS": "2"} if env is None else env, "drive": {"samples": 10, "occupancy": occ}}


class ArmComparisonTests(unittest.TestCase):
    def test_ratio_identity_and_both_readings(self):
        parallel = [{"cells": [_cell(21.6, 2.1), _cell(21.9, 1.9)], "pair_overlap": {"shared_s": 40.0, "fraction_of_a": 0.99, "fraction_of_b": 0.89, "start_offset_s": 0.07}}]
        control = [{"cells": [_cell(18.4, 2.15), _cell(18.5, 2.13), _cell(18.9, 2.17)], "pair_overlap": None}]
        result = analyse.compare_arms(parallel, control)
        self.assertTrue(result["same_budget"])
        self.assertTrue(result["same_work"])
        self.assertTrue(result["comparable"])
        self.assertAlmostEqual(result["ratio"], 21.75 / 18.6, places=3)
        self.assertAlmostEqual(result["cost_pct"], round((21.75 / 18.6 - 1) * 100, 1))
        self.assertFalse(result["located_vs_quiet_band"])  # +16.9% sits inside the 20.5% band
        self.assertTrue(result["resolved_vs_within_arm_spread"])  # but far outside the ~2.7% within-arm spread
        self.assertEqual(result["pair_occupancy_totals"], [4.0])
        self.assertIn("COMPARABLE", analyse.render_arms(result))
        self.assertIn("below what this host can measure", analyse.render_arms(result))

    def test_budget_mismatch_is_not_comparable(self):
        parallel = [{"cells": [_cell(21.6, 2.1, env={"OMP_NUM_THREADS": "2"})], "pair_overlap": None}]
        control = [{"cells": [_cell(28.4, 4.5, env={"OMP_NUM_THREADS": None})], "pair_overlap": None}]
        result = analyse.compare_arms(parallel, control)
        self.assertFalse(result["same_budget"])
        self.assertFalse(result["comparable"])
        self.assertIn("NOT COMPARABLE", analyse.render_arms(result))

    def test_work_mismatch_is_not_comparable(self):
        parallel = [{"cells": [_cell(21.6, 2.1, steps=1770)], "pair_overlap": None}]
        control = [{"cells": [_cell(18.4, 2.1, steps=1771)], "pair_overlap": None}]
        result = analyse.compare_arms(parallel, control)
        self.assertFalse(result["same_work"])
        self.assertFalse(result["comparable"])

    def test_failed_cells_do_not_enter_an_arm(self):
        parallel = [{"cells": [_cell(21.6, 2.1), _cell(99.0, 9.0, outcome="failed")], "pair_overlap": None}]
        control = [{"cells": [_cell(18.4, 2.1)], "pair_overlap": None}]
        result = analyse.compare_arms(parallel, control)
        self.assertEqual(result["parallel"]["cells"], 1)
        self.assertEqual(result["pair_occupancy_totals"], [2.1])


class EndToEndTests(unittest.TestCase):
    def test_synthetic_suite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_dir = root / "20260910T050000Z-abcd"
            (run_dir / "artifacts" / "results").mkdir(parents=True)
            (run_dir / "artifacts" / "results" / "metrics_series.csv").write_text("ts_unix,fsm_status\n1000.0,STARTED\n1005.0,TRAINING\n1010.0,COMPLETED\n", encoding="utf-8")
            (run_dir / "artifacts" / "results" / "stats.json").write_text(json.dumps({"cascor": {"training_step_duration": {"total_steps": 1770, "overall_mean_seconds": 0.025}}}), encoding="utf-8")
            (run_dir / "manifest.json").write_text(json.dumps({"timings": {"drive": 10.0}, "completion_reason": "early_stopped", "environment": {"thread_env": {"OMP_NUM_THREADS": "2", "CASCOR_NUM_PROCESSES": "4"}}}), encoding="utf-8")
            suite = root / "suite"
            suite.mkdir()
            (suite / "registry.jsonl").write_text(json.dumps({"cell_id": "c000-deadbeef", "run_id": run_dir.name, "run_dir": str(run_dir), "outcome": "succeeded", "thread_budget": None}) + "\n", encoding="utf-8")
            cols = analyse.NUMERIC
            trace = suite / "occupancy.tsv"
            lines = ["\t".join(("utc_iso", "run_id", *cols))]

            def line(epoch, run_id, tree, total, busy, load="6.0", workers="3", vanished="0"):
                vals = {"epoch_s": f"{epoch:.3f}", "wall_dt": "1.000", "cascor_uvicorn": "0", "cascor_forkserver": "0", "cascor_workers": "0", "cascor_other": "0", "data": "0", "driver": "0", "cascor_tree": f"{tree}", "total": f"{total}", "n_workers": workers, "n_pids": "5", "vanished": vanished, "host_busy_cores": f"{busy}", "load_1m": load}
                return "\t".join(("2026-09-10T05:00:00+00:00", run_id, *(vals[c] for c in cols)))

            # bring-up rows before the window, five rows inside it (4.5 each), one row after
            lines.append(line(998.0, run_dir.name, 0.5, 0.6, 7.0))
            for t in (1001.0, 1002.0, 1003.0, 1004.0, 1005.0):
                lines.append(line(t, run_dir.name, 4.5, 4.7, 9.0))
            lines.append(line(1012.0, run_dir.name, 0.1, 0.1, 5.0))
            lines.append(line(1020.0, "-", 0, 0, 4.0))
            trace.write_text("\n".join(lines) + "\n", encoding="utf-8")

            summary = analyse.summarise(suite, analyse.load_trace(trace))
            buf = io.StringIO()
            with redirect_stdout(buf):
                rc = analyse.main(["--suite", str(suite), "--trace", str(trace), "--json", str(root / "out.json")])
            self.assertEqual(rc, 0)
            self.assertTrue((root / "out.json").is_file())

        cell = summary["cells"][0]
        self.assertEqual(cell["window"], (1000.0, 1010.0))
        self.assertEqual(cell["drive"]["samples"], 5)
        self.assertAlmostEqual(cell["drive"]["occupancy"], 4.5)
        self.assertAlmostEqual(cell["drive"]["ambient_cores"], 9.0 - 4.7)
        self.assertEqual(cell["step_count"], 1770)
        self.assertEqual(cell["mean_step_ms"], 25.0)
        self.assertEqual(cell["thread_env"], {"OMP_NUM_THREADS": "2", "CASCOR_NUM_PROCESSES": "4"})
        self.assertAlmostEqual(cell["drive"]["share_at_or_above_knee"], 0.0)
        self.assertIn("CASCOR_NUM_PROCESSES", buf.getvalue())
        self.assertEqual(summary["aggregate"]["cells"], 1)
        self.assertAlmostEqual(summary["aggregate"]["mean"], 4.5)
        self.assertTrue(summary["aggregate"]["readout_mean"]["pair_worth_running"])
        self.assertEqual(summary["aggregate"]["readout_mean"]["band"], "below-knee")
        self.assertEqual(summary["between_cells"]["samples"], 1)
        self.assertIn("two-arm pair worth running: YES", buf.getvalue())

    def test_failed_cells_are_excluded_from_the_aggregate(self):
        with tempfile.TemporaryDirectory() as tmp:
            suite = Path(tmp)
            (suite / "registry.jsonl").write_text(json.dumps({"cell_id": "c000-deadbeef", "run_id": "20260910T050000Z-abcd", "run_dir": str(suite / "nope"), "outcome": "failed"}) + "\n", encoding="utf-8")
            summary = analyse.summarise(suite, [])
        self.assertIsNone(summary["aggregate"])
        self.assertIsNone(summary["cells"][0]["drive"])
        self.assertIn("nothing to read off the curve", analyse.render(summary))


if __name__ == "__main__":
    unittest.main()
