"""
Apply turing bring-up G4's promotion, idempotently: host-tooling-macos joins the Quality Gate's needs.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-20
Status: ad-hoc — one-off (turing bring-up task G4's promotion step)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (task G4: "Advisory first; required
         after 10 green runs by adding it to the Quality Gate's required-checks.needs, never as a separate ruleset
         context"; §17.3 E-LAND-2); tests/test_ci_host_tooling_macos.py; tests/test_ci_quality_gate.py;
         util/ad-hoc/2026-10-20_turing_g4_apply.py (G4 itself)

Provenance: drafted by the "mac dev env" session, which never ran it against main and handed the promotion over;
reviewed, extended (the regression-step comment, REFERENCE's suite entry, the hard-predicate pin and the
12-run streak) and landed by the "code signing" session.

Why: G4 landed the job advisory (juniper-ml#2276). Its promotion criterion is 10 consecutive green runs. The ci.yml
push runs on main from 3968ca04 (G4's merge) to e3ba1936 (G1's merge) each ran the suites and passed: 12 in a row,
checked job by job through the Actions API on 2026-10-20. The last of them ran all eleven suites, G1's two included.
The Quality Gate runs `if: always()` and tests each `needs.<job>.result` itself, so joining `needs:` gates nothing
without an `if` arm in its script (tests/test_ci_quality_gate.py says so). This script adds both.

The edits:
- ci.yml: `host-tooling-macos` appended to required-checks `needs:`, a status echo line, and a `!= "success"` arm. The
  job reports success when no host-tooling path changed and always runs on push, so it never reads skipped.
- ci.yml: the job's banner says REQUIRED and records the promotion; the regression step's comment for its gate follows.
- tests/test_ci_quality_gate.py: REQUIRED_NEEDS gains the job (with its reason), the hard-predicate pin gains it, and
  failure and skipped rehearsals are added.
- tests/test_ci_host_tooling_macos.py: test_the_job_is_advisory becomes test_the_job_is_required_through_the_quality_gate;
  the docstring follows.
- docs/REFERENCE.md: the CI/CD Pipeline Reference job item and the suite entry say required.
- CHANGELOG.md: a [Unreleased] / Changed entry, at the end of that section (clear of the contended top).

Each edit has a marker. When the marker is already present the edit is skipped; otherwise its anchor must occur
exactly once. A re-run on a newer main therefore applies cleanly or stops loudly.

Usage:
    python3 -I util/ad-hoc/2026-10-20_turing_g4_promote_apply.py [--root REPO_ROOT] [--dry-run]

Exit 0 = every edit applied or already present; 1 = an anchor is missing or ambiguous (nothing written).
"""

import argparse
import sys
from pathlib import Path

PLAN = "notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md"
CI = ".github/workflows/ci.yml"
REFERENCE = "docs/REFERENCE.md"
QG_TEST = "tests/test_ci_quality_gate.py"
G4_TEST = "tests/test_ci_host_tooling_macos.py"
NEEDS = "    needs: [pre-commit, tests, build, docs, security, claude-yaml-audit, ruleset-scope-guard, dependency-docs, sops-validation"
STREAK = "12 consecutive green push runs on main (3968ca04 to e3ba1936)"


