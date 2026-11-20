# Lane A1-receipts — final report (verbatim, 2026-09-08)

**Lane verdict: PASS (receipts-level), with corrections.** 13 rows: **CONFIRMED 7 / REFUTED 1 / PARTIAL 4 / UNVERIFIABLE 1.** Every PR number, merge SHA, worktree name and §1 number in the document is real and reproducible; the errors are one stale-false claim (ml#1813), one inherited miscount (stashes), one self-refuting sweep claim, and one enumeration slip.

## Table

| # | Claim (§) | Verdict | Evidence | Correction |
|---|---|---|---|---|
| 1 | §2 table: data#381 `c8f09fe`, cascor#630 `1ea2062`, recurrence#151 `e5679b0` MERGED; ml#1813 "still OPEN" (§7/§8) | **PARTIAL** | `gh pr view`: #381 MERGED 14:32:55Z `c8f09fe3…`; #630 MERGED 14:19:44Z `1ea20626…`; #151 MERGED 14:21:07Z `e5679b00…`. **ml#1813 MERGED 2026-09-07T15:15:42Z, mergeCommit `26e12019…`**, head `2d78782a`, mergedBy pcalnon. Document text is byte-identical between draft commit `07eb031c` (14:43:14Z) and archive `94cc9b3c` (16:22:34Z): `git diff --stat` empty. | **True when written, false when archived.** #1813 merged 32 min after the draft; the handoff branch merged `main` twice afterwards (15:40Z, 16:15Z) without the text being updated. Also §2 says "all four merge SHAs verified" but lists only three — ml#1813's (`26e12019`) is absent, contradicting §8. |
| 2a | §2: each SHA is an ANCESTOR of its repo's `origin/main` | **CONFIRMED** | `merge-base --is-ancestor … origin/main; echo $?` → data `c8f09fe` 0, cascor `1ea2062` 0, recurrence `e5679b0` 0, ml `26e12019` 0. HEAD == origin/main in all four. | — |
| 2b | §8: "`origin/main` still carries the old `total`-scoped wording" | **REFUTED (stale)** | `git grep origin/main -- notes/…DEFECT-REGISTER.md` line 676: the re-scoped `APD-DATA-019` row. Last register commit on main is `26e12019` (#1813). | The re-scoped row IS on `origin/main`; nothing needs merging. Note the shipped row quotes **114.8x** — the precision §7 itself calls "unsupportable". |
| 3 | §2: round-36 PRs all MERGED; data#378 "merged by the Overtoad at 22:06 as `005a82b`" | **PARTIAL** | #376 `7064030d` 20:34Z, #377 `df71574a` 20:59Z, #378 **`005a82b3` 2026-09-05T22:06:11Z**, cascor#621 `58a0d426`, #624 `995be91f`, ml#1791 `9523f7cc`, #1795 `5406882c` — all MERGED, all `mergedBy: pcalnon`. | Facts confirmed. "Round 36's **five** PRs (…)" enumerates **six** (seven with #378). "By the Overtoad" is unverifiable from receipts — every merge in all six repos shows `mergedBy=pcalnon`. |
| 4 | §6: three worktrees exist as named; five from round 36 all merged; two pre-existing data stashes | **PARTIAL** | `ls worktrees/` + `git worktree list`: all three exist with the exact names at `73a45ae`/`b13a447`/`19879e5`; `gh pr list --head` → exactly one PR each (#381/#630/#151, MERGED). Round-36 §6 names five; all present, all MERGED. `git log -g refs/stash` in juniper-data → **THREE**: 2026-05-20 (×2), 2026-04-28. | Stash count is **3, not 2**; the "two" is copied verbatim from round 36's §6. Unmentioned worktree created 09-07: `juniper-cascor--fix--xor-staged-epoch-pair--20260907-1300--ec872cf0` (cascor#629, MERGED, another arc). Harness worktree `compiled-inventing-sprout` now sits on `docs/round-37-handoff` @`07eb031c`; both remote branches are deleted. |
| 5 | §1 expected values | **CONFIRMED** | grep → `79`; `register_open_set.py` → `96 rows \| 79 fixed \| 17 open`; `register_status_crosscheck.py` → 79 / 79 / 79 AGREE. | — |
| 6 | §0.3: neither env var set in juniper-deploy, tracked or untracked | **CONFIRMED** | `git grep` and recursive `grep -rn --exclude-dir=.git` (untracked + ignored + all six `.env*`) → exit 1. Defined in juniper-data (`equities/params.py:108`, `api/settings.py:219`, `equities/generator.py:294/305/483/564`, docs) and juniper-cascor (`src/main.py:630/661`, `api/settings.py:563`, `lifecycle/manager.py:3683`, `constants_api_defaults.py:125`). | Caveat: `.env.secrets.enc` is SOPS-encrypted — "zero" is over the readable tree. |
| 7 | §0.5: no `.md`/`.env` in cascor/data/canopy/ml mentions the flag or env var; cascor `CHANGELOG.md` documents `allow_truncated_datasets` | **PARTIAL (true but misleading)** | cascor `.md`/`.env`: only `CHANGELOG.md:37` and `:54` — zero hits for the flag/env var. data: exit 1. canopy: exit 1. **ml: three `.md` files hit** — the round-35, round-36 and round-37 handoffs. | Literally false for ml; true for operator-facing docs. |
| 8 | §0.5: four follow-ups filed in cascor#624's body; unbuilt | **CONFIRMED** | `gh pr view 624 --json body` "Still open (not in this PR)" lists all four verbatim. cascor main since 09-05 = #622/623/621/624/625/626/629/630/627/628; pickaxe for `_auto_start_training` and `get_metrics` since 09-05 → none; `dataset_shortfall` → #621/#624 only; open cascor PRs: none. | — |
| 9 | §0.2: canopy zero `allow_truncation`; `juniper_canopy/` holds only `__init__.py` | **CONFIRMED** | `grep -rn allow_truncation juniper-canopy` → exit 1. `git ls-files juniper_canopy/` → 1 tracked file. | — |
| 10 | Landed since the document's SHAs | **CONFIRMED (informational)** | data `c8f09fe..origin/main`: #380, #379 (requirements), #382 (`util/ad-hoc/2026-09-07_measure_filter_datasets_cost.py`). **None touch `equities/generator.py`, `csv_import/generator.py`, `api/routes/datasets.py`, `storage/*`**. cascor: #627/#628 (requirements). recurrence: none. ml `94cc9b3c..`: 6 handoff archives + `claude.yml`; register untouched. | Any stale line numbers were stale **on the day written**. |
| 11 | Duplicate-work guard | **CONFIRMED (clean)** | Open PRs: data#383 (dependabot) only; cascor/canopy/ml/recurrence/deploy `[]`. Merged since 09-07 on the flagged subjects: none build them. Adjacent: **data#382** (ad-hoc APD-DATA-019 cost script); **canopy#599** (`api_stage_dataset` gains a `hasattr(backend,"stage_dataset")` 501 guard). | No collision with §0.2/§0.12/§0.13/§0.8/§0.9 work. |
| 12 | §7/§8: two adversarial rounds run 2026-09-07 | **UNVERIFIABLE** | ml#1818 body asserts "two adversarial validation rounds"; `94cc9b3c` adds only the handoff; `grep -rli 'round[ -]37' prompts/ notes/` → only the handoff. #1818's body also repeats "ml#1813, still open" although #1813 merged 67 min before #1818. | No artifact; only self-assertion. |

## New findings the document does not contain

1. **The re-scoped register row ships the withdrawn precision.** `origin/main` line 676 says "(114.8x at N=100)"; §7 row 6 of the document says that figure is "unsupportable precision — spread ~2×".
2. **data#382 landed a docstring that is false on arrival** — its header says InMemory is "the ONLY store whose JD-PERF-02 TTL cache is live" (the pre-#381 state).
3. **§8's "Merge it, or the next session reads the superseded text" is now a no-op.**
4. **Timeline consistent with "went BEHIND 3 times"**: six unrelated ml PRs landed during #1813's 70-minute life; #1813 carries five `Merge branch 'main'` commits. Consistent, not proof.
5. **The harness worktree's local branches are behind their PR heads** and both branches are deleted on GitHub.

## What the evidence cannot support

Whether the two adversarial rounds happened (only asserted). Whether data#378 was merged "by the Overtoad" as distinct from a session. Whether safe_merge refused #1813 twice. Anything inside `.env.secrets.enc`. Any source-level claim — out of this lane's entry point.

## Unfinished

Nothing in scope. No source files read; no fetch/prune run.
