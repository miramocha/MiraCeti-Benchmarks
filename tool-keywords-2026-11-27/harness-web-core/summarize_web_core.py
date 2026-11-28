"""Tables for the web-core run: python summarize_web_core.py <tool-keywords folder>. Writes run-web-core/*.json."""

import json
import math
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

S = Path(sys.argv[1])
OUT = S / "run-web-core"
SIZES = {16: "run-web-core/tools-16", 36: "run-web-core/tools-36", 66: "run-web-core/tools-66"}
VARIANTS = {"full_live": "Full", "expand_live": "Expand", "webexp_live": "Web core + expand", "catkw_live": "Keyword categories",
            "webcat_live": "Web core + keyword categories"}
PER_SIZE = len(VARIANTS) * 98 * 5


def subset(row):
    if row["id"].startswith("hold-web"):
        return "web"
    if row["id"].startswith("hold-talk"):
        return "talk"
    return "old"


def mcnemar(a, b):
    n, k = a + b, min(a, b)
    return 1.0 if n == 0 else min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n)


status, results, picks, wrong = [], [], [], []
for tools, folder in SIZES.items():
    path = S / folder / "calls.jsonl"
    rows = [json.loads(line) for line in path.open(encoding="utf-8")] if path.exists() else []
    finished = (S / folder / "summary.json").exists()
    status.append({"tools": tools, "checks": len(rows), "of": PER_SIZE,
                   "state": "done" if finished else ("running" if rows else "queued")})
    lines = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if not r["failed"]:
            lines[r["id"]][r["variant"]].append(r["right"])
    for v, label in VARIANTS.items():
        rs = [r for r in rows if r["variant"] == v and not r["failed"]]
        if not rs:
            continue
        part = {s: [r for r in rs if subset(r) == s] for s in ("old", "web", "talk")}
        row = {"key": f"{tools}|{v}", "tools": tools, "variant": v, "label": label,
               "right": sum(r["right"] for r in rs), "total": len(rs),
               "rate": round(sum(r["right"] for r in rs) / len(rs), 4)}
        for s, xs in part.items():
            row[f"{s}_right"] = sum(r["right"] for r in xs)
            row[f"{s}_total"] = len(xs)
        row["near_miss_alarms"] = sum(1 for r in rs if r["group"] == "near_miss" and r["picked"])
        row["second_pass"] = sum(1 for r in rs if r.get("expanded"))
        row["intent_est"] = round(statistics.mean(r["intent_est"] for r in rs), 1)
        row["median_ms"] = round(statistics.median(r["ms"] for r in rs), 1)
        if v != "expand_live":
            wa = sum(1 for d in lines.values() if v in d and "expand_live" in d
                     and sum(d[v]) / len(d[v]) > sum(d["expand_live"]) / len(d["expand_live"]))
            wb = sum(1 for d in lines.values() if v in d and "expand_live" in d
                     and sum(d[v]) / len(d[v]) < sum(d["expand_live"]) / len(d["expand_live"]))
            row.update(line_only_this=wa, line_only_expand=wb, line_p=round(mcnemar(wa, wb), 4))
        results.append(row)
        if v in ("catkw_live", "webcat_live"):
            more = sum(1 for r in rs if r.get("expanded") and not r.get("categories"))
            counts = Counter(g for r in rs for g in r.get("categories", ()))
            if more:
                counts["more_tools"] = more
            for group, count in counts.most_common():
                picks.append({"key": f"{tools}|{v}|{group}", "tools": tools, "variant": label,
                              "picked": group, "count": count})
    wrong_counts = Counter((r["variant"], r["id"], ", ".join(r["picked"]) if r["picked"] else "no tool")
                           for r in rows if not r["right"] and not r["failed"])
    for (v, line_id, picked), count in sorted(wrong_counts.items()):
        wrong.append({"key": f"{tools}|{v}|{line_id}|{picked}", "tools": tools, "variant": VARIANTS[v],
                      "id": line_id, "picked": picked, "count": count})

for name, data in (("status", status), ("results", results), ("picks", picks), ("wrong", wrong)):
    (OUT / f"{name}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
print(json.dumps(status))
for r in results:
    print(r["key"], f"old {r['old_right']}/{r['old_total']} web {r['web_right']}/{r['web_total']} "
          f"talk {r['talk_right']}/{r['talk_total']} 2nd {r['second_pass']} vs-expand {r.get('line_p')}")
