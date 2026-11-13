#!/usr/bin/env python3
"""
Differential test of the agent guard's brace_expand against this host's bash, on an independently generated corpus.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-11
Status: ad-hoc — investigation (Cursor flood-4 round-2 ml-code carrier, round 3: the validator's corpus, run again)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: validator findings ml-code-port-lens F1 and F5. This is the port lens's own generator
         (2026-11-09_flood4r2_val_ml-code-port_differential.py, written for the round-2 validation), copied with only
         this header changed, so that ``--n 6000 --seed 20261109`` draws the 10,934 words the validator judged round 2
         on. The builder's own probe, util/ad-hoc/2026-11-08_flood4r2_ml_code_brace_sequence_probe.py, shares no
         corpus or generator with it.

Usage: python3 -I 2026-11-11_flood4r2_ml-code-r3_port_differential.py <guard file> <out.json> [--n N] [--seed S] [--workers W]

Words are drawn from four sources, none containing a quote, a backslash, ``$``, a backtick, ``~``, whitespace or a
shell metacharacter, so bash's brace expansion sees exactly the text the guard sees:

  fixed     a hand-written list of edge cases (padding, signs, steps, intmax_t edges, nesting, odd separators)
  grammar   a recursive brace grammar: lists of 0-5 parts (empty parts, nested lists, nested sequences,
            stray braces), sequences with integer, letter, mixed, signed, padded, huge and non-ASCII endpoints
  soup      random strings over a brace-heavy token alphabet
  seqmix    sequences inside lists and lists inside sequences, with prefixes and suffixes

For each word bash runs ``ulimit -v 409600; ulimit -t 3; set -f; printf '%s\\037' WORD`` (one process per word,
``W`` at a time, at most 4, PATH an empty directory so a generated backtick runs nothing, LC_ALL=C, HOME a scratch
directory, 10 s timeout; the ulimits matter: bash really builds a sequence such as {1..2147483647..2}, and a first
run without them grew four children past 1 GB each before it was stopped). The guard file is
loaded by path and ``brace_expand(WORD)`` is timed. Classes:

  exact    the guard's set minus the source word equals bash's words minus the source word
  over     the guard judges every bash word plus more (never a miss)
  UNSAFE   bash makes a non-empty word the guard does not judge
  refused  MalformedInput (fail closed)        crash   any other exception (also fail closed in the hook)
  bash-fail bash produced nothing parseable (rc != 0 and no words)

Writes <out.json> (every non-exact row in full, counts by class and source, the slowest words) and prints a summary.
"""

import argparse
import importlib.util
import json
import random
import subprocess  # nosec B404 -- runs bash printf on generated words without metacharacters
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

INTMAX = 2**63 - 1
INT_EDGES = ["0", "1", "2", "3", "9", "10", "-1", "-2", "+1", "+3", "01", "001", "010", "-01", "-001", "-0", "+0", "00", "+01", "007", "99", "100", "-10", "2147483647", "2147483648", "02147483648", "4294967296", "04294967296", "-2147483649", str(2**61), str(2**61 + 1), "-" + str(2**61), str(2**62), str(INTMAX), str(INTMAX + 1), "-" + str(INTMAX + 1), "-" + str(INTMAX + 2), "0" + str(2**61)]
LETTERS = ["a", "b", "c", "e", "h", "s", "t", "x", "z", "A", "C", "Y", "Z", "é", "Ω", "ab"]
STEPS = ["0", "1", "2", "3", "-1", "-2", "+2", "-0", "02", "26", "64", "65", "1000", str(2**31), str(2**61), str(2**62), str(INTMAX), str(INTMAX + 1), ""]
SOUP = ["{", "}", ",", "..", ".", "a", "s", "h", "Z", "Y", "0", "1", "9", "01", "-1", "+", "-", "/", "x", "{}", "{,}", "{a}", ",,", "...", "é", "_", "@", "%", "="]

