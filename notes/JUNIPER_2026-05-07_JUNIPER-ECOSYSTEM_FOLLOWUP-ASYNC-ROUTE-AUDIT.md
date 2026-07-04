# Followup — Async-route audit migration deferred items

**Status**: open (created 2026-05-07)
**Owner**: Paul Calnon
**Trigger**: see per-item triggers below
**Source plan**: [`JUNIPER_2026-05-07_JUNIPER-ECOSYSTEM_ASYNC-ROUTE-AUDIT-HOOK-MIGRATION-PLAN.md`](./JUNIPER_2026-05-07_JUNIPER-ECOSYSTEM_ASYNC-ROUTE-AUDIT-HOOK-MIGRATION-PLAN.md)
**Estimated effort**: ~30 minutes (item 1) + ~2 hours (item 2, only if triggered)

---

## Background

The four-phase async-route audit migration shipped end-to-end on 2026-05-05–06 (15 PRs across four repos; see the plan's §0 "Migration ledger"). Two items were deliberately deferred at the time of close-out and are tracked here so they don't slip.

## Item 1 — Add the new CI lane to branch-protection required-checks

**What**: Each in-scope repo gained a new CI job, `Async-route audit (BUG-JD-10 class)`, in Phase 4. The job hard-fails on any new ASYNC* violation, but it is not yet on the "Require status checks" list in branch-protection rules. A PR could currently be merged even if this job fails (only the contributor's discipline / review prevents it).

**Why deferred**: GitHub branch-protection rules can only be edited from the web UI (or via `gh api` against the protected-branches endpoint, which requires the user's auth, not Claude Code's session) and the change is repo-admin-only. It was cleaner to merge the four code PRs first, confirm the lane runs green on a real PR in each repo, and only then promote it to required.

**Why we should still do it**: a soft-required CI lane drifts. Without "Required" status, a year from now someone disables the lane in the workflow file and nobody notices because nothing fails. Promoting it to required is the difference between "we have a check" and "the check enforces."

### Affected repos

Four repos. For each, the new check name is exactly **`Async-route audit (BUG-JD-10 class)`** (the same string GitHub displays in PR check lists; no "soft-fail" suffix because Phase 4 dropped that).

| Repo | Branch protection settings URL | Verifier (run a PR; the check should appear) |
|------|--------------------------------|----------------------------------------------|
| juniper-data           | <https://github.com/pcalnon/juniper-data/settings/branches> | Already passing on data#98 |
| juniper-cascor         | <https://github.com/pcalnon/juniper-cascor/settings/branches> | Already passing on cascor#235 |
| juniper-canopy         | <https://github.com/pcalnon/juniper-canopy/settings/branches> | Already passing on canopy#248 |
| juniper-cascor-worker  | <https://github.com/pcalnon/juniper-cascor-worker/settings/branches> | Already passing on worker#57 |

### Procedure (per repo)

1. Open the repo's branch-protection rule for `main` (Settings → Branches → "main" rule → Edit).
2. Under "Require status checks to pass before merging", add `Async-route audit (BUG-JD-10 class)` to the required-checks list.
3. Save the rule.
4. Open a trivial PR (e.g. a whitespace fix) and verify the new lane appears as **Required** in the PR's checks panel.

### `gh` CLI alternative (one-liner per repo)

If you'd rather script it (requires `repo:admin` scope on the token):

```bash
# Repeat for each of the four repos. Replace REPO appropriately.
REPO=pcalnon/juniper-data
gh api -X GET "repos/${REPO}/branches/main/protection/required_status_checks" \
  --jq '.contexts'   # see what's currently required
gh api -X PATCH "repos/${REPO}/branches/main/protection/required_status_checks" \
  -f 'contexts[]=existing-check-1' \
  -f 'contexts[]=existing-check-2' \
  -f 'contexts[]=Async-route audit (BUG-JD-10 class)'
```

(Pass the **full** `contexts` list — the PATCH replaces, not appends.)

### Don't-forget tripwire

Run this periodically and confirm all four repos return the check name:

```bash
for REPO in pcalnon/juniper-data pcalnon/juniper-cascor \
            pcalnon/juniper-canopy pcalnon/juniper-cascor-worker; do
  echo "=== $REPO ==="
  gh api "repos/${REPO}/branches/main/protection/required_status_checks" \
    --jq '.contexts[]' 2>/dev/null | grep -i "async-route" \
    || echo "  ⚠ NOT REQUIRED"
done
```

---

## Item 2 — Optional centralised deny-list (`util/check_async_routes.py`)

**What**: §5.2 of the migration plan proposed a 100-line companion AST script in `juniper-ml/util/check_async_routes.py` that walks `async def` bodies in each repo's API code and flags calls to project-internal blocking primitives that ruff's stdlib-focused ASYNC* rules don't recognise (e.g. `*Store.get_meta`, `*Store.update_meta`, anything decorated with `@blocking`). Q3 in §10 confirmed the centralised location.

**Why deferred**: Phase 0 enumeration found that ruff's stdlib coverage caught all 27 violation sites without the custom script. Writing it now would mean writing infrastructure for a problem we don't have. The trigger for actually building it is a future regression that ruff misses.

**Trigger** (any one is sufficient):

1. A new BUG-JD-10-class incident occurs in production where a sync call inside an `async def` route handler stalls the event loop, **and** the call site would not have been caught by ruff's `--select ASYNC` (i.e. it's a project-internal helper, not a stdlib primitive).
2. A code review surfaces a sync call inside an `async def` that uses a project-internal helper (typical pattern: `store.<method>` from `juniper_data.storage`) and the reviewer notes "this should have been caught by automation."
3. We add a third sync helper class to `juniper_data` / `juniper_cascor` and want defense in depth without relying on the reviewer noticing.

**Estimated implementation**: ~2 hours when needed. Outline:

- Walk each repo's `*/api/routes/*.py` and `*/api/main.py` (configurable via a small JSON manifest).
- For each `async def`, AST-walk the body for `Call` nodes whose `func` matches a deny-list pattern.
- Skip calls wrapped in `await asyncio.to_thread(...)` (the standard escape hatch).
- Honour `# noqa: BLOCKING` line-level escape with mandatory `# why:` comment.
- Wire as a pre-commit `local` hook in each consumer repo + a CI job (mirror the ruff lane added in Phase 4).

**Initial deny-list** (from the migration plan, §5.2):

| Pattern | Why it blocks |
|---|---|
| `*Store.get_meta` / `update_meta` / `delete_meta` | filesystem I/O |
| `*Store.read_artifact` / `write_artifact` | filesystem I/O |
| `requests.*` (use `httpx.AsyncClient`) | sync HTTP — already caught by ruff ASYNC210 |
| `httpx.Client.*` (use `httpx.AsyncClient`) | sync HTTP — already caught by ruff ASYNC210 |
| `@blocking` (sentinel decorator we'd add) | explicit opt-in marker |

(Two of those rows duplicate ruff's coverage and would be dropped at implementation time; the unique value is the `Store.*` and decorator rows.)

**Don't-forget tripwire**: this item is dormant until a real regression triggers it. The migration plan §0 ledger flags it under "Open follow-ups"; this followup doc is its standalone tracker so it doesn't get buried.

---

## Related

- [`JUNIPER_2026-05-07_JUNIPER-ECOSYSTEM_ASYNC-ROUTE-AUDIT-HOOK-MIGRATION-PLAN.md`](./JUNIPER_2026-05-07_JUNIPER-ECOSYSTEM_ASYNC-ROUTE-AUDIT-HOOK-MIGRATION-PLAN.md) — the source plan, §0 ledger lists every Phase-1–4 PR
- [`JUNIPER_2026-05-06_JUNIPER-ECOSYSTEM_ASYNC-ROUTE-VIOLATIONS.md`](./JUNIPER_2026-05-06_JUNIPER-ECOSYSTEM_ASYNC-ROUTE-VIOLATIONS.md) — Phase 0 enumeration
- BUG-JD-10 — the original incident that motivated the migration (juniper-data `batch_update_tags` route)
