#!/usr/bin/env python3
"""Independently re-prove one ruling-26 port in a validator's own clone (V26 CODE lens, flood-4 session 11).

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (validation of the ruling-26 lockfile-print ports; tmp/flood4/session11/r26/val_code/)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/session11/briefs/V26_ports_validator.txt (CODE lens); juniper-canopy#814 (the model fix);
    util/ad-hoc/2026-11-24_flood4_s11_r26_proof.py (the builder's harness, which this one does NOT reuse)

In order, for one clone at the recorded base:
  install  copy each frozen file (--final/<path> for every path in --paths) over the clone, after saving the clone's
           own (main's) copy under <out>/main_copy/; verify every installed file against --sha256 (stop on mismatch);
  fixed    run pytest with the given args on the frozen tree;
  main     put main's workflow back (the frozen tests stay) and run again;
  V..      apply each of this validator's own mutants to the frozen workflow and run again (each OLD must occur once);
  collect  `pytest --collect-only -q` with CI's own unit-lane args (--ci-args), to show CI selects the new tests;
  extra    (optional, --extra-args) a second pytest run on the frozen tree, e.g. every test that reads .github/.
After every swap the frozen workflow is written back and its sha256 re-checked. The frozen files stay installed.
pytest gets --basetemp under --out, -p no:cacheprovider, TMPDIR under --out, GIT_CEILING_DIRECTORIES=--out, and an
environment without SENTRY_SDK_DSN and JUNIPER_CASCOR_LOG_DIR. This script runs no git command.

Verdict (summary.json / summary.txt): fixed has no failure; main's failing set EQUALS --expect-new exactly (names as
junit reports them, `func[param-id]`); every mutant fails at least one test (survivors are listed, not hidden);
every --expect-new test is collected under --ci-args.

Usage:
    python3 util/ad-hoc/2026-11-24_flood4_s11_v26_code_proof.py --clone DIR --final DIR --paths FILE --sha256 FILE \
        --workflow REL --out DIR --python PY --not-committed WORD --expect-new NAME [...] \
        --ci-args "ARGS" [--ci-cwd-rel REL] [--extra-args "ARGS"] -- PYTEST_ARGS...
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import shutil
import subprocess  # nosec B404 -- runs pytest with a fixed interpreter and argv
import sys
import xml.etree.ElementTree as ET  # nosec B405 -- parses junit XML this script's own pytest runs wrote
from pathlib import Path

DROP_ENV = ("SENTRY_SDK_DSN", "JUNIPER_CASCOR_LOG_DIR")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _line_with(text: str, needle: str) -> str:
    hits = [line for line in text.splitlines() if needle in line]
    if len(hits) != 1:
        raise SystemExit(f"STOP: expected one line containing {needle!r}, found {len(hits)}")
    return hits[0]


def _indent(line: str) -> str:
    return line[: len(line) - len(line.lstrip())]


def _mutants(fixed: str, not_committed: str) -> list[dict[str, str]]:
    """This validator's own mutants of the fix block. Each OLD is taken from the frozen text and must occur once."""
    diag = _line_with(fixed, f'echo "::error::createCommitOnBranch failed — {not_committed}:"')
    rerun = _line_with(fixed, 'needs only the re-run."')
    rerun_exit = rerun + "\n" + _indent(rerun) + "exit 1"
    hint = _line_with(fixed, 'echo "HTTP 401: CROSS_REPO_DISPATCH_TOKEN is invalid or expired."')
    hint_if = _line_with(fixed, '*"(HTTP 401)"*')
    http_tail = hint + "\n" + _indent(hint_if) + "fi\n" + _indent(hint_if) + "exit 1"
    status_init = _line_with(fixed, "GH_STATUS=0")
    capture = _line_with(fixed, "|| GH_STATUS=$?")
    errors_if = _line_with(fixed, "if jq -e '.errors'")
    return [
        {"name": "V01-gh-msg-to-stdout", "why": "gh's captured message printed to stdout, not stderr", "old": 'redact "${GH_STDERR}" >&2', "new": 'redact "${GH_STDERR}"'},
        {"name": "V02-errors-exit-0", "why": "the .errors branch exits 0 (wrong exit code)", "old": rerun_exit, "new": rerun + "\n" + _indent(rerun) + "exit 0"},
        {"name": "V03-diag-after-exit", "why": "the step's diagnostic placed after `exit 1` (unreachable again)", "old": diag, "new": _indent(diag) + "exit 1\n" + diag},
        {"name": "V04-status-hardcoded-1", "why": "gh's exit status replaced by a constant 1", "old": "|| GH_STATUS=$?", "new": "|| GH_STATUS=1"},
        {"name": "V05-http-no-exit", "why": "the HTTP branch falls through to the success print (no exit)", "old": http_tail, "new": hint + "\n" + _indent(hint_if) + "fi"},
        {"name": "V06-mask-first-only", "why": "the mask replaces only the first occurrence of the token", "old": '${1//"${GH_TOKEN:-}"/***}', "new": '${1/"${GH_TOKEN:-}"/***}'},
        {"name": "V07-no-status-init", "why": "GH_STATUS=0 removed (set -u on the success path)", "old": status_init + "\n", "new": ""},
        {"name": "V08-errors-only-if-gh-ok", "why": "the .errors branch reachable only when gh exits 0 (the old semantics)", "old": errors_if, "new": errors_if.replace("if jq -e", 'if [ "${GH_STATUS}" -eq 0 ] && jq -e', 1)},
        {"name": "V09-diag-to-stderr", "why": "the ::error:: diagnostic printed to stderr", "old": diag, "new": diag + " >&2"},
        {"name": "V10-hint-unconditional", "why": "the 401 hint printed on every HTTP failure", "old": hint_if, "new": _indent(hint_if) + "if true; then"},
        {"name": "V11-http-exit-gh-status", "why": "the HTTP branch exits with gh's status instead of 1", "old": http_tail, "new": hint + "\n" + _indent(hint_if) + "fi\n" + _indent(hint_if) + 'exit "${GH_STATUS}"'},
        {"name": "V12-gh-stderr-dropped", "why": "gh's stderr discarded instead of captured", "old": capture, "new": capture.replace("; } 2>&1)", "; } 2>/dev/null)", 1)},
        {"name": "V13-jq-noise-cosmetic", "why": "COSMETIC: the .errors probe's own stderr not silenced (main's form); expected to survive", "old": errors_if, "new": errors_if.replace(" > /dev/null 2>&1; then", " > /dev/null; then", 1)},
        {"name": "V14-http-annotation-dropped", "why": "the HTTP branch's `::error::` prefix dropped (no annotation on the run page)", "old": 'echo "::error::gh api graphql failed', "new": 'echo "gh api graphql failed'},
        {"name": "V15-errors-annotation-dropped", "why": "the .errors branch's `::error::` prefix dropped (no annotation on the run page)", "old": diag, "new": diag.replace('echo "::error::', 'echo "', 1)},
    ]


