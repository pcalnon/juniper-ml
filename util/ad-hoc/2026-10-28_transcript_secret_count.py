#!/usr/bin/env python3
"""
Count, by VALUE, where the backup arc's secrets persist in Claude Code's own files -- prints labels, paths and
counts only, never a value.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-28
Status: ad-hoc -- one-off (backup arc, Phase C item 7's transcript row; owner ruling 2026-10-28: build it now, the
        owner runs it before Phase D step 9)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md §6 (the transcript row,
         the instruments row) and notes sink-a, sink-c;
         notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md §6.3.1, §6.6

WHAT IT ANSWERS
    D note sink-c: a transcript is counted "by value, never by label -- this arc's own prose quotes every label --
    and never with a value on argv". So the values are read here from the credential files, by PATH, and searched
    for in every regular file under:
      * <home>/.claude -- the .jsonl transcripts AND the separately persisted <session>/tool-results/ files (note
        sink-a: a purge that walks only the transcripts misses them), and the rest of that tree;
      * <home>/.claude.json;
      * <home>/Development/python/Juniper/juniper-ml/tmp, where CLAUDE_CODE_TMPDIR has put scratchpads and task
        output since 2026-10-26. Scope (the counting-scripts ruling of 2026-10-26): that repository's tmp/ ALONE,
        deliberately, because it is where Claude Code writes; the rest of the repository is not searched.
    Add roots with --root. Phase D step 9 shreds the service .env, the only holder of the 64-character settings key
    and its commented secrets: run this BEFORE step 9, or the count can cover only the credential file's values.

WHO RUNS IT
    The OWNER, never a session: it reads secret files (the recovery plan's §6.0 item 6). The service .env is
    0640 duplicati:duplicati, so run it as root, with --home given explicitly (a root shell's own home is /root,
    and a scan of the wrong tree would read as a clean zero -- which is why <home>/.claude must exist). In a root
    shell, bash's ~user expansion names each home without $HOME:
        python3 util/ad-hoc/2026-10-28_transcript_secret_count.py --home ~pcalnon \\
            --env-file ~duplicati/.config/Duplicati/.env --env-file ~pcalnon/.config/duplicati-backup/env
    Only paths ever reach argv.

WHAT IS COUNTED
    Every NAME=value line of each --env-file, commented-out ones included ("# NAME=value": the service .env keeps
    retired secrets in comments). One pair of matching outer quotes is stripped; a double-quoted value is also tried
    with its \\" and \\\\ escapes undone, and an unquoted one also without a trailing " # comment". Values shorter
    than --min-length (default 16) are listed by label as skipped: a short value is a flag or a port, and matches
    everywhere. A value found under several labels is counted once and printed under all of them -- which says that
    those labels hold equal values, and nothing more. Each value is searched for as written and in its one- and
    two-level JSON-escaped forms (the transcripts are JSON; a tool result that was itself JSON is escaped twice),
    case-sensitively. NOT found: a UTF-16LE, base64 or URL-encoded copy, or a value split across lines.

WHAT IT WRITES
    Nothing. Stdout only: labels, file paths, counts, and each root's file and byte totals, so that a scan of the
    wrong tree shows as a small number rather than as a clean zero. No value, hash or fingerprint of a value is
    printed. The credential files themselves are never counted, even when a root contains them.

EXIT
    0 scanned, no value found; 1 scanned, at least one value found (the per-file lines say where); 2 a usage or read
    error: an unreadable --env-file, no countable value, a missing <home>/.claude or --root.
"""

import argparse
import json
import mmap
import os
import re
import sys
from pathlib import Path

ASSIGN_RE = re.compile(rb"^\s*(#\s*)?(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$")
INLINE_COMMENT_RE = re.compile(rb"\s+#.*$")


def candidates(raw: bytes) -> list[bytes]:
    """The forms one NAME=value line's value may take in use: quotes stripped (and escapes undone), or as written
    and without a trailing comment."""
    if len(raw) >= 2 and raw[:1] == raw[-1:] and raw[:1] in (b"'", b'"'):
        inner = raw[1:-1]
        found = [inner]
        if raw[:1] == b'"':
            found.append(inner.replace(b'\\"', b'"').replace(b"\\\\", b"\\"))
    else:
        found = [raw, INLINE_COMMENT_RE.sub(b"", raw)]
    return list(dict.fromkeys(found))


def entry_patterns(forms: list[bytes]) -> list[bytes]:
    """Every search form of one entry, minus any form that CONTAINS another: each occurrence of the longer form is
    already an occurrence of the shorter one, and counting both would count it twice."""
    patterns = list(dict.fromkeys(p for f in forms for p in search_forms(f)))
    return [p for p in patterns if not any(q != p and q in p for q in patterns)]


def search_forms(value: bytes) -> list[bytes]:
    """The value as written, plus its JSON-escaped forms, one and two levels deep."""
    forms = [value]
    try:
        text = value.decode("utf-8")
    except UnicodeDecodeError:
        return forms
    once = json.dumps(text, ensure_ascii=False)[1:-1]
    forms.append(once.encode("utf-8"))
    forms.append(json.dumps(text)[1:-1].encode("ascii"))
    forms.append(json.dumps(once, ensure_ascii=False)[1:-1].encode("utf-8"))
    return list(dict.fromkeys(forms))


