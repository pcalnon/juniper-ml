#!/usr/bin/env python3
"""
Register the ml-code carrier's suites and descriptions: ci.yml, main-verify.yml, docs/REFERENCE.md and AGENTS.md.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-08
Status: ad-hoc — one-off (flood-4 round-2 ml-code carrier build)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: BRIEF_COMMON_R2 rules 7, 8 and 10 (re-derive registrations on main; bump each doc once; AGENTS.md
         Last Updated). Drafts: #2502 #2504 #2505 #2508 #2513 (their registration hunks, re-applied by anchor).

Usage: python3 2026-11-08_flood4r2_ml_code_wire.py   (run from the worktree root)

Every edit names an exact anchor that must occur exactly once; the script refuses to write anything
otherwise. Idempotent: a file whose edits are already present is left as it is.
"""
import sys
from pathlib import Path

TODAY = "2026-11-09"  # UTC date of the build
CI = ".github/workflows/ci.yml"
MV = ".github/workflows/main-verify.yml"
REF = "docs/REFERENCE.md"
AGENTS = "AGENTS.md"

NEW_SUITES = (
    "tests/test_prompt_file_later_flag.py",
    "tests/test_claudey_empty_prompt_file_env.py",
    "tests/test_predict_merge_inherited_git_env.py",
    "tests/test_claude_agent_guard_git_sign_abbrev.py",
    "tests/test_claude_agent_guard_push_signed_abbrev.py",
)

CI_EDITS = [
    (
        "          python3 -m unittest -v tests/test_wake_the_claude.py\n          # claude_interactive.bash (`claudey`): DEBUG-forced\n",
        "          python3 -m unittest -v tests/test_wake_the_claude.py\n"
        "          # tests/test_prompt_file_later_flag.py: a later --file / --path that does not resolve must not\n"
        "          # send the prompt an earlier flag resolved.\n"
        "          python3 -m unittest -v tests/test_prompt_file_later_flag.py\n"
        "          # claude_interactive.bash (`claudey`): DEBUG-forced\n",
    ),
    (
        "          python3 -m unittest -v tests/test_claude_interactive.py\n          # Env-repr safety: lint gate forbidding raw os.environ-derived\n",
        "          python3 -m unittest -v tests/test_claude_interactive.py\n"
        "          # An exported empty CLAUDE_PROMPT_FILE / CLAUDE_PROMPT_PATH is the env form of\n"
        '          # -f "${HANDOFF}" with HANDOFF unset: claudey must refuse it, not send the default prompt.\n'
        "          python3 -m unittest -v tests/test_claudey_empty_prompt_file_env.py\n"
        "          # Env-repr safety: lint gate forbidding raw os.environ-derived\n",
    ),
    (
        "          python3 -m unittest -v tests/test_predict_merge.py\n          # tests/test_fleet_supervisor_contract.py:",
        "          python3 -m unittest -v tests/test_predict_merge.py\n"
        "          # tests/test_predict_merge_inherited_git_env.py: GIT_SHALLOW_FILE, GIT_GRAFT_FILE, and\n"
        "          # GIT_INDEX_FILE inherited from a hook must not change the predicted verdict or the source index.\n"
        "          python3 -m unittest -v tests/test_predict_merge_inherited_git_env.py\n"
        "          # tests/test_fleet_supervisor_contract.py:",
    ),
    (
        "          # tests/test_claude_agent_guard_brace_cap.py: brace expansion keeps a credential\n"
        "          # name in the 64th alternative and drops the 65th. A numeric range of 64 includes\n"
        "          # both ends; one past the cap drops the far end inside _brace_range.\n"
        "          python3 -m unittest -v tests/test_claude_agent_guard_brace_cap.py\n",
        "          # tests/test_claude_agent_guard_brace_cap.py: brace expansion keeps a credential\n"
        "          # name in the 64th alternative, and a word past the cap (a list, a range or a\n"
        "          # product of groups) fails closed, exit 2, instead of being judged on its first 64.\n"
        "          python3 -m unittest -v tests/test_claude_agent_guard_brace_cap.py\n"
        "          # tests/test_claude_agent_guard_git_sign_abbrev.py: git 2.53 runs a prefix of\n"
        "          # --gpg-sign (--g on commit and merge signs) and of tag --sign / --local-user\n"
        "          # (--si signs, --lo selects the key). The full spellings are in the suite above.\n"
        "          # --no-gpg-sign, --signoff, rebase/cherry-pick --skip, and tag --sort stay allowed.\n"
        "          python3 -m unittest -v tests/test_claude_agent_guard_git_sign_abbrev.py\n"
        "          # tests/test_claude_agent_guard_push_signed_abbrev.py: git 2.53 runs an unambiguous\n"
        "          # prefix of `git push --signed` (`--si`, `--sign=true`, `--si=if-asked`) as a signed\n"
        "          # push. `--s` is ambiguous with `--set-upstream` and stays allowed, and so does\n"
        "          # `--si=false`.\n"
        "          python3 -m unittest -v tests/test_claude_agent_guard_push_signed_abbrev.py\n",
    ),
]

