"""Reply clean-up. The chat window shows plain text, and models like to write markdown."""
import re

_TABLE_SEPARATOR = re.compile(r"(?m)^[ \t]*\|?[ \t:|-]{3,}\|?[ \t]*$")
_TABLE_ROW = re.compile(r"(?m)^[ \t]*\|(.+)\|[ \t]*$")
_BOLD = re.compile(r"(\*\*|__)(.+?)\1", re.S)
_INLINE_CODE = re.compile(r"`([^`\n]*)`")
_HEADING = re.compile(r"(?m)^[ \t]{0,3}#{1,6}[ \t]+")
_BULLET = re.compile(r"(?m)^[ \t]*[*•][ \t]+")
_BLANK_RUNS = re.compile(r"\n{3,}")

# Typographic look-alikes that break copy-paste and searching: a SKU written with a
# non-breaking hyphen no longer matches the real SKU.
_LOOKALIKES = {"‑": "-", "‐": "-", " ": " ", " ": " "}


def to_plain_text(text: str) -> str:
    for bad, good in _LOOKALIKES.items():
        text = text.replace(bad, good)
    text = _TABLE_SEPARATOR.sub("", text)
    text = _TABLE_ROW.sub(lambda m: " | ".join(cell.strip() for cell in m.group(1).split("|")), text)
    text = _BOLD.sub(r"\2", text)
    text = _INLINE_CODE.sub(r"\1", text)
    text = _HEADING.sub("", text)
    text = _BULLET.sub("- ", text)
    return _BLANK_RUNS.sub("\n\n", text).strip()
