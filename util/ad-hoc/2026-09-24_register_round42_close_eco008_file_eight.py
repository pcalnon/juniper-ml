#!/usr/bin/env python3
"""Defect-register round 42: close APD-ECO-008, file eight rows, and correct what rounds 3-4 refuted.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc register maintenance
Author:      Paul Calnon
Created:     2026-09-24
Version:     1.0.0
License:     MIT
Status:      single-use (round 42); retained as provenance

WHAT THIS DOES
--------------
One register edit, because every part of it moves the same counts:

1. **Closes `APD-ECO-008`** (juniper-canopy#660 + juniper-ml#2059; disclosure follow-up
   juniper-canopy#678). Five touches: the §4.9 row, its park/rulings entry, a §5.1 row, the §2
   list and count, the header date. The ruling's last step -- dispatch `docs-full-check` after the
   widening -- ran 2026-09-24 (run 35975353661: the drift step ran 11 tests, OK, none skipped).
2. **Files eight post-primer rows**, all awaiting an owner ruling: `APD-ECO-009` / `-010` / `-011`
   (canopy's missing body cap and failed-auth throttle, and its auth-off cross-site POST),
   `APD-DATA-054` / `-055` / `-056` (the weak artifact validator, the preconditions only PATCH
   honours, a lone-surrogate tag that durably 500s a dataset), `APD-ML-007` (the release ceremony
   can publish notes for a different release than it tags) and `APD-ML-008` (the drift gate's
   key-handling guards are satisfied by marker text).
3. **Corrects** what juniper-ml#2032's round-4 validation refuted (a close date, the guards'
   promotion history, claims overtaken by juniper-cascor#678, juniper-canopy#678 and
   juniper-ml#2059), the "seventy-nine" beside "eighty-one", and the ID-free Security /
   Correctness sentences that the new rows would make false.
4. **Records** the owner rulings of 2026-09-23 (service-core as a gate site, "Yes, same gate PR")
   and 2026-09-24 (mixed provenance: "Keep while any split is fetched").

Evidence: `reports/2026-09-24_defect-register-round-42/`.

WHY A SCRIPT
------------
Every replacement asserts it matched **exactly once**, and nothing is written unless all do. A
register edit that half-applies leaves the counts and the prose disagreeing while every
count-based check still passes. This script does not compute counts: re-derive afterwards with
`util/ad-hoc/register_open_set.py` (expect `134 rows | 100 fixed | 34 open`) and
`util/ad-hoc/register_status_crosscheck.py` (expect AGREE).

Run from the repo root; `--dry-run` writes nothing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REGISTER = REPO / "notes" / "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
REFERENCE = REPO / "docs" / "REFERENCE.md"

CANOPY660 = "[juniper-canopy#660](https://github.com/pcalnon/juniper-canopy/pull/660)"
CANOPY678 = "[juniper-canopy#678](https://github.com/pcalnon/juniper-canopy/pull/678)"
ML2059 = "[juniper-ml#2059](https://github.com/pcalnon/juniper-ml/pull/2059)"
CASCOR678 = "[juniper-cascor#678](https://github.com/pcalnon/juniper-cascor/pull/678)"
DATA428 = "[juniper-data#428](https://github.com/pcalnon/juniper-data/pull/428)"
DATA435 = "[juniper-data#435](https://github.com/pcalnon/juniper-data/pull/435)"
REPORTS = "`reports/2026-09-24_defect-register-round-42/`"

# ---------------------------------------------------------------------------------------------
# The eight new §4.9 rows (appended after the last row of the table, APD-CASCOR-013)
# ---------------------------------------------------------------------------------------------

NEW_ROWS = [
    "| APD-ECO-009 | **canopy's request-body cap counts only a declared `Content-Length`, so a chunked or under-declared body is never measured** — the streaming-body-cap shape `APD-DATA-002` closed in juniper-data, a guard its three siblings carry and canopy is not a gate site of (§2.3). `RequestBodyLimitMiddleware.dispatch` compares the header with `max_bytes` and passes any request without one straight to `call_next`; nothing counts the bytes received. Measured 2026-09-23 under both uvicorn parsers: a chunked body passes the cap; a request carrying both `Content-Length` and `Transfer-Encoding` got 64 bytes through under h11, and httptools refused it with 400. Found validating `APD-ECO-008`'s ruling — the first item of that entry's \"Residue\" | S | `juniper-canopy/src/middleware.py:59-74` (`main` `e9053227`) | — | High |",
    "| APD-ECO-010 | **canopy has no failed-authentication throttle, and its 401 path consumes no rate-limit budget** — the pre-auth-throttle shape `APD-DATA-001` † closed in juniper-data. The three siblings each wire a `FailedAuthThrottle` (juniper-data `api/security.py:297`, juniper-cascor `src/api/security.py:256`, juniper-service-core `juniper_service_core/security.py:341`); canopy's `src/` has none. And `SecurityMiddleware.dispatch` checks the key (`:129`) before it calls the rate limiter (`:132`), so a refused key raises out of the `try` before the limiter runs: wrong-key attempts are not counted at all. Found validating `APD-ECO-008`'s ruling — the second item of that entry's \"Residue\" | S | `juniper-canopy/src/middleware.py:77-133` (`main` `e9053227`) | — | High |",
    "| APD-ECO-011 | **In canopy's auth-off demo profile, any web page can regenerate the demo dataset with a cross-site \"simple\" POST.** Routes outside `/api/train/*` carry no Origin check, and `POST /api/dataset/generate` parses the body with `await request.json()` whatever its `Content-Type`, so a `text/plain` POST — which a browser sends cross-site without a CORS preflight — is accepted: measured 200 with a regenerated dataset. The route acts only in demo mode, and juniper-deploy's `juniper-canopy-demo` and `juniper-canopy-dev` services are open by design (no key), which is exactly where it is reachable. Not introduced by " + CANOPY660 + "; found in its second validation round. A canopy-behaviour row, so it also belongs in the canopy E2E ledger (`F-CANOPY-*`); filed here because it was found through `APD-ECO-008` | S | `juniper-canopy/src/main.py:1642-1654` (`main` `e9053227`) | — | High |",
    "| APD-DATA-054 | **The artifact's `ETag` can only be weak: nothing records a digest of the bytes a store serves.** `checksum` is `sha256(arrays_to_bytes(arrays))` — an UNCOMPRESSED `np.savez` with the keys sorted — while every store serves `np.savez_compressed` output, so `sha256(served bytes) != checksum` on every store, and identical arrays re-serialized (another numpy or zlib, another key order: the in-memory store sorts keys, the others do not) change the served bytes and keep the hash. " + DATA428 + " therefore sends `W/\"<checksum>\"` (owner ruling 2026-09-23: \"let's do option 1 now, and document this as a gap to be addressed in future work\"). Consequences: `If-Match` can match an artifact only through `*`, and `If-Range`, which accepts only a strong validator (RFC 9110 §13.1.5), cannot key a resumable download. Remedy of record: each store records the SHA-256 of the exact bytes it writes, with a fallback for artifacts written before it. | R | `core/artifacts.py:33-63`; `storage/local_fs.py:212`, `storage/memory.py:71`, `storage/redis_store.py:107`, `storage/postgres_store.py:392`; the gap is stated in `api/http_cache.py`'s module docstring | — | High |",
    "| APD-DATA-055 | **Only the tag PATCH honours preconditions, and its lost-update protection holds per host.** `DELETE /v1/datasets/{id}` does not evaluate `If-Match`, so a stale tag still deletes (RFC 9110 §13.1.1: an origin MUST NOT perform the method when an `If-Match` condition evaluates false), and `PATCH /v1/datasets/batch-tags` evaluates neither header. The PATCH's check-then-write runs under `DatasetStore._version_lock` plus LocalFS's per-dataset file lock; the Redis, Postgres and `CachedDatasetStore` stores inherit a no-op cross-process lock, so on them it holds within one process only. " + DATA428 + " documents all three and implements none | C | `api/routes/datasets.py` (`delete_dataset`, `batch_update_tags`); `storage/base.py` (`_version_lock`, `update_tags`) | — | High |",
    "| APD-DATA-056 | **A tag holding a lone surrogate makes its dataset answer 500 on every metadata read until the tag is removed, and each 500 logs caller-supplied text at ERROR.** `PATCH .../tags` with `add_tags=[\"\\ud800\"]` persists the tag; every later metadata GET or PATCH of that dataset fails to serialise (`PydanticSerializationError`, raised rendering `_metadata_response`), and the app's handler logs `\"Response serialization failed\"` with a traceback that carries the surrogate. Pre-existing, not from " + DATA428 + ": the untouched `GET /v1/datasets/filter` 500s on it too. Found by #428's round-3 validation (security lane) | R | `api/routes/datasets.py:138` (`_metadata_response`); `api/app.py:226-227` | — | High |",
    "| APD-ML-007 | **The release ceremony can publish notes for a different release from the one it tags, and a Release body cannot be re-cut.** `changelog_version_section` returns the FIRST `## [<version>]` heading's section only, and `create_release` runs `gh release create <tag>` with no `--target`, so the tag lands on the default branch's HEAD at cut time, whatever the CHANGELOG described. Both routes in were live on juniper-data 0.16.0 until " + DATA435 + " folded its CHANGELOG: an update-branch 3-way merge that DUPLICATED the version heading (the notes would have held #428's 8 bullets alone, dropped the 5 the release proposal cut — a BREAKING removal among them — and read \"Breaking changes: NO\"), and PRs merged between the version bump and the cut, whose entries sat in `[Unreleased]` while their code shipped in the tag. Remedy candidates: refuse a CHANGELOG with a repeated version heading; refuse to cut while `[Unreleased]` holds entries, or pass `--target` set to the commit whose CHANGELOG was rendered. Found by juniper-data#428's round-3 validation | C | `util/release_train/ceremony.py` (`changelog_version_section`, `create_release`) | — | High |",
    "| APD-ML-008 | **The fork-drift gate's two key-handling guards are satisfied by marker TEXT, so a regression that keeps the text passes.** `guard_is_present` is a whole-file substring match, and round 42's validation of " + ML2059 + " kept the gate green through seven constructed regressions at the canopy and juniper-service-core sites — among them `break` after a match, `return True` inside the loop, an early `any()` with the loop left below as dead code, and the pre-#660 constructor with its markers moved into a docstring — while a behavioural check caught all seven on service-core. The premise that made a marker \"the only possible check\" is false: " + CANOPY660 + "'s `test_validate_compares_every_key_even_when_the_first_matches` counts `compare_digest` calls across three keys; juniper-data's and juniper-cascor's spy tests use one key and cannot tell the two shapes apart. Adjacent gaps in the same gate: its cross-repo assertions run only in `docs-full-check.yml`, whose drift step has no `if: always()`, so an earlier failing step skips it — and with canopy's clone missing, the link check that runs first fails on a juniper-ml note linking into canopy, so the file-existence failure designed for a missing canopy is never reached; a failed juniper-data or juniper-cascor clone still skips every guard; `util/ad-hoc/2026-09-23_verify_shared_package_guard_sites_are_not_vacuous.py` mutates only by deleting markers; and the test file's comment that the service-core sites were unwatched until #2059 is wrong for the blank-key filter, whose removal service-core's own `test_security.py` catches — only the compare loop was unwatched. Remedy candidates: markers scoped with `ast`, or behavioural arms (port canopy's three-key spy test into service-core, data and cascor) | M | `tests/test_service_fork_drift.py` (`guard_is_present`; the `nonshortcircuit-key-compare` and `blank-api-key-filter` sites); `.github/workflows/docs-full-check.yml` (the drift step) | — | High |",
]

NEW_PARKS = """- `APD-ECO-009`, `APD-ECO-010`, `APD-ECO-011` — **filed 2026-09-24; awaiting an owner ruling, do
  not action.** The first two are canopy's missing copies of guards its three siblings carry, so the
  question mirrors `APD-ECO-008`'s: fix the code, and decide whether canopy becomes a site of
  `streaming-body-cap` and `pre-auth-throttle`. `APD-ECO-011`'s remedy is a canopy design choice (an
  Origin check on every state-changing route, or refusing a non-JSON body on `POST
  /api/dataset/generate`) in a profile that is open by design.
