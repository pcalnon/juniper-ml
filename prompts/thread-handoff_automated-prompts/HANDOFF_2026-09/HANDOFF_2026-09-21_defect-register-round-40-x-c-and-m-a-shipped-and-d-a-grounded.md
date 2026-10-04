# HANDOFF 2026-09-21 — round 40: X-C and M-A shipped, two rows closed, and D-A grounded

Successor to
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`
(the **predecessor**; every bare "round 39" below means that file, and its **§9 is this arc's
immediate prior state** — §9.1–§9.9 were written by the session handing off here).

**Validate this document with independent agents before trusting it** (memory
`feedback_validate_handoff_prompts_independently`). Its own record is §6 — **and §6 is the one
section you must read first**, because this document's validation did NOT complete and §6 says
exactly which claims nobody attacked.

**A bare "§N" means a section OF this document.** Every reference to another file names it. This
document is
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-21_defect-register-round-40-x-c-and-m-a-shipped-and-d-a-grounded.md`.
All dates and times UTC.

**Register** (`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`): **119 rows, 97
fixed, 22 open**. Re-derive rather than trusting that line — `python3 util/ad-hoc/register_open_set.py`.

**What changed about this arc:** round 39 ended with thirty rulings taken and only eight
implemented. Two more are now implemented and closed — **X-C (`APD-CASCOR-005`)** and **M-A
(`APD-ML-001`)** — and **`APD-DATA-047` was ratified by the owner**, which was the register's last
outstanding owner decision. Every open row is now implementation work. The next item, **D-A**, is
grounded in §3 but **not started**.

---

## 0. Remaining work

Round 39's `§0` is still the map; do not re-derive it. What has changed since:

| Item | State |
|---|---|
| D-A … D-G (juniper-data) | **OPEN.** D-A grounded in §3 below, not started. D-A…D-D share `juniper_data/api/routes/datasets.py` — sequence them. |
| C-A … C-C (three clients) | **OPEN**, untouched. C-A and C-B collide on 38 `def` lines; sequence them. |
| X-A, X-B (juniper-cascor) | **OPEN.** X-A is **NOT cleanly actionable** — see §4. |
| X-C (`APD-CASCOR-005`) | **SHIPPED + CLOSED** (§1) |
| M-A (`APD-ML-001`) | **SHIPPED + CLOSED** (§2) |
| `APD-DATA-047` | **RATIFIED at `1e11`** by the owner 2026-09-21, closed as a decision |
| Round 39 §0.4's two no-row items | **STILL no register row.** Re-verified 2026-09-21: `grep -rn data_quality --include='*.py'` over juniper-recurrence is still **0**; canopy's `val_ratio` is still in `INFRASTRUCTURE_FIELDS` at `juniper-canopy/src/dataset_schema.py:115` (round 39 §0.4 says `:114` — off by one). |
| **canopy's fourth `APIKeyAuth` copy** | **NEW, and has no row** (§1). |

---

## 1. X-C shipped — and there are FOUR copies, not three

`APD-CASCOR-005`. juniper-data's non-short-circuiting `matched`-flag loop ported into both forks
the ruling named. **Merged and verified by content on `origin/main`, not by a MERGED badge:**
juniper-cascor#659 (squash `b47bd262`) → `src/api/security.py:68,72`; juniper-ml#1974 (squash
`ea24a19a`) → `juniper-service-core/juniper_service_core/security.py:73,77` plus the guard at
`tests/test_service_fork_drift.py:155`. Closed by juniper-ml#1983 (squash `78e36d8e`), five
touches — that row **has** a §3 detail entry.

**The finding that outlives the fix: there are four copies and the drift gate can only ever see
two.** `juniper-canopy/src/security.py:74` is a fourth `APIKeyAuth`, still short-circuiting and
**not fixed**. It cannot simply be added to the guard: `tests/test_service_fork_drift.py` declares
`_FORK_REPOS = ("juniper-data", "juniper-cascor")` and `test_every_guard_is_well_formed` asserts
every site's repo is a member — **so a canopy row is rejected by the gate's own structural check.**
Widening `_FORK_REPOS` would assert every existing guard against canopy too; that is a real change
with a real blast radius, not a one-line edit. **It has no register row. File one.**

