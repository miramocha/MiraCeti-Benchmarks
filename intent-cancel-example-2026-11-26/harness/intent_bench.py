"""Intent-check benchmark: does one cancel example fix the thinking-off intent check without new false alarms?

Runs CetiMind's IntentRouter alone (no turn) on the prompt-order test lines plus held-out cancel lines and
near-miss lines that need no tool. Three variants, interleaved per line:
  off          thinking off, today's instruction (arm D's intent check)
  off_example  thinking off, today's instruction plus one cancel example (worded unlike every test line)
  on128        thinking on with the 128-token Tools cap (arm A's intent check under the live settings)

    uv run python bench/prompt_order/intent_bench.py --base-url http://HOST:PORT/v1 --out DIR [--repeats 5]
Writes DIR/calls.jsonl, one row per intent check.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

os.environ["CETIMIND_DATA_DIR"] = tempfile.mkdtemp(prefix="cetimind-intent-")
sys.path.insert(0, str(Path(__file__).parent))

import heavy  # noqa: E402
from lines import CASES  # noqa: E402

import cetimind.app.intent as intent_module  # noqa: E402
from cetimind.app.intent import IntentRouter  # noqa: E402
from cetimind.app.router import FailedRoute, RouteTurn  # noqa: E402
from cetimind.app.tools.schedule import user_tools  # noqa: E402
from cetimind.app.tools.web import web_tools  # noqa: E402
from cetimind.llm.capabilities import Capabilities  # noqa: E402
from cetimind.llm.client import LlmClient  # noqa: E402

MODEL = "qwen3.5-4b"
CAPS = Capabilities(thinking="reasoning_effort", tools=True, named_tool_choice="unsupported")
TOOLS = (*user_tools(), *web_tools())
BASE_INSTRUCTION = intent_module.INTENT_INSTRUCTION
# Worded unlike every test line on purpose, so a hit on the test lines is not the example being copied.
CANCEL_EXAMPLE = (
    ' Example: "Never mind the laundry alarm, I already emptied it." needs schedule_list and schedule_cancel, '
    "because the user wants an existing reminder removed."
)


@dataclass(frozen=True)
class Line:
    id: str
    lang: str
    text: str
    group: str  # tool, none, either, cancel_test, cancel_new, near_miss
    expect: frozenset[str]
    need: str  # any, all, none, either, cancel


CANCEL_NEW = {
    "en": ["Drop the water reminder, I just had a glass.", "I don't need the stretch alarm anymore.",
           "Scrap my oven timer, the bread is out.", "Turn off the reminder about the oven.",
           "No need to remind me about water today.", "Can you clear my reminders?"],
    "ja": ["水のリマインダーはいらない、今飲んだから。", "ストレッチのアラームはもういらない。",
           "オーブンのタイマーは消して、パンはもう出した。", "オーブンのリマインダーをオフにして。",
           "今日は水のことリマインドしなくていいよ。", "リマインダーを全部消してくれる？"],
}
NEAR_MISS = {
    "en": ["I cancelled my gym membership today.", "I already checked the oven, the bread looks great.",
           "My reminders app at work is so annoying.", "I forgot to drink water again, oops."],
    "ja": ["今日ジムの会員を解約したよ。", "もうオーブンは確認した、パンいい感じ。",
           "職場のリマインダーアプリ、ほんと面倒。", "また水飲むの忘れてた、あはは。"],
}
CANCEL_TEST = ("cancel-", "forget-")


def all_lines() -> list[Line]:
    out = []
    for case in heavy.cases():
        if case.id.startswith(CANCEL_TEST):
            out.append(Line(case.id, case.lang, case.line, "cancel_test", frozenset({"schedule_cancel"}), "cancel"))
        elif case.need == "none":
            out.append(Line(case.id, case.lang, case.line, "none", frozenset(), "none"))
        elif case.need == "either":
            out.append(Line(case.id, case.lang, case.line, "either", case.tools, "either"))
        else:
            out.append(Line(case.id, case.lang, case.line, "tool", case.tools, case.need))
    for lang in ("en", "ja"):
        for i, text in enumerate(CANCEL_NEW[lang]):
            out.append(Line(f"cnew{i}-{lang}", lang, text, "cancel_new", frozenset({"schedule_cancel"}), "cancel"))
        for i, text in enumerate(NEAR_MISS[lang]):
            out.append(Line(f"near{i}-{lang}", lang, text, "near_miss", frozenset(), "none"))
    return out


def right(line: Line, picked: set[str] | None) -> bool:
    if picked is None:
        return False
    if line.need == "none":
        return not picked
    if line.need == "either":
        return picked <= line.expect
    if line.need == "cancel":
        return "schedule_cancel" in picked
    if line.need == "all":
        return line.expect <= picked
    return bool(picked & line.expect)


VARIANTS = {
    "off": (BASE_INSTRUCTION, False, None),
    "off_example": (BASE_INSTRUCTION + CANCEL_EXAMPLE, False, None),
    "on128": (BASE_INSTRUCTION, True, 128),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20261126)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    client = LlmClient(args.base_url, MODEL, "unused", max_tokens=2048, capabilities=CAPS)
    router = IntentRouter(client)
    last = {lang: heavy.HISTORY[lang][-1][1] for lang in ("en", "ja")}
    lines = all_lines()
    client.chat([{"role": "user", "content": "hi"}], think=False)
    started = time.perf_counter()
    try:
        with (out / "calls.jsonl").open("a", encoding="utf-8") as handle:
            for repeat in range(args.repeats):
                rng = random.Random(args.seed + repeat)
                for line in lines:
                    order = list(VARIANTS)
                    rng.shuffle(order)
                    for name in order:
                        instruction, think, budget = VARIANTS[name]
                        intent_module.INTENT_INSTRUCTION = instruction
                        t0 = time.perf_counter()
                        chosen = router.decide(RouteTurn(line.text, last[line.lang], TOOLS, think, budget))
                        ms = (time.perf_counter() - t0) * 1000
                        failed = isinstance(chosen, FailedRoute)
                        picked = None if failed else {spec.name for spec in chosen}
                        row = {"variant": name, "repeat": repeat, "id": line.id, "lang": line.lang, "line": line.text,
                               "group": line.group, "need": line.need, "expect": sorted(line.expect),
                               "picked": None if picked is None else sorted(picked), "failed": failed,
                               "right": right(line, picked), "ms": round(ms, 1)}
                        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                        handle.flush()
                print(json.dumps({"repeat": repeat, "elapsed_s": round(time.perf_counter() - started)}), flush=True)
    finally:
        intent_module.INTENT_INSTRUCTION = BASE_INSTRUCTION
        client.close()


if __name__ == "__main__":
    main()
