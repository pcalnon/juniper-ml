<!-- Archived verbatim 2026-09-24 from subagent ad32dacf1c456fe8b of session 8f86dec2 (final message). -->

**Verdict: REFUTED.** v2 fixes most of what round 1 found, and its line invariance, anchors, lint, rendering and toy-ETag fix all hold. But it adds one false claim about live data-loss behavior (E.2), misdates the lost-update fix in the II.11 example, and still leaves the II.11 motivation paragraph unmarked because its marker sits on the preceding paragraph.

Short names: **`…PRIMER.md`** is `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`; **`…DEFECT-REGISTER.md`** is `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`. Line numbers are `…PRIMER.md` at `b6129bf8` unless stated otherwise.

I judged against juniper-data main **`1afc3484`**: `3adb33ea` plus #437, which touches only the `equities_seq` generator, the generators route, CHANGELOG and tests. `fix/conditional-requests-round3-followups` exists only in a local worktree, with no commits beyond `1afc348` and no PR, so nothing from it has merged. For history I used `7125e161` (just before #428), `9e8b7ef4` (just before #263) and the `v0.16.0` tag `39d1cab2`.

## Findings

### HIGH-1 — E.2 says a GET can no longer undo a tag edit. At main, it can.

`…PRIMER.md` L9946: "juniper-data#263 (2026-08-14, `APD-DATA-006`) made tag updates atomic, so a GET can no longer undo one". L9944 adds "each has since been fixed". The marker on L4200 ("reading a dataset can undo an edit to it") sends the reader to this bullet.

- **Code:** at `1afc3484`, and identically in the `v0.16.0` tag, `PATCH /v1/datasets/batch-tags` (`api/routes/datasets.py:714-754`) still reads and writes in two unlocked hops: `get_meta` at `:737`, `update_meta` at `:746`. It takes neither `_version_lock` nor `_meta_write_lock`. This is the APD-DATA-006 pattern that #263 removed from the single-dataset route only (`storage/base.py:375`).
- **Measured** with `batch_race_demo.py` against `1afc3484`, 12 rounds, LocalFS, in-process threads:
  - the batch route kept **28 of 144** concurrent tag additions; the single-route control kept 144/144;
  - a plain GET (`record_access`) **undid a batch tag edit in 6 of 12 rounds**;
  - the one conditional PATCH that answered 200 (1 of 1) was then erased by a concurrent batch write.
  - An earlier 5-round run agrees: 17/60 kept, 1/5 undone.
- **Why nothing else catches it:**
  - The row E.2 cites, `APD-DATA-055` in `…DEFECT-REGISTER.md` on #2074's branch, says only that batch-tags "evaluates neither header".
  - `…DEFECT-REGISTER.md`'s APD-DATA-007 fix note says "Both whole-document writers are fixed". There are three.
  - juniper-data#428's round-3 refute report (`data428-round3-laneB-refute.md`, item 1, MEDIUM) found the missing lock, but that finding reached neither the register row nor E.2.
  - E.2's own caveat "writers that take the same lock" (L9951) gestures at this without naming the route, and it doesn't qualify bullet 1.
- **Fix:**
  - Scope bullet 1 to the single-dataset route, and state that `PATCH /batch-tags` still does an unlocked two-hop read-modify-write: a GET can undo a batch edit, and a batch write can erase a conditional PATCH's 200.
  - L9944: "fixed on the route these passages describe".
  - File a register row (or widen APD-DATA-055) and correct APD-DATA-007's note.
  - The same claim sits in the docstring of `2026-09-24_primer_correct_artifact_validator.py` ("the tag write is atomic (#263, #282)").

### MEDIUM-1 — The II.11 rewrite credits #428 with ending a lost update it did not end

`…PRIMER.md` L5362-5364: "two clients that read the same dataset and both PATCHed it produced a silent lost update -- until juniper-data#428 made that PATCH conditional on ``If-Match``". L5786-5787: "the scenario juniper-data's tag PATCH got wrong until juniper-data#428."

