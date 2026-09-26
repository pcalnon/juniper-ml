<!-- Archived verbatim 2026-09-24 from subagent a41961813422e6131 of session bc31e993 (final message). -->

# Lane A: factual re-probe of `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`

I found two HIGH findings. The document's F5 fix is wrong, and canopy#685 has merged since the document was written. Everything else holds apart from one MEDIUM and some LOWs and NITs. I changed nothing, and my scratch directory `hvA/` is removed.

## Findings

**1. HIGH: the F5 fix does nothing.**
- **Document says:** "Add `"🔑"`."
- **What is true:** all three copies of `_ENCODING_PROBES` already contain `"\U0001f511"`, which is 🔑:
  - service-core `tests/test_security.py:101`
  - data `test_security.py:34` at `0bee089e`
  - cascor `test_api_security.py:31` at `97341680`
- The fix in `bytes-compare-ml2086-data440-cascor689-validation.md` (lines 63-64) is the **surrogate pair** `"\ud83d\udd11"`. Its Housekeeping note (line 131) warns that escapes become literal characters on the way in, and the document reproduces exactly that error.
- **Evidence:** built with `chr()`, U+1F511 and U+D83D U+DD11 encode to the same bytes under UTF-16-LE with `surrogatepass` (`b'=\xd8\x11\xdd'`), but to different bytes under UTF-8. The mutant only collides when both strings are probed, so adding 🔑 leaves it alive.
- **Corrected:** "Add the two-code-point surrogate pair `chr(0xD83D) + chr(0xDD11)`, written as the escape `"\ud83d\udd11"`, not the literal 🔑 (U+1F511), which every copy already has."

**2. HIGH (changed since writing): canopy#685 has merged, without validation.**
- **Document says:** "head `4a8af2a04911` … Open, not armed."
- **What is true:**
  - The sweeper armed it at 22:48:09Z, and it merged at 23:24:14Z as `dc5ea02e`, merged by pcalnon.
  - The head is now `e70b54dc`. Two new commits (`78c08ec3`, `e70b54dc`) touch only `util/ad-hoc/2026-09-24_683_validation_leak_probes.py` (+8 −4, OSError handling). The squash tree `7cc93012` equals the head tree, so the production code is exactly what the document describes.
  - Post-merge CI: Post-Merge Main Verification and CodeQL passed; CI/CD Pipeline was still running.
  - The worktree's local `4caf9389` has tree `7fbccc33`, which is not byte-identical to the squash.
  - APD-ECO-014's condition ("until canopy#685 lands") is now met.
- **Corrected:** "canopy#685 MERGED 23:24Z as `dc5ea02e` (head `e70b54dc`) before validation; validate `dc5ea02e` and fix forward in a new PR."

**3. MEDIUM: the validators' probes are not gone.**
- **Document says:** "The validators' probe scripts from this round lived in `/tmp` and are gone."
- **What is true:**
  - This lane's validator probes still exist in this session's scratchpad, in `v683/`, `v686/probes/`, `v688/probes/` and `vbytes/`.
  - Earlier round-42 probes were already kept by juniper-ml#2081 (`7e8c7ff9`, 22:45Z), in `util/ad-hoc/2026-09-24_round42_probes/` (202 scripts).
  - `v683` and `v686` still hold about 493 MB of unpruned extracted trees (5,319 and 4,527 `.py` files), with `/tmp` inodes at 85%.
- **Corrected:** "This lane's probes survive in `…/bc31e993…/scratchpad/{v683,v686,v688,vbytes}` until the session's tmpfs goes. Copy them to `util/ad-hoc/` before handoff, then prune v683/v686."

**4. LOW: three row IDs are not in the register yet.**
- **Document says:** "This is register row APD-CASCOR-014" and "closes APD-ECO-014 … APD-ECO-013."
- **What is true:** `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` has 0 hits for all three IDs. The register lane announced them by message ("Row IDs, which I'll file in the next register PR", 18:34Z and 20:36Z).
- **Corrected:** "…(IDs reserved by the register lane, not yet filed)."

**5. LOW: four reports fall outside the archiver's byte-check.**
- `cascor686-implementation-report.md`, `cascor686-fixup-implementation-report.md`, `cascor688-implementation-report.md` and `cascor690-implementation-report.md` carry a "(turn-ending report N of 6…)" header. The archiver's `HEADER_RE` requires `(final message)`, so it will not byte-check them.
- The labels also skip "4": `cascor690-implementation-report.md` is the agent's 4th of 5 reports, not the 5th. The sixth turn-ending record is a session-limit notice.
- I byte-checked all 12 reports myself against their agents' transcripts, and all are exact.

**6. LOW: the canopy copies are stale only once #690 merges.**
- **Document says:** "the stale copies of #687's 'Nothing was loaded' sentence."
- **What is true:** cascor `main` (`7f4a7213`) still emits that sentence at `manager.py:4766`. Only the open #690 rewords it (`:4841`).
- **Corrected:** "…copies that go stale when #690 merges."

**7. LOW: the register lane's data branch owns more files.**
- `fix/conditional-requests-round4-followups` (`d1c66a11`, no PR yet) also changes `CHANGELOG.md`, `juniper_data/api/app.py`, `docs/REFERENCE.md` and `docs/api/JUNIPER_DATA_API.md`, which the document does not list.

