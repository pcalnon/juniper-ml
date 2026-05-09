# Followup — Drop `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` override

**Status**: open (created 2026-05-06)
**Owner**: Paul Calnon
**Trigger**: gitleaks-action publishes a release that runs on Node.js 24 (upstream PR [#215](https://github.com/gitleaks/gitleaks-action/pull/215))
**Tracking issue**: [pcalnon/juniper-ml#229](https://github.com/pcalnon/juniper-ml/issues/229)
**Estimated effort**: ~30 minutes (six identical workflow edits across the ecosystem)

---

## Background

On 2026-05-06 the Juniper ecosystem hit GitHub's Node.js 20 → 24 forced
deprecation: gitleaks-action v2.3.9 (the latest released version) ships as a
Node.js 20 action, and GitHub will force-migrate Node 20 actions to Node 24
on **2026-06-02**. Until upstream releases a node24-pinned build, every
gitleaks invocation across the ecosystem emits:

```
##[warning]Node.js 20 actions are deprecated. The following actions are
running on Node.js 20 and may not work as expected:
gitleaks/gitleaks-action@ff98106e4c7b2bc287b24eaf42907196329070c7. Actions
will be forced to run with Node.js 24 by default starting June 2nd, 2026.
```

We worked around this by setting GitHub's documented escape hatch
`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"` as a step-level env variable on
each gitleaks-action invocation in 6 repos. This forces the existing v2.3.9
action to run on Node.js 24 right now, eliminates the deprecation warning,
and ensures continued operation past the cutover.

The override is a temporary measure. It must be removed once gitleaks-action
ships a release that runs on Node.js 24 natively.

## Removal trigger

Watch for any of these signals — **any one** is sufficient:

1. Upstream PR [gitleaks/gitleaks-action#215](https://github.com/gitleaks/gitleaks-action/pull/215)
   ("chore: migrate to Node 24 runtime (v3)") merges.
2. Upstream PR [#207](https://github.com/gitleaks/gitleaks-action/pull/207)
   ("Upgrade from 'node20' to 'node24'") merges.
3. A new gitleaks-action release tag appears that lists Node 24 in its
   `action.yml` runtime declaration (`runs.using: 'node24'`).

Quick check command:

```bash
gh api repos/gitleaks/gitleaks-action/releases/latest --jq '.tag_name'
gh api repos/gitleaks/gitleaks-action/contents/action.yml --jq '.content' \
  | base64 -d | grep "using:"
```

## Removal procedure

When the trigger fires, do the following in **one PR per repo** (or one
ecosystem-wide PR if convenient):

1. Bump the gitleaks-action SHA pin in each repo to the new node24-pinned
   release.
2. Remove the `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"` line from each
   gitleaks-action env block.
3. Remove the explanatory comment block introduced by the override PRs
   (the 5-line block referencing "GitHub forces Node 24 on 2026-06-02").
4. Verify on each PR that the gitleaks step still runs and produces no
   deprecation warnings.

Affected files (one gitleaks-action invocation in each):

| Repo | File | Override PR |
|------|------|-------------|
| juniper-cascor | `.github/workflows/ci.yml` | [#229](https://github.com/pcalnon/juniper-cascor/pull/229) |
| juniper-cascor-worker | `.github/workflows/ci.yml` | [#54](https://github.com/pcalnon/juniper-cascor-worker/pull/54) |
| juniper-data | `.github/workflows/ci.yml` | [#91](https://github.com/pcalnon/juniper-data/pull/91) |
| juniper-canopy | `.github/workflows/ci.yml` | [#242](https://github.com/pcalnon/juniper-canopy/pull/242) |
| juniper-data-client | `.github/workflows/ci.yml` | [#52](https://github.com/pcalnon/juniper-data-client/pull/52) |
| juniper-cascor-client | `.github/workflows/ci.yml` | [#39](https://github.com/pcalnon/juniper-cascor-client/pull/39) |

Locator command (run from the parent `Juniper/` directory):

```bash
grep -rn "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24" \
  juniper-*/.github/workflows/
```

## Don't-forget tripwires

If the override is still in place after **2026-06-02** (the GitHub-forced
cutover), the override becomes a no-op (Node 24 is the default) but the
explanatory comments will be misleading. Run the locator command above
periodically.

If gitleaks-action issues a new release that drops support for the
`FORCE_JAVASCRIPT_ACTIONS_TO_NODE24` env (unlikely but possible) and we
still rely on it, the override may either be ignored (silent fallback to
Node 24) or cause an action error. The locator command catches this case
too.

## Related

- juniper-cascor#224 — first cleanup of the gitleaks-action `Unexpected input(s) 'fail'` warning
- juniper-cascor#230 — `repository_dispatch` guard fix (separate issue, surfaced same evening as the override PRs)
- GitHub deprecation announcement: <https://github.blog/changelog/2025-09-19-deprecation-of-node-20-on-github-actions-runners/>
