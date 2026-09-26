<!-- Archived verbatim 2026-09-24 from subagent afe00e807f4117068 of session bc31e993 (final message). -->

# Round 2, lane B: refutation of `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`

The rewrite fixes every round-1 HIGH. It introduces one new HIGH: it hands the release to this lane, against the owner's own ruling text. There are also three new MEDIUMs.

Nothing was edited. The document's hash is unchanged (`ffd111ef…`), and `hvE/` is pruned.

## New errors

**1. HIGH: the release is reassigned, against the owner's ruling.**
- **Text:** L33 "That covers validation, fix-forwards, the release PRs and the lock and floor PRs." L108 "This lane opens version-bump and release-notes PRs". L111 "This is the only owner step."
- **Problem:** the option the owner chose as "Fix everywhere now (Recommended)" reads "Up to four PRs. … **Releases stay yours.**" That comes from the transcript and is archived at `reports/2026-09-24_defect-register-round-42/pending-items-snapshot-2026-09-24T1110Z.md:9`.
- v1 had this right ("Owner steps: not agent work"). Lane C's H3 moved it without seeing this text.
- As written, a successor chooses the version numbers itself, and the sweeper may merge those bumps. L111's "only owner step" also contradicts L118 and the (a)–(c) calls.
- **Replacement:** "The owner reserved releases ('Releases stay yours'). Once the juniper-ml F-PR validates, ask the owner with verbatim options:
  - the owner prepares and cuts both releases; or
  - this lane opens the bump and notes PRs at versions the owner names, and the owner cuts the Releases.

  Ask separately about the cap, lock and floor PRs. Never approve the `pypi` gate (`feedback_deploy_approvals_paul_manages.md`)."

**2. MEDIUM: canopy's F5 is a no-op, the same defect class as round 1's HIGH.**
- **Text:** L89 "every `_ENCODING_PROBES`: … canopy `src/tests/unit/test_security.py:172`". L101 "one new canopy PR for F5 and the NIT".
- **Evidence:** at `dc5ea02e`, canopy has no `_ENCODING_PROBES`.
  - `:172` is `NON_ASCII`. It is checked only as `APIKeyAuth(["key1"]).validate(presented) is False` (`:174-176`).
  - The collision needs the pair presented against a configured U+1F511. Only a configured-by-presented matrix does that, as in service-core `tests/test_security.py:104-108`.
  - The validation scopes F5 to "all three" (`bytes-compare-…-validation.md:60-64`), meaning service-core, data and cascor.
- **Replacement:** "F5 applies to service-core, data and cascor only. Canopy's `NON_ASCII` is checked only against `["key1"]`, so the pair kills nothing there. Either add a configured-by-presented matrix over `NON_ASCII` plus the pair, or drop canopy from F5."

**3. MEDIUM: cascor's container-image lock is missing.**
- **Text:** L113 "cascor `:63/:65`".
- **Evidence:** cascor `requirements-cpu.lock:129` and `:133` pin `==0.4.0` and `==0.7.0`. Its header reads "CPU-only lock for the juniper-cascor CONTAINER IMAGE". L106's goal ("reaches no running service") depends on that file.
- **Replacement:** add "cascor `requirements-cpu.lock:129/:133` (the image's lock)".

**4. MEDIUM: cap raises are ordered after the Release, against the memory L110 cites.**
- **Text:** L112-116 put the caps in step 4, after the Releases.
- **Evidence:** `feedback_semver_beats_consumer_cap_2026-09-05.md` says "widen the consumer's ceiling … *before* the Release, or the consumer cannot install the artefact", and "raise the … floor only *after* the wheel is on PyPI".
- **Replacement:** "If a bump crosses a cap, the cap PRs land before the Release. Lock and floor PRs follow it."

