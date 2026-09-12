#!/usr/bin/env python
# ---------------------------------------------------------------------------
# Project     : Juniper
# Sub-Project : juniper-ml (ad-hoc)
# Application : release train
# Author      : Paul Calnon
# License     : MIT License
# ---------------------------------------------------------------------------
"""Print the EXACT release-notes body the ceremony would publish, before it runs.

``ceremony.py --dry-run --json`` reports the four planned actions but not
``plan.archive_content`` -- and that content is both the Release body and the archived
file, so it is the one artefact of the ceremony that a human should read *before*
`--execute`, not after. Cutting a Release is not reversible by re-cutting.

Standalone ``notes_render.py`` is NOT a substitute: it sources the CHANGELOG's
``[Unreleased]`` section, while the ceremony sources the RELEASED ``[<version>]`` section
(ceremony.changelog_version_section, :417). On a package whose proposal PR has already
moved the bullets, the standalone renderer prints "no [Unreleased] bullets found" while
the ceremony renders the full set -- opposite answers to the same question.

Usage:
  python util/ad-hoc/2026-09-12_ceremony_notes_preview.py \
      --package juniper-canopy --version 0.8.0 --release-date 2026-09-12
"""

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
# ceremony.py itself does a flat ``import detect``, so the package dir -- not ``util/`` --
# is what has to be on the path.
sys.path.insert(0, str(REPO_ROOT / "util" / "release_train"))

import ceremony  # noqa: E402
import detect  # noqa: E402
import notes_render  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--package", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--release-date", required=True)
    ap.add_argument("--released-version", default=None, help="previous released version (for the bump label)")
    ap.add_argument("--repo-root", default=str(REPO_ROOT))
    ap.add_argument("--ecosystem-root", default=None)
    args = ap.parse_args()

    repo_root = Path(args.repo_root).resolve()
    eco_root = Path(args.ecosystem_root).resolve() if args.ecosystem_root else repo_root.parent

    entries = detect.load_registry(REPO_ROOT / "util" / "release_train" / "registry.yaml")
    entry = next((e for e in entries if e.pypi_name == args.package), None)
    if entry is None:
        print(f"no registry entry for {args.package!r}", file=sys.stderr)
        return 2

    base = repo_root if entry.repo == "juniper-ml" else (eco_root / entry.repo)
    clog_path = base / ceremony.changelog_rel(entry)
    sections = ceremony.changelog_version_section(clog_path.read_text(encoding="utf-8"), args.version)
    if not sections:
        print(f"EMPTY: no [{args.version}] section in {clog_path} -- the ceremony would HALT", file=sys.stderr)
        return 1

    tag = ceremony.release_tag(entry, args.version)
    link_base = f"https://github.com/{ceremony.DEFAULT_OWNER}/{entry.repo}/blob/{tag}"
    body = notes_render.render_notes(
        entry.pypi_name,
        args.version,
        bump=ceremony.infer_bump(args.released_version, args.version),
        release_date=args.release_date,
        sections=sections,
        repo_root=repo_root,
        link_base=link_base,
        changelog_url=f"{link_base}/{ceremony.changelog_rel(entry)}",
        final=True,
    )
    print(f"# archive: {ceremony.archive_relpath(entry, args.version)}", file=sys.stderr)
    print(f"# tag:     {tag}", file=sys.stderr)
    print(f"# sections: {[(k, len(v)) for k, v in sections.items()]}", file=sys.stderr)
    sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
