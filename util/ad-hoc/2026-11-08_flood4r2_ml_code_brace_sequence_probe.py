#!/usr/bin/env python3
"""
Compare the agent guard's brace_expand with this host's bash, word by word, for brace sequence expressions.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation (flood-4 round-2 ml-code carrier: the increment-range bypass, owner ruling "Carry in ml-code")
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: tmp/flood4r2/ml-code/proposed/increment_range_probe.txt (the builder's finding: `cat ~/.{r..t..1}sh/config`
         passed the guard); BRIEF_COMMON_R2 rules 12 and 14.

Usage: python3 -I 2026-11-08_flood4r2_ml_code_brace_sequence_probe.py <guard file> <out.json> [--fuzz N] [--seed S]

For every word, bash runs ``set -f; echo WORD; printf '<%s>\\n' WORD`` in an empty scratch directory with a
minimal environment (HOME is that directory, PATH is /usr/bin:/bin), under ``ulimit -v 409600; ulimit -t 5`` (400 MB,
5 CPU seconds: bash builds a whole sequence before it prints one word). ``set -f`` turns pathname expansion off, so the
printf lines are exactly the words brace expansion produced; the echo line is kept for reading. The fixed cases run
under LC_ALL=C and LC_ALL=C.UTF-8 and must agree; the fuzz words run under C.UTF-8. In this process the guard file
is loaded by path and ``brace_expand(WORD)`` is called. Each word is then classified:

  exact    the guard's set is bash's words plus the source word (brace_expand always keeps the source word)
  refused  the guard raised MalformedInput: fail closed (the message is recorded)
  over     the guard's set strictly contains bash's: it judges more spellings than bash produces (no bypass)
  UNSAFE   bash produces a word the guard never judges: the class of the {r..t..1} bypass
  bash-error  the guard did not refuse, and bash rejected the command (it never runs), e.g. a generated backtick
              that opens a command substitution with no close

The fixed cases are named by category. The fuzz words come from a seeded generator (a small brace grammar and a
token soup over ``{ } , .. . a c s Z 0 1 3 01 -1 + -``), so a run is reproducible; words without ``..`` never reach
the sequence code and are reported apart, since a difference there is the list expander's, not the sequences'.

Writes <out.json> and <out>.txt (a table). Exit 0 when no fixed case and no fuzz word containing ``..`` is UNSAFE.
"""

import argparse
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import random
import shutil
import subprocess  # nosec B404 -- runs bash on words from a fixed alphabet
import sys
import tempfile
from pathlib import Path

