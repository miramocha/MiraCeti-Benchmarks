"""Live check: qwen alone, nemotron alone, and the split. Temp store, fake tool handlers, nothing saved."""

from __future__ import annotations

import json
import logging
import os
import sys
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path

os.environ["CETIMIND_DATA_DIR"] = tempfile.mkdtemp(prefix="cetimind-bench-")

from cetimind.app.intent import IntentRouter  # noqa: E402
from cetimind.app.safety import JsonMissCheck  # noqa: E402
from cetimind.app.settings import Settings  # noqa: E402
from cetimind.app.tools.registry import ToolRegistry  # noqa: E402
from cetimind.app.tools.schedule import user_tools  # noqa: E402
from cetimind.app.tools.web import web_tools  # noqa: E402
from cetimind.app.turn import Memory, TurnOptions, finish_turn, reply_turn, run_net  # noqa: E402
from cetimind.config import llm_base_url  # noqa: E402
from cetimind.core.persona import Persona  # noqa: E402
from cetimind.llm.client import LlmClient  # noqa: E402
from cetimind.memory.store import Store  # noqa: E402

PERSONA = Persona(name="Ceti", tone="Warm, playful", boundaries=("Be brief.",), prompt="You are Ceti, a cheerful companion.")
TOOLS = (*user_tools(), *web_tools())
CASES = [
    ("What time is it right now?", {"current_time"}),
    ("Remind me to drink water in 20 minutes.", {"schedule_create"}),
    ("What reminders do I have?", {"schedule_list"}),
    ("Cancel my water reminder.", {"schedule_list", "schedule_cancel"}),
    ("Every morning at 8, remind me to stretch.", {"schedule_create"}),
    ("In 2 hours tell me to check the oven.", {"schedule_create"}),
    ("Search the web for the latest Godot engine release.", {"web_search"}),
    ("Who won the most recent Formula 1 race?", {"web_search"}),
    ("What does https://example.com say?", {"http_get"}),
    ("Tell me about your day!", set()),
    ("I love ramen, especially tonkotsu.", set()),
    ("How are you feeling today?", set()),
    ("Wake me up at 7 tomorrow.", {"schedule_create"}),
    ("Set a timer for 5 minutes.", {"schedule_create"}),
    ("Are my reminders still on?", {"schedule_list"}),
    ("Forget the oven reminder, I already checked it.", {"schedule_list", "schedule_cancel"}),
    # The prompt carries the date, so answering with or without current_time are both right.
    ("What day is it today?", {"current_time", "*"}),
    ("What's the weather in Tokyo right now?", {"web_search"}),
    ("Read https://godotengine.org for me.", {"http_get"}),
    ("lol that's so funny", set()),
    ("I'm going to drink some water now.", set()),
    ("My favorite color is blue.", set()),
    ("Do you remember what we talked about yesterday?", set()),
]


class Zero:
    def embed_document(self, text: str) -> list[float]:
        return [0.0] * 768

    def embed_query(self, text: str) -> list[float]:
        return [0.0] * 768


class NoJudge:
    def complete_json(self, prompt, schema):
        return {"facts": [], "events": []}


def registry(ran: list[str]) -> ToolRegistry:
    reg = ToolRegistry()
    canned = {
        "current_time": "2026-11-16 14:05 (Monday), local time.",
        "schedule_create": "Scheduled job 7.",
        "schedule_list": "Jobs: 7 'Drink water' in 18 minutes. 8 'Check the oven' in 1 hour 40 minutes.",
        "schedule_cancel": "Cancelled job 7.",
        "web_search": "1. Godot 4.6 released (godotengine.org) 2. F1: Verstappen won the Las Vegas GP.",
        "http_get": "Example Domain. This domain is for use in illustrative examples in documents.",
    }
    for spec in TOOLS:
        def handler(arguments, name=spec.name):
            ran.append(name)
            return canned[name]
        reg.register(spec, handler)
    return reg


def client(settings: Settings, base: str, model: str) -> LlmClient:
    return LlmClient(base, model, "text-embedding-nomic-embed-text-v1.5", max_tokens=1024,
                     capabilities=settings.capabilities_for(base, model))


