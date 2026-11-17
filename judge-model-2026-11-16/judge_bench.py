"""Judge benchmark: the real learn step on a temp store, per judge model. Nothing is saved to the real data."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

os.environ["CETIMIND_DATA_DIR"] = tempfile.mkdtemp(prefix="cetimind-judge-")

from cetimind.app.judge import JudgeAdapter  # noqa: E402
from cetimind.app.settings import Settings  # noqa: E402
from cetimind.config import llm_base_url  # noqa: E402
from cetimind.llm.client import LlmClient  # noqa: E402
from cetimind.memory.learn import learn  # noqa: E402
from cetimind.memory.store import ListQuery, Store  # noqa: E402

EMBED = "text-embedding-nomic-embed-text-v1.5"
# (line, keywords each expected fact or event must contain). [] means nothing should be learned.
EXTRACT = [
    ("I love ramen, especially tonkotsu.", [["ramen"]]),
    ("My sister Aiko lives in Osaka.", [["aiko"]]),
    ("I work as a game developer at a small indie studio.", [["game"]]),
    ("I'm allergic to peanuts.", [["peanut"]]),
    ("My cat's name is Mochi and she's 3 years old.", [["mochi"]]),
    ("I don't like horror movies.", [["horror"]]),
    ("My favorite color is blue.", [["blue"]]),
    ("I just finished my first marathon yesterday!", [["marathon"]]),
    ("lol that's so funny", []),
    ("What time is it?", []),
    ("Can you remind me to drink water in 20 minutes?", []),
    ("How are you feeling today?", []),
]
# (seeded fact, line, keyword that must be present after, keyword that must be gone, keyword that must appear once)
UPDATE = [
    ("User's favorite color is blue.", "Actually my favorite color is green now.", "green", "blue", None),
    ("User lives in Tokyo.", "I moved to Kyoto last month.", "kyoto", "tokyo", None),
    ("User loves ramen.", "I really love ramen.", "ramen", None, "ramen"),
]


def client(settings: Settings, base: str, model: str) -> LlmClient:
    return LlmClient(base, model, EMBED, max_tokens=1024, thinking="auto", capabilities=settings.capabilities_for(base, model))


def texts(store: Store) -> list[str]:
    records = [*store.list_records(ListQuery(kind="fact")), *store.list_records(ListQuery(kind="event"))]
    return [record.text for record in records]


def open_store(embedder: LlmClient) -> Store:
    folder = Path(tempfile.mkdtemp())
    return Store.open(folder / "m.db", embedder=embedder, embed_model=EMBED, embed_dim=768, clock=lambda: datetime.now(UTC))


def run(settings: Settings, base: str, model: str, repeat: int) -> None:
    judge_client = client(settings, base, model)
    judge = JudgeAdapter(judge_client)
    try:
        for index, (line, expected) in enumerate(EXTRACT):
            store = open_store(judge_client)
            started = time.perf_counter()
            error = ""
            try:
                learn(store, judge, judge_client, line, name="User", assistant="Ceti")
            except Exception as failure:  # noqa: BLE001
                error = f"{type(failure).__name__}: {failure}"[:200]
            elapsed = round((time.perf_counter() - started) * 1000)
            stored = texts(store)
            store.close()
            lowered = [text.lower() for text in stored]
            if expected:
                ok = all(any(all(word in text for word in group) for text in lowered) for group in expected)
            else:
                ok = not stored
            row = {"kind": "extract", "model": model, "repeat": repeat, "case": index, "line": line,
                   "ok": ok, "ms": elapsed, "stored": stored, "error": error}
            print(json.dumps(row, ensure_ascii=False), flush=True)
        for index, (seed, line, present, gone, once) in enumerate(UPDATE):
            store = open_store(judge_client)
            store.add_fact(seed, source="user")
            started = time.perf_counter()
            error = ""
            try:
                learn(store, judge, judge_client, line, name="User", assistant="Ceti")
            except Exception as failure:  # noqa: BLE001
                error = f"{type(failure).__name__}: {failure}"[:200]
            elapsed = round((time.perf_counter() - started) * 1000)
            stored = texts(store)
            store.close()
            lowered = [text.lower() for text in stored]
            ok = any(present in text for text in lowered)
            if gone:
                ok = ok and not any(gone in text for text in lowered)
            if once:
                ok = ok and sum(once in text for text in lowered) == 1
            row = {"kind": "update", "model": model, "repeat": repeat, "case": index, "line": line,
                   "ok": ok, "ms": elapsed, "stored": stored, "error": error}
            print(json.dumps(row, ensure_ascii=False), flush=True)
    finally:
        judge_client.close()


def main() -> None:
    settings = Settings.load(Path(sys.argv[1]))
    base = llm_base_url(settings.llm_base_url)
    repeats = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    for repeat in range(repeats):
        for model in ("qwen3.5-4b", "nvidia/nemotron-3-nano-4b"):
            run(settings, base, model, repeat)


if __name__ == "__main__":
    main()
