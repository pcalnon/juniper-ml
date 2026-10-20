"""
Apply turing bring-up G4's edits to the shared files, idempotently: the advisory host-tooling-macos CI job.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: ad-hoc — one-off (turing bring-up task G4: host tooling under BSD userland and /bin/bash 3.2)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task G4, §9.1 test classes,
         §9.2 gate placement, §9.4 the macOS runner tradeoff; §17.3 E-LAND-2); tests/test_ci_host_tooling_macos.py;
         util/ad-hoc/2026-10-20_turing_g5_apply.py (the pattern this follows)

Why: G4 lands through the GitHub API as whole-file uploads of four files every other PR shares: ci.yml,
docs/REFERENCE.md, AGENTS.md and CHANGELOG.md. An upload built from an older base silently reverts whatever
main gained since (E-LAND-2). So the edits live here, keyed on anchors, and are re-applied to a fresh
origin/main copy right before the upload.

The edits:
- ci.yml gains the `host-tooling-macos` job (name "Host Tooling (macOS)"), before the Quality Gate and absent
  from its `needs:` (advisory). A detection step sets `relevant`; every later step is gated on it.
- ci.yml's regression step runs tests/test_ci_host_tooling_macos.py, the job's gate.
- docs/REFERENCE.md: the suite in "Running every suite" (and 217 in its intro's count history) and § Test Suite
  Reference, and the job in § CI/CD Pipeline Reference's ci.yml job list.
- AGENTS.md: the suite count follows ci.yml's regression step, and **Last Updated** takes today's UTC date.
- CHANGELOG.md: an [Unreleased] / Added entry, directly below G2's entry: away from the top of the list, where
  concurrent PRs insert theirs, and from the spot below G5's entry, where G6 goes.

Each edit has a marker. When the marker is already present the edit is skipped; otherwise its anchor must occur
exactly once. A re-run on a newer main therefore applies cleanly or stops loudly.

Usage:
    python3 -I util/ad-hoc/2026-10-20_turing_g4_apply.py [--root REPO_ROOT] [--dry-run]

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
SUITE_LINE = "python3 -m unittest -v tests/test_ci_host_tooling_macos.py"
# The run-list intro sentence keeps a count history; juniper-ml#2273 left it at 216.
RUN_LIST_COUNTS = "**216** on 2026-10-20 with W5.5 / W5.6's `tests/test_stats_summary_target_summary.py` and `tests/test_experiment_stack_shared_equities_cache.py`"
G2_CHANGELOG_TAIL = "  -`util/ad-hoc/2026-10-17_turing_g2_mutation_check.py` (new) shows that the suite kills 16 of 16 mutants.\n\n"
QUALITY_GATE_HEADER = (
    "  # ═══════════════════════════════════════════════════════════════════════════════════════════════\n"
    "  # Quality Gate: All required checks must pass\n"
)

JOB = r"""  # ═══════════════════════════════════════════════════════════════════════════════════════════════
  # Host Tooling (macOS) -- ADVISORY (turing bring-up G4). The host-tooling suites run here under
  # BSD userland and /bin/bash 3.2, which the Linux regression step cannot show: each suite calls
  # /bin/bash itself, and on macos-latest that is 3.2. A step asserts it, and that `brew --prefix`
  # is not turing's Intel /usr/local, so a green run also shows the scripts are prefix-independent.
  #
  # No on.paths filter (it would skip all of ci.yml). The detection step sets `relevant`, and every
  # later step is gated on it, so the job reports success when no host-tooling path changed; it
  # always runs on push and dispatch. It is absent from the Quality Gate `needs:`. After 10
  # consecutive green runs it becomes required by joining required-checks.needs, never as a
  # separate ruleset context. Gate: tests/test_ci_host_tooling_macos.py, which also runs the
  # detection shell under a stub git.
  # ═══════════════════════════════════════════════════════════════════════════════════════════════
  host-tooling-macos:
    name: Host Tooling (macOS)
    runs-on: macos-latest
    timeout-minutes: 30
    permissions:
      contents: read
    env:
      # The suites (tests/test_<name>.py) and the other paths whose change re-runs the job;
      # tests/redacted_env.py and this workflow always count. G1's two suites join when it lands.
      HOST_TOOLING_SUITES: >-
        juniper_clone find_encryption_readme_notes macvm_ctl claude_agent_guard
        git_remote_alias_check headless_signing_preflight juniper_repo_ssh_setup home_path_literal_check
      HOST_TOOLING_PATHS: >-
        util/juniper_clone.bash util/find_encryption_readme_notes.bash util/macvm_ctl.bash
        util/claude_agent_guard.py util/install_claude_agent_guard.bash util/git_remote_alias_check.py
        util/headless_signing_preflight.bash util/juniper_repo_ssh_setup.bash util/home_path_literal_check.py
        conf/home_path_literal_baseline.json .pre-commit-config.yaml
    steps:
      - name: Checkout Code (full history)
        uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
        with:
          fetch-depth: 0

      - name: Detect host-tooling changes
        id: changes
        env:
          EVENT_NAME: ${{ github.event_name }}
          PR_BASE_SHA: ${{ github.event.pull_request.base.sha }}
          MG_BASE_SHA: ${{ github.event.merge_group.base_sha }}
        run: |
          set -euo pipefail
          case "$EVENT_NAME" in
            pull_request) base="$PR_BASE_SHA" ;;
            merge_group) base="$MG_BASE_SHA" ;;
            *)
              echo "relevant=true" >> "$GITHUB_OUTPUT"
              echo "${EVENT_NAME}: the suites always run"
              exit 0
              ;;
          esac
          if ! git cat-file -e "${base}^{commit}" 2>/dev/null; then
            git fetch --no-tags --depth=1 origin "$base"
          fi
          changed="$(git diff --name-only "$base" HEAD)"
          watched="$(mktemp)"
          for suite in $HOST_TOOLING_SUITES; do echo "tests/test_${suite}.py"; done > "$watched"
          for path in $HOST_TOOLING_PATHS tests/redacted_env.py .github/workflows/ci.yml; do echo "$path"; done >> "$watched"
          hits="$(printf '%s\n' "$changed" | grep -F -x -f "$watched" || true)"
          rm -f "$watched"
          if [ -n "$hits" ]; then
            echo "relevant=true" >> "$GITHUB_OUTPUT"
            echo "host-tooling paths changed:"
            printf '%s\n' "$hits" | sed 's/^/  /'
          else
            echo "relevant=false" >> "$GITHUB_OUTPUT"
            echo "no host-tooling path changed; the suites are skipped and the job passes"
          fi

      - name: Set up Python ${{ env.PYTHON_TEST_VERSION }}
        if: steps.changes.outputs.relevant == 'true'
        uses: actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97 # v7.0.0
        with:
          python-version: ${{ env.PYTHON_TEST_VERSION }}

      - name: Install test dependencies
        if: steps.changes.outputs.relevant == 'true'
        run: |
          python -m pip install --upgrade "pip>=26.1.1"
          # PyYAML: the G5 and G6 cases read .pre-commit-config.yaml and ci.yml.
          pip install "pyyaml>=6.0"

      - name: Assert the macOS userland under test
        if: steps.changes.outputs.relevant == 'true'
        run: |
          set -euo pipefail
          bash_major="$(/bin/bash -c 'echo "${BASH_VERSINFO[0]}"')"
          echo "/bin/bash: $(/bin/bash --version | head -1)"
          [ "$bash_major" = 3 ] || { echo "::error::/bin/bash is bash ${bash_major}: this job no longer tests bash 3.2"; exit 1; }
          prefix="$(brew --prefix)"
          echo "brew --prefix: ${prefix} ($(uname -m))"
          [ "$prefix" != /usr/local ] || { echo "::error::brew --prefix is turing's Intel /usr/local, so a green run no longer shows prefix independence"; exit 1; }

      - name: Run the host-tooling suites
        if: steps.changes.outputs.relevant == 'true'
        run: |
          set -uo pipefail
          failed=""
          for suite in $HOST_TOOLING_SUITES; do
            echo "::group::tests/test_${suite}.py"
            python3 -m unittest -v "tests/test_${suite}.py" || failed="$failed $suite"
            echo "::endgroup::"
          done
          if [ -n "$failed" ]; then
            echo "::error::host-tooling suites failed under macOS:${failed}"
            exit 1
          fi

      - name: No host-tooling change
        if: steps.changes.outputs.relevant != 'true'
        run: echo "No host-tooling path changed; the suites are skipped and the job passes."

