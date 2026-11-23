#!/usr/bin/env python3
"""
Build juniper-data's "run the unrun tests" carrier into a landing worktree of juniper-data main d48c22e (after #538).

Project: juniper-ml
Sub-Project: ad-hoc tooling (Cursor-fleet flood-4 consolidation, landing)
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc — one-off (flood-4 session 8: landing the unrun-tests carrier on the main that holds juniper-data#538)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: tmp/flood4r2-val/d2-unrun-tests-s7/findings.json "landing_on_main.if_main_moves" (VF2's recipe, followed here)

Why: VF2 validated the carrier for a landing on main 3cf8867c and wrote the recipe for the case where juniper-data#538
merges first. It did (d48c22e, 2026-11-15T00:22:51Z), and its merged copies of CHANGELOG.md and docs/REFERENCE.md
differ from the pull-request head VF2 measured, so both three-ways are redone here against the real d48c22e.

What it writes into --landing (a detached juniper-data worktree at d48c22e), for each of the carrier's 16 paths:
  * deleted paths: removed (and juniper_data/tests/api/ once empty);
  * CHANGELOG.md: <three-way>/CHANGELOG.merged.md (git merge-file, exit 0) with the COPY/CHANGELOG.md entries of VF2's
    text_fixes.json applied (each old exactly once);
  * docs/REFERENCE.md: <three-way>/REFERENCE.merged.md with its two conflicts (the header and footer stamp blocks, and
    nothing else) resolved BY RULE to main's 0.4.9 + one step = 0.4.10 and the landing day, November 15, 2026;
  * AGENTS.md: VF2's 2026-11-15 copy (sha256 checked against its list);
  * the two testing documents: VF2's 2026-11-15 copies with F8 applied (checked: exactly that one line differs);
  * every other path: the carrier's copy, checked against its sha256_final.txt, and only where main's blob equals the
    base's (c68e6b4c) -- otherwise it refuses.
Refuses (exit 1, writes nothing) on any check that fails. Prints the sha256 of every file written.

Usage: python3 <this> --landing <worktree> --report <json>
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess  # nosec B404 - fixed argv: read-only git plumbing in the caller's own landing worktree
import sys
from pathlib import Path

WT = Path(Path.home(), "Development/python/Juniper/worktrees")
CARRIER = WT / "juniper-data--test--run-the-unrun-tests--20261112-1815--c68e6b4c"
CD = CARRIER / "tmp" / "flood4-fix" / "d2-unrun-tests"
O = Path(__file__).resolve().parents[2]
S = O / "tmp" / "flood4r2-val" / "d2-unrun-tests-s7"
T = O / "tmp" / "flood4" / "session8" / "land" / "data-unrun" / "three-way"
BASE, MAIN = "c68e6b4c", "d48c22e"
NEW_VERSION, NEW_DATE = "0.4.10", "November 15, 2026"
MAIN_VERSION, MAIN_DATE = "0.4.9", "November 14, 2026"
TESTING = ("docs/testing/TESTING_MANUAL.md", "docs/testing/TESTING_REFERENCE.md")

CONFLICT = re.compile(r"^<<<<<<< [^\n]*\n(.*?)^=======\n(.*?)^>>>>>>> [^\n]*\n", re.MULTILINE | re.DOTALL)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob(landing: Path, ref: str, path: str) -> "bytes | None":
    probe = subprocess.run(["git", "cat-file", "-e", f"{ref}:{path}"], cwd=landing, capture_output=True)  # nosec B603 B607
    if probe.returncode != 0:
        return None
    return subprocess.run(["git", "cat-file", "blob", f"{ref}:{path}"], cwd=landing, capture_output=True, check=True).stdout  # nosec B603 B607


def resolve_reference(text: str) -> "tuple[str | None, list[str]]":
    """Resolve exactly the two stamp-block conflicts by rule; anything else refuses."""
    notes: list[str] = []
    blocks = list(CONFLICT.finditer(text))
    if len(blocks) != 2:
        return None, [f"expected 2 conflicts, found {len(blocks)}"]
    header_ours = "**Version:** 0.4.8\n**Status:** Active\n**Last Updated:** November 13, 2026\n"
    header_theirs = f"**Version:** {MAIN_VERSION}\n**Status:** Active\n**Last Updated:** {MAIN_DATE}\n"
    footer_ours = "**Last Updated:** November 13, 2026\n**Version:** 0.4.8\n"
    footer_theirs = f"**Last Updated:** {MAIN_DATE}\n**Version:** {MAIN_VERSION}\n"
    wanted = [
        (header_ours, header_theirs, f"**Version:** {NEW_VERSION}\n**Status:** Active\n**Last Updated:** {NEW_DATE}\n"),
        (footer_ours, footer_theirs, f"**Last Updated:** {NEW_DATE}\n**Version:** {NEW_VERSION}\n"),
    ]
    out, last = [], 0
    for block, (ours, theirs, new) in zip(blocks, wanted):
        if block.group(1) != ours or block.group(2) != theirs:
            return None, [f"conflict at offset {block.start()} is not the expected stamp block"]
        out.append(text[last : block.start()])
        out.append(new)
        last = block.end()
        notes.append(f"stamp block at offset {block.start()} -> {new.strip()!r}")
    out.append(text[last:])
    resolved = "".join(out)
    if re.search(r"^(<<<<<<<|=======|>>>>>>>)", resolved, re.MULTILINE):
        return None, ["a conflict marker survives"]
    if resolved.count(f"**Version:** {NEW_VERSION}\n") != 2 or f"**Version:** {MAIN_VERSION}\n" in resolved:
        return None, ["the Version stamp is not exactly twice 0.4.10"]
    return resolved, notes


def apply_fixes(text: str, fixes: list[dict], target: str) -> "tuple[str | None, list[str]]":
    notes = []
    for fix in fixes:
        if fix["file"] != target:
            continue
        if text.count(fix["old"]) != 1:
            return None, [f"{fix.get('finding')}: old occurs {text.count(fix['old'])} times in {target}"]
        text = text.replace(fix["old"], fix["new"])
        notes.append(f"{fix.get('finding')} applied to {target}")
    return text, notes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--landing", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    landing = args.landing.resolve()
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=landing, capture_output=True, text=True, check=True).stdout.strip()  # nosec B603 B607
    if not head.startswith(MAIN):
        print(f"REFUSED: the landing worktree is at {head[:12]}, not {MAIN}")
        return 1
    manifest = json.loads((CD / "manifest.json").read_text(encoding="utf-8"))
    files = manifest["files"]
    recorded = {}
    for line in (CD / "sha256_final.txt").read_text(encoding="utf-8").splitlines():
        digest, _, path = line.partition("  ")
        recorded[path.strip()] = digest.strip()
    text_fixes = json.loads((S / "text_fixes.json").read_text(encoding="utf-8"))
    vf2_list = {}
    for line in (S / "proposed" / "landing_on_main_2026-11-15_sha256.txt").read_text(encoding="utf-8").splitlines():
        digest, _, path = line.partition("  ")
        vf2_list[Path(path.strip()).name if "/" not in path.strip() else path.strip()] = digest.strip()
    f8 = json.loads((S / "text_fixes_if_538_lands_first.json").read_text(encoding="utf-8"))
    plan, problems, notes = {}, [], []
    for entry in files:
        path = entry["path"] if isinstance(entry, dict) else entry
        status = entry.get("status", "") if isinstance(entry, dict) else ""
        if status.startswith("D") or status == "deleted":
            if git_blob(landing, BASE, path) != git_blob(landing, MAIN, path):
                problems.append(f"{path}: main changed a deleted path")
            plan[path] = None
            continue
        if path == "CHANGELOG.md":
            merged = (T / "CHANGELOG.merged.md").read_text(encoding="utf-8")
            fixed, why = apply_fixes(merged, text_fixes, "COPY/CHANGELOG.md")
            if fixed is None:
                problems += why
                continue
            notes += why
            plan[path] = fixed.encode("utf-8")
            continue
        if path == "docs/REFERENCE.md":
            resolved, why = resolve_reference((T / "REFERENCE.merged.md").read_text(encoding="utf-8"))
            if resolved is None:
                problems += why
                continue
            notes += why
            plan[path] = resolved.encode("utf-8")
            continue
        if path == "AGENTS.md" or path in TESTING:
            if git_blob(landing, BASE, path) != git_blob(landing, MAIN, path):
                problems.append(f"{path}: main changed it since {BASE}; VF2's copy cannot be taken as is")
                continue
            vf2 = (S / "proposed" / "landing_on_main" / path).read_bytes()
            if vf2_list.get(path) != sha(vf2):
                problems.append(f"{path}: VF2's 2026-11-15 copy does not match its sha256 list")
                continue
            if path in TESTING:
                fix = [x for x in f8 if x["file"] == f"COPY/{path}"]
                text = vf2.decode("utf-8")
                if len(fix) != 1 or text.count(fix[0]["old"]) != 1:
                    problems.append(f"{path}: F8 does not apply exactly once")
                    continue
                fixed = text.replace(fix[0]["old"], fix[0]["new"]).encode("utf-8")
                ready = (S / "vf2_if_538" / "fixed" / "COPY" / path).read_bytes()
                if fixed != ready:
                    problems.append(f"{path}: VF2's fixed copy is not its 2026-11-15 copy plus F8")
                    continue
                plan[path] = fixed
                notes.append(f"F8 applied to {path}")
            else:
                plan[path] = vf2
            continue
        data = (CARRIER / path).read_bytes()
        if recorded.get(path) != sha(data):
            problems.append(f"{path}: the carrier's copy does not match sha256_final.txt")
            continue
        if git_blob(landing, BASE, path) != git_blob(landing, MAIN, path):
            problems.append(f"{path}: main changed it since {BASE}")
            continue
        plan[path] = data
    if problems:
        for problem in problems:
            print("PROBLEM", problem)
        print("REFUSED: nothing written")
        return 1
    written = {}
    for path, data in plan.items():
        target = landing / path
        if data is None:
            target.unlink()
            written[path] = "deleted"
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        written[path] = sha(data)
    api_dir = landing / "juniper_data" / "tests" / "api"
    if api_dir.is_dir() and not any(p for p in api_dir.iterdir() if p.name != "__pycache__"):
        shutil.rmtree(api_dir)
        notes.append("juniper_data/tests/api/ removed (empty)")
    for line in notes:
        print("note", line)
    for path, value in written.items():
        print(f"{value[:16] if value != 'deleted' else 'deleted':16}  {path}")
    args.report.write_text(json.dumps({"landing": str(landing), "head": head, "base": BASE, "written": written, "notes": notes}, indent=1) + "\n", encoding="utf-8")
    print(f"OK: {len(written)} paths written into {landing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