INTMAX = "9223372036854775807"
FIXED = [
    ("char", "{a..e}"),
    ("char", "{e..a}"),
    ("char", "{a..a}"),
    ("char", "{r..t}"),
    ("char", "{A..E}"),
    ("char", "{Z..a}"),
    ("char", "{a..Z}"),
    ("char", "{X..c}"),
    ("char", "{A..z}"),
    ("char-backslash", ".ss{Y..a..3}h"),
    ("char-backtick", "{Z..a..3}pwd{Z..a..3}"),
    ("char-step", "{a..e..2}"),
    ("char-step", "{e..a..2}"),
    ("char-step", "{a..e..1}"),
    ("char-step", "{r..t..1}"),
    ("char-step", "{a..z..5}"),
    ("char-step", "{A..z..2}"),
    ("char-step", "{a..e..+2}"),
    ("char-step", "{a..e..02}"),
    ("char-negative-step", "{a..e..-2}"),
    ("char-negative-step", "{e..a..-2}"),
    ("char-negative-step", "{t..r..-1}"),
    ("char-negative-step", "{r..t..-1}"),
    ("char-zero-step", "{a..e..0}"),
    ("char-zero-step", "{e..a..0}"),
    ("char-zero-step", "{a..e..-0}"),
    ("char-zero-step", "{a..e..00}"),
    ("char-step-past-range", "{a..e..10}"),
    ("char-step-past-range", "{e..a..-10}"),
    ("char-step-past-range", "{a..a..3}"),
    ("char-step-past-range", "{s..s..1}"),
    ("char-step-past-range", "{a..b..2}"),
    ("int", "{1..5}"),
    ("int", "{5..1}"),
    ("int", "{-2..2}"),
    ("int", "{2..-2}"),
    ("int", "{0..0}"),
    ("int", "{-0..2}"),
    ("int", "{+1..3}"),
    ("int", "{1..+3}"),
    ("int", "{-1..-3}"),
    ("int", "{7..7}"),
    ("int-step", "{1..10..3}"),
    ("int-step", "{10..1..3}"),
    ("int-step", "{1..5..+2}"),
    ("int-step", "{1..5..02}"),
    ("int-step", "{-5..5..5}"),
    ("int-step", "{5..-5..5}"),
    ("int-step", "{0..9..4}"),
    ("int-negative-step", "{1..10..-3}"),
    ("int-negative-step", "{10..1..-3}"),
    ("int-negative-step", "{-1..-9..-4}"),
    ("int-zero-step", "{1..5..0}"),
    ("int-zero-step", "{5..1..0}"),
    ("int-zero-step", "{1..5..-0}"),
    ("int-zero-step", "{1..5..000}"),
    ("int-step-past-range", "{1..5..10}"),
    ("int-step-past-range", "{5..1..-10}"),
    ("int-step-past-range", "{2..2..1}"),
    ("int-step-past-range", "{1..2..2}"),
    ("int-step-past-range", "{1..1..-5}"),
    ("zero-padded", "{01..03}"),
    ("zero-padded", "{1..03}"),
    ("zero-padded", "{01..3}"),
    ("zero-padded", "{001..3}"),
    ("zero-padded", "{1..010}"),
    ("zero-padded", "{00..3}"),
    ("zero-padded", "{0..03}"),
    ("zero-padded", "{-01..3}"),
    ("zero-padded", "{-1..03}"),
    ("zero-padded", "{-001..2}"),
    ("zero-padded", "{3..01}"),
    ("zero-padded", "{1..-03}"),
    ("zero-padded", "{+01..3}"),
    ("zero-padded", "{+1..03}"),
    ("zero-padded", "{+01..03}"),
    ("zero-padded", "{-0..3}"),
    ("zero-padded", "{-00..3}"),
    ("zero-padded", "{00..00}"),
    ("zero-padded", "{-0..-0}"),
    ("zero-padded", "{-00..-00}"),
    ("zero-padded-step", "{01..10..3}"),
    ("zero-padded-step", "{010..1..3}"),
    ("zero-padded-step", "{1..10..03}"),
    ("zero-padded-step", "{05..1..-2}"),
    ("zero-padded-step", "{-05..05..5}"),
    ("zero-padded-step", "{001..2..7}"),
    ("not-a-sequence", "{a..1}"),
    ("not-a-sequence", "{1..a}"),
    ("not-a-sequence", "{aa..b}"),
    ("not-a-sequence", "{a..bb}"),
    ("not-a-sequence", "{a..}"),
    ("not-a-sequence", "{..a}"),
    ("not-a-sequence", "{a..b..}"),
    ("not-a-sequence", "{a..b..c}"),
    ("not-a-sequence", "{1..2..x}"),
    ("not-a-sequence", "{1..2..1..2}"),
    ("not-a-sequence", "{1..2..1.5}"),
    ("not-a-sequence", "{1.5..3}"),
    ("not-a-sequence", "{a...c}"),
    ("not-a-sequence", "{1...3}"),
    ("not-a-sequence", "{a..b.}"),
    ("not-a-sequence", "{..}"),
    ("not-a-sequence", "{...}"),
    ("not-a-sequence", "{1..2.}"),
    ("not-a-sequence", "{1..3..+}"),
    ("not-a-sequence", "{1..3..-}"),
    ("not-a-sequence", "{--1..3}"),
    ("not-a-sequence", "{1..--3}"),
    ("not-a-sequence", "{0x1..3}"),
    ("not-a-sequence", "{a..1}{x,y}"),
    ("not-a-sequence", "x{a..1}y"),
    ("not-a-sequence", "{a..e..2x}"),
    ("nested", "{{a..c},d}"),
    ("nested", "{a..{c,d}}"),
    ("nested", "{{a..c}..e}"),
    ("nested", "{a..{b..c}}"),
    ("nested", "{x{a..c}}"),
    ("nested", "{{a..c}}"),
    ("nested", "{a,{1..3..1}}"),
    ("nested", "{{1..3..1},a}"),
    ("nested", "{a..c{1,2}}"),
    ("nested", "x{{a,b}..c}"),
    ("nested", "{a..c,{d..f}}"),
    ("nested", "{{r..t..1}..x}"),
    ("nested", "{a..{c,d}}z"),
    ("nested", "{{a..c}..e}{x,y}"),
    ("nested", "{a..c}{1..2..1}"),
    ("nested", "{{a,b}..{c,d}}"),
    ("nested", "{a..{b..d,e}}"),
    ("nested", "{{01..02},{a..c..2}}"),
    ("nested", "{1..{2,3}}"),
    ("nested", "{1..3{,}}"),
    ("nested", "{{1..2}..{3..4}}"),
    ("nested", "{x,{a..e..2}y}"),
    ("nested", "{{a..c}x,y}"),
    ("nested", "{a..e..{1,2}}"),
    ("nested", "{a..{e..2}}"),
    ("nested", "{{a..c}..e..2}"),
    ("extreme", "{%s..9223372036854775806}" % INTMAX),
    ("extreme", "{9223372036854775808..%s}" % INTMAX),
    ("extreme", "{1..3..9223372036854775808}"),
    ("extreme", "{-9223372036854775808..-%s}" % INTMAX),
    ("extreme", "{0..9223372036854775806..1000000000000000000}"),
    ("extreme", "{1..2..-9223372036854775808}"),
    ("extreme", "{1..2..%s}" % INTMAX),
    ("extreme", "{-9223372036854775808..%s..%s}" % (INTMAX, INTMAX)),
    ("extreme", "{9223372036854775800..%s..5}" % INTMAX),
    ("extreme", "{-9223372036854775809..1}"),
    ("credential", ".{r..t..1}sh"),
    ("credential", ".{f..h..1}nupg"),
    ("credential", ".ss{h..h..1}"),
    ("credential", ".{s..s..5}sh"),
    ("credential", ".{t..r..-1}sh"),
    ("credential", ".{q..u..2}sh"),
    ("credential", ".gnup{g..g..0}"),
    ("credential", "{s..s..1}udo"),
    ("credential", "gpg{2..2..1}"),
    ("credential", "gpg{0..2..2}"),
    ("credential", "gpg{02..2}"),
    ("credential", ".{s..s}sh"),
    ("test-pin", "{1..010..3}"),
    ("test-pin", "{Y..a..2}"),
    ("test-pin", "{x{.,a}.y}"),
    ("test-pin", "{a}b,c}"),
    ("test-pin", "{1..9223372036854775808}"),
    ("test-pin", "{2305843009213693952..2305843009213693952}"),
    ("test-pin", "{2305843009213693953..2305843009213693953}"),
    ("test-pin", "{1..640..10}"),
    ("test-pin", "{1..650..10}"),
    ("test-pin", "{+1..+3}"),
    ("test-pin", "{a..e..2}x{1..2}"),
    ("test-pin", "{Z..a..3}"),
]
SOUP = ["{", "{", "}", "}", ",", "..", "..", ".", "a", "c", "s", "Z", "0", "1", "3", "01", "-1", "+", "-"]
ATOMS = ["a", "c", "e", "s", "Z", "z", "0", "1", "3", "10", "01", "003", "-1", "-02", "+2", "x", ""]
STEPS = ["0", "1", "2", "-1", "-3", "+2", "02", "9", ""]
FILLERS = ["a", ".", "s", "1", ".ss", "x", ""]


