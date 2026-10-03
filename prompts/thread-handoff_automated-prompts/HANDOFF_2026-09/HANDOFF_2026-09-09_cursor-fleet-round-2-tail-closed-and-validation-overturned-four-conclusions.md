# HANDOFF — Cursor fleet round 2: the tail is closed, and validation overturned eight of my claims

**Date**: 2026-09-09
**Session**: `67e29fd9-d3bf-49e9-86a9-f476354eb35d` (`https://claude.ai/code/session_019dCjJ7wtsyvrRnJdLedp8G`)
**Worktree**: `juniper-ml/.claude/worktrees/adaptive-moseying-lampson`
**Validation**: six independent agents — 3 Lane A + 2 Lane B (round 1), then 1 briefed only on
the corrections (round 2). **Round 1 overturned eight claims and found a content loss I had
shipped; round 2 found five NEW errors introduced by the fix pass itself.** Full record in **§7** — read it before §1,
because §1 is what survived.

---

## 1. Goal statement for the next thread

```text
Continue the cursor-fleet round-2 tail for juniper-ml. All six items of the 2026-09-07
handoff are merged (#1831, #1833, #1834, #1837, #1849, #1856). What remains is SIX items.
Only ONE is an owner decision -- an earlier draft of this handoff called two of them
decisions, and measurement answered both.

Completed so far:
- The 2026-09-07 handoff's items 0-5, merged and verified on main by CONTENT.
- docs/REFERENCE.md: 8 repeated `##` sections -> 3; four doubly-claimed version numbers
  disambiguated. 7542 -> 7068 lines at #1837 (7088 today; #1857 added 20 after).
- Live notes/ structure debt: 12 files / 63 findings -> 5 files / 24.
- Whole-tree: 102 problems / 21 files -> 63 / 14.
- A content loss THIS SESSION CAUSED, found by validation and repaired in this PR: #1837
  collapsed four soak sections and deleted all THREE copies of the systemd install recipe,
  leaving zero. Collapsing N duplicates must leave one. `2026-09-08_section_loss_check.py`
  reported it clean because it only extracted code spans, links and dotted paths -- the
  recipe is bare commands inside a ```bash fence -- so of the 25 losses the tool DID report
  on that diff, not one was the recipe. It now compares every fenced line (real CommonMark
  matching, ``` and ~~~) and was mutation-checked against exactly this loss.

Remaining work, in priority order:
1. A REAL RENDERING DEFECT, mis-filed by me as a false positive.
   notes/JUNIPER_2026-03-12_JUNIPER-ML_PROMPT-ANALYSIS-AND-AUTOMATION-PLAN.md opens
   ```jinja2 at :816. The bare ``` at :856 CLOSES it (a fence with an info string cannot
   close; a bare one can), so :857-864 escape into prose and `{% endif %}`,
   `{% include ... %}` and `{% endblock %}` render as visible text on github.com. The bare
   ``` at :865 then OPENS a further block, so :866-873 -- the "Example snippet" caption and
   its ```markdown tag -- render as code. Note none of the FOUR screen findings on this file
   IS the defect (those H2s legitimately sit inside the template sample); the defect is
   adjacent, and was found only by investigating them. #1834
   retagged six bare fences in this same file and left this one. Fix the fence.
   I had called this "a template that emits markdown", overriding my own triage tool,
   which had classified it LOST-FENCE? -- its damage bucket.
