# Round 2, lane S4 (fold completeness) -- final report, verbatim

I have everything I need. Final report follows.

---

# Lane S4 review of spec v2: fold completeness and amputation

**Verdict: COMPLETE WITH FINDINGS.** All fourteen findings are folded. Nothing was dropped outright. Two folds are partial and three were decided differently, one of them without a label. The three MAJORs below (D1–D3) should be fixed before the owner rules.

The spec is `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md`: v1 at `8b8d5d94`, v2 at `8c9d65f`. Bare § numbers below refer to v2. I read everything through `git show` and changed nothing.

To check the folds I:
- ran a sentence-level diff of v1's §1–§13 and §15 against v2;
- re-ran `util/ad-hoc/2026-09-23_partition_provenance_v2_reference_gate.py` without a juniper-data checkout (48 PASS, 4 SKIP, which matches §10.2);
- probed that gate for D1;
- re-read the cited source lines at v2's pins.

## Fold table

| id | status | evidence |
|---|---|---|
| B-1 | FOLDED | The stores are now legal with a train fit (§5.3, §5.4, §8.2). `method` now covers only the carve's own permutation, and the new `pre_carve_order` is derived from `params` (§5.2, §8.2, L8). v2 also gave mnist, arc_agi and csv_import their own rows, so it took both proposed alternatives. |
| B-2 | FOLDED, except (iv) REVERSED | The G0 int checks, the scheme-keyed G1–G4 and `min_reader_version` are all in. v1 proposed "an unknown enum makes the block `unverifiable`, not illegal"; v2 makes it **illegal** (§7.1). The reason given is valid, but §14 doesn't flag the change (D4). |
| B-3 | FOLDED | `id_nonce`, an unconditional G4, and W6's nonce argument plus a returned dict. Only two callers of `generate_dataset_id` exist at `90ad035e` (the route and `external_dataset_id`), so the fold covers everything. |
| B-4 | FOLDED DIFFERENTLY | The table is filled after the release (W11). The reason (§11.1) is valid, and §14 labels it. |
| B-5 | PARTIAL | The exact allowlist and the nine refusal vectors are in. The stores' dtypes are never stated (D5). |
| B-6 | FOLDED | §4.1, §5.1, L5. |
| B-7 | FOLDED, except (d) DIFFERENTLY | (a), (b) and (c) are in. For (d), v2 took neither proposed option. Its reason holds: at recurrence `9b240253` only tests call `load_sequence_npz`. The departure is unlabelled (D4). |
| R-1 | FOLDED, except (iii) PARTIAL | W12 is added and `bench/datasets.py` is declared. The claimed census re-run has no recorded evidence (D6). |
| R-2 | FOLDED, for OQ-2 only | The same defect is still open for OQ-1 (D3). |
| R-3 | FOLDED | W7–W9. The new W12 brings the gap back (D7). |
| R-4 | FOLDED DIFFERENTLY | 4.0.0 then 4.1.0, instead of v1's example "3.0.1, say". #430 shipped 4.0.0, so this is valid. |
| R-5 | FOLDED | §16 plus W3, which sits outside the claimed "§1–§13". |
| R-6 | FOLDED | §8.3, W7. The citations `settings.py:557` and `manager.py:3739` hold at `f7a6d573`. |
| R-7 | FOLDED | A grep finds no remaining "#422's head" wording. |
| C-1..C-4 | CORRECT | At `90ad035e` / `9bc8870a`: `hf_store.py:199` and `kaggle_store.py:288` (`save`); `:162` and `:256` (`params = {`); `exceptions.py:82`; `hf_store.py:282` (`/ 255.0`). |

## Defects

**D1. MAJOR: §7.1 and §9.3 contradict each other.**
- §7.1 says a change to the integrity core "MUST come with a new `digest.scheme` name", and that a gate which doesn't know the scheme "can check nothing but G0, and reports `unverifiable`".
- But G0, which runs *before* the scheme check, requires "the eight core fields present with their JSON types; `digest.algorithm` is `sha256`".
- Probing the reference gate with a new scheme name:
  - `algorithm: blake3` is REFUSED at G0;
  - dropping `id_nonce` is REFUSED;
  - reshaping `partitions` is REFUSED.
- None of these is overridable. The gate's own `CORE_FIELDS` comment promises "unverifiable", and no vector tests this case (B2.f changes only the scheme string).
- **Fix:** limit G0 to decoding, the version fields and a string `scheme`. Move the core-field and `algorithm` checks into the scheme stage, and add a vector for "unknown scheme with a changed core gives `unverifiable`".

**D2. MAJOR: v1's §7.1 versioning rules were dropped, with nothing replacing them.**
- Lost text: "When it changes. Only when a v1 reader would misjudge…", "Adding a field does not change it", "A gate MUST verify every schema version up to its own", "a producer upgrade cannot break an older consumer".
- v2 says only that the legality layer "may change with `schema_version`". It never says when `schema_version` increments. It never requires a gate to judge older schema versions; that appears only as "the producer's promise".
- The two version fields sit in neither the frozen core nor the legality layer.
- The reference gate's B2.c bumps `schema_version` to 2 for an added field, which is the opposite of v1's rule. So the rule was changed, not superseded.
- **Fix:** restore an increment rule, a gate obligation ("judge every schema from 1 to `GATE_SCHEMA_VERSION`") and frozen version fields.

