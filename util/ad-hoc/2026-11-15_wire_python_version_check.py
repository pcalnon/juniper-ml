#!/usr/bin/env python3
"""
Wire util/python_version_check.py and its two suites into ci.yml, docs/REFERENCE.md, CHANGELOG.md and AGENTS.md.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-11-15
Status: ad-hoc — one-off (the local half of phase 1 of the Python 3.15 migration)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/python_version_check.py; conf/python_versions.yaml; tests/test_python_version_check.py;
         tests/test_python_version_matrix_drift.py; util/ad-hoc/2026-10-17_turing_wire_suite.py (the anchors
         this follows); juniper-ml#2567 (the CI half, which edited the same four files)

Why: the four shared files are edited by other PRs while this one waits (juniper-ml#2567 first, then the
peer flood-4 PRs that move REFERENCE.md's version and AGENTS.md's suite count). A hand edit made against
one main is wrong against the next. So this never edits the worktree's copies: it reads each file AS IT IS
ON --base (``git show <base>:<path>``), applies the edits, and writes the result into the worktree. Every
number is derived from that base at run time:

- AGENTS.md's "full ordered list of N": recounted from ci.yml's regression step after the two suites are
  added, and required to equal docs/REFERENCE.md's "Running every suite" list;
- docs/REFERENCE.md's version: the base's ``**Version:**`` plus one patch level, in the header, the
  footer and a new version-history row after the base's own row;
- both files' dates: today's UTC date (the ``Verify AGENTS.md Last Updated`` check reads UTC).

Every edit refuses (exit 2) when its anchor is missing or not unique, or when the base already carries
the change, so a moved anchor fails loudly instead of producing a half-wired file. Run it again after
fetching whenever --base moves; it rewrites the four files from scratch each time.

Usage:
    git fetch origin main
    python3 util/ad-hoc/2026-11-15_wire_python_version_check.py --base origin/main [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import subprocess  # nosec B404 - read-only `git show` of this checkout's own base ref
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CI = ".github/workflows/ci.yml"
REFERENCE = "docs/REFERENCE.md"
CHANGELOG = "CHANGELOG.md"
AGENTS = "AGENTS.md"
SUITES = ("tests/test_python_version_check.py", "tests/test_python_version_matrix_drift.py")
HELPER = "util/python_version_check.py"

CI_BLOCK = """\
          # tests/test_python_version_check.py: util/python_version_check.py, the local half of phase 1 of the Python 3.15
          # migration (owner ruling 2026-11-14). It builds a venv per repo and version at a FIXED path in the repo's primary
          # tmp/ (pyvenv/py<version>), installs the repo with its CI's commands and runs the repo's own wrapper there, exiting 0
          # whatever the results unless --strict. Pinned: conf/python_versions.yaml's ruling and validation; the venv path,
          # which TMPDIR, the cwd and --checkout do not move; unavailable versus failed; --dry-run and --list writing nothing;
          # where the logs land; the child environment; the venv's reuse and the paths it never removes; and that pre-commit
          # never runs it. A stub interpreter, venv and wrapper on PATH: no real venv, pip or repo. Stdlib plus PyYAML.
          python3 -m unittest -v tests/test_python_version_check.py
          # tests/test_python_version_matrix_drift.py: every Python-version matrix in .github/workflows/ (pre-commit exempt)
          # runs each informational version of conf/python_versions.yaml as an `include` entry with `experimental: true`,
          # under the job-level continue-on-error expression on matrix.experimental, and never in its plain list; no blocking
          # version is experimental, and this job's matrix runs exactly the blocking list. The config's juniper-ml recipe
          # installs exactly the requirements of this job's "Install test dependencies" step. Negative controls for each
          # violating shape. PyYAML only.
          python3 -m unittest -v tests/test_python_version_matrix_drift.py
