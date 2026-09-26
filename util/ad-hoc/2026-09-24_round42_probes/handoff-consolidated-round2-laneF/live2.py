import subprocess, json, sys
def gh(args):
    r = subprocess.run(["gh"] + args, capture_output=True, text=True)
    return r.stdout.strip() + (("\nERR:" + r.stderr.strip()) if r.returncode else "")
# post-merge CI runs on main for merge commits
for repo, sha in [("juniper-cascor", "b9484fef98430a6b0c833c5a158cb94f4a132912"),
                  ("juniper-cascor", "0fbb447a1455ca19ef042a5f925b306ab2d3e3e2"),
                  ("juniper-data", "264915319cd32632d362e7ce5f401028658c75f1"),
                  ("juniper-ml", "5af9d7229505f5ef3bf07cbca1dd4f1e12720371"),
                  ("juniper-canopy", "dc5ea02e8aac81a009cb30e35633ce8b43d972c8")]:
    print("--- runs", repo, sha[:8])
    out = gh(["api", f"repos/pcalnon/{repo}/actions/runs?head_sha={sha}&per_page=50",
              "--jq", '.workflow_runs[] | [.name, .event, .status, (.conclusion // "-"), .created_at, .updated_at] | @tsv'])
    print(out)
print("--- checks 2097")
print(gh(["pr", "checks", "2097", "--repo", "pcalnon/juniper-ml"]))
print("--- checks 2089")
print(gh(["pr", "checks", "2089", "--repo", "pcalnon/juniper-ml"]))
print("--- 690 commits")
print(gh(["api", "repos/pcalnon/juniper-cascor/pulls/690/commits", "--jq", '.[] | [.sha[0:8], .commit.author.date, .commit.committer.date, .commit.verification.verified, (.commit.message|split("\n")[0]), (.parents|map(.sha[0:8])|join(","))] | @tsv']))
print("--- 689 commits")
print(gh(["api", "repos/pcalnon/juniper-cascor/pulls/689/commits", "--jq", '.[] | [.sha[0:8], .commit.committer.date, .commit.verification.verified, (.commit.message|split("\n")[0])] | @tsv']))
print("--- 440 commits")
print(gh(["api", "repos/pcalnon/juniper-data/pulls/440/commits", "--jq", '.[] | [.sha[0:8], .commit.committer.date, .commit.verification.verified, (.commit.message|split("\n")[0])] | @tsv']))
print("--- 94ce8b1f commit")
print(gh(["api", "repos/pcalnon/juniper-data/commits/94ce8b1fa8e229c92e8674a1074d518e59142488", "--jq", '[.sha, .commit.committer.date, .commit.author.date, .commit.verification.verified, .commit.verification.reason, (.parents|map(.sha)|join(",")), (.files|length)] | @tsv']))
print("--- d1c66a11 parent")
print(gh(["api", "repos/pcalnon/juniper-data/commits/d1c66a11", "--jq", '[.sha, (.parents|map(.sha)|join(",")), .commit.verification.verified, (.commit.message|split("\n")[0])] | @tsv']))
print("--- repo squash settings")
for repo in ["juniper-data", "juniper-cascor", "juniper-canopy", "juniper-ml"]:
    print(repo, gh(["api", f"repos/pcalnon/{repo}", "--jq", '[.squash_merge_commit_title, .squash_merge_commit_message] | @tsv']))
