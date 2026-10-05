#!/usr/bin/env python3
"""Lane C round 3: does one credential file mean ONE key to all three readers?

Readers: the wrapper (bash `$(<file)`, what the unit's server receives as SETTINGS_ENCRYPTION_KEY),
the password-init hand start (Python text-mode read -> --parameters-file), and the re-key gate
(Python text-mode read -> sha256). Server side (2.4.0.0): the env var is used verbatim
(Server/Program.cs:986-987), parameters-file lines are trimmed (Program.cs:1621), and the key hash is
uppercase hex SHA-256 of the UTF-8 key (EncryptedFieldHelper.cs:58-59, HashExtentions.cs:37,46).
Only FAKE keys; the stub server records the key's LENGTH and whether it ends in CR -- never the value.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import subprocess
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C")
F = S / "frozen"
OUT = S / "cr_key"
ME = subprocess.run(["id", "-un"], capture_output=True, text=True, check=True).stdout.strip()
K = "dummy-key-0123456789"


def stub_server(d: Path) -> Path:
    p = d / "server-stub"
    p.write_text("#!/usr/bin/env bash\n"
                 "k=\"${SETTINGS_ENCRYPTION_KEY:-}\"\n"
                 "for a in \"$@\"; do case \"$a\" in --parameters-file=*) f=\"${a#--parameters-file=}\";; esac; done\n"
                 "if [[ -n \"${f:-}\" ]]; then python3 -c 'import sys\nfor l in open(sys.argv[1], newline=\"\").read().split(\"\\n\"):\n  if l.startswith(\"--settings-encryption-key=\"): v=l.split(\"=\",1)[1]; print(\"PARAMS key len=%d ends_with_CR=%s (server trims: len=%d)\" % (len(v), v.endswith(\"\\r\"), len(v.strip())))' \"$f\" >> \"$REPORT\"; fi\n"
                 "if [[ -n \"$k\" ]]; then printf 'ENV key len=%s ends_with_CR=%s\\n' \"${#k}\" \"$([[ \"$k\" == *$'\\r' ]] && echo True || echo False)\" >> \"$REPORT\"; fi\n"
                 "exit 102\n")
    p.chmod(0o700)
    return p


def blob(key: str, ct: str = "c0ffee") -> str:
    return "enc-v1:" + hashlib.sha256(ct.encode()).hexdigest().upper() + hashlib.sha256(key.encode()).hexdigest().upper() + ct


def db_under(path: Path, key: str) -> Path:
    con = sqlite3.connect(path)
    con.executescript('CREATE TABLE "Option" ("BackupID" INTEGER, "Filter" TEXT, "Name" TEXT, "Value" TEXT);'
                      'CREATE TABLE "Backup" ("ID" INTEGER, "Name" TEXT, "TargetURL" TEXT, "DBPath" TEXT);')
    con.execute('INSERT INTO "Option" VALUES (-2, "", "encrypted-fields", "True")')
    con.execute('INSERT INTO "Option" VALUES (-2, "", "pbkdf-config", ?)', (blob(key, "p"),))
    con.execute('INSERT INTO "Backup" VALUES (2, "Y", ?, "x.sqlite")', (blob(key, "t"),))
    con.commit()
    con.close()
    return path


def case(label: str, content: str) -> None:
    d = OUT / label
    if d.exists():
        shutil.rmtree(d)
    (d / "data").mkdir(parents=True, mode=0o700)
    (d / "data").chmod(0o700)
    (d / "creds").mkdir()
    keyfile = d / "creds/settings-key"
    keyfile.write_bytes(content.encode())
    keyfile.chmod(0o600)
    pw = d / "pw"
    pw.write_text("dummy-pw-not-real\n")
    pw.chmod(0o600)
    report = d / "report.txt"
    srv = stub_server(d)
    env = dict(os.environ, REPORT=str(report), PYTHONDONTWRITEBYTECODE="1", PATH=f"{S / 'stubs/bin'}:{os.environ['PATH']}", STUB_LOG=str(d / "stub.log"))
    # 1. the unit's path: the wrapper with LoadCredential's directory
    wenv = dict(env, CREDENTIALS_DIRECTORY=str(d / "creds"), DUPLICATI_ENV_FILE=str(F / "util/systemd/duplicati-env.contract"),
                DUPLICATI_DATA_FOLDER=str(d / "data"), DUPLICATI_REQUIRE_MOUNT="", DUPLICATI_SERVER=str(srv), SETTINGS_ENCRYPTION_KEY="")
    w = subprocess.run(["bash", str(F / "scripts/duplicati-wrapper.bash")], env=wenv, capture_output=True, text=True)
    # 2. the hand start (same user, stub server)
    henv = dict(env, DUPLICATI_RUN_AS=ME, DUPLICATI_SERVER=str(srv))
    h = subprocess.run(["bash", str(F / "util/ad-hoc/2026-10-03_password_init_hand_start.bash"), "--data-folder", str(d / "data"),
                        "--settings-key-file", str(keyfile), "--ui-password-file", str(pw), "--port", "1"], env=henv, capture_output=True, text=True)
    # 3. the gate, against databases written under each candidate key
    g_unit = subprocess.run(["python3", str(F / "util/ad-hoc/2026-10-03_rekey_gate.py"), str(db_under(d / "db_unitkey.sqlite", content.rstrip("\n"))), str(keyfile)], capture_output=True, text=True, env=env)
    trimmed = keyfile.read_text(encoding="utf-8").rstrip("\n")  # exactly the gate's/hand start's own read
    g_py = subprocess.run(["python3", str(F / "util/ad-hoc/2026-10-03_rekey_gate.py"), str(db_under(d / "db_pykey.sqlite", trimmed)), str(keyfile)], capture_output=True, text=True, env=env)
    print(f"== key file {content.encode()!r}  (fake)")
    print(f"   wrapper exit={w.returncode}; hand start exit={h.returncode} ({'refused' if h.returncode == 1 else 'ran'})")
    for ln in (report.read_text().splitlines() if report.exists() else []):
        print(f"   {ln}")
    print(f"   gate vs a DB written under the UNIT's key (bash-read): exit={g_unit.returncode}  {g_unit.stdout.strip()}")
    print(f"   gate vs a DB written under the Python-read key:        exit={g_py.returncode}  {g_py.stdout.strip()}")
    if K in (w.stdout + w.stderr + h.stdout + h.stderr + g_unit.stdout + g_unit.stderr):
        print("   !! the (fake) key reached an output stream")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    case("lf", K + "\n")
    case("crlf", K + "\r\n")
    case("cr_only", K + "\r")
    case("trailing_space", K + " \n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