**8. LOW: "edited by Copilot Autofix" is unproven.**
- The commit is `095a21085a`, authored "Paul Calnon", message "refactor(mutation_check): improve file handling with context managers". It has no Autofix trailer, and I found no CodeQL alert on the file.
- Behaviour is unchanged, as claimed: `originals[path]` is recorded before `text` is reassigned, and a `continue` follows.

**9. NIT: Git status.** `origin/main` has moved to `7e8c7ff9` (#2081), so this worktree's HEAD `c061a99f` is one commit behind. #2081 does not overlap the 18 untracked files.

**10. NIT: F9 wording.** The report says "rejected: ASGI close 4001, HTTP 403 on the wire".

**11. NIT: F6 is incomplete.** The report also asks for "one wire test with `in_app_exclude`".

**12. NIT: "the `cascor688` harness" is ambiguous.** Two exist. The imported one is `2026-09-24_cascor688_fixforward_mutation_check.py` (`spec_from_file_location`, lines 39 and 80). No other harness imports by path.

## Verified

- **PRs:**
  - **#690:** head `78e99414`, branch `fix/shortfall-688-validation`, 2 commits (`c4e002d2`, `78e99414`), open, not armed.
  - **#689** (`97341680`) and **data#440** (`0bee089e`): branch `fix/bytes-compare-no-500`, open, not armed. The register lane's acknowledgement names these same validated heads.
  - **#688:** merged as `7f4a7213`. Its body states the supersession, "keep while fetched splits stay", the seven findings, #686's fixup and the conflict resolution.
  - **#686:** CLOSED at 18:45Z.
  - **#687:** merged as `ec8b5bdb`. It really conflicted on two lines: a `merge-tree` run gives two one-line conflicts in `manager.py`, the `_reload_dataset(...)` call and its signature.
  - **canopy#683:** `7ab994e5`; body matches the row. **ml#2086:** `c061a99f`, 9 files.
  - **#2072** (the 09-23 handoff plus reports), **#2077** (the cascor678/cascor686 harnesses) and **#2084** (the register handoff): all merged.
  - Post-merge `main` CI is green on all five merge commits.
- **Code (`file:line`):**
  - canopy `security.py:115`, `:273` and `csrf.py:91` compare `str` at `7ab994e5`. #685 compares bytes at `security.py:137`, `:300` and `csrf.py:97`, and `outbound_errors.py:57-61` passes status-carrying text through.
  - `test_start_fresh_refusal_and_modal_text.py:42` and `dashboard_manager.py:8381` carry the sentence. The `" The resulting dataset"` cut is at `:8410`.
  - `juniper-observability==0.4.0` at data `requirements.lock:88`, cascor `:63`, canopy `:79`. Canopy caps it at `>=0.4.0,<0.5.0`. PyPI serves observability 0.4.0 and service-core 0.7.0.
  - cascor `conftest.py:35-37` is `import os`, `sys`, `sysconfig`, with no Sentry handling.
  - service-core: `surrogatepass` and no `break` (lines 88-92). observability: `include_local_variables=False`, the `vars` pop, and no `before_send_transaction`.
  - data: `TestAPIKeyAuth` (line 37) is unmarked, the spy test is at `:176`, and `ci.yml:287` runs `-m "unit and not slow"`. Only data has `sentry_send_pii`.
  - F7's AST match is at `:33-35`.
- **Numbers:** these match the reports.
  - `cascor688-validation.md`: 2 MEDIUM, 3 LOW, 2 NIT.
  - `cascor690-fixup-implementation-report.md`: "f"/"n" were read as true.
  - bytes-compare validation: 9 files sent 25 envelopes (24 errors plus 1 log batch), 0 failures over U+0000–U+10FFFF, 0 responses of 500, and a timing profile that follows only the configured key's length.
  - `canopy685-implementation-report.md`: judgement calls (a)–(c) and the frame-local key capture.
- **Commands:**
  - Command 1 printed the document's four heads when I first ran it.
  - Command 2 printed "Ran 11 tests … OK (skipped=3)"; the 3 skips name `JUNIPER_DRIFT_TEST_FORCE_LOCAL`.
  - Command 3 lists six directories; `bytes-compare` also matches the juniper-ml worktree.
- **Worktrees:**
  - All six exist and are clean.
  - The #690 worktree's HEAD is the PR head. The #685, #689 and #440 worktrees hold unsigned local commits that are tree-identical to their PR heads (for #685, to `4a8af2a0`, its head when written).
  - The stale branch `fix/shortfall-mixed-provenance-and-678-followups` exists at `e452a660`. The `-v2`, #683, #687 and ml#2086 branches are deleted.
- **Owner rulings:**
  - "Keep while fetched splits stay" and "Mine: fix forward" were answered at 07:32:48Z.
  - "Fix everywhere now (Recommended)" was answered at 18:30:09Z; its option text says "Up to four PRs".
  - **"Split: old does follow-ups" is supported only as a claim relayed by "defect reg [977fa8]".** The owner's own answer in this session (08:01:26Z) was "Resume both here", which is consistent with the split.
  - "defect reg [24f8d8]" is [977fa8]'s successor.
- **Files and traps:**
  - 18 untracked files: 1 handoff, 12 reports and 5 harnesses. Both predecessor files exist.
  - These are all in the transcript:
    - the refusal to resume a user-stopped agent;
    - the resume of a limit-killed agent;
    - `/tmp` at 100% of its inodes;
    - "2 pending events".
  - `SENTRY_SDK_DSN` is exported.

**Changed:** nothing.
