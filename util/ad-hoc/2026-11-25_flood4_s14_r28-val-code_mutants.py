"""
Mutants of the four X7 off-loop sites juniper-canopy's test_x7_sites_outside_main_gate.py pins, run against the r28
carrier's new test file (and, for comparison, main's old one), with and without an in-process load.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc -- validation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: the Overtoad's ruling 28 (notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8);
    flood-4 session 14 code lens r28-val-code; runner util/ad-hoc/2026-11-25_flood4_s14_r28-val-code_run.py

Usage:
    python <this file> --python <venv python> --new-tree <assembled tree copy> --old-tree <main tree copy>
        --out <dir> [--only ID,ID] [--skip-old] [--skip-load]

Each mutant is one exact text replacement (the old text must occur exactly once) in one source file of a tree. The
file's sha256 is recorded before, after mutation and after restore; restore happens in a `finally:` and a mismatch
stops the script. Conditions: "new" = the new file, no load; "new_gcload" = the new file under R28V_LOAD=gc (12 M
retained objects, gc.collect() every 0.25 s); "old" = main's old file, no load (old tree, same mutant).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess  # nosec B404 - runs the lens's own runner
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "2026-11-25_flood4_s14_r28-val-code_run.py"
SUMMARY = HERE / "2026-11-25_flood4_s14_r28-val-code_summarize.py"
TEST = "src/tests/regression/test_x7_sites_outside_main_gate.py"
ADAPTER = "src/backend/cascor_service_adapter.py"
BACKEND = "src/backend/service_backend.py"
POOL = '__import__("concurrent.futures").futures.ThreadPoolExecutor(max_workers=1)'

C_OLD = "return bool(await asyncio.to_thread(self._client.is_alive))"
A_OLD = "has_network = await asyncio.to_thread(self._adapter.attach_to_existing)"
S_OLD = "self._synced_state = await asyncio.to_thread(CascorStateSync(self._adapter.client).sync)"
R_OLD = "topology = await asyncio.to_thread(self.extract_network_topology)"

MUTANTS = [
    ("C1", "connect", ADAPTER, C_OLD, "return bool(self._client.is_alive())", "inline on the loop"),
    ("C2", "connect", ADAPTER, C_OLD, f"return bool({POOL}.submit(self._client.is_alive).result())", "offloaded, loop blocks on the result"),
    ("C3", "connect", ADAPTER, C_OLD, "return True", "never calls is_alive"),
    ("C4", "connect", ADAPTER, C_OLD, "await asyncio.to_thread(self._client.is_alive); return bool(await asyncio.to_thread(self._client.is_alive))", "calls is_alive twice"),
    ("A1", "attach", BACKEND, A_OLD, "has_network = self._adapter.attach_to_existing()", "inline on the loop"),
    ("A2", "attach", BACKEND, A_OLD, f"has_network = {POOL}.submit(self._adapter.attach_to_existing).result()", "offloaded, loop blocks on the result"),
    ("A3", "attach", BACKEND, A_OLD, "has_network = False", "never calls attach_to_existing"),
    ("A4", "attach", BACKEND, A_OLD, "await asyncio.to_thread(self._adapter.attach_to_existing); has_network = await asyncio.to_thread(self._adapter.attach_to_existing)", "calls attach_to_existing twice"),
    ("S1", "sync", BACKEND, S_OLD, "self._synced_state = CascorStateSync(self._adapter.client).sync()", "inline on the loop"),
    ("S2", "sync", BACKEND, S_OLD, f"self._synced_state = {POOL}.submit(CascorStateSync(self._adapter.client).sync).result()", "offloaded, loop blocks on the result"),
    ("S3", "sync", BACKEND, S_OLD, "self._synced_state = SyncedState()", "never calls sync (a default state instead)"),
    ("S4", "sync", BACKEND, S_OLD, "await asyncio.to_thread(CascorStateSync(self._adapter.client).sync); self._synced_state = await asyncio.to_thread(CascorStateSync(self._adapter.client).sync)", "calls sync twice"),
    ("R1", "relay", ADAPTER, R_OLD, "topology = self.extract_network_topology()", "inline on the loop"),
    ("R2", "relay", ADAPTER, R_OLD, f"topology = {POOL}.submit(self.extract_network_topology).result()", "offloaded, loop blocks on the result"),
    ("R3", "relay", ADAPTER, R_OLD, "topology = None", "never calls extract_network_topology"),
    ("R4", "relay", ADAPTER, R_OLD, "await asyncio.to_thread(self.extract_network_topology); topology = await asyncio.to_thread(self.extract_network_topology)", "calls extract_network_topology twice"),
    ("R5", "relay", ADAPTER, R_OLD, '__import__("time").sleep(1.0); topology = await asyncio.to_thread(self.extract_network_topology)', "offloaded, but the loop is blocked 1.0 s beside it (a bounded on-loop stall that is not the held call)"),
    ("R6", "relay", ADAPTER, R_OLD, "topology = await asyncio.get_running_loop().run_in_executor(None, self.extract_network_topology)", "EQUIVALENT refactor (run_in_executor): must PASS"),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(python: str, tree: Path, out: Path, label: str, env: list[str]) -> dict:
    command = [sys.executable, str(RUNNER), "--python", python, "--tree", str(tree), "--out", str(out), "--label", label, "--no-cov", "--no-maxfail"]
    for pair in env:
        command += ["--env", pair]
    command += ["--", TEST]
    started = time.time()
    subprocess.run(command, check=False, capture_output=True, text=True)  # nosec B603
    summary = subprocess.run([sys.executable, str(SUMMARY), str(out), label], check=False, capture_output=True, text=True)  # nosec B603
    result = json.loads(summary.stdout.strip().splitlines()[-1]) if summary.stdout.strip() else {}
    result["wall_seconds"] = round(time.time() - started, 1)
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--python", required=True)
    parser.add_argument("--new-tree", required=True)
    parser.add_argument("--old-tree", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--only", default="")
    parser.add_argument("--skip-old", action="store_true")
    parser.add_argument("--skip-load", action="store_true")
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    only = {x for x in args.only.split(",") if x}
    load = ["R28V_LOAD=gc", "R28V_HEAP_M=12", "R28V_GC_INTERVAL=0.25", "R28V_HELD=1"]
    for mid, site, rel, old, new, what in MUTANTS:
        if only and mid not in only:
            continue
        record = {"id": mid, "site": site, "file": rel, "old": old, "new": new, "what": what, "conditions": {}}
        trees = [("new", Path(args.new_tree), ["R28V_HELD=1"])]
        if not args.skip_load:
            trees.append(("new_gcload", Path(args.new_tree), load))
        if not args.skip_old:
            trees.append(("old", Path(args.old_tree), []))
        for condition, tree, env in trees:
            path = tree / rel
            before = sha256(path)
            text = path.read_text(encoding="utf-8")
            if text.count(old) != 1:
                record["conditions"][condition] = {"error": f"old text occurs {text.count(old)} times"}
                continue
            try:
                path.write_text(text.replace(old, new), encoding="utf-8")
                mutated = sha256(path)
                result = run(args.python, tree, out, f"{mid}_{condition}", env)
            finally:
                path.write_text(text, encoding="utf-8")
            after = sha256(path)
            result.update({"sha256_before": before, "sha256_mutated": mutated, "sha256_after": after, "restored_byte_for_byte": before == after})
            record["conditions"][condition] = result
            if before != after:
                print(json.dumps({"FATAL": "restore mismatch", "id": mid, "path": str(path)}), flush=True)
                return 2
        with open(out / f"{mid}.json", "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=1)
        brief = {c: {"per_test": r.get("per_test"), "wall": r.get("wall_seconds"), "restored": r.get("restored_byte_for_byte")} for c, r in record["conditions"].items()}
        print(json.dumps({"id": mid, "what": what, "results": brief}), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
