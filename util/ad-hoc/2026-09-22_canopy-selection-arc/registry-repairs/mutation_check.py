"""Mutation-check the new/changed guard tests of fix/registry-record-repairs (items 10, 11-adjacent, 12, 14).

For each mutation: hash the file, apply an anchored replacement (the anchor must match EXACTLY
once), run the targeted tests, restore the original bytes in a ``finally``, and verify the restore
by re-hashing. A mutation whose anchor misses is reported as SKIPPED and counts as a harness
failure -- a silently skipped arm is the defect class this arc keeps finding. Scratch only.
"""

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

WT = Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--registry-record-repairs--20260922-2021--26e0546f")
SRC = WT / "src"
PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
REG = SRC / "model_registry.py"
SCHEMA = SRC / "dataset_schema.py"
DM = SRC / "frontend" / "dashboard_manager.py"
CONTRACT = "tests/regression/test_dataset_generator_contract.py"
REGISTRY_TESTS = "tests/unit/test_model_registry.py"

EQUITIES_SEED = '''            "symbols": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"],
            "fundamentals_fill": "drop",
            "normalize_features": True,'''
DATASET_TYPES_END = '''            "fundamentals_fill": "drop",
        },
    ),
)

# Default dataset type'''
TWENTY = ", ".join(f'"T{i:02d}"' for i in range(20))

