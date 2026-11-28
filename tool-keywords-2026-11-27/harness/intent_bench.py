"""Intent-check regression bench: do the live intent prompt and the tools' intent_examples catch cancels
without new false alarms?

Runs CetiMind's IntentRouter alone (no turn), thinking off, on the prompt-order test lines plus the held-out
cancel lines and near misses in intent_lines.py. Two variants, interleaved per line:
  live  today's INTENT_INSTRUCTION and every ToolSpec.intent_examples line
  bare  the same instruction with the examples stripped, as the baseline

Rerun it whenever INTENT_INSTRUCTION or any example changes:
    uv run python bench/prompt_order/intent_bench.py --base-url http://HOST:PORT/v1 --out DIR [--repeats 5]
Writes DIR/calls.jsonl (one row per check) and DIR/summary.json, prints the groups and whether live meets the bar
in intent_lines.py, and exits 1 when it does not. A failed check is its own miss, not a near-miss alarm. On any
or all lines, live may not pick more stray tools than bare does.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import os
import random
import statistics
import sys
import tempfile
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

# A direct run must not open the real data folder. A test already set its own folder.
if not os.environ.get("CETIMIND_DATA_DIR"):
    os.environ["CETIMIND_DATA_DIR"] = tempfile.mkdtemp(prefix="cetimind-intent-")
sys.path.insert(0, str(Path(__file__).parent))

import heavy  # noqa: E402
import intent_lines  # noqa: E402

from cetimind.app.intent import IntentRouter  # noqa: E402
from cetimind.app.router import FailedRoute, RouteTurn  # noqa: E402
from cetimind.app.tools.schedule import user_tools  # noqa: E402
from cetimind.app.tools.web import web_tools  # noqa: E402
from cetimind.llm.capabilities import Capabilities  # noqa: E402
from cetimind.llm.client import LlmClient  # noqa: E402

MODEL = "qwen3.5-4b"
CAPS = Capabilities(thinking="reasoning_effort", tools=True, named_tool_choice="unsupported")
LIVE_TOOLS = (*user_tools(), *web_tools())
BARE_TOOLS = tuple(dataclasses.replace(spec, intent_examples=()) for spec in LIVE_TOOLS)
VARIANTS = {"live": LIVE_TOOLS, "bare": BARE_TOOLS}
GROUPS = ("cancel_test", "cancel_new", "near_miss", "tool", "none", "either")
# current_time is already in the prompt, so picking it beside the needed tool is not a stray.
_CLOCK = frozenset({"current_time"})
_STRAY_NEEDS = frozenset({"any", "all"})


@dataclass(frozen=True)
class Line:
    id: str
    lang: str
    text: str
    group: str  # tool, none, either, cancel_test, cancel_new, near_miss
    expect: frozenset[str]
    need: str  # any, all, none, either, cancel


def all_lines() -> list[Line]:
    out = []
    for case in heavy.cases():
        if case.id.startswith(intent_lines.CANCEL_TEST):
            out.append(Line(case.id, case.lang, case.line, "cancel_test", frozenset({"schedule_cancel"}), "cancel"))
        elif case.need == "none":
            out.append(Line(case.id, case.lang, case.line, "none", frozenset(), "none"))
        elif case.need == "either":
            out.append(Line(case.id, case.lang, case.line, "either", case.tools, "either"))
        else:
            out.append(Line(case.id, case.lang, case.line, "tool", case.tools, case.need))
    for lang in ("en", "ja"):
        for i, text in enumerate(intent_lines.CANCEL_NEW[lang]):
            out.append(Line(f"cnew{i}-{lang}", lang, text, "cancel_new", frozenset({"schedule_cancel"}), "cancel"))
        for i, text in enumerate(intent_lines.NEAR_MISS[lang]):
            out.append(Line(f"near{i}-{lang}", lang, text, "near_miss", frozenset(), "none"))
    return out


class ExampleReuseError(Exception):
    """An intent example copies a bench line, so the bench would measure copying."""


def check_wording(lines: list[Line]) -> None:
    """Raise when an intent example reuses a bench line, so the bench measures generalizing, not copying."""
    texts = {" ".join(line.text.lower().split()) for line in lines}
    for spec in LIVE_TOOLS:
        for example in spec.intent_examples:
            if " ".join(example.line.lower().split()) in texts:
                raise ExampleReuseError(f"{spec.name} intent example reuses a bench line: {example.line!r}")


def _covered(line: Line, picked: set[str]) -> bool:
    """True when every pick is an expected tool or the clock."""
    return picked <= (line.expect | _CLOCK)


def right(line: Line, picked: set[str] | None) -> bool:
    """True when the pick matches the line. An any or all line is wrong when it also picks a stray tool."""
    if picked is None:
        return False
    if line.need == "none":
        return not picked
    if line.need == "either":
        return picked <= line.expect
    if line.need == "cancel":
        return "schedule_cancel" in picked
    if not _covered(line, picked):
        return False
    if line.need == "all":
        return line.expect <= picked
    return bool(picked & line.expect)


def _rate(table: dict, variant: str, group: str) -> float:
    cell = table[variant][group]
    return cell["right"] / cell["total"] if cell["total"] else 0.0


def _stray(row: dict) -> bool:
    """An any or all line that picked a tool outside its expect, other than the clock."""
    if row["failed"] or row["need"] not in _STRAY_NEEDS or not row["picked"]:
        return False
    return bool(set(row["picked"]) - set(row["expect"]) - _CLOCK)


def _near_miss_alarms(rows: list[dict]) -> int:
    """Live near misses that picked a tool. A failed check is not an alarm."""
    return sum(
        1
        for row in rows
        if row["variant"] == "live" and row["group"] == "near_miss" and not row["failed"] and row["picked"]
    )


def summarize(rows: list[dict]) -> dict:
    """Right counts per variant and group, median times, and whether live meets the bar.

    Failed checks are left out of the rates and are not near-miss alarms. They fail the run on their own.
    """
    hits: dict[tuple[str, str], list[bool]] = defaultdict(list)
    times: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        times[row["variant"]].append(row["ms"])
        if not row["failed"]:
            hits[(row["variant"], row["group"])].append(row["right"])
    table = {
        variant: {
            group: {"right": sum(hits[(variant, group)]), "total": len(hits[(variant, group)])} for group in GROUPS
        }
        for variant in VARIANTS
    }
    medians = {variant: round(statistics.median(times[variant]), 1) for variant in VARIANTS if times[variant]}
    failures = sum(1 for row in rows if row["failed"])
    alarms = _near_miss_alarms(rows)
    strays = {variant: sum(1 for row in rows if row["variant"] == variant and _stray(row)) for variant in VARIANTS}
    checks = {
        "cancel_new": _rate(table, "live", "cancel_new") >= intent_lines.MIN_CANCEL_NEW,
        "near_miss_alarms": alarms <= intent_lines.MAX_NEAR_MISS_ALARMS,
        "no_failures": failures == 0,
        "no_extra_strays": strays["live"] <= strays["bare"],
        **{
            f"no_drop_{group}": _rate(table, "live", group) >= _rate(table, "bare", group)
            for group in intent_lines.NO_DROP_GROUPS
        },
    }
    return {
        "groups": table,
        "median_ms": medians,
        "failures": failures,
        "near_miss_alarms": alarms,
        "stray_lines": strays,
        "checks": checks,
        "pass": all(checks.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20261126)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    lines = all_lines()
    try:
        check_wording(lines)
    except ExampleReuseError as error:
        sys.exit(str(error))
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    client = LlmClient(args.base_url, MODEL, "unused", max_tokens=2048, capabilities=CAPS)
    router = IntentRouter(client)
    last = {lang: heavy.HISTORY[lang][-1][1] for lang in ("en", "ja")}
    client.chat([{"role": "user", "content": "hi"}], think=False)
    started = time.perf_counter()
    rows: list[dict] = []
    try:
        with (out / "calls.jsonl").open("w", encoding="utf-8") as handle:
            for repeat in range(args.repeats):
                rng = random.Random(args.seed + repeat)
                for line in lines:
                    order = list(VARIANTS)
                    rng.shuffle(order)
                    for name in order:
                        t0 = time.perf_counter()
                        chosen = router.decide(RouteTurn(line.text, last[line.lang], VARIANTS[name], False, None))
                        ms = (time.perf_counter() - t0) * 1000
                        failed = isinstance(chosen, FailedRoute)
                        picked = None if failed else {spec.name for spec in chosen}
                        row = {"variant": name, "repeat": repeat, "id": line.id, "lang": line.lang, "line": line.text,
                               "group": line.group, "need": line.need, "expect": sorted(line.expect),
                               "picked": None if picked is None else sorted(picked), "failed": failed,
                               "right": right(line, picked), "ms": round(ms, 1)}
                        rows.append(row)
                        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                        handle.flush()
                print(json.dumps({"repeat": repeat, "elapsed_s": round(time.perf_counter() - started)}), flush=True)
    finally:
        client.close()
    summary = summarize(rows)
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    if not summary["pass"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
