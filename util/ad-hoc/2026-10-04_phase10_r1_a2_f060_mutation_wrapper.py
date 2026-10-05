# ---------------------------------------------------------------------------
# ARCHIVED VERBATIM, 2026-10-04: a probe from round 1 of the canopy E2E ledger's Phase 10 validation.
# Source: this session's tmpfs scratchpad, lane10A2.g5NzBN/f060_mutation_wrapper.py
# Written by Lane 10-A2 (evidence and instruments), a review lane (a subagent), not by the orchestrator.
# Project: juniper-ml / Sub-Project: ad-hoc tooling / Author: Paul Calnon
# Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
# Related: notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md, Phase 10;
#   reports/e2e-canopy-2026-09-02/consensus/2026-10-04_validator_reports_phase10_round1.md
# Everything below this block is the lane's file, unmodified.
# ---------------------------------------------------------------------------
"""Run the F-060 instrument UNCHANGED except that canopy's dashboard_manager.py text it reads from the git
object is mutated in memory (the instrument reads canopy from git objects, so a scratch-tree edit cannot
reach it). Usage: python3 f060_mutation_wrapper.py <mutation> [script args...]"""
import importlib.util
import sys

SCRIPT = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/clever-juggling-spring/util/ad-hoc/2026-10-04_phase10_f060_rederive.py"
MUTATIONS = {
    # keep the cap's own sentence: stop at cascor's closing phrase instead of juniper-data's
    "stop_at_cascor_closing": ('for stop in (" To accept it,", " The resulting dataset"):', 'for stop in (" To accept it,", " The resulting dataset is permanently annotated as partial"):'),
    # the control flips: also stop before IncompleteDataError's closing sentence
    "stop_before_either_choice": ('for stop in (" To accept it,", " The resulting dataset"):', 'for stop in (" To accept it,", " The resulting dataset", " Either choice"):'),
    # the prompt never opens
    "never_open_prompt": ("return DATASET_SHORTFALL_REFUSAL_MARKER in text or DATASET_SHORTFALL_REFUSAL_SENTENCE in text", "return False"),
}
name = sys.argv[1]
old, new = MUTATIONS[name]
spec = importlib.util.spec_from_file_location("f060", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
real_git_show = mod.git_show


def mutated_git_show(repo, sha, path):
    text = real_git_show(repo, sha, path)
    if path == "src/frontend/dashboard_manager.py":
        assert text.count(old) == 1, "mutation anchor not found exactly once"
        text = text.replace(old, new)
    return text


mod.git_show = mutated_git_show
sys.argv = [SCRIPT] + sys.argv[2:]
print(f"### MUTATION {name}")
sys.exit(mod.main())