- **Different semantics:** juniper-data's PATCH applies add/remove deltas (`UpdateTagsRequest`; `storage/base.py` `update_tags`). The toy's `TagUpdate` replaces the whole list.
- **The headline interleaving never lost anything in juniper-data.** `lost_update_demo.py` runs it translated to juniper-data (A GET, B GET, A adds `approved`, B adds `rejected`, no precondition). A's change survives at `7125e161` and even at `9e8b7ef4`.
- **The real loss was a concurrent server-side race, and #263/#282 closed it before #428, without `If-Match`:**
  - at `9e8b7ef4`: 3/12 thread writes and 2/12 process writes survived (5 of 12 workers also crashed on a concurrent temp-file rename);
  - at `7125e161`: 12/12 and 12/12.
- **It contradicts the primer itself:** E.2 bullet 1, and `…PRIMER.md` L4277-4279 ("Adding an `If-Match` check … would buy a correct 412 and change nothing about the race").
- **It is also wrong after #428:** the batch route still loses tags (HIGH-1).
- **Fix** (same-line rewrites):
  - L5362-5364: say the PATCH applies add/remove deltas, lost tags to a concurrent race until #263/#282, and gained an optional `If-Match` in #428.
  - L5786-5787: say juniper-data's delta PATCH never had this replace-style overwrite.

### MEDIUM-2 — The II.11 marker is on the true paragraph; the false one is unmarked

- **Where the marker is:** L5330 carries "**[Corrected: E.1]**" after the toy's feature list ("content-addressed identifiers, strong `ETag`s, …"). E.1 declares the toy honest (L9935-9937).
- **What is unmarked:** L5332, "its artifacts are the strongest possible candidate for `ETag` plus `Cache-Control: immutable` … The validator it needs is already sitting in the codebase". My render check shows the two are separate paragraphs.
- **Terminology knock-on:** the toy still calls its own ids content-addressed (L5346, the banners at L5468 and L5813, "the real juniper-data scheme" at L5481). E.1 item 2 (L9916) says that same scheme is "not content-addressed". So the L5330 marker reads as retracting the toy's ids too.
- **Why v2 moved it:** L5332 is 498 characters, and appending the marker gives 543.
- **Fix:** restore L5330 to its base text. On L5332, replace "The validator it needs is already sitting in the codebase." with the marker (484 characters). The register doesn't cite L5332.

### MEDIUM-3 — Two headings still state the refuted premise, and E.1's list of unlinked passages (L9884-9886) omits them

- L1952: "#### Juniper in Practice: The Strongest Candidate, Unused". Both halves are now false.
- L4213: "#### ETag generation, and the fix already sitting in juniper-data".
- L594: "Caching benefits are claimed and not implemented (as in `juniper-data`)." Overtaken by #428.

Nothing in the repo links to either heading anchor, so markers fit (102, 110 and 357 characters). **Fix:** mark all three, or name them, with line numbers, in E.1's enumeration.

### LOW

- **L-1 (wrong target on L3400).** The sentence before the E.2 marker is "Since juniper-data emits no cache headers at all, the duplication is latent rather than live." That is E.1's subject: `/latest` and `/{id}` now send `private, no-cache` and the same strong ETag. E.2 covers only L3399's `Content-Location` half. **Fix:** link both E.1 and E.2.
- **L-2 (release state).** L9883-9884: "#428 is queued for juniper-data 0.16.0, unreleased when this was written; 0.15.0, the latest on PyPI, …".
  - Re-probed: the GitHub Release `v0.16.0` was published 08:52:14Z, tagging `39d1cab2`, which contains #428's merge `af7831be` (ancestry checked).
  - PyPI still serves 0.15.0; its "Publish to PyPI" run 35977786108 is `waiting`. So "the latest on PyPI" goes false as soon as that run is approved.
  - The author commit (08:49:45Z) predates the Release by 2.5 minutes, so "unreleased when this was written" was accurate. "Queued" is now stale.
  - The same commit says at L5358 "#428 has since shipped the fix", which disagrees with E.1.
  - **Fix:** "#428 shipped in juniper-data 0.16.0 (GitHub Release, 2026-09-24; tag `39d1cab2`); 0.15.0 and earlier send none of these headers."
