"""
One-shot rename of notes/*.md to the JUNIPER_<DATE>_JUNIPER-<REPO>_<PHRASE>.md convention.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-07-04
Status: ad-hoc — one-off migration
Retire when: the notes/ naming-convention migration PR is merged and verified
Related: notes/ naming-convention migration PR (chore/notes-naming-convention)

Scope (per owner decision 2026-07-04): all tracked notes/**/*.md EXCEPT
notes/{legacy,releases,requirements,templates}/ and README.md files.
Date: first YYYY-MM-DD in the filename, else the file's last git-commit date.
Tag: one of ML, CANOPY, RECURRENCE, CASCOR, CASCOR-CLIENT, CASCOR-WORKER,
DATA, DATA-CLIENT, DEPLOY, ECOSYSTEM (ECOSYSTEM = cross-repo/platform-wide).

Usage:  python util/ad-hoc/2026-07-04_notes_rename_convention.py [--apply]
Default is a dry run that prints the old->new mapping as TSV on stdout.
"""

import re
import subprocess
import sys

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
EXCLUDED_DIRS = ("legacy/", "releases/", "requirements/", "templates/")
VALID_TAGS = {"ML", "CANOPY", "RECURRENCE", "CASCOR", "CASCOR-CLIENT", "CASCOR-WORKER", "DATA", "DATA-CLIENT", "DEPLOY", "ECOSYSTEM"}
NEW_NAME_RE = re.compile(r"^JUNIPER_\d{4}-\d{2}-\d{2}_JUNIPER-(ML|CANOPY|RECURRENCE|CASCOR|CASCOR-CLIENT|CASCOR-WORKER|DATA|DATA-CLIENT|DEPLOY|ECOSYSTEM)_[A-Z0-9][A-Z0-9-]*\.md$")

DIR_DEFAULT_TAG = {
    "code-review": "ECOSYSTEM",
    "concurrency": "CASCOR",
    "development": "ECOSYSTEM",
    "development/partials": "ECOSYSTEM",
    "documentation": "ECOSYSTEM",
    "interface_proposals": "ECOSYSTEM",
    "observability": "ECOSYSTEM",
    "proposals": "CASCOR",
    "pull_requests": "ML",
    "regressions": "ECOSYSTEM",
}

TOP_PREFIX_TAGS = [
    ("JUNIPER_CANOPY_", "CANOPY"),
    ("JUNIPER_CASCOR_", "CASCOR"),
    ("JUNIPER_RECURRENCE_", "RECURRENCE"),
    ("JUNIPER_RECURSE_", "RECURRENCE"),
    ("JUNIPER_MODEL_CORE_", "ML"),
    ("JUNIPER_SERVICE_CORE_", "ML"),
    ("JUNIPER_ML_", "ML"),
    ("JUNIPER_CI-TOOLS_", "ML"),
    ("JUNIPER_CI_TOOLS_", "ML"),
    ("JUNIPER_CONFIG_TOOLS_", "ML"),
    ("JUNIPER_DOC_TOOLS_", "ML"),
    ("JUNIPER_DEPLOY_", "DEPLOY"),
    ("JUNIPER_ECOSYSTEM_", "ECOSYSTEM"),
]

