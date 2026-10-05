#!/usr/bin/env python3
"""Attack the Phase B record's archiver and re-assembly script on a scratch copy -- never on the repo.

Project:     juniper-ml
Sub-Project: ad-hoc tooling
Author:      Paul Calnon
Created:     2026-10-05
Status:      ad-hoc -- validation record
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related:     util/ad-hoc/2026-10-04_archive_phase_b_round_reports.py (the archiver under attack)
             util/ad-hoc/2026-10-05_reassemble_phase_b_record.bash (the re-assembly under attack)
             notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md

Three validation rounds on 2026-10-05 broke earlier versions of both scripts. This copies the two scripts,
the header, the record and every report file it can find into a fresh directory under --scratch, runs each
attack there, and checks the outcome:

   1  --from-files rebuilds the same record, and the record parses whole: header, sections, nothing after
   2  default mode, under --check, says IDENTICAL and exits 0
   3  a report added to ENTRIES is archived, and survives its file's deletion; --from-files refuses the
      missing file. The added report quotes a closing marker, a section opening and a WHOLE section
      (third round, N-4): none of them is read as structure
   4  removing that entry is refused as a drop; --allow-drop still names what it drops
   5  a length shortened to end at a closing marker quoted inside the body (A6) breaks the parse, and a run
      over that record is refused instead of losing what follows
   6  a length grown to swallow the next section (A7) breaks the parse
   7  a section archived twice is refused
   8  an ENTRIES origin, or a report file, that disagrees with the archived report is refused unless
      --replace names it (third round, N-2)
   9  --check compares bytes: a CRLF copy of the record is DIFFERENT, exit 1
  10  an edit to the record's header, or text appended after the last section, is refused instead of being
      silently discarded (third round, N-3)

Round 2's report files are read from ROUND2_DIR when it is set, else from the default the re-assembly script
names. Where the untracked report files are absent -- a clone of main -- the checks that need them are
SKIPPED and said to be. Nothing in the repository is written. Exit 0 only if every check that ran passed.

Usage:
    python3 util/ad-hoc/2026-10-05_attack_phase_b_archiver.py --scratch <dir>
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
ARCHIVER = "util/ad-hoc/2026-10-04_archive_phase_b_round_reports.py"
SCRIPT = "util/ad-hoc/2026-10-05_reassemble_phase_b_record.bash"
HEADER = "util/ad-hoc/2026-10-04_backup-phase-b-round3/RECORD_HEADER.md.in"
RECORD = "notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md"
NEEDED = [ARCHIVER, "util/ad-hoc/2026-09-22_archive_consensus_reports.py", SCRIPT, HEADER, RECORD]
REPORT_DIRS = ["util/ad-hoc/2026-10-04_backup-phase-b-round3", "util/ad-hoc/2026-10-04_ml2115_fix_forward"]
FAKE = "Round 9, lane Z — an attack fixture"
QUOTED_CLOSE = "\n<!-- markdownlint-enable -->\n"
R3A = "Round 3, lane A — fold-in fidelity"
R3B = "Round 3, lane B — procedure consequences"


def load(tree: Path):
    spec = importlib.util.spec_from_file_location("phase_b_archiver_under_attack", tree / ARCHIVER)
    if spec is None or spec.loader is None:
        raise SystemExit("cannot load the archiver copy")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def run(tree: Path, *args: str) -> subprocess.CompletedProcess:
    env = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}
    if "ROUND2_DIR" in os.environ:
        env["ROUND2_DIR"] = os.environ["ROUND2_DIR"]
    return subprocess.run(["bash", str(tree / SCRIPT), *args], capture_output=True, text=True, env=env, check=False)


def set_entry(tree: Path, line: str | None) -> None:
    """Append the fixture's entry to ENTRIES in the copied script, or remove it when line is None."""
    script = tree / SCRIPT
    text = re.sub(rf'\n    "{re.escape(FAKE)}\|[^\n]*"', "", script.read_text(encoding="utf-8"))
    if line is not None:
        text = text.replace("\n)\n\nmode=record", f'\n    "{line}"\n)\n\nmode=record', 1)
    script.write_text(text, encoding="utf-8")


