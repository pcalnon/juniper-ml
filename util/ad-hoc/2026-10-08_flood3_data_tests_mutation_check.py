#!/usr/bin/env python3
"""
Mutation check for the Cursor flood-3 juniper-data test PRs: apply one targeted mutation at a
time to the production code a suite claims to pin, run that suite, and restore the file.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-10-08
Status: ad-hoc — investigation (flood-3 evaluator ``data-tests``; juniper-data #449-#473)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data #449 #450 #453 #458 #459 #461 #466 #467 #469 #471 #473

Usage::

    python3 util/ad-hoc/2026-10-08_flood3_data_tests_mutation_check.py \\
        --repo /path/to/juniper-data-worktree --out results.json [--only ID ...]

Every mutation must match its anchor EXACTLY ONCE (an anchor that matches zero or several times
is reported as an error, never silently skipped). Each file is restored byte-for-byte from the
in-memory original in a ``finally`` block, and the restore is verified by comparing bytes.
The script runs pytest only; it never runs git.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess  # nosec B404 - runs pytest with a fixed argv
import sys
from pathlib import Path

U = "juniper_data/tests/unit/"
NS = "util/check_image_no_secrets.py"
CP = "util/check_image_cpu_only.py"
SV = "util/check_image_serves.py"
EQ = "juniper_data/generators/equities/generator.py"
NC = ".github/workflows/notify-consumers.yml"
SS = ".github/workflows/sequence-safety.yml"
BA = ".github/workflows/pr-budget-alarm.yml"
BG = ".github/workflows/pr-base-branch-guard.yml"
LU = ".github/workflows/lockfile-update.yml"
CI = ".github/workflows/ci.yml"
MV = ".github/workflows/main-verify.yml"
AM = ".github/workflows/agents-md-touch-up.yml"

# The two image-gate PRs (#449, #450) add the SAME two filenames. Round 1 stages them side by side
# as ``*_p449.py`` / ``*_p450.py``; the consolidated suite keeps the plain name. Missing files are
# skipped, so one list serves both rounds.
NS_SUITES = [U + "test_check_image_no_secrets_p449.py", U + "test_check_image_no_secrets_p450.py", U + "test_check_image_no_secrets.py"]
CP_SUITES = [U + "test_check_image_cpu_only_p449.py", U + "test_check_image_cpu_only_p450.py", U + "test_check_image_cpu_only.py"]

# (id, file, old, new, [test files])
MUTATIONS: list[tuple[str, str, str, str, list[str]]] = [
    # -- check_image_no_secrets.py (#449 / #450) -------------------------------------------------
    ("NS1-suffix-to-substring", NS, "    if name.endswith(ALLOWED_SUFFIXES):\n", "    if any(s in name for s in ALLOWED_SUFFIXES):\n", NS_SUITES),
    ("NS2-zero-files-passes", NS, "    if files_seen == 0:\n", "    if files_seen < 0:\n", NS_SUITES),
    ("NS3-prune-bad-dirs-before-report", NS, "dirnames[:] = [d for d in dirnames if d not in PRUNE_DIRS]", "dirnames[:] = [d for d in dirnames if d not in PRUNE_DIRS and d not in BAD_DIRS]", NS_SUITES),
    ("NS4-follow-symlinks", NS, "os.walk(root)", "os.walk(root, followlinks=True)", NS_SUITES),
    ("NS5-case-insensitive-roots", NS, 'if name.startswith("juniper") or', 'if name.lower().startswith("juniper") or', NS_SUITES),
    # -- check_image_cpu_only.py (#449 / #450) ---------------------------------------------------
    ("CP1-drop-cuda-family", CP, '_FORBIDDEN_PREFIXES = ("nvidia-", "cuda-")', '_FORBIDDEN_PREFIXES = ("nvidia-",)', CP_SUITES),
    ("CP2-absent-ignores-metadata", CP, 'if torch_importable() or "torch" in names:', "if torch_importable():", CP_SUITES),
    ("CP3-unanchored-version-re", CP, r'_CPU_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+\+cpu$")', r'_CPU_VERSION_RE = re.compile(r"^\d+\.\d+\.\d+\+cpu")', CP_SUITES),
    ("CP4-no-strip", CP, 'expect = os.environ.get("EXPECT_TORCH", "").strip()', 'expect = os.environ.get("EXPECT_TORCH", "")', CP_SUITES),
    (
        "CP5-scan-before-usage-check",
        CP,
        '    expect = os.environ.get("EXPECT_TORCH", "").strip()\n',
        '    expect = os.environ.get("EXPECT_TORCH", "").strip()\n    installed_distributions()\n',
        CP_SUITES,
    ),
    # -- check_image_serves.py driver (#461) ------------------------------------------------------
    ("SV1-first-line-cid", SV, "cid = out.splitlines()[-1].strip()", "cid = out.splitlines()[0].strip()", [U + "test_check_image_serves_driver.py"]),
    ("SV2-nonzero-exec-is-status", SV, "    if code != 0 or not out:\n        return None, out\n", "    if not out:\n        return None, out\n", [U + "test_check_image_serves_driver.py"]),
    ("SV3-override-entrypoint", SV, '_docker(["run", "-d", args.image], timeout=120)', '_docker(["run", "-d", "--entrypoint", "python", args.image], timeout=120)', [U + "test_check_image_serves_driver.py"]),
    ("SV4-rm-not-in-finally", SV, '    finally:\n        _docker(["rm", "-f", cid], timeout=60)\n', '    finally:\n        pass\n    _docker(["rm", "-f", cid], timeout=60)\n', [U + "test_check_image_serves_driver.py"]),
    # -- equities generator, W1.8 drop (#453) -----------------------------------------------------
    ("EQ1-no-pre-purchase-drop", EQ, '        if params.fundamentals_fill == "drop":\n            pre_purchase = frame.index < basis_known_from\n', '        if False:\n            pre_purchase = frame.index < basis_known_from\n', [U + "test_equities_cost_basis_drop_edges.py"]),
    ("EQ2-basis-field-ignored", EQ, 'basis_field = params.basis_price_field if params.basis_price_field in frame.columns else "close"', 'basis_field = "close"', [U + "test_equities_cost_basis_drop_edges.py"]),
    ("EQ3-basis-first-row", EQ, "basis = float(on_or_before[basis_field].iloc[-1])", "basis = float(on_or_before[basis_field].iloc[0])", [U + "test_equities_cost_basis_drop_edges.py"]),
    (
        "EQ4-dropna-instead-of-index",
        EQ,
        '        frame["cost_basis"] = np.where(frame.index >= basis_known_from, basis, np.nan)\n',
        '        frame["cost_basis"] = np.where(frame.index >= basis_known_from, basis, np.nan)\n        if params.fundamentals_fill == "drop":\n            frame = frame.dropna(subset=["cost_basis"])\n',
        [U + "test_equities_cost_basis_drop_edges.py"],
    ),
    # -- notify-consumers.yml (#458) --------------------------------------------------------------
    ("NC1-title-prefix-match", NC, "select(.display_title == $title)", "select(.display_title | startswith($title))", [U + "test_notify_consumers_dispatch.py"]),
    ("NC2-unanchored-version", NC, '=~ ^[0-9]+\\.[0-9]+\\.[0-9]+$ ]]', '=~ ^[0-9]+\\.[0-9]+\\.[0-9]+ ]]', [U + "test_notify_consumers_dispatch.py"]),
    ("NC3-unlisted-blamed-on-consumer", NC, "          if (( listed == 0 )); then\n", "          if (( listed == 99 )); then\n", [U + "test_notify_consumers_dispatch.py"]),
    # -- sequence-safety.yml (#459) ---------------------------------------------------------------
    ("SS1-substring-label", SS, "grep -qx 'allow-symbol-loss'", "grep -q 'allow-symbol-loss'", [U + "test_sequence_safety_label_hatch.py"]),
    ("SS2-stderr-as-labels", SS, "--jq '.labels[].name' 2>/dev/null || true)", "--jq '.labels[].name' 2>&1 || true)", [U + "test_sequence_safety_label_hatch.py"]),
    ("SS3-invocation-error-swallowed", SS, 'if [ "${src}" -ge 2 ] || [ "${drc}" -ge 2 ]; then', 'if [ "${src}" -ge 3 ] || [ "${drc}" -ge 3 ]; then', [U + "test_sequence_safety_label_hatch.py"]),
    # -- pr-budget-alarm.yml / pr-base-branch-guard.yml (#466) ------------------------------------
    ("BA1-cursor-substring", BA, 'select(.headRefName | startswith("cursor/"))', 'select(.headRefName | ascii_downcase | contains("cursor"))', [U + "test_pr_budget_alarm.py"]),
    ("BA2-empty-threshold", BA, 'warn="${PR_BUDGET_WARN:-15}"', 'warn="${PR_BUDGET_WARN-15}"', [U + "test_pr_budget_alarm.py"]),
    ("BA3-strict-gt-boundary", BA, 'if [ "$total" -ge "$alarm" ] ||', 'if [ "$total" -gt "$alarm" ] ||', [U + "test_pr_budget_alarm.py"]),
    ("BG1-any-bypass-value", BG, 'if [ "${HAS_BYPASS}" = "true" ]; then', 'if [ -n "${HAS_BYPASS}" ]; then', [U + "test_pr_base_branch_guard.py"]),
    ("BG2-merge-group-not-exempt", BG, 'if [ "${EVENT_NAME}" = "merge_group" ]; then', 'if [ "${EVENT_NAME}" = "merge-group" ]; then', [U + "test_pr_base_branch_guard.py"]),
    ("BG3-prefix-base-match", BG, 'if [ "${BASE_REF}" = "${DEFAULT_BRANCH}" ]; then', 'if [[ "${BASE_REF}" == "${DEFAULT_BRANCH}"* ]]; then', [U + "test_pr_base_branch_guard.py"]),
    # -- lockfile-update.yml / ci.yml lockfile-check (#467) ---------------------------------------
    ("LU1-actor-glob", LU, 'elif [[ "${{ github.actor }}" == "dependabot[bot]" ]]; then', 'elif [[ "${{ github.actor }}" == dependabot* ]]; then', [U + "test_lockfile_signed_commit.py"]),
    ("LU2-graphql-errors-ignored", LU, "          if jq -e '.errors' /tmp/lockfile-commit-result.json > /dev/null; then\n", "          if false; then\n", [U + "test_lockfile_signed_commit.py"]),
    ("LU3-freshness-compares-whole-file", CI, "          grep '^[^[:space:]#]' requirements.lock | sort > /tmp/lock_pins\n", "          sort requirements.lock > /tmp/lock_pins\n", [U + "test_lockfile_signed_commit.py"]),
    # -- main-verify.yml (#469) -------------------------------------------------------------------
    ("MV1-absent-code-is-clean", MV, '          # Absent outputs are treated as an invocation error, never as coverage.\n          src="${SRC:-99}"\n', '          # Absent outputs are treated as an invocation error, never as coverage.\n          src="${SRC:-0}"\n', [U + "test_main_verify_screen_verdicts.py"]),
    ("MV2-finding-unscreened", MV, 'if [ "${src}" -ge 2 ] || [ "${drc}" -ge 2 ]; then', 'if [ "${src}" -ge 1 ] || [ "${drc}" -ge 1 ]; then', [U + "test_main_verify_screen_verdicts.py"]),
    ("MV3-title-prefix-match", MV, "select(.title == env.TITLE)", "select(.title | startswith(env.TITLE))", [U + "test_main_verify_notify_upsert.py"]),
    ("MV4-create-failure-green", MV, '              echo "::error::failed to open the stable-title tracking issue"\n              exit 1\n', '              echo "::error::failed to open the stable-title tracking issue"\n              exit 0\n', [U + "test_main_verify_notify_upsert.py"]),
    ("MV5-webhook-in-payload", MV, "Run: {run_url}\"\n", "Run: {run_url} {os.environ['SLACK_WEBHOOK_URL']}\"\n", [U + "test_main_verify_notify_upsert.py"]),
    # -- ci.yml Quality Gate (#471) ---------------------------------------------------------------
    ("QG1-docs-only-on-failure", CI, 'if [[ "${{ needs.docs.result }}" != "success" ]]; then', 'if [[ "${{ needs.docs.result }}" == "failure" ]]; then', [U + "test_quality_gate_results.py"]),
    ("QG2-security-requires-success", CI, 'if [[ "${{ needs.security.result }}" == "failure" ]]; then', 'if [[ "${{ needs.security.result }}" != "success" ]]; then', [U + "test_quality_gate_results.py"]),
    ("QG3-no-always", CI, "    if: always()\n    needs: [pre-commit, unit-tests, build,", "    needs: [pre-commit, unit-tests, build,", [U + "test_quality_gate_results.py"]),
    # -- agents-md-touch-up.yml (#473) ------------------------------------------------------------
    ("AM1-two-dot-diff", AM, 'if git diff "${BASE_SHA}...HEAD" -- AGENTS.md', 'if git diff "${BASE_SHA}..HEAD" -- AGENTS.md', [U + "test_agents_md_date_check.py"]),
    ("AM2-no-future-check", AM, 'if [[ "$current" > "$today" ]]; then', 'if [[ "$current" > "9999-99-99" ]]; then', [U + "test_agents_md_date_check.py"]),
    ("AM3-last-header-line", AM, "            | head -1 \\\n", "            | tail -1 \\\n", [U + "test_agents_md_date_check.py"]),
]

_SUMMARY = re.compile(r"^=*\s*(\d+ (?:failed|passed|error|skipped).*?) in [0-9.]+s")


def _run_pytest(repo: Path, env_name: str, tests: list[str], path_prefix: str | None = None) -> tuple[int, str]:
    cmd = ["conda", "run", "-n", env_name, "python", "-m", "pytest", "-p", "no:cacheprovider", "-m", "unit and not slow", "--tb=line", "-rf", *tests]
    env = dict(os.environ)
    if path_prefix:
        env["PATH"] = path_prefix + os.pathsep + env.get("PATH", "")
    proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, check=False, timeout=900, env=env)  # nosec B603 B607
    return proc.returncode, proc.stdout + proc.stderr


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    ap.add_argument("--repo", required=True, type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--env", default="JuniperData")
    ap.add_argument("--only", action="append", default=[])
    # Portability probe: run the given suites once, unmutated, with DIR prepended to PATH (e.g. a
    # directory of BSD-behaving `date` / `base64` shims standing in for the macOS runner userland).
    ap.add_argument("--probe-path", help="run --probe suites with this directory prepended to PATH; no mutation")
    ap.add_argument("--probe", nargs="*", default=[])
    args = ap.parse_args()

    if args.probe_path:
        rc, out = _run_pytest(args.repo, args.env, args.probe, path_prefix=args.probe_path)
        print("\n".join(line for line in out.splitlines() if not line.startswith("ERROR conda")))
        print(f"probe rc={rc}")
        return 0
    if args.out is None:
        ap.error("--out is required unless --probe-path is given")

    results = []
    for mid, rel, old, new, tests in MUTATIONS:
        if args.only and mid not in args.only:
            continue
        tests = [t for t in tests if (args.repo / t).is_file()]
        if not tests:
            print(f"{mid:40s} SKIP no suite present", flush=True)
            continue
        target = args.repo / rel
        original = target.read_bytes()
        text = original.decode("utf-8")
        count = text.count(old)
        if count != 1:
            results.append({"id": mid, "file": rel, "error": f"anchor matched {count} times"})
            print(f"{mid:40s} ERROR anchor matched {count} times", flush=True)
            continue
        per_test: dict[str, dict] = {}
        try:
            target.write_text(text.replace(old, new, 1), encoding="utf-8")
            for test in tests:
                rc, out = _run_pytest(args.repo, args.env, [test])
                # pytest 9 reports a failing unittest subTest as SUBFAILED, not FAILED. ``conda run``
                # adds its own "ERROR conda.cli.main_run" line on any non-zero exit; that is not a test.
                failed = [line for line in out.splitlines() if line.startswith(("FAILED ", "SUBFAILED", "ERROR ")) and not line.startswith("ERROR conda")]
                summary = next((m.group(1) for m in map(_SUMMARY.search, reversed(out.splitlines())) if m), "no summary line")
                per_test[test] = {"rc": rc, "summary": summary, "failed": failed}
        finally:
            target.write_bytes(original)
        if target.read_bytes() != original:
            print(f"RESTORE FAILED for {rel}", file=sys.stderr)
            return 3
        killed = {t: (r["rc"] != 0 and any(not line.startswith("ERROR ") for line in r["failed"])) for t, r in per_test.items()}
        results.append({"id": mid, "file": rel, "per_test": per_test, "killed": killed})
        print(f"{mid:40s} " + " | ".join(f"{Path(t).name}: {'KILLED' if k else 'survived'} ({per_test[t]['summary']})" for t, k in killed.items()), flush=True)

    args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
