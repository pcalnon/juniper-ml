<!-- Archived verbatim 2026-09-24 from subagent aebc684c555a675b4 of session bc31e993 (final message). -->

# Lane B (amputation hunt): findings for `HANDOFF_2026-09-24_round-42-follow-up-lane-four-prs-await-validation-and-the-observability-release.md`

I changed no files. My scratch directory `hvB/` is deleted, and `/tmp` inodes are at 85%. My only other actions were read-only `gh` and `git -C` queries.

The handoff has two HIGH problems. Its F5 fix would do nothing, and canopy#685 has merged since it was written.

## Omissions and unsupported closures

**HIGH-1: F5's fix text is a no-op.**
- **Source:** `bytes-compare-ml2086-data440-cascor689-validation.md`.
  - Line 63: "U+1F511 and the pair U+D83D U+DD11 both become `=\xd8\x11\xdd`".
  - Line 64: "**Fix:** add `"\ud83d\udd11"` to the probes; my probe catches the mutant with it."
  - Line 131 names the cause: "a surrogate-pair escape became one astral character."
- **Handoff line 53:** "Add `"🔑"`". The bytes are `F0 9F 94 91`, which is U+1F511.
- **Why it fails:** every copy already holds U+1F511, so the addition is a duplicate and the mutant survives.
  - service-core `tests/test_security.py:101` on main;
  - data `juniper_data/tests/unit/test_security.py:34` and cascor `src/tests/unit/api/test_api_security.py:31` on their PR branches;
  - canopy `src/tests/unit/test_security.py:172`, as `("emoji", "\U0001f511")`.
- **Spread:** the same wrong text went to the register lane at 20:35:57Z. The compaction summary had it right.
- **Text to add:** "F5: add the two-code-point surrogate PAIR `"\ud83d\udd11"`, typed with literal backslashes. Every copy already holds U+1F511. The Write, Edit and SendMessage paths decode a JSON `\ud83d\udd11` into U+1F511, so build the pair as `chr(0xD83D) + chr(0xDD11)` or check it with `od -c`. Tell the register lane its F5 text is wrong."

**HIGH-2: canopy#685 merged after the handoff was written.** This is state drift, lane A's ground. I flag it because it rewrites item 2.
- **Live state:**
  - MERGED at 23:24:14Z as `dc5ea02e8aac`, from head `e70b54dcee0b`.
  - Armed at 22:48:09Z.
  - Two Copilot Autofix commits were added first: `78c08ec3` (23:00Z) and `e70b54dc` (23:06Z). Both add `print(e)` to `util/ad-hoc/2026-09-24_683_validation_leak_probes.py` and touch nothing else.
- **Handoff lines 34 and 94:** "head `4a8af2a04911` … Open, not armed" and "keep".
- **The worktree:** its local branch holds the unsigned `4caf9389`, which was never pushed (`canopy685-implementation-report.md:72`). Its tree lacks the autofix edits, so the "byte-identical to the merged squash" cleanup check will flag that probe file.
- **Text to add:** "canopy#685 MERGED as `dc5ea02e`. Validate the merged tree, then fix forward. Send the merge SHA to the register lane: APD-ECO-014 and the ledger's LOW3/LOW4 wait on it. The worktree's `4caf9389` is unsigned. It differs from the merge only by the autofix edits to the probe script."

**MEDIUM-1: the promise to forward owner-ruling text is dropped.**
- **Sources:**
  - 08:01:39Z, this session: "the PR number, the merge SHA and a validation summary, plus the text of any new owner ruling."
  - 07:59:16Z, from 977fa8: "and the text of any owner ruling you receive."
  - 09:06:00Z, from 977fa8: "the register must quote the owner verbatim."
- **Handoff line 70** lists only the PR number, merge SHA and summary. Meanwhile three owner calls, (a)–(c), are pending (lines 37-40).
- **Text to add:** "…and the verbatim question, options and answer of every owner ruling, canopy#685's (a)–(c) included."

**MEDIUM-2: the drift-gate guard for the bytes compare was never added and never routed.**
- **Source:** the bytes-compare implementation report, line 51: "Not added: a drift-gate guard for the bytes compare, because that section belongs to the register session."
- None of the 16 outgoing messages mentions it.
- `tests/test_service_fork_drift.py` on main has no `surrogatepass` or `encode(` marker, yet four copies of the compare now exist.
- **Text to add:** "Owed and unrouted: a fork-drift guard pinning `.encode("utf-8", "surrogatepass")` at all four sites. Agree an owner with the register lane."

**MEDIUM-3: later arc items C-A…D-G are dropped.**
- **Source:** the previous handoff (`HANDOFF_2026-09-23_defect-register-round-42-four-prs-armed-by-an-unseen-actor-two-merged-unvalidated.md`), line 82: "C-A (relaunch fresh…), C-B, C-C, D-C, D-D, D-E, D-F, D-G (048/049/051). D-F collides with data#428 on `storage/base.py`."
- The split message (07:59:16Z) assigned them to neither lane. The register handoff lists them only under "Owner decisions to surface" (line 51).
- The new handoff never mentions them; line 17 omits them.
- **Text to add:** "Unowned: C-A…D-G. Ask the owner which lane owns them. C-A must be relaunched fresh. D-F collides with `storage/base.py`."

