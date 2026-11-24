#!/usr/bin/env python3
"""
List every "owner" token juniper-ml#2606 renamed to "Overtoad", and flag the ones whose context says TECHNICAL.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — investigation (the technical-owner sweep that follows juniper-ml#2606)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2606; util/ad-hoc/2026-11-23_overtoad_rename_repair.py (``classify``, whose blind spots
    this sweep closes); util/ad-hoc/2026-11-24_technical_owner_restore.py (applies the reviewed list)

Why this exists
---------------
#2606 renamed "owner" to "Overtoad" wherever ``classify`` judged the word to mean the person. ``classify``
reads one word on each side of the token, so it misses a technical owner that is named by a possessive
("the env file's owner": the word before is "s"), an attribute list ("mode, owner", "mode and owner"), a
verb ("change owner") or a header ("Owner:group"). The 2026-11-24 list from the previous session
(``tmp/rename-repair-s2/unix_owner_candidates.py`` in worktree crispy-forging-falcon) also skipped the 363
files #2606 ADDED, because they have no base version.

What it does
------------
For every file #2606 changed (``--base`` .. ``--head``) it pairs each base line with its head line and lists
every token whose base text is "owner"/"Owner" and whose head text is "Overtoad"/"The Overtoad":

- a modified file: the base line is the file at ``--base``. Lines pair one to one; when the counts differ,
  equal-length changed blocks pair line by line and the rest is reported as UNALIGNED.
- an added file: there is no base, so the base line is the head line with the two-step inverse applied
  ("The Overtoad" -> "Owner", then "Overtoad" -> "owner"), which is how #2606's rebuild reconstructed it.
  The arc's own tools (``ARC_TOOLS``) are skipped: they were written after the rename and use the word
  "Overtoad" deliberately, in code.

Each row also names where the token sits (``kind``): PROSE, COMMENT, DOCSTRING, STRING (a Python string that
is not a docstring), CODE, MD-FENCE (a fenced markdown block), MD-INLINE (a markdown code span) or OTHER. A
token in code or a code string is where a technical owner breaks behaviour, not only wording.

Each row is flagged by three independent nets, and every flag is a CANDIDATE for review, not a verdict:

- ``U``: Unix ownership vocabulary within ``WINDOW`` characters (mode, chown, uid, group, umask, stat, an
  octal mode, a file/directory/volume noun ...);
- ``T``: other technical vocabulary (a lock, slot, process, thread, socket, repository, token, field ...);
- ``P``: the shapes ``classify`` cannot see (a possessive before the token, an attribute list, a verb that
  acts on an owner, "owner:group").

Usage
-----
    python3 util/ad-hoc/2026-11-24_technical_owner_candidates.py --repo . --base 515e16a0 --head 5a049144 --out tmp/x/all.tsv
"""

from __future__ import annotations

import argparse
import ast
import difflib
import io
import re
import subprocess
import sys
import tokenize

SEP = re.compile(r"(Owner|owner)")
WINDOW = 70
ARC_TOOLS = {
    "util/ad-hoc/2026-11-23_deploy_281_technical_restore.py",
    "util/ad-hoc/2026-11-23_overtoad_rename_repair.py",
    "util/ad-hoc/2026-11-23_pr2606_rebuild.py",
    "util/ad-hoc/2026-11-23_pr2606_upload.py",
    "util/ad-hoc/2026-11-23_recurrence_237_symlink_restore.py",
    "util/ad-hoc/2026-11-23_rename_pr_damage_audit.py",
    "util/ad-hoc/2026-11-23_run_ci_regression_suites.py",
    "util/ad-hoc/2026-11-23_symlink_regressions.py",
    "util/ad-hoc/2026-11-23_transcript_file_original.py",
}
NET_U = re.compile(
    r"\bmodes?\b|chmod|chown|chgrp|\buid\b|\bgid\b|\bgroups?\b|\bperms?\b|permissions?|umask|\bstat\b|\b0[0-7]{3,4}\b|"
    r"-rw[-x]|\broot:root\b|setgid|setuid|\bsticky\b|\bACLs?\b|\binode\b|:group|group:|"
    r"\b(?:file|files|dir|directory|directories|folder|volume|volumes|copy|path|socket|env|unit|archive|keyfile|"
    r"spool|backup|database|db|mount|tmpfs)(?:'s)?\b",
    re.I,
)
NET_T = re.compile(
    r"\b(?:locks?|slots?|process(?:es)?|pids?|threads?|listener|lease|mutex|semaphore|fd|repos?|repository|branch|"
    r"tags?|images?|packages?|tokens?|secrets?|jobs?|tasks?|workers?|queues?|rows?|records?|fields?|columns?|"
    r"attributes?|callbacks?|components?|props?|outputs?|stores?|CODEOWNERS|org|organization|account|login|"
    r"endpoint|ports?|daemon|container|tty|pty|cgroup|systemd|key)\b",
    re.I,
)
ATTR = r"(?:mode|modes|group|groups|perm|perms|permissions?|type|size|path|uid|gid|mtime|ctime|inode|content|contents|name|links?)"
NET_P = (
    ("possessive", re.compile(r"[A-Za-z]'s\s+$")),
    ("list-before", re.compile(ATTR + r"\s*(?:,|and|or|/|&|\+)\s*$", re.I)),
    ("verb-before", re.compile(r"\b(?:change[sd]?|changing|set|sets|setting|preserve[sd]?|preserving|keeps?|kept|resets?|restore[sd]?|"
                               r"match(?:es|ed)?|wrong|correct|expected|actual|numeric|chown(?:s|ed)?)\s+(?:the\s+|its\s+|their\s+)?$", re.I)),
)
NET_P_AFTER = (
    ("list-after", re.compile(r"^\s*(?:,|and|or|/|&|\+|:)\s*" + ATTR + r"\b", re.I)),
)


