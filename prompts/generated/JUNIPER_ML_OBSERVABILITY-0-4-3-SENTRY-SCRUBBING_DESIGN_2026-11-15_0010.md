# juniper-observability 0.4.3, designed and validated on its own (R-OBS-SC-3): the Sentry paths 0.4.2 left open

## Role

You are a fresh session that writes the design of record for juniper-observability 0.4.3, runs its independent
validation rounds, and brings the design to the owner to rule on. You write no implementation, cut no release and open
no lock PR: the owner's ruling of 2026-11-13 puts all three after their ruling on your design.

The ruling (R-OBS-SC-2 round 2, Q1, answered 2026-11-13 02:14:33Z in session `218ff61e`; label and option text
verbatim): "Now, in its own thread (Recommended)" -- "I write a start prompt for a fresh session. That session writes
the design to notes/, runs its validation rounds, and brings you the design to rule on. Implementation, the 0.4.3
release and the third lock round follow that ruling. Cost: one design plus review rounds, on whichever model has quota
(the flood-4 session reports the weekly Fable limit was reached today)." This file is that start prompt, written on
2026-11-15 by session `1b4fec84`. It prints with
`python3 util/ad-hoc/2026-11-09_r_obs_sc_2_owner_answers.py 218ff61e --full`.

## Resources

