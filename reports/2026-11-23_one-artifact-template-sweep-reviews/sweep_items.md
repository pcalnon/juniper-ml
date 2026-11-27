# One-artifact template: items for ONE sweep across juniper-cascor and every port (after the 8 PRs merge)

Collected 2026-11-15 from the independent reviews of the ports and of juniper-ml#2592. Each changes the template
text that every port copies verbatim (and the ports that pin the blocks' sha256 must move their pins with it).

1. The comment above the republish job: "A dispatch run is not a release-event run, and the ceremony never reads one"
   is false once juniper-ml#2592 merges (the monitor reads the publisher's dispatch runs on the tag).
2. Sub-package publishers' top comment "Each job adds what it needs to this": job-level `permissions` REPLACE the
   workflow block, they do not add to it (review of recurrence#236, NIT 12).
3. The republish "Find the release run's artifact" step accepts a bare `v<version>` tag in a SUB-package publisher
   (its tag parsing takes `v` or `<package>-v`): narrow it to `<package>-v` there (recurrence#236 review, NIT 5; also
   noted by the juniper-ml port). Latent: needs the pypi approval and only publishes TestPyPI's files.
4. Tests pin retention `> 30`, not the documented 90 (recurrence#236 review, NIT 6): pin 90.
5. Tests exempt a build step from the reuse condition by its `if:` TEXT (`github.event_name == 'push'`), not by the
   gate step's name (NIT 7).
6. SECURITY HARDENING to consider: the TestPyPI job holds `id-token: write` and also runs the install check, which
   executes TestPyPI's package plus dependencies from PyPI with the token-request variables in its environment
   (NIT 9). Moving the install check to its own job without `id-token` removes that exposure. Pre-existing (the token
   was workflow-level before), not widened by the ports.
7. Docs in every port: the ladder holds only for tags cut after the port merged (old tags: skip-existing, no checks,
   7-day artifacts, no republish input); and after a PLAIN dispatch has itself published to TestPyPI, rung 2 targets
   the dispatch run, not the release run (recurrence#236 review, MINOR 1 and 2: fixed in recurrence; check the others).
8. juniper-cascor's own template test (`src/tests/unit/test_publish_one_artifact.py`) shares items 4 and 5.
9. Tests never pin a check step's `if:`/`continue-on-error` nor a job's `continue-on-error` (canopy#823 review, MAJOR,
   inherited from cascor's test: 15 mutations survived, e.g. `continue-on-error: true` on "Verify TestPyPI still serves
   exactly these files"). Fixed in canopy's copy in #823's follow-up; the identity checker now fails a job-level
   `continue-on-error` (step-level ones already fail its step comparison). Add to cascor's test and every port's.
10. Install checks import the package from the CHECKOUT root (`python -c` puts the cwd first), so a broken wheel can
    pass (canopy#823 review reproduced it with the real 0.10.0 wheel; cascor has `juniper_cascor/` at its root too).
    Fixed in canopy (#823 follow-up); run every repo's import from outside the checkout.
11. Ladder docs: after a TestPyPI job failed AFTER its upload (the install check), the republish would publish files
    whose install check failed (it does not check that job's result). CORRECTION (canopy#823 follow-up, confirmed in
    warehouse `forklift/legacy.py` file_upload ~1195-1198 and by the trio review): "Re-run failed jobs" re-uploads the
    SAME bytes from the run's artifact, which TestPyPI/PyPI accept (200, before attestations), so the re-run repeats
    both checks harmlessly -- my earlier claim that it "fails at the upload every time" was WRONG. What TestPyPI
    refuses is a re-CUT (a new build: new bytes under existing names). Fixed in canopy's runbook; cascor's MANUAL and every port need it. OWNER QUESTION: should
    the republish job require that the release run's TestPyPI job succeeded?
12. The single-package build guard `startsWith(tag, 'v')` silently skips `rc*`/`hf*` tags, which the publish
    environments admit for future conventions (D2 of `notes/JUNIPER_2026-08-17_JUNIPER-ECOSYSTEM_PUBLISH-PATH-AUTHORIZATION-DESIGN.md`).
14. Tests' `BUILD_COMMAND` knows only four build commands and the order checks allow extra steps, so a rebuild slipped
    into the PyPI job (`pyproject-build`, `hatch build`) or a deleted `setup-python` passes (data#543 review, MINOR,
    inherited). Pin the exact step list of each job (fixed in data's and canopy's copies in their follow-ups).
15. Template docs (cascor MANUAL, copied by ports): when "Verify PyPI serves exactly these files" fails the files are
    ALREADY on PyPI (the step runs after the upload), so "do not publish this version from this run" is wrong
    (data#543 review NIT 6).
16. MERGE ORDER: the four ports that ADD a build job (data, data-client, cascor-client, cascor-worker) merge after
    juniper-ml#2592, or a build failure there reads as a note with no issue until #2592 lands.
17. Each port's test should pin its workflow `name:` ending in "to PyPI": juniper-ml#2592's monitor drops runs of any
    other workflow, so a renamed publisher fails QUIETLY (NOT_FOUND, then IN_PROGRESS, exit 0, no issue) (#2592
    round-2 review NIT 7). All 18 comply today.
18. juniper-ml `docs/REFERENCE.md` version line: #2592 edited the file without a bump (#2593 bumps it to 0.6.77); the
    plan record PR can bump it once more.
19. Tests let the install check be switched off (`|| true` on its pip line, `continue-on-error` on the step or job),
    accept the action's old `skip_existing` spelling and `attestations: false`, and allow an extra step writing into
    `dist/` before Record SHA256SUMS (trio review S5). Fixed in each port's follow-up where flagged; cascor's test too.
20. The republish job derives the version from the tag, so a tag that is not `v` + the exact package version (e.g.
    data-client's `v0.3.1-beta`, which shipped 0.3.1 files) cannot be republished: TestPyPI's JSON 404s, it fails safe.
21. MAJOR-class doc gap everywhere (ml#2593 review, MAJOR; canopy/trio/data reviews too): rung 1 republishes TestPyPI's
    files whatever the release run's TestPyPI job concluded, so a real install-check failure must route to a new patch
    version, never rung 1; and "fix; re-cut (idempotent)" is false for a same-version re-cut now that `skip-existing`
    is gone (TestPyPI refuses new bytes under existing names). Fixed per port in the follow-ups (ml#2593 after #2592
    merges); cascor's MANUAL needs it. OWNER QUESTION (item 11): make the republish job refuse unless the release run's
    TestPyPI job succeeded?
22. A sub-package republish dispatched from the META `v<version>` tag publishes TestPyPI's sub-package files of that
    number without consulting the sub-package's release run (ml#2593 review rehearsed it with the PR's own steps); no
    version collides today. Template fix: accept only `<package>-v<version>` in a sub-package publisher (item 3).
23. The raw-text sha256 pins of the template blocks (data, cascor-client, data-client, worker, ml) include the action SHA
    pins inside the template steps (upload/download-artifact, pypa/gh-action-pypi-publish in the republish job), so a
    Dependabot bump of those actions fails each such port's digest case until it is re-ported from cascor: Dependabot
    PRs touching them need a person. Decide in the sweep whether to pin the blocks' `run` scripts only.
24. Status after this handoff was written (session 08ef3e, 23:50Z): ml#2592 MERGED 23:36:08Z (`6541b2cc`); data#543's
    fix-up pushed (head `6fc7d53f`, CI green, CLEAN) -- ready to merge in the next thread. canopy#823's fix-up pushed
    (head `1e8a8ece`, CI green, CLEAN; 69 cases, 86 mutations; install check now imports from `$RUNNER_TEMP`) -- ready.
    Only canopy's fix-up brief carried the wrong re-run claim (item 11), and canopy's agent corrected it from warehouse's
    code. The trio's and ml#2593's briefs spoke of a BROKEN package or of NEW bytes, which hold; still read each port's
    final ladder text against item 11 before merging.
26. ml#2593's fix-up pushed (head `acc5c262`, CI green; behind main only by #2594, which shares no file with it, so
    safe_merge's update-branch handles it). OWNER QUESTION / doc clarification it raised: after a TestPyPI job that
    failed only for a transient index lag, rung 1 (republish) publishes files whose install check never passed, while
    "Re-run failed jobs" on the release run re-uploads the SAME bytes (accepted, item 11) and re-runs the install check.
    The owner's ladder (dialog 2) was asked about an expired `pypi` gate, i.e. a release whose TestPyPI job succeeded;
    propose: the ladder applies only after a green TestPyPI job, and a transiently failed TestPyPI job is re-run.
27. STATE at 2026-11-16 08:39Z (read from gh): MERGED -- recurrence#236 (11-15 23:07Z), ml#2592 (11-15 23:36Z), ml#2594
    the handoff (11-16 00:03Z), canopy#823 (08:27Z, head 1e8a8ece), data#543 (08:30Z, 6fc7d53f), cascor-client#199
    (08:31Z, fe962b7b), data-client#264 (08:36Z, 61d6b44b); the last four by the owner's armed auto-merge. OPEN with
    auto-merge armed, CI running -- ml#2593 (head 67e9aab1, an update-branch merge over the reviewed acc5c262) and
    cascor-worker#232 (head a0b5e363, an update-branch merge over the reviewed 41933886). The identity checker passes
    all 7 merged workflows as they are on each repo's main (`tmp/ports/verify_main.bash`). Next thread: confirm those
    two merge, run the checker on their mains, then the sweep and plan v1.15.17.
25. The cross-repo identity checker exempts a build step gated `github.event_name == 'push'` from the reuse condition
    (needed for the sub-package shape's push-only release gate); keep or narrow it to that step's name in the sweep.
13. Evidence for the plan's unverified item: canopy 0.10.0's TestPyPI provenance shows `environment: null` while PyPI's
    shows `pypi` (cascor 0.14.0: null on both), so canopy's TestPyPI trusted publisher looks environment-unbound.
