#!/usr/bin/env python3
"""
Independent Sequence-Safety docs screen, heading census and anchor check for the juniper-canopy flood-4 DOCS carrier.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-canopy DOCS carrier VALIDATION)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-canopy#790 #791 #793 #796; flood-4 validation brief (claims/fidelity lens)

Reads git objects only; writes nothing to any repository.

1. Loads juniper-ci-tools' docs_additions_check.py SOURCE from a juniper-ml tag (the published 0.9.1 is what
   CI's `juniper-ci-tools>=0.9.0,<0.10.0` resolves to) and runs its run() exactly as sequence-safety.yml's
   CLI call does (repo root, base, head, no --files, default --min-run, no --scope). Then re-classifies the
   same hunks WITHOUT fence maps (the pre-0.9.1 behaviour the host's 0.8.0 has), for comparison.
2. Heading census per changed .md file: headings (outside fences) at BASE vs HEAD; any BASE heading absent
   at HEAD (removed or renamed) is listed; duplicate slugs at HEAD are listed (GitHub suffixes -1, -2).
3. Anchor check: every markdown link in every tracked .md file at HEAD whose target is one of the changed
   files (or a same-file anchor inside a changed file) must name an anchor that exists at HEAD.

    python3 2026-11-07_flood4_val_canopy_docs_screens.py <juniper-ml worktree> <ci-tools tag> <canopy repo/worktree> <base sha> <head sha>
"""

from __future__ import annotations

import json
import re
import subprocess  # nosec B404 -- fixed argv, no shell
import sys
import types
from pathlib import PurePosixPath


def _git(root: str, *args: str) -> str:
    return subprocess.run(["git", "-C", root, *args], check=True, capture_output=True, text=True).stdout


def load_module(ml_root: str, tag: str) -> types.ModuleType:
    src = _git(ml_root, "show", f"{tag}:juniper-ci-tools/juniper_ci_tools/docs_additions_check.py")
    mod = types.ModuleType("docs_additions_check_from_tag")
    mod.__file__ = f"<{tag}>/docs_additions_check.py"
    sys.modules[mod.__name__] = mod
    exec(compile(src, mod.__file__, "exec"), mod.__dict__)  # nosec B102 -- the package's own source at a tag
    return mod


