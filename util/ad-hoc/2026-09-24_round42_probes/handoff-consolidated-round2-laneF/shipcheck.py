import subprocess, pathlib, hashlib
REPO = pathlib.Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream")
def run(*c):
    return subprocess.run(c, cwd=REPO, capture_output=True, text=True)
files = """prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md
prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md
reports/2026-09-24_defect-register-round-42/data438-fixforward-pr-draft.md
reports/2026-09-24_defect-register-round-42/data438-fixforward-round1-fix-report.md
reports/2026-09-24_defect-register-round-42/data438-fixforward-round1-laneA-reprobe.md
reports/2026-09-24_defect-register-round-42/data438-fixforward-round1-laneB-refute.md
reports/2026-09-24_defect-register-round-42/handoff-2fba4397-round1-laneF-reprobe.md
reports/2026-09-24_defect-register-round-42/handoff-2fba4397-round1-laneO-amputation.md
reports/2026-09-24_defect-register-round-42/handoff-2fba4397-round1-laneP-fresh-session.md
reports/2026-09-24_defect-register-round-42/handoff-2fba4397-round2-laneF-reprobe.md
reports/2026-09-24_defect-register-round-42/handoff-2fba4397-round2-laneO-amputation.md
reports/2026-09-24_defect-register-round-42/handoff-2fba4397-round2-laneP-fresh-session.md
reports/2026-09-24_defect-register-round-42/handoff-2fba4397-round3-laneF-reprobe.md
reports/2026-09-24_defect-register-round-42/handoff-2fba4397-round3-laneP-fresh-session.md
reports/2026-09-24_defect-register-round-42/handoff-consolidated-round1-laneF-reprobe.md
reports/2026-09-24_defect-register-round-42/handoff-consolidated-round1-laneO-amputation.md
reports/2026-09-24_defect-register-round-42/handoff-consolidated-round1-laneP-fresh-session.md
reports/2026-09-24_defect-register-round-42/owner-ruling-key-leaks-verbatim.md
util/ad-hoc/2026-09-24_archive_round42_reports.py
util/ad-hoc/2026-09-24_data438_round2_stall_probe_throughout.py
util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py
util/ad-hoc/2026-09-24_open_round42_consolidated_handoff_pr.py""".split()
for f in files:
    h = run("git", "rev-parse", "--verify", "--quiet", f"HEAD:{f}").stdout.strip()[:8] or "-"
    m = run("git", "rev-parse", "--verify", "--quiet", f"origin/main:{f}").stdout.strip()[:8] or "-"
    w = run("git", "hash-object", f).stdout.strip()[:8]
    print(f"{h:9} {m:9} {w:9} {f}")
print("--- status")
print(run("git", "status", "--porcelain=v1", "--untracked-files=all").stdout)
print("--- diff extractor")
print(run("git", "diff", "HEAD", "--", "util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py").stdout)
print("--- diff archiver (stat)")
print(run("git", "diff", "--stat", "HEAD", "--", "util/ad-hoc/2026-09-24_archive_round42_reports.py").stdout)
print("--- verdict lines")
rep = REPO / "reports/2026-09-24_defect-register-round-42"
for p in sorted(rep.glob("handoff-2fba4397-round*-lane*.md")):
    lines = p.read_text(encoding="utf-8").splitlines()
    v = next((l for l in lines if "VERDICT" in l.upper() or "Verdict" in l), "")
    print(p.name, "|", v[:160])
