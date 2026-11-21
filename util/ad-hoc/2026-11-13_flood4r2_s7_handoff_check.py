#!/usr/bin/env python3
"""Re-derive every checkable claim of the flood-4 session-7 handoff from its source, then stamp the file.

Project:     Juniper
Sub-Project: juniper-ml
Application: util/ad-hoc (single-use helper of the Cursor flood-4 disposition arc, session 7)
Author:      Paul Calnon
Version:     0.1.0
License:     MIT License

Why it exists: the Overtoad asked for the handoff to be validated "with particular attention paid to avoiding
hallucinations, while reducing the token use to the extent practicable". A second agent reading the handoff would
cost several hundred thousand tokens and would still be reading prose. This script instead ties each claim to the
thing it is about: GitHub (through `gh`), the trees on disk (existence, sha256, the carriers' own verify commands),
the agents' report files (a needle that must occur) and this session's own transcript (the Overtoad's answers, the
agents' token counts, the limit message). A claim that fails is printed with what was found.

Usage:
    python3 util/ad-hoc/2026-11-13_flood4r2_s7_handoff_check.py            # check only
    python3 util/ad-hoc/2026-11-13_flood4r2_s7_handoff_check.py --finalize # check, then replace the two placeholders

`--finalize` writes the clock's reading into `@@WRITTEN_UTC@@` and `@@CHECKED@@` only when every check passed.
Exit 0 = every check passed; 1 = at least one failed (nothing is stamped).
"""

from __future__ import annotations

import datetime
import hashlib
import json
import pathlib
import re
import subprocess
import sys

O = pathlib.Path(__file__).resolve().parents[2]
JM = O.parents[2]  # .../juniper-ml  (O is .../juniper-ml/.claude/worktrees/<name>)
J = JM.parent  # .../Juniper
WT = JM / ".claude" / "worktrees"
HANDOFF = O / "prompts" / "thread-handoff_automated-prompts" / "HANDOFF_2026-11-13_flood4-session7-data-fix-landed-rulings-30-32-fable-limit-three-agents-dead.md"
TRANSCRIPT = pathlib.Path.home() / ".claude" / "projects" / "-home-pcalnon-Development-python-Juniper-juniper-ml--claude-worktrees-humming-stargazing-papert" / "db29e0f6-305f-478a-a946-07b83a657114.jsonl"
ML_TESTS = WT / "agent-a4cd1de89c2b57ea3"
ML_PROPOSE = WT / "agent-a211deee35ec85ad3"
GUARD = WT / "agent-a5303a15bb4329057"
UNRUN = J / "worktrees" / "juniper-data--test--run-the-unrun-tests--20261112-1815--c68e6b4c"
VF = O / "tmp" / "flood4r2-val" / "d2-unrun-tests-s7"
L1 = O / "tmp" / "flood4r2-val" / "ml-tests-r2-tests-lens-s7"
K2 = O / "tmp" / "flood4r2-val" / "ml-propose-r3b-quick-s7"
S7 = O / "tmp" / "flood4" / "session7"

RESULTS: list[tuple[bool, str, str]] = []
FILL: dict[str, str] = {}


def record(ok: bool, claim: str, found: str = "") -> None:
    RESULTS.append((bool(ok), claim, found))


def run(argv: list[str], cwd: pathlib.Path | None = None) -> tuple[int, str]:
    done = subprocess.run(argv, cwd=str(cwd) if cwd else None, capture_output=True, text=True, check=False)
    return done.returncode, (done.stdout + done.stderr).strip()


