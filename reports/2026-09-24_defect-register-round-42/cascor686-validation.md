<!-- Archived verbatim 2026-09-24 from subagent a133ee99474cfbe0c of session bc31e993 (final message). -->

# cascor#686 validation: 653bc3f (PR commit) and 8f28272 (PR commit merged with main)

**Verdict:** #686 does what it claims at both SHAs. The owner's ruling holds on every entry path, and all eight findings from the earlier validation are resolved or explicitly left. It still cannot merge: once main (with #685) is merged in, a required lint check fails, and neither PR fails it alone.

**State:** #686 is **not merged**, so there is no squash tree or merge SHA to check. It is OPEN at head `8f28272`, squash auto-merge was armed at 09:09:26Z, and GitHub reports it BLOCKED. Main is `d922010` (#685).

## Findings

**1. HIGH (blocks the merge; not a runtime defect): the merge with #685 makes `start_training` too complex for flake8.**
- **Where:** `src/api/lifecycle/manager.py:2542` at 8f28272.
- **What:** flake8 C901 reports complexity 16, over the limit of 15. The base scores 14, #686 alone 15, #685 alone 15. Together they reach 16.
- **Evidence:**
  - `flake8 --select=C901 --max-complexity=15` on the four trees gives 14 / 15 / 15 / **16**.
  - `gh pr checks 686`: Pre-commit fails on 3.12, 3.13 and 3.14, each with `manager.py:2542:5: C901 … (16)`. Quality Gate fails.
  - Unit Tests, Quick and Full Integration, Build, Docker and Security Scans are all skipped. All of these are required.
  - 653bc3f's own pipeline was cancelled by the merge push, so CI has never run the test suites on this PR.
  - Golden, CodeQL, Sequence Safety, Docs Links, Lockfile, Memory Budget, Conformance and the base-branch guard pass.
- **Fix:** move branches out of `start_training` rather than adding `# noqa`. Two options:
  - fold the `if dataset_shortfall is not None:` log call into `_rebind_dataset_record_locked`;
  - or have `_reapply_carried_params_locked` accept `{}` and call it unconditionally.

  The rebind must stay before the pending reload. No test pins that order (see NM11 in finding 3).

**2. LOW: an annotation from a caller's own fetch is silently dropped while another fetch's split is still loaded, and the log and status then disagree.**
- **Where:** `manager.py:2529-2532` (`if left: … return`) and `:2670`. Auto-start binds through `app.py:657-666`, which keeps any partition it doesn't supply.
- **Scenario:** a clean staged fetch is loaded, then auto-start delivers a partial train+val artifact with no test split.
- **Evidence** (`probe_s9_log.py`, 8f28272):
  - The log says `DATASET SHORTFALL: this run is training on a partial dataset…` and `DATASET IS PARTIAL: 14 of 503…`.
  - Status reports `dataset_shortfall: None` and `current_dataset: {'dataset_type':'equities','tickers':['AAPL']}` (the earlier clean fetch), with described partitions `['test']`.
  - Mutant NM4, which adopts the caller's annotation instead, survives 2472/2472. Neither behaviour is pinned.
- **Reach:** small. It needs data loaded before the boot-time auto-start binds, plus an artifact with no test split.
- **Fix:** auto-start is a fetch, so bind it wholesale the way `_reload_dataset` does. Clear partitions it doesn't supply (the cascor#582 rule), describe the ones it filled, and add a test.

**3. LOW (test gap): four mutants that break the ruling survive every unit test.**
- **NM19:** `_start_fresh_reset_locked` forgets `_described_partitions`.
- **NM20:** start-fresh clears the record.
- **NM1:** `_reload_dataset` (`:4771`) describes the artifact's keys instead of the bound tensors. A legacy train+test artifact (val promoted under `JUNIPER_CASCOR_ALLOW_MISSING_VALIDATION_SPLIT`) then loses "val".
- **NM11:** the rebind moves after the pending staged reload.
- **Evidence:**
  - At 653bc3f all four survive the 167 named tests and all 2472 in `tests/unit/api`.
  - At 8f28272 they survive 223 tests: the four shortfall files plus the three start-fresh files.
  - None is equivalent: under each one, the ruling probe flags an under-claim and a lost `current_dataset` name. For example, NM19 gives `start_fresh + inline train … sf=None cd={'dataset_type': None}` while val and test are still ds-1's.
  - No `unit/api` test combines start_fresh with the record.
- **Fix:** add these cases to `TestKeepWhileFetchedSplitsStay`:
  - start_fresh, both on retained data and with inline train;
  - a legacy artifact with promoted val, then an inline train+test start;
  - inline train plus a pending staged fetch, then a val+test start;
  - finding 2's case.

  `CHANGELOG.md:223`'s "the ruling's full matrix" overstates the coverage.

