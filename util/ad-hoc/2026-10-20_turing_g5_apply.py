"""
Apply turing bring-up G5's edits to the shared files, idempotently, and refresh its baseline.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: ad-hoc — one-off (turing bring-up task G5: the G-PATH gate's wiring)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task G5, gate G-PATH,
         decision D12; §17.3 E-LAND-2); util/home_path_literal_check.py; util/ad-hoc/2026-10-19_turing_e6_errata.py
         (the pattern this follows)

Why: G5 lands through the GitHub API as whole-file uploads, and five of its files are shared with every
other PR: ci.yml, .pre-commit-config.yaml, docs/REFERENCE.md, AGENTS.md and CHANGELOG.md. An upload built
from an older base silently reverts whatever main gained since (E-LAND-2: juniper-ml#2262 reverted #2259).
So the edits live here, keyed on anchors, and are re-applied to a fresh origin/main copy right before the
upload. The new files (the checker, its suite, the mutation check, this script) are not shared.

What it does, in order:
1. Recount conf/home_path_literal_baseline.json from the tree (the checker's own --update-baseline logic),
   so a file another PR added or changed in the meantime is baselined at its current count.
2. Insert the G5 blocks: the Pre-commit job's whole-scope step and the suite line in ci.yml's regression
   step; the pre-commit hook; REFERENCE.md's suite-list line, Test Suite Reference entry, Utility Script
   Reference entry and Pre-commit Hook Reference row; the CHANGELOG [Unreleased] / Added entry.
3. Set AGENTS.md's suite count to the number of suites ci.yml's regression step runs, and its
   **Last Updated** to today's UTC date (the advisory check wants UTC).

Each insertion has a marker. When the marker is already present the edit is skipped; otherwise its anchor
must occur exactly once. A re-run on a newer main therefore applies cleanly or stops loudly.

Usage:
    python3 -I util/ad-hoc/2026-10-20_turing_g5_apply.py [--root REPO_ROOT] [--dry-run]

Exit 0 = every edit applied or already present; 1 = an anchor is missing or ambiguous (nothing written).
"""

import argparse
import datetime
import importlib.util
import re
import sys
from pathlib import Path

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
CI = ".github/workflows/ci.yml"
PRE_COMMIT = ".pre-commit-config.yaml"
REFERENCE = "docs/REFERENCE.md"
SUITE_LINE = "python3 -m unittest -v tests/test_home_path_literal_check.py"


