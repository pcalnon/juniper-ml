#!/usr/bin/env python3
"""
Apply what the pre-PR validation of round 42's second fix-forward refuted, before any PR exists.

Project: juniper-ml
Sub-Project: ad-hoc tooling (defect-register maintenance)
Author: Paul Calnon
Created: 2026-09-24
Status: ad-hoc -- single-use editor; all-or-nothing, refuses to run twice
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)

util/ad-hoc/2026-09-24_register_round42_second_fixforward.py made the branch
`docs/register-round-42-second-fixforward` (commit e2f87aae). Two independent lanes validated that pushed
branch BEFORE a PR was opened, because the owner's PR sweeper merges an open PR as soon as its checks pass.
Their reports are archived verbatim in reports/2026-09-24_defect-register-round-42/ as
register-fixforward2-round1-laneA-reprobe.md and register-fixforward2-round1-laneB-refute.md. Neither found a
HIGH. Both found that the change's own new sentences carried two false claims (APD-ECO-008's filing, and
Appendix E's account of the toy's input handling) and one unit error ("four notes"). This applies every
finding that survived re-derivation against source:

- notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md: those three, the `record_access` scope in
  the two other places that still overstated it, the park block's header and its one range-only bullet,
  cascor#688's merge on APD-CASCOR-013 and that row's writers named (the omitted N1), the §4 note's mixed
  units, and the lanes' NITs;
- notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md: Appendix E's toy
  sentence made exact, the params restriction named as a divergence, the error-model claims scoped to what
  the code does, a numeric-string arm that pins "never coerced", `RecursionError` caught in `decode_cursor`,
  E.1 item 3's cost clause completed -- every edit on its own line, so nothing moves.

Each register substitution must match exactly the number of times it declares. Each primer edit names its line
and that line's exact current text; the primer must keep its line count, only the named lines may change, and
no new line may carry a character `str.splitlines()` breaks on. Nothing is written unless every check passes.

Usage: python3 util/ad-hoc/2026-09-24_register_round42_second_fixforward_corrections.py [--dry-run] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REG_REL = "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"
PRIMER_REL = "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md"
PREREQ = "a second fix-forward the last 5"  # the first editor's output must be present
DONE_MARKER = "is an eighth, and round 42 filed two more"

# (label, old, new, expected count)
REG_SUBS: list[tuple[str, str, str, int]] = [
    (
        "s2.2 the primer's length now (B N8)",
        "*(9,866 since juniper-ml#1098 inserted three; still zero on 2026-09-24)*",
        "*(9,866 since juniper-ml#1098 inserted three, and 9,982 since juniper-ml#2075 appended Appendix E; still zero on 2026-09-24)*",
        1,
    ),
    (
        "s2.3 APD-ECO-008 was filed by #2005, not round 42 (A L1, B M1)",
        "Round 42 filed three more, all in canopy: `APD-ECO-008` (closed 2026-09-24), `APD-ECO-009` and `APD-ECO-010`; `APD-ECO-012`,"
        " canopy's CORS ordering, joined the table too, with no shared implementation to copy",
        "`APD-ECO-008`, filed 2026-09-22 by juniper-ml#2005 and closed 2026-09-24, is an eighth, and round 42 filed two more, `APD-ECO-009`"
        " and `APD-ECO-010` — all three canopy's; `APD-ECO-012`, canopy's CORS ordering, joined the table too, with no shared"
        " implementation to copy",
        1,
    ),
    (
        "#2059's merge date, APD-CASCOR-005 routing bullet (A N5)",
        "that the drift gate could not express until juniper-ml#2059 (`APD-ECO-008`, closed 2026-09-24).",
        "that the drift gate could not express until juniper-ml#2059 (merged 2026-09-23; `APD-ECO-008` closed 2026-09-24).",
        1,
    ),
    (
        "s3 APD-DATA-006: record_access's real scope (A L3)",
        "`record_access` — fired on every metadata read and every artifact download — does read-modify-write",
        "`record_access` — fired on every single-dataset metadata read and every artifact download, though not by the list, filter,"
        " `/latest` or versions reads — does read-modify-write",
        1,
    ),
    (
        "s4 note: one unit (A N3, B N2)",
        "its fix-forward then corrected 43 anchors in 39 rows' `Primer` cells, 8 of which had landed on blank lines, and 7 in the prose,"
        " and a second fix-forward the last 5,",
        "its fix-forward then corrected 42 citations in 39 rows' `Primer` cells (43 numbers, a range counting both its ends), 8 of which"
        " had landed on blank lines, and 7 in the prose, and a second fix-forward the last 5 citations,",
        1,
    ),
    (
        "s4 note: lines rewritten in place since (B N1)",
        "but that check holds for every non-blank line past 5758, so it cannot tell a right anchor from a wrong one.",
        "but that check holds for every non-blank line past 5758 that no later commit rewrote in place, so it cannot tell a right anchor"
        " from a wrong one.",
        1,
    ),
    (
        "s4 note: the census in both units (A N3, B N2)",
        "lays out every citation past 5758 beside the line it lands on (82 on 2026-09-24, each read).",
        "lays out every citation past 5758 beside the line it lands on (69 on 2026-09-24, 82 numbers counting both ends of a range;"
        " each read).",
        1,
    ),
    (
        "#2059's merge date, APD-CASCOR-005 row (A N5)",
        "Widening `_FORK_REPOS` was follow-up, done by juniper-ml#2059 (`APD-ECO-008`, closed 2026-09-24).",
        "Widening `_FORK_REPOS` was follow-up, done by juniper-ml#2059 (merged 2026-09-23; `APD-ECO-008` closed 2026-09-24).",
        1,
    ),
    (
        "APD-CASCOR-013: #688 merged (A N7, B's omission caveat)",
        "*(Implemented by [juniper-cascor#678](https://github.com/pcalnon/juniper-cascor/pull/678), merged 2026-09-23, which writes it in"
        " three places now; open until the fix-forward of its post-merge validation lands, including the 2026-09-24 mixed-provenance ruling"
        " below.)*",
        "*(Implemented by [juniper-cascor#678](https://github.com/pcalnon/juniper-cascor/pull/678), merged 2026-09-23, and fixed forward by"
        " [juniper-cascor#688](https://github.com/pcalnon/juniper-cascor/pull/688), merged 2026-09-24, which applies the 2026-09-24"
        " mixed-provenance ruling below. Open until #688's own post-merge validation holds; it asked for a further fix-forward,"
        " [juniper-cascor#690](https://github.com/pcalnon/juniper-cascor/pull/690), open on 2026-09-24.)*",
        1,
    ),
    (
        "APD-CASCOR-013: the writers named (A L5, the specification's N1)",
        "`src/api/lifecycle/manager.py` (init, the single write in `_reload_dataset` — three since juniper-cascor#678 — and the read in"
        " `get_status`)",
        "`src/api/lifecycle/manager.py` (init; the writes in `start_training` :2572, `_rollback_pre_swap_state` :3924 and"
        " `_reload_dataset` :4691 at `ec8b5bdb` — `_reload_dataset`'s the only one before juniper-cascor#678, and four since #688 — and"
        " the read in `get_status`)",
        1,
    ),
    (
        "APD-ML-008: two notes, four links (A L2, B L1)",
        "since four juniper-ml notes link into cascor.",
        "since two juniper-ml notes hold four links into cascor.",
        1,
    ),
    (
        "APD-DATA-057: #438 merged (B N7)",
        "[juniper-data#438](https://github.com/pcalnon/juniper-data/pull/438), open when this was filed, routes batch-tags through"
        " `update_tags`",
        "[juniper-data#438](https://github.com/pcalnon/juniper-data/pull/438), open when this was filed and merged 2026-09-24 after the"
        " v0.16.0 cut, routes batch-tags through `update_tags`",
        1,
    ),
    (
        "APD-DATA-057: the n=1 in context (B N7)",
        "(once, n=1; a forced interleaving reproduces it, `ml2080-round1-laneA-reprobe.md` claim 17).",
        "(once, n=1, in that measurement; a re-run of the same demo erased 2 of 3, `data438-round1-laneA-reprobe.md` claim 1a, and a forced"
        " interleaving reproduces it, `ml2080-round1-laneA-reprobe.md` claim 17).",
        1,
    ),
    (
        "park header: sentences name their rows (A L4)",
        "(row-level sentences; a sentence here parks\nor unparks its row and nothing else):",
        "(sentences that name their rows, some several at\nonce; a sentence here parks or unparks the rows it names and nothing else):",
        1,
    ),
    (
        "park: APD-ML-002 to -006 by id, so a grep finds each (A L4)",
        "- `APD-ML-002` … `APD-ML-006` — **UNPARKED, and NOT thereby actionable.**",
        "- `APD-ML-002`, `APD-ML-003`, `APD-ML-004`, `APD-ML-005`, `APD-ML-006` — **UNPARKED, and NOT thereby actionable.**",
        1,
    ),
    (
        "park APD-ML-008: the silent path is a narrower question (B L6)",
        "  is the owner's release path. `-008` asks whether the drift gate should test behaviour rather than\n  text, which goes beyond what"
        " `APD-ECO-008`'s ruling asked for.",
        "  is the owner's release path. `-008` asks whether the drift gate should test behaviour rather than\n  text, which goes beyond what"
        " `APD-ECO-008`'s ruling asked for; its silent missing-juniper-data-clone path, added 2026-09-24, is a narrower question with a"
        " remedy of its own (a variable only the drift step sets), which could be ruled on separately.",
        1,
    ),
    (
        "s5.1 APD-DATA-007: record_access's real scope (A L3)",
        "— `record_access` fires on every metadata read and every artifact download and also rewrites the entire document",
        "— `record_access` fires on every single-dataset metadata read and every artifact download and also rewrites the entire document",
        1,
    ),
]

# line -> (exact current text, replacement). Every replacement is one line: nothing may move.
PRIMER_LINES: dict[int, tuple[str, str]] = {
    # A L3: record_access never fired on the list, filter, /latest or versions reads.
    4199: (
        "on every metadata read and artifact download (`routes/datasets.py:672`, `:698`). It holds `_version_lock`;",
        "on every single-dataset metadata read and artifact download (`routes/datasets.py:672`, `:698`; the list, filter, `/latest` and"
        " versions reads fire none). It holds `_version_lock`;",
    ),
    # B L4: the params restriction is a second divergence from the real service; name it where the first is named.
    5346: (
        "One deliberate divergence from the real service: this example returns **200** when a content-addressed dataset already exists,"
        " reserving **201** for genuine creation. `juniper-data` returns 201 either way (`juniper_data/api/routes/datasets.py:71`), so a"
        " client cannot tell whether it created anything.",
        "One deliberate divergence from the real service: this example returns **200** when a content-addressed dataset already exists,"
        " reserving **201** for genuine creation. `juniper-data` returns 201 either way (`juniper_data/api/routes/datasets.py:71`), so a"
        " client cannot tell whether it created anything. A second: its `params` accept JSON numbers only, never coerced, so a string, a"
        " boolean, a null or a nested value is a 422 here — including the `seed: null` that [Appendix E, E.1](#e1-artifact-validator)"
        " describes the real service reading as a request for a fresh nonce.",
    ),
    # B L3: FastAPI's own 404/405/body-parse 400 keep their shape, and n_samples is read unchecked.
    5377: (
        "* **RFC 9457 problem details** on every error path, including FastAPI's",
        "* **RFC 9457 problem details** on every error path the routes raise, and on FastAPI's",
    ),
    5378: (
        "  validation errors, which otherwise emit a differently shaped body. (An exception nothing anticipated still reaches Starlette's"
        " plain-text 500.)",
        "  validation errors, which otherwise emit a differently shaped body. Not on FastAPI's own 404, 405 or body-parse 400, which keep"
        " ``{\"detail\": ...}``, and not on an unhandled exception: ``n_samples`` is read unchecked, so a huge one is Starlette's plain-text 500.",
    ),
    5433: (
        "    Centralising the rendering is what keeps *every* error path the same shape,",
        "    Centralising the rendering is what keeps every error path it covers the same shape,",
    ),
    5434: (
        "    including the ones FastAPI generates on your behalf.",
        "    including the validation errors FastAPI generates on your behalf (not its 404, 405 or body-parse 400).",
    ),
    # A M1, B M2: the comment claimed more than the type does.
    5502: (
        "    params: dict[str, StrictInt | StrictFloat] = Field(default_factory=dict)  # JSON numbers only, never coerced: anything else is a 422,"
        " not a 500",
        "    params: dict[str, StrictInt | StrictFloat] = Field(default_factory=dict)  # JSON numbers only, never coerced: \"512\" or true is a"
        " 422, not 512 or 1",
    ),
    # B L7: a cursor nested past the recursion limit raised RecursionError, which the tuple did not catch.
    5600: (
        "    except (ValueError, KeyError, TypeError, binascii.Error) as exc:",
        "    except (ValueError, KeyError, TypeError, RecursionError, binascii.Error) as exc:  # RecursionError: a cursor nested past the limit",
    ),
    # B L2: nothing pinned "never coerced"; a lax int | float passed the whole harness.
    6117: (
        "        bad_extra = await client.post(\"/v1/datasets\", json={**SPIRAL, \"typo_field\": 1})",
        "        bad_extra, bad_str = await client.post(\"/v1/datasets\", json={**SPIRAL, \"typo_field\": 1}), await client.post(\"/v1/datasets\","
        " json={**SPIRAL, \"params\": {\"n_samples\": \"512\"}})  # \"512\" must not be coerced",
    ),
    6120: (
        "    for response in (bad_enum, bad_extra, bad_query, bad_nan):",
        "    for response in (bad_enum, bad_extra, bad_str, bad_query, bad_nan):",
    ),
    # A M1, B M2, A N1 / B N4: the toy sentence made exact, and the fourth in-place correction named.
    9880: (
        "5838, 5857 and 5945) now also check that each metadata `ETag` is the digest of the exact body sent — the POST-create 201's own body"
        " only since a second correction the same day, which also restricted a create's `params` to JSON numbers, so that NaN, Infinity or a"
        " non-integer `n_samples` is a 422 problem where it had been a plain-text 500 (lines 5400, 5498, 5502, 5631, 6119 and 6120).",
        "5838, 5857 and 5945) now also check that each metadata `ETag` is the digest of the exact body sent — the POST-create 201's own body"
        " only since a second correction the same day. That correction also limited a create's `params` to JSON numbers, never coerced (line"
        " 5346): NaN, Infinity, or an `n_samples` that `int()` rejects, is a 422 problem where it had been a plain-text 500, and any other"
        " non-number is refused where it had been accepted; `n_samples` itself stays unchecked, so a fraction is truncated and a huge value is"
        " a plain-text 500, as lines 5377-5378 now say. It also made a cursor nested past the recursion limit a 400 problem (line 5600), and"
        " marked line 4224's bold as added emphasis, a fourth line corrected in place.",
    ),
    # A N2, B L5: instability also costs spurious 412s on conditional writes.
    9943: (
        "   validator; unstable field order or float formatting only makes it change more often than the data does, which",
        "   validator; unstable field order or float formatting only makes it change when the dataset has not, which costs",
    ),
    9944: (
        "   costs revalidations but never serves stale bytes. juniper-data's metadata `ETag` and II.11's are both such hashes.",
        "   revalidations and spurious `412`s on conditional writes, but never serves stale bytes. juniper-data's metadata `ETag` and"
        " II.11's are both such hashes.",
    ),
}

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
    print(f"  ok  primer: {len(changed)} lines rewritten in place, {len(text.splitlines())} lines before and after, none moved")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()

    reg = (REPO / REG_REL).read_text(encoding="utf-8")
    if PREREQ not in reg:
        raise SystemExit("FAIL: the register lacks the second fix-forward (commit e2f87aae); build on it")
    if DONE_MARKER in reg:
        raise SystemExit("FAIL: these corrections have already been applied")

    reg = apply(reg, REG_SUBS)
    primer = edit_primer((REPO / PRIMER_REL).read_text(encoding="utf-8"))

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
