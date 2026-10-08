# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-08: a probe from round 5 of the canopy E2E ledger's Phase 11 validation.
# Source: a tmpfs scratch directory, r5b.KImIJx/codeql_r4.py
# Written by Lane 11-R5B (adversarial, on round 4's correction pass), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 11;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-08_validator_reports_phase11_round5.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Lane 11-R5B: rebuild round 4's 18 archived probes from the lanes' scratch sources, replay the CodeQL pass's
round-4 edits in memory, and compare both with the committed files at 684d70bc (read with git show)."""
import importlib.util
import subprocess
import sys
from pathlib import Path

WT = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/dreamy-fluttering-kite")
ADHOC = WT / "util" / "ad-hoc"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


arch = load("arch", ADHOC / "2026-10-05_archive_phase11_lane_probes.py")
fix = load("fix", ADHOC / "2026-10-05_phase11_probes_codeql_fixes.py")


def committed(rev, rel):
    return subprocess.run(["git", "-C", str(WT), "show", f"{rev}:{rel}"], capture_output=True, text=True, check=False).stdout


n_same = n_diff = 0
for lane, (dirname, label, files) in arch.LANES_R4.items():
    for name in files:
        src = arch.SCRATCH / dirname / name
        text = src.read_text(encoding="utf-8")
        body, shebang = text, ""
        if body.startswith("#!"):
            shebang, body = body.split("\n", 1)
            shebang += "\n"
        archived = shebang + arch.header(label, src, 4) + body
        suffix = f"r4_{lane}_{name}"
        expect = archived
        edits = fix.EDITS.get(suffix)
        if edits:
            for old, new, _k in edits:
                assert expect.count(old) == 1, (suffix, old)
                expect = expect.replace(old, new)
            what = "; ".join(fix.WHAT[k] for k in dict.fromkeys(k for _o, _n, k in edits))
            expect = expect.replace(fix.VERBATIM, fix.AMENDED.format(what=what))
        rel = f"util/ad-hoc/2026-10-08_phase11_{suffix}"
        got = committed("684d70bc", rel)
        same = got == expect
        n_same += same
        n_diff += not same
        print(f"{'SAME' if same else 'DIFF'} {suffix} edits={len(edits) if edits else 0}")
print(f"{n_same} same, {n_diff} differ; edits={sum(len(v) for k, v in fix.EDITS.items() if k.startswith('r4'))} in {sum(1 for k in fix.EDITS if k.startswith('r4'))} files")
