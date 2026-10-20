"""
Show that the H2 contract suites kill a mutant for each defect class they claim to pin.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: ad-hoc — investigation (suite strength evidence for the turing bring-up H2 change)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task H2, §11, D11);
         .claude/agents/{macos-host-sme,signing-auth-sme,k8s-node-sme}.md; tests/agent_contract_support.py;
         tests/test_{macos_host_sme,signing_auth_sme,k8s_node_sme}_contract.py;
         util/ad-hoc/2026-10-20_turing_g1_mutation_check.py (the pattern this follows)

Each mutant re-introduces one defect into a COPY of an agent file or of util/claude_agent_guard.py. The
agent defects include a Must-never item dropped or demoted from bold, a guard rule cited for the wrong
item or one the guard does not have, a mutating tool or Bash added, the procedure prescribing a call that
is not a plain GET, the report allowed to overwrite, the OWNER command list dropped, and the k8s agent's
no-Bash rationale or D1 sizing drifted. The guard defects are the other half of "enforced by D11's deny
list": a forbidden call the guard stops denying, a renamed rule, and an over-broad rule that would deny
the agents' own procedure (ssh -G, a plain gh api GET). All three suites then run against that copy, in a
scratch tree that mirrors the files they read (they locate everything relative to their own files).

A mutant is KILLED when the suites fail; the report names the tests that failed. The unmutated control
must pass, or the run is void. Each mutant gets its own scratch tree, so ``--jobs`` mutants run at once.
Nothing in the repository is modified. Not wired into CI: it is evidence, not a gate.

Exit codes:
    0  every mutant was killed and the control passed
    1  a mutant survived, or the control failed
    2  a mutant's anchor text did not occur exactly once (a file changed; update the mutant)

Usage:
    python3 util/ad-hoc/2026-10-20_turing_h2_mutation_check.py [--jobs N] [--only ID[,ID...]]
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MACOS = ".claude/agents/macos-host-sme.md"
SIGNING = ".claude/agents/signing-auth-sme.md"
K8S = ".claude/agents/k8s-node-sme.md"
GUARD = "util/claude_agent_guard.py"
STAGED = (
    MACOS,
    SIGNING,
    K8S,
    GUARD,
    "tests/agent_contract_support.py",
    "tests/redacted_env.py",
    "tests/test_macos_host_sme_contract.py",
    "tests/test_signing_auth_sme_contract.py",
    "tests/test_k8s_node_sme_contract.py",
    "util/host_state_check.py",
    "util/host_state_probe.bash",
    "util/git_remote_alias_check.py",
    "util/configure_commit_signing.py",
    "util/headless_signing_preflight.bash",
    "util/macvm_ctl.bash",
    "conf/hosts/turing/expected.yaml",
    "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md",
    "notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md",
    "notes/JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md",
)
SUITES = ("tests.test_macos_host_sme_contract", "tests.test_signing_auth_sme_contract", "tests.test_k8s_node_sme_contract")
SUITE_TIMEOUT = 600

MACOS_SUDO = "- **`sudo`**, or any other privilege escalation: `su`, `doas`, `osascript` with administrator\n  privileges. (guard: `PRIV-ESCALATION`)\n"
K8S_TARGET = (
    "- **Anything outside its write target.** Write the one `notes/` audit and nothing else. Never write or\n"
    "  change the primer, the inventory, the plan, `expected.yaml`, a report, or any other file. The guard\n"
    "  denies writes to credential, Claude-settings and git-configuration paths; this prompt holds the rest.\n"
    "  (guard: `CRED-PATH-FILE`, `SELF-PROTECT-FILE`, `GIT-SIGNING-FILE`)\n"
)

# (mutant id, file, defect re-introduced, [(anchor, replacement), ...]); each anchor must occur exactly once.
MUTANTS = [
    ("A1", MACOS, "the sudo item is dropped (a passing mention of sudo remains)", [(MACOS_SUDO, "")]),
    ("A2", MACOS, "defaults write cites the wrong rule", [("(guard: `MACOS-DEFAULTS-WRITE`)", "(guard: `PRIV-ESCALATION`)")]),
    ("A3", MACOS, "a cited rule does not exist in the guard", [("(guard: `MACOS-DEFAULTS-WRITE`)", "(guard: `MACOS-SETTINGS-WRITE`)")]),
    ("A4", MACOS, "a mutating tool is added", [("tools: Read, Grep, Glob, Bash, Write\n", "tools: Read, Grep, Glob, Bash, Write, Edit\n")]),
    ("A5", MACOS, "the procedure no longer measures with --json", [("1. **Measure once.** Run `python3 util/host_state_check.py --json`, or", "1. **Measure once.** Run `python3 util/host_state_check.py`, or")]),
    ("A6", MACOS, "a denied call is retried", [("Never retry it under another spelling,", "Retry it under another spelling,")]),
    ("A7", MACOS, "the report may overwrite", [("dated in UTC. Plan §9.1 records integration runs in that directory. If the path already exists,\n  stop and report; never overwrite.", "dated in UTC. Plan §9.1 records integration runs in that directory.")]),
    ("A8", MACOS, "a gate the check leaves to others goes unnamed", [("It leaves G-AUTH, G-PATH and G-AGENT to\nothers", "It leaves G-AUTH and G-PATH to\nothers")]),
    ("A9", MACOS, "the agent re-judges gates", [("You do not re-judge a gate.", "Re-judge each gate yourself.")]),
    ("A10", MACOS, "the credential-probe item is demoted from bold", [("- **Run a credential probe**:", "- Run a credential probe:")]),
    ("S1", SIGNING, "gpg -K is dropped from the items", [("- **`gpg --card-status`**, **`gpg -K`**, or any", "- **`gpg --card-status`**, or any")]),
    ("S2", SIGNING, "the gh api write item cites the wrong rule", [("method-override header. A plain `gh api <path>` is the GET this agent uses. (guard: `GH-API-WRITE`)", "method-override header. A plain `gh api <path>` is the GET this agent uses. (guard: `GH-PR-WRITE`)")]),
    ("S3", SIGNING, "a prescribed gh api call carries a flag", [("- **Rulesets.** `gh api repos/pcalnon/juniper-ml/rulesets`, then", "- **Rulesets.** `gh api -X GET repos/pcalnon/juniper-ml/rulesets`, then")]),
    ("S4", SIGNING, "the OWNER command list leaves the report", [("  - the OWNER command list, as one fenced `bash` block, each command preceded by a comment naming its\n    task and its pass condition.\n", "")]),
    ("S5", SIGNING, "the model drifts from the suite default", [("\nmodel: opus\n", "\nmodel: sonnet\n")]),
    ("S6", SIGNING, "the any-gh-write item is demoted from bold", [("- **Any `gh` write.** The guard denies", "- Any `gh` write. The guard denies")]),
    ("S7", SIGNING, "the procedure reads deploy keys through gh repo deploy-key", [("- **Deploy keys.** `gh api repos/pcalnon/juniper-k8s/keys`.", "- **Deploy keys.** `gh repo deploy-key list -R pcalnon/juniper-k8s`.")]),
    ("K1", K8S, "Bash is added beside WebFetch", [("tools: Read, Grep, Glob, WebFetch, Write\n", "tools: Read, Grep, Glob, WebFetch, Write, Bash\n")]),
    ("K2", K8S, "the no-Bash rationale is gone", [("`Bash` is a prompt-injection-to-exfiltration path:", "`Bash` is a convenience:")]),
    ("K3", K8S, "the write-target item is dropped", [(K8S_TARGET, "")]),
    ("K4", K8S, "D1's sizing drifts to the primer's", [("4 vCPU / 6 GiB / 60 GB", "8 vCPU / 44 GB")]),
    ("K5", K8S, "upstream reads are not limited to kubernetes.io", [("from kubernetes.io only and matched", "from any site and matched")]),
    ("G1", GUARD, "the guard stops denying sudo", [('        if name in PRIV_COMMANDS:\n            self.hit("PRIV-ESCALATION", name)\n', '        if False:\n            self.hit("PRIV-ESCALATION", name)\n')]),
    ("G2", GUARD, "ssh -G counts as a credential probe", [('                    if ch in "GV":\n', '                    if ch in "V":\n')]),
    ("G3", GUARD, "a plain gh api GET is denied", [("    def _check_gh_api(self, words: list) -> None:\n        for word in words:\n", '    def _check_gh_api(self, words: list) -> None:\n        self.hit("GH-API-WRITE", "gh api")\n        for word in words:\n')]),
    ("G4", GUARD, "gh api --method passes", [('GH_API_LONG = ("method", "field", "raw-field", "input")', 'GH_API_LONG = ("field", "raw-field", "input")')]),
    ("G5", GUARD, "writes to git hooks and ~/.gitconfig pass", [('        if ctx.is_signing_config(candidates):\n            hits.append(Hit("GIT-SIGNING-FILE", path))\n', '        if False:\n            hits.append(Hit("GIT-SIGNING-FILE", path))\n')]),
    ("G6", GUARD, "a cited rule is renamed in the guard's table", [('Rule("KEYCHAIN-DUMP", "Bash", "a macOS keychain read', 'Rule("KEYCHAIN-READ", "Bash", "a macOS keychain read')]),
]

# unittest's failure headers: "FAIL: test_x (tests.test_mod.Class.test_x)" (3.11+), optionally with a [subtest].
_FAILURE_RE = re.compile(r"^(?:FAIL|ERROR): (?P<test>\w+) \((?P<qual>[\w.]+)\)", re.MULTILINE)


def stage(tree: Path, rel: str | None = None, text: str | None = None) -> None:
    """Mirror the files the suites read; optionally replace one of them with a mutant."""
    for path in STAGED:
        dest = tree / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO / path, dest)
    if rel is not None and text is not None:
        (tree / rel).write_text(text, encoding="utf-8")


def failed_tests(output: str) -> list[str]:
    names = set()
    for match in _FAILURE_RE.finditer(output):
        parts = match.group("qual").split(".")
        cls = parts[-2] if parts[-1] == match.group("test") else parts[-1]
        names.add(f"{cls}.{match.group('test')}")
    return sorted(names)


def run_suite(rel: str | None, text: str | None) -> tuple[bool, list[str], str]:
    with tempfile.TemporaryDirectory() as raw:
        tree = Path(raw).resolve()
        stage(tree, rel, text)
        proc = subprocess.run([sys.executable, "-m", "unittest", *SUITES], cwd=tree, capture_output=True, text=True, timeout=SUITE_TIMEOUT)
    output = proc.stdout + proc.stderr
    return proc.returncode == 0, failed_tests(output), output


def mutate(original: str, edits: list[tuple[str, str]]) -> str | None:
    mutated = original
    for anchor, replacement in edits:
        if mutated.count(anchor) != 1:
            return None
        mutated = mutated.replace(anchor, replacement)
    return mutated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument("--jobs", type=int, default=min(4, os.cpu_count() or 1), help="mutants to run at once (default: up to 4)")
    parser.add_argument("--only", help="run only these mutant ids, comma-separated")
    args = parser.parse_args()

    chosen = MUTANTS
    if args.only:
        wanted = set(args.only.split(","))
        chosen = [m for m in MUTANTS if m[0] in wanted]
    originals = {rel: (REPO / rel).read_text(encoding="utf-8") for rel in (MACOS, SIGNING, K8S, GUARD)}
    mutated: dict[str, str] = {}
    for mid, rel, _, edits in chosen:
        text = mutate(originals[rel], edits)
        if text is None or text == originals[rel]:
            print(f"ANCHOR {mid}: an anchor does not occur exactly once in {rel}; update the mutant")
            return 2
        mutated[mid] = text

    passed, failures, output = run_suite(None, None)
    if not passed:
        print(f"VOID   control: the suites fail on the unmutated files: {', '.join(failures) or 'see output'}")
        print(output[-4000:])
        return 1
    print(f"OK     control: {len(SUITES)} suites pass on the unmutated agents and guard")

    with ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        results = list(pool.map(lambda mutant: (mutant, run_suite(mutant[1], mutated[mutant[0]])), chosen))

    killed = 0
    for (mid, _, defect, _), (survived, failures, _) in results:
        if survived:
            print(f"SURVIVED {mid:<4} {defect}")
            continue
        killed += 1
        shown = ", ".join(failures[:3]) + (f", +{len(failures) - 3} more" if len(failures) > 3 else "")
        print(f"KILLED   {mid:<4} {defect} -- {len(failures)} failing test(s): {shown}")

    print(f"\n{killed} of {len(chosen)} mutants killed")
    return 0 if killed == len(chosen) else 1


if __name__ == "__main__":
    raise SystemExit(main())
