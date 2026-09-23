"""
Mutation-check canopy's "every staging path sends one payload + the nn_model mirror" tests.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-23
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy feat/nn-model-mirror-restart-and-live-swap
         (``src/tests/regression/test_staging_paths_send_one_payload.py``)

Each mutation re-introduces one defect the new tests exist for, in canopy SOURCE, one at a time. N2 is
the one parity cannot see: the shared builder losing the seed for BOTH paths at once, which leaves
"swap == apply" true -- only the explicit seed assertions catch it. Each anchor must match exactly once
(else the script refuses) and the file is restored byte-for-byte in a ``finally`` and verified.

Usage:
    python util/ad-hoc/2026-09-23_mutation_check_staging_paths.py <canopy-worktree>
"""

import os
import subprocess
import sys
from pathlib import Path

PYTHON = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
TESTS = ["tests/regression/test_staging_paths_send_one_payload.py"]
DM = "frontend/dashboard_manager.py"

# name -> (file relative to src/, anchor, replacement, test-name substrings that MUST fail)
MUTATIONS = {
    "N1 the live swap builds its old typed-only body": (
        DM,
        "        payload = self._dataset_stage_payload(dataset_type, n_samples=n_samples, noise=noise, rotations=rotations, n_spirals=n_spirals, gen_values=gen_values, gen_ids=gen_ids, nn_model=nn_model)\n        try:\n            resp = requests.post(\n                self._api_url(\"/api/live_dataset_swap\"),",
        "        payload = {k: v for k, v in {\"nn_dataset_type\": dataset_type, \"nn_dataset_elements\": n_samples, \"nn_dataset_noise\": noise, \"nn_spiral_number\": n_spirals, \"nn_spiral_rotations\": rotations}.items() if v is not None}\n        try:\n            resp = requests.post(\n                self._api_url(\"/api/live_dataset_swap\"),",
        ["test_every_dataset_gets_one_body", "test_a_seeded_generator_s_seed_travels_with_the_swap", "test_the_two_seeds_the_defect_was_found_on", "test_a_non_spiral_swap_carries_no_spiral_fields", "test_the_live_swap_mirrors_the_model"],
    ),
    "N2 the shared builder drops the seed on BOTH paths (parity still holds)": (
        DM,
        "            params = dict(dataset_default_params(dataset_type))\n            params.update(DashboardManager._collect_generator_params(",
        "            params = {}\n            params.update(DashboardManager._collect_generator_params(",
        ["test_a_seeded_generator_s_seed_travels_with_the_swap", "test_the_two_seeds_the_defect_was_found_on"],
    ),
    "N3 the live swap ignores the mirror": (
        DM,
        "gen_values=gen_values, gen_ids=gen_ids, nn_model=nn_model)\n        try:\n            resp = requests.post(\n                self._api_url(\"/api/live_dataset_swap\"),",
        "gen_values=gen_values, gen_ids=gen_ids, nn_model=None)\n        try:\n            resp = requests.post(\n                self._api_url(\"/api/live_dataset_swap\"),",
        ["test_the_live_swap_mirrors_the_model"],
    ),
    "N4 the modal re-stage ignores the mirror": (
        DM,
        "        if nn_model:\n            payload[\"nn_model\"] = nn_model\n        try:\n            resp = requests.post(\n                self._api_url(\"/api/stage_dataset\"),\n                json=payload,\n                timeout=DashboardConstants.DASHBOARD_LONG_POST_TIMEOUT,\n                headers=internal_api_headers(),\n            )\n            if resp.status_code == 200:\n                self.logger.info(\"Restart modal re-staged dataset: %s\", payload)",
        "        try:\n            resp = requests.post(\n                self._api_url(\"/api/stage_dataset\"),\n                json=payload,\n                timeout=DashboardConstants.DASHBOARD_LONG_POST_TIMEOUT,\n                headers=internal_api_headers(),\n            )\n            if resp.status_code == 200:\n                self.logger.info(\"Restart modal re-staged dataset: %s\", payload)",
        ["test_the_modal_re_stage_mirrors_the_model", "test_the_restart_confirm_mirrors_on_both_modify_phases"],
    ),
    "N5 the restart's parameter apply ignores the mirror": (
        DM,
        "            applied, toast = self._apply_params_via_backend(param_updates, nn_model=nn_model)",
        "            applied, toast = self._apply_params_via_backend(param_updates)",
        ["test_the_restart_confirm_mirrors_on_both_modify_phases"],
    ),
    "N6 the live-swap callback reads the wrong store": (
        DM,
        "            State({\"type\": \"nn-gen-param\", \"name\": dash.ALL}, \"id\"),\n            State(\"model-selection-store\", \"data\"),",
        "            State({\"type\": \"nn-gen-param\", \"name\": dash.ALL}, \"id\"),\n            State(\"model-state-store\", \"data\"),",
        ["test_the_model_is_read_as_state_not_input"],
    ),
}


def run(src):
    env = dict(os.environ, LIBTORCH="", LD_LIBRARY_PATH="")
    proc = subprocess.run([PYTHON, "-m", "pytest", *TESTS, "-p", "no:cacheprovider", "-rfE"], cwd=src, env=env, capture_output=True, text=True, check=False)
    failed = [line for line in proc.stdout.splitlines() if line.startswith(("FAILED", "ERROR"))]
    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else proc.stderr.strip()[-300:]
    return proc.returncode, failed, tail


def main():
    src = Path(sys.argv[1]).resolve() / "src"
    code, failed, tail = run(src)
    print(f"baseline: exit={code} :: {tail}")
    if code != 0:
        print("baseline not green; refusing to judge mutations")
        return 2
    survivors = []
    for name, (rel, anchor, replacement, must_fail) in MUTATIONS.items():
        target = src / rel
        original = target.read_bytes()
        text = original.decode()
        if text.count(anchor) != 1:
            print(f"{name}: anchor found {text.count(anchor)} times, expected 1 -- REFUSING")
            return 2
        try:
            target.write_text(text.replace(anchor, replacement))
            code, failed, tail = run(src)
        finally:
            target.write_bytes(original)
        assert target.read_bytes() == original, f"restore failed for {rel}"
        missed = [t for t in must_fail if not any(t in line for line in failed)]
        verdict = "KILLED" if not missed else f"SURVIVED by {missed}"
        if missed:
            survivors.append(name)
        print(f"{name}: {verdict} :: {tail}")
    print(f"restored byte-for-byte; survivors: {survivors or 'none'}")
    return 1 if survivors else 0


if __name__ == "__main__":
    sys.exit(main())
