#!/usr/bin/env python3
"""
Raise juniper-ml's ``[tools]`` floors to juniper-observability>=0.4.2 and juniper-service-core>=0.7.2,<0.8.0, at every site.

Project: juniper-ml
Sub-Project: ad-hoc tooling (R-OBS-SC-2 follow-ups)
Author: Paul Calnon
Created: 2026-11-12
Status: ad-hoc -- one-off writer for the [tools] floor PR (owner ruling 2026-11-09, "Floor PR, then 0.11.5")
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2314 (0.11.1's floor PR, the template for the site list);
         notes/releases/RELEASE_NOTES_juniper-observability_v0.4.2.md;
         notes/releases/RELEASE_NOTES_juniper-service-core_v0.7.2.md;
         notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md (R-OBS-SC-2's follow-ups)

Why a script
------------
The floors are stated in nine files, and ``util/open_signed_pr.py`` uploads whole files. If ``main`` moves under one
of them between the edit and the upload, a hand edit has to be redone by hand; a scripted one is re-run on main's
copy. Each edit is an exact string asserted to occur a stated number of times, so a site that moved or was already
edited stops the run instead of being skipped or doubled.

What it edits
-------------
* ``pyproject.toml`` -- ``[tools]``: the two floors.
* ``tests/test_pyproject_extras.py`` -- ``EXPECTED_EXTRAS["tools"]``.
* ``README.md`` -- the "Ecosystem Compatibility" table (two rows) and the extras table.
* ``AGENTS.md`` -- the extras table, and ``**Last Updated**`` (the ``Verify AGENTS.md Last Updated`` check).
* ``docs/QUICK_START.md`` -- the extras table.
* ``docs/REFERENCE.md`` -- the Extras Reference rows, the two sub-packages' **Current Version** cells (0.4.1 and
  0.7.1, stale since the 2026-11-09 publish), the observability table's ``sentry`` extra row (0.4.2 requires
  ``sentry-sdk[fastapi]>=2.35.0``), service-core's **Meta pin** row, and the compatibility matrix: the
  ``0.11.x`` row's ``juniper-observability`` cell, with two clauses in the paragraph above it that say what the
  published 0.11.4 declares (so the paragraph stays true while the row tracks ``pyproject.toml``).
* ``docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`` -- the "Current truth" statement of the service-core pin, which still
  read ``>=0.2.0,<0.8.0`` (0.11.1's floor PR missed it; no test reads the file).
* ``juniper-service-core/README.md`` -- the pin advice.
* ``CHANGELOG.md`` -- ``[Unreleased]`` -> ``### Security``.

What it leaves, on purpose
--------------------------
* ``docs/REFERENCE.md``'s Package Overview **Version** cell and the sentence "``juniper-ml`` 0.11.4 declares the
  following pins" name the published release and move at the 0.11.5 cut. 0.11.1's floor PR (juniper-ml#2314) left
  the whole matrix for its cut (``util/ad-hoc/2026-10-25_juniper_ml_0_11_1_cut_cochanges.py``); this one moves the
  cell because juniper-ml#2507's test, on its way to ``main``, pins the current series row to ``pyproject.toml``.
* **To undo at the next cut, by hand**: the two clauses this script adds to that paragraph ("except the
  ``juniper-observability`` cell ..." and "``main`` raises it to ..."). Nothing rewrites the two clauses: on
  ``main`` the release train edits neither the sentence nor the row, and juniper-ml#2507's carrier is to extend it
  to four sites only (the Version cell, that sentence, the current series row and the recurrence "sets them to"
  clause), so the clauses would survive a cut as stale text and no test would notice. A 0.11.x cut deletes them. A
  cut that is not a 0.11.x (the detector reads ``[Unreleased]`` as a minor) must ALSO put the ``0.11.x`` cell back
  to ``>=0.4.1``, because the row would then describe the last published 0.11 release.
* ``juniper-observability/README.md`` already advises ``>=0.4.2``.

Usage
-----
    python3 util/ad-hoc/2026-11-12_tools_floors_observability_0_4_2_service_core_0_7_2.py [--root DIR]
    python3 util/ad-hoc/2026-11-12_tools_floors_observability_0_4_2_service_core_0_7_2.py --check [--root DIR]

Without ``--check`` it applies every edit (all or none: it validates every site before it writes anything).
``--check`` writes nothing and exits 0 only when every edit is already applied.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

#: The UTC date the PR opens. ``Verify AGENTS.md Last Updated`` FAILS a stamp later than the run's UTC date; otherwise
#: it passes when the stamp is that date or the diff adds the stamp line. ``main`` already carried 2026-11-12, so a PR
#: opened on the 13th moves it, and must not be opened or pushed to before 00:00Z that day.
LAST_UPDATED = "2026-11-13"

_PAIR_OLD = "`juniper-observability>=0.4.1`, `juniper-service-core>=0.7.1,<0.8.0`"
_PAIR_NEW = "`juniper-observability>=0.4.2`, `juniper-service-core>=0.7.2,<0.8.0`"

#: (file, old, new): ``old`` must occur exactly once before the edit; ``new`` exactly once after it.
EDITS: list[tuple[str, str, str]] = [
    ("pyproject.toml", '    "juniper-observability>=0.4.1",\n', '    "juniper-observability>=0.4.2",\n'),
    ("pyproject.toml", '    "juniper-service-core>=0.7.1,<0.8.0",\n', '    "juniper-service-core>=0.7.2,<0.8.0",\n'),
    ("tests/test_pyproject_extras.py", '        "juniper-observability>=0.4.1",\n', '        "juniper-observability>=0.4.2",\n'),
    ("tests/test_pyproject_extras.py", '        "juniper-service-core>=0.7.1,<0.8.0",\n', '        "juniper-service-core>=0.7.2,<0.8.0",\n'),
    ("README.md", "| `juniper-observability`                       | `>=0.4.1`        |\n", "| `juniper-observability`                       | `>=0.4.2`        |\n"),
    ("README.md", "| `juniper-service-core`                        | `>=0.7.1,<0.8.0` |\n", "| `juniper-service-core`                        | `>=0.7.2,<0.8.0` |\n"),
    ("README.md", _PAIR_OLD, _PAIR_NEW),
    ("AGENTS.md", _PAIR_OLD, _PAIR_NEW),
    ("docs/QUICK_START.md", _PAIR_OLD, _PAIR_NEW),
    (
        "docs/REFERENCE.md",
        "|             | `juniper-observability`                                                                  | `>=0.4.1`         |\n",
        "|             | `juniper-observability`                                                                  | `>=0.4.2`         |\n",
    ),
    (
        "docs/REFERENCE.md",
        "|             | `juniper-service-core`                                                                   | `>=0.7.1,<0.8.0`  |\n",
        "|             | `juniper-service-core`                                                                   | `>=0.7.2,<0.8.0`  |\n",
    ),
    (
        "docs/REFERENCE.md",
        "| **Current Version**   | `0.4.1`                                                                    |\n",
        "| **Current Version**   | `0.4.2`                                                                    |\n",
    ),
    (
        "docs/REFERENCE.md",
        "| **Current Version**   | `0.7.1`                                                                  |\n",
        "| **Current Version**   | `0.7.2`                                                                  |\n",
    ),
    (
        "docs/REFERENCE.md",
        "| **Meta pin**          | `juniper-service-core>=0.7.1,<0.8.0` under `[tools]` / `[all]`            |\n",
        "| **Meta pin**          | `juniper-service-core>=0.7.2,<0.8.0` under `[tools]` / `[all]`            |\n",
    ),
    # The compatibility matrix: the current series row tracks pyproject (juniper-ml#2507's test, on its way to main,
    # pins every cell of it), so the cell moves here and the paragraph above says what the PUBLISHED 0.11.4 declares.
    (
        "docs/REFERENCE.md",
        "| 0.11.x     | >=0.17.1     | >=0.12.0       | >=0.9.0        | >=0.5.0             | >=0.8.0               | >=0.4.0               | >=0.1.0          | >=0.1.0,<0.2.0     | >=0.4.1               |\n",
        "| 0.11.x     | >=0.17.1     | >=0.12.0       | >=0.9.0        | >=0.5.0             | >=0.8.0               | >=0.4.0               | >=0.1.0          | >=0.1.0,<0.2.0     | >=0.4.2               |\n",
    ),
    (
        "docs/REFERENCE.md",
        "The `0.11.x` row is 0.11.4's, and its floors are 0.11.2's. ",
        "The `0.11.x` row is 0.11.4's, and its floors are 0.11.2's, except the `juniper-observability` cell: it holds `main`'s floor, `>=0.4.2` (unreleased; first in juniper-ml 0.11.5), where the published 0.11.4 declares `>=0.4.1`. ",
    ),
    (
        "docs/REFERENCE.md",
        "from `>=0.2.0,<0.8.0` to `>=0.7.1,<0.8.0`. The three `recurrence` pins have no columns here.",
        "from `>=0.2.0,<0.8.0` to `>=0.7.1,<0.8.0`; `main` raises it to `>=0.7.2,<0.8.0` (unreleased; first in juniper-ml 0.11.5). The three `recurrence` pins have no columns here.",
    ),
    # juniper-observability 0.4.2 raised its own ``sentry`` extra to sentry-sdk[fastapi]>=2.35.0 (``enable_logs``
    # needs it). The row sits ten lines under the Current Version cell this script moves to 0.4.2. One character
    # longer, so the five-line table is rewritten a column wider.
    (
        "docs/REFERENCE.md",
        "| Extra        | Additional packages          |\n"
        "|--------------|------------------------------|\n"
        "| `prometheus` | `prometheus-client>=0.20.0`  |\n"
        "| `sentry`     | `sentry-sdk[fastapi]>=2.0.0` |\n"
        "| `all`        | Both optional groups         |\n",
        "| Extra        | Additional packages           |\n"
        "|--------------|-------------------------------|\n"
        "| `prometheus` | `prometheus-client>=0.20.0`   |\n"
        "| `sentry`     | `sentry-sdk[fastapi]>=2.35.0` |\n"
        "| `all`        | Both optional groups          |\n",
    ),
    # A live statement of the service-core pin that 0.11.1's floor PR (juniper-ml#2314) missed: it still named the
    # floor of two releases ago. No test reads this file.
    (
        "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
        "Current truth: `juniper-model-core>=0.1.0,<0.4.0`, `juniper-service-core>=0.2.0,<0.8.0`.",
        "Current truth: `juniper-model-core>=0.1.0,<0.4.0`, `juniper-service-core>=0.7.2,<0.8.0`.",
    ),
    (
        "juniper-service-core/README.md",
        "[`CHANGELOG.md`](./CHANGELOG.md) for history. Pin with `juniper-service-core>=0.7.1,<0.8.0` —\n"
        "the range the `juniper-ml` meta-package uses for its `tools` / `all` extras. 0.7.1 is the security\n"
        "patch: a non-ASCII `X-API-Key` is a 401, not a 500, and `FailedAuthThrottle.check()` is bounded\n"
        "(it does not insert). The 10,000-entry cap, which drops the oldest live source IPs, is a separate\n"
        "bound: [REFERENCE](../docs/REFERENCE.md#the-failed-auth-table-drops-the-oldest-source-ips).\n",
        "[`CHANGELOG.md`](./CHANGELOG.md) for history. Pin with `juniper-service-core>=0.7.2,<0.8.0` —\n"
        "the range the `juniper-ml` meta-package uses for its `tools` / `all` extras. 0.7.2 rounds\n"
        "`FailedAuthThrottle`'s `Retry-After` up instead of truncating it. 0.7.1 is the security patch: a\n"
        "non-ASCII `X-API-Key` is a 401, not a 500, and `FailedAuthThrottle.check()` is bounded (it does\n"
        "not insert). The 10,000-entry cap, which drops the oldest live source IPs, is a separate bound:\n"
        "[REFERENCE](../docs/REFERENCE.md#the-failed-auth-table-drops-the-oldest-source-ips).\n",
    ),
]

CHANGELOG_ANCHOR = "## [Unreleased]\n\n"
CHANGELOG_BLOCK = """### Security

