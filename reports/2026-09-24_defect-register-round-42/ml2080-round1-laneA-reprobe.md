<!-- Archived verbatim 2026-09-24 from subagent a3212838e6d1674b7 of session 8f86dec2 (final message). -->

# Lane A: post-merge re-derivation of juniper-ml#2080 (register fix-forward) and juniper-ml#2075 (primer v3)

**Verdict:** Almost every claim in both PRs reproduces from primary sources, but four do not.
- **#2080 (HIGH):** the fix-forward's completeness claim is false. Five primer citations are still three lines short, in three places.
- **#2075 (MEDIUM):** II.11's tests pin only 3 of the 4 metadata `ETag`s, although Appendix E says "each".
- **LOW:** one misleading drift-test parenthetical in the register, and one primer passage that Appendix E neither links nor names.

## Documents, sources and method

**Documents.** Line numbers are at `origin/main` `94ec75ab`. At that commit the register equals `f2688a95` and the primer equals `f4d050c6`.
- The register is `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, shortened below to `…DEFECT-REGISTER.md`.
- The primer is `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`, shortened to `…IMPLEMENTATION-PRIMER.md`.
- The PR bodies are `ml_register_fixforward_pr_body.md` and `ml_primer_v3_pr_body.md`.
- The procedure followed is `JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.

