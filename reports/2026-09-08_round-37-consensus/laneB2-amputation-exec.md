# Lane B2 — amputation / executability / receipts — final report (verbatim, 2026-09-08)

## 1. Verdicts

| Lens | Verdict | Counts |
|---|---|---|
| 1 Amputation | **NEEDS CORRECTIONS** | 47 predecessor items classified: 21 CARRIED, 2 POINTED, 16 DROPPED-RECOVERABLE, **4 DROPPED-LOST**, 4 MOOT. Reverse check: §0.12, §0.13, §0.7 are genuinely new; nothing is a re-discovery. One chain-level loss predates r37 (the Overtoad's spec text exists nowhere) |
| 2 Executability | **NEEDS CORRECTIONS** | 5 of 13 §0 items actionable as written; 3 blocked-on-Overtoad; 4 carry missing information; 2 literal-following hazards (§0.2 poller, §0.12 cache turnover). §1/§5.7 runnable and current; §5.6 degraded |
| 3 Receipts | **NEEDS CORRECTIONS** (one false past-tense claim, two miscounts) | 24 DID-claims: 14 TRUE (8 re-derived exactly), 1 **FALSE at archive time**, 2 miscounts, 5 UNVERIFIABLE, 2 partial |

Overall: **NOT safe to archive as-is** — the false receipt (§7/§8 ml#1813), the §0.2↔§0.13 contradiction, and the two lost recipes need fixing; the substantive claims hold.

## 2. Lens 1 — DROPPED-LOST and POINTED-TO-STUB only

| Predecessor item | Class | Why it is lost |
|---|---|---|
| r36 §5.3: the SHA in `MERGED #N at <sha>` is the **head** it merged, not the squash commit; verify against `origin/main`'s tip | **DROPPED-LOST** | Real: `util/safe_merge.py:889` prints `head[:8]`. No memory carries it. r35 §5.2's recipe (`merge-base --is-ancestor <that sha> origin/main`) false-negatives on every squash merge. |
| r36 §5.7 / r35 §5.4: `pytest -q` on top of juniper-data's addopts `-q` suppresses the summary line | **DROPPED-LOST** | addopts really carries `-q` (`pyproject.toml:221-227`); not in juniper-data `AGENTS.md`, workflows, or any memory |
| r36 §4 / r35 §3.5: `test_shares_are_not_visible_before_they_were_filed`'s `ages.min() >= 0` cannot catch a stale value | **DROPPED-LOST** | Not in data#376/#377 bodies, the sizing note, the register, or memory; the test still stands at `test_equities_generator.py:948/976`. §0.7 restates the consequence without the finding |
| r35 §5.3: the circular-import chain | DROPPED-LOST (detail) | r37 §5.6 keeps only "a circular import otherwise" |
| r35 §0.3 "the Overtoad's spec, quoted verbatim in §3" | LOST AT CHAIN LEVEL (not r37's doing) | r35 §3 is the four findings; the spec is paraphrased in memory only |

No POINTED item resolved to a stub. The 16 DROPPED-RECOVERABLE items are recoverable only because MEMORY.md indexes them — r37 itself names none of the targets.

## 3. Lens 2 — per §0 item

- **§0.1** actionable as written.
- **§0.2** blocked by the document's own §0.13 + missing information: (a) the three options' wire forms are absent (memory has them); (b) **staging does not fetch** — `_reload_dataset` runs only from `start_training` (`manager.py:2269`) and `swap_dataset_live` (`:3028`), so a juniper-data 422 surfaces as a cascor 409 on start (`routes/training.py:116-126`), which canopy already renders verbatim — "the prompt fires at dataset-apply time" is wrong for the cold path; (c) canopy already polls status every fast tick via `/api/status` → `normalize_status`, a **whitelist** that would drop `dataset_shortfall` — the fix is one line there; (d) the apply callback is `_apply_dataset_handler`, not `parameters_panel.py`; "deselect" needs the `nn-dataset-type-dropdown` value Output owned by `gate_dataset_options`; "cancel" already exists. **Literal hazard**: a new poll callback is the F-035/F-039 renderer-starvation trigger class.
- **§0.3** blocked-on-Overtoad, and the question omits its two options and consequences. Pure information; **§8 still lists it as a hole to fix**, contradicting the withdrawal.
- **§0.4** blocked-on-Overtoad; the register's §2 operating-rule paragraph (lines 123-125) still names the withdrawn `total` remedy — ml#1813 edited only the §4.1 bullet.
- **§0.5** actionable; no file-vs-fix routing stated.
- **§0.6** actionable; anchors exact; the causal-median definition is unspecified; no ruling that these are to be fixed.
- **§0.7** actionable to file only; no remedy design; must not regress `test_a_same_day_restatement_keeps_the_current_period` (`:996`).
- **§0.8** actionable (file a row).
- **§0.9** actionable; `:866/:868/:771` land on docstring/decorator lines (actual `:869/:871/:774-775`).
- **§0.10** actionable; exact.
- **§0.11** actionable as written; the register rule has **no machine marker**; its paragraph is stale ("Both unparked rows"; `total` remedy). Mechanical open+unparked set = {`APD-DATA-019`}.
- **§0.12** actionable; "defined only on `EquitiesGenerator`" is false (`csv_import/generator.py:345` too); **literal hazard**: binding `max_symbols=None→14` changes `dataset_id` for every `equities_seq` request — a cache turnover the document does not mention.
- **§0.13** actionable but under-specified: the producer's descriptor carries no "accepted via", so "derive from the producer's response" can say `accepted`, never by whom.
- **§1** runnable; values current. **§5.6** `-p` is pytest's plugin flag; the document never says "pytest". **§5.7** all three gates real; runnable.
- **§8 ordering**: §0.2 (feature) leads; §0.12/§0.13 (live shipped defects, one gating §0.2) sit last — indefensible as written.

## 4. Lens 3 — DID-claims (false first)

| Claim | Status |
|---|---|
| §7/§8 "ml#1813 is still OPEN … `origin/main` still carries the old wording" | **FALSE at archive time.** MERGED 15:15:42Z (`26e12019`); text committed 14:43Z (true then); ml#1818 merged 16:22Z uncorrected. |
| §2 "All four merge SHAs verified" | Miscount — three SHAs in the table |
| §2 "Round 36's five PRs (…six numbers)" | Miscount — six |
| §7 withdraws "114.8× / 92.9×" | Yet ml#1813, data#381's body and the register row on main all ship "114.8× at N=100" |
| data#381 `c8f09fe`, cascor#630 `1ea2062`, recurrence#151 `e5679b0`, data#378 Overtoad-merged 22:06 `005a82b` | TRUE, exact |
| §4 measurements (485; 2009-04-15; 2009-12-18; 43.1%; 44.3%/46.0%; 503/500/15; 44.85%) | **RE-DERIVED EXACTLY** |
| §0.6 "61 of 485"; §0.9 "0 of 485 empty"; §0.10 "71 dei points"; §0.7 KO figures | TRUE, re-derived |
| §7 "two adversarial rounds run" | UNVERIFIABLE — no lane record anywhere |
| §5.1 "heredocs into `python3 -` DO work" | REFUTED in this lane (refused) |
| Anchors `:3933`, `:505`, `:866/:868/:771`, `:726` | Stale; 20 others exact |

No instrument for the §4/§0.6/§0.7 measurements is preserved in any `util/ad-hoc/` (rule violation); the §0.4 one is.

## 5. Internal contradictions

1. §0.2 "every blocker is now merged" vs §0.13 "should be fixed before canopy renders it"; §0/§8 order puts §0.2 first.
2. §0.3 withdraws "prefer fixing the OR" vs §8 "[ ] The `or settings.*` hole … not enforceable without it".
3. "All four merge SHAs" vs three; "five PRs" vs six.
4. §7 "five places" vs §0.3's four named.
5. §7 rejects 114.8× precision while the session's own ml#1813 wrote it into the register.
6. §8 "re-scoped row exists only on the PR head" vs merged 67 min before archive; the register's §2 paragraph still carries the old remedy.
7. §0.2's "fires at apply time" vs cascor fetching only at start/swap.
8. §5.1 heredoc claim vs r35 §5.1 and observed refusal.

**Naming-rule violations** (11): the register referred to by role four times without its filename; `docs/REFERENCE.md`/`CHANGELOG.md` twice without a repo; "five places" unnamed; "the partial-data spec" never located; **no changed-files list**.

## 6. What the evidence cannot support / unfinished

Whether the two validation rounds happened as described; the 44-day and 19-day KO episodes, the "four runs" spread, the `_auto_start` and `test_crossval` runtime claims — not re-run; whether `-p juniper_data.api.app` is still required — untested (would write into the frozen tree); ancestry checks used local `origin/main` refs.