def switch_cost(settings_path: str, rounds: int = 10) -> None:
    """Time the intent check on nemotron right after a nemotron call, and right after a qwen call."""
    settings = Settings.load(Path(settings_path))
    base = llm_base_url(settings.llm_base_url)
    qwen = client(settings, base, "qwen3.5-4b")
    nemo = client(settings, base, "nvidia/nemotron-3-nano-4b")
    router = IntentRouter(nemo)
    from cetimind.app.router import RouteTurn

    turn = RouteTurn("Remind me to drink water in 20 minutes.", "Hi!", TOOLS)
    message = [{"role": "user", "content": "Say one short friendly sentence."}]
    try:
        for before_label, before in (("after_nemotron", nemo), ("after_qwen", qwen)):
            times = []
            for _ in range(rounds):
                before.chat(message, think=False)
                started = time.perf_counter()
                router.decide(turn)
                times.append(round((time.perf_counter() - started) * 1000))
            row = {"config": "switch", "case": before_label, "route_ms": times}
            print(json.dumps(row), flush=True)
    finally:
        qwen.close()
        nemo.close()


def run(label: str, chat_model: str, tool_model: str | None, repeat: int = 0, thinking: str = "auto",
        tool_thinking: str = "auto") -> list[dict]:
    settings = Settings.load(Path(sys.argv[1]))
    base = llm_base_url(settings.llm_base_url)
    chat = client(settings, base, chat_model)
    tool = client(settings, base, tool_model or chat_model)
    split = tool_model is not None
    rows = []
    try:
        chat.chat([{"role": "user", "content": "hi"}], think=False)
        tool.chat([{"role": "user", "content": "hi"}], think=False)
        for index, (line, expected) in enumerate(CASES):
            ran: list[str] = []
            folder = Path(tempfile.mkdtemp())
            # The real embedder, so the memory search's embed call overlaps the intent check as in the app.
            store = Store.open(folder / "m.db", embedder=chat, embed_model="text-embedding-nomic-embed-text-v1.5",
                               embed_dim=768, clock=lambda: datetime.now(UTC))
            options = TurnOptions(
                temperature=0.7,
                memory=Memory(store, NoJudge(), chat),
                tools=TOOLS,
                registry=registry(ran),
                router=IntentRouter(tool),
                net=JsonMissCheck(tool),
                now=datetime.now().astimezone(),
                tool_chatter=tool if split else None,
                thinking=thinking,
                tool_thinking=tool_thinking,
            )
            row = {"config": label, "repeat": repeat, "case": index, "line": line, "expected": sorted(expected)}
            started = time.perf_counter()
            try:
                produced = reply_turn(chat, PERSONA, line, options)
                row["turn_ms"] = round((time.perf_counter() - started) * 1000)
                row["route_ms"] = round(produced.report.timings.route)
                row["routed"] = produced.report.routed
                row["reply"] = produced.text.replace("\n", " ")[:140]
                row["rescued"] = produced.report.rescued
                finish_turn(produced.pending)
                if produced.net is not None:
                    net_started = time.perf_counter()
                    net = run_net(chat, produced.net, lambda: False)
                    row["net_ms"] = round((time.perf_counter() - net_started) * 1000)
                    row["net_fired"] = net.fired
                    if net.follow_up:
                        row["follow_up"] = net.follow_up.replace("\n", " ")[:140]
            except Exception as error:  # noqa: BLE001
                row["turn_ms"] = round((time.perf_counter() - started) * 1000)
                row["error"] = f"{type(error).__name__}: {error}"[:300]
            finally:
                store.close()
            row["ran"] = ran
            got = set(ran)
            if "*" in expected:
                expected = expected - {"*"}
                row["ok"] = not got or got <= expected
                rows.append(row)
                print(json.dumps(row, ensure_ascii=False), flush=True)
                continue
            row["ok"] = (not expected and not got) or (bool(expected) and bool(got) and got <= expected | {"current_time"}
                                                       and bool(got & expected))
            rows.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
    finally:
        chat.close()
        tool.close()
    return rows


def main() -> None:
    logging.basicConfig(level=logging.WARNING)
    which = sys.argv[2] if len(sys.argv) > 2 else "all"
    repeats = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    configs = {
        "qwen": ("qwen3.5-4b", None, "auto", "auto"),
        "nemotron": ("nvidia/nemotron-3-nano-4b", None, "auto", "auto"),
        "split": ("qwen3.5-4b", "nvidia/nemotron-3-nano-4b", "auto", "auto"),
        "qwen_off": ("qwen3.5-4b", None, "off", "auto"),
        "split_tooloff": ("qwen3.5-4b", "nvidia/nemotron-3-nano-4b", "auto", "off"),
    }
    if which in ("all", "switch"):
        switch_cost(sys.argv[1])
    # Configs interleave per repeat, so drift on the server lands on all three alike.
    for repeat in range(repeats):
        for label, (chat_model, tool_model, thinking, tool_thinking) in configs.items():
            if which in ("all", label) or label in which.split(","):
                run(label, chat_model, tool_model, repeat, thinking, tool_thinking)


if __name__ == "__main__":
    main()
