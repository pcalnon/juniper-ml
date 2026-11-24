#!/usr/bin/env python3
"""Round-38 juniper-data PR: finish the executor's work (comments, CHANGELOG) -- exact-match edits.

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

import sys
from pathlib import Path

W = Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--equities-seq-deployment-defaults-and-incomplete-policy--20260908-0730--03b7548f")
GEN = W / "juniper_data/generators/equities/generator.py"
PARAMS = W / "juniper_data/generators/equities/params.py"
CHANGELOG = W / "CHANGELOG.md"


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL {path.name}: expected exactly 1 match, found {n} for:\n---\n{old[:300]}\n---")
    path.write_text(text.replace(old, new))
    print(f"edited {path.relative_to(W)}: {old.splitlines()[0][:70]!r}")


# The executor cited a PR number that does not exist yet.
replace_once(
    GEN,
    "        # Classify, refuse or prune, and build the annotation -- BEFORE assembling\n"
    "        # anything. Shared with ``equities_seq``, which reuses this whole pipeline\n"
    "        # and went a release without the policy at all (juniper-data#385).\n",
    "        # Classify, refuse or prune, and build the annotation -- BEFORE assembling\n"
    "        # anything. Shared with ``equities_seq``, which reuses this whole pipeline\n"
    "        # and went a release without the policy at all (found by the round-38\n"
    "        # handoff validation in juniper-ml, 2026-09-08).\n",
)

# Stale column counts: reference the constant instead of restating a number.
replace_once(
    GEN,
    '        """Stack the ordered feature columns into a float32 (n, 10) matrix."""\n',
    '        """Stack the ordered feature columns into a float32 ``(n, len(EQUITIES_FEATURE_COLUMNS))`` matrix."""\n',
)
replace_once(
    PARAMS,
    "    NPZ contract: a 10-column numeric feature matrix, a one-hot next-day\n",
    "    NPZ contract: a numeric feature matrix with one column per entry of\n"
    "    ``EQUITIES_FEATURE_COLUMNS`` (``defaults.py``; 16 as of generator 3.0.0), a one-hot next-day\n",
)

# CHANGELOG: the withdrawn precision, and the two new Fixed entries.
replace_once(
    CHANGELOG,
    "  Measured on `LocalFSDatasetStore` after the fix: **114.8× at 100 datasets** (18.87 → 0.16 ms) and\n"
    "  **92.9× at 1,000** (157.16 → 1.69 ms).\n",
    "  Measured on `LocalFSDatasetStore` after the fix: of order **100×** at both 100 and 1,000 datasets.\n"
    "  The exact ratio is instrument- and machine-specific — independent re-measurements on 2026-09-08\n"
    "  ranged 96–180× at N=100 — so only the order is quotable; the four-significant-figure values an\n"
    "  earlier version of this entry carried were not reproducible and are withdrawn.\n",
)
replace_once(
    CHANGELOG,
    "## [Unreleased]\n\n### Fixed\n\n- **The JD-PERF-02 metadata cache was inert in production, and its test suite could not see that.**\n",
    "## [Unreleased]\n\n### Fixed\n\n"
    "- **`equities_seq` now binds the deployment policy before hashing, so its `dataset_id` follows the\n"
    "  policy it actually runs under.** `bind_deployment_defaults` existed only on `EquitiesGenerator`,\n"
    "  and the create route finds the binder by `getattr` — so for `equities_seq` nothing was bound while\n"
    "  its `generate` still applied the same symbol cap and the same `allow_truncation` OR through\n"
    "  `EquitiesGenerator._resolve_symbols`. `generate_dataset_id` therefore hashed the **schema**\n"
    "  defaults (`max_symbols` unclamped, `allow_truncation=false`) rather than the effective values.\n"
    "  Proven by execution on 2026-09-08: two `equities_seq` requests, identical but for\n"
    "  `JUNIPER_DATA_EQUITIES_ALLOW_TRUNCATION` off vs on, hashed to the **same** id, so toggling the\n"
    "  deployment opt-in kept serving the artifact built under the old policy; `equities` gave two ids\n"
    "  for the same pair. The sequence generator now delegates to the flat generator's binder\n"
    "  (`EquitiesSeqParams` subclasses `EquitiesParams`; `model_copy` keeps the concrete class).\n"
    "\n"
    "  **Deliberate consequence: every `equities_seq` `dataset_id` changes once.** `max_symbols=None`\n"
    "  now hashes as the bound cap and `allow_truncation` as the effective value, so the first request\n"
    "  after this ships regenerates. That one-time cache turnover is the point — the old ids were\n"
    "  computed from a policy the generator did not run under.\n"
    "\n"
    "- **`equities_seq` now applies the fail / accept / drop contract to rows no rescue path could\n"
    "  recover.** The sequence generator reuses the flat generator's universe resolution, conditioning\n"
    "  and normalisation, but had no copy of the incomplete-data block: an unrescued ticker shipped\n"
    "  there with NaN (or, under `fundamentals_fill=\"zero\"`, `0.0`) `total_shares` / `market_cap` —\n"
    "  no refusal, no `data_quality` annotation, whatever `allow_truncation` said — while the identical\n"
    "  request to `equities` was refused with 422. The classify / resolve / fail-or-drop / annotate block\n"
    "  is extracted into one shared helper, `EquitiesGenerator._apply_incomplete_policy`, called by both\n"
    "  generators (for the sequence generator: after conditioning and **before** the normaliser fit and\n"
    "  the windowing, so a dropped ticker reaches neither). The flat generator's behaviour is unchanged\n"
    "  and its existing tests pin it. Pinned for the sequence generator by\n"
    "  `test_equities_seq_deployment_policy.py` (default refusal, accept annotates, drop removes the\n"
    "  ticker from every window and still annotates, drop-that-empties still fails, clean carries no\n"
    "  annotation).\n"
    "\n"
    "  Both found by the round-38 handoff validation in juniper-ml (2026-09-08). Also in this change:\n"
    "  three stale comments corrected in `equities/generator.py` and `params.py` (the KO / ABT\n"
    "  \"no shares concept\" example — the on-disk cache holds 71 and 68 dei facts for them; the\n"
    "  circular-import paragraph, obsolete since juniper-data#333; and two \"10-column\" feature counts\n"
    "  that now reference `EQUITIES_FEATURE_COLUMNS`), and the measurement instruments behind the\n"
    "  round-37 validation's SEC-shares-cache findings graduated from a session scratch directory into\n"
    "  `util/ad-hoc/2026-09-08_equities_shares_cache_census/` (read-only on the cache, network blocked).\n"
    "\n"
    "- **The JD-PERF-02 metadata cache was inert in production, and its test suite could not see that.**\n",
)
print("ALL DATA EDITS APPLIED")
