"""
Write REF:AGENTS.md to OUT with its `**Last Updated**:` line set to DATE; refuse unless exactly that one line changes.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-18
Status: ad-hoc — one-off (the UTC-midnight rollover on juniper-ml#2245)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-ml#2245, juniper-ml#2247; util/ad-hoc/2026-10-17_push_signed_with_retry.py (pushes OUT)

Why: the advisory "Verify AGENTS.md Last Updated" check fails any PR that changes AGENTS.md without setting
`**Last Updated**:` to today's UTC date. #2245 (G2) was refreshed after 00:00Z on 2026-10-19 and failed it. This
produced the one-line bump for a signed push, but auto-merge, which does not wait for advisory checks, merged
#2245 first. B7 (#2247) then carried the bump. turing never commits locally, so the bumped file is written
out for `push_signed_with_retry.py --file OUT:AGENTS.md`, not edited in place.

Usage:
    python3 -I util/ad-hoc/2026-10-18_agents_md_last_updated_bump.py REF YYYY-MM-DD OUT
"""
import re
import subprocess
import sys
from pathlib import Path

ref, date, out = sys.argv[1:]
subprocess.run(["git", "fetch", "origin", "--quiet"], check=True)
text = subprocess.run(["git", "show", f"{ref}:AGENTS.md"], check=True, capture_output=True, text=True).stdout
new, n = re.subn(r"^\*\*Last Updated\*\*: \d{4}-\d{2}-\d{2}$", f"**Last Updated**: {date}", text, count=1, flags=re.M)
if n != 1 or new == text:
    sys.exit(f"refusing: matched {n} line(s), changed={new != text}")
Path(out).write_text(new, encoding="utf-8")
changed = [(a, b) for a, b in zip(text.splitlines(), new.splitlines()) if a != b]
print(f"wrote {out}; {len(changed)} line changed: {changed}")