"""


def sentences(*parts: str) -> str:
    """One markdown line from its sentences (keeps this file inside the 512-column convention)."""
    return " ".join(parts)


TEST_BULLET_HELPER = sentences(
    "- `tests/test_python_version_check.py` -- `util/python_version_check.py`, the local half of phase 1 of the Python 3.15 migration (owner ruling 2026-11-14: 3.12-3.14 blocking, 3.15 informational).",
    "`conf/python_versions.yaml` must carry the ruling, and an invalid config exits 2: a version in both lists, an unquoted version (YAML reads `3.10` as `3.1`), an unknown key, a bad step or repo name.",
    "The venv path is `{root}/{repo}/tmp/pyvenv/py{version}` whatever TMPDIR, the cwd or `--checkout` say.",
    "A run exits 0 whatever its results, and 1 under `--strict` on a failed or unavailable check; a missing interpreter, or one that reports another version, is `unavailable`, not a crash.",
    "`--dry-run` and `--list` invoke nothing and write nothing.",
    "The summary and every step's log land under `{root}/juniper-ml/tmp/python-version-checks/<UTC stamp>/`.",
    "Each child gets the venv first on PATH, `VIRTUAL_ENV`, the repo's `tmp/` as `TMPDIR` (prepended to `GIT_CEILING_DIRECTORIES`), and no `PYTHONPATH`, `PYTHONHOME` or `env_unset` name.",
    "The venv is reused, rebuilt on `--recreate` or when its interpreter reports another version, and a symlink or a directory without `pyvenv.cfg` is never removed; a lock another run holds is `unavailable`.",
    "A run changes no file of the checkout, and `.pre-commit-config.yaml` never runs the helper.",
    "A stub interpreter builds a stub venv, the demo checkout's wrapper records its environment, and PATH holds only the stubs and symlinked shell tools, so the host's own interpreters are never found.",
)

TEST_BULLET_DRIFT = sentences(
    "- `tests/test_python_version_matrix_drift.py` -- Every Python-version matrix in `.github/workflows/` (pre-commit exempt, the owner's ruling of 2026-11-14) must run each `informational` version of `conf/python_versions.yaml` as an `include` entry with `experimental: true`,",
    "under the job-level `continue-on-error: ${{ matrix.experimental == true }}`, and never in its plain `python-version` list, which would make it blocking.",
    "No `include` entry may mark another version experimental, and `ci.yml`'s regression matrix runs exactly the `blocking` list.",
    "The scan must find the seven matrices juniper-ml#2567 gave informational legs (`ci.yml`'s `tests` and the six `ci-<pkg>.yml` `test` jobs).",
    "The config's juniper-ml recipe must install exactly the requirements of the `tests` job's `Install test dependencies` step, and name a regression runner that exists.",
    "Negative controls for each violating shape. PyYAML only.",
)

TEST_BULLETS = TEST_BULLET_HELPER + "\n" + TEST_BULLET_DRIFT + "\n"

UTIL_BULLET = (
    sentences(
        "- `util/python_version_check.py` -- Runs a Juniper repo's own test wrapper under another Python version, locally: the local half of phase 1 of the Python 3.15 migration (owner ruling 2026-11-14).",
        "`python3 util/python_version_check.py (--repo NAME... | --all) [--python X.Y]... [--checkout PATH] [--root DIR] [--config FILE] [--recreate] [--dry-run] [--strict]`, or `--list`.",
        "`conf/python_versions.yaml` holds the version lists (`blocking` 3.12, 3.13 and 3.14; `informational` 3.15, the default `--python`) and one recipe per repo.",
        "A recipe's `install` commands are the repo's CI install step, and its `test` commands the repo's existing wrapper: `bash util/run_coverage.bash`; canopy's `make test PYTEST=\"$VIRTUAL_ENV/bin/python -m pytest\"`;",
        "harcot's `PYTHON=\"$VIRTUAL_ENV/bin/python\" bash util/run_coverage.bash`; deploy's `pytest tests/`, because its `make test` runs in Docker on python:3.12-slim;",
        "recurrence's packages each from its subdirectory and the bench from the root; juniper-ml's `util/ad-hoc/2026-11-15_run_ci_regression_list_locally.py`.",
        "For each repo and version it builds a venv from `/usr/bin/python<version>` (else `python<version>` on PATH) at the FIXED path `{root}/{repo}/tmp/pyvenv/py{version}`, the primary checkout's gitignored `tmp/`,",
        "never derived from TMPDIR or `--checkout`, and holds an `flock` on `py{version}.lock` beside it.",
        "Each command runs as `bash -e -o pipefail -c` from the checkout, with the venv first on PATH, `VIRTUAL_ENV` set, `TMPDIR` the repo's `tmp/`, and `PYTHONPATH`, `PYTHONHOME` and the recipe's `env_unset` names removed.",
        "A result is `passed`; `failed`, with the phase (venv, install or test); or `unavailable`: no interpreter or one reporting another version, a missing checkout, a held lock.",
        "`summary.json` and each step's log go to `{root}/juniper-ml/tmp/python-version-checks/<UTC stamp>/`, never pruned.",
        "Exit 0 whatever the results, 1 with `--strict` on a failed or unavailable check, 2 on a usage or config error.",
        "It never edits a checkout's tracked files, never touches a conda env or `/usr/bin/python3` (which stays 3.14), and is not a pre-commit hook.",
        "`--dry-run` and `--list` run and write nothing. `JUNIPER_ROOT` and `PYTHON_VERSION_CHECK_SYSTEM_BIN` (default `/usr/bin`) are overridable.",
        "First real run, 2026-11-15: juniper-data-client on 3.15.2 passed, 537 tests passed and 19 skipped, coverage 99.68%.",
        "Tests: `tests/test_python_version_check.py`; `tests/test_python_version_matrix_drift.py` holds CI's matrices to the same lists.",
    )
    + "\n"
)

CI_SECTION_ANCHOR = "no ruleset requires a 3.15 context). "
CI_SECTION_SENTENCE = "`tests/test_python_version_matrix_drift.py` holds every such matrix to the lists in `conf/python_versions.yaml`, which `util/python_version_check.py` reads to run the same versions locally. "

CHANGELOG_ENTRY = """\
- **Local Python-version checks: `util/python_version_check.py` runs a repo's own tests under Python 3.15 (or any
  listed version) in a venv kept at a fixed path, and reports without blocking.** The local half of phase 1 of the
  Python 3.15 migration (the owner's request and ruling of 2026-11-14; juniper-ml#2567 was the CI half).
  - `conf/python_versions.yaml` holds the ecosystem's version lists, `blocking` 3.12, 3.13 and 3.14 and
    `informational` 3.15, and one recipe per repo: its CI's install commands and its existing local wrapper.
  - For each repo and version the helper builds a venv from `/usr/bin/python<version>` at
    `{root}/{repo}/tmp/pyvenv/py{version}`, the primary checkout's gitignored `tmp/`, runs the recipe with the venv
    first on PATH, and writes `summary.json` and each step's log under juniper-ml's primary `tmp/`. It exits 0
    whatever the results unless `--strict`, reports a missing interpreter as `unavailable`, and is not a pre-commit
    hook. `/usr/bin/python3` stays 3.14.
  - Two suites are wired into ci.yml: `tests/test_python_version_check.py` (stubs only, no real venv, pip or repo)
    and `tests/test_python_version_matrix_drift.py` (every CI Python matrix runs each informational version as an
    experimental `include` entry and never in its plain list; the juniper-ml recipe installs exactly what ci.yml's
    `tests` job installs). `util/ad-hoc/2026-11-15_wire_python_version_check.py` writes this entry and the other
    shared-file edits from the current base, so the counts and the docs version are derived, not remembered.
  - First real run, juniper-data-client on 3.15.2: passed (537 passed, 19 skipped; coverage 99.68%).
"""


class WireError(Exception):
    pass


def base_text(base: str, path: str) -> str:
    proc = subprocess.run(["git", "-C", str(ROOT), "show", f"{base}:{path}"], capture_output=True, text=True, check=False)  # nosec B603 B607
    if proc.returncode != 0:
        raise WireError(f"git show {base}:{path} failed: {proc.stderr.strip()}")
    return proc.stdout


def replace_once(text: str, old: str, new: str, what: str) -> str:
    count = text.count(old)
    if count != 1:
        raise WireError(f"{what}: expected the anchor exactly once, found it {count} times: {old[:80]!r}")
    return text.replace(old, new, 1)


def section_bounds(lines: list[str], heading: str) -> tuple[int, int]:
    """[start, end) of a markdown section; ``` fences are skipped (the suite list is a bash block of `# ...`)."""
    level = len(heading.split(" ", 1)[0])
    if lines.count(heading) != 1:
        raise WireError(f"{REFERENCE}: expected exactly one heading {heading!r}")
    start = lines.index(heading)
    in_fence = False
    for i in range(start + 1, len(lines)):
        if lines[i].startswith("```"):
            in_fence = not in_fence
            continue
        m = re.match(r"(#{1,6}) ", lines[i])
        if not in_fence and m and len(m.group(1)) <= level:
            return start, i
    return start, len(lines)


def regression_suites(ci_text: str) -> list[str]:
    """The suites ci.yml's regression step invokes, in order (comment lines skipped)."""
    import yaml

    doc = yaml.safe_load(ci_text)
    step = next(s for s in doc["jobs"]["tests"]["steps"] if s.get("name") == "Run Python regression tests")
    return [line.strip() for line in step["run"].splitlines() if line.strip().startswith("python3 -m unittest ")]


def wire_ci(text: str) -> str:
    for suite in SUITES:
        if f"python3 -m unittest -v {suite}" in text:
            raise WireError(f"{CI}: the base already invokes {suite}")
    anchor = "\n\n      - name: Run bash regression tests\n"
    return replace_once(text, anchor, "\n" + CI_BLOCK.rstrip("\n") + anchor, CI)


def wire_reference(text: str, today: str, suite_count: int) -> tuple[str, str]:
    if f"- `{HELPER}` --" in text:
        raise WireError(f"{REFERENCE}: the base already documents {HELPER}")
    lines = text.split("\n")
    start, end = section_bounds(lines, "### Running every suite")
    hits = [i for i in range(start, end) if lines[i] == "bash scripts/test_resume_file_safety.bash"]
    if len(hits) != 1:
        raise WireError(f"{REFERENCE}: `Running every suite` must hold the resume-file-safety line exactly once")
    lines[hits[0] : hits[0]] = [f"python3 -m unittest -v {suite}" for suite in SUITES]
    listed = sum(1 for line in lines[start : end + len(SUITES)] if line.startswith("python3 -m unittest "))
    if listed != suite_count:
        raise WireError(f"{REFERENCE}: `Running every suite` lists {listed} suites but ci.yml runs {suite_count}; reconcile the base first")

    start, end = section_bounds(lines, "## Test Suite Reference")
    hits = [i for i in range(start, end) if lines[i].startswith("- `scripts/test.bash` --")]
    if len(hits) != 1:
        raise WireError(f"{REFERENCE}: no single `scripts/test.bash` bullet in the Test Suite Reference")
    lines[hits[0] : hits[0]] = TEST_BULLETS.rstrip("\n").split("\n")

    start, end = section_bounds(lines, "## Utility Script Reference")
    hits = [i for i in range(start, end) if lines[i].startswith("- `util/juniper_repo_tmp.bash` --")]
    if len(hits) != 1:
        raise WireError(f"{REFERENCE}: no single `util/juniper_repo_tmp.bash` bullet in the Utility Script Reference")
    lines[hits[0] + 1 : hits[0] + 1] = UTIL_BULLET.rstrip("\n").split("\n")
    text = "\n".join(lines)

    names = ", ".join(f"`{suite}`" for suite in SUITES)
    text = replace_once(text, ". The drift script above counts, so re-run it", f", **{suite_count}** on {today} with the local Python-version helper's two ({names}). The drift script above counts, so re-run it", f"{REFERENCE} suite-count sentence")
    text = replace_once(text, CI_SECTION_ANCHOR, CI_SECTION_ANCHOR + CI_SECTION_SENTENCE, f"{REFERENCE} Shared-Package CI Workflows")

    header = re.findall(r"(?m)^\*\*Version:\*\* (\S+)$", text)
    if len(header) != 2 or header[0] != header[1]:
        raise WireError(f"{REFERENCE}: expected the same `**Version:**` in the header and the footer, found {header}")
    old = header[0]
    if not re.fullmatch(r"\d+\.\d+\.\d+", old):
        raise WireError(f"{REFERENCE}: version {old!r} is not X.Y.Z; bump it by hand")
    major, minor, patch = (int(part) for part in old.split("."))
    new = f"{major}.{minor}.{patch + 1}"
    text = re.sub(r"(?m)^\*\*Version:\*\* \S+$", f"**Version:** {new}", text)
    text, n = re.subn(r"(?m)^\*\*Last Updated:\*\* \S+$", f"**Last Updated:** {today}", text)
    if n != 2:
        raise WireError(f"{REFERENCE}: expected two `**Last Updated:**` lines, found {n}")
    rows = [line for line in text.split("\n") if line.startswith(f"| {old} ")]
    if len(rows) != 1:
        raise WireError(f"{REFERENCE}: expected one version-history row for {old}, found {len(rows)}")
    summary = sentences(
        f"Local Python-version checks (phase 1 of the Python 3.15 migration, owner ruling 2026-11-14): `{HELPER}` runs a repo's own test wrapper in a venv at `{{root}}/{{repo}}/tmp/pyvenv/py{{version}}`",
        "built from `/usr/bin/python<version>`, from the version lists and recipes in `conf/python_versions.yaml`, and exits 0 unless `--strict` (§ Utility Script Reference);",
        f"`tests/test_python_version_matrix_drift.py` holds CI's Python matrices to the same lists (§ Shared-Package CI Workflows); two suites registered ({suite_count})",
    )
    row = f"| {new:<7} | {today} | {summary} |"
    text = replace_once(text, rows[0] + "\n", rows[0] + "\n" + row + "\n", f"{REFERENCE} version history")
    return text, new


def wire_changelog(text: str) -> str:
    if HELPER in text:
        raise WireError(f"{CHANGELOG}: the base already mentions {HELPER}")
    head = "## [Unreleased]\n\n### Added\n\n"
    return replace_once(text, head, head + CHANGELOG_ENTRY.rstrip("\n") + "\n\n", CHANGELOG)


def wire_agents(text: str, today: str, suite_count: int) -> str:
    text, n = re.subn(r"the full ordered list of \d+ `python3 -m unittest`", f"the full ordered list of {suite_count} `python3 -m unittest`", text)
    if n != 1:
        raise WireError(f"{AGENTS}: the `full ordered list of N` sentence was not found exactly once")
    text, n = re.subn(r"(?m)^\*\*Last Updated\*\*: \S+$", f"**Last Updated**: {today}", text)
    if n != 1:
        raise WireError(f"{AGENTS}: expected one `**Last Updated**:` line, found {n}")
    return text


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--base", required=True, help="the ref the PR's commit is parented on, e.g. origin/main (fetch it first)")
    ap.add_argument("--dry-run", action="store_true", help="report the derived numbers and write nothing")
    args = ap.parse_args(argv)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    try:
        for suite in SUITES:
            if not (ROOT / suite).is_file():
                raise WireError(f"{suite} is not in this checkout")
        ci = wire_ci(base_text(args.base, CI))
        base_count = len(regression_suites(base_text(args.base, CI)))
        suite_count = len(regression_suites(ci))
        if suite_count != base_count + len(SUITES):
            raise WireError(f"{CI}: expected {base_count} + {len(SUITES)} suites after wiring, counted {suite_count}")
        reference, version = wire_reference(base_text(args.base, REFERENCE), today, suite_count)
        changelog = wire_changelog(base_text(args.base, CHANGELOG))
        agents = wire_agents(base_text(args.base, AGENTS), today, suite_count)
    except WireError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(f"base {args.base}: ci.yml {base_count} -> {suite_count} suites; docs/REFERENCE.md -> {version}; dated {today}")
    if args.dry_run:
        return 0
    for path, text in ((CI, ci), (REFERENCE, reference), (CHANGELOG, changelog), (AGENTS, agents)):
        (ROOT / path).write_text(text, encoding="utf-8")
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
