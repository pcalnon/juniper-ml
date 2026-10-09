#!/usr/bin/env python3
"""Round 5 lane A: fresh mutants of the round-4 fold-in code (9ce2f602), judged in the mount-absent ci-sim tree.

Usage: r5a_mutants.py <cisim-tree> [ids...]
Each mutant is applied, the covering suites run, the file restored (sha256 checked).
"""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
import sys
from pathlib import Path

W = "scripts/duplicati-wrapper.bash"
I = "util/install_duplicati_service.bash"  # noqa: E741
R = "util/ad-hoc/2026-10-03_rekey_settings_key.bash"
G = "util/ad-hoc/2026-10-03_rekey_gate.py"
P = "util/ad-hoc/2026-10-03_password_init_hand_start.bash"
A1 = "util/ad-hoc/2026-09-22_confirm_a0_premise.bash"
A2 = "util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash"
CONTRACT = "tests/test_duplicati_wrapper_contract.py"
INST = "tests/test_duplicati_installer_real_path.py"
REKEY = "tests/test_backup_rekey_real_path.py"
A0SUITE = "tests/test_a0_restore_scripts.py"  # added 2026-10-08 by the coordinator (C2 round 5): the A0 scripts gained a suite
ALL = [CONTRACT, INST, REKEY, A0SUITE]
SUITES = {W: [CONTRACT, INST], I: [CONTRACT, INST], R: [CONTRACT, REKEY], G: [CONTRACT, REKEY], P: [CONTRACT], A1: ALL, A2: ALL}

M = [
    ("F01", W, "production default mount emptied: an UNSET variable no longer checks any mount",
     '"${DUPLICATI_REQUIRE_MOUNT-/nonexistent-r5a/Backups}"', '"${DUPLICATI_REQUIRE_MOUNT-}"'),
    ("F02", W, "NUL check deleted from the credential path",
     "        [[ \"$(wc -c < \"${cred}\")\" -eq \"$(tr -d '\\000' < \"${cred}\" | wc -c)\" ]] || die", "        true || die"),
    ("F03", W, "NUL check strips newlines instead of NULs (a normal key with a trailing newline refused)",
     "tr -d '\\000' < \"${cred}\"", "tr -d '\\n' < \"${cred}\""),
    ("F04", W, "trailing CR stripped once (if, not while)",
     "        while [[ \"${line}\" == *$'\\r' ]]; do line=\"${line%$'\\r'}\"; done", "        if [[ \"${line}\" == *$'\\r' ]]; then line=\"${line%$'\\r'}\"; fi"),
    ("F05", W, "inner-CR refusal deleted",
     "        [[ \"${line}\" != *$'\\r'* ]] || die \"${file}:${n}: a carriage return inside the line (allowed only at its end)\"\n", ""),
    ("F06", I, "UNBLESSED no longer sets drift (reported, then installed quietly)",
     '            echo "UNBLESSED: installed ${dst} differs from the repository and was never blessed" >&2\n            drift=1\n',
     '            echo "UNBLESSED: installed ${dst} differs from the repository and was never blessed" >&2\n'),
    ("F07", I, "env-file GROUP check dropped (root:root 0640 -- unreadable by duplicati -- accepted)",
     '[[ "${env_owner}" != root || "${env_group}" != duplicati ]]', '[[ "${env_owner}" != root ]]'),
    ("F08", I, "env-file group-write allowed (022 -> 002)",
     "(8#${env_mode} & 8#022) != 0", "(8#${env_mode} & 8#002) != 0"),
    ("F09", I, "env-file other-write allowed (022 -> 020)",
     "(8#${env_mode} & 8#022) != 0", "(8#${env_mode} & 8#020) != 0"),
    ("F10", I, "env-file mode/owner refusal does not exit on a real run",
     '            echo "REFUSING: ${ENV_DST} is ${env_meta}; the service reads it as duplicati -- make it root:duplicati 0640 first" >&2\n            exit 2\n',
     '            echo "REFUSING: ${ENV_DST} is ${env_meta}; the service reads it as duplicati -- make it root:duplicati 0640 first" >&2\n'),
    ("F11", I, "env-file meta check skipped on an unreadable (dry-run) file -> moved inside the readable branch",
     '    env_meta="$(stat -c \'%U:%G:%a\' "${ENV_DST}")"\n', '    env_meta="root:duplicati:640"\n'),
    ("F12", I, "Next hint: `unset url id` dropped from the guard block",
     "cat <<'EOF'\nunset url id\n", "cat <<'EOF'\n"),
    ("F13", I, "wrapper_accepts passes the HOST mount again (DUPLICATI_REQUIRE_MOUNT unset)",
     'DUPLICATI_DATA_FOLDER="${scratch}" DUPLICATI_REQUIRE_MOUNT= \\', 'DUPLICATI_DATA_FOLDER="${scratch}" \\'),
    ("F14", G, "Source rows at -1/-2 treated as attached",
     '(\"Source.Path\", \'SELECT "BackupID", "Path" FROM "Source"\', backups)', '(\"Source.Path\", \'SELECT "BackupID", "Path" FROM "Source"\', backups | SETTINGS_IDS)'),
    ("F15", G, "absent Backup table -> everything attached",
     "            backups = frozenset()\n", "            backups = frozenset(range(-2, 100000))\n"),
    ("F16", G, "BackupTargetUrl dropped from the orphan loop",
     "                                (\"BackupTargetUrl.TargetURL\", 'SELECT \"BackupID\", \"TargetURL\" FROM \"BackupTargetUrl\"', backups)):",
     "                                ):"),
    ("F17", G, "Option keep set loses -2 only (server settings counted as orphans)",
     "SETTINGS_IDS = frozenset({-1, -2})", "SETTINGS_IDS = frozenset({-1})"),
    ("F18", G, "Option keep set loses -1 only",
     "SETTINGS_IDS = frozenset({-1, -2})", "SETTINGS_IDS = frozenset({-2})"),
    ("F19", P, "hand start: NUL refused in the password only, not the key",
     'if "\\0" in key or "\\0" in pw:', 'if "\\0" in pw:'),
    ("F20", G, "read_key: NUL check after the one-line check (order only; expected equivalent)",
     '    if "\\0" in key:\n        print("FATAL: the key file holds a NUL byte', '    if "\\0" in key and False:\n        print("FATAL: the key file holds a NUL byte'),
    ("F21", R, "REKEY_CREDSTORE_DIR honoured when set EMPTY (CRED becomes /duplicati-settings-key)",
     'if [[ -n "${REKEY_CREDSTORE_DIR:-}" ]]; then', 'if [[ -n "${REKEY_CREDSTORE_DIR+x}" ]]; then'),
    ("F22", A1, "A0 premise script: -wal/-journal copy removed",
     '    if [[ -e "${JOBDB}${sfx}" ]]; then cp -p "${JOBDB}${sfx}" "${TMPDB}${sfx}"; fi\n', '    :\n'),
    ("F23", A2, "A0 restore script: -wal/-journal copied under the WRONG name",
     'cp -p "${JOBDB}${sfx}" "${TMPDB}${sfx}"', 'cp -p "${JOBDB}${sfx}" "${TMPDB}.copy${sfx}"'),
    ("F24", I, "PREEXISTING (copy-aside) no longer recorded for an unblessed file",
     '            PREEXISTING["${dst}"]=1\n            # An absent', '            # An absent'),
]


