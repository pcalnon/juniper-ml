#!/usr/bin/env python3
"""Read-only: where does each path the consolidated handoff cites live (origin/main, #2097's branch, #2089's branch, fizzy only, memory)?"""
import subprocess
from pathlib import Path

WT = Path("/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream")
MEM = Path("/home/pcalnon/.claude/projects/-home-pcalnon-Development-python-Juniper-juniper-ml/memory")
R = "reports/2026-09-24_defect-register-round-42/"
P = "prompts/thread-handoff_automated-prompts/"
REFS = {"main": "origin/main", "2097": "origin/docs/handoff-round42-followup-lane", "2089": "origin/chore/round42-probe-provenance-session-2fba4397"}

REPO_PATHS = [
    "notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md",
    "notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md",
    "notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md",
    "tests/test_service_fork_drift.py",
    "docs/REFERENCE.md",
    "util/ad-hoc/register_status_crosscheck.py",
    "util/ad-hoc/register_open_set.py",
    "util/ad-hoc/2026-09-24_register_round42_second_fixforward_round2.py",
    "util/ad-hoc/2026-09-24_register_primer_citation_census.py",
    "util/ad-hoc/2026-08-13_run_primer_examples.py",
    "util/ad-hoc/2026-09-24_primer_toy_pin_mutation_check.py",
    "util/ad-hoc/2026-09-24_archive_round42_reports.py",
    "util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py",
    "util/ad-hoc/2026-09-24_verify_data_0_16_0_notes_match_tag.py",
    "util/ad-hoc/2026-09-24_round42_probes/README.md",
    "util/ad-hoc/2026-09-24_serve_scratch_juniper_data.bash",
    "util/ad-hoc/2026-09-24_open_round42_consolidated_handoff_pr.py",
    "util/ad-hoc/2026-09-24_data438_round2_stall_probe_throughout.py",
    "util/push_signed_commit.py",
    "util/open_signed_pr.py",
    "util/safe_merge.py",
    ".github/workflows/codeql.yml",
    R + "owner-ruling-key-leaks-verbatim.md",
    R + "owner-rulings-verbatim.md",
    R + "pending-items-snapshot-2026-09-24T1110Z.md",
    R + "canopy685-implementation-report.md",
    R + "canopy683-validation.md",
    R + "cascor688-validation.md",
    R + "cascor686-fixup-implementation-report.md",
    R + "cascor690-implementation-report.md",
    R + "cascor690-fixup-implementation-report.md",
    R + "bytes-compare-ml2086-data440-cascor689-validation.md",
    R + "data428-round3-laneA1-security.md",
    R + "data438-round1-laneA-reprobe.md",
    R + "data438-round1-laneB-refute.md",
    R + "data438-fixforward-round1-laneA-reprobe.md",
    R + "data438-fixforward-round1-laneB-refute.md",
    R + "data438-fixforward-round1-fix-report.md",
    R + "data438-fixforward-pr-draft.md",
    R + "register-fixforward2-round2-laneA-reprobe.md",
    R + "register-fixforward2-round2-laneB-refute.md",
    R + "ml2080-round1-laneA-reprobe.md",
    R + "handoff-2fba4397-round2-laneF-reprobe.md",
    R + "handoff-2fba4397-round3-laneF-reprobe.md",
    P + "HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md",
    P + "HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md",
    P + "HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md",
    P + "HANDOFF_2026-09-23_defect-register-round-42-four-prs-armed-by-an-unseen-actor-two-merged-unvalidated.md",
    P + "HANDOFF_2026-09-24_defect-register-round-42-ml2088-merged-data-fixforward-refuted-and-fixing-closes-pr-owed.md",
    P + "HANDOFF_2026-09-24_defect-register-round-42-consolidated-both-lanes-validations-and-closes-pr-owed.md",
]
MEMORY = [
    "feedback_headless_merge_approval_policy.md",
    "feedback_deploy_approvals_paul_manages.md",
    "feedback_semver_beats_consumer_cap_2026-09-05.md",
    "feedback_worktree_cleanup_only_on_explicit_merge_2026-05-15.md",
    "feedback_memory_index_target_is_20kb.md",
    "reference_git_trailer_must_be_last_paragraph.md",
    "reference_typed_escapes_become_real_characters.md",
    "reference_backticks_eaten_in_shell_messages.md",
    "reference_subagents_killed_by_session_limit_resume_with_sendmessage.md",
    "feedback_validate_handoff_prompts_independently.md",
    "reference_a_disarmed_pr_is_rearmed_by_an_unseen_actor_draft_it.md",
    "MEMORY.md",
]


def exists(ref: str, path: str) -> bool:
    r = subprocess.run(["git", "cat-file", "-e", f"{ref}:{path}"], cwd=WT, capture_output=True)
    return r.returncode == 0


for p in REPO_PATHS:
    where = [k for k, ref in REFS.items() if exists(ref, p)]
    local = (WT / p).exists()
    print(f"{','.join(where) or '-':14} fizzy={'y' if local else 'n'}  {p}")
print()
for m in MEMORY:
    print(f"memory {'y' if (MEM / m).exists() else 'MISSING'}  {m}")