2. RESTORE the four table rows, do not ratify them. This was drafted as an owner decision;
   the evidence is one-way. `notes/JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md:360`
   says verbatim: "Moved to the companion model document (§3.2) -- numerical-correctness,
   known-answer/golden, regression-metric, time-series-leakage, growth-loop, determinism,
   overfit-tiny, and architecture-specific stability suites". All EIGHT belong in
   notes/JUNIPER_2026-05-31_JUNIPER-RECURRENCE_RECURSE-MODEL-DESIGN-AND-PLAN.md §3.2; four
   are missing, so their absence is a live cross-document inconsistency. My "case for
   leaving them" was wrong three ways: §3.3 of the companion does NOT hold them (zero
   hits); the survivor/deleted split is INVERTED (deleted `Known-answer / golden` tests the
   Reber grammar, the most model-specific content in the doc, while surviving
   `Determinism` is carried by companion §3.1); and 4da40fe9 deleted header, separator and
   rows in ONE hunk, so restoring the header on an accident theory while withholding the
   rows on an intent theory reads one deletion two ways.
   Recover with: git show 22c32bd1:notes/JUNIPER_RECURSE_MODEL_DESIGN_AND_PLAN_2026-05-31.md
   -- the PRE-RENAME path; the current path exits 128 at that commit.
3. RETARGET ALL TEN dangling symlinks -- not one, and do not delete nine. Every target is a
   tracked file on main today, renamed by 432ed644 -- the SAME commit that broke the tenth.
   My "nine permanently broken" came from grepping `notes/legacy/regressions/`, the links'
   RESOLVED path, which never existed. TWO different fixes -- do not apply one recipe to ten:
     * the NINE under notes/legacy/ -> `../regressions/<renamed basename>`; targets sit in
       notes/regressions/ (27 files), one level up.
     * the TENTH, notes/development/JUNIPER_2026-04-24_..._V7-IMPLEMENTATION-ROADMAP.md, is
       NOT in notes/regressions/ and its DATE changed in the rename -- target is
       notes/JUNIPER_2026-05-25_JUNIPER-ECOSYSTEM_OUTSTANDING-DEVELOPMENT-ITEMS-V7-IMPLEMENTATION-ROADMAP.md.
       Its basename is not mechanically derivable from the link.
4. SCREEN PRECISION -- and it is a REQUIRED-GATE defect, not accounting. A PR adding any .md
   with a valid GFM single-hyphen delimiter (`| - |`, `|:-:|`) FAILS the required
   `Documentation Links` context today (`docs` is only the ci.yml job id), because `util/markdown_structure_delta.py` imports this screen and grades an
   ADDED file against zero. Relax SEPARATOR at
   `util/ad-hoc/2026-09-05_markdown_structure_check.py:55` from `-{2,}` to `-+`.
   MEASURED EFFECT, whole tree: 63 -> 54 (not the 56 an earlier draft claimed -- that
   subtracted only the live-notes hits and assumed the fix could not reach the ratified set;
   it clears 4 there and takes 3 of the 6 notes/legacy/ files to zero). Live notes/ 24 -> 19 (whole-tree delta is 9; 4 of it lands in the ratified set).
   A length-aware fence walker (four-backtick blocks) takes it to 49.
5. THE RATIFICATION IS RECORDED NOWHERE -- and DO NOT WRITE IT DOWN UNTIL 1-4 LAND.
   The owner ruled in session 2026-09-08 "fix live notes/ only, ratify the rest"; nothing in
   the repo says so. But the number is not yet correct and the set is not uniformly benign:
     * item 4's fix removes >=4 of the 39 and empties 3 of its 9 files;
     * the 39 contains REAL damage the ruling was made without -- TWO unclosed fences,
       BOTH in prompts/ (prompts/generated/JUNIPER_ML_CUSTOM-AGENT-SUITE-ENHANCEMENTS_PLAN_2026-06-26_2048.md:101
       and prompts/manual/prompt053_2026-03-30.md:50), plus >=2 genuinely broken tables that
       survive the regex fix (notes/legacy/DEVELOPER_CHEATSHEET-ORIGINAL.md:22 has a
       delimiter row and NO header; notes/legacy/METRICS_MONITORING_ROADMAP_2026-04-25.md:353
       has a space inside a delimiter cell).
     * 7 of the prompts/ findings are prompts/agent_templates/README.md:26, the exact class
       `util/ad-hoc/2026-09-08_tag_sample_fences.py` fixes in one word.
   So: re-measure, repair what is real, THEN record what is genuinely accepted.
   OWNER DECISION -- the ruling was given without knowing the set held real defects.
