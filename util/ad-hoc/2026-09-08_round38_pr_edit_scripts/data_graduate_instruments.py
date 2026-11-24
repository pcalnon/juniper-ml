#!/usr/bin/env python3
"""Graduate lane A3's SEC-shares-cache instruments into juniper-data util/ad-hoc (session scratch).

Copies each script, merges the ad-hoc header into its module docstring (keeping the original
docstring text), and writes a README with the 2026-09-08 headline numbers. No script body is
changed: they already take the output directory as argv[1], block the network by patching
``_sec_get`` to raise, and never write into the real cache.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-08
Status: ad-hoc — one-off (applied once, on 2026-09-08, to the PR worktree named below; the paths inside are that session's)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-data#388 (worktree juniper-data--fix--equities-seq-deployment-defaults-and-incomplete-policy--20260908-0730--03b7548f);
         HANDOFF_2026-09-08_defect-register-round-38-the-three-way-prompt-built-and-the-annotation-made-truthful.md
"""
from __future__ import annotations

import ast
from pathlib import Path

SRC = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/4af5ce60-c37f-4baf-8585-18271a95cc91/scratchpad/laneA3")
W = Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--equities-seq-deployment-defaults-and-incomplete-policy--20260908-0730--03b7548f")
DST = W / "util/ad-hoc/2026-09-08_equities_shares_cache_census"

PURPOSE = {
    "a3lib.py": "Shared helpers: a standalone replica of _fetch_shares's parse/dedup/outlier steps, so every number can be re-derived without the package, plus loaders for the on-disk SEC cache.",
    "census_cache.py": "Census of the cached SEC shares payloads: count, concepts, empties, all-zero payloads, mtimes.",
    "universe_diff.py": "Bundled default universe (503 tickers / 500 CIKs) vs the cached payload set; names the members with no cached payload.",
    "first_filing.py": "Per CIK, the first filing date and the share of a default 2000-01-01..today window that precedes it (raw min-filed and generator-faithful definitions).",
    "final_checks.py": "Re-derives the first-filing coverage under alternative definitions (end-date, business-day) for the sensitivity note.",
    "ko_restatement.py": "Replays the generator's latest-filed-per-period-end dedup on KO (CIK 21344) against a first-publication alternative; the three overstated episodes.",
    "restatement_population.py": "The 8-K restatement effect across every cached CIK (corrections included).",
    "restatement_population_v2.py": "Same, restricted to same-value re-statements (the handoff's mechanism only), business-day calendar.",
    "first_pub_moved.py": "CIKs whose FIRST available count is deferred by the latest-filed dedup (NaN rows where the figure was already public).",
    "outlier_census.py": "The whole-history-median outlier filter (_SHARES_OUTLIER_FACTOR): CIKs losing >=1 point, and the causal-median alternatives.",
    "placeholder_scan.py": "Cached payloads whose deduped series is all-zero or placeholder-valued (silent market_cap 0.0 on a warm cache).",
    "warm_cache_trace.py": "Traces which guards and rescue rungs run on a warm cache hit vs cold, in a SCRATCH cache directory (never the real one).",
}

HEADER = """{purpose}

Project: juniper-data
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-08
Status: ad-hoc — investigation (round-37 defect-register handoff validation, lane A3)
Retire when: the SEC shares cache gains a versioned key / TTL and the restatement + outlier
    findings are closed in the defect register (or the instruments are superseded by a test).
Related: juniper-ml/notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md;
    juniper-ml/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-08_defect-register-round-38-*.md

READ-ONLY on the cache (``~/.cache/juniper_data/equities`` or ``JUNIPER_DATA_EQUITIES_CACHE_DIR``);
the network is blocked (``_sec_get`` is patched to raise) so a missing payload is reported, never
fetched. Output goes to the directory given as the first argument. Run with the JuniperData
interpreter from this directory (the scripts import ``a3lib`` from beside themselves):

    cd util/ad-hoc/2026-09-08_equities_shares_cache_census
    /opt/miniforge3/envs/JuniperData/bin/python {name} /tmp/shares-census-out
"""

