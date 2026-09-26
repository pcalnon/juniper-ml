<!-- Archived verbatim 2026-09-24 from subagent a7605941a055e6f60 of session bc31e993 (final message). -->

**Round 3, lane B: refutation of v3**

Documents:
- **v3** is `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`. Its sha256 `62f9b2bf…` is unchanged.
- **v2** is `handoff_v2_as_round2_saw_it.md`.
- **R2A** and **R2B** are `handoff-followup-lane-round2-laneA-reprobe.md` and `…-round2-laneB-refute.md`.
- The **validation report** is `bytes-compare-ml2086-data440-cascor689-validation.md`.

v3 fixes round 2's HIGH (who owns the release) and all of its MEDIUMs. I found one new MEDIUM, five LOWs (one is a round-1 regression) and four NITs. No owner-only action is left for the agent to take. I edited nothing, and `hvG/` is pruned.

## Findings

**MEDIUM-1. The juniper-data serve command is not safe as written.**
- **Text (v3 L70):** "Serve juniper-data by hand, with auth, metrics and Sentry off and scratch storage and import dirs: `…python -s -m uvicorn --factory juniper_data.api.app:create_app --host 127.0.0.1 --port <port>`, run from a juniper-data `main` tree."
- **Problem:** the command sets nothing the prose asks for, and names no variable.
  - `storage_path` defaults to `./data/datasets` (`juniper_data/api/settings.py:32`), so datasets get written into whichever checkout it runs from.
  - It reads that checkout's `./.env` (`:18`).
  - It picks up any `JUNIPER_DATA_API_KEYS`, `JUNIPER_DATA_API_KEYS_FILE` (`:169-172`) or `JUNIPER_DATA_REQUIRE_AUTH` in the shell. None is exported today, so that risk is latent; the storage write is not.
  - The obvious "main tree" is the shared checkout. It holds 42 cached entries and is at `1afc3484`, one commit behind `main` (`0f0f7e0e`).
- **Evidence:** the validator's own `run_jd.bash` (agent `a9ffba2344397011a`, 18:56:12Z) did it differently:
  - it served a scratch copy, not a checkout;
  - it ran `unset JUNIPER_DATA_API_KEYS JUNIPER_DATA_API_KEYS_FILE JUNIPER_DATA_REQUIRE_AUTH SENTRY_SDK_DSN SENTRY_DSN JUNIPER_DATA_SENTRY_DSN`;
  - it exported `JUNIPER_DATA_STORAGE_PATH`, `JUNIPER_DATA_IMPORT_DIR` and `JUNIPER_DATA_METRICS_ENABLED=false`;
  - it ran under `timeout 1500`.
- **Replacement:** "Serve a scratch COPY of juniper-data `origin/main`, never a checkout, because a checkout's `./.env` is read and storage lands in `./data/datasets`. Recreate `run_jd.bash` in `util/ad-hoc/`: unset those six variables, point the storage and import paths into scratch, turn metrics off, then run `exec timeout 1500 …uvicorn …` from the copy."

**LOW-1. #690 lost its fix-forward target, which re-opens round-1 C-M4.**
- v2 L64 said "**Then:** fix forward, per 'Where fixes go' below". v3's OPEN 1 (L62-71) drops that, and "Today that means" (L104-108) has no #690 entry.
- **Add to OPEN 1:** "Fix forward per 'Where fixes go': a signed fixup while #690 is open, or a new PR from `main` once it has merged."

**LOW-2. The consolidation trigger is misstated, and the step that sends the PR number is gone.**
- **Text:** L9 says "published after this file's PR merges". L24 says only "ask it for the consolidated handoff's path". v2 L20 also had "send it this file's PR number".
- **Evidence:** the register lane wrote "send me the final path plus the commit SHA or PR number" (23:34:29Z), and later "I consolidate the three once you send your final path and PR number" (00:21:47Z). Nothing waits on a merge.
- **Replacement for L9:** "…which it starts once it has this file's final path and PR number."
- **Replacement for L24:** "Unless it confirms `[042116]` already sent them, send this file's path and PR number, then ask for the consolidated handoff's path."

**LOW-3. State has drifted since the freeze: the README rows now ride juniper-ml#2089.**
- **Text (L205):** "plus the four new rows in `util/ad-hoc/2026-09-24_round42_probes/README.md`".
- **Evidence:**
  - At 00:25:06Z the register lane put those rows into #2089 (`a2fa3ad8`, open, not armed) and asked for the README to be dropped. The author agreed at 00:25:24Z.
  - The opener `2026-09-24_open_followup_handoff_pr.py` takes every modified path (its L14). Run as it stands, it re-adds the README, and this PR and #2089 would then conflict.
  - This file's PR is not open yet (`gh pr list --head …` prints `[]`), and v3 does not say who opens it.
- **Replacement for L205:** "the 63 probes (their README rows ride #2089)".
- **Add under Verification:** "If `[]`, restore `README.md` to `main` in `happy-skipping-hollerith`, then run the opener."

**LOW-4. A new spy test in data would never run in CI.**
- **Text (L92):** "In data, also mark the existing spy test `unit`".
- **Evidence:** at #440's head four classes are unmarked (`test_security.py:37`, `:269`, `:446`, `:590`). The validation report shows CI runs 72 of the file's 116 tests. A new spy test placed beside the old one would be deselected, so it would test nothing.
- **Replacement:** "Mark the new spy test `unit` too, or put it in the marked `TestNonAsciiApiKey` class (`:206`)."

