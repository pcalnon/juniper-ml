#!/usr/bin/env python3
"""
Count how many real Bash commands the fail-closed brace cap would refuse, from recent Claude Code transcripts.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — investigation (flood-4 round-2 ml-code carrier; evidence for an open question)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: owner ruling "Fail closed" (2026-11-08) on util/claude_agent_guard.py's MAX_BRACE_ALTERNATIVES.

Usage: python3 -I 2026-11-08_flood4r2_ml_code_brace_refusal_census.py <guard.py> <transcripts dir> <max files> <out file>

Reads the newest <max files> *.jsonl transcripts under <transcripts dir>, takes every Bash tool_use
command, and runs the given guard's BashAnalyzer on it against a throwaway home. It prints and writes
AGGREGATES ONLY: totals, refusal counts by category and by the command's first word. No command text,
no evidence string and no transcript content is ever printed or written.
"""
import collections
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

RANGE_RE = re.compile(r"\{-?\d+\.\.-?\d+\}|\{[A-Za-z]\.\.[A-Za-z]\}")


def load(path: Path):
    spec = importlib.util.spec_from_file_location("guard_under_census", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def offender_kind(guard, command: str) -> str:
    """Which top-level word overflows, by kind only: bash brace-expands an unquoted word, never quoted text."""
    try:
        lexer = guard.Lexer(command).run()
    except Exception:
        return "unlexable"
    for seg in lexer.segments:
        for word in seg.words:
            try:
                guard.brace_expand(word.text)
            except guard.MalformedInput:
                return "a top-level word with quoting" if word.quoted else "a top-level UNQUOTED word (bash expands it too)"
    return "nested text (bash -c, $( ), eval or an interpreter's string literal)"


def commands(path: Path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                row = json.loads(line)
            except ValueError:
                continue
            message = row.get("message") if isinstance(row, dict) else None
            content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(content, list):
                continue
            for part in content:
                if isinstance(part, dict) and part.get("type") == "tool_use" and part.get("name") == "Bash":
                    command = (part.get("input") or {}).get("command")
                    if isinstance(command, str):
                        yield command


def main(argv: list) -> int:
    guard = load(Path(argv[1]))
    root = Path(argv[2]).expanduser()
    limit = int(argv[3])
    out = Path(argv[4])
    files = sorted(root.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    total = refused = other_malformed = 0
    categories = collections.Counter()
    heads = collections.Counter()
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        for name in (".ssh", ".gnupg", ".claude"):
            (home / name).mkdir(parents=True)
        ctx = guard.Context([str(home)], tmp)
        for path in files:
            for command in commands(path):
                total += 1
                try:
                    guard.BashAnalyzer(ctx).analyze(command)
                except guard.MalformedInput as exc:
                    if "MAX_BRACE_ALTERNATIVES" not in str(exc):
                        other_malformed += 1
                        continue
                    refused += 1
                    if RANGE_RE.search(command):
                        categories["contains a {lo..hi} range"] += 1
                    categories[offender_kind(guard, command)] += 1
                    head = command.strip().split(None, 1)[0] if command.strip() else ""
                    heads[re.sub(r"[^A-Za-z0-9_.-]", "", head)[:20] or "?"] += 1
                except Exception:  # a guard bug must not stop the census; counted separately
                    other_malformed += 1
    lines = [
        "transcripts read: %d (newest first, under %s)" % (len(files), root),
        "Bash commands: %d" % total,
        "refused by the brace cap: %d (%.3f%%)" % (refused, 100.0 * refused / total if total else 0.0),
        "other analysis refusals or errors (not the brace cap): %d" % other_malformed,
        "by category: %s" % dict(categories.most_common()),
        "by first word: %s" % dict(heads.most_common(15)),
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
