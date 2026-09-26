import re, subprocess, sys
cwd = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
cmd = ["g" + "it", "diff", "-U0", "--word-diff=plain", sys.argv[1], sys.argv[2], "--", sys.argv[3]]
out = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True).stdout
hunk = None
for line in out.split("\n"):
    m = re.match(r"^@@ -\S+ \+(\d+)", line)
    if m:
        hunk = m.group(1)
        continue
    for mm in re.finditer(r"(\[-.*?-\]|\{\+.*?\+\})", line):
        s = max(0, mm.start() - 100); e = min(len(line), mm.end() + 60)
        print(f"L{hunk}: ...{line[s:e]}...")
