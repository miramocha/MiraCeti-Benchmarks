"""Experiment 12: force the tool the intent check would pick, with thinking off.

The same full 8-tool list goes out every time (as CetiMind #50 now does). Variants:
  named     thinking off, tool_choice = {"type": "function", "function": {"name": <expected tool>}}
  required  thinking off, tool_choice = "required" (1 run per line, because experiment 3's discarded run took ~78 s per call)
  think     thinking on (reasoning_effort "low"), no tool_choice, as the baseline
Writes forced.jsonl with the full arguments for scoring by hand.
"""
import json, pathlib, sys, time
from datetime import datetime
import httpx2
from cetimind.app.persona import load_persona
from cetimind.app.settings import Settings
from cetimind.app.tools.schedule import user_tools
from cetimind.core.prompt import PromptContext, build_prompt
from cetimind.core.tools import ToolSpec
from cetimind.llm.client import _function_tool

URL = "http://localhost:1234/v1/chat/completions"
HERE = pathlib.Path(__file__).parent
s = Settings.load(); persona = load_persona(saved=s.persona)
http = httpx2.Client(timeout=300)
STUBS = (
    ToolSpec("web_search", "Search the web for current or outside information. Returns titles, links, and snippets.",
             {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"], "additionalProperties": False}),
    ToolSpec("http_get", "Fetch one web page by URL and return its text.",
             {"type": "object", "properties": {"url": {"type": "string"}}, "required": ["url"], "additionalProperties": False}),
    ToolSpec("list_add", "Add an item to one of the user's lists, such as shopping or todo.",
             {"type": "object", "properties": {"list": {"type": "string"}, "item": {"type": "string"}},
              "required": ["list", "item"], "additionalProperties": False}),
    ToolSpec("list_show", "Show the items on one of the user's lists.",
             {"type": "object", "properties": {"list": {"type": "string"}}, "required": ["list"], "additionalProperties": False}),
)
WIRE = [_function_tool(t) for t in (*user_tools(), *STUBS)]
CASES = [("schedule_create", l) for l in [
    "remind me to drink water in 20 minutes", "can you remind me at 9pm to call mom",
    "every day at 8am tell me to stretch", "ping me in an hour about the laundry",
    "set a reminder for tomorrow 3pm, dentist", "hey in 10 min tell me to check the oven"]] + [
    ("web_search", "what's the latest news about the nintendo switch 2?"),
    ("web_search", "search for the best ramen places in osaka"),
    ("http_get", "what does https://example.com say?"),
    ("http_get", "summarize this page for me https://example.org/blog/post-12"),
    ("list_add", "add milk to my shopping list"),
    ("list_show", "show me my todo list")]


def reps(variant, tool):
    if variant == "required":
        return 1
    return 3 if tool == "schedule_create" else 2


def call(variant, tool, line):
    now = datetime.now().astimezone()
    built = build_prompt(persona, line, PromptContext(user_name=s.user_name or "User", now=now))
    body = {"model": s.chat_model, "messages": [{"role": m.role, "content": m.content} for m in built],
            "temperature": s.chat_temperature, "max_tokens": s.chat_max_tokens, "tools": WIRE,
            "reasoning_effort": "low" if variant == "think" else "none"}
    if variant == "named":
        body["tool_choice"] = {"type": "function", "function": {"name": tool}}
    elif variant == "required":
        body["tool_choice"] = "required"
    started = time.perf_counter()
    response = http.post(URL, json=body)
    ms = round((time.perf_counter() - started) * 1000)
    if response.status_code >= 400:
        return {"ms": ms, "error": f"HTTP {response.status_code}: {response.text[:200]}"}
    data = response.json()
    message = data["choices"][0]["message"]
    calls = message.get("tool_calls") or []
    return {"ms": ms, "now": now.isoformat(timespec="minutes"),
            "called": [c["function"]["name"] for c in calls], "args": [c["function"]["arguments"] for c in calls],
            "reasoning_tokens": ((data.get("usage") or {}).get("completion_tokens_details") or {}).get("reasoning_tokens"),
            "completion_tokens": (data.get("usage") or {}).get("completion_tokens"),
            "content": (message.get("content") or "")[:200]}


only = sys.argv[1].split(",") if len(sys.argv) > 1 else ["named", "think", "required"]
out = (HERE / "forced.jsonl").open("a", encoding="utf-8")
for variant in only:
    hits = runs = 0
    times = []
    for tool, line in CASES:
        for rep in range(reps(variant, tool)):
            result = call(variant, tool, line)
            out.write(json.dumps({"variant": variant, "want": tool, "line": line, "rep": rep, **result}) + "\n"); out.flush()
            runs += 1
            if "error" in result:
                print(f"   ERROR {variant} {line!r}: {result['error']}", flush=True)
                continue
            ok = tool in result["called"]
            hits += ok; times.append(result["ms"])
            print(f"   {'ok  ' if ok else 'MISS'} {variant:8} {result['ms']:6}ms r={result['reasoning_tokens']} "
                  f"c={result['completion_tokens']} {line!r} -> {result['called']} {result['args'] or repr(result['content'][:60])}",
                  flush=True)
    times.sort()
    print(f"{variant}: {hits}/{runs} called the expected tool, median {times[len(times) // 2] if times else 0} ms, "
          f"mean {sum(times) / len(times) if times else 0:.0f} ms\n", flush=True)