- **L-3 (Appendix E describes itself wrongly).**
  - L9871 says "Each affected prose passage keeps its text and gains a **Corrected** link". E.1's own enumeration (L9884-9886) and MEDIUM-3 contradict that.
  - Two in-place corrections are listed nowhere in Appendix E: L3639 (the `If-Match` value) and L4222 (the §8.8.1 paraphrase). Yet L5 now says "corrections are listed in Appendix E".
- **L-4 (merge order is a request, not a gate).** E.1 (L9915) and E.2 (L9952-9953) cite APD-DATA-054/-055. Those rows exist only on #2074's branch (`36de4c8a`); `origin/main` (`602094e3`) has 0 hits. Both #2074 and #2075 have native auto-merge armed, so the PR body's "Land that first" enforces nothing.
- **L-5 (instruments).**
  - The Appendix D harness (`2026-08-13_run_primer_examples.py`) executes every changed route: a NameError planted in each fails 1, 10, 6 and 2 tests. But reverting GET, PATCH or POST-reuse to `JSONResponse`, or adding one trailing space to the PATCH body, still passes 62/62 on both toolchains. The toy fix is pinned only by `2026-09-24_primer_toy_etag_matches_body.py`, which nothing runs. **Fix:** add a same-line assertion at L5857.
  - `2026-09-24_primer_correct_artifact_validator.py --check` can't re-verify the committed file: on the branch and on main it can only REFUSE. Fed the base primer instead, its build reproduces the head file byte-for-byte.
  - Its proof prints "9866 lines, none moved" even when a newline is smuggled into one rewrite (the output then has 9,867 lines before Appendix E), and the asserts vanish under `-O`. The shipped output is unaffected (see my position check below).

### NIT

- **N-1.** L9918 says "a generator's documented default seed is `DEFAULT_GENERATOR_SEED`". That holds for 10 of 16 generators. `spiral` defaults to 42, and the five synthetic sequence generators default to `seed: int = 0` (`_synthetic.py:65`), where `seed=None` is rejected with a 400. The conclusion (an omitted seed gives a deterministic id) holds for all 16.
- **N-2.** E.1's RFC quote is verbatim, but it is the "at the same time" clause. Most of E.1's cases are sequential (cache states, a numpy/zlib upgrade). §8.8.1's strong-validator definition, which the checksum fails, fits them better.
- **N-3.** L9951-9952: "per host only: the Redis, Postgres and cached stores hold a per-process lock". Per-host holds only on LocalFS (`local_fs.py:124` is the sole `_meta_write_lock` override); everywhere else it is per process, including the Hugging Face and Kaggle stores.
- **N-4.** L9937-9938 endorses `http_cache.py`'s docstring as the corrected reasoning. That docstring still quotes the paraphrase "Same content, possibly different bytes" as the RFC definition (`:17-19`) and lacks the "cleaned up" qualifier (`:33`), both of which v2 fixed in E.1 itself.
- **N-5.** L5366, "wires up those semantics": "those" now points back to #428's weak tag and `no-cache`, while the bullets below describe the opposite choices (strong tags, `immutable`, a required precondition).
- **N-6.** `canonical_json` (L5477) keeps `allow_nan=True`. A POST carrying a non-standard `NaN` raised at base; at head it returns `201 application/json` with `"noise":NaN`, which is not JSON. Same on both toolchains.
- **N-7.** Two unmarked lines still sit awkwardly with E.1:
  - L4314-4315, "juniper-data avoided this deliberately": the digest is key-sorted but the served bytes are not, which is exactly E.1 item 1's mechanism.
  - L4220, "Hash of serialized JSON | usually weak": #428's strong metadata ETag is exactly such a hash.
- **N-8.** The PR body and the armed squash-commit body say "The II.4 `If-Match` example". L3639 is in II.3.

## What did not land