FIXED = [
    "{}", "{,}", "{a}", "{,,}", "{a,}", "{,a}", "x{}y", "x{,}y", "{}{a,b}", "{},a}", "{a}b,c}", "{a,b}}", "{{a,b}", "{{a,b}}",
    "{a,{b,c}}", "{a,{b,{c,d}}}", "{{{a,b},c},d}", "{a{,}}", "{,{,}}", "{.,a}", "{x{.,a}.y}", "{a..c}{1..2}", "{a..c}x{1..2}",
    "{1..3", "1..3}", "{1...3}", "{1....3}", "{1..3..}", "{..3}", "{1..}", "{..}", "{...}", "{a..}", "{1..3..2..1}",
    "{1..10..3}", "{10..1..3}", "{1..10..-3}", "{10..1..-3}", "{1..1..5}", "{5..1..0}", "{a..z..5}", "{z..a..-5}", "{A..z..7}",
    "{a..A}", "{Z..a..4}", "{Z..a..5}", "{a..Z..2}", "{z..Z..10}", "{01..3}", "{1..03}", "{-01..1}", "{-1..01}", "{-0..2}",
    "{+01..3}", "{1..+03}", "{007..9}", "{9..007}", "{0..0}", "{-0..-0}", "{00..0}", "{1..-1}", "{-3..3..2}", "{3..-3..2}",
    "{1..2..+1}", "{1..2..01}", "{a..c..+1}", "{a..c..01}", "{a..c..-0}", "{1..2147483648..2147483647}",
    "{2147483647..2147483649}", "{02147483647..02147483649}", "{04294967296..04294967297}", "{4294967296..4294967297}",
    "{-2147483649..-2147483648}", "{-02147483649..-02147483648}", "{9223372036854775806..9223372036854775807}",
    "{0..9223372036854775807..4611686018427387904}", "{a..b}{c..d}{e..f}{g..h}{i..j}{k..l}{m..n}",
    "{1..64}", "{1..65}", "{0..63}", "{a..z}{a..b}{a..b}", "{a,b}{c,d}{e,f}{g,h}{i,j}{k,l}{m,n}",
    "{a..c,d}", "{a,c..e}", "{1..3,5}", "{a..{c,d}}", "{{a,b}..c}", "{a..c{d,e}}", "{a,b..c}", "{1,2..3}", "{.,.}", "{..,}",
    "{,..}", "{a.,.b}", "{a..b.}", "{.a..b}", "x{a..b}.{c..d}", "{a..b}..{c..d}", "{a..b..}{1..2}", "{é..ê}",
    "{a..é}", "{é,a}", "{Ω..A}", "{1..٣}", "{١..3}", "-{a,b}", "+{1..2}", "{-,+}", "{-a,-b}", "{--a,b}",
    "{a,b}-", "{1..2}-{3..4}", "-{-1..-3}-", "{a,b}{}", "{}{}", "{{}}", "{{},}", "{,{}}", "{a,{}}", "{}a,b}", "a{}b,c}",
    "{a,}{,b}", "{,}{,}{,}", "{1..1}", "{1..1}{1..1}{1..1}", "{a..a}", "{a..a..0}", "{Y..a..3}", "{a..Y..3}", "{Z..a..6}",
    "{.ss,h}", ".ss{h,}", ".{s,}s{h,}", ".s{s,}{h,}", ".{r..t}sh", ".{q..z..2}sh", ".s{r..t}h", ".ss{g..i}", ".{s..s}{s..s}{h..h}",
    ".gnu{o..q}g", ".gn{u..u}pg", ".{f..h}nupg", "{.,}ssh", "{.ssh,}", "{a..c}.ssh", "/{home,x}/{a..b}",
]


