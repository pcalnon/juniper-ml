#!/usr/bin/env python3
"""Correct the API primer's artifact-validator and tag-write premises WITHOUT moving a line anchor.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc documentation tooling
Author:      Paul Calnon
Created:     2026-09-24
Version:     2.0.0
License:     MIT License
Status:      single-use (defect-register round 42; retained as provenance)

Why this exists
---------------
``notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`` treats
juniper-data's ``GET /v1/datasets/{id}/artifact`` as an IMMUTABLE, CONTENT-ADDRESSED blob whose stored
``checksum`` is a ready-made STRONG ``ETag``, and its tag PATCH as an unguarded read-modify-write.
juniper-data#428 (and #263 / #282 before it) found or fixed all of that:

* ``compute_checksum`` digests an UNCOMPRESSED, key-sorted ``np.savez``, while every store serves
  ``np.savez_compressed`` -- so the checksum can back only a WEAK validator (register ``APD-DATA-054``);
* ``generate_dataset_id`` hashes the REQUEST, not the bytes, so the artifact is not immutable and
  ``Cache-Control: ... immutable`` would serve stale data;
* the tag write is atomic (#263, #282) and conditional (#428), and ``/latest`` sets
  ``Content-Location``.

The defect register cites this primer by BARE LINE NUMBER. Inserting one line anywhere shifts every
anchor below it. So:

* a prose passage keeps its text and gains a short ``**[Corrected: E.n](...)**`` link, appended to an
  EXISTING line or inserted mid-line right after the false sentence;
* text inside the executable II.11 example, which a markdown link cannot enter, is reworded ON THE SAME
  LINES -- and four metadata responses now send exactly the canonical bytes their strong ``ETag``
  hashes (the Appendix D harness must still pass);
* the explanation goes in a new Appendix E appended at the END of the file, and the header's Status
  line points to it.

v1 of this script was validated by two independent lanes (round 42, reports
``primer-correction-round1-lane{A,B}-*.md``), which found it incomplete; v2 applies their findings.
v1's ``--check`` passed vacuously once applied. v2 always rebuilds from ``git show HEAD:<primer>`` and
PROVES the result: every untouched line is byte-identical to HEAD, and the line count before Appendix E
is unchanged.

Usage: python3 util/ad-hoc/2026-09-24_primer_correct_artifact_validator.py [--check]
  --check  build and prove, then compare with the working-tree file; write nothing
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PRIMER = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
MAX_LINE = 512
E1 = " **[Corrected: E.1](#e1-artifact-validator)**"
E2 = " **[Corrected: E.2](#e2-conditional-tag-writes)**"

# (1-based line, a phrase that must be on that line, marker, insert-after anchor or None to append)
MARKERS = [
    (463, "having a stable strong validator, was already done", E1, None),
    (1565, "so a UUID nonce is mixed in", E1, None),
    (1956, "The `{id}` is content-addressed", E1, None),
    (1958, "**The body for a given id cannot change.**", E1, None),
    (1960, "a precomputed strong validator", E1, "and a payload big enough to matter."),
    (1974, "The stored `checksum` is a strong `ETag` waiting to be emitted", E1, "waiting to be emitted"),
    (2015, "juniper-data's unused `checksum` is the case in point", E1, None),
    (2026, "bytes that cannot have changed", E1, None),
    (3400, "Since juniper-data emits no cache headers at all", E2, None),
    (3453, "nonce deliberately breaks content-addressing", E1, None),
    (3647, "a SHA-256 over the serialised NPZ bytes", E1, "The material is there; the header is not."),
    (3685, "juniper-data computes one and discards it", E1, None),
    (3995, "large immutable content-addressed artifacts", E1, None),
    (4018, "support conditional GETs on an immutable blob", E1, None),
    (4174, "last writer wins, whole document, no version check", E2, None),
    (4200, "`update_dataset_tags` never takes that lock", E2, None),
    (4232, "That is the textbook strong-validator case", E1, "That is the textbook strong-validator case"),
    (4245, "treat its own semantics as unverified.)", E1, None),
    (4251, "or split them into a sub-resource.", E1, None),
    (4279, "The storage layer is what would have to change first.", E2, None),
    (5330, "content-addressed identifiers, strong `ETag`s", E1, None),
    (9510, "the right header is `private, max-age=31536000, immutable`", E1, None),
]

# (1-based line, exact old line, exact new line). The II.11 example is extracted and executed by
# Appendix D, so every code line here must stay valid Python and every test must still pass.
SUBS = [
    (5, "**Status**: Reference primer — living document",
     "**Status**: Reference primer — living document; corrections are listed in [Appendix E](#appendix-e--corrections)"),
    (3639, 'If-Match: "a3f8e12b4c567890"', 'If-Match: "9c4b7e2d01f5a863"'),
    (4222, 'The cost objection is answered in §8.8.1: a collision-resistant hash suffices as a strong validator "if the data is',
     'The cost objection is answered in §8.8.1: a collision-resistant hash applied to the representation data suffices as a strong validator "if the data is'),
    # -- II.11 example docstring: the motivation, in the past tense and accurate --
    (5352, "Motivation (the fix is already sitting in the codebase)", "Motivation (a real gap when written; see Appendix E)"),
    (5354, "``juniper-data`` computes a SHA-256 over every artifact's serialized bytes and",
     "When this primer was written, ``juniper-data`` stored a SHA-256 of every"),
    (5355, "stores it on ``DatasetMeta.checksum`` -- then never uses it as an HTTP validator.",
     "dataset's arrays on ``DatasetMeta.checksum`` and never sent it as an HTTP"),
    (5356, "There is no ``ETag``, no ``Cache-Control``, no ``If-None-Match`` and no 304",
     "validator: no ``ETag``, no ``Cache-Control``, no ``If-None-Match``, no 304,"),
    (5357, "anywhere in the service, so ``GET /v1/datasets/{id}/artifact`` re-transfers",
     "so ``GET /v1/datasets/{id}/artifact`` re-transferred every artifact in full."),
    (5358, "large, **immutable, content-addressed** blobs in full on every request. The",
     "juniper-data#428 has since shipped the fix -- with a WEAK artifact tag,"),
    (5359, "identifier is already a hash of the inputs and the body is already hashed: the",
     "because that hash covers the arrays, not the bytes served, and ``no-cache``,"),
    (5360, "validator exists and is simply not emitted.",
     "because a request-derived id does not make a body immutable."),
    (5362, "The service also cannot reject a stale write. Tags are mutable, so two clients",
     "Nor could it reject a stale write. Tags are mutable, so two clients that read"),
    (5363, "that read the same dataset and both PATCH it produce a silent lost update -- the",
     "the same dataset and both PATCHed it produced a silent lost update -- until"),
    (5364, "second write wins and the first is gone, with no error anywhere.",
     "juniper-data#428 made that PATCH conditional on ``If-Match``."),
    (5366, "This example wires up what that service is missing:",
     "This example wires up those semantics in a small, unauthenticated service:"),
    # -- II.11 example code: the artifact's immutability is the toy's, not the id's --
    (5419, "#: The artifact is safe to cache forever *because* the id is content-addressed:",
     "#: The artifact is safe to cache forever *because* this toy synthesizes it"),
    (5420, "#: a different byte stream is necessarily a different URL, so a cached entry can",
     "#: deterministically from its id, so a URL can never serve other bytes. An id"),
    (5421, '#: never go stale. "immutable" is only honest under that invariant.',
     "#: that merely hashes the request cannot promise that (Appendix E, E.1)."),
    # -- II.11 example code: send exactly the canonical bytes the strong metadata ETag hashes --
    (5646, "    async def create_dataset(body: DatasetCreate) -> JSONResponse:", "    async def create_dataset(body: DatasetCreate) -> Response:"),
    (5653, "            return JSONResponse(", "            return Response("),
    (5654, "                existing.metadata(),", '                canonical_json(existing.metadata()), media_type="application/json",'),
    (5671, "        return JSONResponse(", "        return Response("),
    (5672, "            dataset.metadata(),", '            canonical_json(dataset.metadata()), media_type="application/json",'),
    (5722, "        return JSONResponse(dataset.metadata(), headers=headers)",
     '        return Response(canonical_json(dataset.metadata()), media_type="application/json", headers=headers)'),
    (5748, "    ) -> JSONResponse:", "    ) -> Response:"),
    (5773, "        return JSONResponse(", "        return Response("),
    (5774, "            dataset.metadata(),", '            canonical_json(dataset.metadata()), media_type="application/json",'),
    # -- II.11 tests --
    (5786, "whole reason optimistic concurrency exists, and it is the scenario the real",
     "whole reason optimistic concurrency exists, and it is the scenario"),
    (5787, "service silently gets wrong.", "juniper-data's tag PATCH got wrong until juniper-data#428."),
    (5901, '    # "immutable" is only honest because the id is a hash of the inputs.',
     '    # "immutable" is honest here only because the bytes are a pure function of the id.'),
]

APPENDIX = """
## Appendix E — Corrections