MV_EDITS = [
    (
        "          python3 -m unittest -v tests/test_wake_the_claude.py\n          python3 -m unittest -v tests/test_claude_interactive.py\n",
        "          python3 -m unittest -v tests/test_wake_the_claude.py\n"
        "          python3 -m unittest -v tests/test_prompt_file_later_flag.py\n"
        "          python3 -m unittest -v tests/test_claude_interactive.py\n"
        "          python3 -m unittest -v tests/test_claudey_empty_prompt_file_env.py\n",
    ),
    (
        "          python3 -m unittest -v tests/test_ci_fleet_pr_lint.py\n",
        "          python3 -m unittest -v tests/test_ci_fleet_pr_lint.py\n          python3 -m unittest -v tests/test_predict_merge_inherited_git_env.py\n",
    ),
]

GUARD_TABLE_SENTENCE = (
    " **Flood-4 round 2** pins GnuPG's two-letter floor (`GPG_MIN_ABBREV`) in the GnuPG table, re-derived on GnuPG 2.4.8"
    " (an empty homedir, no agent): one-letter `--s`, `--c`, `--d`, `--l` and `--e` stay allowed, since GnuPG rejects each as ambiguous;"
    " `--cl`, `--cle`, `--ls`, `--lsi` and `--det`, which GnuPG runs as clear-sign, lsign-key and detach-sign, and `--clea` are denied `GPG-SIGN`;"
    " `--li`, `--ex`, `--ca`, `--expo`, `--list=keys` and `--LIST` are denied `GPG-SECRET`; `--export` stays allowed (juniper-ml#2493, and juniper-ml#2485 rewritten)."
)

BRACE_OLD = (
    "- `tests/test_claude_agent_guard_brace_cap.py` -- Turing bring-up C8: `util/claude_agent_guard.py`'s brace expansion at its cap, `MAX_BRACE_ALTERNATIVES` (64), "
    "which `tests/test_claude_agent_guard.py` never reaches. A brace list of exactly 64 alternatives keeps its last slot, so a `.ssh` name assembled there is denied as "
    "`CRED-PATH-BASH` although the source word does not contain `.ssh`; with 65 alternatives the last one is dropped and the command is not denied on it. A numeric range "
    "of exactly 64 includes both ends in either direction, and one past the cap drops the far end inside `_brace_range`, also when `brace_expand` is given a higher limit. "
    "Carried from juniper-ml#2466.\n"
)

