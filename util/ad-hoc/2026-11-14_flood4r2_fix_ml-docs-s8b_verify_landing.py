#!/usr/bin/env python3
"""
Read a re-derived ml-docs landing tree the way a reviewer would: stamps, Version History, CHANGELOG position,
every applied fix visible, and the tree's changes against the main it was derived on.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (Cursor flood-4 session 8: the ml-docs carrier's fix-up, I4)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-14_flood4r2_fix_ml-docs-s8b_specs.py (the spec whose fixes are looked for);
         the carrier's util/ad-hoc/2026-11-14_flood4r2_ml-docs_rederive.py (what wrote the tree)

Checks, each recorded in --out:
  stamps     each stamped document: every Version line is main's header version plus one patch step, every
             date line is --landing-date, and main's own header and footer agreed;
  history    docs/REFERENCE.md's Version History: no version twice, the new row directly after main's row;
  changelog  the entry sits once in the top [Unreleased] '### Added' (the only one there), after that group's
             last entry with one blank line between, and before the next heading;
  fixes      every applied fix whose text lands in this tree: its new text present once, its old text absent;
  status     the tree's files against ``git ls-tree -r <main>`` (read in --repo): modified / added / deleted.

Usage:
  2026-11-14_flood4r2_fix_ml-docs-s8b_verify_landing.py --tree <landing tree> --main <sha> --repo <checkout>
      --spec <spec_apply.json> --landing-date <YYYY-MM-DD> --out <report.json>
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

STAMPED = ("docs/REFERENCE.md", "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md", "docs/DOCUMENTATION_OVERVIEW.md", "docs/QUICK_START.md")
STAMP_LINE = re.compile(r"^\*\*(Version|Last Updated|Date)(?::\*\*|\*\*:)\s*(\S+)\s*$")
HISTORY_ROW = re.compile(r"^\| (\d+\.\d+\.\d+)\s+\| (\d{4}-\d{2}-\d{2}) \|")
ENTRY_MARKER = "- **Operator documentation consolidated from the Cursor flood-4 round-2 docs drafts**"
DELIV = "tmp/flood4r2/ml-docs/"
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules"}
# A fix whose old text reaches outside the carrier's own lines (the blank line before the entry depends on which
# entry precedes it on the main in question) is checked by the changelog check instead.
OUTSIDE = {"F8#11"}


def run(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=str(repo), capture_output=True, text=True, check=True).stdout


def stamps(text: str) -> list:
    return [(number, m.group(1), m.group(2)) for number, line in enumerate(text.splitlines(), start=1) if (m := STAMP_LINE.match(line))]


def bump(version: str) -> str:
    major, minor, patch = version.split(".")
    return f"{major}.{minor}.{int(patch) + 1}"


def check_stamps(tree: Path, repo: Path, main: str, day: str) -> dict:
    out = {}
    for doc in STAMPED:
        before = stamps(run(repo, "show", f"{main}:{doc}"))
        after = stamps((tree / doc).read_text(encoding="utf-8"))
        main_versions = [value for _, kind, value in before if kind == "Version"]
        want = bump(main_versions[0])
        versions = [(n, value) for n, kind, value in after if kind == "Version"]
        dates = [(n, value) for n, kind, value in after if kind != "Version"]
        ok = len(set(main_versions)) == 1 and len(versions) >= 2 and all(v == want for _, v in versions) and dates and all(v == day for _, v in dates)
        out[doc] = {"ok": ok, "main": main_versions, "want": want, "versions": versions, "dates": dates}
    return out


def check_history(tree: Path, main_version: str, new_version: str) -> dict:
    lines = (tree / "docs/REFERENCE.md").read_text(encoding="utf-8").splitlines()
    rows = [(i, m.group(1)) for i, line in enumerate(lines) if (m := HISTORY_ROW.match(line))]
    versions = [v for _, v in rows]
    dupes = sorted({v for v in versions if versions.count(v) > 1})
    at_main = [i for i, v in rows if v == main_version]
    at_new = [i for i, v in rows if v == new_version]
    adjacent = len(at_main) == 1 and len(at_new) == 1 and at_new[0] == at_main[0] + 1
    return {"ok": not dupes and adjacent, "duplicates": dupes, "main_row_line": [i + 1 for i in at_main], "new_row_line": [i + 1 for i in at_new]}


def check_changelog(tree: Path) -> dict:
    lines = (tree / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()
    tops = [i for i, line in enumerate(lines) if line.startswith("## [")]
    top, end = tops[0], tops[1]
    added = [i for i in range(top + 1, end) if lines[i] == "### Added"]
    marks = [i for i, line in enumerate(lines) if line.startswith(ENTRY_MARKER)]
    ok = lines[top] == "## [Unreleased]" and len(added) == 1 and len(marks) == 1
    detail = {"top": lines[top], "top_line": top + 1, "added_lines": [i + 1 for i in added], "entry_lines": [i + 1 for i in marks], "next_release_heading": lines[end], "next_release_line": end + 1}
    if ok:
        at = marks[0]
        nxt = next(i for i in range(at + 1, len(lines)) if lines[i].startswith(("### ", "## ")))
        ok = added[0] < at < nxt <= end and lines[at - 1] == "" and lines[at - 2].strip() != "" and lines[nxt - 1] == ""
        detail.update({"line_before_blank": lines[at - 1] == "", "line_two_before": lines[at - 2][:100], "next_heading": lines[nxt], "next_heading_line": nxt + 1})
    return {"ok": ok, **detail}


def target(rel: str):
    if rel.startswith(DELIV + "content/docs/"):
        return "docs/" + rel[len(DELIV + "content/docs/"):]
    if rel == DELIV + "content/history_row.txt":
        return "docs/REFERENCE.md"
    if rel in (DELIV + "content/changelog_entry.txt", DELIV + "changelog_entry.txt"):
        return "CHANGELOG.md"
    if rel.startswith(DELIV):
        return None
    return rel


def check_fixes(tree: Path, spec: dict) -> dict:
    rows = []
    for edit in spec["edits"]:
        where = target(edit["file"])
        if where is None or edit["id"] in OUTSIDE:
            continue
        text = (tree / where).read_text(encoding="utf-8")
        new_count = text.count(edit["new"])
        old_count = 0 if edit["old"] in edit["new"] else text.count(edit["old"])
        rows.append({"id": edit["id"], "source": edit["file"], "in": where, "new_count": new_count, "old_count": old_count, "ok": new_count == 1 and old_count == 0})
    return {"ok": all(r["ok"] for r in rows), "checked": len(rows), "rows": rows}


def blob_id(path: Path) -> str:
    data = os.readlink(path).encode() if path.is_symlink() else path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def check_status(tree: Path, repo: Path, main: str) -> dict:
    listed = {}
    for line in run(repo, "ls-tree", "-r", main).splitlines():
        meta, path = line.split("\t", 1)
        kind, sha = meta.split()[1:]
        if kind == "blob":
            listed[path] = sha
    seen = set()
    modified, added = [], []
    for root, dirs, files in os.walk(tree):
        rel_root = Path(root).relative_to(tree)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not (rel_root == Path(".") and d == "tmp")]
        for name in files:
            rel = str((rel_root / name).as_posix()).removeprefix("./")
            seen.add(rel)
            if rel not in listed:
                added.append(rel)
            elif blob_id(Path(root) / name) != listed[rel]:
                modified.append(rel)
    deleted = sorted(p for p in listed if p not in seen and not p.startswith("tmp/"))
    return {"modified": sorted(modified), "added": sorted(added), "deleted": deleted}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tree", required=True)
    ap.add_argument("--main", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--spec", required=True)
    ap.add_argument("--landing-date", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    tree, repo = Path(args.tree), Path(args.repo)
    report = {"tree": str(tree), "main": args.main, "landing_date": args.landing_date}
    report["stamps"] = check_stamps(tree, repo, args.main, args.landing_date)
    ref = report["stamps"]["docs/REFERENCE.md"]
    report["history"] = check_history(tree, ref["main"][0], ref["want"])
    report["changelog"] = check_changelog(tree)
    report["fixes"] = check_fixes(tree, json.loads(Path(args.spec).read_text(encoding="utf-8")))
    report["status"] = check_status(tree, repo, args.main)
    report["ok"] = all(v["ok"] for v in report["stamps"].values()) and report["history"]["ok"] and report["changelog"]["ok"] and report["fixes"]["ok"]
    Path(args.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    for doc, row in report["stamps"].items():
        print(f"stamps {doc}: ok={row['ok']} main={row['main']} -> {row['want']} versions={row['versions']} dates={row['dates']}")
    print(f"history: {report['history']}")
    print(f"changelog: {json.dumps(report['changelog'])}")
    print(f"fixes: ok={report['fixes']['ok']} checked={report['fixes']['checked']} bad={[r['id'] for r in report['fixes']['rows'] if not r['ok']]}")
    print(f"status: modified={len(report['status']['modified'])} {report['status']['modified']} added={len(report['status']['added'])} deleted={report['status']['deleted']}")
    print(f"ok={report['ok']}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
