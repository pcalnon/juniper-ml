"""
Apply the commit-signing PR's edits to the shared files, idempotently, against any copy of them.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-19
Status: ad-hoc — landing helper (the commit-signing PR; tasks K2, K3, K4)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md (§9 K2-K4,
         §11 landing); util/configure_commit_signing.py; tests/test_configure_commit_signing.py

Why: these files are shared with every concurrent session. A whole-file upload through the GitHub
API that was built from a stale copy silently reverts other PRs' lines: juniper-ml#2262 reverted
#2259 this way. So each upload is built by running this script against a FRESH `origin/main` copy,
taken at upload time. The files it edits:

- `.github/workflows/ci.yml`;
- `.github/workflows/main-verify.yml`;
- `docs/REFERENCE.md`;
- `CHANGELOG.md`;
- `AGENTS.md`;
- the bring-up plan.

Every edit has a marker. When the marker is present the edit is skipped; otherwise its anchor
must occur exactly once. A second run therefore changes nothing. The AGENTS.md suite count is
recomputed from REFERENCE.md's "Running every suite" list, and `Last Updated` is set to today's
UTC date, which is what the "Verify AGENTS.md Last Updated" check wants.

Usage:
    python3 -I util/ad-hoc/2026-10-19_commit_signing_shared_file_edits.py [--base DIR] [--check]

`--base DIR` holds repo-relative copies of the files (default: the repository root). `--check`
reports what would change and writes nothing.

Exit codes:

- 0: applied, or nothing to do;
- 1: `--check` found pending edits;
- 2: an anchor was missing or not unique (the file changed; update the anchor).
"""

from __future__ import annotations

import argparse
import datetime
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLAN = "notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md"
BRINGUP = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
SUITE = "tests/test_configure_commit_signing.py"
TOOL = "util/configure_commit_signing.py"
MUTATION = "util/ad-hoc/2026-10-19_commit_signing_mutation_check.py"
# The final run of MUTATION (plan §14.4): round 1's 40 mutants plus 10 for round 2's defect classes.
MUTANTS_KILLED = "50 of 50"

CI_ANCHOR = "          python3 -m unittest -v tests/test_headless_signing_preflight.py\n"
CI_BLOCK = (
    "          # tests/test_configure_commit_signing.py: commit-signing plan R-S1..R-S19 (bring-up B4a, gate G-SIGN).\n"
    "          # util/configure_commit_signing.py installs the owner's signing for the Juniper tree as one includeIf\n"
    "          # (gitdir/i: on the root, rendered from realpaths) plus an include file, and checks it without\n"
    "          # credentials. Real git on temp checkouts under a temp HOME with every GIT_* scrubbed and a\n"
    "          # Homebrew-shaped recording fake gpg: terminal, IDE-argv, merge, cherry-pick and annotated-tag\n"
    "          # commits sign with the pinned key; D11's env keeps a plain agent commit unsigned, while -S,\n"
    "          # -c include.path= and --config-env still sign (the gap the C8 guard and K12 close). Also pinned:\n"
    "          # planted local keys, include integrity, IDE settings (JSONC), agent auto-approve verdicts, an exact\n"
    "          # --remove, and an audit hook proving no ~/.gnupg or ~/.ssh open, no gpg run, no stray write.\n"
    "          python3 -m unittest -v tests/test_configure_commit_signing.py\n"
)
# G4's macOS job (juniper-ml#2276) runs the host-tooling suites under BSD userland; this suite joins it.
MACOS_SUITES_ANCHOR = "        git_remote_alias_check headless_signing_preflight juniper_repo_ssh_setup home_path_literal_check\n"
MACOS_SUITES_NEW = "        git_remote_alias_check headless_signing_preflight juniper_repo_ssh_setup home_path_literal_check configure_commit_signing\n"
MACOS_PATHS_ANCHOR = "        util/headless_signing_preflight.bash util/juniper_repo_ssh_setup.bash util/home_path_literal_check.py\n"
MACOS_PATHS_NEW = "        util/headless_signing_preflight.bash util/juniper_repo_ssh_setup.bash util/home_path_literal_check.py util/configure_commit_signing.py\n"
MACOS_GATE = "tests/test_ci_host_tooling_macos.py"
MACOS_GATE_ANCHOR = '    "home_path_literal_check",\n}\n'
MACOS_GATE_NEW = '    "home_path_literal_check",\n    "configure_commit_signing",  # commit-signing plan K2\n}\n'
REF_MACOS_OLD = "Its suite list must equal the eight turing host-tooling suites,"
REF_MACOS_NEW = "Its suite list must equal the nine host-tooling suites (the eight turing bring-up suites and commit-signing K2's `tests/test_configure_commit_signing.py`),"
BATTERY_ANCHOR = "          python3 -m unittest -v tests/test_check_conda_env_torch.py\n"
BATTERY_LINE = "          python3 -m unittest -v tests/test_configure_commit_signing.py\n"

