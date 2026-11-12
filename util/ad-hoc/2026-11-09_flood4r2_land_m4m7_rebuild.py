#!/usr/bin/env python3
"""
Rebuild the M-4/M-7 carrier's four shared files on the CURRENT main, after the paused-fit fix (juniper-ml#2531) bumped
the same doc stamps and opened the same juniper-service-core [Unreleased] section.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — one-off (Cursor flood-4 session 4: landing M-4/M-7, the service-core training-stream resume losses)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: <carrier>/tmp/flood4-fix/m4m7-r3/stamps.json (the re-derive rules this applies),
         util/ad-hoc/2026-11-09_flood4r2_land_snapshot.py (takes the rebuilt files via --prebuilt)

Usage:
  2026-11-09_flood4r2_land_m4m7_rebuild.py --tree <carrier> --stamps <stamps.json> --date YYYY-MM-DD --out <dir>
      [--base <sha>] [--main-ref origin/main]

Run from a juniper-ml checkout whose --main-ref is fetched (git reads THIS object store).
  docs/REFERENCE.md, docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md: the carrier's stamp sites are set back to the base's values
    and its Version History row is taken out, then ``git merge-file`` (carrier', base, main) must be clean; the header and
    footer Version become main's + 1 and the dates --date; the row, renumbered and re-dated, goes directly after the
    row of main's version (stamps.json's rule: after the highest-version row, which is not the table's last).
  CHANGELOG.md: ``git merge-file`` (carrier, base, main) must be clean; the carrier's pointer line's two versions move.
  juniper-service-core/CHANGELOG.md: structured: main's [Unreleased] holds only ``### Fixed``; the carrier's holds
    ``### Added``, ``### Changed`` and ``### Fixed``. Result: the carrier's Added and Changed blocks, then one Fixed block
    with main's bullets FIRST and the carrier's after them (the arc's CHANGELOG rule 9).
Each result is checked: main -> result is insertions plus the stamp lines only, and every carrier-added line is present.
Writes <out>/<repo path> for the four files, <out>/rebuild.json (the values used), and prints a summary.
"""

from __future__ import annotations

import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

REF = "docs/REFERENCE.md"
CHEAT = "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md"
ROOT_CL = "CHANGELOG.md"
SC_CL = "juniper-service-core/CHANGELOG.md"


def show(ref: str, path: str) -> str:
    return subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True, text=True, check=True).stdout


def merge3(carrier: str, base: str, main: str, scratch: Path, stem: str) -> str:
    files = []
    for name, text in (("carrier", carrier), ("base", base), ("main", main)):
        path = scratch / f"{stem}.{name}"
        path.write_text(text, encoding="utf-8")
        files.append(str(path))
    proc = subprocess.run(["git", "merge-file", "-p", *files], capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"REFUSED: {stem}: git merge-file reported {proc.returncode} conflict(s)")
    return proc.stdout


def bump(version: str) -> str:
    head, _, last = version.rpartition(".")
    return f"{head}.{int(last) + 1}"


def neutralize(text: str, sites: list[dict], row: dict | None) -> str:
    lines = text.split("\n")
    for site in sites:
        index = site["line_in_this_tree"] - 1
        if site["new"] not in lines[index]:
            raise SystemExit(f"REFUSED: {site['file']}:{site['line_in_this_tree']} does not hold {site['new']!r}: {lines[index]!r}")
        restored = lines[index].replace(site["new"], site["old"])
        if restored != site["text_on_main"]:
            raise SystemExit(f"REFUSED: {site['file']}:{site['line_in_this_tree']} restores to {restored!r}, not {site['text_on_main']!r}")
        lines[index] = restored
    if row is not None:
        index = row["line_in_this_tree"] - 1
        if lines[index] != row["row"]:
            raise SystemExit(f"REFUSED: the Version History row is not at {row['line_in_this_tree']}")
        del lines[index]
    return "\n".join(lines)


def restamp(text: str, version_key: str, date_keys: tuple[str, str], new_version: str, date: str) -> tuple[str, str]:
    """Set the header (first 12 lines) and footer (last 12 lines) Version and date stamps; return (text, main_version)."""
    lines = text.split("\n")
    version_re = re.compile(rf"^{re.escape(version_key)} (\S+)$")
    head_ix = [i for i in range(min(12, len(lines))) if version_re.match(lines[i])]
    foot_ix = [i for i in range(max(0, len(lines) - 12), len(lines)) if version_re.match(lines[i])]
    if len(head_ix) != 1 or len(foot_ix) != 1:
        raise SystemExit(f"REFUSED: expected one header and one footer {version_key!r} line, got {head_ix} / {foot_ix}")
    old_versions = {version_re.match(lines[i]).group(1) for i in head_ix + foot_ix}
    if len(old_versions) != 1:
        raise SystemExit(f"REFUSED: header and footer Version disagree on main: {old_versions}")
    main_version = old_versions.pop()
    for i in head_ix + foot_ix:
        lines[i] = f"{version_key} {new_version}"
    for key, window in ((date_keys[0], range(min(12, len(lines)))), (date_keys[1], range(max(0, len(lines) - 12), len(lines)))):
        date_re = re.compile(rf"^{re.escape(key)} (\d{{4}}-\d{{2}}-\d{{2}})$")
        hits = [i for i in window if date_re.match(lines[i])]
        if len(hits) != 1:
            raise SystemExit(f"REFUSED: expected one {key!r} line in its window, got {hits}")
        lines[hits[0]] = f"{key} {date}"
    return "\n".join(lines), main_version