BRACE_NEW = (
    "- `tests/test_claude_agent_guard_brace_cap.py` -- Turing bring-up C8: `util/claude_agent_guard.py`'s brace expansion at its cap, `MAX_BRACE_ALTERNATIVES` (64), "
    "which `tests/test_claude_agent_guard.py` never reaches. A brace list of exactly 64 alternatives keeps its last slot, so a `.ssh` or `.gnupg` name assembled there is "
    "denied as `CRED-PATH-BASH` although the source word does not contain it. A word past the cap fails closed (owner ruling, 2026-11-08): 65 alternatives, and 10,000 or "
    "100,000, raise `MalformedInput` in the analyzer, and the hook exits 2 with an empty stdout for a Bash command, a Glob or Grep pattern and a Serena include glob. "
    "Until then the 65th alternative was dropped and the command passed. A product of groups counts as its product: six `{a,b}` are judged, a seventh is refused. "
    "A numeric range of exactly 64 includes both ends in either direction; one past the cap is refused inside `_brace_range`, also when `brace_expand` is given a "
    "higher limit, and `{1..1000000000000}` is refused without being built. `for i in {1..100}` is refused; `$(seq 1 100)` is not. Carried from juniper-ml#2466, and "
    "inverted under the ruling.\n"
    "- `tests/test_claude_agent_guard_git_sign_abbrev.py` -- `GPG-SIGN` for git's long-option prefixes, re-derived on git 2.53.0 with a recording `gpg.program` stub: "
    "`--g`, `--gp`, `--gpg`, `--gpg-s` and `--gpg=KEY` are `--gpg-sign` on `commit`, and the suite also denies them on `merge`, `rebase`, `cherry-pick`, `revert`, `am`, "
    "`pull` and `commit-tree`; `git tag --si`, `--sig`, `--lo`, `--loc` and `--local-u` are `--sign` and `--local-user`. `git tag --si=` (git refuses it) and "
    "`cherry-pick` / `revert --gpg` (git prints the usage) are denied too. Allowed: `--signoff`, `-s`, `--no-gpg-sign`, `--no-gpg`, `--no-g`, `git tag --s` (ambiguous "
    "with `--sort`), `--l` (with `--list`), `--so`, `--sort`, `--no-sign` and `--signoff`, `rebase` / `cherry-pick` / `am` / `revert --skip`, and `merge "
    "--verify-signatures` / `--signoff`. Carried from juniper-ml#2502.\n"
    "- `tests/test_claude_agent_guard_push_signed_abbrev.py` -- `GPG-SIGN` for `git push --signed` prefixes, re-derived on git 2.53.0 against a local bare remote that "
    "advertises no push certificates: `--si`, `--sig`, `--sign`, `--signe`, `--signed`, `--sign=true`, `--signed=1` / `yes` / `on` / `YES` and `--si=if-asked` are "
    "denied, and so are `--signed=`, `--si=` and `--signed=00` (git reads them as false) and `--signed=falsehood` (git refuses it). Allowed: `--s` (ambiguous with "
    "`--set-upstream`), `--se`, `--set-upstream`, `--si=false` / `0` / `no` / `off`, `--signed=false` / `FALSE` / `No` / `off` / `0`, `--no-signed`, `--no-si`, "
    "`--no-sig`, and `--SIGNED` / `--Si` (unknown options: git compares option names case-sensitively). Carried from juniper-ml#2508.\n"
)

WAKE_OLD = "- `tests/test_wake_the_claude.py` -- Regression tests for resume/session-id and argument handling in `wake_the_claude.bash`\n"
WAKE_NEW = (
    "- `tests/test_wake_the_claude.py` -- Regression tests for resume/session-id and argument handling in `wake_the_claude.bash`. It also pins the effort default "
    "(owner ruling, 2026-11-08): `--effort 0` sends `--effort max`, and `auto`, through any alias and in any case, sends no `--effort`, so Claude Code uses its own "
    "default. juniper-ml#2396 had made the default `auto`, which Claude Code ignores with a warning.\n"
    "- `tests/test_prompt_file_later_flag.py` -- A later `--file` or `--path` that does not resolve must not send the prompt an earlier flag resolved "
    "(`--file good.md --file missing.md`, `--path good.md --path emptydir`, and the `--file-name`, `-f`, `--file-path` and `-l` spellings): each exits 1 naming the "
    "later flag, and `claude` is never invoked. The later resolved flag is the prompt, and `--file <name> --path <dir>` still resolves in either order. Carried from "
    "juniper-ml#2505.\n"
    "- `tests/test_claudey_empty_prompt_file_env.py` -- An exported empty `CLAUDE_PROMPT_FILE` or `CLAUDE_PROMPT_PATH` is the environment form of `-f \"${HANDOFF}\"` "
    "with `HANDOFF` unset. `claudey` exits 1 with `Missing value for --file` or `--path` and does not launch, even when the other variable names a path. A `--file` on "
    "the command line replaces the empty variable. One space is forwarded. Both set are both forwarded, and both unset still send the default prompt. No Claude "
    "binary. Carried from juniper-ml#2504.\n"
)

PM_SUB_PREFIX = "  - Also covers docs-screen edges (header ignore / additions-only / non-`.md`), no-`.py` gate skip, and `repair`/`fix-first` heal tokens (juniper-ml#910)."
PM_ENTRY = (
    "- `tests/test_predict_merge_inherited_git_env.py` -- Inherited `GIT_SHALLOW_FILE`, `GIT_GRAFT_FILE`, and `GIT_INDEX_FILE` leave a behind branch "
    "`NEEDS-UPDATE-BRANCH` with true delta equal to the branch's own file, and leave the source index, HEAD, and refs unchanged. Before juniper-ml#2513 the shallow "
    "file made the merge exit 128 and the graft reported `MERGE-CLEAN`. Carried from juniper-ml#2513.\n"
)

