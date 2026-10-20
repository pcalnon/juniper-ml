"""
Apply turing bring-up G6's edits to the shared files, idempotently: the git-remote-alias pre-push hook.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: ad-hoc — one-off (turing bring-up task G6: the G-ALIAS gate at push time)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task G6, gate G-ALIAS,
         §9.2 gate placement; §17.3 E-LAND-2); util/git_remote_alias_check.py (task G2, which G6 runs);
         util/ad-hoc/2026-10-20_turing_g5_apply.py (the pattern this follows)

Why: G6 lands through the GitHub API as whole-file uploads of four files that every other PR shares:
.pre-commit-config.yaml, ci.yml, docs/REFERENCE.md and CHANGELOG.md. An upload built from an older base
silently reverts whatever main gained since (E-LAND-2). So the edits live here, keyed on anchors, and are
re-applied to a fresh origin/main copy right before the upload.

The edits:
- .pre-commit-config.yaml gains the `git-remote-alias` local hook: `python3 util/git_remote_alias_check.py
  --check --if-configured` at the pre-push stage, with `pass_filenames: false` and `always_run: true`.
  `minimum_pre_commit_version` rises from 3.0.0 to 3.2.0, the release that named the stage `pre-push`.
  `default_stages: [pre-commit]` keeps every other hook at commit time: a hook with no `stages` runs at every
  stage, so without it a push re-runs the whole commit suite and the CI smoke step lints the whole tree.
  check-added-large-files and isort get `stages: [pre-commit]` of their own: their upstream manifests list
  pre-push, and a manifest's `stages` overrides default_stages.
- ci.yml's Pre-commit job runs the pre-push stage once as a smoke test. A runner has no github_juniper-*
  alias, so the hook must skip there.
- docs/REFERENCE.md: the hook's row in § Pre-commit Hook Reference, the opt-in install command in its
  setup block, and a sentence on the hook-config pins in the G2 suite's Test Suite Reference entry.
- CHANGELOG.md: an [Unreleased] / Added entry.

Each edit has a marker. When the marker is already present the edit is skipped; otherwise its anchor
must occur exactly once. A re-run on a newer main therefore applies cleanly or stops loudly.

Usage:
    python3 -I util/ad-hoc/2026-10-20_turing_g6_apply.py [--root REPO_ROOT] [--dry-run]

Exit 0 = every edit applied or already present; 1 = an anchor is missing or ambiguous (nothing written).
"""

import argparse
import sys
from pathlib import Path

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
CI = ".github/workflows/ci.yml"
PRE_COMMIT = ".pre-commit-config.yaml"
REFERENCE = "docs/REFERENCE.md"
STAGE_RUN = "pre-commit run --hook-stage pre-push git-remote-alias --all-files"


