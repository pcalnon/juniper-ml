"""Scratch analyzer (agent-s): summarize a ws_repeat_plugin log.

Usage: python3 analyze_seq.py <log.jsonl> [--show N]

Reports per-test outcome counts, and for every recorded WS session whether a
`state` frame was read before `initial_status` (the CI failure shape). When the
log was produced with --wsr-drain, also reports the FULL wire sequence (frames
the test read, then frames drained at session close) for those sessions, and
checks that both connect-time unicasts (initial_status, and a state after it)
still arrived -- i.e. whether anything was dropped or only reordered.
"""

import collections
import json
import sys


def main():
    path = sys.argv[1]
    show = 0
    if "--show" in sys.argv:
        show = int(sys.argv[sys.argv.index("--show") + 1])
    outcomes = collections.Counter()
    seqs = collections.OrderedDict()
    posts = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            rec = json.loads(line)
            if "outcome" in rec:
                outcomes[rec["outcome"]] += 1
                continue
            key = (rec["node"], rec["sid"])
            if "post" in rec:
                posts[key] = rec["post"]
                continue
            seqs.setdefault(key, []).append(rec["type"])
    print(f"test call outcomes: {dict(outcomes)}")
    print(f"ws sessions recorded: {len(seqs)}")
    shapes = collections.Counter()
    state_before_initial = []
    for key, seq in seqs.items():
        shapes[" > ".join(seq)] += 1
        # '*' suffix = broadcast-tagged frame (post-fix runs); treat 'state*' as a state here,
        # because the question is whether ANY state frame beat initial_status onto the wire.
        plain = [t.rstrip("*") if isinstance(t, str) else t for t in seq]
        if "state" in plain:
            first_state = plain.index("state")
            if "initial_status" not in plain[:first_state]:
                state_before_initial.append((key, seq))
    print(f"sessions where a `state` was read before `initial_status`: {len(state_before_initial)}")
    print("sequence shapes (as read by the test helper):")
    for shape, n in shapes.most_common():
        print(f"  {n:6d}  {shape}")
    if posts:
        full_shapes = collections.Counter()
        intact = 0
        for key, seq in state_before_initial:
            full = seq + posts.get(key, [])
            # Normalise the tail: keep up to the first `state` after `initial_status`.
            if "initial_status" in full:
                i = full.index("initial_status")
                tail = full[i + 1 :]
                if "state" in tail:
                    intact += 1
                    full = full[: i + 1 + tail.index("state") + 1]
            full_shapes[" > ".join(full)] += 1
        print(f"of those, sessions whose initial_status AND a later state both still arrived: {intact}/{len(state_before_initial)}")
        print("full wire shapes for those sessions (truncated at the first state after initial_status):")
        for shape, n in full_shapes.most_common():
            print(f"  {n:6d}  {shape}")
    for key, seq in state_before_initial[:show]:
        print(f"  EXAMPLE {key}: read={seq} drained={posts.get(key)}")


if __name__ == "__main__":
    main()