def edits():
    """(path, marker, anchor, replacement)."""
    sops_arm = '          if [[ "${{ needs.sops-validation.result }}" != "success" ]]; then\n            echo "::error::SOPS structural validation failed"\n            exit 1\n          fi\n'
    host_arm = (
        '          if [[ "${{ needs.host-tooling-macos.result }}" != "success" ]]; then\n'
        '            echo "::error::Host tooling suites failed under macOS (BSD userland, /bin/bash 3.2)"\n'
        "            exit 1\n"
        "          fi\n"
    )
    old_banner = "  # Host Tooling (macOS) -- ADVISORY (turing bring-up G4). The host-tooling suites run here under\n"
    new_banner = "  # Host Tooling (macOS) -- REQUIRED (turing bring-up G4). The host-tooling suites run here under\n"
    old_promo = (
        "  # always runs on push and dispatch. It is absent from the Quality Gate `needs:`. After 10\n"
        "  # consecutive green runs it becomes required by joining required-checks.needs, never as a\n"
        "  # separate ruleset context. Gate: tests/test_ci_host_tooling_macos.py, which also runs the\n"
    )
    new_promo = (
        "  # always runs on push and dispatch. It joined the Quality Gate `needs:` on 2026-10-20, after\n"
        f"  # {STREAK}, never as a separate ruleset context.\n"
        "  # Gate: tests/test_ci_host_tooling_macos.py, which also runs the\n"
    )
    old_step_comment = "          # prefix asserted, absent from the Quality Gate needs. The detection shell runs under a stub git.\n"
    new_step_comment = "          # prefix asserted, a hard Quality Gate need since 2026-10-20. The detection shell runs under a stub git.\n"
    old_step_head = "          # tests/test_ci_host_tooling_macos.py: turing bring-up G4. ci.yml's advisory host-tooling-macos\n"
    new_step_head = "          # tests/test_ci_host_tooling_macos.py: turing bring-up G4. ci.yml's required host-tooling-macos\n"
    qg_required = '    "sops-validation",\n)'
    qg_required_new = '    "sops-validation",\n' '    "host-tooling-macos",\n' ")"
    qg_reason_anchor = "# script gates NOTHING. The rehearsal arm below is what proves this one bites.\n"
    qg_reason = (
        "# script gates NOTHING. The rehearsal arm below is what proves this one bites.\n"
        "#\n"
        "# ``host-tooling-macos`` joined 2026-10-20 (turing bring-up G4's promotion, after 12 consecutive green\n"
        "# push runs on main). It has no job-level ``if`` and no path filter: on a pull request with no host-tooling\n"
        "# change it reports success, and on push it always runs the suites, so it never reads skipped. A hard need,\n"
        "# with its own ``!= success`` arm.\n"
    )
    qg_hard_old = '        for job in ("pre-commit", "tests", "build", "docs", "claude-yaml-audit", "dependency-docs"):\n'
    qg_hard_new = '        for job in ("pre-commit", "tests", "build", "docs", "claude-yaml-audit", "dependency-docs", "host-tooling-macos"):\n'
    qg_tests_anchor = "    def test_tests_skipped_fails_gate(self) -> None:\n"
    qg_tests = (
        "    def test_host_tooling_macos_failure_fails_gate(self) -> None:\n"
        '        """Negative control for the arm added with G4\'s promotion (2026-10-20)."""\n'
        "        results = self._all_success()\n"
        '        results["host-tooling-macos"] = "failure"\n'
        "        proc = self._run(results)\n"
        "        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)\n"
        '        self.assertIn("Host tooling suites failed under macOS", proc.stdout + proc.stderr)\n'
        "\n"
        "    def test_host_tooling_macos_skipped_fails_gate(self) -> None:\n"
        "        results = self._all_success()\n"
        '        results["host-tooling-macos"] = "skipped"\n'
        "        proc = self._run(results)\n"
        "        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)\n"
        "\n"
        "    def test_tests_skipped_fails_gate(self) -> None:\n"
    )
    g4_doc_old = (
        "- advisory first. After 10 green runs it becomes required by joining the Quality Gate's\n"
        "  ``required-checks.needs``, never as a separate ruleset context. ``test_the_job_is_advisory`` pins today's\n"
        "  state, and the promotion changes it on purpose.\n"
    )
    g4_doc_new = (
        "- required through the Quality Gate. It was advisory until 2026-10-20, when, after 12 consecutive green push\n"
        "  runs on main, it joined ``required-checks.needs`` with its own ``!= success`` arm, never as a separate\n"
        "  ruleset context. ``test_the_job_is_required_through_the_quality_gate`` pins that.\n"
    )
    g4_test_old = (
        "    def test_the_job_is_advisory(self) -> None:\n"
        "        # The promotion (plan G4: after 10 green runs) adds the job here and flips this assertion.\n"
        '        needs = self.workflow["jobs"]["required-checks"]["needs"]\n'
        "        self.assertNotIn(JOB, needs)\n"
    )
    g4_test_new = (
        "    def test_the_job_is_required_through_the_quality_gate(self) -> None:\n"
        "        # Promoted 2026-10-20 after 12 consecutive green push runs (plan G4). A need with no arm gates nothing.\n"
        "        # It replaces test_the_job_is_advisory; the promotion's commits waive that loss (Allow-Symbol-Loss).\n"
        '        gate = self.workflow["jobs"]["required-checks"]\n'
        '        self.assertIn(JOB, gate["needs"])\n'
        '        script = next(s for s in gate["steps"] if s.get("name") == "Check Quality Gate Status")["run"]\n'
        "        self.assertIn('if [[ \"${{ needs.host-tooling-macos.result }}\" != \"success\" ]]; then', script)\n"
    )
    ref_item_old = "10. **host-tooling-macos** (ADVISORY; turing bring-up G4) --"
    ref_item_new = "10. **host-tooling-macos** (REQUIRED through the Quality Gate since 2026-10-20; turing bring-up G4) --"
    ref_item_promo_old = "Absent from the Quality Gate `needs:`; after 10 consecutive green runs it becomes required by joining it, never as a separate ruleset context. Gate: `tests/test_ci_host_tooling_macos.py`."
    ref_item_promo_new = f"It joined the Quality Gate `needs:` on 2026-10-20, after {STREAK}, with its own `!= success` arm, never as a separate ruleset context. Gate: `tests/test_ci_host_tooling_macos.py`."
    ref_suite_old = "The job is absent from the Quality Gate `needs:`, and the promotion after 10 green runs flips that pin."
    ref_suite_new = "The job is in the Quality Gate `needs:` with its own `!= success` arm, since its promotion on 2026-10-20 after 12 consecutive green push runs."
    ref_gates_old = "It gates ci.yml's advisory `host-tooling-macos` job,"
    ref_gates_new = "It gates ci.yml's `host-tooling-macos` job, a hard Quality Gate need since 2026-10-20,"
    changelog = (
        "- **ci.yml's `host-tooling-macos` job is required** (turing bring-up task G4's promotion step, per\n"
        f"  `{PLAN}`).\n"
        f"  - It joins the Quality Gate's `needs:` after {STREAK}, each of which ran the suites;\n"
        "    the last ran all eleven, G1's two included. It has its own `!= success` arm, because the gate tests each\n"
        "    need's result itself.\n"
        "  - It never reads skipped: it has no job-level `if` and no path filter, and on a pull request with no host-tooling\n"
        "    change it reports success.\n"
        "  - `tests/test_ci_quality_gate.py` pins the need and its success predicate, and rehearses its failure and skip;\n"
        "    `tests/test_ci_host_tooling_macos.py` flips its advisory pin.\n"
        "\n"
    )
    return [
        (CI, NEEDS + ", host-tooling-macos]", NEEDS + "]", NEEDS + ", host-tooling-macos]"),
        (
            CI,
            'echo "Host Tooling (macOS): ${{ needs.host-tooling-macos.result }}"',
            '          echo "SOPS Validation:      ${{ needs.sops-validation.result }}"\n',
            '          echo "SOPS Validation:      ${{ needs.sops-validation.result }}"\n          echo "Host Tooling (macOS): ${{ needs.host-tooling-macos.result }}"\n',
        ),
        (CI, host_arm, sops_arm, sops_arm + "\n" + host_arm),
        (CI, new_banner, old_banner, new_banner),
        (CI, "It joined the Quality Gate `needs:` on 2026-10-20", old_promo, new_promo),
        (CI, new_step_comment, old_step_comment, new_step_comment),
        (CI, new_step_head, old_step_head, new_step_head),
        (QG_TEST, '    "host-tooling-macos",\n', qg_required, qg_required_new),
        (QG_TEST, "``host-tooling-macos`` joined 2026-10-20", qg_reason_anchor, qg_reason),
        (QG_TEST, '"dependency-docs", "host-tooling-macos"):', qg_hard_old, qg_hard_new),
        (QG_TEST, "def test_host_tooling_macos_failure_fails_gate", qg_tests_anchor, qg_tests),
        (G4_TEST, "- required through the Quality Gate.", g4_doc_old, g4_doc_new),
        (G4_TEST, "def test_the_job_is_required_through_the_quality_gate", g4_test_old, g4_test_new),
        (REFERENCE, ref_item_new, ref_item_old, ref_item_new),
        (REFERENCE, ref_item_promo_new, ref_item_promo_old, ref_item_promo_new),
        (REFERENCE, ref_suite_new, ref_suite_old, ref_suite_new),
        (REFERENCE, ref_gates_new, ref_gates_old, ref_gates_new),
        # anchor None: the end of [Unreleased] / ### Changed, located by unreleased_changed_end().
        ("CHANGELOG.md", "**ci.yml's `host-tooling-macos` job is required**", None, changelog),
    ]


def unreleased_changed_end(text: str, block: str) -> str | None:
    """Put ``block`` last under [Unreleased] / ### Changed (just before that section's next heading), or None."""
    start = text.find("\n## [Unreleased]\n")
    end = text.find("\n## [", start + 1)
    head = text.find("\n### Changed\n", start, end)
    if start < 0 or head < 0:
        return None
    nxt = text.find("\n### ", head + 1, end)
    at = (nxt if nxt >= 0 else end) + 1
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
            print(f"present  {rel}: {marker.strip()[:60]!r}")
        elif anchor is None:
            new = unreleased_changed_end(text, repl)
            if new is None:
                print(f"FAIL     {rel}: no [Unreleased] / ### Changed heading")
                failed += 1
            else:
                text = new
                print(f"apply    {rel}: end of [Unreleased] / ### Changed")
        elif text.count(anchor) == 1:
            text = text.replace(anchor, repl)
            print(f"apply    {rel}: {marker.strip()[:60]!r}")
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