# Content-based classification for files whose names alone are ambiguous.
OVERRIDE_TAGS = {
    # top-level
    "CAN_013_INTEGRATION_MODE_DESIGN.md": "CASCOR",
    "CASCOR_CONDA_ENV_FIX_2026-05-07.md": "CASCOR",
    "CASCOR_FIT_KWARGS_LATENT_BUG.md": "CASCOR",
    "CI_TOOLS_EXTRACTION_PLAYBOOK.md": "ML",
    "CONDA_DEPENDENCY_FILE_HEADER.md": "ML",
    "DEPENDENCY_UPDATE_WORKFLOW.md": "CANOPY",
    "JUNIPER-ML_OTHER_DEPENDENCIES.md": "ML",
    "JUNIPER_WS6_APHASE_READINESS_VALIDATION_2026-06-22.md": "CASCOR",
    "JUNIPER_juniper-ml_agent-suite-convenience-utilities_DESIGN_2026-06-25.md": "ML",
    "MCP_SERVER_SETUP_PLAN.md": "ML",
    "META_PACKAGE_EXTRAS_REQUIREMENTS_2026-05-21.md": "ML",
    "P1_RC4_INVESTIGATION_PLAN_2026-05-03.md": "CASCOR",
    "PIP_DEPENDENCY_FILE_HEADER.md": "ML",
    "POST_V38_OPEN_ISSUES_PLAN_2026-05-03.md": "CASCOR",
    "PROMPT_ANALYSIS_AND_AUTOMATION_PLAN.md": "ML",
    "STATUS_ROADMAP_AUDIT_2026-05-19.md": "ML",
    "THREAD_HANDOFF_IMPLEMENTATION.md": "ML",
    "THREAD_HANDOFF_PROCEDURE.md": "ML",
    "V38_GROW_NETWORK_INVESTIGATION_PLAN_2026-05-02.md": "CASCOR",
    "WORKTREE_CLEANUP_PROCEDURE_V2.md": "ML",
    "WORKTREE_SETUP_PROCEDURE.md": "ML",
    "canopy_frontend_issues_plan_2026-05-09.md": "CANOPY",
    "temp.md": "CANOPY",
    # subdirectories
    "code-review/CASCOR_CODE_REVIEW_FINDINGS_2026-04-04.md": "CASCOR",
    "code-review/CASCOR_COMPREHENSIVE_CODE_REVIEW_PLAN_2026-04-04.md": "CASCOR",
    "development/DASHBOARD_AUGMENTATION_PLAN.md": "CANOPY",
    "development/META_PARAMETERS_ENHANCEMENT_PLAN.md": "CANOPY",
    "observability/CANOPY_DASHBOARD_SELF_CALL_REFACTOR_2026-05-10.md": "CANOPY",
    "observability/GRAFANA_DASHBOARDS_STATE_AND_GAPS_2026-05-10.md": "DEPLOY",
    "observability/REGISTER_OR_REUSE_HELPER_DESIGN_2026-05-05.md": "ML",
    "proposals/PROPOSAL_08_UI_LOCK_AND_VISUALIZATION.md": "CANOPY",
    "regressions/REGRESSION_ANALYSIS_05_2026-04-02.md": "CASCOR",
    "regressions/REGRESSION_ANALYSIS_06_2026-04-02.md": "CANOPY",
    "regressions/REGRESSION_ANALYSIS_07_2026-04-02.md": "CASCOR",
}


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def in_scope_files():
    out = []
    for path in git("ls-files", "notes/").splitlines():
        rel = path[len("notes/"):]
        if not path.endswith(".md") or rel.startswith(EXCLUDED_DIRS) or rel.rsplit("/", 1)[-1] == "README.md":
            continue
        out.append(path)
    return out


def classify(rel):
    if rel in OVERRIDE_TAGS:
        return OVERRIDE_TAGS[rel]
    if "/" in rel:
        return DIR_DEFAULT_TAG[rel.rsplit("/", 1)[0]]
    for prefix, tag in TOP_PREFIX_TAGS:
        if rel.startswith(prefix):
            return tag
    return "ECOSYSTEM"


def doc_date(path, basename):
    m = DATE_RE.search(basename)
    if m:
        return m.group(0)
    return git("log", "-1", "--format=%ad", "--date=format:%Y-%m-%d", "--", path).strip()


def phrase_for(basename, tag):
    stem = DATE_RE.sub("", basename[:-3])  # drop .md and every date token
    tokens = [t for t in re.split(r"[_\s.]+", stem) if t]
    drop = {"JUNIPER", tag, f"JUNIPER-{tag}"}
    kept = [t.upper() for t in tokens if t.upper() not in drop]
    phrase = re.sub(r"-{2,}", "-", "-".join(kept)).strip("-")
    return phrase


def build_mapping():
    mapping, errors = [], []
    for path in in_scope_files():
        rel = path[len("notes/"):]
        basename = rel.rsplit("/", 1)[-1]
        subdir = rel.rsplit("/", 1)[0] + "/" if "/" in rel else ""
        tag = classify(rel)
        if tag not in VALID_TAGS:
            errors.append(f"BAD TAG {tag}: {path}")
            continue
        new_base = f"JUNIPER_{doc_date(path, basename)}_JUNIPER-{tag}_{phrase_for(basename, tag)}.md"
        if not NEW_NAME_RE.match(new_base):
            errors.append(f"BAD NEW NAME {new_base}: {path}")
            continue
        mapping.append((path, f"notes/{subdir}{new_base}"))
    seen = {}
    for old, new in mapping:
        if new in seen:
            errors.append(f"COLLISION {new}: {seen[new]} vs {old}")
        seen[new] = old
    return mapping, errors


def main():
    apply_moves = "--apply" in sys.argv[1:]
    mapping, errors = build_mapping()
    for old, new in mapping:
        print(f"{old}\t{new}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    if apply_moves:
        for old, new in mapping:
            subprocess.run(["git", "mv", old, new], check=True)
        print(f"APPLIED {len(mapping)} renames", file=sys.stderr)
    else:
        print(f"DRY RUN: {len(mapping)} renames planned (use --apply)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
