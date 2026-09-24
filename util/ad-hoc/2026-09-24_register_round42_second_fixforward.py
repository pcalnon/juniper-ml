#!/usr/bin/env python3
"""
Fix forward what the post-merge validation of juniper-ml#2080 and #2075 refuted, in the register, the primer and REFERENCE.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register maintenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use editor; all-or-nothing, refuses to run twice
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

juniper-ml#2080 (round 42's register fix-forward) and #2075 v3 (the API primer's correction) were validated
after merge by two independent lanes, archived verbatim in
reports/2026-09-24_defect-register-round-42/ml2080-round1-laneA-reprobe.md and
reports/2026-09-24_defect-register-round-42/ml2080-round1-laneB-refute.md. This applies every finding that
survived re-derivation against source:

- notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md: the five primer citations #2080's audit
  never read (H1), the silent missing-juniper-data-clone path in APD-ML-008 (H2), the lock-less writers and
  `record_access` scope in APD-DATA-055 / -057, and the dated or miscounted prose the lanes named;
- notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md: II.11's create-route
  ETag pin (M1), E.1 item 3's rule (M2), the toy's NaN / non-numeric params 500 (L4), E.2's writer count, and
  two unmarked premise passages -- every edit on its own line, so no line moves and no register anchor
  shifts (the register cites the primer by bare line number);
- docs/REFERENCE.md: the drift gate's silent missing-juniper-data-clone path (H2).

Each register and REFERENCE substitution must match exactly the number of times it declares. Each primer
edit names its line and that line's exact current text; the script refuses unless the primer keeps its line
count, only the named lines change, and no new line carries a character `str.splitlines()` would break on.
Nothing is written unless every check passes.

Usage: python3 util/ad-hoc/2026-09-24_register_round42_second_fixforward.py [--dry-run] [--out-dir DIR]
  --out-dir  write the three files under DIR (same relative paths) instead of in place, for a trial run
"""

from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REG_REL = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
PRIMER_REL = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
REF_REL = "docs/REFERENCE.md"
V = "`ml2080-round1-laneB-refute.md`"  # lane B's report, cited by name in every correction note
A = "`ml2080-round1-laneA-reprobe.md`"
BY = "the post-merge validation of juniper-ml#2080"
DONE_MARKER = "a second fix-forward the last 5"