TRIAGE_OLD = "It was `git clone --shared` until 2026-11-06, which turns its local mode off for a shallow source and then carries only local branches."
TRIAGE_NEW = (
    TRIAGE_OLD + " Scratch git commands drop inherited `GIT_DIR`, `GIT_INDEX_FILE`, `GIT_SHALLOW_FILE`, and `GIT_GRAFT_FILE`. A shallow-file path that names the branch "
    "tip otherwise makes `git merge` refuse unrelated histories. A graft that names `main` as that tip's parent otherwise reports `MERGE-CLEAN` and includes main's file "
    "in the true delta. `GIT_INDEX_FILE` left set would rewrite the source index."
)

UTIL_OLD = "  - Turing bring-up C8. Tests: `tests/test_claude_agent_guard.py`, `tests/test_claude_agent_guard_brace_cap.py`.\n"
UTIL_NEW = (
    "  - **1.3.0** (the Cursor flood-4 round-2 code carrier) fails closed on a brace expansion past its cap and denies the git and GnuPG prefixes that sign:\n"
    "    - **A brace expansion past `MAX_BRACE_ALTERNATIVES` (64) fails closed** (owner ruling, 2026-11-08). A word that needs more alternatives, as a list, a range "
    "or a product of groups, raises `MalformedInput`, and the hook exits 2, for a Bash word, a Glob or Grep pattern and a Serena include glob alike. It used to be "
    "judged on its first 64, so a `.ssh` or `.gnupg` spelled in alternative 65 passed. A list is counted before it is built and a range is sized arithmetically, so "
    "`{1..1000000}` is refused without being expanded. `for i in {1..100}` is refused too; `$(seq 1 100)` is not.\n"
    "    - **`GPG-SIGN` and GnuPG prefixes.** A long option counts from two letters (`GPG_MIN_ABBREV`): GnuPG 2.4.8 runs `--cl` as clear-sign, `--ls` as "
    "lsign-key and `--det` as detach-sign, and rejects every one-letter prefix of a denied option as ambiguous.\n"
    "    - **`GPG-SIGN` and git prefixes.** An unambiguous prefix of a signing option is the same request as the full option (git 2.53): `--g` is `--gpg-sign` on "
    "`commit`, `merge`, `rebase`, `am`, `pull` and `commit-tree`; `git tag --si` and `--lo` are `--sign` and `--local-user`; and `git push --si`, `--sign=true` and "
    "`--si=if-asked` request a signed push. `git tag --s` (with `--sort`), `git tag --l` (with `--list`) and `git push --s` (with `--set-upstream`) are ambiguous and "
    "stay allowed, as do `--no-gpg-sign`, `--signoff`, `--no-si` and a push value of `false`, `no`, `off` or `0` (any case), including `--si=false`.\n"
    "  - Turing bring-up C8. Tests: `tests/test_claude_agent_guard.py`, `tests/test_claude_agent_guard_brace_cap.py`, `tests/test_claude_agent_guard_git_sign_abbrev.py`, "
    "`tests/test_claude_agent_guard_push_signed_abbrev.py`.\n"
)

COUNT_OLD = "`tests/test_claude_agent_guard_brace_cap.py`, `tests/test_host_state_gate_boundaries.py`); the drift script above counts"
COUNT_NEW = (
    "`tests/test_claude_agent_guard_brace_cap.py`, `tests/test_host_state_gate_boundaries.py`), **237** on 2026-11-09 with the flood-4 round-2 code carrier's five ("
    + ", ".join("`%s`" % s for s in NEW_SUITES)
    + "); the drift script above counts"
)

HISTORY_ROW = (
    "| 0.6.65  | 2026-11-09 | Cursor flood-4 round-2 code carrier: the agent guard (1.3.0) fails closed on a brace expansion past its 64-alternative cap, and denies the git and "
    "GnuPG prefixes that sign (re-derived on git 2.53.0 and GnuPG 2.4.8); `wake_the_claude.bash` defaults to `--effort max` and sends no flag for `auto`; five suites "
    "registered (237); the brace-cap suite's description inverted |\n"
)


def apply(text: str, edits: list, name: str) -> str:
    for old, new in edits:
        if new in text:
            continue
        count = text.count(old)
        if count != 1:
            raise SystemExit("%s: anchor occurs %d times: %r" % (name, count, old[:90]))
        text = text.replace(old, new)
    return text


