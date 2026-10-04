# HANDOFF 2026-09-09 — pointer-follow soak: evidence recovered, predictors refuted, four items still open

**Validated by independent agent consensus before archiving** (procedure
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`).
§10 records what validation changed and what this document still cannot support.

State re-derived 2026-09-09. `origin/main` moves several times an hour; **treat every SHA
here as advisory and re-run §9** rather than trusting a pin.

## 0. The arc's position

`main` is **`BET-FAILING seeded=43/35 rate=60.5% ci=[0.456, 0.736]`**, `status` exits **1**,
and `util/soak_run_probe.py` refuses every real run without `--force`.

A mechanism re-audit of all 43 transcripts
(`notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md`) puts the
rate at **24/43 = 55.8%, CI [0.411, 0.696]**, margin to the boundary **0.0543**. The
predecessor handoff
(`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_soak-arc-outstanding-work.md`)
expected the rate to *hold* at 60.5% under the protocol's own standard; that expectation is
refuted.

> **THE RE-AUDIT IS NOT THE VERDICT, AND DOES NOT RESCUE §4.5.** The ledger is unmodified,
> so `status` still computes **26/43, upper 0.7363, margin 0.0137**. §4.5 of
> `notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md` — *the verdict
> is one observation deep* — **still binds on the operative number**: re-derived with the
> repo's own `wilson()`, **27/43 gives upper 0.7562, which is NOT terminal**. One row
> re-scored the other way flips the verdict. §4.5's other half also stands and is now
> doubly relevant: the verdict was produced by ml#1644's own channel fix reclassifying P15,
> and ml#1855 plus the ordering re-fix in §3.E have moved the channel *again*.
> 55.8% is a better estimate of the same quantity; it is not a more stable one.

Four qualifications bind, all from
`notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md`:

- **§4.5 — one observation deep.** See the box above.
- **§4.6 — neither corpus is a clean read, and NEITHER ERA IS TERMINAL.** Split as §15.4 of
  `notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` requires:
  **pre-intervention 24/35 = 68.6% [0.520, 0.814] — not terminal**; **post-intervention
  2/8 = 25.0% [0.071, 0.591]**, whose `IN-PROGRESS` is an n-gate, not a pass. The terminal
  verdict exists **only because of the pooling §15.4 forbids**. §15.4 also says the four
  rung-1 probes are the only ones it touches — yet **4 of the 8 post-intervention runs are
  on probes rung 1 never touched**.
- **§4.7 — 95.3% retention is a one-way artefact.** `RESCORE_OUTCOMES = ("source-recovered",)`
  can only raise it; the corpus was **74.4%** as originally recorded. Never quote 95.3% bare.
- **§4.1 — the n≈8–10 campaign cannot resolve its targets.** P23 needs n≥31. Inside 8–10 the
  Wilson resolving threshold never leaves `k≤1`, so runs 9 and 10 *lower* the chance of an
  answer.

**Do not `--force` past the verdict.** Whether the per-probe campaign runs at all is owner
decision §7.6 of the 09-04 consensus document.

## 1. What to do first

### 1.0 Git status at handoff — READ THIS BEFORE ANYTHING ELSE

Branch **`handoff-work`**, based on `origin/main`. **The corrections this document reports
are IN A PR, not on `main` at the time of writing.** Until it merges, a successor who runs
§9 against `main` will see the *old* numbers and conclude this document is wrong:

| on `main` before the PR lands | this document says |
|---|---|
| `docs/REFERENCE.md`: 22/43 = 51.2%, "None excludes 50%", `wilson(0,3)` upper `0.562` | 24/43 = 55.8%, P15/P19 **do** exclude 50%, upper `0.561` |
| `…SOAK-STRATUM-PREDICTOR-ANALYSIS.md`: `13951/20000 = 69.8%` | 68.1%, from the shipped tool |
| `util/soak_run_probe.py`: the `cd`-before-prefix ordering bug, **live on the scoring path** | fixed, pinned both directions |

**FIRST ACTION for a successor: confirm the archive PR merged** (`gh pr list --state merged
--search soak`). If it did not, land it — that is the one genuinely time-critical item here,
and §9's `expect none` for open soak PRs only holds afterwards.

### 1.1 Then, the work itself

**Nothing else is time-critical, and the systemd units are still not installed**
(`systemctl --user is-enabled juniper-soak-probe.timer` → `not-found`). The arc is blocked on
**owner decisions (§6)**, not on engineering.

If work proceeds before those are settled, this order is defensible:

1. **The predictor gap (§4)** — the design doc of record calls it *"the actual blocker to
   decision support"*, and refuting three candidates did **not** close it. It is first on
   value; it is gated behind a registry change (§6.1), which is why the engineering items
   below can proceed in parallel.
2. **Item A — the stopping rule fails open** (§3.A). Fix direction verified this session,
   including which pins it must deliberately invert; still unwritten. Dormant only while the
   units stay uninstalled.
3. **Item F′ — screen the ledger** (§3.F′). The hazard is real and unscreened on every path,
   though demonstrated only once, on a pilot-era manual run.
4. **Harden the wired channel** (§3.E, "follow-up not done"). Two false-positive mechanisms
   remain in `util/soak_run_probe.py` — the path that scores real runs, not the unwired
   screen. Its own note says this belongs in its own PR.
5. **The 10 unexplained pilot runs** (§5) — 17.5% of the pilot's probe runs, absent from the
   corpus with no recorded basis. A selection question upstream of every rate here.
6. **Item H — P06's discriminator** (§3.H), if §6.4 is ruled.
7. **`AGENTS.md` lists 9 of the 12 soak suites** (§3.K) — cheap, operator-facing.

## 2. State, verified 2026-09-09

| fact | value |
|---|---|
| ledger | 64 records → 49 observations / **43 valid** (6 invalidate, 9 rescore) |
| verdict | `BET-FAILING`, exit **1** |
| mechanism-checked rate | **24/43 = 55.8%**, CI [0.411, 0.696] |
| newest observation | `2026-09-04T09:55:27Z` (P21) — **no probe has run since** |
| post-intervention coverage | 8 runs over 7 of 15 probes; 8 probes at zero |
| systemd units | **not installed**; `logs/soak_probe_failures.log` does not exist |
| open PRs touching soak | **none** |
| soak suites | **12**, all wired in `.github/workflows/ci.yml`; **281** tests green |
| `MEMORY.md` | 153 lines / 147 rows, 19,759 B; headroom 5,241; runway **7.1 days**. Quote `util/memory_index_check.py`, never this row |

## 3. Open work

### A. The stopping rule fails open — verified, unwritten

`util/soak_run_probe.py` never reads `st.returncode`, and `verdict_is_terminal` tests only
`("BET-FAILING", "HOLDS-AT-")`, so `NO-DATA`, `DEGRADED`, `NO-SEEDED-DATA` and `""` all pass
the spend control.

**Both obvious fixes are wrong, and all three claims were re-measured this session:**

| probe | measured rc |
|---|---|
| real crash (`--ledger <a directory>` → `IsADirectoryError`) | **1**, not 2 |
| argparse misuse (`status --probes /nonexistent.json`) | **2** — same code as a degraded ledger |
| readable-but-EMPTY ledger | verdict `NO-DATA`, rc **2** |

So `if st.returncode == 2` misses the stated hazard, and keying on truthiness refuses every
escalated soak. **The fix that works**: refuse on the token set **including `""`** —
`{"", "NO-DATA", "DEGRADED", "NO-SEEDED-DATA"}` — **and preserve the `--dry-run` exemption**
(`refuses_terminal_verdict` already carries it). Put it in the *refusal* predicate, not in
`verdict_is_terminal`, or you break the `VerdictIsTerminalPrefixOnly` pins for no reason.

**The predecessor said "the test suite cannot tell the correct fix from the bug — the
stopping-rule suite stubs `ledger_rc=0`". That is wrong and was inherited unchecked.**
`tests/test_soak_run_probe_stopping_rule.py` carries **six** non-zero stubs (`ledger_rc=1`
×4, `ledger_rc=2` ×2); `rc=0` is only the `_invoke` helper's default. The suite **does**
discriminate, and the two candidate fixes have different signatures: `if st.returncode`
reddens `test_inconclusive_with_ledger_exit_1_does_not_refuse`, while the token-set fix
reddens `test_degraded_fails_open_on_a_real_run` and `test_a_ledger_tool_crash_fails_open`.
**Those two are deliberate pins** — inverting them is part of the work, not a surprise.

The end-to-end control that discriminates is a **readable but EMPTY** ledger, where the
correct fix leaves `--dry-run` at **rc 0** and the ml#1690 bug gives **rc 2 with empty
stdout**. Do *not* use an unreadable ledger: a correct fix returns 1 there.

**Bundled, same cause**: `util/systemd/juniper-soak-probe.service` is `Type=oneshot` with no
`SuccessExitStatus=`, so once installed every refusal writes a strike.
`SuccessExitStatus=2` is **not** free — argparse also exits 2, so a typo in `ExecStart=`
would read as success forever. **The alternative, and its price:** make the guard exit **0**
when it refuses by design. That costs **six `assertEqual(rc, 2)` sites** across the soak
suites. No test parses the unit file at all, so nothing catches a wrong choice there.

### B/C. Picker and stopper read different corpora; `analyse()` has no era filter

`util/soak_next_probe.py` filters to post-intervention rows; the stopper reads the **pooled**
verdict. Both are now documented in `docs/REFERENCE.md`, including the danger: wiring the
stopper to the post-only corpus makes the spend control stop refusing — **~27 further billed
runs with no `--force`** — because that slice's `IN-PROGRESS` fires on an **OR** of two n-gates —
`runs < 35` **or** `distinct probes < 15` — and at 8 runs over 7 probes **both** fire,
before any test. **Choosing the corpus IS owner
decision §6.3.**

`util/soak_ledger.py` `analyse(rows, bad_lines)` structurally cannot honour §15.4, and
`tests/test_soak_analyse_date_pool.py` pins the signature as exactly `["rows","bad_lines"]`
**and enumerates `since|until|after|split|cutoff|ts` as forbidden**. Building an era
parameter is inert until a caller passes it, so "fix C" either ships nothing or *is* §6.3.
**Say which you did.**

### D. The instrument still cannot see half of a FOLLOW

`parse_events` captures only `tool_use`; `grep -rn tool_result` across the three soak scripts
→ **0**. §4 of `notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` defines
FOLLOW as "opened the destination, **grepped it**, or otherwise read it" and scores from the
tool log — inputs **and** results. The capability exists, unwired, in
`util/ad-hoc/2026-08-21_soak_probe_evidence.py`. Adding it changes the standard, so it is
§6.1's neighbourhood, not a plumbing fix.

### E. Two retrieval standards — evidence RECOVERED, standard still unratified

Both blockers the predecessor called hard were tractable, and both are now solved in-tree:

- `SUBAGENT_DIRS` had one stale **project-dir** component; fixed, and the screen resolves.
- The label→file mapping believed "recorded nowhere" is recoverable: each transcript's
  sidecar `agent-<id>.meta.json` carries a `description` that **begins with the probe id**,
  and mtime orders repeat runs. **All 43 valid rows bind**
  (`util/ad-hoc/2026-09-08_soak_label_to_transcript.py`).

The re-audit found **three mechanisms by which a hit is not retrieval**. One is fixed; two are
open:

| mechanism | status |
|---|---|
| a **sibling repo's** `docs/REFERENCE.md` (7 of 8 siblings ship one; 8 repos including ml) | **FIXED** — ml#1855, **re-fixed** for the ordering bug below |
| a `grep -rln` **filename list** (nothing read) | **OPEN** — this is the standard question |
| the **soak ledger's own note** | **OPEN** — see F′ |

**Two rows disagree with their recorded outcome** (1× P24 genuinely foreign, 1× P21
filename-only). They are candidates, not re-scorings — and **re-scoring a follow *downward*
is not expressible**: `RESCORE_OUTCOMES = ("source-recovered",)` with `choices=` bound to it.
That is a schema change, not a data edit.

> **THE SIBLING-REPO FIX HAD A FALSE-NEGATIVE BUG, FOUND BY THIS HANDOFF'S OWN VALIDATION
> AND FIXED HERE.** `_own_repo_occurrence` tested the `cd` target **before** the
> per-occurrence path prefix, so a subject working from the **ecosystem parent**
> (`cd /…/Juniper && sed -n … juniper-ml/docs/REFERENCE.md`) had genuine reads of *our* file
> discarded — the parent directory matches no `juniper-ml` root segment. It was live in
> `util/soak_run_probe.py`, i.e. on the automated scoring path, and it is what produced the
> original **51.2%** headline (true figure **55.8%**). An explicitly qualified path now
> outranks the cwd in both directions, and `tests/test_soak_run_probe.py` pins both.
> **Generalise it:** when a check has a specific signal and a contextual one, the specific
> signal must be consulted first, or the fix trades a false positive for a false negative.

### F′. NEW — the ledger is an unscreened answer sheet (hazard real, exposure smaller than first stated)

**8 of the 43 runs touched `reports/soak/pointer_follow_soak.jsonl`; exactly ONE read its
contents.** It records, per observation, the probe's `pointer`, its scored `outcome`, and a
`note` restating the answer in prose, so an unscoped `grep -rn <term> --include="*" .` shows
a subject the previous run's answer *and* its scoring. That is what happened to
`P18-health-interval-non-positive` on 2026-08-22.

**The other seven saw only the FILENAME** — in a porcelain status listing, a diff stat, an
`ls -t reports/*/`, or a `grep -l` list. Two of the eight are 2026-09-04 automated runs (P06,
P19), but **both are filename sightings**, so the claim that the leak is *demonstrated live
on the automated path* is **withdrawn**. The hazard is unscreened on every path; it has been
demonstrated on one, pilot-era, manual.

Applying the content-vs-filename distinction to this measurement is exactly what the
re-audit demands for `docs/REFERENCE.md`; the first version of both documents did not.

The contamination screen **cannot see any of it**: it checks
`ANSWER_KEY = "conf/soak_probes.json"` and `PROTOCOL_DOC = "POINTER-FOLLOW-SOAK-LEDGER"`
(the *notes* filename); the ledger's own path matches neither. This is the authoring rule
from
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-23_memory-budget-soak-and-side-findings.md`
— *"store identifier-shaped facts in a form the subject's own grep cannot hit"* — violated
by the instrument's own record.

Item F's original half also stands: the screen is **unwired**. `conf/soak_probes.json`'s
`_README` says scoring MUST run it; nothing in the three soak scripts references it.

**Follow-up NOT done, and it is on the wired path.** §10 of
`notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md` records
that the remaining false-positive mechanisms are **code defects**, in that screen's `scan()`
and in `util/soak_run_probe.py`'s channel — and that hardening them "belongs in its own PR".
The screen being unwired costs nothing today; `util/soak_run_probe.py` is **not** unwired,
and its test is the one that scored the P24 rows. Do not let §3.E's framing of these as
*standard* questions hide that one of them is a code-hardening task on the scoring path.

### G/H. Instrument validity; P06's discriminator

Unchanged. All 15 probes point at `docs/REFERENCE.md`, differing only by `#anchor`. P06's
discriminator still under-specifies (§9.6 of
`notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md`), and the
three-ways-invalid taxonomy **has been re-homed** — the predecessor said it had not, and that
was stale. It is in the protocol of record:
`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md:679` ("Three distinct ways
a probe can be invalid") and `:672` for the identifier-shaped-facts authoring rule. **No
re-homing task remains**; the 08-23 handoff is kept in §8 as provenance, not as a to-do.

### I. `BET-FAILING`'s prescribed action has still never been carried out

`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` says **"Revisit owner
decision #7. Never re-inline."** Decision #7 is at
`notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md:654`, deferred *"revisit
only if the P3 soak shows a real pointer-follow problem."* **That trigger fired on 2026-09-07.**
Verified 2026-09-09: neither document has been substantively touched (the plan's last commit
is an unrelated fleet-docs consolidation), and every `status` prints the instruction.

### J. `docs/REFERENCE.md` — DONE this session (ml#1857)

Verdict block, era table, per-probe intervals, the retrieval-channel description, two further
copies in the utility reference, the operator loop, and the `p = 0.0017` mislabelling. The
file now matches `util/soak_ledger.py status` exactly.

### K. `AGENTS.md` lists 9 of the 12 soak suites

Verified by set difference: `test_soak_ledger`, `test_soak_next_probe`, `test_soak_run_probe`
are in `.github/workflows/ci.yml` and missing from the operator list.

## 3a. `MEMORY.md` — the intervention under test keeps eroding

**Carried forward from §4 of the predecessor handoff, and it has got worse.** This is the
treatment the whole soak measures; every probe run is scored against whatever index state its
parent session was served.

Measured 2026-09-09: **147 rows, 109 with an empty hook**. Of the four rung-1 rows — the
facts this soak was built to measure — **three now carry no hook at all**:

| row | hook |
|---|---|
| Port check fail-opens | `— missing \`ss\` reads "free"` (already reduced; lost `; clean ≠ proof`) |
| **Per-run timeout ordering** | **none** — the predecessor recorded this one's hook as *surviving*; it has since been lost |
| Reaper over-protects | none |
| Diverging worktree | none |

**Consequence, stated conservatively:** any probe run from here measures a different index
state from the 8 post-intervention runs already recorded. Treat pre-/post-prune as a further
era when interpreting, and record which side a run falls on.

**What decides the side is the PARENT session's start time, not the run's.** §17 of
`notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` establishes that memory
context is a snapshot taken when the parent session starts, so a probe dispatched from an old
session measures the old index while `MEMORY.md` on disk is the new one. **The ledger has no
field for this**, and building one is unclaimed work.

**Do NOT "restore the hooks".** The prior text for most rows exists nowhere; §17 means a
restore-then-run cannot measure its own restoration; and — the operational trap —
`util/systemd/juniper-soak-probe.path:29` carries
`PathChanged=…/memory/MEMORY.md`, so **on a host with the units installed, editing this file
fires a probe run**. It is not watched on *this* host only because nothing is installed.

`util/memory_index_check.py` is the tool: headroom, runway, hook-size errors.

## 4. §8.2's predictor gap — three candidates refuted, gap OPEN

`notes/JUNIPER_2026-09-09_JUNIPER-ML_SOAK-STRATUM-PREDICTOR-ANALYSIS.md` tested all three
candidates §8.2 of `notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md`
named. **All three fail** — and the null is readable, because at **4 vs 8** probes a perfect
split would give Fisher p = **0.0020** and one discordant probe still 0.0182. A predictor that
worked would have been found. (Best candidate: `discriminator_is_refusal`, p = 0.2081.)

**Do not re-derive the grouped-strata contrast.** An earlier draft reported that never-follow
and always-follow have disjoint Wilson intervals and called it evidence. It is **circular** —
the groups are defined by the outcomes. Under the null, noise reproduces it in **68.1% of
trials**; run `--validate` and quote what it prints, because the analysis note briefly carried
a figure from an uncommitted draft that the shipped, seeded tool does not produce.

What survives is the heterogeneity test, which partitions nothing and is calibrated (p roughly
uniform on synthetic null data), giving **0 hits in 200,000 shuffles** against the design
conversation's mislabelled `0.0017`. **Quote that as a floor with its draw count, not as a
measurement**: `permutation_p` returns `(hits+1)/(draws+1)`, so 200,000 draws floors at
≈5e-6 and the default 20,000 floors at 5e-5 — an order of magnitude apart for the same data.

**Testing any new predictor needs NEW probe ids.** Registry rule 1 in `conf/soak_probes.json`
freezes the 15: *"Add a new probe with a new id; never edit a run one."* That is a registry
change — §6.1's neighbourhood.

## 5. What this evidence CANNOT support

- **The organic arm has never run.** `arm` is `"seeded"` in all 49 rows. Every claim is single-arm.
- **One rater.** `scored_by` is `claude-opus-5` in all 49; no inter-rater reliability, and items
  D/E turn on scoring judgement. The mechanism re-audit replaces prose judgement with
  mechanical classification, **not** with a second rater — the classification *rules* are still
  one judgement.
- **`pointer_defects = 0`** has never had an input that could make it non-zero.
- **`p = 0.0017` is still mislabelled where it lives.** `docs/REFERENCE.md` now flags it, but
  the source — `notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md:423`
  — still reads `permutation p-value = 0.0017` uncorrected. It is a parametric bootstrap.
  **Fixing that document is unclaimed work**; §3.J's "DONE" covers only the reference.
- **Which model answered any given probe is unrecorded.** §7 of
  `notes/JUNIPER_2026-09-02_JUNIPER-ML_SOAK-SESSION-ROLE-AUTOMATION-ANALYSIS.md`: the
  dispatch carries no `--model` flag and `meta.json` records none. Every cross-run comparison
  here assumes a constant that is not captured.
- **17 pilot probe runs never entered the ledger — NEW, and upstream of every rate here.**
  57 transcripts carry a probe-id description; 40 bind to a ledger observation. The missing
  17 split into **7 with a recorded retirement reason** in `conf/soak_probes.json`'s
  `retired` block — P01, P04, P05, P09, P10, P13 **and P17** — and **10 with no recorded
  basis**: P06×3, P23×2, and one each of P14/P16/P18/P20/P22. The tooling's docstring says
  "8 pilot runs were discarded for registry leakage"; the unexplained count is **10**, or
  **17.5%** of the 57 probe runs. (An earlier draft said "17, ~30%, no recorded basis" and
  mis-grouped P17 — adversarial review caught both.) Still a selection question no rate in
  this document addresses.
- **There is no PER-PROBE `rung` field** in the ledger or `conf/soak_probes.json` (the
  string does appear in `util/soak_ledger.py`'s escalation dicts); "rung-1 probes" is an
  attribution from the plan, not something the instrument records.
- **Per-probe membership is MOSTLY unresolved** — but under the **recorded** standard
  **P15 and P19 are 0/4, upper bound `0.490`, which DOES exclude 50%** (and `P14` at 0/3,
  upper 0.561, excludes the pooled 0.605). Under the **mechanism** standard `P21` is 0/4 too,
  so it is three probes there, not two. **State the standard whenever quoting these.** It takes n≥4 with zero follows; `wilson(0,3)` is
  `[0.000, 0.561]` and does not. The blanket "no probe excludes 50%" was false and is
  withdrawn from `docs/REFERENCE.md` too.

## 6. Owner decisions — DO NOT DECIDE THESE

1. Whether **index-recovery** becomes a scored outcome (registry change; read F′ first).
2. Whether **BET-FAILING** feeds back into relocation policy.
3. Whether the stopping rule keys on the **pooled** or **post-intervention** verdict — re-arms ~27 billed runs.
4. **P06's discriminator.**
5. Whether to **`--force`** past a terminal verdict at all.
6. **Whether the per-probe campaign runs at all.** Upstream of 1–5.
7. **WHICH RETRIEVAL STANDARD BINDS.** This is the decision that selects between the
   headline numbers — 60.5% as recorded, 55.8% mechanism-checked, 41.9% input-only — and it
   was missing from this list until validation caught it. §7.1 of
   `notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md`.
8. **Whether the ledger leak invalidates its runs**, as the pilot's 8 registry-leak runs were
   once discarded. This one changes the **denominator**. §7.3 of the same document. Note the
   exposure is one demonstrated content read, not eight (§3.F′).

Also unadjudicated: §15.3 of the ledger pre-registered that rung 1 would **not** move the
follow rate on the four treated probes. P23's only post-intervention run is a follow, and
nobody has adjudicated that against the pre-registration.

## 7. Traps

- **`--outcome miss` needs `--class`**; `pointer-defect` has never been used.
- **Probe ids are full slugs.** `--probe-id P19` → `no such probe`.
- **Never pipe an exit-code-significant command through `tail`/`head`.** `status` exits 1; `status | tail -20` exits **0**.
- **`--probes` position changes the failure mode**: before the subcommand it is silently ignored; after it is rc 2 with no verdict — the same code the spend guard uses.
- **Mutation records name their target in `invalidates` / `rescores`**, not their own `obs_id`.
- **`python3 <file>` skips test classes below `unittest.main()`.** Use `-m unittest`.
- **A checkout is not a deployment.** The service unit's `WorkingDirectory=` is the primary checkout.
- **`gh pr merge` can return exit 0 while refusing.** Read the text, not the code.
- **An unresolved CodeQL thread blocks a merge while every check reads GREEN** — hit this session on ml#1854 (`mergeState=BLOCKED`, 17/17 success). Query `reviewThreads(isResolved:false)`. Fix the finding; a `# noqa` satisfies flake8 and not CodeQL.
- **The merge lane is contended.** `main` landed a commit every ~10 min while CI takes ~9–10, so `update-branch` + CI repeatedly lost the race. `gh pr merge --auto` survives it; babysitting does not.
- **A repo-relative path matches sibling repos.** 8 ecosystem repos ship `docs/REFERENCE.md` (juniper-ml plus 7 siblings). Check the `cd` target too — it carries **no trailing slash** — but consult the explicit path prefix FIRST (§3.E).
- **There is no per-probe f/n tool.** `soak_next_probe.py --status` gives post-intervention *coverage counts* in a confusable format; `soak_ledger.py report` gives pooled aggregates; `util/ad-hoc/2026-09-04_soak_handoff_consensus_checks.py` gives reducer/standards/era splits and **prints no probe ids**. The only f/n table is hand-maintained prose at `notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md` §10.5 — and **nothing in §9 produces one**, which was itself a finding against a previous handoff (§4.10 of the 09-04 review).
- **`util/wait_for_checks.py` has no `--auto`** — that is `gh pr merge`, via `util/safe_merge.py`.
- **`safe_merge --execute` exits 0 WITHOUT merging** on an unresolved review thread; it prints `auto-merge net disarmed` and names the thread. Look for the `MERGED` line. (Distinct from the `gh pr merge` trap above — both return 0 while refusing, for different reasons.)
- **`gh pr edit` is broken on gh 2.46.0** — use `gh api -X PATCH .../pulls/N -F body=@file`.
- **Stale cleanup, unclaimed**: five stale remote branches and the worktree `worktrees/juniper-ml--test--soak-harvest--20260905-1500--soak` hold nothing `main` lacks.
- **`SIBLING_REPO_SEGMENTS` is hand-maintained and already incomplete.** `juniper-slacker` exists on disk, is absent from the parent ecosystem map **and** from that tuple. Inert today (it ships no `docs/REFERENCE.md`), but the parent `CLAUDE.md` records this exact class: a repo absent from the ecosystem map is absent from every sweep that starts there.
- **ml#1699, ml#1700, ml#1725, ml#1728 are CLOSED, never merged.** Their tests reached `main` via ml#1771 and ml#1793, so a reader chasing those numbers finds closed PRs and may conclude the work was abandoned.

## 8. Documents

- `notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md` — the re-audit; mechanism classes; the ledger leak.
- `notes/JUNIPER_2026-09-09_JUNIPER-ML_SOAK-STRATUM-PREDICTOR-ANALYSIS.md` — predictors refuted; the circularity refutation; the calibrated permutation test.
- `notes/JUNIPER_2026-09-04_JUNIPER-ML_SOAK-HANDOFF-CONSENSUS-VALIDATION.md` — §4.1 campaign arithmetic, §4.6 both §15.4 breaches, §4.7 retention provenance, §7 limits, §8 owner decisions.
- `notes/JUNIPER_2026-08-20_JUNIPER-ML_POINTER-FOLLOW-SOAK-LEDGER.md` — protocol of record. §4 FOLLOW, §15.3 pre-registration, §15.4 pooling prohibition, §17 the snapshot limit.
- `notes/JUNIPER_2026-09-03_JUNIPER-ML_SOAK-TRIGGER-DESIGN-CONVERSATION.md` — §8.2 the predictor gap, §9.6 P06, §10.5 the per-probe table.
- `notes/JUNIPER_2026-08-18_JUNIPER-ML_SHARED-SESSION-MEMORY-PLAN.md` — owner decision #7 at `:654`.
- `notes/JUNIPER_2026-09-02_JUNIPER-ML_SOAK-SESSION-ROLE-AUTOMATION-ANALYSIS.md` — automation
  boundaries, and **three live items no other document carries**: its §8 un-executed
  recommendation (build a candidate scorer, run it blind against the answer key — "one
  afternoon"); §6b, that the calibration set cannot validate its own headline safety property
  because the ledger's two effective misses are the same probe (P15), and that miss-**class**
  agreement is outside the bar while `soak_ledger.py` fires the rung-2 escalation on
  `miss_class` rather than on the outcome; and **§7's model confound — the dispatch command
  carries no `--model` flag and `meta.json` records none, so which model answered any given
  probe is unrecorded.** That last one bears directly on §3.E, whose binder is built on those
  same `meta.json` sidecars.
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-04_soak-per-probe-characterisation.md`
  — **SUPERSEDED**; archived UNVERIFIED, and its central instruction is to `--force` past the
  verdict, which §0 forbids. History only. Kept named here so a successor grepping this
  directory for "soak" does not find it unmarked.
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-08-23_memory-budget-soak-and-side-findings.md` — the registry-leak authoring rule, the three-ways-invalid taxonomy, the negative-control discipline.
- `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_soak-arc-outstanding-work.md` — **predecessor**; its items E and J are closed, its prediction about the rate is refuted. History only.

## 8a. What shipped, by PR and by file

| PR | what it did |
|---|---|
| **ml#1644** (09-07) | flipped the verdict to `BET-FAILING`; narrowed the channel to tool inputs |
| **ml#1690** | `refuses_terminal_verdict` — the `--dry-run` exemption item A must preserve |
| **ml#1837** (09-09) | consolidated four duplicate copies of the REFERENCE.md soak section; prerequisite for ml#1857 |
| **ml#1846** | evidence recovery: `SUBAGENT_DIRS` fix, the binder, the re-audit note |
| **ml#1854** | the predictor analysis + tool |
| **ml#1855** | the sibling-repo channel narrowing (whose ordering bug this handoff fixes) |
| **ml#1857** | the REFERENCE.md operator-surface correction |

**Changed by the handoff PR itself** (validation-driven, all in one change):
`util/soak_run_probe.py`, `tests/test_soak_run_probe.py`,
`util/ad-hoc/2026-09-08_soak_label_to_transcript.py`,
`notes/JUNIPER_2026-09-08_JUNIPER-ML_SOAK-RETRIEVAL-STANDARD-EVIDENCE-RECOVERY.md`,
`notes/JUNIPER_2026-09-09_JUNIPER-ML_SOAK-STRATUM-PREDICTOR-ANALYSIS.md`,
`docs/REFERENCE.md`, and this file.

**Not changed, in any of them**: `reports/soak/pointer_follow_soak.jsonl`,
`conf/soak_probes.json`. No probe has been run.

## 9. Verify first

```bash
git fetch origin && git log origin/main --oneline -1          # advisory; main moves hourly
python3 util/soak_ledger.py status; echo "rc=$?"              # BET-FAILING, rc 1 -- do NOT pipe
wc -l reports/soak/pointer_follow_soak.jsonl                  # expect 64
python3 util/soak_next_probe.py --status                      # 8 runs, 7 covered, 8 at zero
python3 util/soak_run_probe.py --dry-run; echo "rc=$?"        # expect rc 0 + terminal NOTE on stderr
python3 util/ad-hoc/2026-09-08_soak_label_to_transcript.py reports/soak/pointer_follow_soak.jsonl
python3 util/ad-hoc/2026-09-09_soak_stratum_predictors.py --validate
python3 util/ad-hoc/2026-09-09_soak_stratum_predictors.py --standard mechanism --draws 200000
                                                              # the 200k floor; --validate's is 5e-5
python3 util/memory_index_check.py; echo "rc=$?"              # rc 1 is EXPECTED -- pre-existing
                                                              # hook-length errors on other rows
systemctl --user is-enabled juniper-soak-probe.timer          # expect not-found -- item A is dormant
python3 -m unittest tests.test_soak_run_probe tests.test_soak_ledger tests.test_soak_next_probe
gh pr list --repo pcalnon/juniper-ml --state open --search soak   # expect none
```

`--dry-run` returning **2 with empty stdout** means ml#1690's exemption has been reverted.

## 10. What validation changed, and residual uncertainty

Three Lane A reviewers ran with genuinely different entry points — repository artifacts,
git/GitHub history, and the raw transcript tree — followed by two Lane B adversarial rounds
(refutation, and omission/amputation). **Total: 11 refutations, 2 omissions, 16 further
omissions, and 15 attacks on the corrections.** Two Lane A findings were reached independently
by two reviewers each.

**Do not read this section as a clean process.** Lane B found that the fix pass itself
introduced errors, including a *new* false-positive class in the very function the earlier
round fixed, and three corrections that a single tool run would have caught — so the claim
"every load-bearing finding was re-derived before acceptance" was itself too generous and is
withdrawn. What is true: everything below was re-derived *eventually*, and the round that
caught the fix-pass errors is the reason.

**The review found a live defect in shipped code, not just in the prose.**
`_own_repo_occurrence` in `util/soak_run_probe.py` — the wired scoring path — tested the `cd`
target before the per-occurrence path prefix, discarding genuine reads by any subject working
from the ecosystem parent. It is fixed here, with pins in both directions. **The headline it
produced was wrong: 51.2% → 55.8%, and the margin claim 0.0962 → 0.0543.**

What else changed:

| claim as drafted | corrected to | found by |
|---|---|---|
| mechanism rate 22/43 = 51.2% | **24/43 = 55.8%** | A3 (root cause), reconciler re-derived |
| all three P24 runs read juniper-deploy's copy | **one** did; two read ours, one by `sed` | A3 |
| "8 runs read the ledger" | 8 **touched** it; **one** read content | A3 |
| one automated-path leak | **two** rows, but both filename-only → live-path claim **withdrawn** | A1 + A2 |
| "no probe's interval excludes 50%" | **P15, P19 do** (0/4 → upper 0.490) | A1 |
| 69.8% circularity figure, "`--validate` reproduces this" | **68.1%**; the figure came from an uncommitted draft | A1 + A2 |
| `p < 5e-6` stated as measured | it is the **floor** of 200,000 draws | A1 |
| "the suite stubs `ledger_rc=0`" (inherited) | **six** non-zero stubs; the suite discriminates | A1 |
| "purely the n-gate" | an **OR**; both disjuncts fire | A1 |
| "no `rung` field anywhere" | none per-probe; the string exists in escalation dicts | A1 |
| 17 unaccounted pilot runs | **new gap**, added to §5 | A3 |
| four of seven PRs named, no changed-file list | §8a added | A2 |
| `wilson(0,3)` upper printed as 0.562 | **0.561** — ml#1857 changed a right digit to a wrong one | A2 |

**Then a Lane B round attacked the corrected document under an omission lens and returned 16
more findings — two of them critical.** The pattern the procedure predicts held exactly: the
fix pass introduced its own errors, and the biggest gaps were things the *first* draft had
silently dropped rather than got wrong.

| omission | restored as |
|---|---|
| **the whole `MEMORY.md` section** — the intervention under test — was amputated, and it has degraded further (3 of 4 rung-1 rows now hookless, incl. one the predecessor recorded as surviving) | §3a |
| **git status absent**, while §1 said "nothing is time-critical", §2 said "open PRs: none" and §9 said "expect none" — with the entire diff unlanded | §1.0 |
| §4.5 "one observation deep" dropped, and `0.0137` presented as superseded by a margin the **ledger does not carry** | §0 box; 27/43 → 0.7562, non-terminal |
| era figures gone — **neither era is terminal**; the verdict exists only via the pooling §15.4 forbids | §0 |
| two owner decisions missing: **which standard binds**, and **whether the leak invalidates its runs** | §6.7, §6.8 |
| `…SOAK-SESSION-ROLE-AUTOMATION-ANALYSIS.md` dropped, taking the **model confound** with it | §5, §8 |
| `p = 0.0017` still mislabelled at its source; §3.J read as if fixed | §5 |
| the wired-path code-hardening follow-up reframed as a *standard* question | §3.F′ |
| supersession warning on the 09-04 handoff; five dropped traps; the closed-PR note | §7, §8 |
| two contradictory "Residual uncertainty" paragraphs | one removed |
| a **phantom** task: the three-ways-invalid taxonomy is already re-homed | §3.G corrected |

**Round 3 — adversarial attack on the corrections — broke the fix pass, as the procedure
predicts.** Fifteen findings; the load-bearing ones:

| what the fix pass got wrong | corrected to |
|---|---|
| the reorder introduced a **new false-positive class**: `"/juniper-ml"` is a PREFIX (matched `juniper-mlx`, `juniper-ml-scratch`), and a 60-char text window is not a path, so a grep **pattern** naming our file scored as reading it | decide from the **path token** the match sits in; segments now end at a boundary; 3 new pins |
| "one P24 run read juniper-deploy's copy" | **all three did** — the wrong half was the *inference*, not the observation. Two also read ours |
| the output-scored table said 7/1/0 | the tool prints **6/1/1** |
| the predictor note's fenced blocks were **appended to, not replaced** — two header lines, and a calibration block whose 12 values the tool does not emit | both replaced with real output |
| `docs/REFERENCE.md`'s "or the pooled rate" half left asserted, and still false | **three** probes exclude 0.605 |
| "17 unaccounted, no recorded basis" | **7 have a recorded retirement reason** (incl. P17, mis-grouped); **10** unexplained, 17.5% |
| "the correction changed no conclusion" | with 5 features, Bonferroni α=0.01: the one-discordant floor crossed it (0.0070 → 0.0182) |
| `fact_points_to_source` reported as tested | **vacuous** — identically 0 in both strata |
| 276 tests | **281** |

**Two reviewers explicitly could not reproduce one thing each**, and both are recorded rather
than dropped: ml#1854's transient `mergeState=BLOCKED` is unrecoverable post-merge (the commit
message is the only witness), and the ml#1690-bug behaviour on an empty ledger cannot be
exercised without moving the live ledger, so it is reasoned from the code path only.

**Residual uncertainty.** The mechanism classification is one rater's rules applied
mechanically, not a second rater. The `nearest`-transcript binding was re-derived
independently by a reviewer using subject-text matching (Jaccard 0.30–0.59 for the bound
probe vs 0.03–0.10 for the best competitor, 0 ambiguous) — that is stronger than the mtime
argument the tool uses, and it held. The ledger-leak count of 8 was probed for upward leakage
from two directions and did not move, but it was not exercised from below, so treat it as a
floor. **Item A's fix is still unwritten.** No probe was run and the ledger was not modified
in producing this document.

*(A second, pre-validation copy of this paragraph stood here and contradicted the one above
on how the binding was verified. It was a fix-pass artefact — exactly the failure §4 of the
consensus procedure predicts — and was removed when a reviewer flagged it.)*
