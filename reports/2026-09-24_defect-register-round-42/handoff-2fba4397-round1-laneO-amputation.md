<!-- Archived verbatim 2026-09-24 from subagent a6a7b815d4ecf1415 of session 2fba4397 (final message). -->

VERDICT: FAIL

The snapshot is `handoff_session_r1_frozen.md` in the session scratchpad, sha256 prefix `1e5db1832f6131a8`, verified. "L<n>" below means its line n. Unless a path is absolute, it is relative to the worktree `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream`.

It fails on three HIGH findings: a commitment made to the peer lane is broken, uncommitted evidence is described as archived, and 195 probe scripts cited by the archived reports exist only on tmpfs with no task to preserve them. Every finding below comes with replacement text, so all are correctable.

## HIGH

**H1. Dropped task (broken commitment): the peer's F5–F10 as residue on APD-ECO-013, and the corrected F5**
- **Sources:**
  - This session's transcript, `2fba4397-7d9b-4929-8ca2-375b8168e1c8.jsonl`:
    - SendMessage at 20:36:26Z: "F5-F10 go on the row as known residue unless they are fixed first."
    - SendMessage at 23:35:52Z: "The consolidated handoff will carry only your corrected version [of F5] … It will not carry the U+1F511 text."
    - Peer messages at 20:35:57Z (F1–F10) and 23:35:30Z (the F5 retraction).
  - The peer's `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`, § "Coordination with the register lane": "F5–F10 go on its row as residue unless fixed first."
- **Snapshot:** Appendix A (L104-112) names only F2 and F3. F5, F6, F7, F9 and F10 have zero hits. "F8" appears only as data#438's F8 (L20, L193).
  - The peer's F8 is a defect in the gate this lane owns: a `break` after `matched = True` keeps both drift-gate markers. It confirms the "guard may be defeatable" row that `HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md` §9.7 marked UNVALIDATED.
