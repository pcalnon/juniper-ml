# Round-39 handoff — independent-agent consensus record (2026-09-15/16)

Validation of
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`
and of the round-39 edits to `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, under
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`. Rounds 37 and
38 are recorded in `reports/2026-09-08_round-37-consensus/` and
`reports/2026-09-09_round-38-consensus/`.

## The one-sentence version

**Both rounds failed, and both failures changed shipped code** — round 1 found that
juniper-data#395 had delivered two tickers' share counts 990× and 428× too large, and round 2 found
that the fix for *that*, as first written, had a worse failure than the defect it repaired.

## Minimum record (procedure §7)

- **Tree.** Not frozen, and deliberately so: juniper-data#404 was open across both rounds and was
  amended twice in response to them. juniper-ml worktree `pure-toasting-token` at `44de51c5` with
  the register edits uncommitted; juniper-data `origin/main` at `f379763` during the rounds, then
  `1bbb6976` (the #404 squash) after. Both lanes A and B1 independently recorded #404's open state
  and the timestamps at which they observed it, which is what the non-frozen tree costs and what
  makes it legible anyway.
- **Two rounds, three lanes each, one launch message per round, three distinct briefs:**

  | Round | Lane | Entry point | Verdict |
  |---|---|---|---|
  | 1 | A | receipts and source | PASS WITH CORRECTIONS |
  | 1 | B1 | refutation | **REFUTED — found the shipped #395 regression** |
  | 1 | B2 | amputation / executability / naming | FAIL — 9 DROPPED-LOST |
  | 2 | A | receipts and source | PASS WITH CORRECTIONS — 2 numeric refutations, 1 new finding |
  | 2 | B1 | refutation | **PARTIALLY REFUTED — found the absorbing basis in the fix** |
  | 2 | B2 | amputation / executability / naming | FAIL — 10 DROPPED-LOST, no PR procedure |

- **Round 1's three lane reports are not in this directory, and that is a loss.** They were returned
  as agent final messages and were lost to a context compaction before being written to disk; the
  lanes' working directories survive under the session scratchpad (`laneR39A/`, `laneR39B1/`,
  `laneR39B2/`) but the prose does not. What round 1 found is recorded through the changes it
  caused — juniper-data#404 itself, `APD-DATA-052`, and §7 of the handoff — rather than in its own
  words. **Write a lane's report to `reports/` when it lands, not at the end of the round.**
- **Round 2's reports are here**, as the lanes returned them: `laneA-receipts-and-source.md`,
  `laneB1-refute.md`, `laneB2-amputation-exec-naming.md`.

## What round 2 changed

**In shipped code** (`juniper-data`, all in PR #404 before it merged):

1. **The relative filter's basis was replaced.** Judging each point against the median of the
   already-**accepted** values is *absorbing*: if a series' first value is a typo the ceiling cannot
   reach, the accepted set is that typo alone, every genuine value is >100× away, and nothing is
   ever accepted again — 0 of 20 genuine counts survive, measured on a real payload shape. The
   shipped basis is now the **lower median of prior *seen* values**. Pinned by
   `test_a_sub_ceiling_typo_in_the_first_filing_does_not_delete_the_series`, which fails against the
   basis it replaces.
2. **Two figures in the ceiling's rationale were wrong**, in the code comment, the CHANGELOG and the
   register row the owner is being asked to ratify: the largest genuine count in the cache is
   Citigroup's 2.92e10, not AAPL's 1.70e10 (which is the largest in the *default 14-symbol prefix*),
   so headroom is 3.4× and not 5.9×; and "18 observations across 24 series" conflated two bands
   (18 across 9 in `(1e11, 1e13]`; 39 across 24 above `1e11`).
3. **Lane A's unverified side observation became the design's best argument.** The four largest
   values that pass the 1e11 ceiling are themselves typos (PNR, PKG, REG, MAA, 483–949× their own
   medians), every one caught by the relative filter, and the ceiling cannot be tightened to reach
   them without crossing Citigroup's genuine 2.92e10. The two populations overlap across any
   absolute bound — which is what makes the two instruments complementary rather than redundant.

**In `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`:**

- `APD-DATA-047` — the siting figures corrected, and the real shape of the owner's choice stated.
- `APD-DATA-049` — "485 payloads" → 486.
- The `APD-ECO-003` ruling — its evidence sentence generalised one client's transport to three.
  juniper-data-client is ready; juniper-cascor-client's `_request` takes no `**kwargs`;
  juniper-recurrence-client is 2 of 9.
- §4.9's preamble — an earlier draft claimed the `val_ratio` / `INFRASTRUCTURE_FIELDS` item "belongs
  to the canopy ledger". No such row exists in any canopy note. The item is resolved in the code
  (`juniper-canopy/src/dataset_schema.py:114`) and unrecorded as a decision.

**In the handoff:** ten restored traps (the signed-PR procedure, the cascor byte-mirror obligation,
the sandbox's structural refusals, the crosscheck's silent-miss modes, and six more), three newly
named collisions (D-B/D-F, C-A/C-B, X-A/X-B), the three X-C sites and M-A's pins and test named for
the first time, and §5.2 rewritten around what actually shipped.

## The reusable lesson

**A design the corpus cannot distinguish from its alternatives is not thereby validated.** All three
candidate bases — unshifted, shifted-seen, and accepted-only — deliver *identical* multisets across
all 483 in-bounds series of the real cache, because the absolute ceiling removes the poisoners
before the relative test ever runs. The whole-cache sweep was run, agreed, and proved nothing; the
separation is visible only on constructed shapes. Twice in two rounds the load-bearing finding came
from executing the code against adversarial data, not from reading it and not from a corpus sweep.

The instruments are in juniper-data: `util/ad-hoc/2026-09-15_compare_outlier_basis_designs.py` (the
shapes that separate the three) and `util/ad-hoc/2026-09-15_verify_lower_median_over_cache.py` (the
whole-cache equivalence that does not).
