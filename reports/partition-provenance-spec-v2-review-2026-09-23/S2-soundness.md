# Round 2, lane S2 (soundness) -- final report, verbatim

I'm lane S2, and my verdict is that the v2 spec is **not ready for ratification**. Round 1's B-2 fix holds: a newer or corrupted version number can no longer skip the integrity checks. But the new versioning mechanism breaks on both of its evolution paths, and the exact-prefix fix created a regression.

For every generator's code at the pin, the class rows are true, and no truthful artifact I built was refused. All the refused-although-correct cases below involve a future producer, a new generator or a new store. The accepted-although-wrong cases (Finding 5) apply to today's code.

**What was read.** "Spec" means `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md` at `8c9d65f`. "Gate" means `util/ad-hoc/2026-09-23_partition_provenance_v2_reference_gate.py` at `8c9d65f`. v1 is the same spec file at `8b8d5d94`. The gate's baseline reproduced: 52 PASS, 0 FAIL, 0 SKIP. Vector ids below (A1, C1, …) refer to my scratch scripts, listed at the end.

## Findings

**1. MAJOR — versioning: spec §7.1 contradicts G0 (§9.3).**
- §7.1 says a change to the core MUST come with a new `digest.scheme`, and that a gate that doesn't know the scheme runs only G0 and reports `unverifiable`.
- But G0 itself checks the eight core fields' presence and types, and `digest.algorithm == "sha256"`, before the scheme check.
- A1 (new scheme plus a `blake3` algorithm), A2 (new scheme, `id_nonce` dropped) and A3 (new scheme, `partitions` re-shaped) are all refused by G0, not reported `unverifiable`. That refusal is not overridable.
- So the only sanctioned way to change the core fails closed across every consumer. This is new in v2: v1's G0 simply required `juniper-array-v1`.
- Related (A4): the unknown-scheme stop also skips the check that the block's `dataset_id` equals the requested id, which is a plain string compare. A block for a different dataset comes back `unverifiable`, contradicting §13 item 4's claim that the gate catches "the wrong artifact being served".
- **Fix:** split G0. The first part checks encoding, the two version fields, that `digest` is an object with a string `scheme`, and `dataset_id` against the requested id. The core types and the algorithm move after the scheme check. Freeze the location of `digest.scheme` and the meaning of `dataset_id` across all schemes.

**2. MAJOR — identity: the exact prefix rule (§7.2) contradicts §8.**
- §8 says an unknown generator "gets only the class-independent rules; being unknown is never, on its own, a reason to refuse".
- D1: a third store built through the real `external_dataset_id("openml-61", "openml", …)` gets a non-overridable G4 refusal, because the prefix rule is a two-entry table inside the gate.
- v1's "ends with" check accepted this. v2's fix for round-1 B-7(c) introduced the regression and kept §8's sentence word for word.
- The prefix rules are also missing from §7.1's list of frozen core fields, and they are fragile. `storage/local_fs.py:40` (`_VALID_DATASET_ID`) already rejects ids containing `/`, so `hf-ylecun/mnist-…` cannot be cached on disk today. The natural producer fix (sanitising the name) would make every deployed gate refuse every HF artifact.
- **Fix:** carry `id_prefix` as a core field. Check the prefix exactly for the two known stores; for unknown generators, check only the hash part. List the prefix rules and the `"unshuffled"` marker in the frozen core.