def gh_json(args: list[str]):
    code, out = run(["gh", *args])
    if code != 0:
        return None
    try:
        return json.loads(out)
    except ValueError:
        return out


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_github() -> None:
    pulls = [
        ("juniper-data", 537, "MERGED", "3cf8867c", "2026-11-13T02:54:07Z"),
        ("juniper-ml", 2558, "MERGED", "48b66130", "2026-11-13T10:08:14Z"),
        ("juniper-ml", 2559, "MERGED", "ae801a70", None),
        ("juniper-data-client", 260, "MERGED", "b45aafbb", None),
        ("juniper-cascor", 756, "MERGED", "44b60af2", None),
    ]
    for repo, number, state, sha8, merged_at in pulls:
        data = gh_json(["pr", "view", str(number), "--repo", f"pcalnon/{repo}", "--json", "state,mergedAt,mergeCommit,headRefOid"])
        ok = isinstance(data, dict) and data.get("state") == state and (data.get("mergeCommit") or {}).get("oid", "").startswith(sha8)
        if ok and merged_at:
            ok = data.get("mergedAt") == merged_at
        record(ok, f"{repo}#{number} {state} as {sha8}" + (f" at {merged_at}" if merged_at else ""), json.dumps(data)[:160])
        if number == 2558 and isinstance(data, dict):
            record(not data.get("headRefOid", "").startswith("d4dcefbc"), "#2558 merged from a head other than d4dcefbc", data.get("headRefOid", "")[:8])
    main = gh_json(["api", "repos/pcalnon/juniper-ml/commits/main", "--jq", ".sha"])
    archive = gh_json(["pr", "view", "2561", "--repo", "pcalnon/juniper-ml", "--json", "state,mergeCommit,files,autoMergeRequest"])
    files = [f["path"] for f in (archive or {}).get("files", [])] if isinstance(archive, dict) else []
    record(files == ["notes/releases/RELEASE_NOTES_v0.11.5.md"], "juniper-ml#2561 changes one file, the 0.11.5 release notes", str(files))
    merged_sha = ((archive or {}).get("mergeCommit") or {}).get("oid", "") if isinstance(archive, dict) else ""
    state = (archive or {}).get("state") if isinstance(archive, dict) else None
    if state == "MERGED":
        ok = isinstance(main, str) and main == merged_sha
        FILL["@@PR2561@@"] = "had merged as `" + merged_sha[:8] + "`"
    else:
        ok = isinstance(main, str) and main.startswith("48b66130") and state == "OPEN" and bool(archive.get("autoMergeRequest"))
        FILL["@@PR2561@@"] = "was still open"
    FILL["@@MAIN@@"] = str(main)[:8]
    record(ok, "juniper-ml main is 48b66130, or #2561's merge commit on top of it", f"main {str(main)[:8]} / #2561 {state} {merged_sha[:8]}")
    release = gh_json(["release", "view", "v0.11.5", "--repo", "pcalnon/juniper-ml", "--json", "targetCommitish,publishedAt,isDraft"])
    ok = isinstance(release, dict) and release.get("targetCommitish", "").startswith("48b66130") and release.get("publishedAt") == "2026-11-13T10:24:18Z" and not release.get("isDraft")
    record(ok, "the v0.11.5 Release was published at 2026-11-13T10:24:18Z on 48b66130", json.dumps(release)[:200])
    tagged = gh_json(["api", "repos/pcalnon/juniper-ml/commits/v0.11.5", "--jq", ".sha"])
    record(isinstance(tagged, str) and tagged.startswith("48b66130"), "the tag v0.11.5 resolves to commit 48b66130", str(tagged)[:12])
    drafts = gh_json(["pr", "list", "--repo", "pcalnon/juniper-ml", "--state", "open", "--limit", "200", "--json", "isDraft,number"])
    count = len([p for p in drafts or [] if p.get("isDraft")])
    record(count == 33, "33 draft pull requests open on juniper-ml", str(count))
    for number in (2404, 2406, 2494):
        data = gh_json(["pr", "view", str(number), "--repo", "pcalnon/juniper-ml", "--json", "state,isDraft"])
        record(isinstance(data, dict) and data.get("state") == "OPEN", f"juniper-ml#{number} is open", json.dumps(data))
    runs = gh_json(["run", "list", "--repo", "pcalnon/juniper-data", "--commit", "3cf8867cdbcf487483161cf25f4f084884b17d12", "--limit", "20", "--json", "name,conclusion,event"])
    pushes = [r for r in runs or [] if r.get("event") == "push"]
    record(len(pushes) == 3 and all(r.get("conclusion") == "success" for r in pushes), "three post-merge push runs on juniper-data 3cf8867c, all success", json.dumps(pushes)[:200])
    files = gh_json(["pr", "view", "537", "--repo", "pcalnon/juniper-data", "--json", "files"])
    paths = sorted(f["path"] for f in (files or {}).get("files", []))
    expected = sorted(["CHANGELOG.md", "docs/REFERENCE.md", "docs/DEVELOPER_CHEATSHEET.md", "juniper_data/api/security.py", "juniper_data/tests/unit/test_retry_after_rounds_up.py"])
    record(paths == expected, "juniper-data#537 changes exactly the five named files", str(paths))
    newest = gh_json(["pr", "list", "--repo", "pcalnon/juniper-data-client", "--state", "all", "--limit", "1", "--json", "number"])
    record(bool(newest) and newest[0].get("number") == 260, "no pull request has opened on juniper-data-client after #260", json.dumps(newest))
    issue = gh_json(["issue", "view", "536", "--repo", "pcalnon/juniper-data", "--json", "state"])
    record(isinstance(issue, dict) and issue.get("state") == "OPEN", "juniper-data#536 is open", json.dumps(issue))


