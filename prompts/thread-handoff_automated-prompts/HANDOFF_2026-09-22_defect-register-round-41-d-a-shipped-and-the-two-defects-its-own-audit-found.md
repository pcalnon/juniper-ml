# HANDOFF 2026-09-22 — round 41: D-A shipped, and the two defects its own audit found

Successor to
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-21_defect-register-round-40-x-c-and-m-a-shipped-and-d-a-grounded.md`
(the **predecessor**; every bare "round 40" below means that file). Round 39 is
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`,
and **its §0 is still the arc map — do not re-derive it.**

**Validate this document with independent agents before trusting it** (memory
`feedback_validate_handoff_prompts_independently`). Its own record is §6.

**A bare "§N" means a section OF this document.** Every reference to another file names it. This
document is
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-22_defect-register-round-41-d-a-shipped-and-the-two-defects-its-own-audit-found.md`.
All dates and times UTC.

**Register** (`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`): **121 rows, 99
fixed, 22 open**. Re-derive rather than trusting that line —
`python3 util/ad-hoc/register_open_set.py`.

**What changed about this arc.** Round 40 handed off D-A grounded but not started. **D-A
(`APD-DATA-052`) is implemented and closed.** It was the register's last ruled-but-unimplemented
row and, by round 40's §0, the largest single unit of work left in the arc. Two rows were filed
that did not exist when round 40 was written, and **neither came from a validation round** — one
is the residue of closing `APD-CASCOR-005`, the other was found by auditing D-A's own
documentation surfaces. The open count is unchanged at 22 by coincidence, not by stasis: one
closed, one filed open, one filed already-fixed.

---

## 0. Remaining work

| Item | State |
|---|---|
| **D-A** (`APD-DATA-052`) | **SHIPPED + CLOSED** (§1) |
| D-B … D-G (juniper-data) | **OPEN**, untouched. Round 39 §0 is still the map. D-B…D-D share `juniper_data/api/routes/datasets.py` — sequence them. |
| C-A … C-C (three clients) | **OPEN**, untouched. C-A and C-B collide on 38 `def` lines. |
| X-A (`APD-CASCOR-008`) | **OPEN and still NOT cleanly actionable** — round 40 §4 stands verbatim; an owner decision on the unreachable-at-startup case is owed before code. X-B collides with it. |
| **`APD-ECO-008`** | **NEW, OPEN, and needs an owner decision** (§2). Filed this round. |
| **`APD-DATA-053`** | **NEW, filed already-FIXED** (§2). |
| Round 39 §0.4's two no-row items | **STILL no register row.** Not re-probed this round. |

---

## 1. D-A shipped — and the ruling's own framing named two of three sites

`APD-DATA-052`, juniper-data#418. `allow_truncation` is `bool | None` defaulting to `None`:
`true` opts in, `false` refuses **even where the deployment opted in**, `null`/omitted defers.
Applies to `csv_import`, `equities` and `equities_seq` (which inherits `EquitiesParams` and
redeclares nothing — verified by MRO, not by reading).

**Round 40 §3 said "exactly three `or settings.*` sites" and it was right, but its framing
invited a two-site fix.** The third, `equities/generator.py::_resolve_incomplete_policy`, reads
the flag *independently of* `_resolve_bounds` and gates the unresolvable-fundamentals policy
rather than a cap. Converting only the two cap sites would have let a caller refuse an over-cap
universe **while still being served fabricated market caps** — the exact failure the
incomplete-data contract exists to prevent. `false` now closes both gates.

**The `max_bytes` clamp docstring had to be rewritten, not left alone.** It adduced
`allow_truncation`'s privilege model as the *precedent* for clamping. That premise is gone. The
clamp is unchanged and now argued on its own terms; the paragraph states the axis explicitly —
a resource bound may only be pushed toward *more* safety, which is the same direction an explicit
`false` pushes — and says "do not restore the OR by appeal to this paragraph."

**Non-vacuity is proven, and one mutation could not have done it.** `None or settings.X ==
settings.X`, so reverting the sites to the OR leaves the three deference tests green; reverting
the schemas to a plain `bool` leaves the three opt-out tests green. The two halves fail in
**opposite directions**. `juniper-data/util/ad-hoc/2026-09-22_verify_tristate_tests_are_not_vacuous.py`
runs both and asserts each is caught by exactly the tests that should see it **and by no others**.

**`test_request_cannot_opt_out_of_deployment_allow_truncation` was INVERTED, not deleted**, and
its same-file rename needed an `Allow-Symbol-Loss:` trailer — see §5.

---

## 2. The two defects the fix walked past

Both were found *while implementing D-A*, neither by a validation round. That is the finding
worth carrying: **the two defects nearest a fix were the one it did not reach and the one its own
audit walks past.**

### `APD-ECO-008` — a fourth `APIKeyAuth`, and a gate that cannot name it

Round 40 §1 flagged this and said "File one." It is filed. Re-derived for the row rather than
inherited: `juniper-canopy/src/security.py:74` is still
`any(hmac.compare_digest(api_key, k) for k in self._api_keys)`, and `:53` is
`set(api_keys) if api_keys else set()` with no blank-key filter.

**The row is filed for the gate, not the line.** `tests/test_service_fork_drift.py:59` declares
`_FORK_REPOS = ("juniper-data", "juniper-cascor")` and `test_every_guard_is_well_formed` at
`:285` asserts every site's repo is a member — so a canopy site is rejected by the gate's own
structural check and **no guard can reference canopy even in principle**. Widening the tuple
asserts all six existing guards against a repo they were never written for. **Fixing the line
alone is the cheapest option and it leaves the class open**; the row says so and parks on an
owner decision.

The `:53` divergence is recorded as **probably not an auth bypass** (its only caller maps `""` to
`None`, disabling auth; `enforce_auth_posture` fails the boot when `require_auth` is set) and
explicitly **not as settled** — no lane has ever attacked that reading. Do not let a future
summary promote it.

### `APD-DATA-053` — three merge-conflict blocks committed to `main`

`juniper-data/docs/DEVELOPER_CHEATSHEET.md` carried **nine literal `<<<<<<<` / `=======` /
`>>>>>>>` lines** on `origin/main`, rendering verbatim. All three conflicts were purely
**additive** — distinct sections and distinct table rows on each side — so nothing had to be
chosen between and no content was dropped. Fixed in juniper-data#417 (`-9 / +6`).

**The point is not the nine lines.** No check in juniper-data or juniper-ml looks for conflict
markers and markdownlint does not flag them, so the defect survived every required check on the
PR that introduced it and on every PR since. An independent lane swept all nine repos (including
diff3 `|||||||` and trailing-space variants): these were the only ones.

---

## 3. Two rotted mutation anchors in one instrument, and only one was mine

`juniper-data/util/ad-hoc/2026-09-04_apd_data_018_mutation_check.py`.

- **M3** anchored on the exact `or settings.*` line D-A deletes. Mine to fix, and predictable.
- **M2** anchored on the **pre-#372** record-boundary condition. #372 moved the trim into
  `_parse_csv_stream` and widened it with the unclosed-quote clause without re-anchoring, so
  **that arm has been dead on `main` for some time** and the matrix has been running eleven arms
  while §5.1's `APD-DATA-018` row recorded "Matrix is 12/12". Corrected in the register this
  round.

**Why it survived: the script exits 0 on a SKIPPED arm**, and one skipped line among twelve reads
as noise. I found M2 only because fixing M3 made me re-run the whole matrix. **A mutation
instrument that cannot find its own target is not a passing check** — read the arm count, never
the exit code.

---

## 4. Verify starting state

From the juniper-ml worktree root:

```bash
git fetch origin
python3 util/ad-hoc/register_open_set.py
python3 util/ad-hoc/register_status_crosscheck.py
python3 -m unittest tests/test_register_status_crosscheck.py tests/test_register_open_set.py \
    tests/test_register_close_protocol.py tests/test_thread_handoff_archive.py \
    tests/test_service_fork_drift.py tests/test_pyproject_extras.py