def run(tree: Path, suites: list[str]) -> tuple[bool, str]:
    env = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1", "HOME": str(tree)}
    r = subprocess.run([sys.executable, "-m", "unittest", *suites], cwd=tree, env=env, capture_output=True, text=True, timeout=2400)
    fails = sorted(set(re.findall(r"^(?:FAIL|ERROR): (\w+)", r.stderr, re.M)))
    tail = " ".join(ln for ln in r.stderr.splitlines() if ln.startswith(("Ran ", "OK", "FAILED")))
    return r.returncode == 0, tail + (f" -- failing: {', '.join(fails)}" if fails else "")


def main() -> int:
    tree = Path(sys.argv[1])
    only = set(sys.argv[2:])
    killed = total = 0
    for mid, rel, desc, old, new in M:
        if only and mid not in only:
            continue
        p = tree / rel
        orig = p.read_bytes()
        text = orig.decode()
        n = text.count(old)
        if n != 1:
            print(f"{mid} ANCHOR {n}x -- SKIPPED ({desc})", flush=True)
            continue
        p.write_text(text.replace(old, new), encoding="utf-8")
        try:
            ok, line = run(tree, SUITES[rel])
        finally:
            p.write_bytes(orig)
        assert hashlib.sha256(p.read_bytes()).hexdigest() == hashlib.sha256(orig).hexdigest()
        total += 1
        killed += not ok
        print(f"{mid} {'KILLED  ' if not ok else 'SURVIVED'} {desc} [{line}]", flush=True)
    print(f"killed {killed} of {total}", flush=True)
    return 0


if __name__ == "__main__":
    os.environ.pop("DUPLICATI_REQUIRE_MOUNT", None)
    sys.exit(main())
