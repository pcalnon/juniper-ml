"""
Write the turing bring-up Session 3 record: plan v1.3.0 §18, and the E2 spec-header corrections, idempotently.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: ad-hoc — one-off (the Session 3 record of the turing bring-up)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§17, §18);
         prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_turing-session-2-e6-d5-d6-h1-done-e2-blocked-on-little-snitch.md
         (the handoff Session 3 continued from); reports/2026-10-20_turing-e2-envs/README.md

Why: Session 3 landed G5, G6 and G4, created two of E2's three envs, and found four errata. The plan records them
in a new §18, the same way §16 and §17 recorded Sessions 1 and 2. The conda-env spec headers carried a recreate
command that ran mamba without TLS verification (E-SSL) and a STATUS line that is no longer true, so those change
too. The plan is only ever edited by turing sessions, but the edits still live here, re-applied to a fresh
origin/main copy before the upload (§17.3 E-LAND-2).

Each edit has a marker. When the marker is already present the edit is skipped; otherwise its anchor must occur
exactly once. A re-run on a newer main therefore applies cleanly or stops loudly.

Usage:
    python3 -I util/ad-hoc/2026-10-20_turing_session3_record.py [--root REPO_ROOT] [--dry-run]

Exit 0 = every edit applied or already present; 1 = an anchor is missing or ambiguous (nothing written).
"""

import argparse
import sys
from pathlib import Path

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
ENVS = "conf/hosts/turing/conda-envs/"
HOSTTOOLS = "conf/hosts/turing/hosttools-environment.yml"
PREV_HANDOFF = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-19_turing-session-2-e6-d5-d6-h1-done-e2-blocked-on-little-snitch.md"
HANDOFF = "prompts/thread-handoff_automated-prompts/HANDOFF_2026-10-20_turing-session-3-g5-g6-g4-landed-e2-two-envs-created-pypi-blocked.md"

G5 = "juniper-ml#2272 (`a5311979`)"
G6 = "juniper-ml#2274 (`223d09a7`)"
G4 = "juniper-ml#2276 (`3968ca04`)"

OLD_STATUS = (
    "# STATUS 2026-10-19: the spec solves; the env is NOT yet created or validated. On turing, outbound connections\n"
    "# from mamba and from every python interpreter time out while curl and gh connect (Little Snitch's network\n"
    "# extension is active), so no package could be downloaded.\n"
)
STATUS = {
    "JuniperCascor1": (
        "# STATUS 2026-10-20: CREATED on turing with MAMBA_SSL_VERIFY=true and mamba 2.1.1 (67 packages, the solve above;\n"
        "# torch.backends.mkl.is_available() is True). NOT yet validated: CI's pip steps need pypi.org from this env's\n"
        "# python3.14, which Little Snitch holds for an unanswered alert (plan §18.3 E-NET-3). Resume with\n"
        "# util/ad-hoc/2026-10-19_turing_e2_validate_envs.py cascor --phase install. Export: reports/2026-10-20_turing-e2-envs/.\n"
    ),
    "JuniperData": (
        "# STATUS 2026-10-20: CREATED on turing with MAMBA_SSL_VERIFY=true and mamba 2.1.1 (91 packages, the solve above).\n"
        "# NOT yet validated: CI's pip steps need pypi.org from this env's python3.14, which Little Snitch holds for an\n"
        "# unanswered alert (plan §18.3 E-NET-3). Resume with util/ad-hoc/2026-10-19_turing_e2_validate_envs.py data\n"
        "# --phase install. Export: reports/2026-10-20_turing-e2-envs/.\n"
    ),
    "JuniperCanopy1": (
        "# STATUS 2026-10-20: the spec still solves (223 conda packages, 189 MB); the env is NOT yet created. mamba now\n"
        "# reaches conda.anaconda.org, but the pip section runs the new env's python3.14 against pypi.org, which Little\n"
        "# Snitch holds for an unanswered alert (plan §18.3 E-NET-3). Create it once the owner allows pypi.org and\n"
        "# files.pythonhosted.org for the env interpreters.\n"
    ),
}
SSL_NOTE = "#   (mamba 2.x reads MAMBA_SSL_VERIFY; CONDA_SSL_VERIFY reaches only conda itself: plan §18.3 E-SSL.)\n"

