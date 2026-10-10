#!/usr/bin/env python3
"""Round 4 lane C: hostile env-file lines against the a0ff619c wrapper (--print-command, /bin/true server).

Usage: envfile_attacks.py <tree> <scratch>
Every value is fake. Prints exit code and the wrapper's argv words (option names; values redacted by the
wrapper itself where secret-named) or the FATAL line.
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

tree, scratch = Path(sys.argv[1]), Path(sys.argv[2])
scratch.mkdir(parents=True, exist_ok=True)
data = scratch / "data"
data.mkdir(mode=0o700, exist_ok=True)
WRAPPER = tree / "scripts/duplicati-wrapper.bash"

CASES: list[tuple[str, bytes]] = [
    ("baseline allowed", b"--log-level=Information\n"),
    ("leading spaces + allowed", b"   --log-level=x\n"),
    ("tab + denied", b"\t--disable-db-encryption\n"),
    ("space before =", b"--log-level =x\n"),
    ("space after =", b"--log-level= x\n"),
    ("upper allowed", b"--LOG-LEVEL=x\n"),
    ("CRLF allowed", b"--log-level=x\r\n"),
    ("CRLF denied", b"--disable-db-encryption\r\n"),
    ("double CR allowed", b"--log-level=x\r\r\n"),
    ("trailing space denied", b"--disable-db-encryption \n"),
    ("cyrillic i in denied name", "--dіsable-db-encryption\n".encode()),
    ("cyrillic o in allowed name", "--webservice-pоrt=1\n".encode()),
    ("Kelvin K in allowed name", "--ping-pong-Keepalive=true\n".encode()),
    ("dotless i in denied name", "--dısable-db-encryption\n".encode()),
    ("long s in denied name", "--server-dataſoldеr=/x\n".encode()),
    ("dotted capital I denied", "--DİSABLE-DB-ENCRYPTION\n".encode()),
    ("fullwidth hyphens", "－－log-level=x\n".encode()),
    ("BOM then allowed", b"\xef\xbb\xbf--log-level=x\n"),
    ("-- alone", b"--\n"),
    ("--=x", b"--=x\n"),
    ("triple dash", b"---log-level=x\n"),
    ("allowed name extended", b"--log-level-x=1\n"),
    ("allowed then = chain", b"--webservice-port=8300=9\n"),
    ("duplicate allowed, last wins", b"--log-level=a\n--log-level=b\n"),
    ("allowed with embedded denied text", b"--log-level=x --disable-db-encryption\n"),
    ("NUL inside denied name", b"--disable\x00-db-encryption\n"),
    ("NUL inside secret name (installer grep blind)", b"SETTINGS_ENCRYPTION_\x00KEY=abcdefghijklmnop\n"),
    ("key with CR mid", b"SETTINGS_ENCRYPTION_KEY=abc\rdef\n"),
    ("key CRLF quoted", b'SETTINGS_ENCRYPTION_KEY="abcdef"\r\n'),
    ("key double CR", b"SETTINGS_ENCRYPTION_KEY=abcdef\r\r\n"),
    ("key leading space in quotes", b"SETTINGS_ENCRYPTION_KEY=' abcdef'\n"),
    ("key mismatched quotes", b"SETTINGS_ENCRYPTION_KEY='abcdef\"\n"),
    ("key internal space", b"SETTINGS_ENCRYPTION_KEY=abc def\n"),
    ("export double space", b"export  TZ=UTC\n"),
    ("export tab", b"export\tTZ=UTC\n"),
    ("LC_ALL then upper allowed", b"LC_ALL=C\n--LOG-LEVEL=x\n"),
    ("no trailing newline denied", b"--disable-db-encryption"),
    ("very long allowed line (1 MiB)", b"--log-level=" + b"a" * (1 << 20) + b"\n"),
    ("10k allowed lines", b"--log-level=x\n" * 10000),
]

LOCALES = ["C", "C.UTF-8", "en_US.UTF-8"]


def run(body: bytes, loc: str) -> tuple[int, str, float]:
    f = scratch / "env"
    f.write_bytes(body)
    env = {"PATH": "/usr/bin:/bin", "DUPLICATI_ENV_FILE": str(f), "DUPLICATI_SERVER": "/bin/true",
           "DUPLICATI_DATA_FOLDER": str(data), "DUPLICATI_REQUIRE_MOUNT": "", "LC_ALL": loc}
    t0 = time.monotonic()
    r = subprocess.run(["bash", str(WRAPPER), "--print-command"], env=env, capture_output=True, timeout=600)
    dt = time.monotonic() - t0
    out = r.stdout.decode("utf-8", "replace").strip()
    err = r.stderr.decode("utf-8", "replace")
    fatal = [ln for ln in err.splitlines() if "FATAL" in ln]
    keyline = [ln for ln in err.splitlines() if "settings encryption key" in ln]
    if r.returncode == 0:
        words = out.split(" ")[2:]
        words = [w[:60] + ("…" if len(w) > 60 else "") for w in words]
        desc = "argv=" + " ".join(words) + (" | " + keyline[0].split(": ", 1)[1] if keyline else "")
    else:
        desc = (fatal[0].split("FATAL: ", 1)[1] if fatal else err.strip()[-200:])[:220]
    return r.returncode, desc, dt


for name, body in CASES:
    for loc in LOCALES:
        rc, desc, dt = run(body, loc)
        print(f"[{loc:11}] {name:48} exit={rc:<3} {dt:5.2f}s {desc}")
