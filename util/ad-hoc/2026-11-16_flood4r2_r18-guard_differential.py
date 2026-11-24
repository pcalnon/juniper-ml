#!/usr/bin/env python3
"""
Differential of the agent guard's word reading against real bash, on words WITH quotes, escapes and substitutions.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-16
Status: ad-hoc — investigation (Cursor flood-4 disposition arc, session 9: the guard's word-structure hardening)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/claude_agent_guard.py (bash_brace_expand, Lexer.word_only); util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_port_differential.py
         (main's differential, on bare words only); util/ad-hoc/2026-11-16_flood4r2_r18-guard_bash_words.py (bash's side).

Usage:
    python3 -I util/ad-hoc/2026-11-16_flood4r2_r18-guard_differential.py <guard.py> <scratch dir> <out.json> [--n N] [--seed S]

Words are drawn from a fixed list of edge cases and a seeded generator over ATOMS: plain characters, brace syntax,
quoted and escaped brace characters, ``$'...'`` and ``$"..."``, and substitutions whose output is known (``$(:)`` is
empty, ``$(printf h)`` is ``h``, a backtick ``printf s`` is ``s``, ``${x}`` is empty, ``${x:-h}`` is ``h``,
``$((1))`` is ``1``). bash prints each word's words (``bash_words``: printf only, ``set -f``, PATH an empty
directory, a scratch HOME). The guard's words are the union of its two readings: reading B
(``bash_brace_expand`` on the word as written, then ``Lexer.word_only``) and reading A (main's lexer, then
``brace_expand``); each computed part is replaced by its known output. Classes, per word:

  exact     reading B's words equal bash's (empty words aside)
  over      every bash word is among the guard's, which judges more
  UNSAFE    bash makes a non-empty word that neither reading judges
  refused   reading B raises MalformedInput (fail closed)
  bash-fail bash exits non-zero with no words (a word bash itself rejects)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import random
import shlex
import sys
from pathlib import Path

KNOWN = {"$(:)": "", "$(printf h)": "h", "`printf s`": "s", "${x}": "", "${x:-h}": "h", "$((1))": "1", '"$(printf h)"': "h"}
ATOMS = ["a", "s", "h", ".", "/", "x", "{", "}", ",", "..", "{", "}", ",", "'{'", "'}'", "','", "\\{", "\\}", "\\,", "\\.", "\\$", "'$'", '"$"', "\"{a,b}\"", "$'\\x7d'", "$'\\x2c'", "$'\\x7b'", '$"s"', "$(:)", "$(printf h)", "`printf s`", "${x}", "${x:-h}", "$((1))", '"$(printf h)"', "{}", "{,}", "{h,s}", "{1..3}", "{a..c}"]
FIXED = [
    ".ss{h,b\\}c}", "su{do,x\\}y}", ".ss{h,$(:{)}", ".ss{h,`:{`}", ".ss$(:)h", ".ss`:`h", ".ss${x}h", "'$'{Y/../.ss,z}h",
    ".ss{h,$'\\x7d'c}", ".ss{h,\"$(:{)\"}", "{a,$'\\'',b}", "{}{},01,,-}", "{a..c','}", "{a,b'{'}", "\\${a,b}", "{a,$\"x,y\"}",
    "\"{a,b}\"", "{\"a,b\",c}", "{\\},a}", "$'{a,b}'", "\"$\"{a,b}", "${x:-{a,b}}", "'{'a,b}", "{a,b'}'", "{a,$(printf %s \")\")}",
    "{a,$((1)),b}", "{a,b}{}", "{{},a}", "{a,\"${x:-}}\"}", "{a,${x:-\\}}}", "{a\\,b,c}", "{a,b\\}", "{a..c\\}", "{'1'..3}",
    "{a,`printf %s \"}\"`}", "\"`printf %s \"{h,x}\"`\"", "{a,'$'{b,c}}", ".ss\"`printf %s \"{h,x}\"`\"", ".ss\"${x:-\"{h,y}\"}\"",
    "{a,b}=c", "x{a,b", "{,}", "{a,}{b}", "{1..3}'x'", "a{b,c}d{e,f}g", ".s{s,x}{h,y}", "{.ss,x}h", "{$'\\x2c',a}",
    ".ss{h,$(case x in a) : ;; esac)}", ".ss{h,$(: # )\n)}", "{a,$(: <<E\n)\nE\n)}",
]


def load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _words(text: str):
    try:
        return "".join(shlex.split(text))
    except ValueError:
        return None


def _value(part: str):
    """The output bash gives one computed part of the corpus (every body is :, printf, a case, or a parameter)."""
    if part in KNOWN:
        return KNOWN[part]
    if part.startswith("$(") or part.startswith("`"):
        body = (part[2:-1] if part.startswith("$(") else part[1:-1]).strip()
        if body.startswith(":") or body.startswith("case "):
            return ""
        if body.startswith("printf"):
            args = shlex.split(body)[1:]
            return "".join(args[1:] if args[:1] == ["%s"] else args)
        return None
    if part.startswith("${x:-") and part.endswith("}"):
        return _words(part[5:-1])
    return None


def evaluate(word) -> str:
    """The text bash makes of a guard word, each computed part replaced by its known output (None if unknown)."""
    out = []
    last = 0
    for start, end in word.spans:
        value = _value(word.text[start:end])
        if value is None:
            return None
        out.append(word.text[last:start])
        out.append(value)
        last = end
    out.append(word.text[last:])
    return "".join(out)


def guard_words(guard, raw: str) -> tuple:
    """(reading B's evaluated words, reading A's evaluated words, refusal reason or None)."""
    try:
        alts = guard.bash_brace_expand(raw)
    except guard.MalformedInput as exc:
        return set(), set(), str(exc)[:80]
    b_words = {evaluate(guard.Lexer(alt, faithful=True).word_only("arg")) for alt in alts}
    a_words = set()
    for seg in guard.Lexer(raw).run().segments:
        for word in seg.words:
            try:
                expanded = guard.brace_expand(word.text)
            except guard.MalformedInput:
                expanded = []
            a_words.update(_substitute_known(alt) for alt in expanded)
    return b_words, a_words, None


def _substitute_known(text: str) -> str:
    """Reading A's words keep no spans: replace each known substitution's text by its output."""
    for part, value in sorted(KNOWN.items(), key=lambda kv: -len(kv[0])):
        text = text.replace(part.strip('"'), value)
    return text


def generate(rng: random.Random, n: int) -> list:
    words = []
    while len(words) < n:
        size = rng.randint(2, 10)
        words.append("".join(rng.choice(ATOMS) for _ in range(size)))
    return words


def main(argv: list) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("guard")
    ap.add_argument("scratch")
    ap.add_argument("out")
    ap.add_argument("--n", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=20261115)
    args = ap.parse_args(argv[1:])
    here = Path(__file__).resolve().parent
    bash_side = load(str(here / "2026-11-16_flood4r2_r18-guard_bash_words.py"), "r18_bash_words")
    guard = load(args.guard, "r18_guard_under_test")
    rng = random.Random(args.seed)
    corpus = list(dict.fromkeys(FIXED + generate(rng, args.n)))
    bash = bash_side.bash_words(corpus, Path(args.scratch).resolve(), workers=4)
    counts = {"exact": 0, "over": 0, "UNSAFE": 0, "refused": 0, "bash-fail": 0}
    unsafe = []
    refused = []
    for raw, result in zip(corpus, bash):
        bash_set = {w for w in result["words"] if w}
        if result["exit"] != 0 and not bash_set:
            counts["bash-fail"] += 1
            continue
        b_words, a_words, reason = guard_words(guard, raw)
        if reason is not None:
            counts["refused"] += 1
            refused.append({"word": raw, "reason": reason, "bash": sorted(bash_set)[:8]})
            continue
        b_set = {w for w in b_words if w}
        if bash_set == b_set:
            counts["exact"] += 1
        elif bash_set <= (b_set | {w for w in a_words if w}):
            counts["over"] += 1
        else:
            counts["UNSAFE"] += 1
            unsafe.append({"word": raw, "bash": sorted(bash_set), "reading_b": sorted(w for w in b_set if w is not None), "missing": sorted(bash_set - b_set - a_words)})
    report = {"corpus": len(corpus), "fixed": len(FIXED), "generated": args.n, "seed": args.seed, "counts": counts, "unsafe": unsafe, "refused": refused}
    Path(args.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in ("unsafe", "refused")}, indent=1))
    for row in unsafe[:25]:
        print("UNSAFE", repr(row["word"]), "bash", row["bash"], "B", row["reading_b"], "missing", row["missing"])
    return 1 if unsafe else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
