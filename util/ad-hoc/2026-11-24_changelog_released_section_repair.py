#!/usr/bin/env python3
"""
Move the seven CHANGELOG bullets that four commits misfiled: each to the release whose tag first contains it, under
the category its author filed it in. Two of them (B and D below) shipped under ``### Changed``, because the heading
that misfiled them came before their release; they return to ``### Added``.

Project: juniper-ml
Sub-Project: ad-hoc tooling (R-OBS-SC-2 follow-ups; the Overtoad's ruling of 2026-11-24 on R50's findings)
Author: Paul Calnon
Created: 2026-11-24
Version: 0.1.0
License: MIT License
Status: single-use; landed with the repair as provenance, as 288de462's was. A second run on the repaired file refuses.
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: util/ad-hoc/2026-11-24_released_section_drift.py (R50, which found them)

What it moves (all verbatim; nothing is reworded)
-------------------------------------------------
- A: four bullets the v0.9.0 cut (``abfdfecf``) moved from ``[0.8.0] ### Changed`` into ``[0.9.0] ### Changed``, back
  under a re-created ``[0.8.0] ### Changed``, between that section's second ``### Added`` and its ``### Fixed``, where
  the v0.8.0 tag shows them, in the tag's order.
- B: "Editable-install drift check now detects stale metadata", the fifth bullet the cut moved. It was filed under
  ``### Added``; ``6b99f2ab`` (ml#1112) inserted its own ``### Changed`` heading above it. It goes back to
  ``[0.8.0] ### Added``, directly after ``tests/test_open_signed_pr.py``, the bullet that preceded it in that Added
  list.
- C: ``4b13f318``'s perf-lane bullet ("nothing stops the first-pass burst"), filed under the RELEASED ``[0.8.0]``
  ``### Added`` by the first commit after the v0.8.0 tag. It first shipped in 0.9.0, so it goes to the end of
  ``[0.9.0]``'s second ``### Added`` list, the list ``86c397cc`` started, where newest-first order puts the oldest.
- D: "§5 drift-detection guard rails", filed under ``### Added``; ``3d083988`` (ml#295) inserted its own
  ``### Changed`` heading above it. It goes back to the end of ``[0.5.0]``'s first ``### Added`` list, after the
  ``[all]`` bullet, which is where ml#295's own Added bullets ended.

Checks
------
Every block and anchor is matched by exact text, once. The result must be a permutation of the original plus exactly
one new ``### Changed`` line and one blank line; every block must sit under its target version and category; and the
file outside the moved blocks must be unchanged line for line.

    python3 -I 2026-11-24_changelog_released_section_repair.py CHANGELOG.md            # check only
    python3 -I 2026-11-24_changelog_released_section_repair.py CHANGELOG.md --write    # write in place

Exit status: 0 ok (written with --write); 1 a check failed (nothing written).
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

EM = "—"
SECT = "§"

# (name, first line, last line, expected line count)
BLOCKS = {
    "A": ("- **All eight decision-11 floors raised " + EM + " the meta-package now resolves the released contract, not the", '  than a "retire when" condition already met.', 45),
    "B": ("- **Editable-install drift check now detects stale metadata**, a second axis orthogonal to", "    synthetic conda dir + ecosystem root, no real pip).", 27),
    "C": ("- **Perf lane " + EM + ' nothing "stops" the first-pass burst; the training thread is re-pinned during', "  `notes/JUNIPER_2026-09-10_JUNIPER-ECOSYSTEM_PERF-LANE-PF8-OCCUPANCY-PROBE.md` (" + SECT + "4.2).", 33),
    "D": ("- **" + SECT + "5 drift-detection guard rails** for the `juniper-doc-tools` PyPI", "      week (default 5 of 6 = catastrophic juniper-doc-tools regression).", 24),
}
# Where each block is before, and where it must be after: (version heading prefix, category heading)
FROM = {"A": ("## [0.9.0]", "### Changed"), "B": ("## [0.9.0]", "### Changed"), "C": ("## [0.8.0]", "### Added"), "D": ("## [0.5.0]", "### Changed")}
TO = {"A": ("## [0.8.0]", "### Changed"), "B": ("## [0.8.0]", "### Added"), "C": ("## [0.9.0]", "### Added"), "D": ("## [0.5.0]", "### Added")}

D4_LAST = "  the probe that settles it, and it reads **structural** outcomes, so it does not need a quiet host."
OPEN_SIGNED_PR_TEST = [
    "- `tests/test_open_signed_pr.py` " + EM + " hermetic suite for the above (`gh` is a PATH stub recording argv",
    "  and replaying canned stdout; no network, repo, or `git`). `util/` sits outside every pre-commit",
    "  Python hook's scope, so this is the gate. Wired into `ci.yml`.",
]
BOT_GROUP_LAST = "  squash and the armed-but-`BEHIND` split that exposed the config deadlock above."
RUNNER_FIXED = "- **Runner-commit automations no longer produce unsigned, unmergeable branches** (juniper-ml#1099)."
ALL_EXTRA_LAST = "  package: 3 servers, 2 clients, 1 worker, and 3 tools."
NEXT_AFTER_C = "- **Perf lane " + EM + " the initial output pass's ~11-core burst is libgomp under torch, not NumPy's"


class RepairError(Exception):
    pass


def check(cond: bool, msg: str) -> None:
    if not cond:
        raise RepairError(msg)


def only_index(lines: list[str], text: str, start: int = 0, end: int | None = None) -> int:
    end = len(lines) if end is None else end
    hits = [i for i in range(start, end) if lines[i] == text]
    check(len(hits) == 1, f"expected exactly one line {text[:70]!r} in [{start},{end}), found {len(hits)}")
    return hits[0]


def only_seq(lines: list[str], seq: list[str]) -> int:
    hits = [i for i in range(len(lines) - len(seq) + 1) if lines[i : i + len(seq)] == seq]
    check(len(hits) == 1, f"expected the {len(seq)}-line sequence starting {seq[0][:60]!r} once, found {len(hits)}")
    return hits[0]


def location(lines: list[str], index: int) -> tuple[str, str]:
    version, category = "(no version)", "(no category)"
    for line in lines[: index + 1]:
        if line.startswith("## ["):
            version, category = line, "(no category)"
        elif line.startswith("### "):
            category = line.strip()
    return version, category


def extract(lines: list[str], name: str) -> tuple[int, int]:
    first, last, count = BLOCKS[name]
    start = only_index(lines, first)
    stop = only_index(lines, last) + 1
    check(stop - start == count, f"block {name}: {stop - start} lines, expected {count}")
    return start, stop


def repair(lines: list[str]) -> tuple[list[str], dict[str, list[str]]]:
    a0, a1 = extract(lines, "A")
    b0, b1 = extract(lines, "B")
    c0, c1 = extract(lines, "C")
    d0, d1 = extract(lines, "D")
    for name, (s, _e) in {"A": (a0, a1), "B": (b0, b1), "C": (c0, c1), "D": (d0, d1)}.items():
        v, c = location(lines, s)
        check(v.startswith(FROM[name][0]) and c == FROM[name][1], f"block {name} is under {v} / {c}, expected {FROM[name]}")
    check(lines[a1] == "" and b0 == a1 + 1 and lines[b1] == "", "A and B are not adjacent, each followed by one blank line")
    check(lines[c0 - 1] == "" and lines[c1] == NEXT_AFTER_C, "C is not the first bullet of [0.8.0]'s first Added list")
    check(lines[d1] == "" and lines[d1 + 1] == "### Removed", "D is not the last bullet before [0.5.0]'s ### Removed")

    p_c = only_index(lines, "## [0.8.0] - 2026-09-11")
    check(lines[p_c - 1] == "" and lines[p_c - 2] == D4_LAST, "the end of [0.9.0] is not D4's bullet then a blank line")
    v080, v071 = p_c, only_index(lines, "## [0.7.1] - 2026-08-09")
    p_b = only_seq(lines, OPEN_SIGNED_PR_TEST) + len(OPEN_SIGNED_PR_TEST)
    check(v080 < p_b < v071 and lines[p_b] == "" and lines[p_b + 1] == "### Added", "tests/test_open_signed_pr.py is not the end of [0.8.0]'s first Added list")
    p_a = only_index(lines, "### Fixed", v080, v071)
    check(lines[p_a - 1] == "" and lines[p_a - 2] == BOT_GROUP_LAST and lines[p_a + 2] == RUNNER_FIXED, "[0.8.0]'s ### Fixed is not where the v0.8.0 tag puts it")
    v050, v041 = only_index(lines, "## [0.5.0] - 2026-05-21"), only_index(lines, "## [0.4.1] - 2026-04-28")
    p_d = only_index(lines, "### Changed", v050, v041)
    check(lines[p_d - 1] == "" and lines[p_d - 2] == ALL_EXTRA_LAST, "[0.5.0]'s ### Changed does not follow the [all] bullet")
    check(a0 < b1 < p_c < c0 < c1 < p_b < p_a < p_d < d0 < d1, "the anchors are not in the expected order")

    A, B, C, D = lines[a0:a1], lines[b0:b1], lines[c0:c1], lines[d0:d1]
    return (
        lines[:a0]
        + lines[b1 + 1 : p_c - 1]
        + C
        + lines[p_c - 1 : c0]
        + lines[c1:p_b]
        + [""]
        + B
        + lines[p_b:p_a]
        + ["### Changed", ""]
        + A
        + [""]
        + lines[p_a:p_d]
        + D
        + [""]
        + lines[p_d:d0]
        + lines[d1 + 1 :]
    ), {"A": A, "B": B, "C": C, "D": D}


def verify(before: list[str], after: list[str], blocks: dict[str, list[str]]) -> list[str]:
    report = []
    check(Counter(after) == Counter(before) + Counter({"### Changed": 1, "": 1}), "lines are not conserved (+1 '### Changed', +1 blank)")
    report.append(f"lines conserved: {len(before)} -> {len(after)} (+1 '### Changed', +1 blank)")
    for name, block in blocks.items():
        start = only_seq(after, block)
        v, c = location(after, start)
        check(v.startswith(TO[name][0]) and c == TO[name][1], f"block {name} ended under {v} / {c}, expected {TO[name]}")
        report.append(f"block {name}: {len(block)} lines, byte-identical, now at line {start + 1} under {v} / {c}")
    # Excise the moved blocks (and the heading this adds) from both sides: what remains must be identical.
    skeleton_before, skeleton_after = list(before), list(after)
    for block in blocks.values():
        i = only_seq(skeleton_before, block)
        del skeleton_before[i : i + len(block)]
        j = only_seq(skeleton_after, block)
        del skeleton_after[j : j + len(block)]
    # The moved blocks leave or take blank separators; compare with blank runs collapsed.
    def collapse(seq: list[str]) -> list[str]:
        out: list[str] = []
        for line in seq:
            if line == "" and out and out[-1] == "":
                continue
            out.append(line)
        return out

    sb, sa = collapse(skeleton_before), collapse(skeleton_after)
    v080, v071 = sa.index("## [0.8.0] - 2026-09-11"), sa.index("## [0.7.1] - 2026-08-09")
    new_heading = [i for i in range(v080, v071) if sa[i] == "### Changed"]
    check(len(new_heading) == 1, f"[0.8.0] holds {len(new_heading)} '### Changed' headings after the repair, expected 1")
    del sa[new_heading[0]]
    check(collapse(sa) == sb, "outside the moved blocks, the file is not identical apart from the new heading")
    report.append("outside the moved blocks: identical apart from the new [0.8.0] '### Changed' heading")
    return report


def main(argv: list[str]) -> int:
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 1
    path = Path(argv[0])
    write = "--write" in argv[1:]
    text = path.read_text(encoding="utf-8")
    before = text.split("\n")
    try:
        after, blocks = repair(before)
        for line in verify(before, after, blocks):
            print(line)
    except RepairError as exc:
        print(f"REFUSED: {exc}")
        return 1
    if write:
        path.write_text("\n".join(after), encoding="utf-8")
        print(f"written: {path}")
    else:
        print("check only (pass --write to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