REF_RUN_ANCHOR = "python3 -m unittest -v tests/test_headless_signing_preflight.py\n"
REF_RUN_LINE = "python3 -m unittest -v tests/test_configure_commit_signing.py\n"
REF_SUITE_ANCHOR = "`util/test_gpg_signing.bash`, its last validator, stays deleted.\n"
REF_SUITE_BULLET = (
    "- `tests/test_configure_commit_signing.py` -- Commit signing for the terminal and the IDEs, regressions R-S1..R-S19 "
    f"(`{PLAN}`; bring-up B4a, gate G-SIGN).\n"
    "  - **Fixtures.** Real `git` runs on temp checkouts of the 10 active repos under a temp `HOME`, with every `GIT_*` variable "
    "scrubbed. `gpg.program` is a recording fake installed as Homebrew would install it (`opt/Cellar/gnupg/<v>/bin/gpg` behind "
    "`bin/gpg`), and it answers like a successful detached signature.\n"
    "  - **What signs.** In the Juniper tree these all get the pinned key's signature: a terminal commit, the IDEs' exact argv "
    "(with and without `-S`), an argv carrying Cursor's injected config keys, a merge, a cherry-pick and an annotated tag. A "
    "lightweight tag now fails (plan S4). A linked worktree checked out outside the root signs (R-S11). A repo outside the root "
    "is untouched (R-S12), and so are `$HOME` and a root spelled through symlinks (R-S15).\n"
    "  - **D11.** Its `GIT_CONFIG_COUNT` keeps a plain agent commit from calling gpg, and it does not mask the owner-effective "
    "values `--check` judges. Its boundary is pinned too: `-S`, `-c include.path=` and `--config-env` still sign (R-S4).\n"
    "  - **Refusals.** These exit 2 before any write: an unpinned key (R-S1); an unsound `gpg.program` (R-S2); a program outside a "
    "known GnuPG install, unless vouched for (R-S18); a root at or above `$HOME`, a glob in the root, and an include under the "
    "root or inside a work tree (R-S13).\n"
    "  - **Failures.** These fail and name their scope: a repo-local or later-global `false` (R-S3); planted local `gpg.program`, "
    "`include.*`, `core.sshCommand`, a foreign `core.hooksPath` or a program-valued `core.fsmonitor` (R-S16); a missing, "
    "symlinked or writable include or include directory, and a missing include then lets a commit land unsigned (R-S17); an "
    "unmanaged key in the include (R-S19). A key planted in a linked worktree's `config.worktree` fails too, and global or "
    "system hook and include settings are reported (R-S16).\n"
    "  - **IDE settings.** An injected `GIT_CONFIG_*`, `GNUPGHOME` or `HOME` fails in `env` and in profile `env`, while `null` "
    "unsets. JSONC parses. An unparseable file, a dead user-level `git.path` and `chat.tools.global.autoApprove` fail. "
    "Workspace, root, folder and profile files are scanned (R-S5). VS Code's auto-approve rules are judged deny-first, with "
    "the legacy key and `enableAutoApprove`, and a rule that matches the empty string protects nothing, as in VS Code. A "
    "catch-all allow rule is named, and so is an unconditional Amp `Bash allow`; Amp's rules are first-match (R-S14).\n"
    "  - **Writes.** `--apply --dry-run` writes nothing and exits like `--check` (R-S6). A second `--apply` changes no byte "
    "(R-S7). Backups are made once, and an owner include survives (R-S8). `--apply` will not write through a symlinked "
    "include or into a writable directory (R-S17). `--remove` restores `~/.gitconfig` byte for byte, keeps an include another "
    "root still uses, and refuses to delete an include that differs from what `--apply` writes, even by a comment. An audit "
    "hook proves no `~/.gnupg` or `~/.ssh` open and no gpg run, and a snapshot of the temp `HOME` proves `--apply` changes "
    "only the include and the backups (R-S9).\n"
    f"  - **Also.** `--help` and `--check` run under `/usr/bin/python3`, and the source parses as Python 3.9. `{MUTATION}` "
    f"kills {MUTANTS_KILLED} mutants, each by its own pin test.\n"
)
REF_UTIL_ANCHOR = "Tests: `tests/test_headless_signing_preflight.py`.\n"
REF_UTIL_BULLET = (
    "- `util/configure_commit_signing.py` -- The owner's commit signing for the Juniper tree, in a terminal and in the IDEs:\n"
    "  `python3 util/configure_commit_signing.py [--check | --apply [--dry-run] | --remove [--dry-run]] [--json] [--root DIR] "
    "[--signing-key KEYSPEC] [--gpg-program PATH] [--include-file PATH] [--ide-settings FILE]...`.\n"
    "  - **`--apply`** writes `~/.config/git/juniper-signing.gitconfig`: the pinned `user.signingkey`, `commit.gpgsign`, "
    "`tag.gpgsign`, and an absolute `gpg.program` in a known GnuPG install. It adds one "
    '`includeIf "gitdir/i:~/Development/python/Juniper/"` to the global config, rendered from realpaths. Each value is written '
    "only when it differs, after one dated backup. It never edits IDE settings or a repository's config, never runs gpg, and "
    "never reads `~/.gnupg` or `~/.ssh`.\n"
    "  - **`--apply`** stops with exit 2 before any write when the include, or its directory, is a symlink or unsafe.\n"
    "  - **`--remove`** undoes exactly that, with `--fixed-value`. It keeps an owner include of the same pattern, and an "
    "include file that another include still points at.\n"
    "  - **`--check`** (the default) only reads. Git's repo-local variables are scrubbed (D11's `GIT_CONFIG_COUNT` among them), "
    "so an agent session judges the owner's configuration. It checks:\n"
    "    - each checkout's owner-effective values and the program's soundness;\n"
    "    - planted local or worktree `gpg.*`, `include*`, `core.sshCommand`, `core.hooksPath` and `core.fsmonitor`, in each "
    "checkout and each of its linked worktrees;\n"
    "    - the include file's integrity;\n"
    "    - IDE settings (JSONC): injected terminal variables, a dead `git.path`, global auto-approve.\n"
    "  - **INFO lines** report the layout, hooks with sha256, global or system hook and include settings, D11, and "
    "config-redirecting variables. They also say whether an IDE agent's plain `git commit`, or one of 17 bypass spellings, "
    "runs unprompted under VS Code's or Amp's rules, and they name any catch-all allow rule.\n"
    "  - Exit 0 / 1 / 2. The JSON schema is in the docstring. `GIT`, `JUNIPER_ROOT`, `COMMIT_SIGNING_GPG_CANDIDATES` and "
    f"`COMMIT_SIGNING_TODAY` are overridable. Signing plan K2. Tests: `{SUITE}`.\n"
)

