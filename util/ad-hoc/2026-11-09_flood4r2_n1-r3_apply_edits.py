"""
Apply the round-2 validators' findings to fix N-1's carrier tree and its PR texts (round 3), exactly once each.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (builder session, flood-4 round 2, fix N-1 round 3)
Created: 2026-11-09
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md §8 ruling 11 (juniper-cascor's paused-fit wedge);
         tmp/flood4r2-val/n1-r2-code-lens/findings.json and tmp/flood4r2-val/n1-r2-claims-lens/findings.json (this worktree)

Usage: python3 <this> [--dry-run]

Each edit is (target, finding, old, new). A target is a path in the N-1 worktree, or ``@r3/<name>``
for a PR text in the worktree's tmp/flood4-fix/n1-r3/ (copied from n1-r2/ on first use). ``old``
must occur exactly once and ``new`` not at all, or the edit must already be applied (``old``
absent, ``new`` present exactly once), in which case it is skipped: the script is idempotent.
Any other state is an error and nothing is written. Writes n1-r3/apply_edits.json (per edit:
finding, target, result; per file: sha256 before and after).
"""

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

JUNIPER = Path.home() / "Development" / "python" / "Juniper"
TREE = JUNIPER / "worktrees" / "juniper-cascor--fix--paused-fit-wedge--20261108-1815--f3dfee8c"
R2 = TREE / "tmp" / "flood4-fix" / "n1-r2"
R3 = TREE / "tmp" / "flood4-fix" / "n1-r3"
R3_TEXTS = ("pr_body.txt", "commit_body.txt", "pr_title.txt")

TEST_MODULE = "src/tests/unit/api/test_lifecycle_paused_fit_return.py"
FSM_TESTS = "src/tests/unit/api/test_lifecycle_state_machine.py"
REPRO = "util/ad-hoc/2026-11-08_stop_then_start_race_repro.py"
MUTATION_CHECK = "util/ad-hoc/2026-11-08_paused_fit_wedge_mutation_check.py"
CHANGELOG = "CHANGELOG.md"
SCHEMAS = "docs/api/API_SCHEMAS.md"

RULING_17 = 'the owner\'s ruling 17 (2026-11-09, recorded in the record-update PR), "cascor: stop-then-start"'

FSM_LOCK_TEST = '''        assert resumed == [True]
        assert completed == [True]
        assert sm.is_completed()

    @pytest.mark.parametrize(
        "call",
        [
            pytest.param(lambda sm: sm.handle_command(Command.PAUSE), id="handle_command"),
            pytest.param(lambda sm: sm.set_phase(TrainingPhase.CANDIDATE), id="set_phase"),
            pytest.param(lambda sm: sm.save_candidate_state({"epoch": 1}), id="save_candidate_state"),
            pytest.param(lambda sm: sm.get_candidate_state(), id="get_candidate_state"),
            pytest.param(lambda sm: sm.mark_completed(), id="mark_completed"),
            pytest.param(lambda sm: sm.mark_failed("x"), id="mark_failed"),
            pytest.param(lambda sm: sm.mark_resume_ready(), id="mark_resume_ready"),
            pytest.param(lambda sm: sm.mark_investigating(), id="mark_investigating"),
            pytest.param(lambda sm: sm.mark_replaying(), id="mark_replaying"),
            pytest.param(lambda sm: sm.get_state_summary(), id="get_state_summary"),
        ],
    )
    def test_every_transition_and_multi_field_read_waits_for_the_lock(self, call):
        """Every ``@_atomic`` method waits while another thread holds the machine's lock.

        ``mark_failed`` matters as much as ``mark_completed``: a fit that raises while its run is
        paused settles through it, and a resume held between its PAUSED check and its STARTED write
        would otherwise strand the run STARTED with no training thread behind it.
        """
        sm = TrainingStateMachine()
        sm.handle_command(Command.START)
        finished = threading.Event()
        worker = threading.Thread(target=lambda: (call(sm), finished.set()), daemon=True)
        with sm._lock:
            worker.start()
            assert not finished.wait(timeout=0.2), "ran while another thread held the machine's lock"
        assert finished.wait(timeout=5.0)
        worker.join(timeout=5.0)

    def test_reset_clears_candidate_state(self):
'''

