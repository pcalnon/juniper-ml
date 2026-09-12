# Soak retrieval standard — the evidence, recovered

**Project**: juniper-ml
**Date**: 2026-09-08
**Status**: evidence recovered; the standard question stays with the owner
**Scope**: item E of `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_soak-arc-outstanding-work.md`

---

## 1. What this settles, and what it does not

§4.8 of `notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md`
records that two retrieval standards are live in one corpus: 8 follows scored on tool
**output**, 18 on tool **input**. The headline pointer-follow rate is therefore **60.5%**
as scored and **41.9%** if only input-scored follows count, and nobody has ratified a
standard. The 8 output-scored rows — all dated 2026-08-22 — had never been re-audited:
ml#1644's re-audit covered only the automated 2026-09-03/04 runs.

The 2026-09-07 handoff ranked recovering that evidence first, on the grounds that it is
the only outstanding item that can move the headline rate. It anticipated the answer:
*"Under the protocol's own standard (inputs ∪ results, item D) the rate stays 60.5%."*

**That expectation is not supported by the transcripts.** Applying the protocol's own
§4 definition and then checking what each hit actually *is* gives **55.8%**, below the
as-recorded rate — and the evidence recovery **strengthens** the `BET-FAILING` verdict
rather than putting it back in play.

This document does **not** re-score the ledger. Whether a filename-only hit or a
sibling-repo hit counts as a follow is precisely the standard question item E puts to
the owner, and `reports/soak/pointer_follow_soak.jsonl` is unmodified.

## 2. Both blockers were tractable

The handoff named two obstacles. Neither was a dead end.

**Blocker 1 — the screen resolved no transcript.** `SUBAGENT_DIRS` in
`util/ad-hoc/2026-08-21_soak_probe_evidence.py` named a **worktree-suffixed** project
directory (`…juniper-ml--claude-worktrees-giggly-marinating-backus`) that no longer
exists. Only that one path component was stale; the session UUID under it was always
correct, and the 128 transcript files live under the primary project directory. Fixed
here by putting the primary directory first and keeping the old entry as a fallback.
The screen now resolves and reports:

```
$ python3 util/ad-hoc/2026-08-21_soak_probe_evidence.py a6733960f4d68be8b
=== a6733960f4d6 ===
  records 35  tool_calls 12  -> RETRIEVED docs/REFERENCE.md (opened=0 via-search-output=1)
```

**Blocker 2 — the label→file mapping was "recorded nowhere".** 41 of 49 ledger rows
carry hand-written labels (`soak-A-P02`) rather than session UUIDs. The mapping is
nonetheless fully recoverable, by two disjoint mechanisms:

| row kind | key | binding |
|---|---|---|
| hand-labelled (35 valid) | each transcript's sidecar `agent-<id>.meta.json` carries a `description` **beginning with the probe id** (`"P02 assert release tag"`), and mtime orders repeat runs | nearest transcript at or before the row's `ts` |
| UUID session (8 valid) | `<uuid>.jsonl` at the top level of a project directory — the automated runs were dispatched from the `nifty-tinkering-wave` worktree, so they are not under the pilot's `subagents/` dir | exact, by filename |

**All 43 valid rows bind.** Ordinal position alone does *not* work: P02 carries two
observation rows for one run (an 08-21 miss, later invalidated, and its 08-22
re-score), so counting rows against files leaves that probe's last run unbound.

## 3. Method, and its limits

`util/ad-hoc/2026-09-08_soak_label_to_transcript.py` walks each bound transcript and
classifies **every occurrence** of `docs/REFERENCE.md` into one of four mechanisms:

| class | what it is | is it a follow? |
|---|---|---|
| `content` | the document's own text came back (`path:LINE:text` from a `grep -rn`), or it was opened by name in a tool input | yes — §4's "opened the destination, grepped it, or otherwise read it" |
| `filename` | only its **name** came back (`grep -rl`, `ls`) | no — nothing was read |
| `foreign` | a **sibling repo's** same-named file | no — a different document |
| `ledger` | the match is inside the soak ledger's own JSON | no — and it is contamination (§5) |

