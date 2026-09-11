# Falsy-guard population: triaged, and the count was wrong in both directions

**Date**: 2026-09-11
**Repo**: juniper-ml
**Arc**: cursor-fleet round 2, standing item 2
**Predecessor**: [`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_cursor-fleet-round-2-closed-and-three-numbers-that-were-instrument-artifacts.md`](../prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_cursor-fleet-round-2-closed-and-three-numbers-that-were-instrument-artifacts.md)

---

## 1. Why this document exists

`HANDOFF_2026-09-11_cursor-fleet-round-2-closed-and-three-numbers-that-were-instrument-artifacts.md`
closed the arc with a through-line: *every headline number it carried was an artifact of the
instrument that produced it, not a property of the tree.* It then left one standing item —
**"117 live read-class sites across 19 files remain"** — and told a successor to triage rather
than sweep.

That number is the fourth instrument artifact. It is wrong in **both directions at once**, and
the corrected figure changes what the remaining work looks like.

## 2. The count

| | |
| --- | --- |
| handoff's figure | **117 sites / 19 files** |
| census rows re-measured (one per USE) | 116 |
| **distinct guards** (the unit of repair) | **77** |
| guards the census structurally cannot see | **+8** |
| **true population before this change** | **85** |
| fixed here | −6 |
| **population now** | **79** (72 census-visible + 7 blind) |

### 2a. The over-count: a row is a USE, not a guard

`util/ad-hoc/2026-09-11_falsy_guard_census.py` emits one finding per *dict-shaped use* of a
guarded name. `identity = stats.get('identity') or {}` at
[`util/experiments/stats_summary.py`](../util/experiments/stats_summary.py):273 is used six
times, so it appears six times. Both units are correct for their own question — "how exposed is
this value?" versus "how many lines must change?" — and they must not be added together. 116
rows are 77 guards.

### 2b. The under-count: the census only reads the top of a scope

`_ScopeVisitor._scan_scope` iterates `for stmt in body` over the **direct children** of a scope and tests
`isinstance(stmt, (ast.Assign, ast.AnnAssign))`. An assignment nested inside `while:` / `try:` /
`if:` / `for:` is never registered as a guard. Eight read-class guards are invisible for that
reason alone, including
[`util/experiments/run_experiment.py`](../util/experiments/run_experiment.py):990
(`monitor = last_data.get("monitor") or {}`), which sits inside `while` → `try` and is one of
the six defects fixed below.

So **85 was a floor, not a total**, and 79 still is. Anyone quoting a falsy-guard figure should
run both tools and say which unit they mean.

> **The first version of this measurement said nine, and was itself an artifact.** The scan
> originally reported every nested `X = <read> or {}` regardless of whether a dict-shaped USE
> followed it — a looser rule than the census applies. The difference then measured the rule,
> not the census's reach. `deep_guard_scan` now applies the census's own criterion (use
> required, `isinstance` suppresses) and the figure is eight. A comparison between two
> instruments is only a measurement when their criteria match, which is the same lesson §2a
> teaches about units.

## 3. Triage by provenance

`util/ad-hoc/2026-09-11_falsy_guard_triage.py` classifies each guard by the provenance of the
*container* being read, because that — not the expression shape — decides whether a truthy
non-dict can arrive:

| provenance | guards | meaning |
| --- | --- | --- |
| `operator` | 5 | parsed from hand-authored YAML; a bad value is reachable **by typing** |
| `machine` | 6 | parsed from an artifact this codebase writes; reachable across a version skew |
| `unknown` | 51 | provenance not resolvable inside one file (a parameter, an import) |
| `derived` | 15 | the container is itself the product of an earlier guard |

**The `operator` class — the only one reachable by typing — is already clean.** All five sites
are in [`util/experiments/run_suite.py`](../util/experiments/run_suite.py) reading the parsed
`doc`, and ml#1895's fix was not the single-site patch the handoff describes: it added
`_require_mapping(doc, ...)` / `_require_sequence(doc, ...)` gates at `load_suite`:129-134, which
type-check every nested block before any `or {}` runs. `expand_cells` and `main` read `doc` only
after `load_suite` returns it — verified by call-site sweep, not assumed — so the guards at
`run_suite.py`:291, :697 and :698 are covered too. That class needs nothing.

## 4. What was fixed, and why these six

All six are in [`util/experiments/run_experiment.py`](../util/experiments/run_experiment.py),
and the case for them is not a census count — it is that **the file already contains the fix and
did not finish applying it.**

`_mapping(value)` at :531 is a documented non-raising type coercer whose own docstring states the
defect verbatim: *"`x.get(k) or {}` guards ABSENCE, not TYPE, so a truthy non-dict reaches the
next `.get` and raises `AttributeError`."* Its test class `MappingGuardTest` in
[`tests/test_run_experiment.py`](../tests/test_run_experiment.py) opens *"Two sites needed it"*.
Six more sites of the identical class kept the bare form. This is the
audit-every-call-site-of-a-shared-helper failure, with the reasoning already written down.

