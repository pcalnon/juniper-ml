#!/usr/bin/env python3
"""
The reviewed decisions of the technical-owner sweep: every token juniper-ml#2606 renamed that is NOT the person.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-11-24
Status: ad-hoc — migration (the technical-owner sweep that follows juniper-ml#2606)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (Overtoad policy 2026-08-25)
Related: juniper-ml#2606; util/ad-hoc/2026-11-24_technical_owner_candidates.py (the candidate list this reads);
    util/ad-hoc/2026-11-24_technical_owner_restore.py (applies the list this writes)

How the decisions were reached
------------------------------
The candidate list (7,741 renamed tokens in 2,068 files, base ``515e16a0``, head ``5a049144``) was reviewed in
slices, each by hand: the Unix-ownership and shape nets (720 rows), the strong technical vocabulary (263), every
token in code, a code string, a fenced block or a code span (82), every ``Owner:`` field label, the generic
determiners ("an owner", "no owner", "its own owner"), the words before and after the token, and every token in
``notes/interface_proposals/`` and ``notes/code-review/``. The remaining 1,830 rows went to four review lanes
with a high-recall brief; each lane's 171 flags were then judged here, one by one, against the base line.
That gave 327. Then the regression run found a test needle (``owner root``) that asserts a restored message,
the backup lane's review found two mutant labels, and a manual pass over every token in a code-adjacent string
and over the shape ``classify`` keeps (``its`` / ``their`` / ``whose`` owner, then a verb) found the rest: 340.

Categories
----------
UNIX    Unix ownership of a file, directory or process ("mode and owner", "owner:group", owner-only bits)
GITHUB  a GitHub or registry owner: the account a repository belongs to, a trusted-publisher field
CODE    code or a code snippet: a GraphQL argument, an identifier, an object key, a regex alternative
FIELD   a field that names the owning repository or requirement area ("Owner: juniper-ml", "Owner repo")
ROLE    a generic role that is not the person ("each phase owner", "an assigned owner", a code owner)
GPG     GPG's owner trust
TECH    another technical owner (a race's winner, the per-repo ``latest`` badge)

Usage
-----
    python3 util/ad-hoc/2026-11-24_technical_owner_decisions.py --candidates tmp/x/all_5a049144.tsv --out LIST.tsv
"""

from __future__ import annotations

import argparse
import sys

RI = "notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-1-RECORD.md"
SR = "notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-STEP-REPORTS-RECORD.md"
ID = "notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md"
R2 = "notes/JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_BACKUP-DESIGN-CONSENSUS-ROUND-2-RECORD.md"
SA = "notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md"
PB = "notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_BACKUP-PHASE-B-CONSENSUS-RECORD.md"
CP = "notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md"
CS = "notes/JUNIPER_2026-10-19_JUNIPER-ECOSYSTEM_COMMIT-SIGNING-TERMINAL-AND-IDE-PLAN.md"
E2E = "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md"
CDP = "notes/JUNIPER_2026-06-26_JUNIPER-CANOPY_DEBUG-PROMPT-ANALYSIS.md"
TSA = "notes/JUNIPER_2026-06-26_JUNIPER-ECOSYSTEM_TEST-SUITE-AUDIT-PLAN.md"
CAP = "notes/JUNIPER_2026-06-26_JUNIPER-ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS-PROMPT-ANALYSIS.md"
TSP = "notes/JUNIPER_2026-06-26_JUNIPER-ML_TEST-SUITE-AUDIT-PROMPT-ANALYSIS.md"
CAE = "notes/JUNIPER_2026-06-27_JUNIPER-ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS-PLAN.md"
PMT = "notes/code-review/JUNIPER_2026-05-05_JUNIPER-ECOSYSTEM_POST-METRICS-MON-TRACKER.md"
RIP = "notes/JUNIPER_2026-05-11_JUNIPER-ECOSYSTEM_REQUIREMENTS-IDENTIFICATION-PLAN.md"
GEN = "prompts/generated/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_2026-06-26_2048.md"
H5U = "notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-UNVETTED-MCP-SERVERS-AUDIT.md"
PRG = "notes/JUNIPER_2026-08-20_JUNIPER-ECOSYSTEM_PR-BASE-BRANCH-GUARD-AUDIT.md"
CQ = "notes/JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_CODE-QUALITY-RULE-AUDIT.md"
SP = "notes/JUNIPER_2026-08-18_JUNIPER-ECOSYSTEM_STRICT-POLICY-COST-BENEFIT-AUDIT.md"
YAP = "util/ad-hoc/yamaguchi_acceptance_probe.py"
YSA = "util/ad-hoc/yamaguchi_server_api.py"
CSB = "util/ad-hoc/2026-10-03_clear_stop_and_sync_backup_design.py"
L2F = "util/ad-hoc/2026-09-24_round42_probes/handoff-consolidated-round2-laneF/live1.py"
L4F = "util/ad-hoc/2026-09-24_round42_probes/handoff-consolidated-round4-laneF/gh_probe.py"
PSM = "util/ad-hoc/2026-09-10_soak_stopping_rule/patch_safe_merge2.py"