Per **occurrence**, not per result: one `grep -rn` result carried six occurrences of the
path in different roles, and classifying a result by its first occurrence reports
whichever happened to sort first.

**Limits.** The rater is still one (`claude-opus-5` on all 49 rows), so this replaces
prose judgement with mechanical classification but not with a second rater — the
classification *rules* remain a judgement. Counting a single `grep -rn` line as
retrieval is the reading §4's language most naturally supports and is what the existing
screen already does, but it is a reading. The `nearest` binding for the four rows in §4
was additionally confirmed by hand against each transcript's `description` and mtime.

## 4. Finding 1 — two of the eight do not survive

> **CORRECTED 2026-09-09 after Lane A review.** The first version of this section said
> **all three** P24 runs read juniper-deploy's copy, and put the mechanism-checked rate at
> 51.2%. Both were wrong, from one cause: the classifier tested the `cd` target **before**
> the per-occurrence path prefix, so it discarded the whole input when a subject worked
> from the **ecosystem parent** (`cd /…/Juniper && sed -n … juniper-ml/docs/REFERENCE.md`)
> — a directory that matches no `juniper-ml` root segment. Genuine reads of *our* file were
> thrown away. The bug was live in shipped code (`util/soak_run_probe.py`) as well as in the
> re-audit tool; both are fixed, and `tests/test_soak_run_probe.py` now pins both directions.

| | rows |
|---|---|
| hit is the document's own text | **6** |
| filename only (`grep -rln`) — never read | **1** — 2026-08-22T21:41:09 `P21-pidfile-key-prefix-guard` |
| a **sibling repo's** `docs/REFERENCE.md` | **1** — 2026-08-22T21:41:09 `P24-grafana-port-3001-deliberate` |

**Two** rows in total disagree with their recorded outcome:

| ts | probe | recorded | evidence |
|---|---|---|---|
| 2026-08-22T21:41:09 | P21 | follow | `filename=1` |
| 2026-08-22T21:41:09 | P24 | follow | `foreign=2` |