Canopy diverges a second way — `:53` is `set(api_keys) if api_keys else set()`, a ternary with
no blank-key filter anywhere in the constructor (`:47-54`), where the other three carry
`{k for k in (api_keys or []) if isinstance(k, str) and k.strip()}` — and
**this is very probably NOT the auth bypass it looks like — but read §6 before relying on
it, because no lane attacked this and it is a *mechanism* claim.** Its only caller (`get_api_key_auth()`,
`src/security.py:262-267`) does `[api_key] if api_key else None`, so `""` becomes `None` and auth
is simply *disabled*. The residual whitespace-only case is env-var-only (`get_secret` strips a
secret *file* but returns `os.environ.get` raw, `src/secrets_util.py:62`/`:64`) and fails
**CLOSED**, with `enforce_auth_posture` (`src/main.py:341`) failing the boot when `require_auth`
is set. That reasoning was traced through the caller, `get_secret` and the boot check, and
not merely read off the line — but it was never independently refuted, so treat it as the best
current reading rather than a settled fact, and do not let a future summary promote it further.
Memory:
`reference_fork_drift_gate_cannot_express_canopy`.

> **Carry-forward for the next register touch, not worth a PR of its own.** The `APD-CASCOR-005`
> row in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (merged in juniper-ml#1983)
> describes canopy's `:53` as "a bare `set(api_keys)`". The line is actually the ternary quoted
> above. The substance — no blank-key filter — is right, and a reader who opens `:53` sees that
> immediately, so this changes no conclusion; it is recorded here so the next edit to that row
> tightens the quote instead of propagating it.

**No behavioural test can pin X-C, and one written to try is vacuous** — `any(...)` and the flag
loop return the same value for every input. The instrument is a SOURCE marker, and it was verified
to FAIL against the unported forks before being committed:
`JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest tests/test_service_fork_drift.py`.

---

## 2. M-A shipped — and the ruling presupposed something untrue

`APD-ML-001`, juniper-ml#1987 (merged 2026-09-21T18:49:19Z). The ruling reads "state the capping
rule; leave the pins" — but **the rule was written down nowhere.** The register carries only the
primer's claim that the pattern is "coherent even if never stated as policy". The work was to
*derive* it, not copy it. Now stated in `pyproject.toml` (block above
`[project.optional-dependencies]`) and in `tests/test_pyproject_extras.py`'s docstring:

- **ceiling** → shared libraries a consumer imports and must migrate to (`config-tools`,
  `doc-tools`, `model-core`, `service-core`, `recurrence` ×3);
- **no ceiling** → standalone applications and clients (`canopy`, `cascor`, `data`,
  `data-client`, `cascor-client`, `cascor-worker`), because capping them makes juniper-ml gate
  every sibling `0.y` release.

**Writing it down found two exceptions, both shared libraries the rule says should be capped.**
`juniper-ci-tools` was capped `<0.2.0` when its extra was added (ml#293) and **lost the ceiling in
ml#295, in the same diff that folded `ci-tools` into `[tools]`**, while `doc-tools` kept its
ceiling in that same PR. `juniper-observability` never had one. Recorded, not corrected — the
ruling forbids pin changes. So the primer's "coherent" is **qualified, not confirmed**.

"No pin changed" is proven two ways: `tests/test_pyproject_extras.py` passes with its **assertions**
untouched — the file is `+30/−0`, and every added line is inside the module docstring — and the
`pyproject.toml` diff is **+37/−0**, every added line a comment or blank. `util/ad-hoc/2026-09-21_verify_pin_ceiling_rule.py` measures the stated rule (7
capped / 8 uncapped) and carries a `--self-test` negative control.

---

## 3. D-A — grounded, NOT started. Read this before writing code.

`APD-DATA-052`. Make `allow_truncation` tri-state so a caller can refuse truncation even where the
operator enabled it. **Read memory `project_partial_data_contract_arc_2026-09-05` first** — the
owner's spec exists verbatim only there, and round 39's §0.1 paraphrases it.

**Verified against `origin/main` 2026-09-21 — exactly three `or settings.*` sites:**

```
juniper_data/generators/csv_import/generator.py:153   allow = bool(params.allow_truncation or settings.csv_import_allow_truncation)
juniper_data/generators/equities/generator.py:499     allow = bool(params.allow_truncation or settings.equities_allow_truncation)
juniper_data/generators/equities/generator.py:529     allowed = bool(params.allow_truncation or settings.equities_allow_truncation)
```

`equities/generator.py:532` is `incomplete_rows`, a **different field** — not one of the three.

**Schema, both plain `bool`:** `csv_import/params.py:67`, `equities/params.py:108`. They must
become `bool | None = None`; the site logic becomes
`settings.X if params.allow_truncation is None else params.allow_truncation`.

**Three constraints that will bite:**

1. **A `model_fields_set` presence guard does NOT work** — measured twice (round 39 §5.1).
   `bind_deployment_defaults` ends in `model_copy(update=...)`, which *adds* keys to
   `model_fields_set`, and the route binds before `generate`. This is why it is a tri-state.
2. **The memory says `or settings.*` is "a DELIBERATE privilege model — do not fix it."** That is
   **not** a contradiction of D-A: the same memory says "the real question is whether option 3
   should be a *caller* right at all", and the **owner ruled it IS** (MEMORY.md index line for
   `project_partial_data_contract_arc_2026-09-05`). D-A implements that ruling. Say so in the PR,
   or the next reader will think the memory was ignored.
3. **The test whose NAME is the old behaviour must be INVERTED, not deleted:**
   `juniper_data/tests/unit/test_csv_import_generator.py::test_request_cannot_opt_out_of_deployment_allow_truncation`.
   The half that survives: an *omitted* flag still defers to the deployment.

Also update the prose, and **round 39's §0.1 is imprecise about one of these — Lane A caught it
(§6)**. In `equities/generator.py` the sentence wraps lines **474-476** and carries markdown
emphasis: *"A client cannot opt \*out\* of the operator's choice."* In
`csv_import/generator.py` the two cited lines are **two different sentences, not one repeated
phrase**: `:145` is the tail of the `allow_truncation` OR sentence (`:142-145`) and IS in scope,
while **`:133` documents the analogous `max_bytes` clamp asymmetry, adduced by analogy — a
different field.** Round 39 §0.1 and the first draft of this section both read as though both
lines were about `allow_truncation`. **Editing `:133` as if it were would be wrong.**
Also: both param `description=` strings; `juniper-data/docs/REFERENCE.md`;
`juniper-data/CHANGELOG.md`. **Both those filenames also exist in juniper-ml** — check the repo.

---

## 4. X-A is not cleanly actionable — an owner decision is owed

`APD-CASCOR-008`. The ruling says derive the truncatable-generator set from juniper-data's
`/v1/generators`, and rejects both cheaper options. But it **does not say what cascor does when
juniper-data is unreachable at startup**, and round 39 §0.3 says that must be decided before code.
Fail closed, fail open, or cache the last-known set — ask before building. **X-B collides with
X-A** in `src/api/lifecycle/manager.py` (X-A edits the membership test near `:3876`, X-B the
`_dataset_shortfall` lifecycle at `:1243`/`:4175`), so sequencing them needs X-A settled first.

X-A is also **byte-mirrored** — round 39 §0.3 has the constant, both paths and the drift test.

---

## 4a. How work gets LANDED here — round 40's first draft dropped this entirely

**Round 39's §5.6-§5.8 carry the full mechanism and you should read them.** This section exists
because round 40's first draft omitted all of it, and Lane B caught that round 39's *own*
round-2 validation had caught the identical omission one cycle earlier. Regressing a defect a
validator already found is worse than never fixing it: the lineage looks like it has the guard.

- **A local `git push` cannot land a mergeable commit.** All nine repos have
  `required_signatures`; local signing hangs (the key needs a hardware touch), and one unsigned
  commit anywhere in a branch's history blocks the merge — squash does not rescue it.
- **Open a PR:** `python3 util/open_signed_pr.py --repo <repo> --branch <branch> --add
  LOCAL:REPOPATH --message <msg> --title <title> --body-file <path>`. Only GraphQL
  `createCommitOnBranch` signs; `PUT /contents` does not.
- **Follow-up commit:** `python3 util/ad-hoc/2026-08-26_push_signed_fixup.py`.
- **Both send WHOLE FILES.** Re-check `git log HEAD..origin/main -- <path>` immediately before
  every push or you silently revert someone else's merged change.
- **Verify a merge in two steps** — and this arc got it wrong: `util/safe_merge.py` prints the
  **HEAD** sha, not the squash commit (§6). Take the squash from
  `gh api repos/<owner>/<repo>/pulls/<N> --jq .merge_commit_sha`, then confirm the CONTENT is on
  `main`.
- **`safe_merge` can exit 0 without merging**, and an armed auto-merge on a `behind` PR waits
  forever under a `strict:true` ruleset — see §8.
- **Environments** (round 39 §5.15): juniper-data → `/opt/miniforge3/envs/JuniperData/bin/python`;
  juniper-cascor → `.../JuniperCascor1/bin/python` (**trailing `1`**); juniper-canopy → `conda run
  -n JuniperCanopy1` (invoking its python directly skips the hook that strips the Rust `libtorch`
  path). juniper-recurrence has **no** environment.
- **The sandbox refuses shell STRUCTURE** (round 39 §5.13): loops, `&&` with a heredoc,
  `${PIPESTATUS}`, unquoted vars in an option position, and any `git`/`gh` argument computed at
  runtime. Put multi-line edits in a script under `util/ad-hoc/` and run it by absolute path;
  `/tmp/` is prohibited for script source.

---

## 5. Verify starting state

From the juniper-ml worktree root:

```bash
git fetch origin
python3 util/ad-hoc/register_open_set.py
python3 util/ad-hoc/register_status_crosscheck.py
python3 -m unittest tests/test_register_status_crosscheck.py tests/test_register_open_set.py tests/test_register_close_protocol.py tests/test_thread_handoff_archive.py tests/test_service_fork_drift.py tests/test_pyproject_extras.py
python3 util/ad-hoc/2026-09-21_verify_pin_ceiling_rule.py --self-test
```

Expected: **`119 rows | 97 fixed | 22 open`**; the crosscheck prints four lines — `§4 tables`,
`§2 prose list` and `§5.1 verified` each **97**, then **`AGREE`** (it is not the single literal
string `97 / 97 / 97`); **50 tests
OK** (3 skipped — the cross-repo drift assertions, by design); self-test **PASS**. `APD-ML-001`
and `APD-CASCOR-005` must both be **absent** from the open set, and the `APD-ML` prefix should not
appear in it at all.

That `test_thread_handoff_archive.py` line is not decoration — it requires every handoff a
top-level note cites to exist in `prompts/thread-handoff_automated-prompts/`.

For juniper-data, confirm D-A's three sites are still exactly where §3 says
(**absolute paths — a worktree-isolated session refuses a computed `git -C`**):

```bash
git -C /home/pcalnon/Development/python/Juniper/juniper-data fetch origin
git -C /home/pcalnon/Development/python/Juniper/juniper-data grep -n 'or settings\.' origin/main -- 'juniper_data/generators/*'
```

---

## 6. Validation — two rounds ran, and Lane B did NOT pass this document

Procedure: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.

### Round 1 (the X-C / M-A work) — 1 of 5 lanes survived

Sized at 3 Lane A + 2 Lane B. **Four died on API rate limits and produced nothing.** Only
**Lane A3** (raw source-tree census) completed: denied the register and the handoff, it
independently reached **four** `APIKeyAuth` copies, named canopy as the only one without the
blank-key filter, stated the `_FORK_REPOS` consequence more sharply than the author had ("no
guard can reference canopy even in principle"), and established that **juniper-recurrence is a
CONSUMER of `juniper_service_core`, not a fifth copy**. Round 39 §9.7 holds the table of what
nobody attacked.

### Round 2 (this document) — Lane A verified it; Lane B found four defects

**Lane A (measurement re-creation)** re-derived §5's whole block, §3's grounding and §1/§2's
claims, and **verified every substantive one** — including by widening its own pathspec to prove
"exactly three sites" was not an artefact, confirming the recurrence zero-hit ran over a
non-empty 89-file corpus, and proving the `_FORK_REPOS` gate **by executing** a constructed
`ForkSite("juniper-canopy", ...)` rather than by reading the assertion. It found four
imprecisions, all now fixed; **one mattered** — §3 had inherited round 39 §0.1's implication that
`csv_import/generator.py:133` documents the `allow_truncation` asymmetry. It documents the
**`max_bytes`** clamp, by analogy. A D-A implementer would have edited the wrong sentence.

**Lane B (amputation / executability / false authority) did not pass it.** Three findings were
re-derived before being accepted (procedure §5.2 — a lone finding is a lead, not a fact):

1. **Two cited "squash" SHAs were HEAD shas, and neither is on `main`.** `968b9e9e` (ml#1974)
   and `435d6069` (cascor#659) are branch heads; the real merge commits are `ea24a19a` and
   `b47bd262`, re-derived with `merge-base --is-ancestor` and each PR's `merge_commit_sha`.
   **This trap is already in memory** — `reference_safe_merge_exits_zero_without_merging` says
   plainly that `util/safe_merge.py` prints the head sha, not the squash commit — and it was
   walked into anyway, inside a sentence whose whole point was "verified by content, not by a
   badge". The content claim survives (the diff between cited and actual SHA is empty, and
   content on `main` was checked separately); the *citation* was wrong. Fixed here and in round
   39 §9.8. The register cites no SHAs and is clean.
2. **The PR-opening mechanism was amputated wholesale** — no `open_signed_pr`, no
   `required_signatures`, no conda environments, no shell-structure limits, and no pointer to
   round 39 §5, which carries them. **Round 39's own round-2 validation caught this identical
   omission one cycle earlier**, and round 39 fixed it. Regressing a defect a validator already
   found is worse than never having fixed it, because the lineage then *looks* like it has the
   guard. §4a now carries the minimum and points at round 39 §5 for the rest.
3. **§9's git status was wrong twice** — the branch is `worktree-eager-seeking-milner`, not
   `main` (a worktree cannot share a branch with the primary checkout), and "carries only this
   document" was false.

A fourth finding — that §1 stated the canopy fail-closed mechanism as settled while §6 called it
unvalidated — is accepted as **framing**, and §1 is now hedged to match.

Lane B also **correctly reported the one attack that did not land**: §3's reasoning about the
memory's *"do not fix the `or settings.*`"* SURVIVED, and Lane B found the confirming passage the
author had missed — that same memory carries a later **"OWNER RULING: option 3 becomes a CALLER
right"** entry which supersedes the earlier caution and enumerates the very sites §3 lists. It
also found the memory's line numbers (`:432`/`:462`) are **stale**, and §3's re-derived
`:499`/`:529` correct.

### What remains unattacked

The canopy fail-closed mechanism, the register closes' protocol compliance, whether the guard's
two markers are defeatable, behavioural equivalence of the two loops, and the PR census — listed
in round 39 §9.7, attacked by no surviving lane. **M-A (§2) was verified by Lane A but never
adversarially attacked.** Re-run those lanes.

**Neither round passed on its first pass, and both changed this document.** That is now three
consecutive rounds in this lineage of which that is true — which is the argument for running the
lanes, not evidence that the documents are getting worse.

---

## 7. What this session did

**Changed, by filename** — juniper-ml: `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`,
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`
(§9.1–§9.9), this document, `juniper-service-core/juniper_service_core/security.py`,
`juniper-service-core/CHANGELOG.md`, `tests/test_service_fork_drift.py`, `pyproject.toml`,
`tests/test_pyproject_extras.py`, and `util/ad-hoc/`:
`2026-09-21_port_nonshortcircuit_key_compare.py`, `2026-09-21_register_close_data047_ratified.py`,
`2026-09-21_register_close_cascor005.py`, `2026-09-21_register_cascor005_sweep_followups.py`,
`2026-09-21_register_close_ml001.py`, `2026-09-21_verify_pin_ceiling_rule.py`,
`2026-09-21_wait_for_pr_merge.py`. juniper-cascor: `src/api/security.py`.
Memory: `reference_fork_drift_gate_cannot_express_canopy.md`, `MEMORY.md`.

| PR | State |
|---|---|
| juniper-cascor#659 | MERGED `b47bd262` |
| juniper-ml#1973 | MERGED `2dec7631` — `APD-DATA-047` ratified + round-39 §9 |
| juniper-ml#1974 | MERGED `ea24a19a` |
| juniper-ml#1983 | MERGED `78e36d8e` — `APD-CASCOR-005` closed |
| juniper-ml#1987 | MERGED 18:49:19Z — M-A + `APD-ML-001` closed |

---

## 8. Traps this session paid for

- **`util/safe_merge.py` exits 0 WITHOUT merging** in a contended lane (`went BEHIND while
  waiting — re-syncing` ×2, then `auto-merge net disarmed`). Read the `MERGED` line, never the
  exit code.
- **An ARMED auto-merge on a `behind` PR waits FOREVER** under a `strict:true` ruleset — all
  checks green, nothing failing, nothing happening. Arm, then `gh api -X PUT
  .../pulls/N/update-branch`. Auto-merge survives the sync. This is why
  `util/ad-hoc/2026-09-21_wait_for_pr_merge.py` signals on **timeout and close-unmerged as well
  as merge** — silence must not read as success.
- **The close protocol's sweep must be READ, not grepped, and it caught three stale sentences —
  one written by the closing script itself.** A SUPERSEDED marker anchored mid-paragraph left
  §4.3's routing note *opening* with the stale claim and saying "below" about text above it.
  Writing a correction is not placing it where the reader meets it. Also: §2's "Four groupings
  now have no open row" and §6's Confidence list — **neither names an ID, so no ID-keyed sweep
  can reach them.**
- **Renaming a §3 heading moves its anchor.** Sweep the ecosystem for referrers first (`APD-CASCOR-005`
  had exactly one, line 23 of the register) and run `juniper-check-doc-links`.
- **Run `juniper-service-core`'s suite from `juniper-service-core/`.** From the repo root,
  `test_smoke.py` fails against a stale `juniper_service_core` **0.4.0** in `JuniperCascor1`'s
  site-packages. Environment state, not repo content — pre-existing.

---

## 9. Git status

juniper-ml worktree `eager-seeking-milner`
(`juniper-ml/.claude/worktrees/eager-seeking-milner`), branch **`worktree-eager-seeking-milner`**
— *not* `main`; a worktree cannot share a branch with the primary checkout. Behind
`origin/main` (all five PRs above are merged; the register and both handoffs were refreshed from
`origin/main` before each edit).

**The working tree is NOT clean, and an earlier draft of this section wrongly said it carried
only this document.** It holds this document plus the session's `util/ad-hoc/` scripts
(untracked), and a staged `notes/` tree. That staging is an artefact of
`git checkout origin/main -- notes/`, which restages **every** notes file differing between this
worktree's stale HEAD and `origin/main` — so files from unrelated arcs (the container-registry
plan, the backup-tests note) appear staged. They are `origin/main` content, not uncommitted work
from another session, but **verify with `git status --short` rather than trusting this
paragraph**, and never `git commit -a` from here.

Worktree created this arc and **deliberately not removed** (cleanup needs the owner's explicit
signal, and `git worktree remove` deletes ignored files):
`juniper-cascor--fix--nonshortcircuit-key-compare--20260921-0846--c6c848f2`.

`MEMORY.md` is **23.5 KB against a 20 KB target** (memory `feedback_memory_index_target_is_20kb`;
a hook asks for 17.1 KB, which contradicts that recorded decision). Compaction is by **retiring
entries, never stripping hooks**, and the owner has not delegated which to retire.
