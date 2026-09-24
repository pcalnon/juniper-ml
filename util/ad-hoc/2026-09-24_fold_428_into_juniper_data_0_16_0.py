#!/usr/bin/env python3
"""Fold juniper-data#428, #431 and #434 into the single [0.16.0] section they will ship in.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release tooling
Author:      Paul Calnon
Created:     2026-09-24
Version:     0.1.0
License:     MIT License
Status:      single-use (juniper-data 0.16.0 release, post-bump merges)

Why this exists
---------------
The 0.16.0 version bump (juniper-data#433, ``7125e16``) moved ``[Unreleased]`` into
``## [0.16.0] - 2026-09-23``. Three PRs merged after it:

* #428 (ETags, conditional requests, the counters leave the representation). Its branch
  CHANGELOG was rebuilt on the release cut BEFORE update-branch, and the update-branch 3-way
  merge duplicated the release heading with no conflict. ``main`` therefore carries
  ``## [0.16.0] - 2026-09-23`` TWICE, with #428's ``### Added`` / ``### Changed`` under the
  first copy;
* #431 (notify-consumers waits for the consumer's run) and #434 (arc_agi review follow-ups),
  both correctly filed under ``[Unreleased]``.

**The Release creates the tag at the current branch head.** ``util/release_train/ceremony.py``
runs ``gh release create <tag>`` with no ``--target``, so ``v0.16.0`` tags a tree that already
contains all three PRs, whatever the CHANGELOG says. The notes are rendered from the FIRST
``## [0.16.0]`` match (``changelog_version_section``), which today holds #428's entries ALONE:
the published notes would drop #421, #422, #426, #427 and #429 and could not be re-cut. The
owner ruled 2026-09-24: fold #428 into 0.16.0 (and with it #431 and #434), leaving an empty
``[Unreleased]``. This is the 2026-09-22 0.15.0 precedent
(``2026-09-22_fold_pr418_into_juniper_data_0_15_0.py``) with one deliberate difference: that
fold left a duplicate ``### Changed`` heading, which #428 later repaired as a defect (a
duplicate category files later bullets under the wrong heading). This fold MERGES categories,
in Keep-a-Changelog order, so the section has each category heading exactly once.

Two entries are reworded, and only where they would otherwise be false once they sit inside
0.16.0: #434 and #431 describe "0.16.0's" behaviour, meaning a state that existed only on
``main`` between merges and never in any release (round-2 finding 12 on #428 is this class).
Every other line is moved verbatim; ``--check`` proves it by bullet census.

Writes to ``--out``; never touches a checkout. Refuses unless the input has exactly the
structure described above.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

HEADING = "## [0.16.0] - 2026-09-23"
UNRELEASED = "## [Unreleased]"
ORDER = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]

# (old, new): each OLD must occur exactly once in the input.
REWORDS = [
    (
        "- **Review follow-ups to 0.16.0's arc_agi fix** (#434, for #429; #430's entry is under\n  `[0.16.0]`):",
        "- **Review follow-ups to the arc_agi fix above** (#434, for #429; #430 is that entry):",
    ),
    (
        "  - **The cached store's population-failure log is bounded.** 0.16.0 turned a silently\n    swallowed cache population into a `WARNING` with its traceback, and a stored arc_agi\n    artifact that can never be cached then logged one on **every** read (100 reads gave 100\n    records).",
        "  - **The cached store's population-failure log is bounded.** #430 turned a silently\n    swallowed cache population into a `WARNING` with its traceback, and as first merged a\n    stored arc_agi artifact that can never be cached then logged one on **every** read (100\n    reads gave 100 records).",
    ),
    (
        "second residual gap on juniper-recurrence#178). 0.16.0's `notify-consumers.yml` took the\n  dispatch API's `204` as delivery,",
        "second residual gap on juniper-recurrence#178). `notify-consumers.yml` as #426 first merged\n  it took the dispatch API's `204` as delivery,",
    ),
]


def split_categories(block: str) -> "list[tuple[str, str]]":
    """Split a version-section body into [(category, body)] in file order."""
    parts = re.split(r"(?m)^### (.+)$", block)
    if parts[0].strip():
        raise SystemExit(f"ERROR: text before the first ### heading: {parts[0][:120]!r}")
    out = []
    for i in range(1, len(parts), 2):
        out.append((parts[i].strip(), parts[i + 1].strip("\n")))
    return out


def bullets(body: str) -> "list[str]":
    """Top-level bullets (a line starting '- ' at column 0 opens one)."""
    found, cur = [], []
    for line in body.split("\n"):
        if line.startswith("- "):
            if cur:
                found.append("\n".join(cur).rstrip())
            cur = [line]
        elif cur:
            cur.append(line)
    if cur:
        found.append("\n".join(cur).rstrip())
    return found


def fold(text: str) -> str:
    for old, _new in REWORDS:
        n = text.count(old)
        if n != 1:
            raise SystemExit(f"ERROR: reword anchor occurs {n} times (need 1): {old[:80]!r}")
    if text.count(UNRELEASED + "\n") != 1:
        raise SystemExit("ERROR: expected exactly one '## [Unreleased]'")
    if text.count(HEADING + "\n") != 2:
        raise SystemExit(f"ERROR: expected exactly two {HEADING!r} (found {text.count(HEADING + chr(10))}); already folded?")
    for old, new in REWORDS:
        text = text.replace(old, new)

    u0 = text.index(UNRELEASED + "\n")
    h1 = text.index(HEADING + "\n")
    h2 = text.index(HEADING + "\n", h1 + 1)
    m = re.compile(r"(?m)^## \[").search(text, h2 + len(HEADING))
    if not m:
        raise SystemExit("ERROR: no version heading after the second 0.16.0")
    end = m.start()

    unreleased = text[u0 + len(UNRELEASED) + 1 : h1]
    first = text[h1 + len(HEADING) + 1 : h2]
    second = text[h2 + len(HEADING) + 1 : end]

    # Merge order inside a category: the released proposal's own entries first (#433's
    # section), then #428's, then [Unreleased]'s (#434, #431) -- i.e. merge order.
    merged: "dict[str, list[str]]" = {}
    for block in (second, first, unreleased):
        for cat, body in split_categories(block):
            if cat not in ORDER:
                raise SystemExit(f"ERROR: unknown category {cat!r}")
            merged.setdefault(cat, []).append(body)

    out = [HEADING, ""]
    for cat in ORDER:
        if cat not in merged:
            continue
        out.append(f"### {cat}")
        out.append("")
        out.append("\n\n".join(b.strip("\n") for b in merged[cat]))
        out.append("")
    section = "\n".join(out) + "\n"
    return text[: u0 + len(UNRELEASED) + 1] + "\n" + section + text[end:]


def census(text: str, headings: "list[str]") -> "dict[str, list[str]]":
    """category -> bullets, over the named version headings (first match of each, plus Unreleased)."""
    res: "dict[str, list[str]]" = {}
    idx = []
    for h in headings:
        start = 0
        while True:
            i = text.find(h + "\n", start)
            if i < 0:
                break
            idx.append(i)
            start = i + 1
    for i in sorted(set(idx)):
        head_end = text.index("\n", i) + 1
        m = re.compile(r"(?m)^## \[").search(text, head_end)
        block = text[head_end : m.start() if m else len(text)]
        for cat, body in split_categories(block) if block.strip() else []:
            res.setdefault(cat, []).extend(bullets(body))
    return res


def load_ceremony(repo_root: Path):
    # ceremony.py imports its siblings (detect, notes_render) as top-level modules.
    sys.path.insert(0, str(repo_root / "util/release_train"))
    spec = importlib.util.spec_from_file_location("ceremony", repo_root / "util/release_train/ceremony.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["ceremony"] = mod
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--changelog", required=True, help="juniper-data CHANGELOG.md as on main (input, read only)")
    ap.add_argument("--out", required=True, help="where to write the folded CHANGELOG.md")
    args = ap.parse_args()

    src = Path(args.changelog).read_text(encoding="utf-8")
    folded = fold(src)

    # 1. Bullet census: every bullet of the three source sections is in the folded 0.16.0,
    #    verbatim except the rewords, and nothing else changed anywhere in the file.
    before = census(src, [UNRELEASED, HEADING])
    after = census(folded, [UNRELEASED, HEADING])
    rew = dict(REWORDS)

    def norm(b: str) -> str:
        for old, new in rew.items():
            b = b.replace(old, new)
        return b

    ok = True
    for cat in sorted(set(before) | set(after)):
        want = sorted(norm(b) for b in before.get(cat, []))
        got = sorted(after.get(cat, []))
        status = "OK" if want == got else "MISMATCH"
        ok &= want == got
        print(f"  {cat:8} before={len(before.get(cat, [])):2} after={len(got):2} {status}")
    tail_src = src[src.index("## [0.15.0]") :]
    tail_out = folded[folded.index("## [0.15.0]") :]
    print(f"  everything from [0.15.0] down: {'byte-identical' if tail_src == tail_out else 'CHANGED'}")
    ok &= tail_src == tail_out
    print(f"  '{HEADING}' occurrences: {folded.count(HEADING)}")
    ok &= folded.count(HEADING) == 1

    # 2. What the release ceremony would publish, read by the ceremony's own parsers.
    repo_root = Path(__file__).resolve().parents[2]
    cer = load_ceremony(repo_root)
    import notes_render  # noqa: E402  (util/release_train is on sys.path now)

    for label, text in (("main today", src), ("folded", folded)):
        sec = cer.changelog_version_section(text, "0.16.0")
        unrel = notes_render.parse_unreleased(text)
        print(f"  ceremony 0.16.0 notes, {label}: " + ", ".join(f"{k}={len(v)}" for k, v in sec.items()) + f" | [Unreleased]: " + (", ".join(f"{k}={len(v)}" for k, v in unrel.items()) or "empty"))
    sec = cer.changelog_version_section(folded, "0.16.0")
    expect = {cat: len(v) for cat, v in after.items()}
    got = {k: len(v) for k, v in sec.items()}
    print(f"  ceremony renders every folded bullet: {got == expect} ({got} vs census {expect})")
    ok &= got == expect
    ok &= not notes_render.parse_unreleased(folded)

    if not ok:
        print("REFUSED: census or ceremony check failed; nothing written", file=sys.stderr)
        return 1
    Path(args.out).write_text(folded, encoding="utf-8")
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