README = """# SEC shares-cache census instruments (2026-09-08)

The measurement instruments behind the round-37 handoff validation's SEC-shares-cache findings
(juniper-ml, lane A3 of the 2026-09-08 consensus run). Graduated here from a session scratch
directory because an instrument that lives only in scratch is lost with the session, and every
number below was re-derived by it.

All scripts are **read-only on the cache** and **block the network**; each takes the output
directory as its first argument and imports `a3lib.py` from beside itself. Run with the
JuniperData interpreter from this directory.

| Script | Measures | Headline (2026-09-08, cache of 2026-06-03, main 03b7548f) |
|---|---|---|
| `census_cache.py` | payload count, concepts, empties, all-zero, mtimes | 485 payloads (473 dei + 12 us-gaap), 0 empty, one batch 2026-06-03T01:18-01:58Z |
| `universe_diff.py` | bundled universe vs cached set | 503 tickers / 500 CIKs; 15 members with no payload (EL TSN RL META XYZ ABNB TTD STZ DASH TKO UHS HRL MKC LEN ERIE) |
| `first_filing.py`, `final_checks.py` | share of the default window before the first filing | earliest 2009-04-15, median 2009-12-18; mean 43.1% (raw min-filed) / 43.2% (generator-faithful) as of 2026-09-07; 44.85% universe-wide |
| `ko_restatement.py` | latest-filed dedup vs first publication, KO | 3 episodes, 103 trading days, all OVERSTATED: +0.638% (40 d), +0.450% (44 d), +0.104% (19 d) |
| `restatement_population_v2.py` | the same effect, every CIK | 162/485 CIKs with a re-stated end; 155 with >=1 differing row; 17,569 rows; ADM (default prefix) up to +11.55% |
| `first_pub_moved.py` | first available count deferred by the dedup | 9 CIKs; 8 CIKs / 1,225 business-day rows NaN where the figure was public (EXPE 521) |
| `outlier_census.py` | whole-history-median outlier filter | 61/485 CIKs lose >=1 point (92 points); causal alternatives keep a different set for 15 or 16 |
| `placeholder_scan.py` | all-zero / placeholder series | 6 payloads (TAP, DDOG, CVNA, FOX/FOXA, PSKY, BRK.B-scale) -> silent market_cap 0.0, not NaN |
| `warm_cache_trace.py` | which guards run warm vs cold | warm hit skips the concept loop, its empty-units guard and the rescue ladder; the post-load guard still runs and returns None |

Definitions and instrument caveats are in each script's docstring; the handoff that consumed these
numbers records what the evidence cannot support (no live-endpoint comparison, business-day vs
trading-day calendars for tickers other than KO).
"""


def graduate(name: str) -> None:
    source = (SRC / name).read_text()
    module = ast.parse(source)
    header = HEADER.format(purpose=PURPOSE[name], name=name)
    original = ast.get_docstring(module, clean=False)
    if original is not None and module.body and isinstance(module.body[0], ast.Expr):
        end = module.body[0].end_lineno
        lines = source.splitlines(keepends=True)
        rest = "".join(lines[end:])
        merged = header.rstrip("\n") + "\n\nOriginal notes\n--------------\n" + original.strip("\n") + "\n"
        body = rest
    else:
        merged = header
        body = source
    text = '"""' + merged + '"""\n' + ("\n" if not body.startswith("\n") else "") + body
    (DST / name).write_text(text)
    compile(text, name, "exec")  # syntax must survive the merge
    print(f"graduated {name}")


DST.mkdir(parents=True, exist_ok=True)
for script in PURPOSE:
    graduate(script)
(DST / "README.md").write_text(README)
print("README written; ", len(PURPOSE), "scripts")
