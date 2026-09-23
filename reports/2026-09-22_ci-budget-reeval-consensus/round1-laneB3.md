# CI-budget re-evaluation -- consensus round 1, Lane B3 -- argue SHIP, and attack the soak verdict

- **Procedure**: [`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`](../../notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md)
- **Document under test**: [`HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`](../../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md) and the PR carrying it
- **Frozen at**: ml#2017 at `53d05121`
- **Archived**: the lane's final report, copied verbatim from the session transcript on
  2026-09-23. Nothing below the rule is edited; the reconciliation is the handoff's
  § Validation record 2026-09-22.

---

I ran every check in the brief. My read: ship the budget raises and the new waiter default, and add a few fixes. The "do not promote the soak" conclusion holds and is stronger than the handoff says. But four points of its supporting text need correcting before merge (A, B, C and G below).

Repo root: `/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/ancient-yawning-biscuit` (paths below are relative to it). The handoff under review is `/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/36979dd7-9695-4932-8e7f-158acf63af9c/scratchpad/round1/HANDOFF_frozen_round1.md`, a frozen copy of `HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`.

## I. The case for shipping (checked)

- **Tests pass.** At `53d05121`, `python3 -m unittest tests/test_safe_merge.py tests/test_wait_for_checks.py` gives `Ran 124 tests … OK`.
- **The refreshed spans catch the stale budgets.** In a scratch copy with data / data-client / deploy set back to 2400 / 2400 / 700, the run gives `FAILED (failures=6)`. That is exactly those three repos, at both pin sites (`KillResilienceTest` and `TimeoutSizingTest`).
- **The raises follow the owner-ratified rule.** Data's window is (2589, 6604] and data-client's is (2565, 6180], both clamped to 3300. Deploy's is (965, 1800], mid 1382, so 1400.
- **No caller relied on the old 1800 s default.** Every script that runs the waiter passes `--timeout` explicitly: `util/safe_merge.py:802`, `util/ad-hoc/2026-08-24_bot_pr_merge_sweep.py:124`, `util/ad-hoc/watch_prs_until_terminal.bash:75`. Loading `safe_merge.py` from the waiter is safe: its signal and ctypes calls sit inside functions.
- **The docs match the code.** `docs/REFERENCE.md`'s spans and budgets rows agree with `REPO_TIMEOUTS` and `MEASURED_SPANS`.

## What ml#2017 missed

- **E1 (minor): the old lockfile explanation survives in four live places.** They still say a `GITHUB_TOKEN` PR "does NOT trigger CI (GitHub's recursion guard)":
  - `docs/REFERENCE.md:3830`, a file this PR already edits;
  - `.github/workflows/release-train.yml:64-69`;
  - `.github/workflows/release-train.yml:565`, which is printed into the release-train output;
  - `notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md:982-983`.

  None mentions the cheaper fix, approving the parked runs. Fix: apply the same correction, scoped to what was measured.
- **E2 (minor): the waiter mislabels the unmeasured fallback as measured.** At `util/wait_for_checks.py:483`, `resolve_timeout('juniper-not-measured')` returns `(2400, 'measured budget for juniper-not-measured (...)')`. The test at `tests/test_wait_for_checks.py:660` checks only the seconds, so it misses this. Also, line 478 loads `safe_merge.py` without registering it in `sys.modules`: that is the known `@dataclass` trap, though the new tests would catch it.
- **E3 (minor): another script has the same flat default.** `util/ad-hoc/watch_prs_until_terminal.bash:53` defaults to 2400 s, now below 6 of the 9 budgets (it was 4). It also parses JSON out of merged stdout+stderr (`:75`, `2&gt;&amp;1`). So the obvious fix, dropping `--timeout`, would break on the new `wait budget:` stderr line.
- **E4 (minor): `ci.yml:1618-1620` still justifies the soak with "ZERO false positives".** It was not updated with the live record.
- **E5 (informational): four of nine budgets now sit at the 3300 s ceiling.** Data has 711 s of headroom and data-client 735 s. The next time either goes stale, raising cannot fix it. Nothing detects staleness, and the budgets went stale twice in 13 days.

## II. Attacking the soak conclusion

`readjudicate_soak_findings.py` rebuilt each flagged file at the flagged head and at the base named in that run's own annotation; all 30 findings reproduced. `window_structure_replay.py` replayed the 57 commits merged to main since 2026-09-18.

- **A (major): the proposed C4 repair would fail its own backtest.** The handoff (§1, non-owner item 1) says C4 should accept a heading "whose old text survives inside a renamed one". The old text survives only for #1973 and for 2 of #2009's 5 headings. For example:
  - #1976: `### 0.5 \`JuniperCascor1\` environment repair — owner has not ruled, asked 3+ times` became `### 0.5 ~~…environment repair~~ — **MOOT, CLOSED 2026-09-21**`.
  - #1983: `…two of three copies` became `…three of four copies`.
  - #1992 and #2009's `## 3.` heading had their endings replaced the same way.

  Under that rule, 4 of the 5 C4 PRs still fail. A working rule: pair each lost heading with a gained heading at the same level and leading identifier (section number, `APD-…` id, "Option A/B"); this pairs all 10 lost headings. Then flag only when some file links to the old anchor. The required link checker validates same-file anchors only (`juniper-doc-tools/juniper_doc_tools/check_doc_links.py:286-296`) and never checks `other.md#anchor` links.