**P24 is the instructive case, and not in the way first reported.** Its pointer is
`docs/REFERENCE.md#ecosystem-compatibility`, and juniper-ml's own copy carries the fact
verbatim under [Ecosystem Compatibility](../docs/REFERENCE.md) (*"Grafana defaults to
`3001`, not `3000`, deliberately"*).

**All three runs did read juniper-deploy's copy** — that observation was right and is
unchanged. What was wrong was the *inference* drawn from it: two of the three **also** read
juniper-ml's own file, so reading the sibling did not mean failing to follow the pointer.
`soak-C-P24` went further and ran `sed -n '145,175p' juniper-ml/docs/REFERENCE.md`, opening
the destination by name. Those two are follows; only `soak-A-P24` (2026-08-22T21:41:09) has
a sibling hit and nothing else.

The underlying hazard is still real: 7 of the 8 sibling repos ship their own
`docs/REFERENCE.md` (all but juniper-recurrence, measured 2026-09-08), and a bare substring
test cannot tell them apart. But the fix for it must not be ordered so that a qualified
path loses to a neutral cwd — that trades a false positive for a false negative, which is
how 51.2% happened.

## 5. Finding 2 — the ledger is an unscreened answer sheet

**8 of the 43 runs touched `reports/soak/pointer_follow_soak.jsonl`; exactly ONE read its
contents.**

> **CORRECTED 2026-09-09 after Lane A review.** The first version said all 8 "read the
> ledger". Opening all eight shows seven saw only the **filename** — in a porcelain status
> listing, a diff stat, an `ls -t reports/*/`, or a `grep -l` file list. That is the same
> content-vs-filename distinction this document insists on for `docs/REFERENCE.md`, not
> applied to its own new measurement. The one genuine content leak is
> `P18-health-interval-non-positive` (2026-08-22), a **pilot-era manual run**. Both
> 2026-09-04 automated rows are filename sightings, so the claim that the leak is
> *demonstrated live on the automated path* is **withdrawn**. What stands: the hazard is
> real, unscreened, and reachable from any unscoped recursive grep.

The ledger records, per observation, the probe's `pointer`, its scored `outcome`, and a
`note` restating the answer in prose. A subject running an unscoped
`grep -rn <term> --include="*" .` from the repo root matches it and is shown the
previous run's answer *and* its scoring. Measured, from `P18-health-interval-non-positive`
at 2026-08-22T21:41:09:

```
"note": "CORRECT: refused to set 0, explained that a non-positive interval never
advances elapsed so the timeout is unreachable, and found the clamp plus its guard
test. RETRIEVED docs/REFERENCE.md via a directory-scoped search (via-search-output=1).",
"obs_id": "a44e03cb-…", "outcome": "follow", "pointer": "docs/REFEREN…
```

The contamination screen **cannot see this**. It checks
`ANSWER_KEY = "conf/soak_probes.json"` and `PROTOCOL_DOC = "POINTER-FOLLOW-SOAK-LEDGER"`
(the *notes* filename); the ledger's own path, `reports/soak/pointer_follow_soak.jsonl`,
matches neither.

This is the authoring rule from
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-23_memory-budget-soak-and-side-findings.md`
— *"store identifier-shaped facts in a form the subject's own grep cannot hit"* — being
violated by the instrument's own record. The affected runs:

| ts | probe | outcome |
|---|---|---|
| 2026-08-22T21:41:09 | P18-health-interval-non-positive | follow |
| 2026-08-22T21:41:09 | P20-chop-proc-root-tests-only | follow |
| 2026-08-22T21:42:29 | P16-editable-ambiguous-no-autopick | follow |
| 2026-08-22T21:46:31 | P14-per-run-timeout-ordering | source-recovered |
| 2026-08-22T21:49:43 | P16-editable-ambiguous-no-autopick | follow |
| 2026-08-22T21:50:18 | P23-reaper-over-protection-bias | source-recovered |
| 2026-09-04T09:10:51 | P06-expect-removals-scope | follow |
| 2026-09-04T09:52:49 | P19-port-check-fail-opens | source-recovered |

Two of the eight rows are 2026-09-04 automated runs (P06, P19), so the *sighting* is not
confined to the pilot era — but both are filename-only, and the single demonstrated content
leak is a pilot-era manual run. The hazard is unscreened on every path; it has been
**demonstrated** on one.

## 6. Finding 3 — what the rate becomes

| standard | rate | Wilson 95% | margin to the 0.75 boundary |
|---|---|---|---|
| as recorded | 26/43 = **60.5%** | [0.456, 0.736] | **0.0137** |
| survives a mechanism check | 24/43 = **55.8%** | [0.411, 0.696] | **0.0543** |
| input-scored only (the floor) | 18/43 = **41.9%** | [0.284, 0.567] | 0.1833 |

The middle row is the new one. It is **not a third standard**: it applies the protocol's
own §4 definition (inputs ∪ results) and then discards hits that are not the destination
document at all.

**Consequence for the verdict.** §4.5 of
`notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md` warns that
`BET-FAILING` is one observation deep, with margin **0.0137** to the boundary. Under the
mechanism check that margin becomes **0.0543** — four times larger. The verdict is more
robust than the 09-04 review could establish, and the direction is opposite to what the
handoff anticipated: recovering this evidence does not put the bet back in play.

`p̂` and the CI are unchanged for the input-only floor, so §4.7's warning stands: 95.3%
retention remains a one-way artefact and none of the three rows above rehabilitates it.

## 7. What is still the owner's call

Unchanged, and this document deliberately decides none of them:

1. **Which retrieval standard binds.** The three rows in §6 are the menu; §7.2 of the
   09-04 review is where the choice lands.
2. Whether the four §4 rows are **re-scored**. A `rescore` verb exists but
   `RESCORE_OUTCOMES = ("source-recovered",)` can only move rows in the
   retention-raising direction, so re-scoring a follow *downward* is not currently
   expressible in the ledger — that is a schema change, not a data edit.
3. Whether the ledger leak (§5) invalidates its 8 runs, as the pilot's 8 registry-leak
   runs were once discarded. This is owner decision §7.1's neighbourhood.

## 8. Reproduce

```bash
python3 util/ad-hoc/2026-09-08_soak_label_to_transcript.py reports/soak/pointer_follow_soak.jsonl
python3 util/ad-hoc/2026-09-08_soak_label_to_transcript.py reports/soak/pointer_follow_soak.jsonl \
    --only-output-scored --evidence          # the raw hit + the tool that produced it
python3 util/ad-hoc/2026-08-21_soak_probe_evidence.py a6733960f4d68be8b   # screen now resolves
python3 -m unittest tests.test_soak_probe_evidence
```

## 9. Changed files

- `util/ad-hoc/2026-09-08_soak_label_to_transcript.py` — **new**; the resolver and
  mechanism-classifying re-audit.
- `util/ad-hoc/2026-08-21_soak_probe_evidence.py` — `SUBAGENT_DIRS` now names the
  primary project directory first; the stale worktree-suffixed entry is kept as a
  fallback. No behaviour change beyond resolving transcripts that previously resolved
  to nothing; `tests/test_soak_probe_evidence.py` passes unchanged (14 tests).
- `notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md` —
  this document.

**Not changed**: `reports/soak/pointer_follow_soak.jsonl`. No probe was run.

## 10a. CORRECTION 2026-09-12 — §10's follow-up is NOT a code task. It is owner decision 7.

**§10 below told the next session that hardening `retrieval_channel` "belongs in its own PR".
That was attempted on 2026-09-12 and REFUTED by consensus. §10 is wrong, and it is wrong in a
way that reads as an invitation, so this correction sits above it.**

The attempt added a guard suppressing the pointer hit whenever the ledger's path appeared in the
same tool input. Four measured reasons it was withdrawn:

1. **It decided an owner question.** §3's table defines the `ledger` class as *"the match is
   **inside the soak ledger's own JSON**"*. In `grep -n "docs/REFERENCE.md" <ledger>` the match is
   inside a **shell command**, so that occurrence is §3's **`filename`** class — the row this
   document's §7 and the 09-09 handoff's §6 item 7 both list as **the owner's call**. The guard
   took a `filename` shape, relabelled it `ledger` on the strength of what the *other* token in
   the command was, and shipped the `filename` answer.
2. **The selector was one hard-coded path, not a principle.** Measured: the identical shape aimed
   at `README.md` or `docs/QUICK_START.md` still scored `follow`; only the literal ledger path was
   suppressed. If the principle were *"a different document was read"*, all three would agree.
3. **It destroyed the canonical positive.** `{"file_path": "docs/REFERENCE.md"}` scores a follow;
   adding a `description` field that mentions the ledger flipped it to MISS — and **every** Claude
   Code Bash/Read input carries a `description`. That is the same false-negative class as the
   `cd`-ordering bug in §4 which produced the wrong 51.2% headline.
4. **The shape it fixed does not occur.** 0 occurrences across the 49 bound transcripts. All
   **7** real ledger sightings are **result-side**, which this channel cannot see by design
   (`tests/test_soak_run_probe.py::WiredChannelSeesToolInputsOnly`). Re-scoring the whole corpus
   pre- and post-guard produced **0 flips**.

Also withdrawn: a `ledger_touched` boolean on `retrieval_channel`'s output. It is false on **8 of
8** real ledger contacts for the same result-side reason, collapses the content-vs-filename
distinction whose collapse §5's own **CORRECTED 2026-09-09** block retracted, duplicates the
three-valued `ledger_exposure()` that already ships in the screen, and printed an always-clean
contamination field into `scoring_packet.md` — the artifact that deliberately redacts corpus
progress from the scorer.

**The repo's own instrument settles the classification.** Run
`util/ad-hoc/2026-08-21_soak_probe_evidence.py::ledger_exposure` against the guard's own trigger
shape — `{"command": "grep -n docs/REFERENCE.md reports/soak/pointer_follow_soak.jsonl"}` — and it
returns **`"filename"`**, not `"content"`. The screen already in the tree classifies that shape the
way §3 defines it, and the way the withdrawn guard did not.

**What is left, and where it goes.**

| §3 row | status |
|---|---|
| `foreign` | **fixed on the WIRED path** (§4, ml#1855 + the re-fix). **NOT ported to the screen** — see below |
| `ledger` | **reported, not screened.** `ledger_exposure()` is three-valued and wired into both `scan()` branches (ml#1894), and is deliberately not folded into `contaminated` |
| `filename` | **owner decision 7.** Cannot be implemented without ruling it |

**Correction to an earlier claim in this session: "the screen's half is done" is only half true.**
`ledger_exposure()` *reports* exposure, but `scan()`'s own **retrieval verdict** (`dest_hits`,
`via_output`) is still a bare `DEST in blob` substring test, with no sibling-repo segments, no
path-token walk-back and no filename/content gating. So the screen's `retrieved` credits
`filename`, `foreign` **and** `ledger` occurrences alike. The screen is unwired, so it costs nothing
live today.

**And "simply not ported" is wrong — measured 2026-09-12, before writing any change.** The `foreign`
half looked like the one piece of §10 that is not owner-gated: document identity, already ratified
on the wired path. It is not portable, for a structural reason:

| blob, as `scan()` actually receives it | wired guard says |
|---|---|
| `tool_use` — the real P24 command `cd …/juniper-deploy && grep -rn 3001 .` | not ours *(the path never appears)* |
| **`tool_result` of that command — `docs/REFERENCE.md:88:…`, RELATIVE** | **OURS** |
| `tool_result` with a **qualified** sibling path | not ours |
| `tool_use` — genuine read of our copy | ours |

**Read row 2.** That is the only form in which the real sibling content reaches the screen, and the
guard calls it ours — because the `cd` that makes it foreign lives in a **different JSONL record**,
which `scan()` has already discarded by the time it sees the result. `_own_repo_occurrence` uses the
`cd` in the *same* tool input as context; `scan()` holds no per-record state at all.

So a straight port would suppress a qualified sibling path in a result — a shape not shown to occur
— and **miss the one instance in the corpus**. Catching row 2 needs cross-record state carried from
a `tool_use` to the `tool_result` that follows it. **That is new machinery, not a port**, and it
would be new machinery in an unwired screen for **1 sibling-naming transcript in 57**.

**Not done, deliberately.** Recorded here so the next session does not spend the same day
rediscovering it, and does not ship the port believing it closes the `foreign` row. Evidence:
`util/ad-hoc/2026-09-12_soak_foreign_screen/`.

A regression pin now guards the withdrawal:
`tests/test_soak_run_probe.py::test_naming_the_ledger_in_metadata_does_not_suppress_a_real_read`.
It was confirmed sensitive — it fails against the withdrawn guard — unlike the guard's own
"negative control", which passed against both builds and could never have failed.

Evidence: `util/ad-hoc/2026-09-12_soak_ledger_channel/` (`retrieval_channel_shapes_probe.py`,
`refutation_recheck.py`).

## 10. Follow-up not done here

The three false-positive mechanisms in §3 are defects in
`util/ad-hoc/2026-08-21_soak_probe_evidence.py`'s `scan()` and in
`util/soak_run_probe.py`'s `retrieval_channel` (the line number this cited went stale within
the day — address it by symbol). Hardening them changes screen
behaviour and needs its pinned tests updated, so it belongs in its own PR. The screen is
**unwired** (item F), so the blind spots cost nothing live today — but
`util/soak_run_probe.py` is not unwired, and its substring test is the one that scored
the three P24 rows.
