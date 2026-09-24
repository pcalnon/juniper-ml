<!-- Archived verbatim 2026-09-24 from subagent a256e7aa15a92fe2d of session 8f86dec2 (final message). -->

**Verdict: INADEQUATE.** Two of the primer's most copyable passages still teach the refuted premise with no link to E.1:

- **Appendix A.6 Q37** (lines 9509-9510), an interview "strong answer".
- **The II.11 worked example**, which Appendix D extracts and runs.

The II.3 best-practice bullet at 3685, twin of the marked line 2015, is also unmarked. The anchor-preservation work itself is sound.

Documents referenced: the primer (`notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`, "…PRIMER.md" below), the register (`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, "…DEFECT-REGISTER.md"), the correction script (`util/ad-hoc/2026-09-24_primer_correct_artifact_validator.py`), the handoff (`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-23_defect-register-round-42-four-prs-armed-by-an-unseen-actor-two-merged-unvalidated.md`), and juniper-data `main` (local `origin/main` 3a76a4c; remote head 39d1cab changes only `CHANGELOG.md`). All line numbers are …PRIMER.md worktree lines unless stated.

### Missed passages (no marker)

| Line(s) in …PRIMER.md | Quoted claim | Why it is false or misleading | Proposed treatment |
|---|---|---|---|
| **9509-9510** (A.6 Q37) — HIGH | "Juniper's dataset artifacts are content-addressed and would qualify … the right header is `private, max-age=31536000, immutable`" | Exactly what E.1 item 2 says "would serve stale data for up to a year". | Marker on 9510 (413 characters with it). Covered by E.1 item 2. |
| **5332** (II.11 motivation) — HIGH | "its dataset identifiers are already content-addressed … strongest possible candidate for `ETag` plus `Cache-Control: immutable` … The validator it needs is already sitting in the codebase" | Asserts all three refuted premises. At 498 characters the script's 512 cap could not take the marker, so it was dropped rather than handled. | Marker on 5330 or 5346 (both fit), plus an E.1 sentence naming II.11. |
| **5352-5360, 5366** (docstring of the extracted `conditional_datasets.py`) — HIGH | "computes a SHA-256 over every artifact's serialized bytes … re-transfers large, **immutable, content-addressed** blobs … the validator exists and is simply not emitted"; "wires up what that service is missing" | Executable code states false facts about juniper-data. A markdown marker cannot go inside the fence. | Reword in place (same line count) and re-run the Appendix D harness. |
| **5419-5422; 5889, 5901-5902** (example code and test) — HIGH | "safe to cache forever *because* the id is content-addressed"; `ARTIFACT_CACHE_CONTROL = "public, max-age=31536000, immutable"`; `# "immutable" is only honest because the id is a hash of the inputs.` | Directly contradicts E.1's third lesson ("An identifier derived from inputs buys idempotent creation without buying immutability"). The toy is immutable only because `_synthesize_artifact` (5550-5553) is a pure function of the id. Under 5366's "what that service is missing" framing, `public` also contradicts I.9 (1984-1986) and E.1's second lesson. | Attribute immutability to the deterministic synthesis; drop `public`; re-run the harness. |
| **3685** (II.3 Best Practices) — MEDIUM | "Emit an `ETag` whenever you already compute a digest — juniper-data computes one and discards it — and support `If-Match` on every unsafe method" | Twin of the marked 2015. E.1 item 1 says this tag matches `If-Match` only via `*`, and a tag edit does not change it. "Discards" was never true: the checksum is persisted on `DatasetMeta.checksum`. Missed because the line says "digest", not "checksum". | Marker on 3685 (216 characters). |
| **3452-3453** (II.2) — MEDIUM | "nonce deliberately breaks content-addressing for exactly the case where its premise is false" | E.1 item 2 shows the premise also fails for seeded requests (equities, re-creation). "With `seed` absent the generator is itself non-deterministic" has been stale since juniper-data#322 (2026-09-03). | Marker on 3453. |
| **3426, 3431** (II.2 table row and heading) — MEDIUM | "Content hash \| `/datasets/spiral-v1.0.0-a3f8…` \| Deduplicating, immutable, cache-friendly"; "Ground truth: juniper-data's content-addressed dataset ID" | Uses juniper-data's own id format as the immutable content-hash example. A marker appended after a table row's last pipe is dropped by GFM (extra cell) and trips MD056. The heading has no inbound links, so it can be marked safely. | E.1 sentence, or a marker on 3443. |
| **463** (I.3) — MEDIUM | "The hard part of caching, having a stable strong validator, was already done" | Same paragraph as 462, but the marker on 462 lands *before* this sentence. That breaks the script's own "LAST line of a paragraph" rule. | Move the marker to 463. |
| **3399-3400** (II.2) — MEDIUM | "neither sets `Content-Location` … Since juniper-data emits no cache headers at all, the duplication is latent" | #428 also closed APD-DATA-029 (`Content-Location` on `/latest`) and sends `private, no-cache`. E.1 says so itself, so this now contradicts E.1. The register's APD-DATA-029 row cites line 3399. | Marker on 3400, plus an E.2 entry or an E.1 sentence. |
| **4171-4174, 4197-4200, 4273-4279, 5362-5364, 5785-5787** — MEDIUM | The tag PATCH is an unguarded read-modify-write; "the scenario the real service silently gets wrong" | APD-DATA-006 was fixed 2026-08-14 (juniper-data#263), and #428 evaluates `If-Match` inside `update_tags`' lock. E.1 bullet 3 says the PATCH is now conditional, so these contradict it. | E.2 entry, with markers on 4200, 4279 and 5364. |
| **5537** (`metadata_etag`) — MEDIUM | "A *strong* validator: a hash of the exact representation we would send." | It hashes `canonical_json` (sorted keys, ASCII-escaped), but 5722 sends `JSONResponse` bytes (insertion order, UTF-8). My probe shows the two digests differ for the test fixture. That is the same shape E.1 item 1 rules weak. | Hash the rendered body, as #428's `PrerenderedJSONResponse` + `body_etag` does. |
| 1563, 1565 (I.7) — LOW | "juniper-data illustrates the content-addressed variant"; the seedless-nonce claim | Wording conflicts with E.1 item 2; the seed claim is stale since #322. | Marker on 1565. |
| 3638-3639 — LOW | `If-Match: "a3f8e12b4c567890"` | The example uses the dataset-id digest as the PATCH validator. An id-derived tag cannot change when tags change, so this precondition can never fail. | Change the value in place. |
| 4213 heading, 4220 — LOW | "the fix already sitting in juniper-data"; "Hash of serialized JSON \| usually weak" | 4220 conflicts with E.1's strong ETag, which is "the SHA-256 of the exact response body". | Mark the heading; fix the cell in place. |
| 4222-4225 — LOW | Paraphrase of RFC 9110 §8.8.1 | Drops "applied to the representation data" (checked against the RFC text), which is the exact condition the checksum fails. | Restore the qualifier. |
| 1952/1954, 4314-4315, 543, 594 — NIT | "Strongest Candidate, Unused"; "juniper-data avoided this deliberately"; "If you already compute a content digest, you have already done the hard part"; "Caching benefits are claimed and not implemented (as in `juniper-data`)" | Overtaken, or echoes of the refuted framing. | Optional. |

### Other findings

- **MEDIUM — dangling register row.** E.1 cites register row `APD-DATA-054`, which does not exist in …DEFECT-REGISTER.md (the highest is APD-DATA-053). It exists only as a plan in step 3 of the handoff. **Fix:** land the register row first or in the same PR, or write "to be filed as".
- **MEDIUM — the correction script's `--check` passes vacuously.** Run on the corrected file, it prints "already applied (Appendix E present); nothing to do" and exits 0 without checking anything (reproduced on a scratch copy). Its docstring's claim that `--check` "proves every original line is unchanged" holds only before the edit is applied. **Fix:** re-run the proof against `git show HEAD:` in that branch.
- **LOW-MEDIUM — E.1's nonce wording is stale.** E.1 says "plus a per-call nonce when no seed is given". Since #322, an omitted seed takes `DEFAULT_GENERATOR_SEED` and gets no nonce; only an explicit `seed=None` does (`test_default_generator_seed.py`). E.1's own equities example depends on this: `equities` has an integer default seed, `end_date=None` means today (`generator.py:315`), and `params.model_dump()` hashes both, so the same request gets the same id across days. As written, E.1 undercuts its own example.
- **LOW — E.1 overreaches on three markers.** It calls every linked passage "wrong on two counts", but:
  - The 4251 passage predicted correctly, and #428 took its own second option (splitting the counters to `/access`). Only the aside "the artifact endpoint's would work perfectly" is wrong.
  - The 3650 marker follows a true sentence.
  - 4018's "could carry an `ETag` for free and support conditional GETs" is exactly what #428 did.
- **LOW — "ships in juniper-data 0.16.0" is not yet true.** There is no v0.16.0 tag or Release, and PyPI's latest is 0.15.0. Every present-tense "juniper-data sends …" in E.1 is true of `main` only.
- **LOW — "is conditional on a strong `ETag`" overstates.** The PATCH precondition is optional: unconditional writes are accepted and there is no 428.
- **LOW — nothing points readers to Appendix E.** It is reachable only from the 13 markers, and the marker convention implies that unmarked passages are current. Appending a pointer to an existing header line (such as line 5) would fix this without moving any line.
- **NIT.**
  - On 1960 and 1974 the marker sits after a colon that introduces a code block, so it reads as the thing the colon introduces.
  - Expiry alone does not re-create a dataset: the create path returns an expired dataset as a cache hit until it is deleted or cleaned up.
- **Out of scope, found in passing.**
  - Pre-existing anchor drift: the register was created (adbe92b0) about ten hours before f7b89745 added three lines at 5758. As a result "Q26 at 9463" and Primer-column "9592" now land on blank lines; the true targets are 9466 and 9595.
  - …DEFECT-REGISTER.md lines 340-343 still record the superseded "strong `ETag` derived from the stored SHA-256" ruling, with no mention of the 2026-09-23 re-ruling.

### Attacks that did not land

- **Anchors.** All 120 distinct primer lines cited by the register (Primer column and prose) resolve to identical text. Only the 13 marked lines changed, all 9,866 original lines keep their positions, and 56 lines were appended. No cited line carries a marker. Running the script on a HEAD copy reproduces the worktree file byte for byte.
- **Rendering.** None of the 13 lines is in a table, code fence or blockquote. The pinned markdownlint v0.42.0, run without `--fix` on scratch copies, reports nothing on either version. The `#e1-artifact-validator` anchor matches its heading.
- **E.1's core facts check out on juniper-data main and in RFC 9110:**
  - Checksum construction, and all store serialization (the HF, Kaggle and cached stores delegate to the four E.1 names).
  - The weak `W/"<checksum>"` tag, `private, no-cache` headers and bodiless 304.
  - The strong metadata ETag, the `/access` route and the `http_cache.py` docstring.
  - The equities date default, and If-Range's weak-tag prohibition.
- No passage claims download integrity checks against the checksum. The general immutable-resource guidance (1870, 1950, 1994, 2007, 2014, 4043, 4061, 4283-4285) is true and needs no marker. Line 3581 is still true (GETs still call `record_access`).

### What this evidence cannot support

- I read I.3, I.7, I.9, II.2-II.6, II.11 (to 5910), all appendices and the Reading Guide in full. The other sections were covered only by keyword sweeps using about 40 terms, so a passage phrased differently could remain.
- I did not run the Appendix D harness. The `metadata_etag` finding rests on emulating Starlette 0.50.0's `render`; the primer pins 1.6.0, which I did not inspect.
- I read the remote state through `gh api` only and did not fetch.

Nothing in any repo was modified. No stash, commit, push or comment was made. No secrets were printed or sent. `git show` output displayed a commit author's email locally only. Scratch files are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/primer-laneB/`:
- `anchor_check.py`
- `toy_metadata_etag_probe.py`
- `kwindex.py`
- `show_hits.py`
- `primer_HEAD.md`, `primer_WT.md`, `primer.diff`
- `rootWT/`, `rootHEAD/`
- `lint_HEAD.txt`, `lint_WT.txt`
- `rfc9110.txt`
