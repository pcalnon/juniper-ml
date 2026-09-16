#!/usr/bin/env python3
"""Apply round-2 lanes A and B1's findings to the round-39 handoff.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-15
Status: ad-hoc -- one-off
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: reports/2026-09-15_round-39-consensus/;
         juniper-data#404 (merged 2026-09-16T02:08:43Z, squash 1bbb6976)

The largest change here is 5.2. Lane B1 refuted the design the previous revision of this document
described: judging each point against the median of the values already ACCEPTED is ABSORBING, and
juniper-data#404 was amended before merge to use the LOWER MEDIAN of prior SEEN values instead.
The trap has to describe what shipped, and -- more usefully -- why two plausible bases are both
wrong in opposite directions.
"""

from __future__ import annotations

import sys
from pathlib import Path

HANDOFF = (
    Path(__file__).resolve().parents[2]
    / "prompts/thread-handoff_automated-prompts"
    / "HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md"
)
REG = "`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`"

text = HANDOFF.read_text()


def sub(old: str, new: str, label: str) -> None:
    global text
    if new in text and old not in text:
        print(f"  --  {label} (already applied)")
        return
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL [{label}]: found {n} occurrences of:\n{old[:200]}")
    text = text.replace(old, new, 1)
    print(f"  ok  {label}")


# ---------------------------------------------------------------- §2: the merge is real now
sub(
    "| **juniper-data#404** | MERGED | The regression #395 shipped: a first- or second-filing scale typo survived the causal median. `generator_version` 5.0.0 |",
    "| **juniper-data#404** | MERGED 2026-09-16T02:08:43Z, squash `1bbb6976` | The regression #395 shipped: a first- or second-filing scale typo survived the causal median. `generator_version` 5.0.0. **Amended twice before merge, both times by validation** — see §4 and §5.2 |",
    "§2: #404 merge commit and the amendments",
)
sub(
    "juniper_data/tests/unit/test_equities_generator.py`,\n"
    "`juniper_data/tests/unit/test_equities_seq_generator.py`,\n"
    "`juniper_data/tests/unit/test_val_emission_guards.py`, `CHANGELOG.md`,",
    "juniper_data/tests/unit/test_equities_generator.py`,\n"
    "`juniper_data/tests/unit/test_val_emission_guards.py`, `CHANGELOG.md`,",
    "§2: drop test_equities_seq_generator.py, which neither PR touched",
)
sub(
    "`util/ad-hoc/2026-09-15_equities_changelog_entry.py`.",
    "`util/ad-hoc/2026-09-15_equities_changelog_entry.py`,\n"
    "`util/ad-hoc/2026-09-15_equities_fix_ceiling_rationale_numbers.py`,\n"
    "`util/ad-hoc/2026-09-15_equities_fix_absorbing_basis.py`,\n"
    "`util/ad-hoc/2026-09-15_equities_changelog_absorbing_basis.py`,\n"
    "`util/ad-hoc/2026-09-15_compare_outlier_basis_designs.py`,\n"
    "`util/ad-hoc/2026-09-15_verify_lower_median_over_cache.py`.",
    "§2: add the five round-2 juniper-data scripts",
)

