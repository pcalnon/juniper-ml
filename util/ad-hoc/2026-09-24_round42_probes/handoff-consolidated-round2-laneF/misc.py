import subprocess, base64, hashlib, json, re
from pathlib import Path
def gh(args):
    r = subprocess.run(["gh"] + args, capture_output=True, text=True)
    return r.stdout + (("\nERR:" + r.stderr.strip()) if r.returncode else "")
def content(repo, path, ref):
    out = gh(["api", f"repos/pcalnon/{repo}/contents/{path}?ref={ref}", "--jq", ".content"])
    try:
        return base64.b64decode(out).decode("utf-8", "replace")
    except Exception:
        return "ERR " + out[:200]
print("--- cascor CI on 0fbb447a / b9484fef CI/CD run details")
print(gh(["api", "repos/pcalnon/juniper-cascor/actions/runs?head_sha=0fbb447a1455ca19ef042a5f925b306ab2d3e3e2&per_page=20", "--jq", '.workflow_runs[] | [.name, .status, (.conclusion // "-"), .updated_at] | @tsv']))
print(gh(["api", "repos/pcalnon/juniper-cascor/actions/runs?head_sha=b9484fef98430a6b0c833c5a158cb94f4a132912&per_page=20", "--jq", '.workflow_runs[] | select(.name == "CI/CD Pipeline") | [.id, .status, .conclusion, .updated_at] | @tsv']))
print("--- serve script (#2097 head)")
s = content("juniper-ml", "util/ad-hoc/2026-09-24_serve_scratch_juniper_data.bash", "2e4917c2727fcd57a8cb7885118782a7da1d2eef").splitlines()
print([(i + 1, l.strip()[:140]) for i, l in enumerate(s) if "timeout" in l or "JuniperData/bin/python" in l][:5])
h = content("juniper-ml", "util/ad-hoc/2026-09-24_cascor690_as_bool_stance_mutation_check.py", "2e4917c2727fcd57a8cb7885118782a7da1d2eef").splitlines()
print([(i + 1, l.strip()[:140]) for i, l in enumerate(h) if "cascor688_fixforward" in l][:4])
print("--- happy-skipping-hollerith vs #2097")
W = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/happy-skipping-hollerith")
gitfile = (W / ".git").read_text().strip()
gitdir = Path(gitfile.split(": ", 1)[1])
head = (gitdir / "HEAD").read_text().strip()
print("HEAD file:", head)
ref = head.split(": ", 1)[1] if head.startswith("ref:") else None
common = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.git")
refpath = common / ref if ref else None
sha = refpath.read_text().strip() if refpath and refpath.exists() else "(packed?)"
if sha == "(packed?)":
    for line in (common / "packed-refs").read_text().splitlines():
        if line.endswith(" " + ref):
            sha = line.split()[0]
print("ref sha:", sha[:8])
files = gh(["api", "--paginate", "repos/pcalnon/juniper-ml/pulls/2097/files", "--jq", ".[] | [.filename, .sha] | @tsv"]).strip().splitlines()
ok = bad = missing = 0
for line in files:
    fn, bsha = line.split("\t")
    p = W / fn
    if not p.is_file():
        missing += 1
        continue
    data = p.read_bytes()
    hsh = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
    if hsh == bsha:
        ok += 1
    else:
        bad += 1
print("2097 files:", len(files), "identical", ok, "differ", bad, "missing", missing)
print("--- canopy security.py / csrf.py at main (dc5ea02e)")
c = content("juniper-canopy", "src/security.py", "dc5ea02e8aac81a009cb30e35633ce8b43d972c8").splitlines()
print([(i + 1, l.strip()[:110]) for i, l in enumerate(c) if "surrogatepass" in l or "compare_digest" in l or "_compare_bytes" in l or re.search(r"presented\s*=", l)])
for n in (42, 52, 113, 115, 135, 136, 137, 300):
    print(n, c[n - 1][:120])
cs = content("juniper-canopy", "src/csrf.py", "dc5ea02e8aac81a009cb30e35633ce8b43d972c8").splitlines()
print("csrf 97:", cs[96][:120])
o = content("juniper-canopy", "src/outbound_errors.py", "dc5ea02e8aac81a009cb30e35633ce8b43d972c8").splitlines()
print("outbound 57-61:", [o[i][:100] for i in range(56, 61)])
t = content("juniper-canopy", "src/tests/unit/test_cascor_service_adapter_gate_coverage.py", "dc5ea02e8aac81a009cb30e35633ce8b43d972c8").splitlines()
print("gate cov 49-50:", [t[i][:120] for i in range(48, 50)] if len(t) > 50 else "short/missing", len(t))
