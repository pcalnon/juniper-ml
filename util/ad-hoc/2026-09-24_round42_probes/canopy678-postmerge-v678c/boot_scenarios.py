"""Boot real canopy under uvicorn in several key/posture scenarios and report what was logged.

Usage: python boot_scenarios.py <tree-dir>
For each scenario: start ``uvicorn main:app``, wait until /v1/health/live answers (or the
process exits), stop it, then count blank-key WARNINGs on stdout / stderr, parse JSON lines,
and grep the tree's logs/system.log for lines written by THIS boot.
"""

import json
import os
import socket
import subprocess
import sys
import time
import regex as re

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = os.path.join(HERE, sys.argv[1])
PY = "/opt/miniforge3/envs/JuniperCanopy1/bin/python"
MARK = os.environ.get("BLANK_MARK", "blank (empty or whitespace-only)")

blank_file = os.path.join(HERE, "blank_key_file")
with open(blank_file, "w") as fh:
    fh.write("  \n")
real_file = os.path.join(HERE, "real_key_file")
with open(real_file, "w") as fh:
    fh.write("validator-real-key\n")

SCENARIOS = [
    ("env-blank/json", {"CANOPY_API_KEY": " \t ", "JUNIPER_CANOPY_LOG_FORMAT": "json"}),
    ("file-blank+env-real/json", {"CANOPY_API_KEY_FILE": blank_file, "CANOPY_API_KEY": "real-env-key", "JUNIPER_CANOPY_LOG_FORMAT": "json"}),
    ("env-empty", {"CANOPY_API_KEY": ""}),
    ("env-real", {"CANOPY_API_KEY": "validator-real-key"}),
    ("file-real", {"CANOPY_API_KEY_FILE": real_file}),
    ("unset", {}),
    ("env-blank+require_auth", {"CANOPY_API_KEY": " \t ", "JUNIPER_CANOPY_REQUIRE_AUTH": "true"}),
    ("env-blank+skip_posture", {"CANOPY_API_KEY": " \t ", "JUNIPER_SKIP_AUTH_POSTURE_CHECK": "1"}),
    ("env-blank+require_auth+skip", {"CANOPY_API_KEY": " \t ", "JUNIPER_CANOPY_REQUIRE_AUTH": "true", "JUNIPER_SKIP_AUTH_POSTURE_CHECK": "1"}),
    ("env-real-padded", {"CANOPY_API_KEY": " real-key-with-leading-space"}),
]

_TOKEN_PATTERNS = [re.compile(r"hf_[A-Za-z0-9]{20,}"), re.compile(r"pypi-[A-Za-z0-9_\-]{20,}"), re.compile(r"(?i)(x-api-key['\"]?\s*[:=]\s*['\"]?)[^'\"\s,}]+")]


def redact(text: str) -> str:
    for pat in _TOKEN_PATTERNS:
        text = pat.sub(lambda m: (m.group(1) if m.groups() else "") + "<redacted>", text)
    return text


def free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def health(port):
    try:
        s = socket.create_connection(("127.0.0.1", port), timeout=1)
        s.sendall(b"GET /v1/health/live HTTP/1.1\r\nHost: x\r\nConnection: close\r\n\r\n")
        d = s.recv(200)
        s.close()
        return d.startswith(b"HTTP/1.1 200")
    except OSError:
        return False


syslog = os.path.join(TREE, "logs", "system.log")
for name, extra in SCENARIOS:
    port = free_port()
    env = {k: v for k, v in os.environ.items() if not k.startswith(("CANOPY_", "JUNIPER_", "SENTRY"))}
    env.update(JUNIPER_CANOPY_DEMO_MODE="1", JUNIPER_SKIP_DEP_FLOOR_CHECK="1", PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=f"{TREE}/src:{TREE}", LIBTORCH="", LD_LIBRARY_PATH="")
    env.update(extra)
    before = os.path.getsize(syslog) if os.path.exists(syslog) else 0
    out_path = os.path.join(HERE, f"boot-{sys.argv[1]}-{name.replace('/', '_')}.out")
    err_path = out_path[:-4] + ".err"
    with open(out_path, "wb") as o, open(err_path, "wb") as e:
        proc = subprocess.Popen([PY, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)], cwd=f"{TREE}/src", env=env, stdout=o, stderr=e)
        started = False
        for _ in range(400):
            if proc.poll() is not None:
                break
            if health(port):
                started = True
                break
            time.sleep(0.1)
        proc.terminate()
        try:
            proc.wait(15)
        except subprocess.TimeoutExpired:
            proc.kill()
    out = open(out_path, encoding="utf-8", errors="replace").read()
    err = open(err_path, encoding="utf-8", errors="replace").read()
    with open(syslog, encoding="utf-8", errors="replace") as fh:
        fh.seek(before)
        sl = fh.read()
    json_hits = []
    for line in err.splitlines():
        if MARK in line:
            try:
                json_hits.append(json.loads(line))
            except ValueError:
                json_hits.append("NON-JSON: " + line[:90])
    crit = [line[:160] for line in (out + err).splitlines() if "Auth posture FAILED" in line or "SKIPPED via JUNIPER_SKIP_AUTH" in line][:2]
    print(f"--- {name}: started={started} rc={proc.returncode}")
    print(f"    stdout blank-lines={out.count(MARK)} stderr blank-lines={err.count(MARK)} system.log blank-lines={sl.count(MARK)} file-advice={('CANOPY_API_KEY_FILE is blank' in out + err)}")
    for h in json_hits[:1]:
        print("    stderr record:", h if isinstance(h, str) else {k: h.get(k) for k in ("level", "levelname", "logger", "name", "service", "message")})
    for c in crit:
        print("    posture:", c)
    for secret in (" \t ", "real-env-key", "validator-real-key", " real-key-with-leading-space"):
        if secret.strip() and secret.strip() in (out + err + sl):
            print(f"    !!! value {redact(secret)!r} appears in the logs")
