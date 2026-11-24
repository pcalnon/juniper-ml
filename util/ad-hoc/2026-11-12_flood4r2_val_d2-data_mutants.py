#!/usr/bin/env python3
"""
Validator mutants for juniper-data's "run the unrun tests" carrier: one-line breaks of product code that only a newly
selected test should see, run against the newly selected tests and against main's two pull-request lanes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (Cursor flood-4 session 7: validating the d2-unrun-tests carrier)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session7/briefs/VF_validate_data_unrun_tests.txt (check D),
         util/ad-hoc/2026-11-12_flood4r2_val_d2-data_run_lane.py (the lane runner this calls)

The mutants below are the validator's own; none is one of the builder's seven. ``BM2`` is the one exception and is
labelled so: it is the builder's M2, re-run here because the brief asks for one of M1-M4 to be re-checked.

Verbs:

  hashes --tree <tree>
      Prints the sha256 of every file a mutant may touch (to be logged BEFORE any mutation run).

  discover --tree <tree> --python <venv python> --new-nodes <file> --out <dir> [--only ID,ID]
      Each mutant alone, against the newly selected tests of the modules it names (node ids taken from
      --new-nodes, so that a module's long-selected tests are left out). A mutant is "killed" when the run fails.

  lanes --tree <tree> --python <venv python> --deselect-unit <file> --deselect-integration <file> --out <dir>
        --ids ID,ID[,ID...]
      All named mutants applied AT ONCE, then CI's unit lane (no coverage) and CI's integration lane with the newly
      selected tests deselected, which is exactly the selection main's lanes have. Passing means no test main's
      pull-request lanes run sees any of them.

Every mutation is applied to a tree of the validator's own, checked to occur exactly once, restored in ``finally``,
and the file's sha256 is compared with its value before the mutant after every run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

RUN_LANE = Path(__file__).with_name("2026-11-12_flood4r2_val_d2-data_run_lane.py")
UNIT = "juniper_data/tests/unit/"
INTEGRATION = "juniper_data/tests/integration/"

MUTANTS = {
    "VM1": {
        "file": "juniper_data/storage/local_fs.py",
        "old": 're.compile(r"[A-Za-z0-9][A-Za-z0-9._',
        "new": 're.compile(r"[A-Za-z0-9.][A-Za-z0-9._',
        "what": "the dataset-id allowlist accepts a leading dot (a hidden file name such as '.hidden')",
        "modules": [UNIT + "test_local_fs_path_traversal.py"],
    },
    "VM2": {
        "file": "juniper_data/storage/local_fs.py",
        "old": '._\\-]{0,127}")',
        "new": '._\\-]{0,255}")',
        "what": "the dataset-id allowlist's length bound moves from 128 to 256 characters",
        "modules": [UNIT + "test_local_fs_path_traversal.py"],
    },
    "VM3": {
        "file": "juniper_data/storage/local_fs.py",
        "old": "                    exc_info=True,\n                )\n            raise\n        self._invalidate_metadata_cache()\n        return True\n",
        "new": "                    exc_info=True,\n                )\n            raise\n        return True\n",
        "what": "LocalFSDatasetStore.update_meta stops invalidating the metadata cache",
        "modules": [UNIT + "test_metadata_cache.py"],
    },
    "VM4": {
        "file": "juniper_data/storage/local_fs.py",
        "old": "        if deleted:\n            self._invalidate_metadata_cache()\n        return deleted\n",
        "new": "        if deleted:\n            pass\n        return deleted\n",
        "what": "LocalFSDatasetStore.delete stops invalidating the metadata cache",
        "modules": [UNIT + "test_metadata_cache.py"],
    },
    "VM5": {
        "file": "juniper_data/storage/hf_store.py",
        "old": '        """Save to cache store."""\n        self._cache_store.save(dataset_id, meta, arrays)\n        self._invalidate_metadata_cache()\n',
        "new": '        """Save to cache store."""\n        self._cache_store.save(dataset_id, meta, arrays)\n',
        "what": "HuggingFaceDatasetStore.save stops invalidating the metadata cache",
        "modules": [UNIT + "test_metadata_cache.py"],
    },
    "VM6": {
        "file": "juniper_data/storage/cached.py",
        "old": "        # The primary write above changed what ``list_all_metadata`` returns.\n        self._invalidate_metadata_cache()\n",
        "new": "        # The primary write above changed what ``list_all_metadata`` returns.\n        pass\n",
        "what": "CachedDatasetStore.save stops invalidating its own metadata cache",
        "modules": [UNIT + "test_metadata_cache.py"],
    },
    "VM7": {
        "file": "juniper_data/api/app.py",
        "old": '            content={"detail": jsonable_encoder(exc.errors())},',
        "new": '            content={"detail": str(exc.errors())},',
        "what": "the app's 422 handler flattens the per-field error list into one string (APD-DATA-013)",
        "modules": [UNIT + "test_api_app.py"],
    },
    "VM8": {
        "file": "juniper_data/api/routes/datasets.py",
        "old": "        arrays = await asyncio.to_thread(generator_class.generate, params)",
        "new": "        arrays = generator_class.generate(params)",
        "what": "POST /v1/datasets runs the generator on the event-loop thread (SEC-04)",
        "modules": [UNIT + "test_phase1d_security.py"],
    },
    "VM9": {
        "file": "juniper_data/api/routes/datasets.py",
        "old": "        total_updated=len(updated),",
        "new": "        total_updated=len(request.dataset_ids),",
        "what": "PATCH /v1/datasets/batch-tags counts the ids it did not find as updated",
        "modules": [UNIT + "test_batch_operations.py"],
    },
    "VM10": {
        "file": "juniper_data/api/routes/datasets.py",
        "old": '                zf.writestr(f"{dataset_id}.npz", artifact_bytes)',
        "new": '                zf.writestr(f"{dataset_id}.npy", artifact_bytes)',
        "what": "POST /v1/datasets/batch-export names each archive member .npy",
        "modules": [UNIT + "test_batch_operations.py"],
    },
    "VM11": {
        "file": "juniper_data/api/routes/datasets.py",
        "old": '                            "requested": list(request.dataset_ids),',
        "new": '                            "requested": exported,',
        "what": "the batch-export manifest reports the exported ids as the requested ones (APD-DATA-010)",
        "modules": [UNIT + "test_batch_operations.py"],
    },
    "VM12": {
        "file": "juniper_data/api/routes/datasets.py",
        "old": "                    error=e.detail,\n                )\n            )\n            total_failed += 1\n",
        "new": "                    error=e.detail,\n                )\n            )\n            total_failed += 0\n",
        "what": "batch-create does not count an item refused with an HTTP error as failed",
        "modules": [UNIT + "test_batch_operations.py"],
    },
    "VM13": {
        "file": "juniper_data/api/settings.py",
        "old": "        parse_trusted_networks(v)\n        return v\n",
        "new": "        return v\n",
        "what": "Settings accepts an unparseable metrics_trusted_ips entry (SEC-16 fail-loud)",
        "modules": [UNIT + "test_phase1d_security.py"],
    },
    "VM14": {
        "file": "juniper_data/api/constants.py",
        "old": '        f"{API_PREFIX}/health/ready",\n',
        "new": "",
        "what": "/v1/health/ready is no longer exempt from API-key authentication and rate limiting",
        "modules": [INTEGRATION + "test_security_integration.py", UNIT + "test_r2_1_2_wire_compat.py", UNIT + "test_phase1d_security.py"],
    },
    "VM15": {
        "file": "juniper_data/api/constants.py",
        "old": '        "/metrics",\n',
        "new": "",
        "what": "/metrics is no longer exempt from API-key authentication (only the trailing-slash form is)",
        "modules": [UNIT + "test_phase1d_security.py"],
    },
    "VM16": {
        "file": "juniper_data/api/routes/health.py",
        "old": "    response.headers[READINESS_HEADER] = overall\n",
        "new": "",
        "what": "/v1/health/ready stops sending X-Juniper-Readiness",
        "modules": [UNIT + "test_r2_1_2_wire_compat.py"],
    },
    "BM2": {
        "file": "juniper_data/storage/local_fs.py",
        "old": '    if ".." in dataset_id:',
        "new": '    if "..." in dataset_id:',
        "what": "THE BUILDER'S M2, re-checked: _validate_dataset_id stops refusing a parent reference inside an id",
        "modules": [UNIT + "test_local_fs_path_traversal.py"],
    },
}


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def touched_files() -> list[str]:
    return sorted({spec["file"] for spec in MUTANTS.values()})


def apply(tree: Path, ids: list[str]) -> dict[str, bytes]:
    """Apply the named mutants; return the original bytes of every file touched."""
    originals: dict[str, bytes] = {}
    try:
        for mutant_id in ids:
            spec = MUTANTS[mutant_id]
            path = tree / spec["file"]
            originals.setdefault(spec["file"], path.read_bytes())
            text = path.read_text(encoding="utf-8")
            if text.count(spec["old"]) != 1:
                raise SystemExit(f"{mutant_id}: the old text occurs {text.count(spec['old'])} times in {spec['file']}, not once")
            path.write_text(text.replace(spec["old"], spec["new"]), encoding="utf-8")
    except (Exception, SystemExit, KeyboardInterrupt):
        restore(tree, originals)
        raise
    return originals


def restore(tree: Path, originals: dict[str, bytes]) -> None:
    for name, data in originals.items():
        (tree / name).write_bytes(data)


def run_lane(python: str, tree: Path, out: Path, lane: str, extra: list[str]) -> dict:
    subprocess.run([sys.executable, str(RUN_LANE), "--python", python, "--tree", str(tree), "--out", str(out), "--lane", lane, *extra], capture_output=True, text=True, check=False)
    return json.loads((out / "result.json").read_text(encoding="utf-8"))


def verb_hashes(ns: argparse.Namespace) -> int:
    tree = Path(ns.tree)
    for name in touched_files():
        print(f"{sha256_of(tree / name)}  {name}")
    return 0


def verb_discover(ns: argparse.Namespace) -> int:
    tree, out = Path(ns.tree), Path(ns.out)
    out.mkdir(parents=True, exist_ok=True)
    new_nodes = [line.strip() for line in Path(ns.new_nodes).read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = ns.only.split(",") if ns.only else [key for key in MUTANTS]
    before = {name: sha256_of(tree / name) for name in touched_files()}
    report = {"tree": str(tree), "python": ns.python, "sha256_before": before, "mutants": {}}
    for mutant_id in ids:
        spec = MUTANTS[mutant_id]
        nodes = [node for node in new_nodes if node.split("::", 1)[0] in spec["modules"]]
        if not nodes:
            raise SystemExit(f"{mutant_id}: no newly selected test in {spec['modules']}")
        nodes_file = out / f"{mutant_id}_nodes.txt"
        nodes_file.write_text("\n".join(nodes) + "\n", encoding="utf-8")
        originals = apply(tree, [mutant_id])
        try:
            result = run_lane(ns.python, tree, out / mutant_id, "nodes", ["--nodes-file", str(nodes_file)])
        finally:
            restore(tree, originals)
        restored = sha256_of(tree / spec["file"]) == before[spec["file"]]
        step = result["steps"]["run01"]
        entry = {"what": spec["what"], "file": spec["file"], "newly_selected_tests_run": len(nodes), "exit": step["exit"], "summary": step["summary"], "killed": step["exit"] == 1, "failed": step["junit"].get("failed_or_error", []), "restored_byte_for_byte": restored, "sha256_after": sha256_of(tree / spec["file"])}
        report["mutants"][mutant_id] = entry
        print(f"{mutant_id:5s} killed={entry['killed']} exit={entry['exit']} restored={restored} | {entry['summary']} | {len(entry['failed'])} failed of {len(nodes)}")
        (out / "discover.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
        if not restored:
            raise SystemExit(f"{spec['file']} was not restored after {mutant_id}")
    return 0


def verb_lanes(ns: argparse.Namespace) -> int:
    tree, out = Path(ns.tree), Path(ns.out)
    out.mkdir(parents=True, exist_ok=True)
    ids = ns.ids.split(",")
    before = {name: sha256_of(tree / name) for name in touched_files()}
    originals = apply(tree, ids)
    try:
        during = {name: sha256_of(tree / name) for name in originals}
        unit = run_lane(ns.python, tree, out / "unit", "unit", ["--no-cov", "--deselect-file", ns.deselect_unit])
        integration = run_lane(ns.python, tree, out / "integration", "integration", ["--deselect-file", ns.deselect_integration])
    finally:
        restore(tree, originals)
    after = {name: sha256_of(tree / name) for name in touched_files()}
    report = {
        "tree": str(tree),
        "python": ns.python,
        "mutants_applied_at_once": {mutant_id: MUTANTS[mutant_id]["what"] for mutant_id in ids},
        "sha256_before": before,
        "sha256_with_mutants": during,
        "sha256_after": after,
        "restored_byte_for_byte": after == before,
        "main_unit_lane": {"exit": unit["steps"]["pytest"]["exit"], "summary": unit["steps"]["pytest"]["summary"], "failed": unit["junit"].get("failed_or_error", []), "deselected_by_file": unit["deselected_by_file"]},
        "main_integration_lane": {"exit": integration["steps"]["pytest"]["exit"], "summary": integration["steps"]["pytest"]["summary"], "failed": integration["junit"].get("failed_or_error", []), "deselected_by_file": integration["deselected_by_file"]},
    }
    (out / "lanes.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(f"mutants at once: {ids}")
    print(f"main unit lane:        exit={report['main_unit_lane']['exit']} | {report['main_unit_lane']['summary']} | failed {report['main_unit_lane']['failed']}")
    print(f"main integration lane: exit={report['main_integration_lane']['exit']} | {report['main_integration_lane']['summary']} | failed {report['main_integration_lane']['failed']}")
    print(f"restored byte for byte: {report['restored_byte_for_byte']}")
    return 0 if report["restored_byte_for_byte"] else 3


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    verbs = parser.add_subparsers(dest="verb", required=True)
    hashes = verbs.add_parser("hashes")
    hashes.add_argument("--tree", required=True)
    hashes.set_defaults(func=verb_hashes)
    discover = verbs.add_parser("discover")
    for option in ("tree", "python", "new-nodes", "out"):
        discover.add_argument(f"--{option}", required=True)
    discover.add_argument("--only", default="")
    discover.set_defaults(func=verb_discover)
    lanes = verbs.add_parser("lanes")
    for option in ("tree", "python", "deselect-unit", "deselect-integration", "out", "ids"):
        lanes.add_argument(f"--{option}", required=True)
    lanes.set_defaults(func=verb_lanes)
    ns = parser.parse_args()
    return ns.func(ns)


if __name__ == "__main__":
    sys.exit(main())
