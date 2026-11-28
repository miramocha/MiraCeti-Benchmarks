"""Stray web_search in full turns: python web_strays.py <run folder> [<run folder> ...].

Counts, per arm, the turns on lines that don't expect web_search where the intent check routed web_search, and the
turns where a tool round called it. Tool-round calls come from steps.jsonl, so calls after the miss check count too
(the turn's ran field leaves those out).
"""

import json
import sys
from collections import defaultdict
from pathlib import Path


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.open(encoding="utf-8")]


for folder in map(Path, sys.argv[1:]):
    turns = load(folder / "turns.jsonl")
    calls: dict = defaultdict(set)
    for step in load(folder / "steps.jsonl"):
        if step["step"] == "task_round":
            calls[(step["arm"], step["case"], step["repeat"])].update(step["calls"])
    print(f"## {folder.name}")
    for arm in sorted({t["arm"] for t in turns}):
        rows = [t for t in turns if t["arm"] == arm and "web_search" not in t.get("expected", [])]
        routed = [t for t in rows if "web_search" in (t.get("routed") or [])]
        called = [t for t in rows if "web_search" in calls[(arm, t["case"], t["repeat"])]]
        print(f"- {arm}: of {len(rows)} turns on lines that don't need web_search, intent routed it on "
              f"{len(routed)} and a tool round called it on {len(called)}")
        for t in called:
            print(f"    {t['case']} r{t['repeat']}: {t['line']}")
