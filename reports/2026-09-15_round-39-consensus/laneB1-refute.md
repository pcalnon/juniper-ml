# Round 39, round 2 — Lane B1 (adversarial refutation)

**Verdict: PARTIALLY REFUTED** — two load-bearing failures, one of them a live regression class in
the fix the document celebrates.

Brief: refute the target document, not confirm it. Round 1's B1 lane had found that
juniper-data#395 shipped a regression delivering two tickers 990× and 428× too large, by *running*
the shipped code against real data; this lane was briefed to aim for that class again.

Target:
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`
(the revision that preceded this one).

---

## CRITICAL 1 — juniper-data#404 was OPEN, not MERGED

The document asserted `MERGED` in §2's table, §4, §5.8, §5.9 and §8.

```
$ gh pr view 404 --json state,mergedAt,isDraft
state=OPEN merged=null draft=false

$ git show origin/main:juniper_data/generators/equities/generator.py \
    | grep -E '^VERSION|_SHARES_ABSOLUTE_CEILING = |expanding\('
57:VERSION = "4.0.0"
103:_SHARES_ABSOLUTE_CEILING = 1.0e13
1112:        running_median = observations["shares"].expanding(min_periods=3).median()
```

By the document's own §1 rule, that output means the delivered share counts were still wrong for
AIZ and EOG — on `main` and in the published 0.14.0 wheel. Downstream: the register marked
`APD-DATA-050` **FIXED** and counted it in the 94; `APD-DATA-047` was described as "now at 1e11"
when the deployed value was 1e13.

**Resolved** — #404 merged 2026-09-16T02:08:43Z, squash `1bbb6976`, after the corrections below.

---

## CRITICAL 2 — #404's accepted-only basis is ABSORBING

**Claim refuted** (document §5.2, register `APD-DATA-050`): *"The basis must be the median of what
was **accepted**, not of what was **seen**"*.

Method: extracted both trees with `git archive` (`origin/main` and `origin/fix/…`), pointed the
cache at a copy of the real 486-payload cache, blocked `_sec_get`, and fed both **real shipped
modules** the real PNR payload (CIK 0000077360) with the typo record's `filed` date moved so the
already-present 1000× typo becomes the earliest-known fact — the shape EOG already exhibits for
real.

```
PRE-#404 (main, 4.0.0): delivered n=67  max=98,419,314,000
#404 (5.0.0):           delivered n=1   max=98,419,314,000
observations LOST by #404: 66     #404 kept: ['98,419,314,000']
```

Basis comparison on the same 67 real values:

| basis | kept | genuine kept | typos kept |
|---|---|---|---|
| accepted-only (**#404 as first written**) | 1/67 | **0/66** | 1 |
| `shift(1)` (rejected by the doc) | 65/67 | 64/66 | 1 |
| unshifted `min_periods=3` (#395) | 67/67 | 66/66 | 1 |

On the document's *own* counter-example (`[1e8, 5e10, 1.01e8, …]`), accepted-only keeps 5/5 genuine
and `shift(1)` keeps 4/5 — so accepted-only buys **one** genuine point in the position-1 case and
pays **the whole series** in the position-0 case. `shift(1)` self-corrects because the seen-median
re-converges; accepted-only has no recovery path: once `kept_values == [typo]`, every genuine value
is ≥100× away forever.

Low-side instance, using the register's own PSKY number: a 100,000-share placeholder (exactly at
`_SHARES_ABSOLUTE_FLOOR`, so it survives) followed by 20 genuine 1,071,666,977 counts →

```
PRE-#404: delivered 21/21 (20/20 genuine)
#404:     delivered  1/21 ( 0/20 genuine)  -> [100000.0]
```

This re-creates verbatim the defect the floor was added to fix.

**Reachability — latent, not live.** On the bundled cache the failure mode fires **zero** times: 0
series whose post-bound head is a >100× outlier, 0 records with a missing `filed` date. But both
ingredients are present in the same 486 payloads — a position-0 scale typo occurs for real (EOG,
`end 2009-08-03 / filed 2009-08-06`, the earliest fact in its payload), and sub-ceiling 1000× typos
occur in **4 series / 7 observations** (PNR 9.84e10 @pos 3, REG 8.19e10 @pos 3, PKG 8.99e10 @pos
51/55/62, MAA 7.5e10 @pos 14/16). Only their coincidence is absent, and the cache TTL is 7 days.
**No test in #404 covered a sub-ceiling head typo** — `test_a_typo_in_a_series_first_filing_is_…`
used 5.00e11 (above the ceiling) and `test_a_genuine_first_filing_is_not_dropped` used 1.70e10.

**Resolved before merge** — the basis is now the lower median of prior *seen* values, and
`test_a_sub_ceiling_typo_in_the_first_filing_does_not_delete_the_series` pins it (0 of 20 genuine
survive the old basis; 19 of 20 survive the new one).

---

## MAJOR 3 — The ceiling's siting is wrong in BOTH directions

Claim (document §0.5, register `APD-DATA-047`, the `_SHARES_ABSOLUTE_CEILING` comment, and a test
docstring): *"between the largest genuine count in the bundled universe (AAPL, 1.70e10) and the
smallest demonstrated typo in the cache (AIZ, 1.168e11): 5.9× of headroom below it, and every
observed scale error above it."*

- **Largest genuine count is Citigroup, 29,206,440,560 (2.92e10)** — 1.72× larger than AAPL. Proven
  genuine internally: C's series runs 22,863,947,261 → 29,206,440,560 monotonically across 7
  consecutive quarters, then steps to 2,917,949,115 — an exact 1:10 reverse split (May 2011).
  NVDA's 24,530,000,000 (post-10:1 split, 8 consecutive recent quarters) is also above AAPL.
  **Real headroom is 3.42×, not 5.9×.**
- **"Every observed scale error above it" is false.** Seven observed scale errors sit *below* the
  ceiling: PNR 98,419,314,000 (PNR's pos-0/1/2 are 98,701,186 / 98,690,604 / 98,409,192 — a literal
  ×1000), REG 81,867,549,000 (exactly 1000× its own pos-1 value 81,867,549), PKG ×3 at ~8.9e10, MAA
  ×2 at ~7.5e10. **The smallest demonstrated typo in the cache is MAA's 74,776,229,000 (7.48e10)**,
  not AIZ's 1.168e11.

The populations **overlap across the bound**. The owner was being asked to ratify 1e11 against two
numbers that are both wrong.

---

## MAJOR 4 — "18 observations across 24 series" is arithmetically impossible

```
observations strictly above 1e11 : 39, across 24 series
observations in (1e11, 1e13]     : 18, across  9 series
```

18 observations cannot occupy 24 series. The "24" belongs with 39. (The adjacent claims *"the
relative test rejects at least one observation in 6 series and the ceiling in 24"* both verify
exactly.)

---

## MAJOR 5 — juniper-recurrence-client does NOT "already have the whole thing": 2 of 9

AST walk of `juniper-recurrence/juniper-recurrence-client/juniper_recurrence_client/client.py`:

| method | per-call `timeout`? |
|---|---|
| `train`, `crossval` | **yes** |
| `predict`, `training_status`, `crossval_status`, `get_model`, `get_dataset`, `health_check`, `is_ready` | **no** |

No method takes `**kwargs`, so the transport's `setdefault` at `:265` is unreachable from 7 of 9
public calls — including `predict`, the other long-running one. The `APD-RCLIENT-002` close is
honest about this (*the other public calls stay on the client-wide scalar*); the handoff dropped
the qualifier. Related and uncorrected at the time: the `APD-ECO-003` ruling text in the register
still said *"The transport already honours it … so only the public signatures are missing"*, which
is false for juniper-cascor-client (`client.py:530` takes no `**kwargs`, passes `timeout=self.timeout`
literally at `:544`).

---

## MAJOR 6 — §0.2's "independent … of each other" is false for C-A / C-B

C-A adds a `timeout` parameter to public method signatures; C-B changes the return annotations of
the `Dict[str, Any]` methods. Measured overlap: **38 identical `def` lines in the same two files** —
12 of 20 public methods in `juniper_data_client/client.py`, 26 of 30 in
`juniper_cascor_client/client.py`.

---

## MINOR 7-11

- **X-A and X-B collide in one file, unnamed.** `APD-CASCOR-008` edits
  `juniper-cascor/src/api/lifecycle/manager.py:3876-3879`; `APD-CASCOR-013` edits
  `_dataset_shortfall` in the same file (`:1243`, `:2831`, `:2898`, `:4175`).
- **Register self-contradiction:** `APD-DATA-049` says *"orphans the **485** payloads"*;
  `APD-DATA-051` and §6 say **486**. The cache holds 486.
- **D-A's doc-update list is incomplete:** `csv_import/generator.py:133` and `:145` carry the same
  documented asymmetry and were not named.
- **§7's record directory did not exist** at the time of the lane.
- **The Berkshire "bounded close" is synthetic only.** The bundled BRK payload (CIK 0001067983)
  holds **7 facts, all Class A** (941,481–1,103,764); both variants deliver an identical 6. The
  dual-class claim is demonstrated by the new fixture, not by the cache.

---

## Claims tried hard and could NOT break

All executed against the real shipped modules and the real 486-payload cache.

1. **990× and 428×** — exact: AIZ 116,799,796,000 / 117,926,517 = **990.45**; EOG 251,931,774,000 /
   587,723,622 = **428.66**.
2. **"AIZ's typo at position 1 and EOG's at position 0"** under the module's own ordering
   (`drop_duplicates(["end","filed"], keep="last")` → `sort_values(["filed","end"], kind="stable",
   na_position="first")`) — exact, both.
3. **"shift(1) and accepted-only agree on all 486 series"** — **0 disagreements**. The stated reason
   (the ceiling removes the poisoners first) is correct.
4. **No over-deletion on the bundled cache.** Delivered **multisets** differ in exactly **2 of 486**
   series, both pure removals of the two known typos. 0 emptied, 0 genuine lost.
5. **The 1e11 ceiling rejects no genuine observation** anywhere in the cache: all 39 values above it
   are ≥1.168e11.
6. **"6 series and 24"** for the relative test and the ceiling — exact.
7. **§5.11's remeasurement** — 486 payloads, **183** restatement CIKs (comment says 162), **42**
   value-changing end collisions (comment says 54). Reproduces exactly.
8. **§5.3** — all four #404 fixtures run against the pre-#404 module: the three new regressions
   **FAIL** pre-fix and **PASS** post-fix; the over-correction guard passes under both, as claimed.
9. **Loop cost** — `0.0001s` at the real worst case (longest series 85 post-bound observations). It
   *is* O(n²) (`n=2000 → 0.0137s`, `n=10000 → 0.4388s`), but "the series are short … so the loop is
   free" holds.
10. **Edge cases** — single observation kept; all-identical kept; exactly-at-floor and
    exactly-at-ceiling kept; `1e11+1` → `None`; negative and zero heads dropped by the floor before
    the loop sees them; the ×100 boundary is inclusive.
11. **§1's juniper-ml half** — FIXED 94; `119 rows | 94 fixed | 25 open`; crosscheck 94/94/94 AGREE;
    33 tests OK; archive test 2 OK.
12. **§5.9 / §5.10** — `test_val_emission_guards.py:290-292` asserts major ≥ 3 plus the allow-list;
    `core/dataset_id.py:23-61` does hash `version` into the id, so the bump argument is sound.
13. **§0.1 mechanical facts** — `datasets.py` is 1030 lines; exactly three `or settings.*`
    allow-truncation sites; the named test exists; the two counters are at `storage/base.py` ×4,
    `storage/postgres_store.py` ×2, `core/models.py` ×2.
14. **PR states** — juniper-ml#1864 and #1898 MERGED; juniper-data#395 merged at `b6ab7c1`.
