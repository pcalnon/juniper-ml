<!-- Archived verbatim 2026-09-24 from subagent a5e53dde657452894 of session 8f86dec2 (final message). -->

Everything is clean — server stopped, no stray processes, all scripts in scratch. Here is my final report.

---

## Lane A1 (SECURITY) — juniper-data#428 at `3a76a4c` — FINAL REPORT

**VERDICT: HOLDS WITH FINDINGS.** The round-2 HIGH ReDoS is genuinely fixed — I proved the new `_ENTITY_TAG_LIST` accepts exactly the old language and runs in linear time by three independent methods plus a negative control, and confirmed it live (a 45-byte field that stalled the service ~1.7 s now parses in microseconds). Three other security-relevant round-2 findings (caller-id logging, orphan If-Match, fail-closed write) are verified fixed from primary artifacts. The residual findings are all LOW. My tree was verified byte-identical to `3a76a4c` in the main checkout (all 7 files `MATCH`).

### Findings (most severe first)

**F1 — LOW — `juniper_data/api/http_cache.py:138` and `:154`: the `*` sentinel is matched with Python `str.strip()`, so `*`+obs-text-whitespace fails OPEN on a write.**
`_well_formed` (`:138`) and `_list_names` (`:154`) test `field.strip() == "*"`. Python `str.strip()` is Unicode-aware and removes more than RFC 9110 OWS (SP/HTAB). Of the extra characters, `0x85` (NEL) and `0xA0` (NBSP) are valid HTTP field-value bytes (obs-text) and reach the app, so `If-Match: *\x85` is read as `*`. This contradicts the module's own stated contract ("a write fails closed on a precondition it cannot read", `:53–56`) and the round-2 fail-closed fix (their finding 10).
Evidence — live PATCH proceeded and wrote tags it should have 412'd (`live_functional2.py`):
```
PATCH IM '*'+NEL \x85  -> 200   (expected 412)
PATCH IM '*'+NBSP \xa0 -> 200   (expected 412)
tags now: ['star-85', 'star-a0', 'w4']    # both writes landed
```
`star_strip.py` enumerates the reachable over-strip set as exactly `{0x85, 0xA0}` (VT/FF/FS are rejected by httptools with 400 first) and shows the write path: `if_match_fails("*\x85")=False`, so a bare `If-Match: *\x85` on PATCH → `write_preconditions_hold=True` → proceeds. Impact is low (caller weakens only their own precondition against an existing resource; no cross-caller effect, no DoS). Proposed fix: strip only OWS — `field.strip(" \t") == "*"` at both sites; verified this leaves every legal field unchanged and makes every `*`+obs-ws malformed (→ fail-closed).

**F2 — LOW — cap `http_cache.py:76` (8192) + global lock `storage/base.py:115`: residual bounded cost; the cap is ~8× larger than any legitimate field.**
The fix bounds the parse, but a worst-case field *at* the cap still costs real synchronous CPU that runs on the event loop for a GET and under `DatasetStore._version_lock` for a PATCH (the precondition callback `datasets.py:1254-1257` runs `write_preconditions_hold` inside `with self._version_lock` at `base.py:375,379`; that lock is a single class attribute shared by every dataset, also held by `record_access` on every GET). Measured (`route_combo_cost.py`): worst under-cap request ≈ **4.1 ms (GET), 5.2 ms (PATCH)** of pure parse; a legitimate request (a few tags) is <50 µs. The 8192 cap admits ~2730 tiny tags / ~120 full sha256 tags. Live load with rate-limiting off (`live_load.py`): `/v1/health` median rose from **2.3 ms idle → 186 ms** (get_meta worst-case) / p99 **424 ms** (artifact). Bounded and gated by the default 60-req/min rate limiter, so a single caller's cost is negligible; it is a hardening observation, not the exponential blow-up. Proposed fix: lower `MAX_PRECONDITION_FIELD_LENGTH` (e.g. 1024) — cuts worst-case event-loop/lock hold ~8× at zero cost to real clients.