CHANGELOG_ENTRY = (
    f"- **Commit signing for the terminal and the IDEs** (`{PLAN}`, VALIDATED after two consensus rounds; it extends arc B of\n"
    f"  `{BRINGUP}`).\n"
    f"  - **What the tool does.** `{TOOL}` installs and verifies the owner's signing for every checkout under\n"
    '    `~/Development/python/Juniper/` with one `includeIf "gitdir/i:~/Development/python/Juniper/"`, which points at\n'
    "    `~/.config/git/juniper-signing.gitconfig`. That file holds yamaguchi's values: `user.signingkey` pinned to the full\n"
    "    fingerprint with `!`, `commit.gpgsign` and `tag.gpgsign`, plus an absolute `gpg.program` in a known GnuPG install.\n"
    "  - **Why the IDEs need no setting.** Cursor's and VS Code's git extension adds `-S` only on request and never disables\n"
    "    signing. So both IDEs sign through git's config, without the shell's PATH or a TTY.\n"
    "  - **What is unchanged.** Repositories outside the root, and Claude Code sessions, which D11 keeps unsigned by\n"
    "    construction.\n"
    "  - **What `--check` covers.** It verifies the setup without credentials:\n"
    "    - planted repo-local signing keys and hooks;\n"
    "    - the include's integrity;\n"
    "    - IDE settings that would defeat the config;\n"
    "    - whether an IDE agent can commit, or bypass signing, without a prompt.\n"
    "  - **The other modes.** `--remove` undoes `--apply` exactly.\n"
    f"  - **Tests and evidence.** `{SUITE}` pins R-S1..R-S19, and `{MUTATION}` kills {MUTANTS_KILLED} mutants.\n"
    f"  - **Doc changes.** `{BRINGUP}` gains §19 (v1.4.0). The AGENTS.md unsigned-commit hazard gains the IDE-agent rule.\n"
    "  - **Applied on turing (2026-10-20).** An owner commit in the tree now fails closed until the owner imports the public\n"
    "    key and learns the card stubs (bring-up B2/B3). The first `gpg --card-status` writes the stubs, so no card goes into\n"
    "    turing until the agent guard (C8) is installed, the guard rules (K12) are merged and re-installed, and the IDE-agent\n"
    "    approval rules (K13) are in place. The touch policy (S11) is set at that first insertion.\n"
)