- **Change:** after L112, add:
  > - **Residue on the row, unless fixed first** (the peer's successor fixes these and says which landed; source `bytes-compare-ml2086-data440-cascor689-validation.md`):
  >   - **F5 LOW:** add the surrogate PAIR as two code points, `chr(0xD83D) + chr(0xDD11)`, to every `_ENCODING_PROBES`, and fix the false "only total AND injective" comment. **Not U+1F511: every copy already holds it** (the peer retracted that text at 23:35Z). Build it with `chr()`, and check the file with `od -c`.
  >   - **F6 LOW:** no observability test frame has `in_app: False`.
  >   - **F7 LOW:** cascor's AST test matches only the spelling `sentry_sdk.init`.
  >   - **F8 LOW:** a `break` after `matched = True` keeps both drift-gate markers and survives every suite (F3's spy test kills it). This is this lane's gate: state it in `docs/REFERENCE.md`'s drift-gate section with Remaining 4.
  >   - **F9 NIT:** "ASGI close 4001; HTTP 403 on the wire".
  >   - **F10 NIT:** observability's CHANGELOG line "Consumers inherit both on upgrade, with no code change" is false, because every consumer locks `==0.4.0`.

**H2. Unsupported closure and under-reported uncommitted work**
- **Sources:**
  - `git status --short` shows 6 entries:
    - `util/ad-hoc/2026-09-24_archive_round42_reports.py` (M): its only change adds the MISSING entries `a6afb722d69732ae5` → `data438-fixforward-round1-laneA-reprobe.md` and `a641405b9532742e6` → `data438-fixforward-round1-laneB-refute.md`;
    - `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py` (M);
    - both data reports and `owner-ruling-key-leaks-verbatim.md` (??);
    - the handoff file itself (??).
  - The transcript's status messages at 23:46:44Z and 23:53:46Z list these files as changed.
- **Snapshot:**
  - L32 says the two data reports "are archived in reports/…", but they are uncommitted.
  - The Git status section (L94) lists 2 of the 6 entries.
  - Neither lane's agent id appears anywhere in the snapshot, so if the worktree is removed, nothing left in it can re-archive the reports.
- **Change:**
  - L32: replace "their reports are archived in" with "their reports are archived locally, UNCOMMITTED (see Git status), in".
  - Replace L94 with:
    > - **Uncommitted, for the next juniper-ml PR (nothing else holds them):** `util/ad-hoc/2026-09-24_extract_mixed_provenance_rulings.py` (M); `util/ad-hoc/2026-09-24_archive_round42_reports.py` (M: MISSING entries `a6afb722d69732ae5` / `a641405b9532742e6`, session 2fba4397); `reports/2026-09-24_defect-register-round-42/owner-ruling-key-leaks-verbatim.md`, `data438-fixforward-round1-laneA-reprobe.md` and `data438-fixforward-round1-laneB-refute.md` (??); and this handoff. From a fresh checkout, `--check` gives 34, not 36.

**H3. Dropped task: preserve this session's lane probes off tmpfs**
- **Sources:**
  - juniper-ml#2081 (merged 22:45:08Z, `7e8c7ff9`): "keep round 42's validation probes … off tmpfs".
  - `util/ad-hoc/2026-09-24_round42_probes/` on `origin/main` has 15 lane directories, none from this session.
  - The "Scripts" sections of `register-fixforward2-round1-laneA-reprobe.md`, `register-fixforward2-round1-laneB-refute.md`, `register-fixforward2-round2-laneA-reprobe.md`, `register-fixforward2-round2-laneB-refute.md`, `data438-fixforward-round1-laneA-reprobe.md` and `data438-fixforward-round1-laneB-refute.md` cite `scratchpad/r42b/`, `r42b2/` and `r42d/`. Those hold **195** `.py`/`.sh`/`.bash` files, all on tmpfs.
  - Juniper `AGENTS.md`'s script-placement rule prohibits `/tmp` as a script home.
  - The executor brief (SendMessage, 23:48:49Z) re-runs lane B's `stall_probe2.py`, `xproc_create_race.py`, `stripe_probe.py`, `fault_survey.py` and `access_suppression_probe.py` from there.
  - The pinned toy venv `scratchpad/primer-venv` is also on tmpfs.
- **Snapshot:** silent. Only the PR drafts are to be copied (L159).
- **Change:** add a Remaining item:
  > **Preserve this session's lane probes** (the #2081 precedent). Copy `scratchpad/r42b/lane{A,B}`, `r42b2/lane{A,B}` and `r42d/lane{A,B}/scripts` (195 scripts, cited by the six archived `register-fixforward2-*` and `data438-fixforward-*` reports) into `util/ad-hoc/2026-09-24_round42_probes/<report-stem>/`, with README rows, in the next juniper-ml PR. The Appendix D venv (CPython 3.13.13, fastapi 0.141.1, starlette 1.6.0, pydantic 2.13.4, httpx 0.28.1, pytest 8.4.2) is on tmpfs too: rebuild it for Remaining 1, then run `python3 util/ad-hoc/2026-08-13_run_primer_examples.py --doc <primer> --venv <venv>` (62 tests).

## MEDIUM

**M1. Conflict: APD-DATA-047 is presented as an open owner decision**
- **Sources:**
  - `HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md` §0.6 ("RULED 2026-09-21: RATIFIED at 1e11") and §9.6 (closed).
  - The register `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` on `origin/main`: L1284 `**FIXED (RATIFIED by the owner, 2026-09-21 …`, plus L1661 and L177.
  - `HANDOFF_2026-09-23_defect-register-round-42-four-prs-armed-by-an-unseen-actor-two-merged-unvalidated.md` lists D-G as "048/049/051" only.
- **Snapshot:** L69 and L148.
- **Change:**
  - L148 → "- D-G: `APD-DATA-048/-049/-051`. (`APD-DATA-047`, the 1e11 ceiling, was RATIFIED on 2026-09-21 and is FIXED in the register.)"
  - L69 → "- sequencing C-A…D-G;"

**M2. Unsupported closure: canopy#685 is unvalidated, and no gate says so**
- **Sources:**
  - Peer message at 23:35:30Z: "Its independent validation is still mine."
  - This session's SendMessage at 23:34:29Z: "#685's independent validation is yours."
  - `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`: its Merged table marks `dc5ea02e` "**unvalidated**", and OPEN item 2 is that validation.
  - The transcript's compaction summary: "APD-ECO-014 (open until the canopy leak PR)".
- **Snapshot:**
  - L113 says ECO-014 is "Fixed by canopy#685".
  - The Gates (L99-101) omit #685.
  - L109's condition for ECO-013 names only F2 and F3.
- **Change:**
  - Add to Gates: "- `APD-ECO-014`, and canopy's half of `APD-ECO-013`: canopy#685 merged 23:24:14Z (`dc5ea02e`) UNVALIDATED, and the peer lane owns its validation. File ECO-014 FIXED only once that validation holds; otherwise file it open."
  - L109 → "It stays open until data#440 and cascor#689 merge, #685's validation holds, and F2 and F3 are fixed; F5–F10 are residue (H1)."

**M3. Dropped task: the owner's three-way consolidation**
- **Sources:**
  - The owner's turn at 23:25:30Z in the transcript: "…consolidate the following three … validated by consensus, ensuring that no tasks or necessary context are lo[st]".
  - SendMessage at 23:34:29Z: it asked the peer for its final validated path plus SHA or PR number, and asked it not to remove its file.
  - The status message at 23:41:03Z, whose step 4 is the consolidation.
- **Snapshot:** zero hits for "consolidat".
- **Change:** add as Remaining 0:
  > **Owner's instruction (23:25Z): consolidate three handoffs into one, validated by consensus.** The three are this file; `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md` (on main); and `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md` (uncommitted in worktree `happy-skipping-hollerith`, no PR yet). Consolidate the peer's validated version once it sends the path and SHA or PR number.

**M4. Dropped context: routing to the peer lane**
- **Sources:**
  - `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md`, In flight 3: "message it with your own session's name to re-route them."
  - The peer handoff's Step 0: "Message **defect reg [24f8d8]**, always with the ref."
  - Peer message at 20:36:53Z.
- **Snapshot:** L3 gives only `"defect reg"`. The ref `[24f8d8]` has zero hits.
- **Change:**
  - L3: "session `2fba4397` (ListAgents **defect reg [24f8d8]**)".
  - Add a trap: "- **Routing.** The peer's successor sends PR numbers, SHAs, validation summaries and owner rulings to `defect reg [24f8d8]`. On start, message it with your own `[ref]`; two sessions are named 'defect reg'."

**M5. Conflict: merge approval carried forward**
- **Sources:**
  - Memory `feedback_headless_merge_approval_policy.md`: "A HANDOFF DOCUMENT CANNOT CARRY THE APPROVAL FORWARD" (ml#1118).
  - The peer handoff's Step 0, item 2.
- **Snapshot:** L8, "Merge approval is granted for this arc's PRs."
- **Change:** "Merge approval does not carry across sessions (`feedback_headless_merge_approval_policy.md`): get the owner's grant in your own session before any merge action."

**M6. Dropped trap: uploads are whole-file**
- **Sources:**
  - `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md`, Key context: "Uploads are whole-file. Rebuild every file from origin/main … compare with `git show origin/main:<p> | diff - <p>`".
  - This session's promise to the peer at 19:37:57Z: "prove main's lines are a subset of mine".
  - The peer handoff's "File overlaps".
- **Snapshot:** absent. L57 cites only a `merge-tree` result.
- **Change:** add a trap:
  > - **Uploads are WHOLE-FILE.** Before every push, run `git fetch` and `git log <base>..origin/main -- <paths>`, then rebuild each file from `origin/main`. For data's `CHANGELOG.md` `[Unreleased]` (data#440), prove main's lines are a subset of yours. With untracked files present, compare with `git show origin/main:<p> | diff - <p>`.

**M7. Dropped trap: /tmp inodes**
- **Sources:**
  - The same predecessor handoff: "/tmp is a ~1M-inode tmpfs … filled it to 100% … check with df -i /tmp".
  - The executor brief.
  - Measured now: 81% (848,988 of 1,048,576).
- **Change:**
  - Add a trap: "- **/tmp is a ~1M-inode tmpfs (81% at handoff; it hit 100% on 2026-09-24).** Brief every lane to prune."
  - Add `df -i /tmp | tail -1` to the verification commands.

**M8. Dropped trap: Sentry DSNs**
- **Sources:**
  - The peer handoff's Traps: set `SENTRY_SDK_DSN` (exported by this shell), `SENTRY_DSN`, `JUNIPER_CASCOR_SENTRY_DSN`, `JUNIPER_DATA_SENTRY_DSN`, `CANOPY_SENTRY_DSN` and `JUNIPER_CANOPY_SENTRY_DSN` to `""`.
  - This session's executor brief: "Unset every Sentry DSN variable … never 8100".
- **Change:** add that trap. It covers the executor and the data round-2 lanes, which run suites and live uvicorn servers.

**M9. Information loss: scope of the key-leaks releases**
- **Sources:**
  - Peer message at 19:48:28Z: the service-core half reaches recurrence only after a service-core release.
  - F10 in the peer message at 20:35:57Z: data `requirements.lock:88`, cascor `:63`, canopy `:79`.
  - The peer handoff's OPEN item 5: recurrence `:70`; caps `<0.5.0`.
  - This session's commitment at 19:48:50Z to record "the surrogatepass-not-surrogateescape reasoning" and "the OWNER STEPS".
- **Snapshot:** L108 names only canopy's lock.
- **Change:** replace L108 with:
  > - The frame-locals half reaches no running service until juniper-observability is released and every consumer's `==0.4.0` lock moves (data `:88`, cascor `:63`, canopy `:79`, recurrence `:70`; canopy and recurrence also cap `<0.5.0`). The service-core half reaches recurrence only after a service-core release. Record why `surrogatepass` was chosen over `surrogateescape`: it is total and injective.

**M10. Dropped owner item: a juniper-data release**
- **Sources:**
  - `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md`, Remaining 6: "it ships defects #438 fixes; 0.16.1 is the alternative".
  - `pending-items-snapshot-2026-09-24T1110Z.md`: "ships batch-tags race, NBSP star, symlink fault".
- **Snapshot:** L26 records only "published".
- **Change:** add to Remaining 7:
  > - juniper-data 0.16.0 on PyPI ships the defects #438 fixed. Those fixes and the fix-forward reach users only in the next data release, which also carries X8. The owner cuts it.

## LOW

- **L1. Dropped residue.** `pending-items-snapshot-2026-09-24T1110Z.md` "cascor residue (b)", repeated in the peer message at 19:06:26Z. Add to the Residue list: "After an inline start that replaces only some partitions, `current_dataset` names the fetch (the ruling intends this); canopy reads only `.dataset_type`. Record, no row."
- **L2. Garbled residue (L124).** Sources: peer messages at 19:24:36Z and 20:18:49Z. Replace with: "The flag-off 422 is no longer shown as a shortfall (#688). A juniper-data 400 for a bad param still was until #690, which keys on 'Re-submit with allow_truncation=true'. #690 also makes `_as_bool_stance` parse as juniper-data does."
- **L3. canopy#685's owner calls.** The peer handoff's OPEN item 2 lists (a), (b) and (c) as owner calls, and "Coordination" says the register quotes the owner's rulings verbatim. At L131-133, mark (b) and (c) as owner calls too, and add: "Quote the owner's rulings on (a)–(c) verbatim when the peer sends them."
- **L4. APD-CASCOR-014's fixing PR is unnamed.** The peer handoff's OPEN item 4 fixes F4 as a fixup on cascor#689. Add: "File it FIXED only if that fixup has merged and validated; otherwise file it open, citing #689."
- **L5. "done (F-CANOPY-060)" is overstated (L203, L24).**
  - The canopy e2e message at 19:40:28Z says the ids are "RESERVED, not yet in the ledger … 060 has no owner".
  - Re-derived: branch `docs/canopy-e2e-handoff-2026-09-24` is at `dd4413e5` with no PR, and `HANDOFF_2026-09-24_canopy-combined-e2e-y2-wave2-selection-owner-calls.md` is uncommitted in worktree `bubbly-meandering-pie`.
  - Change: "Reserved, and the fix is unowned. The reservation is recorded only off main, so re-check the ledger before citing it."
- **L6. Remaining 1's scope list omits part of the delta.** `git diff 990ef3f9 2439d049` also changes primer lines 4199, 5330, 5378, 5600 and 6091. Add them, and add: "Give the lanes the whole range, not this list."
- **L7. Chain drop from `HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md` §0.4.** `HANDOFF_2026-09-22_defect-register-round-41-d-a-shipped-and-the-two-defects-its-own-audit-found.md` still carried it; every handoff since dropped it.
  - `equities_seq`'s `data_quality` has no consumer in juniper-recurrence (0 hits, checkout `db41e77`) and none in the register.
  - `val_ratio` is recorded only in the register's §4.9 preamble (L1251-1257).
  - Change: add both to Remaining 7.
- **L8. Register-lane worktrees awaiting the owner's cleanup signal, carried by no handoff since 09-22.** All four are still on disk: `juniper-cascor--fix--nonshortcircuit-key-compare--20260921-0846--c6c848f2`, `juniper-data--feature--tri-state-allow-truncation--20260922-0753--e8db3ba6`, `juniper-data--fix--cheatsheet-conflict-markers--20260922-0820--e8db3ba6` and `juniper-cascor--docs--tri-state-truncation-prose--20260922-0822--8065ca0f`. Change: list them under Git status.
- **L9. Untracked findings from `data428-round3-laneA1-security.md`.** F3 is filed as `APD-DATA-056` (register L1303). F2 (the 8192 cap, parsed under `_version_lock`) and F4 (header limits) are recorded nowhere. Change L195 to: "F3 = APD-DATA-056; file or decline F2 and F4, with a reason, in the closes PR."
- **L10. Dropped residue.** `pending-items-snapshot-2026-09-24T1110Z.md`: "#683 item 3 is a DISCLOSED behaviour change (whitespace-only env key -> /docs etc. 200)". Add it to the Residue list.
- **L11. No "Changed" list, which the Juniper `AGENTS.md` naming rule requires.**
  - The transcript status at 23:53:46Z changed `reference_git_trailer_must_be_last_paragraph.md`, `reference_typed_escapes_become_real_characters.md` (new, and not indexed in `MEMORY.md`), `reference_backticks_eaten_in_shell_messages.md` and `MEMORY.md` (25,125 bytes).
  - The compaction summary adds `reference_subagents_killed_by_session_limit_resume_with_sendmessage.md`.
  - Change: add these five files as a "Changed by this session" line.
- **L12. Predecessor traps dropped.**
  - "Never name an OPEN id on the register's §2 status line": relevant because the closes PR files ECO-013 open.
  - The curated-squash re-arm recipe: `gh pr merge --disable-auto`, then `--auto --squash --subject … --body-file …`.
  - From `HANDOFF_2026-09-23_defect-register-round-42-four-prs-armed-by-an-unseen-actor-two-merged-unvalidated.md`: "The sweeper's arms store the DEFAULT squash body; put the waiver trailer in a COMMIT body."
- **L13. Internal contradiction at L140.** It says "none is started", but D-B is done (L143) and C-A's forks were killed (L152). At 23:35:52Z this lane also told the peer "C-A…D-G: I carry them." Change: "All are ruled. D-B is done; C-A was started and its forks were killed. This lane carries them. The order is 09-15 §0's; the owner decides when to start."
- **L14. D-F's rebuild point (L147).** Change "rebuild it on post-#438 code" to "rebuild it after the data fix-forward merges; it rewrites `save_versioned` and the lock stripes in `storage/base.py` and `storage/local_fs.py`."
- **L15. The #437 breaking-marker decision is unexplained (L65).** Source: `pending-items-snapshot-2026-09-24T1110Z.md`. Add: "Data's `[Unreleased]` carries #437's `equities_seq` 6.0.0, and the renderer computes breaking = NO."

## NIT

- **N1.** Appendix C (L164-190) leaves out parts of the executor brief:
  - M-1's CHANGELOG cost statement;
  - L-1's text scoping;
  - the tests that kill MX23, MX24, MX13 and MX14;
  - `[0.16.0]` must stay byte-identical to the tag (the redirect at 19:05:46Z).
- **N2.** L126, "#678's squash message is stale", is already recorded in the register (L1616-1617, via ml#2074).
- **N3.** L136 should add two things:
  - `--check` skips four peer reports headed "turn-ending report": `cascor686-implementation-report.md`, `cascor686-fixup-implementation-report.md`, `cascor688-implementation-report.md` and `cascor690-implementation-report.md`;
  - this lane promised (20:37:02Z) to byte-compare each peer report against its agent's transcript.
- **N4.** Say where the executor's report lands: the last message of `subagents/agent-a46e715a6801b98ca.jsonl` under session 2fba4397. The file moves when the session leaves its worktree.
- **N5.** The peer handoff says the register lane owns the `MEMORY.md` compaction; L68 frames it only as an owner decision.

## Coverage

| Source | Items checked | Carried | Closed with evidence | Dropped / conflict |
|---|---|---|---|---|
| `HANDOFF_2026-09-24_defect-register-round-42-fixforwards-merged-438-fixing-in-place-second-fixforward-owed.md` | 22 | 6 | 11 (#2084 re-derived; #2081 `7e8c7ff9`; #2088) | 5 (M4, M6, M7, L12, M5) |
| `pending-items-snapshot-2026-09-24T1110Z.md` | 49 | 10 | 36 (the second fix-forward via #2088) | 3 (L1, L10, M10) |
| 09-23, 09-22 and 09-15 chain (C-A…C-C, D-B…D-G, X-A…X-C, M-A, §0.4, worktrees) | 24 | 12 | 5 (X-C and M-A closed; D-B; `val_ratio` in the register) | 5 (M1, L7, L8, L12, L14) |
| Six lane reports (82 findings) | 82 + A1 F2–F4 | 23 (data, Appendix C) + 28 (round 2, Remaining 1) | 29 (on `origin/main`); 2 declined with a reason | A1 F2/F4 (L9); the probe scripts (H3) |
| Transcript: 12 inbound messages, 17 SendMessages, compaction summary, 3 status messages, owner's turn at 23:25Z | ~40 | 24 | 6 | 10 (H1, H2, M2, M3, M4, M8, M9, L1, L2, L11) |
| juniper-ml#2088 PR body | 32 | 3 | 29 | 0 (L6 is information loss) |
| Peer handoff, "Coordination" and traps | 20 | 9 | 2 | 9 (H1, M2, M4, M5, M6, M8, L3, L4, L12) |

The snapshot's merge facts all re-derive: #2088 (`5af9d722`, 23:41:16Z, commits `e2f87aae`, `990ef3f9`, `2439d049` and `1f116c38`), #2081, ml#2086, canopy#683, canopy#685 and cascor#688. Main-verify and CodeQL passed on `5af9d722`. The data branch is still at `d1c66a11`. data#440 and cascor#689/#690 are open at the stated heads.

## What I could not verify

- The executor `a46e715a6801b98ca`'s uncommitted work: I read committed refs only.
- Whether `SENTRY_SDK_DSN` is exported. I printed no environment variables, so this relies on the peer's word.
- `bytes-compare-ml2086-data440-cascor689-validation.md`, which is uncommitted in the peer's worktree and was not read.
- canopy#685's validation status, beyond the peer's message at 23:35Z.
- The archiver `--check` count of 36, which I did not run. I re-ran no harness or probe; the round-2 closures rest on the #2088 PR body plus spot checks of the census docstring and primer lines 6084-6087 and 6117-6120 on `origin/main`.
- Anything in the transcript after about 23:53Z.

**Changed:** no repository file. My only scratch was `hv1/laneO/` (8 files), now deleted.
