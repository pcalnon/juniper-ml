#!/usr/bin/env python3
"""
Count the real Bash commands two guard versions refuse, by reason, from the same recent Claude Code transcripts.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation (flood-4 round-2 ml-code carrier: the cost of the brace-sequence refusals)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: 2026-11-08_flood4r2_ml_code_brace_refusal_census.py (the builder's census, adapted here: it lumped
         every refusal that is not the cap together, and read whatever files were newest at the time).

Usage: python3 -I 2026-11-08_flood4r2_ml_code_r2_refusal_census.py <transcripts dir> <max files> <out file> <guard.py> [<guard.py> ...]

Reads the newest <max files> *.jsonl transcripts under <transcripts dir> ONCE, then runs each guard's
BashAnalyzer over every Bash tool_use command against a throwaway home. AGGREGATES ONLY are printed and
written: totals, and refusals counted by the guard's own reason (the text of its MalformedInput up to the first
": ", where the evidence would begin), by exception class for anything that is not a MalformedInput (a guard
bug), by whether the word that fails is quoted (bash never brace-expands quoted text, so such a refusal is a
false one), and by the command's first word with everything but [A-Za-z0-9_.-] removed. With two guards or
more it also counts the commands whose outcome (passes, the set of rule ids denied, or refused) differs
between the first guard and the last, by the pair of outcomes. No command text, no evidence string and no
transcript content is printed or written.
"""

import collections
import importlib.machinery
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path


def load(path: str, index: int):
    loader = importlib.machinery.SourceFileLoader("guard_under_census_%d" % index, path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


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


def failing_word_kind(guard, command: str) -> str:
    """Whether the top-level word that brace_expand refuses is quoted; nested text when no top-level word fails."""
    try:
        lexer = guard.Lexer(command).run()
    except Exception:
        return "unlexable"
    for seg in lexer.segments:
        for word in seg.words:
            try:
                guard.brace_expand(word.text)
            except guard.MalformedInput:
                return "a top-level word with quoting" if word.quoted else "a top-level UNQUOTED word"
            except Exception:
                return "a top-level word that crashes brace_expand"
    return "nested text (bash -c, $( ), eval or an interpreter's string literal)"


def census(guard, every: list) -> dict:
    reasons = collections.Counter()
    kinds = collections.Counter()
    heads = collections.Counter()
    outcomes = []  # per command: "ok", or the sorted rule ids it denies, or "refused: <reason>"
    refused = 0
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        for name in (".ssh", ".gnupg", ".claude"):
            (home / name).mkdir(parents=True)
        ctx = guard.Context([str(home)], tmp)
        for command in every:
            try:
                hits = guard.BashAnalyzer(ctx).analyze(command)
                outcomes.append(" ".join(sorted({hit.rule_id for hit in hits})) or "ok")
                continue
            except guard.MalformedInput as exc:
                reason = str(exc).split(": ", 1)[0][:110]
            except Exception as exc:  # a guard bug must not stop the census; counted by class only
                reason = "NOT a MalformedInput: " + exc.__class__.__name__
            outcomes.append("refused: " + reason[:40])
            refused += 1
            reasons[reason] += 1
            kinds[(reason[:40], failing_word_kind(guard, command))] += 1
            head = command.strip().split(None, 1)[0] if command.strip() else ""
            heads[re.sub(r"[^A-Za-z0-9_.-]", "", head)[:20] or "?"] += 1
    return {"refused": refused, "by reason": dict(reasons.most_common()), "by reason and failing word": {"%s | %s" % k: v for k, v in kinds.most_common()}, "by first word": dict(heads.most_common(15)), "outcomes": outcomes}


def main(argv: list) -> int:
    root = Path(argv[1]).expanduser()
    limit = int(argv[2])
    out = Path(argv[3])
    files = sorted(root.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[:limit]
    every = [command for path in files for command in commands(path)]
    lines = ["transcripts read: %d (newest first, under %s)" % (len(files), root), "Bash commands: %d" % len(every)]
    results = []
    for index, guard_path in enumerate(argv[4:]):
        guard = load(guard_path, index)
        result = census(guard, every)
        results.append(result)
        lines.append("guard %s (%s): refused %d (%.3f%%)" % (guard_path, getattr(guard, "__version__", "?"), result["refused"], 100.0 * result["refused"] / len(every) if every else 0.0))
        for key in ("by reason", "by reason and failing word", "by first word"):
            lines.append("  %s: %s" % (key, json.dumps(result[key], sort_keys=False)))
    if len(results) >= 2:
        # The first guard against the last: how many commands changed outcome, by (before -> after) outcome.
        changes = collections.Counter("%s -> %s" % (a, b) for a, b in zip(results[0]["outcomes"], results[-1]["outcomes"]) if a != b)
        lines.append("outcome changes, first guard -> last guard: %d commands; %s" % (sum(changes.values()), json.dumps(dict(changes.most_common()), sort_keys=False)))
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