def fixture(archiver) -> str:
    """A report that quotes the wrapper three ways: a closing marker after a blank line, a section opening,
    and a whole self-consistent section."""
    quoted = archiver.section("Quoted, not a report", "A body inside a body.\n", "nowhere")
    parts = [
        "# A fixture\n\nIt quotes the closing marker:\n",
        f"{QUOTED_CLOSE}and keeps going. It quotes an opening:\n",
        "\n---\n\n## Quoted opening\n\nArchived verbatim (12 characters\n\n",
        f"and a whole section:\n{quoted}\nThe end.\n",
    ]
    return "".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", required=True, type=Path)
    args = ap.parse_args()
    args.scratch.mkdir(parents=True, exist_ok=True)
    tree = Path(tempfile.mkdtemp(prefix="phase-b-archiver-", dir=args.scratch))
    for rel in NEEDED:
        (tree / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, tree / rel)
    for rel in REPORT_DIRS:
        (tree / rel).mkdir(parents=True, exist_ok=True)
        for report in sorted((REPO / rel).glob("*.md")) if (REPO / rel).is_dir() else []:
            shutil.copy2(report, tree / rel / report.name)
    print(f"scratch tree: {tree}")
    archiver = load(tree)
    record = tree / RECORD
    failures: list[str] = []
    skipped: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}{(': ' + detail[-500:]) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    def skip(name: str) -> None:
        print(f"  SKIP  {name}: the untracked report files are not all here")
        skipped.append(name)

    def parsed():
        return archiver.parse(record.read_text(encoding="utf-8"), record)

    def said(result: subprocess.CompletedProcess) -> str:
        return result.stdout + result.stderr

    probe = run(tree, "--from-files", "--check")
    have_files = "no such report file" not in said(probe)

    # 1, 2
    if have_files:
        check("1 --from-files --check IDENTICAL, exit 0", probe.returncode == 0 and "IDENTICAL" in probe.stdout, said(probe))
    else:
        skip("1 --from-files --check")
    whole = parsed()
    check("1 the record parses whole", not whole.remainder and len(whole.held) >= 16, f"{len(whole.held)} sections, remainder at line {whole.stopped_at_line}")
    result = run(tree, "--check")
    check("2 default --check IDENTICAL, exit 0", result.returncode == 0 and "IDENTICAL" in result.stdout, said(result))
    entries = list(whole.held)

    # 3 (and the third round's N-4)
    fake = tree / REPORT_DIRS[0] / "FAKE_ROUND9.md"
    fake.write_text(fixture(archiver), encoding="utf-8")
    set_entry(tree, f"{FAKE}|{fake}|a test fixture written by the attack script")
    result = run(tree)
    check("3 a new entry is archived", result.returncode == 0 and FAKE in parsed().held, said(result))
    check("3 nothing quoted is read as structure", list(parsed().held) == entries + [FAKE] and not parsed().remainder, str(list(parsed().held)[-3:]))
    fake.unlink()
    result = run(tree, "--check")
    check("3 once archived, it survives its file's loss", result.returncode == 0 and "IDENTICAL" in result.stdout, said(result))
    if have_files:
        result = run(tree, "--from-files", "--check")
        check("3 --from-files refuses the missing file", result.returncode != 0 and "FAKE_ROUND9.md" in said(result), said(result))
    else:
        skip("3 --from-files refuses the missing file")
    pristine = record.read_bytes()

    # 4
    set_entry(tree, None)
    result = run(tree, "--check")
    check("4 dropping an archived report is refused", result.returncode == 2 and f"WOULD DROP: {FAKE}" in result.stderr, said(result))
    result = run(tree, "--check", "--allow-drop")
    check("4 --allow-drop still names the drop", result.returncode == 1 and f"DROPPING: {FAKE}" in result.stderr, said(result))
    set_entry(tree, f"{FAKE}|{fake}|a test fixture written by the attack script")

    text = pristine.decode("utf-8")
    held = archiver.parse(text, record).held

    def opening(heading: str, within: str) -> int:
        return within.index(f"\n---\n\n## {heading}\n\nArchived verbatim (")

    def body_start(heading: str, within: str) -> int:
        return within.index(archiver.OPEN, opening(heading, within)) + len(archiver.OPEN)

    def recount(heading: str, size: int) -> str:
        at = opening(heading, text)
        old = f"Archived verbatim ({len(held[heading][0]):,} characters"
        return text[:at] + text[at:].replace(old, f"Archived verbatim ({size:,} characters", 1)

    # 5 (A6): end the fixture's length at the closing marker it quotes after a blank line.
    cut = held[FAKE][0].index("\n" + QUOTED_CLOSE) + 1
    attacked = recount(FAKE, cut)
    check("5 A6 meets a closing marker", attacked.startswith(archiver.CLOSE, body_start(FAKE, attacked) + cut))
    broken = archiver.parse(attacked, record)
    check("5 A6 breaks the parse at the fixture", FAKE not in broken.held and bool(broken.remainder))
    record.write_text(attacked, encoding="utf-8")
    fake.write_text(fixture(archiver), encoding="utf-8")
    result = run(tree, "--check")
    check("5 a run over the broken record is refused", result.returncode == 2 and "WOULD DROP" in result.stderr, said(result))
    fake.unlink()
    record.write_bytes(pristine)

    # 6 (A7): grow the first section's length to end at the SECOND section's closing marker.
    first, second = entries[0], entries[1]
    swollen = body_start(second, text) + len(held[second][0]) - body_start(first, text)
    attacked = recount(first, swollen)
    if len(f"{swollen:,}") != len(f"{len(held[first][0]):,}"):
        swollen = body_start(second, attacked) + len(held[second][0]) - body_start(first, attacked)
        attacked = recount(first, swollen)
    check("6 A7 meets a closing marker", attacked.startswith(archiver.CLOSE, body_start(first, attacked) + swollen))
    broken = archiver.parse(attacked, record)
    check("6 A7 breaks the parse at the first section", first not in broken.held and bool(broken.remainder))

    # 7
    start, stop = opening(second, text), opening(entries[2], text)
    try:
        archiver.parse(text[:stop] + text[start:stop] + text[stop:], record)
        refused = False
    except SystemExit as stopped:
        refused = "two sections" in str(stopped)
    check("7 a section archived twice is refused", refused)

    # 8 (the third round's N-2)
    script = tree / SCRIPT
    original = script.read_text(encoding="utf-8")
    line = next(row for row in original.splitlines() if row.strip().startswith(f'"{R3A}|'))
    script.write_text(original.replace(line, line.replace("2026-10-04", "2026-10-09"), 1), encoding="utf-8")
    result = run(tree, "--check")
    check("8 an edited ENTRIES origin is refused", result.returncode == 2 and f"DIFFERS: {R3A}" in result.stderr and "origin" in result.stderr, said(result))
    if have_files:
        result = run(tree, "--check", "--replace", R3A)
        check("8 --replace takes the new origin", result.returncode == 1 and "DIFFERENT" in result.stdout and "DIFFERS" not in result.stderr, said(result))
    else:
        skip("8 --replace takes the new origin")
    script.write_text(original, encoding="utf-8")
    saved = tree / REPORT_DIRS[0] / "R3B.md"
    if saved.is_file():
        before = saved.read_bytes()
        saved.write_bytes(before + b"\nA line added after the report was archived.\n")
        result = run(tree, "--check")
        check("8 a report file saved again is refused", result.returncode == 2 and f"DIFFERS: {R3B}" in result.stderr, said(result))
        saved.write_bytes(before)
    else:
        skip("8 a report file saved again is refused")

    # 9
    record.write_bytes(pristine.replace(b"\n", b"\r\n"))
    result = run(tree, "--check")
    check("9 a CRLF copy is DIFFERENT, exit 1", result.returncode == 1 and "DIFFERENT" in result.stdout, said(result))
    record.write_bytes(pristine)

    # 10 (the third round's N-3)
    edited = text.replace("**Date**:", "**Date** (edited on main):", 1)
    check("10 the header edit applied", edited != text)
    record.write_text(edited, encoding="utf-8")
    result = run(tree, "--check")
    check("10 an edited record header is refused", result.returncode == 2 and "header differs" in result.stderr, said(result))
    result = run(tree, "--check", "--accept-header")
    check("10 --accept-header lets the header file win", result.returncode == 1 and "header differs" not in result.stderr, said(result))
    record.write_text(text + "\n## Owner's note\n\nAdded by hand.\n", encoding="utf-8")
    result = run(tree, "--check")
    check("10 text after the last section is refused", result.returncode == 2 and "no intact section" in result.stderr, said(result))
    record.write_bytes(pristine)
    result = run(tree, "--check")
    check("10 the restored copy is IDENTICAL again", result.returncode == 0, said(result))

    print(f"\n{len(failures)} failure(s), {len(skipped)} skipped" + (f"; failed: {', '.join(failures)}" if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
