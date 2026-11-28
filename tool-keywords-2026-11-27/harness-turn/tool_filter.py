"""Keyword narrowing of a typed turn's tool list (#154). No I/O.

The core tools always stay, and so does any tool that has no keyword list, such as a module tool that brought
none. Any other offered tool stays only when one of its keywords is a substring of the line. Both sides are
normalized with Unicode NFKC plus casefold, so full-width and half-width forms, case, and scripts without spaces all
match the same way, and the matcher has no per-language code.

There is no fallback to the full list when nothing matches: the 2026-11-27 bench showed that fallback hands most
lines the full list. Instead the intent check gets MORE_TOOLS beside the narrowed list, and picking it reruns the
check on the full list.
"""

from __future__ import annotations

import unicodedata
from collections.abc import Mapping, Sequence

from cetimind.core.instructions import CORE_TOOLS, MORE_TOOLS_DESCRIPTION, TOOL_KEYWORDS
from cetimind.core.tools import ToolSpec

# Listed only in the intent check, never in a tool round. Its name is not a real tool's.
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
    """offered without the keyword tools the line does not match, in offered order.

    A core tool, or a tool with no keyword list, always stays. Only drops tools, never adds one, so a tool the
    mode has off stays off.
    """
    hits = matched(line, keywords)
    keep = set(core) | hits
    return tuple(spec for spec in offered if spec.name in keep or not keywords.get(spec.name))
