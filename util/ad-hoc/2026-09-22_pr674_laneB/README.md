# juniper-cascor#674 — Lane B's evidence probes (verbatim, 2026-09-22)

**Project**: Juniper · **Sub-Project**: juniper-ml (ad-hoc) · **Application**: canopy E2E validation arc ·
**Author**: Paul Calnon · **License**: MIT License

These three scripts are the round-1 Lane B reviewer's own experiments against juniper-cascor PR #674
(F-CASCOR-004). They were copied out of the session scratchpad **unmodified**, because they are the
evidence for that review's findings, and editing them would make them something else. Each carries its
own docstring with arguments.

| script | what it established |
|---|---|
| `slow_consumer_probe.py` | a REAL slow reader over TCP loopback. On the PR head `7cfad9fc`: the false `ERROR … exception in shielded future` on Python 3.14, and on the sans-I/O stack a 1006 instead of 1011 |
| `flow_diag2.py` | how much unread backlog it takes to trip the 0.5 s send timeout (~9 MB of incompressible payload) |
| `oversize_parity.py` | the undisclosed behaviour change: on `main`, an oversized message holding a NumPy scalar was delivered in chunks, coerced by `default=str`; the PR refuses it |

Run them under the stack you mean to test. `PYTHONPATH` selects uvicorn/websockets. The pinned container
stack is uvicorn 0.53.0 + websockets 17.1 (`requirements-cpu.lock`); `JuniperCascor1` has 0.46 + 16.0.

The review's full report is in
`reports/e2e-canopy-2026-09-02/consensus/2026-09-22_validator_reports_round1b.md`. The fixes and the
round-2 re-measurement are in Phase 7 of `notes/JUNIPER_2026-08-09_JUNIPER-CANOPY_E2E-VALIDATION-EVIDENCE.md`.