def check_paths() -> None:
    must_exist = [
        O / "tmp/flood4/session7/STATE_S7.txt",
        O / "tmp/flood4/session7/BRIEF_S7_ADDENDUM.txt",
        O / "tmp/flood4/session7/bash_cmds.py",
        O / "tmp/flood4/session7/pr756_body.md",
        O / "tmp/flood4/session7/pr2558.diff",
        O / "tmp/flood4/session7/land/data-code/freeze/plan.json",
        O / "tmp/flood4/session7/land/data-code/safe_merge.log",
        O / "tmp/flood4/session6/briefs/J_ruling18_guard_word_structure.txt",
        O / "tmp/flood4/session5/BRIEF_R10_PORT.txt",
        O / "tmp/flood4/session5/data-landing/REPORT.txt",
        O / "tmp/flood4/session5/data-landing/PROGRESS.txt",
        O / "tmp/flood4/session5/data-landing/stage3/manifest.json",
        O / "tmp/flood4/session5/data-landing/stage3/s6/state47",
        O / "tmp/flood4/session5/data-landing/stage3/s7",
        O / "util/ad-hoc/2026-11-12_flood4r2_s7_log.py",
        O / "util/ad-hoc/2026-11-12_flood4r2_val_ml-propose-r3b_compare_2558.py",
        O / "util/ad-hoc/2026-11-12_flood4r2_data-landing_second_opinion.py",
        O / "util/safe_merge.py",
        O / "prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_flood4-session5-seven-more-landed-queue-and-decisions-pending.md",
        O / "prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_flood4-session6-four-landed-rulings-19-29-fable-limit-five-agents-dead.md",
        K2 / "REPORT.txt",
        K2 / "findings.json",
        K2 / "text_fixes.json",
        VF / "PROGRESS.txt",
        VF / "findings.json",
        VF / "fixes_input.json",
        VF / "proposed/landing_on_main/CHANGELOG.md",
        VF / "proposed/landing_on_main/docs/REFERENCE.md",
        L1 / "PROGRESS.txt",
        L1 / "mutants/results.json",
        ML_TESTS / "tmp/flood4r2/ml-tests/r2/REPORT.txt",
        ML_TESTS / "tmp/flood4r2/ml-tests/r2/manifest.json",
        ML_PROPOSE / "tmp/flood4r2/ml-propose/r3b/REPORT.txt",
        WT / "agent-a1e6389f6c2d68753/tmp/flood4r2/ml-docs/PROGRESS.txt",
        GUARD / "tmp/flood4-fix/r18-guard/DESIGN.md",
        GUARD / "tmp/flood4-fix/r18-guard/PROGRESS.txt",
        GUARD / "tmp/flood4-fix/r18-guard/probes",
        GUARD / "tmp/flood4-fix/r18-guard/logs",
        UNRUN / "tmp/flood4-fix/d2-unrun-tests/manifest.json",
        UNRUN / "tmp/flood4-fix/d2-unrun-tests/sha256_final.txt",
        J / "worktrees/juniper-data--val--flood4r2-d2-unrun-tests--20261112-2110--3cf8867c",
        J / "worktrees/juniper-data--val--flood4r2-d2-unrun-tests-base--20261112-2110--c68e6b4c",
    ]
    briefs = ["A2_data_stage3_finish_47", "H2_ml_tests_round2_finish", "K2_ml_propose_r3b_quick_check", "I2_ml_docs_finish", "VF_validate_data_unrun_tests", "M_d14_resume_four_rules_shared_table", "N_cascor_pause_check_then_act", "L1_ml_tests_r2_tests_lens", "L2_ml_tests_r2_claims_lens"]
    must_exist += [S7 / "briefs" / f"{name}.txt" for name in briefs]
    missing = [str(p) for p in must_exist if not p.exists()]
    record(not missing, f"{len(must_exist)} cited paths exist", "; ".join(missing)[:400])
    on_disk = sorted(p.name for p in (S7 / "briefs").glob("*.txt"))
    record(on_disk == sorted(f"{name}.txt" for name in briefs), "session 7's briefs directory holds exactly the nine named briefs", str(on_disk))
    must_not_exist = [VF / "text_fixes.json", VF / "REPORT.txt", L1 / "findings.json", L1 / "REPORT.txt", O / "tmp/flood4r2-val/ml-tests-r2-claims-lens-s7"]
    present = [str(p) for p in must_not_exist if p.exists()]
    record(not present, "the files the handoff calls NOT written are absent", "; ".join(present))
    for pattern, expected in (("2026-11-12_flood4r2_val_ml-propose-r3b_*", 13), ("2026-11-12_flood4r2_val_d2-data_*", 9), ("2026-11-12_flood4r2_val_ml-tests-r2-tests_*", 11)):
        found = len(list((O / "util" / "ad-hoc").glob(pattern)))
        record(found == expected, f"{expected} helpers match {pattern}", str(found))
    for rel in ("util/install_claude_agent_guard.bash", "util/remove_stale_worktrees.bash", "prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-11_flood4-seven-landed-validations-pending.md"):
        code, _ = run(["git", "cat-file", "-e", f"origin/main:{rel}"], cwd=O)
        record(code == 0, f"origin/main holds {rel}")
    # The claim is "uncommitted": on disk here and on no commit of main. (This worktree's old HEAD also shows two
    # older handoffs as untracked that main holds; they are not part of the claim.)
    not_on_main = []
    for name in sorted(p.name for p in HANDOFF.parent.glob("HANDOFF_2026-11-1[23]_flood4-session*.md")):
        code, _ = run(["git", "cat-file", "-e", f"origin/main:prompts/thread-handoff_automated-prompts/{name}"], cwd=O)
        if code != 0:
            not_on_main.append(name)
    record(len(not_on_main) == 3 and [n.split("_")[2].split("-")[1] for n in not_on_main] == ["session5", "session6", "session7"], "the handoffs of sessions 5, 6 and 7 are on disk here and not on origin/main", str(not_on_main))
    shared = J / "worktrees"
    for pattern, expected in (("juniper-ml--val--flood4r2-ml-propose-r3b*", 7), ("juniper-ml--flood4r2-ml-tests-r2s7-*", 5), ("juniper-ml--val--flood4r2-ml-tests-r2-tests*", 5), ("juniper-data--val--flood4r2-d2-unrun-tests*", 2)):
        found = len(list(shared.glob(pattern)))
        record(found == expected, f"{expected} entries under Juniper/worktrees match {pattern}", str(found))
    record((shared / "juniper-ml--val--flood4r2-ml-propose-r3b--20261112-1920--26ea0ecb").is_dir(), "one ml-propose validation worktree is session 6's (made 2026-11-12 19:20 local, before session 7 began)")
    agents = ["agent-a4cd1de89c2b57ea3", "agent-a5303a15bb4329057", "agent-a61564fc0ee03e2a2", "agent-afa2d849b67f0bfb0"]
    record(all((WT / name).is_dir() for name in agents), "the four session-7 isolation worktrees named exist")
    code, out = run(["git", "diff", "--cached", "--name-only"], cwd=O)
    record(code == 0 and out == "", "nothing is staged in the orchestrator worktree", out[:120])
    backup = gh_json(["pr", "view", "2548", "--repo", "pcalnon/juniper-ml", "--json", "state"])
    record(isinstance(backup, dict) and backup.get("state") == "OPEN", "juniper-ml#2548 is open", json.dumps(backup))
    code, out = run(["git", "rev-parse", "--short=8", "HEAD"], cwd=O)
    record(out == "734aab58", "the orchestrator worktree's HEAD is 734aab58", out)
    code, out = run(["git", "branch", "--show-current"], cwd=O)
    record(out == "worktree-humming-stargazing-papert", "its branch is worktree-humming-stargazing-papert", out)