def load_guard(path: str):
    loader = importlib.machinery.SourceFileLoader("guard_under_probe", path)
    spec = importlib.util.spec_from_loader("guard_under_probe", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def bash_words(bash: str, word: str, scratch: str, locale: str) -> tuple:
    env = {"PATH": "/usr/bin:/bin", "HOME": scratch, "LC_ALL": locale}
    # bash really builds a sequence before printing it ({1..2147483647..2} passes 1 GB in seconds), so cap the child.
    script = "ulimit -v 409600; ulimit -t 5; set -f; echo %s; printf '<%%s>\\n' %s" % (word, word)
    proc = subprocess.run([bash, "-c", script], cwd=scratch, env=env, capture_output=True, text=True, timeout=20, check=False)  # nosec B603 -- fixed argv, words from a fixed alphabet
    lines = proc.stdout.split("\n")
    echo = lines[0] if lines else ""
    words = [line[1:-1] for line in lines[1:] if line.startswith("<") and line.endswith(">")]
    return proc.returncode, echo, words, proc.stderr.strip()


def guard_words(guard, word: str) -> tuple:
    try:
        return guard.brace_expand(word), None
    except guard.MalformedInput as exc:
        return None, str(exc)


def classify(word: str, bash: list, guard: list, refusal, bash_exit: int = 0) -> str:
    if refusal is not None:
        return "refused"
    if bash_exit != 0:
        return "bash-error"
    got = set(guard)
    if got == set(bash) | {word}:
        return "exact"
    return "over" if set(bash) <= got else "UNSAFE"


def seq_word(rng) -> str:
    body = rng.choice(ATOMS) + ".." + rng.choice(ATOMS)
    if rng.random() < 0.5:
        body += ".." + rng.choice(STEPS)
    return "{" + body + "}"


def grammar_word(rng, depth: int = 0) -> str:
    parts = []
    for _ in range(rng.randint(1, 3)):
        roll = rng.random()
        if roll < 0.35:
            parts.append(seq_word(rng))
        elif roll < 0.55 and depth < 2:
            items = [grammar_word(rng, depth + 1) if rng.random() < 0.4 else rng.choice(ATOMS) for _ in range(rng.randint(1, 3))]
            parts.append("{" + ",".join(items) + "}")
        elif roll < 0.7 and depth < 2:
            parts.append("{" + grammar_word(rng, depth + 1) + ".." + rng.choice(ATOMS) + "}")
        elif roll < 0.8 and depth < 2:
            parts.append("{" + rng.choice(ATOMS) + ".." + grammar_word(rng, depth + 1) + "}")
        else:
            parts.append(rng.choice(FILLERS))
    return "".join(parts)


def fuzz_words(count: int, seed: int) -> list:
    rng = random.Random(seed)
    words = []
    seen = set()
    while len(words) < count:
        if rng.random() < 0.6:
            word = grammar_word(rng)
        else:
            word = "".join(rng.choice(SOUP) for _ in range(rng.randint(3, 10)))
        if "{" in word and word not in seen and len(word) <= 40:
            seen.add(word)
            words.append(word)
    return words


def render(report: dict) -> list:
    lines = ["# %s | guard %s %s (sha256 %s)" % (report["bash_version"], report["guard"], report["guard_version"], report["guard_sha256"])]
    for row in report["fixed"]:
        if row["refusal"]:
            shown = "REFUSED: " + row["refusal"][:60]
        else:
            shown = " ".join(w for w in (row["guard"] or []) if w != row["word"]) or "(source word only)"
        lines.append("%-8s %-22s %-46s bash: %-40s guard: %s" % (row["verdict"], row["category"], row["word"], " ".join(row["bash_words"]), shown))
    fuzz = report["fuzz"]
    lines.append("fuzz (seed %d, %d words): %s" % (fuzz["seed"], fuzz["count"], json.dumps(fuzz["counts"], sort_keys=True)))
    for row in fuzz["notable"]:
        shown = ("REFUSED: " + row["refusal"][:50]) if row["refusal"] else " ".join(row["guard"] or [])
        lines.append("fuzz %-8s %-9s %-42s bash: %-40s guard: %s" % (row["verdict"], row["scope"], row["word"], " ".join(row["bash_words"]), shown))
    lines.append("summary: %s" % json.dumps(report["summary"], sort_keys=True))
    return lines


def main(argv: list) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("guard")
    ap.add_argument("out")
    ap.add_argument("--fuzz", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=20261109)
    args = ap.parse_args(argv[1:])
    bash = shutil.which("bash") or "/bin/bash"
    version = subprocess.run([bash, "--version"], capture_output=True, text=True, check=False).stdout.splitlines()[0]  # nosec B603 -- fixed argv
    with open(args.guard, "rb") as fh:
        guard_sha = hashlib.sha256(fh.read()).hexdigest()
    guard = load_guard(args.guard)
    scratch = tempfile.mkdtemp(prefix="brace-probe-")
    report = {"bash": os.path.realpath(bash), "bash_version": version, "guard": args.guard, "guard_sha256": guard_sha, "guard_version": getattr(guard, "__version__", "?"), "fixed": [], "fuzz": {}}
    try:
        for category, word in FIXED:
            runs = {loc: bash_words(bash, word, scratch, loc) for loc in ("C", "C.UTF-8")}
            code, echo, words, err = runs["C.UTF-8"]
            got, refusal = guard_words(guard, word)
            verdict = classify(word, words, got or [], refusal, code)
            report["fixed"].append({"category": category, "word": word, "bash_exit": code, "bash_echo": echo, "bash_words": words, "bash_stderr": err, "locales_agree": runs["C"][2] == words, "guard": got, "refusal": refusal, "verdict": verdict})
        counts = {}
        notable = []
        fuzz = fuzz_words(args.fuzz, args.seed)
        for word in fuzz:
            code, _echo, words, err = bash_words(bash, word, scratch, "C.UTF-8")
            got, refusal = guard_words(guard, word)
            verdict = classify(word, words, got or [], refusal, code)
            scope = "sequence" if ".." in word else "list-only"
            counts.setdefault(scope, {}).setdefault(verdict, 0)
            counts[scope][verdict] += 1
            if verdict in ("UNSAFE", "over", "bash-error") or (verdict == "refused" and "more than" not in (refusal or "")):
                notable.append({"scope": scope, "word": word, "bash_words": words, "bash_stderr": err, "guard": got, "refusal": refusal, "verdict": verdict})
        report["fuzz"] = {"seed": args.seed, "count": len(fuzz), "counts": counts, "notable": notable}
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    verdicts = {}
    for row in report["fixed"]:
        verdicts[row["verdict"]] = verdicts.get(row["verdict"], 0) + 1
    report["summary"] = {
        "fixed_verdicts": verdicts,
        "fixed_unsafe": [row["word"] for row in report["fixed"] if row["verdict"] == "UNSAFE"],
        "fuzz_sequence_unsafe": [row["word"] for row in report["fuzz"]["notable"] if row["verdict"] == "UNSAFE" and row["scope"] == "sequence"],
        "locale_disagreements": [row["word"] for row in report["fixed"] if not row["locales_agree"]],
    }
    out = Path(args.out)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = render(report)
    out.with_suffix(".txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[-1:]))
    summary = report["summary"]
    return 1 if summary["fixed_unsafe"] or summary["fuzz_sequence_unsafe"] or summary["locale_disagreements"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
