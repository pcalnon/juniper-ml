"""
One-shot check of turing's Wi-Fi link before a large API upload: current radio, SNR, gateway loss, and a timed 1.33 MB single-flow upload.

Project: juniper-ml
Sub-Project: ad-hoc tooling
Author: Paul Calnon (authored via Claude Code)
Created: 2026-10-18
Status: ad-hoc — investigation (the link gate run before each turing bring-up Session 1 landing)
Retire when: RETAINED — ad-hoc scripts are kept as provenance of record (owner policy 2026-08-25)
Related: util/ad-hoc/2026-10-17_turing_network_probe.bash (the full read-only probe);
         notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md (§2.2)

Why: GitHub's GraphQL frontend drops a createCommitOnBranch request that runs past about 7-10 s, and
docs/REFERENCE.md goes up as a 1.33 MB base64 body. On turing's weak 2.4 GHz radio that upload took about 9 s
and failed with HTTP 499; on a 5 GHz radio it takes 1-2 s. The gate: SNR >= 20 dB with clean pings, or the
timed upload finishes in under 5 s. On 2026-10-18/19 turing sat on 5 GHz ch 149 at SNR 9-12 dB, yet every
upload took 1.2-2.1 s with 0% gateway loss, and every REFERENCE.md push landed on attempt 1, so the upload
time is the better predictor.

The upload body is random bytes (`head -c 1361920 /dev/urandom > FILE`), posted to Cloudflare's speed-test
endpoint, so no repository content leaves the host. The gateway address is turing's (192.168.50.1).

Usage:
    python3 -I util/ad-hoc/2026-10-18_turing_link_gate.py [--upload RANDOM_1330K_FILE]
"""
import re
import subprocess
import sys
import time

t = subprocess.run(["system_profiler", "SPAirPortDataType"], capture_output=True, text=True).stdout
if "Current Network Information:" not in t:
    print("wifi: not associated")
else:
    b = t.split("Current Network Information:", 1)[1].split("Other Local Wi-Fi Networks:", 1)[0]
    ch = re.search(r"Channel: (\S+) \((\S+?),", b)
    sn = re.search(r"Signal / Noise: (-?\d+) dBm / (-?\d+) dBm", b)
    phy = re.search(r"PHY Mode: (\S+)", b)
    rate = re.search(r"Transmit Rate: (\d+)", b)
    snr = int(sn.group(1)) - int(sn.group(2)) if sn else None
    print(f"wifi: {ch.group(2) if ch else '?'} ch {ch.group(1) if ch else '?'}, signal {sn.group(1) if sn else '?'} dBm, SNR {snr} dB, PHY {phy.group(1) if phy else '?'}, tx rate {rate.group(1) if rate else '?'} Mbps")

p = subprocess.run(["ping", "-c", "20", "-i", "0.2", "-q", "192.168.50.1"], capture_output=True, text=True).stdout
m = re.search(r"([\d.]+)% packet loss", p)
r = re.search(r"= [\d.]+/([\d.]+)/([\d.]+)/", p)
print(f"gateway: loss {m.group(1) if m else '?'}%, avg rtt {r.group(1) if r else '?'} ms, max {r.group(2) if r else '?'} ms")

if "--upload" in sys.argv:
    blob = sys.argv[sys.argv.index("--upload") + 1]
    t0 = time.monotonic()
    u = subprocess.run(
        ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code} %{size_upload} %{time_total}", "--max-time", "60", "-X", "POST", "--data-binary", "@" + blob, "https://speed.cloudflare.com/__up"],
        capture_output=True,
        text=True,
    )
    print(f"upload: {u.stdout.strip() or u.stderr.strip()} (wall {time.monotonic() - t0:.2f} s)")