def git(repo: str, *args: str) -> str:
    proc = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"git {' '.join(args[:3])} failed: {proc.stderr.strip()[:300]}")
    return proc.stdout


def invert(text: str) -> str:
    return text.replace("The Overtoad", "Owner").replace("Overtoad", "owner")


def renamed(base_line: str, head_line: str) -> list[tuple[int, int, int, str, str, int]] | None:
    """Every renamed token of BASE_LINE as (occurrence, start, end, base token, head token, head column); None if
    the lines differ beyond the rename."""
    pieces = SEP.split(base_line)
    if len(pieces) == 1:
        return None
    pattern = "".join(re.escape(p) if k % 2 == 0 else "(Owner|owner|The Overtoad|Overtoad)" for k, p in enumerate(pieces))
    match = re.fullmatch(pattern, head_line)
    if not match:
        return None
    out, pos, head_pos = [], len(pieces[0]), len(pieces[0])
    for k in range(1, len(pieces), 2):
        orig, got = pieces[k], match.group((k + 1) // 2)
        start, end = pos, pos + len(orig)
        if got != orig:
            out.append(((k + 1) // 2, start, end, orig, got, head_pos))
        pos = end + len(pieces[k + 1])
        head_pos += len(got) + len(pieces[k + 1])
    return out


def nets(line: str, start: int, end: int) -> list[str]:
    window = line[max(0, start - WINDOW) : end + WINDOW]
    flags = []
    if NET_U.search(window):
        flags.append("U")
    if NET_T.search(window):
        flags.append("T")
    before, after = line[:start], line[end:]
    for name, pattern in NET_P:
        if pattern.search(before):
            flags.append("P:" + name)
    for name, pattern in NET_P_AFTER:
        if pattern.search(after):
            flags.append("P:" + name)
    return flags


CODE_SUFFIXES = (".py", ".bash", ".sh", ".yml", ".yaml", ".js", ".ts", ".json", ".toml", ".cfg", ".ini", ".conf")


def python_kinds(text: str) -> dict[int, list[tuple[int, int, str]]]:
    """Per line, the (start column, end column, kind) of every comment and string token; kind is COMMENT,
    DOCSTRING or STRING. A multi-line token is split into its lines."""
    spans: dict[int, list[tuple[int, int, str]]] = {}
    docstring_lines: set[int] = set()
    try:
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                    docstring_lines.update(range(first.lineno, (first.end_lineno or first.lineno) + 1))
    except SyntaxError:
        docstring_lines = set()  # not parseable as a whole (a fragment): no string is taken for a docstring
    string_types = {tokenize.STRING} | {getattr(tokenize, n) for n in ("FSTRING_START", "FSTRING_MIDDLE", "FSTRING_END") if hasattr(tokenize, n)}
    try:
        for tok in tokenize.generate_tokens(io.StringIO(text).readline):
            if tok.type == tokenize.COMMENT:
                kind = "COMMENT"
            elif tok.type in string_types:
                kind = "DOCSTRING" if tok.start[0] in docstring_lines else "STRING"
            else:
                continue
            (r1, c1), (r2, c2) = tok.start, tok.end
            for row in range(r1, r2 + 1):
                spans.setdefault(row, []).append((c1 if row == r1 else 0, c2 if row == r2 else 10**9, kind))
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return spans  # not tokenizable to the end: keep the spans read before the error; a later token reads as CODE
    return spans


def kind_of(path: str, lines: list[str], spans: dict[int, list[tuple[int, int, str]]] | None, fences: set[int], number: int, column: int) -> str:
    line = lines[number - 1]
    if path.endswith(".md") or path.endswith(".md.in"):
        if number in fences:
            return "MD-FENCE"
        ticks = [m.start() for m in re.finditer(r"`+", line)]
        inside = sum(1 for t in ticks if t < column) % 2 == 1
        return "MD-INLINE" if inside else "PROSE"
    if path.endswith(".py"):
        for c1, c2, kind in (spans or {}).get(number, []):
            if c1 <= column < c2:
                return kind
        return "CODE"
    if path.endswith(CODE_SUFFIXES) or line.startswith("#!"):
        hash_at = line.find("#")
        return "COMMENT" if 0 <= hash_at <= column and not line[:hash_at].count('"') % 2 and not line[:hash_at].count("'") % 2 else "CODE"
    return "OTHER"


def fenced_lines(lines: list[str]) -> set[int]:
    inside, out = False, set()
    for number, line in enumerate(lines, 1):
        if re.match(r"^\s*(```|~~~)", line):
            inside = not inside
            continue
        if inside:
            out.add(number)
    return out


def pairs(base_lines: list[str], head_lines: list[str]):
    if len(base_lines) == len(head_lines):
        yield from ((n, b, h) for n, (b, h) in enumerate(zip(base_lines, head_lines), 1))
        return
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, base_lines, head_lines, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace" and i2 - i1 == j2 - j1:
            for off in range(i2 - i1):
                yield j1 + off + 1, base_lines[i1 + off], head_lines[j1 + off]
        else:
            yield j1 + 1, None, f"UNALIGNED {tag} base {i1 + 1}-{i2} head {j1 + 1}-{j2}"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("--repo", required=True)
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    rows, notes = [], []
    for row in git(args.repo, "diff", "--name-status", "--no-renames", args.base, args.head).splitlines():
        status, path = row.split("\t", 1)
        if status not in ("M", "A") or path in ARC_TOOLS:
            notes.append(f"SKIP\t{status}\t{path}")
            continue
        try:
            head_text = git(args.repo, "show", f"{args.head}:{path}")
            base_text = git(args.repo, "show", f"{args.base}:{path}") if status == "M" else invert(head_text)
        except UnicodeDecodeError:
            notes.append(f"SKIP-BINARY\t{status}\t{path}")
            continue
        head_lines = head_text.split("\n")
        spans = python_kinds(head_text) if path.endswith(".py") else None
        fences = fenced_lines(head_lines) if path.endswith((".md", ".md.in")) else set()
        for number, base_line, head_line in pairs(base_text.split("\n"), head_lines):
            if base_line is None:
                notes.append(f"UNALIGNED\t{path}:{number}\t{head_line}")
                continue
            if base_line == head_line or "Overtoad" not in head_line:
                continue
            tokens = renamed(base_line, head_line)
            if tokens is None:
                notes.append(f"BEYOND\t{path}:{number}\t{base_line[:100]!r}")
                continue
            for occurrence, start, end, orig, got, head_col in tokens:
                kind = kind_of(path, head_lines, spans, fences, number, head_col)
                lo, hi = max(0, start - WINDOW), end + WINDOW
                shown = base_line[lo:start] + "[[" + orig + "]]" + base_line[end:hi]
                rows.append("\t".join((status, f"{path}:{number}", str(occurrence), orig, got, ",".join(nets(base_line, start, end)) or "-", kind, shown.replace("\t", " ").strip())))
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(rows) + ("\n" if rows else ""))
    with open(args.out + ".notes", "w", encoding="utf-8") as handle:
        handle.write("\n".join(notes) + ("\n" if notes else ""))
    flagged = sum(1 for r in rows if r.split("\t")[5] != "-")
    kinds: dict[str, int] = {}
    for r in rows:
        kinds[r.split("\t")[6]] = kinds.get(r.split("\t")[6], 0) + 1
    print(f"{len(rows)} renamed token(s) in {len({r.split(chr(9))[1].rsplit(':', 1)[0] for r in rows})} file(s); {flagged} flagged by a net -> {args.out}")
    print("by position: " + " ".join(f"{k}={v}" for k, v in sorted(kinds.items())))
    print(f"{len(notes)} note(s) -> {args.out}.notes")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
