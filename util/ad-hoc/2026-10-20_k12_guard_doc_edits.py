"""
Apply the K12 guard-rules PR's edits to the shared files, idempotently, against any copy of them.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: ad-hoc — landing helper (commit-signing plan task K12)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md (S9, K12);
         util/claude_agent_guard.py; tests/test_claude_agent_guard.py;
         util/ad-hoc/2026-10-19_commit_signing_shared_file_edits.py (the K2-K4 counterpart)

Why: the shared files take concurrent whole-file uploads, so each upload is built by running this against a
FRESH `origin/main` copy at upload time (the juniper-ml#2262 revert class). Every edit has a marker (skip
when present) and an anchor that must occur exactly once. The files: `.github/workflows/ci.yml`,
`docs/REFERENCE.md`, `CHANGELOG.md` and the commit-signing plan (its S9 sentence, §14.4 and §15, which the
K2-K4 PR landed with the 1.0.0 guard's line numbers).

Usage:
    python3 -I util/ad-hoc/2026-10-20_k12_guard_doc_edits.py [--base DIR] [--check] --mutants N/M

`--mutants N/M` is the K12 mutation result to record (for example `18/18`).

Exit codes:

- 0: applied, or nothing to do;
- 1: `--check` found pending edits;
- 2: an anchor was missing or not unique.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PLAN = "notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md"
MUTATION = "util/ad-hoc/2026-10-20_k12_guard_mutation_check.py"

CI_OLD = (
    "          # gh auth, deploy keys, gh api write/field flags in any position, keychain dumps and\n"
    "          # user-level .claude settings edits. Payloads pipe through it with a temp\n"
)
CI_NEW = (
    "          # gh auth, deploy keys, gh api write/field flags in any position, keychain dumps,\n"
    "          # user-level .claude settings edits, and (commit-signing K12) changes to the owner's signing\n"
    "          # configuration and git hooks: -c include.path= / gpg.program, --config-env, signing-key\n"
    "          # git config writes, ~/.gitconfig, ~/.config/git, the system gitconfigs and .git/hooks. Payloads pipe\n"
    "          # through it with a temp\n"
)
REF_UTIL_OLD = "It denies by rule id (`--list-rules` lists the 15) and otherwise prints nothing"
REF_UTIL_NEW = "It denies by rule id (`--list-rules` lists the 17) and otherwise prints nothing"
REF_UTIL_TAIL_OLD = "the known gaps are listed in its docstring. Turing bring-up C8. Tests: `tests/test_claude_agent_guard.py`.\n"
REF_UTIL_TAIL_NEW = (
    "the known gaps are listed in its docstring.\n"
    f"  - **K12** (`{PLAN}`, S9) adds two rules that guard the owner's signing configuration.\n"
    "  - **`GIT-SIGNING-CONFIG` (Bash)** denies:\n"
    "    - `git -c include.*` / `includeIf.*` / `gpg.program` / `gpg.<format>.program`;\n"
    "    - `git --config-env` with any key, as `--config-env=<key>=<var>` or `--config-env <key>=<var>`;\n"
    "    - a `git config` write at any scope of `gpg.*`, `user.signingkey`, `commit.gpgsign`, `tag.gpgsign`, `include*`, "
    "`core.hooksPath`, `core.fsmonitor` or `core.sshCommand`;\n"
    "    - `git config --edit`, and removing or renaming those sections;\n"
    "    - any mention of `~/.gitconfig`, `~/.config/git`, a system gitconfig or a `.git/hooks` path;\n"
    "    - `util/configure_commit_signing.py --apply` / `--remove` without `--dry-run`.\n"
    "  - **`GIT-SIGNING-FILE` (writers)** denies writes to `~/.gitconfig`, `~/.config/git/`, a repository's `.git/config` "
    "or `config.worktree`, `.git/hooks/`, and the system gitconfigs (`/usr/local/etc/gitconfig`, `/opt/homebrew/etc/gitconfig`, "
    "`/etc/gitconfig`). Reads stay allowed.\n"
    "  - Turing bring-up C8. Tests: `tests/test_claude_agent_guard.py`.\n"
)
REF_SUITE_ANCHOR = "`util/ad-hoc/2026-10-17_turing_c8_guard_review_probe.py` is the lead's independent black-box review (71 of 71 cases).\n"
CHANGELOG_ENTRY = (
    f"- **The agent guard protects the owner's signing configuration (K12)** (`{PLAN}`, S9). With the YubiKey stubs\n"
    "  learned, an agent that could rewrite the owner's signing configuration could obtain the owner's signature. It could\n"
    "  point `gpg.program` or `core.hooksPath` at its own program, plant a repository-local key that outranks the include,\n"
    "  drop a `post-commit` hook inside a cached-touch window, or re-enable signing past D11 with `git -c include.path=` or\n"
    "  `--config-env`.\n"
    "  - `util/claude_agent_guard.py` 1.1.0 adds two rules:\n"
    "    - `GIT-SIGNING-CONFIG` (Bash) denies those forms. It also denies signing-key `git config` writes at any scope,\n"
    "      `git config --edit`, any mention of `~/.gitconfig`, `~/.config/git`, a system gitconfig or `.git/hooks`, and\n"
    "      `util/configure_commit_signing.py --apply` / `--remove` without `--dry-run`.\n"
    "    - `GIT-SIGNING-FILE` (the file writers) denies writes to the same files. Reads stay allowed.\n"
    "  - `tests/test_claude_agent_guard.py` pins 63 Bash cases (42 denied, 21 allowed) and 18 file cases (10 denied, 8\n"
    "    allowed), and the self-test runs 40 checks.\n"
    f"  - `{MUTATION}` kills @MUTANTS@ mutants, each by its own pin test.\n"
    "  - The owner re-runs `bash util/install_claude_agent_guard.bash --apply` (task C8) from an up-to-date `main` to install\n"
    "    the new copy. No YubiKey goes into turing until then: the first `gpg --card-status` writes the card stubs (plan §1).\n"
)


# The plan (landed by the K2-K4 PR) cites the 1.0.0 guard's lines; K12 moves them and closes S9's gap.
PLAN_S9_OLD = "The guard checks only `-c *gpgsign*` (`util/claude_agent_guard.py:1105-1111`)."
PLAN_S9_NEW = (
    "Before K12 the guard checked only `-c *gpgsign*` (`util/claude_agent_guard.py:1105-1111` in 1.0.0). "
    "In 1.1.0, GIT-SIGNING-CONFIG denies both forms (:1155-1164)."
)
PLAN_REF_OLD = "- `util/claude_agent_guard.py`: CRED-PATH-BASH (:152), GPG-SIGN (:157), the `-c`/`--config-env` handling (:1105-1111)\n"
PLAN_REF_NEW = (
    "- `util/claude_agent_guard.py` 1.1.0: CRED-PATH-BASH (:165), GPG-SIGN (:170), K12's GIT-SIGNING-CONFIG (:177-186) and "
    "GIT-SIGNING-FILE (:189), the `-c`/`--config-env` handling (:1155-1164)\n"
)
PLAN_EVIDENCE_OLD = "The K12 guard rules carry their own evidence, recorded with that PR.\n"
PLAN_EVIDENCE_NEW = (
    f"**K12.** `{MUTATION}` re-introduces one defect per mutant into a copy of the guard, as above. It kills "
    "@KILLED@ of @TOTAL@ mutants (K1–K18), each by its own pin. The guard's `--self-test` runs 40 of 40 checks under "
    "JuniperPython and `/usr/bin/python3` 3.9.6.\n"
)


class AnchorError(Exception):
    pass


def replace_once(text: str, old: str, new: str, marker: str) -> str:
    if marker in text:
        return text
    if text.count(old) != 1:
        raise AnchorError(f"text occurs {text.count(old)} times (need 1): {old[:80]!r}")
    return text.replace(old, new)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", default=str(REPO))
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--mutants", required=True, help="the K12 mutation result, N/M")
    args = ap.parse_args(argv)
    if not re.fullmatch(r"\d+/\d+", args.mutants):
        print("--mutants must look like 15/15", file=sys.stderr)
        return 2
    killed, total = args.mutants.split("/")
    base = Path(args.base)
    names = (".github/workflows/ci.yml", "docs/REFERENCE.md", "CHANGELOG.md", PLAN)
    texts = {name: (base / name).read_text(encoding="utf-8") for name in names}
    try:
        new = dict(texts)
        plan = replace_once(texts[PLAN], PLAN_S9_OLD, PLAN_S9_NEW, "Before K12 the guard checked only")
        plan = replace_once(plan, PLAN_REF_OLD, PLAN_REF_NEW, "`util/claude_agent_guard.py` 1.1.0: CRED-PATH-BASH")
        evidence = PLAN_EVIDENCE_NEW.replace("@KILLED@", killed).replace("@TOTAL@", total)
        new[PLAN] = replace_once(plan, PLAN_EVIDENCE_OLD, evidence, f"**K12.** `{MUTATION}`")
        new[".github/workflows/ci.yml"] = replace_once(texts[".github/workflows/ci.yml"], CI_OLD, CI_NEW, "(commit-signing K12) changes to the owner's signing")
        ref = replace_once(texts["docs/REFERENCE.md"], REF_UTIL_OLD, REF_UTIL_NEW, "`--list-rules` lists the 17")
        ref = replace_once(ref, REF_UTIL_TAIL_OLD, REF_UTIL_TAIL_NEW, "  - **K12** (`")
        suite_tail = (
            f" **K12** pins `GIT-SIGNING-CONFIG` (63 Bash cases: 42 denied, 21 allowed) and `GIT-SIGNING-FILE` (18 file cases: 10 denied, 8 allowed), and the self-test"
            f" runs 40 checks; `{MUTATION}` kills {killed} of {total} mutants, each by its own pin.\n"
        )
        new["docs/REFERENCE.md"] = replace_once(ref, REF_SUITE_ANCHOR, REF_SUITE_ANCHOR[:-1] + suite_tail, "**K12** pins `GIT-SIGNING-CONFIG`")
        changelog = texts["CHANGELOG.md"]
        start = changelog.find("## [Unreleased]")
        end = changelog.find("\n## [", start + 1)
        section = changelog[start:end if end >= 0 else len(changelog)]
        if "**The agent guard protects the owner's signing configuration (K12)**" not in section:
            if section.count("\n### Added\n\n") != 1:
                raise AnchorError("the Unreleased section does not have exactly one '### Added'")
            entry = CHANGELOG_ENTRY.replace("@MUTANTS@", f"{killed} of {total}")
            section = section.replace("\n### Added\n\n", "\n### Added\n\n" + entry + "\n", 1)
            changelog = changelog[:start] + section + (changelog[end:] if end >= 0 else "")
        new["CHANGELOG.md"] = changelog
    except AnchorError as exc:
        print(f"ANCHOR: {exc}", file=sys.stderr)
        return 2
    changed = [name for name in names if new[name] != texts[name]]
    for name in changed:
        print(f"{'would change' if args.check else 'changed'}: {name}")
        if not args.check:
            (base / name).write_text(new[name], encoding="utf-8")
    if not changed:
        print("nothing to do: every edit is already present")
    return 1 if args.check and changed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