- **Line invariance** (my own `line_invariance.py`, not the author's script):
  - Of the 9,866 base lines, 9,814 are byte-identical at the same index.
  - 22 differ only by one marker; removing it restores the base line exactly, and no trailing whitespace was stripped.
  - 30 are rewritten, exactly the declared set. Appendix E starts at L9867.
  - Negative controls: inserting one line flags 6,774 lines; editing L4200 in place flags exactly {4200}.
- **Register anchors:** 161 distinct cited lines at base and on main, 162 on #2074's branch. All land on identical content; 4 (2026, 3647, 4200, 4279) carry only a marker; none lands on a rewritten line. I printed 14 explicitly.
- **Lint:** markdownlint-cli v0.42.0 (the pinned rev) with `.markdownlint.yaml` reports 0 findings on base and head. No changed line exceeds 512 characters. Three pre-existing lines do (786, 1344, 9481); they are unchanged and pass lint.
- **Rendering:** base and head render to the same 1,916 blocks. Each marked block differs only by its marker; the only other prose changes are the declared rewrites at L5 and L4222. `#appendix-e--corrections`, `#e1-artifact-validator` and `#e2-conditional-tag-writes` each resolve uniquely, and all 69 in-document fragment links resolve.
- **The toy fix:**
  - The toy probe gives 4/4 MATCH at head and 4/4 MISMATCH at base, and flagged each of my 3 single-route mutations exactly.
  - Route by route, base and head match on status, content type, length and JSON value, with 304s bodiless.
  - The 412/428 responses carry the current metadata ETag by design (the headline test pins it). The list route has no ETag. The artifact ETag hashes the bytes actually sent.
  - Both toolchains pass 62/62: the JuniperData env (CPython 3.14t, FastAPI 0.137, Starlette 0.50) and a venv built to the Appendix D.2 pins (CPython 3.13.13, FastAPI 0.141.1, Starlette 1.6.0, Pydantic 2.13.4).
- **RFC 9110** (fetched from rfc-editor.org): E.1's quote, L4222's quoted tail and paraphrase basis, the §13.1.5 weak-tag ban, and §13.1.1/§13.1.2 comparison functions are all verbatim.
- **juniper-data facts in E.1/E.2:** every other claim checks out at `1afc3484`:
  - the checksum construction, the four stores' `savez_compressed`, and the in-memory store's key sort;
  - the delegating stores, the `W/` tag, and `If-Match` matching only through `*`;
  - a strong metadata ETag shared by GET and the PATCH precondition, with the precondition optional and no 428;
  - `/access`, `private, no-cache`, bodiless 304s, and `Content-Location`;
  - the PR dates of #263, #282, #322 and #428; the equities binder leaving `end_date` unbound; and no such headers in 0.15.0.
- **Copilot commit:** `b6129bf8` removes only an unused `import sys`; pyflakes is clean on both scripts.
- **Round-1 fixes applied:** all of E.1's four round-1 errors are fixed, as are Q37, L3685, L463 and the pointer from the Status line.

## What this evidence cannot support

- The race counts come from in-process TestClient threads on LocalFS and vary with timing. Nothing was run under multi-worker uvicorn, Redis or Postgres. The conditional-PATCH erasure is a single observation.
- The history probes ran the source trees under the JuniperData env's libraries, not each release's pinned dependencies.
- Rendering and slugs were checked with markdown-it-py plus an emulated GitHub slugger, not GitHub's own renderer, which would have meant sending repo content out.
- The sweep was regex-based: 9 concept families, 619 hits. I read every hit on or near a juniper-data mention and all of I.3, I.7, I.9, II.2, II.3, II.5, II.6, II.11 and A.6; I only sampled general teaching elsewhere.
- The register-cite extraction is a heuristic.
- The 2026-09-23 owner ruling is corroborated only by secondary records.
- I did not read the uncommitted round-3 work, which could change the batch route.
- PyPI state and merge order may change at any moment.

## Scripts

All are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/primer-r2-laneB/`:
- `sweep_concepts.py`
- `mutate_toy.py`, `mutate_nameerror.py`
- `toy_routes_compare.py`
- `pypi_probe.py`
- `lost_update_demo.py`, `batch_race_demo.py`
- `rfc_check.py`
- `line_invariance.py`, `mutate_invariance.py`, `spot_check_cites.py`
- `render_check.py`
- `check_correction_script.py`

The directory also holds the extracted trees (`head/`, `base/`, `jd_main/`, `jd_pre428/`, `jd_pre263/`), `venv_pinned/`, `rfc9110.txt`, and the mutated primer copies.

**Changed**: no repository file. No refs, worktrees or servers were created, no processes are left, and nothing secret was printed or sent. Outbound traffic was limited to `gh` reads, PyPI, and rfc-editor.org.