**5. LOW: F9 is missing from the juniper-ml PR.**
- **Text:** L100.
- **Evidence:** `main` `juniper-service-core/CHANGELOG.md:57-58`, under `[Unreleased]`, says "checks the handshake closes 4001". F9 is scoped "all three" (validation `:84-88`), and that text ships in the release notes.
- **Replacement:** "…for F2, F6, F9 (service-core CHANGELOG), F10…".

**6. LOW: F8's false gate comment is unrouted.**
- **Text:** L82 "F8 … is killed by F3."
- **Evidence:** `tests/test_service_fork_drift.py:205-209` says "no behavioural test can tell them apart", which validation `:78-82` refutes. The file is the register lane's (L133).
- **Replacement:** "Ask the register lane to correct `:205-209` alongside the `surrogatepass` marker."

**7. LOW: there is no executable rule for which handoff governs.**
- **Text:** L9 "If a register-lane handoff newer than this file is on `main`, that one governs. Use this file for what it cites." L21 "the newest register-lane handoff on `main`".
- **Problem:** nothing names the consolidated handoff (no file, PR or search), and both files are dated 2026-09-24.
  - #2084's stale 11:10Z file is itself "a register-lane handoff on main", so a literal reader could pick it.
  - The register lane writes the consolidation only after this PR (its 23:34Z message), so a successor that starts first is never told to switch.
- **Replacement:** "`[24f8d8]` will publish a consolidated handoff after this PR merges. Ask it for the path at Step 0, and again before each OPEN item. Once it is on `main`, it governs every instruction, and this file becomes only an evidence index. #2084's handoff never governs."

**8. LOW: cleanup has no owner gate.**
- **Text:** L170-171 "Removable". L177 "is safe to delete".
- **Evidence:** `feedback_worktree_cleanup_only_on_explicit_merge_2026-05-15.md` requires the owner's explicit go-ahead per PR plus `gh` confirming MERGED. v1's "Before removing: verify each is clean…" was dropped. Deleting #686's branch also blocks reopening #686.
- **Replacement:** "Only with the owner's go-ahead in your session. First re-check `git status` and `gh pr view --json state,mergedAt`."

**9. LOW: the git status is incomplete.**
- **Text:** L193-197.
- **Evidence:** the worktree also holds the three round-1 reports, `2026-09-24_archive_followup_handoff_validation.py` and `2026-09-24_open_followup_handoff_pr.py`. The opener adds every changed path (about 90 files).

**10. NITs.**
- L25, "adds commits: canopy#685 got two": both are web-flow commits by the owner's account with Autofix-style messages. Nothing shows the sweeper made them.
- L184: the title search is fragile. `--head docs/handoff-round42-followup-lane` is exact, taken from the opener script.
- L87 marks data's whole `TestAPIKeyAuth` class `unit`, while the report says to mark only the spy test. That is a wider change.

## Amputations (v1 true, v2 dropped)

- **LOW:** v1's F4 row said "This is register row APD-CASCOR-014". The register lane files APD-CASCOR-014 as open "until the conftest fix lands" (20:37Z). v2 L127 lists it only as "reserved".
  - Fix: add it to L124-127: "APD-CASCOR-014 closes when F4 lands."
- **LOW:** the sandbox refusal "the literal word 'git' inside a `python3 -c` string" was dropped. I reproduced it this round.
  - Separately, the refusal list is too narrow. Variables around `sed`, `find` and `env -u` are refused too, not only around `git`, `gh` and `tar`.
- **NIT:** OPEN 3 no longer cites the bytes-compare implementation report.

## Actionability and length

- **The goal is findable:** the title, the Goal section and the ordered OPEN list.
- **The goal statement is over target.** L29-118 is 1,427 words, or 1,825 with Step 0, against a target of about 1,200. The Merged table and the F-table evidence could be cut down to references.

## Verified sound

- **Live state:**
  - #690, #689 and #440 are OPEN, CLEAN and unarmed at the documented heads.
  - #685 is MERGED as `dc5ea02e`.
  - All six merges have post-merge rollups at SUCCESS.
  - `main` is `5af9d722`.
