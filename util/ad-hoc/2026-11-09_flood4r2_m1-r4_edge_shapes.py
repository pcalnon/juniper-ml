#!/usr/bin/env python3
"""
Re-run round 2's merge edge shapes (content, modify/delete, add/add, binary, rename-vs-modify, add/add with a token) through round 2's and round 4's pull-request scan step.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation (round 4 of the juniper-data pull-request Gitleaks fix: finding R3-02's git filter)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §4 (the juniper-data row)

WHY THIS EXISTS
Round 2's 2026-11-08_flood4r2_jd-gitleaks_remerge_edge_probe.py showed each shape below passing the step when resolved
honestly, with no git error in the engine's log, and an add/add resolution that writes a token reported under the
merge's SHA. Round 4 runs the engine's git through a filter that deletes --remerge-diff's `remerge ...` notes, and
these are exactly the shapes that write such notes, so they are measured again. That probe cannot be reused as it
stands: it locates its repositories under TMPDIR (session 4's brief forbids changing TMPDIR) and runs the step without
RUNNER_TEMP, which round 4's step requires. This driver keeps its six scenarios verbatim (validator A's scan_harness
Repo, imported READ-ONLY with bytecode writing off) and runs each through each step's run: block, extracted from the
given ci.yml, under `bash -e`, with RUNNER_TEMP set as GitHub sets it. Repositories live under --out, have no remote,
and carry only FAKE-marked tokens built at runtime; reports are redacted.

Usage:
    python3 -B <this> --engine <gitleaks 8.24.3> --harness <dir holding scan_harness.py> --r2-ci <ci.yml> --r4-ci <ci.yml> --worktree <juniper-data worktree> --out <dir>
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import subprocess  # nosec B404 - fixed argv: git and bash running the extracted step
import sys
from pathlib import Path

import yaml

STEP_NAME = "Run Gitleaks over the pull request (Secrets Detection)"
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def load_harness(path: Path):
    spec = importlib.util.spec_from_file_location("scan_harness", path / "scan_harness.py")
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot load {path / 'scan_harness.py'}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["scan_harness"] = module
    spec.loader.exec_module(module)
    return module


def extract(ci: Path, dest: Path) -> Path:
    steps = yaml.safe_load(ci.read_text(encoding="utf-8"))["jobs"]["security"]["steps"]
    found = [s for s in steps if s.get("name") == STEP_NAME]
    if len(found) != 1 or "shell" in found[0]:
        raise SystemExit(f"{ci}: expected one {STEP_NAME!r} step that names no shell")
    dest.write_text(found[0]["run"], encoding="utf-8")
    return dest


def findings(sarif: Path) -> list[list[str]]:
    if not sarif.is_file():
        return [["<no report>", ""]]
    results = json.loads(sarif.read_text(encoding="utf-8"))["runs"][0].get("results") or []
    if not all(r["locations"][0]["physicalLocation"]["region"]["snippet"]["text"] == "REDACTED" for r in results):
        return [["<NOT REDACTED>", ""]]
    return sorted([r["partialFingerprints"].get("commitSha", "")[:8], r["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]] for r in results)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--engine", type=Path, required=True)
    ap.add_argument("--harness", type=Path, required=True, help="directory holding validator A's scan_harness.py (read only)")
    ap.add_argument("--r2-ci", type=Path, required=True)
    ap.add_argument("--r4-ci", type=Path, required=True)
    ap.add_argument("--worktree", type=Path, required=True, help="seeds each repository's .gitleaks.toml and .gitleaksignore")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    sys.dont_write_bytecode = True  # importing the harness must not write into the validator's directory
    harness = load_harness(args.harness)
    harness.WT = args.worktree
    engine = args.engine.resolve()
    blob_a, blob_b, blob_c = bytes(range(256)) * 4, bytes(reversed(range(256))) * 4, bytes(range(0, 256, 3)) * 8
    report: dict[str, list[dict]] = {}
    for label, ci in (("r2", args.r2_ci), ("r4", args.r4_ci)):
        out = (args.out / label).resolve()
        out.mkdir(parents=True, exist_ok=True)
        engine_bin = out / "engine-bin"
        engine_bin.mkdir(exist_ok=True)
        link = engine_bin / "gitleaks"
        if link.exists() or link.is_symlink():
            link.unlink()
        link.symlink_to(engine)
        stepfile = extract(ci, out / "pr_scan_step.sh")
        runner_temp = out / "runner-temp"
        runner_temp.mkdir(exist_ok=True)

        def put(p: Path, content: bytes | str) -> None:
            p.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                p.write_bytes(content)
            else:
                p.write_text(content, encoding="utf-8")

        def fork(r, files: dict[str, bytes | str]) -> None:
            for rel, content in files.items():
                put(r.dir / rel, content)
                r.git("add", "--", rel)
            r.git("commit", "-q", "--no-verify", "-m", "fork point", date=harness.next_date())

        def on(r, branch: str, edits: dict[str, bytes | str | None], new_branch: bool = False) -> str:
            r.git("checkout", "-q", *(["-b"] if new_branch else []), branch)
            for rel, content in edits.items():
                if content is None:
                    r.git("rm", "-q", "--", rel)
                    continue
                put(r.dir / rel, content)
                r.git("add", "--", rel)
            r.git("commit", "-q", "--no-verify", "-m", f"edit on {branch}", date=harness.next_date())
            return r.rev("HEAD")

        def build(files, pr_edits, base_edits):
            def prepare(r):
                fork(r, files)
                on(r, "pr", pr_edits, new_branch=True)
                base = on(r, "main", base_edits)
                r.git("checkout", "-q", "pr")
                return base

            return prepare

        def keep_ours(paths):
            def resolve(r):
                for rel in paths:
                    r.git("checkout", "--ours", "--", rel, check=False)
                    r.git("add", "--", rel)

            return resolve

        def write(rel: str, text: str):
            def resolve(r):
                (r.dir / rel).write_text(text, encoding="utf-8")
                r.git("add", "--", rel)

            return resolve

        def scenario(name: str, prepare, resolve, expect_token: bool, out: Path = out, stepfile: Path = stepfile, engine_bin: Path = engine_bin, runner_temp: Path = runner_temp) -> dict:
            r = harness.Repo(out / name)
            base = prepare(r)
            merge_rc = subprocess.run(["git", "-C", str(r.dir), "merge", "--no-ff", "-q", "-m", "merge the base branch", base], env=harness.git_env(r.home, harness.next_date()), capture_output=True, text=True, timeout=120, check=False).returncode  # nosec B603 B607
            resolve(r)
            r.git("commit", "-q", "--no-verify", "-m", "merge the base branch", date=harness.next_date(), check=False)
            merge = r.rev("HEAD")
            head = r.commit("pr/after.txt", "after\n")
            sarif = r.dir / "reports" / "security" / "gitleaks.sarif"
            env = harness.git_env(r.home)
            env.update({"PATH": f"{engine_bin}{os.pathsep}{env['PATH']}", "BASE_SHA": base, "HEAD_SHA": head, "PR_COMMITS": str(len(r.pr_list(base, head))), "GITHUB_STEP_SUMMARY": str(r.root / "step-summary.md"), "RUNNER_TEMP": str(runner_temp)})
            res = subprocess.run(["bash", "-e", str(stepfile)], cwd=r.dir, env=env, capture_output=True, text=True, timeout=600, check=False)  # nosec B603 B607
            log = ANSI.sub("", res.stdout + res.stderr)
            (r.root / "step.log").write_text(log, encoding="utf-8")
            git_errors = [line for line in log.splitlines() if "[git]" in line or "failed to" in line.lower()]
            reported = findings(sarif)
            scanned = (re.findall(r"(\d+) commits scanned", log) or [None])[-1]
            ok = (res.returncode == 1 and [c for c, _ in reported] == [merge[:8]]) if expect_token else (res.returncode == 0 and reported == [] and not git_errors)
            return {"scenario": name, "merge_exit": merge_rc, "merge": merge[:8], "step_exit": res.returncode, "reported": reported, "engine_commits_scanned": scanned, "git_error_lines": git_errors[:5], "expect_token": expect_token, "verdict": "AS EXPECTED" if ok else "UNEXPECTED"}

        rows = [
            scenario("content", build({"conf/s.txt": "a=1\nb=2\nc=3\n"}, {"conf/s.txt": "a=1\nb=PR\nc=3\n"}, {"conf/s.txt": "a=1\nb=BASE\nc=3\n"}), write("conf/s.txt", "a=1\nb=PR-and-BASE\nc=3\n"), False),
            scenario("modify-delete", build({"conf/f.txt": "one\ntwo\n"}, {"conf/f.txt": "one\nTWO\n"}, {"conf/f.txt": None}), keep_ours(["conf/f.txt"]), False),
            scenario("add-add", build({"conf/seed.txt": "s\n"}, {"conf/g.txt": "pr\n"}, {"conf/g.txt": "base\n"}), write("conf/g.txt", "pr\nbase\n"), False),
            scenario("binary", build({"data/b.bin": blob_a}, {"data/b.bin": blob_b}, {"data/b.bin": blob_c}), keep_ours(["data/b.bin"]), False),
            scenario("rename-vs-modify", build({"conf/h.txt": "".join(f"line {i}\n" for i in range(40))}, {"conf/h.txt": None, "conf/h2.txt": "".join(f"line {i}\n" for i in range(40))}, {"conf/h.txt": "".join(f"line {i}\n" for i in range(39)) + "line 39 changed\n"}), lambda r: None, False),
            scenario("add-add-with-token", build({"conf/seed.txt": "s\n"}, {"conf/g.txt": "pr\n"}, {"conf/g.txt": "base\n"}), write("conf/g.txt", "pr\nGITHUB_TOKEN=" + harness.fake_token(83) + "\n"), True),
        ]
        for row in rows:
            print(json.dumps({label: row}), flush=True)
        report[label] = rows
    (args.out / "results.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    bad = [f"{label}:{row['scenario']}" for label, rows in report.items() for row in rows if row["verdict"] != "AS EXPECTED"]
    print("UNEXPECTED: " + ", ".join(bad) if bad else "every scenario AS EXPECTED on both steps")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
