# juniper-canopy v0.10.0 – :lock: SECURITY RELEASE (MINOR)

**Release Date:** 2026-11-15
**Release Type:** MINOR (security-bearing)
**Priority:** High: upgrade every juniper-canopy deployment that reports to Sentry, first any with `ws_auth_enabled` on
**Package Affected:** juniper-canopy

---

This is a security-bearing minor release of `juniper-canopy` v0.10.0. Its image locks `juniper-observability` 0.4.2, and its wheel now floors `juniper-observability>=0.4.2,<0.5.0`, whose `configure_sentry` scrubs transactions as well as error events and filters four more credential headers. Under 0.4.1, once a Sentry DSN was set, a request's `Sec-WebSocket-Protocol`, `X-CSRF-Token` and `X-XSRF-Token` headers reached Sentry in every error event and transaction, and `Sec-WebSocket-Protocol` carries canopy's own WebSocket key (`bearer, <key>`) when the opt-in `ws_auth_enabled` is on. canopy leaves `send_pii` off, so the `X-API-Key` and cookie leaks that 0.4.2 also closes were not reachable here. It also floors `juniper-service-core>=0.7.2,<0.8.0`, a plain patch. 0.4.2 does not close every path to Sentry: its notes leave query strings, Sentry Logs, request bodies, breadcrumbs and exception values for 0.4.3. For canopy the first includes the `?api_key=` WebSocket query parameter, which reaches Sentry under the default `send_pii=False`. The second Security entry makes CI's Gitleaks step load gitleaks' built-in ruleset; it had loaded none and could not fail. The release also fixes F-CANOPY-069 (under every dash 3.x the dashboard was inert; the fix works on dash 3 too) and raises the runtime floor to `dash>=4.0.0`, the line canopy tests, so an environment still on dash 3 moves to dash 4 with it.

---

## Security Impact (Medium)