EDITS = [
    # --- code lens F1 (BLOCKER): api.lifecycle.manager imported both ways -------------------------------
    (TEST_MODULE, "code-F1",
     "import api.lifecycle.manager as manager_module\nfrom api.app import create_app\nfrom api.lifecycle.manager import TrainingInterrupted, TrainingLifecycleManager\n",
     "from api.app import create_app\nfrom api.lifecycle import manager as manager_module\nfrom api.lifecycle.manager import TrainingInterrupted, TrainingLifecycleManager\n"),
    (REPRO, "code-F1",
     "    import api.lifecycle.manager as manager_module\n    from api.lifecycle.manager import TrainingLifecycleManager\n",
     "    from api.lifecycle import manager as manager_module\n    from api.lifecycle.manager import TrainingLifecycleManager\n"),
    # --- code lens F2 (MAJOR) / F3 (MINOR): every lock pinned by one parametrized test --------------------
    (FSM_TESTS, "code-F2",
     "        assert resumed == [True]\n        assert completed == [True]\n        assert sm.is_completed()\n\n    def test_reset_clears_candidate_state(self):\n",
     FSM_LOCK_TEST),
    # ... and the mutation check removes the lock from each of the ten methods that take it.
    (MUTATION_CHECK, "code-F2",
     "Status: ad-hoc — investigation (verifies src/tests/unit/api/test_lifecycle_paused_fit_return.py\n        and the mark_completed tests in src/tests/unit/api/test_lifecycle_state_machine.py)\n",
     "Status: ad-hoc — investigation (verifies src/tests/unit/api/test_lifecycle_paused_fit_return.py\n        and the mark_completed and lock tests in src/tests/unit/api/test_lifecycle_state_machine.py)\n"),
    (MUTATION_CHECK, "code-F2",
     "- the state machine makes each transition under its own lock, so a resume whose transition\n  straddles the settle's cannot write STARTED over COMPLETED (M21-M23).\n",
     "- the state machine makes each transition, and each read of more than one field, under its own\n  lock, so a resume whose transition straddles the settle's cannot write STARTED over COMPLETED,\n  and a fit that fails while paused cannot be settled inside another thread's transition (M21\n  removes the lock altogether; M22-M31 each remove it from one of the ten methods that take it).\n"),
    (MUTATION_CHECK, "code-F2",
     '_NO_LOCK = \'        self._lock = __import__("contextlib").nullcontext()\\n\'\n',
     '_NO_LOCK = \'        self._lock = __import__("contextlib").nullcontext()\\n\'\n'
     "# Every method that holds the machine's lock (``@_atomic``), in the order M22-M31 unlock them.\n"
     '_LOCKED_METHODS = ("handle_command", "mark_completed", "set_phase", "save_candidate_state", "get_candidate_state", "mark_failed", "mark_resume_ready", "mark_investigating", "mark_replaying", "get_state_summary")\n'),
    (MUTATION_CHECK, "code-F2",
     '    return (MANAGER, old, new)\n\n\n# (name, [(file, old, new), ...])',
     '    return (MANAGER, old, new)\n\n\n'
     'def _unlocked(method: str) -> tuple:\n'
     '    """Remove ``@_atomic`` from one state-machine method, so it runs without the machine\'s lock."""\n'
     '    return (STATE_MACHINE, f"    @_atomic\\n    def {method}(", f"    def {method}(")\n\n\n'
     '# (name, [(file, old, new), ...])'),
    (MUTATION_CHECK, "code-F2",
     '    ("the state machine takes no lock", [(STATE_MACHINE, _FSM_LOCK, _NO_LOCK)]),\n'
     '    ("handle_command is not atomic", [(STATE_MACHINE, "    @_atomic\\n    def handle_command(", "    def handle_command(")]),\n'
     '    ("mark_completed is not atomic", [(STATE_MACHINE, "    @_atomic\\n    def mark_completed(", "    def mark_completed(")]),\n]\n',
     '    ("the state machine takes no lock", [(STATE_MACHINE, _FSM_LOCK, _NO_LOCK)]),\n'
     '    *[(f"{method} is not atomic", [_unlocked(method)]) for method in _LOCKED_METHODS],\n]\n'),
    # --- code lens F4 (MINOR): the same STOPPED / Completed pair without a start ------------------------
    (SCHEMAS, "code-F4",
     "and `training_state.status` becomes `Completed` beside `state_machine.status` `STOPPED`. It is to be fixed in a separate change.\n",
     "and `training_state.status` becomes `Completed` beside `state_machine.status` `STOPPED`. It is to be fixed in a separate change. "
     "The same pair follows without a `start`: the settle writes `Completed` whatever `mark_completed` answers, so a `stop` that lands after its stop check, "
     "while it computes the final score, leaves `STOPPED` beside `Completed`, keeps that score and counts a successful session, and a `reset` that lands "
     "between `mark_completed` and that write leaves the same pair. Neither is a wedge: the next `start` runs.\n"),
    # --- claims lens F1 (BLOCKER): cascor's race is ruling 17; no ruling chose a design -----------------
    (CHANGELOG, "claims-F1",
     'The owner ruled on 2026-11-09 ("Fix all four now") that it gets its own fix, in a separate PR: a per-run stop signal, or a start that refuses or fences a live fit.',
     f"{RULING_17[0].upper()}{RULING_17[1:]}, gives it its own fix, in its own PR. Candidate fixes, which no ruling chose: a per-run stop signal, or a start that refuses or fences a live fit."),
    (REPRO, "claims-F1+F4",
     'Status: ad-hoc — investigation (evidence for a reported race; the owner ruled on 2026-11-09,\n        "Fix all four now", that it gets its own fix, in a separate PR)\n'
     "Retire when: that PR has merged (a per-run stop signal, or a start that refuses or fences a\n             live fit)\n",
     "Status: ad-hoc — investigation: evidence for a reported race, which gets its own fix in its own\n"
     "        PR by the owner's ruling 17 (2026-11-09, recorded in the record-update PR), \"cascor:\n"
     '        stop-then-start"\n'
     "Retire when: that PR has merged\n"),
    # --- claims lens F2 (MAJOR): service-core's fix merged (juniper-ml#2531) ---------------------------
    (CHANGELOG, "claims-F2",
     "Unlike juniper-service-core, where the new run starts at once and the old fit's return completes it, cascor's queue",
     "Unlike juniper-service-core, where the new run starts at once on its own thread and already owns the lifecycle when the old fit returns, cascor's queue"),
    (REPRO, "claims-F2",
     "Unlike juniper-service-core, where the new run starts on its own thread at once and the old\n"
     "fit's return marks it COMPLETED while it trains, cascor's queue keeps the new run from starting\n"
     "until the old fit returns. The lifecycle-ownership guard therefore does not change this race:\n"
     "the stale fit is still the owner when it settles. ``swap_dataset_live`` has a variant: when its\n"
     "10 s join on the old future times out, it clears ``_stop_event`` before submitting the swapped\n"
     "run, which un-stops the old fit the same way.\n",
     "Unlike juniper-service-core, where the new run starts on its own thread at once and so already\n"
     "owns the lifecycle when the old fit returns (juniper-ml#2531's thread check; the published 0.7.2\n"
     "predates it, and there the old fit's return still marks the new run COMPLETED while it trains),\n"
     "cascor's queue keeps the new run from starting until the old fit returns. The lifecycle-ownership\n"
     "guard therefore does not change this race: the stale fit is still the owner when it settles.\n"
     "``swap_dataset_live`` has a variant: when its 10 s join on the old future times out, it clears\n"
     "``_stop_event`` before submitting the swapped run, which un-stops the old fit the same way.\n"),
    # --- the PR body (round 2's text, copied to n1-r3/) ---------------------------------------------------
    ("@r3/pr_body.txt", "claims-F2",
     "juniper-service-core's fix for the same wedge, built before this one and not merged as of this PR, needed such a check",
     "juniper-service-core's fix for the same wedge, built before this one and merged as juniper-ml#2531 (`7b3b91b7`), needed such a check"),
    ("@r3/pr_body.txt", "claims-F1",
     'The owner ruled on 2026-11-09 ("Fix all four now") that it gets its own fix, in a separate PR. A reproducer is included.',
     f"{RULING_17[0].upper()}{RULING_17[1:]}, gives it its own fix, in its own PR. A reproducer is included."),
    ("@r3/pr_body.txt", "claims-F3",
     ", which lands in juniper-ml separately.",
     ", on juniper-ml `main` since juniper-ml#2530 (`734aab58`)."),
    ("@r3/pr_body.txt", "code-F5",
     "and cascor installs no custom log handler, so the lock cannot join a lock-order cycle",
     "and no handler it reaches (the standard library's, and sentry_sdk's when a DSN is set) calls back into the machine, so the lock cannot join a lock-order cycle"),
    ("@r3/pr_body.txt", "claims-F2",
     "juniper-service-core's fix for the same wedge (unmerged; its `main`, juniper-ml `4bae7520`, has no such guard) checks",
     "juniper-service-core's fix for the same wedge (juniper-ml#2531, `7b3b91b7`) checks"),
    ("@r3/pr_body.txt", "claims-F2",
     "There the new run starts at once on its own thread and the old fit's return completes it.",
     "There the new run starts at once on its own thread, so it already owns the lifecycle when the old fit returns: since juniper-ml#2531 that return settles nothing (juniper-service-core 0.7.2, published before #2531, still completes the new run)."),
    ("@r3/pr_body.txt", "claims-F1",
     'The owner ruled on 2026-11-09 ("Fix all four now") that this race gets its own fix, in a separate PR: a per-run stop signal, or a start that refuses or fences a live fit.',
     f"{RULING_17[0].upper()}{RULING_17[1:]}, gives this race its own fix, in its own PR. Candidate fixes, which no ruling chose: a per-run stop signal, or a start that refuses or fences a live fit."),
    ("@r3/pr_body.txt", "brief",
     "\n🤖 Generated with [Claude Code](https://claude.com/claude-code)\n\nhttps://claude.ai/code/session_016H76AjZYVKxwr19XfGm6kE\n",
     ""),
    # --- the commit body ---------------------------------------------------------------------------------
    ("@r3/commit_body.txt", "claims-F1",
     "this change alike. It needs its own fix, which the owner ruled on 2026-11-09 to\nmake in a separate PR.\n",
     "this change alike. It gets its own fix, in its own PR: the owner's ruling 17\n(2026-11-09, recorded in the record-update PR), \"cascor: stop-then-start\".\n"),
]


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def resolve(target: str) -> Path:
    if target.startswith("@r3/"):
        return R3 / target[4:]
    return TREE / target


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    R3.mkdir(parents=True, exist_ok=True)
    for name in R3_TEXTS:
        if not (R3 / name).exists():
            shutil.copy2(R2 / name, R3 / name)

    texts, before = {}, {}
    for target, _finding, _old, _new in EDITS:
        if target not in texts:
            texts[target] = resolve(target).read_text(encoding="utf-8")
            before[target] = sha256(texts[target])

    results, errors = [], 0
    for target, finding, old, new in EDITS:
        text = texts[target]
        old_count = text.count(old)
        new_count = text.count(new) if new else 0
        if old_count == 1 and (new_count == 0 or not new):
            texts[target] = text.replace(old, new)
            verdict = "applied"
        elif old_count == 0 and new and new_count == 1:
            verdict = "already applied"
        else:
            verdict = f"ERROR: old occurs {old_count} times, new {new_count} times"
            errors += 1
        results.append({"finding": finding, "target": target, "result": verdict, "old_head": old[:90]})
        print(f"{verdict:16s} {finding:12s} {target}  [{old[:70]!r}]")

    if errors:
        print(f"{errors} edit(s) cannot apply; nothing written.")
        return 1
    files = {}
    for target, text in texts.items():
        files[target] = {"sha256_before": before[target], "sha256_after": sha256(text)}
        if not args.dry_run and files[target]["sha256_before"] != files[target]["sha256_after"]:
            resolve(target).write_text(text, encoding="utf-8")
    if not args.dry_run:
        with open(R3 / "apply_edits.json", "w", encoding="utf-8") as fh:
            json.dump({"edits": results, "files": files}, fh, indent=1)
    print(f"{len(results)} edits, {sum(r['result'] == 'applied' for r in results)} applied now; {'dry run, nothing written' if args.dry_run else 'written'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