MUTATIONS = [
    # --- item 12
    ("M12a structured seed added", REG, DATASET_TYPES_END, DATASET_TYPES_END.replace("    ),\n)\n", '    ),\n    DatasetTypeSpec(value="arc_agi", label="ARC-AGI", task_type="structured", ndim=2),\n)\n'), [REGISTRY_TESTS, "-k", "compatible_model or hint_non_none"], ["test_every_seeded_dataset_has_a_compatible_model[arc_agi]", "test_dataset_model_hint_non_none_for_every_seed_dataset"]),
    ("M12b recurrence loses regression", REG, 'supported_task_types=frozenset({"regression"}),\n        family="lmu",', 'supported_task_types=frozenset({"classification"}),\n        family="lmu",', [REGISTRY_TESTS, "-k", "test_every_seeded_dataset_has_a_compatible_model"], ["[multi_sine]", "[equities_seq]"]),
    # --- item 14 (G11)
    ("M11a equities seed loses symbols", REG, EQUITIES_SEED, '''            "fundamentals_fill": "drop",
            "normalize_features": True,''', [CONTRACT, "-k", "TestG11"], ["test_every_unbounded_import_seed_pins_a_bounding_key[equities]"]),
    ("M11b unclassified seed added", REG, DATASET_TYPES_END, DATASET_TYPES_END.replace("    ),\n)\n", '    ),\n    DatasetTypeSpec(value="sine_burst", label="Sine Burst", task_type="regression", ndim=3, temporal="regular"),\n)\n'), [CONTRACT, "-k", "TestG11"], ["test_every_seeded_generator_is_classified[sine_burst]"]),
    ("M11c equities symbols emptied", REG, EQUITIES_SEED, EQUITIES_SEED.replace('["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]', "[]"), [CONTRACT, "-k", "TestG11"], ["test_every_unbounded_import_seed_pins_a_bounding_key[equities]"]),
    ("M11d equities symbols over the ceiling", REG, EQUITIES_SEED, EQUITIES_SEED.replace('["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]', f"[{TWENTY}]"), [CONTRACT, "-k", "TestG11"], ["test_every_unbounded_import_seed_pins_a_bounding_key[equities]"]),
    ("M11e equities reclassified self-bounded", REG, '''    "equities": GeneratorBound(
        "Pulls an operator-sized universe: with no symbols it asks for all 503 bundled constituents, which a default juniper-data deployment refuses (422) against its 14-symbol ceiling.",
        bounding_keys=frozenset({"symbols"}),
    ),''', '''    "equities": GeneratorBound(
        "Pulls an operator-sized universe: with no symbols it asks for all 503 bundled constituents, which a default juniper-data deployment refuses (422) against its 14-symbol ceiling.",
    ),''', [CONTRACT, "-k", "TestG11"], ["test_the_equities_pair_stays_classified_as_unbounded_imports"]),
    ("M11f bounding key with no rule", REG, '''    "equities_seq": GeneratorBound(
        "Pulls an operator-sized universe: with no symbols it asks for all 503 bundled constituents, which a default juniper-data deployment refuses (422) against its 14-symbol ceiling.",
        bounding_keys=frozenset({"symbols"}),''', '''    "equities_seq": GeneratorBound(
        "Pulls an operator-sized universe: with no symbols it asks for all 503 bundled constituents, which a default juniper-data deployment refuses (422) against its 14-symbol ceiling.",
        bounding_keys=frozenset({"tickers"}),''', [CONTRACT, "-k", "TestG11"], ["test_every_bounding_key_has_a_rule"]),
    # --- item 10
    ("M10a seed carries allow_truncation False", REG, EQUITIES_SEED, EQUITIES_SEED + '\n            "allow_truncation": False,', [CONTRACT, "-k", "TestNoPathSendsAPartialDataStance"], ["test_no_seed_carries_a_policy_field[equities]", "test_the_default_apply_sends_neither_field[equities]", "test_the_one_shot_start_body_sends_neither_field[equities]", "test_a_stale_policy_control_is_filtered_and_nothing_else_is"]),
    ("M10b form filter drops the policy set", SCHEMA, "FORM_EXCLUDED_FIELDS: frozenset[str] = INFRASTRUCTURE_FIELDS | PARTIAL_DATA_POLICY_FIELDS", "FORM_EXCLUDED_FIELDS: frozenset[str] = INFRASTRUCTURE_FIELDS", [CONTRACT, "-k", "TestNoPathSendsAPartialDataStance"], ["test_a_stale_policy_control_is_filtered_and_nothing_else_is"]),
    ("M10c restart re-stage sends false", DM, '        payload["nn_dataset_type"] = dtype\n        for key, pkey in (("n_samples", "nn_dataset_elements")', '        payload["nn_dataset_type"] = dtype\n        payload["nn_dataset_params"] = {"allow_truncation": False}\n        for key, pkey in (("n_samples", "nn_dataset_elements")', [CONTRACT, "-k", "TestNoPathSendsAPartialDataStance"], ["test_the_restart_modal_restage_sends_neither_field[spirals]", "test_the_restart_modal_restage_sends_neither_field[equities]"]),
    ("M10d prompt accept sends false", DM, '"dataset-shortfall-accept-button": {"allow_truncation": True, "incomplete_rows": "accept"},', '"dataset-shortfall-accept-button": {"allow_truncation": False, "incomplete_rows": "accept"},', [CONTRACT, "-k", "TestNoPathSendsAPartialDataStance"], ["test_the_shortfall_prompt_only_ever_opts_in"]),
    ("M10e one-shot handler adds false", DM, "        params = dataset_default_params(dataset_generator)\n        if params:\n            dataset_ref[\"params\"] = params", "        params = dataset_default_params(dataset_generator)\n        params[\"allow_truncation\"] = False\n        if params:\n            dataset_ref[\"params\"] = params", [CONTRACT, "-k", "TestNoPathSendsAPartialDataStance"], ["test_the_one_shot_start_body_sends_neither_field[spirals]", "test_the_one_shot_start_body_sends_neither_field[multi_sine]"]),
    # --- the tightened equities test: a seeded allow_truncation True is no longer a substitute for symbols
    ("M-escape symbols swapped for allow_truncation True", REG, EQUITIES_SEED, '''            "allow_truncation": True,
            "fundamentals_fill": "drop",
            "normalize_features": True,''', [CONTRACT, "-k", "test_every_equities_seed_pins_its_universe"], ["test_every_equities_seed_pins_its_universe"]),
]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(args):
    env = dict(os.environ, LIBTORCH="", LD_LIBRARY_PATH="", PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run([PY, "-m", "pytest", *args, "-q", "-rfE", "-p", "no:cacheprovider", "--no-header"], cwd=SRC, env=env, capture_output=True, text=True, check=False)
    failed = re.findall(r"^(?:FAILED|ERROR) (\S+)", proc.stdout, flags=re.MULTILINE)
    return proc.returncode, failed, proc.stdout[-1500:]


# Probes run under a mutation to show what the PRE-CHANGE assertion would have said.
PROBES = {
    "M12a": "from model_registry import DATASET_TYPES, dataset_model_hint; print('pre-change hint assertion (is not None) passes under M12a:', all(dataset_model_hint(d.value) is not None for d in DATASET_TYPES), '| hint for arc_agi =', repr(dataset_model_hint('arc_agi')))",
    "M-escape": "from model_registry import DATASET_TYPES; seeds = [d for d in DATASET_TYPES if d.value in ('equities', 'equities_seq')]; ok = all((isinstance(d.default_params.get('symbols'), (list, tuple)) and len(d.default_params['symbols']) > 0) or d.default_params.get('allow_truncation') is True for d in seeds); print('pre-change equities predicate (pinned OR allow_truncation) passes under M-escape:', ok)",
}


def probe(code):
    env = dict(os.environ, LIBTORCH="", LD_LIBRARY_PATH="", PYTHONDONTWRITEBYTECODE="1")
    proc = subprocess.run([PY, "-c", code], cwd=SRC, env=env, capture_output=True, text=True, check=False)
    return (proc.stdout + proc.stderr).strip()[-600:]


def main() -> int:
    only = set(sys.argv[1:])
    harness_ok = True
    for label, path, anchor, replacement, args, expected in MUTATIONS:
        if only and label.split()[0] not in only:
            continue
        original = path.read_bytes()
        before = sha(path)
        text = original.decode("utf-8")
        count = text.count(anchor)
        if count != 1:
            print(f"SKIPPED {label}: anchor matched {count} times")
            harness_ok = False
            continue
        probe_out = None
        try:
            path.write_text(text.replace(anchor, replacement), encoding="utf-8")
            code, failed, tail = run(args)
            if label.split()[0] in PROBES:
                probe_out = probe(PROBES[label.split()[0]])
        finally:
            path.write_bytes(original)
        if probe_out:
            print(f"PROBE      {probe_out}")
        restored = sha(path) == before
        missing = [e for e in expected if not any(e in f for f in failed)]
        verdict = "CAUGHT" if code != 0 and not missing else "NOT CAUGHT"
        if verdict != "CAUGHT" or not restored:
            harness_ok = False
        print(f"{verdict:10} {label}: pytest exit={code}, {len(failed)} failing; restored={'yes' if restored else 'NO'}")
        for f in failed:
            print(f"             - {f}")
        if missing:
            print(f"             expected but not failing: {missing}")
            print(tail)
    print("HARNESS", "OK" if harness_ok else "PROBLEM")
    return 0 if harness_ok else 1


if __name__ == "__main__":
    sys.exit(main())