# (path, line, occurrence on the base line, category, reason)
DECISIONS: list[tuple[str, int, int, str, str]] = [
    # --- UNIX: file, directory and process ownership ---
    (".github/workflows/ci.yml", 1224, 1, "UNIX", "(path, mode, owner) of a refused file"),
    ("docs/REFERENCE.md", 786, 1, "UNIX", "a refusal names the path, the mode and the owner"),
    ("docs/REFERENCE.md", 4034, 1, "UNIX", "each message names path, mode and owner"),
    ("notes/JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md", 143, 1, "UNIX", "a listener's owner is not resolvable without root"),
    ("notes/JUNIPER_2026-07-30_JUNIPER-ECOSYSTEM_CLI-EXPERIMENTATION-P0-PREFLIGHT-EVIDENCE.md", 144, 1, "UNIX", "each pid's cmdline and owner"),
    ("notes/JUNIPER_2026-08-25_JUNIPER-ECOSYSTEM_DUPLICATI-YAMAGUCHI-BACKUP-CERTIFICATION.md", 721, 1, "UNIX", "the dnsmasq owner is a uid collision"),
    (RI, 189, 1, "UNIX", "owner-only mode"),
    (RI, 352, 1, "UNIX", "quotes Duplicati's source: the owner must be the current user or root"),
    (RI, 352, 2, "UNIX", "owner current user or root"),
    (RI, 565, 1, "UNIX", "owner current user or root"),
    (RI, 655, 1, "UNIX", "run as the copy's owner in a 0700 dir"),
    (RI, 735, 1, "UNIX", "owner bits grant write regardless of the group"),
    (SR, 862, 1, "UNIX", "mode 0600, owner pcalnon"),
    (SR, 896, 1, "UNIX", "writable for pcalnon (owner) and under sg duplicati (group)"),
    (SR, 916, 1, "UNIX", "owner is not uid 1000, not in group, no other bits"),
    (SR, 1164, 1, "UNIX", "owner pcalnon:duplicati 0770"),
    (SR, 1185, 1, "UNIX", "chmod 0700/0600 owner pcalnon"),
    (SR, 1268, 1, "UNIX", "quotes Duplicati: the owner must be the current user or root"),
    (SR, 1270, 2, "UNIX", "a root owner is trusted"),
    (SR, 1287, 2, "UNIX", "--for-service sets owner root"),
    (ID, 424, 1, "UNIX", "97 of 118 directories changed owner"),
    (ID, 1349, 1, "UNIX", "a scratch prefix's owner from the host's"),
    (ID, 1736, 1, "UNIX", "the Owner:group column header"),
    (ID, 2296, 1, "UNIX", "the env file's owner and mode"),
    (ID, 2311, 1, "UNIX", "the env file's owner and mode"),
    (ID, 2728, 1, "UNIX", "as the copy's owner, in a 0700 directory"),
    (ID, 2850, 1, "UNIX", "directories to change owner"),
    (R2, 525, 1, "UNIX", "directories changed owner"),
    (R2, 949, 1, "UNIX", "owner in {current uid, root}"),
    (R2, 2632, 1, "UNIX", "a directory's owner can always delete"),
    (SA, 275, 1, "UNIX", "directories to change owner"),
    (SA, 489, 1, "UNIX", "the re-own changed every volume's owner"),
    (SA, 643, 1, "UNIX", "name, size, mode and owner"),
    (SA, 803, 1, "UNIX", "the env file's owner and mode"),
    (PB, 615, 1, "UNIX", "quotes Duplicati's message: owner is uid"),
    (PB, 1148, 1, "UNIX", "no owner or parent-directory check"),
    (PB, 1151, 1, "UNIX", "only the file's owner can write it"),
    (PB, 1158, 1, "UNIX", "the refusal text: mode NNNN, owner pcalnon (uid 1000)"),
    (PB, 4840, 1, "UNIX", "the file must be owner root, group duplicati"),
    (PB, 4930, 1, "UNIX", "the env file's owner and mode"),
    (PB, 5164, 1, "UNIX", "env-file owner and mode"),
    (PB, 5462, 1, "UNIX", "the installer checks owner, group and mode"),
    (CP, 479, 1, "UNIX", "an owner-only 0600 path"),
    (CP, 492, 1, "UNIX", "an owner-only 0700 directory"),
    (CS, 201, 2, "UNIX", "the Homebrew prefix is writable by the owner and by admin"),
    (CS, 336, 1, "UNIX", "a 0600 file: git reads it as the file's owner"),
    ("tests/test_duplicati_installer_real_path.py", 23, 1, "UNIX", "their real owner is the test user"),
    ("tests/test_duplicati_web_credential.py", 22, 1, "UNIX", "every message names path, mode and owner"),
    ("tests/test_phase_d_finish.py", 1111, 1, "UNIX", "cp -p keeps mode, owner and group"),
    ("tests/test_yamaguchi_acceptance_probe.py", 1085, 1, "UNIX", "a path, a mode, an owner"),
    ("util/ad-hoc/2026-09-21_lint_design_snippets.py", 179, 1, "UNIX", "chmod 0o700: owner-only"),
    ("util/ad-hoc/2026-09-22_apply_round2_corrections.py", 55, 1, "UNIX", "directories changed owner (design text)"),
    ("util/ad-hoc/2026-09-22_apply_round2_corrections.py", 586, 1, "UNIX", "directories to change owner (design text)"),
    ("util/ad-hoc/2026-09-22_reconcile_backup_design.py", 784, 1, "UNIX", "mode 0600, owner duplicati:duplicati"),
    ("util/ad-hoc/2026-09-22_reconcile_backup_design.py", 1427, 1, "UNIX", "as the copy's owner, in a 0700 directory"),
    (CSB, 177, 1, "UNIX", "directories to change owner (design text)"),
    (CSB, 479, 1, "UNIX", "the env file's owner and mode (design text)"),
    (CSB, 494, 1, "UNIX", "the env file's owner and mode (design text)"),
    (CSB, 863, 1, "UNIX", "directories to change owner (design text)"),
    (CSB, 864, 1, "UNIX", "directories to change owner (design text)"),
    ("util/ad-hoc/2026-10-04_gitleaks_zero_rule_probe.py", 138, 1, "UNIX", "a report path only its owner can read"),
    ("util/ad-hoc/2026-10-29_write_matched_settings_key.py", 53, 1, "UNIX", "mode 0600, owner the effective user"),
    ("util/ad-hoc/2026-11-11_phase_d_tools_mutation_check.py", 232, 1, "UNIX", "the directory's owner is not checked"),
    ("util/ad-hoc/2026-11-23_backup_slowdown_evidence.py", 18, 1, "UNIX", "volume classes (type, mode, owner)"),
    ("util/ad-hoc/duplicati_secret_check.py", 119, 1, "UNIX", "a printed message: need owner or root to read /proc/<pid>/environ"),
    ("util/ad-hoc/duplicati_verify_passphrase.bash", 17, 1, "UNIX", "a mktemp file is owner-only"),
    (YAP, 53, 1, "UNIX", "(kind, mode, owner) classes"),
    (YAP, 69, 1, "UNIX", "the dlist's mode and owner"),
    (YAP, 526, 1, "UNIX", "size, mtime, mode, owner"),
    (YAP, 570, 1, "UNIX", "a printed finding: mode ... owner ..."),
    (YAP, 570, 3, "UNIX", "a printed finding: the lane writes 0600, owner ..."),
    (YAP, 626, 1, "UNIX", "destination files (name, mtime, owner)"),
    (YAP, 1118, 1, "UNIX", "a path, a mode, an owner"),
    (YSA, 46, 1, "UNIX", "refused, naming the path, mode and owner"),
    (YSA, 128, 1, "UNIX", "the mode and the owner"),
    (YSA, 171, 1, "UNIX", "a raised message: (mode ..., owner ...)"),
    (YSA, 173, 1, "UNIX", "a raised message: mode ..., owner ..."),
    ("util/ad-hoc/yamaguchi_server_db_snapshot.py", 173, 1, "UNIX", "a printed line: mode 0600, owner ..."),
    ("util/claude_agent_guard.py", 361, 1, "UNIX", "Homebrew's prefix is owner-writable"),
    ("util/configure_commit_signing.py", 1266, 1, "UNIX", "owner-only file mode"),
    ("util/configure_commit_signing.py", 1266, 2, "UNIX", "git reads it as the file's owner"),
    ("util/install_duplicati_service.bash", 228, 1, "UNIX", "a scratch prefix's owner from the host's"),
    # --- GITHUB: a repository's owner account, a trusted-publisher field ---
    ("docs/REFERENCE.md", 5222, 1, "GITHUB", "the owner is --owner (default pcalnon)"),
    ("docs/REFERENCE.md", 8944, 1, "GITHUB", "a personal-account owner, not an org"),
    ("docs/REFERENCE.md", 8968, 1, "GITHUB", "a personal-account owner"),
    ("docs/REFERENCE.md", 9930, 1, "GITHUB", "trusted publisher: workflow file, environment, owner, repository"),
    ("notes/JUNIPER_2026-05-10_JUNIPER-ECOSYSTEM_ANTHROPIC-API-KEY-ACCESS-VALIDATION-WALKTHROUGH.md", 45, 1, "GITHUB", "the owner is a personal account, not an org"),
    ("notes/JUNIPER_2026-06-09_JUNIPER-ECOSYSTEM_PACKAGE-PLACEMENT-AND-RELOCATION-PLAN.md", 270, 1, "GITHUB", "trusted publisher (owner, repo, workflow, environment)"),
    ("notes/JUNIPER_2026-06-09_JUNIPER-ECOSYSTEM_PACKAGE-PLACEMENT-AND-RELOCATION-PLAN.md", 296, 1, "GITHUB", "trusted publisher (owner, repository, workflow, environment)"),
    ("notes/JUNIPER_2026-08-16_JUNIPER-ML_MERGE-QUEUE-ENABLEMENT-RUNBOOK.md", 322, 1, "GITHUB", "code coupled to the owner/ prefix of a repository slug"),
    ("notes/JUNIPER_2026-08-16_JUNIPER-ML_MERGE-QUEUE-ENABLEMENT-RUNBOOK.md", 331, 1, "GITHUB", "bare repository names with no owner prefix"),
    (CQ, 4, 1, "GITHUB", "all 9 repos, owner pcalnon"),
    (CQ, 35, 1, "GITHUB", "the 9 owner-pcalnon repos"),
    (SP, 35, 1, "GITHUB", "the 9 owner (pcalnon) repositories"),
    (H5U, 71, 1, "GITHUB", "an upstream repository's known owner"),
    (H5U, 231, 1, "GITHUB", "an upstream repository's owner: a personal account"),
    (H5U, 614, 1, "GITHUB", "an upstream repository's owner"),
    (H5U, 614, 2, "GITHUB", "the owner is an organization"),
    ("notes/templates/ci/README.md", 18, 1, "GITHUB", "owner pcalnon is a personal account"),
    ("tests/test_release_train_ceremony.py", 402, 1, "GITHUB", "owner-qualified repository names"),
    ("util/ad-hoc/2026-09-24_round42_probes/register-fixforward2-round1-laneA/a20_pr_dates.py", 4, 1, "GITHUB", "a repository named without its owner"),
    ("util/ad-hoc/2026-09-24_round42_probes/register-fixforward2-round1-laneA/a20_pr_dates.py", 4, 2, "GITHUB", "owner pcalnon"),
    ("util/ad-hoc/2026-11-07_flood4_ml_docs_fixes.py", 170, 1, "GITHUB", "no repository of that name under that owner"),
    # --- CODE: GraphQL arguments, identifiers, keys, regex alternatives ---
    ("util/safe_merge.py", 599, 1, "CODE", "GraphQL repository(owner: ...): the unresolved-thread probe failed open"),
    ("util/ad-hoc/2026-08-26_requirements_cross_view_diff.py", 53, 1, "CODE", "regex alternative for the **Owner**: field"),
    (PSM, 50, 2, "CODE", "a code snippet: {\"owner\": owner, ...}"),
    (PSM, 58, 2, "CODE", "a code snippet: {\"owner\": owner, ...}"),
    (PSM, 70, 1, "CODE", "a code snippet: pr_state(owner, repo, pr)"),
    ("util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/round2-laneA/r2a_spans.py", 50, 1, "CODE", "GraphQL repository(owner: ...)"),
    ("util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/round2-laneA/r2a_spans.py", 65, 1, "CODE", "GraphQL repository(owner: ...)"),
    ("util/ad-hoc/2026-09-22_laneA2_cdp_store_apply_check.py", 416, 1, "CODE", "a JavaScript variable"),
    ("util/ad-hoc/2026-09-22_laneA2_cdp_store_apply_check.py", 417, 1, "CODE", "a JavaScript variable"),
    ("util/ad-hoc/2026-09-22_laneA2_cdp_store_apply_check.py", 510, 1, "CODE", "a JavaScript object key"),
    ("util/ad-hoc/2026-09-23_converge_pr_through_moving_main.py", 38, 1, "CODE", "GraphQL repository(owner: ...)"),
    (L2F, 6, 1, "CODE", "GraphQL repository(owner: ...)"),
    (L2F, 12, 1, "CODE", "GraphQL repository(owner: ...)"),
    (L2F, 16, 1, "CODE", "GraphQL repository(owner: ...)"),
    (L2F, 20, 1, "CODE", "GraphQL repository(owner: ...)"),
    (L4F, 44, 1, "CODE", "GraphQL repository(owner: ...)"),
    (L4F, 49, 1, "CODE", "GraphQL repository(owner: ...)"),
    (L4F, 52, 1, "CODE", "GraphQL repository(owner: ...)"),
    (L4F, 59, 1, "CODE", "GraphQL repository(owner: ...)"),
    ("util/ad-hoc/2026-10-08_fleet_flood3_census.py", 46, 1, "CODE", "GraphQL repository(owner: ...)"),
    ("util/ad-hoc/2026-10-08_fleet_flood3_pr_actions.py", 58, 1, "CODE", "GraphQL repository(owner: ...)"),
    ("util/ad-hoc/2026-11-07_flood4_val_gh_heads.py", 28, 1, "CODE", "GraphQL repository(owner: ...)"),
    ("util/ad-hoc/2026-11-08_flood4r2_val_canopy-docs_step_e2e.py", 62, 1, "CODE", "GraphQL repository(owner: ...)"),
    ("util/ad-hoc/2026-11-11_flood4r2_val_r17-canopy-lockfile_real_gh_probe.py", 32, 1, "CODE", "GraphQL repository(owner: ...)"),
    ("util/ad-hoc/retired/2026-08-14_signing_arc_status_RETIRED-2026-08-14.py", 67, 1, "CODE", "GraphQL repository(owner: ...)"),
    (CQ, 586, 1, "CODE", "a quoted gh api graphql command: repository(owner: ...)"),
    (SP, 839, 2, "CODE", "a quoted GraphQL query: repository(owner: $owner, ...)"),
    (PRG, 554, 1, "CODE", "a quoted gh api graphql command: repository(owner: ...)"),
    (PRG, 707, 1, "CODE", "a quoted gh api graphql command: repository(owner: ...)"),
    (PRG, 769, 1, "CODE", "a quoted gh api graphql command: repository(owner: ...)"),
    ("notes/JUNIPER_2026-09-22_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-DESIGN.md", 142, 1, "CODE", "a code span: find_open_pr(owner, repo, branch)"),
    ("notes/JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-CONSENSUS-ROUND-1-RECORD.md", 747, 1, "CODE", "a code span: find_open_pr(owner, repo, args.branch)"),
    (ID, 1070, 1, "CODE", "a shell code block: local folder=\"$1\" owner (its uses read $owner)"),
    # --- FIELD: a field naming the owning repository, team or requirement area ---
    ("docs/REFERENCE.md", 8165, 1, "FIELD", "the (owner, category) bucket key"),
    ("docs/REFERENCE.md", 8182, 1, "FIELD", "the requirements owner field"),
    ("docs/REFERENCE.md", 8193, 1, "FIELD", "a new area code or owner"),
    ("docs/REFERENCE.md", 8193, 2, "FIELD", "the 9 owner shortcodes"),
    (RIP, 456, 1, "FIELD", "(owner, category, brief) bucketing"),
    (RIP, 465, 1, "FIELD", "(owner, category) buckets"),
    (RIP, 474, 1, "FIELD", "the rec owner block"),
    ("notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md", 1337, 1, "FIELD", "the requirements owner enum"),
    ("notes/JUNIPER_2026-07-29_JUNIPER-ECOSYSTEM_CASCOR-RECURRENCE-CLI-TEST-VALIDATION-EXPERIMENTATION-PLAN.md", 1339, 1, "FIELD", "the requirements owner enum"),
    ("notes/JUNIPER_2026-08-08_JUNIPER-RECURRENCE_JR-REC-REQUIREMENTS-BLOCK-PROPOSAL.md", 4, 1, "FIELD", "the juniper-recurrence owner block"),
    ("notes/JUNIPER_2026-08-08_JUNIPER-RECURRENCE_JR-REC-REQUIREMENTS-BLOCK-PROPOSAL.md", 15, 1, "FIELD", "the owner-repo enum"),
    ("notes/JUNIPER_2026-09-23_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-GROUNDING-INVENTORIES-RECORD.md", 800, 1, "FIELD", "a template header field: Owner"),
    ("notes/JUNIPER_2026-06-28_JUNIPER-ML_CI-TOOLS-ENV-DRIFT-CHECK-PROMPT-ANALYSIS.md", 83, 1, "FIELD", "owner: juniper-recurrence"),
    ("notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md", 101, 1, "FIELD", "Owner is the repo that must change"),
    ("notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md", 332, 1, "FIELD", "the owner repo of a work item"),
]
DECISIONS += [(CDP, n, 1, "FIELD", "Owner: names the owning repository") for n in (141, 145, 153, 158, 166, 171, 175, 184, 186, 199)]
DECISIONS += [(TSA, n, 1, "FIELD", "Owner: names the owning repository") for n in (577, 580, 589, 593)]
DECISIONS += [(CAP, n, 1, "FIELD", "Owner: names the owning repository") for n in (153, 171, 180)]
DECISIONS += [(TSP, n, 1, "FIELD", "Owner: names the owning repository") for n in (170, 177, 179, 186, 188, 196, 199, 208)]
DECISIONS += [(CAE, n, 1, "FIELD", "Owner repo / Owner: names the owning repository") for n in (148, 228, 262, 297, 326, 369, 394, 426, 456, 487, 526, 546, 574, 596, 600, 604, 609, 614, 622, 627, 630, 631, 633, 661)]
DECISIONS += [(PMT, n, 1, "FIELD", "Owner repo: names the owning repository") for n in (41, 64, 99, 126, 158, 184, 209, 229, 245, 266, 282, 309, 336)]
DECISIONS += [(GEN, n, 1, "FIELD", "the owner repo of a work unit") for n in (204, 231, 425, 452)]
DECISIONS += [
    # --- ROLE: a generic role, not the person ---
    ("notes/JUNIPER_2026-04-29_JUNIPER-ECOSYSTEM_CI-VALIDATION-FINDINGS.md", 248, 1, "ROLE", "the canopy product owner"),
    ("notes/JUNIPER_2026-04-29_JUNIPER-ECOSYSTEM_CI-VALIDATION-FINDINGS.md", 262, 1, "ROLE", "the canopy product owner"),
    ("notes/JUNIPER_2026-05-02_JUNIPER-CASCOR_V38-GROW-NETWORK-INVESTIGATION-PLAN.md", 590, 1, "ROLE", "the cascade-correlation component's owner"),
    ("notes/JUNIPER_2026-05-07_JUNIPER-ECOSYSTEM_ASYNC-ROUTE-AUDIT-HOOK-MIGRATION-PLAN.md", 140, 1, "ROLE", "each repo's owner"),
    ("notes/JUNIPER_2026-05-07_JUNIPER-ECOSYSTEM_ASYNC-ROUTE-AUDIT-HOOK-MIGRATION-PLAN.md", 185, 1, "ROLE", "per repo, owner-scoped"),
    (RIP, 229, 1, "ROLE", "an explicit owner and ETA"),
    ("notes/JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md", 444, 1, "ROLE", "the owner workstream column"),
    ("notes/JUNIPER_2026-06-17_JUNIPER-ML_MODEL-CORE-CROSSVAL-BUILD-ROADMAP.md", 150, 1, "ROLE", "the owner phase column"),
    ("notes/JUNIPER_2026-06-19_JUNIPER-CASCOR_WS6-BPHASE-MODEL-CORE-ADOPTION-BUILD-PLAN.md", 67, 1, "ROLE", "owner boundaries between workstreams"),
    ("notes/JUNIPER_2026-06-21_JUNIPER-ECOSYSTEM_DOCS-REALITY-AUDIT.md", 89, 1, "ROLE", "the Owner / next column"),
    ("notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-PLAN-COVERAGE-AUDIT.md", 346, 1, "ROLE", "no phase owner"),
    ("notes/JUNIPER_2026-08-08_JUNIPER-CANOPY_E2E-CLICK-BY-CLICK-TEST-MATRIX.md", 159, 1, "ROLE", "the browser-side owner of a WebSocket route"),
    (E2E, 1008, 1, "ROLE", "the measurement narrows the owner (the component at fault)"),
    (E2E, 1039, 1, "ROLE", "narrowed the owner (the component at fault)"),
    (E2E, 6962, 1, "ROLE", "the REST poll was the un-demoted owner of the store"),
    (E2E, 13196, 1, "ROLE", "the gated click-through had no owner (no matrix item drives it)"),
    (E2E, 13201, 1, "ROLE", "--expected-head's owner"),
    ("util/ad-hoc/2026-10-21_phase15_ledger_round2_corrections.py", 247, 1, "ROLE", "the gated click-through had no owner (ledger text)"),
    ("util/ad-hoc/2026-10-21_phase15_ledger_round2_corrections.py", 252, 1, "ROLE", "--expected-head's owner (ledger text)"),
    ("notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md", 3391, 1, "ROLE", "REST: a parent that is a filter rather than an owner"),
    ("notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md", 4882, 1, "ROLE", "an owner segment in a code namespace"),
    ("notes/JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-A-SKILLS-PROGRESSIVE-DISCLOSURE.md", 304, 1, "ROLE", "a different owner surface"),
    ("notes/JUNIPER_2026-08-18_JUNIPER-ML_MEMORY-PROPOSAL-B-PATH-SCOPED-LOCALITY.md", 1204, 1, "ROLE", "a work item with its own owner"),
    ("notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md", 117, 1, "ROLE", "P3.3, the rotation owner"),
    ("notes/JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md", 654, 2, "ROLE", "a step needs an owner and a slot"),
    ("notes/JUNIPER_2026-09-02_JUNIPER-ML_SOAK-SESSION-ROLE-AUTOMATION-ANALYSIS.md", 41, 1, "ROLE", "a gap with no owner at all"),
    ("notes/JUNIPER_2026-09-22_JUNIPER-ML_DYNAMIC-WORKFLOW-HARNESS-DESIGN.md", 479, 1, "ROLE", "V3's owner"),
    (R2, 1606, 1, "ROLE", "a code change with no PR, no step and no owner"),
    ("notes/JUNIPER_2026-10-03_JUNIPER-RECURRENCE_EQUITIES-END-TO-END-AUDIT-AND-DEVELOPMENT-PLAN.md", 279, 1, "ROLE", "juniper-deploy named as an owner"),
    ("notes/JUNIPER_2026-10-25_JUNIPER-ML_TURING-H6-VSCODE-MCP-SERVERS-AUDIT.md", 245, 1, "ROLE", "H4's owner"),
    ("notes/development/JUNIPER_2026-04-20_JUNIPER-ECOSYSTEM_R5-01-CANONICAL-DEVELOPMENT-PLAN.md", 1736, 1, "ROLE", "CODEOWNERS: no owner review blocks the PR"),
    ("prompts/generated/JUNIPER_ECOSYSTEM_TEST-SUITE-AUDIT_PLAN_2026-06-26_1548.md", 228, 1, "ROLE", "a recommended owner for each issue"),
    # --- GPG, TECH ---
    ("notes/JUNIPER_2026-08-03_JUNIPER-ECOSYSTEM_YUBIKEY-GPG-ED448-KEYTOCARD-PROCEDURE.md", 285, 1, "GPG", "gpg owner trust (--edit-key ... trust)"),
    ("util/release_train/ceremony.py", 981, 1, "TECH", "the per-repo latest badge's owner"),
    # --- found after the first apply: the regression run (the test needle) and the backup lane's review, then a
    #     manual pass over every code-adjacent string and the "its/their owner <verb>" shape classify keeps ---
    ("tests/test_yamaguchi_acceptance_probe.py", 580, 3, "CODE", "the test's needle for the probe's finding text: owner root"),
    ("tests/test_juniper_clone.py", 287, 1, "CODE", "a subtest label for the --owner flag"),
    ("tests/test_juniper_clone.py", 293, 1, "CODE", "a subtest label for the --owner flag"),
    ("tests/test_juniper_repo_ssh_setup.py", 723, 1, "CODE", "a subtest label for the --owner flag"),
    ("tests/test_juniper_repo_ssh_setup.py", 733, 1, "CODE", "a subtest label for the --owner flag"),
    ("util/ad-hoc/2026-09-24_round42_probes/handoff-consolidated-round4-laneF/archiver_probe.py", 29, 1, "CODE", "a key matched against LOWERCASED text: Overtoad-email could never match"),
    ("util/ad-hoc/2026-09-24_archive_round42_reports.py", 224, 1, "CODE", "the owner-email label the probe matches"),
    ("util/ad-hoc/2026-11-11_phase_d_tools_mutation_check.py", 193, 1, "UNIX", "the run root's owner is not checked (a mutant label)"),
    ("util/ad-hoc/2026-11-11_phase_d_tools_mutation_check.py", 207, 1, "UNIX", "shred: the owner is not checked (a mutant label)"),
    ("util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py", 48, 1, "ROLE", "owner-drop shapes: a pin whose owning package is lost"),
    ("util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py", 113, 1, "ROLE", "its owner (the package a pin is attributed to) is a guess"),
    ("util/ad-hoc/2026-09-22_ci_tools_pin_census_remote.py", 964, 1, "ROLE", "its owner (the package a pin is attributed to) is a guess"),
    ("util/ad-hoc/2026-09-07_f035_renderer_dispatch_probe.py", 224, 1, "ROLE", "four outcomes, each with a different owner (responsible party)"),
    ("util/ad-hoc/2026-11-09_flood4r2_n1-r3_apply_edits.py", 147, 1, "TECH", "the stale fit is still the owner (of the race) when it settles"),
    ("util/ad-hoc/2026-11-09_flood4r2_n1-r3_apply_edits.py", 154, 1, "TECH", "the stale fit is still the owner (of the race) when it settles"),
    ("util/ad-hoc/2026-11-09_flood4r2_val_n1-r2-claims_findings.py", 36, 1, "TECH", "the old fit is still the owner (of the race) when it settles"),
    ("util/ad-hoc/2026-11-09_flood4r2_val_n1-r2-claims_findings.py", 36, 2, "TECH", "the old fit is still the owner (of the race) when it settles"),
]
# Every renamed token in these April 2026 proposals is a team role ("Owner-class: backend-cascor", "kill switch owner =
# security lead", a CODEOWNERS owner review); none is the person (reviewed row by row, 72 tokens).
WHOLE_DIRECTORY_ROLE = ("notes/interface_proposals/",)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.strip().split("\n")[0])
    ap.add_argument("--candidates", required=True, help="the TSV of 2026-11-24_technical_owner_candidates.py")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    rows = {}
    with open(args.candidates, encoding="utf-8") as handle:
        for raw in handle:
            row = raw.rstrip("\n").split("\t")  # status, where, occurrence, orig, got, nets, kind, window
            rows[(row[1], int(row[2]))] = (row[3], row[4], row[6], row[7])
    chosen: dict[tuple[str, int], tuple[str, str]] = {}
    for path, line, occurrence, category, reason in DECISIONS:
        key = (f"{path}:{line}", occurrence)
        if key not in rows:
            raise SystemExit(f"NOT A RENAMED TOKEN: {key[0]} occurrence {occurrence}")
        if key in chosen:
            raise SystemExit(f"DUPLICATE DECISION: {key[0]} occurrence {occurrence}")
        chosen[key] = (category, reason)
    for (where, occurrence) in rows:
        if where.startswith(WHOLE_DIRECTORY_ROLE) and (where, occurrence) not in chosen:
            chosen[(where, occurrence)] = ("ROLE", "a team role in the April 2026 proposals")
    out = ["path\tline\toccurrence\tbase\thead\tcategory\treason\tkind\twindow"]
    for (where, occurrence), (category, reason) in sorted(chosen.items(), key=lambda kv: (kv[0][0].rsplit(":", 1)[0], int(kv[0][0].rsplit(":", 1)[1]), kv[0][1])):
        orig, got, kind, window = rows[(where, occurrence)]
        path, line = where.rsplit(":", 1)
        out.append("\t".join((path, line, str(occurrence), orig, got, category, reason, kind, window)))
    with open(args.out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(out) + "\n")
    counts: dict[str, int] = {}
    for category, _ in chosen.values():
        counts[category] = counts.get(category, 0) + 1
    files = {where.rsplit(":", 1)[0] for where, _ in chosen}
    print(f"{len(chosen)} token(s) in {len(files)} file(s): " + " ".join(f"{k}={v}" for k, v in sorted(counts.items())) + f" -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
