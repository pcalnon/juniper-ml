#!/usr/bin/env python3
"""
Build one CUMULATIVE landing stage of juniper-data's flood-4 round-2 carriers as an uncommitted tree on a fresh main.

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor flood-4 round 2: landing prep for juniper-data's three carriers)
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (the carriers were built on 4f04fc8d and validated; main has moved since)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4/BRIEF_COMMON_R2.txt rules 7-9; tmp/flood4/session4/BRIEF_S4_ADDENDUM.txt (``git merge-file`` is the
         rebuild that works); notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md

Usage:
    python3 <this> --repo <juniper-data primary> --carrier-base <sha the carrier was built on> --m0 <origin/main sha>
        --carrier <name> --carrier-wt <carrier worktree> --carrier-manifest <its manifest.json>
        --stage <N> --stage-wt <detached worktree at M0> [--parent-wt <previous stage's worktree>]
        --changelog-entry <carrier's changelog_entry.txt> --changelog-section Added|Changed|Fixed
        --out <scratch>/stage<N> [--date YYYY-MM-DD] [--apply-after <apply_after_data_docs.json>]
        [--hand <repo path>=<file holding the hand-resolved text> ...]

What it does, in order:
 1. Checks the inputs: the stage worktree's HEAD is M0, the carrier worktree's HEAD is the carrier base, and every
    carrier file still has the sha256 its validated manifest records.
 2. Resets the stage worktree to M0 (it is this script's own output), then copies in every path the parent stage
    changed, so the tree equals the parent's before the carrier goes on. With no ``--parent-wt`` the parent is M0.
 3. Takes each carrier file. Stamp lines (``**Version:**`` / ``**Last Updated:**`` in a doc's header and footer, or
    the cheat sheet's one-line header) are first put back to the carrier base's values, so the carrier contributes
    no stamp hunk. A file the parent tree did not change since the carrier base is then copied; any other is rebuilt
    three-way with ``git merge-file -p <carrier> <base> <parent>``. A conflict stops the build unless ``--hand``
    supplies the resolved text for that path.
 4. Proves each rebuilt file carries exactly the carrier's own hunks: the (removed, added) line groups of
    base -> carrier equal those of parent -> stage, as multisets.
 5. Optionally applies the required edits of ``--apply-after`` (each ``old`` must occur exactly once).
 6. Stamps: every doc this stage changes is bumped ONCE from the PARENT tree's value (patch + 1), with the given UTC
    date, header == footer. The merged text is first required to hold the parent's stamps unchanged, which is what
    catches a stale stamp that a clean merge would keep when both sides had bumped to the same value.
 7. CHANGELOG: the lines the stage adds to the parent's CHANGELOG.md must be exactly the carrier's validated entry,
    nothing may be removed, and the entry must sit under the top ``## [Unreleased]``, in the named subsection.
 8. Writes build.json, stamps.json, changelog_entry.txt and one parent -> stage diff per changed file under --out.

Exit 0 only when every check holds; 3 when a conflict needs a hand resolution. Nothing is committed, staged or pushed.
"""

from __future__ import annotations

import argparse
import collections
import datetime
import difflib
import hashlib
import json
import re
import shutil
import subprocess  # nosec B404 - fixed argv: read-only git queries, git merge-file on scratch copies, and checkout in this script's own stage worktree
import sys
from pathlib import Path

LONG_VERSION = re.compile(r"^\*\*Version:\*\* (\d+)\.(\d+)\.(\d+)$")
LONG_DATE = re.compile(r"^\*\*Last Updated:\*\* ([A-Z][a-z]+ \d{1,2}, \d{4})$")
CHEAT = re.compile(r"^\*\*Version\*\*: (\d+)\.(\d+)\.(\d+) \| \*\*Date\*\*: (\d{4}-\d{2}-\d{2}) \| (.*)$")
HEADER_LINES = 12
FOOTER_LINES = 6


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _git(cwd: Path, *argv: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(cwd), *argv], capture_output=True, check=check)  # nosec B603 B607