Claims about the Juniper codebase that proved false, or that a later change overtook, are corrected here
rather than rewritten in place. Each affected prose passage keeps its text and gains a **Corrected** link
to its entry below. Passages inside the II.11 executable example, which a link cannot enter, were
reworded on the same lines, and the Appendix D harness re-run. Nothing above was moved: the defect
register (`JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`) cites this document by bare line
number, and inserting a line would shift every anchor after it. That is also why the table of contents
does not list this appendix; the header's **Status** line points here instead.

### E.1 Artifact validator

**Corrected 2026-09-24.** juniper-data#428 (merged 2026-09-23) implemented conditional requests on
`GET /v1/datasets/{id}/artifact` and found false the premises of the passages linked here. They treat
the artifact as an immutable, content-addressed blob whose stored `checksum` is a ready-made strong
validator. #428 is queued for juniper-data 0.16.0, unreleased when this was written; 0.15.0, the latest
on PyPI, sends none of the headers below. Beyond the linked passages, the same premises appear in II.2's
content-hash table row and its "content-addressed dataset ID" heading, and in II.11's motivation
paragraph.

1. **The stored `checksum` does not digest the bytes the route serves, so it can back only a weak
   validator.** `compute_checksum` (`juniper_data/core/artifacts.py`) hashes `arrays_to_bytes(arrays)`:
   an *uncompressed* `np.savez` of the arrays, keys sorted. Every store serves `np.savez_compressed`
   output instead (`storage/local_fs.py`, `memory.py`, `redis_store.py`, `postgres_store.py`; the
   cached, Hugging Face and Kaggle stores delegate to one of these), so `sha256(served bytes) !=
   checksum` on every store. The hash changes whenever the arrays change, which is what whole-body
   revalidation needs. But one dataset can be served as two different byte strings under one
   checksum: the in-memory store sorts the arrays' keys and the others keep the generator's order, so
   the bytes differ between stores, and between the cache states of `CachedDatasetStore`; another
   numpy or zlib could do the same. RFC 9110 §8.8.1 calls such a validator weak: "a validator is weak
   if it is shared by two or more representations of a given resource at the same time, unless those
   representations have identical representation data". juniper-data therefore sends
   `ETag: W/"<checksum>"`, per the owner's ruling of 2026-09-23. Three consequences for the passages
   linked here:

   - `If-None-Match` compares weakly, so revalidation works. `If-Match` compares strongly, so it can
     match an artifact only through `*`.
   - `If-Range` accepts only a strong validator (§13.1.5), so resumable range downloads cannot be keyed
     on this tag.
   - The checksum was never the right validator for PATCH's lost-update protection either: it covers
     the arrays, and a tag edit does not change them. juniper-data's `PATCH /v1/datasets/{id}/tags` can
     be made conditional on a *strong* `ETag` over the metadata representation, the SHA-256 of the
     exact response body. The precondition is optional: a PATCH without one is applied, and nothing
     answers `428`. The body is stable only because the access counters left it (`APD-DATA-032`); they
     are served at `GET /v1/datasets/{id}/access` now.

   A strong artifact validator needs each store to record the SHA-256 of the exact bytes it writes.
   That known gap is defect-register row `APD-DATA-054`.
