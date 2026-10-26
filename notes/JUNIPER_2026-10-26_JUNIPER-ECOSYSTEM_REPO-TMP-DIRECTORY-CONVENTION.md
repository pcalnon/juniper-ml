# Repo `tmp/` Directory Convention -- never `/tmp`

**Project**: Juniper (ecosystem-wide)
**Owner**: Paul Calnon
**Status**: In force since 2026-10-26 (owner directive)
**Date**: 2026-10-26
**Canonical copy**: this file, in juniper-ml. Each repo's `AGENTS.md` carries the short form under
"Temporary files: `tmp/`, never `/tmp` (mandatory)".

---

## 1. The rule, in the owner's words

> Every repo directory should have a juniper-**/tmp/ subdirectory (that is git ignored). All temp files should be
> written to that, repo-specific, directory. Absolutely NO files should ever be written to the /tmp directory. This
> is a key requirement of the Juniper project harness. This needs to be standard practice across all sessions, work
> arcs, repos, and development environments.

It covers every script, test, tool, service, session and agent, and `/var/tmp` as well as `/tmp`. Two things are
out of scope (section 5): GitHub-hosted CI runners and a container's own `/tmp`.

## 2. The incident

`util/isolated_stack.bash` defaulted its run directory to `${TMPDIR:-/tmp}/juniper-e2e`. That directory held the
stack's pid files and the juniper-data service's venv. In the week to 2026-10-26 `systemd-tmpfiles-clean` emptied it
three times, deleting every pid file and the venv while the services were running.

The pid files were the orphan reaper's protection. `util/reap_pytest_orphans.bash` treats a process reparented to
`systemd --user` as an orphan unless a run-dir `*.pid` names it or its command line names a run root. With the pid
files gone, seven live E2E servers matched the orphan predicate: the trio on ports 8101, 8202 and 8051, and the canopy
verify legs on 8052, 8053, 8058 and 8059. A reaper run without `--dry-run` would have killed all seven.

On 2026-10-26 `util/ad-hoc/2026-10-26_guard_live_e2e_servers.py` wrote guard pid files for them under
`~/.local/state/juniper-experiments/e2e-trio-2026-09-22/` and `~/.local/state/juniper-experiments/e2e-legs-2026-10-10/`.
The reaper reads every `*.pid` under that experiment root (depth 3) whatever `TMPDIR` is, and nothing ages it. The
script writes a guard only when the listener's cwd and interpreter are the ones the server was launched with.

A second defect sat underneath. The reaper's own default for the protected run dir was ALSO `${TMPDIR:-/tmp}/juniper-e2e`,
computed from the REAPER's `TMPDIR`. A stack launched by a session with one `TMPDIR` and reaped by a session with
another was not protected at all. Once every session sets `TMPDIR` (section 4.2), that is the normal case. A
protection keyed on `TMPDIR` is no protection.

## 3. Facts measured on the Linux host (2026-10-26)

- `/tmp` is a tmpfs (`findmnt /tmp`), so a reboot erases it.
- `systemd-tmpfiles-clean.timer` runs daily. `/usr/lib/tmpfiles.d/tmp.conf` reads `q /tmp 1777 root root 10d`
  (lowercase `q`): any file untouched for ten days is deleted, whether or not a process still uses it. Directories
  are kept, which is why a ten-day-old venv survives as a skeleton of empty directories (the `data_up` comment in
  `util/isolated_stack.bash` records the 2026-09-22 instance).
