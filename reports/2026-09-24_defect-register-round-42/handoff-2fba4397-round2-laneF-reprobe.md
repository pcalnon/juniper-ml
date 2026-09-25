<!-- Archived verbatim 2026-09-24 from subagent ad4c472203a4c4b54 of session 2fba4397 (final message). -->

VERDICT: PASS WITH CORRECTIONS

All line numbers below ("L<n>") refer to the frozen snapshot `handoff_session_r2_frozen.md` (sha256 `6822f3ff0402793e…`, verified; written at 00:28:17Z). Other documents are named by filename every time:
- the register `JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` and the primer `JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md`, both read at juniper-ml `origin/main` = `5af9d722`;
- the peer's draft `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md` (sha256 prefix `62f9b2bf`, mtime 00:21Z);
- the peer's `bytes-compare-ml2086-data440-cascor689-validation.md`;
- the predecessor `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md`.

The rewrite's facts mostly re-derive: every PR state, head, merge SHA and time; the counts; the routing names; all 13 Git-status entries; and every verification command, each matching its annotation. Six MEDIUM problems remain, and none is a wrong SHA:
- Both "verify, then file" candidates predict the wrong outcome. I measured each.
- #2089's CodeQL check failed 26 s before the freeze, and the snapshot gives no remedy.
- A round-1 correction weakened the marker plan.
- The lock list misses cascor's image lock.
- The liveness test can call a live executor dead.

## Claims table

