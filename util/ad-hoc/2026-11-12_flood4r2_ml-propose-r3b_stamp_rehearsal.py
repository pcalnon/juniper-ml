#!/usr/bin/env python3
"""
Rehearse the ml-propose carrier's landing: the same main and date, a later date, and a main that moved under it.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (finishing round 3 of the ml-propose carrier, flood-4 session 6)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14;
         util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3b_land.py (the landing command this rehearses)

WHY THIS EXISTS
The carrier lands on a later day than it was built, after other carriers that bump docs/REFERENCE.md too. The
landing command must therefore re-derive every stamp and date from main, and that has to be shown before the
landing, not at it. Four cases, each run through the landing command itself:

A. the same main and the same date: a dry run must reproduce every carrier file byte for byte, and the PR texts;
B. a later date: only the date sites may move (docs/REFERENCE.md's header, footer and history row, the
   runbook's header) and the PR body's "Stamps" line;
C. a main that moved: the files of another carrier's frozen snapshot (--overlay, a directory holding them at
   their repository paths) are committed onto a scratch worktree as a local, unsigned, never-pushed probe commit,
   and the landing is run against it as a dry run. docs/REFERENCE.md must take the number after that carrier's,
   with its history row directly after that carrier's row;
D. the same, with the modelled hand [tools] floor raise committed on top (the simulator's own model), and the
   landing written into the scratch worktree for real. The raise's cell and its sentence must survive, and the
   carrier's suite must pass in that tree.

The scratch worktree (--moved-main-worktree) is created beforehand, detached at the carrier's base, OUTSIDE every
juniper-ml tmp/ (it holds a pyproject.toml with a [project] table). It is left as case D leaves it. The carrier
itself is never written to. No child process may reach the error-reporting service: the six DSN variables are set
to the empty string.

Usage (from the worktree root):
    python3 util/ad-hoc/2026-11-12_flood4r2_ml-propose-r3b_stamp_rehearsal.py --out <scratch dir>
        --landing-date YYYY-MM-DD --later-date YYYY-MM-DD
        [--moved-main-worktree <scratch worktree at the base> --overlay <snapshot dir> [--floor-model]]
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess  # nosec B404 - fixed argv: this worktree's helpers, and probe commits in a scratch worktree
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAND = Path(__file__).with_name("2026-11-12_flood4r2_ml-propose-r3b_land.py")
SIMULATE = Path(__file__).with_name("2026-11-12_flood4r2_ml-propose-r3_simulate.py")
SCRATCH_REL = "tmp/flood4r2/ml-propose/r3b"
REFERENCE = "docs/REFERENCE.md"
RUNBOOK = "notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md"
PROPOSE_SUITE = "tests/test_release_train_propose.py"
TEXTS = ("pr_title.txt", "pr_body.txt", "commit_body.txt", "changelog_entry.txt")
SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str, check: bool = True) -> str:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=check).stdout  # nosec B603 B607


def land(out: Path, dest: Path, landing_date: str, *, dry_run: bool) -> dict:
    command = [sys.executable, "-B", str(LAND), "--carrier", str(ROOT), "--dest", str(dest), "--landing-date", landing_date, "--out", str(out)]
    if dry_run:
        command.append("--dry-run")
    done = subprocess.run(command, capture_output=True, text=True, check=False)  # nosec B603
    out.mkdir(parents=True, exist_ok=True)
    (out / "land.stdout").write_text(done.stdout + done.stderr, encoding="utf-8")
    report_path = out / "landing_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.is_file() else {"ok": False, "files": [], "problems": ["no landing report"]}
    report["exit"] = done.returncode
    return report


def changed_lines(old: str, new: str) -> list:
    """The removed (``-``) and added (``+``) lines going from ``old`` to ``new``, without context or headers."""
    diff = difflib.unified_diff(old.splitlines(), new.splitlines(), "a", "b", n=0, lineterm="")
    return [line for line in diff if line[:1] in ("-", "+") and not line.startswith(("--- a", "+++ b"))]


def assembled(out: Path, path: str) -> bytes:
    return (out / "assemble" / (Path(path).name + ".assembled")).read_bytes()


def case_same(out: Path, manifest: dict, landing_date: str) -> dict:
    report = land(out, ROOT, landing_date, dry_run=True)
    differing = [row["path"] for row in manifest["files"] if report["ok"] and sha256(assembled(out, row["path"])) != row["sha256"]]
    texts = {name: (out / "texts" / name).read_bytes() == (ROOT / SCRATCH_REL / name).read_bytes() for name in TEXTS} if report["ok"] else {}
    return {"case": "A: the same main, the same date", "landing_ok": report["ok"], "main_sha": report.get("main_sha"), "files": len(manifest["files"]), "files_not_byte_identical": differing, "texts_byte_identical": texts, "ok": report["ok"] and not differing and bool(texts) and all(texts.values())}


def case_later(out: Path, manifest: dict, later_date: str) -> dict:
    report = land(out, ROOT, later_date, dry_run=True)
    moved = {}
    for row in manifest["files"] if report["ok"] else []:
        result = assembled(out, row["path"])
        if sha256(result) != row["sha256"]:
            moved[row["path"]] = changed_lines((ROOT / row["path"]).read_text(encoding="utf-8"), result.decode("utf-8"))
    expected = {REFERENCE: 3, RUNBOOK: 1}
    counts = {path: sum(line.startswith("+") for line in lines) for path, lines in moved.items()}
    dated = all(later_date in line for lines in moved.values() for line in lines if line.startswith("+"))
    body = changed_lines((ROOT / SCRATCH_REL / "pr_body.txt").read_text(encoding="utf-8"), (out / "texts" / "pr_body.txt").read_text(encoding="utf-8")) if report["ok"] else []
    other_texts = {name: (out / "texts" / name).read_bytes() == (ROOT / SCRATCH_REL / name).read_bytes() for name in TEXTS if name != "pr_body.txt"} if report["ok"] else {}
    ok = report["ok"] and counts == expected and dated and len(body) == 2 and all(line[1:].startswith("- Stamps: ") for line in body) and all(other_texts.values())
    return {"case": f"B: the same main, a later date ({later_date})", "landing_ok": report["ok"], "lines_rewritten": counts, "expected": expected, "every_rewritten_line_carries_the_later_date": dated, "changed_lines": moved, "pr_body_changed_lines": body, "other_texts_byte_identical": other_texts, "ok": ok}


def commit_probe(tree: Path, message: str) -> str:
    git(tree, "add", "-A")
    git(tree, "-c", "commit.gpgsign=false", "commit", "--no-verify", "-q", "-m", message)
    return git(tree, "rev-parse", "HEAD").strip()


def stamp_of(text: str) -> str:
    return next(line.split()[-1] for line in text.splitlines() if line.startswith("**Version:** "))


def case_moved(out: Path, manifest: dict, tree: Path, overlay: Path, landing_date: str, floor_model: bool) -> list:
    base = manifest["base_sha"]
    if git(tree, "status", "--porcelain").strip():
        raise SystemExit("--moved-main-worktree must be clean")
    if git(tree, "rev-parse", "HEAD").strip() != base:
        # A scratch worktree an earlier rehearsal left on its probe commits: back to the carrier's base, detached.
        git(tree, "checkout", "-q", "--detach", base)
    copied = []
    for source in sorted(path for path in overlay.rglob("*") if path.is_file()):
        rel = source.relative_to(overlay).as_posix()
        target = tree / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        copied.append(rel)
    carrier_paths = {row["path"] for row in manifest["files"]}
    probe = commit_probe(tree, "probe (local, unsigned, never pushed): another carrier's frozen snapshot, as the main this carrier lands on")
    their_reference = (tree / REFERENCE).read_text(encoding="utf-8")
    report = land(out / "moved", tree, landing_date, dry_run=True)
    rows = []
    row = {
        "case": "C: a main that moved (another carrier's frozen snapshot committed on the base)",
        "probe_commit": probe,
        "overlay": str(overlay),
        "overlay_files": len(copied),
        "overlay_files_this_carrier_also_changes": sorted(carrier_paths & set(copied)),
        "main_reference_stamp": stamp_of(their_reference),
        "landing_ok": report["ok"],
        "problems": report.get("problems"),
        "methods": {item["path"]: item["method"] for item in report["files"] if "three-way" in (item.get("method") or "")},
        "conflicts": {item["path"]: item["conflicts"] for item in report["files"] if item.get("conflicts")},
        "stamp_sites": report.get("stamp_sites"),
        "pr_body_stamps_line": next((line for line in (out / "moved" / "texts" / "pr_body.txt").read_text(encoding="utf-8").splitlines() if line.startswith("- Stamps: ")), None) if report["ok"] else None,
        "ok": report["ok"],
    }
    rows.append(row)
    if not floor_model:
        return rows
    spec = importlib.util.spec_from_file_location("flood4r2_ml_propose_r3_simulate", SIMULATE)
    simulate = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = simulate
    spec.loader.exec_module(simulate)
    try:
        simulate.floor_pr(tree)
    except simulate.EditError as exc:
        rows.append({"case": "D: the modelled [tools] floor raise on top", "ok": False, "problems": [f"the floor model does not apply to this main: {exc}"]})
        return rows
    probe_floor = commit_probe(tree, "probe (local, unsigned, never pushed): the modelled hand [tools] floor raise on top")
    report = land(out / "moved-floor", tree, landing_date, dry_run=False)
    reference = (tree / REFERENCE).read_text(encoding="utf-8")
    suite = subprocess.run([sys.executable, "-B", "-m", "unittest", PROPOSE_SUITE], cwd=tree, capture_output=True, text=True, check=False, timeout=900)  # nosec B603
    (out / "moved-floor" / "propose_suite.log").write_text(suite.stdout + suite.stderr, encoding="utf-8")
    tail = (suite.stdout + suite.stderr).strip().splitlines()[-3:]
    floor_row = next((line for line in reference.splitlines() if line.startswith("| 0.11.x ")), "")
    row = {
        "case": "D: the same moved main with the modelled [tools] floor raise on top; the landing WRITTEN into the scratch worktree",
        "probe_commit": probe_floor,
        "landing_ok": report["ok"],
        "written_into_the_scratch_worktree": report.get("written_into_dest"),
        "problems": report.get("problems"),
        "conflicts": {item["path"]: item["conflicts"] for item in report["files"] if item.get("conflicts")},
        "stamp_sites": report.get("stamp_sites"),
        "floor_sentence_kept": simulate.NEW_SENTENCE in reference,
        "floor_cell_kept": ">=0.4.2" in floor_row,
        "propose_suite": {"rc": suite.returncode, "tail": tail},
        "scratch_worktree_status": git(tree, "status", "--porcelain", "--untracked-files=all").splitlines(),
    }
    row["ok"] = bool(report["ok"] and row["written_into_the_scratch_worktree"] and row["floor_sentence_kept"] and row["floor_cell_kept"] and suite.returncode == 0)
    rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--landing-date", required=True)
    parser.add_argument("--later-date", required=True)
    parser.add_argument("--moved-main-worktree", type=Path)
    parser.add_argument("--overlay", type=Path)
    parser.add_argument("--floor-model", action="store_true")
    args = parser.parse_args()
    os.environ.update(dict.fromkeys(SENTRY_DSN_NAMES, ""))
    manifest = json.loads((ROOT / SCRATCH_REL / "manifest.json").read_text(encoding="utf-8"))
    before = {row["path"]: sha256((ROOT / row["path"]).read_bytes()) for row in manifest["files"]}
    args.out.mkdir(parents=True, exist_ok=True)
    cases = [case_same(args.out / "same", manifest, args.landing_date), case_later(args.out / "later", manifest, args.later_date)]
    if args.moved_main_worktree is not None:
        if args.overlay is None or not args.overlay.is_dir():
            raise SystemExit("--moved-main-worktree wants --overlay <directory of another carrier's files>")
        cases.extend(case_moved(args.out, manifest, args.moved_main_worktree.resolve(), args.overlay.resolve(), args.landing_date, args.floor_model))
    untouched = before == {row["path"]: sha256((ROOT / row["path"]).read_bytes()) for row in manifest["files"]}
    report = {"carrier": str(ROOT), "base_sha": manifest["base_sha"], "landing_date": args.landing_date, "cases": cases, "carrier_untouched": untouched, "ok": untouched and all(case["ok"] for case in cases)}
    (args.out / "stamp_rehearsal.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for case in cases:
        print(("ok  " if case["ok"] else "FAIL"), case["case"])
    print("carrier untouched:", untouched, "|", "OK" if report["ok"] else "NOT OK")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