def removed_lines(old: str, new: str) -> list[str]:
    return [line[2:] for line in difflib.ndiff(old.split("\n"), new.split("\n")) if line.startswith("- ")]


def check_insertions(main: str, result: str, carrier_removed: list[str], stamp_lines: int, label: str) -> dict:
    """main -> result may remove only lines the carrier itself removed from the base, plus ``stamp_lines`` stamp lines."""
    removed = removed_lines(main, result)
    budget = list(carrier_removed)
    foreign = []
    for line in removed:
        if line in budget:
            budget.remove(line)
        else:
            foreign.append(line)
    if len(foreign) > stamp_lines or any(not re.match(r"^\*\*(Version|Last Updated|Date)(:\*\*|\*\*:) ", line) for line in foreign):
        raise SystemExit(f"REFUSED: {label}: main lines removed that the carrier did not remove: {foreign[:6]}")
    added = [line for line in difflib.ndiff(main.split("\n"), result.split("\n")) if line.startswith("+ ")]
    return {"removed_or_changed": len(removed), "of_which_stamp_lines": len(foreign), "added": len(added)}


def sc_changelog(carrier: str, main: str) -> str:
    def unreleased(text: str) -> tuple[int, int]:
        start = text.index("## [Unreleased]\n")
        end = text.index("\n## [", start + 1) + 1
        return start, end

    m_start, m_end = unreleased(main)
    c_start, c_end = unreleased(carrier)
    m_body = main[m_start:m_end]
    c_body = carrier[c_start:c_end]
    if m_body.count("### ") != 1 or "### Fixed\n" not in m_body:
        raise SystemExit("REFUSED: main's service-core [Unreleased] is not a lone ### Fixed block any more")
    if [h for h in re.findall(r"^### (\w+)$", c_body, re.M)] != ["Added", "Changed", "Fixed"]:
        raise SystemExit("REFUSED: the carrier's service-core [Unreleased] is not Added / Changed / Fixed")
    added_changed = c_body[c_body.index("### Added\n"):c_body.index("### Fixed\n")]
    carrier_fixed = c_body[c_body.index("### Fixed\n") + len("### Fixed\n"):]
    main_head = m_body[:m_body.index("### Fixed\n")]
    main_fixed = m_body[m_body.index("### Fixed\n") + len("### Fixed\n"):]
    merged_body = main_head + added_changed + "### Fixed\n" + main_fixed.rstrip("\n") + "\n" + carrier_fixed
    return main[:m_start] + merged_body + main[m_end:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tree", required=True)
    parser.add_argument("--stamps", required=True)
    parser.add_argument("--date", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--base", default="4bae75203ff1e9cf64d49fde01a141d6cc01809a")
    parser.add_argument("--main-ref", default="origin/main")
    args = parser.parse_args()
    tree = Path(args.tree).resolve()
    stamps = json.loads(Path(args.stamps).read_text(encoding="utf-8"))
    out = Path(args.out)
    scratch = out / "merge-scratch"
    scratch.mkdir(parents=True, exist_ok=True)
    main_sha = subprocess.run(["git", "rev-parse", args.main_ref], capture_output=True, text=True, check=True).stdout.strip()
    report: dict = {"main_sha": main_sha, "base_sha": args.base, "date": args.date, "files": {}}
    results: dict[str, str] = {}

    # docs/REFERENCE.md
    sites = [s for s in stamps["stamp_sites"] if s["file"] == REF]
    row = stamps["version_history_row"]
    carrier = (tree / REF).read_text(encoding="utf-8")
    carrier_n = neutralize(carrier, sites, row)
    ref_carrier_removed = removed_lines(show(args.base, REF), carrier_n)
    merged = merge3(carrier_n, show(args.base, REF), show(main_sha, REF), scratch, "REFERENCE")
    main_ref_text = show(main_sha, REF)
    main_version = re.search(r"^\*\*Version:\*\* (\S+)$", main_ref_text, re.M).group(1)
    new_version = bump(main_version)
    merged, seen = restamp(merged, "**Version:**", ("**Last Updated:**", "**Last Updated:**"), new_version, args.date)
    if seen != main_version:
        raise SystemExit(f"REFUSED: merged REFERENCE carries {seen}, main {main_version}")
    lines = merged.split("\n")
    anchor = [i for i, line in enumerate(lines) if line.startswith(f"| {main_version} ")]
    history_versions = [tuple(int(p) for p in m.group(1).split(".")) for line in lines if (m := re.match(r"^\| (\d+\.\d+\.\d+) +\| \d{4}-\d{2}-\d{2} \|", line))]
    if len(anchor) != 1 or max(history_versions) != tuple(int(p) for p in main_version.split(".")):
        raise SystemExit(f"REFUSED: main's version row {main_version} is not the single highest row ({anchor}, max {max(history_versions)})")
    new_row = row["row"].replace("| 0.6.65  | 2026-11-09 |", f"| {new_version}  | {args.date} |", 1)
    if new_row == row["row"] and new_version != "0.6.65":
        raise SystemExit("REFUSED: could not renumber the row")
    lines.insert(anchor[0] + 1, new_row)
    results[REF] = "\n".join(lines)
    report["files"][REF] = {"main_version": main_version, "new_version": new_version, "row_after_line": anchor[0] + 1, **check_insertions(main_ref_text, results[REF], ref_carrier_removed, 4, REF)}

    # docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md
    sites = [s for s in stamps["stamp_sites"] if s["file"] == CHEAT]
    carrier = (tree / CHEAT).read_text(encoding="utf-8")
    main_cheat = show(main_sha, CHEAT)
    carrier_n = neutralize(carrier, sites, None)
    cheat_carrier_removed = removed_lines(show(args.base, CHEAT), carrier_n)
    merged = merge3(carrier_n, show(args.base, CHEAT), main_cheat, scratch, "CHEATSHEET")
    cheat_main_version = re.search(r"^\*\*Version\*\*: (\S+)$", main_cheat, re.M).group(1)
    cheat_new = bump(cheat_main_version)
    lines = merged.split("\n")
    for key, value in (("**Version**:", cheat_new), ("**Date**:", args.date)):
        hits = [i for i in range(12) if lines[i].startswith(key + " ")]
        if len(hits) != 1:
            raise SystemExit(f"REFUSED: cheatsheet header {key} hits {hits}")
        lines[hits[0]] = f"{key} {value}"
    for key, value in (("**Last Updated:**", args.date), ("**Version:**", cheat_new)):
        hits = [i for i in range(len(lines) - 12, len(lines)) if lines[i].startswith(key + " ")]
        if len(hits) != 1:
            raise SystemExit(f"REFUSED: cheatsheet footer {key} hits {hits}")
        lines[hits[0]] = f"{key} {value}"
    results[CHEAT] = "\n".join(lines)
    report["files"][CHEAT] = {"main_version": cheat_main_version, "new_version": cheat_new, **check_insertions(main_cheat, results[CHEAT], cheat_carrier_removed, 4, CHEAT)}

    # CHANGELOG.md
    carrier = (tree / ROOT_CL).read_text(encoding="utf-8")
    main_cl = show(main_sha, ROOT_CL)
    merged = merge3(carrier, show(args.base, ROOT_CL), main_cl, scratch, "CHANGELOG")
    old_line = "  - `docs/REFERENCE.md` (0.6.65) and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` (1.0.65) describe the fixed"
    new_line = f"  - `docs/REFERENCE.md` ({new_version}) and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` ({cheat_new}) describe the fixed"
    if merged.count(old_line) != 1:
        raise SystemExit("REFUSED: the CHANGELOG pointer line is not there exactly once")
    results[ROOT_CL] = merged.replace(old_line, new_line)
    report["files"][ROOT_CL] = check_insertions(main_cl, results[ROOT_CL], removed_lines(show(args.base, ROOT_CL), carrier), 0, ROOT_CL)

    # juniper-service-core/CHANGELOG.md
    carrier = (tree / SC_CL).read_text(encoding="utf-8")
    main_sc = show(main_sha, SC_CL)
    if show(args.base, SC_CL).split("## [0.7.2]", 1)[1] != main_sc.split("## [0.7.2]", 1)[1]:
        raise SystemExit("REFUSED: main changed the service-core CHANGELOG below [Unreleased] since the base")
    if carrier.split("## [0.7.2]", 1)[1] != main_sc.split("## [0.7.2]", 1)[1]:
        raise SystemExit("REFUSED: the carrier changed the service-core CHANGELOG below [Unreleased]")
    results[SC_CL] = sc_changelog(carrier, main_sc)
    report["files"][SC_CL] = check_insertions(main_sc, results[SC_CL], removed_lines(show(args.base, SC_CL), carrier), 0, SC_CL)
    carrier_added = [line for line in difflib.ndiff(show(args.base, SC_CL).split("\n"), carrier.split("\n")) if line.startswith("+ ")]
    result_lines = set(results[SC_CL].split("\n"))
    missing = [line for line in carrier_added if line[2:] not in result_lines]
    if missing:
        raise SystemExit(f"REFUSED: carrier lines missing from the merged service-core CHANGELOG: {missing[:4]}")

    for path, text in results.items():
        target = out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    (out / "rebuild.json").write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
