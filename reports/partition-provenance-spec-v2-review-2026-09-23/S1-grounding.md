# Round 2, lane S1 (grounding) -- final report, verbatim

**Verdict: GROUNDED WITH FINDINGS.** The spec (`notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md` at 8c9d65f) is grounded in almost every claim about the code at its pins. The two real problems are in its release plan (§11.2): one version is already taken, and one precondition is missing.

## Findings

**1. MAJOR: the version plan collides with a release that already merged.**
- **Spec text:** §11.2 "juniper-data 0.15.0 → 0.16.0. MINOR, because it adds an artifact key". W6 "ends with Release 0.16.0". W10 "`[servers]`: `juniper-data>=0.16.0` … so that `pip install juniper-ml[all]` installs a producer that emits the block".
- **Source:** juniper-data main is now `7125e161`, "release: juniper-data 0.16.0 (#433)". It merged at 15:24:52, five minutes before 8c9d65f (15:29:51). Its body says "Ships #420, #421, #426, #422 and #430", and its CHANGELOG has `## [0.16.0] - 2026-09-23`. PyPI still shows 0.15.0 and no v0.16.0 GitHub Release exists yet.
- **Consequence:** 0.16.0 carries no block, so a `>=0.16.0` floor would admit a producer that doesn't emit one.
- **Correction:** the block ships in 0.17.0 and W10's floor becomes `>=0.17.0`. "Not yet released" (§1 item 9, §3.1 note 3, §3.2) should become "ships in 0.16.0 (#433); Release not yet cut".

**2. MAJOR: W10's preconditions are not enough.**
- **Spec text:** §11.2 "juniper-ml meta-package, after both releases are published: `[clients]`: `juniper-data-client>=0.6.0`".
- **Source:** juniper-ml's `recurrence` extra admits only `juniper-recurrence>=0.5.0,<0.6.0`. The published 0.5.0 declares a core dependency `juniper-data-client<0.6.0,>=0.4.2` (PyPI JSON).
- **Consequence:** `juniper-ml[all]` can't be installed until recurrence publishes a release with W4's widened cap. canopy 0.8.1's cap sits in its `juniper-data` extra, which juniper-ml doesn't request, so canopy doesn't bind.
- **Correction:** add "W4's recurrence cap published" to W10's dependencies.

**3. MINOR: §11.2's cap list misses recurrence's caps on the producer.**
- `juniper-recurrence/pyproject.toml:97` and `:106` (at `9b240253`) cap `juniper-data>=0.9.0,<0.16.0` in `[bench]` and `[bench-equities]`.
- Those extras feed `bench/datasets.py`, which §4.4 names as an in-process caller. The caps exclude both 0.16.0 and the block release.

**4. MINOR: §4.2's size figures describe v1's block, not v2's.**
- **Spec text:** "1,155 characters … grows from 2,657 to 3,822 bytes".
- **Source:** v1's P1 reproduces those numbers exactly. v2's block for the same artifact adds `id_nonce`, `min_reader_version` and `pre_carve_order`. It is **1,226 characters**, and the stored file grows 2,657 → **3,881 bytes** (3,888 at `3.1.0`).
- **Correction:** quote v2's figures, or label them as v1's.

**5. MINOR: §7.3 quotes a timing for code that no longer exists.**
- **Spec text:** "`arc_agi` from HF took 511 s (§9.4.6)".
- **Source:** that section of `JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md` recorded 511 s for a *defective* run. It decoded a dataset with the wrong schema and returned an empty (0, 900) artifact.
- **At the pin:** the source is `lordspline/arc-agi`, "~348 KB" (`arc_agi/generator.py:56`), and the old path now raises.
- **Correction:** drop the figure or re-measure.

**6. MINOR: §5.3 overstates what a test pins.**
- **Spec text:** "The first three generators' fallback branch; pinned by `test_normaliser_fit_scope.py:172`".
- **Source:** line 172 is inside `TestCsvImportFitScope`, so it pins csv_import only. equities is pinned separately at `test_equities_generator.py:368`. I found no test pinning equities_seq's fallback (`equities_seq/generator.py:205`).
- **Checker:** passes this row because its token is just `falls_back`.

**7. NIT: two glosses in §6 don't match the code.**
- "`<i4` (24: … dates, report dates and ticker codes)" leaves out `week52_high_date`, `week52_low_date` and `window_end_date`, which are 9 of the 24 keys.
- "`<f8`, `<i8`, `|b1` … for parity with the stores' code" is unsupported: both stores emit float32 only (`hf_store.py:236/245/282`, `kaggle_store.py:217/234`).

**8. NIT: three bare citations point at the wrong file, and the checker can't see them.**
- The checker's coverage regex only matches `name.ext:NN`, so none of the spec's **40** bare `:NN` citations is covered.
- Read by the spec's own convention (a bare `:NN` belongs to the last file named), three land in the wrong place:
  - §3.1 "mnist: `/ 255.0` (`:124`)" follows `core/partition_params.py`, where line 124 is blank.
  - §5.3 "equities (`:395`)" follows `csv_import/generator.py:95`; csv_import line 395 is a `model_copy(max_bytes…)` return.
  - §5.3 "equities_seq (`:194-206`)" lands on csv_import's `_apply_minmax` at line 194.