def ref_edits(text: str) -> str:
    edits = [
        ("**Version:** 0.6.64\n**Status:** Active\n**Last Updated:** 2026-11-07\n", "**Version:** 0.6.65\n**Status:** Active\n**Last Updated:** %s\n" % TODAY),
        ("**Last Updated:** 2026-11-07\n**Version:** 0.6.64\n**Maintainer:**", "**Last Updated:** %s\n**Version:** 0.6.65\n**Maintainer:**" % TODAY),
        (
            "\npython3 -m unittest -v tests/test_wake_the_claude.py\npython3 -m unittest -v tests/test_claude_interactive.py\n",
            "\npython3 -m unittest -v tests/test_wake_the_claude.py\npython3 -m unittest -v tests/test_prompt_file_later_flag.py\n"
            "python3 -m unittest -v tests/test_claude_interactive.py\npython3 -m unittest -v tests/test_claudey_empty_prompt_file_env.py\n",
        ),
        ("\npython3 -m unittest -v tests/test_predict_merge.py\n", "\npython3 -m unittest -v tests/test_predict_merge.py\npython3 -m unittest -v tests/test_predict_merge_inherited_git_env.py\n"),
        (
            "\npython3 -m unittest -v tests/test_claude_agent_guard_brace_cap.py\n",
            "\npython3 -m unittest -v tests/test_claude_agent_guard_brace_cap.py\npython3 -m unittest -v tests/test_claude_agent_guard_git_sign_abbrev.py\n"
            "python3 -m unittest -v tests/test_claude_agent_guard_push_signed_abbrev.py\n",
        ),
        (COUNT_OLD, COUNT_NEW),
        (WAKE_OLD, WAKE_NEW),
        (BRACE_OLD, BRACE_NEW),
        (TRIAGE_OLD, TRIAGE_NEW),
        (UTIL_OLD, UTIL_NEW),
    ]
    text = apply(text, edits, REF)
    # the predict_merge entry goes AFTER the existing entry's indented sub-bullet (the draft put it between them)
    if PM_ENTRY not in text:
        if text.count(PM_SUB_PREFIX) != 1:
            raise SystemExit("REFERENCE: predict_merge sub-bullet anchor count %d" % text.count(PM_SUB_PREFIX))
        at = text.index(PM_SUB_PREFIX)
        end = text.index("\n", at) + 1
        text = text[:end] + PM_ENTRY + text[end:]
    # the GnuPG-floor sentence closes the test_claude_agent_guard.py entry's line
    if GUARD_TABLE_SENTENCE not in text:
        prefix = "- `tests/test_claude_agent_guard.py` -- Turing bring-up C8 ("
        if text.count(prefix) != 1:
            raise SystemExit("REFERENCE: guard entry anchor count %d" % text.count(prefix))
        at = text.index(prefix)
        end = text.index("\n", at)
        text = text[:end] + GUARD_TABLE_SENTENCE + text[end:]
    # a Version History row for this bump, after 0.6.64's
    if HISTORY_ROW not in text:
        prefix = "| 0.6.64  | 2026-11-07 |"
        if text.count(prefix) != 1:
            raise SystemExit("REFERENCE: 0.6.64 history row count %d" % text.count(prefix))
        at = text.index(prefix)
        end = text.index("\n", at) + 1
        text = text[:end] + HISTORY_ROW + text[end:]
    return text


def main() -> int:
    root = Path.cwd()
    plan = {
        CI: lambda t: apply(t, CI_EDITS, CI),
        MV: lambda t: apply(t, MV_EDITS, MV),
        REF: ref_edits,
        AGENTS: lambda t: apply(
            t,
            [
                ("**Last Updated**: 2026-11-08\n", "**Last Updated**: %s\n" % TODAY),
                ("# Run all tests -- the full ordered list of 232 `python3 -m unittest`", "# Run all tests -- the full ordered list of 237 `python3 -m unittest`"),
            ],
            AGENTS,
        ),
    }
    staged = {}
    for rel, fn in plan.items():
        before = (root / rel).read_text(encoding="utf-8")
        staged[rel] = (before, fn(before))
    for rel, (before, after) in staged.items():
        if after != before:
            (root / rel).write_text(after, encoding="utf-8")
        print("%-40s %s" % (rel, "updated" if after != before else "unchanged"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
