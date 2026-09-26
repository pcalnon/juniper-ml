import subprocess, base64, json, re, pathlib
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
src = content(M, "util/ad-hoc/2026-09-24_round42_probes/bytes-compare-ml2086-data440-cascor689-vbytes/surrogate_config_probe.py", "2e4917c2727fcd57a8cb7885118782a7da1d2eef").splitlines()
for n in range(8, 31):
    print(n, src[n - 1][:130] if n - 1 < len(src) else "")
b = gh(["api", f"repos/pcalnon/{M}/pulls/2080", "--jq", ".body"]).split("\n")
for n in range(22, 25):
    print("2080 body", n, b[n - 1][:160])
h = "2e4917c2727fcd57a8cb7885118782a7da1d2eef"
print("--- #2100 handoff grep")
for f in ("prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_data-0-16-0-on-pypi-and-pinned-the-stack-generates-equities-wave-4-waits-on-the-token.md",):
    t = content(M, f, "afc12c6558cdeecd73ff72fa3cc906651bde45dd")
    for i, l in enumerate(t.splitlines()):
        if re.search(r"notify|403|dispatch|2703c8|containers \[", l, re.I):
            print(i + 1, l[:200])
    print("head:", t.splitlines()[:6])
print("--- #2100 commit session")
print(gh(["api", f"repos/pcalnon/{M}/pulls/2100/commits", "--jq", ".[] | [.sha[0:8], .commit.committer.date, (.commit.message | split(\"\\n\") | map(select(test(\"Claude-Session\"))) | join(\" \"))] | @tsv"]))
