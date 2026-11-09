#!/usr/bin/env python3
"""
Re-derive the load-bearing claims of juniper-data's flood-4 docs drafts against main's tree and the pinned upstreams.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (generated with Claude Code)
Created: 2026-11-07
Status: ad-hoc -- one-off (Cursor flood-4 consolidation, juniper-data docs carrier)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: juniper-data#509 #510 #511 #515; flood-4 common brief ("re-derive every docs claim")

The flood-4 triage's "TRUE" for docs was a spot-check. Each claim below is a needle that must be present
(or absent) in a named source: a file of the carrier worktree (whose non-doc files are main's), or an
upstream file fetched with `gh api` at the SHA or tag the docs name. Upstream files are saved under
<out>/upstream/ as .txt and only grepped, never executed.

    python3 2026-11-07_flood4_data_docs_claim_check.py <docs worktree> <out dir>

Prints PASS/FAIL per claim and `<p>/<n> claims hold`; exit 0 only when all hold.
"""

from __future__ import annotations

import base64
import json
import re
import subprocess
import sys
from pathlib import Path

UPSTREAM = {
    "cca/branch.ts": ("anthropics/claude-code-action", "src/github/operations/branch.ts", "6d5ae526d25ce88daa2200be073e1a373167f064"),
    "cca/tag-index.ts": ("anthropics/claude-code-action", "src/modes/tag/index.ts", "6d5ae526d25ce88daa2200be073e1a373167f064"),
    "gla/index.js": ("gitleaks/gitleaks-action", "src/index.js", "e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e"),
    "gla/gitleaks.js": ("gitleaks/gitleaks-action", "src/gitleaks.js", "e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e"),
    "gl/root.go": ("gitleaks/gitleaks", "cmd/root.go", "v8.24.3"),
    "gl/git.go": ("gitleaks/gitleaks", "sources/git.go", "v8.24.3"),
    "gl/config.go": ("gitleaks/gitleaks", "config/config.go", "v8.24.3"),
    "gl/rule.go": ("gitleaks/gitleaks", "config/rule.go", "v8.24.3"),
}

