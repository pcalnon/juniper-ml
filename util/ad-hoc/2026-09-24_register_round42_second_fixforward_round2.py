#!/usr/bin/env python3
"""
Apply what round 2 of the pre-PR validation of round 42's second fix-forward refuted, before any PR exists.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register maintenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use editor; all-or-nothing, refuses to run twice
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

Branch `docs/register-round-42-second-fixforward` holds the second fix-forward (e2f87aae) and its round-1
corrections (990ef3f9, util/ad-hoc/2026-09-24_register_round42_second_fixforward_corrections.py). Round 2
validated that delta with two more independent lanes, archived verbatim in
reports/2026-09-24_defect-register-round-42/ as register-fixforward2-round2-laneA-reprobe.md and
register-fixforward2-round2-laneB-refute.md. Lane A found no HIGH or MEDIUM. Lane B found one MEDIUM, and it
was a regression the fix-forward itself introduced: restricting the II.11 toy's `params` to numbers turned a
lone-surrogate string, which JSON allows, from an accepted 201 into a plain-text 500, because the 422 that echoes
it could not be rendered by Starlette's `JSONResponse` (`ensure_ascii=False`). This applies every finding that
survived re-derivation:

- the toy: problem bodies are ASCII-escaped `json.dumps` output, so no echoed input can break one, and the
  list route renders through `canonical_json` like every other route, because the same class reached it by
  another way: a `str` field accepts a lone surrogate, so a TAG stores one with a 201 and the next list was a
  plain-text 500 (a sibling no lane named; the probe shows it on `main` too). `n_samples` is bounded to an
  integer from 1 to 1,000,000 on lines 5658-5659 (the walrus keeps the assignment), which retires the
  "fraction is truncated, huge is a 500" caveats instead of documenting more of them. The suite pins the bound,
  the echoed surrogate, `true`, `null` and the deep cursor on the lines its arms already use (6084-6087 and
  6117-6120): both lanes showed the deep cursor fits, refuting the reason the first round gave for leaving it
  to the probe. The list stays pinned by the probe only. The two remaining "every error"
  claims (the II.11 intro and the test section heading) are scoped. Appendix E's sentence is rewritten to
  match, names its code lines again, and counts line 4199 as the fifth line corrected in place. E.1 item 3's
  cost clause gains If-None-Match (RFC 9110 §13.1.2) and names the lost 304 as the cost;
- the register: `record_access` is the `GET /{id}` read (a single-dataset read, but so is `/latest`, which never
  fired it), the census count names the retired `6592` it includes, APD-CASCOR-013's Source cell cites cascor's
  CURRENT writers (§4's `Source` column is "the current file:line"), the last range-only id list is spelled
  out, and APD-DATA-057's park bullet stops calling a row actionable without a ruling, against §1.

Each register substitution must match exactly the number of times it declares. Each primer edit names its line
and that line's exact current text; the primer must keep its line count, only the named lines may change, and
no new line may carry a character `str.splitlines()` breaks on. Nothing is written unless every check passes.

Usage: python3 util/ad-hoc/2026-09-24_register_round42_second_fixforward_round2.py [--dry-run] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REG_REL = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
PRIMER_REL = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
PREREQ = "is an eighth, and round 42 filed two more"  # round 1's corrections must be present
DONE_MARKER = "n_samples must be an integer from 1 to 1,000,000"
DATA_057_WAS = "it said \"actionable, needs no ruling\" until corrected the same day"

# The characters str.splitlines() breaks on besides "\n", built from code points so that this file's own
# source holds none of them (round 2 found both earlier editors embedding raw U+2028 / U+2029).
LINE_BREAKERS = "".join(map(chr, (0x0D, 0x0B, 0x0C, 0x1C, 0x1D, 0x1E, 0x85, 0x2028, 0x2029)))

# (label, old, new, expected count)
REG_SUBS: list[tuple[str, str, str, int]] = [
    (
        "s3 APD-DATA-006: the GET /{id} read (A N1)",
        "fired on every single-dataset metadata read and every artifact download, though not by the list, filter, `/latest` or"
        " versions reads —",
        "fired on the `GET /{id}` metadata read and every artifact download, and never by the list, filter, `/latest` or versions"
        " reads —",
        1,
    ),
    (
        "s4 note: the census count includes the retired 6592 (B N8)",
        "(69 on 2026-09-24, 82 numbers counting both ends of a range; each read).",
        # Names the anchor without its number: the census counts every bare number, so writing it here would make 70.
        "(69 on 2026-09-24, the retired anchor the next sentence names among them, and 82 numbers counting both ends of a range;"
        " each read).",
        1,
    ),
    (
        "APD-CASCOR-013: the current writers (B N9)",
        "`src/api/lifecycle/manager.py` (init; the writes in `start_training` :2572, `_rollback_pre_swap_state` :3924 and"
        " `_reload_dataset` :4691 at `ec8b5bdb` — `_reload_dataset`'s the only one before juniper-cascor#678, and four since #688 —"
        " and the read in `get_status`)",
        "`src/api/lifecycle/manager.py` (init; the writes in `_bind_start_tensors_locked` :2560, `_rebind_dataset_record_locked`"
        " :2623, `_rollback_pre_swap_state` :4104 and `_reload_dataset` :4947 at `7f4a7213`, #688's merge — before juniper-cascor#678"
        " `_reload_dataset` held the only one, and `ec8b5bdb` had three — and the read in `get_status`)",
        1,
    ),
    (
        "rulings block: APD-ML-002 to -006 by id (B N10)",
        "  `APD-ML-002` … `APD-ML-006` were filed needing one before code is written, and still do.",
        "  `APD-ML-002`, `APD-ML-003`, `APD-ML-004`, `APD-ML-005` and `APD-ML-006` were filed needing one before code is written,"
        " and still do.",
        1,
    ),
    (
        "park APD-DATA-057: not 'actionable without a ruling' (B L6)",
        "- `APD-DATA-057` — **filed 2026-09-24; actionable, needs no ruling.** The remedy is the lock the",
        "- `APD-DATA-057` — **filed 2026-09-24 with its fix already written, as part of the fix-forward of juniper-data#428's"
        " validation, so no session actions it without a ruling** *(" + DATA_057_WAS + ", which §1's rule does not allow)*. The"
        " remedy is the lock the",
        1,
    ),
    (
        "s5.1 APD-DATA-007: the GET /{id} read (A N1)",
        "fires on every single-dataset metadata read and every artifact download and also rewrites the entire document",
        "fires on the `GET /{id}` metadata read and every artifact download and also rewrites the entire document",
        1,
    ),
]

# The bound takes the formerly blank line 5658 and the assignment's line 5659: the walrus binds n_samples in the
# condition, so the route keeps its line count without a one-line `if ...: raise`.
NSAMPLES_IF = "        if not isinstance(n_samples := body.params.get(\"n_samples\", 512), int) or not 1 <= n_samples <= 1_000_000:"
NSAMPLES_RAISE = (
    "            raise ProblemException(status=422, title=\"Request validation failed\", detail=\"n_samples must be an integer"
    " from 1 to 1,000,000.\", type_=\"https://errors.example.com/validation-failed\")"
)

# line -> (exact current text, replacement). Every replacement is one line: nothing may move.
PRIMER_LINES: dict[int, tuple[str, str]] = {
    # A N1: /latest is a single-dataset read too, and it never fired record_access.
    4199: (
        "on every single-dataset metadata read and artifact download (`routes/datasets.py:672`, `:698`; the list, filter, `/latest`"
        " and versions reads fire none). It holds `_version_lock`;",
        "on the `GET /{id}` metadata read and every artifact download (`routes/datasets.py:672`, `:698`; the list, filter,"
        " `/latest` and versions reads fire none). It holds `_version_lock`;",
    ),
    # B L3: the II.11 intro still said problem+json "for every error".
    5330: (
        "This example builds the HTTP semantics of Part II into one small service: content-addressed identifiers, strong `ETag`s,"
        " conditional `GET` returning 304, optimistic concurrency with `If-Match` and 412, `428 Precondition Required` for writes"
        " that omit the precondition, keyset pagination with a `Link` header, and RFC 9457 `application/problem+json` for every"
        " error.",
        "This example builds the HTTP semantics of Part II into one small service: content-addressed identifiers, strong `ETag`s,"
        " conditional `GET` returning 304, optimistic concurrency with `If-Match` and 412, `428 Precondition Required` for writes"
        " that omit the precondition, keyset pagination with a `Link` header, and RFC 9457 `application/problem+json` for every"
        " error its routes raise.",
    ),
    # The bound below retires the "n_samples is read unchecked" caveat.
    5378: (
        "  validation errors, which otherwise emit a differently shaped body. Not on FastAPI's own 404, 405 or body-parse 400, which"
        " keep ``{\"detail\": ...}``, and not on an unhandled exception: ``n_samples`` is read unchecked, so a huge one is Starlette's"
        " plain-text 500.",
        "  validation errors, which otherwise emit a differently shaped body. Not on FastAPI's own 404, 405 or body-parse 400, which"
        " keep ``{\"detail\": ...}``, and not on an exception nothing here anticipates, which is Starlette's plain-text 500.",
    ),
    # B M1, and its sibling the list route: nothing renders through JSONResponse (ensure_ascii=False) any more.
    5399: (
        "from fastapi.responses import JSONResponse, Response",
        "from fastapi.responses import Response",
    ),
    # B M1: render problem bodies ASCII-escaped, so an echoed lone surrogate cannot break one.
    5455: (
        "    def to_response(self, request: Request) -> JSONResponse:",
        "    def to_response(self, request: Request) -> Response:",
    ),
    5464: (
        "        return JSONResponse(body, status_code=self.status, media_type=PROBLEM_JSON, headers=self.headers)",
        "        return Response(json.dumps(body, allow_nan=False), status_code=self.status, media_type=PROBLEM_JSON,"
        " headers=self.headers)  # ASCII-escaped: an echoed lone surrogate cannot break it",
    ),
    # B N5: it is the JSON parser's C recursion limit, not sys.getrecursionlimit().
    5600: (
        "    except (ValueError, KeyError, TypeError, RecursionError, binascii.Error) as exc:  # RecursionError: a cursor nested past"
        " the limit",
        "    except (ValueError, KeyError, TypeError, RecursionError, binascii.Error) as exc:  # RecursionError: nested deeper than the"
        " JSON parser allows",
    ),
    5618: (
        "    async def _problem_handler(request: Request, exc: ProblemException) -> JSONResponse:",
        "    async def _problem_handler(request: Request, exc: ProblemException) -> Response:",
    ),
    5622: (
        "    async def _validation_handler(request: Request, exc: RequestValidationError) -> JSONResponse:",
        "    async def _validation_handler(request: Request, exc: RequestValidationError) -> Response:",
    ),
    # A N7 / B L1: bound n_samples, instead of documenting truncation and huge allocations.
    5658: ("", NSAMPLES_IF),
    5659: ("        n_samples = int(body.params.get(\"n_samples\", 512))", NSAMPLES_RAISE),
    # B M1's sibling: a lone surrogate STORED in a tag (a str field accepts one) made the list a plain-text 500.
    5682: ("    ) -> JSONResponse:", "    ) -> Response:"),
    5699: (
        "        return JSONResponse({\"items\": [d.metadata() for d in page], \"count\": len(page)}, headers=headers)",
        "        return Response(canonical_json({\"items\": [d.metadata() for d in page], \"count\": len(page)}),"
        " media_type=\"application/json\", headers=headers)",
    ),
    # A LOW-2 / B L4: the deep cursor fits the suite on the lines its garbage-cursor test already uses. "W1tb" is
    # base64 for "[[[" and "XV1d" for "]]]", so the cursor needs no import: 15,000 nested arrays, past the C limit.
    6084: (
        "        response = await client.get(\"/v1/datasets?cursor=not-a-real-cursor\")",
        "        response, deep = await client.get(\"/v1/datasets?cursor=not-a-real-cursor\"), await client.get(\"/v1/datasets?cursor=\""
        " + \"W1tb\" * 5000 + \"XV1d\" * 5000)  # base64 of 15,000 nested arrays",
    ),
    6086: (
        "    assert response.status_code == 400",
        "    assert response.status_code == deep.status_code == 400  # deep: nested past what the JSON parser allows",
    ),
    6087: (
        "    assert response.headers[\"content-type\"].startswith(\"application/problem+json\")",
        "    assert all(r.headers[\"content-type\"].startswith(\"application/problem+json\") for r in (response, deep))",
    ),
    # B L3 / A N8: the test section heading made the same "everywhere" claim.
    6091: (
        "# 6. One error model everywhere",
        "# 6. One error model: the routes' errors and FastAPI's validation errors",
    ),
    # Pin true and null (A N6 / B L5), the bound and the ASCII-escaped problem body in the suite itself, on the lines
    # the arms already use. true and null go on `seed`, so the n_samples bound cannot be what refuses them.
    6117: (
        "        bad_extra, bad_str = await client.post(\"/v1/datasets\", json={**SPIRAL, \"typo_field\": 1}), await"
        " client.post(\"/v1/datasets\", json={**SPIRAL, \"params\": {\"n_samples\": \"512\"}})  # \"512\" must not be coerced",
        "        bad_extra, bad_str, bad_bool = await client.post(\"/v1/datasets\", json={**SPIRAL, \"typo_field\": 1}), await"
        " client.post(\"/v1/datasets\", json={**SPIRAL, \"params\": {\"n_samples\": \"512\"}}), await client.post(\"/v1/datasets\","
        " json={**SPIRAL, \"params\": {\"seed\": True}})  # \"512\" and true must not be coerced",
    ),
    6118: (
        "        bad_query = await client.get(\"/v1/datasets?limit=99999\")",
        "        bad_query, bad_fraction, bad_null = await client.get(\"/v1/datasets?limit=99999\"), await client.post(\"/v1/datasets\","
        " json={**SPIRAL, \"params\": {\"n_samples\": 1.5}}), await client.post(\"/v1/datasets\", json={**SPIRAL, \"params\":"
        " {\"seed\": None}})  # nor 1.5 truncated, nor null taken for a number",
    ),
    6119: (
        "        bad_nan = await client.post(\"/v1/datasets\", content=b'{\"generator\": \"spiral\", \"params\": {\"noise\": NaN}}',"
        " headers={\"Content-Type\": \"application/json\"})",
        "        bad_nan, bad_surrogate = await client.post(\"/v1/datasets\", content=b'{\"generator\": \"spiral\", \"params\":"
        " {\"noise\": NaN}}', headers={\"Content-Type\": \"application/json\"}), await client.post(\"/v1/datasets\","
        " content=b'{\"generator\": \"\\\\ud800\"}', headers={\"Content-Type\": \"application/json\"})  # the 422 echoes a lone"
        " surrogate",
    ),
    6120: (
        "    for response in (bad_enum, bad_extra, bad_str, bad_query, bad_nan):",
        "    for response in (bad_enum, bad_extra, bad_str, bad_bool, bad_query, bad_fraction, bad_null, bad_nan, bad_surrogate):",
    ),
    # A LOW-1 / B L2 (4199 is a fifth in-place line), B N6 (the code anchors), and the sentence rewritten to the new code.
    9880: (
        "5838, 5857 and 5945) now also check that each metadata `ETag` is the digest of the exact body sent — the POST-create 201's own"
        " body only since a second correction the same day. That correction also limited a create's `params` to JSON numbers, never"
        " coerced (line 5346): NaN, Infinity, or an `n_samples` that `int()` rejects, is a 422 problem where it had been a plain-text"
        " 500, and any other non-number is refused where it had been accepted; `n_samples` itself stays unchecked, so a fraction is"
        " truncated and a huge value is a plain-text 500, as lines 5377-5378 now say. It also made a cursor nested past the"
        " recursion limit a 400 problem (line 5600), and marked line 4224's bold as added emphasis, a fourth line corrected in place.",
        "5838, 5857 and 5945) now also check that each metadata `ETag` is the digest of the exact body sent — the POST-create 201's own"
        " body only since a second correction the same day. That correction also limited a create's `params` to JSON numbers, never"
        " coerced (lines 5346, 5400, 5498 and 5502), and `n_samples` to an integer from 1 to 1,000,000 (lines 5658-5659): NaN,"
        " Infinity, any other non-number, and an `n_samples` out of that range or not an integer are 422 problems now, where the same"
        " requests had been plain-text 500s, silently truncated, or accepted, depending on the input. It renders every problem body,"
        " and the list, ASCII-escaped like the other routes, so a lone surrogate echoed in a 422 or stored in a tag no longer makes a"
        " plain-text 500 (lines 5399, 5455, 5464, 5618, 5622, 5682 and 5699), and it makes a cursor nested deeper than the JSON"
        " parser allows a 400 (line 5600). This suite pins the create route's tag (line 5838), the deep cursor (lines 6084, 6086 and"
        " 6087), and a numeric string, `true`, `null`, a fractional `n_samples`, a NaN and an echoed lone surrogate (lines"
        " 6117-6120); `util/ad-hoc/2026-09-24_primer_toy_error_paths_probe.py` pins the rest, the list included. Two more lines were"
        " corrected in place: line 4199's `record_access` claim, and line 4224's bold, now marked as added emphasis. That makes five in"
        " all.",
    ),
    # A N2 / B L5, B N7: the lost 304 is the revalidation cost, and RFC 9110 §13.1.2 adds an If-None-Match write that passes.
    9943: (
        "   validator; unstable field order or float formatting only makes it change when the dataset has not, which costs",
        "   validator; unstable field order or float formatting only makes it change when the dataset has not, which costs the",
    ),
    9944: (
        "   revalidations and spurious `412`s on conditional writes, but never serves stale bytes. juniper-data's metadata `ETag` and"
        " II.11's are both such hashes.",
        "   `304`s it would have earned, and can fail an `If-Match` write that should pass or pass an `If-None-Match` write (§13.1.2)"
        " that should fail, but never serves stale bytes. juniper-data's metadata `ETag` and II.11's are both such hashes.",
    ),
}


def apply(text: str, subs: list[tuple[str, str, str, int]]) -> str:
    for label, old, new, want in subs:
        got = text.count(old)
        if got != want:
            raise SystemExit(f"FAIL {label}: expected {want} match(es), found {got}; nothing written")
        text = text.replace(old, new)
        print(f"  ok  {label} (x{want})")
    return text


def edit_primer(text: str) -> str:
    lines = text.split("\n")
    before = len(text.splitlines())
    for n, (old, new) in sorted(PRIMER_LINES.items()):
        if lines[n - 1] != old:
            raise SystemExit(f"FAIL primer line {n}: it does not hold the text this edit expects; nothing written\n  have: {lines[n - 1]!r}")
        bad = [c for c in new if c in LINE_BREAKERS]
        if bad:
            raise SystemExit(f"FAIL primer line {n}: the new text holds a line-breaking character {bad[0]!r}; nothing written")
        lines[n - 1] = new
    out = "\n".join(lines)
    changed = [i + 1 for i, (a, b) in enumerate(zip(text.split("\n"), out.split("\n"))) if a != b]
    if len(out.splitlines()) != before or len(out.split("\n")) != len(text.split("\n")) or changed != sorted(PRIMER_LINES):
        raise SystemExit(f"FAIL primer: lines moved or unexpected lines changed (changed {changed}); nothing written")
    print(f"  ok  primer: {len(changed)} lines rewritten in place, {before} lines before and after, none moved")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    reg = (REPO / REG_REL).read_text(encoding="utf-8")
    primer = (REPO / PRIMER_REL).read_text(encoding="utf-8")
    if PREREQ not in reg:
        raise SystemExit("FAIL: the register lacks round 1's corrections (commit 990ef3f9); build on them")
    if DONE_MARKER in primer or DATA_057_WAS in reg:
        raise SystemExit("FAIL: these corrections have already been applied")

    reg = apply(reg, REG_SUBS)
    primer = edit_primer(primer)

    if args.dry_run:
        print("dry run: nothing written")
        return 0
    base = args.out_dir if args.out_dir is not None else REPO
    for rel, text in ((REG_REL, reg), (PRIMER_REL, primer)):
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
