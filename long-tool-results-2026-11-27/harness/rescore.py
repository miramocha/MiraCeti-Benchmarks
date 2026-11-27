"""Rescore run/turns.jsonl with long_results.says_answer and print the tables in summary.md.

The run scored replies with exact keys. Spoken forms (number words, kanji numerals, spaced dates) were added to the
matcher partway through, so every table here is rescored from the saved replies: python rescore.py ../run
"""

import json
import math
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

import long_results as L

run = Path(sys.argv[1])
keys = {c.id: c.keys for c in L.cases()}
rows = [json.loads(line) for line in (run / "turns.jsonl").open(encoding="utf-8") if line.strip()]
steps = [json.loads(line) for line in (run / "steps.jsonl").open(encoding="utf-8") if line.strip()]
for r in rows:
    r["right"] = L.says_answer(r["case"], keys[r["case"]], r["reply"])
    r["wrong"] = any(m.lower() in r["reply"].lower() for m in L.wrong_marks(r["case"])) and not r["right"]
ARMS = ["L", "L2500", "LFULL", "LSUM"]


def count(v, f=lambda r: True):
    sub = [r for r in v if f(r)]
    return f"{sum(r['right'] for r in sub)}/{len(sub)}"


def pct(values, q):
    if not values:
        return float("nan")
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(q * len(ordered)) - 1))
    return ordered[index]


def med(vals):
    return f"{st.median(vals):,.0f} ({pct(vals, 0.9):,.0f})" if vals else "–"


print(f"Turns: {len(rows)}, errors: {sum(bool(r.get('error')) for r in rows)}\n")
print("Times are medians in ms (p90 in brackets).\n")
print("| Measure | " + " | ".join(ARMS) + " |")
print("| --- |" + " --- |" * len(ARMS))
specs = [
    ("Answer named, all", lambda v: count(v)),
    ("Answer early (under 1,000 chars)", lambda v: count(v, lambda r: r["position"] == "early")),
    ("Answer in the middle", lambda v: count(v, lambda r: r["position"] == "mid")),
    ("Answer late", lambda v: count(v, lambda r: r["position"] == "late")),
    ("English", lambda v: count(v, lambda r: r["lang"] == "en")),
    ("Japanese", lambda v: count(v, lambda r: r["lang"] == "ja")),
    ("Fetched pages", lambda v: count(v, lambda r: not r["case"].startswith("marathon"))),
    ("Search results", lambda v: count(v, lambda r: r["case"].startswith("marathon"))),
    ("Distractor named instead", lambda v: f"{sum(r['wrong'] for r in v)}/{len(v)}"),
    ("Right tools called", lambda v: f"{sum(r['ok'] for r in v)}/{len(v)}"),
    ("Answer time", lambda v: med([r["reply_ms"] for r in v])),
]
by_arm = {a: [r for r in rows if r["arm"] == a] for a in ARMS}
for label, fn in specs:
    print(f"| {label} | " + " | ".join(fn(by_arm[a]) for a in ARMS) + " |")
for step, label in (("say_this", "Say-this call"), ("summary", "Summary call")):
    print(f"| {label} | " + " | ".join(med([s["ms"] for s in steps if s["arm"] == a and s["step"] == step])
                                     for a in ARMS) + " |")
tok = {a: [s["prompt_tokens"] for s in steps if s["arm"] == a and s["step"] == "say_this"] for a in ARMS}
print("| Say-this prompt tokens (median) | " + " | ".join(f"{st.median(tok[a]):,.0f}" for a in ARMS) + " |")

pairs = defaultdict(dict)
for r in rows:
    pairs[(r["case"], r["repeat"])][r["arm"]] = r["right"]
print("\nPaired, answer named (exact McNemar; x-only = x right, y wrong):")
for x, y in (("L", "LFULL"), ("L", "LSUM"), ("L", "L2500"), ("LSUM", "LFULL"), ("L2500", "LFULL")):
    a = sum(1 for v in pairs.values() if v.get(x) is True and v.get(y) is False)
    b = sum(1 for v in pairs.values() if v.get(x) is False and v.get(y) is True)
    n = a + b
    p = min(1.0, 2 * sum(math.comb(n, i) for i in range(min(a, b) + 1)) / 2**n) if n else 1.0
    print(f"- {x} vs {y}: {x}-only {a}, {y}-only {b}, p = {p:.2g}")
