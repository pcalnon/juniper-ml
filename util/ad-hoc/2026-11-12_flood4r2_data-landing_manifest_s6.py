#!/usr/bin/env python3
"""
Assemble stage 3's final manifest.json against the main it now lands on, from the records of the runs.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: finishing juniper-data's stage-3 carrier, session 6)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (every mutant row and every sha256 is read from a file a run wrote, never typed)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: 2026-11-11_flood4r2_data-landing_manifest.py (the three-stage version, whose base is the older main);
         notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md

Usage:
    python3 <this> --stage-dir <scratch>/stage3 --repo <juniper-data primary> --base <main commit>
                   --control-wt <clean worktree of --base> --twin-wt <the mutation twin> --carrier-manifest <json>
                   --status in-progress|final --how <path>=<text> [...]
                   --mutations <label>=<mutants_summary.json> [...] --second-opinion-log <log>
                   --helper <script> [...] --forbid <string> [...] [--forbid-in <file> ...]

It refuses to write (exit 2) unless:
  - each of the stage's files in the carrier worktree has the sha256 stage-dir/build.json records;
  - the carrier differs from --base on exactly those files (every path of the commit and every unignored file of
    the tree is compared by blob id), and the twin holds the same bytes;
  - the control worktree is --base with nothing changed.
What it writes into manifest.json:
  - ``base_sha`` (--base, resolved) and, per file, ``parent_sha256``: the sha256 of that path at --base;
  - ``mutations``: one row per mutant of every --mutations summary, in order, with the result the runner recorded;
  - ``second_opinion``: the verdict lines of the other mutation script's log, as it printed them;
  - ``helpers``: for every --helper, its sha256 and the exit status of the path-literal gate, the CodeQL prescreen
    and the seven-shape screen, run here;
  - the fragments beside build.json (checks, text_changes, open_questions, if_main_moves) and the deliverables'
    sha256, with the text checks: no CI-skip marker, no trailer, no attribution footer, the CHANGELOG entry file
    occurring once in the tree, and none of the --forbid strings in any deliverable text or --forbid-in file. The
    forbidden strings themselves are not written anywhere: only how many were looked for and where one was found.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess  # nosec B404 - fixed argv: read-only git queries and this repo's own screening scripts
import sys
from pathlib import Path

TEXTS =("title.txt", "pr_body.md", "commit_body.txt", "changelog_entry.txt")
SKIP_MARKER = re.compile(r"\[(?:skip ci|ci skip|no ci|skip actions|actions skip)\]|\*\*\*NO_CI\*\*\*|skip-checks:", re.IGNORECASE)
TRAILER = re.compile(r"^(?:Co-Authored-By|Signed-off-by|Claude-Session|Allow-Symbol-Loss):", re.IGNORECASE | re.MULTILINE)
VERDICT = re.compile(r"^\s{2}(?P<name>\S.*?)\s+exit=(?P<exit>-?\d+)\s+\[tests=(?P<tests>-?\d+) failures=(?P<failures>-?\d+) \(not assertions: (?P<other>-?\d+)\) errors=(?P<errors>-?\d+) skipped=(?P<skipped>-?\d+)\]\s+(?P<verdict>OK|NOT OK|KILLED|SURVIVED)(?P<note>.*)$")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(cwd: Path, *argv: str) -> bytes:
    return subprocess.run(["git", "-C", str(cwd), *argv], capture_output=True, check=True).stdout  # nosec B603 B607


def _load(path: Path, default):
    if not path.is_file():
        return default
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\x00" % len(data) + data, usedforsecurity=False).hexdigest()


def _differs_from(repo: Path, ref: str, tree: Path) -> dict[str, str]:
    """Paths on which ``tree`` differs from commit ``ref``: every blob of the commit and every unignored file of the tree."""
    blobs: dict[str, str] = {}
    for record in _git(repo, "ls-tree", "-r", "-z", ref).split(b"\x00"):
        if record:
            meta, name = record.split(b"\t", 1)
            if meta.split()[1] == b"blob":
                blobs[name.decode("utf-8")] = meta.split()[2].decode("ascii")
    listed = _git(tree, "ls-files", "-z") + _git(tree, "ls-files", "-z", "--others", "--exclude-standard")
    found: dict[str, str] = {}
    for path in sorted(set(blobs) | {name.decode("utf-8") for name in listed.split(b"\x00") if name}):
        target = tree / path
        present = target.is_symlink() or target.is_file()
        if path not in blobs:
            if present:
                found[path] = "added"
        elif not present:
            found[path] = "deleted"
        else:
            data = str(target.readlink()).encode("utf-8") if target.is_symlink() else target.read_bytes()
            if _blob_id(data) != blobs[path]:
                found[path] = "modified"
    return found


def _mutation_rows(label: str, summary_path: Path) -> list[dict]:
    summary = _load(summary_path, None)
    if summary is None:
        raise SystemExit(f"{summary_path} is missing")
    rows = []
    for mutant in summary["mutants"]:
        rows.append(
            {
                "run": label,
                "test_file": mutant.get("test_file"),
                "id": mutant["id"],
                "mutant": mutant.get("mutant"),
                "why": mutant.get("why"),
                "result": mutant["result"],
                "expected": mutant.get("expect"),
                "as_expected": mutant.get("as_expected"),
                "tests_run": mutant.get("tests_run"),
                "failed": [node.split("::", 1)[-1] for node in mutant.get("failed", [])],
                "failed_not_on_an_assertion": [node.split("::", 1)[-1] for node in mutant.get("failed_not_on_an_assertion", [])],
                "must_fail": mutant.get("must_fail", []),
                "must_pass": mutant.get("must_pass", []),
                "restored": mutant.get("restored"),
                "sha256_before": mutant.get("sha256_before"),
                "sha256_after": mutant.get("sha256_after"),
                "log": mutant.get("log"),
            }
        )
    return rows


def _screen(repo_root: Path, helper: Path) -> dict:
    runs = {
        "g_path": [sys.executable, str(repo_root / "util" / "home_path_literal_check.py"), str(helper)],
        "codeql_prescreen": [sys.executable, str(repo_root / "util" / "ad-hoc" / "2026-10-05_codeql_python_prescreen.py"), str(helper)],
        "seven_shapes": [sys.executable, str(repo_root / "util" / "ad-hoc" / "2026-11-11_flood4r2_data-landing_codeql_shapes.py"), str(helper)],
    }
    row: dict = {"helper": helper.name, "sha256": _sha(helper)}
    for name, argv in runs.items():
        proc = subprocess.run(argv, cwd=repo_root, capture_output=True, text=True, check=False)  # nosec B603
        row[name] = {"exit": proc.returncode, "last_line": (proc.stdout.strip().splitlines() or [""])[-1]}
    row["clean"] = all(row[name]["exit"] == 0 for name in runs)
    return row


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--stage-dir", type=Path, required=True)
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--control-wt", type=Path, required=True)
    ap.add_argument("--twin-wt", type=Path, required=True)
    ap.add_argument("--carrier-manifest", type=Path, required=True)
    ap.add_argument("--status", required=True, choices=["in-progress", "final"])
    ap.add_argument("--how", action="append", default=[], help="<repo-relative path>=<how this file came to be>")
    ap.add_argument("--mutations", action="append", default=[], help="<label>=<mutants_summary.json>")
    ap.add_argument("--second-opinion-log", type=Path)
    ap.add_argument("--helper", action="append", default=[], type=Path)
    ap.add_argument("--forbid", action="append", default=[])
    ap.add_argument("--forbid-in", action="append", default=[], type=Path)
    args = ap.parse_args()
    stage_dir = args.stage_dir.resolve()
    repo = args.repo.resolve()
    juniper_ml_root = Path(__file__).resolve().parents[2]
    build = _load(stage_dir / "build.json", None)
    if build is None or build.get("status") != "ok":
        print(f"{stage_dir / 'build.json'} is missing or not ok")
        return 2
    base = _git(repo, "rev-parse", args.base).decode("ascii").strip()
    carrier = Path(build["worktree"])
    control = args.control_wt.resolve()
    twin = args.twin_wt.resolve()
    expected = {entry["path"]: entry["status"] for entry in build["files"]}
    problems = [f"{entry['path']}: {_sha(carrier / entry['path'])} is not the build record's {entry['sha256']}" for entry in build["files"] if _sha(carrier / entry["path"]) != entry["sha256"]]
    for name, tree, want in (("carrier", carrier, expected), ("twin", twin, expected), ("control", control, {})):
        found = _differs_from(repo, base, tree)
        if found != want:
            problems.append(f"{name} differs from {base[:8]} on {found}, not on {want}")
    problems += [f"twin {path}: not the carrier's bytes" for path in expected if _sha(twin / path) != _sha(carrier / path)]
    if problems:
        print("REFUSED: " + "; ".join(problems))
        return 2

    how = dict(item.split("=", 1) for item in args.how)
    files = []
    for entry in build["files"]:
        parent = control / entry["path"]
        files.append(
            {
                "path": entry["path"],
                "status": entry["status"],
                "sha256": entry["sha256"],
                "how": how.get(entry["path"], entry.get("how")),
                "parent_sha256": _sha(parent) if parent.is_file() else None,
                "sha256_as_built": entry.get("sha256_as_built"),
                "built_how": entry.get("built_how", entry.get("how")),
                "amended_by": entry.get("amended_by", []),
            }
        )

    deliverables = {name: _sha(stage_dir / name) for name in (*TEXTS, "stamps.json") if (stage_dir / name).is_file()}
    text_checks: dict = {}
    for name in TEXTS:
        text = (stage_dir / name).read_text(encoding="utf-8")
        checks = {"no_ci_skip_marker": SKIP_MARKER.search(text) is None, "no_trailer": TRAILER.search(text) is None, "no_attribution_footer": "Generated with" not in text and "claude.ai/code/session" not in text}
        checks["none_of_the_forbidden_strings"] = not any(word in text for word in args.forbid)
        text_checks[name] = checks
    for extra in args.forbid_in:
        clean = not any(word in extra.read_text(encoding="utf-8") for word in args.forbid)
        text_checks[str(extra)] = {"none_of_the_forbidden_strings": clean}
    forbidden_hits = [name for name, checks in text_checks.items() if not checks["none_of_the_forbidden_strings"]]
    entry_text = (stage_dir / "changelog_entry.txt").read_text(encoding="utf-8")
    text_checks["changelog_entry.txt"]["occurs_once_in_the_tree"] = (carrier / "CHANGELOG.md").read_text(encoding="utf-8").count(entry_text) == 1
    title = (stage_dir / "title.txt").read_text(encoding="utf-8")
    text_checks["title.txt"]["one_line"] = title.count("\n") == 1 and title.endswith("\n")
    text_checks["title.txt"]["length"] = len(title.strip())

    mutations = []
    for item in args.mutations:
        label, path = item.split("=", 1)
        mutations += _mutation_rows(label, Path(path))
    second_opinion = []
    if args.second_opinion_log is not None:
        for line in args.second_opinion_log.read_text(encoding="utf-8").splitlines():
            hit = VERDICT.match(line)
            if hit:
                second_opinion.append({"name": hit["name"].strip(), "exit": int(hit["exit"]), "tests": int(hit["tests"]), "failures": int(hit["failures"]), "failures_not_assertions": int(hit["other"]), "errors": int(hit["errors"]), "verdict": hit["verdict"], "note": hit["note"].strip()})
    helpers = [_screen(juniper_ml_root, helper.resolve()) for helper in args.helper]
    with open(stage_dir / "s6" / "helpers_s6.json", "w", encoding="utf-8") as fh:
        json.dump(helpers, fh, indent=1)
        fh.write("\n")

    carrier_manifest = _load(args.carrier_manifest, {})
    manifest = {
        "status": args.status,
        "repo": build["repo"],
        "carrier": build["carrier"],
        "stage": build["stage"],
        "base_sha": base,
        "base_note": "juniper-data origin/main, which holds stages 1 and 2 (juniper-data#534, #535). The carrier worktree's HEAD is the older main it was built on; its tree is base_sha plus the five files below, proved path by path by this script before it wrote this file",
        "built_on": {"m0": build["base_sha"], "carrier_base_sha": build["carrier_base_sha"], "parent_then": build["parent"]},
        "worktree": build["worktree"],
        "control_worktree": str(control),
        "mutation_twin_worktree": str(twin),
        "files": files,
        "carried": carrier_manifest.get("carried", []),
        "carried_note": carrier_manifest.get("carried_note"),
        "carrier_manifest": str(args.carrier_manifest.resolve()),
        "stamps": "see stamps.json beside this file",
        "amendments": build.get("amendments"),
        "changelog": build["changelog"],
        "applied_after": build["applied_after"],
        "checks": _load(stage_dir / "checks.json", []),
        "mutations": mutations,
        "mutations_summary": {label: {"mutants": len([row for row in mutations if row["run"] == label]), "killed": len([row for row in mutations if row["run"] == label and row["result"] == "killed"]), "survived": len([row for row in mutations if row["run"] == label and row["result"] == "survived"]), "all_restored": all(row["restored"] for row in mutations if row["run"] == label)} for label in dict.fromkeys(row["run"] for row in mutations)},
        "second_opinion": second_opinion,
        "text_changes": _load(stage_dir / "text_changes.json", []),
        "open_questions": _load(stage_dir / "open_questions.json", []),
        "if_main_moves": _load(stage_dir / "if_main_moves.json", {}),
        "deliverables_sha256": deliverables,
        "deliverable_checks": text_checks,
        "forbidden_strings": {"looked_for": len(args.forbid), "found_in": forbidden_hits},
        "helpers": helpers,
    }
    with open(stage_dir / "manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=1)
        fh.write("\n")
    bad = [f"{name}.{key}" for name, checks in text_checks.items() for key, value in checks.items() if value is False]
    dirty = [row["helper"] for row in helpers if not row["clean"]]
    print(json.dumps({"wrote": str(stage_dir / "manifest.json"), "status": args.status, "base_sha": base, "files": {row["path"]: row["sha256"] for row in files}, "checks": len(manifest["checks"]), "mutations": manifest["mutations_summary"], "second_opinion_rows": len(second_opinion), "text_changes": len(manifest["text_changes"]), "open_questions": len(manifest["open_questions"]), "failed_text_checks": bad, "helpers_not_clean": dirty}, indent=1))
    return 0 if not bad and not dirty else 1


if __name__ == "__main__":
    sys.exit(main())
