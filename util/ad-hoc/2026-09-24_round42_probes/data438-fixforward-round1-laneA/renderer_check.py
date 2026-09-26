#!/usr/bin/env python3
"""Lane A: run juniper-ml's notes_render.parse_unreleased (at df21367d) over head's and base's CHANGELOG.md.

notes_render.py is read with ``git show df21367d:...`` into scratch (read-only) and imported from there.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

SCRATCH = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/r42d/laneA")
ML = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
DATA = "/home/pcalnon/Development/python/Juniper/juniper-data"
render_src = subprocess.run(["git", "-C", ML, "show", "df21367d:util/release_train/notes_render.py"], check=True, capture_output=True).stdout
dest = SCRATCH / "notes_render_df21367d.py"
dest.write_bytes(render_src)
spec = importlib.util.spec_from_file_location("notes_render_df21367d", dest)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

for name, ref in (("head", "d1c66a112e4bc70ee97496a14265f7b90e10fb88"), ("base", "0f0f7e0e226e6046fc49541a4baa6dd1bd8b67ce")):
    text = subprocess.run(["git", "-C", DATA, "show", f"{ref}:CHANGELOG.md"], check=True, capture_output=True, text=True).stdout
    sections = mod.parse_unreleased(text)
    counts = {key: len(bullets) for key, bullets in sections.items()}
    moved = [key for key, bullets in sections.items() for bullet in bullets if "Moved here from" in bullet]
    print(f"{name}: sections={counts} breaking={mod._is_breaking(sections)} 'Moved here' in bullets of: {moved}")
    if name == "head":
        for key, bullets in sections.items():
            for i, bullet in enumerate(bullets):
                first = bullet.splitlines()[0][:110]
                print(f"   {key}[{i}] marker={mod._has_breaking_marker(bullet)} :: {first}")
