"""Load the archiver with importlib, as the handoff says, and call last_report() on the executor transcript. Read-only."""
import glob
import importlib.util
import inspect
import sys

WT = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream"
spec = importlib.util.spec_from_file_location("archiver", WT + "/util/ad-hoc/2026-09-24_archive_round42_reports.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["archiver"] = mod
spec.loader.exec_module(mod)
print("signature:", inspect.signature(mod.last_report))
path = glob.glob("/home/pcalnon/.claude/projects/*/2fba4397-7d9b-4929-8ca2-375b8168e1c8/subagents/agent-a46e715a6801b98ca.jsonl")[0]
params = list(inspect.signature(mod.last_report).parameters)
try:
    from pathlib import Path
    out = mod.last_report(Path(path))
except TypeError:
    out = mod.last_report(path)
print("type:", type(out).__name__, "len:", len(out) if out else 0)
print("first 200 chars:", (out or "")[:200].replace("\n", " | "))