def _show(repo: Path, sha: str, path: str) -> bytes | None:
    proc = _git(repo, "show", f"{sha}:{path}", check=False)
    return proc.stdout if proc.returncode == 0 else None


def _changed_paths(worktree: Path) -> dict[str, str]:
    """Paths a worktree changes against its HEAD: {path: 'modified' | 'added' | 'deleted'} (ignored files excluded)."""
    out = _git(worktree, "status", "--porcelain", "--untracked-files=all").stdout.decode("utf-8")
    found: dict[str, str] = {}
    for line in out.splitlines():
        code, path = line[:2], line[3:]
        if code == "??" or "A" in code:
            found[path] = "added"
        elif "D" in code:
            found[path] = "deleted"
        else:
            found[path] = "modified"
    return found


def _sites(text: str) -> list[dict]:
    """Every stamp site of a doc: header lines near the top, footer lines near the bottom."""
    lines = text.split("\n")
    total = len(lines)
    sites: list[dict] = []
    for index, line in enumerate(lines):
        if index < HEADER_LINES:
            where = "header"
        elif index >= total - FOOTER_LINES:
            where = "footer"
        else:
            continue
        if LONG_VERSION.match(line):
            sites.append({"where": where, "kind": "version", "index": index, "text": line})
        elif LONG_DATE.match(line):
            sites.append({"where": where, "kind": "date", "index": index, "text": line})
        elif CHEAT.match(line):
            sites.append({"where": where, "kind": "version+date", "index": index, "text": line})
    return sites


def _site_keys(sites: list[dict]) -> list[tuple[str, str]]:
    return [(s["where"], s["kind"]) for s in sites]


def _with_stamps_of(text: str, donor: str) -> str:
    """``text`` with each stamp line replaced by the donor's line at the same (where, kind) site."""
    mine, theirs = _sites(text), _sites(donor)
    if _site_keys(mine) != _site_keys(theirs):
        raise SystemExit(f"stamp sites differ: {_site_keys(mine)} vs {_site_keys(theirs)}")
    lines = text.split("\n")
    for site, donor_site in zip(mine, theirs):
        lines[site["index"]] = donor_site["text"]
    return "\n".join(lines)


def _version_of(site: dict) -> tuple[int, int, int]:
    match = LONG_VERSION.match(site["text"]) or CHEAT.match(site["text"])
    if match is None:
        raise SystemExit(f"not a version stamp: {site['text']!r}")
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def _bump(text: str, date: datetime.date, path: str, parent_sites: list[dict]) -> tuple[str, list[dict]]:
    """Bump every stamp site once from the parent's value; return the new text and one record per site."""
    sites = _sites(text)
    if [s["text"] for s in sites] != [s["text"] for s in parent_sites] or _site_keys(sites) != _site_keys(parent_sites):
        raise SystemExit(f"{path}: the merged stamps are not the parent tree's: {[s['text'] for s in sites]} vs {[s['text'] for s in parent_sites]}")
    versions = {_version_of(s) for s in sites if s["kind"] in ("version", "version+date")}
    if len(versions) != 1:
        raise SystemExit(f"{path}: the parent's header and footer versions disagree: {sorted(versions)}")
    major, minor, patch = versions.pop()
    new_version = f"{major}.{minor}.{patch + 1}"
    long_date = f"{date.strftime('%B')} {date.day}, {date.year}"
    lines = text.split("\n")
    records = []
    for site in sites:
        old = site["text"]
        if site["kind"] == "version":
            new = f"**Version:** {new_version}"
        elif site["kind"] == "date":
            new = f"**Last Updated:** {long_date}"
        else:
            match = CHEAT.match(old)
            if match is None:
                raise SystemExit(f"{path}: not a cheat-sheet stamp: {old!r}")
            new = f"**Version**: {new_version} | **Date**: {date.isoformat()} | {match.group(5)}"
        lines[site["index"]] = new
        records.append({"path": path, "where": site["where"], "kind": site["kind"], "line": site["index"] + 1, "parent_value": old, "new_value": new})
    stamped = "\n".join(lines)
    after = _sites(stamped)
    header = [s["text"] for s in after if s["where"] == "header"]
    footer = [s["text"] for s in after if s["where"] == "footer"]
    if footer and sorted(header) != sorted(footer):
        raise SystemExit(f"{path}: header and footer disagree after the bump: {header} vs {footer}")
    return stamped, records


