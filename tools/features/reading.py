"""Word count and reading-time estimates for Chinese lesson text."""

from __future__ import annotations

import re

CJK_RE = re.compile(r"[一-鿿]")


def count_cjk(text: str) -> int:
    return len(CJK_RE.findall(text))


def reading_minutes(text: str, chars_per_minute: int = 300) -> int:
    return max(1, round(count_cjk(text) / chars_per_minute))
