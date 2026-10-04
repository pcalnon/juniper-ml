#!/usr/bin/env python3
"""
Mutation check for B2's three suites: every pin must fail when the defect it guards is put back.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-03
Status: ad-hoc — investigation (verification evidence for the B2 PR)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md §6.2 row B2;
         tests/test_duplicati_web_credential.py, tests/test_yamaguchi_server_api.py,
         tests/test_yamaguchi_watchdog.py

Each mutation puts ONE defect back into the working tree -- one that B2 removed, or one a later
edit could plausibly introduce -- runs the suite that is supposed to catch it, and restores the
file byte-for-byte (sha256-verified) whatever happens. A mutation the suite does not kill marks
a vacuous pin. The suites are run unmutated first; a red baseline makes every kill meaningless,
so the script stops there.

Bytecode: every run gets a fresh, empty PYTHONPYCACHEPREFIX and PYTHONDONTWRITEBYTECODE=1, so a
mutation that keeps a file's size and lands in the same second as the last compile cannot be
masked by a stale .pyc.

Nothing here talks to a server or reads a secret: the suites are hermetic (an in-process urllib
stub), and the only files written are the repository files being mutated, which are restored.
The deploy script is mutated as TEXT only -- its suite checks it statically and never executes it.

Run from anywhere:  python3 util/ad-hoc/2026-10-03_b2_mutation_check.py
Exit 0 = every mutation killed; 1 = at least one survived; 2 = baseline red or an anchor missing.

2026-10-04, the ml#2115 fix-forward: two anchors moved with the code (export's failure branch is
now in _export; the watchdog's id is default="" rather than required=True), and thirteen mutations
were added for what it changed -- export's single-operation token and its TargetURL check, the stub
that enforces 2.4.0.0's statuses (400 token-less, 500 unsigned, 401 another operation), the absent id
recorded as JOB_MISSING, and the watchdog's usage exit 64. Five of them came from the fix-forward's
two validation lanes: three statuses the stub had wrong or unpinned, and two branches no test reached.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SUITES = {
    "cred": "tests/test_duplicati_web_credential.py",
    "cli": "tests/test_yamaguchi_server_api.py",
    "wd": "tests/test_yamaguchi_watchdog.py",
}
CLIENT = "util/ad-hoc/yamaguchi_server_api.py"
DAPI = "util/ad-hoc/duplicati_api.py"
WATCHDOG = "util/ad-hoc/yamaguchi_watchdog.py"
UNIT = "util/systemd/yamaguchi-watchdog.service"
DEPLOY = "util/ad-hoc/yamaguchi_watchdog_deploy.bash"
STUB = "tests/duplicati_api_stub.py"

# (name, file, anchor -- must occur exactly once, replacement, suite expected to kill it)
MUTATIONS = [
    ("credential mode check removed", CLIENT, "        if mode & 0o077:", "        if False and mode & 0o077:", "cred"),
    ("bare-secret fallback restored", CLIENT, "    if len(values) != 1:", "    if not values:\n        return text.strip()\n    if len(values) != 1:", "cred"),
    ("pre-B2 quote strip (every quote at either end)", CLIENT, "    value = value.strip()\n    if len(value) >= 2", "    return value.strip().strip(\"'\\\"\")\n    if len(value) >= 2", "cred"),
    ("credential path back to the checkout .env", CLIENT, 'CRED_FILE = "~/.config/duplicati-backup/web-credential"', 'CRED_FILE = "/home/pcalnon/Development/python/Juniper/juniper-ml/.env"', "cred"),
    ("duplicati_api honours the retired DUPLICATI_PW_FILE", DAPI, "    return read_credential()", '    return read_credential(os.environ.get("DUPLICATI_PW_FILE") or None)', "cred"),
    ("pause sends a duration (no longer indefinite)", CLIENT, 'f"/api/v1/serverstate/{verb}"', 'f"/api/v1/serverstate/{verb}?duration=1h"', "cli"),
    ("pause/resume trust the 200 without reading back", CLIENT, '    if state.get("ProgramState") != want:', "    if False:", "cli"),
    ("serverstate exits 0 when Paused", CLIENT, '    if program == "Paused":\n        return 2', '    if program == "Paused":\n        return 0', "cli"),
    ("a missing job id defaults to 2", CLIENT, "    if not given:\n        ap.error(", '    if not given:\n        given = {"2"}\n    if False:\n        ap.error(', "cli"),
    ("job id matched as a prefix (accepts 7\\n, 2/../x)", CLIENT, "    if not JOB_ID.fullmatch(bid):", "    if not JOB_ID.match(bid):", "cli"),
    ("pre-B2 export failure: message on stdout, exit 0", CLIENT, '        return _failed(f"export {target}", status, body)', '        print(f"export failed {status}: {body}")\n        return 0', "cli"),
    ("export sends no operation token (ml#2115 as merged)", CLIENT, '{"export-passwords": "false", "token": op}', '{"export-passwords": "false"}', "cli"),
    ("export passes the Bearer access token as the operation token", CLIENT, '"token": op}', '"token": tok}', "cli"),
    ("export downloads although issuetoken failed", CLIENT, "    if not op:\n", "    if False:\n", "cli"),
    ("the operation token is printed", CLIENT, "    query = urllib.parse.urlencode(", '    print(f"token={op}", file=sys.stderr)\n    query = urllib.parse.urlencode(', "cli"),
    ("an export body without a TargetURL ({} included) is printed as success", CLIENT, "    if status != 200 or _target_url(body) is None:", "    if status != 200 or not isinstance(body, dict):", "cli"),
    ("an empty TargetURL counts as one", CLIENT, "    return url if isinstance(url, str) and url else None", "    return url if isinstance(url, str) else None", "cli"),
    ("a non-error issuetoken body is echoed (it may carry the token)", CLIENT, '        detail = body if status >= 400 else {"error": "the issuetoken response carried no usable Token"}', "        detail = body", "cli"),
    ("stub answers 401 for a token it never signed (2.4.0.0 answers 500)", STUB, '            return 500, {"Error": "An error occurred", "Code": 500}', '            return 401, {"Error": "Invalid operation", "Code": 401}', "cli"),
    ("stub's issuetoken accepts any Bearer token", STUB, '            if headers.get("authorization") != f"Bearer {self.bearer}":', '            if not headers.get("authorization", "").startswith("Bearer "):', "cli"),
    ("stub's export rule covers one job only", STUB, '_EXPORT_PATH = re.compile(r"/api/v1/backup/[^/]+/export")', '_EXPORT_PATH = re.compile(r"/api/v1/backup/7/export")', "cli"),
    ("stub applies no product rule: a token-less export is answered (the fixture that hid ml#2115)", STUB, "        refusal = self._product_refusal(method, parts.path, query, headers)", "        refusal = None", "cli"),
    ("usage errors exit argparse's 2 again", CLIENT, "EXIT_USAGE = 64", "EXIT_USAGE = 2", "cli"),
    ("server-wide verbs silently accept an id", CLIENT, '        ap.error(f"{args.cmd} is server-wide', '        pass\n    if False:\n        ap.error(f"{args.cmd} is server-wide', "cli"),
    ("login failure prints the password", CLIENT, 'sys.exit(f"FATAL: login failed ({status}): {json.dumps(body)[:300]}")', 'sys.exit(f"FATAL: login failed ({status}) with {read_credential()}")', "cli"),
    ("PAUSED_WITH_QUEUE never fires (pre-B2)", WATCHDOG, "        if queue:", "        if False:", "wd"),
    ("freshness from ANY operation (pre-B2 gap 2)", WATCHDOG, '            if result.get("MainOperation") == "Backup":', "            if True:", "wd"),
    ("watchdog --backup-id defaults to 2 (pre-B2)", WATCHDOG, '"--backup-id", default="",', '"--backup-id", default="2",', "wd"),
    ("an absent --backup-id is a usage error again: no record (ml#2115 as merged)", WATCHDOG, '"--backup-id", default="",', '"--backup-id", required=True,', "wd"),
    ("watchdog usage errors exit argparse's 2 (reads as UNDETERMINED)", WATCHDOG, "    ap = _UsageParser(", "    ap = argparse.ArgumentParser(", "wd"),
    ("an invalid id is sent to the server", WATCHDOG, "    if not JOB_ID.fullmatch(backup_id):", "    if False:", "wd"),
    ("an unknown ProgramState passes silently", WATCHDOG, '    if program not in ("Running", "Paused"):', "    if False:", "wd"),
    ("log paging without offset", WATCHDOG, '("" if offset is None else f"&offset={offset}")', '""', "wd"),
    ("record details keep their newlines", WATCHDOG, 'details = str(details).replace("\\r", " ").replace("\\n", " ")', "details = str(details)", "wd"),
    ("notify-send child is handed the password", WATCHDOG, "check=False, capture_output=True)", 'check=False, capture_output=True, env=dict(os.environ, DUPLICATI_WEB_CREDENTIAL=api.read_credential()))', "wd"),
    ("unit passes the id unbraced (splits / vanishes)", UNIT, "--backup-id ${YAMAGUCHI_BACKUP_ID}", "--backup-id $YAMAGUCHI_BACKUP_ID", "wd"),
    ("unit takes no id at all (pre-B2)", UNIT, " --backup-id ${YAMAGUCHI_BACKUP_ID}", "", "wd"),
    ("deploy script defaults the id", DEPLOY, 'BACKUP_ID=""', 'BACKUP_ID="2"', "wd"),
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_suite(key: str) -> tuple[int, str]:
    with tempfile.TemporaryDirectory(prefix="b2-mutation-pyc-") as prefix:
        env = dict(os.environ, PYTHONPYCACHEPREFIX=prefix, PYTHONDONTWRITEBYTECODE="1")
        proc = subprocess.run([sys.executable, "-m", "unittest", SUITES[key]], cwd=REPO, env=env, capture_output=True, text=True, timeout=300, check=False)
    tail = [line for line in proc.stderr.splitlines() if line.strip()]
    return proc.returncode, (tail[-1] if tail else "")


def main() -> int:
    for key, suite in SUITES.items():
        rc, tail = run_suite(key)
        print(f"baseline  {suite}: rc={rc} {tail}")
        if rc != 0:
            print("BASELINE RED -- a kill would mean nothing; stopping")
            return 2

    survived = []
    for name, rel, anchor, replacement, key in MUTATIONS:
        path = REPO / rel
        original = path.read_bytes()
        digest = sha256(original)
        text = original.decode("utf-8")
        count = text.count(anchor)
        if count != 1:
            print(f"CANNOT APPLY  {name}: the anchor occurs {count} times in {rel}")
            return 2
        try:
            path.write_bytes(text.replace(anchor, replacement).encode("utf-8"))
            rc, tail = run_suite(key)
        finally:
            path.write_bytes(original)  # restored whatever happened, including an interrupt
        if sha256(path.read_bytes()) != digest:
            print(f"RESTORE FAILED for {rel} -- inspect the working tree before anything else")
            return 2
        verdict = "KILLED  " if rc != 0 else "SURVIVED"
        print(f"{verdict}  [{key:4}] {name}  ({tail})")
        if rc == 0:
            survived.append(name)

    print(f"\n{len(MUTATIONS) - len(survived)}/{len(MUTATIONS)} mutations killed; every mutated file restored and sha256-verified")
    for name in survived:
        print(f"  SURVIVED: {name}")
    return 1 if survived else 0


if __name__ == "__main__":
    sys.exit(main())