**D3. MAJOR: the body decides OQ-1 while claiming to decide nothing.**
- The header says the document "decides none of them".
- Yet §9.2 exports `FIRST_EMITTING_VERSION`, defined as "the per-generator table of §7.3", which is OQ-1's recommendation.
- W11, §11.2's "0.6.0 → 0.6.1 (W11)", §1 item 8, §13 item 10 and §5.5's `spiral-3.1.0` are all written unconditionally.
- Only §9.4's row and OQ-1's evidence mention the dependency. This is R-2's defect class, fixed only for OQ-2.
- **Fix:** mark these conditional on a yes to OQ-1, and write out what happens on a no.

**D4. MINOR: §14 doesn't label two folds that departed from the proposals.**
- B-2's row, "An unknown enum at a readable version is illegal", reverses v1's proposal.
- B-7(d) took neither of the two proposed options.
- Only B-4 carries the "Resolved differently" label.

**D5. MINOR (the B-5 partial): §6's reason for three dtypes is unsupported.**
- §6 says "`<f8`, `<i8` and `|b1` are admitted … for parity with the stores' code".
- But the stores emit `<f4` only: `hf_store.py:236/242/245/282` and `kaggle_store.py:222/231/234`.
- `util/ad-hoc/2026-09-23_partition_provenance_dtype_inventory.py` says the stores' dtypes are "stated separately in the spec". They are not.
- **Fix:** state the stores' dtypes with citations, and either justify the three extra dtypes or drop them.

**D6. MINOR (the R-1 partial): the census re-run is claimed but not evidenced.**
- §9.5 says "This census was re-run…" but records no repo set, no search patterns and no script.
- My own sweep found juniper-deploy's `tests/test_data_service.py:113,123,134` fetching raw `/artifact`. They are neither listed nor declared as non-consumers. They are safe, because they read named keys only.
- **Fix:** record the swept repos and patterns, and declare the deploy tests.

**D7. MINOR: two §9.1 statements went stale when W12 was added.**
- "only one of the three consumers": there are now four.
- "Every consumer already depends on the client": the plot loaders fetch through `_http_bytes`, not the client.
- W12 names no client dependency or floor, which brings back R-3's gap.

**D8. MINOR: §4.3's reader list is incomplete.**
- "No existing reader breaks on an extra `<U` key" lists four readers. It omits recurrence's `validate_npz_contract` and `sequence_data_from_arrays`, and the plot loaders.
- §11.1's "Either order is safe" depends on that list.
- I checked the omitted readers: all read named keys, so the conclusion holds. They just need adding.

**D9. MINOR: the vector coverage is overstated.**
- The header says "vectors for every round-1 finding", and §10.2 says "each round-1 finding".
- Vectors exist only for B-1..B-7, and not for B-7(d).

**D10. MINOR: §9.3 omits the stripped-block refusal.**
- §9.3's "Checks, in order" leaves out the first check that actually runs: the absent/stripped-block refusal.
- That refusal has no id, and §8.3's list of non-overridable failures, "G0–G4", misses it.

**D11. MINOR: OQ-6 argues against the kind of switch v2 itself adds.**
- OQ-6 argues that "A report-only mode is a switch someone can forget to turn off".
- Yet W11 is exactly that kind of switch. Nothing ties it to W6's release, and no floor rises to 0.6.1.

**D12. MINOR: §5.3 contradicts §3.1 note 4.**
- §5.3's train row says equities_seq fits "whenever train is non-empty".
- §3.1 note 4 says a train fit with zero train windows is correct.

**D13. MINOR: the juniper-data version will collide.**
- §11.2 says "0.15.0 → 0.16.0", and W10 floors `juniper-data>=0.16.0` "so that… a producer that emits the block" gets installed.
- But #422 (breaking) and #430 are merged and unreleased, so the next release takes 0.16.0 without blocks. This is R-4's collision class, at package level.

**D14. MINOR: provenance was amputated.**
- v1's pins (`68c3cd7`, `e052ef8`, `2f973ca2`, `1c84c40`, `11e45297`) are gone. §10.1 still says "editable installs of the v1 checkouts" without naming them.
- numpy's quoted warning ("Custom dtypes are saved as python objects using the pickle protocol") was cut. Check E4 still carries the underlying fact.

**D15. NITs**
- "folds … into §1–§13", but R-5 went to §16.
- "in two layers", but §1 item 2 lists three groups.
- The spec says I1 covers "15 generators"; the check asserts only ≥10.
- §13 item 2: "None of them can be derived" versus "(pre_carve_order entirely)".
- §13 item 8: "Legacy artifacts stay unverifiable", but they report `absent`.
- The recurrence gate moved from after `validate_npz_contract` to before it with no disposition. The move is harmless.
- §2's seeded-id non-goal cites I2, which is the unseeded check.
- §14 places C-4 "during round 1"; v1 says a later lane found it.
- The ids L1/L2 and B3 each name both a check and a rule or finding.
- `juniper-array-v1` was redefined (the dtype set, and `|b1` hashed by value) under an unchanged name. That is acceptable only because v1 never shipped, and the spec should say so.

## Files
- **Changed:** none.
- **Scratch:** `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/e6c1cb6d-7448-4908-a645-501d40eb9356/scratchpad/specS4/` holds `sentdiff.py` and `probe_scheme.py` (the D1 probe). This is session-local. Under the ecosystem's script-placement rule, copy them to `util/ad-hoc/` if they should be kept.
