#!/usr/bin/env python3
"""Lane A: characterise the 2-byte difference between each report body and its agent's last message."""
import importlib.util
import sys
from pathlib import Path

S = Path("/tmp/claude-1000/-home-pcalnon-Development-python-Juniper-juniper-ml/8f86dec2-21ea-43f2-911a-bb2314a822ec/scratchpad/r42/pr2074-laneA")
spec = importlib.util.spec_from_file_location("rc", S / "reports_check.py")
src = (S / "reports_check.py").read_text().split("\nok = 0\n")[0]  # definitions only
rc = {}
exec(compile(src, "reports_check_defs", "exec"), rc)
R, SESS, ADDED, last_assistant_text = rc["R"], rc["SESS"], rc["ADDED"], rc["last_assistant_text"]

allok = True
for name in ADDED:
    raw = (R / name).read_bytes()
    text = raw.decode("utf-8")
    first, _, body = text.partition("\n")
    agent = first.split("subagent ", 1)[1].split(" ", 1)[0]
    sess = first.split("of session ", 1)[1].split(" ", 1)[0]
    last, _, _ = last_assistant_text(SESS[sess] / f"agent-{agent}.jsonl")
    lead = len(body) - len(body.lstrip("\n"))
    trail = len(body) - len(body.rstrip("\n"))
    core = body[lead:len(body) - trail] if trail else body[lead:]
    last_lead = len(last) - len(last.lstrip("\n"))
    last_trail = len(last) - len(last.rstrip("\n"))
    same_core = core == last.strip("\n") and last_lead == 0 and last_trail == 0
    shape = f"body = {lead}x'\\n' + message + {trail}x'\\n'" if same_core else "CONTENT DIFFERS"
    exact_framed = body == "\n" + last + "\n"
    allok &= exact_framed
    print(f"{name:45s} {shape}; body == '\\n' + last + '\\n': {exact_framed}; message ends with newline: {last.endswith(chr(10))}")
print("ALL framed-identical:", allok)
