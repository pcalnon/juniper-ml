#!/usr/bin/env python3
"""
Simulate release proposals on two mains (today's, and today's plus the planned [tools] floor PR) under #2507's tests.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc — one-off (round 3 of the ml-propose carrier, flood-4 session 5)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 14

WHY THIS EXISTS
Ruling 14's point is that a generated release proposal passes ReferenceCompatibilityMatrixTest (juniper-ml#2507's
tests, as the tests carrier ships them). A hand "floor PR" is due on main before this carrier lands: it raises
pyproject's [tools] floors (juniper-observability to >=0.4.2, juniper-service-core to >=0.7.2,<0.8.0), moves the
`0.11.x` matrix row's observability cell and rewords the paragraph above the matrix with an exception clause. The
carrier must be right on BOTH mains, so every scenario runs on each:

* ``main``  -- a fresh `git archive HEAD` extraction of this worktree's HEAD (clean origin/main);
* ``floor`` -- the same, with the floor PR applied as exact once-only replacements (the final-check validator's
  model: 2026-11-11_flood4r2_val_ml-propose-final_floor_raise.py).

Two variants per scenario: ``unextended`` (main's propose.py and its tests) and ``carrier`` (this worktree's
changed files: code copied, the three documents rebuilt three-way onto the sandbox). Both get the tests carrier's
tests/test_pyproject_extras.py, rebuilt three-way onto the sandbox's copy. A scenario may hand-edit the sandbox
first (a floor raise between releases, moved in lockstep on every surface main's own tests pin); the gate runs
before the proposal and after it, in child interpreters, and the proposal is built by the sandbox's own
propose.build_proposal and written to disk the way the executor commits it (each edit's whole new text).

Every sandbox holds a pyproject.toml with a [project] table, so --sims-root must be OUTSIDE every juniper-ml tmp/.

Usage:
    python3 <this> --sims-root <dir outside any juniper-ml tmp/> --gate-file <tests carrier's gate file>
                   --gate-base <its base sha> --out <scratch>/sim [--python <interpreter>] [--jobs 4]
                   [--only <scenario>] [--mains main,floor] [--variants unextended,carrier]
                   [--carrier-override <repo-relative code file>=<variant file>]
    python3 <this> --child-build <sandbox> --package <pypi name> --bump <patch|minor> --released <version>
"""

from __future__ import annotations

import argparse
import dataclasses
import difflib
import io
import json
import re
import shutil
import subprocess  # nosec B404 - fixed argv: git plumbing in this script's own worktree, and child interpreters
import sys
import tarfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
GATE_REL = "tests/test_pyproject_extras.py"
GATE_CLASS = "tests.test_pyproject_extras.ReferenceCompatibilityMatrixTest"
PROPOSE_SUITE = "tests/test_release_train_propose.py"
RUNBOOK_REL = "notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md"
CARRIER_COPY = ("util/release_train/propose.py", PROPOSE_SUITE)
CARRIER_MERGE = ("CHANGELOG.md", "docs/REFERENCE.md", RUNBOOK_REL)
RELEASE_DATE = "2026-11-12"
OLD_SENTENCE = "The `0.11.x` row is 0.11.4's, and its floors are 0.11.2's."
NEW_SENTENCE = (
    "The `0.11.x` row is 0.11.4's, and its floors are 0.11.2's, except the `juniper-observability` cell: it is main's `>=0.4.2`, which 0.11.5 will publish, "
    "while the published 0.11.4 declares `>=0.4.1`. Main also raises `juniper-service-core`, which has no column here, to `>=0.7.2,<0.8.0`."
)
SPLIT_BEFORE = "The three `recurrence` pins have no columns here."
INLINE_TABLES = ("AGENTS.md", "README.md", "docs/QUICK_START.md")
SPLIT_TABLES = ("README.md", "docs/REFERENCE.md")