def check_trees() -> None:
    code, out = run([sys.executable, "util/ad-hoc/2026-11-12_flood4r2_ml-tests-r2_manifest.py", "--scratch", "tmp/flood4r2/ml-tests/r2", "--verify"], cwd=ML_TESTS)
    record(code == 0 and "59 manifest files" in out and "differing from the recorded sha256: none" in out, "ml-tests carrier: 59 of 59 files match its manifest", out[-200:])
    code, out = run(["sha256sum", "-c", "tmp/flood4-fix/d2-unrun-tests/sha256_final.txt"], cwd=UNRUN)
    record(code == 0 and out.count(": OK") == 14, "unrun-tests carrier: 14 of 14 files at their recorded sha256", out[-200:])
    record(sha256(GUARD / "util/claude_agent_guard.py").startswith("7b5ee677"), "the guard builder's tree holds util/claude_agent_guard.py with sha256 7b5ee677...")
    done = subprocess.run(["git", "show", "origin/main:util/claude_agent_guard.py"], cwd=str(O), capture_output=True, check=False)
    record(hashlib.sha256(done.stdout).hexdigest().startswith("09c5db22"), "main's util/claude_agent_guard.py has sha256 09c5db22...", hashlib.sha256(done.stdout).hexdigest()[:16])
    done = subprocess.run(["git", "ls-tree", "-r", "--name-only", "origin/main", "tests/"], cwd=str(O), capture_output=True, text=True, check=False)
    main_guard_tests = sorted(name for name in done.stdout.split() if name.startswith("tests/test_claude_agent_guard"))
    tree_guard_tests = sorted(f"tests/{p.name}" for p in (GUARD / "tests").glob("test_claude_agent_guard*.py"))
    same = main_guard_tests == tree_guard_tests
    if same:
        for rel in main_guard_tests:
            blob = subprocess.run(["git", "show", f"origin/main:{rel}"], cwd=str(O), capture_output=True, check=False).stdout
            same = same and hashlib.sha256(blob).hexdigest() == sha256(GUARD / rel)
    record(same, "the guard builder's tree holds no new or changed guard test file", f"main {len(main_guard_tests)} / tree {len(tree_guard_tests)}")
    plan = json.loads((S7 / "land/data-code/freeze/plan.json").read_text())
    record("c68e6b4c" in json.dumps(plan), "juniper-data#537 was frozen on c68e6b4c", json.dumps(plan)[:120])
    log = (S7 / "land/data-code/safe_merge.log").read_text()
    record("MERGED #537 at b00a7ac1 via squash" in log, "safe_merge's log has its MERGED line for #537")


