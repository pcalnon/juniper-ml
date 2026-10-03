# HANDOFF 2026-10-03 — k8s primer (CONSOLIDATED): CLOSED in juniper-ml; the work continues in the private `juniper-k8s` repo

**Consolidated source**: `prompts/thread-handoff_automated-prompts/HANDOFF_2026-09-24_k8s-primer-end-to-end-secure-automated-juniper-cluster.md`. That handoff says it is **UNVALIDATED**.
**Supersedes**: that same file.
**Live probe**: 2026-10-03, by `gh pr view` and `gh api` against `pcalnon/juniper-ml` and `pcalnon/juniper-k8s`.

## Goal statement (paste as the new thread's first prompt)

```text
No juniper-ml work remains on the Kubernetes primer path. Do not reopen it here.

Completed:
- The primer was written, consensus-validated and merged: juniper-ml#2101 (branch docs/k8s-primer),
  merged 2026-09-25 02:17Z as b82d12d7, file notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_KUBERNETES-PRIMER.md.
  Per its PR body, three validators (Kubernetes/OS/hardware, networking/storage/monitoring, Juniper
  grounding) ran four rounds; round 4 found 0 defects.
- Its handoff PR, juniper-ml#2098 (docs/k8s-primer-handoff), merged 2026-09-25 01:47Z.
- The owner then deleted the primer from juniper-ml: juniper-ml#2104, merged 2026-09-26 10:20Z as
  4b5227e3. Its commit message: "move all Juniper K8S code, documentation, and resources to a
  dedicated, private git repo: juniper-k8s".
- pcalnon/juniper-k8s (PRIVATE) holds notes/JUNIPER_2026-09-24_JUNIPER-ECOSYSTEM_KUBERNETES-PRIMER.md
  plus inventory/, raspi/ and util/. Its last push was 2026-10-01 (PR #7, longhorn and kubelet installs).

Remaining work: none in juniper-ml. Any Kubernetes work happens in juniper-k8s under its own
AGENTS.md. The parent Juniper/CLAUDE.md does not list juniper-k8s yet. Adding it is an owner
decision, and that file is unversioned.
```

All state above: `[VERIFIED 2026-10-03: gh pr view 2098/2101/2104; gh api repos/pcalnon/juniper-k8s]`.

## Dependencies on other paths

None in juniper-ml. A cluster deployment would consume P4's published images and wheels (release and distribution). That dependency now lives in juniper-k8s.

## Context the remaining work needs

The source handoff's "Leads to verify" were hardware and currency hypotheses: the Pi 5 has 4 cores, not 8; no Intel MacBook Pro has 12 physical cores; macOS cannot run a kubelet; ingress-nginx is retired; Promtail is EOL. `[UNVERIFIED — from HANDOFF_2026-09-24_k8s-primer-end-to-end-secure-automated-juniper-cluster.md, which was not validated]`. The validated primer in juniper-k8s is now the reference, not this list.

## Verification commands

```bash
gh pr view 2104 -R pcalnon/juniper-ml --json state,mergeCommit
gh api repos/pcalnon/juniper-k8s/contents/notes --jq '.[].name'
git ls-tree origin/main notes/ | grep -ci kubernetes   # expect 0
```

## Dispositioned / closed items

| Item | Source | Disposition | Evidence |
|---|---|---|---|
| 1–7: worktree, grounding, hardware probe, currency checks, draft, consensus, PR + merge | k8s handoff, "Remaining work" | Done | juniper-ml#2101, merged as `b82d12d7` |
| Handoff PR `docs/k8s-primer-handoff` not merged | k8s handoff, "Git state" | Merged | juniper-ml#2098 |
| Primer location | — | Moved to `juniper-k8s` by the owner | juniper-ml#2104, `4b5227e3` |

## Git state

- juniper-ml `origin/main` is `afb02801`. It holds no primer. `[VERIFIED 2026-10-03: git log]`
- The originating worktree is `zany-juggling-goblet`. Its branches `docs/k8s-primer` and `docs/k8s-primer-handoff` were merged. Remote branch cleanup was not probed.
