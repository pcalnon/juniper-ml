"""Mutation runner for the PR-678 validation (scratch copy only; restores every file it touches).

Usage: python mutate.py <mutation-id> [<mutation-id> ...]
Each mutation replaces exactly one occurrence of `old` with `new` in `path`, runs the
named test files, prints which tests FAILED, then restores the file byte-for-byte.
"""

import os
import re
import subprocess
import sys

S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v678"
ROOT = S + "/cascor"
MGR = "src/api/lifecycle/manager.py"
TESTS = [
    "src/tests/unit/api/test_shortfall_lifecycle.py",
    "src/tests/unit/api/test_auto_start_shortfall.py",
    "src/tests/unit/api/test_truncatable_generators.py",
    "src/tests/unit/api/test_allow_truncated_datasets.py",
    "src/tests/unit/api/test_status_current_dataset.py",
    "src/tests/unit/api/test_lifecycle_manager_swap.py",
    "src/tests/unit/api/test_c5_retention_reset.py",
]

MUTATIONS = {
    # X-B: the inline binding of the annotation is dropped (pre-fix shape on the inline path)
    "B1_no_inline_bind": (MGR, "                self._dataset_shortfall = dataset_shortfall\n", ""),
    # X-B: the swap rollback no longer restores the annotation
    "B2_no_swap_rollback": (MGR, "        self._dataset_shortfall = pre.dataset_shortfall\n", ""),
    # X-B: a refused staged fetch no longer restores the annotation
    "B3_no_staged_restore": (MGR, "            self._dataset_shortfall = prior_shortfall\n", "            pass\n"),
    # X-B: reset clears the annotation (the rejected first-cut behaviour)
    "B4_reset_clears": (MGR, "        self.monitor.clear_metrics()\n        # APD-CASCOR-013: reset does NOT clear", "        self.monitor.clear_metrics()\n        self._dataset_shortfall = None\n        # APD-CASCOR-013: reset does NOT clear"),
    # X-A: memo ignores the URL
    "A1_url_blind_memo": (MGR, "            cached = self._by_source.get(source)\n", "            cached = self._by_source.get('k')\n"),
    "A1b_url_blind_memo_set": (MGR, "            self._by_source[source] = derived\n", "            self._by_source['k'] = derived\n"),
    # X-A: a failure is memoised as an empty set
    "A2_memoise_failure": (MGR, "            return None\n        with self._lock:\n            self._by_source[source] = derived", "            with self._lock:\n                self._by_source[source] = frozenset()\n            return None\n        with self._lock:\n            self._by_source[source] = derived"),
    # X-A: the withheld remedy branch is dropped
    "A3_no_withheld_remedy": (MGR, "        elif opt_in_withheld:\n", "        elif False:\n"),
    # X-A: eager read -- the list is read on every resolution
    "A4_eager_read": (MGR, "        opt_in_withheld = False\n        if allow_truncated and \"allow_truncation\" not in params:\n            truncatable = truncatable_generators()\n", "        opt_in_withheld = False\n        _eager = truncatable_generators()\n        if allow_truncated and \"allow_truncation\" not in params:\n            truncatable = _eager\n"),
    # X-A: the listing uses the DEFAULT client (30 s x 3 retries)
    "A5_default_client": (MGR, "return client_class(base_url=source, api_key=api_key, timeout=_GENERATOR_LIST_TIMEOUT_SECONDS, retries=_GENERATOR_LIST_RETRIES)", "return client_class(base_url=source, api_key=api_key)"),
    # X-A: an unknown set is treated as "everything is truncatable" (guess toward accepting)
    "A6_unknown_means_all": (MGR, "            if truncatable is None:\n", "            if truncatable is None and False:\n"),
    # X-A: an unknown set drops the caller's own value (override instead of default)
    "A7_withheld_drops_caller": (MGR, "        caller_stance = TrainingLifecycleManager._as_bool_stance(params.get(\"allow_truncation\"))\n        opt_in_withheld = False\n", "        caller_stance = TrainingLifecycleManager._as_bool_stance(params.get(\"allow_truncation\"))\n        opt_in_withheld = False\n        if allow_truncated and truncatable_generators() is None:\n            params = {k: v for k, v in params.items() if k != \"allow_truncation\"}\n"),
    # X-A: derive ignores inheritance-free schemas? (predicate keyed on 'required' instead of 'properties')
    "A8_predicate_required": (MGR, "            properties = schema.get(\"properties\") if isinstance(schema, dict) else None\n", "            properties = {k: 1 for k in (schema.get(\"required\") or [])} if isinstance(schema, dict) else None\n"),
    # X-B: auto-start writes the annotation onto the manager instead of handing it to the start
    "B5_autostart_not_handed": ("src/api/app.py", "            dataset_shortfall=dataset_shortfall,\n        )", "        )"),
}


def run(mid: str) -> None:
    path, old, new = MUTATIONS[mid]
    full = os.path.join(ROOT, path)
    with open(full, encoding="utf-8") as fh:
        original = fh.read()
    count = original.count(old)
    if count != 1:
        print(f"[{mid}] SKIPPED: anchor occurs {count} times")
        return
    try:
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(original.replace(old, new, 1))
        env = dict(os.environ)
        for k in ("SENTRY_SDK_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "SENTRY_DSN"):
            env.pop(k, None)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        proc = subprocess.run(
            ["/opt/miniforge3/envs/JuniperCascor1/bin/python", "-m", "pytest", "-p", "no:cacheprovider", "-rf", *TESTS],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=900,
        )
        failed = sorted(set(re.findall(r"^FAILED (\S+)", proc.stdout, re.MULTILINE)))
        summary = [ln for ln in proc.stdout.splitlines() if re.search(r"\d+ (passed|failed)", ln)]
        print(f"[{mid}] {summary[-1] if summary else '(no summary)'}")
        for f in failed:
            print(f"    FAILED {f.split('::', 1)[1] if '::' in f else f}")
    finally:
        with open(full, "w", encoding="utf-8") as fh:
            fh.write(original)
        with open(full, encoding="utf-8") as fh:
            assert fh.read() == original, "restore failed"


if __name__ == "__main__":
    for m in sys.argv[1:]:
        run(m)
