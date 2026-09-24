"""Lane A: does service-core's OWN behavioural suite watch the two guards the #2059 gate
now names at the canonical copy? Mutate a scratch copy of juniper-service-core and run
its tests/test_security.py under the JuniperCascor1 interpreter, importing the package
from the scratch copy (PYTHONPATH first), never from an installed wheel.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

S = Path(__file__).resolve().parent
SRC = S / "eco" / "juniper-ml" / "juniper-service-core"
WORK = S / "svc-mut"
PY = "/opt/miniforge3/envs/JuniperCascor1/bin/python"
REL = Path("juniper_service_core/security.py")

FILTER = "self._api_keys: set[str] = {k for k in (api_keys or []) if isinstance(k, str) and k.strip()}"
LOOP = "        matched = False\n        for candidate in self._api_keys:\n            if hmac.compare_digest(api_key, candidate):\n                matched = True\n        return matched\n"

MUTATIONS = [
    ("baseline", None, None),
    ("S1 filter removed", FILTER, "self._api_keys: set[str] = set(api_keys) if api_keys else set()"),
    ("S2 strip dropped", "if isinstance(k, str) and k.strip()}", "if isinstance(k, str) and k}"),
    ("S5 enabled from raw (gate markers kept)", "self._enabled = len(self._api_keys) > 0", "self._enabled = bool(api_keys)"),
    ("S3 compare any()", LOOP, "        return any(hmac.compare_digest(api_key, k) for k in self._api_keys)\n"),
    ("S4 compare break (gate markers kept)", LOOP, LOOP.replace("                matched = True\n", "                matched = True\n                break\n")),
]

if WORK.exists():
    shutil.rmtree(WORK)
shutil.copytree(SRC, WORK)
original = (WORK / REL).read_text(encoding="utf-8")
env = dict(os.environ)
env["PYTHONPATH"] = str(WORK)
env.pop("JUNIPER_DRIFT_TEST_FORCE_LOCAL", None)

for name, old, new in MUTATIONS:
    text = original
    if old is not None:
        assert original.count(old) == 1, (name, original.count(old))
        text = original.replace(old, new)
    (WORK / REL).write_text(text, encoding="utf-8")
    proc = subprocess.run([PY, "-s", "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_security.py", "-x", "--no-header", "-o", "addopts="], cwd=WORK, env=env, capture_output=True, text=True, check=False)
    tail = [ln for ln in proc.stdout.splitlines() if ln.strip()][-3:]
    failed = [ln for ln in proc.stdout.splitlines() if ln.startswith("FAILED")]
    print(f"{name:42s} exit={proc.returncode}  {' / '.join(tail)[-200:]}")
    for ln in failed:
        print(f"      {ln[:200]}")
(WORK / REL).write_text(original, encoding="utf-8")
# Prove the import came from the scratch copy.
proc = subprocess.run([PY, "-s", "-c", "import juniper_service_core.security as m; print(m.__file__)"], cwd=WORK, env=env, capture_output=True, text=True, check=False)
print("imported from:", proc.stdout.strip() or proc.stderr.strip()[-300:])
