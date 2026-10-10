#!/usr/bin/env python3
"""Lane C1's fail-before and mutation runs for the wrapper / installer / snapshot fold-in.

Project:     juniper-ml
Sub-Project: backup infrastructure
Author:      Paul Calnon
Created:     2026-10-08
Version:     1.3.0 (2026-10-08: round-6 `r6` mode; round-5 mutants R17-R27; ci-sim by a `mountpoint` PATH stub)
Status:      ad-hoc -- validation instrument (Phase B round-3 fold-in, lane C1)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/ad-hoc/2026-10-04_backup-phase-b-round3/r3c-harness/t6_mutations.py (round 3's M01-M25)
             util/ad-hoc/2026-10-04_backup-phase-b-round3/R3C.md (D-5: 14 of 25 mutants survived)

Usage:  c1_mutations.py <scratch-dir> <frozen-tree> <worktree> {before|failbefore|after|cisim|r5a|r6} [mutant ids]
  before      round 3's wrapper/installer mutants M14-M21 on a copy of the FROZEN tree, judged by the
              frozen suite's WrapperEnvContract and InstallerDriftGate (the only classes that run the
              wrapper or the installer) -- the "before" kill count.
  failbefore  the worktree's new/changed tests run against the FROZEN code (each must fail there).
  after       mutants of the NEW code on a copy of the worktree, judged by the lane's classes
              (WrapperEnvContract, InstallerDriftGate) plus tests/test_duplicati_installer_real_path.py.

Everything runs on copies under <scratch-dir>; nothing in the worktree or on the host is changed. No
unit, binary or secret is touched: the suites themselves are hermetic.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

WRAPPER = "scripts/duplicati-wrapper.bash"
INSTALLER = "util/install_duplicati_service.bash"
SNAPSHOT = "util/ad-hoc/yamaguchi_server_db_snapshot.py"
CONTRACT_SUITE = "tests/test_duplicati_wrapper_contract.py"
REAL_SUITE = "tests/test_duplicati_installer_real_path.py"

# Round 3's wrapper/installer mutants, verbatim from t6_mutations.py (anchors are the frozen code's).
BEFORE = [
    ("M14", WRAPPER, "DUPLICATI__* re-admitted to the export allow-list",
     "readonly ENV_EXPORT_ALLOW='^(SETTINGS_ENCRYPTION_KEY|TMPDIR|TZ|LANG|LC_ALL)$'", "readonly ENV_EXPORT_ALLOW='^(SETTINGS_ENCRYPTION_KEY|TMPDIR|TZ|LANG|LC_ALL|DUPLICATI__[A-Z0-9_]+)$'"),
    ("M15", WRAPPER, "option names no longer lower-cased", '    name="${name,,}"   # the server\'s slim parser compares option names case-insensitively\n', ''),
    ("M16", WRAPPER, "webservice-pre-auth-tokens dropped from ENV_OPTION_DENY", '|webservice-pre-auth-tokens|', '|'),
    ("M17", WRAPPER, "deny check case-sensitive", 'if [[ "${line,,}" =~ ${ENV_OPTION_DENY} ]]; then', 'if [[ "${line}" =~ ${ENV_OPTION_DENY} ]]; then'),
    ("M18", INSTALLER, "commented assignments no longer refused", "SECRET_ASSIGN='^[[:space:]]*#?[[:space:]]*(export", "SECRET_ASSIGN='^[[:space:]]*(export"),
    ("M19", INSTALLER, "option gate case-sensitive", 'if grep -Eiq "${HAZARD_OPTION}" "${ENV_SRC}"; then', 'if grep -Eq "${HAZARD_OPTION}" "${ENV_SRC}"; then'),
    ("M20", INSTALLER, "drift copy-aside's real command replaced by `true`",
     '(the drifted installed copy is kept as evidence)" cp -p "${dst}" "${aside}"', '(the drifted installed copy is kept as evidence)" true'),
    ("M21", INSTALLER, "drifted file not recorded", '        DRIFTED["${dst}"]=1\n', ''),
]

# Mutants of the NEW code: round 3's that still have an anchor, plus one per new behaviour.
AFTER = [
    ("M14", WRAPPER, "DUPLICATI__* re-admitted to the export allow-list",
     "readonly ENV_EXPORT_ALLOW='^(SETTINGS_ENCRYPTION_KEY|TMPDIR|TZ|LANG|LC_ALL)$'", "readonly ENV_EXPORT_ALLOW='^(SETTINGS_ENCRYPTION_KEY|TMPDIR|TZ|LANG|LC_ALL|DUPLICATI__[A-Z0-9_]+)$'"),
    ("M15", WRAPPER, "option names no longer lower-cased", '    name="${name,,}"   # the server\'s slim parser compares option names case-insensitively\n', ''),
    ("M16", WRAPPER, "webservice-pre-auth-tokens dropped from ENV_OPTION_DENY", '|webservice-pre-auth-tokens|', '|'),
    ("M17", WRAPPER, "deny check case-sensitive", 'if [[ "${line,,}" =~ ${ENV_OPTION_DENY} ]]; then', 'if [[ "${line}" =~ ${ENV_OPTION_DENY} ]]; then'),
    ("W1", WRAPPER, "parameters-file and parameterfile dropped from ENV_OPTION_DENY", '|parameters-file|parameterfile|', '|'),
    ("W2", WRAPPER, "allow-list check removed", '            if [[ ! "${line,,}" =~ ${ENV_OPTION_ALLOW} ]]; then\n', '            if false; then\n'),
    ("W3", WRAPPER, "allow-list check case-sensitive", 'if [[ ! "${line,,}" =~ ${ENV_OPTION_ALLOW} ]]; then', 'if [[ ! "${line}" =~ ${ENV_OPTION_ALLOW} ]]; then'),
    ("W4", WRAPPER, "allow-list widened by one posture option", '|webservice-suppress-welcome-page)(=|$)', '|webservice-suppress-welcome-page|log-file)(=|$)'),
    ("W5", WRAPPER, "CR check on the key removed", "    [[ \"${key}\" != *$'\\r'* ]] || die", "    true || die"),
    ("W6", WRAPPER, "edge-whitespace check on the key removed", '    [[ "${key}" == "${key#[[:space:]]}" && "${key}" == "${key%[[:space:]]}" ]] || die', '    true || die'),
    ("W7", WRAPPER, "key-shape check skipped on the credential path", '        check_key_shape "systemd credential ${CRED_NAME}" "${key}"\n', ''),
    ("W8", WRAPPER, "alias webservice-allowedhostnames dropped from ENV_OPTION_DENY", '|webservice-allowedhostnames|', '|'),
    ("M18", INSTALLER, "commented assignments no longer refused", "SECRET_ASSIGN='^[[:space:]]*(#[#[:space:]]*)?(export", "SECRET_ASSIGN='^[[:space:]]*(export"),
    ("I1", INSTALLER, "secret gates back to a single optional `#`", "SECRET_ASSIGN='^[[:space:]]*(#[#[:space:]]*)?(export", "SECRET_ASSIGN='^[[:space:]]*#?[[:space:]]*(export"),
    ("I2", INSTALLER, "commented secret --option gate removed", 'if grep -Eiq "${SECRET_OPTION}" "${ENV_SRC}"; then', 'if false; then'),
    ("I3", INSTALLER, "wrapper gate on the contract removed", 'if ! wrapper_accepts "${ENV_SRC}"; then', 'if false; then'),
    ("I4", INSTALLER, "wrapper gate on an existing env file removed", '    elif ! wrapper_accepts "${ENV_DST}"; then', '    elif false; then'),
    ("I5", INSTALLER, "wrapper gate always passes", '    return "${rc}"\n}', '    return 0\n}'),
    ("M20", INSTALLER, "drift copy-aside's real command replaced by `true`",
     '(the drifted installed copy is kept as evidence)" cp -p "${dst}" "${aside}"', '(the drifted installed copy is kept as evidence)" true'),
    ("M21", INSTALLER, "drifted file not recorded", '        DRIFTED["${dst}"]=1\n', ''),
    ("I6", INSTALLER, "never-blessed file not recorded (no pre-install copy)", '            PREEXISTING["${dst}"]=1\n', ''),
    ("I7", INSTALLER, "pre-install copy-aside's real command replaced by `true`",
     '(a never-blessed file that differs from the repository is kept)" cp -p "${dst}" "${aside}"', '(a never-blessed file that differs from the repository is kept)" true'),
    ("I8", INSTALLER, "pre-install copy taken even when identical", '        if [[ -f "${dst}" ]] && ! cmp -s "${src}" "${dst}"; then', '        if [[ -f "${dst}" ]]; then'),
    ("I9", INSTALLER, "existing env file overwritten", 'if [[ -e "${ENV_DST}" ]]; then\n    say "kept existing', 'if false; then\n    say "kept existing'),
    ("I10", INSTALLER, "data-folder check removed", '[[ "$(stat -c \'%U:%a\' "${DATA_FOLDER}")" != "duplicati:700" ]]; then', 'false; then'),
    ("I11", INSTALLER, "bless writes the SOURCE checksum, not the installed file's",
     '''        printf '%s  %s\\n' "$(sha256sum "${dst}" | cut -d' ' -f1)" "${dst}" >> "${BLESSED}.new"''',
     '''        printf '%s  %s\\n' "$(sha256sum "${src}" | cut -d' ' -f1)" "${dst}" >> "${BLESSED}.new"'''),
    ("I12", INSTALLER, "credential mode check removed", '[[ "$(stat -c \'%U:%a\' "${CRED_DST}")" == "root:600" ]] ||', 'true ||'),
    ("I13", INSTALLER, "snapshot-destination NOTE removed", 'if [[ ! -d "${SNAP_DEST_DIR}" ]]; then', 'if false; then'),
    ("I14", INSTALLER, "guard hint loses `unset url id` (round 4: R4A N-1, R4B N-7)", 'cat <<\'EOF\'\nunset url id\n', 'cat <<\'EOF\'\n'),
    ("I15", INSTALLER, "systemctl daemon-reload dropped", 'act "systemctl daemon-reload" systemctl daemon-reload\n', ''),
    ("S1", SNAPSHOT, "snapshot left in WAL mode", '            dst_conn.execute("PRAGMA journal_mode=DELETE")\n', ''),
    ("S2", SNAPSHOT, "residue of earlier runs not removed", '    for path in stale:\n        if os.path.exists(path):\n            os.unlink(path)\n', ''),
    # Round 4 (wrapper 2.4.0, installer 1.4.0).
    ("R1", WRAPPER, "mount default back to `:-` (an empty override ignored)", '"${DUPLICATI_REQUIRE_MOUNT-/mnt/Backups}"', '"${DUPLICATI_REQUIRE_MOUNT:-/mnt/Backups}"'),
    ("R2", WRAPPER, "allow-list back to the non-existent suppress-welcome-page", '|webservice-suppress-welcome-page)(=|$)', '|suppress-welcome-page)(=|$)'),
    ("R3", WRAPPER, "only one trailing CR stripped (R4C X06's class)",
     "        while [[ \"${line}\" == *$'\\r' ]]; do line=\"${line%$'\\r'}\"; done", "        line=\"${line%$'\\r'}\""),
    ("R4", WRAPPER, "a CR inside a line no longer refused", "        [[ \"${line}\" != *$'\\r'* ]] || die", "        true || die"),
    ("R5", WRAPPER, "NUL check on the credential removed", '[[ "$(wc -c < "${cred}")" -eq "$(tr -d \'\\000\' < "${cred}" | wc -c)" ]] || die', 'true || die'),
    ("R6", WRAPPER, "quotes no longer stripped from KEY=VALUE (R4C X10)", '            value="$(strip_quotes "${BASH_REMATCH[3]}")"', '            value="${BASH_REMATCH[3]}"'),
    ("R7", WRAPPER, "env file overrides the environment (R4C X11)", '            if [[ -n "${!key+x}" ]]; then', '            if false; then'),
    ("R8", INSTALLER, "UNBLESSED no longer needs the switch", '            echo "UNBLESSED: installed ${dst} differs from the repository and was never blessed" >&2\n            drift=1\n', ''),
    ("R9", INSTALLER, "existing env file's owner/group/mode not checked", '    if [[ "${env_owner}" != root || "${env_group}" != duplicati ]] ||', '    if false &&'),
    ("R10", INSTALLER, "env mode check admits group write", '(8#${env_mode} & 8#022) != 0', '(8#${env_mode} & 8#002) != 0'),
    ("R11", INSTALLER, "real run does not say where the drifted copy went", '        (( DRY_RUN )) || say "kept the drifted ${dst} as ${aside}"\n', ''),
    ("R12", INSTALLER, "pre-install copy without -p (R4C X15)", '(a never-blessed file that differs from the repository is kept)" cp -p "${dst}" "${aside}"',
     '(a never-blessed file that differs from the repository is kept)" cp "${dst}" "${aside}"'),
    ("R13", INSTALLER, "key NOTE back to `test ! -s` without sudo", 'sudo test ! -e ${CRED_DST} &&', 'test ! -s ${CRED_DST} &&'),
    ("R14", INSTALLER, "prerequisites dropped from the hint", 'echo "     holds paused-until = 0, read back with startup-delay; the web credential is written"\n', ''),
    ("R16", WRAPPER, "allow-list loses its (=|$) terminator (R4C X01, re-anchored after the rename)",
     "|webservice-suppress-welcome-page)(=|$)'", "|webservice-suppress-welcome-page)'"),
    # Round 5 (installer 1.5.0): R5A's F01 and F07-F11, re-anchored on the new code, plus the new behaviours.
    ("R17", WRAPPER, "production default mount emptied (R5A F01)", '"${DUPLICATI_REQUIRE_MOUNT-/mnt/Backups}"', '"${DUPLICATI_REQUIRE_MOUNT-}"'),
    ("R18", INSTALLER, "root:root 0640 accepted -- the group dropped (R5A F07)", '        root:duplicati:640|duplicati:duplicati:600) ;;', '        root:duplicati:640|root:root:640|duplicati:duplicati:600) ;;'),
    ("R19", INSTALLER, "other-readable 0644 accepted (R5A NIT-1)", '        root:duplicati:640|duplicati:duplicati:600) ;;', '        root:duplicati:640|root:duplicati:644|duplicati:duplicati:600) ;;'),
    ("R20", INSTALLER, "O-12's dissent form refused (R5A DEFECT-2)", '        root:duplicati:640|duplicati:duplicati:600) ;;', '        root:duplicati:640) ;;'),
    ("R21", INSTALLER, "group-writable 0660 accepted (R5A F08)", '        root:duplicati:640|duplicati:duplicati:600) ;;', '        root:duplicati:640|root:duplicati:660|duplicati:duplicati:600) ;;'),
    ("R22", INSTALLER, "mode refusal does not exit on a real run (R5A F10)",
     '                echo "REFUSING: ${ENV_DST} is ${env_meta}; the service reads it as duplicati -- make it ${ENV_MODES_ACCEPTED}" >&2\n                exit 2\n',
     '                echo "REFUSING: ${ENV_DST} is ${env_meta}; the service reads it as duplicati -- make it ${ENV_MODES_ACCEPTED}" >&2\n'),
    ("R23", INSTALLER, "meta not read from the file (R5A F11)", '    env_meta="$(stat -c \'%U:%G:%a\' "${ENV_DST}")"\n', '    env_meta="root:duplicati:640"\n'),
    ("R24", INSTALLER, "symlink check removed", 'if [[ -L "${ENV_DST}" ]]; then', 'if false; then'),
    ("R25", INSTALLER, "Running: pause again, not stop (R5A DEFECT-1)", 'If it reads Running, stop the unit at once"', 'If it reads Running, pause at once"'),
    ("R26", INSTALLER, "step 10's restart dropped from the hint (R5B N-1)",
     'echo "  5. Then, on A0, A2 and B, restart the unit before resume (step 10): sudo systemctl stop duplicati.service,"\n', ''),
    ("R27", INSTALLER, "Procedure A's …-key.new dropped from the NOTE (R5A NIT-2)", ', and a random one at ${CRED_DST}.new, which P0.5b swaps in -- the same command with .new', ''),
    ("R15", INSTALLER, "wrapper_accepts no longer blanks the mount (host mount decides)", 'DUPLICATI_DATA_FOLDER="${scratch}" DUPLICATI_REQUIRE_MOUNT= \\', 'DUPLICATI_DATA_FOLDER="${scratch}" \\'),
]


def run(tree: Path, targets: list[str], path_prefix: str | None = None) -> tuple[bool, str]:
    path = f"{path_prefix}:/usr/bin:/bin" if path_prefix else "/usr/bin:/bin"
    r = subprocess.run([sys.executable, "-m", "unittest", *targets], cwd=tree, capture_output=True, text=True,
                       env={"PATH": path, "PYTHONDONTWRITEBYTECODE": "1", "HOME": str(tree)}, timeout=1800)
    fails = sorted(set(re.findall(r"^(?:FAIL|ERROR): (\w+) ", r.stderr, re.M)))
    tail = " ".join(ln for ln in r.stderr.splitlines() if ln.startswith(("Ran ", "OK", "FAILED")))
    return r.returncode == 0, tail + (f" -- failing: {', '.join(fails)}" if fails else "")


def mutate(tree: Path, mutants, targets: list[str], path_prefix: str | None = None) -> None:
    ok, line = run(tree, targets, path_prefix)
    print(f"baseline: {'PASS' if ok else 'FAIL'} [{line}]")
    if not ok:
        sys.exit("baseline does not pass; mutation counts would be meaningless")
    killed = 0
    for mid, rel, desc, old, new in mutants:
        path = tree / rel
        orig = path.read_bytes()
        text = orig.decode()
        n = text.count(old)
        if n != 1:
            print(f"{mid}: anchor found {n}x -- SKIPPED ({desc})")
            continue
        path.write_text(text.replace(old, new), encoding="utf-8")
        try:
            ok, line = run(tree, targets, path_prefix)
        finally:
            path.write_bytes(orig)
        killed += not ok
        print(f"{mid} {'KILLED  ' if not ok else 'SURVIVED'} {desc} [{line}]")
    print(f"killed {killed} of {len(mutants)}")


NEEDED = ("tests/redacted_env.py", CONTRACT_SUITE, WRAPPER, INSTALLER, SNAPSHOT,
          "util/systemd/duplicati.service", "util/systemd/duplicati.default", "util/yamaguchi-pre-backup-guard.bash",
          "util/systemd/duplicati-env.contract", "util/systemd/yamaguchi-server-db-snapshot.service",
          "util/systemd/yamaguchi-server-db-snapshot.timer")
FIXTURE = ("tests/fixtures/duplicati_2.4.0.0_server_options.txt",)
CISIM_SUITES = [CONTRACT_SUITE, REAL_SUITE, "tests/test_backup_rekey_real_path.py", "tests/test_clear_stop_backup_design.py"]


def minimal_copy(src: Path, dst: Path, extra: tuple[str, ...] = ()) -> None:
    """Only what the targeted suites read -- not the whole 190 MB tree."""
    for rel in NEEDED + extra:
        (dst / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src / rel, dst / rel)


def main() -> int:
    scratch, frozen, worktree, mode = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
    tree = scratch / f"tree_{mode}"
    if tree.exists():
        shutil.rmtree(tree)
    if mode == "before":
        minimal_copy(frozen, tree)
        mod = CONTRACT_SUITE[:-3].replace("/", ".")
        mutate(tree, BEFORE, [f"{mod}.WrapperEnvContract", f"{mod}.InstallerDriftGate"])
    elif mode == "failbefore":
        # <frozen-tree> is whichever commit the new tests must fail against (c3d0e890 for round 3, a0ff619c for round 4).
        minimal_copy(frozen, tree)
        for rel in (CONTRACT_SUITE, REAL_SUITE) + FIXTURE:
            (tree / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(worktree / rel, tree / rel)
        ok, line = run(tree, [f"{CONTRACT_SUITE[:-3].replace('/', '.')}.WrapperEnvContract", f"{CONTRACT_SUITE[:-3].replace('/', '.')}.InstallerDriftGate", REAL_SUITE])
        print(f"new tests against the FROZEN code: {'PASS' if ok else 'FAIL'} [{line}]")
    elif mode == "after":
        minimal_copy(worktree, tree, (REAL_SUITE,) + FIXTURE)
        mod = CONTRACT_SUITE[:-3].replace("/", ".")
        only = set(sys.argv[5:])  # optional mutant ids
        # Run as ci-sim (1.2.0): every mutant is judged with /mnt/Backups reading "not a mountpoint".
        stub_dir = tree / ".cisim-bin"
        stub_dir.mkdir()
        (stub_dir / "mountpoint").write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
        (stub_dir / "mountpoint").chmod(0o755)
        mutate(tree, [m for m in AFTER if not only or m[0] in only], [f"{mod}.WrapperEnvContract", f"{mod}.InstallerDriftGate", REAL_SUITE], str(stub_dir))
    elif mode == "r5a":
        # R5A's own mutants (util/ad-hoc/2026-10-08_backup-phase-b-round4/r5a-bin/r5a_mutants.py), unchanged, on a full
        # worktree copy with the `mountpoint` stub first on PATH: its run() hard-codes PATH, so it is wrapped here.
        # Remaining argv: mutant ids. R5A built its ci-sim by editing the wrapper default, which round 5's F01 pin now
        # refuses by design; F01 is therefore re-anchored on the production default before the run.
        import importlib.util
        shutil.copytree(worktree, tree, symlinks=True, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
        stub_dir = tree / ".cisim-bin"
        stub_dir.mkdir()
        (stub_dir / "mountpoint").write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
        (stub_dir / "mountpoint").chmod(0o755)
        spec = importlib.util.spec_from_file_location("r5a_mutants", worktree / "util/ad-hoc/2026-10-08_backup-phase-b-round4/r5a-bin/r5a_mutants.py")
        r5a = importlib.util.module_from_spec(spec)
        sys.modules["r5a_mutants"] = r5a
        spec.loader.exec_module(r5a)
        r5a.M = [(m[0], m[1], m[2], m[3].replace("/nonexistent-r5a/Backups", "/mnt/Backups"), m[4]) for m in r5a.M]
        r5a.run = lambda t, suites: run(t, suites, str(stub_dir))
        sys.argv = [sys.argv[0], str(tree), *sys.argv[5:]]
        r5a.main()
    elif mode == "r6":
        # Round 6's mutants (util/ad-hoc/2026-10-08_backup-phase-b-round4/r6-bin/r6_mutants.py), unchanged except that
        # only the ids named in argv run (lane C1 owns N07-N10, the installer's), and its hard-coded PATH gets the
        # ci-sim `mountpoint` stub first.
        import importlib.util
        shutil.copytree(worktree, tree, symlinks=True, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
        stub_dir = tree / ".cisim-bin"
        stub_dir.mkdir()
        (stub_dir / "mountpoint").write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
        (stub_dir / "mountpoint").chmod(0o755)
        spec = importlib.util.spec_from_file_location("r6_mutants", worktree / "util/ad-hoc/2026-10-08_backup-phase-b-round4/r6-bin/r6_mutants.py")
        r6 = importlib.util.module_from_spec(spec)
        sys.modules["r6_mutants"] = r6
        spec.loader.exec_module(r6)
        only = set(sys.argv[5:])
        r6.M = [m for m in r6.M if not only or m[0] in only]

        r6.run = lambda t, suites: run(t, suites, str(stub_dir))
        sys.argv = [sys.argv[0], str(tree)]
        r6.main()
    elif mode == "cisim":
        # R4C's ci-sim: a host where /mnt/Backups is NOT a mountpoint, simulated by pointing the wrapper's
        # default at a path that does not exist, in a full copy of the worktree. The four Phase B suites run whole.
        # 1.2.0: absence is simulated by a `mountpoint` stub that always answers "not a mountpoint", first on
        # PATH -- NOT by editing the wrapper's default, which round 5 pins (R5A F01) and which an edit would
        # therefore fail by construction. Every suite inherits this PATH.
        shutil.copytree(worktree, tree, symlinks=True, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
        stub_dir = tree / ".cisim-bin"
        stub_dir.mkdir()
        (stub_dir / "mountpoint").write_text("#!/usr/bin/env bash\nexit 1\n", encoding="utf-8")
        (stub_dir / "mountpoint").chmod(0o755)
        print(f"ci-sim PATH stub: {stub_dir}/mountpoint (exit 1 for every path)")
        for suite in CISIM_SUITES:
            ok, line = run(tree, [suite], path_prefix=str(stub_dir))
            print(f"ci-sim {suite}: {'PASS' if ok else 'FAIL'} [{line}]")
    else:
        sys.exit(f"unknown mode {mode}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
