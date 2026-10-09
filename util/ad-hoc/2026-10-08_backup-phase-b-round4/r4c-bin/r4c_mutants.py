#!/usr/bin/env python3
"""Round 4 lane C: fresh mutants of the a0ff619c fold-in code, judged by the suites that cover each file.

Usage: r4c_mutants.py <tree> [ids...]   (<tree> is a scratch copy of `git archive a0ff619c`)
Each mutant is applied to the scratch tree, the suites are run, and the file is restored (sha256 checked).
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
S = "util/ad-hoc/yamaguchi_server_db_snapshot.py"
R = "util/ad-hoc/2026-10-03_rekey_settings_key.bash"
G = "util/ad-hoc/2026-10-03_rekey_gate.py"
C = "util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py"
CONTRACT = "tests/test_duplicati_wrapper_contract.py"
INST = "tests/test_duplicati_installer_real_path.py"
REKEY = "tests/test_backup_rekey_real_path.py"
CLEAR = "tests/test_clear_stop_backup_design.py"
SUITES = {W: [CONTRACT, INST], I: [CONTRACT, INST], S: [CONTRACT, INST], R: [CONTRACT, REKEY], G: [CONTRACT, REKEY], C: [CLEAR]}

M = [
    # wrapper: the allow-list matcher, case/whitespace/CR handling, check_key_shape
    ("X01", W, "allow-list loses its (=|$) terminator: any option that EXTENDS an allowed name passes",
     "|suppress-welcome-page)(=|$)'", "|suppress-welcome-page)'"),
    ("X04", W, "check_key_shape: leading whitespace no longer refused",
     '[[ "${key}" == "${key#[[:space:]]}" && "${key}" == "${key%[[:space:]]}" ]]', '[[ "${key}" == "${key%[[:space:]]}" ]]'),
    ("X05", W, "check_key_shape skipped on the ENVIRONMENT path",
     '        check_key_shape "SETTINGS_ENCRYPTION_KEY" "${SETTINGS_ENCRYPTION_KEY}"\n', ''),
    ("X06", W, "env file: CRLF no longer stripped",
     "        line=\"${line%$'\\r'}\"\n", ''),
    ("X07", W, "env file: leading whitespace no longer stripped",
     '        line="${line#"${line%%[![:space:]]*}"}"   # drop leading whitespace\n', ''),
    ("X10", W, "env file: quotes no longer stripped from KEY=VALUE",
     '            value="$(strip_quotes "${BASH_REMATCH[3]}")"', '            value="${BASH_REMATCH[3]}"'),
    ("X11", W, "env file overrides a variable systemd already set",
     '            if [[ -n "${!key+x}" ]]; then', '            if false; then'),
    ("X34", W, "deny check removed (allow-list alone refuses)",
     '            if [[ "${line,,}" =~ ${ENV_OPTION_DENY} ]]; then\n', '            if false; then\n'),
    # installer: wrapper_accepts, PREEXISTING copy-aside, env mode, secret gates
    ("X12", I, "wrapper_accepts no longer blanks DUPLICATI_REQUIRE_MOUNT (host mount decides)",
     'DUPLICATI_DATA_FOLDER="${scratch}" DUPLICATI_REQUIRE_MOUNT= \\', 'DUPLICATI_DATA_FOLDER="${scratch}" \\'),
    ("X14", I, "pre-install aside has no timestamp (a re-run overwrites the earlier aside)",
     'aside="${dst}.pre-install-$(date -u +%Y%m%dT%H%M%SZ)"', 'aside="${dst}.pre-install"'),
    ("X15", I, "pre-install aside copied without -p (mode/mtime of the evidence lost)",
     '(a never-blessed file that differs from the repository is kept)" cp -p "${dst}" "${aside}"',
     '(a never-blessed file that differs from the repository is kept)" cp "${dst}" "${aside}"'),
    ("X17", I, "env file installed 0644 (world-readable)",
     'install -m 0640 -o root -g duplicati "${ENV_SRC}" "${ENV_DST}"', 'install -m 0644 -o root -g duplicati "${ENV_SRC}" "${ENV_DST}"'),
    ("X18", I, "SECRET_OPTION back to a single optional #",
     "SECRET_OPTION='^[[:space:]]*(#[#[:space:]]*)?--", "SECRET_OPTION='^[[:space:]]*#?--"),
    ("X19", I, "wrapper_accepts prints no reason on refusal",
     "    (( rc == 0 )) || printf '%s\\n' \"${out}\" | sed 's/^/  wrapper: /' >&2\n", ''),
    ("X35", I, "existing env file never judged (always 'cannot judge')",
     '    if [[ ! -r "${ENV_DST}" ]]; then', '    if true; then'),
    # snapshot: residue removal
    ("X20", S, "dest-wal/dest-shm residue of 1.1.0 not removed",
     'stale = [tmp, tmp + "-wal", tmp + "-shm", tmp + "-journal", dest + "-wal", dest + "-shm"]', 'stale = [tmp, tmp + "-wal", tmp + "-shm", tmp + "-journal"]'),
    ("X21", S, "post-check residue removal loop removed (expected equivalent under DELETE mode)",
     '    for path in stale[1:4]:\n', '    for path in []:\n'),
    # re-key trap / pre-flight
    ("X22", R, "key_tag labels the OLD key NEW",
     '    if [[ -n "${OLD_H}" && "${h}" == "${OLD_H}" ]]; then echo OLD', '    if [[ -n "${OLD_H}" && "${h}" == "${OLD_H}" ]]; then echo NEW'),
    ("X24", R, "UNSWAPPED no longer admits .old==OLD (cp succeeded, mv failed)",
     '    if [[ "${c}" == OLD && "${n}" == NEW && ( "${o}" == absent || "${o}" == OLD ) ]]; then keys=UNSWAPPED',
     '    if [[ "${c}" == OLD && "${n}" == NEW && "${o}" == absent ]]; then keys=UNSWAPPED'),
    ("X25", R, "--unrewritten crash (exit 2) treated as pass",
     '        *) die "pre-flight: cannot count', '        *) log "pre-flight: cannot count'),
    ("X26", R, "timer is-active: anything but 'active' passes (activating/failed/empty)",
     '    [[ "${timer_active}" == "inactive" ]] || die', '    [[ "${timer_active}" != "active" ]] || die'),
    ("X28", R, "foreign ...key.old pre-flight removed",
     '    if [[ -e "${CRED}.old" && "$(key_tag "${CRED}.old")" != OLD ]]; then', '    if false; then'),
    ("X29", R, "STARTED/PAUSED set only AFTER a successful pause",
     'STARTED=1; PAUSED=1   # before the call: a pause that errors may still have paused\napi pause\n', 'api pause\nSTARTED=1; PAUSED=1\n'),
    ("X40", R, "'RECOVERY, FIRST: stop the unit' never printed",
     '    if [[ "${unit}" == active && ( ${DECRYPT_ATTEMPTED} -eq 1 && ${ENCRYPT_ATTEMPTED} -eq 0 ) ]]; then', '    if false; then'),
    ("X38", G, "--unrewritten: ConnectionString blobs not refusing",
     '    return conn + orphaned, f"never-rewritten', '    return orphaned, f"never-rewritten'),
    ("X39", G, "gate read_key strips ALL trailing whitespace (wrapper keeps/refuses it)",
     '    key = key.rstrip("\\n")\n', '    key = key.rstrip()\n'),
    # clearing script
    ("X31", C, "STOP sha gate passes an UNTERMINATED STOP block",
     '    if digest is not None and digest != STOP_SHA256:', '    if digest not in (None, "unterminated") and digest != STOP_SHA256:'),
    ("X32", C, "FIXFWD_PR checked with match (prefix), not fullmatch",
     '    if not FIXFWD_FORM.fullmatch(FIXFWD):', '    if not FIXFWD_FORM.match(FIXFWD):'),
    ("X33", C, "phase-marker gone pattern narrowed to the original wording",
     'gone=r"(?im)^\\*[^*\\n]*\\bheld by the STOP\\b")', 'gone=r"(?m)^\\*Held by the STOP at the top of")'),
]


def run(tree: Path, suites: list[str]) -> tuple[bool, str]:
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
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
    sys.exit(main())
