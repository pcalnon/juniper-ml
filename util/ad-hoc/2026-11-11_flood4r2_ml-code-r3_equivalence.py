#!/usr/bin/env python3
"""
Show that two copies of the agent guard expand braces identically: same words in the same order, or the same refusal.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — one-off (Cursor flood-4 round-2 ml-code carrier, round 3: the linear brace scan)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: validator finding ml-code-port-lens F1 (the scan was quadratic); util/claude_agent_guard.py
         (_brace_closes, _brace_words, BRACE_SCAN_BUDGET); the round-2 guard, saved by the caller (round 2's
         carrier worktree holds it; tests/test_claude_agent_guard_brace_cap.py carries the same scan as an oracle,
         so the comparison of the scan itself needs no file from outside the tree).

Usage:
    python3 -I util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_equivalence.py <old guard.py> <new guard.py> <out.json>
        [--shard I/N] [--exhaustive LEN] [--structural LEN] [--random COUNT] [--long COUNT] [--seed SEED]

Round 3 replaced round 2's scan from each ``{`` (the square of the word's length) with one pass from the right.
This compares ``brace_expand`` of the two files on:
- every word of up to --exhaustive characters over ``{ } , . $ a 1`` (default 7: 960,800 words);
- every word of up to --structural characters over ``{ } , . a`` (default 9: 2,441,406 words);
- --random seeded words of 8 to 60 characters over a wider alphabet (signs, digits, letters, ``$``, ``-``);
- --long seeded words of 200 to 2,000 characters, mostly plain text with sparse braces and separators;
- shaped words where the old scan was slow or deep: runs of ``{a}``, of ``{``, of ``{1..1}``, nested lists up to
  and past the 64 cap, long alternatives, sequences next to lists.
A word counts as equal when both return the same list, or both raise the same exception class with the same
message. --shard I/N takes every N-th word of each enumeration, so N processes can share the work without the
multiprocessing module. Writes counts and every difference to <out.json>; exit 1 when any word differs.
"""
import argparse
import importlib.util
import itertools
import json
import random
import sys


def load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def outcome(module, word: str):
    try:
        return ("ok", module.brace_expand(word))
    except Exception as exc:  # the class and message are the result being compared
        return (exc.__class__.__name__, str(exc))


def shaped() -> list:
    words = []
    for n in (1, 2, 5, 30, 64, 65, 200):
        words += ["{a}" * n, "{" * n, "}" * n, "{1..1}" * n, "{a..a}" * n, "v%d={x%d};" % (n, n) * n, "{a}" * n + "{b,c}", "{a}" * n + ",}", "{b,c}" + "{a}" * n]
        words += ["{a," * n + "b" + "}" * n, "{" * n + "a,b" + "}" * n, "{a,b}" * min(n, 8), "x{1..%d}y" % n, "{%s}" % ",".join("p%d" % k for k in range(n))]
        words += ["${" * n + "a,b" + "}" * n, "{a,${b" * n + "}" * (2 * n), "{ab..cd}" * n, "{1..3..}" * n, "{a..}b,c}" * min(n, 6), "." * n + "{..}", "{" + "." * n + "}"]
    words += ["{a,b}{c,d}{e,f}{g,h}{i,j}{k,l}" + "{1..1}" * 40, "{{1..60},{1..60}}", "{{1..64},{1..64}}", "{" + "x" * 5000 + ",y}", "{a,b}" + "z" * 5000, "{a..{c,d}}" + "{q}" * 50]
    words += ["{%s}" % ("x" * k + "," + "y" * k) * 3 for k in (1, 10, 100)]
    return words


def enumerate_words(alphabet: str, longest: int):
    for length in range(longest + 1):
        for letters in itertools.product(alphabet, repeat=length):
            yield "".join(letters)


def random_words(count: int, seed: int):
    rng = random.Random(seed)
    alphabet = "{{{}}},,,...$-+0123456789abcYZ_"
    for _ in range(count):
        yield "".join(rng.choice(alphabet) for _ in range(rng.randint(8, 60)))


def long_words(count: int, seed: int):
    """Mostly plain text with sparse braces and separators, so groups are far apart and often stay under the cap."""
    rng = random.Random(seed)
    alphabet = "aaaaaaaaaaaaaaaaaaaaaaaa01bc/_-{{}},..$"
    for _ in range(count):
        yield "".join(rng.choice(alphabet) for _ in range(rng.randint(200, 2000)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("old")
    ap.add_argument("new")
    ap.add_argument("out")
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--exhaustive", type=int, default=7)
    ap.add_argument("--structural", type=int, default=9)
    ap.add_argument("--random", type=int, default=400000)
    ap.add_argument("--long", type=int, default=4000)
    ap.add_argument("--seed", type=int, default=20261111)
    args = ap.parse_args()
    index, shards = (int(part) for part in args.shard.split("/"))
    old, new = load(args.old, "guard_old"), load(args.new, "guard_new")
    sources = (
        ("exhaustive<=%d over '{},.$a1'" % args.exhaustive, enumerate_words("{},.$a1", args.exhaustive)),
        ("structural<=%d over '{},.a'" % args.structural, enumerate_words("{},.a", args.structural)),
        ("random 8..60 chars, seed %d" % args.seed, random_words(args.random, args.seed)),
        ("random 200..2000 chars, seed %d" % (args.seed + 1), long_words(args.long, args.seed + 1)),
        ("shaped", iter(shaped())),
    )
    report = {"old": args.old, "new": args.new, "old_version": old.__version__, "new_version": new.__version__, "shard": args.shard, "sets": [], "differences": []}
    for label, words in sources:
        seen = same_ok = same_refused = 0
        for number, word in enumerate(words):
            if number % shards != index:
                continue
            seen += 1
            a, b = outcome(old, word), outcome(new, word)
            if a != b:
                report["differences"].append({"set": label, "word": word[:300], "old": [a[0], str(a[1])[:400]], "new": [b[0], str(b[1])[:400]]})
            elif a[0] == "ok":
                same_ok += 1
            else:
                same_refused += 1
        report["sets"].append({"set": label, "words": seen, "same_words": same_ok, "same_refusal": same_refused})
        print("%-44s words %9d  same words %9d  same refusal %8d" % (label, seen, same_ok, same_refused), flush=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=1)
    print("differences: %d" % len(report["differences"]))
    return 1 if report["differences"] else 0


if __name__ == "__main__":
    sys.exit(main())