2. **The artifact is not content-addressed, so it is not immutable.** `generate_dataset_id`
   (`juniper_data/core/dataset_id.py`) hashes the *request* — generator, version and parameters — not
   the bytes produced. Since juniper-data#322 (2026-09-03) a generator's documented default seed is
   `DEFAULT_GENERATOR_SEED`, so an omitted seed gives a deterministic id, and only an explicit
   `seed=None` mixes in a per-call nonce. A dataset that is deleted (or expires and is cleaned up) and
   is then re-created serves whatever the generator produces now, at the same URI. `equities` with its
   default `end_date=None` means "today", so the same parameters yield different data on different
   days under one id. Part II states the governing rule, *content-address only over inputs that fully
   determine the output*, and applies it to the seedless case; it applies here too, because the inputs
   do not fully determine the bytes. `Cache-Control: private, max-age=31536000, immutable` would
   therefore serve stale data for up to a year with revalidation suppressed. juniper-data sends
   `Cache-Control: private, no-cache` on the artifact and on both metadata reads, and answers a
   matching `If-None-Match` with a bodiless `304`.

What stands is the linked passages' central advice. Emit a validator when you hold a digest
(juniper-data now does). Keep read counters out of a validated representation, or move them to a
sub-resource (juniper-data moved them to `/access`). Use `private`, not `public`, when the credential is
a custom header. A digest in your data model is not an HTTP validator until someone puts it on the
wire, and it is a *strong* one only if it digests the bytes actually sent. An identifier derived from
inputs buys idempotent creation without buying immutability. II.11's example keeps `immutable` for its
own artifacts, and honestly so, because that toy synthesizes each artifact deterministically from its
id; its metadata responses now send exactly the bytes their strong `ETag` hashes. The corrected
reasoning is also recorded at the source, in the module docstring of `juniper_data/api/http_cache.py`.