**4. LOW (item 4 with the flag off, which the implementer left open): in the default deployment an ordinary 422 is still presented as a shortfall refusal that names the flag.**
- **Where:** `manager.py:4162`.
- **Evidence:** `probe_ordinary422.py` (spiral, `n_spirals=1`) gives `flag=false: token=True … re-run with --allow-truncated-datasets (or set JUNIPER_CASCOR_ALLOW_TRUNCATED_DATASETS=true…`. Canopy then opens its partial-data prompt for a plain parameter error.
- "The list is never read" isn't the only way out. Both of juniper-data's refusal messages (`limits.py:168` and `:189`) contain `allow_truncation`, so the bare `"422"` check only adds false positives.
- **Fix:** `looks_like_shortfall = "allow_truncation" in detail or "incomplete_rows" in detail`. On a scratch copy the 167 named tests pass and the probe shows `token=False` with the flag on and off. This also covers an unreadable list followed by an ordinary 422.

**5. NIT: docs.**
- `AGENTS.md:188-189` says a 422 for an undeclared generator is a plain failure. That is only true with the flag on; CHANGELOG qualifies it, AGENTS.md doesn't.
- `AGENTS.md:192-193` and the API reference `:867` say the record clears "once train, val and test have all been replaced". It should say "all of the fetch's partitions": a train+val fetch clears once train and val are replaced.

**6. NIT (canopy side, predates this PR):** canopy's second cut point, `" The resulting dataset"` (`dashboard_manager.py:8362` at 5907713b), also removes juniper-data's own last sentence from the cap refusal (`limits.py:168`). It does this on every branch, at base too. Fix in canopy: cut only at `" To accept it,"`.

**7. NIT:** in the armed squash body, `Allow-Symbol-Loss:` sits in a paragraph before the last one, so git won't parse it as a trailer. The #678 validation saw main-verify honour the same shape.

## Attacks that did not land
- **All eight earlier findings are resolved at both SHAs.**
  - `probe_mixed`: ds-1 is kept and `current_dataset` names equities.
  - Canopy's parser, copied verbatim, returns the producer's own text on all 10 refusal branches.
  - A null stance, flag on or off, names no knob.
  - A partial listing is not memoised (`gen_calls=2`).
  - The listing client's kwargs are pinned.
  - Auto-start's refusal names only its own retry.
  - A refused artifact leaves nothing in the log.
- **The ruling over real HTTP holds.** `probe_ruling_matrix.py` ran about 60 steps with no over-claims or under-claims, and gave identical output at both SHAs. It covered:
  - inline X, X+val, X+test and all three, including across several starts, and a new fetch after partial replacement;
  - train+val and legacy train+test artifacts;
  - refused staged fetches and swaps (both the 422 and the §6.1 refusal), plus a successful swap;
  - inline data alongside a pending staged fetch, the spiral route, auto-start, `reset()`, Stop→Start and start_fresh.
- **Locking:** every read and write of `_described_partitions` happens under `_lock`, and `get_status()` never reads it.
- **Interaction with #685:**
  - After a partial fetch and a train-only start, start_fresh keeps ds-1 and `{val,test}`, and the carried params survive (32 and 60 live after the network rebuild).
  - `_start_fresh_reset_locked` touches no tensor and no record.
  - A forced failure while re-applying params leaves the record consistent.
- **Merged CHANGELOG** is well formed: one `[Unreleased]`, no lines lost (+61/−0 against base), and both PRs' entries are present verbatim. The duplicate `[0.4.0]`–`[0.7.0]` headings already exist at base. The merge is exactly the union of the two diffs.
- **Canopy compatibility:** canopy reads only `current_dataset.dataset_type` (`main.py:4104-4138`, `dashboard_manager.py:2937`). The shape is unchanged, and canopy never sends inline or spiral data to cascor, so nothing breaks. After another client's partial start, the dropdown now shows the fetch's type instead of the empty selection, which is what the ruling intends.
- The real juniper-data lists a schema for every generator (`generators.py:262`).
- The implementer's harness reproduces: 34/34 mutants killed, plus the BASE pseudo-mutant.

## Suites
| | 653bc3f | 8f28272 |
|---|---|---|
| four shortfall files | 167 passed (39/36/29/63) | 167 passed |
| plus `test_start_fresh_carries_params.py` | — | 177 passed |
| `tests/unit/api` | 2472 passed | 2482 passed |
| 24 files that import `manager.py` or `app.py`, with `--integration` | 287 passed, 16 skipped (need `--slow`) | 287 passed, 16 skipped |

**Documents referenced:** `reports/2026-09-24_defect-register-round-42/cascor678-postmerge-validation.md`, plus cascor's `AGENTS.md`, `CHANGELOG.md` and `docs/api/JUNIPER_CASCOR_API_REFERENCE.md`.

**Changed:** none; everything was read-only. Probes and logs are in `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/bc31e993-97b0-4a01-ae04-cb39593eb647/scratchpad/v686/`, which is temporary.