def edits():
    """(path, marker, anchor, replacement). The replacement keeps the anchor and adds the G6 text."""
    hook = (
        "\n"
        "  # ═══════════════════════════════════════════════════════════════════════════\n"
        "  # G-ALIAS at push time (turing bring-up G6): every Juniper checkout must reach\n"
        "  # GitHub through its own github_juniper-<repo> ssh alias. The hook runs\n"
        "  # util/git_remote_alias_check.py (task G2) over all 10 checkouts, at the\n"
        "  # pre-push stage only, so each host opts in with\n"
        "  #   pre-commit install --hook-type pre-push\n"
        "  # --if-configured exits 0 where ~/.ssh/config defines no github_juniper-*\n"
        "  # alias, so CI and hosts without the aliases pass; ci.yml's Pre-commit job runs\n"
        "  # the stage as a smoke test. Where the aliases exist, an origin that bypasses\n"
        "  # its alias, a missing checkout or a key not at mode 600 blocks the push.\n"
        "  # ═══════════════════════════════════════════════════════════════════════════\n"
        "  - repo: local\n"
        "    hooks:\n"
        "      - id: git-remote-alias\n"
        "        name: Juniper checkouts use their per-repo ssh alias (G6, G-ALIAS)\n"
        "        entry: python3 util/git_remote_alias_check.py --check --if-configured\n"
        "        language: system\n"
        "        stages: [pre-push]\n"
        "        pass_filenames: false\n"
        "        always_run: true\n"
    )
    ci_step = (
        "            pre-commit run --all-files --show-diff-on-failure\n"
        "          fi\n"
        "\n"
        "      - name: Run the pre-push stage (G6 smoke)\n"
        "        # Turing bring-up G6. The git-remote-alias hook runs only at the pre-push stage, which the\n"
        "        # run above never reaches. On a runner it must skip: ~/.ssh/config defines no\n"
        "        # github_juniper-* alias, so util/git_remote_alias_check.py --check --if-configured exits 0.\n"
        "        # The hook is named, so a hook that later joins the stage cannot turn this into a whole-tree\n"
        "        # lint run; and a git-remote-alias that left the stage fails here (\"No hook with id\").\n"
        f"        run: {STAGE_RUN}\n"
    )
    default_stages = (
        "\n"
        "# Hooks run at commit time unless they name their stage. Without this, every hook\n"
        "# would also run at the pre-push stage that the git-remote-alias hook (G6) needs:\n"
        "# a push would re-run the whole commit suite, and ci.yml's pre-push smoke step\n"
        "# would lint the whole tree. 3.2.0 is the release that named the stages pre-*.\n"
        "default_stages: [pre-commit]\n"
    )
    # A hook whose upstream manifest declares `stages` ignores default_stages; these two list pre-push.
    manifest_note = "        stages: [pre-commit]  # its manifest adds pre-push, which default_stages cannot narrow (G6)\n"
    hook_row = "| git-remote-alias   | local     | The pre-push stage only (`always_run`, no files); opt in with `pre-commit install --hook-type pre-push` | Every Juniper checkout's origin uses its `github_juniper-<repo>` alias: `util/git_remote_alias_check.py --check --if-configured`, which skips a host without the aliases (turing bring-up G6, gate G-ALIAS) |\n"
    gitleaks_row = "| gitleaks           | v8.24.3   | The staged diff (`--staged`; scans nothing in CI) | Secret detection before commit, with `.gitleaks.toml` (default ruleset + `juniper-secret-assignment`); `rev` must equal `ci.yml`'s `GITLEAKS_VERSION` |\n"
    g2_end = "`util/ad-hoc/2026-10-17_turing_g2_mutation_check.py` kills 16 of 16 mutants."
    g6_pins = (
        " Task G6's hook is pinned too. `.pre-commit-config.yaml` runs exactly `--check --if-configured` at the pre-push stage, with `pass_filenames: false` and `always_run: true`, and it is the only hook at that stage (`default_stages: [pre-commit]`). "
        "That configured entry skips on a host without aliases, `minimum_pre_commit_version` is at least 3.2.0, and ci.yml runs the stage."
    )
    setup = "pip install pre-commit\npre-commit install\npre-commit run --all-files\n```"
    setup_new = "pip install pre-commit\npre-commit install\npre-commit run --all-files\npre-commit install --hook-type pre-push   # opt-in: the G6 git-remote-alias hook\n```"
    changelog = (
        "- **The `git-remote-alias` pre-push hook** (turing bring-up task G6, gate G-ALIAS of\n"
        f"  `{PLAN}`).\n"
        "  - `.pre-commit-config.yaml` runs `util/git_remote_alias_check.py --check --if-configured` (task G2) at the\n"
        "    pre-push stage. On a host with the `github_juniper-*` aliases, a push is blocked while any of the 10\n"
        "    checkouts bypasses its alias, is missing, or has a key not at mode 600. A host without the aliases skips.\n"
        "  - Each host opts in with `pre-commit install --hook-type pre-push`. `minimum_pre_commit_version` rises from\n"
        "    3.0.0 to 3.2.0, the release that named the stage `pre-push`.\n"
        "  - `default_stages: [pre-commit]` keeps every other hook at commit time. Without it, a hook with no `stages`\n"
        "    runs at every stage: a push would re-run the whole commit suite, and the CI smoke step would lint the\n"
        "    whole tree, undoing the Pre-commit job's changed-files split. `check-added-large-files` and `isort` set\n"
        "    `stages: [pre-commit]` themselves, because their upstream manifests list pre-push and override\n"
        "    `default_stages`.\n"
        "  - ci.yml's Pre-commit job runs the pre-push stage as a smoke test, and `tests/test_git_remote_alias_check.py`\n"
        "    pins the hook's configuration.\n"
        "\n"
    )
    return [
        (PRE_COMMIT, "id: git-remote-alias", "\n# CI configuration (for pre-commit.ci service, if used)\n", hook + "\n# CI configuration (for pre-commit.ci service, if used)\n"),
        (PRE_COMMIT, 'minimum_pre_commit_version: "3.2.0"', 'minimum_pre_commit_version: "3.0.0"\n', 'minimum_pre_commit_version: "3.2.0"\n'),
        (PRE_COMMIT, "default_stages: [pre-commit]", 'minimum_pre_commit_version: "3.2.0"\n', 'minimum_pre_commit_version: "3.2.0"\n' + default_stages),
        (PRE_COMMIT, "        args: [--maxkb=1000]\n" + manifest_note, "      - id: check-added-large-files\n        name: Check for large files\n        args: [--maxkb=1000]\n", "      - id: check-added-large-files\n        name: Check for large files\n        args: [--maxkb=1000]\n" + manifest_note),
        (PRE_COMMIT, "          - --profile=black\n          - --line-length=512\n        files: ^(scripts|tests)/.*\\.py$\n" + manifest_note, "          - --profile=black\n          - --line-length=512\n        files: ^(scripts|tests)/.*\\.py$\n", "          - --profile=black\n          - --line-length=512\n        files: ^(scripts|tests)/.*\\.py$\n" + manifest_note),
        (CI, "Run the pre-push stage (G6 smoke)", "            pre-commit run --all-files --show-diff-on-failure\n          fi\n", ci_step),
        (REFERENCE, "| git-remote-alias   |", gitleaks_row, gitleaks_row + hook_row),
        (REFERENCE, "Task G6's hook is pinned too.", g2_end, g2_end + g6_pins),
        (REFERENCE, "pre-commit install --hook-type pre-push   # opt-in", setup, setup_new),
        ("CHANGELOG.md", "**The `git-remote-alias` pre-push hook**", None, changelog),
    ]


def insert_unreleased_added(text: str, block: str) -> str | None:
    """Put ``block`` first under [Unreleased] / ### Added, or None when that heading is missing."""
    start = text.find("\n## [Unreleased]\n")
    end = text.find("\n## [", start + 1)
    head = text.find("\n### Added\n\n", start, end)
    if start < 0 or head < 0:
        return None
    at = head + len("\n### Added\n\n")
    return text[:at] + block + text[at:]


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
            print(f"present  {rel}: {marker[:60]!r}")
        elif anchor is None:
            new = insert_unreleased_added(text, repl)
            if new is None:
                print(f"FAIL     {rel}: no [Unreleased] / ### Added heading")
                failed += 1
            else:
                text = new
                print(f"apply    {rel}: [Unreleased] / ### Added entry")
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
