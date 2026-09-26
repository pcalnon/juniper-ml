"""Compare #2097's files at 2e4917c2 with the untracked copies in happy-skipping-hollerith (blob sha)."""
import hashlib, json, os, subprocess
W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/happy-skipping-hollerith"
tree = json.loads(subprocess.run(["gh", "api", "repos/pcalnon/juniper-ml/git/trees/2e4917c2727fcd57a8cb7885118782a7da1d2eef?recursive=1"], capture_output=True, text=True).stdout)
blobs = {e["path"]: e["sha"] for e in tree["tree"] if e["type"] == "blob"}
files = [l.strip() for l in open("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/hc1/laneF/pr2097_files.txt") if l.strip()]
def blob_sha(p):
    data = open(p, "rb").read()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
same = diff = missing = 0
for f in files:
    lp = os.path.join(W, f)
    if not os.path.exists(lp):
        missing += 1; print("MISSING", f); continue
    if blob_sha(lp) == blobs.get(f):
        same += 1
    else:
        diff += 1; print("DIFF", f)
print(f"#2097 files: {len(files)}; identical {same}; differ {diff}; missing {missing}")
