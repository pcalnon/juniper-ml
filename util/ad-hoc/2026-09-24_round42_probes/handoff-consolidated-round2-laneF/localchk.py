import subprocess, re, os, glob, datetime
from pathlib import Path
ML = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream")
SC = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad")
R = ML / "reports/2026-09-24_defect-register-round-42"
def g(*a, cwd=ML):
    return subprocess.run(["git"] + list(a), cwd=cwd, capture_output=True, text=True).stdout
def mt(p):
    return datetime.datetime.utcfromtimestamp(os.path.getmtime(p)).strftime("%H:%M:%SZ")
print("--- PR draft vs tmpfs")
d = (R / "data438-fixforward-pr-draft.md").read_text(encoding="utf-8")
t = (SC / "data_fixforward_pr_title.txt").read_text(encoding="utf-8") if (SC / "data_fixforward_pr_title.txt").exists() else None
b = (SC / "data_fixforward_pr_body.md").read_text(encoding="utf-8") if (SC / "data_fixforward_pr_body.md").exists() else None
if t is not None and b is not None:
    print("equal:", d == "# " + t.strip("\n") + "\n\n" + b, "| alt:", d.rstrip("\n") == ("# " + t.strip() + "\n\n" + b).rstrip("\n"))
    print("mtimes draft", mt(R / "data438-fixforward-pr-draft.md"), "title", mt(SC / "data_fixforward_pr_title.txt"), "body", mt(SC / "data_fixforward_pr_body.md"))
print("draft line1:", d.splitlines()[0][:200])
print("mentions d1c66a11:", d.count("d1c66a11"), "94ce8b1f:", d.count("94ce8b1f"))
print("--- fix report numbers")
fr = (R / "data438-fixforward-round1-fix-report.md").read_text(encoding="utf-8")
for pat in ["1923", "97.60", "1783", "140 deselected", "118", "89 arms", "132 caught", "0 vacuous", "135 control", "111/111", "100 must-fail", "12 files", "2 findings", "19 warn", "17 of 123", "39", "7.4", "0.66", "0.74", "4.693", "0.011", "4.686", "0.014", "95 rows", "stall_probe2", "M86", "0.73", "175, 183", "either order", "merge cleanly", "cleanly", "ruff format", "http_cache"]:
    hits = [l.strip()[:150] for l in fr.splitlines() if pat in l]
    print(f"[{pat}]", len(hits), hits[:1])
print("--- doc2 quotes")
d2 = (SC / "hc2/doc2_peer_final_2e4917c2.md").read_text(encoding="utf-8")
for pat in ["closes when F4 lands", "condition is met", "Never message it", "governs"]:
    print(f"[{pat}]", [l.strip()[:200] for l in d2.splitlines() if pat in l][:3])
d1 = (SC / "hc2/doc1_r2_frozen.md").read_text(encoding="utf-8")
print("--- doc1 'message it too'", [l.strip()[:200] for l in d1.splitlines() if "message it too" in l][:3])
print("--- snapshot 11-20")
snap = g("show", "origin/main:reports/2026-09-24_defect-register-round-42/pending-items-snapshot-2026-09-24T1110Z.md")
sl = snap.splitlines()
for n in range(11, 21):
    print(n, sl[n - 1][:170] if n - 1 < len(sl) else "")
print("--- round3 laneF report cascor/data measurement")
r3 = (R / "handoff-2fba4397-round3-laneF-reprobe.md").read_text(encoding="utf-8")
for pat in ["0.137.0", "1.0.0", "VALIDATION_ERROR", "detail: null", "\"detail\": null", "lifespan", "capture transport", "0.141.1", "Sentry"]:
    print(f"[{pat}]", [l.strip()[:200] for l in r3.splitlines() if pat in l][:2])
print("--- register L176/L177 (worktree and origin/main)")
reg = (ML / "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md").read_text(encoding="utf-8").splitlines()
print(176, reg[175][:120]); print(177, reg[176][:120])
regm = g("show", "origin/main:notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md").splitlines()
print("main 177", regm[176][:120])
print("--- Work 5 diff stat")
print(g("diff", "--stat=160", "990ef3f9", "2439d049"))
print("--- safe_merge MERGED")
sm = (ML / "util/safe_merge.py").read_text(encoding="utf-8")
print([l.strip()[:140] for l in sm.splitlines() if "MERGED" in l][:4])
ps = (ML / "util/push_signed_commit.py").read_text(encoding="utf-8")
print("push_signed_commit --commit-body-file:", "--commit-body-file" in ps)
print("--- pythons")
print(subprocess.run(["/opt/miniforge3/envs/JuniperCanopy1/bin/python", "--version"], capture_output=True, text=True).stdout.strip())
print(sorted(os.path.basename(p) for p in glob.glob("/opt/miniforge3/envs/JuniperCascor1/lib/python3.14/site-packages/fastapi-*.dist-info") + glob.glob("/opt/miniforge3/envs/JuniperCascor1/lib/python3.14/site-packages/starlette-*.dist-info")))
print("--- SENTRY_SDK_DSN exported in this shell:", "SENTRY_SDK_DSN" in os.environ)
print("--- ml tests fork drift: walk-up + FORCE_LOCAL")
fd = (ML / "tests/test_service_fork_drift.py").read_text(encoding="utf-8").splitlines()
print([(i + 1, l.strip()[:120]) for i, l in enumerate(fd) if "FORCE_LOCAL" in l or "parents" in l or "ECOSYSTEM" in l.upper() and "root" in l.lower()][:10])
print("205-209:", [fd[i][:120] for i in range(204, 209)])
print("289:", fd[288][:140])