AGENTS_OLD = "  `git log -1 --format=%G?` (`N` = unsigned). Plan:\n  `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`.\n"
AGENTS_NEW = (
    "  `git log -1 --format=%G?` (`N` = unsigned). An IDE agent (Cursor, Copilot, Amp) must\n"
    "  never answer a signing failure with `--no-gpg-sign` or `-c commit.gpgsign=false`: stop\n"
    "  and ask the owner, who approves the run and touches the key. Owner signing for the\n"
    "  Juniper tree: `util/configure_commit_signing.py`. Plans:\n"
    "  `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`,\n"
    "  `notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md`.\n"
)

# The bring-up session's Session 3 record takes §18 / v1.3.0 (cross-session agreement, 2026-10-20), so
# this edit is §19 / v1.4.0 and refuses to run until §18 is on the copy it edits.
BRINGUP_PREREQ = "\n## 18. "
BRINGUP_VERSION_RE = re.compile(r"(?m)^- \*\*Version\*\*: (?P<ver>\d+\.\d+\.\d+) — (?P<rest>.*)$")
BRINGUP_VERSION = "1.4.0"
BRINGUP_ANCHOR = "## Appendix A — probe output excerpts (2026-10-15)\n"
REF_HISTORY_ANCHOR = "; the drift script above counts, so re-run it rather than trusting this figure."
REF_HISTORY_MARKER = "with commit-signing K2's `tests/test_configure_commit_signing.py`"
BRINGUP_SECTION = f"""## 19. Commit signing for the terminal and the IDEs (v1.4.0, 2026-10-20)

`{PLAN}` (the signing plan; VALIDATED after two consensus rounds) extends arc B to the owner's IDE commits, from Cursor and VS Code. It also replaces the git-config half of B4. Where it and this plan disagree on B3, B4 or B5, the signing plan wins.

### 19.1 Task changes

| Task | Change |
|---|---|
| B4 | **Split.** **B4a (AGENT, at the owner's request on 2026-10-19):** `python3 {TOOL} --apply` writes the four signing values to `~/.config/git/juniper-signing.gitconfig`, and includes that file from `~/.gitconfig` with `[includeIf "gitdir/i:~/Development/python/Juniper/"]` rather than `git config --global` (signing plan S1). Applied on turing on 2026-10-20; every repo check passes. **B4b (OWNER):** the UID check, plus the touch policy as signing-plan S11 rules it |
| B2, B3 | Any `gpg --card-status` writes the card's stubs, and signing is live once the public key (B2) is there too. So no card goes into turing until C8 is installed, the guard rules (K12) are merged and re-installed, and the IDE-agent approvals (K13) are done. The touch policy is set at that first insertion, before B2 and B3 (signing plan §1, §9, §13) |
| B5 | Widened to the signing plan's I-SIGN matrix: the terminal, both Source Control views, both integrated terminals, an agent-session negative control, and IDE-agent prompt rows. It still depends on A3 |
| new | **Signing plan K12:** guard rules that deny `-c include.path=`, `--config-env` in both forms, signing-key writes at any scope, and writes to `.git/hooks/`, a repository's config, `~/.gitconfig`, `~/.config/git/` and the system gitconfigs; also the tool's `--apply`. **Signing plan K13:** IDE-agent approvals |

### 19.2 Errata

- **E-B4-KEY.** B4's `user.signingkey 'BA18D1A733B1831A!'` becomes the full fingerprint `B5619F58FDA4D94E2D73D8BABA18D1A733B1831A!`. It is the same subkey and yamaguchi's exact value, as B4's acceptance asks.
- **E-B4-SCOPE.** `git config --global` becomes the conditional include. Repositories outside the Juniper tree, and temp repositories under `$TMPDIR`, gain no signing requirement.
- **E-B4-GPG.** `gpg.program` is the literal `/usr/local/bin/gpg`, which is what `$(brew --prefix)/bin/gpg` evaluates to. It is absolute because an IDE launched from the Dock does not get the shell's PATH, and on turing `gpg2` exists only under the demoted MacPorts path.
- **E-G-SIGN.** Gate G-SIGN (§9.3) is evaluated inside the checkouts. It needs `{TOOL} --check` to exit 0 and I-SIGN T1–T5 to verify. `git config --global --get` cannot see an include.
- **E-ACTIVE.** From 2026-10-20, an owner commit in the Juniper tree on turing fails closed ("gpg failed to sign the data") until B2 and B3 are done. Before, it would have landed unsigned and so been unmergeable. Agent sessions are unaffected (D11).
- **E-D11-S.** D11's environment does not stop an explicit `-S`, `-c include.path=` or `--config-env=commit.gpgsign=…`, measured with a fake gpg. So no card goes into turing until C8 and K12 are in place, and D11 item 2's touch policy follows the S11 ruling.
- **E-D5-LINE.** The §17.2 D5 row's `~/.bash_profile:87` is `:92` as of 2026-10-19.

"""