_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})(.*)$")
_HEADING_RE = re.compile(r"^ {0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
_LINK_RE = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")


def headings(text: str, fenced: set[int]) -> list[tuple[int, int, str]]:
    out = []
    for n, line in enumerate(text.split("\n"), start=1):
        if n in fenced:
            continue
        m = _HEADING_RE.match(line)
        if m:
            out.append((n, len(m.group(1)), m.group(2)))
    return out


def slug(text: str) -> str:
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    t = t.replace("`", "").lower()
    t = re.sub(r"[^\w\- ]", "", t, flags=re.UNICODE)
    return t.replace(" ", "-")


def slugs_with_dups(hs: list[tuple[int, int, str]]) -> tuple[set[str], list[str]]:
    seen: dict[str, int] = {}
    out: set[str] = set()
    dups: list[str] = []
    for _, _, text in hs:
        s = slug(text)
        if s in seen:
            seen[s] += 1
            out.add(f"{s}-{seen[s]}")
            dups.append(s)
        else:
            seen[s] = 0
            out.add(s)
    return out, dups


def main() -> int:
    ml_root, tag, root, base, head = sys.argv[1:6]
    mod = load_module(ml_root, tag)
    report: dict = {"tag": tag, "base": base, "head": head}

    code, rep = mod.run(root, base, head, None, mod.DEFAULT_MIN_RUN, None)
    report["screen_fence_aware"] = {"exit": code, "stats": rep.get("stats"), "fails": [f for f in rep.get("findings", []) if f["severity"] == "FAIL"]}

    # Pre-fence comparison: same hunks, no fence maps.
    pre = []
    for path in sorted(set(mod.changed_files(root, base, head))):
        if not mod.in_docs_scope(path):
            continue
        hunks = mod.parse_hunks(mod.file_diff(root, base, head, path))
        pre.extend(f for f in mod.classify_file(path, hunks, mod.DEFAULT_MIN_RUN, None, None) if f.severity == "FAIL")
    report["screen_pre_fence_fails"] = [{"path": f.path, "reason": f.reason, "detail": f.detail} for f in pre]

    # Which deletion hunks are stamp-only and which delete main CONTENT (each is one small-deletion WARN).
    stamp_re = re.compile(r"^\*\*(Version|Last Updated|Date)(:\*\*|\*\*:)")
    warn_hunks = {"stamp_only": 0, "content": []}
    for path in sorted(set(mod.changed_files(root, base, head))):
        if not mod.in_docs_scope(path):
            continue
        for h in mod.parse_hunks(mod.file_diff(root, base, head, path)):
            if not h.deleted:
                continue
            if all(stamp_re.match(x) for x in h.deleted):
                warn_hunks["stamp_only"] += 1
            else:
                warn_hunks["content"].append({"path": path, "old_start": h.old_start, "deleted": len(h.deleted), "added": len(h.added), "first_deleted": h.deleted[0][:90]})
    report["deletion_hunks"] = warn_hunks

    changed = [p for p in _git(root, "diff", "--name-only", base, head).split() if p.endswith(".md")]
    census = {}
    head_slugs: dict[str, set[str]] = {}
    for path in changed:
        btxt = _git(root, "show", f"{base}:{path}")
        htxt = _git(root, "show", f"{head}:{path}")
        bh = headings(btxt, mod.fenced_lines(btxt))
        hh = headings(htxt, mod.fenced_lines(htxt))
        bset = {(lvl, t) for _, lvl, t in bh}
        hset = {(lvl, t) for _, lvl, t in hh}
        hs, dups = slugs_with_dups(hh)
        head_slugs[path] = hs
        census[path] = {
            "base_headings": len(bh),
            "head_headings": len(hh),
            "removed_or_renamed": sorted(f"{'#' * lvl} {t}" for lvl, t in bset - hset),
            "added": sorted(f"{'#' * lvl} {t}" for lvl, t in hset - bset),
            "duplicate_slugs_at_head": sorted(set(dups)),
        }
    report["heading_census"] = census

    # Anchor check over every tracked .md at HEAD that links into a changed file.
    tracked = [p for p in _git(root, "ls-tree", "-r", "--name-only", head).split("\n") if p.endswith(".md")]
    bad = []
    checked = 0
    for src in tracked:
        try:
            text = _git(root, "show", f"{head}:{src}")
        except subprocess.CalledProcessError:
            continue
        fenced = mod.fenced_lines(text)
        for n, line in enumerate(text.split("\n"), start=1):
            if n in fenced:
                continue
            for m in _LINK_RE.finditer(line):
                target = m.group(1)
                if "://" in target or target.startswith("mailto:") or "#" not in target:
                    continue
                file_part, anchor = target.split("#", 1)
                if file_part:
                    tgt = str(PurePosixPath(src).parent.joinpath(file_part))
                    parts = []
                    for seg in tgt.split("/"):
                        if seg == "..":
                            if parts:
                                parts.pop()
                        elif seg not in (".", ""):
                            parts.append(seg)
                    tgt = "/".join(parts)
                else:
                    tgt = src
                if tgt not in head_slugs:
                    # A link FROM a changed file into an unchanged one: resolve that target too.
                    if src not in changed or not tgt.endswith(".md"):
                        continue
                    try:
                        ttxt = _git(root, "show", f"{head}:{tgt}")
                    except subprocess.CalledProcessError:
                        bad.append({"from": f"{src}:{n}", "target": target, "resolved": tgt, "why": "target file absent at HEAD"})
                        continue
                    head_slugs[tgt], _ = slugs_with_dups(headings(ttxt, mod.fenced_lines(ttxt)))
                checked += 1
                if anchor not in head_slugs[tgt]:
                    bad.append({"from": f"{src}:{n}", "target": target, "resolved": tgt})
    report["anchor_check"] = {"links_into_changed_files_checked": checked, "unresolved": bad}
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