def read_values(paths: list[str], min_length: int) -> tuple[dict[tuple[bytes, ...], list[str]], list[str]]:
    """Map each countable value (the tuple of its candidate forms) to its labels; return the report lines too."""
    entries: dict[tuple[bytes, ...], list[str]] = {}
    report = []
    for index, path in enumerate(paths, 1):
        try:
            data = Path(path).read_bytes()
        except OSError as exc:
            raise SystemExit(f"cannot read --env-file {path}: {exc.strerror}") from exc
        counted = skipped = 0
        skipped_labels = []
        for line in data.splitlines():
            m = ASSIGN_RE.match(line)
            if not m:
                continue
            label = f"{'#' if m.group(1) else ''}{m.group(2).decode('ascii')} (env-file {index})"
            forms = tuple(sorted(c for c in candidates(m.group(3)) if len(c) >= min_length))
            if not forms:
                skipped += 1
                skipped_labels.append(label)
                continue
            counted += 1
            labels = entries.setdefault(forms, [])
            if label not in labels:
                labels.append(label)
        summary = f"  env-file {index}: {path} -- {counted} counted, {skipped} skipped (shorter than {min_length})"
        report.append(summary + (f": {', '.join(skipped_labels)}" if skipped_labels else ""))
    return entries, report


def count_in_file(path: str, patterns: list[tuple[bytes, int]]) -> dict[int, int]:
    """Occurrences of each pattern in one file, keyed by the value index it belongs to."""
    hits: dict[int, int] = {}
    with open(path, "rb") as fh:
        with mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            for pattern, value_index in patterns:
                pos = mm.find(pattern)
                while pos != -1:
                    hits[value_index] = hits.get(value_index, 0) + 1
                    pos = mm.find(pattern, pos + len(pattern))
    return hits


def main() -> int:
    ap = argparse.ArgumentParser(description="Count, by value, where the backup arc's secrets persist (counts only).")
    ap.add_argument("--home", required=True, help="the home whose .claude tree is searched, e.g. ~pcalnon in a root shell")
    ap.add_argument("--env-file", action="append", required=True, help="a credential file to read values from (repeat)")
    ap.add_argument("--root", action="append", default=[], help="an extra directory or file to search (repeat)")
    ap.add_argument("--min-length", type=int, default=16, help="skip values shorter than this (default 16)")
    args = ap.parse_args()

    home = Path(args.home)
    if not (home / ".claude").is_dir():
        print(f"usage error: {home / '.claude'} is not a directory -- wrong --home?", file=sys.stderr)
        return 2
    try:
        values, report = read_values(args.env_file, args.min_length)
    except SystemExit as exc:
        print(exc, file=sys.stderr)
        return 2
    if not values:
        print("no countable value in any --env-file", file=sys.stderr)
        return 2

    ordered = list(values.items())
    labels = [" / ".join(lbls) for _, lbls in ordered]
    patterns = [(p, i) for i, (forms, _) in enumerate(ordered) for p in entry_patterns(list(forms))]
    skip = {os.path.realpath(p) for p in args.env_file}

    roots = [(home / ".claude", True), (home / ".claude.json", False),
             (home / "Development/python/Juniper/juniper-ml/tmp", False)]
    roots += [(Path(r), True) for r in args.root]

    print("credential files:")
    print("\n".join(report))
    print(f"values counted: {len(ordered)} distinct, {len(patterns)} search forms")
    print("roots:")
    per_file: list[tuple[str, dict[int, int]]] = []
    unreadable = 0
    for root, required in roots:
        if not root.exists():
            if required:
                print(f"usage error: --root {root} does not exist", file=sys.stderr)
                return 2
            print(f"  {root}: absent, skipped")
            continue
        files = nbytes = 0
        if root.is_file():
            walk = [(str(root.parent), [], [root.name])]
        else:
            walk = os.walk(root, followlinks=False)
        for dirpath, _, filenames in walk:
            for name in filenames:
                path = os.path.join(dirpath, name)
                if os.path.islink(path) or not os.path.isfile(path) or os.path.realpath(path) in skip:
                    continue
                try:
                    size = os.path.getsize(path)
                    files += 1
                    nbytes += size
                    if size:
                        hits = count_in_file(path, patterns)
                        if hits:
                            per_file.append((path, hits))
                except (OSError, ValueError):
                    unreadable += 1
        print(f"  {root}: {files} files, {nbytes} bytes")
    if unreadable:
        print(f"  unreadable files (not counted): {unreadable}")

    totals = [[0, 0] for _ in ordered]
    if per_file:
        print("hits (file: label=count):")
        for path, hits in per_file:
            print(f"  {path}: " + ", ".join(f"{labels[i]}={n}" for i, n in sorted(hits.items())))
            for i, n in hits.items():
                totals[i][0] += n
                totals[i][1] += 1
    print("totals:")
    for i, (n, nfiles) in enumerate(totals):
        print(f"  {labels[i]}: {n} occurrence(s) in {nfiles} file(s)")
    print(f"RESULT: {len(per_file)} file(s) hold at least one counted value")
    return 1 if per_file else 0


if __name__ == "__main__":
    raise SystemExit(main())