# (pr, claim, source, kind, needle). kind: "has" substring, "re" regex, "not" substring absent, "nofile" path absent.
CLAIMS = [
    ("509", "claude.yml pins claude-code-action v1.0.265 at 6d5ae526", ".github/workflows/claude.yml", "re", r"anthropics/claude-code-action@6d5ae526d25ce88daa2200be073e1a373167f064\s+#\s*v1\.0\.265"),
    ("509", "claude.yml checks out with fetch-depth: 1", ".github/workflows/claude.yml", "re", r"fetch-depth:\s*1\b"),
    ("509", "claude.yml on: lists pull_request_review", ".github/workflows/claude.yml", "re", r"(?m)^\s*pull_request_review:"),
    ("509", "claude.yml on: lists pull_request_review_comment", ".github/workflows/claude.yml", "re", r"(?m)^\s*pull_request_review_comment:"),
    ("509", "claude.yml on: does not subscribe to pull_request", ".github/workflows/claude.yml", "re!", r"(?m)^\s*pull_request:\s*$"),
    ("509", "upstream: 'was updated after the trigger' error text", "cca/branch.ts", "has", "was updated after the trigger"),
    ("509", "upstream: '>=' comparison in that error", "cca/branch.ts", "has", ">="),
    ("509", "upstream: activity lookup with per_page 1", "cca/branch.ts", "re", r"per_page:\s*1\b"),
    ("509", "upstream: 'Could not determine when' error", "cca/branch.ts", "has", "Could not determine when"),
    ("509", "upstream: 'head repository is not available, cannot pin the PR version'", "cca/branch.ts", "has", "head repository is not available, cannot pin the PR version"),
    ("509", "upstream: fork checked out as pr-<n>", "cca/branch.ts", "re", r"pr-\$\{"),
    ("509", "upstream: checkout -B <local> <sha>", "cca/branch.ts", "has", 'execGit(["checkout", "-B", localBranch, headSha'),
    ("509", "upstream: 'checked out ... expected' guard", "cca/branch.ts", "re", r"checked out .*expected"),
    ("509", "upstream: pull_request delivery error 'Push again or mention Claude'", "cca/branch.ts", "has", "Push again or mention Claude to run on the latest version"),
    ("509", "upstream: tag mode calls setupBranch", "cca/tag-index.ts", "has", "setupBranch"),
    ("509", "upstream: a non-open PR branches from the base_branch input or the default branch", "cca/branch.ts", "has", "sourceBranch = repoResponse.data.default_branch"),
    ("509", "claude.yml sets no base_branch input", ".github/workflows/claude.yml", "not", "base_branch"),
    ("510", "link-check hook runs only when a .md file is in the commit", ".pre-commit-config.yaml", "re", r"pass_filenames:\s*false\s*\n\s*files:\s*\\\.md\$"),
    ("510", "ci.yml docs job is named Documentation Links", ".github/workflows/ci.yml", "re", r"name:\s*Documentation Links"),
    ("510", "ci.yml installs juniper-doc-tools>=0.1.0,<0.2.0", ".github/workflows/ci.yml", "has", "juniper-doc-tools>=0.1.0,<0.2.0"),
    ("510", "ci.yml installs juniper-ci-tools>=0.9.0,<0.10.0", ".github/workflows/ci.yml", "has", "juniper-ci-tools>=0.9.0,<0.10.0"),
    ("510", "ci.yml runs juniper-lint-workflow-paths", ".github/workflows/ci.yml", "has", "juniper-lint-workflow-paths"),
    ("510", "ci.yml runs juniper-lint-agents-md-version", ".github/workflows/ci.yml", "has", "juniper-lint-agents-md-version"),
    ("510", "ci.yml runs juniper-lint-agents-md-header", ".github/workflows/ci.yml", "has", "juniper-lint-agents-md-header"),
    ("510", "pre-commit hook pins juniper-doc-tools>=0.1.1,<0.2.0", ".pre-commit-config.yaml", "has", "juniper-doc-tools>=0.1.1,<0.2.0"),
    ("510", "pre-commit runs no juniper-lint-* command", ".pre-commit-config.yaml", "not", "juniper-lint-"),
    ("510", "pyproject version is 0.17.1", "pyproject.toml", "re", r'(?m)^version\s*=\s*"0\.17\.1"'),
    ("510", "AGENTS.md **Version**: 0.17.1", "AGENTS.md", "re", r"(?m)^\*\*Version\*\*:\s*0\.17\.1\s*$"),
    ("510", "agents-md-touch-up.yml workflow name AGENTS.md Date Check", ".github/workflows/agents-md-touch-up.yml", "re", r"(?m)^name:\s*AGENTS\.md Date Check"),
    ("510", "agents-md-touch-up.yml job Verify AGENTS.md Last Updated", ".github/workflows/agents-md-touch-up.yml", "has", "Verify AGENTS.md Last Updated"),
    ("510", "agents-md-touch-up.yml never commits or pushes (outside comments)", ".github/workflows/agents-md-touch-up.yml", "re!", r"(?m)^(?!\s*#).*\bgit (push|commit)\b"),
    ("510", "no scripts/check_doc_links.py", "scripts/check_doc_links.py", "nofile", ""),
    ("510", "no util/test_workflow_script_paths.py", "util/test_workflow_script_paths.py", "nofile", ""),
    ("510", "no util/test_agents_md_version_drift.py", "util/test_agents_md_version_drift.py", "nofile", ""),
    ("511", "ci.yml pins gitleaks-action v3.0.0 at e0c47f4f", ".github/workflows/ci.yml", "re", r"gitleaks/gitleaks-action@e0c47f4f8be36e29cdc102c57e68cb5cbf0e8d1e\s+#\s*v3\.0\.0"),
    ("511", "ci.yml GITLEAKS_VERSION 8.24.3", ".github/workflows/ci.yml", "re", r"GITLEAKS_VERSION:\s*\"?8\.24\.3"),
    ("511", "ci.yml skips on repository_dispatch", ".github/workflows/ci.yml", "has", "github.event_name != 'repository_dispatch'"),
    ("511", "ci.yml self-test command", ".github/workflows/ci.yml", "has", "python -m pytest juniper_data/tests/unit/test_gitleaks_config.py -v"),
    ("511", "ci.yml GITLEAKS_PARITY_REQUIRED", ".github/workflows/ci.yml", "has", "GITLEAKS_PARITY_REQUIRED"),
    ("511", "security-scan.yml has no gitleaks", ".github/workflows/security-scan.yml", "not", "gitleaks"),
    ("511", ".gitleaks.toml [extend] useDefault = true", ".gitleaks.toml", "re", r"\[extend\]\s*\n\s*useDefault\s*=\s*true"),
    ("511", ".gitleaks.toml generic-api-key entry", ".gitleaks.toml", "has", 'id = "generic-api-key"'),
    ("511", ".gitleaks.toml AND condition", ".gitleaks.toml", "re", r'condition\s*=\s*"AND"'),
    ("511", ".gitleaks.toml allowlisted commit 4bd37a6c", ".gitleaks.toml", "has", "4bd37a6c7057e7380cd4470fcc717a76289fa193"),
    ("511", ".gitleaks.toml conda paths", ".gitleaks.toml", "has", "requirements-conda"),
    ("511", "test_gitleaks_config.py reads GITLEAKS_VERSION from ci.yml", "juniper_data/tests/unit/test_gitleaks_config.py", "has", "GITLEAKS_VERSION"),
    ("511", "test_gitleaks_config.py exercises github-pat", "juniper_data/tests/unit/test_gitleaks_config.py", "has", "github-pat"),
    ("511", "upstream action default engine 8.24.3", "gla/index.js", "has", "8.24.3"),
    ("511", "upstream action: GITLEAKS_LICENSE for organizations", "gla/index.js", "has", "GITLEAKS_LICENSE"),
    ("511", "upstream action: GITLEAKS_ENABLE_COMMENTS == \"false\" skips comments", "gla/gitleaks.js", "has", 'GITLEAKS_ENABLE_COMMENTS == "false"'),
    ("511", "upstream action: BASE_REF", "gla/index.js", "has", "BASE_REF"),
    ("511", "upstream action: --no-merges --first-parent range", "gla/gitleaks.js", "has", "--no-merges --first-parent"),
    ("511", "upstream action: still calls detect", "gla/gitleaks.js", "has", "detect"),
    ("511", "upstream engine: GITLEAKS_CONFIG_TOML", "gl/root.go", "has", "GITLEAKS_CONFIG_TOML"),
    ("511", "upstream engine: --full-history --all", "gl/git.go", "has", "--full-history"),
    ("511", "engine: the global [allowlist] has no Condition field (OR-only)", "gl/config.go", "re", r"Allowlist struct \{\s*Commits\s+\[\]string\s*Paths\s+\[\]string\s*RegexTarget\s+string\s*Regexes\s+\[\]string\s*StopWords\s+\[\]string\s*\}"),
    ("511", "engine: no targetRules key is read (dropped)", "gl/config.go", "not", "TargetRules"),
    ("511", "engine: per-rule allowlists carry a Condition (the AND list)", "gl/config.go", "has", "c := strings.ToUpper(a.Condition)"),
    ("511", "engine: extend.useDefault loads the default rules", "gl/config.go", "has", "c.extendDefault()"),
    ("511", "engine: empty-rule refusal text", "gl/rule.go", "has", "both |regex| and |path| are empty, this rule will have no effect"),
    ("511", "carrier quotes that refusal text exactly (corrected from the draft's paraphrase)", "docs/ci_cd/CICD_MANUAL.md", "has", "`generic-api-key: both |regex| and |path| are empty, this rule will have no effect`"),
    ("515", "registry has 16 generators", "juniper_data/api/routes/generators.py", "py-registry", "16"),
    ("515", "_sequence.py defines window_one_ticker", "juniper_data/generators/_sequence.py", "has", "def window_one_ticker"),
    ("515", "_sequence.py defines window_regular_series", "juniper_data/generators/_sequence.py", "has", "def window_regular_series"),
    ("515", "_sequence.py defines window_timed_series", "juniper_data/generators/_sequence.py", "has", "def window_timed_series"),
    ("515", "core/split.py defines temporal_split_indices", "juniper_data/core/split.py", "has", "def temporal_split_indices"),
    ("515", "test_sequence_windowing_leakage.py exists", "juniper_data/tests/unit/test_sequence_windowing_leakage.py", "has", "def test"),
    ("515", "test_multi_sine_generator.py exists", "juniper_data/tests/unit/test_multi_sine_generator.py", "has", "def test"),
    ("515", "test_ar_p_generator.py exists", "juniper_data/tests/unit/test_ar_p_generator.py", "has", "def test"),
    ("515", "test_delay_product_generator.py exists", "juniper_data/tests/unit/test_delay_product_generator.py", "has", "def test"),
]


