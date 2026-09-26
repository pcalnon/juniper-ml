"""cascor#686 ruling matrix: every entry path, through the REAL _reload_dataset / auto-start over HTTP (scratch).

After every step, each loaded partition's PROVENANCE (which fetch or inline call bound that exact tensor
object) is compared with what get_status() reports:
  OVERCLAIM  -- dataset_shortfall / current_dataset names a fetch none of whose partitions is loaded;
  UNDERCLAIM -- a partition from a PARTIAL fetch is loaded, yet dataset_shortfall is null or names another;
  NAMELOSS   -- a partition from a fetch is loaded, yet current_dataset names no fetch that is loaded.
usage: probe_ruling_matrix.py <cascor-tree>
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import torch

ROOT = sys.argv[1]
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(__file__))
logging.basicConfig(level=logging.CRITICAL)
for _n in ("", "api", "cascor", "juniper_cascor"):
    logging.getLogger(_n).setLevel(logging.CRITICAL)

from fakejd2 import PARTIAL_META, FakeJD  # noqa: E402

import api.lifecycle.manager as M  # noqa: E402
from api.app import _auto_start_training  # noqa: E402
from api.routes.training import _generate_spiral_data  # noqa: E402

SLOTS = (("train", "_train_x"), ("val", "_val_x"), ("test", "_test_x"))
fake = FakeJD()
os.environ["JUNIPER_DATA_URL"] = fake.url
os.environ.pop("JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS", None)
problems: List[str] = []


class Run:
    def __init__(self, name: str) -> None:
        self.name = name
        self.m = M.TrainingLifecycleManager()
        self.prov: Dict[int, Dict[str, Any]] = {}
        self.keep: List[Any] = []  # keep every tensor alive so ids are never reused
        self.n_inline = 0
        print(f"\n=== {name}")

    # -- labelling -----------------------------------------------------------------------
    def _label_new(self, info: Dict[str, Any]) -> None:
        for _p, slot in SLOTS:
            t = getattr(self.m, slot)
            if t is not None and id(t) not in self.prov:
                self.prov[id(t)] = info
                self.keep.append(t)

    def _fetch_info(self, *, config_hint: str) -> Dict[str, Any]:
        sf = self.m.get_status()["dataset_shortfall"]
        return {"label": f"fetch:ds-{len(fake.posts)}", "kind": "fetch", "dataset_id": f"ds-{len(fake.posts)}", "partial": bool(fake.meta), "config": dict(self.m._current_dataset_config or {}), "hint": config_hint, "sf_at_bind": (sf or {}).get("dataset_id")}

    # -- actions -------------------------------------------------------------------------
    def start(self, **kw: Any) -> str:
        with patch.object(self.m, "_run_training"):
            try:
                self.m.start_training(**kw)
                if self.m._training_future is not None:
                    self.m._training_future.result(timeout=10)
                return "ok"
            except Exception as exc:  # noqa: BLE001
                return f"{type(exc).__name__}: {str(exc)[:60]}"

    def staged(self, tickers: str, **kw: Any) -> str:
        posts_before = len(fake.posts)
        self.m.stage_dataset_config(dataset_type="equities", params={"tickers": [tickers]})
        out = self.start(**kw)
        if out == "ok" and len(fake.posts) > posts_before:
            self._label_new(self._fetch_info(config_hint=tickers))
        return out

    def inline(self, *parts: str, **extra: Any) -> str:
        kw: Dict[str, Any] = dict(extra)
        self.n_inline += 1
        tensors = {}
        for p in parts:
            x, y = torch.randn(8, 2), torch.randn(8, 2)
            tensors[p] = x
            key = {"train": ("X", "y"), "val": ("X_val", "y_val"), "test": ("X_test", "y_test")}[p]
            kw[key[0]], kw[key[1]] = x, y
        out = self.start(**kw)
        for p, x in tensors.items():
            if id(x) not in self.prov:
                self.prov[id(x)] = {"label": f"inline-{self.n_inline}", "kind": "inline"}
                self.keep.append(x)
        return out

    def spiral(self) -> str:
        x, y = _generate_spiral_data({"n_points_per_spiral": 10})
        self.n_inline += 1
        out = self.start(X=x, y=y, dataset_config={"dataset_type": "spiral", "n_points_per_spiral": 10})
        self.prov[id(x)] = {"label": f"spiral-{self.n_inline}", "kind": "spiral"}
        self.keep.append(x)
        return out

    def swap(self, tickers: str) -> str:
        m = self.m
        m._experimental_functions_enabled = True
        if m.model is None or not hasattr(m.network, "_resize_network_for_dataset"):
            net = SimpleNamespace(input_size=2, output_size=2, active_output_dim=2, output_weights=torch.zeros(2, 2), output_bias=torch.zeros(2), hidden_units=[], candidate_pool_size=8)
            net._resize_network_for_dataset = MagicMock(return_value={"hidden_preserved": 0, "input_delta": 0, "output_delta": 0})
            net.record_dataset_swap_event = MagicMock(return_value=None)
            m.model = SimpleNamespace(network=net)
        posts_before = len(fake.posts)
        with patch.object(m.state_machine, "is_started", return_value=True), patch.object(m, "save_snapshot", return_value=None), patch.object(m, "_run_training"):
            try:
                r = m.swap_dataset_live(dataset_type="equities", params={"tickers": [tickers]})
                out = r["status"]
            except Exception as exc:  # noqa: BLE001
                out = f"{type(exc).__name__}: {str(exc)[:60]}"
        if out == "swapped" and len(fake.posts) > posts_before:
            self._label_new(self._fetch_info(config_hint=tickers))
        m.model = None
        return out

    def autostart(self, *, artifact: str = "three") -> str:
        fake.artifact_mode = artifact
        posts_before = len(fake.posts)
        settings = SimpleNamespace(juniper_data_url=fake.url, auto_dataset="equities", auto_dataset_params='{"tickers": ["AUTO"]}', allow_truncated_datasets=False, auto_network="{}")
        app = SimpleNamespace(state=SimpleNamespace(lifecycle=self.m))
        with patch.object(self.m, "_run_training"):
            asyncio.run(_auto_start_training(app, settings))
            if self.m._training_future is not None:
                self.m._training_future.result(timeout=10)
        fake.artifact_mode = "three"
        if self.m._auto_start_failure:
            return "FAILED: " + self.m._auto_start_failure[:60]
        if len(fake.posts) > posts_before:
            info = {"label": f"auto:ds-{len(fake.posts)}", "kind": "fetch", "dataset_id": f"ds-{len(fake.posts)}", "partial": bool(fake.meta), "config": {"dataset_type": "equities", "tickers": ["AUTO"]}}
            self._label_new(info)
        return "ok"

    # -- the check -----------------------------------------------------------------------
    def check(self, step: str, out: str) -> None:
        st = self.m.get_status()
        sf, cd = st["dataset_shortfall"], st["current_dataset"]
        loaded = {p: self.prov.get(id(getattr(self.m, slot)), {"label": "?UNTRACKED", "kind": "?"}) for p, slot in SLOTS if getattr(self.m, slot) is not None}
        fetches = [i for i in loaded.values() if i.get("kind") == "fetch"]
        fetch_ids = {i["dataset_id"] for i in fetches}
        flags = []
        if sf is not None and sf.get("dataset_id") not in fetch_ids:
            flags.append("OVERCLAIM(shortfall)")
        if cd and cd.get("dataset_type") not in (None, "spiral") and not any(i["config"] == cd for i in fetches):
            flags.append("OVERCLAIM(current_dataset)")
        partial_ids = {i["dataset_id"] for i in fetches if i["partial"]}
        if partial_ids and (sf is None or sf.get("dataset_id") not in partial_ids):
            flags.append(f"UNDERCLAIM(partial {sorted(partial_ids)} loaded, shortfall={None if sf is None else sf.get('dataset_id')})")
        if fetches and not (cd and any(i["config"] == cd for i in fetches)):
            flags.append(f"NAMELOSS(current_dataset={cd})")
        if len(fetch_ids) > 1:
            flags.append(f"TWO-FETCHES-LOADED{sorted(fetch_ids)}")
        prov = " ".join(f"{p}={i['label']}" for p, i in loaded.items())
        print(f"  {step:44s} -> {out[:44]:44s} | {prov:52s} | sf={None if sf is None else sf.get('dataset_id')} cd={cd} parts={sorted(self.m._described_partitions)} {' '.join(flags)}")
        for f in flags:
            problems.append(f"{self.name} / {step}: {f}")

    def done(self) -> None:
        self.m.shutdown()


def scenario_inline_only() -> None:
    r = Run("S1 inline starts on a fresh service")
    for parts in (("train",), ("train", "val"), ("train", "test"), ("train", "val", "test")):
        r.check(f"inline {'+'.join(parts)}", r.inline(*parts))
    r.done()


def scenario_partial_replacements() -> None:
    for parts in (("train",), ("train", "val"), ("train", "test"), ("train", "val", "test")):
        r = Run(f"S2 staged partial fetch, then inline {'+'.join(parts)}")
        r.check("staged fetch (three)", r.staged("AAPL"))
        r.check(f"inline {'+'.join(parts)}", r.inline(*parts))
        r.check("Stop->Start retained", r.start())
        r.m.reset()
        r.check("reset()", "ok")
        r.check("start_fresh retained", r.start(start_fresh=True))
        r.check("start_fresh + inline train", r.inline("train", start_fresh=True))
        r.check("new staged fetch", r.staged("MSFT"))
        r.done()


def scenario_across_starts() -> None:
    r = Run("S3 replaced across several starts")
    r.check("staged fetch (three)", r.staged("AAPL"))
    r.check("inline train", r.inline("train"))
    r.check("inline train+val", r.inline("train", "val"))
    r.check("inline train+test", r.inline("train", "test"))
    r.check("staged fetch #2", r.staged("MSFT"))
    r.check("inline val+test (direct call)", r.inline("val", "test"))
    r.check("inline train (direct call)", r.inline("train"))
    r.done()


def scenario_shapes() -> None:
    r = Run("S4 artifact shapes: train+val, and train+test (legacy, override on)")
    fake.artifact_mode = "train_val"
    r.check("staged fetch (train+val)", r.staged("AAPL"))
    fake.artifact_mode = "three"
    r.check("inline train+test", r.inline("train", "test"))
    r.check("inline train+val", r.inline("train", "val"))
    os.environ["JUNIPER_CASCOR_ALLOW_MISSING_VALIDATION_SPLIT"] = "true"
    fake.artifact_mode = "train_test"
    r.check("staged fetch (train+test, val promoted)", r.staged("MSFT"))
    fake.artifact_mode = "three"
    r.check("inline train+test", r.inline("train", "test"))
    r.check("inline train+val", r.inline("train", "val"))
    os.environ.pop("JUNIPER_CASCOR_ALLOW_MISSING_VALIDATION_SPLIT", None)
    r.done()


def scenario_refusals_and_swaps() -> None:
    r = Run("S5 refused fetches and live swaps after a partial replacement")
    r.check("staged fetch (three)", r.staged("AAPL"))
    r.check("inline train", r.inline("train"))
    fake.create_mode = "422"
    r.check("refused staged fetch (422)", r.staged("IBM"))
    r.m.clear_pending_dataset_config()
    fake.create_mode, fake.artifact_mode = "ok", "train_only"
    r.check("refused artifact (6.1)", r.staged("IBM"))
    r.m.clear_pending_dataset_config()
    fake.artifact_mode = "three"
    fake.create_mode = "422"
    r.check("live swap refused (422)", r.swap("ORCL"))
    fake.create_mode, fake.artifact_mode = "ok", "train_only"
    r.check("live swap refused artifact", r.swap("AMD"))
    fake.artifact_mode = "three"
    r.check("inline train+val after rollbacks", r.inline("train", "val"))
    r.check("inline train+test after rollbacks", r.inline("train", "test"))
    r.check("staged fetch #2", r.staged("MSFT"))
    r.check("inline train", r.inline("train"))
    r.check("live swap OK", r.swap("NVDA"))
    r.check("inline train+val", r.inline("train", "val"))
    r.done()


def scenario_inline_plus_pending() -> None:
    r = Run("S6 inline tensors in the same start as a pending staged config")
    r.check("staged fetch (three)", r.staged("AAPL"))
    r.m.stage_dataset_config(dataset_type="equities", params={"tickers": ["TSLA"]})
    fake.create_mode = "422"
    r.check("inline train + pending(422)", r.inline("train"))
    fake.create_mode = "ok"
    posts_before = len(fake.posts)
    out = r.inline("train")
    if len(fake.posts) > posts_before:
        r._label_new(r._fetch_info(config_hint="TSLA"))
    r.check("inline train + pending(ok)", out)
    r.check("inline val+test (direct call)", r.inline("val", "test"))
    r.done()


def scenario_spiral_route() -> None:
    r = Run("S7 POST /start dataset.generator=spiral (X only + dataset_config) after a partial fetch")
    r.check("staged fetch (three)", r.staged("AAPL"))
    r.check("spiral start", r.spiral())
    r.check("inline train+val+test", r.inline("train", "val", "test"))
    r.check("spiral start on inline val/test", r.spiral())
    r.done()


def scenario_autostart() -> None:
    r = Run("S8 auto-start (all three), then a train-only inline start")
    r.check("auto-start", r.autostart())
    r.check("inline train", r.inline("train"))
    r.done()
    r = Run("S9 a clean staged fetch, then auto-start delivers a PARTIAL train+val artifact (no test)")
    fake.meta = {}
    r.check("clean staged fetch (three)", r.staged("AAPL"))
    fake.meta = dict(PARTIAL_META)
    r.m.model = None  # auto-start creates its own network
    r.check("auto-start (train+val, partial)", r.autostart(artifact="train_val"))
    r.done()


for fn in (scenario_inline_only, scenario_partial_replacements, scenario_across_starts, scenario_shapes, scenario_refusals_and_swaps, scenario_inline_plus_pending, scenario_spiral_route, scenario_autostart):
    fake.create_mode, fake.artifact_mode, fake.meta = "ok", "three", dict(PARTIAL_META)
    fn()
fake.close()
print("\nPROBLEMS:" if problems else "\nPROBLEMS: none")
for p in problems:
    print("  " + p)
