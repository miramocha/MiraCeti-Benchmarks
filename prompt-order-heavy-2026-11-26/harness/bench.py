"""Prompt-order benchmark: CetiMind's split order (arm A) against one full persona prompt with every tool (arm B).

Arm A is CetiMind's own reply_turn: intent check, then the hold line beside task-shaped tool rounds, then a say-this
reply, with the miss check. The later miss check runs at once, as in the terminal.
Arm B builds the same persona prompt with CetiMind's own _load and runs CetiMind's own _tool_rounds on it, so one
conversation calls the tools and writes the reply. No intent check, hold line, or miss check.

Both arms use one model and the settings pinned in SETTINGS (copied from the live settings on 2026-11-26). Each turn
gets a fresh copy of a seeded temporary store. Tools are fakes with canned results. The real data directory is never
opened, and the live settings.toml is never read.

Run from a CetiMind checkout:
    uv run python bench/prompt_order/bench.py --base-url http://HOST:PORT/v1 --out DIR [--repeats 3] [--lang en]
Writes DIR/steps.jsonl (one row per HTTP call) and DIR/turns.jsonl (one row per turn).
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import random
import re
import shutil
import sys
import tempfile
import threading
import time
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path

os.environ["CETIMIND_DATA_DIR"] = tempfile.mkdtemp(prefix="cetimind-bench-")
sys.path.insert(0, str(Path(__file__).parent))

from lines import CANNED, CASES, INJECT_MARKS, PERSONA, SEED, USER_NAME, Case  # noqa: E402
import heavy  # noqa: E402

from cetimind.app.intent import IntentRouter  # noqa: E402
from cetimind.app.router import FailedRoute, RouteTurn  # noqa: E402
from cetimind.app.safety import JsonMissCheck  # noqa: E402
from cetimind.app.settings import Settings  # noqa: E402
from cetimind.app.tool_modes import typed_tools  # noqa: E402
from cetimind.app.tools.registry import ToolRegistry  # noqa: E402
from cetimind.app.tools.schedule import user_tools  # noqa: E402
from cetimind.app.tools.web import web_tools  # noqa: E402
from cetimind.app.turn import (  # noqa: E402
    Memory,
    TurnOptions,
    _history,
    _last_assistant,
    _load,
    _Plan,
    _safe,
    _schedule_lines,
    _tool_rounds,
    reply_turn,
    run_net,
)
from cetimind.core.calls import SAY_INSTRUCTION, TOOL_INSTRUCTION, hold_messages, wire_messages  # noqa: E402
from cetimind.core.persona import Persona  # noqa: E402
from cetimind.llm.capabilities import Capabilities  # noqa: E402
from cetimind.llm.client import LlmClient  # noqa: E402
from cetimind.memory.store import Store  # noqa: E402

MODEL = "qwen3.5-4b"
EMBED_MODEL = "nomic-embed-text-v1.5"
EMBED_DIM = 768
# The live settings on 2026-11-26, pinned. tool_model and judge_model are empty, so one model does everything.
SETTINGS = Settings(
    chat_model=MODEL,
    embed_model=EMBED_MODEL,
    chat_temperature=0.6,
    tool_temperature=0.6,
    chat_max_tokens=2048,
    tool_max_tokens=2048,
    judge_max_tokens=2048,
    chat_thinking="on",
    tool_thinking="auto",
    judge_thinking="auto",
    think_hold="off",
    think_replies="follow",
    think_tools="follow",
    think_judge="follow",
    budget_hold=128,
    budget_replies=128,
    budget_tools=128,
    budget_judge=256,
    tool_mode="all",
    user_name=USER_NAME,
)
CAPS = Capabilities(thinking="reasoning_effort", tools=True, named_tool_choice="unsupported")
# A fixed clock, so the prompt start stays the same and current_time's canned answer matches it.
NOW = datetime(2026, 11, 26, 14, 5).astimezone()
TOOLS = (*user_tools(), *web_tools())
TOOL_NAMES = {spec.name for spec in TOOLS}


def _light_seed(lang: str) -> dict:
    seed = SEED[lang]
    return {"pinned": seed["facts"], "facts": [], "profile": seed["profile"], "summary": seed["summary"],
            "history": seed["history"]}


# light: the first run (2026-11-26). heavy: context sized like real use, with traps and the jobs list.
PROFILES = {
    "light": {"persona": PERSONA, "seed": _light_seed, "jobs": None, "cases": lambda: CASES},
    "heavy": {"persona": heavy.PERSONA, "seed": heavy.seed, "jobs": lambda: heavy.job_lines(NOW),
              "cases": heavy.cases},
}
PROFILE = PROFILES["light"]

# --- step log -------------------------------------------------------------------------------------------------------

_lock = threading.Lock()


@dataclass
class TurnLog:
    arm: str
    case: str
    repeat: int
    t0: float
    phase: str = "turn"
    rows: list | None = None
    task_rounds_without_call: int = 0
    tool_ran: bool = False


CURRENT: TurnLog | None = None


def _classify(body: dict) -> str:
    if "input" in body:
        return "embed"
    messages = body.get("messages") or []
    system = messages[0]["content"] if messages and messages[0].get("role") == "system" else ""
    last_user = next((m.get("content") or "" for m in reversed(messages) if m.get("role") == "user"), "")
    if "response_format" in body:
        if system.startswith("Which tools"):
            return "intent"
        if system.startswith("Did the user ask"):
            return "miss"
        return "json"
    if system.startswith(TOOL_INSTRUCTION):
        return "task_round" if "tools" in body else "task_cap"
    if "You have not looked this up yet" in last_user:
        return "hold"
    if SAY_INSTRUCTION in last_user:
        return "say_this"
    if "tools" in body:
        return "full_round"
    return "persona"


_original_post = LlmClient._post


def _timed_post(self, url, body, timeout_s, kind, cancel=None):
    log = CURRENT
    started = time.perf_counter()
    error = ""
    payload = None
    try:
        payload = _original_post(self, url, body, timeout_s, kind, cancel)
        return payload
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"[:200]
        raise
    finally:
        ended = time.perf_counter()
        if log is not None:
            _record(log, body, payload, started, ended, error)


def _record(log: TurnLog, body: dict, payload: object, started: float, ended: float, error: str) -> None:
    step = _classify(body)
    usage = payload.get("usage", {}) if isinstance(payload, dict) else {}
    message = {}
    if isinstance(payload, dict) and payload.get("choices"):
        message = payload["choices"][0].get("message") or {}
    calls = [c.get("function", {}).get("name", "") for c in (message.get("tool_calls") or [])]
    reasoning = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens", 0) or 0
    with _lock:
        if step in ("task_round", "full_round"):
            if calls:
                log.tool_ran = True
            elif not log.tool_ran:
                log.task_rounds_without_call += 1
                if step == "task_round" and log.task_rounds_without_call == 2:
                    step = "task_retry"
        row = {
            "arm": log.arm,
            "case": log.case,
            "repeat": log.repeat,
            "phase": log.phase,
            "step": step,
            "start_ms": round((started - log.t0) * 1000, 1),
            "end_ms": round((ended - log.t0) * 1000, 1),
            "ms": round((ended - started) * 1000, 1),
            "prompt_tokens": usage.get("prompt_tokens"),
            "completion_tokens": usage.get("completion_tokens"),
            "reasoning_tokens": reasoning,
            "thought": bool(reasoning) or bool(message.get("reasoning_content")),
            "think_sent": body.get("reasoning_effort"),
            "budget": body.get("thinking_budget_tokens"),
            "tools_offered": len(body.get("tools") or []),
            "calls": calls,
            "content": (message.get("content") or "")[:200] if step in ("intent", "miss", "json") else "",
            "error": error,
        }
        log.rows.append(row)


LlmClient._post = _timed_post

# --- fixtures -------------------------------------------------------------------------------------------------------


class NoJudge:
    def complete_json(self, prompt, schema):
        return {"facts": [], "events": []}


def _client(base: str) -> LlmClient:
    return LlmClient(base, MODEL, EMBED_MODEL, max_tokens=SETTINGS.chat_max_tokens, thinking=SETTINGS.judge_thinking,
                     capabilities=CAPS, judge_max_tokens=SETTINGS.judge_max_tokens)


def _registry(case: Case, ran: list[str]) -> ToolRegistry:
    reg = ToolRegistry()
    for spec in TOOLS:
        def handler(arguments, name=spec.name):
            ran.append(name)
            return case.overrides.get(name, CANNED[name])
        reg.register(spec, handler)
    return reg


def _open(path: Path, embedder: LlmClient) -> Store:
    return Store.open(path, embedder=embedder, embed_model=EMBED_MODEL, embed_dim=EMBED_DIM,
                      clock=lambda: datetime.now(UTC))


def seed_templates(folder: Path, embedder: LlmClient) -> dict[str, Path]:
    """One seeded store per language. Each turn copies one, so seeding costs nothing per turn."""
    paths = {}
    for lang in ("en", "ja"):
        seed = PROFILE["seed"](lang)
        path = folder / f"seed-{lang}.db"
        store = _open(path, embedder)
        try:
            for fact in seed["pinned"]:
                store.add_fact(fact, source="user", pinned=True)
            for fact in seed["facts"]:
                store.add_fact(fact, source="user")
            if seed["profile"]:
                store.set_profile(seed["profile"], mark=store.facts_mark())
            store.set_summary(seed["summary"], source="system")
            for user, reply in seed["history"]:
                store.add_exchange(user, reply)
        finally:
            store.close()
        paths[lang] = path
    return paths


def _options(store: Store, embedder: LlmClient, case: Case, ran: list[str], chat: LlmClient, *, routed: bool,
             on_hold=None) -> TurnOptions:
    picked = typed_tools(SETTINGS, TOOLS, endpoint_tools=True)
    return TurnOptions(
        temperature=SETTINGS.chat_temperature,
        memory=Memory(store, NoJudge(), embedder),
        user_name=USER_NAME,
        tools=picked.tools,
        now=NOW,
        registry=_registry(case, ran),
        thinking=SETTINGS.chat_thinking,
        router=IntentRouter(chat) if routed else None,
        net=JsonMissCheck(chat) if routed else None,
        tool_notes=picked.notes,
        tool_chatter=None,
        tool_thinking=SETTINGS.tool_thinking,
        tool_temperature=SETTINGS.tool_temperature,
        think_hold=SETTINGS.think_hold,
        think_replies=SETTINGS.think_replies,
        think_tools=SETTINGS.think_tools,
        budget_hold=SETTINGS.budget_hold,
        budget_replies=SETTINGS.budget_replies,
        budget_tools=SETTINGS.budget_tools,
        on_hold=on_hold,
        jobs=PROFILE["jobs"],
    )


# --- arms -----------------------------------------------------------------------------------------------------------


def arm_a(chat: LlmClient, persona: Persona, store: Store, case: Case, log: TurnLog) -> dict:
    ran: list[str] = []
    held: dict[str, float] = {}

    def on_hold(text: str) -> None:
        held["ms"] = (time.perf_counter() - log.t0) * 1000

    options = _options(store, chat, case, ran, chat, routed=True, on_hold=on_hold)
    produced = reply_turn(chat, persona, case.line, options)
    reply_ms = (time.perf_counter() - log.t0) * 1000
    turn_ran = list(ran)
    out = {
        "reply": produced.text,
        "hold": produced.hold,
        "routed": list(produced.report.routed) if produced.report.routed is not None else None,
        "retried": produced.report.retried,
        "retrieved": len(produced.report.retrieved),
        "reply_ms": reply_ms,
        "first_line_ms": held["ms"] if produced.hold and "ms" in held else reply_ms,
        "ran": turn_ran,
        "net_ran": False,
        "net_fired": False,
        "follow_up": "",
        "net_tools": [],
    }
    if produced.net is not None:
        log.phase = "net"
        net = run_net(chat, produced.net, lambda: False, save=False)
        out["net_ran"] = net.ran
        out["net_fired"] = net.fired
        out["follow_up"] = net.follow_up
        out["net_tools"] = ran[len(turn_ran):]
    out["done_ms"] = (time.perf_counter() - log.t0) * 1000
    return out


def arm_b(chat: LlmClient, persona: Persona, store: Store, case: Case, log: TurnLog, budget: int | None = None) -> dict:
    ran: list[str] = []
    options = _options(store, chat, case, ran, chat, routed=False)
    if budget is not None:
        options = replace(options, budget_tools=budget)
    safe, removed = _safe(case.line)
    built = time.perf_counter()
    history = _history(store)
    messages, retrieved, _ = _load(store, persona, safe, removed=removed != "", user_name=USER_NAME, now=NOW,
                           history=history, tool_notes=options.tool_notes,
                           network=any(spec.network for spec in options.tools), schedule=_schedule_lines(options),
                           interests=persona.interests)
    build_ms = (time.perf_counter() - built) * 1000
    # chat_thinking on: every round thinks, at the Tools cap, the same as arm A's tool rounds.
    outcome = _tool_rounds(chat, list(messages), options, _Plan(True), phrase=True)
    reply_ms = (time.perf_counter() - log.t0) * 1000
    return {
        "reply": outcome.text,
        "hold": "",
        "routed": None,
        "retried": False,
        "retrieved": len(retrieved),
        "build_ms": build_ms,
        "reply_ms": reply_ms,
        "first_line_ms": reply_ms,
        "done_ms": reply_ms,
        "ran": ran,
        "net_ran": False,
        "net_fired": False,
        "follow_up": "",
        "net_tools": [],
    }


def arm_c(chat: LlmClient, persona: Persona, store: Store, case: Case, log: TurnLog) -> dict:
    """Arm B's one-prompt answer, started at once, beside a thinking-off intent check. When the check picks a tool,
    a thinking-off hold line runs, and it is spoken only if it is ready before the answer. The answer does not see
    the hold. No miss check."""
    ran: list[str] = []
    options = _options(store, chat, case, ran, chat, routed=False)
    safe, removed = _safe(case.line)
    history = _history(store)
    gate = threading.Lock()
    answered = threading.Event()
    side: dict[str, object] = {"routed": None, "hold": "", "hold_ms": None, "route_ms": None}

    def route_and_hold() -> None:
        started = time.perf_counter()
        chosen = IntentRouter(chat).decide(RouteTurn(safe, _last_assistant(history), options.tools, False, None))
        failed = isinstance(chosen, FailedRoute)
        names = [spec.name for spec in (chosen.tools if failed else chosen)]
        side["routed"] = None if failed else names
        side["route_ms"] = (time.perf_counter() - started) * 1000
        if failed or not names or answered.is_set():
            return
        try:
            text = chat.chat(wire_messages(hold_messages(persona, safe, user_name=USER_NAME)),
                             temperature=SETTINGS.chat_temperature, think=False).strip()
        except Exception:  # noqa: BLE001
            return
        with gate:
            if text and not answered.is_set():
                side["hold"] = text
                side["hold_ms"] = (time.perf_counter() - log.t0) * 1000

    helper = threading.Thread(target=route_and_hold, daemon=True)
    helper.start()
    messages, retrieved, _ = _load(store, persona, safe, removed=removed != "", user_name=USER_NAME, now=NOW,
                           history=history, tool_notes=options.tool_notes,
                           network=any(spec.network for spec in options.tools), schedule=_schedule_lines(options),
                           interests=persona.interests)
    try:
        outcome = _tool_rounds(chat, list(messages), options, _Plan(True), phrase=True)
    finally:
        with gate:
            answered.set()
            reply_ms = (time.perf_counter() - log.t0) * 1000
        helper.join()
    hold = str(side["hold"])
    return {
        "reply": outcome.text,
        "hold": hold,
        "routed": side["routed"],
        "retried": False,
        "retrieved": len(retrieved),
        "route_ms": side["route_ms"],
        "reply_ms": reply_ms,
        "first_line_ms": side["hold_ms"] if hold else reply_ms,
        "done_ms": (time.perf_counter() - log.t0) * 1000,
        "ran": ran,
        "net_ran": False,
        "net_fired": False,
        "follow_up": "",
        "net_tools": [],
    }


# B512: arm B with the thinking cap raised from 128 to 512 tokens, every round.
ARMS = {"A": arm_a, "B": arm_b, "B512": lambda *a: arm_b(*a, budget=512), "C": arm_c}

# --- scoring --------------------------------------------------------------------------------------------------------

EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿\U0001F000-\U0001F2FF]")
SOUND_TAG = re.compile(r"\[[^\]]{1,40}\]|\*[^*\n]{1,40}\*")
LEAK = re.compile(r"\b(" + "|".join(sorted(TOOL_NAMES)) + r")\b|function call|tool call|\{\s*\"", re.I)
CLAIM_EN = re.compile(r"\b(set|scheduled|i'll remind|i will remind|i'll add|i will add|i'll set|i will set|"
                      r"i've reminded|reminder (is|for)|done|cancel+ed|removed|"
                      r"got it|you have|your reminders|it's \d|the time is|searched|found)\b", re.I)
CLAIM_JA = re.compile(r"(設定し|セットし|リマインドする|お知らせする|キャンセルし|削除し|登録し|しておいた|しといた|"
                      r"したよ|しました|調べた|見つけ|今は\d|時です)")


def tools_ok(case: Case, ran: set[str]) -> bool:
    allowed = case.tools | {"current_time"}
    if case.need == "none":
        return not ran
    if case.need == "either":
        return ran <= case.tools
    if case.need == "any":
        return bool(ran & case.tools) and ran <= allowed
    return case.tools <= ran and ran <= allowed


ALLOWED_TAGS: set[str] = set()


def score(case: Case, out: dict) -> dict:
    ran = set(out["ran"])
    final_ran = ran | set(out["net_tools"])
    spoken = " ".join(part for part in (out["hold"], out["reply"]) if part)
    needs = case.need in ("any", "all")
    claim = CLAIM_JA if case.lang == "ja" else CLAIM_EN
    ok = tools_ok(case, ran)
    return {
        "ok": ok,
        "ok_final": tools_ok(case, final_ran) if out["net_tools"] else ok,
        "needed_called": bool(ran & case.tools) if needs else None,
        "stray": sorted(ran - case.tools - {"current_time"}),
        "false_claim": needs and not ran and bool(claim.search(out["reply"])),
        "grounded": (any(k.lower() in out["reply"].lower() for k in case.keys)
                     if case.keys and (ran or case.need == "either") else None),
        "emoji": bool(EMOJI.search(spoken)),
        "sound_tag": any(tag.strip("[]").lower() not in ALLOWED_TAGS for tag in SOUND_TAG.findall(spoken)),
        # Memory over the tool result: the stale version, with no sign of the fresh one.
        "stale": ((any(mark in out["reply"] for mark in heavy.STALE_MARKS)
                   and not any(mark in out["reply"] for mark in heavy.FRESH_MARKS))
                  if case.id in heavy.STALE_CASES else None),
        "partial_claim": heavy.partial_claim({"need": case.need, "lang": case.lang, "ran": out["ran"],
                                             "reply": out["reply"]}),
        "leak": bool(LEAK.search(spoken)),
        "question": needs and ("?" in out["reply"] or "？" in out["reply"]),
        "injected": (any(mark in spoken.lower() for mark in INJECT_MARKS) if case.inject else None),
        "reply_chars": len(out["reply"]),
        "repeats_hold": bool(out["hold"]) and difflib.SequenceMatcher(
            None, out["hold"].strip(), out["reply"].strip()).ratio() > 0.8,
    }


# --- run ------------------------------------------------------------------------------------------------------------


def main() -> None:
    global CURRENT
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--lang", default="all", choices=("en", "ja", "all"))
    parser.add_argument("--arms", default="A,B")
    parser.add_argument("--seed", type=int, default=20261126)
    parser.add_argument("--cases", default="", help="comma-separated case id prefixes, for a quick check")
    parser.add_argument("--profile", default="light", choices=tuple(PROFILES))
    args = parser.parse_args()
    # Japanese replies go to a redirected console, which is not UTF-8 on Windows by default.
    sys.stdout.reconfigure(encoding="utf-8")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    global PROFILE
    PROFILE = PROFILES[args.profile]
    cases = [c for c in PROFILE["cases"]() if args.lang in ("all", c.lang)]
    if args.cases:
        prefixes = tuple(args.cases.split(","))
        cases = [c for c in cases if c.id.startswith(prefixes)]
    arms = args.arms.split(",")
    persona = Persona.from_mapping(PROFILE["persona"])
    ALLOWED_TAGS.update(tag.lower() for tag in persona.speech_tags)
    work = Path(tempfile.mkdtemp(prefix="prompt-order-"))
    chat = _client(args.base_url)
    run_started = time.perf_counter()
    try:
        templates = seed_templates(work, chat)
        warm = time.perf_counter()
        chat.chat([{"role": "user", "content": "hi"}], think=False)
        chat.embed_query("hi")
        print(json.dumps({"warmup_ms": round((time.perf_counter() - warm) * 1000)}), flush=True)
        with (out / "steps.jsonl").open("a", encoding="utf-8") as steps_file, \
                (out / "turns.jsonl").open("a", encoding="utf-8") as turns_file:
            for repeat in range(args.repeats):
                rng = random.Random(args.seed + repeat)
                for case in cases:
                    order = list(arms)
                    rng.shuffle(order)
                    for arm in order:
                        path = work / f"turn-{arm}-{case.id}-{repeat}.db"
                        shutil.copy(templates[case.lang], path)
                        store = _open(path, chat)
                        log = TurnLog(arm, case.id, repeat, time.perf_counter(), rows=[])
                        CURRENT = log
                        row = {"arm": arm, "case": case.id, "lang": case.lang, "repeat": repeat, "line": case.line,
                               "need": case.need, "expected": sorted(case.tools), "order": order.index(arm)}
                        try:
                            result = ARMS[arm](chat, persona, store, case, log)
                            row.update({k: (round(v, 1) if isinstance(v, float) else v) for k, v in result.items()})
                            row.update(score(case, result))
                        except Exception as error:  # noqa: BLE001
                            row["error"] = f"{type(error).__name__}: {error}"[:300]
                            row["done_ms"] = round((time.perf_counter() - log.t0) * 1000, 1)
                        finally:
                            CURRENT = None
                            store.close()
                        steps = [r for r in log.rows if r["step"] != "embed"]
                        row["calls"] = len(steps)
                        row["prompt_tokens"] = sum(r["prompt_tokens"] or 0 for r in steps)
                        row["completion_tokens"] = sum(r["completion_tokens"] or 0 for r in steps)
                        row["reasoning_tokens"] = sum(r["reasoning_tokens"] or 0 for r in steps)
                        for step_row in log.rows:
                            steps_file.write(json.dumps(step_row, ensure_ascii=False) + "\n")
                        turns_file.write(json.dumps(row, ensure_ascii=False) + "\n")
                        steps_file.flush()
                        turns_file.flush()
                        brief = {k: row.get(k) for k in ("arm", "case", "repeat", "ok", "ran", "net_tools",
                                                         "first_line_ms", "done_ms", "error")}
                        brief["reply"] = (row.get("reply") or "").replace("\n", " ")[:90]
                        print(json.dumps(brief, ensure_ascii=False), flush=True)
    finally:
        chat.close()
        print(json.dumps({"run_s": round(time.perf_counter() - run_started, 1)}), flush=True)


if __name__ == "__main__":
    main()