**F3 — LOW (out of scope; pre-existing, NOT introduced by #428) — a tag containing a lone surrogate durably 500s the dataset and writes caller-derived text into an ERROR log at request rate.**
`PATCH .../tags add_tags=["\ud800"]` persists, then every subsequent metadata GET/PATCH of that dataset → 500 (`PydanticSerializationError` at `_metadata_response`/`datasets.py:156`), logged by `app.py:227` `logger.exception("Response serialization failed")` whose traceback carries the surrogate. Confirmed pre-existing because the untouched `/v1/datasets/filter` route also 500s on it. Recoverable by removing the tag. Out of the conditional-request scope but worth a register row.

**F4 — NIT (out of scope) — HTTP layer accepts 100 000 header lines (394 ms) and an 8 MB single header (112 ms).** The 8192 cap protects the *regex* (a 100k-line `If-None-Match` joins to ~400 KB, is measured over-cap, and never reaches the regex), but uvicorn buffers the raw headers regardless; `RequestBodyLimitMiddleware` covers the body only. A uvicorn/reverse-proxy concern, not #428.

### Verified FIXED (round-2 findings), from primary artifacts
- **F1 HIGH ReDoS** — new `_ENTITY_TAG_LIST` (`:95`) proven equivalent to the old (`git show 3ecb106`) by derivative bisimulation (7 state pairs), exhaustive enumeration (6.7M strings, 0 diffs), and 300k random differential — `equiv_proof.py`; a negative control catches 5 language-changing mutants — `equiv_negative_control.py`. Linear: log-log slope ~1.0 within the cap (`redos_scaling.py`); the super-linear-*looking* per-char cost appears only *far above* the cap and is memory pressure (tracemalloc scales linearly; the flat-memory ` `*n shape stays 104 ns/char), unreachable because the length check (`:136`) fires before the regex.
- **F3 MEDIUM caller-id logging** — diffed pre-fix→merged: `InvalidDatasetIdError` re-raised (`datasets.py:1079`), fallback logs `type(exc).__name__` only, no `exc_info` (`:1082`). Live: invalid-id artifact request → 400 with no WARNING carrying the id.
- **F6 LOW orphan If-Match** and **F10 NIT fail-closed write** — live: over-cap/garbage `If-None-Match` on PATCH → 412, nothing written; orphan/absent → 404/412 (`live_functional.py`, `live_functional2.py`).

### Non-vacuity (task 8) — proven
`TestEntityTagListRunsInLinearTime` **FAILS** when the old backtracking regex is restored in a scratch copy (`tree-oldregex`): subprocess timed out at 30 s, `AssertionError: ...the entity-tag list grammar backtracks`, 1 failed in 32.9 s. It **PASSES** on `3a76a4c` (56 passed in 7.7 s). The test is non-vacuous and pins the fix.

### Attacks that did not land (numbers)
- Every hostile shape (whitespace/comma/quote/`W/`-heavy, many short elements, fail-at-end, fail-at-start) at 256 B → 1 MiB (`redos_offline.py`): within the operative range (≤ cap) all are **≤ ~1.8 ms**; entry points at 8192 peak **≈ 5.2 ms**; one char over the cap drops to **≤ 3.4 µs** (cap short-circuits the regex).
- Cap is enforced **before** the regex and over the **combined/joined** field: live 2033 header lines joining to 8194 chars → treated over-cap (200, not 304); two under-cap lines joining over → over-cap.
- `*` placement: length check precedes the `*` test, so `*`+8192 spaces is malformed (matches the suite's own assertion).
- After-parse compare cost is linear in tag count (~3.4 ms for ~2730 tags at the cap); nothing quadratic.
- Path-param `_validate_dataset_id` is linear/bounded (129 chars → 3.4 µs; 64 KiB → 135 µs).

### What this evidence cannot support
- Measured on the `JuniperData` env's **free-threaded 3.14.2** build with **uvicorn 0.40.0 / httptools 0.7.1** (httptools re-enabled the GIL — `gil_enabled=True`). Production `Dockerfile` uses `python:3.14-slim` (default GIL build) with **uvicorn 0.53.0 / httptools 0.8.0** (`requirements.lock`). Same single-loop / regex-on-loop / GIL-during-`re` architecture, so the *qualitative* residual-cost finding transfers; exact production latencies I cannot state.
- Load numbers (F2) were taken with **rate limiting disabled**, 24 connections, on a box at loadavg ~23 — they show the amplification mechanism, not production-representative latency (default 60/min/key bounds a single caller to negligible cost).
- The over-strip set (F1) was enumerated only over `0x00–0xFF`; the reachable set there is `{0x85, 0xA0}`.

### Credential hygiene
No slip. The scratch server ran under `env -i` (no inherited secrets) with a self-chosen dummy key `laneA1-scratch-key`; nothing was sent to any external service; the owner's email was never used. I stopped the server I started (SIGTERM; "shutdown complete" logged; port 18431 free); the exit-143 background notice is that expected SIGTERM. No process I did not start was touched.

### Scripts I wrote (all under `…/scratchpad/r42/data428-laneA1/`)
`equiv_proof.py`, `equiv_negative_control.py`, `redos_offline.py`, `redos_scaling.py`, `route_combo_cost.py`, `star_strip.py`, `serve_scratch.py`, `start_server.bash`, `rawhttp.py`, `live_functional.py`, `live_functional2.py`, `live_load.py`, `verify_tree.bash`. Reference extracts: `http_cache_3ecb106.py`, `datasets_3ecb106.py`; the mutated copy `tree-oldregex/`; results JSON `redos_offline_results.json`, `live_functional.json`, `live_functional2.json`, `live_load_results.jsonl`.
