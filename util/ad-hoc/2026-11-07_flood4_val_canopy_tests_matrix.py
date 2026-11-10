#!/usr/bin/env python3
"""
Validation matrix for the juniper-canopy flood-4 TESTS carrier: macOS base64 simulation, git-config hostility, mutants.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-canopy tests carrier VALIDATION)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy#789 #792 #794 #795; flood-4 validation brief (test correctness / non-vacuity lens)

Runs ONLY in the validator's own mutation worktree (argument 1), never in the carrier. Three parts:

1. #792 base64: two simulated macOS base64 programs (an Apple-like one that takes -w but refuses a FILE
   operand, as CI's macos-26-arm64 job 126503186102 shows; and one that also refuses -w) are put first on
   PATH by 2026-11-07_flood4_val_canopy_b64sim_plugin, with sys.platform simulated as darwin or left as
   linux, with the stand-in enabled or disabled. Each run records which base64 every case used.
2. #794 git config: test_agents_md_date_check.py and test_lockfile_regen_empty_payload.py under hostile
   global configs (signing on with a bogus program, ssh signing, no identity + useConfigOnly + another
   default branch, color.ui=always, a hooksPath whose hooks fail).
3. Mutants of the workflow lines the carried tests pin (one or more per carried file, none from the
   builder's list), each restored byte-for-byte (sha256 before == after).

Transient fixture programs (fake base64, failing hooks) are created with tempfile under $TMPDIR (the repo
tmp/, never the system temp dir); config files and logs go to the scratch dir (argument 2).

    python3 2026-11-07_flood4_val_canopy_tests_matrix.py <mutation worktree> <scratch dir> <macOS job log>
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ADHOC = Path(__file__).resolve().parent
RUNNER = ADHOC / "2026-11-07_flood4_val_canopy_run_pytest.py"
B64PLUGIN = "2026-11-07_flood4_val_canopy_b64sim_plugin"
LOCK_TEST = "src/tests/regression/test_lockfile_regen_empty_payload.py"
DATE_TEST = "src/tests/unit/test_agents_md_date_check.py"
BANDIT_TEST = "src/tests/regression/test_bandit_sarif_upload.py"
CODECOV_TEST = "src/tests/regression/test_codecov_token_upload.py"

APPLE_BASE64 = r'''#!/usr/bin/env python3
# Simulated macOS (Apple) base64 for a validation run. Mirrors what CI's macos-26-arm64 runner printed for
# `base64 -w0 requirements.lock`: "-w" is taken, the FILE operand is refused with "invalid argument".
import base64
import sys

USAGE = "Usage:\tbase64 [-Ddh] [-b num] [-i in_file] [-o out_file]"
REJECT_W = REJECT_W_PLACEHOLDER
args = sys.argv[1:]
src = None
dst = None
i = 0
while i < len(args):
    arg = args[i]
    if arg.startswith("-w"):
        if REJECT_W:
            sys.stderr.write("base64: invalid option -- w\n" + USAGE + "\n")
            sys.exit(64)
        if arg == "-w":
            i += 1
    elif arg in ("-b", "-i", "-o"):
        if i + 1 >= len(args):
            sys.stderr.write(USAGE + "\n")
            sys.exit(64)
        if arg == "-i":
            src = args[i + 1]
        if arg == "-o":
            dst = args[i + 1]
        i += 1
    elif arg.startswith("-b"):
        pass
    else:
        sys.stderr.write("base64: invalid argument " + arg + "\n" + USAGE + "\n")
        sys.exit(64)
    i += 1
data = open(src, "rb").read() if src and src != "-" else sys.stdin.buffer.read()
text = base64.b64encode(data).decode("ascii") + "\n"
if dst and dst != "-":
    open(dst, "w").write(text)
else:
    sys.stdout.write(text)
'''

FAILING_HOOK = "#!/bin/sh\necho 'validation hook refused the commit' >&2\nexit 1\n"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(worktree: Path, scratch: Path, name: str, tests: list[str], *, git_global: str = "devnull", env: dict | None = None, plugin: bool = False) -> dict:
    log = scratch / f"{name}.log"
    cmd = [sys.executable, str(RUNNER), "--root", str(worktree), "--cwd", "root", "--git-global", git_global, "--log", str(log)]
    for key, value in (env or {}).items():
        cmd += ["--env", f"{key}={value}"]
    if plugin:
        cmd += ["--plugin", B64PLUGIN]
    cmd += ["--", "-m", "not requires_cascor and not requires_server and not slow", *tests, "--timeout=60"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    text = log.read_text(encoding="utf-8", errors="replace")
    failed = sorted(set(re.findall(r"^FAILED (\S+(?: \S+)*?)(?: - |$)", text, flags=re.M)))
    summary = [line for line in proc.stdout.splitlines() if line.startswith("summary:")]
    origin = [line for line in proc.stdout.splitlines() if "modules-from-primary" in line]
    return {"name": name, "exit": proc.returncode, "summary": summary[0] if summary else "", "failed": failed, "origin": origin, "log": str(log)}


def b64_report(path: Path) -> dict:
    rows = path.read_text(encoding="utf-8").splitlines() if path.is_file() else []
    counts: dict[str, int] = {}
    for row in rows:
        kind = row.split("\t", 1)[0]
        counts[kind] = counts.get(kind, 0) + 1
    return {"counts": counts, "rows": rows}


def mutate(path: Path, old: str, new: str) -> tuple[str, bytes]:
    original = path.read_bytes()
    text = original.decode("utf-8")
    assert text.count(old) == 1, f"{path}: {old!r} occurs {text.count(old)} times"
    path.write_text(text.replace(old, new), encoding="utf-8")
    return hashlib.sha256(original).hexdigest(), original


def restore(path: Path, original: bytes, before: str) -> bool:
    path.write_bytes(original)
    return sha(path) == before


def main() -> int:
    worktree, scratch, joblog = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3])
    tmp_root = os.environ.get("TMPDIR", "")
    assert tmp_root and not tmp_root.startswith(("/tmp", "/var/tmp")), f"refusing TMPDIR={tmp_root!r}"  # tmp-path-literal: allow (guard: refuses a TMPDIR under the system temp dir)
    fixtures = Path(tempfile.mkdtemp(prefix="flood4-val-canopy-fixtures-", dir=tmp_root))
    results: dict = {"worktree": str(worktree), "fixtures_dir": str(fixtures), "b64": [], "gitconfig": [], "mutants": []}

    ci_failed = sorted(set(re.findall(r"FAILED (src/tests/regression/test_lockfile_regen_empty_payload\.py::\S+(?: [^-\n]\S*)*?) - ", joblog.read_text(encoding="utf-8", errors="replace"))))
    results["ci_macos_failed_ids"] = ci_failed

    fakes = {}
    for variant, reject_w in (("apple", "False"), ("rejects-w", "True")):
        bindir = fixtures / f"bsd-{variant}"
        bindir.mkdir()
        exe = bindir / "base64"
        exe.write_text(APPLE_BASE64.replace("REJECT_W_PLACEHOLDER", reject_w), encoding="utf-8")
        exe.chmod(0o755)
        fakes[variant] = bindir
    probe = subprocess.run([str(fakes["apple"] / "base64"), "-w0", "requirements.lock"], capture_output=True, text=True, check=False)
    results["fake_apple_probe"] = {"rc": probe.returncode, "stderr": probe.stderr.strip()}

    # Part 1 -- #792 on a simulated macOS leg.
    scenarios = [
        ("b64_darwin_apple_standin", {"VAL_PREPEND_PATH": str(fakes["apple"]), "VAL_SIM_PLATFORM": "darwin"}),
        ("b64_darwin_apple_no_standin", {"VAL_PREPEND_PATH": str(fakes["apple"]), "VAL_SIM_PLATFORM": "darwin", "VAL_DISABLE_STANDIN": "1"}),
        ("b64_darwin_rejectsw_standin", {"VAL_PREPEND_PATH": str(fakes["rejects-w"]), "VAL_SIM_PLATFORM": "darwin"}),
        ("b64_darwin_rejectsw_no_standin", {"VAL_PREPEND_PATH": str(fakes["rejects-w"]), "VAL_SIM_PLATFORM": "darwin", "VAL_DISABLE_STANDIN": "1"}),
        ("b64_linux_apple", {"VAL_PREPEND_PATH": str(fakes["apple"])}),
        ("b64_linux_real", {}),
        ("b64_darwin_real_base64", {"VAL_SIM_PLATFORM": "darwin"}),
    ]
    for name, env in scenarios:
        report = scratch / f"{name}.b64report.txt"
        report.unlink(missing_ok=True)
        env = {**env, "VAL_B64_REPORT": str(report)}
        row = run(worktree, scratch, name, [LOCK_TEST], env=env, plugin=True)
        row["base64_used"] = b64_report(report)
        row["failed_equals_ci_macos"] = row["failed"] == ci_failed
        results["b64"].append(row)

    # Part 2 -- hostile global git configs.
    hooks = fixtures / "hooks"
    hooks.mkdir()
    for hook in ("pre-commit", "commit-msg"):
        (hooks / hook).write_text(FAILING_HOOK, encoding="utf-8")
        (hooks / hook).chmod(0o755)
    configs = {
        "gitcfg_signing_bogus": f"[commit]\n\tgpgsign = true\n[tag]\n\tgpgsign = true\n[gpg]\n\tprogram = {fixtures}/no-such-gpg-program\n[user]\n\tsigningkey = DEADBEEFDEADBEEF\n",
        "gitcfg_signing_ssh_bogus": f"[commit]\n\tgpgsign = true\n[tag]\n\tgpgsign = true\n[gpg]\n\tformat = ssh\n[gpg \"ssh\"]\n\tprogram = {fixtures}/no-such-ssh-keygen\n[user]\n\tsigningkey = {fixtures}/no-such-key.pub\n",
        "gitcfg_noident_useconfigonly_trunk": "[init]\n\tdefaultBranch = trunk\n[user]\n\tuseConfigOnly = true\n",
        "gitcfg_color_always": "[color]\n\tui = always\n",
        "gitcfg_hookspath_failing": f"[core]\n\thooksPath = {hooks}\n",
    }
    for name, body in configs.items():
        cfg = scratch / f"{name}.txt"
        cfg.write_text(body, encoding="utf-8")
        row = run(worktree, scratch, f"{name}_run", [DATE_TEST, LOCK_TEST], git_global=str(cfg))
        results["gitconfig"].append(row)

    # Part 3 -- mutants (restored byte-for-byte). The #792 mutants run on the simulated macOS leg WITH the
    # stand-in, so a kill proves that leg is not vacuous; none of them lets an unrelocated case reach jq.
    mac_env = {"VAL_PREPEND_PATH": str(fakes["apple"]), "VAL_SIM_PLATFORM": "darwin"}
    mutants = [
        ("mut789_findings_recorded_false", ".github/workflows/ci.yml", 'echo "bandit_found_issues=true" >> "$GITHUB_OUTPUT"', 'echo "bandit_found_issues=false" >> "$GITHUB_OUTPUT"', [BANDIT_TEST], "devnull", None),
        ("mut795_files_stale_path", ".github/workflows/ci.yml", "          files: reports/coverage.xml\n", "          files: ./coverage.xml\n", [CODECOV_TEST], "devnull", None),
        ("mut792_headline_swapped_on_mac_sim", ".github/workflows/lockfile-update.yml", 'if [[ "${EVENT_NAME}" == "pull_request" ]]; then', 'if [[ "${EVENT_NAME}" != "pull_request" ]]; then', [LOCK_TEST], "devnull", mac_env),
        ("mut792_head_oid_is_tree_on_mac_sim", ".github/workflows/lockfile-update.yml", "HEAD_OID=$(git rev-parse HEAD)", "HEAD_OID=$(git rev-parse 'HEAD^{tree}')", [LOCK_TEST], "devnull", mac_env),
        ("mut794_two_dot_diff_under_signing_cfg", ".github/workflows/agents-md-touch-up.yml", 'git diff "${BASE_SHA}...HEAD" -- AGENTS.md', 'git diff "${BASE_SHA}" HEAD -- AGENTS.md', [DATE_TEST], str(scratch / "gitcfg_signing_bogus.txt"), None),
    ]
    for name, rel, old, new, tests, git_global, env in mutants:
        target = worktree / rel
        before, original = mutate(target, old, new)
        try:
            report = scratch / f"{name}.b64report.txt"
            report.unlink(missing_ok=True)
            run_env = {**env, "VAL_B64_REPORT": str(report)} if env else None
            row = run(worktree, scratch, name, tests, git_global=git_global, env=run_env, plugin=bool(env))
            if env:
                row["base64_used"] = b64_report(report)
        finally:
            restored = restore(target, original, before)
        row.update({"target": f"{rel}", "old": old.strip(), "new": new.strip(), "sha256_before": before, "restored_byte_for_byte": restored, "killed": row["exit"] != 0 and bool(row["failed"])})
        results["mutants"].append(row)

    out = scratch / "val_matrix_summary.json"
    out.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")
    for section in ("b64", "gitconfig", "mutants"):
        for row in results[section]:
            extra = ""
            if "base64_used" in row:
                extra = f" base64_used={row['base64_used']['counts']}"
            if "failed_equals_ci_macos" in row:
                extra += f" failed==CI-macOS:{row['failed_equals_ci_macos']}"
            if "killed" in row:
                extra += f" killed={row['killed']} restored={row['restored_byte_for_byte']}"
            print(f"{section:9} {row['name']}: exit={row['exit']} {row['summary']}{extra} failed={len(row['failed'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
