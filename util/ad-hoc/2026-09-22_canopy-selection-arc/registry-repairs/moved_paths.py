"""Per-path drift check before upload: `git log --oneline HEAD..origin/main -- <path>` for every path. Scratch only."""

import subprocess
import sys

WT = "/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--registry-record-repairs--20260922-2021--26e0546f"
PATHS = [
    "CHANGELOG.md",
    "src/dataset_schema.py",
    "src/model_registry.py",
    "src/tests/regression/test_dataset_generator_contract.py",
    "src/tests/regression/test_model_picker.py",
    "src/tests/regression/test_selection_reachability_guardrails.py",
    "src/tests/unit/frontend/test_n7_dataset_panel.py",
    "src/tests/unit/test_model_registry.py",
]
base = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
moved = 0
for path in PATHS:
    out = subprocess.run(["git", "-C", WT, "log", "--oneline", f"{base}..origin/main", "--", path], check=True, capture_output=True, text=True).stdout.strip()
    print(f"{path}: {'MOVED -> ' + out.replace(chr(10), ' | ') if out else 'clean'}")
    moved += bool(out)
print(f"moved={moved} of {len(PATHS)} (range {base}..origin/main)")
