#!/usr/bin/env python3
"""Diff notes_render's "Breaking changes" verdict, old rule vs new, over every registered CHANGELOG.

Project:     Juniper
Sub-Project: juniper-ml
Application: ad-hoc release-train verification
Author:      Paul Calnon
Created:     2026-09-22
Version:     0.1.0
License:     MIT License
Status:      single-use (the _is_breaking marker normalisation; round 3 of the decision-11 arc)

Why this exists
---------------
``util/release_train/notes_render.py`` decides the published "Breaking changes: YES/NO" line. The
2026-09-22 fix honoured an uppercase ``BREAKING`` marker and was measured only on the two releases
it was built for; juniper-canopy marks breaks in three other ways and a substring test reads
``NON-BREAKING`` as a break. This script renders both rules over EVERY ``## [<version>]`` section
of all 18 registry packages (read from each repo's ``origin/main``, not a checkout) and prints the
sections whose verdict flips, with the line that caused it -- so each flip can be judged by a human.

A corpus that agrees with a rule does not validate it: this finds WHERE the rules differ; the unit
tests in ``tests/test_release_train_ceremony.py`` decide which is right, on constructed shapes.

It also censuses ``###`` headings that carry a breaking qualifier after the category word (e.g.
``### Changed (BREAKING -- ...)``): both section parsers keep only the first word, so such a
qualifier never reaches the verdict. The docstring of ``_is_breaking`` claims no registered package
uses that form; this is the measurement behind the claim.

Usage
-----
    python3 util/ad-hoc/2026-09-22_breaking_marker_corpus_diff.py [--ecosystem-root DIR]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "util" / "release_train"))  # the modules import each other top-level

import ceremony  # noqa: E402
import notes_render  # noqa: E402

_VERSION_HEADING = re.compile(r"^##\s*\[([^\]]+)\]", re.MULTILINE)
_QUALIFIED_HEADING = re.compile(r"^###\s+[A-Za-z]+\W.*break", re.IGNORECASE)


def _old_rule(sections: dict) -> bool:
    """The rule as shipped before this change (kept verbatim for the comparison).

    Must be fed OLD-shaped sections (``_old_shape``): the old parsers keyed every heading by its
    first word, so a qualified ``### Removed (...)`` was a plain ``Removed`` to this rule."""
    if "removed" in {k.lower() for k in sections}:
        return True
    return any("BREAKING" in bullet for bullets in sections.values() for bullet in bullets)


def _old_shape(sections: dict) -> dict:
    """Re-key new-parser output the way the old parsers keyed it: by category word, merged."""
    merged: dict = {}
    for key, bullets in sections.items():
        merged.setdefault(notes_render.category_word(key), []).extend(bullets)
    return merged


def _read_changelog(eco: Path, repo: str, rel: str) -> "str | None":
    try:
        return subprocess.run(["git", "-C", str(eco / repo), "show", f"origin/main:{rel}"], check=True, capture_output=True, text=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        path = eco / repo / rel
        return path.read_text(encoding="utf-8") if path.exists() else None


def _evidence(sections: dict) -> str:
    for key in sections:
        if key.lower().startswith("breaking") or (key != notes_render.category_word(key) and "break" in key.lower()):
            return f"heading '### {key}'"
    for bullets in sections.values():
        for bullet in bullets:
            for line in bullet.splitlines():
                if notes_render._LABEL_RE.match(line.strip()) or "BREAKING" in line:
                    return line.strip()[:110]
    return "(no marker line -- verdict from category keys)"


def _default_ecosystem_root() -> str:
    """The nearest ancestor holding the sibling repos -- a worktree lives several levels down."""
    for parent in _REPO.parents:
        if (parent / "juniper-cascor").is_dir() and (parent / "juniper-canopy").is_dir():
            return str(parent)
    return str(_REPO.parent)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ecosystem-root", default=_default_ecosystem_root())
    args = ap.parse_args()
    eco = Path(args.ecosystem_root)

    registry = yaml.safe_load((_REPO / "util/release_train/registry.yaml").read_text(encoding="utf-8"))
    packages = registry["packages"] if isinstance(registry, dict) else registry

    n_sections = n_flips = n_render = 0
    qualified: list = []
    for pkg in packages:
        rel = str(Path(pkg.get("path") or ".") / "CHANGELOG.md").removeprefix("./")
        text = _read_changelog(eco, pkg["repo"], rel)
        if text is None:
            print(f"!! {pkg['pypi_name']}: no CHANGELOG at {pkg['repo']}/{rel}")
            continue
        # dict.fromkeys: some CHANGELOGs repeat a version heading (pre-polyrepo history), and the
        # section parser only ever reads the first -- count each version once.
        for version in dict.fromkeys(_VERSION_HEADING.findall(text)):
            if version.lower() == "unreleased":
                sections = notes_render.parse_unreleased(text)
            else:
                sections = ceremony.changelog_version_section(text, version)
            n_sections += 1
            old, new = _old_rule(_old_shape(sections)), notes_render._is_breaking(sections)
            if old != new:
                n_flips += 1
                print(f"FLIP {pkg['pypi_name']} [{version}]: {'YES' if old else 'NO'} -> {'YES' if new else 'NO'}  | {_evidence(sections)}")
            kept = [k for k in sections if k != notes_render.category_word(k)]
            if kept:
                n_render += 1
                print(f"RENDER {pkg['pypi_name']} [{version}]: heading(s) now kept whole: {kept}")
        for line in text.splitlines():
            if _QUALIFIED_HEADING.match(line):
                qualified.append(f"{pkg['pypi_name']}: {line.strip()[:110]}")

    print(f"\n{n_sections} sections across {len(packages)} packages; {n_flips} verdict flip(s); {n_render} section(s) whose rendered headings change.")
    print(f"qualified '### <Category> ...break...' headings in registered CHANGELOGs: {len(qualified)}")
    for q in qualified:
        print(f"  {q}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
