# HANDOFF 2026-09-15 — round 39: thirty rulings taken, eight implemented, and the rest sequenced into PRs

Successor to
`HANDOFF_2026-09-09_defect-register-round-38-the-three-way-prompt-shipped-and-two-corrections-that-reversed-themselves.md`
(the **predecessor**; every bare "round 38" below means that file).

**Validate this document with independent agents before trusting it** (memory
`feedback_validate_handoff_prompts_independently`). Its own record is §7 — and read §7 before §0,
because round 1 of that validation found a shipped regression and this document's first draft was
wrong in eleven places.

**A bare "§N" means a section OF this document.** Every reference to another file names it —
and this document is
`prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-15_defect-register-round-39-thirty-rulings-taken-eight-implemented-and-the-arc-sequenced.md`,
which the changed-file list in §2 must name like any other. All
dates and times UTC.

**Register** (`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`): **119 rows, 94
fixed, 25 open** — 17 primer + 8 post-primer.

> ## REVALIDATED 2026-09-21 — still current, with five corrections
>
> A later session re-ran §1's verification block in full and swept all nine repos. **Every item
> in §0 was still outstanding six days on**, and the register was byte-identical to the state
> described above: `119 rows | 94 fixed | 25 open`, crosscheck `94 / 94 / 94 AGREE`, 33 tests OK,
> archive test OK, and the open-id set identical to the set §0 sequences. No PR merged in any of
> the nine repos between 2026-09-15 and 2026-09-21 touches D-A…D-G, C-A…C-C, X-A…X-C or M-A, and
> no open PR does either. The intervening days went to other arcs (the logging arc's P1.3/P1.5,
> container-registry Wave 3, the soak arc, the perf lane, duplicati/backup, the CI budget alarm,
> and releases).
>
> **The sections below are corrected in place where they had drifted. The historical record —
> §2's changed-file list, §3, §4, §5, §7 — is left exactly as that session wrote it**, because
> those sections are an archive of what was done and when, not a statement about today. The
> corrections are:
>
> 1. **§0.3's X-C names three copies of the API-key check. There are four.**
>    `juniper-canopy/src/security.py:74` carries the identical short-circuiting
>    `any(hmac.compare_digest(...))` and is named in neither §0.3 nor the `APD-CASCOR-005` row —
>    whose §3 heading in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` likewise
>    reads *"in two of three copies"*. It is **three of four**. See §0.3 and §9.
> 2. **§1's verification block greps for a `kept_values` loop that does not exist.** The shipped
>    identifiers are `prior_values` / `keep`. Corrected in §1 — the old text made a successor
>    conclude they were on a pre-#404 commit when they were not.
> 3. **§2's last table row — "juniper-ml (this PR)" — merged.** It is **juniper-ml#1947**,
>    2026-09-16T03:17:15Z. Recorded in §2 as a completion of that row, not a rewrite of it.
> 4. **§8's ecosystem-note line was stale and mis-cited.** It claimed `Juniper/AGENTS.md` was
>    "stale again at 5.0.0" and pointed at §5.8. §5.9 of this document records the 5.0.0 update
>    landing 2026-09-16, and `Juniper/AGENTS.md` now reads `5.0.0`. Both fixed in §8.
> 5. **§6's git status describes a worktree that is no longer the working one.** Superseded by §9.
>
> **`APD-DATA-047` is RULED.** §0.6's outstanding owner decision was put to the owner on
> 2026-09-21 and **ratified at `1e11`**. §0.6 and §8 updated. That leaves **no owner decision
> owed anywhere in the register**.
>
> **The register therefore no longer reads as the line above this banner says.** The `119 rows,
> 94 fixed, 25 open` at the top of this document was verified true on 2026-09-21 and was then
> changed by that close, in the same session: it now reads **`119 rows | 95 fixed | 24 open`**,
> crosscheck **`95 / 95 / 95, AGREE`**. The pre-close figures are left standing above because
> they are what §1's block was checked against; §9.6 carries the close. Re-derive with
> `util/ad-hoc/register_open_set.py` rather than reading either figure — that is the register's
> own standing instruction, for exactly this reason.
>
> New work started under this revalidation is §9.

**What changed about this arc, and it is the only thing you need to hold in mind:** for two years
of register rounds the blocking constraint was that nothing could be actioned without an owner
ruling, and the set of actionable rows was empty. On 2026-09-09 and 2026-09-11 the owner ruled on
**all thirty open questions**, interactively, in batches of four. That set is no longer empty. The
work is no longer "get a decision"; it is "implement what was decided", and §0 is that list
sequenced into PR-sized units.

**The owner's partial-data spec exists verbatim only in the memory
`project_partial_data_contract_arc_2026-09-05`** — its table of the three options and their
wire forms. `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` and every handoff paraphrase it. D-A
(§0.1) implements option 3's wire form, so read the memory, not the paraphrase.

---

## 0. Remaining work

Eight rulings are implemented — seven by juniper-data#395, and the regression #395 itself shipped
by juniper-data#404 (§4). Twenty-five rows remain open, all but one ruled. Below they are grouped
into the PRs that would implement them, in dependency order, with the file collisions that make
several of them un-parallelisable.

### 0.1 juniper-data — the ruled HTTP and contract work

**D-A … D-D share `juniper_data/api/routes/datasets.py`. Do NOT run them in parallel** — that file
is ~1000 lines and every one of them edits route decorators. Sequence them, or one of them spends
its life DIRTY.

1. **D-A · the tri-state `allow_truncation`** — register row **`APD-DATA-052`**. The contract
   change, and the largest. Ruled 2026-09-09: `allow_truncation` becomes `true | false | null`,
   with `null` (or omitted) deferring to the deployment, so a caller can refuse truncation even
   where the operator enabled it. **This reverses a deliberate, documented, test-pinned design**,
   and the test whose name IS the old behaviour must be inverted rather than deleted:
   `juniper_data/tests/unit/test_csv_import_generator.py::test_request_cannot_opt_out_of_deployment_allow_truncation`.
   The half that survives is that an *omitted* flag still defers to the deployment. Also update:
   the `"A client cannot opt out of the operator's choice"` docstring in
   `juniper_data/generators/equities/generator.py` **and the same documented asymmetry in
   `juniper_data/generators/csv_import/generator.py` at `:133` and `:145`** ("there the
   operator's choice cannot be undone") — the first draft named only the equities one — the
   three `or settings.*` sites
   (`csv_import/generator.py`, `equities/generator.py` ×2), `juniper-data/docs/REFERENCE.md` and
   `juniper-data/CHANGELOG.md` (both filenames also exist in juniper-ml).
   **Do not reach for a `model_fields_set` presence guard** — it was measured and does not work;
   see §5.1.
   > `APD-DATA-052` was filed **2026-09-15, six days after the ruling**. Until then this work had a
   > ruling and no row: it was written down only in the predecessor handoff named at the top of this
   > document, and §4.9 of `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` had already flagged that as a gap. Round-1 validation caught that §0 was sequencing a defect the
   > register did not contain. **A ruled item with no row is invisible to every count the register
   > produces**, and to anyone who does not read a superseded handoff.
2. **D-B · caching.** `APD-DATA-017` + `APD-DATA-032` + `APD-DATA-029`. A strong `ETag` from the
   stored SHA-256; move `access_count` / `last_accessed_at` out of `DatasetMeta`'s representation
   (they change on every read and are exactly what blocks a metadata ETag); emit `Content-Location`
   naming the canonical `/{dataset_id}` from `/latest`. **D-B also edits storage** — the two
   counters live in `juniper_data/storage/base.py` (4 sites) and `storage/postgres_store.py` (2) as
   well as `core/models.py` — so see the D-F note below.
3. **D-C · the error surface.** `APD-DATA-030` + `APD-DATA-031` + `APD-DATA-022`. RFC 9457
   problem+json from all three sources (`api/app.py`'s three handlers, `api/middleware.py`, route
   raises), with a stable `type` and a retryability signal; and the error surface declared once as
   **router-level defaults** rather than per-route `responses={}`. Note `Retry-After` already exists
   on the auth-throttle 429 — the row's claim that nothing carries a retryability signal is too
   broad, and is corrected in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`.
