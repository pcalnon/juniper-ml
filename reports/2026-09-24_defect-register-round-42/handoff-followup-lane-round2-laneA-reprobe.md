<!-- Archived verbatim 2026-09-24 from subagent a105b96f1f3471bb3 of session bc31e993 (final message). -->

I found 1 HIGH, 3 MEDIUM, 4 LOW and 2 NIT problems in the revised `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`. The rest of its new and changed claims hold against GitHub, git and the files. Most importantly, F5 would send a successor to open a canopy PR whose test change does nothing. I changed nothing in any repo, and my scratch directory `hvD/` is deleted (/tmp inodes at 82%).

## Findings

**HIGH-1. F5's canopy site is not an `_ENCODING_PROBES` list, and the pair kills nothing there.**
- **Text:** "every `_ENCODING_PROBES`: … canopy `src/tests/unit/test_security.py:172`", and "one new canopy PR for F5 and the NIT".
- **What is true:**
  - canopy's file has no `_ENCODING_PROBES` and no "total and injective" comment.
  - Line 172 is `NON_ASCII`, a list of presented values checked only against the fixed key `APIKeyAuth(["key1"])`.
  - `bytes-compare-ml2086-data440-cascor689-validation.md` (lines 60-64) scopes F5 to "all three": service-core, data and cascor.
- **Evidence:** I loaded canopy's real `security.py` at `dc5ea02e`, added the pair to `NON_ASCII`, and patched `_compare_bytes` to UTF-16-LE:
  `UTF-16-LE mutant: NON_ASCII(+pair) test passes=True; cross-product (configured U+1F511, presented pair) passes=False`
- **It has spread:** this session's 23:35:30Z message told the register lane that "Every copy's _ENCODING_PROBES already holds U+1F511", listing "canopy test_security.py:172".
- **Corrected text:** "F5: service-core `tests/test_security.py:101` (main), data `test_security.py:34` (#440 head), cascor `test_api_security.py:31` (#689 head). canopy has no `_ENCODING_PROBES`: its `NON_ASCII` (`:172`) is checked against a fixed `"key1"`, so the pair there is inert. To cover canopy, add a configured-by-presented case (configure U+1F511, present the pair, and the reverse). Tell the register lane its 23:35Z F5 list wrongly includes canopy."

**MEDIUM-1. `4caf9389` WAS pushed.**
- **Text:** "The local `4caf9389` is unsigned and was never pushed".
- **What is true:** the remote juniper-canopy has branches `pr-63` and `pr-683`, both at `4caf9389`.
  - The branch API reports them unprotected, with the commit unverified ("unsigned") and no PR.
  - The canopy reflog records "update by push" at 22:55:30Z and 22:55:40Z.
  - The local branch's upstream is `refs/heads/pr-683`, so a plain `git push` from that worktree lands there.
  - No Claude transcript contains the push. The branch config carries a `vscode-merge-base` key, so VS Code is likely (unproven).
- **Corrected text:** "…unsigned, and pushed at 22:55Z to stray remote branches `pr-63` and `pr-683` (no PR). Surface them to the owner; do not delete them unasked."

**MEDIUM-2. `095a2108` did not edit `main`'s copy.**
- **Text:** "`main`'s copy of `…cascor678_followup_mutation_check.py` was later edited by `095a2108`", and the trap "later commits edit merged files (`095a2108`)".
- **What is true:** `095a2108` (19:39:42Z) is one of #2077's own six branch commits. #2077 was squash-merged as `6c23fdde` at 19:52:49Z.
  - `git merge-base --is-ancestor 095a2108 origin/main` exits 1.
  - The file's only commit on `main` is `6c23fdde`.
  - `main`'s copy is byte-identical to `095a2108`'s.
- **Corrected text:** "#2077's branch picked up the sweeper's `095a2108` before the squash, so `main` holds the edited file." For the trap: "The sweeper adds commits to open PRs (#2077 got `095a2108`, canopy#685 got two)."

**MEDIUM-3. `24103c23` is signed.**
- **Text:** "The local `24103c23` is unsigned", and "in three worktrees HEAD is an unsigned local copy".
- **What is true:** `git log --show-signature` gives "Good signature from "Paul Calnon (…Yubikey…)" [ultimate]". Only data's `5bd5eec5` and canopy's `4caf9389` are unsigned (`%G?` = N).
- **Impact:** none on action. In all three worktrees HEAD is still not the PR head.
- **Corrected text:** "…HEAD is a local copy, not the PR head."

