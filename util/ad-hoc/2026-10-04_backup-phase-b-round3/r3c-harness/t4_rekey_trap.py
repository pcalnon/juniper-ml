#!/usr/bin/env python3
"""Lane C round 3, task 4: drive the re-key's NON-dry-run path and its EXIT trap through failure points.

A COPY of util/ad-hoc/2026-10-03_rekey_settings_key.bash with its four host paths (installed unit, the
two credential files, the runtime drop-in dir) rewritten into a per-case scratch root, placed in a
scratch "repo" next to a STUB API client and the REAL gate. PATH-shadowed stubs: systemctl, journalctl,
sudo (runs as the current user), id (-u -> 0), chown, sleep, install (refuses host paths), stat (reports
root ownership for the scratch credstore only). Fake keys only. Nothing reaches /etc, /run or a unit.

Usage: t4_rekey_trap.py [--script PATH] [--quiet]   (--script lets the mutation harness reuse it)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C")
F = S / "frozen"
STUBS = S / "stubs/bin"
OLD, NEW = "OLDKEY-fake-not-a-secret-0001", "NEWKEY-fake-not-a-secret-0002"
VENDOR = "/usr/lib/systemd/system/duplicati.service"

API_STUB = r'''#!/usr/bin/env python3
import json, os, sys
log = os.environ["API_LOG"]
args = sys.argv[1:]
if args[:1] == ["--help"]:
    print("usage: yamaguchi_server_api.py {status,serverstate,pause,resume,export,...}"); sys.exit(0)
verb = args[0] if args else ""
open(log, "a").write("API " + " ".join(args) + "\n")
fail = os.environ.get("STUB_API_FAIL", "").split()
if verb in fail:
    sys.exit(1)
state_file = os.environ["API_STATE"]
paused = os.path.exists(state_file) and open(state_file).read().strip() == "Paused"
if verb == "pause":
    open(state_file, "w").write("Paused"); sys.exit(0)
if verb == "resume":
    open(state_file, "w").write("Running"); sys.exit(0)
if verb == "serverstate":
    if os.environ.get("STUB_FAIL_SERVERSTATE_AFTER_RESUME") and "API resume" in open(log).read():
        sys.exit(1)
    active = os.environ.get("STUB_ACTIVE_TASK") or None
    print(json.dumps({"ProgramState": "Paused" if paused else "Running", "ActiveTask": ({"Item1": 2, "Item2": active} if active else None)}))
    sys.exit(2 if paused else 0)
sys.exit(0)
'''

STAT_STUB = r'''#!/usr/bin/env bash
if [[ "$#" -eq 3 && "$1" == "-c" && "$2" == "%U:%a" && "$3" == "${STUB_CREDSTORE:?}/"* && -e "$3" ]]; then
    printf 'STAT-STUB %s\n' "$3" >> "${STUB_LOG:?}"
    printf 'root:%s\n' "$(/usr/bin/stat -c '%a' "$3")"; exit 0
fi
exec /usr/bin/stat "$@"
'''

CHMOD_STUB = r'''#!/usr/bin/env bash
# fails `chmod 0600 <CRED>` once CRED_NEW is gone (i.e. right after the swap's mv), when STUB_CHMOD_FAIL_AFTER_MV=1
if [[ "${STUB_CHMOD_FAIL_AFTER_MV:-0}" == 1 && "$#" -eq 2 && "$2" == "${STUB_CRED:?}" && ! -e "${STUB_CRED}.new" ]]; then
    printf 'CHMOD-STUB FAIL %s\n' "$*" >> "${STUB_LOG:?}"; exit 1
fi
exec /usr/bin/chmod "$@"
'''


def blob(key: str, ct: str) -> str:
    return "enc-v1:" + hashlib.sha256(ct.encode()).hexdigest().upper() + hashlib.sha256(key.encode()).hexdigest().upper() + ct


def make_db(path: Path, key: str, flag: str = "True") -> None:
    con = sqlite3.connect(path)
    con.execute("PRAGMA journal_mode=WAL")
    con.executescript('CREATE TABLE "Option" ("BackupID" INTEGER, "Filter" TEXT, "Name" TEXT, "Value" TEXT);'
                      'CREATE TABLE "Backup" ("ID" INTEGER, "Name" TEXT, "TargetURL" TEXT, "DBPath" TEXT);'
                      'CREATE TABLE "Source" ("BackupID" INTEGER, "Path" TEXT);')
    con.execute('INSERT INTO "Option" VALUES (-2, "", "encrypted-fields", ?)', (flag,))
    con.execute('INSERT INTO "Option" VALUES (-2, "", "pbkdf-config", ?)', (blob(key, "p"),))
    con.execute('INSERT INTO "Backup" VALUES (2, "Yamaguchi", ?, "x.sqlite")', (blob(key, "t"),))
    con.execute('INSERT INTO "Source" VALUES (2, ?)', (blob(key, "s"),))
    con.commit()
    con.close()


def prepare(case: str, script_src: Path, db_key: str = NEW, db_flag: str = "True"):
    root = S / "rekey_trap" / case
    if root.exists():
        shutil.rmtree(root)
    repo = root / "repo"
    (repo / "util/ad-hoc").mkdir(parents=True)
    (repo / "util/systemd").mkdir(parents=True)
    text = script_src.read_text(encoding="utf-8")
    reps = {
        "INSTALLED_UNIT=/etc/systemd/system/${UNIT}": f"INSTALLED_UNIT={root}/etc/systemd/system/${{UNIT}}",
        "CRED=/etc/credstore/duplicati-settings-key\n": f"CRED={root}/etc/credstore/duplicati-settings-key\n",
        "CRED_NEW=/etc/credstore/duplicati-settings-key.new": f"CRED_NEW={root}/etc/credstore/duplicati-settings-key.new",
        "DROPIN_DIR=/run/systemd/system/${UNIT}.d": f"DROPIN_DIR={root}/run/systemd/system/${{UNIT}}.d",
    }
    for a, b in reps.items():
        if text.count(a) != 1:
            raise SystemExit(f"rewrite anchor not unique in {script_src}: {a!r} ({text.count(a)}x)")
        text = text.replace(a, b)
    script = repo / "util/ad-hoc/rekey.bash"
    script.write_text(text, encoding="utf-8")
    (repo / "util/ad-hoc/yamaguchi_server_api.py").write_text(API_STUB)
    shutil.copy(F / "util/ad-hoc/2026-10-03_rekey_gate.py", repo / "util/ad-hoc/2026-10-03_rekey_gate.py")
    shutil.copy(F / "util/systemd/duplicati.service", repo / "util/systemd/duplicati.service")
    (root / "etc/systemd/system").mkdir(parents=True)
    shutil.copy(F / "util/systemd/duplicati.service", root / "etc/systemd/system/duplicati.service")
    cs = root / "etc/credstore"
    cs.mkdir(parents=True)
    for name, val in (("duplicati-settings-key", OLD), ("duplicati-settings-key.new", NEW)):
        (cs / name).write_text(val)
        (cs / name).chmod(0o600)
    (root / "data").mkdir()
    make_db(root / "data/Duplicati-server.sqlite", db_key, db_flag)
    (root / "run/systemd/system").mkdir(parents=True)
    sb = root / "stubbin"
    sb.mkdir()
    for f in STUBS.iterdir():
        (sb / f.name).symlink_to(f)
    (sb / "stat").write_text(STAT_STUB)
    (sb / "chmod").write_text(CHMOD_STUB)
    for f in ("stat", "chmod"):
        (sb / f).chmod(0o755)
    return root, script


def run(root: Path, script: Path, **env_extra: str):
    env = dict(os.environ)
    env.update({
        "PATH": f"{root / 'stubbin'}:{os.environ['PATH']}", "STUB_LOG": str(root / "stub.log"), "API_LOG": str(root / "stub.log"),
        "API_STATE": str(root / "api_state"), "STUB_UID": "0", "STUB_CREDSTORE": str(root / "etc/credstore"),
        "STUB_CRED": str(root / "etc/credstore/duplicati-settings-key"),
        "STUB_FRAGMENT": str(root / "etc/systemd/system/duplicati.service"), "STUB_IS_ACTIVE": "active", "STUB_IS_ENABLED": "disabled",
        "REKEY_WORKDIR": str(root / "workdir"), "DUPLICATI_DATA_FOLDER": str(root / "data"), "PYTHONDONTWRITEBYTECODE": "1",
        "STUB_DROPIN": str(root / "run/systemd/system/duplicati.service.d/zz-rekey-disable-db-encryption.conf"),
    })
    env.pop("SUDO_USER", None)
    env.update(env_extra)
    r = subprocess.run(["bash", str(script)], env=env, capture_output=True, text=True, timeout=300)
    return r


def state(root: Path) -> dict:
    cs = root / "etc/credstore"
    def who(p: Path):
        if not p.exists():
            return "absent"
        v = p.read_text()
        return "OLD" if v == OLD else ("NEW" if v == NEW else "other")
    dropin = root / "run/systemd/system/duplicati.service.d/zz-rekey-disable-db-encryption.conf"
    log = (root / "stub.log").read_text().splitlines() if (root / "stub.log").exists() else []
    sched = (root / "api_state").read_text().strip() if (root / "api_state").exists() else "Running (never paused)"
    copies = sorted(p.name for p in (root / "workdir").glob("gate-*")) if (root / "workdir").exists() else []
    return {
        "CRED": who(cs / "duplicati-settings-key"), "CRED.new": who(cs / "duplicati-settings-key.new"), "CRED.old": who(cs / "duplicati-settings-key.old"),
        "drop-in": "PRESENT" if dropin.exists() else "absent", "gate copies": copies or "none", "scheduler": sched,
        "starts": sum(1 for x in log if x.startswith("SYSTEMCTL-STUB start")), "reloads": sum(1 for x in log if x.startswith("SYSTEMCTL-STUB daemon-reload")),
        "revert": sum(1 for x in log if "revert" in x),
        "dropin_at_starts": [x.split(" ", 1)[1].replace(str(root), "<root>") for x in log if x.startswith("DROPIN-AT-START")],
    }


CASES = [
    # name, prepare kwargs, env, description
    ("S0_success", {}, {}, "every step succeeds"),
    ("P1_active_task", {}, {"STUB_ACTIVE_TASK": "Backup"}, "pre-flight: serverstate reports an ActiveTask"),
    ("P2_vendor_fragment_at_preflight", {}, {"STUB_FRAGMENT": VENDOR}, "pre-flight: systemd loads the vendor unit"),
    ("P3_timer_enabled", {}, {"STUB_IS_ENABLED": "enabled"}, "pre-flight: snapshot timer enabled"),
    ("F1a_pause_fails", {}, {"STUB_API_FAIL": "pause"}, "before the decrypt start: API pause fails"),
    ("F1b_decrypt_start_fails", {}, {"STUB_SYSTEMCTL_FAIL": "start duplicati.service"}, "before the decrypt start completes: systemctl start fails (drop-in written)"),
    ("F2_stop_after_decrypt_fails", {}, {"STUB_SYSTEMCTL_FAIL": "stop duplicati.service", "STUB_SYSTEMCTL_FAIL_ONCE_FILE": "@root/failed_once_marker_skip1"}, "after the decrypt start: the stop before the swap fails"),
    ("F2b_chmod_after_mv_fails", {}, {"STUB_CHMOD_FAIL_AFTER_MV": "1"}, "inside the swap: mv done, then chmod fails"),
    ("F3_fragment_vendor_after_dropin_removal", {}, {"STUB_FRAGMENT_AFTER_RELOADS": "2", "STUB_FRAGMENT_LATER": VENDOR}, "after the key swap: FragmentPath is the vendor unit after the drop-in removal"),
    ("F3b_encrypt_start_never_logs_started", {}, {"STUB_START_LINE_FOR": "1 3"}, "after the key swap: the encrypt start never logs 'Server has started'"),
    ("F4_gate_fails_db_under_old_key", {"db_key": OLD}, {}, "after the encrypt start: the gate fails (blobs under the OLD key)"),
    ("F4b_gate_fails_flag_false", {"db_flag": "False"}, {}, "after the encrypt start: the gate fails (encrypted-fields False)"),
    ("F6_serverstate_after_resume_fails", {}, {"STUB_API_FAIL": "serverstate-after-resume"}, "after resume: serverstate fails"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", default=str(F / "util/ad-hoc/2026-10-03_rekey_settings_key.bash"))
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    results = {}
    for name, pkw, env, desc in CASES:
        root, script = prepare(name, Path(args.script), **pkw)
        env = {k: (v.replace("@root", str(root)) if isinstance(v, str) else v) for k, v in env.items()}
        if name == "F2_stop_after_decrypt_fails":
            # fail the SECOND `systemctl stop` (the first is step 3, before the decrypt start)
            env.pop("STUB_SYSTEMCTL_FAIL_ONCE_FILE")
            env["STUB_SYSTEMCTL_FAIL"] = ""
            env["STUB_FAIL_NTH_STOP"] = "2"
        if name == "F6_serverstate_after_resume_fails":
            env["STUB_API_FAIL"] = ""
            env["STUB_FAIL_SERVERSTATE_AFTER_RESUME"] = "1"
        r = run(root, script, **env)
        st = state(root)
        trap = [ln.split(": ", 1)[1] if ": " in ln else ln for ln in r.stderr.splitlines() if any(k in ln for k in ("FATAL", "ABORTED", "STATE:", "RECOVERY:", "          ", "removing the drop-in", "shredded", "resume", "re-key complete"))]
        results[name] = {"exit": r.returncode, "state": st, "trap": trap, "aborted_printed": "ABORTED" in r.stderr,
                         "do_not_start_printed": "do NOT start the unit" in r.stderr}
        if not args.quiet:
            print(f"== {name}: {desc}")
            print(f"   exit={r.returncode}  post-state: {json.dumps(st)}")
            for ln in trap:
                print(f"   | {ln[:240]}")
    if args.json:
        Path(args.json).write_text(json.dumps(results, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