class EditError(RuntimeError):
    """A hand edit did not find its anchor exactly once: the scenario does not apply to this tree as written."""


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, check=check)  # nosec B603 B607


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise EditError(f"{path}: expected exactly one {old!r}, found {text.count(old)}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def replace_in_line(path: Path, line_marker: str, old: str, new: str) -> None:
    """Replace ``old`` once, inside the single line that contains ``line_marker``."""
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    hits = [i for i, line in enumerate(lines) if line_marker in line and old in line]
    if len(hits) != 1 or lines[hits[0]].count(old) != 1:
        raise EditError(f"{path}: expected one line with {line_marker!r} and one {old!r} in it, found {len(hits)}")
    lines[hits[0]] = lines[hits[0]].replace(old, new)
    path.write_text("".join(lines), encoding="utf-8")


def current_pin(sandbox: Path, package: str) -> str:
    """The requirement pyproject.toml holds for ``package``, e.g. ``juniper-observability>=0.4.1``."""
    found = set(re.findall(r'"(' + re.escape(package) + r'>=[^"]+)"', (sandbox / "pyproject.toml").read_text(encoding="utf-8")))
    if len(found) != 1:
        raise EditError(f"{sandbox}: expected one pin for {package}, found {sorted(found)}")
    return found.pop()


def raised(pin: str) -> str:
    """``juniper-x>=0.4.1,<0.5.0`` -> ``juniper-x>=0.4.2,<0.5.0``: the floor's patch number plus one."""
    m = re.match(r"^(.*>=\d+\.\d+\.)(\d+)(.*)$", pin)
    if m is None:
        raise EditError(f"cannot raise {pin!r}")
    return f"{m.group(1)}{int(m.group(2)) + 1}{m.group(3)}"


def move_pin(sandbox: Path, old: str, new: str, *, lockstep: bool = True) -> "tuple[str, str]":
    """Move one requirement in pyproject.toml and, with ``lockstep``, on every surface main's own tests pin to
    it: the membership list in the gate file, the three inline extras tables, and the split-column rows of
    README.md and docs/REFERENCE.md. -> (old spec, new spec), the part after the package name."""
    package = re.match(r"^[a-z0-9-]+", old).group(0)
    old_spec, new_spec = old[len(package) :], new[len(package) :]
    replace_once(sandbox / "pyproject.toml", f'"{old}"', f'"{new}"')
    if lockstep:
        replace_once(sandbox / GATE_REL, f'"{old}"', f'"{new}"')
        for rel in INLINE_TABLES:
            replace_once(sandbox / rel, f"`{old}`", f"`{new}`")
        for rel in SPLIT_TABLES:
            replace_in_line(sandbox / rel, f"| `{package}` ", f"`{old_spec}`", f"`{new_spec}`")
    return old_spec, new_spec


def floor_pr(sandbox: Path) -> None:
    """The planned hand floor PR, as the final-check validator modelled it (lockstep, the cell, the paragraph)."""
    move_pin(sandbox, "juniper-observability>=0.4.1", "juniper-observability>=0.4.2")
    move_pin(sandbox, "juniper-service-core>=0.7.1,<0.8.0", "juniper-service-core>=0.7.2,<0.8.0")
    reference = sandbox / "docs" / "REFERENCE.md"
    replace_in_line(reference, "| 0.11.x ", ">=0.4.1 ", ">=0.4.2 ")
    replace_once(reference, OLD_SENTENCE, NEW_SENTENCE)


def raise_column_floor(sandbox: Path, *, rewrite_row: bool) -> None:
    """A hand raise, between releases, of a [tools] floor that HAS a matrix column (juniper-observability)."""
    old = current_pin(sandbox, "juniper-observability")
    old_spec, new_spec = move_pin(sandbox, old, raised(old))
    if rewrite_row:
        replace_in_line(sandbox / "docs" / "REFERENCE.md", "| 0.11.x ", f"{old_spec} ", f"{new_spec} ")


def raise_nocolumn_floor(sandbox: Path) -> None:
    """A hand raise of a [tools] floor that has NO matrix column (juniper-service-core)."""
    old = current_pin(sandbox, "juniper-service-core")
    move_pin(sandbox, old, raised(old))


def raise_recurrence_floor(sandbox: Path, *, rewrite_clause: bool) -> None:
    """A hand raise of a [recurrence] floor; the paragraph's "sets them to" clause is that pin's only record."""
    old = current_pin(sandbox, "juniper-recurrence")
    new = raised(old)
    move_pin(sandbox, old, new)
    if rewrite_clause:
        replace_in_line(sandbox / "docs" / "REFERENCE.md", " sets them to ", f"`{old}`", f"`{new}`")


def split_paragraph(sandbox: Path) -> None:
    """Part the "sets them to" clause from the "declares" sentence with a paragraph break (final-check F2)."""
    replace_once(sandbox / "docs" / "REFERENCE.md", " " + SPLIT_BEFORE, "\n\n" + SPLIT_BEFORE)


def no_hand_edit(sandbox: Path) -> None:
    """A scenario with no hand edit before the proposal."""
    if not (sandbox / "pyproject.toml").is_file():
        raise EditError(f"{sandbox}: not an extraction")


def column_raise_row_left(sandbox: Path) -> None:
    raise_column_floor(sandbox, rewrite_row=False)


def column_raise_row_rewritten(sandbox: Path) -> None:
    raise_column_floor(sandbox, rewrite_row=True)


def recurrence_raise_clause_left(sandbox: Path) -> None:
    raise_recurrence_floor(sandbox, rewrite_clause=False)


def recurrence_raise_clause_rewritten(sandbox: Path) -> None:
    raise_recurrence_floor(sandbox, rewrite_clause=True)


#: name -> (hand edit, bump or None for "no proposal")
SCENARIOS = {
    "pristine": (no_hand_edit, None),
    "patch": (no_hand_edit, "patch"),
    "minor": (no_hand_edit, "minor"),
    "column-raise-row-rewritten-then-patch": (column_raise_row_rewritten, "patch"),
    "column-raise-row-rewritten-then-minor": (column_raise_row_rewritten, "minor"),
    "column-raise-row-left-then-patch": (column_raise_row_left, "patch"),
    "nocolumn-raise-then-patch": (raise_nocolumn_floor, "patch"),
    "recurrence-raise-clause-rewritten-then-patch": (recurrence_raise_clause_rewritten, "patch"),
    "recurrence-raise-clause-left-then-patch": (recurrence_raise_clause_left, "patch"),
    "paragraph-split-then-patch": (split_paragraph, "patch"),
}


def child_build(sandbox: Path, package: str, bump: str, released: str) -> int:
    """Runs INSIDE a child interpreter: build one proposal with the sandbox's own propose.py and write its edits."""
    sys.path.insert(0, str(sandbox / "util" / "release_train"))
    import detect  # noqa: PLC0415 - the sandbox's copy, importable only after the path insert
    import propose  # noqa: PLC0415

    entries = detect.load_registry(None)
    entry = next(e for e in entries if e.pypi_name == package)
    live = propose.make_live_sources("pcalnon", sandbox, sandbox.parent)
    sources = dataclasses.replace(live, list_open_prs=lambda repo: [])
    pkg = {"pypi_name": package, "repo": entry.repo, "classification": propose.PROPOSABLE, "released_version": released, "declared_version": released, "proposed_bump": bump}
    prop = propose.build_proposal(entry, pkg, sources, sandbox, sandbox.parent, entries, RELEASE_DATE)
    paths = [edit.path for edit in prop.edits]
    ref_diff = ""
    for edit in prop.edits:
        if edit.path == "docs/REFERENCE.md":
            ref_diff = "".join(difflib.unified_diff(edit.old_text.splitlines(keepends=True), edit.new_text.splitlines(keepends=True), "a/docs/REFERENCE.md", "b/docs/REFERENCE.md", n=0))
        target = sandbox / edit.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(edit.new_text, encoding="utf-8")
    result = {
        "to_version": prop.to_version,
        "skipped_reason": prop.skipped_reason,
        "edit_paths": paths,
        "duplicate_edit_paths": sorted({p for p in paths if paths.count(p) > 1}),
        "reference_checklist": [item for item in prop.co_change_checklist if "docs/REFERENCE.md" in item],
        "checklist_len": len(prop.co_change_checklist),
        "reference_diff": ref_diff,
    }
    print(json.dumps(result))
    return 0


def extract_main(sandbox: Path) -> None:
    if sandbox.exists():
        shutil.rmtree(sandbox)
    archive = git("archive", "--format=tar", "HEAD")
    sandbox.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as tar:
        tar.extractall(sandbox, filter="data")


def merge_onto(sandbox: Path, rel: str, ours: bytes, base: bytes, work: Path) -> int:
    """Write ``ours`` into the sandbox, three-way against ``base`` when the sandbox's copy has moved from it."""
    target = sandbox / rel
    theirs = target.read_bytes()
    if theirs == base:
        target.write_bytes(ours)
        return 0
    work.mkdir(parents=True, exist_ok=True)
    stem = work / rel.replace("/", "__")
    ours_path, base_path = Path(f"{stem}.ours"), Path(f"{stem}.base")
    ours_path.write_bytes(ours)
    base_path.write_bytes(base)
    merged = git("merge-file", "-p", str(ours_path), str(base_path), str(target), check=False)
    target.write_bytes(merged.stdout)
    return merged.returncode


def install(sandbox: Path, variant: str, gate_file: Path, gate_base: str, work: Path, overrides: dict) -> dict:
    """The tests carrier's gate file, and for ``carrier`` this worktree's five changed files (``overrides`` then
    replaces any of the copied code files with a variant under study). -> conflict counts."""
    conflicts = {GATE_REL: merge_onto(sandbox, GATE_REL, gate_file.read_bytes(), git("show", f"{gate_base}:{GATE_REL}").stdout, work)}
    if variant == "carrier":
        for rel in CARRIER_COPY:
            shutil.copyfile(overrides.get(rel, REPO / rel), sandbox / rel)
        for rel in CARRIER_MERGE:
            conflicts[rel] = merge_onto(sandbox, rel, (REPO / rel).read_bytes(), git("show", f"HEAD:{rel}").stdout, work)
    return conflicts


def run_tests(python: str, sandbox: Path, selector: str) -> dict:
    done = subprocess.run([python, "-B", "-m", "unittest", "-v", selector], cwd=sandbox, capture_output=True, text=True, check=False, timeout=900)  # nosec B603
    output = done.stdout + done.stderr
    ran = re.search(r"^Ran (\d+) tests?", output, re.MULTILINE)
    failing = sorted(set(re.findall(r"^(?:FAIL|ERROR): (test_\w+) \([\w.]+\)(?: \(([^)]*)\))?", output, re.MULTILINE)))
    return {"rc": done.returncode, "ran": int(ran.group(1)) if ran else None, "failing": [name + (f" [{sub}]" if sub else "") for name, sub in failing]}


def paragraph_line(sandbox: Path) -> str:
    return next(line for line in (sandbox / "docs" / "REFERENCE.md").read_text(encoding="utf-8").splitlines() if "declares the following pins." in line and line.startswith("`juniper-ml` "))


def gates(python: str, sandbox: Path) -> dict:
    return {"gate_class": run_tests(python, sandbox, GATE_CLASS), "gate_file": run_tests(python, sandbox, GATE_REL), "propose_suite": run_tests(python, sandbox, PROPOSE_SUITE)}


def run_row(args: argparse.Namespace, main_kind: str, name: str, variant: str) -> dict:
    hand, bump = SCENARIOS[name]
    sandbox = args.sims_root / f"{main_kind}--{name}--{variant}"
    work = args.out / "work" / sandbox.name
    row = {"main": main_kind, "scenario": name, "variant": variant, "sandbox": str(sandbox)}
    extract_main(sandbox)
    try:
        if main_kind == "floor":
            floor_pr(sandbox)
        row["conflicts"] = install(sandbox, variant, args.gate_file, args.gate_base, work, args.overrides)
        hand(sandbox)
    except EditError as exc:
        row["edit_error"] = str(exc)
        return row
    row["before"] = gates(args.python, sandbox)
    if bump is None:
        return row
    paragraph_before = paragraph_line(sandbox)
    released = re.search(r'^version = "([^"]+)"', (sandbox / "pyproject.toml").read_text(encoding="utf-8"), re.MULTILINE).group(1)
    child = subprocess.run([args.python, "-B", str(Path(__file__).resolve()), "--child-build", str(sandbox), "--package", "juniper-ml", "--bump", bump, "--released", released], capture_output=True, text=True, check=False, timeout=900)  # nosec B603
    if child.returncode != 0:
        row["build_error"] = (child.stdout + child.stderr)[-2000:]
        return row
    row["proposal"] = json.loads(child.stdout.strip().splitlines()[-1])
    paragraph_after = paragraph_line(sandbox)
    old_words, new_words = paragraph_before.split(" "), paragraph_after.split(" ")
    matcher = difflib.SequenceMatcher(a=old_words, b=new_words, autojunk=False)
    row["paragraph_word_changes"] = [[" ".join(old_words[i1:i2]), " ".join(new_words[j1:j2])] for tag, i1, i2, j1, j2 in matcher.get_opcodes() if tag != "equal"]
    if NEW_SENTENCE in paragraph_before:
        row["exception_clause_after_proposal"] = "kept verbatim" if NEW_SENTENCE in paragraph_after else "CHANGED"
        row["review_line_names_the_exception_clause"] = any("except the `juniper-observability` cell" in item or "will publish" in item for item in row["proposal"]["reference_checklist"])
    row["after"] = gates(args.python, sandbox)
    return row


def summarize(row: dict) -> str:
    def cell(state: "dict | None") -> str:
        if state is None:
            return "-"
        return " ".join(f"{key}={value['ran']}{'ok' if value['rc'] == 0 else 'FAIL' + str(len(value['failing']))}" for key, value in state.items())

    return f"{row['main']:5s} {row['scenario']:46s} {row['variant']:10s} to={row.get('proposal', {}).get('to_version')} | before: {cell(row.get('before'))} | after: {cell(row.get('after'))}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--child-build", type=Path)
    parser.add_argument("--package")
    parser.add_argument("--bump")
    parser.add_argument("--released")
    parser.add_argument("--sims-root", type=Path)
    parser.add_argument("--gate-file", type=Path)
    parser.add_argument("--gate-base")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--jobs", type=int, default=4)
    parser.add_argument("--only", action="append")
    parser.add_argument("--mains", default="main,floor")
    parser.add_argument("--variants", default="unextended,carrier")
    parser.add_argument("--carrier-override", action="append", default=[], metavar="REL=PATH", help="in the carrier variant, take this copied code file from PATH instead of this worktree (a variant under study)")
    args = parser.parse_args()
    if args.child_build is not None:
        return child_build(args.child_build, args.package, args.bump, args.released)
    args.overrides = {}
    for item in args.carrier_override:
        rel, _, source = item.partition("=")
        if rel not in CARRIER_COPY or not Path(source).is_file():
            raise SystemExit(f"--carrier-override wants one of {CARRIER_COPY}=<existing file>, got {item!r}")
        args.overrides[rel] = Path(source)
    args.out.mkdir(parents=True, exist_ok=True)
    args.sims_root.mkdir(parents=True, exist_ok=True)
    plan = [(main_kind, name, variant) for main_kind in args.mains.split(",") for name in (args.only or list(SCENARIOS)) for variant in args.variants.split(",")]
    with ThreadPoolExecutor(max_workers=max(1, min(args.jobs, 4))) as pool:
        rows = list(pool.map(lambda item: run_row(args, *item), plan))
    for row in rows:
        (args.out / f"{row['main']}--{row['scenario']}--{row['variant']}.json").write_text(json.dumps(row, indent=2) + "\n", encoding="utf-8")
        print(summarize(row))
    head = git("rev-parse", "HEAD").stdout.decode().strip()
    overrides = {rel: str(source) for rel, source in args.overrides.items()}
    (args.out / "summary.json").write_text(json.dumps({"head": head, "python": args.python, "gate_file": str(args.gate_file), "gate_base": args.gate_base, "carrier_overrides": overrides, "rows": rows}, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
