"""
The validator's own mutants of the juniper-data-client ruling-10 port: which of the 25 new tests kill each one.

None of these is among the builder's 48 (util/ad-hoc/2026-11-11_verify_gitleaks_pr_scan_tests_are_not_vacuous.py in
the carrier). Each mutant is an exact-once edit of .github/workflows/ci.yml in the VALIDATOR'S OWN COPY, never the
carrier. The whole test file is run under every mutant (not a chosen subset), with the official gitleaks 8.24.3 binary
and GITLEAKS_PARITY_REQUIRED=1, so a mutant that no test kills shows up as a survivor. A pristine copy of the file is
kept, the file is restored after every mutant, and the restore is proved by sha256.

Usage: python3 util/ad-hoc/2026-11-12_flood4r2_val_r10-data-client_mutants.py --engine <gitleaks 8.24.3> --python <interpreter> --out <dir> [--only <id,...>] [--main-workflow <main's ci.yml>]

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (validator agent, flood-4 session 5)
Created: 2026-11-12
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: ruling 10 in section 8 of notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md; juniper-data#530
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
COPY = JUNIPER / "worktrees" / "juniper-data-client--val--r10-port--20261112-0225--3cd855d1"
CI = ".github/workflows/ci.yml"
TEST_FILE = "tests/test_gitleaks_pr_scan.py"

SCAN_IF = "        if: github.event_name == 'pull_request'\n        env:\n          BASE_SHA:"
INSTALL_IF = "        if: github.event_name == 'pull_request'\n        env:\n          GITLEAKS_VERSION:"
JOB_HEAD = "  security:\n    name: Security Scans\n    runs-on: ubuntu-latest\n    needs: [pre-commit]\n"
SELF_TEST = "        run: python -m pytest tests/test_gitleaks_pr_scan.py -v -v --timeout=120\n"
SHA_LINE = '          echo "${GITLEAKS_SHA256}  ${RUNNER_TEMP}/${asset}" | sha256sum --check --strict\n'
UPLOAD = "      - name: Upload Security Reports\n        uses: actions/upload-artifact@cf430e030ddbb5b0abf93d22962f4752f3646cd9  # v7.0.2\n        if: always()\n        with:\n          name: security-reports\n"

#: (id, what the edit undoes, exact text occurring once in ci.yml, replacement)
MUTANTS: list[tuple[str, str, str, str]] = [
    ("V01", "continue-on-error on the pull-request scan step: a leak no longer fails the job", SCAN_IF, SCAN_IF.replace("        env:", "        continue-on-error: true\n        env:", 1)),
    ("V02", "continue-on-error on the security job", JOB_HEAD, JOB_HEAD + "    continue-on-error: true\n"),
    ("V03", "a job-level if: the whole security job skips Dependabot", JOB_HEAD, JOB_HEAD + "    if: github.actor != 'dependabot[bot]'\n"),
    ("V04", "the self-test's failure is swallowed in its own shell (|| true)", SELF_TEST, SELF_TEST.replace("--timeout=120\n", "--timeout=120 || true\n")),
    ("V05", "the self-test deselects the real-engine cases (-k)", SELF_TEST, SELF_TEST.replace("--timeout=120\n", '--timeout=120 -k "not real_engine"\n')),
    ("V06", "the digest check's failure is swallowed (|| true)", SHA_LINE, SHA_LINE.replace("--strict\n", "--strict || true\n")),
    ("V07", "the tarball is checked against its own hash, not the pinned digest", SHA_LINE, '          echo "$(sha256sum "${RUNNER_TEMP}/${asset}" | cut -d " " -f 1)  ${RUNNER_TEMP}/${asset}" | sha256sum --check --strict\n'),
    ("V08", "continue-on-error on the install step", INSTALL_IF, INSTALL_IF.replace("        env:", "        continue-on-error: true\n        env:", 1)),
    ("V09", "the report upload no longer runs after a failed scan (if: always() dropped)", UPLOAD, UPLOAD.replace("        if: always()\n", "")),
    ("V10", "the report upload no longer includes the gitleaks report", "          name: security-reports\n          path: reports/security/\n", "          name: security-reports\n          path: reports/security/bandit.sarif\n"),
    ("V11", "the range is a symmetric difference (base...head)", '          range="${BASE_SHA}..${HEAD_SHA}"', '          range="${BASE_SHA}...${HEAD_SHA}"'),
    ("V12", "--exit-code=2 dropped: a leak exits with gitleaks' default code", "-v --exit-code=2 --report-format=sarif", "-v --report-format=sarif"),
    ("V13", "the engine's exit status is swallowed (|| true)", '"--log-opts=--remerge-diff ${range}" || rc=$?', '"--log-opts=--remerge-diff ${range}" || true'),
    ("V14", "the report is written under another name", "--report-path=reports/security/gitleaks.sarif", "--report-path=reports/security/results.sarif"),
    ("V15", "the action also skips push: a push runs neither scan", "        if: github.event_name != 'pull_request'\n", "        if: github.event_name != 'pull_request' && github.event_name != 'push'\n"),
    ("V16", "the scan step skips Dependabot pull requests", SCAN_IF, SCAN_IF.replace("'pull_request'\n", "'pull_request' && github.actor != 'dependabot[bot]'\n", 1)),
    ("V17", "the install step skips Dependabot pull requests", INSTALL_IF, INSTALL_IF.replace("'pull_request'\n", "'pull_request' && github.actor != 'dependabot[bot]'\n", 1)),
    ("V18", "the action's engine floats (GITLEAKS_VERSION: latest)", '          GITLEAKS_VERSION: "8.24.3"\n        # The action declares no inputs', '          GITLEAKS_VERSION: "latest"\n        # The action declares no inputs'),
    ("V19", "the git filter deletes every line that holds the word remerge, not only git's notes", "sed -e '/^remerge /d'", "sed -e '/remerge/d'"),
    ("V20", "the scan step no longer creates reports/security/ (here nothing else has, before it)", "          mkdir -p reports/security\n          rc=0\n", "          rc=0\n"),
    ("V21", "the security job is renamed (Security Scans is a required check)", "    name: Security Scans\n", "    name: Security\n"),
    ("V22", "the git filter is never made executable, so the engine runs the real git", '          chmod +x "${filter}/git"\n', ""),
    ("V23", "only the base SHA is validated", '          for sha in "${BASE_SHA}" "${HEAD_SHA}"; do\n', '          for sha in "${BASE_SHA}"; do\n'),
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_file(python: str, engine: str, out: Path, label: str, select: str | None = None) -> dict:
    """Run the test file once (all of it, or the cases a -k expression selects); return {passed, failed, errors, skipped, failed_ids}."""
    for stale in (COPY / "tests" / "__pycache__").glob("test_gitleaks_pr_scan*.pyc"):
        stale.unlink()
    junit = out / f"{label}.junit.xml"
    basetemp = out / "basetemp" / label
    basetemp.parent.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "GITLEAKS_PARITY_REQUIRED": "1", "GITLEAKS_BIN": engine}
    for name in ("GITLEAKS_CONFIG", "GITLEAKS_CONFIG_TOML"):
        env.pop(name, None)
    argv = [python, "-m", "pytest", TEST_FILE, "-q", "--no-header", "-p", "no:cacheprovider", "--timeout=180", f"--basetemp={basetemp}", f"--junitxml={junit}", "-rfEs"]
    if select:
        argv += ["-k", select]
    res = subprocess.run(argv, cwd=COPY, capture_output=True, text=True, env=env, check=False)
    (out / f"{label}.log").write_text(res.stdout + "\n--- stderr ---\n" + res.stderr, encoding="utf-8")
    result = {"exit": res.returncode, "passed": 0, "failed": 0, "errors": 0, "skipped": 0, "failed_ids": []}
    if junit.is_file():
        for case in ElementTree.parse(junit).getroot().iter("testcase"):
            name = case.get("name", "")
            if case.find("failure") is not None:
                result["failed"] += 1
                result["failed_ids"].append(name)
            elif case.find("error") is not None:
                result["errors"] += 1
                result["failed_ids"].append(name + " (error)")
            elif case.find("skipped") is not None:
                result["skipped"] += 1
            else:
                result["passed"] += 1
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--engine", required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--only", help="comma-separated mutant ids")
    parser.add_argument("--main-workflow", type=Path, help="main's ci.yml: also run the file with it in place of the carrier's (label MAIN)")
    parser.add_argument("--select", help="a pytest -k expression: run only those cases under every mutant (for a quick re-check of the static pins)")
    parser.add_argument("--expect", type=int, default=25, help="how many cases the baseline must pass (default 25, the whole file)")
    args = parser.parse_args()
    if "--ci--gitleaks-pr-commit-scan--" in str(COPY):
        raise SystemExit("refusing to mutate the carrier worktree")
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    target = COPY / CI
    pristine = out / "pristine" / CI
    if pristine.is_file() and sha256(pristine) != sha256(target):
        raise SystemExit(f"{target} differs from the pristine copy at {pristine}: an earlier run died mid-mutant; restore it first")
    pristine.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(target, pristine)
    before = sha256(target)
    original = target.read_text(encoding="utf-8")
    wanted = set(args.only.split(",")) if args.only else None
    chosen = [mutant for mutant in MUTANTS if wanted is None or mutant[0] in wanted]
    for ident, _, find, _ in chosen:
        if original.count(find) != 1:
            raise SystemExit(f"{ident}: its pattern occurs {original.count(find)} times in {CI} (expected 1)")

    record: dict = {"copy": str(COPY), "ci_sha256": before, "engine_sha256": sha256(Path(args.engine)), "python": args.python, "mutants": []}
    record["select"] = args.select
    record["test_file_sha256"] = sha256(COPY / TEST_FILE)
    record["baseline"] = run_file(args.python, args.engine, out, "baseline", args.select)
    print(f"baseline: {record['baseline']}")
    if record["baseline"]["passed"] != args.expect or record["baseline"]["exit"] != 0:
        print(f"the baseline is not {args.expect} passed: no mutant was run")
        return 1

    if args.main_workflow and (wanted is None or "MAIN" in wanted):
        try:
            shutil.copyfile(args.main_workflow, target)
            record["main_workflow"] = run_file(args.python, args.engine, out, "MAIN")
        finally:
            shutil.copyfile(pristine, target)
        record["main_workflow"]["restored"] = sha256(target) == before
        print(f"MAIN workflow in place: {record['main_workflow']}")

    for ident, what, find, replace in chosen:
        try:
            target.write_text(original.replace(find, replace), encoding="utf-8")
            mutated_sha = sha256(target)
            result = run_file(args.python, args.engine, out, ident, args.select)
        finally:
            shutil.copyfile(pristine, target)
        restored = sha256(target) == before
        entry = {"id": ident, "what": what, "mutated_sha256": mutated_sha, "killed": bool(result["failed_ids"]), "killed_by": result["failed_ids"], "counts": {k: result[k] for k in ("passed", "failed", "errors", "skipped", "exit")}, "restored": restored}
        record["mutants"].append(entry)
        print(f"{ident} {'KILLED  ' if entry['killed'] else 'SURVIVED'} {what}\n      by: {result['failed_ids']}  restored={restored}")
        if not restored:
            raise SystemExit(f"{ident}: RESTORE FAILED")

    record["totals"] = {"mutants": len(record["mutants"]), "killed": sum(1 for m in record["mutants"] if m["killed"]), "survived": [m["id"] for m in record["mutants"] if not m["killed"]], "ci_sha256_after": sha256(target)}
    with open(out / "mutants.json", "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=1)
        fh.write("\n")
    print(json.dumps(record["totals"], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
