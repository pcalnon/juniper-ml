"""Lane A1 (round 3, juniper-data#428): is the new _ENTITY_TAG_LIST the SAME LANGUAGE as the old one?

Three independent methods, none of which reuses the fix agent's equivalence script:

1. An exact proof: parse BOTH pattern strings (read from the two module files, not
   transcribed by hand) into a tiny regex AST over the alphabet PARTITION the patterns
   induce, then walk Brzozowski derivatives of the pair to a fixpoint. Equal nullability at
   every reachable pair <=> equal languages. The partition is exact because the only
   character predicates either pattern uses are SP, HTAB, ',', '"', 'W', '/' and [^"]; every
   other character behaves identically (it matches [^"] and nothing else).
2. Exhaustive enumeration over the 7 partition representatives up to length 8 with the real
   ``re`` engine (both compiled patterns, fullmatch), plus the parser cross-check: my AST
   must agree with ``re`` on every one of those strings, or the proof in (1) proves nothing.
3. Random differential fuzzing with LONGER, structure-biased strings, including characters
   outside ASCII, with the real ``re`` engine.
"""

from __future__ import annotations

import importlib.util
import itertools
import random
import sys
import time

SCRATCH = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/data428-laneA1"
NEW_FILE = f"{SCRATCH}/tree-3a76a4c/juniper_data/api/http_cache.py"
OLD_FILE = f"{SCRATCH}/http_cache_3ecb106.py"


