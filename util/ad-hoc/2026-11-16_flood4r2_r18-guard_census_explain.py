#!/usr/bin/env python3
"""
Explain, by shape only, every real command a newer agent guard denies or refuses that an older one passes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (Cursor flood-4 disposition arc, session 9: the guard's word-structure hardening)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_census.py (whose transcript reader this keeps);
         util/claude_agent_guard.py 1.4.0 (its two readings, BashAnalyzer._mode "A" and "B").

Usage:
    python3 -I util/ad-hoc/2026-11-16_flood4r2_r18-guard_census_explain.py <transcripts dir> <max files> <out.json>
        <older guard.py> <newer guard.py>

Reads the newest <max files> *.jsonl transcripts once and runs every Bash tool_use command through both guards'
``BashAnalyzer`` against a throwaway home. For each command the newer guard denies or refuses while the older one
passes it, it records AGGREGATES and SHAPES only, never command text: the rule, which reading of the newer guard
made the hit ("A" main's, "B" bash's), the SHAPE of the evidence (each letter as ``a``, each digit as ``9``, other
characters kept, 40 at most), whether the command's raw text holds ``.ssh`` or ``.gnupg`` (any case), and the
SHAPE of every top-level word whose two readings differ.
"""

from __future__ import annotations

import collections
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path


def load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
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


def shape(text: str) -> str:
    return re.sub(r"[0-9]", "9", re.sub(r"[A-Za-z]", "a", text))[:40]


def outcome(guard, ctx, command: str, record=None):
    analyzer = guard.BashAnalyzer(ctx)
    if record is not None:
        original = analyzer.hit
        original_path = analyzer._path_word
        original_scan = analyzer._scan
        current = {"word": None, "depth": 0, "text": "", "bases": []}

        def path_word(word, bases, mutating) -> None:
            current["word"] = word
            current["bases"] = bases
            original_path(word, bases, mutating)
            current["word"] = None

        def scan(text: str, depth: int, bases: list) -> None:
            saved = (current["depth"], current["text"])
            current["depth"], current["text"] = depth, text
            original_scan(text, depth, bases)
            current["depth"], current["text"] = saved

        def hit(rule_id: str, evidence: str) -> None:
            word = current["word"]
            where = "path rule on a word raw-shaped %s" % shape(word.raw or "") if word is not None else "a command or raw-text rule"
            homes = [str(h) for h in ctx.home_variants]
            bases = sorted({("<home>" + b[len(h) :]) if b.startswith(h) else "<other>" for b in current["bases"] for h in homes[:1]})
            record.append((rule_id, analyzer._mode, shape(evidence), where, "scan depth %d" % current["depth"], "scanned text shaped " + re.sub(r"[0-9]", "9", re.sub(r"[A-Za-z]", "a", current["text"]))[:80], "bases shaped " + shape(" ".join(bases))))
            original(rule_id, evidence)

        analyzer.hit = hit
        analyzer._path_word = path_word
        analyzer._scan = scan
    try:
        return " ".join(sorted({h.rule_id for h in analyzer.analyze(command)})) or "ok"
    except guard.MalformedInput as exc:
        return "refused: " + str(exc).split(": ", 1)[0][:60]


def main(argv: list) -> int:
    root = Path(argv[1]).expanduser()
    files = sorted(root.rglob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)[: int(argv[2])]
    every = [command for path in files for command in commands(path)]
    older = load(argv[4], "guard_older")
    newer = load(argv[5], "guard_newer")
    rows = []
    counts = collections.Counter()
    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "home"
        for name in (".ssh", ".gnupg", ".claude"):
            (home / name).mkdir(parents=True)
        ctx_old = older.Context([str(home)], tmp)
        ctx_new = newer.Context([str(home)], tmp)
        for command in every:
            before = outcome(older, ctx_old, command)
            after = outcome(newer, ctx_new, command)
            if before != "ok" or after == "ok":
                continue
            record = []
            outcome(newer, ctx_new, command, record)
            differing = []
            for seg in newer.Lexer(command, faithful=True).run().segments:
                for word in seg.words:
                    try:
                        bash_words = newer.bash_brace_expand(word.raw or "")
                    except newer.MalformedInput:
                        bash_words = ["<refused>"]
                    if bash_words != [word.raw]:
                        differing.append(shape(word.raw or ""))
            counts[after] += 1
            rows.append({"after": after, "hits": sorted(set(record)), "raw_names_credential_dir": bool(re.search(r"\.(ssh|gnupg)", command, re.IGNORECASE)), "words_bash_expands": differing[:6], "length": len(command)})
    report = {"transcripts": len(files), "commands": len(every), "older passes, newer blocks": sum(counts.values()), "by newer outcome": dict(counts), "rows": rows}
    Path(argv[3]).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
