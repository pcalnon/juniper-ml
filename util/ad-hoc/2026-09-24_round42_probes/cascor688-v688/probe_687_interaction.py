"""cascor#688 x #687: a Start that continues the network refuses a wider staged dataset BEFORE loading (scratch).

Drives the REAL start path over real HTTP (fakejd3 + the real JuniperDataClient): a real network built by
create-on-start, then a wider staged dataset. After each step prints the record (current_dataset,
dataset_shortfall's dataset_id, _described_partitions), each partition's provenance, and whether the
training log said DATASET SHORTFALL during that step.
usage: probe_687_interaction.py <cascor-tree>
"""

from __future__ import annotations

import asyncio
import copy
import logging
import os
import sys
from types import SimpleNamespace
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import torch

ROOT = sys.argv[1]
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(__file__))
logging.basicConfig(level=logging.CRITICAL)
for _n in ("", "api", "cascor", "juniper_cascor"):
    logging.getLogger(_n).setLevel(logging.CRITICAL)

from fakejd3 import PARTIAL_META, FakeJD  # noqa: E402

import api.lifecycle.manager as M  # noqa: E402
from api.app import _auto_start_training  # noqa: E402

fake = FakeJD()
os.environ["JUNIPER_DATA_URL"] = fake.url
os.environ.pop("JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS", None)
SLOTS = (("train", "_train_x"), ("val", "_val_x"), ("test", "_test_x"))
problems: List[str] = []


class Run:
    def __init__(self, name: str) -> None:
        self.m = M.TrainingLifecycleManager()
        self.name = name
        self.prov: Dict[int, str] = {}
        self.keep: List[Any] = []
        self.n = 0
        print(f"\n=== {name}")

    def _label(self, label: str) -> None:
        for _p, slot in SLOTS:
            t = getattr(self.m, slot)
            if t is not None and id(t) not in self.prov:
                self.prov[id(t)] = label
                self.keep.append(t)

    def snap(self) -> Dict[str, Any]:
        st = self.m.get_status()
        return {"cd": copy.deepcopy(st["current_dataset"]), "sf": copy.deepcopy(self.m._dataset_shortfall), "sf_obj": self.m._dataset_shortfall, "parts": getattr(self.m, "_described_partitions", frozenset({"n/a"})), "tensors": tuple(getattr(self.m, s) for _p, s in SLOTS) + (self.m._train_y, self.m._val_y, self.m._test_y), "pending": copy.deepcopy(st["pending_dataset"]), "warning": self.m._validation_warning, "net": self.m.network}

    def start(self, *, inline: tuple = (), width: int = 2, **kw: Any) -> str:
        spy = MagicMock(wraps=self.m.logger)
        self.n += 1
        tensors = {}
        for p in inline:
            x, y = torch.randn(8, width), torch.randn(8, 2)
            tensors[p] = x
            key = {"train": ("X", "y"), "val": ("X_val", "y_val"), "test": ("X_test", "y_test")}[p]
            kw[key[0]], kw[key[1]] = x, y
        posts = len(fake.posts)
        with patch.object(self.m, "_run_training"), patch.object(self.m, "logger", spy):
            try:
                self.m.start_training(**kw)
                out = "ok"
            except Exception as exc:  # noqa: BLE001
                out = f"{type(exc).__name__}: {str(exc)[:70]}"
                self.last_full = str(exc)
        for x in tensors.values():
            self.prov.setdefault(id(x), f"inline-{self.n}")
            self.keep.append(x)
        if out == "ok" and len(fake.posts) > posts:
            self._label(f"fetch:ds-{len(fake.posts)}")
        self.logged = [c.args[0] for c in spy.warning.call_args_list if "DATASET" in str(c.args[0])]
        return out

    def show(self, step: str, out: str) -> None:
        st = self.m.get_status()
        sf = st["dataset_shortfall"]
        prov = " ".join(f"{p}={self.prov.get(id(getattr(self.m, s)), '?')}" for p, s in SLOTS if getattr(self.m, s) is not None)
        net = self.m.network
        dims = f"{getattr(net, 'input_size', None)}x{getattr(net, 'output_size', None)}" if net is not None else "none"
        logged = "LOGGED-SHORTFALL" if getattr(self, "logged", []) else ""
        print(f"  {step:46s} -> {out[:52]:52s} | {prov:44s} | sf={None if sf is None else sf.get('dataset_id')} cd={(st['current_dataset'] or {}).get('tickers')} parts={sorted(getattr(self.m, "_described_partitions", frozenset({"n/a"})))} net={dims} pending={(st['pending_dataset'] or {}).get('params', {}).get('tickers') if st['pending_dataset'] else None} {logged}")

    def same(self, step: str, before: Dict[str, Any]) -> None:
        now = self.snap()
        diffs = [k for k in ("cd", "sf", "parts", "pending", "warning") if now[k] != before[k]]
        if now["sf_obj"] is not before["sf_obj"]:
            diffs.append("sf(identity)")
        if any(a is not b for a, b in zip(now["tensors"], before["tensors"])):
            diffs.append("tensors")
        if now["net"] is not before["net"]:
            diffs.append("network")
        print(f"      {'UNCHANGED' if not diffs else 'CHANGED: ' + ', '.join(diffs)}")
        if diffs:
            problems.append(f"{self.name} / {step}: {diffs}")


