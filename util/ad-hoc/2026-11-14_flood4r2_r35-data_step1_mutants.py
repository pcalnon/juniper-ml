#!/usr/bin/env python3
"""Apply the twelve blocking-wiring mutants to juniper-data's ci.yml and run its gitleaks test file under each.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use helper of the Cursor flood-4 disposition arc: the juniper-data back-port of the
             gitleaks pull-request scan's blocking-wiring pins)
Author:      Paul Calnon
Created:     2026-11-14
Status:      ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related:     juniper-data#530, juniper-data-client#260 (its validator's finding F1 named these twelve mutants)
Version:     0.1.0
License:     MIT License

WHAT IT DOES
------------
The twelve mutants are the ones juniper-data-client#260's validator found that its first test build left alive, each
an exact-once edit of .github/workflows/ci.yml (the ids are the validator's): continue-on-error on the scan step
(V01), on the job (V02) and on the install step (V08); a job-level `if:` (V03); a job rename (V21); the self-test's
`run:` with `|| true` (V04) and with `-k "not real_engine"` (V05); the digest check with `|| true` (V06) and against a
hash of the downloaded file itself (V07); the report upload without `if: always()` (V09) and with its path narrowed
(V10); the git filter unanchored (V19).

Under the unmutated file (baseline) and under each mutant the test file runs in two lanes, each a fresh pytest process:
  unit       the unit lane's selection and options (`-m "unit and not slow"`, `--timeout=60`) with NO gitleaks binary
             reachable (GITLEAKS_BIN unset, none on PATH), as in CI's unit job: the real-engine cases skip there;
  self-test  the Security Scans self-test's command (`python -m pytest <file> -v`) with the real engine first on PATH
             and GITLEAKS_PARITY_REQUIRED=1, as that step runs it.
A mutant is KILLED when any case fails in either lane, and SURVIVED when both lanes are green.

SAFETY
------
--backup <dir> receives a copy of ci.yml and of the test file, with their sha256, before anything is mutated; ci.yml is
restored from memory in a `finally:` block after every mutant and its sha256 verified (then restored from the backup
copy if it still differs). __pycache__ directories under juniper_data/tests are deleted first, every child runs with
PYTHONDONTWRITEBYTECODE=1 and `-p no:cacheprovider`, and the six Sentry variables are set to "" in every child.

Usage:
    <stdlib python> util/ad-hoc/2026-11-14_flood4r2_r35-data_step1_mutants.py --worktree <juniper-data checkout>
        --python <interpreter with the repo's test deps> --engine <gitleaks 8.24.3 binary> --out <dir> --backup <dir>
        [--only V01,V02,...]

Exit 0 when the baseline is green in both lanes and every restore was exact; 1 otherwise. The verdicts are data:
read <out>/mutants.json.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess  # nosec B404 -- runs pytest with a fixed argv
import sys
import xml.etree.ElementTree as ElementTree  # nosec B405 -- parses the junit XML that our own pytest child wrote
from pathlib import Path

CI = Path(".github") / "workflows" / "ci.yml"
TEST_FILE = "juniper_data/tests/unit/test_gitleaks_config.py"
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
SCRUBBED = ("GITLEAKS_BIN", "GITLEAKS_CONFIG", "GITLEAKS_CONFIG_TOML", "GITLEAKS_PARITY_REQUIRED")

SCAN_IF = "        if: github.event_name == 'pull_request'\n        env:\n          BASE_SHA:"
INSTALL_IF = "        if: github.event_name == 'pull_request'\n        env:\n          GITLEAKS_VERSION:"
JOB_HEAD = "  security:\n    name: Security Scans\n    runs-on: ubuntu-latest\n    needs: [pre-commit]\n"
SELF_TEST = f"        run: python -m pytest {TEST_FILE} -v\n"
SHA_LINE = '          echo "${GITLEAKS_SHA256}  ${RUNNER_TEMP}/${asset}" | sha256sum --check --strict\n'
UPLOAD = "      - name: Upload Security Reports\n        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9  # v7.0.2\n        if: always()\n        with:\n          name: security-reports\n"
UPLOAD_PATH = "          name: security-reports\n          path: reports/security/\n"
COE = "        continue-on-error: true\n        env:"

#: (id, what the edit undoes, exact text occurring once in ci.yml, replacement)
MUTANTS: list[tuple[str, str, str, str]] = [
    ("V01", "continue-on-error on the pull-request scan step: a leak no longer fails the job", SCAN_IF, SCAN_IF.replace("        env:", COE, 1)),
    ("V02", "continue-on-error on the security job", JOB_HEAD, JOB_HEAD + "    continue-on-error: true\n"),
    ("V03", "a job-level if: the whole security job skips Dependabot", JOB_HEAD, JOB_HEAD + "    if: github.actor != 'dependabot[bot]'\n"),
    ("V04", "the self-test's failure is swallowed in its own shell (|| true)", SELF_TEST, SELF_TEST.replace(" -v\n", " -v || true\n")),
    ("V05", "the self-test deselects the real-engine cases (-k)", SELF_TEST, SELF_TEST.replace(" -v\n", ' -v -k "not real_engine"\n')),
    ("V06", "the digest check's failure is swallowed (|| true)", SHA_LINE, SHA_LINE.replace("--strict\n", "--strict || true\n")),
    ("V07", "the tarball is checked against its own hash, not the pinned digest", SHA_LINE, '          echo "$(sha256sum "${RUNNER_TEMP}/${asset}" | cut -d " " -f 1)  ${RUNNER_TEMP}/${asset}" | sha256sum --check --strict\n'),
    ("V08", "continue-on-error on the install step", INSTALL_IF, INSTALL_IF.replace("        env:", COE, 1)),
    ("V09", "the report upload no longer runs after a failed scan (if: always() dropped)", UPLOAD, UPLOAD.replace("        if: always()\n", "")),
    ("V10", "the report upload no longer includes the gitleaks report", UPLOAD_PATH, UPLOAD_PATH.replace("path: reports/security/\n", "path: reports/security/bandit.sarif\n")),
    ("V19", "the git filter deletes every line that holds the word remerge, not only git's notes", "sed -e '/^remerge /d'", "sed -e '/remerge/d'"),
    ("V21", "the security job is renamed (Security Scans is a required check)", "    name: Security Scans\n", "    name: Security\n"),
]


def sha256_bytes(data: bytes) -> str:
    """Return the hex SHA-256 of ``data``."""
    return hashlib.sha256(data).hexdigest()


def child_env(engine_dir: Path | None) -> dict[str, str]:
    """The environment of one pytest child: no scanner variables, empty Sentry variables, no bytecode."""
    env = {k: v for k, v in os.environ.items() if k not in SCRUBBED}
    env.update({name: "" for name in SENTRY_DSN_NAMES})
    env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/nonexistent/no-session-bus"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if engine_dir is not None:
        env["PATH"] = f"{engine_dir}{os.pathsep}{env.get('PATH', os.defpath)}"
        env["GITLEAKS_PARITY_REQUIRED"] = "1"
    return env


def lane_argv(python: str, lane: str, junit: Path, basetemp: Path) -> list[str]:
    """The pytest argv of a lane, with a junit report and a private basetemp added."""
    common = ["-p", "no:cacheprovider", f"--junitxml={junit}", f"--basetemp={basetemp}"]
    if lane == "unit":
        return [python, "-m", "pytest", "-m", "unit and not slow", TEST_FILE, "--timeout=60", *common]
    return [python, "-m", "pytest", TEST_FILE, "-v", *common]


def read_junit(junit: Path) -> dict[str, object]:
    """Counts and the failing / skipped case names from a junit XML file."""
    if not junit.is_file():
        return {"junit": "missing"}
    root = ElementTree.parse(junit).getroot()  # nosec B314 -- our own child's report
    failed: list[str] = []
    skipped: list[str] = []
    passed = 0
    for case in root.iter("testcase"):
        name = case.get("name", "?")
        if case.find("failure") is not None or case.find("error") is not None:
            failed.append(name)
        elif case.find("skipped") is not None:
            skipped.append(name)
        else:
            passed += 1
    return {"passed": passed, "failed": failed, "skipped_count": len(skipped), "skipped": skipped}


def run_lane(worktree: Path, python: str, lane: str, label: str, out: Path, engine_dir: Path | None) -> dict[str, object]:
    """Run one lane in a fresh process and summarise it."""
    junit = out / "junit" / f"{label}-{lane}.xml"
    junit.parent.mkdir(parents=True, exist_ok=True)
    basetemp = out / "basetemp" / f"{label}-{lane}"
    basetemp.parent.mkdir(parents=True, exist_ok=True)
    argv = lane_argv(python, lane, junit, basetemp)
    env = child_env(engine_dir if lane == "self-test" else None)
    proc = subprocess.run(argv, cwd=worktree, env=env, capture_output=True, text=True, timeout=900, check=False)  # nosec B603
    log = out / "logs" / f"{label}-{lane}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(f"$ {' '.join(argv)}\n(exit {proc.returncode})\n{proc.stdout}\n--- stderr ---\n{proc.stderr}", encoding="utf-8")
    summary: dict[str, object] = {"exit": proc.returncode, "log": str(log), "command": " ".join(argv[1:])}
    summary.update(read_junit(junit))
    return summary


def drop_pycache(worktree: Path) -> list[str]:
    """Delete every __pycache__ under juniper_data/tests and util/ad-hoc; return what was deleted."""
    removed = []
    for top in (worktree / "juniper_data" / "tests", worktree / "util" / "ad-hoc"):
        for cache in sorted(top.rglob("__pycache__")):
            shutil.rmtree(cache)
            removed.append(str(cache.relative_to(worktree)))
    return removed


def main(argv: list[str]) -> int:
    """Baseline, then each mutant, restoring ci.yml after every one."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--worktree", required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--engine", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--backup", required=True)
    parser.add_argument("--only", default="", help="comma-separated mutant ids (default: all twelve)")
    args = parser.parse_args(argv)
    worktree = Path(args.worktree).resolve()
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    backup = Path(args.backup).resolve()
    backup.mkdir(parents=True, exist_ok=True)
    ci_path = worktree / CI
    test_path = worktree / TEST_FILE
    original = ci_path.read_bytes()
    original_sha = sha256_bytes(original)
    test_sha = sha256_bytes(test_path.read_bytes())
    shutil.copyfile(ci_path, backup / "ci.yml")
    shutil.copyfile(test_path, backup / Path(TEST_FILE).name)
    (backup / "SHA256SUMS").write_text(f"{original_sha}  {CI.as_posix()}\n{test_sha}  {TEST_FILE}\n", encoding="utf-8")
    engine_dir = out / "engine-bin"
    engine_dir.mkdir(exist_ok=True)
    link = engine_dir / "gitleaks"
    if link.is_symlink() or link.exists():
        link.unlink()
    link.symlink_to(Path(args.engine).resolve())
    wanted = [m for m in MUTANTS if not args.only or m[0] in args.only.split(",")]
    result: dict[str, object] = {
        "worktree": str(worktree),
        "python": args.python,
        "engine": str(Path(args.engine).resolve()),
        "ci_yml_sha256": original_sha,
        "test_file_sha256": test_sha,
        "pycache_removed": drop_pycache(worktree),
        "lanes": {"unit": " ".join(lane_argv("python", "unit", Path("<junit>"), Path("<basetemp>"))[1:]), "self-test": " ".join(lane_argv("python", "self-test", Path("<junit>"), Path("<basetemp>"))[1:])},
        "baseline": {},
        "mutants": [],
        "restores_exact": True,
    }
    text = original.decode("utf-8")
    result["baseline"] = {lane: run_lane(worktree, args.python, lane, "baseline", out, engine_dir) for lane in ("unit", "self-test")}
    ok = all(lane["exit"] == 0 and not lane.get("failed") for lane in result["baseline"].values())
    (out / "mutants.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    for mid, what, find, replace in wanted:
        count = text.count(find)
        entry: dict[str, object] = {"id": mid, "what": what, "anchor": find, "replacement": replace, "anchor_count": count}
        if count != 1:
            entry["verdict"] = f"NOT APPLIED: the anchor occurs {count} times"
            result["mutants"].append(entry)
            ok = False
            continue
        mutated = text.replace(find, replace, 1)
        try:
            ci_path.write_bytes(mutated.encode("utf-8"))
            entry["mutated_sha256"] = sha256_bytes(ci_path.read_bytes())
            entry["lanes"] = {lane: run_lane(worktree, args.python, lane, mid, out, engine_dir) for lane in ("unit", "self-test")}
        finally:
            ci_path.write_bytes(original)
            restored = sha256_bytes(ci_path.read_bytes())
            if restored != original_sha:
                shutil.copyfile(backup / "ci.yml", ci_path)
                restored = sha256_bytes(ci_path.read_bytes())
            entry["restored_sha256"] = restored
            if restored != original_sha:
                result["restores_exact"] = False
                ok = False
        lanes = entry["lanes"]
        killed_by = {lane: data.get("failed", []) for lane, data in lanes.items() if data["exit"] != 0 or data.get("failed")}
        entry["verdict"] = "killed" if killed_by else "survived"
        entry["killed_by"] = killed_by
        result["mutants"].append(entry)
        (out / "mutants.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
        print(f"{mid} {entry['verdict']}: unit exit {lanes['unit']['exit']} ({lanes['unit'].get('passed')} passed, {len(lanes['unit'].get('failed', []))} failed, {lanes['unit'].get('skipped_count')} skipped); self-test exit {lanes['self-test']['exit']} ({lanes['self-test'].get('passed')} passed, {len(lanes['self-test'].get('failed', []))} failed, {lanes['self-test'].get('skipped_count')} skipped)", flush=True)
    result["test_file_sha256_after"] = sha256_bytes(test_path.read_bytes())
    result["ci_yml_sha256_after"] = sha256_bytes(ci_path.read_bytes())
    if result["test_file_sha256_after"] != test_sha or result["ci_yml_sha256_after"] != original_sha:
        ok = False
    (out / "mutants.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    base = result["baseline"]
    print(f"baseline: unit exit {base['unit']['exit']} ({base['unit'].get('passed')} passed, {base['unit'].get('skipped_count')} skipped); self-test exit {base['self-test']['exit']} ({base['self-test'].get('passed')} passed)")
    print(f"survived: {[m['id'] for m in result['mutants'] if m.get('verdict') == 'survived']}")
    print(f"killed: {[m['id'] for m in result['mutants'] if m.get('verdict') == 'killed']}")
    print(f"restores exact: {result['restores_exact']}; ci.yml after {result['ci_yml_sha256_after']}; test file after {result['test_file_sha256_after']}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
