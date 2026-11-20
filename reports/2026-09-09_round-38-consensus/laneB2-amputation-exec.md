# Round 2 — Lane B2 (amputation / executability / naming) — final report, 2026-09-09

*(Verbatim as returned by the lane. Two of its findings were re-derived by the orchestrating
session and one was refuted; see `README.md` § Reconciliation in this directory.)*

## 1. Verdicts

| Lens | Verdict | Counts |
|---|---|---|
| 1 Amputation | **NEEDS CORRECTIONS** | 13 r37 §0 items + 7 r37 §5 traps + 10 r37 §8 lines classified: 6 CARRIED, 2 POINTED (both pointers resolve), 5 DROPPED-RECOVERABLE, **2 DROPPED-LOST**, 5 MOOT. §5.9 recovers 2 of round-1 B2's 4 lost recipes in-section, 1 at §5.6, 1 rendered MOOT at §4 — **all four accounted for, all four ACCURATE** |
| 2 Executability | **NEEDS CORRECTIONS** | 7 §0 items: 3 actionable as written, 1 blocked-on-Overtoad, 2 missing information, 1 literal-following hazard. §1 reproduces EXACTLY. §5.10 paths all exist. Every §0 anchor resolves on today's post-merge `main` |
| 3 Receipts / naming | **NEEDS CORRECTIONS** | 10 distinct `<<PLACEHOLDER>>` tokens / 14 occurrences unfilled; 1 false receipt (`push_signed_commit.py`); 1 receipt contradicted by source (KO/ABT comment); 2 §6 errors; ~26 naming violations; 3 changed files unlisted. §7's round-1 summary is **exact on all six lanes** |

Whole document **3,221 words**; **§0 alone 825 words** (lines 26–101).

## 2. Placeholders (author must fill every one)

`<<ML_PR>>` L20, L129 ×2, L159, L296 · `<<CASCOR_633>>` L126 · `<<CANOPY_605>>` L127 · `<<DATA_388>>` L128 · `<<ML_STATE>>` L129 · `<<ROUND2>>` L281 · `<<X633>>` L293 · `<<X605>>` L294 · `<<X388>>` L295 · `<<XREG>>` L296.

Fill values verified today: cascor#633 **MERGED** `44dafe018e3841b078e5a15bb2769c7dfdec60a6` 17:57:06Z; canopy#605 **MERGED** `b587e54efd18d6afa098a75415850d37ea0cd2b7` 19:25:55Z; data#388 **MERGED** `d7f4be5bd6c3d4f60a420c32fff64e59de96c231` 17:14:32Z.

## 3. DROPPED-LOST (in full — 2)

1. **r37 §5.2 — the CodeQL remedy.** *"The fix that works is `importlib.import_module(...)`: a **call**, not an import"*, for `py/side-effect-in-assert` and `py/unused-import` on subclass-registration imports. Absent from the draft. Memory `reference_noqa_hides_a_real_defect` carries the *diagnosis* half only (it is about `import ast  # noqa: F401`), not `py/side-effect-in-assert` and not the `importlib` remedy — and **the draft names that memory nowhere**. Lost.
2. **r37 §5.6 — the juniper-recurrence test recipe.** *"borrow one and set `PYTHONPATH=juniper-recurrence-model`, or a stale installed copy shadows the worktree… `test_crossval.py` does not collect (stale `juniper_model_core`) and one torch test skips — both pre-existing."* Draft §5.10 (L246) keeps only *"juniper-recurrence has no env."* This is the exact tier draft §0.5 sends the successor into, and the two known pre-existing failures are the ones a fresh session will mistake for its own breakage. Lost.

### Round-1 B2's four DROPPED-LOST recipes — §5.9 audit (all four ACCURATE)

| Recipe | Where recovered | Accurate? |
|---|---|---|
| `safe_merge.py` prints the **head** SHA | §5.9 bullet 1 | **YES** — `util/safe_merge.py:889`: `return f"MERGED #{pr} at {head[:8]} via {method}"` |
| `ages.min() >= 0` cannot catch a STALE value | §5.9 bullet 2 | **YES** — `juniper-data/juniper_data/tests/unit/test_equities_generator.py:976`, inside `test_shares_are_not_visible_before_they_were_filed` (`:948`) |
| The Overtoad's spec exists verbatim only in memory | §5.9 bullet 3 | **YES** — `project_partial_data_contract_arc_2026-09-05.md` carries the three-option table with wire forms (`allow_truncation=true`+`incomplete_rows="accept"` / `"drop"` / send neither → 422) |
| `-q` doubling with `addopts` | **§5.6**, not §5.9 | **YES** — `-q` present in all three: cascor `pyproject.toml:205`, juniper-data `:223`, canopy `:358` |
| (chain-level, r35 §5.3 circular import) | **§4**, as MOOT | **YES** — "Stale since data#333"; round-1 A2 confirmed `-p` unnecessary |

