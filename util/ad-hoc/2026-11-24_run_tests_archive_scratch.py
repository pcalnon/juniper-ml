#!/usr/bin/env python3
"""
Archive the local test runner arc's scratch scripts into util/ad-hoc/, and move the arc's scratch data to the
primary checkout's tmp/ before its worktree is removed.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — one-off (the arc's cleanup: AGENTS.md § Script placement and the tmp/ retention rule)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2615, #2621 and #2629 (the local test runner, util/run_tests.py, and its two re-lands)

The arc wrote about twenty helper scripts into its worktree's ``tmp/run-tests-design/``. A script that produces,
modifies or analyzes repository content belongs in ``util/ad-hoc/`` (AGENTS.md § Script placement), and
``git worktree remove`` deletes a worktree's ``tmp/``. So:

``--archive``
    Writes each listed script to ``util/ad-hoc/<date>_run_tests_<name>.py``, ``<date>`` being the day its archived
    version was written (local time, as ``ls`` shows it). The module docstring becomes the directory's standard
    header, a hand-written purpose and the PRs it served, followed by the original docstring verbatim; the code
    after it is unchanged. Each output must parse. A file that already exists is refused, never overwritten.
``--move-data``
    Moves what is left of ``tmp/run-tests-design/`` (logs, snapshots, merge inputs, file copies, and the original
    scripts) into the primary checkout's ``tmp/``, as ``run-tests-design--<worktree name>/``, where it outlives the
    worktree. Nothing is deleted; the retention rule decides that later. Refused when the destination exists.
``--verify``
    For each archived script: the code after its docstring is byte-identical to the original's, and the original
    docstring appears verbatim in the new one. Reads the originals from ``tmp/run-tests-design/``, or from the
    moved data directory once ``--move-data`` has run.
``--dry-run``
    With ``--archive`` or ``--move-data``: print what would be written or moved, and write nothing.

Two scratch files are not archived as scripts: ``registry.main.py`` and ``run_tests.pr-head.py`` are copies of
repository files, and ``b914_control.py`` is ``b914_scan.py``'s control input, a deliberate implicit concatenation
inside a list, which CodeQL would report. All three move with the data.
"""

from __future__ import annotations

import argparse
import ast
import datetime
import shutil
import subprocess  # nosec B404 - runs git with fixed argv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRATCH = ROOT / "tmp" / "run-tests-design"
OUT_DIR = ROOT / "util" / "ad-hoc"
ARCHIVED_ON = "2026-11-24"