**3. MAJOR — versioning and legality: class rows are keyed on generator name, not version.**
- §7.1 requires raising `min_reader_version` only when a producer "changes the meaning of a legality field, or adds an enum value". A generator that gains new behaviour at a new version does neither.
- C1: mnist `3.2.0` with a train-fitted standardiser is refused ("fit_scope 'train' is not legal for mnist").
- C2: csv_import `3.2.0` with a seeded row sample is refused on `pre_carve_order`.
- K1: L6 is class-independent but keyed on the parameter name `shuffle`. An unknown generator whose `shuffle` means a pre-carve shuffle (the stores' semantics) is refused by L6, which again contradicts §8.
- W6's fleet test runs against the newest published gate, so it cannot catch any of this. Nothing in the spec says a newer gate judges an older block by that block's `schema_version`.
- **Fix:**
  - Key class rows on the generator plus the version range the gate knows, and apply only class-independent rules above that range.
  - Restrict L6 and L7 to known generators.
  - Widen the trigger to "changes the legal combinations for any generator".
  - Run the producer's CI against the oldest supported gate.

**4. MINOR — versioning: legality can be switched off by editing two integers.**
- B0 (`fit_scope: all_rows`) is refused. B1 is the same block with `schema_version` 2 and `min_reader_version` 2, and it comes back `integrity_only`, which is tolerated. No digest has to be recomputed.
- This is round-1 B-2 moved into the legality layer. §13 concedes the unknown-scheme case (item 5) but not this one.
- **Fix:** concede it in §13, or fill a table after the fact (as W11 does) of the highest `min_reader_version` each shipped generator version emits, and refuse anything above it.

**5. MINOR — legality: `fit_scope` is derivable but trusted, and §13 item 2 is false.**
- §13 item 2 says fit scope "cannot be derived from a single artifact". For 16 of 18 sources it follows from the id-bound `params` plus the verified row counts, just as `pre_carve_order` does.
- The gate verifies three false blocks:
  - J1: csv_import with `normalize_features: true` and 6 train rows declaring `none` (the truth is `train`, `csv_import/generator.py:83-92`);
  - J2: mnist with `normalize: false` declaring `constant`;
  - J3: kaggle with `normalize_features: false` declaring `train`.
- None of them hides an illegal state, because `all_rows` cannot be derived either way. That is why this is MINOR.
- **Fix:** derive `fit_scope` wherever `params` decide it. Correct §13 item 2, and G5's "Trusts `method`": `method` is fully derived for every known generator.

**6. MINOR — the W11 table (§11.2, §11.3, §9.4).**
- W11 fills the table with "the versions W6's release actually shipped". That is not the invariant the refusal needs.
- If W6 misses a generator's version bump, or OQ-1 is answered "no", the table records a version that 0.15.0 also shipped without a block. A PATCH release then refuses every legacy artifact at that version, and the refusal is not overridable.
- **Fix:** record a version only if no earlier release shipped that version or a higher one without a block, checked against both wheels. Make W11 conditional on OQ-1 being answered yes.

**7. MINOR — encoding: two decode failures escape G0.**
- §4.1 says "anything else is a malformed block".
- E1 (JSON nested 200,000 deep) raises `RecursionError`. E2 (a 5,000-digit integer) raises the integer-length `ValueError`. Neither is a provenance refusal, and `RecursionError` is not even a `ValueError`, so `except ValueError` call sites crash.
- **Fix:** turn every decode exception into a G0 finding, and bound the text's depth and length.

**8. MINOR — encoding: unknown nested keys are unspecified.**
- The spec only says to ignore unknown top-level fields.
- The gate refuses an extra key in `partitions.train` (F3) but verifies extras in `strategy`, and in `digest`, which is a core field (F1, F2). Two gates that both follow the text can disagree.
- **Fix:** state the rule for each object.

**9. NIT — digest (§6).** The dtype allowlist keys on `dtype.str`. Where `longdouble` is 64-bit (MSVC Windows, macOS arm64) its `.str` is `<f8`, so the required `np.longdouble` refusal vector is digested there, harmlessly, as a float64. I reasoned this rather than ran it: this host's `longdouble` is `<f16`. **Fix:** exclude `dtype.char == 'g'`, or make the vector host-conditional.

**10. NIT — §9.4's right-to-left id parse fails open.** A dashed generator name (G1, `multi-sine`) and a newline inside a store prefix (G2) both come back `absent` rather than refused. **Fix:** have G0 require `generator` to match `[a-z0-9_]+`.

**11. NIT — §9.2, §9.5 and §8.**
- `dataset_id` is optional in the interface, so the stripped-block refusal is opt-in at each call site. Make passing it a MUST at §9.5's sites.
- §8 says the id re-derivation "authenticates" the generator. The id hash is 64 bits, so a crafted colliding pair costs about 2^32 hashes. It binds against accidents, not deliberate forgery.

## Claims I tried and could not refute
- **The seed test `params.get("seed") is None` is right for everything at the pin.**
  - pydantic always fills in `seed` for all 16 generators and turns `True`, `7.0` and `"7"` into ints. The five sequence synthetics reject a null seed.
  - The stores' hashed seed is always an int or `"unshuffled"` (`operator.index`).
  - The gate's re-derivation equals the real `generate_dataset_id` with seed 0, seed null and seed absent.
- **The prefix rules match `hf_store.py:177-178` and `kaggle_store.py:270` exactly.** A `-` or the marker string inside a name cannot break G4 or the right-to-left parse.
- **Every `pre_carve_order` derivation is true of the code:**
  - mnist shuffles whenever a seed is set (`mnist/generator.py:115-116`);
  - arc_agi reorders only with both a seed and `n_tasks`, on both paths, including `n_tasks` at or above the task count (a full permutation);
  - the stores shuffle only when a seed is given;
  - csv_import and equities never reorder: equities' ticker list is sorted and its seed is unused.
- **L6 holds at the pin:** all nine generators with a `shuffle` param pass it straight to the carve, which permutes only when it is true.
- **L3 cannot be violated:** both equities normaliser fallbacks are global, so a fallback always means zero train rows or windows. The other boundary cases also match §5.3: csv_import with every partition empty is `none`, HF with a train maximum of at most 1 is `none`, and arc_agi has no normalise parameter at all.
- **§9.4's "at or above the first emitting version means a block is present" holds on the producer side:** the only artifact writers are the create route (`datasets.py:355`) and the two store loaders, the cached store re-saves every key, and no storage backend filters keys.
- **Digest:** the header is unambiguous, bools are hashed by value, and trailing NULs, big-endian input and 0-d shape are all handled.
- **Encoding:** the duplicate-key, canonical-form and strict-int rules are implemented as written.
- **Integrity runs whatever `schema_version` says,** so a newer or corrupted version number cannot hide a corrupted array.

## Verdict by layer
| layer | verdict | why |
| --- | --- | --- |
| Identity | Sound with findings | Sound at the pin. Finding 2 is a regression v2 introduced |
| Versioning | Unsound, but fixable | Round-1 B-2 is fixed, but both evolution paths (a new scheme, changed legality) wrongly refuse legitimate newer blocks (Findings 1 and 3) |
| Legality | Sound with findings | Findings 3 and 5 |
| Digest | Sound | Finding 9 is a NIT |
| Encoding | Sound with findings | Findings 7 and 8 |

Nothing in any repo was changed. These scratch files are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/e6c1cb6d-7448-4908-a645-501d40eb9356/scratchpad/specS2/`:
- `attack_s2.py`
- `attack_s2_b.py`
- `probe_seed_types.py`
- `ref_gate.py`
- `spec_v2.md`
- `spec_v1.md`
