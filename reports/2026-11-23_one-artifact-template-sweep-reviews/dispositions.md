# Cascor sweep: review dispositions (orchestrator `e71d3e`, 2026-11-23)

Every fix goes into the WRITER `util/ad-hoc/2026-11-23_cascor_one_artifact_sweep_edits.py`, never only into the clone,
so a re-run on cascor `main` after #772 reproduces it. Reviews are on the frozen clone `tmp/sweep/cascor/juniper-cascor`
(diff sha256 `da204bfa…`).

## Workflow lens (report: `tmp/review-workflow-lens/`; 0 blocker, 0 major, 6 minor, 7 nits)

| id | finding (short) | disposition |
|---|---|---|
| M1 | Sub-package install checks swallow 5 pip failures and then fail on the import, so index lag looks like a broken package. `publish.yml` has no retry. MANUAL routes "does not install or import" to a new patch version. | FIX. After the 5th failure: `::error::` "… not installable from TestPyPI after 5 tries (index lag?): Re-run failed jobs; a real failure repeats". Give `publish.yml` the same loop. MANUAL: "if unsure, Re-run failed jobs first". |
| M2 | Template comment and MANUAL say a carried-over job "keeps the record of the attempt that ran it". On the live API (canopy run 43135960676, a real "Re-run failed jobs") GitHub COPIES carried jobs into attempt N+1 (`run_attempt` N+1, new id, attempt N's `started_at`/conclusion). The selection is still right; the wording and the log line are wrong. | FIX the comment, the MANUAL text and the log line ("in the latest attempt (N)"). ADD a rehearsal with the copied-record shape. Record in plan v1.15.18 that `filter=latest` is now VERIFIED equivalent (plan v1.15.17 says unverified). |
| M3 | Re-cutting a Release starts a new release run that TestPyPI refuses (400), and that newest run then blocks rung 1 for the tag forever. | DOCS. Never re-cut a Release to retry; use "Re-run failed jobs". After a re-cut, rung 1 refuses that tag, so the next rung applies. |
| M4 | A sub-package PLAIN dispatch accepts any tag (`v*` included), while the docs say a `v` tag is refused. | FIX the guard: add `&& startsWith(github.ref_name, '<pkg>-v')` to the dispatch branch, then check the docs match. |
| M5 | `publish.yml`'s install check tests the TAG's version; nothing asserts that tag == built version. | DEFER, as new SWEEP item 28 (pre-existing; the fix touches template steps or outputs). Record it in plan v1.15.18. |
| M6 | The protocol install check reads only metadata, so a wheel lacking the package passes. | FIX: also assert `importlib.util.find_spec("juniper_cascor_protocol")`. |
| N1 | `${{ github.event.release.tag_name }}` is expanded into the script. | FIX: pass it through `env:`. |
| N2 | The sparse checkout persists credentials while TestPyPI code runs. | FIX: `persist-credentials: false`. |
| N3 | "witness to what the TestPyPI job tested" is stale template text. | FIX the wording (the install job tests now). |
| N4 | Sub-package PyPI jobs hold `contents: read` with no checkout. | FIX: drop it, so the job holds exactly `id-token: write`. Update MANUAL `:687` and REFERENCE `:268`. Tests and checker pin it. |
| N5 | `startsWith` is case-insensitive while Python's `str.startswith` is not. | NO CHANGE (fails safe). |
| N6 | The gate runs after the `pypi` approval, so the approver approves blind. | DEFER, as SWEEP item 29 (a pre-gate check job). Record it. |
| N7 | After the artifact expires, republish takes every file TestPyPI lists. | DOCS: say it in rung 1's text. |

### M2 verified by the orchestrator (~14:00Z)

`python3 -I tmp/arc/attempt_compare.py juniper-canopy 43135960676`, a real "Re-run failed jobs" (attempt 2 of 2):

- Each attempt lists 19 job records, and so does `filter=latest`.
- Twelve attempt-2 records are COPIES: a new id, `run_attempt` 2, and attempt 1's `started_at` and conclusion.

The per-name-latest rule is right. The template comment, the MANUAL text and the log line must describe copies, not "keeps the record of the attempt that ran it".

## Test lens (report: `tmp/review-test-lens/`)

Summary: 15 of 55 property-breaking mutations survive the suite, and the checker passes 21. Tools:

- harness: `util/ad-hoc/2026-11-23_publish_one_artifact_test_lens_mutations.py`;
- proposed pins: `util/ad-hoc/2026-11-23_publish_one_artifact_test_lens_proposed_fixes.py`, which gives 143 cases on unchanged workflows and kills all 15 survivors.

Every item below is FIX unless marked.

| id | gap | fix |
|---|---|---|
| G1 | No test refuses SKIPPED TestPyPI jobs, the normal failure shape when the build fails. | A rehearsal where the build failed and both TestPyPI jobs were skipped: refuse. |
| I1-I8 | The install check can be switched off or redirected: `exit 0`, `trap 'exit 0' ERR`, `PIP_EXTRA_INDEX_URL` in step or job `env`, a hard-coded `VERSION`, a pre-install from PyPI. | Pin each install step's WHOLE command list exactly, comment lines dropped, written AFTER the M1 change. Pin its keys to exactly `{name, run}` (plus whatever the step needs). Give every job a key allow-list, and refuse any `PIP_*` in step or job `env`. |
| G16 | Nothing proves an older passing run cannot vouch for a newer failed one. | A fixture where the newest run failed and an older one passed: refuse, and never request the older run's jobs. |
| F4 | "names other files" is unpinned. | Cases where the release run lists an extra file, and where TestPyPI does: both refuse before any download. |
| B1/B2 | The sub-package build commands are unpinned. | Pin all three publishers' build commands. |
| J1 | Job-level `env` can override the poll bounds. | Refuse `HASH_CHECK_*` (and any `env`) on the publish jobs, or pin each job's `env` exactly. |
| G7 | Every fixture lists attempts oldest-first. | Add reversed-order fixtures. |
| R2 | `runs-on` is unpinned outside the install job. | Pin `runs-on` for every job. |
| C2/C3 | A harmless comment inside an install script fails a test. | Resolved by the exact command-list pin, which drops comments. |
| D1/D2 | An `@ref` bump fails only inside the republish job. | Compare the republish jobs by action name, plus ONE explicit test that each action has a single ref across the three files ("keep them aligned"). |
| docs | Poll numbers (20 attempts, 15 s apart, 285 s, ~15 min) and the 5×10 s retry are unpinned. | Pin them exactly, or reword the docs. The retry pin must match the post-M1 loop. |
| N4 / BRIEF 3 | Sub-package PyPI jobs hold `contents: read` with no checkout. | Same as N4: drop it, and pin exactly `id-token: write`. |

**Checker** (`util/ad-hoc/2026-11-23_publish_port_template_identity.py`), all FIX:

- K3: the build guard must EQUAL one of the two exact forms, with the prefix filled in. Today an `||` defeats it.
- K4/W8/W8b: compare each publish job's (name, action) list with the template's. A rebuild step before the PyPI upload must fail.
- K1/K2/I3/I4: the install job has exactly one `pip install`, with `--index-url https://test.pypi.org/simple/`, `--no-deps` and no `--extra-index-url`, and no `PIP_*` in any `env`.
- I1/I2/I8: refuse `exit`, `trap` and `set +o` lines in the install step; the import is the last command. I6 (a hard-coded version) is the repo test's job.
- K5/K6: no `continue-on-error` or `if:` on upload steps.
- K8: the prefix must match `PUBLISH_DIST_DIR`'s shape: `dist` with `v`, `<pkg>/dist` with `<pkg>-v`.
- No early `return`: report every failure that can still be checked.
- No extra job's name may contain "pypi" (ceremony.py:660-661).
- The `cd` check must catch `(cd X && python …)`.

Then RE-RUN:

- the full test file on both bases;
- both mutation tools: `mutation_proof.py` (34) and the test-lens harness (every property-breaking mutation caught, the harmless ones passing);
- the checker on cascor's three workflows, plus negative cases;
- actionlint, pre-commit, B914, and sequence-safety.

## Round-2 review (report: `tmp/r2review/`, probes `util/ad-hoc/2026-11-23_publish_sweep_r2_review_probes.py`)

The workflow fixes hold when executed. The CHECKER (`util/ad-hoc/2026-11-23_publish_port_template_identity.py`), which
gates the ports, is both too strict and too weak. In the port simulation (`tmp/r2review/port-sim/`, fetched mains in
`tmp/r2review/ports-main/`), 10 of the 15 faithful ports fail it.

| id | sev | finding | disposition |
|---|---|---|---|
| F1 | blocker | The build-window rule (only `twine check` between the build and `Record SHA256SUMS`) rejects juniper-ml's `Assert release tag matches built version` (all 7 ml publishers, pinned by ml tests) and canopy's `Import smoke test (built wheel, nothing from the checkout)`. It is also too weak: a `twine check` step with an appended `cp` passes. | FIX (checker): an EXACT-match allow-list for that window: `twine check dist/*`, the ml assert command with its prefix, and canopy's smoke step verbatim. |
| F2 | blocker | juniper-ml `publish.yml`'s two-phase verify (#384: TestPyPI `pip download --no-deps`, then three PyPI installs of the local wheel) is the inverse of the install rules. | FIX (checker): key the TestPyPI rules on the ONE command that fetches `<pkg>==` (`--no-deps`, the TestPyPI index alone, before any other pip command). A later pip command must not name the target (the local wheel excepted), may use at most `--index-url https://pypi.org/simple/`, never `--extra-index-url` or `-f`. The lag rule: the last try prints `::error::` then `exit 1`, with the count read from the loop. The juniper-ml side (drop `|| true` after `ls -la`; `pip download … && { FETCHED=1; break; }` in place of the `set +e` block) belongs to the ml PORT, not here. |
| F3 | major | recurrence-client and recurrence-model install runtime deps by name after the TestPyPI install, then import (recurrence-model pins it in `test_publish_smoke_pins.py:47`). | FIX (checker): F2's target-keyed rule admits them. |
| F4 | major | Install rules bypassed: `export PIP_EXTRA_INDEX_URL`, `pip config set`, inline `PIP_*=` on the target line, `pip -q install` / `pip3.12 install` before the loop, the twine-step append. | FIX (checker): match pip in any form (`(?:python3? -m \|uv )?pip(?:3(?:\.\d+)?)?(?:\s+-{1,2}[\w-]+(?:[= ]\S+)?)*\s+(install\|download)`); refuse `PIP_[A-Z_]+=`, `pip config`, `PIP_CONFIG_FILE`, `pip.conf` anywhere in the script; refuse `PIP_*`/`PYTHON*`/`UV_*` env keys at every level. |
| F5 | minor | MANUAL `:713`, `:760` overclaim M4 for tags cut before the change. | FIX: "for tags cut after this change". |
| F6 | minor | `test_publish_docs_bounds.py` fails on a harmless rewrap. | FIX: compare whitespace-normalized text. |
| F7 | minor | Key allow-lists refuse `timeout-minutes`, `run-name`, `concurrency`. | FIX: admit them (workflow `run-name` and `concurrency`, job `timeout-minutes` and `concurrency`); state the rationale in the test. |
| F8a | nit | MANUAL re-cut: "TestPyPI refuses its files" holds only once TestPyPI holds the version. | FIX the wording. |
| F8b | nit | `publish-protocol.yml:388` uses `assert`, which `PYTHONOPTIMIZE` strips. | FIX: `raise SystemExit(...)`. |
| F8c | nit | The checker says `shell:` means `-e` is not applied, which is false for `shell: bash`. | FIX the checker's reason text (keep refusing `shell:` if wanted, with a true reason). |
| F8d | nit | MANUAL `:760` "only from a tag": the guard tests `ref_name`, and the tag-only environments refuse branches. | FIX the wording. |
| F8e | nit | `publish.yml:398` "witness to what the install check tested": only the wheel is install-tested. | FIX the wording. |
| F8f | nit | A tag/built-version mismatch first reads as "(index lag?)". | NO CHANGE (M5 deferred as item 28). Note: juniper-ml's assert step IS M5's fix for ml, so F1 must keep it. |

Acceptance for the checker fix:

- cascor's 3 round-2 workflows PASS on both bases;
- every port simulation PASSES, after the small changes the review lists (canopy: one `cd`; data, cascor-client, cascor-worker: tag via env; config-tools and doc-tools: `python -c` last; ml `publish.yml`: the F2 juniper-ml edits);
- all bypass mutants in `tmp/r2review/neg/` FAIL;
- the earlier 43 negative cases keep their verdicts;
- re-run the review's probes script.

## Round 3 (the second fix pass; reviewed by round 4, below)

The executor reported this. Its full report is in session `11a98f94`'s subagent transcript (`agent-ad9ca4951fdc326a5`),
and its evidence is in `tmp/sweep/cascor-r3/evidence/`.

**Final tree.** `tmp/sweep/cascor-r3/juniper-cascor`: diff `tmp/sweep/cascor-r3/sweep.diff`, sha256
`e02b4da8bfbe1a99c2b46e0c23e66f91cbaf884c7d5bf7a79f957cb63e3cb525`, 11 files, +1151/-190. Treat it as FROZEN.

**Interdiff and versions.** The round 2 -> round 3 interdiff is `tmp/sweep/cascor-r3/r2_to_r3.diff` (250 lines).
- Writer sha256: `a287376f…`.
- Checker sha256: `2feceecf…`.
- The checker as round 2 reviewed it: `tmp/sweep/cascor-r3/checker_r2_as_reviewed.py`.

**Applied.**
- Checker: F1-F4 and F8c.
- Cascor: F5, F6, F7, F8a, F8b, F8d, F8e.
- Rules round 3 ADDED beyond the review, named in the checker's own docstring:
  - the install job: no `container`, and no action except setup-python and checkout;
  - an install step's `env` may hold `RELEASE_TAG` only;
  - the install script: no `GITHUB_ENV`/`GITHUB_PATH` write, no `PATH` assignment, no alias or function;
  - no workflow `defaults.run.shell`;
  - no `cancel-in-progress` concurrency;
  - `bash -n` on every bash step.

**Results, on both bases** (cascor `main` `802399ab` and #772's head `1e6e877a`):
- tests: 161 passed (`test_publish_one_artifact.py` and `test_publish_docs_bounds.py`); the 14 workflow-reader files
  433 passed and 8 skipped;
- the 45-mutation proof: 45 of 45 caught;
- the test-lens harness (81 edits): 68 of 68 caught, 10 of 10 harmless pass, 3 fail BY DESIGN (C4, D1, D2);
- the checker: cascor's 3 PASS;
- the port simulations: 15 of 15 pass (12 faithful, 2 reordered, 1 faithful plus the ml F2 edits); before round 3,
  5 of 15 passed;
- the bypass mutants in `tmp/r2review/neg/`: all 7 FAIL;
- the earlier 43 cases: all unchanged;
- `checker_proof_r3.py`: 74 of 74;
- cascor's 11-15 non-vacuity script: 41 of 43. The other 2 don't apply, because their anchors were rewritten;
- actionlint, cascor pre-commit, B914 (0 sites; `evidence/b914.log` is empty) and the symbol-loss screen: clean.

**Residual risk.** In an F3-style port, a later dependency install can pull a different version of the target.

**Fail by design** (not dispositioned): the suite's H2d, H2e, H4, H10.

## Round-4 review (report: session `11a98f94`'s subagent "Round-4 review of second fix pass"; probes `util/ad-hoc/2026-11-23_publish_sweep_r4_review_probes.py`; output `tmp/r4review/`)

Verdict: 0 BLOCKER, 2 MAJOR. Neither MAJOR is a defect in cascor's frozen tree (`e02b4da8…`), which the writer
reproduces byte for byte. Stopping rule: MAJOR 2 is in the CHECKER, so fix it and run a round-5 review of the
checker's interdiff. The cascor-side MINOR and NIT fixes need no new round.

| id | sev | where | finding | disposition |
|---|---|---|---|---|
| R4-1 | MAJOR | juniper-ml ml PORT | ml's `tests/test_publish_testpypi_verify.py:86-90` and `tests/test_publish_subpackage_workflows.py:92-98` look up the install step only in the TestPyPI job, and raise `SkipTest` when it is missing. After the ruling-2 move, every #384 pin is silently skipped: 28 tests run drop to 4, and CI exits 0. | ML PORT must: retarget both lookups to the install job; make "not found" a FAILURE; set the expected TestPyPI permissions to `{id-token: write}` (`:237`); show no new skip in any repo's publish tests. Add this to the port acceptance. |
| R4-2 | MAJOR | checker | A `\| tee …` or a single `&` after the final `python -c` makes a failing import exit 0 under `bash -e` (no pipefail), and the checker passes it (mutants M1, M2, M10). | FIX: the last command must be exactly `python`/`python3`, `-c`, one argument; refuse a `\|` or single-`&` control operator anywhere in the install script outside `$(...)`. |
| R4-3 | MINOR | checker | Obfuscations pass: a `python()` function (M3); `hash -p` (M4); `-mpip` (M5); `"${p:-pip}"` (M6); `pip${u} config` (M7); an unquoted fetch target (M8); `PYTHONPATH+=`. | FIX: refuse a command whose first word contains `$` or a backtick; refuse `-m\s*pip`; refuse `hash`, `eval`, `source`, `.`, `exec`, `bash -c`/`sh -c` and any `NAME ()` definition; require the fetch target and `--dest` quoted; cover `+=`. Or narrow the docstring. |
| R4-4 | MINOR | cascor test, CHANGELOG, checker | A job-level `concurrency` group CANCELS pending jobs (GitHub's default `queue: single`), so the PyPI job can be cancelled between uploads. | FIX: admit `concurrency` at WORKFLOW level only (plus the build job if wanted); keep job `timeout-minutes`. Correct the test comment (`:182-186`, `:282`), `CHANGELOG.md:292`, the checker (`:580-583`) and `checker_proof_r3.py` control C5. |
| R4-5 | MINOR | checker / ports | 6 ports end their install check with metadata only (cascor-client, cascor-worker, data, data-client, ml ci-tools, ml observability): the M6 gap. | DEFER as a port item: each such port adds a failing `find_spec(<module>)` (ml's policy at `test_publish_subpackage_workflows.py:302-309` allows it). The checker may require `import <mod>` or `find_spec`, exempting the meta-package. |
| R4-6 | MINOR | checker | The F1 window is wider than its comment: a build-job `defaults.run.shell` wrapper (M12); `TAG_ASSERT` admitted in every repo (M13); `CANOPY_SMOKE` resolves deps. | FIX: refuse `defaults.run.shell` on the build job; admit `TAG_ASSERT` only for juniper-ml and its 6 sub-packages, `CANOPY_SMOKE` only for canopy; reword the comment. |
| R4-n | NIT | cascor CHANGELOG | `:276-277` "(MANUAL.md says the same)"; `:284` "builds only from the package's own tag" (the guard tests the ref NAME); `:292` lists `run-name` as a job key; #767's unreleased entry `:197` still says "witnesses what the install check tested". | FIX the wording. Correct #767's entry in place. |
| R4-n | NIT | cascor test comment | It says jobs may add `timeout-minutes`, but the republish job may not (it must stay byte-identical). | FIX the comment. |
| R4-n | NIT | checker | It no longer requires the template's exact lag-error text, so a port can lose the operator signature `MANUAL.md:709` quotes. Several rules are over-strict: `shell: bash`; `PYTHON*` keys in build jobs; `pip --version`; `-i`; `for … in $(seq …)`; an echo naming "pip <word>". | FIX: require the error text. Relax the over-strict rules where safe, else document them. |

**Sound:**
- the writer reproduces the frozen tree;
- actionlint is clean;
- 161 tests pass, and every round-2 harmless edit now passes;
- F8b holds when executed;
- the loop simulation holds;
- 15 of 15 port simulations reproduce, and the 7 round-2 mutants fail;
- the port policies are kept (recurrence-model's smoke pins, canopy's smoke step, ml's tag assert, #384's two phases once retargeted);
- the MANUAL lines match the YAML.

## Fix pass 3 (round 4's fixes; tree cascor-r4)

The executor reported this: the final message of session `d935c226`'s subagent `agent-a3e7199340f4d2bf4` (orchestrator
`ffffd3`, brief `tmp/sweep/FIXPASS3_BRIEF.md`). Its evidence is in `tmp/sweep/cascor-r4/evidence/`; every driver that
produced it is beside it in `tmp/sweep/cascor-r4/`. The proofs ran twice. The first run (kept in
`tmp/sweep/cascor-r4/run1/`) found a ragged line in the CHANGELOG's Pins bullet, which the writer's last change
re-flowed (it adds R4-4's reason, "which by default cancels its pending job when another queues"). `rerun_all.bash`
then rebuilt both trees and re-ran every proof on them; the results below are that second run's.

**Final trees.** Both are fresh clones with the writer applied. Treat both as FROZEN.
- Base B, cascor `main` `e9c86f83` (#772 merged): `tmp/sweep/cascor-r4/main/juniper-cascor`, diff
  `tmp/sweep/cascor-r4/main/sweep.diff`, sha256 `a63991221c1f66a57aa59bd95ea7c7b4d5c1d0630e3b43788b18352f4f1fb42e`,
  2078 lines, 11 files, +1161/-190.
- Base A, cascor `802399ab`: `tmp/sweep/cascor-r4/juniper-cascor`, diff `tmp/sweep/cascor-r4/sweep.diff`, sha256
  `f056c538f8600d007ab721793eedb2f6a5ad59215f2b7d57fe49629ebe5abaa4`, 2087 lines, 11 files, +1162/-191 (one more
  `AGENTS.md` line: its `**Last Updated**` already reads 2026-11-23 on `e9c86f83`).
- The proofs ran on `work-a` and `work-main` (copies of the unswept trees, the writer applied); their sweep files equal
  the clones' (`evidence/interdiffs.log`).
- cascor `main` moved during this pass: #774 (the B914 literal merges) merged at 21:17:44Z as `829af03d`, one commit on
  `e9c86f83`. It changes 27 files, none of the eleven; on `829af03d` the writer makes the same eleven files byte for
  byte (`evidence/base_c_check.log`, `evidence/base_c_pytest.out`).

**Interdiffs and versions.**
- Cascor, round 3 -> round 4: `tmp/sweep/cascor-r4/r3_to_r4.diff` (112 lines, sha256 `6253ed85…`):
  `src/tests/unit/test_publish_one_artifact.py` +16/-8 and `CHANGELOG.md` +13/-11, nothing else; no workflow changes.
  The same 7 hunks on base B (`evidence/compare_fixpass3_hunks.log`).
- Writer: `tmp/sweep/cascor-r4/writer_r3_to_r4.diff` (135 lines); sha256 `a287376f…` -> `3f1d3ead6fbd29537ae20388f99c77ad63cd0a1cb9429e1f65f1fc5488a3e952`.
  As round 4 reviewed it: `tmp/sweep/cascor-r4/writer_r3_as_reviewed.py`.
- Checker: `tmp/sweep/cascor-r4/checker_r3_to_r4.diff` (580 lines); sha256 `2feceecf…` -> `c826ab875ecb5d6ad95891e341fb3b27020cfddf25d0161a4a44e04c74f88236`.
  As round 4 reviewed it: `tmp/sweep/cascor-r4/checker_r3_as_reviewed.py`.
- `tmp/arc/sweep_scripts.sha256` regenerated over the same six paths (only the writer's and checker's lines change;
  round 3's kept as `tmp/arc/sweep_scripts.r3.sha256`); `sha256sum -c` passes.

**Base B, accounted for** (`evidence/account_base_b.log`). 32 files differ between round 3's `cascor-r3/work-after772`
and base B's swept tree:
- fix pass 3: the test module and `CHANGELOG.md` (the same hunks as on base A), and `logs/juniper_cascor.log`, round
  3's test run, in its `work-after772` only;
- the base, 30, the same with or without the writer: #772 was rebuilt after round 3 (its head `1e6e877a` -> `31136d64`,
  one commit on `802399ab`, squashed as `e9c86f83`; read-only `gh` compare). 27 files pass through untouched or through
  the writer; `AGENTS.md`'s other hunk is its date line, which the writer sets to 2026-11-23 on both bases;
  `scripts/default_interactive_session_claude_code.bash` and `scripts/wake_the_claude.bash` are regular files at
  `1e6e877a` and out-of-tree symlinks at `e9c86f83`, which the archive skips;
- unexplained: none. The person-word differs as expected (`owner` on `802399ab`, the renamed word on `e9c86f83`).

**Applied.**
- R4-2 (checker): an install step that runs pip ends at exactly `python`/`python3`, `-c`, one argument; no `|` or
  `|&` outside `$(...)`, no `&`, no process substitution (`check_install_job`, `check_constructs`).
- R4-3 (checker): no computed command name (`$` or a backtick in it); no `-m pip` in any spelling; `eval`, `source`,
  `.`, `exec`, `hash` and the shells refused as commands (a shell whether or not `-c` follows); no function in either
  form; the fetch target and `--dest` double-quoted; `+=` counted as an assignment, and `PYTHON*` and `PATH` refused on
  any mention in the script. The fix, not the docstring narrowing.
- R4-4 (writer, so cascor's test and `CHANGELOG.md`; the checker; the proofs): `concurrency` admitted at the workflow
  level only (`OPTIONAL_WORKFLOW_KEYS`), `timeout-minutes` kept for jobs (`OPTIONAL_JOB_KEYS`); the job-level
  `_cancels` assertion removed, since the key allow-list now refuses any job group; the test comments (`:182-190`,
  `:605-610`) and the CHANGELOG's Pins bullet say why, qualified "by default (`queue: single`)". The checker refuses a
  job's group on EVERY job, the build job included (the "if wanted" option not taken: a cancelled pending build has
  uploaded nothing, but no port has one and one rule is simpler). C5 is now FAIL in `checker_proof_r4.py`; the test
  lens's C10 moves to "catch", with C11 and R4a added.
- R4-6 (checker): a build-job `defaults.run.shell` refused; `TAG_ASSERT` admitted only under `--repo juniper-ml` for
  its seven packages, `CANOPY_SMOKE` only under `--repo juniper-canopy`; the F1-window comment reworded. The repository
  comes from the operator: `--repo` is required, one of `REPOS`; every caller this pass added passes it
  (`checker_with_repo.py` for round 2's and round 3's unchanged drivers).
- R4-n NITs (writer): the CHANGELOG's "(`MANUAL.md` says the same)" now "(`MANUAL.md` now says so too)", scoped to what
  MANUAL says; "builds only from the package's own tag" now "from a ref whose name starts with the package's tag
  prefix" (and the same in the sub-package bullet, which the review did not list); the Pins bullet's key list; #767's
  entry corrected in place (`CHANGELOG_767_OLD`/`_NEW`: it witnesses the files the run built, whose wheel the install
  check installs; no check installs the sdist). The key-pin comments say the republish job takes `timeout-minutes`
  only in all three files at once.
- R4-n NIT (checker): the lag error required verbatim (`LAG_ERROR`), with the package, the version variable and the
  loop's own try count. Juniper-ml's port must therefore also change its error text (its simulation now does).
- Not applied, as dispositioned: R4-1 and R4-5, the ports' own items.

**Rules ADDED beyond the review**, named in the checker's docstring ("added beyond the review"), each a way `bash -e`
lets a failure pass: `&&` outside the flag form's fetch; `!` before a command; `while`/`until`; an `if`/`elif` testing
a command other than the fetch (only a `[ ]` test); `shopt` and `enable`; a backtick anywhere; every pip command after
the fetch a line of its own; the fetch's `--dest` and wheel named only by their assignments, the fetch, `ls -la`, an
`echo`, a `[ ]` test and the later installs (round 4's M11); `TAG_ASSERT` bound to juniper-ml's own packages as well as
the repository.

**Relaxations** (the checker NIT), each with a negative case in `checker_proof_r4.py`: `shell: bash` on an install step
(F8c, now PASS); five `PYTHON*` keys in the build job's env (`BUILD_PYTHON_ENV`); a line exactly `pip --version` or
`pip -V`; `-i` read as `--index-url`; `for <var> in $(seq [1] N); do`; a plain-text `echo` naming pip.

**Results, on both bases** (`e9c86f83` | `802399ab`, identical unless stated):
- tests: 161 passed (`test_publish_one_artifact.py` collects 159, so the CHANGELOG's count and `--changelog-cases`
  stay 159); `--noconftest` 161 passed; the 14 workflow-reader files 433 passed, 8 skipped; the two doc readers 46
  passed, 7 subtests passed;
- the 45-mutation proof: 45 of 45 caught;
- the test-lens harness (r4 copy `test_lens_mutations_r4.py`; C10, a job's own group on the PyPI job, reclassified
  from harmless to property-breaking; C11, `timeout-minutes` alone, and R4a, a group on the build job, added): 83
  edits: 70 of 70 caught, 10 of 10 harmless pass, 3 fail by design (C4, D1, D2); the checker fails 65 of the 70 and 0
  harmless, on both;
- the docs-pin proof 10 of 10; the guard probe caught on both; cascor's 11-15 non-vacuity script 41 of 43 (the same 2
  no longer apply, as in round 3);
- this round's test module against older workflows: 64 of 159 fail on unswept `e9c86f83`, 64 on `802399ab`, 16 on
  round 1's, 1 on round 2's, 0 on round 3's;
- the checker: cascor's 3 PASS on both trees and both clones; `checker_proof_r4.py` 153 of 153 (round 3's 74, five
  overridden: F1b, F1e, F8c, C5, ML1; 77 new; 2 command-line); round 2's 43 cases 43 of 43, every verdict kept (six
  with a new reason: R5, R9, R15, R17, R18, R27);
- the port simulations: 15 of 15 pass (12 faithful, 2 reordered, juniper-ml's `publish.yml` with the F2 edits and,
  new, the template's lag error); the generated simulations equal round 3's;
- bypass mutants: round 4's 15 (M1-M15) all FAIL, round 2's 7 all FAIL (0 of 7 pass), and 14 new ones (N1-N14,
  `new_mutants_r4.py`) all FAIL; the controls T0, P0 and ML0 PASS;
- the round-2 probes: `suite` 16 of 16 harmless pass, 5 of 5 mutations fail, 4 fail by design (H2d, H2e, H4, H10); the
  round-4 `edits` 2 of 2 harmless pass, 7 of 7 mutations fail, 3 fail by design (E1, E2, E3); `loop-sim` and
  `findspec` output identical to round 3's, paths aside (`evidence/probe_outputs_vs_r3.log`);
- cascor pre-commit (11 files): every hook passed, none changed a file; actionlint clean (the unswept bases keep their
  one SC2086 info); B914 0 sites (test modules, writer, checker); symbol loss 0 unwaived; docs screen 0 blocking; the
  markdown-structure delta 0 -> 0 on the six docs (an unbalanced fence in a copy counts 21); the writer's refusal
  proof OK; memory budget OK (56271 | 56255 of 58189, delta +80);
- juniper-ml pre-commit on the writer and the checker: 11 hooks passed, neither file changed; B914 0 sites.

**Residual risk.**
- The checker refuses listed forms; it cannot prove a script safe. Its docstring names what it cannot see: a command
  that overwrites the interpreter on `PATH`, a glob reaching `--dest`, a file written then run (`./x.sh`,
  `python x.py`), `env`/`xargs` prefixes, `awk`/`perl`/`sed e`, pip by a computed name inside `python -c`; I6 (where
  the version comes from); a build-job step before the build that leaves an extra wheel for `Record SHA256SUMS`.
- Over-strict corners left in place (they refuse, never admit): a trailing `# comment` read as command words;
  `[[ a && b ]]` refused as `&&`.
- From round 3: in an F3-style port, a later dependency install can pull a different version of the target.
- `publish.yml`'s comment "A dispatch runs it only from this package's own tag" keeps the ref-name imprecision R4-n
  fixed in the CHANGELOG; changing it changes a workflow, which this pass may not.

**Fail by design** (not dispositioned): the suite's H2d, H2e, H4, H10; the round-4 `edits` E1 (`timeout-minutes` on
every `publish.yml` job, the republish job among them, which stays identical in all three files), E2 and E3 (a job's own
group, now refused by R4-4); the test lens's C4, D1, D2.

## Round-5 review (report: session `ffffd3`'s subagent "Round-5 adversarial review of fix pass 3", 2026-11-23 22:28Z-23:32Z; brief `tmp/sweep/ROUND5_BRIEF.md`; probes and outputs `tmp/r5review/`)

Verdict: 0 BLOCKER, 1 MAJOR, 5 MINOR, 2 NIT. The MAJOR is in the CHECKER; cascor's tree is sound. On cascor `main`
`36dd6f2d` (after #774 and #776) the writer applies cleanly, the only difference from base B is #776's own CHANGELOG
entry, and every count the PR states holds (161 tests; 45/45; test lens 70/70, 10/10; checker proof 153/153; 433 + 8
skipped; actionlint, pre-commit, B914 clean). All 18 new bypass mutants (R5-1..R5-18) PASS the round-4 checker, and
executing their install scripts changes the outcome; round 3's checker passes 17 of them (it refuses R5-1).

**Orchestrator's decision (ffffd3).** The stopping rule exists so that what LANDS has had a round with no BLOCKER or
MAJOR. Round 5's MAJOR is in the checker, which is juniper-ml tooling that gates the PORTS and is not part of the cascor
PR. The cascor PR therefore lands now, with NIT 8 fixed in the writer and findings 1, 2, 6 and 8 applied to its texts
(the PR body stops describing the checker's coverage). The checker gets fix pass 4 and a round-6 review of its
interdiff BEFORE any port is built against it.

| id | sev | where | finding | disposition |
|---|---|---|---|---|
| R5-F1 | MAJOR | checker `:421-427`, `:736`, `:788`; claims `:89-96` | The plain-echo relaxation reopens a bypass: bash expands an echo's arguments before echo runs, and `${x@P}` (prompt expansion) or `${a[x]}` (arithmetic subscript) runs a command a `${x:=…}` stored (R5-1, R5-2, R5-11). The relaxation's premise ("what it names is printed, never run") is false. | FIX PASS 4 (checker): an echo is plain only if, with simple `$NAME`/`${NAME}` removed, it holds no `$`, backtick or unquoted `{ } [ ] * ?`; add R5-1, R5-2, R5-11 as FAIL cases; correct the docstring. The cascor PR body drops its checker-coverage claims. |
| R5-F2 | MINOR | checker `:217`, `:651-652`, `:212`, `:237`, `:780-789`; claims `:55-57`, `:74-79`, `:97-103` | R4-3's class stays open (R5-3, -4, -8, -9, -14, -15, -16, -17, -18): substitution inside a string or a redirect target, brace/glob command names, `rbash`, `mapfile -C`, `[[ ]]` arithmetic, `-mp""ip`, `${!d}` indirection. The docstring says the class is closed. | FIX PASS 4: prefer the positive allow-list of command names after quote removal (no glob/brace characters), refuse `[[`, `((`/`$((`, `let`, `declare`/`local`, `mapfile`/`readarray`, `printf -v`, `${…@…}`, `${!…}`, and scan every `$(…)` body after quote removal; else list each form under "What this cannot see". |
| R5-F3 | MINOR | checker `:188-190`, `:205-213`, `:712-723` | Exit, trap, `set +`, `PIP_*`, `PATH`, `PYTHON*` rules read raw text; quotes defeat them (R5-5, -6, -7, -10, -12). | FIX PASS 4: test on quote-removed words; `exit` only as `exit 1`; refuse `trap` and `set +…`; match the env patterns against every word and `$(…)` body. |
| R5-F4 | MINOR | checker `:219`, `:861-870`, `:881-883` | `BASH_ENV` in the build job's `env` gets around R4-6's build-job rule (R5-13: a third file in `dist/` before the record). | FIX PASS 4: refuse `BASH_ENV`, `ENV`, `BASHOPTS`, `SHELLOPTS` at every env level. |
| R5-F5 | MINOR | juniper-ml port | The required lag-error text breaks ml's `tests/test_publish_testpypi_verify.py:477` (`assertIn("never served", …)`) once R4-1 retargets the lookups. | PORT item (ml), beside R4-1: line 477 asserts the template's lag-error text. |
| R5-F6 | MINOR | cascor PR body | The body describes base `e9c86f83`; `main` is `36dd6f2d` (#774, #776; #776 changed `CHANGELOG.md`). | LANDING: regenerate the body on the landing-day `main`, name #774 and #776, restate the base and the table's columns. |
| R5-F7 | NIT | checker `:775-777`, `:786-789` | Over-strict: a redirected runtime install (O1, with a false reason) and a standalone `[ -f "${WHEEL}" ]` (O2). | FIX PASS 4: drop redirections before comparing; admit a standalone `[ … ]` or reword. |
| R5-F8 | NIT | cascor CHANGELOG `:307`, `pr_body.md:242`, `commit_message.txt:36` | "a `concurrency` group that never cancels a run": a workflow group still cancels an older PENDING run. | FIXED in the writer (sha256 `c47940ad…`): "without `cancel-in-progress`", which is what the pins admit; the texts follow at landing. Verified on a copy of round 5's `36dd6f2d` tree: 1 of 11 files differs, by that one CHANGELOG line (`tmp/sweep/cascor-r4/r5nit/`). |

Writer after NIT 8: sha256 `c47940add4abcfa6e087c3454d81a00fdb328b3e0e71c36a5aeaf2b0a31c352a` (round 5 reviewed
`3f1d3ead…`, saved as `tmp/sweep/cascor-r4/writer_r4_as_reviewed.py`). Checker unchanged so far: `c826ab87…`, saved as
`tmp/sweep/cascor-r4/checker_r4_as_reviewed.py`. Manifests: `tmp/arc/sweep_scripts.r4.sha256` (round 5's inputs),
`tmp/arc/sweep_scripts.sha256` (current).

## Fix pass 4 (round 5's checker fixes; checker-r5)

The executor reported this: the final message of session `d935c226`'s subagent for fix pass 4 (orchestrator `ffffd3`,
brief `tmp/sweep/FIXPASS4_BRIEF.md`), 2026-11-23 23:45Z to 2026-11-24 00:40Z. The checker only: the writer, cascor's
tree, every workflow file and `tmp/sweep/land/` are untouched. Every driver is in `tmp/sweep/checker-r5/` beside its
evidence (`evidence/`); `rerun_all.bash` re-runs steps 1 to 4 (its output `evidence/rerun_all.out`), `run_proof43.bash`
step 5, `lint_checker.bash` step 6. The template for every run is the landing tree's
`tmp/sweep/cascor-r4/main/juniper-cascor/.github/workflows/publish.yml` (base B), but round 2's seven mutants (below).

**Versions.**
- Checker: `c826ab875ecb5d6ad95891e341fb3b27020cfddf25d0161a4a44e04c74f88236` (as round 5 reviewed it:
  `tmp/sweep/cascor-r4/checker_r4_as_reviewed.py`) -> `ebeb75562d61c43e071a77855a10c92841d5967addb2d4c60f9723f92e9207b8`,
  1043 -> 1623 lines; frozen as `tmp/sweep/checker-r5/checker_r5_as_delivered.py`.
- Interdiff: `tmp/sweep/checker-r5/checker_r4_to_r5.diff`, 785 lines, +591/-46, sha256 `bc14fa9f…`. Most of it is one
  new block (the lexer, `structure`, `command_shape`, `check_allowlist`, `line_problems`) and the docstring.
- Manifest: round 5's kept as `tmp/arc/sweep_scripts.r5nit.sha256`; `tmp/arc/sweep_scripts.sha256` regenerated over the
  same six paths: only the checker's line changes, the writer's stays `c47940ad…`; `sha256sum -c` passes
  (`evidence/manifest.log`).

**The approach.** A positive allow-list in place of more deny rules, derived from what the template and the 15 port
simulations run (`evidence/inventory_ports.out`, `evidence/build_job_keys.out`), never from a mutant. The checker now
lexes each install-script command as bash does (quote removal, every `$` form, each `$(...)` body, redirections,
reserved words, comments: `lex`, `structure`) and refuses what the ports never use. The deny rules stay, as a second
line and for their messages.

**Applied.**
- R5-F1 (MAJOR): `plain_echo` is true only for an echo with no redirection or second command whose words, simple
  `$NAME`/`${NAME}` aside, hold no `$`, backtick or unquoted `{ } [ ] * ?`; the loop's echo must be plain too. The
  docstring's claim ("what it names is printed, never run") is corrected in place, with R5-1, R5-2 and R5-11 named.
  Belt and braces: every non-simple `$` form is refused anywhere (R5-F2).
- R5-F2: the allow-list, by the name bash runs after quote removal, with no `$`, backtick, glob or brace character in
  it: `TOP_COMMANDS` (`cd set sleep echo pip python python3 ls [ break exit`), `CONSOLE_SCRIPTS`
  (juniper-doc-tools' `juniper-check-doc-links`), and in a `$(...)` body `SUBST_COMMANDS`
  (`python python3 grep head sed mktemp seq`, piped and nothing else). Each in the ports' shapes (`command_shape`).
  Reserved words: `if then elif else fi for do done { }` alone (`[[`, `case`, `select`, `time`, `coproc`, `while`,
  `until`, `!`, `function` refused); no `( )` (so no subshell and no `(( ))`). `$` forms: `$NAME`, `${NAME}`,
  `${NAME#<literal>}` and `$(...)` alone (`$((`, `$[`, `${!`, `${…@…}`, `${a[…]}`, `${x:…}`, `${x:=…}`, `$'…'`, `$"…"`,
  `$?` and the rest refused). No unquoted glob or brace character but `[ ] { }` standing alone. Every `$(...)` body is
  checked by the same rules and scanned for pip after quote removal. `let`, `declare`, `local`, `mapfile`, `readarray`
  and `printf` are refused as unlisted names. The docstring no longer says the deny rules close the class; it says the
  allow-list does, and lists round 5's nine forms against the deny rules.
- R5-F3: `exit` only as `exit 1`, `set` only with `-e`, `-u`, `-o pipefail`, `cd` only as the first line, each judged
  by the name bash runs; `trap` is not admitted; the `PIP_*`, `UV_*`, `PYTHON*`, `PATH`, `GITHUB_ENV`/`GITHUB_PATH`,
  `pip.conf`, alias and `-m pip` refusals read the quote-removed text of every command and every body as well as the
  raw text (`unquoted_texts`).
- R5-F4: `BASH_ENV`, `ENV`, `BASHOPTS` and `SHELLOPTS` refused as env keys at every level (`SHELL_ENV`).
- R5-F7 (NIT): O1, a later pip line's redirections set aside before the line-of-its-own comparison (`own_line`); O2, a
  standalone `[ ... ]` (no substitution, no redirection) may name the `--dest` or the wheel (`test_only`). Round 5's O1
  and O2 now pass; O3 still passes (`evidence/overstrict.log`).

**Rules ADDED beyond the review**, each named in the docstring with a FAIL and a PASS case in `checker_proof_r5.py`;
each of the first eleven closes a bypass of the round-4 checker this pass EXECUTED (N5-1 to N5-16, below):
- `set` beyond `-e`, `-u`, `-o pipefail`: `set -n` and `set -t` end the script with status 0 before the import
  (N5-1, N5-2); `set -x` expands `PS4`;
- `[ ]` operators beyond `! -f -d -e -s -n -z -eq -ne -lt -le -gt -ge = !=`: `[ -v 'a[$(cmd)]' ]` runs cmd (N5-3);
  `[ x -eq y ]` does not evaluate arithmetic (`evidence/bash_semantics_probe_r5.out`);
- redirections: output only, onto `&1`/`&2`, `/dev/null` or `${RUNNER_TEMP}/<name>.log|.txt`; no input redirection or
  here-document: an echo wrote `juniper_cascor.py` into `$RUNNER_TEMP` and a real `python -c` import passed with
  nothing installed (N5-4);
- `${NAME#<literal>}` alone: `${RELEASE_TAG#$(cmd)}` runs cmd (N5-5);
- `cd` judged after quote removal: `"c"d` into a widened checkout imported the checkout's source (N5-6);
- shapes for `sed` (`[-E] 's/…/…/'`, no flags: the `e` flag ran a PyPI install, N5-7), `grep`, `head`, `mktemp -d`,
  `seq`, `sleep`, `break`, `python` (`-c <code>`, or `-m <its own module> --opts`), the console script;
- the build job's own `env` (and its container's) holds `BUILD_PYTHON_ENV` keys alone: `PATH` (N5-8),
  `BASH_FUNC_twine%%` (N5-9) and `SHELLOPTS: xtrace` with `PS4` (N5-10) each put a third wheel in `dist/` before
  `Record SHA256SUMS`;
- an env key that is not a shell identifier, or starts `BASH_FUNC_`, refused at every level; an `env` that is not a
  mapping refused;
- `line_problems`, found against this pass's own first draft (`checker_r5_draft1.py`, sha256 `af11f945…`, which N5-11
  to N5-14 pass: `evidence/new_mutants_draft1.out`): a continuation into a blank or comment line (bash ends the command
  there and runs the next line alone: `echo … \` then `# note` then `"exit" 0` exits 0, N5-11, N5-14), a line ending
  in an even run of backslashes (N5-13) or in a backslash and then whitespace, and a line break other than `\n`
  (`commands()` splits on `str.splitlines()`'s set; bash on `\n` alone); and `$[expr]`, the deprecated arithmetic
  expansion (N5-12);
- a backtick substitution in any word at any depth (`skeleton()` hides a `$(...)` body, so round 4's backtick rule
  never saw one there: N5-15), and assigned names: lowercase, or the ports' own `VERSION`, `DOWNLOAD_DIR`, `FETCHED`,
  `WHEEL` (`ASSIGNABLE`), since an uppercase name may be one the runner exports (N5-16: `HOME` set to a checkout widened
  to `.config/pip/` made pip read a committed `pip.conf`; a real `pip config list` shows `extra-index-url` in effect).
  Both found against the second draft (not saved; reconstructed from the delivered checker by
  `reconstruct_draft2.py`, sha256 `d2a060de…`: N5-15 and N5-16 pass it, N5-1 to N5-14 fail it,
  `evidence/new_mutants_draft2.out`);
- the install job's checkout: a sparse checkout of one `pyproject.toml` or `_version.py` (`SPARSE_PATH`), in cone mode,
  with `persist-credentials: false` and no other input (N5-16's other half, and N5-6's precondition);
- the build job on `ubuntu-latest`, with no `container` or `services` (each would choose what the window steps'
  `twine` is: R5-13's class); no admitted case needed them (every port's build job holds none);
- an inline comment after a command (inside `$( )` a `#` hides where the substitution ends:
  `evidence/bash_semantics_probe_r5.out`).

**Relaxed:** R5-F7's two (O1, O2) only. **Narrowed:** the plain echo (R5-F1).

**Results** (`evidence/rerun_all.out` unless named):
- cascor's three publishers: 3 of 3 PASS (`evidence/checks_cascor.log`);
- the 15 port simulations: 15 of 15 PASS under the new checker and the reviewed one (`evidence/port_sim_table.md`); the
  regenerated simulations equal fix pass 3's byte for byte (0 diff lines), and the generator's 25 variants keep fix
  pass 3's verdicts (19 PASS, 6 FAIL, as before: juniper-ml's `publish.yml` before its F2 edits, two variants, now with
  more reasons for its `set +e` block; and config-tools' and doc-tools' `faithful` variants, two each, whose
  `python -c` is not last, hence their `reorder` rows in the table);
- round 5's R5-1 to R5-18: 18 of 18 FAIL, each for its class's reason; controls T0, ML0, S3, S4 PASS; S1, S2 FAIL
  (`evidence/judge_mutants.md`);
- round 4's M1 to M15: 15 of 15 FAIL, as round 4 wrote them (`tmp/r4review/mutants/`; there T0 and P0 PASS and ML0
  FAILS on juniper-ml's old lag error, which those files predate, as under the reviewed checker) and regenerated by
  round 4's own driver on these simulations (T0, P0, ML0 PASS; `evidence/r4review_mutants.txt`);
- round 2's 7: 7 of 7 FAIL against round 2's own template (`tmp/sweep/cascor-r2/work-main`), as fix pass 3 and round 5
  ran them (built on it, they would fail the landing template vacuously); its control PASSES;
- fix pass 3's N1 to N14: 14 of 14 FAIL, as written and regenerated (`evidence/new_mutants_r4_rerun.txt`, 0
  unexpected); controls PASS;
- this pass's 16 new mutants (`new_mutants_r5.py`, `evidence/new_mutants_r5.out`): each PASSES the reviewed checker
  and FAILS the new one, and each is executed (round 5's stand-ins under `bash -e`, a real `python3` where the import's
  outcome is the point, the window step with the build job's env) and changes the outcome: rc 0 with the import
  failing (N5-1, N5-2, N5-11, N5-13, N5-14); a hidden PyPI install runs (N5-3, N5-5, N5-7, N5-12, N5-15); a real import
  passes with nothing installed (N5-4, N5-6); a third wheel in `dist/` before the record (N5-8, N5-9, N5-10); pip runs
  with a committed `pip.conf` in effect (N5-16). Controls T0, T0r, CN0p, P0, W0 PASS both; CN0r, N5-6's execution
  baseline, holds the widened checkout the new checkout rule refuses;
- the checker proof `checker_proof_r5.py`: 261 of 261 (round 3's 74, five overridden as before; fix pass 3's 77, two
  overridden with their reasons: R42e's control piped `printf` into `wc` inside `$(...)`, kept with the ports' own
  `grep | head | sed`, its old line now the FAIL case R42e5; R43v's control assigned an uppercase `NOTE`, kept with a
  lowercase name, its old lines now the FAIL case B5aj; 108 new; 2 command-line) (`evidence/checker_proof_r5.log`);
  fix pass 3's proof run unchanged against the new checker: 152 of 153, R42e alone moving
  (`evidence/checker_proof_r4_on_live.log`);
- round 2's 43 cases: 43 of 43, every verdict kept; K12, R12, R13, R14, R16, R17, R18 and R19 gain reasons
  (`evidence/checker_proof43.log`);
- pre-commit (juniper-ml's config, `--files`): 11 passed, 0 failed, the file unchanged; B914 0 sites; `--help` exit 0;
  flake8 at 512 columns 0 findings; Black at 512 would re-quote two f-strings in `check_fetch` that the reviewed copy
  holds too (not this pass's lines; left).

**Residual risk** (the docstring's "What this cannot see", rewritten):
- Python is not parsed: `python -c` code can run anything (pip by any name, a file it wrote, a glob reaching the
  `--dest`), and `python -m <own module>` and the console script run the package's code (as intended).
- A later `pip install` of another package from PyPI (F3 admits any plain requirement) runs that package's code: its
  build, a `.pth` file its wheel installs (run at every Python start, the check's included), its import.
- setup-python's inputs (`cache`) and every action's `@ref` (item 23 drops it) are not judged.
- A lowercase variable the runner exports (a proxy setting) may be reassigned.
- The checker reads one workflow: what a repository commits beside it (the file a one-path sparse checkout brings, with,
  in cone mode, each parent directory's own files) is not read.
- I6 (where the version comes from), what the `python -c` check asserts, and the build job's steps up to and including
  the build, as before.
- The lexer approximates bash's; every divergence found (four, in `line_problems`, `$[`, and `#` inside `$( )`) is
  refused, but others may remain. The bash semantics relied on were probed on bash 5.3.9 (the runner's ubuntu-latest
  ships 5.2): `[ -eq ]` evaluating no arithmetic is the one safety this pass relies on rather than refuses.
- Over-strict corners (each refuses, never admits; none hits a port): a trailing `# comment`; a one-argument `[ x ]`;
  a continuation on a script's last line; `head` with a file argument; an uppercase variable a port might name beyond
  the four.

## Landed: juniper-cascor#777 (session `ffffd3`, 2026-11-24)

- **Landing prep** (brief `tmp/sweep/LAND_BRIEF.md`, everything under `tmp/sweep/land/`): fresh clones of cascor `main`
  `36dd6f2d` (#776, after #774), the writer `c47940ad…` with `--date 2026-11-23`, the account against base B (31 files
  differ: 27 are #774's, 4 are #776's, none unexplained), and every check on the landing tree: 161 tests; 433 passed +
  8 skipped; mutation proof 45/45; test lens 70/70, 10/10, C4/D1/D2 by design; the frozen checker copy 3/3 PASS;
  actionlint, pre-commit, B914 (0), symbol loss (1 finding, waived by the trailer), docs screen, markdown-structure
  delta, memory budget. The gate's one finding, `AGENTS.md:148` (`JUNIPER_CASCOR_API_KEYS`, default `None`, identical
  on `main`, not an added line), was accepted as not a credential, checked by the orchestrator.
- **Opened** 2026-11-24 ~00:30Z as one signed commit `a12b2c5f` on `36dd6f2d`; readback 11/11 same.
- **Fix-up commit** `74971d3a`: `Verify AGENTS.md Last Updated` (not required) failed because the commit landed after
  midnight UTC dated 2026-11-23. The writer re-run on `36dd6f2d` with `--date 2026-11-24` moves exactly three date lines
  (AGENTS.md and REFERENCE.md `**Last Updated**`, the cheatsheet's `**Date**`); 161 tests and pre-commit pass on that
  tree; gate PASS (`tmp/sweep/land/date24/`). So the landed tree = the writer `c47940ad…` with `--date 2026-11-24` on
  `36dd6f2d`.
- **CI**: 25/25 required success on both heads (`evidence/wait_checks_777*.log`).
- **MERGED** 2026-11-24 00:56:52Z by `util/safe_merge.py` ("MERGED #777 at 74971d3a via squash"): `f5ed3017`, parent
  `36dd6f2d`, signature verified, 11 files. The squash message (COMMIT_MESSAGES) holds both commits, the
  `Allow-Symbol-Loss:` line among them.
- **After**: `tmp/ports/verify_all_mains_v2.bash` (the fix-pass-4 checker `ebeb7556…`, under round-6 review) prints
  `3 of 18 pass`: cascor's three PASS against `main`'s merged template; the 15 ports fail until ported
  (`tmp/ports/verify_all_mains_v2.after777.log`).

## Round-6 review (report: `tmp/r6review/ROUND6_REPORT.md`; session `ffffd3`'s subagent "Round-6 adversarial review of the checker", finished 2026-11-24 ~01:20Z; brief `tmp/sweep/ROUND6_BRIEF.md`)

Verdict: 1 BLOCKER, 0 MINOR, 2 NIT, against the checker `ebeb7556…` (fix pass 4). The stopping rule applies: fix pass 5
on the checker, then round 7, before any port is built. Over-strictness: no finding against a real port (15 of 15 PASS;
every harmless edit passes except OS11, NIT 1).

| id | sev | where | finding | disposition |
|---|---|---|---|---|
| R6-F1 | BLOCKER | checker `commands()` `:416-431` (join at `:425`), `line_problems` `:677-702`, carriers `plain_echo` `:934-946` and the raw-pip exclusion `:1293`; claims `:83`, `:114`; "What this cannot see" `:174-186` | A line continuation is joined with a SPACE where bash DELETES `\<newline>`: `echo "… $\` + newline + `(pip install … pypi.org … juniper-cascor==0.14.0)"` reads to the checker as a literal `$ (`, so the echo counts as plain, while bash runs the `$(…)`. Six executed mutants PASS (R6-1..R6-6): hidden PyPI installs, a spoofed import (R6-2), round 5's R5-1 behind a continuation (R6-3), the retry-loop path (R6-4), and a NUL byte, which bash drops, in two forms (R6-5, R6-6; lower confidence, a strict YAML parser may reject NUL). The docstring claims the allow-list "closes the class"; false. | FIX PASS 5: refuse a continuation unless the backslash is preceded by whitespace (all 66 continuation backslashes in the template and the 15 ports are, and none abut on both sides: `tmp/r6review/check_continuations.out`), or reconcile bash's join with `commands()`'s and refuse when they tokenize differently; refuse a NUL byte anywhere in a run script; correct `:83`, `:114`, and name shell-lexing divergence under "What this cannot see". R6-1..R6-6 must FAIL. |
| R6-N1 | NIT | checker | A trailing inline `# comment` on a command is refused (OS11); no port uses one. | Fix pass 5 may admit it (strip a trailing unquoted `#…` outside `$( )`), else leave and document. |
| R6-N2 | NIT | checker `PREFIX_REMOVAL` `:184` | `${NAME##literal}` / `${NAME%…}` refused; only a single `#` admitted; no port uses them. | Leave (cosmetic), or admit with proof cases. |

**Sound (round 6):** 3/3 cascor; 15/15 port simulations, byte-identical to fix passes 3 and 4; every earlier mutant
FAILs and every control PASSes (R5 24/24, M 18/18, round 2 8/8, N 17/17); fix pass 4's N5-1..N5-16 each PASS the
reviewed checker and FAIL the live one; `checker_proof_r5.py` 261/261; round 2's 43/43; pre-commit unchanged; B914 0.

## Fix pass 5 (round 6's checker fixes; checker-r6)

The executor reported this: the final message of session `d935c226`'s subagent for fix pass 5 (orchestrator `ffffd3`,
brief `tmp/sweep/FIXPASS5_BRIEF.md`), 2026-11-24 01:18Z to 02:08Z. The checker only: the writer, cascor's tree, every
workflow file, every port, `tmp/sweep/land/` and every earlier review directory are untouched. Every driver is in
`tmp/sweep/checker-r6/` beside its evidence (`evidence/`): `rerun_all.bash` re-runs steps 1 to 4 (its output
`evidence/rerun_all.out`; the first full run, on an interim hash with the same code and an older docstring, is kept as
`evidence/rerun_all.ced77ca8.out`), `lint_checker.bash` step 5. The template for every run is the landing tree's
`tmp/sweep/cascor-r4/main/juniper-cascor/.github/workflows/publish.yml` (base B), but round 2's seven mutants.

**Versions.**
- Checker: `ebeb75562d61c43e071a77855a10c92841d5967addb2d4c60f9723f92e9207b8` (as round 6 reviewed it, saved before any
  edit as `tmp/sweep/checker-r6/checker_r5_as_reviewed.py`) -> `6b2443c6d24ee7692e606d0b010526f113aaf0070d9b7a5dd35597dd94d11f85`,
  1623 -> 1704 lines; frozen as `tmp/sweep/checker-r6/checker_r6_as_delivered.py`.
- Interdiff: `tmp/sweep/checker-r6/checker_r5_to_r6.diff`, 155 lines, +86/-5, sha256
  `6f629f0492231d55be8db947bdf953d5c50ac519fbe36ba71272cfbac19ce43c` (`evidence/interdiff.log`). About 19 executable
  lines: one constant (`NUL`), five in `line_problems` for NUL and the other characters, nine there for continuations
  (one condition rewritten), three in `check()` running `line_problems` at the build window. The rest is the docstring
  and comments. `commands()`, the lexer, every allow-list entry and every deny rule are unchanged.
- Manifest: round 6's kept as `tmp/arc/sweep_scripts.r6.sha256` (copied before any edit); `tmp/arc/sweep_scripts.sha256`
  regenerated over the same six paths (sha256 `3c5cfb089087318f16c95bb50fbae27f28b31afe7d1b099e652c1d97c7195ceb`): only the
  checker's line changes, the writer's stays `c47940ad…`; `sha256sum -c` passes (`evidence/manifest.log`).
- juniper-cascor `main` is `f5ed3017` (#777); its three publishers, fetched read-only at 2026-11-24 01:31Z through
  `util/ad-hoc/2026-11-15_fetch_pr_files.py` into `tmp/sweep/checker-r6/cascor-main-fetch/`, are byte-identical to the
  landing tree's (`evidence/fetch_cascor_main.log`).

**The approach.** The smallest change that refuses every line `commands()` reads otherwise than bash, wherever
`commands()` reads a script before it is judged: more rules in `line_problems`, and `line_problems` run at the build
window as well as in the install steps. Derived from what the template and the 15 simulations hold
(`evidence/inventory_continuations.out`: 251 runs; 66 continuation backslashes, every one with a space before it, none
escaped, none with a tab, every one followed by an indented line; no character outside printable text, space, tab and
newline), and checked against bash 5.3.9 (`evidence/bash_semantics_probe_r6.out`, 18 cases, each beside the reviewed
checker's reading: a comment line ending in a backslash does not continue; a trailing comment ending in one does not
either; a backslash at the end of a script with no newline after it is passed on as an argument; a tab before the
backslash separates as a space does; an escaped space before it gives two words where `commands()` gives one; inside
single quotes bash keeps the backslash and newline; a no-break space is part of a word).

**Applied.**
- R6-F1 (BLOCKER), the join: a continuation is refused unless a space or tab precedes its backslash and that blank is
  not itself escaped (an odd run of backslashes before it). With an unescaped blank there, each join is a run of blanks
  in both readings: a separator outside quotes, and text inside them, where only the run's length differs (inside
  single quotes bash also keeps the backslash and newline). R6-1 to R6-4 FAIL on it.
- R6-F1, NUL: a NUL anywhere in an install or window script is refused, with the reason (bash drops it, so `$<NUL>(` is a
  substitution to bash and a literal `$` to the lexer). R6-5 and R6-6 FAIL on it.
- R6-F1, the claims: `:83` now says the allow-list judges R4-3's class "only as far as this checker reads a script as bash
  does", and `:114` that a place where `commands()`'s and the lexer's reading differs from bash's reopens the class. The
  fix pass 5 bullet names every rule and every place checked: `commands()` (install steps and window), `line_problems`,
  the lexer and every `$(...)` body, `plain_echo`, the retry loop, `check_fetch`'s quoting counts, `shell_words`,
  `skeleton`/`operators`, the raw pip count, `unquoted_texts` and the deny rules, the window's allow-list, `bash -n`, and
  the template steps and republish job (YAML-equal to the template's). "What this cannot see" now names the shell-lexing
  divergence: any reading that differs from bash's and is not yet refused; the two admitted as inert; and that the pip
  rules read pip's words with `shell_words` (`shlex`), which models no `$(...)`, while the allow-list reads them with
  `lex`.
- R6-N1 (NIT): LEFT REFUSED, documented in the docstring. Admitting a trailing comment would need every raw-text reading
  (the deny rules, the raw pip count, the loop's and the fetch's exact strings, the python -c end rule) to drop it
  first, and bash does not continue a line whose comment ends in a backslash (probe case 2), so a comment there would
  hide the next line from this checker: N6-10, executed, runs a hidden PyPI install exactly so. No port has one.
- R6-N2 (NIT): LEFT REFUSED, documented: `${NAME##...}`, `${NAME%...}`, `${NAME%%...}`. No port uses them, and the
  allow-list holds what the ports run (proof cases X6a, X6b).

**Rules ADDED beyond the review**, each in the docstring with FAIL and PASS cases in `checker_proof_r6.py`:
- every character but printable text, a tab and a newline (the line breaks keep their own message): `commands()` strips
  a no-break space, or another space Python's `str.strip()` knows, from a line's ends where bash reads it as part of a
  word, and a control or format character hides text from the review that reads the script;
- a continuation on a script's last line with no newline after it (bash passes the backslash on as an argument). With a
  newline after it, it was already refused, as a continuation into a blank line;
- the escaped blank (above);
- `line_problems` at the build window, every step between the build and `Record SHA256SUMS`: a NEW FINDING of this pass,
  R6-F1's class at a site round 6 did not test. `commands()` skips a comment line even inside a continuation, so
  `twine check dist/*\` then `# || cp stash/*.whl dist/` read as the allowed `twine check dist/*`, while bash ran
  `twine check 'dist/*#'` (real twine 6.2.0 exits 1 on it: `evidence/twine_missing_file_probe.out`) and then the `cp`.
  Executed (N6-8, and N6-9 with a no-break space before the `#`): a third wheel in `dist/` before the record. Both PASS
  the checker as round 6 reviewed it.

**Relaxed:** nothing. **Narrowed:** nothing. Every change refuses; none admits.

**Results** (`evidence/rerun_all.out` unless named):
- cascor's three publishers: 3 of 3 PASS from the landing tree, and 3 of 3 from `main` as fetched
  (`evidence/checks_cascor.log`);
- the 15 port simulations: 15 of 15 PASS under the new checker and the reviewed one (`evidence/port_sim_table.md`);
  regenerated by round 2's probes, they equal fix pass 4's byte for byte (0 diff lines); the generator's 25 variants
  keep 19 PASS / 6 FAIL;
- round 6's R6-1..R6-6, rebuilt by round 6's own code and executed (`r6_mutants_rerun.py`,
  `evidence/r6_mutants_rerun.out`): each PASSES the reviewed checker and FAILS the new one; executed, each still changes
  the outcome (hidden PyPI installs, R6-4's on the lag path; R6-2's real import exits 0 with nothing installed);
  controls T0, T0r, P0, ML0 PASS both. As round 6 wrote them (`judge_mutants_r6.py`, set r6): 10 of 10 as expected;
- fix pass 4's N5-1..N5-16 (`new_mutants_r5_copy.py`, `evidence/new_mutants_r5.out`): each PASSES the checker they were
  built against (`c826ab87`) and FAILS the new one, every one executed; controls PASS; CN0r FAILS (by design). As fix
  pass 4 wrote them (set fp4): 22 of 22;
- round 5's R5-1..R5-18 and controls 24 of 24; round 4's M1..M15 and controls 18 of 18 as written, and regenerated by
  round 4's driver (M1-M15 FAIL, T0, P0, ML0 PASS); round 2's 7 and control 8 of 8 against round 2's own template; fix
  pass 3's N1..N14 and controls 17 of 17 as written, and regenerated (0 unexpected). `judge_mutants_r6.py`: 0
  mismatches across all six sets (`evidence/judge_mutants.md`);
- this pass's mutants (`new_mutants_r6.py`, `evidence/new_mutants_r6.out`), 13 plus 5 controls, every one executed:
  - bypasses of the reviewed checker that FAIL the new one: N6-4 (a `$\` continuation inside a `$(...)` body: a hidden
    PyPI install ran), N6-7 (a NUL there: the same), N6-8 and N6-9 (the window: a third wheel in `dist/`);
  - refused as the class, executing them changes nothing material: N6-2 (`\\` before the continuation), N6-3 (inside
    single quotes), N6-5 (a continuation at the end of the script; python gets a `\` argument), N6-11 (an escaped space
    before the backslash), N6-13 (a no-break space ending a later install's line; pip is asked for a requirement with
    it);
  - PASS, because executing them changes nothing: N6-1 and N6-12 (R6-1 and R6-4 with a tab between `$` and the
    backslash: to bash `$` then a tab is a literal `$`, and no PyPI install runs);
  - regression guards that FAIL both: N6-6 (a CRLF: executed, `exit 0` runs before the import), N6-10 (a trailing
    comment ending in a backslash: executed, a hidden PyPI install runs; the comment rule refuses it, hence R6-N1 stays
    refused);
  - controls T0, T0r, P0, W0, C6-1 (a spaced continuation inside a `$(...)`) PASS both; 0 verdicts other than
    expected;
- over-strictness: round 5's O1-O3 and round 6's OS1-OS12 as their builders wrote them: all PASS but OS11 (a trailing
  inline comment, R6-N1), as under the reviewed checker (`evidence/overstrict.log`);
- the checker proof `checker_proof_r6.py`: 289 of 289 (round 3's 74, five overridden as before; fix pass 3's 77, two
  overridden as before; fix pass 4's 108, none overridden; 28 new; 2 command-line) (`evidence/checker_proof_r6.log`).
  Fix pass 4's `checker_proof_r5.py`, unchanged, on the new checker: 261 of 261, no verdict moved
  (`evidence/checker_proof_r5_on_live.log`). `checker_proof_r6.py` on the reviewed checker: 274 of 289, the 15
  mismatches exactly the new FAIL cases that need fix pass 5 (J6a, J6d, J6f, J6g, J6i, J6j, J6k, N6a-N6d, W6a, W6b,
  W6e, W6f) (`evidence/checker_proof_r6_on_reviewed.log`);
- round 2's 43 cases: 43 of 43, every verdict kept against fix pass 3's log and fix pass 4's (no reason reworded since
  fix pass 4) (`evidence/checker_proof43.log`);
- pre-commit (juniper-ml's config, `--files`): 11 passed, 0 failed, 15 skipped, the file unchanged; B914 0 sites;
  `--help` exit 0; flake8 `--isolated` at 512 columns: 12 E203 (Black's slice spacing), the same 12 as the reviewed
  copy, none on a changed line (`evidence/precommit_checker.log`, `b914_checker.log`, `flake8_checker.log`).

**Residual risk** (the docstring's "What this cannot see", as rewritten):
- The checker reads a script with `commands()` and `lex`, not with bash. Every divergence found so far is refused
  (fix pass 4's four; round 6's join and NUL; this pass's escaped blank, last-line backslash, Python's spaces and the
  window), but others may remain.
- Two differences are admitted as inert text: the blank run's length at a continuation inside quotes, and the
  backslash and newline bash keeps inside single quotes.
- The pip rules (F2-F4), the loop's and the import check's comparisons and the second-line deny rules read words with
  `shell_words` (`shlex`), which models no `$(...)`, while the allow-list reads with `lex`; where the two readings of a
  command differ, pip's arguments are judged as `shlex` reads them. A probe of that difference
  (`tmp/sweep/checker-r6/shlex_probe.py`, `evidence/shlex_probe.out`) found a command on which `lex` and `pip_calls`
  disagree about a pip command and which both checkers PASS; executed under `bash -e` it fails the step (rc 1) and runs
  no hidden install, so no bypass was shown. This pass made no change there (out of the brief's scope, and untested
  code is what rounds 4 to 6 kept finding weakest); round 7 is asked to examine it.
- Unchanged from fix pass 4: Python is not parsed; a later `pip install` of another PyPI package runs its code;
  setup-python's inputs and every action's `@ref` are not judged; a lowercase variable the runner exports may be
  reassigned; files a sparse checkout brings are not read; I6, the `python -c` assertion and the build job's steps up to
  the build are each repository's own business. juniper-ml's admitted tag assert pastes `${{ github.ref }}` into its
  window script (by design, R4-6).
- Over-strict corners (each refuses, never admits; none hits a port): a trailing `# comment`; `${NAME##...}` and
  `${NAME%...}`; a one-argument `[ x ]`; `head` with a file argument; an uppercase variable a port might name beyond the
  four; and, from this pass, a continuation with no blank before its backslash where bash reads it harmlessly (inside
  single quotes, or after an escaped backslash pair: N6-3, N6-2), a blank after a backslash before the continuation
  even inside quotes, a line that is a bare backslash, and a continuation on a script's last line.

**Next:** round 7 (`tmp/sweep/ROUND7_BRIEF.md`), on this interdiff, before any port is built against the checker.

## Round-7 review (report: `tmp/r7review/ROUND7_REPORT.md`; session `ffffd3`'s subagent, finished 2026-11-24 ~02:55Z; brief `tmp/sweep/ROUND7_BRIEF.md`) -- INCOMPLETE

Verdict: 0 BLOCKER, 0 MAJOR, 1 MINOR, 4 NIT against the checker `6b2443c6…` (fix pass 5), **but the round is INCOMPLETE
and does NOT clear the checker for ports.** The reviewer reports that a safety interruption stopped its step 4 (no new
executed mutants were built), the bypass hunt for new reader divergences in steps 1-2, and the executed side of the
two-readers question; earlier mutants were re-judged by verdict only, not re-executed. Everything it did run matches the
"Fix pass 5" section: 3/3 cascor (landing tree and `main`, byte-identical), 15/15 simulations (regenerated byte-identical),
`checker_proof_r6.py` 289/289, `checker_proof_r5.py` 261/261, round 2's 43/43, every earlier mutant set by verdict, 66
continuations all blank-preceded, 30 of 32 harmless edits admitted (the 2 refusals predate fix pass 5).

**Orchestrator's decision (ffffd3):** the stopping rule needs a COMPLETE round with no BLOCKER/MAJOR. Next: fix pass 6
(R7-1 and the NITs, brief `tmp/sweep/FIXPASS6_BRIEF.md`), then round 8 with the full executed-mutant step. If round 8's
mutant step is interrupted again, stop and ask the owner whether the static rounds suffice; do not start the ports
without a complete round or that ruling.

| id | sev | where | finding | disposition |
|---|---|---|---|---|
| R7-1 | MINOR (static) | checker `:361`, `:876-877`, `:923`; `pip_calls` `:492-497`, `:1048-1055`, `:1356-1365`, `:1404-1409` | The allow-list admits `pip` by name and leaves its arguments to F2-F4, which judge only what `pip_calls` (read with `shlex`) finds; `lex` and `shlex` can disagree, so a pip command F2-F4 never see passes (fix pass 5's `checker-r6/shlex-probe/S1.yml` PASSES; fed the `lex` words, F3 refuses them). Predates fix pass 5. Fix pass 5 executed S1 and the step failed with nothing hidden run; an outcome change would make it MAJOR. | FIX PASS 6: in `check_install_job`, refuse any command on which the two readers disagree about its pip commands (0 disagreements across the template and the 15 simulations: 259 install commands, 21 pip commands). |
| R7-2 | NIT | checker `:772-773` | The escaped-blank rule refuses `x\ \` + an UNINDENTED line, where bash and the checker read the same word; its message ("ends the word at the next line's indentation") is false there. | FIX PASS 6: refuse only when the next line starts with a blank, or reword. |
| R7-3 | NIT | checker `:768-769` | A last line ending `cmd \` + newline reads the same to both; refused with "runs the next line alone" though there is none. | FIX PASS 6: admit, or give it a true message. |
| R7-4 | NIT | `check_loop` `:1216-1218` | A fetch whose output goes to `${RUNNER_TEMP}/fetch.log` is refused with a false reason: the comparison keeps the redirection on one side only. | FIX PASS 6: set redirections aside before comparing (with a FAIL case for a redirection that changes the outcome). |
| R7-5 | NIT | docstring `:206-207` | "compared as YAML text": they are compared as parsed YAML (`:1625-1644`). | FIX PASS 6: reword. |

## Fix pass 6 (round 7's checker fixes; checker-r7)

The executor reported this: the final message of session `d935c226`'s subagent for fix pass 6 (orchestrator `ffffd3`,
brief `tmp/sweep/FIXPASS6_BRIEF.md`), 2026-11-24 02:32Z to ~03:15Z (times from `date -u`). The checker only: the writer,
cascor's tree, every workflow file, every port, `tmp/sweep/land/` and every earlier review directory are untouched.
Every driver is in `tmp/sweep/checker-r7/` beside its evidence (`evidence/`): `rerun_all.bash` re-runs steps 1 to 4 (its
output `evidence/rerun_all.out`, 03:01:28Z to 03:07:20Z), `lint_checker.bash` step 5. Each driver is a copy of fix pass
5's, adapted by exact replacements (most by `make_driver_copies.py`; each copy's header names its source and what
changed), or new (`two_readers_probe_r7.py`, `two_readers_inventory_r7.py`, `new_mutants_r7.py`, `make_minus_r71.py`).
The template for every run is the landing tree's `tmp/sweep/cascor-r4/main/juniper-cascor/.github/workflows/publish.yml`
(base B), but round 2's seven mutants. The mutants below are negative test cases for this CI checker.

**Versions.**
- Checker: `6b2443c6d24ee7692e606d0b010526f113aaf0070d9b7a5dd35597dd94d11f85` (as round 7 reviewed it, saved before any
  edit as `tmp/sweep/checker-r7/checker_r6_as_reviewed.py`) -> `789287c5316baef0d874c3e71220dc4049d4d2a07f6449b5ab92f55b58cd22b2`,
  1704 -> 1753 lines; frozen as `tmp/sweep/checker-r7/checker_r7_as_delivered.py`.
- Interdiff: `tmp/sweep/checker-r7/checker_r6_to_r7.diff`, 120 lines, +54/-7, sha256
  `4b680c760b634293e2ae3911f142774044f4b532b33b569e52273d1aa8f9bdd5` (`evidence/interdiff.log`). About 21 executable
  lines: `lex_pip_calls` (8), its comparison in `check_install_job` (6), two conditions in `check_loop`, and in
  `line_problems` one branch split in two (4 lines for 1) and one message. The rest is the docstring and comments.
  `commands()`, the lexer, `structure`, `pip_calls`, every allow-list entry and every deny rule are unchanged.
- Manifest: round 7's kept as `tmp/arc/sweep_scripts.r7.sha256` (copied before any edit; sha256 `3c5cfb08…`);
  `tmp/arc/sweep_scripts.sha256` regenerated over the same six paths (sha256
  `924328b11fb8d15eab8563015dcd6f08c1b2fdd146d409290dc89bb00f18e5e7`): only the checker's line changes, the writer's
  stays `c47940ad…`; `sha256sum -c` passes (`evidence/manifest.log`).
- juniper-cascor `main` is now `a68dd84e` (#778, a docs change); its three publishers, fetched read-only at 2026-11-24
  03:01Z through `util/ad-hoc/2026-11-15_fetch_pr_files.py` into `tmp/sweep/checker-r7/cascor-main-fetch/`, are
  byte-identical to the landing tree's (`evidence/fetch_cascor_main.log`).

**R7-1 executed (the question round 7 left open): the gap changes an outcome, so it was a MAJOR on the checker round 7
reviewed** (`two_readers_probe_r7.py`, `evidence/two_readers_probe_r7.out`; fix pass 4's stand-ins under `bash -e`).
- Fix pass 5's `S1`, as built, cannot change an outcome: it PASSES the reviewed checker, but executed the step fails
  (rc 1) before the hidden install, because `grep -E "'"` finds no single quote in the stand-in workspace's
  `pyproject.toml`; cascor's real install job checks nothing out, so on the runner the file is absent and grep fails too.
- Its variants keep the shlex trick and make the substitutions succeed: `S1p` (`"$(python -c "import tomllib #'")"`
  twice, no file read), `S1g` (`grep -E "'|"` then `"|'"`, patterns that match every line) on the template, and
  `S1g-cn`, `S1g` on canopy's port, whose sparse checkout brings `pyproject.toml` on the runner too. Each PASSES the
  reviewed checker; executed, each runs `pip install --no-deps --force-reinstall --index-url https://pypi.org/simple/`
  of the package under test between the TestPyPI fetch and the import check, and the step exits 0: the import check then
  judges PyPI's artifact, not the one TestPyPI served. By the brief's rule (an allow-list entry, `pip`, that admits a
  bypass) R7-1 was a MAJOR. Each FAILS the live checker, on the new rule.

**Applied.**
- R7-1: `lex_pip_calls(c)`, `pip_calls` read with `lex`, in the same form (each simple command holding a word that
  fullmatches `PIP_WORD`, as the words before it, it and the words after it, after quote removal, redirections set aside
  by `structure`). `check_install_job` refuses every install command on which it and `pip_calls(c)` differ ("its two
  readers disagree about the pip commands in a command"); a command `lex` cannot read is left to the allow-list, which
  refuses it. Over the template and the 15 simulations: 259 install commands, 21 pip commands by each reader, 0
  disagreements (`evidence/two_readers_inventory_r7.out`, read with the checker's own two functions).
- R7-4: `check_loop` compares the fetch's line as `pip_calls` reads the fetch, `pieces(shell_words(...)) == [([],
  fetch_words)]`, in both loop forms: redirections set aside, no reserved word before the fetch, and the fetch alone on
  the line. Round 7's H8 now PASSES. Each redirection's target is still judged by the allow-list: the FAIL cases are a
  `.py` file under `$RUNNER_TEMP` (N7-5), the wheel's own path in the `--dest` (N7-6), and an input redirection (L7f).
- R7-2 (NIT): the escaped-blank message now says what each reader does, and that the rule refuses wherever it stands:
  "this checker strips that blank and joins the next line with one space, where bash keeps the blank (a tab stays a
  tab) and reads the next line as it stands, so that outside quotes an indented next line, or a blank after the escaped
  one, ends bash's word there". Kept refused, not narrowed: an unindented next line still diverges after an escaped tab,
  after an unescaped blank that follows the escaped one, and inside single quotes; no port has an escaped blank.
- R7-3 (NIT): the blank-or-comment branch now gives one of two messages, each true wherever it is given. Where only blank
  lines follow, to the script's end: "continues the script's last command line into the end of the script (only blank
  lines follow it): bash runs that command alone there, and it is refused all the same". Otherwise, a message that
  holds for a blank line, for a comment line after a blank-preceded join, and for a comment line after an abutting or
  escaped join. The old message was also false for that last case: in fix pass 5's W6a, bash runs `twine check
  'dist/*#'` and `|| cp`, which that message called the command's end. Kept refused (no port continues its last line).
- R7-5 (NIT): the docstring says the template steps and the republish job are compared as parsed YAML (each action by
  name), so each of their run scripts equals the template's character for character.
- The docstring: a fix pass 6 bullet; "What this cannot see" now says that the pip rules judge `lex`'s words, and that
  the loop's and the import check's comparisons, `own_line` and the deny rules still read `shlex`'s words, each only
  adding refusals to the allow-list's reading of the same command.

**Found beyond the review** (N7-3, `evidence/new_mutants_r7.out`): R7-4's relaxation alone would have opened a hole.
`pieces()` takes any digit word before a redirection operator for its file descriptor. On
`"juniper-cascor==${VERSION}" 0 > "${RUNNER_TEMP}/fetch.log"`, the fetch's words as `pip_calls` and the relaxed
`check_loop` read them are the template's. bash, and `lex` (which takes a descriptor only when it abuts the operator),
pass `0` to pip: a second requirement fetched from TestPyPI, which F2 forbids (executed: `PIP install --no-deps
--index-url https://test.pypi.org/simple/ juniper-cascor==0.15.0 0`). The reviewed checker refused the line only because
it refused every redirection on the fetch's line. The live checker refuses it by R7-1's rule alone: the checker mutant
`checker_r7_minus_r71.py` (the live checker with that one comparison switched off, written by `make_minus_r71.py`)
PASSES N7-3, as it passes N7-1, N7-2 and N7-4. The same divergence on a later install (N7-4: bash also installs PyPI's
`0`, a plain requirement F3 would have admitted had it seen it) and on the flag form's fetch (proof case T7f) is refused
the same way.

**Relaxed:** R7-4 alone: a redirection on the fetch's line whose target the allow-list admits (round 7's H8; C7-1 and
C7-2; proof cases L7a to L7c). **Narrowed:** nothing.

**Results** (`evidence/rerun_all.out` unless named):
- cascor's three publishers: 3 of 3 from the landing tree, and 3 of 3 from `main` as fetched (`evidence/checks_cascor.log`);
- the 15 port simulations: 15 of 15 PASS under the new checker and the reviewed one (`evidence/port_sim_table.md`);
  regenerated by round 2's probes, they equal fix pass 5's byte for byte (0 diff lines); the generator's 25 variants
  keep 19 PASS / 6 FAIL;
- every earlier set by verdict, as its builder wrote it (`judge_mutants_r7.py`, `evidence/judge_mutants.md`): round 5's
  24 of 24, round 4's 18 of 18, round 2's 8 of 8, fix pass 3's 17 of 17, fix pass 4's 22 of 22, round 6's 10 of 10, and
  (added) fix pass 5's N6 set 18 of 18, N6-1 and N6-12 PASS as recorded; 0 mismatches;
- re-executed, as round 7 could not: round 4's M1-M15 and fix pass 3's N1-N14, regenerated and run by their own drivers
  (all FAIL, controls PASS, 0 unexpected); fix pass 4's N5-1..N5-16 (each PASSES `c826ab87` and FAILS the live checker;
  CN0r FAILS by design); round 6's R6-1..R6-6 (each PASSES `ebeb7556` and FAILS the live checker); fix pass 5's
  N6-1..N6-13 (N6-1 and N6-12 PASS, executing them changes nothing; the rest FAIL; controls PASS); 0 verdicts other than
  expected in each (`evidence/new_mutants_r5.out`, `r6_mutants_rerun.out`, `new_mutants_r6.out`,
  `r4review_mutants.txt`, `new_mutants_r4_rerun.txt`). Round 5's R5 set and round 2's were judged by verdict only;
- the two-readers probe: its 7 rows as expected (above);
- this pass's mutants (`new_mutants_r7.py`): 9, plus 6 controls, every one executed and judged by the reviewed checker,
  the live one and the R7-1-off mutant (`evidence/new_mutants_r7.out`):
  - N7-1 and N7-2 (hidden PyPI installs) and N7-4 PASS the reviewed checker and FAIL the live one;
  - N7-3 FAILS both and PASSES the R7-1-off mutant (above);
  - N7-5 and N7-6 FAIL all three, on the allow-list's targets. N7-5 sends the fetch's output into
    `${RUNNER_TEMP}/juniper_cascor.py`; executed with a real python, the import reads that file: `ImportError: cannot
    import name '__version__' from 'juniper_cascor' (.../runner_temp/juniper_cascor.py)`. N7-6 sends the download's
    output onto the wheel's path; executed, pip download keeps the file the redirection made, and the later installs
    install it;
  - N7-7, N7-8 and N7-9 (R7-2's and R7-3's forms; executing them changes nothing) FAIL all three, the live checker with
    the new messages;
  - controls T0, T0r, ML0 and W0 PASS all three; C7-1 and C7-2 FAIL the reviewed checker and PASS the live one;
  - 0 verdicts other than expected;
- over-strictness: round 5's O1-O3, round 6's OS1-OS12 and round 7's H0-H24 and W1-W8, 48 edits as their builders
  wrote them: 46 PASS the live checker; OS11 (R6-N1) and H19 (`>&2` on the lag error, by design) FAIL, as under the
  reviewed checker; H8 moved from FAIL to PASS (`evidence/overstrict.log`);
- the checker proof `checker_proof_r7.py`: 308 of 308 (fix pass 5's 289 kept, none overridden: every earlier reason
  substring is a message's leading words, which fix pass 6 kept; 19 new) (`evidence/checker_proof_r7.log`). Fix pass
  5's `checker_proof_r6.py`, unchanged, on the live checker: 289 of 289 (`evidence/checker_proof_r6_on_live.log`).
  `checker_proof_r7.py` on the reviewed checker: 296 of 308, the 12 mismatches exactly the new cases that need fix pass
  6 (T7a, T7b, T7c, T7f, L7a, L7b, L7c, B7a, B7b, B7c, E7a, E7b) (`evidence/checker_proof_r7_on_reviewed.log`);
- round 2's 43 cases: 43 of 43, every verdict kept against fix pass 3's log and fix pass 5's, no reason reworded since
  fix pass 5 (`evidence/checker_proof43.log`);
- the continuation inventory: unchanged (251 runs; 66 continuations, every one blank-preceded, none escaped; no
  character outside printable text, space, tab and newline);
- pre-commit (juniper-ml's config, `--files`): 11 passed, 0 failed, 15 skipped, the file unchanged; B914 0 sites;
  `--help` exit 0; flake8 `--isolated` at 512 columns: 14 E203 (Black's slice spacing: the reviewed copy's 12, and two
  on new lines, `:790` and `:1092`) (`evidence/precommit_checker.log`, `b914_checker.log`, `flake8_checker.log`).

**Residual risk** (the docstring's "What this cannot see", as rewritten):
- `lex` is still not bash. With R7-1's rule, F2-F4 judge `lex`'s pip words, so a place where `lex` or `commands()` reads
  a script otherwise than bash reopens the class. Round 7 did not hunt for new divergences; round 8 is asked to.
- The loop's and the import check's comparisons, `own_line`, the deny rules and the `pip --version` exemption still
  read `shlex`'s words. Each only adds refusals to the allow-list's reading; the exemption spares only a command whose
  pip commands both readers read as `pip --version` alone. No executed divergence there has been sought.
- R7-1's rule compares pip commands only; every other command is judged by the allow-list as `lex` reads it.
- R7-1's rule could refuse a command whose two readings differ harmlessly; none was found in the template, the 15
  simulations or the 48 harmless edits.
- Unchanged from fix pass 5: Python is not parsed; a later `pip install` of another PyPI package runs its code;
  setup-python's inputs and every action's `@ref` are not judged; a lowercase variable the runner exports may be
  reassigned; files a sparse checkout brings are not read; I6, the `python -c` assertion and the build job's steps up
  to the build are each repository's own business.

**Next:** round 8 (`tmp/sweep/ROUND8_BRIEF.md`), on this interdiff and on what round 7 could not do, before any port is
built against the checker. Round 7's decision stands: if round 8's executed-mutant step is interrupted again, stop and
ask the owner whether the static rounds suffice; no port without a complete round or that ruling.

**Deviation (fix pass 6, found by its own `checker-r7/untouched_r7.bash`):** the first two runs of
`checker-r7/quick_check.bash` (an editing aid, not evidence) ran fix pass 5's `port_sim_table_r6.py` on
`tmp/sweep/checker-r6/port-sim`, and that table's `ml_port()` regenerates
`checker-r6/port-sim/faithful+ml-F2+lag/juniper-ml/workflows/publish.yml` in its `--sim-dir`. The file's bytes did not
change: it equals fix pass 4's, round 7's and fix pass 6's copies by `cmp` (sha256 `2538be24…`); only its mtime moved,
to 02:50:51Z. Nothing else outside this pass's allowed outputs is newer than its first driver
(`checker-r7/evidence/untouched_r7.out`). `quick_check.bash` now runs `port_sim_table_r7.py` on `checker-r7/port-sim`.

## Status (session `ffffd3`, 2026-11-24 03:13Z)

Round 8 (brief `tmp/sweep/ROUND8_BRIEF.md`, a fresh reviewer, the checker `789287c5…`) was launched at 03:13Z. Its report:
`tmp/r8review/ROUND8_REPORT.md`. A new session: if that file exists and its first section lists nothing undone, record its
dispositions here as `## Round-8 review`; if it shows an undone step, the owner rules whether the static rounds suffice
(the decision in § "Round-7 review"); if the file is missing and no session is running round 8 (`ListAgents`), launch it
with `ROUND8_BRIEF.md`, unedited. No port is built before a COMPLETE round reports no BLOCKER and no MAJOR.

## Round-8 review (report: `tmp/r8review/ROUND8_REPORT.md`; session `ffffd3`'s subagent, finished 2026-11-24 ~04:00Z; brief `tmp/sweep/ROUND8_BRIEF.md`) -- COMPLETE

Verdict: 0 BLOCKER, 3 MAJOR, 0 MINOR, 5 NIT against the checker `789287c5…` (fix pass 6). Every step done, nothing
interrupted; limits it states: no bash 5.2 run (host has 5.3.9 only), pre-commit's two fixer hooks skipped (their
conditions checked directly), fixes only probed (`tmp/r8review/fixprobe/checker_r8_fixprobe.py`). Each MAJOR is an
executed mutant that passes the live checker and changes the outcome under `bash -e`. The stopping rule applies.

| id | sev | where | finding | disposition |
|---|---|---|---|---|
| R8-1 | MAJOR (new in fix pass 6) | `structure()` `:869`, `pieces()` `:535-537`; R7-4's relaxation `:1258`, `:1264` | A digit against `&>`/`&>>` is read as a file descriptor by BOTH readers, so R7-1's comparison agrees and R7-4 admits the line; bash passes the digit to pip as an argument (B8-1..B8-3 run a second TestPyPI requirement `0`, N7-3's outcome). | FIX PASS 7: a descriptor only before an operator starting with `<` or `>`. |
| R8-2 | MAJOR (predates fix pass 6) | `ASSIGNABLE_LOWER` `:423`, `SIMPLE_REFERENCE` `:405` | `_` is admitted as a name and an expansion; bash resets `$_` after every command to its last argument. B8-5 (ml's port, wheel variable `_`) installs `juniper-ml` from PyPI and never the TestPyPI wheel. | FIX PASS 7: refuse `_` as a name and an expansion. |
| R8-3 | MAJOR (predates fix pass 6) | the if-tests-only-`[ ]` rule `:1307`, the last-command check `:1477` | Both read with `shlex`, which fix pass 5's `"$(python -c "#'")"` trick fools: B8-7 swallows a failing later install (step returns 0), B8-8 a failing import (`ModuleNotFoundError`, step returns 0). | FIX PASS 7: judge an if's condition and the last command with `lex`. |
| R8-n | NIT ×5 | messages, docstring | R7-3's message is wrong for a CR / VT / FF / no-break-space "blank" line; three harmless edits refused with false reasons (a one-line `if [ -f ]`, `set -e -u` before the `cd`, the retry echo to `>&2`); three docstring claims these findings contradict. | FIX PASS 7: true messages, docstring corrected; admit the harmless edits only with FAIL cases for their divergent forms. |

The fix probe refuses B8-1..B8-3 and B8-5..B8-8 while keeping 3/3 cascor, 15/15 simulations and 308/308 proof cases, and
moves no over-strict verdict. **Sound:** every count of § "Fix pass 6" re-derived; every earlier mutant set
re-EXECUTED with its own driver (all fail except N6-1 and N6-12, whose execution changes nothing; controls pass); fix
pass 6's S1p/S1g/S1g-cn answer to R7-1 holds; 23 of 28 new harmless edits admitted.

**Pattern (orchestrator, ffffd3):** rounds 4-8 each found MAJOR-or-worse bypasses in the install-script rules
(R4-2; R5-F1; R6-F1; R7-1, executed by fix pass 6; R8-1..R8-3), each from the checker reading shell differently from
bash. The next step is the owner's choice between continuing this loop and a design change; see the owner's ruling
recorded below this section once given.

## The owner's ruling on the checker's install-step judgement (2026-11-24, answered by 12:15:11Z; session `ffffd3`'s dialog)

Asked after round 8 (`AskUserQuestion`, header "Checker"): "The one-artifact sweep's cross-repo port checker keeps
failing review: rounds 4-8 each found a MAJOR-or-worse bypass, every one because the checker's own reading of a port's
install script differs from what bash does (round 8: 3 MAJORs, with a fix probe already validated). juniper-cascor#777
has merged; the 15 ports in 7 repos wait on this checker. How should the checker's install-step judgement proceed?"

**Answer, verbatim: "Pin exact scripts (Recommended)"**, whose option text read: "Stop judging port install scripts with
a bash reader. Each port's install step must equal, after whitespace normalization, a pinned reviewed script for that
port (seeded from the 15 port simulations, updated in each port's own review). This closes every lexing bypass at once
and matches what each repo's tests already pin. One review round on that change, then the ports."

Not chosen: "Keep fixing the reader" (fix pass 7 with round 8's probed fixes, then round 9, repeating) and "Fix pass 7,
then ports" (no further checker round).

**Consequences:**
- Fix pass 7 implements exact pins (brief `tmp/sweep/FIXPASS7_BRIEF.md`). Round 8's R8-1..R8-3 close by construction for
  install scripts; the bash reader may stay only where the checker still needs it (the build window, other steps), and
  round 9 reviews that change once.
- Each port's own review then updates its pinned script.
- Round 8's probed fixes (`tmp/r8review/fixprobe/checker_r8_fixprobe.py`) still apply wherever the reader remains.

## Fix pass 7 (the owner's exact-pins ruling; checker-r8)

The executor reported this: the final message of session `d935c226`'s subagent for fix pass 7 (orchestrator `ffffd3`,
brief `tmp/sweep/FIXPASS7_BRIEF.md`), 2026-11-24 ~12:25Z to 13:15Z (times from `date -u`). It implements the owner's
ruling above ("Pin exact scripts"). Written: the checker, the new pins file, the manifest, this section,
`tmp/sweep/ROUND9_BRIEF.md` and new files under `tmp/sweep/checker-r8/`. The writer, cascor's tree, every workflow, every
port, `tmp/sweep/land/` and every earlier review directory are untouched (`checker-r8/evidence/untouched_r8.out`; the two
files it lists, `tmp/arc/handoff-pr2/wait_checks_2630.log` and `safe_merge_2630.log`, 12:36:37Z and 12:36:53Z, are another
session's merge of juniper-ml#2630, not this pass's). Every
driver is in `tmp/sweep/checker-r8/` beside its evidence (`evidence/`): `rerun_all_r8.bash` re-runs every step
(`evidence/rerun_all.out`, 2026-11-24T13:10:18Z to 2026-11-24T13:15:12Z), `finish_r8.bash` freezes the outputs and writes the interdiff and
the manifest. The mutants are negative test cases for this CI checker.

**Versions.**
- Checker: `789287c5316baef0d874c3e71220dc4049d4d2a07f6449b5ab92f55b58cd22b2` (as round 8 reviewed it, saved before any
  edit as `checker-r8/checker_r7_as_reviewed.py`) -> `039e5e6d5830955c1593ccdec4b7bfdbc0bc1558c305d21fca85b47ff4bc13e0`, 1753 -> 953 lines
  (122110 -> 72746 bytes); frozen as `checker-r8/checker_r8_as_delivered.py`.
- Interdiff: `checker-r8/checker_r7_to_r8.diff`, 1765 lines, +393/-1193, sha256 `65253032f0279b8db45aa77874c9541a22319d3742de43a6517a2e5699849953`
  (`evidence/interdiff.log`). Most of it is deletion: the shell reader and every install-script rule.
- Pins file (new): `util/ad-hoc/2026-11-24_publish_port_install_pins.json`, sha256
  `fde7e0ca4686ec7ed65bdfb7f5d813e7b75987b4a4e8c0f0e56d46df9efe1906`, 18 pins, 552 lines; frozen as
  `checker-r8/pins_as_delivered.json`; written by `checker-r8/make_pins.py` (`evidence/make_pins.out`).
- Manifest: round 8's kept as `tmp/arc/sweep_scripts.r8.sha256` (copied before any edit; `924328b1…`);
  `tmp/arc/sweep_scripts.sha256` regenerated over SEVEN paths (sha256 `24c8e1e12f74d5e1f9f663c4b2a4cfebbdaa70ffb6b10359acdcb9a2da59efca`): the checker's line changes,
  the pins file's line is new (after the checker's), the writer's stays `c47940ad…`; `sha256sum -c` passes
  (`evidence/manifest.log`).
- juniper-cascor: fetched read-only at 12:32:30Z at `f5ed3017` (#777's merge, the seed of cascor's three pins) and at
  `main` `b5b28dc3` (#779) into `checker-r8/cascor-f5ed3017-fetch/` and `cascor-main-fetch/`; each of the three
  publishers byte-identical to the landing tree at both (`evidence/fetch_cascor_main.log`).

**Design decisions** (each stated in the checker's docstring, § "Fix pass 7: exact pins"):
- **What is pinned:** every `run` step of the job named `Verify the TestPyPI install`: one step per publisher, 18 in all
  (cascor's three included; `evidence/survey_install_steps.out`). No other per-port run script needed a pin. The only
  other one the checker read with a shell reader is a build-window step (`evidence/survey_window_steps.out`), judged
  against the checker's own exact allow-list, which the brief keeps.
- **The key:** (`--repo`, the workflow file's name as the operator passes its path, the step's `name`). Each pin also
  names its package, which must equal the workflow's `PUBLISH_PACKAGE`, so a pin never vouches for another package.
- **The pins file:** beside the checker, loaded from `Path(__file__)`'s directory; `--pins PATH` overrides it, an
  operator argument only. JSON: `format` (`juniper-publish-install-pins/1`), `about`, `pins`; each pin holds exactly
  `repo`, `workflow`, `step`, `package`, `source` (provenance), `sha256` and `lines` (the text is the lines joined with
  `\n`, no final newline; one array element per line, so a port's review diffs it line by line). Written with
  `ensure_ascii`, so every non-ASCII character shows as an escape. Refused whole as it loads (exit 1, nothing checked):
  a repeated JSON key, another format, a pin without exactly those fields, a repository not in `REPOS`, a bad workflow or
  step name, empty or newline-holding lines, a repeated pin key, a text a step would be refused for, a sha256 that is not
  its text's, and no single retry loop with the template's lag error (`LAG_ERROR`, kept as a text check on each pin).
  The path and the sha256 of the bytes validated are printed first.
- **The comparison:** the step's `run` as YAML delivers it (YAML has already made `\r\n` into `\n`) is REFUSED, never
  normalized, for a NUL, a character other than printable text, a tab and a newline (CR, NEL, LS, PS, control and format
  characters), trailing whitespace on any line (a backslash then a space is an escaped space; stripping it would make a
  continuation), a final backslash (a final newline would decide its meaning) or `${{` (the runner substitutes an
  expression into the text before bash reads it). Otherwise only its final newline(s) are removed (chomping: `|`, `|-`
  and `|+` deliver the same script) and the rest is compared byte for byte, comments included.
- **A mismatch** names the key, the first differing line (the pin's and the step's) and a unified diff (24 lines at
  most), and says to update the pin through that port's review if the change is intended. A step with no pin, a pin with
  no step, two run steps under one name, and an install-step key GitHub does not define (`Run:`) each fail on their own.
- **What the runner runs, against what the checker reads** (beyond the brief, from "think about what the runner actually
  executes"): the runner writes GitHub's parse of the YAML, and the checker reads PyYAML's (YAML 1.1). Where the two are
  known to differ, the file is refused: any character other than printable text, a tab, LF or CR LF anywhere in the
  workflow file (`file_problems`: PyYAML reads a raw U+0085 as a line break and drops the next line's indentation, a
  YAML 1.2 parser keeps both in the line; `evidence/yaml_divergence_probe.out`); a repeated key, by its text or by
  PyYAML's value, and a merge key (`UniqueKeyLoader`: PyYAML keeps the last of repeated keys and applies merges). The
  file is read as bytes and decoded, never through Python's newline translation. The workflow's
  `defaults.run.working-directory` is refused (where a pinned script starts; no port sets one).
- **Removed:** the shell reader (`lex`, `structure`, `shell_words`, `pieces`, `skeleton`, `operators`, the lexer's
  helpers) and every rule that read an install script with it: fix pass 4's allow-list, F2/F3, F4's script rules, the
  retry-loop rule, R4-2's last command, R4-3's deny rules, the cd-first, `||`, `set +`, `trap` and `exit` rules, the
  dest and wheel rule, R7-1 and R7-4, and `line_problems` on install steps.
- **Kept:** template-block identity, the jobs, `needs`, permissions, environments, every env-key rule, the install job's
  actions, checkout, step, shell, env and working-directory rules, `bash -n`, the build window's exact allow-list,
  `--repo` scoping and LAG_ERROR (now on the pins).
- **The reader that stays, and why:** the build window, read by `commands()` and checked by `line_problems` (fix pass
  5's line rules). Its allow-list is the checker's own (`TWINE_CHECK`, `TAG_ASSERT`, `CANOPY_SMOKE`), compared as
  commands so that layout edits bash reads alike keep passing (round 7's W1-W8, which the brief protects). Its forms hold
  none of the quoting, substitution or pip of rounds 4-8's lexer bypasses, and round 8 found no window bypass (B8-16).
- **Considered and not made:** a rule holding a pinned `run` to a literal block or one line (to rule out YAML folding
  differences): the juniper-ml simulation's install step (a seed) and, at the window, canopy's smoke step and round 7's
  W3, W4 and W7 are single-quoted scalars over several lines (`evidence/survey_scalar_styles.out`), so it would refuse a
  seed and flip protected verdicts. Left to round 9 as a divergence to probe.

**Round 8's findings.**
- R8-1, R8-2, R8-3 (MAJOR): closed by construction for install scripts: any such edit changes the text. Their seven
  executed bypasses (B8-1 to B8-3, B8-5 to B8-8) FAIL on their pins. Round 8's probed fixes had nothing left to apply
  to: every place they touched (`structure`, `pieces`, the allow-list, its if rule, R4-2's last command) is removed.
- N8-1: applied where `line_problems` remains, the build window (`following = lines[at + 1].strip(" \t")`); proof case
  W8a shows the true message alone (a window continuation into a CR-only line: "holds a line break other than a newline",
  and not the blank-line message).
- N8-2 to N8-4: their over-strict rules are removed; the edits they refused (O8-11, O8-14, O8-18) fail now as pin
  mismatches, by design. N8-5: the docstring is rewritten (the three claims are gone with their rules).

**Found beyond the brief** (`new_mutants_r8.py`, executed): two YAML-level forms PASS the checker round 8 reviewed:
- X8-2: a raw U+0085 in place of the newline after a comment line. PyYAML reads the pinned text. Under a YAML 1.2
  reading the comment swallows the next line: the `for` line never runs, `break` runs outside a loop, and bash stops at a
  syntax error at `done` (rc 2; the pin's script: rc 0).
- X8-3: a repeated `run:` key, an unpinned script first and the pinned one last. PyYAML keeps the last. A parser that
  keeps the first runs `pip install --force-reinstall --index-url https://pypi.org/simple/` of the package under test
  and imports it (rc 0, TestPyPI never fetched): a bypass under such a parser.

Whether GitHub's parser reads either otherwise than PyYAML was not verified (no GitHub parser here). The live checker
refuses both (`file_problems`, `UniqueKeyLoader`); proof cases Y8a to Y8e cover the class.

**Results** (`evidence/rerun_all.out` unless named):
- **1. cascor's three publishers:** 3 of 3 from the landing tree, 3 of 3 from `f5ed3017` and 3 of 3 from `main` as
  fetched (`evidence/checks_cascor.log`).
- **2. the 15 port simulations:** 15 of 15 PASS (`evidence/port_sim_table.md`). Regenerated by round 2's probes into
  `checker-r8/port-sim`, they equal fix pass 6's (the seeds) byte for byte (0 diff lines); the generator's 25 variants
  keep 19 PASS / 6 FAIL.
- **3. every earlier mutant set FAILS, the controls PASS** (`judge_all_r8.py`, `evidence/judge_all_r8.md`; each file as
  its builder or fix pass 6 wrote it, placed under its pinned workflow name; execution not repeated, since what each runs
  does not depend on the checker and round 8 re-executed every set), 0 findings:

  | set | mutants FAIL | controls PASS |
  |---|---|---|
  | round 8's B8 | 17 of 17 (B8-4, B8-12 to B8-14 passed before, changing nothing: by design) | 5 of 5 |
  | fix pass 6's N7 | 9 of 9 | 4 of 6 (C7-1, C7-2 by design) |
  | fix pass 6's two-readers probe (S1, S2, S1p, S1g, S1g-cn) | 5 of 5 | 1 of 2 (A0 by design) |
  | round 6's R6 | 6 of 6 | 4 of 4 |
  | fix pass 5's N6 | 13 of 13 (N6-1, N6-12, the tab rows that passed before: by design) | 4 of 5 (C6-1 by design) |
  | fix pass 4's N5 | 16 of 16 | 5 of 6 (CN0r failed before: a widened checkout) |
  | round 5's R5 (and S1, S2) | 20 of 20 | 4 of 4 (T0, ML0, S3, S4) |
  | round 4's M | 15 of 15 | 2 of 3 (ML0 failed before: the old lag error) |
  | round 2's seven | 7 of 7 | 1 of 1 |
  | fix pass 3's N | 14 of 14 | 3 of 3 |

  Round 8's seven bypasses of the reviewed checker (B8-1 to B8-3, B8-5 to B8-8) all FAIL now. Many mutants fail on a pin
  mismatch, which is correct.
- **4. harmless edits:** of 76 earlier harmless edits (round 5's O1-O3, round 6's OS1-OS12, round 7's H0-H24 and W1-W8,
  round 8's O8-1 to O8-28), the 9 outside install scripts keep their verdicts (H0 and W1 to W8 PASS). Every
  install-script edit that PASSED the reviewed checker FAILS now **by design under the ruling, 70 in all**: the
  corpora's O1-O3, OS1-OS10, OS12, H1-H18, H20-H24 and O8-1 to O8-10, O8-12, O8-13, O8-15 to O8-17, O8-19 to O8-24,
  O8-27, O8-28 (comments, `set -eu`, renamed variables, tabs, redirections, reordered options, `python3`, echo text, a
  blank line, `sleep 60`); and among the mutant sets' controls and harmless rows, C6-1, N6-1, N6-12, C7-1, C7-2, A0, B8-4
  and B8-12 to B8-14. OS11, H19, O8-11, O8-14, O8-18, O8-25 and O8-26 failed before and fail now.
- **5. the proof** (`checker_proof_r8.py`, built by `make_proof_r8.py`: fix pass 6's file with its 306 table cases kept
  byte for byte and its main() replaced; `evidence/checker_proof_r8.log`): 349 of 349. Every changed verdict and why:
  - the rule, stated on each row: a case whose install steps are not their pins must FAIL on a pin reason, by design;
    every other case keeps fix pass 6's verdict and reason;
  - PASS -> FAIL by design, 43: F2a, R42e, R42f, R42h, R43b, R43f, R43m, R43p, R43v, PVa, IXa, SQa, SQb, EPa, ADe, ADl,
    E5d, A5u to A5x, A5ae, A5af, A5aq, B5d, B5f, B5h, B5k, O5a, O5b, O5e, O5f, J6b, J6c, J6e, J6h, J6l, N6e, T7d, T7e,
    L7a, L7b, L7c (each a harmless install-script edit, now a pin mismatch);
  - FAIL kept on the pin, 197: 192 whose fix pass 6 reason (from a removed rule) gives way to the pin's, 5 (A9, N6a to
    N6d) whose fix pass 6 reason is still given beside it;
  - 66 unchanged: their install scripts equal their pins (63), or no pin names their (repo, package) (3: R46a, R46b,
    R46d, `--repo` scoping cases);
  - the driver's one fix: each simulation case is written under its pinned workflow name (fix pass 6 wrote doc-tools'
    and recurrence-model's as `publish.yml`);
  - NEW8, 40 cases: trailing whitespace (T8a-T8c, `\` then a space included), a changed, dropped or added comment
    (K8a-K8c), CRLF (CR8a, CR8b: PASS), a pin key for the wrong repo (R8a-R8c), a missing pin and a renamed, extra or
    repeated step (M8a-M8d), a tampered `--pins` and eight more refused pins files (P8a-P8i), the YAML-level refusals
    (Y8a-Y8j: a repeated or merge key, a raw NEL or lone CR, `on` and `"on"`, a step key `Run`, escaped CR and NUL, `${{`,
    a final backslash), chomping (CH8a, CH8b: PASS; CH8c, a leading blank line: FAIL), the workflow working-directory
    (D8a), N8-1's window message (W8a) and a window layout control (W8b: PASS); and 3 command-line cases (`--repo`
    missing, not one of `REPOS`, `--pins` naming no file).
- **round 2's 43 cases** (`run_proof43_r8.bash`, `evidence/proof43_classes.out`): 29 as round 2 expected; C1 PASS ->
  FAIL by design; 13 FAIL kept, their reason moved to the pin's (K5, K12, R6-R9, R12-R18); 0 other changes.
- **New executed negative tests** (`new_mutants_r8.py`, `evidence/new_mutants_r8.out`), 8, each run as the runner would
  run it under `bash -e` with stand-ins, beside the pin's own script: each FAILS the live checker, PASSES
  `checker_r8_naive.py` (the live checker with that refusal replaced by a weaker normalization, so each refusal is
  load-bearing), and changes the outcome; 0 unexpected:
  - X8-1, a backslash then a space after `if pip install`: pip runs as `install ' '` and the option lines run as
    commands (rc 1);
  - X8-2, a raw NEL, and X8-3, a repeated `run:`: above;
  - X8-4, an escaped CR after canopy's version line: the fetch asks for `juniper-canopy==0.15.0\r`;
  - X8-5, `--no-deps` written with fullwidth hyphens (NFKC-equal, printable): pip runs without `--no-deps`;
  - X8-6, `#; exit 0` against the lag error's closing quote: with TestPyPI lagging, the step exits 0 without the import
    check (the pin: rc 1);
  - X8-7, an unpinned step first writing `BASH_ENV` into `GITHUB_ENV`: `python()` is redefined and a failing import
    exits 0;
  - X8-8, a pin (through `--pins`, its sha256 updated) and its step holding `${{ github.event.release.name }}`: a
    release name runs a PyPI install before the fetch.
  - Fix pass 6's checker refuses six of the eight, not X8-2 and X8-3.
- **6. lint** (`lint_checker_r8.bash`): pre-commit (juniper-ml's config, `--files` the checker and the pins file):
  12 passed, 0 failed, 14 skipped, both files unchanged; B914 0 sites; flake8 `--isolated` at 512 columns: 3 E203
  (Black's slice spacing); `--help` exit 0 (`evidence/precommit_checker.log`, `b914_checker.log`, `flake8_checker.log`,
  `checker_help.log`). An earlier lint run found a B014 (a redundant `UnicodeDecodeError` beside `ValueError`), fixed.

**Expected pin updates, per port** (each port's own review makes its pin equal its final script; listed so each review
knows):
- every port: its final text (comments, layout) replaces the simulation seed; cascor's three are final;
- R4-5, a failing `importlib.util.find_spec(<module>)` check: juniper-cascor-client `publish.yml`, juniper-cascor-worker
  `publish.yml`, juniper-data `publish.yml`, juniper-data-client `publish.yml`, juniper-ml `publish-ci-tools.yml` and
  `publish-observability.yml`;
- juniper-ml `publish.yml` (R5-F5 with R4-1): the simulation's three edits (the flag-form fetch, `ls -la` without
  `|| true`, the template's lag error), with `tests/test_publish_testpypi_verify.py:477` moved to the template's lag
  text;
- no known content update beyond the final text: juniper-canopy, juniper-recurrence's three, juniper-ml's
  config-tools, doc-tools, model-core and service-core.

**Residual risk** (the docstring's "What this cannot see"):
- equality is all the checker proves: what a pin does is each port's review's business (under `bash -e {0}` and, with
  `shell: bash`, `-eo pipefail`);
- GitHub's YAML parser is not PyYAML: the known differences are refused, others (folding in multi-line flow scalars,
  escapes) are not known and not ruled out; the runner is assumed to write the substituted `run` string unchanged;
- unchanged from earlier passes: setup-python's inputs and every action's `@ref`; files a sparse checkout brings; extra
  jobs (noted); the build job's steps up to the build; juniper-ml's tag assert pastes `${{ github.ref }}` by design.

**Next:** round 9 (`tmp/sweep/ROUND9_BRIEF.md`), once, on this interdiff and the pins file. The stopping rule is
unchanged: no port until a COMPLETE round reports no BLOCKER and no MAJOR.

## Status (session `ffffd3`, 2026-11-24 13:17Z)

Fix pass 7 finished (checker `039e5e6d…`, 953 lines; pins `util/ad-hoc/2026-11-24_publish_port_install_pins.json`
`fde7e0ca…`, 18 pins; manifest 7 paths). Round 9 (brief `tmp/sweep/ROUND9_BRIEF.md`, a fresh reviewer) launched at 13:17Z; its
report: `tmp/r9review/ROUND9_REPORT.md`. Record it here as `## Round-9 review`. A COMPLETE round with no BLOCKER and no
MAJOR clears the ports; anything else follows the stopping rule.

## Port item added after #2630 (session `ffffd3`, 2026-11-24 13:25Z; reported by the rename session eb0525, verified)

- **juniper-recurrence, all three publishers** (`publish-recurrence-app.yml`, `-model.yml`, `-client.yml`): line 22, in the
  "TRUSTED-PUBLISHER REGISTRATION" header, reads `#        Overtoad       = pcalnon`. That field is PyPI's technical
  `owner` (the GitHub account), rename collateral from juniper-recurrence#237. The recurrence port restores
  `#        owner       = pcalnon` (aligned with `repository  =`) in all three. It is a header comment, outside every
  pinned install script, so the pins are unaffected. cascor's template has no such line; its "the Overtoad" text names
  the person and is right.

## Round-9 review (report: `tmp/r9review/ROUND9_REPORT.md`; session `ffffd3`'s subagent, finished 2026-11-24 ~14:05Z; brief `tmp/sweep/ROUND9_BRIEF.md`) -- COMPLETE

Verdict: 1 BLOCKER, 3 MAJOR, 2 MINOR, 3 NIT against the checker `039e5e6d…` and pins `fde7e0ca…` (fix pass 7). Every
step done. Limits: GitHub's server-side parser was not available; its open-source lineage was run (actions/runner
`aea9aaa3`, YamlDotNet 5.3.0 / 16.3.0, libyaml, Node `yaml`); four effects were shown with local stand-ins. **Fix pass 7's
own code held**: across 84 hand-built install-step forms, 4,500 random mutants and the 18 pins in 810 scalar renderings,
no case where PyYAML and GitHub's lineage both parse and read different text. All blocking findings are one level
outside the install script and predate fix pass 7. The stopping rule applies: fix pass 8, then round 10.

| id | sev | where (checker `039e5e6d…`) | finding | disposition |
|---|---|---|---|---|
| B9-1 | BLOCKER | `:824-864`; claim `:830` | The TestPyPI and PyPI jobs (they hold the upload credential) accept `container:`, `services:` and any `runs-on`. M9-13 (a job container: its `python3` passes "Verify the dist against SHA256SUMS" on a wrong dist and swaps the files the upload sends), M9-14 (a service with the work tree mounted rewrites dist after the check), M9-15, M9-16 PASS. | FIX PASS 8: hold each job of the chain to the template's exact job keys, `runs-on: ubuntu-latest`. |
| M9-A | MAJOR | `:619-638` | The install job refuses `container` but accepts `services:`; M9-1 (a service writes a pip config) turns rc 1 into rc 0 with a wheel that never came from TestPyPI. | FIX PASS 8: an exact key list for the install job. |
| M9-B | MAJOR | `:660-661`; note `:169` | setup-python's `with:` is never read: `mirror` + `check-latest` downloads an interpreter from any URL, runs its `setup.sh`, and puts it first on PATH (M9-2 flips rc 1 to 0). | FIX PASS 8: admit only `python-version` (with the template's value). |
| M9-C | MAJOR | `:306-314` | PyYAML types plain scalars by YAML 1.1, GitHub by 1.2 core: `retention-days: 1:30` is 90 to the checker and "1:30" -> 1 day to upload-artifact; `0132`, `default: no` also pass. | FIX PASS 8: load plain scalars with YAML 1.2 core rules (or refuse every 1.1/1.2-ambiguous plain scalar); no current file changes verdict. |
| m9-a | MINOR | block-scalar claim | `\|`, `\|-`, `\|+` are not "the same script" when it ends inside an unterminated here-document (three newlines flip rc 1 to 0; M9-11). No pin ends that way. | FIX PASS 8: accept at most one final newline. |
| m9-b | MINOR | `:94` | The pins file is claimed ASCII-escaped but the loader does not enforce it: M9-7, a Cyrillic look-alike of the TestPyPI host, loads and passes (pip asks `test.xn--pi-kmcm.org`). | FIX PASS 8: refuse a non-ASCII pins file. |
| n9-a | NIT | `:330` | X8-2 (raw NEL): YamlDotNet reads it as PyYAML does; X8-3 (repeated `run:`): GitHub's TemplateReader refuses the file. Keep both refusals; reword the message. A leading BOM and a no-break space in a comment are refused with a reason untrue for them (no current file has either). | FIX PASS 8: true messages. |
| n9-b | NIT | `:542` | The mismatch message names the default pins file even under `--pins`. | FIX PASS 8. |
| n9-c | NIT | `:741` | A non-mapping step crashes the checker (exit 1: fails closed, but later workflows in the run go unchecked). | FIX PASS 8: a clean refusal. |

**Sound (round 9):** 3/3 cascor (landing tree, `f5ed3017`, `main`); 15/15 simulations, 0 lines from the seeds; the 18
pins re-derive equal; proof 349/349; every earlier mutant set as fix pass 7 recorded; M9-8 (package binding), M9-9 (a pin
line ending `\ `), M9-10 (the build window's hidden `cp`) and P9-2 correctly refused; no over-strict refusal against a
real port.

## Fix pass 8 (round 9's fixes; checker-r9)

The executor reported this: the final message of session `d935c226`'s subagent for fix pass 8 (orchestrator `ffffd3`,
brief `tmp/sweep/FIXPASS8_BRIEF.md`), 2026-11-24 ~14:10Z to 15:04Z (times from `date -u`). Written: the checker, the pins
file (its `about` alone), the manifest, this section, `tmp/sweep/ROUND10_BRIEF.md` and new files under
`tmp/sweep/checker-r9/`. The writer, cascor's tree, every workflow, every port, fix pass 7's tools and every earlier
review directory (round 9's included) are untouched (`checker-r9/evidence/untouched_r9.out`; the one other file it
lists, `tmp/arc/plan_v1_15_18_inputs.md`, modified 14:52:19Z, is another session's, not this pass's). Every driver is in
`tmp/sweep/checker-r9/` beside its evidence (`evidence/`): `rerun_all_r9.bash` re-runs every step in order
(`evidence/rerun_all.out`, 2026-11-24T14:56:23Z to 2026-11-24T15:03:54Z), `finish_r9.bash` freezes the outputs and writes the interdiffs
and the manifest. The mutants are negative test cases for this CI checker.

**Versions.**
- Checker: `039e5e6d5830955c1593ccdec4b7bfdbc0bc1558c305d21fca85b47ff4bc13e0` (as round 9 reviewed it, saved before any
  edit as `checker-r9/checker_r8_as_reviewed.py`) -> `9cf16a2f13152ddc75ce2f695758a6f5df95f93c713b347b46adc5959c157bb9`, 953 -> 1172 lines (72746 -> 91921
  bytes); frozen as `checker-r9/checker_r9_as_delivered.py`.
- Interdiff: `checker-r9/checker_r8_to_r9.diff`, 530 lines, +270/-51, sha256 `f019b759b0b829354e18dfa5447f6e90689cdf008a89d81aa9359332e16c0f29`
  (`evidence/interdiff.log`).
- Pins file: `fde7e0ca4686ec7ed65bdfb7f5d813e7b75987b4a4e8c0f0e56d46df9efe1906` (saved as `checker-r9/pins_r8_as_reviewed.json`)
  -> `d539f05fbd6666d4311fc57cfbf2a4680bfb4ca498b983dc7ccb93c4878a69b3`, 552 lines; frozen as `checker-r9/pins_r9_as_delivered.json`. Only its `about` changed
  (`checker-r9/pins_r8_to_r9.diff`, 10 lines, sha256 `ac7dcc1238c68e450ff545a2e3c6c44f26066dff1e174dc0a2558e097f078994`; written by `update_pins_about_r9.py`, which
  asserts the 18 pins unchanged): "apart from the final newline(s)" became "apart from one final newline (a step ending in
  more than one is refused: fix pass 8)", and it now says the checker refuses a pins file holding any byte outside ASCII.
  The file was already pure ASCII, every em dash an escape, so no pinned text changed.
- Manifest: fix pass 7's kept as `tmp/arc/sweep_scripts.r9.sha256` (copied before any edit; `24c8e1e1…`);
  `tmp/arc/sweep_scripts.sha256` regenerated over the same seven paths (sha256 `ba75d4c7cfd6bd3dbb17043da2f179a70404ae88dbbcfbb2bc2e7a909c8ca4fd`): the checker's and the pins
  file's lines change, the writer's stays `c47940ad…`; `sha256sum -c` passes (`evidence/manifest.log`).
- juniper-cascor: `main` re-fetched read-only at 14:29:46Z, still `b5b28dc3` (#779), its three publishers byte-identical
  to the landing tree (`evidence/fetch_cascor_main.log`); `f5ed3017` is fix pass 7's fetch, used read-only.

**Round 9's findings, each closed** (the decisions are in the checker's docstring, § "Fix pass 8: the jobs' keys and
YAML 1.2 typing"):
- **B9-1, M9-A**: each job of the chain carries exactly its template job's keys, the sets juniper-cascor's own test pins
  (`CHAIN_JOB_KEYS`), with `timeout-minutes` (that test's `OPTIONAL_JOB_KEYS`) on every job but the republish job:
  - build: `name`, `if`, `runs-on`, `permissions`, `steps` (+ `timeout-minutes`; + `defaults` in a sub-package's
    publisher, exactly `{run: {working-directory: <PUBLISH_PACKAGE>}}`);
  - TestPyPI and PyPI: `name`, `needs`, `runs-on`, `environment`, `permissions`, `steps` (+ `timeout-minutes`);
  - install: `name`, `needs`, `runs-on`, `permissions`, `steps` (+ `timeout-minutes`);
  - republish: its template's six, compared whole as before (so no `timeout-minutes`), and now also by the key set.
  `runs-on` is `ubuntu-latest` on all five (newly compared on the TestPyPI and PyPI jobs); `permissions`, `needs`, `if`
  and the environment's name compared as before; the environment's `{name, url}` mapping (cascor's sub-package
  publishers and 9 of the 15 simulations write it, `evidence/survey_job_keys.out`) holds those two keys alone, `url` a
  string. This refuses
  `container`, `services`, `strategy`, `env`, `outputs`, `concurrency` and any other key and runner on every chain job.
  The earlier specific rules stay (their messages); the build-job env rule's message was made true.
- **M9-B**: every setup-python step of the build and install jobs takes `with: {python-version: <"3.N">}` alone
  (`setup_python_problems`; the action matched by name, case-insensitively). The docstring's residual (old `:169`) now
  says setup-python's inputs are judged. **Deviation:** not "the template's value": canopy's simulation (and its port)
  uses "3.14", so the form is held (a CPython version written as a string; unquoted, YAML makes `3.10` the number 3.1).
- **M9-C**: plain scalars are typed as GitHub's reader types them: `GITHUB_SCALARS`, transcribed from actions/runner's
  `YamlObjectReader.AllowLiteral` (`aea9aaa3`; MatchNull, MatchBoolean, MatchInteger, MatchFloat), PyYAML's YAML 1.1
  resolvers no longer used. Tags as GitHub's reader admits them (`!!str` in any style; `!!null`, `!!bool`, `!!int`,
  `!!float` on a plain scalar holding the form); every other tag refused (GitHub refuses it on a scalar; on a
  collection it ignores one where PyYAML would build a set or pairs). `on` now loads as the text `on` (no restoring);
  the merge-key refusal is by text (a plain `<<`); a document that is not a mapping is refused; a `0x`/`0o` integer
  above 0x7FFFFFFF is refused (GitHub reads it as 32 bits: negative). `retention-days: 1:30`, `0132` and `9_0`, and
  `default: no`, now FAIL (Y9a to Y9e, N9-6, M9-3, M9-3b, M9-4).
- **m9-a**: a pinned step's `run` ends in one newline at most (`|` or `|-`); M9-11 and N9-8 FAIL.
- **m9-b**: `load_pins` refuses a pins file holding any byte outside ASCII; M9-7, P9a (raw em dashes), P9b (a BOM)
  refused.
- **n9-a**: `file_problems` keeps every refusal; its message now says what is true of each character (GitHub's
  YamlDotNet reads a raw NEL as PyYAML does; a BOM or a no-break space changes nothing PyYAML reads and is refused as
  defence in depth). **Correcting § "Fix pass 7"'s X8-2 and X8-3 text** (this file is append-only): X8-2 (a raw NEL) is
  not a bypass on GitHub, whose YamlDotNet reads it as PyYAML does, and X8-3 (a repeated `run:`) is not one either,
  since GitHub's TemplateReader refuses the file (`ValueAlreadyDefined`); both refusals stay as defence in depth.
- **n9-b**: a pin mismatch names the pins file this run loaded (each loaded pin carries its file).
- **n9-c**: `shape_problems` refuses a workflow whose `on`, `jobs`, a job or a step is not a mapping (or `steps` not a
  list) with a message; any other shape no rule reads fails that workflow alone (a catch-all in `main()`), and the
  next workflow is still checked (CLI4).

**Results** (`evidence/rerun_all.out` unless named):
- **1. cascor's three:** 3 of 3 from the landing tree, from `f5ed3017` and from `main` (`evidence/checks_cascor.log`).
- **2. the 15 simulations:** 15 of 15 PASS (`evidence/port_sim_table.md`; fix pass 7's checker PASSES all 15 too);
  regenerated by round 2's probes they equal the seeds byte for byte (0 diff lines; 19 PASS / 6 FAIL among the 25
  variants, as before). **The 18 pins re-derive equal** (`rederive_pins_r9.py`, round 9's, copied: libyaml and
  YamlDotNet 5.3.0 agree on every source; `evidence/rederive_pins.out`). Its "ends with newline: False" line is a
  driver bug inherited from round 9 (the f-string tests `b'\\n'`, a backslash and an `n`); the file ends in a newline.
- **3. every mutant set:**
  - earlier sets (`judge_all_r9.py`, `evidence/judge_all_r9.md`): every row keeps fix pass 7's recorded verdict, 0
    moved, 0 findings, set by set as fix pass 7's section lists (r5 24/24 … r8-O8 28/28);
  - round 9's (`judge_r9_mutants.py`, `evidence/judge_r9_mutants.md`): 32 of 32 as expected; its 13 bypasses (M9-1 to
    M9-7, M9-3b, M9-11, M9-13 to M9-16) FAIL; M9-8 to M9-10 and P9-2 FAIL; P9-1 FAILS cleanly (no traceback); the
    controls M9-11c and M9-12 PASS; O9-1 to O9-12 keep round 9's verdicts (O9-7 and O9-8 FAIL, now with a true message);
  - fix pass 7's X8-1 to X8-8 (`new_mutants_r8_rerun.py`): each FAILS the live checker, PASSES `checker_r8_naive.py`,
    FAILS fix pass 7's checker and changes the outcome; 0 unexpected;
  - **new, executed** (`new_mutants_r9.py`, `evidence/new_mutants_r9.out`): N9-1 to N9-9 each FAIL the live checker and
    PASS fix pass 7's (each was a bypass of it); executed with stand-ins (a real pip where pip's behaviour is the
    point), the outcome changes for all eight run: N9-1 (a `*key` alias makes the PyPI job's `container`: the image's
    python3 passes the verify step and replaces both files), N9-2 (`runs-on: [self-hosted, ubuntu-latest]`: the same on
    the TestPyPI job), N9-3 (flow-style `services`: the dist is swapped after its check), N9-4 (the install job's
    setup-python `with: *pyw` with `mirror`: rc 1 -> 0), N9-5 (the build job's setup-python `mirror`: its python3 runs
    Record SHA256SUMS, which records a wheel of its own, and the TestPyPI verify passes on it), N9-6 (`retention-days:
    9_0`: PyYAML 1.1 90, YamlDotNet delivers "9_0", upload-artifact's `parseInt` makes 9 days), N9-7 (the install
    job's `services: *svc`: a wheel not from TestPyPI installed and imported, rc 1 -> 0), N9-8 (a double-quoted step
    ending in two newlines after a final here-document: rc 1 -> 0); N9-9 (`environment: {name: pypi, deployment:
    false}`) not executable here. Controls C9-1 to C9-5 (timeouts, the `{name, url}` mapping, `0x5A`, "3.14",
    `!!int 90`) PASS.
- **4. the proof** (`checker_proof_r9.py`, built by `make_proof_r9.py` from fix pass 7's, `evidence/checker_proof_r9.log`):
  396 of 396: fix pass 6's 306 table cases, fix pass 7's 40 NEW8, 46 NEW9 and 4 command-line cases. Every earlier case
  keeps fix pass 7's expectation but three, **changed by design**, each stated on its row: PYa (PYTHONUNBUFFERED in the
  build job's own env: PASS -> FAIL, the build job carries no env; a build step's still may, PYb stays PASS), R46f
  (`defaults: {run: {working-directory: .}}` on a root package's build job: PASS -> FAIL, only a sub-package's build job
  carries defaults, as cascor's test pins; no port's root build job has one) and CH8b (`run: |+` ending in two newlines:
  PASS -> FAIL, m9-a). Fix pass 7's re-baselining is unchanged (43 PASS -> FAIL by design, 192 + 5 FAIL kept). NEW9:
  K9a-K9p (key sets: container, services, matrix, outputs, runs-on list and image, an alias key, republish timeout, a
  build-job env, an environment key, sub-package and root defaults; controls), S9a-S9h (setup-python), Y9a-Y9k (typing
  and tags), C9a-C9b (chomping), P9a-P9b (ASCII), B9a (the pins file named), N9a-N9d (shapes), E9a-E9b (true messages);
  CLI4: a workflow with a string step, then the template, on one command line: FAIL then PASS, exit 1, no traceback.
  Round 2's 43 (`run_proof43_r9.bash`): 29 of 43 as round 2 expected, C1 by design, 13 FAIL kept; 0 other changes.
- **5. round 9's YAML divergence fuzz, on the new checker** (copies of its drivers in `checker-r9/parsers/`, the keep
  filter the live checker's own file rule and loader): seed 9001, 1500 cases kept: libyaml, YamlDotNet 5.3.0, 16.3.0 and
  Node 0 differ; seed 424242, 3000 kept: libyaml and both YamlDotNets 0 differ, Node 7, the construct round 9 found (an
  escaped line break then an empty line; Node alone departs from the spec) (`evidence/fuzz_seed9001.out`,
  `fuzz_seed424242.out`). **Still no case where PyYAML and GitHub's lineage both parse and read different text.**
  Beyond the brief, a typing differential (`parsers/typing_diff.py`): GitHub's own typing rules, transcribed from
  `YamlObjectReader.cs` apart from the checker's code, applied to YamlDotNet 5.3.0's events, against the live loader,
  on 3320 documents (120 hand forms, 2000 random, 8 tags and 2 quote styles): 2453 agree, 861 both refuse, 0 refused
  by GitHub alone, 6 by the checker alone (hex and octal above 0x7FFFFFFF, by design), **0 divergences**
  (`evidence/typing_diff.out`).
- **6. lint** (`lint_checker_r9.bash`): pre-commit (juniper-ml's config, `--files` the checker and the pins file) 12
  passed, 0 failed, 14 skipped, both files unchanged; B914 0 sites; flake8 `--isolated` at 512 columns: 3 E203 (Black's
  slice spacing); `--help` exit 0.

**Found beyond the brief, not fixed (leads for round 10, unverified):**
- **Extra jobs are not judged, and an extra job can run beside the chain.** One with `needs: build` could, for example,
  upload an artifact named `<PUBLISH_PACKAGE>-dist` with upload-artifact's `overwrite: true` before the TestPyPI job
  downloads it; the dist and SHA256SUMS would then agree with each other, every template check would pass, and both
  indexes would receive files the build job never made. Not executed; whether a job of the same run can replace the
  artifact this way, and how the race resolves, is for round 10 to establish. A candidate rule: every extra job needs
  the PyPI job (it runs after the publish), or holds no `needs` on the build or TestPyPI jobs.
- The upload steps' own `env` and `with` beyond the four inputs checked (`skip-existing`, `attestations`,
  `packages-dir`, `repository-url`): a `TWINE_*` env key is not refused by the F4 rules.
- Item 23's residual: every action's `@ref` is dropped, so an action's code is whatever its ref names.

**Residual risk** (the docstring's "What this cannot see"): equality is all the pins prove; GitHub's server-side parser
was not run (its open-source lineage was, and agrees); an extra job is noted, never judged; the build job's steps up to
the build are each repository's own business; every action's `@ref` is not judged.

**Next:** round 10 (`tmp/sweep/ROUND10_BRIEF.md`), once, on the r8 -> r9 interdiffs. The stopping rule is unchanged: no
port until a COMPLETE round reports no BLOCKER and no MAJOR.

## Status (session `ffffd3`, 2026-11-24 15:05Z)

Fix pass 8 finished (checker `9cf16a2f…`, pins `d539f05f…` with the same 18 pins; manifest 7 paths). Round 10 (brief
`tmp/sweep/ROUND10_BRIEF.md`, a fresh reviewer) launched at 15:05Z; its report: `tmp/r10review/ROUND10_REPORT.md`. Record it
here as `## Round-10 review`. A COMPLETE round with no BLOCKER and no MAJOR clears the ports.

## Round-10 review (report: `tmp/r10review/ROUND10_REPORT.md`; session `ffffd3`'s subagent, finished 2026-11-24 ~15:50Z; brief `tmp/sweep/ROUND10_BRIEF.md`) -- COMPLETE

Verdict: 3 BLOCKER, 0 MAJOR, 1 MINOR, 2 NIT against the checker `9cf16a2f…` and pins `d539f05f…` (fix pass 8). Every
step done; GitHub itself unavailable (actions/runner `aea9aaa3` C# read; `@actions/workflow-parser` 0.3.61 run; R10-6 and
R10-8 not executable here; R10-5 and R10-7 with stand-ins, R10-5's race untimed). **Fix pass 8's own code held** (job key
sets, setup-python, YAML 1.2 typing, ASCII and newline rules; all 18 pins re-derive equal through GitHub's TypeScript
parser). The three BLOCKERs sit one level further out. The stopping rule applies: fix pass 9, then round 11.

| id | sev | where (checker `9cf16a2f…`) | finding | disposition |
|---|---|---|---|---|
| B10-1 | BLOCKER | upload step `with` `:1125-1137` | Only four literal input names are read, but GitHub matches input names case-insensitively and evaluates expression KEYS, and the pinned publish action uses its deprecated `repository_url` when `repository-url` is empty. R10-1 (`repository_url:`), R10-2 (`Repository-URL:`), R10-3 (`${{ 'repository-url' }}:`) PASS; executed, the action's own `oidc-exchange.py` sends the PyPI job's OIDC token (audience `pypi`) to the named host. R10-4: `Skip-Existing: true`, `${{ 'attestations' }}: false` defeat two existing rules. | FIX PASS 9: the upload step exactly `{name, uses, with}`, its `with` an exact set of literal keys (as cascor's own test pins); refuse any key that is not exactly a template key (case-sensitive) and any expression key. |
| B10-2 | BLOCKER | extra jobs (noted, never judged) | R10-5 (executed, stand-ins): an extra job with `upload-artifact` `overwrite: true` replaces the build's artifact; every template check passes and both indexes get files the build never made (`testpypi` has no reviewer or wait timer: a race, untimed on GitHub). R10-6: the same through a reusable workflow with `secrets: inherit` (never read). R10-7 (executed): even after the PyPI job, an extra job can leave a 0.14.1 artifact that "Re-run failed jobs" publishes without any install check, so "every extra job needs the PyPI job" is not enough. | FIX PASS 9: refuse every extra job except an exact allow-list: today only juniper-data's `notify-consumers`, its called workflow pinned by sha256. |
| B10-3 | BLOCKER (a documented residual: SWEEP item 23 dropped `@ref` on purpose) | `uses:` compared by name | R10-8 PASSES with `actions/download-artifact@main`, or the publish action at a commit existing only in a fork (GitHub's API serves that fork commit, with a different `action.yml`, under the upstream name; whether `uses:` resolves it the same way is unverified). | THE OWNER'S RULING (asked 2026-11-24 ~15:55Z): pin each action's SHA in the credential-holding jobs, or accept the residual in writing. |
| m10-a | MINOR | `main()` catch-all | A deeply nested file (RecursionError) or a lone surrogate (UnicodeEncodeError) still crashes `main()`: exit 1 (fails closed), but later workflows on the command line go unjudged, contrary to fix pass 8's claim. | FIX PASS 9: catch per workflow, report, go on. |
| n10-a/b | NIT | messages | `runs-on: [ubuntu-latest]` and `persist-credentials: "false"` are refused with reasons untrue for those forms (no port writes either). | FIX PASS 9: true messages. |

Round 10's sketch `tmp/r10review/candidate_rules_r10.py` refuses R10-1..R10-9 and admits cascor's three and all 15
simulations. **Outside the checker** (for the template): no publish job ties the version in SHA256SUMS to the release
tag, which is what lets R10-7 publish 0.14.1 from a v0.14.0 run: SWEEP item 28 (M5), deferred, now with a concrete
exploit path; record it in plan v1.15.18.

## The owner's ruling on action refs (B10-3; answered by 2026-11-24T21:16:47Z; session `ffffd3`'s dialog, header "Action refs")

**Answer, verbatim: "Pin template SHAs (Recommended)"**, whose option text read: "In the jobs that hold id-token
(TestPyPI, PyPI, republish) and the jobs they need, every uses: must equal the template's exact owner/repo@<40-hex SHA>.
A Dependabot bump in a port repo then fails this cross-repo check until cascor's template takes the same bump; each
repo's own CI keeps item 23's ref-free digests, so no repo's CI is affected." Not chosen: "Any full SHA" and "Accept
the residual". Fix pass 9 implements it with B10-1, B10-2, m10-a and the NITs (brief `tmp/sweep/FIXPASS9_BRIEF.md`).

## Fix pass 9 (round 10's fixes and the action-refs ruling; checker-r10)

The executor reported this: the final message of session `d935c226`'s subagent for fix pass 9 (orchestrator `ffffd3`,
brief `tmp/sweep/FIXPASS9_BRIEF.md`), 2026-11-24 21:20Z to 22:23Z (times from `date -u`). Written: the checker, the
manifest, this section, `tmp/sweep/ROUND11_BRIEF.md` and new files under `tmp/sweep/checker-r10/`. **The pins file is
unchanged** (`d539f05f…`), and **no allow-list data file was added**: the extra-job allow-list is `EXTRA_JOBS`, a
constant of the checker, so the manifest keeps its seven paths. The writer, cascor's tree, every workflow, every port,
fix pass 8's tools and every earlier review directory (round 10's included) are untouched
(`checker-r10/evidence/untouched_r10.after-finish.out`, run after `finish_r10.bash`: no file outside the allowed outputs
is newer than this pass's first, no `__pycache__` outside `checker-r10/`, none in it outside the stand-in venvs, whose
1429 are pip's own, and the manifest 7 of 7 OK; the final run's own `untouched_r10.out` shows 6 of 7, taken before the
manifest was regenerated). Every driver is in `tmp/sweep/checker-r10/` beside its evidence
(`evidence/`): `rerun_all_r10.bash` re-runs every step in order (`evidence/rerun_all.out`, 2026-11-24T22:13:02Z to
2026-11-24T22:22:00Z), `finish_r10.bash` freezes the outputs and writes the interdiffs and the manifest. Fix pass 8's drivers
were copied by `adapt_r10.py` (exact, asserted edits; each copy's docstring names them). Nothing was deleted: the
development runs before the final one were moved aside with `mv` and are kept (suffixes `.pre`, `.run1` to `.run4`; the
retention rule), and every copied driver that deleted its output directory now refuses an existing one. The mutants are
negative test cases for this CI checker, run on this host only with stand-ins; nothing was sent anywhere but 127.0.0.1.

**Versions.**
- Checker: `9cf16a2f13152ddc75ce2f695758a6f5df95f93c713b347b46adc5959c157bb9` (as round 10 reviewed it, saved before
  any edit as `checker-r10/checker_r9_as_reviewed.py`) -> `23707ac6de0b351291372ec7a3c07eb2f328c2200d80f831dacf4976e393ba35`, 1172 -> 1439
  lines (91921 -> 116390 bytes); frozen as `checker-r10/checker_r10_as_delivered.py`.
- Interdiff: `checker-r10/checker_r9_to_r10.diff`, 489 lines, +305/-38, sha256 `f53c070e5f11d3f331304f062abe686530c72d383ea4cf7801e25d5956a62f16`
  (`evidence/interdiff.log`).
- Pins file: `d539f05fbd6666d4311fc57cfbf2a4680bfb4ca498b983dc7ccb93c4878a69b3` (saved as
  `checker-r10/pins_r9_as_reviewed.json`), unchanged; frozen as `checker-r10/pins_r10_as_delivered.json`;
  `checker-r10/pins_r9_to_r10.diff` is empty (0 lines, sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).
- Manifest: fix pass 8's kept as `tmp/arc/sweep_scripts.r10.sha256` (copied before any edit; `ba75d4c7…`);
  `tmp/arc/sweep_scripts.sha256` regenerated over the same seven paths (sha256 `e701709e2b11585f30511e96f9823c28c9c44e5b405b10232713b6636ca3f42d`): only the checker's
  line changes; the pins file's stays `d539f05f…` and the writer's `c47940ad…`; `sha256sum -c` passes
  (`evidence/manifest.log`).
- juniper-cascor: `main` re-fetched read-only at 21:26:47Z, still `b5b28dc3` (#779), its three publishers byte-identical
  to the landing tree. juniper-data: `main` `6b734fd9` (#551) fetched read-only the same minute; its publish.yml's
  `notify-consumers` job equals the simulation's, and its `notify-consumers.yml` is sha256 `e17ddc9b…`, 11039 bytes,
  blob `ab0cade2`, the bytes round 10 read (`evidence/fetch_main_r10.log`).

**Round 10's findings, each closed** (the decisions are in the checker's docstring, § "Fix pass 9: upload inputs, extra
jobs and action SHAs"):
- **B10-1** (`upload_problems`, `UPLOAD_STEP_KEYS`, `UPLOAD_OPTIONAL_INPUTS`): each TestPyPI and PyPI upload step holds
  exactly `name`, `uses` and `with`, and its `with` exactly the template's inputs under their literal names with the
  template's values as GitHub types them (TestPyPI `repository-url: https://test.pypi.org/legacy/` and `packages-dir:
  ${{ env.PUBLISH_DIST_DIR }}/`; PyPI `packages-dir` alone), read from the template given (`template()` refuses one
  whose uploads are not so). A port may add `verbose` and `attestations`, each only the boolean true. A key equal to an
  input but for case or `-`/`_`, an expression key, a key that is not text, a missing input and any other input each
  fail with their own message, naming the pinned action's five deprecated underscore aliases (read from its action.yml
  at 7245906f: `repository_url`, `packages_dir`, `verify_metadata`, `skip_existing`, `print_hash`, each read when the
  kebab-case input is empty). The four earlier input rules stay (their messages), now robust to a `with` that is not a
  mapping. Every other step of the TestPyPI, PyPI and republish jobs is a template step compared whole, so every step
  of a job holding id-token is held exactly. **Reading of "the template's exact set"** (recorded as a deviation below):
  the template's keys plus the two optional ones, because cascor's own sub-package publishers (pinned by cascor's test,
  `UPLOAD_INPUTS`) add `verbose`, and three simulations add `attestations: true`; no publisher of the 18 adds any other.
  Beyond the brief (round 10's O-2): `document_problems` refuses a mapping key holding `${{` anywhere in the workflow
  (no template, port or simulation holds one: `evidence/survey_fp9.out`).
- **B10-2** (`extra_job_problems`, `EXTRA_JOBS`): every job outside the chain's five is refused, unless the allow-list
  holds it for (`--repo`, the workflow file's name, the job id), compared whole as GitHub types it; its called reusable
  workflow is read beside the workflow (a local `./.github/workflows/<file>` call runs that file at the caller's
  commit) and compared by sha256, and a missing called file fails with a message saying to fetch it with the workflow.
  **The 15 simulations need no other extra job** (`evidence/survey_fp9.out`: juniper-data's `notify-consumers` is the
  only job outside the chain in cascor's three, the 15 simulations and every repository's current workflows).
- **B10-3, the owner's ruling "Pin template SHAs"** (`uses_problems`, `PINNED_USES`, `template()`): every `uses:` of the
  build, TestPyPI, install, PyPI and republish jobs equals the template's exact `owner/repo@<SHA>` for an action the
  template's job of that kind uses; another ref (a tag, a branch, a short SHA, another commit, upper-case hex), another
  owner, a local action, a container action or an action the template's job does not use is refused. The template is
  refused (exit 1, nothing checked) when a `uses:` of its chain is not `owner/repo@<40 lowercase hex>` or it pins one
  action at two refs. **Deviation:** the install job admits `INSTALL_ACTIONS` (setup-python and checkout) at the
  template's SHAs, not the root template's install job's set alone (setup-python): cascor's own sub-package publishers'
  install jobs use a sparse checkout, and 17 of the 18 publishers' install jobs use checkout.
- **m10-a**: `main()` judges, labels and prints each workflow inside a catch-all (a crash fails that workflow, never
  passes it, and the next is judged); stdout and stderr are reconfigured with `backslashreplace`; `check()` reads a
  `RecursionError` at load as a load failure; `document_problems` refuses a lone surrogate in any key or string (beyond
  round 10's minimum, as its fix suggested; walked without recursion). Exit status 1 when any workflow failed or crashed.
  Found while testing: under this host's C.UTF-8 locale Python's stdout uses `surrogateescape`, so fix pass 8's checker
  wrote a lone U+DC80..U+DCFF as a raw byte (invalid UTF-8 in its output) and stopped only on the others; now every
  surrogate is printed as an escape.
- **n10-a, n10-b**: `runs_on_problem` gives one message, true of every form refused (the string `ubuntu-latest`, as the
  template writes it, a one-label list naming it included), on the build, TestPyPI, install and PyPI jobs; the install
  checkout's message says what the step gives (or that it gives nothing) and that any form but the boolean false is
  refused, the text "false" included.
- **Outside the checker, recorded only**: R10-7's root cause, that no publish job ties the version in SHA256SUMS to the
  release tag (SWEEP item 28, M5, deferred), is the template's. Fix pass 9's N10-6 shows a second path to it, through an
  allow-listed job's called file and "Re-run all jobs" (round 10's lead 6), which the called file's sha256 pin closes
  for the checker; the template is unchanged. Record it in plan v1.15.18.

**The extra-job allow-list (`EXTRA_JOBS`), whole.** One entry: (`juniper-data`, `publish.yml`, `notify-consumers`) ->
`{name: Notify consumer repos, needs: pypi, permissions: {}, uses: ./.github/workflows/notify-consumers.yml, with:
{version: ${{ github.event.release.tag_name }}}, secrets: {CROSS_REPO_DISPATCH_TOKEN: ${{
secrets.CROSS_REPO_DISPATCH_TOKEN }}}}`, calling `notify-consumers.yml` at sha256
`e17ddc9b3ac99d87600c99835b2c87bc16f252034f966645975c0b776ec8e078` (juniper-data `main` `6b734fd9`: one job, `dispatch`,
`permissions: {}`, a two-repository matrix, two run steps that POST and then poll GitHub's API with the named secret; no
`uses:` step).

**Per-port ref changes under the ruling: none.** Every `uses:` of the five chain jobs in all 15 simulations, cascor's
three publishers and every repository's current publish workflows (round 9's fetch) is one of the template's five
(`actions/checkout@3d3c42e5…`, `actions/setup-python@6d4fd22b…`, `actions/upload-artifact@cf430e03…`,
`actions/download-artifact@9000827c…`, `pypa/gh-action-pypi-publish@7245906f…`; `evidence/survey_fp9.out`), so no
ref-corrected copy was needed and none was made. **One port-procedure change, for juniper-data's review:** the check of
its port needs `notify-consumers.yml` beside `publish.yml`; `fetch_pr_files.py --pr N` fetches only the files the pull
request changes, so name `.github/workflows/notify-consumers.yml` too (a missing file FAILS with that message). A later
change to `notify-consumers.yml` fails the check until `EXTRA_JOBS`'s sha256 is updated through review; a Dependabot
bump of an action in a port's repository fails it until cascor's template takes the same bump (the ruling).

**Results** (`evidence/rerun_all.out` unless named):
- **1. cascor's three:** 3 of 3 from the landing tree, from `f5ed3017` and from `main` (`evidence/checks_cascor.log`).
- **2. the 15 simulations:** 15 of 15 PASS (`evidence/port_sim_table.md`; fix pass 8's checker PASSES all 15 too);
  regenerated by round 2's probes they equal the seeds byte for byte (0 diff lines). The probes' own run: 18 PASS / 7
  FAIL among the 25 variants, fix pass 8's 6 and juniper-data's [faithful], by design: the probe writes no
  `notify-consumers.yml` beside it (`run_port_sim_r10.bash` then places juniper-data's, as its tree holds it, before the
  table). **The 18 pins re-derive equal** (`evidence/port_sim_rederive_pins.out`; its "ends with newline: False" is the
  inherited driver bug).
- **3. every mutant set:**
  - earlier sets (`judge_all_r10.py`, `evidence/judge_all_r10.md`): every row keeps fix pass 8's recorded verdict, 0
    moved, 0 findings (r5 24/24 … r8-O8 28/28);
  - round 9's (`judge_r9_mutants_r10.py`): 32 of 32; its 13 bypasses FAIL; **M9-12 PASS -> FAIL by design** (B10-2: a
    control holding an extra job, `extra-echo`);
  - fix pass 7's X8-1 to X8-8: each FAILS the live checker, PASSES `checker_r8_naive.py`, FAILS fix pass 8's; 0
    unexpected; fix pass 8's N9-1 to N9-9: each FAILS the live checker and PASSES fix pass 7's, executed as before;
    C9-1 to C9-5 PASS; 0 unexpected;
  - round 10's (`judge_r10_mutants.py`, `evidence/judge_r10_mutants.md`): R10-1 to R10-8 FAIL, each naming fix pass 9's
    rule (R10-1, R10-2: an input the template's upload does not give; R10-3: the expression key, twice; R10-4:
    `Skip-Existing` not an input the template gives, and the expression key; R10-5 to R10-7: an extra job; R10-8: both
    refs); R10-9 FAIL as before; R10-10 and R10-11 FAIL with the template judged after them (exit 1, [FAIL, PASS], no
    traceback; fix pass 8's stopped with a traceback); C10-0 PASS; O10-1 to O10-14 keep round 10's verdicts but
    **O10-7 (an extra job) and O10-8 (`print-hash: true`) PASS -> FAIL by design** (B10-2, B10-1); O10-11 and O10-13
    FAIL with true messages; 0 findings;
  - **new, executed** (`new_mutants_r10.py`, `evidence/new_mutants_r10.out`): N10-1 to N10-16 each FAIL the live checker
    and PASS fix pass 8's (N10-13 stops fix pass 8's with a traceback); executed with stand-ins, **the outcome changes
    for 7**: N10-2 (`!!str REPOSITORY_URL` on the PyPI upload) and N10-16 (`"repository\x5furl"`, an escaped key): the
    action's own `oidc-exchange.py` sends the PyPI job's OIDC token to the stand-in index the workflow names; N10-3
    (`Skip_Existing: true`): twine-upload.sh runs `--skip-existing`; N10-4 (an extra job named "Build and Validate") and
    N10-5 (an extra job calling a LOCAL reusable workflow): both indexes receive a wheel the build job never made; N10-6
    (juniper-data's allow-listed job, exact, its called `notify-consumers.yml` gaining a job that leaves a 0.14.1
    `juniper-data-dist` after the PyPI job, then "Re-run all jobs"): the template's own reuse step reuses it, the install
    check passes on the tag's 0.14.0, and PyPI receives 0.14.1, never install-checked (control C10-2, the called file
    unchanged: attempt 2 stops at TestPyPI's refusal of an existing file name); N10-13 (a lone `\ud83d` in a build
    step's name, then the template): fix pass 8's stops with a traceback, the template unjudged; the live checker FAILS
    it and PASSES the template, exit 1. **N10-1** (a `with` key through an alias) is not a bypass on GitHub: its
    TypeScript parser refuses the file ("Unexpected value 'undefined'"); the checker's refusal is defence in depth.
    Not executable here (GitHub resolves refs and secrets): N10-7 (`secrets: inherit`), N10-8 (a short SHA), N10-9
    (another owner at the template's SHA), N10-10 (a tag), N10-11 (`actions/cache` in the build job), N10-12 (the
    republish job's download at `@main`), N10-14 (an `id` on the upload step), N10-15 (an expression key in the build
    checkout's `with`). Controls C10-1 (the template), C10-2 and C10-3 (cascor's publish-cascor-model.yml, `verbose:
    true`) PASS.
- **4. the proof** (`checker_proof_r10.py`, built by `make_proof_r10.py` from fix pass 8's, `evidence/checker_proof_r10.log`):
  432 of 432: fix pass 6's 306, fix pass 7's 40 NEW8, fix pass 8's 46 NEW9, 33 NEW10 and 7
  command-line cases. **Seven expectations changed, each a message, no verdict**, each stated on its row: B5ap, B5aq,
  B5ar (the build job's runs-on message, n10-a), K9d, K9e (the publish jobs', n10-a), Y9j (`persist-credentials: no`,
  n10-b), N9d (the catch-all's message, m10-a). Fix pass 7's and 8's re-baselining unchanged (43 / 192 / 5; PYa, R46f,
  CH8b). NEW10: U10a-U10n (upload inputs: the alias name, case, expression key, step key, value, text "true",
  `attestations: TRUE` and verbose+attestations controls, a missing input, `password`, an integer key, a flow mapping
  control, an expression key elsewhere, cascor's model publisher control), X10a-X10g (extra jobs, juniper-data with and
  without its called file, the file changed, its job changed, its job in cascor's publisher, a second "Publish to
  TestPyPI"), A10a-A10f (a tag, upper-case hex, another commit, a container action, a local action, another owner),
  M10a (a lone surrogate), R10a-R10c and P10a-P10b (true messages). CLI5: a workflow nested 1000 deep, then the
  template: FAIL (RecursionError) then PASS, no traceback; CLI6, CLI7: a template at `@v8`, and one pinning
  setup-python at two refs: refused, nothing checked. Round 2's 43 (`run_proof43_r10.bash`,
  `evidence/proof43_classes.out`): 26 as round 2 expected, C1 and 13 FAIL kept (fix pass 7), **K1 and K2 PASS -> FAIL
  by design** (item 23's own cases, a Dependabot bump in one publisher only: the owner's ruling refuses them), R19 FAIL
  kept with n10-b's message; 0 other changes.
- **5. round 9's YAML divergence fuzz and fix pass 8's typing differential, on the new checker** (copies in
  `checker-r10/parsers/`): seed 9001, 1500 kept: libyaml, YamlDotNet 5.3.0, 16.3.0 and Node 0 differ; seed 424242,
  3000 kept: libyaml and both YamlDotNets 0, Node 7 (round 9's construct); typing differential, 3320 documents: 2453
  agree, 861 both refuse, 6 refused by the checker alone (hex and octal above 0x7FFFFFFF), 0 by GitHub alone, **0
  divergences** (`evidence/fuzz_*.out`). The loader is unchanged by this pass.
- **6. lint** (`lint_checker_r10.bash`): pre-commit (juniper-ml's config, `--files` the checker and the pins file) 12
  passed, 0 failed, 14 skipped, both files unchanged; B914 0 sites; flake8 `--isolated` at 512 columns: 3 E203 (Black's
  slice spacing, as before); `--help` exit 0.

**Deviations from the brief.**
- B10-1's "the template's exact set of literal keys" is read as the template's keys and values plus `verbose` and
  `attestations`, each only the boolean true: a literal reading refuses cascor's own two sub-package publishers and 12
  of the 15 simulations. `print-hash` is refused (no publisher uses it; round 10's O10-8 now FAILS).
- B10-3's "a port step whose action the template does not use in that job is refused" is read with the install job's
  set widened to `INSTALL_ACTIONS` at the template's SHAs (above). The template's refs must be 40 LOWERCASE hex (as git
  writes a SHA), one ref per action: slightly stricter than "40 hex characters".
- Beyond the brief: the expression-key rule applies to every mapping key of the workflow (round 10's O-2); the lone
  surrogate rule applies to every string (round 10's own suggested fix for m10-a).
- Round 10's tools were copied, not run in place: `node/` (tsparse.mjs, inputs.mjs, their modules) and the execution
  methods of `r10_mutants.py`, re-written in `new_mutants_r10.py` with the package as a parameter.

**Found beyond the brief, not fixed (leads for round 11, unverified):**
- The build job's checkout's inputs (`token`, `repository`, `ref`, `path`) and its steps before the build are judged
  only by the actions they use; what they build stays each repository's business (the documented residual).
- A double-quoted escape can put a control or format character (`\x1b`, `​`) into a loaded string the raw-file
  rule never sees; pinned scripts and window steps refuse them, other strings do not (only lone surrogates are refused
  everywhere). No path to the credential is known.
- The allow-listed job's called file is read beside the workflow the operator passes; that it is the file GitHub runs
  rests on the operator fetching both at one commit.
- Round 10's lead 6, "Re-run all jobs" reusing any unexpired `<pkg>-dist`, is the template's: N10-6 executed it through
  a changed called file; with the file pinned, no job of an admitted port can leave another artifact.

**Residual risk** (the docstring's "What this cannot see"): equality is all the pins prove, and the called workflow's
sha256 likewise; GitHub's server-side parser was not run (its open-source lineages were, and agree); what an action does
at the template's SHA is the template's review's; the build job's steps up to the build are each repository's own
business; SHA256SUMS' version is not tied to the tag (SWEEP item 28, the template's).

**Next:** round 11 (`tmp/sweep/ROUND11_BRIEF.md`), once, on the r9 -> r10 interdiff. The stopping rule is unchanged: no
port until a COMPLETE round reports no BLOCKER and no MAJOR.

**Correction to this section's opening (the file is append-only):** `evidence/rerun_all.out` ran from 2026-11-24T22:13:02Z to 2026-11-24T22:22:07Z; 22:22:00Z above is the fuzz step's own finish, which `fill_docs_r10.py`'s pattern matched first. And the pass began just before 21:26:11Z, the time of its first written file (`checker-r10/survey_fp9.py`), the reviewed copies having been saved before it; 21:20Z is when its brief was written.

## Status (session `ffffd3`, 2026-11-24 22:24Z)

Fix pass 9 finished (checker `23707ac6…`, pins unchanged `d539f05f…`, manifest 7 paths; no per-port ref changes;
juniper-data's check needs `notify-consumers.yml` fetched beside `publish.yml`). Round 11 (brief `tmp/sweep/ROUND11_BRIEF.md`,
a fresh reviewer) launched at 22:24Z; its report: `tmp/r11review/ROUND11_REPORT.md`. Record it here as `## Round-11 review`.
Plan v1.15.18 also records round 10's template finding: no publish job ties SHA256SUMS's version to the release tag
(SWEEP item 28, M5), with R10-7 as its concrete path.

## Round-11 review (report: `tmp/r11review/ROUND11_REPORT.md`; session `ffffd3`'s subagent, 2026-11-24 22:25Z-23:05Z; brief `tmp/sweep/ROUND11_BRIEF.md`) -- COMPLETE

Verdict: 0 BLOCKER, 1 MAJOR, 4 MINOR, 5 NIT against the checker `23707ac6…` (fix pass 9). Every step done; limits:
GitHub unavailable (its TS parser 0.3.61 and the runner's `OrdinalIgnoreCase` input map run instead; M11-8, M11-10 not
executable); lint on byte-identical copies; juniper-data's own CI not read. One mtime change outside its directory (an
empty dir under `tmp/r9review/parsers/dotnet/metadata/`, by round 9's SDK). **Fix pass 9's own rules held.** The stopping
rule applies: fix pass 10, then round 12. The MAJOR is in what the checker PRINTS; its exit status stays correct.

| id | sev | where (checker `23707ac6…`) | finding | disposition |
|---|---|---|---|---|
| M11-A | MAJOR | `main()` `:1399-1401`, docstring `:239-243`; messages `:1247`, `:1220`, `:1197`, `:1273`, `:1057-1068`, `:1026`, `:1030`, `:1113`, `:1120`, `:1238`, `:1282`; printed `:1428-1429` | Messages interpolate loaded strings raw; a double-quoted `\x1b` or `\n` is printable ASCII in the file. M11-1: a refused workflow DISPLAYS `PASS … 1 of 1 pass` in a terminal and the FAIL line vanishes (tmux shows later lines concealed); M11-2: two workflows display `2 of 2 pass`; M11-3: newlines alone inject a `PASS` line and a count line. GitHub's TS parser accepts all three. Exit status stays 1. | FIX PASS 10: refuse, in every loaded string, any character other than printable text, tab or newline, and a newline in keys and in step/job names (all 37 files checked admit it); also print every workflow value with `!r` and escape C0/C1 in all output. |
| M11-B | MINOR | `document_problems` `:573-587`; loader `:488-493` | Aliases are walked as a tree: an alias bomb (49 KB, depth 9) runs past 120 s and the next workflow is never judged (fails closed; m10-a's claim untrue). | FIX PASS 10: refuse anchors and aliases at load (none of the 37 files uses one). |
| M11-C | MINOR | build job before the build (`:271-276`, R5-F4 `:67-68`, `uses_problems`) | M11-9: a `BASH_ENV` hook written to `$GITHUB_ENV` runs inside the unchanged `twine check` and adds a wheel the build never made; M11-12: `upload-artifact` at the template's SHA BEFORE the build, after "Re-run failed jobs", ships files never built or recorded. Both change the outcome (stand-ins); neither reaches an id-token job's code or credentials, only the artifact's bytes. | FIX PASS 10: admit `upload-artifact` only in the `Upload dist artifacts` step (all 37 admit it); refuse a write to `$GITHUB_ENV`/`$GITHUB_PATH` in the build job's own steps if every file admits it, else document; correct the docstring. |
| M11-D | MINOR | `:1126-1135`; reasoning `:55-58` | A workflow `concurrency` group shared with another workflow can cancel a publish run between uploads: M11-10 passes with `group: pr-budget-alarm`, which cascor's scheduled `pr-budget-alarm.yml` uses with `cancel-in-progress: true` (not executable here). | FIX PASS 10: the group must be exactly `<workflow file stem>-${{ github.ref_name }}` with `cancel-in-progress: false` (all 37 admit it); correct the reasoning. |
| M11-E | MINOR | docstring `:266-268` | The SHA pin does not bind the code that handles the token: the publish action runs its OIDC exchange, attestations and twine upload from `ghcr.io/pypa/gh-action-pypi-publish:<sha>`, a registry tag that can be re-pushed. | FIX PASS 10: correct the docstring; record as a residual for plan v1.15.18. |
| n11-a..e | NIT | messages, `template()` | CRLF-only called-file difference refused with an untrue message; `PyPA/…` (case) refused with untrue reasons; `needs: [pypi]` and `verbose: "true"` refused although harmless (by design); `installs` shadows a module function; the two-refs message's reason. | FIX PASS 10: true messages; rename the local; record n11-c as by design. |

**Sound (round 11):** every count of § "Fix pass 9" reproduced row for row; 15/15 simulations; cascor's three (landing
tree, `f5ed3017`, `main`); 18/18 pins re-derived with independent libyaml code; the runner's case folding gives no
look-alike hole (executed); the called workflow runs at the caller's commit; other workflows cannot swap the artifact
or mint a credential; 11 harmless forms pass.

## Fix pass 10 (round 11's fixes; checker-r11)

The executor reported this: the final message of session `d935c226`'s subagent for fix pass 10 (orchestrator `ffffd3`,
brief `tmp/sweep/FIXPASS10_BRIEF.md`), 2026-11-24T23:07:57Z to 2026-11-25T01:14:10Z, when this section was filled (it is appended last, after the check of
untouched files; times from `date -u` and file times: the
reviewed checker and fix pass 9's manifest were copied first, with `cp -p`, at 23:07:57Z; the first new file written
was `checker-r11/survey_fp10.py`, 23:17:52Z; the pins file's copy is dated 23:35:29Z, and the pins file is unchanged).
Written: the checker, the manifest, this section, `tmp/sweep/ROUND12_BRIEF.md` and new files under
`tmp/sweep/checker-r11/`. **The pins file is unchanged** (`d539f05f…`), so the manifest keeps its seven paths and only
the checker's line moves. The writer, cascor's tree, every workflow, every port, fix pass 9's directory and every
earlier review directory (round 11's included) are untouched (`checker-r11/evidence/untouched_r11.after-finish.out`,
run after `finish_r11.bash`: manifest 7 of 7 OK; `util/ad-hoc`'s own directory time moved, 41 ms after the checker's
last save, the Edit tool's rename, and no other file there is newer than this pass's first). Every driver is in
`tmp/sweep/checker-r11/` beside its evidence (`evidence/`):
`rerun_all_r11.bash` re-runs every step in order (`evidence/rerun_all.out`, 2026-11-25T01:00:13Z to 01:08:54Z),
`extras_r11.bash` then runs the evidence for the five linear rewrites below (`evidence/extras_r11.out`), and
`finish_r11.bash` freezes the outputs and writes the interdiffs and the manifest.

**Three full runs.** The first (2026-11-25T00:09:29Z to 00:18:10Z) tested `536cdc83…`; one docstring line then changed
(its cost figure read the development run's 48.1 s where the cited evidence measured 44.9 s), and its outputs are kept
as `.run1` (`aside_run1_r11.bash`; `evidence/compare_runs_r11.out`: 19 of 19 evidence files equal by their summary
lines). The second (00:19:16Z to 00:28:21Z) tested `26b6a70c…`, which `finish_r11.bash` froze as delivered. After it
this pass found five paths in M11-B's class that grew as the square of a file (below) and made each linear, and the
docstring's cost passage stopped quoting a range a re-run moves (it said "45 to 48 s"; the second run measured 48.5 s).
The second run's outputs and frozen copies are kept as `.run2` (`aside_run2_r11.bash`, `evidence/aside_run2_r11.out`:
51 moved, nothing deleted; the manifest copied as `checker-r11/sweep_scripts.run2.sha256`, `dbc85acc…`). The third
run, on the checker as delivered (`b807d3ca…`), is the record below; `evidence/compare_runs_r11b.out` compares it with the second: 17 of 19 evidence files equal by their summary lines, and the two that differ as expected, flake8's E203 count (3 -> 2: the rewrite of `line_problems` removed a slice) and the f-string audit's (88 distinct raw expressions in 219 fields -> 91 in 220: `shown()`'s and `place()`'s own parts). Fix pass 9's drivers were copied
by `adapt_r11.py` (exact, asserted path edits), then `adapt_r11_expectations.py` (two stated expectation changes,
below) and `adapt_r11_labels.py` (one column label). Nothing was deleted: the development runs were moved aside with
`mv` and are kept (suffixes `.dev`, `.dev1`, `.dev2`, `.pre`, `.run1`, `.run2`; the retention rule), the tmux socket
is left where tmux made it, and every copied driver refuses an existing output. The mutants are negative test cases
for this CI checker, run on this host only with stand-ins and a local terminal emulator; nothing was sent anywhere but
127.0.0.1, and the only network use was read-only `gh api` GETs (`fetch_main_r11.bash`).

**Versions.**
- Checker: `23707ac6de0b351291372ec7a3c07eb2f328c2200d80f831dacf4976e393ba35` (as round 11 reviewed it, saved before any
  edit as `checker-r11/checker_r10_as_reviewed.py`) -> `b807d3ca9c45f14ba3a5771c562fecb5df5f82dc905fb294b88c5622628ea92d`,
  1439 -> 1750 lines (116390 -> 144784 bytes); frozen as `checker-r11/checker_r11_as_delivered.py`. The first delivery
  (`26b6a70c519f52175e9966d9e29de2cd52c0e8e19f136db455e96ab5dada8aad`, 1680 lines) is kept as
  `checker_r11_as_delivered.run2.py`, with its interdiff as `checker_r10_to_r11.run2.diff`.
- Interdiff: `checker-r11/checker_r10_to_r11.diff`, 1106 lines, +451/-140, sha256 `fd6fb7c08f677d6d02d56287bd27f6d2f5297a9fa017de76b56efbd38f94e1a3`
  (`evidence/interdiff.log`).
- Pins file: `d539f05fbd6666d4311fc57cfbf2a4680bfb4ca498b983dc7ccb93c4878a69b3` (saved as `checker-r11/pins_r10_as_reviewed.json`),
  unchanged; frozen as `checker-r11/pins_r11_as_delivered.json`; `checker-r11/pins_r10_to_r11.diff` is empty (0 lines,
  sha256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`).
- Manifest: fix pass 9's kept as `tmp/arc/sweep_scripts.r11.sha256` (copied before any edit; `e701709e…`);
  `tmp/arc/sweep_scripts.sha256` regenerated over the same seven paths (sha256 `40f09c653bec74af59d0bb34bb5d87027c7bcfdba6f2b964ffda2ad1937dc16b`): only the checker's
  line changes; the pins file's stays `d539f05f…` and the writer's `c47940ad…`; `sha256sum -c` passes
  (`evidence/manifest.log`).
- juniper-cascor `main` re-fetched read-only at 2026-11-24T23:36:49Z: now `ea8e68b8` (#773, a CI bump), its three
  publishers byte-identical to the landing tree. juniper-data `main` `607bae32` (#550): its `publish.yml` and
  `notify-consumers.yml` byte-identical to fix pass 9's fetch, the called file still sha256 `e17ddc9b…`, 11039 bytes,
  blob `ab0cade2` (`evidence/fetch_main_r11.log`).

**Before any edit** (`survey_fp10.py`, `evidence/survey_fp10.out`): over the 37 files round 11 listed, 0 hold a
character other than printable text, a tab or a newline in a loaded string, 0 a newline in a key or a workflow, job or
step name, 0 a tab in a key or name, 0 an anchor or alias, 0 an `upload-artifact` in the build job outside `Upload dist
artifacts`, **0 a build-job run step naming `GITHUB_ENV` or `GITHUB_PATH`** (round 11 had not checked this; no other
job's run step names either), 0 a concurrency form other than absent (15) or exactly `<stem>-${{ github.ref_name }}`
with `cancel-in-progress: false` (22, 11 publishers), 0 a job concurrency, 0 an action owner in upper case; the pins
file holds no string with a character other than printable text, and no tab. So every rule the brief made conditional
is admitted by all 37, and each was made. `cost_probe_fp10.py` (`evidence/cost_probe_fp10.out`) found M11-B's class
without aliases: a flat mapping of 16,000 keys loaded in 2.73 s and grew as its square (the duplicate check scanned a
list), and `bash -n` costs about 2.8 ms per run step.

**Round 11's findings, each closed** (the decisions are in the checker's docstring, § "Fix pass 10: what is printed,
aliases, the build job's upload and file commands, concurrency"):
- **M11-A (MAJOR)**, two ways, as the brief asked:
  - at load (`document_problems`, `unprintable`): every loaded string, keys and values at every depth, is refused when
    it holds a character other than printable text, a tab or a newline (code points and places listed, at most 12, the
    rest counted; a lone surrogate keeps fix pass 9's message and is not listed twice); a newline in any mapping key and
    in the `name` of the workflow, a job or a step is refused. Beyond the brief, the workflow's own `name` is in that set
    (the ceremony reads it as one line) and the pins file is held to the same (`load_pins`: every field and the `about`
    printable text alone; a pin's lines keep `script_problems`, which admits a tab), since a JSON `\u001b` escape loads
    a control character from an ASCII file and messages print a pin's package;
  - at output: every workflow-derived value a message names goes through `shown()` (a string of `[A-Za-z0-9._/@+-]` as
    it stands, every other value as its repr; since the five rewrites, at most 200 characters of a string or of a repr,
    then the count of the rest), or `!r`, or a list's or a mapping's `str()` (its repr), or `visible()` for a YAML
    error's, a crash's and bash's own text; `main()` passes every line it prints, stdout and stderr, through `visible()`
    (every character `str.isprintable()` rejects written as Python's escape: C0, C1, DEL, line and paragraph
    separators, format characters, surrogates), prints a message's further lines (a pin mismatch's diff) indented by
    eight spaces, and catches a refused pins file's or template's `SystemExit` to print it so. **Reading of "with `!r`,
    or an equivalent escape"** (recorded as a deviation below): a plain token is printed bare, because its repr would
    add only quotes and it can hold nothing a terminal or a reader takes for structure; job ids, env keys and paths are
    such tokens in every real port, so 0 of the proof's 432 earlier expectations moved for them, and the five that
    moved are names holding a space. `audit_interpolations_r11.py` (`evidence/audit_interpolations_r11.out`) lists
    every f-string field still printed raw: constants, counts, operator paths, lists and mappings (whose str() is their
    repr), strings built from `shown()`, `shown()`'s and `place()`'s own parts (the cut text and its count; a place,
    which messages print only inside a list, as its repr), and a pin mismatch's diff lines, which only reach printing
    after `script_problems` has held them to printable text and tabs.
  - **M11-1, M11-2 and M11-3 are refused**, and in tmux 3.6 (`render_tmux_fp10.bash`, `screen_check_fp10.py`,
    `evidence/screen_check_fp10.out`) the displayed text now matches the verdict: the real FAIL lines and the real
    summary are visible, no cell is concealed, no visible row begins `PASS `, and the line printed before the run is
    still in the scrollback. Under fix pass 9's checker the same files still display `PASS … 1 of 1 pass` (M11-1),
    `PASS, PASS … 2 of 2 pass` (M11-2), an injected PASS row and two summaries (M11-3), and in M11-1, M11-2, N11-1 and
    N11-10 the exit-status row itself is concealed.
- **M11-B (MINOR)** (`UniqueKeyLoader.compose_node`): an alias, or an anchor on any node, is refused before the node is
  composed. M11-4's bombs (depth 3 to 6) fail in 0.15-0.17 s each (round 11: 0.28-8.28 s), and depth 9 then the
  template gives FAIL then PASS, `1 of 2 pass`, in 0.23 s (round 11: nothing printed in 120 s). **Beyond the
  brief, the same class without aliases:** the duplicate-key check reads sets (a list made it quadratic), and
  `read_text` refuses a workflow file over `MAX_WORKFLOW_BYTES` (256 KiB, five times the largest publisher's 52,353
  bytes) before it is parsed, reading at most that and one byte. **After the second full run, five more paths of the
  class, each made linear and giving what it gave** (`cost_probe_square_fp10.py`: `evidence/cost_probe_square_fp10.before.out`
  on the first delivery and `.after.out` on the live checker, each case's file then the template, as an operator runs
  them; `equivalence_fp10.py`, `evidence/equivalence_fp10.out`, the old code against the new, input by input):
  - `document_problems` built every node's place whole, so a key's text was copied into the place of each node
    beneath it (fix pass 9's walk), and fix pass 10's own newline rule copied a job's id into the place of each of its
    steps' names. Case C, an explicit top-level key of 40,000 characters over a list of 20,000 items (a file of
    128 KB), held 795 MB (after: 40 MB, and 64 MB at the bound); for the first delivery at the bound (100,000 over 56,927) the arithmetic is gigabytes. Now
    `place()` cuts a place at `SHOWN_CHARS` (200) characters, then `...`, and the places are a list, so two cut alike
    are both counted;
  - a job's id was copied into the scope built for each of its steps (the env rule) and into each message naming the
    job. Case D, an explicit job id of 30,000 characters over 15,000 steps, held 463 MB (after: 43 MB, and 64 MB at the bound, 100,000 over 37,939). Now
    `shown()` prints at most 200 characters of a string, or of a repr, then `... (N more characters)`;
  - the `${{ }}` substitution before `bash -n` (`re.sub(r"\$\{\{.*?\}\}", …)`, from early passes) scanned from each
    `${{` to its line's end. Case A, one line of 40,000 `${{`, took 22.7 s (after: 0.5 s, and 0.6 s at the bound, 71,264). Now `expression_words`
    scans once, with the same result;
  - the window's check of a continuation into a blank line joined every later line for each such line (fix pass 6's
    wording for R7-3). Case B, 26,000 such pairs (256 KB), took 5.4 s (after: 1.4 s, and 1.5 s at the bound; 9.0 MB of messages in both,
    one per pair, linear). Now `line_problems` finds once, from the end, whether a later line holds text;
  - fix pass 10's own duplicate check compared a key that is a list or a mapping with each such key before it. Case E,
    10,000 list keys, took 3.5 s (after: 2.0 s, and 2.9 s at the bound, 14,998). Now `frozen()` holds each as a hashable value equal exactly when
    the two values are equal, in a set of its own.

  The equivalence: on the delivered checker (`b807d3ca…`) against the first delivery, 0 of 688,281 strings differ for `expression_words` (every string of up to 8 characters over `$ { } \n a`, and 200,000 random ones of tokens), 0 of 435,923 scripts for `line_problems`, 0 of 90,445 values of at most 200 characters for `shown()` (3,000 longer ones cut, printable and their rest counted truly), 0 of 30,000 documents for `document_problems` (a key of 1,000 characters and a job id of 500 have their places cut and every place counted), and 0 of 30,000 documents for `load_text`. Its first run found a slip of this pass's own: the rewrite of
  `document_problems`' message lost a space (`]:a double-quoted`; `evidence/equivalence_fp10.dev.out`), fixed before
  the third run. The cost left is `bash -n`, once per run step: the most the bound holds (case F, 42,762 single-pair
  `run:` mappings in a flow list) take 143.7 s, at 116 MB, and 14,254 block-style run steps 47.8 s
  (`cost_probe_live_fp10.out`; 44.9 s and 48.5 s in the first two runs); 6,288 env keys at the bound take about 1 s;
  the flat mapping grows linearly (2,000 to 16,000 keys: 0.11 to 0.83 s). So m10-a's claim now reads "a delay, bounded,
  never a stop", and the docstring says so without a figure a re-run moves. A template that does not load is refused
  with a message (it raised a traceback before).
- **M11-C (MINOR)**: `actions/upload-artifact` in the build job is admitted only as its `Upload dist artifacts` step
  (the template's, compared whole and last); a build step whose `run` or `env` names `GITHUB_ENV`, `GITHUB_PATH`,
  `github.env`, `github.path` or `_runner_file_commands`, in any case (`ENV_FILE_NAMES`), is refused, since all 37 files
  admit it (above). **M11-12 and M11-9 are refused**; so are this pass's N11-6a (a second name), N11-7a
  (`${{ github.env }}`), N11-7b (`$GITHUB_PATH`, a stand-in twine first on PATH) and N11-7c (a step env naming
  `github.env`), each of which PASSED fix pass 9's checker and, EXECUTED, changes the outcome (staged files never built
  nor recorded, or a wheel the build never made, reach both indexes); and N11-6b (a second step named `Upload dist
  artifacts`) and N11-6c (`Actions/Upload-Artifact`), which fix pass 9 already refused on other rules. The docstring's
  account of the steps before the build is corrected (R5-F4's "every level" is of the workflow's YAML; "What this
  cannot see" states $GITHUB_ENV, $GITHUB_PATH, a background process, a replaced tool, and a background
  `<PUBLISH_PACKAGE>-dist`). **The residual, documented:** the env-file rule reads text, so R11-1, an indirect name
  (`f=GITHUB_; f="${f}ENV"; ... >> "${!f}"`), PASSES and, executed, publishes a wheel the build never made (M11-9's
  outcome). Closing that class needs the build job's steps before the build pinned, as install scripts are (round 11's
  fix 3): an owner decision for plan v1.15.18.
- **M11-D (MINOR)** (`check()`): the workflow's `concurrency`, when present, is exactly `{group: <file stem>-${{
  github.ref_name }}, cancel-in-progress: false}`, compared with its types (so `cancel-in-progress: 0`, Python's 0 ==
  False, is refused), the form 22 of the 37 files write; the R4-4 reasoning at the old `:55-58` is corrected (the run
  queued NEXT decides, by its own setting). **M11-10 is refused**, and N11-5a to N11-5d (the ref, another publisher's
  group, `0`, the string form) and the proof's K11a to K11e. Residual, documented: another workflow of the repository
  can still name this group, or cancel the run through the API; availability only.
- **M11-E (MINOR)**: the docstring at the old `:266-268` now says the SHA pins the publish action's composite steps and
  the NAME of the image they run (`docker://ghcr.io/pypa/gh-action-pypi-publish:<the action's ref>`,
  `create-docker-action.py:16-20`), not the image, where the OIDC exchange, the attestations and twine run; recorded as
  a residual for plan v1.15.18 (accept it in writing, or record the image digest the template's review saw).
- **n11-a**: a called file whose sha256 differs is refused as "its bytes differ from the pinned file's (a change of line
  endings alone, which YAML reads alike, is refused all the same: the pin is of the bytes)" (O11-10, X11a). **n11-b**:
  an action in another case is refused as "the template's '<owner/repo>' in another case: GitHub reads an owner and a
  repository without regard to case, so it names that action" (M11-8, B11a, B11b, N11-6c), and `uploads()`, `checkouts()`
  and the install job's action check read the owner and repository without regard to case (`action_name`), so M11-8 no
  longer reports "has 0 uploads". **n11-c**: `needs: [pypi]` and `verbose: "true"` stay refused, by design, recorded in
  the docstring. **n11-d**: `template()`'s local is `install_jobs` (and `pin_mismatch`'s local `shown`, which would have
  shadowed the new helper, is `diff_lines`). **n11-e**: the two-refs refusal says the install job admits one ref of each
  of `INSTALL_ACTIONS`, and with two, which one would be arbitrary (CLI7 now requires those words).

**Results** (the third run: `evidence/rerun_all.out` unless named):
- **1. cascor's three:** 3 of 3 from the landing tree, from `f5ed3017` and from `main` `ea8e68b8`
  (`evidence/checks_cascor.log`).
- **2. the 15 simulations:** 15 of 15 PASS (`evidence/port_sim_table.md`; fix pass 9's checker PASSES all 15 too), with
  juniper-data's `notify-consumers.yml` beside it; regenerated by round 2's probes they equal fix pass 6's seeds byte for
  byte (0 diff lines). The probes' own run: 18 PASS / 7 FAIL among 25 variants, as fix pass 9 recorded (juniper-data's
  [faithful] needs its called file, placed before the table). **The 18 pins re-derive equal**
  (`evidence/port_sim_rederive_pins.out`).
- **3. every mutant set:**
  - earlier sets (`judge_all_r11.py`, `evidence/judge_all_r11.md`): every row keeps fix pass 9's recorded verdict, 0
    moved, 0 findings, each set's tally line for line fix pass 9's;
  - round 9's (`judge_r9_mutants_r11.py`): 32 of 32 as expected, 13 bypasses present;
  - X8-1 to X8-8 (`new_mutants_r8_rerun_r11.out`): each FAILS the live checker, PASSES `checker_r8_naive.py`, FAILS fix
    pass 9's; 0 unexpected. N9-1 to N9-9 (`new_mutants_r9_rerun_r11.out`): each FAILS the live checker and PASSES fix pass
    7's, every executed row as before; C9-1 to C9-5 PASS; 0 unexpected;
  - round 10's (`judge_r10_mutants_r11.py`): every row as fix pass 9 recorded it (O10-7, O10-8 moved by fix pass 9), 0
    findings; N10-1 to N10-16 (`new_mutants_r10_rerun_r11.out`): every row identical to fix pass 9's (7 executed with the
    outcome changing, 1 refused by GitHub's TypeScript parser, 8 not executable, controls PASS, 0 unexpected);
  - **round 11's** (`judge_r11_mutants.py`, `evidence/judge_r11_mutants.md`): C11-0, C11-2, C11-3 PASS; M11-1 to M11-3
    FAIL, each naming the load rule, printed as printable text alone, every line the checker's own, one summary, the last
    (fix pass 9's printed `FAIL, PASS`, `FAIL, PASS, PASS, FAIL` and `FAIL, PASS` verdict lines for them); M11-4 as
    above; M11-7 FAIL (as round 11 recorded), M11-8 FAIL with n11-b's message and never "has 0 uploads", M11-9, M11-10,
    M11-12 FAIL naming fix pass 10's rules (each PASSED fix pass 9), M11-11 PASS (round 11: not a bypass); O11-1 to O11-13
    keep round 11's verdicts (O11-4d, O11-9 by design, n11-c; O11-7 by design, B10-2; O11-10 with n11-a's message;
    O11-13 a real change); 0 findings;
  - **new, executed** (`new_mutants_r11.py`, `evidence/new_mutants_r11.out`): 21 negative tests FAIL the live checker as expected (N11-1, N11-2a, N11-2b, N11-3a, N11-3b, N11-4a, N11-4b, N11-5a to N11-5d, N11-6a to N11-6c, N11-7a to N11-7c, N11-8a, N11-9, N11-10, N11-11), 12 of which PASSED fix pass 9's checker (N11-2b, N11-3b, N11-4a, N11-4b, N11-5a, N11-5b, N11-5d, N11-6a, N11-7a, N11-7b, N11-7c, N11-8a); under fix pass 9's, N11-1, N11-2a, N11-3a and N11-10 printed raw control characters and N11-11 printed lines the workflow wrote. Executed with fix pass 9's stand-ins, N11-6a and N11-7a to N11-7c change the outcome (staged files, or a wheel the build never made, reach both indexes), each now refused; the residual probe R11-1 (an indirect `${!f}`) PASSES and, executed, changes the outcome, as documented; 6 controls PASS (C11-a to C11-e, N11-8b); 0 unexpected. N11-9 (12,000 keys) took 3.60 s on fix pass 9's checker, 1.53 s on the live one.
- **4. the proof** (`checker_proof_r11.py`, built by `make_proof_r11.py` from fix pass 9's, `evidence/checker_proof_r11.log`):
  479 of 479 cases as expected (306 of fix pass 6's table, 40 of fix pass 7's NEW8, 46 of fix pass 8's NEW9, 33 of fix pass 9's NEW10, 41 NEW11, 13 command-line). **Six expectations changed, each a message, no verdict**, each stated on its row: W6a, W6b, W6e,
  W6f, B7b (`build: step 'Check package' …`, a name with a space now printed as its repr, M11-A) and K9h (an alias:
  refused at load now, M11-B). CLI7 also requires n11-e's reason. Fix pass 7's, 8's and 9's re-baselining unchanged.
  NEW11 (41): C11a-C11j (the character rule: ESC, a C1 in a key, U+200B, U+202E, U+00A0, DEL, CR; a tab, printable
  non-ASCII and a tab in a run admitted), L11a-L11e (the newline rule: a step, a job and the workflow's name, a key; a
  newline in a run admitted), O11a-O11c (output: a string needs, a packages-dir and an env key printed as their repr),
  A11a-A11c (anchors on a scalar, a mapping with its alias, a sequence), U11a-U11c (upload-artifact), E11a-E11g (the
  file commands, E11g's own GITHUB_OUTPUT admitted), K11a-K11g (concurrency; the exact group and cascor's model
  publisher admitted), X11a (n11-a), B11a, B11b (n11-b). CLI8 (an alias bomb, then the template: FAIL, PASS within 30 s),
  CLI9 and CLI9b (one byte over the bound, then the template; exactly at it), CLI10 (a pins file holding ESC in a step:
  refused, printed escaped), CLI11 (a template holding an anchor: refused with a message, no traceback), CLI12 (M11-1's
  payload, then the template: printable text alone, every line the checker's own). The five rewrites add no proof row:
  `equivalence_fp10.py` is their evidence, and the proof's 479 rows pass on the delivery as on the first. Round 2's 43
  (`run_proof43_r11.bash`, `evidence/proof43_classes.out`): as fix pass 9 recorded, 0 other changes.
- **5. the fuzz and the typing differential** (copies in `checker-r11/parsers/`): seed 9001, 1500 kept: libyaml, YamlDotNet 5.3.0, 16.3.0 and Node 0 differ; seed 424242, 3000 kept: libyaml and both YamlDotNets 0, Node 7 (round 9's construct); typing differential, 3320 documents: 2453 agree, 861 both refuse, 6 refused by the checker alone, 0 by GitHub alone, **0 divergences** (`evidence/fuzz_*.out`). More cases were tried to keep as many (3066 and 6390, fix pass 9: 3052 and 6383): the fuzz alphabet holds `&a ` and `*a`, which the live loader now refuses, so those cases are not kept; the verdicts are unchanged.
- **6. lint** (`lint_checker_r11.bash`): pre-commit (juniper-ml's config, `--files` the checker and the pins file) 12 passed, 0 failed, 14 skipped, both files unchanged; B914 0 sites; flake8 `--isolated` at 512 columns: 2 E203 (Black's slice spacing; the first two runs' third, `lines[at + 1 :]` in `line_problems`, went with its rewrite; two over-long new messages were shortened in development); `--help` exit 0.
- **7. the f-string audit** (`audit_interpolations_r11.py`): 91 distinct raw expressions in 220 fields (88 in 219 before the rewrites; the three new are `shown()`'s cut text and its count, and `place()`'s part), each judged as above (`evidence/audit_interpolations_r11.out`).

**Deviations from the brief.**
- "Print every workflow-derived value with `!r`, or an equivalent escape" is read as above: `shown()` prints a plain
  token bare and everything else as its repr, and `visible()` escapes every character but printable text in every
  output line. A reviewer who wants every value quoted should say so: it would move no verdict, and the message of
  every rule that names a job id or an env key (not counted here).
- Beyond the brief: the workflow's `name` in the newline rule; the pins file's strings held printable; the size bound and
  the linear duplicate check (M11-B's class without aliases, measured before and after); a template that does not load
  refused with a message; `checkouts()` and the install job's action check read case-insensitively with `uploads()`
  (n11-b's reading applied where the same misreading stood); the env-file rule also names `github.env`, `github.path` and
  `_runner_file_commands`, and reads a step's `env` values as well as its `run`.
- Beyond the brief, after the second full run: the five paths made linear (M11-B above), a value or a place cut at
  `SHOWN_CHARS` (200) characters in a message, a third full run and `extras_r11.bash`. Each rewrite equals the code it
  replaced on every input `equivalence_fp10.py` tried; the cut changes a message only where a value or a place exceeds
  200 characters, which no template, port, simulation or earlier case's checked message holds (the third run's counts
  equal the second's but where stated).
- Two copied drivers' expectations changed, each stated in `adapt_r11_expectations.py`: the N9 re-run's stand-in
  runner reads a case through fix pass 9's loader (N9-1 holds an anchor; refusing it is the checker's verdict, which the
  judge rows show, not how GitHub's runner reads the file); N10-1's reason is now the anchor's. My own drivers read a
  summary anchored as a whole line (`grep -E '^[0-9]+ of [0-9]+ pass$'`, `re.fullmatch`): fix pass 9's step-1 idiom
  `grep -E 'pass$'`, and my first judge's unanchored search, both matched words a printed value can hold.

**Found beyond the brief, not fixed (leads for round 12, unverified):**
- Printable text a terminal renders unusually is outside `visible()`: combining marks, wide characters, right-to-left
  letters in a bidi-aware terminal, look-alikes, and a long line's soft wrap (documented: "What a terminal does with
  printable text"). None can begin a line or hide one, as far as this pass found.
- The env-file rule is a text rule (R11-1 passes it, executed). An action in the build job that writes the env file is
  judged only by being the template's (setup-python writes `PATH` and `pythonLocation` by design).
- The worst case under the size bound is now `bash -n`'s, linear: case F, 143.7 s, at 116 MB. Nothing faster than linear
  was found after the five rewrites; the rewrites themselves are new code.
- No rule reads the workflow's top-level keys beyond those it names (`name`, `on`, `permissions`, `env`, `defaults`,
  `concurrency`, `jobs`): case C's file, the template with an extra top-level key, PASSES both deliveries
  (`cost_probe_square_fp10.*.out`). GitHub refuses a workflow with an unknown top-level key, so such a file never runs;
  `run-name` is valid and only displays. A rule holding the top-level keys to the template's (with `concurrency`) would
  be an exact rule of the kind that has held; not made here: beyond the brief, and nothing found that changes what runs.

**Residual risk** (the docstring's "What this cannot see", for plan v1.15.18): the publish action's container image is
named by a re-pushable registry tag (M11-E); the build job's steps before the build can still reach the window and the
artifact by means no text rule sees (R11-1, a background process, a replaced tool), which only pinning those steps would
close (M11-C); another workflow can name this workflow's concurrency group or cancel its run (M11-D, availability only);
a terminal's own rendering of printable text; and, unchanged, equality is all the pins prove, GitHub's server-side
parser was not run, and SHA256SUMS' version is not tied to the tag (SWEEP item 28, the template's).

**Next:** round 12 (`tmp/sweep/ROUND12_BRIEF.md`), once, on the r10 -> r11 interdiff. The stopping rule is unchanged: no
port until a COMPLETE round reports no BLOCKER and no MAJOR.

## Status (session `ffffd3`, 2026-11-25 01:16Z)

Fix pass 10 finished (checker `b807d3ca…`, pins unchanged, manifest 7 paths). Round 12 (brief `tmp/sweep/ROUND12_BRIEF.md`,
a fresh reviewer) launched at 01:16Z; its report: `tmp/r12review/ROUND12_REPORT.md`. Record it here as `## Round-12 review`.
Residuals so far for plan v1.15.18: the publish action's container-image tag (M11-E), unpinned build steps before the
build (M11-C, R11-1), another workflow naming this one's concurrency group (M11-D, availability only).

## Round-12 review (report: `tmp/r12review/ROUND12_REPORT.md`; session `ffffd3`'s subagent, 2026-11-25 01:16:47Z-01:58Z; brief `tmp/sweep/ROUND12_BRIEF.md`) -- COMPLETE, CLEARS THE GATE

Verdict: **0 BLOCKER, 0 MAJOR**, 3 MINOR, 7 NIT against the checker `b807d3ca…` and pins `d539f05f…` (fix pass 10).
Every step done (lint by content checks on byte-identical copies; display in tmux 3.6 only, no bidi terminal; N12-4a-c
run through Record SHA256SUMS with a stand-in runner). Every count of § "Fix pass 10" reproduced; 15/15 simulations;
cascor's three from all three trees; 18/18 pins re-derived (libyaml C loader); fix pass 10's rewrites equivalent (0 of
535,923 + 150,000 + 63,000 + 100,000 differ); no class from rounds 4-11 reached in a form that changes what runs.

**Orchestrator's decision (ffffd3, 2026-11-25):** this is the first COMPLETE round with no BLOCKER and no MAJOR, so the
stopping rule CLEARS THE PORTS. M12-C is a MINOR, as the reviewer rates it. The exit status, every printed line (the
declared verdict) and the last visible summary rows stay true, nothing is concealed (unlike M11-1/2), captured output
is not forged (unlike M11-3), and the workflow must guess the terminal width. The MINORs and NITs are fixed in fix pass
11 without another round, per the rule; fix pass 11 re-runs every proof.

| id | sev | where (checker `b807d3ca…`) | finding | disposition |
|---|---|---|---|---|
| M12-A | MINOR | `extra_job_problems` `:1283-1287` (`called.read_bytes()`, no bound); `read_text` `:676-683` (bounds bytes, not time; no regular-file check); claims `:291-294`, `:244-250` | A called file or a workflow that is a symlink to `/dev/stdin` blocks forever (N12-2b, N12-3: no verdict, the next workflow never judged); `/dev/zero` grows until a cap (N12-1b). GitHub would not run such a file: availability, never a verdict (M11-B's class anew). | FIX PASS 11: `lstat` and refuse anything but a regular file (or `O_NOFOLLOW\|O_NONBLOCK` + `fstat` `S_ISREG`); read the called file through `read_text`'s bound; correct both claims; the operator's `--pins`/`--template` may take the same guard. |
| M12-B | MINOR | `ENV_FILE_NAMES` `:533`, rule `:1540-1544`, docstring `:343-347` | The env-file text rule misses `$(dirname "$GITHUB_OUTPUT")/set_env_*` (N12-4a), `${{ github['env'] }}` (N12-4b, substituted before bash), and a `shell: python` glob of `_runner_file_c*/set_env_*` (N12-4c); each adds a never-built wheel that Record records (stand-in runner). Reaches only the artifact's bytes, which the build step's own text can decide anyway (M11-C's class; R11-1's residual). | FIX PASS 11: state the residual truly (only literal spellings are stopped); optionally add `github['env']`/`github['path']` and refuse `_runner_file_c`; the class closes only by pinning the steps before the build (plan v1.15.18 residual). |
| M12-C | MINOR (close call; the orchestrator's decision above) | uncut `{key!r}` at `:1266` (also `:1254`, `:1256`, `:1264`) and other uncut `!r` values; `shown()`'s cut only where used; docstring `:356-358` | Soft wrap: an explicit YAML key of blanks + `PASS <label> (…)` + `1 of 1 pass`, at offsets that are multiples of 400, makes a terminal of width 80/100/200 show a fake PASS row and a `1 of 1 pass` row, pushing the real FAIL line off the pane; the true `0 of 1 pass` and exit status remain the last rows (N12-5b; tmux 200x50 and 80x50). | FIX PASS 11: route every printed value through `shown()` (cut) and collapse runs of blanks in shown values, or hard-wrap every printed line at 72-80 columns with indented continuations; restate the residual for narrower terminals. |
| n12-a | NIT | `place()` `:736-742`, `:806` | The 200-char cut can make two refused places print alike. | Keep a place's tail or an index when cutting. |
| n12-b | NIT | concurrency rule `:1410-1413`; claims `:60-61`, `:302-306` | `<stem>-<ref>` can coincide across two publishers for crafted refs (both `cancel-in-progress: false`: at most a pending run replaced). | Reword the claim. |
| n12-c | NIT | steps before the build | A duplicate step `id` passes the checker; GitHub refuses the file (not a bypass). | Optionally refuse a duplicate step id. |
| n12-d | NIT | `check_pinned_steps` `seen` list `:1060-1069` | Quadratic, immaterial (20,000 steps 2.24 s). | Use a set. |
| n12-e | NIT | `:682` under `:1374` | A size refusal reads as a YAML load failure. | Its own prefix. |
| n12-f | NIT | `OPTIONAL_JOB_KEYS` `:459`, `:1444` | `timeout-minutes` values unread (`1` on the PyPI job passes; fail-closed, except a partial upload). | Record, or hold to a floor. |
| n12-g | NIT | ROUND12_BRIEF | The brief's path for `notify-consumers.yml` omits `.github/workflows/`. | Record. |

**Also re-fetched (01:56:48Z):** juniper-cascor `main` `5e3d9801` (#775), juniper-data `main` `8e08d209` (#548); all
five files byte-identical to the frozen copies; the called file still `e17ddc9b…`.

## Fix pass 11 (round 12's MINORs and NITs; checker-r12; FINAL for the ports)

The executor reported this: session `d935c226`'s subagent for fix pass 11 (orchestrator `ffffd3`, brief
`tmp/sweep/FIXPASS11_BRIEF.md`), 2026-11-25T02:03:56Z to 2026-11-25T03:20:19Z, when this section was filled; it is
appended last, after the check of untouched files (times from `date -u`). The reviewed checker, fix pass 10's manifest
and the pins file were copied first, with `cp -p`, at 02:04:04Z, and `checker-r12/START_REF` touched; the
first new file was `checker-r12/survey_fp11.py`. Written: the checker, the manifest, this section and new files under
`tmp/sweep/checker-r12/`. **The pins file is unchanged** (`d539f05f…`), so the manifest keeps its seven paths and only
the checker's line moves. The writer, cascor's tree, every workflow, every port and every earlier pass's and review's
directory are untouched: round 12's tools were copied to `checker-r12/r12tools/` and run there, and its files were only
read (`checker-r12/evidence/untouched_r12.after-finish.out`). No round-13 brief, as the brief says. Drivers:
`rerun_all_r12.bash` re-runs every step in order (`evidence/rerun_all.out`, 2026-11-25T03:03:57Z to 03:19:05Z), and
`finish_r12.bash` freezes the outputs and writes the interdiffs and the manifest. Three record runs were stopped early,
each to make a message or the docstring true before the run that counts:
- run 1, at step 3a: the env-file message was 564 characters, over flake8's 512;
- run 2, at step 2: the size refusal said "before it is parsed: every rule's cost" of the called file, which is hashed,
  never parsed;
- run 3, at step 3a: the docstring gave a tool's message a counted cut (`said()` cuts silently, a crash's at 200),
  left a tool's message (300) out of the terminal residual, and did not say that only the called file grew.

Their partial outputs are kept as `.run1` to `.run3` (`aside_run1_r12.bash`, `aside_run_r12.bash`), and the development
runs as `.dev*`; nothing was deleted. The mutants are
negative test cases for this CI checker, run on this host only with stand-ins and a local terminal emulator (tmux 3.6);
the only network use was read-only `gh api` GETs (`fetch_main_r12.bash`).

**Versions.**
- Checker: `b807d3ca9c45f14ba3a5771c562fecb5df5f82dc905fb294b88c5622628ea92d` (saved before any edit as
  `checker-r12/checker_r11_as_reviewed.py`) -> **`a452db3d285d70838adb3c6cfc9091c9cf0999996bf6e718c6ef5e49e05cee35`**,
  1750 -> 1923 lines (144784 -> 160658 bytes), frozen as `checker-r12/checker_r12_as_delivered.py`. **This is the
  checker the ports are checked with.**
- Interdiff: `checker-r12/checker_r11_to_r12.diff`, 841 lines, +279/-106, sha256
  `472c97f3c92845eedc56c2badd62a447ee5d8c8f9f55314e45c20adff224859a` (`evidence/interdiff.log`).
- Pins file: `d539f05fbd6666d4311fc57cfbf2a4680bfb4ca498b983dc7ccb93c4878a69b3`, unchanged (`pins_r11_to_r12.diff` is
  empty).
- Manifest: fix pass 10's kept as `tmp/arc/sweep_scripts.r12.sha256` (copied before any edit; `40f09c65…`).
  `tmp/arc/sweep_scripts.sha256` is regenerated over the same seven paths (sha256
  `9a00840b37b8d2ea2c3331a8524e487600f0bf25c912bc8b2c7327d3d9a0a1b1`). Only the checker's line changes; the pins
  file's stays `d539f05f…` and the writer's `c47940ad…`; `sha256sum -c` passes 7 of 7 (`evidence/manifest.log`).
- Fetched read-only at 2026-11-25T02:32:16Z (`evidence/fetch_main_r12.log`):
  - juniper-cascor `main` is `5e3d9801` (#775), its three publishers byte-identical to the landing tree;
  - juniper-data `main` is `8e08d209` (#548), its `publish.yml` and `notify-consumers.yml` byte-identical to fix pass 10's
    fetch; the called file is still sha256 `e17ddc9b…`, 11039 bytes, blob `ab0cade2`.

**Before any edit** (`survey_fp11.py`, `evidence/survey_fp11.out`): the 37 files of fix pass 10's survey, and the two
fetches of the called file.
- Every one is a regular file, within the bound (the largest is 52,353 bytes).
- No build step's `run` or `env` names `github['env']`, `github['path']` or `_runner_file_c`, and no step id repeats in a
  job.
- No key holds a blank, and no name holds two in a row (`evidence/survey_names_fp11.out`). The longest blank run in a
  `run` script is 16, in any other value 1, and in a pin's line 4; the longest pin line is 436 characters.
- `timeout-minutes` stands only in juniper-data's called file (`dispatch`: 10).

So all 37 admit every new rule.

**Round 12's findings, each closed** (the checker's docstring, § "Fix pass 11"):
- **M12-A** (`read_regular`, `FileRefused`, `file_kind`). Every file the checker reads (a workflow, the called file,
  `--template`, `--pins`) is read only when `lstat` finds a regular file, so nothing else is ever opened. It is then
  opened with `O_NOFOLLOW | O_NONBLOCK`, `fstat` must agree, and at most its bound and one byte are read
  (`MAX_WORKFLOW_BYTES` for a workflow, the template and the called file; `MAX_PINS_BYTES`, 1 MiB, for the pins file).
  - **The symlink decision: refused, even a link to a regular file.** Git holds a link's target path at that path, not
    the file it names, so bytes read through a link are not the bytes the tree holds there. No template, port,
    simulation or driver uses one; the drivers' named copies are byte copies. It moves one control: round 12's C12-1
    (the called file a link to the real file), PASS -> FAIL.
  - Round 12's N12-1, N12-1b, N12-2, N12-2b and N12-3 now FAIL at once (0.2 to 0.4 s), and the workflow after each is
    judged and PASSES. Under fix pass 10's checker, N12-2, N12-2b and N12-3 gave no verdict in 20 s, and N12-1 and
    N12-1b stopped only at the 2 GB cap.
  - The claims at the old `:244-250` (m10-a) and `:291-294` (M11-B's "a delay, bounded, never a stop") now say what
    round 12 found and that fix pass 11 brings both reads inside them.
  - Traced (`strace_fp11.bash`, `evidence/strace_fp11.out`), a workflow that is a link to `/dev/zero`, and one that is a
    FIFO, each then the template: no open call names the case or `/dev/zero`, two `lstat`-family calls do, and the
    template is opened only with `O_RDONLY|O_NONBLOCK|O_NOFOLLOW|O_CLOEXEC`; FAIL, PASS, `1 of 2 pass` in each.
  - A link among a path's directories is still followed (an operator's own path may hold one): a residual, below.
- **M12-B.** `ENV_FILE_NAMES` adds `github['env']` and `github['path']`, and the prefix `_runner_file_c` in place of
  `_runner_file_commands`; none of the 37 holds one. N12-4b and N12-4c are refused now, PASS -> FAIL; executed by the
  copied `m12_envfile.py`, their outcome is unchanged (a wheel the build never made is recorded). The residual is stated
  truly, in the docstring and in the rule's message: a text check of literal spellings alone, so N12-4a's
  `$(dirname "$GITHUB_OUTPUT")/set_env_*` (F11-6c), a glob, another expression spelling or another shell still passes,
  and only pinning the steps before the build closes the class.
- **M12-C** (`shown()`, `quoted()`, `fold()`, `said()`, `clipped()`), the brief's first option. Every workflow-derived
  value a message names is cut and folded.
  - The cut: 200 characters (`SHOWN_CHARS`), then the count of the rest; a diff line at 1000 (`DIFF_CHARS`; the
    longest pin line is 436), also counted; a tool's message at 300 and a crash's at 200, silently, as fix pass 10 cut
    them.
  - The fold: a run of more than 8 blanks (`BLANKS_KEPT`; spaces, U+2800 and the four Hangul fillers) is written as its
    count, `<N blanks>`, so no two values that differ in their blanks print alike, and a pin's indentation still shows.
  - Every `!r` of a workflow's value is now `quoted()`, which prints exactly what `!r` printed for a value of at most 200
    characters with no such run. Every workflow-derived list goes through `shown()`, and bash's message and a crash's
    through `said()`. Two uncapped place lists go through `few()`.
  - The f-string audit (`audit_fp11.py`) also lists `sorted()` and `list()`, which fix pass 10's audit passed as
    escaping. It classifies all 123 expressions in 260 fields (14 of them `!r`), none left unclassified. Its first
    run found one more uncut list, `{sorted(map(str, job))}` (a job's keys), which now goes through `shown()`.
  - In tmux 3.6 at 200x50 and 80x50 (`render_wrap_fp11.bash`, `screen_check_fp11.py`), N12-5b shows no fake PASS row
    and no fake summary; the real FAIL line and the true summary are on the pane. Under fix pass 10's checker the same
    file still shows round 12's fake rows at both widths. The residual is restated, below.
- **n12-a.** `place()` keeps a long place's first 140 and last 40 characters and counts those between, so N12-6's two
  places now print apart (F11-7).
- **n12-b.** The concurrency claims at `:58-61` and `:302-306`, and the rule's comment, are reworded: a group no other
  publisher's file uses, for the refs the publishers use.
- **n12-c, recorded:** a repeated step id passes this checker, and GitHub refuses the file (the brief made a rule
  optional; none was made).
- **n12-d.** `check_pinned_steps`' `seen` is a set. Round 12's `cost_seen_r12.py`, copied, at 20,000 run steps:
  0.05 s (round 12: 2.24 s).
- **n12-e.** A workflow refused before it is parsed is reported as "the workflow file is refused before any of it is
  parsed: …" (the template's: "refused before any of it is parsed"), not as a YAML load failure. The inner text keeps
  "the file holds more than 262144 bytes", which CLI9 reads.
- **n12-f, recorded:** at `OPTIONAL_JOB_KEYS` and in § "Fix pass 11": fail-closed, but for a timeout between two
  uploads, R4-4's availability harm.
- **n12-g, recorded here:** `ROUND12_BRIEF.md` named `juniper-data-main-fetch/notify-consumers.yml`; the file is
  `checker-r11/juniper-data-main-fetch/.github/workflows/notify-consumers.yml` (sha256 `e17ddc9b…`).

**Results** (the record run, `evidence/rerun_all.out`, unless named):
1. **Cascor's three:** 3 of 3 PASS from the landing tree, from `f5ed3017` and from `main` `5e3d9801`
   (`evidence/checks_cascor.log`).
2. **The 15 simulations:** 15 of 15 PASS under both checkers (`evidence/port_sim_table.md`), with juniper-data's
   `notify-consumers.yml` beside its copy (`e17ddc9b…`). Regenerated by round 2's probes, they give 18 PASS and 7 FAIL
   among 25 variants, as recorded, and 0 diff lines against fix pass 6's seeds. **The 18 pins re-derive equal**
   (`evidence/port_sim_rederive_pins.out`).
3. **Every mutant set.** The judges' contrast is fix pass 10's checker as round 12 reviewed it; each bypass re-run keeps
   the checker its cases bypassed.
   - Earlier sets (`judge_all_r12.py`): each of the 15 sets as expected, 0 verdicts moved, 0 findings.
   - Round 9's (`judge_r9_mutants_r12.py`): 32 of 32 as expected (13 bypasses present).
   - X8-1 to X8-8: each FAILS the live checker, PASSES the naive one, FAILS fix pass 10's; 0 unexpected.
   - N9-1 to N9-9: each FAILS, against fix pass 7's PASS; C9-1 to C9-5 PASS; 0 unexpected.
   - Round 10's: only O10-7 and O10-8 moved from round 10's record (fix pass 9's own moves); 0 findings.
   - N10-1 to N10-16: 7 executed with the outcome changing, 1 refused by GitHub's TS lineage, 2 controls, 8 not
     executable; 0 unexpected.
   - Round 11's (`judge_r11_mutants_r12.py`): none moved, 0 findings.
   - N11 (`new_mutants_r11_rerun_r12.py`): 21 negative tests FAIL, the residual probe R11-1 as expected, 6 controls PASS;
     0 unexpected.
   - Fix pass 10's tmux check (`render_tmux_r12.bash`, `screen_check_r12.py`; "before" still fix pass 9's): 0 findings.
   - **Round 12's tools, copied to `r12tools/` and run there** (outputs under `r12rerun/`):
     - `m12_unbounded*`: C12-1 FAILS (the link choice). N12-1, N12-2, N12-3, N12-1b and N12-2b each FAIL in 0.2 to
       0.4 s, and the workflow after each is judged (C12-1b PASSES; the template PASSES after N12-3).
     - `m12_envfile`: C12-4 PASSES (1 wheel); N12-4a PASSES (the documented residual; executed, 2 wheels); N12-4b and
       N12-4c FAIL on the new names (executed, 2 wheels: the outcome they would have).
     - `m12_wrap`, `m12_wrap_b`, `m12_more`, `m12_dupid_b`: N12-5 and N12-5b FAIL, N12-6 to N12-9 and N12-10 as round
       12 recorded. The regenerated N12-5b equals round 12's byte for byte (`fab605fc…`).
     - The over-strict tools: `m12_overstrict` gives its 25 rows exactly as round 12 recorded them, then stops at its own
       assertion on O12-21a, as round 12's run did; `m12_overstrict_b` stops at its own assertion on O12-21's size,
       as round 12's did; `m12_overstrict_c` gives O12-21c PASS, O12-21d FAIL and O12-22 PASS.
     - `cost_seen_r12`: 20,000 run steps take 0.05 s (round 12: 2.24 s).
     - `render_wrap_r12.bash` (the live checker, as round 12 rendered it): N12-5b at 200 and 80 columns shows its real
       FAIL line, `'<200 blanks>'... (12570 more characters)`, `0 of 1 pass` and exit status 1, with no fake row.
   - **Round 12's cases on round 12's own files** (`judge_r12_mutants.py`, read-only, `evidence/judge_r12_mutants.md`):
     20 cases and 29 over-strict cases. Exactly the six stated verdicts move:
     - C12-1, PASS -> FAIL (the link choice);
     - N12-2, N12-2b and N12-3, from no verdict in 20 s to FAIL, and the next workflow PASSES, in 0.3 s;
     - N12-4b and N12-4c, PASS -> FAIL (M12-B).

     N12-1 and N12-1b keep FAIL then PASS (fix pass 10: 1.7 s, a `MemoryError` at the 2 GB cap; now 0.3 s). Every
     over-strict case keeps its verdict; 0 unexpected.
   - **This pass's negative tests** (`new_mutants_r12.py`, `evidence/new_mutants_r12.out`): 26 of 26 as expected. That is
     19 negative tests (each FAILS, or the run is refused: F11-1e to F11-1g), the M12-B residual probe F11-6c (PASSES,
     as documented) and 6 controls. Four controls PASS; F11-C4 and F11-C7 FAIL, as under fix pass 10's checker, by
     another rule than the one they control (a called file of exactly the bound, refused by its sha256 and not its
     size; a place under the cut, printed whole beside its ESC). Under fix pass 10's checker:
     - F11-1a, F11-1b, F11-1e and F11-1f gave no verdict in 20 s (a FIFO, read);
     - F11-1d and F11-1g passed through a link, and F11-6a and F11-6b passed.

     Each now FAILS, or is refused, in under 0.4 s.
   - **M12-C in tmux 3.6** (`render_wrap_fp11.bash`, `screen_check_fp11.py`, `evidence/screen_check_fp11.out`): 28 panes,
     0 unexpected.
     - Under fix pass 10's checker, N12-5b, F11-5a, F11-5c and F11-5d are DISHONEST at 200 and at 80 columns, and F11-5b
       and F11-5e at 80: fake PASS rows, fake summaries, the real FAIL line off the pane.
     - Under the live checker every pane is HONEST, but F11-5b at 80 columns, the documented residual (a key of 130
       characters wraps where an 80-column row begins).
     - C12-5 (the template) is HONEST under both.
4. **The proof** (`checker_proof_r12.py`, built by `make_proof_r12.py` from fix pass 10's,
   `evidence/checker_proof_r12.log`):
   479 of 479 cases as expected (306 of fix pass 6's table, 40 NEW8, 46 NEW9, 33 NEW10, 41 NEW11, 13 command-line).
   - One expectation moved, a message with no verdict: E11e (`names ['_runner_file_c']`, M12-B), stated in
     `NEW11_OVERRIDES_R12`.
   - CLI9 still finds "the file holds more than 262144 bytes" under n12-e's prefix.
   - Round 2's 43 (`run_proof43_r12.bash`, `evidence/proof43_classes.out`): 26 of 43 as round 2 expected. The 17
     mismatched rows are exactly fix pass 9's classes: K1, K2 and R19; C1; and 13 FAILs kept, their reason moved to the
     pin's. 0 other changes.
5. **The fuzz and the typing differential** (copies in `parsers/`, `evidence/fuzz_*.out`), all as fix pass 10 recorded:
   - seed 9001: 3066 tried, 1500 kept; libyaml, YamlDotNet 5.3.0 and 16.3.0 and Node: 0 differ;
   - seed 424242: 6390 tried, 3000 kept; libyaml and both YamlDotNets 0, Node 7 (round 9's construct);
   - the typing differential, 3320 documents: 2453 agree, 861 both refuse, 6 refused by the checker alone, 0 by GitHub
     alone, 0 divergences.
6. **Lint** (`lint_checker_r12.bash`):
   - pre-commit (juniper-ml's config, `--files` the checker and the pins file): 12 passed, 0 failed, 14 skipped, both
     files unchanged (G-TMP and G5 among the passes);
   - B914: 0 sites;
   - flake8 `--isolated` at 512 columns: 2 E203, as fix pass 10's;
   - `--help`: exit 0.
7. **Beyond the list.**
   - The equivalence (`equivalence_fp11.py`, `evidence/equivalence_fp11.out`), 0 differing:
     - `shown()`: 100,000 values, 34,011 equal and 65,989 equal once folded;
     - `quoted()`: 33,748 short values equal to `!r`, and 66,252 longer ones equal to the cut repr, folded;
     - `place()`: 58,288 short places equal to fix pass 10's, folded, and 41,712 longer ones holding their head, tail
       and count;
     - `said()`: 50,000 texts;
     - `fold()`: 50,000 texts, no long run left and every count exact;
     - `check_pinned_steps()`: 20,000 install jobs;
     - `document_problems()`: 30,000 documents;
     - `read_text()`: 87 regular files, and the file over the bound refused by both.
   - The cost (`cost_probe_live_r12.py`):
     - a flat mapping is linear (2,000 to 16,000 keys: 0.11 to 0.90 s);
     - 14,254 run steps at the bound take 52.1 s (fix pass 10: 44.9 to 48.5 s; round 12: 50.3 s), `bash -n` per step,
       linear;
     - 6,288 env keys take 1.0 s;
     - round 12's `cost_r12.py`, copied: 18 shapes, the largest ratio per doubling 2.3, the slowest 3.3 s at the bound
       (round 12: 3.4 s).
   - The audits: `audit_fp11.py` finds 123 expressions in 260 fields (14 `!r`), 0 unclassified. Fix pass 10's own audit,
     for the record, finds 127 raw expressions in 296 fields; it does not know `quoted()`, `said()`, `fold()` or
     `clipped()`.
8. **The survey again** (`evidence/survey_fp11.rerun.out`): the same totals.
9. **Untouched** (`untouched_r12.bash`, `evidence/untouched_r12.after-finish.out`):
   - no file outside the allowed outputs is newer than `START_REF`;
   - only `util/ad-hoc`'s own directory time moved (03:03:33Z, the Edit tool's last save of the checker);
   - no `__pycache__` outside the stand-in venvs;
   - the pins file, the writer and the template are unchanged;
   - the manifest passes 7 of 7 after `finish_r12.bash`.

**Deviations from the brief.**
- M12-A: a symlink to a regular file is refused (the brief let this pass choose); round 12's control C12-1 moves PASS ->
  FAIL. `--template` and `--pins` take the same guard, link refusal included (F11-1e to F11-1g).
- M12-C: the cut and fold of option 1, not a hard wrap. Every driver reads a reason from the line that begins `    - `,
  so a wrap would split reasons across lines in every driver, and the drivers would need rewriting with no review to
  follow. The fold writes a run of more than 8 blanks as its count rather than collapsing every run to one blank, so a
  message stays exact (a pin mismatch's indentation, a whitespace-only change) and a run of up to 8 is kept. The fold
  also counts U+2800 and the Hangul fillers as blanks. A diff line is cut at 1000 characters, not 200, since a pin's
  line is up to 436.
- Beyond the brief:
  - in the checker: the job-keys list the audit found; `few()` on the expression-key and surrogate place lists; bash's
    message cut at 300; the called-file note in "What this cannot see";
  - as evidence: the equivalence of the rewrites (`equivalence_fp11.py`), the classified audit (`audit_fp11.py`), the
    syscall trace (`strace_fp11.bash`) and the names survey (`survey_names_fp11.py`).
- n12-c: not fixed (optional), recorded. n12-f: recorded, not held to a floor.
- The re-run: round 12's `m12_dupid.py` was not re-run. It reads C12-10 and N12-10 files that no round 12 tool writes;
  `m12_dupid_b.py` writes N12-10 itself, and `judge_r12_mutants.py` judges both from round 12's own files.
  `m12_overstrict_b.py` stops at its own assertion on O12-21's size, as round 12's run did, and `m12_overstrict_c.py`
  follows it.
- One proof expectation moved, a message with no verdict: E11e, stated in `NEW11_OVERRIDES_R12`.
- The guard rule's list of the template's two forms prints the workflow's prefix through `shown()`. A plain prefix
  (every real one) prints as before, and any other as its repr (N11-10's message).

**Every message, not only the verdict** (`compare_messages_fp11.py`, `evidence/compare_messages_fp11.out`, beyond the
brief): the four most recent sets (round 12's mutants and over-strict cases, round 11's mutants, fix pass 10's N11),
judged in-process by both checkers. Six files are left to `judge_r12_mutants.py`, since each is or calls a device, a pipe
or a link that fix pass 10's checker reads with no bound; 86 files are judged by both.
- Verdicts moved: 2, N12-4b and N12-4c (M12-B).
- Messages: 50 equal, 2 added (those two cases' refusals), 0 removed, and 14 changed, each by a stated change:
  - a long value cut: M11-8's step list, N11-1's key (`!r` -> `quoted()`), N12-5b's key;
  - the place cut: N12-6, and N11-1's two place lists;
  - M12-B's message tail: M11-9, O12-11, N11-7a to N11-7c;
  - n12-e's prefix: O12-21d, N11-8a;
  - the guard's forms: N11-10.
- A first run of this script took `--repo` from the worktree's own path (`juniper-ml`), a bug of the script's; its
  output is kept as `.dev1`.

**Residuals for plan v1.15.18** (the docstring's "What this cannot see"):
1. **The publish action's container image** is named by a re-pushable registry tag (M11-E; fix pass 10's).
2. **The build job's steps before the build** are unpinned. They can reach the window and the artifact by means no text
   rule sees: R11-1's computed name, N12-4a's file-command directory, a glob, another expression spelling, another
   shell, a background process, a replaced tool. Only pinning those steps, as install scripts are pinned, closes the
   class (M11-C; fix pass 10's; M12-B restates it).
3. **Another workflow of the repository** can name this workflow's concurrency group or cancel its run through the API
   (M11-D, availability only; fix pass 10's). Two publishers' groups can also coincide for refs a writer crafts, each
   `cancel-in-progress: false`, so at most a pending run is replaced (n12-b).
4. **Added by this pass, the display:** where a terminal wraps a line inside a value, the row begins with the workflow's
   own text. A refused workflow can still show a row that begins like a PASS line, or like a summary, inside one of its
   FAIL messages, in any terminal narrower than that line, and most messages are. At 80 columns, 130 characters of one
   value place one (F11-5b: the pane DISHONEST at 80 columns, HONEST at 200). No value can fill rows with blanks, show
   more than its first 200 characters (a diff line 1000, a tool's message 300), or hide the real FAIL line by blanks.
   The exit status and the lines as printed are the verdict, and the last line printed is the summary.
5. **Added by this pass, a link above a file:** a link among the directories of a path is followed, so a port's tree
   that makes `.github` or `workflows` a link is read through it, though git holds a link there, not that directory's
   files.
6. **Unchanged:**
   - equality is all the pins prove;
   - GitHub's server-side parser was not run;
   - SHA256SUMS' version is not tied to the tag (SWEEP item 28, the template's);
   - `timeout-minutes` values are not read (n12-f);
   - a repeated step id passes (n12-c; GitHub refuses the file).

**How to run the checker on a port** (this is how each port is checked). Run it from a juniper-ml checkout that holds the
checker and the pins file as the manifest lists them, on a fresh checkout of the port's branch, with a `python3` that
has PyYAML (here JuniperCascor1: Python 3.14.7, PyYAML 6.0.3), one command per repository:

    python3 -I -B util/ad-hoc/2026-11-23_publish_port_template_identity.py \
        --repo <REPO> \
        --template <juniper-cascor checkout at main>/.github/workflows/publish.yml \
        [--pins util/ad-hoc/2026-11-24_publish_port_install_pins.json] \
        <port checkout>/.github/workflows/<publisher>.yml [<port checkout>/.github/workflows/<publisher>.yml ...]

- `--repo`: the repository the workflows belong to, as the operator knows it, one of `REPOS` (`juniper-canopy`,
  `juniper-cascor`, `juniper-cascor-client`, `juniper-cascor-worker`, `juniper-data`, `juniper-data-client`,
  `juniper-ml`, `juniper-recurrence`). Pass all of one repository's publishers on one command line: juniper-ml's seven
  (`publish.yml` and the six `publish-<package>.yml`), juniper-recurrence's three. The workflow text never decides it.
- `--template`: juniper-cascor's own `publish.yml` at `main`, which is `5e3d9801` at this pass's fetch (sha256
  `b6826ee65f7fc511a1cc68a169730c8d54933d5fd6bff08b25ffc3148f40078b`, byte-identical to the landing tree
  `tmp/sweep/cascor-r4/main/juniper-cascor`). A template whose action refs are not full commit SHAs is refused.
- `--pins`: optional; by default the pins file beside the checker (`d539f05f…`, 18 pins, the manifest's line). A
  port's review updates its own pin there (its `lines` and their `sha256`) when its install script is meant to change.
  The checker prints the pins file's path and sha256 first; match them with `tmp/arc/sweep_scripts.sha256`.
- **juniper-data's called file:** `notify-consumers.yml` must sit beside juniper-data's `publish.yml`, as the checkout
  holds it, at `<checkout>/.github/workflows/notify-consumers.yml`. It must be a regular file (since fix pass 11 a link
  is refused), and `EXTRA_JOBS` pins its sha256 (`e17ddc9b3ac99d87600c99835b2c87bc16f252034f966645975c0b776ec8e078`,
  11039 bytes, juniper-data `main` `8e08d209`). If juniper-data changes it, `EXTRA_JOBS` changes through that port's
  review first.
- Every path names a regular file in a fresh checkout. Each file's name is its pin key's workflow name, so keep the
  publisher's own file name and pass no renamed copy. Exit 0 means every workflow passed every check, and 1 otherwise.
  Each failure is printed under its workflow's FAIL line, and the last line printed is the summary (`N of M pass`).

**FINAL.** Under the stopping rule (round 12 was a complete round with no BLOCKER and no MAJOR), the ports may start
with this checker, `a452db3d285d70838adb3c6cfc9091c9cf0999996bf6e718c6ef5e49e05cee35`. Any later change to it is a new pass.

## Status (session `b71989`, ListAgents `moonlit-percolating-sun-fa`, appended 2026-11-26 01:31:46Z): the ports begin

From the handoff of ml#2658. Verified first: `sha256sum -c tmp/arc/sweep_scripts.sha256` 7 of 7 OK; the checker
`a452db3d…`; no port PR open in any of the 7 repos; every publisher unchanged on `main` since the 11-16 port
(recurrence's three since #237, 11-20); cascor `main` still `5e3d9801`. This session is worktree-isolated in
`juniper-ml/.claude/worktrees/moonlit-percolating-sun` (`$WT`): it can write `$W` only through Bash, so the ports run
in `$WT` and are mirrored here (`tmp/ports/s2/`, by `$WT/tmp/s2/mirror_to_w.py`).
- Fresh clones of all 8 repos (7 ports + cascor's template): `$WT/tmp/ports/clones/<repo>`, each `==main` at 01:25Z.
- The done-check, adapted: `$WT/tmp/s2/verify_all_mains_v3.bash`: `--pins` explicit, juniper-data's
  `notify-consumers.yml` fetched beside its publisher, one checker run per repository with all its publishers.
  Baseline at 01:26Z: `3 of 18 pass` (cascor's 3).
- The port brief: `$WT/tmp/ports/SWEEP_PORT_BRIEF.md`; the independent review brief:
  `$WT/tmp/ports/SWEEP_PORT_REVIEW_BRIEF.md`. Each port proposes its pin change in
  `$WT/tmp/ports/<repo>/pins.proposed.json`; the pins file here changes only after that port's review.
- Pilots launched between 01:26:36Z and 01:31:46Z (task-executor agents): juniper-cascor-client and juniper-data-client.

## The owner's merge approval for the ports (2026-11-26, answered by 01:47:14Z; session `b71989`'s dialog, header "Merge ports")

Asked (`AskUserQuestion`): "One-artifact sweep ports: the port checker is final (round 12 clean), and the first two port
PRs (juniper-cascor-client, juniper-data-client) are being built now; five more repos follow, one PR each. Merging a
publish workflow publishes nothing by itself (it runs only on a GitHub Release or a dispatch). May I merge each port PR
with util/safe_merge.py once its CI is green, its independent review has no BLOCKER or MAJOR left open, and the checker
passes on the PR's fetched head with that port's reviewed install pin?"

**Answer, verbatim: "Approve all 7 (Recommended)"**, whose option text read: "I merge each of the 7 port PRs when it
meets all three conditions, and also this arc's juniper-ml docs PRs (handoffs, and the plan v1.15.18 record that lands
the sweep's scripts). I stop and ask about anything that falls outside those conditions."

Not chosen: "Ports only", "Ask per PR", "You merge". The approval is this session's (`b71989`); a later session asks
again.

## Status (session `b71989`, 2026-11-26 02:24Z): the first port is open; its review and the canopy port run

- **juniper-cascor-client#206** opened 02:19:17Z (`createdAt`), head `0e042e85ca542b70ef10b4741293e67169f62863`, one
  signed commit on `358eef4f`, 4 files (+897 -154). The executor's report: `$WT/tmp/ports/juniper-cascor-client/REPORT.txt`
  (mirrored: `tmp/ports/s2/extra/tmp/ports/juniper-cascor-client/REPORT.txt`); its writer
  `$WT/util/ad-hoc/2026-11-26_juniper-cascor-client_one_artifact_sweep_port.py` (mirrored beside it). It reports:
  121 publish tests pass (69 before), 0 skipped; checker `1 of 1 pass` on the clone and on the PR-head fetch with its
  proposed pins (`$WT/tmp/ports/juniper-cascor-client/pins.proposed.json`, `9f7e03e8…`); 38 of 38 mutations caught;
  screens pass with the repo's own scope and two `Allow-Symbol-Loss:` lines
  (`TestFindReleaseRun.test_the_newest_release_run_that_still_holds_the_artifact_is_found`, and
  `TestUnchanged.test_the_testpypi_job_keeps_its_setup_and_its_install_check`); the gate passed with one accepted
  finding (`docs/REFERENCE.md:661`, unchanged since 2026-09-05). Its pin moves from 18 lines (`8281a039…`) to 31
  (`9dc38ffe…`): `find_spec('juniper_cascor_client')` in place of the metadata line, and 13 comment lines. Its install
  job has no checkout (the version comes from the tag). It names three small inaccuracies in its own PR body.
- Its independent review (a fresh `general-purpose` agent on `$WT/tmp/ports/SWEEP_PORT_REVIEW_BRIEF.md`) and the
  juniper-canopy port started at about 02:24Z; juniper-data-client's port is still running.
- The brief gained "Addenda from the pilots" (own-worktree isolation, the screens' scope, every removed symbol
  waived, a checkout only where the script reads the workspace, the PR body re-read, concurrent PRs).
- The pins file here is unchanged until #206's review is in.

## Status (session `b71989`, 2026-11-26 02:45Z): the second port is open; its outputs rescued from its agent worktree

- **juniper-data-client#274** opened 02:36:19Z (`createdAt`), head `8ef0c329e2b4b34bee9cb82b6bc66e2a55d9baeb`, one
  signed commit on `5c329a39`, 5 files (+983 -148: `publish.yml`, `CHANGELOG.md`, `docs/REFERENCE.md`,
  `tests/test_publish_one_artifact.py`, new `tests/test_publish_docs_bounds.py`). CI at 02:41:23Z (the executor's
  read): 24 pass, 0 fail, 0 pending, 6 skipping. Its report: 119 publish tests pass (69 before), no new skip; checker
  `1 of 1 pass` on the clone and the PR-head fetch with its proposed pins (`cb387ade…`); 38 of 38 mutations caught;
  screens pass with the repo's scope and the same two `Allow-Symbol-Loss:` lines as #206; the gate passed with one
  accepted pre-existing finding (`docs/REFERENCE.md:640`). Its pin moves from 18 lines (`aa16d5b2…`) to 30
  (`d7bbf100…`): `find_spec('juniper_data_client')` and the step's own comments. It ported `test_publish_docs_bounds.py`
  (its docs now state the install check's tries, waits and lag error).
- **Its executor ran in its own agent worktree** (`.claude/worktrees/agent-a2750c00ae7f6c8a4`), and its outputs were
  there only. Copied into `$WT` by `$WT/tmp/s2/rescue_agent_outputs.py` before 02:45:05Z (3827 files, manifest
  `$WT/tmp/ports/juniper-data-client/RESCUED_FROM_agent-a2750c00ae7f6c8a4.sha256`): the writer
  `$WT/util/ad-hoc/2026-11-26_juniper-data-client_one_artifact_sweep_port.py` (`6798f7b7…`), the scratch dir, and its
  landing clone (`$WT/tmp/ports/juniper-data-client/landing-clone/`). The juniper-cascor-client executor's worktree
  (`agent-ac7331d10482e7dff`) had already been removed when checked; that executor had copied its outputs into `$WT`
  before finishing.
- #274's independent review started before 02:45:05Z. #206's review and the canopy port are still running.

## Review of juniper-cascor-client#206 (report: `$WT/tmp/ports/juniper-cascor-client/review/REVIEW.txt`; a fresh `general-purpose` agent on `SWEEP_PORT_REVIEW_BRIEF.md`, its last `date -u` 2026-11-26 02:49:52Z) -- COMPLETE

Verdict: **BLOCKER 0, MAJOR 0, MINOR 1, NIT 6**, on head `0e042e85` (base `358eef4f`, still `main`). The FINAL checker
passes the fetched head with the proposed pins (`9f7e03e8…`) and fails it with the seed pins (the control); all 14
template blocks and the republish job byte-identical raw; 121 publish tests pass, no new skip; 22 of 22 of the
reviewer's own mutations caught (8 of 8 by the rehearsals alone; the checker 23 of 23 with the ref-move probe P1,
which this repo's CI passes by design: item 23's ref-free digests, the cross-repo checker's exact SHAs); all 20 required
checks green; the commit verified; the writer replays byte for byte. The proposed pin: ACCEPT (stepsim under
`bash -e`: present 0; metadata only, bare namespace, no dist-info, nothing installed 1, with `PYTHONOPTIMIZE` 1 and 2
too; the lag error after 5 failed tries; the `cd` hides a checkout's package).

| id | sev | finding | disposition (orchestrator `b71989`) |
|---|---|---|---|
| R1 | MINOR | `CHANGELOG.md:231-232`: "the package it installed ran with that job's OIDC token-request variables" is false here (the base check read metadata only); carried from cascor's entry, true there | FIX-UP: the writer's `CHANGELOG_ENTRY` |
| R2 | NIT | `docs/REFERENCE.md:724/:728`: the lead-in excludes its own third bullet (a failed PyPI JSON check is after the upload) | FIX-UP, as cascor's MANUAL |
| R3 | NIT | `docs/REFERENCE.md:727`: "never delete and publish a Release again" lacks ruling 1's consequence | FIX-UP |
| R4 | NIT | #199's earlier `[Unreleased]` entry keeps three statements the new entry supersedes | LEAVE: #777 left its own earlier entry the same way |
| R5 | NIT | the package check prints "TestPyPI install OK … package at None" before failing | FIX-UP: cascor's neutral `print('TestPyPI install', …)`; moves the pin and the test's pins |
| R6 | NIT | both waived symbols on one `Allow-Symbol-Loss:` line | NO CHANGE (the screen read both); later ports one line per symbol |
| R7 | NIT | the writer's `--changelog-cases`/`--changelog-mutations` default to placeholders substituted unchecked | FIX-UP (writer only) |

The fix-up goes to #206's own executor (resumed), as ONE signed commit through `run_push_signed_commit.py` with
`expected_head` `0e042e85…`, re-verified, its PR body corrected (the three inaccuracies the executor reported). The
lessons went into the port brief's addenda for the later ports. data-client#274 has the same R5 form ("TestPyPI OK:
v…" before its `SystemExit`); its review is running.

## #206's fix-up, checked; cascor-client's pin applied; the merge started (session `b71989`, 2026-11-26 03:12Z)

- **The fix-up** (by #206's own executor, resumed): one signed commit `2a1f2a27ae63e280e03feaf2c72852019d2b4fa7` on
  `0e042e85` (verified, reason valid). Its report: `$WT/tmp/ports/juniper-cascor-client/REPORT_FIXUP.txt`. The
  orchestrator read its whole patch (`gh api …/compare/0e042e85…2a1f2a27`, 4 files, +18 -13): exactly R1 (the
  CHANGELOG sentence), R2 (the failed PyPI JSON check out of the "before PyPI" list, as its own paragraph), R3 (the
  re-cut's consequence), R5 (`print('TestPyPI install', …)`, with the test's `PACKAGE_CHECK` and a rehearsal that
  asserts no "OK" before the verdict); R7 is in the writer alone (`17035d90…`). Its executor reports 121 publish tests,
  the full suite 720 passed / 8 skipped (`main`'s 8), 42 of 42 mutations, screens, gate, and the PR body corrected.
- **The orchestrator's check of the head as GitHub holds it** (`$WT/tmp/s2/check_pr_head.bash`, 03:11:10Z): the FINAL
  checker on `2a1f2a27`'s `publish.yml`, template cascor `main` (`b6826ee6…`), pins the proposal `1dd592c2…`:
  `PASS`, `1 of 1 pass`, exit 0.
- **The pin, applied** (`$WT/tmp/s2/apply_pin.py`, 03:11:55Z, which refuses a proposal that moves any other repo's
  pin or a file that does not re-serialize byte for byte): juniper-cascor-client's `Verify TestPyPI install` pin
  `8281a039…` (18 lines) -> `575be747…` (31 lines). The pins file is now
  `1dd592c224adeec82910328d5d2a9127e1a3bc6d7b3d5c9ded11ed971b7bacc7`; the manifest regenerated over its 7 paths,
  `sha256sum -c` 7 of 7 OK. Backups: `tmp/arc/pins.before-juniper-cascor-client-20261126T031155Z.json`,
  `tmp/arc/sweep_scripts.before-juniper-cascor-client-20261126T031155Z.sha256`.
- **The merge conditions** (the owner's approval of 01:47:14Z): the review has no BLOCKER or MAJOR (and its MINOR and
  NITs are fixed or disposed); the checker passes the fetched head with the reviewed pin; CI: 20 pass, 1 pending
  (`Build Package`) at 03:11:45Z. `util/safe_merge.py --pr 206 --repo juniper-cascor-client --merge-method squash
  --execute` started then (log `$WT/tmp/ports/juniper-cascor-client/merge/safe_merge.log`); it merges only when the
  required checks have finished green.

## Landed: juniper-cascor-client#206 (session `b71989`, 2026-11-26)

- **MERGED 2026-11-26T03:13:03Z** as `beb6b349689273b07d3df8240cd89f6ae9dda3fb` (parent `358eef4f`, verified, reason
  valid), by `util/safe_merge.py`'s armed auto-merge net pinned to `2a1f2a27` once the required checks were green
  (log `$WT/tmp/ports/juniper-cascor-client/merge/safe_merge.log`, 03:12:05Z-03:13:15Z). The squash message holds both
  commits' messages (COMMIT_MESSAGES): the `Allow-Symbol-Loss:` line naming both symbols, each commit's two trailers,
  and GitHub's own `Co-authored-by` paragraph after them.
- Post-merge on `main` (read before 03:13:47Z): Post-Merge Main Verification `success` (run 45747484262); CodeQL Analysis
  (45747484231) and CI/CD Pipeline (45747484239) in progress.
- Port 1 of 7 landed. The done-check now expects juniper-cascor-client's `publish.yml` to PASS on `main` with the
  canonical pins (`1dd592c2…`).

## Review of juniper-data-client#274 (report: `$WT/tmp/ports/juniper-data-client/review/REVIEW.txt`; a fresh `general-purpose` agent, written after 03:19Z by its `date -u`) -- COMPLETE

Verdict: **BLOCKER 0, MAJOR 1, MINOR 3, NIT 1**, plus a merge-order note N1, on head `8ef0c329` (base `5c329a39`).
The workflow is right: the FINAL checker passes the fetched head with the proposed pins (`cb387ade…`) and fails it with
the seed pins; all 14 template blocks and the 307-line republish job byte-identical raw; 119 publish tests pass, the
full suite 665 passed / 18 skipped (the base's 18, none in a publish module); 16 of 16 of the reviewer's own mutations
caught; all 20 required contexts green; one verified commit. The install-step harness (the real 0.6.0 wheel, a 3.12
venv, `bash -e`): C1 passes, metadata-only / namespace directory / `PYTHONOPTIMIZE=1` / decoy in the checkout / no
dist-info / no pyproject fail, the lag error after 5 tries; the seed's metadata-only line passes a wheel without the
package (C11, C12), which is why R4-5 is needed. The sparse checkout reproduced locally in cone mode.

| id | sev | finding | disposition (orchestrator `b71989`) |
|---|---|---|---|
| F1 | MAJOR | `docs/REFERENCE.md:702` sends every failed `Verify PyPI serves exactly these files` "past the ladder" to a new patch version; a TIMEOUT is index lag ("Re-run failed jobs", as cascor's MANUAL :821), only a MISMATCH needs a patch version (:819) | FIX-UP: split the two causes, as cascor's MANUAL does |
| F2 | MINOR | `CHANGELOG.md:230-231` ("the package it installed ran beside…") and `docs/REFERENCE.md:685` ("It runs the package…") are false here: the check read metadata alone (R1's shape) | FIX-UP: "installs", none of its code ran; the workflow's banner comments are cascor's template text (shared by its find_spec-only `publish-protocol.yml`): LEAVE |
| F3 | MINOR | the package check prints "TestPyPI OK: v… package at None" before failing (R5) | FIX-UP: cascor's neutral line, as #206's fix-up; moves the pin |
| F4 | MINOR | #264's earlier `[Unreleased]` entry keeps three statements this PR makes false | LEAVE, as #206's R4 (#777 left its own earlier entry's statements, correcting only the witness line; the new entry's "Until now" marks each change) |
| F5 | NIT | the two waived symbols share one `Allow-Symbol-Loss:` line | NO CHANGE (a fix-up cannot rewrite the first commit; CI's screen read both) |
| N1 | note | open data-client#273 (another session's run_tests PR) conflicts with #274 in `docs/REFERENCE.md`'s footer (`git merge-tree`, either order); `CHANGELOG.md` merges | #274 merges first if ready first; the PR body says so; #273's session (`run-tests-rollout-recurrence-copy-landed-data-client-copy-next`) told by message; the executor stops if #273 merges before its push |

**#206 re-read for F1** (cascor-client `main`'s `docs/REFERENCE.md:729`): "A failed `Verify PyPI serves exactly these
files` is not in that list: the step runs after the upload, so this run's files are already on PyPI. If PyPI lists a
file this run did not build, or another sha256, …; only a new patch version ships tested files under a clean version."
It keeps the patch-version advice to the mismatch and never calls the case past the ladder (rungs 1-2 still apply to a
timeout), so no follow-up there.

The fix-up goes to #274's own executor (resumed). The brief's addenda gained #274's lessons, and both running
executors (canopy, cascor-worker) were sent them.

## Status (session `b71989`, 2026-11-26 03:29Z): the third port is open; its known gaps go to a fix-up before its review; the juniper-data port starts

- **juniper-canopy#844** opened 03:23:49Z (`createdAt`), head `dcc58bb5510874227dd04206b0b77a3f7df2916e`, one signed
  commit on `2cec71fe` (canopy `main` moved from `60880efc` by #843 at 03:01:13Z during the port; the executor pulled
  and re-checked its anchors), 7 files (+816 -152 and the new `src/tests/unit/test_publish_docs_bounds.py`). Its report:
  `$WT/tmp/ports/juniper-canopy/REPORT.txt`; writer `$WT/util/ad-hoc/2026-11-26_juniper-canopy_one_artifact_sweep_port.py`
  (`7e56cdfd…`). It reports: 128 publish-related tests pass (113 + 2 docs-bounds + 13 wheel smoke), the unit lane 8546
  passed / 17 skipped (main 8500 / the same 17); checker `1 of 1 pass` on the clone and the PR-head fetch with its
  proposed pins (`0fa60256…`; canopy's pin 18 -> 23 lines, comments only, no content change: canopy's check imports the
  package, so no R4-5); 55 of 55 mutations caught (17 of 17 by the rehearsals alone); screens pass with one
  `Allow-Symbol-Loss:` line per symbol; the gate passed with two accepted pre-existing findings (`CHANGELOG.md:1744`).
- **Its own gaps against the reviews' lessons** (the lessons reached it after the PR opened): the MANUAL's failed
  `Verify PyPI serves exactly these files` bullet sends a timeout to the mismatch remedy (#274's MAJOR class); its
  lead-in excludes that bullet (#206 R2); the writer's placeholder arguments are not required (#206 R7). Its executor,
  resumed, makes ONE fix-up for these three (and the CHANGELOG / PR body sentences that name the case); #844's
  independent review then runs on the fixed head.
- **juniper-data's port** started after 03:25:20Z (the executor brief names all three earlier ports and their reviews).
- Running: #274's fix-up, #844's fix-up, juniper-cascor-worker's port, juniper-data's port.

## Status (session `b71989`, 2026-11-26 03:42Z): the fourth port is open; its review runs

- **juniper-cascor-worker#238** opened 03:37:40Z (`createdAt`), head `1965e557d1993c797c699e30a324048e14766365`, one
  signed commit on `7df573f0` (`main` at upload), 5 files (+911 -157: `publish.yml`, `tests/test_publish_one_artifact.py`,
  `AGENTS.md`, `docs/DEVELOPER_CHEATSHEET.md`, `CHANGELOG.md`). Report `$WT/tmp/ports/juniper-cascor-worker/REPORT.txt`;
  writer `$WT/util/ad-hoc/2026-11-26_juniper-cascor-worker_one_artifact_sweep_port.py` (`ceabb57e…`). It reports: 121
  publish tests (69 on `main`), the full suite 664 passed / 8 skipped (`main` 612 / the same 8); checker `1 of 1 pass`
  on the clone and the PR-head fetch with its proposed pins (`63992351…`, built on the canonical `1dd592c2…`: the
  worker's pin 18 lines `231b1999…` -> 31 `f5968714…`, `find_spec('juniper_cascor_worker')` in cascor's neutral form);
  59 of 59 mutations (18 of 18 by the rehearsals alone); screens pass, one `Allow-Symbol-Loss:` line per symbol; the
  memory budget passes `AGENTS.md` at 26,717 of 26,832 characters; the gate passed with two accepted pre-existing
  findings (`AGENTS.md:123-124`). The #274 lessons were applied before the PR opened (the PyPI JSON check's two causes
  kept apart; "installs", not "runs"; the neutral line).
- Its independent review started before 03:41:54Z (the brief now names the addenda's lessons as requirements, and the
  canonical pins file `1dd592c2…`).
- Checked: no mutation runner wrote under `/tmp` (the pilot's passes no `env=`, so pytest inherited the session's
  `TMPDIR`, the primary's `tmp/`; `/tmp` holds no pytest leftovers).
- Running: #274's fix-up, #844's fix-up, juniper-data's port, #238's review.

## Status (session `b71989`, 2026-11-26, after 03:56Z): #844's known gaps fixed; its review runs on the fixed head

- **juniper-canopy#844's fix-up** (its executor, resumed): one signed commit `e6557ec4cd6d603b2d1dfb534204316b219994df`
  on `dcc58bb5` (verified, reason valid; pushed 03:55:24Z-03:55:30Z by its log), 2 files: `docs/ci_cd/CICD_MANUAL.md`
  (the failed `Verify PyPI serves exactly these files` bullet split into "gave up waiting" = index lag, Re-run failed
  jobs, a fresh `pypi` approval, with `Verify TestPyPI still serves exactly these files` giving up before the upload
  taking the same re-run; and "found a mismatch" = only a new patch version; the lead-in now "When rung 1 refuses, or a
  check of the release run failed:") and `CHANGELOG.md` (the Docs bullet names both causes). The writer
  (`5fca1dca…`; the first commit's kept as `fixup/writer-commit1.py`) now requires its three count arguments and
  refuses a placeholder. Its report: `$WT/tmp/ports/juniper-canopy/REPORT_FIXUP.txt` (128 publish tests, unit lane 8546
  / 17 as before, checker `1 of 1` on the re-fetched head, 55 of 55 mutations re-run, screens on the two-commit range,
  the gate). The PR body was updated (both causes; cross-repo `#777`/`#763`/`#767` qualified as juniper-cascor#…,
  since canopy has its own #777).
- **#844's independent review** started then, on head `e6557ec4` (both commits), with the addenda's lessons as
  requirements.
- Running: #274's fix-up, juniper-data's port, #238's review, #844's review.

## Review of juniper-cascor-worker#238 (report: `$WT/tmp/ports/juniper-cascor-worker/review/REVIEW.txt`; a fresh `general-purpose` agent) -- COMPLETE

Verdict: **BLOCKER 0, MAJOR 0, MINOR 1, NIT 2**, on head `1965e557` (base `7df573f0`). The FINAL checker passes the
fetched head with the proposed pins (`63992351…`; only the worker's entry differs from the canonical `1dd592c2…`) and
fails it with the canonical file (the control); all 14 template blocks and the 307-line republish job raw
byte-identical; 121 publish tests pass (69 on the base), no new skip; 39 of 39 of the reviewer's own mutations caught;
the pin rehearsed with a real wheel built from the head under Python 3.12, 3.13 and 3.14 (26 of 26 as expected; metadata
alone passes only from a checkout root, the hazard the `cd` avoids); CI all green, `CLEAN`; one verified commit, one
`Allow-Symbol-Loss:` line per symbol.

| id | sev | finding | disposition (orchestrator `b71989`) |
|---|---|---|---|
| R-1 | MINOR | `docs/DEVELOPER_CHEATSHEET.md:282`: a `Verify PyPI serves exactly these files` that gave up waiting is sent to "Re-run failed jobs on the release run, within 30 days"; the step also runs in the republish job's dispatch run (the usual case past 30 days) | FIX-UP: name the run whose check gave up; the lesson added to the brief and sent to #274's fix-up and the juniper-data port |
| N-1 | NIT | the pinned step comment says "installs and imports" where the check only inspects | LEAVE: the sweep-wide wording (cascor-client's applied pin; cascor's `publish-protocol.yml`) |
| N-2 | NIT | labels "R4-5 of the sweep's review", "SWEEP item 23" cite documents only in juniper-ml worktrees' `tmp/` | LEAVE: plan v1.15.18 records the review ids and the SWEEP items (the plan already names SWEEP items) |

**Open item for the end of the sweep (two reviews point at it):** juniper-cascor-client's merged
`docs/REFERENCE.md:729` states only the mismatch cause of a failed `Verify PyPI serves exactly these files`; the
timeout cause (index lag: Re-run failed jobs on the run whose check gave up) is not stated. Not a misdirection (it
keeps the patch-version advice to the mismatch and never calls the case past the ladder), so it was not reopened when
#274's review found the MAJOR; a one-paragraph follow-up PR brings it level with the other ports.

## #274's fix-up, checked (session `b71989`, 2026-11-26 04:14Z)

- **The fix-up** (its executor, resumed): one signed commit `a93f10d67dd49082a210b7ed90f45862537e8c96` on `8ef0c329`
  (verified, valid), 4 files (+32 -19). Report: `$WT/tmp/ports/juniper-data-client/REPORT_FIXUP.txt`. The orchestrator
  read the workflow and docs patch (`gh api …/compare/8ef0c329…a93f10d6`): F1 (the failed `Verify PyPI serves exactly
  these files` paragraph now gives its two causes: a mismatch -> only a new patch version; "gave up waiting" -> index
  lag, "Re-run failed jobs on that run", a fresh `pypi` approval; it names "that run", so #238's R-1 holds), F2
  ("installs"), F3 (`print('TestPyPI install', …)`). The writer (revision 2, `c2295899…`; revision 1 kept as
  `fixup/r1/writer.py`) also lost its 39 implicit string concatenations (not in the PR). The executor reports 119
  publish tests, the full suite 665 / 18 as before, the checker 1 of 1 with the new pins and both controls failing,
  38 + 12 + 4 mutations, the screens on the two-commit range, the gate; CI at 04:11:16Z all 20 required success.
- **The orchestrator's check of the head as GitHub holds it** (04:13:34Z): the FINAL checker on `a93f10d6`'s
  `publish.yml`, template cascor `main` (`b6826ee6…`), pins the new proposal `824c50d9…` (built on the canonical
  `1dd592c2…`): `PASS`, `1 of 1 pass`. `apply_pin.py --dry-run`: only data-client's pin moves, `aa16d5b2…` (18 lines)
  -> `b60ce6b8…` (30 lines), the value #274's review predicted for its F3 fix.
- CI: `CLEAN`, 24 pass, 6 skipping. data-client#273 still OPEN (`078901ad`), so #274 merges first; its PR body says so.
- The executor is being resumed once more with the late #238 R-1 message (its text already names "that run"); the
  merge waits for that report.

## Landed: juniper-data-client#274 (session `b71989`, 2026-11-26); the recurrence port starts

- **The R-1 question on #274** (its executor's final report): the pushed text reads "Re-run failed jobs on that run",
  "that run" being the run whose check failed (the paragraph's lead-in), without naming the two runs or a 30-day window.
  Orchestrator's decision: ACCEPT as is, no third commit. It names the run whose check gave up, which is R-1's point
  (never "the release run" alone); the 30-day limit stands in rung 2 beside it.
- **The pin, applied** (`apply_pin.py`, 04:15:21Z): juniper-data-client's `Verify TestPyPI install` pin `aa16d5b2…`
  (18 lines) -> `b60ce6b8…` (30 lines). Pins file now
  `824c50d909da821a90bf2ff7d748066370b7e9f97170a176c9080dc0e4df17d4`; manifest regenerated, 7 paths. Backups
  `tmp/arc/pins.before-juniper-data-client-20261126T041521Z.json`, `tmp/arc/sweep_scripts.before-juniper-data-client-20261126T041521Z.sha256`.
  The FINAL checker on #274's head `a93f10d6` with the canonical file: `PASS`, `1 of 1 pass`.
- **MERGED 2026-11-26T04:15:39Z** as `4b78d540f3d598449be0f246eaf591c43bf8e71c` (parent `5c329a39`, verified, valid),
  by `util/safe_merge.py` (required checks green on `a93f10d6`; log `$WT/tmp/ports/juniper-data-client/merge/safe_merge.log`).
  The squash message holds both commits' messages and the `Allow-Symbol-Loss:` line. Post-Merge Main Verification
  `success`; CodeQL and CI/CD in progress at the read.
- data-client#273's session (`run-tests-rollout-recurrence-copy-landed-data-client-copy-next`) told that `main` moved
  and what its re-cut keeps (its section, Version 0.5.5).
- Ports landed: 2 of 7 (cascor-client, data-client). **juniper-recurrence's port** (its three publishers) started after
  04:15:29Z (the start of #274's merge run).

## #238's fix-up, checked; the worker's pin applied; #238 merging; the juniper-ml port starts (session `b71989`, 2026-11-26 04:25Z)

- **#238's fix-up** (its executor, resumed): one signed commit `5b7340f0aad19215f2d931b49518f2b02013ac5a` on `1965e557`
  (verified, valid), 2 files: `docs/DEVELOPER_CHEATSHEET.md:282` ("Re-run failed jobs on the run whose check gave up
  (the release run, or the republish's dispatch run), within 30 days of that run") and `CHANGELOG.md` (the Docs bullet
  likewise). The orchestrator read the patch (`gh api …/compare/1965e557…5b7340f0`). `publish.yml`, the test and
  `AGENTS.md` unchanged, so the mutation proof stands. Report: `$WT/tmp/ports/juniper-cascor-worker/REPORT_FIXUP.txt`.
- **`apply_pin.py` widened** (after it REFUSED the worker's proposal, correctly: built on the canonical `1dd592c2…`
  before data-client's pin was applied, its data-client entry was the old seed). It still takes only REPO's entries
  from a proposal; another repo's entry may now equal the current file's OR that repo's entry in any earlier canonical
  file (fix pass 11's `tmp/sweep/checker-r12/pins_r12_as_delivered.json` and every `tmp/arc/pins.before-*.json`).
  Negative control: a proposal with a tampered canopy entry is refused ("equal to no canonical version").
- **The pin, applied** (04:24:38Z): juniper-cascor-worker's `Verify TestPyPI install` pin `231b1999…` (18 lines) ->
  `f5968714…` (31 lines). Pins file now `19d6acd36d6ad0d0648ab160e20be8e863fba4c21d25e57e539a8b9c26fe125d`; manifest
  regenerated, 7 paths; backups `tmp/arc/pins.before-juniper-cascor-worker-20261126T042438Z.json` and the manifest's.
  The FINAL checker on #238's head `5b7340f0` with the canonical file: `PASS`, `1 of 1 pass`.
- **#238's merge** started (`safe_merge.py`; CI 20 pass, 3 pending, 5 skipping at the read).
- **juniper-ml's port** (its seven publishers) started then; its brief names R4-1, R4-5 (ci-tools, observability),
  the F2 edits and R5-F5, item G, ml's own gates (the CI wiring drift test, the memory budget, the date check,
  REFERENCE.md's version row) and the concurrent-PR check.
- Running: juniper-data's, juniper-recurrence's and juniper-ml's ports; #844's review.

## Landed: juniper-cascor-worker#238 (session `b71989`, 2026-11-26)

- **MERGED 2026-11-26T04:26:48Z** as `f9122a8a96e3b117b71c01a3a1a267107c727b2b` (parent `7df573f0`, verified, valid),
  by `util/safe_merge.py`'s auto-merge net pinned to `5b7340f0` once the required checks were green (log
  `$WT/tmp/ports/juniper-cascor-worker/merge/safe_merge.log`). The squash message holds both `Allow-Symbol-Loss:` lines
  (one per symbol). Its post-merge runs (Post-Merge Main Verification, CodeQL, CI/CD) were in progress at the read.
- juniper-data-client `main` `4b78d540`'s post-merge runs, re-read before 04:27:14Z: Post-Merge Main Verification,
  CodeQL Analysis and CI/CD Pipeline all `success`.
- Ports landed: 3 of 7 (cascor-client, data-client, cascor-worker).

## Status (session `b71989`, 2026-11-26 04:32Z): the fifth port is open; its review runs

- **juniper-data#553** opened 04:28:47Z (`createdAt`), head `62e0854a6fe608b2bb7e397d78a5541e9b1a8aef`, one signed
  commit on `8e08d209`, 10 files (+1182 -218, and the new `juniper_data/tests/unit/test_publish_docs_bounds.py`):
  `publish.yml`, `CHANGELOG.md`, `docs/DEVELOPER_CHEATSHEET.md`, `docs/REFERENCE.md`, `docs/ci_cd/CICD_MANUAL.md`,
  `CICD_QUICK_START.md`, `CICD_REFERENCE.md`, `test_publish_one_artifact.py`, `test_testpypi_install_verify.py`. Report
  `$WT/tmp/ports/juniper-data/REPORT.txt`; writer `$WT/util/ad-hoc/2026-11-26_juniper-data_one_artifact_sweep_port.py`
  (`f789b881…`; `--changelog-cases 125 --changelog-mutations 51` required). It reports: 160 publish-related tests
  (`JuniperData`, `-m "unit and not slow"`), the unit lane 2665 passed / 15 skipped; actionlint clean (the base failed
  SC2086); checker `1 of 1 pass` on the clone and the PR-head fetch (`notify-consumers.yml` `e17ddc9b…` beside it) with
  its proposed pins (`c67ad8c6…`, built on the canonical `19d6acd3…`: juniper-data's pin 18 lines `3783295d…` -> 31
  `4a05dbb2…`, `find_spec('juniper_data')` in the neutral form); 51 of 51 mutations (16 of 16 by the rehearsals);
  the symbol screen 5 waived (one line each) and 1 warning (the removed constant `INSTALL_CHECK`); the gate passed with
  four accepted pre-existing findings. The #238 lesson was applied before the PR opened. Its template pins were parsed
  YAML (not raw text as item G assumed); it kept them, refs stripped, and added #206's raw-text pins, since the checker
  does not compare YAML comments outside run scripts.
- Its independent review started before 04:32:07Z.
- Running: juniper-recurrence's and juniper-ml's ports; #844's and #553's reviews.

## Review of juniper-canopy#844 (report: `$WT/tmp/ports/juniper-canopy/review/REVIEW.txt`; a fresh `general-purpose` agent, on head `e6557ec4`, both commits) -- COMPLETE

Verdict: **BLOCKER 0, MAJOR 0, MINOR 2, NIT 3**. The FINAL checker passes the head with the proposed pins
(`0fa60256…`) and fails it with the canonical file only on the three added comment groups (the control); all 14
template steps and the 307-line republish job raw byte-identical; the parsed structure equals the faithful simulation;
115 publish tests pass (113 + 2), 13 smoke, 69 on the base, no new skip (CI's JUnit agrees); 14 of 14 behaviour
mutations and one docs-bounds edit caught; the pin rehearsed under `bash -e` with a real venv (seven scenarios; the
`cd` is what stops a checkout's package passing); the sparse checkout replayed; the addenda's lessons all met. CI run
45751954645: 19 of 21 required pass; `UI Sub-suite (Playwright)` failed on
`test_ws_silent_poll_liveness.py::test_populated_store_survives_poll_after_stop[chromium]`, which failed the same way
on `main` (run 45530414633), and `Quality Gate` fails on it alone; the first commit passed everything (45748645895).

| id | sev | finding | disposition (orchestrator `b71989`) |
|---|---|---|---|
| M1 | MINOR | `docs/ci_cd/CICD_REFERENCE.md:565` says the docs-bounds module pins "the numbers in this section"; the section's "kept 90 days" is not pinned (mutation R15 survives) | FIX-UP: narrow the claim, as cascor's "this paragraph" |
| M2 | MINOR | the template's YAML comments outside `run:` scripts are guarded by neither canopy's tests nor the checker (parsed YAML): restoring the sweep's old republish or witness comment (R17, R18) passes both; the PR body says comment drift is "the cross-repo checker's to catch" | PR BODY: correct the claim. NO new pins: item 23/G gave comment-level pins only to the ports that had raw-text pins (canopy and recurrence had none); recorded as an arc-wide RESIDUAL for plan v1.15.18 (juniper-data#553's executor found the same gap and added raw-text pins there) |
| N1 | NIT | `CHANGELOG.md:272-273` says the module requires "the two docs" to state the bounds; the JSON-check bounds are required in `CICD_REFERENCE.md` only | FIX-UP |
| N2 | NIT | test comments cite `util/ad-hoc/2026-11-23_publish_port_template_identity.py`, not on juniper-ml `main` | LEAVE: it lands with plan v1.15.18 |
| N3 | NIT | the PR body's `Build and Validate` bullet omits the changed `Upload dist artifacts` comment | PR BODY |

The fix-up goes to #844's executor (resumed); its new head re-runs the Playwright job. The pin: apply canopy's entry
alone (the proposal was built on `d539f05f…`; `apply_pin.py` accepts its other entries as earlier canonical values).

## #844's second fix-up, checked; canopy's pin applied; #844 merging (session `b71989`, 2026-11-26 05:02Z)

- **The second fix-up** (its executor, resumed): one signed commit `704896b422a27caaad67e224425c54db9728b891` on
  `e6557ec4` (verified, valid), 2 files (`docs/ci_cd/CICD_REFERENCE.md:565`: the docs-bounds module now named for
  exactly the bounds it pins, M1; `CHANGELOG.md`: which doc must state which bound, N1). The PR body corrected for M2
  (comment drift is caught only inside `run:` scripts; elsewhere review alone keeps it) and N3. Report:
  `$WT/tmp/ports/juniper-canopy/REPORT_FIXUP2.txt` (128 tests, the unit lane 8546 / 17, 55 + 17 mutations, the screens
  on the three-commit range, the gate). Writer now `9f5fe73f…`.
- **The pin, applied** (05:01:42Z): juniper-canopy's `Verify TestPyPI install` pin `36d5694d…` (18 lines) ->
  `ffc59071…` (23 lines; comments only). Pins file now
  `e3723222b23b4a8e5f4bf34e7beaa90a0b8c0195ece5894c8cdaca80804000ea`; manifest regenerated, 7 paths; backups
  `tmp/arc/pins.before-juniper-canopy-20261126T050142Z.json` and the manifest's. The FINAL checker on #844's head
  `704896b4` with the proposal and with the canonical file: `PASS`, `1 of 1 pass` both.
- **#844's merge** started (`safe_merge.py`); its required checks were in progress, the Playwright sub-suite among them.

## Review of juniper-data#553 (report: `$WT/tmp/ports/juniper-data/review/REVIEW.txt`; a fresh `general-purpose` agent, on head `62e0854a`) -- COMPLETE

Verdict: **BLOCKER 0, MAJOR 0, MINOR 1, NIT 5**. The FINAL checker passes the head with the proposed pins (`c67ad8c6…`;
only juniper-data's entry differs from the canonical `19d6acd3…`; `notify-consumers.yml` `e17ddc9b…` beside it) and
fails it with the canonical file (the control); every template block and the republish job byte-identical; 133 publish
tests pass and 27 notify-consumers tests (base 73), all `unit`-marked, no new skip; 14 of 14 of the reviewer's own
mutations caught (the find-step and install-script ones by the rehearsals alone too); the pin on a real wheel built from
the head under `bash -e` (present: exit 0; bare directory or metadata only: exit 1, with `PYTHONOPTIMIZE=1` too); each
of the six removed symbols has an equal or stronger replacement; a republish dispatch skips `notify-consumers` (build
skipped, `needs: pypi`), stated truly everywhere; the addenda met (two causes, the run named, lead-ins, "installs");
the writer replays (0 of 480 files differ). CI: every required check passes (`Slow Tests` skipped, as on every PR).
The reviewer saw `BLOCKED` with no check failing; re-read by the orchestrator: `CLEAN`, `MERGEABLE`, 0 unresolved
threads (juniper-data-client's ruleset carries the same `require_extra_approval_for_unattributed_changes` and merged
`CLEAN`, so the earlier state was transient).

| id | sev | finding | disposition (orchestrator `b71989`) |
|---|---|---|---|
| R-1 | MINOR | two test comments false of juniper-data, copied from cascor (`:618`, "runs the package") and cascor-client (`:784`, "holds juniper_cascor_client/") | FIX-UP (comments only; the writer's TEST_MODULE too) |
| R-2 | NIT | `OTHER_DIST_NAME` (`:65`) is unused | FIX-UP: use it or drop it |
| R-3 | NIT | `assert not _cancels(...)` beside the base's stricter `"concurrency" not in wf` cannot fail | FIX-UP: keep the base's stricter line alone |
| R-4 | NIT | the pinned comment's "installs and imports" where the check imports nothing of the package | LEAVE: the template's sweep-wide wording (as #238's N-1); a later pin round rewords every find_spec port together (residual for plan v1.15.18) |
| R-5 | NIT | spelled-out try counts ("five") unpinned beside the pinned digit forms | LEAVE (optional) |
| R-6 | NIT | CHANGELOG "to the entry below" is two entries below | FIX-UP: "to juniper-data#543's entry below" |

The fix-up goes to #553's executor (resumed).

## Landed: juniper-canopy#844 (session `b71989`, 2026-11-26)

- **MERGED 2026-11-26T05:14:24Z** as `aa9ac7346ac4d78476518befbf08e5001a81b8dc` (parent `2cec71fe`, verified, valid),
  by `util/safe_merge.py`'s auto-merge net pinned to `704896b4` once the required checks were green (the Playwright
  sub-suite passed on this head; log `$WT/tmp/ports/juniper-canopy/merge/safe_merge.log`). The squash message keeps
  both `Allow-Symbol-Loss:` lines (one per symbol).
- Ports landed: 4 of 7 (cascor-client, data-client, cascor-worker, canopy). Open: juniper-data#553 (fix-up running),
  juniper-recurrence#241 (review running); juniper-ml (port running).

## #553's fix-up, checked; juniper-data's pin applied; #553 merging (session `b71989`, appended 2026-11-26 05:18:59Z)

- **The fix-up** (its executor, resumed): one signed commit `9cf7158d52447396c50463caf0ee93cc6d37f74e` on `62e0854a`
  (verified, valid), 2 files (+6 -14): `test_publish_one_artifact.py` (R-1's two comments, R-2's `OTHER_DIST_NAME`
  used, R-3's always-true assertion and `_cancels` dropped) and `CHANGELOG.md` (R-6). No workflow, doc, pin, digest or
  case count moved. Report `$WT/tmp/ports/juniper-data/REPORT_FIXUP.txt` (160 tests, the checker 1 of 1, 51 of 51
  mutations, the screens with the same six findings, the gate). Writer now `3327f4e6…`.
- **The pin, applied** (05:18:38Z): juniper-data's `Verify TestPyPI install` pin `3783295d…` (18 lines) -> `4a05dbb2…`
  (31 lines). Pins file now `9d38c76fac1cbdb36f2088a3d223baa697a7fdd01330711682ae0aa763481c30`; manifest regenerated, 7
  paths; backups `tmp/arc/pins.before-juniper-data-20261126T051838Z.json` and the manifest's. The FINAL checker on
  #553's head `9cf7158d` with the proposal and with the canonical file: `PASS`, `1 of 1 pass` both.
- **#553's merge** started (`safe_merge.py`); `BLOCKED` at the read, its CI running on the new head.

## Landed: juniper-data#553 (session `b71989`, 2026-11-26)

- **MERGED 2026-11-26T05:24:33Z** as `a0bb1558a7dac16698e6d3f2fb651cc466fccb38` (parent `8e08d209`, verified, valid),
  by `util/safe_merge.py`'s auto-merge net pinned to `9cf7158d` once the required checks were green (log
  `$WT/tmp/ports/juniper-data/merge/safe_merge.log`). The squash message keeps all six `Allow-Symbol-Loss:` lines.
- Ports landed: 5 of 7 (cascor-client, data-client, cascor-worker, canopy, data). Open: juniper-recurrence#241 (review
  running); juniper-ml (port running).

## Review of juniper-recurrence#241 (report: `$WT/tmp/ports/juniper-recurrence/review/REVIEW.txt`; a fresh `general-purpose` agent, on head `d7adc41c`) -- COMPLETE

Verdict: **BLOCKER 0, MAJOR 0, MINOR 2, NIT 3**. The FINAL checker passes all three publishers with the proposed pins
(`b62731ee…`; only recurrence's three entries change, comment lines only) and fails each with the canonical file
only at its install pin (the control); the 10 template steps and the whole republish job raw byte-identical to cascor's
sub-package publishers, comments included; each `PUBLISH_TAG_PREFIX` equals its guard's literals, the guard's
dispatch branch is #777's M4, the top comment is item 2's; line 22 reads `#        owner       = pcalnon` again
(byte-equal to before #237); 204 publish tests (base 121), no new skip, CI's app lane +83 = the module's growth; each
install check imports its package, so no `find_spec` (probed under `python -S`); 14 of 14 of the reviewer's own
mutations caught; the writer replays (177 files, none differ); CI all green, `CLEAN`; one verified commit, one waiver.

| id | sev | finding | disposition (orchestrator `b71989`) |
|---|---|---|---|
| F1 | MINOR (the reviewer: MAJOR read strictly) | `README.md:214-215` says a tag that is not the prefix + the exact version is refused "before any request"; a prefixed, inexact tag (`juniper-recurrence-v0.3.1-beta`) passes the find step's prefix check and fails later, at the TestPyPI fetch, publishing nothing (probed) | FIX-UP: the review's text (cascor's MANUAL:713 keeps the two apart) |
| F2 | MINOR | the module pins the three copies equal to each other, no digest pins: an edit made alike in all three `run:` scripts passes the suite (the checker catches it, P1, P2); YAML comments outside `run:` pass both (P3, P4) | LEAVE: the design from #236 and the brief's table; the arc-wide comment-guard RESIDUAL (as canopy's M2) for plan v1.15.18; the PR body corrected if it claims more |
| N1 | NIT | `README.md:232-234` lists the step's runs without a plain dispatch's re-fire | FIX-UP |
| N2 | NIT | ragged line breaks (`README.md:178`, `:186`; client `AGENTS.md:74-76`) | FIX-UP: rewrap |
| N3 | NIT | `publish-recurrence-model.yml:15-17` header (pre-existing) | LEAVE: not made false by the sweep |

The fix-up goes to #241's executor (resumed).

## The cascor-client follow-up is open: juniper-cascor-client#207 (session `b71989`, 2026-11-26)

- **juniper-cascor-client#207** (created 05:47:48Z), branch `docs/publish-pypi-check-two-causes`, head
  `faaf6538bd003b8a018f951ddbf560e3f6d4815f`, one signed commit on `beb6b349` (#206's merge; verified, valid), 2 files
  (+10 -3): `docs/REFERENCE.md` (the failed `Verify PyPI serves exactly these files` paragraph now gives both causes:
  a mismatch -> only a new patch version; "gave up waiting" -> index lag, "Re-run failed jobs on the run whose check
  gave up (the release run, or the republish's dispatch run), within 30 days of that run", a fresh `pypi` approval;
  version 0.1.7 -> 0.1.8) and `CHANGELOG.md` (one `[Unreleased]` entry). Report:
  `$WT/tmp/ports/juniper-cascor-client-followup/REPORT.txt`; writer
  `$WT/util/ad-hoc/2026-11-26_juniper-cascor-client_pypi_check_two_causes.py` (`e7a8dd3b…`). Tests 121 publish / 720
  full (8 gitleaks skips, as `main`), doc links, pre-commit, the screens (no Python changed), the gate (one accepted
  pre-existing finding, `docs/REFERENCE.md:661`). The orchestrator read the whole diff (in the report).
- **Its merge is OUTSIDE the owner's approval of 01:47:14Z** (the 7 port PRs and this arc's juniper-ml docs PRs): ask
  the owner before merging it.

## #241's fix-up, checked; recurrence's three pins applied; #241 merging (session `b71989`, 2026-11-26)

- **The fix-up** (its executor, resumed): one signed commit `57559a28f8329a3aeaefabbfd100fb9908692e44` on `d7adc41c`
  (verified, valid), 2 files (+21 -22): `juniper-recurrence/README.md` (F1, the review's text verbatim; N1 in two
  places, the sentence the finding cites and the remedy's bracket list; N2 rewrapped, words unchanged) and
  `juniper-recurrence-client/AGENTS.md` (N2). The PR body corrected for F2 (neither guard compares a YAML comment
  outside a `run:` script; the arc-wide residual). Report `$WT/tmp/ports/juniper-recurrence/REPORT_FIXUP.txt` (204 +
  2 tests, the checker 3 of 3, the review's raw-text block comparison 66 IDENTICAL, the screens, the gate). Writer
  revision 2 `7ab9ab51…`. The orchestrator accepts N1 in both places (both make the README true). CI on `57559a28`:
  37 success, 1 skip (`Bench smoke`, as before).
- **The pins, applied** (06:12:25Z), recurrence's three entries from the rebuilt proposal (`da50213c…`, built on the
  canonical `9d38c76f…`): app `1065e246…` (19) -> `66ad441e…` (29), client `9f6db030…` (20) -> `ab1ddc68…` (28),
  model `bee31e9e…` (20) -> `221d0462…` (33). Pins file now
  `da50213c00c12377c386e1698b5a6fc1e3488be83f357c0aaf7090ebaddc3d86`; manifest regenerated, 7 paths; backups
  `tmp/arc/pins.before-juniper-recurrence-20261126T061225Z.json` and the manifest's. The FINAL checker on #241's head
  with the proposal and with the canonical file: `3 of 3 pass` both. `CLEAN`.
- **#241's merge** started (`safe_merge.py`).
- Open: juniper-ml's port (running); juniper-cascor-client#207 (the follow-up; needs the owner's approval).

## Landed: juniper-recurrence#241; the done-check reads 11 of 18 (session `b71989`, 2026-11-26)

- **MERGED 2026-11-26T06:12:43Z** as `8a5a062eb8e7c5f88f44983f0ce85cc98bff1107` (parent `2ce346da`, verified, valid),
  by `util/safe_merge.py` once the required checks were green on `57559a28` (log
  `$WT/tmp/ports/juniper-recurrence/merge/safe_merge.log`). The squash message keeps its `Allow-Symbol-Loss:` line.
- **Ports landed: 6 of 7** (cascor-client #206, data-client #274, cascor-worker #238, canopy #844, data #553,
  recurrence #241). Open: juniper-ml's port (running); the follow-up juniper-cascor-client#207 (owner's approval).
- **The done-check** (`$WT/tmp/s2/verify_all_mains_v3.bash`, after 06:12:46Z; output
  `$WT/tmp/ports/verify-all-mains-v3/<stamp>/`): the FINAL checker `a452db3d…`, the canonical pins `da50213c…`, every
  repo's `main` (cascor `5e3d9801`, canopy `aa9ac734`, data `a0bb1558` with `notify-consumers.yml` `e17ddc9b…`,
  data-client `4b78d540`, cascor-client `beb6b349`, cascor-worker `f9122a8a`, recurrence `8a5a062e`, ml `bceac63c`):
  every port repo `exit 0`, juniper-ml `0 of 7` (unported): **`11 of 18 pass`**.

## The owner's rulings on #207 and on the arc's merges (session `b71989`, 2026-11-26)

1. **#207** (`AskUserQuestion`, header "Merge #207", asked after 06:13:35Z, answered by 11:27:00Z): "juniper-cascor-client#207
   is a small docs follow-up to the merged port #206 … May I merge it with util/safe_merge.py once its CI is green?"
   **Answer, verbatim: "Yes, merge it (Recommended)"**, whose option text read: "I merge juniper-cascor-client#207 with
   util/safe_merge.py once its required checks are green, and record it with the ports." Not chosen: "Leave it for
   me", "Close it".
2. **The arc** (the owner's own message, received at 11:27:00Z, mid-turn): **"merge approval granted for this work
   arc"**. This session's (`b71989`) merges of this arc's PRs are approved; a later session asks again.

The dialog held this session from after 06:13:35Z to 11:27:00Z; #2673's review finished meanwhile.

## Landed: juniper-cascor-client#207; the review of juniper-ml#2673 (session `b71989`, 2026-11-26)

- **juniper-cascor-client#207 MERGED 2026-11-26T11:27:26Z** as `7e1399d8e7accfe513ee6f094c96b5121326f416`, by
  `util/safe_merge.py` (required checks green on `faaf6538`; log
  `$WT/tmp/ports/juniper-cascor-client-followup/merge/safe_merge.log`), under the owner's "Yes, merge it".

### Review of juniper-ml#2673 (report: `$WT/tmp/ports/juniper-ml/review/REVIEW.txt`; a fresh `general-purpose` agent, on head `7dd1466f`, both commits) -- COMPLETE

Verdict: **BLOCKER 0, MAJOR 0, MINOR 3, NIT 5**. The FINAL checker passes all seven with the proposed pins
(`142b4714…`; juniper-ml's seven entries; its three recurrence entries predate recurrence's applied pins: apply ml's
alone) and fails all seven with the canonical file (the control); every template block and the whole republish job
byte-identical (130 of 130 step blocks, 13 of 13 whole-job comparisons, against cascor's publisher or both
sub-package publishers); the pinned digests recompute from cascor's file (item G, normalized); R4-1 (both modules find
the step in the job named `Verify the TestPyPI install`; a miss fails; TestPyPI `{id-token: write}`; 3 skip constructs
-> 0), R4-5 (real wheels of ci-tools 0.9.1 and observability 0.4.3: present 0; metadata only or namespace dir 1, with
`PYTHONOPTIMIZE` 1 and 2), R5-F5 and the F2 edits met; the four publish suites green on 3.12.16, 3.13.18, 3.14.7 and
3.15.2 (92 / 30 / 13 / 2), no new skip; commit 1's tree reproduces CI's six 3.12 failures, the second commit's fix is
the right reason; 13 of 14 of the reviewer's own mutations caught (M14, F2); the wiring drift test, the memory budget
(AGENTS.md 27721 / 28000) and the ceremony (`HALT_TESTPYPI`) fine; both commits verified; the screens pass (5 findings,
3 waived, 2 constants WARN); CI all required green, `CLEAN`; no other open PR touches the 18 files.

| id | sev | finding | disposition (orchestrator `b71989`) |
|---|---|---|---|
| F1 | MINOR | `docs/REFERENCE.md:10116`, the PyPI-publish procedure note's `:712` and the PR body: "the re-run uploads the same bytes … and repeats both checks" is false when the lag-failed job is `Verify the TestPyPI install` (nothing re-uploads; only the install check repeats); from SWEEP_BRIEF item D's own wording | FIX-UP: cascor's MANUAL:709 wording |
| F2 | MINOR | `test_publish_docs_bounds.py` pins none of the docs' derived figures ("four waits, ~40s", "~60s"); M14 (the pre-sweep "five waits, ~50s") passes every suite and the checker | FIX-UP: digits, pinned from the workflows |
| F3 | MINOR | `tests/test_publish_one_artifact.py:4` names the person ("The Overtoad's directive") where the base said "owner" | FIX-UP: "The directive of 2026-11-15:" |
| N1 | NIT | the package check's "nothing" case is under-asserted | FIX-UP |
| N2 | NIT | `docs/REFERENCE.md:10130` (rung 2 after a plain dispatch) | FIX-UP: cascor MANUAL:712's sentence |
| N3 | NIT | `docs/REFERENCE.md:5059` dates #777 by the port | FIX-UP |
| N4 | NIT | `publish.yml:255` (a repo comment) reads as if a refused republish could still finish the release | FIX-UP |
| N5 | NIT | `publish.yml`'s header "Last Modified" not moved | FIX-UP |

The fix-up goes to #2673's executor (resumed). Arc-wide notes from this review: the sub-package banner comments' "runs
the package" is cascor's text (as elsewhere); ci.yml's actionlint with shellcheck/pyflakes does not finish (also on
main).

## Note (session `b71989`, 2026-11-26T11:37:05Z): data-client#273 resolved against #274 by its own session

The run_tests session (`run-tests-rollout-recurrence-copy-landed-data-client-copy-next`) reported by message: it reproduced
the footer conflict with `git merge-tree` against data-client `main` `4b78d540` (`docs/REFERENCE.md` only); its fix commit
`38307835` on `feat/local-test-runner` moves § Running Tests Locally above § Test Markers and Commands and restores
the footer to the base's lines, so `main`'s (Version 0.5.5, November 26, 2026) survives; merge-tree clean; the merged
tree passed `util/run_tests.py all` (727 unit tests, #274's included); the owner approved its merge. Nothing needed
from this arc.

## Note (session `b71989`): #2673's branch was synced and auto-merge armed outside this session

Read 2026-11-26 (before the time below): #2673's head moved from `7dd1466f` to `2eb9a9306278dd11ac27d154b139116b8d8076c6`,
"Merge branch 'main' into fix/publish-one-artifact-sweep" (author pcalnon, committer web-flow, 11:42:13Z; parents
`7dd1466f` and main's `8378665f`; it brings only one prompts/ handoff file, none of the PR's 18). Auto-merge (squash)
was enabled at 11:42:15Z by the owner's account. Neither this session nor its executor ran either. The executor's
fix-up (F1-F3, N1-N5; report `$WT/tmp/ports/juniper-ml/REPORT_FIXUP.txt`) stopped at its stale `expected_head`
and was told to re-pin to the current head and push, not to touch the armed net. If the net merges `2eb9a930`
first (allowed: no BLOCKER or MAJOR open), the fix-up's six files go as a follow-up PR on fresh `main`.

## Landed: juniper-ml#2673 -- ALL PORTS LANDED; the done-check reads `18 of 18 pass` (session `b71989`, 2026-11-26)

- **#2673's fix-up** (its executor, after the re-pin): one signed commit `67b6db2049fb575d8c567c52bb679169a1cff70f` on
  the sync merge `2eb9a930` (verified, valid), 6 files (F1-F3, N1-N5; report
  `$WT/tmp/ports/juniper-ml/REPORT_FIXUP.txt`, its OUTCOME section). The FINAL checker on `67b6db20`: `7 of 7 pass`.
- **The pins, applied** (11:55:32Z): juniper-ml's seven entries (proposal `142b4714…`, built before recurrence's pins
  were applied; `apply_pin.py` took ml's entries alone). Pins file now
  **`faa198c274779db9eafc2451bcdc799a75066378290de10b44426748e0bc9e41`**, equal byte for byte to the executor's own
  rebuild on the canonical `da50213c…` (its `pins.proposed.v3-seedda50213c.json`). All 18 pins are reviewed final
  scripts. Manifest regenerated, 7 paths OK; backups `tmp/arc/pins.before-juniper-ml-20261126T115532Z.json` and the
  manifest's.
- **The merge**: `safe_merge.py`'s first run REFUSED at 12:52:36Z ("went BEHIND 3 times without a stable green head;
  main is moving faster than CI completes") and disarmed its net; the PR stayed open, up to date at `1730127c` (the
  checker there: `7 of 7 pass`). The retry armed the net pinned to `1730127c`: **MERGED 2026-11-26T13:08:46Z** as
  `e2e463ead35275df18b96a62ec9b49d9e0fb58c9` (parent `6ffdaab6`, verified, valid), the squash keeping all five
  `Allow-Symbol-Loss:` lines (log `$WT/tmp/ports/juniper-ml/merge/safe_merge.log`).
- **The done-check** (`$WT/tmp/s2/verify_all_mains_v3.bash`, after 13:08:47Z): the FINAL checker `a452db3d…`, the
  canonical pins `faa198c2…`, every repo's `main` (cascor `5e3d9801`, canopy `374c0fb9`, data `a0bb1558` with
  `notify-consumers.yml` `e17ddc9b…`, data-client `51e34f71`, cascor-client `7e1399d8`, cascor-worker `f9122a8a`,
  recurrence `8a5a062e`, ml `e2e463ea`): every repo `exit 0`, **`18 of 18 pass`**.
- **The ports are DONE**: 15 publishers in 7 repos (#206, #274, #238, #844, #553, #241, #2673) and the follow-up #207.
  Next: plan v1.15.18 (handoff
  `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-26_one-artifact-sweep-all-ports-landed-18-of-18-plan-v1-15-18-next.md`).

## Session `b71989` ends: the handoff landed (2026-11-26)

- juniper-ml#2676 (the handoff, one file) MERGED 2026-11-26T13:41:52Z as `3db71b5b673d2e3f71f909d65f9ee4b66e33b37f`
  (`safe_merge.py`; log `$WT/tmp/s2/handoff_pr/merge/safe_merge.log`). The next session starts from
  `prompts/thread-handoff_automated-prompts/HANDOFF_2026-11-26_one-artifact-sweep-all-ports-landed-18-of-18-plan-v1-15-18-next.md`:
  plan v1.15.18 on a fresh clone of juniper-ml `main`.
- Keep `$W` and `$WT` until plan v1.15.18 lands their files and `tmp/` is archived.