def _hunks(old: str, new: str) -> collections.Counter:
    """The (removed, added) line groups that turn ``old`` into ``new``, as a multiset."""
    a, b = old.split("\n"), new.split("\n")
    groups: collections.Counter = collections.Counter()
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag != "equal":
            groups[(tuple(a[i1:i2]), tuple(b[j1:j2]))] += 1
    return groups


def _added_and_removed(old: str, new: str) -> tuple[list[str], list[str], int]:
    """Lines ``new`` adds to ``old``, lines it removes, and the 0-based index in ``new`` of the first added line."""
    a, b = old.split("\n"), new.split("\n")
    added: list[str] = []
    removed: list[str] = []
    first = -1
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if tag in ("replace", "delete"):
            removed += a[i1:i2]
        if tag in ("replace", "insert"):
            if first < 0:
                first = j1
            added += b[j1:j2]
    return added, removed, first


def _changelog_position(text: str, first_added: int, section: str) -> dict:
    lines = text.split("\n")
    releases = [i for i, line in enumerate(lines) if line.startswith("## [")]
    top, nxt = releases[0], releases[1]
    heads = [(i, lines[i]) for i in range(top, nxt) if lines[i].startswith("### ")]
    owner = [h for h in heads if h[0] < first_added][-1]
    entries_before = [i for i in range(owner[0], first_added) if lines[i].startswith("- ")]
    return {
        "top_release_heading": lines[top],
        "entry_first_line": first_added + 1,
        "under_top_unreleased": top < first_added < nxt and lines[top].strip() == "## [Unreleased]",
        "subsection": owner[1],
        "subsection_as_expected": owner[1].strip() == f"### {section}",
        "top_level_entries_above_it_in_the_subsection": len(entries_before),
        "entry_above_starts": lines[entries_before[-1]][:120] if entries_before else None,
        "line_after_the_entry_is_a_top_level_entry_or_blank": None,
    }


