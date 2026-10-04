"""
Repair the markdown links broken by moving the archived handoff prompts into per-month subdirectories.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-03
Status: ad-hoc — migration
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: branch task/reorg-prompts-directory-subdirs-by-month (9ca80284 moved 222 files from
         prompts/thread-handoff_automated-prompts/ into its HANDOFF_YYYY-MM/ subdirectories);
         the juniper-check-doc-links hook in .pre-commit-config.yaml; .github/workflows/docs-full-check.yml

The move broke links in three shapes:
  inbound         a link in a document that did not move (notes/, reports/, a handoff still at the
                  top level) names the old path of a moved handoff;
  outbound        a link inside a moved handoff was written relative to its old directory, so its
                  ``../../notes/...`` now resolves under ``prompts/``;
  moved-to-moved  a link between two moved handoffs that landed in different month directories.

All three are repaired the same way: resolve the target from where the linking file stood at the
base, map it through the rename table, and re-express it relative to where the linking file stands
now. Links are found as ``juniper-check-doc-links`` (0.1.2) finds them -- fenced blocks skipped,
inline code spans ignored, inline ``[text](target)`` only -- and a link is touched only if it is
broken now.

Every rewrite is guarded: the old target must exist at the base, and the new target must hold the
same blob in the index that the old one held at the base. A rewrite can therefore only re-point a
link at the very document it reached before the move. Anything that fails a guard is reported and
left alone, and the script exits non-zero. A link that was already broken at the base is not this
move's damage: it is listed, never rewritten, and does not fail the run.

Renames are read from the merge-base of ``--base`` and HEAD to the INDEX, so moves made with
``git mv`` but not yet committed are covered too -- re-run this after moving the handoffs that are
still at the top level.

Usage:
    python util/ad-hoc/2026-10-03_fix_reorg_handoff_links.py              # dry run: report only
    python util/ad-hoc/2026-10-03_fix_reorg_handoff_links.py --apply      # write the rewrites
    python util/ad-hoc/2026-10-03_fix_reorg_handoff_links.py --base REF   # default: main
"""

import argparse
import posixpath
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

# Mirrors juniper_doc_tools.check_doc_links so the links examined are the links it validates.
LINK_PATTERN = re.compile(r"\[([^\]]*)\]\(([^)]+)\)")
INLINE_CODE = re.compile(r"`[^`]+`")
FENCE_OPEN = re.compile(r"^(`{3,}|~{3,})")
FENCE_CLOSE = re.compile(r"^(`{3,}|~{3,})\s*$")
EXTERNAL_PREFIXES = ("http://", "https://", "mailto:", "ftp://", "data:", "//")
DOC_EXTENSIONS = (".md", ".markdown", ".rst", ".txt")

# Inline code is masked with a same-length filler (the checker deletes it) so that match offsets
# still index the original line. A target containing the filler crossed a code span.
MASK = "\x00"

KINDS = {(False, True): "inbound", (True, False): "outbound", (True, True): "moved-to-moved"}

# A link that was already broken at the base is not this move's breakage: it is reported, never
# rewritten, and does not fail the run. Both CI lanes exclude the directories these live in.
PREEXISTING = "broken at the base too"


