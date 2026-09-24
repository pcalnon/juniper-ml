"""Lane A: run canopy's OWN APIKeyAuth tests (the #660 ones) against the gate-marker-preserving
mutations C4 (break) and C6 (enabled from raw), on a scratch copy of canopy origin/main.
Interpreter: JuniperCanopy1. Only the APIKeyAuth test class is selected.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

S = Path(__file__).resolve().parent
SRC = S / "eco" / "juniper-canopy"
WORK = S / "canopy-mut"
PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
REL = Path("src/security.py")
LOOP = "        matched = False\n        for candidate in self._api_keys:\n            if hmac.compare_digest(api_key, candidate):\n                matched = True\n        return matched\n"

MUTATIONS = [
    ("baseline", None, None),
    ("C3 compare any()", LOOP, "        return any(hmac.compare_digest(api_key, k) for k in self._api_keys)\n"),
    ("C4 compare break (gate markers kept)", LOOP, LOOP.replace("                matched = True\n", "                matched = True\n                break\n")),
    ("C6 enabled from raw (gate markers kept)", "self._enabled = len(self._api_keys) > 0", "self._enabled = bool(api_keys)"),
]

if not WORK.exists():
    shutil.copytree(SRC, WORK, symlinks=True)
original = (SRC / REL).read_text(encoding="utf-8")
env = dict(os.environ)
env.pop("JUNIPER_DRIFT_TEST_FORCE_LOCAL", None)
cmd = [PY, "-s", "-m", "pytest", "-q", "-p", "no:cacheprovider", "--no-header", "-o", "addopts=", "src/tests/unit/test_security.py", "-k", "TestAPIKeyAuth or APIKeyAuth"]
for name, old, new in MUTATIONS:
    text = original
    if old is not None:
        assert original.count(old) == 1, (name, original.count(old))
        text = original.replace(old, new)
    (WORK / REL).write_text(text, encoding="utf-8")
    proc = subprocess.run(cmd, cwd=WORK, env=env, capture_output=True, text=True, check=False, timeout=600)
    lines = [ln for ln in proc.stdout.splitlines() if ln.strip()]
    failed = [ln for ln in lines if ln.startswith("FAILED") or ln.startswith("ERROR")]
    print(f"{name:42s} exit={proc.returncode}  {lines[-1][-160:] if lines else proc.stderr[-300:]}")
    for ln in failed[:6]:
        print(f"      {ln[:220]}")
(WORK / REL).write_text(original, encoding="utf-8")
print("restored:", (WORK / REL).read_text(encoding="utf-8") == original)