def load_guard(path: Path):
    spec = importlib.util.spec_from_file_location("validator_guard_under_test", str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def endpoint(rng: random.Random) -> str:
    roll = rng.random()
    if roll < 0.45:
        return rng.choice(INT_EDGES)
    if roll < 0.85:
        return rng.choice(LETTERS)
    return rng.choice(["", "1a", "a1", ".", "{a,b}", "{1..2}", "-", "+", "0x1", "1e3"])


def sequence(rng: random.Random, depth: int) -> str:
    left, right = endpoint(rng), endpoint(rng)
    if depth < 2 and rng.random() < 0.1:
        left = grammar_word(rng, depth + 1)
    step = rng.choice(STEPS)
    body = "%s..%s" % (left, right) + ("..%s" % step if step and rng.random() < 0.55 else "")
    return "{%s}" % body


def brace_list(rng: random.Random, depth: int) -> str:
    parts = []
    for _ in range(rng.choice([0, 1, 2, 2, 2, 3, 3, 4, 5])):
        roll = rng.random()
        if roll < 0.15:
            parts.append("")
        elif roll < 0.3 and depth < 4:
            parts.append(brace_list(rng, depth + 1))
        elif roll < 0.45 and depth < 4:
            parts.append(sequence(rng, depth + 1))
        elif roll < 0.55:
            parts.append(rng.choice(["{}", "{a}", "}", "{", "..", "a..b", "1..3", "{,}"]))
        else:
            parts.append(rng.choice(["a", "b", "s", "h", ".ss", "x1", "-", "+", "0", "01", "Z", "é"]))
    if len(parts) < 2 and rng.random() < 0.7:
        parts.append(rng.choice(["", "a", "{b,c}"]))
    return "{%s}" % ",".join(parts)


def grammar_word(rng: random.Random, depth: int = 0) -> str:
    pieces = []
    for _ in range(rng.choice([1, 1, 2, 2, 3, 4])):
        roll = rng.random()
        if roll < 0.35:
            pieces.append(brace_list(rng, depth))
        elif roll < 0.65:
            pieces.append(sequence(rng, depth))
        elif roll < 0.8:
            pieces.append(rng.choice(["x", ".", "-", "+", "/", "ab", ".ss", "h", "0", "_"]))
        else:
            pieces.append(rng.choice(["{", "}", ",", "..", "{}", "{,}", "{a}", "}{", "{.."]))
    return "".join(pieces)


def soup_word(rng: random.Random) -> str:
    return "".join(rng.choice(SOUP) for _ in range(rng.randint(2, 14)))


def seqmix_word(rng: random.Random) -> str:
    seq = sequence(rng, 3)
    inner = "{%s,%s}" % (seq, rng.choice(["a", "", "{b,c}", sequence(rng, 3)]))
    outer = "{%s..%s}" % (rng.choice(["a", "1", inner]), rng.choice(["c", "3", inner]))
    return rng.choice(["", "x", "-", ".s", "0"]) + rng.choice([inner, outer, seq + inner, inner + seq]) + rng.choice(["", "y", ".", "1"])


def bash_expand(word: str, scratch: Path, empty_path: Path) -> dict:
    env = {"HOME": str(scratch), "PATH": str(empty_path), "LC_ALL": "C"}
    # bash really builds {1..2147483647..2} (10**9 strings): cap every child at 400 MB and 3 CPU seconds so a huge
    # sequence fails inside bash ("failed to allocate memory") instead of eating the host's memory.
    script = "ulimit -v 409600; ulimit -t 3; set -f; printf '%%s\\037' %s" % word
    try:
        proc = subprocess.run(["/usr/bin/bash", "-c", script], cwd=str(scratch), env=env, stdin=subprocess.DEVNULL, capture_output=True, timeout=10)  # nosec B603
    except subprocess.TimeoutExpired:
        return {"rc": None, "words": None, "err": "TIMEOUT"}
    out = proc.stdout.decode("utf-8", "surrogateescape")
    words = out.split("\x1f")[:-1] if out.endswith("\x1f") else None
    return {"rc": proc.returncode, "words": words, "err": proc.stderr.decode("utf-8", "replace")[-200:]}


def guard_expand(guard, word: str) -> dict:
    started = time.perf_counter()
    try:
        alts = guard.brace_expand(word)
        status = "ok"
        detail = ""
    except guard.MalformedInput as exc:
        alts, status, detail = None, "refused", str(exc)[:200]
    except Exception as exc:  # the hook would fail closed on this too; record it
        alts, status, detail = None, "crash", "%s: %s" % (exc.__class__.__name__, str(exc)[:200])
    return {"status": status, "alts": alts, "detail": detail, "seconds": time.perf_counter() - started}


def classify(word: str, bash: dict, guard: dict) -> str:
    if guard["status"] != "ok":
        return guard["status"]
    if bash["words"] is None:
        return "bash-fail"
    gset = set(guard["alts"]) - {word}
    bset = set(w for w in bash["words"] if w != "") - {word}
    if bset - set(guard["alts"]):
        return "UNSAFE"
    if gset - {""} == bset:
        return "exact"
    return "over"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("guard", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--n", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=20261109)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    guard = load_guard(args.guard.resolve())
    rng = random.Random(args.seed)
    corpus = [("fixed", w) for w in FIXED]
    corpus += [("grammar", grammar_word(rng)) for _ in range(args.n)]
    corpus += [("soup", soup_word(rng)) for _ in range(args.n // 2)]
    corpus += [("seqmix", seqmix_word(rng)) for _ in range(args.n // 2)]
    seen = set()
    corpus = [(src, w) for src, w in corpus if not (w in seen or seen.add(w))]
    with tempfile.TemporaryDirectory(prefix="brace-diff-") as tmp:
        scratch = Path(tmp)
        empty_path = scratch / "empty-path"
        empty_path.mkdir()
        with ThreadPoolExecutor(max_workers=min(args.workers, 4)) as pool:
            bash_rows = list(pool.map(lambda item: bash_expand(item[1], scratch, empty_path), corpus))
    rows = []
    counts = {}
    for (src, word), bash in zip(corpus, bash_rows):
        guard_row = guard_expand(guard, word)
        cls = classify(word, bash, guard_row)
        counts.setdefault(src, {}).setdefault(cls, 0)
        counts[src][cls] += 1
        order_differs = cls == "exact" and bash["words"] and guard_row["alts"] and [a for a in guard_row["alts"] if a != word or word in bash["words"]] != [w for w in bash["words"] if w != ""]
        rows.append({"source": src, "word": word, "class": cls, "bash": bash["words"], "bash_rc": bash["rc"], "bash_err": bash["err"], "guard": guard_row["alts"], "guard_detail": guard_row["detail"], "seconds": round(guard_row["seconds"], 6), "order_differs": bool(order_differs)})
    keep = [r for r in rows if r["class"] not in ("exact",)]
    slowest = sorted(rows, key=lambda r: -r["seconds"])[:10]
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump({"guard": str(args.guard), "seed": args.seed, "n": len(rows), "counts": counts, "non_exact": keep, "slowest": [{"word": r["word"], "seconds": r["seconds"]} for r in slowest], "order_differs": sum(1 for r in rows if r["order_differs"])}, fh, indent=1, ensure_ascii=False)
    print(json.dumps(counts, indent=1))
    unsafe = [r for r in rows if r["class"] in ("UNSAFE",)]
    for r in unsafe[:40]:
        print("UNSAFE %r\n   bash : %r\n   guard: %r" % (r["word"], r["bash"], r["guard"]))
    print("words: %d  UNSAFE: %d  crash: %d  order-differs(exact): %d  slowest: %.4fs" % (len(rows), len(unsafe), sum(1 for r in rows if r["class"] == "crash"), sum(1 for r in rows if r["order_differs"]), slowest[0]["seconds"]))
    return 1 if unsafe else 0


if __name__ == "__main__":
    sys.exit(main())
