"""
Re-derive, per juniper-cascor release tag, the facts N1 round 2's "How far back" text states.

For every v* tag of juniper-cascor (read from a cascor worktree given on the command line) this
reads the tagged src/api/lifecycle/state_machine.py and manager.py and reports:
  - the states mark_completed accepts, measured by EXECUTING that tag's own state machine
    (START, PAUSE, mark_completed; then START from the result, and RESUME from the result);
  - each mark_completed call site in manager.py and whether its result is used;
  - whether the start precheck refuses STARTED ("Training already in progress") and PAUSED
    ("Cannot start training while paused");
  - whether the tag has the interrupt checkpoint (_check_for_interrupt) and any
    _pause_event.wait() call anywhere under src/api;
  - whether monitored_fit exists;
and, for the two commits the text cites (4710cc1, cascor#584; f4453fa, cascor#244), their
subject lines and the first tag that contains each.

Usage: python3 -I <this> <cascor-worktree> <scratch-dir>
The tagged state_machine.py blobs are written to <scratch-dir>/sm_blobs/ and imported from there.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-09
Status: ad-hoc — investigation
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: flood-4 round 2, N1 (juniper-cascor paused-fit wedge) claims-lens validation;
         juniper-ml notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11
"""

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

SM_PATH = "src/api/lifecycle/state_machine.py"
MGR_PATH = "src/api/lifecycle/manager.py"


def git(repo: Path, *args: str) -> str:
    out = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    return out.stdout


def git_ok(repo: Path, *args: str) -> bool:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False).returncode == 0


def probe_fsm(blob_path: Path, tag: str) -> str:
    spec = importlib.util.spec_from_file_location(f"sm_{tag.replace('.', '_')}", blob_path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    status = mod.TrainingStatus
    cmd = mod.Command

    def fresh_paused():
        sm = mod.TrainingStateMachine()
        sm.handle_command(cmd.START)
        sm.handle_command(cmd.PAUSE)
        return sm

    sm = fresh_paused()
    accepted_paused = sm.mark_completed()
    after_mc = sm.status.name
    sm_start = fresh_paused()
    sm_start.mark_completed()
    start_ok = sm_start.handle_command(cmd.START)
    after_start = sm_start.status.name
    sm_resume = fresh_paused()
    sm_resume.mark_completed()
    resume_ok = sm_resume.handle_command(cmd.RESUME)
    after_resume = sm_resume.status.name
    sm_started = mod.TrainingStateMachine()
    sm_started.handle_command(cmd.START)
    accepted_started = sm_started.mark_completed()
    _ = status
    return f"mark_completed(STARTED)={accepted_started} mark_completed(PAUSED)={accepted_paused} -> {after_mc}; " f"then START={start_ok} -> {after_start}; or RESUME={resume_ok} -> {after_resume}"


def call_sites(mgr: str) -> list:
    sites = []
    for no, line in enumerate(mgr.splitlines(), 1):
        if "mark_completed(" in line and "def mark_completed" not in line:
            stripped = line.strip()
            used = not re.match(r"^(self\.state_machine|sm|self\._state_machine)\.mark_completed\(\)\s*(#.*)?$", stripped)
            sites.append(f"{no}: {stripped[:110]} [result {'USED' if used else 'ignored'}]")
    return sites


def main() -> int:
    repo = Path(sys.argv[1])
    scratch = Path(sys.argv[2])
    blob_dir = scratch / "sm_blobs"
    blob_dir.mkdir(parents=True, exist_ok=True)
    tags = [t for t in git(repo, "tag", "-l", "v*", "--sort=v:refname").split() if t]
    print("TAGS:", " ".join(tags))
    for sha in ("4710cc1", "f4453fa"):
        subj = git(repo, "log", "-1", "--format=%H %ad %s", "--date=short", sha).strip()
        first = [t for t in tags if git_ok(repo, "merge-base", "--is-ancestor", sha, t)]
        print(f"COMMIT {sha}: {subj}")
        print(f"  first tag containing it: {first[0] if first else 'none'}; contained in: {' '.join(first)}")
    for tag in tags:
        print(f"===== {tag} ({git(repo, 'log', '-1', '--format=%h %ad', '--date=short', tag).strip()})")
        sm_src = git(repo, "show", f"{tag}:{SM_PATH}")
        mgr = git(repo, "show", f"{tag}:{MGR_PATH}")
        if not sm_src or not mgr:
            print("  lifecycle files missing")
            continue
        blob = blob_dir / f"sm_{tag.replace('.', '_')}.py"
        blob.write_text(sm_src)
        try:
            print("  FSM:", probe_fsm(blob, tag))
        except Exception as exc:  # report, keep going
            print("  FSM probe error:", repr(exc))
        for site in call_sites(mgr):
            print("  call", site)
        print("  refuses STARTED on start ('Training already in progress'):", "Training already in progress" in mgr)
        print("  refuses PAUSED on start ('Cannot start training while paused'):", "Cannot start training while paused" in mgr)
        print("  has _check_for_interrupt:", "def _check_for_interrupt" in mgr)
        api_tree = git(repo, "grep", "-n", "_pause_event.wait", tag, "--", "src/api")
        print("  _pause_event.wait() sites under src/api:", len([ln for ln in api_tree.splitlines() if ln.strip()]))
        print("  has monitored_fit:", "monitored_fit" in mgr)
        mc_body = re.search(r"def mark_completed\(self\)[^\n]*\n(.*?)\n    def ", sm_src, re.S)
        if mc_body:
            cond = [ln.strip() for ln in mc_body.group(1).splitlines() if ln.strip().startswith("if ")]
            print("  mark_completed condition:", cond[:1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
