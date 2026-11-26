"""Tables from a prompt-order run: uv run python bench/prompt_order/summarize.py DIR [DIR ...]"""

from __future__ import annotations

import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path


def load(dirs: list[str], name: str) -> list[dict]:
    rows = []
    for folder in dirs:
        with (Path(folder) / name).open(encoding="utf-8") as handle:
            rows.extend(json.loads(line) for line in handle if line.strip())
    return rows


def pct(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(q * len(ordered)) - 1))
    return ordered[index]


def wilson(hits: int, total: int) -> str:
    if total == 0:
        return "-"
    z = 1.96
    p = hits / total
    centre = (p + z * z / (2 * total)) / (1 + z * z / total)
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return f"{hits}/{total} ({100 * p:.0f}%, {100 * max(0, centre - half):.0f}–{100 * min(1, centre + half):.0f})"


def count(rows: list[dict], key: str, where=lambda r: True) -> str:
    picked = [r for r in rows if where(r) and r.get(key) is not None]
    return wilson(sum(bool(r[key]) for r in picked), len(picked))


def mcnemar(turns: list[dict], key: str, other: str = "B") -> str:
    """Exact two-sided McNemar on paired (case, repeat) results, A against other."""
    by = defaultdict(dict)
    for r in turns:
        if r.get(key) is not None and "error" not in r:
            by[(r["case"], r["repeat"])][r["arm"]] = bool(r[key])
    a_only = sum(1 for v in by.values() if v.get("A") is True and v.get(other) is False)
    b_only = sum(1 for v in by.values() if v.get("A") is False and v.get(other) is True)
    n = a_only + b_only
    if n == 0:
        return "A-only 0, B-only 0, p = 1"
    k = min(a_only, b_only)
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n)
    return f"A-only {a_only}, B-only {b_only}, p = {p:.3f}"


def main() -> None:
    dirs = sys.argv[1:]
    turns = load(dirs, "turns.jsonl")
    steps = load(dirs, "steps.jsonl")
    arms = sorted({r["arm"] for r in turns})
    langs = sorted({r["lang"] for r in turns})
    tool = lambda r: r["need"] in ("any", "all")  # noqa: E731
    plain = lambda r: r["need"] == "none"  # noqa: E731

    print("## Accuracy\n")
    print("| Metric | " + " | ".join(arms) + " |")
    print("| --- |" + " --- |" * len(arms))
    metrics = [
        ("Errors", lambda rs: str(sum("error" in r for r in rs))),
        ("Right tools, in the turn", lambda rs: count(rs, "ok")),
        ("Right tools, after the miss check", lambda rs: count(rs, "ok_final")),
        ("Needed tool called (tool lines)", lambda rs: count(rs, "needed_called")),
        ("Stray tool call", lambda rs: wilson(sum(bool(r.get("stray")) for r in rs), len(rs))),
        ("False claim (tool line, no tool, claims done)", lambda rs: count(rs, "false_claim", tool)),
        ("Grounded in the tool result", lambda rs: count(rs, "grounded")),
        ("No-tool line got a late tool + follow-up",
         lambda rs: wilson(sum(bool(r.get("net_tools")) for r in rs if plain(r)), sum(plain(r) for r in rs))),
        ("Injection followed", lambda rs: count(rs, "injected")),
        ("Reply repeats the hold", lambda rs: count(rs, "repeats_hold", lambda r: bool(r.get("hold")))),
        ("Hold spoken (tool lines)", lambda rs: wilson(sum(bool(r.get("hold")) for r in rs if tool(r)),
                                                        sum(tool(r) for r in rs))),
        ("Question on a tool turn", lambda rs: count(rs, "question", tool)),
        ("Emoji", lambda rs: count(rs, "emoji")),
        ("Sound tag", lambda rs: count(rs, "sound_tag")),
        ("Tool name or JSON in the reply", lambda rs: count(rs, "leak")),
    ]
    for lang in [None, *langs]:
        subset = [r for r in turns if lang is None or r["lang"] == lang]
        if lang is not None and len(langs) == 1:
            continue
        if lang is not None:
            print(f"| **{lang.upper()}** |" + " |" * len(arms))
        for label, fn in metrics:
            print(f"| {label} | " + " | ".join(fn([r for r in subset if r["arm"] == a]) for a in arms) + " |")
    print()
    for other in [a for a in arms if a != "A"]:
        print(f"Paired, A vs {other} (exact McNemar; A-only = A right, {other} wrong):")
        for key in ("ok", "ok_final", "false_claim"):
            print(f"- {key}: {mcnemar(turns, key, other).replace('B-only', other + '-only')}")
    print()

    print("## Time per turn (ms, median / p90)\n")
    print("| Measure | Lines | " + " | ".join(arms) + " |")
    print("| --- | --- |" + " --- |" * len(arms))
    for key in ("first_line_ms", "reply_ms", "done_ms"):
        for label, where in (("all", lambda r: True), ("tool", tool), ("no tool", plain)):
            cells = []
            for a in arms:
                vals = [r[key] for r in turns if r["arm"] == a and where(r) and key in r and "error" not in r]
                cells.append(f"{statistics.median(vals):.0f} / {pct(vals, 0.9):.0f}" if vals else "-")
            print(f"| {key} | {label} | " + " | ".join(cells) + " |")
    for key in ("calls", "prompt_tokens", "completion_tokens", "reasoning_tokens"):
        cells = []
        for a in arms:
            vals = [r[key] for r in turns if r["arm"] == a and "error" not in r]
            cells.append(f"{statistics.mean(vals):.1f}" if vals else "-")
        print(f"| {key} (mean) | all | " + " | ".join(cells) + " |")
    print()

    print("## Time per step (ms)\n")
    print("| Arm | Phase | Step | Calls | Median | p90 | Mean prompt tok | Mean reasoning tok |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- |")
    groups = defaultdict(list)
    for s in steps:
        groups[(s["arm"], s["phase"], s["step"])].append(s)
    for (arm, phase, step), rows in sorted(groups.items()):
        ms = [r["ms"] for r in rows]
        ptok = [r["prompt_tokens"] or 0 for r in rows]
        rtok = [r["reasoning_tokens"] or 0 for r in rows]
        print(f"| {arm} | {phase} | {step} | {len(rows)} | {statistics.median(ms):.0f} | {pct(ms, 0.9):.0f} | "
              f"{statistics.mean(ptok):.0f} | {statistics.mean(rtok):.0f} |")
    print()
    print("## Time per turn share by step (mean ms per turn)\n")
    for arm in arms:
        n_turns = sum(1 for r in turns if r["arm"] == arm)
        share = defaultdict(float)
        for s in steps:
            if s["arm"] == arm:
                share[f"{s['phase']}:{s['step']}"] += s["ms"]
        parts = ", ".join(f"{k} {v / n_turns:.0f}" for k, v in sorted(share.items(), key=lambda kv: -kv[1]))
        print(f"- {arm}: {parts}")


if __name__ == "__main__":
    main()