```

Expected: **`121 rows | 99 fixed | 22 open`**; the crosscheck prints `§4 tables` / `§2 prose list`
/ `§5.1 verified` each **99**, then **`AGREE`**. `APD-DATA-052` and `APD-DATA-053` must both be
**absent** from the open set; `APD-ECO-008` must be **present**.

For juniper-data (**absolute paths — a worktree-isolated session refuses a computed `git -C`;
`cd` to the absolute path and run plain `git`**):

```bash
cd /home/pcalnon/Development/python/Juniper/juniper-data && git fetch origin
git grep -n 'is None else params.allow_truncation' origin/main -- 'juniper_data/generators/*'   # expect 3
git grep -c 'allow_truncation or settings' origin/main -- 'juniper_data/generators/*'           # expect 0
/opt/miniforge3/envs/JuniperData/bin/python util/ad-hoc/2026-09-22_verify_tristate_tests_are_not_vacuous.py
/opt/miniforge3/envs/JuniperData/bin/python util/ad-hoc/2026-09-04_apd_data_018_mutation_check.py   # expect 12/12, NOT 11/12
```

**Run the unit suite with `-v`, not `-q`.** Under pytest 9.0.2 with this repo's `-q` addopt the
summary line is **never printed at all** — not lost to the warnings footer, absent. Grepping `-q`
output for `N passed` fails forever. `-v` restores it: **1734 passed**.

---

## 5. How work gets LANDED here

**Round 39 §5.6–§5.8 carry the full mechanism.** The minimum, plus what this round paid for:

- **A local `git push` cannot land a mergeable commit** — all nine repos have
  `required_signatures` and local signing hangs. Open a PR with
  `python3 util/open_signed_pr.py`; follow up with
  `python3 util/ad-hoc/2026-08-26_push_signed_fixup.py`.
- **Both send WHOLE FILES.** Re-check `git log HEAD..origin/main -- <path>` immediately before
  every push. **This round that was not theoretical** — see §8.
- **`--head HEAD` is a VACUOUS PASS for the sequence-safety screens.** Those tools commit
  server-side via GraphQL, so the local branch ref never advances and the screen reports
  `files_screened=0` and exits 0. Fetch the branch and pass `--head origin/<branch>`.
  A **same-file rename reports LOST** (cross-file reports RELOCATED) and needs
  `Allow-Symbol-Loss: <Class>.<name>` in a **commit body**.
- **Environments**: juniper-data → `/opt/miniforge3/envs/JuniperData/bin/python`; juniper-cascor →
  `.../JuniperCascor1/bin/python` (**trailing `1`**); juniper-canopy → `conda run -n JuniperCanopy1`.
  juniper-recurrence has none.
- **The sandbox refuses shell STRUCTURE**: loops, `&&` with a heredoc, unquoted vars in an option
  position, and any `git`/`gh` argument computed at runtime (`git -C <computed>` is refused —
  `cd <absolute> && git …` works). Put multi-line edits in a script under `util/ad-hoc/`.

---

## 6. Validation — two lanes, and one of them refuted a claim of mine

Procedure: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.
Both lanes completed. **Both independently found the same P1 from opposite directions**, which is
the procedure working rather than redundancy.

**Lane A (measurement re-creation)** confirmed all seven claims it was given and **refuted one
sub-claim by execution**: "No `dataset_id` churn … *and it mints no artifact at all*." The churn
half survives — 12/12 non-`false` rows hash byte-identically, measured by materialising
`origin/main`'s source into a separate tree. The trailing clause does not: with an **under-cap,
complete** source, deployment ON and explicit `false`, both versions *succeed* with **different
ids**, because the flag is hashed even when behaviourally inert. It appeared in four places, all
corrected. Lane A also caught **its own** instrument being non-discriminating first — `csv_import`
binds `get_settings` at module scope, so patching `juniper_data.api.settings.get_settings` never
reached it and every csv row silently scored deployment-off.

**Lane B (amputation / executability / false authority)** found that the "found every surface"
claim **stopped at the repo boundary**: juniper-cascor carried six surviving statements of the
reversed rule, one a **runtime operator-facing string** rendered by canopy, plus three test
docstrings; juniper-ml's own always-loaded docs carried six more. It also found
`juniper-data/AGENTS.md:377` — the `docs/REFERENCE.md` *copy* of that env-var row had been fixed
and the *original* missed. All corrected.

**Eleven attacks did not land** and are recorded as survivals: the owner-ruling quote, canopy#605,
the non-vacuity harness (Lane B re-ran it independently, exit 0, line-for-line match), the ruff
figures, the memory-budget headroom, and #417's completeness and content-preservation.

**What remains unattacked**: the canopy fail-closed mechanism (still, three rounds running); the
register closes' protocol compliance this round; whether `APD-ECO-008`'s gate analysis has a
cheaper option nobody proposed. **Neither lane attacked the register edit itself.**

---

## 7. What this session did

**Changed, by filename** — juniper-data: `juniper_data/generators/csv_import/params.py`,
`juniper_data/generators/csv_import/generator.py`, `juniper_data/generators/equities/params.py`,
`juniper_data/generators/equities/generator.py`,
`juniper_data/generators/equities_seq/generator.py`,
`juniper_data/tests/unit/test_csv_import_generator.py`,
`juniper_data/tests/unit/test_equities_generator.py`,
`juniper_data/tests/unit/test_equities_seq_deployment_policy.py`, `AGENTS.md`, `CHANGELOG.md`,
`docs/REFERENCE.md`, `docs/USER_MANUAL.md`, `docs/DEVELOPER_CHEATSHEET.md`,
`docs/api/JUNIPER_DATA_API.md`, `util/ad-hoc/2026-09-22_verify_tristate_tests_are_not_vacuous.py`
(new), `util/ad-hoc/2026-09-04_apd_data_018_mutation_check.py`.
juniper-cascor: `src/api/lifecycle/manager.py`,
`src/cascor_constants/constants_api/constants_api_defaults.py`,
`juniper-cascor-model/cascor_constants/constants_api/constants_api_defaults.py`,
`src/tests/unit/api/test_allow_truncated_datasets.py`,
`src/tests/unit/api/test_auto_start_shortfall.py`.
juniper-ml: `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, `docs/REFERENCE.md`,
`docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`,
`util/ad-hoc/2026-09-22_register_close_data052_and_file_two.py` (new), this document.
Memory: `reference_sequence_safety_local_repro.md`.