**§5.9's framing is misleading**: its heading claims to recover the recipes lane B2 found lost, but lists three, one of which was the *chain-level* loss rather than one of the four. Add pointers to §5.6 and §4.

## 4. Contradictions and false receipts (in full — 8)

1. **`util/ad-hoc/push_signed_commit.py` is NOT this session's deliverable.** §2(d) L129 lists it under `ml#<<ML_PR>>`; §5.2 L177 calls it *"(new)"*. It landed on `origin/main` in **ml#1830** (merged 2026-09-09T00:25:17Z), whose body attributes it to the **canopy#601** session, and was revised by **ml#1853** (merged 18:52:26Z, *"now reads back what it wrote"*). It is not untracked in this worktree (`ls` fails; `git status` does not list it). A second copy, `util/ad-hoc/2026-09-08_push_signed_commit.py`, is also on `main`. §5.2's *description* does match main's version (`--expected-head` required full SHA, `:112`/`:150`; *"sends WHOLE FILE contents"*, `:22`) but omits #1853's read-back.
2. **§2's "three stale comments" (data#388) does not include r37 §0.10's.** `generator.py`'s *"no shares concept to SEC at all"* comment **still exists on juniper-data `origin/main`** (1 grep hit). r37 §0.10 is therefore open, and §2 reads as though it were closed.
3. **§2 ↔ §5.7.** §2 records shipping `_PROJECT_API_SHORTFALL_REFUSAL_TOKEN`; §5.7 L224 says *"A constant named `*_TOKEN` fails `hardcoded_password_string` whatever its value. Name it `*_MARKER`."* The shipped constant carries **no `# nosec`** (`src/cascor_constants/constants_api/constants_api_defaults.py:148`), sits inside the bandit hook's scope (`files: ^src/.*\.py$`, `--skip=B101,B301,B311,B403` — B105 **not** skipped), and merged green. Canopy's twin **is** `DATASET_SHORTFALL_REFUSAL_MARKER` (`src/frontend/dashboard_manager.py:515`). Either §5.7 is over-general (the cascor site is an annotated assignment) or §2 records a latent hook failure; the draft reconciles neither.
4. **§6 L252 — "branch `main` at `44de51c5`".** The worktree branch is **`worktree-pure-toasting-token`**, and `origin/main` is **`5fbe3bc1`**, not `44de51c5`.
5. **§6 L254-255 — "the worktree carries their files untracked".** Untracked today: `reports/2026-09-08_round-37-consensus/`, `util/ad-hoc/2026-09-08_round38_pr_edit_scripts/`, `util/ad-hoc/register_round38_file.py`, **`util/ad-hoc/register_round38_dates.py`** (unlisted anywhere in §2). `push_signed_commit.py` is absent.
6. **Header L11-13 ↔ §7 L281.** The header already reports round-2 outcomes (*"this round's B1 lane partially succeeded against the predecessor's own overturns"*) while §7's round-2 line is still `<<ROUND2>>`.
7. **§2(c) claims `reports/2026-09-08_round-38-consensus/` (round 2, three).** The directory **does not exist**; round 2 is running now (2026-09-09), so its `2026-09-08` date stamp will also be wrong, and the "three" is unverifiable from inside a lane.
8. **§0.7 vs the register as filed.** §0.7 L99 says the 16 parked rows *"need Overtoad unparking before any session may action them"* — true — but the register's own 2026-09-09 note (`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md:130-136`) states the §4.9 rows **end the empty set**: `APD-DATA-039`'s cache-key half and `APD-CASCOR-009 / -010 / -012` *"are the first a session may work without asking first."* The draft never says this. **Verified consistent otherwise**: 28 open = 17 primer (16 parked + `APD-DATA-019`) + 11 post-primer.

## 5. Per-§0-item executability