6. TAIL, none of it owner-gated:
   a. CROSS-REPO FAN-OUT. `Sequence Safety` is a REQUIRED context in ALL EIGHT sibling
      repos, and all eight workflows say "ADVISORY, NOT a required check ... never blocks a
      merge" (juniper-cascor/.github/workflows/sequence-safety.yml:24 and the same text in
      canopy/data/recurrence/cascor-client/cascor-worker/deploy/data-client). #1849/#1856
      fixed juniper-ml only, and `util/ad-hoc/2026-09-09_required_check_comment_drift.py`
      hard-codes DEFAULT_RULESET and the juniper-ml API path. No sibling has any
      markdown-structure gate at all.
   b. THE `or {}` SWEEP IS NOT CLOSED. 28 unguarded chains remain across 7 files the
      predecessor never named, incl. `util/ad-hoc/2026-09-04_laneA1_independent_verify.py`
      (9 -- a validation instrument). The census is blind to the split-across-lines form
      (live example: util/experiments/stats_summary.py:273-279) so a clean run is NOT
      evidence, and it silently returns NOTHING when pointed at a sibling path because
      UNTRUSTED is a hard-coded juniper-ml artifact roster. ~135 sibling sites.
   c. SIX SITES STILL ASSERT 102/21, now stale at 63/14 -- ci.yml:1061 and :1579,
      tests/test_markdown_structure_delta.py:18 and :114, util/markdown_structure_delta.py:20,
      docs/REFERENCE.md:2921 (was :2911; this PR's restore shifted it). I wrote four of those in #1831 (correcting 104/23), and #1834
      invalidated them 48 minutes later. Do not re-sweep until 1-4 land or it goes stale again.
   d. 87 RESIDUE LINES STILL UNADJUDICATED, from the predecessor's §5 -- §4 of
      notes/JUNIPER_2026-09-06_JUNIPER-ML_DOCS-FLEET-CONSOLIDATION-ROUND-2-RESIDUE.md, one
      commit ever. The arc's only remaining open CONTENT-LOSS question.
   e. tests/test_markdown_structure_screen.py (added by #1831) is absent from AGENTS.md's
      hand-maintained test list. CI runs it; the local instructions do not name it.

Key context:
- RE-MEASURE BEFORE ACTING. #1857 landed the soak-number follow-up this session had flagged
  as outstanding, before this was written. Every count here is timestamped, not durable.
- THE AUTO-MERGE NET ARMS WITH AN EMPTY `commitBody`, overriding COMMIT_MESSAGES and dropping
  the whole body. #1831 merged subject-only. On a PR carrying an `Allow-*` trailer that
  reddens main at Post-Merge Main Verification and nowhere earlier. Check
  `gh pr view <N> --json autoMergeRequest --jq '.autoMergeRequest.commitBody | length'`
  before the net fires; re-arm with `--subject` + `--body-file`. Re-cutting does not help.
- "KEEP THE LONGEST COPY" WOULD HAVE SHIPPED FALSEHOODS. The four soak copies contradicted
  each other and the RICHEST was wrong twice. Adjudicate against SOURCE, never by length.
- CLASSIFY BEFORE REPAIRING, THEN CHECK THE CLASSIFIER. Of 63 live-notes findings 8 were
  real -- but I then over-trusted the classification and mis-filed a real defect (item 1)
  and invented an authority for another (§5).
```

---

## 2. State at handoff

| | |
| --- | --- |
| `origin/main` at write time | `8a2a8e94` — **re-measure; it moves every few minutes** |
| this session's PRs | **#1831, #1833, #1834, #1837, #1849, #1856 — all MERGED** |
| whole-tree structure debt | **63 problems / 14 files** (was 102 / 21) |
| — of which legacy + prompts | 39 / 9 — **provisionally** ratified; see §1 item 5 |
| — of which live `notes/` | 24 / 5 — **one is a real defect** (§1 item 1), not zero |
| `docs/REFERENCE.md` | **7088** at `8a2a8e94` (7068 at #1837; #1857 added 20) — **7098 after this PR's restore**; 0 structural problems, 0 duplicate `##` |
| dangling markdown symlinks | 10 — **all ten repairable** |

### Verification commands

Run from the repo root on a tree synced to `origin/main`.

**Never read a gate's exit code through a pipe** — the shell reports the LAST command's
status. `xargs` is a pipe *and* remaps: it turns any child exit in 1–125 into **123**, so
the screen's exit 2 is invisible through it. This document's author committed that error
three times, including once in this very block, one line below the warning. The invocation
below therefore avoids `xargs` entirely.

```bash
git fetch origin main && git log origin/main --oneline -1

# Whole-tree structure debt. The screen's OWN exit is 2 by design (ten dangling symlinks
# it now refuses to skip silently); 2 here is honesty, not failure.
git ls-files -z '*.md' > /tmp/md0
python3 - <<'PY'
import subprocess, sys
paths = [p for p in open('/tmp/md0').read().split('\0') if p]
r = subprocess.run([sys.executable, 'util/ad-hoc/2026-09-05_markdown_structure_check.py'] + paths)
print("screen exit =", r.returncode)   # 2 = refused to report on a partial examination
PY

# Classify before repairing. Prints BLOCKS (fence/table groups), not per-line problems --
# 9 blocks == the 24 screen findings. Expect 5 TABLE / 2 LOST-FENCE? / 1 SAMPLE / 1 TRANSCRIPT.
# The LOST-FENCE? at PROMPT-ANALYSIS:816 is REAL (§1 item 1); the tool is right, I was not.
python3 util/ad-hoc/2026-09-08_notes_structure_triage.py; echo "exit=$?"

# REFERENCE.md integrity
python3 util/ad-hoc/2026-09-07_duplicate_section_census.py docs/REFERENCE.md
python3 util/ad-hoc/2026-09-08_version_collision_recency.py     # "no colliding version numbers"

# Are the four disputed rows still absent? (0 = still absent)
grep -c 'Numerical correctness' \
  notes/JUNIPER_2026-05-31_JUNIPER-RECURRENCE_RECURSE-MODEL-DESIGN-AND-PLAN.md

# Every unclosed fence on main -- all three are in the "ratified" set (§1 item 5)
python3 - <<'PY'
import subprocess, sys, re
paths = [p for p in open('/tmp/md0').read().split('\0') if p]
out = subprocess.run([sys.executable, 'util/ad-hoc/2026-09-05_markdown_structure_check.py'] + paths,
                     capture_output=True, text=True).stdout
cur = None
for ln in out.splitlines():
    m = re.match(r'^=== (.+) ===$', ln)
    if m: cur = m.group(1)
    if 'UNCLOSED' in ln: print(cur, '->', ln.strip())
PY
```

---

## 3. Tools this arc built

All on `origin/main` except `section_loss_check.py`, whose fenced-line comparison ships in
THIS PR. **Read the docstring first.** `writes?` marks file mutators; every one
defaults to dry-run and needs `--apply`.

| tool (`util/ad-hoc/`) | writes? | question |
| --- | --- | --- |
| `2026-09-08_notes_structure_triage.py` | no | is this finding real damage, or one of four non-damage classes? |
| `2026-09-08_tag_sample_fences.py` | **yes** | label a bare fence holding a markdown SAMPLE |
| `2026-09-08_repair_notes_tables.py` | **yes** | the eight real table repairs, each asserting its target line first |
| `2026-09-08_version_collision_recency.py` | no | which row of a colliding version pair landed later? |
| `2026-09-08_repair_version_collisions.py` | **yes** | apply the `+N` suffixes, merge the duplicated row |
| `2026-09-08_reconcile_reference_sections.py` | **yes** | collapse the repeated `##` sections |
| `2026-09-08_section_loss_check.py` | no | **what does the BEFORE have that the AFTER lacks?** |
| `2026-09-09_required_check_comment_drift.py` | no | does a comment call a REQUIRED check advisory? (candidate finder, exits 0) |

**Two carry a known limit, stated because a clean run from either is not evidence:**
`notes_structure_triage.py` classifies by the fence's info string alone — it never checks
whether the content was captured, which is how §5 came to assert a "transcript" that never
existed. `section_loss_check.py` compares atoms, so a rewording is invisible to it by design;
it now also compares fenced lines, which is what it was missing when it passed the loss
described in §1.

---

## 4. Traps this arc paid for

1. **A pipe eats the exit code, and knowing it does not protect you.** Three times, once
   inside the verification block warning about it. `xargs` additionally remaps 2 → 123.
2. **The auto-merge net's empty `commitBody`** — see §1. The one failure that would have
   reddened `main`.
3. **A loss check that only reads decoration cannot see a code block.** Inline spans, link
   targets and dotted paths all key on markdown punctuation; a `​```bash` block has none, so
   three copies of an install recipe vanished and the instrument said clean.
4. **Classifying by an info string is not classifying by evidence.** ` ```text ` made the
   triage tool say TRANSCRIPT, and I repeated that as a fact about a specimen for a script
   that has never existed in git.
5. **An assertion in a repair script earns its keep** — `repair_notes_tables.py` refused on
   a mismatched line and caught an off-by-one (the screen reports a table defect at the
   HEADER; the malformed separator is the line after).
6. **The census under-counts by construction** — it matches single-expression chains, so
   `x = d.get(k) or {}` then `x.get(...)` later is invisible. Reported 6; there were 9.
7. **`is_file()` follows symlinks**, so a dangling link scores clean. Ten did.
8. **A comment and a ruleset are different authorities.** `ci.yml` called two REQUIRED
   checks advisory; one contradicted itself four lines later.
9. **A negative result is only as good as its predicate.** `grep`ping a symlink's RESOLVED
   path proved a directory never existed and concluded nine files were gone. They are on
   `main`, one level up. Search the target's BASENAME.

**Corrected from an earlier draft — `safe_merge` was blamed unfairly.** It refused three
PRs, but "Quality Gate never reported" is false: it reported `success` on #1834's head
`6d01031f` at 09:31:56Z, nine seconds before the 09:32:05Z merge -- outside safe_merge's wait
budget, not outside CI — which is why two budget fixes merged the same
day (#1828, #1851). Its disarm-on-refusal is its **central documented guarantee**, not a
trap, and it warns explicitly when a disarm fails. The real lesson is the inverse of what
was written: **after a `safe_merge` refusal the net is guaranteed down, so you must re-arm
to proceed.**

---

## 5. Decisions made — do not re-litigate

- **`+N` build metadata for a doubly-claimed version**, not `.1` (invalid SemVer) and not
  `-1` (a PRE-RELEASE, which orders the newer row *before* the older). `+N` is ignored for
  precedence — it asserts no order at all, which is the honest thing to assert.
- **`0.6.40` was merged, not suffixed** — one change described twice by one commit (#1797).
- **`0.6.19`'s suffix is documentary only** — both rows landed in the same commit (#1787).
- **The ` ```text ` block at STANDING-ITEMS:1103 stays unedited** — but **not** for the
  reason an earlier draft gave. It is *not* a captured transcript: `util/headless_signing_preflight.bash`
  has never existed in git and the block carries the literal placeholder
  `<the C4 command, run interactively>`. It is a hand-authored specimen of a banner a
  specified-but-unwritten script would print. It stays because the fence is well-formed and
  the `##` lines are banner art, so the 13 findings are genuine screen false positives —
  a rendering fact, not a provenance one.

---

## 6. Documents this handoff references or changes

**References**: `notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`,
`notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`,
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-07_cursor-fleet-round-2-disposition-closed-and-the-re-land-repair.md`,
`notes/JUNIPER_2026-05-31_JUNIPER-RECURRENCE_RECURSE-MODEL-DESIGN-AND-PLAN.md`,
`notes/JUNIPER_2026-05-31_JUNIPER-ECOSYSTEM_MODEL-MIDDLEWARE-REFACTOR-DESIGN-AND-PLAN.md`,
`notes/JUNIPER_2026-09-06_JUNIPER-ML_DOCS-FLEET-CONSOLIDATION-ROUND-2-RESIDUE.md`,
`notes/JUNIPER_2026-03-12_JUNIPER-ML_PROMPT-ANALYSIS-AND-AUTOMATION-PLAN.md`,
`notes/JUNIPER_2026-08-09_JUNIPER-ECOSYSTEM_STANDING-ITEMS-CLOSEOUT-AND-HARNESS-REMEDIATION-PLAN.md`,
`notes/JUNIPER_2026-06-17_JUNIPER-RECURRENCE_STATE-ASSESSMENT-AND-ROADMAP.md`,
`notes/JUNIPER_2026-07-30_JUNIPER-ML_CURSOR-DASHBOARD-CONFIG-REQUESTS.md`,
`notes/legacy/CASCOR_DEMO_TRAINING_ERROR_PLAN.md`,
`notes/legacy/DEVELOPER_CHEATSHEET-ORIGINAL.md`,
`notes/legacy/METRICS_MONITORING_ROADMAP_2026-04-25.md`,
`prompts/agent_templates/README.md`, `docs/REFERENCE.md`, `AGENTS.md`.

**Changed**: this file,
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-09_cursor-fleet-round-2-tail-closed-and-validation-overturned-four-conclusions.md`;
plus the two repairs the validation forced —
`docs/REFERENCE.md` (the systemd install recipe restored) and
`util/ad-hoc/2026-09-08_section_loss_check.py` (fenced-line comparison added).

---

## 7. Independent validation — what it changed

Run per `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.
Sized at the procedure's bottom-right cell (uncertainty increases downward): a document of record, containing universal quantifiers, written
by the agent whose work it reports — **convenient**. **3 Lane A** (entry points: the repo
tree and its instruments / git + PR history / the predecessor handoff) **+ 2 Lane B**
(lenses: omission, and false authority). Every finding below was **re-derived by the
reconciler** before acceptance; a lone agent report is a lead, not a fact.

### What it overturned

| my claim | measured | why I was wrong |
| --- | --- | --- |
| "only ONE symlink is repairable; the other nine are PERMANENTLY broken" | **all ten** repairable | I grepped the links' RESOLVED path `notes/legacy/regressions/`. The targets are in `notes/regressions/` — 27 tracked files — renamed by the same commit that broke the tenth. One of the options I offered the owner ("delete the nine") would have destroyed nine live cross-references. |
| "NONE [of the 24] is a document defect" | **one is** | `PROMPT-ANALYSIS…:816`'s ` ```jinja2 ` closes early at :856; Jinja tags render as prose on github.com. My triage tool had classified it `LOST-FENCE?` — its damage bucket — and I overrode it by hand. |
| the four RECURSE-MODEL rows are a balanced RESTORE-or-RATIFY | **evidence is one-way: restore** | The companion at `:360` assigns all eight suites to the model doc. §3.3 does not hold them (zero hits). The survivor/deleted split is inverted. |
| "63 → 56" from the two screen fixes | **63 → 54** from the first alone | I subtracted only the live-notes hits, assuming the fix could not reach the ratified set. It clears 4 there and empties 3 of its 9 files — so the "39 accepted debt" figure item 5 was told to record is wrong on both sides. |
| "7555 → 7068 lines" | **7542 → 7068**, and **7088** today | 7555 was my mid-change working-tree count; it exists in no commit. §2 also quoted 7068 against a `main` where the file is 7088. |
| `safe_merge` refused on "a Quality Gate that never reported" | it **reported success**, late | A wait-budget shortfall written up as the tool failing. Corrected in §4. |
| the ` ```text ` block is "a captured transcript" | the script **never existed** | Classified from the info string, not from evidence. The false claim also reached `b264c2a2`'s commit body on `main`. |
| "the 52 duplicate `###` are by design (every operator section closes with Operator pitfalls)" | 52 excess across **12** titles; that cause explains **24** | True conclusion, cause stated over less than half the set. |

### What it found that I had not written down at all

The systemd install-recipe loss (§1, repaired here); the cross-repo fan-out — `Sequence
Safety` required in all eight siblings while all eight workflows call it advisory; 28
remaining `or {}` chains plus the census's two blind spots; the 87 unadjudicated residue
lines; six sites still asserting 102/21; and that both genuine unclosed fences on `main` sit
inside the set the owner was asked to ratify.

### What ROUND 2 found — the fix pass introduced five new errors

Briefed only on the corrections, per §4 of the procedure. It was right to be:

| the fix introduced | reality |
| --- | --- |
| "live notes/ 24 → 17" | **24 → 19.** I corrected the whole-tree half to 54 and left the live-notes half at the old delta — the two then contradicted each other inside one sentence. |
| "THREE unclosed fences", led by `CASCOR_DEMO_TRAINING_ERROR_PLAN.md:1454` "swallowing the last ~97 lines" | **TWO**, both in `prompts/`. `:1454` is the bare CLOSER of the ` ```bash ` at `:1446`; that file is balanced under CommonMark. The screen's toggle slips at `:1200`, where a ` ```python ` line cannot close a fence. `notes/legacy/` has **zero**. |
| "all ten repairable … fix is `../regressions/<renamed>`" | true for **nine**. The tenth's target is not in `notes/regressions/`, is at the same level, and its DATE changed in the rename — one recipe applied to ten leaves it dangling. |
| Quality Gate "reported success 09:39:53Z on #1834's head" | that is the **post-merge run on `main`**. The head `6d01031f` reported at **09:31:56Z**. Right direction, wrong ref. |
| `docs/REFERENCE.md:2911` | **:2921** — this PR's own +10-line restore moved it. |

I also caught one myself before round 2 reported: my first fenced-line implementation used a
boolean toggle, so an inner ` ```bash ` read as a closer and the lines after it were dropped —
**under-collecting**, the one direction a loss check may never fail in. It now does real
CommonMark matching and handles `~~~`.

**The lesson worth carrying**: I accepted "three unclosed fences" from two round-1 agents and
"verified" it by re-running the screen — the very instrument whose fence toggle this document
elsewhere concedes is broken. Re-deriving with the correct parser gives two. Accepting a
correction without re-deriving it is the same error, outsourced; the procedure says so, and I
did it anyway.

### Residual uncertainty

The counts here were measured at `8a2a8e94` on a `main` taking merges every few minutes, and
`docs/REFERENCE.md` had already moved 20 lines between two rows of my own §2 table. **Treat
every number as a timestamp.** Round 2 was briefed only on these corrections, per §4 of the
consensus procedure — the fix pass is the least trustworthy part of any document.

Dissent not resolved: one reviewer read the ` ```jinja2 ` block as recoverable by changing
the inner bare fences, another as needing the outer fence lengthened to ` ````jinja2 `. Only
the second works as literally stated — a closing fence cannot carry an info string, and a
longer bare run still closes a 3-backtick opener, so "retagging" the inner pair helps only if
they become `~~~`. The choice is left to whoever fixes item 1.