- **B (major): both documented promotion recipes produce a check that can never fail.**
  - `ci.yml:1628` says to drop "the `|| true` below", but the step contains no `|| true`.
  - The walkthrough (`…CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md` §7 item 2) says to drop the trailing `exit 0`. That leaves an `if` as the last command, and it returns 0.

  `soak_step_tail_sim.py` ran the real step under `bash -eo pipefail` with a stand-in screen that exits 1. With the `exit 0` removed, the step still exits 0 and only emits the warning. Fix: end the step with `exit "$rc"`, and put this in the owner's promotion decision.
- **C (minor): one finding is counted twice.** The two #1973 entries are the same lost heading, split only because the detail text reads `31 -&gt; 38` in one run and `31 -&gt; 39` in another. The correct tally is 9 distinct findings, 2 true and 7 false, with the C4 false positives spread across 5 PRs. Also, #1983 is a content correction, not a status rename. Its in-file link (`…DEFECT-REGISTER.md:23`) was already updated at the first flagged head (`b9377f64`, read via the API) and in the squash commit `78e36d8e`.
- **D (confirmed): "would have failed 7 PRs" is correct, and understated.** All 7 false-positive PRs were flagged at their final head, and every squash commit reproduces the finding, so a required check would have blocked the merge itself. No waiver exists: neither the checker nor `util/markdown_structure_delta.py` reads any `Allow-` trailer. About 48 PRs that touched markdown merged in the window, so roughly 15% would have been blocked falsely. #1999 was red only at intermediate heads; its final head `be82d281` was clean.
- **The denominators hold.**
  - 184 soak check-runs across 184 heads, fetched with `filter=all`, so it really is once per head.
  - All 11 unreadable logs are runs cancelled by concurrency, on heads that were then superseded.
  - The 30 warnings are per run, which here is also per file.
  - The replay reproduces exactly the 8 PRs flagged at their final head and nothing else.
  - One probe defect: its list of PRs examined (13) undercounts about fourfold, because merged-PR runs carry an empty `pull_requests` field.
- **F: no false negatives found.** Across 88 markdown file changes, the checks the soak cannot run found nothing:
  - table header/delimiter cell mismatches: 0;
  - differences between CommonMark fence parsing and the soak's toggle: 0;
  - broken cross-file anchors: 0 (sibling repos and the memory directory also have no links to any renamed anchor).

  Command-looking lines not on the soak's allowlist were all prose (`for`, `while`, `set`, `source`, `kill`), apart from #1969's script. So widening the allowlist would add false positives; C2 needs a rule that recognises wrapped paragraph lines instead. I did not replay intermediate heads or list-indented fences.
- **G (minor): the walkthrough's backtest is not contradicted; it could not have seen this.** Replaying the 40 commits before ml#1944: C4 lost 0 headings, C2 flagged 0 lines, and C3 fired once, which is the backtest's one true positive. It never exercised C2 or C4, and it scored merged commits while the soak scores every pushed head. The handoff's "did not predict" should read "could not have predicted".

## My adjudication of the 10 listed findings

| # | PR / check | runs | verdict | note |
|---|---|---:|---|---|
| 1 | #1980 C2 `git).` | 7 | FP | wrapped prose; the word-boundary after `git` matches `git)` |
| 2 | #1976 C4 ×2 | 6 | FP | no links to the old anchors; old text not kept |
| 3 | #1973 C4 (31→39) | 4 | FP | status suffix added; no links |
| 4 | #2009 C4 ×5 | 3 | FP | renamed after the ruling; no links |
| 5 | #1999 C3 | 3 | TP | rows `:517-518` cut off from their table; fixed by the final head |
| 6 | #1992 C4 | 2 | FP | no links |
| 7 | #1983 C4 | 2 | FP | one real link, correctly updated |
| 8 | #2007 C2 `make` | 1 | FP | wrapped prose |
| 9 | #1973 C4 (31→38) | 1 | duplicate of #3 | same lost heading |
| 10 | #1969 C2 | 1 | TP | a shell script saved as `.md`; still on main, so the advisory warning went unread |

Total: 2 true, 7 false, 1 duplicate.

## Verdicts

- **Budget raises (data, data-client, deploy):** SHIP.
- **`MEASURED_SPANS` refresh:** SHIP. I did not re-measure the spans; that is Lane A's check.
- **Waiter default:** SHIP, with E2 fixed before or right after merge.
- **Doc corrections:** SHIP, but incomplete. Add E1 and E4; `docs/REFERENCE.md` is already in the diff.
- **Soak section of the handoff:** the "do not promote" conclusion stands and is stronger than written. HOLD the supporting text until A, B, C and G are corrected.

**Referenced:** `HANDOFF_frozen_round1.md` (copy of `HANDOFF_2026-09-09_ci-budget-instrument-corrected-and-the-fleet-slack-deficit.md`), `notes/JUNIPER_2026-09-17_JUNIPER-ML_CI-BUDGET-ARC-DECISIONS-WALKTHROUGH.md`, `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`, `notes/JUNIPER_2026-07-22_JUNIPER-ECOSYSTEM_RELEASE-TRAIN-OPERATOR-RUNBOOK.md`, `docs/REFERENCE.md`, `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`.

**Changed:** no repo file was edited. Created, uncommitted, in `util/ad-hoc/2026-09-22_ci-budget-reeval-consensus/laneB3/`:
- `readjudicate_soak_findings.py`
- `window_structure_replay.py`
- `soak_step_tail_sim.py`
