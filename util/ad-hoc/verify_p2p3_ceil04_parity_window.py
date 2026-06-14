#!/usr/bin/env python3
"""
Ad-hoc adversarial-verification scratch for finding P2P3-CEIL-04.

Question under test: the finding claims the C2/mod-2 (parity) ceiling-break
"survives deployment" under stateless-per-window (h0=0, no carry-across-windows)
because period-2 needs "only depth-1 state" and is below the D<=30 cap, WHEREAS
the LMU horizon is truncated by the same reset. The finding asserts an ASYMMETRY.

This scratch makes concrete the distinction the finding elides:
  (A) PERIOD of a counter / cycle length   -> bounded by unroll depth (<=window)
  (B) HISTORY HORIZON (how far back the function depends) -> also bounded by the
      stateless-per-window reset, for ANY stateful computation, INCLUDING parity.

Parity (C2) of an UNBOUNDED stream is a function of ALL prior symbols. A depth-1
state bit suffices ONLY IF that bit is carried across every step of the stream.
Stateless-per-window forces the bit to 0 at each window boundary, so the deployed
C2 neuron computes parity-of-the-current-window (<=30 symbols), NOT parity-of-stream
-- exactly the same kind of horizon truncation the finding (correctly) ascribes to
the LMU. The asymmetry is therefore not between "period vs horizon" but is COMMON
to both arms: the reset truncates the *history horizon* of both.

No torch / no cascor import (C1 transparency; pure stdlib).
"""

def true_stream_parity(bits):
    """Parity accumulated across the WHOLE stream (depth-1 state, carried)."""
    s = 0
    for b in bits:
        s ^= b
    return s


def windowed_stateless_parity(bits, window):
    """Parity as a STATELESS-PER-WINDOW machine sees it: state resets to 0 at
    each window boundary, so each window's output is parity of THAT window only.
    Returns the per-window outputs (what the deployed C2 neuron would emit)."""
    outs = []
    for start in range(0, len(bits), window):
        chunk = bits[start:start + window]
        s = 0  # h0 = 0, no carry-across-windows
        for b in chunk:
            s ^= b
        outs.append(s)
    return outs


def deployed_can_recover_stream_parity(bits, window):
    """Can the stateless-per-window machine recover the WHOLE-STREAM parity?
    Only if there is exactly one window covering the whole stream (len<=window),
    OR if the downstream were allowed to XOR the per-window outputs -- but that
    XOR-across-windows is itself cross-window state, which is forbidden."""
    return len(bits) <= window


if __name__ == "__main__":
    import random
    random.seed(0)

    print("=== P2P3-CEIL-04 parity-vs-window check ===\n")

    # A stream longer than the window.
    window = 8  # stand-in for the <=30 deployed window
    for n in (8, 9, 20, 64):
        bits = [random.randint(0, 1) for _ in range(n)]
        stream_par = true_stream_parity(bits)
        win_outs = windowed_stateless_parity(bits, window)
        # The deployed machine's "final" output is the LAST window's parity.
        deployed_final = win_outs[-1]
        recoverable = deployed_can_recover_stream_parity(bits, window)
        agree = (deployed_final == stream_par)
        print(f"len={n:3d} window={window}: "
              f"stream_parity={stream_par}  "
              f"per_window_outs={win_outs}  "
              f"deployed_final={deployed_final}  "
              f"recoverable_within_one_window={recoverable}  "
              f"deployed==stream? {agree}")

    print("\nInterpretation:")
    print("- For n <= window the stateless machine sees the whole stream in ONE")
    print("  window, so deployed parity == stream parity (the break 'survives').")
    print("- For n  > window the state RESETS mid-stream; the deployed machine")
    print("  can only report parity-of-the-last-window, NOT stream parity, and")
    print("  cannot recover it without XOR-ing across windows (= cross-window")
    print("  state, which stateless-per-window forbids). The 'depth-1 state'")
    print("  argument is necessary but NOT sufficient for 'survives deployment'.")
    print("- This is the SAME history-horizon truncation the finding (correctly)")
    print("  ascribes to the LMU arm. So the claimed ASYMMETRY (window bounds LMU")
    print("  horizon but NOT the C2 break) does not hold for streams > window:")
    print("  BOTH arms are horizon-truncated to <=window by the reset.")
    print("- The finding is right only in the narrow sense that the *period* (2)")
    print("  is below the cap; it conflates 'period <= window' with 'stream-")
    print("  history available', which is the load-bearing error.")