# ---------------------------------------------------------------- §0.5/0.6: the ceiling's real siting
sub(
    "**The subject moved on 2026-09-15 and the stakes rose.** The row was filed against `1e13`, a number\n"
    "chosen for headroom above the largest genuine count. juniper-data#404 re-sited it to **`1e11`**,\n"
    "between the largest genuine count in the bundled universe (AAPL, 1.70e10) and the smallest\n"
    "demonstrated typo in the cache (AIZ, 1.168e11). At `1e13` the bound was nearly inert — 18\n"
    "observations across 24 series sat in the dead band above `1e11` — and that inertness is why a typo\n"
    "went out the door (§4). At `1e11` it is the **only** instrument that can reach a scale error in a\n"
    "series' *first* filing, because nothing relative has a prior to judge that point against. Removing\n"
    "it now re-opens that hole outright. What #404 did was put the bound in ratifiable form: sited\n"
    "against the data rather than against comfort. The decision is still owed.",
    "**The subject moved on 2026-09-15 and the stakes rose.** The row was filed against `1e13`, a\n"
    "number chosen for headroom above the largest genuine count. juniper-data#404 re-sited it to\n"
    "**`1e11`**, between the largest genuine count in the cache (**Citigroup, 2.92e10**; NVIDIA second\n"
    "at 2.45e10) and the smallest demonstrated typo in it (AIZ, 1.168e11) — **3.4× of headroom**. At\n"
    "`1e13` the bound was nearly inert: 18 observations across 9 series sit in `(1e11, 1e13]`, and that\n"
    "inertness is why a typo went out the door (§4).\n"
    "\n"
    "**Two figures in the first draft of this section were wrong, and the owner would have been\n"
    "ratifying against them.** It said the bound sits above \"the largest genuine count in the bundled\n"
    "universe (AAPL, 1.70e10)\" with 5.9× of headroom — AAPL is the largest in the **default 14-symbol\n"
    "prefix**, not the universe — and it said \"18 observations across 24 series\", conflating two\n"
    "bands: 18 observations across 9 series in `(1e11, 1e13]`, 39 across 24 above `1e11`.\n"
    "\n"
    "**And the decision is narrower than \"is 1e11 right\".** The four largest values that PASS this\n"
    "ceiling are themselves typos — Pentair 9.84e10 (592× its own median), Packaging Corp 8.99e10\n"
    "(949×), Regency Centers 8.19e10 (483×), Mid-America 7.50e10 (659×) — and the relative filter\n"
    "catches every one, delivering all four correctly. So the ceiling cannot be tightened to reach\n"
    "them without crossing Citigroup's genuine 2.92e10 and deleting real mega-cap history: **the two\n"
    "populations overlap across any absolute bound.** The ceiling's job is not scale errors in\n"
    "general but the one case nothing relative can reach — a typo in a series' *first* filing.\n"
    "Removing it re-opens that hole outright. What #404 did was put the bound in ratifiable form,\n"
    "sited against the data rather than against comfort. The decision is still owed.",
    "§0.6: correct the siting figures and state the real choice",
)

# ---------------------------------------------------------------- §0.2: C-A's three states, and the C-A/C-B collision
sub(
    "Independent of everything above and of each other.\n",
    "Independent of everything above. **NOT independent of each other** — C-A adds a `timeout`\n"
    "parameter to public method signatures and C-B changes the return annotation of many of the same\n"
    "methods: **38 identical `def` lines in the same two files** (12 of 20 public methods in\n"
    "`juniper_data_client/client.py`, 26 of 30 in `juniper_cascor_client/client.py`). Run them in\n"
    "sequence or expect a conflict on nearly every line either touches. The first draft of this\n"
    "document said they were independent.\n",
    "§0.2: C-A and C-B collide",
)
sub(
    "  juniper-recurrence-client already has the whole thing — per-call override at\n"
    "  `client.py:265-269`, including reporting the *effective* timeout in the error — under\n"
    "  `APD-RCLIENT-002`, which is closed. Read that one first; it is the reference implementation.",
    "  juniper-recurrence-client is **2 of 9, not complete** — `train` and `crossval` expose a\n"
    "  per-call timeout; `predict`, `training_status`, `crossval_status`, `get_model`, `get_dataset`,\n"
    "  `health_check` and `is_ready` do not, and since **no** method takes `**kwargs` the transport's\n"
    "  `setdefault` at `client.py:265` is unreachable from seven of the nine. What it does have is the\n"
    "  right *shape* for the two it implements, including reporting the **effective** timeout rather\n"
    "  than `self.timeout` in the error (`client.py:266-269`) — read that before writing the other\n"
    "  seven. The `APD-RCLIENT-002` close says plainly that the other public calls stay on the\n"
    "  client-wide scalar; an earlier draft of this document and the `APD-ECO-003` ruling text in "
    + REG
    + " both lost that qualifier, and the ruling text is corrected.",
    "§0.2: C-A recurrence-client is 2 of 9",
)

# ---------------------------------------------------------------- §0.3: X-A / X-B collision
sub(
    "- **X-B · `APD-CASCOR-013`**, clear `_dataset_shortfall` at the **start of every run**.",
    "- **X-B · `APD-CASCOR-013`**, clear `_dataset_shortfall` at the **start of every run**\n"
    "  (`juniper-cascor/src/api/lifecycle/manager.py` — init at `:1243`, the write in\n"
    "  `_reload_dataset` at `:4175`, the read in `get_status`). **Collides with X-A**, which edits the\n"
    "  truncatable-set membership test in the same file around `:3876`. Sequence the two.",
    "§0.3: X-A / X-B collide in manager.py",
)

