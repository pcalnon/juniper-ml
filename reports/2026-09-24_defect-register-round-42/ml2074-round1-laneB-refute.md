<!-- Archived verbatim 2026-09-24 from subagent a69df29a8e3cd7134 of session 8f86dec2 (final message). -->

**Verdict: REFUTED.** The APD-ECO-008 close itself holds. But this PR's fix pass repeats the mistake round 4 caught in the last one: it adds new false statements, it leaves standing a claim round 4 refuted (on a line the PR edited), and its own verification claim fails on one of the search terms it lists.

Documents cited below, by filename:
- the register, `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (shortened to `…DEFECT-REGISTER.md`), at PR head `edfac1e4`;
- the primer, `notes/JUNIPER_2026-08-13_JUNIPER-ECOSYSTEM_API-DESIGN-AND-IMPLEMENTATION-PRIMER.md` (shortened to `…PRIMER.md`);
- `docs/REFERENCE.md`;
- reports under `reports/2026-09-24_defect-register-round-42/`.

Line numbers are at the PR head. Quote the phrase to find each one.

## Findings, most severe first

**1. HIGH: a claim round 4 refuted is still standing, on a line this PR edited.**
- **Phrase** (`…DEFECT-REGISTER.md`, §2.3 blockquote "That drift check now exists"): "The last one promoted, `cors-outside-auth`, needed a mechanism the others did not".
- **Evidence** (the test file's git history on `origin/main`):
  - `d1ce9958` (#1103): three guards `ENFORCED`, two `KNOWN_GAP`.
  - `53751fac` (#1130) and `132832f0` (#1145) promote those two.
  - `b9629de0` (#1201) adds `cors-outside-auth` as a sixth guard, already `ENFORCED`. It was never `KNOWN_GAP`.
  - This PR's own paragraph a few lines above says "Two guards were promoted… `cors-outside-auth` in juniper-ml#1201 [entered as ENFORCED]". §5.1 says the ledger "fired twice (throttle, then blank-key filter)".
  - `ml2032-2059-round4-laneB-refute.md` T2-2 refuted exactly this. The PR edited the line that ends "The last one promoted," and left the claim.
- **Fix:** "The last one added, `cors-outside-auth` (entered `ENFORCED` in juniper-ml#1201)…".

**2. HIGH: a present-tense falsehood about the row being closed, and the PR body's sweep claim is false for its own search term.**
- **Phrase** (`…DEFECT-REGISTER.md` §4.3, "`APD-CASCOR-005` routing — SUPERSEDED 2026-09-21"): "`juniper-canopy/src/security.py` is a fourth, still unfixed, and `juniper-ml/tests/test_service_fork_drift.py` cannot express a canopy guard at all".
- **Evidence:**
  - On canopy `main` (`6c4ad9a9`), `src/security.py:82` has the filter and `:112-116` the `matched` loop.
  - On juniper-ml `main`, `_FORK_REPOS` at `:68` includes canopy, and canopy sites exist at `:186` and `:215`.
  - `git log -L997` shows the line was last touched by #1983 on 2026-09-21.
  - The PR body says the sweep covered "cannot express" and that "Every present-tense hit is now dated or corrected". Neither round-4 lane caught this line either.
- **Fix:** "was a fourth, unfixed until juniper-canopy#660 (2026-09-23), and the gate could not express a canopy guard until juniper-ml#2059 (`APD-ECO-008`, closed 2026-09-24)". Correct the PR body.

**3. MEDIUM: the new correction note gets its history wrong.**
- **Phrase** (`…DEFECT-REGISTER.md` §2): "Round 42 made both false by filing open post-primer rows — three `S`… and one juniper-data `C` (`APD-DATA-055`) — and each sentence names no id".
- **Evidence:**
  - `APD-DATA-046` (juniper-data, Sev C, still open) was filed on 2026-09-09 by #1864.
  - The "no open `Correctness` row" sentence dates from 2026-08-23 (#1290). It was therefore false for 15 days and several rounds before round 42.
  - A row parse of the base register gives open C rows `[APD-DATA-046, APD-ML-002, APD-CASCOR-013]`.
  - The Security sentence names seven ids, so "names no id" is also literally false.
- **Fix:** date the Correctness sentence as false since 2026-09-09 (`APD-DATA-046`), with `APD-DATA-055` as a second instance.

**4. MEDIUM: the PR puts two open rows into §2.3's copy-drift group, but four "closed" claims survive.** It also edited one sentence that `APD-ML-008` refutes.
- **Phrases** (`…DEFECT-REGISTER.md`):
  - "**The primer's `Security` rows and all three §2.3 drift groups are closed**"
  - "That closes… **every copy-drift row in §2.3**"
  - "**All of this group's rows are closed and encoded** *(for the forks the gate walks…*" (canopy is a fork the gate walks)
  - §5.1's intro: "The §2.3 copy-drift list is now worked through too."
  - §5.1's closing paragraph, edited by this PR: "…as `ENFORCED` so they cannot silently regress".
- **Evidence:** the PR's own table cells read "`juniper-canopy` — **open** (`APD-ECO-009`)" and "(`APD-ECO-010`)", and §2.3's lead counts them as the 18th and 19th entries. `APD-ML-008`'s seven marker-preserving regressions pass silently.
- **Fix:** scope each claim to "all but `APD-ECO-009`/`-010`". Replace "cannot silently regress" with "cannot silently lose their markers (`APD-ML-008`)".

**5. MEDIUM: an ID-free counting claim this PR made stale.**
- **Phrase** (`…DEFECT-REGISTER.md` §2): "`util/ad-hoc/register_open_set.py` now prints `APD-ML  5` under OPEN by prefix".
- **Evidence:** running the head's script on the head's register prints `APD-ML 7` (ML-002 through ML-008).
- **Fix:** give 7, or drop the number and keep the instruction to re-derive.

**6. MEDIUM: `APD-DATA-055` claims more protection than the evidence it cites.**
- **Phrase:** "**…and its lost-update protection holds per host.**"
- **Evidence:**
  - `data428-round3-laneB-refute.md` new finding 1 and `data428-round3-laneA2-claims.md` F2 both show batch-tags and DELETE take neither lock.
  - In one LocalFS uvicorn worker, batch-tags' acknowledged edit was lost to a conditional PATCH (1 in 240, live). A PATCH also returned 200 with a new ETag for a dataset that DELETE had removed.
  - The row's own body says "within one process only", which contradicts its title.
- **Fix:** say the guarantee holds only against writers that take the store lock, that batch-tags and DELETE take none, and that round 3 reproduced the race in one process.

**7. MEDIUM: `APD-ECO-011` overstates where the route can be reached.**
- **Phrase:** "juniper-deploy's `juniper-canopy-demo` and `juniper-canopy-dev` services are open by design (no key), which is exactly where it is reachable".
- **Evidence:**
  - In juniper-deploy's `docker-compose.yml`, canopy-demo sets `JUNIPER_CANOPY_CASCOR_SERVICE_URL` and no `DEMO_MODE`. Only canopy-dev sets `JUNIPER_CANOPY_DEMO_MODE: "true"`.
  - canopy's backend factory therefore gives canopy-demo a `ServiceBackend` (`backend_type` "service"). The route returns 400 unless the backend type is "demo" (`src/main.py:1645`).
  - So in juniper-deploy's `demo` profile, which the title's "auth-off demo profile" appears to name, the route does nothing. juniper-deploy's `CHANGELOG.md:179` wrongly says canopy-demo runs demo mode.
- **Also:**
  - "any web page" was not measured in a browser, and both services publish on loopback only.
  - The handler falls back to `{}` on a body it cannot parse, so any simple POST regenerates the dataset. The remedy must check `Content-Type`, not parse failure.
  - "it also belongs in the canopy E2E ledger" names no `F-CANOPY` id. §4.9's intro records round 2 refusing exactly that "intention as a location" pattern.

**8. MEDIUM: the primer-anchor correction is incomplete.**
- **Phrase** (`…DEFECT-REGISTER.md` §4 header): "The Appendix A anchors — Q26, Q57 and Q58… are corrected; the others past 5758 are unverified."
- **Evidence:**
  - `APD-SVCCORE-007`'s anchor `9448` lands on Q22's circuit-breaker answer in `…PRIMER.md`. The row's subject, Q23 (in-memory rate limiting across replicas), is at `9450-9451`.
  - #1098 is the only edit to the primer since the register was created, so every creation-time anchor past 5758 is exactly 3 short.
  - At least 8 rows land on blank lines: `7950`/`7962` (SVCCORE-003), `6400`, `6961` (three rows), `7407`, `6625`, `7615`.
  - §6 still says the primer "is not being edited", and §1 and §2.2 still say "9,863 lines". The primer is 9,866 lines.
- **Fix:** change 9448 to 9451, state the +3 shift as fact, and amend §6 and "9,863".

**9. MEDIUM: a missed canopy copy-drift divergence.**
- **Phrase:** "canopy is a site of no other guard, and its missing body cap and failed-auth throttle are `APD-ECO-009` / `-010`". The §2.3 CORS row says nothing about canopy.
- **Evidence:**
  - canopy `src/main.py` registers `CORSMiddleware` first (`:519`, so it runs innermost) and `SecurityMiddleware` after it (`:540`).
  - `_is_exempt` checks the path only, with no `OPTIONS` bypass. This is the `APD-CASCOR-001b` shape.
  - The gate's own `cors-outside-auth` ordered site, run against canopy `main`, gives `guard_is_present=False`. It gives True for data, for cascor, and for a canopy copy with the CORS block moved last (the control).
  - It is latent: `cors_origins` defaults to `[]` and no deploy profile sets it. This is from code reading; I made no live request.

**10. LOW: instrument adequacy (the counts question).** Both scripts were mutation-checked on scratch copies.
- Editing the prose counts (34→35, thirty-eight→thirty-nine, 19→20, Eighty-one→Eighty) leaves `134 | 100 | 34` and AGREE unchanged.
- A phantom open row gives 135/35 from the open-set script while the crosscheck still says AGREE.
- Changing `APD-ECO-009`'s severity from S to M is invisible to both.
- Removing `APD-ECO-008` from the §2 list still gives **AGREE**. The PR's parenthetical "closed `APD-ECO-008`" sits on the same status line, so for this close the "100 ids named identically in §4, §2 and §5.1" claim does not test the §2 touch. The same blind spot already existed for DATA-047 and DATA-050.
- Controls behave: dropping the §5.1 row or unmarking the §4 row gives DISAGREE.
- The prose numbers are nonetheless correct: re-derived as 96 + 38 = 134 rows, 81 + 19 = 100 fixed, 15 + 19 = 34 open.

**11. LOW: provenance errors in the §4.9 intro.**
- "each row says which" is false for `-054` and `-055`, which name no finder.
- `-009` and `-010` are attributed to "validating `APD-ECO-008`'s two PRs", but their rows say "validating… ruling". The evidence is in `ml2032-round3-validation.md`.
- `-054` came from #428's implementation, per §2.4's own re-ruling note.
- "**FIFTEEN rows… different provenance**" leaves out round 39's DATA-046 to -052.
- "that day" now reads as 2026-09-24.

**12. LOW: stale counting sentences left in the §2 paragraph this PR rewrote, and nearby.**
- "Four were FILED BY a fix for the others": `-054` is a fifth.
- "**Ten of those carry owner rulings taken 2026-09-09** and are actionable": most are now fixed.
- §2.2: "The only unauthenticated memory-exhaustion vector in the register…": `APD-ECO-009` is another.
- The park note on `APD-DATA-047` ("no row… is awaiting an owner decision") lists two ways it is false. It is now false a third way, with eight new rows awaiting rulings.

**13. LOW: `APD-ML-007` says "a Release body cannot be re-cut".** That is a comment in `ceremony.py:431`, not a GitHub constraint: `gh release edit` can change the notes. The row also predates the cut: v0.16.0 was cut at 08:52Z, 12 minutes after this commit, at `39d1cab`, with 41 bullets and "Breaking changes: YES". Its PyPI publish run is still "waiting".

**14. LOW: an unqualified gate claim, in two places.**
- The §5.1 row for `APD-ECO-008` says "a missing canopy checkout FAILS rather than skips". That is true in a unit run only. In CI the link check fails first, which `APD-ML-008` itself says.
- `docs/REFERENCE.md`, in the entry this PR edited, still says the same, still calls docs-full-check "the only job that clones the siblings" (`release-train.yml` clones them too), and still has no marker-text caveat.

**15. NITs.**
- `-054`: "Remedy of record" (the owner deferred the remedy), and "change the served bytes" where juniper-data's docstring says "can change".
- The new park bullets group three, three and two rows. §1 defines that as a group-level park, while the §4.9 intro promises row-level sentences. There is precedent in ML-002 to -006.
- A duplicated "(seven since juniper-ml#1974)" parenthetical.
- `-013`'s Source cell still says "the single write".
- The "disabled when unset" quote is stale: canopy#678 rewrote that docstring line.
- §1 still says "groups sixteen entries".
- `-010`'s sibling anchors point at class definitions, not the wiring.
- The handoff recommended severities M, M, M, L and M. The PR used S, S, S, R and C without saying why, and those choices are what made §2's sentences false.

## APD-ECO-008 close

- **For closing:**
  - Every step of the ruling is done and checked: canopy `src/security.py:82` and `:112-116`, `_FORK_REPOS` plus sites, and the root probe.
  - Run 35975353661 is real: a `workflow_dispatch` on `main` `dcfc024f`, whose drift step ran 11 tests, OK, none skipped.
  - Both halves of the row (the code and the gate's ability to name canopy) are gone.
  - The marker-text weakness applies to the whole gate, has been disclosed since #1103, and is routed to `APD-ML-008`.
  - canopy's own three-key spy test catches the compare regressions.
- **Against closing:**
  - The row existed for the gate half, and the gate protects only marker text: seven regressions pass.
  - The service-core site was ruled on a false premise.
  - The deployed service-core 0.7.0, which juniper-recurrence's lock pins, still short-circuits.
  - The CI arm can still be skipped: no `if: always()`, and a failed data or cascor clone skips everything.
  - The close's own sweep missed findings 1 and 2.
- **My verdict:** the close is justified as a status change. Its prose needs a fix-forward (findings 2 and 14).

## What did not land

- Tables: 34 blocks, constant cell counts, and the checker's control fires.
- The five touches are all present.
- The new rows are not duplicates, their ids are in sequence, and the Sev legend holds against precedent (DATA-001, DATA-002, DATA-006).
- Every other anchor I checked is correct:
  - canopy: `middleware.py:59-74`, `:129`/`:132`; `main.py:1642-1654`;
  - data: `artifacts.py:33-63` and the four store lines;
  - FailedAuthThrottle anchors: data `297`, cascor `256`, service-core `341`;
  - drift test `:68`/`:338`;
  - primer `9466` / `9595-9597` / `9599-9601`.
- The promotion-history paragraph is right, and so is the "ten original copy-drift rows" claim.
- `APD-ML-008` is faithful to both round-4 reports.
- All four owner rulings match the transcripts. None is recorded more broadly than given. "0.x may break v1" is recorded more narrowly: only under -017/-032, although the question also covered D-C and D-D.
- The 44 tests pass (skipped=3).

## What this evidence cannot support

- Findings 7 and 9 come from reading code and config; I made no live or browser requests.
- The service-core 0.7.0 short-circuit rests on two earlier reports; I did not download the wheel.
- I did not check the archived reports for byte-identity.
- I have not seen Lane A's output.

**Changed:** nothing in any repository. Two side effects: I created a remote-tracking ref, `refs/remotes/origin/pr-2074-laneB-scratch`, in juniper-ml's git, and ran `git fetch` in the sibling main checkouts. I printed no credentials and sent nothing externally; I made only GitHub and PyPI reads.

Scripts are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneB/`: `mutcheck.py`, `blindspots.py`, `rows.py`, `tables.py`, `primer_anchors.py`, `cors_site_probe.py`, `transcript_q.py`.
