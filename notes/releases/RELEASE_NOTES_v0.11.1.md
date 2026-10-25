# Juniper ML v0.11.1 – :lock: SECURITY PATCH RELEASE

**Release Date:** 2026-10-25
**Release Type:** Security Patch
**Priority:** [PRIORITY_LEVEL]
**Package Affected:** juniper-ml

---

This is a security-bearing release of `juniper-ml` v0.11.1. It carries a `Security` Keep-a-Changelog category and was drafted by the release-train from the security template; complete the advisory details (CWE, advisory URL, affected versions) before the ceremony.

---

## Security Impact ([SEVERITY])

| Attribute | Value |
| --------- | ----- |
| **Package** | `juniper-ml` |
| **Fixed in** | 0.11.1 |
| **Vulnerability class** | [VULNERABILITY_CLASS] ([CWE_ID]) |
| **Advisory** | [DEPENDABOT_ALERT_URL] |

---

## Changes in v0.11.1

### Security

- **`[tools]` floors the two shared security patches**: `juniper-observability>=0.4.1`
  (`configure_sentry` stops sending frame-local variables, which could hold the real API key, to
  Sentry) and `juniper-service-core>=0.7.1,<0.8.0` (a non-ASCII `X-API-Key` is a 401, not a 500;
  `FailedAuthThrottle.check()` is bounded). The extras tables in `README.md` (both),
  `AGENTS.md`, `docs/QUICK_START.md` and `docs/REFERENCE.md` move with them, as do
  `docs/REFERENCE.md`'s two package rows (whose **Current Version** still read 0.4.0 / 0.7.0) and
  both sub-package READMEs' pin advice. `[servers]` follows once
  the juniper-data 0.17.1 and juniper-cascor 0.12.0 wheels clear their `pypi` gates. A floor on an
  unpublished release would make `[servers]` unresolvable. Item 3 of the Cursor flood-3
  follow-up (`notes/JUNIPER_2026-10-08_JUNIPER-ECOSYSTEM_CURSOR-FLOOD-3-DISPOSITION.md` §8).

### Fixed

- **`save_model` saves the recurrence model the run scored, instead of fitting a second one** (juniper-ml#2211).
  `util/experiments/run_experiment.py` used to re-run the `juniper-recurrence train` CLI in a second process, for
  up to 600 s, and nothing proved that fit saw the run's data: a `dataset_id` does not pin content, and two mints
  of one `equities_seq` id 85 s apart differed (F-P8).
  - When `POST /v1/train` returns an `operation_id` (juniper-recurrence 0.6.0 and later; juniper-ml pins 0.8.0),
    the driver calls `POST /v1/model/snapshots` with it as `expect_operation_id`, so the service saves its
    in-memory model only if that operation produced it. The driver then copies `<snapshots_dir>/<id>.npz`
    (`recurrence_launch.snapshots_dir`, else `$RUN_DIR/snapshots`) to `artifacts/results/model.npz` and checks
    its size against the response's `size_bytes`.
  - A 409 (another caller trained or restored after this run's train) fails the phase (`degraded`, exit 1), and
    nothing re-fits a substitute. An unusable snapshot id or a size mismatch fails it too, and a copy the run
    cannot vouch for is removed. A snapshot this run cannot read is recorded with a note, not faked.
  - Only a train response without an `operation_id` (a pre-W1.5 service) still re-fits through the
    launcher-recorded CLI. The new `manifest.save_model` block names the path that ran: `source` is `snapshot`
    or `refit`.
  - `docs/REFERENCE.md`, `docs/DEVELOPER_CHEATSHEET_JUNIPER-ML.md`, `docs/QUICK_START.md` and
    `docs/DOCUMENTATION_OVERVIEW.md` describe the snapshot path. Eight new tests in
    `tests/test_recurrence_operation_identity_and_dataset_budget.py`, all of which fail against `main`'s driver.
- **The release-train proposal now moves README's "Ecosystem Compatibility" table**, so a generated juniper-ml
  proposal is green as generated. `tests/test_pyproject_extras.py` `ReadmeCompatTableTest` holds that table to
  `pyproject.toml` in two ways, and `util/release_train/propose.py` satisfied neither.
  - **The lead-in.** "The pyproject pins matching `juniper-ml` X:" must name the pyproject version, and the
    generator never moved it. The 0.11.0 proposal (#2306) was the first generated since that guard landed (#1972).
    Its bare form fails Regression Tests with `'0.10.0' != '0.11.0'`, and #2306 carried a hand co-change commit. The
    meta's own bump now rewrites the line. A missing lead-in is never invented; the co-change checklist flags it
    REQUIRED instead.
  - **The rows.** Each pin also has a split-column Package / Pin row, and step 5b-ii moved only README's
    `### Extras` table, so an escaping in-repo bump shipped red. Simulated on `main`, the juniper-config-tools
    0.2.0 proposal (against the meta's `<0.2.0` ceiling) fails `test_compat_table_matches_pyproject`. The
    split-column editor `docs/REFERENCE.md` already used, re-anchored on `## Ecosystem Compatibility`, now moves the
    row in the same README edit as the extras table.
  - The proposal PR body no longer tells the reviewer of every escaping bump that the generator "has a known gap"
    and "will fail 3 arms". #1460 added that warning, and #1478 closed the gap a day later without removing it.
  - `docs/REFERENCE.md`'s compatibility sentence and matrix row remain a manual co-change for the meta's own bump,
    and the co-change checklist now says so.
  - New: `util/ad-hoc/2026-10-21_simulate_release_proposal.py` builds one proposal on a scratch copy and runs the 17
    suites that read the version, the pins, README or REFERENCE, against an untouched baseline. Both proposals
    above regress one suite on `main` and none with the fix. Ten new tests in
    `tests/test_release_train_propose.py`, eight of which fail against `main`'s module.

---

## References

- [CHANGELOG.md](https://github.com/pcalnon/juniper-ml/blob/v0.11.1/CHANGELOG.md)
- Archive target: `notes/releases/RELEASE_NOTES_v0.11.1.md`
