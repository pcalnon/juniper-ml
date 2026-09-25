#!/usr/bin/env python
"""Mutation-check the fix-forward of juniper-cascor#688's validation on a SCRATCH copy of its worktree.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- investigation
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-cascor#688 (merged 7f4a72132572) and its independent validation, whose mutants NV1-NV5
         this round must kill; the two earlier rounds' harnesses, kept as provenance of theirs --
         util/ad-hoc/2026-09-24_cascor678_followup_mutation_check.py (round 1, #686) and
         util/ad-hoc/2026-09-24_cascor686_fixup_mutation_check.py (round 2, #686's fixup and #688).

usage: 2026-09-24_cascor688_fixforward_mutation_check.py <cascor-worktree> <scratch-dir> [MUTANT ...] [--base-dir DIR] [--base-label LABEL]

Same contract as the earlier rounds: the worktree is copied ONCE to <scratch-dir>/tree and never
mutated in place; every edit of a mutant is an exact replacement whose anchor must occur exactly
once (else the mutant is SKIPPED, never silently run as a no-op); files are restored after every
run; an unmutated CONTROL run comes first and must be green. ``--base-dir`` holds ``manager.py``
and ``app.py`` as they are on origin/main (7f4a721, #688 merged); the pseudo-mutant named by
``--base-label`` swaps both in, which asks "do the new tests fail against the code they fix".

This round: round 2's mutants, re-anchored where the fix-forward moved their anchor (the refusal
predicate, the deferral branch, the as_fetch log line), plus

* the validation's NV1, NV2, NV3 and NV5, VERBATIM. NV4 dropped the ``incomplete_rows`` arm of the
  old field-name predicate, which no longer exists: its anchor would be SKIPPED, so it is carried
  as the two clauses of the new check, each dropped (``P1b`` / ``P1c``);
* the predicate family (``P1*``): the fix's own regressions and each clause's removal;
* the blank-string deferral (``B*``), the log placement (``L*``) and #687's wording (``W*``);
* ``A1``, the opted-in clause of the plain-failure test, which the old stand-in text made vacuous.
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
NAMED = [
    "tests/unit/api/test_allow_truncated_datasets.py",
    "tests/unit/api/test_auto_start_shortfall.py",
    "tests/unit/api/test_shortfall_lifecycle.py",
    "tests/unit/api/test_truncatable_generators.py",
    "tests/unit/api/test_start_fresh_carries_params.py",
    "tests/unit/api/test_start_refuses_wider_staged_dataset.py",
]

Edit = Tuple[str, str, str]
BIND_CALL = "            self._bind_start_tensors_locked(X, y, X_val, y_val, X_test, y_test, dataset_config=dataset_config, dataset_shortfall=dataset_shortfall, as_fetch=as_fetch)\n"
STAGED_RELOAD_CALL = "                self._reload_dataset(fetch_path=_FETCH_PATH_STAGED_START, refuse_wider_than=self._continued_network_dims_locked(start_fresh), **self._pending_dataset_config)\n"
STAGED_RELOAD = STAGED_RELOAD_CALL + "                self._pending_dataset_config = None\n"
PENDING_BLOCK = "            if self._pending_dataset_config:\n" + STAGED_RELOAD
START_FRESH_LOG = '        self.logger.info("start_fresh: discarded model + cleared retained metrics/history (snapshots on disk preserved)")\n'
RELOAD_DESCRIBED = '        self._described_partitions = frozenset(name for name, tensor in (("train", new_train_x), ("val", new_val_x), ("test", new_test_x)) if tensor is not None)\n'
F1_CHECK = "        if refuse_wider_than is not None:\n"
RELOAD_LOG = '        self._log_bound_dataset_shortfall(meta, acceptance_source=acceptance_source)\n        self.logger.info("Reloaded dataset'
AS_FETCH_SF = "            self._dataset_shortfall = dataset_shortfall\n            self._described_partitions = filled if"
LEFT_BRANCH = "        if left:\n            self._described_partitions = left\n            return\n"
PREDICATE = '        looks_like_shortfall = _PRODUCER_REFUSAL_REMEDY in detail and getattr(exc, "status_code", None) in (None, _PRODUCER_REFUSAL_STATUS)\n'
PLAIN_TEST = "        if not looks_like_shortfall or allow_truncated or opt_in_skipped == _OPT_IN_SKIPPED_NOT_TRUNCATABLE:\n"
DEFERRAL = '        elif "allow_truncation" in params and params["allow_truncation"] is None:\n'
FETCH_LOG_IF = "            if dataset_shortfall is not None and self._dataset_shortfall is dataset_shortfall:\n"
FETCH_LOG_CALL = '                self._log_bound_dataset_shortfall(dataset_shortfall, acceptance_source=dataset_shortfall.get("acceptance_source"))\n'
FETCH_LOG = FETCH_LOG_IF + FETCH_LOG_CALL
AS_FETCH_RETURN = "            # turn and the annotation is still the one bound (#688's validation).\n            return\n"
NEW_WORDING = "The staged dataset was not loaded: it is still staged, and the current network and its results are unchanged."
OLD_WORDING = "Nothing was loaded: the dataset is still staged, and the current network and its results are unchanged."

MUTANTS: Dict[str, List[Edit]] = {
    # -- the validation's own mutants (NV4 re-anchored as P1b / P1c, below) -------------------------
    "NV1_described_set_before_the_F1_refusal": [(MGR, RELOAD_DESCRIBED, ""), (MGR, F1_CHECK, RELOAD_DESCRIBED + F1_CHECK)],
    "NV2_shortfall_logged_before_the_F1_refusal": [(MGR, RELOAD_LOG, '        self.logger.info("Reloaded dataset'), (MGR, F1_CHECK, "        self._log_bound_dataset_shortfall(meta, acceptance_source=acceptance_source)\n" + F1_CHECK)],
    "NV3_clean_as_fetch_keeps_the_old_annotation": [(MGR, AS_FETCH_SF, "            if dataset_shortfall is not None:\n                self._dataset_shortfall = dataset_shortfall\n            self._described_partitions = filled if")],
    "NV5_named_inline_adopts_config_while_splits_left": [(MGR, LEFT_BRANCH, '        if left:\n            self._described_partitions = left\n            if dataset_config and "train" in bound:\n                self._current_dataset_config = dict(dataset_config)\n            return\n')],
    # -- item 1: the refusal predicate ----------------------------------------------------------------
    "P1a_field_names_again_the_688_predicate": [(MGR, PREDICATE, '        looks_like_shortfall = "allow_truncation" in detail or "incomplete_rows" in detail\n')],
    "P1b_NV4_status_clause_dropped": [(MGR, PREDICATE, "        looks_like_shortfall = _PRODUCER_REFUSAL_REMEDY in detail\n")],
    "P1c_NV4_remedy_clause_dropped": [(MGR, PREDICATE, '        looks_like_shortfall = getattr(exc, "status_code", None) in (None, _PRODUCER_REFUSAL_STATUS)\n')],
    "P1d_status_required_older_clients_lost": [(MGR, PREDICATE, '        looks_like_shortfall = _PRODUCER_REFUSAL_REMEDY in detail and getattr(exc, "status_code", None) == _PRODUCER_REFUSAL_STATUS\n')],
    "P1e_bare_422_again_the_678_predicate": [(MGR, PREDICATE, '        looks_like_shortfall = "422" in detail or "allow_truncation" in detail or "incomplete_rows" in detail\n')],
    "P1f_remedy_shortened_to_the_field_name": [(MGR, '_PRODUCER_REFUSAL_REMEDY = "Re-submit with allow_truncation=true"\n', '_PRODUCER_REFUSAL_REMEDY = "allow_truncation"\n')],
    "P1g_status_constant_wrong": [(MGR, "_PRODUCER_REFUSAL_STATUS = 422\n", "_PRODUCER_REFUSAL_STATUS = 400\n")],
    "A1_opted_in_clause_dropped": [(MGR, PLAIN_TEST, "        if not looks_like_shortfall or opt_in_skipped == _OPT_IN_SKIPPED_NOT_TRUNCATABLE:\n")],
    # -- item 1: a blank string is not a deferral ------------------------------------------------------
    "B1a_blank_is_a_deferral_again": [(MGR, DEFERRAL, '        elif "allow_truncation" in params and caller_stance is None:\n')],
    "B1b_deferral_ignores_the_keys_presence": [(MGR, DEFERRAL, '        elif params.get("allow_truncation") is None:\n')],
    "B1c_any_present_key_is_a_deferral": [(MGR, DEFERRAL, '        elif "allow_truncation" in params:\n')],
    # -- item 3: the as_fetch shortfall is logged once the staged fetch has had its turn -------------
    "L3a_fetch_handed_in_never_logged": [(MGR, FETCH_LOG, FETCH_LOG_IF + "                pass\n")],
    "L3b_logged_whether_or_not_the_staged_fetch_replaced_it": [(MGR, FETCH_LOG_IF, "            if dataset_shortfall is not None:\n")],
    "L3c_logged_as_it_is_bound_the_688_placement": [(MGR, FETCH_LOG, ""), (MGR, AS_FETCH_RETURN, AS_FETCH_RETURN.replace("            return\n", "            if dataset_shortfall is not None:\n" + FETCH_LOG_CALL + "            return\n"))],
    "L3d_logged_before_the_staged_reload": [(MGR, FETCH_LOG, ""), (MGR, PENDING_BLOCK, FETCH_LOG + PENDING_BLOCK)],
    # -- item 4: #687's refusal says only the STAGED dataset was not loaded --------------------------
    "W4a_nothing_was_loaded_again": [(MGR, NEW_WORDING, OLD_WORDING)],
    # -- round 2's mutants, re-anchored where this change moved them ----------------------------------
    "NM1_described_from_artifact_keys": [(MGR, RELOAD_DESCRIBED, '        self._described_partitions = frozenset(name for name, key in (("train", "X_train"), ("val", "X_val"), ("test", "X_test")) if key in arrays)\n')],
    "NM11_bind_after_the_staged_reload": [(MGR, BIND_CALL, ""), (MGR, STAGED_RELOAD, STAGED_RELOAD + BIND_CALL)],
    "NM19_start_fresh_forgets_partitions": [(MGR, START_FRESH_LOG, "        self._described_partitions = frozenset()\n" + START_FRESH_LOG)],
    "NM20_start_fresh_clears_record": [(MGR, START_FRESH_LOG, "        self._current_dataset_config = None\n        self._dataset_shortfall = None\n        self._described_partitions = frozenset()\n" + START_FRESH_LOG)],
    "NM4_ported_fetch_keeps_what_it_did_not_supply": [(MGR, "            self._val_x, self._val_y = X_val, y_val\n            self._test_x, self._test_y = X_test, y_test\n", "            if X_val is not None:\n                self._val_x, self._val_y = X_val, y_val\n            if X_test is not None:\n                self._test_x, self._test_y = X_test, y_test\n")],
    "F2a_fetch_bound_as_inline": [(MGR, "        if as_fetch:\n            self._train_x, self._train_y = X, y\n", "        if False:\n            self._train_x, self._train_y = X, y\n")],
    "F2b_annotation_on_inline_tensors_accepted": [(MGR, "        if dataset_shortfall is not None and not as_fetch:\n", "        if False:\n")],
    "F2c_fetch_without_X_accepted": [(MGR, "        if as_fetch and X is None:\n", "        if False:\n")],
    "F2d_autostart_forgets_as_fetch": [(APP, "            as_fetch=True,\n", "")],
    "F2e_fetch_record_ignores_config": [(MGR, "            self._described_partitions = filled if (self._current_dataset_config or dataset_shortfall is not None) else frozenset()\n", "            self._described_partitions = filled if dataset_shortfall is not None else frozenset()\n")],
    "I1a_record_never_kept_while_splits_left": [(MGR, LEFT_BRANCH, "        if False:\n            self._described_partitions = left\n            return\n")],
    "I1b_fetch_records_no_partitions": [(MGR, RELOAD_DESCRIBED, "        self._described_partitions = frozenset()\n")],
    "I1c_fetch_leaves_partitions_stale": [(MGR, RELOAD_DESCRIBED, "")],
    "I1d_val_test_only_start_keeps_record": [(MGR, '        self._current_dataset_config = dict(dataset_config) if dataset_config and "train" in bound else None\n', '        if "train" not in bound:\n            return\n        self._current_dataset_config = dict(dataset_config) if dataset_config else None\n')],
    "I1e_filled_counts_train_only": [(MGR, '        filled = frozenset(name for name, tensor in (("train", X), ("val", X_val), ("test", X_test)) if tensor is not None)\n', '        filled = frozenset({"train"}) if X is not None else frozenset()\n')],
    "I1f_inline_record_describes_nothing": [(MGR, "        self._described_partitions = bound if self._current_dataset_config else frozenset()\n", "        self._described_partitions = frozenset()\n")],
    "I1h_preswap_snapshot_omits_partitions": [(MGR, "                    described_partitions=self._described_partitions,\n", "")],
    "I1i_rollback_keeps_swap_fetch_partitions": [(MGR, "        self._described_partitions = pre.described_partitions\n", "")],
    "I1j_reset_clears_partitions": [(MGR, "        # same reason ``_described_partitions`` is left alone: every partition\n", "        self._described_partitions = frozenset()\n        # same reason ``_described_partitions`` is left alone: every partition\n")],
    "I2a_withheld_remedy_opens_with_retry": [(MGR, '            remedy = "To accept it, send allow_truncation=true on the dataset request itself, plus incomplete_rows=accept or incomplete_rows=drop -- or retry once juniper-data answers GET /v1/generators:', '            remedy = "Retry once juniper-data answers GET /v1/generators:')],
    "I2b_deferred_remedy_without_the_phrase": [(MGR, '            remedy = "To accept it, send allow_truncation=true on the dataset request itself, plus incomplete_rows=accept or incomplete_rows=drop -- this service', '            remedy = "Send allow_truncation=true on the dataset request itself, plus incomplete_rows=accept or incomplete_rows=drop -- this service')],
    "I2c_new_branch_nobody_listed": [(MGR, "        elif deployment_flag_on:\n            stance = ", '        elif opt_in_skipped == "unlisted":\n            stance = "and a branch nobody listed"\n            remedy = "To accept it, do something."\n        elif deployment_flag_on:\n            stance = ')],
    "M21_null_counts_as_silent": [(MGR, '        if allow_truncated and "allow_truncation" not in params:\n            truncatable = truncatable_generators()\n', '        if allow_truncated and params.get("allow_truncation") is None:\n            truncatable = truncatable_generators()\n')],
    "I3a_resolver_forgets_the_deferral": [(MGR, DEFERRAL, "        elif False:\n")],
    "I3b_describer_ignores_the_deferral": [(MGR, "        elif opt_in_skipped == _OPT_IN_SKIPPED_CALLER_DEFERRED:\n", "        elif False:\n")],
    "I4a_undeclared_generator_is_a_refusal_again": [(MGR, PLAIN_TEST, "        if not looks_like_shortfall or allow_truncated:\n")],
    "I5a_schemaless_entry_skipped": [(MGR, "                raise ValueError(f\"generator {entry['name']!r} carries no parameter schema, so whether it accepts allow_truncation is unknown\")\n", "                continue\n")],
    "I5b_empty_listing_is_an_empty_set": [(MGR, '        if not listing:\n            raise ValueError("juniper-data listed no generators, so no parameter schema says which accept allow_truncation")\n', "")],
    "M22_autostart_listing_drops_api_key": [(APP, "truncatable_generators=_TRUNCATABLE_GENERATORS.reader(JuniperDataClient, source=data_url, api_key=api_key),", "truncatable_generators=_TRUNCATABLE_GENERATORS.reader(JuniperDataClient, source=data_url, api_key=None),")],
    "M23_autostart_listing_hardcoded_url": [(APP, "truncatable_generators=_TRUNCATABLE_GENERATORS.reader(JuniperDataClient, source=data_url, api_key=api_key),", 'truncatable_generators=_TRUNCATABLE_GENERATORS.reader(JuniperDataClient, source="http://localhost:8100", api_key=api_key),')],
    "I6a_listing_timeout_30": [(MGR, "_GENERATOR_LIST_TIMEOUT_SECONDS = 5\n", "_GENERATOR_LIST_TIMEOUT_SECONDS = 30\n")],
    "I6b_listing_retries_3": [(MGR, "_GENERATOR_LIST_RETRIES = 0\n", "_GENERATOR_LIST_RETRIES = 3\n")],
    "I7a_autostart_names_no_path": [(APP, ", fetch_path=_FETCH_PATH_AUTO_START)", ")")],
    "I7b_staged_start_names_the_swap": [(MGR, STAGED_RELOAD_CALL, STAGED_RELOAD_CALL.replace("_FETCH_PATH_STAGED_START", "_FETCH_PATH_LIVE_SWAP"))],
    "R1_resolution_drops_refuse_wider_than": [(MGR, STAGED_RELOAD_CALL, "                self._reload_dataset(fetch_path=_FETCH_PATH_STAGED_START, **self._pending_dataset_config)\n")],
    "R2_resolution_drops_fetch_path": [(MGR, STAGED_RELOAD_CALL, "                self._reload_dataset(refuse_wider_than=self._continued_network_dims_locked(start_fresh), **self._pending_dataset_config)\n")],
    "I7c_swap_names_the_staged_start": [(MGR, "                self._reload_dataset(fetch_path=_FETCH_PATH_LIVE_SWAP, **cfg)\n", "                self._reload_dataset(fetch_path=_FETCH_PATH_STAGED_START, **cfg)\n")],
    "I7d_reload_drops_the_path": [(MGR, "deployment_flag_on=allow_truncated, fetch_path=fetch_path)) from exc", "deployment_flag_on=allow_truncated, fetch_path=None)) from exc")],
    "I7e_retry_table_ignored": [(MGR, '            retry = TrainingLifecycleManager._WITHHELD_RETRY_BY_PATH.get(fetch_path or "")\n', "            retry = None\n")],
    "I7f_every_path_listed_again": [(MGR, '            retry = TrainingLifecycleManager._WITHHELD_RETRY_BY_PATH.get(fetch_path or "")\n', '            retry = " ".join(TrainingLifecycleManager._WITHHELD_RETRY_BY_PATH.values())\n')],
    "I8a_reload_logs_before_conversion": [(MGR, '        meta = result.get("meta") or {}\n        # ...AND ON THE RUN', '        meta = result.get("meta") or {}\n        self._log_dataset_shortfall(meta, acceptance_source=acceptance_source)\n        # ...AND ON THE RUN')],
    "I8b_autostart_logs_before_conversion": [(APP, '        meta = result.get("meta") or {}\n', '        meta = result.get("meta") or {}\n        lifecycle._log_dataset_shortfall(meta, acceptance_source=acceptance_source)\n')],
    "I8d_a_log_failure_undoes_the_load": [(MGR, "        try:\n            self._log_dataset_shortfall(meta, acceptance_source=acceptance_source)\n        except Exception:\n", "        self._log_dataset_shortfall(meta, acceptance_source=acceptance_source)\n        if False:\n")],
    "I8e_reload_never_logs": [(MGR, RELOAD_LOG, '        self.logger.info("Reloaded dataset')],
}


def _env() -> Dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in ("SENTRY_SDK_DSN", "JUNIPER_CASCOR_LOG_DIR", "JUNIPER_CASCOR_SENTRY_DSN", "SENTRY_DSN")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _pytest(tree: str) -> Tuple[str, List[str]]:
    """Run the named files in ``tree``; return (pytest's summary line, sorted failing node ids)."""
    for dirpath, dirnames, _files in os.walk(os.path.join(tree, "src")):
        for d in list(dirnames):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(dirpath, d), ignore_errors=True)
    proc = subprocess.run([PY, "-m", "pytest", *NAMED, "-p", "no:cacheprovider", "-rfE"], cwd=os.path.join(tree, "src"), env=_env(), capture_output=True, text=True, timeout=3000)  # nosec B603
    out = proc.stdout + proc.stderr
    summary = [ln.strip() for ln in out.splitlines() if re.search(r"\d+ (passed|failed|error)", ln)]
    failed = sorted({ln.split(" ", 1)[1].split(" - ")[0] for ln in out.splitlines() if ln.startswith(("FAILED ", "ERROR "))})
    nameerrors = sum(1 for ln in out.splitlines() if "NameError" in ln)
    head = summary[-1] if summary else "?? no pytest summary -- read the raw output"
    return (f"{head} [NameError lines: {nameerrors}]" if nameerrors else head), failed


