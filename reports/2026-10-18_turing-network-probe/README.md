# turing network probe outputs (2026-10-18/19)

These are the outputs of the read-only probe `util/ad-hoc/2026-10-17_turing_network_probe.bash --no-load`. They are the
evidence for erratum E-NET in `notes/JUNIPER_2026-10-15_JUNIPER-ML_TURING-HOST-BRINGUP-DEVELOPMENT-PLAN.md` §16.3: the
HTTP 499s on large `createCommitOnBranch` uploads from turing come from its Wi-Fi link, not ExpressVPN.

| File | When (UTC) | Radio | Gateway loss | Notes |
|---|---|---|---|---|
| `2026-10-18T0152Z_before-wifi-toggle.txt` | 2026-10-18 01:52 | not shown | 26.7% | That version of the probe crashed in its Wi-Fi section (a quoting bug in an f-string, since fixed). The radio was 2.4 GHz ch 3, per the session's other readings. |
| `2026-10-18T0813Z_ch3-after-wifi-toggle.txt` | 2026-10-18 08:13 | 2.4 GHz ch 3, −72 dBm, SNR 8 dB | 6.7% | After an agent-run Wi-Fi power cycle (owner-approved), macOS re-joined the same weak radio. 1.1.1.1 lost 33%. |
| `2026-10-19T0130Z_5ghz-ch149.txt` | 2026-10-19 01:30 | 5 GHz ch 149, −81 dBm, SNR 11 dB | 42% | Uploads on this radio still took 1.2-2.2 s (`util/ad-hoc/2026-10-18_turing_link_gate.py`). `en0` had moved to `.180` (DHCP). |

The 2026-10-19 output shows a radio with the owner's network name and `Security: None` on 2.4 GHz ch 10, flagged to the
owner. The earlier probe version did not print security. The probe prints no network names and no hardware addresses. The addresses shown are private LAN, link-local and VPN-tunnel
addresses.