def _results(junit: Path) -> dict[str, str]:
    outcome: dict[str, str] = {}
    if not junit.is_file():
        return outcome
    root = ET.parse(junit).getroot()  # nosec B314 -- this run's own junit output
    for case in root.iter("testcase"):
        key = f"{case.get('classname', '')}::{case.get('name', '')}"
        state = "passed"
        for child in case:
            if child.tag in ("failure", "error", "skipped"):
                state = {"failure": "failed", "error": "error", "skipped": "skipped"}[child.tag]
                break
        outcome[key] = state
    return outcome


def _env(out: Path) -> dict[str, str]:
    """The child environment. Every temp variable names one ABSOLUTE directory under --out: a relative or missing
    TMPDIR makes Python's tempfile fall back to TEMP, then TMP, then the system temp directory (this script's first
    run passed a relative --out, and pytest's cwd is the clone, so TMPDIR resolved to a directory that did not exist)."""
    env = {key: value for key, value in os.environ.items() if key not in DROP_ENV}
    tmpdir = (out / "tmpdir").resolve()
    tmpdir.mkdir(parents=True, exist_ok=True)
    for key in ("TMPDIR", "TEMP", "TMP"):
        env[key] = str(tmpdir)
    env["GIT_CEILING_DIRECTORIES"] = str(out.resolve())
    return env