HEADER_OLD = "- **Version**: 1.2.0 — v1.1.1 plus the Session 2 record (§17, 2026-10-19). v1.1.1 closed task E6 and added erratum E-CQ; v1.1.0 added the Session 1 record and errata (§16). Where §16 or §17 disagrees with an earlier section, the later section wins."
HEADER_NEW = "- **Version**: 1.3.0 — v1.2.0 plus the Session 3 record (§18, 2026-10-20). v1.2.0 added the Session 2 record (§17); v1.1.1 closed task E6 and added erratum E-CQ; v1.1.0 added the Session 1 record and errata (§16). Where §16, §17 or §18 disagrees with an earlier section, the later section wins."

SECTION = f"""## 18. Session 3 record (v1.3.0, 2026-10-20)

Session 3 ran on turing on 2026-10-19/20 (EDT; 2026-10-20 UTC). It continued from `{PREV_HANDOFF}`, and its own handoff is `{HANDOFF}`.

### 18.1 Owner rulings

- **Merging.** Approval is granted for every PR in the session's work arc, merging only after green, as in §16.1. It does not cover the `pypi` deployment gate.
- No new decision ruling. The E2-first order of §17.1 stood. E2 went first, and the G-arc ran while E2 waited on the owner's Little Snitch approval.

### 18.2 Task status after Session 3

| Task | Status | Record |
|---|---|---|
| G5 | landed | {G5}: `util/home_path_literal_check.py`, the G-PATH gate, with `conf/home_path_literal_baseline.json` (436 files and 651 lines when it landed; 427 of the files under `util/ad-hoc/`). It runs as the `home-path-literal` pre-commit hook and as a whole-scope step in ci.yml's Pre-commit job. 43 tests; `util/ad-hoc/2026-10-20_turing_g5_mutation_check.py` kills 22 of 22 mutants. A CodeQL thread blocked the first head (E-CQ2) |
| G6 | landed | {G6}: the `git-remote-alias` pre-push hook (G2's `--check --if-configured`), with `default_stages: [pre-commit]` (E-G6) and `minimum_pre_commit_version` 3.2.0. CI runs the stage as a smoke test, and the hook skips there. **Acceptance on turing waits on A1:** the stage fails on exactly juniper-k8s and juniper-recurrence, 28 of 30 checks |
| G4 | landed, advisory | {G4}, built after juniper-ml#2273 merged (E-LAND-3): the `host-tooling-macos` job runs the eight host-tooling suites on `macos-latest` under `/bin/bash` 3.2, behind in-job change detection. It joins the Quality Gate's `needs:` after 10 green runs. First run, on the PR: green on arm64 macOS 26 (`/bin/bash` 3.2.57, `/opt/homebrew`), 371 tests, 7 skipped, 2 m 13 s. On turing: 376 tests, 1 skipped |
| E2 | **partial (OWNER: Little Snitch for PyPI)** | JuniperCascor1 (67 packages) and JuniperData (91) were created on 2026-10-20 with `MAMBA_SSL_VERIFY=true` (E-SSL); their exports are in `reports/2026-10-20_turing-e2-envs/`. JuniperCanopy1 is not created: its pip section, and both validations, need `pypi.org` from each new env's `python3.14`, which Little Snitch holds for an unanswered alert (E-NET-3). The validation runner's `prepare` phase is done for cascor and data |
| G1 | not started | next agent task, with E2's validation once PyPI is allowed |

### 18.3 Errata

- **E-SSL (D6's and E2's recipes).** mamba 2.x ignores `CONDA_SSL_VERIFY`. With `~/.condarc`'s `ssl_verify: false`, `CONDA_SSL_VERIFY=true mamba config list ssl_verify --sources` still reports `<false>`; `MAMBA_SSL_VERIFY=true` reports `<system>`.
  - So every `CONDA_SSL_VERIFY=true mamba ...` in this plan's records ran without TLS verification. That covers JuniperHostTools (2026-10-17) and the 2026-10-19 dry runs.
  - The recreate lines in `conf/hosts/turing/hosttools-environment.yml` and the three `conf/hosts/turing/conda-envs/*.yml` now say `MAMBA_SSL_VERIFY=true`. `CONDA_SSL_VERIFY` still governs `conda` itself.
  - OWNER: owner step 4 (`ssl_verify: true` in `~/.condarc`) removes the trap for both tools. Whether to re-create JuniperHostTools with verification on is the owner's call; its packages were checked against repodata that itself arrived without TLS verification.
- **E-NET-3 (E-NET-2 revisited, 2026-10-20).** Little Snitch's verdicts changed between the sessions.
  - `mamba` now reaches conda.anaconda.org: a `mamba search` refreshed the osx-64 and noarch repodata, and both envs downloaded.
  - Base `python3.13` now fails fast with `SSL: UNEXPECTED_EOF_WHILE_READING` in the handshake. That fits a deny verdict rather than a pending alert, and it no longer blocks E2, which uses mamba for the network.
  - Each new env's `python3.14` (JuniperCascor1, JuniperData) hangs past its 15 s socket timeout toward pypi.org: a held connection, an alert nobody answered.
  - `curl` and JuniperPython's `python3.14` reach every URL as before.
  - OWNER: allow `pypi.org` and `files.pythonhosted.org` for `/usr/local/miniforge3/envs/JuniperCascor1/bin/python3.14`, `.../JuniperData/bin/python3.14` and, once created, `.../JuniperCanopy1/bin/python3.14`. Approving the alerts while a run waits also works.
- **E-G6 (G6, pre-commit's stage semantics).** A hook with no `stages` runs at every stage. Without `default_stages`, the pre-push stage G6 needs would have re-run the whole commit suite on every push from an opted-in host. It would also have turned the CI smoke step into a whole-tree lint run, undoing the Pre-commit job's changed-files split.
  - A manifest's own `stages` overrides `default_stages`, so `check-added-large-files` (pre-commit-hooks v6.0.0) and `isort` carry `stages: [pre-commit]` themselves.
  - The smoke step names the hook (`pre-commit run --hook-stage pre-push git-remote-alias --all-files`), so a hook that later joins the stage cannot widen it.
- **E-CQ2 (landing, after E-LAND).** CodeQL's `py/overly-permissive-file` flagged `os.chmod(tmp, 0o644)` in G5's baseline writer. Its review thread blocked {G5.split(" ")[0]} with every check green, until the writer dropped the chmod for a sibling temp file under the process umask. `util/ad-hoc/2026-10-05_codeql_python_prescreen.py` does not predict that rule, so check new code for `chmod(` before landing.
- **E-LAND-3 (concurrent PRs on the shared files).** Two concurrent PRs collide on update-branch (`mergeable: CONFLICTING`) when both insert at the top of CHANGELOG's `[Unreleased]` / `### Added`, or both change AGENTS.md's suite-count line. The PR that lands second must then rebuild those files on the new main. That was the case here for G6 ({G6.split(" ")[0]}) and the recurrence session's juniper-ml#2273, which reported it by cross-session message.
  - G6's entry now anchors directly below G5's entry and G4's below G2's, and `git merge-tree` confirmed the branches merge cleanly. Merge order was agreed: #2273, then G6, then G4.
  - The count line cannot be avoided, so a suite-adding PR (G4) is built from main after the other suite-adding PR merges.

"""


