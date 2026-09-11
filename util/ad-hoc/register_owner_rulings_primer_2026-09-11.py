#!/usr/bin/env python3
"""
Record the owner's rulings on all sixteen parked PRIMER rows (2026-09-11), and correct the two
rows whose text the re-derivation disproved.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon
Created: 2026-09-11
Status: ad-hoc — one-off
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/register_owner_rulings_2026-09-09.py (the post-primer rulings two days earlier);
         HANDOFF_2026-09-09_defect-register-round-38-the-three-way-prompt-shipped-and-two-corrections-that-reversed-themselves.md

With these, **the set of rows a session may action without asking the owner first is no longer
empty** — it is every open row in the register. That sentence has stood since 2026-09-03 and its
removal is the point of this change, so §2's note is rewritten rather than deleted.

Every ruling was taken against evidence re-derived on the day, not against the primer's anchors.
Three rows did not survive that unchanged, and the corrections are applied here:

  * `APD-DATA-030` said error bodies carry NO retryability signal. `Retry-After` IS sent, on the
    auth-throttle 429 (`middleware.py`, via `HEADER_RETRY_AFTER`), and two tests assert it. The gap
    is narrower than written: no signal on 5xx, and no machine-readable code anywhere.
  * `APD-CASCOR-005` said the key comparison short-circuits. All three copies now use
    `hmac.compare_digest`, so the per-key comparison is timing-safe; what remains is the `any(...)`
    wrapper in cascor and juniper-service-core, which short-circuits on the first MATCH and so
    distinguishes key positions. juniper-data already carries the fix and the rationale.
  * `APD-DATA-022` reads "no `responses={}` anywhere". True: the single textual match in the routes
    is a comment naming this very row. Recorded so the next reader's grep does not mislead them.
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REG = ROOT / "notes" / "JUNIPER_2026-08-14_JUNIPER-ECOSYSTEM_DEFECT-REGISTER.md"

text = REG.read_text()


def sub(old: str, new: str, label: str) -> None:
    global text
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL [{label}]: expected 1 match, found {n} for:\n---\n{old[:200]}\n---")
    text = text.replace(old, new)
    print(f"  ok  {label}")


# ---- 1. The empty-set sentence is no longer true. ---------------------------------------------
sub(
    "> **The set of rows a session may action without asking the owner first is still empty.**)*\n",
    "> **The set of rows a session may action without asking the owner first was still empty when this\n"
    "> note was written. It is not any more** — see [§2.4](#24-owner-rulings-on-the-parked-primer-rows-2026-09-11),\n"
    "> which rules on all sixteen remaining parked rows. What that block does NOT do is weaken the rule\n"
    "> above: the rows became actionable because the owner ruled on them one at a time, which is exactly\n"
    "> what §2 requires, and not because a document asserted they were.)*\n",
    "1. empty-set sentence",
)

# ---- 2. The two disproved row texts. ----------------------------------------------------------
sub(
    "| APD-DATA-030   | Error bodies carry no retryability signal ",
    "| APD-DATA-030   | Error bodies carry no retryability signal **except on the auth-throttle 429, which does send `Retry-After` (corrected 2026-09-11)** — the gap is 5xx and the absence of any machine-readable code ",
    "2. APD-DATA-030 corrected",
)
sub(
    "| APD-CASCOR-005   | Key comparison short-circuits on match in 2 of 3 copies (see §3 assessment) ",
    "| APD-CASCOR-005   | Key comparison short-circuits on match in 2 of 3 copies — cascor and `juniper-service-core` wrap `hmac.compare_digest` in `any(...)`; juniper-data uses an explicit non-short-circuiting loop and carries the rationale. **Corrected 2026-09-11: every copy now uses `compare_digest`, so the per-key comparison is timing-safe; only the iteration short-circuits, distinguishing key POSITIONS to a holder of a valid key** (see §3 assessment) ",
    "3. APD-CASCOR-005 corrected",
)

# ---- 3. The rulings block, before §3. ---------------------------------------------------------
BLOCK = """### 2.4 Owner rulings on the parked primer rows (2026-09-11)

All sixteen. Taken interactively, four at a time, each against evidence re-derived that day rather
than against the primer's anchors — which is how the three corrections noted below were found. Each
entry records the option **chosen** and the options **rejected**, because a ruling that records only
its outcome is indistinguishable later from a drift.

**These rulings end the empty set.** They do not weaken §2's rule; they satisfy it.

#### juniper-data — HTTP semantics

- `APD-DATA-008` — **RULED.** Return **200 on reuse, 201 only on creation**. Rejected: keeping 201
  with an added `created` flag; doing both; leaving it. Note `CreateDatasetResponse` has no `created`
  field today, so a caller currently cannot distinguish a cache hit at all. Breaking for anything
  asserting 201.
