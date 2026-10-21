"""
Apply turing bring-up H4's edits to the shared files, idempotently: util/mcp_setup.bash and its suite.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-21
Status: ad-hoc — one-off (turing bring-up task H4: util/mcp_setup.bash, Serena pinned and bound to the checkout)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task H4, D10, §10; §17.3 E-LAND-2
         and §18.3 E-LAND-3); util/ad-hoc/2026-10-20_turing_h2_apply.py and util/ad-hoc/2026-10-20_turing_g1_apply.py
         (the pattern this follows)

Why: H4 lands through the GitHub API as whole-file uploads of files other PRs share. An upload built from an older
base silently reverts whatever main gained since (E-LAND-2). So the edits live here, keyed on anchors, and are
re-applied to a fresh origin/main copy right before the upload. Each edit leaves G1's and H2's markers in place, so
their apply scripts' --dry-run keeps reporting every edit present.

The edits:
- ci.yml: the regression step runs tests/test_mcp_setup.py right after G1's two suites; the host-tooling-macos
  job's HOST_TOOLING_SUITES gains mcp_setup (plan §9.1: the suites run there too), and HOST_TOOLING_PATHS gains the
  script, conf/hosts/turing/mcp.json, .serena/project.yml and .gitignore, which the suite reads.
- tests/test_ci_host_tooling_macos.py: SUITES gains mcp_setup (that suite gates the job's list).
- docs/REFERENCE.md: the suite in "Running every suite" (224 in its count history) and in § Test Suite Reference;
  the script in § Utility Script Reference; G4's entry says the list is twelve.
- AGENTS.md: the suite count follows ci.yml's regression step, **Last Updated** takes today's UTC date, and the
  conf/hosts/<host>/ pointer names mcp.json.
- CHANGELOG.md: an [Unreleased] / Added entry directly below H2's entry (E-LAND-3).
- .gitignore: the script's .mcp.json.bak-* backups, which hold the previous file's API tokens.

Each edit has a marker. When the marker is already present the edit is skipped; otherwise its anchor must occur
exactly once. A re-run on a newer main therefore applies cleanly or stops loudly.

Usage:
    python3 -I util/ad-hoc/2026-10-21_turing_h4_apply.py [--root REPO_ROOT] [--dry-run]

Exit 0 = every edit applied or already present; 1 = an anchor is missing or ambiguous (nothing written).
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
AUDIT = "notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_HEADLESS-SIGNING-AND-SERENA-HARNESS-AUDIT.md"
CI = ".github/workflows/ci.yml"
REFERENCE = "docs/REFERENCE.md"
G4_GATE = "tests/test_ci_host_tooling_macos.py"
LINE = "python3 -m unittest -v tests/test_mcp_setup.py"
CHECK_LINE = "python3 -m unittest -v tests/test_host_state_check.py"
# What util/ad-hoc/2026-10-21_turing_h4_mutation_check.py reported on the landed script.
MUTANT_TALLY = "20 of 20"

CI_SUITE = (
    "          # tests/test_mcp_setup.py: turing bring-up H4. util/mcp_setup.bash writes a checkout's .mcp.json Serena\n"
    "          # entry: pinned to a full commit from conf/hosts/<host>/mcp.json (D10), bound with --project (audit\n"
    "          # A2-F1), on a context whose excluded_tools hold the shell tool. Other servers are kept, a changed file\n"
    "          # is backed up, a second run writes nothing; --check fails on an unpinned, unbound or rebound entry, and\n"
    "          # every refusal writes nothing. Stdlib plus PyYAML (it reads .serena/project.yml); runs /bin/bash.\n"
    f"          {LINE}\n"
)
CI_SUITE_ANCHOR = f"          {CHECK_LINE}\n"
CI_SUITES_OLD = "        host_state_probe host_state_check\n      HOST_TOOLING_PATHS: >-\n"
CI_SUITES_NEW = "        host_state_probe host_state_check\n        mcp_setup\n      HOST_TOOLING_PATHS: >-\n"
CI_PATHS_ANCHOR = "        util/host_state_probe.bash util/host_state_check.py\n"
CI_PATHS_LINE = "        util/mcp_setup.bash conf/hosts/turing/mcp.json .serena/project.yml .gitignore\n"
CI_PIP_OLD = "G1's check reads expected.yaml.\n"
CI_PIP_NEW = "G1's check reads expected.yaml; H4's suite reads .serena/project.yml.\n"

G4_SUITES_OLD = '    "host_state_check",  # G1\n}\n'
G4_SUITES_NEW = '    "host_state_check",  # G1\n    "mcp_setup",  # H4\n}\n'

RUN_LIST_ANCHOR = f"\n{CHECK_LINE}\n"
RUN_LIST_COUNT = "**223** with H2's `tests/test_macos_host_sme_contract.py`, `tests/test_signing_auth_sme_contract.py` and `tests/test_k8s_node_sme_contract.py`"
G4_ENTRY_TAIL = "`tests/test_configure_commit_signing.py`), each of which also runs in the Linux regression step, and every watched path must exist."
G4_ENTRY_ADDED = " H4's `tests/test_mcp_setup.py` made the list twelve."
SUITE_REF_ANCHOR = "- `scripts/test.bash` -- Manual end-to-end harness"
UTIL_REF_ANCHOR = "- `util/wait_for_checks.py` -- Waits for a PR's **required** status checks"

AGENTS_CONFIG_OLD = "and turing's conda-env specs and `hosttools-environment.yml`\n"
AGENTS_CONFIG_NEW = "turing's conda-env specs and `hosttools-environment.yml`, and `mcp.json`, the Serena pin `util/mcp_setup.bash` reads (H4)\n"

H2_CHANGELOG_TAIL = "  - `util/ad-hoc/2026-10-20_turing_h2_mutation_check.py` (new) shows that they kill 28 of 28 mutants, six of\n    them in the guard.\n\n"

GITIGNORE_OLD = "# MCP server config (contains API tokens)\n.mcp.json\n"
GITIGNORE_NEW = "# MCP server config (contains API tokens)\n.mcp.json\n# util/mcp_setup.bash's backups of it, which hold the same tokens\n.mcp.json.bak-*\n"


def edits():
    """(path, marker, anchor, replacement). The replacement keeps the anchor and adds the H4 text."""
    suite = (
        "- `tests/test_mcp_setup.py` -- Turing bring-up H4 (`" + PLAN + "`; D10, §10). Drives `util/mcp_setup.bash` under `/bin/bash` against a temporary checkout and a pin file of its own; the real home and the repository's own `.mcp.json` are never written. "
        "The Serena entry is pinned argument for argument: `uvx --from git+https://github.com/oraios/serena@<commit> serena start-mcp-server --context <context> --project <resolved checkout> --open-web-dashboard False`; a worktree's `.git` file counts. "
        "The three defects it fixes each fail `--check` and are each replaced by a write: an entry without `--project` (audit A2-F1 of `" + AUDIT + "`), one bound to another checkout (A2-F4), and an unpinned source (D10). "
        "Other servers and top-level keys are kept; a changed file is backed up (two changes in one second keep both backups) and keeps its mode; a new file is 600; a second run writes nothing; `--dry-run` writes nothing; `--remove` keeps the rest and deletes a file that held only Serena. "
        "Every refusal exits 2 and writes nothing: a short sha, a branch or a tag for a pin, a context that is a path, a fork for a source, another host's pin, a `.mcp.json` that is not a JSON object or is a symlink, no checkout, no pin, no python. "
        "The committed `conf/hosts/turing/mcp.json` drives the script, `.serena/project.yml` excludes `execute_shell_command` too, and `.gitignore` covers `.mcp.json` and its backups. "
        f"`util/ad-hoc/2026-10-21_turing_h4_mutation_check.py` kills {MUTANT_TALLY} mutants.\n"
    )
    util = (
        "- `util/mcp_setup.bash` -- Writes a checkout's `.mcp.json` Serena entry: `bash util/mcp_setup.bash [--host NAME] [--conf FILE] [--check | --remove] [--dry-run] [checkout]` (default: the checkout that holds the script; a worktree counts). "
        "The entry runs `uvx --from git+https://github.com/oraios/serena@<commit> serena start-mcp-server --context <context> --project <checkout> --open-web-dashboard False`. "
        "`<commit>` (a full 40-hex sha) and `<context>` (a built-in name) come from `conf/hosts/<host>/mcp.json`, the host's approved pin; with no pin it refuses, so Serena never runs unpinned HEAD (decision D10). "
        "turing's pin is v1.7.0 (`949a27ef`), whose claude-code context excludes `execute_shell_command`; `.serena/project.yml` excludes it too. A pin bump must re-read the context's `excluded_tools` at the new commit. "
        "It fixes audit A2-F1 (no `--project`) and A2-F4 (no `.mcp.json` in a worktree). Other servers and keys are kept; a changed file is backed up to `.mcp.json.bak-<UTC time>` (gitignored; it holds the old tokens) and keeps its mode; a second run writes nothing. "
        "`--check` exits 1 on a missing, unpinned, unbound or rebound entry. Exit 2 on usage or environment errors, including an existing `.mcp.json` that is not a JSON object, which it never overwrites. "
        "On turing, Serena v1.7.0 does not yet start: its exact `cryptography==50.0.0` pin has no Intel-macOS wheel, and building it needs Rust 1.83 (the host has 1.71). Tests: `tests/test_mcp_setup.py`.\n"
    )
    changelog = (
        "- **`util/mcp_setup.bash`: each checkout's Serena entry, pinned and bound** (turing bring-up task H4 of\n"
        f"  `{PLAN}`; decision D10).\n"
        "  - It writes `<checkout>/.mcp.json`'s `serena` entry: `uvx --from git+https://github.com/oraios/serena@<commit>\n"
        "    serena start-mcp-server --context <context> --project <checkout> --open-web-dashboard False`. Other\n"
        "    servers are kept, a changed file is backed up first, and a second run writes nothing. `--check` and\n"
        "    `--remove` complete it.\n"
        "  - `--project` fixes audit A2-F1 (Serena started with no active project), and running it per checkout fixes\n"
        f"    A2-F4 (no worktree had a `.mcp.json`), both from `{AUDIT}`.\n"
        "  - The pin comes from `conf/hosts/<host>/mcp.json` (new for turing): Serena v1.7.0 at its full commit, on the\n"
        "    claude-code context, whose `excluded_tools` hold `execute_shell_command`. `.serena/project.yml` now\n"
        "    excludes it too, and `.gitignore` covers the script's `.mcp.json.bak-*` backups.\n"
        "  - On turing the pinned Serena does not start yet: its exact `cryptography==50.0.0` pin ships no Intel-macOS\n"
        "    wheel, and building it needs Rust 1.83 (the host has 1.71). The live `claude mcp list` check waits on\n"
        "    that.\n"
        "  - `tests/test_mcp_setup.py` (new) is wired into `ci.yml`, the `host-tooling-macos` job and\n"
        f"    `docs/REFERENCE.md` (224 suites). `util/ad-hoc/2026-10-21_turing_h4_mutation_check.py` (new) shows that it\n"
        f"    kills {MUTANT_TALLY} mutants.\n"
        "\n"
    )
    return [
        (CI, LINE, CI_SUITE_ANCHOR, CI_SUITE_ANCHOR + CI_SUITE),
        (CI, "        mcp_setup\n      HOST_TOOLING_PATHS", CI_SUITES_OLD, CI_SUITES_NEW),
        (CI, CI_PATHS_LINE, CI_PATHS_ANCHOR, CI_PATHS_ANCHOR + CI_PATHS_LINE),
        (CI, "H4's suite reads .serena/project.yml", CI_PIP_OLD, CI_PIP_NEW),
        (G4_GATE, '    "mcp_setup",  # H4\n', G4_SUITES_OLD, G4_SUITES_NEW),
        (REFERENCE, f"\n{CHECK_LINE}\n{LINE}\n", RUN_LIST_ANCHOR, f"\n{CHECK_LINE}\n{LINE}\n"),
        (REFERENCE, "**224** with H4's", RUN_LIST_COUNT, RUN_LIST_COUNT + ", **224** with H4's `tests/test_mcp_setup.py`"),
        (REFERENCE, G4_ENTRY_ADDED.strip(), G4_ENTRY_TAIL, G4_ENTRY_TAIL + G4_ENTRY_ADDED),
        (REFERENCE, "- `tests/test_mcp_setup.py` --", SUITE_REF_ANCHOR, suite + SUITE_REF_ANCHOR),
        (REFERENCE, "- `util/mcp_setup.bash` --", UTIL_REF_ANCHOR, util + UTIL_REF_ANCHOR),
        ("AGENTS.md", "the Serena pin `util/mcp_setup.bash` reads (H4)", AGENTS_CONFIG_OLD, AGENTS_CONFIG_NEW),
        # Directly below H2's entry, not at the top of [Unreleased] / ### Added, where concurrent PRs insert theirs.
        ("CHANGELOG.md", "**`util/mcp_setup.bash`: each checkout's Serena entry, pinned and bound**", H2_CHANGELOG_TAIL, H2_CHANGELOG_TAIL + changelog),
        (".gitignore", ".mcp.json.bak-*\n", GITIGNORE_OLD, GITIGNORE_NEW),
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
