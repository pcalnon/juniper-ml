#!/usr/bin/env python3
"""
Write the round-2 "ml-docs" carrier's manifest.json from the session-6 decisions, today's re-proofs and the checks.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-14
Status: ad-hoc -- one-off (Cursor flood-4 round-2 docs-carrier finish, session 8)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md (round 2);
         util/ad-hoc/2026-11-12_flood4r2_ml-docs_manifest.py (the session-6 builder: its CARRIED, MAIN_DEFECT_4
         and CLAIMS data are loaded from it, never copied by hand; it was written but never run)

The per-draft decisions and the claims table are the session-6 builder's data. This script adds what was
established in session 8: each draft's head and title as ``gh pr view`` showed them today, the corrections made
while finishing (``SESSION8_FIXES``), the status of every claim (re-proved by a probe re-run, re-proved by a
cited window that ``2026-11-14_flood4r2_ml-docs_cite_check.py`` checked on today's main, or kept with its
subject unchanged), every carrier file's status and sha256, and the checks with their logs. Run it from the
carrier's worktree root.

Usage: 2026-11-14_flood4r2_ml-docs_manifest.py --scratch <dir> --base <sha> --checks <json>
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SESSION6 = REPO / "util" / "ad-hoc" / "2026-11-12_flood4r2_ml-docs_manifest.py"
MODIFIED = [
    ".claude/agents/fleet-supervisor.md",
    "CHANGELOG.md",
    "docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md",
    "docs/DOCUMENTATION_OVERVIEW.md",
    "docs/QUICK_START.md",
    "docs/REFERENCE.md",
]
HELPER_PATTERNS = ("2026-11-12_flood4r2_ml-docs_*.py", "2026-11-14_flood4r2_ml-docs_*.py")
PROBES = ("claims/launcher_probe.json", "claims/guard_probe.json", "claims/predict_merge_probe.json", "claims/symbol_loss_probe.json")
SESSION8_FIXES = {
    "all": [
        "Rebuilt on today's main: the session-6 bytes (verified against probe commit 01cb8495, plus two later launcher lines) were made stamp-free on 26ea0ecb and three-way merged onto main (0 conflicts); every stamp is set by rule from main's value, and the CHANGELOG entry sits in the top [Unreleased] '### Added', after the entries already there.",
        "Session 8 fix-up (I4, 2026-11-15): the session-8 validator's 31 text fixes (findings F1-F8) applied to the carrier tree and to content/, which the re-derive reads, plus the provenance of #2484's paragraph in the commit body and the CHANGELOG entry; re-derived on 7ce8d365 and re-proved there (PROGRESS.txt, REPORT.txt).",
    ],
    2479: [
        "Kept the two wording changes the session-6 builder made after its last probe commit: the entry table says `max` and `opus` 'as of juniper-ml#2554' (it said 'as shipped on 2026-11-13'), and the `--effort auto` pitfall row cites the owner's ruling of 2026-11-08 and juniper-ml#2554; both checked against scripts/claude_interactive.bash:95-116 and scripts/wake_the_claude.bash:255-262.",
    ],
    2494: [
        "Session 8 fix-up (I4): the inherited-GIT_DIR sentences (the scratch bullet, the pitfall row, the CHANGELOG entry, the PR body, this row and claim 50) name both screens: the docs screen is recorded as skip too, so a .md deletion run that is DAMAGED-FIX-FIRST in a plain environment reads MERGE-CLEAN (the session-8 validator's finding F1; its probe re-run on 7ce8d365, s8b/scratch_probe.json).",
    ],
    2484: [
        "Session 8 fix-up (I4): the provenance is stated in this row, the PR body, the commit body and the CHANGELOG entry: the paragraph and the tests/test_predict_merge.py hunk come from draft #2480's commit 406e7d80, which this branch is stacked on, and the tests carrier takes the test file's first test only (the session-8 validator's finding F2).",
    ],
}


DIRECT_REPROOFS = {
    "./claudey is the repo-root symlink": "`ls -l claudey` -> scripts/claude_interactive.bash; scripts/claude_interactive.bash:66 sets WAKE_THE_CLAUDE_SCRIPT and :306 runs it (read on a949d504)",
    "the JSON is written, then the summary printed": "util/ad-hoc/2026-10-05_recurrence_equities_laneA3_checks.py:169, :175, :181, :235 set report fields; :237-238 write the JSON; :270 returns 0 (read on a949d504)",
}
# Session 8 fix-up (I4): the session-8 validator's rows for manifest.json (tmp/flood4r2-val/ml-docs-s8/text_fixes.json,
# findings F1 and F2), the same provenance in #2484's reason, and claim 50, which named only the symbol screen (F1).
S8B_MANIFEST_OLD_1 = "so under an inherited GIT_DIR the symbol screen is recorded as `skip` (probe)."
S8B_MANIFEST_NEW_1 = "so under an inherited GIT_DIR each screen with a file to read (the symbol screen, and the docs screen on a .md delta) is recorded as `skip` (probe)."
S8B_MANIFEST_OLD_2 = "docs/REFERENCE.md only: its paragraph saying that predict_merge's scratch copies a shallow checkout's `shallow` file"
S8B_MANIFEST_NEW_2 = "docs/REFERENCE.md only: the paragraph its diff shows (written in draft #2480's commit 406e7d80, which its branch is stacked on) saying that predict_merge's scratch copies a shallow checkout's `shallow` file"
S8B_MANIFEST_OLD_3 = "tests/test_predict_merge_shallow_worktree.py, its tests/test_predict_merge.py hunk, its .github/workflows/ci.yml line and its 'Running every suite' line in docs/REFERENCE.md: test and registration content, the tests carrier's."
S8B_MANIFEST_NEW_3 = "tests/test_predict_merge_shallow_worktree.py, its .github/workflows/ci.yml line and its 'Running every suite' line in docs/REFERENCE.md: test and registration content, left to the tests carrier (it takes the file's first test only). Its tests/test_predict_merge.py hunk is not its own: it comes from draft #2480's commit 406e7d80 and #2474's pre-squash commit 21a9dabc."
S8B_REASON_OLD = "Docs-only take: one true sentence for its paragraph, with the consequence corrected to main's behaviour; its tests are the tests carrier's."
S8B_REASON_NEW = "Docs-only take: one true sentence for the paragraph its diff shows (written in draft #2480's commit 406e7d80), with the consequence corrected to main's behaviour; its test file is left to the tests carrier, which takes the first test only."
S8B_CLAIM_OLD = "under an inherited GIT_DIR the symbol screen exits 2 on refs/fleet/base and is recorded as skip"
S8B_CLAIM_NEW = "under an inherited GIT_DIR each screen with a file to read (the symbol screen, the docs screen on a .md delta) exits 2 on refs/fleet/base and is recorded as skip"
S8B_EVIDENCE_OLD = "MERGE-CLEAN with ast_symbol_screen.status=skip under GIT_DIR, with and without GIT_WORK_TREE)"
S8B_EVIDENCE_NEW = "MERGE-CLEAN with ast_symbol_screen.status=skip under GIT_DIR, with and without GIT_WORK_TREE); s8b/scratch_probe.json gitdir_md_inherited_GIT_DIR (the session-8 validator's probe, re-run on 7ce8d365: a .md deletion run, DAMAGED-FIX-FIRST in a plain environment, MERGE-CLEAN with docs_additions_only.status=skip)"
TEXT_CORRECTIONS = {
    # Counted on main a949d504 (and on 26ea0ecb): `grep -c -x -F '### Operator pitfalls' docs/REFERENCE.md` is 32.
    "docs/REFERENCE.md already has 40 headings with that exact text": "docs/REFERENCE.md already has 32 headings with that exact text",
    S8B_MANIFEST_OLD_1: S8B_MANIFEST_NEW_1,
    S8B_MANIFEST_OLD_2: S8B_MANIFEST_NEW_2,
    S8B_MANIFEST_OLD_3: S8B_MANIFEST_NEW_3,
    S8B_REASON_OLD: S8B_REASON_NEW,
}
CLAIM_CORRECTIONS = {
    S8B_CLAIM_OLD: S8B_CLAIM_NEW,
    S8B_EVIDENCE_OLD: S8B_EVIDENCE_NEW,
}


def corrected(value):
    """Apply TEXT_CORRECTIONS to every string inside ``value``."""
    if isinstance(value, str):
        for old, new in TEXT_CORRECTIONS.items():
            value = value.replace(old, new)
        return value
    if isinstance(value, list):
        return [corrected(item) for item in value]
    return value


def corrected_claim(claim: dict) -> dict:
    """Apply CLAIM_CORRECTIONS to a claim's text and evidence."""
    fixed = dict(claim)
    for key in ("claim", "evidence"):
        for old, new in CLAIM_CORRECTIONS.items():
            fixed[key] = fixed[key].replace(old, new)
    return fixed