def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def object_id(spec: str) -> str | None:
    result = subprocess.run(["git", "rev-parse", "--verify", "--quiet", spec], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def rename_table(merge_base: str) -> dict[str, str]:
    """Map old path -> new path for every rename from the merge-base to the index."""
    fields = git("diff", "--cached", "-M", "--diff-filter=R", "--name-status", "-z", merge_base).split("\0")
    renames: dict[str, str] = {}
    i = 0
    while i + 2 < len(fields) and fields[i]:
        renames[fields[i + 1]] = fields[i + 2]
        i += 3
    return renames


def inside(path: str) -> bool:
    return path != ".." and not path.startswith("../")


def resolves(repo: Path, src_dir: str, file_part: str) -> bool | None:
    """True/False as the checker judges the link; None when every reading leaves the repository."""
    candidates = [posixpath.normpath(posixpath.join(src_dir, file_part)), posixpath.normpath(file_part)]
    in_bounds = [c for c in candidates if inside(c)]
    if not in_bounds:
        return None
    return any((repo / c).exists() for c in in_bounds)


def repair(file_part: str, src_now: str, src_then: str, renames: dict[str, str], merge_base: str, repo: Path) -> tuple[str | None, str]:
    """Return (new file_part, kind), or (None, why it was not repaired)."""
    then_dir, now_dir = posixpath.dirname(src_then), posixpath.dirname(src_now)
    # The checker accepts a file-relative or a repo-root-relative target; read them in that order,
    # and keep whichever style the link was written in.
    for style, old_target in (("file", posixpath.normpath(posixpath.join(then_dir, file_part))), ("root", posixpath.normpath(file_part))):
        if not inside(old_target):
            continue
        old_id = object_id(f"{merge_base}:{old_target}")
        if old_id is None:
            continue
        new_target = renames.get(old_target, old_target)
        if not (repo / new_target).exists():
            return None, f"target gone: {old_target} -> {new_target}"
        if not (repo / new_target).is_dir() and object_id(f":{new_target}") != old_id:
            return None, f"content differs between {merge_base[:8]}:{old_target} and :{new_target}"
        kind = KINDS.get((src_now != src_then, old_target in renames), "unmoved")
        new_part = posixpath.relpath(new_target, now_dir or ".") if style == "file" else new_target
        return new_part, kind
    return None, PREEXISTING


def process(path: str, text: str, renames: dict[str, str], back: dict[str, str], merge_base: str, repo: Path, stats: Counter, problems: list[str], preexisting: list[str]) -> str:
    src_then = back.get(path, path)
    lines = text.split("\n")
    fence: str | None = None
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if fence is None:
            opened = FENCE_OPEN.match(stripped)
            if opened:
                fence = opened.group(1)
                continue
        else:
            closed = FENCE_CLOSE.match(stripped)
            if closed and closed.group(1)[0] == fence[0] and len(closed.group(1)) >= len(fence):
                fence = None
            continue

        masked = INLINE_CODE.sub(lambda m: MASK * len(m.group(0)), line)
        edits: list[tuple[int, int, str]] = []
        for match in LINK_PATTERN.finditer(masked):
            raw = match.group(2)
            target = raw.strip()
            if target.startswith(EXTERNAL_PREFIXES):
                continue
            file_part, sep, anchor = target.partition("#")
            if not file_part:
                continue
            verdict = resolves(repo, posixpath.dirname(path), file_part)
            if verdict is None:
                if path != src_then:
                    problems.append(f"{path}:{idx + 1}: link leaves the repository from a moved file (not handled): {target}")
                continue
            if verdict:
                continue
            if MASK in target:
                problems.append(f"{path}:{idx + 1}: broken link crosses an inline code span: {line.strip()[:120]}")
                continue
            new_part, kind = repair(file_part, path, src_then, renames, merge_base, repo)
            if new_part is None:
                (preexisting if kind == PREEXISTING else problems).append(f"{path}:{idx + 1}: broken link not repaired ({kind}): {target}")
                continue
            lead = raw[: len(raw) - len(raw.lstrip())]
            trail = raw[len(raw.rstrip()) :]
            edits.append((match.start(2), match.end(2), f"{lead}{new_part}{sep}{anchor}{trail}"))
            stats[kind] += 1
            print(f"  {path}:{idx + 1}: [{kind}] {target}\n      -> {new_part}{sep}{anchor}")
        for start, end, replacement in reversed(edits):
            line = line[:start] + replacement + line[end:]
        lines[idx] = line
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    parser.add_argument("--base", default="main", help="ref the move is measured against (default: main)")
    parser.add_argument("--apply", action="store_true", help="write the rewrites (default: dry run)")
    args = parser.parse_args()

    repo = Path(git("rev-parse", "--show-toplevel").strip())
    merge_base = git("merge-base", args.base, "HEAD").strip()
    renames = rename_table(merge_base)
    back = {new: old for old, new in renames.items()}
    print(f"merge-base {merge_base[:8]}; {len(renames)} renamed path(s) between it and the index\n")

    stats: Counter = Counter()
    problems: list[str] = []
    preexisting: list[str] = []
    changed: list[str] = []
    for path in git("ls-files", "-z").split("\0"):
        # A symlinked document is validated (by the checker) and rewritten (here) as its real file:
        # its links resolve from the real file's directory, and writing through the link would
        # rewrite that file a second time.
        if not path.endswith(DOC_EXTENSIONS) or (repo / path).is_symlink() or not (repo / path).is_file():
            continue
        try:
            # newline="" keeps CRLF files byte-identical outside the rewritten targets.
            with open(repo / path, encoding="utf-8", newline="") as handle:
                original = handle.read()
        except UnicodeDecodeError:
            problems.append(f"{path}: not UTF-8, not scanned")
            continue
        updated = process(path, original, renames, back, merge_base, repo, stats, problems, preexisting)
        if updated != original:
            changed.append(path)
            if args.apply:
                with open(repo / path, "w", encoding="utf-8", newline="") as handle:
                    handle.write(updated)

    verb = "rewritten" if args.apply else "to rewrite (dry run; --apply writes them)"
    print(f"\n{sum(stats.values())} link(s) {verb} in {len(changed)} file(s): " + ", ".join(f"{k}={v}" for k, v in sorted(stats.items())))
    if preexisting:
        by_file = Counter(entry.split(":", 1)[0] for entry in preexisting)
        print(f"\n{len(preexisting)} link(s) already broken at the base, left alone:")
        for name, count in sorted(by_file.items()):
            print(f"  {count:4d}  {name}")
    if problems:
        print(f"\n{len(problems)} problem(s) -- resolve by hand:")
        for problem in problems:
            print(f"  {problem}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
