"""
Apply turing bring-up G1's edits to the shared files, idempotently: the host-state probe and checker.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: ad-hoc — one-off (turing bring-up task G1: util/host_state_probe.bash and util/host_state_check.py)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task G1, the gates of §9.3,
         regression R-G1; §17.3 E-LAND-2; §18.3 E-LAND-3); tests/test_host_state_probe.py; tests/test_host_state_check.py;
         util/ad-hoc/2026-10-20_turing_g4_apply.py (the pattern this follows)

Why: G1 lands through the GitHub API as whole-file uploads of files every other PR shares: ci.yml,
docs/REFERENCE.md, AGENTS.md and CHANGELOG.md. An upload built from an older base silently reverts whatever
main gained since (E-LAND-2). So the edits live here, keyed on anchors, and are re-applied to a fresh
origin/main copy right before the upload.

The edits:
- ci.yml's regression step runs the two suites, directly after G2's suite: not at the end of the step, where
  concurrent suite-adding PRs append (E-LAND-3).
- ci.yml's host-tooling-macos job (G4) gains them in HOST_TOOLING_SUITES, and the probe, the checker and the
  two conf files they read in HOST_TOOLING_PATHS; tests/test_ci_host_tooling_macos.py's SUITES follows.
- docs/REFERENCE.md: the suites in "Running every suite" (and 220 in its intro's count history) and in § Test
  Suite Reference, after G2's; the scripts in § Utility Script Reference, after G2's; G4's suite entry counts
  eleven host-tooling suites.
- AGENTS.md: the suite count follows ci.yml's regression step, and **Last Updated** takes today's UTC date.
- CHANGELOG.md: an [Unreleased] / Added entry, directly below G4's entry.
- util/ad-hoc/2026-10-15_turing_host_state_probe.bash: its header records that G1 superseded it.

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
G4_TEST = "tests/test_ci_host_tooling_macos.py"
AD_HOC_PROBE = "util/ad-hoc/2026-10-15_turing_host_state_probe.bash"
PROBE_SUITE = "python3 -m unittest -v tests/test_host_state_probe.py"
CHECK_SUITE = "python3 -m unittest -v tests/test_host_state_check.py"
G2_SUITE = "python3 -m unittest -v tests/test_git_remote_alias_check.py"
RUN_LIST_COUNTS = "**218** with commit-signing K2's `tests/test_configure_commit_signing.py`"
G4_CHANGELOG_TAIL = "  - `tests/test_ci_host_tooling_macos.py` (new) gates the job's shape and runs the detection shell under a\n    stub `git`. It is wired into `ci.yml` and `docs/REFERENCE.md`.\n\n"


def edits():
    """(path, marker, anchor, replacement). The replacement keeps the anchor and adds the G1 text."""
    ci_suites = (
        "          # tests/test_host_state_probe.py: turing bring-up G1. util/host_state_probe.bash collects the host\n"
        "          # state read-only, as raw captures (exit code, stdout, stderr) in a schema-1 JSON document. Every\n"
        "          # tool is a stub that refuses an unknown argv; output round-trips byte for byte (backslash, quote,\n"
        "          # tab, CR, UTF-8; C0 controls dropped). A hung command is killed at --timeout and a missing one is\n"
        "          # exit 127, under bash 3.2 too. Names and modes only: a canary in every key file is never printed.\n"
        f"          {PROBE_SUITE}\n"
        "          # tests/test_host_state_check.py: turing bring-up G1 / R-G1 (the host gates of plan §9.3).\n"
        "          # util/host_state_check.py evaluates the probe against conf/hosts/<host>/expected.yaml: G-ALIAS,\n"
        "          # G-SIGN, G-SEC, G-TOOLS, G-ENV, G-NET and G-MEM, one condition at a time. R-G1: a VM larger than\n"
        "          # hw.memsize minus the reserve fails vm-fits (the X2 class). G-MEM prints util/macvm_ctl.bash's\n"
        "          # verdicts and text on the same fixtures. The committed expected.yaml is pinned to macvm_ctl's\n"
        "          # defaults, hosttools-environment.yml and the conda-env specs.\n"
        f"          {CHECK_SUITE}\n"
    )
    probe_entry = (
        "- `tests/test_host_state_probe.py` -- Turing bring-up G1 (`" + PLAN + "`; §8, §9.1). "
        "`util/host_state_probe.bash` collects the host state read-only and judges nothing, so the suite pins the collection contract. "
        "Every documented capture appears in its section, in order, with its documented argv. "
        "Each command's stdout and stderr round-trip through the JSON byte for byte (backslashes, quotes, tabs, CRs, `&`, UTF-8); C0 controls are dropped and trailing newlines removed. "
        "A missing program is recorded as exit 127, under bash 3.2 too, and a hung one is killed at `--timeout`; neither is an error. "
        "An absent sibling tool, parent `AGENTS.md`, `juniper-ml` checkout or `~/.ssh` is a skipped capture that names it. "
        "`--section` filters and keeps the canonical order, `--tool` adds each lookup once, `--vm` reaches `showvminfo`, and a bad argument exits 2 and runs nothing. "
        "Names and modes only. `key-material-names` lists the `*.asc` and `*recovery*` names under `~/.ssh` and `~/.gnupg`. `ssh-loose-files` lists the files under `~/.ssh` open to group or others, `*.pub` and `known_hosts*` aside. "
        "A canary inside every key-shaped file never reaches the output, and no credential command runs. "
        "Every tool is a stub reached through its variable, and every case runs under `/bin/bash` (`HOST_STATE_TEST_BASH` overrides it).\n"
    )
    check_entry = (
        "- `tests/test_host_state_check.py` -- Turing bring-up G1 and regression R-G1 (`" + PLAN + "`; the gates of §9.3, as §16.3 E-D6 and §19.2 E-G-SIGN revise them). "
        "`util/host_state_check.py` must evaluate G-ALIAS, G-SIGN, G-SEC, G-TOOLS, G-ENV, G-NET and G-MEM. turing's 2026-10-20 state reads as measured: G-SIGN waits on owner-run checks, and every other gate fails. "
        "The suite pins every condition both ways. The preflight's D11 `commit-gpgsign` line is not judged. A tool resolving outside `~/.local/bin` fails, as does a kubectl more than one minor from the cluster's 1.36. "
        "An unrecorded parent-AGENTS.md hash or reserved address fails, and the bridge NIC's MAC is checked. "
        "R-G1: an `expected.yaml` VM larger than `hw.memsize` minus the reserve fails `vm-fits`, the X2 class. "
        "G-MEM's memory, swap and docker verdicts and text equal `util/macvm_ctl.bash status`'s on the same fixtures. A known failure outranks an unknown in its gate. "
        "Report mode exits 0, `--check` exits 1 on a failure and 2 on an unknown, and environment errors exit 2: a bad probe document, a probe from another host, an unknown `expected.yaml` key. "
        "The checker passes the probe `--section`, `--tool` and `--vm`, and an end-to-end case runs the real probe under `/bin/bash` with stub tools. "
        "The committed `conf/hosts/turing/expected.yaml` loads. Its G-MEM numbers equal `macvm_ctl.bash`'s defaults, its `local_bin` tools are the ones `conf/hosts/turing/hosttools-environment.yml` installs, and its conda envs cover every spec in `conf/hosts/turing/conda-envs/`. "
        "`util/ad-hoc/2026-10-20_turing_g1_mutation_check.py` kills 42 of 42 mutants across both suites.\n"
    )
    probe_util = (
        "- `util/host_state_probe.bash` -- Read-only host-state collector for the turing bring-up gates: `bash util/host_state_probe.bash [--json] [--section NAME]... [--root DIR] [--tool NAME]... [--vm NAME] [--timeout SECONDS]`. "
        "Each capture is one command's raw exit code, stdout and stderr, in twelve sections: hardware, memory, docker, hypervisor, disk, power, network, security, toolchain, env, git and signing. "
        "It judges nothing, so a saved probe can be evaluated again later. Names and modes only: nothing under `~/.ssh` or `~/.gnupg` is opened, and no credential command runs. "
        "A failed, missing or hung command is recorded, not an error, and each capture is killed at `--timeout` (default 60 s). Bash 3.2-safe. Exit 0, or 2 on a usage error; never 1. The JSON schema is in the header. "
        "Every macOS tool is an overridable variable, as are `ALIAS_CHECK`, `SIGNING_CHECK` and `SIGNING_PREFLIGHT`. It graduates `util/ad-hoc/2026-10-15_turing_host_state_probe.bash`. Turing bring-up G1. Tests: `tests/test_host_state_probe.py`.\n"
    )
    check_util = (
        "- `util/host_state_check.py` -- Host gates G-ALIAS, G-SIGN, G-SEC, G-TOOLS, G-ENV, G-NET and G-MEM (plan §9.3): `python3 util/host_state_check.py [--check] [--json] [--section GATE]... [--host NAME] [--expected FILE] [--probe-json FILE | --probe SCRIPT [--root DIR] [--timeout SECONDS]]`. "
        "It runs the probe, or reads a saved one, and compares it with `conf/hosts/<host>/expected.yaml`. Each condition is PASS, FAIL, UNKNOWN, OPERATOR (owner-run: I-SIGN, iperf3) or INFO. "
        "G-ALIAS reads `util/git_remote_alias_check.py`. G-SIGN reads `util/configure_commit_signing.py --check` and the preflight's gpg-agent lines. G-MEM uses `util/macvm_ctl.bash`'s arithmetic and text. "
        "Report mode exits 0. `--check` (I-G1) exits 1 when a gate fails and 2 when one is unknown, and usage and environment errors exit 2. G-AUTH, G-PATH and G-AGENT are evaluated elsewhere, and the report names them. "
        "The JSON schema is in the docstring. Needs PyYAML. Turing bring-up G1. Tests: `tests/test_host_state_check.py`.\n"
    )
    changelog = (
        "- **`util/host_state_probe.bash` and `util/host_state_check.py`: the turing host gates** (turing bring-up task G1 of\n"
        f"  `{PLAN}`; the gates of §9.3).\n"
        "  - The probe collects the host state read-only. Each capture is one command's raw exit code, stdout and stderr,\n"
        "    in twelve sections, as text or schema-1 JSON. Names and modes only. It graduates the 2026-10-15 ad-hoc probe.\n"
        "  - The checker evaluates the seven gates §9.3 gives it (G-ALIAS, G-SIGN, G-SEC, G-TOOLS, G-ENV, G-NET and G-MEM)\n"
        "    against `conf/hosts/turing/expected.yaml` (new). `--check` exits 1 when a gate fails (I-G1). R-G1: a VM\n"
        "    larger than `hw.memsize` minus the reserve fails G-MEM (the X2 class). On turing on 2026-10-20 none of the\n"
        "    seven passes: G-SIGN waits on owner-run checks, and the other six fail on the open owner steps.\n"
        "  - `tests/test_host_state_probe.py` and `tests/test_host_state_check.py` (new) are wired into `ci.yml`, its\n"
        "    `host-tooling-macos` job and `docs/REFERENCE.md`. `util/ad-hoc/2026-10-20_turing_g1_mutation_check.py` (new)\n"
        "    shows that the suites kill 42 of 42 mutants.\n"
        "\n"
    )
    return [
        # ci.yml: the regression step, after G2's suite (E-LAND-3), and the G4 job's lists.
        (CI, PROBE_SUITE, f"          {G2_SUITE}\n          # tests/test_headless_signing_preflight.py:", f"          {G2_SUITE}\n" + ci_suites + "          # tests/test_headless_signing_preflight.py:"),
        (CI, "home_path_literal_check configure_commit_signing host_state_probe host_state_check\n", "home_path_literal_check configure_commit_signing\n", "home_path_literal_check configure_commit_signing host_state_probe host_state_check\n"),
        (CI, "util/host_state_probe.bash util/host_state_check.py conf/hosts/turing/expected.yaml", "        conf/home_path_literal_baseline.json .pre-commit-config.yaml\n", "        util/host_state_probe.bash util/host_state_check.py conf/hosts/turing/expected.yaml conf/hosts/turing/hosttools-environment.yml\n        conf/home_path_literal_baseline.json .pre-commit-config.yaml\n"),
        (CI, "# tests/redacted_env.py and this workflow always count.\n", "# tests/redacted_env.py and this workflow always count. G1's two suites join when it lands.\n", "# tests/redacted_env.py and this workflow always count.\n"),
        # The G4 gate's suite set.
        (G4_TEST, '    "host_state_check",  # G1\n', '    "configure_commit_signing",  # commit-signing plan K2\n}', '    "configure_commit_signing",  # commit-signing plan K2\n    "host_state_probe",  # G1\n    "host_state_check",  # G1\n}'),
        (G4_TEST, "run on the host (plan §8).\n", "run on the host (plan §8). G1's two suites join when it lands.\n", "run on the host (plan §8).\n"),
        # docs/REFERENCE.md.
        (REFERENCE, PROBE_SUITE, f"\n{G2_SUITE}\npython3 -m unittest -v tests/test_headless_signing_preflight.py\n", f"\n{G2_SUITE}\n{PROBE_SUITE}\n{CHECK_SUITE}\npython3 -m unittest -v tests/test_headless_signing_preflight.py\n"),
        (REFERENCE, "**220** with G1's", RUN_LIST_COUNTS, RUN_LIST_COUNTS + ", **220** with G1's `tests/test_host_state_probe.py` and `tests/test_host_state_check.py`"),
        (REFERENCE, "- `tests/test_host_state_probe.py` --", "- `tests/test_headless_signing_preflight.py` -- Turing bring-up B7", probe_entry + check_entry + "- `tests/test_headless_signing_preflight.py` -- Turing bring-up B7"),
        (REFERENCE, "the eleven host-tooling suites", "the nine host-tooling suites (the eight turing bring-up suites and", "the eleven host-tooling suites (the ten turing bring-up suites, G1's two among them, and"),
        (REFERENCE, "- `util/host_state_probe.bash` --", "- `util/headless_signing_preflight.bash` -- Non-credential signing readiness", probe_util + check_util + "- `util/headless_signing_preflight.bash` -- Non-credential signing readiness"),
        # CHANGELOG.md, directly below G4's entry: away from the top of [Unreleased] / ### Added (E-LAND-3).
        ("CHANGELOG.md", "the turing host gates** (turing bring-up task G1", G4_CHANGELOG_TAIL, G4_CHANGELOG_TAIL + changelog),
        # The ad-hoc probe G1 graduates.
        (
            AD_HOC_PROBE,
            "# Status:     superseded",
            "# Status:     ad-hoc — investigation (turing host bring-up evidence capture)\n# Retire when: util/host_state_probe.bash lands (plan task T1.1) and supersedes it\n",
            "# Status:     superseded on 2026-10-20 by util/host_state_probe.bash and util/host_state_check.py (plan task G1)\n# Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25); its output is\n#             the plan's Appendix A\n",
        ),
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
            print(f"FAIL     {rel}: anchor found {text.count(anchor)} times: {anchor[:60]!r}")
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
