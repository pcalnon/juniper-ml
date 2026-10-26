# Juniper ML v0.11.2 – :lock: SECURITY PATCH RELEASE

**Release Date:** 2026-10-25
**Release Type:** Security Patch
**Priority:** [PRIORITY_LEVEL]
**Package Affected:** juniper-ml

---

This is a security-bearing release of `juniper-ml` v0.11.2. It carries a `Security` Keep-a-Changelog category and was drafted by the release-train from the security template; complete the advisory details (CWE, advisory URL, affected versions) before the ceremony.

---

## Security Impact ([SEVERITY])

| Attribute | Value |
| --------- | ----- |
| **Package** | `juniper-ml` |
| **Fixed in** | 0.11.2 |
| **Vulnerability class** | [VULNERABILITY_CLASS] ([CWE_ID]) |
| **Advisory** | [DEPENDABOT_ALERT_URL] |

---

## Changes in v0.11.2

### Added

- **Tier 3: the monthly full set to the offline drive, as a scheduled lane** (owner ruling D-5, 2026-10-25, on §7.9
  and §8 P3 step 3 of `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md`).
  - **The units** (new): `util/systemd/juniper-backup-full.{timer,path,service}` and
    `util/systemd/juniper-backup-full-failure.service`. The service runs tier 2's scheduler and runner with the lane's
    own environment: state directory `~/.local/state/juniper-backup-full`, drive
    `dee46823-4119-4914-ac15-08194ee27d81` ("Ext WD Passport, Blackbox Part 1" in the owner's `/etc/fstab`, mounted at
    `/run/media/<user>/<UUID>`), directory `Juniper/Backups`, a 30-day period and a 45-day staleness limit. Its
    `--label full --repos "…"` names the ten application repos, `juniper-legacy` and the parent-level
    `notes prompts util backups`, and the scheduler hands both to the runner unchanged. The timer fires monthly and
    the path unit on connection. The owner's fstab deprecates `/mnt/JuniperArchive`, so the path that §7.9 of
    `notes/JUNIPER_2026-09-21_JUNIPER-ECOSYSTEM_BACKUP-INFRASTRUCTURE-INTEGRATED-DESIGN.md` proposed
    is superseded, and that section gains a dated as-built note. Retention stays manual: nothing prunes.
  - **`JUNIPER_BACKUP_DIR` may be a path.** `util/juniper-backup.bash` 1.1.0 accepts a relative path of
    `[A-Za-z0-9._-]+` components (no empty, `.` or `..` component, no leading `/`) and judges every one-component
    value as before. `util/juniper-backup-scheduled.bash` 1.1.0, which checked nothing, runs the same function (its
    body byte-identical) and records a malformed value as `FAILED`, exit 2, before it probes a drive.
  - **The installer.** `util/install_juniper_backup_timer.bash` 1.1.0 gains `--lane full`: the three shared scripts
    and the four full units, copied rather than symlinked, with `--dry-run`, then the full timer and path unit
    enabled. No `--lane`, or `--lane usb`, is the tier-2 install unchanged. `util/duplicati_backup_failure.bash`'s
    header lists the third caller.
  - **The lanes are independent.** Separate state directories give each lane its own lock, status and stamps, so
    one lane's run never blocks or skips the other's, and one lane's success never hides the other's staleness. Both
    path units watch `/run/media/pcalnon`, so every mount starts both checks, and each judges only its own drive.
  - **The gate.** `tests/test_juniper_backup_tier3_lane.py` (new, 47 tests) is wired into `ci.yml` and
    `docs/REFERENCE.md`, which documents the lane in § Juniper Project-Tree Backup.
    `util/ad-hoc/2026-10-25_juniper_backup_tier3_mutation_check.py` (new) shows that it kills 46 of 46 mutants.
    The tier-2 suite passes unchanged, and `util/ad-hoc/2026-10-03_juniper_backup_tier2_mutation_check.py` still
    kills 30 of 30. `util/ad-hoc/2026-10-25_backup_tier2_install_parity.py` (new) shows that the installer's
    default lane installs exactly what the one it replaces did, and
    `util/ad-hoc/2026-10-25_backup_tier3_host_resolution_probe.bash` (new) shows, read-only, that both scripts
    resolve the drive's `Juniper/Backups` on the host from the unit's own settings.
