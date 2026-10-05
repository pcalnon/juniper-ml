#!/usr/bin/env python3
"""Lane C round 3, task 4 (cont.): the trap's full text for the states that matter, and a RE-RUN after a
post-swap failure (what the operator does next). Reuses t4_rekey_trap.py's scratch machinery."""
import importlib.util
import json
from pathlib import Path

spec = importlib.util.spec_from_file_location("t4", "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C/bin/t4_rekey_trap.py")
t4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t4)
SRC = t4.F / "util/ad-hoc/2026-10-03_rekey_settings_key.bash"


def short(s: str, root: Path) -> str:
    return s.replace(str(root), "<root>")


def full(name, pkw, env):
    root, script = t4.prepare(name, SRC, **pkw)
    r = t4.run(root, script, **env)
    print(f"== {name}: exit={r.returncode}  post-state={json.dumps(t4.state(root))}")
    keep = False
    for ln in r.stderr.splitlines():
        body = ln.split(": ", 1)[1] if ln.startswith("rekey.bash: ") else ln
        if body.startswith(("FATAL", "ABORTED")) or "GATE FAILED" in ln or "encrypted-fields=" in ln:
            keep = True
        if keep:
            print("   | " + short(body, root))
    return root, script


# F2: the stop after the decrypt start fails -> cleartext, keys NOT swapped
full("X_F2_full", {}, {"STUB_FAIL_NTH_STOP": "2"})
# F3: FragmentPath turns into the vendor unit after the drop-in removal
full("X_F3_full", {}, {"STUB_FRAGMENT_AFTER_RELOADS": "2", "STUB_FRAGMENT_LATER": t4.VENDOR})
# F4: the gate fails -- a row under the OLD key that the product's rewrite never touches
full("X_F4_full", {"db_key": t4.NEW}, {})  # control: passes
root, script = t4.prepare("X_F4_conn", SRC)
import sqlite3
con = sqlite3.connect(root / "data/Duplicati-server.sqlite")
con.execute('CREATE TABLE "ConnectionString" ("ID" INTEGER, "Name" TEXT, "Description" TEXT, "BaseUrl" TEXT, "CreatedAt" INTEGER, "UpdatedAt" INTEGER)')
con.execute('INSERT INTO "ConnectionString" VALUES (1, "c", "", ?, 0, 0)', (t4.blob(t4.OLD, "cs"),))
con.commit(); con.close()
r = t4.run(root, script)
print(f"== X_F4_conn (every column under the NEW key except one ConnectionString row under the OLD key): exit={r.returncode}  post-state={json.dumps(t4.state(root))}")
keep = False
for ln in r.stderr.splitlines():
    body = ln.split(": ", 1)[1] if ln.startswith("rekey.bash: ") else ln
    if "GATE FAILED" in ln or body.startswith("ABORTED"):
        keep = True
    if keep:
        print("   | " + short(body, root))
for ln in r.stdout.splitlines():
    print("   stdout| " + ln)

# R1: re-run in the SAME root after the F3 failure (keys swapped, .new gone, CRED.old present)
root3 = t4.S / "rekey_trap" / "X_F3_full"
r = t4.run(root3, root3 / "repo/util/ad-hoc/rekey.bash")
print(f"== R1 re-run after X_F3_full: exit={r.returncode}  post-state={json.dumps(t4.state(root3))}")
for ln in r.stderr.splitlines():
    body = ln.split(": ", 1)[1] if ln.startswith("rekey.bash: ") else ln
    print("   | " + short(body, root3))