| PR | State |
|---|---|
| juniper-data#417 | conflict markers — see §9 for final state |
| juniper-data#418 | D-A tri-state — see §9 |
| juniper-cascor (prose) | prepared, opened after #418 |
| juniper-ml (register) | prepared, opened after #418 |

---

## 8. Traps this session paid for

- **A RELEASE was cut under an open PR, two minutes after it opened.** juniper-data#416 cut
  v0.15.0, emptying `[Unreleased]` into `## [0.15.0]` and bumping `AGENTS.md`. Because
  `open_signed_pr` sends whole files, the stale branch copies would have **reverted the release**
  — and the CHANGELOG would have auto-merged with **no conflict**, filing the new bullet under a
  released heading whose GitHub Release notes are rendered from that section and are **not
  re-cuttable**. AGENTS.md conflicted and CHANGELOG.md did not, so the resolver's attention is
  drawn to the wrong file. Both lanes found this independently.
- **A duplicate `### Changed` heading was 11 minutes from happening.** #415 added one under
  `[Unreleased]`; appending to it was correct until #416 moved it. This is the ml#1966 defect
  shape — a second category heading silently swallows bullets. **Re-read the CHANGELOG's heading
  structure immediately before writing, not from memory of it.**
- **`pgrep -f <pattern>` matches the WAITING process's own command line.** Every
  `until ! pgrep -f <script>` waiter contained that literal string, saw itself, and could never
  fire; it also inflated the process count with my own waiters, which read as the job spawning
  children. Wait on a **PID** (`while kill -0 <pid>`), not a name.