**LOW-1. F9 is allocated to the wrong PRs.**
- **Text:** "fixups on data#440 for F3, F5 and F9", and "one new juniper-ml PR for F2, F6, F10 and service-core's F3 and F5".
- **What is true:**
  - data#440 is one commit, and no "4001", "close", "403" or WebSocket text appears in its commit body, CHANGELOG diff or PR body.
  - `juniper-service-core/CHANGELOG.md:58` on `main` says "handshake closes 4001", and so does #2086's commit body.
- **Corrected text:** move F9 to the juniper-ml PR (service-core `CHANGELOG.md:58`), and drop it from data#440.

**LOW-2. The canopy ledger timeline is off.**
- **Text:** "This lane sent them to the register lane at 20:42Z. It had said, at 20:25Z…"
- **What is true:**
  - The 20:42:33Z message carried only `:8381` and `:42`.
  - The `" The resulting dataset"` item and LOW3/LOW4 went at 19:06:26Z; LOW3/LOW4 went again at 19:48Z and 21:10Z.
  - "It" is the register lane. Its 20:25:20Z message says "I'll forward them to the canopy e2e session", but the sentence reads as this lane.
- **Corrected text:** "Sent at 19:06Z (the `:8410` item, LOW3, LOW4) and 20:42Z (`:8381`, `:42`). The register lane said at 20:25Z it would forward them."

**LOW-3. Two listed sandbox refusals did not reproduce, and one real refusal is missing.**
- `git -C util/ad-hoc log -1` ran and printed `5af9d722`. A script run from `util/ad-hoc/` also ran.
- What IS refused is `git -C` (or `cd … &&` git) into the shared juniper-ml checkout, even with an absolute path. So "`git -C <owning repo> worktree remove`" fails for the juniper-ml worktree. Use `git worktree remove <path>` from your own worktree.

**LOW-4. The #690 probes cannot be re-run as the handoff implies.**
- `run_jd.bash` is cited as a lane probe at `cascor688-validation.md:89` but was not archived, because the copier takes `.py` only.
- `probe_realjd_refusals.py` needs a live juniper-data URL (`sys.argv[2]`), and `run_jd.bash` was what served one.
- Add: "the real-juniper-data probes need a juniper-data server started by hand."

**NIT-1.** "All 60 of #683's CHANGELOG lines": numstat says 61 insertions (60 non-blank plus 1 blank). All of them sit in `[Unreleased]`, at new-file lines 557-648 against `[0.8.1]` at 649.

**NIT-2. The Git-status list will be short.** The PR will also carry three round-1 reports and `2026-09-24_archive_followup_handoff_validation.py` (both 23:49Z), plus `2026-09-24_open_followup_handoff_pr.py` (23:51Z). The handoff was saved at 23:48:25Z, so it was accurate when written.

**One note on your brief:** the copier's `--lint` is not read-only. `pre-commit run --files` rewrites untracked files in place, so I did not run it and checked the files myself instead.

## Verified

- **canopy#685:** merged 23:24:14Z by pcalnon as `dc5ea02e`, from head `e70b54dc`.
  - `78c08ec3` and `e70b54dc` are authored by pcalnon and touch only the probe script (+8/−4 against `4a8af2a0`).
  - The squash tree and the head tree are both `7cc93012`.
- **canopy#683:**
  - `34e06747` is a merge whose parents are `8917fdac` and `f2147403`, and the squash tree equals it.
  - main's 12 files overlap #683's only in `CHANGELOG.md`.
  - The latest canopy release is v0.8.1 (2026-09-18).
- **Merge SHAs:** ml#2072 `ac912eba`, ml#2077 `6c23fdde`, ml#2086 `c061a99f`, cascor#688 `7f4a7213`. #2075, #2084 and #2088 are merged.
- **CI:** every push-triggered run on all six merge commits succeeded. One `repository_dispatch` CI run on `7f4a7213` started at 23:53Z, after writing, and is still in progress.
- **Sessions and pushers:**
  - `[042116]` is bc31e993 (its `ListAgents` result at 21:17Z).
  - `[24f8d8]` is `2fba4397`: its own `ListAgents` names it, and its cwd is `fizzy-hugging-dream`.
  - Both pushers are on `main`; `--expected-head` is required and takes a full 40-hex SHA.
  - `util/worktree_cleanup.bash` pushes and runs `gh pr create`.