# ---------------------------------------------------------------- D-A's doc list
sub(
    "   the `\"A client cannot opt out of the operator's choice\"` docstring in\n"
    "   `juniper_data/generators/equities/generator.py`, the three `or settings.*` sites",
    "   the `\"A client cannot opt out of the operator's choice\"` docstring in\n"
    "   `juniper_data/generators/equities/generator.py` **and the same documented asymmetry in\n"
    "   `juniper_data/generators/csv_import/generator.py` at `:133` and `:145`** (\"there the\n"
    "   operator's choice cannot be undone\") — the first draft named only the equities one — the\n"
    "   three `or settings.*` sites",
    "D-A: the csv_import docstrings carry the same asymmetry",
)

# ---------------------------------------------------------------- §4: the absorbing regression row
sub(
    "| juniper-data#395 fixed the share-count outlier filter | **It shipped a REGRESSION, and delivered it** |",
    "| **This session's own fix, as first written, had a WORSE failure than the one it repaired** | **Refuted by round-2 validation, before merge** | Judging each point against the median of the values already ACCEPTED is **absorbing**: if a series' first value is a typo the ceiling cannot reach, the accepted set is that typo alone, every genuine value is >100× away, and nothing is ever accepted again — the whole real series is deleted and the typo is what ships. Measured on a real payload shape: **0 of 20 genuine counts survived**. The shipped basis is now the **lower median of prior SEEN values**; see §5.2. |\n"
    "| juniper-data#395 fixed the share-count outlier filter | **It shipped a REGRESSION, and delivered it** |",
    "§4: add the absorbing-basis row",
)

# ---------------------------------------------------------------- §5.2: rewrite for what shipped
sub(
    "- **`.shift(1)` is the tempting one-liner and is also wrong.** It excludes the point from its own\n"
    "  basis but still lets a *rejected* value into the basis for the next one: a genuine `1.0e8`\n"
    "  followed by a `5.0e10` typo gives the third point a basis of `median(1e8, 5e10) = 2.55e10`, and\n"
    "  the genuine third filing is deleted as a hundredfold-low outlier. The basis must be the median of\n"
    "  what was **accepted**, not of what was **seen**. On the bundled cache the two agree on all 486\n"
    "  series — the ceiling removes the poisoners before the relative test runs — **which is exactly why\n"
    "  the one-liner would have looked fine**.\n",
    "- **Two plausible bases are wrong in OPPOSITE directions, and the cache cannot tell you.** This\n"
    "  cost two rounds, so it is worth the space.\n"
    "  - `.shift(1)` on the **seen** median excludes the point from its own basis but lets a\n"
    "    *rejected* value into the basis for the next one: a genuine `1.0e8` then a `5.0e10` typo\n"
    "    gives the third point `median(1e8, 5e10) = 2.55e10`, and the genuine third filing is deleted\n"
    "    as a hundredfold-low outlier.\n"
    "  - The obvious repair — judge against the median of what was **accepted** — is **absorbing**,\n"
    "    and strictly worse. If a series' first value is a typo the ceiling cannot reach, the accepted\n"
    "    set is that typo alone, every genuine value is >100× away from it, and **nothing is ever\n"
    "    accepted again**; only an acceptance could widen the basis, so there is no way back. Measured\n"
    "    on a real payload shape: **0 of 20** genuine counts survive. Both ingredients are in the\n"
    "    cache — a position-0 typo is real (EOG) and four series carry sub-ceiling ~1000× typos (PNR\n"
    "    9.84e10, PKG 8.99e10, REG 8.19e10, MAA 7.50e10) — only their coincidence is absent, and the\n"
    "    cache TTL is 7 days. **This is what juniper-data#404 shipped in its first two commits**, and\n"
    "    what round-2 lane B1 caught before merge.\n"
    "  - What shipped is the **lower median of prior SEEN values**, `prior[(n-1)//2]`. *Prior* rather\n"
    "    than prior-accepted kills the absorbing state, because a rejected value still counts towards\n"
    "    the sample and the basis re-converges. The *lower* median rather than the interpolating one\n"
    "    kills the first failure, because it is always a number some filing actually reported and\n"
    "    cannot land between two disagreeing values.\n"
    "  - **All three deliver identical multisets across the 483 in-bounds series of the real cache**,\n"
    "    because the ceiling removes the poisoners before the relative test runs. The whole-cache\n"
    "    check cannot separate them; only constructed shapes can\n"
    "    (`juniper-data/util/ad-hoc/2026-09-15_compare_outlier_basis_designs.py`, and\n"
    "    `2026-09-15_verify_lower_median_over_cache.py` for the equivalence). **A design that the\n"
    "    corpus cannot distinguish from its alternatives is not thereby validated.**\n",
    "§5.2: rewrite for the absorbing finding and what shipped",
)

