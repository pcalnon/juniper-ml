<!-- Archived verbatim 2026-09-24 from subagent a6a4a26ed6b92d6e5 of session bc31e993 (final message). -->

## PR #2032 check (juniper-ml, head `bd3284db`)

Nothing was changed in any repo. I ran `git fetch` in juniper-ml, -canopy, -data, -cascor and -deploy, which moved remote-tracking refs only. Scratch copies and two symlinks are in my scratchpad.

**Path key**
- **ML** = `/home/pcalnon/Development/python/Juniper/juniper-ml`
- **CAN** = `…/Juniper/juniper-canopy` (origin/main `26e0546f`)
- **CAS** = `…/Juniper/juniper-cascor` (`0d2d826b`)
- **DATA** = `…/Juniper/juniper-data` (`68c3cd7c`)
- **REG** = `ML/notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, line numbers from the PR branch.

| Claim | Verdict | Evidence |
|---|---|---|
| a. Rulings match the owner's choices and list every rejected option | **Mostly verified, small additions** | Both chosen options are faithful, and all 3+3 rejected options are listed. X-A (REG:1354-1365) adds things the owner did not choose: "logs that it did so", a reason for each rejection, and "the first time a dataset request *needs* it". ECO-008 leaves "two PRs … then juniper-ml" implicit. The sentence "taken against a corrected premise" (REG:1429) cannot be checked from the owner's answers. |
| b. `_FORK_REPOS` is read in exactly three places; every guard names its sites | **VERIFIED** | Every hit in code on origin/main is in `ML/tests/test_service_fork_drift.py`: `:59` (the definition), then reads at `:264`, `:285`, `:353`. All 7 guards list their `sites` explicitly. Two checks that could have failed: (1) a canopy site with the 2-repo tuple fails `:285` (`'juniper-canopy' not found`); (2) with the tuple widened and canopy sites added, the test fails on canopy's missing markers. |
| c. Widening leaves results unchanged, 8/0/0/0 | **VERIFIED** | I loaded the worktree copy (byte-identical to origin/main) with `FORCE_LOCAL=1`: before 8/0/0/0, after monkeypatching 8/0/0/0, same ecosystem root. The data, cascor and canopy checkouts are clean and HEAD equals origin/main. The before/after match is guaranteed whenever a canopy *directory* exists, because its contents are never read. The zeros only show that data and cascor are current. |
| d. `docs-full-check` clones canopy; "the one real cost" | **Clone VERIFIED; "one real cost" MISLEADING** | `docs-full-check.yml:82` lists canopy, and run 35568824732 cloned it and ran 8 tests OK. But `:110` swallows a failed clone (`\|\| echo "WARNING…"`). With the tuple widened and no canopy directory the result is 5 pass, 3 **skip**, and the run still counts as successful. With the same root and the current 2-repo tuple it is 8/0/0/0. So one failed canopy clone would silently switch off the whole cross-repo check, including data and cascor, while the job stays green. |
| e. `get_secret` strips a secret file but returns the env var raw | VERIFIED | `CAN/src/secrets_util.py:62` strips; `:64` returns the env var as-is. |
| e. `[api_key] if api_key else None` is the only caller | VERIFIED | `CAN/src/security.py:265-267` is the only non-test `APIKeyAuth(` call. |
| e. No blank-key filter at `:53`; `:74` short-circuits | VERIFIED | `security.py:53` and `:74`. |
| e. `main.py` calls `enforce_auth_posture`; `real_keys` treats whitespace as no key | VERIFIED | `CAN/src/main.py:336-346`; `ML/juniper-service-core/juniper_service_core/auth_posture.py:61-71` and `:119-127`. |
| e. A whitespace-only env key enables `APIKeyAuth` | VERIFIED | Canopy's class, run from its origin/main source: `APIKeyAuth(["   "])` is enabled and `validate("   ")` returns True. |
| e. "a key no client can present, so every request is refused" (REG:1441) | **REFUTED** | Over HTTP the header can't carry it: h11 and httptools both parse it to `b''`, so the call gets a 401. But `main.py:712` falls back to `query_params.get("api_key")`, and canopy's own `_authenticate_websocket` code accepted `/ws?api_key=+++` as AUTHENTICATED in a live test. The three WebSocket endpoints also admit clients with no key at all (`allow_browser_auth=True`, `:776`, `:913`, `:3576`). The dashboard, health and metrics paths are exempt (`canopy_constants.py:658-667`), and `/api/train/*` and `/api/csrf` skip the key check (`:689-690`). canopy#660 itself says "WebSocket accepted the whitespace key". |
| e. The three siblings disable auth for whitespace-only keys | VERIFIED | DATA `security.py:73`, CAS `:40`, service-core `:45`. Run with `"   "`, `" \t "` and `""`, all three stay disabled. |
| f. Seven guards; ml#1974; the new table row | VERIFIED (row incomplete) | There are 7 `Guard(` entries. ml#1974 merged 2026-09-21T13:09:18Z (`ea24a19a`), and `git log -S` finds only that commit. It added the guard directly as ENFORCED, so "last one promoted = `cors-outside-auth`" still holds. cascor#659 merged 13:09:01Z and touched `src/api/security.py`. |
| g. Line refs `:53` `:74` `:59` `:285` | VERIFIED | As above. |
| g. "the 2026-09-11 ruling/text" (REG:1355, :1364, PR body) | **REFUTED** | The X-A ruling sits in the "OWNER RULINGS, 2026-09-09" block (REG:1323). It was added by `6ccf80fa` (ml#1864) on 2026-09-09 18:52 -05:00, via `util/ad-hoc/register_owner_rulings_2026-09-09.py`. §2.4 (2026-09-11) does not contain it. |
| g. The set is consulted on two paths, auto-start and the staged reload | VERIFIED | Its only consumer in code is `CAS/src/api/lifecycle/manager.py:3889-3892`. That is called from `_reload_dataset` (`:4162`) and `_auto_start_training` (`src/api/app.py:543`). |
| g. juniper-data's default "errs toward refusing" partial data | VERIFIED | `DATA/juniper_data/core/limits.py:138-139` are both False, and juniper-deploy sets neither variable. |
| g. Round-41 recorded this as "unattacked" | VERIFIED in substance | `ML/prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_defect-register-round-41-d-a-shipped-and-the-two-defects-its-own-audit-found.md:219-221`. The quoted wording is not verbatim. |
| PR-body verification numbers | VERIFIED | 126 rows / 99 fixed / 27 open; cross-check AGREE; 33 tests OK. |
| PR body: "cascor's X-A + X-B are in flight" | UNVERIFIABLE | canopy#660 is open; I found no open cascor PR for X-A or X-B. |

## Defects, most severe first

1. **High (factual).** REG:1439-1446 says a whitespace-only key is unpresentable and "every request is refused". Both are false (see the refuted row above), and canopy#660, the PR that implements this ruling, says the opposite. What is actually true: HTTP routes that check `X-API-Key` refuse every caller; WebSocket accepts `?api_key=<spaces>` and keyless browser clients; exempt paths are unaffected.
2. **Medium.** REG:1434-1435 calls the canopy checkout "the one real cost" and treats it as covered because the weekly job "already clones" canopy. That understates it. The root finder needs all listed repos or it finds nothing, and a missing root is a skip, not a failure. A swallowed clone failure therefore silently disables the whole check. The widening PR should either probe only the repos that sites actually name, or fail under `GITHUB_ACTIONS` when the root is not found.
3. **Medium.** The date "2026-09-11" is wrong in three places (REG:1355, REG:1364, PR body); the X-A ruling is from 2026-09-09.
4. **Medium (would mislead a successor).** "After the filter the service runs open with that warning" covers only `APIKeyAuth`. `CAN/src/frontend/internal_api.py:59-60` still sends `X-API-Key: "   "` on at least 34 `requests` self-calls, and requests 2.34.2 raises `InvalidHeader` on that value (checked), both today and after the fix. `main.py:494` also keeps the docs switched off. canopy#660 touches only `security.py`.
5. **Medium (successor, X-A).**
   - When the opt-in is withheld, `_describe_dataset_fetch_failure` (`manager.py:3735-3743`) goes by what went on the wire. It will tell the operator to set `JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS=true`, which is already on, and it emits the refusal token canopy keys on. "logs that it did so" does not cover this message.
   - "sends **no** truncation opt-in" should say it withholds only cascor's own default. A value the caller supplied must still pass through ("A DEFAULT, NEVER AN OVERRIDE", `manager.py:3895-3906`, `app.py:539-542`).
   - `_resolve_truncation_stance` is a `@staticmethod`, so the memoised list needs shared state and a data client that neither caller passes in.
6. **Low-medium.** The count correction is incomplete:
   - The new row (REG:270) and the blank-key row both list canopy nowhere as missing the guard, although APD-ECO-008 is open.
   - REG:242 "All of this group is now closed" still stands.
   - REG:1559 still says "all six copy-drift guards … every row in §2.3's table" (the table now has 7), and REG:1104 still says "six guards".
7. **Low.** REG:270 lists juniper-service-core as fixed in a row marked ENFORCED, but service-core is not a site of `nonshortcircuit-key-compare` (the test lists only data and cascor, `:172-173`). A regression in service-core's copy would not be caught.
8. **Low.** Beyond the X-A additions in row a, the ECO-008 behaviour change (auth on but unusable over HTTP → fully open) was not in the chosen option's description, and the register doesn't say whether the owner was shown it.
9. **Low.** REG:1278 says "the other three carry `{k … k.strip()}`". juniper-data actually uses `list(dict.fromkeys(...))` (`security.py:73`), deliberately a list.
10. **Low.** REG:1437 quotes the round-41 handoff inexactly and doesn't name the file.
11. **Info.** Canopy's `:74` short-circuit has no effect in production, because only one key is ever configured (`security.py:265-267`); the fix is for gate uniformity. The register also doesn't name the exact marker strings canopy's fix must contain, though canopy#660 does contain them.
12. **Trivial.** "lagged it until 2026-09-22" (REG:253-254) is only true if the PR, still open, merges on the 22nd.