def main(argv: List[str]) -> int:
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return 0 if argv else 2
    base_dir: Optional[str] = None
    base_label = "BASE_origin_main_7f4a721"
    if "--base-dir" in argv:
        i = argv.index("--base-dir")
        base_dir = argv[i + 1]
        argv = argv[:i] + argv[i + 2 :]
    if "--base-label" in argv:
        i = argv.index("--base-label")
        base_label = argv[i + 1]
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
    print(f"CONTROL (no mutation): {summary}", flush=True)
    if failed or "failed" in summary or "?" in summary:
        print("CONTROL IS NOT GREEN -- no KILLED verdict below would mean anything. Stopping.")
        for f in failed:
            print(f"    {f}")
        return 2

    plan: List[Tuple[str, List[Tuple[str, str, str, str]]]] = []
    for name, edits in MUTANTS.items():
        if only and name not in only:
            continue
        plan.append((name, [(rel, "anchor", old, new) for rel, old, new in edits]))
    if base_dir and (not only or base_label in only):
        plan.append((base_label, [(MGR, "file", os.path.join(base_dir, "manager.py"), ""), (APP, "file", os.path.join(base_dir, "app.py"), "")]))

    killed = survived = skipped = 0
    for name, edits in plan:
        originals: Dict[str, str] = {}
        ok = True
        for rel, kind, old, new in edits:
            path = os.path.join(tree, rel)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
            originals.setdefault(path, text)
            if kind == "file":
                with open(old, encoding="utf-8") as src, open(path, "w", encoding="utf-8") as dst:
                    dst.write(src.read())
                continue
            count = text.count(old)
            if count != 1:
                print(f"{name}: SKIPPED -- anchor occurs {count} times in {rel}", flush=True)
                ok = False
                break
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text.replace(old, new))
        if ok:
            summary, failed = _pytest(tree)
            verdict = "KILLED" if failed else "SURVIVED"
            killed += verdict == "KILLED"
            survived += verdict == "SURVIVED"
            print(f"{name}: {verdict} | {summary}", flush=True)
            for f in failed:
                print(f"    {f}", flush=True)
        else:
            skipped += 1
        for path, text in originals.items():
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(text)
    shutil.rmtree(tree, ignore_errors=True)
    print(f"\nTOTAL: {killed} killed, {survived} survived, {skipped} skipped, of {len(plan)}", flush=True)
    return 1 if survived or skipped else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
