import subprocess, json, sys
def gh(args):
    r = subprocess.run(["gh"] + args, capture_output=True, text=True)
    return r.stdout.strip() + (("\nERR:" + r.stderr.strip()) if r.returncode else "")
q = '''query {
 a: repository(owner:"pcalnon", name:"juniper-cascor") {
  p690: pullRequest(number:690) { state isDraft mergeStateStatus headRefOid mergedAt mergedBy{login} autoMergeRequest { enabledAt enabledBy{login} } mergeCommit { oid } baseRefName headRefName }
  p689: pullRequest(number:689) { state isDraft mergeStateStatus headRefOid mergedAt mergedBy{login} autoMergeRequest { enabledAt } mergeCommit { oid } headRefName }
  p688: pullRequest(number:688) { state headRefOid mergedAt mergeCommit { oid } }
  p686: pullRequest(number:686) { state headRefOid closedAt }
 }
 b: repository(owner:"pcalnon", name:"juniper-canopy") {
  p685: pullRequest(number:685) { state headRefOid mergedAt mergeCommit { oid } }
  p683: pullRequest(number:683) { state headRefOid mergedAt mergeCommit { oid } }
 }
 c: repository(owner:"pcalnon", name:"juniper-data") {
  p440: pullRequest(number:440) { state isDraft mergeStateStatus headRefOid mergedAt mergedBy{login} autoMergeRequest { enabledAt } mergeCommit { oid } headRefName }
  p438: pullRequest(number:438) { state headRefOid mergedAt mergeCommit { oid } }
 }
 d: repository(owner:"pcalnon", name:"juniper-ml") {
  p2089: pullRequest(number:2089) { state isDraft mergeStateStatus headRefOid autoMergeRequest { enabledAt } headRefName }
  p2097: pullRequest(number:2097) { state isDraft mergeStateStatus headRefOid autoMergeRequest { enabledAt } headRefName }
  p2096: pullRequest(number:2096) { state isDraft mergeStateStatus headRefOid createdAt mergedAt autoMergeRequest { enabledAt enabledBy{login} } mergeCommit { oid } headRefName title }
  p2088: pullRequest(number:2088) { state mergedAt mergeCommit { oid } }
  p2081: pullRequest(number:2081) { state mergedAt mergeCommit { oid } }
  p2086: pullRequest(number:2086) { state mergedAt mergeCommit { oid } }
  p2072: pullRequest(number:2072) { state mergedAt mergeCommit { oid } }
  p2077: pullRequest(number:2077) { state mergedAt mergeCommit { oid } }
  p2098: pullRequest(number:2098) { state mergedAt mergeCommit { oid } }
  p2090: pullRequest(number:2090) { state mergedAt mergeCommit { oid } }
 }
}'''
print(gh(["api", "graphql", "-f", "query=" + q]))
print("---consolidation PR")
print(gh(["pr", "list", "--repo", "pcalnon/juniper-ml", "--head", "docs/handoff-round42-consolidated", "--state", "all", "--json", "number,state,mergeCommit"]))
print("---data branch ref")
print(gh(["api", "repos/pcalnon/juniper-data/git/ref/heads/fix/conditional-requests-round4-followups", "--jq", ".object.sha"]))
print("---data branch PRs")
print(gh(["pr", "list", "--repo", "pcalnon/juniper-data", "--head", "fix/conditional-requests-round4-followups", "--state", "all"]))
for repo in ["juniper-data", "juniper-cascor", "juniper-canopy", "juniper-ml"]:
    print("---open PRs", repo)
    print(gh(["pr", "list", "--repo", "pcalnon/" + repo, "--state", "open", "--json", "number,title,headRefName,headRefOid,createdAt,autoMergeRequest"]))