# (label, old, new, expected count)
REG_SUBS: list[tuple[str, str, str, int]] = [
    # ---- section 2 -------------------------------------------------------------------------------------
    (
        "s2 crosscheck blind spots (L6)",
        "so a phantom open row moves the open-set count while the crosscheck still says AGREE.)*",
        "so a phantom open row moves the open-set count while the crosscheck still says AGREE. Two more, measured by mutation on round 42's fix-forward"
        " (`reports/2026-09-24_defect-register-round-42/ml2080-round1-laneB-refute.md`, L6): a `**FIXED` marker put in an open row's `Source` cell makes"
        " `register_open_set.py`, which tests the whole row, count it fixed, while the crosscheck, which reads only the status cell, still says AGREE;"
        " and a duplicated row is invisible to both.)*",
        1,
    ),
    (
        "s2 DATA-057 was the fix-forward's (N7)",
        "and round 42 added `APD-DATA-055` and `APD-DATA-057`; round 42 made the first false",
        "and round 42 added `APD-DATA-055`, and its fix-forward `APD-DATA-057`; round 42 made the first false",
        1,
    ),
    # ---- section 2.3 ----------------------------------------------------------------------------------
    (
        "s2.3 more than a seventh",
        "and `APD-CASCOR-005` is a seventh of the kind, one where the shared package was itself among the drifted copies.",
        "and `APD-CASCOR-005` is a seventh of the kind, one where the shared package was itself among the drifted copies. Round 42 filed three more,"
        " all in canopy: `APD-ECO-008` (closed 2026-09-24), `APD-ECO-009` and `APD-ECO-010`; `APD-ECO-012`, canopy's CORS ordering, joined the table"
        f" too, with no shared implementation to copy *(this sentence stopped at the seventh until {BY}, {V})*.",
        1,
    ),
    (
        "s2.3 sibling group closed 08-28 (L5)",
        "**The sibling-package-drift group is CLOSED** (2026-08-21).",
        "**The sibling-package-drift group is CLOSED** (2026-08-28, when cclient#143 fixed its last table row; this said 2026-08-21, the day the"
        f" exception-context fix described below closed, until {BY}, {V} L5).",
        1,
    ),
    # ---- section 3: APD-SVCCORE-003's primer field (same width, so the table stays aligned) ------------
    (
        "s3 SVCCORE-003 primer field (H1)",
        "III.7 — lines 7950-7951, 7962, 7964-7968",
        "III.7 — lines 7953-7954, 7965, 7967-7971",
        1,
    ),
    # ---- section 4 note -------------------------------------------------------------------------------
    (
        "s4 note: 68f62f5b and #2075 (N3, N8)",
        "ten hours after this register was created, and it is the only commit to touch the primer since, so every anchor past that line recorded at"
        " creation was three short.",
        "ten hours after this register was created — restoring a four-line block that `68f62f5b`, the primer revision the register was built"
        " against, had collapsed into one — and it is the only commit to move a primer line since (juniper-ml#2075 corrected the primer on"
        " 2026-09-24 without moving one), so every anchor past that line recorded at creation was three short.",
        1,
    ),
    (
        "s4 note: the last five, and what proves them (H1)",
        "its fix-forward then corrected all the rest — 43 anchors in 39 rows' `Primer` cells, 8 of which had landed on blank lines, and 7 in the"
        " prose — each proven by content: line N of the primer the register was built against (`68f62f5b`) is line N+3 today"
        " (`util/ad-hoc/2026-09-24_register_primer_anchor_audit.py`).",
        "its fix-forward then corrected 43 anchors in 39 rows' `Primer` cells, 8 of which had landed on blank lines, and 7 in the prose, and"
        f" {DONE_MARKER}, in three places the first one's audit did not read: `APD-SVCCORE-003`'s §3 `**Primer**` field (three, two of them on blank"
        f" lines) and the §5.1 prose of `APD-SVCCORE-011` / `-015` and `APD-SVCCORE-012` (one each; {A} H1, {V} H1). The shift itself is proven by"
        " content — line N of `68f62f5b` is line N+3 today (`util/ad-hoc/2026-09-24_register_primer_anchor_audit.py`, which reads §4 cells only) —"
        " but that check holds for every non-blank line past 5758, so it cannot tell a right anchor from a wrong one. What shows each one right is"
        " reading it against the text its sentence quotes: `util/ad-hoc/2026-09-24_register_primer_citation_census.py` lays out every citation past"
        " 5758 beside the line it lands on (82 on 2026-09-24, each read).",
        1,
    ),
    # ---- section 4.9 ----------------------------------------------------------------------------------
    (
        "s4.9 park sentences name runs of rows (L7)",
        "is `—`, and each row's park status is stated in its own row-level sentence below the table (the",
        "is `—`, and each row's park status is stated below the table in a sentence that names it, one sentence sometimes covering a run of rows (the",
        1,
    ),
    (
        "ECO-010 the throttle's wiring, not its class (L7)",
        "The three siblings each wire a `FailedAuthThrottle` (juniper-data `api/security.py:297`, juniper-cascor `src/api/security.py:256`,"
        " juniper-service-core `juniper_service_core/security.py:341`); canopy's `src/` has none.",
        "The three siblings each wire a `FailedAuthThrottle` into `SecurityMiddleware`, which checks it before authenticating and records every 401"
        " (juniper-data `api/middleware.py:199-221` at `1afc3484`, juniper-cascor `src/api/middleware.py:195-217` at `ec8b5bdb`, juniper-service-core"
        " `juniper_service_core/middleware.py:216-238`; the class itself is at `api/security.py:297`, `src/api/security.py:256` and"
        f" `juniper_service_core/security.py:341`, which this row cited as the wiring until {BY}, {V} L7); canopy's `src/` has none.",
        1,
    ),
    (
        "DATA-055 four lock-less writers (L1)",
        "Neither of those two takes the lock, so the PATCH's guarantee fails even in ONE process:",
        "Neither of those two takes the lock, and nor do `POST /v1/datasets/batch-delete` and `POST /v1/datasets/cleanup-expired`, which call `delete`"
        " unlocked through `batch_delete` and `delete_expired` (`storage/base.py:590-615`, `:423-431` at `1afc3484`; this said \"those two\" alone"
        f" until {BY}, {V} L1), so the PATCH's guarantee fails even in ONE process:",
        1,
    ),
    (
        "DATA-055 #438 merged, all four locked, create not",
        "[juniper-data#438](https://github.com/pcalnon/juniper-data/pull/438), open when this was written, makes `DELETE` and batch-tags take the"
        " lock (`APD-DATA-057` records what the missing lock cost).",
        "[juniper-data#438](https://github.com/pcalnon/juniper-data/pull/438), open when this was written and merged 2026-09-24 after the v0.16.0"
        " cut, makes all four take it, while creating a dataset, as #438 merged, still took no per-dataset lock (`data438-round1-laneA-reprobe.md`"
        " F1); `APD-DATA-057` records what the missing lock cost.",
        1,
    ),
    (
        "ML-007 #2071 before the cut (N4)",
        "[juniper-ml#2071](https://github.com/pcalnon/juniper-ml/pull/2071) then added `--target-sha`, which tags a named commit and gates on that"
        " commit's own CI run.",
        "[juniper-ml#2071](https://github.com/pcalnon/juniper-ml/pull/2071), merged 52 seconds before that cut, added `--target-sha`, which tags a"
        " named commit and gates on that commit's own CI run; the v0.16.0 Release records its target as the SHA `39d1cab2…` where the default cuts"
        " of 0.14.0 and 0.15.0 record `main`, so this cut named its commit, which was main's HEAD either way *(this said #2071 came \"then\", after"
        f" the cut, until {BY}, {A} N4)*.",
        1,
    ),
    (
        "ML-008 the silent missing-data-clone path (H2)",
        "; a failed juniper-data or juniper-cascor clone skips every guard the same way, since juniper-ml's notes link into both (run on its own, the"
        " test would skip only those forks' sites: `OK (skipped=3)`);",
        "; a failed juniper-cascor clone fails that link check the same way, since four juniper-ml notes link into cascor. **A failed juniper-data"
        " clone is the silent case**: the clone step swallows the failure (`docs-full-check.yml:110`), no juniper-ml note links into juniper-data, so"
        " the link check passes, and the drift step then finds no ecosystem root (`_ROOT_ANCHOR_REPOS` needs juniper-data and juniper-cascor both)"
        " and skips all three cross-repo tests — every one of the 16 sibling sites, canopy's two included — so the job stays green with only the"
        " shared-package and registry checks run: `OK (skipped=3)` *(until 2026-09-24 this said a failed juniper-data clone failed the link check too,"
        " \"since juniper-ml's notes link into both\", and that the test \"would skip only those forks' sites\"; the post-merge validation of"
        " juniper-ml#2080 counted the links — one into canopy, four into cascor, none into juniper-data — and ran the test on synthetic roots:"
        f" {V} H2, {A} L1)*;",
        1,
    ),
    (
        "ML-008 remedy for the silent path",
        "Remedy candidates: markers scoped with `ast`, or behavioural arms (port canopy's three-key spy test into service-core, data and cascor) |",
        "Remedy candidates: markers scoped with `ast`, or behavioural arms (port canopy's three-key spy test into service-core, data and cascor); and,"
        " for the silent path, a variable only `docs-full-check.yml`'s drift step sets, under which a missing ecosystem root fails instead of"
        " skipping — not `GITHUB_ACTIONS=true` alone, which the validation proposed: every Actions job sets it, and `ci.yml:500` runs the same file"
        " there without siblings, so it would fail every CI run |",
        1,
    ),
    (
        "DATA-057 record_access scope (L2)",
        "`record_access`, which every metadata read and artifact download fires, takes the lock",
        "`record_access`, which the single-dataset metadata read and the artifact download fire (`api/routes/datasets.py:999`, `:1105`, `:1137`,"
        " `:1141`; `/latest`, the list, filter and versions routes record no access — this said \"every metadata read\" until"
        f" {BY}, {V} L2), takes the lock",
        1,
    ),
    (
        "DATA-057 the erased 200 was once (n=1)",
        "and a batch write erased a conditional PATCH's acknowledged 200.",
        f"and a batch write erased a conditional PATCH's acknowledged 200 (once, n=1; a forced interleaving reproduces it, {A} claim 17).",
        1,
    ),
    (
        "ruling quote 1 is an opening (N5)",
        "whose description, which the owner was shown, reads \"The fetch's",
        "whose description, which the owner was shown, begins \"The fetch's",
        1,
    ),
    (
        "ruling quote 1 ellipsis (N5)",
        "clears only once train, val and test have all been replaced.\"; and \"Keep while any split is fetched",
        "clears only once train, val and test have all been replaced. …\"; and \"Keep while any split is fetched",
        1,
    ),
    (
        "ruling quote 2 is an opening (N5)",
        "(Recommended)\" (07:53:26Z, session `8f86dec2`), described as \"The annotation stays whenever any",
        "(Recommended)\" (07:53:26Z, session `8f86dec2`), whose description begins \"The annotation stays whenever any",
        1,
    ),
    (
        "ruling quote 2 ellipsis (N5)",
        "partition the run uses came from a short fetch; it is null only when every partition is inline.\"",
        "partition the run uses came from a short fetch; it is null only when every partition is inline. …\"",
        1,
    ),
    (
        "ruling quotes archived in full (N5)",
        "change). Both calls are archived verbatim in",
        "change). Both calls, each description in full, are archived verbatim in",
        1,
    ),
    (
        "CASCOR-005 routing: #2059 merged 09-23 (N2)",
        "could not express a canopy guard until [juniper-ml#2059](https://github.com/pcalnon/juniper-ml/pull/2059) (`APD-ECO-008`, closed 2026-09-24).",
        "could not express a canopy guard until [juniper-ml#2059](https://github.com/pcalnon/juniper-ml/pull/2059) (merged 2026-09-23;"
        " `APD-ECO-008` closed 2026-09-24).",
        1,
    ),
    (
        "park DATA-057: #438 merged",
        "single-dataset route already takes, and juniper-data#438 applies it (open when filed). Close it when\n  #438 has merged and its validation holds.",
        "single-dataset route already takes, and juniper-data#438 applies it (open when filed; merged 2026-09-24 after the v0.16.0 cut, its"
        " batch-tags fix reproduced by `data438-round1-laneA-reprobe.md` claim 1). Close it when\n  the fix-forward of #438's validation has merged"
        " and its own validation holds.",
        1,
    ),
    # ---- section 5.1 ----------------------------------------------------------------------------------
    ("s5.1 SVCCORE-011 cite (H1)", 'so **pick one per package**" (7944)', 'so **pick one per package**" (7947)', 1),
    ("s5.1 SVCCORE-012 cite (H1)", "The primer states the risk precisely (8089):", "The primer states the risk precisely (8092):", 1),
    (
        "s5.1 drift gate is silent on a missing data clone (H2)",
        "*(not their behaviour: a regression that keeps the marker text passes, `APD-ML-008`; and canopy's three open rows,",
        "*(not their behaviour: a regression that keeps the marker text passes, `APD-ML-008`; not in `docs-full-check.yml` when the juniper-data"
        " clone fails, which skips every sibling site and stays green, `APD-ML-008` again; and canopy's three open rows,",
        1,
    ),
    # ---- section 6 ------------------------------------------------------------------------------------
    (
        "s6 freshness: which anchors were short (H1)",
        "juniper-ml#1098 inserted three at line 5758 on 2026-08-14, and every anchor past it was three short until 2026-09-24 (see §4's note);",
        "juniper-ml#1098 inserted three at line 5758 on 2026-08-14, and every anchor past it that the register took from the earlier text was three"
        " short until 2026-09-24 (see §4's note) — two §5.1 citations written on 2026-08-28 among them, copied from creation-era §4 cells, while"
        " `APD-RCLIENT-005`'s `8188-8195`, read from the primer itself on 2026-08-30, was right all along;",
        1,
    ),
]