- **Two gitleaks fleet instruments: the provenance of the zero-rule fix in three sibling repos** (the fleet follow-up
  to juniper-ml#2203, which found that a `.gitleaks.toml` with no `[extend]` table loads zero rules).
  - `util/ad-hoc/2026-10-25_gitleaks_fleet_survey.py` reads each of the nine repos' REMOTE default branch through
    the contents API: the `.gitleaks.toml` tables, the `.gitleaksignore` entry count, every workflow step that runs
    gitleaks (action SHA, `GITLEAKS_VERSION`, `GITLEAKS_CONFIG`, `--config`, `if:`), the events those workflows run
    on, any `GITLEAKS_*` variable at any level, and any gitleaks pre-commit hook. It saves each config for the probe.
  - `util/ad-hoc/2026-10-25_gitleaks_probe_for_repo.py` runs `util/ad-hoc/2026-10-10_gitleaks_probe.py` unchanged
    against another checkout (it re-points the probe's `REPO` global), so the `ci-dispatch` scope rules are the
    probe's own rather than a copy's.
  - Verdicts, by the probe's `vacuity` check with gitleaks 8.24.3 (all nine run gitleaks-action v3.0.0, `e0c47f4f`):
    juniper-data, juniper-canopy and juniper-deploy **VACUOUS** (PRs juniper-data#490, juniper-canopy#764,
    juniper-deploy#259); juniper-cascor, juniper-cascor-client and juniper-ml **ACTIVE**; juniper-data-client,
    juniper-cascor-worker and juniper-recurrence have no `.gitleaks.toml`, so gitleaks loads its built-in default.
    juniper-recurrence runs no secret scan in any workflow.

### Changed

- **G-SEC's firewall condition follows C2's block-all form** (turing bring-up task C2, the §18.2 C2 row of
  `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`; owner ruling 2026-10-25).
  The owner chose to block all incoming connections while nothing inbound is needed, over per-app inbound
  denies (RR-11 of `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md`).
  The condition passed at `State = 1`, and its fix still said "allowing signed software".
  - `util/host_state_probe.bash` also captures `socketfilterfw --getblockall` (`blockall` in the security section).
  - `util/host_state_check.py` passes the firewall only when it is on and `--getblockall` reports block all. It
    accepts both block-all sentences in the binary's strings, since turning block all on needs the owner's sudo.
    An unknown or undefined state, or a probe without the capture, cannot be judged (exit 2 under `--check`),
    unless the firewall is off, which fails anyway. The fix names only the missing `socketfilterfw` steps.
    Stealth mode stays reported, not gated, as G1 designed it.
  - `tests/test_host_state_check.py` gains 3 failure cases and a `FirewallTest` class of 5 tests (59 tests across
    the two G1 suites), and `tests/test_host_state_probe.py` pins the capture.
    `util/ad-hoc/2026-10-25_turing_c2_gate_mutation_check.py` kills 11 of 11 mutants, and the 57 of `util/ad-hoc/2026-10-20_turing_g1_mutation_check.py` still apply.
  - `conf/hosts/turing/expected.yaml`'s G-SEC comment follows. turing still fails the condition: its firewall is
    off (`State = 0`), as it was on 2026-10-15.
- **H4's Serena entry turns Serena's usage report off** (turing bring-up, erratum E-H6 of
  `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md`; owner ruling 2026-10-25).
  Serena v1.7.0 sends the OS, the dashboard flag, the version, the backend and the context name to
  `oraios-software.de` at every start unless `SERENA_USAGE_REPORTING` is exactly `false`
  (`src/serena/agent.py:724-737` at `949a27ef`; SER-E1 of `notes/JUNIPER_2026-10-25_JUNIPER-ML_TURING-H6-VSCODE-MCP-SERVERS-AUDIT.md`).
  `util/mcp_setup.bash` wrote `"env": {}`.
  - `util/mcp_setup.bash` now writes `"env": {"SERENA_USAGE_REPORTING": "false"}`. `False` or `0` would still
    report, so the value is the exact string. An entry written before this fails `--check`, and the next write
    replaces it, backing up the old file first. No checkout on turing had an entry yet: H4's live check still
    waits on E-H4-WHEEL.
  - `conf/hosts/turing/mcp.json`'s `verified` record adds the check made at the pin, so a pin bump re-reads it.
  - `tests/test_mcp_setup.py` gains 3 tests (38 in all) and pins the exact value.
    `util/ad-hoc/2026-10-25_turing_h4_usage_report_mutation_check.py` kills 7 of 7 mutants, and the 20 of `util/ad-hoc/2026-10-21_turing_h4_mutation_check.py` still apply.

### Fixed

- **`run_suite` refuses a `per_run_timeout_seconds` the driver's own budgets can outrun** (juniper-ml#2210).
  The subprocess ceiling was compared, in a test only, with the wall budget alone, but the driver's other
  budgets add to that one: two 90 s health waits, dataset creation, and on recurrence a fresh wall budget for
  predict and for crossval plus `save_model`. A suite could pass the test and still be killed from outside:
  `timed_out` with `exit_code: null`, no `manifest.json`, and a re-run on `--resume`.
  - `util/experiments/run_experiment.py` gains `worst_case_budget`, the sum of the bound the driver puts on each
    phase a config runs. `save_model` counts the larger of its two paths: the wall-bounded snapshot `POST`, or
    the 60 s version probe plus the 600 s CLI re-fit for a service that returns no `operation_id`. Those two
    timeouts and cascor's `snapshot_at_end` timeout become named constants.
  - `util/experiments/run_suite.py` sums it per cell after materialisation and exits 2 before the first `--up`
    when `per_run_timeout_seconds` (default 3600) does not exceed it, naming the largest cell and its terms.
    `load_suite` stays structural, so CI's suite gate still needs no sibling repo (D5).
  - The nine recurrence suites sat under their 3900 s budget and now carry `per_run_timeout_seconds: 4500`;
    the 20 cascor suites already cleared theirs (`util/ad-hoc/2026-10-25_driver_budget_survey.py`).
  - The R-6 gate in `tests/test_experiment_suite_yamls.py` sums the same budget. New tests in
    `tests/test_run_experiment.py` and `tests/test_run_suite.py`, including the first to drive the subprocess
    kill. `docs/REFERENCE.md` gains § Suite timeout budget, and it and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`
    state the new rule.

### Security

- **`juniper-secret-assignment` fires on a QUOTED value that contains spaces** (owner-approved 2026-10-25; a
  follow-up to the backup recovery B9 rule of juniper-ml#2203). A value opened by `"` or `'` right after the `=`
  stopped at its first space, so a quoted diceware phrase left only its first word, which is under the
  12-character minimum, and never fired.
  - `.gitleaks.toml`: the regex gains a double-quoted and a single-quoted branch. Each runs to its own close
    quote, spaces and tabs included, and still needs 12 characters. Unquoted values keep the no-whitespace rule.
    The reported value is whichever of the three groups matched, so the rule sets no `secretGroup`. A fourth
    allowlist holds quoted prose: a value containing an English function word as a whole word, such as
    `passphrase="the one you set"`. The comment's measurement and "Known boundary" are updated. Still silent:
    whitespace in a value not quoted right after the `=` (unquoted, unterminated, or systemd's
    `Environment="NAME=..."`), and a quoted passphrase that contains a function word.
  - Across every commit on every remote branch and tag (about 3,130 commits, `--no-ignore`), the rule reports 10
    historical lines, up from 8. The two new ones are one test fixture, two dictionary words in single quotes in
    `tests/test_yamaguchi_edit_target.py`, at two commits. `.gitleaksignore` adds them as commit-scoped entries
    under a new class comment, 34 entries in all.
  - `tests/test_gitleaks_secret_assignment_rule.py`: quoted phrases built at runtime, in both quote styles under
    every name, must report the WHOLE phrase, and the same phrases must stay silent in every unquoted form. It adds
    quoted-prose negatives and pins the boundary lines. Its model takes the first non-empty group, as gitleaks does.
  - `util/ad-hoc/2026-10-10_gitleaks_rule_mutation_check.py` runs 21 mutants, up from 16: dropping the quoted
    branches, an unquoted value running on through spaces, a double- or single-quoted value running past its close
    quote, and dropping the quoted-prose allowlist. A mutant may now state how many times its target text occurs.
    `…_secret_assignment_corpus_survey.py` reads the value group the same way, and `docs/REFERENCE.md`'s suite
    description follows.
- **`[servers]` floors `juniper-cascor>=0.12.0` and `juniper-data>=0.17.1`**, up from `>=0.11.0` and `>=0.17.0`: the two server releases that floor
  the shared security patches (R-ML-SERVERS in §5 of `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`). This is the `[servers]` half of juniper-ml#2314,
  which floored `juniper-observability>=0.4.1` and `juniper-service-core>=0.7.1,<0.8.0` under `[tools]` and left
  `[servers]` until both releases were on PyPI, because a floor on an unpublished release makes the extra
  unresolvable.
  - **juniper-cascor 0.12.0** (PyPI 2026-10-25) floors both patches unconditionally, so an upgrade of `[servers]`
    over an environment that holds observability 0.4.0 or service-core 0.7.0 now moves them too. It also carries
    cascor's own fixes: a non-ASCII `X-API-Key` is a 401, not a 500 whose Sentry event could carry the real key;
    `FailedAuthThrottle.check()` stays bounded; `APIKeyAuth` checks every configured key; and the CLI's own Sentry
    init stops sending frame-local variables.
  - **juniper-data 0.17.1** (PyPI 2026-10-23) differs from 0.17.0 only in its version string and those two floors,
    measured on the published wheels (the builder's setuptools version aside). Both floors sit under its `[api]`
    extra, and `[servers]` installs bare `juniper-data`, so in a `[servers]` environment the patches arrive through
    cascor 0.12.0. The data floor keeps `[servers]` level with the image juniper-deploy#258 pins.
  - The extras tables in `README.md` (both), `AGENTS.md`, `docs/QUICK_START.md` and `docs/REFERENCE.md` move with
    the pins. The `0.11.x` row of `docs/REFERENCE.md`'s compatibility matrix moves with the release that carries
    this, which is the owner's cut. Applied by `util/ad-hoc/2026-10-25_raise_servers_floors_cascor_0_12_0_data_0_17_1.py`, which asserts each site's exact text and requires exactly
    one match apiece.
  - **Pre-flighted against real PyPI** on 2026-10-25 with `util/ad-hoc/2026-10-18_preflight_extras_against_pypi.py`, which resolves Linux x86_64 wheels and
    installs nothing. `[servers]` resolves in 61 packages and `[all]` in 95, on Python 3.12, 3.13 and 3.14, with
    cascor 0.12.0, data 0.17.1, observability 0.4.1 and service-core 0.7.1 (and juniper-cascor-worker 0.6.1 under
    `[all]`). A control with `juniper-cascor>=0.13.0`, which is not on PyPI, fails it.
- **The agent guard covers Serena's edit tools and MCP registration (task C9)** (`notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` §18.2, widened by RR-10 of
  `notes/JUNIPER_2026-10-21_JUNIPER-ML_TURING-H5-RESTORED-MCP-SERVERS-RISK-ANALYSIS.md`). An MCP tool call reached the C8 guard only through its settings matcher, which named Claude Code's own
  tools, so Serena's edit tools could write `.git/hooks` in a primary checkout unseen (E-SERENA-EDIT). No rule covered MCP
  registration either, and a registered server runs a command the guard never sees.
  - `util/claude_agent_guard.py` 1.2.0 adds three rules:
    - `MCP-EDIT-PATH` judges Serena v1.7.0's 19 edit tools. A path argument, resolved against the project roots literally
      and through `realpath`, may not reach `.git/`, `.ssh` or `.gnupg`, Claude's settings or hooks, the owner's git
      configuration, `~/.claude.json` or a `.mcp.json`. `replace_in_files`' include glob and `repl` are judged too, and
      Serena's `execute_shell_command` gets the Bash rules.
    - `MCP-REGISTER-BASH` denies `mcp add`, `add-json` and `add-from-claude-desktop` after any command word, `--mcp-config`,
      and any mention of `~/.claude.json`, a `.mcp.json` file or the two approval keys. So `cat ~/.claude.json` is now
      denied; the Read tool still reads it.
    - `MCP-REGISTER-FILE` denies writer calls on `~/.claude.json` and any `.mcp.json`, and a `.claude/settings*.json` write
      that sets `enabledMcpjsonServers` or `enableAllProjectMcpServers`. `util/mcp_setup.bash` keeps working.
  - The settings matcher now names the eight built-in tools and Serena's tools (`--settings-matcher` prints it).
    `util/install_claude_agent_guard.bash` reads it from the guard, and `--apply` replaces a 1.1.0 entry in place.
  - `tests/test_claude_agent_guard.py` adds 10 tests: 46 registration Bash cases (30 denied), 15 registration file cases
    (8 denied), every Serena edit tool, 32 path cases, 20 `replace_in_files` cases and 7 shell cases. The self-test runs
    50 checks.
  - `util/ad-hoc/2026-10-25_turing_c9_guard_mutation_check.py` kills 26 of 26 mutants, each by its own pin test.
  - The owner re-runs `bash util/install_claude_agent_guard.bash --apply` (task C8) from an up-to-date `main` to install it.

---

## References

- [CHANGELOG.md](https://github.com/pcalnon/juniper-ml/blob/v0.11.2/CHANGELOG.md)
- Archive target: `notes/releases/RELEASE_NOTES_v0.11.2.md`