- macOS ages `/tmp` too.
- Every `juniper-*` repo on the host has an empty `tmp/` at its root: the owner made them on 2026-10-05, and
  juniper-slacker's on 2026-10-26. On 2026-10-26 `/tmp/` was added to every repo's `.git/info/exclude`. That file
  is LOCAL ONLY (shared by a repo's worktrees, absent from every other clone, host and CI checkout), so each repo
  also commits a root-anchored `/tmp/` line to `.gitignore`.
- Claude Code 2.1.310 puts its per-uid temp root `claude-<uid>/` (scratchpad, task output) under
  `CLAUDE_CODE_TMPDIR`, else `CLAUDE_TMPDIR`, else `/tmp`.
- A settings-file `env` value OVERRIDES the process environment.

## 4. The design, layer by layer

### 4.1 The directory and its ignore rule

Each repo's temp root is its own `tmp/`, ignored by a root-anchored `/tmp/` in `.gitignore`. Root-anchored, so a
nested `tmp/` package or fixture directory stays tracked; check the repo for one before adding the line.

### 4.2 `TMPDIR` for programs: the launcher and a SessionStart hook

`tempfile`, `mktemp`, pytest's `tmp_path`, node and most other programs honour `TMPDIR`. Two layers set it:

- **`scripts/wake_the_claude.bash`** (the juniper-ml launcher) exports `TMPDIR`, `TMP` and `TEMP` before it starts
  `claude`: the PRIMARY checkout's `tmp/` of the Juniper repo the session starts in, else juniper-ml's own. A repo
  outside the Juniper tree never gets a `tmp/` created in it. If no `tmp/` can be made, the launcher exits non-zero
  instead of launching, because an unset or missing `TMPDIR` makes Python fall back to `/tmp` silently.
- **A user-level SessionStart hook** (marker `juniper-repo-tmpdir` in `~/.claude/settings.json`) appends
  `export TMPDIR=... TMP=... TEMP=...` to `$CLAUDE_ENV_FILE`, which Claude Code sources before every Bash command.
  It gives the same answer as the launcher. `TMPDIR` must NOT go in the settings `env` block: that overrides the
  process environment, so every repo would get one path. The hook's command, its known answers and an idempotent
  installer are in `util/ad-hoc/2026-10-26_session_tmpdir_hook_probe.py`.
- Both layers also export **`GIT_CEILING_DIRECTORIES`** (section 4.7): the primary's `tmp/`, plus the starting
  directory's own top-level `tmp/` when that is a linked worktree under a Juniper repo (`.claude/worktrees/`) or under
  `Juniper/worktrees/`, then any inherited value. The hook writes the inherited part as a literal
  `${GIT_CEILING_DIRECTORIES:+:$GIT_CEILING_DIRECTORIES}`, which expands when the env file is sourced.

### 4.3 `CLAUDE_CODE_TMPDIR` for Claude Code itself

`~/.claude/settings.json` sets `env.CLAUDE_CODE_TMPDIR` to juniper-ml's primary `tmp/`, so the scratchpad and task
output land there. The launcher exports the same value. The two must agree, and the settings value wins anyway.

### 4.4 Fixed paths for state another process must find

Pid files, run directories and lock directories are read by OTHER processes (the reaper, a teardown, a second
launcher), so their location must not depend on the reader's `TMPDIR`. They live at a fixed path under the primary
checkout's `tmp/`, or under `~/.local/state/`:

- `util/juniper_repo_tmp.bash` prints the primary checkout's `tmp/` for a directory, creating it, and exits 1 outside
  any checkout. Sourced, it defines `juniper_repo_primary` and `juniper_repo_tmp`.
- `util/isolated_stack.bash` defaults its run dir to the fixed `tmp/juniper-e2e` of the juniper-ml primary checkout.
- `util/reap_pytest_orphans.bash` protects that same fixed path. It also protects, read-only, the legacy run dirs
  older checkouts defaulted to (`/tmp/juniper-e2e` and `${TMPDIR}/juniper-e2e`): over-protection is its documented
  safe direction. It exits 1, reaping nothing, when it cannot resolve the default.
- `util/experiment_stack.bash` keeps its lock root in `XDG_RUNTIME_DIR`, and without one falls back to juniper-ml's
  primary `tmp/juniper-experiments`, which every worktree shares, so the locks still serialise launchers.
- `util/ad-hoc/2026-09-04_canopy_verify_instance.bash` defaults its run dir to the isolated stack's.
- `util/host_state_probe.bash` and `util/headless_signing_preflight.bash` make their per-run scratch directory under
  `TMPDIR`, else the checkout's `tmp/`. They derive it from their own path because neither may run `git` for it.
  `util/ad-hoc/watch_fable5_availability.bash` does the same for its probe directory.

### 4.5 Two `tmp/` directories per repo

- `TMPDIR` (programs) is the PRIMARY checkout's `tmp/`, which outlives any worktree.
- Claude Code's worktree isolation REFUSES Write and Edit tool calls into a shared primary checkout (Bash writes are
  not refused). So a file a worktree-isolated session or agent writes itself with Write or Edit goes in ITS
  worktree's `tmp/`, which the same `/tmp/` rule ignores. A sibling repo's file goes in that repo's `tmp/` through Bash.

### 4.6 Gate G-TMP

`util/tmp_path_literal_check.py` keeps a new literal from landing. It mirrors gate G-PATH
(`util/home_path_literal_check.py`): the same CLI, exit codes, baseline schema and `--update-baseline` / `--dry-run`.
Its scope is every tracked `.bash`/`.sh`/`.py`/`.yml`/`.yaml`/`.toml`/`.service`/`.timer` file under `util/`,
`scripts/`, `tests/`, `conf/`, `.claude/` and the six sub-packages; `.github/` is excluded (section 5). A file may
hold no more literal lines than `conf/tmp_path_literal_baseline.json` allows it, and a line carrying
`tmp-path-literal: allow` is not counted. The matcher is:

```text
(?<![\w.~$})\]/])/(?:var/|private/)?tmp(?![\w-])
```

It matches an absolute path to the temp directory, in its Linux, `var/tmp` and macOS `private/tmp` forms, however
the path starts (a quote, a space, `=`, `:-`). It does not match a repo's own `$REPO/tmp`, `${ROOT}/tmp`, `./tmp`
or `~/tmp`, a URL path, or a longer name such as `tmpfs`, `tmp_dir` or `tmp-foo`. It runs as the `tmp-path-literal`
pre-commit hook and as a whole-scope step in ci.yml's Pre-commit job. When it landed the baseline held 314 files and
452 lines; 289 of the files are under `util/ad-hoc/`, 260 of them dated records. Tests: `tests/test_tmp_path_literal_check.py`.

### 4.7 Side effects of a `TMPDIR` inside a checkout

Moving `TMPDIR` from the system temp dir into a repo's `tmp/` changes what tools see around a temp file. Each repo
needs the four checks below; CI is unaffected, because a runner's `TMPDIR` is its own temp dir and a fresh checkout's
`tmp/` is empty.

1. **git discovery.** git run anywhere under the repo's `tmp/` walks up to the ENCLOSING checkout, so a test's
   "not a git repository" fixture under `tmp_path` stops being one. Measured: without a ceiling
   `git -C <worktree>/tmp/ceiling-test/a/b rev-parse --show-toplevel` printed the worktree; with
   `GIT_CEILING_DIRECTORIES=<worktree>/tmp/ceiling-test` it said "not a git repository" (exit 128); at the worktree
   root git is unaffected. The launcher and the hook export the ceiling for sessions; a test that scrubs `GIT_*` or
   needs its own fixture outside every repo sets it in its subprocess env. The ceiling must be a PROPER ancestor of
   the directory git starts in: git never treats its starting directory as a ceiling. In juniper-ml this fixed five
   tests in `tests/test_configure_commit_signing.py`, `tests/test_predict_merge.py` and `tests/test_prompt_discovery.py`
   (juniper-deploy hit two of the same kind).
2. **Tree walkers.** A tool that walks the directory tree, rather than git's tracked files, ignores `.gitignore` and
   `info/exclude`, so it scans `tmp/`. `juniper-check-doc-links` is one: with a lane's scratch under
   `<worktree>/tmp/` it scanned 1,832 markdown files and failed on 55 broken links, every one inside `tmp/`. juniper-ml
   passes `--exclude tmp` in its pre-commit hook, its CI invocations and the `AGENTS.md` commands. A default exclude in
   juniper-doc-tools needs a package release (section 10).
3. **pytest recursion.** pytest's default `norecursedirs` does not list `tmp`, so a repo without `testpaths` collects
   whatever test files a lane or pytester leaves under `tmp/`. juniper-ml sets `testpaths = ["tests"]` at its root and in
   all six sub-packages, so a bare `pytest` never reaches `tmp/`; an explicit `pytest .` still would.