- **F5, other parts:**
  - The three real `_ENCODING_PROBES` lines are right at the right refs, and each holds U+1F511.
  - Built with `chr()`, U+1F511 and the pair both encode to `b'=\xd8\x11\xdd'` under UTF-16-LE with `surrogatepass`, and differ under UTF-8.
  - `json.loads` of the typed pair escape yields U+1F511, which is the mechanism behind the tool-path trap.
- **F3, F4, F6, F7, F9 wording:**
  - Data's `TestAPIKeyAuth` is at `:37` (#440 head) and unmarked; `ci.yml:287`; canopy's spy test exists.
  - cascor `conftest.py:37` is `import sysconfig`.
  - F7's `:33-35` is `_sentry_init_calls`, and the symbol-loss gate scopes `src/**/*.py`.
  - `_ALLOW_RE` is MULTILINE and reads every commit in BASE..HEAD.
  - All match `bytes-compare-ml2086-data440-cascor689-validation.md` lines 42, 48, 58, 70, 76 and 88.
- **Release lines, on each `origin/main`:**
  - Locks: data `:88/:90`, cascor `:63/:65`, canopy `:79/:81`, recurrence `:70/:74`.
  - Observability caps: canopy `:109`, recurrence `:79`, client `:41/:46`.
  - Service-core caps: data `:110`, cascor `:105`, canopy `:119`, recurrence `:51`, and ml `[tools]` at `pyproject.toml:94`.
  - Versions 0.4.0 and 0.7.0, on `main` and PyPI.
- **DSN names:** all six are read by real code: cascor `main.py:183-184`, sentry-sdk `client.py:114`, data's `JUNIPER_DATA_` prefix, and canopy `settings.py:661/663`. Only `SENTRY_SDK_DSN` is exported.
- **Register IDs:** none of the three reserved IDs is on `main`; the highest are CASCOR-013 and ECO-012.
- **Branches:** `refs/pull/686/head` is `e452a660`. Both local branches exist and neither is checked out.
- **Line anchors:**
  - canopy `:8381`, `:8410`, test `:42`, `security.py:137/:300`, `csrf.py:97` and `outbound_errors.py:57-61` hold.
  - `rate_limit_enabled` defaults to False.
  - The stub comment is contradicted by `ci.yml:170`.
  - cascor `:4766` holds on `main` and `:4841` at #690's head.
- **Messages and ownership:**
  - 20:25:20Z and 20:42:33Z are real.
  - At 23:34-23:35Z the register lane reported the consolidation request and took the drift marker and C-A…D-G.
  - The traps match the predecessor handoff's lines 87-89.
- **Verification commands:**
  - GraphQL: #690, #689 and #440 are OPEN, CLEAN and unarmed; #685 is MERGED.
  - The `gh pr list` search printed `[]`. No PR exists yet, but the search does match titles.
  - Fork drift: "Ran 11 tests … OK (skipped=3)"; with the opt-in, "OK". The checkout is at `7e8c7ff9`, and the test is unchanged since.
  - `ls` lists six directories, and `df -i` shows 81%.
- **Supporting files:**
  - 63 files (19, 10, 13 and 21), each byte-identical to exactly one scratch source.
  - No copies of repository code, and no secrets: only `LEAKME`-style markers and `127.0.0.1` DSNs.
  - The four README rows are correct.
- **Archivers:**
  - The round-42 archiver's `--check` prints OK for every "(final message)" file and exits 0.
  - The follow-up archiver's `--check` prints 3× "exists … left alone" and exits 0.
- **Headers:** agent a7b8f376 has 5 turn-ending reports plus one session-limit notice. The "1-4 of 5" numbering is consistent, and all 5 bodies match their messages.
- **Worktrees:** all six are clean, and the trees match as stated.

**Changed:** no repository file. Side effects: plain `git fetch` in eight sibling repos, and `refs/remotes/origin/pr685` in canopy, which I created and then deleted.
