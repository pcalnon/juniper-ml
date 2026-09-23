"""Scratch waiter (agent-s): block until a file contains a marker string, or a timeout passes.

Usage: python3 wait_for_text.py <file> <marker> <timeout_seconds>
Prints the last 1500 bytes of the file when done. Exit 0 = marker seen, 3 = timed out.
"""

import sys
import time


def main():
    path, marker, timeout = sys.argv[1], sys.argv[2], float(sys.argv[3])
    deadline = time.monotonic() + timeout
    seen = False
    while time.monotonic() < deadline:
        try:
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        except FileNotFoundError:
            text = ""
        if marker in text:
            seen = True
            break
        time.sleep(5)
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    print(text[-1500:])
    print(f"\n[wait_for_text] marker {'SEEN' if seen else 'NOT seen (timeout)'}: {marker!r}")
    sys.exit(0 if seen else 3)


if __name__ == "__main__":
    main()
