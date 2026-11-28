"""Keyword narrowing of a typed turn's tool list. No I/O.

The core tools always stay. Any other offered tool stays only when one of its keywords is a substring of the line.
Both sides are normalized with Unicode NFKC plus casefold, so full-width and half-width forms, case, and scripts
without spaces all match the same way, and the matcher has no per-language code. When nothing beyond the core
tools matches, the full list comes back, so a line the keywords miss still gets every tool the mode has on.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence

from tool_keywords import CORE_TOOLS, TOOL_KEYWORDS

from cetimind.core.tools import ToolSpec


def norm(text: str) -> str:
    """NFKC, then casefold."""
    return unicodedata.normalize("NFKC", text).casefold()


def matched(line: str, keywords: Mapping[str, Sequence[str]] = TOOL_KEYWORDS) -> frozenset[str]:
    """The tool names with a keyword in the line."""
    text = norm(line)
    return frozenset(name for name, words in keywords.items() if any(norm(word) in text for word in words if word))


def narrow(
    line: str,
    offered: Sequence[ToolSpec],
    *,
    core: Sequence[str] = CORE_TOOLS,
    keywords: Mapping[str, Sequence[str]] = TOOL_KEYWORDS,
) -> tuple[ToolSpec, ...]:
    """offered without the non-core tools the line does not match, in offered order.

    Only drops tools, never adds one, so a tool the mode has off stays off. The full list comes back when no
    non-core tool matches.
    """
    hits = matched(line, keywords)
    keep = set(core) | hits
    if not any(spec.name in hits and spec.name not in core for spec in offered):
        return tuple(offered)
    return tuple(spec for spec in offered if spec.name in keep)
