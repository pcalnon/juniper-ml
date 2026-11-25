"""
Assemble r23l's manifest.json, final/ copies, final.sha256 and base.txt check from the logs on disk.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-25
Status: ad-hoc — one-off (flood-4 session 14, builder r23l: the deliverables' manifest)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md section 8 (ruling 23)

Reads ``<dir>/paths.txt`` (repo-relative changed paths), copies each from ``--repo-root`` to ``<dir>/final/<path>``,
writes ``<dir>/final.sha256`` and ``<dir>/manifest.json``. Every check's result is read from its log or JSON under
``<dir>/logs`` (a missing log is recorded as missing, never invented). ``--added`` names the paths that are new.

Usage: python3 <this file> --dir <r23l dir> --repo-root <clone> --base-sha SHA --added PATH[,PATH...]
       --open-questions FILE
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _last_line(path: Path, pattern: str) -> str | None:
    if not path.is_file():
        return None
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = [line.strip() for line in fh if re.search(pattern, line)]
    return lines[-1] if lines else None


def _json(path: Path):
    if not path.is_file():
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--dir", required=True, type=Path)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--added", required=True)
    parser.add_argument("--open-questions", required=True, type=Path)
    args = parser.parse_args(argv)
    d, logs = args.dir, args.dir / "logs"
    added = set(args.added.split(","))
    with open(d / "paths.txt", encoding="utf-8") as fh:
        paths = [line.strip() for line in fh if line.strip()]
    files, sha_lines = [], []
    for rel in paths:
        src = args.repo_root / rel
        dst = d / "final" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        digest = _sha(dst)
        if digest != _sha(src):
            raise SystemExit(f"copy mismatch for {rel}")
        files.append({"path": rel, "status": "added" if rel in added else "modified", "sha256": digest})
        sha_lines.append(f"{digest}  {rel}")
    with open(d / "final.sha256", "w", encoding="utf-8") as fh:
        fh.write("\n".join(sha_lines) + "\n")

    checks = []
    for v in ("3.12", "3.13", "3.14"):
        py = f"{d}/venvs/py{v}/bin/python"
        checks.append(
            {
                "check": f"ci-service-core.yml test command (final tree), py{v}",
                "command": f"pytest juniper-service-core/tests/ -v --cov=juniper_service_core --cov-report=term-missing --cov-report=json:<logs>/coverage_final_py{v}.json --cov-fail-under=80 --basetemp=<r23l>/basetemp/final-py{v} (from the clone root, venv pytest script, COVERAGE_FILE under logs/, runenv.bash)",
                "interpreter": py,
                "result": _last_line(logs / f"suite_final_py{v}.log", r"(passed|failed).* in [0-9.]+s"),
                "total_coverage": _last_line(logs / f"suite_final_py{v}.log", r"Total coverage"),
                "log": f"logs/suite_final_py{v}.log",
            }
        )
        checks.append({"check": f"per-file coverage gate (juniper-coverage-gap-map --enforce), py{v}", "command": f"juniper-coverage-gap-map --coverage-json logs/coverage_final_py{v}.json --enforce", "interpreter": py, "result": _last_line(logs / f"gate_final_py{v}.log", r"Enforcing gate"), "log": f"logs/gate_final_py{v}.log"})
    checks.append({"check": "main's tree, same CI command (comparison)", "interpreter": f"{d}/venvs/py3.12/bin/python", "result": _last_line(logs / "suite_main_py3.12.log", r"(passed|failed).* in [0-9.]+s"), "total_coverage": _last_line(logs / "suite_main_py3.12.log", r"Total coverage"), "log": "logs/suite_main_py3.12.log", "coverage_diff": "logs/coverage_diff_main_vs_fix_py3.12.txt"})
    precommit_lines: list[str] = []
    if (logs / "precommit.log").is_file():
        with open(logs / "precommit.log", encoding="utf-8") as fh:
            precommit_lines = [line.rstrip() for line in fh]
    counts = [sum(1 for line in precommit_lines if line.endswith(k)) for k in ("Passed", "Skipped", "Failed")]
    checks.append({"check": "pinned pre-commit (4.6.0) run --files on the 14 changed files", "command": "/opt/miniforge3/envs/JuniperCascor1/bin/pre-commit run --files $(cat paths.txt) (from the clone)", "result": _last_line(logs / "precommit.log", r"G-TMP"), "passed_skipped_failed": counts, "files_unchanged": (logs / "precommit_sha256_before.txt").read_text() == (logs / "precommit_sha256_after.txt").read_text(), "log": "logs/precommit.log"})
    checks.append({"check": "pinned ruff 0.15.18 check + format --check on the seven util/ad-hoc scripts (no hook covers them)", "result": _last_line(logs / "ruff_adhoc.log", r"(passed|formatted)"), "log": "logs/ruff_adhoc.log"})
    checks.append({"check": "CodeQL prescreen (util/ad-hoc/2026-10-05_codeql_python_prescreen.py) on the 11 changed .py files", "result": _last_line(logs / "codeql_prescreen.log", r"predicted alert"), "log": "logs/codeql_prescreen.log", "note": "--known-answer not run: it writes through tempfile under the session TMPDIR, outside r23l/"})
    checks.append({"check": "markdown structure check on the 3 changed .md files", "result": _last_line(logs / "markdown_structure.log", r"structural problems"), "log": "logs/markdown_structure.log"})
    rs = _json(logs / "reader_suites.json") or []
    real = [r for r in rs if r.get("in_ci")]
    checks.append(
        {
            "check": "juniper-ml root suites that read a changed path (python3 -m unittest -v tests/<f>.py as ci.yml runs them)",
            "interpreter": "/opt/miniforge3/envs/JuniperCascor1/bin/python3 (3.14.7)",
            "suites_matched": len(rs),
            "suites_in_ci": len(real),
            "passed": sum(1 for r in real if r["exit"] == 0),
            "failed": [r["suite"] for r in real if r["exit"] != 0],
            "tests": sum(r["ran"] for r in real),
            "skipped": sum(r["skipped"] for r in real),
            "not_suites": [r["suite"] for r in rs if not r.get("in_ci")],
            "failed_on_clean_main_too": [r["suite"] for r in (_json(logs / "reader_suites_clean_main.json") or []) if r["exit"] != 0],
            "log": "logs/reader_suites.json, logs/reader_suites_clean_main.json",
        }
    )
    checks.append({"check": "juniper-symbol-loss-check --scope 'tests/*.py' --scope 'util/**/*.py' --scope 'util/**/*.bash' --base origin/main --head <probe>", "probe_commit": "e6b3c694e957281f6f2ab29321274ff4005c33cc (unsigned, --no-gpg-sign, parent 906668eb, tree 6130809b, on no branch, never pushed)", "result": _last_line(logs / "symbol_loss.log", r"files_screened"), "allow_symbol_loss_needed": "none", "log": "logs/symbol_loss.log"})
    checks.append({"check": "juniper-docs-additions-check --base origin/main --head <probe>", "result": _last_line(logs / "docs_additions.log", r"files_screened"), "log": "logs/docs_additions.log"})
    for label in ("main_py3.12", "main_py3.13", "main_py3.14", "fix_py3.12", "fix_py3.13", "fix_py3.14"):
        doc = _json(logs / f"probe_{label}.json")
        if doc:
            rows = doc["rows"]
            checks.append({"check": f"probe ({label})", "manager_sha256": doc["header"]["manager_sha256"], "python": doc["header"]["python"].split()[0], "rows": len(rows), "defect_seen": sum(1 for r in rows if r.get("defect_seen")), "setup_errors": sum(1 for r in rows if "setup_error" in r), "log": f"logs/probe_{label}.json"})

    mutants = {}
    for v in ("3.12", "3.13"):
        rows = _json(logs / f"mutation_final_py{v}.json") or []
        mutants[f"py{v}"] = [{"mutant": r["mutant"], "targets": r.get("targets"), "expected": r.get("expected"), "summary": r.get("summary"), "failed_count": len(r.get("failed", [])), "killers_missing": r.get("killers_missing", []), "verdict": r["verdict"]} for r in rows]
    flakes = []
    for name in ("flake50_py3.12", "flake50_py3.13", "flake50_py3.14", "flake50_stress_py3.12"):
        p = logs / f"{name}.summary"
        flakes.append({"run": name, "summary": p.read_text(encoding="utf-8").strip() if p.is_file() else None, "log": f"logs/{name}.log"})
    with open(args.open_questions, encoding="utf-8") as fh:
        open_questions = json.load(fh)
    manifest = {
        "repo": "pcalnon/juniper-ml",
        "base_sha": args.base_sha,
        "clone": str(args.repo_root),
        "files": files,
        "checks": checks,
        "mutants": mutants,
        "flake_runs": flakes,
        "open_questions": open_questions,
    }
    with open(d / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
    print(f"manifest: {len(files)} files, {len(checks)} checks, mutants {[len(v) for v in mutants.values()]}, flakes {len(flakes)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
