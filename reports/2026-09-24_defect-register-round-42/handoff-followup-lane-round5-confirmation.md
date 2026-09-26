<!-- Archived verbatim 2026-09-24 from subagent aa10d6cb5ba1666b4 of session bc31e993 (final message). -->

**v5 is not ready to publish as frozen, but only two wording fixes stand in the way.** v5 fixes round 4's MEDIUM: the fallback now keeps this lane's work in this lane. The problem is timing. The register lane rewrote its handoff (`…closes-pr-owed.md`) at 01:10:29Z, two minutes after v5 froze at 01:08:17Z, and two claims v5 makes about that file are now false. I found 1 LOW and 3 NITs. v5 (`HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`, sha256 `4661dc06…`) did not change during the review.

## Findings

**LOW-1. The routing claim in L27 is now false.**
- **Text:** "Its handoff tells it to message `[042116]`, which is gone, so tell it you replace `[042116]`."
- **Problem:** this was true of the 00:25Z `…closes-pr-owed.md` (`:19`). The 01:10Z version says otherwise (`:22-25`):
  - message the peer's SUCCESSOR, and "say you replace [24f8d8]";
  - message `[042116]` only "if [042116] is still listed";
  - "never wait on a message for the peer's PR".
- The action v5 prescribes is still right; only the stated fact is wrong.
- **Fix:** "Its handoff has it look for you too, and message `[042116]` only if still listed. Tell it you replace `[042116]`."

**NIT-1. The L134 line reference `:157` now points at the wrong line.**
- **Text:** "(the register lane's handoff, `:157`)".
- **Problem:** `:157` of `…closes-pr-owed.md` is now a `gh pr list` command. The condition has moved to `:200`, and v5's wording still matches it exactly. The citation is also a bare line number into an untracked file that another session is still editing, cited by role, which the CLAUDE.md naming rule forbids.
- **Fix:** write "(`…closes-pr-owed.md`, Appendix A, APD-ECO-013)".
- **Worth telling `[24f8d8]`:** its `:199-201` still says the two handoffs' APD-ECO-013 conditions "differ", and that the consolidation must choose. v5 now uses its condition, so they agree. Its "(its line 131)" reference into this file is also wrong; the row is at v5 L134.

**NIT-2. The "ask the user" line in L29 applies even when a successor exists.** It is a sibling of the no-successor bullet, so a reader who finds a live successor still asks. **Fix:** fold it into L28.

**NIT-3. The script's unsets match exact case only, but juniper-data reads its settings case-insensitively.** `settings.py:26,136` sets `case_sensitive=False`, so a lower-case variant would survive the `unset`. This shell exports no `JUNIPER_DATA_*` name in any case, so this is optional hardening.

## Checks

1. **Fallback rule:** it never sends the reader to the register lane's handoff as instructions (L12, L29). Its routing claim and the `:157` anchor were true at freeze and are stale now (LOW-1, NIT-1).
2. **Env names:** all three are real fields under `env_prefix="JUNIPER_DATA_"` (`settings.py:15,133`) at `:215`, `:216` and `:231`. The rate limit defaults to True, and both places that read it use the setting (`app.py:129`, `security.py:481`).
3. **cascor squash setting:** it is `COMMIT_MESSAGES`. #689's only commit, `97341680`, says "a 4001 close". ✓
4. **Stale comment:** it is at canopy `dc5ea02e`, `src/tests/unit/backend/test_cascor_service_adapter_gate_coverage.py:49-50`. The path in your brief is missing `backend/`; v5's bare filename is unique, so v5 is fine. CI does install the real client (canopy `ci.yml:170-177`). ✓
5. **Probe caveats:** `make_nv1_tree.py:8` deletes `sys.argv[2]`, and `fix_probe_pairs.py:2,29` rewrites a `compare_probe.py` in the working directory. ✓
6. **E2E branch:** it exists at `dd4413e5` and has no PR. Its blob `cc267d2b` matches the untracked copy. ✓
7. **Script:** shellcheck 0.11.0 is clean; `-o all` adds only the style warning SC2292. The script was last modified at 01:06:08Z, before the 01:07Z test. `JUNIPER_DATA_API_KEYS_FILE` is a real input (`core/secrets.py:19`). No scratch server is still running, and the juniper-data checkout is clean.
8. **Sandbox and `pkill` items:** both are internally consistent. My own `pgrep -f` matched my shell, and the bracketed form did not.

## Per-edit disposition

A = `handoff-followup-lane-round4-laneA-reprobe.md`, B = `handoff-followup-lane-round4-laneB-refute.md`.

| v5 line | Answers | Status |
|---|---|---|
| 11 | B LOW-5 | ✓ |
| 12 | A LOW-1, B MED-1, A NIT-4 | ✓ |
| 15 | glob also covers round 5 | ✓ |
| 16-18 | B LOW-2 | ✓ |
| 27-29 | A LOW-1, B MED-1 | ◐ LOW-1, NIT-2 |
| 55 | B NIT; the transcript answer is verbatim | ✓ |
| 69-73 | A NIT-2/3, B LOW-1, B NIT date | ✓ |
| 80 | rewording | ✓ |
| 81 | A NIT-5, B LOW-3 | ✓ |
| 93 | B NIT F9 | ✓ |
| 134 | B LOW-4 | ◐ NIT-1 |
| 145 | A NIT-5 | ✓ |
| 174-177 | A NIT-1 | ✓ |
| 180-186 | A NIT-4, B NIT | ✓ |
| 197, 210 | B LOW-5 | ✓ (`4a8af2a0...e70b54dc` is 2 commits touching one probe file) |
| 234-235 | B LOW-6 | ✓ |

Nothing v4 had right was dropped. "Use the consolidated handoff" survives at L10.

**Verdict:** no, not as frozen. LOW-1 blocks it: a claim that the register lane's 01:10Z rewrite made false. Reword L27 and L134 as above; both are wording-only and need no further round.

**Changed:** nothing; `hvJ/` is pruned.