**MEDIUM-4: three traps from the previous handoff are dropped (its lines 87-89).**
- **The traps, quoted:**
  - "The sweeper's arms store the DEFAULT squash body. Put any waiver trailer (`Allow-Symbol-Loss:`) in a COMMIT body in the range."
  - "A CHANGELOG built on a release cut BEFORE update-branch mis-files silently… update-branch first, then push the corrected file."
  - "`--commit-body "$(cat f)"` to the pushers IS accepted."
- **Why they matter now:**
  - F7 replaces an AST test file, which is a symbol loss and needs a waiver. #690 already carries three waived symbols.
  - The owner is to release observability while F2/F6/F10 edit `juniper-observability/CHANGELOG.md`.
- **Text to add:** all three, verbatim, under "Traps".

**LOW-1: two merged-state claims have no source behind them.**
- **Main CI (line 19, "post-merge `main` CI green"):** no source records main CI for any of the three merges.
  - `cascor688-validation.md:5` says: "A second round of unit-test jobs was still running."
  - My re-probe finds the rollup at SUCCESS for `7f4a7213`, `7ab994e5` and `c061a99f`.
  - ml#2086's squash tree equals its validated merge head (`5890d7b4`).
- **canopy#683's merged head:** it merged from `34e06747`, which merges main `f2147403` into the validated `8917fdac` (12 files; the only overlap is `CHANGELOG.md`).
  - `canopy683-validation.md:87` warned: "An update-branch would create a new head SHA that needs re-checking."
  - No re-check appears anywhere.
- **Fix:** state both facts explicitly instead of implying them.

**LOW-2: the register lane's conditions for closing APD-ECO-013 are compressed.**
- **Sources:**
  - 19:48:50Z: "close APD-ECO-013 citing all three once they merge and validate."
  - 20:36:26Z: "F5-F10 go on the row as known residue unless they are fixed first."
- **Line 71** omits both. data#440 and cascor#689 must merge and validate, and the register must be told which F-items got fixed.

**LOW-3: the canopy ledger items are incomplete, and one claim is unconfirmed.**
- **Sources:**
  - 18:34:04Z: "LOW 3 and LOW 4 … go to the canopy E2E ledger."
  - 18:35:22Z: "record them as fixed-by that PR."
  - 20:25:20Z: "I'll forward them". This is future tense, and no confirmation followed.
- **Line 74** says "forwarded by the register lane" and omits LOW3 and LOW4.
- **Fix:** add LOW3/LOW4 as fixed by `dc5ea02e`, and write "said it would forward".

**LOW-4: stale local branches are left out of the cleanup.**
- The cascor repo still has local branches `fix/shortfall-mixed-provenance-and-678-followups` and `fix/shortfall-mixed-provenance-and-678-followups-v2`.
- Line 101 names only the remote branch. The remote `-v2` and `fix/blank-key-678-followups` are already gone.

**LOW-5: part of the archive is not machine-checked.**
- I byte-compared all 12 new reports: each body equals one message of its agent exactly.
- Four of them are headed "(turn-ending report k of 6…)": `cascor686-implementation-report.md`, `cascor686-fixup-implementation-report.md`, `cascor688-implementation-report.md` and `cascor690-implementation-report.md`.
- The register's `--check` verifies only "(final message)" headers against an agent's last message (20:37:02Z), so it skips these four.
- **Fix:** say so when sending the filenames.

**NIT: small unowned items.**
- A stale comment in canopy `test_cascor_service_adapter_gate_coverage.py` (`canopy685-implementation-report.md:69`). It was never routed anywhere.
- `2026-09-23_blank_api_key_warning_mutation_check.py`: its retire condition is met, but nobody owns retiring it.
- The owner step should name juniper-recurrence as the consumer that needs the service-core release.

## Items confirmed as carried

- **Validations owed:** #690 on both commits (20:42:33Z, "my successor's first task") and #685. The judgement calls (a)–(c) match `canopy685-implementation-report.md:64-67`.
- **Fix-forward items:** F1→#685, F2, F3 plus F8, F4 as APD-CASCOR-014, F6, F7, F9 and F10 all match the bytes-compare validation.
- **Owner steps:** the lock lines (data `:88`, cascor `:63`, canopy `:79`, canopy's `<0.5.0` cap) and the possibly polluted live Sentry project.
- **CASCOR-008/-013:** held until #690 merges and validates (19:25:30Z, 20:25:20Z).
- **Coordination:** the archive header, the overlap and subset rules, the register's `fix/conditional-requests-round4-followups` files, and the two canopy ledger items.
- **Previous handoff's items:** routed to the register lane by the split (data#428 round 3, ml#2032/#2059, the register PR, the primer, `MEMORY.md`). The follow-ups became #688 and #683.
- **"Both are correct in scope"** for #689 and #440 is supported: validation line 3 and lines 96-106.
