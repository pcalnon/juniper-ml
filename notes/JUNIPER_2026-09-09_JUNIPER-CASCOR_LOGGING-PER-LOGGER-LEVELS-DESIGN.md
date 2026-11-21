# Per-logger levels — dispatch design and the dual-access question

- **Project**: Juniper
- **Sub-Project**: juniper-cascor (`src/log_config/`)
- **Author**: Paul Calnon
- **License**: MIT License
- **Version**: 0.7.1
- **Last Updated**: 2026-09-10
- **Status**: DESIGN — decision 5 RULED 2026-09-10 as **A2-bind with a `_default` setter** (§9.1); §11 is the implementation design. Landing is gated on P1.1 (§11.7)
- **Answers**: [`JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`](JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md) §13 decision 5, and the Overtoad's follow-on question about serving logging as **both** class and instance calls
- **Measured at**: juniper-cascor `origin/main` `53c0338`, Python 3.13.13 (`JuniperCascor1`)

> **Documents referenced here**, by short name, full filename given once:
>
> | short name    | filename, all under `juniper-ml/notes/`                                     |
> |---------------|------------------------------------------------------------------------------|
> | **ROADMAP**   | `JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-REDESIGN-ROADMAP.md`              |
> | **RECON**     | `JUNIPER_2026-09-02_JUNIPER-CASCOR_LOGGING-CURRENT-STATE-RECONCILIATION.md`  |
> | **DESIGN**    | `JUNIPER_2026-08-29_JUNIPER-CASCOR_LOGGING-REDESIGN-DESIGN.md`               |

---

## 1. Why this document exists

