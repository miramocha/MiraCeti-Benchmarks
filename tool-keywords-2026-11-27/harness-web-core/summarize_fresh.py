"""Tables for the fresh held-out run: python summarize_fresh.py <tool-keywords folder>. Writes run-fresh/summary.json.

A line counts as right for a variant when most of its repeats were right, as in the rest of the write-up.
"""

import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

S = Path(sys.argv[1])
OUT = S / "run-fresh"
SIZES = {16: "run-fresh/tools-16", 36: "run-fresh/tools-36", 66: "run-fresh/tools-66"}
VARIANTS = {"full_live": "Full", "expand_live": "Expand", "webexp_live": "Web core + expand"}


def mcnemar(a: int, b: int) -> float:
    n, k = a + b, min(a, b)
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n)


def majority(values: list[bool]) -> bool:
    return sum(values) * 2 > len(values)


summary: dict = {}
for tools, folder in SIZES.items():
    path = S / folder / "calls.jsonl"
    if not path.exists():
        continue
    rows = [json.loads(line) for line in path.open(encoding="utf-8")]
    votes: dict = defaultdict(lambda: defaultdict(list))
    for r in rows:
        votes[r["id"]][r["variant"]].append(bool(r["right"]) and not r["failed"])
    size: dict = {}
    for v, label in VARIANTS.items():
        rs = [r for r in rows if r["variant"] == v]
        if not rs:
            continue
        web = [r for r in rs if r["id"].startswith("fresh-web")]
        talk = [r for r in rs if r["id"].startswith("fresh-talk")]
        cell = {
            "label": label,
            "web_right": sum(r["right"] for r in web),
            "web_total": len(web),
            "web_lines_right": sum(majority(votes[i][v]) for i in {r["id"] for r in web}),
            "talk_right": sum(r["right"] for r in talk),
            "talk_total": len(talk),
            "talk_web_search": sum(1 for r in talk if r["picked"] and "web_search" in r["picked"]),
            "failed": sum(r["failed"] for r in rs),
            "second_checks": sum(1 for r in rs if r.get("expanded")),
            "second_check_lines": len({r["id"] for r in rs if r.get("expanded")}),
            "intent_est": round(statistics.mean(r["intent_est"] for r in rs), 1),
            "median_ms": round(statistics.median(r["ms"] for r in rs), 1),
            "wrong": Counter(
                f"{r['id']}: {', '.join(r['picked']) if r['picked'] else 'no tool'}"
                for r in rs
                if not r["right"]
            ).most_common(),
        }
        for other in ("expand_live", "full_live"):
            if other == v:
                continue
            pairs = [(majority(d[v]), majority(d[other])) for d in votes.values() if d[v] and d[other]]
            a = sum(1 for x, y in pairs if x and not y)
            b = sum(1 for x, y in pairs if y and not x)
            cell[f"vs_{other}"] = {"only_this": a, "only_other": b, "p": round(mcnemar(a, b), 4)}
        size[v] = cell
    summary[tools] = size

(OUT / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
for tools, size in summary.items():
    for v, c in size.items():
        print(
            f"{tools} {c['label']}: web {c['web_right']}/{c['web_total']} ({c['web_lines_right']} lines) "
            f"talk {c['talk_right']}/{c['talk_total']} talk->web_search {c['talk_web_search']} "
            f"2nd {c['second_checks']} ({c['second_check_lines']} lines) tok {c['intent_est']} ms {c['median_ms']} "
            f"vs expand {c.get('vs_expand_live')} vs full {c.get('vs_full_live')} failed {c['failed']}"
        )
        for w, n in c["wrong"]:
            print(f"    {n}x {w}")