def check_needles() -> None:
    needles = [
        (O / "tmp/flood4/session5/data-landing/REPORT.txt", ["47 passed", "31 fail", "48 of 48 killed"]),
        (K2 / "REPORT.txt", ["SHIP-WITH-FIXES", "F.5 AT THE FREEZE, IF #2558 HAS MERGED", "exits 1", "If #2558's merged head is not d4dcefbc, re-run compare_2558.py before using text fix 5"]),
        (ML_TESTS / "tmp/flood4r2/ml-tests/r2/REPORT.txt", ["THE LANDING COMMAND", "--ml-propose-pr", "--landing-date", "5. THE macOS JOB: WHAT TO READ IN THE PULL REQUEST'S LOG BEFORE MERGING", "02:38:10Z", "02:41:42Z"]),
        (VF / "PROGRESS.txt", ["text fixes: 23 drafted", "RUNNING in V1", "RUNNING in V0"]),
        (L1 / "PROGRESS.txt", ["MUTATION RUN END: 56 mutants"]),
        (GUARD / "tmp/flood4-fix/r18-guard/PROGRESS.txt", ["[N1]", "[N7]", "NEXT: DESIGN.md, then the guard"]),
        (O / "prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-12_flood4-session6-four-landed-rulings-19-29-fable-limit-five-agents-dead.md", ["## A side effect of juniper-cascor#756", "## Traps (new this session)", "9. Landing steps", "`b6b843b6` or later","close #2494 and the docs drafts, and the triage's NONE group"]),
        (S7 / "STATE_S7.txt", ['"2-3 Fable agents (Recommended)"', '"Four rules + shared table"', '"Read as 0 (Recommended)"', '"Fix it + document"', "merge approval granted"]),
        (O / "tmp/flood4/session6/STATE_S6.txt", ["(tests/test_service_fork_drift.py, the defect register, docs/REFERENCE.md's fork-drift entry)"]),
        (S7 / "BRIEF_S7_ADDENDUM.txt", ["DBUS_SESSION_BUS_ADDRESS=unix:path=/nonexistent/no-session-bus", "tmp/flood4/session4/BRIEF_S4_ADDENDUM.txt"]),
    ]
    for path, wanted in needles:
        text = path.read_text(encoding="utf-8", errors="replace")
        missing = [needle for needle in wanted if needle not in text]
        record(not missing, f"{path.name} ({path.parent.name}) carries {len(wanted)} quoted fact(s)", "; ".join(missing)[:300])
    fixes = json.loads((K2 / "text_fixes.json").read_text())
    record(len(fixes) == 6 and all("pr_body.txt" in item.get("file", "") for item in fixes), "the ml-propose check's text_fixes.json holds six fixes, all for pr_body.txt", str(len(fixes)))
    findings = json.loads((VF / "findings.json").read_text())
    majors = [f for f in findings.get("findings", []) if f.get("severity") == "MAJOR"]
    record(findings.get("status") == "in-progress" and len(findings.get("findings", [])) == 1 and len(majors) == 1 and "0.4.8" in json.dumps(majors), "the unrun-tests validator's findings.json is in progress with one MAJOR about the stale 0.4.8 stamp", findings.get("status", ""))
    rows = json.loads((L1 / "mutants/results.json").read_text())
    rows = rows if isinstance(rows, list) else rows.get("results") or rows.get("mutants") or []
    tally: dict[str, int] = {}
    for row in rows:
        key = str(row.get("result") or row.get("outcome") or row.get("status"))
        tally[key] = tally.get(key, 0) + 1
    record(tally == {"killed": 44, "test fails (sound)": 7, "PASSES": 3, "SURVIVED": 2}, "the tests lens's 56 mutants: 44 killed, 7 'test fails (sound)', 3 'PASSES', 2 'SURVIVED'", str(tally))
    manifest = json.loads((ML_TESTS / "tmp/flood4r2/ml-tests/r2/manifest.json").read_text())
    record(len(manifest.get("carried", [])) == 18 and len(manifest.get("files", [])) == 59, "ml-tests manifest: 18 carried drafts, 59 files", f"{len(manifest.get('carried', []))} / {len(manifest.get('files', []))}")
    record(any("main-verify.yml" in json.dumps(q) and "six of the fifteen" in json.dumps(q) for q in manifest.get("open_questions", [])), "ml-tests manifest asks about main-verify.yml holding six of the fifteen suites")
    unrun = json.loads((UNRUN / "tmp/flood4-fix/d2-unrun-tests/manifest.json").read_text())
    first = json.dumps((unrun.get("open_questions") or [""])[0])
    record(all(tag in first for tag in ("(A)", "(B)", "(C)", "(D)", "(E)", "41 benchmarks")), "the unrun-tests manifest's first open question holds the benchmark options A-E")


