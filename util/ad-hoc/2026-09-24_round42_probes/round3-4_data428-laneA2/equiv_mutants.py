"""Mutation-check the shipped equivalence script: feed it language-changing mutants of NEW.

A check that reports 0 mismatches for every mutant has no power. The script is loaded from the
tree by path, its NEW / EXPECTED_NEW swapped for each mutant, and its own sweep counted.
"""

import importlib.util
import itertools
import re
import sys
from pathlib import Path

tree = Path(sys.argv[1])
path = tree / "util/ad-hoc/2026-09-23_verify_entity_tag_list_regex_equivalence.py"
spec = importlib.util.spec_from_file_location("equiv_under_test", path)
mod = importlib.util.module_from_spec(spec)
sys.modules["equiv_under_test"] = mod
spec.loader.exec_module(mod)
print("NEW imported from:", sys.modules["juniper_data.api.http_cache"].__file__)

T = r'(?:W/)?"[^"]*"'
MUTANTS = {
    "no OWS after the FIRST tag": r'[ \t]*(?:' + T + r')?(?:,[ \t]*(?:' + T + r'[ \t]*)?)*',
    "no empty element after a comma": r'[ \t]*(?:' + T + r'[ \t]*)?(?:,[ \t]*' + T + r'[ \t]*)*',
    "opaque may not contain a comma": r'[ \t]*(?:(?:W/)?"[^",]*"[ \t]*)?(?:,[ \t]*(?:(?:W/)?"[^",]*"[ \t]*)?)*',
    "at most 5 list elements after the first": r'[ \t]*(?:' + T + r'[ \t]*)?(?:,[ \t]*(?:' + T + r'[ \t]*)?){0,5}',
    "at most 7 list elements after the first": r'[ \t]*(?:' + T + r'[ \t]*)?(?:,[ \t]*(?:' + T + r'[ \t]*)?){0,7}',
    "opaque of at most 6 chars": r'[ \t]*(?:(?:W/)?"[^"]{0,6}"[ \t]*)?(?:,[ \t]*(?:(?:W/)?"[^"]{0,6}"[ \t]*)?)*',
    "HTAB not OWS": r'[ ]*(?:' + T + r'[ ]*)?(?:,[ ]*(?:' + T + r'[ ]*)?)*',
}


def sweep(new: re.Pattern) -> tuple[int, int, list[str]]:
    """The script's own two sweeps, counting mismatches between OLD and ``new``."""
    ex_mis = rnd_mis = 0
    examples: list[str] = []
    for length in range(mod.EXHAUSTIVE_MAX_LEN + 1):
        for chars in itertools.product(mod.ALPHABET, repeat=length):
            text = "".join(chars)
            if (mod.OLD.fullmatch(text) is None) != (new.fullmatch(text) is None):
                ex_mis += 1
                if len(examples) < 2:
                    examples.append(text)
    import random

    rng = random.Random(20260923)
    for _ in range(mod.RANDOM_CASES):
        text = "".join(rng.choice(mod.TOKENS) for _ in range(rng.randint(0, mod.RANDOM_MAX_TOKENS)))
        if (mod.OLD.fullmatch(text) is None) != (new.fullmatch(text) is None):
            rnd_mis += 1
            if len(examples) < 3:
                examples.append(text)
    return ex_mis, rnd_mis, examples


for label, pattern in MUTANTS.items():
    ex_mis, rnd_mis, examples = sweep(re.compile(pattern))
    print(f"{label:45s} exhaustive_mismatches={ex_mis:7d} random_mismatches={rnd_mis:6d} e.g. {examples[:2]!r}")

# And the script's own main() with a mutant swapped in: does it exit 1?
mod.NEW = re.compile(MUTANTS["no OWS after the FIRST tag"])
mod.EXPECTED_NEW = mod.NEW.pattern
print("main() exit with a mutant NEW:", mod.main())
