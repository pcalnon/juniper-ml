"""NEW mutants for cascor#686 (not among the implementer's 35), run on a scratch copy of a tree (scratch only).

usage: mutate_new.py <src-tree> <work-dir> <scope: named|unit_api> [MUTANT ...]
Each mutant is an exact replacement whose anchor must occur exactly once, or it is SKIPPED.
A CONTROL run comes first and must be green. Reads pytest's own summary line.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess  # nosec B404
import sys
from typing import Dict, List, Tuple

PY = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
MGR = "src/api/lifecycle/manager.py"
NAMED = ["tests/unit/api/test_allow_truncated_datasets.py", "tests/unit/api/test_auto_start_shortfall.py", "tests/unit/api/test_shortfall_lifecycle.py", "tests/unit/api/test_truncatable_generators.py", "tests/unit/api/test_start_fresh_carries_params.py", "tests/unit/api/test_c5_retention_reset.py", "tests/unit/api/test_lifecycle_monitor.py"]

MUTANTS: Dict[str, Tuple[str, str, str]] = {
    # A legacy train+test artifact (X_test promoted to the val slot under the override): describe the
    # partitions the ARTIFACT carried rather than the ones that were bound -- "val" drops out.
    "NM1_described_from_artifact_keys": (
        MGR,
        '        self._described_partitions = frozenset(name for name, tensor in (("train", new_train_x), ("val", new_val_x), ("test", new_test_x)) if tensor is not None)\n',
        '        self._described_partitions = frozenset(name for name, key in (("train", "X_train"), ("val", "X_val"), ("test", "X_test")) if key in arrays)\n',
    ),
    # A caller that hands in its OWN annotated fetch (auto-start) replaces the record even while an
    # earlier fetch's partition is left -- the opposite of 653bc3f's choice. Survival = unpinned either way.
    "NM4_caller_annotation_wins_over_leftovers": (
        MGR,
        "        left = self._described_partitions - bound\n        if left:\n",
        "        left = self._described_partitions - bound\n        if left and dataset_shortfall is None:\n",
    ),
    # A start-fresh is a "clean-launch reset": forget which partitions the record stands on.
    "NM19_start_fresh_forgets_partitions": (
        MGR,
        '        self.logger.info("start_fresh: discarded model + cleared retained metrics/history (snapshots on disk preserved)")\n',
        '        self._described_partitions = frozenset()\n        self.logger.info("start_fresh: discarded model + cleared retained metrics/history (snapshots on disk preserved)")\n',
    ),
    # ...or clear the record outright, as a clean launch would.
    "NM20_start_fresh_clears_record": (
        MGR,
        '        self.logger.info("start_fresh: discarded model + cleared retained metrics/history (snapshots on disk preserved)")\n',
        '        self._current_dataset_config = None\n        self._dataset_shortfall = None\n        self._described_partitions = frozenset()\n        self.logger.info("start_fresh: discarded model + cleared retained metrics/history (snapshots on disk preserved)")\n',
    ),
    # Move the record rebind AFTER the pending staged fetch ("bind the record once the data is final").
    "NM11_rebind_after_pending_reload": (
        MGR,
        "            self._rebind_dataset_record_locked(bound, dataset_config=dataset_config, dataset_shortfall=dataset_shortfall)\n            if dataset_shortfall is not None:\n",
        "            _nm11 = (bound, dataset_config, dataset_shortfall)\n            if dataset_shortfall is not None:\n",
    ),
}
# NM11 needs a second edit: rebind after the pending reload.
NM11_SECOND = (
    MGR,
    "                self._reload_dataset(fetch_path=_FETCH_PATH_STAGED_START, **self._pending_dataset_config)\n                self._pending_dataset_config = None\n",
    "                self._reload_dataset(fetch_path=_FETCH_PATH_STAGED_START, **self._pending_dataset_config)\n                self._pending_dataset_config = None\n            self._rebind_dataset_record_locked(_nm11[0], dataset_config=_nm11[1], dataset_shortfall=_nm11[2])\n",
)


def _env() -> Dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in ("SENTRY_SDK_DSN", "JUNIPER_CASCOR_LOG_DIR", "JUNIPER_CASCOR_SENTRY_DSN", "SENTRY_DSN")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _pytest(tree: str, scope: str) -> Tuple[str, List[str]]:
    for dirpath, dirnames, _files in os.walk(os.path.join(tree, "src")):
        for d in list(dirnames):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(dirpath, d), ignore_errors=True)
    if scope == "probe":
        probe = os.path.join(os.path.dirname(os.path.abspath(__file__)), "probes", "probe_ruling_matrix.py")
        proc = subprocess.run([PY, probe, tree], cwd=os.path.dirname(probe), env=_env(), capture_output=True, text=True, timeout=3000)  # nosec B603
        lines = [ln for ln in proc.stdout.splitlines() if " -> " in ln and ("OVERCLAIM" in ln or "UNDERCLAIM" in ln or "NAMELOSS" in ln) and "TWO-FETCHES" not in ln]
        return (f"probe: {len(lines)} flagged step(s)" + (" -- 1 passed" if not lines else " -- 1 failed")), lines
    targets = NAMED if scope == "named" else ["tests/unit/api"]
    proc = subprocess.run([PY, "-m", "pytest", *targets, "-p", "no:cacheprovider", "-rfE"], cwd=os.path.join(tree, "src"), env=_env(), capture_output=True, text=True, timeout=3000)  # nosec B603
    out = proc.stdout + proc.stderr
    summary = [ln.strip() for ln in out.splitlines() if re.search(r"\d+ (passed|failed|error)", ln)]
    failed = sorted({ln.split(" ", 1)[1].split(" - ")[0] for ln in out.splitlines() if ln.startswith(("FAILED ", "ERROR "))})
    return (summary[-1] if summary else "?? no summary"), failed


def _apply(tree: str, rel: str, old: str, new: str) -> str:
    path = os.path.join(tree, rel)
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    n = text.count(old)
    if n != 1:
        raise LookupError(f"anchor occurs {n} times in {rel}")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text.replace(old, new, 1))
    return text


def main(argv: List[str]) -> int:
    src_tree, work, scope = argv[0], argv[1], argv[2]
    only = argv[3:]
    tree = os.path.join(work, "tree")
    shutil.rmtree(tree, ignore_errors=True)
    shutil.copytree(src_tree, tree, symlinks=True, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
    summary, failed = _pytest(tree, scope)
    print(f"CONTROL: {summary}", flush=True)
    if failed or "failed" in summary or "??" in summary:
        print("CONTROL NOT GREEN -- stopping", failed)
        return 2
    for name, (rel, old, new) in MUTANTS.items():
        if only and name not in only:
            continue
        originals = {}
        try:
            originals[rel] = _apply(tree, rel, old, new)
            if name == "NM11_rebind_after_pending_reload":
                path = os.path.join(tree, NM11_SECOND[0])
                with open(path, encoding="utf-8") as fh:
                    cur = fh.read()
                if cur.count(NM11_SECOND[1]) != 1:
                    raise LookupError("second anchor not unique")
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(cur.replace(NM11_SECOND[1], NM11_SECOND[2], 1))
        except LookupError as exc:
            print(f"{name}: SKIPPED ({exc})", flush=True)
            for r, t in originals.items():
                with open(os.path.join(tree, r), "w", encoding="utf-8") as fh:
                    fh.write(t)
            continue
        summary, failed = _pytest(tree, scope)
        verdict = "KILLED" if (failed or "failed" in summary or "error" in summary) else "SURVIVED"
        print(f"{name}: {verdict} -- {summary}", flush=True)
        for f in failed[:12]:
            print(f"    {f}", flush=True)
        for r, t in originals.items():
            with open(os.path.join(tree, r), "w", encoding="utf-8") as fh:
                fh.write(t)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