def _unified(old: str, new: str, path: str) -> str:
    return "".join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True), f"parent/{path}", f"stage/{path}"))


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").strip().splitlines()[0])
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--carrier-base", required=True)
    ap.add_argument("--m0", required=True)
    ap.add_argument("--carrier", required=True)
    ap.add_argument("--carrier-wt", type=Path, required=True)
    ap.add_argument("--carrier-manifest", type=Path, required=True)
    ap.add_argument("--stage", type=int, required=True)
    ap.add_argument("--stage-wt", type=Path, required=True)
    ap.add_argument("--parent-wt", type=Path)
    ap.add_argument("--changelog-entry", type=Path, required=True)
    ap.add_argument("--changelog-section", required=True, choices=["Added", "Changed", "Fixed"])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--date", help="UTC date for the stamps (default: today, UTC)")
    ap.add_argument("--apply-after", type=Path)
    ap.add_argument("--hand", action="append", default=[], help="<repo path>=<file with the hand-resolved text>")
    args = ap.parse_args()

    repo, stage_wt, carrier_wt, out = args.repo.resolve(), args.stage_wt.resolve(), args.carrier_wt.resolve(), args.out.resolve()
    parent_wt = args.parent_wt.resolve() if args.parent_wt else None
    date = datetime.date.fromisoformat(args.date) if args.date else datetime.datetime.now(datetime.timezone.utc).date()
    hand = dict(item.split("=", 1) for item in args.hand)
    (out / "merge").mkdir(parents=True, exist_ok=True)
    (out / "diffs").mkdir(parents=True, exist_ok=True)
    problems: list[str] = []

    # 1. inputs
    m0 = _git(repo, "rev-parse", args.m0).stdout.decode().strip()
    carrier_base = _git(repo, "rev-parse", args.carrier_base).stdout.decode().strip()
    stage_head = _git(stage_wt, "rev-parse", "HEAD").stdout.decode().strip()
    carrier_head = _git(carrier_wt, "rev-parse", "HEAD").stdout.decode().strip()
    if stage_head != m0:
        raise SystemExit(f"stage worktree HEAD {stage_head} is not M0 {m0}")
    if carrier_head != carrier_base:
        raise SystemExit(f"carrier worktree HEAD {carrier_head} is not the carrier base {carrier_base}")
    carrier_manifest = json.loads(args.carrier_manifest.read_text(encoding="utf-8"))
    carrier_files = carrier_manifest["files"]
    carrier_status = _changed_paths(carrier_wt)
    if sorted(carrier_status) != sorted(f["path"] for f in carrier_files):
        raise SystemExit(f"the carrier worktree's changed paths are not its manifest's: {sorted(carrier_status)}")
    for entry in carrier_files:
        actual = _sha((carrier_wt / entry["path"]).read_bytes())
        if actual != entry["sha256"]:
            raise SystemExit(f"{entry['path']}: the carrier's copy changed since validation ({actual} != {entry['sha256']})")

    # 2. reset the stage worktree to M0, then lay down the parent stage's tree
    for path, status in _changed_paths(stage_wt).items():
        if status == "added":
            (stage_wt / path).unlink()
        else:
            _git(stage_wt, "checkout", "HEAD", "--", path)
    if _changed_paths(stage_wt):
        raise SystemExit("the stage worktree did not reset to M0")
    parent_paths: dict[str, str] = {}
    if parent_wt is not None:
        if _git(parent_wt, "rev-parse", "HEAD").stdout.decode().strip() != m0:
            raise SystemExit("the parent stage's worktree is not at M0")
        parent_paths = _changed_paths(parent_wt)
        for path, status in parent_paths.items():
            if status == "deleted":
                raise SystemExit(f"the parent stage deletes {path}; not handled")
            (stage_wt / path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(parent_wt / path, stage_wt / path)
        if _changed_paths(stage_wt) != parent_paths:
            raise SystemExit("the stage worktree does not equal the parent tree after the copy")

    # 3-4. the carrier's files
    files: list[dict] = []
    merges: list[dict] = []
    pre_stamp: dict[str, str] = {}
    parent_text: dict[str, str] = {}
    conflicts: list[str] = []
    for entry in carrier_files:
        path = entry["path"]
        carrier_bytes = (carrier_wt / path).read_bytes()
        base_bytes = _show(repo, carrier_base, path)
        target = stage_wt / path
        parent_bytes = target.read_bytes() if target.exists() else None
        if base_bytes is None:
            if parent_bytes is not None:
                raise SystemExit(f"{path}: added by the carrier but the parent tree already holds it")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(carrier_bytes)
            files.append({"path": path, "status": "added", "how": "carrier"})
            continue
        if parent_bytes is None:
            raise SystemExit(f"{path}: in the carrier base but not in the parent tree")
        carrier_text, base_text, parent = carrier_bytes.decode("utf-8"), base_bytes.decode("utf-8"), parent_bytes.decode("utf-8")
        has_stamps = bool(_sites(base_text))
        if has_stamps:
            carrier_text = _with_stamps_of(carrier_text, base_text)
        parent_text[path] = parent
        if parent_bytes == base_bytes:
            merged, how = carrier_text, "carrier"
        else:
            safe = path.replace("/", "__")
            work = out / "merge" / safe
            work.mkdir(parents=True, exist_ok=True)
            (work / "carrier").write_text(carrier_text, encoding="utf-8")
            (work / "base").write_text(base_text, encoding="utf-8")
            (work / "parent").write_text(parent, encoding="utf-8")
            proc = subprocess.run(  # nosec B603 B607
                ["git", "merge-file", "-p", "-L", f"carrier/{args.carrier}", "-L", f"base/{carrier_base[:8]}", "-L", "parent", str(work / "carrier"), str(work / "base"), str(work / "parent")],
                capture_output=True,
                check=False,
            )
            merged = proc.stdout.decode("utf-8")
            how = "three-way"
            record = {"path": path, "merge_file_exit": proc.returncode, "conflicts": proc.returncode if 0 <= proc.returncode < 127 else None, "conflict_markers": "<<<<<<< " in merged, "stderr": proc.stderr.decode("utf-8", "replace").strip()}
            if proc.returncode != 0 or record["conflict_markers"]:
                (work / "merged_with_conflicts").write_text(merged, encoding="utf-8")
                if path in hand:
                    merged = Path(hand[path]).read_text(encoding="utf-8")
                    how = "hand"
                    record["hand_resolution"] = hand[path]
                else:
                    conflicts.append(path)
                    merges.append(record)
                    continue
            merges.append(record)
        want, got = _hunks(base_text, carrier_text), _hunks(parent, merged)
        if want != got:
            problems.append(f"{path}: the stage's hunks against its parent are not the carrier's own hunks against its base ({sum(want.values())} vs {sum(got.values())} groups; how={how})")
        pre_stamp[path] = merged
        files.append({"path": path, "status": "modified", "how": how, "carrier_hunk_groups": sum(want.values()), "hunks_equal_the_carriers_own": want == got})
    if conflicts:
        (out / "build.json").write_text(json.dumps({"status": "CONFLICTS", "conflicts": conflicts, "merges": merges}, indent=1) + "\n", encoding="utf-8")
        print(f"CONFLICTS in {conflicts}: see {out / 'merge'}")
        return 3

    # 5. the edits that become due once the carrier sits on its parent
    applied_after: list[dict] = []
    if args.apply_after:
        spec = json.loads(args.apply_after.read_text(encoding="utf-8"))
        for edit in spec["edits"]:
            text = pre_stamp[edit["file"]]
            count = text.count(edit["old"])
            if count != edit.get("old_must_occur", 1):
                raise SystemExit(f"{edit['id']}: old text occurs {count} times, not {edit.get('old_must_occur', 1)}")
            pre_stamp[edit["file"]] = text.replace(edit["old"], edit["new"])
            line = text[: text.index(edit["old"])].count("\n") + 1
            applied_after.append({"id": edit["id"], "file": edit["file"], "line": line, "old_occurrences_before": count, "old_occurrences_after": pre_stamp[edit["file"]].count(edit["old"]), "new_occurrences_after": pre_stamp[edit["file"]].count(edit["new"])})
        applied_after += [{"id": e["id"], "applied": False, "why": "optional: left to the orchestrator"} for e in spec.get("optional_edits", [])]

    # 6. stamps, then write
    stamps: list[dict] = []
    for path, text in pre_stamp.items():
        parent_sites = _sites(parent_text[path])
        if parent_sites:
            text, records = _bump(text, date, path, parent_sites)
            stamps += records
        (stage_wt / path).write_text(text, encoding="utf-8")

    # 7. the CHANGELOG insertion is exactly the validated entry
    entry_text = args.changelog_entry.read_text(encoding="utf-8")
    if not entry_text.endswith("\n"):
        raise SystemExit("the validated changelog entry does not end with a newline")
    stage_changelog = (stage_wt / "CHANGELOG.md").read_text(encoding="utf-8")
    parent_changelog = parent_text["CHANGELOG.md"]
    at = stage_changelog.find(entry_text)
    if at < 0:
        raise SystemExit("CHANGELOG.md: the validated entry is not in the stage's CHANGELOG")
    first = stage_changelog[:at].count("\n")
    without = stage_changelog[:at] + stage_changelog[at + len(entry_text) :]
    added, removed, _ = _added_and_removed(parent_changelog, stage_changelog)
    changelog = {
        "validated_entry_sha256": _sha(entry_text.encode("utf-8")),
        "validated_entry_lines": entry_text.count("\n"),
        "entry_occurs_in_stage": stage_changelog.count(entry_text),
        "entry_occurs_in_parent": parent_changelog.count(entry_text),
        "entry_starts_a_line": at == 0 or stage_changelog[at - 1] == "\n",
        "stage_minus_entry_is_the_parent_byte_for_byte": without == parent_changelog,
        "difflib_added_lines": len(added),
        "difflib_removed_lines": len(removed),
        "difflib_added_equals_entry": "\n".join(added) + "\n" == entry_text,
        **_changelog_position(stage_changelog, first, args.changelog_section),
    }
    after_entry = stage_changelog.split("\n")[first + entry_text.count("\n")]
    changelog["line_after_the_entry_is_a_top_level_entry_or_blank"] = after_entry.startswith("- ") or after_entry == ""
    for key in ("entry_starts_a_line", "stage_minus_entry_is_the_parent_byte_for_byte", "under_top_unreleased", "subsection_as_expected", "line_after_the_entry_is_a_top_level_entry_or_blank"):
        if not changelog[key]:
            problems.append(f"CHANGELOG.md: {key} is false")
    if changelog["entry_occurs_in_stage"] != 1 or changelog["entry_occurs_in_parent"] != 0:
        problems.append("CHANGELOG.md: the entry must occur once in the stage and not at all in its parent")
    if removed:
        problems.append(f"CHANGELOG.md: the stage removes {len(removed)} line(s) of its parent")
    (out / "changelog_entry.txt").write_text(stage_changelog[at : at + len(entry_text)], encoding="utf-8")

    # 8. what the stage changes against its parent, and the records
    stage_paths = _changed_paths(stage_wt)
    expected = dict(parent_paths)
    for entry in files:
        expected.setdefault(entry["path"], entry["status"])
    if sorted(stage_paths) != sorted(expected):
        problems.append(f"the stage worktree's changed paths {sorted(stage_paths)} are not parent + carrier {sorted(expected)}")
    for entry in files:
        path = entry["path"]
        data = (stage_wt / path).read_bytes()
        entry["sha256"] = _sha(data)
        before = parent_text.get(path, "")
        (out / "diffs" / (path.replace("/", "__") + ".diff")).write_text(_unified(before, data.decode("utf-8"), path), encoding="utf-8")
        if path in parent_text and data.decode("utf-8") == parent_text[path]:
            problems.append(f"{path}: the stage does not change it against its parent")
    untouched = [p for p in parent_paths if p not in {f["path"] for f in files} and (stage_wt / p).read_bytes() != (parent_wt / p).read_bytes()]
    if untouched:
        problems.append(f"paths of the parent stage changed without being carrier files: {untouched}")
    build = {
        "status": "ok" if not problems else "PROBLEMS",
        "problems": problems,
        "repo": "juniper-data",
        "carrier": args.carrier,
        "stage": args.stage,
        "base_sha": m0,
        "carrier_base_sha": carrier_base,
        "worktree": str(stage_wt),
        "parent": "M0" if parent_wt is None else f"stage {args.stage - 1} ({parent_wt})",
        "stamp_date_utc": date.isoformat(),
        "files": [{"path": f["path"], "status": f["status"], "sha256": f["sha256"], "how": f["how"]} for f in files],
        "file_checks": files,
        "merges": merges,
        "applied_after": applied_after,
        "changelog": changelog,
        "worktree_changed_paths": stage_paths,
    }
    (out / "build.json").write_text(json.dumps(build, indent=1) + "\n", encoding="utf-8")
    rule = "bumped once (patch + 1) from the value in the tree this stage lands on; header == footer; dated the UTC day of the build"
    (out / "stamps.json").write_text(json.dumps({"stage": args.stage, "carrier": args.carrier, "date_utc": date.isoformat(), "rule": rule, "version_history_tables": "none of juniper-data's five stamped docs has a Version History table", "sites": stamps}, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"status": build["status"], "problems": problems, "files": [(f["path"], f["how"]) for f in files], "merges": merges, "stamps": [(s["path"], s["where"], s["kind"], s["parent_value"], s["new_value"]) for s in stamps], "changelog": changelog, "applied_after": applied_after}, indent=1))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())