- **Correction:** write these citations with explicit file names.

**9. NIT: two citations are imprecise.**
- The id format `{generator}-{version}-{16 hex}` is cited to `datasets.py:150`, which is only the call. The format is built at `core/dataset_id.py:61`.
- "Applied … only when `scale > 1.0`" is cited to `hf_store.py:157`. The condition and the loop are at :158-160.

**10. NIT: v2's I1 narrows v1's J2 rather than "repeating" it (§7.2).**
- v1's J2 covered all 16 generators (csv_import built with `file_path="rows.csv"`) and hashed after `bind_deployment_defaults`, as the route does.
- v2's I1 skips csv_import and never calls the binder.

**11. NIT: §14 doesn't flag every deviation from round 1's proposals.**
- Only B-4 is marked "Resolved differently from the proposal".
- B-2 also deviates: v1's §14 proposed that an unknown enum be `unverifiable`, and v2 makes it illegal (L1).

**12. NIT: v1's evidence script now fails at v2's pins.**
- Re-run at the pins, the v1 round-trip script gives 14 PASS, 3 INFO, 1 FAIL. P3 fails with `task_ids dtype is <U5`, because F-1 is fixed.
- §10.1 should say so.

**13. NIT: cascor main moved before the spec was committed.**
- cascor#678 (`0e016a7c`, 15:22) shifted every cited `manager.py` line (4210→4517, 2846→3069, 3739→3966).
- `dataset_shortfall` is now published at two sites, so W7's "beside `dataset_shortfall`" is ambiguous on main.

## Verified correct
- **Citation checker:** 139 (file, line, token) rows, 0 failures; the coverage pass reports no uncovered `name.ext:NN` citation.
- **Sentences:** I checked about 60 against the code. All the listed §3, §5, §7.2, §8.2 and §9.5 sentences hold, apart from those in findings 5, 6, 8 and 9. That includes:
  - mnist's shuffle before the subset;
  - arc_agi's random-order `rng.choice` in the Hub (:183) and local (:215) loaders;
  - csv_import never reordering rows;
  - the HF `scale > 1.0` rule and Kaggle's non-empty-train guard;
  - the store prefixes and the `"unshuffled"` marker;
  - the ratio validation before download;
  - no production caller passing `embargo`;
  - all four storage backends writing `savez_compressed`;
  - every call site sitting inside the function the spec names.
- **PRs, issues and SHAs:**
  - #422 = `ce436819` and #430 = `90ad035e`, which closes #429 and #427. `90ad035e`'s only parent is `ce436819`.
  - #423's quotation is verbatim.
  - canopy#663 = `cc3588a8`, merged 2026-09-23, and records the owner's 2026-09-22 ruling.
  - cascor-client#155 and canopy#584 both merged 2026-09-05.
  - juniper-ml#2043 merged as `8b8d5d94`. Its §14 holds B-1..B-7, R-1..R-7 and C-1..C-4 with the same severities (4 BLOCKER, 8 MAJOR, 2 MINOR = 14 findings).
  - recurrence#185 = `ca9609f0` changed one file, `.github/workflows/ci-recurrence-bench.yml`.
  - `8fa3f95` added arc_agi with `dtype=object`, and `33dffb8e` normalised before carving.
- **Published 0.15.0 wheel:** both stores cut `X[:n_train]` / `X[n_train:]`, emit `X_full`, and normalise before the cut.
- **Version numbers:** 13 generators at `3.0.0`, arc_agi `4.0.0`, the equities pair `5.0.0`, `EXTERNAL_STORE_VERSION` `3.0.0`. PyPI has juniper-data 0.15.0 and juniper-data-client 0.5.0. Every cap and floor §11.2 quotes matches its line.
- **Counts:**
  - Dtype inventory: `<f4` 138 keys, `<i4` 24, `|u1` 18, `<U{n}` 3, across 16 generators, with no 0-d arrays.
  - Reference gate: 52 PASS / 0 FAIL / 0 SKIP at the pin, and 48 PASS / 4 SKIP without a checkout.
  - I1 covers 15 generators.
  - All nine golden digests and the fingerprint `47fba46f…` are reproduced by my own implementation written from §6's prose alone.
  - The other figures match their sources: 511 s, 19 of 60, 40 of 40, 4 distinct rows of 200, and the §10.1 Python/numpy versions of all four named envs.
- **Census (my own sweep):**
  - cascor 3 sites, canopy 2, recurrence 1 client site plus 6 in-process generators, juniper-ml 2 raw fetches plus 1 in-process caller.
  - juniper-deploy, juniper-cascor-worker and juniper-cascor-client have none in production code.
  - Nothing is missing or mislocated. `load_sequence_npz` and the bypassing client methods appear only in tests and ad-hoc scripts.
  - Every reader I checked, including `validate_npz_contract` and `derive_full_split`, ignores an extra `<U` key.

**Changed:** nothing. Everything was read via `git show`, with bytecode writes disabled and temp files redirected. My scratch files, including `independent_digest.py`, `bare_citations.py` and the extracted 0.15.0 wheel, are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/e6c1cb6d-7448-4908-a645-501d40eb9356/scratchpad/specS1/`.