- **A mutation script mutates the working tree while it runs.** Do not push, commit or edit that
  worktree until it exits — a push mid-run captures mutated source.
- **Five register table rows had an unescaped `|` splitting a cell** (one mine, four
  pre-existing). A naive cell-count check also mis-flags rows containing a correctly escaped
  `\|`, so the checker must be escape-aware.
- **An open post-primer row needs a park/actionable sentence**, or it sits in limbo; every other
  open post-primer row had one and the newly filed `APD-ECO-008` did not until it was added.

---

## 9. Git status

juniper-ml worktree `fluffy-crunching-wadler`
(`juniper-ml/.claude/worktrees/fluffy-crunching-wadler`), branch **`worktree-fluffy-crunching-wadler`**
— *not* `main`; a worktree cannot share a branch with the primary checkout. **Verify with
`git status --short` rather than trusting this paragraph.**

Worktrees created this arc and **deliberately not removed** (cleanup needs the owner's explicit
signal, and `git worktree remove` deletes ignored files):

- `juniper-data--feature--tri-state-allow-truncation--20260922-0753--e8db3ba6`
- `juniper-data--fix--cheatsheet-conflict-markers--20260922-0820--e8db3ba6`
- `juniper-cascor--docs--tri-state-truncation-prose--20260922-0822--8065ca0f`

**The two juniper-data worktree names carry the SHA `e8db3ba6`, which was `origin/main` when they
were created. It is now `1aaeedce`** — the directory name is a creation-time stamp, not a base
pointer, and this arc is a standing example of why you must not read it as one.

**juniper-data `AGENTS.md` has ~486 chars of memory-budget headroom** (26,479 / 26,965). The next
author adding a hazard there must ratchet something out first.

`MEMORY.md` was **23.5 KB against a 20 KB target** at round 40 and is being edited concurrently by
other sessions (memory `reference_memory_md_concurrent_edits`). Compaction is by **retiring
entries, never stripping hooks**, and the owner has not delegated which to retire.
