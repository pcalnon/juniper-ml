# Extraction — P5 partition arc / Decision 12

<!-- markdownlint-disable -->

> **Archived verbatim.** An extraction report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Corrections found by validation are in the `round*-reconciliation.md` files in this directory, and the plan's §10. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

measured_at: 2026-10-04T20:53Z–21:05Z. Tools: `gh api` REST and the search API (no GraphQL), PyPI JSON, and `cat`/`grep`/`ls` on local files. No scripts, tests or services were run, and no git command targeted another repo.

Aliases: **HO** is `HANDOFF_2026-10-03_partition-arc-decision-12-consolidated.md`. **SPEC** is `notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md`. **EQ** is `notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md`; its "P1–P5" labels are its own phases, not development paths.

## 0. Sources read

- HO (`prompts/thread-handoff_automated-prompts/`): read in full, lines 1–256.
- `HANDOFF_2026-10-03_INDEX_consolidated-development-paths.md`: read in full.
- SPEC v0.2.0: read in full, lines 1–733.
- `HANDOFF_2026-09-24_partition-arc-spec-v2-round-2-recorded-v3-next-three-prs-await-0-16-0.md` (H-0924): read in full.
- `HANDOFF_2026-09/HANDOFF_2026-09-23_partition-arc-residue-stores-conformed-canopy-advisory-decision-12-spec-unsound.md` (H-0923): read in full.
- `HANDOFF_2026-09/HANDOFF_2026-09-09_partition-arc-decision-11-release-train-cut-six-gates-await-owner.md` (H-0909): §10 only (lines 283–537), which includes §10.2 and §10.5.
- `reports/partition-provenance-spec-v2-review-2026-09-23/`:
  - `README.md` and `S3-executability.md`: in full;
  - `S1-grounding.md`: findings 1–3 and 12–13, plus the finding headings;
  - `S2-soundness.md` and `S4-fold-completeness.md`: finding headings only.
- `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_TRAIN-EVAL-TEST-PARTITION-DESIGN.md`: §9.6.3–§9.6.6.
- `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_PARTITION-IMPLEMENTATION-PLAN.md`: §9 (S-1 to S-5) and §10 "Still open" with its 2026-09-23 update.
- `notes/JUNIPER_2026-08-29_JUNIPER-ECOSYSTEM_GATED-MEASUREMENTS-RESULTS.md`: grep only.
- `HANDOFF_2026-10-03_defect-register-round-42-consolidated.md` (P3): lines 1–80, plus a grep for `routes/datasets`.
- `HANDOFF_2026-10-03_perf-lane-consolidated.md` (P6): lines 40–80, plus grep.
- `HANDOFF_2026-10-03_release-and-distribution-consolidated.md` (P4): grep only.
- EQ: header (lines 1–40), plus a grep for overlap.
- GitHub:
  - juniper-data #423 (with its comments), #424, #434 and #431 (commit lists);
  - data-client #213;
  - cascor #677 (the plan comment, in full) and #582;
  - juniper-ml #2034 (body and comment) and #2064 (body);
  - recurrence #178 (with its closing comment) and #188;
  - run 37114403856 (its jobs and steps).
- **Could not read**: lane D's round-3 report on #431, #434 and #212. It was never archived (H-0924 §3).

## 1. Work items