4. **D-D · lists, pagination, identity.** `APD-DATA-026` + `APD-DATA-027` + `APD-DATA-028` +
   `APD-DATA-008`. Make `/filter` canonical and deprecate the bare list in OpenAPI while keeping it
   served; emit RFC 8288 `Link`; add `/v1/datasets/named/{name}/versions` and `/named/{name}/latest`
   (the `named/` prefix is required — `/{dataset_id}` owns that path slot); and return **200 on
   reuse, 201 only on creation**.
5. **D-E · idempotency.** `APD-ECO-001`, ruled as the **full mechanism on every mutating route**,
   including create — the narrower option (key only batch-delete, cleanup-expired and
   batch-create, and document create's natural content-addressed idempotency) was offered and
   rejected. Needs a key store and an expiry policy, which lands in `juniper_data/storage/`;
   likely a new module, but it is the same package D-B and D-F are both editing, so run it
   **after D-F**. **Three things the ruling does not settle and the implementer must:** the TTL,
   the store backend, and the enumeration of "every mutating route" — write them down before
   coding, because none of the three is recoverable from the ruling.
6. **D-F · storage pushdown.** `APD-DATA-019`, ruled **all stores**: one Postgres pushdown, LocalFS
   and Redis index builds, four delegations. **This is NOT independent of the route work, and the
   first draft of this document said it was.** D-F edits `storage/base.py` and
   `storage/postgres_store.py`; so does D-B, for the two counters. Run D-F **after** D-B, or resolve
   one conflict in `base.py`.
7. **D-G · the four rows juniper-data#395 and #404 created.** `APD-DATA-048` (a feature-column
   parameter, so `adj_close` is reachable as a feature again — it is *not* wholly unreachable
   today; `basis_price_field` still selects it for the cost basis, see §4), `APD-DATA-049` (migrate
   the **486** orphaned SEC cache payloads into the versioned path), `APD-DATA-051` (the comment
   figures that cannot be reproduced, §5.11), and `APD-DATA-047` (**owner decision owed**: ratify or
   remove the ceiling, now at **1e11**). `APD-DATA-046`, Berkshire's dual-class mismatch, stays
   deferred with a share-class-aware lookup recorded as its remedy — and **#404 made it visible**:
   the two classes are now filtered as a scale error, pinned by its own test. **That pin is
   synthetic, and knowing so matters**: the bundled BRK payload holds 7 facts, all Class A
   (941,481–1,103,764), and both the old and new filters deliver an identical 6 from it. The
   dual-class collision is demonstrated by the fixture, not by the cache — so a successor who
   goes looking for it in the real data will not find it there.

### 0.2 The three clients

Independent of everything above. **NOT independent of each other** — C-A adds a `timeout`
parameter to public method signatures and C-B changes the return annotation of many of the same
methods: **38 identical `def` lines in the same two files** (12 of 20 public methods in
`juniper_data_client/client.py`, 26 of 30 in `juniper_cascor_client/client.py`). Run them in
sequence or expect a conflict on nearly every line either touches. The first draft of this
document said they were independent.

- **C-A · `APD-ECO-003`**, per-call timeout on the public methods of all three clients. **The three
  are in three different states, and the first draft of this document generalised from one of
  them.** juniper-data-client's transport is ready —
  `juniper_data_client/client.py:302` does `kwargs.setdefault("timeout", self.timeout)` — so only
  the public signatures are missing. juniper-cascor-client's is **not**:
  `juniper_cascor_client/client.py:530` takes no `**kwargs` and passes `timeout=self.timeout`
  literally, so `_request` itself has to change before any signature can matter.
  juniper-recurrence-client is **2 of 9, not complete** — `train` and `crossval` expose a
  per-call timeout; `predict`, `training_status`, `crossval_status`, `get_model`, `get_dataset`,
  `health_check` and `is_ready` do not, and since **no** method takes `**kwargs` the transport's
  `setdefault` at `client.py:265` is unreachable from seven of the nine. What it does have is the
  right *shape* for the two it implements, including reporting the **effective** timeout rather
  than `self.timeout` in the error (`client.py:266-269`) — read that before writing the other
  seven. The `APD-RCLIENT-002` close says plainly that the other public calls stay on the
  client-wide scalar; an earlier draft of this document and the `APD-ECO-003` ruling text in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` both lost that qualifier, and the ruling text is corrected.
- **C-B · `APD-ECO-004`**, `TypedDict` response shapes for the 43 `Dict[str, Any]` returns in
  juniper-data-client and juniper-cascor-client. Ruled against sharing the servers' Pydantic models
  here, because those ship as separately released packages and the lockstep is the objection.
- **C-C · `APD-RCLIENT-004`**, and it is deliberately the OPPOSITE ruling: the recurrence client
  **uses its server's own models**, because client and server ship from one repository at one
  version, so the lockstep objection does not apply. If you find yourself making these two
  consistent, re-read the `APD-RCLIENT-004` ruling in §4.9 of `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`.

### 0.3 juniper-cascor and juniper-service-core

- **X-A · `APD-CASCOR-008`**, derive the truncatable-generator set from juniper-data's
  `/v1/generators`. Ruled against the two cheaper options (widening cascor's `dataset_type`
  Literal, or narrowing the constant to its one reachable member). The startup dependency this
  introduces is a constraint on the implementation, not a reason to revisit — but the ruling does
  **not** say what cascor does when juniper-data is unreachable at startup, and that has to be
  decided before the code is written.
  > **This edit is byte-mirrored, and the mirror has its own CI.** The constant is
  > `_PROJECT_API_TRUNCATABLE_GENERATORS`, at **line 139 of both**
  > `juniper-cascor/src/cascor_constants/constants_api/constants_api_defaults.py` and
  > `juniper-cascor/juniper-cascor-model/cascor_constants/constants_api/constants_api_defaults.py`
  > (also in each file's `__all__`, line 279). `juniper-cascor-model/tests/test_drift.py`
  > compares the two trees byte-for-byte over
  > `_EXTRACTED_DIRS = ("candidate_unit", "utils", "log_config", "cascor_constants")`. Mirror
  > with `diff`, not by remembering that you copied the file — and note that
  > `Test (Python 3.12)` is **not a required check on juniper-cascor**, so a red mirror merges
  > and leaves `main` red with nothing naming it. juniper-cascor#633 did exactly that.
- **X-B · `APD-CASCOR-013`**, clear `_dataset_shortfall` at the **start of every run**
  (`juniper-cascor/src/api/lifecycle/manager.py` — init at `:1243`, the write in
  `_reload_dataset` at `:4175`, the read in `get_status`). **Collides with X-A**, which edits the
  truncatable-set membership test in the same file around `:3876`. Sequence the two.
- **X-C · `APD-CASCOR-005`**, port juniper-data's explicit non-short-circuiting `matched`-flag
  loop into cascor and `juniper-service-core`. All three sites, since the first draft named
  none of them: the **reference** is
  `juniper-data/juniper_data/api/security.py:99-103`; the two to change are
  `juniper-cascor/src/api/security.py:61` and
  `juniper-ml/juniper-service-core/juniper_service_core/security.py:66`, both currently
  `return any(hmac.compare_digest(api_key, k) for k in self._api_keys)`. Every copy already
  uses `compare_digest`; it is the `any(...)` **iteration** that short-circuits. Candidate for a
  named guard in `juniper-ml/tests/test_service_fork_drift.py`. Note
  `juniper-ml/juniper-service-core/` is a published sub-package, so this is a release, not just
  a commit.
  > **CORRECTION 2026-09-21 — there is a FOURTH copy, and it is three of four, not two of
  > three.** `juniper-canopy/src/security.py:74` carries the identical short-circuiting line in
  > an identical `APIKeyAuth.validate`. Neither this section, nor the `APD-CASCOR-005` row, nor
  > that row's §3 heading in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`
  > (*"in two of three copies"*) names it. The reason nobody saw it is structural and worth more
  > than the fix: **`juniper-ml/tests/test_service_fork_drift.py` cannot express canopy.** Its
  > `_FORK_REPOS` is `("juniper-data", "juniper-cascor")`, and
  > `test_every_guard_is_well_formed` asserts `site.repo in _FORK_REPOS` — so a canopy row is
  > rejected by the registry's own structural check. The gate that exists to catch copy drift is
  > **blind to a quarter of the copies**, and no count it produces can say so.
  >
  > Canopy diverges a **second** way, and this one is not cosmetic:
  > `src/security.py:53` is `set(api_keys) if api_keys else set()` — it has **no blank-key
  > filter**, where all three siblings carry
  > `{k for k in (api_keys or []) if isinstance(k, str) and k.strip()}`. That is the
  > `blank-api-key-filter` guard (`APD-DATA-003` / `APD-CASCOR-006`), ENFORCED in both forks the
  > gate does watch.
  >
  > **State the impact accurately — it is NOT the bypass the guard's own summary describes.**
  > Canopy's only caller is `get_api_key_auth()` (`src/security.py:262-267`), which does
  > `api_keys = [api_key] if api_key else None`; a truthiness test, so `""` becomes `None` and
  > auth is simply **disabled**, not enabled-and-accepting-empty. The residual case is a
  > whitespace-only key, reachable **only** through the env var — `get_secret` strips a secret
  > *file* but returns `os.environ.get(env_var)` raw (`src/secrets_util.py:62`, `:64`) — and it
  > fails **CLOSED** (auth enabled with a key no HTTP client can present), with
  > `enforce_auth_posture` (`src/main.py:341`) additionally failing the boot when
  > `require_auth` is set. So: a real divergence and a real blind spot in the gate,
  > **not** a live vulnerability. Do not let a future summary promote it to one.

