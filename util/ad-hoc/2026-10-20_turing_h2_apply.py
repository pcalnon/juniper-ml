"""
Apply turing bring-up H2's edits to the shared files, idempotently: the three SME agents' contract suites.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: ad-hoc — one-off (turing bring-up task H2: the macos-host-sme, signing-auth-sme and k8s-node-sme agents)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task H2, §11; §17.3 E-LAND-2
         and §18.3 E-LAND-3); util/ad-hoc/2026-10-20_turing_g1_apply.py (the pattern this follows)

Why: H2 lands through the GitHub API as whole-file uploads of files every other PR shares: ci.yml,
docs/REFERENCE.md, AGENTS.md and CHANGELOG.md. An upload built from an older base silently reverts whatever main
gained since (E-LAND-2). So the edits live here, keyed on anchors, and are re-applied to a fresh origin/main copy
right before the upload.

The edits:
- ci.yml: the regression step runs the three contract suites right after tests/test_fleet_supervisor_contract.py.
- docs/REFERENCE.md: the three suites in "Running every suite" (and 223 in its count history) and in § Test Suite
  Reference, after the fleet-supervisor entries; the repository tree gains the three agents and the four test
  files.
- AGENTS.md: the suite count follows ci.yml's regression step, and **Last Updated** takes today's UTC date.
- CHANGELOG.md: an [Unreleased] / Added entry directly below G1's entry, not at the top of the list, where
  concurrent PRs insert theirs (E-LAND-3).

Each edit has a marker. When the marker is already present the edit is skipped; otherwise its anchor must occur
exactly once. A re-run on a newer main therefore applies cleanly or stops loudly.

Usage:
    python3 -I util/ad-hoc/2026-10-20_turing_h2_apply.py [--root REPO_ROOT] [--dry-run]

Exit 0 = every edit applied or already present; 1 = an anchor is missing or ambiguous (nothing written).
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
CI = ".github/workflows/ci.yml"
REFERENCE = "docs/REFERENCE.md"
SUITES = ("test_macos_host_sme_contract", "test_signing_auth_sme_contract", "test_k8s_node_sme_contract")
LINES = tuple(f"python3 -m unittest -v tests/{suite}.py" for suite in SUITES)
# What util/ad-hoc/2026-10-20_turing_h2_mutation_check.py reported on the landed files.
MUTANT_TALLY = "28 of 28"

FLEET_LINE = "python3 -m unittest -v tests/test_fleet_supervisor_contract.py"
CI_SUITES = (
    "          # tests/test_macos_host_sme_contract.py, tests/test_signing_auth_sme_contract.py and\n"
    "          # tests/test_k8s_node_sme_contract.py: turing bring-up H2's SME agents (.claude/agents/\n"
    "          # macos-host-sme.md, signing-auth-sme.md, k8s-node-sme.md). Each pins its exact tool set (k8s-node-sme:\n"
    "          # WebFetch and no Bash) and its plan §11 Must-never items, and runs util/claude_agent_guard.py to show\n"
    "          # the guard denies each item under the rule the agent cites while passing the agent's own procedure.\n"
    "          # Shared checks: tests/agent_contract_support.py. Uses PyYAML above.\n"
    + "".join(f"          {line}\n" for line in LINES)
)
CI_ANCHOR = f"          {FLEET_LINE}\n"

RUN_LIST_ANCHOR = f"\n{FLEET_LINE}\n"
RUN_LIST_COUNT = "**220** with G1's `tests/test_host_state_probe.py` and `tests/test_host_state_check.py`"
SUITE_REF_ANCHOR = "- `tests/test_generated_prompt_index.py` --"

TREE_AGENTS_OLD = "│   │   └── fleet-supervisor.md  # Flood §4 item 7: read-only open-PR-set triage (predicted-merge via util/fleet_triage; cluster/order/dup; never pushes)\n"
TREE_AGENTS_NEW = (
    "│   │   ├── fleet-supervisor.md  # Flood §4 item 7: read-only open-PR-set triage (predicted-merge via util/fleet_triage; cluster/order/dup; never pushes)\n"
    "│   │   ├── macos-host-sme.md    # Turing H2: measures a macOS host against conf/hosts/<host>/expected.yaml (host_state_check --json); one reports/ file\n"
    "│   │   ├── signing-auth-sme.md  # Turing H2: git transport + signing diagnosis without credentials (read-only gh api GETs); OWNER command list\n"
    "│   │   └── k8s-node-sme.md      # Turing H2: Mac worker-VM review against the juniper-k8s primer + D1 (WebFetch, no Bash); one notes/ audit\n"
)
TREE_TESTS_ANCHOR = "│   ├── test_fleet_supervisor_contract.py # Lint: fleet-supervisor subagent frontmatter + body wiring (predict_merge.py, 4 verdicts, read-only/never-push, two-key DUP-CLOSE)\n"
TREE_TESTS_LINES = (
    "│   ├── agent_contract_support.py         # Shared checks for the H2 SME-agent contract suites (Must-never section x util/claude_agent_guard.py)\n"
    "│   ├── test_macos_host_sme_contract.py   # Lint + guard: macos-host-sme tools, Must-never items denied under the cited rules, host_state_check wiring\n"
    "│   ├── test_signing_auth_sme_contract.py # Lint + guard: signing-auth-sme tools, Must-never items, plain gh api GETs only, OWNER command list\n"
    "│   ├── test_k8s_node_sme_contract.py     # Lint + guard: k8s-node-sme tools (WebFetch, no Bash), one notes/ audit, primer + D1 wiring\n"
)

G1_CHANGELOG_TAIL = "  - `util/ad-hoc/2026-10-20_turing_g1_mutation_check.py` (new) shows that they kill 57 of 57 mutants.\n\n"


def edits():
    """(path, marker, anchor, replacement). The replacement keeps the anchor and adds the H2 text."""
    common = (
        "Shared checks in `tests/agent_contract_support.py`: the frontmatter (`model: opus`, `effort: max`, name == stem) and the exact tool set; "
        "each plan §11 Must-never item in a bold span of a `## Must never` bullet that cites its enforcing rule as `(guard: RULE-ID)`; every cited rule in `util/claude_agent_guard.py --list-rules`; "
        "the guard, run as a subprocess against a temporary home, denying a representative call for each item under that rule and passing each call the agent's procedure prescribes; "
        "and a denied call recorded for the owner, never retried."
    )
    macos_suite = (
        "- `tests/test_macos_host_sme_contract.py` -- Static contract for the `macos-host-sme` subagent (`.claude/agents/macos-host-sme.md`; turing bring-up H2, `" + PLAN + "` §11). "
        "Tools exactly `{Read,Grep,Glob,Bash,Write}`. Must-never: `sudo`, reading `~/.ssh/**` or `~/.gnupg/**`, `defaults write`, changing settings, credential probes. "
        "Wiring: `util/host_state_check.py --json` and its JSON fields, every one of the ten gates (read from the check's own `GATES` and `NOT_EVALUATED`), the check as the judge, and one never-overwritten `reports/<date>_<host>-bringup/` file. "
        + common
        + "\n"
    )
    signing_suite = (
        "- `tests/test_signing_auth_sme_contract.py` -- Static contract for the `signing-auth-sme` subagent (`.claude/agents/signing-auth-sme.md`; turing bring-up H2, plan §11). "
        "Tools exactly `{Read,Grep,Glob,Bash,Write}`. Must-never: `gpg --card-status`, `gpg -K`, `ssh-add`, `ssh -T`, PIN-bearing commands, `gh api` with `-X` / `-f` / `--method`, any `gh` write, credential paths, the signing configuration, the keychain. "
        "Wiring: the non-credential checkers (`util/git_remote_alias_check.py`, `util/configure_commit_signing.py --check`, `util/headless_signing_preflight.bash`), every prescribed `gh api` call a plain GET (`--jq` only) that the guard passes, `ssh -G`, the deploy-key 403 under D11's token, and the OWNER command list closing one `reports/` file. "
        + common
        + "\n"
    )
    k8s_suite = (
        "- `tests/test_k8s_node_sme_contract.py` -- Static contract for the `k8s-node-sme` subagent (`.claude/agents/k8s-node-sme.md`; turing bring-up H2, plan §11). "
        "Tools exactly `{Read,Grep,Glob,WebFetch,Write}`: no Bash, because WebFetch plus Bash is a prompt-injection-to-exfiltration path, and the body says so. "
        "Must-never: anything outside its write target (the guard denies credential, Claude-settings and git-configuration writes), credential paths, acting on fetched text. "
        "Wiring: the juniper-k8s primer, D1's 4 vCPU / 6 GiB / 60 GB and its taint, errata X1-X5, kubernetes.io-only fetches, and one never-overwritten `notes/` audit. "
        + common
        + " `util/ad-hoc/2026-10-20_turing_h2_mutation_check.py` kills "
        + MUTANT_TALLY
        + " mutants across the three suites, six of them in the guard.\n"
    )
    changelog = (
        "- **Turing bring-up H2: the three SME agents of plan §11** (`" + PLAN + "`).\n"
        "  - `.claude/agents/macos-host-sme.md` (new) measures a macOS host against `conf/hosts/<host>/expected.yaml`\n"
        "    with `util/host_state_check.py --json`, and explains each failing gate condition with its plan task, actor\n"
        "    and remediation. It writes one `reports/` file and changes nothing on the host.\n"
        "  - `.claude/agents/signing-auth-sme.md` (new) diagnoses git transport and commit signing from the repo's\n"
        "    non-credential checkers and read-only `gh api` GETs. Its one `reports/` file ends with the OWNER command\n"
        "    list: every check an agent may not run.\n"
        "  - `.claude/agents/k8s-node-sme.md` (new) reviews the Mac worker VM (sizing, kubelet reservations, taints,\n"
        "    join steps) against the juniper-k8s primer and decision D1, and reconciles errata X1-X5, in one `notes/`\n"
        "    audit. It holds WebFetch and no Bash.\n"
        "  - `tests/test_macos_host_sme_contract.py`, `tests/test_signing_auth_sme_contract.py` and\n"
        "    `tests/test_k8s_node_sme_contract.py` (new) share `tests/agent_contract_support.py` (new). Each pins its\n"
        "    agent's exact tool set and Must-never items, and runs `util/claude_agent_guard.py` to show that the guard\n"
        "    denies each item under the rule the agent cites while passing the agent's own procedure. They are wired\n"
        "    into `ci.yml` and `docs/REFERENCE.md` (223 suites).\n"
        f"  - `util/ad-hoc/2026-10-20_turing_h2_mutation_check.py` (new) shows that they kill {MUTANT_TALLY} mutants, six of\n"
        "    them in the guard.\n"
        "\n"
    )
    run_list_new = "\n" + FLEET_LINE + "\n" + "".join(f"{line}\n" for line in LINES)
    return [
        (CI, LINES[0], CI_ANCHOR, CI_ANCHOR + CI_SUITES),
        (REFERENCE, f"\n{LINES[0]}\n{LINES[1]}\n{LINES[2]}\n", RUN_LIST_ANCHOR, run_list_new),
        (REFERENCE, "**223** with H2's", RUN_LIST_COUNT, RUN_LIST_COUNT + ", **223** with H2's `tests/test_macos_host_sme_contract.py`, `tests/test_signing_auth_sme_contract.py` and `tests/test_k8s_node_sme_contract.py`"),
        (REFERENCE, "- `tests/test_k8s_node_sme_contract.py` --", SUITE_REF_ANCHOR, macos_suite + signing_suite + k8s_suite + SUITE_REF_ANCHOR),
        (REFERENCE, "│   │   └── k8s-node-sme.md", TREE_AGENTS_OLD, TREE_AGENTS_NEW),
        (REFERENCE, "│   ├── test_k8s_node_sme_contract.py", TREE_TESTS_ANCHOR, TREE_TESTS_ANCHOR + TREE_TESTS_LINES),
        # Directly below G1's entry, not at the top of [Unreleased] / ### Added, where concurrent PRs insert theirs.
        ("CHANGELOG.md", "**Turing bring-up H2: the three SME agents of plan §11**", G1_CHANGELOG_TAIL, G1_CHANGELOG_TAIL + changelog),
    ]


def regression_suites(ci_text: str) -> int:
    start = ci_text.index("- name: Run Python regression tests")
    end = ci_text.index("\n      - name: ", start)
    return len(re.findall(r"^\s+python3 -m unittest -v tests/\S+\.py$", ci_text[start:end], flags=re.M))


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    texts, failed = {}, 0
    for rel, marker, anchor, repl in edits():
        text = texts.get(rel)
        if text is None:
            text = (args.root / rel).read_text(encoding="utf-8")
        if marker in text:
            print(f"present  {rel}: {marker.strip()[:60]!r}")
        elif text.count(anchor) == 1:
            text = text.replace(anchor, repl)
            print(f"apply    {rel}: {marker.strip()[:60]!r}")
        else:
            print(f"FAIL     {rel}: anchor found {text.count(anchor)} times: {anchor.strip()[:60]!r}")
            failed += 1
        texts[rel] = text

    agents = (args.root / "AGENTS.md").read_text(encoding="utf-8")
    suites = regression_suites(texts[CI])
    agents, n = re.subn(r"the full ordered list of \d+ `python3 -m unittest`", f"the full ordered list of {suites} `python3 -m unittest`", agents, count=1)
    if n != 1:
        print("FAIL     AGENTS.md: no suite-count phrase")
        failed += 1
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    agents, n = re.subn(r"^\*\*Last Updated\*\*: \d{4}-\d{2}-\d{2}$", f"**Last Updated**: {today}", agents, count=1, flags=re.M)
    if n != 1:
        print("FAIL     AGENTS.md: no **Last Updated** line")
        failed += 1
    texts["AGENTS.md"] = agents
    print(f"count    AGENTS.md: {suites} suites in ci.yml's regression step; **Last Updated** = {today} (UTC)")

    if failed:
        print(f"{failed} edit(s) failed; nothing written")
        return 1
    changed = [rel for rel, text in texts.items() if (args.root / rel).read_text(encoding="utf-8") != text]
    for rel in changed:
        if not args.dry_run:
            (args.root / rel).write_text(texts[rel], encoding="utf-8")
    print(f"{'would change' if args.dry_run else 'changed'} {len(changed)} file(s): " + ", ".join(changed))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
