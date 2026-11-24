#!/usr/bin/env python3
"""Round 4 lane F probe: read-only GitHub queries for the facts r4 changed.

Only `gh api` GET requests and GraphQL queries. Prints no environment value.
"""
import json
import subprocess


def gh(*args):
    p = subprocess.run(["gh", *args], capture_output=True, text=True)
    if p.returncode != 0:
        return {"__error__": p.stderr.strip()[:300]}
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return p.stdout


def commit(repo, sha):
    c = gh("api", f"repos/pcalnon/{repo}/commits/{sha}")
    if "__error__" in c:
        return c
    return {
        "sha": c["sha"],
        "parents": [x["sha"][:8] for x in c["parents"]],
        "author": (c["commit"]["author"]["name"], c["commit"]["author"]["date"]),
        "committer": (c["commit"]["committer"]["name"], c["commit"]["committer"]["date"]),
        "verified": c["commit"]["verification"]["verified"],
        "reason": c["commit"]["verification"]["reason"],
        "files": len(c.get("files", [])),
        "subject": c["commit"]["message"].splitlines()[0][:120],
    }


print("== data branch ref ==")
print(gh("api", "repos/pcalnon/juniper-data/git/ref/heads/fix/conditional-requests-round4-followups"))
print(gh("api", "repos/pcalnon/juniper-data/pulls?head=pcalnon:fix/conditional-requests-round4-followups&state=all"))
for s in ("d1c66a11", "94ce8b1f"):
    print(s, commit("juniper-data", s))

print("\n== cascor#689/#690, data#440, canopy#685 ==")
q = """query {
 a: repository(owner:"pcalnon", name:"juniper-cascor") {
  p690: pullRequest(number:690) { state mergedAt mergedBy { login } headRefOid headRefName mergeCommit { oid } autoMergeRequest { enabledAt }
    commits(first:20) { nodes { commit { oid committedDate messageHeadline parents(first:3){ nodes { oid } } signature { isValid } author { name } } } } }
  p689: pullRequest(number:689) { state mergedAt mergedBy { login } headRefOid headRefName mergeCommit { oid } }
 }
 c: repository(owner:"pcalnon", name:"juniper-data") {
  p440: pullRequest(number:440) { state mergedAt mergedBy { login } headRefOid headRefName mergeCommit { oid } }
 }
 b: repository(owner:"pcalnon", name:"juniper-canopy") {
  p685: pullRequest(number:685) { state mergedAt headRefOid mergeCommit { oid } }
 }
}"""
print(json.dumps(gh("api", "graphql", "-f", f"query={q}"), indent=1))

print("\n== #690 timeline: auto-merge and head events ==")
q2 = """query { repository(owner:"pcalnon", name:"juniper-cascor") { pullRequest(number:690) {
 timelineItems(last:40, itemTypes:[AUTO_MERGE_ENABLED_EVENT, AUTO_MERGE_DISABLED_EVENT, MERGED_EVENT, HEAD_REF_FORCE_PUSHED_EVENT, PULL_REQUEST_COMMIT, READY_FOR_REVIEW_EVENT, CONVERT_TO_DRAFT_EVENT, HEAD_REF_DELETED_EVENT]) {
  nodes { __typename
   ... on AutoMergeEnabledEvent { createdAt actor { login } }
   ... on AutoMergeDisabledEvent { createdAt actor { login } }
   ... on MergedEvent { createdAt actor { login } commit { oid } }
   ... on ReadyForReviewEvent { createdAt actor { login } }
   ... on ConvertToDraftEvent { createdAt actor { login } }
   ... on HeadRefDeletedEvent { createdAt actor { login } }
   ... on PullRequestCommit { commit { oid committedDate pushedDate } }
  } } } } }"""
print(json.dumps(gh("api", "graphql", "-f", f"query={q2}"), indent=1))

print("\n== commit 81154187 (cascor) ==")
print(commit("juniper-cascor", "81154187"))
for s in ("c4e002d2", "78e99414", "0fbb447a", "b9484fef"):
    print(s, commit("juniper-cascor", s))
print("data 26491531", commit("juniper-data", "26491531"))