REF_SUBS: list[tuple[str, str, str, int]] = [
    (
        "REFERENCE drift gate: the silent missing-data-clone path (H2)",
        "In `docs-full-check.yml` the cross-repo link check runs first and fails on a missing sibling, and the drift step has no `if: always()`, so"
        " there the step is skipped instead.",
        "In `docs-full-check.yml` the cross-repo link check runs first and fails on a missing canopy or cascor checkout, which juniper-ml's notes"
        " link into, and the drift step has no `if: always()`, so there the step is skipped instead. A missing juniper-data checkout is the silent"
        " case: no juniper-ml note links into juniper-data, so the link check passes, and the drift step finds no ecosystem root and skips every"
        " sibling site, green (`OK (skipped=3)`; `APD-ML-008` in the defect register).",
        1,
    ),
]

E1 = " **[Corrected: E.1](#e1-artifact-validator)**"
# line -> (exact current text, replacement). Every replacement is one line: nothing may move.
PRIMER_LINES: dict[int, tuple[str, str]] = {
    # L2 (lane A): restates E.1's refuted premise with neither a link nor a name.
    1954: (
        "juniper-data (v0.11.0) has a textbook caching candidate and emits no cache headers at all.",
        "juniper-data (v0.11.0) has a textbook caching candidate and emits no cache headers at all." + E1,
    ),
    # NIT (lane B): "a content-addressed identifier" -- E.1 item 2 says the scheme is not content-addressed.
    3346: (
        "This section covers the resource/endpoint/representation distinction, the noun rule and where it honestly breaks, collection and item"
        " patterns, identifier design, and the syntactic details that produce real bugs. It grounds in two juniper-data mechanisms: a load-bearing"
        " route-ordering dependency, and a content-addressed identifier with a deliberate escape hatch.",
        "This section covers the resource/endpoint/representation distinction, the noun rule and where it honestly breaks, collection and item"
        " patterns, identifier design, and the syntactic details that produce real bugs. It grounds in two juniper-data mechanisms: a load-bearing"
        " route-ordering dependency, and a content-addressed identifier with a deliberate escape hatch." + E1,
    ),
    # Observation (lane A): part of a verbatim RFC 9110 section 8.8.1 quote is bold with no attribution of the emphasis.
    4224: (
        "a validation request is received**.\" Hashing per response makes the 304 — the cheap case — cost a full-body hash.",
        "a validation request is received**.\" (Emphasis added.) Hashing per response makes the 304 — the cheap case — cost a full-body hash.",
    ),
    # L3 (lane B): the batch tag route kept losing tags through 0.16.0 (APD-DATA-057).
    5363: (
        "which lost tags to a concurrent race until juniper-data#263 and #282; since",
        "which lost tags to a concurrent race until juniper-data#263 and #282 (its batch route through 0.16.0); since",
    ),
    # L4 (lane B): the toy's "every error path" claim, scoped to what the code does.
    5378: (
        "  validation errors, which otherwise emit a differently shaped body.",
        "  validation errors, which otherwise emit a differently shaped body. (An exception nothing anticipated still reaches Starlette's plain-text 500.)",
    ),
    # L4 (lane B): a NaN / Infinity, or a non-numeric value, in a create's params reached canonical_json(...,
    # allow_nan=False) or int(...) unrefused and escaped as a text/plain 500; the schema now refuses both as a 422.
    # Strict, not lax: lax `int | float` would coerce `true` to 1 and "512" to 512, silently changing the input the
    # content-addressed id hashes.
    5400: (
        "from pydantic import BaseModel, ConfigDict, Field",
        "from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt",
    ),
    5498: (
        '    model_config = ConfigDict(extra="forbid")',
        '    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)  # Python\'s JSON parser accepts NaN and Infinity: refuse them as a 422',
    ),
    5502: (
        "    params: dict[str, Any] = Field(default_factory=dict)",
        "    params: dict[str, StrictInt | StrictFloat] = Field(default_factory=dict)  # JSON numbers only, never coerced: anything else is a 422, not a 500",
    ),
    # ...and the 422 handler must be able to echo a refused NaN: Starlette renders JSON with allow_nan=False.
    5631: (
        "            errors=json.loads(json.dumps(exc.errors(), default=str)),",
        "            errors=json.loads(json.dumps(exc.errors(), default=str), parse_constant=str),  # a refused NaN is echoed as \"NaN\"",
    ),
    # M1 (both lanes): the create response's ETag was compared by value, never hashed against its own body.
    5838: (
        "    assert first.headers[\"etag\"] == second.headers[\"etag\"] == '\"' + hashlib.sha256(second.content).hexdigest()[:32] + '\"'",
        "    assert first.headers[\"etag\"] == '\"' + hashlib.sha256(first.content).hexdigest()[:32] + '\"' == second.headers[\"etag\"] =="
        " '\"' + hashlib.sha256(second.content).hexdigest()[:32] + '\"'  # each tag is its own body's digest",
    ),
    # L4's test, on the blank line before the loop, so nothing moves.
    6119: (
        "",
        "        bad_nan = await client.post(\"/v1/datasets\", content=b'{\"generator\": \"spiral\", \"params\": {\"noise\": NaN}}',"
        " headers={\"Content-Type\": \"application/json\"})",
    ),
    6120: (
        "    for response in (bad_enum, bad_extra, bad_query):",
        "    for response in (bad_enum, bad_extra, bad_query, bad_nan):",
    ),
    # M1's claim made true, and the second correction recorded where the first is.
    9880: (
        "5838, 5857 and 5945) now also check that each metadata `ETag` is the digest of the exact body sent.",
        "5838, 5857 and 5945) now also check that each metadata `ETag` is the digest of the exact body sent — the POST-create 201's own body only"
        " since a second correction the same day, which also restricted a create's `params` to JSON numbers, so that NaN, Infinity or a"
        " non-integer `n_samples` is a 422 problem where it had been a plain-text 500 (lines 5400, 5498, 5502, 5631, 6119 and 6120).",
    ),
    # M2 (lane B): the bold rule was broader than its argument, and the RFC clause quoted does not cover field-order churn.
    9939: (
        "3. **A hash of serialized JSON is a strong validator.** The ETag-generation table (line 4220) rates",
        "3. **A hash of the exact bytes sent is a strong validator.** The ETag-generation table (line 4220) rates a hash of",
    ),
    9940: (
        "   one \"usually weak\". But a hash of the exact bytes sent changes whenever those bytes change, which is",
        "   serialized JSON \"usually weak\", which is right when the JSON hashed is not the JSON sent: a hash of some other",
    ),
    9941: (
        "   what §8.8.1 asks of a strong validator. Unstable field order or float formatting makes such a tag",
        "   serialization is strong only if nothing can change the bytes sent without changing it, and a serializer upgrade",
    ),
    9942: (
        "   change too often, never too rarely, and §8.8.1 allows that: \"A strong validator might change for",
        "   can. A hash of the exact bytes sent changes whenever those bytes change, which is what §8.8.1 asks of a strong",
    ),
    9943: (
        "   reasons other than a change to the representation data\". juniper-data's metadata `ETag` and II.11's",
        "   validator; unstable field order or float formatting only makes it change more often than the data does, which",
    ),
    9944: (
        "   are both such hashes.",
        "   costs revalidations but never serves stale bytes. juniper-data's metadata `ETag` and II.11's are both such hashes.",
    ),
    # L1 (lane B): four lock-less writers, not two; #438 has merged since.
    9973: (
        "  writers that take the same lock (through 0.16.0, `PATCH /v1/datasets/batch-tags` and `DELETE` took",
        "  writers that take the same lock (through 0.16.0, `PATCH /v1/datasets/batch-tags`, `DELETE`, `POST /v1/datasets/batch-delete` and"
        " `POST /v1/datasets/cleanup-expired` took",
    ),
    9974: (
        "  none; juniper-data#438 makes them take it), and per host at most: LocalFS orders processes with an",
        "  none; juniper-data#438, merged after 0.16.0, makes them take it, though creating a dataset, as it merged, took no per-dataset lock), and"
        " per host at most: LocalFS orders processes with an",
    ),
}