| ID | Item | Source | Live status | Gate | Depends on | Repo(s) | Effort | Criticality |
|---|---|---|---|---|---|---|---|---|
| P5-01 | Write spec v3: fold §15's ten MAJOR clusters (rows a–j) into §1–§13; add a §14-style round-2 disposition table | HO goal item 1; SPEC §15 | [VERIFIED 2026-10-04: SPEC at main `cf711cf4` reads `Version 0.2.0`, with 10 `R2-` rows; `git ls-remote --heads` finds no provenance/partition/v3 branch; search finds no PR] | STARTABLE | — | ml | L | UNBLOCKER |
| P5-01a | R2-1: split G0 so decoding, the version fields, a string `digest.scheme` and the requested-id compare all run before the scheme check; add the vector | SPEC §15 (S2-F1, S4-D1) | as P5-01 | as P5-01 | — | ml | in P5-01 | DATA-INTEGRITY |
| P5-01b | R2-2: restore the `schema_version` increment rule and the duty to judge every schema up to the gate's own; freeze the version fields | §15 (S4-D2) | as P5-01 | as P5-01 | — | ml | in P5-01 | DATA-INTEGRITY |
| P5-01c | R2-3: key class rows on generator plus version range; restrict L6/L7 to known generators; run producer CI against the oldest supported gate | §15 (S2-F3) | as P5-01 | as P5-01 | — | ml | in P5-01 | DATA-INTEGRITY |
| P5-01d | R2-4: carry the store prefix in the core and check it exactly only for known stores; freeze the prefix rules and `"unshuffled"` | §15 (S2-F2) | as P5-01 | as P5-01 | — | ml | in P5-01 | DATA-INTEGRITY |
| P5-01e | R2-5 / HO (c): make W11 and `FIRST_EMITTING_VERSION` conditional on OQ-1 = yes, and write the "no" branch; bump each VERSION in its emission PR; fill W11 from W6's verified list | §15; HO 1(c) | as P5-01 | as P5-01 | — | ml | in P5-01 | DATA-INTEGRITY |
| P5-01f | R2-6 / HO (a): the floor is "the first juniper-data release whose wheel emits the block"; pin the number only at the cut | §15; HO 1(a) | [CHANGED SINCE HANDOFF: EQ W1.11 (EQ:389) now plans juniper-data **0.17.0** for X8, without the block] | as P5-01 | P4, EQ | ml | in P5-01 | UNBLOCKER |
| P5-01g | R2-7 / HO (b): W10's precondition is a recurrence release carrying W4's cap, plus an `[all]` dry-run. Also handle juniper-ml `[recurrence]` `<0.6.0` against a recurrence 0.6.0 (S3-F1) | §15; HO 1(b) | [VERIFIED 2026-10-04: ml `pyproject.toml:105` reads `juniper-recurrence>=0.5.0,<0.6.0`] | as P5-01 | P4, EQ | ml | in P5-01 | UNBLOCKER |
| P5-01h | R2-8: a W6 CI job that tests against the PUBLISHED client | §15 (S3-F2) | [VERIFIED 2026-10-04: data `ci.yml:273,434,494,601,905` still install the client `@main`] | as P5-01 | — | ml | in P5-01 | DATA-INTEGRITY |
| P5-01i | R2-9 / HO (d): drop "0.6.1 is a PATCH"; either release a MINOR or ask the owner in §16 | §15 (S3-F4) | as P5-01 | as P5-01 | OD-7 | ml | in P5-01 | HYGIENE |
| P5-01j | R2-10 / HO (e): name, per consumer and for both OQ-2 answers, a status field, a setting and a caveat slot that something reads; add a canopy line to §16 | §15 (S3-F5) | [NOT RE-PROBED — S3-F5: cascor's `_validation_warning` is written but never read] | as P5-01 | — | ml | in P5-01 | DATA-INTEGRITY |
| P5-02 | Fold every MINOR and NIT, each by lane id: S1-F3…F13, S2-F4…F11, S3-F6…F12 and S4-D4…D15. This includes the lock pins (S3-F9), the docs/CHANGELOG/deploy-tag/operator-note omissions (S3-F11), and the clash with the existing `juniper_data/provenance.py` (S3-F12) | §15 | [VERIFIED 2026-10-04: §15 unchanged; all 4 reports present] | STARTABLE | P5-01 | ml | M | HYGIENE |
| P5-03 | Fold four inputs that no round has reviewed (see the list after this table) | HO 1(f); this extraction | [VERIFIED 2026-10-04: probes listed after this table] | STARTABLE | P5-01, EQ | ml | S | DATA-INTEGRITY |
| P5-04 | Add a vector per R2 cluster to `util/ad-hoc/2026-09-23_partition_provenance_v2_reference_gate.py`. R2-1's: an unknown scheme with a changed core is `unverifiable` | HO 1 | [NOT RE-PROBED — not run. The 52-PASS result is corroborated only by `S3-executability.md:5`. The lanes' scratch scripts are gone (`README.md`), so rebuild the vectors from the report text] | STARTABLE | P5-01 | ml | M | UNBLOCKER |
| P5-05 | Re-pin `…_v2_citation_check.py` (`PINS`, :44-50) to the main heads at freeze time | HO 1 | [CHANGED SINCE HANDOFF: heads are now data `29be6d35`, data-client `75f15a62`, cascor `95cdc562`, canopy `1b2dd438`, recurrence `be081fae` (unchanged) and ml `cf711cf4`. The siblings' local `origin/main` refs equal these heads] | STARTABLE | P5-01 | ml | S | HYGIENE |
| P5-06 | Review round 3: fresh lanes on frozen v3, at least one on identity/versioning/legality; archive every report verbatim; record in a new section | HO 1; traps | [VERIFIED 2026-10-04: v3 does not exist] | BLOCKED-ON P5-01..05 | P8 (soft) | ml | M | UNBLOCKER |
| P5-07 | Post v3 and round 3's outcome on juniper-data#423 | HO "Mirror rulings" | [VERIFIED 2026-10-04: #423 OPEN, 2 comments, the last on 2026-09-23T21:21Z (round 2)] | BLOCKED-ON P5-06 | — | data (issue) | S | HYGIENE |
| P5-08 | W3: the owner rules in SPEC §16 (OD-1…OD-7), mirrored on #423 | SPEC §16, W3 | [VERIFIED 2026-10-04: every §16 row is "—" except OQ-4] | OWNER-DECISION; BLOCKED-ON P5-06 | — | ml, data | S | UNBLOCKER |
| P5-09 | New juniper-data PR from fresh main carrying #434's round-3 NITs (see the notes after this table) | HO goal item 2 | [VERIFIED 2026-10-04: main has only the weak `test_cached_store.py:187`; main's bound test (:214-237) has no `exc_info` check; the #434 worktree holds the strict form (:188, :238) and the wording (CHANGELOG :29-30); main's wording sits at `CHANGELOG.md:407`, inside `[0.16.0]` (:161-421); #434 merged at head `ae5a3b18`, whose last real commit is `ac6bdc8b`] | STARTABLE (merge: OWNER-ACTION, a per-session grant) | P3 item 1 (CHANGELOG `[Unreleased]`) | data | S | HYGIENE |
| P5-10 | Optional: lock the cached store's warned-id set (a round-3 NIT judged benign) | HO #434 residue | [UNVERIFIED — from H-0924; lane D's report is unarchived] | STARTABLE | — | data | S | HYGIENE |
| P5-11 | ml#2064: show `eval_metrics.final` (split, n_samples) in `stats_summary.py` `eval_scalars` (:225) and `plots_cascor.py` `render_eval_metrics` (:193); label the in-loop scores; make a run with no `final` block say so; add tests | HO goal item 3 | [VERIFIED 2026-10-04: #2064 OPEN with 0 comments; both sites still read the top-level (in-loop val) f1/precision/recall/roc_auc; no PR] | BLOCKED-ON P6 (index rule for `util/experiments/`) | P6 item 4 (same file) | ml | S | DATA-INTEGRITY |
| P5-12 | ml#2034 step 3: re-measure the pre-decision-11 corpora (T6, the P3 thresholds, attribution), pinning `sizing_mode: carve`; then close #2034 | HO 3; #2034 comment | [VERIFIED 2026-10-04: #2034 OPEN; step 2 is ml#2066, merged as `f9c81d80`] | BLOCKED-ON P5-11 | P6 (box time); P5-13 (the B−A input) | ml | L | RESEARCH |
| P5-13 | V-3 compute per cascor#677's plan (see the notes after this table) | HO goal item 4 | [VERIFIED 2026-10-04: #677 OPEN, plan only, no PR. At 21:00Z: load 3.43/3.60/3.14 on 16 cores and `clamscan` running about 9.9 h, so by P6's definition this is not a quiet window; no `:8230` listener] | WAIT-QUIET-WINDOW | P6 (PF-3 needs the same windows) | cascor, ml | M | RESEARCH |
| P5-14 | data-client follow-ups to #212: reword the `ci.yml:801` comment to "a later run in the receiver's concurrency group"; add `--max-time` at :817, :828 and :839; find an owner for #213 | HO goal item 5 | [VERIFIED 2026-10-04: both still true on `75f15a62`; #213 is OPEN with no PR] | STARTABLE (optional) | — | data-client | S | HYGIENE |
| P5-15 | Fix cascor-worker's stale fallback `__version__` | HO goal item 6 | [CHANGED SINCE HANDOFF: juniper-data's fallback is now `"0.16.0"`, which matches its version. cascor-worker `__init__.py:35` is still `"0.6.0"` against 0.6.1] | STARTABLE | — | cascor-worker | S | HYGIENE |
| P5-16 | recurrence `load_sequence_data` promises `ValueError`, but a `KeyError` escapes data-client `contract.py:72` | HO 6 | [VERIFIED 2026-10-04: the docstring is at ~:69-71; `contract.py:72` reads `arrays[f"{NPZ_KEY_X}_train"]`] | STARTABLE | EQ W0.6 / F-S9 (same function) | recurrence or data-client | S | HYGIENE |
| P5-17 | cascor `publish.yml`'s TestPyPI check imports from the checkout | HO 6 | [VERIFIED 2026-10-04: checkout, then `from juniper_cascor import __version__` (:51) at the repo root, where `juniper_cascor/` exists. Since cascor#672 (unreleased) the printed value comes from metadata, so only the import path is wrong] | STARTABLE | — | cascor | S | HYGIENE |
| P5-18 | Release cuts: cascor (#672), canopy (#663), juniper-data next (#437 X8, #436, #438, #440 and P3's fix-forward), recurrence (the #188 `<0.17.0` cap) | HO owner list | [VERIFIED 2026-10-04: PyPI cascor 0.11.0, canopy 0.8.1, data 0.16.0, recurrence 0.5.0, with no newer GitHub Releases; data main is 9 ahead of v0.16.0 and recurrence main 19 ahead of v0.5.0] | OWNER-ACTION | P4; the data cut needs P3 item 1 | cascor, canopy, data, recurrence | M | UNBLOCKER |
| P5-19 | data#424: does §6.2's generate-shortfall survive decision 9, or is canopy's disabled "Fill synthetically" retired? | HO owner list | [VERIFIED 2026-10-04: #424 OPEN with 0 comments; canopy `validation_gate.py:50` holds the reason, and :110-113 disable the option] | OWNER-DECISION | P2 | data, canopy | S | USER-FACING |
| P5-20 | Close cascor#582, with #677 as its residue? | HO owner list | [VERIFIED 2026-10-04: OPEN, last activity 2026-08-29] | OWNER-DECISION | P4 item 7 | cascor | S | HYGIENE |
| P5-21 | W4: widen the client caps `<0.6.0` in canopy (`pyproject:192`, an extra) and recurrence (`:54`, core) | SPEC §11.3 | [VERIFIED 2026-10-04: both caps are on main] | BLOCKED-ON P5-08 | EQ W1.13 may widen them first | canopy, recurrence | S | DATA-INTEGRITY |
| P5-22 | W5: data-client `provenance.py`, with fakes that mint re-derived ids, the vector tests, and a release | §11.3 | [VERIFIED 2026-10-04: PyPI 0.5.0; main is 23 ahead, CI-only changes] | BLOCKED-ON P5-08, P5-21 | EQ (contends for 0.6.0) | data-client | M | DATA-INTEGRITY |
| P5-23 | W6: the producer (builder, nonce argument, `partition_facts` in 16 generators, route insertion, store builders, VERSION bumps, fleet tests), then a release | §11.3 | [VERIFIED 2026-10-04: no code exists; the insertion point is now `routes/datasets.py:390-392`] | BLOCKED-ON P5-22 and P3 item 1 | P3, P4 | data | L | DATA-INTEGRITY |
| P5-24 | W7: cascor's three call sites, setting, `get_status()` field and floor; about 20 tests break (S3-F7) | §11.3 | [NOT RE-PROBED — the `manager.py` lines moved at `0e016a7c` and since] | BLOCKED-ON P5-22 | P6 PF-2 axis 1 (`manager.py`) | cascor | M | DATA-INTEGRITY |
| P5-25 | W8: canopy's two download sites (OQ-5) and floor | §11.3 | [NOT RE-PROBED] | BLOCKED-ON P5-22 | P2 | canopy | S | DATA-INTEGRITY |
| P5-26 | W9: the recurrence call site, the `load_sequence_npz` docstring, and floor | §11.3 | [NOT RE-PROBED] | BLOCKED-ON P5-22 | EQ (same function) | recurrence | S | DATA-INTEGRITY |
| P5-27 | W10: the meta-package floors (`[clients]` :67, `[servers]` :86), an `[all]` dry-run, and widening `[recurrence]` if needed | §11.3; R2-7 | [VERIFIED 2026-10-04: :67 reads `>=0.5.0`, :86 reads `juniper-data>=0.15.0`; `publish.yml` checks only `[clients]` (:195) and `[tools]` (:202)] | BLOCKED-ON P5-22 and P5-23 published, plus P4's recurrence release | P4; EQ (juniper-ml 0.11.0 edits the same lines) | ml | M | UNBLOCKER |
| P5-28 | W11: fill `FIRST_EMITTING_VERSION` from what was shipped and verified; MINOR release; consumer floors and a lock refresh (S3-F9) | §11.3 | Conditional on OQ-1 = yes | BLOCKED-ON P5-23 published, P5-08 | — | data-client and consumers | S | DATA-INTEGRITY |
| P5-29 | W12: the ml plot loaders run the gate and record its status, and never refuse | §11.3 | [NOT RE-PROBED] | BLOCKED-ON P5-22 and P6 coordination | P6 | ml | S | DATA-INTEGRITY |
| P5-30 | Correct stale docs of record: `docs/REFERENCE.md:5789` ("v1 draft"), `:5792` (stores "not yet released", but they shipped in 0.16.0), and the 2026-09-23 update in the plan's §10 | residue | [VERIFIED 2026-10-04: grep on main] | STARTABLE | — | ml | S | HYGIENE |
| P5-31 | Remove merged-task worktrees: data #431, data-client #212, ml `warm-prancing-yeti` and `rippling-wobbling-torvalds` (check first), and #434 only after P5-09. Keep `…spec-v2-pin…90ad035e` | HO Git state | [VERIFIED 2026-10-04: all exist (`ls`); dirty state not probed] | OWNER-ACTION (isolated sessions are refused cross-worktree git) | P5-09 | data, data-client, ml | S | HYGIENE |
| P5-32 | At the next data release, check that the release-event notify job's "Confirm the consumer started a run" step and the recurrence bench run are both green | HO owner item (closure bar) | [CHANGED SINCE HANDOFF: recurrence#178 was CLOSED 2026-10-03T10:16Z by pcalnon on `workflow_dispatch` run 37114403856 (4/4 steps success) and bench run 37114410788. No release-event run has happened since] | BLOCKED-ON P5-18 | P4 | data, recurrence | S | HYGIENE |

**P5-03: the four unreviewed inputs.**

- **(i) Restate S1-F3.** Recurrence main caps `juniper-data<0.17.0` in `[bench]` and `[bench-equities]` (`:97`, `:106`, via #188). PyPI 0.5.0 caps it at `<0.12.0`.
- **(ii) `equities_seq` is at `6.0.0`.** Its `generator.py:56` reads `6.0.0`, so its first emitting version is `6.1.0`, not §7.3's `5.1.0`. The allow-list is now at `test_val_emission_guards.py:300` and includes `equities_seq: 6.0.0`.
- **(iii) data-client 0.6.0 is contested.** EQ claims it for validator changes (EQ:382, :391). Name the gate's release generically.
- **(iv) Route citations have drifted.** `generate_dataset_id` is now at `:242` (SPEC cites `:150`), the pops are at `:379-390` (SPEC: `:287-298`), and `compute_checksum` is at `:392` (SPEC: `:300`).

**P5-09: what the PR carries.**

- The strict assertion `exc_info and exc_info[0] is not None` at `test_cached_store.py:187`.
- The same check in the bound test.
- The CHANGELOG `/versions?name=` fix, as a new `[Unreleased]` note or dropped. Never edit `[0.16.0]`.

**P5-13: the plan to follow** (cascor#677):

- Run the B/B′ identity check on two seeds first.
- Then run B and C over seeds 42–49 (16 runs); A is derived.
- Use a private juniper-data instance.
- Set `max_epochs` and `output_epochs` to the same value.
- Write the result up beside V-2.

## 2. Owner decisions pending

| ID | Question | Options, and the source's recommendation | Blocks | Source |
|---|---|---|---|---|
| OD-1 | Ratify the spec | Only after round 3 rates v3 ratifiable | W3 → W4–W12 | SPEC §16; HO |
| OD-2 | OQ-1: bump VERSION when emitting? | Yes, MINOR: 3.1.0; arc_agi 4.1.0; equities 5.1.0; the stores 3.1.0. `equities_seq` is now at 6.0.0, so its target would be 6.1.0 (P5-03 ii) | W11 / the stripped-block refusal; W6's bumps | §7.3, §12 |
| OD-3 | OQ-2: refuse with a recorded override, or warn only? | Refuse by default, with a recorded override. v3 must spell out the "warn only" signature (S3-F10) | W5, W7–W9 surfaces | §8.3, §12 |
| OD-4 | OQ-3: `source_sha256`? | Yes for csv_import; defer HF/Yahoo/SEC | W6 | §12 |
| OD-5 | OQ-5: does canopy call the gate? Plus a new §16 line: does canopy enforce legality, or only advise? | Yes, at both sites. The legality-refusal mode is open (R2-10) | W8 | §12, §15 |
| OD-6 | OQ-6: enforce from the first release? | Enforce. "Report-only" has no mechanism yet (S3-F10) | W5/W6 | §12 |
| OD-7 | The number for W11's release | The owner's rule (cascor-client#155) says a MINOR; v3 may still put the question to the owner | W11 | §15 R2-9 |
| OD-8 | data#424 | Build §6.2's generate-shortfall, or retire canopy's disabled option | canopy UI | HO |
| OD-9 | Close cascor#582, with #677 as its residue? | — | — | HO |
| OD-10 | The four release cuts (P5-18) | — | P5-27, P5-32 | HO |
| OD-11 | A merge grant for each session (P5-09, P5-11, the v3 PR) | — | merges | HO traps |

## 3. Cross-path dependencies

- **P5 → P4.**
  - P5-18 is the four cuts.
  - P5-27 needs a recurrence release carrying a widened client cap.
  - P5-01f and P5-03(iii) need the numbers P4 actually cuts.
  - P5-32 rides the next data release.
- **P4 → P5.** P4's item 7 also carries #582 and #423 as owner questions.
- **P5 → P3.** The `routes/datasets.py` dependency appears only in the index and in P3's handoff, not in HO.
  - P5-23 (W6) must follow P3's item 1, the data fix-forward. Its branch `fix/conditional-requests-round4-followups` is at `94ce8b1f` and touches `routes/datasets.py`. It has no PR and is now **2 ahead / 6 behind** main.
  - P5-09 shares data `CHANGELOG.md` `[Unreleased]` with that branch.
  - The next data release (P5-18) waits on P3's item 1.
- **P5 → P6.**
  - P5-11 and P5-29 edit `util/experiments/`. P6's item 4 (APD-ML-005/-006) also edits `stats_summary.py`.
  - P5-12 and P5-13 need box time, and P5-13 needs a quiet window that PF-3 also wants.
  - P6's handoff says "No dependency on P5–P9", which is not true in practice.
- **P5 → P8 (soft).** Launch round 3 (P5-06) when no other arc is mid-round.
- **P5 ↔ EQ** (the plan was merged after the consolidation):
  - EQ W1.11 plans data 0.17.0 for X8 with no block, which confirms P5-01f.
  - EQ W1.4 and W1.13 plan data-client 0.6.0 for validator changes, which collides with W5 (P5-03 iii).
  - EQ's recurrence 0.6.0 would carry the widened client cap, which helps W4 and W10, but juniper-ml's `[recurrence]` `<0.6.0` excludes it (P5-01g, P5-27).
  - EQ W0.6 and F-S9 edit `load_sequence_data`, the same function as P5-16 and P5-26.
  - EQ's juniper-ml 0.11.0 floors edit the same `pyproject.toml` lines as W10.
- **P5 → P2.** P5-25 (canopy `demo_mode.py`) and OD-8.

## 4. Hazards

1. **The only copy of P5-09's diff is uncommitted** in `worktrees/juniper-data--fix--arc-agi-task-ids-unicode-429--20260923-1422--ce436819`. Any sweep destroys it, so harvest it before P5-31.
2. **`[0.16.0]` in juniper-data's CHANGELOG must stay byte-identical to the tag** (P3's precedent). A release cut under an open PR silently moves its `[Unreleased]` bullets into the released heading; this happened twice in this arc.
3. **Freeze v3 while the round-3 lanes run.** Record findings in a new section, and archive every lane report: lane D's report was lost.
4. **The owner's PR sweeper un-drafts and merges.** Drafting is not a hold, so validate before pushing to a PR branch.
5. **A negated closing keyword still closes.** "Does not close pcalnon/juniper-data#423" in a v3 PR body would close the Decision 12 tracker.
6. **Unrelated releases consume version numbers.** This is R2-6, and it now applies to data 0.17.0 and data-client 0.6.0. Pin a floor only after reading the wheel.
7. **W11's refusal is non-overridable.** If a VERSION bump lands without its emission, deploy builds from source onto a named volume and the refusals become permanent (S3-F3).
8. **V-3 and PF-3 both need quiet windows.** Check for `clamscan` and the load at launch.
9. **Sequence Safety counts a same-file test rename as a LOST test**, which matters for P5-09.
10. **Signing a headless commit hangs.** Use `util/open_signed_pr.py` or `util/push_signed_commit.py --expected-head <40-char sha>`. `util/safe_merge.py` can exit 0 without merging; read its `MERGED` line.

## 5. Discrepancies

1. **recurrence#178.** HO says it is OPEN and should close only after "a release's own notify job" goes green. It is CLOSED: the owner's account closed it on 2026-10-03 on a `workflow_dispatch` re-run.
2. **#431's confirmation step.** HO's "Evidence…" section says this step "has never run green in Actions". Run 37114403856 shows the step "Confirm the consumer started a run" with conclusion success. HO's own DONE note contradicts the same claim.
3. **Remote branches.** The four ml remote branches HO lists as present are deleted, so HO's `git branch -r | grep -i provenance` returns nothing.
4. **Main heads have moved** in data, data-client, cascor and canopy (P5-05). Data main is 9 ahead of v0.16.0; the P4 handoff said 7, and the extra 2 are dependabot merges.
5. **Item 6's stale literals.** The juniper-data literal has been fixed; only cascor-worker's remains stale.
6. **The data-client "0.6.0".** HO says it "still holds". PyPI is still 0.5.0, but EQ now claims 0.6.0.
7. **SPEC is stale on `equities_seq`.** §7.3 and §12 give `5.0.0 → 5.1.0`, and the allow-list `:296` is cited with `equities_seq` at 5.0.0. Main has had 6.0.0 since 2026-09-24, and round 2 froze before that.
8. **SPEC's route citations have drifted** by about 92 lines (P5-03 iv).
9. **P3's fix-forward branch** is 2 ahead / 6 behind main, not 2 ahead / 4 behind as P3's handoff says.
10. **`validation_gate.py:50`** holds the reason constant; the disabled option itself is at :110-113.
11. **"cascor main moved at `0e016a7c`"** is tagged UNVERIFIED in HO, but it is true: cascor#678 merged as `0e016a7c` on 2026-09-23T20:22Z, and S1-F13 records the shift.

## 6. Residue: open items HO does not carry

- P5-30: the stale docs of record. They are not in HO.
- The `routes/datasets.py` sequencing dependency is missing from HO's own "Dependencies" section.
- No source plans the juniper-ml `[recurrence]` `<0.6.0` widening against EQ's recurrence 0.6.0.
- Design §9.6.6 says round 2 of the §9.4 review "remains unrun for §9.4's other content". No handoff tracks it, and it may be moot. UNTRACEABLE.
- The gated-measurements note records "Cap 64 remains unmeasured" for V-2. That is a caveat, and nothing tickets it.
- P5-32: the bar recurrence#178 set, a release-event run, is unmet.

## 7. Path assessment

- **Urgency: low to moderate.** There is no live user breakage, with one exception: every cascor run's `stats.json`/`eval_metrics.png` shows the in-loop val scores as its eval scalars (#2064), which skews experiment conclusions. P5-09's diff is also at risk of loss.
- **Leverage.**
  - v3 → round 3 → the rulings unblock all of W4–W12, the whole of Decision 12 across five repos.
  - #2064 unblocks #2034's re-measurement.
  - Writing release numbers generically now avoids a second R2-6 cycle, because EQ will consume data 0.17.0 and data-client 0.6.0 ahead of the block.
- **Cost.** The v3 fold is L: 10 clusters, about 40 MINOR/NIT findings and four new inputs. Round 3 is four lanes on a shared usage budget. P5-09 is S. #2064 is S. V-3 is about 18 runs in a quiet window.
- **Recommended next actions:**
  1. **P5-09**: harvest the #434 worktree diff into a new PR from main. It is S, it is startable, and it removes the loss risk.
  2. **P5-01, with P5-02 through P5-05**: write v3, including P5-03's four inputs, extend the gate vectors and re-pin. Then run **P5-06** when no other arc is mid-round.
  3. **P5-11** (#2064), once P6 has confirmed that `util/experiments/` is clear. It shares `stats_summary.py` with P6's item 4.

## 8. What this report cannot support

- No script, test or gate was run. The 52-PASS result rests on an archived lane report, and nothing re-proved the citation pins.
- Worktree dirty state was not probed with git; I only grepped file contents.
- I did not read S1, S2 and S4 in full. P5-02 relies on SPEC §15's own count of their findings.
- Lane D's findings exist only as H-0924 summarises them.
- The quiet-window reading is from 21:00Z only.
- EQ was skimmed for overlap; its own items belong to another extractor.
- A PyPI version shows what is published, not what the wheel contains.
