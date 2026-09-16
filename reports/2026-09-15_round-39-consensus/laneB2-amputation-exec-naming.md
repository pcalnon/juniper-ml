# Round 39, round 2 — Lane B2 (amputation, executability, naming)

- **PART 1 — AMPUTATION: FAIL.** 10 items in the LOST class; 7 DEGRADED.
- **PART 2 — EXECUTABILITY: FAIL.** §1's juniper-data block was both un-runnable as written *and*
  asserted a state that did not exist (juniper-data#404 was OPEN). The document never stated how a
  PR is opened in this fleet.
- **PART 3 — NAMING / CONVENTION: PASS WITH CORRECTIONS.** One broken internal pointer, one dangling
  path, the document never named itself, ~8 unfilenamed role references under a two-or-more rule.

Source key: **P38** = the predecessor handoff
(`HANDOFF_2026-09-09_defect-register-round-38-the-three-way-prompt-shipped-and-two-corrections-that-reversed-themselves.md`);
**DRAFT** = the first round-39 draft (`…-seven-implemented-…`).

---

## PART 1 — AMPUTATION

| # | Dropped item | Source | Class |
|---|---|---|---|
| 1 | **Signed commits are mandatory; a local `git push` cannot land a mergeable commit.** P38 §5.2 named `util/open_signed_pr.py` and the follow-up tool; the target named both only as *failure modes*, and the rule itself was gone. | P38 §5.2 | **LOST** |
| 2 | **The cascor `juniper-cascor-model` byte-mirror test.** Any edit under `src/cascor_constants/`, `candidate_unit/`, `utils/` or `log_config/` must be mirrored byte-for-byte or `juniper-cascor-model/tests/test_drift.py` fails. **Not hypothetical for X-A**: it edits `_PROJECT_API_TRUNCATABLE_GENERATORS` at line 139 of both trees. P38 also records that cascor#633 merged with that test red because `Test (Python 3.12)` is not required there. | P38 §5.3 | **LOST** |
| 3 | **The sandbox refuses shell STRUCTURE.** Loops, `&&`+heredoc, `${PIPESTATUS}`, a `git -C` whose target is computed at runtime. Confirmed live: §1's `git -C ../../../../juniper-data fetch origin` was refused. | P38 §5.1 | **LOST** |
| 4 | **The `val_ratio` / `INFRASTRUCTURE_FIELDS` finding is in no ledger.** `grep -rn "INFRASTRUCTURE_FIELDS\|val_ratio"` across `juniper-canopy/notes/` returns nothing, so the register's claim that it "belongs to the canopy ledger" is unsupported. P38's point was that the *direction* was a real choice: excluding it removes the only sidebar control over the in-loop selection split. | P38 §0.6 | **LOST** |
| 5 | **`equities_seq` has no `data_quality` consumer in the recurrence tier.** Still true: `grep -rn data_quality --include='*.py'` in juniper-recurrence → zero hits. The target dropped the item from every §0 unit and every checkbox. | P38 §0.7 | **LOST** |
| 6 | **Merge verification doctrine** — verify with `gh pr view … --json state,mergedAt,mergeCommit` **and** that the content is on `main`; a MERGED badge is not ancestry. **The cost was realised in this very document**, which asserted #404 MERGED while `gh pr view 404` returned `state: OPEN`. | P38 §2 + §5.9 | **LOST** |
| 7 | **The consensus-procedure document name**, `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md` — the target told the successor to run the protocol without naming it. | P38 §7 | **LOST** |
| 8 | **Why `tests/test_thread_handoff_archive.py` is in the §1 block** — the register cites the handoff by filename and the test requires it to exist in `prompts/thread-handoff_automated-prompts/`, which is why they must land in one PR. | P38 §1 | **LOST** |
| 9 | **The owner's partial-data spec exists verbatim only in memory** `project_partial_data_contract_arc_2026-09-05`. Directly load-bearing for D-A, whose whole content is option 3's wire form. | P38 §5.9 | **LOST** |
| 10 | **The register crosscheck's two silent-miss modes** — a WON'T FIX close with no §5.1 row, and abbreviated ids that its regex does not match; plus that it treats every id on the status line as claimed-fixed. | DRAFT §5.2 | **LOST** |
| 11 | CodeQL on subclass-registration imports: the fix that works is `importlib.import_module(...)`, a **call**, not an import. Relevant to D-E. | P38 §5.9 | DEGRADED |
| 12 | "Primary checkouts drift" — read `git show origin/main:<path>`. | P38 §5.10 | DEGRADED |
| 13 | Why canopy needs `conda run -n JuniperCanopy1`: the env's python invoked directly skips the `libtorch`-path strip hook; tests that never import torch pass either way, which is how a partial run reads healthy. | P38 §5.5 | DEGRADED |
| 14 | The CHANGELOG release-move merge doctrine and its experimental disproof. D-A edits `CHANGELOG.md`. | P38 §5.2 | DEGRADED |
| 15 | `test_shares_are_not_visible_before_they_were_filed` asserts `ages.min() >= 0`, which catches a *future* value and cannot catch a **stale** one. | P38 §5.9 | DEGRADED |
| 16 | Bandit B105 name-keying; "a delegated agent cited its own future PR number". Both reachable via `MEMORY.md`. | P38 §5.7/§5.8 | DEGRADED |
| 17 | §6's branch SHA `44de51c5`. | P38 §6 / DRAFT §6 | DEGRADED |
| 18 | The three round-38 PR worktrees, named in P38 and reduced to "the three round-38 PR worktrees". | P38 §6 | DEGRADED |
| 19 | P38 §0.2 — the cascor partial-data follow-ups PR. | P38 §0.2 | **CORRECTLY DROPPED** (cascor#640 MERGED) |
| 20 | P38 §0.5's "the empty set is still empty" and the five parked owner questions. | P38 §0.5 | **CORRECTLY DROPPED** (superseded by the thirty rulings) |
| 21 | DRAFT §5.5's `pre-commit` PATH breakage. | DRAFT §5.5 | **CORRECTLY DROPPED** — the target records the supersession and keeps the surviving half |
| 22 | P38 §0.4 — live E2E of the prompt on `equities` is impossible at canopy's defaults; workaround: `start_date` ≥ 2010 or `fundamentals_fill='drop'`. | P38 §0.4 | DEGRADED |

---

## PART 2 — EXECUTABILITY

§1 commands, run from the worktree root:

| Command | Result |
|---|---|
| `grep -cE …` | **94** — matches |
| `register_open_set.py` | `119 rows \| 94 fixed \| 25 open` — matches |
| `register_status_crosscheck.py` | 94/94/94 — AGREE |
| the three register suites | **Ran 33 tests — OK** |
| `test_thread_handoff_archive.py` | 2 tests — OK |
| `git -C ../../../../juniper-data fetch origin` | **REFUSED by the harness** — the `-C` target is computed at runtime |
| the juniper-data `grep` | Refused as written; with an absolute path returns `VERSION = "4.0.0"`, `1.0e13`, no `kept_values` — **the exact signature §1 says means you are on a commit before #404** |

**The §1 juniper-data expectation was unreachable**: #404 had not merged. §2's table row and §8's
checkbox were both false, and §0's "Eight rulings are implemented" was seven.

Per-unit start check:

| Unit | Can a fresh agent start? | What is missing |
|---|---|---|
| D-A | Yes | `docs/REFERENCE.md` / `CHANGELOG.md` unprefixed; both names exist in two repos |
| D-B | Yes | No statement of whether the counters move or are dropped from the wire — the ETag depends on it |
| D-C | Yes | The `type` URI namespace is not chosen |
| D-D | Yes | The deprecation *signal* is unstated; no file named |
| D-E | Partly | **TTL, key-store backend, and the enumeration of "every mutating route" all unspecified**; its order relative to D-B/D-F unstated |
| D-F | Yes | Collision with D-B correctly named and ordered |
| D-G | Partly | `APD-DATA-049`'s source/target cache paths only in §6; the instruments named in §5.11/§2 **do not exist in the juniper-data checkout** (unmerged branch only) |
| C-A | Yes | The `APD-ECO-003` ruling in the register still carries the over-generalised claim §0.2 corrects — a successor told "the register is the record" reads the wrong thing |
| C-B | Yes | No file list for the 43 returns; no census instrument named |
| C-C | Yes | The register carries an AST census and an `inspect.signature` parity pin, neither in the handoff; the register also records an owner **deferral** of 2026-08-26 on that row |
| X-A | Partly | **The `juniper-cascor-model` byte-mirror obligation** (PART 1 #2); and no fallback stated for juniper-data unreachable at startup |
| X-B | Yes | File named only via the register |
| X-C | Partly | **The `juniper-service-core` path is named nowhere** |
| M-A | Partly | **"the contract test" is named in neither the handoff nor the register** |

**Coverage (a strength):** the 14 units partition all 25 open rows exactly — no orphan, no
double-assignment. **Dependency ordering: executable, no deadlock.**

**How to open a PR — NOT STATED.** A fresh agent will reach for `git commit && git push`, which
cannot produce a mergeable commit. **Merge-approval policy — NOT STATED**; it reaches a successor
only through `MEMORY.md`. **Worktree rules — adequate by inheritance** from the always-loaded
`Juniper/AGENTS.md`. **Attribution trailers — not a document gap**; injected per-session.

---

## PART 3 — NAMING AND CONVENTION COMPLIANCE

Governing text: `Juniper/AGENTS.md` § Cross-Project Conventions — *every reference to a document
must carry its filename … two or more → **every** reference*; and the summary must list **by
filename** every document it created or modified.

1. **Broken internal pointer** — `(not a git repo …; §5.7)` should be **§5.8**. Every other §N
   pointer resolves.
2. **`§4.9`** used bare for a section of the register, violating the document's own rule that a bare
   §N means a section of itself.
3. **Role references without a filename** — "corrected in the register", "the register's own
   analysis", "Everything else in the register is ruled", "The row said …", "recorded in the
   register (§3)", and four more.
4. **"re-read the ruling"** — reference by implication to the `APD-RCLIENT-004` ruling.
5. **"The row said …"** — neither the id nor the file named.
6. **The document never names itself.** The changed-document list says "this document"; the string
   `HANDOFF_2026-09-15_…` appears nowhere in the file.
7. **§7 describes the consensus procedure but never names it.**
8. **`reports/2026-09-15_round-39-consensus/` does not exist.**
9. **Dangling paths** — the four `juniper-data/util/ad-hoc/2026-09-15_*.py` scripts exist only on
   the unmerged branch.
10. **`docs/REFERENCE.md` / `CHANGELOG.md`** ambiguous between two repos.
11. *(Borderline, not counted)* the declared "round 38" alias for the predecessor.

**Archive filename / `test_thread_handoff_archive.py`: PASS** — `Ran 2 tests … OK`; the name matches
`^HANDOFF_\d{4}-\d{2}-\d{2}_[A-Za-z0-9][A-Za-z0-9._-]*\.md$`.

**Word count: 3,921.** **The ~1,200-word target does not apply to the whole document** —
`notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md:99-102` says it governs the *goal
statement*, and :95-97 notes that handoffs carrying the validation apparatus occupy the top quarter
by length. **No violation.**

**Markdown links:** none in the document; all repo-relative paths are inline code and were verified
individually.

## Could not check

- The content of juniper-data#404's diff (lane A/B1 territory).
- Whether collisions exist beyond the two named — the `storage/base.py` overlap was confirmed by
  grep, but the edits were not attempted.
- Whether `tests/test_pyproject_extras.py` is in fact M-A's contract test — inference, not fact.
- Which follow-up signed-commit tool is canonical; `util/ad-hoc/2026-08-26_push_signed_fixup.py` is
  present and was read.
- P38 §0.4's canopy-defaults E2E blocker — would need a live stack.
