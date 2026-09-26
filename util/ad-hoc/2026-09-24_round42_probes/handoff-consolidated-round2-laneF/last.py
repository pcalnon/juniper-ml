import subprocess
from pathlib import Path
D = "/home/pcalnon/Development/python/Juniper/juniper-data"
ML = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream")
def g(repo, *a):
    return subprocess.run(["git", "-C", repo] + list(a), capture_output=True, text=True).stdout
print("d1c66a11 committer date:", g(D, "log", "-1", "--format=%cI %G?", "d1c66a11").strip())
mv = g(D, "show", "origin/main:.github/workflows/main-verify.yml").splitlines()
for i in range(225, 245):
    if i < len(mv):
        print(i + 1, mv[i][:150])
fr = (ML / "reports/2026-09-24_defect-register-round-42/data438-fixforward-round1-fix-report.md").read_text(encoding="utf-8")
for pat in ["access_suppression", "stripe_probe", "test_meta_cross_process_lock", "constants.py", "created_after", "N-9"]:
    print(f"[{pat}]", [l.strip()[:200] for l in fr.splitlines() if pat in l][:2])
sc = (ML / "juniper-service-core/juniper_service_core/security.py").read_text(encoding="utf-8").splitlines()
print("service-core encode sites:", [(i + 1, l.strip()[:90]) for i, l in enumerate(sc) if 'encode("utf-8", "surrogatepass")' in l])
print("service-core main == HEAD for security.py:", g(str(ML), "rev-parse", "HEAD:juniper-service-core/juniper_service_core/security.py").strip()[:8], g(str(ML), "rev-parse", "origin/main:juniper-service-core/juniper_service_core/security.py").strip()[:8])
