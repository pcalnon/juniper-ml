#!/usr/bin/env python3
"""
The ruling's point on today's main: #2507's tests before and after a PATCH and a MINOR proposal, with and without the carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, validation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (quick check of the ml-propose carrier, round 3b, flood-4 session 7)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14

WHY THIS EXISTS
The Overtoad ruled that #2507's tests are carried with propose.py extended, because the tests alone would fail every
juniper-ml release proposal. This measures that on the main of the day, which now holds a real hand floor raise:

* a sandbox is a fresh ``git archive`` extraction of the landing worktree's HEAD (main), kept OUTSIDE every
  juniper-ml tmp/ (it holds a pyproject.toml); the "landed" sandboxes also get the landed carrier's files;
* the tests carrier's gate file is installed as tests/test_pyproject_extras.py in every sandbox;
* a proposal is built in a child process by the sandbox's OWN propose.build_proposal (live file reads, no network:
  the open-PR list is empty) and its edits are written the way the executor commits them: each edit's whole
  new text at its path, in order;
* the gate file, its ReferenceCompatibilityMatrixTest alone and (in the landed sandboxes) the propose suite are
  run before and after, each as its own process with the six Sentry DSN variables empty.

Usage:
    python3 <this> --make --landed <landing worktree> --gate <gate file> --sims <dir> --out <dir> [--python <exe>]
    python3 <this> --build-in <sandbox> --version X.Y.Z --bump patch|minor --report <json>     (the child)
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess  # nosec B404 - fixed argv: read-only plumbing in the landing worktree, the interpreter and unittest
import sys
import tarfile
import tomllib
from pathlib import Path

SENTRY_DSN_NAMES = ("SENTRY_SDK_DSN", "SENTRY_DSN", "JUNIPER_CASCOR_SENTRY_DSN", "JUNIPER_DATA_SENTRY_DSN", "CANOPY_SENTRY_DSN", "JUNIPER_CANOPY_SENTRY_DSN")
# No test run may reach the desktop session bus: an older tree's scheduled-backup suite runs the real notify-send.
QUIET_DESKTOP = {"DBUS_SESSION_BUS_ADDRESS": "unix:path=/nonexistent/no-session-bus"}
GATE = "tests/test_pyproject_extras.py"
GATE_CLASS = "tests.test_pyproject_extras.ReferenceCompatibilityMatrixTest"
PROPOSE_SUITE = "tests/test_release_train_propose.py"
REFERENCE = "docs/REFERENCE.md"
RAN = re.compile(r"^Ran (\d+) tests? in ", re.MULTILINE)
RESULT = re.compile(r"^(OK|FAILED)(?: \((.*)\))?\s*$", re.MULTILINE)
PROBLEM = re.compile(r"^(FAIL|ERROR): (\S+) \((\S+?)\)(?: \[(.*)\]| \((.*)\))?\s*$", re.MULTILINE)
DECLARES = re.compile(r"`juniper-ml` \d+\.\d+\.\d+ declares the following pins\.")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run_tests(python: str, sandbox: Path, target: str, log: Path) -> dict:
    env = {**os.environ, **{name: "" for name in SENTRY_DSN_NAMES}, **QUIET_DESKTOP}
    done = subprocess.run([python, "-B", "-m", "unittest", "-v", target], cwd=sandbox, env=env, capture_output=True, text=True, timeout=900, check=False)  # nosec B603
    output = done.stdout + done.stderr
    log.write_text(output, encoding="utf-8")
    ran, result = RAN.findall(output), RESULT.findall(output)
    failing = sorted({m.group(2) + (f" [{m.group(4)}]" if m.group(4) else "") + (f" ({m.group(5)})" if m.group(5) else "") for m in PROBLEM.finditer(output)})
    return {
        "exit": done.returncode,
        "ran": int(ran[-1]) if ran else None,
        "result": (result[-1][0] + (f" ({result[-1][1]})" if result[-1][1] else "")) if result else None,
        "failing": failing,
        "failing_test_methods": sorted({item.split(" ")[0] for item in failing}),
    }


def build_in(sandbox: Path, version: str, bump: str, report_path: Path) -> int:
    """The child: build one juniper-ml proposal with the sandbox's own modules and write its edits."""
    sys.path.insert(0, str(sandbox / "util" / "release_train"))
    import detect  # noqa: E402 - the sandbox's own copy, by design
    import propose  # noqa: E402 - the sandbox's own copy, by design

    if not Path(propose.__file__).resolve().is_relative_to(sandbox):
        raise SystemExit(f"imported {propose.__file__}, which is not the sandbox's propose.py")
    entries = detect.load_registry(None)
    entry = {item.pypi_name: item for item in entries}["juniper-ml"]
    from_version = tomllib.loads((sandbox / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    pkg = {
        "pypi_name": "juniper-ml",
        "repo": entry.repo,
        "released_version": from_version,
        "declared_version": from_version,
        "classification": "UNRELEASED_CHANGES",
        "proposed_bump": bump,
        "proposed_version": version,
        "ship_evidence": [],
        "changelog_unreleased_categories": [],
        "changelog_conflict": None,
        "propagation_edges": [],
    }
    live = propose.make_live_sources("pcalnon", sandbox, sandbox.parent)
    sources = propose.ProposeSources(read_file=live.read_file, list_open_prs=lambda _repo: [])
    before = (sandbox / REFERENCE).read_text(encoding="utf-8")
    prop = propose.build_proposal(entry, pkg, sources, sandbox, sandbox.parent, entries, "2026-11-13")
    report = {"sandbox": str(sandbox), "propose_py_sha256": sha256(Path(propose.__file__).read_bytes()), "from_version": from_version, "to_version": prop.to_version, "bump": prop.bump, "skipped_reason": prop.skipped_reason}
    if prop.skipped:
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return 1
    paths = [edit.path for edit in prop.edits]
    report["edit_paths"] = paths
    report["paths_edited_more_than_once"] = sorted({path for path in paths if paths.count(path) > 1})
    for edit in prop.edits:
        (sandbox / edit.path).write_bytes(edit.new_text.encode("utf-8"))
    after = (sandbox / REFERENCE).read_text(encoding="utf-8")
    changed = [line for line in difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="", n=0) if line[:1] in "+-" and not line.startswith(("+++", "---"))]
    report["reference_changed_lines"] = {"removed": sum(1 for line in changed if line.startswith("-")), "added": sum(1 for line in changed if line.startswith("+")), "lines_cut_to_160": [line[:160] for line in changed]}
    old_paragraph = [line for line in before.splitlines() if DECLARES.search(line)]
    new_paragraph = [line for line in after.splitlines() if DECLARES.search(line)]
    report["paragraph_lines"] = {"before": len(old_paragraph), "after": len(new_paragraph)}
    report["paragraph_before"] = old_paragraph
    report["paragraph_after"] = new_paragraph
    version_cell = re.compile(r"^\| \*\*Version\*\* .*$", re.MULTILINE)
    report["version_cell"] = {"before": version_cell.findall(before), "after": version_cell.findall(after)}
    series_rows = re.compile(r"^\| \d+\.\d+\.x\s+\|.*$", re.MULTILINE)
    report["matrix_rows"] = {"before": series_rows.findall(before), "after": series_rows.findall(after)}
    if len(old_paragraph) == 1 and len(new_paragraph) == 1:
        old_words, new_words = old_paragraph[0].split(" "), new_paragraph[0].split(" ")
        matcher = difflib.SequenceMatcher(a=old_words, b=new_words, autojunk=False)
        report["paragraph_word_changes"] = [[" ".join(old_words[i1:i2]), " ".join(new_words[j1:j2])] for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != "equal"]
        row_sentence = re.search(r"The `0\.11\.x` row is .*?declares `>=0\.4\.1`\.", old_paragraph[0])
        report["floor_raise_sentence_on_main"] = row_sentence.group(0) if row_sentence else None
        report["floor_raise_sentence_after_the_proposal"] = "kept verbatim" if row_sentence and row_sentence.group(0) in new_paragraph[0] else "CHANGED OR ABSENT"
        service_core = "`main` raises it to `>=0.7.2,<0.8.0` (unreleased; first in juniper-ml 0.11.5)."
        report["service_core_sentence_after_the_proposal"] = "kept verbatim" if service_core in old_paragraph[0] and service_core in new_paragraph[0] else "CHANGED OR ABSENT"
    report["reference_checklist_lines"] = [item for item in prop.co_change_checklist if "docs/REFERENCE.md" in item]
    review = [item for item in prop.co_change_checklist if "prose (REVIEW by hand in this PR)" in item]
    report["review_line"] = review
    report["review_line_names"] = {needle: any(needle in item for item in review) for needle in ("is 0.11.4's", "juniper-observability", ">=0.4.2", "unreleased", "first in juniper-ml 0.11.5", "the [recurrence] clause now names", "previous series' row", "moved in place")}
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return 0


def extract(landed: Path, sandbox: Path) -> None:
    archive = subprocess.run(["git", "archive", "--format=tar", "HEAD"], cwd=landed, capture_output=True, check=True).stdout  # nosec B603 B607
    sandbox.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(sandbox, filter="data")


def make(args: argparse.Namespace) -> int:
    landed, sims, out = args.landed.resolve(), args.sims.resolve(), args.out.resolve()
    if "/juniper-ml/" in str(sims) + "/":
        raise SystemExit("--sims must be outside every juniper-ml checkout (a sandbox holds a pyproject.toml)")
    out.mkdir(parents=True, exist_ok=True)
    sims.mkdir(parents=True, exist_ok=True)
    gate_bytes = args.gate.read_bytes()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=landed, capture_output=True, text=True, check=True).stdout.strip()  # nosec B603 B607
    status = subprocess.run(["git", "status", "--porcelain"], cwd=landed, capture_output=True, text=True, check=True).stdout.splitlines()  # nosec B603 B607
    carrier_files = [line[3:] for line in status]
    summary = {"main_sha": head, "landed": str(landed), "gate_file": str(args.gate), "gate_sha256": sha256(gate_bytes), "python": args.python, "carrier_files_overlaid": len(carrier_files), "rows": []}
    scenarios = (("pristine", None, None), ("patch", args.patch_version, "patch"), ("minor", args.minor_version, "minor"))
    summary["scenarios"] = [list(item) for item in scenarios]
    for tree in ("main", "landed"):
        for scenario, version, bump in scenarios:
            name = f"{tree}--{scenario}"
            sandbox = sims / name
            if sandbox.exists():
                shutil.rmtree(sandbox)
            extract(landed, sandbox)
            if tree == "landed":
                for rel in carrier_files:
                    (sandbox / rel).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(landed / rel, sandbox / rel)
            (sandbox / GATE).write_bytes(gate_bytes)
            row = {"sandbox": name, "tree": tree, "scenario": scenario, "version": version, "propose_py_sha256": sha256((sandbox / "util/release_train/propose.py").read_bytes())}
            row["before"] = {"gate_file": run_tests(args.python, sandbox, GATE, out / f"{name}.before.gate.log"), "gate_class": run_tests(args.python, sandbox, GATE_CLASS, out / f"{name}.before.class.log")}
            if version is not None:
                child = subprocess.run([args.python, "-B", str(Path(__file__).resolve()), "--build-in", str(sandbox), "--version", version, "--bump", bump, "--report", str(out / f"{name}.proposal.json")], cwd=sandbox, env={**os.environ, **{key: "" for key in SENTRY_DSN_NAMES}, **QUIET_DESKTOP}, capture_output=True, text=True, timeout=900, check=False)  # nosec B603
                (out / f"{name}.build.log").write_text(child.stdout + child.stderr, encoding="utf-8")
                row["build_exit"] = child.returncode
                row["proposal"] = json.loads((out / f"{name}.proposal.json").read_text(encoding="utf-8")) if (out / f"{name}.proposal.json").is_file() else None
                row["after"] = {"gate_file": run_tests(args.python, sandbox, GATE, out / f"{name}.after.gate.log"), "gate_class": run_tests(args.python, sandbox, GATE_CLASS, out / f"{name}.after.class.log")}
                if tree == "landed":
                    row["after"]["propose_suite"] = run_tests(args.python, sandbox, PROPOSE_SUITE, out / f"{name}.after.propose.log")
            elif tree == "landed":
                row["before"]["propose_suite"] = run_tests(args.python, sandbox, PROPOSE_SUITE, out / f"{name}.before.propose.log")
            summary["rows"].append(row)
            (out / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
            after = row.get("after")
            print(f"{name}: before gate {row['before']['gate_file']['result']} ({row['before']['gate_file']['ran']}), class {row['before']['gate_class']['result']} ({row['before']['gate_class']['ran']})" + (f"; after gate {after['gate_file']['result']} ({after['gate_file']['ran']}), class {after['gate_class']['result']} ({after['gate_class']['ran']}), failing {after['gate_class']['failing_test_methods']}" + (f", propose suite {after['propose_suite']['result']} ({after['propose_suite']['ran']})" if "propose_suite" in after else "") if after else "") + (f"; propose suite {row['before']['propose_suite']['result']} ({row['before']['propose_suite']['ran']})" if "propose_suite" in row["before"] else ""), flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--make", action="store_true")
    parser.add_argument("--landed", type=Path)
    parser.add_argument("--gate", type=Path)
    parser.add_argument("--sims", type=Path)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--python", default="/opt/miniforge3/bin/python3.12")
    parser.add_argument("--patch-version", default="0.11.5", help="the patch proposal's version (the next patch of the tree's version)")
    parser.add_argument("--minor-version", default="0.12.0", help="the minor proposal's version")
    parser.add_argument("--build-in", type=Path)
    parser.add_argument("--version")
    parser.add_argument("--bump")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.build_in is not None:
        return build_in(args.build_in.resolve(), args.version, args.bump, args.report.resolve())
    if not args.make or not (args.landed and args.gate and args.sims and args.out):
        parser.error("--make needs --landed, --gate, --sims and --out")
    return make(args)


if __name__ == "__main__":
    sys.exit(main())