| Claim (line) | What I ran or read | Result |
|---|---|---|
| L3, L19, L86: session names [24f8d8], [042116] (= `bc31e993`), canopy combined [577a1c], containers [2703c8]; the canopy E2E session has exited | ListAgents output in transcript `2fba4397-7d9b-4929-8ca2-375b8168e1c8.jsonl` at 19:03:13Z, 19:35:42Z, 20:42:44Z and 00:18:48Z. The peer's message at 19:06:26Z calls itself "the old defect-reg session (bc31e993)". `canopy e2e [fd9ad3]` is absent from 20:42Z on | REPRODUCED |
| L23: #2088 merged at 23:41:16Z as `5af9d722` | `gh pr view 2088`: MERGED, merge `5af9d7229505…`, commits `e2f87aae`, `990ef3f9`, `2439d049`, `1f116c38` | REPRODUCED |
| L26: harness 62/62, probe 27/27, 136 / 100 / 36, AGREE | Harness with the primer venv on `origin/main`'s primer: "62 passed". Probe: "all 27". Register tools rerun | REPRODUCED (mutation check not rerun) |
| L27: "On `main`, the probe differs in 25 cases" | Probe on current `main`'s primer: 0 differ. On the pre-merge `c061a99f` primer: "25 of 27" | PARTLY (N1) |
| L28: main verification and CodeQL passed; the waiver is honoured | Every action run on `5af9d722` succeeded. `juniper-symbol-loss-check` over `c061a99f..5af9d722` and over `5af9d722^..5af9d722` prints `waived (Allow-Symbol-Loss): const:SESSIONS` | REPRODUCED |
| L29–L30: #2089 OPEN, head `a2fa3ad8`, not armed; 129 probes; README carries the peer's four rows | `pulls/2089`: 132 files (129 probes, the copier, the opener, the README), `auto_merge` null. Commits `d8a495f7` and `a2fa3ad8`. README rows 39–42 at `a2fa3ad8` | REPRODUCED |
| L31: "CodeQL may flag the probes" | CodeQL check-run on `a2fa3ad8` completed with **failure** at 00:27:51Z: "33 new alerts including 4 high severity security vulnerabilities" | REFUTED by timing (M1) |
| L32–L33: branch at `d1c66a11…`, parent `0f0f7e0e`; #438 merged 18:52Z | `commits/d1c66a11`: verified, parent `0f0f7e0e`. #438 merged 18:52:00Z | REPRODUCED |
| L36: 5 s readiness timeout; three failures needed | `juniper-deploy` `k8s/helm/juniper/values.yaml:87-91`: `timeoutSeconds: 5`, `failureThreshold: 3` | REPRODUCED (6.6 s not re-measured) |
| L37: ruling times and answer | `owner-ruling-key-leaks-verbatim.md` lines 7, 19 and 38 | REPRODUCED |
| L40–L44: items resolved since the predecessor | `gh pr view` for ml#2081, ml#2086, canopy#683, canopy#685 and cascor#688. juniper-data run 35977786108: "Publish to PyPI" 18:35:46Z, notify-consumers job failed | REPRODUCED |
| L47–L50: executor brief; full brief is the user record at 23:48:49Z; `last_report()` | `agent-a46e715a6801b98ca.jsonl` has a user record (isMeta) at 23:48:49.313Z. `def last_report` is at `2026-09-24_archive_round42_reports.py:151` on `origin/main` | REPRODUCED |
| L49: "written in the last ~10 minutes" means alive | The executor transcript has 600 s and 580 s gaps while alive | PARTLY (M5) |
| L54: consolidation order, about 23:25Z | User records at 23:25:30.566Z and 23:25:49.935Z | REPRODUCED |
| L58: "This session had begun the consolidation" | Status at 23:41:03Z lists it as step 4. Status at 00:29:24Z: "After round 2 comes the three-way consolidation". No draft exists | REFUTED (L4) |
| L62: `990ef3f9..2439d049` never validated | `2439d049`'s parent is `990ef3f9`. The transcript's Agent launches include no lane on it | REPRODUCED |
| L68: data#440 head `0bee089e` edits `CHANGELOG.md` | `gh pr view 440` (CLEAN, not armed); `diff --stat` | REPRODUCED |
| L71: "PR CI runs only `SharedPackageGuardTest` (`ci.yml:500`)" | `ci.yml:500` runs the whole file. `ServiceForkDriftTest._require_cross_repo` skips without siblings; `GuardRegistryStructureTest` always runs | PARTLY (N2) |
| L72: the `:205-209` text, refuted by F8 | `tests/test_service_fork_drift.py:205-209` on `origin/main`; `bytes-compare-ml2086-data440-cascor689-validation.md:78-82` | REPRODUCED |
| L74–L80: candidate (a) | data `app.py:187-212` and its docstring; `f6791d6` is #281; primer 4742–4743; cascor `src/api/app.py:856`; register L1303 (APD-DATA-056). **In-process probe of the real juniper-data app returned 400** | Anchors REPRODUCED; outcome REFUTED (M4) |
| L81: candidate (b) | Primer lines 2662, 2686, 2687. In-process probe of `idempotent_jobs.py`: validation error `string_unicode`, and `store.begin` is never reached | REFUTED (M3) |
| L82: #2080's body still rejects the nit | `gh pr view 2080`: body line 69, `updatedAt` 10:18:16Z. `ml2080-round1-laneA-reprobe.md:156` holds N6 | REPRODUCED |
| L90: 5 commits behind | `rev-list --left-right --count HEAD...origin/main` → `3 5` | REPRODUCED |
| L91: the §2 status line is about L177 | Register L176 | REPRODUCED |
| L93: names of the DSN variables | Source greps in canopy, cascor and data. I read no environment | REPRODUCED |
| L101–L103: harness, venv pins, mutation-check options | argparse in both scripts. Primer venv: `pyvenv.cfg` 3.13.13; dist-info shows fastapi 0.141.1, starlette 1.6.0, pydantic 2.13.4, httpx 0.28.1, pytest 8.4.2 | REPRODUCED |
| L104: the editor refuses a rerun and line moves; census 69 / 82 | `…_round2.py:9`, `:293-294`, `:310`. Census run: "69 citation(s), 82 number(s)" | REPRODUCED |
| L105: `git log --format='%(trailers:…)' 5af9d722` "prints nothing" | Run verbatim, it prints **11** waiver lines from older commits. With `-1` it prints one empty line. `%(trailers)` shows only `Co-authored-by`. `grep -c` gives 3 | PARTLY (L1) |
| L107: `--expected-head` must be the full SHA | `util/push_signed_commit.py --help` | REPRODUCED |
| L114–L124: the 11 verification commands | Ran each as written. Every annotation matches: 13; MERGED; 136 / 100 / 36; AGREE; 39; `d1c66a11…`; 12 M files; transcript mtime current; #440, #689 and #690 open. `/tmp` is at 83% now | REPRODUCED |
| L128–L138: Git status | `git status --short`: 13 entries. The two M diffs against `origin/main` show only the stated changes. The untracked #2089 files are byte-identical to `a2fa3ad8` (132 of 132) | REPRODUCED (L6: placement) |
| L129: three unsigned scratch commits carrying #2088's content | `%G?` = N for all three. `git diff ee0b9382 5af9d722` over #2088's files is empty | REPRODUCED |
| L141–L145: four older worktrees; data worktree on the round4 branch | `ls -d`; `rev-parse --abbrev-ref HEAD` | REPRODUCED |
| L150–L152: gates | #690 OPEN at `78e99414`. Open set includes CASCOR-008/-013 and DATA-017/-029/-032/-057. Register rows L788, L800, L803 and L1636 | REPRODUCED |
| L155–L166: F2–F10 | `bytes-compare-…-validation.md` F2–F10. Service-core `tests/test_security.py:97-101`; data#440 `test_security.py:34`; cascor#689 `test_api_security.py:31`, all holding U+1F511. Canopy has only `NON_ASCII` at `:172`. `juniper-service-core/CHANGELOG.md:57-58`; `juniper-observability/CHANGELOG.md:64`; no `in_app` in `test_sentry.py`; cascor#689 AST test `:33-35` | REPRODUCED |
| L157: close condition for ECO-013 | The peer's draft, line 131, states a different one | CONFLICT (L5) |
| L167–L172: releases | Locks: data `:88`, cascor `:63`, canopy `:79` (cap at `pyproject.toml:109`), recurrence `juniper-recurrence/requirements.lock:70` (cap at `pyproject.toml:79`). cascor `app.py:335` goes through `api/observability.py:37`/`:122` to the shared `configure_sentry`. #689 changes only `main.py`. **cascor's `Dockerfile:41-42` installs `requirements-cpu.lock`, which pins 0.4.0 at `:129`.** Recurrence has no Sentry at all | PARTLY (M2, L3) |
| L175–L177: CASCOR-014 | cascor `test_cfg_03…py:25`; `main.py:210-242` runs Sentry init at module level; `conftest.py:37` is `import sysconfig` | REPRODUCED |
| L180: APD-DATA-055's lock half is fixed at `0f0f7e0e` | `storage/base.py`: `:415` defines `delete_under_lock`; `:484` (`delete_expired`) and `:657` (`batch_delete`) call it | REPRODUCED |
| L186–L195: residue and its sources | `cascor686-fixup-implementation-report.md:16`; `pending-items-snapshot-2026-09-24T1110Z.md:40`; canopy mutation script `:22` retire condition; register L1616; both canopy handoff files exist; branch `docs/canopy-e2e-handoff-2026-09-24` at `dd4413e5`, no PR, 4 F-CANOPY-06x hits | REPRODUCED |
| L200: A1's F2 and F4 are recorded nowhere | `data428-round3-laneA1-security.md:23`, `:26`, `:29`. The register has no 8192 or header-limit record | REPRODUCED |
| L201: four "turn-ending report" headers | First lines of the peer's reports | REPRODUCED |
| L205–L217: owner decisions | No AskUserQuestion after 18:30:09Z in either transcript. PyPI: observability 0.4.0, service-core 0.7.0, data 0.16.0. `pr-63` and `pr-683` both at `4caf9389` (unsigned; parent `7ab994e5`; tree `7fbccc33` = `4a8af2a0`'s); activity API shows branch creation by pcalnon at 22:55:30Z and 22:55:39Z. MEMORY.md 24,929 characters | REPRODUCED (one open decision missing: M1) |
| L219–L235: the later arc items | Open set; register L1284 (047 FIXED); `HANDOFF_2026-09-22_defect-register-round-41-…md:37` (38 `def` lines); register L1251–1257; 0 `data_quality` hits in recurrence | REPRODUCED |
| L240–L245: PR drafts | The durable copy equals `"# " + title + "\n\n" + body` byte for byte; mtime 00:27Z. The tmpfs drafts are unchanged since 20:46Z | REPRODUCED |
| L249–L277: brief summary and anchors at `d1c66a11` | Compared with the 23:48:49Z brief. Every anchor (1357-1362, 45-47, 200-202, 93-94, 1374-1375, 117-118, 546-547, 1282) holds the stated text. `[0.16.0]` is 261 lines, the same sha across `v0.16.0`, `0f0f7e0e`, `d1c66a11` and `0bee089e` | REPRODUCED |
| L281–L290: the predecessor's items | Predecessor handoff lines 21–58 | REPRODUCED |
| L295–L305: marker anchors | Service-core `:88`/`:91`, plus a `surrogatepass` comment at `:82`. canopy `:42-52` (docstring `:49`), `:137`, `:300`, `csrf.py:91`/`:97`. data#440 `:115`/`:118` (comment `:108`). cascor#689 `:84`/`:87` (comment `:78`). REFERENCE `:2977`. Register guard counts at L252, L1106, L1751. `FORCE_LOCAL` run: 11 OK | Anchors REPRODUCED; plan PARTLY (M6, L2) |
| L309–L325: Appendix F | #2088 diff; memory-file mtimes today; link at `reference_backticks_eaten_in_shell_messages.md:65` | REPRODUCED |

## Findings

### MEDIUM

**M1. #2089's CodeQL check has FAILED. That block was the owner's decision last time, and the snapshot says neither.**
- Quoted: L31 "CodeQL may flag the probes, as it did #2081's." L61 "Merge #2089 once it is green, with your own grant."
- Evidence:
  - CodeQL completed at 00:27:51Z, 26 s before the freeze: "33 new alerts including 4 high".
  - The four highs are `py/overly-permissive-file`, all in `data438-fixforward-round1-laneB/stripe_probe.py`. The rest are `file-not-closed` warnings and notes. `mergeStateStatus` is BLOCKED.
  - The predecessor handoff, In flight 2, calls #2081's identical block "the owner's decision (paths-ignore, dismissal, or a tarball)".
  - The owner cleared it by committing `73dc109c` and `f9964d78` himself, at 22:24Z and 22:31Z.
  - #2089 also carries the peer's four README rows. The peer agreed at 00:25:06Z to drop them from its own PR.
- Replacement:
  - L31: "CodeQL FAILED on `a2fa3ad8` at 00:27:51Z: 33 new alerts, 4 high (`py/overly-permissive-file` in `data438-fixforward-round1-laneB/stripe_probe.py`). The same block on #2081 was the owner's decision, and the owner cleared it by committing `73dc109c` and `f9964d78`. Surface it; do not dismiss alerts or edit the preserved probes yourself. If #2089 is closed or rebuilt, keep the peer's four README rows."
  - L61: "Merge #2089 once the owner has resolved its CodeQL block and it is green, with your own grant."
  - Appendix B: add "#2089's CodeQL alerts (as #2081's)."

**M2. The release list omits the lock that cascor's image actually installs.**
- Quoted: L168 "data `requirements.lock:88`, cascor `:63`, canopy `:79`, recurrence `:70`;"
- Evidence:
  - juniper-cascor `Dockerfile:41-42`: `COPY requirements-cpu.lock` and `pip install … -r requirements-cpu.lock`.
  - `requirements-cpu.lock:129` pins `juniper-observability==0.4.0`, and `:133` pins `juniper-service-core==0.7.0`.
  - Moving `:63` alone leaves the running cascor container on 0.4.0.
  - The peer's draft carries this lock at line 116.
- Replacement: "data `requirements.lock:88`; cascor `requirements.lock:63` **and `requirements-cpu.lock:129`, the lock its image installs (`Dockerfile:41-42`)**; canopy `requirements.lock:79`;"

**M3. Candidate 6(b) is refuted: the surrogate never reaches `store.complete`.**
- Quoted: L81 "`store.complete` (2686) stores the payload before rendering it, so every replay of that key (2662) fails the same way."
- Evidence (in-process run of the primer's `idempotent_jobs.py` with the primer venv, no port):
  - `dataset_id` holding a lone surrogate (U+D800) fails validation as `string_unicode`. It is a constrained `str`, `Field(min_length=1, max_length=200)`.
  - The traceback ends in FastAPI's `request_validation_exception_handler`, at `JSONResponse.render`.
  - POST gives 500 text/plain, and the retry with the same key gives 500 text/plain again.
  - The key store holds only the control's record, and `app.state.jobs` holds only the control's job.
  - No client string reaches L2686 or L2687, so no stored payload exists to fail on replay. This was code-read only in round 1 (`handoff-2fba4397-round1-laneF-reprobe.md`, "What I could not verify").
- Replacement for L81: "(b) The primer's `idempotent_jobs.py` example has candidate (a)'s defect: it registers no `RequestValidationError` handler, and a lone surrogate in `dataset_id` fails validation (`string_unicode`), so FastAPI's default 422 handler cannot render the echo. Measured in-process: a plain-text 500, and another on retry, because no key record is ever created. Nothing reaches `store.complete` (2686) or the 201 render (2687), so there is no replay defect. File it under (a), or drop it."

**M4. Candidate 6(a) predicts the wrong outcome for both named services.**
- Quoted: L74 "…is a plain-text 500 for a lone surrogate." L76 "juniper-data's APD-DATA-013 handler (…) is such a copy."
- Evidence:
  - `UnicodeEncodeError` is a `ValueError`, so a failed 422 render is re-dispatched to the app's `ValueError` handler.
  - Real juniper-data app, in-process with its lifespan, from checkout `1afc348` (its `app.py` equals `0f0f7e0e`'s), in the JuniperData env:
    - a lone surrogate in `ttl_seconds` gave **400 `application/json` `{"detail":"Invalid request parameters"}`**;
    - the control gave 422.
  - Model at data's locked versions (fastapi 0.141.1 / starlette 1.6.0, data `requirements.lock:47`, `:173`):
    - 422 handler only: plain-text 500;
    - 422 + `ValueError` + `Exception` handlers: 400 JSON;
    - 422 + `Exception` only: 500 JSON.
  - cascor has the same shape: its 422 handler at `:856` and its `ValueError` handler at `:916` return 400 `VALIDATION_ERROR`. I did not run cascor.
- Replacement for L74–L78: "(a) A 422 that echoes the input through Starlette's `JSONResponse` (`ensure_ascii=False`) raises `UnicodeEncodeError` for a lone surrogate. That is a `ValueError`, so what the client sees depends on the app's handlers:
  - FastAPI's default app: a plain-text 500;
  - juniper-data: `app.py:187-212` renders the 422, and its `ValueError` handler at `:214` catches the failure. Measured in-process: **400 `{"detail":"Invalid request parameters"}`**. The 422's per-field `detail`, which juniper-data-client parses, is silently lost. It is not a 500, so no Sentry event;
  - cascor: `:856`, with its `ValueError` handler at `:916`. Same shape, expected 400 `VALIDATION_ERROR`; not run."

**M5. The liveness test calls a live executor dead during exactly the phase it is in.**
- Quoted: L49 "If that file was written in the last ~10 minutes, the old session is still running…"
- Evidence:
  - `agent-a46e715a6801b98ca.jsonl` went unwritten for 600 s (20:21:04Z to 20:31:04Z) and 580 s (20:31:33Z to 20:41:13Z) while it waited on the mutation harness under a 600 s tool timeout.
  - Its current brief makes it rerun that harness. A "dead" reading here launches a second executor on the same dirty worktree.
- Replacement: "The old session is alive while `ListAgents` lists "defect reg [24f8d8]": treat the executor as alive while it is. The transcript's mtime is only a positive signal; it went 600 s without a write while waiting on the harness. Call the executor dead only if that session is gone, or its transcript is 30+ minutes old."

**M6. A round-1 correction weakened the marker: bare `surrogatepass` is satisfied by comment text at every site.**
- Quoted: L295 "Pin a PAIR of markers … `surrogatepass` and `compare_digest(presented,`."
- Evidence:
  - The bare word also appears in a comment or docstring at each site: service-core `:82`, data#440 `:108`, cascor#689 `:78`, canopy `:49`. `guard_is_present` is a whole-file substring match.
  - Constructed mutant: drop every `.encode("utf-8", "surrogatepass")` call, keeping the comments and the variable name.
    - The snapshot's pair stays **green at all four sites**.
    - The literal `encode("utf-8", "surrogatepass")` fails at all four.
  - `handoff_session_r1_frozen.md` pinned `.encode("utf-8", "surrogatepass")`, and at 23:41:03Z the session promised the peer that literal. Round 1's replacement text dropped it.
- Replacement: "Pin a PAIR: `encode("utf-8", "surrogatepass")` and `compare_digest(presented,`. Not the bare word: each site also carries it in a comment or docstring (service-core `:82`, data#440 `:108`, cascor#689 `:78`, canopy `:49`), so a revert that drops the `.encode` calls keeps a bare-word pair green. At canopy, a revert to `presented = api_key` that keeps `_compare_bytes` passes even the literal pair; the F3 spy's bytes-argument check catches it."

### LOW

- **L1.** L105: "`git log --format='%(trailers:key=Allow-Symbol-Loss)' 5af9d722` prints nothing".
  - Run verbatim, `git log` walks the history and prints 11 older waivers.
  - Replacement: "`git log -1 --format='%(trailers:key=Allow-Symbol-Loss)' 5af9d722` prints an empty line (without `-1` it prints older commits' waivers)".
- **L2.** L303: "Update the "seven guards" counts in `docs/REFERENCE.md` (about L2977) and in the register (about L1751)."
  - The register's "all seven guards are `ENFORCED`" statement is at L252. L1751 reads "**all six** … *(Seven since …)*", and L1106 reads "its six guards *(seven since ml#1974 …)*".
  - Replacement: "The guard count is stated in `docs/REFERENCE.md` (about L2977) and the register (about L252, L1106, L1751). Update all four."
- **L3.** L167–L171 list recurrence as a frame-locals consumer.
  - Recurrence initialises no Sentry: no `sentry` outside its locks and docs at `origin/main`, and `bytes-compare-…-validation.md:113` says "recurrence has no Sentry". What recurrence needs is the service-core release.
  - Replacement: delete "recurrence `:70`" from the frame-locals list. Change the service-core bullet to "…reaches recurrence only after a service-core release and a move of `juniper-recurrence/requirements.lock:74` (`==0.7.0`); its cap `<0.8.0` (`juniper-recurrence/pyproject.toml:51`) blocks a 0.8.0."
- **L4.** L58: "This session had begun the consolidation."
  - No draft exists (statuses at 23:41:03Z and 00:29:24Z).
  - Replacement: "No consolidated draft exists; this session only coordinated it with the peer (23:34:29Z)."
- **L5.** The two handoffs disagree on when rows close, and one clause conflicts with this snapshot's own gate rule.
  - L157 keeps ECO-013 open until F2 and F3 are fixed. The peer's draft (line 131) closes it once the three bytes-compare PRs merge and validate.
  - L178, "It closes when F4's fix lands", contradicts L149's rule (the PR merges AND its validation holds).
  - Replacement: add "The peer's handoff (line 131) closes ECO-013 without F2/F3; the consolidation must choose". At L178, write "when F4's fix merges and its validation holds".
- **L6.** L138 puts #2089's files under the heading "ship ALL of these in the next juniper-ml PR".
  - Shipping them would duplicate #2089 and inherit its CodeQL block.
  - Replacement: move that bullet to a separate "Not for the next PR" item, with "byte-identical to `a2fa3ad8`; leave them out".
- **L7.** L19: "SendMessage the peer lane, "defect reg [042116]"".
  - The peer is handing off too, and its draft (line 3) says "Never message it".
  - Replacement, append: "If [042116] is gone or has handed off, message the other live "defect reg [...]" session (the peer's successor), or ask the owner."
- **L8.** L112 says "(run from this worktree)", but a successor normally starts in its own worktree. The sandbox refused my `git -C` into another juniper-ml worktree (`happy-skipping-hollerith`).
  - Replacement: "run from `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream`. From elsewhere, read its files by absolute path; `git -C` into it is refused."

### NIT

- **N1.** L27, "On `main`": `main` now includes #2088, and the probe shows 0 differences there. Write "On the pre-merge primer (`c061a99f`)".
- **N2.** L71: replace with "PR CI (`ci.yml:500`) runs the whole file but skips every fork site without siblings; only `SharedPackageGuardTest` and the registry-structure tests assert there".
- **N3.** L110, "refuses compound shell around git and gh", is contradicted by L117 and L123, which run. Name the refused forms as the peer's draft does at lines 157–163.
- **N4.** L119, "39 here", rises by one for each round-2 report archived.
- **N5.** L29, "129 lane probe scripts": they are Python only. The 67 shell runners are deliberately not kept, as #2089's README line 51 says.
- **N6.** L242 says to re-copy the drafts after the executor finishes, but First action 4 ships them now. State which comes first.

## What I could not verify

- **Not rerun:** the mutation check (12/12), the 3.14.2 probe count (24), and lane B's 6.6 s timing.
- **cascor's surrogate outcome:** inferred from code only. I did not run cascor.
- **The stray canopy branches:** "apparently from VS Code". The activity API shows only that pcalnon created them.
- **`SENTRY_SDK_DSN` being exported:** policy forbade reading the environment.
- **The peer's side:**
  - its worktree's `git status`; the sandbox refused `-C`;
  - whether its PR drops the README rows: its draft (line 205, 00:21Z) predates the 00:25Z agreement.
- **`open_signed_pr.py` refusing an existing branch:** testing it would write to the repository.
- **The 403 message text, and the renderer's "breaking = NO":** the failed job is confirmed; the message and the renderer result come from the lane A report's row 22.
- **After the freeze:** the executor's context was compacted at 00:29:28Z, and it has not pushed. Review its commit with that in mind.

**Side effects:**
- I ran `git fetch` in the juniper-ml worktree and in the data, cascor, canopy and recurrence checkouts. Only FETCH_HEAD and origin refs moved, plus data's tag `v0.16.0`.
- Importing the data checkout in-process rewrote two git-ignored bytecode files: `juniper_data/api/routes/__pycache__/generators.cpython-314.pyc` and `juniper_data/generators/equities_seq/__pycache__/generator.cpython-314.pyc`. Its `git status` is still clean.
- No port was opened.
- I kept 14 small helper scripts in `…/scratchpad/hv2/laneF2/`, including `surrogate_422_layers.py`, `real_data_surrogate.py`, `idem_surrogate.py`, `idem_trace.py` and `marker_mutant.py`. The two `idem_*` scripts need `probe.py` re-extracted from `origin/main:util/ad-hoc/2026-09-24_primer_toy_error_paths_probe.py`. All other extracted copies are deleted.

**Changed:** no repository file, and no report or notes file created.
