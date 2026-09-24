#!/usr/bin/env python3
"""
Fix forward what juniper-ml#2074's post-merge validation refuted in the defect register; file APD-ECO-012.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register maintenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use editor; all-or-nothing, refuses to run twice
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

juniper-ml#2074 (defect-register round 42) was validated after merge, per the owner's 2026-09-24 policy
("validate after merge and fix forward"), by two independent lanes archived in
reports/2026-09-24_defect-register-round-42/ml2074-round1-laneA-reprobe.md and
reports/2026-09-24_defect-register-round-42/ml2074-round1-laneB-refute.md. The APD-ECO-008 close held;
the prose did not. This applies every finding that survived re-checking against source, to
notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md and docs/REFERENCE.md:

- every primer anchor the register took before juniper-ml#1098 shifted the primer by three lines,
  proven by content through util/ad-hoc/2026-09-24_register_primer_anchor_audit.py (section-4 cells)
  and the seven prose citations checked the same way;
- the claims that were false when #2074 made them, or that #2074 left standing on a line it edited;
- APD-ECO-012, canopy's copy of APD-CASCOR-001b (CORS inside auth), latent;
- the verbatim record of the two mixed-provenance rulings (owner-rulings-verbatim.md);
- APD-ML-007's facts after juniper-data v0.16.0 was cut and juniper-ml#2071 added --target-sha.

Each substitution must match exactly the number of times it declares, or nothing is written.

Usage: python3 util/ad-hoc/2026-09-24_register_round42_fixforward.py [--dry-run]
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REG = REPO / "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
REF = REPO / "docs/REFERENCE.md"
PRIMER = REPO / "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
AUDIT = REPO / "util/ad-hoc/2026-09-24_register_primer_anchor_audit.py"
R42 = "reports/2026-09-24_defect-register-round-42"
CANOPY_MAIN = "5907713b"

# (label, old, new, expected count)
SUBS: list[tuple[str, str, str, int]] = [
    # ---- section 1 -------------------------------------------------------------------------------
    (
        "s1 shape count",
        "groups sixteen entries *(fifteen when this was written)* into",
        "groups twenty entries *(fifteen when this was written; §2.3 records how each joined)* into",
        1,
    ),
    # ---- section 2 status paragraph -----------------------------------------------------------------
    ("s2 post-primer filed", "thirty-eight filed, of which", "forty filed, of which", 1),
    (
        "s2 open counts",
        "— and nineteen are open — **34 open in all**, 15 primer + 19 post-primer (the post-primer figure moved 7 → 12 on 2026-09-22 when five new `APD-ML-*` rows were filed against `util/experiments/`, and 12 → 19 on 2026-09-24, when round 42 filed eight rows and closed `APD-ECO-008`).",
        "— and twenty-one are open — **36 open in all**, 15 primer + 21 post-primer (the post-primer figure moved 7 → 12 on 2026-09-22 when five new `APD-ML-*` rows were filed against `util/experiments/`, 12 → 19 on 2026-09-24, when round 42 filed eight rows and closed `APD-ECO-008`, and 19 → 21 the same day, when round 42's fix-forward filed two more: canopy's CORS ordering and juniper-data's unlocked batch-tags write — no ids here, because the crosscheck reads every id on this line as closed).",
        1,
    ),
    (
        "s2 ten rulings",
        "**Ten of those carry owner rulings taken 2026-09-09** and are actionable; see the rulings block under [§4.9](#49-filed-after-the-primer).",
        "**Ten of those carried owner rulings taken 2026-09-09** and were actionable when this was written; most have since closed, so read the rulings block under [§4.9](#49-filed-after-the-primer), not this count.",
        1,
    ),
    (
        "s2 APD-ML count",
        "`util/ad-hoc/register_open_set.py` now prints `APD-ML  5` under OPEN by prefix, which is exactly the re-derivation the next sentence asks for.",
        "`util/ad-hoc/register_open_set.py` now lists `APD-ML` under OPEN by prefix, which is exactly the re-derivation the next sentence asks for *(this quoted the count, `APD-ML  5`, which round 42's two `APD-ML` rows made 7 two days later — so the count is gone)*.",
        1,
    ),
    (
        "s2 crosscheck blind spots",
        "pins the ID-keyed half: §4's `**FIXED` set, the §2 prose list and the §5.1 verification rows must name the same ids, and it reads all three independently.)*",
        "pins the ID-keyed half: §4's `**FIXED` set, the §2 prose list and the §5.1 verification rows must name the same ids, and it reads all three independently.)* *(Its blind spots, measured by mutation on 2026-09-24 — `reports/2026-09-24_defect-register-round-42/ml2074-round1-laneB-refute.md`, finding 10: an id that is also named in a parenthetical on the §2 status line satisfies the §2 touch even after it is dropped from the list itself, which is true of `APD-ECO-008`, `APD-DATA-047` and `APD-DATA-050`; and neither it nor `register_open_set.py` checks the prose counts or the `Sev` column, so a phantom open row moves the open-set count while the crosscheck still says AGREE.)*",
        1,
    ),
    (
        "s2 security and drift groups",
        "**The primer's `Security` rows and all three §2.3 drift groups are closed** *(for the rows in §2.3's tables. `APD-ECO-008`, canopy's fourth copy of the two key-handling guards, filed 2026-09-22, closed 2026-09-24. The same day round 42 filed three post-primer `S` rows, all open: `APD-ECO-009` and `APD-ECO-010` are canopy's missing body cap and failed-auth throttle — the copy-drift theme again, in a service the gate walks for two guards only — and `APD-ECO-011` is canopy's auth-off demo profile)*.",
        "**The primer's `Security` rows are closed, and so are all three §2.3 drift groups but for three canopy rows** *(`APD-ECO-008`, canopy's fourth copy of the two key-handling guards, filed 2026-09-22, closed 2026-09-24. The same day round 42 filed three post-primer `S` rows, all open: `APD-ECO-009` and `APD-ECO-010` are canopy's missing body cap and failed-auth throttle — the copy-drift theme again, in a service the gate walks for two guards only — and `APD-ECO-011` is canopy's auth-off demo mode; its fix-forward then filed `APD-ECO-012`, canopy's copy of the CORS-inside-auth defect, `C` and latent. `APD-ECO-009`, `-010` and `-012` sit in §2.3's tables, so until that fix-forward this sentence called the groups closed while its own tables showed them open)*.",
        1,
    ),
    (
        "s2 correction note",
        "*(Until 2026-09-24 these sentences said \"every `Security` entry in this register\" and \"`juniper-data` now has no open `Correctness` row\". Round 42 made both false by filing open post-primer rows — three `S` (`APD-ECO-009`–`-011`) and one juniper-data `C` (`APD-DATA-055`) — and each sentence names no id, so no close-protocol grep would have routed a session here.)*",
        "*(Until 2026-09-24 these sentences said \"every `Security` entry in this register\" and \"`juniper-data` now has no open `Correctness` row\". The second had been false since 2026-09-09, when juniper-ml#1864 filed `APD-DATA-046` (juniper-data, `C`, open) — fifteen days and several rounds unnoticed — and round 42 added `APD-DATA-055` and `APD-DATA-057`; round 42 made the first false by filing three open `S` rows, `APD-ECO-009`–`-011`. Neither sentence names the rows that falsified it — the first names only the seven it covers — so no close-protocol grep would have routed a session here. This note itself first blamed round 42 alone; the post-merge validation of juniper-ml#2074 corrected it: `reports/2026-09-24_defect-register-round-42/ml2074-round1-laneA-reprobe.md` and `reports/2026-09-24_defect-register-round-42/ml2074-round1-laneB-refute.md`.)*",
        1,
    ),
    (
        "s2 copy-drift closes",
        "That closes every item in §2.2's ranked list **and every copy-drift row in §2.3** — the `OPTIONS`/CORS row",
        "That closed every item in §2.2's ranked list **and every copy-drift row §2.3 then held** *(three canopy rows have joined it since, all open: `APD-ECO-009`, `-010`, `-012`)* — the `OPTIONS`/CORS row",
        1,
    ),
    # ---- section 2.2 ----------------------------------------------------------------------------------
    (
        "s2.2 only vector",
        "The only unauthenticated memory-exhaustion vector in the register when the service runs in the open bare/dev profile —",
        "The only unauthenticated memory-exhaustion vector in the register when the service runs in the open bare/dev profile *(when this was ranked; `APD-ECO-009`, filed 2026-09-24, is canopy's copy of the same gap)* —",
        1,
    ),
    (
        "s2.2 item 3 batch route",
        "3. **`APD-DATA-006` — a `GET` can silently undo a write.** `record_access` rewrites the whole metadata document under a lock the tag-update path does not take.",
        "3. **`APD-DATA-006` — a `GET` can silently undo a write.** *(Fixed on the single-dataset tag route by juniper-data#263; `PATCH /v1/datasets/batch-tags` kept the defect through 0.16.0 — `APD-DATA-057`, filed 2026-09-24.)* `record_access` rewrites the whole metadata document under a lock the tag-update path does not take.",
        1,
    ),
    (
        "s2.2 primer length",
        "and `FailedAuthThrottle` appears zero times in its 9,863 lines.",
        "and `FailedAuthThrottle` appears zero times in its 9,863 lines *(9,866 since juniper-ml#1098 inserted three; still zero on 2026-09-24)*.",
        1,
    ),
    # ---- section 2.3 ----------------------------------------------------------------------------------
    (
        "s2.3 lead count",
        "Sixteen entries share one shape *(fifteen until the non-short-circuiting compare row, `APD-CASCOR-005`, joined the copy-drift table; `APD-ECO-008`, canopy's copy of the two key-handling guards, is a seventeenth, closed 2026-09-24; `APD-ECO-009` and `APD-ECO-010`, canopy's missing body cap and failed-auth throttle, are an eighteenth and a nineteenth, filed open that day)*:",
        "Twenty entries share one shape *(fifteen originally; the non-short-circuiting compare row, `APD-CASCOR-005`, made sixteen when it joined the copy-drift table; `APD-ECO-008`, canopy's copy of the two key-handling guards, is a seventeenth, closed 2026-09-24; `APD-ECO-009` and `APD-ECO-010`, canopy's missing body cap and failed-auth throttle, are an eighteenth and a nineteenth, filed open that day; and `APD-ECO-012`, canopy's copy of the CORS-inside-auth defect, is a twentieth, filed open the same day by the fix-forward of round 42's post-merge validation)*:",
        1,
    ),
    (
        "s2.3 group closed",
        "**All of this group's rows are closed and encoded** *(for the forks the gate walks. Since [juniper-ml#2059](https://github.com/pcalnon/juniper-ml/pull/2059), juniper-canopy and juniper-service-core are also sites of the two key-handling guards, which closed `APD-ECO-008`; canopy is a site of no other guard, and its missing body cap and failed-auth throttle are `APD-ECO-009` / `-010`, open)*:",
        "**All of this group's rows but three are closed and encoded** *(the three are canopy's: its missing body cap and failed-auth throttle, `APD-ECO-009` / `-010`, and its CORS-inside-auth ordering, `APD-ECO-012` — all open. Since [juniper-ml#2059](https://github.com/pcalnon/juniper-ml/pull/2059), juniper-canopy and juniper-service-core are also sites of the two key-handling guards, which closed `APD-ECO-008`; canopy is a site of no other guard. \"Encoded\" means the markers are pinned, not the behaviour: a regression that keeps its marker text passes the gate, `APD-ML-008`)*:",
        1,
    ),
    (
        "s2.3 refuted from",
        "All three came from juniper-ml#2032's round-3 fix pass; its round-4 validation refuted them from the gate's git history.)*",
        "All three came from juniper-ml#2032's round-3 fix pass; its round-4 validation refuted them — the promotions from the gate's git history, the CORS date from juniper-cascor-client#143's merge date, and \"all but the compare row\" from this table's `(nowhere)` cells.)*",
        1,
    ),
    (
        "s2.3 last one promoted",
        "The last one promoted,\n> `cors-outside-auth`, needed a mechanism the others did not:",
        "One of them,\n> `cors-outside-auth` (entered `ENFORCED` in juniper-ml#1201, never a `KNOWN_GAP`), needed a mechanism the others did not:",
        1,
    ),
    (
        "s2.3 CORS table row",
        "~~`juniper-cascor`, `juniper-data`~~ — **both fixed** (`APD-CASCOR-001b` cascor#540, `APD-DATA-035` † data#273)   |",
        "~~`juniper-cascor`, `juniper-data`~~ — **both fixed** (`APD-CASCOR-001b` cascor#540, `APD-DATA-035` † data#273); `juniper-canopy` — **open**, latent (`APD-ECO-012`), not a site |",
        1,
    ),
    # ---- the seven prose primer citations (content-checked like the section-4 cells) --------------
    ("prose 7950", "At 7950-7951 it calls it", "At 7953-7954 it calls it", 1),
    ("prose 7964", "at 7964-7965 it names the benefit", "at 7967-7968 it names the benefit", 1),
    ("prose 7967", "typo pair (7967-7968)", "typo pair (7970-7971)", 1),
    ("prose 7615/6343", "(\"73-line\", 7615; \"60 lazy names\", 6343)", "(\"73-line\", 7618; \"60 lazy names\", 6346)", 1),
    ("prose 7332", "file headers at 7332-7337", "file headers at 7335-7340", 1),
    ("prose 7445", "says at 7445-7446 that", "says at 7448-7449 that", 1),
    # ---- section 4 legend ---------------------------------------------------------------------------
    (
        "s4 legend anchors",
        "*(Corrected 2026-09-24: juniper-ml#1098 inserted three lines at primer line 5758 on 2026-08-14, after this register's anchors were taken, so an anchor past that line recorded at creation can be three short. The Appendix A anchors — Q26, Q57 and Q58, which had landed on blank lines or the wrong question — are corrected; the others past 5758 are unverified. Found by the round-42 validation of the primer's artifact-validator correction.)*",
        "*(Corrected 2026-09-24: juniper-ml#1098 inserted three lines at primer line 5758 on 2026-08-14, ten hours after this register was created, and it is the only commit to touch the primer since, so every anchor past that line recorded at creation was three short. Round 42 first corrected the Appendix A anchors Q26, Q57 and Q58, which had landed on blank lines or the wrong question; its fix-forward then corrected all the rest — {cells} anchors in {rows} rows' `Primer` cells, {blank} of which had landed on blank lines, and 7 in the prose — each proven by content: line N of the primer the register was built against (`68f62f5b`) is line N+3 today (`util/ad-hoc/2026-09-24_register_primer_anchor_audit.py`). `APD-DCLIENT-008`'s `6592` was a blank line even at creation; it now names the paragraph it meant, `6596`. Found by the round-42 validation of the primer's artifact-validator correction, and of juniper-ml#2074.)*",
        1,
    ),
    # ---- section 4 rows -------------------------------------------------------------------------------
    (
        "DATA-017/-029/-032 release",
        "merged 2026-09-23, shipping in 0.16.0; open until the fix-forward of its round-3 validation lands.)*",
        "merged 2026-09-23, in the v0.16.0 Release (cut 2026-09-24 at `39d1cab2`; PyPI still served 0.15.0 that day, its publish awaiting approval); open until the fix-forward of its round-3 validation lands.)*",
        3,
    ),
    (
        "CASCOR-005 routing",
        "`juniper-canopy/src/security.py` is a fourth, still unfixed, and `juniper-ml/tests/test_service_fork_drift.py` cannot express a canopy guard at all.",
        "`juniper-canopy/src/security.py` was a fourth, unfixed until [juniper-canopy#660](https://github.com/pcalnon/juniper-canopy/pull/660) (2026-09-23), and `juniper-ml/tests/test_service_fork_drift.py` could not express a canopy guard until [juniper-ml#2059](https://github.com/pcalnon/juniper-ml/pull/2059) (`APD-ECO-008`, closed 2026-09-24).",
        1,
    ),
    (
        "s4.9 provenance count",
        "`reports/2026-09-08_round-37-consensus/`). **FIFTEEN rows below have a different provenance**, and the\ncount moved from two on 2026-09-22, and from seven on 2026-09-24 — `APD-ML-002`–`-006` were filed that day from the cursor-fleet\nround-2 close-out,",
        "`reports/2026-09-08_round-37-consensus/`); round 38 filed its sixteen rows\n([juniper-ml#1858](https://github.com/pcalnon/juniper-ml/pull/1858)). **TWENTY-FOUR rows below have a different provenance**\n*(corrected 2026-09-24: this said two, then seven, then fifteen, and undercounted each time, because each\nedit counted only the rows it added. It missed `APD-DATA-046`, filed 2026-09-09 with the owner's rulings\nby juniper-ml#1864, and `APD-DATA-047`–`-052`, filed by round 39 in juniper-ml#1947; the filing commit of\nevery row is printed by `util/ad-hoc/2026-09-24_register_row_filing_commits.py`)*. `APD-ML-002`–`-006`\nwere filed on 2026-09-22 from the cursor-fleet round-2 close-out,",
        1,
    ),
    (
        "s4.9 round-42 provenance",
        "The eight filed 2026-09-24 came\nfrom round 42's validation rounds, and each row says which: `APD-ECO-009`–`-011` and `APD-ML-008` from\nvalidating `APD-ECO-008`'s two PRs, and `APD-DATA-054`–`-056` and `APD-ML-007` from the rounds on\njuniper-data#428 (`reports/2026-09-24_defect-register-round-42/`).",
        "The ten filed 2026-09-24 came\nfrom round 42, and each row says which: `APD-ECO-009` and `-010` from validating `APD-ECO-008`'s ruling\n(the residue juniper-ml#2032 recorded, `ml2032-round3-validation.md`), `APD-ECO-011` and `APD-ML-008` from\nvalidating its two PRs, `APD-DATA-054` from implementing juniper-data#428, `APD-DATA-055`, `-056` and\n`APD-ML-007` from #428's validation rounds, `APD-ECO-012` from the post-merge validation of\njuniper-ml#2074, which filed the first eight, and `APD-DATA-057` from round 2 of the primer correction's\nvalidation (all in `reports/2026-09-24_defect-register-round-42/`).",
        1,
    ),
    (
        "CASCOR-013 source",
        "(init, the single write in `_reload_dataset`, the read in `get_status`)",
        "(init, the single write in `_reload_dataset` — three since juniper-cascor#678 — and the read in `get_status`)",
        1,
    ),
    (
        "ECO-011 row",
        "**In canopy's auth-off demo profile, any web page can regenerate the demo dataset with a cross-site \"simple\" POST.** Routes outside `/api/train/*` carry no Origin check, and `POST /api/dataset/generate` parses the body with `await request.json()` whatever its `Content-Type`, so a `text/plain` POST — which a browser sends cross-site without a CORS preflight — is accepted: measured 200 with a regenerated dataset. The route acts only in demo mode, and juniper-deploy's `juniper-canopy-demo` and `juniper-canopy-dev` services are open by design (no key), which is exactly where it is reachable. Not introduced by [juniper-canopy#660](https://github.com/pcalnon/juniper-canopy/pull/660); found in its second validation round. A canopy-behaviour row, so it also belongs in the canopy E2E ledger (`F-CANOPY-*`); filed here because it was found through `APD-ECO-008` | S | `juniper-canopy/src/main.py:1642-1654` (`main` `e9053227`) |",
        "**In canopy's auth-off demo mode, a cross-site \"simple\" POST regenerates the demo dataset.** With auth off no HTTP route checks `Origin`: `require_browser_control_auth` returns before its Origin step (`src/security.py:453-455`), and cross-site `text/plain` POSTs to `/api/train/pause`, `/resume` and `/stop` measured 200 too. `POST /api/dataset/generate` reads the body with `await request.json()` whatever its `Content-Type`, and falls back to `{}` when it cannot parse it (`src/main.py:1651-1654`), so a `text/plain` POST — which a browser sends cross-site without a CORS preflight — is accepted: measured 200 with a regenerated dataset. The route acts only in demo mode (`:1645-1646`). Of juniper-deploy's two keyless canopy services only `juniper-canopy-dev` runs it (`JUNIPER_CANOPY_DEMO_MODE: \"true\"`); `juniper-canopy-demo` names a cascor URL and runs `ServiceBackend`, so the route answers 400 there, unless cascor-demo is unreachable at boot and canopy falls back to the demo backend (`src/main.py:420-434`). Both bind `${BIND_HOST:-127.0.0.1}`, so by default the attacker is a page open in a browser on the same host; no browser run was made. juniper-deploy's `CHANGELOG.md:179` says both run demo mode; only `-dev` does. Not introduced by [juniper-canopy#660](https://github.com/pcalnon/juniper-canopy/pull/660); found in its second validation round. A canopy-behaviour row with no `F-CANOPY` id yet; filed here because it was found through `APD-ECO-008` *(corrected 2026-09-24 by juniper-ml#2074's post-merge validation, which found `juniper-canopy-demo` in service mode and the Origin gap on every route)* | S | `juniper-canopy/src/main.py:1642-1654`, `:420-434`; `src/security.py:453-455` (`main` `" + CANOPY_MAIN + "`) |",
        1,
    ),
    (
        "DATA-054 can change",
        "the in-memory store sorts keys, the others do not) change the served bytes and keep the hash.",
        "the in-memory store sorts keys, the others do not) can change the served bytes and keep the hash.",
        1,
    ),
    (
        "DATA-054 remedy + provenance",
        "Remedy of record: each store records the SHA-256 of the exact bytes it writes, with a fallback for artifacts written before it. |",
        "Remedy, which that ruling deferred: each store records the SHA-256 of the exact bytes it writes, with a fallback for artifacts written before it. Found implementing juniper-data#428 (§2.4's re-ruling note), and confirmed by its first validation round (`data428-round1-laneA-reprobe.md`) |",
        1,
    ),
    (
        "DATA-055 row",
        "**Only the tag PATCH honours preconditions, and its lost-update protection holds per host.** `DELETE /v1/datasets/{id}` does not evaluate `If-Match`, so a stale tag still deletes (RFC 9110 §13.1.1: an origin MUST NOT perform the method when an `If-Match` condition evaluates false), and `PATCH /v1/datasets/batch-tags` evaluates neither header. The PATCH's check-then-write runs under `DatasetStore._version_lock` plus LocalFS's per-dataset file lock; the Redis, Postgres and `CachedDatasetStore` stores inherit a no-op cross-process lock, so on them it holds within one process only. [juniper-data#428](https://github.com/pcalnon/juniper-data/pull/428) documents all three and implements none |",
        "**Only the tag PATCH honours preconditions, and its lost-update protection holds only against writers that take the store lock.** `DELETE /v1/datasets/{id}` does not evaluate `If-Match`, so a stale tag still deletes (RFC 9110 §13.1.1: an origin MUST NOT perform the method when an `If-Match` condition evaluates false), and `PATCH /v1/datasets/batch-tags` evaluates neither header. Neither of those two takes the lock, so the PATCH's guarantee fails even in ONE process: in a single LocalFS uvicorn worker an acknowledged batch-tags edit was lost to a conditional PATCH (1 of 240, live; 0 of 240 in the control), and a PATCH answered 200 with a new `ETag` for a dataset `DELETE` had just removed. Among lock-takers the PATCH's check-then-write runs under `DatasetStore._version_lock` plus LocalFS's per-dataset file lock; the Redis, Postgres and `CachedDatasetStore` stores inherit a no-op cross-process lock, so on them it holds within one process only. [juniper-data#428](https://github.com/pcalnon/juniper-data/pull/428) documents all three and implements none; [juniper-data#438](https://github.com/pcalnon/juniper-data/pull/438), open when this was written, makes `DELETE` and batch-tags take the lock (`APD-DATA-057` records what the missing lock cost). Found by #428's round-2 validation (`data428-round2-validation.md` item 7) and extended by round 3 (`data428-round3-laneB-refute.md` finding 1, `data428-round3-laneA2-claims.md` F2) *(the title said the protection \"holds per host\" until juniper-ml#2074's post-merge validation)* |",
        1,
    ),
    (
        "ML-007 headline",
        "**The release ceremony can publish notes for a different release from the one it tags, and a Release body cannot be re-cut.**",
        "**The release ceremony can publish notes for a different release from the one it tags, and never re-renders a Release it finds.**",
        1,
    ),
    (
        "ML-007 after the cut",
        "or pass `--target` set to the commit whose CHANGELOG was rendered. Found by juniper-data#428's round-3 validation |",
        "or pass `--target` set to the commit whose CHANGELOG was rendered. Found by juniper-data#428's round-3 validation. *(Updated 2026-09-24, after filing. \"A Release body cannot be re-cut\" was the ceremony's own comment (`ceremony.py:462`), not a GitHub limit: `gh release edit` can replace a body, and it is the ceremony's policy to resume monitoring and never re-cut (`:1011`). juniper-data v0.16.0 was cut at 08:52:14Z, tagging `39d1cab2` — #435's fold, main's HEAD at the cut — and its notes are that commit's one `[0.16.0]` section, every non-blank line in order, 15 top-level bullets (the renderer drops 4 blank lines between items; `util/ad-hoc/2026-09-24_verify_data_0_16_0_notes_match_tag.py`); so the fold, not the tool, closed both routes for this release. [juniper-ml#2071](https://github.com/pcalnon/juniper-ml/pull/2071) then added `--target-sha`, which tags a named commit and gates on that commit's own CI run. It is opt-in: by default the tag still lands on main at cut time, the notes still come from the `--ecosystem-root` checkout, which nothing checks is at the target, and `changelog_version_section` still returns the first heading. Open.)* |",
        1,
    ),
    (
        "ML-008 clone skip",
        "a failed juniper-data or juniper-cascor clone still skips every guard;",
        "a failed juniper-data or juniper-cascor clone skips every guard the same way, since juniper-ml's notes link into both (run on its own, the test would skip only those forks' sites: `OK (skipped=3)`);",
        1,
    ),
    # ---- section 4.9 park and rulings -------------------------------------------------------------------
    (
        "DATA-047 park note",
        "`APD-ML-002` … `APD-ML-006` were filed needing one before code is written, and still do.)*",
        "`APD-ML-002` … `APD-ML-006` were filed needing one before code is written, and still do. **False a\n  third way from 2026-09-24**: round 42 filed eight rows awaiting a ruling, and its fix-forward a ninth\n  — see the park block below the §4.9 table.)*",
        1,
    ),
    (
        "mixed-provenance heading",
        "keep the annotation while any partition the run uses came from a\n  short fetch.**",
        "keep the annotation (and `current_dataset`) while any partition the\n  run uses came from a short fetch.**",
        1,
    ),
    (
        "mixed-provenance verbatim",
        "  those splits while status and `/v1/metrics` say null. Asked with three options, the owner chose\n  \"Keep while any split is fetched\" — the annotation is null only when every partition in use is\n  inline. Rejected: dropping the retained val/test (a training-behaviour change) and a per-partition\n  annotation (an API-shape change).",
        "  those splits while status and `/v1/metrics` say null. Two sessions asked, each with three options,\n  and the owner chose the same rule both times: \"Keep while fetched splits stay (Recommended)\"\n  (07:32:48Z, session `bc31e993`), whose description, which the owner was shown, reads \"The fetch's\n  annotation (and current_dataset) stays for as long as any of its partitions is still loaded. It\n  clears only once train, val and test have all been replaced.\"; and \"Keep while any split is fetched\n  (Recommended)\" (07:53:26Z, session `8f86dec2`), described as \"The annotation stays whenever any\n  partition the run uses came from a short fetch; it is null only when every partition is inline.\"\n  The first names `current_dataset`; the second question did not. Rejected both times: dropping the\n  retained val/test (a training-behaviour change) and a per-partition annotation (an API-shape\n  change). Both calls are archived verbatim in\n  `reports/2026-09-24_defect-register-round-42/owner-rulings-verbatim.md`.",
        1,
    ),
    (
        "canopy docstring quote",
        "posture `src/security.py`'s module docstring describes as \"disabled when unset\")",
        "posture `src/security.py`'s module docstring describes as \"disabled when unset\" — on canopy `main` `" + CANOPY_MAIN + "` it reads \"Disabled when unset, empty or whitespace-only\")",
        1,
    ),
    (
        "ECO-011 park remedy",
        "`APD-ECO-011`'s remedy is a canopy design choice (an\n  Origin check on every state-changing route, or refusing a non-JSON body on `POST\n  /api/dataset/generate`) in a profile that is open by design.",
        "`APD-ECO-011`'s remedy is a canopy design choice (an\n  Origin check on every state-changing route, or refusing `POST /api/dataset/generate` unless its\n  `Content-Type` is `application/json` — not on a parse failure, which the handler already turns into\n  `{}`) in a mode that is open by design.",
        1,
    ),
    (
        "ECO-012 park",
        "  text, which goes beyond what `APD-ECO-008`'s ruling asked for.\n",
        "  text, which goes beyond what `APD-ECO-008`'s ruling asked for.\n- `APD-ECO-012` — **filed 2026-09-24 by round 42's fix-forward; awaiting an owner ruling, do not\n  action.** The question mirrors `APD-ECO-009` / `-010`: fix canopy's middleware order, and decide\n  whether canopy becomes a site of `cors-outside-auth`. Latent until someone sets `cors_origins`.\n- `APD-DATA-057` — **filed 2026-09-24; actionable, needs no ruling.** The remedy is the lock the\n  single-dataset route already takes, and juniper-data#438 applies it (open when filed). Close it when\n  #438 has merged and its validation holds.\n",
        1,
    ),
    # ---- section 5.1 -------------------------------------------------------------------------------------
    (
        "s5.1 DATA-007 writers",
        "**Both whole-document writers are fixed, not just the one this entry names** —",
        "**Both whole-document writers are fixed, not just the one this entry names** *(two of three, it turned out: `PATCH /v1/datasets/batch-tags` rewrites the document too, and took no lock through juniper-data 0.16.0 — `APD-DATA-057`, filed 2026-09-24)* —",
        1,
    ),
    (
        "s5.1 intro",
        "The §2.3 copy-drift list is now worked through too.",
        "The §2.3 copy-drift list was worked through too, until round 42 added three canopy rows to it, all open (`APD-ECO-009`, `-010`, `-012`).",
        1,
    ),
    (
        "s5.1 ECO-008 CI caveat",
        "a missing canopy checkout FAILS rather than skips;",
        "a missing canopy checkout FAILS rather than skips when the test runs (in CI the cross-repo link check fails first, and the drift step, which has no `if: always()`, never runs — `APD-ML-008`);",
        1,
    ),
    (
        "s5.1 closing guards",
        "now holds **all six** *(seven since juniper-ml#1974)* copy-drift guards as `ENFORCED` so they cannot silently regress — every row in §2.3's table.",
        "now holds **all six** copy-drift guards as `ENFORCED` so they cannot silently lose their markers — every row in §2.3's table *(not their behaviour: a regression that keeps the marker text passes, `APD-ML-008`; and canopy's three open rows, `APD-ECO-009`, `-010` and `-012`, have no guard at canopy yet)*.",
        1,
    ),
    # ---- section 6 -----------------------------------------------------------------------------------------
    (
        "s6 freshness",
        "the primer line anchors are stable because that document is not being edited.",
        "the primer line anchors are stable only while no line of that document moves: juniper-ml#1098 inserted three at line 5758 on 2026-08-14, and every anchor past it was three short until 2026-09-24 (see §4's note); the primer's 2026-09-24 correction, juniper-ml#2075, was built to move none.",
        1,
    ),
]

REF_SUBS: list[tuple[str, str, str, int]] = [
    (
        "REFERENCE missing canopy",
        "so a missing canopy checkout FAILS the file-existence test instead of silently skipping every guard.",
        "so a missing canopy checkout FAILS the file-existence test instead of silently skipping every guard — when the test runs. In `docs-full-check.yml` the cross-repo link check runs first and fails on a missing sibling, and the drift step has no `if: always()`, so there the step is skipped instead. And the guards match marker TEXT: a regression that keeps its markers passes (`APD-ML-008` in the defect register).",
        1,
    ),
    (
        "REFERENCE only job",
        "It bites in `docs-full-check.yml`, the only job that clones the siblings.",
        "It bites in `docs-full-check.yml`, the only job that runs it with the siblings cloned (`release-train.yml` clones them too, for its own steps; `ci.yml` runs it without them, so only the always-on checks and `SharedPackageGuardTest` bite there).",
        1,
    ),
]

ECO012_ROW = (
    "| APD-ECO-012 | **canopy has `APD-CASCOR-001b`'s defect: CORS runs inside `SecurityMiddleware`, so a CORS preflight would be refused 401.** "
    "`CORSMiddleware` is added at `src/main.py:519`, before `SecurityMiddleware` at `:540`, and Starlette runs the last-added middleware outermost; "
    "`SecurityMiddleware._is_exempt` (`src/middleware.py:149-163`) checks the path only, with no `OPTIONS` bypass. A key-authenticated cross-origin call sends "
    "`X-API-Key`, which forces a preflight; the preflight carries no key, reaches auth first and is refused 401 without CORS headers, so the browser never sends "
    "the call — and an ordinary cross-origin request that auth rejects carries no CORS headers either, the second half juniper-cascor#540 fixed there. "
    "**Latent:** CORS is added only when `cors_origins` is set (`src/main.py:517`; the default is `[]`, `src/settings.py:314`), and no juniper-deploy profile "
    "sets it. Run against canopy `main`, the gate's own `cors-outside-auth` ordered-site check reports the guard absent, and present for juniper-data, "
    "juniper-cascor, and a canopy copy with the CORS block moved last. Found by the post-merge refutation lane of juniper-ml#2074 "
    "(`ml2074-round1-laneB-refute.md` finding 9), from code reading; no live request made | C | "
    "`juniper-canopy/src/main.py:517-525`, `:540`; `src/middleware.py:149-163` (`main` `" + CANOPY_MAIN + "`) | — | High |"
)


DATA057_ROW = (
    "| APD-DATA-057 | **`PATCH /v1/datasets/batch-tags` rewrites each dataset's metadata in two unlocked steps, so a plain `GET` can undo a batch "
    "tag edit, and concurrent batch edits lose tags.** `batch_update_tags` reads with `get_meta` and writes with `update_meta` in two hops, taking "
    "neither `_version_lock` nor `_meta_write_lock` — the `APD-DATA-006` defect, which juniper-data#263 fixed on the single-dataset route only. "
    "`record_access`, which every metadata read and artifact download fires, takes the lock and rewrites the whole document, so it can land between "
    "the two hops and write the old tags back. Measured on `main` `1afc3484` (the same code as the `v0.16.0` tag), LocalFS, in-process threads, 12 "
    "rounds: a `GET` undid a batch edit in 6; concurrent batch additions kept 28 of 144; and a batch write erased a conditional PATCH's acknowledged "
    "200. `APD-DATA-007`'s fix note said both whole-document writers were locked; this is a third. Found by the round-2 refutation lane of the "
    "primer's correction (`primer-correction-round2-laneB-refute.md`, HIGH-1); #428's round 3 had found the missing lock "
    "(`data428-round3-laneB-refute.md`, finding 1) but not this consequence. [juniper-data#438](https://github.com/pcalnon/juniper-data/pull/438), "
    "open when this was filed, routes batch-tags through `update_tags` | C | `api/routes/datasets.py:714-754` (`batch_update_tags`; `:737`, `:746`); "
    "`storage/base.py:375` (`update_tags`, the locked path) (`main` `1afc3484`) | — | High |"
)


def load_audit():
    spec = importlib.util.spec_from_file_location("register_primer_anchor_audit", AUDIT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def apply(text: str, subs: list[tuple[str, str, str, int]], fmt: dict) -> str:
    for label, old, new, want in subs:
        got = text.count(old)
        if got != want:
            raise SystemExit(f"FAIL {label}: expected {want} match(es), found {got}; nothing written")
        text = text.replace(old, new.format(**fmt) if "{cells}" in new else new)
        print(f"  ok  {label} (x{want})")
    return text


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    reg = REG.read_text(encoding="utf-8")
    if "| APD-ML-008 |" not in reg:
        raise SystemExit("FAIL: the register lacks juniper-ml#2074's rows; build on #2074's merged content")
    if "| APD-ECO-012 |" in reg:
        raise SystemExit("FAIL: APD-ECO-012 already filed; this fix-forward has run")

    # 1. The section-4 primer cells, on the untouched line numbers the audit reports.
    audit = load_audit()
    lines = reg.split("\n")
    rewrites, moved, bad = audit.audit(lines, PRIMER.read_text(encoding="utf-8").split("\n"), verbose=False)
    if bad:
        raise SystemExit(f"FAIL: {bad} primer anchor(s) failed the content check; nothing written")
    blank_before = 0
    for rw in rewrites:
        line = lines[rw["line"] - 1]
        parts = re.split(r"(?<!\\)\|", line)
        hits = [i for i, p in enumerate(parts) if p.strip() == rw["old"]]
        if len(hits) != 1 or rw["id"] not in parts[1]:
            raise SystemExit(f"FAIL {rw['id']}: its Primer cell {rw['old']!r} is not unique in its row; nothing written")
        parts[hits[0]] = parts[hits[0]].replace(rw["old"], rw["new"])
        lines[rw["line"] - 1] = "|".join(parts)
    primer_now = PRIMER.read_text(encoding="utf-8").split("\n")
    for rw in rewrites:
        for old_n in re.findall(r"\b\d{4,5}\b", rw["old"]):
            if int(old_n) > 5758 and old_n not in rw["new"] and primer_now[int(old_n) - 1].strip() == "":
                blank_before += 1
    print(f"  ok  primer cells: {moved} anchors in {len(rewrites)} rows shifted ({blank_before} had landed on blank lines)")
    reg = "\n".join(lines)

    # 2. Every text substitution, then the new row after APD-ML-008's.
    reg = apply(reg, SUBS, {"cells": moved, "rows": len(rewrites), "blank": blank_before})
    lines = reg.split("\n")
    at = [i for i, line in enumerate(lines) if line.startswith("| APD-ML-008 |")]
    if len(at) != 1:
        raise SystemExit("FAIL: APD-ML-008's row is not unique; nothing written")
    lines.insert(at[0] + 1, ECO012_ROW)
    lines.insert(at[0] + 2, DATA057_ROW)
    reg = "\n".join(lines)
    print("  ok  APD-ECO-012 and APD-DATA-057 rows filed after APD-ML-008's")

    ref = apply(REF.read_text(encoding="utf-8"), REF_SUBS, {})

    if args.dry_run:
        print("dry run: nothing written")
        return 0
    REG.write_text(reg, encoding="utf-8")
    REF.write_text(ref, encoding="utf-8")
    print(f"wrote {REG.relative_to(REPO)} and {REF.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