- `APD-DATA-054`, `APD-DATA-055`, `APD-DATA-056` — **filed 2026-09-24; awaiting an owner ruling, do
  not action.** `-054` is the gap the owner's 2026-09-23 ruling chose to document rather than close;
  `-055` records what juniper-data#428 documents rather than implements; `-056` predates #428.
- `APD-ML-007`, `APD-ML-008` — **filed 2026-09-24; awaiting an owner ruling, do not action.** `-007`
  is the owner's release path. `-008` asks whether the drift gate should test behaviour rather than
  text, which goes beyond what `APD-ECO-008`'s ruling asked for.
"""

ECO008_CLOSED = (
    "\n  **CLOSED 2026-09-24.** Code half: " + CANOPY660 + " (`3a6dea95`). Gate half: " + ML2059 + " (`f5222f9d`),\n"
    "  which adds juniper-canopy to `_FORK_REPOS`, makes canopy and juniper-service-core sites of both\n"
    "  key-handling guards (service-core's through the always-on `SharedPackageGuardTest`, which reads\n"
    "  this checkout), and keeps the ecosystem-root probe anchored on juniper-data and juniper-cascor, so\n"
    "  an absent canopy clone fails the gate instead of skipping it. The ruling's last step — dispatch the\n"
    "  workflow after the widening — ran 2026-09-24: `docs-full-check` run 35975353661, whose drift step\n"
    "  ran 11 tests, OK, none skipped. Disclosure follow-up: " + CANOPY678 + " (`05f2dfc2`), which\n"
    "  carries (2)'s figures and moves the WARNING into the lifespan, worded per source. **What the close\n"
    "  does not claim**: the gate matches marker TEXT, and round 42's validation of #2059 kept it green\n"
    "  through seven constructed regressions that preserve the markers (`APD-ML-008`); and service-core's\n"
    "  compare fix is on `main` only — its latest published wheel, 0.7.0, which juniper-recurrence pins,\n"
    "  still short-circuits. `main`'s squash messages for #660 (`3a6dea95`) and juniper-cascor#678\n"
    "  (`0e016a7`) are stale arm-time bodies; each repo's `CHANGELOG.md` is the record of what shipped.\n"
    "  Evidence: " + REPORTS + "."
)

# ---------------------------------------------------------------------------------------------
# (label, file, old, new) -- each OLD must occur exactly once in its file
# ---------------------------------------------------------------------------------------------

SUBS = [
    # ---- header and §1 ----
    ("header date", REGISTER, "**Last Updated**: 2026-09-23", "**Last Updated**: 2026-09-24"),
    ("§1 drift-check tense", REGISTER,
     "into a single failure mode and recommends a drift check that does not exist;",
     "into a single failure mode and recommends a drift check that did not exist when this was written *(it does now — §2.3)*;"),
    # ---- §2 status paragraph ----
    ("§2 seventy-nine", REGISTER,
     "and all seventy-nine are recorded in [§5](#5-fixed-findings-before-and-since-the-primer) with their PR and verification.",
     "and all eighty-one are recorded in [§5](#5-fixed-findings-before-and-since-the-primer) with their PR and verification *(this said \"seventy-nine\", two closes behind the count it follows, until 2026-09-24; found by juniper-ml#2032's round-3 validation)*."),
    ("§2 post-primer filed count", REGISTER, "thirty filed, of which (2026-09-09)", "thirty-eight filed, of which (2026-09-09)"),
    ("§2 post-primer list, counts", REGISTER,
     "/ `APD-DATA-053` ([juniper-data#417](https://github.com/pcalnon/juniper-data/pull/417)) — and twelve are open — **27 open in all**, 15 primer + 12 post-primer (the post-primer figure moved 7 → 12 on 2026-09-22 when five new `APD-ML-*` rows were filed against `util/experiments/`).",
     "/ `APD-DATA-053` ([juniper-data#417](https://github.com/pcalnon/juniper-data/pull/417)) and (2026-09-24) `APD-ECO-008` (" + CANOPY660 + " + " + ML2059 + ") — and nineteen are open — **34 open in all**, 15 primer + 19 post-primer (the post-primer figure moved 7 → 12 on 2026-09-22 when five new `APD-ML-*` rows were filed against `util/experiments/`, and 12 → 19 on 2026-09-24, when round 42 filed eight rows and closed `APD-ECO-008`)."),
    ("§2 Security class", REGISTER,
     "**The `Security` class and all three §2.3 drift groups are now closed** *(for the rows in §2.3's tables; `APD-ECO-008`, canopy's fourth copy of the two key-handling guards, filed 2026-09-22, is open)*. What remains is",
     "**The primer's `Security` rows and all three §2.3 drift groups are closed** *(for the rows in §2.3's tables. `APD-ECO-008`, canopy's fourth copy of the two key-handling guards, filed 2026-09-22, closed 2026-09-24. The same day round 42 filed three post-primer `S` rows, all open: `APD-ECO-009` and `APD-ECO-010` are canopy's missing body cap and failed-auth throttle — the copy-drift theme again, in a service the gate walks for two guards only — and `APD-ECO-011` is canopy's auth-off demo profile)*. Among the primer rows, what remains is"),
    ("§2 every Security entry", REGISTER,
     "**Every `Security` entry in this register is now `FIXED`.** All seven — `APD-DATA-001`–`-004`, `APD-CASCOR-004`, `APD-CASCOR-006`, `APD-SVCCORE-003` — are closed; every remaining open row is `C` / `R` / `M` / `E`. **`juniper-data` now has no open `Correctness` row either** — all ten are closed, and what is left there is `R` / `M` / `E`.",
     "**Every primer `Security` entry is `FIXED`.** All seven — `APD-DATA-001`–`-004`, `APD-CASCOR-004`, `APD-CASCOR-006`, `APD-SVCCORE-003` — are closed; every remaining open primer row is `C` / `R` / `M` / `E`. **The primer's `juniper-data` `Correctness` rows are all closed too** — all ten, and what is left of the primer's juniper-data rows is `R` / `M` / `E`. *(Until 2026-09-24 these sentences said \"every `Security` entry in this register\" and \"`juniper-data` now has no open `Correctness` row\". Round 42 made both false by filing open post-primer rows — three `S` (`APD-ECO-009`–`-011`) and one juniper-data `C` (`APD-DATA-055`) — and each sentence names no id, so no close-protocol grep would have routed a session here.)*"),
    ("§2 CORS last of fifteen (close date)", REGISTER,
     "the `OPTIONS`/CORS row was the last of the original fifteen to close (2026-08-20)",
     "the `OPTIONS`/CORS row was the last of the ten original copy-drift rows to close (2026-08-20)"),
    # ---- §2.3 ----
    ("§2.3 opening count", REGISTER,
     "`APD-ECO-008`, canopy's copy of the two key-handling guards, is an open seventeenth)*:",
     "`APD-ECO-008`, canopy's copy of the two key-handling guards, is a seventeenth, closed 2026-09-24; `APD-ECO-009` and `APD-ECO-010`, canopy's missing body cap and failed-auth throttle, are an eighteenth and a nineteenth, filed open that day)*:"),
    ("§2.3 copy-drift paragraph", REGISTER,
     "A drift check against `juniper-service-core` would catch these — all but the compare row, whose guard service-core lacked too until it was fixed alongside the forks. **All of this group is now closed, and every row is encoded** *(for the two forks the gate walks — a fourth copy of the two key-handling guards, in `juniper-canopy`, is `APD-ECO-008`; juniper-service-core's copy of the compare is not a gate site at all)*: each has been ported (or, for the two rows with no shared implementation, fixed independently in both forks) and is `ENFORCED` — promoted from `KNOWN_GAP`, except the compare row, which entered the gate already fixed and was added directly as `ENFORCED`. The `OPTIONS`/CORS row was the last of the original fifteen to close —",
     "A drift check against `juniper-service-core` would catch most of these — not the compare row, whose guard service-core lacked too until it was fixed alongside the forks, and not the two rows with no shared implementation (`(nowhere)` in the table), which had to be fixed independently in both forks. **All of this group's rows are closed and encoded** *(for the forks the gate walks. Since " + ML2059 + ", juniper-canopy and juniper-service-core are also sites of the two key-handling guards, which closed `APD-ECO-008`; canopy is a site of no other guard, and its missing body cap and failed-auth throttle are `APD-ECO-009` / `-010`, open)*: each has been ported (or, for the two rows with no shared implementation, fixed independently in both forks) and is `ENFORCED`. Two guards were promoted from `KNOWN_GAP` — `pre-auth-throttle` ([juniper-ml#1130](https://github.com/pcalnon/juniper-ml/pull/1130)) and `blank-api-key-filter` ([juniper-ml#1145](https://github.com/pcalnon/juniper-ml/pull/1145)); the other five entered the gate as `ENFORCED` — three in its first version ([juniper-ml#1103](https://github.com/pcalnon/juniper-ml/pull/1103)), after their fixes had merged, `cors-outside-auth` in [juniper-ml#1201](https://github.com/pcalnon/juniper-ml/pull/1201), and the compare row in [juniper-ml#1974](https://github.com/pcalnon/juniper-ml/pull/1974). *(Corrected 2026-09-24: this said every guard was \"promoted from `KNOWN_GAP`, except the compare row\", that a drift check against service-core would catch \"all but the compare row\", and that the CORS row was \"the last of the original fifteen\" — which also span the other two groups, whose last row closed 2026-08-28. All three came from juniper-ml#2032's round-3 fix pass; its round-4 validation refuted them from the gate's git history.)* The `OPTIONS`/CORS row was the last of the ten original copy-drift rows to close —"),
    ("§2.3 blockquote: seven guards", REGISTER,
     "a fourth copy of both key-handling guards, in `juniper-canopy`, is\n> `APD-ECO-008`)*.",
     "since " + ML2059 + " juniper-canopy and\n> juniper-service-core are sites of both key-handling guards, closing `APD-ECO-008`)*."),
    ("§2.3 blockquote: where the gate runs", REGISTER,
     "> The gate runs against sibling checkouts in `docs-full-check.yml`.",
     "> The gate runs against sibling checkouts in `docs-full-check.yml`, weekly or when dispatched; the\n> canopy sites first ran there on 2026-09-24 (run 35975353661: 11 tests, OK, none skipped). It checks\n> marker TEXT — see `APD-ML-008`."),
    ("§2.3 table: streaming body cap", REGISTER,
     "| ~~`juniper-data`~~ — **fixed** (`APD-DATA-002`, data#261)                                                        | `ENFORCED`                          |",
     "| ~~`juniper-data`~~ — **fixed** (`APD-DATA-002`, data#261); `juniper-canopy` — **open** (`APD-ECO-009`), not a site | `ENFORCED` (data, cascor) |"),
    ("§2.3 table: blank-key filter", REGISTER,
     "| ~~`juniper-data`, `juniper-cascor`~~ — **both fixed** (`APD-DATA-003` data#267, `APD-CASCOR-006` † cascor#527)   | `ENFORCED`                          |",
     "| ~~`juniper-data`, `juniper-cascor`, `juniper-canopy`~~ — **all fixed** (`APD-DATA-003` data#267, `APD-CASCOR-006` † cascor#527, `APD-ECO-008` canopy#660) | `ENFORCED` (canopy and service-core sites since ml#2059) |"),
    ("§2.3 table: pre-auth throttle", REGISTER,
     "| ~~`juniper-data`, `juniper-cascor`~~ — **both fixed** (`APD-DATA-001` † data#266, `APD-CASCOR-004` † cascor#524) | `ENFORCED`                          |",
     "| ~~`juniper-data`, `juniper-cascor`~~ — **both fixed** (`APD-DATA-001` † data#266, `APD-CASCOR-004` † cascor#524); `juniper-canopy` — **open** (`APD-ECO-010`), not a site | `ENFORCED` (data, cascor) |"),
    ("§2.3 table: key compare", REGISTER,
     "| ~~`juniper-cascor`, `juniper-service-core`~~ — **both fixed** (`APD-CASCOR-005` cascor#659, ml#1974)             | `ENFORCED`                          |",
     "| ~~`juniper-cascor`, `juniper-service-core`, `juniper-canopy`~~ — **all fixed** (`APD-CASCOR-005` cascor#659, ml#1974; `APD-ECO-008` canopy#660). service-core's fix is on `main` only: its latest published wheel, 0.7.0, which juniper-recurrence pins, still short-circuits | `ENFORCED` (canopy and service-core sites since ml#2059) |"),
    # ---- §4.9 intro ----
    ("§4.9 intro count", REGISTER,
     "**SEVEN rows below have a different provenance**, and the\ncount moved from two on 2026-09-22 —",
     "**FIFTEEN rows below have a different provenance**, and the\ncount moved from two on 2026-09-22, and from seven on 2026-09-24 —"),
    ("§4.9 intro: the eight", REGISTER,
     "the one it did not reach and the one its own audit walks past.**",
     "the one it did not reach and the one its own audit walks past.** The eight filed 2026-09-24 came\nfrom round 42's validation rounds, and each row says which: `APD-ECO-009`–`-011` and `APD-ML-008` from\nvalidating `APD-ECO-008`'s two PRs, and `APD-DATA-054`–`-056` and `APD-ML-007` from the rounds on\njuniper-data#428 (" + REPORTS + ")."),
    # ---- §4.9 table: APD-ECO-008 row ----
    ("§4.9 ECO-008 status", REGISTER,
     "| APD-ECO-008 | **There is a FOURTH `APIKeyAuth`, and the drift gate cannot express it.**",
     "| APD-ECO-008 | **FIXED (" + CANOPY660 + " + " + ML2059 + "; disclosure follow-up " + CANOPY678 + ")** — **There is a FOURTH `APIKeyAuth`, and the drift gate cannot express it** *(true until juniper-ml#2059)*."),
    ("§4.9 ECO-008 gate half", REGISTER,
     "The row stays open for the gate half.)*",
     "The gate half closed 2026-09-24: " + ML2059 + " put canopy and juniper-service-core on both key-handling guards, and the dispatched `docs-full-check` run 35975353661 ran the canopy sites for the first time — 11 tests, OK, none skipped.)*"),
    ("§4.9 ECO-008 anchors", REGISTER,
     "declares `_FORK_REPOS = (\"juniper-data\", \"juniper-cascor\")` at `:59`, and `test_every_guard_is_well_formed` asserts `site.repo in _FORK_REPOS` at `:285` — so a canopy site is rejected by the gate's own structural check and **no guard can reference canopy even in principle**.",
     "declared `_FORK_REPOS = (\"juniper-data\", \"juniper-cascor\")` at `:59`, and `test_every_guard_is_well_formed` asserted `site.repo in _FORK_REPOS` at `:285` *(both before juniper-ml#2059; on `main` the tuple, with canopy in it, is at `:68` and the assertion at `:338`)* — so a canopy site was rejected by the gate's own structural check and **no guard could reference canopy even in principle**."),
    # ---- §4.9 table: CASCOR-008 / -013 status notes (the close waits for the follow-up) ----
    ("§4.9 CASCOR-008 status", REGISTER,
     "| APD-CASCOR-008 | `_PROJECT_API_TRUNCATABLE_GENERATORS`",
     "| APD-CASCOR-008 | *(Implemented by " + CASCOR678 + ", merged 2026-09-23; open until the fix-forward of its post-merge validation lands — see the rulings below.)* `_PROJECT_API_TRUNCATABLE_GENERATORS`"),
    ("§4.9 CASCOR-013 status", REGISTER,
     "| APD-CASCOR-013 | `_dataset_shortfall` is written at one line and **never cleared**",
     "| APD-CASCOR-013 | *(Implemented by " + CASCOR678 + ", merged 2026-09-23, which writes it in three places now; open until the fix-forward of its post-merge validation lands, including the 2026-09-24 mixed-provenance ruling below.)* `_dataset_shortfall` is written at one line and **never cleared**"),
    # ---- present-tense "the gate cannot express canopy" claims found by the close's own sweep ----
    ("§2.4 CASCOR-005 ruling: cannot express", REGISTER,
     "found a FOURTH copy (juniper-canopy) that the drift gate cannot express.",
     "found a FOURTH copy (juniper-canopy) that the drift gate could not express until juniper-ml#2059 (`APD-ECO-008`, closed 2026-09-24)."),
    ("§4.9 intro: cannot name", REGISTER,
     "(a fourth copy the drift gate\ncannot name)",
     "(a fourth copy the drift gate\ncould not name until juniper-ml#2059)"),
    ("§4.9 ECO-008: over HTTP", REGISTER,
     "Over HTTP the reading holds as written.",
     "Over HTTP the conclusion holds, though not for the stated reason: a whitespace key ENABLED auth, which then refused every caller."),
    ("§4.9 ECO-008: source anchors", REGISTER,
     "(`_FORK_REPOS` at `:59`, the assertion at `:285`) | — | High |",
     "(`_FORK_REPOS` at `:59`, the assertion at `:285`, both before juniper-ml#2059) | — | High |"),
    # ---- §4.1: the three rows juniper-data#428 implemented (the close waits for its fix-forward) ----
    ("§4.1 DATA-017 status", REGISTER,
     "| APD-DATA-017   | No `ETag`/`Cache-Control`/conditional requests despite a stored SHA-256",
     "| APD-DATA-017   | *(Implemented by " + DATA428 + ", merged 2026-09-23, shipping in 0.16.0; open until the fix-forward of its round-3 validation lands.)* No `ETag`/`Cache-Control`/conditional requests despite a stored SHA-256"),
    ("§4.1 DATA-029 status", REGISTER,
     "| APD-DATA-029   | Two URIs return the same representation with no `Content-Location`",
     "| APD-DATA-029   | *(Implemented by " + DATA428 + ", merged 2026-09-23, shipping in 0.16.0; open until the fix-forward of its round-3 validation lands.)* Two URIs return the same representation with no `Content-Location`"),
    ("§4.1 DATA-032 status", REGISTER,
     "| APD-DATA-032   | Access counters live in the representation, blocking a strong metadata `ETag`",
     "| APD-DATA-032   | *(Implemented by " + DATA428 + ", merged 2026-09-23, shipping in 0.16.0; open until the fix-forward of its round-3 validation lands.)* Access counters live in the representation, blocking a strong metadata `ETag`"),
    # ---- §4.3 CASCOR-005 row and §5.1 CASCOR-005 row: the gate now names canopy ----
    ("§4.3 CASCOR-005: no guard can reference canopy", REGISTER,
     "— so **no guard can reference canopy even in principle**, and the gate that exists to catch copy drift is blind to a quarter of the copies.",
     "— so **no guard could reference canopy even in principle**, and the gate that exists to catch copy drift was blind to a quarter of the copies *(until juniper-ml#2059, 2026-09-23)*."),
    ("§4.3 CASCOR-005: widening is follow-up", REGISTER,
     "Widening `_FORK_REPOS` is follow-up.",
     "Widening `_FORK_REPOS` was follow-up, done by juniper-ml#2059 (`APD-ECO-008`, closed 2026-09-24)."),
    ("§5.1 CASCOR-005: gate cannot yet", REGISTER,
     "and the drift gate cannot yet express it — see `APD-ECO-008`. |",
     "and the drift gate could not express it until juniper-ml#2059 — see `APD-ECO-008`, closed 2026-09-24. |"),
    # ---- park block: CASCOR-013 ruling (reading marker + the 2026-09-24 ruling) ----
    ("CASCOR-013 ruling: reset() reading + mixed provenance", REGISTER,
     "Rejected: null because\n  nothing was fetched, which would report no shortfall for a run training on partial data — the\n  denial `APD-CASCOR-007` removed.",
     "Rejected: null because\n  nothing was fetched, which would report no shortfall for a run training on partial data — the\n  denial `APD-CASCOR-007` removed. *(The `reset()` clause is this entry's reading of \"follow the loaded\n  data\", not the owner's words; juniper-cascor#678 implements it.)*\n  **Mixed provenance RULED 2026-09-24: keep the annotation while any partition the run uses came from a\n  short fetch.** juniper-cascor#678's post-merge validation found the case the two clauses above leave\n  open: an inline train-only start after a partial fetch binds new `X` (so the annotation went null)\n  but keeps the fetch's `X_val` / `X_test` (retain-on-omit), and the run early-stops on and reports\n  those splits while status and `/v1/metrics` say null. Asked with three options, the owner chose\n  \"Keep while any split is fetched\" — the annotation is null only when every partition in use is\n  inline. Rejected: dropping the retained val/test (a training-behaviour change) and a per-partition\n  annotation (an API-shape change)."),
    # ---- park block: APD-ECO-008 entry ----
    ("ECO-008 entry: anchors pinned", REGISTER,
     "`src/security.py` gets the `matched`-flag compare (`:74`) **and** the blank-key filter (`:53`);",
     "`src/security.py` gets the `matched`-flag compare (`:74` at `48074653`) **and** the blank-key filter (`:53` at `48074653`);"),
    ("ECO-008 entry: three places, when", REGISTER,
     "read in exactly three places:",
     "read in exactly three places (as it stood when ruled, before juniper-ml#2059):"),
    ("ECO-008 entry: spaces and tabs", REGISTER,
     "both uvicorn parsers reduce an all-whitespace `X-API-Key` to empty;",
     "both uvicorn parsers reduce an `X-API-Key` of spaces and tabs to empty;"),
    ("ECO-008 entry: residue filed", REGISTER,
     "**Residue, not yet filed as rows**: two",
     "**Residue, filed 2026-09-24 as `APD-ECO-009` and `APD-ECO-010`**: two"),
    ("ECO-008 entry: service-core watched by nothing", REGISTER,
     "`matched` loop is watched by nothing: it is not a gate site, no behavioural test can tell it from\n  `any(...)`, and `juniper-service-core/CHANGELOG.md` nevertheless describes the guard as a marker in\n  this gate.",
     "`matched` loop was watched by nothing: it was not a gate site, and `juniper-service-core/CHANGELOG.md`\n  nevertheless described the guard as a marker in this gate. *(Owner ruling 2026-09-23, asked as \"Add\n  juniper-ml/service-core as a site of the two key-handling guards in the same gate PR?\": \"Yes, same\n  gate PR\" — done by juniper-ml#2059. The question's premise, \"no behavioral test can tell the loop\n  from `any()`\", is false: juniper-canopy#660's\n  `test_validate_compares_every_key_even_when_the_first_matches` counts `compare_digest` calls across\n  three keys and fails on a short-circuit. The ruling stands on its own terms; the premise is corrected\n  in `APD-ML-008`.)*"),
    ("ECO-008 entry: route count pinned", REGISTER,
     "measured: 55 method-path pairs, 27 of them state-changing, and the 25\n  parameterless GETs all 401 before the fix and 200 after.",
     "measured at canopy `26e0546f`: 55 method-path pairs, 27 of them state-changing, and the 25\n  parameterless GETs all 401 before the fix and 200 after (56 / 27 / 26 at `48074653`, the base #660\n  merged onto, because #662 added `GET /api/selection`)."),
    ("ECO-008 entry: canopy's record", REGISTER,
     "canopy's own record does not say it.",
     "canopy's own record did not say it until juniper-canopy#678 added it."),
    ("ECO-008 entry: (3) filed + CLOSED + new parks", REGISTER,
     "in canopy; (3) needs a row of its own and is not filed yet.\n",
     "in canopy, and juniper-canopy#678 did it; (3) is filed as `APD-ECO-011` (2026-09-24)." + ECO008_CLOSED + "\n" + NEW_PARKS),
    # ---- §5.1 ----
    ("§5.1 CASCOR-005: none can", REGISTER,
     "No behavioural test pins this, and none can** — `any(...)` and the flag loop return the same value for every input, so a test written to distinguish them passes against both and is vacuous (the §5.3 trap, in its sharpest form).",
     "No behavioural test pins this, and none can** — `any(...)` and the flag loop return the same value for every input, so a test written to distinguish them passes against both and is vacuous (the §5.3 trap, in its sharpest form). *(Corrected 2026-09-24: \"none can\" is false. A test that counts `compare_digest` CALLS — juniper-canopy#660's, over three keys — distinguishes them; only a test of the return value cannot. See `APD-ML-008`. And the service-core half is on `main` only: its latest published wheel, 0.7.0, which juniper-recurrence pins, still short-circuits.)*"),
    ("§5.1 all six guards", REGISTER,
     "now holds **all six** copy-drift guards as `ENFORCED`",
     "now holds **all six** *(seven since juniper-ml#1974)* copy-drift guards as `ENFORCED`"),
    ("docs/REFERENCE.md all six", REFERENCE,
     "all six copy-drift guards are `ENFORCED`.",
     "all seven copy-drift guards are `ENFORCED` (six until juniper-ml#1974 added `nonshortcircuit-key-compare`)."),
]

# (label, file, old, new, expected count): the few edits whose anchor legitimately occurs more than once
SUBS_N = [
    ("§4 legend: the #1098 anchor shift", REGISTER,
     "`Primer` gives the line in the primer asserting the claim; `Source` gives the current `file:line`.",
     "`Primer` gives the line in the primer asserting the claim; `Source` gives the current `file:line`. *(Corrected 2026-09-24: juniper-ml#1098 inserted three lines at primer line 5758 on 2026-08-14, after this register's anchors were taken, so an anchor past that line recorded at creation can be three short. The Appendix A anchors — Q26, Q57 and Q58, which had landed on blank lines or the wrong question — are corrected; the others past 5758 are unverified. Found by the round-42 validation of the primer's artifact-validator correction.)*", 1),
    ("§3 Q57 anchors", REGISTER, "Appendix A Q57 — lines 9592-9594", "Appendix A Q57 — lines 9595-9597", 2),
    ("§3 Q58 anchor", REGISTER, "Appendix A Q58 — lines 9596-9598", "Appendix A Q58 — lines 9599-9601", 1),
    ("§3 Q26 anchor", REGISTER, "Appendix A Q26 — line 9463", "Appendix A Q26 — line 9466", 1),
    ("§3 Q26 prose", REGISTER, "Q26 at 9463", "Q26 at 9466", 1),
    ("§4.3 CASCOR-005 primer cell", REGISTER, "| 1027-1029, 9463     |", "| 1027-1029, 9466     |", 1),
    ("§4.1 DATA-034 primer cell", REGISTER, "| 9596 (cascor sibling) |", "| 9599 (cascor sibling) |", 1),
    ("§4.1 DATA-035 primer cell", REGISTER, "| 9592 (cascor sibling) |", "| 9595 (cascor sibling) |", 1),
    ("§4.3 CASCOR-001a/b primer cells", REGISTER, "| 9592                |", "| 9595                |", 2),
    ("§4.3 CASCOR-002 primer cell", REGISTER, "| 9596                |", "| 9599                |", 1),
    ("§2.4 D-B ruling: the 2026-09-23 re-rulings", REGISTER,
     "The two rows are one fix: the counters are precisely what blocks the metadata ETag.",
     "The two rows are one fix: the counters are precisely what blocks the metadata ETag. *(Re-ruled 2026-09-23 for the artifact, when implementation found that the stored SHA-256 digests an UNCOMPRESSED, key-sorted serialization and not the bytes any store serves: \"let's do option 1 now, and document this as a gap to be addressed in future work\" — a weak `W/\"<checksum>\"`, with the byte-digest gap filed as `APD-DATA-054`. The metadata ETag is strong, the SHA-256 of the exact response body. Ruled the same day, because the counters' removal breaks `/v1`: \"Amend policy: 0.x may break v1\" — the API versioning policy lets `/v1` break while juniper-data is 0.x, flagged Breaking. Both shipped in juniper-data#428.)*", 1),
]

# §5.1 verification row for APD-ECO-008, appended after the last §5.1 row (APD-DATA-018's).
ECO008_51_ANCHOR = "| APD-DATA-018 | No async job pattern — generation runs inside the request |"
ECO008_51_ROW = (
    "| APD-ECO-008 | canopy's `APIKeyAuth` lacked the blank-key filter and the non-short-circuiting compare, and the drift gate could not name canopy | "
    + CANOPY660 + " + " + ML2059 + " (disclosure follow-up: " + CANOPY678 + ") | "
    "Both constructs are on canopy `main` at the gate's markers (`src/security.py:82`, `:112-116`). The gate, re-derived post-merge by round 42's "
    "independent validation: 11 tests OK against every sibling's `origin/main`, none skipped; the pre-#660 control (canopy `48074653`) fails exactly the two "
    "canopy subtests; a missing canopy checkout FAILS rather than skips; `SharedPackageGuardTest` is always on and runs in the required regression job; and the "
    "dispatched `docs-full-check` run 35975353661 (2026-09-24) ran the drift step: 11 tests, OK, none skipped. **Evidence of presence, not of behaviour**: seven "
    "marker-preserving regressions pass the gate (`APD-ML-008`). Reports: " + REPORTS + ". |"
)


def substitute(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"REFUSED [{label}]: anchor matched {count} times (need exactly 1); nothing written")
    return text.replace(old, new, 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    texts = {REGISTER: REGISTER.read_text(encoding="utf-8"), REFERENCE: REFERENCE.read_text(encoding="utf-8")}
    for label, path, old, new in SUBS:
        texts[path] = substitute(texts[path], old, new, label)
        print(f"  ok  {label}")
    for label, path, old, new, n in SUBS_N:
        got = texts[path].count(old)
        if got != n:
            raise SystemExit(f"REFUSED [{label}]: anchor matched {got} times (need exactly {n}); nothing written")
        texts[path] = texts[path].replace(old, new)
        print(f"  ok  {label} (x{n})")

    reg = texts[REGISTER]
    # New §4.9 rows go after the table's last row (APD-CASCOR-013's), whatever its text now says.
    start = reg.index("| APD-CASCOR-013 |")
    end = reg.index("\n", start)
    reg = reg[: end + 1] + "\n".join(NEW_ROWS) + "\n" + reg[end + 1 :]
    print(f"  ok  §4.9: {len(NEW_ROWS)} rows appended after APD-CASCOR-013")

    # §5.1: APD-ECO-008's verification row after APD-DATA-018's.
    if reg.count(ECO008_51_ANCHOR) != 1:
        raise SystemExit("REFUSED [§5.1 anchor]: APD-DATA-018 verification row not found exactly once")
    s = reg.index(ECO008_51_ANCHOR)
    e = reg.index("\n", s)
    reg = reg[: e + 1] + ECO008_51_ROW + "\n" + reg[e + 1 :]
    print("  ok  §5.1: APD-ECO-008 verification row added")
    texts[REGISTER] = reg

    if args.dry_run:
        print("--dry-run: nothing written")
        return 0
    for path, text in texts.items():
        path.write_text(text, encoding="utf-8")
        print(f"wrote {path.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