**Entry points.** Six independent routes, none of them the PRs' own logic:
1. the register's history at `adbe92b0` (creation), `6aabe4cc` (before the fix-forward) and `f2688a95`;
2. primer content at `8d3d4573`, `68f62f5b`, `dcfc024f` and main, mapped with difflib rather than assuming +3;
3. a sweep of every bare number in the register;
4. primary sources on GitHub at pinned refs: canopy `5907713b` (byte-identical to today's main `14a0e4c7` for all four cited files), data `1afc3484`, `v0.15.0` and `39d1cab2`, deploy `d589dd95`, cascor `ec8b5bdb`;
5. the two session transcripts;
6. replays of the PRs' own instruments, each with a negative control.

**Sample.** This was a census, not a sample: all 96 anchored §4 rows, all 14 §3 `**Primer**` rows, and every candidate number in 200..9982.

## Claims table

### juniper-ml#2080

| # | Claim (where) | What I measured | Result |
|---|---|---|---|
| 1 | 43 anchors in 39 §4 rows moved +3, proven by content (§4 note, L766) | My own parser: 41 numbers moved +3 and one moved +4 (`APD-DCLIENT-008`), in 39 rows. "43" counts `APD-ML-001`'s `7445-7446` as two. I read all 39 rows against the text they cite. | REPRODUCED |
| 2 | The register was built against `68f62f5b` | All 40 creation anchors I checked match the text at that line of `68f62f5b`, never `8d3d4573`. `68f62f5b` collapsed four lines at 5758 (paste damage) and #1098 restored them. | REPRODUCED |
| 3 | 8 anchors had landed on blank lines; `APD-DCLIENT-008`'s `6592` was blank even at creation, and `6596` is the paragraph it meant | Blank at 7950, 7615, 6400, 6961 (×3), 7407 and 6625. `68f62f5b`@6592 is blank and the next line is "Named and typed… all nine are positional-or-keyword". | REPRODUCED |
| 4 | 7 prose citations were moved (L532 ×2, L536, L980 ×2, L1166, L1218) | Each now lands on the quoted text. | REPRODUCED |
| 5 | "its fix-forward then corrected all the rest" (L766); "every anchor past it was three short until 2026-09-24" (L1781); "The anchor audit on the result finds nothing left to shift" (PR body) | L527, L1736 and L1737 are still three short (see H1). The audit script reads only §4 `Primer` cells. | **REFUTED** |
| 6 | Anchors at or below 5758 needed no shift | All 57 of those numbers sit at unmoved positions and land correctly. | REPRODUCED |
| 7 | 136 rows, 100 fixed, 36 open (15 primer + 21 post-primer); crosscheck AGREE | Both repo tools give this. So does my own parser (leading `**FIXED` marker only, plus §5.1 coverage). | REPRODUCED |
| 8 | The editor made 47 substitutions (49 occurrences), 43/39 anchor cells, 2 new rows and 2 REFERENCE edits; it is all-or-nothing and refuses a second run | I replayed it on the `6aabe4cc` inputs. The register and `docs/REFERENCE.md` it produces are byte-identical to `f2688a95`. A second run gives "FAIL: APD-ECO-012 already filed". | REPRODUCED |
| 9 | "44 tests OK (skipped=3)" | Same result on main's files. | REPRODUCED |
| 10 | B1: `cors-outside-auth` "entered `ENFORCED` in juniper-ml#1201, never a `KNOWN_GAP`" (L255) | `git log -S` finds a single commit, `b9629de0`, and the status is `ENFORCED` there. | REPRODUCED |
| 11 | B2: canopy's `security.py` was a fourth copy, unfixed until canopy#660 (L997) | Before #660 (`48074653`) the check is `any(hmac.compare_digest…)`. After it (`3a6dea95`) it is a `matched`-flag loop. | REPRODUCED (NIT N2) |
| 12 | A3/B3: false since `APD-DATA-046` (#1864, 2026-09-09) (L182) | Filing commit is `6ccf80fa`; the row is `C` and open. The only open juniper-data `C` rows are `-046`, `-055` and `-057`. | REPRODUCED (NIT N7) |
| 13 | B4: scoping, and the claim that canopy is a site of no other guard | 7/7 primer `S` rows are fixed and 10/10 primer juniper-data `C` rows are fixed. Canopy is a site of 2 of the 7 guards only. | REPRODUCED |
| 14 | B6: `APD-DATA-055`: batch-tags and `DELETE` take no lock; 1 of 240 | Code confirms it. Forced interleaving case D (below) gives a PATCH returning metadata for a deleted dataset. `data428-round3-laneB-refute.md` L46-47 carries the 1/240 and 0/240 figures. Redis, Postgres and cached stores inherit the no-op lock. | REPRODUCED |
| 15 | A1/B7/A4: `APD-ECO-011` (`src/main.py:1642-1654`, `:420-434`; `src/security.py:453-455`; deploy `CHANGELOG.md:179`) | Each line matches. `-demo` sets a cascor URL and so gets `ServiceBackend` (`create_backend` rule 4); only `-dev` sets `JUNIPER_CANOPY_DEMO_MODE`. With auth off, no HTTP route checks Origin (`/api/csrf` is auth-gated; the rest are WebSocket). | REPRODUCED (code only) |
| 16 | B9: `APD-ECO-012` | `main.py:517/519/540`, `settings.py:314` (`[]`) and `middleware.py:149-163` (path-only, no `OPTIONS` bypass) all confirmed. Starlette 1.3.1's `add_middleware` uses `insert(0)`, so the last-added middleware is outermost. The gate's own matcher says canopy is absent, data and cascor present, and canopy-with-CORS-moved-last present. No CORS setting anywhere in deploy's compose, env templates or helm. | REPRODUCED (no live preflight) |
| 17 | `APD-DATA-057`: code lines, "same code as `v0.16.0`", and the mechanism | `datasets.py:714-754/737/746` and `base.py:375` confirmed. `v0.16.0...1afc3484` touches neither routes nor storage. Forced interleavings on juniper-data's own code: (A) a GET undoes a batch edit, while the locked control keeps it; (B) a batch write erases a PATCH's acknowledged tags; (C) concurrent batches lose one. | REPRODUCED (rates not re-measured) |
| 18 | juniper-data#438 cited as open | Still **OPEN** (head `28fced18`). Its diff routes batch-tags through `update_tags` and `DELETE` through `delete_under_lock`. | REPRODUCED |
| 19 | B10: the disclosed crosscheck blind spots | My own mutations: dropping `-050`, `ECO-008` or `-047` from the list still gives AGREE. The control (dropping `-053`, named once) gives DISAGREE. A phantom open row gives 137 \| 100 \| 37 with AGREE. | REPRODUCED |
| 20 | A6/A7/B11: "TWENTY-FOUR"; `-046` from #1864; `-047`–`-052` from #1947 | My own `git log -G` on each row's table line: #1858 filed 16 rows; the other 24 were filed by #1864 (1), #1947 (6), #2005 (2), #2026 (5), #2074 (8) and #2080 (2). | REPRODUCED |
| 21 | B12: "false a third way" (8 rows awaiting a ruling plus a ninth) | The park block lists 8 rows plus `APD-ECO-012` awaiting rulings; `APD-DATA-057` is actionable. | REPRODUCED |
| 22 | B13: `APD-ML-007` | `ceremony.py:462` and `:1011` confirmed. The release was published 08:52:14Z at `39d1cab2`, and the next main commit is at 08:57:15Z. The notes equal the `[0.16.0]` section's 244 non-blank lines in order, with 15 bullets and 4 blanks dropped. `--target-sha` is opt-in, nothing checks the root, and the first heading is used. | REPRODUCED (NIT N4) |
| 23 | B14: `docs/REFERENCE.md` and the §5.1 `APD-ECO-008` row | `docs-full-check.yml` has no `if:` anywhere, and its link check (`:125`) runs before the drift step (`:256`). `release-train.yml` clones siblings. `ci.yml:500` runs the test without them. On a synthetic root with canopy missing: `FAILED (failures=2)`. | REPRODUCED |
| 24 | A-nit: `APD-ML-008`, "would skip only those forks' sites: `OK (skipped=3)`" (L1305) | The count is right, but every fork site is skipped, canopy's included. | **PARTLY REFUTED** (L1) |
| 25 | Owner rulings "verbatim" (L1494-1504) | Labels, sessions and times all match the transcripts (07:32:48Z `bc31e993`, 07:53:26Z `8f86dec2`). Both descriptions are truncated. | REPRODUCED (NIT N5) |
| 26 | The rejection reasons | B12 holds: the checksum already differed from served bytes at `v0.15.0`. B15 holds. The APD-ML-008 A-nit's reason is imprecise. | Mixed (NIT N6) |
| 27 | "all 26 archived reports equal their agents' last messages" | Not re-derived. | NO ARTIFACT |

### juniper-ml#2075

| # | Claim (where) | What I measured | Result |
|---|---|---|---|
| 28 | No line moved; 22 markers, 35 rewrites, 1 in-line replacement; +116 lines | My own classifier: the only structural change is an insert at 9866. The 22 markers are 17 appended at line end and 5 inserted mid-line. The 35 rewrites are 30 rewrites and 5 plain inserts. The replacement is L5332. | REPRODUCED |
| 29 | Build `--check --base dcfc024f`: MATCHES | It MATCHES, and still does under `python3 -O`. My mutated control gives "DIFFERS", exit 1. A newline injected into a marker is "REFUSED". | REPRODUCED |
| 30 | Appendix D harness: 62 pass | 62 passed over 6 files on the pinned venv (Python 3.13.13, fastapi 0.141.1, starlette 1.6.0, pydantic 2.13.4). | REPRODUCED |
| 31 | Toy probe: MATCH on 4 of 4 | MATCH 4/4 on main; MISMATCH 4/4 on `dcfc024f` (negative control). | REPRODUCED |
| 32 | Pin mutation check: every revert caught, control passes | True for its 3 mutants. A 4th revert (POST create) **passes 62/62**. | **REFUTED as "each"** (M1) |
| 33 | RFC 9110 quotes are verbatim | Checked against rfc-editor.org's `rfc9110.txt`. The §8.8.1 definition, E.1 item 3 and L4222's restored phrase are verbatim and attributed to the right section. The If-Range, If-Match and If-None-Match semantics match §13.1.5/.1/.2. | REPRODUCED |
| 34 | Appendix E's factual claims about juniper-data | All code claims confirmed: checksum is uncompressed `np.savez` with sorted keys; stores serve `savez_compressed`; memory sorts keys; cached, HF and Kaggle delegate; `W/"<checksum>"`; `private, no-cache`; bodiless 304; body-hash `ETag`; optional precondition evaluated inside the lock; no 428; `/access`; `Content-Location`; #322 seed defaults with nonce only on explicit `seed=None`; `end_date=None` means today; `v0.15.0` sent none of these headers; #428 is an ancestor of `39d1cab2`. Measured: served `sha256` ≠ checksum on LocalFS and InMemory; different bytes for the same checksum across those two stores and across Cached cold vs warm. | REPRODUCED |
| 35 | The in-place-corrections list is complete and accurate | Outside the II.11 blocks (5349-5779 and 5782-6125), the only non-marker edits are L5, L3639, L4222 and L5332, exactly the ones listed. Lines 1952, 4213, 3426, 3431 and 4220 land as named. | REPRODUCED |
| 36 | "Each affected prose passage … gains a **Corrected** link … except … named" (L9872-9875) | L1954 is neither linked nor named. | **REFUTED narrowly** (L2) |
| 37 | Register citations still land after #2075 | No line moved. No cited line is among #2075's rewrites; 3647, 4200 and 4279 only gained markers. | REPRODUCED |

## Findings

### HIGH

**H1. The fix-forward missed five primer citations in three places, so its completeness claims are false.**

The three misses, all in `…DEFECT-REGISTER.md`:
- **L527** (§3, `APD-SVCCORE-003`) reads `| **Primer** | III.7 — lines 7950-7951, 7962, 7964-7968 |`.
  - It was recorded at creation (`adbe92b0` L221), and it matches `68f62f5b` exactly: "The most interesting trade…", "instead: eleven distinct names…", "The benefit is genuine decoupling… forever, silently."
  - Today 7950 and 7962 are **blank** and 7951 is `#### Duck-Typed Configuration Lookup`.
  - Five lines below, L532's prose was moved to "7953-7954 … 7967-7968", so the two lines now disagree about the same text.
  - Fix: `7953-7954, 7965, 7967-7971`.
- **L1736** (§5.1, `APD-SVCCORE-011`/`-015`) cites "(7944)" for "so **pick one per package**".
  - The quote is at 7948-7949, and the sentence starts at 7947.
  - Today 7944 reads "`websocket/control_stream.py:230`. A `commands` property…".
  - The number was copied from §4's creation-era anchor. Fix: `(7947)`.
- **L1737** (§5.1, `APD-SVCCORE-012`) cites "(8089)" for "invites the inheritance you were avoiding…".
  - The quote is at 8093-8096, and the paragraph starts at 8092.
  - Today 8089 reads "ABC's: `@runtime_checkable`…". Fix: `(8092)`.

Not a miss: L1742's `8188-8195` spans exactly today's paragraph. It was written after #1098 and was rightly left alone.

The claims these misses refute:
- L766: "its fix-forward then corrected all the rest";
- L1781: "every anchor past it was three short until 2026-09-24" (three sites still are, and L1742 never was);
- the PR body: "The anchor audit on the result finds nothing left to shift".

The audit (`util/ad-hoc/2026-09-24_register_primer_anchor_audit.py`, `primer_cells()`) reads only §4 `Primer` cells. So it could not have found any of these, and its "nothing left" is vacuous for §3, §5.1 and prose.

Fix:
- move the five citations;
- restate L766's census as 43 + 7 + 5;
- either scope the audit claim to §4 cells, or extend the audit to `| **Primer** |` rows and to bare numbers in prose, with the same content check.

### MEDIUM

**M1. II.11's tests pin 3 of the 4 metadata `ETag`s, not "each".**

The claims:
- `…IMPLEMENTATION-PRIMER.md` L9879-9880: "II.11's tests (lines 5791, 5838, 5857 and 5945) now also check that each metadata `ETag` is the digest of the exact body sent."
- `ml_primer_v3_pr_body.md`: "makes each `JSONResponse` revert fail the harness".

What I measured:
- I reverted only POST create (L5671-5672) to its `dcfc024f` text (`return JSONResponse(` / `dataset.metadata(),`).
- The toy probe then gives **MISMATCH on POST create 201** and MATCH on the other three routes, so the mutant is live.
- The Appendix D harness still gives **"62 passed … All primer examples passed."**, exit 0.
- The cause is L5838. It hashes `second.content` only; `first` is compared by `ETag` value, never by its body.
- The mutation check's `MUTANTS` covers GET, PATCH and POST reuse, with no POST create.

Fix, same line with no move: L5838 → `assert first.headers["etag"] == second.headers["etag"] == '"' + hashlib.sha256(first.content).hexdigest()[:32] + '"' == '"' + hashlib.sha256(second.content).hexdigest()[:32] + '"'`. Also add a `"POST create"` mutant, or reword to "three of the four".

### LOW

**L1. The `APD-ML-008` parenthetical misstates what the drift test skips.** `…DEFECT-REGISTER.md` L1305 says "(run on its own, the test would skip only those forks' sites: `OK (skipped=3)`)".
- `_find_ecosystem_root` (`tests/test_service_fork_drift.py:317`) requires **both** anchor repos.
- On synthetic roots built from each repo's main:

| Missing checkout | Result | What is skipped |
|---|---|---|
| juniper-data | `OK (skipped=3)` | all three cross-repo methods ("ecosystem root not found"), including canopy's two sites |
| juniper-cascor | `OK (skipped=3)` | same |
| juniper-canopy | `FAILED (failures=2)` | nothing; the file-existence test fails |
| none | `OK` | nothing |

- Fix: "(run on its own, it finds no ecosystem root and skips every fork site, canopy's too: `OK (skipped=3)`; only the shared-package and registry checks run)".

**L2. One primer passage carries the refuted premise with no link and no name.** `…IMPLEMENTATION-PRIMER.md` L1954 reads "juniper-data (v0.11.0) has a textbook caching candidate and emits no cache headers at all."
- It restates E.1's refuted premise, and its "emits no cache headers" is the phrase E.2 (L9978-9979) calls overtaken.
- It is neither linked nor named, against the intro at L9872-9875.
- Mitigating: it is version-qualified, sits under the named heading 1952, and L1956 below it is marked.
- Fix: append ` **[Corrected: E.1](#e1-artifact-validator)**` on the same line.

### NIT (all in `…DEFECT-REGISTER.md` unless stated)

- **N1**, L1297 (`APD-CASCOR-013` Source cell): "the single write in `_reload_dataset` — three since juniper-cascor#678". Cascor `ec8b5bdb` has three writes in the file: `start_training` :2572, `_rollback_pre_swap_state` :3924 and `_reload_dataset` :4691. `_reload_dataset` itself still has only one. Name the three functions.
- **N2**, L997: "until juniper-ml#2059 (`APD-ECO-008`, closed 2026-09-24)". #2059 merged 2026-09-23 22:57Z; 2026-09-24 is the row's close date (#2074).
- **N3**, L766: "it is the only commit to touch the primer since" has been false since #2075, which merged 7 minutes later but moved no line. Say "to move a line".
- **N4**, L1304: "juniper-ml#2071 then added `--target-sha`". #2071 merged 52 s *before* the cut.
- **N5**, L1496-1500: both owner-ruling descriptions are silently truncated; the first is presented as what it "reads". The omitted sentences are "This extends your 'follows the loaded data' ruling to each partition…" and "Smallest change, never under-reports…". The full text is in `owner-rulings-verbatim.md`. Add "…".
- **N6**, `ml_register_fixforward_pr_body.md`: the rejection "the sentence is about CI, where the step never runs" is wrong about CI as a whole. `ci.yml:500` runs the file, so `SharedPackageGuardTest` runs in CI; only `docs-full-check.yml`'s step never runs. The fix-forward's own `docs/REFERENCE.md` L2975 says this.
- **N7**, L182: "round 42 added `APD-DATA-055` and `APD-DATA-057`". `-057` was filed by the fix-forward, as L177 says.
- **N8**, L766 (context only, not false): `68f62f5b` had deleted the four-line block that #1098 restored. So the creation anchors are three short relative to #1080 too, which the note does not explain.
- **Observation, not introduced by #2075**: `…IMPLEMENTATION-PRIMER.md` L4223-4224 bolds part of a verbatim §8.8.1 quote without "emphasis added".

## What this evidence cannot support

- **Live HTTP behaviour.** Canopy (`APD-ECO-011`'s 200s, `APD-ECO-012`'s 401 preflight) was checked from code and the gate matcher only. No request was sent.
- **Rates.** `APD-DATA-057`/`-055`'s 6/12, 28/144 and 1/240 come from timing races. My forced interleavings prove each interleaving can happen, not how often.
- **Other stores.** I measured served bytes against the checksum on LocalFS, InMemory and Cached only. Round 1's "7 of 7" (Redis, Postgres, HF, Kaggle) was not re-measured.
- **Other RFC quotes.** I checked only the RFC 9110 text #2075 introduced or touched. The primer's other RFC quotes were not audited; a whole-document pass is dominated by other RFCs.
- **Marker completeness.** My sweep for unlinked premise passages is lexical, so a passage stating the premise in other words could escape it.
- **Scope of the anchor census.** It covers the register only, not other documents that cite the primer.
- **Not re-derived:** the archive script's 26-report claim, and #2075's pre-commit result.
- **Shared venv.** The pinned venv was another lane's, used as provided.

## Scripts

All are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2080-laneA/`.

Written for this lane:
- **Register anchors:**
  - `laneA_primer_cells.py`
  - `laneA_cell_history.py`
  - `laneA_anchor_content.py`
  - `laneA_unshifted.py`
  - `laneA_number_diff.py`
  - `laneA_number_sweep.py`
  - `laneA_worddiff_view.py`
- **Register counts and provenance:**
  - `laneA_counts.py`
  - `laneA_row_filing.py`
  - `laneA_crosscheck_mutation.py`
- **Primary sources, drift gate and data probes:**
  - `laneA_fetch.py`
  - `laneA_pr_states.py`
  - `laneA_cors_gate_probe.py`
  - `laneA_drift_skip_probe.py`
  - `laneA_data057_interleave.py`
  - `laneA_served_bytes_vs_checksum.py`
- **Transcripts:** `laneA_owner_rulings.py`
- **Primer:**
  - `laneA_primer_invariance.py`
  - `laneA_primer_classify2.py`
  - `laneA_premise_sweep.py`
  - `laneA_rfc_quotes.py`
  - `laneA_rfc_targeted.py`
  - `laneA_build_check_wrapper.py`
  - `laneA_build_newline_mutant.py`
  - `laneA_post_create_mutant.py`

Repo instruments, copied from main unmodified and run:
- `audit_script_main.py`
- `editor_main.py` (replayed in `replay/`)
- `build_main.py`
- `harness_main.py`
- `toy_probe_main.py`
- `pin_mutation_main.py`
- `test_service_fork_drift_main.py`
- the `mini/` tree

**Process disclosure.** My first full-tree `git archive` extraction (0.1 GB) hit "No space left on device" on the shared `/tmp` tmpfs. Other activity had nearly filled it, so concurrent sessions may briefly have seen the error too. I removed the partial extraction at once, and 12 GB was free afterwards. I started no servers.

**Changed:** no repository file. All work was read-only, apart from scratch files.