def edits():
    out = []
    for env, status in STATUS.items():
        path = f"{ENVS}{env}.yml"
        line = f"#   CONDA_SSL_VERIFY=true mamba env create --override-channels -c conda-forge -f {path}\n"
        new = f"#   MAMBA_SSL_VERIFY=true mamba env create --override-channels -c conda-forge -f {path}\n" + SSL_NOTE
        out.append((path, SSL_NOTE, line, new))
        out.append((path, status.splitlines()[0], OLD_STATUS, status))
    hosttools_line = f"#   CONDA_SSL_VERIFY=true mamba env create --override-channels -f {HOSTTOOLS}\n"
    out.append((HOSTTOOLS, SSL_NOTE, hosttools_line, f"#   MAMBA_SSL_VERIFY=true mamba env create --override-channels -f {HOSTTOOLS}\n" + SSL_NOTE))
    out.append((PLAN, HEADER_NEW, HEADER_OLD, HEADER_NEW))
    out.append((PLAN, "## 18. Session 3 record (v1.3.0, 2026-10-20)", "## Appendix A — probe output excerpts (2026-10-15)", SECTION + "## Appendix A — probe output excerpts (2026-10-15)"))
    return out


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    if any(token in SECTION for token in ("G6SHA", "G4PR", "G4SHA")):
        print("FAIL     fill in G6 and G4's PR numbers and merge shas first")
        return 1
    texts, failed = {}, 0
    for rel, marker, anchor, repl in edits():
        text = texts.get(rel)
        if text is None:
            text = (args.root / rel).read_text(encoding="utf-8")
        if marker in text:
            print(f"present  {rel}: {marker[:60]!r}")
        elif text.count(anchor) == 1:
            text = text.replace(anchor, repl)
            print(f"apply    {rel}: {marker[:60]!r}")
        else:
            print(f"FAIL     {rel}: anchor found {text.count(anchor)} times: {anchor[:60]!r}")
            failed += 1
        texts[rel] = text

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