- **Numbers and mappings:**
  - The lock and cap lines are correct, apart from finding 3.
  - The harness mapping (L62) matches both implementation reports.
  - The probe count of 63 is right.
  - The headers now read "k of 5".
- **Identities and quotes:**
  - The Step 0 identities are right, and `2fba4397` was active at 23:53Z.
  - The owner quotes are verbatim, and the merge grant ("merge approval granted.", 2026-09-22T17:59:59Z) is real.
- **Traps:** the three restored traps match the 09-23 handoff verbatim.

## Round-1 disposition

Key: ✓ = addressed correctly; ◐ = addressed, but with a flaw (the new-error or amputation number follows); ✗ = not addressed.

| Finding | Line | Status |
|---|---|---|
| A1, B-H1, C-M5 (F5) | 89 | ◐ correct for the three validated copies; canopy extension is a no-op (#2) |
| A2, B-H2 (#685 merged) | 49, 65, 167 | ✓ |
| A3, C-M1 (probes) | 13, 63 | ✓ |
| A4 (IDs unfiled) | 127 | ◐ F4 mapping lost |
| A5, B-L5, C-L3 (headers) | 128 | ✓ |
| A6 | 137 | ✓ |
| A7 | 134 | ✓ |
| A8 (Autofix unproven) | 52, 145 | ✓ (new unproven claim at L25) |
| A9-A12 | 192, 92, 90, 62 | ✓ |
| B-M1 (verbatim rulings) | 122 | ✓ |
| B-M2 (drift marker) | 38 | ✓ |
| B-M3, C-M7 (C-A…D-G) | 39 | ✓, as the register lane asked |
| B-M4 (three traps) | 143, 144, 158 | ✓ |
| B-L1 (main CI, #683 head) | 54, 48 | ✓ (re-probed) |
| B-L2 | 125 | ✓ |
| B-L3 (ledger) | 135-138 | ✓ ("It" is ambiguous; no action stated) |
| B-L4 | 178 | ✓ |
| B-NIT (stale comment) | 77, 101 | ✓ |
| B-NIT (blank-key script retire) | none | ✗, harmless. The script is in canopy's `util/ad-hoc/`, and juniper-ml's policy (owner, 2026-08-25) makes retirement owner-only. Leave it out. |
| B-NIT (recurrence) | 113-116 | ✓ |
| C-H1 (Step 0) | 16-21 | ◐ the fallback can select #2084's handoff (#7) |
| C-H2 | 22-23 | ✓ |
| C-H3 (release) | 106-117 | ◐ addressed wrongly (#1, #3, #4) |
| C-M2, C-M3, C-M4, C-M6, C-M8 | 11, 95-97, 95, 27/60/105, 150 | ✓ |
| C-L1 | 183-187 | ✓ (L184 fragile) |
| C-L2, C-L6 (cleanup; branch gate) | 173-177 | ◐ reason given, but gate dropped with no owner signal (#8) |
| C-L4 (harness mapping) | 62 | ✓ (verified) |
| C-L5 | 148 | ✓ |
| C-NITs | 51-52, 88, 36, 135 | ✓ |

**Changed:** nothing. Documents referenced: the handoff under review, the v1 scratch copy, the three `handoff-followup-lane-round1-lane{A,B,C}-*.md` reports, `bytes-compare-ml2086-data440-cascor689-validation.md`, `pending-items-snapshot-2026-09-24T1110Z.md`, `HANDOFF_2026-09-23_…-two-merged-unvalidated.md`, `feedback_semver_beats_consumer_cap_2026-09-05.md`, `feedback_deploy_approvals_paul_manages.md`, `feedback_worktree_cleanup_only_on_explicit_merge_2026-05-15.md`, and juniper-ml `util/ad-hoc/README.md`.