"""


def edits():
    """(path, marker, anchor, replacement). The replacement keeps the anchor and adds the G4 text."""
    ci_suite = (
        "          # tests/test_ci_host_tooling_macos.py: turing bring-up G4. ci.yml's advisory host-tooling-macos\n"
        "          # job: macos-latest, no path filter, every step after detection gated on its `relevant` output,\n"
        "          # the suite list equal to the turing host-tooling set, /bin/bash 3.x and a non-/usr/local brew\n"
        "          # prefix asserted, absent from the Quality Gate needs. The detection shell runs under a stub git.\n"
        f"          {SUITE_LINE}\n"
    )
    suite_entry = (
        "- `tests/test_ci_host_tooling_macos.py` -- Turing bring-up G4 (`" + PLAN + "`; §9.1, §9.4). "
        "It gates ci.yml's advisory `host-tooling-macos` job, which runs the turing host-tooling suites on `macos-latest` under BSD userland and `/bin/bash` 3.2. "
        "The job must have no workflow path filter and no job-level `if`, must fire on `merge_group`, and must gate every step after `Detect host-tooling changes` on its `relevant` output, with exactly one step reporting the skip. "
        "Its suite list must equal the eight turing host-tooling suites, each of which also runs in the Linux regression step, and every watched path must exist. "
        "A step must assert that `/bin/bash` is 3.x and that `brew --prefix` is not `/usr/local`; the suites run one by one and every failure is named. "
        "The job is absent from the Quality Gate `needs:`, and the promotion after 10 green runs flips that pin. "
        "The detection shell is extracted from ci.yml and run under a stub `git`. Push and dispatch always run without diffing. An unrelated pull request skips. "
        "A suite, a watched script, `tests/redacted_env.py` or ci.yml makes the job run, and a near-miss path does not. `merge_group` diffs against its own base, and a missing base is fetched first.\n"
    )
    job_item = (
        "10. **host-tooling-macos** (ADVISORY; turing bring-up G4) -- Runs the turing host-tooling suites on `macos-latest`, under BSD userland and `/bin/bash` 3.2, after asserting both and that `brew --prefix` is not `/usr/local`. "
        "There is no workflow path filter. A detection step sets `relevant` from the PR or merge-group diff (always true on push and dispatch), and every later step is gated on it, so the job reports success when no host-tooling path changed. "
        "Absent from the Quality Gate `needs:`; after 10 consecutive green runs it becomes required by joining it, never as a separate ruleset context. Gate: `tests/test_ci_host_tooling_macos.py`.\n"
        "11. **required-checks** -- Quality gate enforcing all checks must pass"
    )
    changelog = (
        "- **ci.yml's `host-tooling-macos` job, advisory** (turing bring-up task G4 of\n"
        f"  `{PLAN}`).\n"
        "  - It runs the eight turing host-tooling suites on `macos-latest`, under BSD userland and `/bin/bash` 3.2,\n"
        "    which the Linux regression step cannot show. A step asserts both, and that `brew --prefix` is not\n"
        "    turing's Intel `/usr/local`, so a green run also shows the scripts are prefix-independent.\n"
        "  - No workflow path filter: a detection step sets `relevant` from the pull request or merge-group diff,\n"
        "    and every later step is gated on it, so the job reports success when no host-tooling path changed.\n"
        "  - Absent from the Quality Gate `needs:` until 10 consecutive green runs; it then joins them, never as a\n"
        "    separate ruleset context.\n"
        "  - `tests/test_ci_host_tooling_macos.py` (new) gates the job's shape and runs the detection shell under a\n"
        "    stub `git`. It is wired into `ci.yml` and `docs/REFERENCE.md`.\n"
        "\n"
    )
    return [
        (CI, "  host-tooling-macos:\n", QUALITY_GATE_HEADER, JOB + QUALITY_GATE_HEADER),
        (CI, SUITE_LINE, "\n\n      - name: Run bash regression tests\n", "\n" + ci_suite + "\n      - name: Run bash regression tests\n"),
        (REFERENCE, SUITE_LINE, "\nbash scripts/test_resume_file_safety.bash\n# doc-link validator", f"\n{SUITE_LINE}\nbash scripts/test_resume_file_safety.bash\n# doc-link validator"),
        (REFERENCE, "- `tests/test_ci_host_tooling_macos.py` --", "- `scripts/test.bash` -- Manual end-to-end harness", suite_entry + "- `scripts/test.bash` -- Manual end-to-end harness"),
        (REFERENCE, "**217** with G4's", RUN_LIST_COUNTS, RUN_LIST_COUNTS + ", **217** with G4's `tests/test_ci_host_tooling_macos.py`"),
        (REFERENCE, "**host-tooling-macos** (ADVISORY", "10. **required-checks** -- Quality gate enforcing all checks must pass", job_item),
        # Directly below G2's entry: not at the top of [Unreleased] / ### Added, where concurrent PRs insert theirs, and
        # not below G5's, where G6 goes. Two insertions at one spot conflict on update-branch (juniper-ml#2273 vs #2274).
        ("CHANGELOG.md", "**ci.yml's `host-tooling-macos` job, advisory**", G2_CHANGELOG_TAIL, G2_CHANGELOG_TAIL + changelog),
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
