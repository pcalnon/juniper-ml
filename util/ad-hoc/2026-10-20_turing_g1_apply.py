"""
Apply turing bring-up G1's edits to the shared files, idempotently: the host-state probe and check.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: ad-hoc — one-off (turing bring-up task G1: util/host_state_probe.bash and util/host_state_check.py)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task G1, the gates of §9.3,
         regression R-G1; §17.3 E-LAND-2 and §18.3 E-LAND-3); util/ad-hoc/2026-10-20_turing_g4_apply.py (the pattern
         this follows)

Why: G1 lands through the GitHub API as whole-file uploads of files every other PR shares: ci.yml,
docs/REFERENCE.md, AGENTS.md and CHANGELOG.md. An upload built from an older base silently reverts whatever main
gained since (E-LAND-2). So the edits live here, keyed on anchors, and are re-applied to a fresh origin/main copy
right before the upload.

The edits:
- ci.yml: the regression step runs tests/test_host_state_probe.py and tests/test_host_state_check.py, right after
  tests/test_ci_host_tooling_macos.py; the host-tooling-macos job's HOST_TOOLING_SUITES gains both, and
  HOST_TOOLING_PATHS gains the two scripts and the conf/hosts/turing/ files the check suite pins.
- tests/test_ci_host_tooling_macos.py: SUITES gains both (that suite gates the job's list).
- docs/REFERENCE.md: both suites in "Running every suite" (and 220 in its count history) and in § Test Suite
  Reference; G4's entry counts eleven host-tooling suites; both scripts in § Utility Script Reference.
- AGENTS.md: the suite count follows ci.yml's regression step, **Last Updated** takes today's UTC date, and the
  Configuration list points at conf/hosts/ (plan §12, "once G1 lands").
- CHANGELOG.md: an [Unreleased] / Added entry directly below G4's entry, not at the top of the list, where
  concurrent PRs insert theirs (E-LAND-3).

Each edit has a marker. When the marker is already present the edit is skipped; otherwise its anchor must occur
exactly once. A re-run on a newer main therefore applies cleanly or stops loudly.

Usage:
    python3 -I util/ad-hoc/2026-10-20_turing_g1_apply.py [--root REPO_ROOT] [--dry-run]

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
G4_GATE = "tests/test_ci_host_tooling_macos.py"
PROBE_LINE = "python3 -m unittest -v tests/test_host_state_probe.py"
CHECK_LINE = "python3 -m unittest -v tests/test_host_state_check.py"
# What util/ad-hoc/2026-10-20_turing_g1_mutation_check.py reported on the landed code.
MUTANT_TALLY = "57 of 57"

CI_SUITES = (
    "          # tests/test_host_state_probe.py: turing bring-up G1. util/host_state_probe.bash captures a macOS\n"
    "          # host's state (argv, rc, stdout, stderr per command) as one JSON object: a missing, failing or\n"
    "          # hung command is recorded (killed at --timeout), sections come in canonical order, ~/.ssh and\n"
    "          # ~/.gnupg get name and permission tests only (mode-000 fixtures), and no credential program\n"
    "          # runs. Stub tools answer from a response table; the real find runs on a temp HOME; /bin/bash.\n"
    f"          {PROBE_LINE}\n"
    "          # tests/test_host_state_check.py: turing bring-up G1, regression R-G1. util/host_state_check.py\n"
    "          # judges those captures against conf/hosts/<host>/expected.yaml: G-ALIAS, G-SIGN, G-SEC, G-TOOLS,\n"
    "          # G-ENV, G-NET and G-MEM, each condition failing or erroring on its own. A VM that cannot fit\n"
    "          # (R-G1, the X2 class) exits 2; G-MEM's verdicts equal util/macvm_ctl.bash status's; the real\n"
    "          # probe feeds the check; the committed turing file agrees with macvm_ctl, hosttools and conda-envs.\n"
    f"          {CHECK_LINE}\n"
)
CI_SUITES_ANCHOR = "          python3 -m unittest -v tests/test_ci_host_tooling_macos.py\n"

CI_ENV_OLD = """\
      # The suites (tests/test_<name>.py) and the other paths whose change re-runs the job;
      # tests/redacted_env.py and this workflow always count. G1's two suites join when it lands.
      HOST_TOOLING_SUITES: >-
        juniper_clone find_encryption_readme_notes macvm_ctl claude_agent_guard
        git_remote_alias_check headless_signing_preflight juniper_repo_ssh_setup home_path_literal_check configure_commit_signing
      HOST_TOOLING_PATHS: >-
        util/juniper_clone.bash util/find_encryption_readme_notes.bash util/macvm_ctl.bash
        util/claude_agent_guard.py util/install_claude_agent_guard.bash util/git_remote_alias_check.py
        util/headless_signing_preflight.bash util/juniper_repo_ssh_setup.bash util/home_path_literal_check.py util/configure_commit_signing.py
        conf/home_path_literal_baseline.json .pre-commit-config.yaml