### E.2 Conditional tag writes

**Corrected 2026-09-24.** The passages linked here describe juniper-data's tag update as an unguarded
read-modify-write that an ordinary read could undo, and `GET /v1/datasets/latest` as setting no
`Content-Location`. Each was true when written, and each has since been fixed:

- juniper-data#263 (2026-08-14, `APD-DATA-006`) made tag updates atomic, so a GET can no longer undo
  one, and juniper-data#282 (2026-08-23, `APD-DATA-007`) made the metadata read-modify-write atomic
  across processes on the local-filesystem store.
- juniper-data#428 made `PATCH /v1/datasets/{id}/tags` conditional. It evaluates `If-Match` and
  `If-None-Match` inside the store's lock, answers a stale tag with `412` and writes nothing, and
  returns the new strong `ETag`. Its protection holds against writers that take the same lock, and
  per host only: the Redis, Postgres and cached stores hold a per-process lock (defect-register row
  `APD-DATA-055`). The precondition is optional.
- `/v1/datasets/latest` and the tag PATCH's response now carry `Content-Location` naming the
  canonical `/v1/datasets/<dataset_id>` (`APD-DATA-029`).

II.11's example service, which demonstrates the conditional PATCH, now describes juniper-data's gap in
the past tense.
"""


def head_primer() -> str:
    out = subprocess.run(["git", "show", f"HEAD:{PRIMER}"], cwd=REPO, capture_output=True, text=True, check=True)
    return out.stdout


def build(head: str) -> str:
    if not head.endswith("\n") or "## Appendix E — Corrections" in head:
        raise SystemExit("REFUSED: HEAD's primer already carries Appendix E, or lacks a final newline")
    lines = head.split("\n")[:-1]
    original = list(lines)
    edited: "dict[int, str]" = {}
    for lineno, old, new in SUBS:
        if lines[lineno - 1] != old:
            raise SystemExit(f"REFUSED: line {lineno} is not the expected text; the primer moved\n  want {old!r}\n  have {lines[lineno - 1]!r}")
        lines[lineno - 1] = new
        edited[lineno] = new
    for lineno, phrase, marker, after in MARKERS:
        if lineno in edited:
            raise SystemExit(f"REFUSED: line {lineno} is both substituted and marked")
        line = lines[lineno - 1]
        if phrase not in line:
            raise SystemExit(f"REFUSED: line {lineno} lacks {phrase!r}; the primer moved")
        if after is None:
            new = line.rstrip() + marker
        else:
            if line.count(after) != 1:
                raise SystemExit(f"REFUSED: line {lineno}: insert anchor {after!r} occurs {line.count(after)} times")
            new = line.replace(after, after + marker, 1)
        lines[lineno - 1] = new
        edited[lineno] = new
    # Proof: nothing moved, and every line outside the edit set is byte-identical to HEAD.
    assert len(lines) == len(original)
    for i, (old, new) in enumerate(zip(original, lines), start=1):
        if i not in edited:
            assert new == old, i
    too_long = [i for i in edited if len(lines[i - 1]) > MAX_LINE] + [f"appendix+{i}" for i, ln in enumerate(APPENDIX.split("\n")) if len(ln) > MAX_LINE]
    if too_long:
        raise SystemExit(f"REFUSED: lines over {MAX_LINE} characters: {too_long}")
    print(f"{len(MARKERS)} markers + {len(SUBS)} same-line rewrites; {len(original)} lines, none moved; every other line byte-identical to HEAD; appendix +{len(APPENDIX.splitlines())} lines")
    return "\n".join(lines) + "\n" + APPENDIX


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="build and prove, compare with the working tree, write nothing")
    args = ap.parse_args()
    out = build(head_primer())
    target = REPO / PRIMER
    if args.check:
        same = target.read_text(encoding="utf-8") == out
        print("working tree", "MATCHES" if same else "DIFFERS FROM", "the build")
        return 0 if same else 1
    target.write_text(out, encoding="utf-8")
    print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
