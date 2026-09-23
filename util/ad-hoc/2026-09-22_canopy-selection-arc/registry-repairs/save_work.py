"""Save my uncommitted canopy edits before re-basing onto origin/main: a patch plus full-file copies with sha256. Scratch only."""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

WT = Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--registry-record-repairs--20260922-2021--26e0546f")
OUT = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/6452333c-87c8-4e42-a56d-8b7d4ef20767/scratchpad/agent-e/saved-work")
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

OUT.mkdir(parents=True, exist_ok=True)
patch = subprocess.run(["git", "-C", str(WT), "diff", "--full-index"], check=True, capture_output=True).stdout
(OUT / "my-changes.patch").write_bytes(patch)
manifest = {"base": subprocess.run(["git", "-C", str(WT), "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip(), "files": {}}
for rel in PATHS:
    src = WT / rel
    dst = OUT / "files" / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    digest = hashlib.sha256(src.read_bytes()).hexdigest()
    assert hashlib.sha256(dst.read_bytes()).hexdigest() == digest, rel
    manifest["files"][rel] = digest
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
print(f"patch bytes={len(patch)}; saved {len(PATHS)} files; base={manifest['base']}")
