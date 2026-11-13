# Juniper ML v0.11.5 – :lock: SECURITY PATCH RELEASE

**Release Date:** 2026-11-13
**Release Type:** Security Patch
**Priority:** High: upgrade every environment installed through `juniper-ml[tools]` or `juniper-ml[all]`
**Package Affected:** juniper-ml

---

This is a security-bearing patch release of `juniper-ml` v0.11.5. The meta-package ships no code: its `[tools]` extra now floors `juniper-observability>=0.4.2`, the security patch that scrubs Sentry transactions, parsed cookies and four more credential headers, and `juniper-service-core>=0.7.2,<0.8.0`, so upgrading an environment through `juniper-ml[tools]` or `juniper-ml[all]` also upgrades an older release of either. juniper-observability 0.4.2 is rated Medium in its own notes, and so is this release; juniper-service-core 0.7.2 is a plain patch. 0.4.2 does not close every path to Sentry: its notes list what stays open for 0.4.3, query strings and Sentry Logs among them. `[servers]` and `[recurrence]` are unchanged: the newest juniper-canopy, juniper-cascor, juniper-data and juniper-recurrence releases still accept juniper-observability 0.4.1 and juniper-service-core 0.7.1, and each is to raise its own floors in its next release (owner ruling 2026-11-09).

---

## Security Impact (Medium)