def check_transcript() -> None:
    text = TRANSCRIPT.read_text(encoding="utf-8", errors="replace")
    wanted = [
        r'=\"2-3 Fable agents (Recommended)\"', r'=\"Four rules + shared table\"', r'=\"Read as 0 (Recommended)\"', r'=\"Fix it + document\"',
        "merge approval granted", "commit and PR the handoff. i'll take care of the merge.",
        "<subagent_tokens>477640</subagent_tokens>", "<subagent_tokens>664263</subagent_tokens>", "<subagent_tokens>642144</subagent_tokens>",
        "You've hit your Fable limit · resets Nov 18, 9pm (America/Chicago)",
        "a5303a15bb4329057", "ab098e2e0ce5c1cfc", "afa2d849b67f0bfb0",
        "PINNED to that merge commit", "a push to main while that run is in flight cancels it",
        "the guard + register PR follows the cut", "the arc's next handoff will be the newest HANDOFF_2026-11-13_r-obs-sc-2-follow-ups-* file",
    ]
    missing = [needle for needle in wanted if needle not in text]
    record(not missing, f"this session's transcript carries {len(wanted)} quoted Overtoad answers, agent facts and peer statements", "; ".join(missing)[:300])


def check_document() -> None:
    text = HANDOFF.read_text(encoding="utf-8")
    goal = re.search(r"## Goal\n\n```text\n(.*?)\n```", text, re.S)
    words = len(goal.group(1).split()) if goal else 0
    record(bool(goal) and words <= 1300, "the Goal block is at most about 1,200 words", str(words))
    record(not re.search(r"\]\([^)]*\)", text), "the handoff holds no markdown link (nothing for the link checker to break)")
    record(not re.search(r"(?<![\w.~)\]}])/(?:var/)?tmp(?:/|\b)", text), "the handoff holds no system temp-directory path literal")
    record(max(len(line) for line in text.split("\n")) <= 512, "no line is longer than 512 characters", str(max(len(line) for line in text.split("\n"))))
    for token in ("N1 ", "sudo"):
        record(token not in text, f"the handoff does not spell out the unruled guard findings ({token.strip()!r} absent)")
    record(len(text.split()) > 0, f"whole document: {len(text.split())} words, {len(text.encode('utf-8'))} bytes")


