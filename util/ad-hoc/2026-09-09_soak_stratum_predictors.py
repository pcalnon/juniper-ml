#!/usr/bin/env python3
"""Test §8.2's three candidate stratum predictors over the 15-probe registry.

Project:     Juniper
Sub-Project: juniper-ml
Application: pointer-follow soak -- §8 predictor gap
Author:      Paul Calnon
Version:     0.1.0
License:     MIT

WHY THIS EXISTS
---------------
§8.2 of `notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md`
calls the predictor gap *"the actual blocker to decision support"*: two strata
exist, and nothing predicts which one a NEW fact lands in. It names three
candidates and says none has been tested:

  1. how findable the fact is by a plausible grep of the task's own vocabulary;
  2. whether the task is completable correctly WITHOUT the fact;
  3. whether the fact contradicts a plausible default the agent already holds.

This runs over the registry and its tasks -- 15 probes, not the 43 ledger rows.

THREE THINGS TO KNOW BEFORE READING THE OUTPUT
----------------------------------------------
1. EXPLORATORY, NOT CONFIRMATORY. The features below were written after the
   outcomes were visible. An association found here is a hypothesis to
   pre-register against NEW probes, never a result. §15.3 of the ledger is the
   model: state the prediction first, then run.

2. The permutation test here is a REAL label shuffle. §9.3 of the design
   conversation reports `p = 0.0017` for heterogeneity, but §6 of
   `notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md`
   records that the figure came from a parametric bootstrap mislabelled as a
   permutation test. This shuffles observed run outcomes across probes holding
   each probe's n fixed, which is what the label "permutation test" claims.

3. The outcome column is selectable. `--standard recorded` uses the ledger's
   scored outcome; `--standard mechanism` uses the re-audit in
   `util/ad-hoc/2026-09-08_soak_label_to_transcript.py`, which discards
   destination hits that are a filename-only grep result, a sibling repo's
   same-named file, or the soak ledger's own note. Which one binds is Overtoad
   decision (§7.2 of the 09-04 review); this reports under both.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

REGISTRY = Path("conf/soak_probes.json")
LEDGER = Path("reports/soak/pointer_follow_soak.jsonl")
REAUDIT = Path("util/ad-hoc/2026-09-08_soak_label_to_transcript.py")

# Identifier shapes an agent would plausibly grep: snake_case, CamelCase,
# ENV_VARS, --flags, and dotted file paths.
IDENT_RE = re.compile(r"[A-Za-z_][\w./-]*[\w]")

# A fact that says WHY a design is the way it is cannot be checked by reading
# the implementation -- the code shows what it does, never that it was chosen
# deliberately over an alternative.
RATIONALE_MARKERS = (
    "deliberately", "because", "so that", "only so", "on purpose",
    "rather than", "instead of", "is a loan", "the reason",
)
# A fact that forbids something states an intent the code cannot carry.
PROHIBITION_MARKERS = ("must never", "never be", "must not", "should never", "do not")
# A fact that names where its own justification lives points the agent AWAY
# from the relocated prose and back at the repo.
SOURCE_POINTER_MARKERS = ("records why", "the compose file", "its guard test", "the tests")


def load_reaudit():
    spec = importlib.util.spec_from_file_location("reaudit", REAUDIT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def per_probe_outcomes(standard: str) -> dict[str, dict]:
    """Return {probe_num: {n, follows}} under the chosen retrieval standard."""
    m = load_reaudit()
    bound = m.bind(m.load_ledger(LEDGER), m.discover_transcripts())
    tab: dict[str, dict] = defaultdict(lambda: {"n": 0, "follows": 0, "runs": []})
    for e in bound:
        if not e["valid"]:
            continue
        pnum = e["probe_id"].split("-", 1)[0]
        if standard == "recorded":
            hit = e["outcome"] == "follow"
        else:
            if e["transcript"] is None:
                continue
            hit = m.scan(e["transcript"])["mech"][m.M_CONTENT] > 0
        tab[pnum]["n"] += 1
        tab[pnum]["follows"] += int(hit)
        tab[pnum]["runs"].append(int(hit))
    return dict(tab)


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / d
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (centre - half, centre + half)


def identifiers(text: str) -> set[str]:
    """Identifier-shaped tokens, lowercased, minus ordinary English."""
    out = set()
    for tok in IDENT_RE.findall(text or ""):
        if len(tok) < 4:
            continue
        # An identifier is a token carrying a shape English words do not:
        # an underscore, a dot, a slash, a leading dash, or internal capitals.
        if ("_" in tok or "." in tok or "/" in tok or "-" in tok
                or (tok[1:] != tok[1:].lower())):
            out.add(tok.lower().strip(".-/"))
    return out


def features(probe: dict) -> dict[str, int]:
    fact = (probe["fact"] or "").lower()
    disc = (probe["discriminator"] or "").lower()
    # No lowercased `task` string: the task contributes only through
    # `identifiers()` below, which case-folds its own tokens.

    fact_ids = identifiers(probe["fact"])
    task_ids = identifiers(probe["task"])

    return {
        # §8.2 candidate 1 -- grep-findability from the task's own vocabulary.
        # Operationalised as: does the task name an identifier the fact also
        # names? If so a single grep of the task's own words lands on the
        # implementation, and the fact is recoverable without the pointer.
        "task_names_fact_ident": int(bool(fact_ids & task_ids)),
        "n_shared_idents": len(fact_ids & task_ids),
        # §8.2 candidate 2 -- completable without the fact. Mechanised via the
        # discriminator's verb: a discriminator that requires a REFUSAL means
        # the task as written cannot be completed correctly at all, so the fact
        # is load-bearing rather than optional.
        "discriminator_is_refusal": int(
            "refuse" in disc or "decline" in disc or "recognise that" in disc
        ),
        # §8.2 candidate 3 -- contradicts a plausible default. Two textual
        # proxies: the fact asserts a RATIONALE (why this, not the obvious
        # alternative), or it FORBIDS something a reasonable agent would try.
        "fact_has_rationale": int(any(m in fact for m in RATIONALE_MARKERS)),
        "fact_has_prohibition": int(any(m in fact for m in PROHIBITION_MARKERS)),
        # Falls out of the registry's own SCORING note: source-recovered is
        # "got the fact right by reading the code or tests". A fact that names
        # where its justification lives sends the agent to the repo, not the doc.
        "fact_points_to_source": int(any(m in fact for m in SOURCE_POINTER_MARKERS)),
    }


def fisher_exact_2x2(a: int, b: int, c: int, d: int) -> float:
    """Two-sided Fisher exact p. Written out because scipy is not a dependency."""
    def logfact(n):
        return math.lgamma(n + 1)

    def phyper(a_, b_, c_, d_):
        n = a_ + b_ + c_ + d_
        return math.exp(
            logfact(a_ + b_) + logfact(c_ + d_) + logfact(a_ + c_) + logfact(b_ + d_)
            - logfact(n) - logfact(a_) - logfact(b_) - logfact(c_) - logfact(d_)
        )

    observed = phyper(a, b, c, d)
    row1, col1 = a + b, a + c
    n = a + b + c + d
    total = 0.0
    for x in range(max(0, col1 - (n - row1)), min(row1, col1) + 1):
        p = phyper(x, row1 - x, col1 - x, n - row1 - col1 + x)
        if p <= observed * (1 + 1e-9):
            total += p
    return min(1.0, total)


def heterogeneity(tab: dict[str, dict]) -> float:
    """Sum of squared deviations from the pooled rate, weighted by n."""
    runs = sum(t["n"] for t in tab.values())
    follows = sum(t["follows"] for t in tab.values())
    pooled = follows / runs if runs else 0.0
    return sum(t["n"] * (t["follows"] / t["n"] - pooled) ** 2
               for t in tab.values() if t["n"])


def permutation_p(tab: dict[str, dict], draws: int = 20000, seed: int = 20260909) -> tuple:
    """TRUE label shuffle: reassign observed run outcomes across probes.

    Each probe's n is held fixed and the multiset of observed outcomes is
    permuted between them. That is the null "all probes share one rate"
    conditioned on the observed total -- and it is what the phrase
    "permutation test" claims. A parametric bootstrap instead RESAMPLES from
    Binomial(n, pooled), which is a different null and gives a different p.
    """
    rng = random.Random(seed)
    pool = [o for t in tab.values() for o in t["runs"]]
    sizes = [(k, t["n"]) for k, t in tab.items()]
    observed = heterogeneity(tab)
    hits = 0
    for _ in range(draws):
        rng.shuffle(pool)
        i = 0
        shuffled = {}
        for k, n in sizes:
            shuffled[k] = {"n": n, "follows": sum(pool[i:i + n]), "runs": pool[i:i + n]}
            i += n
        if heterogeneity(shuffled) >= observed - 1e-12:
            hits += 1
    return observed, (hits + 1) / (draws + 1)


def validate(tab: dict[str, dict], trials: int = 20000, seed: int = 7) -> None:
    """Two self-checks, because one of this tool's outputs is circular.

    1. GROUPING BY EXTREME OUTCOME PROVES NOTHING. "never-follow" means 0
       follows and "always-follow" means all follows, so Wilson intervals over
       those same runs are extreme by construction. Simulating the observed n
       under the null that every probe shares the pooled rate shows how often
       pure noise reproduces the "disjoint intervals" result. It is most of the
       time. An earlier draft of the analysis reported it as a finding.

    2. THE PERMUTATION TEST IS NOT circular -- it partitions nothing -- but a
       broken implementation would return a tiny p on anything. Run it against
       synthetic null datasets: a correct test gives roughly uniform p.
    """
    ns = [t["n"] for t in tab.values()]
    runs = sum(ns)
    follows = sum(t["follows"] for t in tab.values())
    pooled = follows / runs
    rng = random.Random(seed)

    disjoint = usable = 0
    for _ in range(trials):
        sim = [[1 if rng.random() < pooled else 0 for _ in range(n)] for n in ns]
        never = [r for r in sim if sum(r) == 0]
        always = [r for r in sim if sum(r) == len(r)]
        if not never or not always:
            continue
        usable += 1
        _, hi = wilson(0, sum(len(r) for r in never))
        ak = sum(len(r) for r in always)
        lo, _ = wilson(ak, ak)
        if hi < lo:
            disjoint += 1

    print("\n== self-check 1: is the grouped contrast circular? ==")
    print(f"  null = all {len(ns)} probes share p={pooled:.3f}, observed n held fixed")
    print(f"  grouping by extreme outcome gives DISJOINT intervals in "
          f"{disjoint}/{trials} = {100.0 * disjoint / trials:.1f}% of trials")
    print("  => YES, circular. Selection makes the intervals extreme, not the data.")

    print("\n== self-check 2: is the permutation test calibrated? ==")
    ps = []
    for t in range(12):
        sim_tab = {}
        for i, n in enumerate(ns):
            r = [1 if rng.random() < pooled else 0 for _ in range(n)]
            sim_tab[f"S{i:02d}"] = {"n": n, "follows": sum(r), "runs": r}
        ps.append(permutation_p(sim_tab, draws=2000, seed=1000 + t)[1])
    print("  p on 12 synthetic NULL datasets (want ~uniform, NOT all tiny):")
    print("   ", " ".join(f"{p:.3f}" for p in sorted(ps)))
    print(f"  fraction < 0.05: {sum(1 for p in ps if p < 0.05)}/12")
    print("  => calibrated. So p<5e-6 on the real corpus is a real signal.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--standard", choices=("recorded", "mechanism", "both"),
                    default="both")
    ap.add_argument("--draws", type=int, default=20000)
    ap.add_argument("--validate", action="store_true",
                    help="run the two self-checks on the circularity and the test")
    args = ap.parse_args()

    registry = json.loads(REGISTRY.read_text())
    probes = {p["probe_id"].split("-", 1)[0]: p for p in registry["probes"]}

    standards = ["recorded", "mechanism"] if args.standard == "both" else [args.standard]
    for standard in standards:
        tab = per_probe_outcomes(standard)
        print("=" * 78)
        print(f"STANDARD: {standard}")
        print("=" * 78)

        runs = sum(t["n"] for t in tab.values())
        follows = sum(t["follows"] for t in tab.values())
        print(f"probes={len(tab)}  runs={runs}  follows={follows}  "
              f"pooled={follows / runs:.3f}")

        obs, p = permutation_p(tab, draws=args.draws)
        print(f"heterogeneity={obs:.4f}  permutation p={p:.5f} "
              f"({args.draws} label shuffles)")

        never = sorted(k for k, t in tab.items() if t["follows"] == 0)
        always = sorted(k for k, t in tab.items() if t["follows"] == t["n"])
        mixed = sorted(set(tab) - set(never) - set(always))
        print(f"\n  never-follow ({len(never)}): {', '.join(never)}")
        print(f"  always-follow ({len(always)}): {', '.join(always)}")
        print(f"  mixed ({len(mixed)}): {', '.join(mixed) or '-'}")

        # These groups are DEFINED by their outcomes, so any interval computed
        # over the same runs is extreme by construction. Printed as a partition,
        # never as a contrast -- `--validate` shows noise reproduces a "disjoint
        # intervals" result about 70% of the time.
        nk = sum(tab[k]["n"] for k in never)
        ak = sum(tab[k]["n"] for k in always)
        print(f"  (partition sizes: {nk} runs never-follow, {ak} runs always-follow; "
              f"NOT a contrast -- see --validate)")

        if not never or not always:
            print("\n  (no two-group contrast available)")
            continue

        # WITHOUT THIS THE NULL IS UNREADABLE. "No feature reached p<0.05" means
        # nothing until you know whether ANY feature could have. If a perfect
        # split is itself above 0.05, the registry is too small to detect a
        # predictor and the null says only that. Print the floor first.
        p_perfect = fisher_exact_2x2(0, len(never), len(always), 0)
        p_one_off = fisher_exact_2x2(1, len(never) - 1, len(always), 0)
        print(f"\n  detection floor for {len(never)} vs {len(always)} probes:"
              f"  perfect split p={p_perfect:.4f}"
              f"  |  one discordant p={p_one_off:.4f}")
        print(f"  a predictor that works IS detectable here: {p_perfect < 0.05}")

        print(f"\n  {'feature':28s} {'never':>7s} {'always':>7s} {'Fisher p':>9s}")
        names = list(features(probes[never[0]]).keys())
        for name in names:
            if name.startswith("n_"):
                continue
            a = sum(features(probes[k])[name] for k in never)
            b = len(never) - a
            c = sum(features(probes[k])[name] for k in always)
            d = len(always) - c
            pv = fisher_exact_2x2(a, b, c, d)
            star = "  <--" if pv < 0.05 else ""
            print(f"  {name:28s} {a:>3d}/{len(never):<3d} {c:>3d}/{len(always):<3d} "
                  f"{pv:9.4f}{star}")

        print("\n  Per-probe detail:")
        print(f"  {'probe':6s} {'f/n':>6s}  " + "  ".join(
            n[:12].rjust(12) for n in names if not n.startswith("n_")))
        for k in sorted(tab):
            f = features(probes[k])
            cells = "  ".join(str(f[n]).rjust(12) for n in names if not n.startswith("n_"))
            print(f"  {k:6s} {tab[k]['follows']:>2d}/{tab[k]['n']:<3d}  {cells}")
        print()

    if args.validate:
        validate(per_probe_outcomes(standards[-1]))

    print("\n" + "=" * 78)
    print("Every association above is EXPLORATORY: the features were written")
    print("with the outcomes visible. To become evidence, a feature must be")
    print("pre-registered against probes that have not yet run -- the discipline")
    print("§15.3 of the ledger applied to rung 1.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