**LOW-5. L17 contradicts L68, and L17 is false.**
- L17 says "the paths inside them point at a dead scratchpad". L68 says "Re-runnable probes".
- **Evidence:** none of the 63 files contains `claude-1000` or `bc31e993`. The `cascor688-v688` probes take their tree and URL from `sys.argv`, and the others build paths from `Path(__file__)`. The dead-scratchpad sentence is true of #2081's older 202 scripts, not these.
- **Replacement for L17:** "Most take a tree (and a URL) as arguments; some write under a `work/` or `out/` directory beside themselves."

**NITs**
- **L53, "signed commits cannot merge":** replace with "the signing path cannot create the merge commit that would resolve it".
- **L134, "It was asked (2026-09-24)":** the request went at 00:19:33Z on 09-25, and the register lane agreed at 00:21:47Z. Write "It agreed (00:21Z)".
- **F9's "commit text" (L97, L106):** a signed single-parent fixup cannot rewrite #689's commit body, and the default squash body will quote it again. Aim F9 at the CHANGELOG and the PR body.
- **Two things v2 had that v3 dropped:**
  - "the owner's ruling" before "Keep while fetched splits stay" (L53);
  - the `ci.yml:287` reference (L92).

## Specific checks

- **OPEN item 5 is correct.**
  - Releases stay with the owner.
  - Option (1) repeats the owner's own text. Option (2) is offered to the owner, not assumed.
  - The order is right: cap PRs before the Release, lock and floor PRs after the wheel is on PyPI. That matches `feedback_semver_beats_consumer_cap_2026-09-05.md` lines 25-30.
  - A grep for `releas|bump|floor|cap` finds no release work left to this lane.
- **The governance rule can be followed**, apart from LOW-2.
- **The owner gates are consistent** at L26, L115, L122, L169, L173 and L186.
- **F3, F5 and F9 are routed as the F-table says:**
  - juniper-ml: service-core's F3, F5 and F9;
  - cascor#689: F3, F5 and F9;
  - data#440: F3 and F5;
  - canopy: none.
- **Live state matches the document.**
  - #690, #689 and #440 are open, CLEAN and not armed, at the documented heads.
  - `pr-63` and `pr-683` both point at `4caf9389`.
  - CI is green on all six merges, including the late `repository_dispatch` run on `7f4a7213`.
  - `main` is `5af9d722`.
- **The new sandbox item is real.** The transcript refuses "`-C` relative to a `cd`" at line 6477. Two of my own commands were refused the same way: a loop around `sed`, and a `python3 -c` string containing "Git" (capital G, so the match ignores case).

## Actionability and length

- A successor following v3 would not take any owner-only action. The remaining risks are MEDIUM-1 and LOW-3.
- **The goal is easy to find:** the title, Step 0, `## Goal`, and "OPEN … in order".
- **The goal is long, and no reason is given.** Step 0 through OPEN is **1,755 words**, against a target of about 1,200; the same span in v2 was 1,645. The whole file is 3,140 words. R2B suggested cuts, and v3 made none.
- **Safe cuts, about 350 words in all:**
  - the Merged table's notes: cut each to its SHA plus one clause, about 130 words;
  - the lock and cap line anchors (L116-117): move them below the goal, about 90;
  - the evidence clauses in F2, F4 and F10: drop them, keeping every "how", about 80;
  - OPEN 2's "Also on record": move it to Coordination, about 50.
- That leaves about 1,400 words with no instruction lost. The length is hard to defend, because this file becomes only an evidence index once the consolidated handoff lands.

## Round-2 disposition

| Finding | v3 line | Status |
|---|---|---|
| R2A H1 / R2B 2 (canopy F5) | 94, 108 | ✓ (register lane told at 00:19Z) |
| R2A M1 (stray branches) | 122, 174 | ✓ |
| R2A M2 (`095a2108`) | 30, 58, 151 | ✓ |
| R2A M3 (`24103c23` is signed) | 101, 175 | ✓ |
| R2A L1 / R2B 5 (F9) | 97, 105-107 | ✓ |
| R2A L2 (ledger timeline) | 141 | ✓ |
| R2A L3 (sandbox refusals) | 157-163, 180 | ✓ |
| R2A L4 (re-running the probes) | 68-70 | ◐ MEDIUM-1, LOW-5 |
| R2A NIT1 / NIT2 | 54 / 201-206 | ✓ / ◐ LOW-3 |
| R2B 1 (release) | 37, 111-115 | ✓ |
| R2B 3 (cascor image lock) | 116 | ✓ |
| R2B 4 (cap order) | 114 | ✓ |
| R2B 6 (gate comment) | 134 | ✓ (NIT) |
| R2B 7 (which handoff governs) | 7, 9-11, 22-25 | ◐ LOW-2 |
| R2B 8 (owner gate on cleanup) | 169, 186 | ✓ |
| R2B 9 (git status) | 201-206 | ✓, then drifted (LOW-3) |
| R2B NITs (sweeper commits / `--head` / spy marking) | 30 / 192 / 92 | ✓ / ✓ / ◐ LOW-4 |
| R2B dropped items (APD-CASCOR-014, refusals, bytes-compare implementation report) | 130, 160-161, 86 | ✓ |
| R2B length | 20-123 | ✗ |

From round 1, only C-M4 has regressed (LOW-1).

**Changed:** none.
