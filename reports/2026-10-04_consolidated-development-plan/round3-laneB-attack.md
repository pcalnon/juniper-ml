# Round 3 — Lane B (attack the round-2 corrections)

<!-- markdownlint-disable -->

> **Archived verbatim.** A round-3 validation lane report for `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md`. Its findings are dispositioned in `round3-reconciliation.md` in this directory. Only this header was added; line numbers that other reports cite in this file refer to the text without it, so add 4.

<!-- markdownlint-disable MD013 -->

- Instrument:
  - **Read**:
    - `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` v1.2.0 (sha256 `68ba9e62dbc6c803`, verified; "Lnnn" is one of its lines);
    - the diff, `round2-reconciliation.md` and `round2-lane*.md`;
    - where touched: the two `util/ad-hoc/` instruments and the cascor source.
  - **REST**, 10:30–10:51Z: recurrence, canopy#702, ml#2122/#2134/#2139 and data's `ci.yml`; gitleaks and gitleaks-action `e0c47f4f`.
  - **Not done**: no scripts, tests or host actions, and no secret read. Short forms are the plan's own.
- Entry point: the round-2 corrections (diff + reconciliation)

## Findings

| ID | Severity | Plan location (v1.2) | What the correction says | What it broke (evidence) | Proposed correction |
| --- | --- | --- | --- | --- | --- |
| R3B-01 | BLOCKER | §3 L264–267; §9 L758, L760; L460 | Pushes are gated by a default-rules scan "(plus the B9 rule once it exists)" with the probe's `--scan-dir`. §9: "Hard until XC-LEAKS lands; after that, CI covers new commits" | **B9 is optional.** R2B-01 asked for defaults + B9; nothing puts B9 before P1-09 or P1-10.<br>**Defaults miss the class.** gitleaks' generic rule (`generic.go:16-36`) has no "passphrase". B2-01 found three `PASSPHRASE=`/`SETTINGS_ENCRYPTION_KEY=` lines in row a's `A.md` and `C.md`, which P1-09 archives.<br>**The tool cannot add B9.** It passes no config (`:102`) and strips only the env vars (`:68`), so a `.gitleaks.toml` at the scratch root is loaded instead (gitleaks precedence item 4).<br>**§9's lapse.** CI scans commits that are already public (H-18), which contradicts §3's "from now on" | A §9 edge: B9 exists before P1-09/P1-10. Force `useDefault` + B9, and refuse a root config. Strike the lapse |
| R3B-02 | MAJOR | Row k L245; §3 L264; L460 | Rows a, b **and k** reach `main` through P1-09/P1-10 | Row k is transcripts.<br>H-21 (L877) forbids copying them into a repository, and the probe's docstring (`:24-26`) says never to scan them. XC-CRED records credentials inside them | P1-09 archives the lane reports' final text, extracted from the transcripts |
| R3B-03 | MAJOR | XC-LEAKS L282, L288–290; S0.2 L415 | Config PRs "go green"; a local history scan runs separately; the owner rotates | **Unordered.** Data's daily cron (`ci.yml:50`) runs a full-history scan (`index.js:176`). Its public summary links each hit as `blob/<sha>/<file>#L<line>` (`summary.js:30`). So once data's config has rules, the next run publishes those links, before any rotation.<br>**The local scan is vacuous for passphrases.** It uses defaults only, and "counts only" gives the owner nothing to rotate. It names no private sink and has no tool (`--scan-dir` is `--no-git`) | Order it: history scan (defaults + B9), then owner rotation, then data's config PR. Turn off the summary and artifact for `schedule` |
| R3B-04 | MAJOR | §5 L546–547, L556; §9 L755 | New R-RECURRENCE-SEC: "a patch for W1.14", cut at step 3 | **The chain by definition.** L547's P12 chain is "the first … recurrence … releases carrying P12 W1.x", and W1.14 is W1.x.<br>**Main's content.** `main` is 21 commits past `juniper-recurrence-v0.5.0`, including `feat` #172 and #190 (`### Added`), and L532 cuts from `origin/main`.<br>**The planned release.** P4-18 and D-4/5/6 of `extraction-P4-release-P11-k8s.md` make the next release 0.6.0 "Breaking", past ml's `<0.6.0` cap (`pyproject.toml:105`). The row is gated by none of D-6, R8 or a cap PR | The owner chooses at A1: 0.5.1 from the v0.5.0 tag (an exception to L532), or W1.14 rides the P12 chain |
| R3B-05 | MAJOR | L76–79, L161, L326; H-22 L878 | F-S10 is "recurrence 502s"; H-22 lapses "until W1.14 lands" | **The text is the data client's** (`client.py:350`).<br>**Cascor relays it.** `manager.py:4955`/`:4353` feed `routes/training.py:130` (409) and `:337` (502), and the env-var key is unstripped (`api/secrets.py:42`).<br>**The lapse is early.** Merged is not running, and the service logs carry the key too | H-22 covers every data-client consumer's bodies and logs, until the running services are fixed. Add a cascor or data-client fix. The metric becomes 3 |
| R3B-06 | MAJOR | Wave 0 L398–410 against §6 L576–587 | Rulings first: A1, part of A2, A6 and A7 | Group A is headed "before the host steps", yet A3 *is* the host steps. A4, A5, A8 and A2's O-2/O-7/O-8/O-12 get no slot. Step 6's XC-SENTRY (b) needs O13 (L298), which is in A5. No session drafts A6's retirement set | Move O13 into step 1. Schedule the rest. A session drafts A6's set |
| R3B-07 | MAJOR | §1.3 L200–201; §7.1 L668–673, L688–689 | One non-safety round at a time, three agents per round; safety rounds start freely | Rounds 1–6 are all S. With five XC-LEAKS lanes, ten rounds can overlap, with no account-wide cap: the loss `…harness-consolidated.md` L86 records.<br>The arithmetic counts 9 rounds, not 13, and "three" sittings, though the cuts need at least two | An account-wide cap that S rounds also obey; S buys queue position only. Recount |
| R3B-08 | MAJOR | XC-FLEET L314–320 | The dispositions table | Three rows are not dispositions under L320: "Fix only if wanted", "Do not merge" and "Re-run CI". ml#2122 is an open draft with 22/22 checks green, so H-1's sweeper can merge it | Close ml#2122. Give the other three rows real dispositions |
| R3B-09 | MINOR | L163; §8 L728–731; §7.2 L719 | 42 drafts "not yet triaged", target 0. ml#2139 "refuses `JuniperCascor1`" | **Drafts.** The census counts open drafts, not triage, and the fleet grew 12 → 42 in about 13 h. #2147 and #2149 edit `run_suite.py`, `run_experiment.py` and `isolated_stack.bash`, which §8 serializes without listing them.<br>**ml#2139.** Its preflight runs only in `recurrence_up`, and the ungated override re-admits what W0.2 refuses | Count dispositioned drafts. List the fleet in §8. Scope L719, and require an owner OK for the override |
| R3B-10 | MINOR | Status L7; L13; L1083; L1089 | Rounds reconciled; "as of 10:25Z"; a termination rule | The re-probe additions (F-S10, S0.11, R-RECURRENCE-SEC, H-22) sit under Round 2, though no lane saw them.<br>L1089 exempts drift from `…CONSENSUS-PROCEDURE.md` §4, yet drift added those actions, and Deviations omits the exemption.<br>The census measured only PRs, merges, releases and PyPI | Mark the additions unvalidated. Record the deviation. Narrow the "as of" claim |
| R3B-11 | MINOR | L199, L406, L416, L821, L1023, L1089; "W5.1 note" ×8 | R2B-15 rewritten "throughout" | Added lines carry bare references: "The ecosystem guide"; "Step 8's text on `main`"; `pr2115.md`, which is missing from the table; "the W5.1 note"; "The procedure's §4"; "(§11.1)". L813, L819 and L830 are unchanged | Add the filenames |
| R3B-12 | NIT | L122, L994; L335 | "seven item IDs" *(v)* | W1.14 came from P12's own plan (L124), not from validation. P6-34 is the retirement ruling, not a gate fix (`extraction-P6-perf.md` L68). A6 drops "P6 OD-12" | Count six IDs. Restore OD-12 |

## Corrections checked and sound (short)

- **XC-MEM's "over the ceiling"**: the index is 25,695 characters, and this session's loaded copy ends before its last entries.
- **The W5.1 note** is ml#2130's measurement note (`…equities-p0-executed-go-verdict-p1-next.md` L17).
- **F-S10's padding condition**: canopy#702 reproduced it with a fake key.
- **The watchdog command** matches ml#2134's body; ml#2134 touched no installer file.
- **Live counts**: the ml 28 and canopy 8 drafts are all `cursor[bot]` (the other six were not checked); cascor `95cdc562` and data's 9-ahead hold.

## Could not check

- Host state: whether the key is padded, and where cascor reads it from.
- Whether canopy relays cascor's 409 detail.
- Whether data's history holds real hits.

## What this report cannot support

- **Severities** are judgement. R3B-01 inherits R2B-01's assumption that the matches could be real.
- **Later state**: nothing after 2026-10-05T10:51Z.
- **Unchanged text**, beyond where the diff touches it.

**Changed**: this file only, `reports/2026-10-04_consolidated-development-plan/round3-laneB-attack.md`.
