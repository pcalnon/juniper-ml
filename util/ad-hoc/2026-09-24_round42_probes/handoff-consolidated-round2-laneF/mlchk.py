import subprocess, base64, json, re
def gh(args):
    r = subprocess.run(["gh"] + args, capture_output=True, text=True)
    return r.stdout + (("\nERR:" + r.stderr.strip()) if r.returncode else "")
def content(repo, path, ref):
    out = gh(["api", f"repos/pcalnon/{repo}/contents/{path}?ref={ref}", "--jq", ".content"])
    try:
        return base64.b64decode(out).decode("utf-8", "replace")
    except Exception:
        return "ERR " + out[:200]
M = "juniper-ml"
print("--- check-run 107905207679")
print(gh(["api", f"repos/pcalnon/{M}/check-runs/107905207679", "--jq", "[.completed_at, .head_sha[0:8], .conclusion, .output.title] | @tsv"]))
print("--- check-run 107892339574 (#2089)")
print(gh(["api", f"repos/pcalnon/{M}/check-runs/107892339574", "--jq", "[.completed_at, .head_sha[0:8], .conclusion, .output.title] | @tsv"]))
print("--- high alerts on refs/pull/2097/merge and head")
for ref in ("refs/pull/2097/merge", "refs/pull/2097/head", "refs/pull/2089/merge"):
    out = gh(["api", "--paginate", f"repos/pcalnon/{M}/code-scanning/alerts?ref={ref}&state=open&per_page=100",
              "--jq", '.[] | select(.rule.security_severity_level == "high") | [.number, .rule.id, .most_recent_instance.location.path, .most_recent_instance.location.start_line] | @tsv'])
    print(ref, out.strip()[:1500])
print("--- probe lines (#2097 head)")
base = "util/ad-hoc/2026-09-24_round42_probes/bytes-compare-ml2086-data440-cascor689-vbytes/"
for f, lines in (("surrogate_config_probe.py", (18, 29)), ("sentry_deep_probe.py", (18, 196, 201))):
    src = content(M, base + f, "2e4917c2727fcd57a8cb7885118782a7da1d2eef").splitlines()
    for n in lines:
        print(f, n, src[n - 1][:150] if n - 1 < len(src) else "")
    print(f, "SECRET defs:", [(i + 1, l.strip()[:100]) for i, l in enumerate(src) if re.match(r"\s*SECRET\s*=", l)])
print("--- #2089 README counts")
rd = content(M, "util/ad-hoc/2026-09-24_round42_probes/README.md", "a2fa3ad830623528ad4737cbd2cad03c4be51c12")
for i, l in enumerate(rd.splitlines()):
    if re.search(r"\b(66|67|48|18|129)\b", l) or ".bash" in l or "shell" in l.lower():
        print(i + 1, l[:220])
print("rows mentioning lane F dirs:", [l[:80] for l in rd.splitlines() if any(k in l for k in ("cascor686-v686", "canopy683-v683", "cascor688-v688", "vbytes"))][:8])
print("--- #2089 file counts")
fl = gh(["api", "--paginate", f"repos/pcalnon/{M}/pulls/2089/files", "--jq", ".[].filename"]).split()
print(len(fl), "py", sum(1 for f in fl if f.endswith(".py")), "md", sum(1 for f in fl if f.endswith(".md")))
print("--- codeql.yml on main")
cq = content(M, ".github/workflows/codeql.yml", "main")
print([l.strip() for l in cq.splitlines() if "queries" in l or "config" in l or "paths-ignore" in l or "security-and-quality" in l])
print("--- #2080 body lines")
b = gh(["api", f"repos/pcalnon/{M}/pulls/2080", "--jq", ".body"]).split("\n")
for n in (19, 20, 21, 41, 42, 65, 69):
    print(n, b[n - 1][:200] if n - 1 < len(b) else "")
print("--- #2088 body line 47")
b2 = gh(["api", f"repos/pcalnon/{M}/pulls/2088", "--jq", ".body"]).split("\n")
print(47, b2[46][:200] if len(b2) > 46 else "")
print("--- #2088 files")
print(gh(["api", "--paginate", f"repos/pcalnon/{M}/pulls/2088/files", "--jq", ".[].filename"]))
print("--- #2100 body grep")
b3 = gh(["api", f"repos/pcalnon/{M}/pulls/2100", "--jq", ".body"])
print([l[:200] for l in b3.splitlines() if "notify" in l.lower() or "403" in l or "2703c8" in l or "containers" in l.lower()][:10])
fl3 = gh(["api", f"repos/pcalnon/{M}/pulls/2100/files", "--jq", ".[].filename"])
print(fl3)