- **`[tools]` floors `juniper-observability>=0.4.2` and `juniper-service-core>=0.7.2,<0.8.0` (owner ruling
  2026-11-09).** They were `>=0.4.1` and `>=0.7.1,<0.8.0`. By default pip upgrades a dependency only when the
  installed one no longer satisfies its range, so `pip install -U juniper-ml[tools]` left an environment that held
  0.4.1 and 0.7.1 on them.
  - **juniper-observability 0.4.2** is the security patch in which `configure_sentry` scrubs Sentry transactions as
    well as error events, redacts the request's parsed cookies and filters four more credential headers
    (`notes/releases/RELEASE_NOTES_juniper-observability_v0.4.2.md`).
  - **juniper-service-core 0.7.2**'s one module change rounds `FailedAuthThrottle`'s `Retry-After` up instead of
    truncating it (`notes/releases/RELEASE_NOTES_juniper-service-core_v0.7.2.md`).
  - The extras tables in `README.md` (both), `AGENTS.md`, `docs/QUICK_START.md` and `docs/REFERENCE.md` move with
    the floors, as do `docs/REFERENCE.md`'s two **Current Version** cells (which still read 0.4.1 and 0.7.1), its
    observability `sentry` extra row (0.4.2 requires `sentry-sdk[fastapi]>=2.35.0`, and the row said `>=2.0.0`), its
    service-core **Meta pin** row and `juniper-service-core/README.md`'s pin advice. The compatibility matrix's
    `0.11.x` row moves its `juniper-observability` cell with them, and the paragraph above it says that the published
    0.11.4 declares `>=0.4.1`; the sentence naming the release moves at the 0.11.5 cut.
    `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`'s "Current truth" for the service-core pin moves too: it still read
    `>=0.2.0,<0.8.0`, the floor before 0.11.1's.
  - The floors reach `pip` users with juniper-ml 0.11.5. The consumers' own floors (juniper-data, juniper-cascor,
    juniper-canopy and juniper-recurrence) move in each one's next release PR, by the same day's ruling; their locks
    already pin both releases.

