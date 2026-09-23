# Round 2, lane S3 (executability) -- final report, verbatim

**Verdict: EXECUTABLE WITH GAPS.** I found 0 blockers, 5 majors, 6 minors and 1 nit. Round 1's findings hold as fixed. The new gaps are in release mechanics, in the premise W11 rests on, and in the consumer surfaces.

I reviewed `JUNIPER_2026-09-22_JUNIPER-ECOSYSTEM_PARTITION-PROVENANCE-SPEC.md` at 8c9d65f. W0–W12 are that file's §11.3 work items. I re-ran `2026-09-23_partition_provenance_v2_reference_gate.py` against the pinned juniper-data worktree (JuniperData env, bytecode writes off, temp files in scratch). It gave **52 PASS, 0 FAIL, 0 SKIP**, which matches the spec's §10.2.

**Per item** (can I start it / is the order right / what breaks elsewhere / is the size right)
- **W0**: already merged (the pin 90ad035e is #430's merge), but the table doesn't mark it Done. W1 and W2 are done.
- **W3**: the owner can rule, but two alternative answers have no plan (F10). There is no §16 line for whether canopy enforces legality or only advises (F5).
- **W4**: fine as a merge, but recurrence must also publish a release (F1). S.
- **W5**: can ship before W6. The golden vectors and id re-derivation stand alone. The fake depends on uuid ids in more places than the spec says (F6). M.
- **W6**: status `verified` is reachable while `FIRST_EMITTING_VERSION` is empty, because the table is read only when the block is absent. But CI does not use the published gate (F2), and the interfaces are loose (F8). About 15 test files churn. L is plausible.
- **W7**: the status field is unnamed (F5), and about 20 tests break (F7). M.
- **W8/W9**: no setting and no status surface (F5). S only if none is added.
- **W10**: breaks `pip install juniper-ml[all]` (F1). Not S.
- **W11**: needs something W6 never produces (F3); it is not really a PATCH (F4); nothing makes consumers adopt 0.6.1 (F9).
- **W12**: no evidence field is named. `run_experiment.py` imports only the stdlib, so a client import is new. S.

**Hand-written fakes refused after W11: none.**
- cascor serves `test-id`, `ds-42` and `fake-id-001`.
- canopy's only realistic-looking id is `equities-3.0.0-abc` (`test_dataset_shortfall_prompt.py:223`, `test_service_backend.py:535`). It is not 16 hex and is a display fixture.
- recurrence serves `created-1`, `latest-of-…` and `bench`.
- juniper-ml has matching ids only in notes/, reports/ and util/ad-hoc/, all at old versions.
- The package fake stamps version `1.0.0` (`constants.py:311`), below every first-emitting version.

**§11.2 numbers are all correct at the pins**: client 0.5.0; canopy cap `<0.6.0` (`:192`, in an extra); recurrence cap `<0.6.0` (`:54`, a **core** dependency); cascor `>=0.3.0` (`:118`); juniper-ml `:67` and `:86`; juniper-data's test extra `:123`.

**Findings**

**F1 MAJOR (W10, W4): W10 makes `juniper-ml[all]` unresolvable.**
- W10 sets `[clients]` to `juniper-data-client>=0.6.0`, while `[recurrence]` keeps `juniper-recurrence>=0.5.0,<0.6.0` (`pyproject.toml:105`).
- PyPI's newest juniper-recurrence is 0.5.0, whose core dependency is `juniper-data-client<0.6.0,>=0.4.2` (I queried PyPI).
- W4 only merges the widened cap. If W9 then ships recurrence as 0.6.0, the meta-package cap excludes it.
- `publish.yml:195,202` checks only `[clients]` and `[tools]`, so a broken `[all]` would be published.
- *Fix*: W4 publishes a recurrence 0.5.x with the widened cap, or W10 widens `[recurrence]`. Make W10 depend on that release, and add an `[all]` dry-run resolve.

**F2 MAJOR (W6): CI does not run the "published" gate.** The spec's §11.1, OQ-6 and §13 item 5 rest on juniper-data's CI running the published client gate. At the pin, juniper-data's CI installs `juniper-data-client @ git+…@main` before `.[all]` (`ci.yml:273,434,494,601,905`). A gate fix merged but not released would pass the producer while consumers still refuse.
- *Fix*: a W6 CI job that installs `juniper-data-client==<published version>` from PyPI, with no git override.

**F3 MAJOR (W11, W6): W11's premise is asserted, not produced.** The premise is "a genuine artifact at or above its generator's first emitting version always carries a block" (spec §11.2).
- W11 has no condition on OQ-1. If the owner says "no bump", the versions shipped are 3.0.0/4.0.0/5.0.0, which every legacy artifact carries. W11 would then refuse every legacy artifact, and the spec's §9.4 makes that refusal non-overridable.
- The fleet test's scope is unstated: through the real route, or through a test helper? The HF and Kaggle stores are not registered generators, yet W11 fills their versions too.
- W6 spans several PRs, and nothing requires a generator's VERSION bump to land with or after its block emission. juniper-deploy builds `../juniper-data` from source onto the named volume `juniper-data-datasets` (`docker-compose.yml:155-164,200`). An intermediate `main` can therefore mint block-less artifacts at the new version, and W11 refuses them permanently.
- *Fix*:
  - Condition W11 on OQ-1 = yes, and assert each filled version is above every version released before 0.16.0.
  - Bump each generator's VERSION in the same PR as its emission, on every write path.
  - Test through a real POST→GET and through the store loaders with downloads mocked.
  - Have W6 output a generator → version → `verified` list as W11's input.

**F4 MAJOR (§11.2, W11): the PATCH claim conflicts with the cited owner rule.** The spec says 0.6.1 is a PATCH and "the `<0.7.0` caps admit it". The owner rule (juniper-cascor-client#155) is: set the version from the change, never from a consumer cap. W11 changes an exported constant and turns a tolerated `absent` into a non-overridable exception. That is a behaviour change, so MINOR before 1.0, and a consumer pinned `~=0.6.0` would get a new refusal in a patch.
- *Fix*: drop the caps clause. Either release 0.7.0 after widening the caps to `<0.8.0`, or ask the owner to rule on it in §16.

**F5 MAJOR (W7, W8, W9, W12): the status and override surfaces are unnamed.** Two of the spec's MUSTs have nowhere concrete to live: record the status beside the run (§9.4), and a per-consumer setting plus a caveat on the reported metrics (§8.3).
- The caveat the spec tells W7 to copy is **never read**. `_validation_warning` is written at `manager.py:4261` and read nowhere in cascor's `src/` at f7a6d573. Copying it literally produces a caveat nobody sees.
- W7 places the status "beside" existing `get_status()` fields but names no field or shape. The `dataset_shortfall` precedent appears on both `get_status()` (`:2846`) and `get_metrics()` (`:2941`).
- Auto-start and the CLI (`data_provider.py:193`) get nothing.
- W8 and W9 name no setting and no surface. For recurrence, the obvious home is the `descriptor` dict (`data.py:82`).
- W12 names no evidence field.
- *Fix*: for each consumer and both OQ-2 answers, name the status field and its shape, the setting (name, env var, default) and a caveat slot that something actually reads. Add a canopy line to §16.

**F6 MINOR (W5): the fake depends on uuid ids beyond `:417`.**
- Repeated identical seeded creates now share one id and overwrite each other at `:471`. Name, tags and `dataset_version` are lost, `list_versions` and `batch_create` diverge, and one delete removes both. The real service returns the cached record, and the fake should too.
- The fake's own tests assert a UUID length of 36 (`test_fake_client.py:189-194`) and exact key sets (`:334,371,430,550,570,578,586`; `test_fake_client_batch.py:296`).
- The caller's params must now be JSON-serialisable.
- The spec doesn't say which legality facts or version the fake declares.

**F7 MINOR (W7): wiring the gate into cascor breaks about 20 tests.** cascor treats the client as optional (`manager.py:4147-4150`). `TestReloadDataset` injects a stub module exposing only `JuniperDataClient` (`test_lifecycle_manager_swap.py:150-167`, used through `:373`), and `test_api_app_coverage_deep.py:208` injects a mock module. Importing the gate breaks those tests. The local JuniperCascor1 env still has client 0.5.0, so a cascor that imports the gate would report the client as "not installed". "No-ops until blocks exist" is true only at runtime.
- *Fix*: import the gate separately and give "client older than 0.6.0" its own error.

**F8 MINOR (W6): the nonce and store-id interfaces are loose.**
- A nonce passed alongside a seed must raise. If it is ignored, every seeded block records a nonce its id never used and fails the id check.
- Seeded ids are otherwise safe: no juniper-data test pins a hash value or patches `uuid`.
- The new return type of `external_dataset_id` is unstated. Changing it breaks the reference gate at `…v2_reference_gate.py:722`.
- The #430 fleet test pops the reserved channels by name (`test_artifacts_load_without_pickle.py:44-48`). The new channel must be added there, or all 16 generators fail.
- Test assertions to update: `test_api_routes.py:752`, and the version pins in `test_hf_store.py:162` and `test_kaggle_store.py:190`.

**F9 MINOR (W7–W9, W11): locks and adoption of 0.6.1.**
- Raising floors to `>=0.6.0` conflicts with `==0.5.0` lock pins, which must be regenerated in the same PR:
  - cascor: `requirements.lock:57`, `requirements-cpu.lock:120`, `conf/requirements_ci.txt:90`;
  - canopy: `requirements.lock:75`, and canopy's CI fails a lock that no longer satisfies pyproject (`ci.yml:651-706`);
  - recurrence: `requirements.lock:63`.
- No work item moves any consumer or `[clients]` to 0.6.1, so W11's refusal never reaches a deployment.
- *Fix*: add floor `>=0.6.1` and a lock refresh to W11.

**F10 MINOR (W3): two answers the owner can give have no plan.** OQ-6's report-only answer has no mechanism and no release that removes it. Under OQ-2 "warn only", the spec doesn't say what happens to `allow_illegal` in the §9.2 signature.

**F11 MINOR: omissions.**
- juniper-ml's `pyproject.toml:61-63` requires AGENTS.md, README.md, docs/QUICK_START.md and docs/REFERENCE.md to change with any pin, enforced by `tests/test_pyproject_extras.py`.
- The Data Contract text goes stale: `Juniper/AGENTS.md:156` ("six, not eight") and `:213`, plus juniper-data's `docs/api/JUNIPER_DATA_API.md`.
- No CHANGELOGs, release notes or version-string updates are listed. The client carries its version in both `pyproject.toml` and `__init__.__version__`.
- No juniper-deploy image-tag bumps (`docker-compose.yml:164,227,592`).
- No operator note covering the cache-miss cost, pinned ids, the new cascor env var, or how to recover from a stripped-block refusal.

**F12 NIT.**
- W0 is not marked Done.
- `juniper_data/provenance.py` already exists (build SHA and date), and W6 adds a second module named `provenance` meaning something else.
- `ProvenanceReport`, `JuniperDataProvenanceError` and a status Literal are missing from §9.2's export list.
- The §6 fingerprint depends on key names given only in the scripts.

**Changed**: none. This was a read-only review. My only files are scratch copies (`spec.md`, `ref_gate.py`) under `scratchpad/specS3/`.
