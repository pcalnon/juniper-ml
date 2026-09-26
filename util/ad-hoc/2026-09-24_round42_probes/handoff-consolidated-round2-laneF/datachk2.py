import subprocess, pathlib
D = "/home/pcalnon/Development/python/Juniper/juniper-data"
ML = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
def g(repo, *a):
    r = subprocess.run(["git", "-C", repo] + list(a), capture_output=True, text=True)
    return r.stdout
src = g(D, "show", "d1c66a11:juniper_data/api/app.py").splitlines()
print("d1c66a11", [(i + 1, l.strip()[:60]) for i, l in enumerate(src) if "exception_handler" in l])
print("--- ml main has verify script?")
print(g(ML, "ls-tree", "--name-only", "origin/main", "util/ad-hoc/2026-09-24_verify_data_0_16_0_notes_match_tag.py"))
print("--- data workflows symbol-loss")
for f in g(D, "ls-tree", "--name-only", "origin/main", ".github/workflows/").split():
    body = g(D, "show", f"origin/main:{f}")
    if "symbol-loss" in body or "symbol_loss" in body:
        lines = [(i + 1, l.strip()[:160]) for i, l in enumerate(body.splitlines()) if "symbol-loss-check" in l or "symbol_loss" in l]
        print(f, lines[:6])
print("--- data worktree HEAD")
wt = "/home/pcalnon/Development/python/Juniper/worktrees/juniper-data--fix--conditional-requests-round3-followups--20260924-0323--39d1cab2"
print(g(wt, "rev-parse", "HEAD"))
print("--- 5 older/other worktrees: HEAD, dirty counts")
base = "/home/pcalnon/Development/python/Juniper/worktrees/"
for name in ["juniper-cascor--fix--shortfall-mixed-provenance-and-678-followups--20260924-0235--0e016a7c",
             "juniper-canopy--fix--secret-leaks-683-validation--20260924-1333--8917fdac",
             "juniper-cascor--fix--bytes-compare-no-500--20260924-1337--ec8b5bdb",
             "juniper-data--fix--bytes-compare-no-500--20260924-1337--1afc3480",
             "juniper-canopy--fix--blank-key-678-followups--20260924-0235--e9053227",
             "juniper-cascor--fix--nonshortcircuit-key-compare--20260921-0846--c6c848f2",
             "juniper-data--feature--tri-state-allow-truncation--20260922-0753--e8db3ba6",
             "juniper-data--fix--cheatsheet-conflict-markers--20260922-0820--e8db3ba6",
             "juniper-cascor--docs--tri-state-truncation-prose--20260922-0822--8065ca0f"]:
    p = base + name
    head = g(p, "rev-parse", "--short=8", "HEAD").strip()
    tree = g(p, "rev-parse", "--short=8", "HEAD^{tree}").strip()
    sig = g(p, "log", "-1", "--format=%G?").strip()
    st = subprocess.run(["git", "--no-optional-locks", "-C", p, "status", "--porcelain"], capture_output=True, text=True).stdout
    n = len([l for l in st.splitlines() if l.strip()])
    print(f"{name[:70]:72} HEAD {head} tree {tree} sig {sig} dirty {n}")
print("--- trees of PR heads")
C = "/home/pcalnon/Development/python/Juniper/juniper-cascor"
CA = "/home/pcalnon/Development/python/Juniper/juniper-canopy"
print("97341680 tree", g(C, "rev-parse", "--short=8", "97341680^{tree}").strip())
print("0bee089e tree", g(D, "rev-parse", "--short=8", "0bee089e^{tree}").strip())
print("4a8af2a0 tree", g(CA, "rev-parse", "--short=8", "4a8af2a0^{tree}").strip())
print("--- shared clones HEAD vs origin/main")
for repo in (D, C, CA):
    print(repo.rsplit("/", 1)[1], g(repo, "rev-parse", "--short=8", "HEAD").strip(), g(repo, "rev-parse", "--short=8", "origin/main").strip(), g(repo, "branch", "--show-current").strip())
