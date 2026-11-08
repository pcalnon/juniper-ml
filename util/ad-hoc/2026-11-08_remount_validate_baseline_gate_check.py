#!/usr/bin/env python3
"""
Check the remount validator's baseline gate, then show by mutation that the checks catch a broken gate.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — remediation validation (test and test-efficacy evidence)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-11-07_securityfs_remount_validate.bash,
         notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-API-FILESYSTEM-REMOUNT-RUNBOOK.md (step 4),
         notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-SECURITYFS-UNMOUNT-ROOT-CAUSE-ANALYSIS.md (§14)

On 2026-11-08 the runbook's step 4 compared the remediated host against an empty file, and the validator
printed 22 "UNEXPECTED" differences for a host on which nothing unexpected had changed. The validator now
refuses a baseline that is not a fingerprint. The cases below check that it refuses each kind of
non-fingerprint, that it still accepts a real one, and that ``verify`` refuses before any efficacy check
runs. Each seeded defect of the gate (MUTANTS) is then run against the same cases. A defect the cases do
not catch is reported as SURVIVED.

Isolation: every run gets a PATH whose ``docker`` and ``snap`` are stubs that exit 97, an empty
JUNIPER_DEPLOY_DIR and a nonexistent VALIDATE_IMAGE. So even a mutant that wrongly reaches the efficacy
checks starts no container and runs no snap. C14 also stubs ``awk``, to show that a key check that fails
is a refusal, not a pass. The two capture cases read this host's state, read-only, as runbook step 1 does. Files go under the repo's tmp/ directory, never the system temp directory, in a
fresh directory per validator version, so no run can see another's files.

Usage: python3 util/ad-hoc/2026-11-08_remount_validate_baseline_gate_check.py
Exit: 0 every case passed on the real validator and every mutant was killed; 1 otherwise.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VALIDATOR = REPO / "util" / "ad-hoc" / "2026-11-07_securityfs_remount_validate.bash"
EVIDENCE = REPO / "reports" / "2026-11-07_yamaguchi-securityfs-unmount"
FINGERPRINT = EVIDENCE / "2026-11-08T0215Z_remount-fingerprint-incident-state.txt"
PROBE_REPORT = EVIDENCE / "2026-11-08T0135Z_probe-before-remediation.txt"
STUB = '#!/usr/bin/env bash\necho "gate-check stub: $(basename "$0") must not run" >&2\nexit 97\n'

# (id, mode, input, expected exit, text the output must contain, extra command to stub or None).
# Run in order: C12 checks C11's capture. C3 and C10 are the cases that caught the first gate passing the
# probe's report (…_first-gate-FAILED.txt in the evidence directory).
CASES = [
    ("C1", "check", "missing", 2, "no such file", None),
    ("C2", "check", "empty", 2, "empty file", None),
    ("C3", "check", "probe report", 2, "not a fingerprint: 17 of 17 required keys missing", None),
    ("C4", "check", "fingerprint minus pid.dockerd", 2, "1 of 17 required keys missing, the first being pid.dockerd", None),
    ("C5", "check", "fingerprint minus snap_service.snap.etcd.etcd", 2, "the first being snap_service.snap.etcd.etcd", None),
    ("C6", "check", "fingerprint minus mount./sys/fs/bpf", 2, "the first being mount./sys/fs/bpf", None),
    ("C7", "check", "committed fingerprint", 0, "is a usable baseline (31 lines, all 17 required keys)", None),
    ("C8", "verify", "missing", 2, "no such file", None),
    ("C9", "verify", "empty", 2, "empty file", None),
    ("C10", "verify", "probe report", 2, "not a fingerprint", None),
    ("C11", "capture", "fresh capture", 0, "(a usable baseline: all 17 required keys)", None),
    ("C12", "check", "fresh capture", 0, "is a usable baseline", None),
    ("C13", "capture", "capture into a missing directory", 1, "is NOT a usable baseline", None),
    ("C14", "check", "committed fingerprint", 2, "the key check itself failed", "awk"),
]

# (name, old, new): `old` must occur exactly once in the validator.
MUTANTS = [
    ("verify skips the baseline gate", '        gate verify "$file"\n', "        :\n"),
    ("check accepts any file", '        gate check "$file"\n', "        :\n"),
    ("a missing file is not reported as missing", '    if [[ ! -r "$file" ]]; then echo "no such file"; return; fi\n', "    :\n"),
    ("an empty file is not reported as empty", '    if [[ ! -s "$file" ]]; then echo "empty file"; return; fi\n', "    :\n"),
    ("required keys are never checked", "if (!(want[i] in have))", "if (0)"),
    ("the snap service keys are not required", 'for unit in "${SNAP_K8S_SERVICES[@]}"; do REQUIRED_KEYS+=("snap_service.$unit"); done\n', ":\n"),
    ("the mount keys are not required", 'for where in "${API_MOUNT_POINTS[@]}"; do REQUIRED_KEYS+=("mount.$where"); done\n', ":\n"),
    ("a refused baseline exits 0", "    exit 2  # refuse: not a usable baseline\n", "    exit 0  # refuse: not a usable baseline\n"),
    ("capture does not check its own output", '        if [[ "$problem" != none ]]; then\n            echo "capture:', '        if false; then\n            echo "capture:'),
    ("a failed key check counts as no keys missing", '        || { echo "the key check itself failed"; return; }\n', "        || true\n"),
]
DAEMON_STUBS = ("docker", "snap")  # must never run, in any case


def build_inputs(work: Path) -> dict[str, Path]:
    """Create every case input in WORK, a directory no other run uses."""
    lines = FINGERPRINT.read_text(encoding="utf-8").splitlines(keepends=True)

    def without(prefix: str) -> str:
        kept = [line for line in lines if not line.startswith(prefix)]
        if len(kept) != len(lines) - 1:
            raise SystemExit(f"fixture error: {prefix!r} does not start exactly one line of {FINGERPRINT.name}")
        return "".join(kept)

    work.mkdir(parents=True)
    inputs = {
        "missing": work / "no-such-baseline.txt",
        "empty": work / "empty.txt",
        "probe report": PROBE_REPORT,
        "fingerprint minus pid.dockerd": work / "without-pid.dockerd.txt",
        "fingerprint minus snap_service.snap.etcd.etcd": work / "without-snap-etcd.txt",
        "fingerprint minus mount./sys/fs/bpf": work / "without-mount-bpf.txt",
        "committed fingerprint": FINGERPRINT,
        "fresh capture": work / "fresh-capture.txt",
        "capture into a missing directory": work / "no-such-directory" / "before.txt",
    }
    inputs["empty"].write_text("", encoding="utf-8")
    inputs["fingerprint minus pid.dockerd"].write_text(without("pid.dockerd="), encoding="utf-8")
    inputs["fingerprint minus snap_service.snap.etcd.etcd"].write_text(without("snap_service.snap.etcd.etcd="), encoding="utf-8")
    inputs["fingerprint minus mount./sys/fs/bpf"].write_text(without("mount./sys/fs/bpf="), encoding="utf-8")
    return inputs


def make_stubs(directory: Path, names: tuple[str, ...]) -> Path:
    """Write a failing stub for each command in NAMES into DIRECTORY, and return DIRECTORY."""
    directory.mkdir()
    for name in names:
        stub = directory / name
        stub.write_text(STUB, encoding="utf-8")
        stub.chmod(0o755)
    return directory


def run_cases(validator: Path, work: Path, env: dict[str, str], extra_stubs: dict[str, Path]) -> list[tuple[str, str, str, int, str | None]]:
    """Run every case against VALIDATOR. Each result: (id, mode, input, exit code, failure reason or None)."""
    inputs = build_inputs(work)
    results = []
    for case_id, mode, input_name, expected_exit, expected_text, extra in CASES:
        case_env = env if extra is None else dict(env, PATH=f"{extra_stubs[extra]}{os.pathsep}{env['PATH']}")
        proc = subprocess.run(["bash", str(validator), mode, str(inputs[input_name])], capture_output=True, text=True, env=case_env, timeout=300, check=False)
        output = proc.stdout + proc.stderr
        reason = None
        if proc.returncode != expected_exit:
            reason = f"exit {proc.returncode}, expected {expected_exit}"
        elif expected_text not in output:
            reason = f"output lacks {expected_text!r}"
        elif mode == "verify" and "== efficacy" in output:
            reason = "the efficacy checks ran"
        elif any(f"gate-check stub: {name} " in output for name in DAEMON_STUBS):
            reason = "a stubbed daemon command (docker or snap) ran"
        results.append((case_id, mode, input_name, proc.returncode, reason))
    return results


def main() -> int:
    source = VALIDATOR.read_text(encoding="utf-8")
    tmp_root = Path(os.environ.get("TMPDIR") or (REPO / "tmp"))
    tmp_root.mkdir(parents=True, exist_ok=True)
    failures = 0
    print(f"# remount validator baseline-gate check, run {datetime.now(timezone.utc):%Y-%m-%dT%H:%M:%SZ}")
    print(f"# validator: {VALIDATOR.relative_to(REPO)}  sha256 {hashlib.sha256(source.encode('utf-8')).hexdigest()}")
    print(f"# fixtures:  {FINGERPRINT.relative_to(REPO)}, {PROBE_REPORT.relative_to(REPO)}")
    with tempfile.TemporaryDirectory(dir=tmp_root, prefix="remount_gate_check_") as work_name:
        work = Path(work_name)
        stubs = make_stubs(work / "stubs", DAEMON_STUBS)
        extra_stubs = {"awk": make_stubs(work / "stubs-awk", ("awk",))}
        empty_deploy = work / "empty-deploy"
        empty_deploy.mkdir()
        env = dict(os.environ, PATH=f"{stubs}{os.pathsep}{os.environ.get('PATH', '')}", JUNIPER_DEPLOY_DIR=str(empty_deploy), VALIDATE_IMAGE="gate-check.invalid/none:0")

        print("\n== cases, against the real validator")
        for case_id, mode, input_name, code, reason in run_cases(VALIDATOR, work / "real", env, extra_stubs):
            verdict = "PASS" if reason is None else "FAIL"
            print(f"[{verdict}] {case_id:<4} {mode:<8} {input_name:<46} exit {code}" + ("" if reason is None else f"  -- {reason}"))
            failures += reason is not None

        print("\n== seeded defects in the gate (each must make at least one case fail)")
        for index, (name, old, new) in enumerate(MUTANTS, 1):
            if source.count(old) != 1:
                print(f"[EDIT-FAILED] M{index} {name}: its anchor occurs {source.count(old)} times")
                failures += 1
                continue
            mutant = work / f"mutant_{index:02d}.bash"
            mutant.write_text(source.replace(old, new), encoding="utf-8")
            caught = [case_id for case_id, _, _, _, reason in run_cases(mutant, work / f"m{index:02d}", env, extra_stubs) if reason is not None]
            if caught:
                print(f"[KILLED]   M{index} {name}: caught by {', '.join(caught)}")
            else:
                print(f"[SURVIVED] M{index} {name}")
                failures += 1

    print(f"\n== {'PASS' if failures == 0 else f'FAIL ({failures})'}: {len(CASES)} cases, {len(MUTANTS)} seeded defects")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
