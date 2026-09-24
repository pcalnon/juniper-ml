"""Validator's own mutation arms for #678 (none duplicates the builder's M1-M8).

Each arm: copy the 05f2dfc2 tree, apply exact-once edits, run a targeted test set, and list
which tests FAIL. The control (no edit) must pass fully and bind to the copy, or nothing was
measured. Output: one block per arm.
"""

import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC_TREE = HERE / "05f2dfc2"
WORK = HERE / "mut"
PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"

TESTS = [
    "src/tests/unit/test_security.py",
    "src/tests/unit/test_secrets_util.py",
    "src/tests/unit/test_secrets_util_coverage.py",
    "src/tests/unit/test_juniper_data_api_key_resolution.py",
    "src/tests/unit/test_middleware.py",
    "src/tests/unit/test_middleware_coverage.py",
    "src/tests/unit/test_browser_control_auth.py",
    "src/tests/unit/frontend/test_internal_api_gate_coverage.py",
    "src/tests/regression/test_blank_api_key_warning_boot.py",
    "src/tests/regression/test_auth_posture_boot_check.py",
    "src/tests/regression/test_rate_limit_default.py",
]

PROBE = '''
from pathlib import Path
import main, security, secrets_util
ROOT = Path(__file__).resolve().parents[3]
def test_zz_binding():
    for m in (main, security, secrets_util):
        assert ROOT in Path(m.__file__).resolve().parents, m.__file__
'''

SEC = "src/security.py"
SU = "src/secrets_util.py"
MAIN = "src/main.py"

ARMS = [
    ("CONTROL", "no edit", []),
    (
        "V1-real-key-warns",
        "the blank condition loses its enabled-check: any SET key is recorded, so a REAL key gets the blank WARNING",
        [(SEC, "            _blank_key_source = source if api_key is not None and not _api_key_auth.enabled else None\n", "            _blank_key_source = source if api_key is not None else None\n")],
    ),
    (
        "V2-file-no-longer-stripped",
        "resolve_secret stops stripping the FILE: get_secret('CANOPY_API_KEY') for juniper-deploy's 'key\\n' file becomes an unpresentable key",
        [(SU, "            return path.read_text().strip(), file_env_var\n", "            return path.read_text(), file_env_var\n")],
    ),
    (
        "V3-env-now-stripped",
        "resolve_secret starts stripping the ENV var: flips main._docs_enabled and internal_api for padded/blank env keys",
        [(SU, "    value = os.environ.get(env_var)\n    return value,", "    value = os.environ.get(env_var)\n    value = value.strip() if value is not None else None\n    return value,")],
    ),
    (
        "V4-wrong-logger",
        "the lifespan reports through a stdlib module logger: after configure_logging it reaches root (stderr/JSON) but NOT logs/system.log",
        [(MAIN, "    report_blank_api_key(system_logger)\n", '    report_blank_api_key(__import__("logging").getLogger("juniper_canopy.security"))\n')],
    ),
    (
        "V5-blank-file-falls-through",
        "a blank FILE no longer wins: resolution falls through to CANOPY_API_KEY (a plausible 'fix' that changes precedence for every get_secret caller)",
        [(SU, "            return path.read_text().strip(), file_env_var\n", "            content = path.read_text().strip()\n            if content:\n                return content, file_env_var\n")],
    ),
    (
        "V6-logged-at-error",
        "the WARNING is emitted at ERROR (would page / create a Sentry EVENT)",
        [(SEC, '    log.warning(_BLANK_KEY_FILE_WARNING if source == "CANOPY_API_KEY_FILE" else _BLANK_KEY_ENV_WARNING)\n', '    log.error(_BLANK_KEY_FILE_WARNING if source == "CANOPY_API_KEY_FILE" else _BLANK_KEY_ENV_WARNING)\n')],
    ),
    (
        "V7-get_secret-drops-custom-file-var",
        "get_secret stops forwarding file_env_var (every in-repo caller uses the default, so only a unit test can see it)",
        [(SU, "    return resolve_secret(env_var, file_env_var)[0]\n", "    return resolve_secret(env_var)[0]\n")],
    ),
    (
        "V8-main-bypasses-get_api_key_auth",
        "main.py builds its APIKeyAuth directly instead of via get_api_key_auth(): in production nothing is recorded, so the lifespan never warns",
        [(MAIN, "api_key_auth = get_api_key_auth()\n", "from security import APIKeyAuth as _AKA\n\napi_key_auth = _AKA([_k] if (_k := get_secret(\"CANOPY_API_KEY\")) else None)\n")],
    ),

]


def run_arm(name, edits):
    dest = WORK / name
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(SRC_TREE, dest, symlinks=True, ignore=shutil.ignore_patterns("__pycache__", "logs", "reports", "*.pyc"))
    (dest / "logs").mkdir(exist_ok=True)
    (dest / "src/tests/unit/test_zz_binding_probe.py").write_text(PROBE)
    for path, old, new in edits:
        f = dest / path
        t = f.read_text()
        n = t.count(old)
        if n != 1:
            return f"ANCHOR matched {n}x in {path}: {old[:70]!r}", None
        f.write_text(t.replace(old, new))
    junit = dest / "junit.xml"
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CANOPY_", "JUNIPER_", "SENTRY"))}
    env.update(LIBTORCH="", LD_LIBRARY_PATH="", PYTHONDONTWRITEBYTECODE="1", CASCOR_BACKEND_AVAILABLE="0", RUN_SERVER_TESTS="0", ENABLE_SLOW_TESTS="0")
    cmd = [PY, "-B", "-m", "pytest", "-p", "no:cacheprovider", "-q", "--timeout=120", f"--junitxml={junit}", *TESTS, "src/tests/unit/test_zz_binding_probe.py"]
    subprocess.run(cmd, cwd=dest, env=env, capture_output=True, text=True)
    res = {}
    for tc in ET.parse(junit).getroot().iter("testcase"):
        st = "passed"
        for ch in tc:
            if ch.tag in ("failure", "error"):
                st = ch.tag
            elif ch.tag == "skipped" and st == "passed":
                st = "skipped"
        res[f'{tc.get("classname").split(".")[-2] if tc.get("classname").split(".")[-1].startswith("Test") else tc.get("classname").split(".")[-1]}::{tc.get("classname").split(".")[-1] + "::" if tc.get("classname").split(".")[-1].startswith("Test") else ""}{tc.get("name")}'] = st
    shutil.rmtree(dest, ignore_errors=True)
    return None, res


WORK.mkdir(exist_ok=True)
only = sys.argv[1:]
for name, why, edits in ARMS:
    if only and name not in only and name != "CONTROL":
        continue
    err, res = run_arm(name, edits)
    if err:
        print(f"{name}: {err}")
        continue
    total = len(res)
    failed = sorted(k for k, v in res.items() if v in ("failure", "error"))
    binding = [k for k in res if k.endswith("test_zz_binding")]
    bound = binding and res[binding[0]] == "passed"
    print(f"=== {name}: {total} tests, {len(failed)} failing, binding={'OK' if bound else 'FAILED'}  [{why}]")
    for k in failed:
        print("    FAIL", k)