- **The plan of record**: `notes/JUNIPER_2026-10-04_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN.md` (v1; 1.15.15
  when this was written, and v1.15.16 may have landed since). Find these by text, not line number:
  - §5's row "**R-OBS-SC-3** (owed; owner ruling 2026-11-08): juniper-observability 0.4.3": the owner's scope is query
    strings (canopy's `?api_key=` among them) and a Sentry Logs policy; round 1's queue beside them is request bodies,
    breadcrumbs, exception values and list-shaped headers. Its process column reads "Designed and validated on its own
    (the owner's ruling); then its own lock round", and its unblocks column "XC-SENTRY's end; the trio's restart, if
    S0.11's pass needs it".
  - §5's R-OBS-SC-2 note, bullet "What it leaves open", and the bullets on what the 0.4.2 pins changed per consumer.
  - §3 "XC-SENTRY": mitigations (a), a Sentry-side scrubbing rule that must cover Sentry Logs as well as events, and
    (b), blank DSNs on the running services at their next restart. Both stay in force until 0.4.3 reaches the running
    services. The owner's ruling 6 of 2026-11-13 ("Probe per environment") has the restart proceed with blank DSNs.
- **The v2 draft**: `notes/JUNIPER_2026-11-12_JUNIPER-ECOSYSTEM_CONSOLIDATED-DEVELOPMENT-PLAN-V2.md` is "a draft re-plan,
  not validated"; v1 holds the record (the draft says so itself).
- **What 0.4.2 left**: `notes/releases/RELEASE_NOTES_juniper-observability_v0.4.2.md`, the paragraph "**Still open, for
  0.4.3**": query strings, including canopy's `?api_key=` WebSocket parameter, which reaches Sentry under the default
  `send_pii=False`; Sentry Logs (`enable_logs=True` has no `before_send_log`, so neither the hook nor the SDK's scrubber
  sees a log record, and a uvicorn access line carries its query string); request bodies; breadcrumbs; exception
  values; and `headers` sent as a list of pairs, which nothing in Juniper emits. The same notes give 0.4.2's rating
  (Medium) and class (CWE-201), and the test design (`TestNoSensitiveRequestValueReachesTheWire`).
- **The code**: `juniper-observability/juniper_observability/sentry.py` (`configure_sentry`, its `before_send` and
  `before_send_transaction` hook, `enable_logs`), `juniper-observability/tests/test_sentry.py`, and the package's
  `CHANGELOG.md`. The publish pipeline is in `docs/REFERENCE.md` § "Independent Sibling Package Publish Pipelines".
- **The probe that measured 0.4.2**: `util/ad-hoc/2026-11-08_p3_07_sentry_wire_probe.py` (P3-07's wire probe; it sends
  secrets in request headers and cookies only, so it does not yet cover query strings, logs, bodies or exception
  values).
- **The consumers** (read each repository's `main`; never a primary's working tree as the truth):
  - juniper-data turns `send_pii` on only through `JUNIPER_DATA_SENTRY_SEND_PII` (opt-in, off by default);
  - juniper-cascor calls `configure_sentry` through `src/api/observability.py`, and its CLI has its own
    `sentry_sdk.init` in `src/main.py` (`send_default_pii=False`);
  - juniper-canopy calls it through `src/observability.py`; its WebSocket accepts the key as `?api_key=` and, under the
    opt-in `ws_auth_enabled`, as `Sec-WebSocket-Protocol: bearer, <key>`;
  - juniper-recurrence's lock has no `sentry-sdk`.
  - juniper-cascor 0.14.0 and juniper-canopy 0.10.0 floor `juniper-observability>=0.4.2`. Both were cut on 2026-11-15;
    check PyPI for whether they are published.
- **Test hygiene**: blank the six Sentry DSN variables for every test or service run
  (`util/ad-hoc/2026-11-12_run_with_blank_sentry_dsns.py`; never through an interactive shell). `SENTRY_SDK_DSN` is set
  and non-empty in this host's session environment.

## Primary Objective

Write `notes/JUNIPER_<YYYY-MM-DD>_JUNIPER-ML_OBSERVABILITY-0-4-3-SENTRY-SCRUBBING-DESIGN.md` (the notes naming
convention: `notes/JUNIPER_2026-07-04_JUNIPER-ML_NOTES-FILE-NAMING-CONVENTION.md`). Validate it, and bring the owner the
decisions it needs. For each path below, the design states:

1. what reaches Sentry today, MEASURED on the wire with the real SDK at the versions the consumers lock (extend the
   P3-07 probe; name the sentry-sdk versions you ran);
2. the options, with what each costs and breaks;
3. the recommendation;
4. the tests that would pin it, and how a mutation check would show those tests are not vacuous;
5. what changes for each consumer.

The paths:

- **Query strings**: the request URL's query in events and transactions, and the uvicorn access log line.
- **Sentry Logs**: whether the floor SDK offers a log hook, and the policy (scrub, drop, or turn `enable_logs` off).
  State the sentry-sdk floor each option needs, and check that floor against every consumer's lock and `pyproject.toml`.
- **Round 1's queue**: request bodies, breadcrumbs, exception values and list-shaped headers.

**Addendum, 2026-11-23: sentry-sdk 3.0.0.** This was added after the prompt was generated; see
`notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md`, R14, R15 and R57.

- **What 3.0.0 removed.** sentry-sdk 3.0.0 reached PyPI at 2026-11-23T09:30:33Z. It has no `send_default_pii` option
  and no `sentry_sdk.scrubber` module, and `sentry_sdk/client.py:102` raises `TypeError("Unknown option ...")` for an
  unknown option.
- **What that breaks.** `juniper_observability/sentry.py:182` passes `send_default_pii`, so `configure_sentry` with a
  DSN raises under 3.x. With an empty DSN, it returns before `sentry_sdk.init`.
- **The cap.** juniper-ml#2608 (merged 2026-11-23T20:50:42Z) caps `sentry-sdk[fastapi]>=2.35.0,<3` at
  `juniper-observability/pyproject.toml:35` and `:44`, under `[Unreleased]`. No release carries it yet, and which
  release number carries it is the Overtoad's ruling (R14).
- **The consumers' floors are uncapped.** juniper-cascor `pyproject.toml:151` and juniper-canopy `:251` require
  `sentry-sdk>=2.0.0`, and juniper-data `:142` requires `sentry-sdk[fastapi]>=2.0.0`. juniper-cascor's
  `src/main.py:236` passes `send_default_pii` itself (R15).
- **What the design must now state.** "The sentry-sdk floor each option needs" above gains a ceiling. The design
  states whether 0.4.3 stays on 2.x behind the cap or ports `configure_sentry` to 3.x. For each path above, it says
  what 3.x offers in place of the scrubber and of `send_default_pii`, measured with the real SDK, not assumed.

**Addendum, 2026-11-24: this design is now 0.4.4, and 0.4.3 ports to sentry-sdk 3.x.** The Overtoad ruled on
2026-11-24 (22:26:46Z) on three points:

- juniper-observability **0.4.3** is the sentry-sdk 3.x port, supporting both majors (`sentry-sdk[fastapi]>=2.35.0,<4`);
- R-OBS-SC-3, this design, becomes **0.4.4**;
- the consumers are ported to 3.x.

The rulings are recorded in `notes/JUNIPER_2026-11-23_JUNIPER-ECOSYSTEM_R-OBS-SC-2-FOLLOW-UPS-REMAINING-TASKS.md`
(R14, R15, R20). This file keeps its name as a record. The port is juniper-ml#2647. What it changes here:

- **Both majors are in scope.** On 2.x, 0.4.3's `configure_sentry` passes 0.4.2's options, and on 3.x
  `data_collection` and `before_send_span`. Each option this design adds needs a form on each major, or a ruling that
  drops one.
- **Already done on 3.x in 0.4.3:**
  - Query parameters are filtered by 3.x's own substring denylist; `?api_key=` reaches Sentry raw on 2.x only.
  - Request bodies are off (`http_bodies: []`) until this design rules on them.
  - The hooks apply 2.76.0's `EventScrubber` denylist and, without PII, its PII denylist. 3.0.0 deleted the scrubber.
- **`before_send_log` is a top-level option on 2.35.0, 2.76.0 and 3.0.0** (each wheel's `consts.py`). A Sentry Logs
  policy can install one on both majors. 0.4.3 installs none.
- **Pre-existing findings of the port's reviews**, all in this design's channels:
  - juniper-canopy's `POST /api/remote/connect` body field `authkey` reaches Sentry on 2.x, in `request.data`, because
    2.x's denylist does not match it;
  - five proxy headers carry the client address without `send_pii`: `Forwarded`, `X-Client-IP`, `CF-Connecting-IP`,
    `True-Client-IP` and `X-Cluster-Client-IP`;
  - Sentry Logs carry logging extras raw on both majors.

Then the release plan. Patch or minor, judged by what the change does to the public API and to what consumers see.
After the release comes the third lock round in each consumer, and the floors in each consumer's next release
PR: round 1's ruling 1 of 2026-11-09, "In release PRs", records that each consumer raises the floors in its
next `release/<pkg>-v<ver>` PR. Also cover what retires XC-SENTRY (a) and (b), and in what order.

## Assigned Tasks / Directives

1. Read the resources above first. Check every fact this prompt states against its source before you rely on it. This
   prompt names nothing as measured that its author did not read, but the tree has moved since.
2. Draft the design. Cite `file:line` on `main` for code and `§`/text anchors for documents, and never invent a path,
   a symbol or a version.
3. Validate it in independent rounds: at least two reviewers per round, briefed with the code and the design rather
   than your conclusions (the repo's adversarial validation SOP). Record every finding and what you did about it.
   Reviewers return their reports as their final message, because sub-agents cannot write report files here.
4. Bring the owner the decisions it needs, one question at a time. Open each with a short plain-language account of
   what it decides, what waits on it, and what each option would set in motion (the owner's ruling 3 of 2026-11-13).
   Before asking, release any peer session that waits on you, because the dialog blocks until it is answered.
5. Land the design through a docs PR, under whatever merge approval the owner gives your session. Approval does not
   carry over from an earlier session.

## Constraints

- No implementation, release or lock PR before the owner rules on the design.
- Never write under `/tmp` or `/var/tmp`: use the repo's gitignored `tmp/`.
- Never pull or switch a primary checkout. The owner's ruling 7 of 2026-11-13 allows guarded fast-forwards of the
  juniper-ml primary only, on its stated conditions. Read sibling code from `origin/main` (`git show`, or a tarball of
  an exact SHA).
- Every commit is GitHub-signed (`util/open_signed_pr.py`, `util/push_signed_commit.py`). Never commit unsigned.
- Follow the thread-handoff procedure (`notes/JUNIPER_2026-02-23_JUNIPER-ML_THREAD-HANDOFF-PROCEDURE.md`) before
  context runs short.
- In every summary, name every document you reference or change, by filename.
