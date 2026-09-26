"""NEW mutants for cascor#688 (scratch; the implementer's 48 do not include these).

usage: mutate_v688.py <cascor-tree> <scratch-dir> [MUTANT ...] [--suite named|api]
The tree is copied once to <scratch-dir>/tree; each mutant is an exact replacement whose anchor must occur
exactly once (else SKIPPED); files are restored after every run; an unmutated CONTROL runs first.
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
NAMED = [
    "tests/unit/api/test_allow_truncated_datasets.py",
    "tests/unit/api/test_auto_start_shortfall.py",
    "tests/unit/api/test_shortfall_lifecycle.py",
    "tests/unit/api/test_truncatable_generators.py",
    "tests/unit/api/test_start_fresh_carries_params.py",
    "tests/unit/api/test_start_refuses_wider_staged_dataset.py",
]
RELOAD_DESCRIBED = '        self._described_partitions = frozenset(name for name, tensor in (("train", new_train_x), ("val", new_val_x), ("test", new_test_x)) if tensor is not None)\n'
F1_CHECK = "        if refuse_wider_than is not None:\n"
RELOAD_LOG = "        self._log_bound_dataset_shortfall(meta, acceptance_source=acceptance_source)\n        self.logger.info(\"Reloaded dataset"
AS_FETCH_SF = "            self._dataset_shortfall = dataset_shortfall\n            self._described_partitions = filled if"
LEFT_BRANCH = "        if left:\n            self._described_partitions = left\n            return\n"

Edit = Tuple[str, str, str]
MUTANTS: Dict[str, List[Edit]] = {
    # #687 interaction: the refused (too-wide) artifact's partitions leak into the record's partition set.
    "NV1_described_set_before_the_F1_refusal": [(MGR, RELOAD_DESCRIBED, ""), (MGR, F1_CHECK, RELOAD_DESCRIBED + F1_CHECK)],
    # #687 interaction: item 8's guarantee on the F1 path -- a dataset refused as too wide is logged as trained on.
    "NV2_shortfall_logged_before_the_F1_refusal": [(MGR, RELOAD_LOG, '        self.logger.info("Reloaded dataset'), (MGR, F1_CHECK, "        self._log_bound_dataset_shortfall(meta, acceptance_source=acceptance_source)\n" + F1_CHECK)],
    # as_fetch: a CLEAN fetch handed in keeps whatever annotation was loaded before (only a non-None one binds).
    "NV3_clean_as_fetch_keeps_the_old_annotation": [(MGR, AS_FETCH_SF, "            if dataset_shortfall is not None:\n                self._dataset_shortfall = dataset_shortfall\n            self._described_partitions = filled if")],
    # item 4: drop the incomplete_rows arm of the refusal predicate.
    "NV4_predicate_drops_incomplete_rows": [(MGR, '        looks_like_shortfall = "allow_truncation" in detail or "incomplete_rows" in detail\n', '        looks_like_shortfall = "allow_truncation" in detail\n')],
    # ruling: while a fetch's partitions are left, a NAMED inline start (the route's spiral) adopts its own config.
    "NV5_named_inline_adopts_config_while_splits_left": [(MGR, LEFT_BRANCH, "        if left:\n            self._described_partitions = left\n            if dataset_config and \"train\" in bound:\n                self._current_dataset_config = dict(dataset_config)\n            return\n")],
}


def _env() -> Dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in ("SENTRY_SDK_DSN", "JUNIPER_CASCOR_LOG_DIR", "JUNIPER_CASCOR_SENTRY_DSN", "SENTRY_DSN")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _pytest(tree: str, suite: str) -> Tuple[str, List[str]]:
    for dirpath, dirnames, _files in os.walk(os.path.join(tree, "src")):
        for d in list(dirnames):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(dirpath, d), ignore_errors=True)
    targets = NAMED if suite == "named" else ["tests/unit/api"]
    proc = subprocess.run([PY, "-m", "pytest", *targets, "-p", "no:cacheprovider", "-rfE", "-x" if suite == "api" else "-rfE"], cwd=os.path.join(tree, "src"), env=_env(), capture_output=True, text=True, timeout=3000)  # nosec B603
    out = proc.stdout + proc.stderr
    summary = [ln.strip() for ln in out.splitlines() if re.search(r"\d+ (passed|failed|error)", ln)]
    failed = sorted({ln.split(" ", 1)[1].split(" - ")[0] for ln in out.splitlines() if ln.startswith(("FAILED ", "ERROR "))})
    return (summary[-1] if summary else "?? no summary"), failed


def main(argv: List[str]) -> int:
    suite = "named"
    if "--suite" in argv:
        i = argv.index("--suite")
        suite = argv[i + 1]
        argv = argv[:i] + argv[i + 2 :]
    src_tree, scratch = argv[0], argv[1]
    only = argv[2:]
    tree = os.path.join(scratch, "tree")
    if not os.path.isdir(tree):
        shutil.copytree(src_tree, tree, symlinks=True, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".pytest_cache"))
    summary, failed = _pytest(tree, suite)
    print(f"CONTROL ({suite}): {summary}", flush=True)
    if failed or "failed" in summary or "?" in summary:
        print("CONTROL NOT GREEN", failed)
        return 2
    for name, edits in MUTANTS.items():
        if only and name not in only:
            continue
        originals: Dict[str, str] = {}
        ok = True
        for rel, old, new in edits:
            path = os.path.join(tree, rel)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            originals.setdefault(path, text)
            if text.count(old) != 1:
                print(f"{name}: SKIPPED -- anchor occurs {text.count(old)} times", flush=True)
                ok = False
                break
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text.replace(old, new))
        if ok:
            summary, failed = _pytest(tree, suite)
            print(f"{name}: {'KILLED' if failed else 'SURVIVED'} | {summary}", flush=True)
            for f in failed:
                print(f"    {f}", flush=True)
        for path, text in originals.items():
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