- **§0.1** (validate cold) — **actionable as written**.
- **§0.2** (cascor follow-ups) — **actionable as written**. Every anchor resolves on cascor `main` **after** #633 (`44dafe0`): `_auto_start_training` `src/api/app.py:482` (scheduled `:422`), `get_metrics` `manager.py:2824`, `_reload_dataset` `:3963`, `--allow-truncated-datasets` `src/main.py:624`. The doc-gap claim is **exact**: neither `AGENTS.md` (Auto-Start block `:161`) nor `.env.example` (Auto-Start block at lines 79–85 of 106 — "line ~80" correct) names `JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS`; `src/main.py:630`'s help text does, which is not a doc. Its "base on `main` after it merges" trap is now satisfied.
- **§0.3** (live E2E) — **missing information**: no stack-launch recipe, no ports, and the **canopy E2E ledger is never named by filename**. The `equities` NaN precondition is correct.
- **§0.4** (four Overtoad decisions) — **blocked-on-Overtoad**, correctly stated. All anchors resolve: `model_fields_set` for `max_bytes` at `csv_import/generator.py:151`; `test_request_cannot_opt_out_of_deployment_allow_truncation` at `test_csv_import_generator.py:727`; `_CACHE_DIR / "shares" / f"{int(cik):010d}.json"` at `equities/generator.py:869` with `if use_cache and cache.exists()` at `:871`; the census dir exists on data `origin/main` as `util/ad-hoc/2026-09-08_equities_shares_cache_census`.
- **§0.5** (`equities_seq` `data_quality` consumer in recurrence) — **missing information**: no file, symbol or package anchor anywhere in `juniper-recurrence`, and §5.10 has been stripped of the recurrence recipe (DROPPED-LOST 2).
- **§0.6** (canopy `INFRASTRUCTURE_FIELDS`) — **literal-following hazard**. Anchor confirmed: `juniper-canopy/src/dataset_schema.py:82-90` = `{train_ratio, test_ratio, shuffle, seed, use_cache}`; `val_ratio` absent, so it does render. But "one line" = adding `val_ratio` to the exclusion set, which **removes** the in-loop split control from the sidebar; the ecosystem data contract makes `val` the selection split. Say which direction is intended.
- **§0.7** (16 parked rows) — **actionable but materially incomplete**; see contradiction 8.

**§1 reproduces EXACTLY** from the worktree root: `grep -c` → **82**; `register_open_set.py` → **`110 rows | 82 fixed | 28 open`**; `register_status_crosscheck.py` → **82 / 82 / 82, AGREE**. §4.9 exists (register `:1116`), cites this handoff by filename (`:1126`), and **`114.8×` has 0 occurrences** in the filed register. §5.10's three interpreter paths all exist. §4's corrected line numbers all land at the frozen SHAs (`:508` `bind_deployment_defaults`, `:869`/`:871`, `:774` OHLCV key, cascor `:3956` `allow_truncated = bool(Settings().allow_truncated_datasets)`). §2's "One PR because…" justification is real: `tests/test_thread_handoff_archive.py:50-59`. r37 §0.8's fork-drift row is filed and resolves: `APD-CASCOR-008` at register `:1140`.

**§7's round-1 summary is exact on all six lanes** — A1 *"PASS (receipts-level), with corrections"*; A2 *"**FAIL** — 21 claims probed: 15 CONFIRMED, 2 REFUTED, 2 PARTIAL, 4 STALE-LINE"*; A3 *"PASS — 10/10 claims confirmed on substance… 6 new findings"*; A4 *"PASS — 9 claims: 6 CONFIRMED…"*; B1 *"0 succeeded / 2 partially succeeded (Attacks 1, 6) / 4 failed"*; B2 *"NEEDS CORRECTIONS"* on all three lenses, *"4 DROPPED-LOST"*.

## 6. Naming-rule violations (line numbers)

Two or more documents are cited, so **every** reference must carry a filename. Unnamed references to the predecessor by round number or by its section number: **L12, L55, L64, L72, L118, L138, L143 (§4 heading), L147, L148, L149, L150, L151, L152, L153, L154, L155, L156, L157, L162, L269, L292**. Unnamed **role** references: **L52** "the canopy E2E ledger"; **L99-100** "the register's own operating rule"; **L129** "Register: §4.9"; **L241** "the register and the handoffs paraphrase it"; **L300** "partial-data arc updated". The consensus procedure `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` governs §7 and is **never named**.

**Changed-file list incomplete** (§2 / §8): missing `util/ad-hoc/register_round38_dates.py`; the three new memories are named only inside the §5.4 / §5.7 / §5.8 traps, never as changed files (all three verified present, mtime 2026-09-08 19:11–19:12); `juniper-data/util/ad-hoc/2026-09-08_equities_shares_cache_census/` appears at L79 as an instrument, not as a directory this round created; `project_partial_data_contract_arc_2026-09-05.md` was updated (verified — it now carries cascor#633 / canopy#605 / data#388 sections) but §8 names it only by role.

## 7. What the evidence cannot support

Whether round 2 ran as §7 will describe (`<<ROUND2>>` unfilled; `reports/2026-09-08_round-38-consensus/` absent). Whether ml#1830's session and the round-38 session are the same actor (its body points to canopy#601; no session id recorded). Whether bandit B105 truly does not fire on the cascor annotated assignment (not executed — read-only lane, no hook run). The `aecd0bb8` / `5179bca2` follow-up commit SHAs in §2 (not resolved). The 24-test and 3-manifest-row counts in the canopy#605 row (not counted). Whether `val_ratio` is present in every generator schema canopy renders. All merge-ancestry checks used `gh` API `mergeCommit` oids, not a local `merge-base --is-ancestor`.
