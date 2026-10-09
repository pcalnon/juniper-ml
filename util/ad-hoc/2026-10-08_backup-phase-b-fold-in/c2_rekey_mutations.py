#!/usr/bin/env python3
"""Lane C2 of the Phase B round-3 fold-in: fail-before evidence and mutation kill counts for the re-key,
its gate and the password-init hand start.

Project:     juniper-ml
Sub-Project: backup infrastructure
Author:      Paul Calnon
Created:     2026-10-08
Status:      ad-hoc -- validation instrument (round-3 fold-in, lane C2; R3C D-5)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/ad-hoc/2026-10-04_backup-phase-b-round3/r3c-harness/t6_mutations.py (the round-3 mutants
             M01-M13 this re-runs; its anchors are reused verbatim for the BEFORE tree)
             tests/test_backup_rekey_real_path.py, tests/test_duplicati_wrapper_contract.py

Everything runs on SCRATCH trees, never on the checkout:

  fail-before --before <tree> --scratch <dir>
      <tree> is an extraction of c3d0e890 (`git archive c3d0e890` untarred). Copies the CURRENT two suites
      into a copy of it, adds only the REKEY_INSTALLED_UNIT hook to its re-key (so a failure is about
      behaviour, not the missing hook), and runs lane C2's tests there, printing each test's verdict.
  mutate --set before --tree <c3d0e890 extraction> --scratch <dir>
      the round-3 mutants M01-M13 (re-key and gate) against that tree's OWN contract suite.
  mutate --set after --repo <checkout> --scratch <dir>
      the same intents re-anchored on the current code, plus mutants of the round-3 fold-in's new code,
      against the current contract suite and tests/test_backup_rekey_real_path.py.

Each mutant is applied to one scratch copy and restored byte-for-byte (checked by sha256) afterwards.
Round 4 (2026-10-08) added R4C's four surviving re-key mutants (X24, X25, X26, X40, verbatim from
util/ad-hoc/2026-10-08_backup-phase-b-round4/r4c-bin/r4c_mutants.py) and mutants of the round-4 fold-in
(N15, N16, G05-G09, P02) to the after set. Round 5 added R5A's F14, F19, F21, F22 and F23 (verbatim from
util/ad-hoc/2026-10-08_backup-phase-b-round4/r5a-bin/r5a_mutants.py) and tests/test_a0_restore_scripts.py to
the after set's suites.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

REKEY = "util/ad-hoc/2026-10-03_rekey_settings_key.bash"
GATE = "util/ad-hoc/2026-10-03_rekey_gate.py"
PWINIT = "util/ad-hoc/2026-10-03_password_init_hand_start.bash"
CONTRACT = "tests/test_duplicati_wrapper_contract.py"
REALPATH = "tests/test_backup_rekey_real_path.py"
A0_SUITE = "tests/test_a0_restore_scripts.py"
A0_PREMISE = "util/ad-hoc/2026-09-22_confirm_a0_premise.bash"
A0_RESTORE = "util/ad-hoc/2026-09-22_restore_server_db_from_fileset.bash"
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")

# Round 3's M01-M13, anchors verbatim from r3c-harness/t6_mutations.py (they match c3d0e890).
BEFORE = [
    ("M01", REKEY, "drop-in removal: the real rm deleted", '    rm -f "${DROPIN}"\n    rmdir "${DROPIN_DIR}" 2>/dev/null || true\n    systemctl daemon-reload\n', '    rmdir "${DROPIN_DIR}" 2>/dev/null || true\n    systemctl daemon-reload\n'),
    ("M02", REKEY, "FragmentPath assertion deleted", '    [[ "${fragment}" == "${INSTALLED_UNIT}" ]] || die "systemd now loads ${fragment}, not ${INSTALLED_UNIT}: do NOT start the unit; re-run the installer first"\n', ''),
    ("M03", REKEY, "ActiveTask pre-flight neutralised", 'sys.exit(3 if s.get("ActiveTask") else 0)', 'sys.exit(0 if s.get("ActiveTask") else 0)'),
    ("M04", REKEY, "key swap by cp, not mv", 'mv -f "${CRED_NEW}" "${CRED}"; chmod 0600 "${CRED}"', 'cp -f "${CRED_NEW}" "${CRED}"; chmod 0600 "${CRED}"'),
    ("M05", REKEY, "swap order inverted", '    cp -p "${CRED}" "${CRED}.old"; chmod 0600 "${CRED}.old"; chown root:root "${CRED}.old"\n    mv -f "${CRED_NEW}" "${CRED}"; chmod 0600 "${CRED}"; chown root:root "${CRED}"\n', '    mv -f "${CRED_NEW}" "${CRED}"; chmod 0600 "${CRED}"; chown root:root "${CRED}"\n    cp -p "${CRED}" "${CRED}.old"; chmod 0600 "${CRED}.old"; chown root:root "${CRED}.old"\n'),
    ("M06", REKEY, "trap no longer removes the drop-in", '        rm -f "${DROPIN}"; rmdir "${DROPIN_DIR}" 2>/dev/null || true\n        systemctl daemon-reload || true\n', '        systemctl daemon-reload || true\n'),
    ("M07", REKEY, "trap cleanup EXIT removed", 'trap cleanup EXIT\n', '\n'),
    ("M08", REKEY, "drop-in without the ExecStart= reset", "printf '[Service]\\nExecStart=\\nExecStart=%s --disable-db-encryption\\n'", "printf '[Service]\\nExecStart=%s --disable-db-encryption\\n'"),
    ("M09", REKEY, "trap DONE guard removed", '    if (( DONE )); then return 0; fi\n', ''),
    ("M10", GATE, "gate: ConnectionString dropped", '    (\'SELECT "BaseUrl" FROM "ConnectionString"\', "ConnectionString.BaseUrl"),\n', ''),
    ("M11", GATE, "gate: one blob under another key tolerated", 'and bool(blobs) and bad == 0', 'and bool(blobs) and bad <= 1'),
    ("M12", GATE, "gate: zero blobs pass", 'and bool(blobs) and bad == 0', 'and bad == 0'),
    ("M13", GATE, "gate: flag False accepted", 'str(flag[0]).lower() == "true"', 'str(flag[0]).lower() in ("true", "false")'),
]

AFTER = [
    # M01-M13, same intents, anchors on the current code.
    ("M01", REKEY, "drop-in removal: the real rm deleted", '    rm -f "${DROPIN}"\n    rmdir "${DROPIN_DIR}" 2>/dev/null || true\n    systemctl daemon-reload\n', '    rmdir "${DROPIN_DIR}" 2>/dev/null || true\n    systemctl daemon-reload\n'),
    ("M02", REKEY, "FragmentPath assertion deleted", '    if [[ "${FRAGMENT_SEEN}" != "${INSTALLED_UNIT}" ]]; then\n', '    if false; then\n'),
    BEFORE[2], BEFORE[3], BEFORE[4],
    ("M06", REKEY, "trap no longer removes the drop-in", '        rm -f "${DROPIN}"; rmdir "${DROPIN_DIR}" 2>/dev/null\n', ''),
    BEFORE[6], BEFORE[7], BEFORE[8], BEFORE[9], BEFORE[10], BEFORE[11], BEFORE[12],
    # The fold-in's new code.
    ("N01", REKEY, "pre-flight count's refusal ignored", 'UNREWRITTEN="$(python3 "${GATE}" --unrewritten "${COPY}")" || count_rc=$?', 'UNREWRITTEN="$(python3 "${GATE}" --unrewritten "${COPY}")" || true'),
    ("N02", REKEY, "timer is-active check removed", '    [[ "${timer_active}" == "inactive" ]] || die', '    true || die'),
    ("N03", REKEY, "timer is-enabled back to != enabled", '        disabled|masked|masked-runtime|not-found|"") ;;', '        disabled|masked|masked-runtime|not-found|enabled-runtime|linked|"") ;;'),
    ("N04", REKEY, "trap no longer stops the unit", '        systemctl stop "${UNIT}" || log "WARNING', '        : || log "WARNING'),
    ("N05", REKEY, "DECRYPT_ATTEMPTED never set", 'DECRYPT_ATTEMPTED=1\nrun systemctl start', 'run systemctl start'),
    ("N06", REKEY, "ENCRYPT_ATTEMPTED never set", 'ENCRYPT_ATTEMPTED=1\nrun systemctl start', 'run systemctl start'),
    ("N07", REKEY, "DO_NOT_START never set", '        DO_NOT_START=1\n', ''),
    ("N08", REKEY, "SWAPPED never derived from the files", '    elif [[ "${c}" == NEW && "${o}" == OLD && "${n}" == absent ]]; then keys=SWAPPED', '    elif false; then keys=SWAPPED'),
    ("N09", REKEY, "gate counts not printed by the trap", '    if [[ -n "${GATE_REPORT}" ]]; then log "STATE: gate counts: ${GATE_REPORT}"; fi\n', ''),
    ("N10", REKEY, "dry run claims the decrypt start happened", 'log "dry run: after the decrypt start every field would be CLEARTEXT on disk; nothing was started"', 'log "decrypt start done: every field is now CLEARTEXT on disk; proceeding immediately"'),
    ("N11", REKEY, "REKEY_INSTALLED_UNIT ignored", 'INSTALLED_UNIT="${REKEY_INSTALLED_UNIT:-/etc/systemd/system/${UNIT}}"', 'INSTALLED_UNIT="/etc/systemd/system/${UNIT}"'),
    ("N12", REKEY, "a pre-flight refusal prints the ABORTED block", '        fi\n        return 0\n    fi\n    log "ABORTED', '        fi\n    fi\n    log "ABORTED'),
    ("N13", REKEY, "identical keys accepted", '    [[ "${OLD_H}" != "${NEW_H}" ]] || die', '    true || die'),
    ("N14", REKEY, "UNSWAPPED branch says leave the NEW key", '            log "RECOVERY: the keys were NOT swapped', '            log "RECOVERY: leave the NEW key; the keys were NOT swapped'),
    ("G01", GATE, "gate: SQLite BLOB values not decoded", '    if isinstance(value, bytes):', '    if False:'),
    ("G02", GATE, "--unrewritten: orphan filter matches nothing", 'WHERE "BackupID" NOT IN (SELECT "ID" FROM "Backup")\'))', 'WHERE 0\'))'),
    ("G03", GATE, "gate: a CR in the key accepted", '    if "\\r" in key:', '    if False:'),
    ("G04", GATE, "--unrewritten always exits 0", '        return 1 if n else 0', '        return 0'),
    ("P01", PWINIT, "password-init: dry run skips the secret-format gate", 'write_params ""\n', '\n'),
    # Round 4 (R4C): its four surviving re-key mutants, verbatim from r4c-bin/r4c_mutants.py, and the
    # round-4 fold-in's new code.
    ("X24", REKEY, "UNSWAPPED no longer admits .old==OLD (cp succeeded, mv failed)",
     '    if [[ "${c}" == OLD && "${n}" == NEW && ( "${o}" == absent || "${o}" == OLD ) ]]; then keys=UNSWAPPED',
     '    if [[ "${c}" == OLD && "${n}" == NEW && "${o}" == absent ]]; then keys=UNSWAPPED'),
    ("X25", REKEY, "--unrewritten crash (exit 2) treated as pass", '        *) die "pre-flight: cannot count', '        *) log "pre-flight: cannot count'),
    ("X26", REKEY, "timer is-active: anything but 'active' passes", '    [[ "${timer_active}" == "inactive" ]] || die', '    [[ "${timer_active}" != "active" ]] || die'),
    ("X40", REKEY, "'RECOVERY, FIRST: stop the unit' never printed",
     '    if [[ "${unit}" == active && ( ${DECRYPT_ATTEMPTED} -eq 1 && ${ENCRYPT_ATTEMPTED} -eq 0 ) ]]; then', '    if false; then'),
    ("N15", REKEY, "REKEY_CREDSTORE_DIR honoured on a real run", 'if (( DRY_RUN == 0 )); then echo "FATAL: REKEY_CREDSTORE_DIR', 'if false; then echo "FATAL: REKEY_CREDSTORE_DIR'),
    ("N16", REKEY, "REKEY_CREDSTORE_DIR ignored", '    CRED_DIR="${REKEY_CREDSTORE_DIR}"\n', ''),
    ("G05", GATE, "--unrewritten: settings rows -1/-2 counted as orphans", 'backups | SETTINGS_IDS),', 'backups),'),
    ("G06", GATE, "--unrewritten: orphaned Option/Source/BackupTargetUrl rows do not refuse", '            total += orphaned\n', ''),
    ("G07", GATE, "--unrewritten: Option rows not counted", '(("Option.Value", \'SELECT "BackupID", "Value" FROM "Option"\', backups | SETTINGS_IDS),\n                                ', '(\n                                '),
    ("G08", GATE, "--unrewritten: ConnectionString does not refuse", '            total += conn\n', ''),
    ("G09", GATE, "gate: a NUL in the key accepted", '    if "\\0" in key:', '    if False:'),
    ("P02", PWINIT, "password-init: a NUL in a secret accepted", 'if "\\0" in key or "\\0" in pw:', 'if False:'),
    # Round 5 (R5A NIT-4, NIT-5): verbatim from util/ad-hoc/2026-10-08_backup-phase-b-round4/r5a-bin/r5a_mutants.py.
    ("F14", GATE, "Source rows at -1/-2 treated as attached",
     '("Source.Path", \'SELECT "BackupID", "Path" FROM "Source"\', backups)', '("Source.Path", \'SELECT "BackupID", "Path" FROM "Source"\', backups | SETTINGS_IDS)'),
    ("F19", PWINIT, "hand start: NUL refused in the password only, not the key", 'if "\\0" in key or "\\0" in pw:', 'if "\\0" in pw:'),
    ("F21", REKEY, "REKEY_CREDSTORE_DIR honoured when set EMPTY", 'if [[ -n "${REKEY_CREDSTORE_DIR:-}" ]]; then', 'if [[ -n "${REKEY_CREDSTORE_DIR+x}" ]]; then'),
    ("F22", A0_PREMISE, "A0 premise script: -wal/-journal copy removed",
     '    if [[ -e "${JOBDB}${sfx}" ]]; then cp -p "${JOBDB}${sfx}" "${TMPDB}${sfx}"; fi\n', '    :\n'),
    ("F23", A0_RESTORE, "A0 restore script: -wal/-journal copied under the WRONG name",
     'cp -p "${JOBDB}${sfx}" "${TMPDB}${sfx}"', 'cp -p "${JOBDB}${sfx}" "${TMPDB}.copy${sfx}"'),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_suites(tree: Path, suites: list[str]) -> tuple[bool, str]:
    r = subprocess.run([sys.executable, "-m", "unittest", *suites], cwd=tree, env=ENV, capture_output=True, text=True, timeout=2400)
    tail = [ln for ln in r.stderr.splitlines() if ln.startswith(("Ran ", "OK", "FAILED"))]
    fails = sorted(set(re.findall(r"^(?:FAIL|ERROR): (\w+)", r.stderr, re.M)))
    return r.returncode == 0, " ".join(tail) + (f" -- failing: {', '.join(fails[:4])}{' ...' if len(fails) > 4 else ''}" if fails else "")


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    for part in ("tests", "scripts", "util"):
        shutil.copytree(src / part, dst / part, symlinks=True, ignore=shutil.ignore_patterns("__pycache__"))


def add_unit_hook(tree: Path) -> None:
    p = tree / REKEY
    t = p.read_text()
    a = "INSTALLED_UNIT=/etc/systemd/system/${UNIT}\n"
    if t.count(a) == 1:
        t = t.replace(a, 'INSTALLED_UNIT="${REKEY_INSTALLED_UNIT:-/etc/systemd/system/${UNIT}}"\n')
    # Round 4: the real-path suite rewrites CRED_DIR, which a0ff619c spelt as two absolute assignments.
    # Same paths, no behaviour change -- only the test's anchor.
    b = "CRED=/etc/credstore/duplicati-settings-key\nCRED_NEW=/etc/credstore/duplicati-settings-key.new\n"
    if t.count(b) == 1:
        t = t.replace(b, "CRED_DIR=/etc/credstore\nCRED=${CRED_DIR}/duplicati-settings-key\nCRED_NEW=${CRED}.new\n")
    p.write_text(t)


def fail_before(before: Path, repo: Path, scratch: Path) -> int:
    for label, hook in ((f"{before.name} + test-anchor plumbing only", True), (f"{before.name} unmodified", False)):
        tree = scratch / ("fb_hook" if hook else "fb_plain")
        copy_tree(before, tree)
        if hook:
            add_unit_hook(tree)
        for suite in (CONTRACT, REALPATH):
            shutil.copy(repo / suite, tree / suite)
        r = subprocess.run([sys.executable, "-m", "unittest", "-v", "tests.test_duplicati_wrapper_contract.RecoveryHelperGates",
                            "tests.test_duplicati_wrapper_contract.RekeyGate", "tests.test_backup_rekey_real_path"],
                           cwd=tree, env=ENV, capture_output=True, text=True, timeout=2400)
        print(f"== {label}")
        name = ""
        for ln in r.stderr.splitlines():
            m = re.match(r"^(test_\w+) \(([\w.]+)\)", ln)
            if m:
                name = m.group(2).split(".")[-2] + "." + m.group(1)
            v = re.search(r" \.\.\. (ok|FAIL|ERROR)$", ln)
            if v and name:
                print(f"   {v.group(1):5} {name}")
                name = ""
        print("   " + " ".join(x for x in r.stderr.splitlines() if x.startswith(("Ran ", "OK", "FAILED"))))
    return 0


def mutate(tree: Path, mutants, suites: list[str], only: set[str]) -> int:
    ok, line = run_suites(tree, suites)
    print(f"baseline (unmutated): {'PASS' if ok else 'FAIL'} [{line}]")
    if not ok:
        return 1
    killed = total = 0
    for mid, rel, desc, old, new in mutants:
        if only and mid not in only:
            continue
        path = tree / rel
        orig = path.read_bytes()
        text = orig.decode()
        n = text.count(old)
        if n != 1:
            print(f"{mid}: anchor found {n}x -- SKIPPED ({desc})")
            continue
        path.write_text(text.replace(old, new), encoding="utf-8")
        try:
            ok, line = run_suites(tree, suites)
        finally:
            path.write_bytes(orig)
        assert sha(path) == hashlib.sha256(orig).hexdigest(), f"restore failed for {rel}"
        total += 1
        killed += not ok
        print(f"{mid} {'KILLED  ' if not ok else 'SURVIVED'} {desc} [{line}]", flush=True)
    print(f"killed {killed} of {total}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    fb = sub.add_parser("fail-before")
    fb.add_argument("--before", required=True, type=Path)
    fb.add_argument("--repo", default=Path(__file__).resolve().parents[3], type=Path)
    fb.add_argument("--scratch", required=True, type=Path)
    mu = sub.add_parser("mutate")
    mu.add_argument("--set", choices=("before", "after"), required=True)
    mu.add_argument("--tree", type=Path, help="the c3d0e890 extraction (--set before)")
    mu.add_argument("--repo", default=Path(__file__).resolve().parents[3], type=Path)
    mu.add_argument("--scratch", required=True, type=Path)
    mu.add_argument("only", nargs="*")
    a = ap.parse_args()
    a.scratch.mkdir(parents=True, exist_ok=True)
    if a.cmd == "fail-before":
        return fail_before(a.before, a.repo, a.scratch)
    tree = a.scratch / f"mut_{a.set}"
    if a.set == "before":
        copy_tree(a.tree, tree)
        return mutate(tree, BEFORE, [CONTRACT], set(a.only))
    copy_tree(a.repo, tree)
    return mutate(tree, AFTER, [CONTRACT, REALPATH, A0_SUITE], set(a.only))


if __name__ == "__main__":
    sys.exit(main())
