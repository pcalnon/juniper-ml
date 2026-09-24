"""Run the proposed atomicity tests against the PR head, N1 and N2 (validator scratch)."""

import os
import shutil
import subprocess
import sys

sys.path.insert(0, "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v428r2/probes")
import my_mutations as mm  # noqa: E402

PROPOSED = mm.V / "probes" / "test_proposed_atomicity.py"
variants = {"PR head": []}
for key, edits in mm.MUTATIONS.items():
    if key.startswith(("N1", "N2")):
        variants[key.split(":")[0]] = edits
for name, edits in variants.items():
    work = mm.V / "fixcheck" / name.replace(" ", "_")
    if work.exists():
        shutil.rmtree(work)
    shutil.copytree(mm.SRC, work, ignore=shutil.ignore_patterns("__pycache__", "data", "logs", ".git"))
    for rel, find, repl in edits:
        p = work / rel
        text = p.read_text(encoding="utf-8")
        assert text.count(find) == 1
        p.write_text(text.replace(find, repl), encoding="utf-8")
    shutil.copy(PROPOSED, work / "juniper_data/tests/unit/test_proposed_atomicity.py")
    proc = subprocess.run([mm.PY, "-m", "pytest", "juniper_data/tests/unit/test_proposed_atomicity.py", "-p", "no:cacheprovider", "--no-header"], cwd=work, capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    lines = [line for line in proc.stdout.splitlines() if " passed" in line or " failed" in line or line.startswith("FAILED")]
    print(f"{name}: rc={proc.returncode}")
    for line in lines:
        print("   ", line)
    shutil.rmtree(work)
