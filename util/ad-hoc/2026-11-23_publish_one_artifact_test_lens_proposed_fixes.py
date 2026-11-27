#!/usr/bin/env python3
"""Apply the TEST-lens review's proposed pins to a SCRATCH copy of cascor's test_publish_one_artifact.py.

Project: juniper-ml
Sub-Project: ad-hoc tooling (publish artifact identity)
Author: Paul Calnon
Created: 2026-11-23
Status: ad-hoc -- one-off (TEST-lens review of the one-artifact template sweep: proof that each proposed pin kills its mutant)
Retire when: RETAINED -- ad-hoc scripts are kept as provenance of record (policy of 2026-08-25)
Related: util/ad-hoc/2026-11-23_publish_one_artifact_test_lens_mutations.py (the mutation run the pins answer);
         tmp/sweep/cascor/juniper-cascor (the frozen clone: never edited)

Why
---
A proposed fix to a test is itself a claim: that it passes on the workflows as they are and fails on the mutant it
targets. This patches a COPY of the test with the proposals, so the mutation run can be repeated against it. The
literal command lists are generated with repr() from the pristine workflows, as a person would copy them.

    python3 -I util/ad-hoc/2026-11-23_publish_one_artifact_test_lens_proposed_fixes.py --test <copy>/src/tests/unit/test_publish_one_artifact.py \
        --pristine <dir holding the three pristine publishers>
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

FILES = ("publish.yml", "publish-cascor-model.yml", "publish-protocol.yml")
INSTALL = "verify-testpypi-install"
SUB_BUILD_STEPS = ("Install build tools", "Build sdist + wheel", "Validate distribution metadata")

NEW_INSTALL_TEST = '''    @pytest.mark.parametrize("workflow", sorted(PUBLISHERS))
    def test_the_install_checks_moved_to_their_job_with_the_commands_they_ran_before(self, workflow):
        # Exactly these commands, in this order, comments and blank lines dropped: no `exit 0`, trap, earlier install or
        # second VERSION can be added, and none dropped, while a comment may change freely.
        step = _step(_workflow(workflow)["jobs"][INSTALL], INSTALL_STEPS[workflow])
        assert [line.strip() for line in step["run"].splitlines() if line.strip() and not line.strip().startswith("#")] == INSTALL_COMMANDS[workflow]


'''

OLD_REPUBLISH = '''        jobs = [_workflow(workflow)["jobs"][REPUBLISH] for workflow in PUBLISHERS]
        assert all(job == jobs[0] for job in jobs)
'''

NEW_REPUBLISH = '''        jobs = [_by_action(_workflow(workflow)["jobs"][REPUBLISH]) for workflow in PUBLISHERS]
        assert all(job == jobs[0] for job in jobs)

    def test_each_action_is_pinned_to_one_ref_in_every_publisher(self):
        # Dependabot bumps an action in all three files at once; a hand edit that bumps one copy fails here, wherever it is.
        refs: dict[str, set[str]] = {}
        for workflow in PUBLISHERS:
            for job in _workflow(workflow)["jobs"].values():
                for step in job.get("steps") or []:
                    if step.get("uses"):
                        name, _, ref = str(step["uses"]).partition("@")
                        refs.setdefault(name, set()).add(ref)
        assert {name: len(found) for name, found in refs.items()} == {name: 1 for name in refs}
'''

HELPER = '''

def _by_action(value):
    """VALUE with every ``uses:`` reduced to the action's name."""
    if isinstance(value, dict):
        return {k: (str(v).split("@", 1)[0] if k == "uses" else _by_action(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_by_action(v) for v in value]
    return value


def _workflow(name: str) -> dict:'''

NEW_CLASS = r'''

class TestReviewAdditions:
    """The TEST-lens review's proposed pins; each kills a mutation the suite let through."""

    @pytest.mark.parametrize("workflow", sorted(PUBLISHERS))
    def test_every_job_and_the_install_step_carry_only_their_listed_keys(self, workflow):
        # An `env` on a job or on the install step (PIP_EXTRA_INDEX_URL, HASH_CHECK_ATTEMPTS), a container, a matrix or a
        # self-hosted runner changes what a check runs, or against what.
        wf = _workflow(workflow)
        sub = workflow != "publish.yml"
        _, _, test_id, prod_id = PUBLISHERS[workflow]
        assert set(wf) == {"name", "on", "permissions", "env", "jobs"} | ({"concurrency"} if sub else set())
        publish = {"name", "needs", "runs-on", "environment", "permissions", "steps"}
        want = {"build": {"name", "if", "runs-on", "permissions", "steps"} | ({"defaults"} if sub else set()), test_id: publish, INSTALL: {"name", "needs", "runs-on", "permissions", "steps"}, prod_id: publish, REPUBLISH: {"name", "if", "runs-on", "environment", "permissions", "steps"}}
        assert {job_id: set(job) for job_id, job in wf["jobs"].items()} == want
        assert {job["runs-on"] for job in wf["jobs"].values()} == {"ubuntu-latest"}
        if sub:
            assert wf["jobs"]["build"]["defaults"] == {"run": {"working-directory": PUBLISHERS[workflow][0]}}
        assert set(_step(wf["jobs"][INSTALL], INSTALL_STEPS[workflow])) == {"name", "run"}

    @pytest.mark.parametrize("workflow", ["publish-cascor-model.yml", "publish-protocol.yml"])
    def test_the_sub_package_build_steps_run_their_commands(self, workflow):
        build = _workflow(workflow)["jobs"]["build"]
        assert {name: str(_step(build, name)["run"]).strip() for name in SUB_PACKAGE_BUILD_RUNS} == SUB_PACKAGE_BUILD_RUNS

    def test_a_release_run_whose_build_failed_so_both_testpypi_jobs_were_skipped_is_refused(self, workspace, tmp_path, stand):
        # A skipped TestPyPI job never ran its check. Real records look like this (status completed, conclusion skipped).
        records = [_job(100, "Build and Validate", "failure"), _job(101, "Publish to TestPyPI", "skipped"), _job(102, INSTALL_NAME, "skipped"), _job(103, "Publish to PyPI", "skipped"), _job(104, REPUBLISH_NAME, "skipped")]
        server = TestFindReleaseRun._serve(stand, records)
        proc = _run(_script(FIND, tmp_path), workspace, **TestFindReleaseRun._env(tmp_path, server))
        assert proc.returncode == 1
        assert "  Publish to TestPyPI: skipped (attempt 1)" in proc.stdout
        assert f"  {INSTALL_NAME}: skipped (attempt 1)" in proc.stdout
        assert _outputs(tmp_path) == {}

    def test_an_older_release_run_that_passed_does_not_vouch_for_a_newer_one_that_failed(self, workspace, tmp_path, stand):
        # Ruling 1 reads the tag's NEWEST release run (a release can be published again, which starts another run).
        runs = [{"id": 4243, "head_branch": "v9.9.9"}, {"id": 4242, "head_branch": "v9.9.9"}]
        server = stand({_runs_path("v9.9.9"): [(200, {"workflow_runs": runs})], _jobs_path(4243): [_listing(*_attempt(1, 300, testpypi="failure", install="skipped", pypi="skipped"))], _jobs_path(4242): [_listing(*_attempt(1, 100))], _artifacts_path(4242): [(200, {"artifacts": LIVE_ARTIFACT})]})
        proc = _run(_script(FIND, tmp_path), workspace, **TestFindReleaseRun._env(tmp_path, server))
        assert proc.returncode == 1
        assert "  Publish to TestPyPI: failure (attempt 1)" in proc.stdout
        assert _jobs_path(4242) not in server.paths()
        assert _outputs(tmp_path) == {}

    @pytest.mark.parametrize("newest_first", [False, True], ids=["oldest-first", "newest-first"])
    @pytest.mark.parametrize(("first", "second", "passes"), [("success", "failure", False), ("failure", "success", True)], ids=["second-attempt-failed", "second-attempt-passed"])
    def test_the_highest_attempt_wins_in_whatever_order_the_listing_gives(self, workspace, tmp_path, stand, newest_first, first, second, passes):
        # GitHub does not document the order of filter=all; the step claims the record with the highest (run_attempt, id).
        records = _attempt(1, 100, testpypi=first, install="success" if first == "success" else "skipped", pypi="skipped") + _attempt(2, 200, testpypi=second, install="success" if second == "success" else "skipped", pypi="skipped")
        server = TestFindReleaseRun._serve(stand, list(reversed(records)) if newest_first else records)
        proc = _run(_script(FIND, tmp_path), workspace, **TestFindReleaseRun._env(tmp_path, server))
        assert (proc.returncode == 0) is passes, proc.stdout + proc.stderr
        if not passes:
            assert "  Publish to TestPyPI: failure (attempt 2)" in proc.stdout

    @pytest.mark.parametrize("which", ["release-run-lists-more", "testpypi-lists-more"])
    def test_testpypi_and_the_release_runs_sha256sums_must_name_the_same_files(self, tmp_path, stand, which):
        # "names other files" (the step's own comment), in either direction, not only another digest for a shared name.
        root = tmp_path / "workspace"
        root.mkdir()
        extra = "juniper_cascor-9.9.9-py2.py3-none-any.whl"
        recorded = dict(SERVED) | ({extra: _sha(b"another wheel")} if which == "release-run-lists-more" else {})
        served = dict(BUILT) | ({extra: b"another wheel"} if which == "testpypi-lists-more" else {})
        sums = tmp_path / "release-run" / "SHA256SUMS"
        sums.parent.mkdir()
        sums.write_text("".join(f"{digest}  {name}\n" for name, digest in sorted(recorded.items())), encoding="utf-8")
        server = TestFetchTestPyPIFiles()._serve(stand, served)
        proc = _run(_script(FETCH, tmp_path), root, **TestFetchTestPyPIFiles._env(server, sums))
        assert proc.returncode == 1
        assert "disagree" in proc.stdout
        assert not [p for p, _ in server.requests if p.startswith("/files/")]
'''


def commands(run: str) -> list[str]:
    return [line.strip() for line in run.splitlines() if line.strip() and not line.strip().startswith("#")]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--test", required=True, type=Path)
    parser.add_argument("--pristine", required=True, type=Path)
    args = parser.parse_args()
    text = args.test.read_text(encoding="utf-8")

    def once(old: str, new: str) -> None:
        nonlocal text
        if text.count(old) != 1:
            raise SystemExit(f"anchor occurs {text.count(old)} times: {old[:80]!r}")
        text = text.replace(old, new)

    install, sub_runs = {}, None
    for name in FILES:
        wf = yaml.safe_load((args.pristine / name).read_text(encoding="utf-8"))
        step = [s for s in wf["jobs"][INSTALL]["steps"] if "run" in s][0]
        install[name] = commands(step["run"])
        if name != "publish.yml":
            runs = {s["name"]: str(s["run"]).strip() for s in wf["jobs"]["build"]["steps"] if s.get("name") in SUB_BUILD_STEPS}
            if sub_runs is not None and runs != sub_runs:
                raise SystemExit("the two sub-package build jobs differ")
            sub_runs = runs
    constants = f"#: workflow -> its install step's commands, comment and blank lines dropped (review fix).\nINSTALL_COMMANDS = {install!r}\n#: The sub-package build steps' own commands (review fix).\nSUB_PACKAGE_BUILD_RUNS = {sub_runs!r}\n"

    start = text.index('    @pytest.mark.parametrize("workflow", sorted(PUBLISHERS))\n    def test_the_install_checks_moved_to_their_job_with_the_commands_they_ran_before')
    end = text.index("class TestTemplate:")
    once(text[start:end], NEW_INSTALL_TEST)
    once(OLD_REPUBLISH, NEW_REPUBLISH)
    once("\n\ndef _workflow(name: str) -> dict:", "\n\n" + constants + HELPER)
    text += NEW_CLASS
    args.test.write_text(text, encoding="utf-8")
    print(f"patched {args.test}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