def fetch(out: Path) -> dict[str, str]:
    texts: dict[str, str] = {}
    up = out / "upstream"
    up.mkdir(parents=True, exist_ok=True)
    for key, (repo, path, ref) in UPSTREAM.items():
        proc = subprocess.run(["gh", "api", f"repos/{repo}/contents/{path}?ref={ref}"], capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            texts[key] = ""
            print(f"FETCH-FAIL {key}: {proc.stderr.strip()[:200]}")
            continue
        text = base64.b64decode(json.loads(proc.stdout)["content"]).decode("utf-8")
        (up / (key.replace("/", "__") + ".txt")).write_text(text, encoding="utf-8")
        texts[key] = text
    return texts


def main(argv: list[str]) -> int:
    root = Path(argv[1])
    out = Path(argv[2])
    upstream = fetch(out)
    held = 0
    for pr, claim, source, kind, needle in CLAIMS:
        if kind == "nofile":
            ok = not (root / source).exists()
        elif kind == "py-registry":
            proc = subprocess.run(
                ["/opt/miniforge3/envs/JuniperData/bin/python", "-c", "from juniper_data.api.routes.generators import GENERATOR_REGISTRY as r; print(len(r)); print(sorted(r))"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            ok = proc.returncode == 0 and proc.stdout.splitlines()[0].strip() == needle
            claim = f"{claim} ({proc.stdout.strip()[:300]})"
        else:
            text = upstream.get(source, "") if source in upstream else ((root / source).read_text(encoding="utf-8") if (root / source).exists() else "")
            if not text:
                ok = False
                claim += " [source unreadable]"
            elif kind == "has":
                ok = needle in text
            elif kind == "not":
                ok = needle not in text
            elif kind == "re":
                ok = re.search(needle, text) is not None
            elif kind == "re!":
                ok = re.search(needle, text) is None
            else:
                raise SystemExit(f"bad kind {kind}")
        held += ok
        print(f"{'PASS' if ok else 'FAIL'} #{pr} {claim} [{source}]")
    print(f"{held}/{len(CLAIMS)} claims hold")
    return 0 if held == len(CLAIMS) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