# Characters str.splitlines() breaks on besides "\n" (and "\r\n"); a new line holding one would read as one
# line to split("\n") and as two to splitlines(), the defect lane B found #2075's build proof could not see.
LINE_BREAKERS = "\r\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029"


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
    before = len(lines)
    for n, (old, new) in sorted(PRIMER_LINES.items()):
        if lines[n - 1] != old:
            raise SystemExit(f"FAIL primer line {n}: it does not hold the text this edit expects; nothing written\n  have: {lines[n - 1]!r}")
        bad = [c for c in new if c in LINE_BREAKERS]
        if bad:
            raise SystemExit(f"FAIL primer line {n}: the new text holds a line-breaking character {bad[0]!r}; nothing written")
        lines[n - 1] = new
    out = "\n".join(lines)
    after = out.split("\n")
    changed = [i + 1 for i, (a, b) in enumerate(zip(text.split("\n"), after)) if a != b]
    if len(after) != before or changed != sorted(PRIMER_LINES) or len(out.splitlines()) != len(text.splitlines()):
        raise SystemExit(f"FAIL primer: lines moved or unexpected lines changed ({len(after)} vs {before}; changed {changed}); nothing written")
    print(f"  ok  primer: {len(changed)} lines rewritten in place, {before} lines before and after, none moved")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    reg = (REPO / REG_REL).read_text(encoding="utf-8")
    if "| APD-DATA-057 |" not in reg:
        raise SystemExit("FAIL: the register lacks juniper-ml#2080's rows; build on #2080's merged content")
    if DONE_MARKER in reg:
        raise SystemExit("FAIL: this second fix-forward has already run")

    reg = apply(reg, REG_SUBS)
    primer = edit_primer((REPO / PRIMER_REL).read_text(encoding="utf-8"))
    ref = apply((REPO / REF_REL).read_text(encoding="utf-8"), REF_SUBS)

    if args.dry_run:
        print("dry run: nothing written")
        return 0
    base = args.out_dir if args.out_dir is not None else REPO
    for rel, text in ((REG_REL, reg), (PRIMER_REL, primer), (REF_REL, ref)):
        target = base / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        print(f"wrote {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
