"""Strict keyword narrowing, as the categories and web-core runs used it. No I/O.

The core tools always stay, and so does any tool that has no keyword list. Any other offered tool stays only when
one of its keywords is a substring of the line. Both sides are normalized with Unicode NFKC plus casefold. There is
no fallback to the full list: the intent check gets MORE_TOOLS beside the narrowed list instead.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence

from tool_keywords import CORE_TOOLS, MORE_TOOLS_DESCRIPTION, TOOL_KEYWORDS

from cetimind.core.tools import ToolSpec

# Listed only in the intent check. Its name is not a real tool's.
MORE_TOOLS = ToolSpec(
    name="more_tools",
    description=MORE_TOOLS_DESCRIPTION,
    parameters={"type": "object", "properties": {}},
)


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
    """offered without the keyword tools the line does not match, in offered order."""
    hits = matched(line, keywords)
    keep = set(core) | hits
    return tuple(spec for spec in offered if spec.name in keep or not keywords.get(spec.name))
