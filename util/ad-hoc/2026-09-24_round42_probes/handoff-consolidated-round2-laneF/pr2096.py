import subprocess, json, base64, hashlib, pathlib
def gh(args):
    r = subprocess.run(["gh"] + args, capture_output=True, text=True)
    return r.stdout.strip() + (("\nERR:" + r.stderr.strip()) if r.returncode else "")
def run(*c, cwd=None):
    return subprocess.run(c, cwd=cwd, capture_output=True, text=True)
head = "00e9eb2d8c0597333a6fd9865bbb80860c084723"
files = gh(["api", "--paginate", "repos/pcalnon/juniper-ml/pulls/2096/files", "--jq", ".[] | [.filename, .sha, .status] | @tsv"])
print(files)
# compare blobs with other worktrees' files
wt = pathlib.Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees")
cands = {
  "graceful-sprouting-panda handoff": wt / "graceful-sprouting-panda/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-e2e-phase9-landed-ten-rounds-owner-answered-followup-684.md",
  "bubbly draft": wt / "bubbly-meandering-pie/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md",
}
for k, p in cands.items():
    if p.is_file():
        data = p.read_bytes()
        h = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
        print(k, h[:8], len(data))
        lines = data.decode("utf-8", "replace").splitlines()
        if "bubbly" in k:
            for i in range(163, 171):
                print("   ", i + 1, lines[i][:200] if i < len(lines) else "")
        else:
            for i in range(52, 67):
                print("   ", i + 1, lines[i][:160] if i < len(lines) else "")
    else:
        print(k, "MISSING", p)
