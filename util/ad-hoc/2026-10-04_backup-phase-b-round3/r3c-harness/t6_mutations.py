#!/usr/bin/env python3
"""Lane C round 3, task 6: mutations of the fold-in's new code paths, on ONE scratch copy of the frozen
tree (mut_tree), applied one at a time and restored byte-for-byte after each.

For every mutant: (1) the five suites the brief names, run in mut_tree; (2) an independent instrument of
this lane aimed at the same path (the stub-driven re-key harness, the gate DB matrix, wrapper/installer
probes, the installer's non-dry-run harness, the clearing script's reproduction and gate attacks).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/c9277a65-ade5-4846-8663-19cc9b311f97/scratchpad/val/R3C")
F = S / "frozen"
M = S / "mut_tree"
SUITES = ["tests/test_duplicati_wrapper_contract.py", "tests/test_ci_test_wiring_drift.py", "tests/test_yamaguchi_server_api.py",
          "tests/test_duplicati_web_credential.py", "tests/test_yamaguchi_watchdog.py"]
REKEY = "util/ad-hoc/2026-10-03_rekey_settings_key.bash"
GATE = "util/ad-hoc/2026-10-03_rekey_gate.py"
WRAPPER = "scripts/duplicati-wrapper.bash"
INSTALLER = "util/install_duplicati_service.bash"
CLEAR = "util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py"
PWINIT = "util/ad-hoc/2026-10-03_password_init_hand_start.bash"
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")

MUTANTS = [
    ("M01", REKEY, "drop-in removal: the real `rm -f` of the drop-in deleted",
     '    rm -f "${DROPIN}"\n    rmdir "${DROPIN_DIR}" 2>/dev/null || true\n    systemctl daemon-reload\n',
     '    rmdir "${DROPIN_DIR}" 2>/dev/null || true\n    systemctl daemon-reload\n', "rekey"),
    ("M02", REKEY, "FragmentPath assertion after the drop-in removal deleted",
     '    [[ "${fragment}" == "${INSTALLED_UNIT}" ]] || die "systemd now loads ${fragment}, not ${INSTALLED_UNIT}: do NOT start the unit; re-run the installer first"\n',
     '', "rekey"),
    ("M03", REKEY, "ActiveTask pre-flight neutralised",
     'sys.exit(3 if s.get("ActiveTask") else 0)', 'sys.exit(0 if s.get("ActiveTask") else 0)', "rekey"),
    ("M04", REKEY, "key swap by cp instead of the atomic mv (CRED_NEW left behind)",
     'mv -f "${CRED_NEW}" "${CRED}"; chmod 0600 "${CRED}"', 'cp -f "${CRED_NEW}" "${CRED}"; chmod 0600 "${CRED}"', "rekey"),
    ("M05", REKEY, "swap order inverted: mv first, then the OLD-key copy (copies the NEW key to .old)",
     '    cp -p "${CRED}" "${CRED}.old"; chmod 0600 "${CRED}.old"; chown root:root "${CRED}.old"\n    mv -f "${CRED_NEW}" "${CRED}"; chmod 0600 "${CRED}"; chown root:root "${CRED}"\n',
     '    mv -f "${CRED_NEW}" "${CRED}"; chmod 0600 "${CRED}"; chown root:root "${CRED}"\n    cp -p "${CRED}" "${CRED}.old"; chmod 0600 "${CRED}.old"; chown root:root "${CRED}.old"\n', "rekey"),
    ("M06", REKEY, "EXIT trap no longer removes the drop-in",
     '        rm -f "${DROPIN}"; rmdir "${DROPIN_DIR}" 2>/dev/null || true\n        systemctl daemon-reload || true\n',
     '        systemctl daemon-reload || true\n', "rekey"),
    ("M07", REKEY, "`trap cleanup EXIT` removed",
     'trap cleanup EXIT\n', '\n', "rekey"),
    ("M08", REKEY, "drop-in written WITHOUT the `ExecStart=` reset line",
     "printf '[Service]\\nExecStart=\\nExecStart=%s --disable-db-encryption\\n'", "printf '[Service]\\nExecStart=%s --disable-db-encryption\\n'", "rekey"),
    ("M09", REKEY, "trap's DONE guard removed (a successful run reports ABORTED)",
     '    if (( DONE )); then return 0; fi\n', '', "rekey"),
    ("M10", GATE, "gate: ConnectionString.BaseUrl dropped from COLUMNS",
     '    (\'SELECT "BaseUrl" FROM "ConnectionString"\', "ConnectionString.BaseUrl"),\n', '', "gate"),
    ("M11", GATE, "gate: tolerates one blob under another key", 'and bool(blobs) and bad == 0', 'and bool(blobs) and bad <= 1', "gate"),
    ("M12", GATE, "gate: zero blobs pass", 'and bool(blobs) and bad == 0', 'and bad == 0', "gate"),
    ("M13", GATE, "gate: flag False accepted", 'str(flag[0]).lower() == "true"', 'str(flag[0]).lower() in ("true", "false")', "gate"),
    ("M14", WRAPPER, "wrapper: DUPLICATI__* re-admitted to the export allow-list",
     "readonly ENV_EXPORT_ALLOW='^(SETTINGS_ENCRYPTION_KEY|TMPDIR|TZ|LANG|LC_ALL)$'", "readonly ENV_EXPORT_ALLOW='^(SETTINGS_ENCRYPTION_KEY|TMPDIR|TZ|LANG|LC_ALL|DUPLICATI__[A-Z0-9_]+)$'", "wrapper"),
    ("M15", WRAPPER, "wrapper: option names no longer lower-cased (case-sensitive dedup)", '    name="${name,,}"   # the server\'s slim parser compares option names case-insensitively\n', '', "wrapper"),
    ("M16", WRAPPER, "wrapper: webservice-pre-auth-tokens dropped from ENV_OPTION_DENY", '|webservice-pre-auth-tokens|', '|', "wrapper"),
    ("M17", WRAPPER, "wrapper: deny check on the line as written (case-sensitive)", 'if [[ "${line,,}" =~ ${ENV_OPTION_DENY} ]]; then', 'if [[ "${line}" =~ ${ENV_OPTION_DENY} ]]; then', "wrapper"),
    ("M18", INSTALLER, "installer: commented assignments no longer refused (`#?` dropped)",
     "SECRET_ASSIGN='^[[:space:]]*#?[[:space:]]*(export", "SECRET_ASSIGN='^[[:space:]]*(export", "installer"),
    ("M19", INSTALLER, "installer: option gate case-sensitive (grep -Eq)", 'if grep -Eiq "${HAZARD_OPTION}" "${ENV_SRC}"; then', 'if grep -Eq "${HAZARD_OPTION}" "${ENV_SRC}"; then', "installer"),
    ("M20", INSTALLER, "installer: drift copy-aside's real command replaced by `true` (description kept)",
     '(the drifted installed copy is kept as evidence)" cp -p "${dst}" "${aside}"', '(the drifted installed copy is kept as evidence)" true', "installer"),
    ("M21", INSTALLER, "installer: drifted file not recorded (no copy-aside, still refused)", '        DRIFTED["${dst}"]=1\n', '', "installer"),
    ("M22", CLEAR, "clearing: fence gate disabled", '    if after != expected:\n', '    if False:\n', "clear"),
    ("M23", CLEAR, "clearing: ml#FIXFWD placeholder check removed", '    if "ml#FIXFWD" in text:\n', '    if False:\n', "clear"),
    ("M24", CLEAR, "clearing: fence_edit() no longer declares its edit", '    FENCE_EDITS.append((old, new))\n', '    pass\n', "clear"),
    ("M25", PWINIT, "password-init: edge-whitespace refusal removed", 'if key != key.strip() or pw != pw.strip():', 'if False:', "pwinit"),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def run_suites() -> tuple[bool, str]:
    r = subprocess.run([sys.executable, "-m", "unittest", *SUITES], cwd=M, env=ENV, capture_output=True, text=True, timeout=1200)
    tail = [ln for ln in r.stderr.splitlines() if ln.startswith(("Ran ", "OK", "FAILED"))]
    fails = sorted(set(re.findall(r"^(?:FAIL|ERROR): (\w+) \(([\w.]+)\)", r.stderr, re.M)))
    names = ", ".join(f"{t}" for t, _c in fails[:4]) + (" ..." if len(fails) > 4 else "")
    return r.returncode == 0, " ".join(tail) + (f" -- failing: {names}" if fails else "")


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


T4_BASE = json.loads((S / "t4_baseline.json").read_text())


def inst_rekey(mid: str) -> tuple[bool, str]:
    out = S / f"mut_out/{mid}_t4.json"
    subprocess.run([sys.executable, str(S / "bin/t4_rekey_trap.py"), "--script", str(M / REKEY), "--quiet", "--json", str(out)], env=ENV, check=True, timeout=1200)
    got = json.loads(out.read_text())
    diffs = []
    for case, base in T4_BASE.items():
        g = got[case]
        for key in ("exit", "aborted_printed", "do_not_start_printed"):
            if g[key] != base[key]:
                diffs.append(f"{case}.{key} {base[key]}->{g[key]}")
        for k, v in base["state"].items():
            if g["state"][k] != v:
                diffs.append(f"{case}.{k} {v}->{g['state'][k]}")
    return bool(diffs), "; ".join(diffs[:4]) + (" ..." if len(diffs) > 4 else "")


def inst_gate(mid: str) -> tuple[bool, str]:
    t5 = (S / "bin/t5_gate.py").read_text().replace('GATE = S / "frozen/util/ad-hoc/2026-10-03_rekey_gate.py"', f'GATE = Path("{M / GATE}")')
    p = S / f"mut_out/{mid}_t5.py"
    p.write_text(t5)
    r = subprocess.run([sys.executable, str(p)], env=ENV, capture_output=True, text=True, timeout=600)
    bad = [ln.split(" exit=")[0].strip() for ln in r.stdout.splitlines() if "UNEXPECTED" in ln and "SQLite BLOB type" not in ln]
    return bool(bad), ("unexpected: " + "; ".join(bad[:3])) if bad else "matrix unchanged"


def wrapper_probe(env_line: str | None, argv: list[str]) -> subprocess.CompletedProcess:
    d = S / "mut_out/wrap"
    d.mkdir(parents=True, exist_ok=True)
    (d / "data").mkdir(mode=0o700, exist_ok=True)
    envf = d / "env"
    envf.write_text((env_line + "\n") if env_line else "")
    e = dict(ENV, DUPLICATI_ENV_FILE=str(envf), DUPLICATI_DATA_FOLDER=str(d / "data"), DUPLICATI_REQUIRE_MOUNT="", DUPLICATI_SERVER="/bin/true", SETTINGS_ENCRYPTION_KEY="")
    return subprocess.run(["bash", str(M / WRAPPER), *argv, "--print-command"], env=e, capture_output=True, text=True)


def inst_wrapper(mid: str) -> tuple[bool, str]:
    checks = []
    r = wrapper_probe("DUPLICATI__DISABLE_DB_ENCRYPTION=true", [])
    checks.append(("DUPLICATI__ export refused", r.returncode == 78))
    r = wrapper_probe(None, ["--Webservice-Port=8301"])
    checks.append(("one port after a mixed-case argv override", r.stdout.lower().count("webservice-port") == 1))
    r = wrapper_probe("--webservice-pre-auth-tokens=x", [])
    checks.append(("pre-auth-tokens refused from the env file", r.returncode == 78))
    r = wrapper_probe("--WebService-Reset-JWT-Config=true", [])
    checks.append(("mixed-case reset-jwt-config refused", r.returncode == 78))
    failed = [n for n, ok in checks if not ok]
    return bool(failed), ("probe failed: " + "; ".join(failed)) if failed else "all probes as shipped"


def inst_installer(mid: str) -> tuple[bool, str]:
    msgs = []
    out = S / f"mut_out/{mid}_inst"
    r = subprocess.run(["bash", str(S / "bin/t3_installer_real.bash")], env=dict(ENV, INSTALLER_REPO=str(M), INSTALLER_OUT=str(out)), capture_output=True, text=True, timeout=600)
    if "marker kept: 1" not in r.stdout:
        msgs.append("non-dry-run drift: no aside with the drifted bytes")
    # contract probes on a scratch repo copy of the mutant
    sr = S / f"mut_out/{mid}_repo"
    if sr.exists():
        shutil.rmtree(sr)
    for rel in ("util/install_duplicati_service.bash", "scripts/duplicati-wrapper.bash", "util/systemd/duplicati.service", "util/systemd/duplicati.default",
                "util/yamaguchi-pre-backup-guard.bash", "util/systemd/duplicati-env.contract", "util/ad-hoc/yamaguchi_server_db_snapshot.py",
                "util/systemd/yamaguchi-server-db-snapshot.service", "util/systemd/yamaguchi-server-db-snapshot.timer"):
        (sr / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(M / rel, sr / rel)
    base = (sr / "util/systemd/duplicati-env.contract").read_text()
    for label, line in (("commented key", "# SETTINGS_ENCRYPTION_KEY=abcdefghijklmnop"), ("mixed-case key option", "--Settings-Encryption-Key=abcdefghijklmnop")):
        (sr / "util/systemd/duplicati-env.contract").write_text(base + line + "\n")
        pre = S / f"mut_out/{mid}_pre"
        if pre.exists():
            shutil.rmtree(pre)
        pre.mkdir(parents=True)
        rr = subprocess.run(["bash", str(sr / "util/install_duplicati_service.bash"), "--dry-run"], env=dict(ENV, DUPLICATI_INSTALL_PREFIX=str(pre), DUPLICATI_INSTALL_BLESSED=str(pre / "absent"), TMPDIR=str(S / "tmp")), capture_output=True, text=True)
        if rr.returncode != 2:
            msgs.append(f"{label} not refused (exit {rr.returncode})")
    return bool(msgs), "; ".join(msgs) if msgs else "all as shipped"


def inst_clear(mid: str) -> tuple[bool, str]:
    atk = load("atk", S / "bin/t1_gate_attacks.py")
    atk.OUT = S / f"mut_out/{mid}_attacks"
    atk.OUT.mkdir(parents=True, exist_ok=True)
    script = (M / CLEAR).read_text()
    msgs = []
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        _r, _w = atk.run_case("repro", atk.STAGED, script, expect_write=True)
        same = (atk.OUT / "repro" / atk.D_REL).exists() and sha(atk.OUT / "repro" / atk.D_REL) == sha(F / atk.D_REL)
        b1 = atk.append_edits(script, "edit('stray', 'readonly CRED_NAME=\"settings-key\"', 'readonly CRED_NAME=\"settings-key2\"')")
        _r, wrote_b1 = atk.run_case("b1", atk.STAGED, b1)
        _r, wrote_d1 = atk.run_case("d1", atk.STAGED, script, {"FIXFWD_PR": "ml#FIXFWD"})
    if not same:
        msgs.append("reproduction no longer byte-identical to the frozen D")
    if wrote_b1:
        msgs.append("attack b1 (prose edit inside a tagged block) WROTE")
    if wrote_d1:
        msgs.append("attack d1 (FIXFWD placeholder) WROTE")
    return bool(msgs), "; ".join(msgs) if msgs else "repro identical; b1, d1 refused"


def inst_pwinit(mid: str) -> tuple[bool, str]:
    t3 = load("t3pw", S / "bin/t3_pwinit.py")
    t3.SCRIPT = M / PWINIT
    t3.OUT = S / f"mut_out/{mid}_pw"
    t3.OUT.mkdir(parents=True, exist_ok=True)
    d, stub = t3.setup("e2")
    (d / "pw").write_text(" dummy-not-a-secret \n")
    r = t3.run(d, stub, dry=False)
    called = (d / "server.log").exists()
    return (r.returncode != 1 or called), f"edge-whitespace pw: exit={r.returncode} server_invoked={called}"


INSTRUMENTS = {"rekey": inst_rekey, "gate": inst_gate, "wrapper": inst_wrapper, "installer": inst_installer, "clear": inst_clear, "pwinit": inst_pwinit}


def main() -> int:
    if M.exists():
        shutil.rmtree(M)
    shutil.copytree(F, M, symlinks=True)
    (S / "mut_out").mkdir(exist_ok=True)
    ok, line = run_suites()
    print(f"baseline (unmutated mut_tree): suites {'PASS' if ok else 'FAIL'} [{line}]")
    rows = []
    only = set(sys.argv[1:])
    for mid, rel, desc, old, new, kind in MUTANTS:
        if only and mid not in only:
            continue
        path = M / rel
        orig = path.read_bytes()
        text = orig.decode()
        n = text.count(old)
        if n != 1:
            print(f"{mid}: anchor found {n}x -- SKIPPED")
            continue
        path.write_text(text.replace(old, new), encoding="utf-8")
        try:
            ok, line = run_suites()
            killed_mine, why = INSTRUMENTS[kind](mid)
        finally:
            path.write_bytes(orig)
            assert sha(path) == sha(F / rel), f"restore failed for {rel}"
        verdict = "KILLED" if not ok else "SURVIVED"
        print(f"{mid} [{kind}] {desc}\n     suites: {verdict} [{line}]\n     lane-C instrument: {'KILLED' if killed_mine else 'survived'} -- {why}")
        rows.append({"id": mid, "kind": kind, "desc": desc, "suites": verdict, "suite_line": line, "mine": killed_mine, "mine_why": why})
    (S / "t6_mutations.json").write_text(json.dumps(rows, indent=1))
    print("all files restored; mut_tree == frozen for every mutated file")
    return 0


if __name__ == "__main__":
    sys.exit(main())