class AnchorError(Exception):
    pass


def insert_after(text: str, anchor: str, addition: str, marker: str) -> str:
    if marker in text:
        return text
    if text.count(anchor) != 1:
        raise AnchorError(f"anchor occurs {text.count(anchor)} times (need 1): {anchor[:80]!r}")
    return text.replace(anchor, anchor + addition)


def insert_before(text: str, anchor: str, addition: str, marker: str) -> str:
    if marker in text:
        return text
    if text.count(anchor) != 1:
        raise AnchorError(f"anchor occurs {text.count(anchor)} times (need 1): {anchor[:80]!r}")
    return text.replace(anchor, addition + anchor)


def replace_once(text: str, old: str, new: str, marker: str) -> str:
    if marker in text:
        return text
    if text.count(old) != 1:
        raise AnchorError(f"text occurs {text.count(old)} times (need 1): {old[:80]!r}")
    return text.replace(old, new)


def edit_changelog(text: str) -> str:
    start = text.find("## [Unreleased]")
    if start < 0:
        raise AnchorError("no ## [Unreleased] heading")
    end = text.find("\n## [", start + 1)
    section = text[start:end if end >= 0 else len(text)]
    if "**Commit signing for the terminal and the IDEs**" in section:
        return text
    if section.count("\n### Added\n\n") != 1:
        raise AnchorError(f"the Unreleased section has {section.count(chr(10) + '### Added' + chr(10) + chr(10))} '### Added' headings (need 1)")
    section = section.replace("\n### Added\n\n", "\n### Added\n\n" + CHANGELOG_ENTRY + "\n", 1)
    return text[:start] + section + (text[end:] if end >= 0 else "")


def suite_count(reference: str) -> int:
    return len(re.findall(r"(?m)^python3 -m unittest -v tests/test_\S+\.py$", reference))


def edit_reference_history(text: str) -> str:
    """Add this suite's step to the run-list intro's count history (the house convention)."""
    if REF_HISTORY_MARKER in text:
        return text
    if text.count(REF_HISTORY_ANCHOR) != 1:
        raise AnchorError(f"the count-history sentence occurs {text.count(REF_HISTORY_ANCHOR)} times (need 1)")
    return text.replace(REF_HISTORY_ANCHOR, f", **{suite_count(text)}** {REF_HISTORY_MARKER}" + REF_HISTORY_ANCHOR)


