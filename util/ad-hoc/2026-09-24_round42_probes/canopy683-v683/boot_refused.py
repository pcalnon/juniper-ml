"""Real uvicorn boots of <tree>/src under JUNIPER_CANOPY_REQUIRE_AUTH=true: exit code, and what each log stream carries.

usage: python boot_refused.py <python-exe> <tree-dir> <scenario>...
"""

import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY, TREE = sys.argv[1], Path(sys.argv[2]).resolve()
MARKERS = {
    "blank": "blank (empty or whitespace-only)",
    "refused-wording": "canopy refuses to start",
    "open-wording": "serves without a key, exactly as with no key configured",
    "missing-file": "CANOPY_API_KEY_FILE is set but does not name an existing file",
    "padded": "has leading or trailing whitespace, or a line break",
    "critical": "CRITICAL",
    "AuthPostureError": "AuthPostureError",
    "Application startup failed": "Application startup failed",
}


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


SCEN = {
    "blank-env+require": {"CANOPY_API_KEY": " \t ", "JUNIPER_CANOPY_REQUIRE_AUTH": "true"},
    "blank-file+require": {"CANOPY_API_KEY_FILE": "@BLANKFILE@", "CANOPY_API_KEY": "real-env-key-overridden", "JUNIPER_CANOPY_REQUIRE_AUTH": "true"},
    "unset+missing-file+require": {"CANOPY_API_KEY_FILE": "/nonexistent/canopy-key", "JUNIPER_CANOPY_REQUIRE_AUTH": "true"},
    "blank-env+require+skip": {"CANOPY_API_KEY": " \t ", "JUNIPER_CANOPY_REQUIRE_AUTH": "true", "JUNIPER_SKIP_AUTH_POSTURE_CHECK": "1"},
    "unset+require": {"JUNIPER_CANOPY_REQUIRE_AUTH": "true"},
    "real+require": {"CANOPY_API_KEY": "real-key-xyz", "JUNIPER_CANOPY_REQUIRE_AUTH": "true"},
}

for name in sys.argv[3:]:
    work = Path(tempfile.mkdtemp(prefix=f"boot-{name}-", dir=str(HERE / "work")))
    (work / "conf").mkdir()
    shutil.copy(TREE / "conf" / "logging_config.yaml", work / "conf" / "logging_config.yaml")
    blank = work / "blank_key_file"
    blank.write_text("  \n")
    port = free_port()
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CANOPY_", "JUNIPER_", "SENTRY", "CASCOR_"))}
    env.update(JUNIPER_CANOPY_DEMO_MODE="1", JUNIPER_DATA_URL=f"http://127.0.0.1:{free_port()}", JUNIPER_CANOPY_SERVER__PORT=str(port), JUNIPER_SKIP_DEP_FLOOR_CHECK="1", PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=str(TREE / "src"), LIBTORCH="", LD_LIBRARY_PATH="")
    env.update({k: v.replace("@BLANKFILE@", str(blank)) for k, v in SCEN[name].items()})
    out, err = open(work / "stdout.log", "wb"), open(work / "stderr.log", "wb")
    proc = subprocess.Popen([PY, "-m", "uvicorn", "main:app", "--app-dir", str(TREE / "src"), "--host", "127.0.0.1", "--port", str(port)], cwd=str(work), env=env, stdout=out, stderr=err)
    served = None
    for _ in range(90):
        if proc.poll() is not None:
            break
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/v1/health/live", timeout=1)
            served = True
            break
        except Exception:  # noqa: BLE001
            time.sleep(0.5)
    if proc.poll() is None:
        proc.terminate()
        proc.wait(20)
        rc = f"(served={served}; terminated, rc={proc.returncode})"
    else:
        rc = proc.returncode
    out.close()
    err.close()
    streams = {"stdout": (work / "stdout.log").read_text(errors="replace"), "stderr": (work / "stderr.log").read_text(errors="replace"), "system.log": (work / "logs" / "system.log").read_text(errors="replace") if (work / "logs" / "system.log").exists() else ""}
    print(f"== {TREE.name} {name}: exit={rc}")
    for label, mark in MARKERS.items():
        counts = {s: sum(1 for ln in t.splitlines() if mark in ln) for s, t in streams.items()}
        if any(counts.values()):
            print(f"   {label:<28} {counts}")
    sl = streams["system.log"].splitlines()
    order = [("CRIT" if " | CRITICAL | " in ln else "BLANK") for ln in sl if " | CRITICAL | " in ln or MARKERS["blank"] in ln]
    print("   system.log order:", order)
