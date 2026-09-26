"""Does the durable PR-draft copy equal "# " + title + "\\n\\n" + body, byte for byte? Read-only."""
import os
import time
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad")
title_p, body_p = S / "data_fixforward_pr_title.txt", S / "data_fixforward_pr_body.md"
copy_p = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/reports/2026-09-24_defect-register-round-42/data438-fixforward-pr-draft.md")
title, body, copy = title_p.read_bytes(), body_p.read_bytes(), copy_p.read_bytes()
for p in (title_p, body_p, copy_p):
    print(p.name, len(p.read_bytes()), "bytes, mtime", time.strftime("%H:%M:%SZ", time.gmtime(os.stat(p).st_mtime)))
print("title ends with newline:", title.endswith(b"\n"), "| title has internal newline:", b"\n" in title.rstrip(b"\n"))
recipe = b"# " + title + b"\n\n" + body
print("copy == '# ' + title + '\\n\\n' + body :", copy == recipe)
recipe_strip = b"# " + title.rstrip(b"\n") + b"\n\n" + body
print("copy == '# ' + title.rstrip('\\n') + '\\n\\n' + body :", copy == recipe_strip)
lines = copy.split(b"\n")
print("copy line 1 starts '# ':", lines[0].startswith(b"# "), "| line 2 blank:", lines[1] == b"", "| line 3 == body line 1:", lines[2] == body.split(b"\n")[0])
print("line-3-onward == body:", b"\n".join(lines[2:]) == body)
