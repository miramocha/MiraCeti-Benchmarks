"""Summarize bench.py output: gate precision/recall, dedupe accuracy, latency, TTFT."""

import json
import statistics as st
import sys
from collections import defaultdict

rows = [json.loads(line) for path in sys.argv[1:] for line in open(path, encoding="utf-8")]


def med(values):
    return round(st.median(values)) if values else "-"


print("## Gate (item 1)  label True = worth remembering")
print("| cand | lang | TP | FN (missed) | FP | TN | precision | recall | errors | median ms |")
print("|---|---|---|---|---|---|---|---|---|---|")
gate = [r for r in rows if r.get("part") == "gate" and r.get("repeat", 0) == 0]
for cand in ("kev", "nemotron", "qwen", "extract_qwen"):
    for lang in ("en", "ja"):
        sel = [r for r in gate if r["cand"] == cand and r["lang"] == lang]
        ok = [r for r in sel if "pred" in r]
        tp = sum(r["pred"] and r["label"] for r in ok)
        fn = sum((not r["pred"]) and r["label"] for r in ok)
        fp = sum(r["pred"] and not r["label"] for r in ok)
        tn = sum((not r["pred"]) and not r["label"] for r in ok)
        prec = f"{tp / (tp + fp):.2f}" if tp + fp else "-"
        rec = f"{tp / (tp + fn):.2f}" if tp + fn else "-"
        print(f"| {cand} | {lang} | {tp} | {fn} | {fp} | {tn} | {prec} | {rec} | {len(sel) - len(ok)} | {med([r['ms'] for r in ok])} |")

# Kev threshold sweep (tuned on the test set, so optimistic).
kev = [r for r in gate if r["cand"] == "kev" and "p" in r]
if kev:
    print("\nKev noul threshold sweep (EN+JA, tuned on the test set):")
    for t in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8):
        wrong = sum((r["p"] >= t) != r["label"] for r in kev)
        print(f"  t={t}: {wrong}/{len(kev)} wrong")
    pos = [r["p"] for r in kev if r["label"]]
    neg = [r["p"] for r in kev if not r["label"]]
    pairs = sum((a > b) + 0.5 * (a == b) for a in pos for b in neg)
    print(f"  AUC {pairs / (len(pos) * len(neg)):.2f}; mean p yes {st.mean(pos):.2f}, no {st.mean(neg):.2f}")
    rep = defaultdict(list)
    for r in rows:
        if r.get("part") == "gate" and r.get("cand") == "kev" and "p" in r:
            rep[(r["lang"], r["case"])].append(r["p"])
    drift = max((max(v) - min(v) for v in rep.values() if len(v) > 1), default=0)
    print(f"  max p drift between 2 repeats: {drift:.3f}")

# Gate vs extract: lines a gate would block where extract stored something (facts lost), and calls saved.
ext = {(r["lang"], r["case"]): r for r in gate if r["cand"] == "extract_qwen" and "pred" in r}
print("\nGate vs today's extract (qwen): calls saved = lines gated off; lost = gated off but extract stored something")
for cand in ("kev", "nemotron", "qwen"):
    sel = [r for r in gate if r["cand"] == cand and "pred" in r]
    saved = sum(not r["pred"] for r in sel)
    lost = [r["line"] for r in sel if not r["pred"] and ext.get((r["lang"], r["case"]), {}).get("pred")]
    print(f"  {cand}: saved {saved}/{len(sel)}, lost {len(lost)}: {lost}")
wrong_ext = [(r["line"], r["stored"]) for r in ext.values() if r["pred"] != r["label"]]
print(f"  extract_qwen disagreements with label: {wrong_ext}")

print("\n## Dedupe (item 3)")
print("| cand | lang | right | same | update | different | errors | median ms |")
print("|---|---|---|---|---|---|---|---|")
dd = [r for r in rows if r.get("part") == "dedupe"]
for cand in ("kev", "nemotron", "qwen", "current_path"):
    for lang in ("en", "ja"):
        sel = [r for r in dd if r["cand"] == cand and r["lang"] == lang]
        ok = [r for r in sel if "pred" in r]
        by = {lab: f"{sum(r['pred'] == lab for r in ok if r['label'] == lab)}/{sum(r['label'] == lab for r in ok)}"
              for lab in ("same", "update", "different")}
        right = sum(r["pred"] == r["label"] for r in ok)
        print(f"| {cand} | {lang} | {right}/{len(ok)} | {by['same']} | {by['update']} | {by['different']} | "
              f"{len(sel) - len(ok)} | {med([r['ms'] for r in ok if 'ms' in r])} |")
for r in dd:
    if r["cand"] == "current_path" and "pred" in r and r["pred"] != r["label"]:
        print(f"  current_path miss [{r['lang']}] {r['label']}->{r['action']} cos={r['cos']}: {r['stored']} | {r['new']} -> {r['after']}")
for r in dd:
    if "error" in r:
        print(f"  error {r['cand']} [{r['lang']}] {r['case']}: {r['error']}")

tt = [r for r in rows if r.get("part") == "ttft"]
if tt:
    print("\n## qwen TTFT during a background call")
    for kind in ("idle", "kev", "nemotron", "qwen", "extract_qwen"):
        v = [r["ttft_ms"] for r in tt if r["during"] == kind]
        if v:
            print(f"  {kind}: median {med(v)} ms, max {max(v)}, n={len(v)}")