# ---------------------------------------------------------------- §5.9: AGENTS.md updated
sub(
    "history, and invisible to any other machine. The `generator_version` statement there was updated by\n"
    "hand for the 4.0.0 bump **and is now stale again** — the equities pair is at 5.0.0. Nothing enforces\n"
    "it, so it drifts silently. Fix it in the next session that touches juniper-data.",
    "history, and invisible to any other machine. The `generator_version` statement there was updated\n"
    "by hand for the 4.0.0 bump, went stale the moment juniper-data#404 merged, and was updated again\n"
    "to 5.0.0 on 2026-09-16 by `util/ad-hoc/2026-09-15_ecosystem_agents_md_generator_version_5.py` —\n"
    "which exists as a script rather than a hand edit precisely because that file has no history, so\n"
    "the script is the only record that the change was made and against which merge. Round-2 lane A\n"
    "caught that an earlier draft called it stale *prematurely*: while #404 was open, `4.0.0` was\n"
    "correct. Nothing enforces this statement, so check it whenever a generator version moves.",
    "§5.9: AGENTS.md is updated, and was not stale while #404 was open",
)

# ---------------------------------------------------------------- Berkshire close is synthetic
sub(
    "deferred with a share-class-aware lookup recorded as its remedy — and **#404 made it visible**:\n"
    "   the two classes are now filtered as a scale error, pinned by its own test.",
    "deferred with a share-class-aware lookup recorded as its remedy — and **#404 made it visible**:\n"
    "   the two classes are now filtered as a scale error, pinned by its own test. **That pin is\n"
    "   synthetic, and knowing so matters**: the bundled BRK payload holds 7 facts, all Class A\n"
    "   (941,481–1,103,764), and both the old and new filters deliver an identical 6 from it. The\n"
    "   dual-class collision is demonstrated by the fixture, not by the cache — so a successor who\n"
    "   goes looking for it in the real data will not find it there.",
    "D-G: the Berkshire pin is synthetic",
)

# ---------------------------------------------------------------- §7 and §8
sub(
    "**Round 2** validates this revision. Record for both rounds:\n"
    "`reports/2026-09-15_round-39-consensus/`.",
    "**Round 2** validated this revision, and did not pass either:\n"
    "\n"
    "- **Lane B1 (refutation) found that the fix itself had a worse failure than the defect it\n"
    "  repaired** — the absorbing basis, §5.2 — and it was corrected and re-pinned before\n"
    "  juniper-data#404 merged. Twice in two rounds the load-bearing finding came from *running* the\n"
    "  code against real data, not from reading it.\n"
    "- **Lane A (receipts) found two wrong numbers in the ceiling's siting**, both of which had\n"
    "  reached the shipped code comment, the CHANGELOG and the register row the owner is being asked\n"
    "  to ratify (§0.6).\n"
    "- **Lane B2 (amputation / executability / naming) found ten traps dropped from the predecessor**,\n"
    "  including the byte-mirror obligation that X-A will hit (§0.3), and that this document never\n"
    "  said how a PR is opened in a fleet where a local `git push` cannot land a mergeable commit\n"
    "  (§5.6).\n"
    "- Both rounds also found the register carrying claims it could not support — an item said to\n"
    "  \"belong to the canopy ledger\" that no ledger row records, and a ruling that generalised one\n"
    "  client's transport to three. Both corrected in " + REG + ".\n"
    "\n"
    "Record for both rounds: `reports/2026-09-15_round-39-consensus/`.",
    "§7: round 2's record",
)
sub(
    "- [x] juniper-data#404 — the regression #395 shipped — `generator_version` 5.0.0 — MERGED (§4)",
    "- [x] juniper-data#404 — the regression #395 shipped — `generator_version` 5.0.0 — MERGED\n"
    "      2026-09-16, squash `1bbb6976`, verified by content on `main` and not by the badge (§4)\n"
    "- [x] `Juniper/AGENTS.md` moved to `5.0.0` after that merge (§5.9)",
    "§8: the merge and the AGENTS.md follow-up",
)
sub(
    "- [ ] This document validated — round 1 recorded in §7, round 2 pending",
    "- [x] This document validated — two rounds, three lanes each, both recorded in §7; neither\n"
    "      passed on the first pass and both changed shipped code",
    "§8: validation is complete",
)

HANDOFF.write_text(text)
print(f"\nhandoff updated: {HANDOFF.name}")