"""

_LAST_UPDATED = re.compile(r"^\*\*Last Updated\*\*: (\d{4}-\d{2}-\d{2})$", re.MULTILINE)


def plan(root: Path) -> tuple[dict[str, str], list[str], int, int]:
    """(new text per file, problems, edits to apply, edits already applied)."""
    texts: dict[str, str] = dict()
    problems: list[str] = []
    todo = done = 0

    def load(name: str) -> str:
        if name not in texts:
            texts[name] = (root / name).read_text(encoding="utf-8")
        return texts[name]

    for name, old, new in EDITS:
        text = load(name)
        olds, news = text.count(old), text.count(new)
        if olds == 1 and news == 0:
            texts[name] = text.replace(old, new)
            todo += 1
        elif olds == 0 and news == 1:
            done += 1
        else:
            problems.append(f"{name}: expected the old text once and the new text never (or the reverse); found old x{olds}, new x{news}: {old.strip()[:90]!r}")

    agents = load("AGENTS.md")
    stamps = _LAST_UPDATED.findall(agents)
    if len(stamps) != 1:
        problems.append(f"AGENTS.md: expected one **Last Updated** line, found {len(stamps)}")
    elif stamps[0] >= LAST_UPDATED:
        # Equal, or main already carries a LATER date (ISO dates compare as text): never move the stamp backwards.
        done += 1
    else:
        texts["AGENTS.md"] = _LAST_UPDATED.sub(f"**Last Updated**: {LAST_UPDATED}", agents)
        todo += 1

    changelog = load("CHANGELOG.md")
    if CHANGELOG_BLOCK in changelog:
        done += 1
    elif changelog.count(CHANGELOG_ANCHOR) != 1:
        problems.append(f"CHANGELOG.md: expected one '## [Unreleased]' anchor, found {changelog.count(CHANGELOG_ANCHOR)}")
    else:
        head, _, tail = changelog.partition(CHANGELOG_ANCHOR)
        unreleased = tail.split("\n## [", 1)[0]
        if re.search(r"^### Security$", unreleased, flags=re.MULTILINE):
            problems.append("CHANGELOG.md: [Unreleased] already has a '### Security' section; merge the entry into it by hand")
        else:
            texts["CHANGELOG.md"] = head + CHANGELOG_ANCHOR + CHANGELOG_BLOCK + tail
            todo += 1
    return texts, problems, todo, done


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", default=".", help="the juniper-ml checkout to edit (default: the current directory)")
    parser.add_argument("--check", action="store_true", help="write nothing; exit 0 only when every edit is already applied")
    args = parser.parse_args(argv)
    root = Path(args.root)

    texts, problems, todo, done = plan(root)
    total = len(EDITS) + 2
    for line in problems:
        print(f"PROBLEM  {line}")
    if problems:
        print(f"nothing written: {len(problems)} problem(s)")
        return 1
    if args.check:
        print(f"check: {done} of {total} already applied, {todo} to apply")
        return 0 if todo == 0 else 1
    for name, text in texts.items():
        path = root / name
        if path.read_text(encoding="utf-8") != text:
            path.write_text(text, encoding="utf-8")
            print(f"wrote {name}")
    print(f"applied {todo} edit(s); {done} were already applied ({total} in all)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