| Attribute | Value |
| --------- | ----- |
| **Package** | `juniper-ml` |
| **Fixed in** | 0.11.5 |
| **Vulnerability class** | Fixed by juniper-observability 0.4.2, which this release floors: sensitive information sent to an external service ([CWE-201](https://cwe.mitre.org/data/definitions/201.html)) |
| **Advisory** | None. Internal findings, fixed in juniper-observability 0.4.2, which its own notes rate Medium: round-42 finding F2 (2026-09-24) and the validation of consolidated-plan item P3-07 (2026-11-08); there is no CVE or Dependabot alert |

---

## Changes in v0.11.5

### Security

- **`[tools]` floors `juniper-observability>=0.4.2` and `juniper-service-core>=0.7.2,<0.8.0` (owner ruling
  2026-11-09).** They were `>=0.4.1` and `>=0.7.1,<0.8.0`. By default pip upgrades a dependency only when the
  installed one no longer satisfies its range, so `pip install -U juniper-ml[tools]` left an environment that held
  0.4.1 and 0.7.1 on them.
  - **juniper-observability 0.4.2** is the security patch in which `configure_sentry` scrubs Sentry transactions as
    well as error events, redacts the request's parsed cookies and filters four more credential headers
    (`notes/releases/RELEASE_NOTES_juniper-observability_v0.4.2.md`).
  - **juniper-service-core 0.7.2**'s one module change rounds `FailedAuthThrottle`'s `Retry-After` up instead of
    truncating it (`notes/releases/RELEASE_NOTES_juniper-service-core_v0.7.2.md`).
  - The extras tables in `README.md` (both), `AGENTS.md`, `docs/QUICK_START.md` and `docs/REFERENCE.md` move with
    the floors, as do `docs/REFERENCE.md`'s two **Current Version** cells (which still read 0.4.1 and 0.7.1), its
    observability `sentry` extra row (0.4.2 requires `sentry-sdk[fastapi]>=2.35.0`, and the row said `>=2.0.0`), its
    service-core **Meta pin** row and `juniper-service-core/README.md`'s pin advice. The compatibility matrix's
    `0.11.x` row moves its `juniper-observability` cell with them, and the paragraph above it names 0.11.5 as the
    release that raises both floors.
    `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`'s "Current truth" for the service-core pin moves too: it still read
    `>=0.2.0,<0.8.0`, the floor before 0.11.1's.
  - The floors reach `pip` users with juniper-ml 0.11.5. The consumers' own floors (juniper-data, juniper-cascor,
    juniper-canopy and juniper-recurrence) move in each one's next release PR, by the same day's ruling; their
    `requirements.lock` files already pin both releases.

### Added

- **The repo `tmp/` convention: no file is written under `/tmp`** (owner directive, 2026-10-26;
  `notes/JUNIPER_2026-10-26_JUNIPER-ECOSYSTEM_REPO-TMP-DIRECTORY-CONVENTION.md`, new). On the Linux host `/tmp` is a
  tmpfs that `systemd-tmpfiles-clean` ages daily (`q /tmp 1777 root root 10d`). It emptied the isolated E2E stack's
  pid files and venv three times in a week, leaving seven live servers killable by the orphan reaper.
  - `util/tmp_path_literal_check.py` (new), gate G-TMP: a tracked script, test or config under `util/`, `scripts/`,
    `tests/`, `conf/`, `.claude/` or a sub-package may hold no more system temp-dir literal lines than
    `conf/tmp_path_literal_baseline.json` (new; 315 files, 453 lines) allows it. It mirrors G-PATH's CLI, exit codes
    and baseline schema; `# tmp-path-literal: allow` exempts a line; `.github/` is out of scope. It runs as the
    `tmp-path-literal` pre-commit hook and as a whole-scope step in ci.yml's Pre-commit job.
  - `util/juniper_repo_tmp.bash` (new) prints the PRIMARY checkout's gitignored `tmp/` for a directory, creating it,
    and exits 1 outside any checkout; sourced, it defines `juniper_repo_primary` and `juniper_repo_tmp`.
  - `tests/test_tmp_path_literal_check.py` and `tests/test_juniper_repo_tmp.py` (new), wired into ci.yml and
    `docs/REFERENCE.md` (234 suites).
  - `.gitignore` ignores the root-anchored `/tmp/`.
  - Records: `util/ad-hoc/2026-10-26_tmp_literal_sweep.py` (the inventory), `util/ad-hoc/2026-10-26_guard_live_e2e_servers.py`
    (wrote the seven reaper guards) and `util/ad-hoc/2026-10-26_session_tmpdir_hook_probe.py` (the SessionStart hook,
    its known answers and its installer).
- **`HARCOT` joins the `notes/` repository tokens (2026-11-10).** juniper-harcot, the private
  equities-analysis repository built on juniper-recurrence, names its notes
  `JUNIPER_<date>_JUNIPER-HARCOT_<phrase>.md`. The token is added everywhere the list is stated:
  `notes/JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md` (§2, with an assignment
  rule), `AGENTS.md`, `.claude/agents/{planner,auditor}.md`, and
  `prompts/agent_templates/{audit,plan,code-review}.md`.
  Documentation only; no script enforces the token list.
- **The yamaguchi securityfs incident: root cause, remedy, and a host check that would have caught
  it (2026-11-07).** juniper-deploy's `make up` failed on every container with *"Could not check if
  docker-default AppArmor profile was loaded: open /sys/kernel/security/apparmor/profiles: no such
  file or directory"*. The cause is a missing mount, not a missing profile. A root `umount -a`-like
  event on 2026-10-27 at 17:55:25 CDT unmounted everything not in use. The same-day repair restored
  what `systemctl` lists: the snaps and the six unit-file API mounts. PID 1's own securityfs, pstore
  and bpf mounts have no unit file, so nothing listed them and nothing remounted them. dockerd caches
  AppArmor support once, at start, so it kept checking the absent interface. snap-confine has been
  failing every snap since: the legacy k8s snaps, `helm`, and every snapd refresh.
  - `notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-SECURITYFS-UNMOUNT-ROOT-CAUSE-ANALYSIS.md`
    holds the causal chain, each link pinned to evidence and to upstream source lines at the host's
    exact versions. It also has the timeline, the blast radius, the rejected hypotheses, the
    unconfirmed actor, and the vetting against the kubeadm install.
  - `notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-API-FILESYSTEM-REMOUNT-RUNBOOK.md` is the
    owner's root procedure: no reboot, legacy snap k8s services disabled first (decision D-1), three
    `mount` commands with systemd's options, then validation.
  - `util/host_api_filesystems_check.py` (new) judges `/proc/self/mountinfo` against systemd's
    API-filesystem table and AppArmor's interface. Tests: `tests/test_host_api_filesystems_check.py`,
    25 tests, CI-wired. Its mutation check kills 11 of 11, including "judge only unit-file mounts",
    the repair's own blind spot.
  - `reports/2026-11-07_yamaguchi-securityfs-unmount/` holds the evidence: probe, systemd timelines,
    source pins, the validator's negative control, the deploy suite's main-vs-branch comparison, and
    both mutation logs. The investigation scripts are kept in `util/ad-hoc/2026-11-07_*`.
  - Finding 17 of `notes/JUNIPER_2026-10-03_JUNIPER-ECOSYSTEM_BACKUP-SYSTEM-STATE-ASSESSMENT-AND-RECOVERY-PLAN.md`
    carries an erratum: "repaired without a reboot" was incomplete.
- **Regression tests carried from 28 Cursor fleet drafts (the flood-4 consolidation, owner ruling 2026-11-06), each
  mutation-checked against the code it pins.** In `juniper-service-core/tests/`: the failed-auth tracker drops the
  oldest of its 10,000 source IPs (#2419); an exhausted rate-limit window admits again at its boundary (#2427); a
  worker connection burst refills only up to its cap (#2430); a stuck worker's scores become a duplicate (#2436);
  `/ws/control` refill and handshake edges (#2439); replay continuity at the buffer edge (#2441); an anomaly warning
  still accepts the result (#2443); replay speed, range and paused terminal transitions (#2445); a measured zero
  heartbeat overwrites and the exact timeout is stale (#2447); a request body, a WebSocket frame and a result's
  attachments that exactly fill their caps are admitted (#2451, #2458, #2463); a task at the exact reassignment
  timeout (#2461). In `juniper-ci-tools`: a list-item fence indented three spaces is not a heading (#2425). At the top
  level: a zero score and a zero theta stay measured values (#2413); the `AGENTS.md` date check's three-dot diff,
  whitespace and unset `BASE_SHA` (#2414); which capture decides G-SEC block-all (#2416); a non-object `stats.json`
  (#2429); a failed snapshot save that does not re-fit (#2431); a schema-1 `eval_scalars` block (#2434); the Phase D
  trial drop-in merged onto the live unit (#2421); and four new suites, wired into `ci.yml` and `docs/REFERENCE.md`:
  `tests/test_claude_agent_guard_brace_cap.py` (#2466), `tests/test_per_run_timeout_boundary.py` (#2448),
  `tests/test_host_state_gate_boundaries.py` (#2459) and `tests/test_release_train_exact_caps.py` (#2455).
  - **Fixed before carrying.** #2455's six mypy errors (`list.append(...) or value` lambdas). #2410's wheel test keeps
    its positive half and drops its negative control, whose premise is false: setuptools 81.0.0 and 84.2.1 package a
    `py.typed` they find even undeclared; the same file's older text, which said an undeclared marker misses the
    wheel, is corrected too. The regression job installs `setuptools` and `wheel` for it. #2403's and #2407's launcher
    tests are rewritten against `main` after #2438 and #2468 (the `--` before the prompt, `-v` reporting Claude Code's
    version, remote control on by default), and #2407's mypy error is fixed. #2403's effort test keeps only its
    `--effort 1` half: its `--effort 0` half pinned `--effort auto`, which Claude Code rejects ("Unknown --effort
    value"), so that carrier left the script's default open; the launchers entry under Fixed, below, sets it to
    `max`.
  - **From two docs drafts**, the Test Suite Reference sentences this block owns: #2424's on the `--getglobalstate`
    line in `tests/test_host_state_check.py`'s entry, and #2432's on when `aggregate` falls back from `stats.json`
    in `tests/test_run_suite.py`'s, each without its link to a section only the docs carrier adds.
- **Operator documentation consolidated from the Cursor flood-4 docs drafts** (ml#2409, #2412, #2417, #2418,
  #2422, #2426, #2428, #2432, #2433, #2437, #2442, #2444, #2446, #2449, #2456, #2457, #2460, #2462, #2464 and
  #2465), every claim re-derived from `main`, the sub-package code, PyPI and the Claude Code settings docs:
  `docs/REFERENCE.md` 0.6.64, the developer cheatsheet, the documentation overview, the quick start, and the
  `juniper-config-tools` and `juniper-service-core` READMEs. #2424 makes #2426's claim; only #2426's
  wording is carried. Corrected where a draft had gone stale or was wrong: recurrence 0.8.1 has been on PyPI since
  2026-11-06, so the crossval-500 page gives the fix instead of a wait; an undeclared `py.typed` still reaches a
  wheel (setuptools adds it implicitly), and the 0.1.0 wheel is untyped because the file did not exist yet;
  `juniper-config-tools` joined `[tools]` in juniper-ml 0.6.0, not 0.5.0; juniper-ml#2271 closed unmerged; a fit
  that returns while paused is documented as the defect it is (after resume a start with data is a 409 until stop
  or reset); seven sections that sat in the footer, split a paragraph or had swallowed existing text were moved.
  Also corrected in `main`'s own pages: the first releases with the non-ASCII API-key and Sentry frame-locals
  fixes (`juniper-service-core` 0.7.1 and `juniper-observability` 0.4.1; juniper-data 0.17.0, juniper-cascor
  0.12.0 and juniper-canopy 0.9.0 for their own key compare); `accuracy` (juniper-cascor#731) first ships in
  juniper-cascor 0.13.0; the CR-024 413 for an under-declared `Content-Length` holds only at the ASGI layer; and
  juniper-data's HTTP body limit and the worker binary-frame cap are 10 MiB and 100 MiB.
  From #2452 only the cheatsheet's `--fork-session` example is carried: its forwarded argv now shows the `--` that
  `wake_the_claude.bash` puts before the prompt. Not carried: #2440, the same launcher claim; the rest of #2452's
  launcher page predates #2468, whose own cheatsheet text is current.
- **The Cursor flood-4 disposition record, with its render inputs and provenance scripts (round 1 complete).**
  `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md` records how the 74-PR census was
  disposed of: six carriers (juniper-data#518 and #519, juniper-canopy#797 and #802, juniper-ml#2517 and #2519)
  merged, and all 68 census drafts assigned to them closed, 67 of them carried. It also records each carrier's 2 to
  6 independent validation rounds, the defects found on `main`, the per-PR disposition (§5), the process traps, and
  the owner's rulings 1–7 of 2026-11-08: round 2 takes 48 drafts; the launcher's effort default becomes `max`, and
  an explicit `auto` will send no `--effort` flag; three of the four open defect rows in §4 get their own fixes
  now; and juniper-ml#2271's one setting moved to user settings, with its branch deleted. Later rulings decide that
  the agent guard's brace cap is to fail closed, that the gitleaks fix is to be ported to the seven other
  repositories that run the action, and that four more defects found while the first fixes were built are to be
  fixed, each in its own PR; none of these had landed when this record merged. Since then the brace-cap change and the
  two `juniper-service-core` fixes among those four (the broadcast-drop and stop-then-start entries under Fixed, below)
  have landed in this repository. §5's six manifests and render config are archived under
  `reports/2026-11-08_flood4-disposition/`, from which §5 re-rendered byte for byte (the renderer also reads each
  PR's live state). The arc's 160 `util/ad-hoc/2026-11-07_flood4_*` and `2026-11-08_flood4_*` scripts, from the
  nine of its worktrees that held them, are kept as provenance. Before upload they were made to pass gates G-TMP
  and G-PATH and the secret scan, 21 of 28 predicted CodeQL alerts were fixed (the other 7 are pydantic fields the
  prescreen misreads), and 29 probes gained provenance fields; nothing they compute changed. Round 1's closing
  handoff and its successor are archived under `prompts/thread-handoff_automated-prompts/`.

### Changed

- **Fixed temp paths instead of the system temp dir** (the 2026-10-26 repo `tmp/` rule).
  - `scripts/wake_the_claude.bash` exports `TMPDIR` / `TMP` / `TEMP` (the starting Juniper repo's primary `tmp/`, else
    juniper-ml's) and `CLAUDE_CODE_TMPDIR` (juniper-ml's, as `~/.claude/settings.json` sets it), and refuses to launch
    when no `tmp/` can be made. It also exports `GIT_CEILING_DIRECTORIES` at the `tmp/` dirs, so git run under a
    `TMPDIR` inside a checkout does not find the enclosing checkout; the SessionStart hook in
    `util/ad-hoc/2026-10-26_session_tmpdir_hook_probe.py` writes the same list (6 of 6 known answers pass).
  - Five tests that build a "not a git repository" fixture set `GIT_CEILING_DIRECTORIES` in their subprocess env
    (`tests/test_configure_commit_signing.py`, `tests/test_predict_merge.py`, `tests/test_prompt_discovery.py`); no
    assertion changed.
  - `juniper-check-doc-links` gets `--exclude tmp` in the pre-commit hook, `ci.yml`, `docs-full-check.yml` (both
    invocations), `AGENTS.md` and the cheatsheet: it walks the tree, so scratch markdown under `tmp/` failed it locally.
  - `util/isolated_stack.bash` defaults its run dir to the FIXED `tmp/juniper-e2e` of the juniper-ml primary checkout,
    never derived from `TMPDIR`; `util/ad-hoc/2026-09-04_canopy_verify_instance.bash` follows it.
  - `util/experiment_stack.bash` falls back to juniper-ml's primary `tmp/juniper-experiments` for its lock root when
    `XDG_RUNTIME_DIR` is unset.
  - `util/host_state_probe.bash`, `util/headless_signing_preflight.bash` and `util/ad-hoc/watch_fable5_availability.bash`
    make their scratch dir under `TMPDIR`, else the checkout's `tmp/` (no `git`), and
    `tests/test_headless_signing_preflight.py`'s socket dir no longer uses `/tmp`.
  - `AGENTS.md` gains a resident hazard and § Temporary files, and drops § Script placement's "/tmp as a scratch
    workspace" exception. § Requirements (JR-ID) moved to `docs/REFERENCE.md` to pay for them (25930 -> 25991 chars).
  - The operative procedures that wrote under `/tmp` now use `tmp/`: the PyPI publish, worktree cleanup, YubiKey
    key-to-card and Docker Hub secret procedures, the SOPS guide (the new age key goes beside the old one), the
    isolated-stack checklist, the release-train runbook, `docs/REFERENCE.md`, the developer cheatsheet and the
    Template Agent's standing rule.
- **The owner's 2026-10-26 rulings on `tmp/`**, quoted in section 1 of
  `notes/JUNIPER_2026-10-26_JUNIPER-ECOSYSTEM_REPO-TMP-DIRECTORY-CONVENTION.md`: the doc-link checker and local Docker
  builds ignore `tmp/`; pytest does not; a counting script chooses its scope deliberately (the owner's revision, later
  the same day); full-tree repo copies and log copies may live there; and a work arc's `tmp/` file is kept until four
  conjunctive conditions hold (that doc's section 6).
  - `--exclude tmp` reaches the remaining doc-link checker invocations: two more cheatsheet rows, `docs/REFERENCE.md`'s
    Docs Full Check summary and `juniper-doc-tools/README.md` (CLI and library examples). The `--version` smoke steps
    walk nothing. `--exclude` matches any path component, so a nested `juniper-*/tmp/` is covered too (measured).
  - pytest: no `norecursedirs`, `--ignore` or `collect_ignore` names `tmp` at the root, in the six sub-packages or in
    the three `conftest.py` files, so nothing changed; `testpaths` keeps a bare `pytest` in `tests/`.
  - Docker: juniper-ml has no build context (no Dockerfile, Containerfile, compose file or `.dockerignore`, the
    sub-packages included).
  - The owner's revised search ruling: a script that counts matches with `grep` or `find` searches the repo with its
    `tmp/` excluded, or `tmp/` alone, and both only for a stated edge case; existing counting scripts are to be
    modified to make that choice explicit, not left to `.gitignore` or a tool's defaults. The convention doc's new
    section 11 documents the juniper-ml counting sites still owed that change (ten rows, twelve files), as the owner
    asked; none of them is modified here. The ten sibling repos report theirs in their own PRs.
  - `util/ad-hoc/2026-10-26_tmp_literal_sweep.py` (0.3.0) makes the choice: by default the repo with `tmp/` excluded by
    the explicit root-anchored glob `!tmp/**` (not by ripgrep's `.gitignore` handling), and with `--tmp-only` the
    `tmp/` alone, its own ignore files disregarded, reported as a `scratch` class.
  - `AGENTS.md` § Temporary files gains the rulings and drops the "tree walkers must skip `tmp/`" bullet they
    supersede (26390 -> 27404 of 28000 chars). The convention doc gains them in sections 1, 4.7, 4.8 (new), 6, 9, 10
    and 11 (new), and the Template Agent's standing rules gain `repo_tmp_rulings`.
- **`-v` reports Claude Code's version in both launchers, `claudey` takes a prompt file, and the default interactive
  session turns on remote control (owner rulings, 2026-11-06).** In `scripts/wake_the_claude.bash` (now 1.1.0), `-v`
  joins `-V`, `--version` and `--claude-version`, as `claude -v` does; it printed the script's own version, which
  `--script-version` alone now prints. `claudey` (`scripts/claude_interactive.bash`, now 0.2.0) runs `wake_the_claude.bash
  --version` for all four, so they print Claude Code's version too; `-v` and `--version` printed claudey's,
  which `--script-version` now prints. `claudey` forwards a prompt file, `--file` / `-f` / `--file-name` and `--path` /
  `-l` / `--file-path` (or `CLAUDE_PROMPT_FILE` / `CLAUDE_PROMPT_PATH`), and then sends no default prompt:
  `wake_the_claude.bash` prefers `--prompt` to a prompt file, so the default would have discarded the file. A prompt
  together with a prompt file exits 1 for the same reason. `scripts/default_interactive_session_claude_code.bash` sends
  a bare `--remote-control`, as `claudey` does. `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` describes all three, and no
  longer says `claude` is invoked with an unquoted parameter array: both the interactive and the `nohup` call quote it.
  Found in review:
  - `claudey` exits with `wake_the_claude.bash`'s status. It always exited 0, so a prompt file that
    `wake_the_claude.bash` refused ended in "Closed …" and success.
  - It refuses an empty `--file` / `--path` value and an empty word. An empty word ended its parsing, and the words
    after it were dropped, so `-f "${UNSET}"` or `-w '' --file f` launched with the default prompt. `-w ''` is now a
    bare `-w`.
  - `wake_the_claude.bash` prints its errors on stderr as well as in the debug log: a version flag with no `claude`
    on `PATH` or no version printed, a prompt file that never resolves, and any flag it refuses. With `WTC_DEBUG=1`
    each was a bare exit 1 or the usage text alone.
  - `claudey`'s usage text names its own script instead of `wake_the_claude.bash`, lists `-h`, and shows a prompt
    and a prompt file as alternatives. An empty word is reported as "(an empty word)". `claudey -v` prints no debug
    log unless `WTC_DEBUG` asks for one.

### Fixed

- **The pre-commit doc-link hook skips the repo's gitignored `tmp/`.** The hook runs
  `juniper-check-doc-links` with `pass_filenames: false`, so the checker walks the whole checkout, `tmp/`
  included, and scratch copies of notes kept there failed it. It reads `.txt` as well as markdown, so even
  captured logs there can fail it. On 2026-11-08 the primary checkout failed with 2,424 broken-link lines,
  every one under `tmp/`. With `--exclude tmp` it passes: 2,365 files scanned, every link valid. This
  implements the 2026-10-26 owner ruling for the
  hook only. The hunk is byte-identical to juniper-ml#2360's, which has since merged (2026-11-12 UTC) and carries
  the CI and documented invocations. `--exclude` matches a whole path component, so only directories named
  exactly `tmp` are skipped; no tracked file lives in one.
  `util/ad-hoc/2026-11-08_doc_links_tmp_exclusion_check.py` reads the hook's arguments from
  `.pre-commit-config.yaml` and checks a fixture tree in four cases: a broken link under `tmp/` is skipped;
  without the flag it fails; a broken link in `notes/` or in `tmp-archive/` still fails.
- **`juniper-service-core`: a `resume_ok` on `/ws/training` now means the client missed nothing up to the moment
  its socket goes live.** The defect is the juniper-service-core `resume_ok` row of the defect table in
  `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`, ruled "Fix now" by the owner on
  2026-11-08. A broadcast made with no socket active is now sequenced and buffered. One that lands while the
  replay is being sent reaches the client before its socket goes live, through the new keyword-only
  `promote_to_active(..., replayed_through=...)`. A resume that cannot stay continuous after `resume_ok` is closed
  1011 `Resume replay incomplete` instead of being left with a hole.
  - Unreleased. The new API makes the next juniper-service-core release a minor (0.8.0), and `[tools]` caps
    `juniper-service-core<0.8.0`, so that cap has to rise when 0.8.0 ships. The current releases of
    juniper-canopy, juniper-cascor, juniper-data (`[api]`) and juniper-recurrence cap it below 0.8.0 too, so
    `[servers]`, `[recurrence]` and `[all]` stay on 0.7.x until they raise theirs.
  - `docs/REFERENCE.md` (0.6.66) and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` (1.0.66) describe the fixed
    behaviour. `util/ad-hoc/2026-11-08_service_core_resume_continuity_mutation_check.py` is the mutation check
    (25/25 arms).
  - juniper-cascor's own copies of the manager and handler carry both defects and are not changed. Details are in
    `juniper-service-core/CHANGELOG.md`.
- **The yamaguchi securityfs incident: remediated, recorded, and two defects in its validator fixed.**
  The owner ran the remount runbook on 2026-11-08, and the three filesystems have been mounted since
  08:28:29Z. The validator passes, all seven juniper containers run confined by `docker-default`, and
  juniper-deploy's suite has no failures (409 passed, where 17 had failed). The record is §14 of
  `notes/JUNIPER_2026-11-07_JUNIPER-ECOSYSTEM_YAMAGUCHI-SECURITYFS-UNMOUNT-ROOT-CAUSE-ANALYSIS.md`.
  - **The validator accepted an empty baseline.** Step 4 compared the host against an empty file and
    listed 22 `UNEXPECTED` differences where nothing unexpected had changed.
    `util/ad-hoc/2026-11-07_securityfs_remount_validate.bash` now refuses a baseline that is not a
    fingerprint (exit 2, before any check runs), fails closed, and has a `check` mode. Its first
    version passed the probe's report, because bash abandons a function on an empty
    associative-array key; the key check now runs in `awk`.
    `util/ad-hoc/2026-11-08_remount_validate_baseline_gate_check.py` runs 14 cases and 10 seeded
    defects: all cases pass, and every defect is caught.
  - **The analysis is corrected.** systemd never gives an API mount point a unit, mounted or not
    (`src/core/mount.c`, `mount_setup_unit()`). The analysis had said the units are garbage-collected
    once unmounted. `util/ad-hoc/2026-11-08_api_mount_units_check.bash` tests the correction live. The
    conclusion stands.
  - **Runbook step 1** sets `J`, stops when the scripts are missing, and runs the probe only after a
    good capture. Step 4 names a fallback baseline.
  - The evidence, from the owner's terminal output to the after-probe, is in
    `reports/2026-11-07_yamaguchi-securityfs-unmount/`.
- **`util/fleet_triage/predict_merge.py` triages a PR whose head exists only as `origin/<branch>` from a shallow
  checkout, and refuses a history that a shallow checkout cannot show.**
  - **The cause.** The scratch was `git clone --shared <checkout>`, which writes the alternate only for a local
    clone, and git turns local mode off for a shallow source. juniper-ml's primary checkout has been shallow since
    at least 2026-09-10 (a stray `.git/shallow` entry from 09-07). The clone was therefore a pack transfer that
    carried only objects reachable from the checkout's local branches and tags. Every fleet PR's head failed
    `update-ref` ("nonexistent object"): 44 of 45 open PRs came back `ERROR` on 2026-11-04, and 56 of 57 on
    2026-11-06.
  - **The fix.** The scratch is now `git init`, matched to the checkout's object format, plus an
    `objects/info/alternates` entry naming the checkout's object store.
  - **Four more defects, found by review of the fix, also fixed:**
    - The scratch takes the source's `.git/shallow`. A merge or ancestor check that fails for any reason other than a
      conflict is now an error, and so is a behind branch whose merge did not take `main`. A history cut above the
      merge base had come back mergeable, unmerged.
    - No filter driver runs in the scratch (`* -filter`), so `filter.lfs.required` configured without git-lfs
      installed no longer breaks it.
    - A binary file in a PR no longer raises `UnicodeDecodeError` mid-batch.
    - An inherited `GIT_DIR` no longer re-initialises the source.
  - **Docs.** `docs/REFERENCE.md` describes the new scratch. `.claude/agents/fleet-supervisor.md` drops three wrong
    claims:
    - the rulesets' strict up-to-date policy is off: it is on in juniper-ml, juniper-data and juniper-canopy;
    - CI never runs on the merge result: a PR's CI runs on `refs/pull/N/merge`;
    - a BEHIND branch is fixed by a rebase: GitHub's update-branch is the fix.
- **The agent guard expands brace sequences as bash does, fails closed on a brace expansion past its cap, and denies
  the git and GnuPG prefixes that sign (`util/claude_agent_guard.py` 1.3.0).**
  - **Brace cap: "Fail closed"** (owner ruling, 2026-11-08). The guard expands at most `MAX_BRACE_ALTERNATIVES` (64)
    alternatives. A word that needed more was judged on its first 64, so a `.ssh` or `.gnupg` spelled in alternative
    65 passed the credential check. Such a word now raises `MalformedInput` and the hook exits 2, for a Bash word, a
    range, a product of groups, a Glob or Grep pattern and a Serena include glob alike. A list is counted part by
    part, so at most one part past the cap is taken in (a nested part adds at most 64 words), and a range is sized
    arithmetically, so `{1..1000000}` is refused without being expanded. `for i in {1..100}` is refused too;
    `$(seq 1 100)` is not.
  - **Brace sequences** (owner ruling "Carry in ml-code", 2026-11-09). bash 4 and later expand `{x..y..incr}`, which
    the guard left as written, so `cat ~/.{r..t..1}sh/config` read `~/.ssh/config` and passed the credential check;
    `{s..s..1}udo` and `gpg{2..2..1}` hid `sudo` and `gpg2` the same way. The guard now follows bash 5.3's brace code
    for sequences and the lists around them: a step of either sign, a step of 0, a step past the range, `+` signs, zero
    padding (`{01..03}`, which it had expanded as `1 2 3`), a `}` met before the first separator kept as text, and no
    rescan of the words one expansion made. It refuses (exit 2) what it does not model: a sequence group with a brace
    inside it, which bash 5.2 and 5.3 expand differently; a letter sequence that makes a backslash or a backtick, which
    bash 5.3 reads as an escape (it makes `.ssYh .ssh .ss_h` of `.ss{Y..a..3}h`) or a command substitution; and an
    operand past 2**61. Checked word by word against bash 5.3.9 (173 fixed words, 2,000 generated ones):
    `util/ad-hoc/2026-11-08_flood4r2_ml_code_brace_sequence_probe.py`.
  - **The brace scan is one pass, with a budget.** bash finds the `}` of each `{` by scanning to the end of the
    word, which costs the square of the word's length when most groups never close. Ported as written, that took
    the hook 7.7 s on a 25.8 KB `python3 -c` word of `{name}` placeholders (0.12 s on `main`, same run), and the
    hook's timeout is 10 s. `_brace_closes` now answers every `{` of a word in one pass from the right, and the same
    word takes 0.08 s. A list part is scanned again when it is expanded, so `BRACE_SCAN_BUDGET` (2,000,000
    characters per expansion) bounds the sum: a word that needs more is refused (exit 2), never passed unexamined.
    Of the 40,942 Bash commands in the newest 200 session transcripts, the longest is 35,859 characters, and no
    expansion among them scans more than 24,126, 1.2% of the budget.
    `util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_equivalence.py` compares the new scan with the ported one on 3.8
    million words: the same words in the same order, or the same refusal, on every one.
  - **What the brace expansion still does not see.** It reads each word after quote removal, so it cannot tell a
    quoted or escaped brace from a bare one. That judges words bash does not make, and it can also leave a word
    that bash does make unjudged, in three ways:
    - an escaped `}` ends a brace list here that bash keeps open, and a quoted `$` hides a group that bash expands;
    - bash's `{}` rule is not modelled (a `{` followed at once by `}` at the start of a word, of a list part or of
      the text after a group opens nothing);
    - bash steps over the body of a `$(...)` and of backticks, which the scan reads as text.
  - **Known open bypasses.** Three spellings are known to reach `~/.ssh` or `~/.gnupg` and pass, on `main` as
    well, and they stay open: `cat ~/.ss{h,b\}c}/config` (the escape gap: the owner has ruled that a quote- and
    escape-aware expansion follows in its own PR); and, behind an `X/..` hop, an unbalanced `{` inside a command
    substitution in a brace list (`~/X/../.ss{h,$(:{)}/config`) and an empty substitution or parameter spliced into
    the name (`~/X/../.ss$(:)h/config`). The owner has ruled that the same PR fixes those two. The guard's docstring lists all
    three (gap 12), and `util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_pins_vs_bash.py` shows that each still passes.
  - **GnuPG** (juniper-ml#2493): a long option counts from two letters, not four. GnuPG 2.4.8 runs `--cl` as
    clear-sign, `--ls` as lsign-key and `--det` as detach-sign, and rejects every one-letter prefix of a denied
    option as ambiguous, so one letter stays allowed. juniper-ml#2485's floor pins are rewritten into
    `tests/test_claude_agent_guard.py`: as submitted they asserted that `gpg --cle` is allowed.
  - **git** (juniper-ml#2502, juniper-ml#2508): a prefix git runs as a signing option is denied. `--g` is
    `--gpg-sign` on `commit`, `merge`, `rebase`, `am`, `pull` and `commit-tree`; `git tag --si` and `--lo` are
    `--sign` and `--local-user`; `git push --si`, `--sign=true` and `--si=if-asked` request a signed push.
    `--no-gpg-sign`, `--signoff` and the ambiguous `git tag --s`, `git tag --l` and `git push --s` stay allowed.
    One matcher, `_git_long_abbrev`, serves all three subcommand families.
  - Every git and GnuPG claim was re-derived on this host's git 2.53.0 and GnuPG 2.4.8, with a recording
    `gpg.program` stub for git and an empty GnuPG homedir with no agent for gpg, so no keyring, agent or smartcard
    was reachable: `util/ad-hoc/2026-11-08_flood4r2_ml_code_git_gpg_probe.py`.
  - The owner re-runs `bash util/install_claude_agent_guard.bash --apply` from an up-to-date `main` to install it.
- **The launchers: `max` is the effort default again, `auto` sends no `--effort`, and two prompt-file holes are
  closed.**
  - **Effort** (owner ruling, 2026-11-08). juniper-ml#2396 had made `scripts/wake_the_claude.bash`'s
    `EFFORT_DEFAULT` `auto`, which Claude Code answers with "Unknown --effort value 'auto'" and ignores.
    `--effort 0` now sends `--effort max`, and `--effort auto` (any alias, any case) sends no `--effort` flag, so
    Claude Code uses its own default. `scripts/claude_interactive.bash` already defaulted to `max` and forwards
    `-e auto` unchanged, so its effort handling needed no change.
  - **A later unresolved prompt file does not send the earlier one** (juniper-ml#2505). `--file good.md --file
    missing.md` and `--path good.md --path emptydir` exited 0 and sent `good.md`; they now exit 1 without launching.
  - **An exported empty `CLAUDE_PROMPT_FILE` or `CLAUDE_PROMPT_PATH` is refused** (juniper-ml#2504), as `--file ''`
    already was. It launched with the default prompt.
- **`util/fleet_triage/predict_merge.py` drops an inherited `GIT_SHALLOW_FILE` and `GIT_GRAFT_FILE`**
  (juniper-ml#2513). A shallow file naming the branch tip turned a merely-behind branch into an error ("refusing to
  merge unrelated histories"), and a graft reparenting the tip onto `main` reported `MERGE-CLEAN`. Its docstring now
  describes the scratch repository and its error rules (juniper-ml#2494's docstring hunk).
- **Tests.** Five new suites, 239 in CI's regression list: `tests/test_claude_agent_guard_git_sign_abbrev.py`,
  `tests/test_claude_agent_guard_push_signed_abbrev.py`, `tests/test_prompt_file_later_flag.py`,
  `tests/test_claudey_empty_prompt_file_env.py` and `tests/test_predict_merge_inherited_git_env.py`.
  `tests/test_claude_agent_guard_brace_cap.py` is inverted under the ruling and extended to `.gnupg`, 10,000 and
  100,000 alternatives, products, ranges and the hook's exit 2. Its `BraceSequenceTest` pins the words bash 5.3.9
  makes of 35 sequence words, the stepped-sequence denies and the refusals. Its `BraceScanTest` checks the one-pass
  scan against a scan from each brace on every word of up to 7 characters over `{ } , . a`, and pins the budget:
  the exact character at which a word is refused, a list part charged again, a word with no brace never charged,
  and the hook's exit 2. `tests/test_claude_agent_guard.py` gains stepped-sequence rows in its credential,
  privilege and GnuPG tables, and the self-test seven checks (50 to 57). `tests/test_wake_the_claude.py` pins both
  effort behaviours. `util/ad-hoc/2026-11-11_flood4r2_ml-code-r3_mutants.py` runs the carrier's tests against
  `main`'s four code files, where they fail, and applies 72 one-line mutants to a copy of the tree: 70 are killed,
  and the two that survive are equivalent (the list is round 2's 36, a validator's 22 and 14 on the scan and its
  budget).
- **`juniper-service-core`: a `fit` that returns while the run is paused settles `COMPLETED` instead
  of wedging the lifecycle, and the training thread settles only a run it still owns** (the
  "paused-fit wedge" in §4 of `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`;
  owner ruling "Fix now", 2026-11-08). The training thread called `mark_completed()`, which refuses
  `PAUSED`, and ignored the refusal. The machine stayed `PAUSED` with no thread behind it; after a
  resume it read `STARTED`, and every start with data was a 409 until a stop or reset. The thread now
  releases the pause before it records the completion, and the state machine is unchanged. Every
  settle is also guarded by `self._thread is threading.current_thread()`, so a stopped run's `fit`
  that outlives a following start no longer completes or fails the newer run when it ends. The overlap
  itself remains: that `fit` still runs to its end, and its events still reach the shared sink. The
  pause release on a paused completion or failure also wakes such a `fit` if it is waiting at the
  shared pause gate, and a start is then accepted beside it. The owner has ruled that this race gets
  its own fix, in its own PR (§8, ruling 11 of
  `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`); that fix is the
  stop-then-start entry below, with which such a start is refused while the stopped `fit` still runs.
  - Pinned by `juniper-service-core/tests/test_lifecycle_paused_fit_return.py` (11 tests).
    `util/ad-hoc/2026-11-08_paused_fit_wedge_mutation_check.py` runs nine mutants of `manager.py`;
    each is killed by that file and by no other test. `util/ad-hoc/2026-11-08_paused_fit_wedge_doc_stamps.py`
    re-derives the four doc stamps below from `main`'s values, for a rebase.
  - `docs/REFERENCE.md` 0.6.65, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` 1.0.65, `docs/QUICK_START.md`
    0.3.45 and `docs/DOCUMENTATION_OVERVIEW.md` 0.2.57 describe the fixed behaviour and keep the old one
    for juniper-service-core 0.7.2 and earlier, which still have it.
  - Details are in `juniper-service-core/CHANGELOG.md`; unreleased, first in the juniper-service-core
    release after 0.7.2.
- **`juniper-service-core`: a `/ws/training` socket whose broadcast send fails or times out is closed 1011
  instead of being left open on a stream nothing is sent to** (owner ruling 11 in §8 of
  `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`). `broadcast` dropped such a socket
  from the fan-out without closing it, so the client kept answering heartbeats, was never told it was missing
  frames, and held a socket that its released per-IP slot no longer counted. It is now closed **1011**
  `Broadcast send failed or timed out`, as juniper-cascor's copy closes it (F-CASCOR-004), and after any
  server-side close the receive loop drains until the disconnect instead of raising Starlette's `RuntimeError`
  on a late frame.
  - Known limit, not changed here. The drop still releases the socket's connection and per-IP slots at once,
    before the socket is gone, and `endpoint_counts()` counts the socket until its handler returns. So while
    the close is in progress, a new socket from the same address can be admitted past
    `max_connections_per_ip`. Under real uvicorn, for a client that had stopped reading, that lasted 29.5 to
    29.9 s with the default `websockets` implementation and more than the 45 s observed with `wsproto`.
  - It is also a change for a service's own handler on a socket it registered with `connect()`: the manager
    now closes that socket, and the handler must then drain with `receive()`.
  - Unreleased; first in the next juniper-service-core release, 0.8.0.
  - `docs/REFERENCE.md` (0.6.67) and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` (1.0.67) describe the fixed
    behaviour and its limits. `util/ad-hoc/2026-11-11_flood4r2_n4-r2_mutation_check.py` is the mutation check
    (38 of 41 arms killed; it records the three survivors and why),
    `util/ad-hoc/2026-11-09_flood4r2_n4_probe_broadcast_drop.py` re-derives the defect on a given tree, and
    `util/ad-hoc/2026-11-11_flood4r2_n4-r2_uvicorn_probe.py` measures it under real uvicorn.
  - Details, and the other known limits, are in `juniper-service-core/CHANGELOG.md` (Changed and Fixed).
- **`juniper-service-core`: a start sent while a stopped run's `fit` is still running is refused, so that
  `fit` sees its stop** (the stop-then-start race; §8, ruling 11 of
  `notes/JUNIPER_2026-11-06_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-4-DISPOSITION.md`, "Fix all four now", which names
  the defect and no mechanism). The owner's ruling of 2026-11-12 accepts the refusal (that record's next
  update adds it to its §8). A stop is seen at `fit`'s next event, and `start_training` cleared it, so a
  start sent before then cancelled the stop: the stopped run's `fit` ran on beside the new run, on the same
  model, its events landed in the new run's monitor, and the pause releases juniper-ml#2531 added woke it if
  it was waiting at the shared pause gate, after which a start was accepted beside it. juniper-ml#2531 fenced
  only the settle. `start_training` now refuses (HTTP 409,
  `Training cannot be started: The stopped run's fit is still running (a stop takes effect at its next event)`)
  while the previous training thread is alive with the stop pending, before it touches anything (over HTTP the
  route has already merged the request's `params` and `epochs` into the parameter store); the stop stays set,
  that `fit` unwinds at its next event, and the start is accepted once its thread has ended. Every release that
  ships the manager, 0.2.0 through 0.7.2, accepts that start.
  - The cost: a `fit` that does not end at its next event (it emits none, it hangs, or its model catches the
    interrupt and carries on) holds every start back until it returns or raises; a reset does not unblock it,
    and the status reads `STOPPED` meanwhile. Not covered: a `fit` driven by a direct `run()`, and a run that
    a leftover replay session's `stop` reset. Known and not fixed: after a stop, a snapshot load is still
    accepted while the stopped `fit` runs, and that `fit`'s thread then settles over the loaded state.
  - Pinned by `juniper-service-core/tests/test_lifecycle_stop_then_start.py` (13 tests; 11 fail without the
    refusal, 2 are controls). Five tests of `test_lifecycle_paused_fit_return.py` now clear the stop before
    their start, rebuilding the interleaving the refusal prevents, and still pin the ownership guard.
    `util/ad-hoc/2026-11-09_flood4r2_n2_mutation_check.py` runs twelve mutants of `manager.py`, each killed;
    `util/ad-hoc/2026-11-09_flood4r2_n2_race_probe.py` reproduces the race on a tree without the fix,
    `util/ad-hoc/2026-11-09_flood4r2_n2_release_census.py` reads every release tag's `start_training`, and
    `util/ad-hoc/2026-11-11_flood4r2_n2-r2_inactive_while_fit_runs_probe.py` shows the cost and what the
    check does not cover.
  - `docs/REFERENCE.md` (0.6.69) and `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md` (1.0.68) describe the refusal
    and its cost, and keep the overlap for juniper-service-core 0.7.2 and earlier, which still have it.
  - Details are in `juniper-service-core/CHANGELOG.md`; unreleased, first in the next juniper-service-core
    release, 0.8.0.
- **The orphan reaper protected the isolated stack only when its own `TMPDIR` matched the stack's.**
  `util/reap_pytest_orphans.bash` derived the stack's protected run dir from `${TMPDIR:-/tmp}`, so a stack launched under
  one `TMPDIR` and reaped under another had no pid-file protection, and every session sets `TMPDIR` now. It protects the
  FIXED default (`util/juniper_repo_tmp.bash`), resolved after the arguments are parsed, plus, read-only, the legacy
  `/tmp/juniper-e2e` and `${TMPDIR}/juniper-e2e` that older checkouts' stacks may still use. It exits 1, reaping nothing,
  when it cannot resolve the default. `tests/test_reap_pytest_orphans.py` gains 8 tests and redirects the legacy roots.

---

## References

- [CHANGELOG.md](https://github.com/pcalnon/juniper-ml/blob/v0.11.5/CHANGELOG.md)
- Archive target: `notes/releases/RELEASE_NOTES_v0.11.5.md`
