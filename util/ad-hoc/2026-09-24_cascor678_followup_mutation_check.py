#!/usr/bin/env python
"""Mutation-check the cascor#678 follow-up PR's tests on a SCRATCH copy of its worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor#678 (merged 0e016a7) and its follow-up PR; the post-merge validation at
         reports/2026-09-24_defect-register-round-42/cascor678-postmerge-validation.md, whose
         findings 1-8 are the follow-up's items 1-8 and whose mutants M21-M23 survived #678's suite.

usage: 2026-09-24_cascor678_followup_mutation_check.py <cascor-worktree> <scratch-dir> [MUTANT ...] [--base-dir DIR]

The worktree is copied ONCE to <scratch-dir>/tree (never mutated in place). Each mutant is an
exact string replacement whose anchor must occur exactly once in its file -- a mutant whose
anchor is missing or ambiguous is reported as SKIPPED, never silently run as a no-op. The file
is restored after every run. A CONTROL run with no mutation comes first and must be green, or
every KILLED below would be meaningless.

``--base-dir`` names a directory holding ``manager.py`` and ``app.py`` as they were at the PR's
base (``git show 0e016a7:<path>``); the pseudo-mutant ``BASE_0e016a7`` swaps BOTH in, which is
"do the new tests fail against the code they were written to fix".

Runs with PYTHONDONTWRITEBYTECODE=1 and -p no:cacheprovider (a stale .pyc can resurrect the
unmutated module), without JUNIPER_CASCOR_LOG_DIR (it fails six unrelated cascor tests), and
reads pytest's own summary rather than trusting a piped exit status.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess  # nosec B404 - runs pytest on a scratch copy
import sys
from typing import Dict, List, Optional, Tuple

PY = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
MGR = "src/api/lifecycle/manager.py"
APP = "src/api/app.py"
NAMED = ["tests/unit/api/test_allow_truncated_datasets.py", "tests/unit/api/test_auto_start_shortfall.py", "tests/unit/api/test_shortfall_lifecycle.py", "tests/unit/api/test_truncatable_generators.py"]

# name -> (file, anchor, replacement). Items are the follow-up's 1-8.
MUTANTS: Dict[str, Tuple[str, str, str]] = {
    # -- item 1: keep while fetched splits stay ------------------------------------------------
    "I1a_record_never_kept_while_splits_left": (MGR, "        if left:\n            self._described_partitions = left\n            return\n", "        if False:\n            self._described_partitions = left\n            return\n"),
    "I1b_fetch_records_no_partitions": (MGR, '        self._described_partitions = frozenset(name for name, tensor in (("train", new_train_x), ("val", new_val_x), ("test", new_test_x)) if tensor is not None)\n', "        self._described_partitions = frozenset()\n"),
    "I1c_fetch_leaves_partitions_stale": (MGR, '        self._described_partitions = frozenset(name for name, tensor in (("train", new_train_x), ("val", new_val_x), ("test", new_test_x)) if tensor is not None)\n', ""),
    "I1d_val_test_only_start_keeps_record": (MGR, "        else:\n            self._current_dataset_config = None\n            self._dataset_shortfall = None\n        has_record", "        else:\n            pass\n        has_record"),
    "I1e_bound_counts_train_only": (MGR, '            bound = frozenset(name for name, tensor in (("train", X), ("val", X_val), ("test", X_test)) if tensor is not None)\n', '            bound = frozenset({"train"}) if X is not None else frozenset()\n'),
    "I1f_caller_record_describes_nothing": (MGR, "        self._described_partitions = bound if has_record else frozenset()\n", "        self._described_partitions = frozenset()\n"),
    "I1g_has_record_ignores_config": (MGR, "        has_record = bool(self._current_dataset_config) or self._dataset_shortfall is not None\n", "        has_record = self._dataset_shortfall is not None\n"),
    "I1h_preswap_snapshot_omits_partitions": (MGR, "                    described_partitions=self._described_partitions,\n", ""),
    "I1i_rollback_keeps_swap_fetch_partitions": (MGR, "        self._described_partitions = pre.described_partitions\n", ""),
    "I1j_reset_clears_partitions": (MGR, "        # same reason ``_described_partitions`` is left alone: every partition\n", "        self._described_partitions = frozenset()\n        # same reason ``_described_partitions`` is left alone: every partition\n"),
    # -- item 2: every remedy opens with "To accept it," --------------------------------------
    "I2a_withheld_remedy_opens_with_retry": (MGR, '            remedy = "To accept it, send allow_truncation=true on the dataset request itself, plus incomplete_rows=accept or incomplete_rows=drop -- or retry once juniper-data answers GET /v1/generators:', '            remedy = "Retry once juniper-data answers GET /v1/generators:'),
    "I2b_deferred_remedy_without_the_phrase": (MGR, '            remedy = "To accept it, send allow_truncation=true on the dataset request itself, plus incomplete_rows=accept or incomplete_rows=drop -- this service', '            remedy = "Send allow_truncation=true on the dataset request itself, plus incomplete_rows=accept or incomplete_rows=drop -- this service'),
    "I2c_new_branch_nobody_listed": (MGR, "        elif deployment_flag_on:\n            stance = ", '        elif opt_in_skipped == "unlisted":\n            stance = "and a branch nobody listed"\n            remedy = "To accept it, do something."\n        elif deployment_flag_on:\n            stance = '),
    # -- item 3: a null stance defers whatever the flag ---------------------------------------
    "M21_null_counts_as_silent": (MGR, '        if allow_truncated and "allow_truncation" not in params:\n            truncatable = truncatable_generators()\n', '        if allow_truncated and params.get("allow_truncation") is None:\n            truncatable = truncatable_generators()\n'),
    "I3a_resolver_forgets_the_deferral": (MGR, '        elif "allow_truncation" in params and caller_stance is None:\n', "        elif False:\n"),
    "I3b_describer_ignores_the_deferral": (MGR, "        elif opt_in_skipped == _OPT_IN_SKIPPED_CALLER_DEFERRED:\n", "        elif False:\n"),
    # -- item 4: not-truncatable is a plain failure --------------------------------------------
    "I4a_undeclared_generator_is_a_refusal_again": (MGR, "        if not looks_like_shortfall or allow_truncated or opt_in_skipped == _OPT_IN_SKIPPED_NOT_TRUNCATABLE:\n", "        if not looks_like_shortfall or allow_truncated:\n"),
    # -- item 5: any schema-less entry fails the read ------------------------------------------
    "I5a_schemaless_entry_skipped": (MGR, "                raise ValueError(f\"generator {entry['name']!r} carries no parameter schema, so whether it accepts allow_truncation is unknown\")\n", "                continue\n"),
    "I5b_empty_listing_is_an_empty_set": (MGR, '        if not listing:\n            raise ValueError("juniper-data listed no generators, so no parameter schema says which accept allow_truncation")\n', ""),
    # -- item 6: the auto-start listing client ---------------------------------------------------
    "M22_autostart_listing_drops_api_key": (APP, "truncatable_generators=_TRUNCATABLE_GENERATORS.reader(JuniperDataClient, source=data_url, api_key=api_key),", "truncatable_generators=_TRUNCATABLE_GENERATORS.reader(JuniperDataClient, source=data_url, api_key=None),"),
    "M23_autostart_listing_hardcoded_url": (APP, "truncatable_generators=_TRUNCATABLE_GENERATORS.reader(JuniperDataClient, source=data_url, api_key=api_key),", 'truncatable_generators=_TRUNCATABLE_GENERATORS.reader(JuniperDataClient, source="http://localhost:8100", api_key=api_key),'),
    "I6a_listing_timeout_30": (MGR, "_GENERATOR_LIST_TIMEOUT_SECONDS = 5\n", "_GENERATOR_LIST_TIMEOUT_SECONDS = 30\n"),
    "I6b_listing_retries_3": (MGR, "_GENERATOR_LIST_RETRIES = 0\n", "_GENERATOR_LIST_RETRIES = 3\n"),
    # -- item 7: each path's own retry -------------------------------------------------------------
    "I7a_autostart_names_no_path": (APP, ", fetch_path=_FETCH_PATH_AUTO_START)", ")"),
    "I7b_staged_start_names_the_swap": (MGR, "                self._reload_dataset(fetch_path=_FETCH_PATH_STAGED_START, **self._pending_dataset_config)\n", "                self._reload_dataset(fetch_path=_FETCH_PATH_LIVE_SWAP, **self._pending_dataset_config)\n"),
    "I7c_swap_names_the_staged_start": (MGR, "                self._reload_dataset(fetch_path=_FETCH_PATH_LIVE_SWAP, **cfg)\n", "                self._reload_dataset(fetch_path=_FETCH_PATH_STAGED_START, **cfg)\n"),
    "I7d_reload_drops_the_path": (MGR, "deployment_flag_on=allow_truncated, fetch_path=fetch_path)) from exc", "deployment_flag_on=allow_truncated, fetch_path=None)) from exc"),
    "I7e_retry_table_ignored": (MGR, '            retry = TrainingLifecycleManager._WITHHELD_RETRY_BY_PATH.get(fetch_path or "")\n', "            retry = None\n"),
    "I7f_every_path_listed_again": (MGR, '            retry = TrainingLifecycleManager._WITHHELD_RETRY_BY_PATH.get(fetch_path or "")\n', '            retry = " ".join(TrainingLifecycleManager._WITHHELD_RETRY_BY_PATH.values())\n'),
    # -- item 8: log once the data is bound -------------------------------------------------------
    "I8a_reload_logs_before_conversion": (MGR, '        meta = result.get("meta") or {}\n        # ...AND ON THE RUN', '        meta = result.get("meta") or {}\n        self._log_dataset_shortfall(meta, acceptance_source=acceptance_source)\n        # ...AND ON THE RUN'),
    "I8b_autostart_logs_before_conversion": (APP, '        meta = result.get("meta") or {}\n', '        meta = result.get("meta") or {}\n        lifecycle._log_dataset_shortfall(meta, acceptance_source=acceptance_source)\n'),
    "I8c_start_never_logs_a_callers_annotation": (MGR, '                self._log_bound_dataset_shortfall(dataset_shortfall, acceptance_source=dataset_shortfall.get("acceptance_source"))\n', "                pass\n"),
    "I8d_a_log_failure_undoes_the_load": (MGR, "        try:\n            self._log_dataset_shortfall(meta, acceptance_source=acceptance_source)\n        except Exception:\n", "        self._log_dataset_shortfall(meta, acceptance_source=acceptance_source)\n        if False:\n"),
    "I8e_reload_never_logs": (MGR, '        self._log_bound_dataset_shortfall(meta, acceptance_source=acceptance_source)\n        self.logger.info("Reloaded dataset', '        self.logger.info("Reloaded dataset'),
}


def _env() -> Dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in ("SENTRY_SDK_DSN", "JUNIPER_CASCOR_LOG_DIR", "JUNIPER_CASCOR_SENTRY_DSN")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _pytest(tree: str) -> Tuple[str, List[str]]:
    """Run the named files in ``tree``; return (pytest's summary line, sorted failing node ids)."""
    for dirpath, dirnames, _files in os.walk(os.path.join(tree, "src")):
        for d in dirnames:
            if d == "__pycache__":
                shutil.rmtree(os.path.join(dirpath, d), ignore_errors=True)
    proc = subprocess.run([PY, "-m", "pytest", *NAMED, "-p", "no:cacheprovider", "-rfE"], cwd=os.path.join(tree, "src"), env=_env(), capture_output=True, text=True, timeout=3000)  # nosec B603
    out = proc.stdout + proc.stderr
    summary = [ln.strip() for ln in out.splitlines() if re.search(r"\d+ (passed|failed|error)", ln)]
    failed = sorted({ln.split(" ", 1)[1].split(" - ")[0] for ln in out.splitlines() if ln.startswith(("FAILED ", "ERROR "))})
    return (summary[-1] if summary else "?? no pytest summary -- read the raw output"), failed


def main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    base_dir: Optional[str] = None
    if "--base-dir" in argv:
        i = argv.index("--base-dir")
        base_dir = argv[i + 1]
        argv = argv[:i] + argv[i + 2 :]
    if len(argv) < 2:
        print(__doc__)
        return 2
    src_tree, scratch = argv[0], argv[1]
    only = argv[2:]
    tree = os.path.join(scratch, "tree")
    shutil.rmtree(tree, ignore_errors=True)
    shutil.copytree(src_tree, tree, symlinks=True, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", "reports", ".pytest_cache"))

    summary, failed = _pytest(tree)
    print(f"CONTROL (no mutation): {summary}")
    if failed or "failed" in summary or "?" in summary:
        print("CONTROL IS NOT GREEN -- no KILLED verdict below would mean anything. Stopping.")
        for f in failed:
            print(f"    {f}")
        return 2

    plan: List[Tuple[str, List[Tuple[str, str]]]] = []
    for name, (rel, old, new) in MUTANTS.items():
        if only and name not in only:
            continue
        plan.append((name, [(rel, "anchor", old, new)]))  # type: ignore[list-item]
    if base_dir and (not only or "BASE_0e016a7" in only):
        plan.append(("BASE_0e016a7", [(MGR, "file", os.path.join(base_dir, "manager.py"), ""), (APP, "file", os.path.join(base_dir, "app.py"), "")]))  # type: ignore[list-item]

    killed = survived = skipped = 0
    for name, edits in plan:
        originals: Dict[str, str] = {}
        ok = True
        for rel, kind, old, new in edits:  # type: ignore[misc]
            path = os.path.join(tree, rel)
            with open(path, encoding="utf-8") as f:
                text = f.read()
                # text = open(path, encoding="utf-8").read()

            originals[path] = text
            if kind == "file":
                # open(path, "w", encoding="utf-8").write(open(old, encoding="utf-8").read())
                with open(path, "w", encoding="utf-8") as f_out:
                    with open(old, encoding="utf-8") as f_in:
                        text = f_in.read()
                    f_out.write(text)
                continue
            count = text.count(old)
            if count != 1:
                print(f"{name}: SKIPPED -- anchor occurs {count} times in {rel}")
                ok = False
                break
            # open(path, "w", encoding="utf-8").write(text.replace(old, new))
            with open(path, "w", encoding="utf-8") as f_out:
                f_out.write(text.replace(old, new))
        if ok:
            summary, failed = _pytest(tree)
            verdict = "KILLED" if failed else "SURVIVED"
            killed += verdict == "KILLED"
            survived += verdict == "SURVIVED"
            print(f"{name}: {verdict} | {summary}")
            for f in failed:
                print(f"    {f}")
        else:
            skipped += 1
        for path, text in originals.items():
            open(path, "w", encoding="utf-8").write(text)
    print(f"\nTOTAL: {killed} killed, {survived} survived, {skipped} skipped, of {len(plan)}")
    return 1 if survived or skipped else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