| Attribute | Value |
| --------- | ----- |
| **Package** | `juniper-canopy` |
| **Fixed in** | 0.10.0 |
| **Vulnerability class** | Fixed by juniper-observability 0.4.2, which this release floors and its image locks: sensitive information sent to an external service ([CWE-201](https://cwe.mitre.org/data/definitions/201.html)) |
| **Advisory** | None. Internal findings, fixed in juniper-observability 0.4.2, which its own notes rate Medium: round-42 finding F2 (2026-09-24) and the validation of consolidated-plan item P3-07 (2026-11-08); there is no CVE or Dependabot alert |

---

## Changes in v0.10.0

### Added

- **Regression tests harvested from the Cursor flood-4 test PRs** (canopy#789, #792, #794, #795): four new test
  files over four workflows. `src/tests/regression/test_bandit_sarif_upload.py` pins the Security Scans job's
  `bandit[sarif]` install, its `|| BANDIT_EXIT=$?` capture, and the SARIF upload, which runs `if: always()` and
  whose failure fails the job only on a pull request (`continue-on-error: ${{ github.event_name != 'pull_request' }}`);
  it runs the job's Bandit step against a stub, and the weekly `security-scan.yml` must install the same extra and
  not swallow a formatter error with `|| true` (#780, #781). `src/tests/regression/test_lockfile_regen_empty_payload.py`
  runs `lockfile-update.yml`'s commit step: an empty encode and a failing `base64` exit before `jq` or `gh`, the
  mutation carries the lockfile's own bytes and the trigger's headline, and a GraphQL error or an unchanged lockfile
  commits nothing (#775). `src/tests/unit/test_agents_md_date_check.py` runs `agents-md-touch-up.yml`'s verify step
  over each header state (missing, not YYYY-MM-DD, future, today, bumped, unchanged, a base tip that moved the
  header) and pins its SHA-pinned full-history checkout and read-only permissions.
  `src/tests/regression/test_codecov_token_upload.py` pins that every `codecov/codecov-action` step sends
  `${{ secrets.CODECOV_TOKEN }}` and uploads the xml its job's pytest writes (#779). Each was re-run on `main` and
  mutation-checked against the workflow line it pins, and
  corrected where the head was wrong. #792 ran the coreutils form `base64 -w0 FILE` on the required macOS leg,
  whose BSD `base64` refuses the file operand (5 failures); off Linux, a runner whose `base64` fails a probe of
  that exact form on a one-byte file now gets a stand-in for that one form, and nothing is skipped. #792 also ran the
  cases meant to stop before `jq` with the step's own `/tmp/lockfile-commit.json` path, so a regressed guard wrote
  that file on the host and the check that no body was written read a path the step never wrote; every run now
  relocates both of the step's paths under `tmp_path`. #794's fixture read the developer's global git config: a
  signing config asked the signing key for every fixture commit, `color.ui=always` broke the diff the step parses,
  and a refusing `core.hooksPath` hook failed every commit. Its git calls now pass
  `-c commit.gpgsign=false -c tag.gpgsign=false`, and they and the step it runs set `GIT_CONFIG_GLOBAL` to the
  null device and `GIT_CONFIG_NOSYSTEM=1`. Test-only.
- **Regression tests harvested from the Cursor flood-4 round-2 test PRs** (canopy#800, #801): two new test files.
  `src/tests/unit/backend/test_apply_partition_flat_legs.py` pins that `apply_params` reads `applied` / `skipped`
  from each leg's own result and unions them (F-CANOPY-065, #763). The mixed-apply test already on `main`
  (`src/tests/integration/test_n5_apply_params_ux.py`) pairs a WebSocket result whose partition is at the top level
  with a REST envelope whose partition sits under `data`. Those keys do not collide, so reading the partition from
  one dict merged from both legs stays green there. A flat REST body uses the same top-level keys, so a merge
  replaces the WebSocket leg's lists, and an empty `skipped` wipes the key that leg declined; the new tests fail on
  that regression. They also pin that a `/ws/control` ack whose `data.result` is not a dict unwraps to `{}`, not to
  that value (`dict.update` raises on the list, string and number they send) or to the command envelope.
  `src/tests/unit/test_schema_drift_nested_equality.py` pins the JSON equality of
  `util/check_juniper_data_generator_schemas.py` inside arrays (#737). `diff_json` walks objects and hands every
  other value, `enum` and `anyOf` included, to `json_equal`, and both committed snapshots carry both. Python's `==`
  says `[0, 1] == [false, true]` and `[{"minimum": 1}] == [{"minimum": true}]`, so a `json_equal` that compared
  arrays with `==` would miss exactly the drift the job exists to catch, while every test on `main` stayed green
  (`src/tests/unit/test_check_juniper_data_generator_schemas.py` checks booleans against numbers, and `NaN`, as
  bare values only). The new tests fail on that regression, through `json_equal` and through the drift report.
  `NaN` equals `NaN` at any depth, and the drift report's `NaN` case pins that rule but cannot catch an `==` over
  whole arrays: `json` parses every `NaN` to one shared float, which list equality matches by identity, so an `==`
  over arrays would not report a matching `NaN` as drift, contrary to the draft's text. The script's docstrings now
  state the rule for arrays, with that correction. Tests and docstrings only.
- **Documentation harvested from the Cursor flood-4 docs PRs** (canopy#790, #791, #793, #796). The CI/CD set
  (`docs/ci_cd/CICD_MANUAL.md`, `CICD_QUICK_START.md`, `CICD_REFERENCE.md`, `CICD_ENVIRONMENT_SETUP.md`) gains the
  Gitleaks ruleset contract (`.gitleaks.toml`'s `[extend] useDefault = true`, the AND-scoped `generic-api-key`
  allowlist for conda build strings, the pinned 8.24.3 binary and its `GITLEAKS_PARITY_REQUIRED` self-test), and its
  weekly-scan runbook now matches `security-scan.yml` (`pip install -e ".[dev]"`, then
  `pip-audit --desc on --skip-editable`, where it said `pip install -e .` and `pip-audit --strict --desc on`) and
  says that workflow runs no Gitleaks (#790). It documents the unit lane's Codecov upload as `ci.yml` runs it
  (`token: ${{ secrets.CODECOV_TOKEN }}`, `files: reports/coverage.xml`) in place of a stale `codecov-action@v4`
  example, and that a test module must sit in a directory some lane names, never at the top of `src/tests/` (#791).
  It documents the verify-only AGENTS.md date check (`agents-md-touch-up.yml`) and its header states, and the
  `Documentation Links` job's header and version lints (#793). The product docs (`docs/DEVELOPER_CHEATSHEET.md`,
  `QUICK_START.md`, `REFERENCE.md`, `USER_MANUAL.md`, `api/API_REFERENCE.md`) describe the mnist declared-param
  filter canopy#778 landed: the restart modal renders Samples alone, and on the cascor service path a posted Noise
  is withheld and named at INFO (#796). Claims were re-checked against `main`, and four the drafts got wrong are
  corrected. Removing `[extend]` alone makes gitleaks 8.24.3 refuse this config, so the Gitleaks step fails; only a
  file with no `[[rules]]` either, as before 2026-10-25, passes with zero rules. The Dependabot secret store has
  held `CODECOV_TOKEN` since 2026-11-04, so a Dependabot pull request's upload carries it. `POST /api/stage_dataset`
  echoes the staged config in `data`. A test module directly in `src/tests/` fails the unit lane
  (`TestNoTestModuleSitsAtTheTopOfTheTestTree`) rather than silently never running. The first two false claims
  are also corrected in comments on `main` (`.gitleaks.toml`, `.github/workflows/ci.yml`,
  `src/tests/regression/test_gitleaks_config.py`), with no logic change. The drafts' version stamps are dropped and
  each file is bumped once (minor where it gains a section, as `docs/DOCUMENTATION_OVERVIEW.md` prescribes); the
  eight lines over markdownlint's 512-character limit are wrapped (#790 one, #793 four, #796 three); #790's loss of `CICD_QUICK_START.md`'s header hard breaks is
  not carried; and #793's two code spans of `##` plus a trailing space, which markdownlint's `--fix` rewrites to
  bare `##`, are reworded. Docs and comments only.
- **Documentation harvested from the Cursor flood-4 round-2 docs PRs** (canopy#798, #799, which duplicate each
  other). `docs/ci_cd/CICD_MANUAL.md`'s Dependabot lockfile runbook now documents, once, the commit step's refusal
  of an empty payload (#775): `lockfile-update.yml` encodes `requirements.lock` on a line of its own under
  `set -euo pipefail` and exits 1 on an empty result before `jq` or `gh` runs, because `base64 -w0` of an empty
  file prints nothing and exits 0. A table gives the log lines the step ends on, what happened, and whether
  anything was committed; `CICD_REFERENCE.md` and `CICD_QUICK_START.md` point to it. Re-checked against `main`, one
  claim both drafts made is corrected: a GraphQL error does not reach the step's own
  `createCommitOnBranch failed — lockfile NOT committed:` message, because `gh api graphql` exits 1 on a response
  that carries `errors` and `set -e` ends the step there, so the log shows `gh: <message>`.
  `CICD_ENVIRONMENT_SETUP.md`'s security install snippet said `pip install -e .`; it now shows each workflow's own
  install, `pip install -e ".[juniper-data,juniper-cascor,observability]"` in `ci.yml`'s `Security Scans` and
  `pip install -e ".[dev]"` in `security-scan.yml` (#799). The drafts' Bandit SARIF material is not carried: the
  upload's pull-request failure is already documented in `CICD_MANUAL.md` (the CodeQL runbook's constraints and the
  `security` troubleshooting bullet). The drafts' version stamps are dropped and each file is bumped once. Docs only.
- **juniper-canopy#737: a CI job now notices juniper-data parameter drift against the committed generator-schema
  snapshot.** W1.2's declared-param filter (canopy#733) reads `DECLARED_PARAM_DEFAULTS`, which the unit tests pin to
  `src/tests/fixtures/juniper_data_sequence_generator_schemas.json`, but nothing compared that capture with
  juniper-data: a parameter added upstream would be withheld from every request, one removed still sent and dropped
  in silence, and a changed default sent as an edit. `util/check_juniper_data_generator_schemas.py` compares every
  generator in every `src/tests/fixtures/juniper_data_*generator_schemas.json` (the snapshots decide which, so a sibling capture is covered from the commit that adds it, as flat `equities` and `mnist` are in this release) with `GENERATOR_REGISTRY[name]`:
  `params_class.model_json_schema()` and `version`, with JSON equality (`1` equals `1.0`; `false` is not `0`). Any
  difference exits 1, naming the generator, the field and key, both values, and the exact re-capture command; a
  check that cannot run (no or malformed snapshot, juniper-data not importable, not the expected version, or a
  `juniper_data` imported from anywhere but the distribution it reports) exits 2. The new
  `.github/workflows/juniper-data-schema-drift.yml` installs the released `juniper-data[api]` (a bare install cannot
  import the registry: `pydantic_settings`) and runs it daily at 07:17 UTC, on `workflow_dispatch` (optionally for
  a version), on `repository_dispatch` `juniper-data-published` (the event juniper-recurrence's bench lane receives; juniper-data's notify-consumers matrix has listed canopy since juniper-data#501, 2026-10-30, so juniper-data's next release sends it here), and on a pull request touching the
  workflow, the script or a snapshot. Against juniper-data 0.17.1 on 2026-10-26: no drift in any of the six
  generators. Tests: `src/tests/unit/test_check_juniper_data_generator_schemas.py` (each kind of drift is named and
  exits 1; equality passes; both import modes run in subprocesses; the workflow's contract with juniper-data's sender
  is pinned). Mutation check: `util/ad-hoc/2026-10-26_737_drift_check_mutation_check.py`, 23 of 23 arms caught. The
  opt-in `test_the_live_source_still_matches_the_capture` docstring now points at the new check.

### Fixed

- **A 429 never says `Retry-After: 0`, and the wait it names is rounded up (APD-ECO-016; Overtoad ruling 2026-11-09).**
  `RateLimiter.check` in `src/security.py` reported `int(window - elapsed)`, which truncates. A rejection in a
  window's last second therefore carried `Retry-After: 0` and `X-RateLimit-Reset: 0`, telling a client to retry at
  once into a limiter that rejects again, and every other fractional remainder was a second short (9.4s left said 9).
  The allowed path, which feeds `X-RateLimit-Reset`, truncated the same way. Both now report
  `max(1, ceil(window - elapsed))`, as juniper-service-core's copy does (`APD-SVCCORE-004`). canopy keeps its own
  copy of the limiter and does not import juniper-service-core's, so that fix never reached it; canopy has no
  failed-auth throttle. `src/tests/unit/test_retry_after_rounds_up.py` (30 tests, frozen clock) pins the rounding on
  both paths, and in the headers and the message a caller receives. `docs/api/API_REFERENCE.md`'s Rate Limiting
  section now shows what the limiter sends: it showed `X-RateLimit-Reset` as a timestamp and a 429 body the code
  never returned. A robustness fix, not a leak.
- **juniper-canopy#778: the restart modal rendered Noise for `mnist`, and juniper-data dropped the value.** cascor
  forwarded the re-staged `noise`, and juniper-data's `MnistParams` (generator `3.0.0`, 13 parameters) declares
  none, so it vanished without a word: the F-C3 class juniper-canopy#736 closed for flat `equities`.
  `DECLARED_PARAM_DEFAULTS` gains `mnist`, captured from the published juniper-data 0.17.1 wheel (sha256
  `cce2c167…`, equal to PyPI's; 101 package files byte-identical to release tag `v0.17.1` = `381e660b`) by
  `util/ad-hoc/2026-10-26_capture_published_generator_schemas.py`, whose default now captures both generators, with
  its own provenance (`MNIST_DECLARED_PARAMS_SOURCE`). `src/tests/fixtures/juniper_data_tabular_generator_schemas.json`
  holds both: the re-captured `equities` entry is identical, and only `captured` moved, from 2026-10-26 to
  2026-11-03. The capture needed no `[mnist]` extra, because juniper-data imports `datasets` lazily, so an
  `[api]`-only install serves `mnist`'s schema while it reports `available: false`. `_UNAVAILABLE_REASONS["mnist"]`
  concerns generating `mnist`, which does need the extra, so it is unchanged, and its comment now says which.
  - The restart modal renders Samples alone for `mnist` (`staged_typed_fields`).
  - The cascor path shapes `mnist`'s staging body as it shapes `equities`', on Apply, the live swap and the
    re-stage alike: the registry seed's `flatten: True`, plus what the operator edited. A staged `noise` is withheld
    and named. `n_samples` rides in `params` under its own name, which cascor's `_translate_staged_config` passes
    through to juniper-data.
  - The schema drift job now compares 8 generators in 2 fixtures; against 0.17.1, none drifts.
  - Tests: `test_cascor_staging_declared_params.py` (`TestMnistGetsTheDeclaredParamFilter`) and
    `test_recurrence_request.py`. The `mnist` expectations that pinned its Noise field changed in
    `test_restart_modal_restages_what_it_shows.py` and `test_empty_axis_commit_and_restage_zeros.py`.
- **Unit-lane tests no longer talk to whatever listens on the host's Juniper service ports** (the Overtoad's ruling 17 of 2026-11-09 in juniper-ml's Cursor flood-4 arc; as of this release its record, `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`, lists rulings 1 to 14 in §8 and not this one). A census of the CI unit lane at
  `b4b01904` (CI's selector, 8290 tests) found 20 unmocked connects to `127.0.0.1:8050` from 16 tests and 2 to
  `127.0.0.1:8200` from 2 (a race: any of the four relay tests in
  `src/tests/unit/backend/test_cascor_service_adapter_boundary.py` can dial, so the count varies by run). Ten of
  the :8050 tests mocked only `requests.post` around `_apply_parameters_handler`, whose read-back
  `GET /api/state` went out unmocked; six called `_gate_dataset_options_handler` without `generators`, whose fetch
  of `/api/dataset/generators` went out unmocked; the :8200 connects came from the metrics relay's tests, whose
  control-stream supervisor dialed cascor. CI's runner refuses those connects and the handlers swallow the
  refusal, so the tests passed there; on a machine running canopy they reached it, and the generator list a live
  canopy answers with decides what the dataset gate greys out. Each test now mocks that transport as its
  neighbours do. `src/tests/conftest.py` gains a unit-lane network guard: while a test from the unit lane's
  directories (or a `unit`-marked test not marked `integration`) runs, a connect the pytest process makes through
  Python's `socket` module to canopy 8050-8059, juniper-cascor 8200-8202 or juniper-recurrence 8210-8211 is
  refused as an empty host refuses it, and the test then fails, even when the code swallowed the refusal or the
  test is an expected failure (xfail). A refusal fails whichever test is running when it happens, so one made off
  the main thread is reported with its thread's name. A test's own server on port 0 keeps working, and
  `@pytest.mark.allow_service_ports` opts out a test that connects to a service port it listens on itself.
  juniper-data's 8100 is not guarded: 124 tests reach it through the app's own startup probe and
  `/v1/health/ready`, so guarding it is deferred. Tests: `src/tests/unit/test_unit_lane_network_guard.py`;
  documented in `docs/testing/TESTING_REFERENCE.md`.
- **The Security Scans job's Bandit SARIF report is written and uploaded again.** `.github/workflows/ci.yml`
  installed bare `bandit`, whose CLI has no `sarif` formatter without the `bandit[sarif]` extra. So `bandit -f sarif`
  failed with `invalid choice: 'sarif'`, no report was written, the step warned "Bandit found security issues" for an
  argument error, and the upload's `continue-on-error: true` kept the job green over `Path does not exist:
  reports/security/bandit.sarif` (main run 40942351409, job 123689681187). The job now installs `"bandit[sarif]"`,
  as `security-scan.yml` and every sibling repository's `ci.yml` already do. Run on `src/` with `.bandit.yml`,
  Bandit 1.9.4 exits 0 with 0 results, so the upload adds no alert. Found by the Cursor flood-3 evaluation: juniper-ml
  `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` §4.
- **The memory-budget gate's own 40 tests now run in the required unit legs, and the Codecov upload sends the
  repository's token.** #516 (2026-08-25) ported `util/memory_budget_check.py` with its suite at
  `src/tests/test_memory_budget_check.py`, the top of the test tree, which no CI lane reaches: the unit job selects
  by path (`src/tests/unit/`, `regression/`, `contract/`, `performance/`), the integration and ui jobs name one
  directory each, and the scheduled lane walks `testpaths` under `-m "slow or integration"`, which deselects an
  unmarked module. So the negative controls behind the `Memory Budget` check had never run in CI. The suite moves to
  `src/tests/unit/test_memory_budget_check.py`, its repo root goes from `parents[2]` to `parents[3]`, and it gains
  `pytestmark = pytest.mark.unit` for `pytest -m unit` runs (the unit job's selector is negative, so the path is
  what CI keys on). No test body changed, and the checker's docstring now names the real path.
  `src/tests/regression/test_ci_lane_wiring.py` gains `TestNoTestModuleSitsAtTheTopOfTheTestTree`, because its
  directory guard walks subdirectories and could not see a module at this level; restoring the old layout fails it.
  At this change the unit lane selected 8,224 of 8,228 collected tests, up from 8,182 of 8,186: the 40 of this suite plus the
  guard's 2. The twin of juniper-cascor#734. Separately, the Codecov step in `.github/workflows/ci.yml` now passes
  `token: ${{ secrets.CODECOV_TOKEN }}`, as juniper-data's does, after the Overtoad added the secret on 2026-10-29.
  Until then its uploads were refused ("Token required - not valid tokenless upload") inside a step that stays
  green under `fail_ci_if_error: false`: all 24 in the six `ci.yml` runs from 2026-10-28 20:56Z to 2026-10-29
  19:41Z. A Dependabot PR reads the Dependabot secret store, which did not hold the token then, so its upload stayed tokenless until the Overtoad added the token there on 2026-11-04. Found by the Cursor flood-3 evaluation: juniper-ml
  `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` §4.
- **The lockfile regen could have committed an empty `requirements.lock` without failing.** The commit step built
  its payload with `--arg contents "$(base64 -w0 requirements.lock)"`. A failure inside a command substitution used
  as an argument does not trip `set -e`, so a failing `base64` would have handed `jq` an empty string and the step
  would have made a signed commit that empties the lockfile. Latent: GNU `base64` does not fail on
  `ubuntu-latest`. The encoding is now its own assignment, which `set -e` does catch, and an empty result fails the
  step before anything is committed. `.github/workflows/lockfile-update.yml` banner 0.1.2 (0.1.3 after the next entry's change). Found by the Cursor
  flood-3 evaluation: juniper-ml `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` §4.
- **The lockfile regen's own failure message never printed: a GraphQL error ended the step at the `gh` line.**
  `gh api graphql` exits 1, not 0, on a response that carries GraphQL `errors` (it writes the body to stdout and
  `gh: <message>` to stderr; cli/cli `pkg/cmd/api/api.go`, `processResponse`), and on an HTTP failure. Called bare
  under `set -euo pipefail`, that exit ended `lockfile-update.yml`'s commit step before its `.errors` check, so
  `createCommitOnBranch failed — lockfile NOT committed:` was unreachable and the log showed only gh's line. The
  step now captures gh's exit status and stderr, prints gh's message with the `CROSS_REPO_DISPATCH_TOKEN` value
  masked, and fails with its own diagnostic: the GraphQL `errors` and what to do, or, when the response carries no
  `errors`, `gh api graphql failed` and the branch to check, because that log cannot show whether the commit
  landed. A successful run prints what it printed before. The stub `gh` in
  `src/tests/regression/test_lockfile_regen_empty_payload.py` now fails as the real CLI does, and eight new cases
  pin both diagnostics, the mask and gh's exit status; `docs/ci_cd/CICD_MANUAL.md`, `CICD_REFERENCE.md` and `CICD_QUICK_START.md`
  describe the new log lines (they documented the old ending, juniper-canopy#808).
  `.github/workflows/lockfile-update.yml` banner 0.1.3. Cursor flood-4 evaluation, Overtoad ruling 17 (2026-11-09).
- **`claude.yml`'s header said `ANTHROPIC_API_KEY` is set at the organization level.** Juniper repos are
  user-owned, so no organization secret can reach them; the key is a repository secret here, added 2026-10-10.
  The header now says so, and the three CI docs that repeated the claim (`docs/ci_cd/CICD_REFERENCE.md`,
  `docs/ci_cd/CICD_ENVIRONMENT_SETUP.md` and `docs/ci_cd/CICD_MANUAL.md`) are corrected with it. Comments and docs
  only: no trigger, step, pin or job name changed. Found by the Cursor flood-3 evaluation: juniper-ml `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` §4.
- **`docs/DOCUMENTATION_OVERVIEW.md`'s two template examples carried the document's own live stamp.** The example
  document header (`:510-511`) and the metadata example (`:965-966`) both read `1.0.1` / October 8, 2026, the
  header's own values, so a stamp bump rewrote the examples along with the header. juniper-cascor#709 made exactly
  that edit to cascor's copy (a row in that flood-3 record); the juniper-cascor flood-3 backlog PR found this one. The
  examples now show placeholders, and the header moves to 1.0.2, October 26, 2026.
- **F-CANOPY-069: under every dash 3.x release the dashboard was inert in the browser.** Two callback pairs each
  claimed one `allow_duplicate` Output from one Input: `accept_live_switch` and `open_progress_alert_on_accept` on
  `live-switch-accept-button.n_clicks`, and `execute_restart` and `open_restart_progress` on
  `restart-confirm-button.n_clicks`. Dash hashes the inputs into an `allow_duplicate` output id
  (`create_callback_id`), so each pair's ids collided. dash 3's renderer validates the served dependency list
  unconditionally and, on that `Duplicate callback outputs` error, drops the whole callback graph: the page
  rendered and nothing on it worked (measured on 3.0.4, 3.2.0, 3.3.0 and 3.4.0; `conf/conda_environment.yaml`
  pinned 3.3.0). dash 4 validates only with dev tools on, ran both members of each pair, and let the order of
  their responses decide whether the spinner flashed or stuck. The openers existed to show the progress spinner
  before the slow POST returned, which is what a callback's `running=` spec is for: `accept_live_switch` and
  `execute_restart` now carry their progress alerts (and the live-swap in-flight store) as `running=`, so the
  renderer opens them the moment the request leaves and closes them when the response lands, with no second
  callback and no round trip. `open_progress_alert_on_accept`, `open_restart_progress` and
  `_open_progress_alert_on_accept_handler` are gone. Pinned by
  `src/tests/unit/frontend/test_f069_duplicate_callback_outputs.py`: no output id is claimed by two callbacks
  (ids computed as `create_callback_id` does, over the served dependency list; the scan is shown to catch the
  shape that bit canopy), each progress alert has one writer, each of the two Inputs runs one callback, and the
  two `running` specs are what the renderer expects. Verified alive in the browser on legs of this tree under
  dash 3.3.0 and 4.4.1 (juniper-ml `util/ad-hoc/2026-10-20_canopy_dash_duplicate_outputs_probe.py`, Phase 14's
  per-dash probe; one POST per click, the spinner opening on the request and closing on the response,
  `util/ad-hoc/2026-10-20_f069_pair_members_probe.py`). Ledger: juniper-ml
  `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, Phase 14 (filed) and Phase 15 (closed).
- **juniper-canopy#736: the cascor staging body for flat `equities` carried every rendered field, and the restart
  modal added parameters `equities` does not have.** W1.2 (canopy#733) gave the recurrence request a declared-param
  filter and R7's "send only what the operator edited"; the cascor path had neither. Sidebar Apply and the live swap
  posted every rendered value, so untouched fields went to cascor at canopy's displayed defaults, and the restart
  modal re-staged `n_samples` / `noise`, which juniper-data's flat `EquitiesParams` does not declare and silently
  ignores (F-C3). `ServiceBackend.stage_dataset` and `swap_dataset_live` now forward
  `recurrence_request.shape_stage_payload`'s body, built with the recurrence request's own `shape_staged_ref`: for a
  generator `DECLARED_PARAM_DEFAULTS` covers, the registry seed plus every field the operator edited (an edit still
  wins over the seed), with an undeclared parameter withheld; every other generator's body goes as staged. Each
  shaped body is logged at INFO (forwarded params, edited, untouched, not forwarded), and a parameter withheld as
  undeclared is a WARNING naming the capture. `DECLARED_PARAM_DEFAULTS` gains `equities` (17 parameters, generator
  `5.0.0`), captured from the published juniper-data 0.17.1 wheel (sha256 `cce2c167…`, byte-identical to release tag
  `v0.17.1` = `381e660b`) by `util/ad-hoc/2026-10-26_capture_published_generator_schemas.py` into
  `src/tests/fixtures/juniper_data_tabular_generator_schemas.json`, with per-entry provenance
  (`DECLARED_PARAMS_SOURCES`). No full cascor preview: the logs, and the restart modal's plan below, cover it. Tests:
  `test_cascor_staging_declared_params.py` (dashboard body to the real route, `ServiceBackend` and adapter, read off
  the wire), `test_recurrence_request.py` (`TestShapeStagePayload`, the capture pins, `TestNoCascorRenamedGeneratorIsDeclared`).
- **juniper-canopy#735: the restart modal showed the spiral-era dataset fields for every type and re-staged them all.**
  Samples, Noise, Spiral rotations and Spirals were rendered and re-staged for sequence generators and `equities`
  alike, so the modal "planned" values that were then dropped. Each field now renders only when the selected type's
  generator has a parameter for it (`recurrence_request.staged_typed_fields`: all four for spiral, none for
  `equities` or a sequence generator, Samples and Noise otherwise), driven by the type alone
  (`show_restart_dataset_fields`), and Confirm re-stages exactly the rendered fields through one builder
  (`_restart_restage_payload`) that the Restart plan also reads. This keeps the Overtoad's 2026-09-22 ruling that
  "Confirm re-stages exactly what the modal displays" (point 4 of §5.6.1 of juniper-ml's
  `JUNIPER_2026-06-17_JUNIPER-CANOPY_MODEL-DATASET-SELECTION-DESIGN.md`): the plan now names the registry defaults and
  the model a re-stage carries, every value it does not send, and whether anything is re-staged at all. The
  `enabled[0]` swap and the `⊥` refusal are unchanged, but the swap now counts as a change: its baseline used to take
  the swapped value, so an untouched Confirm after a swap re-staged nothing and restarted on the dataset the modal had
  replaced. Tests: `test_restart_modal_restages_what_it_shows.py` (Confirm's keys equal the rendered fields plus the
  seed and mirror, for every type and after the swap); `test_recurrence_staging.py`'s assertion that the modal sends
  the spiral fields to `equities_seq` is flipped.
- **The recurrence preview did not quote the declarations it filtered against** (juniper-canopy#737, its smaller
  item). `dataset_schema.py` said the source was "quoted in the preview" while the notes never showed it; they now
  name the capture for the request's generator, and `FitRequest.describe` reports none when nothing was filtered.
- **F-CANOPY-028: a pin made just before a table rebuild was discarded.** `update_pinned_params_store` fires on every
  change to any pin checkbox's `value`, and the Parameters tables are rebuilt on every params-store or pin-store
  change, each rebuild re-creating all 22 checkboxes, so a rebuild whose request was in flight when a click's write
  landed rendered the pin set it was computed from, fired the writer with every checkbox "changed" and the new pin
  unchecked, and the writer (canopy#533's merge of the rendered set into the stored one) persisted that set over
  the click (juniper-ml ledger Phase 14, item 30: one drive in eight; the mount render used to do the same with an
  empty store, the shape #533 closed). The writer now persists a user's toggle only: exactly one pin input
  triggered (`CallbackContextAdapter.get_triggered_prop_ids`), that key added to or removed from the stored list,
  the rest untouched; a rebuild (every input triggered at once) and a toggle the store already reflects write
  nothing. `_merge_pinned_params` is replaced by `_apply_pin_toggle`. Tests: `test_p2_wave_batch_b.py`
  (`TestF028PinnedParamsPreserved`: a rebuilt table from a stale set after a toggle leaves the store as the toggle
  left it, the mount render writes nothing, the toggle cases) and `test_dashboard_manager_gate_coverage_inner1.py`.
  Live: the pin-after-reload drive (`2026-10-20_item30_fixwave_redrive.py --step f028`) at fixed delays after the
  reload, on a leg of this tree, is recorded in the ledger's Phase 15.
- **`docs/USER_MANUAL.md`, Patch Weights:** the values sentence said comma-, semicolon- or newline-separated
  floats; for `output_weights` semicolons and newlines separate rows, so F-CANOPY-012's cases B and C (a flat list
  broken up by either) are refused on any network with more than one output. The sentence now states the row idiom
  and the flat-list reshape.
- **Patch Weights refused space-separated values for the three 1-D targets.** The manual says values are "floats
  separated by commas or spaces", and `_parse_float_list`'s docstring said "comma/whitespace-separated", but the
  parser folded newlines and semicolons into commas and split on commas alone, so `0.1 0.2` for `output_bias`,
  `hidden_unit_weights` or `hidden_unit_bias` (and for Append Hidden Unit's weights, the parser's other caller)
  reached `float()` as one token and was refused; `output_weights` rows already split on whitespace. Whitespace of
  any kind now separates values too. Every input accepted before parses to the same list, since `float()` refuses a
  token with whitespace inside it. Tests: `test_network_editor_panel.py` (`TestParseFloatList`) and
  `test_patch_values_manual_separators.py`, which reads the manual's sentence and drives every target with commas
  and with spaces. Ledger: juniper-ml `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, Phase 15
  item 34.
- **F-CANOPY-065: an Apply's toast never reported a key the WS leg declined.** `apply_params` sends hot keys over
  `/ws/control` and cold keys over REST. juniper-cascor-client resolves `set_params` with the whole
  `command_response` frame, and cascor nests `update_params`' return (the C2a `applied` / `skipped` partition) at
  `data.result`, but `_extract_cascor_partition` scans a result's top level and `data` only, and `apply_params` read
  it from one dict merged from both legs, whose `data` the REST envelope's replaced. So the WS keys never reached
  `applied`, and a key cascor declined there (`epochs_max`, `not-updatable`) never reached the toast: the selection
  arc's A-N2 Apply answered `{"applied": ["cn_training_iterations"]}` for five keys, and the toast read "Parameters
  applied", where 0.6.0 promised `epochs_max (not-updatable)`. `_apply_params_hot` now unwraps the ack
  (`_unwrap_control_ack`), and `apply_params` reads each leg's partition from that leg's own result and unions them.
  Corrected with it: the extractor's "the WS ack carries it flat" docstring, the N5 test's flat ack fake, and
  `use_websocket_set_params`' "default off" comment (it is on). Tests: `test_n5_apply_params_ux.py`
  (`TestF065BothLegsPartitionsReachTheToast`: A-N2's mixed Apply through the real `apply_params`, a WS-only Apply,
  the toast, the unwrap). Live on turing against a throwaway cascor 0.12.0 leg, the same five keys: `main` answers
  `["cn_training_iterations"]`; this tree answers the four applied keys and `nn_max_total_epochs (not-updatable)`.
  Ledger: juniper-ml `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`, Phase 10 (filed) and item
  20.

### Changed

- **`agents-md-touch-up.yml` pins `actions/checkout` to a commit SHA (Overtoad ruling 2026-11-03).** It checked out with
  the `v7.0.1` tag, the only tag-only `actions/checkout` in `.github/workflows/`. It now uses
  `3d3c42e5aac5ba805825da76410c181273ba90b1  # v7.0.1`, the commit that tag resolves to and the pin every other
  workflow here uses, so behaviour is unchanged. A census of the nine Juniper repositories' `main` on 2026-11-01 found
  249 `actions/checkout` uses, 242 pinned to that SHA; the seven tag-only ones were this workflow's copies, one per
  repository. juniper-data#503 pinned juniper-data's, and this change is one of the seven that pin the rest.
- **A failed Bandit SARIF upload now fails `Security Scans` on a pull request (Overtoad ruling 2026-10-30).**
  `.github/workflows/ci.yml`'s upload step is `continue-on-error: ${{ github.event_name != 'pull_request' }}`, as in
  juniper-cascor#735. No ruleset here requires the `Bandit` check that code scanning creates from the upload, so a
  failed upload was silent: juniper-canopy#780 found the step uploading nothing while `Security Scans` stayed green.
  `Security Scans` is required, so a PR now shows the failure, with the cause in the step log. Pushes and dispatches
  still tolerate it. `docs/ci_cd/CICD_MANUAL.md` says so. Found in the 2026-10-08 flood-3 disposition (juniper-ml
  `notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` §8).
- **Temporary files go in the repo's gitignored `tmp/`, never `/tmp` (Overtoad directive, 2026-10-26), and the Overtoad's
  rulings on it are applied.** `/tmp/` is ignored, and `AGENTS.md` § Temporary files carries the rule and the
  rulings, retention included. `juniper-check-doc-links` passes `--exclude tmp` in the pre-commit hook and in CI,
  and `.dockerignore` lists `tmp/`; nothing keeps pytest out of it, and counting scripts are to choose their scope
  as to `tmp/` deliberately (the Overtoad's revised ruling). To stay under the memory budget, `AGENTS.md`'s Test
  Environment Variables table moved verbatim to `docs/AGENTS_REFERENCE.md`.
- **The dash floor is `dash>=4.0.0`** (`pyproject.toml`; `conf/requirements_ci.txt`, which `requirements.txt` and
  `requirements_ci.txt` link to), and `conf/conda_environment.yaml` pins `dash=4.4.1` with dash 4's two new run
  dependencies, `comm` and `janus`, at the lock's versions. Everything canopy tested at the fix ran dash 4.x (the
  lock's 4.4.1, which has since moved to 4.5.0, CI's 4.4.1 pip lane and 4.1.0 conda lane, every live drive in the E2E
  ledger), and a floor that nothing tests is
  how F-CANOPY-069 stayed invisible: the two conda files (`conf/conda_environment.yaml` and `conf/conda_environment_cpu.yaml`, both `dash=3.3.0`) were the environments on 3.x, and nobody drove them. This release moves only `conf/conda_environment.yaml`: `conf/conda_environment_cpu.yaml` still pins `dash=3.3.0`, below the new floor. The fix itself does not depend on the dash version; a 3.3.0 leg of this tree is alive too.
- **The app opts out of FastAPI's native telemetry (Overtoad ruling 2026-11-09).** FastAPI 0.142 added OpenTelemetry
  instrumentation of its own, with tracing, metrics, logs and operation spans on by default, and the lock pins FastAPI
  0.162.5. `src/main.py` now builds `app` with `telemetry=`, those four switches and `auto_configure` set to `False`,
  as juniper-data does (juniper-data#454), so FastAPI's instrumentation cannot overlap canopy's configured
  observability (Sentry, Prometheus, its own logging). This is hardening, not a fix for a live leak: the
  instrumentation stays idle until an OpenTelemetry provider is configured, and the lock holds `opentelemetry-api`
  1.45.2 and no OpenTelemetry SDK. FastAPI can also set up export by itself, when `FASTAPI_OTEL_AUTO_CONFIGURE` is `true`
  and the environment names an OTLP endpoint; without the SDK that attempt only logs a startup warning, and the
  explicit `auto_configure: False` now rules it out. On FastAPI < 0.142, which `pyproject.toml` still admits, the
  keyword lands in `app.extra` and does nothing; the new test in `src/tests/unit/test_main_import_and_lifespan.py`
  pins all five switches off and skips there.
- **The dependency lock moved** (`requirements.lock`, which the image installs), through the lock regenerations of
  the Dependabot updates merged since 0.9.0 (#755, #770, #771, #772, #810, #811, #813), F-CANOPY-069's fix (#760)
  and #806's two security pins (Security, below). The notable runtime pins: `fastapi` 0.143.3 -> 0.162.5 with
  `starlette` 1.8.0 -> 1.10.0, `dash` 4.4.1 -> 4.5.0, `pydantic` 2.14.1 -> 2.14.3 (with `pydantic-core` 2.50.4 and
  `pydantic-settings` 2.16.2), `sentry-sdk` 2.72.0 -> 2.74.0, `websockets` 17.2 -> 17.4, `python-multipart`
  0.0.32 -> 0.0.33, `importlib-metadata` 9.0.1 -> 10.2.0, `anyio` 4.15.1 -> 4.16.0 and `certifi` 2026.7.22 ->
  2026.10.23, plus seven smaller moves, and `lazy-importer` 0.1.0 joins it. Apart from the dash floor (above) and the
  two security floors (Security, below), the wheel's declared requirements are unchanged.

### Security

- **The image picks up juniper-observability 0.4.2, the security patch, and juniper-service-core 0.7.2, a plain patch released with it.** #806 moved `requirements.lock` from 0.4.1 and 0.7.1 to them, and nothing else; #810 later added `lazy-importer` (the release's other lock moves are under Changed), so the lock this release installs holds 61 pins, which CI's constraint-mode freshness resolution reproduces. The image installs that lock (`Dockerfile:40`).
  - **observability 0.4.2** fixes `configure_sentry`, which `src/main.py:312` calls through `src/observability.py`'s
    wrapper. Under 0.4.1, once a Sentry DSN was set, a request's `Sec-WebSocket-Protocol`, `X-CSRF-Token` and
    `X-XSRF-Token` headers reached Sentry in every error event and transaction. `Sec-WebSocket-Protocol` is the header
    that carries canopy's own WebSocket key (`bearer, <key>`) when the opt-in `ws_auth_enabled` is on. 0.4.2 runs its
    scrubbing hook on transactions too (`before_send_transaction`), redacts the parsed cookies, and filters those three
    headers and `Proxy-Authorization`. The wrapper leaves `send_pii` off, so the `X-API-Key` and cookie leaks that 0.4.2
    also closes were not reachable here.
  - **Still open**: 0.4.2's notes leave query strings, Sentry Logs, request bodies, breadcrumbs and exception values for juniper-observability 0.4.3, so this lock does not close them. The query strings include canopy's `?api_key=` WebSocket parameter, which reaches Sentry under the default `send_pii=False`.
  - **service-core 0.7.2** rounds `FailedAuthThrottle`'s `Retry-After` up instead of truncating it. canopy imports only
    `enforce_auth_posture`, `AuthPostureError` and `enforce_dependency_floors` from service-core, so the change does not
    reach it, and the pin is consistency with the sibling services.
  - Regenerated with `--upgrade-package` for the two packages only, compiled onto a copy of the lock so every other pin
    is held (juniper-ml `util/ad-hoc/2026-10-10_targeted_lock_refresh.py`). The wheel's floors follow in this release:
    `juniper-observability>=0.4.2,<0.5.0` and `juniper-service-core>=0.7.2,<0.8.0`, so a pip install over an older
    environment upgrades both. The boot-time `enforce_dependency_floors` reads the **installed** metadata, so an existing
    editable install keeps booting until it is reinstalled; the reinstall upgrades it. The lock moved in #806; the floors
    ride in the release proposal, because a `pyproject.toml` change on any branch but `release/` triggers
    `lockfile-update.yml`'s full `--upgrade` regen.
- **CI's Gitleaks step loaded zero rules and could not fail; it now loads gitleaks' built-in ruleset.**
  `.gitleaks.toml` held an `[allowlist]` and no `[extend]` table, and a gitleaks v8 config without
  `[extend] useDefault = true` loads only its own `[[rules]]`, of which it had none. Every push, pull-request and
  dispatched scan therefore passed vacuously: a fabricated GitHub token went through the config while gitleaks'
  built-in config flags it (the defect juniper-ml#2203 fixed there). The table is added. The `paths` allowlist keeps
  `conf/.*\.lock` and `notes/mcp/.*`; its conda environment YAML entry is replaced (below).
  - **History measured.** A `workflow_dispatch` run scans every commit reachable from every remote branch and tag.
    Measured with gitleaks 8.24.3 over exactly that scope (84 head/tag SHAs, 1575 commits): 18 findings, all false
    positives -- 4 conda `<package>=<version>=<build>` hashes in `conf/requirements-conda.txt` (a path the allowlist
    does not cover), 4 prose matches in `docs/IMPLEMENTATION_PLAN.md`, 9 synthetic probe keys (the padded-key and
    #683 leak probes, and the padded key quoted in a test docstring and in this file) and 1 model-registry key in a
    test fixture. Each is a commit-scoped entry in the new `.gitleaksignore`, under a comment naming its class; the
    rescan finds none. With the `paths` allowlist removed the same scan adds 30 findings, all in its own paths: 29
    conda build hashes and one `YOUR_API_KEY`-shaped placeholder in `notes/mcp/EXA_API_REFERENCE.md`.
  - **Conda build strings get a narrow allowlist, because they recur, and it REPLACES the broad conda path
    exemption.**
    - **Why.** Every conda-env refresh rewrites the `<package>=<version>=<build>` lines under a new commit, and no commit-scoped entry can name that commit in advance. The old global `conf/conda_environment.*\.ya?ml` path entry kept such a refresh from failing only by skipping EVERY rule in those files; without it, the next refresh of a conda environment file would fail the PR scan and then the push scan of `main`. (`conf/requirements-conda.txt`, which the new allowlist also names, has not been in the tree since before 0.9.0; its four findings are in history only.)
    - **What.** `.gitleaks.toml` adds an AND-scoped allowlist to `generic-api-key` alone. A finding is dropped only
      when its file is `conf/conda_environment*.y(a)ml` or `conf/requirements-conda.txt` AND its whole secret is
      `<version>=<build>` with a conda build string (`h<7 hex>_<n>`, `pyh<7 hex>_<n>` or `py<NNN>h<7 hex>_<n>`).
      The conda YAML entry leaves the global `paths`.
    - **Why a rule allowlist.** gitleaks 8.24.3 has no top-level `[[allowlists]]` or `targetRules`, which its config
      loader would drop silently, and its global `[allowlist]` is OR-only. So the allowlist is merged into the
      default `generic-api-key` rule, which keeps its regex, entropy and own allowlists.
    - **Measured over the same scope** (85 SHAs, 1576 commits with this PR's branch): the narrowing exposes no
      finding. Without the ignore file the scan reports 14 findings, exactly the non-conda ones; the 29 conda-YAML
      and 4 `requirements-conda.txt` findings are all covered by the allowlist. Their commit-scoped entries stay.
  - **The engine is pinned**: `GITLEAKS_VERSION: "8.24.3"` on the gitleaks-action step, the version its v3.0.0
    installs by default, so a bump of the action SHA cannot change it silently.
  - Pins: `src/tests/regression/test_gitleaks_config.py` (new, 12 tests):
    - the config extends the defaults;
    - the conda allowlist is AND-scoped, on `generic-api-key` only, over exactly those two path patterns;
    - no global path exemption covers a conda file, and only `conf/.*\.lock` and `notes/mcp/.*` remain;
    - the real engine fires the built-in `github-pat` rule on a runtime-built fabricated token through the
      auto-discovered and the explicit config (with a no-config control);
    - in a conda file the real engine allowlists a build string, but still fires on the same line in any other file
      and on a real-looking value in a conda file, under `generic-api-key` and `github-pat` alike;
    - the ignore file is commit-scoped and classed;
    - CI pins the engine and runs this file.

    Its real-engine cases skip in the unit lane (no binary) and run in the Security Scans job, after pip-audit, with
    `GITLEAKS_PARITY_REQUIRED=1`, which turns a missing binary into a failure. That run uses `--noconftest` and
    installs only pytest and PyYAML: the module imports nothing from `src/`.

---

## References

- [CHANGELOG.md](https://github.com/pcalnon/juniper-canopy/blob/v0.10.0/CHANGELOG.md)
- Archive target: `notes/releases/RELEASE_NOTES_juniper-canopy_v0.10.0.md`
