"""
Show that tests/test_macvm_ctl.py kills a mutant for each defect class it claims to pin.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-17
Status: ad-hoc — investigation (suite strength evidence for the turing bring-up F5a change)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task F5a;
         gate G-MEM in §9.3; regression R-F5); util/macvm_ctl.bash; tests/test_macvm_ctl.py

Each mutant re-introduces one defect into a COPY of util/macvm_ctl.bash: no swap check, an
off-by-one threshold, Docker ignored, a start on a failed gate, startvm without --type headless,
and so on. The suite then runs against that copy in a scratch tree that mirrors the repo layout
(the suite locates the script relative to its own file). A mutant is KILLED when the suite fails.
The unmutated control must pass, or the run is void.

The suite drives only stubs, and its PATH shadow fails any bare-name tool call, so no mutant can
reach a real VBoxManage. Nothing in the repository is modified. Not wired into CI: it is evidence,
not a gate.

Exit codes: 0 every mutant killed and the control passed; 1 a mutant survived or the control
failed; 2 a mutant's anchor text was not found (the script changed; update the mutant).

Usage:
    python3 util/ad-hoc/2026-10-17_turing_f5a_mutation_check.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPT = "util/macvm_ctl.bash"
SUITE = "tests/test_macvm_ctl.py"

# (mutant id, defect re-introduced, [(anchor, replacement), ...]); each anchor must occur exactly once.
MUTANTS = [
    ("M1", "swap check removed (any swap use passes)", [('        if [[ "$SWAP_USED_MIB" -le "$MAX_SWAP_MIB" ]]; then', "        if true; then")]),
    ("M2", "memory threshold off by one (> for >=)", [('if [[ "$AVAIL_MIB" -ge "$NEED_MIB" ]]; then', 'if [[ "$AVAIL_MIB" -gt "$NEED_MIB" ]]; then')]),
    ("M3", "swap threshold off by one (< for <=)", [('if [[ "$SWAP_USED_MIB" -le "$MAX_SWAP_MIB" ]]; then', 'if [[ "$SWAP_USED_MIB" -lt "$MAX_SWAP_MIB" ]]; then')]),
    ("M4", "a running Docker Desktop ignored", [("            0) DOCKER_HITS=\"${DOCKER_HITS:+$DOCKER_HITS, }${name} (pid ${pids//$'\\n'/ })\" ;;", "            0) ;;")]),
    ("M5", "start goes ahead when G-MEM fails", [('    if [[ "$GATE_UNKNOWN" -gt 0 || "$GATE_FAILED" -gt 0 ]]; then', "    if false; then")]),
    ("M6", "startvm without --type headless", [('    if "$VBOXMANAGE" startvm "$VM" --type headless; then', '    if "$VBOXMANAGE" startvm "$VM"; then')]),
    ("M7", "page size hard-coded to 4096 (header ignored)", [('    if [[ ! "$MEM_PAGE_SIZE" =~ $size_re ]]; then', '    MEM_PAGE_SIZE=4096\n    if [[ ! "$MEM_PAGE_SIZE" =~ $size_re ]]; then')]),
    ("M8", "speculative pages not counted as free", [("    FREE_PAGES=$((10#$MEM_FREE_PAGES + 10#$MEM_SPEC_PAGES))", "    FREE_PAGES=$((10#$MEM_FREE_PAGES))")]),
    ("M9", "inactive pages not counted", [("    AVAIL_MIB=$(((FREE_PAGES + 10#$MEM_INACTIVE_PAGES) * MEM_PAGE_SIZE / 1048576))", "    AVAIL_MIB=$((FREE_PAGES * MEM_PAGE_SIZE / 1048576))")]),
    ("M10", "swap in G read as M", [("        G) SWAP_USED_MIB=$(((n * 1024 + scale - 1) / scale)) ;;", "        G) SWAP_USED_MIB=$(((n + scale - 1) / scale)) ;;")]),
    ("M11", "fractional swap rounds down (in the VM's favour)", [("        M) SWAP_USED_MIB=$(((n + scale - 1) / scale)) ;;", "        M) SWAP_USED_MIB=$((n / scale)) ;;")]),
    ("M12", "an unmeasurable input fails open", [('    if [[ "$GATE_UNKNOWN" -gt 0 || "$GATE_FAILED" -gt 0 ]]; then', '    if [[ "$GATE_FAILED" -gt 0 ]]; then')]),
    ("M13", "an already-running VM still has the gate evaluated", [('    if [[ "$VM_STATE" == "running" ]]; then', '    if [[ "$VM_STATE" == "running" ]] && evaluate_gate >/dev/null; then')]),
    ("M14", "--dry-run still starts the VM", [('    if [[ "$DRY_RUN" -eq 1 ]]; then\n        echo "DRY-RUN: G-MEM passed;', '    if false; then\n        echo "DRY-RUN: G-MEM passed;')]),
    ("M15", "stop powers off on timeout without --force", [('    if [[ "$FORCE" -eq 1 ]]; then\n        echo "VM ${VM} is still', '    if true; then\n        echo "VM ${VM} is still')]),
    ("M16", "stop --force never powers off", [('    if [[ "$FORCE" -eq 1 ]]; then\n        echo "VM ${VM} is still', '    if false; then\n        echo "VM ${VM} is still')]),
    ("M17", "stop reports success without waiting for poweroff", [('    wait_until_off "$TIMEOUT" || rc=$?\n    case "$rc" in\n        0)\n            echo "VM ${VM} stopped', '    rc=0\n    case "$rc" in\n        0)\n            echo "VM ${VM} stopped')]),
    ("M18", "the stop wait does not sleep between polls", [('        sleep "$POLL_INTERVAL"', "        :")]),
    ("M19", "status exits 1 when G-MEM fails", [('    [[ "$env_error" -eq 0 ]] || exit 2\n    exit 0', '    [[ "$env_error" -eq 0 ]] || exit 2\n    [[ "$GATE_FAILED" -eq 0 ]] || exit 1\n    exit 0')]),
    ("M20", "status exits 0 for an unregistered VM", [('        env_error=1\n        echo "VM ${VM}: $(vm_problem_summary)"', '        echo "VM ${VM}: $(vm_problem_summary)"')]),
    ("M21", "the VM's configured memory ignored", [('    if [[ "$VM_CONF_MIB" =~ $mib_re ]] && [[ $((10#$VM_CONF_MIB)) -gt "$VM_MIB" ]]; then', "    if false; then")]),
    ("M22", "the vmnetd launchd helper counts as Docker running", [('    for name in com.docker.backend "Docker Desktop" Docker; do', '    for name in com.docker.backend "Docker Desktop" Docker com.docker.vmnetd; do')]),
]


def stage(tmp: Path) -> None:
    """Mirror the files the suite needs: the suite, the env helper and the script."""
    for rel in (SCRIPT, SUITE, "tests/redacted_env.py"):
        dest = tmp / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / rel, dest)


def suite_passes(tmp: Path) -> bool:
    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "-q", SUITE],
        cwd=tmp,
        capture_output=True,
        text=True,
        timeout=900,
    )
    return proc.returncode == 0


def main() -> int:
    original = (REPO / SCRIPT).read_text(encoding="utf-8")
    for mid, _, edits in MUTANTS:
        for anchor, _ in edits:
            if original.count(anchor) != 1:
                print(f"ANCHOR {mid}: {anchor!r} occurs {original.count(anchor)} times in {SCRIPT} (need exactly 1)")
                return 2
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        stage(tmp)
        if not suite_passes(tmp):
            print(f"VOID   control: {SUITE} fails on the unmutated {SCRIPT}")
            return 1
        print(f"OK     control: {SUITE} passes on the unmutated {SCRIPT}")

        survivors = 0
        for mid, defect, edits in MUTANTS:
            mutated = original
            for anchor, replacement in edits:
                mutated = mutated.replace(anchor, replacement)
            (tmp / SCRIPT).write_text(mutated, encoding="utf-8")
            try:
                killed = not suite_passes(tmp)
            finally:
                (tmp / SCRIPT).write_text(original, encoding="utf-8")
            survivors += 0 if killed else 1
            print(f"{'KILLED' if killed else 'SURVIVED':8} {mid:4} {defect}")

        total = len(MUTANTS)
        print(f"\n{total - survivors} of {total} mutants killed")
        return 0 if survivors == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