def load_checker(root: Path):
    spec = importlib.util.spec_from_file_location("home_path_literal_check", root / "util" / "home_path_literal_check.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def edits(n_files: int, n_lines: int, n_adhoc: int):
    """(path, marker, anchor, replacement). The replacement keeps the anchor and adds the G5 block."""
    ci_step = (
        "            pre-commit run --all-files --show-diff-on-failure\n"
        "          fi\n"
        "\n"
        "      - name: Check home-path literals, whole scope (G5, G-PATH)\n"
        "        # Turing bring-up G5 (decision D12). The home-path-literal pre-commit hook sees only the\n"
        "        # changed files on a pull request; this step checks every tracked .bash/.sh/.py/.yml under\n"
        "        # util/, scripts/ and .github/ against conf/home_path_literal_baseline.json. A file may hold\n"
        "        # no more lines carrying the Linux home-path literal than the baseline allows it.\n"
        "        run: python3 util/home_path_literal_check.py\n"
    )
    ci_suite = (
        "          # tests/test_home_path_literal_check.py: turing bring-up G5 (gate G-PATH, decision D12).\n"
        "          # util/home_path_literal_check.py fails a tracked .bash/.sh/.py/.yml under util/, scripts/\n"
        "          # or .github/ holding more lines with the Linux home-path literal than\n"
        "          # conf/home_path_literal_baseline.json allows it; \"# home-path-literal: allow\" exempts a\n"
        "          # line. Real git on temp repos; the committed baseline must match this checkout.\n"
        f"          {SUITE_LINE}\n"
    )
    hook = (
        "\n"
        "  # ═══════════════════════════════════════════════════════════════════════════\n"
        "  # G-PATH: no new /home/pcalnon literal in scripts or CI (turing bring-up G5,\n"  # home-path-literal: allow -- text this script writes
        "  # decision D12). A staged .bash/.sh/.py/.yml file under util/, scripts/ or\n"
        "  # .github/ may hold no more literal lines than conf/home_path_literal_baseline.json\n"
        "  # allows it; staging the baseline itself re-checks the whole scope. A line that\n"
        "  # must keep the literal ends with \"# home-path-literal: allow\". The Pre-commit\n"
        "  # job in ci.yml also runs the whole-scope check as its own step.\n"
        "  # ═══════════════════════════════════════════════════════════════════════════\n"
        "  - repo: local\n"
        "    hooks:\n"
        "      - id: home-path-literal\n"
        "        name: No new /home/pcalnon literal in scripts or CI (G5)\n"  # home-path-literal: allow
        "        entry: python3 util/home_path_literal_check.py\n"
        "        language: system\n"
        "        files: '^((util|scripts|\\.github)/.+\\.(bash|sh|py|yml)|conf/home_path_literal_baseline\\.json)$'\n"
    )
    suite_entry = (
        "- `tests/test_home_path_literal_check.py` -- Turing bring-up G5, gate G-PATH (`" + PLAN + "`, decision D12). "
        "`util/home_path_literal_check.py` must fail a tracked `.bash`/`.sh`/`.py`/`.yml` file under `util/`, `scripts/` or `.github/` that holds more lines carrying `/home/pcalnon` than `conf/home_path_literal_baseline.json` allows it, and must list each such line. "  # home-path-literal: allow
        "The suite pins these rules. A line counts once, however many literals it holds, and a file's count does not depend on line numbers. A count equal to the baseline passes, and one over it fails. "
        "Every scope directory and suffix is checked, and nothing else is (`.yaml`, `docs/util/`, `tests/`). `# home-path-literal: allow` exempts only its own line. "
        "Whole-scope mode skips untracked files and symlinks. A named file is checked whether or not it is tracked. Naming the baseline re-checks the whole scope. "
        "A count below its baseline, or a baseline entry for a deleted file, is a NOTE. A missing or malformed baseline, a root that is not a git checkout, and a missing git each exit 2. "
        "`--update-baseline` writes sorted per-file counts, one per line, and leaves a current file untouched; `--dry-run` writes nothing. "
        "Real `git` runs on temp repos with every `GIT_*` variable scrubbed. "
        "Against this checkout, the suite also asserts these points. The committed baseline matches the tree and is in rendered form, and the script holds no literal line of its own. The pre-commit hook's `files` pattern selects exactly the scope, and ci.yml runs the whole-scope step. "
        "`util/ad-hoc/2026-10-20_turing_g5_mutation_check.py` kills 22 of 22 mutants.\n"
    )
    util_entry = (
        "- `util/home_path_literal_check.py` -- Gate G-PATH: `python3 util/home_path_literal_check.py [--root DIR] [--baseline FILE] [FILE ...]`, or the same with `--update-baseline [--dry-run]`. "
        "A tracked `.bash`/`.sh`/`.py`/`.yml` file under `util/`, `scripts/` or `.github/` may hold no more lines carrying `/home/pcalnon` than `conf/home_path_literal_baseline.json` allows it. "  # home-path-literal: allow
        f"When the gate landed that was {n_files} files and {n_lines} lines, {n_adhoc} of the files under `util/ad-hoc/`. A line ending in `# home-path-literal: allow` is not counted. "
        "With FILE arguments it checks those files, or the whole scope when the baseline is one of them; that is the `home-path-literal` pre-commit hook. "
        "Without arguments it checks every tracked file in scope; that is the whole-scope step in ci.yml's Pre-commit job. "
        "A count below its baseline is a NOTE: lower the baseline with `--update-baseline`. Exit 0 / 1 / 2. `GIT` is overridable. Turing bring-up G5, decision D12. Tests: `tests/test_home_path_literal_check.py`.\n"
    )
    hook_row = "| home-path-literal  | local     | `.bash`/`.sh`/`.py`/`.yml` under `util/`, `scripts/`, `.github/`; the baseline | No new `/home/pcalnon` line beyond `conf/home_path_literal_baseline.json` (turing bring-up G5, gate G-PATH, decision D12) |\n"  # home-path-literal: allow
    changelog = (
        "- **`util/home_path_literal_check.py`, the G-PATH gate** (turing bring-up task G5, decision D12 of\n"
        f"  `{PLAN}`).\n"
        "  - A tracked `.bash`, `.sh`, `.py` or `.yml` file under `util/`, `scripts/` or `.github/` may hold no more\n"
        "    lines carrying `/home/pcalnon` than `conf/home_path_literal_baseline.json` (new) allows it. The baseline\n"  # home-path-literal: allow
        f"    holds the {n_files} files and {n_lines} lines in scope when the gate landed; {n_adhoc} of the files are under `util/ad-hoc/`.\n"
        "    A line ending in `# home-path-literal: allow` is not counted.\n"
        "  - It runs as the `home-path-literal` pre-commit hook on staged files, and as a whole-scope step in\n"
        "    ci.yml's Pre-commit job. `--update-baseline` recounts, and `--dry-run` writes nothing.\n"
        "  - `tests/test_home_path_literal_check.py` (new) is wired into `ci.yml` and `docs/REFERENCE.md`.\n"
        "  - `util/ad-hoc/2026-10-20_turing_g5_mutation_check.py` (new) shows that the suite kills 22 of 22 mutants.\n"
        "\n"
    )
    gitleaks_row = "| gitleaks           | v8.24.3   | The staged diff (`--staged`; scans nothing in CI) | Secret detection before commit, with `.gitleaks.toml` (default ruleset + `juniper-secret-assignment`); `rev` must equal `ci.yml`'s `GITLEAKS_VERSION` |\n"
    return [
        (CI, "Check home-path literals, whole scope (G5, G-PATH)", "            pre-commit run --all-files --show-diff-on-failure\n          fi\n", ci_step),
        (CI, SUITE_LINE, "\n\n      - name: Run bash regression tests\n", "\n" + ci_suite + "\n      - name: Run bash regression tests\n"),
        (PRE_COMMIT, "id: home-path-literal", "\n# CI configuration (for pre-commit.ci service, if used)\n", hook + "\n# CI configuration (for pre-commit.ci service, if used)\n"),
        (REFERENCE, SUITE_LINE, "\nbash scripts/test_resume_file_safety.bash\n# doc-link validator", f"\n{SUITE_LINE}\nbash scripts/test_resume_file_safety.bash\n# doc-link validator"),
        (REFERENCE, "- `tests/test_home_path_literal_check.py` --", "- `scripts/test.bash` -- Manual end-to-end harness", suite_entry + "- `scripts/test.bash` -- Manual end-to-end harness"),
        (REFERENCE, "- `util/home_path_literal_check.py` --", "- `util/wait_for_checks.py` -- ", util_entry + "- `util/wait_for_checks.py` -- "),
        (REFERENCE, "| home-path-literal  |", gitleaks_row, gitleaks_row + hook_row),
        ("CHANGELOG.md", "**`util/home_path_literal_check.py`, the G-PATH gate**", None, changelog),
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


def regression_suites(ci_text: str) -> int:
    start = ci_text.index("- name: Run Python regression tests")
    end = ci_text.index("\n      - name: ", start)
    return len(re.findall(r"^\s+python3 -m unittest -v tests/\S+\.py$", ci_text[start:end], flags=re.M))


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args(argv)

    checker = load_checker(args.root)
    baseline = args.root / checker.BASELINE_REL
    status = checker.update_baseline(args.root, baseline, args.dry_run)
    if status != 0:
        return 1
    counts = {rel: len(hits) for rel, hits in checker.scan(args.root, checker.readable(args.root, checker.tracked(args.root))).items()}
    n_files, n_lines, n_adhoc = len(counts), sum(counts.values()), sum(1 for rel in counts if rel.startswith("util/ad-hoc/"))

    texts, failed = {}, 0
    for rel, marker, anchor, repl in edits(n_files, n_lines, n_adhoc):
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
