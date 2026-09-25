S = "/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/2fba4397-7d9b-4929-8ca2-375b8168e1c8/scratchpad/"
D = "/home/pcalnon/Development/python/Juniper/juniper-ml/.claude/worktrees/fizzy-hugging-dream/reports/2026-09-24_defect-register-round-42/data438-fixforward-pr-draft.md"
t = open(S + "data_fixforward_pr_title.txt", encoding="utf-8").read()
b = open(S + "data_fixforward_pr_body.md", encoding="utf-8").read()
d = open(D, encoding="utf-8").read()
cands = {"#+t+nn+b": "# " + t.rstrip("\n") + "\n\n" + b, "#+t+nn+b+nl": "# " + t.rstrip("\n") + "\n\n" + b.rstrip("\n") + "\n"}
print({k: v == d for k, v in cands.items()}, len(d))
print("title:", t.strip()[:220])
print("draft line1:", d.split("\n", 1)[0][:220])
