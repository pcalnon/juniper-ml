"""Move my five CHANGELOG bullets to directly after the "A conflict notice..." bullet (the coordinator's insertion point). Scratch only."""

from pathlib import Path

PATH = Path("/home/pcalnon/Development/python/Juniper/worktrees/juniper-canopy--fix--registry-record-repairs--20260922-2021--26e0546f/CHANGELOG.md")
text = PATH.read_text(encoding="utf-8")

BLOCK_START = "- **Registry and test prose still described the dataset snap that the OQ-6 ratification deleted.**"
BLOCK_END = "`KNOWN_UPSTREAM_GENERATORS` was re-checked against juniper-data main and is unchanged at 16.\n"
ANCHOR = "  conflict; a genuine conflict still clears and still names the real dataset.\n"

assert text.count(BLOCK_START) == 1 and text.count(BLOCK_END) == 1 and text.count(ANCHOR) == 1
start = text.index(BLOCK_START)
end = text.index(BLOCK_END) + len(BLOCK_END)
block = text[start:end]
# Where the patch put it: after the F-CANOPY-053 bullet's blank line, followed by a blank line and [0.8.1].
assert text[start - 2 : start] == "\n\n", repr(text[start - 2 : start])
assert text[end : end + len("\n## [0.8.1]")] == "\n## [0.8.1]", repr(text[end : end + 20])
text = text[:start] + text[end + 1 :]  # drop the block and the blank line that followed it
assert "\n\n## [0.8.1]" in text and text.count(BLOCK_START) == 0

anchor_end = text.index(ANCHOR) + len(ANCHOR)
text = text[:anchor_end] + block + text[anchor_end:]
PATH.write_text(text, encoding="utf-8")

lines = text.splitlines()
first = next(i for i, line in enumerate(lines) if line.startswith(BLOCK_START))
print(f"block now starts at line {first + 1}; preceded by: {lines[first - 1][:70]!r}")
last = next(i for i, line in enumerate(lines) if "unchanged at 16." in line)
print(f"block ends at line {last + 1}; followed by: {lines[last + 1]!r} then {lines[last + 2][:60]!r}")