### 0.4 Two open items that belong to no register row
Neither is in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` and neither is in §0.1–§0.3. They are
recorded here because the alternative is that they are recorded nowhere.

- **`equities_seq` has no `data_quality` consumer in the recurrence tier.** juniper-data#388
  made the producer refuse and annotate; nothing reads the annotation downstream —
  `grep -rn data_quality --include='*.py'` across
  `/home/pcalnon/Development/python/Juniper/juniper-recurrence` returns **zero hits**
  (re-checked 2026-09-15). A refusal nobody reads is a refusal that reaches no operator.
- **`val_ratio` was excluded from canopy's sidebar and the direction was never recorded.**
  `val_ratio` now sits in `INFRASTRUCTURE_FIELDS`
  (`juniper-canopy/src/dataset_schema.py:114`), so the three ratio fields are treated alike —
  but that was the non-obvious half of the choice: it makes the set consistent **and removes
  the only sidebar control over the in-loop selection split**. No canopy note or ledger row
  records it. §4.9's preamble in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` carries the same
  correction; an earlier draft of that preamble claimed the item "belongs to the canopy
  ledger", which named an intention as though it were a location.

### 0.5 juniper-ml

- **M-A · `APD-ML-001`**, state the pin-capping rule beside the pins
  (`juniper-ml/pyproject.toml:30-31`, `:34`, `:47-49`, `:52`, `:56` — the row in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` lists them) and in the docstring of
  `juniper-ml/tests/test_pyproject_extras.py`, which is the contract test that reads them. Ruled explicitly AGAINST changing the pins: capping consistently would make juniper-ml
  gate every sibling `0.y` release, and the `APD-ML-001` analysis in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` is that the
  pattern is coherent.
  The defect is the silence.

### 0.6 Owner decisions still owed — NONE, as of 2026-09-21

> **RULED 2026-09-21: `APD-DATA-047` is RATIFIED at `1e11`.** The owner was given the three
> options — ratify at `1e11`, remove the ceiling, ratify at some other value — together with the
> siting evidence below and the overlap argument that makes any absolute bound a compromise, and
> **ratified `_SHARES_ABSOLUTE_CEILING = 1.0e11` as sited by juniper-data#404**. The deciding
> consideration, stated back at the time of the ruling: it is the **only** instrument that
> reaches a typo in a series' *first* filing — `APD-DATA-050`'s EOG case, at position 0, which no
> relative test can see — so removing it re-opens that hole outright.
>
> **With this, no row in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` is
> awaiting an owner decision.** Every open row is now implementation work.
>
> The analysis below is left standing unedited: it is what the ruling was taken against, and a
> ratification whose evidence has been deleted is not reviewable.

Only one **was** owed: **`APD-DATA-047`**, whether the absolute share-count ceiling stays, and at what
value.
Everything else in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` is ruled.

**The subject moved on 2026-09-15 and the stakes rose.** The row was filed against `1e13`, a
number chosen for headroom above the largest genuine count. juniper-data#404 re-sited it to
**`1e11`**, between the largest genuine count in the cache (**Citigroup, 2.92e10**; NVIDIA second
at 2.45e10) and the smallest demonstrated typo in it (AIZ, 1.168e11) — **3.4× of headroom**. At
`1e13` the bound was nearly inert: 18 observations across 9 series sit in `(1e11, 1e13]`, and that
inertness is why a typo went out the door (§4).

**Two figures in the first draft of this section were wrong, and the owner would have been
ratifying against them.** It said the bound sits above "the largest genuine count in the bundled
universe (AAPL, 1.70e10)" with 5.9× of headroom — AAPL is the largest in the **default 14-symbol
prefix**, not the universe — and it said "18 observations across 24 series", conflating two
bands: 18 observations across 9 series in `(1e11, 1e13]`, 39 across 24 above `1e11`.

**And the decision is narrower than "is 1e11 right".** The four largest values that PASS this
ceiling are themselves typos — Pentair 9.84e10 (592× its own median), Packaging Corp 8.99e10
(949×), Regency Centers 8.19e10 (483×), Mid-America 7.50e10 (659×) — and the relative filter
catches every one, delivering all four correctly. So the ceiling cannot be tightened to reach
them without crossing Citigroup's genuine 2.92e10 and deleting real mega-cap history: **the two
populations overlap across any absolute bound.** The ceiling's job is not scale errors in
general but the one case nothing relative can reach — a typo in a series' *first* filing.
Removing it re-opens that hole outright. What #404 did was put the bound in ratifiable form,
sited against the data rather than against comfort. The decision is still owed.

---

## 1. Verify starting state

From the juniper-ml worktree root:

```bash
git fetch origin
grep -cE '^\| APD-[A-Za-z0-9-]+ *†? *\| \*\*FIXED' notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md
python3 util/ad-hoc/register_open_set.py
python3 util/ad-hoc/register_status_crosscheck.py
python3 -m unittest tests/test_register_status_crosscheck.py tests/test_register_open_set.py tests/test_register_close_protocol.py
python3 -m unittest tests/test_thread_handoff_archive.py
```

Expected: FIXED rows **94**; **`119 rows | 94 fixed | 25 open`**; cross-check **94 / 94 / 94,
AGREE**; 33 tests OK; the archive test passes.

That last line is **not decoration**. §4.9 of `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` cites this handoff by
filename, and `tests/test_thread_handoff_archive.py` requires every handoff a top-level note
cites to exist in `prompts/thread-handoff_automated-prompts/`. Until both land in the same PR
the test fails — which is why they are bundled.

In juniper-data, that the equities pair is at **5.0.0** and the corrected filter is in place.
**Absolute paths, not `-C ../../`** — a worktree-isolated session refuses a `git -C` whose
target is computed at runtime (§5.13):

```bash
git -C /home/pcalnon/Development/python/Juniper/juniper-data fetch origin
git -C /home/pcalnon/Development/python/Juniper/juniper-data show origin/main:juniper_data/generators/equities/generator.py | grep -E '^VERSION|_SHARES_ABSOLUTE_CEILING = |prior_values|expanding\('
```

Expected: `VERSION = "5.0.0"`, `_SHARES_ABSOLUTE_CEILING = 1.0e11`, and a `prior_values` loop —
**not** an `expanding()` one-liner. If you see `expanding(min_periods=3)` in *code* you are on a
commit before juniper-data#404 and the delivered share counts are wrong for at least two tickers
(§4). Note the word `expanding` legitimately appears in the **comment** that explains why the
expanding median was wrong, so match on the call, not the word.

> **CORRECTED 2026-09-21.** This block used to grep for `kept_values` and expect "the
> `kept_values` loop". **No such identifier exists** — the shipped loop uses `prior_values` and
> `keep` (`juniper_data/generators/equities/generator.py:1185-1197` on `origin/main`). The grep
> returned nothing while the code was entirely correct, which pushes a successor toward exactly
> the wrong conclusion: that they are on a pre-#404 commit. Re-verified 2026-09-21 — `VERSION`
> and `_SHARES_ABSOLUTE_CEILING` both match as stated.

---

## 2. What this session did

**Changed files, by name.**

juniper-ml: `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`; this document;
`util/ad-hoc/register_owner_rulings_2026-09-09.py`,
`util/ad-hoc/register_owner_rulings_primer_2026-09-11.py`, `util/ad-hoc/register_close_data395.py`,
`util/ad-hoc/register_file_047_to_049.py`, `util/ad-hoc/register_round39_head_typo.py`,
`util/ad-hoc/register_round39_park_sentences.py`,
`util/ad-hoc/register_file_data_052_truncation_optout.py`,
`util/ad-hoc/2026-09-11_equities_rulings/` (4 files).

juniper-data: `juniper_data/generators/equities/generator.py`,
`juniper_data/generators/equities/defaults.py`, `juniper_data/generators/equities/params.py`,
`juniper_data/generators/equities_seq/generator.py`,
`juniper_data/tests/unit/test_equities_generator.py`,
`juniper_data/tests/unit/test_val_emission_guards.py`, `CHANGELOG.md`,
`util/ad-hoc/2026-09-15_remeasure_shares_cache_figures.py`,
`util/ad-hoc/2026-09-15_equities_head_typo_fix.py`,
`util/ad-hoc/2026-09-15_equities_version_pin_bump.py`,
`util/ad-hoc/2026-09-15_equities_changelog_entry.py`,
`util/ad-hoc/2026-09-15_equities_fix_ceiling_rationale_numbers.py`,
`util/ad-hoc/2026-09-15_equities_fix_absorbing_basis.py`,
`util/ad-hoc/2026-09-15_equities_changelog_absorbing_basis.py`,
`util/ad-hoc/2026-09-15_compare_outlier_basis_designs.py`,
`util/ad-hoc/2026-09-15_verify_lower_median_over_cache.py`.

Ecosystem: `Juniper/AGENTS.md` (not a git repo — edited directly, no PR, no CI; §5.8).

Memory: `project_partial_data_contract_arc_2026-09-05.md`, `MEMORY.md`.

| PR | State | What |
|---|---|---|
| **juniper-ml#1864** | MERGED | The thirteen post-primer rulings; `APD-DATA-046` filed; `APD-CASCOR-011` closed WON'T FIX |
| **juniper-ml#1898** | MERGED | All sixteen parked PRIMER rows ruled, in a new §2.4; three rows corrected by re-derivation |
| **juniper-data#395** | MERGED `b6ab7c1` | The six equities data-quality rulings + `generator_version` 4.0.0 |
| **juniper-data#404** | MERGED 2026-09-16T02:08:43Z, squash `1bbb6976` | The regression #395 shipped: a first- or second-filing scale typo survived the causal median. `generator_version` 5.0.0. **Amended twice before merge, both times by validation** — see §4 and §5.2 |
| **juniper-ml#1947** | MERGED 2026-09-16T03:17:15Z | Eight closes, five new rows (`APD-DATA-047` … `-052`), and this document. *(Recorded 2026-09-21: this row read "juniper-ml (this PR) | — |" when the session ended. It carried `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`, this document, the three §7 lane reports under `reports/2026-09-15_round-39-consensus/`, and the ad-hoc scripts §2 lists.)* |

## 3. Owner rulings — thirty, and where they live

Taken interactively across two sessions. **The register is the record**, not this handoff:
§4.9's rulings block in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` for the
thirteen post-primer ones, and §2.4 of that same file for the sixteen primer ones. Each records the
option chosen AND the options rejected, so a later reader can tell a decision from a drift.

The thirtieth is the `equities` / `equities_seq` bump to `generator_version` **4.0.0**, ruled with
the published wheels in view. It is now **5.0.0**; that second bump was not a ruling but a
consequence — see §4.

---

## 4. Corrections to this session's own work

The first entry is the one that matters. The rest are smaller and were caught before shipping.

| Claim | Verdict | Correction |
|---|---|---|
| **This session's own fix, as first written, had a WORSE failure than the one it repaired** | **Refuted by round-2 validation, before merge** | Judging each point against the median of the values already ACCEPTED is **absorbing**: if a series' first value is a typo the ceiling cannot reach, the accepted set is that typo alone, every genuine value is >100× away, and nothing is ever accepted again — the whole real series is deleted and the typo is what ships. Measured on a real payload shape: **0 of 20 genuine counts survived**. The shipped basis is now the **lower median of prior SEEN values**; see §5.2. |
| juniper-data#395 fixed the share-count outlier filter | **It shipped a REGRESSION, and delivered it** | `pandas.Series.expanding().median()` at position *i* **includes** position *i*, so an outlier dominates the median that judges it and can never be rejected — and no `min_periods` value repairs that, because the problem is membership, not sample size. AIZ's typo sits at position 1 and EOG's at position 0; both were delivered, at 116,799,796,000 against a truth of 117,926,517 (990×) and 251,931,774,000 against 587,723,622 (428×). Found by round-1 lane B1, re-derived against the shipped module and the real cache, fixed in juniper-data#404 as `APD-DATA-050`. |
| The `adj_close` ruling "leaves it requestable" | **False when the option was put to the owner; and the row that recorded that was itself too broad** | `EquitiesParams` has no feature-column parameter, so the ruling as implemented removes it as a FEATURE column — filed as `APD-DATA-048`. But `adj_close` is not wholly unreachable: `EquitiesParams.basis_price_field` is a `Literal["close", "adj_close"]` and still selects it as the price the cost basis is struck at. `APD-DATA-048` in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` said "nothing can select it into a dataset"; corrected 2026-09-15. |
| Staleness is a per-row property | **Wrong, and caught by a fixture** | A per-row test flags the tail of every gap, and an annual filer produces a 365-day gap by definition. The ruling was taken on per-SERIES evidence. Implemented per series. |
| The staleness annotation names the issuer | **Wrong cause** | Ford, Nike, Hershey and Regeneron are all flagged over a window ending today and all four file a share count on every 10-Q. What stopped is this cache's extraction of the `dei` concept, not the company. The note now says *available*, not *filed*. juniper-data#404. |
| The causal median needs no other instrument | **Wrong** | It silently drops typo detection for early points. A ceiling was added — not ruled, filed as `APD-DATA-047`. #404 then had to re-site it from `1e13` to `1e11` because at `1e13` it was nearly inert. |
| `APD-DATA-030` "error bodies carry no retryability signal" | **Too broad** | `Retry-After` IS sent on the auth-throttle 429 (`api/middleware.py:206`), asserted by `tests/unit/test_middleware.py:240`. A second test, `tests/integration/test_security_integration.py:138`, asserts it on the **rate-limit** 429 (`api/security.py:287`) — a different mechanism, so the honest count is one test per source, not two on one. Corrected in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`. |
| `APD-CASCOR-005` "key comparison short-circuits" | **Narrower than written** | Every copy now uses `hmac.compare_digest`; only the `any(...)` ITERATION short-circuits, in two of three copies. |
| The comment figures could be renumbered 485 → 486 | **No** | The cache holds 486 payloads, but the numerators do not follow: re-measuring with the generator's own parsing gives 183 restatement CIKs where the comment says 162, and 42 collisions where it says 54. #404 renumbered nothing and filed `APD-DATA-051`. |

---

## 5. Traps

### 5.1 The `model_fields_set` presence guard does not work — measured twice
`EquitiesGenerator.bind_deployment_defaults` ends in `model_copy(update=...)`, which **adds** the
updated keys to `model_fields_set`, and the route binds before `generate`. Downstream of the binder
an omitted flag and an explicit `false` are indistinguishable, so a presence guard at any of the
three `or settings.*` sites is a constant-true guard. Round 38 "refuted" this and round-2 validation
reversed the refutation. It is why D-A (§0.1) is a tri-state and not a one-line guard.

### 5.2 An expanding statistic that includes its own point cannot reject that point
The regression in §4, stated as a rule, because it is not specific to medians. Any
`expanding()`/`rolling()` aggregate used as a *plausibility basis* must exclude the point being
judged, or a large enough outlier drags the basis to meet itself. `min_periods` looks like the knob
and is not — it changes how many points are required, never which ones are counted.

Two further traps sit behind it, and each cost a round:

- **Two plausible bases are wrong in OPPOSITE directions, and the cache cannot tell you.** This
  cost two rounds, so it is worth the space.
  - `.shift(1)` on the **seen** median excludes the point from its own basis but lets a
    *rejected* value into the basis for the next one: a genuine `1.0e8` then a `5.0e10` typo
    gives the third point `median(1e8, 5e10) = 2.55e10`, and the genuine third filing is deleted
    as a hundredfold-low outlier.
  - The obvious repair — judge against the median of what was **accepted** — is **absorbing**,
    and strictly worse. If a series' first value is a typo the ceiling cannot reach, the accepted
    set is that typo alone, every genuine value is >100× away from it, and **nothing is ever
    accepted again**; only an acceptance could widen the basis, so there is no way back. Measured
    on a real payload shape: **0 of 20** genuine counts survive. Both ingredients are in the
    cache — a position-0 typo is real (EOG) and four series carry sub-ceiling ~1000× typos (PNR
    9.84e10, PKG 8.99e10, REG 8.19e10, MAA 7.50e10) — only their coincidence is absent, and the
    cache TTL is 7 days. **This is what juniper-data#404 shipped in its first two commits**, and
    what round-2 lane B1 caught before merge.
  - What shipped is the **lower median of prior SEEN values**, `prior[(n-1)//2]`. *Prior* rather
    than prior-accepted kills the absorbing state, because a rejected value still counts towards
    the sample and the basis re-converges. The *lower* median rather than the interpolating one
    kills the first failure, because it is always a number some filing actually reported and
    cannot land between two disagreeing values.
  - **All three deliver identical multisets across the 483 in-bounds series of the real cache**,
    because the ceiling removes the poisoners before the relative test runs. The whole-cache
    check cannot separate them; only constructed shapes can
    (`juniper-data/util/ad-hoc/2026-09-15_compare_outlier_basis_designs.py`, and
    `2026-09-15_verify_lower_median_over_cache.py` for the equivalence). **A design that the
    corpus cannot distinguish from its alternatives is not thereby validated.**
- **A whole-cache sweep that compares MAXIMA cannot see over-deletion.** The first evaluation of the
  fix reported "2 series change, none emptied, 0 over-deletion" and was measuring
  `max(delivered)` per series. The `.shift(1)` variant deletes genuine interior points while leaving
  the maximum untouched. Compare the delivered **sets**, or at least the counts.

### 5.3 A new test that passes on the first run is not yet evidence
Five regressions were added for the equities rulings and all five passed immediately. Re-run against
the UNMODIFIED source before believing them: one of the five passed there too, making it vacuous,
and was rebuilt with a fixture where the two implementations genuinely disagree. The cheap method:
copy the changed source aside, `git checkout --` it, run the new tests, restore. juniper-data#404's
three new tests were each verified to FAIL against the pre-fix generator before the PR was opened,
and two further tests were added that pass under BOTH — those are the over-correction guards, and
they are supposed to pass under both.

### 5.4 Dates that do not exist coerce to NaT and sort FIRST
A fixture generated filings on the 29th of every month; February 2010 has none, so
`pd.to_datetime(..., errors="coerce")` produced NaT, `na_position="first"` put that fact at the head
of the causal ordering as always-known, and a test failed for a reason unrelated to what it tested.

### 5.5 `pre-commit` — the PATH breakage is FIXED; use the repo's environment anyway
An earlier draft of this document carried a trap saying `pre-commit` on PATH has a dead interpreter
(`/opt/miniforge3/envs/JuniperCascor1/bin/pre-commit`, `bad interpreter: .../python3.13`). **That is
stale**: the environment was repaired 2026-09-12 and `pre-commit 4.6.0` runs. Round-1 validation
caught it. Still prefer each repo's own interpreter
(`/opt/miniforge3/envs/JuniperData/bin/pre-commit` for juniper-data) so the hooks resolve the
dependencies the repo pins.

What is **not** stale in that trap: **ruff format modifies files in the worktree**. Re-run the hooks
AND the tests after it does, or you push unformatted code and test a tree you did not measure.

### 5.6 How a PR is opened here — a local `git push` cannot land a mergeable commit
**Read this before writing any code.** All nine Juniper repos have `required_signatures`.
Local signing hangs (the key needs a hardware touch), and an unsigned commit ANYWHERE in a
branch's history blocks the merge — squash does not rescue it. Commits therefore go through
GitHub's API, and only GraphQL `createCommitOnBranch` signs; `PUT /contents` does not.

- **Open a PR**: `python3 util/open_signed_pr.py --repo <repo> --branch <branch> --add
  LOCAL_PATH:REPO_PATH --message <commit msg> --title <title> --body-file <path>`. `--add` is
  repeatable; exit 0 = opened, 1 = refused (a duplicate PR or an existing branch), 2 = hard
  error. `--dry-run` resolves and prints the plan without writing.
- **Add a follow-up commit** to a branch that already exists:
  `python3 util/ad-hoc/2026-08-26_push_signed_fixup.py --repo <repo> --branch <branch> --add
  … --message …`. It pins `expectedHeadOid` so a concurrent write fails loudly.
- **Both tools send WHOLE FILES.** Re-check `git log HEAD..origin/main -- <path>` immediately
  before every push, or you silently revert someone else's merged change.
- **Verify a merge in two steps**: `gh pr view <N> --json state,mergedAt,mergeCommit` **and**
  that the content is on `main`. A MERGED badge is not ancestry, and `util/safe_merge.py`
  prints the *head* SHA, not the squash commit.
- **Merge approval**: headless merges are gated on the owner's explicit approval, per memory
  `feedback_headless_merge_approval_policy`; deploys are the owner's, per
  `feedback_deploy_approvals_paul_manages`. A session-wide grant covers only the PRs of the
  arc it was given for.

### 5.7 The GraphQL rate limit blocks PR creation while REST keeps working
`gh pr list` and `util/open_signed_pr.py` both use GraphQL and fail with *"API rate limit already
exceeded"* while `gh api` REST calls succeed and `gh api rate_limit` reports 5000 remaining. The
reset is up to an hour. Local implementation is unaffected — do the work, open the PR after.

### 5.8 `open_signed_pr.py` can create the BRANCH and fail the COMMIT
Distinct from §5.6 and new this session. A large payload (nine files, ~330 KB) returned `HTTP 499`
on the `createCommitOnBranch` mutation **after** the branch ref had been created. The branch then
exists at the base SHA with no commit, and re-running `open_signed_pr.py` refuses — correctly, its
dup-guard sees the branch. The recovery is `util/ad-hoc/2026-08-26_push_signed_fixup.py` (which
targets an existing branch) followed by `gh pr create`. Check `git ls-remote --heads` before
concluding anything failed cleanly.

### 5.9 The ecosystem data contract is edited without CI
`Juniper/AGENTS.md` is in the ecosystem parent, which is **not a git repository**: no PR, no CI, no
history, and invisible to any other machine. The `generator_version` statement there was updated
by hand for the 4.0.0 bump, went stale the moment juniper-data#404 merged, and was updated again
to 5.0.0 on 2026-09-16 by `util/ad-hoc/2026-09-15_ecosystem_agents_md_generator_version_5.py` —
which exists as a script rather than a hand edit precisely because that file has no history, so
the script is the only record that the change was made and against which merge. Round-2 lane A
caught that an earlier draft called it stale *prematurely*: while #404 was open, `4.0.0` was
correct. Nothing enforces this statement, so check it whenever a generator version moves.

### 5.10 Decision 11 set a floor, not a fixed point
`juniper-data/juniper_data/tests/unit/test_val_emission_guards.py` asserted every generator equals
`3.0.0`. That was right while all sixteen sat there and became wrong the moment one legitimately
moved. It now asserts major ≥ 3 plus an explicit allow-list naming the equities pair — which #404
had to update again, to `5.0.0`. The allow-list is the point: a generator that moves on its own
still has to record why.

### 5.11 A value-changing fix without a `generator_version` bump serves the old numbers
`generator_version` is hashed into `dataset_id`. #404 corrected values that #395 had delivered
wrongly; without the bump to `5.0.0` the corrected artifact would resolve to the same id as the
wrong one and the cache would keep serving the wrong one. Every artifact minted at `4.0.0` for a
symbol with such a typo carries it.

### 5.12 A comment's numerator does not follow its denominator
Several comments in `juniper_data/generators/equities/generator.py` quote counts from a
485-payload sweep against a cache that now holds 486. Bumping the denominator alone leaves every
numerator asserting a measurement nobody redid — and re-measuring with the generator's own parsing
does **not** reproduce them (183 restatement CIKs where the comment says 162; 42 value-changing
period-end collisions where it says 54), so the predicates themselves differ. #404 deliberately
renumbered nothing and filed `APD-DATA-051`.
`juniper-data/util/ad-hoc/2026-09-15_remeasure_shares_cache_figures.py` is the instrument.

### 5.13 The sandbox refuses shell STRUCTURE, and it is mode-dependent
Loops, `&&` with a heredoc, `${PIPESTATUS}`, unquoted variables in an option position, a
`git -C` whose target is computed at runtime, and any command computing a `git` / `gh`
argument at runtime are all refused in a worktree-isolated session — which is why §1's
juniper-data commands use absolute paths. Put every multi-line edit in a scratch script under
`util/ad-hoc/` and run it by absolute path. That is also the ecosystem rule
(`Juniper/AGENTS.md` § Cross-Project Conventions: `/tmp/` is prohibited as the home of any
script that produces, modifies or analyses repository content), so the workaround and the
convention agree.

### 5.14 The register crosscheck catches two things a close silently misses
`util/ad-hoc/register_status_crosscheck.py` caught both of this arc's protocol slips: a
WON'T FIX close with no §5.1 verification row, and a status line naming ids in ABBREVIATED
form (`-040`), which its `APD-[A-Z]+-\d+` regex does not match. It also treats **every id on
the status line as claimed-fixed**, so an open row mentioned there fails the check. Run it
after every close — the four other touches of the five-touch protocol will not reveal any of
these.

### 5.15 Environments
juniper-data → `/opt/miniforge3/envs/JuniperData/bin/python`; juniper-cascor →
`.../JuniperCascor1/bin/python` (trailing `1`); juniper-canopy → `conda run -n JuniperCanopy1`;
juniper-recurrence has **no** environment — borrow one and set
`PYTHONPATH=juniper-recurrence-model`, or a stale installed copy shadows the worktree (in a
borrowed env `test_crossval.py` does not collect and one torch test skips, both pre-existing).
All three repos carry `-q` in `addopts`, so use `-v … | grep ' passed'` and
`-p no:cacheprovider`. **canopy needs `conda run -n JuniperCanopy1`, not the env's python
directly**: invoked directly it skips the hook that strips the Rust `libtorch` path, and
anything importing torch then dies on `libtorch_python.so: undefined symbol`. Unit tests that
never import torch pass either way, which is how a partial run reads healthy.

---

## 6. Git status

juniper-ml worktree `pure-toasting-token`, branch `worktree-pure-toasting-token`, with
`origin/main` far ahead (this worktree is at `44de51c5`; `origin/main` is well past it) —
`notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` is refreshed from `origin/main` before every edit, so diff
against `origin/main`, never `HEAD`. **Primary checkouts drift**: a lane that reads "main
today" out of a checkout reads whatever that checkout last fetched. Read
`git show origin/main:<path>`.

Worktrees created this arc and **deliberately not removed** (cleanup needs the owner's explicit
signal, and `git worktree remove` deletes ignored files): the three round-38 PR worktrees, plus
`juniper-cascor--fix--mirror-shortfall-constants-all--20260909-1600--3de89b11`,
`juniper-cascor--fix--partial-data-follow-ups--20260909-1536--3de89b11`,
`juniper-data--fix--equities-causal-data-quality--20260911-2310--20cd6788`, and
`juniper-data--fix--equities-head-typo-regression--20260915-2130--f3797634`.

**A local side effect worth knowing:** the SEC payloads were copied to
`~/.cache/juniper_data/equities/shares/v2/` by hand so the new versioned key would find them. That
is a local convenience on ONE machine, not the migration — `APD-DATA-049` is the migration. The
cache holds **486** payloads, not the 485 several comments still say (§5.11).

---

## 7. Validation of this document

Procedure: `notes/JUNIPER_2026-08-30_JUNIPER-ECOSYSTEM_INDEPENDENT-AGENT-CONSENSUS-PROCEDURE.md`.

**Round 1:** three lanes, launched together — receipts-and-source (A), refutation (B1), and
amputation/executability/naming (B2). It did not pass, and the failure was load-bearing rather than
cosmetic:

- **Lane B1 found a shipped regression**, not a documentation defect: juniper-data#395's causal
  median could not reject an outlier in a series' opening filings, and two real tickers were being
  delivered 990× and 428× too large. That is §4's first row and juniper-data#404.
- **Lane B1 also found that §0's D-A sequenced a defect with no register row.** Filed as
  `APD-DATA-052`; the register's §4.9 preamble had named the gap and nothing had closed it.
- **Lanes A and B2 found this document's §5.5 trap was stale** — the `pre-commit` interpreter was
  repaired 2026-09-12.
- Further corrections applied from round 1: C-A generalised one client's transport to all three
  (§0.2); D-F was described as parallelisable with the route work when it collides with D-B in
  `storage/base.py` (§0.1); the register counts, the `equities` version in §1's verification block,
  and §2's changed-file list were all stale.

**Round 2** validated this revision, and did not pass either:

- **Lane B1 (refutation) found that the fix itself had a worse failure than the defect it
  repaired** — the absorbing basis, §5.2 — and it was corrected and re-pinned before
  juniper-data#404 merged. Twice in two rounds the load-bearing finding came from *running* the
  code against real data, not from reading it.
- **Lane A (receipts) found two wrong numbers in the ceiling's siting**, both of which had
  reached the shipped code comment, the CHANGELOG and the register row the owner is being asked
  to ratify (§0.6).
- **Lane B2 (amputation / executability / naming) found ten traps dropped from the predecessor**,
  including the byte-mirror obligation that X-A will hit (§0.3), and that this document never
  said how a PR is opened in a fleet where a local `git push` cannot land a mergeable commit
  (§5.6).
- Both rounds also found the register carrying claims it could not support — an item said to
  "belong to the canopy ledger" that no ledger row records, and a ruling that generalised one
  client's transport to three. Both corrected in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md`.

Record for both rounds: `reports/2026-09-15_round-39-consensus/`.

**What the evidence cannot support:** whether the remaining ruled rows are implementable as
sequenced without collisions beyond those named in §0.1 (the sequencing is reasoned from file paths
and one grep, not from attempting it); anything about SEC's live endpoint; the per-PR effort implied
by §0, which is not estimated anywhere; and the predicates behind the comment numerators in §5.11,
which were not recovered.

---

## 8. Session-close checklist

- [x] Thirty owner rulings taken and recorded in `notes/JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md` (§3)
- [x] juniper-data#395 — six equities rulings + `generator_version` 4.0.0 — MERGED
- [x] juniper-data#404 — the regression #395 shipped — `generator_version` 5.0.0 — MERGED
      2026-09-16, squash `1bbb6976`, verified by content on `main` and not by the badge (§4)
- [x] `Juniper/AGENTS.md` moved to `5.0.0` after that merge (§5.9)
- [x] Eight register rows closed; five new rows filed (`APD-DATA-047` … `APD-DATA-052`)
- [x] Ecosystem data-contract note updated for the 4.0.0 bump — **and again for 5.0.0 on
      2026-09-16** by `util/ad-hoc/2026-09-15_ecosystem_agents_md_generator_version_5.py` (§5.9).
      *(Corrected 2026-09-21: this line read "and stale again at 5.0.0 (§5.8)". It contradicted
      §5.9 of this same document, and `Juniper/AGENTS.md` now reads `5.0.0`. The cross-reference
      was wrong too — §5.8 is the `open_signed_pr.py` branch-without-commit trap.)*
- [ ] D-A … D-G, C-A … C-C, X-A, X-B, M-A (§0) — **still outstanding, re-verified 2026-09-21**
- [x] **X-C** (`APD-CASCOR-005`) — implemented 2026-09-21, PRs open, not yet merged; §9
- [x] `APD-DATA-047` — **RATIFIED at `1e11` by the owner, 2026-09-21** (§0.6). No owner decision
      is owed anywhere in the register now.
- [x] This document validated — two rounds, three lanes each, both recorded in §7; neither
      passed on the first pass and both changed shipped code

---

## 9. Revalidation session, 2026-09-21 — X-C implemented

Appended by the session that ran the REVALIDATED banner at the top. **§0–§8 above are that
banner's subject; this section is new work.**

### 9.1 What was verified, and with what

§1's block was run unaltered and **every expectation held**: FIXED rows `94`;
`119 rows | 94 fixed | 25 open`; crosscheck `94 / 94 / 94, AGREE`; 33 tests OK; the archive test
OK. The open-id set was compared element-by-element against the set §0 sequences and is
**identical** — 17 `APD-DATA`, 3 `APD-CASCOR`, 3 `APD-ECO`, 1 `APD-ML`, 1 `APD-RCLIENT`.

Nine repos were swept for merged PRs since `2026-09-15T00:00:00Z` and for open PRs. **None
implements any §0 item.** juniper-data merged #399, #400, #402, #403, #404; juniper-cascor #652,
#653, #654, #658; juniper-ml #1936-#1969; data-client #203-#205; cascor-client #166, #167;
recurrence #171, #172. The one PR that touches this arc at all is **juniper-ml#1947**, which is
§2's own last row landing (see §2).

Also re-checked, both **unchanged**: §0.4's recurrence item (`grep -rn data_quality
--include='*.py'` over `/home/pcalnon/Development/python/Juniper/juniper-recurrence` still
returns **0**), and §0.4's canopy item (`val_ratio` is still in `INFRASTRUCTURE_FIELDS`, at
`juniper-canopy/src/dataset_schema.py:115` — §0.4 says `:114`, off by one, and the claim itself
stands).

### 9.2 X-C — implemented, not merged

`APD-CASCOR-005`. juniper-data's `matched`-flag loop ported into both copies the ruling names.
Applied by `util/ad-hoc/2026-09-21_port_nonshortcircuit_key_compare.py`, which matches the old
`validate()` body **verbatim** and REFUSES rather than pattern-patching a near-miss — it reports
juniper-data as `ALREADY-PORTED`, which is the cheapest available proof that the instrument
distinguishes the two states.

**Changed, by filename:**

- `juniper-ml/juniper-service-core/juniper_service_core/security.py` — the loop
- `juniper-ml/juniper-service-core/CHANGELOG.md` — `[Unreleased] / Fixed`
- `juniper-ml/tests/test_service_fork_drift.py` — new `nonshortcircuit-key-compare` guard
- `juniper-ml/util/ad-hoc/2026-09-21_port_nonshortcircuit_key_compare.py` — the instrument
- `juniper-cascor/src/api/security.py` — the loop (worktree
  `juniper-cascor--fix--nonshortcircuit-key-compare--20260921-0846--c6c848f2`, branch
  `fix/nonshortcircuit-key-compare`)
- this document

**`src/api/security.py` is NOT byte-mirrored.** X-A's mirror trap does not apply here:
`juniper-cascor-model/tests/test_drift.py` covers `_EXTRACTED_DIRS = ("candidate_unit", "utils",
"log_config", "cascor_constants")`, and a `find` for `security.py` under `juniper-cascor-model/`
returns nothing. Verified rather than assumed.

### 9.3 Two things about X-C that a successor must not re-derive the hard way

**No behavioural test can pin this, and one written to try would be vacuous.** `any(...)` and
the flag loop return the same value for every input. That is not a gap in the testing — it is
the reason the guard is a **source marker** in `juniper-ml/tests/test_service_fork_drift.py`.
§5.3's trap ("a new test that passes on the first run is not yet evidence") has a sharper form
here: a behavioural test would pass against **both** implementations, for ever.

**The guard was verified to be non-vacuous before it was committed**, which is the check §5.3
actually asks for. Run against the local siblings it FAILS on juniper-cascor (absent markers
`['matched = False', 'return matched']`) and PASSES on juniper-data:

```bash
JUNIPER_DRIFT_TEST_FORCE_LOCAL=1 python3 -m unittest tests/test_service_fork_drift.py
```

**That failure is also the merge-order constraint.** The guard is `status=ENFORCED` with a
juniper-cascor site, so **juniper-cascor's PR must merge before juniper-ml's**, or the weekly
`docs-full-check` cross-repo job goes red. Locally the cross-repo assertions skip unless
`JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` is set, so the ordering will not fail a normal PR run — it
fails the weekly job, quietly, later.

### 9.4 Test results, stated as what they do and do not show

| Suite | Result | What it shows |
|---|---|---|
| `juniper-service-core/tests/` (full, run from `juniper-service-core/`) | all pass | No regression. **Not** evidence of the fix — see §9.3. |
| `juniper-cascor src/tests/unit/api/test_api_security.py` | 48 passed | Same. |
| `tests/test_service_fork_drift.py` structural | 8 tests, OK (3 cross-repo skipped) | The registry row is well-formed. |
| `tests/test_service_fork_drift.py` with `JUNIPER_DRIFT_TEST_FORCE_LOCAL=1` | **1 failure, on juniper-cascor** | The marker is non-vacuous. This is the intended result pre-merge. |
| `tests/test_register_*.py`, `tests/test_thread_handoff_archive.py` | 35 tests, OK | The register edits did not break the protocol checks. |

**A pre-existing failure a successor will hit and should not chase.**
`juniper-service-core/tests/test_smoke.py::test_top_level_import_does_not_require_fastapi_or_pydantic_settings`
fails when the suite is run **from the repo root**, and it fails identically against the
unmodified source (checked by §5.3's copy-aside-and-revert method). Cause: the test spawns
`sys.executable`, `python3` resolves to `JuniperCascor1`, and that environment has
`juniper_service_core` **0.4.0** installed in site-packages, which shadows the 0.7.0 worktree
source. **Run the suite from `juniper-service-core/`** and it passes. Environment state, not
repo content — `reference_a_checkout_is_not_a_deployment` again.

### 9.5 Git status

juniper-ml worktree `eager-seeking-milner`
(`juniper-ml/.claude/worktrees/eager-seeking-milner`), branch `main`, which was one commit
behind `origin/main` at session start (`52571621` vs `d721fc78`). **§6's git status is
superseded** — it describes `pure-toasting-token` at `44de51c5`. The register and this document
were both byte-identical to `origin/main` before editing, checked with
`git diff --stat origin/main -- <path>`; §6's standing instruction to diff against `origin/main`
rather than `HEAD` still applies and is why that check was run.

New worktree created and **not** removed (cleanup needs the owner's explicit signal, and
`git worktree remove` deletes ignored files):
`juniper-cascor--fix--nonshortcircuit-key-compare--20260921-0846--c6c848f2`.

### 9.6 `APD-DATA-047` closed as RATIFIED — the register's last owner decision

Applied by `util/ad-hoc/2026-09-21_register_close_data047_ratified.py`, which asserts each anchor
appears **exactly once** and refuses rather than patching a near-miss.

**Four touches, not five** — the protocol ("Closing a row — the five touches") is explicit that a
row with no §3 detail entry takes four, and `APD-DATA-047` has none. §4 table row, §5.1
verification row, §2 status paragraph (the enumeration *and* both counts), header date. A fifth
edit was made that is **not** a touch: §4.9's rulings bullet still read "owner decision owed", and
the protocol's whole-file `grep -n 'APD-<ID>'` sweep requires every hit be read and reconciled.

**Result, and it is the check that matters** (§5.14 — the crosscheck is what catches a partial
close, and the other four touches will not reveal one):

```
119 rows | 95 fixed | 24 open        §4 tables: 119 rows, 95 marked **FIXED
                                     §2 prose list: 95 ids enumerated
                                     §5.1 verified: 95 verification rows      AGREE
```

43 tests OK across `tests/test_register_status_crosscheck.py`,
`tests/test_register_open_set.py`, `tests/test_register_close_protocol.py`,
`tests/test_thread_handoff_archive.py` and `tests/test_service_fork_drift.py`.

**What the close does and does not assert.** It records that a number nobody had chosen now has
an owner. It does **not** assert `1e11` is optimal — the owner was shown that the two populations
overlap across any absolute bound, so this is a judgement, not a calculation — and it does not
extend past the 486-payload cache the bound was sited against. A future symbol with a genuine
count above `1e11`, or a typo below it, reopens the question. Both rejected options and the
reasoning are recorded at the row and in its §5.1 row, per §3's standing requirement that a
reader be able to tell a decision from a drift.

**`APD-CASCOR-005` is deliberately NOT closed**, although §9.2 implements it. "Status is verified,
not inherited" — the fix is on two branches, merged nowhere. It closes when both PRs are on
`main` and the content is verified there, not when the badge says MERGED (§5.6).
