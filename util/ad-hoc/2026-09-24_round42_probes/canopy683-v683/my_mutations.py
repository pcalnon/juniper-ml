"""v683 validator's own mutations (not in the builder's 21-arm harness). Each arm: copy head/, apply ONE edit (anchor must
match exactly once), run a test selection, report failing tests. Selection 'harness' = the builder's six files;
'lane' = the full CI unit-lane selector.

usage: python my_mutations.py <harness|lane> <arm>...
"""

import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
HEAD = HERE / "head"
PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
HARNESS = [
    "src/tests/unit/test_security.py",
    "src/tests/unit/test_secrets_util.py",
    "src/tests/unit/frontend/test_internal_api_key_rules.py",
    "src/tests/unit/frontend/test_internal_api_gate_coverage.py",
    "src/tests/regression/test_blank_api_key_warning_boot.py",
    "src/tests/regression/test_auth_posture_boot_check.py",
]
LANE = ["-m", "not requires_cascor and not requires_server and not slow", "src/tests/unit/", "src/tests/regression/", "src/tests/contract/", "src/tests/performance/"]

ARMS = {
    "M1-blank-key-also-reported-padded": (
        "src/security.py",
        "            _padded_key_source = source if api_key is not None and _api_key_auth.enabled and _is_padded_key(api_key) else None\n",
        "            _padded_key_source = source if api_key is not None and _is_padded_key(api_key) else None\n",
    ),
    "M2-docs-rule-ascii-whitespace-only": (
        "src/main.py",
        '_docs_enabled = not (get_secret("CANOPY_API_KEY") or "").strip()\n',
        '_docs_enabled = not (get_secret("CANOPY_API_KEY") or "").strip(" \\t\\r\\n\\x0b\\x0c")\n',
    ),
    "M3-docs-switch-ignores-the-key-file": (
        "src/main.py",
        '_docs_enabled = not (get_secret("CANOPY_API_KEY") or "").strip()\n',
        '_docs_enabled = not (__import__("os").environ.get("CANOPY_API_KEY") or "").strip()\n',
    ),
    "M4-posture-check-reads-env-only": (
        "src/main.py",
        '    _canopy_api_key = get_secret("CANOPY_API_KEY")\n    try:\n',
        '    _canopy_api_key = __import__("os").environ.get("CANOPY_API_KEY")\n    try:\n',
    ),
}


def main():
    mode = sys.argv[1]
    for name in sys.argv[2:]:
        path, old, new = ARMS[name]
        root = HERE / "mut" / f"{mode}-{name}"
        if root.exists():
            shutil.rmtree(root)
        shutil.copytree(HEAD, root, symlinks=True, ignore=shutil.ignore_patterns("__pycache__", "logs", ".pytest_cache"))
        (root / "logs").mkdir(exist_ok=True)
        (root / "src" / "logs").mkdir(exist_ok=True)
        target = root / path
        text = target.read_text(encoding="utf-8")
        n = text.count(old)
        if n != 1:
            print(f"{name}: ANCHOR matched {n} times -- not measured")
            continue
        target.write_text(text.replace(old, new), encoding="utf-8")
        env = {k: v for k, v in os.environ.items() if k not in ("CANOPY_API_KEY", "CANOPY_API_KEY_FILE", "JUNIPER_CANOPY_REQUIRE_AUTH", "JUNIPER_SKIP_AUTH_POSTURE_CHECK")}
        env.update(LIBTORCH="", LD_LIBRARY_PATH="", PYTHONDONTWRITEBYTECODE="1", PYTHONPYCACHEPREFIX=str(root / ".pyc"), CASCOR_BACKEND_AVAILABLE="0", RUN_SERVER_TESTS="0", ENABLE_SLOW_TESTS="0")
        junit = root / "junit.xml"
        sel = HARNESS if mode == "harness" else LANE
        # binding check: the copy's main.py must be what "import main" resolves to under pytest's pythonpath
        probe = subprocess.run([PY, "-B", "-c", "import sys; sys.path.insert(0, 'src'); import main, security; print(main.__file__); print(security.__file__)"], cwd=root, env=env, capture_output=True, text=True)
        bound = all(str(root) in ln for ln in probe.stdout.split())
        proc = subprocess.run([PY, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "--timeout=300", f"--junitxml={junit}", *sel], cwd=root, env=env, capture_output=True, text=True)
        failed, total = [], 0
        if junit.exists():
            for case in ET.parse(junit).getroot().iter("testcase"):
                total += 1
                if any(ch.tag in ("failure", "error") for ch in case):
                    failed.append(f"{case.get('classname', '').split('.')[-1]}::{case.get('name')}")
        verdict = "CAUGHT" if failed else "SURVIVED"
        print(f"{name} [{mode}] bound={bound}: {verdict} -- {len(failed)} failing of {total} run (pytest exit {proc.returncode})")
        for f in failed[:12]:
            print(f"    {f}")
        tail = [ln for ln in proc.stdout.splitlines() if " passed" in ln or " failed" in ln]
        print("    summary:", tail[-1] if tail else proc.stdout[-300:])


if __name__ == "__main__":
    main()
