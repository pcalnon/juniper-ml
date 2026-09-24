"""Negative control for equiv_proof.py: the bisimulation must FIND a difference when there is one.

A checker that answers EQUIVALENT for every pair proves nothing. Each mutation below changes
the language of the new pattern in a small way; every one must produce a counterexample,
and the counterexample must be confirmed by the real ``re`` engine.
"""

import re
import sys

sys.argv = [sys.argv[0]]
import equiv_proof as E  # noqa: E402  (runs the main proof once on import; that is fine)

NEW = E.NEW_RE.pattern
MUTANTS = {
    "drop W/ in the repeated element": NEW.replace('(?:,[ \\t]*(?:(?:W/)?"', '(?:,[ \\t]*(?:"'),
    "no trailing OWS after the first tag": NEW.replace('"[^"]*"[ \\t]*)?(?:,', '"[^"]*")?(?:,', 1),
    "SP only (no HTAB) in the leading OWS": NEW.replace("[ \\t]*", "[ ]*", 1),
    "tag becomes mandatory in repeated elements": NEW[:-2] + ")*" if False else NEW.replace('"[^"]*"[ \\t]*)?)*', '"[^"]*"[ \\t]*))*'),
    "opaque may contain a quote": NEW.replace('[^"]*', '.*', 1),
}
bad = 0
for name, pat in MUTANTS.items():
    assert pat != NEW, f"mutation did not apply: {name}"
    mut_ast = E.P(pat).parse() if ".*" not in pat else None
    if mut_ast is None:
        # '.' is outside the parser subset; fall back to exhaustive enumeration with the engine
        rx = re.compile(pat)
        import itertools

        witness = None
        for length in range(7):
            for tup in itertools.product(E.REPS, repeat=length):
                s = "".join(tup)
                if (rx.fullmatch(s) is None) != (E.NEW_RE.fullmatch(s) is None):
                    witness = s
                    break
            if witness is not None:
                break
    else:
        seen = {(E.NEW_AST, mut_ast)}
        frontier = [(E.NEW_AST, mut_ast, "")]
        witness = None
        while frontier:
            a, b, w = frontier.pop()
            if E.nullable(a) != E.nullable(b):
                witness = w
                break
            for c in E.REPS:
                pair = (E.deriv(a, c), E.deriv(b, c))
                if pair not in seen:
                    seen.add(pair)
                    frontier.append((pair[0], pair[1], w + c))
    confirmed = witness is not None and (re.compile(pat).fullmatch(witness) is None) != (E.NEW_RE.fullmatch(witness) is None)
    print(f"  mutant [{name}]: counterexample={witness!r} confirmed_by_re={confirmed}")
    bad += not confirmed
print("negative control:", "PASS (every mutant caught)" if bad == 0 else f"FAIL ({bad} mutants not caught)")
sys.exit(1 if bad else 0)