| site | function | what the `AttributeError` costs |
| --- | --- | --- |
| :866 | `_training_fsm` | the docstring promises `""` when unreadable and catches only `ServiceUnreachable` / `RunFailed` — the error escapes the stated contract |
| :989 | `drive_training` | raises **mid-poll**, killing a live training run instead of recording an outcome |
| :990 | `drive_training` | same loop; the guard the census cannot see (§2b) |
| :1383 | `check_g6_shape` | the G-6 anti-silence assert dies instead of reporting |
| :1718 | `_run_cascor` | builds the manifest of a run that **already finished** |
| :2065 | `_run_recurrence` | sibling of :1718 on the recurrence path |

Nothing upstream constrains those nested keys: `_unwrap` returns `payload["data"]` verbatim and
each caller type-checks only the envelope.

**:1718 / :2065 carry their own in-file proof.** The same file reads the same key defensively at
:1213 and :1658 — `meta = dataset_response.get("meta") if isinstance(dataset_response.get("meta"),
dict) else {}`. The author already believed that value can be a non-dict and guarded it twice;
the two manifest sites were missed. Losing provenance there is precisely what `_mapping`'s
docstring refuses: annotation is not worth failing a completed run over.

### Reachability of :1718 is conditional, and the test has to force it

`version` is `generator_entry.get("version") or _mapping(...).get("generator_version")`. `or`
short-circuits, so the fallback is evaluated **only when the registry omits a version**. The stub
had to be taught to drop it (`_ScriptedState.generator_version`), or the arm would have been
vacuous — a passing test that never reached the line it claims to cover.

## 5. Evidence

Mutation-checked before the fix landed: **5 of the 7 new tests fail against the pre-fix code**,
each with `AttributeError: 'str' object has no attribute 'get'`, and the 2 that pass are negative
controls that must (`test_training_fsm_still_reads_a_well_formed_reply`,
`test_registry_version_still_wins_when_present`).

One post-fix assertion is deliberately **not** "the same answer anyway":
`test_completed_run_still_writes_a_manifest_when_meta_is_not_a_mapping` expects `EXIT_ACCEPTANCE`,
not `EXIT_SUCCESS`. An unreadable `meta` carries no `n_features`, so G-6 fails **closed** — which
is correct. What must not happen is the pre-fix crash that produced no manifest at all for a run
whose training had already succeeded.

```bash
# the population, both units, and the blind spot
python3 util/ad-hoc/2026-09-11_falsy_guard_census.py --json util/ > /tmp/c.json
python3 util/ad-hoc/2026-09-11_falsy_guard_triage.py /tmp/c.json
python3 util/ad-hoc/2026-09-11_falsy_guard_triage.py /tmp/c.json --blind-spot

# the six fixes
python3 -m unittest tests.test_run_experiment.ServiceReplyGuardTest \
                    tests.test_run_experiment.ManifestProvenanceGuardTest    # 7 tests
python3 -m unittest tests.test_run_experiment                                # 175 tests
```

## 6. What remains, and the standing advice is unchanged

79 guards: 72 census-visible — `operator` 5, `machine` 6, `unknown` 46, `derived` 15 — plus the
7 the census cannot reach (§2b), which are unclassified because the triage reads its input from
the census and therefore inherits that blind spot.

> The §3 table is the population **before** this change (77). This one is **after** it (72). The
> six fixed sites all came out of `unknown`, which is why only that row moves.

The `operator` class is clean (§3); `derived` (15) inherits the correctness of its parent and is
a reason to fix the parent, never to call the child clean. The bulk is `unknown` (46) —
containers arriving as function parameters, which one-file provenance tracing cannot resolve and
this triage does not pretend to.

**Do not sweep them.** The reasoning in the predecessor handoff holds: this is a large mechanical
change against a class with few reproducible incidents. The six fixed here were not chosen by
count — they were chosen because the file's own helper and its own `isinstance` precedent proved
the author already considered the value untrusted. That is the bar for the next batch.

## 7. Documents this note references or changes

**References**:
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-11_cursor-fleet-round-2-closed-and-three-numbers-that-were-instrument-artifacts.md`,
`util/ad-hoc/2026-09-11_falsy_guard_census.py`, `util/experiments/run_suite.py`,
`util/experiments/stats_summary.py`.

**Changed**: this file,
`notes/JUNIPER_2026-09-11_JUNIPER-ML_FALSY-GUARD-POPULATION-TRIAGE.md`; plus
`util/experiments/run_experiment.py` (six sites), `tests/test_run_experiment.py` (two new test
classes, two new `_ScriptedState` fields), and the new
`util/ad-hoc/2026-09-11_falsy_guard_triage.py`.