# name -> (purpose, related, note); the note goes after the archive paragraph, or "" for none.
SCRIPTS: dict[str, tuple[str, str, str]] = {
    "wf_steps.py": ("Print the run steps of the named workflows: the runner's design survey.", "juniper-ml#2615", ""),
    "env_survey.py": ("Survey the active interpreter, its test dependencies, and each sub-package's pytest and coverage configuration: the runner's design input.", "juniper-ml#2615", ""),
    "shlex_probe.py": ("Confirm shlex's punctuation_chars behaviour on the workflow line shapes that util/run_tests.py splits.", "juniper-ml#2615", ""),
    "precommit_repos.py": ("Map pre-commit's cache directories to their repo and rev, to find the pinned black.", "juniper-ml#2615", ""),
    "mutation_check.py": ("Mutation check for tests/test_run_tests.py: each deliberate break of util/run_tests.py must fail its named test.", "juniper-ml#2615 (its test plan: eight deliberate breaks of the runner each fail their test)", ""),
    "b914_scan.py": (
        "Report same-line implicit concatenations of string literals, the B914 shape of flake8-bugbear 26.11.22.",
        "juniper-ml#2615 (its test plan: 0 sites); main's #2609 took the B914 fixes",
        'Its control input, b914_control.py, moved with the data: it holds `x = ["a" "b"]` and `y = f"{x}" "c"`, and the scan reports both (re-run on 2026-11-24: 2 sites, exit 1).',
    ),
    "make_snapshot.py": ("Freeze the upload set into upload-snapshot/ with each file's sha256, so every signed push is made from, and verified against, one frozen copy.", "juniper-ml#2615, #2621 and #2629", ""),
    "show_ci_diff.py": ("Print main's ci.yml changes since the old base, and the head of main's new CHANGELOG entries.", "juniper-ml#2621 (the first re-land)", "It is a script because the session's worktree guard refused a command line naming the workflows directory."),
    "merge_prep.py": ("Three-way merge each edited tracked file (mine, base f74642b3, origin/main) into rehome2/, for the first re-land.", "juniper-ml#2621 (the first re-land of #2615)", ""),
    "resolve_rehome2.py": ("Resolve the first re-land's three conflicts onto origin/main, renumber what main took, and write rehome2/final/.", "juniper-ml#2621", ""),
    "final_vs_main.py": ("Count each resolved file's added and removed lines against main's copy and against the original diff, for the first re-land (rehome2/).", "juniper-ml#2621", ""),
    "apply_rehome2.py": ("Move the worktree from f74642b3 onto origin/main and write the first re-land's resolved files from rehome2/final/.", "juniper-ml#2621", ""),
    "rename_survey.py": ('Survey how main phrases the person after #2606\'s "owner" -> "Overtoad" rename, and where this arc\'s new text still said "owner".', "juniper-ml#2629 (the second re-land), after juniper-ml#2606", ""),
    "merge_prep3.py": ("The same three-way merge for the second re-land, base ca9762404a, into rehome3/.", "juniper-ml#2629", "Its original docstring was copied from the first re-land's script and still names f74642b3 and rehome2/; the code uses ca9762404a and rehome3/."),
    "resolve_rehome3.py": ('Resolve the second re-land onto origin/main b346a90a, renumber, apply the "owner" -> "Overtoad" rename to this arc\'s new text, and write rehome3/final/.', "juniper-ml#2629", ""),
    "final_vs_main3.py": ("The same line counts for the second re-land (rehome3/).", "juniper-ml#2629", "Its original docstring still names rehome2/; the code reads rehome3/."),
    "apply_rehome3.py": ("Move the worktree from ca9762404a onto origin/main (b346a90a) and write the second re-land's resolved files from rehome3/final/.", "juniper-ml#2629", "Its original docstring was copied from the first re-land's script and still names f74642b3 and rehome2/; the code checks ca9762404a and reads rehome3/."),
    "push_part.py": ("Push one part of the upload set as a signed commit through util/push_signed_commit.py, from the frozen snapshot.", "juniper-ml#2615, #2621 and #2629 (this version pushed #2629's branch, feat/local-test-runner-3)", ""),
    "verify_on_main.py": ("Compare each uploaded file's sha256 on main's squash commit with the frozen upload snapshot.", "juniper-ml#2629 (on d7709ef7, every uploaded file was byte-for-byte the snapshot)", ""),
    "watch_main_runs.py": ("Wait until every workflow run for a commit has completed, then print each one's conclusion.", "juniper-ml#2629 (main at d7709ef7: CI/CD Pipeline, Post-Merge Main Verification and CodeQL Analysis succeeded)", ""),
}


def written_on(path: Path) -> str:
    """The local date the file's current version was written: its birth time where the filesystem records one."""
    proc = subprocess.run(["stat", "-c", "%W", str(path)], capture_output=True, text=True, check=False)  # nosec B603 B607
    born = int(proc.stdout.strip() or 0) if proc.returncode == 0 else 0
    stamp = born or int(path.stat().st_mtime)
    return datetime.datetime.fromtimestamp(stamp).strftime("%Y-%m-%d")


def header(purpose: str, created: str, related: str, note: str, data_dir: str, original: str) -> str:
    archive = (
        f"Archived on {ARCHIVED_ON} from the worktree's tmp/run-tests-design/, where it was written and run; a script does\n"
        "not belong in tmp/ (AGENTS.md § Script placement). Files it names beside itself (upload-snapshot/, rehome2/,\n"
        f"rehome3/ and the like) stayed in that directory, which moved to the primary checkout's\n{data_dir}."
    )
    parts = [
        purpose,
        "",
        "Project: juniper-ml",
        "Sub-Project: ad-hoc tooling",
        "Author: Paul Calnon",
        f"Created: {created}",
        "Status: ad-hoc — one-off (a record of the local test runner arc)",
        "Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)",
        f"Related: {related}",
        "",
        archive,
    ]
    if note:
        parts += ["", note]
    parts += ["", "Original docstring, verbatim:", "", original.strip("\n")]
    return '"""\n' + "\n".join(parts) + '\n"""'