"""
CI_ENV_NEW = """\
      # The suites (tests/test_<name>.py) and the other paths whose change re-runs the job;
      # tests/redacted_env.py and this workflow always count. G1's check suite pins the conf/hosts/turing/
      # files listed here against each other.
      HOST_TOOLING_SUITES: >-
        juniper_clone find_encryption_readme_notes macvm_ctl claude_agent_guard
        git_remote_alias_check headless_signing_preflight juniper_repo_ssh_setup home_path_literal_check configure_commit_signing
        host_state_probe host_state_check
      HOST_TOOLING_PATHS: >-
        util/juniper_clone.bash util/find_encryption_readme_notes.bash util/macvm_ctl.bash
        util/claude_agent_guard.py util/install_claude_agent_guard.bash util/git_remote_alias_check.py
        util/headless_signing_preflight.bash util/juniper_repo_ssh_setup.bash util/home_path_literal_check.py util/configure_commit_signing.py
        util/host_state_probe.bash util/host_state_check.py
        conf/home_path_literal_baseline.json .pre-commit-config.yaml
        conf/hosts/turing/expected.yaml conf/hosts/turing/hosttools-environment.yml conf/hosts/turing/conda-envs/JuniperCanopy1.yml
        conf/hosts/turing/conda-envs/JuniperCascor1.yml conf/hosts/turing/conda-envs/JuniperData.yml
