"""Build gold.jsonl for this run: the judge's labels with hand corrections.

Labels were reviewed by Claude reading each reply, not by a person. Index is the 1-based row number across
7fcacca-reply-graded.jsonl then main-reply-graded.jsonl.
"""

from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).parent
FIXES: dict[int, dict[str, str]] = {
    3: {"dish": "not_mentioned"},
    5: {"wake": "not_mentioned"},
    8: {"wake": "active"},
    21: {"wake": "active"},
    28: {"dish": "active", "wake": "not_mentioned"},
    30: {"dish": "active", "wake": "not_mentioned"},
    37: {"lunch": "not_mentioned"},
    39: {"lunch": "not_mentioned"},
    43: {"wake": "not_mentioned"},
    48: {"wake": "not_mentioned"},
    54: {"wake": "not_mentioned", "dish": "ended", "pr": "not_mentioned", "food": "not_mentioned"},
    55: {"dish": "unclear"},
    57: {"dish": "active", "wake": "not_mentioned"},
    58: {"dish": "active"},
    60: {"dish": "active", "wake": "not_mentioned"},
}

rows = []
for name in ("7fcacca-reply-graded.jsonl", "main-reply-graded.jsonl"):
    rows += [json.loads(line) for line in (HERE / name).read_text("utf-8").splitlines() if line.strip()]
with (HERE / "gold.jsonl").open("w", encoding="utf-8") as sink:
    for index, row in enumerate(rows, start=1):
        labels = {**(row["labels"] or {}), **FIXES.get(index, {})}
        sink.write(json.dumps({"scenario": row["scenario"], "question": row["question"], "reply": row["reply"], "labels": labels}, ensure_ascii=False) + "\n")
print(len(rows), "rows")
