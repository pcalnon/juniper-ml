# Handoff: Y2 wave 2 + the 09-08 addendum, round 15 validated; its fix pass, round 16, then open and merge

- **Date**: 2026-09-24. Written by session `idempotent-jumping-sparkle` (the canopy arc's handoffs call it "peer session `canopy`"), after a context compaction. This is a mid-work handoff, not the arc's closing one.
- **Start the new session in the juniper-ml worktree** `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/idempotent-jumping-sparkle`. The session tools hard-code it.
- **Merge approval** (user, this arc): ONLY this session's four PRs (2b, 2a, 2c, addendum), plus the closing PR. No deploys, images, PyPI or GitHub Releases. The juniper-recurrence release is owner-gated. Never merge other sessions' PRs.

## Goal statement

Continue the user's request, verbatim: "evaluate the current state of the juniper project with respect to the following handoff prompt: juniper-ml/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-08_canopy-selection-n5-shipped-staging-is-canopy-only.md determine if any outstanding work remains update the handoff document accordingly begin performing the outstanding tasks validation by consensus should be performed where appropriate merge approval granted". It was followed by "continue as planned" several times.

Short names:
- `S` = `reports/2026-09-23_y2-wave2-consensus/session-state/` in the juniper-ml worktree. It is the persistent copy of the old scratchpad (`/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/798c2868-351c-4d37-9737-a13a7c2c41bc/scratchpad/`, tmpfs) and has the same layout, so pass it as the freeze tool's `--scratch`.
- `…PERSISTENCE-DESIGN.md` = `notes/JUNIPER_2026-09-16_JUNIPER-RECURRENCE_MODEL-PERSISTENCE-DESIGN.md`; "wave N" is its §11.4 step N.
- `…queue-drained.md` = `HANDOFF_2026-09-23_canopy-selection-queue-drained-mirror-shipped-a-n2-run-owner-rulings-open.md` (juniper-ml#2058), the arc's **live work list**. It carries this session's claims on Y2 waves 2/3 and X10 forward to 2026-09-29T00:00Z.

**Completed:**
- **Four PRs are prepared, unopened, in three worktrees:**
  - **2b**, juniper-deploy: bind-mount the LMU snapshot root, with a preflight on every bring-up path.
  - **2a**, juniper-recurrence: track `recurrence-snapshots/.gitkeep`, and correct #172's unreleased claims.
  - **2c**, juniper-ml: both launchers declare the root; a shared static tripwire, `tests/snapshot_root_tripwire.py`; two mutation harnesses.
  - **The addendum**, juniper-ml: status addendum v13 spliced into the 09-08 handoff, with the probe, splice and extract tools.
- **Their bodies, commit bodies and titles** are frozen in `S/main/` (`pr_*.md`, `commit_*.md`, `titles.json`). `S/main/PLAN.md` v5 is the open-and-merge plan.
- **Fifteen rounds of multi-agent adversarial validation.** Round 15 is frozen at `S/r15/` (140 files; `SHA256SUMS` digest `66742624b1533cd11506c7597af458c27abd3aeb6392f1439f49794bfa4a3171`). Its four reports are `S/r15_reports/R15{A,B,C,D}.md`. Earlier reports are in `S/r14_reports/` and `S/r13_reports/`, and so on; rounds 1–4 are in `S/archive_early/`.
- **Evidence at the round-15 freeze:**
  - launcher suites: 193 OK;
  - launcher harness: 103/103;
  - fixture-only check: 33 of 37 fired sweeps caught without the tripwire;
  - deploy preflight: 76 tests; full deploy suite: 360 passed, 42 skipped;
  - deploy harness: 111/111;
  - re-probe: 46/46 at the pins, and exactly the five documented BROKEN rows at `main`.
- **juniper-ml#2061** moved both launcher suites on `main`. It was merged three-way into 2c, and the freeze accepted it through `--merged 2c_ml.diff`, a proven no-op re-merge.
- **Issues** juniper-recurrence#183 (anchor `snapshots_dir`'s default) and #184 (refuse `service.snapshots_dir` in a YAML) are filed. #184's body was PATCHed 2026-09-24T03:36Z.

**Remaining:**
1. **The round-15 fix pass**, below. Round 15 found three MAJORs, ten MINORs and about twenty NITs.
2. **Round 16.**
   - Re-freeze: `python3 util/ad-hoc/2026-09-23_freeze_round.py --scratch S --round 16 --prior r15 --addendum addendum_v14.md --logs S/fix16/logs16 --reports S/r15_reports`. Add `--merged NAME` if `main` moved an uploaded path.
   - Widen the tool's `TOOLS` glob if you create `2026-09-24_*` tools.
   - Run four lanes, from `S/main/lane_common_r15.md` and `lane_R15{A..D}.md` with their contexts updated. Tell R16B that `.env.secrets.enc` is tracked in juniper-deploy, and must be deleted from every clone before a suite runs.
   - Repeat until no MAJOR and no unresolved MINOR remains, then record `APPROVED_FREEZE` in PLAN.md.
3. **Open, then merge, per PLAN.md.**
   - Open 2b, 2a and the addendum as drafts (R15D MAJOR 1).
   - Merge 2c, then 2a (then `git pull --ff-only` the shared `juniper-recurrence` checkout), then 2b, then the addendum.
   - Use `util/safe_merge.py --no-auto-fallback`, run from `origin/main`'s copies.
4. **Closing work:**
   - the closing handoff, from `S/main/handoff_v4.md`, pointed at `…queue-drained.md`;
   - the consensus archive `reports/2026-09-23_y2-wave2-consensus/`: rounds 1–16 plus a README meeting §7 of `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`;
   - a closing PR with the `util/ad-hoc/2026-09-23_*` tools;
   - worktree cleanup, only on an explicit merge signal.
5. **The final summary** names every changed file and repeats the reminder to rotate the leaked `JUNIPER_ML_PYPI` / `JUNIPER_ML_TEST_PYPI` tokens.

**Key context:**
- **Bases at the round-15 freeze:** juniper-ml `f9c81d80`, juniper-recurrence `ca9609f0`, juniper-deploy `d589dd95`.
- **Worktrees:**
  - juniper-recurrence: `/home/pcalnon/Development/python/Juniper/worktrees/juniper-recurrence--feature--y2-recurrence-snapshot-root--20260922-1512--749e7a35`;
  - juniper-deploy: `/home/pcalnon/Development/python/Juniper/worktrees/juniper-deploy--feature--y2-recurrence-snapshot-bind-mount--20260922-1520--13ee87aa`. Its `k8s/helm/juniper/values.yaml` equals deploy `main` and is not uploaded.
- **Validation loop:**
  1. Freeze.
  2. Run independent lanes with frozen-artifact checks, and archive each report verbatim at once (`util/ad-hoc/2026-09-22_extract_lane_reports.py --require-heading "## Housekeeping" S/r16_reports NAME=<transcript>`).
  3. Apply fixes.
  4. Re-freeze.
  - While a round runs, touch no uploaded file.
- **Tool claims must equal the implementation.** Rounds 14 and 15 kept finding overclaims. State an exhaustive list of recognized forms and put everything else explicitly out of scope, so later rounds score gaps as admitted.
- **Security:**
  - never print environment variable values;
  - never read or decrypt a secret; run make only with `-o prepare-secrets` and a docker shim;
  - a lane leaked the two PyPI tokens earlier; the user was told to rotate them.
- **The session guard refuses** complex bash that names git, uses computed arguments, or embeds git words in a heredoc. Use Edit/Write, plain commands, and scripts kept under `util/ad-hoc/`.

## The round-15 fix list

**2c, from `S/r15_reports/R15A.md` (0 MAJOR):**
- **m1, the tripwire.**
  - Extend it: quoted `$(…)` values; one-line arrays; `mapfile`/`readarray` options that take arguments; `printf -v`; `${x:=…}`; `while read … done < <(find ROOT)` loops (track loop frames); joins past comment and blank lines; `|&`; odd trailing backslashes; `$'…'`; `${…}` and multi-line quotes in comment stripping; `: >` after `{`, `if` and `!`; `${X:-rm}`; rm-named variables; a bare `>` into a root; `rsync --delete`; `touch -d/-t/-r`; snapshot-name globs.
  - Then state its recognized forms exhaustively, in its docstring and in `pr_wave2c_ml.md`.
  - Add each form to the suites' planted-spelling lists, and E1–E6 to the harness.
- **m2, the fixtures.**
  - Plant a 40-day-old snapshot, a 3 MiB sparse one, a backdated isolated root and a dead-pid pidfile in both `--status` tests.
  - Check the mtimes of the dated files.
  - List the classes that remain in the body: world-writable, "no snapshot newer than a week", run-dir age after a write, the number of runs, routes at `--up`, and `--dry-run`-only sweeps.
- **n1–n6:**
  - the body still says "83 of 83" once (n1);
  - run the pinned black on the harness (n2);
  - the history claims are off: "nine", not "eight", and 2 of the 19 spellings were seen by round 14 (n3);
  - `~root/…` goes through the override (n4);
  - the harness should name `(module.Class.method)` (n5);
  - fix the false positives: narrow the isolated stack's `SNAPSHOTS?_DIR` to the service variables, and use `[*/]snapshots(?![\w-])` in the experiment stack (n6).

**2b, from `S/r15_reports/R15B.md` (0 MAJOR).** R15B validated its fixes on patched copies (`S/r15b/fix_matrix.py`).
- **m1:** add `"--workdir"` to `_COMPOSE_VALUE_OPTIONS`.
- **m2:** add `cd "$SCRIPT_DIR/.."` in both bring-up scripts; record and compare `os.getcwd()` in the shim; correct the texts that claim the render reads what the bring-up reads.
- **m3:** fail if a process still carries the run's `SHIM_LOG` after make returns; name `systemd-run` and `at` as limits.
- **m4:** `commit_2b_deploy.md` should say Docker refuses a missing recurrence root only, and name the six targets (`make restart` has no preflight).
- **n1–n6:**
  - the `make -n` texts (n1);
  - exactly one snapshot render per target (n2);
  - the shim's `DOCKER_HOST` should point at a nonexistent socket (n3);
  - untested exits X25–X27, and the body's claim that every row "really does something when run behind a recording shim", which row [108] contradicts (n4);
  - name the gated starts, `.env` and the secrets file (n5);
  - the harness should flush its output and delete its tree copies (n6).
- Add harness rows for X10, X18–X21 and the gated starts.

**The addendum, from `S/r15_reports/R15C.md`:**
- **M1:** re-point the live work list to `…queue-drained.md`, in v13 lines 7, 9, 39–40 and 155, the merge-approval sentence, and X11, which is `…queue-drained.md`'s owner ruling 2. Also:
  - row 1: §12.4's A-N2 loop ran; 7 of 8 seeds pass, and `equities`' Start is refused;
  - "Since the pins" bullets for canopy#674 (19:47:32Z), canopy#675 (20:06Z) and juniper-ml#2058 (21:53:07Z);
  - raise the splice tool's `SINCE_NOW_FLOOR` to the latest merge named;
  - add a PLAN step that lists the canopy-selection handoffs on `main` before opening.
- **M2:** canopy#674 extended the `nn_model` mirror to the live swap and the restart modal; canopy#368 is still OPEN.
- **m1, probe 2.5.0.**
  - A statement that contains a call or `:=` is code.
  - For G7, fix or list as gaps: `ui`-lane tests, `slow` / `requires_*` marks, unittest naming, nested classes, a parametrize `pytestmark`, and helper or `pytest.raises` assertions.
  - Pin the fixed cases in `util/ad-hoc/2026-09-23_check_probe_helpers.py`.
- **m2:** use `ls-tree -z`; honour `route`'s positional methods.
- **NITs:**
  - the probe still misreads an annotated `router: APIRouter = …`, `HTTPMethod.GET.value`, and routes that only share a prefix (`/api/selection/history`, `/v2/api/selection`, `/api/selection.json`);
  - the G7 path still crashes on a latin-1 test file and on a syntax error;
  - the splice tool's VALIDATION_LINE claims and its time bounds;
  - the extractor should warn on id-less split records;
  - v13 line 178 still says "CURRENT tags".

**Machinery, from `S/r15_reports/R15D.md`:**
- **MAJOR 1:** use drafts; `gh pr view` all four PRs before each merge; run the post-merge checks and blob-compare the squash commit at once if one merged out of order.
- **MINOR 1:** `--merged` should compare a CHANGELOG as a multiset of lines.
- **MINOR 2:**
  - comment the splice tool's seven `except Refused: pass` handlers (CodeQL "Empty except"; resolving review threads is required);
  - add "a review finding that needs code" to the delta route;
  - re-tie the head's blobs before each merge, and compare the squash commit's blobs after it.
- **NITs:**
  - write `.base` only after a verified open (NIT 1);
  - reuse the splice tool's placeholder census, and cross-check fill numbers against the record directory (NIT 2);
  - give post-merge follow-ups a route (NIT 3);
  - #184 must add the addendum's "Wave 2 is …" sentence (NIT 4);
  - `commit_2c_ml.md` must qualify the symlink loop as uutils-only (NIT 5);
  - GitHub appends ` (#N)` and rewrites the co-author trailer, so the message is not "verbatim" (NIT 6);
  - give `APPROVED_FREEZE` a value slot that the opener reads, and have the opener compare the live tools with the freeze's (NIT 7).
- **PLAN.md:** also document `--merged` in the delta route.

## Verification (run first)

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/idempotent-jumping-sparkle
git status --short | head -40            # the state below
S=reports/2026-09-23_y2-wave2-consensus/session-state
(cd $S/r15 && sha256sum -c --quiet SHA256SUMS && sha256sum SHA256SUMS)   # digest 66742624…4a3171
env -u JUNIPER_E2E_RECURRENCE_SNAPSHOT_DIR -u JUNIPER_RECURRENCE_SNAPSHOTS_DIR python3 -m unittest tests.test_isolated_stack_script tests.test_experiment_stack_script   # 193 OK
python3 util/ad-hoc/2026-09-23_placeholder_census.py        # 2c 6/4, 2a 4/0, 2b 0/0, addendum 3 (self-test)
python3 util/ad-hoc/2026-09-23_check_open_pinned_pr.py $S/r15   # bad=[] (live worktrees tie to r15)
gh api repos/pcalnon/juniper-ml/commits/main --jq .sha      # f9c81d80… at the freeze; if moved, check uploaded paths
gh issue view 184 --repo pcalnon/juniper-recurrence --json state,updatedAt
```

## Git state at handoff

- **juniper-ml worktree:** branch `docs/canopy-selection-0908-handoff-status-2026-09-22` at `5ea8e273`, which is older than `main`. Nothing is committed or staged; the working tree carries both juniper-ml PRs, on disjoint paths.
  - Modified: the 2c files (`notes/…PERSISTENCE-DESIGN.md`, both launchers, both launcher suites) and the addendum's handoff.
  - Intent-to-add: `tests/snapshot_root_tripwire.py` and the four `util/ad-hoc/2026-09-22_*` tools.
  - Untracked:
    - `tests/process_cleanup.py`: `main`'s copy, needed locally, in no upload set;
    - the `util/ad-hoc/2026-09-23_*` tools;
    - `reports/2026-09-23_y2-wave2-consensus/`: session state, not yet curated for commit;
    - this file.
- **juniper-recurrence and juniper-deploy worktrees:** uncommitted 2a and 2b. No PR is open for any of the four.