"""
CI_PIP_OLD = "          # PyYAML: the G5 and G6 cases read .pre-commit-config.yaml and ci.yml.\n"
CI_PIP_NEW = "          # PyYAML: the G5 and G6 cases read .pre-commit-config.yaml and ci.yml; G1's check reads expected.yaml.\n"

G4_SUITES_OLD = """\
# The turing bring-up suites whose scripts run on the host (plan §8). G1's two suites join when it lands.
SUITES = {
    "juniper_clone",
    "find_encryption_readme_notes",
    "macvm_ctl",
    "claude_agent_guard",
    "git_remote_alias_check",
    "headless_signing_preflight",
    "juniper_repo_ssh_setup",
    "home_path_literal_check",
    "configure_commit_signing",  # commit-signing plan K2
}
"""
G4_SUITES_NEW = """\
# The turing bring-up suites whose scripts run on the host (plan §8).
SUITES = {
    "juniper_clone",
    "find_encryption_readme_notes",
    "macvm_ctl",
    "claude_agent_guard",
    "git_remote_alias_check",
    "headless_signing_preflight",
    "juniper_repo_ssh_setup",
    "home_path_literal_check",
    "configure_commit_signing",  # commit-signing plan K2
    "host_state_probe",  # G1
    "host_state_check",  # G1
}
"""

RUN_LIST_ANCHOR = "\npython3 -m unittest -v tests/test_ci_host_tooling_macos.py\nbash scripts/test_resume_file_safety.bash\n"
RUN_LIST_COUNT = "**218** with commit-signing K2's `tests/test_configure_commit_signing.py`"
G4_ENTRY_OLD = "Its suite list must equal the nine host-tooling suites (the eight turing bring-up suites and commit-signing K2's `tests/test_configure_commit_signing.py`)"
G4_ENTRY_NEW = "Its suite list must equal the eleven host-tooling suites (the ten turing bring-up suites, G1's two among them, and commit-signing K2's `tests/test_configure_commit_signing.py`)"
SUITE_REF_ANCHOR = "- `scripts/test.bash` -- Manual end-to-end harness"
UTIL_REF_ANCHOR = "- `util/wait_for_checks.py` -- Waits for a PR's **required** status checks"

AGENTS_CONFIG_ANCHOR = "- `.github/dependabot.yml` -- Automated dependency updates: pip (weekly) and github-actions (weekly)\n"
AGENTS_CONFIG_LINE = "- `conf/hosts/<host>/` -- Per-host target state and records: `expected.yaml`, which `util/host_state_check.py` judges `util/host_state_probe.bash`'s captures against (the host gates; turing bring-up G1), and turing's conda-env specs and `hosttools-environment.yml`\n"

G4_CHANGELOG_TAIL = "    stub `git`. It is wired into `ci.yml` and `docs/REFERENCE.md`.\n\n"


def edits():
    """(path, marker, anchor, replacement). The replacement keeps the anchor and adds the G1 text."""
    probe_suite = (
        "- `tests/test_host_state_probe.py` -- Turing bring-up G1 (`" + PLAN + "`; §8, §9.1). "
        "`util/host_state_probe.bash` must emit one JSON object in the schema its header documents, with every capture's argv, found flag, exit code, timed-out flag, stdout and stderr. "
        "A missing or non-executable program, a failing command and a hung one are recorded and never fatal; a hung one is killed at `--timeout`, and bash's own kill notice stays off stderr. "
        "Sections are collected only when asked for, in canonical order, and a repeated `--tool` is resolved once. "
        "Output round-trips through JSON: quotes, backslashes, tabs, CR, LF and UTF-8 survive, and other control characters are dropped. "
        "Under `~/.ssh` and `~/.gnupg` the probe uses name and permission tests only; the fixtures are mode 000, so a read would fail. "
        "It finds `*.asc` and `*recovery*` files and links to depth 4, and the files directly in `~/.ssh` that group or others may access, public keys, `known_hosts*` and `authorized_keys*` aside. "
        "Each tool records what `command -v` finds and its `~/.local/bin` entry: dangling, non-executable or shadowed. "
        "The alias and signing sections run their repo tools with the root and this checkout. Bad arguments exit 2 before anything runs, and so does an unset `HOME`. "
        "Tripwire `gpg`, `ssh`, `ssh-add`, `gh`, `git` and friends lead `PATH`, and no case may run one. "
        "Stubs answer from a response table keyed by argv, and the real `find` runs on a temp `HOME`, so both BSD and GNU find are pinned. Runs under `/bin/bash`. "
        f"`util/ad-hoc/2026-10-20_turing_g1_mutation_check.py` kills {MUTANT_TALLY} mutants across both G1 suites.\n"
    )
    check_suite = (
        "- `tests/test_host_state_check.py` -- Turing bring-up G1, regression R-G1 (`" + PLAN + "`; §9.3; errata E-D6 and E-G-SIGN). "
        "`util/host_state_check.py` judges the probe's captures against `conf/hosts/<host>/expected.yaml`. An all-green host exits 0 in both modes, and the JSON carries the documented keys. "
        "Each of the 24 conditions of G-ALIAS, G-SIGN, G-SEC, G-TOOLS, G-ENV, G-NET and G-MEM fails or errors on its own and moves only its gate. "
        "There are 55 such cases, among them turing's own captures: SIP's custom configuration, en7 with no carrier, kubectl 1.22 and Docker Desktop running. "
        "A failure exits 1 under `--check` and 0 in the report; an error exits 2 under `--check`, even beside a failure. "
        "expected.yaml is validated before anything runs (26 cases). R-G1, the X2 class, exits 2 on a synthetic file and on the committed turing file: a VM whose memory plus G-MEM's reserve exceeds `hw.memsize`, or one with more vCPUs than cores. A VM that exactly fills the headroom fits. "
        "A probe of another machine, an unmeasurable identity, a document that is not the probe's, and a saved probe without a needed section each exit 2. "
        "G-MEM's verdicts equal `util/macvm_ctl.bash status`'s on the same vm_stat, swap and pgrep output, in ten cases at the rounding edges. "
        "The CLI passes the probe exactly the sections, tools, VM and root its gates read, and a failing, garbled or unlaunchable probe exits 2. The real probe, its tools stubbed, feeds the check end to end. "
        "The committed turing file agrees with `util/macvm_ctl.bash` on the VM and G-MEM thresholds, with `hosttools-environment.yml` on the `~/.local/bin` tools (erratum E-D6), and with `conf/hosts/turing/conda-envs/` on the envs.\n"
    )
    probe_util = (
        "- `util/host_state_probe.bash` -- Collects a macOS host's state, read-only: `bash util/host_state_probe.bash [--json] [--section NAME]... [--tool NAME]... [--root DIR] [--vm NAME] [--timeout SECONDS]`. "
        "Each fact is one command's capture: its argv, exit code, stdout and stderr. "
        "The sections are hardware, memory (G-MEM's inputs, as `util/macvm_ctl.bash` reads them), vm, network, power, security, tools, env, alias (`util/git_remote_alias_check.py --json`) and signing (`util/configure_commit_signing.py --check --json` and `util/headless_signing_preflight.bash`). "
        "It judges nothing. A missing, failing or hung command is recorded, a hung one killed at `--timeout` (default 60 s); the probe exits 0, or 2 on a usage error. "
        "Under `~/.ssh` and `~/.gnupg` it tests names and permission bits only, and it runs no credential probe. "
        "Every program is overridable (`SYSCTL`, `VM_STAT`, `CSRUTIL`, ... `PYTHON`), and commands run with `LC_ALL=C`. The JSON schema is in its header. "
        "Turing bring-up G1. It graduates `util/ad-hoc/2026-10-15_turing_host_state_probe.bash`, whose output is the plan's Appendix A. Tests: `tests/test_host_state_probe.py`.\n"
    )
    check_util = (
        "- `util/host_state_check.py` -- Judges a host against `conf/hosts/<host>/expected.yaml`: `python3 util/host_state_check.py [--host NAME] [--expected FILE] [--probe-json FILE] [--root DIR] [--section GATE]... [--check] [--json]`. "
        "It runs the probe, or reads a saved `--probe-json`. It then evaluates seven of the plan's ten host gates, condition by condition, and names the plan task behind each failure: "
        "G-ALIAS; G-SIGN (erratum E-G-SIGN: `configure_commit_signing.py --check`, the preflight's pinentry, agent-socket and external-cache lines, and the I-SIGN record); G-SEC; "
        "G-TOOLS (erratum E-D6: each listed tool resolves from `~/.local/bin`, and kubectl is within a minor of the cluster); G-ENV; G-NET; and G-MEM (`util/macvm_ctl.bash`'s arithmetic). "
        "G-AUTH, G-PATH and G-AGENT are evaluated elsewhere, and the report names them. "
        "expected.yaml is validated first: a VM that cannot fit the machine is regression R-G1, the X2 class, and exits 2, as does a probe whose hardware does not match its `identity`. "
        "The report exits 0; with `--check` the exit is 0 / 1 / 2, and an unevaluable condition wins. PyYAML is required. `HOST_STATE_PROBE`, `HOST_STATE_BASH` and `JUNIPER_ROOT` are overridable. "
        "Turing's readiness when it landed was 0 of 7. Tests: `tests/test_host_state_check.py`.\n"
    )
    changelog = (
        "- **`util/host_state_probe.bash` and `util/host_state_check.py`, the host gates** (turing bring-up task G1 of\n"
        f"  `{PLAN}`; the gates of §9.3).\n"
        "  - The probe collects a macOS host's state, read-only, as raw command captures in one JSON object. Under\n"
        "    `~/.ssh` and `~/.gnupg` it tests names and permission bits only, and it runs no credential probe. It\n"
        "    graduates `util/ad-hoc/2026-10-15_turing_host_state_probe.bash`.\n"
        "  - The check judges those captures against `conf/hosts/<host>/expected.yaml`, new for turing. It evaluates\n"
        "    G-ALIAS, G-SIGN, G-SEC, G-TOOLS, G-ENV, G-NET and G-MEM condition by condition, and names the plan task\n"
        "    behind each failure. `--check` exits 1 while a gate fails.\n"
        "  - expected.yaml is validated before anything runs. A VM that cannot fit the machine is regression R-G1,\n"
        "    the X2 class (the primer's 44 GB VM on a 16 GiB host), and exits 2.\n"
        "  - Turing's readiness on 2026-10-20 was 0 of 7. Each failure is an open plan task: A1; C1, C2 and C3;\n"
        "    D4; E4; A6 and F2; node mode (F3); and the I-SIGN record (signing plan K10).\n"
        "  - `tests/test_host_state_probe.py` and `tests/test_host_state_check.py` (new) are wired into `ci.yml`,\n"
        "    the advisory `host-tooling-macos` job and `docs/REFERENCE.md` (220 suites).\n"
        f"  - `util/ad-hoc/2026-10-20_turing_g1_mutation_check.py` (new) shows that they kill {MUTANT_TALLY} mutants.\n"
        "\n"
    )
    return [
        (CI, PROBE_LINE, CI_SUITES_ANCHOR, CI_SUITES_ANCHOR + CI_SUITES),
        (CI, "        host_state_probe host_state_check\n", CI_ENV_OLD, CI_ENV_NEW),
        (CI, "G1's check reads expected.yaml", CI_PIP_OLD, CI_PIP_NEW),
        (G4_GATE, '    "host_state_probe",  # G1\n', G4_SUITES_OLD, G4_SUITES_NEW),
        (REFERENCE, f"\n{PROBE_LINE}\n{CHECK_LINE}\n", RUN_LIST_ANCHOR, f"\npython3 -m unittest -v tests/test_ci_host_tooling_macos.py\n{PROBE_LINE}\n{CHECK_LINE}\nbash scripts/test_resume_file_safety.bash\n"),
        (REFERENCE, "**220** with G1's", RUN_LIST_COUNT, RUN_LIST_COUNT + ", **220** with G1's `tests/test_host_state_probe.py` and `tests/test_host_state_check.py`"),
        (REFERENCE, G4_ENTRY_NEW, G4_ENTRY_OLD, G4_ENTRY_NEW),
        (REFERENCE, "- `tests/test_host_state_check.py` --", SUITE_REF_ANCHOR, probe_suite + check_suite + SUITE_REF_ANCHOR),
        (REFERENCE, "- `util/host_state_check.py` --", UTIL_REF_ANCHOR, probe_util + check_util + UTIL_REF_ANCHOR),
        ("AGENTS.md", "- `conf/hosts/<host>/` --", AGENTS_CONFIG_ANCHOR, AGENTS_CONFIG_ANCHOR + AGENTS_CONFIG_LINE),
        # Directly below G4's entry, not at the top of [Unreleased] / ### Added, where concurrent PRs insert theirs.
        ("CHANGELOG.md", "**`util/host_state_probe.bash` and `util/host_state_check.py`, the host gates**", G4_CHANGELOG_TAIL, G4_CHANGELOG_TAIL + changelog),
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

    agents = texts["AGENTS.md"]
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