- `APD-DATA-017` + `APD-DATA-032` — **RULED.** Emit a strong **`ETag` derived from the stored
  SHA-256**, and **move `access_count` / `last_accessed_at` out of the representation** so the
  metadata body can carry one too. Rejected: artifacts only; a weak validator that churns on every
  read. The two rows are one fix: the counters are precisely what blocks the metadata ETag.
- `APD-DATA-022` — **RULED.** Declare the error surface **once as router-level defaults**, with only
  route-specific codes inline. Rejected: per-route `responses={}` across ~30 decorators, which can
  drift route by route. *(The only textual match for `responses=` in the routes today is a comment
  naming this row — a grep alone will mislead.)*
- `APD-DATA-030` + `APD-DATA-031` — **RULED.** Adopt **RFC 9457 problem+json** from all three error
  sources, with a stable `type` and a retryability signal. Rejected: keeping `{"detail": …}` with
  added `code` / `retryable` fields; fixing only the validation inconsistency. Breaking for anything
  parsing `detail`. This also fixes, as a side effect, that validation errors put a LIST under the
  same key every other source fills with a string.
- `APD-DATA-026` — **RULED.** Make **`/filter` canonical and deprecate the bare list** in OpenAPI,
  keeping it served. Rejected: converging the shapes now (immediately breaking); keeping both and
  aligning only pagination. `/filter` with no filters is already a superset.
- `APD-DATA-027` — **RULED.** Emit **RFC 8288 `Link`** (`next` / `prev` / `first`). Rejected: links
  in the body. The cursor state already exists; only its expression is missing.
- `APD-DATA-028` — **RULED.** Add **`/v1/datasets/named/{name}/versions` and `/named/{name}/latest`**
  and deprecate the query form. Rejected: reading `name` as a filter and leaving it; moving without
  an alias. The `named/` prefix is required because `/{dataset_id}` already owns that path slot.
- `APD-DATA-029` — **RULED.** Emit **`Content-Location`** naming the canonical `/{dataset_id}` URI.
  Rejected: a 307 redirect, which costs every caller a round trip. Composes with the ETag work above.

#### Clients and ecosystem

- `APD-ECO-001` — **RULED.** Build the **full `Idempotency-Key` mechanism on every mutating route**,
  including create. Rejected: keying only the genuinely unsafe mutations (batch-delete,
  cleanup-expired, batch-create) and documenting create's natural idempotency, which was the
  narrower option offered. Consistency across the surface was preferred to the smaller change, so
  this ruling accepts a key store and expiry policy on a route that is already content-addressed.
- `APD-ECO-003` — **RULED.** **Expose a per-call timeout** on the public client methods. Rejected:
  per-operation default tables. The transport already honours it — `_request` does
  `kwargs.setdefault("timeout", self.timeout)` — so only the public signatures are missing.
- `APD-ECO-004` — **RULED.** **`TypedDict` response shapes** for the 43 `Dict[str, Any]` returns.
  Rejected: sharing the servers' Pydantic models, which would create a client-to-server dependency
  and a version-lockstep problem across separately released packages.
- `APD-RCLIENT-004` — **RULED.** **Use the recurrence server's own models** — deliberately different
  from `APD-ECO-004`, and the difference is the reason: client and server ship from the SAME
  repository at the same version, so the lockstep objection that decided `-004` does not apply here.

#### Cross-cutting

- `APD-CASCOR-005` — **RULED.** **Port juniper-data's explicit `matched`-flag loop** into cascor and
  `juniper-service-core`. Rejected: accepting and documenting the residual leak. Four lines each,
  against an existing reference implementation that already carries the rationale in a comment.
  Candidate for a named guard in `juniper-ml/tests/test_service_fork_drift.py` (§2.3), since this is
  exactly the copy-drift shape that registry exists to hold.
- `APD-ML-001` — **RULED.** **State the capping rule; leave the pins.** Rejected: capping
  consistently, which would make `juniper-ml` gate every sibling `0.y` release; removing caps
  entirely. The register's own analysis is that the pattern is coherent — so the defect is the
  silence, and the remedy is a note beside the pins and in the contract test's docstring.

#### One consequence, ruled separately

The `equities` / `equities_seq` rulings of 2026-09-09 change artifact content, so those generators
go to **`generator_version` 4.0.0** while the others stay at `3.0.0`. Ruled with the published
wheels in view (juniper-data 0.14.0 and six siblings released 2026-09-10/11): rejected were bumping
every generator to keep the ecosystem single-versioned, and holding the change for a release window.
The ecosystem data-contract note, which currently states every generator is at `3.0.0`, must be
updated in the same change.

---

"""
sub("---\n\n## 3. Critical and security findings — detail\n", BLOCK + "## 3. Critical and security findings — detail\n", "4. §2.4 rulings block")

REG.write_text(text)

sys.path.insert(0, str(HERE))
from register_open_set import format_report, parse_register  # noqa: E402
from register_status_crosscheck import crosscheck  # noqa: E402

seen, fixed = parse_register(text)
print("\nopen-set:", format_report(seen, fixed).splitlines()[0])
raise SystemExit(crosscheck(text))
