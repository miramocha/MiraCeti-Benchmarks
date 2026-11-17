"""Tests 1-3 from the research follow-up: a non-thinking 4B model, example tool calls, and short thinking.

Writes one JSON line per call to probe2.jsonl beside this script, and prints a summary per variant.
"""
import json, sys, time, pathlib
from datetime import datetime, timedelta
import httpx2
from cetimind.app.settings import Settings
from cetimind.app.persona import load_persona
from cetimind.app.tools.schedule import user_tools
from cetimind.core.prompt import PromptContext, build_prompt, format_now
from cetimind.llm.client import _function_tool

URL = "http://localhost:1234/v1/chat/completions"
s = Settings.load(); persona = load_persona(saved=s.persona)
tools = [_function_tool(t) for t in user_tools()]
SCHED = ["remind me to drink water in 20 minutes", "can you remind me at 9pm to call mom",
         "every day at 8am tell me to stretch", "ping me in an hour about the laundry",
         "set a reminder for tomorrow 3pm, dentist", "hey in 10 min tell me to check the oven"]
PLAIN = ["what time is it?", "i remember you said you like tea", "tell me about your day",
         "i forgot to call my mom yesterday lol", "what's the weather like where you are?",
         "can you remind me what we talked about?"]
REPS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
ONLY = sys.argv[2].split(",") if len(sys.argv) > 2 else None
BRIEF = "When you think before answering, keep it under 50 words."
http = httpx2.Client(timeout=300)
log = (pathlib.Path(__file__).parent / "probe2.jsonl").open("a", encoding="utf-8")


def examples(now):
    """Two finished schedule exchanges, in the wire form CetiMind sends for tool rounds."""
    later = format_now((now + timedelta(minutes=15)).astimezone())
    return [
        {"role": "user", "content": "remind me to take my pills in 15 minutes"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "ex_1", "type": "function", "function": {
            "name": "schedule_create",
            "arguments": json.dumps({"prompt": "Tell the user to take their pills", "in_seconds": 900})}}]},
        {"role": "tool", "tool_call_id": "ex_1", "content": f"Scheduled. Next run is {later}. Id is ex1."},
        {"role": "assistant", "content": "Done. I'll remind you about your pills in 15 minutes."},
        {"role": "user", "content": "every weekday at 7:30 tell me to check my calendar"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "ex_2", "type": "function", "function": {
            "name": "schedule_create",
            "arguments": json.dumps({"prompt": "Tell the user to check their calendar", "daily_at": "07:30",
                                     "weekdays": ["mon", "tue", "wed", "thu", "fri"]})}}]},
        {"role": "tool", "tool_call_id": "ex_2", "content": "Scheduled. Id is ex2."},
        {"role": "assistant", "content": "Set. Weekdays at 7:30 I'll tell you to check your calendar."},
    ]


def messages(line, few_shot, brief):
    now = datetime.now().astimezone()
    built = build_prompt(persona, line, PromptContext(user_name=s.user_name or "User", now=now))
    out = [{"role": m.role, "content": m.content} for m in built]
    if brief:
        out[0]["content"] += "\n\n" + BRIEF
    if few_shot:
        out = [out[0], *examples(now), *out[1:]]
    return out


def call(variant, line):
    body = {"model": variant["model"], "messages": messages(line, variant.get("few_shot"), variant.get("brief")),
            "temperature": s.chat_temperature, "max_tokens": s.chat_max_tokens, "tools": tools}
    if variant.get("effort"):
        body["reasoning_effort"] = variant["effort"]
    started = time.perf_counter()
    response = http.post(URL, json=body)
    ms = (time.perf_counter() - started) * 1000
    if response.status_code >= 400:
        return {"error": f"HTTP {response.status_code}: {response.text[:200]}", "ms": ms}
    data = response.json()
    message = data["choices"][0]["message"]
    calls = message.get("tool_calls") or []
    details = (data.get("usage") or {}).get("completion_tokens_details") or {}
    return {
        "ms": round(ms), "calls": [c["function"]["name"] for c in calls],
        "args": [c["function"]["arguments"] for c in calls if c["function"]["name"] == "schedule_create"],
        "reasoning_tokens": details.get("reasoning_tokens"),
        "prompt_tokens": (data.get("usage") or {}).get("prompt_tokens"),
        "content": (message.get("content") or "")[:120],
    }


VARIANTS = {
    "9b-off": {"model": "qwen/qwen3.5-9b", "effort": "none"},
    "9b-off-fewshot": {"model": "qwen/qwen3.5-9b", "effort": "none", "few_shot": True},
    "9b-think": {"model": "qwen/qwen3.5-9b", "effort": "low"},
    "9b-think-brief": {"model": "qwen/qwen3.5-9b", "effort": "low", "brief": True},
    "4b2507": {"model": "qwen/qwen3-4b-2507"},
    "4b2507-fewshot": {"model": "qwen/qwen3-4b-2507", "few_shot": True},
}
print("persona:", persona.name, "| reps:", REPS, flush=True)
for name, variant in VARIANTS.items():
    if ONLY and name not in ONLY:
        continue
    hits = runs = false_calls = errors = 0
    times, reasoning = [], []
    for kind, lines, reps in (("sched", SCHED, REPS), ("plain", PLAIN, 1)):
        for line in lines:
            for rep in range(reps):
                result = call(variant, line)
                log.write(json.dumps({"variant": name, "kind": kind, "line": line, "rep": rep, **result}) + "\n")
                log.flush()
                if "error" in result:
                    errors += 1
                    print("   error", line, result["error"], flush=True)
                    continue
                scheduled = "schedule_create" in result["calls"]
                if kind == "sched":
                    runs += 1; hits += scheduled; times.append(result["ms"])
                    if result["reasoning_tokens"] is not None:
                        reasoning.append(result["reasoning_tokens"])
                    detail = result["args"][0] if scheduled else repr(result["content"][:70])
                    print(f"   {'ok  ' if scheduled else 'MISS'} {result['ms']:6}ms r={result['reasoning_tokens']} {line!r} -> {detail}", flush=True)
                elif scheduled:
                    false_calls += 1
                    print(f"   FALSE {line!r} -> {result['args']}", flush=True)
    avg = sum(times) / len(times) if times else 0
    mid = sorted(reasoning)[len(reasoning) // 2] if reasoning else None
    print(f"{name}: {hits}/{runs} scheduled, avg {avg:.0f} ms, median reasoning {mid}, "
          f"false calls {false_calls}/{len(PLAIN)}, errors {errors}\n", flush=True)