def _pytest(label: str, args: argparse.Namespace, pytest_args: list[str], *, cwd: Path) -> dict:
    out: Path = args.out
    junit = out / f"junit_{label}.xml"
    argv = [args.python, "-m", "pytest", *pytest_args, f"--basetemp={out / f'basetemp_{label}'}", f"--junitxml={junit}", "-p", "no:cacheprovider"]
    proc = subprocess.run(argv, cwd=cwd, env=_env(out), capture_output=True, text=True, check=False, timeout=1800)  # nosec B603 -- fixed interpreter
    (out / f"log_{label}.txt").write_text(f"$ {shlex.join(argv)}\n(cwd {cwd})\nexit {proc.returncode}\n\n{proc.stdout}\n--- stderr ---\n{proc.stderr}", encoding="utf-8")
    results = _results(junit)
    return {
        "label": label,
        "exit": proc.returncode,
        "counts": {state: sum(1 for value in results.values() if value == state) for state in ("passed", "failed", "error", "skipped")},
        "failed": sorted(key for key, state in results.items() if state in ("failed", "error")),
        "skipped": sorted(key for key, state in results.items() if state == "skipped"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--clone", type=Path, required=True)
    parser.add_argument("--final", type=Path, required=True)
    parser.add_argument("--paths", type=Path, required=True)
    parser.add_argument("--sha256", type=Path, required=True)
    parser.add_argument("--workflow", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--python", required=True)
    parser.add_argument("--not-committed", required=True, help="the step's own words, e.g. 'lockfile NOT committed'")
    parser.add_argument("--expect-new", nargs="+", required=True, help="junit test names (func[param]) new in this port")
    parser.add_argument("--ci-args", required=True, help="CI's unit-lane pytest args, one shell-quoted string")
    parser.add_argument("--extra-args", default="", help="a second pytest run on the frozen tree, one shell-quoted string")
    parser.add_argument("--only-collect", action="store_true", help="install and run only the CI collect-only check (writes collect_summary.txt)")
    parser.add_argument("--only", nargs="+", default=[], help="run only these variant labels (writes summary_only.txt)")
    parser.add_argument("pytest_args", nargs="+")
    args = parser.parse_args()
    # Absolute paths only: pytest runs with cwd = the clone, so a relative --out would put --basetemp, --junitxml
    # and TMPDIR inside the clone (or nowhere).
    for name in ("clone", "final", "paths", "sha256", "out"):
        setattr(args, name, getattr(args, name).resolve())
    args.out.mkdir(parents=True, exist_ok=True)

    # install
    rel_paths = [line.strip() for line in args.paths.read_text(encoding="utf-8").splitlines() if line.strip()]
    expected_sha = {}
    for line in args.sha256.read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, rel = line.split(maxsplit=1)
            expected_sha[rel.strip()] = digest
    install_log = []
    for rel in rel_paths:
        target = args.clone / rel
        saved = args.out / "main_copy" / rel
        saved.parent.mkdir(parents=True, exist_ok=True)
        if target.is_file() and not saved.exists():
            shutil.copyfile(target, saved)
        main_sha = _sha(saved) if saved.exists() else "(absent on main)"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(args.final / rel, target)
        got = _sha(target)
        if got != expected_sha.get(rel):
            print(f"STOP: {rel} installed sha256 {got} != final.sha256 {expected_sha.get(rel)}", file=sys.stderr)
            return 2
        install_log.append(f"{rel}: main {main_sha} -> frozen {got} (matches final.sha256)")
    workflow = args.clone / args.workflow
    fixed_text = workflow.read_text(encoding="utf-8")
    fixed_sha = _sha(workflow)
    main_text = (args.out / "main_copy" / args.workflow).read_text(encoding="utf-8")

    mutants = _mutants(fixed_text, args.not_committed)
    for mutant in mutants:
        count = fixed_text.count(mutant["old"])
        if count != 1:
            print(f"STOP: mutant {mutant['name']}: OLD occurs {count} times", file=sys.stderr)
            return 2
    (args.out / "mutants.json").write_text(json.dumps(mutants, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    variants = [("fixed", fixed_text), ("main", main_text)] + [(m["name"], fixed_text.replace(m["old"], m["new"], 1)) for m in mutants]
    if args.only_collect:
        variants = []
    if args.only:
        # A subset run: only the named variants, reported in summary_only.txt; the full run's summary is left alone.
        variants = [(label, text) for label, text in variants if label in args.only]
        runs_only = []
        for label, text in variants:
            workflow.write_text(text, encoding="utf-8")
            try:
                run = _pytest(f"only_{label}", args, args.pytest_args, cwd=args.clone)
            finally:
                workflow.write_text(fixed_text, encoding="utf-8")
            if _sha(workflow) != fixed_sha:
                print(f"STOP: after {label} the workflow sha256 changed", file=sys.stderr)
                return 3
            runs_only.append(run)
        lines = [f"[only {run['label']}] exit {run['exit']} {run['counts']}" + "".join(f"\n    FAILED {f.rsplit('::', 1)[-1]}" for f in run["failed"]) for run in runs_only]
        (args.out / "summary_only.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("\n".join(lines))
        return 0
    runs = []
    for label, text in variants:
        workflow.write_text(text, encoding="utf-8")
        try:
            run = _pytest(label, args, args.pytest_args, cwd=args.clone)
        finally:
            workflow.write_text(fixed_text, encoding="utf-8")
        restored = _sha(workflow)
        if restored != fixed_sha:
            print(f"STOP: after {label} the workflow sha256 is {restored}, not {fixed_sha}", file=sys.stderr)
            return 3
        run["variant_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
        runs.append(run)

    # collect-only under CI's own unit-lane args. `--verbosity=-1` SETS the level (node ids, one per line) after the
    # repository's addopts: an extra `-q` on top of an addopts `-q` gives -2, which prints only per-file counts.
    collect_argv = [args.python, "-m", "pytest", "--collect-only", *shlex.split(args.ci_args), "--verbosity=-1", "-p", "no:cacheprovider", f"--basetemp={args.out / 'basetemp_collect'}"]
    collect = subprocess.run(collect_argv, cwd=args.clone, env=_env(args.out), capture_output=True, text=True, check=False, timeout=1800)  # nosec B603
    (args.out / "log_collect.txt").write_text(f"$ {shlex.join(collect_argv)}\nexit {collect.returncode}\n\n{collect.stdout}\n--- stderr ---\n{collect.stderr}", encoding="utf-8")
    collected = [line.strip() for line in collect.stdout.splitlines() if "::" in line]
    collected_names = {line.rsplit("::", 1)[-1] for line in collected}
    not_collected = sorted(name for name in args.expect_new if name not in collected_names)
    test_file = next((arg for arg in args.pytest_args if arg.endswith(".py")), "")
    file_ids = [line for line in collected if line.split("::", 1)[0] == test_file]
    collect_errors = [line for line in collect.stdout.splitlines() if line.startswith("ERROR ")]
    if args.only_collect:
        text = "\n".join(
            [
                f"[collect under CI args: {args.ci_args}] exit {collect.returncode}; {len(collected)} node ids collected in all",
                f"  {test_file}: {len(file_ids)} node ids collected",
                *(f"    {line}" for line in file_ids),
                f"  new tests not collected: {not_collected}",
                f"  collection errors elsewhere (not this file): {[e for e in collect_errors if test_file not in e]}",
                f"  collection errors in this file: {[e for e in collect_errors if test_file in e]}",
            ]
        )
        (args.out / "collect_summary.txt").write_text(text + "\n", encoding="utf-8")
        print(text)
        return 0 if not not_collected and not [e for e in collect_errors if test_file in e] else 1

    extra = None
    if args.extra_args:
        extra = _pytest("extra_github_readers", args, shlex.split(args.extra_args), cwd=args.clone)

    by = {run["label"]: run for run in runs}
    names = lambda ids: sorted(i.rsplit("::", 1)[-1] for i in ids)  # noqa: E731
    fixed_ok = not by["fixed"]["failed"] and by["fixed"]["counts"]["passed"] > 0
    main_failed = names(by["main"]["failed"])
    main_exact = main_failed == sorted(args.expect_new)
    survivors = [m["name"] for m in mutants if not by[m["name"]]["failed"]]
    verdict = {
        "fixed_all_pass": fixed_ok,
        "main_fails_exactly_the_new_set": main_exact,
        "main_failed_minus_expected": sorted(set(main_failed) - set(args.expect_new)),
        "expected_minus_main_failed": sorted(set(args.expect_new) - set(main_failed)),
        "mutant_survivors": survivors,
        "ci_collects_every_new_test": not not_collected,
        "ci_not_collected": not_collected,
        "ci_collect_exit": collect.returncode,
        "ci_collected_total": len(collected),
        "extra_run": None if extra is None else {"exit": extra["exit"], "counts": extra["counts"], "failed": extra["failed"]},
        "fixed_sha256": fixed_sha,
    }
    (args.out / "summary.json").write_text(json.dumps({"verdict": verdict, "install": install_log, "runs": runs}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [f"clone {args.clone}", *install_log, f"pytest args: {shlex.join(args.pytest_args)}", ""]
    for run in runs:
        lines.append(f"[{run['label']}] exit {run['exit']} {run['counts']}")
        lines.extend(f"    FAILED {name}" for name in names(run["failed"]))
        lines.extend(f"    SKIPPED {name}" for name in names(run["skipped"]))
    lines.append(f"[collect under CI args: {args.ci_args}] exit {collect.returncode}, {len(collected)} collected; new tests not collected: {not_collected}")
    if extra is not None:
        lines.append(f"[extra: {args.extra_args}] exit {extra['exit']} {extra['counts']}")
        lines.extend(f"    FAILED {name}" for name in extra["failed"])
    lines += ["", "verdict: " + json.dumps(verdict, ensure_ascii=False)]
    (args.out / "summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    ok = fixed_ok and main_exact and not not_collected and all(s.startswith("V13") for s in survivors)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