def rebuilt(source: str, new_docstring: str) -> tuple[str, str]:
    """(the file with its module docstring replaced, the original docstring's raw text)."""
    tree = ast.parse(source)
    first = tree.body[0] if tree.body else None
    if not (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str)):
        raise ValueError("no module docstring")
    segment = ast.get_source_segment(source, first)
    if segment is None or not (segment.startswith('"""') and segment.endswith('"""')):
        raise ValueError("the docstring is not a plain triple-quoted string")
    lines = source.splitlines(keepends=True)
    before = "".join(lines[: first.lineno - 1])
    after = "".join(lines[first.end_lineno :])
    return before + new_docstring + "\n" + after, segment[3:-3]


def primary_checkout() -> Path:
    common = subprocess.run(["git", "rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()  # nosec B603 B607
    return Path(common).parent


def data_destination() -> Path:
    return primary_checkout() / "tmp" / f"run-tests-design--{ROOT.name}"


def archive(dry_run: bool) -> int:
    data_dir = f"tmp/run-tests-design--{ROOT.name}/"
    failures = 0
    for name, (purpose, related, note) in SCRIPTS.items():
        src = SCRATCH / name
        created = written_on(src)
        dest = OUT_DIR / f"{created}_run_tests_{src.stem}.py"
        if dest.exists():
            print(f"REFUSED  {dest.relative_to(ROOT)} exists")
            failures += 1
            continue
        source = src.read_text(encoding="utf-8")
        _, original = rebuilt(source, '""""""')
        text, _ = rebuilt(source, header(purpose, created, related, note, data_dir, original))
        ast.parse(text)  # must still parse
        if not text.endswith("\n"):
            text += "\n"
        print(f"{'would write' if dry_run else 'wrote'}  {dest.relative_to(ROOT)}  ({len(text)} bytes)")
        if not dry_run:
            dest.write_text(text, encoding="utf-8")
    return 1 if failures else 0


def move_data(dry_run: bool) -> int:
    dest = data_destination()
    if dest.exists():
        print(f"REFUSED  {dest} exists")
        return 1
    count = sum(1 for p in SCRATCH.rglob("*") if p.is_file())
    print(f"{'would move' if dry_run else 'moving'}  {SCRATCH} ({count} files)  ->  {dest}")
    if not dry_run:
        shutil.move(str(SCRATCH), str(dest))
        print(f"moved; {sum(1 for p in dest.rglob('*') if p.is_file())} files at the destination")
    return 0


def verify() -> int:
    source_dir = SCRATCH if SCRATCH.is_dir() else data_destination()
    bad = 0
    for name in SCRIPTS:
        original = (source_dir / name).read_text(encoding="utf-8")
        matches = sorted(OUT_DIR.glob(f"20??-??-??_run_tests_{Path(name).stem}.py"))
        if len(matches) != 1:
            print(f"FAIL  {name}: {len(matches)} archived copies")
            bad += 1
            continue
        archived = matches[0].read_text(encoding="utf-8")
        orig_tail, orig_doc = rebuilt(original, "")
        new_tail, new_doc = rebuilt(archived, "")
        same_code = orig_tail == new_tail
        doc_kept = orig_doc.strip("\n") in new_doc
        ok = same_code and doc_kept
        bad += not ok
        print(f"{'ok  ' if ok else 'FAIL'}  {matches[0].relative_to(ROOT)}: code {'identical' if same_code else 'DIFFERS'}, original docstring {'kept' if doc_kept else 'MISSING'}")
    print(f"{len(SCRIPTS) - bad} of {len(SCRIPTS)} archived scripts verified against {source_dir}")
    return 1 if bad else 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--archive", action="store_true", help="write the scripts into util/ad-hoc/")
    mode.add_argument("--move-data", action="store_true", help="move the scratch directory to the primary checkout's tmp/")
    mode.add_argument("--verify", action="store_true", help="check each archived script against its original")
    parser.add_argument("--dry-run", action="store_true", help="print and write nothing")
    args = parser.parse_args(argv)
    if args.verify:
        return verify()
    missing = sorted(name for name in SCRIPTS if not (SCRATCH / name).is_file())
    if args.archive and missing:
        print(f"missing from {SCRATCH}: {', '.join(missing)}", file=sys.stderr)
        return 2
    return archive(args.dry_run) if args.archive else move_data(args.dry_run)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