4. **Upward walks for a marker.** Code that walks up from a path looking for a marker finds the REAL one from inside
   `tmp/`: the home directory, the Juniper ecosystem root, a `.github/workflows` directory. Four juniper-ml suites fail
   locally for that reason and pass in CI: `tests/test_a0_restore_scripts.py` (a fixture dir is now inside the backup
   Source, `$HOME`), `tests/test_e2e_f037_render_census.py` and `tests/test_replay_redrive_stack_refusal.py` (they find
   the real ecosystem root), and `tests/test_workflow_script_paths.py` (it finds the primary's `.github/workflows`). A
   git ceiling cannot bound these walks; each needs its code under test to accept a bound (section 10).

## 5. Out of scope

- **GitHub-hosted CI runners.** No workflow in any Juniper repo runs on a self-hosted runner, so a workflow's `/tmp`
  is GitHub's ephemeral runner disk. `.github/` is outside G-TMP's scope.
- **A container's own `/tmp`**: a Kubernetes `emptyDir` mount, a Dockerfile build step.

## 6. Retention

Nothing ages `tmp/`. That is the point: a file there stays until someone deletes it. Prune by hand, and only after
checking that no live process holds a file in it (`fuser -v`, `lsof +D`, the reaper's `--dry-run` view, the pid files
under the run dirs). Never prune the isolated stack's `tmp/juniper-e2e` while a stack runs from it.

## 7. Applying the convention on another host

1. Create each repo's `tmp/` (an ignored, empty directory).
2. Install the SessionStart hook and `CLAUDE_CODE_TMPDIR`:
   `python3 util/ad-hoc/2026-10-26_session_tmpdir_hook_probe.py --install` (from juniper-ml). It runs the known
   answers first, backs up `~/.claude/settings.json` once, and is idempotent. On turing this is the whole step.
3. Start sessions through `scripts/wake_the_claude.bash`, or rely on the hook alone.

## 8. What this supersedes

Until 2026-10-26 juniper-ml's `AGENTS.md` § Script placement banned `/tmp/` only as the home of a script's SOURCE
and kept it as a scratch workspace: "`/tmp/` remains acceptable as a scratch *workspace* for intermediate artifacts
that the script itself creates and reads (e.g., `uv pip compile -o /tmp/lock && mv /tmp/lock requirements.lock`) --
the prohibition is on script *source files*, not on transient data." That exception is gone: transient data goes to
`tmp/` too.

## 9. Per-repo status

One row per repo, recorded 2026-10-26. A PR column reads "pending" until that lane's PR is open. The scope column
quotes each PR's own title; read the PR for its file list.

| Repo | Lane | PR (state on 2026-10-26) | Scope |
|------|------|--------------------------|-------|
| juniper-ml | A | the PR that added this file | launcher `TMPDIR` / `CLAUDE_CODE_TMPDIR` / `GIT_CEILING_DIRECTORIES`; fixed run dir, reaper roots, lock-root fallback, verify leg, three scratch dirs; gate G-TMP; `.gitignore`, `AGENTS.md`, this file |
| juniper-canopy | C | juniper-canopy#774 (open) | "write temp files to the repo's tmp/, never /tmp (find_stalling_tests, docs, AGENTS.md)" |
| juniper-deploy | C | juniper-deploy#263 (open) | "scripts fall back to the repo's tmp/, never /tmp; tmp/ rule in AGENTS.md"; it also fixed 7 `mktemp "${TMPDIR:-/tmp}/..."` scripts |
| juniper-k8s | C | juniper-k8s#14 (open; the repo has no CI) | "temp files go in the repo's tmp/, never /tmp (AGENTS.md, ignore line)" |
| juniper-recurrence | C | juniper-recurrence#225 (open) | "temp files go in the repo's tmp/, never /tmp (AGENTS.md, examples, ignore line)" |
| juniper-slacker | C | juniper-slacker#1 (open; the repo has no CI) | "!file's temp root is the repo's own tmp/, not /tmp" |
| juniper-cascor | B | pending | pending |
| juniper-cascor-client | B | pending | pending |
| juniper-cascor-worker | B | pending | pending |
| juniper-data | B | pending | pending |
| juniper-data-client | B | pending | pending |

## 10. Left in juniper-ml, deliberately

- **Records.** Dated `util/ad-hoc/` scripts, `notes/` history, `prompts/` and `reports/`: they record what happened.
  The dated `util/ad-hoc/` scripts are baselined in G-TMP.
- **Strings that are never created**: mocked paths, assertion strings, the malicious-command fixtures in the guard
  tests, path fields inside fake backup manifests, dry-run arguments.
- **The backup lane** (`util/juniper-backup.bash`, the Duplicati scripts and units, their tests and docs): another
  arc owns them, and Tier 1 is down by owner order. Its `/tmp` mentions are comments and refusal fixtures, and its
  `REFERENCE.md` watchdog example (`--state-dir /tmp/wd`) is listed for that arc.
- **The undated canopy E2E drivers** in `util/ad-hoc/` (`e2e_*.py`, `e2e_*.bash`) still default to the old run dir.
  They operate the LIVE stack, which was launched under the old default, so changing their defaults now would point
  them away from it. Move them with the next relaunch of the stack.
- **The four marker-walk suites** of section 4.7 item 4 fail on a host whose `TMPDIR` is inside the Juniper tree and
  pass in CI. Each needs its code under test to accept a bound (an env var or a parameter naming the root), which
  belongs to the arc that owns the tool.
- **juniper-doc-tools** has no default exclude for `tmp`. Adding one changes a published package, so it waits for
  its own PR and release; until then every caller passes `--exclude tmp`.
- **The installed SessionStart hook.** `~/.claude/settings.json` on the Linux host still carries the hook without the
  ceiling. Updating it is a configuration change the owner makes:
  `python3 util/ad-hoc/2026-10-26_session_tmpdir_hook_probe.py --install`, which runs the known answers first.
