#!/usr/bin/env python3
"""Lane B (round 3, juniper-data#428): run the release ceremony's CHANGELOG section parser
on juniper-data's CHANGELOG.md as it stands at 3a76a4c (extracted copy), read-only.

Prints, for the requested version: every category, its bullet count, and the first line of
each bullet; then renders the FINAL notes body the ceremony would publish.
"""

from __future__ import annotations

import sys
from pathlib import Path

ML = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/hazy-beaming-map")
sys.path.insert(0, str(ML / "util" / "release_train"))

import ceremony  # noqa: E402
import notes_render  # noqa: E402

clog_path = Path(sys.argv[1])
version = sys.argv[2]
text = clog_path.read_text(encoding="utf-8")

sections = ceremony.changelog_version_section(text, version)
print(f"== changelog_version_section({clog_path.name!r}, {version!r})")
total = 0
for cat, bullets in sections.items():
    print(f"-- {cat}: {len(bullets)} bullet(s)")
    total += len(bullets)
    for b in bullets:
        first = b.strip().splitlines()[0] if b.strip() else "<empty>"
        print(f"     * {first[:150]}")
print(f"== total bullets: {total}")

# Mark which heading line the parser anchored on.
lines = text.splitlines()
hits = [i + 1 for i, ln in enumerate(lines) if ln.startswith(f"## [{version}]")]
print(f"== '## [{version}]' heading lines in file: {hits}")

if len(sys.argv) > 3 and sys.argv[3] == "--render":
    body = notes_render.render_notes(
        "juniper-data",
        version,
        bump="minor",
        release_date="2026-09-24",
        sections=sections,
        repo_root=ML,
        link_base=f"https://github.com/pcalnon/juniper-data/blob/v{version}",
        changelog_url=f"https://github.com/pcalnon/juniper-data/blob/v{version}/CHANGELOG.md",
        final=True,
    )
    out = Path(sys.argv[4])
    out.write_text(body, encoding="utf-8")
    print(f"== rendered FINAL notes written to {out} ({len(body)} chars)")