def stage(m: Any, tickers: str) -> None:
    m.stage_dataset_config(dataset_type="equities", params={"tickers": [tickers]})


# P1: a plain continued Start refuses a wider staged dataset; the partition record must not move.
r = Run("P1 partial fetch A (2x2), inline train, then a WIDER staged B on the continued network")
fake.n_features = 2
stage(r.m, "A")
r.show("staged fetch A + create-on-start", r.start())
r.show("inline train (keeps A on val/test)", r.start(inline=("train",)))
fake.n_features = 3
stage(r.m, "WIDE")
before = r.snap()
out = r.start()
r.show("start (continue) with WIDE staged", out)
r.same("refusal #1", before)
if r.logged:
    problems.append(f"P1: the REFUSED wider dataset was logged as a shortfall: {r.logged}")
out = r.start()
r.show("retry start", out)
r.same("refusal #2", before)
r.show("start_fresh consumes WIDE", r.start(start_fresh=True))
r.m.shutdown()

# P2: inline tensors in the SAME start as the refused wider staged dataset (the route's inline_data path).
r = Run("P2 inline train in the same start as a refused WIDER staged dataset")
fake.n_features = 2
stage(r.m, "A")
r.show("staged fetch A + create-on-start", r.start())
fake.n_features = 3
stage(r.m, "WIDE")
out = r.start(inline=("train",))
r.show("start(inline train) with WIDE staged", out)
print(f"      refusal says 'Nothing was loaded': {'Nothing was loaded' in r.last_full} -- yet train is now {r.prov.get(id(r.m._train_x))}")
out = r.start(inline=("val", "test"))
r.show("start(inline val+test) with WIDE staged", out)
r.show("start_fresh consumes WIDE", r.start(start_fresh=True))
r.m.shutdown()

# P3: F1 refusal right after a refused (422) staged fetch, then recovery.
r = Run("P3 A, then a 422 on WIDE, then WIDE refused as too wide, then start_fresh")
fake.n_features = 2
stage(r.m, "A")
r.show("staged fetch A", r.start())
fake.n_features, fake.create_mode = 3, "422"
stage(r.m, "WIDE")
before = r.snap()
r.show("422 on WIDE", r.start())
r.same("422", before)
fake.create_mode = "ok"
r.show("WIDE too wide", r.start())
r.same("F1", before)
r.show("start_fresh", r.start(start_fresh=True))
r.m.shutdown()


# P4: auto-start while a dataset is staged (an operator staged during auto-start's wait_for_ready).
def autostart(m: Any) -> str:
    settings = SimpleNamespace(juniper_data_url=fake.url, auto_dataset="equities", auto_dataset_params='{"tickers": ["AUTO"]}', allow_truncated_datasets=False, auto_network="{}")
    spy = MagicMock(wraps=m.logger)
    with patch.object(m, "_run_training"), patch.object(m, "logger", spy):
        asyncio.run(_auto_start_training(SimpleNamespace(state=SimpleNamespace(lifecycle=m)), settings))
    return [c.args[0] % tuple(c.args[1:]) if len(c.args) > 1 else c.args[0] for c in spy.warning.call_args_list if "DATASET" in str(c.args[0])]


for label, staged_width, staged_meta in (("P4a CLEAN staged (same width) pending when auto-start runs a PARTIAL fetch", 2, {}), ("P4b WIDER staged pending when auto-start runs a PARTIAL fetch", 3, dict(PARTIAL_META))):
    m = M.TrainingLifecycleManager()
    print(f"\n=== {label}")
    try:
        stage(m, "STAGED")
        # auto-start's own fetch: 2x2, PARTIAL. The staged reload inside the same start_training then
        # answers with the staged width/meta (the fake answers every POST with its current config).
        fake.n_features, fake.meta = 2, dict(PARTIAL_META)
        orig_reload = m._reload_dataset

        def reload_with_staged_shape(**kw: Any) -> None:
            fake.n_features, fake.meta = staged_width, staged_meta
            try:
                return orig_reload(**kw)
            finally:
                fake.n_features, fake.meta = 2, dict(PARTIAL_META)

        with patch.object(m, "_reload_dataset", side_effect=reload_with_staged_shape):
            logged = autostart(m)
        st = m.get_status()
        print(f"  auto_start_failure : {(m._auto_start_failure or 'None')[:150]}")
        print(f"  log (WARNING)      : {[w[:80] for w in logged]}")
        print(f"  status shortfall   : {None if st['dataset_shortfall'] is None else st['dataset_shortfall'].get('dataset_id')}")
        print(f"  status current     : {st['current_dataset']}  pending={st['pending_dataset']}  parts={sorted(getattr(m, "_described_partitions", frozenset({"n/a"})))}")
        if logged and st["dataset_shortfall"] is None:
            problems.append(f"{label}: the log says a run is training on a partial dataset; status says dataset_shortfall null")
    finally:
        m.shutdown()

fake.close()
print("\nPROBLEMS:" if problems else "\nPROBLEMS: none")
for p in problems:
    print("  " + p)