def main(argv: list[str]) -> int:
    for step in (check_github, check_paths, check_trees, check_needles, check_transcript, check_document):
        try:
            step()
        except Exception as error:  # a check that cannot run is a failed check, named
            record(False, f"{step.__name__} could not finish", repr(error)[:300])
    failed = [row for row in RESULTS if not row[0]]
    for ok, claim, found in RESULTS:
        print(("PASS  " if ok else "FAIL  ") + claim + ("" if ok or not found else f"   [found: {found}]"))
    print(f"{len(RESULTS) - len(failed)} of {len(RESULTS)} checks passed")
    if failed:
        return 1
    if "--finalize" in argv:
        now = datetime.datetime.now(datetime.timezone.utc)
        text = HANDOFF.read_text(encoding="utf-8")
        if "@@" not in text:
            print("already stamped")
            return 0
        text = text.replace("@@WRITTEN_UTC@@", now.strftime("%Y-%m-%d %H:%MZ")).replace("@@CHECKED@@", now.strftime("%H:%MZ"))
        FILL["@@NCHECKS@@"] = str(len(RESULTS))
        for placeholder, value in FILL.items():
            text = text.replace(placeholder, value)
        if "@@" in text:
            print("refusing: a placeholder is left")
            return 1
        HANDOFF.write_text(text, encoding="utf-8")
        print("stamped " + now.strftime("%Y-%m-%d %H:%MZ") + "; sha256 " + sha256(HANDOFF))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
