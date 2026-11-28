"""Line-level paired comparisons from calls.jsonl files. No model, no CetiMind imports.

A line counts as right for a variant when most of its repeats were right. Each pair of variants gets the lines only
the first got right, the lines only the second got right, and the exact two-sided McNemar p on those counts. It also
prints how many checks picked `more_tools`.

    python harness/paired_lines.py run-expand/tools-66/calls.jsonl [more calls.jsonl ...]
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from math import comb

PAIRS = (
    ("narrow_live", "full_live"),
    ("strict_live", "full_live"),
    ("expand_live", "full_live"),
    ("expand_live", "strict_live"),
)


def mcnemar_p(a_only: int, b_only: int) -> float:
    """Exact two-sided McNemar p."""
    n = a_only + b_only
    if n == 0:
        return 1.0
    k = min(a_only, b_only)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2**n)


def line_results(rows: list[dict]) -> dict[str, dict[str, bool]]:
    """variant -> line id -> right on most repeats."""
    seen: dict[str, dict[str, list[bool]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if not row["failed"]:
            seen[row["variant"]][row["id"]].append(row["right"])
    return {v: {i: sum(x) * 2 > len(x) for i, x in lines.items()} for v, lines in seen.items()}


def compare(path: str) -> None:
    with open(path, encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle]
    results = line_results(rows)
    expanded = sum(1 for r in rows if r.get("expanded"))
    checks = sum(1 for r in rows if r["variant"] == "expand_live")
    print(f"{path}: more_tools picked {expanded} of {checks} expand checks")
    for a, b in PAIRS:
        if a not in results or b not in results:
            continue
        a_only = sorted(i for i in results[a] if results[a][i] and not results[b][i])
        b_only = sorted(i for i in results[a] if results[b][i] and not results[a][i])
        p = mcnemar_p(len(a_only), len(b_only))
        print(f"  {a} vs {b}: {len(a_only)} / {len(b_only)}, p {p:.3f}; first only {a_only}; second only {b_only}")


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        compare(arg)