def load_session6():
    spec = importlib.util.spec_from_file_location("ml_docs_session6_manifest", SESSION6)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cited_windows(evidence: str) -> list[tuple[str, int, int]]:
    """(path, start, end) for every ``path:a[-b]`` in the evidence, ``, :c[-d]`` continuations included."""
    windows = []
    for part in evidence.split(";"):
        match = re.search(r"([A-Za-z0-9_./-]+\.(?:py|bash|yml)):(\d+)(?:-(\d+))?", part)
        if not match:
            continue
        path = match.group(1)
        windows.append((path, int(match.group(2)), int(match.group(3) or match.group(2))))
        for extra in re.finditer(r",\s*:(\d+)(?:-(\d+))?", part[match.end():]):
            windows.append((path, int(extra.group(1)), int(extra.group(2) or extra.group(1))))
    return windows


def claim_status(claim: dict, facts: list[dict]) -> dict:
    evidence = claim["evidence"]
    probes = [probe for probe in PROBES if probe in evidence]
    covered = []
    for path, start, end in cited_windows(evidence):
        for fact in facts:
            if fact.get("ok") and fact.get("path") == path and "lines" in fact:
                low, high = (int(x) for x in fact["lines"].split("-"))
                if start <= high and low <= end:
                    covered.append(fact["fact"])
    direct = [text for key, text in DIRECT_REPROOFS.items() if claim["claim"].startswith(key)]
    if probes:
        status = "re-proved: probe re-run on today's main, same result"
    elif covered:
        status = "re-proved: cited window checked on today's main"
    elif direct:
        status = "re-proved: read on today's main"
    else:
        status = "kept from session 6: subject byte-identical 26ea0ecb..a949d504"
    return {**claim, "status": status, "probes_rerun": probes, "cite_facts": sorted(set(covered)), "read_today": direct}


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--base", required=True)
    parser.add_argument("--checks", required=True, type=Path)
    args = parser.parse_args(argv)
    session6 = load_session6()
    heads = json.loads((args.scratch / "draft_heads_today.json").read_text(encoding="utf-8"))
    facts = json.loads((args.scratch / "claims" / "cite_check.json").read_text(encoding="utf-8"))["rows"]
    carried = []
    for item in session6.CARRIED:
        number = str(item["pr"])
        carried.append(
            {
                "pr": item["pr"],
                "head_sha": heads["heads"][number],
                "title": heads["titles"][number],
                "taken": corrected(item["taken"]),
                "fixes": corrected(item["fixes"]) + SESSION8_FIXES.get(item["pr"], []),
                "dropped": corrected(item["dropped"]),
                "outcome": item["outcome"],
                "reason": corrected(item["reason"]),
            }
        )
    applied = json.dumps(carried)
    for new in TEXT_CORRECTIONS.values():
        if new not in applied:
            raise SystemExit(f"a text correction did not apply: {new!r}")
    carried.append(
        {
            "pr": None,
            "item": "main defect 4 (the round-2 triage's name): stale fleet-triage documentation on main",
            "head_sha": None,
            "title": None,
            "taken": [f"{row['where']}: was {row['was']}; now {row['is']}" for row in session6.MAIN_DEFECT_4],
            "fixes": [f"evidence: {row['evidence']}" for row in session6.MAIN_DEFECT_4],
            "dropped": [],
            "outcome": "fixed-in-main-text",
            "reason": "Each stale sentence found by its text on main and checked against util/fleet_triage/predict_merge.py as main holds it; every one was still wrong, and each is corrected in place.",
        }
    )
    files = [{"path": path, "status": "modified", "sha256": sha256(REPO / path)} for path in MODIFIED]
    for pattern in HELPER_PATTERNS:
        for path in sorted((REPO / "util" / "ad-hoc").glob(pattern)):
            files.append({"path": str(path.relative_to(REPO)), "status": "added", "sha256": sha256(path)})
    checks = json.loads(args.checks.read_text(encoding="utf-8"))
    claims = [claim_status(corrected_claim(claim), facts) for claim in session6.CLAIMS]
    for new in CLAIM_CORRECTIONS.values():
        if new not in json.dumps(claims):
            raise SystemExit(f"a claim correction did not apply: {new!r}")
    tally: dict[str, int] = {}
    for claim in claims:
        key = claim["status"].split(":")[0] + (" (probe)" if claim["probes_rerun"] else (" (cite)" if claim["cite_facts"] else ""))
        tally[key] = tally.get(key, 0) + 1
    manifest = {
        "repo": "pcalnon/juniper-ml",
        "carrier": "ml-docs",
        "base_sha": args.base,
        "worktree": str(REPO),
        "files": files,
        "carried": carried,
        "session8_fixes_all": SESSION8_FIXES["all"],
        "checks": checks["checks"],
        "mutations": [],
        "mutations_note": "No test file is carried (a docs carrier); nothing to mutate.",
        "claims": claims,
        "claims_tally": tally,
        "open_questions": checks["open_questions"],
        "status": checks.get("status", "final"),
    }
    (args.scratch / "manifest.json").write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    print(f"manifest: {len(files)} files, {len(carried)} carried rows, {len(claims)} claims {tally}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
