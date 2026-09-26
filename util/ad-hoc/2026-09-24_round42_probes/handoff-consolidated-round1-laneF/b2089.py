"""Compare #2089's files at a2fa3ad8 with the untracked copies in fizzy-hugging-dream (blob sha), and list extras."""
import hashlib, json, os, subprocess
W = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
tree = json.loads(subprocess.run(["gh", "api", "repos/pcalnon/juniper-ml/git/trees/a2fa3ad830623528ad4737cbd2cad03c4be51c12?recursive=1"], capture_output=True, text=True).stdout)
files = json.loads(subprocess.run(["gh", "api", "--paginate", "repos/pcalnon/juniper-ml/pulls/2089/files?per_page=100", "--jq", "[.[].filename]"], capture_output=True, text=True).stdout.replace("]\n[", ","))
blobs = {e["path"]: e["sha"] for e in tree["tree"] if e["type"] == "blob"}
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
print(f"#2089 files: {len(files)}; identical {same}; differ {diff}; missing {missing}")
# extras in the untracked probe dir not in #2089
probe_root = os.path.join(W, "util/ad-hoc/2026-09-24_round42_probes")
fs = set(files)
extra = []
for dp, dn, fn in os.walk(probe_root):
    for n in fn:
        rel = os.path.relpath(os.path.join(dp, n), W)
        if rel not in fs:
            extra.append(rel)
print("extras in untracked probe dir:", len(extra), extra[:10])