def load(path: str, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


NEW = load(NEW_FILE, "hc_new")
OLD = load(OLD_FILE, "hc_old")
NEW_RE = NEW._ENTITY_TAG_LIST
OLD_RE = OLD._ENTITY_TAG_LIST
print("old pattern:", OLD_RE.pattern)
print("new pattern:", NEW_RE.pattern)

# ---- the alphabet partition ------------------------------------------------------------
REPS = [" ", "\t", ",", '"', "W", "/", "x"]  # 'x' stands for EVERY other character
OTHER = "x"


# ---- a tiny regex parser for the subset both patterns use ------------------------------
class P:
    def __init__(self, s: str) -> None:
        self.s, self.i = s, 0

    def peek(self):
        return self.s[self.i] if self.i < len(self.s) else None

    def take(self):
        c = self.s[self.i]
        self.i += 1
        return c

    def parse(self):
        node = self.alt()
        assert self.i == len(self.s), f"trailing input at {self.i}: {self.s[self.i:]!r}"
        return node

    def alt(self):
        branches = [self.seq()]
        while self.peek() == "|":
            self.take()
            branches.append(self.seq())
        return alt(*branches)

    def seq(self):
        items = []
        while self.peek() not in (None, "|", ")"):
            items.append(self.quant())
        node = EPS
        for it in reversed(items):
            node = cat(it, node)
        return node

    def quant(self):
        atom = self.atom()
        while self.peek() in ("?", "*", "+"):
            q = self.take()
            assert self.peek() not in ("?", "+"), "lazy/possessive quantifiers are not in this subset"
            if q == "?":
                atom = alt(atom, EPS)
            elif q == "*":
                atom = star(atom)
            else:
                atom = cat(atom, star(atom))
        return atom

    def atom(self):
        c = self.take()
        if c == "(":
            if self.s.startswith("?:", self.i):
                self.i += 2
            node = self.alt()
            assert self.take() == ")"
            return node
        if c == "[":
            neg = False
            if self.peek() == "^":
                self.take()
                neg = True
            chars = set()
            while self.peek() != "]":
                ch = self.take()
                if ch == "\\":
                    ch = {"t": "\t", "-": "-", "\\": "\\"}[self.take()]
                chars.add(ch)
            self.take()
            for ch in chars:
                assert ch in REPS[:-1] or ch in "-", f"class char {ch!r} outside the partition"
            members = frozenset(r for r in REPS if ((r in chars) != neg) and r != OTHER) | (frozenset([OTHER]) if neg else frozenset())
            return sym(members)
        if c == "\\":
            ch = {"t": "\t"}[self.take()]
            return sym(frozenset([ch]))
        assert c not in ".^$", f"unsupported metachar {c!r}"
        assert c in REPS[:-1], f"literal {c!r} outside the partition"
        return sym(frozenset([c]))


# ---- AST with smart constructors (ACI-normalised alternation) -----------------------------
EMPTY = ("empty",)
EPS = ("eps",)


def sym(s):
    return EMPTY if not s else ("sym", frozenset(s))


def cat(a, b):
    if a == EMPTY or b == EMPTY:
        return EMPTY
    if a == EPS:
        return b
    if b == EPS:
        return a
    if a[0] == "cat":  # right-associate
        return cat(a[1], cat(a[2], b))
    return ("cat", a, b)


def alt(*xs):
    flat = set()
    for x in xs:
        if x == EMPTY:
            continue
        if x[0] == "alt":
            flat |= x[1]
        else:
            flat.add(x)
    if not flat:
        return EMPTY
    if len(flat) == 1:
        return next(iter(flat))
    return ("alt", frozenset(flat))


def star(a):
    if a in (EMPTY, EPS):
        return EPS
    if a[0] == "star":
        return a
    return ("star", a)


def nullable(r) -> bool:
    k = r[0]
    if k == "eps" or k == "star":
        return True
    if k in ("empty", "sym"):
        return False
    if k == "cat":
        return nullable(r[1]) and nullable(r[2])
    if k == "alt":
        return any(nullable(x) for x in r[1])
    raise AssertionError(k)


_DCACHE: dict = {}


def deriv(r, c):
    key = (r, c)
    if key in _DCACHE:
        return _DCACHE[key]
    k = r[0]
    if k in ("empty", "eps"):
        out = EMPTY
    elif k == "sym":
        out = EPS if c in r[1] else EMPTY
    elif k == "cat":
        first = cat(deriv(r[1], c), r[2])
        out = alt(first, deriv(r[2], c)) if nullable(r[1]) else first
    elif k == "alt":
        out = alt(*(deriv(x, c) for x in r[1]))
    elif k == "star":
        out = cat(deriv(r[1], c), r)
    else:
        raise AssertionError(k)
    _DCACHE[key] = out
    return out


def matches(r, s: str) -> bool:
    for ch in s:
        r = deriv(r, ch if ch in REPS[:-1] else OTHER)
        if r == EMPTY:
            return False
    return nullable(r)


OLD_AST = P(OLD_RE.pattern).parse()
NEW_AST = P(NEW_RE.pattern).parse()



def main() -> int:
    # ---- (1) exact proof by derivative bisimulation ------------------------------------------
    t0 = time.perf_counter()
    seen = {(OLD_AST, NEW_AST)}
    frontier = [(OLD_AST, NEW_AST, "")]
    counterexample = None
    while frontier:
        a, b, witness = frontier.pop()
        if nullable(a) != nullable(b):
            counterexample = witness
            break
        for c in REPS:
            pair = (deriv(a, c), deriv(b, c))
            if pair not in seen:
                seen.add(pair)
                frontier.append((pair[0], pair[1], witness + c))
    print(f"(1) derivative bisimulation: {len(seen)} reachable state pairs, {time.perf_counter() - t0:.2f}s,", "EQUIVALENT" if counterexample is None else f"DIFFER on {counterexample!r}")

    # ---- (2) exhaustive enumeration + parser cross-check against the real engine ------------
    t0 = time.perf_counter()
    n = diffs = ast_disagree = accepted = 0
    MAXLEN = 8
    for length in range(MAXLEN + 1):
        for tup in itertools.product(REPS, repeat=length):
            s = "".join(tup)
            o = OLD_RE.fullmatch(s) is not None
            w = NEW_RE.fullmatch(s) is not None
            n += 1
            accepted += w
            if o != w:
                diffs += 1
                if diffs <= 5:
                    print("   DIFF:", repr(s), "old", o, "new", w)
            if length <= 7 and matches(NEW_AST, s) != w:
                ast_disagree += 1
                if ast_disagree <= 5:
                    print("   AST/re disagree:", repr(s))
    print(f"(2) exhaustive over {len(REPS)} reps up to length {MAXLEN}: {n} strings, {accepted} accepted, {diffs} old/new differences, {ast_disagree} AST-vs-re disagreements (len<=7), {time.perf_counter() - t0:.1f}s")

    # ---- (3) random differential fuzzing, longer and structure-biased ----------------------------
    rng = random.Random(20260924)
    PIECES = [" ", "\t", ",", '"', "W", "/", "x", "é", "\x7f", '"abc"', 'W/"a,b"', ", ", " , ", '""', "W/", '"', ",\t", "\t,", "W/W/", '" "', '","']
    t0 = time.perf_counter()
    fz = fdiff = facc = 0
    for _ in range(300_000):
        k = rng.randint(0, 24)
        s = "".join(rng.choice(PIECES) for _ in range(k))
        o = OLD_RE.fullmatch(s) is not None if s.count(",") <= 12 else None  # old form is exponential; keep it tractable
        w = NEW_RE.fullmatch(s) is not None
        if o is None:
            continue
        fz += 1
        facc += w
        if o != w:
            fdiff += 1
            if fdiff <= 5:
                print("   FUZZ DIFF:", repr(s), o, w)
        # the AST must also agree with the engine on these (non-ASCII mapped to OTHER)
        if matches(NEW_AST, s) != w or matches(OLD_AST, s) != o:
            print("   FUZZ AST DISAGREE:", repr(s))
            break
    print(f"(3) random differential: {fz} strings compared ({facc} accepted), {fdiff} differences, {time.perf_counter() - t0:.1f}s")
    return 0 if counterexample is None and diffs == 0 and fdiff == 0 and ast_disagree == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