def edit_bringup(text: str) -> str:
    if "\n## 19. Commit signing for the terminal and the IDEs" in text:
        return text
    if BRINGUP_PREREQ not in text:
        raise AnchorError("the bring-up plan has no §18 yet: wait for the Session 3 record to merge (it takes §18 / v1.3.0)")
    if "\n## 19. " in text:
        raise AnchorError("the bring-up plan already has another §19: renumber this section first")
    match = BRINGUP_VERSION_RE.search(text)
    if match is None or len(BRINGUP_VERSION_RE.findall(text)) != 1:
        raise AnchorError("the bring-up plan's Version line was not found exactly once")
    old, rest = match.group("ver"), match.group("rest")
    if old != "1.3.0":
        raise AnchorError(f"the bring-up plan is at v{old}, not v1.3.0: renumber this edit first")
    rest = rest.replace("§17 or §18 disagrees", "§17, §18 or §19 disagrees")
    line = f"- **Version**: {BRINGUP_VERSION} — v{old} plus the commit-signing extension of arc B (§19, 2026-10-20). v{old} was {rest}"
    text = text[: match.start()] + line + text[match.end():]
    return insert_before(text, BRINGUP_ANCHOR, BRINGUP_SECTION, "## 19. Commit signing for the terminal and the IDEs")


def edit_agents(text: str, reference: str) -> str:
    text = replace_once(text, AGENTS_OLD, AGENTS_NEW, "`util/configure_commit_signing.py`. Plans:")
    count = suite_count(reference)
    text, n = re.subn(r"full ordered list of \d+ `python3 -m unittest`", f"full ordered list of {count} `python3 -m unittest`", text)
    if n != 1:
        raise AnchorError(f"the suite-count sentence occurs {n} times (need 1)")
    today = datetime.datetime.now(datetime.timezone.utc).date().isoformat()
    text, n = re.subn(r"(?m)^\*\*Last Updated\*\*: \d{4}-\d{2}-\d{2}$", f"**Last Updated**: {today}", text)
    if n != 1:
        raise AnchorError(f"the Last Updated line occurs {n} times (need 1)")
    return text


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=str(REPO))
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    base = Path(args.base)
    paths = {name: base / name for name in (".github/workflows/ci.yml", ".github/workflows/main-verify.yml", "docs/REFERENCE.md", "CHANGELOG.md", "AGENTS.md", BRINGUP, MACOS_GATE)}
    texts = {name: path.read_text(encoding="utf-8") for name, path in paths.items()}
    try:
        new = dict(texts)
        ci = insert_after(texts[".github/workflows/ci.yml"], CI_ANCHOR, CI_BLOCK, "python3 -m unittest -v tests/test_configure_commit_signing.py")
        ci = replace_once(ci, MACOS_SUITES_ANCHOR, MACOS_SUITES_NEW, "home_path_literal_check configure_commit_signing")
        new[".github/workflows/ci.yml"] = replace_once(ci, MACOS_PATHS_ANCHOR, MACOS_PATHS_NEW, "util/home_path_literal_check.py util/configure_commit_signing.py")
        new[MACOS_GATE] = replace_once(texts[MACOS_GATE], MACOS_GATE_ANCHOR, MACOS_GATE_NEW, '"configure_commit_signing",')
        new[".github/workflows/main-verify.yml"] = insert_after(texts[".github/workflows/main-verify.yml"], BATTERY_ANCHOR, BATTERY_LINE, "tests/test_configure_commit_signing.py")
        ref = insert_after(texts["docs/REFERENCE.md"], REF_RUN_ANCHOR, REF_RUN_LINE, REF_RUN_LINE)
        ref = insert_after(ref, REF_SUITE_ANCHOR, REF_SUITE_BULLET, "- `tests/test_configure_commit_signing.py` --")
        ref = insert_after(ref, REF_UTIL_ANCHOR, REF_UTIL_BULLET, "- `util/configure_commit_signing.py` --")
        new["docs/REFERENCE.md"] = replace_once(ref, REF_MACOS_OLD, REF_MACOS_NEW, "the nine host-tooling suites")
        new["CHANGELOG.md"] = edit_changelog(texts["CHANGELOG.md"])
        new["AGENTS.md"] = edit_agents(texts["AGENTS.md"], new["docs/REFERENCE.md"])
        new["docs/REFERENCE.md"] = edit_reference_history(new["docs/REFERENCE.md"])
        new[BRINGUP] = edit_bringup(texts[BRINGUP])
    except AnchorError as exc:
        print(f"ANCHOR: {exc}", file=sys.stderr)
        return 2
    changed = [name for name in paths if new[name] != texts[name]]
    for name in changed:
        print(f"{'would change' if args.check else 'changed'}: {name}")
        if not args.check:
            paths[name].write_text(new[name], encoding="utf-8")
    if not changed:
        print("nothing to do: every edit is already present")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
