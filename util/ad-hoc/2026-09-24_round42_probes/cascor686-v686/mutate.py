"""Mutation check for cascor#678 (scratch only). usage: mutate.py <merged-root> <out-dir> [names...] [--full]"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys

MERGED, OUT = sys.argv[1], sys.argv[2]
FULL = "--full" in sys.argv
ONLY = [a for a in sys.argv[3:] if not a.startswith("--")]
MGR, APP = "src/api/lifecycle/manager.py", "src/api/app.py"

MUTANTS = {
    "M1_memoise_failed_read": (MGR, "            return None\n        with self._lock:\n            self._by_source[source] = derived\n", "            with self._lock:\n                self._by_source[source] = frozenset()\n            return None\n        with self._lock:\n            self._by_source[source] = derived\n"),
    "M2_annotation_before_tensors": (MGR, "        dataset_shortfall = self._build_dataset_shortfall(meta, dataset_id=dataset_id, acceptance_source=acceptance_source)\n", "        dataset_shortfall = self._build_dataset_shortfall(meta, dataset_id=dataset_id, acceptance_source=acceptance_source)\n        self._dataset_shortfall = dataset_shortfall\n"),
    "M2b_annotation_after_convert_before_split": (MGR, "        new_val_x, new_val_y, warning = self._resolve_validation_split(new_val_x, new_val_y, new_test_x, new_test_y)\n        self._val_x = new_val_x\n", "        self._dataset_shortfall = dataset_shortfall\n        new_val_x, new_val_y, warning = self._resolve_validation_split(new_val_x, new_val_y, new_test_x, new_test_y)\n        self._val_x = new_val_x\n"),
    "M3_opt_in_when_unknown": (MGR, "                opt_in_skipped = _OPT_IN_SKIPPED_LIST_UNREADABLE\n", '                params = {**params, "allow_truncation": True}\n'),
    "M4_clear_on_reset": (MGR, "        # APD-CASCOR-013: reset does NOT clear ``_dataset_shortfall``, and that is\n", "        self._dataset_shortfall = None\n        # APD-CASCOR-013: reset does NOT clear ``_dataset_shortfall``, and that is\n"),
    "M5_schemaless_listing_is_empty_set": (MGR, "        if not schemas_seen:\n", "        if False and not schemas_seen:\n"),
    "M6_no_rollback_restore": (MGR, "        self._dataset_shortfall = pre.dataset_shortfall\n", "        pass\n"),
    "M7_inline_keeps_stale": (MGR, "                self._dataset_shortfall = dataset_shortfall\n", "                pass\n"),
    "M8_flag_on_null_names_knob": (MGR, "        elif deployment_flag_on:\n", "        elif False and deployment_flag_on:\n"),
    "M9_memo_not_keyed_by_url": (MGR, "            cached = self._by_source.get(source)\n", "            cached = next(iter(self._by_source.values()), None)\n"),
    "M10_listing_retries_3": (MGR, "_GENERATOR_LIST_RETRIES = 0\n", "_GENERATOR_LIST_RETRIES = 3\n"),
    "M11_eager_fetch": (MGR, '        opt_in_skipped: Optional[str] = None\n        if allow_truncated and "allow_truncation" not in params:\n            truncatable = truncatable_generators()\n', '        opt_in_skipped: Optional[str] = None\n        _eager = truncatable_generators()\n        if allow_truncated and "allow_truncation" not in params:\n            truncatable = _eager\n'),
    "M12_autostart_writes_early": (APP, "        dataset_shortfall = TrainingLifecycleManager._build_dataset_shortfall(meta, dataset_id=dataset_id, acceptance_source=acceptance_source)\n", "        dataset_shortfall = TrainingLifecycleManager._build_dataset_shortfall(meta, dataset_id=dataset_id, acceptance_source=acceptance_source)\n        lifecycle._dataset_shortfall = dataset_shortfall\n"),
    "M13_autostart_drops_annotation": (APP, "            dataset_shortfall=dataset_shortfall,\n", ""),
    "M14_withheld_branch_removed": (MGR, "        elif opt_in_skipped == _OPT_IN_SKIPPED_LIST_UNREADABLE:\n", "        elif False:\n"),
    "M16_preswap_snapshot_omits_annotation": (MGR, "                    dataset_shortfall=self._dataset_shortfall,\n", ""),
    "M17_no_guard_annotation_without_X": (MGR, '            if dataset_shortfall is not None and X is None:\n                raise ValueError("dataset_shortfall annotates caller-supplied tensors; pass it together with X")\n', ""),
    "M18_listing_timeout_30": (MGR, "_GENERATOR_LIST_TIMEOUT_SECONDS = 5\n", "_GENERATOR_LIST_TIMEOUT_SECONDS = 30\n"),
    "M19_describer_ignores_flag_arg_autostart": (APP, "opt_in_skipped=opt_in_skipped, deployment_flag_on=allow_truncated)", "opt_in_skipped=None, deployment_flag_on=False)"),
    "M20_reload_ignores_flag_arg": (MGR, "opt_in_skipped=opt_in_skipped, deployment_flag_on=allow_truncated)) from exc", "opt_in_skipped=None, deployment_flag_on=False)) from exc"),
    "M21_null_counts_as_silent": (MGR, '        if allow_truncated and "allow_truncation" not in params:\n            truncatable = truncatable_generators()\n', '        if allow_truncated and params.get("allow_truncation") is None:\n            truncatable = truncatable_generators()\n'),
    "M22_autostart_listing_drops_api_key": (APP, "truncatable_generators=_TRUNCATABLE_GENERATORS.reader(JuniperDataClient, source=data_url, api_key=api_key),", "truncatable_generators=_TRUNCATABLE_GENERATORS.reader(JuniperDataClient, source=data_url, api_key=None),"),
    "M23_autostart_listing_wrong_url": (APP, "truncatable_generators=_TRUNCATABLE_GENERATORS.reader(JuniperDataClient, source=data_url, api_key=api_key),", 'truncatable_generators=_TRUNCATABLE_GENERATORS.reader(JuniperDataClient, source="http://localhost:8100", api_key=api_key),'),
    "M24_autostart_resolver_not_in_thread": (APP, "await asyncio.to_thread(\n            TrainingLifecycleManager._resolve_truncation_stance,\n            dataset_params,\n", "(lambda f, *a, **k: asyncio.sleep(0, f(*a, **k)))(\n            TrainingLifecycleManager._resolve_truncation_stance,\n            dataset_params,\n"),
    "M25_start_binds_only_non_null": (MGR, "                self._dataset_shortfall = dataset_shortfall\n", "                if dataset_shortfall is not None:\n                    self._dataset_shortfall = dataset_shortfall\n"),
}

NAMED = ["tests/unit/api/test_allow_truncated_datasets.py", "tests/unit/api/test_auto_start_shortfall.py", "tests/unit/api/test_shortfall_lifecycle.py", "tests/unit/api/test_truncatable_generators.py"]

env = {k: v for k, v in os.environ.items() if k not in ("SENTRY_SDK_DSN", "JUNIPER_CASCOR_LOG_DIR", "JUNIPER_CASCOR_SENTRY_DSN")}
env["PYTHONDONTWRITEBYTECODE"] = "1"

for name, (rel, old, new) in MUTANTS.items():
    if ONLY and name not in ONLY:
        continue
    dst = os.path.join(OUT, name)
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(MERGED, dst, symlinks=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "reports"))
    path = os.path.join(dst, rel)
    src = open(path, encoding="utf-8").read()
    count = src.count(old)
    if count != 1:
        print(f"{name}: ANCHOR COUNT {count} != 1 -- SKIPPED")
        continue
    open(path, "w", encoding="utf-8").write(src.replace(old, new))
    targets = ["tests/unit/api"] if FULL else NAMED
    if "--integ" in sys.argv:
        targets = ["tests/integration", "--integration"]
    proc = subprocess.run(["/opt/miniforge3/envs/JuniperCascor1/bin/python", "-m", "pytest", *targets, "-p", "no:cacheprovider", "-rfE"], cwd=os.path.join(dst, "src"), env=env, capture_output=True, text=True, timeout=3000)
    out = proc.stdout + proc.stderr
    summary = [ln for ln in out.splitlines() if re.search(r"\d+ (passed|failed)", ln)]
    failed = sorted({ln.split(" ")[1].split(" - ")[0] for ln in out.splitlines() if ln.startswith("FAILED ")})
    print(f"{name}: {'KILLED' if failed else 'SURVIVED'} | {summary[-1].strip() if summary else '?'}")
    for f in failed:
        print(f"    {f}")
    shutil.rmtree(dst, ignore_errors=True)
