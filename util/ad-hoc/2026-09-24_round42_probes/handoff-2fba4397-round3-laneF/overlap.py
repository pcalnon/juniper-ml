"""Overlap between #2097's files, #2089's files, and this worktree's uncommitted files. Read-only."""
from pathlib import Path

D = Path(__file__).parent
a = set((D / "pr2097_files.txt").read_text().split())
b = set((D / "pr2089_files.txt").read_text().split())
uncommitted = {
    "util/ad-hoc/2026-09-24_archive_round42_reports.py",
    "util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py",
    "util/ad-hoc/2026-09-24_data438_round2_stall_probe_throughout.py",
    "reports/2026-09-24_defect-register-round-42/owner-ruling-key-leaks-verbatim.md",
    "reports/2026-09-24_defect-register-round-42/data438-fixforward-round1-laneA-reprobe.md",
    "reports/2026-09-24_defect-register-round-42/data438-fixforward-round1-laneB-refute.md",
    "reports/2026-09-24_defect-register-round-42/data438-fixforward-pr-draft.md",
    "prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md",
}
uncommitted |= {f"reports/2026-09-24_defect-register-round-42/handoff-2fba4397-round{r}-lane{l}.md" for r in (1, 2) for l in ("F-reprobe", "O-amputation", "P-fresh-session")}
print("#2097 files:", len(a), "| #2089 files:", len(b))
print("#2097 ∩ #2089:", sorted(a & b))
print("#2097 ∩ uncommitted:", sorted(a & uncommitted))
print("#2097 util/ad-hoc entries:", sorted(p for p in a if p.startswith("util/ad-hoc/") and "round42_probes/" not in p))
