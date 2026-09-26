import subprocess, re, pathlib
D = "/home/pcalnon/Development/python/Juniper/juniper-data"
def g(*a):
    r = subprocess.run(["git", "-C", D] + list(a), capture_output=True, text=True)
    return r.stdout
def gh(args):
    r = subprocess.run(["gh"] + args, capture_output=True, text=True)
    return r.stdout.strip() + (("\nERR:" + r.stderr.strip()) if r.returncode else "")
print("--- local refs")
print(g("rev-parse", "HEAD", "origin/main", "origin/fix/conditional-requests-round4-followups"))
print("remote main:", gh(["api", "repos/pcalnon/juniper-data/commits/main", "--jq", ".sha + \" \" + .commit.committer.date"]))
print("--- 94ce8b1f message")
print(g("log", "-1", "--format=%B", "94ce8b1f"))
print("--- d1c66a11 message grep waiver")
print([l for l in g("log", "-1", "--format=%B", "d1c66a11").splitlines() if "Allow-Symbol-Loss" in l])
print("--- files 0f0f7e0e..94ce8b1f / d1c66a11..94ce8b1f / 0f0f7e0e..0bee089e")
print(g("diff", "--stat=200", "d1c66a11", "94ce8b1f"))
print(g("diff", "--name-only", "0f0f7e0e", "94ce8b1f"))
print(g("diff", "--name-only", "0f0f7e0e", "0bee089e"))
print("--- app.py handler anchors")
for sha in ("0f0f7e0e", "94ce8b1f", "26491531"):
    src = g("show", f"{sha}:juniper_data/api/app.py").splitlines()
    hits = [(i + 1, l.strip()[:90]) for i, l in enumerate(src) if "exception_handler" in l or "def _value_error" in l or "ValueError" in l]
    print(sha, hits[:12])
print("--- compute_checksum in datasets.py")
for sha in ("0f0f7e0e", "94ce8b1f"):
    src = g("show", f"{sha}:juniper_data/api/routes/datasets.py").splitlines()
    print(sha, [(i + 1, l.strip()[:100]) for i, l in enumerate(src) if "compute_checksum" in l])
print("--- stage_save / executor / record_access")
src = g("show", "94ce8b1f:juniper_data/storage/local_fs.py")
print("stage_save" in src, src.count("stage_save"))
for p in ("juniper_data/api/routes/datasets.py", "juniper_data/api/app.py", "juniper_data/storage/base.py"):
    s = g("show", f"94ce8b1f:{p}")
    print(p, [(i + 1, l.strip()[:110]) for i, l in enumerate(s.splitlines()) if "ThreadPoolExecutor" in l or "max_workers" in l][:6])
print("--- local_fs.py lines at 94ce8b1f")
lf = g("show", "94ce8b1f:juniper_data/storage/local_fs.py").splitlines()
for n in (175, 183, 237, 243, 248, 325, 326):
    print(n, lf[n - 1][:120] if n - 1 < len(lf) else "")
print("--- CHANGELOG 3-way (base 0f0f7e0e, ours 94ce8b1f, theirs 26491531)")
sc = pathlib.Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/hc2/laneF")
for name, sha in (("base", "0f0f7e0e"), ("ours", "94ce8b1f"), ("theirs", "26491531")):
    (sc / f"cl_{name}.md").write_text(g("show", f"{sha}:CHANGELOG.md"), encoding="utf-8")
r = subprocess.run(["git", "merge-file", "-p", str(sc / "cl_ours.md"), str(sc / "cl_base.md"), str(sc / "cl_theirs.md")], capture_output=True, text=True)
print("merge-file exit (conflicts):", r.returncode)
for n in ("base", "ours", "theirs"):
    (sc / f"cl_{n}.md").unlink()
print("--- main ahead of 26491531?")
print(g("log", "--oneline", "26491531..origin/main"))
print("--- verify script on main")
print(g("ls-tree", "--name-only", "origin/main", "util/ad-hoc/2026-09-24_verify_data_0_16_0_notes_match_tag.py"))
print("--- lock pins")
lock = g("show", "origin/main:requirements.lock").splitlines()
print([l for l in lock if l.startswith(("fastapi==", "starlette==", "juniper-observability==", "juniper-service-core=="))])
print([(i + 1, l) for i, l in enumerate(lock) if l.startswith(("juniper-observability==", "juniper-service-core=="))])
print("--- security.py anchors at main")
sec = g("show", "origin/main:juniper_data/api/security.py").splitlines()
print([(i + 1, l.strip()[:100]) for i, l in enumerate(sec) if "surrogatepass" in l or "compare_digest(" in l])
print("--- 440 files")
print(g("diff", "--name-only", "0f0f7e0e", "26491531"))