ROADMAP §13 decision 5 asks whether "per-logger levels" (#573 scope 3) means **per-instance
loggers** or **named sub-loggers on the class**, and states that per-instance "means
de-classmethod-ing `isEnabledFor` and breaking ~1,200 call sites. This decides whether P4 is M or L."

The Overtoad declined to pick from that framing and asked for the investigation first, plus a specific
further question:

> *"what issues, risks, performance impacts, and concerns would arise from having both class based
> and instance based logging code paths. Having name-keyed level maps, sub-loggers, logging utils,
> etc. accessible as both class and object calls seems like a convenience win. If the fully
> functional logging code path can be utilized both as class based method calls and as per instance
> calls, the cascor modules can optimize their logging based on the specifics of each logging call
> site."*

This document answers both. **Two of the premises the decision rested on turn out to be wrong**, and
correcting them changes the recommendation.

---

## 2. Correction 1 — the break surface is ~45 sites, not ~1,200

ROADMAP §13 decision 5's "~1,200 call sites" counts **call sites**. What actually breaks under an
instance-method design is only the sites that name the **class**, because a site written
`self.logger.debug(...)` is textually identical whether `self.logger` holds the `Logger` class or a
`Logger` instance — only the **bind** changes.

Censused at `53c0338` over tracked `src/`, less `cascade_correlation/backups/` (dead, RECON N-6),
less `src/api/` (stdlib-bound, not Path A, RECON §3.1), less `src/tests/`
(`juniper-ml/util/ad-hoc/2026-09-09_p41_logger_binding_census.py`):

| access syntax          | sites | share  | breaks under instance methods?                            |
|------------------------|------:|-------:|-----------------------------------------------------------|
| `self.logger.M(...)`   | **967** | 81.4 % | **No** — identical either way; only the bind changes      |
| bare `logger.M(...)`   |   112 |  9.4 % | **No** — a local name; survives if the local binds an instance |
| `Logger.M(...)`        | **109** |  9.2 % | **Yes** — direct class access                             |
| `cls.logger.M(...)`    |     0 |    —   | —                                                          |
| **total**              | **1,188** | 100 % | **109 (9.2 %)**                                          |

And of the 109 direct-class sites, **64 are inside `logger.py` itself** — the logger logging about
its own construction, where class access is the natural form and arguably should stay. That leaves
**45 external sites**, in five files:

| file                                      | direct-class sites |
|-------------------------------------------|-------------------:|
| `src/log_config/logger/logger.py`         | 64 *(internal)*    |
| `src/main.py`                             | 15                 |
| `src/snapshots/snapshot_utils.py`         | 11                 |
| `src/spiral_problem/spiral_problem.py`    | 8                  |
| `src/log_config/log_config.py`            | 7                  |
| `src/cascade_correlation/cascade_correlation.py` | 4           |

**Bind sites are 14**, not a sweep: 5 real `self.logger = Logger` (`candidate_unit.py:187`, `:296`,
`cascade_correlation.py:3188`, `cascor_plotter.py:73`, `log_config.py:201` — a sixth grep match is
the docstring at `logger.py:1034`) and 9 `logger = Logger` locals (`cascade_correlation.py:632`,
`:3495`, `:3610`, `:3740`, `:4136`, `:5198`, `cascor_plotter.py:92`, `utils.py:125`, `:273`).

Two further binds reach the class **indirectly** and must not be missed:
`cascade_correlation.py:667` and `spiral_problem.py:310` both do
`self.logger = self.log_config.get_logger()`, and `LogConfig.get_logger` returns `self.logger`,
which `log_config.py:201` set to the `Logger` class.

**Consequence.** Per-instance is an **M**, not an L. The sizing question decision 5 was framed
around does not discriminate between the options.

---

## 3. Correction 2 — dual *syntax* already works; only dual *state* is missing

`@classmethod` is already accessible from an instance. `instance.debug(...)` on a classmethod binds
`cls` to the class and runs fine — measured at **88–97 ns** against **84–90 ns** for `Logger.debug(...)`,
a **+2 … +8 ns** difference (§4).

So the convenience the Overtoad describes — "accessible as both class and object calls" — is *not* what
is missing today. What is missing is that both access paths reach the **same class-level state**.
Every level knob is a class attribute: `_log_level` (`logger.py:193`), `_level_logger_name` (`:164`),
`_level_logger_config` (`:162`), `_level_number_cache` (`:221`), `_logging_file` (`:140`). `Logger`
carries **32 `@classmethod`s**, and `isEnabledFor`'s own docstring (`:1032-1034`) records the reason:
*"Defined as a classmethod for consistency with all other Logger methods … since Logger is used as a
class-level singleton via `self.logger = Logger`."*

**The real question is therefore not "can both syntaxes work" but "can one NAME dispatch on its
receiver — class state for class access, instance state for instance access — and what does that
cost on a path taken 646,016 times per corpus?"**

---

## 4. What each dispatch mechanism costs

Measured with `timeit.repeat(..., repeat=7)` reporting each run's **minimum** — the correct estimator
here, because scheduler noise is one-sided and only ever adds time. Bodies are trivial and identical
across mechanisms (a level compare and an early return), so **the delta is the dispatch cost**.
Level 1 against a threshold of 20, i.e. the **discarded** path — 91.0 % of real calls (RECON §6.1).

Script: `juniper-ml/util/ad-hoc/2026-09-09_p41_dualpath_mechanisms_bench.py`, with the naive
descriptor in `…/2026-09-09_p41_hybrid_descriptor_bench.py`.

Reported as the **range across four independent runs**, not a single run's figures: the host is
shared, and per-row noise reached 50 %. The ranges are what the evidence supports.

| mechanism                                             |  ns/call | vs `@classmethod` | s / 646 k corpus |
|-------------------------------------------------------|---------:|------------------:|-----------------:|
| **B** plain instance method                            | **48–50** | **−36 … −41 ns** | 0.031–0.033      |
| **A** `@classmethod` — **status quo**                  |    84–90 |               —   | 0.054–0.058      |
| **A′** `@classmethod` via an **instance**              |    88–97 |      +2 … +8 ns   | 0.057–0.063      |
| **G** metaclass design, via an **instance**            |   88–111 |      −2 … +27 ns  | 0.057–0.072      |
| **H** eager-bind in `__init__`, via an instance        |   99–116 |     +24 … +30 ns  | 0.064–0.075      |
| **I** instance-`__dict__` cache, steady state          |  243–288 |   +153 … +204 ns  | 0.157–0.186      |
| **F** metaclass **data descriptor**, via the **class** |  353–410 |   +271 … +320 ns  | 0.228–0.265      |
| **hybrid descriptor** (naive `__get__`), either path   |  441–527 |   +350 … +438 ns  | 0.285–0.341      |

**The pattern is unambiguous.** Every mechanism that makes **one name** dispatch on its receiver —
the naive hybrid, the metaclass data descriptor, the instance-`__dict__` cache — costs **3–6× a
classmethod**. Every mechanism that lets the two access paths be **two different bindings** costs
nothing, or is *cheaper* than today.

Two secondary findings from the same runs, both actionable:

- **A plain instance method is 36–41 ns FASTER than a classmethod** (48–50 vs 84–90). Moving the hot
  path to instance methods is a small performance *win*, not a cost.
- **`*args, **kwargs` packing dominates the closure mechanisms.** H (a fixed-signature lambda) is
  99–116 ns; I (a `*a, **kw` closure) is 243–288 ns, on otherwise identical work. Any closure
  introduced on this path must take a fixed signature.

### 4.1 A trap, found by measurement rather than by reading

The obvious metaclass formulation — put `debug` on the metaclass for class access and on the class
for instance access — **does not work**, and fails in a way that reaches the caller as an argument
shift rather than an error at definition time:

```text
TypeError: MetaStyle.debug() missing 1 required positional argument: 'message'
```

`type.__getattribute__` searches the **class's own MRO before** falling back to non-data metaclass
attributes, so the class's instance method shadows the metaclass's function for `Logger.debug`, and
the class call arrives with `self=1, level="m"`. Only a **data** descriptor on the metaclass (one
defining `__set__`/`__delete__`) outranks the class `__dict__` — and that is row **F**, at +263.7 ns.

This is worth recording because the shadowing is silent at import and at definition: nothing warns,
and a suite that only exercises the instance path stays green.

### 4.2 The metaclass design also defeats static analysis

Found by CI rather than by design: **CodeQL raised three "Wrong number of arguments in a call"
alerts** against the corrected, working mechanism **F**, on ml#1860 — *"Call to method
MetaStyle.debug with too few arguments; should be no fewer than 3."*

CodeQL is right about the source and wrong about the runtime. It resolves `MetaStyle.debug` to the
**class's** three-argument instance method, exactly as a human reader would; at runtime the
metaclass **data** descriptor wins and the two-argument call is correct. The benchmark now prints
the resolution to settle it:

```text
MetaStyle.debug        -> _MetaDataDescriptor.__get__.<locals>.bound
MetaStyle().debug      -> MetaStyle.debug
```

**This is an argument against mechanism F beyond its +271…+320 ns.** A design that a whole class of
tooling cannot verify — and that reports a *false positive on every correct call site* — imposes a
permanent cost on review, on CI, and on every future reader. It also blocks merges: an unresolved
CodeQL thread holds `mergeStateStatus: BLOCKED` while all 17 required contexts read green.

---

## 5. Recommendation — two objects, not one overloaded name

> **Superseded in part by §10.** The *principle* below — two bindings, never one name dispatching on
> its receiver — is what was adopted. Its concrete proposal (keep the classmethods as a **second**
> implementation) was replaced by the measured **A2-bind** form, which keeps one implementation and
> is faster on the class path too. Read §5 for the argument, §10–§11 for what ships.

**Do not overload a single name to dispatch on its receiver.** The measured cost is 3–6× on the path
this whole arc has been making cheaper, and it buys nothing that two bindings do not already give.

Recommended shape:

1. **`Logger` keeps its 32 classmethods, unchanged.** The 109 `Logger.M(...)` sites — 64 of them
   inside `logger.py` — are untouched, at 84–90 ns. The class path remains the process-wide default
   and the bootstrap path (it must keep working before any instance exists; `logger.py`'s own
   construction logging depends on that).
2. **Add a factory returning a per-logger instance** whose class defines the eight emit methods and
   `isEnabledFor` as **plain instance methods** — 48–50 ns, *faster than today*, with the level knobs
   as instance attributes falling back to the class value when unset.
3. **The 967 `self.logger.M(...)` sites change zero characters.** Only the **14 bind sites** change,
   from `self.logger = Logger` to `self.logger = <factory>("candidate_unit")` — plus the two indirect
   binds at `cascade_correlation.py:667` and `spiral_problem.py:310`.

This delivers precisely what the Overtoad asked for — one fully-functional logging path reachable both
as class calls and as per-instance calls, with per-call-site tuning — **and it is faster on the hot
path than the status quo**, because the 967-site majority moves from classmethod dispatch to instance
dispatch.

> **Naming note.** `get_logger` is **taken twice** and cannot be the factory name without a
> collision: `Logger.get_logger(self)` (`logger.py:1281`) is an instance method that returns `self`,
> and `LogConfig.get_logger(self)` (`log_config.py:493`) returns `self.logger`. Pick a new name
> (`Logger.for_name(...)` / `Logger.bind(...)` / `Logger.sub(...)`) or deliberately re-purpose
> `logger.py:1281`, whose body is `return self`.

---

## 6. Issues, risks and concerns of a dual-access design

Answering the Overtoad's question directly. These apply to the recommendation in §5 as much as to the
rejected mechanisms, except where noted.

| # | concern | severity | notes |
|---|---------|----------|-------|
| 1 | **Two sources of truth for "the level".** A class-level default and per-instance overrides mean a record's fate depends on which binding the call site used. An operator who sets the global level and sees a module stay quiet has no error to read. | **high** | Mitigate with P4-G1's precedence truth table and a `Logger.describe_levels()`-style dump. This is the cost of the feature, not of the mechanism. |
| 2 | **The state split in N-3 gets WIDER before it gets narrower.** Today `isEnabledFor` reads `_log_level` and the emit filter reads `_level_logger_config`/`_level_logger_name`, and they disagree. Adding a per-instance layer over an already-disjoint pair multiplies the states. | **high** | **P1.1 is a hard prerequisite.** Do not start P4 until one resolved value drives both paths. ROADMAP already gates P4 on P1 for a weaker reason than this. |
| 3 | **Bootstrap ordering.** Class-level logging must work before any instance exists — `logger.py` logs during its own construction, and `logger.py:768`'s root-clobber guard runs at `Logger.__init__` time. A factory that itself logs through an instance can recurse. | medium | The factory must use the class path only, and must not be reachable from `Logger.__init__`. |
| 4 | **Forkserver inheritance of per-instance state.** `cascade_correlation` is preloaded (RECON N-2), so instances created at import or forkserver time are inherited by every child. Per-instance levels set in the parent **after** forkserver start are invisible to children — the classic P4.4 failure. | medium | P4.4 already requires demonstration in a child; extend it to per-instance state specifically. |
| 5 | **Pickling.** `CandidateUnit.__setstate__` already re-binds `self.logger` (`conftest.py:914` stubs exactly this seam), so a logger instance must be excluded from `__getstate__` or be trivially reconstructible. A closure-bearing instance (mechanism **H**) is **not picklable**. | medium | Argues against **H** and for plain instance methods, which pickle normally. |
| 6 | **Reference cycles.** Mechanisms **H** and **I** put a closure over `self` into `self`, creating an `instance → closure → instance` cycle that only the cycle collector reclaims. At one logger per `CandidateUnit`, across a cap-64 pool, that is real. | medium | Another argument for plain instance methods. Not applicable to §5's recommendation. |
| 7 | **Memory per instance.** A logger per `CandidateUnit` costs one object plus its level attributes per candidate. Small, but it is per-candidate in a pool that reaches 64. | low | Measure in P4; keep the instance's `__slots__` tight. |
| 8 | **The mirror.** `candidate_unit/`, `utils/`, `log_config/` and `cascor_constants/` are byte-gated (ROADMAP trap 2), and `log_config/logger/logger.py` is on `_INTENTIONAL_DIVERGENCE`. Any P4 edit touching the bind sites in `candidate_unit.py` carries a mirror re-extraction **and a package release**. | medium | Now governed by the ruled decision 4 (converge — see §8). |
| 9 | **Two idioms invite drift.** Once both work, new code picks either, and the choice stops being deliberate. | low | P6.3's lint rule is the natural home for a "use the instance binding inside `candidate_unit`/`cascade_correlation`" rule. |
| 10 | **`isEnabledFor` as an instance method changes the 8 guard sites' meaning.** They currently ask a class-wide question; they would ask a per-instance one. That is the intent, but it is a behaviour change at exactly the 8 sites whose integers are already wrong (RECON N-3). | medium | Sequence P1.3 (fix the integers) **before** P4 changes what the predicate means. |
| 11 | **A receiver-dispatching name is invisible to static analysis.** §4.2: CodeQL raises a false "too few arguments" on **every correct class-path call site** under mechanism F, and an unresolved CodeQL thread holds a PR at `BLOCKED` while all 17 required contexts read green. | **high** *(F only)* | Does **not** apply to §5's recommendation, where each name has one receiver and every call site is statically checkable. This is a further reason to prefer it. |

**Not a concern, contrary to expectation:** raw dispatch cost, *provided* §5's shape is used. The
967-site majority gets **faster**. It is only the one-name-two-receivers mechanisms that are
expensive, and none of them is needed.

---

## 7. What this document does not settle

- **It does not measure the real logger.** All figures in §4 are dispatch-only, on synthetic bodies,
  on one machine and one interpreter (Python 3.13.13, `JuniperCascor1`). They size the *delta between
  mechanisms*, which is the decision at hand; they are **not** a claim about cascor's logging share.
  Per-row run-to-run noise reached 50 %, which is why §4 reports the RANGE across four runs rather than any single run's figures.
- **It does not re-open P1.** The state split (RECON N-3) and the `is_valid_level` typo
  (`logger.py:341`, N-3a) remain prerequisites, and concern 2 above raises their priority.
- **It does not decide the precedence chain.** ROADMAP P4.2's chain — per-logger env → global env →
  per-logger config → global config → default — is unchanged by this analysis.
- **It carries no post-#598 measurement.** P0.1 still owes the corpus; nothing here substitutes.

---

## 8. Decisions already ruled, recorded here for the implementer

Taken by the Overtoad on 2026-09-09 against ROADMAP §13; §13.1 of that document is the canonical record.

| # | decision | ruling |
|---|----------|--------|
| 1 | Does P2 run at all? | **Pre-authorised: drop P2 if P0.2 puts the logging share below 10 %** |
| 2 | P3.2 console-sink default | **On by default, off in the harness profile** — a policy switch, not runtime detection |
| 3 | P5.1 `configure_logging` fork | **Narrow the fork to the delta**; the rotator stays |
| 4 | P0.6 mirror policy | **Converge** — re-extract `logger.py`, retire `_INTENTIONAL_DIVERGENCE` |
| 5 | P4.1 per-logger shape | **RULED 2026-09-10: A2-bind, with a `_default` setter** (§9.1, §11) |
| 6 | Call-site migration scope | **P6.1 + P6.2 + P6.3 authorised; P6.4 open** pending the sample review |
| 7 | §7.1 swallowed-pytest investigation | **Authorised**, as written in DESIGN §7.1 |

Decision 4's ruling matters to this document: it means a P4 edit to `candidate_unit.py`'s bind sites
carries a live mirror obligation, and that the package's logger — currently pre-#563 **and**
pre-#598, published on PyPI at 0.1.0 — is being brought back into line rather than left frozen.

---

## 9. The decision, and how it was taken

**The question put to the Overtoad:** which shape delivers per-logger levels? Four were tabled:

- **(a) A — two bindings, two implementations.** `Logger` keeps its classmethods; a factory returns
  per-logger instances with plain instance methods. M-sized, faster on the hot path, hazard-free —
  but eight (in fact nine, §11.1) methods exist twice and must stay in step.
- **(b) Named sub-loggers on the class only.** A name-keyed level map consulted by the existing
  classmethods; no instances, no bind changes. Two realisations, both worse: passing the name
  explicitly is a **1,188-site edit**, and deriving it from the caller's frame forces frame
  resolution *before* the filter, which is precisely what **P2.1 exists to undo** — the two are
  mutually exclusive.
- **(c) One overloaded name, dispatching on receiver.** Rejected on two independent grounds:
  measurement (+153 to +438 ns per call, 3–6× the status quo, on the 646 k-call path) and
  verifiability (§4.2 — static analysis cannot resolve it, and reports a false positive on every
  correct class-path call).
- **(d) A2 — two entry points, ONE implementation.** The classmethods become the default instance's
  methods, so there is a single logging path reachable both ways. §10 shows its two mechanisms are
  3× apart, and that the **`-bind`** form is faster than the status quo on *every* call site.

**A correction against the first draft of this document.** §5 recommended (a), on an *estimate* that
A2's class-path indirection would cost ~+45 ns. Measured, the delegator form costs **+146 ns** —
the estimate was wrong by 3×. That measurement also surfaced the `-bind` form, which was not in the
original option set and which dominates (a): same hot path, **faster** class path, one
implementation. §5 stands as the argument for two *bindings*; §10 supersedes its choice of mechanism.

### 9.1 RULED 2026-09-10 — A2-bind, with a `_default` setter

The Overtoad selected **A2**, in its `-bind` form, and directed that `_default` be a **setter that
reassigns the bound attributes** rather than relying on mutate-in-place discipline. §11 is the
implementation design; §10 records the measurement that chose between A2's two forms.

---

## 10. Why A2-**bind**, and not the A2 delegator

A2 has two possible mechanisms, and they are 3× apart. Measured against juniper-cascor's **real**
signature — `debug(cls, message=None, *args)` (`logger.py:548-610`) — because the delegator must
*forward* `*args`, and §4 already showed variadic packing dominating dispatch. Discarded path,
best-of-7 × 5 outer runs (`juniper-ml/util/ad-hoc/2026-09-10_p41_a2_delegation_bench.py`):

| row | ns/call | vs status quo |
|-----|--------:|--------------:|
| **SQ-class** — status quo; what all 1,188 sites cost today | 95–110 | — |
| **A/A2-inst** — plain instance method | **55–77** | **−40** |
| **A2-bind** — the default's *bound method* as the class attribute | **74–89** | **−21** |
| A2-delegator, eager default | 241–266 | **+146** |
| A2-delegator, lazy default | 249–276 | +154 |

With one `%`-argument the delegator degrades further (+168): it pays a second frame **and** repacks
`*args`. **A2-bind pays neither** — the class attribute *is* an already-bound method, so a class
call is an attribute lookup plus the same instance call the hot path makes.

**A2-bind is therefore faster than the status quo on every call site**, which A2-delegator is not
and option A is not:

| | 1,079 bound sites | 109 class sites | implementations |
|---|---:|---:|---:|
| **A** | 55–77 (−40) | 95–110 (+0) | 2 |
| **A2-bind** *(ruled)* | 55–77 (−40) | **74–89 (−21)** | **1** |
| A2-delegator | 55–77 (−40) | 241–266 (+146) | 1 |

> **The 112 bare-local sites move with the binds.** `logger = Logger` inside
> `train_candidate_worker` (`cascade_correlation.py:3495`) and `_train_candidate_unit` (`:3740`) is
> **worker-path** code. Converting those 9 local binds moves 112 sites onto the fast path, so the
> fast population is **1,079**, not 967.

**Two costs of A2-bind are inert in this codebase**, verified rather than assumed: **nothing
subclasses `Logger`** (so no subclass inherits a binding to the parent's default), and **nothing
introspects the emit methods** (no `__func__`, `ismethod`, or `signature()` use against them).

---

## 11. Implementation design — A2-bind

### 11.1 It is NINE attributes, not eight

The 8 emit methods (`trace`, `verbose`, `debug`, `info`, `warning`, `error`, `critical`, `fatal`,
`logger.py:548-610`) **plus `isEnabledFor`** (`:1026`). Leaving `isEnabledFor` behind would make the
8 guard sites in `candidate_unit.py` read the class default while the emit path read the instance —
**that is exactly N-3's shape**, reintroduced one layer up. The nine move together or not at all.

### 11.2 The shape

Prototyped and verified in `juniper-ml/util/ad-hoc/2026-09-10_p41_a2bind_prototype.py` (exit 0):

```python
BOUND_NAMES = ("trace", "verbose", "debug", "info", "warning",
               "error", "critical", "fatal", "isEnabledFor")   # NINE

class _LoggerMeta(type):
    # On the METACLASS: `Logger._default = X` assigns on the CLASS, and a plain
    # property on the class only intercepts assignment on its INSTANCES.
    def _set_default(cls, bound):
        if not isinstance(bound, BoundLogger):
            raise TypeError(...)
        # CALLABLE, not merely present -- a subclass shadowing one of the nine with a
        # non-callable passes hasattr and would bind None onto the class, turning every
        # guard site into a TypeError at first call.
        missing = [n for n in BOUND_NAMES if not callable(getattr(bound, n, None))]
        if missing:
            raise TypeError(f"... refusing to leave the class half-bound")
        type.__setattr__(cls, "_default_instance", bound)
        for name in BOUND_NAMES:
            type.__setattr__(cls, name, getattr(bound, name))
    _default = property(_get_default, _set_default)
```

The descriptor sits on the **assignment** path, which is rare. The **call** path never touches it:
`Logger.__dict__["debug"]` is a `method` object, so a class call is a plain attribute lookup.

### 11.3 What the prototype established

| # | property | result |
|---|----------|--------|
| 1 | the call path keeps its speed | class **84–89 ns**, bound **60–67 ns**, both under the status quo's 95–110 |
| 2 | **the setter closes the stale-binding hazard** | assigning `_default` rebinds **9/9**; the pre-setter version left them stale and silently ignored the swap |
| 3 | per-logger levels are independent | `candidate_unit` at TRACE emits while `spiral_problem` at FATAL and the root at INFO do not |
| 4 | **guard and emit agree, per logger** | 9/9 level×logger combinations — the anti-N-3 check |
| 5 | the guard invariant holds | `all(getattr(Logger, n).__self__ is Logger._default for n in BOUND_NAMES)` |
| 6 | a bad assignment is **refused and atomic** | wrong type *and* missing-callable both rejected; the invariant still holds afterwards |

> One measurement caution: a single run of row 1 read **169 ns** for the class path against 84–89 ns
> across five repeats. The host runs seven-plus concurrent sessions; that reading was noise. Any
> re-measurement must repeat, and must report the range.

### 11.4 Migration — 16 binds, zero call sites

| bind | file:line |
|------|-----------|
| `self.logger = Logger` ×5 | `candidate_unit.py:187`, `:296`, `cascade_correlation.py:3188`, `cascor_plotter.py:73`, `log_config.py:201` |
| `logger = Logger` ×9 | `cascade_correlation.py:632`, `:3495`, `:3610`, `:3740`, `:4136`, `:5198`, `cascor_plotter.py:92`, `utils.py:125`, `:273` |
| **indirect** ×2 | `cascade_correlation.py:667`, `spiral_problem.py:310` — both `self.log_config.get_logger()`, which returns the class via `log_config.py:201` |

**A missed bind degrades gracefully** (verified): a site left as `self.logger = Logger` still works,
on the root level, with no `TypeError`. So the migration can be incremental and a miss is a
lost-granularity bug, not an outage.

**The factory needs a new name.** `get_logger` is taken twice — `Logger.get_logger` (`logger.py:1281`,
body `return self`) and `LogConfig.get_logger` (`log_config.py:493`). The prototype uses
`Logger.for_name(name, level=None)`; `bind` / `sub` are equally fine. Re-purposing `logger.py:1281`
is also open, since its body is `return self`.

### 11.5 Obligations carried from §6

- **Concern 2 — P1.1 is a hard prerequisite, and this design does not relax it.** Per-logger state
  over an already-disjoint guard/emit pair multiplies the states. Property 4 above is the acceptance
  check: guard and emit must agree for every logger at every level.
- **Concern 3 — bootstrap.** `Logger._default` must be assigned at class-definition time, before the
  first class-path call, because `logger.py` logs during its own construction. The prototype assigns
  at module scope immediately after the class body. The setter must not itself log.
- **Concern 4 — forkserver.** The default is built at import, so it is inside the preload snapshot;
  per-logger levels set in the **parent after forkserver start** will not reach children. P4.4's
  demonstration must cover per-instance state specifically, in a child, under a distinct
  `JUNIPER_CASCOR_LOG_DIR` (trap 1).
- **Concern 5 — pickling.** `BoundLogger` is `__slots__`-based and holds only a name and an int, so
  it pickles. `CandidateUnit.__setstate__` (stubbed at `conftest.py:912`) must rebind to the named
  logger, not to the class.
- **Concern 8 — the mirror.** `candidate_unit.py` bind edits are inside a byte-gated tree, so they
  carry a mirror re-extraction and a `juniper-cascor-model` release under the ruled decision 4.

### 11.6 The guard tests this design owes

1. `all(getattr(Logger, n).__self__ is Logger._default for n in BOUND_NAMES)` — pins the invariant.
2. Assigning `_default` rebinds **all nine**; count the rebindings, do not spot-check one.
3. A `_default` missing any of the nine, or holding a non-callable, is **refused**, and the previous
   binding survives the refusal intact.
4. Guard/emit agreement per logger at TRACE / VERBOSE / DEBUG / INFO — the anti-N-3 test, and the
   thing P1.5 generalises.
5. A per-logger level demonstrated **in a forkserver child** (P4-G2).

### 11.7 Sequencing

P4 remains gated on **P1** (ROADMAP §2), and §6 concern 2 raises rather than lowers that gate.
**No cascor code lands from this document until P1.1 reconciles the two level states.** What is
deliverable now is this design plus the verified prototype; the first cascor PR is P1.1's.

---

## 12. References

- [cascor#573](https://github.com/pcalnon/juniper-cascor/issues/573) — the issue and Overtoad scope
- **ROADMAP** §13 decision 5, §7 (Phase 4), P4-G1…P4-G4
- **RECON** N-3 / N-3a (the level-state split), N-2 (forkserver), §3.1 (the call-site census method)
- **DESIGN** §7 decisions 1–6, and §7.1 (the swallowed-pytest protocol)
- `juniper-ml/util/ad-hoc/2026-09-09_p41_logger_binding_census.py` — the §2 census
- `juniper-ml/util/ad-hoc/2026-09-09_p41_dualpath_mechanisms_bench.py` — the §4 table
- `juniper-ml/util/ad-hoc/2026-09-09_p41_hybrid_descriptor_bench.py` — the naive-descriptor rows
- `juniper-ml/util/ad-hoc/2026-09-10_p41_a2_delegation_bench.py` — the §10 table (A2-bind vs A2-delegator)
- `juniper-ml/util/ad-hoc/2026-09-10_p41_a2bind_prototype.py` — the §11 prototype and its six checks
- `juniper-ml/util/ad-hoc/2026-09-02_logging_doc_refutation_probe.py` — the level-state probe
